# cs/issue/typescript/js-language-traps — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
직관                              실제 규칙                         결과
─────────────────────────────    ─────────────────────────────    ──────────────────────
const 는 호이스팅되니 위에서도 됨   선언 줄 전까지 TDZ                 ReferenceError (리팩토링 이동 후)
{A: x(), B: y()}[k] = switch      리터럴 생성 시 모든 값 즉시 평가     선택 안 된 분기 부수효과 매 렌더
같은 키 두 번이면 에러겠지          마지막 값이 조용히 덮어씀            잘못된 표시, 에러 없음
try 안의 return 은 catch 됨        await 없이 반환한 promise 의 reject   catch 우회 → 호출부로 throw
                                  는 try 가 끝난 뒤 발생
while 로 기다리면 됨               단일 스레드: 동기 루프 = 이벤트 루프 정지  화면 정지
String(err) 면 메시지             객체 → Object.prototype.toString     "[object Object]"

교정: 선언을 최상단 · 썽크 맵 · 도메인별 맵 + no-dupe-keys · return await
      · Promise+setTimeout · .message 추출 헬퍼
```

## 핵심 문장

- `let`/`const`는 호이스팅되지만 **선언 전 접근은 TDZ**로 ReferenceError다 — 코드 이동이 이를 드러낸다.
- 객체 리터럴은 **모든 값을 먼저 평가**한 뒤 키로 조회한다 — 지연 평가가 필요하면 값을 함수(썽크)로.
- 객체 리터럴의 **중복 키는 마지막 값이 조용히 이긴다**(JS 런타임 기준) — 린트(`no-dupe-keys`)·TS 검사와 도메인 분리로 막는다.
- async 함수의 try 안에서 **await 없이 반환한** promise의 reject는 catch를 지나친다 — `return await`.
- 페이지 JS는 메인 스레드 하나에서 돈다 — busy-wait은 그 이벤트 루프 전체를 멈춘다.
- 구조화 에러를 `String()`하면 `[object Object]`다 — `.message`를 꺼낸다.
