# Spring 검증과 데이터 바인딩

요청 파라미터가 객체의 필드로 들어가고(`DataBinder`), `@Valid`가 붙으면 검증기가 돌아 오류가 모이기까지의 흐름을 위에서 아래로 따라간다. 결과는 예외가 되거나 `BindingResult`에 담겨 컨트롤러로 전달된다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 검증과 변환의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 @PostMapping void save(@Valid @ModelAttribute UserForm form, BindingResult result)
 |
 +-- [MVC 인자 해석] ModelAttributeMethodProcessor.resolveArgument
        모델에 있으면 그 객체, 없으면 새로 만든다 (또는 생성자 바인딩)
        |
        +-- [01] DataBinder.bind        요청 파라미터 --> 객체 필드
        |      허용/필수 필드 검사 --> 타입 변환 --> 프로퍼티 설정
        |      변환 실패는 예외가 아니라 FieldError 로 쌓인다
        |
        +-- [02] DataBinder.validate    @Valid 가 있을 때만
        |      등록된 Validator 들을 같은 BindingResult 로 실행
        |      Bean Validation(@NotNull 등)은 SpringValidatorAdapter 가 위임
        |
        +-- 다음 파라미터가 BindingResult 인가?
               예   --> 오류를 담아 컨트롤러에 넘긴다 (컨트롤러가 판단)
               아니오 --> MethodArgumentNotValidException 을 던진다 (400)
```

`@RequestBody`는 경로가 조금 다르다.

```text
 @RequestBody @Valid UserDto dto
   RequestResponseBodyMethodProcessor
     HttpMessageConverter 로 본문을 객체로 (여기서는 DataBinder 를 쓰지 않는다)
     그 뒤 같은 validateIfApplicable 로 검증
     오류면 MethodArgumentNotValidException
```

## 단계

1. [DataBinder.bind](01_DataBinder.bind/README.md)가 값을 객체에 넣고 변환 오류를 수집한다.
2. [DataBinder.validate](02_DataBinder.validate/README.md)가 검증기를 실행해 오류를 더한다.

## 어디에서 들어오는가

```text
 [MVC 요청 처리] 인자 해석 단계
   ModelAttributeMethodProcessor.resolveArgument (L106)
     bindRequestParameters --> binder.bind
     validateIfApplicable  --> binder.validate(힌트)
     isBindExceptionRequired --> 다음 인자가 Errors 가 아니면 예외
```

자세한 인자 해석은 [MVC 요청 처리](../webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/01_InvocableHandlerMethod.getMethodArgumentValues/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 채워진 객체
      --> 컨트롤러 메서드의 인자
      --> 모델에도 같은 이름으로 들어가 뷰에서 쓸 수 있다

 BindingResult
      --> 컨트롤러가 result.hasErrors() 로 분기
      --> 뷰에서는 form:errors 로 표시
      --> 오류 코드는 MessageCodesResolver 가 만든 여러 후보 중
          MessageSource 가 찾은 메시지로 표시된다

 예외 (BindingResult 파라미터가 없을 때)
      --> MethodArgumentNotValidException --> DefaultHandlerExceptionResolver --> 400
```

## 다루지 않는 것

타입 변환 자체(`ConversionService`, `PropertyEditor`)의 내부와 메서드 파라미터 검증(`@Validated` 클래스 수준, `MethodValidationInterceptor`)은 별도 주제다. 후자는 AOP 인터셉터로 동작한다.

## 하위 메서드

- [01 DataBinder.bind](01_DataBinder.bind/README.md)
- [02 DataBinder.validate](02_DataBinder.validate/README.md)
- [spi](spi/README.md) — 검증기, 오류 수집, 메시지 코드, 변환기
