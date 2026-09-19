# Errors

상위: [Spring 검증과 데이터 바인딩](../../README.md) / [spi](../README.md)

검증과 바인딩 오류를 모으는 자리다. `BindingResult`가 대상 객체와 바인딩 상태까지 함께 들고 있는 확장형이다.

## 실제 코드

`spring-context` / `org.springframework.validation` / `Errors.java` L48-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/Errors.java#L48-L120))

```java
// Errors.java L48-L120
public interface Errors {

    String NESTED_PATH_SEPARATOR = PropertyAccessor.NESTED_PROPERTY_SEPARATOR;

    String getObjectName();

    default void setNestedPath(String nestedPath) {
        throw new UnsupportedOperationException(getClass().getSimpleName() + " does not support nested paths");
    }

    default String getNestedPath() {
        return "";
    }

    default void pushNestedPath(String subPath) {
        throw new UnsupportedOperationException(getClass().getSimpleName() + " does not support nested paths");
    }

    default void popNestedPath() throws IllegalStateException {
        throw new IllegalStateException("Cannot pop nested path: no nested path on stack");
    }

```

`spring-context` / `org.springframework.validation` / `BindingResult.java` L46-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/BindingResult.java#L46-L120))

```java
// BindingResult.java L46-L120
public interface BindingResult extends Errors {

    String MODEL_KEY_PREFIX = BindingResult.class.getName() + ".";

    @Nullable Object getTarget();

    Map<String, Object> getModel();

    @Nullable Object getRawFieldValue(String field);

    @Nullable PropertyEditor findEditor(@Nullable String field, @Nullable Class<?> valueType);

    @Nullable PropertyEditorRegistry getPropertyEditorRegistry();

    String[] resolveMessageCodes(String errorCode);

```

## 흐름에서 불리는 자리

```text
 DataBinder 가 내부에 BindingResult 를 하나 두고
   bind 단계의 변환 오류와 validate 단계의 검증 오류를 모두 여기에 쌓는다
 컨트롤러가 BindingResult 파라미터로 받으면 그 객체가 그대로 전달된다
```

- [DataBinder.bind](../../01_DataBinder.bind/README.md)
- [DataBinder.validate](../../02_DataBinder.validate/README.md)

## 구현 계층

```text
 Errors
   +-- BindingResult                       대상 객체 + 프로퍼티 접근
         +-- AbstractBindingResult
               +-- BeanPropertyBindingResult   기본 (프로퍼티 접근)
               +-- DirectFieldBindingResult    필드 직접 접근

 오류 종류
   ObjectError    객체 전체에 대한 오류 (reject)
   FieldError     특정 필드 (rejectValue) -- 거부된 값도 함께 담는다

 모델에 담기는 이름
   BindingResult.MODEL_KEY_PREFIX + 속성 이름
   그래서 뷰에서 form:errors 가 찾아 쓸 수 있다
```
