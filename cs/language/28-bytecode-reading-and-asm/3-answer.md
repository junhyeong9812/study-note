# language/28-bytecode-reading-and-asm — 정답

## 정답

### 1. 리플렉션 대신 바이트를 읽는 이유

- 로드·초기화를 피한다. `Class.forName(name)`은 클래스를 로드하고 static 초기화까지 실행한다. 후보가 아닌 수천 개 클래스의 초기화 부작용과 비용을 치르게 된다.
- 의존 클래스 실패를 피한다. 로드는 상위 클래스·인터페이스를 요구한다. 선택 의존성이 없는 클래스는 `NoClassDefFoundError`로 실패한다(실험 5: spring-core jar에서 11개, `org/graalvm/nativeimage/hosted/Feature`).
- 비용 차이: 실험 5에서 ASM 스캔 56~68 ms, 초기화를 끈 로드 379~411 ms(1237클래스, 각 5회).

### 2. 세 역할과 두 API

```text
  읽기:  byte[] → ClassReader → 내 ClassVisitor
  변환:  byte[] → ClassReader → 변환 ClassVisitor → ClassWriter → byte[]
  생성:  내 코드 → ClassWriter → byte[] → (JVM 쪽) defineClass
```

- `ClassReader`가 바이트를 `visit`·`visitAnnotation`·`visitMethod` 같은 이벤트로 바꾼다. `ClassWriter`도 `ClassVisitor`라 사슬 끝에 붙는다.
- 이벤트(core) API: 순서대로 콜백, 객체 트리를 만들지 않음 → 스캔·단순 변환·생성. 트리 API(`org.objectweb.asm.tree`): 클래스 전체를 `ClassNode` 트리로 → 앞뒤를 오가는 복잡한 변환·분석(ASM developer guide).

### 3. ASM vs 리플렉션 출력 (실험 1)

```text
annotation Lapp/Route;
  path = /orders (String)
  handler = Ldep/OrderHandler; (Type) -> getClassName()=dep.OrderHandler
ASM 끝 — static init 출력 없음
== 리플렉션 ==
[Heavy] static init 실행
getAnnotation 성공: app.Route
handler() 실패: java.lang.TypeNotPresentException: Type dep.OrderHandler not present
```

- ASM: 클래스가 없어도 읽기 성공, static 초기화 없음. `handler`는 `org.objectweb.asm.Type`(서술자 `Ldep/OrderHandler;`)으로 온다. 이름일 뿐이다.
- 리플렉션: `forName`에서 static 초기화가 먼저 실행된다. 어노테이션 객체는 얻지만 `handler()`를 부를 때 `Class`로 풀다가 `TypeNotPresentException`.

### 4. ASM 판과 클래스 파일 버전

- ASM 9.7.1: `IllegalArgumentException: Unsupported class file major version 69`. ASM 9.8: 성공(실험 2). versions 페이지: 9.8에서 `Opcodes.V25`가 들어왔다.
- Spring 패치: `ClassReader` 생성자의 버전 검사(`> Opcodes.V27`이면 예외)를 주석 처리해, 새 클래스 파일도 파싱을 시도한다(`SPRING PATCH: leniently try to parse newer class files as well`).
- 대가: 명확한 버전 오류 대신, 모르는 새 구조를 만났을 때 다른 지점에서 실패할 수 있다(해석, 확인 안 함 [?]). `SimpleMetadataReader`는 `IllegalArgumentException`을 "probably due to a new Java class file version" 메시지의 `ClassFormatException`으로 감싼다.

### 5. 이름 하나, 로더 셋 (실험 3)

- `c1 == c2`: `false`. 클래스의 정체는 이름 + 정의한 로더다.
- `c2.cast(...)`: `Cannot cast dep.OrderHandler to dep.OrderHandler`.
- 앱 로더: `ClassNotFoundException: dep.OrderHandler`(클래스가 `plugin/`에만 있다).

### 6. Spring 컴포넌트 스캔 경로

- 공통: `ClassPathScanningCandidateComponentProvider` → `new CachingMetadataReaderFactory(resourceLoader)` → `MetadataReaderFactory.create(...)` → `MetadataReaderFactoryDelegate`.
- JDK 17~23: `SimpleMetadataReaderFactory` → `SimpleMetadataReader`(`ClassReader.accept(..., SKIP_DEBUG|SKIP_CODE|SKIP_FRAMES)`) → `SimpleAnnotationMetadataReadingVisitor#visitAnnotation` → `MergedAnnotationReadingVisitor` → `MergedAnnotation.of(classLoader, source, annotationType, attributes)`.
- JDK 24 이상: 멀티 릴리스 jar의 `META-INF/versions/24` 위임 → `ClassFileMetadataReaderFactory` → `ClassFileMetadataReader`(`ClassFile.of().parse`) → `ClassFileAnnotationDelegate` → 같은 `MergedAnnotation.of`. Spring 7.0부터(`@since 7.0`).
- 로드되는 것: 어노테이션 타입, enum 값의 클래스(`ClassUtils.forName(..., classLoader)`). 못 찾는 어노테이션 타입은 무시한다.
- 로드되지 않는 것: 스캔 대상 클래스 자체, `Class` 타입 속성(문자열로 저장 → 나중에 `TypeMappedAnnotation#adapt`가 `getClassLoader()`로 풀고, 실패하면 `TypeNotPresentException`).

### 7. 메타 어노테이션 쪽만 실패

- 원인: 바이트로 읽은 메타데이터는 `Class` 속성을 문자열로 들고, 풀 때 `MergedAnnotation.of(classLoader, ...)`로 받은 로더를 쓴다. 메타 어노테이션으로 재매핑하며 새 `TypeMappedAnnotation`을 만들 때 로더를 넘기지 않으면(로더 미전달), 메타 쪽은 로더가 `null`이 된다. `getClassLoader()`는 source가 `Class`·`Member`일 때만 그 로더로 대신하므로, 바이트로 읽은 경우에는 `ClassUtils`의 기본 로더(스레드 컨텍스트 로더 우선)로 푼다. 격리 로더에만 있는 클래스는 `TypeNotPresentException`이 나거나, 부모 쪽에도 있으면 다른 로더의 `Class`가 나온다.
- 대칭 근거: 같은 클래스의 `getMetaSource()`·`getRoot()`는 `this.classLoader`를 넘긴다.
- 테스트: `OverridingClassLoader`로 로드한 클래스 이름을 root 속성으로 넣고 `MergedAnnotations.of(List.of(root)).get(Meta.class).getClass("…").getClassLoader()`가 그 로더와 `isSameAs`인지 확인한다. 수정 전 실패, 수정 후 통과를 본다.

### 8. 전부 로드하면 실패하는 클래스 (실험 5)

- 오류: `NoClassDefFoundError` 11건. 첫 실패 `PreComputeFieldFeature -> NoClassDefFoundError: org/graalvm/nativeimage/hosted/Feature`.
- 이유: 로드는 상위 인터페이스까지 로드해야 끝난다. 그 인터페이스가 클래스패스에 없다. ASM은 `org/graalvm/.../Feature`라는 이름을 읽을 뿐이라 실패하지 않는다.
- 시간: ASM 56~68 ms, 로드 379~411 ms(중앙값 약 63 vs 401 ms, 6배 안팎).

### 9. `COMPUTE_FRAMES`와 로더

- 스택 맵 프레임을 계산하다 두 타입의 공통 상위 클래스가 필요했다. 기본 `getCommonSuperClass`는 두 타입을 `Class.forName(..., false, getClassLoader())`로 로드해서 구한다. 그 로더에서 안 보이거나, 지금 만드는 중이라 아직 없는 클래스면 `TypeNotPresentException`(ASM `ClassWriter` 소스).
- 대처: `getCommonSuperClass`를 재정의(로드 없이 계산)하거나 `getClassLoader`를 재정의. Spring 패치는 스레드 컨텍스트 로더를 먼저 쓴다.
- 정의할 로더: 생성 클래스가 참조하는 타입을 볼 수 있고, 원본 클래스와 같은 로더(또는 그 하위). `Lookup.defineClass`는 lookup 클래스와 같은 로더·패키지에 정의한다(실험 4: 266바이트 `GreetingSupplier` 정의 후 호출 성공).

### 10. Class-File API의 동기와 도구 고르기

- JEP 484 동기: JDK 6개월 주기로 클래스 파일 형식이 더 빨리 바뀐다. 프레임워크는 실행 중인 JDK와 맞는 파서가 필요한데, 외부 라이브러리는 새 JDK를 따라잡을 때까지 시차가 있다(실험 2의 실패가 그 시차). JDK 자신도 ASM을 내장해 쓰고 있었다. JDK 24에서 정식.
- 고르기
  - JDK 24 이상만 지원하면 되는 읽기·생성: Class-File API(버전 시차가 없다).
  - 낮은 JDK까지 지원, 빠른 저수준 스캔·변환: ASM.
  - 프록시·에이전트를 고수준 API로: Byte Buddy(ASM 위, Mockito가 사용 — asm.ow2.io).
  - 소스 문자열로 메서드 본문을 주고 싶을 때: Javassist [?].
  - 이미 로드된 클래스·로드해도 되는 소수 클래스: 리플렉션.
