# PropertySourcesPropertyResolver.getProperty

상위: [Spring 리소스와 환경](../README.md)

키 하나를 값으로 바꾼다. 등록된 프로퍼티 소스를 순서대로 훑어 처음 값을 가진 소스가 이기고, 값 안의 `${...}`는 그 자리에서 다시 해석된다.

## 실제 코드

`spring-core` / `org.springframework.core.env` / `PropertySourcesPropertyResolver.java` L72-L100 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/env/PropertySourcesPropertyResolver.java#L72-L100))

```java
// PropertySourcesPropertyResolver.java L72-L100

protected <T> @Nullable T getProperty(String key, Class<T> targetValueType, boolean resolveNestedPlaceholders) {
    if (this.propertySources != null) {
        for (PropertySource<?> propertySource : this.propertySources) {
            if (logger.isTraceEnabled()) {
                logger.trace("Searching for key '" + key + "' in PropertySource '" +
                        propertySource.getName() + "'");
            }
            Object value = propertySource.getProperty(key);
            if (value != null) {
                if (resolveNestedPlaceholders) {
                    if (value instanceof String string) {
                        value = resolveNestedPlaceholders(string);
                    }
                    else if ((value instanceof CharSequence cs) && (String.class.equals(targetValueType) ||
                            CharSequence.class.equals(targetValueType))) {
                        value = resolveNestedPlaceholders(cs.toString());
                    }
                }
                logKeyFound(key, propertySource, value);
                return convertValueIfNecessary(value, targetValueType);
            }
        }
    }
    if (logger.isTraceEnabled()) {
        logger.trace("Could not find key '" + key + "' in any property source");
    }
    return null;
}
```

## 동작 흐름

```text
 getProperty(key, targetValueType, resolveNestedPlaceholders)
 |
 +-- L75 propertySources 를 앞에서부터 순회
       |
       | L80 propertySource.getProperty(key)
       |       null 이면 다음 소스로
       |
       | L82 값이 문자열이고 중첩 해석이 켜져 있으면
       |       resolveNestedPlaceholders(값)
       |       --> 값 안의 ${...} 를 다시 해석 (재귀)
       |
       +-- L92 convertValueIfNecessary(값, 대상 타입)
              ConversionService 로 String -> int, Duration, enum 등으로 변환
 |
 +-- 모든 소스에 없으면 null
       getRequiredProperty 라면 IllegalStateException
```

```text
 전형적인 소스 순서 (StandardEnvironment 기준, 앞이 우선)

 systemProperties          -D 옵션
 systemEnvironment         환경 변수
 (@PropertySource 로 추가한 소스들)
 (애플리케이션이 직접 추가한 소스들)

 Spring Boot 는 여기에 명령행 인자, application.yml, 프로파일별 설정 등을
 정해진 순서로 더 끼워 넣는다
```

1. 문자열 안의 플레이스홀더를 치환하는 경로는 [resolvePlaceholders](01_AbstractPropertyResolver.resolvePlaceholders/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 반환 값
      --> @Value 주입, 설정 클래스의 조건 판정, 데이터 소스 설정 등
      --> 타입 변환 실패는 ConversionFailedException

 소스 순서
      --> 같은 키가 여러 소스에 있으면 앞선 소스가 이긴다
      --> "왜 내 설정이 무시되지" 의 답은 대부분 이 순서에 있다
      --> ConfigurableEnvironment.getPropertySources() 로 순서를 조작할 수 있다

 중첩 해석
      --> db.url=jdbc:mysql://${db.host}:3306/app 같은 값이 동작하는 이유
      --> 순환 참조는 예외로 드러난다
```
