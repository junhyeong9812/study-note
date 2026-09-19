# FetchSpec

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

결과를 어떤 모양으로 꺼낼지 고르는 표면이다. 인터페이스 자체는 비어 있고, 행 조회와 갱신 건수 두 계약을 합친 것뿐이다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core` / `FetchSpec.java` L28-L30 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/FetchSpec.java#L28-L30))

```java
// FetchSpec.java L28-L30
public interface FetchSpec<T> extends RowsFetchSpec<T>, UpdatedRowsFetchSpec {

}
```

## 흐름에서 불리는 자리

```text
 DefaultGenericExecuteSpec.execute 가 DefaultFetchSpec 을 만들어 돌려준다
   one()          결과가 하나여야 한다
   first()        첫 행만
   all()          Flux 로 전부
   rowsUpdated()  갱신 건수
```

- [DefaultGenericExecuteSpec.execute](../../01_DefaultGenericExecuteSpec.execute/README.md)

## 구현 계층

```text
 RowsFetchSpec<T>        one() / first() / all()
 UpdatedRowsFetchSpec    rowsUpdated()
   +-- FetchSpec<T>      둘을 합친 것
         +-- DefaultFetchSpec<T>

 map(...) 을 거치면 RowsFetchSpec 만 남는다
   행 매핑을 지정한 뒤에는 "갱신 건수"가 의미를 잃기 때문이다
```

## 결과가 쓰이는 곳

```text
 one()
      --> 행이 없으면 빈 Mono, 둘 이상이면 오류 신호
      --> "없을 수도 있다"와 "하나여야 한다"를 타입으로 구분하지 않으므로
          빈 결과 처리는 호출자가 switchIfEmpty 등으로 정한다

 all()
      --> inConnectionMany 를 타고, 커넥션은 Flux 가 끝날 때까지 열려 있다
      --> 소비를 멈추면(취소) 그 시점에 커넥션이 반납된다

 rowsUpdated()
      --> INSERT/UPDATE/DELETE 의 영향 행 수
      --> Long 이라 대량 갱신도 담는다
```
