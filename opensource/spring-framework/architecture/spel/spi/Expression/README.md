# Expression

상위: [Spring 표현식 언어 (SpEL)](../../README.md) / [spi](../README.md)

파싱된 식이다. 값 읽기, 값 쓰기, 타입 질의를 제공하고 스레드 안전하다.

## 실제 코드

`spring-expression` / `org.springframework.expression` / `Expression.java` L52-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/Expression.java#L52-L120))

```java
// Expression.java L52-L120
public interface Expression {

    String getExpressionString();

    @Nullable Object getValue() throws EvaluationException;

    <T> @Nullable T getValue(@Nullable Class<T> desiredResultType) throws EvaluationException;

    @Nullable Object getValue(@Nullable Object rootObject) throws EvaluationException;

    <T> @Nullable T getValue(@Nullable Object rootObject, @Nullable Class<T> desiredResultType)
            throws EvaluationException;

    @Nullable Object getValue(EvaluationContext context) throws EvaluationException;

    @Nullable Object getValue(EvaluationContext context, @Nullable Object rootObject) throws EvaluationException;

```

## 흐름에서 불리는 자리

```text
 getValue(context) / getValue(context, expectedType)
   SpelExpression 이 컴파일 여부를 보고 실행 경로를 정한다
 setValue(context, value)
   쓰기 가능한 노드(프로퍼티 등)일 때
```

- [SpelExpression.getValue](../../02_SpelExpression.getValue/README.md)

## 구현 계층

```text
 Expression
   +-- SpelExpression                 SpEL AST 보유
   +-- LiteralExpression              문자열 조각
   +-- CompositeStringExpression      템플릿 조각들의 합

 재사용
   파싱 비용이 있으므로 캐시해 두고 반복 평가한다
   Spring 내부(캐시 키, 이벤트 조건 등)도 모두 캐시한다
```
