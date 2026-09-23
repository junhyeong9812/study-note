# cs/issue/concurrency/out-of-order-completion — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[발행 순서 ≠ 완료 순서]
  t0  req#1(A) ───────────────────────────┐
  t1  req#2(B) ──────┐                    │
  t2       resp#2(B) ┘ → state = B        │
  t3                     resp#1(A) ───────┘ → state = A   ✗ 늦은 옛 결과가 최신을 덮음
  + 옛 요청의 finally { loading=false } 는 아직 진행 중인 최신 요청의 스피너까지 끔

[같은 모양]
  저장 성공(옛 버전)      → dirty=false      편집분이 저장 안 됐는데 clean
  완료 콜백 → 202 도착    → RUNNING          끝난 작업이 영구 RUNNING
  tool_use(늦게 도착)     → InProgress       Completed가 강등
  옛 소켓 onclose         → ws = null        새 소켓 참조를 지움
  등록 promise(옛 세대)   → 목록에 push      해제된 뒤 리스너 유입
  폴링 "두 번 연속 없음"  → 삭제             낡은 응답 2개가 산 데이터 삭제

[교정 — 적용 전에 "아직 유효한가"]
  세대 토큰:  my = ++seq;  ...await...;  if (my !== seq) return;   (await마다, finally도)
  버전 캡처:  v = version; save(); if (v === version) clean
  단조 전이:  if (status.isTerminal()) no-op;  Pending→InProgress만 허용
  동일성:     sock.onclose = () => { if (ws === sock) ws = null }
  in-flight:  if (loading) return   ← 토큰은 폐기만, 중복 발행은 못 막음

[축이 여럿이면 전부 비교]  토큰 && 세션 && 데이터 서명 && epoch && 소유
```

## 핵심 문장

- 비동기 응답·이벤트의 **완료 순서는 발행 순서와 무관**하다 — 무조건 대입하면 마지막에 도착한 것이 이긴다.
- 적용 직전에 "이 결과를 요청한 문맥이 아직 최신인가"를 **세대 토큰**으로 확인한다(모든 await 뒤, 조기 return보다 먼저 증가, `finally`도).
- 상태 기계는 **단조 전이**로 — 종결 상태는 늦은 과거 전이에 덮이지 않는다.
- 핸들러는 공유 변수가 아니라 **자기 인스턴스 동일성**으로 가드한다.
- 토큰은 늦은 결과를 **버릴** 뿐 중복 발행은 못 막는다 → in-flight 가드 별도.
- 전제 축이 여럿(세션·서명·epoch)이면 **모두 비교(CAS)** — 빠진 축으로 stale write가 들어온다.
