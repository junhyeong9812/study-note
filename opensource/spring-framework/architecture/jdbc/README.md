# Spring JDBC

`jdbcTemplate.query(...)` 한 번이 커넥션을 얻고, SQL을 실행하고, 결과를 객체로 바꾸고, 자원을 정리하기까지의 흐름을 위에서 아래로 따라간다. 트랜잭션이 열려 있으면 같은 커넥션을 쓰고, `SQLException`은 Spring의 예외 계층으로 바뀐다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 콜백과 변환 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 jdbcTemplate.query("select ... where id = ?", rowMapper, 42)
 또는 jdbcClient.sql("...").param(42).query(User.class).single()
 |
 +-- [01] JdbcTemplate.execute(PreparedStatementCreator, PreparedStatementCallback)
        |
        +-- [01-01] DataSourceUtils.getConnection
        |      트랜잭션이 열려 있으면 --> 스레드에 바인딩된 커넥션 재사용
        |      아니면               --> DataSource 에서 새로 꺼낸다
        |
        +-- psc.createPreparedStatement(con)     SQL 로 PreparedStatement 생성
        +-- applyStatementSettings(ps)           fetchSize, maxRows, queryTimeout
        +-- action.doInPreparedStatement(ps)     <-- 실제 실행 (쿼리 또는 갱신)
        |      쿼리면 ResultSet --> RowMapper/ResultSetExtractor 로 객체 변환
        |
        +-- [01-02] translateException            SQLException --> DataAccessException
        |
        +-- finally
               PreparedStatement 닫기
               DataSourceUtils.releaseConnection
                 트랜잭션 커넥션이면 닫지 않고 참조 카운트만 줄인다
```

템플릿 메서드 구조라 모든 변형이 같은 골격을 공유한다.

```text
 execute(ConnectionCallback)          커넥션만 얻어 사용자 코드에 넘긴다
 execute(StatementCallback)           Statement 까지 만들어 준다 (정적 SQL)
 execute(PreparedStatementCreator,    PreparedStatement 까지 (파라미터 바인딩)
         PreparedStatementCallback)
 execute(CallableStatementCreator,    CallableStatement 까지 (저장 프로시저)
         CallableStatementCallback)

 query / update / batchUpdate 는 모두 위 중 하나를 콜백으로 감싼 것
```

## 단계

1. [JdbcTemplate.execute](01_JdbcTemplate.execute/README.md)가 자원 획득과 정리, 예외 변환을 맡고 실제 작업은 콜백에 넘긴다.

## 트랜잭션과의 관계

```text
 @Transactional 메서드 안에서 jdbcTemplate 사용
   [트랜잭션] doBegin 이 커넥션을 열어 TransactionSynchronizationManager 에 바인딩
   [JDBC]     DataSourceUtils.getConnection 이 그 커넥션을 찾아 재사용
              releaseConnection 은 닫지 않는다 (트랜잭션이 끝날 때 닫힌다)

 트랜잭션 밖에서 사용
   매 호출이 커넥션을 새로 얻고 바로 반납한다 (자동 커밋)
```

자세한 것은 [트랜잭션](../transaction/README.md) 흐름에 있다.

## 결과가 쓰이는 곳

```text
 매핑된 객체
      --> 호출 코드
      --> JdbcClient 는 같은 JdbcTemplate 위에 fluent API 를 얹은 것이다

 DataAccessException
      --> 벤더별 SQLException 이 Spring 계층 예외로 바뀐다
      --> DuplicateKeyException, DataIntegrityViolationException 등
      --> 이 변환 덕분에 서비스 코드가 드라이버에 의존하지 않는다
```

## 다루지 않는 것

`NamedParameterJdbcTemplate`의 이름 파라미터 파싱, 배치 처리, 저장 프로시저(`SimpleJdbcCall`) 경로는 같은 템플릿 위의 변형이라 이 지도에서는 요약만 했다.

## 하위 메서드

- [01 JdbcTemplate.execute](01_JdbcTemplate.execute/README.md)
- [spi](spi/README.md) — 콜백, 행 매퍼, 예외 변환기
