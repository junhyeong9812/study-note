# HttpFirewall

상위: [spi](../README.md)

필터들이 보게 될 요청과 응답을 정한다. 체인에 들어가기 전에 이상한 요청을 거르는 첫 관문이다.

## 위치

`web` / `org.springframework.security.web.firewall` / `HttpFirewall.java` L32-L47 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/firewall/HttpFirewall.java#L32-L47))

## 실제 코드

```java
// HttpFirewall.java L32-L47 (javadoc 생략)
public interface HttpFirewall {

    FirewalledRequest getFirewalledRequest(HttpServletRequest request) throws RequestRejectedException;

    HttpServletResponse getFirewalledResponse(HttpServletResponse response);

}
```

## 흐름에서 불리는 자리

```text
 FilterChainProxy.doFilterInternal
   L215 getFirewalledRequest(request)    거부 대상이면 여기서 예외
   L216 getFirewalledResponse(response)
```

- [FilterChainProxy.doFilterInternal](../../01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/README.md)

## 구현 계층

```text
 HttpFirewall
   +-- StrictHttpFirewall    기본. 수상한 요청을 거부한다
   +-- DefaultHttpFirewall   경로를 정규화(sanitize)해서 넘긴다
                             javadoc 이 StrictHttpFirewall 쪽을 권한다
   +-- (사용자 구현)

 둘의 차이는 강도가 아니라 방식이다
   고쳐서 통과시키는가, 아니면 거부하는가
```

## 결과가 쓰이는 곳

```text
 FirewalledRequest
      --> 체인 안 모든 필터가 보는 요청 객체다
      --> reset() 은 체인을 나갈 때 불리는 훅이다
          되돌릴 가공을 한 구현에서만 의미가 있고,
          StrictHttpFirewall 의 것은 빈 메서드다

 던진 RequestRejectedException
      --> doFilter 의 catch 가 원인 사슬에서 이것을 찾아
          RequestRejectedHandler 로 넘긴다
      --> 요청을 감쌀 때 거부되면 필터가 하나도 실행되지 않는다
      --> 헤더나 파라미터를 읽는 시점에도 거부가 터질 수 있다
          그때는 체인이 이미 돌고 있다. 원인 사슬을 펴는 이유이기도 하다
```
