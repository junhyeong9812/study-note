# spi

상위: [Spring R2DBC](../README.md)

R2DBC 연동이 기대는 계약 인터페이스 모음이다. 클라이언트 표면, 커넥션 범위, 결과 꺼내기, 문장 가로채기, 드라이버별 바인드 표기, 그리고 리액티브 트랜잭션 계약으로 갈라진다.

```text
 클라이언트
   DatabaseClient          SQL 을 쓰고 결과를 꺼내는 표면
   ConnectionAccessor      커넥션 범위 안에서 콜백을 실행하는 계약

 결과
   FetchSpec               one / first / all / rowsUpdated

 확장
   StatementFilterFunction 문장 실행을 가로채는 필터
   BindMarkersFactory      드라이버별 바인드 표기($1, ?, @P0_id)

 트랜잭션
   ReactiveTransactionManager  리액티브 트랜잭션 계약
```

## 하위 인터페이스

- [DatabaseClient](DatabaseClient/README.md) — 클라이언트 표면
- [ConnectionAccessor](ConnectionAccessor/README.md) — 커넥션 범위 계약
- [FetchSpec](FetchSpec/README.md) — 결과 꺼내기
- [StatementFilterFunction](StatementFilterFunction/README.md) — 문장 필터
- [BindMarkersFactory](BindMarkersFactory/README.md) — 바인드 표기
- [ReactiveTransactionManager](ReactiveTransactionManager/README.md) — 리액티브 트랜잭션
