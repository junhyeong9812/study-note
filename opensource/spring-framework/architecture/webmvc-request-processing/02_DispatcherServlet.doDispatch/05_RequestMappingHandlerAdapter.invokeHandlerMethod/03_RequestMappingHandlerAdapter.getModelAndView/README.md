# RequestMappingHandlerAdapter.getModelAndView

상위: [RequestMappingHandlerAdapter.invokeHandlerMethod](../README.md)

실행이 끝난 뒤 `ModelAndViewContainer`를 보고 `DispatcherServlet`에 돌려줄 `ModelAndView`를 만든다. 응답을 이미 다 썼다면 null을 돌려주는데, 이 null이 "렌더링하지 마라"는 신호다.

## 실제 코드

`spring-webmvc` / `org.springframework.web.servlet.mvc.method.annotation` / `RequestMappingHandlerAdapter.java` L1041-L1061 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-webmvc/src/main/java/org/springframework/web/servlet/mvc/method/annotation/RequestMappingHandlerAdapter.java#L1041-L1061))

```java
// RequestMappingHandlerAdapter.java L1041-L1061
private @Nullable ModelAndView getModelAndView(ModelAndViewContainer mavContainer,
        ModelFactory modelFactory, NativeWebRequest webRequest) throws Exception {

    modelFactory.updateModel(webRequest, mavContainer);
    if (mavContainer.isRequestHandled()) {
        return null;
    }
    ModelMap model = mavContainer.getModel();
    ModelAndView mav = new ModelAndView(mavContainer.getViewName(), model, mavContainer.getStatus());
    if (!mavContainer.isViewReference()) {
        mav.setView((View) mavContainer.getView());
    }
    if (model instanceof RedirectAttributes redirectAttributes) {
        Map<String, ?> flashAttributes = redirectAttributes.getFlashAttributes();
        HttpServletRequest request = webRequest.getNativeRequest(HttpServletRequest.class);
        if (request != null) {
            RequestContextUtils.getOutputFlashMap(request).putAll(flashAttributes);
        }
    }
    return mav;
}
```

## 동작 흐름

```text
 getModelAndView(mavContainer, modelFactory, webRequest)
 |
 | L1044 modelFactory.updateModel(webRequest, mavContainer)
 |         SessionStatus.setComplete() 호출됐음 --> @SessionAttributes 속성을 세션에서 제거
 |         아니면                             --> @SessionAttributes 속성을 세션에 저장
 |         뷰 렌더링이 남아 있고 기본 모델이면 --> 모델에 BindingResult 추가
 |
 +-- L1045 mavContainer.isRequestHandled() ?
 |         true  --> return null        (@ResponseBody, ResponseEntity, void + response 직접 사용)
 |
 | L1048 model = mavContainer.getModel()
 |         "redirect:" 시나리오면 기본 모델 대신 리다이렉트 모델
 |         (컨트롤러가 RedirectAttributes 파라미터를 받았다면 그 객체)
 | L1049 mav = new ModelAndView(viewName, model, status)
 |
 +-- 뷰 이름이 아니라 View 객체가 들어 있으면 --> mav.setView(view)
 |
 +-- model이 RedirectAttributes 이면
 |       flash 속성 --> 출력 FlashMap 에 복사       (다음 요청으로 전달)
 |
 +-- return mav
```

## 결과가 쓰이는 곳

```text
 null
      --> ha.handle 반환 --> doDispatch의 mv == null
          --> applyDefaultViewName 건너뜀 (mv가 null이라)
          --> processDispatchResult에서 render 건너뜀 ("No view rendering")

 ModelAndView(viewName = "home", model)
      --> doDispatch L969 applyDefaultViewName  뷰 이름이 없을 때만 URL에서 추론 ("users/list")
      --> L970 applyPostHandle(mv)               인터셉터가 모델/뷰 수정 가능
      --> processDispatchResult --> render --> ViewResolver가 "home"을 View로

 출력 FlashMap에 복사한 속성
      --> 리다이렉트 응답 뒤 다음 요청의 doService가 INPUT_FLASH_MAP으로 꺼냄
      --> 그 요청의 invokeHandlerMethod L922에서 모델 초기값이 됨
```

`requestHandled` 플래그 하나로 `@ResponseBody`와 뷰 렌더링이 갈리는 곳이 여기다. 플래그를 세우는 쪽은 [handleReturnValue](../02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/README.md)의 처리기들이다.
