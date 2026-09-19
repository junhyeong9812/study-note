# DefaultGenericExecuteSpec.execute

상위: [Spring R2DBC](../README.md)

`sql(...).bind(...)`로 쌓아 둔 것을 실행 가능한 파이프라인으로 바꾸는 자리다. 이름이 `execute`지만 여기서 실행되는 것은 없다. 조립만 하고 돌아간다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `DefaultDatabaseClient.java` L448-L452 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/DefaultDatabaseClient.java#L448-L452))

```java
// DefaultDatabaseClient.java L448-L452
private <T> FetchSpec<T> execute(Supplier<String> sqlSupplier, Function<Result, Publisher<T>> resultAdapter) {
    ResultFunction resultHandler = getResultFunction(sqlSupplier);
    return new DefaultFetchSpec<>(DefaultDatabaseClient.this, resultHandler,
            connection -> sumRowsUpdated(resultHandler, connection), resultAdapter);
}
```

문장을 만드는 함수는 이 안에 있다.

`spring-r2dbc` / `org.springframework.r2dbc.core` / `DefaultDatabaseClient.java` L397-L446 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/DefaultDatabaseClient.java#L397-L446))

```java
// DefaultDatabaseClient.java L397-L446
private ResultFunction getResultFunction(Supplier<String> sqlSupplier) {
    BiFunction<Connection, String, Statement> statementFunction = (connection, sql) -> {
        if (logger.isDebugEnabled()) {
            logger.debug("Executing SQL statement [" + sql + "]");
        }
        if (sqlSupplier instanceof PreparedOperation<?> preparedOperation) {
            Statement statement = connection.createStatement(sql);
            BindTarget bindTarget = new StatementWrapper(statement);
            preparedOperation.bindTo(bindTarget);
            return statement;
        }

        if (DefaultDatabaseClient.this.namedParameterExpander != null) {
            Map<String, Parameter> remainderByName = new LinkedHashMap<>(this.byName);
            Map<Integer, Parameter> remainderByIndex = new LinkedHashMap<>(this.byIndex);

            List<String> parameterNames = DefaultDatabaseClient.this.namedParameterExpander.getParameterNames(sql);
            MapBindParameterSource namedBindings = retrieveParameters(
                    sql, parameterNames, remainderByName, remainderByIndex);

            PreparedOperation<String> operation = DefaultDatabaseClient.this.namedParameterExpander.expand(
                    sql, DefaultDatabaseClient.this.bindMarkersFactory, namedBindings);

            String expanded = getRequiredSql(operation);
            if (logger.isTraceEnabled()) {
                logger.trace("Expanded SQL [" + expanded + "]");
            }

            Statement statement = connection.createStatement(expanded);
            BindTarget bindTarget = new StatementWrapper(statement);

            operation.bindTo(bindTarget);

            bindByName(statement, remainderByName);
            bindByIndex(statement, remainderByIndex);

            return statement;
        }

        Statement statement = connection.createStatement(sql);

        bindByIndex(statement, this.byIndex);
        bindByName(statement, this.byName);

        return statement;
    };

    return new ResultFunction(sqlSupplier, statementFunction, this.filterFunction,
            DefaultDatabaseClient.this.executeFunction);
}
```

## 동작 흐름

```text
 execute(sqlSupplier, resultAdapter)
 |
 | L449 getResultFunction(sqlSupplier)
 |        커넥션을 받으면 Statement 를 만들어 실행하는 함수를 만든다
 |
 +-- L450 DefaultFetchSpec 을 만들어 돌려준다
        (클라이언트, 결과 함수, 갱신 건수 함수, 결과 어댑터)
        = 여기까지 아무 SQL 도 나가지 않았다

 getResultFunction(sqlSupplier)      문장 만들기 세 갈래
 |
 +-- L402 sqlSupplier 가 PreparedOperation
 |        L403 createStatement(sql) 후 operation.bindTo(대상)
 |
 +-- L409 namedParameterExpander 가 있다 (기본 구성)
 |        L413 SQL 에서 :name 파라미터 이름을 뽑는다
 |        L414 바인딩 값을 이름 순서대로 모은다
 |        L417 expand(sql, bindMarkersFactory, 값들)
 |              :id --> $1 / ? / @P0_id  드라이버 표기로 펼친다
 |        L425 펼친 SQL 로 Statement 생성 후 bindTo (L428)
 |        L430-L431 이름/인덱스로 남은 바인딩을 마저 건다
 |
 +-- 그 밖
        SQL 그대로 createStatement
```

```text
 이름 파라미터가 필요한 이유

 JDBC        ? 하나뿐이라 순서만 맞추면 된다
 R2DBC       드라이버마다 표기가 다르다
               PostgreSQL / H2   $1, $2
               MySQL / MariaDB   ?
               SQL Server        @P0_id  (이름이 힌트로 붙는다)
             BindMarkersFactory 가 드라이버를 보고 표기를 정하고,
             NamedParameterExpander 가 :name 을 그 표기로 바꾼다
```

1. 조립된 파이프라인이 실제로 커넥션을 얻는 곳은 [DefaultDatabaseClient.inConnection](../02_DefaultDatabaseClient.inConnection/README.md)이다.

## 결과가 쓰이는 곳

```text
 반환한 FetchSpec
      --> one()   결과가 0개면 빈 Mono, 2개 이상이면 오류
      --> first() 첫 행만
      --> all()   Flux 로 전부
      --> rowsUpdated()  갱신 건수
      --> 각 메서드가 inConnection / inConnectionMany 를 부른다

 ResultFunction
      --> 커넥션을 인자로 받는 함수다. 커넥션은 나중에 주입된다
      --> SqlProvider 도 구현해, 예외 메시지에 실행하려던 SQL 을 실을 수 있다

 바인딩 누락
      --> 이름에 맞는 값이 없으면 InvalidDataAccessApiUsageException
        "No parameter specified for [...] in query [...]"
      --> 다만 이 검사는 Statement 를 만드는 람다 안에 있다 (L414)
          구독해서 커넥션을 얻은 뒤에야 드러난다
```

같은 자리에서 JDBC가 하는 일은 [JdbcTemplate.execute](../../jdbc/01_JdbcTemplate.execute/README.md)에 있다.
