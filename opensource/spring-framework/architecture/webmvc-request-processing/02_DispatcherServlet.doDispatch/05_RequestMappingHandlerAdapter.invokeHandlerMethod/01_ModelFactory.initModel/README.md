# ModelFactory.initModel

상위: [RequestMappingHandlerAdapter.invokeHandlerMethod](../README.md)

컨트롤러 메서드가 실행되기 전에 모델을 준비한다. 세션에 저장해 둔 속성을 꺼내고, 같은 컨트롤러(와 `@ControllerAdvice`)의 `@ModelAttribute` 메서드를 먼저 실행해 그 반환값을 모델에 넣는다.

## 실제 코드

`spring-web` / `org.springframework.web.method.annotation` / `ModelFactory.java` L106-L122 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/annotation/ModelFactory.java#L106-L122))

```java
// ModelFactory.java L106-L122
public void initModel(NativeWebRequest request, ModelAndViewContainer container, HandlerMethod handlerMethod)
        throws Exception {

    Map<String, ?> sessionAttributes = this.sessionAttributesHandler.retrieveAttributes(request);
    container.mergeAttributes(sessionAttributes);
    invokeModelAttributeMethods(request, container);

    for (String name : findSessionAttributeArguments(handlerMethod)) {
        if (!container.containsAttribute(name)) {
            Object value = this.sessionAttributesHandler.retrieveAttribute(request, name);
            if (value == null) {
                throw new IllegalStateException("Expected session attribute '" + name + "'");
            }
            container.addAttribute(name, value);
        }
    }
}
```

`spring-web` / `org.springframework.web.method.annotation` / `ModelFactory.java` L128-L161 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/annotation/ModelFactory.java#L128-L161))

```java
// ModelFactory.java L128-L161
private void invokeModelAttributeMethods(NativeWebRequest request, ModelAndViewContainer container)
        throws Exception {

    while (!this.modelMethods.isEmpty()) {
        InvocableHandlerMethod modelMethod = getNextModelMethod(container).getHandlerMethod();
        ModelAttribute ann = modelMethod.getMethodAnnotation(ModelAttribute.class);
        Assert.state(ann != null, "No ModelAttribute annotation");
        if (container.containsAttribute(ann.name())) {
            if (!ann.binding()) {
                container.setBindingDisabled(ann.name());
            }
            continue;
        }

        Object returnValue = modelMethod.invokeForRequest(request, container);
        if (modelMethod.isVoid()) {
            if (StringUtils.hasText(ann.value())) {
                if (logger.isDebugEnabled()) {
                    logger.debug("Name in @ModelAttribute is ignored because method returns void: " +
                            modelMethod.getShortLogMessage());
                }
            }
            continue;
        }

        String returnValueName = getNameForReturnValue(returnValue, modelMethod.getReturnType());
        if (!ann.binding()) {
            container.setBindingDisabled(returnValueName);
        }
        if (!container.containsAttribute(returnValueName)) {
            container.addAttribute(returnValueName, returnValue);
        }
    }
}
```

`spring-web` / `org.springframework.web.method.annotation` / `ModelFactory.java` L163-L173 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/annotation/ModelFactory.java#L163-L173))

```java
// ModelFactory.java L163-L173
private ModelMethod getNextModelMethod(ModelAndViewContainer container) {
    for (ModelMethod modelMethod : this.modelMethods) {
        if (modelMethod.checkDependencies(container)) {
            this.modelMethods.remove(modelMethod);
            return modelMethod;
        }
    }
    ModelMethod modelMethod = this.modelMethods.get(0);
    this.modelMethods.remove(modelMethod);
    return modelMethod;
}
```

## 동작 흐름

```text
 initModel(request, container, handlerMethod)
 |
 | L109  sessionAttributes = @SessionAttributes로 선언된 이름들을 세션에서 조회
 | L110  container.mergeAttributes()        모델에 없는 것만 추가
 |
 | L111  invokeModelAttributeMethods()
 |        while modelMethods 남아 있음
 |          getNextModelMethod()   의존하는 속성이 이미 모델에 있는 메서드부터 (없으면 아무거나)
 |          이미 같은 이름 속성이 모델에 있으면 --> 건너뜀   (세션/flash 값 우선)
 |          실행 (인자 해석 포함 -- 컨트롤러 메서드와 같은 InvocableHandlerMethod 경로)
 |          반환값을 이름 규칙에 따라 모델에 추가   (void면 메서드가 Model에 직접 넣음)
 |
 | L113  핸들러 파라미터 중 @ModelAttribute이면서 @SessionAttributes에 선언된 이름
 |        모델에 없으면 세션에서 다시 조회
 |          세션에도 없음 --> IllegalStateException("Expected session attribute")
 |
 +-- (반환 없음. 결과는 container에 남음)
```

## 결과가 쓰이는 곳

```text
 container의 모델 속성
      |
      +-- invokeAndHandle의 인자 해석
      |     @ModelAttribute("user") User user
      |       모델에 "user"가 있음 --> 그 객체에 요청 파라미터를 바인딩   (새로 만들지 않음)
      |       모델에 없음         --> 새 인스턴스 생성 후 바인딩
      |     Model / ModelMap 파라미터 --> 이 컨테이너의 모델 그 자체
      |
      +-- getModelAndView --> ModelAndView의 모델 --> 뷰 렌더링의 입력
      |
      +-- getModelAndView 안의 modelFactory.updateModel
            @SessionAttributes 이름에 해당하는 속성을 세션에 다시 저장
```

폼 수정 화면에서 `@ModelAttribute` 메서드로 DB의 엔티티를 먼저 올려 두면, 제출된 파라미터가 그 엔티티 위에 덮어써지는 이유가 첫 번째 가지다.
