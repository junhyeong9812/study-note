# cs/issue/java/language-semantics-traps — 컴파일은 통과하고 런타임에서 틀리는 Java 언어 규칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-24).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. 배치 잡 러너가 `catch (Exception e) { markFailed(); }`로 감싸져 있는데, 잡이 `RUNNING` 상태로 영원히 멈췄고 스레드 덤프에 그 스레드가 없다. 무슨 일이 일어났는가 — `Throwable`·`Error`·`Exception`의 계층으로 설명하고, `catch (Throwable)`로도 막을 수 없는 경우는 무엇인가.
2. 예측: `static final X INSTANCE = new X();`가 `static final List<Rule> RULES = build();`보다 **위에** 선언돼 있고 생성자가 `super(RULES)`를 부른다. 클래스를 처음 쓰는 순간 무슨 예외가 나는가, 왜인가.
3. `service.onLoginFailed(parseSiteId(header), user)` — 헤더가 숫자가 아니라서 `parseSiteId`가 던지면 `onLoginFailed` 본문(실패 카운트·잠금·감사 로그)은 어떻게 되는가. 이것이 왜 보안 결함인가.
4. `List<Sub>`를 `List<Super>`에 대입할 수 없는 이유(불변성)와, `retrieve().body(Paged.class)`로는 `Paged<Item>`의 원소 타입을 받을 수 없는 이유(소거)를 각각 말하라. 소거를 우회하는 "타입 토큰"은 어떻게 동작하는가.
5. 경계: `Optional<Node>`와 `Node`를 `equals`로 비교하는 코드는 왜 컴파일되며 결과는 무엇인가? 같은 식으로, 타입이 같은 두 인자의 순서가 뒤바뀐 호출은 왜 컴파일러가 잡지 못하는가.
6. varargs 오버로드 두 개(`f(Class<?>, Class<?>...)`, `f(Class<?>, Type...)`)에 가변 인자 0개로 호출하면 왜 모호성 에러가 나는가. 오버로드를 하나 추가했더니 기존 테스트의 `verify(mock).m(any(), any())`가 컴파일 에러가 되는 이유도 같은 원리로 설명하라.
7. 연결: 주석 안의 `created_*/modified_*`가 컴파일을 깨는 이유, record 컴포넌트에 단 `@Target(FIELD)` 어노테이션이 `RecordComponent`에서 안 보이는 이유, 정규식 `\W`가 "특수문자"가 아닌 이유 — 이 셋의 공통점은 무엇인가("사람이 읽는 의미 ≠ 언어가 정의한 의미").

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
