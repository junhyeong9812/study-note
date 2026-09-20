# AbstractSecurityWebApplicationInitializer.onStartup

상위: [필터 등록](../README.md)

서블릿 컨테이너에 `DelegatingFilterProxy` 를 꽂는다. 스프링 부트를 쓰지 않을 때의 등록 경로다.

## 위치

`web` / `org.springframework.security.web.context` / `AbstractSecurityWebApplicationInitializer.java` L105-L118 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/AbstractSecurityWebApplicationInitializer.java#L105-L118))

## 실제 코드

```java
// AbstractSecurityWebApplicationInitializer.java L105-L118
public final void onStartup(ServletContext servletContext) {
    beforeSpringSecurityFilterChain(servletContext);
    if (this.configurationClasses != null) {
        AnnotationConfigWebApplicationContext rootAppContext = new AnnotationConfigWebApplicationContext();
        rootAppContext.register(this.configurationClasses);
        servletContext.addListener(new ContextLoaderListener(rootAppContext));
    }
    if (enableHttpSessionEventPublisher()) {
        servletContext.addListener("org.springframework.security.web.session.HttpSessionEventPublisher");
    }
    servletContext.setSessionTrackingModes(getSessionTrackingModes());
    insertSpringSecurityFilterChain(servletContext);
    afterSpringSecurityFilterChain(servletContext);
}
```

실제로 필터를 만들어 넣는 부분은 바로 아래에 있다.

`web` / `org.springframework.security.web.context` / `AbstractSecurityWebApplicationInitializer.java` L134-L142 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/AbstractSecurityWebApplicationInitializer.java#L134-L142))

```java
// AbstractSecurityWebApplicationInitializer.java L134-L142
private void insertSpringSecurityFilterChain(ServletContext servletContext) {
    String filterName = DEFAULT_FILTER_NAME;
    DelegatingFilterProxy springSecurityFilterChain = new DelegatingFilterProxy(filterName);
    String contextAttribute = getWebApplicationContextAttribute();
    if (contextAttribute != null) {
        springSecurityFilterChain.setContextAttribute(contextAttribute);
    }
    registerFilter(servletContext, true, filterName, springSecurityFilterChain);
}
```

## 동작 흐름

```text
 onStartup(servletContext)
 |
 | L106 beforeSpringSecurityFilterChain(servletContext)   하위 클래스 훅
 |
 +-- L107 설정 클래스를 줬으면
 |      L108 AnnotationConfigWebApplicationContext 를 만들고
 |      L109 그 클래스들을 등록한 뒤
 |      L110 ContextLoaderListener 로 붙인다
 |
 +-- L112 enableHttpSessionEventPublisher() 이면
 |      L113 HttpSessionEventPublisher 리스너를 추가한다
 |      기본은 false (L126-128)
 |
 | L115 세션 추적 방식을 설정한다
 | L116 insertSpringSecurityFilterChain(servletContext)
 |      |
 |      +-- L135 filterName = "springSecurityFilterChain"
 |      +-- L136 new DelegatingFilterProxy(filterName)
 |      +-- L138 컨텍스트 속성을 줬으면 설정
 |      +-- L141 registerFilter(servletContext, true, filterName, 프록시)
             true 는 insertBeforeOtherFilters 다
 |
 +-- L117 afterSpringSecurityFilterChain(servletContext)   하위 클래스 훅
```

```text
 프록시는 이름만 안다

 DelegatingFilterProxy("springSecurityFilterChain")

 컨테이너가 이 필터를 만들 때 스프링 컨텍스트는 아직 없을 수도 있다
 레퍼런스가 그 이유를 밝힌다 -- 컨테이너는 기동 전에 필터를 등록해야 하는데
 스프링 컨텍스트는 ContextLoaderListener 가 나중에 띄우기 때문이다

 그래서 빈 자체가 아니라 이름을 들고 있다가 나중에 찾아 위임한다
 (조회 결과를 캐시하는지는 Spring Framework 쪽 구현이다)

 이 간접층 덕분에 서블릿 필터의 생명주기와
 스프링 빈의 생명주기가 분리된다
```

```text
 onStartup 이 final 이다

 L105 public final void onStartup(...)

 하위 클래스는 이 순서를 바꿀 수 없고,
 before / after 훅으로만 끼어든다

 클래스 javadoc 이 "다른 필터보다 앞에 등록한다"고 밝히고 있어
 순서 보장이 목적으로 보인다 (final 인 이유 자체는 소스에 없다)
```

## 결과가 쓰이는 곳

```text
 등록된 DelegatingFilterProxy
      --> 컨테이너가 아는 Spring Security 필터는 보통 이것 하나다
      --> 모든 요청이 이것을 거쳐 FilterChainProxy 로 간다
      --> 다만 같은 onStartup 이 HttpSessionEventPublisher 리스너도 등록할 수 있고
          (L112-113), insertFilters 훅으로 다른 필터를 더할 수도 있다

 registerFilter 의 true 인자
      --> 이름은 insertBeforeOtherFilters 다 (L193)
      --> L200 에서 !insertBeforeOtherFilters 로 뒤집혀 isMatchAfter 가 되므로
          이미 등록된 다른 필터들보다 앞에 매핑된다
      --> 비동기 지원은 별개다. L198 이 isAsyncSecuritySupported() 를 쓰고
          그 기본값이 true 다 (L293-295)
      --> ASYNC 디스패치 적용은 L199 getSecurityDispatcherTypes() 가 정한다

 스프링 부트를 쓰는 경우
      --> 부트가 자동으로 같은 일을 해 준다
      --> 이 클래스를 상속할 일이 없다
```
