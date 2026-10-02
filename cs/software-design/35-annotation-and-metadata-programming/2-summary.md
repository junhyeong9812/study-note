# software-design/35-annotation-and-metadata-programming — 어노테이션과 메타데이터 프로그래밍: 리플렉션 vs 컴파일 타임 처리 — 정리 (힌트)

## 해결하는 문제

같은 반복 작업이 클래스마다 붙는다. 경로 등록, 빈 등록, 게터·생성자, DTO 변환 같은 것이다.

```text
 손으로 쓰기                                   선언으로 쓰기
 router.add("/orders", ctl::list);            @Route("/orders") String list() {...}
 router.add("/orders/1", ctl::one);           @Route("/orders/1") String one() {...}
 public String getName() { return name; }     @Getter class Member { ... }
 dto.name = m.getName(); dto.age = ...        @Mapper interface MemberMapper { ... }
   → 등록과 정의가 두 곳에 흩어진다             → 정의 옆에 "무엇인지"만 적는다
                                               → 누군가(프레임워크·컴파일러)가 읽고 동작을 만든다
```

- *어노테이션(annotation)*: 코드 요소(클래스·메서드·필드 등)에 붙이는 구조화된 메타데이터. 그 자체로는 아무 일도 하지 않는다.
- *메타데이터 프로그래밍*: 동작을 직접 쓰는 대신 "이것은 무엇이다"를 선언하고, 선언을 읽는 쪽이 동작을 만들게 하는 방식.

쉬운 예: 택배 상자에 "취급 주의" 스티커를 붙이면 상자는 그대로다. 스티커를 읽는 물류 직원이 다르게 다룬다.\
똑같은 구조다. 어노테이션은 스티커이고, 읽는 쪽이 둘 있다.

- **런타임 리플렉션**: 프로그램이 돌 때 프레임워크가 클래스를 훑어 스티커를 읽는다(Spring `@Component`·`@RequestMapping`, JPA `@Entity`).
- **컴파일 타임 어노테이션 처리**: 컴파일러가 스티커를 읽어 코드를 만든다(MapStruct `@Mapper`, Lombok `@Getter`).

실무 예: Spring MVC 컨트롤러는 `@GetMapping`만 붙이면 라우팅 표에 들어간다. MapStruct는 `@Mapper` 인터페이스에서 매핑 구현 클래스를 생성한다.

대가도 있다. 동작이 코드에 보이지 않는다("마법"). 스티커를 읽는 쪽이 조용히 못 읽으면 아무 오류 없이 기능이 사라진다(실험 A).

## 동작·원리

### 1. 스티커가 어디까지 살아남나 — 보존 정책

```text
            소스(.java)          클래스 파일(.class)                 실행 중(JVM·리플렉션)
 SOURCE     ● 보인다      ──X   (컴파일러가 버린다)
 CLASS      ● 보인다      ──>   ● RuntimeInvisibleAnnotations ──X  (JVM이 보존할 필요 없음)
 RUNTIME    ● 보인다      ──>   ● RuntimeVisibleAnnotations   ──>  ● getAnnotations()로 읽힌다
 생략        = CLASS (기본값)
```

- *보존 정책(`@Retention`)*: 어노테이션을 어느 단계까지 남길지 정하는 메타 어노테이션. `RetentionPolicy` 값은 `SOURCE`·`CLASS`·`RUNTIME`.
- JDK 21 `RetentionPolicy` 문서: `SOURCE`는 "컴파일러가 버린다", `CLASS`는 "클래스 파일에 기록하지만 런타임에 VM이 보존할 필요는 없다 — 기본값", `RUNTIME`은 "런타임에 보존되어 리플렉션으로 읽을 수 있다".
- 컴파일 타임 처리기가 지금 컴파일하는 소스만 읽는다면 `SOURCE`로 충분하다(예: Lombok `@Getter`는 `SOURCE`). 다른 jar·모듈의 클래스 파일에 붙은 선언까지 봐야 하면 `CLASS` 이상이 필요하다(`SOURCE`는 클래스 파일에 안 남는다 — 실험 A의 `Src`). MapStruct 1.6.3 `@Mapper`는 `CLASS`다(소스 `Mapper.java`). 런타임 프레임워크가 읽으려면 `RUNTIME`이어야 한다.

### 실험 A: 보존 정책과 "조용히 사라지는 라우트"

네 어노테이션을 한 클래스에 붙이고, 미니 프레임워크가 `@Route` 메서드로 라우팅 표를 만든다. `@RouteForgot`은 `@Retention(RUNTIME)`을 빼먹었다.

```java
@Retention(RetentionPolicy.SOURCE)  @interface Src {}
@Retention(RetentionPolicy.CLASS)   @interface Cls {}
@Retention(RetentionPolicy.RUNTIME) @interface Run {}
@interface NoRetention {}                                   // @Retention 생략
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) @interface Route { String value(); }
@Target(ElementType.METHOD) @interface RouteForgot { String value(); }   // RUNTIME을 잊었다

static Map<String, Method> scan(Class<?> c, Class<? extends Annotation> a) {
    Map<String, Method> table = new TreeMap<>();            // 메타데이터 맵: 경로 → 메서드
    for (Method m : c.getDeclaredMethods()) {
        Annotation x = m.getAnnotation(a);                  // 리플렉션으로 스티커 읽기
        if (x == null) continue;
        table.put((String) a.getMethod("value").invoke(x), m);
    }
    return table;
}
```

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, `scratchpad/sd/35/e35/a/Retain.java`, 2026-10-02)

```text
Target1 런타임에 보이는 어노테이션: [@Run()]
@Route 스캔 결과: [/orders, /orders/1]
@RouteForgot 스캔 결과: []  (컴파일 오류·예외 없음)
GET /orders -> 주문 목록
GET /refunds -> 404 (핸들러 없음)
```

같은 클래스를 `javap -v`로 본 클래스 파일:

```text
RuntimeVisibleAnnotations:
  0: #14()
    Run
RuntimeInvisibleAnnotations:
  0: #16()
    Cls
  1: #17()
    NoRetention
```

- 관찰 1 — 리플렉션은 `RUNTIME`만 본다. `Cls`·`NoRetention`은 클래스 파일에 있지만(`RuntimeInvisibleAnnotations`) 런타임에 안 보인다. `Src`는 클래스 파일에도 없다(`javap` 출력에서 `Src` 검색 0건).
- 관찰 2 — `@Retention`을 생략한 `NoRetention`은 `CLASS`로 기록됐다. 문서의 기본값과 같다.
- 관찰 3 — `@RouteForgot`이 붙은 `/refunds`는 컴파일도 실행도 오류 없이 **404**가 됐다. 리플렉션 방식의 실수는 "아무 일도 안 일어남"으로 나타난다.

### 2. 런타임 리플렉션 방식 — 기동 시 스캔

```text
 기동
  │ ① 클래스패스의 .class 목록을 얻는다 (jar 항목·디렉터리)
  │ ② 각 클래스의 어노테이션을 읽는다
  │      - 직접 구현: Class.forName → isAnnotationPresent (클래스를 로드한다)
  │      - Spring: ASM으로 바이트코드만 읽는다 (로드하지 않는다)
  │ ③ 메타데이터 맵을 만든다  클래스 → 어노테이션 → 할 일 (빈 정의·라우팅 표)
  │ ④ 맵을 보고 객체를 만들고 연결한다
  ▼
 요청 처리: 맵을 조회해 메서드를 호출 (Method.invoke 또는 생성된 핸들러)
```

- *리플렉션(reflection)*: 실행 중에 클래스·메서드·필드·어노테이션 정보를 조회하고 호출하는 기능(`java.lang.reflect`).
- *클래스패스 스캔*: 기동 때 패키지 아래 클래스를 훑어 후보를 찾는 일.
- Spring Framework 6.2.11 `ClassPathScanningCandidateComponentProvider` 소스 주석: 후보 탐색은 "ASM `ClassReader`가 뒷받침하는 `MetadataReader`"로 한다. 클래스를 로드하지 않고 바이트코드에서 어노테이션만 읽는다.
- 같은 소스: 미리 만든 후보 색인(`CandidateComponentsIndex`, `META-INF/spring.components`)은 "6.1부터 deprecated, AOT 엔진으로 대체"다.

### 실험 B: 스캔할 클래스 수와 기동 시간

클래스를 N개 만들어 jar로 묶고(절반에 `@Component`), 모든 클래스를 로드해 어노테이션을 확인한다. Spring처럼 ASM으로 읽는 최적화는 하지 않은 **직접 구현**이다.

```java
for (JarEntry e : Collections.list(jar.entries())) {
    if (!e.getName().endsWith(".class")) continue;
    Class<?> c = Class.forName(toClassName(e), false, loader);   // 로드만, 초기화 안 함
    if (c.isAnnotationPresent(component)) found++;
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e35/d/Scan.java`, 2026-10-02 — JVM 기동 시간은 빼고 스캔 구간만 잰다. 3회 실행, 실행마다 다르다)

```text
클래스   101개 로드, @Component    50개, 스캔   87 ms
클래스  1001개 로드, @Component   500개, 스캔  322 ms
클래스  5001개 로드, @Component  2500개, 스캔  921 ms
클래스   101개 로드, @Component    50개, 스캔  123 ms
클래스  1001개 로드, @Component   500개, 스캔  448 ms
클래스  5001개 로드, @Component  2500개, 스캔 1347 ms
클래스   101개 로드, @Component    50개, 스캔  129 ms
클래스  1001개 로드, @Component   500개, 스캔  580 ms
클래스  5001개 로드, @Component  2500개, 스캔 1184 ms
```

- 관찰 — 스캔 시간은 클래스 수에 따라 늘었다(위 3회 범위: 101개 87~129ms, 1001개 322~580ms, 5001개 921~1347ms). 사실 점검 때 같은 jar·같은 제한으로 3회 더 돌리면 101개 127~172ms, 1001개 583~698ms, 5001개 1195~1396ms였다. 6회를 합친 범위는 101개 87~172ms, 1001개 322~698ms, 5001개 921~1396ms다. 절대값은 실행마다 크게 흔들리고, 늘어나는 경향만 같다. 이 제한 환경(2코어)의 값이다.
- 해석 — 런타임 방식은 "선언을 읽는 일"을 **매 기동마다** 한다. 스캔 범위를 좁히거나(`@ComponentScan(basePackages)`), 읽는 비용을 줄이거나(ASM), 빌드 때로 옮기는(AOT) 것이 대책이다.
- 이 수치는 Spring 기동 시간이 아니다. Spring은 클래스를 로드하지 않고 읽으므로 비용 구조가 다르다.

### 3. 컴파일 타임 처리 방식 — 라운드와 코드 생성

```text
 javac
  │ 소스 파싱 → 요소(Element) 트리
  │
  ├─ 라운드 1: 프로세서가 @GenerateBuilder 요소를 받는다 ──> Filer로 새 소스 OrderBuilder.java 생성
  ├─ 라운드 2: 새로 생긴 소스를 다시 처리 대상에 넣는다 (여기엔 대상 0개)
  ├─ 마지막 라운드: 처리할 것이 없다
  │
  └─ 모든 소스(원본 + 생성본) 컴파일 → .class
 실행: 생성된 OrderBuilder는 평범한 코드다. 리플렉션 없음.
```

- *어노테이션 처리기(annotation processor)*: `javax.annotation.processing.Processor`를 구현해 컴파일 중에 불리는 플러그인. JSR 269 "Pluggable Annotation Processing API"(최종 릴리스 2006, jcp.org)가 표준화했다.
- *라운드(round)*: JDK 21 `Processor` 문서 "Annotation processing happens in a sequence of rounds." 생성된 소스는 다음 라운드의 입력이 된다.
- *`Filer`*: 새 파일을 만드는 API. JDK 21 문서는 프로세서가 생성하지 않은 기존 파일을 덮어쓰지 말라고 한다. 기존 클래스를 바꾸고 싶으면 상위·하위 클래스를 생성하는 데코레이터식 설계를 권한다(API Note).
- *`Messager`*: 컴파일러에 NOTE·WARNING·ERROR를 보고하는 API. ERROR를 내면 컴파일이 실패한다.

### 실험 C: 직접 만든 처리기 — 빌더 생성과 컴파일 오류

`record`에 `@GenerateBuilder`(보존 `SOURCE`)를 붙이면 `XxxBuilder` 소스를 만든다. `record`가 아니면 ERROR를 낸다.

```java
@SupportedAnnotationTypes("GenerateBuilder")
@SupportedSourceVersion(SourceVersion.RELEASE_21)
public class BuilderProcessor extends AbstractProcessor {
    public boolean process(Set<? extends TypeElement> annos, RoundEnvironment env) {
        for (Element e : env.getElementsAnnotatedWith(GenerateBuilder.class)) {
            if (e.getKind() != ElementKind.RECORD) {
                processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR,
                    "@GenerateBuilder는 record에만 붙일 수 있다", e);
                continue;
            }
            // record 구성 요소를 읽어 OrderBuilder 소스 문자열을 만들고 Filer로 쓴다
            try (Writer w = processingEnv.getFiler().createSourceFile(name, e).openWriter()) { w.write(src); }
        }
        return true;
    }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/35/e35/b/`, `javac -processorpath pout -s gen ...`, 2026-10-02)

```text
== 1) 정상 컴파일 (프로세서 jar를 -processorpath로)
Note: 라운드 시작, 대상 1개
Note: 라운드 시작, 대상 0개
Note: 라운드 시작, 대상 0개
== 생성된 파일:
OrderBuilder.java
// 생성된 코드 — BuilderProcessor
public final class OrderBuilder {
  private java.lang.String id;
  private long amount;
  private java.lang.String currency;
  public OrderBuilder id(java.lang.String v) { this.id = v; return this; }
  public OrderBuilder amount(long v) { this.amount = v; return this; }
  public OrderBuilder currency(java.lang.String v) { this.currency = v; return this; }
  public Order build() { return new Order(id, amount, currency); }
}
== 실행:
Order[id=o-1, amount=1200, currency=KRW]
Order에 런타임 어노테이션: []
== 2) 규칙 위반 (class에 붙임)
Note: 라운드 시작, 대상 1개
app/Bad.java:2: error: @GenerateBuilder는 record에만 붙일 수 있다
public class Bad { int x; }
       ^
Note: 라운드 시작, 대상 0개
1 error
javac 종료 코드=1
```

`-XprintRounds`로 같은 컴파일을 보면 2라운드의 입력이 생성된 소스다(같은 환경).

```text
Round 1:
	input files: {Order, Main}
	annotations: [GenerateBuilder]
	last round: false
Note: 라운드 시작, 대상 1개
Round 2:
	input files: {OrderBuilder}
	annotations: []
```

- 관찰 1 — 라운드가 셋 돌았다. 첫 라운드에서 대상 1개를 처리했고, 생성된 `OrderBuilder`가 들어간 둘째 라운드와 마지막 라운드에는 대상이 없었다.
- 관찰 2 — 생성 결과는 **읽을 수 있는 소스 파일**이다(`gen/OrderBuilder.java`). 디버거로 따라갈 수 있다.
- 관찰 3 — 실행 시 `Order`에 어노테이션이 없다(`SOURCE`). 런타임 비용이 없다.
- 관찰 4 — 잘못 쓴 선언은 **컴파일 오류**로 막혔다. 실험 A의 "조용한 404"와 대비된다.

### 4. Lombok과 MapStruct — 같은 API, 다른 방식

```text
 MapStruct  @Mapper interface MemberMapper  ──(Filer: 새 소스)──>  MemberMapperImpl.java  (gen/에 파일이 생긴다)
 Lombok     @Getter class Member            ──(javac 내부 AST 수정)──>  Member.class에 getName() 추가
                                                                       (새 소스 파일 없음)
```

- MapStruct는 표준대로 **새 클래스를 생성**한다.
- Lombok은 표준 처리기로 등록되지만(jar의 `META-INF/services/javax.annotation.processing.Processor`), 컴파일 중인 클래스 자체를 바꾼다. jar 안에 `lombok.javac.*` 핸들러가 있다(1.18.42 jar 목록 확인). 표준 `Filer`로는 기존 클래스를 바꿀 수 없으니, 컴파일러 내부 구조를 직접 다루는 것이다.

### 실험 D: Lombok·MapStruct 생성물과 처리기 순서

(실험, JDK 21.0.12 temurin `--cpus=2`, Lombok 1.18.42·MapStruct 1.6.3(Maven Central), `scratchpad/sd/35/e35/c/`, 2026-10-02)

```java
@Getter @RequiredArgsConstructor
public class Member { private final String name; private final int age; }
public record MemberDto(String name, int age) {}
@Mapper public interface MemberMapper {
    MemberMapper INSTANCE = Mappers.getMapper(MemberMapper.class);
    MemberDto toDto(Member m);
}
```

처리기 경로 `lombok:mapstruct-processor`(Lombok 먼저):

```text
== 소스에 getName 정의가 있나:
0
== 컴파일된 Member.class의 메서드(javap):
public class Member {
  private final java.lang.String name;
  private final int age;
  public java.lang.String getName();
  public int getAge();
  public Member(java.lang.String, int);
}
== 생성된 소스 파일:
gen/MemberMapperImpl.java
== 실행:
kim 30
MemberDto[name=kim, age=30]
```

생성된 `MemberMapperImpl.java`의 핵심:

```java
@Generated(value = "org.mapstruct.ap.MappingProcessor", ...)
public class MemberMapperImpl implements MemberMapper {
    @Override
    public MemberDto toDto(Member m) {
        if ( m == null ) { return null; }
        String name = null;
        int age = 0;
        name = m.getName();
        age = m.getAge();
        MemberDto memberDto = new MemberDto( name, age );
        return memberDto;
    }
}
```

처리기 경로 순서를 `mapstruct-processor:lombok`으로 바꾸면:

```text
MemberMapper.java:6: warning: Unmapped target properties: "name, age".
    MemberDto toDto(Member m);
              ^
1 warning
순서 반대 종료=0
(이어서 Use.java를 컴파일·실행)
kim 30
MemberDto[name=null, age=0]
```

- 관찰 1 — 소스에 없는 `getName()`이 클래스 파일에 있다. Lombok이 만든 생성 소스 파일은 없다(`gen/`에는 `MemberMapperImpl.java`만).
- 관찰 2 — 순서를 바꾸자 MapStruct가 게터를 보지 못했다. 컴파일은 **경고 1개로 성공**했고, 실행 결과는 `name=null, age=0`이었다.
- MapStruct 문서(stable reference): Lombok 1.18.16부터 바뀐 동작 때문에 `lombok-mapstruct-binding` 처리기를 추가해야 한다. 이 실험의 Lombok 먼저 순서는 바인딩 없이 동작했지만, 빌드 도구·버전에 따라 다를 수 있다. 문서대로 바인딩을 넣는 것이 안전하다.

같은 실험에서 매핑 누락 정책:

```text
== 기본 정책(WARN)
ViewMapper.java:3: warning: Unmapped target property: "email".
1 warning
종료 코드=0
== unmappedTargetPolicy=ERROR
StrictViewMapper.java:4: error: Unmapped target property: "email".
1 error
종료 코드=1
```

- 기본은 경고다. `unmappedTargetPolicy = ReportingPolicy.ERROR`로 올리면 순서 실수 같은 매핑 누락도 컴파일에서 막힌다.

### 5. javac가 처리기를 찾는 방식 (JDK 버전에 따라 다름)

JDK 21 javac는 실험 D에서 `Use.java`를 컴파일할 때 다음을 출력했다. 이 컴파일은 `-processorpath` 없이 Lombok jar를 클래스패스에만 두었고, javac가 클래스패스에서 처리기를 찾아 돌렸다.

```text
Note: Annotation processing is enabled because one or more processors were found
  on the class path. A future release of javac may disable annotation processing
  unless at least one processor is specified by name (-processor), or a search
  path is specified (--processor-path, --processor-module-path), or annotation
  processing is enabled explicitly (-proc:only, -proc:full).
```

- JDK 23 릴리스 노트(JDK-8321314): JDK 23부터 명시 설정이 없으면 어노테이션 처리를 하지 않는다. 예전 동작을 원하면 `-proc:full`. JDK 21·22는 위 NOTE만 출력한다.
- 그래서 처리기는 `-processorpath`(Maven `annotationProcessorPaths`, Gradle `annotationProcessor`)로 명시해 둔다. 순서도 이 목록이 정한다.

## 쓰이는 자료구조·알고리즘

- **메타데이터 맵(클래스 → 어노테이션 → 할 일)**: 실험 A의 `TreeMap<String, Method>`가 라우팅 표다. Spring의 빈 정의 레지스트리도 같은 모양이다(이름 → 빈 정의).
- **스캔 = 선형 순회**: 클래스 수 N에 비례한다(실험 B). 색인(미리 만든 목록)이나 AOT로 기동 시점에서 빌드 시점으로 옮긴다.
- **AST(추상 구문 트리)와 요소 트리**: 처리기는 `Element`(패키지·타입·메서드·필드) 트리를 읽는다. Lombok은 javac AST를 직접 고친다. 컴파일러 구조는 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md).
- **라운드 = 고정점 반복**: 새 소스가 생기지 않을 때까지 처리를 되풀이한다(실험 C의 라운드 3개).
- **디스패치 테이블**: 요청 경로 → 메서드 맵을 조회해 `Method.invoke`로 부른다(실험 A).

## 적용 — 풀어나가는 법

1. **누가 읽나부터 정한다.**
   - 실행 중 값·설정에 따라 동작이 바뀌어야 한다 → 런타임(`RUNTIME` + 프레임워크).
   - 구조가 컴파일 때 정해지고 실수를 일찍 잡고 싶다 → 컴파일 타임 처리(생성 코드).
2. **런타임 어노테이션을 만들면 `@Retention(RUNTIME)`과 `@Target`을 적는다.** 생략하면 `CLASS`라 리플렉션에 안 보인다(실험 A). 테스트에 "스캔 결과가 비어 있지 않다"를 넣는다.
3. **스캔 범위를 좁힌다.** Spring은 `@SpringBootApplication` 패키지 아래만 본다. 라이브러리 패키지까지 넓히지 않는다.
4. **생성 코드를 읽는다.** Maven은 `target/generated-sources/annotations`, javac는 `-s` 디렉터리에 생성 소스가 있다. 디버거로 생성 클래스에 중단점을 건다. Lombok은 생성 소스가 없으니 `delombok`이나 `javap -p`로 확인한다.
5. **처리기 목록과 순서를 빌드 파일에 명시한다.** Lombok + MapStruct는 처리기 경로에 `lombok-mapstruct-binding`을 추가한다(MapStruct 문서 §14.2, Lombok 1.18.16 이상). 문서의 Maven 예시 순서는 mapstruct-processor → lombok → binding이다 — 순서가 아니라 바인딩에 기댄다. 바인딩 없이 순서에만 기대면 실험 D처럼 순서가 결과를 바꾼다. MapStruct는 `unmappedTargetPolicy = ERROR`(실험 D).
6. **네이티브 이미지(GraalVM)를 쓸 계획이면 리플렉션을 줄이거나 메타데이터를 준다.** GraalVM 문서: 리플렉션 대상은 정적 분석으로 알 수 없어 `reachability-metadata.json` 등으로 알려 줘야 한다. 컴파일 타임 생성 코드는 평범한 호출이라 이 문제가 없다.

진단 도구:

```bash
javap -v -cp out Target1 | grep -A3 RuntimeVisibleAnnotations   # 런타임에 보일 어노테이션
javap -p -cp out Member                                           # Lombok이 만든 메서드
javac -XprintRounds -processorpath ... App.java                   # 라운드별 처리 대상
```

## 장애 시나리오와 대처

### 1. 어노테이션 하나로 생긴 버그를 디버거로 따라가기 어렵다 (⚠ 커리큘럼)

- 현상: 메서드를 불렀는데 트랜잭션·캐시·권한 검사가 끼어 있다. 호출 스택에 내 코드가 아닌 프레임이 수십 개다.
- 보이는 형태: 스택 트레이스에 `$$SpringCGLIB$$`·`Method.invoke`·프록시 클래스. 소스에서 "그 동작을 하는 줄"을 찾을 수 없다.
- 원인: 동작이 선언(어노테이션)에서 생기고, 실제 코드는 프레임워크 안이나 생성 클래스에 있다.
- 대처: 어떤 처리기·후처리기가 그 어노테이션을 읽는지 찾는다(`@Transactional` → 프록시는 [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md)). 생성 소스에 중단점을 건다. 팀 규칙으로 커스텀 어노테이션 수를 제한한다.

### 2. 보존 정책 누락으로 기능이 조용히 꺼진다

- 현상: 새로 만든 커스텀 어노테이션 `@Audited`를 붙였는데 감사 로그가 안 남는다.
- 보이는 형태: 오류·경고 없음. 스캔 결과가 빈 목록(실험 A의 `[]`, `/refunds` 404).
- 원인: `@Retention` 생략 → 기본 `CLASS` → 리플렉션에서 안 보인다.
- 대처: `@Retention(RUNTIME)` 추가. "스캔 결과 ≥ 1" 테스트로 회귀를 막는다. `javap -v`로 `RuntimeVisibleAnnotations`에 있는지 확인한다.

### 3. 기동 시 스캔·리플렉션으로 시작 시간이 늘어난다 (⚠ 커리큘럼)

- 현상: 서비스가 커질수록 기동이 느려져 오토스케일 새 인스턴스가 늦게 붙는다.
- 보이는 형태: 기동 로그의 시작~"Started" 간격 증가. 스캔·빈 생성 단계가 길다.
- 원인: 기동마다 클래스를 훑고 메타데이터를 만든다. 실험 B에서는 클래스 수에 따라 스캔이 늘었다(5001개에서 921~1396ms, 집필·점검 6회 범위, 직접 구현·2코어).
- 대처: 스캔 범위 축소, 지연 초기화, Spring AOT·CDS로 빌드 시점으로 옮기기. 기동 시간의 운영 영향은 [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md).

### 4. 네이티브 이미지에서 리플렉션 대상이 빠져 실패한다 (⚠ 커리큘럼)

- 현상: JVM에서는 되는데 GraalVM 네이티브 이미지에서 특정 기능만 실패한다.
- 보이는 형태: `--exact-reachability-metadata`로 빌드한 엄격 모드에서는 등록되지 않은 리플렉션 접근에 `MissingReflectionRegistrationError`가 난다(GraalVM latest 문서 "Reachability Metadata" — `java.lang.Error`의 하위 타입이다). 같은 문서는 이 모드가 아직 옵션이고 앞으로 기본값이 된다고 한다. 옵션 없는 기본 모드에서 보이는 형태는 확인 못 함 [?]. 이 노트에서는 네이티브 빌드를 돌리지 않았다.
- 원인: GraalVM 문서 — 리플렉션으로 접근할 요소는 정적 분석으로 알 수 없어 reachability metadata로 알려 줘야 한다. 설정에서 빠진 요소는 바이너리에 포함되지 않는다.
- 대처: 메타데이터 수집 에이전트로 설정 생성, 프레임워크 AOT(Spring `RuntimeHints`)로 힌트 등록, 가능한 곳은 컴파일 타임 생성 코드로 바꾼다. 상세는 language/24 aot-native-image-and-startup(미작성, [language README](../../language/README.md)).

### 5. 처리기 순서·설정으로 생성 코드가 틀린다

- 현상: 빌드는 초록인데 DTO 필드가 null이다.
- 보이는 형태: 컴파일 경고 `Unmapped target properties` 한 줄. 실행 결과 `MemberDto[name=null, age=0]`(실험 D).
- 원인: MapStruct가 Lombok보다 먼저 돌아 게터를 보지 못했다. 또는 JDK 23 이상에서 처리기 경로를 명시하지 않아 처리기가 아예 안 돌았다(릴리스 노트 JDK-8321314).
- 대처: `lombok-mapstruct-binding` 추가(순서에 기대지 않게) + `annotationProcessorPaths`를 빌드 파일에 명시, `unmappedTargetPolicy = ERROR`, 경고를 오류로(`-Werror`) 다루는 CI.

## 핵심 문장

- 어노테이션은 스티커일 뿐이다. 동작은 그것을 읽는 쪽(런타임 프레임워크 또는 컴파일 타임 처리기)이 만든다.
- `@Retention`을 생략하면 `CLASS`라 리플렉션에 안 보인다. 실험에서 `RUNTIME`을 빠뜨린 라우트는 오류 없이 404가 됐다.
- 런타임 방식은 기동마다 스캔한다. 직접 구현 실험에서 스캔 시간은 클래스 수에 따라 늘었다.
- 컴파일 타임 처리기는 라운드마다 새 소스를 만들고, 잘못된 선언을 컴파일 오류로 막을 수 있다. 생성 코드는 읽고 디버깅할 수 있다.
- MapStruct는 새 클래스를 생성하고 Lombok은 컴파일 중인 클래스를 바꾼다. 둘을 바인딩 없이 같이 쓰면 처리기 순서가 결과를 바꾼다(실험 D).

## 관련 주제·근거

- 선행
  - [32-inversion-of-control-and-framework-flow](../32-inversion-of-control-and-framework-flow/2-summary.md), [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md)
  - [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) — 파싱·AST·코드 생성
- 후속·연결
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 처리기도 `META-INF/services`로 찾는 플러그인이다
  - [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) — 기동 시간이 운영에 미치는 영향
  - language/24 aot-native-image-and-startup — 미작성([language README](../../language/README.md))
- 문서·소스
  - JDK 21 `java.lang.annotation.Retention`·`RetentionPolicy`(기본 CLASS, 각 정책의 정의) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/annotation/RetentionPolicy.html>
  - JDK 21 `javax.annotation.processing.Processor`(라운드)·`Filer`(새 파일 생성, 기존 파일 덮어쓰기 금지, 데코레이터식 API Note) <https://docs.oracle.com/en/java/javase/21/docs/api/java.compiler/javax/annotation/processing/Filer.html>
  - JSR 269 Pluggable Annotation Processing API(최종 릴리스 2006) <https://jcp.org/en/jsr/detail?id=269>
  - JDK 23 릴리스 노트 "Annotation processing in javac disabled by default"(JDK-8321314) <https://www.oracle.com/java/technologies/javase/23-relnote-issues.html>
  - MapStruct 1.6 Reference Guide — `lombok-mapstruct-binding`, `unmappedTargetPolicy` <https://mapstruct.org/documentation/stable/reference/html/>
  - Project Lombok <https://projectlombok.org/> — 동작 방식은 jar 구성(`lombok.javac.*` 핸들러)으로만 확인했다
  - Spring Framework 6.2.11 소스 `ClassPathScanningCandidateComponentProvider`(ASM `MetadataReader`), `CandidateComponentsIndex`(6.1부터 deprecated) <https://github.com/spring-projects/spring-framework/tree/v6.2.11/spring-context/src/main/java/org/springframework/context>
  - GraalVM Native Image "Reachability Metadata"(정적 분석의 한계, `reachability-metadata.json`, `MissingReflectionRegistrationError`) <https://www.graalvm.org/latest/reference-manual/native-image/metadata/>
- 실험 목록 (모두 JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02, 코드는 scratchpad `sd/35/e35/`)
  - A `a/Retain.java` — 보존 정책별 리플렉션 가시성, `javap -v`, RUNTIME 누락 라우트 404
  - B `d/Gen.java`·`d/Scan.java` — 클래스 101·1001·5001개 스캔 시간 3회(점검 때 3회 더)
  - C `b/proc/BuilderProcessor.java` — 직접 만든 처리기, 라운드 3개, 생성 소스, ERROR 진단
  - D `c/` — Lombok 1.18.42·MapStruct 1.6.3 생성물, 처리기 순서 반대 시 null 매핑, `unmappedTargetPolicy`
