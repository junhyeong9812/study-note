# SQLExceptionTranslator

상위: [Spring JDBC](../../README.md) / [spi](../README.md)

`SQLException`을 Spring 예외 계층으로 바꾸는 전략이다. 어떤 기준으로 판정할지는 구현이 정한다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.support` / `SQLExceptionTranslator.java` L39-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/support/SQLExceptionTranslator.java#L39-L58))

```java
// SQLExceptionTranslator.java L39-L58
public interface SQLExceptionTranslator {

    @Nullable DataAccessException translate(String task, @Nullable String sql, SQLException ex);

}
```

## 흐름에서 불리는 자리

```text
 JdbcTemplate.translateException (L1548)
   getExceptionTranslator().translate(task, sql, ex)
     null 이면 UncategorizedSQLException 으로 감싼다
```

- [JdbcTemplate.translateException](../../01_JdbcTemplate.execute/02_JdbcTemplate.translateException/README.md)

## 구현 계층

```text
 SQLExceptionTranslator
   +-- AbstractFallbackSQLExceptionTranslator    커스텀 -> 자기 판정 -> fallback 순서
   |     +-- SQLErrorCodeSQLExceptionTranslator  벤더 오류 코드 (sql-error-codes.xml)
   |     +-- SQLStateSQLExceptionTranslator      SQLState 앞 두 자리
   |     +-- SQLExceptionSubclassTranslator      JDBC 4 표준 예외 타입
   +-- (사용자 구현)

 기본 선택 (JdbcAccessor.getExceptionTranslator L114-L132)
   SQLExceptionSubclassTranslator      JDBC 4 표준 예외 하위 타입으로 판정 (6.0 이후 기본)
     못 정하면 SQLStateSQLExceptionTranslator 로 폴백
   클래스패스 루트에 사용자가 sql-error-codes.xml 을 둔 경우에만
     SQLErrorCodeSQLExceptionTranslator 로 바뀐다
```
