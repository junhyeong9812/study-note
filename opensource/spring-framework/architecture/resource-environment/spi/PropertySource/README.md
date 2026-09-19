# PropertySource

상위: [Spring 리소스와 환경](../../README.md) / [spi](../README.md)

키-값 한 벌을 나타낸다. 순서 있는 목록으로 묶여 우선순위를 만든다.

## 실제 코드

`spring-core` / `org.springframework.core.env` / `PropertySource.java` L62-L140 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/PropertySource.java#L62-L140))

```java
// PropertySource.java L62-L140
public abstract class PropertySource<T> {

    protected final Log logger = LogFactory.getLog(getClass());

    protected final String name;

    protected final T source;

    public PropertySource(String name, T source) {
        Assert.hasText(name, "Property source name must contain at least one character");
        Assert.notNull(source, "Property source must not be null");
        this.name = name;
        this.source = source;
    }

    @SuppressWarnings("unchecked")
    public PropertySource(String name) {
        this(name, (T) new Object());
    }

    public String getName() {
        return this.name;
    }

    public T getSource() {
        return this.source;
    }

    public boolean containsProperty(String name) {
        return (getProperty(name) != null);
    }

    public abstract @Nullable Object getProperty(String name);

    @Override
    public boolean equals(@Nullable Object other) {
```

## 흐름에서 불리는 자리

```text
 PropertySourcesPropertyResolver.getProperty
   propertySources 를 앞에서부터 순회
   처음 값을 가진 소스가 이긴다
 @PropertySource 파싱
   PropertySourceRegistry 가 환경의 소스 목록에 추가
```

- [PropertySourcesPropertyResolver.getProperty](../../02_PropertySourcesPropertyResolver.getProperty/README.md)

## 구현 계층

```text
 PropertySource<T>
   +-- EnumerablePropertySource         키 목록을 알 수 있다
   |     +-- MapPropertySource
   |     |     +-- PropertiesPropertySource
   |     |     +-- SystemEnvironmentPropertySource   대소문자/구분자 관대 매칭
   |     +-- ResourcePropertySource                  파일에서 로드
   +-- StubPropertySource                            자리만 잡아 두는 소스
   +-- ComparisonPropertySource

 순서 조작
   MutablePropertySources.addFirst / addLast / addBefore / addAfter
   ApplicationContextInitializer 에서 자주 쓰인다
```
