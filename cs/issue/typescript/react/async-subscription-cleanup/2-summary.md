# cs/issue/typescript/react/async-subscription-cleanup — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
effect 실행
   un = undefined
   listen(evt, cb) ──────────────┐  (비동기: 핸들은 나중에 도착)
                                 │
언마운트 / StrictMode 재실행      │
   cleanup: un?.()   ← un 아직 undefined → 아무것도 해제 안 함   ✗
                                 │
                        resolve ─┘  un = f     ← 주인은 이미 사라짐
                                               리스너 영구 잔존 (콜백 2배 · 메모리 참조)

[교정]
   let disposed = false
   listen(evt, cb).then(f => disposed ? f() : (un = f))   도착 즉시 판정
   await 가 여러 번이면 await 마다 "if (disposed) { 정리; return }"
   cleanup: disposed = true; un?.()
   등록 실패(.catch): 선점한 자원(claim·슬롯) 해제 + 화면을 실패 상태로

[같은 원리의 일반형 = 세대 토큰]
   myGen = ++gen          시작 시 세대 발급
   닫기·언마운트 → ++gen   (늦은 결과를 무효화)
   결과 도착: if (myGen !== gen) { 결과 닫기; return }
```

## 핵심 문장

- 해제 핸들이 비동기로 도착하는 구독은 **cleanup 시점에 핸들이 없을 수 있다**.
- 해법은 "도착 시점에 판정": `disposed` 플래그(또는 세대 번호)를 보고 이미 정리됐으면 **받자마자 해제**한다.
- await가 여러 번이면 **await마다** 재검사한다 — 한 번만 검사하면 그 뒤 await 사이에 언마운트될 수 있다.
- 등록 실패도 수명의 한 경로다 — 실패 시 선점 자원을 풀고, 처리되지 않은 rejection으로 빈 화면을 남기지 않는다.
- 재설치 가능한 disposable은 **재할당 전에 이전 것을 해제**한다(AbortController로 묶으면 한 번에).
- 명령형 인스턴스(차트 등)도 같다 — 재생성 전 `destroy()`, 실패한 promise는 캐시에서 비운다.
