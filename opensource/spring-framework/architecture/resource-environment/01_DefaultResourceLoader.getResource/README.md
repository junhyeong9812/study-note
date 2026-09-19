# DefaultResourceLoader.getResource

상위: [Spring 리소스와 환경](../README.md)

위치 문자열 하나를 `Resource` 핸들로 바꾼다. 접두사에 따라 구현이 갈리고, 사용자 정의 접두사는 `ProtocolResolver`로 끼워 넣을 수 있다.

## 실제 코드

`spring-core` / `org.springframework.core.io` / `DefaultResourceLoader.java` L153-L185 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/DefaultResourceLoader.java#L153-L185))

```java
// DefaultResourceLoader.java L153-L185

@Override
public Resource getResource(String location) {
    Assert.notNull(location, "Location must not be null");

    for (ProtocolResolver protocolResolver : getProtocolResolvers()) {
        Resource resource = protocolResolver.resolve(location, this);
        if (resource != null) {
            return resource;
        }
    }

    if (location.startsWith("/")) {
        return getResourceByPath(location);
    }
    else if (location.startsWith(CLASSPATH_URL_PREFIX)) {
        return new ClassPathResource(location.substring(CLASSPATH_URL_PREFIX.length()), getClassLoader());
    }
    else if (location.startsWith(CLASSPATH_ALL_URL_PREFIX)) {
        return new ClassPathAllResource(location.substring(CLASSPATH_ALL_URL_PREFIX.length()), getClassLoader());
    }
    else {
        try {
            // Try to parse the location as a URL...
            URL url = ResourceUtils.toURL(location);
            return (ResourceUtils.isFileURL(url) ? new FileUrlResource(url) : new UrlResource(url));
        }
        catch (MalformedURLException ex) {
            // No URL -> resolve as resource path.
            return getResourceByPath(location);
        }
    }
}
```

패턴을 다루는 상위 구현은 이 결과를 감싼다.

`spring-core` / `org.springframework.core.io.support` / `PathMatchingResourcePatternResolver.java` L355-L362 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/support/PathMatchingResourcePatternResolver.java#L355-L362))

```java
// PathMatchingResourcePatternResolver.java L355-L362
@Override
public Resource getResource(String location) {
    Resource resource = getResourceLoader().getResource(location);
    if (this.useCaches != null && resource instanceof UrlResource urlResource) {
        urlResource.setUseCaches(this.useCaches);
    }
    return resource;
}
```

`spring-core` / `org.springframework.core.io.support` / `PathMatchingResourcePatternResolver.java` L364-L397 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/support/PathMatchingResourcePatternResolver.java#L364-L397))

```java
// PathMatchingResourcePatternResolver.java L364-L397
@Override
public Resource[] getResources(String locationPattern) throws IOException {
    Assert.notNull(locationPattern, "Location pattern must not be null");
    if (locationPattern.startsWith(CLASSPATH_ALL_URL_PREFIX)) {
        // a class path resource (multiple resources for same name possible)
        String locationPatternWithoutPrefix = locationPattern.substring(CLASSPATH_ALL_URL_PREFIX.length());
        // Search the module path first.
        Set<Resource> resources = findAllModulePathResources(locationPatternWithoutPrefix);
        // Search the class path next.
        if (getPathMatcher().isPattern(locationPatternWithoutPrefix)) {
            // a class path resource pattern
            Collections.addAll(resources, findPathMatchingResources(locationPattern));
        }
        else {
            // all class path resources with the given name
            Collections.addAll(resources, findAllClassPathResources(locationPatternWithoutPrefix));
        }
        return resources.toArray(EMPTY_RESOURCE_ARRAY);
    }
    else {
        // Generally only look for a pattern after a prefix here,
        // and on Tomcat only after the "*/" separator for its "war:" protocol.
        int prefixEnd = (locationPattern.startsWith("war:") ? locationPattern.indexOf("*/") + 1 :
                locationPattern.indexOf(':') + 1);
        if (getPathMatcher().isPattern(locationPattern.substring(prefixEnd))) {
            // a file pattern
            return findPathMatchingResources(locationPattern);
        }
        else {
            // a single resource with the given name
            return new Resource[] {getResource(locationPattern)};
        }
    }
}
```

## 동작 흐름

```text
 getResource(location)
 |
 | L158 등록된 ProtocolResolver 를 먼저 묻는다
 |        사용자가 "s3:" 같은 접두사를 지원하게 만드는 확장점
 |
 +-- L165 "/" 로 시작 --> getResourceByPath(location)
 |      기본 구현은 ClassPathContextResource
 |      웹 컨텍스트에서는 ServletContextResource 로 바뀐다 (같은 문자열, 다른 의미)
 |
 +-- L168 "classpath:"  --> ClassPathResource (첫 번째 것 하나)
 +-- L171 "classpath*:" --> ClassPathAllResource (같은 이름 전부)
 |
 +-- L175 그 밖 --> URL 파싱 시도
        file: / http: / jar: 등 --> UrlResource (파일이면 FileUrlResource)
        MalformedURLException  --> 경로로 간주해 getResourceByPath

 getResources(locationPattern)     (패턴 해석기)
 |
 +-- "classpath*:" 로 시작
 |      모듈 경로 탐색 --> 클래스패스 탐색
 |      패턴이면 findPathMatchingResources, 아니면 같은 이름 전부
 +-- 그 밖 --> 접두사 뒤에서 패턴을 찾아 디렉터리를 훑는다
```

## 결과가 쓰이는 곳

```text
 Resource 핸들
      --> 아직 아무것도 읽지 않았다. exists() 나 getInputStream() 이 실제 접근이다
      --> 존재하지 않는 위치도 핸들은 만들어진다

 classpath: 와 classpath*: 의 차이
      --> 전자는 첫 번째 하나, 후자는 모든 jar/디렉터리에서 같은 이름 전부
      --> 라이브러리마다 같은 이름의 설정을 두는 구조에서 후자를 쓴다

 ProtocolResolver
      --> 사용자 정의 접두사를 가장 먼저 처리한다
      --> 표준 접두사보다 우선하므로 기존 동작을 덮어쓸 수도 있다
```
