# SpelExpression.getValue

상위: [Spring 표현식 언어 (SpEL)](../README.md)

구문 트리를 평가해 값을 만든다. 컴파일된 버전이 있으면 그것을 쓰고, 없으면 트리를 해석한다. 반복 평가되는 식은 일정 횟수를 넘기면 바이트코드로 컴파일된다.

## 실제 코드

`spring-expression` / `org.springframework.expression.spel.standard` / `SpelExpression.java` L254-L280 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/standard/SpelExpression.java#L254-L280))

```java
// SpelExpression.java L254-L280
@Override
public @Nullable Object getValue(EvaluationContext context) throws EvaluationException {
    Assert.notNull(context, "EvaluationContext must not be null");

    CompiledExpression compiledAst = this.compiledAst;
    if (compiledAst != null && context.isCompilationSupported()) {
        try {
            return compiledAst.getValue(context.getRootObject().getValue(), context);
        }
        catch (Throwable ex) {
            // If running in mixed mode, revert to interpreted
            if (this.configuration.getCompilerMode() == SpelCompilerMode.MIXED) {
                this.compiledAst = null;
                this.interpretedCount.set(0);
            }
            else {
                // Running in SpelCompilerMode.immediate mode - propagate exception to caller
                throw new SpelEvaluationException(ex, SpelMessage.EXCEPTION_RUNNING_COMPILED_EXPRESSION);
            }
        }
    }

    ExpressionState expressionState = new ExpressionState(context, this.configuration);
    Object result = this.ast.getValue(expressionState);
    checkCompile(expressionState);
    return result;
}
```

`spring-expression` / `org.springframework.expression.spel.standard` / `SpelExpression.java` L478-L498 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/standard/SpelExpression.java#L478-L498))

```java
// SpelExpression.java L478-L498
 */
private void checkCompile(ExpressionState expressionState) {
    this.interpretedCount.incrementAndGet();
    if (!expressionState.getEvaluationContext().isCompilationSupported()) {
        return;
    }
    SpelCompilerMode compilerMode = expressionState.getConfiguration().getCompilerMode();
    if (compilerMode != SpelCompilerMode.OFF) {
        if (compilerMode == SpelCompilerMode.IMMEDIATE) {
            if (this.interpretedCount.get() > 1) {
                compileExpression();
            }
        }
        else {
            // compilerMode = SpelCompilerMode.MIXED
            if (this.interpretedCount.get() > INTERPRETED_COUNT_THRESHOLD) {
                compileExpression();
            }
        }
    }
}
```

## 동작 흐름

```text
 getValue(context)
 |
 +-- L258 컴파일된 AST 가 있고 문맥이 컴파일을 허용하면
 |      compiledAst.getValue(root, context)     바이트코드 실행
 |      실패하면
 |        MIXED 모드   --> 컴파일 결과를 버리고 해석 모드로 되돌린다
 |        IMMEDIATE 모드 --> 예외를 호출자에게 전파
 |
 +-- L276 ExpressionState 생성 (문맥 + 설정 + 활성 객체 스택)
 +-- L277 ast.getValue(expressionState)          트리 해석
 +-- L278 checkCompile(expressionState)
        interpretedCount 증가
        컴파일러 모드가 OFF 가 아니고 임계치를 넘으면 compileExpression
          IMMEDIATE  --> 2회부터
          MIXED      --> 100회(INTERPRETED_COUNT_THRESHOLD)부터
```

노드 평가는 모두 같은 형태다.

`spring-expression` / `org.springframework.expression.spel.ast` / `SpelNodeImpl.java` L112-L120 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-expression/src/main/java/org/springframework/expression/spel/ast/SpelNodeImpl.java#L112-L120))

```java
// SpelNodeImpl.java L112-L120
@Override
public final @Nullable Object getValue(ExpressionState expressionState) throws EvaluationException {
    return getValueInternal(expressionState).getValue();
}

@Override
public final TypedValue getTypedValue(ExpressionState expressionState) throws EvaluationException {
    return getValueInternal(expressionState);
}
```

1. 노드별 평가와 프로퍼티 접근은 [SpelNodeImpl.getValue](01_SpelNodeImpl.getValue/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 평가 결과
      --> 호출자에게. 기대 타입이 있으면 TypeConverter 로 변환
      --> @Value 주입 값, 캐시 키, 조건 판정 등

 ExpressionState
      --> 평가 한 번의 작업 공간 (활성 객체 스택, 변수 스코프)
      --> #this, #root 가 여기서 해석된다

 컴파일
      --> 기본은 OFF 라 대부분의 애플리케이션은 해석 모드로만 동작한다
      --> 켜면 반복 평가가 빨라지지만, 컴파일 가능한 식에만 적용된다
          (타입 정보가 확정되지 않는 식은 컴파일되지 않는다)
```

## 하위 메서드

- [01 SpelNodeImpl.getValue](01_SpelNodeImpl.getValue/README.md)
