# language/28-bytecode-reading-and-asm — 바이트코드 읽기·쓰기와 ASM: 로드 없이 클래스 파일 다루기 — 정리 (힌트)

## 해결하는 문제

"이 클래스에 어떤 어노테이션이 붙어 있나?"를 알고 싶다. 가장 쉬운 길은 리플렉션이다.

```text
  리플렉션으로 묻기                              클래스 파일 바이트로 묻기 (ASM)
  Class.forName("app.Heavy")                    byte[] = Heavy.class 파일 내용
   → 클래스 로드 (상위 클래스·인터페이스도 로드)      → ClassReader가 바이트를 순서대로 파싱
   → static 초기화 실행 (기본 forName)              → "annotation Lapp/Route;" 같은 이벤트
   → getAnnotation(...)                         클래스는 JVM에 올라가지 않는다
  비용: 로드·링크·초기화, 실패: 의존 클래스가 없으면 오류
```

- *리플렉션*: 실행 중에 이미 로드된 `Class` 객체로 타입 정보를 묻고 다루는 API.
- *클래스 파일*: `javac`가 만든 `.class` 파일. JVM 명세 4장이 형식을 정한다.
- *ASM*: 클래스 파일을 바이트 수준에서 읽고 쓰는 자바 라이브러리. 공식 소개는 "all purpose Java bytecode manipulation and analysis framework"이고, 작고 빠르게 만드는 데 초점을 둔다(asm.ow2.io).

쉬운 예: 도서관 책 분류.
- 리플렉션 방식: 책을 한 권씩 빌려 와서(로드) 펼쳐 보고 분류한다. 빌리려면 그 책이 참조하는 부록까지 다 있어야 한다.
- ASM 방식: 서가에서 책등과 목차만 읽고 분류한다. 빌리지 않는다.

똑같은 구조다.\
수천 개 클래스 중 몇 개만 고르는 일(컴포넌트 스캔)에서 전부 로드하면 비싸고, 고르지 않을 클래스의 static 초기화까지 실행되며, 선택 의존성이 없는 클래스에서 실패한다.

실무 예:
- Spring 컴포넌트 스캔은 클래스패스의 `.class`를 바이트로 읽어 `@Component` 후보를 고른다. 고른 것만 나중에 로드한다.
- 코드 커버리지 도구(JaCoCo)·모킹 라이브러리(Byte Buddy를 쓰는 Mockito)·Gradle은 ASM으로 바이트코드를 계측하거나 클래스를 생성한다(asm.ow2.io 사용처 목록).
- 프록시(CGLIB)는 실행 중에 하위 클래스의 바이트코드를 만들어 정의한다.

## 동작·원리

### 1. 클래스 파일의 모양

```text
  ClassFile {                         (JVM 명세 §4.1)
    u4 magic;              0xCAFEBABE
    u2 minor_version;
    u2 major_version;      JDK 25 → 69  (ASM Opcodes.V25 = 69)
    u2 constant_pool_count;
    cp_info constant_pool[...];       ← 이름·문자열·타입 서술자가 모두 여기에 (번호로 참조)
    u2 access_flags; u2 this_class; u2 super_class;
    u2 interfaces_count; u2 interfaces[...];
    fields[...]; methods[...];
    attributes[...];                  ← RuntimeVisibleAnnotations(§4.7.16) 등
  }
```

- *상수 풀(constant pool)*: 클래스 파일 안의 번호 붙은 표. 클래스 이름·메서드 이름·문자열 상수·타입 서술자를 한 번씩 담고, 나머지 구조는 번호로 가리킨다.
- *타입 서술자(descriptor)*: 타입을 문자열로 적는 형식. 클래스 `dep.OrderHandler`는 `Ldep/OrderHandler;`, 내부 이름(internal name)은 `dep/OrderHandler`다.
- 어노테이션 값 중 `Class` 타입 속성(`handler = OrderHandler.class`)은 클래스 파일에 **타입 서술자 문자열**로만 남는다. `Class` 객체가 아니다(실험 1).

### 2. ASM의 세 역할 — 읽는 쪽, 받는 쪽, 쓰는 쪽

```text
  byte[] ──▶ ClassReader ──이벤트──▶ ClassVisitor (사용자 코드) ──이벤트──▶ ClassWriter ──▶ byte[]
             (파싱)          visit(이름, 상위 클래스, ...)  (걸러내기·바꾸기)              (직렬화)
                             visitAnnotation(서술자)
                             visitField / visitMethod
                             visitEnd
```

- `ClassReader`: 클래스 파일 바이트를 방문 이벤트로 바꾸는 유일한 클래스다. 생성자에서 상수 풀을 파싱한다(ASM developer guide).
- `ClassVisitor`: 이벤트를 받는 추상 클래스. 필요한 메서드만 재정의한다. 어노테이션·필드·메서드는 각각 `AnnotationVisitor`·`FieldVisitor`·`MethodVisitor`로 내려간다.
- `ClassWriter`: 이벤트를 받아 클래스 파일 바이트로 다시 쓴다. 그 자체가 `ClassVisitor`다.
- 읽기만 하면 `ClassReader → 내 ClassVisitor`, 변환이면 `ClassReader → 변환 Visitor → ClassWriter`, 생성이면 `내 코드 → ClassWriter`.
- 파싱 옵션 `SKIP_CODE`·`SKIP_DEBUG`·`SKIP_FRAMES`로 메서드 본문·디버그 정보·스택 맵 프레임을 건너뛸 수 있다. Spring의 `SimpleMetadataReader`는 이 셋을 모두 켠다 — 메타데이터만 필요하기 때문이다.

### 3. 이벤트 API와 트리 API

| | core(이벤트) API | tree(객체) API |
|---|---|---|
| 패키지 | `org.objectweb.asm` | `org.objectweb.asm.tree` |
| 모양 | SAX처럼 순서대로 콜백 | DOM처럼 `ClassNode`·`MethodNode` 트리 |
| 메모리 | 클래스 전체를 객체로 만들지 않음 | 클래스 전체를 객체로 만듦 |
| 쓰임 | 스캔, 단순 변환, 생성 | 앞뒤를 오가야 하는 복잡한 변환, 분석(`tree.analysis`) |

- ASM developer guide: core 패키지는 다른 패키지에 의존하지 않고 단독으로 쓸 수 있다. tree 패키지는 core 위의 DOM 같은 층이고, core로 하기 너무 복잡한 변환에 쓴다.
- 스캔에는 이벤트 API가 맞다. 필요한 이벤트만 받고 나머지는 버리면 된다.

### 4. 리플렉션과 갈리는 지점 — 로드, 초기화, 이름만 남은 Class 속성

```text
                       리플렉션                          ASM
  JVM에 클래스 로드        한다 (상위 타입도)                 하지 않는다
  static 초기화           Class.forName(name)은 한다         하지 않는다
  의존 클래스가 없으면      NoClassDefFoundError 등           읽기는 성공 (이름만 본다)
  Class 타입 속성          Class 객체 (없으면 TypeNotPresent)  "dep.OrderHandler" 문자열
  나중에 Class가 필요하면   이미 있음                         어떤 ClassLoader로 풀지 골라야 한다
```

- *ClassLoader*: 클래스 이름을 받아 바이트를 찾고 `Class`로 정의하는 객체. JVM 안에서 클래스의 정체는 **이름 + 정의한 로더**다. 같은 이름을 다른 로더가 정의하면 다른 클래스다(실험 3).
  - 흔한 오해: "이름이 같으면 같은 클래스다." 로더가 다르면 `==`가 거짓이고 캐스트도 실패한다.
- 마지막 줄이 이 주제의 함정이다. ASM은 이름을 줄 뿐이다. 그 이름을 `Class`로 바꾸는 순간, 코드는 로더를 하나 골라야 한다. 잘못 고르면 `ClassNotFoundException`(→ `TypeNotPresentException`)이 나거나, 이름은 같지만 다른 로더의 `Class`를 얻는다.

### 5. 쓰기 — 클래스를 만들어 정의하기

```java
ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES | ClassWriter.COMPUTE_MAXS);
cw.visit(V17, ACC_PUBLIC | ACC_FINAL, "GreetingSupplier", null, "java/lang/Object",
        new String[] {"java/util/function/Supplier"});
// <init>: aload_0; invokespecial Object.<init>; return
MethodVisitor get = cw.visitMethod(ACC_PUBLIC, "get", "()Ljava/lang/Object;", null, null);
get.visitCode();
get.visitLdcInsn("ASM이 만든 클래스에서 인사");
get.visitInsn(ARETURN);
get.visitMaxs(0, 0);   // COMPUTE_MAXS가 계산
get.visitEnd();
cw.visitEnd();
Class<?> c = MethodHandles.lookup().defineClass(cw.toByteArray());
```

- `COMPUTE_FRAMES`: 검증기가 요구하는 스택 맵 프레임을 ASM이 계산한다. 두 타입의 공통 상위 클래스가 필요하면 기본 구현 `getCommonSuperClass`가 **두 클래스를 로드해서** 구한다(ASM `ClassWriter` 소스 주석: "The default implementation of this method loads the two given classes"). 생성 쪽에도 로더 문제가 숨어 있다(장애 5).
- 정의(define)는 ASM이 아니라 JVM 쪽 일이다. `Lookup.defineClass`, 사용자 `ClassLoader#defineClass`, 에이전트의 `ClassFileTransformer`가 바이트를 받아 정의한다.

### 6. 클래스 파일 버전과 ASM 버전

```text
  ASM 판   새 상수        (asm.ow2.io versions)
  9.7.1   Opcodes.V24   2024-10-06
  9.8     Opcodes.V25   2025-03-29
  9.9     Opcodes.V26   2025-10-04
  9.10    Opcodes.V27   2026-05-14
  9.11    Opcodes.V28   2026-10-04 (프리뷰 기능 미지원)
```

- JDK는 6개월마다 나오고 클래스 파일 major 버전도 그때마다 1씩 오른다. ASM의 `ClassReader`는 자기가 아는 최대 버전보다 새 파일을 만나면 `IllegalArgumentException: Unsupported class file major version N`을 던진다(실험 2).
- 그래서 바이트코드 라이브러리를 쓰는 프레임워크는 새 JDK가 나올 때마다 라이브러리를 올려야 한다. JEP 484가 Class-File API를 만든 동기가 이것이다: 클래스 파일 형식이 6개월 주기로 더 빨리 바뀌고, 프레임워크 개발자는 실행 중인 JDK와 맞는 라이브러리가 필요하다.

### 실험 1: 같은 클래스를 ASM과 리플렉션으로 읽기

`app.Heavy`에 static 초기화 블록과 `@Route(path = "/orders", handler = dep.OrderHandler.class)`를 붙였다. 컴파일한 뒤 `dep/OrderHandler.class`만 지웠다(선택 의존성이 빠진 배포를 흉내).

```java
new ClassReader(bytes).accept(new ClassVisitor(Opcodes.ASM9) {
    @Override public AnnotationVisitor visitAnnotation(String desc, boolean visible) {
        System.out.println("annotation " + desc);
        return new AnnotationVisitor(Opcodes.ASM9) {
            @Override public void visit(String n, Object value) { /* 값과 타입 출력 */ }
        };
    }
}, ClassReader.SKIP_CODE | ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
// 이어서 Class.forName("app.Heavy") → getAnnotation(Route) → handler()
```

(실험, JDK 25.0.1 temurin + ASM 9.10, 2026-10-20)

```text
magic=CAFEBABE major=69
== ASM ClassReader ==
class app/Heavy extends java/lang/Object
annotation Lapp/Route;
  path = /orders (String)
  handler = Ldep/OrderHandler; (Type) -> getClassName()=dep.OrderHandler
ASM 끝 — static init 출력 없음
== 리플렉션 ==
[Heavy] static init 실행
getAnnotation 성공: app.Route
handler() 실패: java.lang.TypeNotPresentException: Type dep.OrderHandler not present
```

- ASM은 `OrderHandler`가 없어도 읽기를 끝냈다. `Class` 속성은 `org.objectweb.asm.Type`(서술자 `Ldep/OrderHandler;`)으로 왔다.
- 리플렉션은 static 초기화를 먼저 실행했다. 어노테이션 객체는 얻었지만 `handler()`를 부르는 순간 `TypeNotPresentException`이 났다. `Class` 속성은 접근할 때 풀린다.

### 실험 2: ASM 판과 클래스 파일 버전

같은 소스를 `javac --release 24`(major 68)와 `--release 25`(major 69)로 컴파일하고 ASM 두 판으로 읽었다.

(실험, JDK 25.0.1 temurin, 2026-10-20)

```text
ASM 9.7.1 v24/dep/OrderHandler.class -> dep/OrderHandler
ASM 9.7.1 v25/dep/OrderHandler.class -> java.lang.IllegalArgumentException: Unsupported class file major version 69
ASM 9.8 v24/dep/OrderHandler.class -> dep/OrderHandler
ASM 9.8 v25/dep/OrderHandler.class -> dep/OrderHandler
```

- 9.7.1은 V24까지 안다. 9.8에서 V25가 들어왔다(versions 페이지와 일치).

### 실험 3: 이름 하나, 로더 셋

ASM이 준 이름 `"dep.OrderHandler"`를 앱 로더와, 같은 디렉터리를 가리키는 `URLClassLoader` 두 개로 풀었다(클래스는 `plugin/` 디렉터리에만 있다).

(실험, JDK 25.0.1 temurin, 2026-10-20)

```text
앱 로더: java.lang.ClassNotFoundException: dep.OrderHandler
plugin-1: class dep.OrderHandler loader=plugin-1
plugin-2: class dep.OrderHandler loader=plugin-2
같은 이름, c1 == c2 ? false
c2.cast(c1 인스턴스): Cannot cast dep.OrderHandler to dep.OrderHandler
```

- 같은 이름이 로더에 따라 "없음", "클래스 A", "클래스 B" 세 결과가 됐다. `Cannot cast dep.OrderHandler to dep.OrderHandler`는 로더 불일치의 전형적인 메시지다.

### 실험 4: 생성과 Class-File API

5절 코드를 돌리고, 실험 1의 `Heavy.class`를 JDK의 `java.lang.classfile`로도 읽었다.

(실험, JDK 25.0.1 temurin + ASM 9.10, 2026-10-20)

```text
266 bytes, GreetingSupplier.get() = ASM이 만든 클래스에서 인사
class app/Heavy major=69
annotation Lapp/Route;
  path = OfStringImpl[constant=/orders]
  handler = OfClassImpl[className=Ldep/OrderHandler;]
```

- 266바이트짜리 클래스를 만들어 정의하고 바로 불렀다.
- Class-File API도 `Class` 속성을 서술자(`Ldep/OrderHandler;`)로 준다. 로드 없이 읽는 도구라면 어느 것이든 이름만 준다.

## 쓰이는 자료구조·알고리즘

- **방문자(Visitor) 패턴** — `ClassReader`가 구조를 순회하며 `visitXxx`를 부르고, 사용자는 원하는 노드만 처리한다. 방문자를 사슬로 이어 필터·변환 파이프라인을 만든다([software-design/27](../../software-design/27-design-patterns-gof/2-summary.md)).
- **상수 풀 = 번호로 찾는 심벌 테이블** — 이름·문자열을 한 번만 저장하고 나머지 구조는 번호로 참조한다. 컴파일러의 심벌 테이블과 같은 생각이다([04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md)). `ClassReader`는 생성자에서 상수 풀 항목의 오프셋 배열을 만들어 두고 번호로 바로 찾는다(Spring 내장 ASM `ClassReader` 소스의 `cpInfoOffsets`).
- **해시 테이블로 중복 제거** — `ClassWriter`의 `SymbolTable`은 상수 풀·부트스트랩 메서드 항목을 해시 집합(체이닝)에 넣어 같은 상수를 두 번 쓰지 않는다(소스 주석 "make sure that this table does not contain duplicated entries").
- **트리 API = 클래스의 AST** — `ClassNode`·`MethodNode`·`InsnList`는 파서가 만드는 구문 트리와 같은 역할이다([03-parsing-grammars-ast](../03-parsing-grammars-ast/2-summary.md)).
- **스택 맵 프레임 계산 = 데이터 흐름 분석** — `COMPUTE_FRAMES`는 제어 흐름 그래프 위에서 각 지점의 지역 변수·스택 타입을 합친다. 합칠 때 공통 상위 타입이 필요하다.

## 적용 — 풀어나가는 법

### 1. 쉬운 예 — "어노테이션 붙은 클래스 목록"을 만드는 두 길

```text
  ① 전부 로드          for (이름 : jar 안의 모든 클래스) Class.forName(이름, false, loader) → isAnnotationPresent
  ② 바이트로 고르기     for (바이트 : jar 안의 모든 .class) ClassReader + visitAnnotation → 고른 것만 로드
```

### 실험 5: spring-core jar 하나를 두 길로 훑기

spring-core 7.1.0-SNAPSHOT jar의 클래스 1237개를 미리 메모리에 읽어 둔 뒤, ① ASM(`SKIP_CODE|SKIP_DEBUG|SKIP_FRAMES`)과 ② `Class.forName(name, false, URLClassLoader(jar만, 부모=플랫폼 로더))`로 각각 훑었다. 각 5회, 프로세스를 새로 띄웠다.

(실험, JDK 25.0.1 temurin + ASM 9.10, i7-13700HX, 2026-10-20)

```text
asm   : 1237 classes read, annotated=147, 56 ~ 68 ms   (5회)
load  : 1226 loaded, failed={NoClassDefFoundError=11}, 379 ~ 411 ms   (5회)
  첫 실패: org.springframework.aot.nativex.feature.PreComputeFieldFeature -> java.lang.NoClassDefFoundError: org/graalvm/nativeimage/hosted/Feature
```

- 이 환경에서 로드 쪽이 6배 안팎 느렸다(중앙값끼리 비교하면 약 401 ms vs 63 ms). 초기화를 끈(`false`) 로드인데도 그렇다. 비율은 클래스 구성에 따라 달라질 수 있다 — 이 노트는 jar 하나만 쟀다.
- 11개는 로드 자체가 실패했다. 상위 인터페이스(`org.graalvm...Feature`)가 클래스패스에 없어서다. 로드는 상위 타입까지 요구하고, ASM은 이름만 읽으므로 실패하지 않는다.
- `annotated`는 어노테이션(CLASS·RUNTIME 보존)이 하나 이상 붙은 클래스 수다.

### 2. 실무 예 — Spring 컴포넌트 스캔이 실제로 하는 일

```text
  ClassPathScanningCandidateComponentProvider
   └─ metadataReaderFactory = new CachingMetadataReaderFactory(resourceLoader)
        └─ delegate = MetadataReaderFactory.create(...) → MetadataReaderFactoryDelegate
             ├─ JDK 17~23: SimpleMetadataReaderFactory → new SimpleMetadataReader(resource, classLoader)
             │     └─ ClassReader.accept(SimpleAnnotationMetadataReadingVisitor, SKIP_DEBUG|SKIP_CODE|SKIP_FRAMES)
             │           └─ visitAnnotation → MergedAnnotationReadingVisitor
             │                 · 어노테이션 타입: ClassUtils.forName(typeName, classLoader)  ← 이건 로드한다
             │                 · Class 속성: Type → type.getClassName()  ← 문자열로 둔다
             │                 · 끝: MergedAnnotation.of(classLoader, source, annotationType, attributes)
             └─ JDK 24+: ClassFileMetadataReaderFactory (java.lang.classfile, Spring 7.0부터)
                   └─ ClassFileAnnotationDelegate: OfClass → resolveTypeName(...) 문자열, 끝은 같은 MergedAnnotation.of
```

- 소스(spring-framework main 기준 포크): `spring-context/.../ClassPathScanningCandidateComponentProvider.java`(`new CachingMetadataReaderFactory(resourceLoader)`), `spring-core/src/main/java/org/springframework/core/type/classreading/` 아래 `CachingMetadataReaderFactory`·`MetadataReaderFactoryDelegate`·`SimpleMetadataReaderFactory`·`SimpleMetadataReader`·`SimpleAnnotationMetadataReadingVisitor`·`MergedAnnotationReadingVisitor`, JDK 24용은 `spring-core/src/main/java24/.../classreading/`의 `MetadataReaderFactoryDelegate`·`ClassFileMetadataReaderFactory`·`ClassFileAnnotationDelegate`.
- spring-core jar는 멀티 릴리스 jar다(`spring-core.gradle`의 `multiRelease { releaseVersions 21, 24 }`, 매니페스트 `Multi-Release: true`). JDK 24 이상에서는 `META-INF/versions/24/`의 위임 클래스가 골라져 Class-File API 경로를 쓴다.
- 스캔하는 클래스 자체는 로드하지 않는다. 하지만 **어노테이션 타입과 enum 값의 클래스는 로드한다**(`ClassUtils.forName(...)`). 못 찾으면 그 어노테이션을 무시한다(`ClassFileAnnotationDelegate`의 "Non-loadable annotation type -> ignore").
- `Class` 속성은 문자열로 `MergedAnnotation`에 들어간다. 사용자가 `getClass("…")`로 꺼낼 때 `TypeMappedAnnotation#adapt`가 `ClassUtils.forName(str, getClassLoader())`로 풀고, 실패하면 `TypeNotPresentException`을 던진다(`spring-core/.../core/annotation/TypeMappedAnnotation.java`). 이때 쓰는 로더가 `MergedAnnotation.of(classLoader, ...)`로 받은 그 로더다.
- 그래서 로더가 중간에 빠지면 문제가 된다. 메타 어노테이션(어노테이션에 붙은 어노테이션)으로 재매핑하는 경로에서 로더를 넘기지 않으면, 메타 쪽 `Class` 속성은 기본 로더로 풀린다(장애 3).

### 3. Spring이 ASM을 들고 다니는 방식

- `org.springframework.asm`: ASM을 패키지 이름만 바꿔 넣은 사본이다. `package-info.java`: "Spring's repackaging of ASM 9.x (with Spring-specific patches; for internal use only)", 앱이나 다른 라이브러리의 ASM 판과 충돌하지 않게 하려는 것이다.
- 패치 예(소스 주석 `SPRING PATCH`)
  - `ClassReader`: 상위 ASM의 버전 검사(`> Opcodes.V27`이면 예외)를 주석 처리해 "새 클래스 파일도 관대하게 파싱 시도"한다.
  - `Opcodes`: `ASM10_EXPERIMENTAL`의 프리뷰 검사를 없애 기본으로 쓴다. `SpringAsmInfo.ASM_VERSION = Opcodes.ASM10_EXPERIMENTAL`.
  - `ClassWriter#getClassLoader`: 공통 상위 클래스 계산에 스레드 컨텍스트 클래스 로더를 먼저 쓴다.
- 관대한 파싱의 대가: 버전 검사 대신, 모르는 새 구조를 만났을 때 다른 곳에서 실패할 수 있다(해석, 확인 안 함 [?]). `SimpleMetadataReader`는 `IllegalArgumentException`을 잡아 "probably due to a new Java class file version that is not supported yet"라는 `ClassFormatException`으로 바꾼다.
- `org.springframework.cglib`도 이 ASM 위에서 프록시 클래스를 만든다(`cglib/core/DebuggingClassWriter`가 `new ClassWriter(flags)`를 감싼다).

### 4. 증상 → 원리 → 확인

| 증상 | 원리 | 확인 |
|---|---|---|
| `Unsupported class file major version N` | 바이트코드 라이브러리가 그 버전을 모른다 | `javap -v X.class \| grep major`, 라이브러리 판의 versions 표 |
| `TypeNotPresentException`(Class 속성) | 문자열 이름을 그 로더가 못 찾는다 | 어느 로더로 풀었나: 디버거로 `getClassLoader()` 반환값 |
| `Cannot cast X to X` | 같은 이름, 다른 로더 | `a.getClass().getClassLoader()` vs `B.class.getClassLoader()` |
| 스캔이 느림 | 후보 판단 전에 로드하고 있다 | 프로파일러에서 `ClassLoader.loadClass` 비중 |

## 장애 시나리오와 대처

### 1. JDK를 올렸더니 기동 시 클래스 파일 파싱 실패

- **현상**: 새 JDK로 컴파일한 클래스가 들어오자 스캔·계측·프록시 생성 단계에서 기동이 멈춘다.
- **보이는 형태**: `IllegalArgumentException: Unsupported class file major version 69`(실험 2), Spring에서는 "ASM ClassReader failed to parse class file - probably due to a new Java class file version that is not supported yet"로 감싼 `ClassFormatException`.
- **원인**: 앱·프레임워크·에이전트(커버리지, APM) 중 하나에 든 ASM이 그 major 버전을 모른다. 사본이 여러 개라 어느 것이 오래됐는지 바로 안 보인다.
- **대처**: 스택 트레이스의 패키지로 어느 사본인지 찾는다(`org.objectweb.asm`, `org.springframework.asm`, `net.bytebuddy.jar.asm` 등 [?]). 그 라이브러리를 새 JDK를 지원하는 판으로 올리거나, 당장은 `--release`를 낮춰 컴파일한다.

### 2. 스캔 단계에서 의존성 없는 클래스 때문에 실패

- **현상**: 선택 의존성(예: GraalVM, Kotlin) 없이 배포했더니 클래스 목록을 만들다 죽는다.
- **보이는 형태**: `NoClassDefFoundError: org/graalvm/nativeimage/hosted/Feature`(실험 5의 실제 메시지).
- **원인**: 후보를 고르기 전에 `Class.forName`으로 로드했다. 로드는 상위 클래스·인터페이스를 요구한다.
- **대처**: 바이트로 읽어 고르고(ASM·Class-File API), 고른 것만 로드한다. 로드가 필요하면 `LinkageError`를 클래스 단위로 잡아 건너뛴다.

### 3. 메타 어노테이션의 Class 속성이 엉뚱한 로더로 풀린다

- **현상**: 플러그인·격리 로더로 스캔한 클래스에서, 직접 붙은 어노테이션의 `Class` 속성은 잘 풀리는데 메타 어노테이션 쪽 같은 속성만 실패하거나 다른 클래스로 나온다.
- **보이는 형태**: `TypeNotPresentException: Type x.Y not present`, 또는 `Cannot cast x.Y to x.Y`(실험 3).
- **원인**: 바이트로 읽은 메타데이터는 `Class` 속성을 문자열로 들고 있다. 메타 어노테이션을 재매핑하며 새 객체를 만들 때 로더를 넘기지 않으면 기본 로더(스레드 컨텍스트 등)로 풀린다. Spring `TypeMappedAnnotation`에서 메타 어노테이션 재매핑 시 로더 미전달이 이런 경우다(같은 클래스의 `getMetaSource()`·`getRoot()`는 `this.classLoader`를 넘긴다).
- **대처**: 문자열을 `Class`로 바꾸는 모든 파생 객체가 원래 로더를 물려받는지 확인한다. 테스트는 별도 로더(`OverridingClassLoader` 등)로 읽힌 클래스 이름을 넣고 `getClassLoader()`가 같은지(`isSameAs`) 본다.

### 4. 생성한 프록시 클래스가 `ClassCastException`·`NoClassDefFoundError`

- **현상**: 실행 중 생성한 하위 클래스를 쓰는 순간 캐스트·링크 오류가 난다.
- **원인**: 생성한 바이트를 정의한 로더가 원본 클래스의 로더와 다르거나, 원본 로더가 볼 수 없는 타입을 참조했다. 클래스 정체는 이름 + 정의 로더다.
- **대처**: 원본 클래스와 같은 로더(또는 그 하위)에 정의한다. `Lookup.defineClass`는 lookup 클래스와 같은 로더·패키지에 정의한다(`MethodHandles.Lookup` Javadoc, 실험 4는 이 방식).

### 5. `COMPUTE_FRAMES`에서 `TypeNotPresentException`

- **현상**: 바이트코드 변환 중 ASM이 실패한다. 생성 대상 클래스나 아직 없는 클래스가 관련된다.
- **원인**: 기본 `getCommonSuperClass`가 두 타입을 `Class.forName(..., false, loader)`로 **로드해서** 공통 상위 클래스를 구한다. 그 로더에서 안 보이거나 지금 만드는 클래스면 실패한다(ASM `ClassWriter` 소스).
- **대처**: `getCommonSuperClass`를 재정의해 로드 없이 계산하거나, 알맞은 로더를 돌려주도록 `getClassLoader`를 재정의한다(Spring 패치는 스레드 컨텍스트 로더를 먼저 쓴다).

## 핵심 문장

- ASM은 클래스 파일 바이트를 읽고 쓰는 라이브러리이고, 읽을 때 클래스를 JVM에 로드하지 않는다. 그래서 static 초기화도, 의존 클래스 로드도 일어나지 않는다.
- `ClassReader`가 바이트를 이벤트로 바꾸고, `ClassVisitor`가 받고, `ClassWriter`가 다시 바이트로 쓴다. 트리 API는 그 위의 객체 모델이다.
- 바이트로 읽은 어노테이션의 `Class` 속성은 타입 이름 문자열뿐이다. `Class`로 바꾸는 순간 로더를 골라야 하고, 클래스의 정체는 이름 + 로더다.
- 클래스 파일 버전은 JDK마다 오르고, 바이트코드 라이브러리는 그 버전을 알아야 읽는다. JEP 484의 Class-File API(JDK 24)는 이 따라잡기를 JDK 안으로 들인 것이다.
- Spring은 ASM을 `org.springframework.asm`으로 패치해 들고 다니며 컴포넌트 스캔과 CGLIB 프록시에 쓰고, JDK 24 이상에서는 스캔에 Class-File API를 쓴다.

## 관련 주제·근거

- 선행
  - [01-compile-interpret-jit](../01-compile-interpret-jit/2-summary.md) — 바이트코드와 JVM 실행
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — 로더와 링크
  - [software-design/35-annotation-and-metadata-programming](../../software-design/35-annotation-and-metadata-programming/2-summary.md) — 어노테이션·메타데이터 프로그래밍
  - [languages/java/syntax/58-reflection](../../../languages/java/syntax/58-reflection/2-summary.md) — 리플렉션
- 후속·연결
  - [19-modules-and-dependency-resolution](../19-modules-and-dependency-resolution/2-summary.md) — 클래스패스·의존성 충돌(`NoClassDefFoundError`)
  - [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md) — 빌드 때 메타데이터·리플렉션 힌트
  - [software-design/33-aop-and-proxies](../../software-design/33-aop-and-proxies/2-summary.md) — CGLIB·JDK 동적 프록시
  - [26-pl-symptom-index](../26-pl-symptom-index/2-summary.md) — 증상 역색인
- 대안·관련 도구
  - `java.lang.classfile`(Class-File API): JEP 484, JDK 24에서 정식(Closed / Delivered, Release 24).
  - Byte Buddy: 클래스 생성·변경용 고수준 API. ASM 사용처 목록에 "Byte Buddy (dynamic class generation), which Mockito uses"로 나온다.
  - Javassist: 자바 소스 문자열로 메서드 본문을 줄 수 있는 바이트코드 편집 라이브러리 [?].
  - 리플렉션: 이미 로드된 클래스를 다룰 때는 가장 단순하다.
- 근거
  - ASM 공식 사이트 <https://asm.ow2.io/> (소개, 사용처: OpenJDK·Groovy·Kotlin 컴파일러·JaCoCo·Byte Buddy·Gradle) · versions <https://asm.ow2.io/versions.html> (9.7.1=V24 ~ 9.11=V28, 최신 9.11.1 2026-10-17) · developer guide <https://asm.ow2.io/developer-guide.html> (core/tree 패키지, `ClassReader`·`ClassWriter` 역할)
  - JVM 명세 SE 25 4장 <https://docs.oracle.com/javase/specs/jvms/se25/html/jvms-4.html> — §4.1 `ClassFile` 구조·magic·major 45~69, §4.7.16 `RuntimeVisibleAnnotations`. `Class` 속성이 서술자로 저장된다는 §4.7.16.1의 원문은 이 노트에서 읽지 못했다 [?] — 대신 실험 1·4의 출력(`Ldep/OrderHandler;`)으로 확인했다.
  - JEP 484 Class-File API <https://openjdk.org/jeps/484> — 동기(6개월 주기로 형식 변화, 실행 중인 JDK와 맞는 라이브러리 필요, JDK도 `jar`·`jlink` 등에 ASM을 내장)
  - Spring Framework 소스(포크, main 기준): `spring-core/src/main/java/org/springframework/asm/`(`package-info.java`, `ClassReader`·`Opcodes`·`ClassWriter`의 `SPRING PATCH`, `SpringAsmInfo`), `.../core/type/classreading/`, `spring-core/src/main/java24/.../core/type/classreading/`, `.../core/annotation/TypeMappedAnnotation.java`, `spring-core/spring-core.gradle`, `spring-context/.../context/annotation/ClassPathScanningCandidateComponentProvider.java`, `.../cglib/core/DebuggingClassWriter.java`
- 실험 목록(i7-13700HX, 로컬 JDK 25.0.1 temurin, ASM 9.10·9.8·9.7.1 jar)
  - 실험 1: `Heavy`(static 블록 + `@Route(handler=OrderHandler.class)`, `OrderHandler.class` 삭제)를 ASM `ClassReader`와 리플렉션으로 읽기
  - 실험 2: `--release 24`/`25` 클래스를 ASM 9.7.1·9.8로 읽기
  - 실험 3: 같은 이름을 앱 로더·`URLClassLoader` 두 개로 풀기, `==`·`cast`
  - 실험 4: `ClassWriter`로 `Supplier` 구현 클래스 생성 → `Lookup.defineClass`, 같은 `Heavy.class`를 `java.lang.classfile`로 읽기
  - 실험 5: spring-core 7.1.0-SNAPSHOT jar 1237클래스를 ASM 스캔 vs `Class.forName(…, false, …)`, 각 5회
