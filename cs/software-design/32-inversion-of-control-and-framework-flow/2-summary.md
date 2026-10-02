# software-design/32-inversion-of-control-and-framework-flow — 제어 역전: 흐름은 프레임워크가 쥐고 내 코드는 불린다 — 정리 (힌트)

## 해결하는 문제

웹 서버를 직접 짜면 소켓 열기·요청 읽기·스레드 배정·응답 쓰기·예외 처리를 매번 다시 쓴다. 바뀌는 것은 "이 요청에 무엇을 돌려줄까"뿐이다.

```text
 직접 짠 흐름 (내가 main)                       프레임워크 흐름 (프레임워크가 main)
 main()                                         프레임워크 루프
  ├ 소켓 열기                                     ├ 소켓·스레드·파싱·예외·응답 쓰기   ← 고정 골격
  ├ while: 요청 읽기 → 파싱                        └ 바뀌는 칸만 비워 둔다 ──> 내 코드(핸들러)
  ├   내 로직                                                                  "불린다"
  └   응답 쓰기·예외 처리
```

- *제어 역전(Inversion of Control, IoC)*: 누가 언제 무엇을 부를지(흐름)를 내 코드가 아닌 프레임워크가 정하는 것. 내 코드는 끼워 넣을 자리에 등록되고, 프레임워크가 때가 되면 부른다.
- *할리우드 원칙*: "Don't call us, we'll call you." Fowler는 이 별칭이 Richard Sweet의 Mesa 논문(1983)에서 나온 것으로 보인다고 적었다(bliki 「InversionOfControl」, 2005).

쉬운 예: 식당 주방의 주문 시스템이다. 요리사는 손님을 찾아다니지 않는다. 주문표가 들어오면 그때 요리한다. 언제 무엇을 요리할지는 주문 시스템이 정한다.\
똑같은 구조다.\
실무 예: Spring MVC 컨트롤러 메서드, JUnit의 `@BeforeEach`·`@Test`, `JdbcTemplate`에 넘기는 `RowMapper`, 버튼 클릭 리스너, Express 라우트 핸들러. 모두 내가 부르지 않는데 실행된다.

참고: 기존 노트 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「Spring이 대신 해주는 것」 표가 Template Method를 "`JdbcTemplate`, `RestTemplate` 등 `*Template` 전부"에 대응시킨다. 이 노트는 그 대응의 뼈대(제어 역전)와 깨지는 지점을 다룬다.

## 동작·원리

### 1. 라이브러리 vs 프레임워크 — 누가 부르나

```text
 라이브러리                                 프레임워크
 내 코드 ──call──> Collections.sort()       프레임워크 ──call──> 내 코드(콜백·하위 클래스)
         <─return─                                     <─return─
 흐름의 주인: 내 코드                        흐름의 주인: 프레임워크
```

- Fowler(bliki, 2005): 라이브러리는 내가 부르는 함수 묶음이다. 부르면 일을 하고 제어를 돌려준다. 프레임워크는 추상 설계와 동작을 품고, 나는 하위 클래스나 내 클래스를 끼워 넣는다. 그러면 프레임워크 코드가 그 자리에서 내 코드를 부른다.
- Johnson·Foote, "Designing Reusable Classes"(JOOP 1988, 1권 2호): 프레임워크를 맞추려고 사용자가 정의한 메서드는 대개 프레임워크 **안에서** 불리고, 프레임워크가 메인 프로그램 역할을 하며 이 제어 역전이 프레임워크를 "확장 가능한 골격"으로 만든다고 썼다. Fowler는 "Inversion of Control"이라는 말이 이 논문에서 처음 보인다고 추정한다.

### 2. 끼워 넣는 두 방식 — 상속(화이트박스) vs 콜백(블랙박스)

```text
 템플릿 메서드 (상속)                         콜백 (합성)
 abstract ReportExporter                      JdbcTemplate.query(sql, rowMapper)
   final export() {         ← 고정 골격          ├ 커넥션 얻기·문장 실행·예외 번역   ← 고정 골격
     header()               ← 빈 칸                ├ 행마다 rowMapper.mapRow(rs, i)  ← 넘겨받은 함수
     for row: row(r)        ← 빈 칸                └ 자원 닫기
   }
 CsvExporter extends ...  : header(), row() 채움   (rs, i) -> rs.getString(1)       : 람다 하나
```

- *템플릿 메서드(Template Method, GoF)*: 알고리즘 골격은 상위 클래스에 고정하고, 단계 몇 개만 하위 클래스가 채운다. 선택적으로 바꿀 수 있는 빈 단계를 *훅(hook)*이라 한다.
- *콜백(callback)*: 함수(또는 객체)를 넘겨 두면 받은 쪽이 나중에 부른다.
- Johnson·Foote(1988)는 상속으로 맞추는 프레임워크를 *화이트박스*(상위 클래스 내부 관례를 알아야 쓴다), 정해진 인터페이스의 부품을 끼우는 프레임워크를 *블랙박스*라고 불렀다. 화이트박스에서는 인스턴스 상태가 프레임워크 메서드 전부에 암묵적으로 보이고, 블랙박스에서는 넘겨야 할 정보를 명시적으로 넘긴다.

### 3. IoC 컨테이너 — 객체 생성까지 프레임워크가 쥔다

```text
 컨테이너 기동
  ├ 빈 정의 읽기 (@Configuration, 컴포넌트 스캔)
  ├ 생성 → 의존 주입 → 초기화 콜백(@PostConstruct) → 필요하면 프록시로 감싸기(33)
  └ 내 코드가 받는 것은 "컨테이너가 다 끝낸 객체"
 내가 new로 만든 객체 → 위 단계를 하나도 안 거친다
```

- 의존성 주입(DI)은 제어 역전의 한 형태다(객체 조립의 흐름을 컨테이너가 쥔다). Fowler는 IoC 컨테이너 유행 이후 일반 원리(IoC)와 그 구체적 형태(DI)가 혼동된다고 지적했다(bliki, 2005). DI 자체는 [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md).

### 실험 A~C: 누가 내 코드를 부르나 — 호출 스택으로 보기

라이브러리 호출, 콜백 목록을 가진 미니 프레임워크, Spring 컨테이너의 `@PostConstruct`, `JdbcTemplate`의 `RowMapper`를 차례로 실행했다. 내 코드 안에서 `StackWalker`로 "나를 부른 프레임"을 찍었다.

```java
static class MiniFramework {
    private final List<Runnable> onStart = new ArrayList<>();
    void onStart(Runnable cb) { onStart.add(cb); }                 // 등록만 한다
    void run() {                                                    // 흐름은 프레임워크가 쥔다
        System.out.println("  [fw] 설정 읽기");
        for (Runnable cb : onStart) cb.run();                       // 등록 순서대로 부른다
        System.out.println("  [fw] 요청 루프 시작");
    }
}
List<String> names = jdbc.query("select name from t order by id", (rs, i) -> {
    if (i == 0) whoCalledMe("RowMapper 콜백", 5);
    return rs.getString(1);
});
```

(실험, JDK 21.0.12 temurin `--cpus=2`, Spring Framework 6.2.11 · H2 2.3.232 메모리 DB, 2026-10-02 — `scratchpad/sd/30/e32/src/exp32/Main.java`. 스택은 `java.*`·`jdk.*` 프레임을 걸렀다)

```text
== A. 라이브러리: 내가 부른다
  sorted=[a, b] (흐름은 main이 쥐고 있다)
== B. 미니 프레임워크: 등록하면 프레임워크가 부른다
  [fw] 설정 읽기
  [내 코드] 캐시 예열
  [내 코드] 스케줄 등록
  [fw] 요청 루프 시작
== C. Spring 컨테이너가 내 코드를 부른다
  @PostConstruct init() — 호출 스택(안쪽→바깥):
    Main$Notifier.init
    InitDestroyAnnotationBeanPostProcessor$LifecycleMethod.invoke
    InitDestroyAnnotationBeanPostProcessor$LifecycleMetadata.invokeInitMethods
    InitDestroyAnnotationBeanPostProcessor.postProcessBeforeInitialization
    AbstractAutowireCapableBeanFactory.applyBeanPostProcessorsBeforeInitialization
    AbstractAutowireCapableBeanFactory.initializeBean
  RowMapper 콜백 — 호출 스택(안쪽→바깥):
    Main.lambda$main$5
    RowMapperResultSetExtractor.extractData
    RowMapperResultSetExtractor.extractData
    JdbcTemplate$1QueryStatementCallback.doInStatement
    JdbcTemplate.execute
  rows=[kim, lee]
```

- `init()`을 부른 것은 내 코드가 아니라 `BeanPostProcessor`였다. 소스에서 `init()`의 호출처를 검색해도 나오지 않는다. 이것이 ⚠ "누가 이걸 부르나 추적이 어렵다"의 실체다.
- `RowMapper`는 `JdbcTemplate.execute` → `QueryStatementCallback` → `RowMapperResultSetExtractor`를 거쳐 불렸다. `JdbcTemplate` 자신도 내부 단계를 콜백(`StatementCallback`)으로 나눠 두었다.
- 미니 프레임워크는 등록 순서대로 콜백을 불렀다. "콜백 등록 목록"은 리스트 하나다.

### 4. 프레임워크 수명 주기 밖의 객체

```text
 ctx.getBean(Notifier.class)   →  생성 + @Autowired 주입 + @PostConstruct + (프록시)
 new Notifier()                →  생성만. 필드는 null, init 안 불림, 프록시 아님
```

### 실험 D: 컨테이너 빈 vs `new`

```java
public static class Notifier {
    @Autowired Clock clock;
    boolean initialized;
    @PostConstruct void init() { initialized = true; ... }
    String send() { return "sent at " + clock.now(); }
}
```

(실험, 같은 환경, 2026-10-02)

```text
== D. 컨테이너 밖에서 new로 만든 객체
  컨테이너 빈: initialized=true send=sent at 2026-10-02T00:00
  new 객체:   initialized=false clock=null
  new 객체 send() -> NPE: Cannot invoke "exp32.Main$Clock.now()" because "this.clock" is null
```

- 같은 클래스인데 `new`로 만든 객체는 주입도 초기화 콜백도 받지 못했다. 컴파일 오류는 없고, 쓰는 순간 NPE다.
- 필드 주입은 이 실수를 숨긴다. 생성자 주입이면 `new Notifier()`가 컴파일되지 않는다(필수 인자 누락).

### 5. 템플릿 메서드의 골격은 하위 전부에 퍼진다

```text
 ReportExporter.export()  ← 골격 한 줄 수정
   ├ CsvExporter       동작 바뀜
   ├ TsvExporter       동작 바뀜   (요구는 CSV 하나였어도)
   └ MarkdownExporter  동작 바뀜
```

### 실험 E: 골격 한 줄 vs 훅 하나

CSV·TSV·Markdown 세 하위 클래스를 가진 `ReportExporter`(골격 `final export()`)에 "CSV 연동용으로 끝에 `# total=N` 줄을 붙여 달라"는 요구를 두 방식으로 반영하고, 하위마다 골든 테스트(기대 출력 비교)를 돌렸다. 세 하위 클래스는 한 파일에 있다.

```java
// 방식 1: 골격에 직접 추가
        out.append("# total=").append(rows.size()).append('\n');   // CSV 연동 요구로 추가
// 방식 2: 훅 — 기본은 빈 문자열, CSV만 override
        out.append(trailer(rows));                  // 훅: 기본은 빈 문자열
    String trailer(List<String[]> rows) { return ""; }
```

(실험, JDK 21 temurin, git 2.43.0, 2026-10-02 — `scratchpad/sd/30/e32tm/`)

```text
 v1 (변경 전)                       방식 1: 골격 변경                     방식 2: 훅 추가
  csv golden PASS                    ReportExporter.java | 1 +             ReportExporter.java | 3 +++
  tsv golden PASS                    1 file changed, 1 insertion(+)        1 file changed, 3 insertions(+)
  md golden PASS                      csv golden FAIL                       csv golden FAIL
  실패 0/3                            tsv golden FAIL                       tsv golden PASS
                                      md golden FAIL                        md golden PASS
                                      실패 3/3                              실패 1/3
```

- 방식 1은 한 줄 바꿨는데 세 하위의 동작이 함께 바뀌었다. 요구는 CSV 하나였다.
- 방식 2의 CSV 실패는 의도한 변경이다(골든 파일을 갱신할 대상). TSV·Markdown은 그대로다.
- 반대 상황: 세 형식 모두에 들어가야 하는 수정(예: 줄바꿈 문자 통일)이면 방식 1의 한 줄이 세 곳을 한 번에 고친다. 골격 공유는 "함께 바뀌어야 할 때" 이득이고 "하나만 바뀌어야 할 때" 손해다. 상속의 일반적인 비용은 [21-composition-over-inheritance](../21-composition-over-inheritance/2-summary.md)(취약한 기반 클래스).

## 쓰이는 자료구조·알고리즘

- **고정 골격 + 훅** — 상위 클래스의 `final` 메서드가 순서를 고정하고, 추상 메서드(필수 칸)·기본 구현이 있는 메서드(선택 칸=훅)를 부른다. 동적 디스패치(가상 메서드 테이블)가 하위 구현을 고른다.
- **콜백 등록 목록** — `List<Callback>`에 등록하고, 이벤트가 오면 순회하며 부른다(실험 B). 순서가 의미를 가지면 등록 순서나 `@Order`로 정한다. GoF Observer와 같은 뼈대다.
- **수명 주기 상태 기계** — 컨테이너는 빈마다 생성 → 주입 → 초기화 → 사용 → 소멸 단계를 밟는다. `BeanPostProcessor` 목록이 각 단계에 끼어든다(실험 C 스택).
- **이벤트 루프·디스패처** — 요청·이벤트를 받아 등록된 핸들러로 보내는 루프. 서버 쪽 구현은 [os/27-event-based-concurrency](../../os/27-event-based-concurrency/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **흐름을 누가 쥘지 정한다.** 매번 같은 순서·자원 관리·예외 처리가 반복되면 골격으로 뽑을 후보다. 순서 자체가 경우마다 다르면 라이브러리(내가 부름)로 남긴다.
2. **끼우는 방식을 고른다.** 단계가 한두 개고 상태가 없으면 콜백(람다). 단계가 여럿이고 서로 상태를 나누면 인터페이스 하나를 구현한 객체. 상속(템플릿 메서드)은 하위가 상위 관례를 알아야 하므로(화이트박스) 마지막 선택지로 둔다.
3. **골격을 닫는다.** 템플릿 메서드의 골격 메서드는 `final`로 두어 하위가 순서를 바꾸지 못하게 한다. 하위마다 다른 것은 훅으로 연다(실험 E 방식 2).
4. **불리는 지점을 문서화한다.** "이 메서드는 누가 언제 부르나"를 Javadoc·주석에 적는다. 흐름이 코드에 안 보이기 때문이다.
5. **프레임워크 객체는 프레임워크에게 받는다.** 빈이 필요하면 주입받는다. `new`로 만들지 않는다.

### 2. 코드 — 콜백형 템플릿 (Java)

```java
// 골격: 자원 열기·닫기와 예외 번역은 여기서만
final class FileTemplate {
    <T> T withLines(Path p, Function<Stream<String>, T> callback) {
        try (Stream<String> lines = Files.lines(p)) {
            return callback.apply(lines);                 // 바뀌는 부분만 호출자가 넘긴다
        } catch (IOException e) {
            throw new UncheckedIOException("read failed: " + p, e);
        }
    }
}
long errors = new FileTemplate().withLines(log, s -> s.filter(l -> l.contains("ERROR")).count());
```

### 3. 진단 — "누가 이걸 부르나"

- 브레이크포인트나 `Thread.dumpStack()`·`StackWalker`로 호출 스택을 본다(실험 C). 정적 검색으로는 안 나온다.
- Spring Boot Actuator의 `beans` 엔드포인트는 애플리케이션의 빈 목록을 보여 준다(Spring Boot 3.5 문서 「Endpoints」). 내가 `new`로 만든 객체는 여기에 없다.
- `new`로 만든 프레임워크 객체 찾기: `@Component`·`@Service` 붙은 클래스를 `new`하는 곳을 검색한다(`grep -rn "new OrderService(" src/main`). ArchUnit 규칙으로 막을 수도 있다([41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)).

## 장애 시나리오와 대처

### 1. "누가 이걸 부르나" 추적 불가 (⚠ 커리큘럼)

- 현상: 메서드가 실행되는데 호출처 검색 결과가 0건이다. 또는 이상한 시점에 실행된다.
- 보이는 형태: IDE "Find Usages" 0건. 장애 로그의 스택 맨 아래가 프레임워크 클래스뿐이다(실험 C).
- 원인: 프레임워크가 리플렉션·콜백 목록·`BeanPostProcessor`로 부른다. 흐름이 내 코드에 없다.
- 대처: 스택 트레이스에서 프레임워크 진입점을 찾고, 해당 확장 지점 문서(수명 주기 콜백·이벤트 리스너·스케줄러)를 확인한다. 메서드에 "누가 언제 부르는가"를 적는다.

### 2. 상위 골격 변경이 하위 전부의 동작을 바꿈 (⚠ 커리큘럼)

- 현상: 한 형식(CSV)만 고치려 했는데 다른 형식 출력까지 바뀌었다.
- 보이는 형태: 변경 diff는 1파일·1줄인데 골든·스냅샷 테스트가 하위 개수만큼 깨진다(실험 E 방식 1: 3/3).
- 원인: 골격은 하위 전부가 공유한다. 상위를 고치는 사람은 하위 구현을 다 알기 어렵다(취약한 기반 클래스).
- 대처: 하위마다 다른 요구는 훅으로 연다(실험 E 방식 2: 1/3, 의도한 1건). 하위가 많고 변형이 잦으면 콜백·전략(합성)으로 옮긴다(21).

### 3. 프레임워크 수명 주기 밖 `new` → 주입·훅 미적용 (⚠ 커리큘럼)

- 현상: 같은 클래스인데 어떤 경로에서만 NPE가 나고, 트랜잭션·캐시가 안 걸린다.
- 보이는 형태: `NullPointerException: ... because "this.clock" is null`(실험 D). `@PostConstruct` 로그가 없다.
- 원인: `new`로 만든 객체는 컨테이너의 생성 → 주입 → 초기화 → 프록시 단계를 거치지 않는다.
- 대처: 주입받는다. 필요할 때마다 새 객체가 필요하면 `ObjectProvider<T>`·팩토리 빈을 주입받는다. 필드 주입을 생성자 주입으로 바꾸면 `new`가 필수 인자 때문에 컴파일 단계에서 드러난다.

### 4. 콜백 등록 순서에 숨은 의존

- 현상: 리스너 하나를 추가했더니 다른 리스너가 준비 안 된 데이터를 본다.
- 보이는 형태: 기동 직후에만 나는 NPE·빈 캐시.
- 원인: 콜백은 등록 순서(또는 `@Order`)대로 불린다(실험 B). 순서가 코드에 드러나지 않는다.
- 대처: 순서가 의미를 가지면 `@Order`로 명시하고, 콜백끼리 서로의 결과에 기대지 않게 나눈다.

## 핵심 문장

- 제어 역전은 흐름(누가 언제 부르나)을 프레임워크가 쥐고 내 코드는 정해진 자리에서 불리는 구조다. 라이브러리는 내가 부르고, 프레임워크는 나를 부른다.
- 끼우는 방식은 상속(템플릿 메서드, 화이트박스)과 콜백·인터페이스(블랙박스) 두 갈래다.
- 흐름이 코드에 안 보이므로 호출처 검색이 0건이 된다. 실험에서 `@PostConstruct`를 부른 것은 `BeanPostProcessor`였다.
- 템플릿 메서드 골격 한 줄 변경은 하위 전부에 퍼진다. 실험에서 1줄 변경이 골든 3/3을 깼고, 훅으로 바꾸자 의도한 1건만 바뀌었다.
- 컨테이너 밖에서 `new`로 만든 객체는 주입·초기화·프록시를 받지 못한다.

## 관련 주제·근거

- 선행
  - [22-solid](../22-solid/2-summary.md) — DIP(의존 방향 역전)는 IoC와 이름이 비슷하지만 다른 것이다
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) · 기존 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — Template Method·Observer, 「Spring이 대신 해주는 것」
- 후속·연결
  - [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md) — 컨테이너가 만든 객체를 프록시로 감싼다
  - [34-middleware-filter-interceptor-chains](../34-middleware-filter-interceptor-chains/2-summary.md) — 요청 처리 흐름을 프레임워크가 쥐고 체인을 부른다
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — IoC의 한 형태인 DI
  - [21-composition-over-inheritance](../21-composition-over-inheritance/2-summary.md) — 템플릿 메서드의 상속 비용
  - [36-extension-points-and-plugins](../36-extension-points-and-plugins/2-summary.md) — 확장 지점·SPI
- 글·문서
  - Martin Fowler, "InversionOfControl", bliki, 2005-06-26 — 라이브러리 vs 프레임워크, 템플릿 메서드·JUnit 예, 할리우드 원칙 어원 <https://martinfowler.com/bliki/InversionOfControl.html>
  - Ralph E. Johnson, Brian Foote, "Designing Reusable Classes", JOOP 1(2), 1988-06/07, pp. 22–35 — 제어 역전·화이트박스/블랙박스 프레임워크 <http://www.laputan.org/drc/drc.html>
  - GoF 『Design Patterns』(1994) Template Method — 책 본문은 열람하지 못했다. 구조는 기존 노트와 Fowler bliki의 설명 범위로 썼다
  - Spring Framework 6.2.11 소스·실행: `InitDestroyAnnotationBeanPostProcessor`, `JdbcTemplate`·`RowMapperResultSetExtractor`(실험 C 스택)
- 실험 목록 (JDK 21.0.12 temurin `--cpus=2` 일회용 컨테이너)
  - A~C 라이브러리 호출 vs 미니 프레임워크 콜백 vs Spring `@PostConstruct`·`RowMapper` 호출 스택 — `scratchpad/sd/30/e32/src/exp32/Main.java` (Spring 6.2.11, H2 2.3.232, jakarta.annotation-api 2.1.1)
  - D 컨테이너 빈 vs `new` 객체(주입·초기화 누락, NPE)
  - E 템플릿 메서드 골격 변경 vs 훅: `git diff --stat`과 골든 테스트 실패 수 — `scratchpad/sd/30/e32tm/`(git 저장소, 브랜치 `skeleton-change`·`hook-change`)
