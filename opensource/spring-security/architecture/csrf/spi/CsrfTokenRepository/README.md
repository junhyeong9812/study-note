# CsrfTokenRepository

상위: [spi](../README.md)

토큰을 만들고, 저장하고, 꺼낸다. 어디에 둘지가 이 구현에 달려 있다.

## 위치

`web` / `org.springframework.security.web.csrf` / `CsrfTokenRepository.java` L34-L76 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfTokenRepository.java#L34-L76))

## 실제 코드

```java
// CsrfTokenRepository.java L34-L76 (javadoc 생략)
public interface CsrfTokenRepository {

    CsrfToken generateToken(HttpServletRequest request);

    void saveToken(@Nullable CsrfToken token, HttpServletRequest request, HttpServletResponse response);

    @Nullable CsrfToken loadToken(HttpServletRequest request);

    default DeferredCsrfToken loadDeferredToken(HttpServletRequest request, HttpServletResponse response) {
        return new RepositoryDeferredCsrfToken(this, request, response);
    }

}
```

## 흐름에서 불리는 자리

```text
 CsrfFilter.doFilterInternal
   L110 tokenRepository.loadDeferredToken(request, response)

 그 안의 RepositoryDeferredCsrfToken.init 이
   L69 loadToken     저장소에서 꺼낸다
   L72 generateToken 없으면 만든다
   L73 saveToken     만든 것을 저장한다
```

- [CsrfTokenRepository.loadDeferredToken](../../01_CsrfFilter.doFilterInternal/01_CsrfTokenRepository.loadDeferredToken/README.md)

## 구현 계층

```text
 CsrfTokenRepository
   +-- HttpSessionCsrfTokenRepository   기본. 세션 속성에 담는다
   +-- CookieCsrfTokenRepository        쿠키로 내보낸다
   +-- (사용자 구현)

 loadDeferredToken 은 인터페이스의 default 인데
 두 구현 모두 오버라이드하지 않는다. default 가 실제로 도는 경로다
```

## 결과가 쓰이는 곳

```text
 loadDeferredToken
      --> 읽는 방법만 돌려준다. 이 시점에 저장소를 건드리지 않는다
      --> 돌려주는 RepositoryDeferredCsrfToken 이 나중에 읽고, 없으면 만들어 저장한다

 saveToken 에 null 을 넘기는 것
      --> javadoc 이 "삭제와 같다"고 밝힌다
      --> 로그아웃 시 토큰을 지우는 경로가 이것을 쓴다

 쿠키 저장소를 고르는 경우
      --> 서버가 뷰를 렌더링하지 않는 SPA 에서 쓴다
      --> 자바스크립트가 쿠키를 읽어 헤더에 실어 보내는 구조가 된다
```
