# PR #19335 - Exclude anonymous from additionalAuthorization

## 0. 정향

이 문서는 `spring-security-core`의 `DefaultAuthorizationManagerFactory.anonymous()`가
**자기 javadoc이 "영향 없다"고 명시한 부가 인가를 실제로는 적용하던** 결함의 해설이다.
결함의 실체는 메서드 하나가 형제들과 같은 헬퍼를 탄 것뿐이지만, 그것이 만든 상황은
읽기 까다롭다 - 문서와 코드가 정면으로 어긋나 있고, 그 어긋남을 잡아야 할 기존 테스트는
**버그가 있는 상태에서도 통과**하고 있었으며, 수정은 인가 결정을 deny에서 grant로
뒤집으므로 "버그 수정"이자 "동작 변경"이다. 다 읽으면 "왜 permitAll은 멀쩡한데
anonymous만 깨졌나", "왜 그 테스트가 버그를 못 잡았나", "왜 이 수정이 문서화된 방향의
완화인가"를 설명할 수 있어야 한다.

상태: **리뷰 대기**(2026-06-14 제출, 커밋 `d73fa8d905`, 라벨 `status: waiting-for-triage`).
연결 이슈 gh-19334. 제출 후 2026-09-08까지 리뷰 코멘트는 없다.

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md).
**이 PR은 4종 구성**이다. spring-framework 아카이브의 다섯째 문서(`gates.md`, 이해 게이트
기록)는 이 작업에 해당하는 원자료가 없어 만들지 않았다.

## 1. 배경 - 팩토리, 부가 인가, 그리고 세 개의 예외

`AuthorizationManagerFactory`는 인가 규칙을 찍어 내는 공장이다. `hasRole("ADMIN")`,
`authenticated()`, `permitAll()` 같은 메서드가 각각 `AuthorizationManager` 하나를
돌려주고, 그 매니저가 요청마다 grant(true) / deny(false) / abstain(null)을 판정한다.

`DefaultAuthorizationManagerFactory`는 여기에 **공통 조건을 한 번에 끼워 넣는 장치**를
얹는다.

```java
public void setAdditionalAuthorization(@Nullable AuthorizationManager<T> additionalAuthorization) {
	this.additionalAuthorization = additionalAuthorization;
}
```
(DefaultAuthorizationManagerFactory.java:98-100)

이것이 있으면 "이 애플리케이션의 모든 인가 규칙은 MFA를 통과한 사용자에게만"처럼 횡단
조건을 한 곳에서 걸 수 있다. 실제 사용 경로가
`AuthorizationManagerFactories.multiFactor().requireFactors(...)`다.

중요한 것은 이 setter의 javadoc이 **적용 대상을 목록으로 열거하고, 적용되지 않는 것도
명시한다**는 점이다.

```java
/**
 * Sets additional authorization to be applied to the returned
 * {@link AuthorizationManager} for the following methods:
 *
 * <ul>
 * <li>{@link #hasRole(String)}</li>
 * ...
 * <li>{@link #authenticated()}</li>
 * <li>{@link #fullyAuthenticated()}</li>
 * <li>{@link #rememberMe()}</li>
 * </ul>
 *
 * <p>
 * This does not affect {@code anonymous}, {@code permitAll}, or {@code denyAll}.
 * </p>
 */
```
(DefaultAuthorizationManagerFactory.java:76-97, 발췌)

목록에 아홉 개가 있고 마지막 문단이 셋을 제외한다. **`anonymous`는 제외 목록에 있다.**
이것이 이 PR이 근거로 삼은 계약이다.

부가 인가를 실제로 씌우는 곳은 헬퍼 하나다.

```java
private AuthorizationManager<T> withAdditionalAuthorization(AuthorizationManager<T> manager) {
	if (this.additionalAuthorization == null) {
		return manager;
	}
	return AuthorizationManagers.allOf(new AuthorizationDecision(false), this.additionalAuthorization, manager);
}
```
(DefaultAuthorizationManagerFactory.java:167-172)

`allOf`는 **하나라도 deny면 즉시 deny**이고, 전부 abstain이면 첫 인자의 기본 결정(여기서는
`false` = 거부)을 돌려준다(AuthorizationManagers.java:108-127). 즉 이 래핑은 "원래 규칙
AND 부가 조건"을 만든다. 설정하지 않으면(`null`) 매니저를 그대로 돌려주므로, **부가 인가를
설정하지 않은 애플리케이션에는 이 결함이 존재하지 않는다.**

## 2. 수정 전 동작 - 제외 목록의 셋 중 둘만 실제로 제외됐다

계약이 제외한 셋이 실제로 제외되는 방식은 서로 달랐다.

```java
@Override
public AuthorizationManager<T> authenticated() {
	return createManager(AuthenticatedAuthorizationManager.authenticated());     // :133-135
}
@Override
public AuthorizationManager<T> anonymous() {
	return createManager(AuthenticatedAuthorizationManager.anonymous());         // :147-150
}

private AuthorizationManager<T> createManager(AuthenticatedAuthorizationManager<T> authorizationManager) {
	authorizationManager.setTrustResolver(this.trustResolver);
	return withAdditionalAuthorization(authorizationManager);                    // :162-165
}
```
(수정 전 DefaultAuthorizationManagerFactory.java)

`permitAll()`과 `denyAll()`은 이 클래스에 **아예 없다.** 둘은 `AuthorizationManagerFactory`
인터페이스의 default 메서드이고(AuthorizationManagerFactory.java:34-44)
`DefaultAuthorizationManagerFactory`가 오버라이드하지 않으므로 `createManager`를 지나가지
않는다. 그래서 계약을 **우연히** 지킨다.

`anonymous()`는 다르다. 이 클래스가 오버라이드했고, 그 몸체가 `authenticated()`,
`fullyAuthenticated()`, `rememberMe()`와 **같은 `createManager` 오버로드**를 부른다. 셋은
계약상 부가 인가 적용 대상이고 `anonymous()`는 비대상인데, 넷이 같은 문으로 들어간다.
결과적으로 `anonymous()`만 계약을 깬다.

여기서 눈여겨볼 점은 `createManager(AuthenticatedAuthorizationManager)`가 두 가지 일을
한다는 것이다 - `setTrustResolver` 주입과 부가 인가 래핑. `anonymous()`에게 앞의 것은
필요하고 뒤의 것은 필요 없다. 두 관심사가 한 헬퍼에 묶여 있어서 "하나만 빼기"가 불가능했던
것이 구조적 원인이다.

## 3. 문제 - 익명 전용 엔드포인트가 조용히 닫힌다

발동 조건은 둘의 결합이다: **부가 인가를 설정했고, 그 부가 인가가 익명 사용자에게 deny를
내는 경우.** MFA 구성이 정확히 그 형태다 - 익명 사용자는 어떤 factor 권한도 갖지 않으므로
factor 요구 매니저는 반드시 deny한다.

```
factory.setAdditionalAuthorization(factors 요구 매니저)
AuthorizationManager am = factory.anonymous();
   실제 모습: allOf(deny-by-default, factors매니저, anonymous매니저)

익명 요청 authorize:
   factors매니저   -> deny   (익명은 factor 권한이 없다)
   allOf 규칙      -> 하나라도 deny면 deny, 나머지는 평가조차 안 한다
   최종            -> DENY
   기대(문서)      -> GRANT
```

즉 **로그인 페이지나 공개 진입점처럼 "익명만 허용"으로 보호한 엔드포인트가, MFA를 켜는
순간 아무도 못 들어가는 상태**가 된다. 익명 사용자는 factor가 없어서 막히고 인증
사용자는 `anonymous()` 자체가 막으므로 양쪽이 다 닫힌다. 방향이 fail-closed(과잉 차단)라
권한 상승은 아니지만, 설정한 사람 입장에서는 문서를 읽고 기대한 것과 정반대다.

### 왜 기존 테스트가 못 잡았나

이 클래스에는 정확히 그 이름의 테스트가 이미 있었다.

```java
@Test
public void anonymousWhenAdditionalAuthorizationThenNotInvoked() {
	AuthorizationManager<String> additional = mock(AuthorizationManager.class);
	DefaultAuthorizationManagerFactory<String> factory = new DefaultAuthorizationManagerFactory<>();
	factory.setAdditionalAuthorization(additional);

	factory.anonymous();

	verifyNoInteractions(additional);
}
```
(수정 전 AuthorizationManagerFactoryTests.java:125-134)

이름은 "익명일 때 부가 인가가 호출되지 않는다"이고 주장도 맞다. 그런데 **`authorize`를 한
번도 부르지 않는다.** `factory.anonymous()`는 매니저를 조립할 뿐이고, `allOf`가 돌려주는
것은 판정 시점에야 하위 매니저를 부르는 **지연 평가 람다**다(AuthorizationManagers.java:110-127).
조립 시점에는 버그가 있든 없든 `additional`이 호출되지 않으므로 `verifyNoInteractions`가
통과한다.

**이것이 이 결함의 진짜 은폐물이다.** 테스트가 없어서 못 잡은 것이 아니라, 이름과 의도가
정확한 테스트가 **관측 시점을 잘못 골라서** 통과하고 있었다. 지연 래핑을 검사할 때
"호출되지 않았다"를 조립 시점에서 보면 언제나 참이다.

## 4. 수정 해설 - permitAll이 이미 있는 자리로 옮기기

수정은 `anonymous()`를 `createManager`에서 떼어 내 직접 조립하게 한다.

```java
@Override
public AuthorizationManager<T> anonymous() {
	// Unlike authenticated()/fullyAuthenticated()/rememberMe(), anonymous() does not
	// apply additionalAuthorization, consistent with the permitAll()/denyAll()
	// defaults.
	AuthenticatedAuthorizationManager<T> manager = AuthenticatedAuthorizationManager.anonymous();
	manager.setTrustResolver(this.trustResolver);
	return manager;
}
```
(DefaultAuthorizationManagerFactory.java:147-155)

두 가지를 나눠 보는 것이 요점이다. **`setTrustResolver`는 유지하고 `withAdditionalAuthorization`만
건너뛴다.** trustResolver는 "이 인증이 익명인가"를 판정하는 부품이므로 팩토리 설정값을
계속 넘겨야 하고, 부가 인가는 계약상 비대상이다. 헬퍼가 묶어 놓았던 두 관심사를 호출
지점에서 푼 셈이다.

`roleHierarchy`는 넘기지 않는다. `AuthenticatedAuthorizationManager`에는 그것을 받는
setter가 없고, 원래 `createManager` 오버로드도 이 타입에는 trustResolver만 주입했다
(`:162-165`). 권한 계층은 `AuthorityAuthorizationManager` 계열의 관심사다.

수정 후 `anonymous()`가 인터페이스의 default 구현
(`AuthorizationManagerFactory.java:142-143`, 그냥 `AuthenticatedAuthorizationManager.anonymous()`를
돌려준다)과 다른 점은 trustResolver 주입 하나뿐이다.

### 검토했으나 기각한 대안

`withAdditionalAuthorization` 안에서 인자가 익명 매니저인지 식별해 제외하는 안을
검토했다가 기각했다. 헬퍼가 임의의 `AuthorizationManager`에서 **의미론적 의도를
추론**하게 되므로 타입 식별이 취약하고 결합도가 올라간다. 무엇보다 `permitAll`/`denyAll`은
애초에 이 헬퍼를 거치지 않는데 `anonymous`만 헬퍼 안에서 특별 취급하면 같은 계약의 셋이
서로 다른 방식으로 구현된다. 메서드별 우회가 셋을 같은 범주에 놓는다.

### 호환성 - 이 PR이 본문에 먼저 밝힌 것

**이 수정은 문서화된 방향의 동작 변경이다.** 지금까지 deny되던 요청이 grant된다.

`anonymous()`만으로 보호한 엔드포인트는, 부가 인가(MFA / IP 허용 목록 / 테넌트 상태 /
점검 모드 등)가 실패해도 이제 익명 사용자를 통과시킨다. 부가 인가를 넓은 요청 게이트로
쓰면서 익명 경로에도 걸리기를 기대했던 설정이 있다면 그 설정은 이제 다르게 동작한다.

세 가지를 근거로 이 변화를 감수했다. 첫째, javadoc이 "anonymous에는 영향 없음"을 명시하므로
기대의 근거가 문서에 있다. 둘째, 둘 다 필요하면 `allOf(factory.anonymous(), extraCondition)`으로
명시 조합할 수 있다. 셋째, `anonymous()`는 **여전히 인증 사용자를 거부**하므로 익명 전용
엔드포인트가 로그인 사용자에게 열리는 일은 없다.

이 항목은 codex 교차검증이 지적한 것이기도 하고, 리뷰어가 스스로 발견하기 전에 PR 본문
"Note on impact" 절로 선공개했다. 계약 해석이 걸린 변경에서는 영향 범위를 숨기지 않는 쪽이
리뷰를 빠르게 만든다는 판단이었다.

## 5. 검증

기존 무효 테스트를 **강화**하는 방식을 택했다. 새 테스트를 추가하면 무효 테스트가 그대로
남아 다음 사람을 또 속이기 때문이다.

```java
-		factory.anonymous();
+		AuthorizationManager<String> anonymous = factory.anonymous();

+		assertThat(anonymous.authorize(() -> TestAuthentication.anonymousUser(), "").isGranted()).isTrue();
 		verifyNoInteractions(additional);
```
(AuthorizationManagerFactoryTests.java:125-136)

`authorize`를 실제로 부르는 순간 지연 래핑이 펼쳐지므로, 버그 상태에서는 **단언과
`verifyNoInteractions`가 함께** 깨진다. fix 전 실패 메시지는
`Expecting value to be true but was false`였다. fix 후 `AuthorizationManagerFactoryTests`
31건 green(`--rerun-tasks`), `authorization` 패키지 회귀 0,
`checkstyleMain/Test` + `checkFormatMain/Test` 통과. 상세는 [tests.md](tests.md).

미변경 메서드가 여전히 부가 인가를 적용한다는 보증은 기존 테스트들이 이미 맡고 있다
(`hasRoleWhenAdditionalAuthorizationThenInvoked` :158-171 외 형제 다수). codex가 그
테스트를 추가하라고 권고했으나 diff만 보아 기존 커버리지를 몰랐던 것이라, 추가 없이
기각했다.

stakes는 **중간**으로 판정했다(프레임워크 인가 계약 위반이고 MFA 구성에서 익명 접근이
막히지만, 방향이 fail-closed라 권한 상승이 아니다). 그래서 codex 교차검증 1회를 돌렸고
판정은 승인이었다.

## 6. 상태와 교훈

제출 후 석 달 가까이 `status: waiting-for-triage` 상태다. 같은 날 낸 세 건 중 순수 결함
수정인 #19337은 두 달 만에 머지됐지만, **이 PR은 문서화된 계약의 해석과 동작 변경을
포함**하므로 트리아지에 사람의 판단이 더 필요하다고 보는 것이 자연스럽다. 그 성격 때문에
착수 시점부터 이슈를 먼저 등록하고(gh-19334) PR 본문에 영향 노트를 실었다.

교훈은 셋이다.

1. **javadoc이 계약이면 그 계약도 회귀 대상이다.** 이 결함은 코드 안에서만 보면 모순이
   없다 - `anonymous()`가 다른 셋과 같은 헬퍼를 부를 뿐이다. 위반은 문서와 코드를 나란히
   놓아야 보인다.
2. **지연 평가 앞에서는 "호출되지 않았다"를 조립 시점에 검사하면 안 된다.** 무효 테스트가
   버그를 통과시킨 이유가 이것이고, 이름과 의도가 정확한 테스트일수록 다음 사람이 "이미
   커버됨"으로 믿기 때문에 더 위험하다. 강화가 아니라 추가를 택했다면 무효 테스트가 남아
   같은 함정을 다시 놓았을 것이다.
3. **헬퍼가 두 관심사를 묶으면 "하나만 빼기"가 불가능해진다.** `createManager`가
   trustResolver 주입과 부가 인가 래핑을 함께 하는 한, `anonymous()`는 둘 다 받거나 둘 다
   포기해야 했다. 수정이 호출 지점에서 둘을 푸는 형태가 된 것은 그 구조의 결과다.
