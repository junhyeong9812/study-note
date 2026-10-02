# software-design/50-legacy-migration-strangler-fig — 레거시 이전: Strangler Fig·branch by abstraction·병행 실행 — 정리 (힌트)

## 해결하는 문제

오래된 시스템을 새 시스템으로 바꿔야 한다. 가장 쉬워 보이는 계획은 "새로 다 만들고 하루에 갈아끼우기"다.

```text
 빅뱅 재작성
 t0 ──────────── 새 시스템 개발(구 시스템과 기능을 똑같이 맞추는 중) ──────────── t+2년 전환일
   구 시스템은 그동안에도 새 기능을 받는다 → 맞춰야 할 목표가 계속 움직인다
   전환일 하루에 위험이 몰린다 → 문제가 나면 되돌릴 곳이 "전부"다

 점진 이전 (Strangler Fig)
 t0 ─ 기능1 이전 ─ 기능2 이전 ─ ... ─ 기능N 이전 ─ 구 시스템 제거
   매 단계가 작고, 매 단계 뒤에 운영에서 확인하고, 문제가 나면 그 기능만 되돌린다
```

- *레거시 시스템*: 지금 업무를 돌리고 있지만 바꾸기 어려워진 시스템. 나이가 아니라 "바꾸기 어려움"이 기준이다.
- *빅뱅 재작성(big bang rewrite)*: 구 시스템을 그대로 두고 새 시스템을 처음부터 만든 뒤 한 번에 전환하는 방식.
- *Strangler Fig*: 무화과 덩굴이 숙주 나무를 감싸 자라다 결국 나무를 대신하는 모양에서 온 이름. 새 코드를 구 시스템 옆에 붙여 기능을 하나씩 옮기고, 다 옮기면 구 시스템을 지운다.

Fowler("Strangler Fig", 2024-08-22 개정)는 "같은 일을 하는 새 시스템을 만들자"는 단순한 계획이 "대부분 실패했다(go down in flames most of the time)"고 적는다.
이유로 든 것은 셋이다. 교체가 오래 걸리는데 사용자는 새 기능을 기다리지 못한다. 기존 동작의 세부를 알아내기 어렵다. 그 동작의 상당수는 실제로 필요 없는 것이다.

쉬운 예: 사는 집을 고칠 때 집을 비우고 통째로 다시 짓는 대신, 방 하나씩 고치며 계속 산다.\
똑같은 구조다.\
실무 예: 15년 된 주문 시스템의 할인 계산을 새 가격 서비스로 옮긴다. 할인 계산만 먼저 옮기고, 결과를 구 시스템과 비교하고, 고객 1% → 10% → 100%로 넓힌 뒤 구 코드를 지운다.

## 동작·원리

### 1. 퍼사드가 길을 나눈다 — 네 단계

Azure Architecture Center "Strangler Fig pattern"의 네 단계 그림을 글자로 옮기면 이렇다. 비율 숫자는 이해를 돕는 예시다(Azure 그림은 "일부"·"더 많은 요청"이라고만 적는다).

```text
 ① 퍼사드 도입              ② 점진 분해                 ③ 구 시스템 폐기           ④ 퍼사드 제거
 클라이언트                  클라이언트                  클라이언트                  클라이언트
     │                           │                           │                           │
 [퍼사드]                    [퍼사드]                    [퍼사드]                        │
  │90%   │10%                 │30%   │70%                     │100%                       │
  v      v                    v      v                        v                           v
 구      신                   구      신                       신                          신
```

- *퍼사드(façade)·프록시*: 클라이언트와 두 시스템 사이에서 요청을 받아 어느 쪽으로 보낼지 정하는 앞단. HTTP 게이트웨이일 수도, 코드 안의 라우터일 수도 있다.
- *과도기 아키텍처(transitional architecture)*: 이전이 끝나면 지울 것을 알면서 만드는 코드·인프라(퍼사드, 동기화, 비교기). Fowler는 이것이 낭비처럼 보여도 위험 감소와 이른 가치가 비용보다 크다고 적는다(주장).
- Azure 문서는 이전이 끝나면 퍼사드를 보통 제거한다고 적는다. 구 클라이언트용 어댑터로 남겨 두는 선택지도 함께 적는다.
- Azure 문서의 주의: 퍼사드가 단일 장애 지점이나 성능 병목이 되지 않게 한다. 요청을 가로챌 수 없거나, 시스템이 작아 통째로 바꾸는 편이 쉬우면 이 패턴이 맞지 않는다.

### 2. 코드 안에서는 branch by abstraction

퍼사드가 HTTP 앞단이 아니라 코드 안에 있으면 그것이 branch by abstraction이다(Fowler "BranchByAbstraction", 2014-01-07).

```text
 (1) 직접 호출                 (2) 추상 계층 도입            (3) 새 구현 추가              (4) 구 구현 삭제
 호출자 ──> 구 공급자           호출자 ──> «Discount»          호출자 ──> «Discount»          호출자 ──> «Discount»
                                            │                          │       │                          │
                                         구 구현                     구 구현  신 구현                     신 구현
```

- *추상 계층*: 호출자와 공급자 사이의 인터페이스. 두 구현이 동시에 살 수 있게 한다.
- 순서(Fowler): 호출자 한 구역을 추상 계층 뒤로 옮긴다 → 나머지 호출자도 옮긴다 → 같은 추상으로 새 공급자를 만든다 → 호출자를 구역별로 새 공급자로 바꾼다 → 구 공급자를 지운다. 필요 없으면 추상 계층도 지운다.
- 이 과정 내내 시스템은 빌드되고 실행된다. 그래서 긴 버전 관리 브랜치 없이 주 브랜치에서 진행할 수 있다(Fowler: 이름은 Paul Hammant가 붙였다).

### 3. 병행 실행 — 바꾸기 전에 비교한다

```text
           요청
            │
     ┌──────┴──────┐
     v             v
  control(구)   candidate(신)   ← 신 구현은 실행만, 결과는 버린다
     │             │
     └──> 비교기 <──┘  일치/불일치/후보 예외를 기록(지표·샘플)
            │
            v
     사용자에게는 control 결과만 돌려준다
```

- *병행 실행(parallel run)·섀도(shadow)*: 같은 입력을 두 구현에 주고 결과를 비교하되, 사용자에게는 구 결과만 준다.
- *다크 런칭(dark launching)*: 새 백엔드 기능을 사용자 모르게 호출해 부하·성능 영향을 먼저 재는 것. Fowler "DarkLaunching"은 이것이 재구현 기능의 병행 실행에도 쓰인다고 적는다.
- GitHub Scientist(Ruby 라이브러리) README의 정의: `use` 블록이 control, `try` 블록이 candidate다. `run`은 `use`의 값을 돌려준다(원문 "will always return"). 뒤에서는 try를 돌릴지 정하고, 두 블록의 실행 순서를 무작위로 하고, 시간을 재고, `==`로 비교하고, try의 예외를 삼켜 기록하고, 결과를 발행한다.
- Scientist README의 경고 둘: 후보의 **타임아웃은 막아 주지 않는다**. 쓰기(부수 효과)가 있는 경로는 두 시스템에 함께 쓰고 **읽을 때** 비교하는 방식을 권한다.

### 실험 A: 라우팅 비율·병행 실행·이중 쓰기 (Java)

할인 계산을 옮긴다. 구 구현은 `double` + `Math.round`(0.5는 올림)다. 새 구현 v1은 `BigDecimal`에 `RoundingMode.HALF_EVEN`(0.5는 짝수 쪽)을 골랐다. 이 반올림 규칙은 어디에도 문서화되지 않았다고 하자.

```java
static long legacyDiscount(long amountWon, int pct) { return Math.round(amountWon * pct / 100.0); }
static long newDiscountV1(long amountWon, int pct) {
    return BigDecimal.valueOf(amountWon).multiply(BigDecimal.valueOf(pct))
            .divide(BigDecimal.valueOf(100), 0, RoundingMode.HALF_EVEN).longValueExact();
}
// 라우터: 기능별 전환 비율 + 고객 ID 해시 버킷(같은 고객은 같은 쪽)
static final Map<String, Integer> routePercent = new HashMap<>();
static int bucket(String customerId) { return Math.floorMod(customerId.hashCode() * 0x9E3779B1, 100); }
static boolean toNew(String feature, String customerId) {
    return bucket(customerId) < routePercent.getOrDefault(feature, 0);
}
// 병행 실행: control 값을 돌려주고 candidate는 비교만, 예외는 삼켜 기록
static <T> T science(String name, Supplier<T> control, Supplier<T> candidate, String ctx) {
    T c = control.get();
    try { T n = candidate.get(); compared++; if (!Objects.equals(c, n)) { mismatched++; /* 샘플 기록 */ } }
    catch (RuntimeException e) { compared++; candidateErrors++; }
    return c;
}
```

(실험, JDK 21.0.12 temurin, Docker `--cpus=2`(nproc 2), 2026-10-02 — 입력은 seed 42 난수로 고정, 금액 1,000~99,999원·할인 1~30%, 10만 건)

```text
== 1) 라우팅 비율: 목표 vs 실제 (고객 100000명)
  목표  1% → 실제 1.00%
  목표 10% → 실제 9.98%
  목표 50% → 실제 50.05%
  같은 고객 반복 판정 일치: true
  10%→20% 확대 시 기존 10% 고객이 계속 새 경로: 9980/9980
== 2) 병행 실행(섀도): 새 구현 v1(HALF_EVEN)
  비교 100000건, 불일치 1289건(1.29%), 후보 예외 0건
   예: amt=57786 pct=25 legacy=14447 new=14446
   예: amt=39074 pct=25 legacy=9769 new=9768
   예: amt=51015 pct=30 legacy=15305 new=15304
== 3) 병행 실행(섀도): 새 구현 v2(HALF_UP)
  비교 100000건, 불일치 0건, 후보 예외 0건
== 4) 후보가 예외를 던져도 사용자 응답은 레거시 값
  반환=1500 후보 예외 기록=1 [amt=10000 pct=15 new threw IllegalStateException]
== 5) 이중 쓰기: 레거시와 새 경로가 같은 테이블에 각자 계산해 씀 (v1)
  레거시가 쓴 값과 다른 값으로 덮어쓴 행: 1289 / 100000 (마지막 쓰기가 이김, 에러 없음)
== 6) 되돌리기: 비율을 0으로
  새 경로로 가는 고객: 0
```

- 관찰 1 — 해시 버킷 라우팅은 목표 비율에 가깝게 나뉘었고(10% → 9.98%), 같은 고객은 반복해도 같은 쪽으로 갔다. 비율을 10%에서 20%로 넓혀도 원래 10% 고객 9980명은 모두 새 경로에 남았다. 버킷 `< 비율` 비교라 비율을 키우면 집합이 포함 관계로 커진다.
- 관찰 2 — 새 구현 v1은 단위 테스트(예: 10,000원 15% = 1,500원)로는 통과할 만했다. 병행 실행 10만 건에서 1.29%가 1원씩 달랐다. 전부 금액 × 할인율이 정확히 x.5원이고 정수부 x가 짝수인 입력이었다(샘플: 57786 × 25% = 14446.5). 정수부가 홀수인 .5는 HALF_EVEN도 올리므로 같다(판정 재실험: 같은 범위 무작위 10만 건 중 .5 입력 2,629건 — 정수부 짝수 1,279건 전부 불일치, 홀수 1,350건 불일치 0).
- 관찰 3 — 비교 결과를 보고 v2(HALF_UP)로 맞추자 불일치가 0이 됐다. 이것이 "레거시의 문서화 안 된 동작"을 찾는 방법이다.
- 관찰 4 — 같은 v1을 비교 없이 이중 쓰기로 붙였다면, 1289행이 조용히 다른 값으로 덮였다. 에러는 0건이다. 여기서 "테이블"은 `HashMap`으로 흉내 낸 것이다(실제 DB가 아닌 시뮬레이션). 레거시 쓰기 → 새 경로 쓰기 순서를 고정해 "마지막 쓰기가 이김"을 보였다.
- 관찰 5 — 되돌리기는 비율을 0으로 바꾸는 설정 변경 하나다. 재배포가 필요 없다(이 실험의 라우터는 메모리 맵이다. 실무에서는 설정 저장소·플래그 서비스).

### 4. 데이터는 expand/contract로 옮긴다

코드 경로는 비율로 나눌 수 있지만 데이터는 한쪽이 기준(system of record)이어야 한다. Azure 문서의 데이터베이스 이전 세 단계다.

```text
 단계 1                      단계 2                              단계 3
 신 서비스 → 구 DB 읽기·쓰기    구 DB ──ETL 초기 적재──> 신 도메인 DB   신 서비스 → 신 DB만
                              구 DB ──CDC 동기화────> 신 도메인 DB   구 DB의 해당 테이블 제거
                              두 DB 일치 검증 후 전환                 (제거 후 되돌리기는 복원·재생이 필요)
```

- *CDC(change data capture)*: DB 변경 로그를 읽어 다른 저장소로 흘리는 방식.
- Azure 문서: 단계 2와 단계 3 시작까지는 구 DB로 되돌릴 수 있다. 구 테이블을 지운 뒤 되돌리려면 객체를 복원하고 변경을 재생해야 해서 노력과 위험이 크다. 그래서 구 객체 제거는 "검증 뒤의 의도된 마지막 단계"로 둔다.
- 스키마 수준의 expand → backfill → switch → contract는 [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) §4에 있다. 두 저장소에 함께 쓰는 문제는 [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md).

### 5. 구·신이 서로 불러야 할 때 — ACL

이전 중에는 신 시스템이 아직 안 옮긴 구 기능을 부르고, 구 시스템이 이미 옮긴 신 기능을 부르기도 한다.

```text
 신 시스템 ──> [ACL: 신 모델 ↔ 구 모델 번역] ──> 구 시스템
```

- *ACL(Anti-corruption Layer)*: 두 모델 사이에서 요청·응답을 번역하는 어댑터. 신 시스템의 설계가 구 시스템의 의미(이름·코드값·형식)에 오염되지 않게 막는다.
- Azure 문서는 이전 중 교차 의존을 ACL로 다루라고 적는다. ACL이 없으면 교차 의존이 컴포넌트를 깨뜨리거나 신 시스템이 구 관례를 따르게 된다고 적는다.

## 쓰이는 자료구조·알고리즘

- **라우팅 테이블** — `기능 → 전환 비율`의 맵. 기능 단위로 따로 넓히고 따로 되돌린다(실험 A의 `routePercent`).
- **결정적 해시 버킷** — `hash(고객 ID) mod 100 < 비율`. 같은 고객은 같은 쪽으로 가고(sticky), 비율을 키우면 기존 집합을 포함한다(실험 A 관찰 1). 같은 원리가 피처 플래그 비율 배포에 쓰인다 — [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md).
- **결과 diff 비교기** — control·candidate 값을 비교하고 불일치·예외를 세며 샘플을 남긴다. 비교 함수를 바꿀 수 있어야 한다(Scientist의 `compare`·`compare_errors`, 알려진 차이를 빼는 `ignore`).
- **퍼사드·프록시** — 같은 인터페이스 뒤에서 대상을 고른다. 패턴 자체는 GoF Facade·Proxy([engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)).
- **어댑터(ACL)** — 모델 번역.

## 적용 — 풀어나가는 법

### 1. 순서

1. **결과를 정한다.** Fowler가 인용한 Cartwright·Horn·Lewis의 네 활동 중 첫째가 "원하는 결과를 이해하기"다. "기술 교체"가 아니라 "할인 정책을 하루 안에 바꿀 수 있게" 같은 결과로 쓴다.
2. **자를 단위를 고른다.** 기능·상품군·가치 흐름 단위. 이음새(seam — 코드를 고치지 않고 동작을 바꿀 수 있는 자리, 51 참고)가 있는 곳부터.
3. **퍼사드 또는 추상 계층을 넣는다.** 처음에는 100% 구 시스템으로 보낸다. 이 단계만으로는 동작이 바뀌지 않아야 한다.
4. **새 구현을 붙이고 병행 실행한다.** 사용자에게는 구 결과를 주고 불일치율·후보 예외·지연을 지표로 본다.
5. **불일치가 0(또는 설명 가능한 차이만)이 되면 비율을 넓힌다.** 1% → 10% → 50% → 100%. 각 단계마다 되돌리기 경로(비율 0)를 시험한다.
6. **구 경로를 지운다.** 구 경로로 가는 요청이 0인지 접근 로그로 확인하고, 코드·테이블·퍼사드 규칙을 지운다(54). 이 단계를 일정에 넣지 않으면 두 시스템이 영구히 병존한다.

### 2. 코드 (Java) — 추상 계층 + 라우터 + 비교

```java
interface DiscountPolicy { long discount(long amountWon, int pct); }

final class RoutingDiscount implements DiscountPolicy {     // 퍼사드(branch by abstraction의 추상 뒤)
    private final DiscountPolicy legacy, modern;
    private final Router router;                              // 기능별 비율, 해시 버킷
    private final Comparator comparator;                      // 불일치 지표·샘플
    public long discount(long amountWon, int pct) {
        String customer = RequestContext.customerId();
        if (router.toNew("discount", customer)) return modern.discount(amountWon, pct);
        long c = legacy.discount(amountWon, pct);
        if (router.shadow("discount")) comparator.compare(c, () -> modern.discount(amountWon, pct));  // 실패해도 c를 돌려준다
        return c;
    }
}
```

- 섀도 호출은 요청 경로의 지연을 늘린다. 비동기로 돌리거나 표본 비율로 제한한다. Scientist README도 후보 타임아웃은 막지 않으니 낮은 비율로 시작하라고 적는다.
- 쓰기가 있는 기능은 섀도로 **같은 행에** 두 번 쓰지 않는다. 한쪽을 기준으로 두고 다른 쪽은 동기화·대조(reconciliation)한다(장애 2). Scientist README의 권고는 구·신 **각자의 저장소**에 함께 쓰고 읽을 때 비교하며, 대조 스크립트로 데이터를 맞추는 방식이다.

### 3. 진단

- 불일치율: `science.discount.mismatched / science.discount.compared` 같은 카운터. 불일치 샘플은 입력과 두 결과를 함께 남긴다.
- 전환 비율의 실제값: 라우팅 결정 카운터(`route{feature,target}`)로 목표와 비교한다.
- 구 경로 잔여 트래픽: 구 엔드포인트·구 메서드의 호출 카운터 또는 접근 로그. 0이 일정 기간 이어져야 지운다.
- 남은 과도기 코드: `grep -rn "RoutingDiscount\|routePercent" src/`로 퍼사드가 몇 곳에 남았는지 센다.

## 장애 시나리오와 대처

### 1. 전면 재작성 2년 → 기능 격차로 전환 불가·중단 (⚠ 커리큘럼)

- 현상: 새 시스템이 2년째 "거의 다 됐다". 구 시스템에는 그동안 새 기능이 계속 들어갔다.
- 보이는 형태: 전환 체크리스트의 "구 기능 동등성" 항목이 줄지 않는다. 전환일이 반복해서 밀린다. 운영 지표는 없다(새 시스템이 운영에 나간 적이 없다).
- 원인: 맞춰야 할 목표가 움직인다. Cartwright·Horn·Lewis의 "Patterns of Legacy Displacement"(martinfowler.com)는 한 조직의 반복된 실패를 분석하며 세 번째 핵심 요인으로 **Feature Parity**(현재 기능을 그대로 재현하겠다는 목표)를 들고, 그것이 하루짜리 "빅뱅" 전환 계획으로 이어졌다고 적는다.
- 대처: 기능 하나를 골라 퍼사드 뒤로 옮기고 운영에 내보낸다. "구 기능 전부"가 아니라 "필요한 결과"를 목표로 한다. 쓰이지 않는 구 기능은 옮기지 않고 지운다.

### 2. 신·구 경로가 같은 테이블에 이중 쓰기 → 불일치 (⚠ 커리큘럼)

- 현상: 같은 주문의 할인액이 화면마다 1원 다르다.
- 보이는 형태: 에러 로그는 없다. 정산 대사(reconciliation) 배치에서 차이가 발견된다. 실험 A의 5)처럼 마지막 쓰기가 이긴다.
- 원인: 두 경로가 각자 계산해 같은 행에 쓴다. 어느 쪽이 기준인지 정하지 않았다.
- 대처: 한쪽을 기준(system of record)으로 정하고, 다른 쪽은 그 값을 동기화(CDC)하거나 비교만 한다. 두 저장소에 같은 사건을 남겨야 하면 아웃박스를 쓴다([distributed/16](../../distributed/16-outbox-and-dual-write/2-summary.md)).

### 3. 비교 없이 전환 → 문서화 안 된 동작(반올림·정렬) 소실 (⚠ 커리큘럼)

- 현상: 전환 다음 달, 고객 일부가 "할인액이 1원 적다"고 문의한다.
- 보이는 형태: 단위 테스트 전부 통과. 정산 합계가 구 시스템 시절보다 조금씩 작다. 실험 A에서 v1은 10만 건 중 1.29%가 1원 작았다.
- 원인: 구 시스템의 반올림 규칙(`Math.round`)은 아무 문서에도 없었다. 새 구현은 다른 규칙을 골랐고, 테스트는 .5원 경계를 다루지 않았다. 정렬 순서(동점 처리), 공백 처리, 시간대도 같은 유형이다.
- 대처: 전환 전에 운영 입력으로 병행 실행해 불일치를 0 또는 "설명된 차이"로 만든다. 불일치 샘플에서 찾은 규칙은 특성 테스트로 고정한다([testing](../../testing/README.md) 17 characterization-tests-legacy — 미작성).

### 4. 라우팅 전환 후 구 경로를 지우지 않음 → 두 시스템 영구 병존 (⚠ 커리큘럼)

- 현상: 전환 100%가 1년 전인데 구 시스템 서버·DB·배포 파이프라인이 그대로 있다. 버그 수정을 두 곳에 한다.
- 보이는 형태: 구 엔드포인트 호출이 0이 아니다(배치·관리 화면·외부 파트너 하나가 여전히 부른다). 퍼사드 라우팅 규칙이 계속 늘어난다.
- 원인: 지우는 단계가 일정에 없었다. 잔여 호출자가 누구인지 아무도 모른다.
- 대처: 전환 계획에 "구 경로 제거"를 별도 작업으로 넣는다. 구 경로 호출 카운터에 호출자 식별(서비스 이름·API 키)을 달아 남은 호출자를 찾아 옮긴다. 0이 유지되면 지운다(54 designing-for-deletion).

### 5. 섀도 호출이 운영 지연·부하를 키움

- 현상: 섀도를 켜자 p99 지연이 오르고 새 서비스가 과부하가 된다.
- 보이는 형태: 요청 경로의 지연 = 구 + 신. 새 서비스 오류율은 사용자에게 안 보이지만 비교 지표의 "후보 예외"가 급증한다.
- 원인: 동기 섀도에 표본 제한이 없다. 후보 타임아웃을 막지 않는다(Scientist README의 경고와 같은 지점).
- 대처: 섀도는 비동기·표본 비율(예시: 1%)로 시작한다. 후보 호출에 별도 타임아웃과 격벽을 둔다([reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)).

## 핵심 문장

- Strangler Fig는 퍼사드로 요청을 나눠 기능을 하나씩 옮기고, 다 옮기면 구 시스템을 지우는 점진 이전이다. 위험이 전환일 하루에 몰리지 않는다.
- branch by abstraction은 같은 일을 코드 안에서 한다. 추상 계층 뒤에 두 구현을 두고, 시스템이 계속 빌드·실행되는 상태로 바꾼다.
- 병행 실행은 사용자에게 구 결과를 주면서 새 결과와 비교한다. 실험에서 단위 테스트로는 안 보이던 반올림 차이가 10만 건 중 1.29%로 드러났다.
- 같은 차이를 비교 없이 이중 쓰기로 붙이면 에러 없이 행이 덮인다. 데이터는 기준 저장소 하나를 정하고 나머지는 동기화·대조한다.
- 되돌리기는 비율을 0으로 바꾸는 한 번의 설정 변경이어야 한다. 그리고 구 경로를 지우는 일까지가 이전이다.

## 관련 주제·근거

- 선행
  - [45-monolith-vs-microservices](../45-monolith-vs-microservices/2-summary.md)
  - [testing](../../testing/README.md) 17 characterization-tests-legacy — 미작성
  - [domain-modeling/curriculum](../../domain-modeling/curriculum.md) 19 anti-corruption-layer — 미작성
- 후속·연결
  - 51 legacy-change-techniques(코드 수준의 seam·parallel change) — [51 노트](../51-legacy-change-techniques/2-summary.md)
  - 54 designing-for-deletion(구 경로 제거) — [54 노트](../54-designing-for-deletion/2-summary.md)
  - [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) — expand/contract
  - [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md) — 이중 쓰기
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 비율 배포·해시 버킷
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 원고의 Strangler Fig 한 줄 소개
- 글·문서
  - Martin Fowler, "Strangler Fig", 2024-08-22 (원 글 "Strangler Application" 2004-06-29 — <https://martinfowler.com/bliki/OriginalStranglerFigApplication.html>) <https://martinfowler.com/bliki/StranglerFigApplication.html>
  - Martin Fowler, "BranchByAbstraction", 2014-01-07 <https://martinfowler.com/bliki/BranchByAbstraction.html>
  - Ian Cartwright·Rob Horn·James Lewis, "Patterns of Legacy Displacement"(Feature Parity·Transitional Architecture·Legacy Mimic·Event Interception 등) <https://martinfowler.com/articles/patterns-legacy-displacement/>
  - Martin Fowler, "DarkLaunching" <https://martinfowler.com/bliki/DarkLaunching.html>
  - GitHub Scientist README(control/candidate, 순서 무작위, 예외 기록, 타임아웃 미보호, 쓰기 경로 조언) <https://github.com/github/scientist>
  - Microsoft, Azure Architecture Center "Strangler Fig pattern"(네 단계, ACL, 데이터베이스 세 단계·되돌리기 한계) <https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig>
  - Chris Richardson, microservices.io "Pattern: Strangler application" <https://microservices.io/patterns/refactoring/strangler-application.html>
- 실험 목록
  - 실험 A — 라우팅 비율·sticky·확대 포함 관계, 병행 실행(v1 불일치 1.29% → v2 0), 후보 예외 격리, 이중 쓰기 덮어쓰기, 비율 0 되돌리기. 코드 `scratchpad/sd/50/e50/Strangler.java`, `docker run --rm --cpus=2 eclipse-temurin:21-jdk java Strangler.java`(JDK 21.0.12, nproc 2), 입력 seed 42 고정이라 출력은 재실행해도 같다.
