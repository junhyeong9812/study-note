# RowMapper

상위: [Spring JDBC](../../README.md) / [spi](../README.md)

`ResultSet`의 한 행을 객체 하나로 바꾼다. 행 단위 변환이라 스트리밍에도 그대로 쓸 수 있다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.core` / `RowMapper.java` L52-L66 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/RowMapper.java#L52-L66))

```java
// RowMapper.java L52-L66
public interface RowMapper<T extends @Nullable Object> {

    T mapRow(ResultSet rs, int rowNum) throws SQLException;

}
```

`spring-jdbc` / `org.springframework.jdbc.core` / `ResultSetExtractor.java` L53-L67 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/ResultSetExtractor.java#L53-L67))

```java
// ResultSetExtractor.java L53-L67
public interface ResultSetExtractor<T extends @Nullable Object> {

    T extractData(ResultSet rs) throws SQLException, DataAccessException;

}
```

## 흐름에서 불리는 자리

```text
 query(sql, rowMapper, args)
   내부적으로 RowMapperResultSetExtractor 로 감싼다
   ResultSet 을 돌며 행마다 mapRow(rs, rowNum) 호출
 ResultSetExtractor 는 ResultSet 전체를 한 번에 받는다
   (여러 행을 하나의 객체로 접거나, 커서를 직접 다룰 때)
```

- [JdbcTemplate.execute](../../01_JdbcTemplate.execute/README.md)

## 구현 계층

```text
 RowMapper<T>
   +-- BeanPropertyRowMapper       컬럼명 -> 프로퍼티 (언더스코어/카멜 변환)
   +-- DataClassRowMapper          record/생성자 기반
   +-- SingleColumnRowMapper       단일 컬럼
   +-- (람다 구현)

 ResultSetExtractor<T>
   +-- RowMapperResultSetExtractor    RowMapper 를 감싼 것
   +-- (사용자 구현: 1:N 조인 결과를 한 객체로 접기)

 RowCallbackHandler
   반환값 없이 행마다 부수 효과만 (대용량 처리)
```
