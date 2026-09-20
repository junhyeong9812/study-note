# VirtualFilterChain.doFilter

상위: [필터 체인](../README.md)

고른 필터 목록을 실제로 태우는 자리다. 서블릿 `FilterChain` 을 구현했지만 컨테이너가 만든 것이 아니라 Spring Security 가 만든 가짜(virtual) 체인이다.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L359-L388 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L359-L388))

## 실제 코드

클래스 선언부터 함께 본다. 커서가 인스턴스 필드라는 점이 이 흐름의 핵심이기 때문이다.

```java
// FilterChainProxy.java L359-L388
private static final class VirtualFilterChain implements FilterChain {

    private final FilterChain originalChain;

    private final List<Filter> additionalFilters;

    private final int size;

    private int currentPosition = 0;

    private VirtualFilterChain(FilterChain chain, List<Filter> additionalFilters) {
        this.originalChain = chain;
        this.additionalFilters = additionalFilters;
        this.size = additionalFilters.size();
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response) throws IOException, ServletException {
        if (this.currentPosition == this.size) {
            this.originalChain.doFilter(request, response);
            return;
        }
        this.currentPosition++;
        Filter nextFilter = this.additionalFilters.get(this.currentPosition - 1);
        if (logger.isTraceEnabled()) {
            String name = nextFilter.getClass().getSimpleName();
            logger.trace(LogMessage.format("Invoking %s (%d/%d)", name, this.currentPosition, this.size));
        }
        nextFilter.doFilter(request, response, this);
    }
```

## 동작 흐름

```text
 doFilter(request, response)
 |
 +-- L377 currentPosition == size 이면
 |        L378 originalChain.doFilter(request, response)
 |        L379 return
 |        --> 보안 필터를 다 돌았다. 바깥으로 나간다
 |
 +-- L381 아직 남았으면
        L381 currentPosition++
        L382 nextFilter = additionalFilters.get(currentPosition - 1)
        L387 nextFilter.doFilter(request, response, this)
                                                    ^^^^
                        자기 자신을 체인으로 넘긴다
```

L383~L386 은 trace 로그다.

```text
 커서 하나로 도는 재귀

 filters = [A, B, C],  originalChain = 컨테이너 체인

 VirtualFilterChain.doFilter   pos 0 -> 1, A.doFilter(req, res, this)
   A 가 chain.doFilter(req, res) 를 부르면
     VirtualFilterChain.doFilter pos 1 -> 2, B.doFilter(req, res, this)
       B 가 부르면
         VirtualFilterChain.doFilter pos 2 -> 3, C.doFilter(req, res, this)
           C 가 부르면
             pos == size 이므로 originalChain.doFilter

 호출 스택이 그대로 쌓인다. 빠져나올 때는 역순으로 되돌아온다
 그래서 필터는 "다음을 부르기 전"과 "부른 뒤" 양쪽에 코드를 둘 수 있다
```

```text
 체인을 끊는다는 것

 필터가 chain.doFilter 를 부르지 않으면 커서는 멈춘 채로 끝난다

 예) AuthorizationFilter 가 거부하면 예외를 던진다
     예) LogoutFilter 가 로그아웃 경로를 처리하면 응답만 쓰고 끝낸다
     예) CsrfFilter 가 토큰 불일치를 보면 AccessDeniedHandler 를 부르고 끝낸다

 이 경우 뒤의 필터도, DispatcherServlet 도 실행되지 않는다
 컨트롤러가 안 불렸는데 응답이 나가는 상황이 전부 이것이다
```

```text
 인스턴스는 요청마다 새로 만든다

 currentPosition 은 인스턴스 필드다
 VirtualFilterChainDecorator.decorate 가 요청마다 new 로 만든다
 그래서 커서를 공유하는 사고가 나지 않는다

 반대로 필터 자신들은 싱글톤 빈이다
 필터에 요청 상태를 필드로 두면 안 되는 이유다
```

## 결과가 쓰이는 곳

```text
 originalChain 에 닿았다는 사실
      --> 보안 검사를 전부 통과했다는 뜻이다
      --> 이 뒤에 firewallRequest.reset() 과 컨테이너 체인이 이어진다

 필터가 받은 this
      --> 필터는 자기가 몇 번째인지 모른다. 다음을 부를 수단만 받는다
      --> 그래서 필터 순서는 목록을 만들 때 이미 정해져 있어야 한다

 중간에 끊긴 체인
      --> 응답은 그 필터가 직접 쓴다
      --> 리다이렉트, 401, 403 이 여기서 나간다
```

필터 순서가 어떻게 정해지는지는 [설정 DSL](../../config-dsl/README.md)에 있다.
