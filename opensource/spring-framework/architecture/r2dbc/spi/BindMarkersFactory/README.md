# BindMarkersFactory

상위: [Spring R2DBC](../../README.md) / [spi](../README.md)

드라이버마다 다른 바인드 표기를 만들어 준다. `:name` 표기를 쓸 수 있는 이유가 이 인터페이스다.

## 실제 코드

`spring-r2dbc` / `org.springframework.r2dbc.core.binding` / `BindMarkersFactory.java` L39-L144 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-r2dbc/src/main/java/org/springframework/r2dbc/core/binding/BindMarkersFactory.java#L39-L144))

```java
// BindMarkersFactory.java L39-L144
public interface BindMarkersFactory {

    BindMarkers create();

    default boolean identifiablePlaceholders() {
        return true;
    }

    // Static factory methods

    static BindMarkersFactory indexed(String prefix, int beginWith) {
        Assert.notNull(prefix, "Prefix must not be null");
        return () -> new IndexedBindMarkers(prefix, beginWith);
    }

    static BindMarkersFactory anonymous(String placeholder) {
        Assert.hasText(placeholder, "Placeholder must not be empty");
        return new BindMarkersFactory() {
            @Override
            public BindMarkers create() {
                return new AnonymousBindMarkers(placeholder);
            }
            @Override
            public boolean identifiablePlaceholders() {
                return false;
            }
        };
    }

    static BindMarkersFactory named(String prefix, String namePrefix, int maxLength) {
        return named(prefix, namePrefix, maxLength, Function.identity());
    }

    static BindMarkersFactory named(String prefix, String namePrefix, int maxLength,
            Function<String, String> hintFilterFunction) {

        Assert.notNull(prefix, "Prefix must not be null");
        Assert.notNull(namePrefix, "Index prefix must not be null");
        Assert.notNull(hintFilterFunction, "Hint filter function must not be null");
        return () -> new NamedBindMarkers(prefix, namePrefix, maxLength, hintFilterFunction);
    }

}
```

## 흐름에서 불리는 자리

```text
 getResultFunction --> namedParameterExpander.expand(sql, bindMarkersFactory, 값들)
   :id, :name 을 드라이버 표기로 펼친다
     PostgreSQL / H2   $1, $2        indexed("$", 1)
     SQL Server        @P0_id        named("@", "P", 32)  이름이 힌트로 붙는다
     Oracle            :P0_id        named(":", "P", 32)
     MySQL / MariaDB   ?             anonymous("?")
```

- [DefaultGenericExecuteSpec.execute](../../01_DefaultGenericExecuteSpec.execute/README.md)

## 구현 계층

```text
 BindMarkersFactory
   +-- indexed(prefix, beginWith)   $1, $2 처럼 번호가 붙는 표기
   +-- named(prefix, namePrefix...) @P0 처럼 이름이 붙는 표기
   +-- anonymous(placeholder)       ? 처럼 구분되지 않는 표기
   (정적 팩토리가 각각 내부 구현을 돌려준다)

 BindMarkersFactoryResolver
   ConnectionFactory 를 보고 알맞은 팩토리를 고른다
   드라이버별 구현이 서비스로 등록돼 있다
```

## 결과가 쓰이는 곳

```text
 identifiablePlaceholders()
      --> false 면 자리표시자만으로 구분할 수 없다는 뜻 (익명 ? 표기)
      --> 같은 이름이 SQL 안에 두 자리면 스프링이 값을 두 번 바인딩한다

 클라이언트 빌더에서 지정하지 않으면
      --> BindMarkersFactoryResolver 가 ConnectionFactory 로 추론한다
      --> 지원 목록에 없는 드라이버면 예외가 난다

 :name 표기를 끄면 (namedParameters(false))
      --> SQL 을 드라이버 표기 그대로 써야 한다
      --> 펼치기 단계가 통째로 생략된다
```
