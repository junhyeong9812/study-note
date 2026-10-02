# software-design/48-configuration-and-12factor — 정답

## 정답

### 1. 설정의 정의

- 배포(개발·스테이징·운영 등)마다 달라질 가능성이 있는 모든 것이다. 백엔드 서비스 주소, 외부 서비스 자격 증명, 배포별 값(정식 호스트 이름)이 여기 든다.
- Spring의 모듈 연결 방식 같은 내부 구성은 배포마다 바뀌지 않으므로 이 정의의 설정이 아니다. 코드에 두는 것이 낫다고 12-factor III은 적는다.
- 시험법: 지금 당장 코드를 오픈 소스로 공개해도 자격 증명이 새지 않는가.

### 2. 빌드 → 릴리스 → 실행

```text
 코드 ──build──> 산출물(환경 무관) ──+ 설정──> 릴리스(고유 ID, 수정 불가) ──run──> 프로세스
```

- 설정은 릴리스 단계에서 붙는다. 빌드 산출물은 모든 환경에서 같다.
- 릴리스는 추가 전용 원장이다. 바꾸려면 새 릴리스를 만든다. 그래야 "무엇이 바뀌었나"가 남고 이전 릴리스로 되돌릴 수 있다.
- 실행 중 코드는 바꾸지 않는다. 바꿔도 빌드 단계로 거슬러 전파할 길이 없다.

### 3. 환경 이름 묶음을 피하는 이유

- 배포가 늘면 `staging`·`qa`, 개인용 `joes-staging` 같은 묶음 이름이 계속 생겨 조합이 폭발한다. 배포 관리가 깨지기 쉬워진다.
- 12-factor는 환경 변수를 서로 독립인 개별 조절 손잡이로 두고, 배포마다 따로 관리하라고 한다.

### 4. 우선순위

(실험 A, Spring Boot 4.1.1, JDK 21.0.12)

```text
timeout-ms=1000  ← 이긴 소스: Config resource 'class path resource [application.properties]' via location 'optional:classpath:/'
timeout-ms=3000  ← 이긴 소스: systemEnvironment
timeout-ms=4000  ← 이긴 소스: systemProperties
timeout-ms=5000  ← 이긴 소스: commandLineArgs
```

- 나중(우선순위 높은) 소스가 이긴다. 순서는 jar 안 파일 < OS 환경 변수 < 시스템 속성 < 명령줄 인자다. 문서의 순서와 같다.

### 5. 오타 환경 변수

```text
== 6) 오타 APP_PAYMENT_TIMEOUT=3000
timeout-ms=1000  ← 이긴 소스: Config resource 'class path resource [application.properties]' via location 'optional:classpath:/'
```

- 바인딩 규칙에 안 맞는 이름이라 다른 키로 취급되어 **조용히 무시**됐다. jar 안 기본값 1000이 쓰였고 에러·경고는 없었다.
- 참고: 문서 규칙대로 대시를 뺀 `APP_PAYMENT_TIMEOUTMS`와 대시를 `_`로 바꾼 `APP_PAYMENT_TIMEOUT_MS`는 둘 다 바인딩됐다(이 버전의 `@Value`).

### 6. 필수 값 누락

```text
Caused by: org.springframework.util.PlaceholderResolutionException: Could not resolve placeholder 'app.payment.api-key' in value "${app.payment.api-key}"
java 종료 코드=1
```

- 기동 단계에서 실패한다(종료 코드 1).
- 기본값을 주면 값이 빠진 배포가 엉뚱한 값(개발용 주소·빈 키)으로 떠서, 요청 처리 중에 실패하거나 엉뚱한 곳에 데이터를 쓴다. 배포 시점에 멈추는 쪽이 원인을 찾기 쉽고 피해도 작다.

### 7. 지운 비밀

(실험 B, Docker 29.1.3)

```text
### 컨테이너 안에서 보이나: docker run --rm sn-sd-w45-secret:bad ls -la /app
  total 8
  drwxr-xr-x    1 root     root          4096 Oct  2 02:16 .
  drwxr-xr-x    1 root     root          4096 Oct  2 02:16 ..
### docker save 후 레이어 tar 안에서 secret 찾기
  레이어 blobs/sha256/d5083ef44ae8c02a106269983a35a7b20dd1c41901bb48f04447cae823b0bc44: app/secret.env → PAYMENT_API_KEY=sk_test_FAKE_0123456789
  레이어 blobs/sha256/c481582860407bc58951bed91fca7aea7fab151e1e45713def35c5db7a80d4f7: app/.wh.secret.env → 
  (끝)
```

- 컨테이너 안: `/app`이 비어 있다. 위 레이어의 whiteout이 아래 파일을 가린다.
- `docker save` 레이어: `COPY` 레이어 tar에 원문이 그대로 있다. `rm` 레이어에는 `.wh.secret.env` 표식만 있다.
- 이유: 이미지 레이어는 추가 전용이다. 삭제는 아래 레이어 내용을 지우지 않고 "지웠다" 표식을 더할 뿐이다.

### 8. 환경 변수로 넣어도 남는 경로

- 이미지 레이어에서는 0줄이었다(`good` 이미지).
- 그러나 도커 데몬 권한이 있는 사람은 `docker inspect`로 실행 중 컨테이너의 env에서 원문을 읽었다.
- 그 밖에 프로세스 환경을 덤프하는 로그·진단 도구도 경로가 될 수 있다. 비밀 관리 도구·권한 축소·마운트 파일 같은 방법을 함께 쓴다.

### 9. 스테이징 통과, 운영 장애

- 비교할 것: 두 환경의 실효 설정. 한쪽에만 있는 키(`comm -3`)와 값이 다른 키(`join`)를 본다.
  - 실험 출력: `staging.env에만: FEATURE_NEW_CHECKOUT`, `PAYMENT_RETRY_MAX: 2 vs 5`.
- 원인: 환경별 손 수정이 쌓인 드리프트다. 스테이징이 운영을 대표하지 못했다.
- 재발 방지
  - 설정을 버전 관리한다.
  - 배포 전 환경 diff 검사를 두고, 달라야 하는 키만 허용 목록에 둔다.
  - 설정 변경도 새 릴리스로 만든다.

### 10. 이미지에 들어간 키

- 충분하지 않다. 이미 받아 간 이미지·캐시·레지스트리의 옛 태그에 키가 남는다.
- 먼저 키를 **즉시 폐기·재발급**한다.
- 그다음 비밀을 실행 시점 주입으로 바꿔 다시 빌드한다. 빌드에 필요하면 레이어에 남지 않는 비밀 마운트(BuildKit)를 쓴다. 옛 태그를 정리하고 CI에 이미지 비밀 스캔을 넣는다.
