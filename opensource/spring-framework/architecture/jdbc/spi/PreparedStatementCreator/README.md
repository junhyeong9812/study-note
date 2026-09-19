# PreparedStatementCreator

상위: [Spring JDBC](../../README.md) / [spi](../README.md)

SQL로 `PreparedStatement`를 만드는 책임과, 만들어진 문장에 파라미터를 채우는 책임을 나눈 두 인터페이스다.

## 실제 코드

`spring-jdbc` / `org.springframework.jdbc.core` / `PreparedStatementCreator.java` L44-L57 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/PreparedStatementCreator.java#L44-L57))

```java
// PreparedStatementCreator.java L44-L57
public interface PreparedStatementCreator {

    PreparedStatement createPreparedStatement(Connection con) throws SQLException;

}
```

`spring-jdbc` / `org.springframework.jdbc.core` / `PreparedStatementSetter.java` L44-L54 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-jdbc/src/main/java/org/springframework/jdbc/core/PreparedStatementSetter.java#L44-L54))

```java
// PreparedStatementSetter.java L44-L54
public interface PreparedStatementSetter {

    void setValues(PreparedStatement ps) throws SQLException;

}
```

## 흐름에서 불리는 자리

```text
 execute(psc, action)
   L668 psc.createPreparedStatement(con)    문장 생성
   콜백 안에서 pss.setValues(ps)            파라미터 바인딩
   그 뒤 executeQuery / executeUpdate
```

- [JdbcTemplate.execute](../../01_JdbcTemplate.execute/README.md)

## 구현 계층

```text
 PreparedStatementCreator
   +-- SimplePreparedStatementCreator      SQL 문자열 그대로
   +-- PreparedStatementCreatorFactory 가 만드는 구현 (타입 지정, 생성 키 반환)
   +-- (생성 키가 필요하면 RETURN_GENERATED_KEYS 로 만든다)

 PreparedStatementSetter
   +-- ArgumentPreparedStatementSetter        인자 배열 바인딩
   +-- ArgumentTypePreparedStatementSetter    타입까지 지정
   +-- BatchPreparedStatementSetter           배치 (행마다 setValues)

 ParameterDisposer
   LOB 등 정리가 필요한 파라미터를 finally 에서 해제하는 계약
```
