# ConnectionFactoryUtils.convertR2dbcException

상위: [Spring R2DBC](../README.md)

R2DBC 예외를 스프링 `DataAccessException`으로 옮기는 표다. JDBC와 달리 SQLState를 일일이 해석할 필요가 없다. R2DBC 스펙이 이미 예외를 계층으로 나눠 두었기 때문이다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.connection` / `ConnectionFactoryUtils.java` L226-L259 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/connection/ConnectionFactoryUtils.java#L226-L259))

```java
// ConnectionFactoryUtils.java L226-L259
public static DataAccessException convertR2dbcException(String task, @Nullable String sql, R2dbcException ex) {
    if (ex instanceof R2dbcTransientException) {
        if (ex instanceof R2dbcTransientResourceException) {
            return new TransientDataAccessResourceException(buildMessage(task, sql, ex), ex);
        }
        if (ex instanceof R2dbcRollbackException) {
            if ("40001".equals(ex.getSqlState())) {
                return new CannotAcquireLockException(buildMessage(task, sql, ex), ex);
            }
            return new PessimisticLockingFailureException(buildMessage(task, sql, ex), ex);
        }
        if (ex instanceof R2dbcTimeoutException) {
            return new QueryTimeoutException(buildMessage(task, sql, ex), ex);
        }
    }
    else if (ex instanceof R2dbcNonTransientException) {
        if (ex instanceof R2dbcNonTransientResourceException) {
            return new DataAccessResourceFailureException(buildMessage(task, sql, ex), ex);
        }
        if (ex instanceof R2dbcDataIntegrityViolationException) {
            if (indicatesDuplicateKey(ex.getSqlState(), ex.getErrorCode())) {
                return new DuplicateKeyException(buildMessage(task, sql, ex), ex);
            }
            return new DataIntegrityViolationException(buildMessage(task, sql, ex), ex);
        }
        if (ex instanceof R2dbcPermissionDeniedException) {
            return new PermissionDeniedDataAccessException(buildMessage(task, sql, ex), ex);
        }
        if (ex instanceof R2dbcBadGrammarException) {
            return new BadSqlGrammarException(task, (sql != null ? sql : ""), ex);
        }
    }
    return new UncategorizedR2dbcException(buildMessage(task, sql, ex), sql, ex);
}
```

## 동작 흐름

```text
 convertR2dbcException(task, sql, ex)
 |
 +-- [A] L227 R2dbcTransientException  (다시 시도하면 성공할 수도 있다)
 |      L228 R2dbcTransientResourceException --> TransientDataAccessResourceException
 |      L231 R2dbcRollbackException
 |             L232 SQLState 가 "40001" 이면 --> CannotAcquireLockException
 |             그 밖              --> PessimisticLockingFailureException
 |      L237 R2dbcTimeoutException --> QueryTimeoutException
 |
 +-- [B] L241 R2dbcNonTransientException  (같은 요청은 계속 실패한다)
 |      L242 R2dbcNonTransientResourceException --> DataAccessResourceFailureException
 |      L245 R2dbcDataIntegrityViolationException
 |             L246 중복 키로 판정되면 --> DuplicateKeyException
 |             그 밖                  --> DataIntegrityViolationException
 |      L251 R2dbcPermissionDeniedException --> PermissionDeniedDataAccessException
 |      L254 R2dbcBadGrammarException --> BadSqlGrammarException
 |
 +-- [C] L258 어느 쪽도 아니면 UncategorizedR2dbcException
```

```text
 JDBC 와 비교

 JDBC   SQLException 하나로 다 온다
          --> SQLState 앞 두 자리나 벤더 오류 코드 표로 판정해야 한다
          --> SQLExceptionTranslator 구현이 여럿인 이유다

 R2DBC  스펙이 Transient / NonTransient 로 먼저 갈라 준다
          --> 그 아래 타입만 보고 매핑할 수 있다
          --> SQLState 를 보는 곳은 40001(교착)과 중복 키 판정뿐이다
```

## 결과가 쓰이는 곳

```text
 번역된 DataAccessException
      --> JDBC, JPA 경로와 같은 예외 계층으로 모인다
      --> 접근 기술이 달라도 예외 처리 코드를 공유할 수 있다

 누가 부르는가
      --> inConnection / inConnectionMany 가 파이프라인 오류를 번역할 때
      --> R2dbcTransactionManager 가 커밋/롤백 실패를 번역할 때

 Transient 와 NonTransient 의 구분
      --> Transient 는 재시도가 의미 있는 실패다 (교착, 타임아웃)
      --> 재시도 정책을 예외 타입만 보고 세울 수 있다

 UncategorizedR2dbcException
      --> 표에 없는 예외의 종착지다. 원래 예외와 SQL 을 함께 담는다
      --> JDBC 의 UncategorizedSQLException 과 같은 자리다
```

JDBC 쪽 대응물은 [SQLExceptionTranslator](../../jdbc/spi/SQLExceptionTranslator/README.md), JPA 쪽은 [convertJpaAccessExceptionIfPossible](../../orm-jpa/05_EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible/README.md)에 있다.
