# software-design/44-architecture-in-code — 같은 유스케이스를 계층형·헥사고날·클린으로 — 정리 (힌트)

## 해결하는 문제

계층형·헥사고날·클린 아키텍처의 그림은 많이 봤지만, 코드로 옮기면 질문이 남는다.

```text
 ? 포트 인터페이스는 어느 패키지에 두나
 ? 어댑터는 무엇을 import하나 (화살표 방향)
 ? 매핑은 몇 번 하나, 누가 하나
 ? 트랜잭션은 어디서 열고 닫나
 ? 도메인 예외는 어디서 HTTP 409로 바뀌나
```

이것을 정하지 않으면 두 가지 실패가 나온다.

- **이름만 헥사고날**: `adapter/`·`domain/` 폴더는 있는데 도메인 클래스가 JPA 엔티티다. 의존 방향이 그림과 반대다.
- **의례적 구조**: 계층마다 같은 필드를 1:1로 옮기는 매핑만 반복된다. 바꿀 때 파일만 늘어난다.

이 노트는 유스케이스 하나("포인트 사용")를 세 방식으로 직접 구현하고, 같은 변경 세 개를 적용해 `git diff --stat`으로 비교한다. 예제의 도메인은 [domain-modeling/basic/14-points](../../domain-modeling/basic/14-points/2-summary.md)의 포인트를 잔액 하나로 줄인 것이다(덩어리·만료는 뺐다).

쉬운 예: 같은 집을 세 가지 설계도로 지어 보고, "콘센트 하나 추가", "창문 크기 변경", "배관 교체"를 해 보는 것이다. 어느 설계도가 어떤 공사에 싸고 어떤 공사에 비싼지가 보인다.\
똑같은 구조다: 같은 요구, 같은 변경, 다른 구조.\
실무 예: 팀이 "이번 서비스는 헥사고날로"를 정할 때, 무엇이 싸지고 무엇이 비싸지는지를 근거로 고른다.

## 동작·원리

### 1. 세 구조의 의존 방향

```text
 계층형(layered)                헥사고날(ports & adapters)                 클린(clean)
 web                            adapter.in.web ──> application.port.in     adapters.controllers ──> usecases.InputBoundary
  │                                                     ^ implements              adapters.presenters ──> usecases.OutputBoundary(구현)
  v                                               application.Service              adapters.gateways   ──> usecases.AccountGateway(구현)
 service                                                │ uses                                              │
  │                                                     v                          usecases.Interactor ─────┘
  v                             adapter.out.persistence ──> application.port.out         │
 repository                                             │                                v
  │                                                     v                          entities
  v                                                   domain
 domain (= @Entity) ──> jakarta.persistence      domain: 아무것도 import 안 함        entities: 아무것도 import 안 함
```

- *포트(port)*: 애플리케이션이 바깥과 대화하는 인터페이스. Cockburn(2005)의 의도문: "애플리케이션이 사용자·프로그램·자동 테스트·배치 스크립트에 의해 똑같이 구동되고, 실행 장치·DB와 격리되어 개발·테스트될 수 있게 한다."
- *주도하는(driving, primary) 어댑터*: 애플리케이션을 움직이는 쪽(HTTP 컨트롤러, 테스트). *주도되는(driven, secondary) 어댑터*: 애플리케이션이 부르는 쪽(DB, 외부 API). Cockburn이 primary/secondary 또는 driving/driven이라고 부른다.
- *의존성 규칙(Dependency Rule)*: Martin(2012 블로그): 소스 코드 의존은 안쪽으로만 향한다. 안쪽 원은 바깥 원의 이름을 언급하지 않는다.
- *인터랙터(interactor)·입력/출력 경계(boundary)·프레젠터*: 클린 아키텍처에서 유스케이스 객체, 그것을 부르는 인터페이스, 결과를 받는 인터페이스. 유스케이스가 프레젠터를 직접 부르면 규칙 위반이라 출력 포트 인터페이스를 안쪽에 두고 프레젠터가 구현한다(Martin 2012, "Crossing boundaries").

### 2. 다섯 가지 결정이 놓이는 자리

| 결정 | 계층형 | 헥사고날 | 클린 |
|---|---|---|---|
| 포트 인터페이스 위치 | 없음(서비스가 리포지토리 클래스를 직접 씀) | `application.port.in`·`port.out` — 안쪽 | `usecases`의 Input/OutputBoundary·Gateway — 안쪽 |
| 어댑터 방향 | 위→아래, 도메인이 JPA에 의존 | 어댑터 → 포트(안쪽) | 어댑터 → 유스케이스(안쪽) |
| 매핑 | 없음(엔티티가 곧 도메인) | 영속 엔티티 ↔ 도메인(어댑터 안) | 요청 모델·응답 모델·뷰모델·레코드 ↔ 엔티티 |
| 트랜잭션 경계 | 서비스 메서드 | 애플리케이션 서비스(유스케이스) | 인터랙터, 또는 인터랙터를 감싼 바깥 데코레이터 |
| 도메인 예외 → HTTP | 컨트롤러가 `IllegalStateException`을 409로 | 주도 어댑터가 `InsufficientPointsException`을 409로 | 인터랙터가 실패를 응답 모델로, 프레젠터가 409로 |

- 트랜잭션 경계 칸은 예제 코드에 주석으로만 표시했다(실제 트랜잭션 매니저는 띄우지 않았다).
- 클린에서 "실패를 예외 대신 응답 모델로"는 이 예제의 선택이다. Martin의 글이 이를 요구하지는 않는다.

### 3. 코드 핵심

```java
// 계층형 — 도메인 = JPA 엔티티
@Entity @Table(name = "point_account")
public class PointAccount { @Id private Long id; @Column(name = "balance") private long balance; ... public void spend(long amount) {...} }

// 헥사고날 — 포트는 안쪽, 도메인 언어로 이름(AccountStore), 영속 모델은 어댑터 안 package-private
public interface SpendPointsUseCase { SpendResult spend(long accountId, long amount); record SpendResult(long balance) {} }
public interface AccountStore { Optional<PointAccount> load(long id); void save(PointAccount account); }
class PointAccountJpaEntity { @Id Long id; @Column(name = "balance") long balance; }        // adapter.out.persistence
public class AccountPersistenceAdapter implements AccountStore {
    public Optional<PointAccount> load(long id) { return Optional.ofNullable(rows.get(id)).map(e -> new PointAccount(e.id, e.balance)); }
    public void save(PointAccount a) { rows.put(a.id(), new PointAccountJpaEntity(a.id(), a.balance())); }
}

// 클린 — 요청 모델 → 인터랙터 → 응답 모델 → 프레젠터 → 뷰모델
public void spend(SpendPointsRequest req) {
    PointAccount a = gateway.load(req.accountId()).orElseThrow(...);
    if (!a.canSpend(req.amount())) { presenter.present(new SpendPointsResponse(false, a.balance(), "잔액 부족")); return; }
    a.spend(req.amount()); gateway.save(a);
    presenter.present(new SpendPointsResponse(true, a.balance(), null));
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/40/e44/run.sh`, 2026-10-02 — 세 구현 모두 같은 시나리오: 잔액 10,000에서 3,000 사용 후 9,000 사용. 아래는 실험 B의 변경 C1~C3을 모두 적용한 뒤의 출력. C3은 이 시나리오의 결과를 바꾸지 않는다)

```text
layered: 200 {"balance":7000,"grade":"BASIC"} / 409 {"error":"잔액 부족"}
hexagonal: 200 {"balance":7000,"grade":"BASIC"} / 409 {"error":"잔액 부족: 7000 < 9000"}
clean: SpendPointsViewModel[status=200, body={"balance":7000,"grade":"BASIC"}] / SpendPointsViewModel[status=409, body={"error":"잔액 부족"}]
```

### 실험 A: 크기와 의존 방향

(실험, 같은 환경, 변경 전 base 스냅샷 `scratchpad/sd/40/e44-base`에서 셈 — 조립용 `Main.java` 제외)

```text
layered(base): 파일 4개, 48줄 (Main 제외)
hexagonal(base): 파일 8개, 75줄 (Main 제외)
clean(base): 파일 12개, 78줄 (Main 제외)
```

(실험, 같은 환경, `size.sh`의 jdeps 부분과 `e44-arch/run.sh`의 ArchUnit 1.5.1 규칙 "도메인(`points.domain`·`points.entities`)은 `jakarta.persistence`·어댑터·웹·리포지토리에 의존하지 않는다", 2026-10-02)

```text
== jdeps layered: 도메인 패키지가 무엇에 의존하나
   points.domain -> jakarta.persistence
   (java.base 외 의존 끝)
== jdeps hexagonal: 도메인 패키지가 무엇에 의존하나
   points.domain -> points.domain
   (java.base 외 의존 끝)
== jdeps clean: 도메인 패키지가 무엇에 의존하나
   (java.base 외 의존 끝)
[FAIL] /w/e44/out/layered — was violated (5 times):
   Class <points.domain.PointAccount> is annotated with <jakarta.persistence.Entity> in (PointAccount.java:0)
   Class <points.domain.PointAccount> is annotated with <jakarta.persistence.Table> in (PointAccount.java:0)
   Field <points.domain.PointAccount.balance> is annotated with <jakarta.persistence.Column> in (PointAccount.java:0)
[PASS] /w/e44/out/hexagonal
[PASS] /w/e44/out/clean
```

- 같은 기능에 파일 수가 4 → 8 → 12로 늘었다. 줄 수는 48 → 75 → 78. 늘어난 것은 대부분 인터페이스·요청/응답 모델·매핑이다.
- 계층형 도메인만 `jakarta.persistence`를 안다. 헥사고날의 `points.domain -> points.domain`은 같은 패키지 안의 참조(예외 클래스)다.

### 실험 B: 같은 변경 세 개

C1 영속 변경(낙관적 락 `@Version` 컬럼 추가), C2 응답에 도메인 계산값 추가(잔액 5만 이상이면 등급 GOLD), C3 도메인 규칙 추가(1회 사용 한도 5만). 셋을 차례로 커밋하며 쟀다.

(실험, 같은 환경, `bash e44-base/replay.sh <디렉터리>` — base를 새 git 저장소로 만들고 `changes.py c1·c2·c3`을 적용, 2026-10-02)

```text
#### C1 영속 변경: @Version 컬럼
-- layered
 domain/PointAccount.java | 1 +
 1 file changed, 1 insertion(+)
-- hexagonal
 .../points/adapter/out/persistence/AccountPersistenceAdapter.java   | 6 +++++-
 .../src/points/adapter/out/persistence/PointAccountJpaEntity.java   | 1 +
 2 files changed, 6 insertions(+), 1 deletion(-)
-- clean
 adapters/gateways/AccountRecord.java     | 1 +
 adapters/gateways/JpaAccountGateway.java | 6 +++++-
 2 files changed, 6 insertions(+), 1 deletion(-)
#### C2 응답에 도메인 계산값(등급) 추가
-- layered
 domain/PointAccount.java | 1 +
 web/PointController.java | 2 +-
 2 files changed, 2 insertions(+), 1 deletion(-)
-- hexagonal
 adapter/in/web/PointController.java         | 2 +-
 application/SpendPointsService.java         | 2 +-
 application/port/in/SpendPointsUseCase.java | 2 +-
 domain/PointAccount.java                    | 1 +
 4 files changed, 4 insertions(+), 3 deletions(-)
-- clean
 adapters/presenters/SpendPointsPresenter.java | 2 +-
 entities/PointAccount.java                    | 1 +
 usecases/SpendPointsInteractor.java           | 4 ++--
 usecases/SpendPointsResponse.java             | 2 +-
 4 files changed, 5 insertions(+), 4 deletions(-)
#### C3 도메인 규칙: 1회 한도 5만
-- layered
 domain/PointAccount.java | 1 +
 1 file changed, 1 insertion(+)
-- hexagonal
 domain/PointAccount.java | 1 +
 1 file changed, 1 insertion(+)
-- clean
 entities/PointAccount.java | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)
```

```text
 정리 (위 출력에서)          계층형           헥사고날              클린
 C1 영속 변경               1파일 +1 ★도메인   2파일 +6 −1(어댑터만)  2파일 +6 −1(게이트웨이만)
 C2 응답 필드               2파일 +2 −1        4파일 +4 −3            4파일 +5 −4
 C3 도메인 규칙             1파일 +1           1파일 +1               1파일 +1 −1
```

- 관찰 1 — **C1에서 계층형이 가장 싸다**(1줄 추가). 대신 그 1줄이 도메인 파일에 들어갔다. 영속 관심사(락 버전)가 도메인 클래스를 건드린다.
- 관찰 2 — C1에서 헥사고날·클린은 도메인을 안 건드렸지만 저장 매핑을 고쳐야 했다(어댑터·게이트웨이 파일 +5 −1, 영속 모델 +1). 도메인 객체에 버전이 없으니, 저장 때 기존 행을 찾아 값만 바꿔야 버전이 유지된다. 모델을 나눈 대가가 이런 데서 나온다.
- 관찰 3 — **C2(바깥으로 값 하나 더 내보내기)는 헥사고날·클린이 파일 수로 두 배**다(2 → 4). 값이 포트의 결과 타입·서비스·컨트롤러(또는 응답 모델·인터랙터·프레젠터)를 차례로 통과해야 한다. 이것이 "계층마다 1:1 매핑"의 비용이다.
- 관찰 4 — C3(순수 업무 규칙)는 세 구조가 같다. 규칙이 도메인 객체 안에 있으면 구조와 무관하게 한 파일이다.
- 해석 — 어느 구조가 "싸다"는 변경의 종류에 달렸다. 바깥(DB·프레임워크)이 자주 바뀌고 도메인을 지켜야 하면 헥사고날·클린의 격리가 값을 한다. 화면에 필드를 자주 더하는 CRUD 위주라면 그 비용만 낸다.

## 쓰이는 자료구조·알고리즘

- **의존 그래프(DAG) 방향 검사** — 패키지를 정점으로 놓고 "안쪽 → 바깥쪽" 간선이 없는지 본다. 클린의 의존성 규칙은 "원(層)에 번호를 매겼을 때 모든 간선이 번호가 작아지는(안쪽으로) 방향"이라는 위상 순서 조건이다(해석). 도구: `jdeps`, ArchUnit 규칙(실험 A), [41](../41-architecture-fitness-rules/2-summary.md).
- **의존성 역전(인터페이스를 안쪽에 둔다)** — 제어 흐름은 유스케이스 → DB인데, 소스 의존은 DB 어댑터 → 포트(안쪽)다. Martin 2012: 동적 다형성으로 제어 흐름과 반대 방향의 소스 의존을 만든다.
- **매퍼(필드 대응)** — 경계마다 하나. 헥사고날 영속 어댑터의 `load`/`save`, 클린의 요청·응답 모델·뷰모델. 비용은 C1·C2 diff로 보였다. 매핑 일반은 [43](../43-data-across-boundaries/2-summary.md).
- **조립(Composition Root)** — 세 구현 모두 `Main`이 구체 클래스를 `new`로 엮는다. 안쪽은 인터페이스만 안다 — [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 순서

1. **유스케이스 하나를 끝까지**: 입력(HTTP) → 유스케이스 → 도메인 → 저장 → 출력. 폴더부터 만들지 않는다.
2. **포트는 안쪽에, 도메인 언어로**: `AccountStore.load/save`처럼. `JpaPort`, `RedisPort`처럼 기술 이름이면 기술을 바꿀 때 포트도 바뀐다. Graça("Explicit Architecture", 2017): 포트는 애플리케이션 코어의 필요에 맞춰 만들어야지 도구 API를 흉내 내면 안 된다.
3. **도메인 순수성 규칙을 바로 건다**: 실험 A의 ArchUnit 규칙. 이름만 헥사고날인 상태를 첫날부터 막는다.
4. **트랜잭션은 유스케이스 단위**: 애플리케이션 서비스(인터랙터) 메서드 하나가 하나의 트랜잭션. 어댑터 안에서 열지 않는다.
5. **예외 번역은 주도 어댑터에서**: 도메인 예외 → HTTP 상태는 웹 어댑터(또는 프레젠터)가 정한다. 도메인은 HTTP를 모른다.
6. **매핑을 줄일 곳을 고른다**: 응답이 도메인과 거의 같으면 유스케이스가 도메인의 읽기 전용 뷰를 돌려주는 식으로 C2 비용을 줄인다(트레이드오프: 바깥이 도메인 타입을 알게 됨). 조회 전용 경로는 유스케이스를 거치지 않는 읽기 모델(CQRS)로 뺄 수 있다 — 이 노트에서 실험하지 않았다.

### 2. 진단

```bash
# 도메인이 프레임워크를 아는가
jdeps -verbose:package -filter:none -cp libs/jakarta.persistence-api-3.2.0.jar build/classes | grep -E '^ +[a-z.]*domain +->' | grep -v java.base
# 변경 하나가 몇 개 층을 지나갔나
git diff --stat HEAD~1
# 1:1 매핑 의례 찾기: 필드 이름이 같은 record가 층마다 반복되는가
grep -rhoE 'record [A-Za-z]+\(.*\)' src | sort | uniq -c | sort -rn | head
```

## 장애 시나리오와 대처

### 1. "헥사고날" 폴더명만 있고 도메인이 JPA 엔티티를 import (⚠ 커리큘럼)

- 현상: DB 컬럼 하나 바꾸는 PR이 도메인 패키지 파일을 수정한다. 도메인 단위 테스트에 JPA가 필요하다.
- 보이는 형태: `jdeps`에 `points.domain -> jakarta.persistence`. ArchUnit `Class <points.domain.PointAccount> is annotated with <jakarta.persistence.Entity>`(실험 A, 계층형). C1 diff가 `domain/PointAccount.java`를 건드린다(실험 B).
- 원인: 폴더 구조만 바꾸고 도메인 = 엔티티를 유지했다. 의존 방향 역전이 일어나지 않았다.
- 대처: 영속 엔티티를 어댑터 안으로 옮기고 package-private으로. 도메인 순수성 규칙을 CI에 둔다.

### 2. 포트를 기술 단위로 만들어 교체 불가 (⚠ 커리큘럼)

- 현상: 저장소를 JPA에서 다른 것으로 바꾸려니 포트 인터페이스와 그것을 쓰는 유스케이스까지 바뀐다.
- 보이는 형태: 포트 이름이 `JpaAccountPort`, 메서드가 `findByIdAndDeletedFalse`, 반환 타입이 `Page<...>`(Spring Data 타입).
- 원인: 포트가 애플리케이션의 필요가 아니라 도구 API를 흉내 냈다(Graça).
- 대처: 포트를 유스케이스 언어로 다시 정의한다(`AccountStore.load`). 기술 세부는 어댑터 안에서 번역한다.

### 3. 계층마다 1:1 매핑만 반복하는 의례적 구조 (⚠ 커리큘럼)

- 현상: 응답에 필드 하나 추가하는 데 파일 네 개를 고친다. 리뷰어가 "이 클래스들은 왜 있나"를 묻는다.
- 보이는 형태: C2 diff가 4파일(실험 B, 헥사고날·클린). 이름만 다르고 필드가 같은 record가 층마다 있다.
- 원인: 경계마다 모델을 나누는 것을 원칙으로 적용했는데, 이 시스템에서는 그 경계들이 실제로 다르게 바뀌지 않는다.
- 대처: 실제로 다르게 바뀌는 경계(외부 API 계약, 영속 스키마)에만 모델을 나눈다. Fowler의 LocalDTO 비판([43](../43-data-across-boundaries/2-summary.md))과 같은 축이다. Brown도 이상적인 소스 트리 분리에는 실제 성능·복잡도·유지보수 비용이 따른다고 적는다.

### 4. 트랜잭션 경계가 어댑터에 있어 유스케이스가 반쯤 저장된다

- 현상: 포인트는 차감됐는데 사용 내역이 저장되지 않은 건이 나온다.
- 보이는 형태: 두 저장이 서로 다른 트랜잭션 로그에 있다. 중간 예외 뒤 한쪽만 커밋.
- 원인: 영속 어댑터 메서드마다 트랜잭션을 열었다. 유스케이스 하나가 여러 트랜잭션으로 쪼개졌다.
- 대처: 트랜잭션은 유스케이스(애플리케이션 서비스·인터랙터) 단위로 연다(2절 표). 이 시나리오는 이 노트에서 실행하지 않았다 — 원칙과 해석이다. 트랜잭션 경계 일반은 [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md).

## 핵심 문장

- 세 구조의 차이는 폴더가 아니라 다섯 결정(포트 위치, 어댑터 방향, 매핑, 트랜잭션 경계, 예외 번역)이 놓이는 자리다.
- 같은 유스케이스가 계층형 4파일, 헥사고날 8파일, 클린 12파일이었다. 계층형 도메인만 `jakarta.persistence`에 의존했고 ArchUnit 순수성 규칙에서 실패했다.
- 영속 변경(`@Version`)은 계층형이 1줄 추가로 가장 쌌지만 도메인 파일을 건드렸다. 헥사고날·클린은 도메인을 지키는 대신 저장 매핑을 고쳤다(파일 2개, +6 −1).
- 응답에 값 하나를 더하는 변경은 헥사고날·클린이 4파일, 계층형이 2파일이었다. 순수 도메인 규칙 변경은 셋 다 1파일이었다.
- 어느 구조가 싼지는 자주 오는 변경의 종류로 정한다. 포트는 도구 API가 아니라 애플리케이션의 필요에 맞춰 도메인 언어로 이름 짓는다.

## 관련 주제·근거

- 선행
  - [38-layered-hexagonal-clean](../38-layered-hexagonal-clean/2-summary.md) — 세 구조의 원리(이 노트는 그 코드판)
  - [40-codebase-structure](../40-codebase-structure/2-summary.md) — 배치와 가시성
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 조립
  - [43-data-across-boundaries](../43-data-across-boundaries/2-summary.md) — 경계의 모델과 매핑 비용
- 후속·연결
  - [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md) — 도메인 순수성·계층 규칙을 테스트로
  - [domain-modeling/basic/14-points](../../domain-modeling/basic/14-points/2-summary.md) — 예제 도메인 원본(덩어리·만료 포함)
  - [systems/architecture-styles](../../systems/architecture-styles/2-summary.md) — 아키텍처 스타일 개관
- 글·문서
  - Alistair Cockburn, "Hexagonal Architecture"(원 글 2005, 페이지의 날짜 표기 2005-09-04 v0.9) — 의도문, primary/secondary(driving/driven) <https://alistair.cockburn.us/hexagonal-architecture>
  - Robert C. Martin, "The Clean Architecture", 2012-08-13 — 의존성 규칙, 네 원, 경계 넘기(출력 포트), 경계를 넘는 데이터는 단순 구조 <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
  - Robert C. Martin, 『Clean Architecture』(2017) 22장 "The Clean Architecture" — 장 번호는 독자 요약 저장소 목차로만 확인, 본문 미열람 [?] <https://github.com/serodriguez68/clean-architecture>
  - Herberto Graça, "DDD, Hexagonal, Onion, Clean, CQRS, … How I put it all together"(Explicit Architecture), 2017-11-16 — 포트는 코어의 필요에 맞추고 도구 API를 흉내 내지 않는다 <https://herbertograca.com/2017/11/16/explicit-architecture-01-ddd-hexagonal-onion-clean-cqrs-how-i-put-it-all-together/>
  - Simon Brown, "Package by component"(소스 트리 분리의 비용, Périphérique 안티패턴) <https://simonbrown.je/modular-monolith>
- 실험 목록 (코드: scratchpad `sd/40/e44-base/`(base 스냅샷 + `changes.py` + `replay.sh`), 재생 결과 `sd/40/e44/`, ArchUnit 규칙 `sd/40/e44-arch/DomainPurity.java` / JDK 21.0.12 temurin `--cpus=2`, jakarta.persistence-api 3.2.0, ArchUnit 1.5.1)
  - 세 구현 실행 — `e44/run.sh`
  - A 크기 — base 스냅샷에서 `find … | wc -l` / 의존 방향 — `e44/size.sh`(jdeps), `e44-arch/run.sh`(ArchUnit)
  - B 변경 C1·C2·C3 — `bash e44-base/replay.sh <새 디렉터리>`
