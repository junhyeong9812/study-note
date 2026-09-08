# PR #19337 - 테스트 해설 (테스트 하나하나)

> `InMemoryUserDetailsManagerTests`에 추가된 1건 + 기존 테스트가 맡은 가드 역할. 각
> 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로 해설한다.
> 문제와 수정은 [README.md](README.md), 실구조는 [structure.md](structure.md),
> 착수 분석은 [analysis.md](analysis.md).

배치 전체를 먼저 본다. 이 결함은 **조회 키의 대소문자**가 원인이므로, 새 테스트 하나가
"대문자 username"을 맡고 기존 테스트 둘이 각각 "소문자 username의 changePassword"와
"대문자 username의 형제 메서드"를 맡는 구도가 된다. 그래야 fix가 "철자 대소문자를
무의미하게 만들었다"를 증명한다.

| 무대 | username에 대문자 있음 | username이 소문자 |
|---|---|---|
| `changePassword(old, new)` (결함 메서드) | T1 `changePasswordWhenCurrentUsernameIsNotInLowercaseThenChangesPassword` - **red** | T2 `changePasswordWhenCustomSecurityContextHolderStrategyThenUses`(기존) - 가드 |
| `updatePassword(UserDetails, new)` (형제) | T3 `changePasswordWhenUsernameIsNotInLowercase`(기존) - 무관 가드 | `changePassword`(기존, :62-67) |

## T1. 대문자 username 재현 - red

새로 추가한 한 건은 대문자가 섞인 username으로 매니저를 만들고, 그 사용자로 인증한 상태를
꾸민 뒤 비밀번호 변경을 시킨다.

```java
@Test
public void changePasswordWhenCurrentUsernameIsNotInLowercaseThenChangesPassword() {
	UserDetails userNotLowerCase = User.withUserDetails(PasswordEncodedUser.user()).username("User").build();
	InMemoryUserDetailsManager manager = new InMemoryUserDetailsManager(userNotLowerCase);
	Authentication authentication = new UsernamePasswordAuthenticationToken("User", userNotLowerCase.getPassword(),
			userNotLowerCase.getAuthorities());
	SecurityContextHolderStrategy strategy = mock(SecurityContextHolderStrategy.class);
	given(strategy.getContext()).willReturn(new SecurityContextImpl(authentication));
	manager.setSecurityContextHolderStrategy(strategy);

	String newPassword = "newPassword";
	manager.changePassword(userNotLowerCase.getPassword(), newPassword);

	assertThat(manager.loadUserByUsername("User").getPassword()).isEqualTo(newPassword);
}
```
(InMemoryUserDetailsManagerTests.java, 추가 위치는 기존 `changePasswordWhenCustomSecurityContextHolderStrategyThenUses` 바로 뒤)

- **주장**: username에 대문자가 있어도 현재 사용자의 비밀번호 변경이 성공하고, 그 변경이
  매니저가 실제로 쓰는 맵 엔트리에 반영된다.
- **fix 전 red인 이유**: 매니저는 `"User"`를 키 `"user"`로 저장했는데(생성자 -> `createUser`
  -> `:105`) `changePassword`는 `users.get("User")`로 조회한다(수정 전 `:153`). 결과는
  null이고 다음 줄 `Assert.state`가
  `IllegalStateException("Current user doesn't exist in database.")`를 던진다. 실패가
  단언에서 나지 않고 **호출 자체에서** 나는 형태다.

**설정 세 줄이 각각 하는 일이 있다.**

- `User.withUserDetails(PasswordEncodedUser.user()).username("User")` - 기존 테스트 픽스처를
  재사용하면서 철자만 대문자로 바꾼다. 비밀번호는 `PasswordEncodedUser`가 이미 인코딩한
  값이라 형식이 맞는다.
- `new InMemoryUserDetailsManager(userNotLowerCase)` - 컬렉션 생성자는 각 사용자를
  `createUser`로 등록하므로(`:70-74`) 저장 키가 `"user"`가 되는 것이 여기서 확정된다.
  결함의 전제(저장 키와 조회 키의 철자 불일치)를 만드는 줄이다.
- `mock(SecurityContextHolderStrategy.class)` + `SecurityContextImpl(authentication)` -
  `changePassword`는 인자로 username을 받지 않고 `SecurityContext`에서 현재 사용자를
  꺼내므로(`:135`), 컨텍스트를 심어 주지 않으면 `AccessDeniedException`으로 다른 곳에서
  넘어진다(`:136-140`). 이 패턴은 새로 만든 것이 아니라 같은 파일의
  `changePasswordWhenCustomSecurityContextHolderStrategyThenUses`(:115-124)를 그대로 미러한
  것이다.
- `UsernamePasswordAuthenticationToken("User", ...)` - principal을 `UserDetails`가 아니라
  문자열 `"User"`로 준다. `getName()`이 그 문자열을 그대로 돌려주므로 조회 키가 원본 철자가
  되는 경로를 가장 짧게 만든다.

**단언이 `loadUserByUsername`을 거치는 이유.** 변경을 확인하는 방법은 둘이다. 테스트가
들고 있는 `UserDetails` 객체를 다시 보는 것과, 매니저의 공개 조회 API로 다시 꺼내 보는
것. 앞의 방법은 `changePassword`가 엉뚱한 객체를 고쳤어도 통과할 수 있다. 뒤의 방법은
**매니저가 실제로 조회에 쓰는 맵 엔트리**를 관측하므로 "고친 자리가 맞는 자리인가"까지
검증한다. 인자로 `"User"`를 주는 것도 의도적이다 - 조회 쪽 정규화(`:171`)까지 함께 지나므로,
저장과 조회가 같은 키로 만난다는 사실이 단언 한 줄에 담긴다.

이 단언은 codex 교차검증이 "canonical API로 관측하라"고 권고한 항목이기도 한데, 테스트가
처음부터 그 형태였으므로 추가 작업 없이 충족으로 처리됐다.

## T2. 기존 `changePasswordWhenCustomSecurityContextHolderStrategyThenUses` - 가드 (전후 green)

새 테스트가 "대문자 입력"을 맡는 동안, 소문자 입력에서 아무것도 안 바뀌었음을 고정하는
쪽은 기존 테스트다.

```java
@Test
public void changePasswordWhenCustomSecurityContextHolderStrategyThenUses() {
	Authentication authentication = TestAuthentication.authenticatedUser();
	InMemoryUserDetailsManager manager = new InMemoryUserDetailsManager((User) authentication.getPrincipal());
	SecurityContextHolderStrategy strategy = mock(SecurityContextHolderStrategy.class);
	given(strategy.getContext()).willReturn(new SecurityContextImpl(authentication));
	manager.setSecurityContextHolderStrategy(strategy);
	manager.changePassword("password", "newpassword");
	verify(strategy).getContext();
}
```
(InMemoryUserDetailsManagerTests.java:115-124)

- `TestAuthentication.authenticatedUser()`가 만드는 사용자의 username은 `"user"`로 이미
  소문자다(TestAuthentication.java:49). 그래서 저장 키와 조회 키가 수정 전에도 일치했고 이
  테스트는 **fix 전후 모두 green**이다.
- 그것이 이 가드의 요점이다. 수정이 "이미 되던 입력"의 결과를 바꾸지 않았음을 고정한다.
  정규화가 필요 없던 입력에 정규화를 걸어도 결과가 같아야 한다는 것이 회귀 판정 기준이다.
- 이 테스트가 `changePassword`를 예외 없이 통과시킨다는 사실 자체가 T1의 red를 "설정
  실수"가 아니라 "철자 차이"로 귀속시켜 준다. 두 테스트의 구조가 같고 차이가 username
  대소문자뿐이기 때문이다.

## T3. 기존 `changePasswordWhenUsernameIsNotInLowercase` - 이름이 겹치는 무관 가드

이 파일에서 가장 주의할 테스트다. 이름은 이번 결함을 정확히 겨냥한 것처럼 읽히는데,
몸체가 부르는 것은 다른 메서드다.

```java
@Test
public void changePasswordWhenUsernameIsNotInLowercase() {
	UserDetails userNotLowerCase = User.withUserDetails(PasswordEncodedUser.user()).username("User").build();
	String newPassword = "newPassword";
	this.manager.updatePassword(userNotLowerCase, newPassword);
	assertThat(this.manager.loadUserByUsername(userNotLowerCase.getUsername()).getPassword())
		.isEqualTo(newPassword);
}
```
(InMemoryUserDetailsManagerTests.java:69-76)

- 부르는 것은 `updatePassword(UserDetails, String)`이고, 이 메서드는 수정 전부터
  `users.get(username.toLowerCase(Locale.ROOT))`로 조회한다(`:161`). 즉 **이미 정상인
  경로**를 검사한다.
- 결함이 있는 것은 `changePassword(String, String)`이다. 두 메서드는 소속 인터페이스도
  다르다 - 전자는 `UserDetailsPasswordService`(프레임워크나 관리자가 대상 사용자를 지목해
  바꾼다), 후자는 `UserDetailsManager`(현재 인증된 사용자가 스스로 바꾼다).
- 그래서 새 테스트를 기존 테스트의 강화가 아니라 **별도 메서드**로 추가했다. 이름도
  `...CurrentUsername...`으로 지어 "현재 인증 사용자"라는 구분을 이름에 남겼다.
- 이 테스트도 fix 전후 green이고, 역할은 "형제 메서드는 원래 정상이며 이 수정이 그쪽을
  건드리지 않았다"는 가드다.

## 실측 요약

실행 결과는 예측과 일치했다.

- **fix 전**: T1이 `IllegalStateException: Current user doesn't exist in database.`로 실패.
  단언에 도달하지 못하고 `manager.changePassword(...)` 호출에서 던진다.
- **fix 후**: `InMemoryUserDetailsManagerTests` 18건 green(`--rerun-tasks`),
  `org.springframework.security.provisioning` 패키지 회귀 0.
- **스타일**: `checkstyleMain/Test` + `checkFormatMain/Test` 통과. `./gradlew format`이
  `new UsernamePasswordAuthenticationToken("User", ...)` 한 줄이 길다며 인자에서 줄바꿈했고,
  포맷터 결과를 그대로 채택했다.
- **diff 규모**: 2파일 +17/-1. 프로덕션 변경은 `InMemoryUserDetailsManager.java` 한 줄뿐이다.
