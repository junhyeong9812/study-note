# software-design/02-modularity-coupling-cohesion — 모듈성: 정보 은닉·결합도·응집도 — 정리 (힌트)

## 해결하는 문제

01에서 본 복잡도의 첫 원인은 의존이었다.\
의존은 없앨 수 없다. 모듈이 서로를 쓰지 않으면 시스템이 아니다.\
그래서 질문이 바뀐다. **모듈 사이로 무엇이 흐르게 할까, 모듈 안에는 무엇을 모을까.**

```text
 모듈성이 없을 때                          모듈성이 있을 때
 ┌────────────────────────────┐          ┌──────┐   좁은 인터페이스   ┌──────┐
 │ 모두가 모두의 내부를 안다     │          │  A   │ ───────────────> │  B   │
 │ 내부 표현 하나 바뀌면 전부 수정│          │(내부)│   "무엇"만 오간다   │(내부)│
 └────────────────────────────┘          └──────┘                  └──────┘
                                           B의 "어떻게"가 바뀌어도 A는 그대로
```

- *모듈(module)*: 인터페이스와 구현으로 나뉜 코드 단위. 클래스·패키지·서비스 모두 모듈일 수 있다. Parnas(1972)는 모듈을 서브프로그램이 아니라 **책임 할당(responsibility assignment)** 으로 본다.
- *인터페이스(interface)*: 다른 모듈이 이 모듈을 올바르게 쓰려고 알아야 하는 모든 것. 메서드 시그니처(형식)뿐 아니라 "호출 순서", "반환 리스트를 수정하면 안 됨" 같은 비형식 약속도 포함한다(APOSD 4장, 독자 노트로 확인).

쉬운 예: 콘센트다. 가전제품은 전압과 플러그 모양(인터페이스)만 안다. 발전소가 석탄에서 태양광으로 바뀌어도(구현) 가전은 그대로다.\
똑같은 구조다.\
실무 예: 장바구니 모듈이 내부 저장 형식(`int[]{상품ID, 수량, 단가}`)을 그대로 내보내면, "같은 상품은 한 줄로 합치기" 요구 하나에 가격 계산·재고·영수증·프로모션 모듈이 함께 깨진다(아래 실험).

## 동작·원리

### 1. 정보 은닉 — 모듈은 결정 하나를 숨긴다

```text
          ┌──────────── Cart ────────────┐
 호출자 ──>│ 인터페이스: add, lines()→Line │  ← 바뀌기 어렵다(약속)
          │------------------------------│
          │ 숨긴 결정: 저장을 List로 할지  │  ← 바뀌기 쉽다(비밀)
          │           Map으로 할지        │
          │           같은 상품을 합칠지   │
          └──────────────────────────────┘
```

- *정보 은닉(information hiding)*: 바뀔 가능성이 있는 설계 결정을 한 모듈 안에 넣고, 인터페이스에는 드러내지 않는 것. Parnas 1972 원문: 두 번째 분해의 모든 모듈은 "its knowledge of a design decision which it hides from all others"로 특징지어지고, 인터페이스는 "to reveal as little as possible about its inner workings"로 골랐다.
- *정보 누출(information leakage)*: 한 설계 결정이 여러 모듈에 드러나는 것. 그 결정이 바뀌면 그것이 드러난 모듈들이 함께 바뀐다(APOSD 5장, 독자 노트로 확인).
- 누출은 두 길로 일어난다.
  - 인터페이스로 샌다: 내부 자료구조를 반환값·인자로 그대로 내보낸다.
  - 인터페이스 밖으로 샌다: 두 모듈이 같은 파일 형식·같은 숫자 의미를 각자 안다(01의 세율, 05의 connascence).
- 무엇을 숨길지 고르는 **기준**(바뀔 결정을 숨긴다, 처리 단계로 나누지 않는다)은 04 decompose-by-change에서 KWIC 예로 깊게 다룬다.

### 2. 결합도 — 모듈 사이로 무엇이 흐르나

```text
 강함 ──────────────────────────────────────────────────────> 약함
 내용 결합   공통 결합   외부 결합   제어 결합   스탬프 결합   자료 결합
 남의 내부   전역 변수   외부 형식   "무엇을 할지" 구조체 통째   필요한 값만
 코드·필드   공유       ·프로토콜   플래그 전달   전달(일부만 씀) 인자로
```

- *결합도(coupling)*: 한 모듈에서 다른 모듈로 이어진 연결이 만드는 연관의 강도. Stevens·Myers·Constantine(1974)의 정의로 인용되는 문구는 "the measure of the strength of association established by a connection from one module to another"다(원문 미열람, 인용 2차 출처로 확인).
- 위 단계 이름은 구조적 설계 전통의 분류다. 단계 목록은 Wikipedia "Coupling (computer programming)"로 확인했고, 각 단계가 1974 논문과 1979 Yourdon·Constantine 책 중 어디서 처음 나왔는지는 확인하지 못했다 [?].
- 핵심은 순서다. 오른쪽으로 갈수록 상대의 "어떻게"를 덜 안다.
- 결합의 개수(간선 수)와 **폭**(간선으로 무엇이 흐르나)은 다르다. 아래 실험에서 두 설계의 간선 수는 거의 같은데 변경 비용은 크게 달랐다.

### 3. 응집도 — 모듈 안에 무엇이 모였나

```text
 약함 ───────────────────────────────────────────────────────> 강함
 우연적   논리적    시간적    절차적    통신적     순차적     기능적
 Utils    "입력류"  "시작할 때" 순서대로  같은 데이터  앞 출력=   한 가지 일에
 잡동사니  묶음     하는 일    하는 일    를 다룸     뒤 입력    모두 기여
```

- *응집도(cohesion)*: 모듈 안 요소들이 함께 속하는 정도. 구조적 설계 전통의 분류이고, Wikipedia "Cohesion (computer science)"는 Stevens 외(1974)·Yourdon·Constantine(1979)을 출처로 든다(원문 미열람).
- 같은 문서에 따르면 이 순서는 서열 척도일 뿐 고르게 좋아지는 단계가 아니다. 앞의 두 가지(우연적·논리적)는 나쁘고, 통신적·순차적은 매우 좋고, 기능적이 가장 좋다는 연구를 인용한다.
- 위 척도는 응집을 "요소들이 어떤 관계로 묶였나"로 정의한다. "변경 이유의 수"로 정의하지 않는다.
- 실무 판별(다른 계열의 휴리스틱): "이 모듈을 바꾸게 만드는 이유가 몇 개인가". 이유가 여럿이면 응집이 약할 가능성이 크다. 이 질문은 Martin의 SRP(22 solid)에서 온 것이다.
- 두 기준이 늘 같은 답을 주지는 않는다. 통신적 응집(같은 데이터를 다루는 여러 일)은 척도상 "매우 좋음"이지만 바꿀 이유는 둘 이상일 수 있다.

### 4. 결합과 응집은 짝이다

```text
 응집 약함 + 결합 강함            응집 강함 + 결합 약함
 ┌──┐┌──┐┌──┐                   ┌──────┐     ┌──────┐
 │a1││b1││c1│  한 변경이          │ a1 a2│ ──> │ b1 b2│
 │b2││c2││a2│  모든 상자를 지난다   │ a3   │     │      │
 └──┘└──┘└──┘                   └──────┘     └──────┘
                                 함께 바뀌는 것이 한 상자에
```

- 함께 바뀌는 것을 한 모듈에 모으면(응집↑), 모듈 사이로 흐를 것이 줄어든다(결합↓).
- APOSD 5장은 클래스를 조금 **크게** 만들어 정보 은닉이 좋아지는 경우가 많다고 쓴다(독자 노트로 확인). 작게 쪼갤수록 좋다는 말이 아니다(03).

### 실험: 내부 표현 변경 — 표현을 내보낸 설계 vs 숨긴 설계

설계 A의 `Cart`는 내부 리스트 `List<int[]>`를 그대로 반환한다. 설계 B는 같은 저장을 하되 불변 값 `Line`의 복사본을 반환한다. 호출자는 가격 계산·재고·영수증·프로모션·분석 5개다.

```java
// 설계 A — 내부 표현을 내보낸다
public class Cart {
    private final List<int[]> lines = new ArrayList<>();          // {상품ID, 수량, 단가}
    public List<int[]> lines() { return lines; }                  // 내부 리스트 그 자체
}
class PromotionRule {   // 3개 이상이면 사은품 999를 끼운다 — 내부 리스트에 직접 쓴다
    static void apply(Cart c) { for (int[] l : c.lines()) if (l[1] >= 3) { c.lines().add(new int[]{999, 1, 0}); return; } }
}

// 설계 B — 저장은 숨기고 값만 내보낸다
public class Cart {
    public record Line(int productId, int qty, int unitPrice) {}
    private final List<int[]> lines = new ArrayList<>();
    public List<Line> lines() { /* int[] → Line 변환 */ return List.copyOf(r); }
}
class PromotionRule {   // 쓰기는 Cart의 공개 연산으로만
    static void apply(Cart c) { for (Cart.Line l : c.lines()) if (l.qty() >= 3) { c.add(999, 1, 0); return; } }
}
```

먼저 도구로 두 설계를 봤다.

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 2026-10-02 — `jdeps -verbose:class -filter:none`으로 `-> cart.Cart` 간선 수, `javap -public`)

```text
## a base
edges into Cart: 6
  public java.util.List<int[]> lines();
## b base
edges into Cart: 7
  public java.util.List<cart.Cart$Line> lines();
```

- 간선 수는 A 6개, B 7개다. B의 하나는 `Cart$Line`(중첩 레코드)이 바깥 `Cart`를 가리키는 간선이다. 호출자 수는 같다.
- 차이는 간선 수가 아니라 **시그니처에 무엇이 흐르나**다. A는 `int[]`(저장 형식)가, B는 `Line`(의미 있는 값)이 흐른다.

변경 요청: "같은 상품을 두 번 담으면 한 줄로 합친다." 저장을 `LinkedHashMap<상품ID, int[]>`로 바꾼다. 입력은 상품1 2개, 상품2 1개, 상품1 1개다(합치면 상품1이 3개라 사은품 조건이 된다).

```text
## A1 (반환 타입을 Map으로 바꿈)
src/cart/PriceCalculator.java:3: error: for-each not applicable to expression type
src/cart/PromotionRule.java:4: error: for-each not applicable to expression type
src/cart/PromotionRule.java:4: error: cannot find symbol
src/cart/ReceiptPrinter.java:3: error: for-each not applicable to expression type
src/cart/StockChecker.java:3: error: for-each not applicable to expression type
5 errors
## A1 fixed (호출자까지 고친 뒤)
subtotal=8000 need(1)=3 lines=3 receipt=[#1 x3 #2 x1 #999 x1]
 src/cart/Cart.java            | 10 ++++++----
 src/cart/PriceCalculator.java |  2 +-
 src/cart/PromotionRule.java   |  2 +-
 src/cart/ReceiptPrinter.java  |  2 +-
 src/cart/StockChecker.java    |  2 +-
 5 files changed, 10 insertions(+), 8 deletions(-)
## A2 (반환 타입을 지키려고 List 복사본을 반환)
subtotal=8000 need(1)=3 lines=2 receipt=[#1 x3 #2 x1]
 src/cart/Cart.java | 10 ++++++----
 1 file changed, 6 insertions(+), 4 deletions(-)
## B
subtotal=8000 need(1)=3 lines=3 receipt=[#1 x3 #2 x1 #999 x1]
 src/cart/Cart.java | 10 ++++++----
 1 file changed, 6 insertions(+), 4 deletions(-)
```

| | 바뀐 파일 | 컴파일 오류 | 결과 |
|---|---|---|---|
| A1 표현을 따라 시그니처 변경 | 5 | 5건(호출자 4파일) | 고친 뒤 정상 |
| A2 시그니처를 지키고 복사본 반환 | 1 | 0 | **사은품이 조용히 사라짐**(`lines=2`, `#999` 없음) |
| B 값만 내보냄 | 1 | 0 | 정상(`#999 x1`) |

- A1: 내부 표현이 곧 인터페이스라, 표현을 바꾸니 호출자 4개가 컴파일에서 깨졌다. `Analytics`는 `Map`에도 `size()`가 있어 우연히 살아남았다.
- A2가 더 위험하다. 컴파일은 통과한다. 그러나 `PromotionRule`은 "반환 리스트에 쓰면 장바구니에 들어간다"는 **비형식 인터페이스**에 기대고 있었다. 복사본에 쓴 사은품은 버려졌다.
- B는 `Cart` 한 파일이다. 쓰기가 원래부터 `add()`로만 들어왔으므로 저장 방식을 바꿔도 아무도 몰랐다.
- 해석: 결합의 강도는 간선 수가 아니라 **간선이 실어 나르는 지식**에 달렸다.

### 반대 상황 — 숨기기가 손해일 때

- 숨긴 결정이 **실제로는 호출자가 알아야 하는** 결정이면, 은닉은 인지 부하를 줄이지 않고 놀라움을 만든다. 예: 성능상 차이가 큰 연산(합치기에 O(n) 복사)을 숨기면 호출자가 반복문 안에서 부른다.
- B의 `lines()`는 호출마다 복사본을 만든다. 이 비용은 APOSD가 말하는 "무엇을 숨길지"의 판단 대상이다 — 줄 수가 아주 많은 장바구니라면 반복자·읽기 전용 뷰(`Collections.unmodifiableList`)가 나을 수 있다(예시 판단, 측정 안 함).

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 차수** — 노드의 들어오는 간선 수(fan-in, 의존받음)와 나가는 간선 수(fan-out, 의존함). fan-in이 큰 모듈의 인터페이스 변경은 비싸다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **간선 가중치로서의 "폭"** — 간선마다 오가는 타입·형식을 적어 두면 누출을 찾는다. `javap -public`으로 공개 시그니처에 내부 타입(`int[]`, 가변 컬렉션)이 보이는지 본다(실험).
- **방어적 복사·불변 값** — `List.copyOf`, `record`. 내부 상태로 가는 쓰기 경로를 끊는다. 불변성은 19번대(값 객체·불변) 주제와 이어진다.
- **접근 제어** — Java의 `private`·package-private, JPMS `module-info.java`의 `exports`. 언어가 인터페이스 경계를 강제하는 장치다.
- **군집(클러스터링)** — 응집 판별을 그래프로 하면 "같은 필드를 쓰는 메서드끼리 연결한 그래프의 연결 요소 수"다. 요소가 둘 이상이면 클래스가 두 가지 일을 하고 있을 가능성이 크다(휴리스틱). 연결 요소는 [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. 모듈이 **숨기는 결정 하나**를 한 문장으로 쓴다. 못 쓰면 모듈 경계가 아직 없다.
2. 공개 시그니처를 훑는다. 반환·인자에 내부 저장 타입(`int[]`, `Map<String,Object>`, 엔티티 그 자체), 가변 컬렉션이 보이면 누출 후보다.

```bash
javap -public -cp out cart.Cart          # 공개 시그니처만
jdeps -verbose:class -filter:none out    # 누가 누구를 쓰나 (fan-in)
```

3. 비형식 약속을 찾는다. "반환 리스트에 쓰면 반영된다", "이 메서드 전에 저것을 불러야 한다" 같은 것은 시그니처에 안 보인다. 호출처를 읽어야 보인다.
4. 내부 표현 대신 **의미 있는 값**(record, 값 객체)과 **연산**(`add`, `quantityOf`)을 내보낸다.
5. 응집 점검: 이 모듈을 바꾸는 이유를 적는다. 둘 이상이면 나눌지 판단한다.

### 2. 코드 (Java)

```java
// 누출: 호출자가 저장 형식을 알고, 내부에 직접 쓴다
public List<int[]> lines() { return lines; }

// 은닉: 값의 복사본만, 쓰기는 연산으로
public List<Line> lines() { return lines.values().stream().map(l -> new Line(l[0], l[1], l[2])).toList(); }
public void add(int productId, int qty, int unitPrice) { /* 합치기 규칙은 여기만 안다 */ }
```

- `Stream.toList()`는 JDK 16부터 수정 불가 리스트를 돌려준다(JDK API 문서).

## 장애 시나리오와 대처

### 1. 내부 표현 변경이 호출자 전부를 깨뜨림 (⚠ 커리큘럼 — 정보 누출)

- 현상: 저장 방식 하나(List → Map, 금액 int → long)를 바꿨는데 여러 모듈이 컴파일되지 않는다.
- 보이는 형태: `javac` 오류가 바꾼 파일이 아닌 **호출자 파일들**에 줄줄이 난다. 실험에서는 5건(호출자 4파일).
- 원인: 내부 표현이 공개 시그니처에 그대로 실려 있었다.
- 대처: 표현 대신 값·연산을 내보내도록 인터페이스를 먼저 바꾸는 정리 커밋을 낸다. 그 뒤의 표현 변경은 실험의 B처럼 1파일이 된다.

### 2. 컴파일은 되는데 기능이 사라짐 — 비형식 인터페이스 위반

- 현상: 리팩터링 뒤 프로모션 사은품·감사 로그 같은 "곁다리" 기능이 조용히 빠진다.
- 보이는 형태: 오류 없음. 실험의 `lines=2`, `#999` 없음. 매출·재고 대사에서 늦게 드러난다.
- 원인: 호출자가 "반환 컬렉션에 쓰면 반영된다"는, 시그니처에 없는 약속에 기대고 있었다.
- 대처: 내부 컬렉션을 내보내지 않는다. 내보내야 하면 수정 불가 뷰를 돌려줘서 쓰기 시도가 즉시 `UnsupportedOperationException`으로 드러나게 한다.

### 3. 잡동사니 모듈 — 우연적 응집

- 현상: `CommonUtils`, `Helper`가 수천 줄이고, 거의 모든 PR이 이 파일을 건드린다. 충돌(merge conflict)이 잦다.
- 보이는 형태: `git log --format= --name-only | sort | uniq -c | sort -rn` 상위에 그 파일. fan-in이 매우 크다.
- 원인: 함께 바뀌지 않는 것들이 "어디 둘지 몰라서" 한 곳에 모였다.
- 대처: 함수마다 실제 사용처 근처(그 지식을 쓰는 모듈)로 옮긴다. 옮긴 뒤 fan-in이 줄었는지 jdeps로 확인한다.

### 4. 제어 플래그 결합

- 현상: `process(order, true, false, 2)` 같은 호출이 늘고, 플래그 하나 추가할 때마다 모든 호출자를 고친다.
- 보이는 형태: boolean·int 모드 인자, 메서드 안의 `if (mode == ...)` 분기.
- 원인: 호출자가 피호출자의 내부 흐름을 조종한다(제어 결합).
- 대처: 모드별로 메서드를 나누거나 다형성으로 바꾼다(28 taming-conditionals).

## 핵심 문장

- 의존은 없앨 수 없다. 설계는 모듈 사이로 흐르는 것을 좁히고, 함께 바뀌는 것을 한 모듈에 모으는 일이다.
- 정보 은닉은 바뀔 설계 결정을 한 모듈 안에 숨기는 것이다(Parnas 1972). 숨긴 결정은 바꾸기 쉽고 드러낸 결정은 바꾸기 어렵다.
- 결합의 강도는 간선 수가 아니라 간선이 실어 나르는 지식이다. 실험에서 간선 수가 비슷한 두 설계의 같은 변경이 5파일과 1파일로 갈렸다.
- 시그니처에 없는 약속(반환 리스트에 쓰기)도 인터페이스다. 그것을 깨면 컴파일러는 침묵하고 기능이 조용히 사라진다.
- 응집은 구조적 설계 척도에서는 요소 사이 관계의 종류로 정의된다. 실무에서는 "이 모듈을 바꾸는 이유가 몇 개인가"(SRP 계열 휴리스틱)로 빠르게 점검한다.

## 관련 주제·근거

- 선행
  - [01-complexity](../01-complexity/2-summary.md) — 의존과 모호
- 후속
  - [03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md) — 인터페이스를 얼마나 좁고 깊게
  - [04-decompose-by-change](../04-decompose-by-change/2-summary.md) — 무엇을 숨길지 고르는 기준(KWIC)
  - [05-connascence](../05-connascence/2-summary.md) — 결합을 종류·강도·지역성으로 세분
  - [22-solid](../22-solid/2-summary.md)(SRP) · [28-taming-conditionals](../28-taming-conditionals/2-summary.md)(제어 플래그) · [37-architecture-styles](../37-architecture-styles/2-summary.md)
- 다른 영역
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md)
- 글·문서
  - D. L. Parnas, "On the Criteria To Be Used in Decomposing Systems into Modules", CACM 15(12):1053–1058, 1972-12 — 원문 PDF 열람(모듈 = 책임 할당, 정보 은닉 기준 인용) <https://www.win.tue.nl/~wstomv/edu/2ip30/references/criteria_for_modularization.pdf> · DOI 10.1145/361598.361623
  - W. P. Stevens, G. J. Myers, L. L. Constantine, "Structured design", IBM Systems Journal 13(2):115–139, 1974 — 서지는 Crossref(DOI 10.1147/sj.132.0115)로 확인, 본문 미열람
  - Wikipedia "Coupling (computer programming)", "Cohesion (computer science)" — 결합·응집 단계 목록(2026-10-02 열람) <https://en.wikipedia.org/wiki/Coupling_(computer_programming)> · <https://en.wikipedia.org/wiki/Cohesion_(computer_science)>
  - J. Ousterhout, 『A Philosophy of Software Design』 2판 4장(인터페이스 = 형식 + 비형식)·5장(정보 은닉과 누출, 시간 순 분해 회피, 조금 큰 클래스) — 본문 미열람, 독자 노트(Lebrero 2021) <https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/>로 확인한 요지
  - JDK 21 `jdeps`·`javap` 도구 문서 <https://docs.oracle.com/en/java/javase/21/docs/specs/man/jdeps.html>
- 실험 목록 (코드: scratchpad `sd/01/e02/{a,b}/src/cart/*.java`, A의 변형은 git 브랜치 `master`(A2)·`a1`(A1), 구동 `run.sh`·`deps.sh`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - jdeps 간선 수(A 6, B 7)·`javap -public` 시그니처 비교
  - "같은 상품 합치기" 표현 변경: A1 컴파일 오류 5건·5파일 10/8줄, A2 1파일·사은품 소실, B 1파일·정상
