# software-design/54-designing-for-deletion — 지우기 쉬운 코드: 교체·죽은 코드·플래그 걷어내기·deprecate — 정리 (힌트)

## 해결하는 문제

코드는 쓰는 순간부터 유지보수 비용이 든다. 그런데 지우는 일은 쓰는 일보다 어렵게 설계되는 경우가 많다.

```text
 확장하기 쉽게 만든 코드                         지우기 쉽게 만든 코드
 공통 라이브러리 하나에 여러 쓰임새를 얹는다         쓰임새마다 따로, 결합 지점은 하나
        │                                           │
 요구 하나를 빼려면 → 공통부의 분기를 풀고            요구 하나를 빼려면 → 그 단위를 통째로 지운다
                    호출자 전부를 확인
```

- *지우기 쉬운 코드(easy to delete)*: 다른 부분을 다시 쓰지 않고 떼어 낼 수 있는 코드. tef(programmingisterrible.com)의 2016-02-13 글 "Write code that is easy to delete, not easy to extend"의 주장이다.
- *죽은 코드(dead code)*: 실행 경로에서 더 이상 닿지 않는 코드. 남아 있으면 읽고, 고치고, 테스트하는 비용만 든다.

tef는 Dijkstra(EWD 1036)를 인용해 코드 줄을 "생산한 줄"이 아니라 "쓴(지출한) 줄"로 보자고 한다. 그러면 코드를 지우는 것이 유지보수 비용을 낮추는 일이 된다.

쉬운 예: 레고로 만든 성은 탑 하나를 빼도 나머지가 서 있다. 접착제로 붙인 모형은 탑 하나를 떼려면 성벽이 같이 부서진다.\
똑같은 구조다.\
실무 예: 실험이 끝난 결제 화면 A/B 플래그를 지운다. 분기가 다섯 파일에 흩어져 있으면 다섯 파일을 고쳐야 하고, 하나를 빠뜨리면 옛 화면이 살아 있다. 분기가 팩토리 한 곳에 있으면 그 한 곳과 옛 구현 클래스만 지운다.

## 동작·원리

### 1. 지우기 쉬움과 결합

```text
  결합 높음                               결합 낮음(교체 단위가 분명)
  ┌─────┐  ┌─────┐  ┌─────┐              ┌─────┐  ┌─────┐  ┌─────┐
  │  A  │──│  B  │──│  C  │              │  A  │  │  B  │  │  C  │
  └──┬──┘  └──┬──┘  └──┬──┘              └──┬──┘  └──┬──┘  └──┬──┘
     └──공유 util·전역 상태──┘                 └── 좁은 인터페이스 하나 ──┘
  B를 지우면 A·C·util이 같이 흔들린다       B를 지우면 B와 B를 꽂는 한 줄만
```

- 그림은 이 노트의 해석이다: 결합 지점이 적을수록 떼어 내기 쉽다. tef는 느슨한 결합이 지우기 쉬움을 **보장하지는 않는다**고 적고(아래 마지막 항목), 코드 양·공유 API로 굳은 동작 같은 다른 요인도 든다.

tef 글의 주장 몇 개를 그대로 옮긴다(저자 주장).
- 의존을 **만들지 않으려고** 반복하라. 그러나 의존을 **관리하려고** 반복하지는 마라("repeat yourself to avoid creating dependencies, but don't repeat yourself to manage them").
- 공유 API로 만들면 바꾸기 어려워진다. 호출자는 문서가 아니라 관찰한 동작에 기댄다. "함수 안의 코드를 지우는 것이 함수를 지우는 것보다 쉽다."
- 어렵거나 바뀔 가능성이 큰 부분을 나머지와, 그리고 서로와 떼어 놓는다(Parnas 1972 인용: 어렵거나 바뀔 법한 설계 결정을 모듈마다 하나씩 숨긴다).
- "모듈 하나가 어려운 문제 하나만"보다 "어려운 문제 하나는 모듈 하나에서만" 다루는 것이 더 중요하다.
- 느슨한 결합은 "코드를 많이 바꾸지 않고 마음을 바꿀 수 있는 것"이다. 결합이 느슨한 코드는 지우기 쉽다고 보장되지는 않지만, 교체·변경은 훨씬 쉽다.

- *확장보다 교체*: 기존 단위에 옵션을 계속 더하는 대신, 같은 인터페이스의 새 단위를 만들고 옛 단위를 지운다. 50의 branch by abstraction이 이 모양이다.

### 2. 죽은 코드 찾기 = 루트에서의 도달성

```text
 루트(main·HTTP 핸들러·스케줄러·리스너)
     │
     v
  App ──> OrderService ──> PriceCalc          ← 도달
  OldPriceCalc ──> RoundingHelper             ← 루트에서 안 닿음 = 죽은 코드 후보
  LegacyCsvExporter                           ← 정적 간선 없음. 그러나 Class.forName("...")로 실행 시 적재된다
```

- *도달성(reachability)*: 루트 집합에서 호출·참조 간선을 따라 닿는 노드 집합. 닿지 않는 노드가 죽은 코드 **후보**다.
- 정적 분석의 한계: 리플렉션·설정 문자열·DI 컨테이너·직렬화 프레임워크·외부 호출(다른 서비스·배치)은 간선을 남기지 않는다. 그래서 정적 후보는 **실행 시 관측**(호출 로그·클래스 적재 로그·엔드포인트 지표)으로 확인한 뒤 지운다.

### 실험 F1: jdeps 도달성 vs 실행 시 클래스 적재 (Java)

`shop.App`이 `OrderService → PriceCalc`를 쓰고, `LegacyCsvExporter`는 시스템 속성 문자열로 `Class.forName` 한다. `OldPriceCalc → RoundingHelper`는 아무도 안 부른다.

```java
// App.main
System.out.println(new OrderService().total(3, 1000));
String exporter = System.getProperty("exporter", "shop.LegacyCsvExporter");
Object e = Class.forName(exporter).getDeclaredConstructor().newInstance();   // 정적 간선 없음
```

```java
// Reach.java — jdeps -verbose:class 출력에서 shop.* 간선만 뽑아 BFS
Pattern edge = Pattern.compile("^\\s+(shop\\.\\S+)\\s+->\\s+(shop\\.\\S+)");
Deque<String> q = new ArrayDeque<>(List.of(root)); Set<String> seen = new TreeSet<>(q);
while (!q.isEmpty()) for (String n : g.getOrDefault(q.poll(), Set.of())) if (seen.add(n)) q.add(n);
```

(실험, JDK 21.0.12 temurin `jdeps`·`java`, Docker `--cpus=2`, 2026-10-02, `scratchpad/sd/50/e54/`)

```text
$ jdeps -verbose:class out  (기본 -filter:package)
0
  루트 shop.App에서 도달: [shop.App]
  도달 불가(죽은 코드 후보): [shop.LegacyCsvExporter, shop.OldPriceCalc, shop.OrderService, shop.PriceCalc, shop.RoundingHelper]
```

```text
$ jdeps -verbose:class -filter:none out | grep "-> shop"
   shop.App                                           -> shop.OrderService                                  out
   shop.OldPriceCalc                                  -> shop.RoundingHelper                                out
   shop.OrderService                                  -> shop.PriceCalc                                     out
== 정적 도달성
  루트 shop.App에서 도달: [shop.App, shop.OrderService, shop.PriceCalc]
  도달 불가(죽은 코드 후보): [shop.LegacyCsvExporter, shop.OldPriceCalc, shop.RoundingHelper]
== 실행 시 실제로 적재된 shop 클래스 (-Xlog:class+load)
shop.App
shop.LegacyCsvExporter
shop.OrderService
shop.PriceCalc
```

- 관찰 1 — `jdeps` 기본값(`-filter:package`, `jdeps --help`: "Filter dependences within the same package. This is the default.")은 같은 패키지 간선을 숨긴다. 그대로 쓰면 간선 0개라 거의 전부가 "죽은 코드"로 나온다. `-filter:none`을 줘야 했다.
- 관찰 2 — 정적 후보는 셋이었다. 실행 로그에는 그중 `LegacyCsvExporter`가 적재됐다(리플렉션). 진짜 죽은 것은 `OldPriceCalc`·`RoundingHelper` 둘이다. `RoundingHelper`는 죽은 코드만 부르는 "전이적으로 죽은" 코드다.

정적 후보 셋을 그대로 지우면:

```text
$ (정적 분석의 죽은 코드 후보 3개를 지우고 빌드) javac 종료코드 0
3000
Exception in thread "main" java.lang.ClassNotFoundException: shop.LegacyCsvExporter
	at java.base/jdk.internal.loader.BuiltinClassLoader.loadClass(BuiltinClassLoader.java:641)
	… (이 노트에서 줄임: 스택 프레임 5줄)
	at shop.App.main(App.java:7)
exit=1
```

- 관찰 3 — 컴파일은 통과하고 실행 시점에 `ClassNotFoundException`이 났다. 정적 분석만 믿은 삭제의 전형적인 실패다.

### 3. 플래그 분기 걷어내기 — 결정 지점의 수가 제거 비용을 정한다

```text
 흩어진 분기(scattered)                      결정 지점 하나(central)
 CartStep:    if (flag) new else old         CheckoutFactory: flag ? new NewCheckout() : new OldCheckout()
 OrderStep:   if (flag) new else old         CartStep·OrderStep·...: c.run(...)   ← 플래그를 모른다
 PaymentStep: if (flag) new else old
 ReceiptStep: if (flag) new else old
 MailStep:    if (flag) new else old
```

- Hodgson("Feature Toggles", 글에 적힌 날짜 2017-10-09)은 *토글 지점(toggle point)*과 *토글 라우터(toggle router)*를 나누고, 결정 지점과 결정 로직을 떼어 놓으라고 한다(「De-coupling decision points from decision logic」·「Inversion of Decision」 절).

### 실험 F2: 플래그 제거 커밋 크기와 "설정만 지웠을 때"

```java
// scattered: 다섯 파일이 각각
if (Flags.on("new-checkout")) { return "Cart:new"; } else { return "Cart:old"; }
static boolean on(String k) { return conf.getOrDefault(k, false); }   // 없는 플래그 = false

// central: 팩토리 한 곳
static Checkout create() { return conf.getOrDefault("new-checkout", false) ? new NewCheckout() : new OldCheckout(); }
```

(실험, git 2.43.0 + JDK 21.0.12, `--cpus=2`, 2026-10-02, `scratchpad/sd/50/e54/flags.sh`로 처음 구조를 만들고, 제거 커밋은 그 저장소에서 손으로 편집해 커밋)

```text
== scattered 처음 구조(플래그 도입 시점)
 7 files changed, 54 insertions(+)
== central 처음 구조(플래그 도입 시점)
 9 files changed, 33 insertions(+)
== scattered 제거 커밋
 src/CartStep.java    | 6 +-----
 src/Flags.java       | 2 +-
 src/MailStep.java    | 6 +-----
 src/OrderStep.java   | 6 +-----
 src/PaymentStep.java | 6 +-----
 src/ReceiptStep.java | 6 +-----
 6 files changed, 6 insertions(+), 26 deletions(-)
== central 제거 커밋
 src/CheckoutFactory.java | 4 +---
 src/OldCheckout.java     | 1 -
 2 files changed, 1 insertion(+), 4 deletions(-)
```

```text
== 설정에서만 플래그를 지우면(코드는 그대로) — scattered
플래그 있음: Cart:new Order:new Payment:new Receipt:new Mail:new
플래그 설정 삭제: Cart:old Order:old Payment:old Receipt:old Mail:old
```

- 관찰 1 — 제거 커밋은 scattered 6파일, central 2파일(그중 1개는 파일 삭제)이었다.
- 관찰 2 — central은 처음에 파일이 더 많았다(9 대 7, scattered 쪽 7에는 실험용 `Main` 1개 포함). 인터페이스·구현 클래스가 늘어난 값이다. 이 예에서는 분기 중복이 없어 줄 수는 central이 더 적었다(33 대 54). 분기가 한두 곳뿐이면 central 구조가 오히려 과할 수 있다(12 simple-design-and-yagni).
- 관찰 3 — 설정에서 플래그 항목만 지우자 "없는 플래그 = false" 기본값 때문에 다섯 곳이 전부 **옛 경로로 돌아갔다**. 에러는 없다. 다 쓴 플래그의 `else` 분기가 살아 있는 한, 설정 한 줄로 되살아난다.

### 4. 주석 처리 코드 대신 git

- 주석 처리한 코드는 읽는 사람이 "살아 있나?"를 매번 판단하게 만든다. 컴파일·테스트도 안 거친다. 지운 코드는 git이 기억한다.

(실험 F2 저장소, 해시는 실행마다 다르다)

```text
$ git log -S':old"' --format='%h %s'
f189a7e remove flag new-checkout
2d9d109 base
```

- `git log -S<문자열>`(pickaxe)은 그 문자열의 등장 횟수가 바뀐 커밋을 찾는다. 지운 커밋과 처음 넣은 커밋이 나온다. `git show <hash>~1:<path>`로 지우기 전 내용을 본다.

### 5. 내부 API deprecate 절차

```text
 ① 대체 경로 제공 → ② @Deprecated(forRemoval=true) + 문서 → ③ 호출 수 측정(컴파일 경고·런타임 카운터)
 → ④ 호출자 이전(51 parallel change의 migrate) → ⑤ 0 유지 확인 → ⑥ 삭제
```

- JEP 277(Enhanced Deprecation, JDK 9): `@Deprecated`에 `forRemoval`(앞으로 제거 예정이면 true)과 `since`가 생겼다. 제거 예정 API 사용에는 "removal warning"이 나간다.
- JEP 277: `@SuppressWarnings("deprecation")`은 removal 경고를 끄지 않는다. 일반 deprecation 경고를 꺼 둔 호출처에서도 제거 예정 경고가 다시 보이게 하려는 설계다.

### 실험 F3: 제거 예정 API를 새 코드가 다시 부름

```java
class LegacyApi {
    /** @deprecated 2026-12 제거 예정. 대신 {@link NewApi#send(String)}. */
    @Deprecated(since = "2.3", forRemoval = true)
    static void sendOld(String s) { NewApi.send(s); }
}
class NewFeature { void go() { LegacyApi.sendOld("x"); } }   // "혹시 몰라" 남겨 둔 API를 새 코드가 부른다
```

(실험, JDK 21.0.12 `javac`, 2026-10-02)

```text
$ javac Dep.java
Dep.java:8: warning: [removal] sendOld(String) in LegacyApi has been deprecated and marked for removal
    void go() { LegacyApi.sendOld("x"); }
                         ^
1 warning
exit=0
$ javac -Werror Dep.java
Dep.java:8: warning: [removal] sendOld(String) in LegacyApi has been deprecated and marked for removal
    void go() { LegacyApi.sendOld("x"); }
                         ^
error: warnings found and -Werror specified
1 error
1 warning
exit=1
```

- 관찰 — `forRemoval` 경고는 옵션 없이 나왔지만 빌드는 성공했다(exit 0). 경고만으로는 새 호출을 막지 못한다. `-Werror`(또는 빌드 도구의 "경고를 오류로" 설정)를 걸어야 CI가 막는다.

## 쓰이는 자료구조·알고리즘

- **호출·참조 그래프 + BFS 도달성** — 루트에서 안 닿는 노드 = 죽은 코드 후보(실험 F1). 그래프는 `jdeps -verbose:class -filter:none` 같은 도구로 뽑는다. 순환 참조만 있는 죽은 덩어리(A↔B)도 루트에서 안 닿으면 함께 잡힌다 — 참조 수 세기가 아니라 도달성이라서다.
- **실행 시 관측 집합** — 클래스 적재 로그(`-Xlog:class+load`), 엔드포인트별 호출 카운터. 정적 그래프에 없는 간선(리플렉션·DI)을 보충한다.
- **토글 라우터 + 전략** — 결정을 한 곳에서 내리고 결과를 전략 객체로 넘긴다(실험 F2 central). 제거 비용이 결정 지점 수에 비례한다.
- **텍스트 검색(pickaxe)** — `git log -S`는 커밋마다 문자열 등장 횟수 변화를 본다.

## 적용 — 풀어나가는 법

### 1. 만들 때 — 지울 날을 같이 설계한다

1. **결합 단위를 작게.** 기능·실험·통합 대상마다 진입점 하나(팩토리·라우터·어댑터)를 둔다. 공용 `util`에 업무 규칙을 넣지 않는다(tef: util 파일 하나는 결국 너무 커지고 쪼개기 어려워진다).
2. **플래그는 수명과 함께.** Hodgson의 실천: 릴리스 토글을 만들 때 제거 작업을 백로그에 같이 넣는다, 만료일을 붙인다, 만료가 지나면 테스트를 실패시키는 "시한폭탄", 동시에 둘 수 있는 플래그 수 상한.
3. **"없는 플래그"의 기본값을 정한다.** 실험 F2처럼 기본값이 옛 경로면, 설정만 지웠을 때 옛 코드가 살아난다. 다 쓴 플래그는 설정보다 코드를 먼저 지운다.

### 2. 지울 때 — 순서

1. **후보 찾기**: 정적 도달성(`jdeps -filter:none`, IDE "unused", 언어별 도구) + 커버리지(운영 트래픽 기준이면 더 좋다).
2. **실행 시 확인**: 호출 카운터·로그를 붙이고 충분한 기간(월말·분기 배치를 덮을 만큼) 0을 확인한다. 리플렉션·설정 문자열을 `grep`한다.

```bash
grep -rn "LegacyCsvExporter" src/ conf/ *.yml *.properties   # 문자열로 참조되는 곳
```

3. **삭제는 작은 커밋으로.** 지운 이유와 확인 근거(기간·지표)를 커밋 메시지에 남긴다. 되살릴 일이 있으면 `git revert`.
4. **전이적으로 죽은 것까지.** 지운 뒤 다시 도달성을 돌린다(실험 F1의 `RoundingHelper`).

### 3. 진단 지표

- 죽은 코드 비율: (정적 도달 불가 클래스 수) / (전체) — 추세로 본다.
- 플래그 재고: 코드에 남은 플래그 키 수와 각 키의 나이(`git log -S'"new-checkout"' --format=%ad | tail -1`로 처음 들어온 날).
- 제거 예정 API 호출 수: `javac` `[removal]` 경고 수.

## 장애 시나리오와 대처

### 1. 호출처 없는 코드 30%가 남아 리팩터링 때마다 같이 고침 (⚠ 커리큘럼)

- 현상: 시그니처를 바꾸면 쓰이지도 않는 클래스까지 고쳐야 컴파일된다. 리뷰 시간의 일부가 죽은 코드 읽기에 쓰인다.
- 보이는 형태: 정적 도달성 분석에서 후보 30%(예시). 그 파일들의 최근 커밋은 전부 "컴파일 맞추기" 수정.
- 원인: 기능을 끌 때 코드를 지우지 않았다. 지워도 되는지 확인할 수단(호출 로그)이 없었다.
- 대처: 도달성 후보 → 실행 시 확인 → 작은 삭제 커밋. 앞으로는 기능 종료 작업에 "코드 삭제"를 포함한다.

### 2. 끝난 실험 플래그의 `else` 분기가 몇 년 뒤 재활성 (⚠ 커리큘럼, Knight Capital 유형)

- 현상: 설정 변경·플래그 재사용 뒤 오래된 동작이 운영에서 다시 돈다.
- 보이는 형태: 실험 F2 — 플래그 설정만 지우자 다섯 곳이 전부 `:old`로 돌아갔다. 에러·경고 없음.
- 원인: 플래그 수명이 끝났는데 분기 코드가 남았다. "없는 플래그"의 기본값이 옛 경로였다. 실제 사례로 Knight Capital(2012)은 옛 Power Peg 기능용 플래그를 새 기능에 재사용했고, 새 코드가 배포되지 않은 서버 1대에서 그 플래그가 옛 코드를 켰다(세부와 출처는 [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md)).
- 대처: 플래그를 100%로 고정했으면 분기 코드부터 지운다(실험 F2 제거 커밋). 플래그 키를 재사용하지 않는다. 만료일·시한폭탄 테스트로 남은 플래그를 드러낸다.

### 3. "혹시 몰라" 남긴 구 API를 신규 코드가 다시 호출 (⚠ 커리큘럼)

- 현상: 지우려던 API의 호출 수가 0에서 다시 늘었다. 신규 기능이 그것을 쓰고 있다.
- 보이는 형태: 실험 F3 — `[removal]` 경고는 나오지만 `exit=0`으로 빌드 성공.
- 원인: 제거 예정 표시가 경고에 그쳤다. 대체 API가 문서에 없었다.
- 대처: `@Deprecated(forRemoval = true)` + 대체 API 링크(`{@link}`) + CI에서 removal 경고를 오류로(`-Werror` 등). 런타임 호출 카운터를 두고 0 유지 기간이 지나면 지운다.

### 4. 정적 분석만 믿고 지웠다가 실행 시 실패

- 현상: 배포 후 특정 설정(내보내기 형식 선택)에서만 장애.
- 보이는 형태: 실험 F1 — 컴파일 성공, 실행 시 `ClassNotFoundException: shop.LegacyCsvExporter`.
- 원인: 리플렉션·설정 문자열·DI는 정적 간선을 남기지 않는다. 도구 기본값(`jdeps -filter:package`)이 같은 패키지 간선을 숨긴 것도 오판을 키운다.
- 대처: 정적 후보는 실행 시 관측(`-Xlog:class+load`, 호출 카운터)과 문자열 검색으로 확인한 뒤 지운다. 지울 때 해당 설정 값 검증(시작 시 `Class.forName` 실패를 빠르게 드러내기)도 같이 넣는다.

### 5. 주석 처리한 코드가 쌓임

- 현상: 파일 절반이 `//`로 막힌 옛 구현이다. 어느 것이 최신인지 헷갈린다.
- 보이는 형태: 주석 블록 안의 코드가 지금 API와 맞지 않는다(컴파일을 안 거쳐 낡았다).
- 원인: "나중에 필요할지 몰라서". 이력에서 찾는 법을 모른다.
- 대처: 지운다. 필요하면 `git log -S'<그 코드의 문자열>'`로 찾아 `git show <hash>~1:<path>`로 본다.

## 핵심 문장

- tef의 주장: 확장하기 쉬운 코드가 아니라 지우기 쉬운 코드를 쓰라. 이 노트의 요약으로는, 지우기 쉬움은 결합 지점의 수에 크게 좌우된다.
- 죽은 코드는 루트에서의 도달성으로 찾는다. 정적 후보는 리플렉션·설정 때문에 실행 시 관측으로 확인한 뒤 지운다. 실험에서 정적 후보 셋 중 하나는 실행 시 적재되는 클래스였다.
- 도구 기본값을 확인한다. `jdeps`는 기본으로 같은 패키지 간선을 숨겨, 그대로 쓰면 간선 0개였다.
- 플래그 분기가 흩어져 있으면 제거 커밋이 커진다(실험 6파일 대 2파일). 다 쓴 플래그의 `else`는 설정 한 줄로 되살아난다.
- 제거 예정 표시는 경고일 뿐이다. 대체 경로·호출 측정·CI 게이트까지 갖춰야 deprecate가 삭제로 끝난다.

## 관련 주제·근거

- 선행
  - [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) — 확장점은 두 번째 요구가 올 때
  - [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md) — 경계를 테스트로 강제(지울 단위의 경계 유지)
- 후속·연결
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 플래그 유형·제거 부채·Knight Capital
  - [50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md) — 이전의 마지막 단계는 구 경로 삭제
  - [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md) — parallel change의 contract
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 오래 안 바뀐 코드 찾기(죽은 코드인지는 따로 확인)
- 글·문서
  - tef, "Write code that is easy to delete, not easy to extend.", programmingisterrible.com, 2016-02-13 <https://programmingisterrible.com/post/139222674273/how-to-write-disposable-code-in-large-systems>
  - Pete Hodgson, "Feature Toggles (aka Feature Flags)", martinfowler.com, 2017-10-09(글에 적힌 날짜) — 「Managing the carrying cost of Feature Toggles」(제거 작업·만료일·시한폭탄·개수 상한), 토글 지점·라우터 <https://martinfowler.com/articles/feature-toggles.html>
  - JEP 277: Enhanced Deprecation (JDK 9) — `forRemoval`·`since`, removal warning, `@SuppressWarnings("deprecation")`과의 관계 <https://openjdk.org/jeps/277>
  - `jdeps --help`(JDK 21.0.12) — `-filter:package`가 기본, `-filter:none`
- 실험 목록 (`scratchpad/sd/50/e54/`, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0)
  - F1 — jdeps 정적 도달성(기본 필터 vs `-filter:none`) vs `-Xlog:class+load`, 정적 후보 삭제 시 `ClassNotFoundException`. `shop/src/shop/*.java`, `Reach.java`, 출력 `reach-default.out`·`reach.out`·`delete-reflect.out`.
  - F2 — 플래그 제거 커밋 크기(scattered vs central), 설정만 지웠을 때 옛 경로 재활성, `git log -S`. `flags.sh`(처음 구조만 만든다. 제거 커밋은 손 편집 — `scattered/`·`central/` 저장소의 HEAD 커밋), 출력 `flags-diff.out`·`flags-revive.out`·`gitlogS.out`.
  - F3 — `@Deprecated(forRemoval = true)` 경고와 `-Werror`. `dep/Dep.java`, 출력 `deprecate.out`.
