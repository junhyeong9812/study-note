# spi

상위: [Spring JDBC](../README.md)

템플릿이 사용자 코드에 넘기는 콜백들과, 결과 변환 및 예외 변환 전략이다.

```text
 JdbcTemplate.execute
   문장 생성 ........ PreparedStatementCreator
   파라미터 바인딩 .. PreparedStatementSetter
   결과 변환 ........ RowMapper / ResultSetExtractor
   예외 변환 ........ SQLExceptionTranslator
 연산 목록 .......... JdbcOperations (JdbcTemplate 이 구현)
```

## 하위 인터페이스

- [JdbcOperations](JdbcOperations/README.md)
- [RowMapper](RowMapper/README.md)
- [PreparedStatementCreator](PreparedStatementCreator/README.md)
- [SQLExceptionTranslator](SQLExceptionTranslator/README.md)
