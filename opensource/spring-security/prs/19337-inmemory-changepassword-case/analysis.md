# PR #19337 - 착수 분석: changePassword의 소문자화 누락

> 원본: fork repo의 `analyze-docs/plans/2026-06-14/spring-security-core-bug-hunt/`
> `C-10-inmemoryusermanager-changepassword-case/`(task.md·해설.md·changelog.md·review-log.md).
> 학습 문서로 옮기면서 작업 진행용 절을 덜어내고 실측 근거를 절로 승격했다.
> 결론은 PR #19337로 반영됐다(커밋 `02e7f1537b`, 머지 `9fdd2dc6758`).
>
> **좌표 주의**: 본문의 file:line은 **수정 전** 파일 기준이다.
> 문제와 수정 요약은 [README.md](README.md), 실구조는 [structure.md](structure.md), 테스트는 [tests.md](tests.md).

## 0. 결론 먼저

`InMemoryUserDetailsManager`가 `users` 맵을 만지는 여덟 자리 중 일곱은 `username.toLowerCase(Locale.ROOT)`로 키를 정규화하는데 `changePassword`만 원본 철자로 조회했다(`:153`).

```java
String username = currentUser.getName();                    // :141  원본 철자
MutableUserDetails user = this.users.get(username);         // :153  형제 일곱은 정규화한다
Assert.state(user != null, "Current user doesn't exist in database.");   // :154
```

username에 대문자가 하나라도 있으면 조회가 null이 되고 `IllegalStateException`이 난다.\
같은 사용자로 로그인·조회·관리자 비밀번호 갱신은 전부 성공하므로, **예외 메시지가 관측 사실과 모순되는** 형태로 드러난다.\
수정은 조회 키에 정규화 한 줄을 넣어 관례에 합류시키는 것이다.

> **정규화(normalization)** — 같은 뜻의 여러 표기를 하나의 표준 모양으로 통일하는 것.\
> 예: `"User"`와 `"user"`를 전부 `"user"`로 내려 맵 키를 하나로 만드는 것이 여기서의 정규화다.

## 1. 발견 경로 - 어떻게 찾았나

이 결함은 논리 추적이 아니라 **패턴 스캔**으로 나왔다.\
spring-security core 모듈 14개 패키지군을 병렬 에이전트로 훑는 버그 헌트에서 `provisioning` 담당이 "같은 맵을 만지는 메서드 여덟 개 중 하나만 키 정규화가 없다"를 보고했고(후보 ID C-10), 메인이 재현 테스트로 직접 red를 확인했다.

> **패턴 스캔** — 코드의 의미를 따라가는 대신, 같은 모양이 반복되는 자리를 나열하고 어긋난 것을 세어 찾는 방식.\
> 예: 여기서는 `users`를 만지는 여덟 줄을 한 화면에 늘어놓자 `toLowerCase`가 없는 한 줄이 튀어나왔다.

이 방식이 통한 이유는 결함의 성격 때문이다.\
**계약이 코드에 선언돼 있지 않고 같은 한 줄의 반복으로만 유지될 때**, 그 계약의 위반은 의미를 읽어서가 아니라 모양을 세어서 찾힌다.\
같은 라운드에서 spring-framework의 `SQLErrorCodes` 정렬 누락도 같은 방식으로 나왔다.

## 2. 무대 - 객체와 역할

결함은 저장소 하나와 그것을 여는 문 여덟 개 사이에 있다.

```text
 호출자 (앱 코드 / 시큐리티 필터)
   |  UserDetailsManager.changePassword(old, new)       <- 본인이 바꾼다
   |  UserDetailsPasswordService.updatePassword(u, new) <- 지목해서 바꾼다
   |  UserDetailsService.loadUserByUsername(name)       <- 인증 시 조회
   v
 InMemoryUserDetailsManager     core/.../provisioning/InMemoryUserDetailsManager.java
   |  SecurityContextHolderStrategy  - 현재 인증 출처                 :63-64, :135
   |  AuthenticationManager (nullable) - 선택적 재인증                :67, :145-149
   |  키 정규화 일곱 자리   :105 :108 :114 :121 :124 :130 :161 :171
   |  키 미정규화 한 자리   :153                                      <- 결함
   v
 Map<String, MutableUserDetails> users  (HashMap)                     :61
   키 = 소문자 username / 값 = MutableUser(setPassword 가능)
```

## 3. 핵심 이름표

이 결함을 읽을 때 헷갈리는 것은 "비밀번호를 바꾸는 메서드"가 둘이고 "username"이 두 얼굴을 갖는다는 점이다.\
아래 표는 각 이름표가 **저장 키 쪽인지 원본 철자 쪽인지**를 명시한다.

> **저장 키 / 원본 철자** — 맵에 실제로 들어간 소문자 문자열과, 사용자가 등록할 때 쓴 대소문자 그대로의 문자열.\
> 예: `"User"`로 등록하면 저장 키는 `"user"`이고 원본 철자는 `"User"`이며, 이 결함은 둘을 뒤섞은 데서 나온다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `users` (`Map<String, MutableUserDetails>`) :61 | 인메모리 사용자 저장소. `HashMap`이라 null 키 조회를 허용한다 | 키는 항상 소문자 - 이 클래스의 암묵 계약 |
| `username.toLowerCase(Locale.ROOT)` | 저장 키를 만드는 정규화. 일곱 자리에서 반복된다 | `:153`에만 없었다 |
| `Authentication.getName()` :141 | 현재 인증 주체의 이름. 등록 당시의 **원본 철자**를 돌려준다 | 정규화 없이 그대로 조회 키가 됐다 |
| `changePassword(String, String)` :134 | `UserDetailsManager` - 현재 인증 사용자가 스스로 변경 | 결함이 있는 메서드 |
| `updatePassword(UserDetails, String)` :158 | `UserDetailsPasswordService` - 대상을 지목해 변경 | 이미 정규화한다(`:161`). 이름이 비슷한 기존 테스트가 검사하는 쪽 |
| `Assert.state(user != null, ...)` :154 | 조회 실패를 "있을 수 없는 상태"로 보고 | 결함을 사용자에게 모순된 메시지로 전달한다 |
| `MutableUser` | 값 래퍼. `setPassword`로 제자리 변경 가능 | 갱신 후 맵에 다시 put 하지 않는 이유 |

## 4. 결함 경로 - 저장과 조회가 갈리는 지점

발동 조건은 하나뿐이고, 그 조건 아래에서 연산별 결과가 갈린다.

| 연산 | 조회 키 | 대문자 username 사용자에서의 결과 |
|---|---|---|
| `loadUserByUsername("User")` :171 | `"user"` | 성공 - 로그인이 된다 |
| `userExists("User")` :130 | `"user"` | `true` |
| `updatePassword(userDetails, new)` :161 | `"user"` | 성공 |
| `deleteUser("User")` :114 | `"user"` | 성공 |
| `changePassword(old, new)` (수정 전) :153 | `"User"` | **`IllegalStateException`** |

한 행만 다르다는 것이 이 표의 요점이다.\
**사용자에게는 "계정이 정상인데 비밀번호 변경만 안 되는" 증상으로 보이고**, 예외 메시지("current user doesn't exist")는 원인을 조회 키가 아니라 저장소 상태 쪽으로 잘못 가리킨다.

같은 사용자 `"User"`에 대해 수정 전후의 다섯 연산 결과를 나란히 놓으면 이렇다.

```text
수정 전                                 수정 후
+-----------------------------+        +-----------------------------+
| loadUserByUsername   OK     |        | loadUserByUsername   OK     |
| userExists           true   |        | userExists           true   |
| updatePassword       OK     |        | updatePassword       OK     |
| deleteUser           OK     |        | deleteUser           OK     |
| changePassword       예외    |        | changePassword       OK     |
+-----------------------------+        +-----------------------------+
  한 줄만 빨갛다                          다섯 줄이 같은 답을 낸다
```

재인증 경로가 결함을 가리지 않는다는 점도 확인해 두었다.\
`authenticationManager`가 설정돼 있으면 `:147-148`이 원본 username으로 재인증하는데, 그 경로는 `users` 맵이 아니라 `UserDetailsService`를 거치고 그쪽은 `:171`에서 정규화한다.\
그래서 재인증은 통과하고 그 다음 줄에서 넘어진다.

## 5. 수정안과 대안 비교

채택안은 조회 키 정규화 한 줄이다.\
실제로 검토한 대안은 둘이었다.

| 대안 | 채택 | 사유 |
|---|---|---|
| `users.get(username.toLowerCase(Locale.ROOT))` | 채택 | 형제 일곱 자리와 동일. 최소 변경, 새 분기 없음, `Locale` 이미 임포트됨 |
| `getName()`을 한 번 소문자화해 재인증 입력에도 사용 | 기각 | 재인증은 `UserDetailsService`가 자체 정규화하는 별도 경로. 그 입력을 바꾸면 조회 버그 수정이 인증 입력 정책 변경이 된다 |
| null 가드 추가(`username != null ? ... : null`) | 기각 | 형제 `:161`·`:171`도 null 가드 없이 `toLowerCase`를 부른다. 이 메서드에만 가드를 넣으면 새 비대칭이 생긴다 - 5.1절 |

> **결합도와 비대칭** — 한 클래스 안에서 같은 일을 하는 자리들이 서로 다른 모양을 갖는 것.\
> 예: 형제 일곱이 전부 무방비인데 한 메서드만 null 가드를 갖게 되면, 다음 사람이 "왜 여기만 다른가"를 다시 조사해야 한다.

### 5.1 codex 교차검증에서 나온 유일한 반론

codex는 핵심 수정을 반박하지 못했고(판정: 승인) 지적 다섯 중 넷은 확인 또는 이미 충족이었다.\
남은 하나가 null 회귀 위험이다.\
`users`가 `HashMap`이므로 `getName()`이 null인 별난 `Authentication` 구현에서는 수정 전에 `users.get(null)` -> null -> `IllegalStateException`이 났는데, 수정 후에는 `null.toLowerCase(...)`가 먼저 `NullPointerException`을 던진다.

예외 종류가 어떻게 갈리는지를 나란히 놓으면 이렇다.

```text
getName() 이 null 인 별난 구현
수정 전                                 수정 후
+-----------------------------+        +-----------------------------+
| users.get(null)             |        | null.toLowerCase(ROOT)      |
|   HashMap 은 null 키 허용    |        |   -> NullPointerException   |
|   -> null 반환               |        |                             |
| Assert.state 실패            |        | (Assert.state 까지 못 간다)  |
|   -> IllegalStateException  |        |                             |
+-----------------------------+        +-----------------------------+
  실사용 경로는 아니다 - Principal 계약상 getName() 은 non-null 이다.
```

> **`Principal` 계약** — 자바 표준 인터페이스 `java.security.Principal`이 구현체에 요구하는 약속.\
> 예: `getName()`은 이름을 반드시 돌려주게 돼 있어서, null을 돌려주는 구현은 계약을 어긴 쪽이다.

사실 관계는 맞다.\
그럼에도 가드를 넣지 않은 근거는 셋이다.\
첫째, **클래스 전체가 비방어적**이라 형제 두 자리도 같은 위험을 이미 갖고 있다.\
둘째, `Authentication.getName()`은 `Principal` 계약상 non-null이라 실사용 경로가 아니다.\
셋째, 방어가 옳다는 판단이 선다면 그것은 한 메서드가 아니라 **클래스 전체를 대상으로 하는 별개 변경**이다.\
이 판단은 PR 본문에는 노이즈라 싣지 않고 작업 로그에만 남겼으며, 메인테이너가 지적하면 즉시 방어 버전으로 전환할 준비를 해 두었다.\
실제로는 지적 없이 머지됐다.

## 6. 검증 계획과 실측

계획은 "재현 테스트 red 확인 -> fix -> green + 회귀 0"이었고 그대로 됐다.

- **red**: 대문자 username + 인증 컨텍스트 -> `changePassword` -> `IllegalStateException("Current user doesn't exist in database.")`.\
  실측 확인.
- **green**: `InMemoryUserDetailsManagerTests` 18건 통과(`--rerun-tasks`), `provisioning` 패키지 회귀 0.
- **스타일**: `checkstyleMain/Test` + `checkFormatMain/Test` 통과.
- **중복 리서치**: 착수 전 `gh search issues/prs`로 동일 주제를 전수 확인했고 보고 이력이 없었다.\
  같은 라운드의 다른 후보 둘(C-01 IP 매처, C-02 리액티브 null 가드)은 이 검색에서 이미 남이 제출한 PR이 발견돼 드롭됐으므로, 이 절차가 형식이 아니라 실제로 걸러 냈다.
- **stakes 판정**: 중간.\
  인증된 사용자의 기능이 깨지지만 데이터 의미 변경이 아니고 방향이 fail-closed(과잉 차단)다.\
  그래서 검증 강도는 재현 테스트 + codex 교차검증 1회로 잡았고 듀얼 리뷰 루프는 돌리지 않았다.

> **중복 리서치** — 같은 문제를 이미 누가 보고했는지 착수 전에 훑어보는 절차.\
> 예: 여기서는 검색 결과 때문에 후보 둘이 실제로 취소됐으므로, 형식적인 단계가 아니었다.
