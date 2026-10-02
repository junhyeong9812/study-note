# software-design/48-configuration-and-12factor — 설정·환경 분리·12-factor: 같은 빌드, 다른 설정 — 정리 (힌트)

## 해결하는 문제

같은 코드를 개발·스테이징·운영에 배포한다.
배포마다 다른 것(DB 주소·자격 증명·타임아웃)이 코드나 이미지 안에 박혀 있으면 두 가지가 깨진다.

```text
 설정이 코드·이미지 안에 있을 때
 ─────────────────────────────────────────────
 환경마다 다른 빌드  →  "스테이징에서 통과한 그 산출물"이 운영에 가지 않는다
 비밀이 이미지 안   →  이미지를 받을 수 있는 사람 모두가 비밀을 읽는다 (지운 줄 알아도)
 환경마다 손으로 고침 → 설정이 조금씩 달라져(drift) 스테이징 통과·운영 장애
```

- *설정(config)*: 12-factor의 정의로 **배포마다 달라질 가능성이 있는 모든 것** — 백엔드 서비스 주소(DB·캐시), 외부 서비스 자격 증명, 배포별 값(정식 호스트 이름).
- *12-factor*: Adam Wiggins가 Heroku 플랫폼에서 본 앱들의 경험을 바탕으로 정리한 SaaS 애플리케이션 방법론 12항목(12factor.net 「Background」). 그중 III이 Config다.
- *설정 드리프트(config drift)*: 같아야 할 환경들의 설정이 손 수정·누락으로 조금씩 달라지는 것.

쉬운 예: 같은 레시피(코드)로 여러 지점(환경)에서 요리한다. 지점마다 다른 것은 "가스 화력·납품처 전화번호"다. 이것을 레시피에 적어 두면 지점마다 레시피를 복사해 고쳐야 하고, 복사본들은 서서히 달라진다.\
똑같은 구조다.\
실무 예: `application-prod.yml`을 이미지에 넣어 빌드하면 스테이징 이미지와 운영 이미지가 다른 산출물이 된다. 대신 이미지 하나를 만들고 실행할 때 환경 변수·마운트한 파일로 값을 넣는다.

## 동작·원리

### 1. 빌드 → 릴리스 → 실행 (12-factor V)

```text
 코드 저장소 ──build──> 빌드 산출물 (jar·이미지, 환경 무관)
                            │
               설정 ────────┤ release = 빌드 + 이 배포의 설정, 고유 ID(v100), 한 번 만들면 수정 불가
                            v
                         릴리스 ──run──> 프로세스들 (실행 중 코드 수정 없음)
```

- 12-factor V: 세 단계를 엄격히 나눈다. 릴리스는 **추가 전용 원장**이고 바꾸려면 새 릴리스를 만든다. 그래서 이전 릴리스로 되돌리기가 쉽다.
- 12-factor III: 설정은 코드와 **엄격히 분리**한다. 시험 방법: "지금 당장 코드를 오픈 소스로 공개해도 자격 증명이 새지 않는가."
- 12-factor III의 주의: Spring의 모듈 연결 방식(빈 구성) 같은 **배포마다 안 바뀌는 내부 설정은 이 정의의 설정이 아니다.** 그것은 코드에 둔다.

### 2. 왜 환경 변수인가, 그리고 왜 "환경 이름 묶음"을 피하나

```text
 묶음 방식 (피하라고 함)              개별 변수 방식 (12-factor)
 application-dev.yml                PAYMENT_TIMEOUT_MS=3000
 application-staging.yml            PAYMENT_RETRY_MAX=2
 application-prod.yml               DB_URL=...
 application-joes-staging.yml ←     각 변수는 서로 독립, 배포마다 따로 관리
   배포가 늘면 묶음 이름이 조합 폭발
```

- 12-factor III의 근거: 환경 변수는 코드 변경 없이 배포마다 바꾸기 쉽고, 설정 파일과 달리 저장소에 실수로 커밋될 가능성이 낮고, 언어·OS에 무관한 표준이다.
- 이름 붙인 환경 묶음(development·test·production)은 배포가 늘면 `staging`·`qa`·`joes-staging`이 생기며 조합이 폭발한다고 적는다.
- 이것은 Heroku 경험에서 나온 방법론의 주장이다(사이트 표기 "Last updated 2017"). 쿠버네티스 시크릿 마운트·설정 서버 같은 방식은 III Config 장에 나오지 않는다. 핵심 원칙(빌드와 설정 분리, 비밀은 코드 밖)은 그대로 쓰이고, "꼭 환경 변수여야 하나"는 플랫폼에 따라 다르게 판단한다.

### 3. Spring Boot의 우선순위 — 나중 소스가 이긴다

Spring Boot 레퍼런스 "Externalized Configuration"은 "나중 소스가 앞 소스의 값을 덮어쓴다"고 하고 순서를 적는다(발췌).

```text
 낮음  기본 속성(SpringApplication.setDefaultProperties)
  │    @PropertySource
  │    설정 데이터(application.properties — jar 안 → jar 안 프로필별 → jar 밖 → jar 밖 프로필별)
  │    OS 환경 변수
  │    Java 시스템 속성(-D)
  │    …
  v    명령줄 인자(--)
 높음  (테스트용 @TestPropertySource 등)
```

- 환경 변수 이름 규칙(같은 문서): 점(`.`)은 `_`로, 대시(`-`)는 빼고, 대문자로. 예) `spring.main.log-startup-info` → `SPRING_MAIN_LOGSTARTUPINFO`.

### 실험 A: 같은 jar, 소스를 하나씩 더하기

```java
@Bean
CommandLineRunner show(ConfigurableEnvironment env,
                       @Value("${app.payment.timeout-ms}") int timeoutMs,
                       @Value("${app.payment.api-key}") String apiKey) {   // 기본값 없음 → 없으면 기동 실패
    return a -> {
        // 어느 PropertySource가 이 키를 가졌는지 우선순위 순으로 찾는다(relaxed 이름 포함)
        ...
        System.out.println("timeout-ms=" + timeoutMs + "  ← 이긴 소스: " + winner);
        System.out.println("api-key 길이=" + apiKey.length());
    };
}
// jar 안 application.properties: app.payment.timeout-ms=1000
```

(실험, Spring Boot 4.1.1(spring-core 7.0.9), JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/45/e48/boot/`, 2026-10-02 — 결정적)

```text
== 1) jar 안 application.properties만 + API 키 env
timeout-ms=1000  ← 이긴 소스: Config resource 'class path resource [application.properties]' via location 'optional:classpath:/'
api-key 길이=5
== 2) + OS 환경 변수 APP_PAYMENT_TIMEOUTMS=3000
timeout-ms=3000  ← 이긴 소스: systemEnvironment
api-key 길이=5
== 3) + 시스템 속성 -Dapp.payment.timeout-ms=4000
timeout-ms=4000  ← 이긴 소스: systemProperties
api-key 길이=5
== 4) + 명령줄 인자 --app.payment.timeout-ms=5000
timeout-ms=5000  ← 이긴 소스: commandLineArgs
api-key 길이=5
== 5) 환경 변수 APP_PAYMENT_TIMEOUT_MS=3000 (대시를 _로)
timeout-ms=3000  ← 이긴 소스: systemEnvironment
api-key 길이=5
== 6) 오타 APP_PAYMENT_TIMEOUT=3000
timeout-ms=1000  ← 이긴 소스: Config resource 'class path resource [application.properties]' via location 'optional:classpath:/'
api-key 길이=5
== 7) API 키 없이 기동
Caused by: org.springframework.util.PlaceholderResolutionException: Could not resolve placeholder 'app.payment.api-key' in value "${app.payment.api-key}"
java 종료 코드=1
```

- 관찰 1 — 1 → 4로 갈수록 jar 파일 → 환경 변수 → 시스템 속성 → 명령줄 인자 순으로 덮어썼다. 문서의 순서와 같다.
- 관찰 2 — 문서 규칙대로 대시를 뺀 `APP_PAYMENT_TIMEOUTMS`도, 대시를 `_`로 바꾼 `APP_PAYMENT_TIMEOUT_MS`도 이 버전의 `@Value`에서는 바인딩됐다.
- 관찰 3 — **오타 변수(`APP_PAYMENT_TIMEOUT`)는 조용히 무시되고 jar 안 기본값 1000이 쓰였다.** 에러도 경고도 없다. 운영에서 "3초로 늘렸는데 왜 1초에 끊기지?"가 이렇게 생긴다.
- 관찰 4 — 기본값 없는 필수 값(`api-key`)이 없으면 기동 단계에서 실패했다(종료 코드 1). 요청을 받다가 터지는 것보다 배포 시점에 멈추는 쪽이 싸다(fail-fast).

### 4. 비밀이 이미지에 들어가면 지워도 남는다

```text
 이미지 = 레이어의 쌓임 (각 레이어는 tar)
 ┌─────────────────────────────┐
 │ L3: RUN rm /app/secret.env   │  → ".wh.secret.env" (whiteout 표식만)
 │ L2: COPY secret.env /app/    │  → secret.env 내용이 그대로 있다
 │ L1: FROM nginx:1.27-alpine   │
 └─────────────────────────────┘
 컨테이너에서 보이는 것 = 위에서 내려다본 합성 결과 → 파일이 없어 보인다
 이미지를 받은 사람 = 레이어 tar를 하나씩 풀 수 있다 → L2에서 꺼낸다
```

- *whiteout*: 아래 레이어의 파일을 "지웠다"고 표시하는 빈 파일(`.wh.<이름>`). 아래 레이어 내용은 지우지 않는다.

### 실험 B: 지운 비밀 꺼내기

```dockerfile
FROM nginx:1.27-alpine
COPY secret.env /app/secret.env
RUN grep -c PAYMENT_API_KEY /app/secret.env && rm /app/secret.env
```

(실험, Docker Engine 29.1.3 레거시 빌더(buildx 없음), 가짜 키 `sk_test_FAKE_…`, `scratchpad/sd/45/e48/img/inspect.sh`·`grepsecret.sh`, 2026-10-02 — 레이어 해시는 빌드마다 다르다)

```text
### 컨테이너 안에서 보이나: docker run --rm sn-sd-w45-secret:bad ls -la /app
  total 8
  drwxr-xr-x    1 root     root          4096 Oct  2 02:16 .
  drwxr-xr-x    1 root     root          4096 Oct  2 02:16 ..
### docker history (위 3줄)
  /bin/sh -c grep -c PAYMENT_API_KEY /app/secret.env && rm /app/secret.env | 0B
  /bin/sh -c #(nop) COPY file:a8c102e865fe5853405419a99c9c2b4aa0d931cd33617ca19358598864a44d49 in /app/secret.en
  RUN /bin/sh -c set -x     && apkArch="$(cat /etc/apk/arch)"     && nginxPackages="         nginx=${NGINX_VERSI
### docker save 후 레이어 tar 안에서 secret 찾기
  레이어 blobs/sha256/d5083ef44ae8c02a106269983a35a7b20dd1c41901bb48f04447cae823b0bc44: app/secret.env → PAYMENT_API_KEY=sk_test_FAKE_0123456789
  레이어 blobs/sha256/c481582860407bc58951bed91fca7aea7fab151e1e45713def35c5db7a80d4f7: app/.wh.secret.env → 
  (끝)
```

비교: 비밀을 넣지 않은 이미지(`RUN mkdir -p /app`만)에 실행 시점에 환경 변수로 주입했다.

```text
  sn-sd-w45-secret:bad 레이어 전체에서 'sk_test_FAKE' 발견 줄 수 = 1
  sn-sd-w45-secret:good 레이어 전체에서 'sk_test_FAKE' 발견 줄 수 = 0
### 실행할 때 주입: docker run -e PAYMENT_API_KEY=… (키 길이만 출력)
  PAYMENT_API_KEY 길이=23
### 그러나 실행 중 컨테이너의 env는 docker inspect로 보인다
  PAYMENT_API_KEY=sk_test_FAKE_0123456789
```

- 관찰 1 — 컨테이너 안 `/app`은 비어 있었다. 그러나 `docker save`로 받은 레이어 tar에서 키가 그대로 나왔고, 지운 레이어에는 `.wh.secret.env` 표식만 있었다.
- 관찰 2 — 비밀을 실행 시점에 주입한 이미지에서는 레이어 전체에서 0줄이었다.
- 관찰 3 — 환경 변수도 만능은 아니다. 도커 데몬 권한이 있는 사람은 `docker inspect`로 실행 중 컨테이너의 env를 읽었다. 비밀은 "이미지 밖"에 더해 "누가 실행 환경을 볼 수 있나"까지 관리해야 한다(비밀 관리 도구·마운트 파일·권한).

## 쓰이는 자료구조·알고리즘

- **우선순위 체인(PropertySource 목록)** — 소스를 우선순위 순서로 두고 처음 값을 가진 소스가 이긴다. 체인 오브 리스펀서빌리티의 조회판이다. 실험 A의 "이긴 소스" 찾기가 그 순회다.
- **이름 정규화(relaxed binding)** — `app.payment.timeout-ms` ↔ `APP_PAYMENT_TIMEOUTMS` ↔ `APP_PAYMENT_TIMEOUT_MS`를 같은 키로 보는 매핑. 매핑에 안 걸리는 오타는 다른 키라서 조용히 무시된다(관찰 3).
- **레이어 파일 시스템(유니언 마운트)과 whiteout** — 위 레이어가 아래를 가리는 합성. 삭제는 표식일 뿐 아래 데이터는 남는다. 같은 원리가 LSM 트리의 툼스톤이다.
- **집합 차·조인(드리프트 검사)** — 두 환경의 키 집합 차(`comm -3`)와 같은 키의 값 비교(`join`). 아래 「적용」의 스크립트.

## 적용 — 풀어나가는 법

### 1. 순서

1. **무엇이 설정인지 가른다.** 배포마다 다른 것(주소·자격 증명·용량 값)만 설정이다. 빈 연결·라우팅처럼 안 바뀌는 것은 코드에 둔다(12-factor III).
2. **빌드는 하나.** 같은 jar·이미지를 모든 환경에 올리고, 설정은 실행 시점에 넣는다(12-factor V).
3. **비밀은 이미지·저장소 밖.** 실행 환경이 주입하고(환경 변수·마운트 파일·비밀 관리자), 그 환경을 볼 수 있는 권한도 줄인다.
4. **필수 값은 기본값 없이 + 기동 시 검증.** 없으면 배포가 실패하게 한다(실험 A 관찰 4). 형식·범위도 기동 시 검사한다.
5. **오타를 잡는다.** 알 수 없는 키를 경고하거나, 설정 클래스로 묶어 검증한다.
6. **드리프트를 잰다.** 환경 사이 키 집합과 값 차이를 정기적으로 비교하고, 달라야 정상인 키는 허용 목록으로 뺀다.

### 2. 코드 — 설정을 타입으로 묶고 기동 시 검증 (Java, Spring Boot)

```java
@ConfigurationProperties("app.payment")
@Validated
public record PaymentProperties(
        @NotBlank String apiKey,                 // 없으면 기동 실패
        @NotNull URI baseUrl,
        @Min(100) @Max(30_000) int timeoutMs,    // 단위를 이름에, 범위를 타입 옆에
        @Min(0) @Max(3) int retryMax) {}

@SpringBootApplication
@ConfigurationPropertiesScan
public class App { ... }
```

- `@Validated` 검증은 클래스패스에 Bean Validation 구현(예: `spring-boot-starter-validation`)이 있어야 동작한다. 실험 A는 이 의존성 없이 `@Value`의 placeholder 실패로 fail-fast를 보였다.
- 값의 이유(왜 재시도 2회인가)는 설정 파일이 아니라 ADR에 남기고 주석으로 잇는다([47](../47-architecture-decision-records/2-summary.md)).

### 3. 진단 — 환경 사이 드리프트

```bash
# 두 배포의 설정에서 (1) 한쪽에만 있는 키, (2) 값이 다른 키를 뽑는다. 값이 달라야 정상인 키는 허용 목록으로 뺀다.
A=$1; B=$2; ALLOW='^(DB_URL)$'
keys(){ cut -d= -f1 "$1" | sort; }
comm -3 <(keys $A) <(keys $B)
join -t= <(sort $A) <(sort $B) | awk -F= -v allow="$ALLOW" '$2!=$3 && $1 !~ allow {print "  "$1": "$2" vs "$3}'
```

(실험, 예시 설정 두 벌, `scratchpad/sd/45/e48/drift/drift.sh`, 2026-10-02)

```text
### 한쪽에만 있는 키 (comm -3)
  staging.env에만: FEATURE_NEW_CHECKOUT
### 값이 다른 키 (허용 목록 ^(DB_URL)$ 제외)
  PAYMENT_RETRY_MAX: 2 vs 5
```

- 스테이징에서 시험한 것은 "재시도 2회 + 새 결제 화면"인데 운영은 "재시도 5회 + 옛 화면"이다. 스테이징 통과가 운영을 보증하지 못한다.
- 값에 `=`가 들어가는 키는 이 단순 스크립트로 비교하면 틀린다. 실무에서는 설정 관리 도구의 diff를 쓴다.

## 장애 시나리오와 대처

### 1. 환경별 설정 드리프트 → 스테이징 통과, 운영 장애 (⚠ 커리큘럼)

- 현상: 스테이징에서 부하 시험까지 통과한 릴리스가 운영에서 결제 지연 장애를 낸다.
- 보이는 형태: 같은 이미지 태그인데 동작이 다르다. 설정 diff에 재시도·타임아웃·플래그 차이(위 드리프트 출력).
- 원인: 환경마다 손으로 고친 값이 누적돼 달라졌다. 스테이징은 운영을 대표하지 못했다.
- 대처: 설정을 코드처럼 버전 관리하고(저장소·IaC), 환경 사이 diff를 배포 전 검사에 넣는다. 달라야 하는 키만 허용 목록에 둔다. 12-factor X(dev/prod parity)의 "도구 격차"도 같이 줄인다.

### 2. 시크릿이 이미지에 포함 (⚠ 커리큘럼)

- 현상: 레지스트리 접근 권한이 넓은 이미지에서 결제 키가 유출된다. Dockerfile에서는 "지웠다".
- 보이는 형태: `docker history`에 `COPY secret.env`, 레이어 tar에 원문(실험 B). 비밀 스캐너가 이미지에서 키 패턴을 찾는다.
- 원인: 이미지 레이어는 추가 전용이다. 다음 레이어의 `rm`은 whiteout 표식만 더한다.
- 대처: 유출된 키는 **즉시 폐기·재발급**한다(이미지를 다시 만드는 것으로는 이미 받아 간 사본을 지우지 못한다). 비밀은 실행 시점 주입으로 바꾸고, 빌드에 꼭 필요하면 BuildKit의 비밀 마운트처럼 레이어에 남지 않는 방법을 쓴다. CI에 이미지 비밀 스캔을 넣는다.

### 3. 오타 변수가 조용히 무시된다

- 현상: 타임아웃을 3초로 늘리는 환경 변수를 넣었는데 여전히 1초에 끊긴다.
- 보이는 형태: 에러·경고 없음. 애플리케이션 로그의 실효 설정(또는 `/actuator/env`)에 기본값이 보인다.
- 원인: 바인딩 규칙에 안 맞는 이름은 다른 키다(실험 A 6번: `APP_PAYMENT_TIMEOUT`).
- 대처: 기동 시 실효 설정을 비밀은 가리고 로그로 남긴다. 설정을 타입으로 묶어 검증한다. 배포 매니페스트에 알 수 없는 키 검사를 둔다.

### 4. 필수 설정이 없는데 기본값으로 떠서 운영 데이터를 건드린다

- 현상: 운영 배포에서 `DB_URL`이 빠졌는데 jar 안 기본값(`localhost` 개발 DB)으로 떴다. 또는 반대로 개발 환경이 운영 DB 기본값으로 떴다.
- 보이는 형태: 기동은 정상, 데이터가 엉뚱한 곳에 쌓이거나 연결 오류가 요청 처리 중에 난다.
- 원인: 배포마다 달라야 하는 값에 jar 안 기본값을 줬다.
- 대처: 배포별 값에는 기본값을 두지 않는다. 없으면 기동 실패(실험 A 7번, 종료 코드 1).

### 5. 설정 변경이 릴리스 없이 일어나 되돌릴 수 없다

- 현상: 누군가 운영 서버에서 설정 파일을 직접 고쳤고, 장애 뒤 "무엇이 바뀌었나"를 모른다.
- 보이는 형태: 배포 기록에는 변경이 없는데 동작이 바뀌었다. 서버마다 설정이 다르다.
- 원인: 빌드·릴리스·실행 분리가 깨졌다. 릴리스는 수정할 수 없는 원장이어야 한다(12-factor V).
- 대처: 설정 변경도 새 릴리스(ID)로 만들고 이전 릴리스로 되돌릴 수 있게 한다.

## 핵심 문장

- 12-factor의 설정은 배포마다 달라질 수 있는 모든 것이고, 코드와 엄격히 분리한다. 배포마다 안 바뀌는 내부 연결은 설정이 아니다.
- 빌드 하나를 모든 환경에 올리고 설정은 릴리스 단계에서 붙인다. 릴리스는 수정하지 않고 새로 만든다.
- Spring Boot는 나중 소스가 이긴다. 실험에서 jar 안 1000 → 환경 변수 3000 → 시스템 속성 4000 → 명령줄 5000 순으로 덮어썼고, 오타 변수는 조용히 무시돼 1000이 남았다.
- 이미지 레이어에서 지운 비밀은 남는다. 실험에서 컨테이너 안에는 없었지만 레이어 tar에서 원문이 나왔다. 유출된 키는 폐기·재발급한다.
- 배포별 필수 값에는 기본값을 두지 않고, 없으면 기동 단계에서 실패하게 한다.

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 설정을 읽는 어댑터는 바깥 층에 둔다
- 후속·연결
  - [47-architecture-decision-records](../47-architecture-decision-records/2-summary.md) — 설정 값의 이유를 남기는 곳
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 실행 중 바뀌는 설정(플래그)의 수명
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 릴리스 단위의 배포·되돌리기
  - [reliability/14-graceful-shutdown](../../reliability/14-graceful-shutdown/2-summary.md) — 12-factor IX(빠른 기동·우아한 종료)
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) — 12-factor XI(로그는 이벤트 스트림)
- 글·문서
  - The Twelve-Factor App(Adam Wiggins, 사이트 "Last updated 2017") — 목차, III Config, V Build·release·run, X Dev/prod parity <https://12factor.net/> · <https://12factor.net/config> · <https://12factor.net/build-release-run> · <https://12factor.net/dev-prod-parity>
  - Spring Boot 레퍼런스 "Externalized Configuration" — PropertySource 순서, 설정 데이터 파일 순서, 환경 변수 이름 규칙(2026-10-02 열람, 현재판) <https://docs.spring.io/spring-boot/reference/features/external-config.html>
  - Docker는 이미지 레이어를 추가 전용으로 쌓는다 — 이 노트에서는 문서 대신 실험 B(`docker save` 레이어 tar, whiteout 파일)로 확인했다.
- 실험 목록
  - A Spring Boot 4.1.1 우선순위·relaxed 이름·오타 무시·필수 값 fail-fast — `scratchpad/sd/45/e48/boot/`(pom.xml, `App.java`, Maven 3.9 이미지로 의존성 받음), JDK 21.0.12 temurin `--cpus=2`
  - B 이미지 레이어의 지운 비밀 — `scratchpad/sd/45/e48/img/`(Dockerfile.bad·good, `inspect.sh`, `grepsecret.sh`), Docker 29.1.3, 기반 이미지 `nginx:1.27-alpine`(이미 있던 것), 만든 이미지 `sn-sd-w45-secret:bad|good`는 실험 뒤 삭제
  - C 환경 드리프트 diff — `scratchpad/sd/45/e48/drift/drift.sh`
