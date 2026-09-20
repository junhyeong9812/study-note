# CSRF 방어

다른 사이트가 사용자의 쿠키를 이용해 요청을 위조하는 것을 막는다. 서버가 발급한 토큰을 요청에 함께 실어야만 통과시키는 방식이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 토큰 저장소와 요청 처리기 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 필터 체인의 앞쪽 (인증보다도 앞이다)
 |
 +-- [01] CsrfFilter.doFilterInternal
          저장소에서 지연된 토큰을 받는다
          요청 속성에 심어 두고 처리기에 넘긴다
          보호 대상이 아닌 메서드면 그냥 통과시킨다
          대상이면 요청에서 토큰을 꺼내 대조한다
          대조는 MessageDigest.isEqual 로 한다 (equalsConstantTime L194-205)
          |
          +-- [01-01] CsrfTokenRepository.loadDeferredToken
          |        지금 읽지 않는다. 읽는 방법만 돌려준다
          |        없으면 새로 만든다는 표시도 함께 들고 있다
          |
          +-- [01-02] XorCsrfTokenRequestAttributeHandler.handle
                   요청 속성에 토큰을 노출한다 (뷰가 폼에 심을 수 있게)
                   내보내는 값은 매번 XOR 로 달라진다
```

```text
 보호 대상은 메서드로 가른다

 DEFAULT_CSRF_MATCHER = DefaultRequiresCsrfMatcher
   allowedMethods = { GET, HEAD, TRACE, OPTIONS }
   matches(request) = 이 목록에 없는 메서드이면 true

 즉 POST, PUT, PATCH, DELETE 가 보호 대상이다
 경로가 아니라 메서드로 가른다

 조회는 부작용이 없다는 전제에 기댄 규칙이다
 GET 으로 상태를 바꾸는 API 를 만들면 이 방어가 비껴간다
```

```text
 토큰이 두 값으로 존재한다

 저장된 값   저장소(기본은 세션)에 있는 원본
 내보낸 값   XOR 로 섞어 매번 다르게 만든 것

 브라우저는 내보낸 값을 폼이나 헤더에 담아 보낸다
 서버는 그것을 받아 다시 풀어 원본과 대조한다

 같은 원본이 매 응답마다 다른 문자열로 나가므로
 응답 본문에서 토큰을 추출하는 공격(BREACH)이 어려워진다
```

```text
 두 실패가 다른 예외다

 MissingCsrfTokenException  저장소에 토큰이 아예 없었다
                            (isGenerated 가 true -- 방금 만든 것)
 InvalidCsrfTokenException  있었는데 값이 다르다

 앞의 것은 보통 세션이 만료된 경우다
 그래서 "세션이 끊겼습니다"와 "위조된 요청입니다"를 구분해 응답할 수 있다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 체인의 앞쪽 칸이다. 인증보다도 먼저 돈다
 [예외 변환] 실패는 예외를 던지지 않고 AccessDeniedHandler 를 직접 부른다
 [폼 로그인] 로그인 요청도 POST 라 CSRF 보호 대상이다
```

이 필터가 체인의 어디에 있는지는 [필터 체인](../filter-chain/README.md), 거부 핸들러 계약은 [예외 변환](../exception-translation/README.md)에 있다.

## 단계

1. [CsrfFilter.doFilterInternal](01_CsrfFilter.doFilterInternal/README.md)이 토큰을 대조한다.
2. [CsrfTokenRepository.loadDeferredToken](01_CsrfFilter.doFilterInternal/01_CsrfTokenRepository.loadDeferredToken/README.md)이 읽는 방법을 만든다.
3. [XorCsrfTokenRequestAttributeHandler.handle](01_CsrfFilter.doFilterInternal/02_XorCsrfTokenRequestAttributeHandler.handle/README.md)이 토큰을 노출한다.

## 결과가 쓰이는 곳

```text
 요청 속성 두 개가 생긴다
      --> 필터가 심는 DeferredCsrfToken 속성은
          웹소켓 핸드셰이크(CsrfTokenHandshakeInterceptor)가 읽는다
      --> 처리기가 심는 CsrfToken 속성을 뷰가 읽는다
          CsrfRequestDataValueProcessor 가 그 값으로 hidden 필드를 만든다

 지연 로딩
      --> 아무도 토큰을 꺼내 보지 않으면 저장소를 읽지 않는다
      --> 보호 대상이 아닌 GET 요청은 세션을 건드리지 않을 수 있다

 대조 실패
      --> 체인이 끊긴다. 뒤의 필터도 컨트롤러도 실행되지 않는다
      --> 예외를 던지는 것이 아니라 핸들러를 직접 부른다
          그래서 ExceptionTranslationFilter 를 거치지 않는다

 skipRequest
      --> 요청 속성으로 이 필터를 건너뛰게 만드는 정적 메서드다
      --> main 소스의 실제 사용처는 MockMvc 의 jwt() 와 opaqueToken()
          후처리기다. Bearer 토큰 요청에서 CSRF 를 빼기 위해 쓴다
```

## 다루지 않는 것

`CookieCsrfTokenRepository`의 쿠키 옵션과 SPA 연동, `CsrfAuthenticationStrategy`(로그인 시 토큰 교체), `CsrfLogoutHandler`, `RepositoryDeferredCsrfToken`과 `SupplierCsrfToken`의 지연 구현 세부, `CsrfTokenRequestAttributeHandler`와 XOR 변형의 인코딩 알고리즘, 그리고 `CsrfConfigurer`가 거부 핸들러를 조합하는 방식은 같은 뼈대의 곁가지라 요약만 했다. CSRF 공격 자체의 원리와 SameSite 쿠키 같은 브라우저 차원의 방어도 범위 밖이다.

## 하위 메서드

- [01 CsrfFilter.doFilterInternal](01_CsrfFilter.doFilterInternal/README.md)
- [spi](spi/README.md) — 토큰 저장소, 요청 처리기, 토큰
