# DataBinder.bind

상위: [Spring 검증과 데이터 바인딩](../README.md)

문자열 값 묶음을 대상 객체의 프로퍼티에 넣는다. 허용 필드와 필수 필드를 검사하고, 타입 변환에 실패하면 예외 대신 오류 목록에 쌓는다.

## 실제 코드

`spring-context` / `org.springframework.validation` / `DataBinder.java` L1219-L1226 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/DataBinder.java#L1219-L1226))

```java
// DataBinder.java L1219-L1226
public void bind(PropertyValues pvs) {
    if (shouldNotBindPropertyValues()) {
        return;
    }
    MutablePropertyValues mpvs = (pvs instanceof MutablePropertyValues mutablePropertyValues ?
            mutablePropertyValues : new MutablePropertyValues(pvs));
    doBind(mpvs);
}
```

`spring-context` / `org.springframework.validation` / `DataBinder.java` L1247-L1251 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/DataBinder.java#L1247-L1251))

```java
// DataBinder.java L1247-L1251
protected void doBind(MutablePropertyValues mpvs) {
    checkAllowedFields(mpvs);
    checkRequiredFields(mpvs);
    applyPropertyValues(mpvs);
}
```

`spring-context` / `org.springframework.validation` / `DataBinder.java` L1360-L1371 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/DataBinder.java#L1360-L1371))

```java
// DataBinder.java L1360-L1371
protected void applyPropertyValues(MutablePropertyValues mpvs) {
    try {
        // Bind request parameters onto target object.
        getPropertyAccessor().setPropertyValues(mpvs, isIgnoreUnknownFields(), isIgnoreInvalidFields());
    }
    catch (PropertyBatchUpdateException ex) {
        // Use bind error processor to create FieldErrors.
        for (PropertyAccessException pae : ex.getPropertyAccessExceptions()) {
            getBindingErrorProcessor().processPropertyAccessException(pae, getInternalBindingResult());
        }
    }
}
```

## 동작 흐름

```text
 bind(pvs)
 |
 | L1220 선언적 바인딩 모드인데 허용 필드가 없으면 아무것도 하지 않는다
 |         (6.1의 안전 기본값: 명시한 필드만 바인딩)
 |
 +-- doBind(mpvs)
       |
       | checkAllowedFields
       |   setAllowedFields / setDisallowedFields 에 따라 걸러 낸다
       |   걸러진 값은 suppressed field 로 기록 (조용히 버리지 않고 추적 가능)
       |   = 대량 할당(mass assignment) 방어 지점
       |
       | checkRequiredFields
       |   setRequiredFields 에 있는데 값이 없으면 "required" 오류
       |
       +-- applyPropertyValues(mpvs)
             getPropertyAccessor().setPropertyValues(...)
               프로퍼티마다 타입 변환 후 setter 호출
               ConversionService 또는 등록된 PropertyEditor 사용
             PropertyBatchUpdateException
               --> 각 실패를 BindingErrorProcessor 가 FieldError 로 변환
               --> 예외를 던지지 않고 BindingResult 에 쌓는다
```

## 결과가 쓰이는 곳

```text
 채워진 대상 객체
      --> validate 단계의 검증 대상
      --> 컨트롤러 인자

 FieldError (변환 실패)
      --> typeMismatch 계열 오류 코드
      --> 검증 전에 이미 쌓여 있다
          그래서 "숫자 필드에 문자를 넣으면" @Min 검증까지 가지 않고
          타입 오류로 먼저 보고된다

 ignoreUnknownFields (기본 true)
      --> 대상에 없는 파라미터는 조용히 무시
      --> false 로 두면 알 수 없는 필드도 오류가 된다
```
