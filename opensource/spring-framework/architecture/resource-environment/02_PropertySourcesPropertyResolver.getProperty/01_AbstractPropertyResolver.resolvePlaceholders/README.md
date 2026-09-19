# AbstractPropertyResolver.resolvePlaceholders

상위: [PropertySourcesPropertyResolver.getProperty](../README.md)

문자열 안의 `${...}`를 값으로 치환한다. 못 찾은 플레이스홀더를 그대로 둘지 예외로 만들지가 호출 경로마다 다르다.

## 실제 코드

`spring-core` / `org.springframework.core.env` / `AbstractPropertyResolver.java` L244-L258 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/AbstractPropertyResolver.java#L244-L258))

```java
// AbstractPropertyResolver.java L244-L258
@Override
public String resolvePlaceholders(String text) {
    if (this.nonStrictHelper == null) {
        this.nonStrictHelper = createPlaceholderHelper(true);
    }
    return doResolvePlaceholders(text, this.nonStrictHelper);
}

@Override
public String resolveRequiredPlaceholders(String text) throws IllegalArgumentException {
    if (this.strictHelper == null) {
        this.strictHelper = createPlaceholderHelper(false);
    }
    return doResolvePlaceholders(text, this.strictHelper);
}
```

`spring-core` / `org.springframework.core.env` / `AbstractPropertyResolver.java` L272-L278 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/AbstractPropertyResolver.java#L272-L278))

```java
// AbstractPropertyResolver.java L272-L278
protected String resolveNestedPlaceholders(String value) {
    if (value.isEmpty()) {
        return value;
    }
    return (this.ignoreUnresolvableNestedPlaceholders ?
            resolvePlaceholders(value) : resolveRequiredPlaceholders(value));
}
```

## 동작 흐름

```text
 세 가지 경로와 각각의 실패 정책

 resolvePlaceholders(text)              L245
   비엄격 헬퍼 사용
   못 찾은 ${x} --> 그대로 남긴다 (예외 없음)

 resolveRequiredPlaceholders(text)      L253
   엄격 헬퍼 사용
   못 찾은 ${x} --> IllegalArgumentException

 resolveNestedPlaceholders(value)       L272
   getProperty 안에서 값에 대해 호출
   ignoreUnresolvableNestedPlaceholders 설정에 따라 위 둘 중 하나로 위임

 치환 규칙 (PropertyPlaceholderHelper)
   ${key}            값이 없으면 위 정책대로
   ${key:기본값}      값이 없으면 기본값 사용
   ${a${b}}          안쪽부터 해석 (중첩 허용)
```

## 결과가 쓰이는 곳

```text
 치환된 문자열
      --> @Value("${db.url}") 주입 값
      --> @PropertySource("classpath:${env}/app.properties") 같은 동적 위치
      --> XML 설정의 ${...}

 정책 차이가 드러나는 자리
      --> 컨테이너의 기본 값 해석기는 environment.resolvePlaceholders (비엄격)
      --> PropertySourcesPlaceholderConfigurer 는 기본이 엄격이라
          찾지 못한 플레이스홀더에서 기동이 실패한다
      --> 그래서 같은 ${...} 가 어디에 쓰였느냐에 따라 결과가 달라진다

 기본값 표기
      --> ${db.port:3306} 은 값이 없을 때만 3306
      --> 빈 문자열로 두려면 ${db.port:}
```
