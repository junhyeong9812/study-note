# DataBinder.validate

상위: [Spring 검증과 데이터 바인딩](../README.md)

등록된 검증기들을 같은 `BindingResult` 위에서 실행한다. Bean Validation 애노테이션(`@NotNull`, `@Size` 등)은 어댑터를 거쳐 여기에 합류한다.

## 실제 코드

`spring-context` / `org.springframework.validation` / `DataBinder.java` L1379-L1387 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/DataBinder.java#L1379-L1387))

```java
// DataBinder.java L1379-L1387
public void validate() {
    Object target = getTarget();
    Assert.state(target != null, "No target to validate");
    BindingResult bindingResult = getBindingResult();
    // Call each validator with the same binding result
    for (Validator validator : getValidatorsToApply()) {
        validator.validate(target, bindingResult);
    }
}
```

`spring-context` / `org.springframework.validation` / `DataBinder.java` L1397-L1410 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/DataBinder.java#L1397-L1410))

```java
// DataBinder.java L1397-L1410
public void validate(Object... validationHints) {
    Object target = getTarget();
    Assert.state(target != null, "No target to validate");
    BindingResult bindingResult = getBindingResult();
    // Call each validator with the same binding result
    for (Validator validator : getValidatorsToApply()) {
        if (!ObjectUtils.isEmpty(validationHints) && validator instanceof SmartValidator smartValidator) {
            smartValidator.validate(target, bindingResult, validationHints);
        }
        else if (validator != null) {
            validator.validate(target, bindingResult);
        }
    }
}
```

MVC에서 이 메서드를 부르는 지점이다.

`spring-web` / `org.springframework.web.method.annotation` / `ModelAttributeMethodProcessor.java` L226-L234 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/annotation/ModelAttributeMethodProcessor.java#L226-L234))

```java
// ModelAttributeMethodProcessor.java L226-L234
protected void validateIfApplicable(WebDataBinder binder, MethodParameter parameter) {
    for (Annotation ann : parameter.getParameterAnnotations()) {
        Object[] validationHints = ValidationAnnotationUtils.determineValidationHints(ann);
        if (validationHints != null) {
            binder.validate(validationHints);
            break;
        }
    }
}
```

Bean Validation 어댑터는 제약 위반을 오류로 옮긴다.

`spring-context` / `org.springframework.validation.beanvalidation` / `SpringValidatorAdapter.java` L100-L113 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/beanvalidation/SpringValidatorAdapter.java#L100-L113))

```java
// SpringValidatorAdapter.java L100-L113
@Override
public void validate(Object target, Errors errors) {
    if (this.targetValidator != null) {
        processConstraintViolations(this.targetValidator.validate(target), errors);
    }
}

@Override
public void validate(Object target, Errors errors, Object... validationHints) {
    if (this.targetValidator != null) {
        processConstraintViolations(
                this.targetValidator.validate(target, asValidationGroups(validationHints)), errors);
    }
}
```

## 동작 흐름

```text
 validateIfApplicable(binder, parameter)     (MVC 인자 해석 단계)
 |
 +-- 파라미터 애노테이션을 훑어 @Valid 또는 @Validated 를 찾는다
       ValidationAnnotationUtils.determineValidationHints
         @Validated(Group.class) 이면 그 그룹이 힌트가 된다
         @Valid 면 빈 힌트
       --> binder.validate(힌트)

 validate(validationHints)
 |
 +-- getValidatorsToApply() 의 각 검증기에 대해
       SmartValidator 이고 힌트가 있으면 validate(target, errors, hints)
       아니면 validate(target, errors)
       모두 같은 BindingResult(errors)를 공유한다
       = 여러 검증기의 오류가 한곳에 모인다

 SpringValidatorAdapter.validate
   jakarta Validator.validate(target) 실행
   ConstraintViolation 들을 processConstraintViolations 로
     위반마다 필드 경로를 찾아 FieldError / ObjectError 생성
     오류 코드는 제약 애노테이션 이름 기반 (NotNull, Size 등)
```

## 결과가 쓰이는 곳

```text
 BindingResult 의 오류들
      --> 컨트롤러가 BindingResult 파라미터로 받으면 직접 판단
      --> 받지 않으면 MethodArgumentNotValidException (400)

 검증 힌트(그룹)
      --> @Validated(OnCreate.class) 처럼 상황별 제약 적용
      --> SmartValidator 가 아니면 힌트는 무시된다

 오류 코드
      --> MessageCodesResolver 가 여러 후보를 만든다
          예: NotNull.userForm.email, NotNull.email, NotNull.java.lang.String, NotNull
      --> MessageSource 에서 가장 구체적인 것부터 찾아 메시지를 만든다
```

메서드 파라미터 검증(`@Validated`를 클래스에 붙이는 방식)은 다른 장치다. 그쪽은 AOP 인터셉터가 호출을 가로채 검증하고 `ConstraintViolationException`을 던진다.
