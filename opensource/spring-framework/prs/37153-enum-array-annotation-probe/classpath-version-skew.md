# 개념: classpath 버전 스큐 — "jar 1개로 빌드하는데 어떻게 어긋나?"

> PR #37153 학습 중 놓쳤던 개념. 질문의 형태: "jar A로 구동 중인데 jar B로 재구동할
> 때 겹칠 일이 있어? 빌드는 jar 1개 기준 아니야?"

## 한 줄 요약

애플리케이션의 런타임 classpath는 jar 1개가 아니라 **수십 개의 합**(내 코드 +
의존 라이브러리들)이고, 버전 스큐는 앱을 두 번 빌드해서 생기는 게 아니라 **한 번의
구동 안에서 서로 다른 두 라이브러리 jar 사이**에 생긴다.

## 구체 예시

라이브러리 두 개와 그 공통 의존성 하나만 있으면 어긋남이 만들어진다. 다음은 한 애플리케이션이
동시에 로드하는 classpath의 모습이다.

```
[한 애플리케이션의 classpath — 동시에 전부 로드]
├── my-app.jar
├── acme-monitoring-1.0.jar   <- 이 안의 클래스들에 @AlertOn({Severity.FATAL})
│                                (2년 전 acme-core 1.0의 Severity 기준으로 컴파일된 바이트코드)
└── acme-core-2.0.jar         <- 내가 최신으로 올린 jar. Severity에서 FATAL이 제거됨
```

- `acme-monitoring-1.0.jar`은 그 라이브러리 저자가 과거에 core 1.0을 보고 컴파일한
  산출물 — 바이트코드에 "Severity의 상수명 FATAL"이 박혀 있다.
- 나는 Gradle에서 core만 2.0으로 올렸다(전이 의존성 충돌 해결, BOM 업그레이드 등
  일상적 사유). monitoring은 새 버전이 없어 1.0 그대로.
- JVM에는 `Severity`가 **core 2.0의 것 하나만** 로드된다. monitoring의 annotation이
  FATAL이라는 이름을 내밀면 조회 실패.

Spring Boot fat jar도 내부에 라이브러리 jar들이 그대로 들어 있으므로 동일하다.

## 이 어긋남을 잡는 검사가 어디에도 없다

빌드부터 실행까지 네 단계 가운데 monitoring과 core를 실제로 대조하는 곳은 마지막 하나뿐이다.

| 단계 | 검사 범위 | monitoring<->core 대조? |
|---|---|---|
| 내 `javac` | **내 소스코드만** — 이미 컴파일된 jar의 바이트코드는 재검사 안 함 | 안 함 |
| Gradle/Maven | jar 좌표·버전 해석만 — jar들 사이 바이너리 호환성은 기본 기능 아님 | 안 함 |
| JVM 클래스 로드 | annotation은 지연 파싱 메타데이터 — 이름표를 해석하지 않음 | 안 함 |
| **속성을 읽는 순간** | 이름 <-> 로드된 enum 상수 목록 첫 대조 | **여기서만** |

즉 컴파일러도, 빌드 도구도, 클래스 로더도 안 잡는 틈이며, "읽는 순간 예외"가
정의된 동작이다. 라이브러리가 메이저 버전에서 상수를 개명·제거하는 것은 허용된
breaking change이므로(semver), 대형 프로젝트에서는 일상적으로 발생하는 환경 조건이다.

## 왜 이게 Spring 버그의 전제인가

이 어긋남 자체는 누구의 버그도 아니다 — 환경이 만드는 **전제 조건**이다. Spring
`AttributeMethods`는 "세상의 classpath는 완벽하지 않다"는 전제로 만들어진 방어
장치이고, PR #37153의 버그는 그 방어가 enum 배열에만 구멍 나 있던 것(대응 누락)이다.
층을 나누면: 1번 층 = 환경의 어긋남(JDK가 지연 예외로 정의), 2번 층 = Spring의
대응(스캔 시 필터링), 버그 = 2번 층의 부분 누락.

## 관련

이 전제 위에서 무슨 일이 벌어지는지는 다음 두 문서가 이어 받는다.

- [enum-annotation-name-resolution.md](enum-annotation-name-resolution.md)
- [probe-pattern.md](probe-pattern.md)
