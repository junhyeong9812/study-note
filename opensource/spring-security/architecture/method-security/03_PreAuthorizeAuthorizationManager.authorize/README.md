# PreAuthorizeAuthorizationManager.authorize

상위: [메서드 보안](../README.md)

`@PreAuthorize("hasRole('ADMIN')")` 의 문자열이 실제로 평가되는 곳이다. 문장 다섯 개짜리 메서드다.

## 위치

`core` / `org.springframework.security.authorization.method` / `PreAuthorizeAuthorizationManager.java` L80-L89 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/PreAuthorizeAuthorizationManager.java#L80-L89))

## 실제 코드

```java
// PreAuthorizeAuthorizationManager.java L80-L89
@Override
public @Nullable AuthorizationResult authorize(Supplier<? extends @Nullable Authentication> authentication,
        MethodInvocation mi) {
    ExpressionAttribute attribute = this.registry.getAttribute(mi);
    if (attribute == null) {
        return null;
    }
    EvaluationContext ctx = this.registry.getExpressionHandler().createEvaluationContext(authentication, mi);
    return ExpressionUtils.evaluate(attribute.getExpression(), ctx, authentication, mi);
}
```

거부됐을 때의 처리도 이 클래스가 들고 있다.

`core` / `org.springframework.security.authorization.method` / `PreAuthorizeAuthorizationManager.java` L91-L97 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/PreAuthorizeAuthorizationManager.java#L91-L97))

```java
// PreAuthorizeAuthorizationManager.java L91-L97
@Override
public @Nullable Object handleDeniedInvocation(MethodInvocation methodInvocation,
        AuthorizationResult authorizationResult) {
    ExpressionAttribute attribute = this.registry.getAttribute(methodInvocation);
    PreAuthorizeExpressionAttribute preAuthorizeAttribute = (PreAuthorizeExpressionAttribute) attribute;
    return preAuthorizeAttribute.getHandler().handleDeniedInvocation(methodInvocation, authorizationResult);
}
```

## 동작 흐름

```text
 authorize(authentication, mi)
 |
 | L83 registry.getAttribute(mi)
 |      그 메서드의 @PreAuthorize 표현식을 찾아 온다
 |
 +-- L84 없으면 L85 null 을 돌려준다
 |        인터셉터가 이것을 통과로 다룬다
 |
 | L87 createEvaluationContext(authentication, mi)
 |      표현식이 볼 수 있는 것들을 담은 문맥이다
 |
 +-- L88 ExpressionUtils.evaluate(표현식, 문맥, authentication, mi)
```

```text
 레지스트리가 캐시 역할을 한다

 getAttribute 가 메서드마다 표현식을 찾아 준다
 애노테이션을 매번 리플렉션으로 읽지 않도록 ConcurrentHashMap 에 모아 둔다
 다만 computeIfAbsent 라 null 은 캐시하지 않는다
 애노테이션이 없는 메서드는 호출할 때마다 다시 스캔한다

 애노테이션이 없으면 null 을 돌려주고,
 그 판정이 곧 "이 메서드는 검사 대상이 아니다"가 된다
```

```text
 평가 문맥에 무엇이 담기는가

 authentication   표현식 루트 객체의 principal, authentication 프로퍼티
 mi               메서드 인자에 #이름 으로 접근하는 통로

 그래서 @PreAuthorize("#id == authentication.name") 같은 식이 가능하다
 메서드 인자와 현재 인증을 한 식 안에서 비교한다

 웹 인가의 표현식이 요청과 경로 변수를 보는 것과 같은 구조다
```

```text
 거부 처리를 자기가 들고 있다

 L91-97 handleDeniedInvocation
   표현식 속성에서 핸들러를 꺼내 넘긴다

 즉 어떤 @PreAuthorize 가 거부됐을 때 무엇을 할지가
 애노테이션 단위로 정해질 수 있다
```

## 결과가 쓰이는 곳

```text
 반환한 AuthorizationResult
      --> 인터셉터가 isGranted() 로 통과 여부를 가른다
      --> 표현식 평가 결과를 담은 구현이 온다

 null 반환
      --> @PreAuthorize 가 없는 메서드다
      --> 포인트컷이 대부분 걸러 주지만 계약상 가능한 경로다

 표현식 핸들러
      --> DefaultMethodSecurityExpressionHandler 가 기본이다
      --> hasRole, hasAuthority, permitAll 같은 함수를 제공한다
      --> 설정으로 바꾸면 커스텀 함수를 더할 수 있다
```
