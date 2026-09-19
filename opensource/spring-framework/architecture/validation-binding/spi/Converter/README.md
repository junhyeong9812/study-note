# Converter

상위: [Spring 검증과 데이터 바인딩](../../README.md) / [spi](../README.md)

바인딩 중 문자열을 대상 타입으로 바꾸는 변환 전략이다. 구형 `PropertyEditor`와 신형 `Converter` 두 계열이 함께 쓰인다.

## 실제 코드

`spring-core` / `org.springframework.core.convert.converter` / `Converter.java` L38-L68 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/convert/converter/Converter.java#L38-L68))

```java
// Converter.java L38-L68
public interface Converter<S, T extends @Nullable Object> {

    T convert(S source);

    default <U> Converter<S, @Nullable U> andThen(Converter<? super T, ? extends @Nullable U> after) {
        Assert.notNull(after, "'after' Converter must not be null");
        return (S s) -> {
            T initialResult = convert(s);
            return (initialResult != null ? after.convert(initialResult) : null);
        };
    }

}
```

## 흐름에서 불리는 자리

```text
 applyPropertyValues --> setPropertyValues
   프로퍼티마다 타입이 다르면
     DataBinder 에 설정된 ConversionService 로 변환
     또는 등록된 PropertyEditor 사용
   실패 --> typeMismatch FieldError
```

- [DataBinder.bind](../../01_DataBinder.bind/README.md)

## 구현 계층

```text
 변환 계열
   Converter<S, T>              단순 1:1 변환
   ConverterFactory<S, R>       enum 처럼 계열 변환
   GenericConverter             제네릭/컬렉션까지 다루는 저수준
   Formatter<T>                 로케일을 고려한 표시/파싱 (@DateTimeFormat 등)
   PropertyEditor               JavaBeans 표준 (구형, 스레드 안전하지 않음)

 등록
   @InitBinder 에서 binder.registerCustomEditor / setConversionService
   WebMvcConfigurer.addFormatters 로 전역 등록
```
