# spi

상위: [Spring JPA 연동](../README.md)

JPA 연동이 벤더 차이를 흡수하려고 둔 인터페이스 모음이다. "무엇을 매핑할지", "누가 구현할지", "벤더에게 어떻게 트랜잭션을 걸지"가 각각 다른 인터페이스로 갈라져 있다.

```text
 구성
   PersistenceUnitManager      무엇을 매핑할 것인가 (영속성 유닛 정보)
   JpaVendorAdapter            누가 구현할 것인가 (프로바이더, 기본 프로퍼티)

 실행
   JpaDialect                  벤더별 트랜잭션 시작, JDBC 커넥션 노출
   EntityManagerFactoryInfo    만들어진 팩토리가 스스로를 설명한다

 예외
   PersistenceExceptionTranslator  벤더 예외 --> DataAccessException
```

## 하위 인터페이스

- [PersistenceUnitManager](PersistenceUnitManager/README.md) — 영속성 유닛 정보 공급
- [JpaVendorAdapter](JpaVendorAdapter/README.md) — 벤더별 기본값 묶음
- [JpaDialect](JpaDialect/README.md) — 트랜잭션과 커넥션의 벤더 차이
- [EntityManagerFactoryInfo](EntityManagerFactoryInfo/README.md) — 팩토리 프록시의 자기 설명
- [PersistenceExceptionTranslator](PersistenceExceptionTranslator/README.md) — 예외 번역 계약
