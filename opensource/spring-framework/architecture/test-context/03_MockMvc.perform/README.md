# MockMvc.perform

상위: [Spring 테스트 컨텍스트](../README.md)

서블릿 컨테이너를 띄우지 않고 `DispatcherServlet`을 직접 호출한다. 요청과 응답은 목 객체이고, 그 사이의 처리 과정은 실제 MVC 흐름과 같다.

## 실제 코드

`spring-test` / `org.springframework.test.web.servlet` / `MockMvc.java` L164-L225 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/web/servlet/MockMvc.java#L164-L225))

```java
// MockMvc.java L164-L225
 */
public ResultActions perform(RequestBuilder requestBuilder) throws Exception {
    if (this.defaultRequestBuilder != null && requestBuilder instanceof Mergeable mergeable) {
        requestBuilder = (RequestBuilder) mergeable.merge(this.defaultRequestBuilder);
    }

    MockHttpServletRequest request = requestBuilder.buildRequest(this.servletContext);

    AsyncContext asyncContext = request.getAsyncContext();
    MockHttpServletResponse mockResponse;
    HttpServletResponse servletResponse;
    if (asyncContext != null) {
        servletResponse = (HttpServletResponse) asyncContext.getResponse();
        mockResponse = unwrapResponseIfNecessary(servletResponse);
    }
    else {
        mockResponse = new MockHttpServletResponse();
        servletResponse = mockResponse;
    }

    if (this.defaultResponseCharacterEncoding != null) {
        mockResponse.setDefaultCharacterEncoding(this.defaultResponseCharacterEncoding.name());
    }

    if (requestBuilder instanceof SmartRequestBuilder smartRequestBuilder) {
        request = smartRequestBuilder.postProcessRequest(request);
    }

    MvcResult mvcResult = new DefaultMvcResult(request, mockResponse);
    request.setAttribute(MVC_RESULT_ATTRIBUTE, mvcResult);

    RequestAttributes previousAttributes = RequestContextHolder.getRequestAttributes();
    RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(request, servletResponse));

    MockFilterChain filterChain = new MockFilterChain(this.servlet, this.filters);
    filterChain.doFilter(request, servletResponse);

    if (DispatcherType.ASYNC.equals(request.getDispatcherType()) &&
            asyncContext != null && !request.isAsyncStarted()) {
        asyncContext.complete();
    }

    applyDefaultResultActions(mvcResult);
    RequestContextHolder.setRequestAttributes(previousAttributes);

    return new ResultActions() {
        @Override
        public ResultActions andExpect(ResultMatcher matcher) throws Exception {
            matcher.match(mvcResult);
            return this;
        }
        @Override
        public ResultActions andDo(ResultHandler handler) throws Exception {
            handler.handle(mvcResult);
            return this;
        }
        @Override
        public MvcResult andReturn() {
            return mvcResult;
        }
    };
}
```

## 동작 흐름

```text
 perform(requestBuilder)
 |
 | L166 기본 요청 설정이 있으면 병합 (공통 헤더, 컨텍스트 경로 등)
 | L170 requestBuilder.buildRequest(servletContext)
 |        MockHttpServletRequest 생성 (get("/users/42") 등이 만든 빌더)
 |
 | L173 MockHttpServletResponse 준비
 |        비동기 재디스패치라면 기존 AsyncContext 의 응답을 재사용
 |
 | L188 SmartRequestBuilder 면 후처리 (인증 정보 주입 등 RequestPostProcessor)
 |
 | L192 DefaultMvcResult 를 만들어 요청 속성에 심는다
 |        이후 단계가 핸들러/모델/뷰를 여기에 기록한다
 |
 | L196 RequestContextHolder 에 요청 바인딩
 |        실제 서버의 FrameworkServlet.processRequest 가 하는 일을 대신한다
 |
 +-- L198 MockFilterChain(servlet, filters).doFilter(request, response)
 |        등록된 필터를 거쳐 DispatcherServlet.service 로
 |        --> 여기서부터는 실제 MVC 요청 처리와 동일
 |
 | L201 비동기가 시작됐다가 끝난 경우 AsyncContext 완료 처리
 | L206 기본 결과 검증(alwaysDo) 적용
 | L207 요청 바인딩 복원
 |
 +-- ResultActions 반환
        andExpect / andDo / andReturn 으로 이어지는 fluent 검증
```

1. 필터 체인 뒤의 처리는 [MVC 요청 처리](../../webmvc-request-processing/02_DispatcherServlet.doDispatch/README.md)와 같은 코드다.

## 결과가 쓰이는 곳

```text
 MvcResult
      --> 요청, 응답, 선택된 핸들러, 모델, 뷰, 예외를 모두 담는다
      --> andExpect(status().isOk()), andExpect(model().attribute(...)) 의 검증 대상
      --> 실제 서버로는 볼 수 없는 내부 상태(핸들러 메서드, 모델)까지 검증할 수 있다

 목 요청/응답
      --> 실제 소켓이 없다. 직렬화된 본문은 MockHttpServletResponse 의 버퍼에 남는다
      --> 컨테이너 고유 동작(커밋 시점, 인코딩 기본값)은 실제와 다를 수 있다

 RequestContextHolder 복원
      --> 테스트 스레드에 요청이 남지 않게 한다
      --> 병렬 테스트에서 문맥이 섞이지 않는 근거
```

`MockMvcTester`는 같은 `MockMvc`를 AssertJ 스타일로 감싼 것이고, `RestTestClient`는 같은 인프라 위에 클라이언트 API를 얹은 것이다.
