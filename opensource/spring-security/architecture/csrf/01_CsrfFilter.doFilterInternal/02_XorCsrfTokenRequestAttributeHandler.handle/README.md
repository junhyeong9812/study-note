# XorCsrfTokenRequestAttributeHandler.handle

상위: [CsrfFilter.doFilterInternal](../README.md)

토큰을 요청 속성에 노출해 뷰가 쓸 수 있게 한다. 기본 처리기이고, 내보내는 값을 매번 다르게 만든다.

## 위치

`web` / `org.springframework.security.web.csrf` / `XorCsrfTokenRequestAttributeHandler.java` L58-L75 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/XorCsrfTokenRequestAttributeHandler.java#L58-L75))

## 실제 코드

```java
// XorCsrfTokenRequestAttributeHandler.java L58-L75
@Override
public void handle(HttpServletRequest request, HttpServletResponse response,
        Supplier<CsrfToken> deferredCsrfToken) {
    Assert.notNull(request, "request cannot be null");
    Assert.notNull(response, "response cannot be null");
    Assert.notNull(deferredCsrfToken, "deferredCsrfToken cannot be null");
    Supplier<CsrfToken> updatedCsrfToken = deferCsrfTokenUpdate(deferredCsrfToken);
    super.handle(request, response, updatedCsrfToken);
}

private Supplier<CsrfToken> deferCsrfTokenUpdate(Supplier<CsrfToken> csrfTokenSupplier) {
    return new CachedCsrfTokenSupplier(() -> {
        CsrfToken csrfToken = csrfTokenSupplier.get();
        Assert.state(csrfToken != null, "csrfToken supplier returned null");
        String updatedToken = createXoredCsrfToken(this.secureRandom, csrfToken.getToken());
        return new DefaultCsrfToken(csrfToken.getHeaderName(), csrfToken.getParameterName(), updatedToken);
    });
}
```

받는 쪽도 같은 클래스가 맡는다. 섞인 값을 풀어 원본을 돌려준다.

`web` / `org.springframework.security.web.csrf` / `XorCsrfTokenRequestAttributeHandler.java` L77-L84 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/XorCsrfTokenRequestAttributeHandler.java#L77-L84))

```java
// XorCsrfTokenRequestAttributeHandler.java L77-L84
@Override
public @Nullable String resolveCsrfTokenValue(HttpServletRequest request, CsrfToken csrfToken) {
    String actualToken = super.resolveCsrfTokenValue(request, csrfToken);
    if (actualToken == null) {
        return null;
    }
    return getTokenValue(actualToken, csrfToken.getToken());
}
```

## 동작 흐름

```text
 handle(request, response, deferredCsrfToken)
 |
 | L64 deferCsrfTokenUpdate(deferredCsrfToken)
 |      |
 |      +-- L69 CachedCsrfTokenSupplier 로 감싼다
 |             L70 원래 Supplier 에서 토큰을 꺼내고
 |             L72 createXoredCsrfToken(secureRandom, 원본)
 |             L73 헤더 이름과 파라미터 이름은 그대로 둔 채
 |                 값만 바꾼 DefaultCsrfToken 을 만든다
 |
 +-- L65 super.handle(request, response, 바꾼 Supplier)
        상위 클래스가 요청 속성에 심는다

 resolveCsrfTokenValue(request, csrfToken)   받을 때
 |
 | L79 super.resolveCsrfTokenValue(...)
 |      헤더를 먼저 보고 없으면 파라미터를 본다 (인터페이스 default)
 | L80 없으면 null
 |
 +-- L83 getTokenValue(actualToken, csrfToken.getToken())
        L89 Base64 URL 디코딩 -- 실패하면 null
        L98 길이가 원본의 두 배가 아니면 null
        그리고 XOR 를 풀어 원본을 돌려준다
```

```text
 왜 값을 매번 바꾸는가

 원본 토큰은 그대로 두고, 내보낼 때만 난수와 XOR 한다
 그래서 같은 세션이라도 응답마다 다른 문자열이 나간다

 클래스 javadoc 은 "매 요청마다 값을 가린다(masking)"고만 말한다
 목적을 밝힌 것은 레퍼런스 문서다 --
 servlet/exploits/csrf.adoc 이 BREACH 공격 방어라고 적고 있다

 서버는 받은 값에서 난수 부분을 떼어 내 원본을 복원하므로
 대조는 원본끼리 이루어진다
```

```text
 조용히 null 을 돌려주는 자리들

 Base64 디코딩 실패 (L89-94)
 길이가 안 맞음 (L98)

 둘 다 예외를 던지지 않고 null 을 돌려준다
 그러면 필터의 대조에서 실패해 정상적인 거부 경로를 탄다
 형식이 틀린 입력과 값이 틀린 입력이 같은 응답을 받는다
```

## 결과가 쓰이는 곳

```text
 요청 속성에 심긴 토큰
      --> 뷰 템플릿이 hidden 필드나 메타 태그에 넣는다
      --> Supplier 로 심기 때문에, 뷰가 실제로 쓸 때 값이 만들어진다

 헤더 우선 조회
      --> 인터페이스의 default 가 헤더를 먼저 본다
      --> AJAX 는 헤더로, 폼은 파라미터로 보내는 것이 자연스럽게 지원된다

 처리기를 바꾸는 경우
      --> XOR 를 쓰지 않으려면 CsrfTokenRequestAttributeHandler 를 꽂는다
          레퍼런스 문서가 BREACH 보호를 끄는 방법으로 이것을 든다
      --> SPA 는 csrf().spa() 를 쓴다. 그쪽은 쿠키 저장소와
          SpaCsrfTokenRequestHandler 를 한 번에 꽂는다
```
