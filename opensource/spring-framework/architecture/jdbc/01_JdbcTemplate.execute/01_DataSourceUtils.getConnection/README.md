# DataSourceUtils.getConnection

상위: [JdbcTemplate.execute](../README.md)

커넥션을 얻는 규칙이 담긴 곳이다. 트랜잭션이 열려 있으면 스레드에 바인딩된 커넥션을 재사용하고, 아니면 데이터 소스에서 새로 꺼낸다. 이 규칙 하나로 "같은 트랜잭션은 같은 커넥션"이 성립한다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.datasource` / `DataSourceUtils.java` L79-L89 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/datasource/DataSourceUtils.java#L79-L89))

```java
// DataSourceUtils.java L79-L89
public static Connection getConnection(DataSource dataSource) throws CannotGetJdbcConnectionException {
    try {
        return doGetConnection(dataSource);
    }
    catch (SQLException ex) {
        throw new CannotGetJdbcConnectionException("Failed to obtain JDBC Connection", ex);
    }
    catch (IllegalStateException ex) {
        throw new CannotGetJdbcConnectionException("Failed to obtain JDBC Connection", ex);
    }
}
```

`spring-jdbc` / `org.springframework.jdbc.datasource` / `DataSourceUtils.java` L103-L147 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/datasource/DataSourceUtils.java#L103-L147))

```java
// DataSourceUtils.java L103-L147
public static Connection doGetConnection(DataSource dataSource) throws SQLException {
    Assert.notNull(dataSource, "No DataSource specified");

    ConnectionHolder conHolder = (ConnectionHolder) TransactionSynchronizationManager.getResource(dataSource);
    if (conHolder != null && (conHolder.hasConnection() || conHolder.isSynchronizedWithTransaction())) {
        conHolder.requested();
        if (!conHolder.hasConnection()) {
            logger.debug("Fetching resumed JDBC Connection from DataSource");
            conHolder.setConnection(fetchConnection(dataSource));
        }
        return conHolder.getConnection();
    }
    // Else we either got no holder or an empty thread-bound holder here.

    logger.debug("Fetching JDBC Connection from DataSource");
    Connection con = fetchConnection(dataSource);

    if (TransactionSynchronizationManager.isSynchronizationActive()) {
        try {
            // Use same Connection for further JDBC actions within the transaction.
            // Thread-bound object will get removed by synchronization at transaction completion.
            ConnectionHolder holderToUse = conHolder;
            if (holderToUse == null) {
                holderToUse = new ConnectionHolder(con);
            }
            else {
                holderToUse.setConnection(con);
            }
            holderToUse.requested();
            TransactionSynchronizationManager.registerSynchronization(
                    new ConnectionSynchronization(holderToUse, dataSource));
            holderToUse.setSynchronizedWithTransaction(true);
            if (holderToUse != conHolder) {
                TransactionSynchronizationManager.bindResource(dataSource, holderToUse);
            }
        }
        catch (RuntimeException ex) {
            // Unexpected exception from external delegation call -> close Connection and rethrow.
            releaseConnection(con, dataSource);
            throw ex;
        }
    }

    return con;
}
```

반납 쪽도 같은 규칙을 따른다.

`spring-jdbc` / `org.springframework.jdbc.datasource` / `DataSourceUtils.java` L407-L420 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/datasource/DataSourceUtils.java#L407-L420))

```java
// DataSourceUtils.java L407-L420
public static void doReleaseConnection(@Nullable Connection con, @Nullable DataSource dataSource) throws SQLException {
    if (con == null) {
        return;
    }
    if (dataSource != null) {
        ConnectionHolder conHolder = (ConnectionHolder) TransactionSynchronizationManager.getResource(dataSource);
        if (conHolder != null && connectionEquals(conHolder, con)) {
            // It's the transactional Connection: Don't close it.
            conHolder.released();
            return;
        }
    }
    doCloseConnection(con, dataSource);
}
```

## 동작 흐름

```text
 doGetConnection(dataSource)
 |
 | L106 TransactionSynchronizationManager.getResource(dataSource)
 |        트랜잭션이 이 데이터 소스로 열려 있으면 ConnectionHolder 가 있다
 |
 +-- L107 홀더가 있고 커넥션을 들고 있거나 트랜잭션과 동기화됨
 |      requested()  참조 카운트 증가
 |      필요하면 실제 커넥션을 지금 가져온다 (지연 획득)
 |      --> 그 커넥션 반환                 = 트랜잭션에 참여
 |
 +-- L118 없으면 fetchConnection(dataSource)     풀에서 새 커넥션
 |
 +-- L120 이 DataSource 로 바인딩된 홀더가 없고 동기화는 활성인 경우
 |        (JTA 트랜잭션이 진행 중일 때도 이 갈래를 탄다)
        ConnectionHolder 를 만들어 바인딩하고
        ConnectionSynchronization 을 등록해 종료 시 정리되게 한다

 doReleaseConnection(con, dataSource)
 |
 +-- L413 바인딩된 홀더의 커넥션과 같은 커넥션인가? (프록시를 풀어 비교)
 |      같다 --> released()  참조 카운트만 줄이고 닫지 않는다
 |               (트랜잭션이 끝날 때 트랜잭션 매니저가 닫는다)
 |
 +-- 다르다 --> doCloseConnection --> con.close()
                SmartDataSource 가 닫지 말라고 하면 그대로 둔다
```

## 결과가 쓰이는 곳

```text
 반환된 커넥션
      --> JdbcTemplate.execute 가 문장을 만들고 실행하는 대상
      --> JPA/MyBatis 등 다른 접근 기술도 같은 규칙으로 트랜잭션에 참여한다
          (각자 XxxUtils 를 두고 같은 방식으로 리소스를 바인딩한다)

 참조 카운트
      --> 같은 트랜잭션 안에서 템플릿 호출이 여러 번이어도 커넥션은 하나
      --> 마지막 반납에서도 닫지 않는다. 닫는 주체는 트랜잭션 매니저다

 트랜잭션 밖 호출
      --> 매번 새 커넥션을 얻고 바로 닫는다
      --> 여러 SQL 을 하나로 묶으려면 @Transactional 이 필요하다는 근거
```
