# JdbcTemplate.execute

상위: [Spring JDBC](../README.md)

JDBC의 상투적인 절차(커넥션 획득, 문장 생성, 실행, 닫기, 예외 변환)를 한곳에 모은 템플릿 메서드다. 사용자 코드는 콜백 안에서 실행 부분만 쓴다.

## 실제 코드

가장 단순한 형태는 커넥션만 넘기는 것이다.

`spring-jdbc` / `org.springframework.jdbc.core` / `JdbcTemplate.java` L358-L379 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/JdbcTemplate.java#L358-L379))

```java
// JdbcTemplate.java L358-L379
@Override
public <T extends @Nullable Object> T execute(ConnectionCallback<T> action) throws DataAccessException {
    Assert.notNull(action, "Callback object must not be null");

    Connection con = DataSourceUtils.getConnection(obtainDataSource());
    try {
        // Create close-suppressing Connection proxy, also preparing returned Statements.
        Connection conToUse = createConnectionProxy(con);
        return action.doInConnection(conToUse);
    }
    catch (SQLException ex) {
        // Release Connection early, to avoid potential connection pool deadlock
        // in the case when the exception translator hasn't been initialized yet.
        String sql = getSql(action);
        DataSourceUtils.releaseConnection(con, getDataSource());
        con = null;
        throw translateException("ConnectionCallback", sql, ex);
    }
    finally {
        DataSourceUtils.releaseConnection(con, getDataSource());
    }
}
```

실제로 가장 많이 쓰이는 `PreparedStatement` 경로다.

`spring-jdbc` / `org.springframework.jdbc.core` / `JdbcTemplate.java` L655-L700 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/JdbcTemplate.java#L655-L700))

```java
// JdbcTemplate.java L655-L700
private <T extends @Nullable Object> T execute(PreparedStatementCreator psc, PreparedStatementCallback<T> action, boolean closeResources)
        throws DataAccessException {

    Assert.notNull(psc, "PreparedStatementCreator must not be null");
    Assert.notNull(action, "Callback object must not be null");
    if (logger.isDebugEnabled()) {
        String sql = getSql(psc);
        logger.debug("Executing prepared SQL statement" + (sql != null ? " [" + sql + "]" : ""));
    }

    Connection con = DataSourceUtils.getConnection(obtainDataSource());
    PreparedStatement ps = null;
    try {
        ps = psc.createPreparedStatement(con);
        applyStatementSettings(ps);
        T result = action.doInPreparedStatement(ps);
        handleWarnings(ps);
        return result;
    }
    catch (SQLException ex) {
        // Release Connection early, to avoid potential connection pool deadlock
        // in the case when the exception translator hasn't been initialized yet.
        if (psc instanceof ParameterDisposer parameterDisposer) {
            parameterDisposer.cleanupParameters();
        }
        if (ps != null) {
            handleWarnings(ps, ex);
        }
        String sql = getSql(psc);
        psc = null;
        JdbcUtils.closeStatement(ps);
        ps = null;
        DataSourceUtils.releaseConnection(con, getDataSource());
        con = null;
        throw translateException("PreparedStatementCallback", sql, ex);
    }
    finally {
        if (closeResources) {
            if (psc instanceof ParameterDisposer parameterDisposer) {
                parameterDisposer.cleanupParameters();
            }
            JdbcUtils.closeStatement(ps);
            DataSourceUtils.releaseConnection(con, getDataSource());
        }
    }
}
```

## 동작 흐름

```text
 execute(psc, action, closeResources)
 |
 | L665 DataSourceUtils.getConnection(dataSource)
 |        트랜잭션 커넥션이 있으면 그것, 없으면 새 커넥션
 |
 | L668 psc.createPreparedStatement(con)
 |        SQL 문자열로 PreparedStatement 생성 (파라미터 바인딩은 아래 콜백에서)
 | L669 applyStatementSettings(ps)
 |        fetchSize, maxRows, queryTimeout 적용
 |        트랜잭션 타임아웃이 있으면 남은 시간으로 queryTimeout 설정
 |
 | L670 action.doInPreparedStatement(ps)     <-- 사용자 작업
 |        query  --> ps.executeQuery() 후 ResultSet 을 매퍼에 넘김
 |        update --> ps.executeUpdate()
 |
 | L671 handleWarnings(ps)      경고를 로깅하거나 예외로 (ignoreWarnings 설정)
 |
 +-- L674 SQLException
 |      파라미터 정리, 문장 닫기, 커넥션 먼저 반납
 |        (예외 변환기 초기화가 커넥션을 필요로 할 수 있어 풀 교착을 피하려는 순서)
 |      translateException(...) 으로 DataAccessException 을 만들어 던진다
 |
 +-- finally (closeResources 일 때)
        파라미터 정리 --> 문장 닫기 --> 커넥션 반납
        스트리밍 결과를 돌려주는 경우에는 closeResources = false 로 두고
        호출자가 닫도록 한다
```

1. 커넥션 획득과 반납의 규칙은 [DataSourceUtils.getConnection](01_DataSourceUtils.getConnection/README.md)에 있다.
2. 예외 변환은 [translateException](02_JdbcTemplate.translateException/README.md)이 한다.

## 결과가 쓰이는 곳

```text
 콜백 반환값
      --> query 계열: 매핑된 객체 또는 목록
      --> update 계열: 영향 행 수
      --> 호출 코드로 그대로 전달

 close-suppressing 프록시 (ConnectionCallback 경로)
      --> 사용자가 con.close() 를 불러도 실제로 닫히지 않는다
      --> 트랜잭션 커넥션을 사용자 코드가 실수로 닫는 것을 막는다

 자원 정리 순서
      --> 문장을 먼저 닫고 커넥션을 반납한다
      --> 예외 경로에서도 같은 순서를 지킨다
```

## 하위 메서드

- [01 DataSourceUtils.getConnection](01_DataSourceUtils.getConnection/README.md)
- [02 JdbcTemplate.translateException](02_JdbcTemplate.translateException/README.md)
