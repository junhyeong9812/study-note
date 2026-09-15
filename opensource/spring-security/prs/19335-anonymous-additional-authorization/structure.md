# PR #19335 - 무대의 실구조와 워크플로우

> PR #19335의 무대가 되는 실구조와 워크플로우.
> 문제와 수정은 [README.md](README.md), 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: fork `main`(`ed7ae7969ed`) - **수정 전** 상태다.
> 아래 file:line은 별도 표시가 없으면 수정 전 좌표이고, 수정은 `anonymous()` 한 메서드(`:147-150` -> `:147-155`)다.

## 1. 무대 - 실구조

이 결함의 무대는 **인가 규칙을 찍어 내는 공장과 그 출구에 놓인 래핑 헬퍼 하나**다.\
공장은 열두 개 넘는 메서드를 갖고 있지만, 결함을 이해하는 데 필요한 것은 "어느 메서드가 어느 출구로 나가는가" 하나뿐이다.\
층을 위에서 아래로 그리면 이렇다.

```text
+------------------------------------------------------------------------------+
| 설정 진입점                                                                   |
|   AuthorizationManagerFactories.multiFactor().requireFactors(...)            |
|   또는 직접 factory.setAdditionalAuthorization(manager)              :98-100  |
|   -> 이것을 설정하지 않으면(null) 이 결함은 존재하지 않는다                     |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| AuthorizationManagerFactory (인터페이스)   core/.../authorization/...Factory.java
|   default permitAll()  -> SingleResultAuthorizationManager.permitAll()  :34-36|
|   default denyAll()    -> SingleResultAuthorizationManager.denyAll()    :42-44|
|   default anonymous()  -> AuthenticatedAuthorizationManager.anonymous() :142-143
|   default hasRole/authenticated/... (구현체가 오버라이드)                     |
|                                                                              |
|   ** default 구현은 팩토리 상태를 전혀 안 본다 - 부가 인가도, trustResolver도 ** |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| DefaultAuthorizationManagerFactory<T>   core/.../DefaultAuthorizationManagerFactory.java
|                                                                              |
|  [상태]                                                                       |
|    AuthenticationTrustResolver trustResolver                          :39     |
|    RoleHierarchy roleHierarchy = new NullRoleHierarchy()              :41     |
|    String rolePrefix = "ROLE_"                                        :43     |
|    AuthorizationManager<T> additionalAuthorization (nullable)         :45     |
|                                                                              |
|  [오버라이드하는 메서드 - 전부 createManager 를 거친다]                          |
|    hasRole/hasAnyRole/hasAllRoles/hasAuthority/...       :102-130            |
|    authenticated()                                       :132-135            |
|    fullyAuthenticated()                                  :137-140            |
|    rememberMe()                                          :142-145            |
|    anonymous()                                           :147-150   <- 결함   |
|                                                                              |
|  [오버라이드하지 않는 메서드]                                                   |
|    permitAll() / denyAll()  -> 인터페이스 default 그대로                       |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| createManager 오버로드 3종 - 타입별로 다른 부품을 주입한 뒤 같은 출구로 나간다      |
|                                                                              |
|   createManager(AuthorityAuthorizationManager)         :152-155              |
|     setRoleHierarchy(this.roleHierarchy)                                     |
|   createManager(AllAuthoritiesAuthorizationManager)    :157-160              |
|     setRoleHierarchy(this.roleHierarchy)                                     |
|   createManager(AuthenticatedAuthorizationManager)     :162-165              |
|     setTrustResolver(this.trustResolver)                                     |
|                                                                              |
|   ** 셋 모두 마지막 줄이 return withAdditionalAuthorization(manager) **        |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| withAdditionalAuthorization(manager)                                  :167-172|
|   additionalAuthorization == null 이면 manager 그대로 반환             :168-170|
|   아니면 AuthorizationManagers.allOf(                                  :171   |
|             new AuthorizationDecision(false),   <- 전부 abstain 시 거부        |
|             this.additionalAuthorization,                                    |
|             manager)                                                         |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| AuthorizationManagers.allOf   core/.../authorization/AuthorizationManagers.java|
|   반환값은 지연 평가 람다 - authorize 시점에야 하위 매니저를 부른다      :110-127|
|     각 매니저를 순회하며 authorize                                     :113-116|
|     null(abstain) 이면 건너뜀 / !isGranted() 면 즉시 그 결과 반환      :117-120|
|     전부 abstain 이면 allAbstainDefaultDecision 반환                   :123-124|
|     하나도 deny 없으면 CompositeAuthorizationDecision(true, ...)       :126   |
+------------------------------------------------------------------------------+
```

> **abstain(기권)** — 인가 매니저가 "나는 판단하지 않겠다"는 뜻으로 `null`을 돌려주는 것.\
> 예: 스텁을 주지 않은 목 객체는 기본 반환값이 `null`이라 언제나 abstain한다.

> **지연 평가 람다** — 당장 계산하지 않고, 나중에 불릴 때 계산하도록 감싸 둔 함수 객체.\
> 예: `allOf(...)`가 돌려주는 매니저는 `authorize`가 불리기 전까지 하위 매니저를 건드리지 않는다.

## 2. 워크플로우 - 익명 요청 한 번의 판정

수정 전과 수정 후의 차이는 **조립 단계에서 갈리고 판정 단계에서 드러난다.**\
두 단계를 나눠 따라가는 것이 이 결함의 관측 시점 문제를 이해하는 열쇠다.

```text
[조립]  factory.setAdditionalAuthorization(factors)  이미 설정됨
        factory.anonymous()

   수정 전                                   수정 후
   createManager(anonymous매니저)            AuthenticatedAuthorizationManager.anonymous()
     setTrustResolver                          setTrustResolver
     withAdditionalAuthorization               (래핑 없음)
   반환: allOf(false, factors, 익명매니저)     반환: 익명매니저

   ** 이 시점에는 어느 쪽도 factors 를 호출하지 않는다 - allOf 가 지연 평가라서다.
      기존 테스트가 여기서 verifyNoInteractions 를 검사해 통과했던 자리. **

[판정]  manager.authorize(() -> 익명인증, obj)

   수정 전                                   수정 후
     allOf 람다 진입          :113             익명매니저.authorize
     factors.authorize -> deny                   trustResolver.isAnonymous(익명) -> true
     !isGranted() 이므로 즉시 반환 :118-120      -> GRANT
     익명매니저는 평가조차 안 됨
     -> DENY                                   (부가 인가는 애초에 없다)
```

수정 전 흐름에서 **익명 매니저가 호출조차 되지 않는다**는 점이 이 결함의 성격을 말해 준다.\
`allOf`는 첫 deny에서 단락하므로, 목록의 앞쪽에 있는 부가 인가가 거부하면 뒤쪽의 실제 규칙은 판정에 참여하지 못한다.

> **단락 평가(short-circuit)** — 결과가 확정되는 순간 나머지를 건너뛰고 끝내는 평가 방식.\
> 예: `allOf`가 첫 매니저에서 deny를 보면 그 뒤 매니저들은 아예 실행하지 않는다.

## 3. 계약이 제외한 셋 - 같은 결과, 서로 다른 경로

`setAdditionalAuthorization`의 javadoc은 `anonymous`, `permitAll`, `denyAll` 셋을 비적용 대상으로 명시한다(`:93`).\
셋이 그 계약을 지키는(또는 어기는) 방식은 서로 다르다.\
아래 표는 같은 차원(오버라이드 여부, 어느 출구로 나가는가, 계약 준수)으로 셋을 비교한다.

| 메서드 | `DefaultAuthorizationManagerFactory`가 오버라이드하나 | 출구 | 수정 전 계약 |
|---|---|---|---|
| `permitAll()` | 아니오 - 인터페이스 default :34-36 | 래핑 없음 | 지킴 (구조적으로) |
| `denyAll()` | 아니오 - 인터페이스 default :42-44 | 래핑 없음 | 지킴 (구조적으로) |
| `anonymous()` | 예 :147-150 | `createManager` -> `withAdditionalAuthorization` | **깨짐** |
| `authenticated()` | 예 :132-135 | 같은 출구 | (적용 대상이라 정상) |

같은 계약 아래 놓인 셋이 수정 전후로 어느 범주에 있는지를 나란히 놓으면 이렇다.

```text
수정 전                                   수정 후
+-----------------------------+          +-----------------------------+
| 래핑 없는 쪽                 |          | 래핑 없는 쪽                 |
|   permitAll                 |          |   permitAll                 |
|   denyAll                   |          |   denyAll                   |
+-----------------------------+          |   anonymous  <- 옮겨 옴      |
| 래핑 타는 쪽                 |          +-----------------------------+
|   hasRole / authenticated   |          | 래핑 타는 쪽                 |
|   fullyAuthenticated        |          |   hasRole / authenticated   |
|   rememberMe                |          |   fullyAuthenticated        |
|   anonymous  <- 계약 위반    |          |   rememberMe                |
+-----------------------------+          +-----------------------------+
```

수정은 `anonymous()`를 표의 첫 두 행과 같은 범주로 옮긴다.\
다만 완전히 같지는 않다 - `permitAll`/`denyAll`은 팩토리 상태를 전혀 안 보는 반면, 수정 후 `anonymous()`는 `trustResolver`를 계속 주입한다.

## 4. `anonymous()`가 trustResolver를 필요로 하는 이유

부가 인가만 떼고 `setTrustResolver`는 남긴 판단의 근거가 매니저의 동작에 있다.\
`AuthenticatedAuthorizationManager.anonymous()`가 만드는 매니저는 "이 인증이 익명인가"를 판정해야 하고, 그 판정을 `AuthenticationTrustResolver`에게 위임한다.\
애플리케이션이 커스텀 trustResolver를 팩토리에 설정했다면(`:52-55`) 그 판정 기준도 바뀌어야 하므로, 팩토리가 만든 매니저는 팩토리의 trustResolver를 들고 나가야 한다.

> **위임(delegation)** — 어떤 일을 자기가 하지 않고 들고 있는 다른 객체에게 시키는 것.\
> 예: 익명 매니저는 "익명인가"를 스스로 판정하지 않고 `trustResolver.isAnonymous(...)`에게 물어본다.

`roleHierarchy`는 넘기지 않는다.\
이 타입에는 그것을 받는 setter가 없고, 원래 `createManager(AuthenticatedAuthorizationManager)` 오버로드(`:162-165`)도 trustResolver만 주입했다.\
권한 계층은 `AuthorityAuthorizationManager` 계열이 쓰는 부품이라 `createManager`의 다른 두 오버로드(`:152-160`)에서만 주입된다.

> **오버로드(overload)** — 이름은 같고 인자 타입만 다른 메서드 여러 벌.\
> 예: `createManager`는 인자 타입에 따라 세 벌이 있고, 벌마다 주입하는 부품이 다르다.

결과적으로 수정 후 `anonymous()`는 인터페이스 default(`AuthorizationManagerFactory.java:142-143`)와 **trustResolver 주입 한 줄만큼** 다르다.\
그 한 줄이 "인터페이스 default를 그대로 쓰면 되지 않나"라는 더 짧은 대안을 배제하는 이유다.
