# spi

상위: [Spring 표현식 언어 (SpEL)](../README.md)

파싱과 평가의 확장 지점이다. 무엇으로 파싱할지(ExpressionParser), 무엇이 되는지(Expression), 어떤 문맥에서 평가할지(EvaluationContext), 그 안에서 프로퍼티와 메서드를 어떻게 찾을지(PropertyAccessor, MethodResolver)를 각각 맡는다.

```text
 parseExpression ....... ExpressionParser (+ ParserContext)
   결과 ................ Expression
 getValue .............. EvaluationContext
   a.b ................. PropertyAccessor
   a.b(c) .............. MethodResolver
   @bean ............... BeanResolver
```

## 하위 인터페이스

- [ExpressionParser](ExpressionParser/README.md)
- [Expression](Expression/README.md)
- [EvaluationContext](EvaluationContext/README.md)
- [PropertyAccessor](PropertyAccessor/README.md)
- [MethodResolver](MethodResolver/README.md)
