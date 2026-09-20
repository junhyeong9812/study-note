# CsrfToken

상위: [spi](../README.md)

토큰 하나를 나타낸다. 값뿐 아니라 "어느 헤더와 어느 파라미터로 보내야 하는지"도 함께 들고 있다.

## 위치

`web` / `org.springframework.security.web.csrf` / `CsrfToken.java` L28-L50 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfToken.java#L28-L50))

## 실제 코드

```java
// CsrfToken.java L28-L50 (javadoc 생략)
public interface CsrfToken extends Serializable {

    String getHeaderName();

    String getParameterName();

    String getToken();

}
```

## 흐름에서 불리는 자리

```text
 CsrfFilter.doFilterInternal
   L126 csrfToken.getToken()   대조할 원본 값

 CsrfTokenRequestHandler 의 default resolveCsrfTokenValue
   L54 csrfToken.getHeaderName()     헤더 이름
   L61 csrfToken.getParameterName()  파라미터 이름
```

- [CsrfFilter.doFilterInternal](../../01_CsrfFilter.doFilterInternal/README.md)

## 구현 계층

```text
 CsrfToken (extends Serializable)
   +-- DefaultCsrfToken   값 셋을 담는 단순 구현
   +-- SupplierCsrfToken  CsrfTokenRequestAttributeHandler 내부 private
                          Supplier 를 감싸 실제 호출 시점에 위임한다

 서블릿 쪽 main 구현은 이 둘뿐이다
```

## 결과가 쓰이는 곳

```text
 getHeaderName / getParameterName
      --> 토큰이 자기를 어떻게 보내야 하는지 스스로 알려 준다
      --> 뷰와 자바스크립트가 이름을 하드코딩하지 않아도 된다

 getToken
      --> 대조의 기준값이다
      --> XOR 처리기는 이 값을 섞어 내보내고, 받을 때 풀어 다시 이 값과 비교한다

 Serializable 인 점
      --> HttpSessionCsrfTokenRepository 가 세션 속성에 그대로 담는다
      --> 쿠키 저장소는 값만 쓰므로 직렬화하지 않는다
```
