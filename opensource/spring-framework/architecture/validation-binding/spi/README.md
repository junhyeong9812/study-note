# spi

상위: [Spring 검증과 데이터 바인딩](../README.md)

바인딩과 검증의 확장 지점이다. 무엇으로 바꿀지(Converter), 무엇을 검사할지(Validator), 어디에 모을지(Errors), 어떤 메시지로 보일지(MessageCodesResolver)를 각각 맡는다.

```text
 DataBinder.bind
   타입 변환 ........ Converter / PropertyEditor
   오류 수집 ........ Errors (BindingResult)
 DataBinder.validate
   검증 ............. Validator / SmartValidator
   오류 코드 ........ MessageCodesResolver --> MessageSource
```

## 하위 인터페이스

- [Validator](Validator/README.md)
- [Errors](Errors/README.md)
- [MessageCodesResolver](MessageCodesResolver/README.md)
- [Converter](Converter/README.md)
