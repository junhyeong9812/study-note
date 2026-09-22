# PR #19337 - Find mixed-case usernames in InMemoryUserDetailsManager#changePassword

## 0. 정향

이 문서는 `spring-security-core`의 `InMemoryUserDetailsManager.changePassword`가 **형제 메서드 일곱 개와 달리 조회 키를 소문자로 정규화하지 않던** 결함의 해설이다.\
결함은 한 줄이고 수정도 한 줄이지만, 증상이 나타나는 모습이 특이하다.\
그 사용자는 로그인도 되고 목록 조회도 되고 관리자가 대신 비밀번호를 바꿔 주는 것도 되는데, **본인이 자기 비밀번호를 바꾸는 것만** 실패한다.\
다 읽으면 "왜 한 메서드만 빠졌는데 다른 연산은 전부 멀쩡한가", "왜 이름이 딱 맞아 보이는 기존 테스트가 이 결함을 못 잡았나"를 설명할 수 있어야 한다.

> **정규화(normalization)** — 같은 뜻의 여러 표기를 하나의 표준 모양으로 통일하는 것.\
> 예: `"User"`, `"USER"`, `"user"`를 전부 `"user"`로 내려 같은 키로 만드는 것이 여기서의 정규화다.

상태: **머지 2026-08-13**(머지 커밋 `9fdd2dc6758`, `7.0.x` 브랜치, 마일스톤 7.0.7).\
라벨 `in: core` + `type: bug`.\
연결 이슈 gh-19336.

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md).\
**이 PR은 4종 구성**이다.\
spring-framework 아카이브의 다섯째 문서(`gates.md`, 이해 게이트 기록)는 이 작업에 해당하는 원자료가 없어 만들지 않았다.

## 1. 배경 - 맵 키는 소문자, 그것이 이 클래스의 계약

`InMemoryUserDetailsManager`는 사용자 전체를 필드 하나에 담는다.

```java
private final Map<String, MutableUserDetails> users = new HashMap<>();
```
(InMemoryUserDetailsManager.java:61)

> **인메모리 저장소(in-memory store)** — 데이터베이스가 아니라 프로세스 메모리의 자료구조에 데이터를 담는 저장소.\
> 예: 여기서는 `HashMap` 하나가 사용자 전체이고, 애플리케이션이 죽으면 함께 사라진다.

이 맵을 건드리는 모든 메서드가 **키를 만들 때 같은 한 줄**을 쓴다.

```java
this.users.put(user.getUsername().toLowerCase(Locale.ROOT), mutable);       // createUser  :105
this.users.remove(username.toLowerCase(Locale.ROOT));                       // deleteUser  :114
this.users.put(user.getUsername().toLowerCase(Locale.ROOT), mutable);       // updateUser  :121
return this.users.containsKey(username.toLowerCase(Locale.ROOT));           // userExists  :130
MutableUserDetails mutableUser = this.users.get(username.toLowerCase(...)); // updatePassword :161
UserDetails user = this.users.get(username.toLowerCase(Locale.ROOT));       // loadUserByUsername :171
```

**"맵 키는 항상 소문자"가 이 클래스의 계약**이고, 그 계약이 곧 사용자 정체성 모델이다.\
`"User"`로 만든 사용자와 `"user"`로 만든 사용자는 같은 엔트리를 가리키므로 애초에 공존할 수 없다.\
즉 이 매니저에서 username은 대소문자 무시(case-insensitive)로 취급된다.

> **암묵 계약(implicit contract)** — 코드에 선언돼 있지 않고 관례로만 지켜지는 약속.\
> 예: "맵 키는 항상 소문자"는 어디에도 타입이나 검사로 적혀 있지 않고, 여덟 자리가 같은 한 줄을 쓰기로 한 것이 전부다.

정규화 함수가 `toLowerCase()`가 아니라 `toLowerCase(Locale.ROOT)`인 것도 이 계약의 일부다.\
로케일을 주지 않으면 JVM 기본 로케일이 쓰이고, 터키어 로케일에서는 `"I"`가 점 없는 `"i"`로 내려가 같은 문자열이 환경에 따라 다른 키가 된다.\
`Locale.ROOT`는 그 의존을 끊는다.

> **Locale.ROOT** — 어느 나라 규칙도 아닌 "중립" 로케일.\
> 예: `"I".toLowerCase()`는 터키어 환경에서 `"ı"`(U+0131)가 되지만, `"I".toLowerCase(Locale.ROOT)`는 어디서 돌려도 `"i"`다.

## 2. 수정 전 동작 - 여덟 곳 중 한 곳만 관례 밖

수정 전 `changePassword`만 그 관례에 없었다.

```java
String username = currentUser.getName();                       // :141 원본 대소문자 그대로
...
MutableUserDetails user = this.users.get(username);            // :153 소문자화 없음
Assert.state(user != null, "Current user doesn't exist in database.");   // :154
user.setPassword(newPassword);                                 // :155
```
(수정 전 InMemoryUserDetailsManager.java:141, :153-155)

username 하나가 저장될 때와 조회될 때 어느 길을 거치는지를 세로로 내려 그리면 이렇다.

```text
User.withUsername("User") 로 등록
            |
            v
   createUser(user)                              :105
     users.put("User".toLowerCase(ROOT), ...)
            |
            v
   맵에 저장된 키 = "user"
            |
            +--------------------------+--------------------------+
            |                          |                          |
            v                          v                          v
   loadUserByUsername("User")   updatePassword(details)    changePassword(old, new)
     get("User".toLower..)        get("User".toLower..)      username = getName()  :141
     = get("user")                = get("user")                 -> "User" 그대로
            |                          |                       get("User")          :153
            v                          v                          |
          엔트리 찾음                엔트리 찾음                    v
          -> 로그인 성공             -> 변경 성공                 null (키가 "user" 라서)
                                                                   |
                                                                   v
                                              Assert.state -> IllegalStateException  :154
```

갈림은 단 한 곳, `:153`의 조회 키에 `toLowerCase(Locale.ROOT)`가 붙었느냐뿐이다.

`currentUser`는 `SecurityContext`에서 꺼낸 현재 인증(`:135`)이고 `getName()`은 사용자가 등록할 때 쓴 **원본 철자**를 돌려준다.\
맵의 키는 소문자인데 조회는 원본으로 하니, 철자에 대문자가 하나라도 있으면 조회가 빗나간다.

> **SecurityContext** — 지금 이 요청을 누가 보내고 있는지(인증 정보)를 담아 두는 스프링 시큐리티의 보관소.\
> 예: `changePassword`는 username을 인자로 받지 않고 이 보관소에서 "현재 사용자"를 꺼낸다.

두 번째 인용 줄이 결함의 성격을 결정한다.\
`Assert.state`는 조회 실패를 "찾을 수 없음"이 아니라 "**데이터베이스에 현재 사용자가 없다**"는 상태 오류로 보고한다.\
원래 이 문장은 "인증은 됐는데 저장소에는 없다 - 있을 수 없는 일"이라는 뜻이었는데, 결함 아래에서는 이 불가능해야 할 메시지가 정상 사용자에게 나온다.

> **Assert.state** — "여기까지 왔다면 이 조건은 반드시 참이어야 한다"를 표현하는 스프링의 단언 유틸.\
> 예: 깨지면 `IllegalStateException`이 나고, 그 메시지는 "입력이 잘못됐다"가 아니라 "프로그램 상태가 있을 수 없는 모양이다"로 읽힌다.

## 3. 문제 - 인증은 되는데 비밀번호만 못 바꾼다

발동 조건은 하나다: **username에 대문자가 섞인 사용자가 자기 비밀번호를 바꾸려고 할 때.**

```text
User.withUsername("User")... 로 등록
    createUser -> users.put("user", ...)          키는 소문자

로그인            loadUserByUsername("User") -> users.get("user")     OK
관리자 비번 변경   updatePassword(userDetails, ...) -> users.get("user") OK
존재 확인         userExists("User") -> containsKey("user")            OK
본인 비번 변경     changePassword(old, new) -> users.get("User")        null
                 -> IllegalStateException("Current user doesn't exist in database.")
```

증상이 보고자에게 혼란스러운 이유가 여기 있다.\
**다른 모든 연산이 성공하므로 "사용자가 없다"는 예외 메시지가 관측 사실과 정면으로 모순된다.**\
로그인한 채로 비밀번호 변경만 누르면 서버가 "그런 사용자 없음"이라고 답하는 셈이라, 원인을 조회 키 한 줄로 되짚기 어렵다.

한 가지 더 짚어 둘 것은 **재인증은 정상적으로 통과한다**는 점이다.\
`authenticationManager`가 설정돼 있으면 `changePassword`는 조회 전에 원본 username으로 재인증을 시도하는데(`:145-149`), 그 경로는 이 맵이 아니라 `UserDetailsService`를 거치고 그쪽은 이미 소문자로 정규화한다.\
그래서 "비밀번호가 맞는지"까지 확인된 뒤에 조회에서 넘어진다.

> **재인증(re-authentication)** — 민감한 작업 직전에 비밀번호를 한 번 더 확인하는 절차.\
> 예: 비밀번호 변경 화면에서 "현재 비밀번호"를 다시 묻는 것이 이것이고, 여기서는 그 단계가 통과한 뒤에 조회가 실패한다.

### 왜 지금까지 안 보였나

두 가지가 이 결함을 덮고 있었다.

1. **대문자 username이 흔치 않다.**\
   `InMemoryUserDetailsManager`는 주로 데모, 테스트, 소규모 설정에서 쓰이고 그 자리의 username은 거의 `user`, `admin` 같은 소문자다.\
   소문자 문자열의 `toLowerCase(Locale.ROOT)`는 자기 자신이므로 정규화 유무가 결과를 가르지 않는다.
2. **이름이 딱 맞아 보이는 기존 테스트가 다른 메서드를 검사한다.**\
   `InMemoryUserDetailsManagerTests`에 `changePasswordWhenUsernameIsNotInLowercase`(:70-76)가 이미 있었다.\
   이름만 보면 이 결함을 정확히 겨냥한 것 같지만 몸체가 부르는 것은 `updatePassword(UserDetails, String)` - `UserDetailsPasswordService`의 메서드이고 이미 소문자화돼 있다.\
   결함이 있는 `changePassword(String, String)`은 `UserDetailsManager`의 **다른 메서드**다.\
   이름이 커버리지의 증거가 아니라는 사례다.

> **커버리지(coverage)** — 테스트가 실제로 실행해 본 코드의 범위.\
> 예: 테스트 이름에 메서드 이름이 들어 있어도 그 메서드를 부르지 않으면 커버리지는 0이다.

## 4. 수정 해설 - 관례에 합류시키는 한 줄

수정은 동작을 더하지 않는다.\
**형제 여섯 곳과 같은 줄을 쓰는 것**이 전부다.

```java
MutableUserDetails user = this.users.get(username.toLowerCase(Locale.ROOT));
```
(InMemoryUserDetailsManager.java:153)

같은 입력(`"User"`로 등록한 사용자가 본인 비밀번호 변경)에 결과가 이렇게 갈린다.

```text
수정 전                                  수정 후
+--------------------------------+      +--------------------------------+
| 저장 키   "user"               |      | 저장 키   "user"               |
| 조회 키   "User"               |      | 조회 키   "user"               |
| get 결과  null                 |      | get 결과  MutableUser          |
+--------------------------------+      +--------------------------------+
  Assert.state 실패                       setPassword(newPassword)
  IllegalStateException                   -> 비밀번호 변경 성공
  "Current user doesn't exist"

소문자 username("user") 사용자는 양쪽 다 조회 키가 "user" 라서 결과가 같다.
```

`Locale`은 이미 임포트돼 있고 새 분기도 새 의존도 없다.\
소문자 username에서는 결과가 문자 그대로 같으므로(소문자의 `toLowerCase`는 자기 자신) 기존 사용자의 동작은 불변이고, 바뀌는 것은 지금까지 실패하던 대문자 사용자뿐이다.

**재인증 경로(`:145-149`)는 그대로 두었다.**\
그쪽은 `AuthenticationManager`에게 원본 username을 넘기고, 그 뒤의 `UserDetailsService`가 자기 규칙으로 정규화한다.\
조회 키 문제와 다른 경로이므로 함께 건드리면 수정 범위만 넓어진다.

### 검토했으나 기각한 대안

codex 교차검증이 한 가지 회귀 위험을 지적했다.\
`users`가 `HashMap`이라 null 키 조회를 허용하므로, `getName()`이 null인 별난 `Authentication` 구현에서는 수정 전에 `IllegalStateException`이 나던 자리가 이제 `NullPointerException`이 된다는 것이다.\
사실 관계는 맞지만 방어 코드를 넣지 않았고, 그 근거는 **형제 메서드도 똑같이 비방어적**이라는 것이다.\
`updatePassword`(:161)와 `loadUserByUsername`(:171)도 null 가드 없이 `username.toLowerCase(...)`를 부른다.\
이 한 메서드에만 가드를 넣으면 클래스 안에서 또 다른 비대칭이 생긴다.\
방어가 필요하다는 판단이 선다면 그것은 한 줄이 아니라 클래스 전체를 대상으로 하는 별개 변경이다.\
실제로 `Authentication.getName()`은 `Principal` 계약상 non-null이라 이 경로는 경계 케이스다.

> **회귀(regression)** — 고치기 전에는 되던 것이 수정 때문에 안 되게 되는 것.\
> 예: 예외 종류가 `IllegalStateException`에서 `NullPointerException`으로 바뀌는 것도 그 예외를 잡아 쓰던 코드에는 회귀다.

> **null 가드** — 값이 없을 때를 미리 걸러 내는 방어 코드.\
> 예: `username != null ? username.toLowerCase(ROOT) : null`처럼 앞에서 한 번 막아 주는 줄이다.

`getName()`을 한 번만 소문자화해 재인증에도 함께 쓰는 안도 검토했다가 기각했다.\
재인증은 위에서 말한 별도 경로이고, 그 입력까지 바꾸면 이 PR이 조회 버그 수정이 아니라 인증 입력 정규화 정책 변경이 된다.

### 호환성

두 사용자군 모두 영향이 없다.\
소문자 username 사용자는 결과가 동일하고, 대문자 사용자는 지금까지 예외였던 호출이 성공한다.\
대소문자만 다른 두 사용자가 충돌할 위험도 없다 - 1절에서 본 대로 맵이 이미 소문자 키로 저장하므로 그 둘은 애초에 공존할 수 없다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다.\
`InMemoryUserDetailsManagerTests`에 대문자 username 재현 1건(`changePasswordWhenCurrentUsernameIsNotInLowercaseThenChangesPassword`)을 추가했고, fix 전에는 `IllegalStateException("Current user doesn't exist in database.")`으로 실패한다.\
fix 후 같은 파일 18건 green(`--rerun-tasks`), `provisioning` 패키지 회귀 0, `checkstyleMain/Test` + `checkFormatMain/Test` 통과.\
상세는 [tests.md](tests.md).

> **red -> green** — 버그가 살아 있을 때 실패하는 테스트를 먼저 만들고(red), 고친 뒤 통과시키는(green) 순서.\
> 예: fix 전에 red를 눈으로 보지 않으면, 그 테스트가 정말 이 버그를 잡는지 알 수 없다.

stakes는 **중간**으로 판정했다(인증된 사용자의 기능이 깨지지만 데이터 의미 변경이 아니고 방향이 fail-closed다).\
그래서 codex 교차검증을 한 번 돌렸고, 판정은 승인이었으며 지적 5건 중 1건(null NPE)만 위 근거로 기각하고 나머지는 확인 또는 이미 충족이었다.\
지적 5번("맵 실엔트리가 바뀌었는지 canonical API로 확인하라")은 테스트가 이미 `loadUserByUsername`으로 단언하고 있어 충족 상태였다.

> **fail-closed** — 어긋났을 때 열지 않고 잠그는 쪽으로 떨어지는 실패 방향.\
> 예: 비밀번호가 몰래 바뀌는 것이 아니라 변경이 아예 거부되는 쪽이라, 보안 사고가 아니라 기능 고장이다.

diff는 2파일 +17/-1이고 프로덕션 변경은 한 줄이다.

## 6. 상태와 교훈

머지까지 두 달이 걸렸다(2026-06-14 제출, 2026-08-13 머지).\
리뷰 코멘트는 없었고 메인테이너 `jzheaux`가 `7.0.x`에 머지하며 다음 릴리스에 나간다고 알렸다.\
라벨이 `type: bug`로 붙은 것은 이 변경이 계약 해석 논의가 아니라 명백한 결함으로 받아들여졌다는 뜻이다.

교훈은 셋이다.

1. **같은 계약을 여러 메서드가 손으로 지킬 때, 한 곳이 빠져도 컴파일러는 침묵한다.**\
   "맵 키는 소문자"는 코드 어디에도 선언돼 있지 않고 여덟 곳의 같은 한 줄로만 유지된다.\
   실제 탐지 방법도 논리 추적이 아니라 **같은 맵을 만지는 메서드를 나란히 놓고 정규화가 없는 것을 세는 것**이었다.
2. **테스트 이름이 아니라 무엇을 호출하는지를 봐야 한다.**\
   `changePasswordWhenUsernameIsNotInLowercase`라는 이름은 이 결함을 이미 검사하는 것처럼 읽히지만 실제로는 다른 메서드를 검사한다.\
   이름만 보고 "이미 커버됨"으로 넘겼다면 결함을 놓쳤을 것이다.
3. **일관성 논거는 방어 코드 논거를 이길 수 있다.**\
   null 가드를 넣는 쪽이 언뜻 더 안전해 보이지만, 형제들이 모두 비방어적인 클래스에서 한 메서드만 방어하면 다음 사람이 읽을 때 "왜 여기만 다른가"라는 새 질문이 생긴다.\
   방어가 옳다면 그것은 클래스 전체를 대상으로 하는 별개 변경이다.
