# software-design/01-complexity — 복잡도: 세 증상과 두 원인 — 정리 (힌트)

## 해결하는 문제

"이 코드는 복잡하다"는 말만으로는 무엇을 고쳐야 할지 모른다.\
복잡도를 **증상**(무엇이 힘든가)과 **원인**(왜 힘든가)으로 나눠 부르면, 고칠 대상이 보인다.

```text
 요구 한 줄: "부가세율을 바꿔 주세요"
        │
        v
 ┌─────────────────────────────── 증상 ───────────────────────────────┐
 │ 변경 증폭      고칠 곳이 5군데다                                     │
 │ 인지 부하      5군데를 다 알아야 고칠 수 있다                         │
 │ unknown unknowns  그 5군데가 어디인지 아무도 모른다 (grep에 안 걸린다) │
 └────────────────────────────────────────────────────────────────────┘
        ^
        │ 원인
   의존(dependency) — 한 코드를 다른 코드와 따로 이해·수정할 수 없다
   모호(obscurity)  — 중요한 정보가 드러나 있지 않다
```

- *복잡도(complexity)*: Ousterhout의 정의로, 시스템을 **이해하고 수정하기 어렵게 만드는 구조상의 모든 것**. 저자 대담 원문: "things that make it hard to understand and modify a system".
- *변경 증폭(change amplification)*: 단순해 보이는 변경 하나가 여러 곳의 수정을 요구하는 것.
- *인지 부하(cognitive load)*: 작업 하나를 끝내려고 개발자가 알아야 하는 정보의 양.
- *unknown unknowns*: 알아야 할 것이 있는데, 그게 무엇인지도, 있는지조차도 알아낼 방법이 없는 상태. 셋 중 가장 나쁘다(APOSD 2장).

쉬운 예: 집 안 전등 스위치가 방마다 따로 배선돼 있으면 "전구를 LED로 바꾸자"는 일이 방 개수만큼 늘어난다(변경 증폭). 그런데 다락방 전등이 거실 차단기에 묶여 있다는 사실을 아무도 모르면 거실 공사 중에 다락방이 꺼진다(unknown unknowns).\
똑같은 구조다.\
실무 예: 세율 10%가 결제·영수증·환불·월말 보고에 각자 숫자로 박혀 있다. 세율 변경 요청에 결제·영수증만 고치면 컴파일·실행은 되고, 환불 금액과 월말 보고가 조용히 틀린다(아래 실험).

설계 영역에서 "깨지면"은 크래시가 아니다.\
**변경 비용이 커지고, 고친 곳과 먼 곳에서 조용히 틀린다.**

## 동작·원리

### 1. 증상 셋은 서로 다르다

```text
 변경 증폭           인지 부하               unknown unknowns
 ┌─┐┌─┐┌─┐┌─┐┌─┐     ┌───────────────┐      ┌─┐┌─┐┌─┐  ┌─┐ ← 이것을
 │✎││✎││✎││✎││✎│     │ 알아야 할 것   │      │✎││✎││✎│  │?│   몰랐다
 └─┘└─┘└─┘└─┘└─┘     │ 규칙·순서·예외 │      └─┘└─┘└─┘  └─┘
 고칠 곳이 많다       │ 숨은 전제      │      고칠 곳을 다 찾았다고
 (그래도 다 보인다)   └───────────────┘      믿었는데 하나가 빠졌다
```

- 변경 증폭은 **보이는** 비용이다. 고칠 곳이 다섯이면 다섯을 고치면 된다.
- 인지 부하는 **머릿속** 비용이다. 고칠 곳이 하나여도, 그 한 곳을 고치려고 규칙 열 개를 알아야 하면 부하가 크다.
- unknown unknowns는 **안 보이는** 비용이다. 다 고쳤다고 믿는 순간 남은 하나가 장애가 된다.
- Ousterhout는 줄 수가 많아도 인지 부하가 적으면 더 단순하다고 본다(APOSD 2장). "짧은 코드 = 단순한 코드"가 아니다.

### 2. 원인 둘

```text
 의존(dependency)                         모호(obscurity)
 A ──필요──> B                             "10 / 11" 이 왜 여기 있지?
 B가 바뀌면 A도 봐야 한다                   이름·주석·타입 어디에도
   ├ 명시적: import, 메서드 호출 → 도구가 본다     "부가세 역산"이라는 말이 없다
   └ 암묵적: 같은 숫자·같은 형식·같은 순서를        └ 중요한 정보가 안 드러남
            각자 안다 → 도구가 못 본다
```

- *의존(dependency)*: 어떤 코드를 다른 코드와 따로 이해하거나 수정할 수 없을 때 둘 사이에 있는 관계. 의존 자체는 없앨 수 없다. 줄이고, 드러나게 만든다.
- *모호(obscurity)*: 중요한 정보가 분명하지 않은 것. 일관성 없는 이름·문서 없는 전제가 대표다(APOSD 2장, 독자 노트로 확인).
- 대응: 의존 → 변경 증폭·인지 부하, 모호 → unknown unknowns·인지 부하.
- Ousterhout 대담 원문: 최악은 "a crucial piece of information hidden in some far-away piece of code that the developer has never heard of"다. 암묵적 의존 + 모호가 겹친 경우다.

### 3. 복잡도는 쌓인다

```text
 작은 땜질 1개  ──>  "이 정도야"  ──>  땜질 50개  ──>  누구도 전체를 모른다
   (각각은 무해해 보임)                 (되돌리기 어려움)
```

- APOSD 2장(2.4): 복잡도는 한 번의 큰 실수보다 **작은 것이 하나씩 쌓여** 생긴다. 그래서 저자는 "무관용(zero tolerance)"을 권한다. 2장은 이 말을 예고만 하고, 자세한 논의는 3장 "Working Code Isn't Enough"에 있다(독자 노트로 확인한 요지).
- APOSD 2장의 근사식(독자 노트로 확인): 시스템 복잡도 ≈ Σ(부분 p의 복잡도 cₚ × 개발자가 그 부분에 쓰는 시간의 비율 tₚ). 아무도 건드리지 않는 복잡한 부분은 전체 복잡도에 거의 보태지 않는다.
- 이것은 저자의 주장이다. 측정 공식이 아니라 "어디부터 줄일까"를 정하는 사고 도구다. 변경 빈도로 실제 tₚ를 보는 방법은 [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md)에서 다룬다.

### 실험: 같은 세율 변경을 두 설계에 적용

설계 A는 세율을 각자 안다. 설계 B는 `TaxPolicy` 한 곳만 안다.

```java
// 설계 A — 다섯 파일이 각자 10%를 안다 (발췌)
class Checkout { static long gross(long net) { return net + Math.round(net * 0.10); } }
class Refund   { static long netOf(long gross) { return Math.round(gross / 1.10); } }
class Report   { static long netOf(long gross) { return gross * 10 / 11; } }   // 역산, 정수 연산
class CartView { static String badge() { return "부가세 10% 포함"; } }

// 설계 B — 세율을 아는 곳은 하나
final class TaxPolicy {
    private static final int RATE_PERCENT = 10;
    static long vatOf(long net)   { return Math.round(net * RATE_PERCENT / 100.0); }
    static long gross(long net)   { return net + vatOf(net); }
    static long netOf(long gross) { return Math.round(gross * 100.0 / (100 + RATE_PERCENT)); }
    static String label()         { return "부가세 " + RATE_PERCENT + "%"; }
}
```

변경 요청: 세율 10% → 12%(예시 수치). 개발자가 A에서 `grep "0.10\|10%"`로 찾은 곳만 고쳤다.

(실험, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, git 2.43, 2026-10-02)

```text
$ grep -rn -E "0\.10|10%" src          # 설계 A
src/shop/Invoice.java:4:        long vat = Math.round(net * 0.10);
src/shop/Invoice.java:5:        return "공급가 " + net + " / 부가세(10%) " + vat + " / 합계 " + (net + vat);
src/shop/Checkout.java:4:    public static long gross(long net) { return net + Math.round(net * 0.10); }
src/shop/CartView.java:3:    public static String badge() { return "부가세 10% 포함"; }
 src/shop/CartView.java | 2 +-
 src/shop/Checkout.java | 2 +-
 src/shop/Invoice.java  | 4 ++--
 3 files changed, 4 insertions(+), 4 deletions(-)
## A after grep-change
checkout gross=11200
invoice  공급가 10000 / 부가세(12%) 1200 / 합계 11200
refund   net=10182
report   net=10181  (불일치! 기대 10000)
cart     부가세 12% 포함
```

- 컴파일 오류도, 예외도 없다. 환불 공급가가 10182, 보고 공급가가 10181로 **조용히 틀렸다**.
- grep에 안 걸린 두 곳(`/ 1.10`, `* 10 / 11`)이 unknown unknowns였다. 같은 "10%"가 다른 모양으로 적혀 있었다(모호).

숨은 곳까지 고친 최종 변경과 B의 변경을 비교했다.

```text
## A 전체(base→최종)
 src/shop/CartView.java | 2 +-
 src/shop/Checkout.java | 2 +-
 src/shop/Invoice.java  | 4 ++--
 src/shop/Refund.java   | 2 +-
 src/shop/Report.java   | 2 +-
 5 files changed, 6 insertions(+), 6 deletions(-)
## B
 src/shop/TaxPolicy.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

| | 바뀐 파일 | 바뀐 줄(+/−) | 첫 시도에서 놓친 곳 |
|---|---|---|---|
| A 각자 앎 | 5 | 6/6 | 2 (환불·보고, 조용히 틀림) |
| B 한 곳이 앎 | 1 | 1/1 | 0 |

### 실험: 도구에는 어떤 의존이 보이나 (jdeps)

```text
## a
 shop.Main -> shop.CartView out
 shop.Main -> shop.Checkout out
 shop.Main -> shop.Invoice out
 shop.Main -> shop.Refund out
 shop.Main -> shop.Report out
## b
 shop.CartView -> shop.TaxPolicy out
 shop.Checkout -> shop.TaxPolicy out
 shop.Invoice -> shop.TaxPolicy out
 shop.Main -> shop.CartView out
 shop.Main -> shop.Checkout out
 shop.Main -> shop.Invoice out
 shop.Main -> shop.Refund out
 shop.Main -> shop.Report out
 shop.Refund -> shop.TaxPolicy out
 shop.Report -> shop.TaxPolicy out
```

(`jdeps -verbose:class -filter:none out`, JDK 21.0.12, 같은 환경)

- A에는 세율에 관한 간선이 **하나도 없다**. 다섯 곳이 "10%"라는 지식을 공유하는데 그 의존은 코드 구조에 안 나타난다(암묵적 의존).
- B는 간선이 5개 **늘었다**. 대신 `TaxPolicy`로 들어오는 간선을 따라가면 세율 변경의 영향 범위가 그대로 나온다.
- 해석: 간선 수가 늘었다고 복잡도가 늘어난 것이 아니다. 숨은 의존을 **명시적 의존으로 바꾼** 것이다.

### 실험: 반대 상황 — 공유가 손해인 변경

B에서 "영수증만 `부가세(12%)`처럼 괄호로" 요청이 왔다. `TaxPolicy.label()`을 고쳤다.

```text
 src/shop/TaxPolicy.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
checkout gross=11200
invoice  공급가 10000 / 부가세(12%) 1200 / 합계 11200
refund   net=10000
report   net=10000  (일치)
cart     부가세(12%) 포함
```

- 영수증만 바꾸려 했는데 장바구니 배지까지 바뀌었다.
- 세율(규칙)은 함께 바뀌어야 하는 지식이었다. 표시 문구는 화면마다 따로 바뀌는 지식이었다. **함께 바뀌지 않는 것을 공유하면** 공유가 새 의존이 된다.
- 무엇을 한곳에 모을지는 "무엇이 함께 바뀌나"로 정한다 — 04 decompose-by-change의 주제다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프(유향 그래프)** — 노드 = 클래스·모듈, 간선 = "A가 B를 쓴다". 변경 증폭은 바뀐 노드로 **들어오는 간선의 역방향 도달 집합** 크기로 근사한다. 그래프 기초는 [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **역방향 도달 가능성(BFS·DFS)** — "B를 바꾸면 누가 영향을 받나" = 간선을 뒤집은 그래프에서 B부터 BFS. [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md).
- **강한 연결 요소(SCC)** — 순환 의존 묶음. 묶음 안의 하나를 바꾸면 묶음 전체를 봐야 한다. [algorithm/18-scc](../../algorithm/18-scc/2-summary.md).
- **바이트코드 분석** — `jdeps`는 컴파일된 `.class`의 상수 풀·시그니처에서 참조를 읽어 클래스 간 간선을 만든다. 같은 숫자를 각자 적은 **암묵적 의존은 간선이 없어** 볼 수 없다(위 실험).
- **동시 변경(co-change) 집계** — 커밋마다 함께 바뀐 파일 쌍을 센다. 구조 분석이 못 보는 암묵적 의존을 이력으로 찾는다(53에서 자세히).

## 적용 — 풀어나가는 법

### 1. 변경 요청을 받으면 먼저 범위를 잰다

1. 요구를 한 문장으로 쓴다. "세율 10 → 12".
2. 그 지식이 **코드에 몇 번 적혀 있나**를 찾는다. 문자열 grep만으로는 부족하다. `0.10`, `1.10`, `10/11`, `"10%"`처럼 모양이 다를 수 있다.
3. 명시적 의존은 도구로: `jdeps -verbose:class -filter:none`(Java — 기본 `-filter:package`는 같은 패키지 간선을 숨긴다, [54](../54-designing-for-deletion/2-summary.md) 실험), IDE의 Find Usages.
4. 암묵적 의존은 이력으로: 과거에 같은 종류의 변경이 어떤 파일을 함께 건드렸나.

```bash
# 파일별 변경 횟수(변경 빈도 = tₚ의 근사)
git log --format= --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head
# 한 커밋의 영향 범위
git show --stat <커밋>
```

5. 고칠 곳이 셋을 넘으면 고치기 전에 **한곳으로 모으는 정리**를 먼저 할지 판단한다([14-tidy-first](../14-tidy-first/2-summary.md)).

### 2. 복잡도를 줄이는 방향 — 증상별

| 증상 | 대표 원인 | 줄이는 방향 | 이어지는 노트 |
|---|---|---|---|
| 변경 증폭 | 같은 지식이 여러 곳에 | 한 모듈이 그 지식을 소유 | 02, 04 |
| 인지 부하 | 인터페이스가 넓고 얕다 | 깊은 모듈, 기본값 | 03 |
| unknown unknowns | 암묵적 의존 + 모호 | 명시적 의존(타입·이름), 주석으로 "왜" | 05, 09 |

### 3. 코드 예 (Java) — 숨은 의존을 드러내기

```java
// 전: 각자 "10/11" 을 안다
long net = gross * 10 / 11;

// 후: 지식에 이름을 주고 한 곳에 둔다. 호출자는 규칙이 아니라 의도를 쓴다
long net = TaxPolicy.netOf(gross);
```

- 바꾼 뒤에는 `TaxPolicy`로 들어오는 간선이 곧 영향 범위다. jdeps·IDE가 찾아 준다.

## 장애 시나리오와 대처

### 1. 한 줄 요구 변경에 파일 20개 수정 (⚠ 커리큘럼 — 변경 증폭)

- 현상: "세율 변경", "상태 하나 추가" 같은 요구 하나의 PR이 파일 수십 개를 건드린다.
- 보이는 형태: `git show --stat`의 파일 수가 요구 크기에 비해 크다. 같은 파일 묶음이 커밋마다 함께 바뀐다. 리뷰어가 "다른 데도 있지 않아요?"를 반복한다.
- 원인: 같은 결정(세율·상태 의미·포맷)이 여러 모듈에 복제돼 있다.
- 대처: 이번 변경 전에 그 결정을 한 모듈로 모으는 정리 커밋을 따로 낸다. 실험에서 모은 뒤의 세율 변경은 5파일 → 1파일이었다.

### 2. 수정 후 엉뚱한 곳 장애 (⚠ 커리큘럼 — unknown unknowns)

- 현상: 결제 화면을 고쳤는데 다음 날 환불·정산 금액 문의가 들어온다.
- 보이는 형태: 예외·에러 로그가 없다. 대사(reconciliation) 불일치, 고객 문의, 월말 보고 숫자 차이로 늦게 드러난다. 실험에서는 `refund net=10182`, `report net=10181`.
- 원인: 같은 지식이 다른 모양으로 적힌 암묵적 의존. grep·jdeps에 걸리지 않았다.
- 대처: 불변식을 테스트로 고정한다(예: `netOf(gross(x)) == x`). 지식을 한 곳에 두고 이름을 붙인다. 고친 뒤 "다른 표현으로 같은 것을 아는 곳"을 이력(co-change)으로 찾는다.

### 3. 공유 모듈을 고쳤더니 무관한 화면이 바뀐다

- 현상: 한 화면용 문구·형식 변경이 다른 화면에도 나타난다.
- 보이는 형태: 스냅샷 테스트·화면 QA에서 다른 화면 차이. 실험의 `cart 부가세(12%) 포함`.
- 원인: 함께 바뀌지 않는 지식(화면별 문구)을 공유 모듈에 넣었다. 중복을 없앤 것이 새 의존을 만들었다.
- 대처: "함께 바뀌는가"로 다시 나눈다. 규칙은 공유하고 표현은 각 화면이 갖는다(04, 11 when-to-abstract).

### 4. 아무도 전체를 모른다 — 복잡도 누적

- 현상: 작은 기능에도 추정이 계속 빗나가고, 특정 사람만 고칠 수 있는 모듈이 생긴다.
- 보이는 형태: 같은 파일의 변경 횟수가 계속 상위에 있다. 그 파일 관련 버그 수정 커밋 비율이 높다.
- 원인: 작은 땜질이 쌓였다(APOSD 2장의 "점진적 누적").
- 대처: 변경 빈도가 높은 곳부터(Σcₚtₚ에서 tₚ가 큰 곳) 정리한다. 안 건드리는 복잡한 코드는 후순위다.

## 핵심 문장

- 복잡도는 시스템을 이해하고 수정하기 어렵게 만드는 구조상의 모든 것이다(Ousterhout).
- 증상은 변경 증폭·인지 부하·unknown unknowns 셋이고, 원인은 의존과 모호 둘이다.
- unknown unknowns가 가장 나쁘다. 실험에서 grep으로 찾은 곳만 고치자 컴파일·실행은 됐지만 환불과 보고 금액이 조용히 틀렸다.
- 같은 지식을 각자 적은 의존은 jdeps에도 간선이 없다. 지식을 한 모듈에 모으면 간선은 늘지만 영향 범위가 보인다.
- 모으는 기준은 "함께 바뀌나"다. 함께 바뀌지 않는 것을 공유하면 그것이 새 의존이 된다.

## 관련 주제·근거

- 후속
  - 02 modularity-coupling-cohesion — [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md)
  - 03 deep-modules-and-abstraction — [03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md)
  - 04 decompose-by-change — [04-decompose-by-change](../04-decompose-by-change/2-summary.md)
  - 05 connascence — [05-connascence](../05-connascence/2-summary.md)
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) · [14-tidy-first](../14-tidy-first/2-summary.md) · [11-when-to-abstract](../11-when-to-abstract/2-summary.md)
  - [10 code-smells](../10-code-smells/2-summary.md)(Shotgun Surgery), [52 complexity-metrics](../52-complexity-metrics/2-summary.md)
- 다른 영역
  - [domain-modeling/advanced/06-tax](../../domain-modeling/advanced/06-tax/2-summary.md) — 부가세 규칙 자체가 얼마나 많은 결정을 담는지
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [algorithm/18-scc](../../algorithm/18-scc/2-summary.md)
- 글·문서
  - John Ousterhout, 『A Philosophy of Software Design』 2판(Yaknyam Press, 2021) 2장 "The Nature of Complexity" — 책 본문은 열람하지 못했다. 2장의 세 증상·두 원인·Σcₚtₚ·zero tolerance 예고(본론은 3장)는 독자 노트 두 개(Dan Lebrero, 2021-02-24 <https://danlebrero.com/2021/02/24/philosophy-of-software-design-summary/> · nchelluri의 장별 인용 노트 <https://gist.github.com/nchelluri/c7c0635bddaa7d67687c411ea7621b21> — "unknown unknowns are the worst", "more lines of code is actually simpler, because it reduces cognitive load", "accumulates in lots of small chunks" 인용)와 아래 대담 원문으로 교차 확인한 범위다.
  - Ousterhout·Martin 대담 "aposd-vs-clean-code"(GitHub README) — 복잡도 정의·"far-away piece of code" 원문 <https://github.com/johnousterhout/aposd-vs-clean-code/blob/main/README.md>
  - APOSD 2판 소개·발췌 페이지(저자 사이트) <https://web.stanford.edu/~ouster/cgi-bin/aposd.php>
  - `jdeps` — JDK 21 도구 문서 <https://docs.oracle.com/en/java/javase/21/docs/specs/man/jdeps.html>
- 실험 목록 (코드: scratchpad `sd/01/e01/{a,b}/src/shop/*.java`, 구동 `run.sh`·`deps.sh`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, git 2.43)
  - 세율 10→12 변경: A grep 변경 후 실행(환불 10182·보고 10181), A 최종 5파일 6/6줄, B 1파일 1/1줄
  - jdeps 간선: A는 세율 관련 간선 0, B는 `→ TaxPolicy` 5개
  - 반대 상황: B의 `label()` 변경이 장바구니 배지까지 바꿈
