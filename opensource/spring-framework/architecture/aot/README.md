# Spring AOT 처리

**이 흐름만 런타임 호출 경로가 아니다.** 다른 스물세 흐름이 "요청이 들어오면 무슨 일이 일어나는가"를 따라간다면, 여기서는 빌드 시점에 스프링이 애플리케이션을 미리 분석해 **자바 소스 코드를 생성하는** 파이프라인을 따라간다. 생성된 코드는 런타임에 리플렉션과 설정 파싱을 대신해, 네이티브 이미지와 빠른 기동을 가능하게 한다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 확장점 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [빌드 시점] 메이븐/그레이들 플러그인이 AOT 처리기를 실행한다
 |
 +-- [01] ContextAotProcessor.performAotProcessing
 |        출력 디렉터리를 준비하고 GenerationContext 를 만든다
 |        생성이 끝나면 파일로 쓴다
 |          생성 소스 / 리소스 / 생성 클래스
 |          reachability-metadata.json (네이티브 힌트)
 |          native-image.properties
 |
 +-- [01-01] ApplicationContextAotGenerator.processAheadOfTime
 |        CGLIB 클래스 핸들러를 걸어 두고
 |        컨텍스트를 AOT 용으로 한 번 "돌린다"
 |        기여자들을 모아 코드 생성기에 적용한다
 |
 +-- [02] GenericApplicationContext.refreshForAotProcessing
 |        refresh 의 앞부분만 실행한다
 |          prepareRefresh --> obtainFreshBeanFactory --> prepareBeanFactory
 |          --> postProcessBeanFactory --> invokeBeanFactoryPostProcessors
 |        그다음 빈 정의를 얼리고(freezeConfiguration) 타입을 미리 확정한다
 |        = 싱글톤을 만들지는 않는다. 정의까지만 확정한다
 |
 +-- [03] BeanFactoryInitializationAotContributions.applyTo
          모아 둔 기여자마다 applyTo 를 불러 코드와 힌트를 보탠다
 |
 +-- [03-01] BeanRegistrationsAotProcessor.processAheadOfTime
          빈 정의 하나하나를 "그 빈을 등록하는 자바 코드"로 바꿀 준비를 한다

 [런타임] 생성된 초기화기가 설정 파싱을 대신한다
 |
 +-- AotApplicationContextInitializer.forInitializerClasses(...)
          생성된 ApplicationContextInitializer 를 찾아 적용한다
          @Configuration 파싱도, 스캔도 다시 하지 않는다
```

```text
 무엇이 코드가 되는가

 @Configuration 파싱 결과   --> 빈 정의를 직접 등록하는 자바 코드
 @Autowired 주입 지점        --> 생성자/필드를 직접 호출하는 코드
 프록시가 필요한 빈          --> 미리 생성한 CGLIB 클래스 파일
 리플렉션이 필요한 자리      --> reachability-metadata.json 힌트

 런타임에 사라지는 것
   설정 클래스 파싱, 컴포넌트 스캔, 애노테이션 읽기, 프록시 생성
 런타임에 남는 것
   빈 인스턴스 생성, 의존성 연결, 생애주기 콜백
```

## 어디에서 쓰이는가

```text
 [컨테이너 기동] refresh 의 앞부분을 빌드 시점에 미리 돌린다
   그래서 기동 흐름의 04단계(invokeBeanFactoryPostProcessors)까지가 대상이다
 [빈 생성] 생성된 코드가 빈 정의와 주입 코드를 대신한다
 [AOP 프록시] 프록시 클래스를 빌드 시점에 만들어 파일로 남긴다
```

같은 단계를 런타임에 수행하는 흐름은 [컨테이너 기동](../container-refresh/README.md)이다. 두 흐름을 나란히 보면 무엇이 빌드 시점으로 옮겨졌는지가 드러난다.

## 단계

1. [ContextAotProcessor.performAotProcessing](01_ContextAotProcessor.performAotProcessing/README.md)이 전체를 조율한다.
2. [ApplicationContextAotGenerator.processAheadOfTime](01_ContextAotProcessor.performAotProcessing/01_ApplicationContextAotGenerator.processAheadOfTime/README.md)이 생성을 지휘한다.
3. [GenericApplicationContext.refreshForAotProcessing](02_GenericApplicationContext.refreshForAotProcessing/README.md)이 빈 정의를 확정한다.
4. [BeanFactoryInitializationAotContributions.applyTo](03_BeanFactoryInitializationAotContributions.applyTo/README.md)가 기여자들을 적용한다.
5. [BeanRegistrationsAotProcessor.processAheadOfTime](03_BeanFactoryInitializationAotContributions.applyTo/01_BeanRegistrationsAotProcessor.processAheadOfTime/README.md)이 빈 등록 코드를 준비한다.

## 결과가 쓰이는 곳

```text
 생성된 ApplicationContextInitializer
      --> 런타임에 AotApplicationContextInitializer 가 찾아 적용한다
      --> 설정 클래스 파싱과 스캔이 통째로 생략된다

 생성된 빈 등록 메서드
      --> 빈 정의를 코드로 직접 만든다. 애노테이션을 읽지 않는다
      --> 보이는 생성자는 직접 호출문이 된다
      --> 필드와 세터 주입은 여전히 리플렉션이다. 주입 지점을 찾는 일만 없어진다

 RuntimeHints
      --> reachability-metadata.json 한 파일로 쓰인다
      --> GraalVM 네이티브 이미지가 이 힌트만큼만 리플렉션을 허용한다

 빌드 시점에 정해진다는 제약
      --> 프로파일이나 조건부 설정이 빌드 시점 값으로 고정된다
      --> 런타임에 빈 정의를 바꾸는 코드는 동작하지 않는다
```

## 다루지 않는 것

생성되는 코드의 형태(`BeanDefinitionMethodGenerator`, `InstanceSupplierCodeGenerator`가 만드는 자바 소스), `RuntimeHints`의 종류별 세부(리플렉션, 리소스, 직렬화, 프록시), 테스트 AOT(`spring-test`의 `TestContextAotGenerator`), GraalVM 네이티브 이미지 빌드 자체는 범위 밖이다. 빌드 플러그인이 이 처리기를 어떻게 실행하는지도 스프링 저장소 밖이다.

## 하위 메서드

- [01 ContextAotProcessor.performAotProcessing](01_ContextAotProcessor.performAotProcessing/README.md)
- [02 GenericApplicationContext.refreshForAotProcessing](02_GenericApplicationContext.refreshForAotProcessing/README.md)
- [03 BeanFactoryInitializationAotContributions.applyTo](03_BeanFactoryInitializationAotContributions.applyTo/README.md)
- [spi](spi/README.md) — 기여자, 기여, 힌트 등록기, 런타임 초기화기
