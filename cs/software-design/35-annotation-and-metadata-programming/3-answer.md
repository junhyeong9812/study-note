# software-design/35-annotation-and-metadata-programming — 정답

## 정답

### 1. 어노테이션은 스티커다

- 어노테이션 자체는 아무 일도 하지 않는다. 코드 요소에 붙은 구조화된 메타데이터일 뿐이다.
- 읽는 주체 둘:
  - 런타임 프레임워크 — 실행 중 리플렉션(또는 바이트코드 읽기)으로 스캔한다. 예: Spring `@Component`·`@GetMapping`, JPA `@Entity`.
  - 컴파일 타임 처리기 — javac 안에서 돌며 코드를 생성하거나 오류를 낸다. 예: MapStruct `@Mapper`, Lombok `@Getter`.

### 2. 보존 정책

```text
            소스      클래스 파일                     실행 중(리플렉션)
 SOURCE     ●   ──X
 CLASS      ●   ──>   ● RuntimeInvisibleAnnotations ──X
 RUNTIME    ●   ──>   ● RuntimeVisibleAnnotations   ──> ●
```

- 생략하면 `CLASS`(JDK 21 `RetentionPolicy` 문서 "This is the default", 실험 A의 `NoRetention`이 `RuntimeInvisibleAnnotations`에 기록됨).

### 3. RUNTIME을 빠뜨린 라우트

(실험 A, JDK 21.0.12, 2026-10-02)

```text
@RouteForgot 스캔 결과: []  (컴파일 오류·예외 없음)
GET /refunds -> 404 (핸들러 없음)
```

- 컴파일: 성공. 실행: 예외 없음. 요청: 404.
- 생략 = `CLASS`라 클래스 파일의 `RuntimeInvisibleAnnotations`에 기록되고, 리플렉션(`getAnnotation`)은 `null`을 돌려준다.

### 4. 라운드

(실험 C, 2026-10-02)

```text
Note: 라운드 시작, 대상 1개
Note: 라운드 시작, 대상 0개
Note: 라운드 시작, 대상 0개
```

- 세 번. 1라운드에 `Order` 1개를 처리해 `OrderBuilder.java`를 만든다. 2라운드는 생성된 소스(`-XprintRounds`의 `input files: {OrderBuilder}`)로 돌고 대상 0개, 마지막 라운드도 0개.
- `class Bad`에 붙이면 `error: @GenerateBuilder는 record에만 붙일 수 있다`, `1 error`, javac 종료 코드 1.

### 5. MapStruct vs Lombok

- MapStruct: `Filer`로 **새 소스**(`MemberMapperImpl.java`)를 생성한다. 생성 디렉터리에서 읽을 수 있다.
- Lombok: 생성 소스 파일 없이 **컴파일 중인 클래스 자체**에 `getName()` 등을 넣는다(실험 D의 `javap -p` 출력, 소스 grep 0건).
- 연결: JDK 21 `Filer` 문서는 처리기가 생성하지 않은 기존 파일을 덮어쓰지 말라고 하고, 기존 클래스를 바꾸는 효과는 상위·하위 클래스 생성으로 내라고 한다. Lombok은 표준 처리기로 등록되지만 javac 내부 AST를 다루는 핸들러(`lombok.javac.*`)로 이 제약 밖에서 일한다.

### 6. 처리기 순서

(실험 D, Lombok 1.18.42·MapStruct 1.6.3)

```text
MemberMapper.java:6: warning: Unmapped target properties: "name, age".
1 warning
순서 반대 종료=0
MemberDto[name=null, age=0]
```

- 컴파일은 경고 1개로 성공, 결과는 `name=null, age=0`. MapStruct가 Lombok보다 먼저 돌아 게터를 보지 못했다.
- 막는 설정: `@Mapper(unmappedTargetPolicy = ReportingPolicy.ERROR)`(실험에서 `error: Unmapped target property: "email"`, 종료 코드 1). MapStruct 문서(§14.2)의 `lombok-mapstruct-binding` 추가 — 문서 예시는 순서가 아니라 바인딩에 기댄다.

### 7. Spring 스캔 vs 직접 구현

- 실험 B의 직접 구현은 `Class.forName`으로 클래스를 **로드**한 뒤 `isAnnotationPresent`를 봤다.
- Spring Framework 6.2.11 `ClassPathScanningCandidateComponentProvider`는 ASM `ClassReader` 기반 `MetadataReader`로 바이트코드에서 어노테이션만 읽는다(로드하지 않음, 소스 주석).
- 후보 색인 `CandidateComponentsIndex`는 6.1부터 deprecated(forRemoval), AOT 엔진으로 대체.

### 8. JDK 23의 기본값

- JDK 23 릴리스 노트(JDK-8321314): 명시 설정(`-processor`, `--processor-path`, `-proc:full` 등)이 없으면 어노테이션 처리를 하지 않는다. 예전 동작은 `-proc:full`.
- JDK 21·22는 클래스패스에서 처리기를 찾아 돌리면서 "A future release of javac may disable annotation processing..." NOTE를 출력한다(실험 D에서 실제 출력).

### 9. 네이티브 이미지 실패

- 원인: GraalVM 문서 — 리플렉션 대상은 런타임 데이터에 달려 정적 분석으로 알 수 없으므로 reachability metadata로 알려 줘야 한다. 빠지면 그 요소가 바이너리에 없다.
- 대처: 메타데이터 수집 에이전트, 프레임워크 AOT 힌트(Spring `RuntimeHints`), `reachability-metadata.json`.
- 컴파일 타임 생성 코드는 `new OrderBuilder().id(...)`처럼 평범한 호출이라 정적 분석이 따라간다. 실험 C에서 `Order`에는 런타임 어노테이션도 없었다(`[]`).
- 실패 형태: GraalVM latest 문서는 `--exact-reachability-metadata`(엄격 모드, 아직 옵션이며 앞으로 기본값 예정)로 빌드하면 메타데이터 없는 리플렉션 접근에 `MissingReflectionRegistrationError`를 던진다고 한다. 기본 모드의 형태는 확인 못 함 [?]. 이 노트는 네이티브 빌드를 직접 돌리지 않았다.

### 10. 기동이 느려짐

(실험 B, 직접 구현·2코어, 집필 3회 + 사실 점검 3회 범위)

- 101개 87~172ms, 1001개 322~698ms, 5001개 921~1396ms. 절대값은 실행마다 흔들리지만 스캔 시간은 클래스 수에 따라 늘었다.
- 대책: 스캔 패키지 축소, 지연 초기화, AOT·CDS로 빌드 시점 이동, 리플렉션 대신 생성 코드. 운영 영향은 reliability/42.
