# PersistenceExceptionTranslator

상위: [Spring JPA 연동](../../README.md) / [spi](../README.md)

데이터 접근 기술의 예외를 스프링의 `DataAccessException`으로 옮기는 계약이다. 모르는 예외에는 `null`을 돌려주는 규약이 핵심이다.

## 실제 코드

`spring-tx` / `org.springframework.dao.support` / `PersistenceExceptionTranslator.java` L36-L58 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/dao/support/PersistenceExceptionTranslator.java#L36-L58))

```java
// PersistenceExceptionTranslator.java L36-L58
public interface PersistenceExceptionTranslator {

    @Nullable DataAccessException translateExceptionIfPossible(RuntimeException ex);

}
```

## 흐름에서 불리는 자리

```text
 JpaTransactionManager.doCommit  L556, L565 (doRollback 도 L583 에서 같은 일을 한다)
   커밋/flush 실패를 방언(PersistenceExceptionTranslator 이기도 하다)에게 번역시킨다
 PersistenceExceptionTranslationPostProcessor
   @Repository 빈에 프록시를 붙여 메서드 밖으로 나가는 예외를 번역한다
```

- [JpaTransactionManager.doCommit](../../04_JpaTransactionManager.doCommit/README.md)
- [EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible](../../05_EntityManagerFactoryUtils.convertJpaAccessExceptionIfPossible/README.md)

## 구현 계층

```text
 PersistenceExceptionTranslator
   +-- JpaDialect (인터페이스가 이것을 확장한다)
   |     +-- DefaultJpaDialect --> EntityManagerFactoryUtils 의 변환표를 쓴다
   |           +-- HibernateJpaDialect / EclipseLinkJpaDialect
   +-- HibernateExceptionTranslator      네이티브 하이버네이트 경로
   +-- AbstractEntityManagerFactoryBean  팩토리 빈 자신도 번역기다
   +-- (JDBC 쪽 대응물은 SQLExceptionTranslator 로 따로 있다)
```

## 결과가 쓰이는 곳

```text
 번역 결과
      --> null 이면 "내 소관이 아니다". 원래 예외가 그대로 올라간다
      --> 값이면 그 DataAccessException 이 대신 던져진다

 @Repository 프록시
      --> PersistenceExceptionTranslationPostProcessor 가 붙인다
      --> 리포지터리 구현이 벤더 예외를 던져도 호출 코드는 스프링 예외만 본다

 기술이 달라도 같은 예외
      --> JPA 의 EntityExistsException 과 JDBC 의 제약 위반이
          모두 DataIntegrityViolationException 으로 모인다
      --> 데이터 접근 기술을 바꿔도 예외 처리 코드를 유지할 수 있다는 것이 설계 의도다
```
