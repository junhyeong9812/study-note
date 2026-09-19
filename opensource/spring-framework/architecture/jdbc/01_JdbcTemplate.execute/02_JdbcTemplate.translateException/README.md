# JdbcTemplate.translateException

상위: [JdbcTemplate.execute](../README.md)

드라이버가 던진 `SQLException`을 Spring의 `DataAccessException` 계층으로 바꾼다. 이 변환 덕분에 서비스 코드가 벤더별 오류 코드를 몰라도 된다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.core` / `JdbcTemplate.java` L1547-L1551 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/JdbcTemplate.java#L1547-L1551))

```java
// JdbcTemplate.java L1547-L1551
 */
protected DataAccessException translateException(String task, @Nullable String sql, SQLException ex) {
    DataAccessException dae = getExceptionTranslator().translate(task, sql, ex);
    return (dae != null ? dae : new UncategorizedSQLException(task, sql, ex));
}
```

변환기는 여러 단계를 순서대로 시도한다.

`spring-jdbc` / `org.springframework.jdbc.support` / `AbstractFallbackSQLExceptionTranslator.java` L88-L115 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/support/AbstractFallbackSQLExceptionTranslator.java#L88-L115))

```java
// AbstractFallbackSQLExceptionTranslator.java L88-L115
 */
@Override
public @Nullable DataAccessException translate(String task, @Nullable String sql, SQLException ex) {
    Assert.notNull(ex, "Cannot translate a null SQLException");

    SQLExceptionTranslator custom = getCustomTranslator();
    if (custom != null) {
        DataAccessException dae = custom.translate(task, sql, ex);
        if (dae != null) {
            // Custom exception match found.
            return dae;
        }
    }

    DataAccessException dae = doTranslate(task, sql, ex);
    if (dae != null) {
        // Specific exception match found.
        return dae;
    }

    // Looking for a fallback...
    SQLExceptionTranslator fallback = getFallbackTranslator();
    if (fallback != null) {
        return fallback.translate(task, sql, ex);
    }

    return null;
}
```

## 동작 흐름

```text
 translateException(task, sql, ex)
 |
 +-- getExceptionTranslator().translate(task, sql, ex)
 |     |
 |     | [1] 사용자 지정 변환기가 있으면 먼저 시도
 |     |
 |     | [2] doTranslate       구현별 판정
 |     |       SQLErrorCodeSQLExceptionTranslator  DB 벤더의 오류 코드 표로 판정
 |     |       SQLStateSQLExceptionTranslator      SQLState 앞 두 자리로 판정
 |     |       SQLExceptionSubclassTranslator      JDBC 4 표준 예외 하위 타입으로 판정
 |     |
 |     +-- [3] 못 정하면 fallback 변환기로 위임
 |
 +-- 그래도 null 이면 UncategorizedSQLException 으로 감싼다
```

```text
 변환 결과의 계층 (일부)

 DataAccessException
   +-- NonTransientDataAccessException      다시 시도해도 같은 결과
   |     +-- DataIntegrityViolationException
   |     |     +-- DuplicateKeyException          유니크 제약 위반
   |     +-- BadSqlGrammarException               SQL 문법 오류
   |     +-- DataAccessResourceFailureException   연결 실패 등
   +-- TransientDataAccessException          재시도할 만함
   |     +-- QueryTimeoutException
   |     +-- ConcurrencyFailureException
   |           +-- CannotAcquireLockException
   +-- UncategorizedDataAccessException
         +-- UncategorizedSQLException            분류 실패
```

## 결과가 쓰이는 곳

```text
 던져진 DataAccessException
      --> execute 밖으로 --> 호출 코드
      --> 모두 런타임 예외라 체크 예외 처리가 강제되지 않는다
      --> @Transactional 의 기본 롤백 규칙(언체크 예외)에 그대로 걸린다

 UncategorizedSQLException 이 보인다면
      --> 변환기가 그 오류 코드를 모르는 상태
      --> sql-error-codes.xml 또는 커스텀 변환기로 보완할 수 있다

 벤더 판정
      --> SQLErrorCodeSQLExceptionTranslator 는 DatabaseMetaData 의 제품명으로
          어떤 코드 표를 쓸지 정한다 (데이터 소스에 한 번 접근한다)
```
