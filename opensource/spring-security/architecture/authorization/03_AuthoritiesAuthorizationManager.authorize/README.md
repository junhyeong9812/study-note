# AuthoritiesAuthorizationManager.authorize

상위: [인가](../README.md)

권한 문자열을 대조해 통과 여부를 정한다. `hasRole` 과 `hasAuthority` 가 최종적으로 닿는 곳이다.

## 위치

`core` / `org.springframework.security.authorization` / `AuthoritiesAuthorizationManager.java` L59-L85 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/AuthoritiesAuthorizationManager.java#L59-L85))

## 실제 코드

```java
// AuthoritiesAuthorizationManager.java L59-L85
@Override
public AuthorizationResult authorize(Supplier<? extends @Nullable Authentication> authentication,
        Collection<String> authorities) {
    boolean granted = isGranted(authentication.get(), authorities);
    return new AuthorityAuthorizationDecision(granted, AuthorityUtils.createAuthorityList(authorities));
}

private boolean isGranted(Authentication authentication, Collection<String> authorities) {
    return authentication != null && isAuthorized(authentication, authorities);
}

private boolean isAuthorized(Authentication authentication, Collection<String> authorities) {
    for (GrantedAuthority grantedAuthority : getGrantedAuthorities(authentication)) {
        String authority = grantedAuthority.getAuthority();
        if (authority == null) {
            continue;
        }
        if (authorities.contains(authority)) {
            return true;
        }
    }
    return false;
}

private Collection<? extends GrantedAuthority> getGrantedAuthorities(Authentication authentication) {
    return this.roleHierarchy.getReachableGrantedAuthorities(authentication.getAuthorities());
}
```

## 동작 흐름

```text
 authorize(authentication, authorities)
 |
 | L62 isGranted(authentication.get(), authorities)
 |      |
 |      +-- L67 authentication 이 null 이 아니고 isAuthorized 이면 true
 |             |
 |             +-- L71 getGrantedAuthorities(authentication) 를 훑는다
 |                    L84 roleHierarchy.getReachableGrantedAuthorities(...)
 |                          상위 역할이 하위를 포함하도록 펼친다
 |                    L73 권한 문자열이 null 이면 건너뛴다
 |                    L76 요구 목록에 들어 있으면 true
 |             +-- L80 하나도 없으면 false
 |
 +-- L63 AuthorityAuthorizationDecision(granted, 요구한 권한 목록)
```

```text
 hasRole 은 접두를 붙인 hasAuthority 다

 AuthorityAuthorizationManager.hasAnyRole(roles)
   L96 hasAnyRole(ROLE_PREFIX, roles)
   L111 hasAnyAuthority(toNamedRolesArray(rolePrefix, roles))

 hasRole("ADMIN") 과 hasAuthority("ROLE_ADMIN") 은 같은 것이 된다
 대조 자체는 문자열 비교 하나뿐이다
```

```text
 OR 이지 AND 가 아니다

 L76 authorities.contains(authority) 에서 하나라도 맞으면 즉시 true

 hasAnyRole("ADMIN", "MANAGER")  둘 중 하나면 통과

 "둘 다" 를 요구하는 것은 별도 구현이 맡는다
 AllAuthoritiesAuthorizationManager 가 같은 패키지에 있다
```

```text
 RoleHierarchy 가 끼어드는 자리

 L84 roleHierarchy.getReachableGrantedAuthorities(authentication.getAuthorities())

 기본값은 NullRoleHierarchy 다 (L40)
 아무것도 펼치지 않고 받은 권한을 그대로 돌려준다

 계층을 설정하면 ROLE_ADMIN 하나로
 ROLE_USER 를 요구하는 규칙도 통과하게 만들 수 있다
 대조하기 전에 목록을 부풀리는 방식이다
```

## 결과가 쓰이는 곳

```text
 AuthorityAuthorizationDecision
      --> isGranted() 와 함께 "요구했던 권한 목록"을 들고 있다
      --> 거부 예외에 담겨 올라가므로
          핸들러가 무엇이 부족했는지 응답에 담을 수 있다

 authentication.get()
      --> 이 매니저는 Supplier 를 반드시 get() 한다
      --> 즉 권한 기반 규칙이 걸린 경로는 SecurityContext 를 실제로 읽는다

 null 인 권한 문자열
      --> L73 에서 건너뛴다. 대조 대상에서 빠진다

 익명 사용자
      --> authentication 이 null 이 아니라 익명 토큰이다
      --> ROLE_ANONYMOUS 만 가지므로 대부분의 규칙에서 false 가 된다
```
