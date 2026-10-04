# engineering-practice/10-technical-debt — 기술부채: 원뜻, 이자와 원금, 4사분면, 상환 전략 — 정리 (힌트)

## 해결하는 문제

코드 안의 군더더기가 새 기능을 느리게 만든다. 그런데 그 비용을 말할 언어가 없으면 이런 대화가 반복된다.

- 개발자: "코드가 지저분해서 정리할 시간이 필요해요."
- 관리자: "기능부터 내고 나중에 하죠." — 나중은 오지 않는다.

쉬운 예: 신용카드 빚이다.

```text
  지금 카드로 산다 ──> 물건을 빨리 쓴다(이득)
          │
          └─> 갚기 전까지 매달 이자를 낸다
              원금을 갚으면 이자가 멈춘다
              이자만 계속 내다 한도가 차면 아무것도 못 산다
```

똑같은 구조다. Fowler의 "TechnicalDebt"(2019-05-21) 예시가 이 구조를 그대로 쓴다.

```text
  모듈 구조가 깔끔하면 새 기능  ████            4일
  지금의 군더더기로는           ██████          6일   → 차이 2일 = 이자
  군더더기 정리(원금 상환)      █████           5일
  정리 후 같은 기능              ████(이하)
  → 이번 기능 하나만 보면 5+4 = 9일 > 6일 (손해)
  → 비슷한 기능이 2개 더 오면 먼저 정리하는 쪽이 빠르다
```

- *군더더기(cruft)*: 내부 품질의 결함. 시스템을 고치고 늘리기를 이상적인 경우보다 어렵게 만드는 것(Fowler 2019의 정의).
- *기술부채(technical debt)*: 군더더기를 금융 부채에 빗대어 다루는 은유. Ward Cunningham이 만들었다(Fowler 2019).
- *이자(interest)*: 군더더기 때문에 새 기능에 더 드는 노력. *원금(principal)*: 군더더기를 없애는 데 드는 노력.

실무 예:
- 2년 전엔 2주 걸리던 크기의 기능이 이제 6주 걸린다. 아무도 이유를 하나로 말하지 못한다. 결국 "전부 다시 짜자"는 말이 나온다(장애 1).
- 세율이 바뀌었는데 네 곳에 복사된 계산 중 한 곳을 빠뜨려 환불만 세금을 다르게 계산한다(장애 2, 아래 실험).

## 동작·원리

### 1. 원뜻 — Cunningham 1992

OOPSLA '92 경험 보고서 "The WyCash Portfolio Management System"(1992-03-26)의 문단이다(c2.com 원문).

- "처음 쓴 코드를 출시하는 것은 빚을 지는 것과 같다. 조금의 빚은 개발을 빠르게 한다. 단, **재작성으로 곧 갚는다면**."
- "위험은 빚을 갚지 않을 때 생긴다. 딱 맞지 않는 코드에 쓰는 매 분이 그 빚의 이자다."
- "통합(consolidate)되지 않은 구현의 빚 때문에 엔지니어링 조직 전체가 멈춰 설 수 있다."

같은 문단 앞에서 Cunningham이 말하는 함정은 **통합 실패**다. 잘 돌아가는 미숙한 코드라도 쌓이면 다룰 수 없게 된다는 것이다.

- 흔한 오해: "기술부채 = 대충 짠 코드". Fowler의 사분면 글(2009)은 Uncle Bob의 "엉망(mess)은 부채가 아니다" 주장을 소개한다. Fowler 자신은 엉망도 부채로 보되 **무모한 부채**로 분류한다. Cunningham의 원래 문단은 "배우면서 쓴 첫 코드를 이해가 깊어진 만큼 다시 쓰는 것"에 가깝다(Fowler는 신중·비의도 사분면이 "Ward가 영상에서 말한 종류의 부채"라고 쓴다).

### 2. 이자는 그 코드를 바꿀 때만 낸다 — Fowler 2019

```text
  금융 부채                          기술부채
  이자 = 시간이 지나면 붙는다         이자 = 그 코드를 고칠 때만 낸다
                                     ┌─────────────────────────────┐
  자주 바뀌는 곳(핫스팟)  ────────────> │ 이자 큼 → 군더더기 무관용    │
  지저분하지만 안 바뀌는 곳 ──────────> │ 이자 0에 가까움 → 둬도 된다  │
                                     └─────────────────────────────┘
```

- Fowler 2019: "지저분하지만 안정된(crufty but stable) 영역은 그대로 둘 수 있다. 활동이 많은 영역은 군더더기에 무관용이어야 한다." 은유가 깨지는 지점이라고 스스로 밝힌다(금융 이자는 시간에 붙는다).
- 그래서 상환은 **조금씩**이 기본이다. 기능을 고칠 때 그 주변을 조금 정리한다. 자연히 자주 고치는 곳이 더 많이 정리된다(Fowler 2019 "pay the principal off gradually").
- 이 비용들은 객관적으로 잴 수 없다(Fowler, "CannotMeasureProductivity"). 기능 소요, 정리 후 소요, 정리 비용 모두 추정이고 정확도가 낮다.
- 자주 바뀌는 곳을 git 이력으로 찾는 법은 [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md)에 있다.

### 3. 4사분면 — Fowler 2009

"TechnicalDebtQuadrant"(2009-10-14)의 그림이다. 따옴표 안은 그림의 원문 문장이다.

```text
                   무모함(Reckless)                신중함(Prudent)
              ┌──────────────────────────────┬──────────────────────────────┐
  의도적       │ "We don't have time           │ "We must ship now             │
  (Deliberate) │  for design"                  │  and deal with consequences"  │
              │ 설계할 시간 없다(실은 더 느려짐) │ 출시 이득 > 상환 비용을 따져 봄 │
              ├──────────────────────────────┼──────────────────────────────┤
  비의도적     │ "What's Layering?"            │ "Now we know how we           │
  (Inadvertent)│ 좋은 설계를 모른 채 쌓임       │  should have done it"         │
              │                               │ 만들고 나서야 맞는 설계를 앎    │
              └──────────────────────────────┴──────────────────────────────┘
```

- 핵심 주장(Fowler 2009): 쓸모 있는 구분은 "부채냐 아니냐"가 아니라 **신중한 부채냐 무모한 부채냐**다.
- 신중·의도적: 팀이 빚을 진다는 것을 알고, 일찍 출시하는 이득이 갚는 비용보다 큰지 따져 본다. 이자가 충분히 작으면(거의 안 건드리는 곳) 갚지 않는 것도 선택이다.
- 무모·의도적: 좋은 설계를 알지만 "깨끗하게 짤 시간이 없다"고 생각한다. Fowler는 이것이 보통 무모하다고 본다. 설계가 이득이 되는 선(DesignPayoffLine)을 사람들이 과소평가하기 때문이다.
- 신중·비의도적: 훌륭한 팀에게도 **피할 수 없다**. 프로그래밍하는 동안 배우기 때문이다. Fowler: "최선의 설계가 무엇이었는지 알기까지 1년이 걸리기도 한다."
  - 흔한 오해: "좋은 팀은 부채가 없다". Fowler는 이 사분면의 부채를 피할 수 없고 예상해야 한다고 쓴다. 그러니 무모한 부채로 더 쌓지 말라는 것이다.

### 4. 도구가 말하는 "부채"는 따로 정의된다

- SonarQube Server 문서(Understanding measures and metrics)
  - 기술부채 = 유지보수성 이슈의 수정 비용 합(규칙마다 정해진 분 단위 노력).
  - 기술부채 비율 = 기술부채 ÷ 개발 비용. 개발 비용 = 코드 줄 수 × 한 줄 개발 비용(기본 30분).
  - 문서의 예: 부채 122,563분, 64k줄(63,987) → 6.4%.
  - 유지보수성 등급(기본): A ≤ 5%, B 5~10%, C 10~20%, D 20~50%, E ≥ 50%.
- 해석: 이 수치는 **규칙 위반으로 잡히는 것**만 센다. 4사분면의 "이제야 맞는 설계를 알았다"는 규칙으로 잡히지 않는다. 도구 수치를 부채 전체로 읽으면 안 된다.

### 실험: 이자를 줄 수로 재기 — 복사된 세금 계산 4곳

**시뮬레이션이다.** 일회용 git 저장소에 같은 기능 변경 3건을 두 방식으로 재생했다.

```text
  main ─── 서비스 4개(Order·Invoice·Refund·Quote)에 세금 계산이 복사돼 있다
   ├── debt         : 그대로 두고 F1(세율 10%→8%) · F2(은행가 반올림) · F3(BOOK 면세)
   ├── debt-missed  : debt와 같지만 F3에서 RefundService를 빠뜨림
   └── repay        : 먼저 TaxPolicy로 추출(원금) → 같은 F1·F2·F3
```

```java
// debt: 네 서비스가 각자 이 본문을 갖는다
public class OrderService {
    public long tax(String category, long amountCents) {
        if ("BOOK".equals(category)) return 0;
        return java.math.BigDecimal.valueOf(amountCents).multiply(new java.math.BigDecimal("0.08"))
                .setScale(0, java.math.RoundingMode.HALF_EVEN).longValue();
    }
}

// repay: 규칙은 한 곳, 서비스는 위임만
public class OrderService {
    public long tax(String category, long amountCents) {
        return TaxPolicy.tax(category, amountCents);
    }
}
```

측정은 git이 센 변경 줄 수(추가+삭제, `git show --numstat`)다. 동작 확인은 각 브랜치를 JDK 21로 컴파일해 `tax("FOOD", 1250)`·`tax("BOOK", 1250)`을 출력했다.

(실험, git 2.43.0 / eclipse-temurin:21-jdk(OpenJDK 21.0.12) `--network none --cpus=1`, 2026-10-05 — 입력 고정, 실행마다 같음)

```text
== 브랜치 debt (main 이후 커밋, 오래된 순) — 줄 = 추가+삭제, 누적은 그 시점까지의 합
  F1: tax rate 10% -> 8%                     파일 4  줄   8  | 누적 파일  4  줄   8
  F2: banker's rounding                      파일 4  줄  12  | 누적 파일  8  줄  20
  F3: BOOK is tax-exempt                     파일 4  줄   4  | 누적 파일 12  줄  24
== 브랜치 repay (main 이후 커밋, 오래된 순) — 줄 = 추가+삭제, 누적은 그 시점까지의 합
  refactor: extract TaxPolicy (principal)    파일 5  줄  14  | 누적 파일  5  줄  14
  F1: tax rate 10% -> 8%                     파일 1  줄   2  | 누적 파일  6  줄  16
  F2: banker's rounding                      파일 1  줄   3  | 누적 파일  7  줄  19
  F3: BOOK is tax-exempt                     파일 1  줄   1  | 누적 파일  8  줄  20
== 파일별 변경 횟수 (debt 브랜치 이력)
      4 RefundService.java
      4 QuoteService.java
      4 OrderService.java
      4 InvoiceService.java
      1 LegacyExport.java
      1 Check.java
== 동작: 브랜치 debt
OrderService    FOOD  100  BOOK    0
InvoiceService  FOOD  100  BOOK    0
RefundService   FOOD  100  BOOK    0
QuoteService    FOOD  100  BOOK    0
== 동작: 브랜치 debt-missed
OrderService    FOOD  100  BOOK    0
InvoiceService  FOOD  100  BOOK    0
RefundService   FOOD  100  BOOK  100
QuoteService    FOOD  100  BOOK    0
== 동작: 브랜치 repay
OrderService    FOOD  100  BOOK    0
InvoiceService  FOOD  100  BOOK    0
RefundService   FOOD  100  BOOK    0
QuoteService    FOOD  100  BOOK    0
== 같은 규칙의 복사본 찾기 (git grep, repay 브랜치)
repay:LegacyExport.java:3:        long tax = Math.round(amountCents * 0.10);
repay:TaxPolicy.java:5:        return java.math.BigDecimal.valueOf(amountCents).multiply(new java.math.BigDecimal("0.08"))
```

- 관찰 1 — 이자: 기능마다 debt는 4파일을 고쳤고 repay는 1파일을 고쳤다. 줄 수로 8 vs 2, 12 vs 3, 4 vs 1이다.
- 관찰 2 — 손익분기: 원금 14줄을 먼저 냈다. F1까지 누적은 debt 8 < repay 16(손해). F2까지 20 vs 19로 역전했다. F3까지 24 vs 20. **변경이 한 번뿐이면 상환은 손해였다.** Fowler 예시(기능 하나면 9일 > 6일)와 같은 모양이다.
- 관찰 3 — 이자는 줄 수만이 아니다: debt-missed에서 한 곳을 빠뜨리자 RefundService만 BOOK에 세금 100을 매겼다. 컴파일도 되고 예외도 없다. 조용한 불일치다.
- 관찰 4 — 변경 횟수만 보면 놓친다: LegacyExport는 이력상 1번(생성)만 바뀌어 "둬도 되는 곳"으로 보인다. 그런데 `git grep`은 거기에도 세금 계산이 남아 있고, **상환한 repay에서도 아직 10%** 라는 것을 보여 준다. 같은 규칙의 복사본인지는 변경 이력이 아니라 내용 검색으로 찾아야 한다.
- 한계: 줄 수는 노력의 대리값이다. 실제 시간·결함 비용을 잰 것이 아니다.

## 쓰이는 자료구조·알고리즘

- **부채 대장 = 우선순위 큐** — 항목마다 이자(그 영역의 변경 빈도 × 변경당 추가 비용)와 원금(정리 비용)을 적고, 이자가 큰 것부터 꺼낸다. 변경 빈도는 git 이력에서 센다(53의 핫스팟).
- **손익분기 계산** — 누적 비용 두 줄(그대로 둠 vs 먼저 갚음)을 기능 순서대로 더해 교차점을 찾는다. 실험의 "누적" 열이 그 계산이다. 미래 변경 수를 모르므로 결과는 추정이다.
- **복사본 탐지** — 같은 규칙의 복사본은 텍스트 검색(`git grep`)이나 코드 클론 탐지 도구(PMD CPD 등)로 찾는다. 클론 탐지 알고리즘의 세부는 이 노트에서 확인하지 않았다 `[?]`.
- **변경 결합** — 함께 바뀌는 파일 쌍(Shotgun Surgery의 흔적)은 [software-design/53](../../software-design/53-code-forensics-hotspots/2-summary.md)의 change coupling, [software-design/10-code-smells](../../software-design/10-code-smells/2-summary.md) 실험 A.

## 적용 — 풀어나가는 법

### 1. 부채를 보이게 만든다 — 부채 대장

| 항목 | 위치 | 사분면 | 이자 증거 | 원금 추정 | 결정 |
|---|---|---|---|---|---|
| 세금 계산 4곳 복사 (예시) | `*Service.java` | 무모·비의도 | 최근 3개월 세금 변경 3건, 건마다 4파일 | 1일 (예시) | 다음 세금 변경 때 TaxPolicy로 추출 |
| 출시용 하드코딩 할인 (예시) | `Promo.java` | 신중·의도 | 이벤트 끝나면 안 바뀜 | 0.5일 | 이벤트 종료일에 삭제, 티켓 연결 |
| 레거시 내보내기 (예시) | `LegacyExport.java` | — | 변경 1회, 단 세금 규칙 복사본 | 0.5일 | 규칙만 TaxPolicy로 연결 |

- 신중·의도적 부채는 **진 날 기록한다.** 이유·상환 조건·기한을 남긴다. 결정 기록은 [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md) 형식을 쓸 수 있다.
- 이자 증거는 말이 아니라 데이터로 적는다. 변경 횟수, 변경당 고친 파일 수, 그 영역에서 난 버그 수.

### 2. 상환 전략

1. **건드릴 때 조금씩** — 그 영역의 기능을 고칠 때 먼저 정리하고 기능을 넣는다(Fowler 2019). 정리 커밋과 기능 커밋은 나눈다([software-design/14-tidy-first](../../software-design/14-tidy-first/2-summary.md)).
2. **이자가 큰 곳부터** — 핫스팟(53)부터. 안 바뀌는 곳은 미룬다. 단, 실험의 LegacyExport처럼 **같은 규칙의 복사본**이면 규칙만은 묶는다.
3. **큰 원금은 나눠 갚는다** — 전면 재작성 대신 경로를 하나씩 옮긴다([software-design/50-legacy-migration-strangler-fig](../../software-design/50-legacy-migration-strangler-fig/2-summary.md)).
4. **안전망 먼저** — 리팩터링은 테스트가 동작을 붙잡고 있을 때 한다([software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md)).

### 3. 진단 명령

```sh
# 최근 6개월 파일별 변경 횟수 — 이자가 큰 후보
# (git 2.43: 병합 커밋은 기본으로 파일 목록이 안 나온다. 브랜치 커밋으로는 세지만, 충돌 해결처럼 병합 커밋에서만 고친 것은 빠진다.
#  병합을 한 번의 변경으로 세려면 --first-parent --diff-merges=first-parent)
git log --since=6.months --format= --name-only | grep -v '^$' | sort | uniq -c | sort -rn | head
# 한 커밋이 몇 파일을 건드렸나 — 같은 변경이 여러 곳에 흩어지는지
git show --numstat --format='%h %s' <커밋>
# 같은 규칙의 복사본 — 변경 이력에 안 잡히는 것을 내용으로 찾는다
git grep -n -E 'amountCents \* 0\.|BigDecimal\("0\.'
```

## 장애 시나리오와 대처

### 1. 부채를 안 보이게 둠 → 속도 점진 저하 → 전면 재작성 유혹 (⚠ 커리큘럼)

- 현상: 분기마다 같은 크기의 기능이 조금씩 더 오래 걸린다. 어느 날 "다 갈아엎자"는 제안이 나온다.
- 보이는 형태: 리드 타임 증가([09-dora-metrics](../09-dora-metrics/2-summary.md)), 변경당 건드리는 파일 수 증가, 특정 파일의 반복 수정.
- 원인: 이자를 낸다는 사실이 기록되지 않았다. 원금 상환은 매번 "기능 다음"으로 밀렸다.
- 대처
  - 부채 대장을 만들고 이자 증거를 데이터로 붙인다(적용 1).
  - 전면 재작성 대신 스트랭글러 피그로 나눠 옮긴다. 재작성 2년이 기능 격차로 중단되는 장애는 [software-design/50](../../software-design/50-legacy-migration-strangler-fig/2-summary.md) 장애 1.
  - 기능 일정에 정리 비용을 포함해 추정한다([12-estimation-and-planning](../12-estimation-and-planning/2-summary.md)).

### 2. 복사본 하나를 빠뜨림 → 조용한 불일치

- 현상: 세율 정책을 바꾼 뒤 환불 금액만 고객 문의가 들어온다.
- 보이는 형태: 예외·에러 없음. 실험의 debt-missed처럼 한 서비스만 BOOK에 세금 100을 매긴다.
- 원인: 같은 규칙이 여러 곳에 복사돼 있고, 변경이 그중 일부에만 들어갔다.
- 대처: 규칙을 한 곳으로 모은다(repay). 당장 못 모으면 모든 복사본에 같은 입력을 넣고 결과가 같은지 비교하는 테스트를 둔다.

### 3. 안 바뀌는 곳 상환에 인력 소진

- 현상: "가장 지저분한 모듈"부터 정리했는데, 그 모듈은 1년에 한 번 바뀐다.
- 원인: 이자(변경 빈도)를 안 보고 원금 크기(지저분함)만 봤다. Fowler 2019: 지저분하지만 안정된 곳은 둘 수 있다.
- 대처: 변경 빈도로 우선순위를 정한다(53). 예외는 규칙의 복사본처럼 **다른 곳 변경에 끌려가야 하는 코드**다(실험 관찰 4).

### 4. "부채니까"를 품질 방치의 핑계로 씀

- 현상: 급할 때마다 "일단 부채로 지고 가자"가 반복된다. 상환 기록은 없다.
- 원인: Fowler 2019 — 부채 은유가 내부 품질 방치를 정당화하는 데 쓰인다. 군더더기는 빠르게 영향을 준다. 이런 팀은 "신용카드 한도를 다 쓰고도" 품질에 투자했을 때보다 늦게 낸다. 설계 이득선(DesignPayoffLine)에 몇 달이 아니라 **몇 주** 만에 닿는다는 것이 Fowler의 주장이다.
- 대처: 의도적 부채에는 상환 조건과 기한을 붙여 기록한다. 기한이 지난 항목을 회고에서 본다.

### 5. 도구의 부채 점수를 목표로 → 숫자만 좋아짐

- 현상: "부채 비율 5% 이하" 게이트를 걸었더니 규칙 억제 주석과 의미 없는 분할이 늘었다.
- 원인: 도구 점수는 규칙 위반의 합이다(SonarQube 정의). 목표가 되면 굿하트의 법칙이 작동한다. 지표 게이트를 맞추려 코드를 쪼개는 장애는 [software-design/52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md) 장애 2.
- 대처: 점수는 추세·대화의 재료로만 쓴다. 상환 우선순위는 이자 증거(변경 빈도·버그)로 정한다.

## 핵심 문장

- 기술부채는 Cunningham(1992)의 은유다. 원뜻은 "처음 코드로 빨리 내고, 배운 만큼 곧 다시 써서 갚는다"이고, 갚지 않으면 이자가 조직을 멈춘다.
- 이자는 그 코드를 **바꿀 때만** 낸다(Fowler 2019). 그래서 자주 바뀌는 곳은 무관용, 안 바뀌는 곳은 둘 수 있다.
- 쓸모 있는 구분은 부채냐 아니냐가 아니라 신중하냐 무모하냐다(Fowler 2009). 신중·비의도 부채는 훌륭한 팀에도 생긴다.
- 실험에서 원금 14줄은 변경 한 번(8 vs 16)으로는 손해였고, 두 번째 변경에서 역전했다(20 vs 19). 상환의 가치는 앞으로의 변경 수에 달렸다.
- 복사된 규칙은 줄 수 이자에 더해 조용한 불일치 위험을 진다. 복사본은 변경 이력이 아니라 내용 검색으로 찾는다.
- 도구의 부채 점수는 규칙 위반의 합이다. 부채 전체가 아니다.

## 관련 주제·근거

- 선행
  - [software-design/10-code-smells](../../software-design/10-code-smells/2-summary.md) — 부채의 구체적 모양
- 후속·연결
  - [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md) — 이자가 큰 곳 찾기
  - [software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md) · [14-tidy-first](../../software-design/14-tidy-first/2-summary.md) — 원금 상환 방법
  - [software-design/50-legacy-migration-strangler-fig](../../software-design/50-legacy-migration-strangler-fig/2-summary.md) — 전면 재작성 대신
  - [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md) — 의도적 부채 기록
  - [software-design/52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md) — 지표 게이트와 굿하트
  - [09-dora-metrics](../09-dora-metrics/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md) — 낡은 문서도 부채다
  - [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md) — 정리 비용을 일정에 넣는 추정
  - [19-practice-symptom-index](../19-practice-symptom-index/2-summary.md)
- 글·문서
  - Ward Cunningham, "The WyCash Portfolio Management System", OOPSLA '92 Experience Report(1992-03-26) <http://c2.com/doc/oopsla92.html>
  - Martin Fowler, "TechnicalDebtQuadrant"(2009-10-14) — 그림 원문 문장 확인 <https://martinfowler.com/bliki/TechnicalDebtQuadrant.html>
  - Martin Fowler, "TechnicalDebt"(2019-05-21) — 4일/6일/5일 예시, 이자는 고칠 때, 점진 상환, 은유 남용 <https://martinfowler.com/bliki/TechnicalDebt.html>
  - SonarQube Server 문서 "Understanding measures and metrics" — 기술부채·비율·등급 정의 <https://docs.sonarsource.com/sonarqube-server/latest/user-guide/code-metrics/metrics-definition/>
- 실험 목록
  - 이자 재기 — `scratchpad/ep/09/debt/gen.sh`(브랜치 main·debt·debt-missed·repay 생성), `measure.sh`(numstat 집계, 변경 횟수, JDK 21 컨테이너 `sn-ep-w09-debt-<브랜치>`로 `Check` 실행, git grep). git 2.43.0, eclipse-temurin:21-jdk(21.0.12). 출력 `out.txt`.
