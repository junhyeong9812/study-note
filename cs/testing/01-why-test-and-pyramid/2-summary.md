# testing/01-why-test-and-pyramid — 테스트의 목적, 피라미드, 크기와 범위 — 정리 (힌트)

## 해결하는 문제

코드를 고칠 때마다 "다른 곳이 깨지지 않았나"를 사람이 손으로 확인하면, 확인 비용이 코드 크기만큼 커진다.\
결국 확인을 건너뛰고, 문제는 운영에서 사용자가 먼저 발견한다.

```text
  자동 테스트 없음                              자동 테스트 있음
  변경 ──> 손으로 확인(일부만) ──> 배포            변경 ──> 테스트 수천 개 실행(수 초~수 분) ──> 배포
                 │                                         │
          빠뜨린 곳에서 운영 장애                     깨진 동작을 커밋 전에 발견
          → 변경이 무서워진다 → 코드가 굳는다          → 바꿀 수 있는 코드로 남는다
```

쉬운 예: 엑셀 가계부 수식을 하나 고칠 때마다 모든 칸을 눈으로 다시 확인한다고 하자.\
칸이 100개일 때는 할 만하다. 1만 개가 되면 아무도 확인하지 않는다.\
똑같은 구조다.\
코드도 커질수록 "손 확인"은 빠지고, 테스트가 없으면 변경 하나가 어디까지 번지는지 모른다([software-design/01](../../software-design/01-complexity/2-summary.md)의 unknown unknowns).

실무 예: SWE@G 11장의 Google Web Server(GWS) 이야기.
- 팀이 커지며 출시가 점점 느려지고 버그가 늘었다. 원문: "At one point, more than 80% of production pushes contained user-affecting bugs that had to be rolled back."
- 기술 리더가 "새 변경에는 테스트를 포함하고, 테스트를 계속 돌린다"는 정책을 세웠다.
- 원문: "Within a year of instituting this policy, the number of emergency pushes dropped by half." 같은 기간에 변경 수는 기록적으로 많았다고 적는다.
- 해석: 수치는 한 팀의 경험담이다. 통제 실험이 아니므로 "테스트를 넣으면 긴급 배포가 반으로 준다"는 일반 법칙으로 읽지 않는다.

## 동작·원리

### 1. 테스트가 주는 것 — 목적

SWE@G 11장 "Why Do We Write Tests?" 절의 하위 절 "Benefits of Testing Code"가 꼽는 이득(원문 항목: Less debugging, Increased confidence in changes, Improved documentation, Simpler reviews, Thoughtful design, Fast, high-quality releases).

| 이득 | 뜻 |
|---|---|
| 결함 감소 | 코드 수명 내내 결함이 적다 |
| 변경 자신감 | 리팩터링·기능 추가 때 기존 동작이 지켜지는지 바로 안다 |
| 문서 | 테스트가 "이 코드는 이렇게 쓰고 이렇게 동작한다"를 실행 가능한 형태로 보여 준다 |
| 리뷰 단순화 | 리뷰어가 동작을 머리로 시뮬레이션하지 않고 테스트로 확인한다 |
| 설계 압력 | 테스트하기 어려운 코드는 대개 결합이 강하다 → 설계를 다시 보게 된다 |
| 빠른 출시 | 위가 쌓여 자주, 안전하게 배포한다 |

- **비욘세 규칙(Beyoncé Rule)**: "If you liked it, then you shoulda put a test on it." 깨지면 안 되는 것은 테스트로 지킨다는 뜻이다(SWE@G 11장).
  - 성능·보안·장애 상황의 동작처럼 "기능 목록"에 안 보이는 것도 포함된다.
- 테스트가 **못 하는 것**: 테스트는 실행한 경우만 확인한다. 실행하지 않은 입력·환경의 결함은 남는다. SWE@G 11장도 후반 절 "The Limits of Automated Testing"에서 자동 테스트로 판단하기 어려운 영역(예: 검색 결과 품질처럼 사람의 판단이 필요한 것, 탐색적 테스트)을 따로 둔다.

### 2. 두 개의 축 — 크기(size)와 범위(scope)

"단위 테스트냐 통합 테스트냐"라는 말에는 사실 두 가지 질문이 섞여 있다.

```text
                         범위(scope) — 무엇을 검증하나 (코드 경로)
                    좁음(단위)          중간(통합)            넓음(E2E)
  크기(size)    ┌──────────────────┬───────────────────┬───────────────────┐
  무엇을 쓰나   │ 클래스 하나,      │ 서비스 + 인메모리  │ (드묾)             │
  small         │ 한 프로세스       │ Fake 저장소        │                    │
  (1 프로세스)  ├──────────────────┼───────────────────┼───────────────────┤
  medium        │ (드묾)            │ 서비스 + 같은 기계 │ 브라우저+서버를    │
  (1 머신)      │                   │ 의 실제 DB         │ 한 기계에서        │
                ├──────────────────┼───────────────────┼───────────────────┤
  large         │                   │                    │ 여러 머신의 실제   │
  (여러 머신)   │                   │                    │ 시스템 전체        │
                └──────────────────┴───────────────────┴───────────────────┘
```

- SWE@G 11장 원문: "Size refers to the resources that are required to run a test case ... Scope refers to the specific code paths we are verifying."
  - *크기(size)*: 테스트를 돌리는 데 필요한 자원(프로세스·스레드·네트워크·디스크·시간). 느림과 비결정성의 원천을 제한한다.
  - *범위(scope)*: 테스트가 **검증하는** 코드 경로의 넓이. 실행만 되는 코드가 아니라 결과를 확인하는 코드다.
- 크기 제약(SWE@G 11장 "Test Size")

| 크기 | 허용 | 금지 |
|---|---|---|
| small | 한 프로세스(많은 언어에서 한 스레드로 더 좁힌다) | sleep, I/O, 그 밖의 블로킹 호출 → 네트워크·디스크 접근 불가 |
| medium | 여러 프로세스·스레드, `localhost` 네트워크 호출(예: 같은 기계의 DB) | `localhost` 밖으로의 네트워크 호출 |
| large | 여러 머신에 걸친 실행 | — (Google은 주로 전체 시스템 E2E와 대역을 쓸 수 없는 레거시용으로 쓴다) |

- 범위 정의(SWE@G 11장 "Test Scope")
  - *좁은 범위*(흔히 *단위 테스트*): 클래스·메서드 같은 작은 부분의 로직을 검증한다.
  - *중간 범위*(흔히 *통합 테스트*): 적은 수의 컴포넌트 사이 상호작용을 검증한다(예: 서버와 DB).
  - *넓은 범위*(흔히 *E2E·시스템 테스트*): 시스템의 여러 부분이 함께 만드는 동작을 검증한다.
- Google은 범위와 상관없이 **가능하면 small로** 쓰라고 권한다. small이면 빠르고 결정적이기 쉽다(11장).
  - *결정적(deterministic)*: 같은 코드에 대해 몇 번을 돌려도 같은 결과가 나온다. 반대가 불안정(flaky) 테스트다([09](../09-flaky-tests/2-summary.md)).

### 3. 피라미드 — 범위별 비율

```text
                 /\
                /  \        E2E       ~5%   느림·비쌈·불안정, 그러나 "진짜로 동작하나"의 마지막 확인
               /----\
              /      \      통합      ~15%  경계(DB·다른 서비스)가 맞물리는지
             /--------\
            /          \    단위      ~80%  로직 대부분, 밀리초 단위, 실패 위치가 정확
           /____________\
```

- 비율의 출처: SWE@G 11장 원문 "As a very rough guideline, we tend to aim to have a mix of around 80% ... unit tests ...; 15% ... integration tests ...; and 5% end-to-end tests." — "아주 대략적인 지침"이라고 스스로 단서를 단다.
- 피라미드 그림의 기원: Fowler "TestPyramid"(2012)는 Mike Cohn의 『Succeeding with Agile』(2009) "Test Automation Pyramid"를 출처로 든다.
- Fowler의 근거: UI를 거치는 E2E 테스트는 "brittle, expensive to write, and time consuming to run".
- 같은 글: 상위 테스트가 실패하면 기능 코드의 버그와 함께 "a missing or incorrect unit test"가 있다는 신호다. → 그 결함을 잡는 하위 테스트를 추가한다.
- SWE@G는 80/15/5를 "we tend to aim"이라는 목표로 쓰되 "very rough guideline"이라는 단서를 단다(11장). 비율 자체보다 그 비율이 만드는 결과(빠르고 믿을 만한 피드백)를 보라는 것은 이 노트의 해석이다. SWE@G도 "If you emphasize integration testing ... take longer to run but catch more issues between components"라며 다른 균형을 허용한다. 단위 테스트는 "a contract between two systems developed by different teams" 같은 컴포넌트 사이 상호작용을 검증하지 못한다.

### 4. 안티패턴 두 개

```text
   아이스크림 콘                 모래시계
   ███████████  E2E 많음        █████████  E2E 많음
    █████████                      ███
      ███      통합 적음            █      통합 적음
       █       단위 적음           ███
                                █████████  단위 많음
```

- *아이스크림 콘(ice cream cone)*: E2E는 많고 통합·단위는 적다. SWE@G: "slow, unreliable, and difficult to work with". 프로토타입을 서둘러 운영에 올리고 테스트 부채를 갚지 않은 프로젝트에서 흔하다.
- *모래시계(hourglass)*: E2E와 단위는 많고 통합이 적다. 콘보다는 낫지만 중간 범위 테스트로 더 빨리 잡을 실패가 E2E에서 터진다. 원인: 결합이 강해 의존 하나만 따로 띄우기 어렵다(SWE@G 11장).
- 해석: 둘 다 E2E 비중이 커서 "느리고 불안정한 CI → 실패를 무시 → 테스트가 가치를 잃음"으로 이어지기 쉽다. 근거가 되는 수치는 같은 장의 다른 절("Case Study: Flaky Tests Are Expensive")에 있다. 불안정 비율이 1%에 가까워지면 테스트가 가치를 잃기 시작하고, Google의 불안정 비율은 약 0.15%로 "thousands of flakes every day"다.

### 실험: 크기별 실행 시간과, 층마다 잡는 결함

같은 코드에 small 테스트 1,001개와 medium 테스트 1개를 둔다.
- small: 배송비 규칙 1,000개 경우(`@ParameterizedTest`) + 인메모리 Fake 저장소로 "최근 출고 목록" 1개.
- medium: 같은 "최근 출고 목록"을 실제 PostgreSQL 17 컨테이너에 JDBC로 붙여 1개.
- 저장소 SQL에는 결함을 심었다. "출고된 것만"이라는 `WHERE shipped_at IS NOT NULL`이 빠졌다.

```java
// 운영 코드 — JdbcShipmentRepository.recentShipped (결함 포함)
String sql = "SELECT order_id, shipped_at FROM shipment ORDER BY shipped_at DESC LIMIT ?";

// small 테스트의 Fake — 인메모리 리스트, "출고된 것만"을 올바르게 구현
public List<Shipment> recentShipped(int n) {
    return rows.stream().filter(s -> s.shippedAt() != null)
            .sorted(Comparator.comparing(Shipment::shippedAt).reversed()).limit(n).toList();
}

// 두 테스트의 단언은 같다: o-1(10/1 출고), o-2(미출고), o-3(10/2 출고) 저장 후
assertThat(repo.recentShipped(2)).extracting(Shipment::orderId).containsExactly("o-3", "o-1");
```

(실험, JDK 21.0.12 temurin · JUnit Platform 1.13.4 / Jupiter 5.13.4 · AssertJ 3.27.4 · PostgreSQL 17.11 · pgJDBC 42.7.7 · 컨테이너 `--cpus=2`, 2026-10-03)

```text
postgres:17 컨테이너 기동~접속 가능: 5655 ms

### SmallTest
Test run finished after 2929 ms        (3회: 2929 / 2182 / 2570 ms)
[      1001 tests successful      ]
### MediumTest
Test run finished after 1471 ms        (3회: 1471 / 1153 / 1383 ms)
[         1 tests failed          ]
│              Expecting actual:
│                ["o-2", "o-3"]
│              to contain exactly (and in same order):
│                ["o-3", "o-1"]
```

- 시간: small 1,001개가 2.2~2.9초, medium 1개가 1.2~1.5초에 DB 기동 5.7초가 따로 든다(실행마다 다르다. 위는 3회 범위, 기동은 1회). 같은 날 같은 코드를 다시 3회 돌렸을 때는 small 2.7~3.2초, medium 1.4~1.6초, 기동(`pg_isready` 응답까지) 4.1초였다. 개당으로 보면 small은 수 밀리초, medium은 초 단위다.
  - 이 시간에는 JVM 기동·JDBC 드라이버 적재가 섞여 있다. 정밀 측정이 아니라 자릿수 비교다.
- 결함: Fake를 쓴 small 테스트는 **초록**이었다. Fake는 SQL을 실행하지 않으니 SQL 결함을 볼 수 없다.
- 실제 PostgreSQL에서는 미출고 `o-2`가 맨 앞에 왔다. PostgreSQL 문서(7.5 Sorting Rows): "NULLS FIRST is the default for DESC order". `ORDER BY shipped_at DESC`에서 NULL이 먼저 나온다.
- 반대 방향도 확인했다. SQL을 고치고 배송비 경계를 `>=` → `>`로 망가뜨리면, medium은 통과하고 small 1,001개 중 `[501] 30000` 한 건만 실패했다. 실패한 입력값(30,000)이 곧 결함 위치다.

```text
### MediumTest (SQL 수정 + 배송비 경계 결함 주입)
[         1 tests successful      ]
### SmallTest (SQL 수정 + 배송비 경계 결함 주입)
│     │  ├─ [501] 30000 ✘
[      1000 tests successful      ]
[         1 tests failed          ]
```

- 관찰: 층마다 **볼 수 있는 결함이 다르다.** 로직 결함은 small이 빠르고 정확하게 잡는다. 경계(SQL·DB 방언)의 결함은 그 경계를 실제로 실행하는 medium만 잡는다.
- 그래서 피라미드는 "단위 테스트만"이 아니다. 아래층을 두껍게 하되, 경계마다 중간 테스트를 둔다([08](../08-integration-tests-real-dependencies/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **크기 = 자원 제약 표.** small/medium/large는 "허용 자원 집합"의 포함 관계다(small ⊂ medium ⊂ large). 자원을 넓힐수록 비결정성의 원천(스레드 스케줄·네트워크 지연·외부 상태)이 늘어난다.
- **Fake = 인메모리 자료구조.** 위 실험의 Fake 저장소는 `ArrayList` + 정렬·필터다. 빠르지만 실제 구현(SQL)과 다른 코드이므로, 둘이 같은 계약을 지키는지는 따로 확인해야 한다([03](../03-test-doubles/2-summary.md)).
- **결함 국소화 = 탐색 공간 줄이기.** 실패한 테스트가 실행한 코드 경로가 좁을수록 원인 후보가 적다. 좁은 범위 테스트 실패는 후보를 클래스 하나로, E2E 실패는 시스템 전체로 남긴다.
  - 같은 생각이 `git bisect`(커밋 이진 탐색)다. 테스트가 결정적이어야 이진 탐색이 성립한다.
- **포트폴리오 비용 모델(해석).** 테스트 한 개의 비용 ≈ 작성 + 실행 시간 × 실행 횟수 + 불안정으로 인한 조사. 실행 횟수가 하루 수백~수천 번이면 실행 시간과 불안정 비율이 비용을 지배한다.

## 적용 — 풀어나가는 법

1. **지킬 동작 목록부터.** 비욘세 규칙대로 "깨지면 안 되는 것"을 적는다(기능·경계값·오류 처리·성능 상한).
2. **각 동작을 가장 작은 크기·좁은 범위에서 검증할 수 있나** 본다.
   - 로직이 I/O와 엉켜 있으면 small로 못 쓴다 → 로직을 떼어 내는 설계 변경이 먼저다([software-design/26](../../software-design/26-functional-core-imperative-shell/2-summary.md)).
3. **경계마다 중간 테스트.** DB·메시지 브로커·외부 API 어댑터는 실제(또는 컨테이너) 의존으로 몇 개씩 검증한다.
4. **E2E는 핵심 사용자 여정 몇 개.** 로그인 → 주문 → 결제처럼 "이게 안 되면 장사가 멈춘다"는 경로만.
5. **크기별로 나눠 돌린다.** 커밋마다 small, 병합 전 medium, 배포 전·주기적으로 large.

```java
@Tag("medium")                                   // JUnit 5 태그로 크기를 표시
class JdbcShipmentRepositoryTest { ... }
```

```xml
<!-- Maven Surefire: 태그로 걸러 실행 (Surefire 문서 "Filtering by Tags") -->
<configuration>
  <excludedGroups>medium, large</excludedGroups>  <!-- 빠른 단계: small만 -->
</configuration>
```

6. **측정한다.** 크기별 테스트 수와 총 실행 시간, 불안정 비율(같은 커밋 재실행 시 결과가 바뀐 비율)을 대시보드에 둔다.
   - 콘·모래시계 모양이 보이면 E2E 실패를 하나씩 "이걸 더 아래층에서 잡을 수 있었나"로 분류한다(Fowler의 "missing unit test" 신호).
7. **커버리지는 바닥 확인용.** SWE@G 11장: 커버리지는 줄이 실행됐는지만 재고 결과를 확인했는지는 모른다. 80% 같은 기준은 바닥이 아니라 천장처럼 쓰이기 쉽다([16](../16-coverage-and-its-limits/2-summary.md)).

## 장애 시나리오와 대처

### 1. 아이스크림 콘 CI — 느리고 불안정해서 무시된다 (⚠)

- **현상**: PR마다 CI가 40분(예시) 걸리고 가끔 이유 없이 실패한다. 개발자는 "재실행"을 누르고, 빨간 빌드를 병합한다.
- **보이는 형태**: 같은 커밋의 재실행 결과가 다르다. 실패 로그가 브라우저 타임아웃·요소를 못 찾음 같은 UI 계층 메시지다. 테스트 수 분포가 E2E 쪽에 몰려 있다.
- **원인**: 로직 검증을 E2E로 하고 있다. E2E는 여러 프로세스·네트워크를 거쳐 느리고 비결정적이다.
- **대처**
  - E2E 시나리오의 단언을 분해해, 로직 단언은 단위 테스트로 내린다. E2E는 핵심 여정만 남긴다.
  - 불안정 테스트는 격리(quarantine)하고 원인별로 고친다([09](../09-flaky-tests/2-summary.md)). 실패 시 자동 재실행은 SWE@G도 불안정 비율이 낮을 때는 "CPU 시간과 엔지니어 시간의 맞교환"으로 허용하지만, 근본 원인 수정을 미룰 뿐이라고 적는다. 재실행 통과 건수는 따로 세어 원인 조사 목록에 올린다.

### 2. 모래시계 — 통합 문제가 E2E에서야 터진다

- **현상**: 단위 테스트는 수천 개가 초록인데, E2E에서 "DB 컬럼이 없다", "JSON 필드 이름이 다르다"가 반복된다.
- **보이는 형태**: 실패 위치가 늘 어댑터 경계(리포지토리·HTTP 클라이언트)다.
- **원인**: 결합이 강해 의존 하나만 띄운 중간 테스트를 쓰기 어렵다(SWE@G가 꼽는 원인).
- **대처**: 의존 주입으로 어댑터를 떼어 낸다([software-design/25](../../software-design/25-dependency-injection-and-composition-root/2-summary.md)). 어댑터마다 실제 의존(컨테이너 DB 등)으로 중간 테스트를 둔다([08](../08-integration-tests-real-dependencies/2-summary.md)). 서비스 사이는 계약 테스트([13](../13-contract-testing/2-summary.md)).

### 3. Fake로만 검증한 SQL — 테스트는 초록, 운영은 잘못된 목록

- **현상**: "최근 출고" 화면 맨 위에 미출고 주문이 보인다.
- **보이는 형태**: 단위 테스트 전부 통과. 운영 DB에서 같은 쿼리를 돌리면 NULL 행이 먼저 나온다(위 실험).
- **원인**: Fake는 SQL을 실행하지 않는다. PostgreSQL은 `DESC` 정렬에서 NULL을 먼저 둔다.
- **대처**: 저장소 구현은 실제 DB로 중간 테스트를 둔다. Fake를 계속 쓰려면 Fake와 실제 구현에 **같은 테스트 묶음**을 돌려 둘이 같은 계약을 지키는지 확인한다(SWE@G 13장 "Fakes Should Be Tested").

### 4. "커버리지 90%인데 장애"

- **현상**: 커버리지 목표를 넘겼는데 운영 결함이 줄지 않는다.
- **원인**: 커버리지는 실행을 재지 검증을 재지 않는다. 큰 테스트가 많은 줄을 실행해 수치만 부풀리기도 한다. SWE@G는 커버리지를 small 테스트에서만 재라고 권한다.
- **대처**: "고객이 기대하는 동작이 다 테스트되었나"로 질문을 바꾼다. 변이 테스트로 단언의 판별력을 잰다([15](../15-mutation-testing/2-summary.md)).

## 핵심 문장

- 테스트의 목적은 변경을 안전하고 빠르게 만드는 것이다. 깨지면 안 되는 것은 테스트로 지킨다(비욘세 규칙).
- 크기(필요한 자원)와 범위(검증하는 코드 경로)는 다른 축이다. 가능하면 small로 쓴다.
- 피라미드는 "아래층을 두껍게"라는 경향이다. SWE@G의 80/15/5도 스스로 "아주 대략적인 지침"이라고 한다.
- 층마다 볼 수 있는 결함이 다르다. 로직은 단위 테스트가, 경계(SQL·프로토콜)는 그 경계를 실제로 실행하는 테스트만 잡는다.
- 아이스크림 콘은 느리고 불안정한 CI를 만들고, 불안정한 CI는 실패를 무시하게 만든다.

## 관련 주제·근거

- 선행
  - [software-design/01-complexity](../../software-design/01-complexity/2-summary.md) — 변경 증폭·unknown unknowns, 테스트가 줄이려는 비용
- 후속
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 좋은 단위 테스트의 기준
  - [03-test-doubles](../03-test-doubles/2-summary.md) — Fake·Stub·Mock, small 테스트를 가능하게 하는 대역
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) — 실제 DB로 중간 테스트
  - [09-flaky-tests](../09-flaky-tests/2-summary.md) — 불안정 테스트의 원인
  - [13-contract-testing](../13-contract-testing/2-summary.md) · [15-mutation-testing](../15-mutation-testing/2-summary.md) · [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md)
  - E2E·운영 검증 — [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md), [19-testing-in-production](../19-testing-in-production/2-summary.md)
  - [software-design/25](../../software-design/25-dependency-injection-and-composition-root/2-summary.md) · [software-design/26](../../software-design/26-functional-core-imperative-shell/2-summary.md) — 테스트하기 쉬운 구조
- 교재·문서
  - Winters·Manshreck·Wright, 『Software Engineering at Google』(O'Reilly 2020) 11장 "Testing Overview" — Why Do We Write Tests(GWS 이야기, 80%·절반 수치), Designing a Test Suite(Test Size·Test Scope·The Beyoncé Rule·A Note on Code Coverage), 80/15/5, 아이스크림 콘·모래시계(Figure 11-4), 불안정 0.15%·1%, The Limits of Automated Testing <https://abseil.io/resources/swe-book/html/ch11.html>
  - 같은 책 13장 "Test Doubles" — Fakes Should Be Tested <https://abseil.io/resources/swe-book/html/ch13.html>
  - Martin Fowler, "TestPyramid"(2012-05-01) — Cohn 『Succeeding with Agile』(2009) 기원, UI 테스트의 비용, 아이스크림 콘, "missing or incorrect unit test" <https://martinfowler.com/bliki/TestPyramid.html>
  - PostgreSQL 17 문서 7.5 Sorting Rows — `DESC`의 기본은 `NULLS FIRST` <https://www.postgresql.org/docs/17/queries-order.html>
  - Maven Surefire "Using JUnit 5 Platform — Filtering by Tags"(`groups`·`excludedGroups`) <https://maven.apache.org/surefire/maven-surefire-plugin/examples/junit-platform.html>
- 실험 목록
  - small 1,001개 vs medium 1개(PostgreSQL 17.11 컨테이너) 실행 시간 3회, DB 기동 시간 1회 — eclipse-temurin:21-jdk(21.0.12) 컨테이너, JUnit Console Launcher 1.13.4, `--cpus=2`
  - SQL 결함(`IS NOT NULL` 누락): Fake 기반 small 통과, 실제 DB medium 실패 → 고친 뒤 medium 통과
  - 배송비 경계 결함(`>=`→`>`): small 1,001개 중 입력 30,000 한 건만 실패, medium 통과
