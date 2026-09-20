# RoleHierarchy

상위: [spi](../README.md)

권한 대조 직전에 목록을 부풀린다. "상위 역할은 하위 역할을 포함한다"를 구현하는 자리다.

## 위치

`core` / `org.springframework.security.access.hierarchicalroles` / `RoleHierarchy.java` L28-L46 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/access/hierarchicalroles/RoleHierarchy.java#L28-L46))

## 실제 코드

```java
// RoleHierarchy.java L28-L46 (javadoc 생략)
public interface RoleHierarchy {

    Collection<? extends GrantedAuthority> getReachableGrantedAuthorities(
            Collection<? extends GrantedAuthority> authorities);

}
```

## 흐름에서 불리는 자리

```text
 AuthoritiesAuthorizationManager.getGrantedAuthorities
   L84 roleHierarchy.getReachableGrantedAuthorities(authentication.getAuthorities())
```

- [AuthoritiesAuthorizationManager.authorize](../../03_AuthoritiesAuthorizationManager.authorize/README.md)

## 구현 계층

```text
 RoleHierarchy
   +-- NullRoleHierarchy   기본. 받은 것을 그대로 돌려준다
   +-- RoleHierarchyImpl   계층 정의를 읽어 펼친다
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 펼쳐진 권한 목록
      --> 대조는 이 목록을 상대로 이루어진다
      --> 사용자가 실제로 들고 있는 권한 목록과 다를 수 있다

 기본이 NullRoleHierarchy 인 점
      --> 설정하지 않으면 계층이 없다
      --> ROLE_ADMIN 을 가진 사용자가 hasRole("USER") 규칙에서 막힌다

 대조 시점이 아니라 목록 시점에 끼어드는 점
      --> 매니저는 계층을 모른다. 그냥 목록을 대조할 뿐이다
      --> 그래서 계층을 바꿔도 매니저 구현은 그대로다
