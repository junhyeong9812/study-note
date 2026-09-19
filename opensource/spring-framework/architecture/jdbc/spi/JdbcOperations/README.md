# JdbcOperations

상위: [Spring JDBC](../../README.md) / [spi](../README.md)

`JdbcTemplate`이 구현하는 연산 목록이다. 쿼리, 갱신, 배치, 저장 프로시저가 모두 여기에 선언돼 있고, 테스트에서 목으로 대체하기 쉬운 경계가 된다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.core` / `JdbcOperations.java` L53-L111 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/JdbcOperations.java#L53-L111))

```java
// JdbcOperations.java L53-L111
public interface JdbcOperations {

    //-------------------------------------------------------------------------
    // Methods dealing with a plain java.sql.Connection
    //-------------------------------------------------------------------------

    <T extends @Nullable Object> T execute(ConnectionCallback<T> action) throws DataAccessException;

    //-------------------------------------------------------------------------
    // Methods dealing with static SQL (java.sql.Statement)
    //-------------------------------------------------------------------------

    <T extends @Nullable Object> T execute(StatementCallback<T> action) throws DataAccessException;

    void execute(String sql) throws DataAccessException;

    <T extends @Nullable Object> T query(String sql, ResultSetExtractor<T> rse) throws DataAccessException;
```

## 흐름에서 불리는 자리

```text
 사용자 코드 --> jdbcTemplate.query / update / execute
 모든 메서드가 내부적으로 execute(콜백) 로 수렴한다
```

- [JdbcTemplate.execute](../../01_JdbcTemplate.execute/README.md)

## 구현 계층

```text
 JdbcOperations
   +-- JdbcTemplate                     기본 구현
 그 위의 편의 API
   +-- NamedParameterJdbcTemplate       :name 파라미터 --> 내부에서 JdbcTemplate 위임
   +-- JdbcClient                       fluent API (sql().param().query())
   +-- SimpleJdbcInsert / SimpleJdbcCall  메타데이터 기반 삽입/호출

 JdbcClient 도 결국 JdbcTemplate 을 감싼다
   sql("...").param(42).query(User.class).single()      인덱스 파라미터
     --> JdbcTemplate.execute  (NamedParameterJdbcTemplate 를 거치지 않는다)
   sql("...").param("id", 42).query(User.class).single()  이름 파라미터
     --> NamedParameterJdbcTemplate --> JdbcTemplate.execute
```
