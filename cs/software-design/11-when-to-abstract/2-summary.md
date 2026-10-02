# software-design/11-when-to-abstract — 추상화 시점: 셋째 사례·잘못된 추상화·지식 중복 — 정리 (힌트)

## 해결하는 문제

중복을 보면 합치고 싶다. 합치는 시점이 틀리면 두 방향으로 손해를 본다.

```text
 너무 이르게 합침                               너무 늦게(또는 끝내 안) 합침
 ┌────────────────────────────┐               ┌────────────────────────────┐
 │ format(won, refund, report,│               │ Receipt:   won / 11        │
 │        parenNegative, ...) │               │ Refund:    v / 11          │  같은 규칙이
 │  if (refund) ...           │               │ Settlement:won / 11        │  세 곳에
 │  if (report) ...           │               └────────────────────────────┘
 │  if (parenNegative) ...    │                 규칙이 바뀌면 세 곳을 다 고쳐야 한다
 └────────────────────────────┘                 하나를 빠뜨리면 화면끼리 숫자가 어긋난다
  호출처마다 다른 요구가 플래그로 쌓인다
  한 호출처를 고치면 다른 호출처가 깨진다
```

- *추상화(abstraction)*: 여러 곳의 공통점을 이름 붙은 하나(함수·클래스·모듈)로 뽑아내는 것.
- *우연한 중복*: 코드 모양은 같지만 서로 다른 지식이라 따로 바뀌는 중복.
- *지식 중복*: 같은 규칙·사실이 여러 곳에 적혀 있어 함께 바뀌어야 하는 중복.

쉬운 예: 두 친구의 생일이 같은 날이라 알람 하나로 합쳤다. 한 친구의 생일을 잘못 알았다는 걸 알고 알람 날짜를 고치면, 다른 친구 알람도 같이 옮겨진다.\
똑같은 구조다.\
실무 예: 영수증·환불 영수증·정산 리포트가 금액을 비슷하게 찍는다고 공통 함수 하나로 합쳤다. 정산만 음수를 괄호로 찍어 달라는 요구가 오자 그 함수에 플래그가 붙기 시작한다.

우연한 중복과 진짜 중복을 가르는 기초(카드 수수료 vs 정산 수수료, 서비스 경계의 의도적 중복)는 원본 [engineering/clean-code](../../engineering/clean-code/2-summary.md) 「N — 비중복」 절에 있다.\
이 노트는 **언제** 합치고, 잘못 합쳤으면 **어떻게 되돌리나**를 다룬다.

## 동작·원리

### 1. 판단 기준 — "같은 지식인가, 함께 바뀌나"

```text
   코드 A ─┐                         ┌─ 예 → 지식 중복: 한 곳으로 모은다 (지금 또는 곧)
           ├─ 같은 규칙·사실을 말하나? ┤
   코드 B ─┘   (하나가 바뀌면           └─ 아니오 → 우연한 중복: 그대로 둔다
               다른 것도 바뀌어야 하나?)       (모양이 같아도 합치지 않는다)
```

- 『The Pragmatic Programmer』 20주년판 「The Evils of Duplication」 절(Tip 15)의 DRY 정의: "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."
- 같은 절은 1판 설명이 부족했다고 밝히고, DRY를 "소스 줄을 복사하지 말라"로 읽으면 "작고 사소한 부분"만 본 것이라고 쓴다. DRY는 **지식·의도**의 중복에 관한 원칙이다.
- 같은 절의 예: 나이와 주문 수량 검증 함수 본문이 똑같아도 "That's a coincidence, not a duplication." 규칙이 우연히 같을 뿐이다.
- 시험 질문(같은 절의 "acid test"): 어떤 한 측면을 바꿀 때 여러 곳을, 여러 형식으로 고치게 되나? 그렇다면 DRY가 아니다.

### 2. 셋째 사례 규칙 (Rule of Three)

```text
  사례 1: 그냥 만든다
  사례 2: 중복이 보여 얼굴을 찡그리지만, 그래도 복사한다
  사례 3: 이제 리팩터링한다 (공통점과 차이점이 두 번의 비교로 드러났다)
```

- Fowler 『Refactoring』 1판(1999) 2장이 Don Roberts의 지침으로 소개했다: "The third time you do something similar, you refactor." 흔히 "Three strikes and you refactor"로 줄여 부른다(Wikipedia 표기 — 1판 인용은 2차 출처로 확인).
- 2판(2018)도 2장 「Principles in Refactoring」의 「When Should We Refactor?」 절 첫머리 「The Rule of Three」에 같은 지침을 싣는다. 끝 문장은 "Three strikes, then you refactor."다(목차는 출판사 미리보기, 본문 문구는 독자 노트 — 2차 출처로 확인).
- 셋을 기다리는 이유(해석): 사례가 둘이면 무엇이 공통이고 무엇이 바뀌는지 한 번만 비교한 것이다. 셋째가 오면 "어디가 변하는 축인가"가 한 번 더 확인된다.
- 숫자 3은 경험칙이다. 지식 중복(같은 세율·같은 검증 규칙)은 둘째 사례에서도 모으는 편이 싸다(아래 실험의 CR2).

### 3. 잘못된 추상화가 자라는 순서 (Metz, 2016)

```text
  ① A가 중복을 보고 뽑아 이름을 붙인다 ──> ② 시간이 흐른다
  ③ "거의 맞는" 새 요구가 온다
  ④ B는 추상화를 지키려고 매개변수 하나 + 조건 하나를 더한다
  ⑤ 또 새 요구 → 또 매개변수 → 또 조건      ← ④⑤를 되풀이
  ⑥ 공통 추상화가 "조건투성이 절차"가 된다 → 이해하기 어렵고 깨지기 쉽다
```

- Sandi Metz, "The Wrong Abstraction"(2016-01-20 블로그 재게재 — 원래 뉴스레터 글. RailsConf 2014 발표 "All the Little Things"의 한 절에서 한 주장을 풀어 썼다): "duplication is far cheaper than the wrong abstraction", "prefer duplication over the wrong abstraction".
- 붙잡게 되는 이유로 Metz는 매몰 비용 오류를 든다. 복잡하게 쌓인 코드일수록 "많이 투자했으니 지켜야 한다"는 압력이 커진다.
- 신호: 공유 코드에 매개변수를 넘기고 조건 경로를 더하고 있다면, 그 추상화는 틀렸다(Metz — "처음엔 맞았을 수 있지만 그날은 지났다"). Metz도 무엇이 일어나는지 파악하려고 조건 몇 개를 잠시 쌓는 것은 가끔 말이 된다고 단서를 단다.

### 4. 되돌아가기 — 인라인 → 호출처별로 덜어내기 → 다시 뽑기

```text
 [AmountText.format(won, refund, report, paren)]   ← 플래그 3개
        │ ① 인라인: 본문을 호출처 3곳에 복사
        v
 Receipt      : format 본문(refund=false, report=false, paren=false)
 Refund       : format 본문(refund=true , report=false, paren=false)
 Settlement   : format 본문(refund=false, report=true , paren=true )
        │ ② 호출처마다 넘기던 인자 값으로 안 쓰는 분기를 지운다
        v
 Receipt: 금액+부가세 문구   Refund: 부호 뒤집기+문구   Settlement: 괄호 표기
        │ ③ 남은 중복 중 "같은 지식"만 다시 뽑는다
        v
 Vat.of(won)  ← 세 곳이 반드시 같이 바뀌어야 하는 부가세 규칙만
```

- Metz가 제시한 순서: 추상화된 코드를 모든 호출처에 인라인 → 호출처마다 넘기던 인자로 실제 실행되는 부분만 남김 → 필요 없는 부분 삭제. 그 뒤 중복을 다시 보고 다시 뽑는다.
- 되돌아보면 각 호출처가 실행하던 코드는 꽤 달랐던 경우가 흔하다(Metz).
- Fowler 2판 카탈로그에서 ①은 Inline Function, ③은 Extract Function이다([refactoring.com 카탈로그](https://refactoring.com/catalog/)).

### 실험: 두 요구를 세 설계에 적용

설계 셋을 같은 테스트(`Tests.java`, 4개 확인)로 돌렸다.

- *DUP*: 세 호출처가 비슷한 코드를 각자 가진다(부가세 `won / 11`도 세 번).
- *ABS*: 둘째 사례 때 뽑은 공통 함수 `AmountText.format(won, refund, report)`.
- *RIGHT*: ABS를 인라인한 뒤 부가세 규칙만 `Vat.of`로 다시 뽑았다.

요구 둘:

- CR1(한 호출처만의 요구): 정산 리포트에서만 음수를 괄호로 `(12,000원)`.
- CR2(세 곳이 공유하는 지식): 부가세를 원 미만 반올림으로(12,000/11 = 1,090.9 → 1,091).

```java
// ABS의 CR1 — Metz가 말한 경로: 매개변수 하나 + 조건 하나
static String format(long won, boolean refund, boolean report, boolean parenNegative) { ... }
private static String money(long v, boolean parenNegative) {
  if (parenNegative && v < 0) return String.format("(%,d원)", -v);
  return String.format("%,d원", v);
}
// RIGHT — 진짜 공유 지식만
final class Vat {
  static long of(long amountIncludingVat) { return Math.round(amountIncludingVat / 11.0); }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, PMD 7.28.0, `scratchpad/sd/11/e11/`, 2026-10-02)

출력 발췌(`dup-cr2`·`abs-cr2` 테스트 ALL PASS 줄, `dup-cr2` PMD 줄, `abs-cr2`의 호출처 메서드 줄은 생략).

```text
=== CR1: 정산만 음수 괄호 ===
--- dup-v0 → dup-cr1
 SettlementReport.java | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)
--- abs-v0 → abs-cr1-slip
 AmountText.java | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
--- abs-v0 → abs-cr1
 AmountText.java       | 12 +++++++++---
 Receipt.java          |  2 +-
 RefundReceipt.java    |  2 +-
 SettlementReport.java |  2 +-
 4 files changed, 12 insertions(+), 6 deletions(-)
## 테스트 @dup-cr1 (단계 cr1)
ALL PASS
## 테스트 @abs-cr1-slip (단계 cr1)
FAIL 환불영수증  got=(12,000원) (부가세 (1,090원) 포함)  want=-12,000원 (부가세 -1,090원 포함)
1 FAILED
## 테스트 @abs-cr1 (단계 cr1)
ALL PASS
=== CR2: 부가세 반올림 (공유 지식) ===
--- dup-cr1 → dup-cr2
 Receipt.java          | 2 +-
 RefundReceipt.java    | 2 +-
 SettlementReport.java | 2 +-
 3 files changed, 3 insertions(+), 3 deletions(-)
--- abs-cr1 → abs-cr2
 AmountText.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
## 테스트 @dup-cr2-miss (단계 cr2)
FAIL 환불영수증  got=-12,000원 (부가세 -1,090원 포함)  want=-12,000원 (부가세 -1,091원 포함)
1 FAILED
```

```text
=== 되돌리기: abs-cr2 → right ===
 AmountText.java       | 18 ------------------
 Receipt.java          |  4 +++-
 RefundReceipt.java    |  5 ++++-
 SettlementReport.java |  7 ++++++-
 Vat.java              |  4 ++++
 5 files changed, 17 insertions(+), 21 deletions(-)
## 테스트 @right (단계 cr2)
ALL PASS
=== 같은 지식이 몇 곳에 쓰였나 (grep '/ 11') ===
dup-cr2: Receipt.java RefundReceipt.java SettlementReport.java
abs-cr2: AmountText.java
right: Vat.java
--- @abs-cr2 순환 복잡도(메서드별)
  'format(long, boolean, boolean, boolean)' = 3
  'money(long, boolean)' = 3
--- @right 순환 복잡도(메서드별)
  'line(long)' = 1
  'line(long)' = 1
  'row(long)' = 1
  'paren(long)' = 2
  'of(long)' = 1
```

- 관찰 1 — CR1(한 호출처만의 요구)은 DUP에서 정산 파일 1개만 고쳤다. ABS에서 플래그를 더하면 시그니처가 바뀌어 **4파일**을 고쳤다.
- 관찰 2 — `abs-cr1-slip`은 "정산 전용" 조건을 빠뜨린 **가정한 실수**다. 공통 함수 한 줄 수정이 환불 영수증을 깨뜨렸다. DUP에서는 같은 실수를 해도 정산 파일 밖으로 번질 길이 없다.
- 관찰 3 — 반대 방향도 있다. CR2(공유 지식)는 DUP에서 3파일을 고쳐야 했고, 하나를 빠뜨리면(`dup-cr2-miss`) 환불 영수증의 부가세만 1원 어긋났다. ABS는 1파일이었다.
- 관찰 4 — RIGHT는 두 요구 모두 1파일이다. 부가세 규칙은 `Vat.java` 한 곳, 정산 표기는 `SettlementReport.java` 한 곳이다. 되돌리기 자체는 5파일·+17/−21줄 한 번의 비용이었다.
- 해석: "중복을 없앴나"가 아니라 "바뀌는 이유가 같은 것끼리 묶였나"가 변경 비용을 정했다. 이 실험은 작은 예제 하나라 비율을 일반화하지 않는다.

## 쓰이는 자료구조·알고리즘

- **호출 그래프의 fan-in**: 공통 함수를 부르는 호출처 수. 공통 함수 한 줄 변경의 영향 범위가 곧 fan-in이다(실험: `AmountText` fan-in 3 → 4파일 수정). 의존 그래프 기초는 [01-complexity](../01-complexity/2-summary.md).
- **불리언 매개변수의 경로 수**: 독립 플래그 k개는 실행 경로를 최대 2^k로 늘린다. 경로 수 측정(NPath)과 순환 복잡도는 [52-complexity-metrics](../52-complexity-metrics/2-summary.md).
- **공동 변경 집계(co-change)**: `git log`에서 두 파일이 같은 커밋에 함께 나온 횟수. "함께 바뀌나"를 이력으로 재는 방법이다. 지지도·신뢰도로 확장한 것은 [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md).
- **인라인 + 상수 전파 + 죽은 분기 제거**: Metz의 되돌리기 ①②는 컴파일러가 하는 인라이닝 → 상수 접기 → 도달 불가 코드 제거와 같은 구조다. 호출처가 넘기는 상수(`refund=false`)를 본문에 대입하면 그 호출처에서 실행될 수 없는 분기가 드러난다.

## 적용 — 풀어나가는 법

1. **중복을 발견하면 세 질문**: 같은 지식인가? 실제로 함께 바뀌어 왔나? 몇 번째 사례인가?
2. **"함께 바뀌었나"를 이력으로 확인한다.** 두 파일이 같은 커밋에 몇 번 나왔는지 센다.

```bash
# 두 파일이 함께 바뀐 커밋 수 / 각자 바뀐 커밋 수
a=src/main/java/.../Receipt.java; b=src/main/java/.../SettlementReport.java
both=$(comm -12 <(git log --format=%h -- "$a" | sort) <(git log --format=%h -- "$b" | sort) | wc -l)
echo "함께 $both / A $(git log --format=%h -- "$a" | wc -l) / B $(git log --format=%h -- "$b" | wc -l)"
```

3. **지식 중복이면 둘째 사례에서도 모은다.** 세율·검증 규칙·상태 전이 같은 규칙은 이름 붙은 한 곳(`Vat.of`)으로. 흩어진 같은 지식은 "하나 빠뜨림"으로 실패한다(실험 관찰 3).
4. **모양만 같으면 셋째 사례까지 기다린다.** 둘째 사례에서는 복사하고, 차이점을 주석이나 테스트로 남겨 둔다.
5. **잘못된 추상화 신호를 찾는다.** 공통 함수 호출에 `true`/`false` 리터럴이 줄지어 있으면 의심한다.

```bash
# 불리언 리터럴을 두 개 이상 넘기는 호출 찾기
grep -rnE "\w+\([^)]*\b(true|false)\b[^)]*\b(true|false)\b" --include=*.java src/
```

6. **되돌린다(Metz 순서).** IDE의 Inline Method로 모든 호출처에 펼친다 → 호출처마다 넘기던 상수로 분기를 지운다 → 테스트 → 남은 것 중 지식 중복만 Extract Method.

```java
// 전: 정산 호출처
static String row(long won) { return AmountText.format(won, false, true, true); }
// 후: 정산이 실제로 실행하던 코드만 남기고, 공유 지식(부가세)만 호출
static String row(long won) {
  return String.format("[정산] %s / 부가세 %s", paren(won), paren(Vat.of(won)));
}
```

7. **여러 팀이 공유하는 "공통 모듈"**: 각 팀이 실제로 쓰는 부분을 확인한다. 진짜 공유 지식만 남기고 나머지는 각 팀 코드로 가져간다(복제). 남긴 부분에는 소유 팀을 정한다.

## 장애 시나리오와 대처

### 1. 플래그가 쌓인 공통 함수 — 한 호출처를 고치면 다른 호출처가 깨진다 (⚠ 커리큘럼)

- 현상: 공통 함수에 boolean·type 인자가 5개 붙고 내부 `if`가 12개다. 정산 화면 요구를 반영했더니 환불 영수증이 이상해졌다.
- 보이는 형태: 바뀌지 않은 화면의 회귀 테스트 실패(`FAIL 환불영수증 got=(12,000원)...`). 테스트가 없으면 고객 문의로 처음 드러난다. 리뷰 diff에는 공통 함수 한 파일만 보여 영향이 안 보인다.
- 원인: 서로 다른 지식이 한 함수에 묶여 있다. 수정 한 줄이 fan-in 전체에 퍼진다(실험 관찰 2).
- 대처: 당장은 호출처별 회귀 테스트를 붙인다. 근본적으로는 인라인 후 재추출로 되돌린다. 매개변수를 더 붙이는 방향으로 고치지 않는다.

### 2. 팀 셋이 공유하는 "공통 모듈"을 아무도 못 고친다 (⚠ 커리큘럼)

- 현상: `common-util`의 함수 하나를 바꾸려면 세 팀의 승인이 필요하다. 결국 각 팀이 자기 쪽에 우회 코드를 쌓는다.
- 보이는 형태: 공통 모듈 PR이 몇 주씩 열려 있다. 같은 기능의 `XxxUtil2`, `XxxHelper`가 늘어난다.
- 원인: 공유 이유가 "같은 지식"이 아니라 "비슷한 모양"이었다. 결합만 남았다.
- 대처: 팀별로 실제 쓰는 경로를 확인해 가져가고(복제), 진짜 공유 규칙만 남긴다. 남긴 모듈은 소유 팀과 버전 정책을 정한다. 서비스 경계의 의도적 중복 판단은 원본 [engineering/clean-code](../../engineering/clean-code/2-summary.md) 「의도적 중복이 정당한 경우」.

### 3. 둘째 사례에서 뽑은 추상화가 셋째 사례에 안 맞는다 (⚠ 커리큘럼)

- 현상: 두 사례를 보고 만든 인터페이스에 셋째 사례를 넣으려니 매개변수가 늘고 "이 경우엔 무시" 인자가 생긴다.
- 보이는 형태: `null`이나 기본값을 넘기는 호출처가 생긴다. 인터페이스 구현 중 일부가 `UnsupportedOperationException`을 던진다.
- 원인: 두 사례만으로는 변하는 축을 한 번밖에 확인하지 못했다.
- 대처: 셋째 사례를 일단 복사로 구현하고, 세 사례를 나란히 놓고 공통점을 다시 뽑는다. 이미 퍼졌다면 4절의 되돌리기.

### 4. 반대 실패 — 같은 지식을 흩어 두어 하나를 빠뜨린다

- 현상: 세율 변경 후 영수증과 정산 리포트의 부가세가 1원 다르다.
- 보이는 형태: 정산 대사(대조) 불일치, 화면 간 숫자 차이. 테스트가 화면별로만 있으면 통과할 수도 있다.
- 원인: 함께 바뀌어야 하는 규칙이 세 곳에 복사돼 있었다(실험 `dup-cr2-miss`).
- 대처: 규칙을 이름 붙은 한 곳으로 모은다. 모으기 전이라도 "세 화면의 부가세가 같다"는 교차 테스트를 둔다.

## 핵심 문장

- 추상화 시점의 기준은 글자 중복이 아니라 "같은 지식인가, 함께 바뀌나"다. 『The Pragmatic Programmer』의 DRY도 지식의 중복을 말한다.
- 모양만 같은 중복은 셋째 사례까지 기다린다(Rule of Three). 같은 규칙의 중복은 둘째 사례에서도 모으는 편이 싸다.
- 공유 코드에 매개변수와 조건을 더하고 있다면 그 추상화는 이미 틀렸다. Metz: 잘못된 추상화보다 중복이 훨씬 싸다.
- 되돌리는 순서는 인라인 → 호출처별로 안 쓰는 분기 삭제 → 진짜 공유 지식만 재추출이다.
- 실험에서 플래그 공통 함수는 한 호출처만의 요구에 4파일을 고쳤고, 흩어진 부가세 규칙은 3파일 중 하나를 빠뜨려 1원이 어긋났다. 지식만 뽑은 설계는 두 요구 모두 1파일이었다.

## 관련 주제·근거

- 선행
  - [06-clean-code](../06-clean-code/2-summary.md) — CLEAN의 N(비중복)과 다른 속성의 긴장
  - 원본 [engineering/clean-code](../../engineering/clean-code/2-summary.md) 「N — 비중복」 — 우연한 중복 vs 진짜 중복, 서비스 경계의 의도적 중복
  - [10-code-smells](../10-code-smells/2-summary.md) — Duplicated Code·Speculative Generality 스멜
- 후속·연결
  - [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) — "중복 없음"은 단순 설계 4규칙의 셋째, 확장점은 둘째 요구 때
  - [13-refactoring](../13-refactoring/2-summary.md) — Inline Function·Extract Function을 작은 단계로
  - [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) — 조건문을 패턴으로, 패턴에서 멀어지기
  - [52-complexity-metrics](../52-complexity-metrics/2-summary.md) — 플래그가 늘린 경로 수
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 공동 변경으로 숨은 결합 찾기
- 글·문서
  - Sandi Metz, "The Wrong Abstraction", 2016-01-20 <https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction>
  - Andy Hunt·Dave Thomas, 『The Pragmatic Programmer』 20주년판, 「The Evils of Duplication」(Tip 15, "Not All Code Duplication is Knowledge Duplication") — 출판사 발췌 PDF <https://media.pragprog.com/titles/tpp20/dry.pdf>
  - Martin Fowler, 『Refactoring』 2판(2018) 2장 「When Should We Refactor?」 — 출판사 미리보기 PDF 목차로 절 위치 확인. Rule of Three(Don Roberts) 문구는 1판 2장 인용으로 확인(2차 출처 <https://eoinnoble.com/posts/origins-of-the-rule-of-three/>), 2판 「The Rule of Three」 문구는 독자 노트로 확인(2차 출처 <https://gist.github.com/wataruoguchi/fa527cf25ec41f48c7c335d6ccd7c2fa>)
  - Martin Fowler, "BeckDesignRules", 2015-03-02 — DRY·Once and Only Once <https://martinfowler.com/bliki/BeckDesignRules.html>
  - refactoring.com 카탈로그(Inline Function, Extract Function) <https://refactoring.com/catalog/>
- 실험 목록 (코드: scratchpad `sd/11/e11/build.sh`·`measure.sh`, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, PMD 7.28.0)
  - 세 설계(DUP·ABS·RIGHT) × 두 요구(CR1 한 호출처 전용·CR2 공유 지식)의 `git diff --stat`, 테스트 결과, 지식이 쓰인 파일 수, PMD 순환 복잡도
