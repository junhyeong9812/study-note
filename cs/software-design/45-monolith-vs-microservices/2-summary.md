# software-design/45-monolith-vs-microservices — 모놀리스·모듈러 모놀리스·마이크로서비스, 그리고 언제 쪼개나 — 정리 (힌트)

## 해결하는 문제

시스템이 커지면 "한 덩어리로 배포한다"는 사실이 발목을 잡기 시작한다.
그렇다고 쪼개면 그때부터 네트워크·부분 실패·데이터 정합성이라는 새 비용을 낸다.
이 주제는 **배포 단위를 몇 개로 둘지, 언제 나눌지**를 정하는 판단이다.

```text
 한 덩어리(모놀리스)가 아플 때                 쪼갰는데(분산) 아플 때
 ─────────────────────────────             ─────────────────────────────
 정산 팀 수정 하나가 주문 팀 배포를 기다린다      주소 컬럼 하나 바꾸는데 서비스 3개 동시 배포
 검색만 10배 필요한데 전체를 10대로 늘린다       결제 서비스 하나 죽으면 주문이 502
 경계가 없어 아무 클래스나 서로 부른다           메서드 호출이던 것이 HTTP 3홉, 지연이 수천 배
```

- *모놀리스(monolith)*: 하나의 배포 단위로 만들고 함께 배포하는 애플리케이션.
- *마이크로서비스(microservices)*: 작은 서비스 여럿이 각자 프로세스로 돌고, HTTP 같은 가벼운 수단으로 통신하며, 서비스마다 따로 배포하는 방식(Lewis·Fowler 2014의 정의).
- *모듈러 모놀리스(modular monolith)*: 배포 단위는 하나지만, 안쪽 모듈 경계를 **강제**하는 모놀리스.
- *분산 모놀리스(distributed monolith)*: 서비스로 나눴는데 여전히 같이 바꾸고 같이 배포해야 하는 상태. 분산의 비용과 모놀리스의 결합을 둘 다 가진다.

쉬운 예: 한 주방에서 요리사 다섯이 일하면 말 한마디로 협업한다. 대신 주방이 좁아 서로 부딪힌다. 가게를 다섯으로 나누면 각자 넓게 쓰지만, 재료를 주고받으려면 배달을 불러야 하고 배달이 늦거나 사고가 난다.\
똑같은 구조다.\
실무 예: 주문·결제·배송을 한 스프링 애플리케이션에 두면 메서드 호출과 DB 트랜잭션 하나로 끝난다. 서비스 셋으로 나누면 팀마다 따로 배포할 수 있지만, 호출은 네트워크를 타고 트랜잭션은 사가(saga)로 바뀐다.

## 동작·원리

### 1. 두 축 — 배포 단위 수 × 경계 강제

```text
                      경계를 강제하지 않음          경계를 강제함
                    ┌────────────────────────┬────────────────────────┐
  배포 단위 1개      │ 큰 진흙 공 모놀리스       │ 모듈러 모놀리스           │
                    │ 아무 클래스나 서로 부름    │ 모듈 API로만 부름          │
                    │                        │ 순환 없음, 내부 숨김        │
                    ├────────────────────────┼────────────────────────┤
  배포 단위 N개      │ 분산 모놀리스  ⚠         │ 마이크로서비스             │
                    │ 공유 DB·동시 배포         │ 데이터 소유·독립 배포        │
                    │ 분산 비용 + 결합          │ 분산 비용은 그대로 낸다      │
                    └────────────────────────┴────────────────────────┘
```

- 배포 단위를 나누는 것과 경계를 지키는 것은 **다른 축**이다.
- 서비스로 나눈다고 경계가 생기지 않는다. 경계 없이 나누면 오른쪽 위가 아니라 왼쪽 아래(분산 모놀리스)로 간다.
- Shopify는 2019년 글에서 마이크로서비스 대신 모듈러 모놀리스를 택했다고 적는다. 정의: "모든 코드가 한 애플리케이션을 이루고, 도메인 사이 경계가 엄격히 강제되는 시스템"(Shopify Engineering, 2019-02-21).

### 2. 마이크로서비스의 정의 — 무엇을 사고 무엇을 내나

Lewis·Fowler(2014-03-25)는 정의에 이 요소들을 넣는다: 서비스마다 자기 프로세스, 가벼운 통신(흔히 HTTP 리소스 API), 비즈니스 능력 단위, **완전 자동화된 배포 장치로 독립 배포**, 중앙 관리 최소화, 서비스마다 다른 언어·저장소 가능.

```text
 사는 것                               내는 것 (Fowler "MicroservicePremium", 2015)
 ───────────────────────               ─────────────────────────────────────
 팀별 독립 배포                          자동 배포·모니터링 구축 비용
 서비스별 독립 확장                       부분 실패 처리 (타임아웃·재시도·브레이커)
 서비스별 기술 선택                       최종적 일관성, 분산 트랜잭션 없음
 경계가 프로세스로 강제됨                  경계 이동(서비스 간 리팩터링)이 비싸다 (MonolithFirst)
```

- Fowler는 "모놀리스로 관리하기에 너무 복잡한 시스템이 아니면 마이크로서비스를 고려하지도 말라"고 적는다. 이것은 저자의 주장이다(측정이 아니다).
- 선행 조건(Fowler "MicroservicePrerequisites", 2014): **빠른 프로비저닝**(몇 시간 안에 서버), **기본 모니터링**(기술 지표 + 주문 감소 같은 비즈니스 지표), **빠른 배포**(몇 시간 안에 끝나는 배포 파이프라인). 이 셋이 없으면 이 방식을 고려하지 말라고 쓴다.

### 실험 A: 같은 3단계를 메서드 호출 vs localhost HTTP 3홉

주문 → 재고 → 결제를 (1) 한 프로세스 안 인터페이스 호출, (2) JDK 내장 `HttpServer` 셋과 `HttpClient`(HTTP/1.1)로 3홉 호출해 비교했다.

```java
// 모듈러 모놀리스: 모듈 = 인터페이스, 호출 = 메서드
interface Payment { String pay(int amount); }
interface Stock   { String reserve(int qty); }
static Payment payment = amount -> "paid:" + amount;
static Stock stock = qty -> "reserved:" + qty + "|" + payment.pay(qty * 100);
static String orderInProcess(int qty) { return "order|" + stock.reserve(qty); }

// 서비스 분리: order(18081) → stock(18082) → payment(18083), 응답이 200이 아니면 예외
HttpServer stk = serve(18082, ex -> { try { reply(ex, "reserved:1|" + get(payUrl)); }
                                      catch (Exception e) { ex.sendResponseHeaders(502, -1); ex.close(); } });
```

(실험, JDK 21.0.12 temurin, `--cpus=2`, 호스트 24코어, `scratchpad/sd/45/e45/Hops.java`, 2026-10-02 — 실행마다 다르다. 워밍업 2000회 뒤 3000회, 3회 실행)

```text
== nodelay run 1
인프로세스 메서드 3단계  평균      2.0us  p50      1.3us  p99      8.7us
localhost HTTP 3홉       평균   3705.6us  p50   3167.0us  p99  19694.9us
결제 서비스 중지 후 HTTP 주문 응답 코드: 502
== nodelay run 2
인프로세스 메서드 3단계  평균      1.7us  p50      0.9us  p99     10.3us
localhost HTTP 3홉       평균   3606.7us  p50   3074.1us  p99  19697.0us
결제 서비스 중지 후 HTTP 주문 응답 코드: 502
== nodelay run 3
인프로세스 메서드 3단계  평균      1.6us  p50      1.1us  p99      6.7us
localhost HTTP 3홉       평균   3499.6us  p50   2978.2us  p99  19436.1us
결제 서비스 중지 후 HTTP 주문 응답 코드: 502
```

- 관찰 1 — 같은 일인데 p50이 약 1μs에서 약 3ms로 늘었다(이 환경에서 수천 배). 진짜 네트워크가 아닌 localhost인데도 그렇다. 직렬화·소켓·스레드 전환 비용이다.
- 관찰 2 — 결제 서비스를 내리자(재고가 아무도 듣지 않는 포트로 연결) 주문까지 502가 됐다. 메서드 호출에는 없던 실패 모드다.
- 관찰 3 — 위 수치는 JDK 서버 속성 `-Dsun.net.httpserver.nodelay=true`를 켠 것이다. 이 속성의 기본값은 false다(OpenJDK 21u `sun/net/httpserver/ServerConfig.java`). 기본값 그대로 두면 아래처럼 3홉이 약 50ms가 됐다.

(실험, 같은 환경, 기본 설정, 워밍업 50회 뒤 200회, 2회 실행)

```text
== default run 1
localhost HTTP 3홉       평균  49584.3us  p50  49146.6us  p99  62044.7us
== default run 2
localhost HTTP 3홉       평균  49879.8us  p50  49759.8us  p99  63953.7us
```

- 해석: `TCP_NODELAY`를 켜자 사라졌으므로 Nagle 알고리즘과 지연 ACK의 상호작용으로 본다. 핵심은 원인보다 **"메서드 호출에는 없던 설정 하나가 지연을 50ms로 만든다"**는 점이다. 분산은 이런 층을 하나씩 떠안는다.

### 3. 분산 모놀리스 — 공유 DB가 결합을 그대로 남긴다

```text
 공유 DB                                     데이터 소유 + 공개 계약
 order ──┐                                  order ── orders 테이블 (order만 안다)
 shipping├──> orders 테이블 (셋 다 컬럼을 안다)    │
 billing ┘                                    └──> OrderView(id, shippingAddress)  ← 공개 계약
                                                    ^            ^
 컬럼 하나 변경 → 세 서비스 동시 수정·배포           shipping      billing  (계약만 안다)
```

- *데이터 소유(Database per Service)*: 서비스의 영속 데이터는 그 서비스만 접근하고, 다른 서비스는 API로만 접근한다(microservices.io). 그 패턴의 "Forces"에 "서비스는 독립적으로 개발·배포·확장되도록 느슨히 결합되어야 한다"가 있다.

### 실험 B: 같은 스키마 변경을 두 설계에 적용

변경: `orders.addr`를 `address_line`과 `zip`으로 나눈다. 두 설계를 각각 git 저장소로 만들고 `sed`로 같은 변경을 적용한 뒤 `git diff --stat`을 쟀다.

(실험, git 2.43.0, `scratchpad/sd/45/e45/shared_vs_owned.sh`, 2026-10-02 — 결정적)

```text
### 설계 1: 공유 DB — git diff --stat
 billing/src/InvoiceQuery.java  | 2 +-
 order/src/OrderRepository.java | 4 ++--
 shipping/src/ShippingJob.java  | 4 ++--
 3 files changed, 5 insertions(+), 5 deletions(-)
### 함께 배포해야 하는 서비스:
billing order shipping 
### 설계 2: 데이터 소유 + 계약 — git diff --stat
 order/src/OrderApi.java        | 2 +-
 order/src/OrderRepository.java | 4 ++--
 2 files changed, 3 insertions(+), 3 deletions(-)
### 함께 배포해야 하는 서비스:
order 
```

- 공유 DB에서는 내부 표현(컬럼) 변경이 서비스 세 개로 번졌다. 데이터 소유 설계에서는 `OrderApi`의 번역 한 곳이 흡수해 order 하나만 바뀌었다.
- **반대 상황**도 쟀다. 배송이 우편번호를 따로 받고 싶어 하면, 이번에는 계약 자체가 바뀐다.

```text
### 설계 2, 계약 변경 — git diff --stat
 contracts/OrderView.java      | 2 +-
 order/src/OrderApi.java       | 2 +-
 shipping/src/ShippingJob.java | 2 +-
 3 files changed, 3 insertions(+), 3 deletions(-)
### 바뀐 배포 단위:
contracts order shipping 
### 커밋별로 함께 바뀐 최상위 폴더 (git log --name-only)
[shared-db]
init shared-db: billing order shipping 
split addr: billing order shipping 
[owned]
init owned: billing contracts order shipping 
split addr (owned): order 
add zip to OrderView: contracts order shipping
```

- 계약은 결합을 없애지 않는다. **내부 변경은 흡수하고, 계약 변경은 여전히 퍼진다.** 그래서 계약은 필드 추가(expand) → 소비자 이행 → 옛 필드 제거(contract) 순으로 바꾼다. 필드 추가만이라면 생산자가 먼저 배포하고 소비자는 나중에 따라와도 된다.
- `git log --name-only`로 커밋마다 함께 바뀐 서비스를 세면, "자주 같이 바뀌는 서비스 묶음"이 드러난다. 그 묶음이 사실상 하나의 배포 단위다.

### 4. 동기 호출 체인 — 가용성은 곱으로 떨어진다

```text
 사용자 → A → B → C → D → E      각 99.9%
 전체 가용성 = 0.999^5 ≈ 99.5%   (직렬 합성, reliability/01에서 공식·시뮬레이션으로 확인)
 지연도 더해진다: 각 홉의 p99가 겹칠 확률이 커진다
```

- 실험 A의 관찰 2가 그 실패의 한 칸이다. 결제 하나가 내려가자 주문이 실패했다.
- 비동기 메시지(주문을 받아 두고 결제는 나중에)로 바꾸면 의존이 시간 축으로 풀린다. 대신 "주문했는데 결제 대기"라는 중간 상태가 생긴다([distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md), [distributed/15-saga](../../distributed/15-saga/2-summary.md)).

### 5. 언제 쪼개나 — 신호와 반대 신호

```text
 쪼갤 신호 (측정할 수 있는 것)                        쪼개지 말 신호
 ───────────────────────────                     ───────────────────────────
 배포 대기열: 다른 팀 변경 때문에 릴리스가 밀린다         경계가 아직 자주 움직인다 (요구가 탐색 중)
 변경 빈도가 크게 다른 모듈 (git log로 측정)            자동 배포·모니터링이 없다 (선행 조건 미달)
 자원 요구가 크게 다른 부분 (검색만 CPU 10배)           팀이 하나다
 장애 격리 필요 (이 기능이 죽어도 결제는 돼야)          모듈 사이 호출이 잦고 데이터를 공유한다
```

- Fowler "MonolithFirst"(2015-06-03): 들어 본 성공 사례 대부분이 커진 모놀리스를 나눈 것이고, 처음부터 마이크로서비스로 시작한 경우 대부분이 심각한 문제를 겪었다고 적는다. 첫 이유로 YAGNI를, 둘째로 경계를 처음에 맞히기 어렵고 서비스 사이 리팩터링이 모놀리스 안보다 훨씬 어렵다는 점을 든다. 같은 글에 반론(처음부터 서비스로 시작하자는 쪽)도 소개하고, 자신의 조언은 잠정적이라고 밝힌다.
- 되돌아가는 사례도 있다. Amazon Prime Video 팀(2023-03-22)은 오디오·비디오 모니터링 서비스를 Step Functions·Lambda 기반 분산 구성에서 한 프로세스로 합쳤다. 상태 전이마다 과금되는 오케스트레이션과 S3를 거치는 프레임 전달이 비용 원인이었고, 예상 부하의 약 5%에서 확장 한계에 걸렸다고 적는다. 합친 뒤 인프라 비용이 90% 넘게 줄었다고 보고한다. 해석: 단계 사이에 큰 데이터를 매우 자주 넘기는 구조에서는 프로세스 경계가 비용 그 자체였다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프와 순환 탐지** — 모듈·서비스를 노드, 호출·import를 간선으로 둔다. 모듈러 모놀리스의 첫 규칙은 "모듈 그래프가 DAG"다(Spring Modulith `verify()` 규칙). 순환은 SCC(강한 연결 요소)로 찾는다.
- **변경 결합 행렬(co-change matrix)** — 커밋마다 함께 바뀐 모듈 쌍을 센다. 실험 B의 `git log --name-only` 집계가 그 최소판이다. 깊은 내용은 [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md).
- **직렬·병렬 신뢰도 합성** — 동기 체인은 곱, 이중화는 1 − 실패 확률의 곱. [reliability/01-fault-error-failure-availability](../../reliability/01-fault-error-failure-availability/2-summary.md).
- **번역 계층(매퍼)** — 내부 행 → 공개 계약. 실험 B의 `OrderApi.toView`가 내부 변경을 흡수한 곳이다.
- **사가·아웃박스** — 서비스를 나누면 DB 트랜잭션 하나가 로컬 트랜잭션 여럿 + 보상으로 바뀐다. [distributed/15-saga](../../distributed/15-saga/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **모듈러 모놀리스로 시작한다.** 모듈마다 공개 API 패키지와 내부 패키지를 나누고, 모듈 사이는 API로만 부른다.
2. **경계를 테스트로 강제한다.** 경계가 사람의 주의에만 기대면 무너진다.
3. **데이터 소유부터 나눈다.** 같은 DB 안이라도 모듈마다 자기 테이블만 쓰게 한다. 남의 테이블 조인이 없어야 나중에 떼어낼 수 있다.
4. **쪼갤 신호를 측정한다.** 배포 대기 시간, 모듈별 변경 빈도, 함께 바뀌는 모듈 묶음(아래 진단).
5. **하나씩 떼어낸다.** 변경이 잦고 데이터가 독립된 모듈부터, 라우팅을 조금씩 옮긴다([50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md)).
6. **떼어낸 뒤에는 분산 비용을 낸다.** 타임아웃·재시도·브레이커, 상관 ID 추적, 계약 버전 관리.

### 2. 코드 — 모듈 경계 강제 (Java)

```java
// com.shop.order            ← 공개 API 패키지 (다른 모듈은 여기만)
public interface OrderQueries { OrderView find(String orderId); }
public record OrderView(String id, String shippingAddress) {}

// com.shop.order.internal   ← 내부 (package-private 우선)
class JdbcOrderRepository { /* orders 테이블은 이 모듈만 안다 */ }
```

```java
// ArchUnit 규칙 예 — shipping은 order의 internal을 직접 쓰지 않는다
@ArchTest
static final ArchRule shipping_uses_order_api_only =
    noClasses().that().resideInAPackage("..shipping..")
        .should().dependOnClassesThat().resideInAPackage("..order.internal..");

// Spring Modulith 쓰는 경우: 모듈 순환 금지 + internal 접근 금지를 한 번에 검사
ApplicationModules.of(ShopApplication.class).verify();
```

- Spring Modulith 문서(2.1.1)의 `verify()` 규칙: 모듈 수준 순환 금지, 다른 모듈의 internal 패키지 참조 금지(Open 모듈 예외), 선택적으로 허용 의존 목록. ArchUnit 규칙 작성은 [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md)에서 다룬다.

### 3. 진단 — 사실상 함께 배포되는 묶음 찾기

```bash
# 최근 커밋마다 바뀐 최상위 폴더(=서비스) 목록 — 늘 같이 나오는 묶음이 숨은 배포 단위다
git log --since=90.days --format='@%h' --name-only \
 | awk '/^@/{if(s!="")print s; s=""; delete seen; next}
        NF{split($0,p,"/"); if(!(p[1] in seen)){seen[p[1]]=1; s=s p[1]" "}}
        END{print s}' \
 | sort | uniq -c | sort -rn | head
```

- 서비스 저장소가 여럿이면 저장소별 커밋을 같은 티켓 번호로 묶어 센다.
- 배포 기록에서 "같은 시각에 함께 배포된 서비스 수"도 같은 신호다.

## 장애 시나리오와 대처

### 1. 분산 모놀리스 — 서비스는 나눴는데 동시 배포가 필요하다 (⚠ 커리큘럼)

- 현상: 기능 하나를 내보내려면 서비스 서너 개를 정해진 순서로 같이 배포해야 한다. 하나만 먼저 나가면 장애.
- 보이는 형태: 릴리스 노트에 "A·B·C 동시 배포 필요". 배포 직후 `NoSuchFieldError`·역직렬화 실패·HTTP 400(모르는 필드·누락 필드). `git log`로 보면 같은 서비스 묶음이 커밋마다 함께 바뀐다(실험 B).
- 원인: 서비스 경계가 함께 바뀌는 결정을 가르지 못했다. 공유 라이브러리의 도메인 모델, 공유 DB, 버전 없는 계약.
- 대처: 함께 바뀌는 서비스는 다시 합치는 것도 선택지다. 계약은 expand → migrate → contract로 바꾸고, 공유 도메인 모델 라이브러리를 계약(DTO)으로 바꾼다.

### 2. 공유 DB — 한 팀의 스키마 변경이 다른 서비스를 깨뜨린다 (⚠ 커리큘럼)

- 현상: 주문 팀이 컬럼 이름을 바꿨더니 배송 배치와 청구 리포트가 실패한다.
- 보이는 형태: 다른 서비스 로그에 `column "addr" does not exist`(PostgreSQL) 같은 SQL 오류. 그 서비스는 배포한 적이 없다.
- 원인: 테이블이 사실상 공개 API였다. 실험 B 설계 1에서 컬럼 하나가 서비스 3개로 번졌다.
- 대처: 테이블 소유자를 하나로 정하고, 다른 서비스는 API·이벤트·읽기 전용 뷰로 읽는다. 옮기는 동안은 expand/contract로 옛 컬럼을 남긴다([database/26-schema-migration](../../database/26-schema-migration/2-summary.md), [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md)).

### 3. 동기 호출 체인 — 가용성이 곱셈으로 떨어진다 (⚠ 커리큘럼)

- 현상: 서비스마다 99.9%를 지키는데 사용자 체감 성공률은 그보다 낮다. 꼬리 지연도 길다.
- 보이는 형태: 앞단 서비스의 5xx가 뒷단 하나의 장애와 동시에 오른다(실험 A의 502). 트레이스에서 요청 하나가 홉 여러 개를 지난다.
- 원인: 직렬 의존은 가용성을 곱하고 지연을 더한다.
- 대처: 체인을 짧게(데이터를 미리 복제해 두기), 비동기 이벤트로 바꾸기, 타임아웃·브레이커·폴백([reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)).

### 4. 조기 분해 — 틀린 경계가 굳는다

- 현상: 새 기능마다 서비스 사이로 책임을 옮겨야 한다. 서비스 간 API가 계속 바뀐다.
- 보이는 형태: 서비스 사이 호출 수가 기능 추가마다 는다. 한 서비스의 대부분 코드가 다른 서비스 데이터를 가공한다(Feature Envy의 분산판).
- 원인: 도메인을 탐색하는 중에 쪼갰다. 서비스 사이 리팩터링은 모놀리스 안보다 훨씬 비싸다(Fowler MonolithFirst).
- 대처: 잘못 나눈 서비스를 다시 합치고, 모놀리스 안 모듈로 경계를 다듬은 뒤 다시 판단한다.

### 5. 서비스를 나눴는데 트랜잭션이 사라진 줄 모른다

- 현상: 주문은 생성됐는데 재고는 차감 안 됨. 가끔만 일어난다.
- 보이는 형태: 서비스별 DB 사이 불일치, 대사(reconciliation) 배치에서 어긋난 건수.
- 원인: 모놀리스의 `@Transactional` 하나가 서비스 둘로 나뉘며 원자성이 사라졌다.
- 대처: 사가와 보상, 아웃박스로 이벤트 발행을 로컬 트랜잭션에 묶기([distributed/15-saga](../../distributed/15-saga/2-summary.md), [distributed/16-outbox-and-dual-write](../../distributed/16-outbox-and-dual-write/2-summary.md)).

## 핵심 문장

- 배포 단위를 나누는 것과 경계를 지키는 것은 다른 축이다. 경계 없이 나누면 분산 모놀리스가 된다.
- 마이크로서비스는 독립 배포·독립 확장을 사는 대신 네트워크·부분 실패·최종적 일관성을 낸다. 실험에서 같은 3단계가 메서드 호출 약 1μs에서 localhost HTTP 3홉 약 3ms가 됐고, 하류 하나가 내려가자 502가 났다.
- 공유 DB는 테이블을 공개 API로 만든다. 실험에서 컬럼 하나 변경이 공유 DB에서는 서비스 3개, 데이터 소유 설계에서는 1개를 바꿨다.
- 계약은 내부 변경을 흡수하지만 계약 자체의 변경은 여전히 퍼진다. 그래서 계약은 expand → migrate → contract로 바꾼다.
- 시작은 모듈러 모놀리스로 하고, 배포 대기·변경 빈도·자원 요구 차이를 측정해서 쪼갤 곳을 고른다.

## 관련 주제·근거

- 선행
  - [39-component-principles](../39-component-principles/2-summary.md) — 컴포넌트 묶기·의존 원칙
  - [distributed/01-why-distributed-and-fallacies](../../distributed/01-why-distributed-and-fallacies/2-summary.md) — 네트워크에 대한 8가지 착각
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 아키텍처 스타일 원본(37)
- 후속·연결
  - [46-quality-attributes-and-tradeoffs](../46-quality-attributes-and-tradeoffs/2-summary.md) — 독립 배포 vs 성능·일관성의 맞교환
  - [49-multi-tenancy](../49-multi-tenancy/2-summary.md) — 테넌트 격리 모델은 이 판단 위에 놓인다
  - [50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md) — 모놀리스에서 하나씩 떼어내기
  - [distributed/20-data-ownership-and-cross-service-queries](../../distributed/20-data-ownership-and-cross-service-queries/2-summary.md) — 나눈 뒤의 조회
  - [reliability/47-server-design-antipatterns](../../reliability/47-server-design-antipatterns/2-summary.md) — 공유 데이터베이스 안티패턴
  - [engineering/engineering-axes/system-design.md](../../engineering/engineering-axes/system-design.md) — "모놀리스가 기본값이다", 분산 모놀리스 판별법
- 글·문서
  - James Lewis·Martin Fowler, "Microservices", 2014-03-25 — 정의와 특성 9가지 <https://martinfowler.com/articles/microservices.html>
  - Martin Fowler, "MicroservicePrerequisites", 2014-08-28 <https://martinfowler.com/bliki/MicroservicePrerequisites.html> · "MicroservicePremium", 2015-05-13 <https://martinfowler.com/bliki/MicroservicePremium.html> · "MonolithFirst", 2015-06-03 <https://martinfowler.com/bliki/MonolithFirst.html>
  - Sam Newman, 『Building Microservices』 2판(O'Reilly) — 저자 사이트 목차로 장 구성 확인(2장 How to Model Microservices: 정보 은닉·결합·응집·DDD, 3장 Splitting the Monolith). "분산 모놀리스" 정의의 쪽·절은 본문을 열지 못해 확인하지 못했다 [?] <https://samnewman.io/books/building_microservices_2nd_edition/>
  - Sam Newman, 『Monolith to Microservices』(O'Reilly, 2019) — 목차: 4장 Decomposing the Database의 "Pattern: The Shared Database" 등 <https://samnewman.io/books/monolith-to-microservices/>
  - Chris Richardson, microservices.io "Database per service" <https://microservices.io/patterns/data/database-per-service.html>
  - Shopify Engineering, "Deconstructing the Monolith", 2019-02-21 <https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity>
  - Marcin Kolny, "Scaling up the Prime Video audio/video monitoring service and reducing costs by 90%", 2023-03-22 (원 URL이 리디렉트되어 web.archive.org 2023-12-30 사본으로 열람) <https://web.archive.org/web/20231230202019/https://www.primevideotech.com/video-streaming/scaling-up-the-prime-video-audio-video-monitoring-service-and-reducing-costs-by-90>
  - Spring Modulith 레퍼런스 "Verifying Application Module Structure"(2.1.1) <https://docs.spring.io/spring-modulith/reference/verification.html>
  - OpenJDK 21u `src/jdk.httpserver/share/classes/sun/net/httpserver/ServerConfig.java` — `sun.net.httpserver.nodelay`
- 실험 목록
  - A 인프로세스 3단계 vs localhost HTTP 3홉 지연, 하류 중지 시 502 — `scratchpad/sd/45/e45/Hops.java`, JDK 21.0.12 temurin `--cpus=2`, nodelay 켬 3회·기본 2회
  - B 공유 DB vs 데이터 소유: 같은 컬럼 분리 변경의 `git diff --stat`, 계약 변경(반대 상황), 커밋별 함께 바뀐 서비스 — `scratchpad/sd/45/e45/shared_vs_owned.sh`, git 2.43.0
