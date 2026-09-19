# Spring R2DBC

논블로킹 드라이버로 관계형 DB를 다루는 흐름이다. JDBC 흐름과 하는 일은 같지만, 커넥션을 스레드가 아니라 구독 컨텍스트에 묶고, 결과를 값이 아니라 `Flux`로 돌려준다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 클라이언트와 바인딩 계약 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 databaseClient.sql("SELECT * FROM users WHERE id = :id")
               .bind("id", 42).map(...).one()
 |
 +-- [01] DefaultGenericExecuteSpec.execute
 |        SQL 과 바인딩을 담은 ResultFunction 을 만든다
 |        아직 아무것도 실행하지 않는다. 조립만 한다
 |        :id 같은 이름 파라미터는 NamedParameterExpander 가
 |          드라이버 표기($1, ?, @P0_id)로 펼친다
 |
 +-- [02] DefaultDatabaseClient.inConnection
 |        Mono.usingWhen 으로 커넥션의 수명을 구독에 묶는다
 |        close 를 막은 프록시를 콜백에 넘긴다
 |        R2dbcException 은 DataAccessException 으로 바꾼다
 |
 +-- [02-01] ConnectionFactoryUtils.doGetConnection
 |        구독 컨텍스트에 묶인 커넥션이 있으면 그것
 |        없으면 팩토리에서 새로 받는다
 |        트랜잭션이 아예 없으면(NoTransactionException) 그냥 새로 만든다
 |
 +-- 결과 Publisher 를 구독하는 시점에 SQL 이 실제로 나간다

 [트랜잭션]

 @Transactional (리액티브) --> TransactionalOperator --> R2dbcTransactionManager
 |
 +-- [03] doBegin
 |        커넥션을 받아 ConnectionHolder 로 구독 컨텍스트에 바인딩
 |        원래 autoCommit 을 기억해 둔 뒤 con.beginTransaction(정의)
 |          격리 수준과 읽기 전용은 정의에 담아 드라이버에 넘긴다
 |        NESTED 면 세이브포인트
 |
 +-- [04] doCommit
          con.commitTransaction()  --> R2dbcException 은 번역해서 던진다

 [예외 변환]

 +-- [05] ConnectionFactoryUtils.convertR2dbcException
          R2DBC 예외 계층 --> 스프링 DataAccessException 계층
```

```text
 JDBC 와 나란히 보기

 JDBC                                   R2DBC
 JdbcTemplate.execute                   DatabaseClient.sql(...).fetch()
 DataSourceUtils.getConnection          ConnectionFactoryUtils.doGetConnection
 스레드 로컬에 커넥션 바인딩             구독 컨텍스트에 커넥션 바인딩
 DataSourceTransactionManager           R2dbcTransactionManager
 PlatformTransactionManager             ReactiveTransactionManager
 SQLExceptionTranslator                 ConnectionFactoryUtils.convertR2dbcException
 호출이 반환되면 SQL 이 끝나 있다        구독해야 SQL 이 나간다
```

## 어디에서 쓰이는가

```text
 [트랜잭션] 리액티브 트랜잭션 매니저가 커넥션을 구독 컨텍스트에 묶는다
   같은 체인 안의 모든 DatabaseClient 호출이 그 커넥션을 쓴다
 [WebFlux] 컨트롤러가 돌려준 Flux 가 구독될 때 쿼리가 실행된다
 [빈 생성] ConnectionFactory 빈 하나가 클라이언트와 트랜잭션 매니저의 입력이 된다
```

블로킹 쪽 같은 흐름은 [JDBC](../jdbc/README.md), 트랜잭션 골격은 [트랜잭션](../transaction/README.md), 결과를 흘려보내는 웹 계층은 [WebFlux 요청 처리](../webflux-request-processing/README.md)에 있다.

## 단계

1. [DefaultGenericExecuteSpec.execute](01_DefaultGenericExecuteSpec.execute/README.md)가 SQL과 바인딩을 파이프라인으로 조립한다.
2. [DefaultDatabaseClient.inConnection](02_DefaultDatabaseClient.inConnection/README.md)이 커넥션 수명을 구독에 묶는다.
3. [R2dbcTransactionManager.doBegin](03_R2dbcTransactionManager.doBegin/README.md)이 트랜잭션을 연다.
4. [R2dbcTransactionManager.doCommit](04_R2dbcTransactionManager.doCommit/README.md)이 커밋한다.
5. [ConnectionFactoryUtils.convertR2dbcException](05_ConnectionFactoryUtils.convertR2dbcException/README.md)이 예외를 번역한다.

## 결과가 쓰이는 곳

```text
 FetchSpec / RowsFetchSpec
      --> one(), first(), all(), rowsUpdated() 가 각각 Mono 나 Flux 를 만든다
      --> 그 자체로는 아무 일도 하지 않는다. 구독이 방아쇠다

 구독 컨텍스트에 묶인 커넥션
      --> 같은 리액티브 체인 안에서만 공유된다
      --> 스레드가 바뀌어도 따라간다. 스레드 로컬을 쓰지 않는 이유다

 번역된 DataAccessException
      --> JDBC 경로와 같은 예외 타입으로 모인다
      --> 접근 기술이 달라도 예외 처리 코드를 공유할 수 있다

 커넥션 반납
      --> 트랜잭션이 없으면 체인이 끝날 때 바로 닫는다
      --> 트랜잭션 안이면 커밋/롤백 뒤 정리 단계가 닫는다
```

## 다루지 않는 것

바인드 마커 생성 규칙(`BindMarkersFactory`의 드라이버별 구현), 스크립트 초기화(`ConnectionFactoryInitializer`, `ScriptUtils`), 라우팅 커넥션 팩토리(`AbstractRoutingConnectionFactory`), `BeanPropertyRowMapper` 계열의 매핑 세부는 같은 뼈대의 갈래라 요약만 했다. R2DBC SPI 자체(드라이버 구현)와 리액티브 스트림 규약도 범위 밖이다.

## 하위 메서드

- [01 DefaultGenericExecuteSpec.execute](01_DefaultGenericExecuteSpec.execute/README.md)
- [02 DefaultDatabaseClient.inConnection](02_DefaultDatabaseClient.inConnection/README.md)
- [03 R2dbcTransactionManager.doBegin](03_R2dbcTransactionManager.doBegin/README.md)
- [04 R2dbcTransactionManager.doCommit](04_R2dbcTransactionManager.doCommit/README.md)
- [05 ConnectionFactoryUtils.convertR2dbcException](05_ConnectionFactoryUtils.convertR2dbcException/README.md)
- [spi](spi/README.md) — 클라이언트, 커넥션 접근, 결과 스펙, 문장 필터, 바인드 마커
