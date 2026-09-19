# MessageCodesResolver

상위: [Spring 검증과 데이터 바인딩](../../README.md) / [spi](../README.md)

오류 하나를 여러 메시지 코드 후보로 펼친다. 구체적인 코드부터 일반적인 코드까지 순서대로 만들어, 메시지를 유연하게 정의할 수 있게 한다.

## 실제 코드

`spring-context` / `org.springframework.validation` / `MessageCodesResolver.java` L35-L57 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/validation/MessageCodesResolver.java#L35-L57))

```java
// MessageCodesResolver.java L35-L57
public interface MessageCodesResolver {

    String[] resolveMessageCodes(String errorCode, String objectName);

    String[] resolveMessageCodes(String errorCode, String objectName, String field, @Nullable Class<?> fieldType);

}
```

## 흐름에서 불리는 자리

```text
 rejectValue / 제약 위반 처리 시
   resolveMessageCodes(errorCode, objectName, field, fieldType)
   --> FieldError 에 코드 배열로 저장
 메시지 표시 시
   MessageSource 가 배열을 앞에서부터 찾아 첫 번째로 존재하는 메시지를 쓴다
```

- [DataBinder.validate](../../02_DataBinder.validate/README.md)

## 구현 계층

```text
 MessageCodesResolver
   +-- DefaultMessageCodesResolver

 생성 예 (errorCode=NotNull, objectName=userForm, field=email, type=String)
   NotNull.userForm.email
   NotNull.email
   NotNull.java.lang.String
   NotNull

 messages.properties 에 어느 수준으로 정의하느냐에 따라
 전역 메시지와 필드별 메시지를 섞어 쓸 수 있다
```
