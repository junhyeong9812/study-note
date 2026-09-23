# cs/issue/concurrency/thread-affine-object-confinement — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[문제]
   임의 스레드 T1, T2, T3 (요청 핸들러)
        │   직접 호출
        ▼
   Conn  (!Send: 내부 I/O가 특정 스레드의 로컬 태스크로 돎)
        → 컴파일: Send 위반
        → LocalSet 밖(멀티스레드 런타임 태스크 등)에서 spawn_local: 패닉(tokio)

   루프 L1 의 콜백 ──put_nowait──▶ 루프 L2 의 Queue   → 루프 밖 조작 = 불안전

[교정 — actor: 소유자 안에 가두고 진입점만 노출]
   T1, T2, T3 ──cmd_tx.send()──▶ ┌──────── 전용 스레드 ────────┐
   (Send 가능한 채널 핸들)        │ current_thread 런타임 + LocalSet │
                                  │   Conn 은 여기서만 산다        │
   webview ◀── relay 스레드 ◀──── │   evt_tx.send(event)           │
   (응답: oneshot 으로 park)      └────────────────────────────────┘

   L1 콜백 ──L2.call_soon_threadsafe(offer, q, data)──▶ L2 가 자기 루프에서 q 조작
```

## 핵심 문장

- 특정 스레드·이벤트 루프에 묶인 객체는 **그 소유자 안에 가두고**, 밖에는 **스레드 안전한 채널·threadsafe 진입점만** 노출한다(actor 패턴).
- 로컬 태스크와 `!Send` 상태(`Rc`·`RefCell` 등)를 공유해 I/O를 돌리는 연결은 `!Send` — `Send` future가 요구되는 곳에서 직접 쓰면 컴파일이 막히고, `LocalSet` 밖의 tokio `spawn_local`은 패닉한다.
- asyncio 객체는 대부분 스레드 안전하지 않아 자기 루프 스레드에서만 조작해야 한다 — 다른 루프·스레드에서는 `loop.call_soon_threadsafe`(코루틴이면 `run_coroutine_threadsafe`)로 대상 루프에 예약한다.
- 요청은 명령 채널로, 응답은 oneshot으로 park. 호출 측이 동기라면 동기 send가 되는 채널을 고른다.
- 객체를 한 소유자에 가두면 테스트도 단일 스레드 런타임에서 결정론적으로 돌릴 수 있다.
