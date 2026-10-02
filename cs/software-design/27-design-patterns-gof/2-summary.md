# software-design/27-design-patterns-gof — GoF 디자인 패턴 23: 언제 쓰고 언제 걷어내나 — 정리 (힌트)

## 해결하는 문제

같은 설계 문제를 사람마다 다른 말로 설명하면 리뷰가 길어진다. 패턴은 **반복되는 문제와 해법의 짝에 이름을 붙인 것**이다.

```text
 "타입마다 계산이 다르고, 타입이 계속 늘어난다"
      │  이름이 있으면
      v
 "여기 Strategy로 가자"  ← 한 단어로 구조·장단점·대안까지 전달
      │  그런데 축이 실제로 없으면
      v
 인터페이스 1개 + 구현 1개 + 팩토리 1개 = 간접 계층만 늘어남  (패턴을 위한 패턴)
```

- *디자인 패턴(design pattern)*: 특정 맥락에서 반복되는 설계 문제와 그 해법의 짝. GoF 『Design Patterns: Elements of Reusable Object-Oriented Software』(Gamma·Helm·Johnson·Vlissides, Addison-Wesley 1994)가 객체지향 패턴 23개를 생성 5·구조 7·행위 11로 정리했다.
- *GoF(Gang of Four)*: 위 책의 네 저자.

쉬운 예: 바둑 정석이다. 정석은 국지적 최선이지만 판 전체 흐름에 안 맞으면 버린다.\
똑같은 구조다.\
실무 예: 결제 상태 전이(State), 수단별 수수료(Strategy), 외부 PG 연동(Adapter), 승인 규칙 사슬(Chain of Responsibility).

**23개 각각의 목적·구조·쓰지 말아야 할 때·헷갈리는 쌍·Spring이 흡수한 것은 원본 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)에 있다.**\
이 노트는 원본이 비워 둔 것 — 패턴을 **고르는 기준**, 패턴 안의 자료구조(트리·리스너 목록·상태 기계)가 실제로 깨지는 방식, 그리고 "패턴이 손해인 변경"을 실험으로 보인다.

## 동작·원리

### 1. 패턴 = 변하는 것을 가두는 상자

```text
 GoF 1장의 두 원칙 (Wikipedia "Design Patterns" 문서의 인용 표기: Gang of Four 1995:18, :20)
   "Program to an interface, not an implementation."
   "Favor object composition over class inheritance."

 패턴마다 "무엇이 바뀌어도 되게" 하나
   Strategy      알고리즘          State      상태별 행동
   Factory Method 만들 구체 클래스  Observer   누가 듣는지
   Decorator     덧붙일 기능       Visitor    연산 (대신 타입 추가는 비싸짐)
   Adapter       외부 인터페이스   Composite  잎인가 묶음인가
```

- 패턴은 **한 축의 변경을 싸게** 만들고, 대신 간접 계층(인터페이스·위임 한 단계)을 비용으로 낸다.
- 그래서 고르는 질문은 하나다: **그 축이 실제로 바뀌나?** 바뀌는 축이 없거나 다른 축이 바뀌면 비용만 남는다.

### 2. 고르는 순서

```text
 1. 바뀌는 것이 무엇인가? (git log로 실제 변경 이력을 본다)
 2. 그 변경이 지금 몇 곳을 건드리나?
 3. 언어 기능으로 충분한가?  enum+switch, sealed+패턴 매칭, 람다, record
 4. 프레임워크가 이미 하나?  빈 스코프(Singleton), AOP(Proxy), 이벤트(Observer), 필터 체인(CoR)
 5. 그래도 아프면 패턴 — 가장 작은 형태로
```

- 3번이 Java 17·21에서 커졌다. Visitor 대신 `sealed` + 패턴 매칭 `switch`(원본 23절), Strategy 대신 `Function<A,B>` 람다, Command 대신 record 값(26 functional-core-imperative-shell).
- 참고: 원본 「관련 자료」의 "Martin Fowler, 'Refactoring to Patterns'의 관점"은 저자가 틀렸다. 『Refactoring to Patterns』(2004)는 **Joshua Kerievsky**의 책이고, Fowler는 소개 글(martinfowler.com/books/r2p.html)에서 이 책이 GoF 패턴을 "미리 설계하지 않고 시스템이 자라면서 진화시켜 도달하는" 길을 보인다고 썼다. 리팩터링으로 패턴에 도달하는 경로는 29 refactoring-to-patterns에서 다룬다.

### 실험 A: "패턴을 위한 패턴"에 같은 변경 세 개 적용

두 판을 같은 git 저장소에 두고 같은 변경 요청을 커밋 단위로 적용했다.

```text
 plain    Fees.fee(amount)                         1파일
 pattern  Main → FeeService → FeeCalculator → FeePolicyFactory.create() → FeePolicy(DefaultFeePolicy)
          인터페이스 1 + 구현 1 + 팩토리 1 + 계산기 1 + 서비스 1 + Main 1     6파일
          (구현이 하나뿐인 인터페이스, 인자 없는 팩토리 — "언젠가 바뀌겠지")
          (plain은 main이 Fees.java 안에, pattern은 진입점 Main.java가 따로 있다)
```

변경 1은 요율 3% + 최소 100원, 변경 2는 결제 수단별 요율(카드·계좌·포인트), 변경 3은 수단 하나 추가(가상계좌 0.5%).

(실험, git 2.43.0 + JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/25/e27/build.sh`·`measure.sh`·`run.sh`, 2026-10-02)

```text
== v0 규모
  plain: 파일 1개, 7줄
  pattern: 파일 6개, 26줄
== 변경1(요율3%+최소100)
  [plain]  1 file changed, 1 insertion(+), 1 deletion(-)
  [pattern]  1 file changed, 1 insertion(+), 1 deletion(-)
== 변경2(결제수단별요율)
  [plain]  1 file changed, 10 insertions(+), 3 deletions(-)
  [pattern]  6 files changed, 19 insertions(+), 6 deletions(-)
     pattern/BankFeePolicy.java    | 3 +++
     pattern/FeeCalculator.java    | 6 +++---
     pattern/FeePolicyFactory.java | 9 ++++++++-
     pattern/FeeService.java       | 2 +-
     pattern/Main.java             | 2 +-
     pattern/PointFeePolicy.java   | 3 +++
== 변경3(가상계좌추가)
  [plain]  1 file changed, 2 insertions(+), 1 deletion(-)
  [pattern]  3 files changed, 5 insertions(+), 1 deletion(-)
```

```text
(run.sh — 각 커밋을 컴파일·실행, v0 발췌)
  plain   스택 깊이=3
  plain   fee(10000)=250
  pattern 스택 깊이=5
  pattern fee(10000)=250
```

- 관찰 1 — 변경 1(규칙 수정)은 두 판이 똑같이 한 줄이었다. 간접 계층은 이 변경에 아무 도움이 안 됐다.
- 관찰 2 — 변경 2(진짜로 축이 생김)에서 패턴 판이 **더 비쌌다**(6파일 vs 1파일). 미리 만든 팩토리 `create()`에 인자가 없어, "결제 수단"이라는 실제 축을 위해 `FeeCalculator`·`FeeService`의 시그니처를 층마다 고쳐야 했다. **예측한 축과 실제 축이 달랐다.** 단, 6파일에는 진입점 `Main.java`(2줄)가 들어 있다. plain은 main이 같은 파일 안에 있어 따로 세지 않았다. Main을 빼도 5파일이다.
- 관찰 3 — 축이 생긴 뒤의 변경 3은 둘 다 작았다(plain은 `enum` 상수 1 + `case` 1, pattern은 새 클래스 1 + 팩토리 한 줄 + 호출부 1).
- 관찰 4 — 같은 계산까지 호출 스택이 2단 깊었다(`getStackTrace().length` 3 vs 5, 이 값에는 `getStackTrace` 자신의 프레임이 들어 있다).
- 해석: 이 실험의 범위(한 저장소, 한 팀, 변형 4개)에서는 `enum` + 빠짐없는 `switch`로 충분했다. Strategy가 이득인 쪽은 **변형을 다른 모듈·팀·플러그인이 추가해서 중앙 `switch`를 고칠 수 없을 때**, 또는 변형마다 상태·연산이 여럿일 때다 — 이 실험은 그 경우를 재지 않았다.

### 3. 원본 우선순위표와의 연결

원본 「우선순위」표는 현장 최우선으로 State·Strategy·Adapter·Chain of Responsibility를 꼽는다. 그 넷 모두 **축이 실제로 존재하는 자리**(상태 전이 규칙, 수단별 계산, 외부 시스템 경계, 늘어나는 검증 규칙)에 붙어 있다. 실험 A와 같은 결론이다.

## 쓰이는 자료구조·알고리즘

패턴 안에는 자료구조가 들어 있고, 장애는 대개 그 자료구조의 성질에서 나온다.

### 1. Composite = 트리, 연산 = 재귀

```text
 전표(Group) debit = Σ 자식.debit
  ├─ 분개1(Line) 10,000
  └─ 하위전표(Group)
       ├─ 분개2 3,000
       └─ 분개3 2,000          합계 15,000
 실수로 하위전표.add(전표) → 트리가 아니라 순환 그래프 → 재귀가 끝나지 않음
```

### 2. Observer = 리스너 목록 순회

```text
 publish(e):  for l in listeners: l.accept(e)
   - 하나가 예외 → 뒤의 리스너는 안 불림
   - 순회 중 목록 변경(구독 해지) → ArrayList는 대개 ConcurrentModificationException
     (끝에서 두 번째 리스너가 해지하면 예외 없이 마지막 리스너를 건너뛴다)
   - 리스너가 느리면 → 호출한 스레드가 그만큼 막힘 (동기 호출)
```

### 3. State = 상태 기계(전이 표)

```text
 PENDING ──approve──> APPROVED ──capture──> CAPTURED
    └──decline──> DECLINED
 표에 없는 전이 = 예외 (enum 상수마다 허용 전이만 재정의, 기본은 거부)
```

### 실험 B: 세 자료구조가 깨지는 방식

(실험, JDK 21.0.12 temurin `--cpus=2`, Spring Framework 6.2.11, `scratchpad/sd/25/e27/src/Structures.java`, 2026-10-02)

```java
void publish(String e) { for (Consumer<String> l : ls) l.accept(e); }              // 격리 없음
void publishIsolated(String e) { for (Consumer<String> l : ls) try { l.accept(e); } catch (RuntimeException x) { ... } }
static long debit(Entry e) {
    return switch (e) { case Line l -> l.debit(); case Group g -> g.children.stream().mapToLong(Structures::debit).sum(); };
}
```

```text
[B1] 리스너 하나가 예외를 던지면
  ArrayList, 격리 없음
    리스너1 메일 발송 order#1
    publish 예외: IllegalStateException: 리스너2 포인트 적립 실패
  ArrayList, 리스너마다 try/catch
    리스너1 메일 발송 order#1
    (리스너 예외 격리: 리스너2 포인트 적립 실패)
    리스너3 정산 기록 order#1
[B2] 알림 도중 자기 구독 해지
  ArrayList
    1회용 리스너 order#2 → 구독 해지
    publish 예외: java.util.ConcurrentModificationException
  CopyOnWriteArrayList
    1회용 리스너 order#2 → 구독 해지
    리스너B order#2
    리스너C order#2
[B3] Spring 6.2.11 이벤트: 리스너2가 예외를 던지면
    리스너1 order#3
    publishEvent 예외: IllegalStateException: 리스너2 실패
[C] Composite 전표 트리
  차변 합계 = 15000
  순환 추가 후: StackOverflowError
[D] State 전이
  PENDING → approve → capture = CAPTURED
  approve not allowed in CAPTURED
```

- B1 — 격리 없는 Observer는 리스너2의 예외로 **리스너3(정산 기록)이 조용히 빠졌다.** 발행자는 예외를 받지만 "어느 리스너가 안 불렸나"는 모른다.
- B2 — 순회 중 구독 해지는 `ArrayList`에서 `ConcurrentModificationException`, `CopyOnWriteArrayList`는 순회 시점의 스냅샷을 돌아서 B·C까지 불렀다.
- B2 보충(점검 재실행, 같은 환경) — `ArrayList`라도 해지하는 리스너가 **끝에서 두 번째**(리스너 3개 중 두 번째)이면 예외가 없다. 해지 뒤 `hasNext()`가 `false`가 되어 루프가 끝나고, **마지막 리스너가 조용히 빠졌다**(출력: `리스너A` → `1회용(두 번째) … 구독 해지` → `예외 없음, 끝`). `ArrayList` 반복자의 fail-fast는 최선 노력(best-effort)이라 예외에 기대면 안 된다.
- B3 — Spring의 기본 이벤트 발행도 같았다. `SimpleApplicationEventMulticaster` javadoc: `ErrorHandler`가 기본으로 없어서 "리스너 예외가 현재 멀티캐스트를 멈추고 발행자에게 전파된다". 리스너는 기본으로 호출한 스레드에서 돈다.
- C — 순환이 들어간 Composite는 재귀가 끝나지 않아 `StackOverflowError`.
- D — 표에 없는 전이는 그 자리에서 예외. 잘못된 전이가 한 곳에서 막힌다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **변경 이력에서 축을 찾는다**: 같은 종류의 변경이 반복되는 파일을 본다.

```bash
git log --since=6.months --name-only --format= | sort | uniq -c | sort -rn | head
git log -S 'case CARD' --oneline          # 같은 분기에 case가 추가된 이력
```

2. **언어 기능부터**: `enum` + 빠짐없는 `switch`, `sealed` + 패턴 매칭, 람다.
3. **패턴은 두 번째 변형이 실제로 올 때**: 구현이 하나뿐인 인터페이스·인자 없는 팩토리는 만들지 않는다(12 simple-design-and-yagni).
4. **자료구조의 함정을 함께 막는다**:
   - Observer: 리스너마다 예외 격리, 순회 중 변경이 있으면 `CopyOnWriteArrayList`, 느린 리스너는 비동기로. Spring이면 `SimpleApplicationEventMulticaster.setErrorHandler` 또는 `@TransactionalEventListener(phase = AFTER_COMMIT)`(원본 19절)과 함께 생각한다.
   - Composite: `add` 때 조상인지 검사해 순환을 거부하거나, 불변 트리로 만든다.
   - State: 전이 표 밖은 예외. 상태가 추가되면 컴파일러가 빠진 곳을 알리도록 `switch` **식**(또는 패턴 `switch`)으로 쓰고 `default`를 두지 않는다. 전통적인 enum `switch` **문**은 `default`를 빼도 검사되지 않는다(JEP 441, 28 taming-conditionals).
5. **필요 없어진 패턴은 걷어낸다**: 구현이 하나로 줄어든 Strategy, 아무도 안 바꾸는 Factory는 인라인한다(29의 "패턴에서 멀어지기").

### 2. 패턴 과잉 진단

```bash
# 구현이 하나뿐인 인터페이스 후보 (예시: 이름 기반 근사)
for i in $(grep -rl '^public interface' src/main/java | xargs -n1 basename | sed 's/.java//'); do
  n=$(grep -rl "implements .*\b$i\b" src/main/java | wc -l); [ "$n" -le 1 ] && echo "$i 구현 $n개"; done
# 이름만 패턴인 클래스
find src/main/java -name '*Factory.java' -o -name '*Manager.java' -o -name '*Helper.java'
```

- `jdeps`·IDE 호출 계층으로 "호출부 → 실제 계산"까지 몇 단인지 본다. 실험 A에서 2단이 더 깊었다.

## 장애 시나리오와 대처

### 1. 패턴을 위한 패턴 → 간접 계층만 늘어남 (⚠ 커리큘럼)

- 현상: 요율 하나 바꾸는데 인터페이스·팩토리·계산기·서비스를 다 열어 본다. 실제 요구가 오면 미리 만든 구조가 안 맞아 층마다 시그니처를 고친다.
- 보이는 형태: 실험 A 변경 2 — 패턴 판 6파일(진입점 Main 포함)·19줄 추가 vs plain 1파일·10줄 추가. 스택 트레이스가 깊다(3 vs 5).
- 원인: 실제로 바뀐 적 없는 축을 예측해 상자를 만들었고, 실제 축은 다른 곳에서 왔다(Speculative Generality — 10 code-smells).
- 대처: 상자를 인라인해 단순한 형태로 되돌리고, 축이 두 번 확인되면 그 축에 맞는 패턴을 다시 꺼낸다(11 when-to-abstract의 "인라인 후 재추출").

### 2. Observer 리스너 하나의 실패가 나머지를 조용히 막는다

- 현상: 주문은 됐는데 정산 기록이 가끔 빠진다.
- 보이는 형태: 포인트 적립 리스너의 예외 로그만 있고 정산 리스너 로그는 없다(실험 B1·B3).
- 원인: 동기 순회에서 앞 리스너의 예외가 루프를 끊었다. Spring 기본 멀티캐스터도 같다.
- 대처: 리스너마다 예외 격리(`ErrorHandler`), 꼭 실행돼야 하는 후속 작업은 이벤트 대신 같은 트랜잭션의 outbox로([distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)).

### 3. 알림 중 구독 변경으로 `ConcurrentModificationException`

- 현상: "한 번만 듣는" 리스너를 넣은 뒤 가끔 발행이 실패한다.
- 보이는 형태: `java.util.ConcurrentModificationException`이 `publish` 루프에서(실험 B2). 해지한 리스너의 위치에 따라서는 예외 없이 뒤 리스너 하나가 빠지기만 한다(B2 보충).
- 원인: `ArrayList`를 순회하면서 같은 목록에서 `remove`.
- 대처: `CopyOnWriteArrayList`(쓰기가 드물고 읽기가 많을 때), 또는 해지 요청을 모았다가 순회 뒤 반영.

### 4. Composite에 순환이 들어가 `StackOverflowError`

- 현상: 메뉴·조직도·전표 트리 합계 API가 특정 데이터에서만 죽는다.
- 보이는 형태: `StackOverflowError`, 스택 트레이스에 같은 재귀 메서드가 수천 줄 반복(실험 C).
- 원인: 부모를 자손에 추가해 트리가 그래프가 됐다. DB의 `parent_id`로 트리를 재구성할 때도 데이터 오류로 생긴다.
- 대처: `add` 시점에 조상 검사, 재구성 시 방문 집합으로 순환 탐지(DFS 색칠 — [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)), DB에는 순환 금지 검증.

## 핵심 문장

- 패턴은 반복되는 설계 문제와 해법의 짝에 붙인 이름이고, 한 축의 변경을 싸게 하는 대신 간접 계층을 비용으로 낸다.
- 실험에서 미리 만든 Strategy·Factory는 규칙 수정에 도움이 없었고, 실제 축이 다르게 오자 6파일을 고쳐야 했다(plain은 1파일).
- 패턴을 고르기 전에 실제 변경 이력, 언어 기능(enum·sealed·람다), 프레임워크가 이미 하는 일을 먼저 본다.
- Observer의 동기 순회는 한 리스너의 예외로 나머지를 멈춘다. Spring 6.2.11 기본 이벤트 발행도 그랬다.
- Composite는 트리일 때만 재귀가 끝난다. 순환이 들어가면 `StackOverflowError`다.
- 『Refactoring to Patterns』의 저자는 Kerievsky다. 패턴은 리팩터링 끝에 도달하는 편이 축을 잘못 짚을 위험이 적다.

## 관련 주제·근거

- 원본(이어받음)
  - [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — 23개 패턴의 목적·주의·현장, 헷갈리는 쌍, Spring이 대신 해주는 것, 우선순위표
- 선행
  - [22-solid](../22-solid/2-summary.md) · 원본 [engineering/solid-principles](../../engineering/solid-principles/2-summary.md)
- 후속·연결
  - [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — 조건문 도구 선택, [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) — 리팩터링으로 패턴에 도달·걷어내기
  - [32-inversion-of-control-and-framework-flow](../32-inversion-of-control-and-framework-flow/2-summary.md)(Template Method), [33-aop-and-proxies](../33-aop-and-proxies/2-summary.md)(Proxy), [34-middleware-filter-interceptor-chains](../34-middleware-filter-interceptor-chains/2-summary.md)(CoR), [11-when-to-abstract](../11-when-to-abstract/2-summary.md), [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md)
  - [30 pattern-languages-and-catalogs](../30-pattern-languages-and-catalogs/2-summary.md), [31 antipatterns](../31-antipatterns/2-summary.md), [10 code-smells](../10-code-smells/2-summary.md)
  - [26-functional-core-imperative-shell](../26-functional-core-imperative-shell/2-summary.md) — Command를 값으로 반환
- 글·문서
  - Gamma, Helm, Johnson, Vlissides, 『Design Patterns: Elements of Reusable Object-Oriented Software』, Addison-Wesley 1994, 395쪽 — 1장 두 원칙 인용 위치는 Wikipedia 문서 기준 <https://en.wikipedia.org/wiki/Design_Patterns>
  - Joshua Kerievsky, 『Refactoring to Patterns』(Addison-Wesley, 2004) — 카탈로그 27개 리팩터링 <https://www.industriallogic.com/xp/refactoring/catalog.html> · Fowler의 소개 글 <https://martinfowler.com/books/r2p.html>
  - Spring Framework `SimpleApplicationEventMulticaster` javadoc(`setErrorHandler`: 기본 없음, 예외가 멀티캐스트를 멈추고 전파) <https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/context/event/SimpleApplicationEventMulticaster.html>
- 실험 목록 (코드: scratchpad `sd/25/e27/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - A `build.sh`(git 저장소 생성·커밋 4개) → `measure.sh`(git diff --shortstat/--stat) → `run.sh`(커밋마다 컴파일·실행, 스택 깊이) — plain vs 패턴 판, 변경 3개
  - B `src/Structures.java` — Observer 예외·구독 해지(ArrayList vs CopyOnWriteArrayList), Spring 6.2.11 이벤트 예외 전파, Composite 순환, State 전이 거부
