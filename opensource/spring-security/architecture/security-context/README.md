# 보안 컨텍스트

"지금 누가 요청했는가"를 코드 어디서나 꺼내 쓸 수 있게 하는 장치다. 요청이 들어오면 저장소에서 컨텍스트를 꺼내 `ThreadLocal` 에 얹고, 요청이 끝나면 지운다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 저장소와 보관 전략 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [읽는 쪽] 요청이 들어올 때

 필터 체인의 앞쪽
 |
 +-- [01] SecurityContextHolderFilter.doFilter
 |        FILTER_APPLIED 로 중첩 호출을 가려낸다
 |        저장소에서 "지연된" 컨텍스트를 받아 ThreadLocal 에 얹는다
 |        finally 에서 반드시 지운다
 |
 +-- [01-01] SecurityContextRepository.loadDeferredContext
 |        지금 읽지 않는다. 읽는 방법만 담은 Supplier 를 돌려준다
 |        실제 읽기는 누군가 getContext() 를 부를 때 일어난다
 |
 +-- [02] ThreadLocalSecurityContextHolderStrategy.getContext
          Supplier 를 꺼내 get() 한다
          아무것도 없으면 빈 컨텍스트를 만들어 넣는다

 [쓰는 쪽] 인증에 성공했을 때

 이 흐름에는 "저장" 단계가 없다
 저장은 컨텍스트를 바꾼 쪽이 직접 한다
 |
 +-- AbstractAuthenticationProcessingFilter.successfulAuthentication
 |        새 컨텍스트를 만들어 ThreadLocal 에 얹고
 |        securityContextRepository.saveContext(...) 를 명시적으로 부른다
 |
 +-- BasicAuthenticationFilter, RememberMeAuthenticationFilter,
 |   SwitchUserFilter, DigestAuthenticationFilter,
 |   AbstractPreAuthenticatedProcessingFilter 등도 각자 부른다
 |
 +-- SecurityContextLogoutHandler 는 반대 방향이다
     빈 컨텍스트를 만들어 저장해서 기존 것을 지운다
```

```text
 왜 "지연"인가

 필터는 값이 아니라 Supplier 를 ThreadLocal 에 얹는다
 실제 읽기는 누군가 getContext() 를 부를 때 일어난다

 그래서 SecurityContext 를 한 번도 꺼내 보지 않은 요청은
 저장소를 읽지 않는다
```

```text
 읽기와 쓰기가 분리되어 있다

 SecurityContextHolderFilter   읽기만 한다
 인증 필터들                    쓰기를 각자 명시적으로 한다

 이것이 SecurityContextPersistenceFilter 와 갈리는 지점이다
 그쪽은 요청이 끝날 때 컨텍스트를 자동으로 저장했다
 지금은 그 자동 저장이 없다
 --> 직접 SecurityContextHolder 에 인증을 심기만 하면
     다음 요청에 남지 않는다. 저장소에 저장까지 해야 한다
```

## 어디에서 쓰이는가

```text
 [인가] AuthorizationFilter 가 여기서 Authentication 을 꺼내 판정한다
 [폼 로그인] 인증에 성공한 필터가 컨텍스트를 만들어 저장소에 넣는다
 [메서드 보안] @PreAuthorize 평가도 같은 ThreadLocal 을 본다
 [예외 변환] 익명인지 기억된 사용자인지 보고 401 과 403 을 가른다
```

이 컨텍스트를 읽어 판정하는 쪽은 [인가](../authorization/README.md), 채워 넣는 쪽은 [폼 로그인](../form-login/README.md)에 있다.

## 단계

1. [SecurityContextHolderFilter.doFilter](01_SecurityContextHolderFilter.doFilter/README.md)가 컨텍스트를 얹고 지운다.
2. [SecurityContextRepository.loadDeferredContext](01_SecurityContextHolderFilter.doFilter/01_SecurityContextRepository.loadDeferredContext/README.md)가 읽는 방법을 만든다.
3. [ThreadLocalSecurityContextHolderStrategy.getContext](02_ThreadLocalSecurityContextHolderStrategy.getContext/README.md)가 실제로 꺼낸다.

## 결과가 쓰이는 곳

```text
 ThreadLocal 에 얹힌 Supplier
      --> SecurityContextHolder.getContext() 가 이것을 꺼낸다
      --> 컨트롤러, 서비스, @PreAuthorize 가 전부 같은 값을 본다

 지연 로딩
      --> 아무도 꺼내 보지 않으면 저장소를 읽지 않는다
      --> 반대로 한 번 꺼내면 그 뒤로는 같은 인스턴스를 돌려준다

 finally 의 clearContext
      --> 요청이 끝나면 지운다
      --> 스레드 풀 재사용 환경에서 인증이 새는 것을 막는다

 저장하지 않은 인증
      --> SecurityContextHolder 에만 심으면 그 요청 안에서만 유효하다
      --> 다음 요청에도 남기려면 저장소에 saveContext 를 불러야 한다
```

## 다루지 않는 것

각 저장소 구현의 세부(`HttpSessionSecurityContextRepository`의 세션 생성 규칙, `RequestAttributeSecurityContextRepository`의 속성 키), deprecated 된 `SecurityContextPersistenceFilter`의 자동 저장 경로, 리액티브 쪽 컨텍스트 전파는 같은 뼈대의 곁가지라 요약만 했다. 리액티브 경로는 [리액티브 컨텍스트](../reactive-context/README.md)에서 따로 다룬다.

## 하위 메서드

- [01 SecurityContextHolderFilter.doFilter](01_SecurityContextHolderFilter.doFilter/README.md)
- [02 ThreadLocalSecurityContextHolderStrategy.getContext](02_ThreadLocalSecurityContextHolderStrategy.getContext/README.md)
- [spi](spi/README.md) — 저장소, 보관 전략, 지연 컨텍스트
