# cs/issue/typescript/js-language-traps — 직관과 다른 JS 언어 규칙이 조용히 오동작한다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-24).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. (예측) 컴포넌트 안에서 `useEffect(..., [items, locale])`가 먼저 나오고, 두 줄 아래에 `const { locale } = useRouter();`가 있다. `const`는 호이스팅되는데 왜 렌더 시 ReferenceError가 나는가? TDZ를 설명하라.
2. (왜) `return { [A]: <CompA label={t("a")}/>, [B]: <CompB/> }[step];` — switch처럼 보이지만 선택되지 않은 분기의 `t()` 호출과 엘리먼트 생성이 매 렌더 실행된다. 객체 리터럴의 평가 순서로 설명하라. 어떻게 하면 선택된 것만 평가되는가?
3. (예측) `const META = { PENDING: { tone: "warn" }, /* ... */ PENDING: { tone: "neutral" } }` — 에러가 나는가? `META.PENDING.tone`은 무엇인가? 여러 도메인의 상태를 한 평면 맵에 넣는 것이 왜 이 사고를 부르는가?
4. (경계) `async function f() { try { return api.post(...); } catch (e) { handle(e); } }` — 요청이 네트워크 오류로 reject되면 `handle`이 호출되는가? `return await`와 무엇이 다른가?
5. (왜) `sleep(ms)`를 `while (Date.now() < end) {}`로 구현하면 대기 동안 브라우저 전체가 멈춘다(리뷰에서 지적된 구현). JS의 단일 스레드·이벤트 루프로 설명하라.
6. (예측) IPC가 reject한 에러를 UI에 `String(err)`로 표시했더니 "[object Object]"가 나왔다. 왜인가? 무엇을 꺼내야 하는가?
7. (연결) 1~6은 모두 "런타임 에러 없이(또는 멀리 떨어진 곳에서) 조용히 틀린다"는 공통점이 있다. 각 함정을 **정적으로** 잡을 수 있는 도구(린트 규칙·타입)는 무엇이고, 도구로 못 잡는 것은 무엇인가?

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
