# PR #19337 - 무대의 실구조와 워크플로우

> PR #19337의 무대가 되는 실구조와 워크플로우.
> 문제와 수정은 [README.md](README.md), 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: fork `main`(`ed7ae7969ed`) - **수정 전** 상태다.
> 아래 file:line은 전부 수정 전 좌표이고, 수정은 `:153` 한 줄이다.
> 업스트림 머지 커밋은 `9fdd2dc6758`(7.0.x).

## 1. 무대 - 실구조

이 결함의 무대는 **인메모리 사용자 저장소 하나와 그것을 여는 여덟 개의 문**이다.\
저장소는 평범한 `HashMap` 하나이고, 특별한 것은 그 맵의 키를 만드는 규칙이 클래스 전체에 손으로 복제돼 있다는 점이다.\
층을 위에서 아래로 그리면 이렇다.

```text
+------------------------------------------------------------------------------+
| 호출자                                                                        |
|   애플리케이션 코드 / 스프링 시큐리티 필터 / 관리 화면                          |
|   두 인터페이스가 서로 다른 문을 연다                                          |
|     UserDetailsManager          - 사용자 CRUD + 본인 비밀번호 변경             |
|     UserDetailsPasswordService  - 프레임워크가 대상 사용자를 지목해 갱신        |
|     UserDetailsService          - 인증 시 사용자 조회                          |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| InMemoryUserDetailsManager    core/.../provisioning/InMemoryUserDetailsManager.java
|                                                                              |
|  [상태]                                                                       |
|    Map<String, MutableUserDetails> users = new HashMap<>()            :61     |
|    SecurityContextHolderStrategy securityContextHolderStrategy        :63-64  |
|    AuthenticationManager authenticationManager (nullable)             :67     |
|                                                                              |
|  [키 정규화 - 맵을 만지는 여덟 자리]                                            |
|    createUser          users.put(username.toLowerCase(Locale.ROOT), .)  :105/:108
|    deleteUser          users.remove(username.toLowerCase(Locale.ROOT))  :114  |
|    updateUser          users.put(username.toLowerCase(Locale.ROOT), .)  :121/:124
|    userExists          users.containsKey(username.toLowerCase(ROOT))    :130  |
|    changePassword      users.get(username)          <- 정규화 없음      :153  |
|    updatePassword      users.get(username.toLowerCase(Locale.ROOT))     :161  |
|    loadUserByUsername  users.get(username.toLowerCase(Locale.ROOT))     :171  |
|                                                                              |
|  ** 여덟 자리 중 :153 하나만 원본 철자로 조회한다 **                            |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| Map<String, MutableUserDetails> users  (HashMap)                             |
|   키   = username.toLowerCase(Locale.ROOT)   - 클래스의 암묵적 계약            |
|   값   = MutableUser (setPassword 가능한 래퍼)                                 |
|   결과 = "User" 와 "user" 는 같은 엔트리 - 두 사용자는 공존할 수 없다            |
+------------------------------------------------------------------------------+
```

> **CRUD** — 생성(Create)·조회(Read)·수정(Update)·삭제(Delete)를 묶어 부르는 말.\
> 예: `createUser` / `loadUserByUsername` / `updateUser` / `deleteUser` 네 메서드가 이 저장소의 CRUD다.

> **래퍼(wrapper)** — 원래 객체를 감싸서 기능을 덧붙인 객체.\
> 예: `MutableUser`는 읽기 전용인 `UserDetails`를 감싸 `setPassword`를 쓸 수 있게 해 준다.

## 2. 워크플로우 - changePassword 한 번의 호출

`changePassword`는 인자로 username을 받지 않는다.\
**누구의 비밀번호인지는 보안 컨텍스트에서 나온다**는 것이 이 메서드의 특징이고, 결함의 입력도 거기서 들어온다.

```text
changePassword(oldPassword, newPassword)                                :134
  |
  | 1. 현재 사용자 확보
  |    securityContextHolderStrategy.getContext().getAuthentication()   :135
  |    null 이면 AccessDeniedException                                  :136-140
  |
  | 2. 이름 추출
  |    String username = currentUser.getName();                         :141
  |      -> 등록 당시의 원본 철자. 소문자화되지 않은 값이다.
  |
  | 3. (선택) 재인증
  |    authenticationManager != null 이면                               :145
  |      authenticate(unauthenticated(username, oldPassword))           :147-148
  |      -> 이 경로는 users 맵이 아니라 UserDetailsService 를 거친다.
  |         그쪽은 loadUserByUsername(:171)에서 자체 정규화하므로 통과한다.
  |    없으면 "Password won't be re-checked" 로그만                      :150-152
  |
  | 4. 조회  <- 결함 지점
  |    MutableUserDetails user = this.users.get(username);              :153
  |      수정 전: 원본 철자로 조회 -> 대문자가 있으면 null
  |      수정 후: username.toLowerCase(Locale.ROOT) 로 조회
  |
  | 5. 상태 단언
  |    Assert.state(user != null, "Current user doesn't exist in database.")  :154
  |      -> "인증은 됐는데 저장소에 없다" = 있을 수 없는 일이라는 뜻의 문장.
  |         결함 아래에서는 이 문장이 정상 사용자에게 나온다.
  |
  v 6. 갱신
     user.setPassword(newPassword);                                     :155
       MutableUser 를 제자리에서 고치므로 맵에 다시 put 할 필요가 없다.
```

> **보안 컨텍스트(security context)** — 현재 요청을 수행 중인 주체의 인증 정보를 담아 두는 자리.\
> 예: 로그인한 사용자의 이름과 권한이 여기 들어 있어서, 메서드가 username을 인자로 받지 않아도 "누구"를 알 수 있다.

> **제자리 변경(in-place mutation)** — 새 객체를 만들어 갈아 끼우는 대신 기존 객체의 필드를 직접 고치는 것.\
> 예: `MutableUser.setPassword`가 그 방식이라, 맵에는 같은 객체가 들어 있으므로 다시 `put` 할 필요가 없다.

3단계와 4단계의 관계가 이 결함의 관측을 어렵게 만든다.\
**재인증이 먼저 통과한 뒤에 조회가 넘어지므로**, 사용자 입장에서는 "비밀번호는 맞다고 확인해 놓고 사용자가 없다고 한다"는 모순된 응답을 받는다.

같은 사용자가 겪는 두 세계를 나란히 놓으면 이렇다.

```text
username "user" (소문자)                  username "User" (대문자 섞임)
+-----------------------------+          +-----------------------------+
| 1 현재 사용자 확보    OK     |          | 1 현재 사용자 확보    OK     |
| 2 이름 추출 "user"          |          | 2 이름 추출 "User"          |
| 3 재인증            통과    |          | 3 재인증            통과    |
| 4 get("user")     엔트리    |          | 4 get("User")       null    |
| 5 Assert.state      통과    |          | 5 Assert.state      실패    |
| 6 setPassword       완료    |          | 6 도달 못 함                |
+-----------------------------+          +-----------------------------+
  비밀번호가 바뀐다                        "Current user doesn't exist"
```

두 세계의 차이는 2단계에서 뽑은 문자열의 대소문자뿐이다.

## 3. 두 개의 비밀번호 변경 메서드 - 이름이 겹치는 자리

이 클래스에는 비밀번호를 바꾸는 메서드가 둘이고, 둘의 차이를 모르면 테스트 커버리지도 오판하게 된다.\
아래 표는 같은 차원(누가 대상을 정하는가, 어느 인터페이스인가, 정규화 여부)으로 둘을 비교한다.

| 차원 | `changePassword(old, new)` :134 | `updatePassword(UserDetails, new)` :158 |
|---|---|---|
| 소속 인터페이스 | `UserDetailsManager` | `UserDetailsPasswordService` |
| 대상 결정 | `SecurityContext`의 현재 인증 | 인자로 받은 `UserDetails` |
| 대상 이름 출처 | `currentUser.getName()` :141 | `user.getUsername()` :160 |
| 조회 키 (수정 전) | 원본 철자 :153 | 소문자 :161 |
| 실패 시 | `IllegalStateException` (Assert.state) :154 | `RuntimeException("user ... does not exist")` :162-164 |
| 이번 결함 | 있음 | 없음 |

`InMemoryUserDetailsManagerTests`의 `changePasswordWhenUsernameIsNotInLowercase`(:69-76)가 검사하는 쪽은 **오른쪽 열**이다.\
이름은 왼쪽 열을 가리키는 것처럼 읽힌다.

## 4. 이 무대에서 정규화가 하는 일

`toLowerCase(Locale.ROOT)`는 한 줄짜리 호출이지만 이 클래스에서는 세 가지를 동시에 한다.

- **정체성 정의.**\
  username을 대소문자 무시로 취급한다고 선언한다.\
  그 결과 `"Admin"`과 `"admin"`은 같은 계정이며 둘을 동시에 등록할 수 없다(`createUser`가 `userExists`로 먼저 막는다).
- **로케일 의존 제거.**\
  인자 없는 `toLowerCase()`는 JVM 기본 로케일을 쓴다.\
  터키어 로케일에서 `"I"`는 점 없는 `"i"`(U+0131)로 내려가므로, 같은 문자열이 실행 환경에 따라 다른 키가 된다.\
  `Locale.ROOT`가 그 의존을 끊는다.
- **저장과 조회의 합의.**\
  이 함수를 쓰는 여덟 자리가 모두 같은 결과를 내야 맵이 일관된다.\
  강제 장치는 없고 각 자리가 같은 줄을 쓰기로 한 관례뿐이며, 이번 결함은 그 관례에서 한 자리가 빠진 것이다.

> **로케일(locale)** — 언어·지역별 문자 처리 규칙 묶음.\
> 예: 같은 `toLowerCase()`라도 터키어 로케일에서는 `"I"`를 점 없는 `"ı"`로 내려서, 서버를 어디에 띄웠느냐에 따라 맵 키가 달라진다.
