# Validator

상위: [Spring 검증과 데이터 바인딩](../../README.md) / [spi](../README.md)

대상 객체를 검증해 오류를 `Errors`에 쌓는다. 힌트(그룹)를 받는 `SmartValidator`가 확장형이다.

## 실제 코드

`spring-context` / `org.springframework.validation` / `Validator.java` L63-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/Validator.java#L63-L120))

```java
// Validator.java L63-L120
public interface Validator {

    boolean supports(Class<?> clazz);

    void validate(Object target, Errors errors);

    default Errors validateObject(Object target) {
        Errors errors = new SimpleErrors(target);
        validate(target, errors);
        return errors;
    }

```

`spring-context` / `org.springframework.validation` / `SmartValidator.java` L29-L81 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/SmartValidator.java#L29-L81))

```java
// SmartValidator.java L29-L81
public interface SmartValidator extends Validator {

    void validate(Object target, Errors errors, Object... validationHints);

    default void validateValue(
            Class<?> targetType, @Nullable String fieldName, @Nullable Object value, Errors errors, Object... validationHints) {

        throw new IllegalArgumentException("Cannot validate individual value for " + targetType);
    }

    default <T> @Nullable T unwrap(@Nullable Class<T> type) {
        return null;
    }

}
```

## 흐름에서 불리는 자리

```text
 DataBinder.validate(힌트)
   getValidatorsToApply() 순회
     SmartValidator + 힌트 있음 --> validate(target, errors, hints)
     그 밖                      --> validate(target, errors)
```

- [DataBinder.validate](../../02_DataBinder.validate/README.md)

## 구현 계층

```text
 Validator
   +-- SmartValidator                     검증 힌트(그룹) 지원
   |     +-- SpringValidatorAdapter       Bean Validation(jakarta) 위임
   |           +-- LocalValidatorFactoryBean   컨테이너에서 Validator 빈으로
   |           +-- CustomValidatorBean
   +-- (사용자 구현: supports + validate 두 메서드)

 등록
   @InitBinder 에서 binder.addValidators(...)
   @ControllerAdvice 로 전역 등록
   WebMvcConfigurer.getValidator() 로 기본 검증기 교체
```
