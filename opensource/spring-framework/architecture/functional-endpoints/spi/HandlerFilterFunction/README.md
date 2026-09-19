# HandlerFilterFunction

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

핸들러 함수를 감싸 앞뒤에 일을 끼운다. 애노테이션 경로의 `HandlerInterceptor`에 해당하지만, 체인을 이어갈지 말지를 "다음을 부르느냐"로 직접 정한다는 점이 다르다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `HandlerFilterFunction.java` L35-L46 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/HandlerFilterFunction.java#L35-L46))

```java
// HandlerFilterFunction.java L35-L46
public interface HandlerFilterFunction<T extends ServerResponse, R extends ServerResponse> {

    R filter(ServerRequest request, HandlerFunction<T> next) throws Exception;
```

## 흐름에서 불리는 자리

```text
 RouterFunction.filter(필터)
   FilteredRouterFunction 이 만들어진다
   route 가 핸들러를 찾으면 그 핸들러를 필터로 감싸 돌려준다
     --> 어댑터는 감싼 함수를 부른다. 필터가 먼저 실행된다
```

- [RouterFunction](../RouterFunction/README.md)

## 구현 계층

```text
 HandlerFilterFunction<T, R>
   +-- (사용자 람다)   (request, next) -> { ... next.handle(request) ... }

 만드는 방법 (정적 팩토리 — 모두 람다를 돌려준다)
   ofRequestProcessor(f)    요청만 손보는 필터
   ofResponseProcessor(f)   응답만 손보는 필터
   ofErrorHandler(조건, f)  예외를 응답으로 바꾸는 필터

 합성
   andThen(after)   이 필터 다음에 after 를 적용
   apply(handler)   필터를 핸들러에 적용해 새 핸들러를 만든다
```

```text
 인터셉터와의 차이

 HandlerInterceptor    preHandle 이 false 를 돌려주면 체인이 끊긴다
                       실행 여부를 반환값으로 알린다
 HandlerFilterFunction next.handle(request) 를 부르지 않으면 그것이 곧 차단이다
                       응답을 직접 만들어 돌려주면 핸들러는 실행되지 않는다
```

## 결과가 쓰이는 곳

```text
 filter 가 돌려준 응답
      --> 핸들러가 만든 응답을 그대로 흘려도 되고, 갈아 끼워도 된다
      --> 인증 실패 시 401 응답을 직접 만들어 돌려주는 자리가 여기다

 적용 범위
      --> RouterFunction.filter 는 그 라우터가 고른 모든 핸들러에 붙는다
      --> nest 안쪽 라우터에만 걸면 그 묶음에만 적용된다

 예외 처리
      --> ofErrorHandler 로 예외를 응답으로 바꾸면
          HandlerExceptionResolver 까지 가지 않고 여기서 끝난다
```
