# domain-modeling/17-subdomains — 핵심·지원·일반 서브도메인과 투자 배분 — 정리 (힌트)

## 해결하는 문제

개발 인력과 시간은 한정돼 있다. 그런데 시스템의 모든 부분이 똑같이 중요하지는 않다.

```text
  배달 앱 회사가 만드는 것
  ┌──────────────────────┬────────────────────────────┐
  │ 배차 알고리즘          │ 이걸 잘해야 경쟁사를 이긴다   │  ← 여기에 최고 인력
  │ 가게 정산 규칙         │ 우리 방식이 있지만 차별점 아님 │
  │ 로그인·결제 게이트웨이  │ 대부분 회사가 비슷하게 한다    │  ← 사서 쓰면 된다
  │ 시간대·공휴일 계산      │ 대부분 회사가 비슷하게 한다    │
  └──────────────────────┴────────────────────────────┘
```

- 이 구분 없이 일을 배분하면 흔히 거꾸로 된다. 실력 있는 개발자가 인증 프레임워크·자체 시간대 계산 같은 "깔끔하게 정의된 기술 문제"에 몰린다.
- Evans는 이것을 직접 지적한다. 숙련 개발자는 기술 인프라나, 전문 도메인 지식 없이 이해할 수 있는 문제로 쏠리는 경향이 있다(DDD Reference 2015 "Core Domain").

쉬운 예: 식당.
- 요리(레시피·맛)가 식당의 승부처다. 주방장이 직접 한다.
- 예약·포스 단말기는 남들과 같다. 사서 쓴다.
- 식자재 발주표는 우리 가게 방식이 조금 있지만 손님이 그걸 보고 오지는 않는다. 간단하게 만든다.
- 주방장이 포스 단말기를 직접 만들고 있다면, 요리는 누가 하나.

똑같은 구조다.\
**도메인을 부분(서브도메인)으로 나누고, 부분마다 투자 수준을 다르게 정한다.**

- *도메인*: 사용자가 프로그램을 적용하는 지식·활동의 영역(DDD Reference "Definitions").
- *서브도메인*: 도메인을 이루는 응집된 한 부분. 예: 배차, 정산, 인증.

실무 예:
- 결제 PG 연동, OAuth 로그인, 알림 발송을 자체 구현하다 핵심 기능 일정이 밀린다(⚠ 커리큘럼).
- 시간대 변환을 "UTC+9" 같은 고정값으로 자체 구현했다가 서머타임이 있는 해외 지점에서 서머타임 기간 내내(미국 동부는 연 238일) 1시간 어긋난다. "4~10월"처럼 달 단위 규칙으로 고쳐도 해마다 24일은 틀린다(아래 실험).

## 동작·원리

### 1. 세 분류 — 출처별로 다르게 정의한다

```text
                 경쟁 우위?      복잡도      변동성      구현 방식
  핵심(core)      있다           높다        높다        자체 개발, 최고 인력
  일반(generic)   없다           높다        낮다        구매·오픈소스·공개 모델
  지원(supporting) 없다           낮다        낮다        자체 개발 또는 외주(단순하게)
                                    (Khononov 『Learning DDD』 1장 표의 요지로 정리 — 2차 정리는 세 분류의 정의만 확인, 복잡도·변동성 칸은 원문 미확인 [?])
```

Evans(DDD Reference 2015 V부 "Distillation")의 처방:
- **Core Domain**
  - 모델을 졸여 핵심 도메인을 정하고, 그것을 나머지 지원 모델·코드와 쉽게 구별할 수 있게 한다.
  - 핵심은 작게 유지한다.
  - 최고 인력을 핵심에 배치하고, 그에 맞춰 채용한다.
  - 다른 부분의 투자는 "핵심을 얼마나 돕는가"로 정당화한다.
- **Generic Subdomains**
  - 프로젝트의 동기가 아닌 응집된 서브도메인을 찾아 별도 모듈로 뺀다.
  - 그 안에 우리 전문 분야의 흔적을 남기지 않는다.
  - 개발 우선순위는 핵심보다 낮춘다. 핵심 개발자를 배정하지 않는다(그들이 얻을 도메인 지식이 적다).
  - 기성 솔루션(off-the-shelf)이나 공개된 모델을 고려한다.
- "지원(supporting) 서브도메인"이라는 **이름**은 Reference에 독립 패턴으로 나오지 않는다. Reference는 "supporting model and code", "supporting players"라는 표현을 쓴다. 핵심·지원·일반의 세 분류를 이름 붙여 정리한 것은 Vernon 『IDDD』 2장과 Khononov 『Learning DDD』 1장이다. IDDD는 출판사 견본(목차·색인)에서 "Subdomains — types of, 52", "Supporting Subdomains, 52", "Generic Subdomains, 52"로 2장 안("Focus on the Core Domain" 절, 50~53쪽)에 있음을 확인했다. Khononov는 2차 정리로 확인했다.

Khononov의 정의(2차 정리로 확인한 문장의 요지):
- 핵심: 회사를 경쟁자와 구별하는 활동(새 상품 발명, 원가 절감 최적화 등).
- 일반: 모든 회사가 같은 방식으로 수행하는, 복잡하지만 경쟁 우위를 주지 않는 활동.
- 지원: 사업을 돕지만 경쟁 우위는 주지 않는 활동.

### 2. 분류가 투자를 정한다

```text
  분류         모델링 깊이               테스트·리뷰          인력·조달
  ─────────    ───────────────          ─────────────       ─────────────────
  핵심         풍부한 도메인 모델,       불변식 테스트 최대    최고 인력, 자체 개발
               이벤트 스토밍(20)
  지원         트랜잭션 스크립트·CRUD    기본                  자체(주니어)·외주
               로도 충분할 수 있다(07)
  일반         모델링하지 않는다 —       통합 테스트·계약       구매·라이브러리·SaaS
               공개 모델을 그대로 쓴다    (외부 변경 대비)       + ACL로 감싼다(19)
```

- 지원 서브도메인에 핵심 수준 모델링을 쓰면 매핑 비용만 는다(07번의 ⚠ "단순 CRUD에 풍부한 모델"과 같은 문제).
- 일반 서브도메인은 사서 쓰더라도 **외부 모델이 핵심을 오염시키지 않게** 번역 계층을 둔다(19번).

### 3. 분류는 바뀐다

```text
  시간 →
  핵심 ──(경쟁사가 따라잡고 시장 표준이 됨)──> 일반
  지원 ──(그 영역에서 차별화를 시작)──────────> 핵심
  일반 ──(맞는 기성품이 없음)────────────────> 직접 만들되 핵심 인력은 쓰지 않음
```

- 분류는 회사 전략에 대한 판단이지 코드의 성질이 아니다. 같은 "추천" 기능이 어떤 회사에는 핵심, 다른 회사에는 일반이다.
- 그래서 분류는 주기적으로 다시 본다. Evans는 핵심을 설명하는 한 쪽 분량의 Domain Vision Statement를 일찍 쓰고 이해가 깊어질 때마다 고치라고 한다(Reference "Domain Vision Statement").

### 4. 서브도메인과 바운디드 컨텍스트의 관계

- 서브도메인은 문제 공간의 분류다. 바운디드 컨텍스트는 해법 공간의 모델 경계다(16번).
- 1:1로 맞으면 단순하다. 하지만 한 컨텍스트가 여러 서브도메인을 담을 수도, 한 서브도메인이 여러 컨텍스트로 나뉠 수도 있다.
- Vernon 『IDDD』 2장 "Subdomains and Bounded Contexts at Work" 절이 이 관계를 다룬다(목차로 확인, 세부 권고 [?]).

### 실험: 일반 서브도메인(시간대 규칙)을 직접 만들면

시간대 변환은 "대부분의 회사가 같은 방식으로 하는" 일반 서브도메인의 전형이다. 공개 모델로 IANA tz database가 있다. 이것을 쓰지 않고 직접 만든 두 규칙을 2026·2027년 매일 정오(뉴욕 현지)에 대해 tzdb와 비교했다.

```java
static ZoneId NY = ZoneId.of("America/New_York");
static int fixed(LocalDate d){ return -5; }                                     // 자작 1: 늘 UTC-5
static int monthRule(LocalDate d){ int m=d.getMonthValue(); return (m>=4 && m<=10) ? -4 : -5; } // 자작 2: 4~10월 서머타임
// 매일 정오의 실제 오프셋
int real = NY.getRules().getOffset(d.atTime(12,0).atZone(NY).toInstant()).getTotalSeconds()/3600;
```

(실험, JDK 21.0.12 temurin `--cpus=2`, 2026-10-03 — `Tz.java`)

```text
JDK 21.0.12 tzdb 2026b
2026: 고정 UTC-5 틀린 날 238/365, 월 규칙(4~10월) 틀린 날 24  (정오 기준)
   월 규칙이 틀린 날: 첫 2026-03-08, 마지막 2026-03-31
   tzdb 전이: 2026-03-08T02:00 -05:00->-04:00 / 2026-11-01T02:00 -04:00->-05:00
2027: 고정 UTC-5 틀린 날 238/365, 월 규칙(4~10월) 틀린 날 24  (정오 기준)
   월 규칙이 틀린 날: 첫 2027-03-14, 마지막 2027-11-06
   tzdb 전이: 2027-03-14T02:00 -05:00->-04:00 / 2027-11-07T02:00 -04:00->-05:00
```

관찰:
1. 고정 오프셋은 1년 중 238일(서머타임 기간) 1시간 틀린다.
2. "4~10월" 규칙도 2026·2027년 모두 24일 틀린다. 2026년에는 3월 8~31일이다. 2027년에는 3월 14~31일(18일)과 11월 1~6일(6일)이다. 전이일이 해마다 다르기 때문이다(3월 둘째 일요일·11월 첫째 일요일 — 위 tzdb 전이 줄). 두 전이일 사이는 현행 규칙에서 늘 34주(238일)라서, 틀린 날 수 238·24는 이 규칙이 유지되는 한 해마다 같다(계산).
3. JDK 21.0.12에 든 tzdb 판은 2026b다. IANA 최신판은 2026e(2026-09-29 공표, IANA tzdb NEWS)라서, JDK에 든 판은 IANA보다 늦을 수 있다. 이 규칙 표는 정부가 제도를 바꾸면 갱신된다. 직접 만든 규칙은 그 갱신도 직접 따라가야 한다.

해석: "시간대는 간단하다"는 판단이 일반 서브도메인을 자체 구현하게 만든다. 실제로는 복잡도가 높고 외부(각국 정부)가 바꾼다. Reference의 처방대로 공개 모델(tzdb, `java.time`)을 쓰는 쪽이 비용이 작다. 이 실험이 보이는 것은 "자체 구현의 숨은 복잡도" 하나다. 어느 서브도메인이 핵심인가는 실험으로 정할 수 없는 사업 판단이다.

## 쓰이는 자료구조·알고리즘

- **분류 표(서브도메인 × 속성)** — 행 = 서브도메인, 열 = 경쟁 우위·복잡도·변동성·구현 방식. 위 §1의 표가 그것이다. DDD Crew의 "Core Domain Chart"는 이를 두 축(사업 차별화 × 모델 복잡도) 그림으로 그린다 <https://github.com/ddd-crew/core-domain-charts>.
- **규칙 테이블(tz rules)** — 일반 서브도메인을 공개 모델로 대체한 예. tzdb는 지역별 `(유효 구간, 오프셋, 서머타임 규칙)` 표다. 시간 쪽은 [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md).
- **변경 빈도 집계(churn)** — 커밋 로그에서 폴더별 변경 수를 센다. 변동성이 높은 서브도메인을 찾는 한 신호다. 방법은 [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md). 변경이 많다고 곧 핵심은 아니다(버그가 많아도 많다).

## 적용 — 풀어나가는 법

### 1. 순서

1. **회사가 돈을 버는 이유를 한 쪽으로 쓴다.** Evans의 Domain Vision Statement(약 한 쪽).
2. **서브도메인을 나열한다.** 업무 흐름(이벤트 스토밍 20번의 큰 그림)에서 응집된 덩어리를 찾는다.
3. **각각 분류한다.** "이게 경쟁자보다 나으면 고객이 우리를 고르나?" → 예면 핵심. "대부분의 회사가 똑같이 하나?" → 예면 일반. 나머지는 지원.
4. **투자를 맞춘다.** 핵심 = 최고 인력·풍부한 모델. 지원 = 단순한 구현. 일반 = 구매·라이브러리 + ACL.
5. **표시한다.** Reference "Highlighted Core": 핵심 요소를 저장소에서 표시해 개발자가 안팎을 쉽게 알게 한다.
6. **주기적으로 다시 분류한다.**

### 2. 코드 — 일반 서브도메인을 공개 모델에 맡기고 경계를 둔다 (Java)

```java
// 핵심(배차)은 시간대 규칙을 모른다. "가게 현지 시각"이라는 자기 말만 쓴다
package dispatch;
public interface StoreClock {
    ZonedDateTime localNow(StoreId store);           // 우리 언어
}

// 일반 서브도메인은 공개 모델(tzdb)에 위임 — 직접 오프셋을 계산하지 않는다
package infra.time;
public final class TzdbStoreClock implements dispatch.StoreClock {
    private final Clock clock; private final StoreZoneRepository zones;
    public ZonedDateTime localNow(StoreId store) {
        return ZonedDateTime.now(clock).withZoneSameInstant(zones.zoneOf(store)); // ZoneId.of("America/New_York") 등
    }
}
```

- 핵심 패키지는 인터페이스만 보고, 구현은 인프라 쪽에 둔다. 일반 서브도메인 구현을 다른 라이브러리로 바꿔도 핵심 코드는 그대로다.
- 결제·인증도 같다. PG SDK·OAuth 라이브러리 모델을 핵심 패키지에 import하지 않는다(19번).

### 3. 진단 — 핵심 인력이 어디에 쓰이나

```bash
# 최근 6개월, 폴더(서브도메인)별 서로 다른 작성자 수 — 핵심 인력이 일반 서브도메인에 몰려 있는지 본다
git log --since=6.months --name-only --format='@%an' \
 | awk '/^@/{a=$0; next} NF{split($0,p,"/"); print p[1]"/"p[2]"\t"a}' \
 | sort -u | cut -f1 | sort | uniq -c | sort -rn | head
```

- 결과의 각 행은 "폴더별 서로 다른 작성자 수"다. 인증·알림·자체 유틸 폴더에 핵심 팀원이 많이 보이면 투자 배분을 다시 본다.
- 이 숫자는 신호일 뿐이다. 분류 판단은 사람(사업 판단)이 한다.

## 장애 시나리오와 대처

### 1. 일반 서브도메인 자체 구현에 핵심 역량 소진 (⚠ 커리큘럼)

- 현상: 자체 인증·자체 결제 게이트웨이·자체 알림 서버 유지보수에 팀 시간이 계속 들어간다. 핵심 기능 로드맵이 밀린다.
- 보이는 형태: 스프린트의 상당 부분이 "인증 토큰 갱신 버그", "PG 응답 형식 변경 대응" 같은 티켓이다. 핵심 기능 리드타임이 길어진다.
- 원인: 일반 서브도메인을 "단순하다"고 보고 직접 만들었다. 실제로는 복잡도가 높고 외부가 바꾼다(실험: 자작 시간대 규칙이 2026·2027년 각각 24~238일 틀림).
- 대처
  - 기성 솔루션·공개 모델로 교체를 검토한다(Reference Generic Subdomains).
  - 교체 전에 핵심 코드와의 경계를 인터페이스·ACL로 세운다. 교체 비용이 그 경계 안으로 줄어든다.
  - 일반 서브도메인 작업에 핵심 개발자를 배정하지 않는다(Reference).

### 2. 핵심인데 외주·패키지로 처리했다

- 현상: 차별화하려는 기능을 패키지 설정으로 구현했다. 원하는 규칙 변경이 패키지 한계에 막힌다.
- 보이는 형태: "벤더 로드맵에 있음", "커스터마이징 견적 대기" 상태의 요구가 쌓인다.
- 원인: 경쟁 우위가 있는 부분을 일반으로 분류했다.
- 대처: 핵심으로 재분류하고 자체 모델로 옮긴다. 이전 기간에는 패키지를 ACL 뒤에 두고 단계적으로 바꾼다([software-design/50](../../software-design/50-legacy-migration-strangler-fig/2-summary.md)).

### 3. 지원 서브도메인에 과한 모델링

- 현상: 단순 코드표 관리·관리자 화면에 애그리거트·도메인 이벤트·리포지토리 계층을 다 만들었다.
- 보이는 형태: 필드 하나 추가에 엔티티·DTO·매퍼·이벤트 파일이 같이 바뀐다.
- 원인: 모든 부분에 같은 투자 수준을 적용했다.
- 대처: 지원 서브도메인은 트랜잭션 스크립트·CRUD로 단순화한다(07번). 깊은 모델링은 핵심에 쓴다.

### 4. 분류가 낡았다

- 현상: 몇 년 전 핵심이던 기능이 지금은 시장 표준인데 여전히 최고 인력이 유지보수한다.
- 보이는 형태: 해당 기능 개선이 고객 지표를 거의 움직이지 않는다.
- 원인: 분류를 처음 한 번만 했다.
- 대처: Domain Vision Statement를 갱신하고 분류를 다시 한다. 일반이 된 부분은 구매·단순화를 검토한다.

## 핵심 문장

1. 모든 부분을 똑같이 잘 만들 수는 없다. 서브도메인 분류는 투자를 어디에 쓸지 정하는 도구다.
2. Evans는 핵심을 작게 두고 최고 인력을 쓰며, 일반 서브도메인은 떼어 내 기성품·공개 모델을 고려하라고 한다.
3. 핵심·지원·일반의 세 이름은 Vernon·Khononov가, 속성 표(경쟁 우위·복잡도·변동성)는 Khononov가 정리한 것이다.
4. 일반 서브도메인은 "쉬워 보이지만 복잡하고 남이 바꾸는" 경우가 많다 — 자작 시간대 규칙은 2026·2027년 각각 24~238일 틀렸다(실험).
5. 분류는 코드의 성질이 아니라 사업 판단이며, 시간이 지나면 바뀐다.

## 관련 주제·근거

- 선행
  - [16-bounded-contexts](../16-bounded-contexts/2-summary.md) — 모델 경계(해법 공간)
- 후속·연결
  - [18-context-mapping](../18-context-mapping/2-summary.md) — 일반 서브도메인(외부 제품)과의 관계
  - [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) — 구매한 제품 모델을 감싸기
  - [20-event-storming](../20-event-storming/2-summary.md) — 큰 그림에서 서브도메인 찾기
  - [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md) — 지원 서브도메인에 맞는 단순한 패턴
  - [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) — 시간대 규칙 심화
  - [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md) — 변경 빈도로 보는 투자
  - [software-design/12-simple-design-and-yagni](../../software-design/12-simple-design-and-yagni/2-summary.md) — 필요한 만큼만 설계
- 글·문서
  - Eric Evans, 『Domain-Driven Design Reference』(2015) V부 Distillation — "Core Domain", "Generic Subdomains", "Domain Vision Statement", "Highlighted Core", "Segregated Core" <https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf>
  - Eric Evans, 『Domain-Driven Design』 15장 Distillation — 장 제목은 2차 목차로 확인
  - Vaughn Vernon, 『Implementing Domain-Driven Design』 2장(절 "Focus on the Core Domain" 50쪽, "Subdomains and Bounded Contexts at Work" 44쪽) — 출판사 견본 목차·색인으로 확인(<https://ptgmedia.pearsoncmg.com/images/9780321834577/samplepages/0321834577.pdf>), 본문 세부 [?]
  - Vlad Khononov, 『Learning Domain-Driven Design』(O'Reilly, 2021) 1장 — 세 분류의 정의·속성 표. 원문을 열지 못해 2차 정리로 확인(<https://tigerabrodi.blog/learning-domain-driven-design-ddd>, 검색 요약), 표의 정확한 칸 표현은 [?]
  - DDD Crew, "Core Domain Charts"(README는 CC BY 4.0, 저장소 `LICENCE.md` 파일은 CC BY-SA 4.0 — 2026-10-03 확인) <https://github.com/ddd-crew/core-domain-charts>
  - IANA Time Zone Database <https://www.iana.org/time-zones>, 판 목록 <https://data.iana.org/time-zones/tzdb/NEWS>
- 실험 목록
  - 자작 시간대 규칙(고정 UTC-5, 4~10월 서머타임) vs tzdb 2026b — 2026·2027년 매일 정오 오프셋 비교, 틀린 날 수 — `scratchpad/dm/16/e17/Tz.java`, JDK 21.0.12 temurin `--cpus=2 --network none`
