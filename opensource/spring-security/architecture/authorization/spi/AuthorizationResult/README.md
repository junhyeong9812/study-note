# AuthorizationResult

상위: [spi](../README.md)

판정 결과다. 메서드 하나뿐이지만 구현이 이유를 덧붙일 수 있다.

## 위치

`core` / `org.springframework.security.authorization` / `AuthorizationResult.java` L27-L35 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/AuthorizationResult.java#L27-L35))

## 실제 코드

```java
// AuthorizationResult.java L27-L35 (javadoc 생략)
public interface AuthorizationResult extends Serializable {

    boolean isGranted();

}
```

## 흐름에서 불리는 자리

```text
 AuthorizationFilter.doFilter
   L98 result != null && !result.isGranted()  이면 거부 예외
```

- [AuthorizationFilter.doFilter](../../01_AuthorizationFilter.doFilter/README.md)

## 구현 계층

```text
 AuthorizationResult (extends Serializable)
   +-- AuthorizationDecision            granted 만 담는다
   |     +-- AuthorityAuthorizationDecision   요구한 권한 목록도 담는다
   |     +-- ExpressionAuthorizationDecision  평가한 표현식을 담는다
   |     +-- (AuthorizationManagers 안의 합성 결과들)
   +-- FactorAuthorizationDecision      MFA 요소 판정
   +-- AuthorizationDeniedException     거부 예외가 곧 결과이기도 하다
```

## 결과가 쓰이는 곳

```text
 isGranted()
      --> 통과 여부를 가르는 유일한 기준이다

 Serializable 인 점
      --> 결과가 직렬화 경로를 탈 수 있다는 뜻이다

 이유를 담는 구현
      --> AuthorityAuthorizationDecision 은 요구했던 권한 목록을 들고 있다
      --> 거부 예외에 실려 올라가므로 핸들러가 응답에 쓸 수 있다
      --> 다만 그 정보를 그대로 노출하면 규칙을 알려 주는 셈이 된다
```
