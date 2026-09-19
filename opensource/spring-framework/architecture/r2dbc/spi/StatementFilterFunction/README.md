# StatementFilterFunction

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

문장 실행을 가로채는 필터다. 다음 단계를 부르지 않으면 실행을 막을 수 있다는 점에서, 함수형 엔드포인트의 필터와 같은 모양이다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `StatementFilterFunction.java` L40-L70 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/StatementFilterFunction.java#L40-L70))

```java
// StatementFilterFunction.java L40-L70
public interface StatementFilterFunction {

    StatementFilterFunction EMPTY_FILTER = (statement, next) -> next.execute(statement);

    Publisher<? extends Result> filter(Statement statement, ExecuteFunction next);

    default StatementFilterFunction andThen(StatementFilterFunction afterFilter) {
        Assert.notNull(afterFilter, "StatementFilterFunction must not be null");
        return (request, next) -> filter(request, afterRequest -> afterFilter.filter(afterRequest, next));
    }

}
```

## 흐름에서 불리는 자리

```text
 databaseClient.sql("...").filter(필터).fetch()
   실행 직전에 Statement 를 손볼 수 있다
     fetchSize 지정, 힌트 추가, 실행 로깅
 EMPTY_FILTER 는 아무것도 하지 않고 다음으로 넘긴다
```

- [DefaultGenericExecuteSpec.execute](../../01_DefaultGenericExecuteSpec.execute/README.md)

## 구현 계층

```text
 StatementFilterFunction
   +-- EMPTY_FILTER            (statement, next) -> next.execute(statement)
   +-- (사용자 람다)
   +-- andThen(after) 으로 합성

 ExecuteFunction
   체인의 다음 단계. execute(statement) 를 부르면 진행한다
```

## 결과가 쓰이는 곳

```text
 next.execute(statement) 를 부르지 않으면
      --> 문장이 실행되지 않는다. 그것이 곧 차단이다

 Statement 를 건드릴 수 있다는 점
      --> fetchSize 같은 드라이버 옵션을 여기서 건다
      --> 다만 표준 API 범위를 넘으면 드라이버별 분기가 필요하다

 반환값
      --> Publisher<Result> 를 그대로 흘리거나 감쌀 수 있다
      --> 실행 시간 측정 같은 관측 코드를 여기에 둔다
```

같은 모양의 계약이 [함수형 엔드포인트의 HandlerFilterFunction](../../../functional-endpoints/spi/HandlerFilterFunction/README.md)에도 있다.
