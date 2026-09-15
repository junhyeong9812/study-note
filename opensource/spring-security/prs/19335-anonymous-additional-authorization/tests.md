# PR #19335 - 테스트 해설 (테스트 하나하나)

> `AuthorizationManagerFactoryTests`에서 강화한 1건 + 기존 테스트가 맡은 가드 역할.
> 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로 해설한다.
> 문제와 수정은 [README.md](README.md), 실구조는 [structure.md](structure.md), 착수 분석은 [analysis.md](analysis.md).

배치 전체를 먼저 본다.\
이 결함은 **어떤 팩토리 메서드가 부가 인가를 적용받는가**가 쟁점이므로, 테스트는 "적용받아야 할 쪽"과 "받지 않아야 할 쪽"을 같은 설정에서 짝지어야 한다.\
그 짝이 이미 파일에 절반쯤 갖춰져 있었고, 이 PR은 비어 있던 반쪽을 채웠다.

> **red / green** — 테스트가 실패하는 상태(red)와 통과하는 상태(green).\
> 예: 버그를 재현하는 테스트는 fix 전 red여야 하고, fix 후 green이 되어야 그 테스트가 실제로 버그를 잡았다는 뜻이다.

> **가드 테스트(guard test)** — 이번 수정이 엉뚱한 곳까지 바꾸지 않았음을 지키는, 전후 모두 green인 테스트.\
> 예: `hasRole`이 여전히 부가 인가를 적용한다는 테스트는 "anonymous만 떼어 냈다"의 증거가 된다.

| 팩토리 메서드 | 계약상 부가 인가 | 담당 테스트 |
|---|---|---|
| `anonymous()` | 비적용 | T1 `anonymousWhenAdditionalAuthorizationThenNotInvoked`(강화) - **red** |
| `permitAll()` / `denyAll()` | 비적용 | T2 `permitAllWhen...` :136-145 / `denyAllAllWhen...` :147-156 - 가드 |
| `hasRole()` / `authenticated()` / `fullyAuthenticated()` / `rememberMe()` 등 | 적용 | T3 `hasRoleWhenAdditionalAuthorizationThenInvoked` :158-171 외 - 가드 |
| `anonymous()` (부가 인가 미설정) | - | T4 `anonymousReturnsAuthenticatedAuthorizationManagerByDefault` :118-123 - 가드 |

네 테스트가 계약의 어느 칸을 맡는지를 그림으로 놓으면 이렇다.

```text
                     부가 인가 설정함              부가 인가 미설정
                +----------------------------+  +------------------+
  비적용이어야   |  anonymous   -> T1 (red)    |  |  anonymous -> T4 |
  하는 메서드    |  permitAll   -> T2 (가드)   |  |     (가드)       |
                |  denyAll     -> T2 (가드)   |  +------------------+
                +----------------------------+
  적용되어야     |  hasRole     -> T3 (가드)   |
  하는 메서드    |  authenticated / rememberMe |
                |  fullyAuthenticated         |
                +----------------------------+
```

왼쪽 위 칸 하나만 비어 있었고(정확히는 무효였고), 이 PR이 그 칸을 채운다.

## T1. 무효 테스트를 red로 만들기 - 강화

이 PR의 테스트 변경은 추가가 아니라 **기존 테스트의 강화**다.\
diff는 두 줄이다.

```java
@Test
public void anonymousWhenAdditionalAuthorizationThenNotInvoked() {
	AuthorizationManager<String> additional = mock(AuthorizationManager.class);
	DefaultAuthorizationManagerFactory<String> factory = new DefaultAuthorizationManagerFactory<>();
	factory.setAdditionalAuthorization(additional);

	AuthorizationManager<String> anonymous = factory.anonymous();

	assertThat(anonymous.authorize(() -> TestAuthentication.anonymousUser(), "").isGranted()).isTrue();
	verifyNoInteractions(additional);
}
```
(AuthorizationManagerFactoryTests.java:125-136, 굵은 변화는 `anonymous` 변수 도입과 `assertThat(...)` 한 줄)

> **목(mock)** — 진짜 구현 대신 테스트가 끼워 넣는 가짜 객체.\
> 예: `mock(AuthorizationManager.class)`는 스텁을 주지 않으면 모든 메서드가 `null`을 돌려준다.

- **주장**: 부가 인가가 설정돼 있어도 `anonymous()`가 만든 매니저는 익명 인증을 grant하고, 부가 인가를 부르지도 않는다.
- **fix 전 red인 이유**: 수정 전 `anonymous()`는 `allOf(deny-by-default, additional, anonymous매니저)`를 돌려준다.\
  `authorize`가 그 래핑을 펼치면 목 `additional`이 호출되고, 목의 기본 반환값은 null(abstain)이다.\
  `allOf`는 전부 abstain일 때 첫 인자의 기본 결정(`new AuthorizationDecision(false)`)을 돌려주므로(AuthorizationManagers.java:120-124) 결과가 deny다.\
  실측 실패 메시지는 `Expecting value to be true but was false`.

같은 테스트가 강화 전후로 무엇을 보게 되는지를 나란히 놓으면 이렇다.

```text
강화 전 (조립 시점만 본다)             강화 후 (판정까지 본다)
+-----------------------------+      +-----------------------------+
| factory.anonymous()         |      | am = factory.anonymous()    |
|                             |      | am.authorize(익명사용자)     |
| verifyNoInteractions        |      |   -> additional 호출됨       |
|   additional 호출 0회 -> OK  |      | isGranted() -> false        |
+-----------------------------+      | verifyNoInteractions -> 실패 |
  버그 있어도 green             |      +-----------------------------+
                                       버그 있으면 red
```

**왜 새 테스트를 추가하지 않고 기존 것을 고쳤나.**\
기존 테스트는 이름과 의도가 정확한데 관측 시점만 틀렸다 - `factory.anonymous()`만 부르고 `verifyNoInteractions`를 검사했다.\
`allOf`가 돌려주는 것은 판정 시점에야 하위 매니저를 부르는 지연 평가 람다이므로(AuthorizationManagers.java:110-127), 조립 시점에는 버그가 있든 없든 `additional`이 호출되지 않는다.\
**버그를 통과시키는 테스트가 그 자리에 남아 있으면 다음 사람이 "이미 커버됨"으로 오판한다.**\
그래서 무효 테스트를 살려 두고 옆에 새 테스트를 두는 대신, 무효 테스트 자체를 유효하게 만들었다.

> **관측 시점** — 어느 순간의 상태를 보고 판정하느냐의 문제.\
> 예: 지연 평가를 쓰는 코드에서 조립 직후를 보면 아직 아무 일도 일어나지 않았으므로, 무엇을 검사해도 통과한다.

**단언 한 줄이 두 가지를 동시에 검사한다.**\
버그 상태에서 `authorize`를 부르면 목 `additional`이 실제로 호출되므로, 단언(`isGranted()` = true)뿐 아니라 그 아래 `verifyNoInteractions(additional)`도 함께 깨진다.\
하나의 red가 "결과가 틀렸다"와 "부르지 말아야 할 것을 불렀다"를 모두 보고하는 셈이다.

**인자 하나하나의 의미.**

- `() -> TestAuthentication.anonymousUser()` - `authorize`의 첫 인자는 `Supplier<Authentication>`이라 람다로 감싼다.\
  `anonymousUser()`는 `AnonymousAuthenticationToken("key", "anonymous", ROLE_ANONYMOUS)`를 돌려주는 상수다(TestAuthentication.java:34-35, :58-60).\
  이 파일의 기존 헬퍼 관례를 그대로 미러했다.
- 둘째 인자 `""` - 인가 대상 객체다.\
  이 팩토리는 `DefaultAuthorizationManagerFactory<String>`로 파라미터화돼 있고 `AuthenticatedAuthorizationManager`는 대상 객체를 보지 않으므로 빈 문자열이면 충분하다.
- `.isGranted()` - `authorize`는 `AuthorizationResult`를 돌려주고 그 안의 boolean을 꺼낸다.\
  목이 abstain일 때 `allOf`의 기본 결정이 무엇인지가 이 값에 그대로 나타난다.
- 목 `additional`에 `given(...)`을 주지 않은 것도 의도적이다.\
  **부가 인가가 무엇을 반환하든 상관없이 익명은 grant돼야 한다**는 것이 계약이므로, 스텁 없는 목(항상 abstain)이 가장 약한 전제로 계약을 검사한다.

> **스텁(stub)** — 목 객체에게 "이렇게 물으면 이렇게 답하라"고 미리 심어 두는 응답.\
> 예: `given(additional.authorize(any(), any())).willReturn(...)`이 스텁이고, 이것을 주지 않으면 목은 `null`만 돌려준다.

## T2. `permitAll` / `denyAll` 가드 - 올바른 형태의 본보기 (전후 green)

같은 파일에 계약의 나머지 둘을 검사하는 테스트가 이미 있다.

```java
@Test
public void permitAllWhenAdditionalAuthorizationThenNotInvoked() {
	AuthorizationManager<String> additional = mock(AuthorizationManager.class);
	DefaultAuthorizationManagerFactory<String> factory = new DefaultAuthorizationManagerFactory<>();
	factory.setAdditionalAuthorization(additional);

	factory.permitAll();

	verifyNoInteractions(additional);
}
```
(AuthorizationManagerFactoryTests.java:136-145)

- **fix 전후 모두 green**이다.\
  `permitAll()`은 이 클래스가 오버라이드하지 않은 인터페이스 default(AuthorizationManagerFactory.java:34-36)라 `createManager`를 아예 지나가지 않으므로, 부가 인가가 붙을 자리 자체가 없다.
- 이 테스트의 역할은 회귀 가드보다 **의도의 증거**다.\
  팀이 "부가 인가 비적용"을 테스트로 명시한 대상이 셋 중 둘이었고, 셋째(anonymous)만 검사가 무효였다는 사실이 결함을 "우연한 미구현"이 아니라 "빠진 한 자리"로 규정해 준다.
- 다만 이 테스트도 T1과 같은 관측 시점 문제를 갖고 있다.\
  `authorize`를 부르지 않으므로, 만약 `permitAll()`이 언젠가 오버라이드되어 래핑을 타게 되면 이 테스트는 그것을 잡지 못한다.\
  지금은 오버라이드가 없어 우연히 유효할 뿐이다.
- **파일을 읽다 발견한 별개 사실 하나**: 바로 아래 `denyAllAllWhenAdditionalAuthorizationThenNotInvoked`(:147-156)의 몸체가 `factory.denyAll()`이 아니라 `factory.permitAll()`을 부른다.\
  `denyAll`은 실제로는 검사되지 않고 있다.\
  이 PR의 범위 밖이라 손대지 않았고, 별도 보고나 수정 후보로 남는다.

## T3. 부가 인가 적용 대상 가드 - 과잉 수정 방지 (전후 green)

수정이 "부가 인가를 어디서나 꺼 버리는" 방향으로 새지 않았음을 고정하는 쪽은 형제 테스트들이다.

```java
@Test
public void hasRoleWhenAdditionalAuthorizationThenInvoked() {
	AuthorizationManager<String> additional = mock(AuthorizationManager.class);
	given(additional.authorize(any(), any())).willReturn(new AuthorizationDecision(true),
			new AuthorizationDecision(false));
	DefaultAuthorizationManagerFactory<String> factory = new DefaultAuthorizationManagerFactory<>();
	factory.setAdditionalAuthorization(additional);

	assertUserGranted(factory.hasRole("USER"));
	assertUserDenied(factory.hasRole("USER"));

	verify(additional, times(2)).authorize(any(), any());
}
```
(AuthorizationManagerFactoryTests.java:158-171)

- 이 테스트는 **관측 시점이 옳다.**\
  `assertUserGranted` / `assertUserDenied`가 실제로 `authorize`를 부르므로 지연 래핑이 펼쳐지고, `additional`을 두 번 호출했음이 검증된다.\
  같은 파일 안에 유효한 형태와 무효한 형태가 나란히 있었던 셈이다.
- 목이 첫 호출에 grant, 둘째 호출에 deny를 내도록 스텁돼 있어 **부가 인가의 결과가 최종 결정을 실제로 좌우한다**는 것까지 고정한다.
- `authenticated`, `fullyAuthenticated`, `rememberMe`, `hasAnyRole` 등 형제 메서드에도 같은 꼴의 테스트가 이어진다(:173 이하).\
  이들이 fix 후에도 green이라는 사실이 "anonymous만 떼어 냈다"의 증거다.
- codex 교차검증은 "미변경 메서드가 여전히 부가 인가를 적용함을 같은 설정에서 보장하는 테스트를 추가하라"고 권고했으나, 위 테스트들이 이미 그 역할을 한다.\
  codex는 diff만 받았기 때문에 기존 커버리지를 볼 수 없었고, diff 최소화를 위해 추가하지 않았다.

## T4. 기본 구성 가드 - 반환 타입 고정 (전후 green)

부가 인가를 설정하지 않은 기본 팩토리에서 `anonymous()`가 무엇을 돌려주는지를 고정하는 테스트도 있다.

```java
@Test
public void anonymousReturnsAuthenticatedAuthorizationManagerByDefault() {
	AuthorizationManagerFactory<String> factory = new DefaultAuthorizationManagerFactory<>();
	AuthorizationManager<String> authorizationManager = factory.anonymous();
	assertThat(authorizationManager).isInstanceOf(AuthenticatedAuthorizationManager.class);
}
```
(AuthorizationManagerFactoryTests.java:118-123)

- **fix 전후 모두 green**이다.\
  수정 전에도 `withAdditionalAuthorization`은 `additionalAuthorization == null`이면 매니저를 그대로 돌려주므로(`:168-170`) 반환 타입이 같았다.
- 이 테스트가 중요한 이유는 **결함의 발동 범위를 좁혀 준다**는 점이다.\
  부가 인가를 설정하지 않은 애플리케이션(대다수)에서는 수정 전 코드도 정확히 같은 객체를 돌려줬다.\
  결함은 "부가 인가를 설정한 경우"에만 존재한다.

## 실측 요약

실행 결과는 예측과 일치했다.

- **fix 전**: T1이 `Expecting value to be true but was false`로 실패.\
  익명 요청이 deny된다는 뜻이고, 이것이 결함의 본체다.
- **fix 후**: `AuthorizationManagerFactoryTests` 31건 green(`--rerun-tasks`), `org.springframework.security.authorization` 패키지 회귀 0.
- **스타일**: `checkstyleMain/Test` + `checkFormatMain/Test` 통과.\
  주석에 `anonymous()`라는 토큰이 줄바꿈 경계에 걸려 포맷터가 보기 싫게 쪼개는 일이 있어, 경계에 걸리지 않는 짧은 문장으로 다시 써서 해결했다.
- **diff 규모**: 2파일 +8/-2.\
  프로덕션 변경은 `anonymous()` 한 메서드다.

> **checkstyle / checkFormat** — 소스가 프로젝트의 코딩 규약과 포맷 규칙을 지키는지 검사하는 빌드 태스크.\
> 예: spring-security는 이 둘을 통과하지 못하면 빌드가 실패하므로, 주석 한 줄의 줄바꿈 위치까지 맞춰야 한다.
