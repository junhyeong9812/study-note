# cs/issue/typescript/react/stale-render-state — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
렌더 #1  (isLoading = false)
   handler#1 = () => { showLoader(); await ...; if (!isLoading) stop }   ← isLoading 은 #1 의 false 로 고정
   ─────────────────────────────────────────────
   setState(true) → 렌더 #2 예약 (지금 도는 handler#1 의 변수는 안 바뀜)

같은 틱 연속 이벤트
   click#1: if (sending) return  → false → setSending(true)  (반영은 다음 렌더)
   click#2: if (sending) return  → 아직 false → 두 번째 전송 ✗

우선순위 다른 이벤트
   dragover (연속, 낮은 우선순위) setZone(z)  ─┐ 아직 렌더 안 됨
   drop     (이산, 높은 우선순위) read zone   ◀┘ 옛 zone ✗

수명 긴 콜백 (마운트 1회 등록)
   onData = (d) => { if (locked) return }   ← 마운트 시점 locked 로 고정

[교정]
   최신 값이 필요한 곳 = 가변 ref (렌더와 무관하게 즉시 갱신)
   중복 방지            = 동기 ref single-flight (+ disabled)
   이벤트 판정          = 그 이벤트 자신의 입력으로 순수 함수 재계산
   연속 증감            = getState() / 함수형 업데이트 기준
   effect 에 새 값 전달  = pendingRef 에 넣고 effect 가 consume
```

## 핵심 문장

- 핸들러·클로저는 **자기가 만들어진 렌더의 state 스냅샷**을 본다 — `setState`는 지금 도는 함수의 변수를 바꾸지 않는다.
- 같은 틱의 연속 이벤트와 async 콜백은 옛 값을 본다 — 최신 값이 필요하면 **가변 ref**.
- 중복 실행 방지는 state가 아니라 **동기 ref 가드**로 — state 가드는 다음 렌더까지 열려 있다.
- 우선순위가 다른 이벤트 사이에 state로 값을 넘기지 말고, 판정은 **이벤트 자신의 입력**으로 다시 계산한다.
- 연타 증감은 렌더 캡처 값이 아니라 최신 저장값 기준으로. `Number("") === 0`처럼 빈 입력이 숫자로 통과하는 강제변환도 막는다.
