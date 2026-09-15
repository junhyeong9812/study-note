# PR #19335 - 착수 분석: anonymous()의 계약 위반

> 원본: fork repo의 `analyze-docs/plans/2026-06-14/spring-security-core-bug-hunt/`
> `C-05-authzfactory-anonymous-contract/`(task.md·해설.md·changelog.md·review-log.md).
> 학습 문서로 옮기면서 작업 진행용 절을 덜어내고 실측 근거를 절로 승격했다.
> 결론은 PR #19335로 반영됐다(커밋 `d73fa8d905`).
>
> **좌표 주의**: 본문의 file:line은 **수정 전** 파일 기준이다.
> 문제와 수정 요약은 [README.md](README.md), 실구조는 [structure.md](structure.md), 테스트는 [tests.md](tests.md).

## 0. 결론 먼저

`DefaultAuthorizationManagerFactory.anonymous()`가 `authenticated()`·`fullyAuthenticated()`·`rememberMe()`와 같은 `createManager` 경로를 타고, 그 경로 끝의 `withAdditionalAuthorization`이 부가 인가를 씌운다(`:147-150` -> `:162-165` -> `:167-172`).\
그런데 `setAdditionalAuthorization`의 javadoc은 이렇게 적혀 있다.

```java
 * This does not affect {@code anonymous}, {@code permitAll}, or {@code denyAll}.
```
(DefaultAuthorizationManagerFactory.java:93)

`permitAll`/`denyAll`은 이 클래스가 오버라이드하지 않은 인터페이스 default라 그 경로를 지나지 않으므로 계약을 지킨다.\
**`anonymous()`만 계약을 깬다.**\
결과는 MFA 같은 부가 인가를 켠 구성에서 익명 요청이 거부되는 것이고, 방향이 fail-closed라 권한 상승은 아니지만 문서가 약속한 것과 정반대다.\
수정은 `anonymous()`가 매니저를 직접 조립해 `withAdditionalAuthorization`을 건너뛰게 하는 것이다.

> **계약(contract)** — 코드가 "이렇게 동작한다"고 밖에 약속한 내용.\
> 예: 여기서는 javadoc의 "This does not affect anonymous" 한 문장이 계약이고, 코드가 그것을 어겼다.

> **fail-closed** — 어긋났을 때 열지 않고 잠그는 쪽으로 떨어지는 실패 방향.\
> 예: 익명 사용자가 통과해야 할 자리에서 거부된 것이라 권한 상승 사고는 아니지만, 정상 사용자가 못 들어온다.

## 1. 발견 경로 - 어떻게 찾았나

이 결함은 **문서와 코드를 나란히 놓는 감사**에서 나왔다.\
spring-security core의 `authorization` 패키지를 훑던 에이전트가 "javadoc이 세 메서드를 제외한다고 적었는데 그중 하나는 실제로 제외되지 않는다"를 보고했고(후보 ID C-05), 메인이 재현 테스트로 red를 확인했다.

> **재현 테스트** — 버그가 살아 있을 때 반드시 실패하도록 먼저 써 보는 테스트.\
> 예: fix 전에 red가 나오는 것을 눈으로 확인해야, fix 후의 green이 "고쳤다"의 증거가 된다.

코드만 읽어서는 이 결함이 보이지 않는다는 점이 중요하다.\
`anonymous()`가 형제 셋과 같은 헬퍼를 부르는 것은 코드 안에서 완벽하게 일관된 모습이고, 오히려 **일관돼 보이는 것이 결함**이다.\
위반 여부를 판정하는 근거가 코드 밖(javadoc)에 있으므로, 계약 문서를 읽지 않으면 정상 코드로 지나친다.

## 2. 무대 - 객체와 역할

결함은 팩토리의 출구 하나와 그 출구를 공유하는 네 메서드 사이에 있다.

```text
 설정
   AuthorizationManagerFactories.multiFactor().requireFactors(...)
   또는 factory.setAdditionalAuthorization(manager)                      :98-100
   |
   v
 DefaultAuthorizationManagerFactory<T>    core/.../DefaultAuthorizationManagerFactory.java
   |  trustResolver / roleHierarchy / rolePrefix / additionalAuthorization  :39-45
   |  hasRole 계열 -> createManager(AuthorityAuthorizationManager)          :152-155
   |  authenticated / fullyAuthenticated / rememberMe / anonymous
   |                -> createManager(AuthenticatedAuthorizationManager)     :162-165
   |  permitAll / denyAll -> 오버라이드 없음 (인터페이스 default)
   v
 withAdditionalAuthorization(manager)                                      :167-172
   |  additionalAuthorization == null 이면 그대로 반환
   |  아니면 allOf(new AuthorizationDecision(false), additional, manager)
   v
 AuthorizationManagers.allOf   core/.../AuthorizationManagers.java
      지연 평가 람다 - authorize 시점에 하위 매니저 순회               :110-127
      하나라도 !isGranted() 면 즉시 그 결과 반환                       :117-120
      전부 abstain 이면 첫 인자의 기본 결정(여기서는 deny)              :123-124
```

## 3. 핵심 이름표

이 결함을 읽을 때 헷갈리는 것은 "부가 인가가 적용된다"는 말이 **조립 시점**이 아니라 **판정 시점**의 사건이라는 점이다.\
아래 표는 각 이름표가 조립 쪽인지 판정 쪽인지를 명시한다.

> **조립 시점 / 판정 시점** — 매니저를 만들어 돌려주는 순간과, 그 매니저가 요청 하나를 심사하는 순간.\
> 예: `factory.anonymous()`가 조립 시점이고, 그 결과에 `authorize(...)`를 부르는 것이 판정 시점이다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `additionalAuthorization` :45 | 팩토리가 만드는 규칙에 AND로 끼우는 공통 조건. 기본값 null | null이면 결함이 발동하지 않는다 |
| `setAdditionalAuthorization` javadoc :76-97 | 적용 대상 아홉을 열거하고 `anonymous`/`permitAll`/`denyAll` 셋을 제외 | 이 PR이 근거로 삼은 계약 |
| `createManager(AuthenticatedAuthorizationManager)` :162-165 | trustResolver 주입 + 부가 인가 래핑을 **함께** 한다 | 두 관심사가 묶여 있어 "하나만 빼기"가 불가능했다 |
| `withAdditionalAuthorization` :167-172 | 실제 래핑 지점 | `anonymous()`가 여기 도달한 것이 결함 |
| `AuthorizationManagers.allOf` :108-127 | 조립 시점에는 람다만 만들고 판정 시점에 하위를 부른다 | **지연 평가** - 무효 테스트를 만든 원인 |
| `new AuthorizationDecision(false)` :171 | 전부 abstain일 때의 기본 결정 = 거부 | 스텁 없는 목이 abstain일 때 결과가 deny가 되는 이유 |
| `AuthenticationTrustResolver` :39 | "이 인증이 익명인가"를 판정하는 부품 | 수정이 **유지**해야 하는 주입 |
| `AuthorizationManagerFactory.anonymous()` default :142-143 | 팩토리 상태를 안 보고 bare 매니저 반환 | 수정 후 형태와 trustResolver 한 줄만큼 다르다 |

## 4. 결함 경로 - 언제 발동하고 무엇이 달라지나

발동 조건은 두 개의 결합이고, 둘 다 참일 때만 결과가 갈린다.

| 구성 | 부가 인가 설정 | 부가 인가의 익명 판정 | `anonymous()` 판정 (수정 전) | (수정 후) |
|---|---|---|---|---|
| 기본 | 없음(null) | - | grant | grant |
| 부가 인가가 익명에 grant | 있음 | grant | grant | grant |
| 부가 인가가 익명에 abstain | 있음 | abstain | **deny** (기본 결정) | grant |
| MFA 등 factor 요구 | 있음 | deny | **deny** | grant |

셋째 행이 특히 관측하기 어렵다.\
부가 인가가 명시적으로 거부한 것이 아니라 **판단을 보류했을 뿐인데** `allOf`의 기본 결정이 거부라서 최종 결과가 deny가 된다.

현실 시나리오는 넷째 행이다.\
로그인 페이지처럼 `anonymous()`로 보호한 진입점에 MFA 게이트를 켜면, 익명 사용자는 factor가 없어 막히고 인증 사용자는 `anonymous()` 자체가 막으므로 **양쪽이 다 닫힌다.**

그 "양쪽이 다 닫힌다"를 로그인 페이지 하나에 대고 그리면 이렇다.

```text
MFA 켜기 전 (/login 은 anonymous() 로 보호)     MFA 켠 뒤 (수정 전 코드)
+-----------------------------------+        +-----------------------------------+
| 익명 방문자   -> GRANT (들어감)     |        | 익명 방문자   -> DENY (factor 없음) |
| 로그인 사용자 -> DENY (익명 아님)   |        | 로그인 사용자 -> DENY (익명 아님)    |
+-----------------------------------+        +-----------------------------------+
  로그인 페이지가 열린다                        아무도 로그인 페이지에 못 간다
```

## 5. 수정안과 대안 비교

채택안은 `anonymous()`가 매니저를 직접 조립하고 trustResolver만 주입해 반환하는 것이다.

| 대안 | 채택 | 사유 |
|---|---|---|
| `anonymous()`가 `createManager`를 우회 | 채택 | `permitAll`/`denyAll`이 (오버라이드하지 않아) 우회하는 것과 같은 범주에 놓인다. 최소 변경, 의도가 코드에 드러남 |
| `withAdditionalAuthorization` 안에서 익명 매니저를 식별해 제외 | 기각 | 헬퍼가 임의의 `AuthorizationManager`에서 의미론적 의도를 추론해야 한다 - 타입 식별이 취약하고 결합도가 오른다. 셋 중 하나만 특별 취급하는 모양도 부자연스럽다 |
| 인터페이스 default를 그대로 쓰기(오버라이드 삭제) | 기각 | trustResolver 주입이 사라진다. 커스텀 trustResolver를 설정한 애플리케이션에서 익명 판정 기준이 팩토리 설정을 따르지 않게 된다 |
| javadoc을 코드에 맞춰 고치기 | 기각 | 코드 쪽이 fail-closed로 틀렸다는 판단. `permitAll`/`denyAll`이 문서대로 동작하므로 문서가 셋을 묶어 서술한 의도가 분명하고, 테스트도 그 의도를 이미 명시한다 |

> **결합도(coupling)** — 한쪽을 바꾸면 다른 쪽도 따라 바꿔야 하는 정도.\
> 예: 헬퍼가 인자의 구체 타입을 알아보기 시작하면, 새 매니저 타입이 생길 때마다 헬퍼도 손봐야 한다.

### 5.1 무효 테스트를 발견한 지점

착수 직후 "이미 테스트가 있는 것 아닌가"를 확인하다가 결함의 은폐물을 찾았다.\
`anonymousWhenAdditionalAuthorizationThenNotInvoked`(:125-134)는 이름도 의도도 정확한데 `factory.anonymous()`만 부르고 `verifyNoInteractions`를 검사한다.\
`allOf`가 지연 평가라 조립 시점에는 버그가 있어도 부가 인가가 호출되지 않으므로, **버그 상태에서 통과하는 테스트**였다.

이 발견이 테스트 전략을 결정했다.\
새 테스트를 추가하면 무효 테스트가 그대로 남아 다음 사람을 또 속이므로, 무효 테스트 자체에 `authorize` 호출과 grant 단언을 넣어 유효하게 만들었다.

### 5.2 codex 교차검증

판정은 승인이었고 반박은 없었다.\
지적 다섯 중 넷은 확인이었고 남은 하나는 기존 커버리지를 몰라서 나온 권고였다.

> **교차검증(cross-review)** — 같은 변경을 다른 도구·다른 맥락의 리뷰어에게 한 번 더 보게 하는 절차.\
> 예: 여기서는 diff만 건네받은 codex가 독립적으로 지적 다섯 건을 냈고, 그중 하나는 기존 테스트를 못 봐서 나온 권고였다.

- 확인: `anonymous()`만 바꿨으므로 `authenticated`/`fullyAuthenticated`/`rememberMe`는 여전히 부가 인가를 적용한다.
- 확인: 보존해야 할 것은 `setTrustResolver`이고 `roleHierarchy`는 이 타입에 무관하다.
- **채택**: 호환성 변화가 실재하지만 javadoc이 명시한 방향이다.\
  부가 인가를 넓은 요청 게이트(MFA / IP 허용 목록 / 테넌트 / 점검 모드)로 쓰면서 익명 경로에도 걸리기를 기대한 설정은 이제 다르게 동작한다.\
  둘 다 필요하면 `allOf(factory.anonymous(), extra)`로 명시 조합해야 한다.\
  -> **PR 본문 "Note on impact"로 선공개**하기로 결정.
- 기각: "미변경 메서드가 여전히 적용됨을 보장하는 테스트를 추가하라" - 기존 `hasRoleWhenAdditionalAuthorizationThenInvoked`(:158-171) 등이 이미 검증한다.\
  codex는 diff만 받아 이를 볼 수 없었다.
- 확인: 메서드별 우회가 헬퍼 내부 식별보다 명확하다.

## 6. 검증 계획과 실측

- **red**: `setAdditionalAuthorization(목)` 후 `anonymous().authorize(익명)` -> `Expecting value to be true but was false`.\
  실측 확인.
- **green**: `AuthorizationManagerFactoryTests` 31건 통과(`--rerun-tasks`), `authorization` 패키지 회귀 0.
- **스타일**: `checkstyleMain/Test` + `checkFormatMain/Test` 통과.
- **중복 리서치**: 부가 인가 기능을 도입한 PR #17942(머지됨)는 있으나 이 계약 위반을 보고한 이슈나 PR은 없었다.\
  신규 확인.
- **stakes 판정**: 중간.\
  프레임워크 인가 계약 위반이고 MFA 구성에서 익명 접근이 막히지만 방향이 fail-closed다.\
  검증 강도는 재현 테스트 + codex 교차검증 1회.
- **절차 선택**: 동작 변경을 포함하므로 이슈(gh-19334)를 먼저 등록하고 PR을 냈다.\
  순수 결함 수정이었던 같은 라운드의 #19337과 달리, 계약 해석 논의가 필요할 수 있다고 봤기 때문이다.\
  실제로 이 PR은 제출 후 석 달 가까이 `status: waiting-for-triage`에 있고 #19337은 두 달 만에 머지됐다.

> **stakes** — 이 변경이 틀렸을 때 잃는 것의 크기.\
> 예: 되돌리기 쉽고 영향 범위가 좁으면 낮음, 데이터가 지워지거나 권한이 열리면 높음이다.
