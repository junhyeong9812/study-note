# language/24-aot-native-image-and-startup — 정답

## 정답

### 1. 두 방향

| | JVM 유지 + 결과 캐시 | 네이티브 이미지 |
|---|---|---|
| 미리 하는 것 | 클래스 파싱·로드·링크(CDS·AOT 캐시), JIT 프로파일(JEP 515) | 도달 가능한 코드 전체의 AOT 컴파일, 빌드 때 초기화한 힙 |
| 포기하는 것 | 거의 없음. 훈련 실행 한 번, 조건(같은 JDK·클래스패스)을 지켜야 함 | 동적 기능(메타데이터로 알려 준 것만), 빌드 시간·메모리, 실행 중 프로파일 최적화 |

### 2. 도달성 분석

```text
  Main.main ─▶ OrderController.handle ─▶ OrderService.place ─┬▶ forName("JsonCodec")             → 상수 → 포함
                                                             └▶ forName(config.get("gateway"))   → 이름 모름 → 미포함
  LegacyReport.render ─▶ PdfWriter                              → 닿지 않음 → 빠짐(죽은 코드 제거)
```

- 상수 인자: 빌드 때 값이 계산되어 이미지 힙에 저장된다. 그 클래스가 없으면 호출이 `throw ClassNotFoundException("Foo")`로 바뀐다(GraalVM Reachability Metadata).
- 실행 시 정해지는 이름: 메타데이터로 등록해야 들어간다. 실험 2 모형에서 등록 전 이미지는 `[Main.main, OrderController.handle, OrderService.place, JsonCodec]`, 등록 후에는 `PgPaymentGateway`·`PgHttpClient`가 더해졌다.

### 3. 닫힌 세계

- GraalVM Basics: 도달 가능한 요소만 이미지에 들어가고, 빌드 뒤에는 클래스 로딩 등으로 새 요소를 추가할 수 없다.
- Spring Boot 문서의 차이
  - 빌드 때 main 진입점부터 정적 분석을 하고, 닿지 않는 코드는 빠진다.
  - 리플렉션·리소스·직렬화·동적 프록시를 GraalVM에 알려 줘야 한다.
  - 클래스패스가 빌드 때 고정된다. 지연 클래스 로딩이 없어 실행 파일에 든 것은 시작할 때 메모리에 올라간다.

### 4. CDS 세 가지 (JDK 21)

- 실험 1(20회): 시작~종료가 off 179~265ms > 기본 89~160ms ≥ AppCDS 84~146ms(사실 점검 재실행 20회: 211~246 / 91~141 / 97~126ms).
- 아카이브에서 온 클래스: off 0/735, 기본 698/702, AppCDS 630/632.
- 기본 대비 AppCDS의 이득은 이 작은 프로그램에서 작고 흔들린다.
- 디렉터리 클래스패스: `[error][cds] Error: non-empty directory 'out'` → `Cannot have non-empty directory in paths`로 아카이브 생성이 실패했다. 클래스패스에 비어 있지 않은 디렉터리가 있으면 안 되므로 JAR로 묶는다(`java` 도구 문서 "Restrictions on Class Path and Module Path"; JEP 483의 AOT 캐시도 "클래스패스에는 JAR만").

### 5. 빌드 때 초기화

- 이미지 힙에 저장된다. 시작할 때 바이너리에서 그대로 복사하므로 그 클래스의 static 초기화를 다시 하지 않는다 → 빠르다.
- 같은 이유로 빌드한 기계의 값이 굳는다. GraalVM Basics의 예: `static final String message = System.getProperty("message")`가 빌드 때 실행되면 실행 때 준 속성은 반영되지 않는다.
- 스냅숏 복원도 초기화가 끝난 메모리를 복사해 시작한다. 그래서 고유해야 할 값(난수 시드·ID·비밀값)이 여러 인스턴스에 복제되는 문제가 같다.

### 6. AOT 캐시의 조건

- JEP 483: 같은 JDK 릴리스, 같은 하드웨어 아키텍처·OS, 일관된 클래스패스(운영은 뒤에 덧붙이기만), 클래스패스는 JAR만, 일관된 모듈 옵션. 사용자 정의 클래스 로더가 읽은 클래스는 캐시하지 않는다. GC와 main 클래스는 달라도 된다.
- 맞지 않으면: 경고를 내고 캐시 없이 계속 실행한다. 조용히 느려진다.
- 배포 전 확인: `-XX:AOTMode=on`이면 위반 시 오류로 종료한다(JDK 27부터 `-XX:AOTMode=required`라는 JEP 갱신 메모). 운영에 그대로 쓰면 모니터링 에이전트 같은 옵션 추가로 기동이 실패할 수 있어 조심하라고 JEP가 적는다.

### 7. "미리 해 두는 것"의 확장

- CDS: JDK 클래스 파싱 결과 → AppCDS(JEP 310·350): 앱 클래스까지 → AOT 캐시(JEP 483): 로드·링크된 상태 → JEP 515: 메서드 실행 프로파일 → JEP 544: 컴파일된 기계어.
- 결정적 차이: 이 계열은 **열린 세계**다. 캐시는 가속일 뿐이고, 캐시에 없는 클래스도 평소처럼 로드·리플렉션된다. JEP 544도 운영에서 워크로드가 바뀌면 다시 JIT한다고 적는다. 네이티브 이미지는 빌드 때 목록에 없는 것은 실행 중에 생길 수 없다.

### 8. 네이티브에서만 실패하는 게이트웨이 선택

- 보이는 오류: `ClassNotFoundException`·`NoSuchMethodException`, 또는 현재 GraalVM 문서의 `MissingReflectionRegistrationError`.
- 원인: `Class.forName(config.get("gateway"))`처럼 이름이 실행 중에 정해지는 리플렉션은 정적 분석이 따라가지 못한다. 메타데이터에 없으면 그 클래스가 이미지에 빠졌을 수 있다. 다른 경로로 이미지에 들어가 있어도 리플렉션 등록이 없으면 조회가 실패한다(`MissingReflectionRegistrationError`). JVM에서는 클래스 로더가 그때 찾아 읽으므로 된다(실험 2의 `JvmReflect`).
- 대처
  - 게이트웨이 클래스를 `reachability-metadata.json`(또는 Spring `RuntimeHints`)에 등록한다.
  - tracing agent로 그 경로를 지나는 테스트를 돌려 수집한다.
  - 리플렉션 대신 `switch`로 구현체를 명시해 정적 분석이 보게 한다.
  - 네이티브 바이너리 통합 테스트에 게이트웨이별 경로를 넣는다.

### 9. CI 러너 exit 137

- 볼 것: 네이티브 빌드 출력 끝의 `Peak RSS`와 단계별 시간. 러너 메모리 한도. GraalVM 문서는 컨테이너·CI에서 기본으로 메모리의 85%(최대 30GiB)를 잡는다고 적는다. 문서 예시의 HelloWorld도 2.14GiB·25.5초였다(문서의 예시 빌드 기계 기준).
- 바꿀 것: 네이티브 빌드를 큰 러너의 별도 단계로, 빌드 메모리 한도 명시, PR마다가 아니라 릴리스 파이프라인에서. `Peak RSS`를 지표로 남겨 증가를 본다.

### 10. 프로필이 안 바뀐다

- Spring Boot 문서: 닫힌 세계에서는 빈 정의가 실행 중 바뀔 수 없다. `@Profile`·프로필별 설정에 제한이 있고, 빈 생성 여부를 바꾸는 속성(`@ConditionalOnProperty`, `.enabled`)은 지원되지 않는다. 빈 구성은 빌드 때 Spring AOT가 이미 정했다.
- 대처: 환경별로 따로 빌드하거나, 빈 구성 분기를 실행 시 값(설정 값을 읽는 하나의 빈)으로 바꾼다.
