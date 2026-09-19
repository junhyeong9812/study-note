# ServerRequest

상위: [Spring 함수형 엔드포인트](../../README.md) / [spi](../README.md)

요청을 읽는 표면이다. 애노테이션 경로에서 인자 리졸버들이 대신 꺼내 주던 값을, 여기서는 핸들러가 직접 꺼낸다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.function` / `ServerRequest.java` L64-L76 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/ServerRequest.java#L64-L76))

```java
// ServerRequest.java L64-L76
public interface ServerRequest {

    HttpMethod method();

    URI uri();
```

본문 읽기는 매핑 단계에서 넘겨받은 컨버터를 쓴다.

`spring-webmvc` / `org.springframework.web.servlet.function` / `ServerRequest.java` L133-L133 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/function/ServerRequest.java#L133-L133))

```java
// ServerRequest.java L133-L133
<T> T body(Class<T> bodyType) throws ServletException, IOException;
```

## 흐름에서 불리는 자리

```text
 RouterFunctionMapping.getHandlerInternal
   ServerRequest.create(servletRequest, messageConverters, versionStrategy)
     여기서 넘긴 컨버터가 이후 body(...) 호출에 쓰인다
 조건 판정
   predicate.test(request) 가 method(), path(), headers() 를 읽는다
 핸들러 함수
   request.pathVariable / param / body 로 값을 꺼낸다
```

- [webmvc.RouterFunctionMapping.getHandlerInternal](../../01_webmvc.RouterFunctionMapping.getHandlerInternal/README.md)

## 구현 계층

```text
 ServerRequest
   +-- DefaultServerRequest             서블릿 요청을 감싼 기본 구현
   +-- (DefaultServerRequestBuilder 가 만드는 수정본)   from(request).method(...).build()
   +-- ServerRequestWrapper             위임 래퍼 (리액티브 전용, 필터에서 쓰기 좋다)

 중첩 라우팅이 만드는 변형
   PathPatternPredicate.nest 가 "남은 경로"만 남긴 요청을 새로 만든다
```

```text
 읽기 표면 (일부)

 method() uri() path() headers() cookies()     요청 줄과 헤더
 pathVariable(name) pathVariables()            경로 변수
 param(name) params()                          쿼리/폼 파라미터
 body(Class) body(ParameterizedTypeReference)  본문 --> 객체 (컨버터 사용)
 attribute(name) attributes()                  요청 속성
 servletRequest()                              서블릿 원본 (탈출구)
```

## 결과가 쓰이는 곳

```text
 매핑 단계에서 만든 인스턴스
      --> 요청 속성에 담겨 어댑터와 핸들러 함수가 같은 것을 쓴다
      --> 어댑터가 같은 요청 객체를 다시 만들 수 없기 때문이다 (컨버터와 버전 전략이 없다)
      --> DefaultServerRequest 는 본문을 캐시하지 않는다. body() 를 두 번 부르면 두 번 읽는다

 body(Class)
      --> Content-Type 에 맞는 HttpMessageConverter 를 골라 객체로 만든다
      --> 애노테이션 경로의 @RequestBody 와 같은 컨버터 목록을 쓴다
      --> 다만 @Valid 같은 검증은 자동으로 붙지 않는다. 필요하면 직접 부른다

 pathVariable(name)
      --> 조건이 남긴 URI_TEMPLATE_VARIABLES_ATTRIBUTE 를 읽는다
      --> 이름이 없으면 IllegalArgumentException
```

검증을 직접 붙이려면 [DataBinder](../../../validation-binding/README.md) 흐름의 표면을 쓴다.
