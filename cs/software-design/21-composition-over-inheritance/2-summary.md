# software-design/21-composition-over-inheritance — 상속의 비용·취약한 기반 클래스·위임 — 정리 (힌트)

## 해결하는 문제

코드를 재사용하려고 상속하면, 자식은 부모의 **공개 API만이 아니라 내부 구현 방식**에도 묶인다. 부모가 내부만 바꿨는데 자식이 깨진다.

```text
 상속 (white-box 재사용)                      합성·위임 (black-box 재사용)
 ┌──────────────┐                             ┌──────────────┐
 │ 부모         │ 자식이 부모의 내부 호출 순서    │ 감싸는 쪽     │──호출──> ┌──────────┐
 │  addAll()────┼──> add() ← 자식이 재정의      │  addAll()    │          │ 부품      │
 └──────▲───────┘   (부모가 자기 메서드를        └──────────────┘          │ (공개 API │
        │ extends    부르는지까지 자식이 의존)     부품의 공개 API에만 의존     │  만 사용) │
 ┌──────┴───────┐                                                         └──────────┘
 │ 자식         │
 └──────────────┘
```

- *구현 상속(implementation inheritance)*: `extends`로 부모의 코드를 물려받는 것.
- *합성(composition)*: 다른 객체를 필드로 가지고 그 객체를 써서 기능을 만드는 것.
- *위임(delegation)·전달(forwarding)*: 받은 요청을 가진 객체에게 넘기는 것. 이 노트에서는 둘을 같은 뜻으로 쓴다(엄밀한 구분은 아래 "SELF 문제").
- *화이트박스/블랙박스 재사용*: GoF 1장이 상속을 white-box(부모 내부가 자식에게 보임), 합성을 black-box(내부가 안 보임) 재사용이라 불렀다(책 본문 미열람 — Wikipedia "Design Patterns" 항목의 요약으로 확인). Gamma도 2005 인터뷰(Artima)에서 합성 쪽을 "black box reuse"라고 부른다.

쉬운 예: 남의 집 벽에 못을 박아 선반을 단다. 집주인이 벽을 바꾸면 선반이 떨어진다. 독립 선반장을 두면 벽 공사와 무관하다.\
똑같은 구조다.\
실무 예: `HashSet`을 상속해 "추가 시도 횟수"를 세는 클래스(Bloch Item 18), 라이브러리 기반 클래스를 상속한 커스텀 저장소·컨트롤러가 라이브러리 업그레이드 뒤 조용히 틀어지는 경우.

## 동작·원리

### 1. 자기 호출(self-use)이 자식을 부모 구현에 묶는다

```text
 InstrumentedHashSet.addAll([a,b,c])
   count += 3                                  ← 자식이 셈 (3)
   super.addAll(...)  ── HashSet은 addAll이 없다 → AbstractCollection.addAll
        for e in c: add(e)  ── 동적 디스패치 → InstrumentedHashSet.add(e)
                                  count++  ×3  ← 자식이 또 셈 (+3)
   결과 count = 6
```

- *자기 호출(self-use)*: 클래스가 자기 다른 공개 메서드를 내부에서 부르는 것. `this.add(e)`는 동적 디스패치라 **자식의 재정의가 불린다.**
- JDK 21 소스(openjdk/jdk21u `AbstractCollection.java`)의 `addAll`은 `for (E e : c) if (add(e)) modified = true;`이고, `@implSpec`에 "iterates over the specified collection, and adds each object ... in turn"이라고 적혀 있다. `HashSet.java`에는 `addAll` 재정의가 없다.
- 자식은 이 사실을 문서나 소스를 보고서야 알 수 있다. 부모가 다음 버전에서 자기 호출 방식을 바꾸면 자식의 동작이 바뀐다.

### 실험 A: Bloch Item 18 원본 코드

코드는 저자 저장소 `jbloch/effective-java-3e-source-code`의 `chapter4/item18`을 패키지 줄만 지우고 그대로 실행했다.

```java
public class InstrumentedHashSet<E> extends HashSet<E> {       // "Broken - Inappropriate use of inheritance!"
    private int addCount = 0;
    @Override public boolean add(E e) { addCount++; return super.add(e); }
    @Override public boolean addAll(Collection<? extends E> c) { addCount += c.size(); return super.addAll(c); }
}
public class InstrumentedSet<E> extends ForwardingSet<E> {       // "Wrapper class - uses composition in place of inheritance"
    // add·addAll 재정의는 위와 같다. ForwardingSet이 모든 Set 메서드를 내부 Set s에 넘긴다.
}
// s.addAll(List.of("Snap", "Crackle", "Pop"));  System.out.println(s.getAddCount());
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/20/e21/a/`, 2026-10-02)

```text
$ java InstrumentedHashSet     # 상속
6
$ java InstrumentedSet         # 합성
3
```

- 상속판은 3개를 넣었는데 6을 센다(이중 집계). 합성판의 `ForwardingSet.addAll`은 내부 `s.addAll`을 부르고, 그 안의 `add`는 **내부 `HashSet`의 것**이라 감싼 쪽 `add`가 다시 불리지 않는다.

### 2. 취약한 기반 클래스 — 부모만 바꿨는데 자식이 깨진다

- *취약한 기반 클래스 문제(fragile base class problem)*: 기반 클래스의 겉보기에 안전한 변경이 파생 클래스를 깨뜨리는 문제. Mikhajlov·Sekerinski(ECOOP'98) "A study of the fragile base class problem"이 이 이름으로 다뤘다.

```text
 v1  Inventory.addAll: items.addAll(skus)          ← add()를 안 부른다
 v2  Inventory.addAll: for s: add(s)               ← "검증을 add 한 곳에 모으자" 리팩터링
     (자식 CountingInventory는 한 줄도 안 바뀜)
```

### 실험 B: 기반 클래스만 리팩터링

```java
public class CountingInventory extends Inventory {                  // 상속
    private int count;
    @Override public void add(String sku) { count++; super.add(sku); }
    @Override public void addAll(Collection<String> skus) { count += skus.size(); super.addAll(skus); }
}
public class CountingInventoryW {                                   // 합성
    private final Inventory inner; private int count;
    public void add(String sku) { count++; inner.add(sku); }
    public void addAll(Collection<String> skus) { count += skus.size(); inner.addAll(skus); }
}
// addAll(A,B,C) 후 add(D) → 기대 count = 4
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e21/b/` git 저장소, 2026-10-02 — 첫 블록 v1 실행, 둘째 블록 v2 커밋 뒤 `git diff --stat`과 실행)

```text
상속 count=4 size=4  PASS
합성 count=4 size=4  PASS
```

```text
== git diff --stat v1..v2
 Inventory.java | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
상속 count=7 size=4  FAIL (기대 4)
합성 count=4 size=4  PASS
```

- 바뀐 파일은 기반 클래스 하나(5줄 추가·2줄 삭제)뿐이다. 자식 코드는 그대로인데 상속판 테스트만 깨졌다. 컴파일 오류도, 예외도 없다 — **숫자만 조용히 틀린다.**
- 합성판은 부품의 공개 API(`addAll`)만 썼으므로 부품 내부가 `add`를 부르든 말든 영향이 없다.

### 3. 부모에 새 메서드가 생기면 — 상속은 우회로가 열리고, 합성은 컴파일이 막는다

상속한 자식은 부모의 공개 메서드를 전부 자기 API로 갖는다. 부모가 메서드를 하나 더 만들면 자식에게도 그 문이 생긴다.

### 실험 C: v3 — 기반 클래스에 `addFromCsv` 추가 (items에 직접 넣음)

(실험, 같은 저장소, 2026-10-02)

```text
 Inventory.java | 3 +++
 1 file changed, 3 insertions(+)
상속 addFromCsv 뒤 count=0 size=2
CheckCsvW.java:4: error: cannot find symbol
        w.addFromCsv("E,F");                         // 합성: 감싼 쪽이 열지 않은 메서드
         ^
  symbol:   method addFromCsv(String)
  location: variable w of type CountingInventoryW
1 error
 CountingInventoryW.java | 3 +++
 1 file changed, 3 insertions(+)
합성 addFromCsv 뒤 count=2 size=2
```

- 상속판: 부모의 새 메서드가 자식 API에 **자동으로** 생겼고, 그 길로 들어온 2건은 세지 않았다(count=0, size=2). 자식의 불변식("count = 넣은 수")을 우회하는 새 문이 열렸다.
- 합성판: 감싼 쪽이 열지 않은 메서드는 호출 자체가 컴파일 오류다. 쓰려면 전달 메서드를 **직접** 추가해야 한다(+3줄). 그 자리에서 "어떻게 셀지"를 정하게 된다.
- 대가: 합성은 새 기능을 쓸 때마다 전달 코드를 써야 한다. 이것이 합성의 비용이다(아래 4).

### 4. 합성의 비용 — 전달 코드와 SELF 문제

```text
 ForwardingSet (Bloch) — Set의 메서드를 하나씩 내부 s에 넘기는 전달 클래스 30줄
 InstrumentedSet       — 실제 기능 29줄 (wc -l, 저자 저장소 파일 기준)
```

- 전달 클래스는 한 번 만들어 재사용할 수 있다. Kotlin은 `class Derived(b: Base) : Base by b`로 컴파일러가 전달 메서드를 만들어 준다(Kotlin 문서 "requiring zero boilerplate code").
- *SELF 문제*: 감싸인 객체가 자기 자신(`this`)을 바깥에 넘기면(콜백 등록 등), 그 뒤의 호출은 래퍼를 거치지 않는다. Kotlin 문서도 "members overridden in this way do not get called from the members of the delegate object"라고 적는다.

### 실험 D: 콜백에 `this`를 등록하는 부품을 감쌌을 때

```java
static class Worker implements Handler {
    void start() { BUS.add(this); }                          // 자기 자신(this)을 등록
    public void handle(String msg) { }
}
static class CountingWorker implements Handler {              // 합성
    private final Worker inner; int count;
    void start() { inner.start(); }
    public void handle(String msg) { count++; inner.handle(msg); }
}
static class CountingWorkerSub extends Worker {               // 상속
    int count;
    @Override public void handle(String msg) { count++; super.handle(msg); }
}
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e21/d/SelfProblem.java`, 이벤트 2건 발행)

```text
합성(래퍼) count=0   ← 버스에 등록된 것은 inner(this), 래퍼를 거치지 않는다
상속       count=2
```

- 이 경우는 상속이 맞게 동작한다. **합성이 손해인 상황**이다: 부품이 자기 참조를 바깥에 퍼뜨리는 콜백·리스너 구조.

### 5. 생성자에서 재정의 가능한 메서드를 부르면

부모 생성자 안의 자기 호출도 동적 디스패치로 자식 재정의에 간다. 그때 자식 필드는 아직 초기화 전이다.

### 실험 E: Bloch Item 19 저자 코드(`chapter4/item19`, "NEVER DO THIS!")

```java
public class Super { public Super() { overrideMe(); } public void overrideMe() { } }
public final class Sub extends Super {
    private final Instant instant;
    Sub() { instant = Instant.now(); }
    @Override public void overrideMe() { System.out.println(instant); }
    // main: new Sub().overrideMe();
}
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e21/c/` — 시각은 실행마다 다르다)

```text
null
2026-10-02T01:54:29.780101110Z
```

- 부모 생성자가 도는 시점에는 자식 필드가 아직 초기화 전이다. 한 번 대입되는 `final` 필드인데도 `null`과 실제 시각, 두 값으로 관찰됐다(재실행 3회 모두 첫 줄 `null`).

### 원칙 출처 (주장으로 읽는다)

- GoF 1장 "Favor object composition over class inheritance". Gamma(2005 인터뷰): 상속은 "brittle"하고, 재정의를 허용하는 것은 호출을 허용하는 것보다 "stronger commitment"다. 합성도 작은 인터페이스 상속은 쓴다(리스너 예).
- Bloch 『Effective Java』 3판 4장 Item 18 "Favor composition over inheritance", Item 19 "Design and document for inheritance or else prohibit it". 상속은 같은 패키지·같은 프로그래머 통제 아래이거나 상속용으로 설계·문서화된 클래스일 때 안전하다는 것이 Item 18의 요지로 널리 요약된다(본문 미열람 — 저자 예제 코드와 항목 제목만 확인).
- Snyder, "Encapsulation and inheritance in object-oriented programming languages", OOPSLA '86, pp.38–45 — 상속과 캡슐화의 충돌을 다룬 초기 논문(제목·서지만 확인).

## 쓰이는 자료구조·알고리즘

- **동적 디스패치(vtable)**: 자기 호출이 자식 재정의로 가는 이유. 부모 코드 안의 `add(e)`도 수신 객체의 vtable을 본다 → [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md).
- **전달 체인(forwarding chain)**: 래퍼 → 래퍼 → 실제 객체로 이어지는 연결 리스트 모양. 데코레이터 패턴이 이 구조다([27-design-patterns-gof](../27-design-patterns-gof/2-summary.md)).
- **자기 호출 그래프(self-use graph)**: 클래스 안 메서드들이 서로를 부르는 방향 그래프. 상속하려는 클래스의 이 그래프가 문서화(`@implSpec`)돼 있지 않으면 재정의가 안전한지 알 수 없다.
- **콜백 레지스트리(옵서버 목록)**: 실험 D의 `BUS`. 등록된 참조가 래퍼냐 내부 객체냐가 SELF 문제를 가른다.

## 적용 — 풀어나가는 법

판단 순서:

```text
 재사용하고 싶다
   │
   ├─ 상위 타입의 약속을 다 지키는 진짜 IS-A인가? ── 아니오 ──> 합성
   │                                                (LSP: 22-solid)
   ├─ 부모를 우리가 통제하나(같은 모듈·팀)? ───────── 아니오 ──> 합성 (외부 라이브러리 구체 클래스 상속은 피한다)
   │
   ├─ 부모가 상속용으로 설계·문서화됐나? ──────────── 아니오 ──> 합성
   │   (@implSpec로 자기 호출 명시, protected 훅)
   └─ 예 ──> 상속 가능. 단 생성자에서 재정의 가능 메서드 호출 금지(실험 E)
```

- 상속을 막을 클래스는 `final`로, 정해진 하위 타입만 허용하려면 `sealed`(JDK 17, JEP 409)로 닫는다. Kotlin은 클래스가 기본 `final`이고 `open`을 붙여야 상속된다(Kotlin 문서).
- 합성으로 바꾸는 리팩터링: Fowler 『Refactoring』 2판 카탈로그의 "Replace Superclass with Delegate"·"Replace Subclass with Delegate"(refactoring.com 카탈로그에 항목 확인).
- 전달 코드가 부담이면: 전달 클래스를 한 번 만들어 재사용(Bloch `ForwardingSet`), Kotlin `by`, IDE "Generate delegate methods".
- 콜백·리스너처럼 부품이 `this`를 내보내는 구조에서는 래퍼가 우회된다(실험 D). 이때는 상속, 또는 부품이 등록할 대상을 바깥에서 주입받게 바꾼다.

```java
// 합성 + 인터페이스: 감쌀 대상의 "역할"만 노출
public final class CountingInventory implements InventoryPort {
    private final InventoryPort inner;        // 구체 클래스가 아니라 역할에 의존
    private int count;
    public CountingInventory(InventoryPort inner) { this.inner = inner; }
    @Override public void add(String sku) { count++; inner.add(sku); }
    @Override public void addAll(Collection<String> skus) { count += skus.size(); inner.addAll(skus); }
    public int count() { return count; }
}
```

진단:

```bash
# 우리 코드가 외부 라이브러리의 구체 클래스를 extends 하는 곳
grep -rnE 'class \w+(<[^>]*>)? extends (HashSet|HashMap|ArrayList|Thread|\w+Impl)\b' src/main/java
# 기반 클래스만 바뀐 커밋 뒤 하위 클래스 테스트가 깨진 이력 찾기 (변경 빈도 확인)
git log --numstat --format='%h %s' -- 'src/main/java/*Base*.java' | head -40
```

## 장애 시나리오와 대처

### 1. 부모 변경이 자식 전부를 파손 (fragile base class)

- 현상: 공용 기반 클래스를 리팩터링한 PR은 기반 클래스 파일 하나만 바꿨는데, 배포 뒤 여러 하위 클래스의 집계·감사 로그가 틀어진다.
- 보이는 형태: 하위 클래스 테스트 실패(있다면). 테스트가 없으면 지표 이상(처리 건수가 `addAll` 경로 비중만큼 부풀어 최대 2배) — 실험 B의 `count=7`(기대 4)처럼 예외 없이 숫자만 다르다.
- 원인: 자식이 부모의 자기 호출 방식에 의존했다. 부모가 그 방식을 바꿨다.
- 대처: 즉시는 부모 변경 되돌리기. 근본은 자식을 합성으로 바꾸거나, 부모가 자기 호출을 `@implSpec`로 문서화하고 그것을 계약으로 유지한다. 공용 기반 클래스 변경 PR에는 하위 클래스 목록(IDE "Type Hierarchy")을 붙인다.

### 2. `HashSet` 상속 카운터 이중 집계

- 현상: "추가 시도 횟수" 지표가 실제의 2배다.
- 보이는 형태: 실험 A의 `6`(기대 3). `addAll`을 쓴 경로에서만 부풀고 `add`만 쓴 경로는 맞다.
- 원인: `AbstractCollection.addAll`이 내부에서 `add`를 부른다(JDK 21 소스). 자식이 두 메서드를 다 재정의해 두 번 셌다.
- 대처: 래퍼(합성)로 바꾼다(`InstrumentedSet` → 3). 자식에서 `addAll` 재정의를 지우는 땜질은 JDK 구현 세부에 다시 묶이므로 권하지 않는다.

### 3. 부모의 새 메서드가 자식의 불변식을 우회

- 현상: 라이브러리 업그레이드 뒤 하위 클래스의 검증·집계를 거치지 않은 데이터가 들어온다.
- 보이는 형태: 실험 C의 `count=0 size=2`. 새 메서드를 쓰는 호출부가 생긴 뒤부터 불일치.
- 원인: 상속은 부모의 공개 API를 **전부** 자식 API로 물려준다. 자식이 모르는 새 문이 열린다.
- 대처: 합성으로 노출할 메서드를 고른다(새 메서드는 컴파일 오류로 드러남). 상속을 유지해야 하면 업그레이드 때 부모의 새 공개 메서드 목록을 검토하는 절차를 둔다.

### 4. 생성자에서 재정의 메서드 호출 → `null` 필드

- 현상: 하위 클래스의 `final` 필드가 초기화 중 `null`로 읽혀 NPE 또는 잘못된 로그.
- 보이는 형태: 실험 E의 첫 줄 `null`. 스택 트레이스가 부모 생성자 → 자식 재정의 메서드로 이어진다.
- 원인: 부모 생성자는 자식 필드 초기화 전에 돈다. 그 안의 재정의 가능 메서드 호출이 자식 구현으로 간다.
- 대처: 생성자에서는 `private`·`final`·`static` 메서드만 부른다(Item 19). 초기화 순서가 필요하면 정적 팩토리로 생성 뒤 초기화한다.

### 5. 반대 방향: 합성을 기계적으로 적용 → 래퍼 우회·보일러플레이트

- 현상: 리스너를 래퍼로 감쌌는데 이벤트가 래퍼에 안 온다. 또는 전달 메서드 수십 개를 손으로 유지하다 하나를 빠뜨린다.
- 보이는 형태: 실험 D의 `합성(래퍼) count=0`.
- 원인: 부품이 `this`를 바깥(콜백 레지스트리)에 등록했다(SELF 문제). 전달 코드 누락은 인터페이스가 클 때 생긴다.
- 대처: 콜백 구조는 상속 또는 등록 대상을 주입받는 설계로. 전달 코드는 재사용 전달 클래스·Kotlin `by`·IDE 생성으로 줄이고, 노출할 인터페이스 자체를 작게 만든다(ISP, [22-solid](../22-solid/2-summary.md)).

## 핵심 문장

- 상속은 부모의 공개 API뿐 아니라 **자기 호출 방식**에도 자식을 묶는다. 그래서 부모만 바꿔도 자식이 조용히 깨진다(실험 B: 기반 클래스 1파일 변경, 상속판 count 4→7).
- 합성은 부품의 공개 API에만 의존하므로 부품 내부 변경에 덜 흔들리고, 부품의 새 메서드를 쓰려는 호출은 전달 메서드를 추가하기 전까지 컴파일 오류다.
- 합성의 비용은 전달 코드와 SELF 문제다. 부품이 `this`를 바깥에 넘기는 구조에서는 래퍼가 우회된다(실험 D).
- 상속은 진짜 IS-A이고, 부모를 통제하거나 상속용으로 문서화됐을 때 쓴다. 아니면 `final`/`sealed`로 닫고 합성을 쓴다.

## 관련 주제·근거

- 선행
  - [20-oop-fundamentals](../20-oop-fundamentals/2-summary.md) — 상속·다형성·IS-A/HAS-A, 동적 디스패치
- 후속·연결
  - [22-solid](../22-solid/2-summary.md) — LSP(상속의 행동 기준), ISP(감쌀 인터페이스를 작게)
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) — 데코레이터·전략(합성의 대표 패턴)
  - [05-connascence](../05-connascence/2-summary.md) — 부모-자식 사이의 암묵적 결합을 종류로 나누기
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 감쌀 부품을 바깥에서 넣기
- 글·문서
  - Joshua Bloch, 『Effective Java』 3판(Addison-Wesley, 2018) 4장 Item 18·19 — 저자 예제 `chapter4/item18`(InstrumentedHashSet·ForwardingSet·InstrumentedSet), `chapter4/item19`(Super·Sub) <https://github.com/jbloch/effective-java-3e-source-code>
  - Erich Gamma 인터뷰, Bill Venners, "Design Principles from Design Patterns", Artima, 2005-06-06 <https://www.artima.com/articles/design-principles-from-design-patterns>
  - Wikipedia "Design Patterns"(GoF 책 요약 — white-box/black-box 재사용 용어, 2차 출처) <https://en.wikipedia.org/wiki/Design_Patterns>
  - L. Mikhajlov, E. Sekerinski, "A study of the fragile base class problem", ECOOP'98, LNCS pp.355–382. doi:10.1007/BFb0054099
  - A. Snyder, "Encapsulation and inheritance in object-oriented programming languages", OOPSLA '86, pp.38–45. doi:10.1145/28697.28702
  - OpenJDK jdk21u `src/java.base/share/classes/java/util/AbstractCollection.java`(`addAll`·`@implSpec`), `HashSet.java` <https://github.com/openjdk/jdk21u>
  - Fowler refactoring.com 카탈로그 "Replace Superclass with Delegate" <https://refactoring.com/catalog/replaceSuperclassWithDelegate.html> · "Replace Subclass with Delegate" <https://refactoring.com/catalog/replaceSubclassWithDelegate.html>
  - JEP 409 Sealed Classes(JDK 17) <https://openjdk.org/jeps/409>
  - Kotlin 문서 "Inheritance"(기본 final·open), "Delegation"(`by`, 위임 객체는 재정의를 부르지 않음) <https://kotlinlang.org/docs/inheritance.html> · <https://kotlinlang.org/docs/delegation.html>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`, 2026-10-02)
  - A `scratchpad/sd/20/e21/a/` — Bloch Item 18 원본: 상속 6 vs 합성 3
  - B `scratchpad/sd/20/e21/b/` git 저장소 v1→v2 — 기반 클래스만 바꾼 diff와 테스트 결과
  - C 같은 저장소 v3·v3w — 부모 새 메서드: 상속 우회 vs 합성 컴파일 오류 + 전달 3줄
  - D `scratchpad/sd/20/e21/d/SelfProblem.java` — SELF 문제(합성 손해 사례)
  - E `scratchpad/sd/20/e21/c/` — Bloch Item 19 생성자 재정의 호출
