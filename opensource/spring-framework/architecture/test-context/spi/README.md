# spi

상위: [Spring 테스트 컨텍스트](../README.md)

테스트 지원의 확장 지점이다. 무엇을 담을지(TestContext), 언제 끼어들지(TestExecutionListener), 어떻게 만들지(ContextLoader), 어디에 보관할지(ContextCache), 무엇을 바꿀지(ContextCustomizer)를 각각 맡는다.

```text
 TestContextManager 콜백 ....... TestExecutionListener
   상태 보관 ................... TestContext
   컨텍스트 요청 ............... ContextCache (적중) 또는
                                 ContextLoader (생성) + ContextCustomizer (조정)
```

## 하위 인터페이스

- [TestContext](TestContext/README.md)
- [TestExecutionListener](TestExecutionListener/README.md)
- [ContextLoader](ContextLoader/README.md)
- [ContextCache](ContextCache/README.md)
- [ContextCustomizer](ContextCustomizer/README.md)
