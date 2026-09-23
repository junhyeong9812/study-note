# cs/issue/reliability/shutdown-backstop-independence — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
사용자가 X 클릭
   │
   ▼
[층 1: 화면(웹뷰 JS 이벤트 루프)]
   onCloseRequested: preventDefault → await teardown → destroy
      ✗ teardown 예외/행          → destroy 미도달 → 창이 영원히 안 닫힘
      ✗ 언마운트 cleanup 의존      → destroy 는 cleanup 을 보장하지 않음 (세션 누수·저장 유실)
      교정1: try/finally + 4s 워치독 → destroy 항상 실행
      ✗ 그런데 JS 루프 자체가 멈추면 워치독도 같이 멈춤   ← 백스톱이 고장 지점과 같은 층
   │
   ▼
[층 2: 앱 런타임 이벤트 루프]
      ✗ 앱 종료 API 도 멈춘 이벤트 루프를 경유 → 무효
      ✗ 런타임은 "창이 0개"일 때만 종료 이벤트 → 보조 창이 남으면 프로세스 잔존
   │
   ▼
[층 3: 독립 스레드 + OS]  ← 최후 백스톱
   CloseRequested(런타임 이벤트, JS preventDefault 와 무관하게 발화)
     → 1회만 arm (AtomicBool swap)
     → 독립 스레드: sleep 5s → kill_all() → process::exit(0)
   kill_all: 신호만 보냄 (join 없음) · poison 락 복구 · 멱등
   유예 순서: ack 2.5s < 워치독 4s < 백스톱 5s   (정상 경로 우선, 최악 상한 5s)

[금지] 종료 경로에 join 하는 stop() — 응답 없는 원격에 종료가 종속
```

## 핵심 문장

- 종료 경로는 정상 정리(언마운트·close 이벤트·이벤트 루프)를 보장받지 못한다 — 정리는 닫기 경로에 명시적으로 건다.
- 백스톱이 고장 지점과 같은 층(멈춘 이벤트 루프)을 경유하면 백스톱이 아니다 — 독립 스레드에서 OS 수준 종료.
- 종료 경로의 정리는 best-effort·비블로킹: join 금지, 오염된 락도 복구해 진행, 여러 번 불려도 무해.
- 백스톱 유예는 정상 경로보다 길게 — 우아한 경로에 우선권, 최악도 상한.
- "메인 닫기 = 앱 종료" 같은 의미는 런타임이 저절로 주지 않는다 — 명시적으로 종료한다.
