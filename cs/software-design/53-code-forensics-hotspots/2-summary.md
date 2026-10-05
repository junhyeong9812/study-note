# software-design/53-code-forensics-hotspots — 코드 포렌식: 핫스팟·change coupling·지식 분포 — 정리 (힌트)

## 해결하는 문제

리팩터링할 시간이 2주 생겼다. 50만 줄 중 어디부터 고칠까?

```text
 코드만 보고 고르면                         이력까지 보고 고르면
 "제일 큰 파일 LegacyReport.java(2000줄)"    "자주 바뀌면서 복잡한 PriceEngine.java"
       │                                          │
       v                                          v
 3년 동안 3번 바뀐 파일 → 고쳐도 아낄 시간이 없다   매주 바뀌는 파일 → 고친 효과가 매주 돌아온다
```

- *기술 부채의 이자*: 나쁜 코드 자체가 비용이 아니다. 그 코드를 **고칠 때마다** 더 드는 시간이 비용이다. 안 바뀌는 코드의 복잡도는 이자가 거의 없다. 이 비유는 Tornhill(『Software Design X-Rays』 2장 「Identify Code with High Interest Rates」)의 관점이다(주장).
- *코드 포렌식(behavioral code analysis)*: 코드 내용 대신 버전 관리 이력(누가·언제·무엇을 함께 바꿨나)을 데이터로 분석하는 방법. Tornhill 『Your Code as a Crime Scene』(2판 2024)·『Software Design X-Rays』(2018)가 정리했다.

복잡도 지표(52)는 "이 코드가 얼마나 어렵나"를 말한다. 이력은 "이 코드에 얼마나 자주 손이 가나"와 "무엇이 함께 바뀌나", "누가 아나"를 말한다.

쉬운 예: 도로 보수 예산은 포장이 제일 낡은 길이 아니라, 낡았으면서 차가 많이 다니는 길에 먼저 쓴다.\
똑같은 구조다.\
실무 예: 정산 팀이 "전면 리팩터링" 계획을 세우기 전에 `git log`로 최근 1년 변경 빈도를 뽑고, 복잡한 파일과 겹치는 상위 몇 개만 고른다.

## 동작·원리

### 1. 핫스팟 = 변경 빈도 × 복잡도

```text
 복잡도 ^
        │  LegacyReport            PriceEngine  ← 핫스팟(오른쪽 위)
        │  (크지만 안 바뀜)           (복잡 + 자주 바뀜)
        │
        │                               Order
        │                       StringUtil  (자주 바뀌지만 단순)
        └────────────────────────────────────────> 변경 빈도(커밋 수)
```

- *핫스팟(hotspot)*: 변경 빈도와 복잡도가 모두 높은 파일(또는 함수). 리팩터링·리뷰·테스트를 먼저 투자할 후보다.
- 변경 빈도: 기간 안에 그 파일을 건드린 커밋 수. `git log --numstat`로 센다.
- 복잡도: 줄 수, 순환 복잡도(52), 또는 **들여쓰기 모양**. Tornhill 2판 목차에 「Calculate Complexity Trends from Your Code's Shape」 절이 있다(본문 미열람 — 들여쓰기 합을 복잡도 근사로 쓰는 방식은 이 실험에서 이 노트가 정의해 쓴다).
- Tornhill 2판 목차 절 「Be Aware That Hotspots Reflect Probabilities」, 『X-Rays』 목차 「Identify Code with High Interest Rates」·「Prioritize Technical Debt with Hotspots」. 핫스팟은 **확률적 우선순위**다. 결함이 거기 있다는 증명이 아니다.

### 2. change coupling — 함께 바뀌는 파일

```text
 커밋 이력                         공동 변경 행렬(대칭)
 c1: Order, OrderMapper                    Order  OrderMapper  StringUtil
 c2: Order, OrderMapper           Order      –        55          0
 c3: Order                        OrderMapper 55       –           0
 c4: StringUtil                   StringUtil  0        0           –
 ...
```

- *change coupling(logical·temporal coupling)*: 같은 커밋에 반복해서 함께 나타나는 파일 쌍. 코드에 import가 없어도 "하나를 바꾸면 다른 것도 바꿔야 하는" 숨은 결합을 드러낸다.
- code-maat(Tornhill의 오픈소스 도구) `logical_coupling.clj`의 식: **degree = 공동 커밋 수 ÷ 두 파일 커밋 수의 평균 × 100**.
- code-maat 1.0.4 README의 기본 거르기: `--min-revs 5`(파일 변경 5회 이상), `--min-shared-revs 5`(공동 5회 이상), `--min-coupling 30`(30% 이상), `--max-changeset-size 30`(파일 30개 넘게 바뀐 커밋은 coupling 분석에서 제외).
- 연관 규칙 용어로 보면 다음과 같다(이 노트가 함께 계산해 보이는 값).
  - *지지도(support)*: 공동 커밋 ÷ 전체 커밋. 그 쌍이 얼마나 흔한가.
  - *신뢰도(confidence) A→B*: 공동 커밋 ÷ A의 커밋. "A가 바뀌면 B도 바뀔 확률". 방향이 있다.

### 3. 지식 분포 — 누가 아나

```text
 TokenStore.java   dev-e ██████████ 10/10        ← 혼자만 아는 파일(지식 섬)
 Order.java        dev-b ████ 19/60, 나머지 4명 분산
```

- *주 작성자(main developer)*: 그 파일에 가장 많이 기여한 사람. code-maat는 추가 줄 수 기준(`main-dev`)과 커밋 수 기준(`main-dev-by-revs`)을 따로 둔다.
- *버스 팩터(truck factor)*: 몇 명이 빠지면 프로젝트의 상당 부분을 아는 사람이 없어지나. Tornhill 2판 목차에 「Measure the Truck Factor in Unhealthy Code」 절이 있다. 정의는 연구마다 다르다. 이 노트의 실험은 단순화한 자체 정의(아래)를 쓴다.

### 실험 E: 합성 저장소로 핫스팟·coupling·지식 분포 재기

seed 고정 스크립트로 커밋 205개짜리 git 저장소를 만들었다(파일 40개). 프로파일은 이렇다.
- PriceEngine 643줄·깊은 중첩·40회 변경(dev-a·dev-b)
- Order 363줄·60회, 그중 약 90%는 OrderMapper와 함께 변경
- LegacyReport 2006줄·3회
- StringUtil 83줄·30회
- TokenStore 213줄·dev-e만 10회
- 나머지 Misc 34개
- 대량 커밋 2개(최초 import, 전체 포매터 적용 — 각 40파일)

```bash
git log --format='--%h--%aN' --numstat --no-renames > git.log
java Forensics.java git.log repo 30        # 마지막 인자 = 최대 변경 세트 크기(이보다 큰 커밋 제외)
```

```java
// 핫스팟 점수(이 실험의 정의): (변경 수 / 최대 변경 수) × (들여쓰기 합 / 최대 들여쓰기 합)
static double score(String f, ...) { return (double) revs.get(f) / maxRev * cx.get(f)[1] / maxInd; }
// change coupling: code-maat와 같은 식
double degree = 100.0 * shared / ((revsA + revsB) / 2.0);
// 단순 버스 팩터: 가장 많은 파일을 건드린 사람부터 빼 나가며, '아는 사람 0명' 파일이 절반을 넘을 때의 인원
```

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-02 — 생성 seed 7 고정, `scratchpad/sd/50/e53/`)

```text
######## 최대 변경 세트 30
커밋 205개 중 변경 파일 > 30 인 커밋 2개 제외 → 203개 분석

== 핫스팟 = 변경 빈도 × 복잡도 (각각 최댓값으로 정규화한 곱)
  순위  점수  변경  줄수  들여쓰기합  파일
   1   0.20   40    643      2141   src/billing/PriceEngine.java
   2   0.12   60    363       811   src/order/Order.java
   3   0.05    3   2006      7000   src/report/LegacyReport.java
   4   0.03   55    178       236   src/order/OrderMapper.java
   5   0.01   10    213       410   src/auth/TokenStore.java
   6   0.01   30     83        81   src/util/StringUtil.java
  (참고) 줄 수 1위: src/report/LegacyReport.java — 핫스팟 순위 3위
  (참고) 변경 1위: src/order/Order.java — 핫스팟 순위 2위

== change coupling (공동 변경 ≥ 5, degree ≥ 30%) — degree = 공동 커밋 / 두 파일 변경 수의 평균 (code-maat 식)
  Order.java                   OrderMapper.java               공동 55  변경 60/55  degree  95%  지지도 0.271  신뢰도 Order.java→OrderMapper.java 0.92, 역 1.00
  조건을 넘은 쌍: 1개

== 지식 분포: 주 작성자 비율, 작성자 1명뿐인 파일
  PriceEngine.java               작성자 2명, 주 작성자 dev-a 30/40 (75%)
  Order.java                     작성자 4명, 주 작성자 dev-b 19/60 (32%)
  TokenStore.java                작성자 1명, 주 작성자 dev-e 10/10 (100%)
  작성자 1명뿐인 파일: [TokenStore.java(dev-e), Misc03.java(dev-b), … (이 노트에서 줄임 — 나머지는 Misc 파일 13개)]
  단순 버스 팩터(파일 절반 이상이 '아는 사람 0명'이 될 때까지 빠진 사람): 3명 [dev-b, dev-a, dev-c]
```

- 관찰 1 — 제일 큰 파일(LegacyReport, 2006줄)은 핫스팟 3위였다. 3회만 바뀌었다. 크기만 보고 골랐다면 1순위였다.
- 관찰 2 — Order↔OrderMapper는 degree 95%. Order가 바뀐 커밋의 92%에서 OrderMapper도 바뀌었고, OrderMapper가 바뀐 커밋은 100% Order와 함께였다. 신뢰도는 방향마다 다르다.
- 관찰 3 — TokenStore는 dev-e 혼자 10/10을 바꿨다. dev-e가 떠나면 아는 사람이 없다.

같은 로그를 Tornhill의 code-maat 1.0.4(`-c git2`)로 돌렸다.

(실험, code-maat-1.0.4-standalone.jar(GitHub release), JDK 21.0.12 `--cpus=2`, 2026-10-02)

```text
$ java -jar code-maat-1.0.4-standalone.jar -l git2.log -c git2 -a coupling | head
entity,coupled,degree,average-revs
src/order/Order.java,src/order/OrderMapper.java,95,58
$ ... -a main-dev | grep -E "TokenStore|PriceEngine|Order"
entity,main-dev,added,total-added,ownership
src/auth/TokenStore.java,exp,202,213,0.95
src/billing/PriceEngine.java,exp,602,643,0.94
src/order/Order.java,exp,302,363,0.83
src/order/OrderMapper.java,exp,122,178,0.69
$ ... -a main-dev-by-revs | grep -E "entity|TokenStore|PriceEngine|Order"
entity,main-dev,added,total-added,ownership
src/auth/TokenStore.java,dev-e,10,12,0.83
src/billing/PriceEngine.java,dev-a,30,42,0.71
src/order/Order.java,dev-b,19,62,0.31
src/order/OrderMapper.java,dev-a,17,57,0.3
$ ... -a authors | grep -E "TokenStore|entity"
entity,n-authors,n-revs
src/auth/TokenStore.java,3,12
```

- 관찰 4 — coupling degree 95는 직접 만든 계산기와 같다(같은 식, 같은 기본 거르기).
- 관찰 5 — 추가 줄 수 기준 `main-dev`는 확인한 네 파일(TokenStore·PriceEngine·Order·OrderMapper)의 주인을 전부 `exp`(최초 import 커밋 작성자)로 잡았다. 파일을 처음 만든 커밋 하나가 줄 수 대부분을 차지하기 때문이다. 커밋 수 기준(`main-dev-by-revs`)은 실제 유지보수자(dev-e·dev-a·dev-b)를 잡았다.
- 관찰 6 — 대량 커밋을 빼지 않은 `authors` 분석은 TokenStore 작성자를 3명(dev-e·포매터를 돌린 dev-c·import한 exp)으로 센다. 대량 커밋을 뺀 직접 계산에서는 1명이었다. 지식 섬이 지표에서 사라지는 길이다.
- code-maat README는 `--verbose-results`를 설명하지만 1.0.4 jar에서는 `Unknown option`이었다(이 실행 기준).

## 쓰이는 자료구조·알고리즘

- **커밋 로그 집계(해시맵 카운트)** — `파일 → 커밋 수`, `파일 → (작성자 → 커밋 수)`. 로그 한 번 읽기로 O(전체 파일 변경 수).
- **공동 변경 행렬** — 커밋마다 바뀐 파일 쌍을 전부 센다. 커밋 하나에 파일 k개면 k(k−1)/2쌍이다. 대량 커밋 하나(40파일)가 780쌍을 만든다. 그래서 `max-changeset-size`로 큰 커밋을 뺀다. 행렬은 희소하므로 쌍을 키로 하는 맵에 둔다.
- **연관 규칙(지지도·신뢰도)** — 장바구니 분석과 같은 계산. "Order를 바꾸면 OrderMapper도"가 "빵을 사면 버터도"와 같은 꼴이다.
- **정규화 곱 점수와 정렬** — 핫스팟 순위. 두 축을 각각 0~1로 맞춘 뒤 곱한다(이 실험의 정의. 도구마다 다르다).
- **탐욕 집합 덮기** — 단순 버스 팩터 계산. 가장 많은 파일을 아는 사람부터 제거한다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **기간을 정한다.** 최근 6~12개월(예시). 오래된 이력은 지금 구조와 다르다. `--after=YYYY-MM-DD`.
2. **잡음을 뺀다.** 생성 코드·벤더 폴더(`-- . ":(exclude)vendor/*"`, code-maat README의 방법), 대량 커밋(포매터·라이선스 헤더·이름 일괄 변경), 테스트 픽스처.
3. **변경 빈도 상위를 뽑는다.**

```bash
git log --after=2025-10-01 --format=format: --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head -20
```

4. **복잡도와 겹친다.** 줄 수(`wc -l`), 순환 복잡도(PMD 등, 52), 들여쓰기 근사. 둘 다 높은 상위 몇 개가 후보다.
5. **후보 안을 더 잘게 본다.** 파일이 크면 함수 단위로. 그 파일의 커밋 메시지·버그 티켓을 읽는다.
6. **change coupling을 본다.** 이유가 설명되는 쌍(구현 ↔ 테스트)은 둔다. 설명이 안 되는 쌍(서로 다른 모듈의 `Order`·`Invoice`)은 숨은 결합이다. 합치거나, 공통 개념을 뽑거나, 경계를 다시 긋는다.
7. **지식 섬을 본다.** 핫스팟인데 작성자 1명이면 짝 작업·리뷰 순환·문서화를 먼저 한다.
8. **결정을 기록하고 추세를 다시 잰다.** 리팩터링 후 그 파일의 변경당 수정 줄 수·버그 커밋 비율이 줄었나.

### 2. 진단 명령

- 파일별 작성자: `git shortlog -sn HEAD -- src/auth/TokenStore.java`

(실험 E 저장소, 대량 커밋 포함)

```text
    10	dev-e
     1	dev-c
     1	exp
```

- 이름 변경 추적: 집계는 `--no-renames`로 경로를 고정하고(code-maat 권장 형식), 특정 파일 이력을 볼 때는 `git log --follow -- <path>`.
- code-maat: `-a revisions`(빈도), `-a coupling`(공동 변경), `-a main-dev-by-revs`(주 작성자), `-a summary`(개요).

### 3. 결과를 우선순위로

```text
 후보 = 핫스팟 상위 ∩ (버그 커밋 많음 ∪ 앞으로 바뀔 기능 영역)
 순서 = 이자(변경 빈도) 큰 것부터. 크기·나이·"보기 싫음"은 순서 기준이 아니다.
```

- 이 판단은 [engineering-practice/10-technical-debt](../../engineering-practice/10-technical-debt/2-summary.md)의 상환 순서로 이어진다.

## 장애 시나리오와 대처

### 1. 전체 리팩터링 계획이 거의 안 바뀌는 파일에 인력을 소진 (⚠ 커리큘럼)

- 현상: 6개월 리팩터링 뒤에도 기능 개발 속도·버그 수가 그대로다.
- 보이는 형태: 리팩터링한 파일들의 리팩터링 전 1년 변경 수가 한 자릿수. 정작 매주 바뀌는 파일은 손대지 않았다. 실험 E에서 크기 1위 LegacyReport는 3회 변경이었다.
- 원인: "크다·오래됐다·보기 싫다"로 대상을 골랐다. 이자를 내지 않는 부채를 갚았다.
- 대처: 변경 빈도 × 복잡도로 후보를 좁힌다. 안 바뀌는 큰 파일은 그대로 두거나 격리만 한다.

### 2. 두 파일이 커밋의 90%에서 함께 바뀌는데 아무도 모름 (⚠ 커리큘럼)

- 현상: `Order.java`를 고칠 때마다 `OrderMapper.java`를 깜빡해 버그가 난다. 리뷰어도 매번 놓친다.
- 보이는 형태: 실험 E — degree 95%, 신뢰도 Order→OrderMapper 0.92. "OrderMapper 수정 누락" 핫픽스 커밋이 이력에 반복된다.
- 원인: 같은 지식(필드 목록)이 두 곳에 있다. import 그래프에는 안 보이는 결합이다.
- 대처: 매핑을 생성·공유 정의로 바꾸거나 한 파일로 합친다. 당장은 리뷰 체크리스트·CODEOWNERS로 둘을 묶는다. 다른 모듈·다른 저장소 사이의 쌍이면 경계 설계 문제다(45·40).

### 3. 퇴사자 1명만 알던 모듈에서 장애 (⚠ 커리큘럼)

- 현상: 인증 토큰 저장 로직에서 장애가 났는데 코드를 아는 사람이 없다. 복구가 몇 시간 늦어진다.
- 보이는 형태: 실험 E의 TokenStore처럼 커밋 100%가 한 사람. 그 사람이 떠난 뒤 커밋이 0인 기간.
- 원인: 지식 분포를 재지 않았다. 핫스팟·중요 모듈이 지식 섬이었다.
- 대처: 작성자 1명인 중요 파일 목록을 정기적으로 뽑아 짝 작업·리뷰 순환·런북을 붙인다. 퇴사 전 인수인계 범위를 이 목록으로 정한다.

### 4. 대량 커밋·도구 기본값이 지표를 왜곡

- 현상: 지식 섬이 지표에 안 보이거나, 여러 파일의 주인이 한 사람(import·포매터를 돌린 사람)으로 나온다.
- 보이는 형태: 실험 E — `main-dev`(추가 줄 수 기준)가 전부 `exp`. 대량 커밋을 포함한 `authors`에서 TokenStore 작성자 3명.
- 원인: 파일 생성·일괄 변경 커밋이 줄 수·작성자 수를 지배한다.
- 대처: 대량 커밋을 빼고(`max-changeset-size`·해시 제외), 소유 지표는 커밋 수 기준과 줄 수 기준을 함께 본다. 포매터 커밋은 `.git-blame-ignore-revs`로 모아 두면 `git blame --ignore-revs-file`에도 쓸 수 있다.

### 5. 지표 게이밍·맥락 상실

- 현상: "핫스팟 점수를 낮추라"는 목표가 생기자 파일을 기계적으로 쪼개거나 커밋을 몰아서 한다.
- 보이는 형태: 점수는 내려갔는데 변경당 수정 파일 수는 늘었다.
- 원인: 핫스팟은 우선순위를 정하는 도구다. 목표 지표로 쓰면 측정 대상이 바뀐다.
- 대처: 핫스팟은 "어디를 볼지"에만 쓰고, 성과는 변경 비용(변경당 파일 수·리드타임·버그)으로 잰다.

## 핵심 문장

- 기술 부채의 비용은 그 코드를 바꿀 때 낸다. 그래서 자주 바뀌면서 복잡한 곳(핫스팟)이 먼저다. 실험에서 크기 1위 파일은 3회만 바뀌어 핫스팟 3위였다.
- change coupling은 같은 커밋에 반복해 나타나는 파일 쌍이다. code-maat의 degree는 공동 커밋 ÷ 두 파일 커밋 수의 평균이고, 실험의 Order↔OrderMapper는 95였다.
- 신뢰도는 방향이 있다. Order가 바뀌면 92%에서 OrderMapper도 바뀌었고, 그 역은 100%였다.
- 지식 분포는 커밋 작성자로 본다. 작성자가 1명인 핫스팟·중요 모듈은 장애 복구의 위험이다.
- 대량 커밋과 도구 기본값은 지표를 크게 바꾼다. 줄 수 기준 주 작성자는 import한 사람을 확인한 네 파일 전부의 주인으로 잡았다.

## 관련 주제·근거

- 선행
  - [52-complexity-metrics](../52-complexity-metrics/2-summary.md)
  - [engineering-practice/03-version-control-and-git-internals](../../engineering-practice/03-version-control-and-git-internals/2-summary.md) · [engineering-practice/10-technical-debt](../../engineering-practice/10-technical-debt/2-summary.md)
- 후속·연결
  - [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md) — 핫스팟을 고칠 때의 안전한 변경 기법
  - [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md) — 변경 0인 코드가 죽은 코드인지 확인하는 법
  - [40-codebase-structure](../40-codebase-structure/2-summary.md) — 함께 바뀌는 것을 함께 두기
  - [05-connascence](../05-connascence/2-summary.md) — 결합의 종류
- 글·문서
  - Adam Tornhill, 『Your Code as a Crime Scene』 2판, Pragmatic Bookshelf, 2024-02(336쪽) — 출판사 목차로 절 제목 확인(핫스팟·복잡도 모양·change coupling 알고리즘·truck factor·knowledge map). 본문 미열람 <https://pragprog.com/titles/atcrime2/your-code-as-a-crime-scene-second-edition/>
  - Adam Tornhill, 『Software Design X-Rays』, Pragmatic Bookshelf, 2018-03 — 출판사 목차·저자 인터뷰로 확인(high interest rates, hotspots, change coupling 2·3장). 본문 미열람 <https://pragprog.com/titles/atevol/software-design-x-rays/>
  - code-maat README(로그 형식, 분석 종류, coupling 기본 거르기) <https://github.com/adamtornhill/code-maat> · 소스 `src/code_maat/analysis/logical_coupling.clj`(degree 식)
- 실험 목록
  - 실험 E — 합성 저장소(205커밋·40파일) 핫스팟·change coupling·지식 분포. 생성 `scratchpad/sd/50/e53/gen.py`(seed 7), 분석 `Forensics.java`(`java Forensics.java git.log repo 30` / `1000`), code-maat 1.0.4 대조(`codemaat.out`). JDK 21.0.12 temurin `--cpus=2`, git 2.43.0.
