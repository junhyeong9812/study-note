# Spring 리소스와 환경

`"classpath:config.xml"` 같은 문자열이 읽을 수 있는 리소스가 되고, `${db.url}` 같은 표기가 실제 값으로 바뀌기까지의 흐름을 위에서 아래로 따라간다. 둘 다 프레임워크 전반이 기대는 기초 추상화이고, 컨테이너 기동의 맨 앞에서 쓰인다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 두 추상화의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] 리소스

 resourceLoader.getResource("classpath:app.yml")
 |
 +-- [01] DefaultResourceLoader.getResource
        등록된 ProtocolResolver 에게 먼저 묻는다 (사용자 정의 접두사)
        "/..."        --> getResourceByPath (구현별: 클래스패스 또는 서블릿 컨텍스트)
        "classpath:"  --> ClassPathResource
        "classpath*:" --> ClassPathAllResource
        그 밖         --> URL 로 파싱 (file:, http:, jar: ...)
                          실패하면 경로로 간주
 |
 +-- 패턴이 필요하면 PathMatchingResourcePatternResolver.getResources("classpath*:**/*.xml")
        모듈 경로 --> 클래스패스 순으로 훑어 여러 리소스를 모은다

 [B] 환경(프로퍼티)

 environment.getProperty("db.url")
 |
 +-- [02] PropertySourcesPropertyResolver.getProperty
        PropertySource 목록을 앞에서부터 순회
        처음 값을 가진 소스가 이긴다 (순서가 곧 우선순위)
        값 안에 ${...} 가 있으면 중첩 해석
        대상 타입으로 변환해 반환
 |
 +-- [02-01] resolvePlaceholders / resolveRequiredPlaceholders
        문자열 안의 ${...} 를 값으로 치환
        strict 모드면 못 찾은 자리에서 예외
```

## 어디에서 쓰이는가

```text
 [컨테이너 기동] prepareRefresh
   getEnvironment().validateRequiredProperties()
 [컨테이너 기동] prepareBeanFactory
   ResourceEditorRegistrar 등록 --> "classpath:x.xml" 문자열이 Resource 로 주입된다
 [컨테이너 기동] finishBeanFactoryInitialization
   ${...} 를 environment 로 해석하는 기본 값 해석기 등록
 @PropertySource 파싱, @Value("${...}"), XML import, 스캔 경로 탐색
```

자세한 것은 [컨테이너 기동](../container-refresh/README.md)에 있다.

## 단계

1. [DefaultResourceLoader.getResource](01_DefaultResourceLoader.getResource/README.md)가 위치 문자열을 `Resource`로 바꾼다.
2. [PropertySourcesPropertyResolver.getProperty](02_PropertySourcesPropertyResolver.getProperty/README.md)가 키를 값으로 바꾼다.

## 결과가 쓰이는 곳

```text
 Resource
      --> 설정 파일 읽기, 클래스패스 스캔, 정적 자원 서빙, 템플릿 로딩
      --> 존재 여부(exists)와 열기(getInputStream)가 분리돼 있어
          "핸들을 만드는 것"과 "실제 접근"이 다르다

 프로퍼티 값
      --> @Value 주입, 조건부 설정(@ConditionalOnProperty 류), 데이터 소스 설정
      --> 소스 순서가 우선순위이므로, 같은 키가 여러 곳에 있으면 앞선 소스가 이긴다

 플레이스홀더 해석
      --> ${db.url:기본값} 형태의 기본값 지원
      --> 해석 실패 시 동작이 호출 경로마다 다르다 (아래 노드 참고)
```

## 다루지 않는 것

프로파일 판정(`@Profile`, `acceptsProfiles`)과 `Environment` 구현별 기본 소스 구성(시스템 프로퍼티, 환경 변수, 서블릿 파라미터)은 요약만 했다. 클래스패스 스캔의 디렉터리 순회 세부(jar 내부 탐색 등)도 범위 밖이다.

## 하위 메서드

- [01 DefaultResourceLoader.getResource](01_DefaultResourceLoader.getResource/README.md)
- [02 PropertySourcesPropertyResolver.getProperty](02_PropertySourcesPropertyResolver.getProperty/README.md)
- [spi](spi/README.md) — 리소스, 로더, 환경, 프로퍼티 소스
