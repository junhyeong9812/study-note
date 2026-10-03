# domain-modeling/16-bounded-contexts — 바운디드 컨텍스트: 모델이 통하는 경계 — 정리 (힌트)

## 해결하는 문제

회사에 "고객"이라는 단어는 하나다. 하지만 부서마다 뜻이 다르다.

```text
  영업팀이 말하는 고객   = 주문할 수 있는 사람 (신용 한도, 주문 가능 여부)
  지원팀이 말하는 고객   = 티켓을 여는 사람   (SLA 등급, 서비스 제한 여부)
  청구팀이 말하는 고객   = 돈을 내야 하는 사람 (연체 일수, 독촉 단계)
```

- 이 셋을 클래스 `Customer` 하나로 합치면 필드가 계속 늘어난다.
- 더 큰 문제는 **같은 필드가 셋의 뜻을 동시에 진다**는 것이다. 예: `status` 하나가 "주문 가능", "서비스 제한", "연체 단계"를 함께 표현한다.
- 그러면 한 팀이 자기 뜻대로 `status`를 고치면 다른 팀 코드가 조용히 틀린다.

쉬운 예: 학교에서 "반"이라는 말.
- 담임에게 반은 "3학년 2반"이다.
- 방과 후 교실 강사에게 반은 "화요일 로봇반"이다.
- 둘이 같은 출석부 한 장을 쓰면, 한쪽이 "반"을 고칠 때마다 다른 쪽 출석이 엉킨다.
- 해법은 출석부를 나누는 것이다. 각 출석부 안에서는 "반"이 한 가지 뜻이다. 두 출석부는 학생 번호로만 연결한다.

똑같은 구조다.\
**모델(단어의 뜻과 규칙)이 하나로 통하는 범위를 명시적으로 긋는다.** 그 범위가 바운디드 컨텍스트다.

- *모델*: 도메인의 일부 측면을 골라 추상화한 체계. 그 측면의 문제를 푸는 데 쓴다(DDD Reference 2015 "Definitions").
- *바운디드 컨텍스트(Bounded Context)*: 특정 모델이 정의되고 적용되는 경계. 보통 한 하위 시스템이나 한 팀의 작업 범위다(같은 문서 "Definitions").

실무 예:
- 전사 공유 `Customer` 테이블·클래스를 모든 팀이 고친다. 청구팀의 상태값 추가가 영업팀 주문 차단 로직을 깨뜨린다(아래 실험).
- Fowler는 "Customer"·"Product" 같은 다의어에서 이 혼란이 거듭 생긴다고 적고, 전력 회사에서 "meter(계량기)"가 부서마다 다른 뜻이던 예를 든다("BoundedContext", 2014-01-15).

## 동작·원리

### 1. 경계 안은 하나의 뜻, 경계 사이는 번역

```text
 ┌─ 영업 컨텍스트 ──────────┐   ┌─ 지원 컨텍스트 ──────────┐   ┌─ 청구 컨텍스트 ──────────┐
 │ SalesCustomer            │   │ SupportCustomer          │   │ BillingAccount           │
 │  id, creditLimit,        │   │  id, slaLevel,           │   │  customerId, overdueDays,│
 │  orderingBlocked         │   │  restricted              │   │  standing{GOOD,...}      │
 │ "고객 = 주문하는 사람"    │   │ "고객 = 티켓 여는 사람"   │   │ "고객 = 돈 낼 사람"       │
 └───────────▲──────────────┘   └───────────▲──────────────┘   └────────────┬─────────────┘
             │ 번역기                        │ 번역기                         │
             └──────────── StandingChanged(customerId, orderingBlocked, serviceRestricted) ◄┘
                            ↑ 컨텍스트 사이를 오가는 것은 이 메시지뿐 (공유 키 = customerId)
```

- 경계 안에서는 같은 단어가 한 뜻이다. 클래스·테이블·대화가 그 뜻을 따른다.
- 경계 사이에서는 서로의 내부 모델을 직접 읽지 않는다. 합의한 메시지(또는 API)로만 주고받고, 받는 쪽이 자기 말로 번역한다.
- 경계를 넘어 같은 개체를 가리키려면 **식별자만 공유**한다. 위 그림에서는 `customerId`다.
- Fowler는 컨텍스트끼리 무관한 개념(지원 티켓은 지원 컨텍스트에만 있다)도, 공유 개념(고객·상품)도 함께 가진다고 적는다(BoundedContext).

### 2. Evans가 경계를 긋는 축

DDD Reference(2015)의 Bounded Context 처방을 풀면 이렇다.

| 처방 | 뜻 |
|---|---|
| 모델이 적용되는 컨텍스트를 명시적으로 정의한다 | "어디서 이 모델을 쓰면 안 되는가"가 불분명한 상태를 없앤다 |
| 경계를 팀 조직, 애플리케이션의 사용 범위, 물리적 형태(코드베이스·DB 스키마)로 정한다 | 경계는 코드 패키지만이 아니라 팀·저장소·스키마까지 맞춘다 |
| 경계 안에서는 지속적 통합으로 개념·용어를 엄격히 일관되게 유지한다 | 안쪽은 엄격하게 |
| 경계 밖의 문제에 흔들리지 않는다 | 바깥은 번역으로 다룬다 |
| 컨텍스트 안에서는 한 개발 프로세스로 표준화한다(다른 곳에서 같을 필요는 없다) | 컨텍스트마다 방식이 달라도 된다 |

- Reference는 문제의 원인도 적는다. 큰 프로젝트에는 모델이 여럿 생기는 것이 불가피하다. 문제는 서로 다른 모델 위의 코드를 **섞을 때** 생긴다. 버그가 늘고, 신뢰가 떨어지고, 이해가 어려워진다.
- Fowler는 경계를 정하는 요인 중 보통 지배적인 것이 **사람의 문화(언어)** 라고 적는다. 모델이 유비쿼터스 언어 역할을 하므로, 언어가 바뀌는 곳에서 모델도 달라야 한다는 것이다(BoundedContext).
  - *유비쿼터스 언어(ubiquitous language)*: 도메인 모델을 뼈대로 짠 언어. 한 바운디드 컨텍스트 안의 팀 전원이 대화·문서·코드에서 같이 쓴다(DDD Reference "Definitions"). 자세한 것은 [03번](../03-ubiquitous-language/2-summary.md).

### 3. 바운디드 컨텍스트 ≠ 서브도메인 ≠ 마이크로서비스

```text
  문제 공간(무엇을 하는 회사인가)           해법 공간(어떻게 만드나)
  ─────────────────────────              ───────────────────────────
  서브도메인: 주문, 청구, 고객지원 ...  ──>  바운디드 컨텍스트: 모델 경계
     (발견한다)                              (설계한다)
                                                │ 배포 단위로 1:1일 수도, 아닐 수도
                                                ▼
                                          모듈 / 서비스
```

- Khononov는 『Learning Domain-Driven Design』(O'Reilly, 2021)에서 "서브도메인은 **발견**하고, 유비쿼터스 언어를 바운디드 컨텍스트로 나누는 것은 **설계 결정**"이라고 구분한다(2차 정리로 확인 — 원문 쪽은 [?]).
- 서브도메인 분류는 17번에서 다룬다.
- 컨텍스트는 모델 경계이지 배포 단위가 아니다. 모듈러 모놀리스 안의 패키지 경계로도 둘 수 있다. 배포 단위 선택은 [software-design/45](../../software-design/45-monolith-vs-microservices/2-summary.md)에 있다.
- 크기 기준은 저자마다 다르다.
  - Evans(Reference): 크기 기준을 수치로 주지 않는다. 팀·사용 범위·물리 형태로 경계를 정하라고만 한다.
  - Vernon 『IDDD』 2장에는 "Size of Bounded Contexts" 절이 있다(목차로 확인). 절의 세부 권고는 본문을 열지 못해 [?].
  - Fowler(BoundedContext)도 크기를 정하지 않고 언어·문화 요인을 든다.

### 4. 경계 안에서 "같은 단어 다른 뜻"이 다시 생기면

- Reference "Continuous Integration"은 한 컨텍스트에서 여럿이 일하면 모델이 조각나려는 경향이 강하다고 적는다. 팀이 클수록 심하지만 서너 명으로도 심각해질 수 있다고 한다.
- 처방: 코드와 산출물을 자주 합치고, 자동 테스트로 조각남을 빨리 드러낸다. 유비쿼터스 언어를 끊임없이 써서 머릿속 모델을 맞춘다.
- 같은 절은 반대 방향도 경고한다. 시스템을 계속 더 작은 컨텍스트로 쪼개면 통합성과 일관성을 잃는다.
- 신호: 같은 클래스에 `if (용도 == A)` 분기가 늘고, 회의에서 "그 status는 어느 status냐"는 질문이 나온다.
- 이때 선택은 두 가지다. 언어를 다시 통일하거나, 경계를 다시 그어 컨텍스트를 나눈다.

### 실험: 공유 `Customer` vs 컨텍스트별 모델 — 청구팀 변경 하나의 파급

같은 업무를 두 설계로 짰다.
- 설계 A: 영업·지원·청구가 `shared.Customer` 하나를 쓴다. `status` 문자열이 세 뜻을 진다.
- 설계 B: 컨텍스트마다 자기 모델이 있다. 청구가 `StandingChanged(customerId, orderingBlocked, serviceRestricted)`를 내고, 영업·지원은 각자 번역기로 받는다.

요구 변경(청구팀): "연체 31~90일은 독촉 단계(`DELINQUENT`), 90일 초과만 정지(`SUSPENDED`)".

핵심 코드(설계 A):

```java
// shared/Customer.java — 세 컨텍스트가 공유
public String status = "ACTIVE"; // 뜻이 셋: 영업=주문 가능, 지원=서비스 제한, 청구=연체 단계
// sales/OrderPolicy.java
return !"SUSPENDED".equals(c.status) && c.creditLimit > 0;
// billing/Dunning.java — 청구팀이 고친 한 줄
if (c.overdueDays > 90) c.status = "SUSPENDED"; else if (c.overdueDays > 30) c.status = "DELINQUENT";
```

핵심 코드(설계 B):

```java
// billing/Dunning.java — 공개 언어: 하류가 아는 것은 이 두 플래그뿐이다
boolean blocked    = a.standing != BillingAccount.Standing.GOOD;
boolean restricted = a.standing == BillingAccount.Standing.SUSPENDED;
return new StandingChanged(a.customerId, blocked, restricted);
// sales/BillingTranslator.java
c.orderingBlocked = e.orderingBlocked();
```

테스트 4개는 영업·지원의 기대다(연체 45일 주문 불가, 연체 0일 주문 가능, 연체 120일 티켓 LOW, 연체 0일 GOLD 티켓 HIGH).

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-03 — `run.sh`, 출력 발췌)

```text
=== A after billing-only change
 src/billing/Dunning.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
FAIL sales   | 연체 45일 고객은 주문 불가
PASS sales   | 연체 0일 고객은 주문 가능
PASS support | 연체 120일 고객 티켓은 LOW
PASS support | 연체 0일 GOLD 고객 티켓은 HIGH
failures=1
(관찰) support 연체 45일 티켓 우선순위 = HIGH
=== A after fixing sales too
 src/billing/Dunning.java   | 2 +-
 src/sales/OrderPolicy.java | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
...
failures=0
=== B after billing-only change
 src/billing/BillingAccount.java | 2 +-
 src/billing/Dunning.java        | 2 +-
 2 files changed, 2 insertions(+), 2 deletions(-)
PASS sales   | 연체 45일 고객은 주문 불가
PASS sales   | 연체 0일 고객은 주문 가능
PASS support | 연체 120일 고객 티켓은 LOW
PASS support | 연체 0일 GOLD 고객 티켓은 HIGH
failures=0
(관찰) support 연체 45일 티켓 우선순위 = HIGH
=== A: displayName 추가
 src/shared/Customer.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
=== B: displayName 추가(각 컨텍스트가 자기 모델에)
 src/billing/BillingAccount.java  | 2 +-
 src/sales/SalesCustomer.java     | 2 +-
 src/support/SupportCustomer.java | 2 +-
 3 files changed, 3 insertions(+), 3 deletions(-)
=== 공유 Customer 필드별 사용 컨텍스트
status: billing sales support 
creditLimit: sales 
slaLevel: support 
overdueDays: billing
```

관찰:
1. 설계 A에서 청구팀은 **자기 파일 한 줄**만 고쳤다. 컴파일은 통과했다. 그런데 영업 테스트가 깨졌다. 연체 45일 고객이 주문할 수 있게 됐다. 영업 코드는 `"SUSPENDED"`만 막았기 때문이다.
2. 설계 A를 바로잡으려면 영업 파일도 고쳐야 했다. 청구팀 변경이 영업팀 작업이 됐다(2파일).
3. 설계 A에서 지원의 연체 45일 티켓은 LOW → HIGH로 바뀌었다. 테스트가 없어서 아무도 모른다. 지원팀이 정한 적 없는 변화다.
4. 설계 B에서는 청구 파일 2개만 바뀌었고, 영업·지원 테스트가 그대로 통과했다.
5. 설계 B에서도 지원의 45일 티켓은 HIGH로 바뀌었다. 차이는 **그 결정이 어디에 보이나**다. B에서는 `restricted = standing == SUSPENDED` 한 줄(공개 언어의 뜻)이 결정한다. A에서는 지원 코드의 문자열 비교가 우연히 결정했다.
6. 반대 상황: 세 컨텍스트가 모두 "표시 이름"을 새로 필요로 하면, A는 1파일, B는 3파일이 바뀐다. **모든 컨텍스트가 같은 뜻으로 함께 바뀌는 변경**에서는 나눈 쪽이 비싸다.

해석: 경계의 이득은 "변경이 한 컨텍스트 안에서 끝나는 경우"에 나온다. 단, 설계 B가 이번 변경을 견딘 것은 청구가 공개 언어를 처음부터 `blocked = standing != GOOD`처럼 "GOOD이 아니면 차단"으로 정의해 두었기 때문이다. 같은 B라도 `blocked = standing == SUSPENDED`로 정의해 두면, 새 상태 `DELINQUENT`에서 영업 테스트가 A와 똑같이 깨진다(사실 점검 재실행 변형, 같은 환경: `FAIL sales | 연체 45일 고객은 주문 불가`, `failures=1`). 그때도 고칠 곳은 청구의 공개 언어 정의 한 줄이지 영업 코드가 아니다. 경계는 파급을 한 곳(공개 언어 정의)으로 모을 뿐, 그 정의를 바르게 쓰는 일까지 대신하지 않는다. 같은 뜻을 모두가 공유하는 개념이 많다면, 경계를 잘못 그었거나 그 부분이 공유 커널 후보다(18번).

## 쓰이는 자료구조·알고리즘

- **식별자 매핑 표** — 컨텍스트마다 자기 키를 쓰면 `(컨텍스트, 로컬 ID) → 전역 ID` 표가 필요하다. 경계를 넘는 것은 식별자뿐이므로, 이 표가 사실상 컨텍스트 사이의 조인 키다.
- **번역 함수(사상, mapping)** — 상대 모델 → 내 모델의 순수 함수. 실험 B의 `BillingTranslator.on`. 모르는 값이 들어오면 실패를 드러내야 한다(19번).
- **의존 그래프** — 어느 패키지·서비스가 어느 모델을 import하나. 실험의 "필드별 사용 컨텍스트"가 그 축소판이다. `status`처럼 사용자가 셋 이상인 필드가 경계가 흐려진 후보다. 정적 분석으로 경계를 강제하는 법은 [software-design/41-architecture-fitness-rules](../../software-design/41-architecture-fitness-rules/2-summary.md).
- **변경 결합 분석** — 커밋마다 함께 바뀐 폴더를 센다. 자주 같이 바뀌는 두 컨텍스트는 경계가 틀렸을 수 있다는 신호다. 방법은 [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **다의어를 찾는다.** 회의록·요구서·코드에서 같은 단어가 다른 뜻으로 쓰이는 곳을 표로 모은다. "고객", "상품", "주문 완료", "상태"가 흔한 후보다.
2. **뜻이 갈리는 곳에 선을 긋는다.** 선 하나 = 한 언어가 통하는 범위. Evans(Reference)는 팀 조직을 경계 기준의 하나로 들고, Fowler는 언어(사람의 문화)를 보통 지배적인 요인으로 든다.
3. **경계마다 이름을 붙인다.** 그 이름도 언어의 일부가 된다(Reference "Context Map").
4. **경계를 넘는 것을 정한다.** 식별자와 합의한 메시지·API만. 상대 모델 클래스를 import하지 않는다.
5. **경계를 코드로 강제한다.** 패키지 의존 규칙·모듈 시스템·별도 스키마.
6. **컨텍스트 사이 관계를 고른다.** 순응·ACL·공유 커널 등 — 18번.

### 2. 코드 — 경계별 모델과 번역 (Java)

```java
// 영업 컨텍스트: 자기 말로 된 고객. 청구 모델은 모른다
package sales;
public class SalesCustomer {
    private final long id;              // 경계를 넘는 것은 식별자뿐
    private final long creditLimit;
    private boolean orderingBlocked;    // "주문 차단" — 영업의 말
    public boolean canOrder() { return !orderingBlocked && creditLimit > 0; }
    void apply(StandingView v) { this.orderingBlocked = v.orderingBlocked(); }
}

// 청구 이벤트를 영업 말로 옮기는 자리 — 영업 패키지 안에 둔다
package sales;
record StandingView(long customerId, boolean orderingBlocked) {
    static StandingView from(billing.api.StandingChanged e) {
        return new StandingView(e.customerId(), e.orderingBlocked());
    }
}
```

- JPA를 쓴다면 컨텍스트마다 엔티티를 따로 두고, 가능하면 스키마(또는 최소한 테이블 소유)도 나눈다. 같은 테이블을 두 엔티티가 매핑하면 DB 수준에서 다시 공유 모델이 된다.
- 경계를 넘는 메시지 타입(`billing.api.StandingChanged`)은 청구의 내부 패키지와 분리된 `api` 패키지에 둔다. 하류가 import할 수 있는 것은 그것뿐이다.

### 3. 진단 — 공유 모델이 어디서 새나

```bash
# 공유 클래스의 필드가 몇 개 컨텍스트(최상위 패키지)에서 쓰이나 — 셋 이상이면 경계 후보
for f in status creditLimit slaLevel overdueDays; do
  echo "$f: $(grep -rl "\.$f" src/*/ | cut -d/ -f2 | sort -u | tr '\n' ' ')"
done
```

- 결과 해석: 한 필드를 여러 컨텍스트가 **읽기만** 하면 공개 언어로 옮기기 쉽다. 여러 컨텍스트가 **쓰면**(실험 A의 `status`를 청구가 쓰고 영업·지원이 해석) 뜻 충돌이 이미 있을 가능성이 크다.

## 장애 시나리오와 대처

### 1. 전사 공유 "고객" 모델 — 모든 팀이 서로를 깨뜨린다 (⚠ 커리큘럼)

- 현상: 한 팀의 배포 뒤 다른 팀 기능이 이상해진다. 배포한 팀의 테스트는 다 통과했다.
- 보이는 형태: "연체 고객이 주문을 넣었다" 같은 업무 사고 보고. 에러 로그는 없다. 컴파일도 통과한다(실험 A 관찰 1).
- 원인: 한 필드(`status`)가 여러 뜻을 진다. 한 팀이 자기 뜻대로 값을 추가하면, 다른 팀의 해석 코드(`!"SUSPENDED".equals`)가 새 값을 엉뚱하게 분류한다.
- 대처
  - 당장: 상태값 추가를 공유 모델 변경으로 보고, 모든 소비자의 해석 코드를 찾아 함께 고친다(실험 A처럼 2파일+).
  - 근본: 컨텍스트별 모델로 나누고, 경계에는 의미가 고정된 메시지만 둔다(실험 B).

### 2. 아무도 정하지 않은 동작 변화

- 현상: 지원팀이 "연체 고객 티켓이 언제부터 HIGH로 오나"를 묻는다.
- 보이는 형태: 특정 날짜 이후 우선순위 분포가 바뀐다. 관련 커밋은 다른 팀 저장소에 있다.
- 원인: 공유 값의 해석이 하류에 흩어져 있다. 상류 변경이 하류 동작을 바꿔도 하류 테스트가 그 경우를 다루지 않으면 드러나지 않는다(실험 A 관찰 3).
- 대처: 하류가 의존하는 뜻을 메시지 필드로 명시한다(`serviceRestricted`). 그 필드를 바꾸는 일은 계약 변경으로 다룬다. 계약 테스트는 18번.

### 3. 경계는 그었는데 같은 테이블을 공유한다

- 현상: 코드상 컨텍스트는 나뉘었는데 스키마 변경 때마다 여러 팀이 함께 배포한다.
- 보이는 형태: 마이그레이션 PR에 여러 팀 승인이 붙는다. 컬럼 하나 이름 바꾸기에 몇 주가 걸린다.
- 원인: Reference가 말한 "물리적 형태(DB 스키마)"의 경계를 안 맞췄다. DB 수준에서는 여전히 공유 모델이다.
- 대처: 테이블 소유자를 정하고, 다른 컨텍스트는 API·이벤트·복제 뷰로 읽는다. 공유 DB 비용은 [software-design/45](../../software-design/45-monolith-vs-microservices/2-summary.md) 실험 B, 나눈 뒤 조회는 [distributed/20](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md).

### 4. 너무 잘게 나눠 모든 변경이 여러 컨텍스트를 건드린다

- 현상: 기능 하나 추가에 컨텍스트 서너 개의 모델·번역기를 같이 고친다.
- 보이는 형태: 커밋마다 함께 바뀌는 폴더 묶음이 고정돼 있다. 번역기 코드가 도메인 코드보다 길다.
- 원인: 같은 언어가 통하는 범위를 쪼갰다. Reference "Continuous Integration"이 경고한 "더 작은 컨텍스트로 쪼개면 통합성을 잃는다"는 경우다. 실험 관찰 6(표시 이름 추가에 B는 3파일)이 이 비용의 축소판이다.
- 대처: 함께 바뀌는 컨텍스트를 합치거나, 공통 부분을 작은 공유 커널로 뺀다(18번). 경계는 언어가 갈리는 곳에 둔다.

## 핵심 문장

1. 바운디드 컨텍스트는 한 모델(단어의 뜻과 규칙)이 정의되고 적용되는 명시적 경계다.
2. 큰 시스템에 모델이 여럿인 것은 문제가 아니다. 서로 다른 모델의 코드를 섞는 것이 문제다.
3. 경계 안은 엄격하게 하나의 언어로, 경계 사이는 식별자와 합의한 메시지로만 잇는다.
4. 공유 모델에서는 한 팀의 한 줄 변경이 컴파일 오류 없이 다른 팀 규칙을 깨뜨릴 수 있다(실험 A).
5. 모두가 같은 뜻으로 함께 바꾸는 개념이라면 나누는 쪽이 비싸다. 경계는 언어가 갈리는 곳에 긋는다.

## 관련 주제·근거

- 선행
  - [03-ubiquitous-language](../03-ubiquitous-language/2-summary.md) — 유비쿼터스 언어
  - [software-design/02-modularity-coupling-cohesion](../../software-design/02-modularity-coupling-cohesion/2-summary.md) — 결합·응집
  - [software-design/04-decompose-by-change](../../software-design/04-decompose-by-change/2-summary.md) — 변경 이유로 나누기
- 후속·연결
  - [17-subdomains](../17-subdomains/2-summary.md) — 문제 공간의 분류(발견) vs 컨텍스트(설계)
  - [18-context-mapping](../18-context-mapping/2-summary.md) — 컨텍스트 사이 관계 9가지
  - [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) — 외부 모델 번역 계층
  - [20-event-storming](../20-event-storming/2-summary.md) — 경계를 찾는 워크숍
  - [09-domain-events](../09-domain-events/2-summary.md) — 컨텍스트 사이 메시지
  - [software-design/45-monolith-vs-microservices](../../software-design/45-monolith-vs-microservices/2-summary.md) — 배포 단위와 공유 DB
  - [software-design/40-codebase-structure](../../software-design/40-codebase-structure/2-summary.md) — 최상위 폴더를 업무(컨텍스트)로
  - [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) — 데이터 소유와 교차 조회
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 서비스 경계 = 컨텍스트, 콘웨이 법칙
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015, CC BY 4.0) — "Definitions"(model·context·bounded context), "Bounded Context", "Continuous Integration" <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Eric Evans, 『Domain-Driven Design』(Addison-Wesley, 2003 — Reference는 "2004년 책"이라 부른다) 14장 Maintaining Model Integrity — 장 제목은 2차 목차로 확인
  - Martin Fowler, "BoundedContext", 2014-01-15 <https://martinfowler.com/bliki/BoundedContext.html>
  - Vaughn Vernon, 『Implementing Domain-Driven Design』(2013) 2장 Domains, Subdomains, and Bounded Contexts(절 "Size of Bounded Contexts") — 목차로 확인, 본문 권고는 [?]
  - Vlad Khononov, 『Learning Domain-Driven Design』(O'Reilly, 2021) — "서브도메인은 발견, 컨텍스트는 설계" 구분, 해당 장 번호는 [?] — 2차 정리 <https://tigerabrodi.blog/learning-domain-driven-design-ddd>로 확인
- 실험 목록
  - 공유 `Customer` vs 컨텍스트별 모델: 청구 상태값 추가의 `git diff --stat`·영업/지원 테스트 결과, 반대 변경(displayName), 필드별 사용 컨텍스트 — `scratchpad/dm/16/e16/run.sh`, JDK 21.0.12 temurin `--cpus=2 --network none`, git 2.43.0
