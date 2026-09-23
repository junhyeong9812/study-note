# cs/issue/concurrency/cancellation-reachability — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[취소 신호의 경로]
  owner.drop() ──Shutdown──▶ worker
                               │
        ┌──────────────────────┼──────────────────────────┐
        │ handshake: await rpc1  ← 취소 안 봄 (영구 대기)   │  ✗ 신호 도달 불가
        │            await rpc2                            │
        │ main loop: select!{ cmd, shutdown }  ← 여기만 봄 │
        └──────────────────────────────────────────────────┘
  결과: 상대가 멈추면 스레드 + 자식 프로세스 누수

[교정 1] 모든 대기 지점을 취소와 경주시킨다
  select!{ run_all(),  cancel.changed() }   → 취소 시 future 통째 drop (모든 await 취소)
  단, 비-await 동기 구간(동기 파일 I/O 등)은 선점 불가

[교정 2] join 순서
  ✗ lock(map) → join(thread)          한 세션이 멈추면 전 세션 정지
  ✓ lock(map) → remove → unlock → cancel → join

[교정 3] 깨울 수 없는 블로킹 read
  scope { spawn(relay: stdin.read) ; ... } ← scope 끝에서 join → 입력 없으면 영원히
  ✓ relay는 join하지 않음 + 상대 hang-up(POLLHUP) 감지로 반환

[테스트 함정] 입력 = 즉시 EOF 버퍼 → read가 바로 끝나 "멈춘 read" 재현 불가
```

## 핵심 문장

- 취소를 확인하지 않는 대기 지점이 **하나라도** 있으면, 상대가 멈추는 순간 그곳이 영구 대기가 되고 취소는 전파되지 않는다.
- 스레드를 외부에서 죽일 수 없으면 취소는 **협력적**이다 — 스레드가 스스로 끝나도록 모든 await를 취소 가능하게 만든다.
- (Rust처럼 lazy future인) async에서는 작업 future 전체를 취소와 `select`하면 안의 모든 await가 함께 취소된다. 동기 블로킹 구간·따로 spawn한 태스크는 예외.
- 공유 락을 쥔 채 join하지 않는다 — 먼저 꺼내고 락 밖에서 cancel→join.
- 깨울 수 없는 블로킹 read는 기다리지 않는 구조(join 안 함 + hang-up 감지)로 우회한다.
- 테스트 입력이 즉시 EOF면 "멈춘 상대"를 재현하지 못한다.
