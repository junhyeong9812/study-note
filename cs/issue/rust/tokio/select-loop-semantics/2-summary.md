# cs/issue/rust/tokio/select-loop-semantics — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
select! 한 바퀴 = 준비된 분기 하나를 골라 "본문을 끝까지" 실행 → 다음 바퀴
                  본문 안의 .await 동안 다른 분기는 poll되지 않는다

[함정 1] 패턴 불일치          Some(x) = rx.recv()  → None
         = 그 select! 호출 동안 분기 비활성화 (루프 종료 아님) → 원격 close 후 루프 잔존
         모든 분기 비활성 + else 없음 → panic
[함정 2] 닫힌 채널            recv()/changed() 가 즉시 None/Err 반복
         = 영원히 준비 상태 → break 안 하면 busy loop
[함정 3] 본문 안의 긴 await   입력 분기가 큰 쓰기를 끝까지 await
         = 출력 분기 굶김 (본문 안에서 청크로 쪼개도 한 덩어리)
[함정 4] 흐름제어 자기 교착
         쓰기 await ─ 상대 창 0 ─▶ WINDOW_ADJUST 대기
              ▲                              │ 배달 주체 = 연결 루프
              │                              ▼
         읽기 멈춤 ◀── 수신 큐(cap) 가득 ◀── 연결 루프 park
[함정 5] Builder로 만든 런타임에 IO 드라이버 미활성 → 소켓 I/O 불가 (tokio 1.x: 등록 시 panic)

[교정]
  종료:   모든 분기를 match로 받고 None/Err/Eof/Close => break
  굶김:   pending 버퍼 + 루프 턴당 1청크만 쓰는 always-ready 분기, 유계 입력 큐
  교착:   split() → reader future ∥ writer future, join! (둘 다 매 wake poll)
          신호 2개: Success(쓰기 허가) · done(채널 종료 → writer 해제)
  런타임: new_current_thread().enable_all()
  검증:   대조군이 결정론적으로 교착하는 조건(작은 창)을 먼저 만든 뒤 처치군 측정
```

## 핵심 문장

- `select!`의 패턴 불일치는 "분기 비활성화"이지 "루프 종료"가 아니다 — 종료 조건은 **모든 분기에서** 명시적으로 break한다.
- 닫힌 채널의 recv/changed는 **영원히 즉시 준비**다 — 무시하면 busy loop.
- 선택된 분기의 본문이 끝날 때까지 다른 분기는 poll되지 않는다 — 본문 안의 긴 await 시퀀스는 쪼개도 하나의 긴 블록이다.
- 흐름제어 채널에서 **읽기를 멈춘 쓰기는 자기를 가둔다** — 읽기와 쓰기는 독립적으로 poll되는 두 future여야 한다.
- 처치의 효과는 **대조군이 실패하는 조건**에서만 증명된다.
- `runtime::Builder`로 만든 런타임은 드라이버(IO·time)를 명시적으로 켠다(`#[tokio::main]`은 기본으로 켬).
