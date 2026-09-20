# CsrfTokenRepository.loadDeferredToken

상위: [CsrfFilter.doFilterInternal](../README.md)

읽지 않고, 읽는 방법만 돌려준다. [보안 컨텍스트](../../../security-context/README.md)의 `loadDeferredContext` 와 같은 모양이다.

## 위치

`web` / `org.springframework.security.web.csrf` / `CsrfTokenRepository.java` L72-L74 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfTokenRepository.java#L72-L74))

## 실제 코드

인터페이스의 default 메서드이고, **이번에는 실제로 이 경로가 돈다.** 저장소 구현 중 이것을 오버라이드하는 것이 하나도 없다.

```java
// CsrfTokenRepository.java L72-L74
default DeferredCsrfToken loadDeferredToken(HttpServletRequest request, HttpServletResponse response) {
    return new RepositoryDeferredCsrfToken(this, request, response);
}
```

돌려주는 `RepositoryDeferredCsrfToken` 이 실제 일을 한다.

`web` / `org.springframework.security.web.csrf` / `RepositoryDeferredCsrfToken.java` L52-L75 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/RepositoryDeferredCsrfToken.java#L52-L75))

```java
// RepositoryDeferredCsrfToken.java L52-L75
@Override
public CsrfToken get() {
    init();
    return Objects.requireNonNull(this.csrfToken);
}

@Override
public boolean isGenerated() {
    init();
    return this.missingToken;
}

private void init() {
    if (this.csrfToken != null) {
        return;
    }

    this.csrfToken = this.csrfTokenRepository.loadToken(this.request);
    this.missingToken = (this.csrfToken == null);
    if (this.missingToken) {
        this.csrfToken = this.csrfTokenRepository.generateToken(this.request);
        this.csrfTokenRepository.saveToken(this.csrfToken, this.request, this.response);
    }
}
```

## 동작 흐름

```text
 loadDeferredToken(request, response)
 |
 +-- L73 RepositoryDeferredCsrfToken 을 만들어 돌려준다
        저장소, 요청, 응답을 들고만 있는다. 아직 아무것도 읽지 않는다

 누군가 get() 이나 isGenerated() 를 부르면
 |
 +-- L64 init()
        L65 이미 읽었으면 바로 return
        L69 csrfTokenRepository.loadToken(request)
        L70 결과가 null 이면 missingToken = true
        L71 그러면
              L72 generateToken(request)   새로 만들고
              L73 saveToken(...)           저장소에 저장한다
```

```text
 읽기만 하는 것이 아니다

 init() 은 토큰이 없으면 만들어서 저장까지 한다 (L72-73)

 그래서 "토큰을 꺼내 보는 행위"가 세션을 만들 수 있다
 GET 으로 폼 페이지를 여는 순간 세션이 생기는 이유가 이것이다

 반대로 아무도 토큰을 꺼내지 않으면 저장소를 건드리지 않는다
```

```text
 get 과 isGenerated 가 같은 init 을 탄다

 둘 중 무엇을 먼저 부르든 읽기는 한 번만 일어난다
 L65 의 캐시가 막는다

 CsrfFilter 는 L121 에서 get() 을 부르고
 대조에 실패했을 때만 L127 에서 isGenerated() 를 부른다
 그때는 이미 읽혀 있어 저장소를 다시 치지 않는다
```

## 결과가 쓰이는 곳

```text
 돌려준 DeferredCsrfToken
      --> 필터가 요청 속성에 심어 뒤쪽과 공유한다
      --> 처리기에도 그대로 넘어가 뷰에 노출된다

 missingToken 플래그
      --> 저장소에 없어서 새로 만든 것인지 알려 준다
      --> MissingCsrfTokenException 과 InvalidCsrfTokenException 을 가른다

 기본 저장소
      --> CsrfConfigurer 의 기본값은 HttpSessionCsrfTokenRepository 다
      --> 쿠키로 내보내려면 CookieCsrfTokenRepository 로 바꾼다
          SPA 처럼 서버 렌더링을 쓰지 않는 쪽이 그렇게 한다
```
