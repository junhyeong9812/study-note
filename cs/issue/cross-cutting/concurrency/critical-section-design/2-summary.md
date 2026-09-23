# cs/issue/concurrency/critical-section-design — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[실패 1: check-then-act]
  A: lock; get(k)=None; unlock ┐
  B: lock; get(k)=None; unlock ┤  둘 다 "없음"
  A: lock; insert(k); spawn    │
  B: lock; insert(k); spawn    ┘  → 이중 spawn
  고침: lock { get-or-insert } 한 구역

[실패 2: 불변식을 여러 락이 나눠 가짐]
  Mutex(live)  Mutex(by_id)  Mutex(attached)   → 갱신 사이에 서로 어긋남(tear)
  고침: Mutex<Runtime{ live, by_id, attached }> 하나

[실패 3: 락 안의 느린 일]
  lock(map) ──▶ 원격 호출 30s / join / 서브프로세스 / 블로킹 write
                  └─ 다른 모든 항목의 조작이 이 락에서 대기 → 전역 직렬화
  고침: lock { 꺼내기(Arc clone) · 상태 변경 · 부작용 "계산" } → unlock → 부작용 실행

[실패 4: 블로킹 write under lock]
  writer: Mutex<Write>.lock().write_all(200KiB)  ← 상대가 안 읽음 → 락 보유 채 정지
  shutdown(socket) 은 read만 깨움 → 연결 스레드 미반환 → 연결 슬롯 고갈 → health까지 거부
  고침: 세션당 writer 스레드(락 없음) + 유계 큐 + 대기 상한 초과 시 에러로 "말함"

[실패 5: poison 전파]
  스레드 패닉(락 보유) → poisoned → 모든 lock().unwrap() 패닉 → 전 세션 마비
  고침: 한 곳에서 into_inner 회수 + 1회 경고 (근거: 임계구역이 실질 패닉-프리)
```

## 핵심 문장

- 하나의 불변식은 **하나의 임계구역**에서 원자적으로 갱신한다 — 조회와 행동을 다른 구역에 두지 않는다(check-then-act 금지).
- 함께 일관돼야 하는 자료구조는 **한 락** 아래 둔다.
- 락 안에서는 **상태 변경과 액션 계산만**, I/O·join·emit은 락 밖.
- 블로킹 I/O는 락이 아니라 **전용 스레드 + 유계 큐** 뒤에 둔다 — 역압이 락을 타고 무관한 경로로 번지지 않게.
- 중복 작업은 **single-flight**로 합치고, 리밋은 답이 아니라 작업에 건다.
