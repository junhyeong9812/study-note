# software-design/13-refactoring — 리팩터링: 동작 보존 변환·작은 단계·테스트 안전망 — 정리 (힌트)

## 해결하는 문제

코드 구조를 고치고 싶다. 그런데 고치는 동안 동작이 바뀌면 안 된다. 바뀌었는데 아무도 모르면 더 나쁘다.

```text
 리팩터링 없이 기능만 덧붙임            큰 한 방 "재작성"                  작은 단계 리팩터링
 구조가 계속 나빠짐                    며칠 동안 빌드가 깨진 채 작업        단계마다: 바꾸기 → 컴파일 → 테스트 → 커밋
 다음 변경이 점점 비싸짐                머지 때 충돌·의미 충돌 폭발          틀리면 마지막 초록 커밋으로 되돌림
                                     동작이 바뀌어도 어느 줄인지 모름     바뀐 단계가 2~3줄짜리라 원인이 바로 보임
```

- *리팩터링(명사)*: 관찰 가능한 동작을 바꾸지 않으면서, 이해하기 쉽고 고치기 싸도록 소프트웨어 내부 구조를 바꾸는 것(Fowler "DefinitionOfRefactoring", 2004).
- *리팩터링(동사)*: 그런 리팩터링을 연달아 적용해 구조를 바꾸는 것(같은 글).
- *관찰 가능한 동작*: 바깥에서 보이는 결과(반환값·출력·부수효과). 내부 변수 이름·함수 경계는 포함하지 않는다.

쉬운 예: 이삿짐을 옮기며 방을 정리한다. 한 번에 상자 하나만 옮기고, 옮길 때마다 "물건이 다 있나" 목록과 대조한다. 없어진 물건이 생기면 방금 옮긴 상자만 보면 된다.\
똑같은 구조다.\
실무 예: 영수증 계산 코드를 다듬는다. 이름 바꾸기·함수 추출·반복문 쪼개기를 하나씩 하고, 매번 300건짜리 골든 출력과 비교한다.

## 동작·원리

### 1. 정의의 핵심 — 동작 보존

```text
  구조 변경 ──────┐
                  ├──> 같은 입력 → 같은 출력이면 리팩터링
  (이름·함수·클래스 │
   경계·순서)      └──> 출력이 하나라도 다르면 리팩터링이 아니다 (동작 변경)
```

- 정의에 "without changing its observable behavior"가 두 번 들어 있다(명사·동사 정의 모두).
- 그래서 "구조를 개선하면서 버그도 고쳤다"는 리팩터링이 아니다. 둘을 나누는 이유와 방법은 [14-tidy-first](../14-tidy-first/2-summary.md).
- 『Refactoring』 2판(2018) 2장 「Principles in Refactoring」에는 「Defining Refactoring」·「The Two Hats」·「When Should We Refactor?」·「Problems with Refactoring」·「Refactoring and Performance」 절이 있다(출판사 미리보기 PDF 목차로 확인). 「The Two Hats」는 기능 추가와 리팩터링을 번갈아 하되 한 번에 한 모자만 쓴다는 Beck의 비유로 알려져 있다 — 본문은 열지 못했다 [?].

### 2. 작은 단계 루프

```text
     ┌──────────────────────────────────────────────┐
     v                                              │
  [작은 변환 1개] ─> 컴파일 ─> 테스트 ─ 초록 ─> 커밋 ─┘
                               │
                               빨강 → 원인이 바로 안 보이면
                                      마지막 초록 커밋으로 되돌리고 더 작게 다시
```

- Fowler 2판 1장의 작업 방식(미리보기 본문으로 확인):
  - "Refactoring changes the programs in small steps, so if you make a mistake, it is easy to find where the bug is."
  - 리팩터링이 하나 성공할 때마다 로컬에 커밋한다. 공유 저장소에 push하기 전에 더 의미 있는 커밋으로 squash한다.
  - 테스트가 실패하고 바로 원인이 안 보이면 마지막 good 커밋으로 되돌리고 더 작은 단계로 다시 한다. "small steps are the key to moving quickly".
- *카탈로그 리팩터링*: 이름과 절차가 정해진 변환. 예: Extract Function, Inline Function, Rename Variable, Split Loop, Change Function Declaration([refactoring.com 카탈로그](https://refactoring.com/catalog/)).

### 3. 테스트 안전망

```text
  자기 검증 테스트 (self-checking)
  ┌─────────────────────────────────────┐
  │ 실행 → 기대값과 자동 비교 → 초록/빨강 │   사람이 눈으로 값을 대조하지 않는다
  └─────────────────────────────────────┘
  특성 테스트 / 골든 마스터
  ┌─────────────────────────────────────────────────────┐
  │ 리팩터링 "전" 출력을 기록 → 리팩터링 "후" 출력과 비교 │   명세를 몰라도 "지금 동작"을 고정한다
  └─────────────────────────────────────────────────────┘
```

- Fowler 2판 1장 「The First Step in Refactoring」: "Before you start refactoring, make sure you have a solid suite of tests. These tests must be self-checking." 테스트 만드는 법은 4장 「Building Tests」.
- *특성 테스트(characterization test)*: 코드가 지금 실제로 하는 일을 기록해 고정하는 테스트. 맞는 동작인지가 아니라 **바뀌었는지**를 본다(레거시 쪽 기법은 [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md)).
- 행복 경로 테스트 하나는 안전망이 되기 어렵다. 아래 실험 A에서 행복 경로 테스트는 동작 변경 뒤에도 초록이었다.

### 실험 A: "같아 보이는" 한 단계가 동작을 바꾼다 — 누가 잡고, 어디서 찾나

영수증 계산을 다섯 단계로 다듬었다. 4단계는 "부가세 반올림을 한 곳으로 모으기"다. 줄마다 반올림해 더하던 것을, 합계에서 한 번 반올림하도록 바꿨다.

```java
// 시작: 줄마다 부가세 포함 금액을 반올림해 더한다
long withTax = Math.round(a * 1.1);
t += withTax;
// 4단계 뒤: 합계에서 한 번만 반올림 — 같아 보이지만 다르다
total += a;
...
total = Math.round(total * 1.1);
```

- 테스트 둘: 행복 경로 1건(`책` 1권 10,000원)과 골든 마스터 300건(고정 시드 42로 만든 장바구니, 리팩터링 전 출력을 `golden.txt`에 기록).

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, `scratchpad/sd/11/e13/build.sh`·`measure.sh`, 2026-10-02)

```text
=== 단계마다 테스트 (행복 경로 1건 / 골든 300건) ===
1 Rename Variable: t→total, pts→points: HAPPY PASS / GOLDEN PASS (300건 동일)
2 Extract Function: amountFor: HAPPY PASS / GOLDEN PASS (300건 동일)
3 Split Loop: points: HAPPY PASS / GOLDEN PASS (300건 동일)
4 Consolidate tax rounding: HAPPY PASS / GOLDEN FAIL: 300건 중 72건 다름
5 Extract Function: pointsFor: HAPPY PASS / GOLDEN FAIL: 300건 중 72건 다름
=== git bisect run (작은 단계) ===
f65e2dea38e51641666b6ac6481e1322443614a1 is the first bad commit
    4 Consolidate tax rounding
=== 범인 커밋의 크기 ===
--- 작은 단계 4번:
 Receipt.java | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
--- 큰 한 방:
 Receipt.java | 26 ++++++++++++++++++--------
 1 file changed, 18 insertions(+), 8 deletions(-)
```

골든이 처음 보여 준 차이(영수증 #8):

```text
기대:            실제:
p0 30378         p0 30378
p1 67696         p1 67696
p2 106696        p2 106696
합계 204770      합계 204769
포인트 184       포인트 184
```

- 관찰 1 — 행복 경로 테스트는 다섯 단계 내내 초록이었다. 한 줄짜리 장바구니에서는 "줄마다 반올림"과 "합계에서 반올림"이 같다. 테스트가 이것뿐이었다면 동작 변경이 조용히 들어갔다.
- 관찰 2 — 골든 300건 중 72건이 달라졌다. 차이는 합계 1원이다. 줄마다 찍힌 금액의 합(204,770)과 합계 줄(204,769)이 영수증 안에서 맞지 않게 됐다.
- 관찰 3 — 단계마다 커밋해 두었기 때문에 `git bisect run`이 4단계를 짚었다. 범인 커밋은 2줄 추가·1줄 삭제다. 같은 최종 코드를 한 커밋으로 만든 "큰 한 방"에서는 범인 후보가 26줄 전체다.
- 4단계는 카탈로그 리팩터링이 아니다. 산술상 Σ round(xᵢ)와 round(Σ xᵢ)는 같지 않을 수 있어(실험에서 300건 중 72건) 동작을 바꾼다. 이름만 리팩터링 같은 변경이 섞이는 것이 실무에서 흔한 사고다(해석).

### 실험 B: 오래 사는 큰 리팩터링 브랜치 vs 작게 먼저 합치기

`Price.calcPrice(unit, qty)`를 `priceOf(qty, unit)`로 바꾸는 Change Function Declaration이다. 호출처 18곳을 한 커밋에서 바꾼 브랜치를, 그동안 main에 들어간 기능 커밋 3개(기존 호출 줄 수정 2개, `calcPrice`를 부르는 새 파일 1개) 뒤에 머지했다.

```java
// 대안 B의 expand 단계: 새 이름을 더하고, 옛 이름은 위임으로 남긴다 (1파일)
static long priceOf(int qty, long unit) { return unit * qty; }
@Deprecated static long calcPrice(long unit, int qty) { return priceOf(qty, unit); }
```

(실험, 같은 환경, `scratchpad/sd/11/e13/build-merge.sh`·`measure-merge.sh`, 2026-10-02)

```text
=== A. 큰 리팩터링 브랜치(호출처 18곳 한 커밋)를 기능 3개 뒤에 머지 ===
 7 files changed, 19 insertions(+), 19 deletions(-)
CONFLICT (content): Merge conflict in CartService.java
CONFLICT (content): Merge conflict in InvoiceService.java
CONFLICT (content): Merge conflict in OrderService.java
충돌 파일 수: 3
충돌을 손으로 풀었다고 치고(충돌 파일만 리팩터링 쪽 + 기능 재적용 생략) 컴파일하면:
  BulkService.java:2: error: cannot find symbol
  javac exit=1
=== B. expand 만 먼저 합치고(1파일), 기능 브랜치를 머지 ===
 1 file changed, 3 insertions(+), 1 deletion(-)
충돌 파일 수: 0
  javac exit=0
```

- 관찰 1 — A는 텍스트 충돌 3파일이 났다. 기능이 고친 줄과 리팩터링이 고친 줄이 겹쳤다.
- 관찰 2 — 충돌이 **없던** `BulkService.java`가 컴파일을 깨뜨렸다. 기능 브랜치가 새로 만든 호출이 옛 이름을 쓴다. 텍스트 머지는 성공해도 의미가 충돌한다(*의미 충돌, semantic conflict*).
- 관찰 3 — B는 새 이름만 더한 1파일 커밋을 먼저 합쳤다. 충돌 0, 컴파일 성공. 이 커밋은 호출처를 건드리지 않으니 기능이 고친 줄과 겹칠 일이 없다. 옛 이름을 위임으로 남겨 `BulkService`의 의미 충돌도 생기지 않았다. 호출처는 이후 작은 커밋으로 옮기고, 다 옮긴 뒤 옛 이름을 지운다(expand → migrate → contract, [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md)).

이어서 migrate 단계를 따로 쟀다. 같은 파일별 이전 커밋을 (1) 최신 main(기능·expand 반영 뒤)에서 만들어 바로 합친 경우와 (2) 기능 머지 전 expand 시점에 만들어 두었다가 나중에 합친 경우다.

(실험, 같은 환경, `scratchpad/sd/adj-13/migrate.sh`, 2026-10-02)

```text
=== B-migrate(1): 기능·expand 가 다 합쳐진 최신 main 에서 파일 하나씩 옮겨 바로 합침 ===
OrderService:  1 file changed, 3 insertions(+), 3 deletions(-)
(… Cart·Invoice·Refund·Quote·Report 도 각각 1 file, +3/−3 …)
BulkService:  1 file changed, 1 insertion(+), 1 deletion(-)
남은 calcPrice 호출: 0 파일
  javac exit=0
contract:  1 file changed, 2 deletions(-)
  javac exit=0
=== B-migrate(2): 같은 migrate 커밋을 기능 머지 전(expand 시점)에 만들어 두고 나중에 합침 ===
OrderService: 충돌 1파일, 충돌 구간 1
CartService: 충돌 1파일, 충돌 구간 1
InvoiceService: 충돌 1파일, 충돌 구간 1
RefundService: 충돌 0
QuoteService: 충돌 0
ReportService: 충돌 0
```

- 관찰 4 — migrate 커밋도 기능이 고친 줄을 바꾸므로, 낡은 기준에서 만들면 A와 같은 세 파일에서 충돌한다(2). 작게 나눈다고 충돌이 저절로 사라지지는 않는다.
- 관찰 5 — 최신 main에서 파일 하나씩 옮겨 바로 합치면 충돌 0이고, 단계마다 컴파일이 됐다(1). 새로 생긴 `BulkService`도 이전 대상에 들어가 contract 뒤에도 `javac exit=0`이었다. 차이를 만든 것은 "작게"보다 "최신 기준에서 짧게 살다 합치기"다. 충돌이 나더라도 한 번에 한 파일·한 구간으로 작다(해석).
- 이 실험의 A에서 충돌을 "리팩터링 쪽"으로만 풀면 기능 1·3의 변경이 사라진다. 실제 해결은 충돌마다 두 의도를 합쳐야 하고, 그 작업량이 충돌 수에 비례한다(해석).

## 쓰이는 자료구조·알고리즘

- **AST와 심볼 테이블**: IDE의 자동 리팩터링(Rename, Extract Method)은 텍스트 치환이 아니라 구문 트리와 이름 해석(어떤 식별자가 어떤 선언을 가리키나)을 바탕으로 바꾼다. 그래서 같은 이름의 다른 변수는 건드리지 않는다. 텍스트 `sed`는 이를 모른다(실험 B의 sed 치환은 예제가 작아서 성립했다).
- **이분 탐색(`git bisect`)**: 좋은 커밋과 나쁜 커밋 사이 n개를 테스트 log₂n회 정도로 좁힌다. 커밋이 작을수록 찾은 범인 커밋 안에서 다시 찾을 범위가 작다(실험 A: 3줄 vs 26줄).
- **3-way 머지(공통 조상 기준 diff3)**: 두 브랜치가 공통 조상에서 같은 줄 영역을 바꾸면 충돌이다. 줄 단위 비교라 "다른 파일의 새 호출이 옛 이름을 쓴다"는 의미 충돌은 잡지 못한다(실험 B 관찰 2).
- **골든 마스터 = 출력 스냅샷 비교**: 입력 집합(고정 시드 난수)의 출력을 통째로 저장하고 비교한다. 입력 공간을 넓게 덮을수록 실험 A 같은 경계(여러 줄 장바구니)를 잡을 확률이 오른다.
- **의존 그래프(호출처 목록)**: Change Function Declaration의 영향 범위 = 그 함수를 부르는 모든 노드. 호출처가 많으면 한 번에 바꾸지 말고 expand/contract로 나눈다.

## 적용 — 풀어나가는 법

1. **안전망부터 확인한다.** 바꿀 코드를 덮는 자기 검증 테스트가 있나? 없으면 특성 테스트(골든 마스터)를 먼저 만든다. 입력은 경계(빈 목록·여러 줄·할인 문턱)를 섞어 넓게 만든다.
2. **카탈로그 단위로 한 번에 하나.** 가능한 한 IDE 자동 리팩터링을 쓴다(사람 실수가 줄어든다).
3. **단계마다 컴파일·테스트·커밋.** 실패하고 원인이 바로 안 보이면 고치려 들지 말고 되돌린다.

```bash
git add -A && git commit -qm "Extract Function: amountFor"    # 단계마다 로컬 커밋
git reset --hard HEAD        # 방금 단계를 버리고 마지막 초록으로 (로컬·미공유 커밋에서만)
git bisect start HEAD <마지막으로 확실히 좋던 커밋> && git bisect run ./check.sh   # 어느 단계였나
```

4. **"같아 보이는" 변환을 의심한다.** 반올림 위치, 평가 순서, 부수효과가 있는 호출의 횟수, 예외 시점, `equals`/`hashCode`를 바꾸는 변경은 동작 변경일 수 있다. 골든 마스터가 잡아 준다.
5. **공유 전에 정리.** 로컬의 잘게 나눈 커밋은 push 전에 의미 단위로 squash해도 된다(Fowler 1장). 다만 구조 변경과 동작 변경은 서로 다른 커밋으로 남긴다([14-tidy-first](../14-tidy-first/2-summary.md)).
6. **호출처가 많은 시그니처 변경은 나눈다.** expand(새 것 추가, 옛 것은 위임) → migrate(호출처를 여러 작은 PR로) → contract(옛 것 삭제). 오래 사는 리팩터링 브랜치를 만들지 않는다.
7. **판단층은 다른 노트로.** 언제 정리하나(14), 테스트 없는 레거시를 어떻게 여나(51), 어디부터 하나(53 핫스팟), 잘못된 추상화를 어떻게 되돌리나([11](../11-when-to-abstract/2-summary.md)).

## 장애 시나리오와 대처

### 1. 테스트 없이 리팩터링 → 조용한 동작 변경 (⚠ 커리큘럼)

- 현상: "구조만 바꿨다"는 배포 뒤 정산 대사에서 합계가 1원씩 안 맞는 건이 나온다.
- 보이는 형태: 에러·예외 없음. 영수증의 줄 금액 합과 합계 줄이 다르다. 행복 경로 테스트는 초록(실험 A 관찰 1).
- 원인: 반올림 위치를 옮기는 "같아 보이는" 변환이 동작을 바꿨다. 이를 잡을 넓은 입력의 테스트가 없었다.
- 대처: 리팩터링 전 골든 마스터로 지금 동작을 고정한다. 이미 배포됐다면 단계별 커밋에서 `git bisect run`으로 범인 단계를 찾아 되돌린다.

### 2. 큰 한 방 리팩터링 → 머지 지옥 (⚠ 커리큘럼)

- 현상: 몇 주 산 리팩터링 브랜치를 합치려니 충돌이 쏟아진다. 충돌을 다 풀었는데 빌드가 깨진다.
- 보이는 형태: `CONFLICT (content)` 여러 파일, 충돌 없던 파일에서 `cannot find symbol`(실험 B 관찰 2).
- 원인: 리팩터링과 기능 개발이 같은 줄·같은 이름을 동시에 바꿨다. 줄 단위 머지는 이름 바뀜을 모른다.
- 대처: 리팩터링을 작게 쪼개 최신 main에서 만들어 자주 합친다(쪼개도 낡은 기준에서 만들면 충돌한다 — 실험 B 관찰 4). 시그니처 변경은 expand/contract로. 이미 큰 브랜치라면 main을 자주 당겨 오고 충돌을 작게 나눠 푼다.

### 3. 단계가 커서 무엇이 동작을 바꿨는지 못 찾는다

- 현상: 골든 테스트가 실패했는데 diff가 수백 줄이라 원인 줄을 못 찾는다.
- 보이는 형태: `git bisect`가 거대한 커밋 하나를 가리킨다(실험 A: 26줄 vs 3줄).
- 원인: 단계마다 커밋하지 않았다.
- 대처: 변경을 버리고 마지막 초록에서 더 작은 단계로 다시 한다(Fowler 1장의 대처). 고치려고 버티는 시간이 다시 하는 시간보다 길어지기 쉽다.

### 4. 리팩터링 커밋에 동작 변경이 섞여 리뷰·되돌리기가 어렵다

- 현상: "리팩터링" PR에 버그 수정이 들어 있었다. 나중에 그 수정만 되돌릴 수 없다.
- 보이는 형태: 리뷰에서 rename 수백 줄 사이의 로직 한 줄을 놓친다. revert하면 정리까지 사라진다.
- 원인: 구조 변경과 동작 변경을 한 커밋에 넣었다.
- 대처: 커밋·PR을 나눈다. 실험과 절차는 [14-tidy-first](../14-tidy-first/2-summary.md).

## 핵심 문장

- 리팩터링은 관찰 가능한 동작을 바꾸지 않고 내부 구조를 바꾸는 것이다(Fowler). 출력이 하나라도 바뀌면 리팩터링이 아니다.
- 리팩터링 전에 자기 검증 테스트를 갖춘다. 행복 경로 하나는 안전망이 아니다 — 실험에서 행복 경로는 동작 변경 뒤에도 초록이었고, 골든 300건은 72건 차이를 잡았다.
- 작은 단계마다 컴파일·테스트·커밋한다. 틀리면 마지막 초록으로 되돌리고 더 작게 다시 한다.
- 작게 커밋해 두면 `git bisect`가 범인 단계를 짚고, 그 단계는 2~3줄이다.
- 호출처가 많은 변경을 한 브랜치에 오래 묶으면 텍스트 충돌과 의미 충돌이 같이 온다. expand → migrate → contract로 나눠 자주 합친다.

## 관련 주제·근거

- 선행
  - [10-code-smells](../10-code-smells/2-summary.md) — 어디를 리팩터링할지 알려 주는 냄새
  - testing 영역 02 good-unit-tests — 리팩터링 내성이 있는 테스트([testing/README](../../testing/README.md), 미작성)
- 후속·판단층
  - [14-tidy-first](../14-tidy-first/2-summary.md) — 구조 변경과 동작 변경 분리, 언제 정리하나
  - [11-when-to-abstract](../11-when-to-abstract/2-summary.md) — 잘못된 추상화를 인라인으로 되돌리기
  - [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md) — 테스트 없는 코드의 seam·특성 테스트·parallel change
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 리팩터링 우선순위
  - testing 영역 17 characterization-tests-legacy([testing/README](../../testing/README.md), 미작성)
- 글·문서
  - Martin Fowler, 『Refactoring: Improving the Design of Existing Code』 2판(Addison-Wesley, 2018) — 1장(작은 단계·테스트·커밋 흐름), 2장(정의·Two Hats·When/Problems), 4장(Building Tests). 출판사 미리보기 PDF로 목차와 1장 일부 본문 확인 <https://api.pageplace.de/preview/DT0400.9780134757698_A35687787/preview-9780134757698_A35687787.pdf>
  - Martin Fowler, "DefinitionOfRefactoring", 2004-09-01 <https://martinfowler.com/bliki/DefinitionOfRefactoring.html>
  - refactoring.com 카탈로그 <https://refactoring.com/catalog/>
  - git 문서 `git bisect` <https://git-scm.com/docs/git-bisect>
- 실험 목록 (JDK 21.0.12 temurin `--cpus=2`, git 2.43.0)
  - A: 작은 단계 5개 × (행복 경로 1건 / 골든 300건), `git bisect run`, 범인 커밋 크기 vs 큰 한 방 — scratchpad `sd/11/e13/build.sh`·`measure.sh`·`check.sh`
  - B: 큰 리팩터링 브랜치 머지(텍스트 충돌·의미 충돌) vs expand 먼저 합치기 — `sd/11/e13/build-merge.sh`·`measure-merge.sh`; migrate 단계(최신 main에서 파일별 이전 vs 낡은 기준에서 만든 이전) — `sd/adj-13/migrate.sh`
