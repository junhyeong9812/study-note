# reliability/51-cells-stamps-and-blast-radius — 셀·스탬프·셔플 샤딩: 장애 반경을 구조로 제한하기 — 정리 (힌트)

## 해결하는 문제

이중화(→ [25-high-availability-topology](../25-high-availability-topology/2-summary.md))는 "한 대가 죽으면 다른 대가 받는다"를 만든다. 그런데 어떤 장애는 **받아 주는 쪽도 같이 죽인다.**

```text
 공유 풀 하나에 고객 전부                          독이 든 요청(poison request) 하나
 고객 A·B·C·…·Z ─> [w1 w2 w3 w4 w5 w6 w7 w8]      w1이 죽음 → 그 요청이 w2로 재시도 → w2도 죽음 → … → 전부
                                                  "everything and everyone" (AWS Builders' Library)
```

- *장애 반경(blast radius, scope of impact)*: 장애 하나가 영향을 주는 고객·요청의 범위.
- 이중화는 고장 난 노드를 대신할 노드를 준다. 하지만 장애 원인이 **요청 자체**(독이 든 요청, 한 고객의 폭주, 나쁜 배포·설정)면 그 원인은 대신 받은 노드도 쓰러뜨린다.
- 그래서 장애 반경을 줄이는 방법은 "더 많은 복제"가 아니라 **나누기**다. 고객을 칸막이로 나눠, 한 칸의 문제가 다른 칸으로 못 넘어가게 한다.

쉬운 예: 배의 격벽이다.
- 칸막이 없는 배는 구멍 하나로 전체가 잠긴다.
- 격벽으로 나눈 배는 구멍 난 칸만 물이 찬다. AWS 셀 백서의 비유가 바로 이것이다.

똑같은 구조다.\
실무 예: AWS 서비스 내부의 셀 구조, Azure의 Deployment Stamps, Route 53의 셔플 샤딩, SaaS의 테넌트별 스탬프.\
원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §4 「셀 기반 아키텍처」에 한 단락 소개가 있다. 이 노트는 셀·스탬프·Geode·셔플 샤딩을 구분하고, 장애 반경과 셀 매핑을 실험으로 잰다.

## 동작·원리

### 1. 셀 기반 아키텍처의 세 부품

```text
                    클라이언트 (엔드포인트 하나)
                           │
                   ┌───────▼────────┐   ← 셀 라우터: "가장 얇은 층". 파티션 키 → 셀, 그 일만 한다
                   │   셀 라우터     │
                   └─┬──────┬─────┬─┘
            ┌────────▼┐ ┌───▼────┐ ┌▼────────┐
            │ 셀 1     │ │ 셀 2    │ │ 셀 3     │  ← 셀: 작업 전체의 완결된 사본(앱·DB·큐…)
            │ 고객 A~F │ │ 고객 G~M│ │ 고객 N~Z │     셀끼리 상태를 공유하지 않는다
            └──────────┘ └─────────┘ └──────────┘
   제어 플레인: 셀 생성·삭제, 고객 배치·이동, 배포  (데이터 플레인 = 라우터 + 셀)
```

AWS Well-Architected 백서 "Reducing the Scope of Impact with Cell-Based Architecture"(2023-09-20)의 정의다.

- *셀(cell)*: 작업의 독립된 인스턴스 하나. 다른 셀과 상태를 공유하지 않고 전체 요청의 일부를 처리한다. 백서 예: 셀 10개가 요청 100개를 고르게 나눠 받으면 셀 하나의 장애에도 요청 90%는 영향이 없다. 실제 영향은 고장 난 셀이 받던 요청의 비율이다(아래 실험 3에서는 한 셀이 26.5%를 받았다).
- *파티션 키(partition key)*: 요청을 셀에 나누는 기준(고객 ID·리소스 ID). 대부분의 API 호출에서 쉽게 꺼낼 수 있고, 셀을 가로지르는 상호작용이 적은 단위여야 한다.
- *셀 라우터*: 파티션 키로 셀을 찾아 보내는 층. 백서는 "가장 얇은 가능한 층"이라 부르고, 라우팅만 하라고 한다.
- 셀로 바꾼다고 인프라가 두 배가 되는 것은 아니다. 호스트 30대가 그대로 30대인데 셀로 나뉠 수도 있다(백서).
- 셀이 막아 주는 장애: 나쁜 코드 배포, 독이 든 요청, 한 고객의 폭주. 셀 단위로 **배포 웨이브**(한 번에 셀 하나 또는 몇 개)를 돌고 이상 징후에 롤백하면, 나쁜 배포의 반경은 그 웨이브의 셀들로 줄어든다(백서 "Cell deployment"). 반경은 웨이브 크기와 얼마나 빨리 발견·중단하느냐에 달렸다.

### 2. 이름이 다른 비슷한 것들 — 스탬프·Geode

| 패턴 | 출처 | 한 인스턴스가 받는 요청 | 데이터 |
|---|---|---|---|
| 셀 | AWS 셀 백서 | 그 셀에 배치된 고객만 | 셀마다 따로 |
| 배포 스탬프(Deployment Stamps) | Azure Architecture Center | 그 스탬프의 테넌트만. "stamp는 service unit·scale unit·cell이라고도 부른다" | 스탬프마다 따로(암묵적 샤딩) |
| Geode | Azure Architecture Center | **어느 사용자든** — 가까운 지오드가 받는다 | 전 지오드에 복제(예: Cosmos DB) |

- Azure 문서: 스탬프와 Geode의 차이는 스탬프는 일부 고객만 받고 Geode는 어느 요청이든 어느 인스턴스나 받는다는 것이다. Geode는 설계가 더 복잡하다.
- Geode는 "가까운 곳에서 처리"가 목적이고, 장애 반경 축소보다 지연·지역 가용성에 무게가 있다. 데이터를 전 지오드에 복제하므로 나쁜 데이터도 퍼진다.
- 스탬프는 배포 링(deployment ring)에도 쓴다. 업데이트를 자주 원하는 고객과 아닌 고객을 다른 스탬프에 두고 주기를 달리한다(Azure 문서).

### 3. 셔플 샤딩 — 같은 작업자 수로 반경을 더 줄인다

```text
 작업자 8대

 고정 샤드: 2대씩 4묶음                 셔플 샤드: 고객마다 8대 중 아무 2대 (C(8,2)=28가지)
 [1 2] [3 4] [5 6] [7 8]               무지개 고객 = {1,4}, 장미 고객 = {1,8}, 해바라기 = {4,6} …
 독 고객이 [1 2]를 죽이면               독 고객(무지개)이 {1,4}를 죽이면
 → 같은 묶음 고객 25% 전부 다운          → {1,4}를 그대로 쓰는 고객만 전부 다운(1/28)
                                        → 장미는 8번, 해바라기는 6번으로 버틴다(재시도할 때)
```

- *셔플 샤딩(shuffle sharding)*: 고객마다 작업자 집합을 조합으로 따로 뽑아 주는 것. 두 고객이 작업자를 **전부** 공유할 확률이 작아진다.
- AWS Builders' Library(Colm MacCárthaigh) 원문 숫자
  - 8대·2대씩: 28가지 셔플 샤드 → 반경 1/28. 고정 샤드 4개(반경 1/4)보다 7배 낫다.
  - Route 53: 가상 네임 서버 2,048개, 도메인마다 4개 → 약 7,300억 가지. 어느 두 도메인도 가상 네임 서버를 2개 넘게 공유하지 않게 배정한다.
- 조건: **클라이언트가 재시도로 다른 작업자를 찾아갈 수 있어야** 한다. 원문: "If the requestors are fault tolerant and can work around this (with retries for example)". 한 작업자만 고집하는 클라이언트면 일부가 겹친 고객도 다운된다.

### 4. 실험: 장애 반경·셀 재배치·큰 테넌트

```java
/** 셔플 샤딩: 테넌트 이름을 시드로 작업자 목록을 섞어 앞 k개 */
static int[] shuffleShard(String tenant, int workers, int k) {
    List<Integer> l = new ArrayList<>(); for (int i = 0; i < workers; i++) l.add(i);
    Collections.shuffle(l, new Random(h(tenant)));
    return l.subList(0, k).stream().mapToInt(Integer::intValue).sorted().toArray();
}
// 독 테넌트 tenant-0이 자기 작업자 k개를 모두 죽인다 → 나머지 999 테넌트를
//   전부 다운(자기 작업자가 다 죽음) / 일부 다운(재시도로 버팀) / 무관 으로 센다
// 셀 매핑: 모듈로(h % N) vs 일관 해싱 링(셀당 가상 노드 100) — 셀 10 → 11
// 큰 테넌트: Zipf(s=1.1) 트래픽 테넌트 1000개를 셀 10개에 해시 배치, 1위를 재정의 표로 전용 셀에
```

(실험, JDK 21.0.12 temurin, `--cpus=2`, 해시·시드 고정이라 실행마다 같은 값, 2026-10-01)

```text
== 1. 장애 반경: 작업자 8대, 테넌트 1000, 독 테넌트 1개가 자기 작업자를 모두 죽임
공유 풀(모두가 8대 전부)            사용된 샤드 조합    1개 | 다른 테넌트: 전부 다운  999 (100.0%), 일부 다운    0 (0.0%), 무관    0
고정 샤드 4개×2대                사용된 샤드 조합    4개 | 다른 테넌트: 전부 다운  241 (24.1%), 일부 다운    0 (0.0%), 무관  758
셔플 샤드 2대 (8C2=28)          사용된 샤드 조합   28개 | 다른 테넌트: 전부 다운   24 (2.4%), 일부 다운  435 (43.5%), 무관  540
셔플 샤드 4대 (16C4=1820)       사용된 샤드 조합  791개 | 다른 테넌트: 전부 다운    0 (0.0%), 일부 다운  738 (73.9%), 무관  261
   참고: C(8,2)=28, C(2048,4)=7.309e+11 (Route 53 예)
== 2. 셀 매핑: 테넌트 → 셀. 셀 10개에서 11개로 늘릴 때 다른 셀로 옮겨지는 테넌트
   모듈로(h % N): 9071/10000 이동 (90.7%) | 일관 해싱(셀당 가상 노드 100): 1022/10000 이동 (10.2%)
== 3. 큰 테넌트: 트래픽이 Zipf(s=1.1)인 테넌트 1000개를 셀 10개에 해시 배치
   해시만: 셀 0~9 중 가장 붐비는 셀 1 = 전체 트래픽의 26.5% (셀 0~9 평균 10.0%)
   1위 테넌트(혼자 17.9%)를 전용 셀 10번으로 옮긴 뒤: 셀 0~9 중 가장 붐비는 셀 8 = 전체 트래픽의 12.0% (셀 0~9 평균 8.2%), 전용 셀 10번 17.9%
```

- 관찰 1: 공유 풀은 100%, 고정 샤드는 24.1%(이론 1/4), 셔플 샤드 2대는 2.4%(이론 1/28 ≈ 3.6% — 테넌트 1,000개 표본이라 흔들린다)가 **전부** 다운됐다. 원문의 "7배"와 같은 방향이다.
- 관찰 2: 셔플 샤드에서는 "일부 다운"이 43.5%로 많다. 이 고객들은 살아 있는 다른 작업자로 재시도해야 버틴다. 재시도가 없으면 셔플 샤딩의 이득 대부분이 사라진다.
- 관찰 3: 작업자 16대·4대씩이면 전부 다운이 0명이다. 대신 작업자 4/16이 죽어 용량 25%가 빠졌고(8대·2대의 2/8과 같은 비율), 73.9%가 재시도에 기댄다. 작업자 수와 k를 함께 바꾼 비교라 차이를 k 하나의 효과로만 읽지 않는다. 작업자 수가 같다면 k가 클수록 "전부 겹칠 확률"은 줄고 독 하나가 죽이는 작업자는 는다 — 그 절충이다.
- 관찰 4: 셀을 10 → 11개로 늘릴 때 모듈로 배치는 테넌트 90.7%를 옮긴다. 일관 해싱은 10.2%(이론 1/11 ≈ 9.1%)만 옮긴다. 상태가 있는 셀에서 옮김은 곧 데이터 이전이라 이 차이가 크다.
- 관찰 5: 해시 배치는 고객 수를 고르게 나눌 뿐, **트래픽**을 고르게 나누지 않는다. 1위 테넌트 혼자 17.9%라서 그 테넌트가 든 셀은 26.5%를 받았다(평균의 2.65배). 재정의 표로 1위를 전용 셀로 옮기자 나머지 셀의 최대가 12.0%로 내려갔다.

### 5. 셀 라우터 — 남은 단일 장애점

- AWS 셀 백서 "About resilience of the cell router": 전 셀의 공유 상태를 가진 유일한 구성 요소가 셀 라우터이고, 그래서 **단일 장애점**으로 보인다. 라우터도 최대한 신뢰성 있게, 그 자체도 셀처럼 만들어야 한다.
- 정적 안정성(static stability): 백서 "Control plane and data plane"은 제어 플레인이 내려가도 데이터 플레인(라우터 + 셀)이 마지막으로 받은 상태로 계속 동작해야 한다고 적는다. 예: 라우터가 셀 매핑을 S3에서 메모리로 읽어 두면, 제어 플레인·S3·존 하나가 안 돼도 트래픽을 보낸다.
- 백서: 제어 플레인은 틀린 정보를 주느니 실패하는 쪽(CAP의 CP), 데이터 플레인은 낡은 정보로라도 가용한 쪽(AP)을 택한다.

### 6. 셀 크기와 셀 이동

- 크기의 세 힘(AWS 백서 "Cell sizing"): 가장 큰 작업이 들어갈 만큼 크게 / 전체 규모로 시험할 수 있을 만큼 작게 / 규모의 경제를 얻을 만큼 크게. 셀이 작을수록 반경이 작고(셀 100개면 고르게 나눌 때 1%) 시험이 쉽지만 운영할 사본이 많다.
- 셀마다 한계를 알고(부하 시험·카오스 실험) 넘으면 로드 셰딩한다(→ [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md)).
- 이동(백서 "Cell migration"): 새 위치에 비권위 사본 복제 → 새 사본을 권위로 전환 → 옛 위치에서 새 위치로 리다이렉트 → 옛 데이터 삭제. 이동 중에는 매핑 버전이 둘일 수 있다.
- 백서 "Best practices": 첫날부터 셀을 여러 개로 시작하고, 첫날부터 셀 이동 수단을 갖춰라. Azure 문서도 스탬프를 최소 두 개 두라고 한다. 하나뿐이면 "스탬프는 하나"라는 가정이 코드·설정에 박힌다.

## 쓰이는 자료구조·알고리즘

- **매핑 방식**(AWS 백서 "Cell partition")
  - 전체 매핑(full mapping): 키마다 셀을 표로 저장. 유연하지만 표가 크다.
  - 접두사·범위 매핑: 키 범위 → 셀.
  - 모듈로: `hash(key) % N`. 셀 수가 바뀌면 거의 다 옮긴다(실험 2: 90.7%).
  - 일관 해싱: 셀 수가 바뀌어도 약 1/N만 옮긴다(실험 2: 10.2%). 해시 링·가상 노드는 [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
  - 전체 매핑을 뺀 어느 방식이든 **재정의 표(override table)**를 함께 둔다(전체 매핑은 그 기능을 스스로 가진다) — 시험·격리·무거운 키를 특정 셀로(백서 "A warning for all mapping approaches", 실험 3).
- **조합(셔플 샤드)** — n개 중 k개 고르기, C(n,k)가지. 두 고객이 k개를 전부 공유할 확률 ≈ 1/C(n,k). 결정적 셔플(키를 시드로)로 같은 고객 → 같은 샤드.
- **Zipf 분포** — 소수의 큰 테넌트가 트래픽 대부분을 내는 모양. 개수 기준 균등 배치가 부하 균등을 뜻하지 않는다.
- **토큰 버킷** — 셀 입구에서 셀 한계를 지키는 속도 제한(백서가 예로 든다, [11-rate-limiter](../11-rate-limiter/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. 전역 공유 구성 요소 목록을 만든다. "이것이 죽으면 고객 몇 %가 영향받나?" 100%면 그것이 반경의 상한이다(인증·설정 저장소·전역 DB·메시지 버스·DNS).
2. 파티션 키를 고른다. 대부분 API에 있고, 셀을 가로지르는 호출이 적은 단위. 큰 고객은 둘째 차원(고객 + 지역 등)을 붙일 여지를 둔다(백서 "Cell partition").
3. 셀 수는 처음부터 둘 이상. 지금의 스택을 "셀 0"으로 보고 라우터를 그 앞에 붙인다(백서 "Best practices").
4. 매핑: 일관 해싱 또는 전체 매핑 + 재정의 표. 매핑은 라우터 메모리에 두고 제어 플레인이 갱신한다(정적 안정성).
5. 셀 한계를 잰다(부하 시험). 한계에서 셰딩. 큰 테넌트는 전용 셀로.
6. 배포·설정 변경은 셀 웨이브로(→ [23-deployment-strategies](../23-deployment-strategies/2-summary.md)). 셀 1개 → 몇 개 → 나머지.
7. 셀 이동 절차를 만들고 실제로 써 본다.
8. 공유 작업자 풀이 필요한 곳은 셔플 샤딩 + 클라이언트 재시도.

### 2. 셀 라우터 (Java, 최소형)

```java
/** 재정의 표 → 일관 해싱 링 순서로 셀을 찾는다. 매핑은 메모리 스냅숏(제어 플레인이 교체). */
final class CellRouter {
    private volatile Snapshot snap;                           // 제어 플레인이 원자 교체
    record Snapshot(long version, Map<String, Integer> overrides, NavigableMap<Long, Integer> ring) {}

    int cellFor(String tenantId) {
        Snapshot s = snap;
        Integer o = s.overrides().get(tenantId);              // 큰 테넌트·격리·시험
        if (o != null) return o;
        long h = hash64(tenantId);
        Map.Entry<Long, Integer> e = s.ring().ceilingEntry(h);
        return (e != null ? e : s.ring().firstEntry()).getValue();
    }

    synchronized void replace(Snapshot next) {                // 버전이 커질 때만 받는다 — 비교와 대입을 묶으려고 synchronized
        if (next.version() > snap.version()) snap = next;
    }
    // hash64: 라우터 인스턴스·언어가 달라도 같은 값을 내는 안정된 해시(실험은 String.hashCode에 murmur3 섞기 함수를 얹었다)
}
```

- 제어 플레인이 죽어도 `snap`은 마지막 값으로 남는다. 라우터는 계속 보낸다.

### 3. 관측 — 셀 단위로 본다

```promql
# 셀별 오류율 — 한 셀만 튀면 그 셀의 배포·테넌트를 의심(전 셀이 같이 튀면 공유 구성 요소)
sum by (cell) (rate(http_requests_total{code=~"5.."}[5m])) / sum by (cell) (rate(http_requests_total[5m]))
# 셀 안 테넌트별 트래픽 상위 — 셀을 포화시키는 큰 테넌트 찾기
topk(5, sum by (cell, tenant) (rate(http_requests_total[5m])))
```

## 장애 시나리오와 대처

### 1. ⚠ 전역 공유 구성 요소 하나의 장애 → 전 고객 동시 중단

- 현상: 셀로 나눴는데 장애가 나자 전 셀의 고객이 같이 멈췄다.
- 보이는 형태: 셀별 오류율이 **전 셀에서 동시에** 오른다. 공통 의존성(전역 인증, 전역 설정 저장소, 공유 DB, 공유 큐)의 오류가 같은 시각.
- 원인: 셀이 상태·구성 요소를 공유한다. 백서 "Cell migration": 셀은 셀끼리 상태나 구성 요소를 공유하지 말아야 한다.
- 대처: 공유 의존성을 셀 안으로 넣거나, 셀마다 사본을 둔다. 남길 수밖에 없는 공유 요소는 정적 안정성(마지막 값으로 계속 동작)과 셀 단위 배포를 지킨다.

### 2. ⚠ 셀 라우팅 계층 자체가 SPOF

- 현상: 셀은 다 멀쩡한데 라우터 장애나 매핑 저장소 장애로 전부 접속 불가.
- 보이는 형태: 라우터 5xx·타임아웃, 셀 쪽 트래픽 0. 매핑을 매 요청 원격 조회하는 구조면 매핑 저장소 장애와 시각이 겹친다.
- 원인: 라우터는 전 셀의 매핑을 가진 유일한 구성 요소다(백서). 라우터가 제어 플레인에 실시간으로 기댄다.
- 대처: 라우터를 얇게(라우팅만), 여러 인스턴스·존으로, 매핑은 메모리 스냅숏(제어 플레인 장애에도 동작). 라우터 배포도 웨이브로. Azure 문서도 라우팅 서비스를 여러 리전에 두고 매핑 저장소를 동기화하라고 한다.

### 3. ⚠ 셀 간 이동 절차가 없어 대형 테넌트가 셀 하나를 포화

- 현상: 한 셀만 지연이 오르고 오류가 난다. 그 셀의 다른 고객도 같이 피해를 본다.
- 보이는 형태: 실험 3처럼 한 셀의 트래픽이 평균의 2.65배. `topk`로 보면 테넌트 하나가 대부분.
- 원인: 해시 배치는 고객 수만 고르게 나눈다(트래픽은 Zipf). 테넌트를 옮길 수단이 없다.
- 대처: 재정의 표로 큰 테넌트를 전용 셀로(실험: 나머지 최대 26.5% → 12.0%). 이동 절차(복제 → 권위 전환 → 리다이렉트 → 삭제)를 첫날부터. 셀 한계에서 셰딩해 이웃 고객을 지킨다.

### 4. 셔플 샤딩을 했는데 겹친 고객이 다운

- 현상: 독 고객과 작업자 하나만 겹친 고객도 오류를 낸다.
- 보이는 형태: 실험 1의 "일부 다운" 고객 쪽 오류. 클라이언트가 첫 작업자 실패 후 다른 작업자로 재시도하지 않는다.
- 원인: 셔플 샤딩의 이득은 재시도 가능한 클라이언트를 전제로 한다(Builders' Library 원문).
- 대처: 클라이언트가 샤드 안의 다른 작업자로 재시도(지터 포함, [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md)). 독 요청 자체는 격리 용량으로 옮긴다(Route 53 예).

### 5. 셀 수를 바꾸자 대량 재배치

- 현상: 셀을 하나 늘렸더니 테넌트 대부분의 데이터가 이동해야 한다.
- 보이는 형태: 실험 2의 모듈로처럼 90.7% 이동.
- 원인: `hash % N` 매핑.
- 대처: 일관 해싱(10.2%)이나 전체 매핑 표. 새 셀에는 새 테넌트만 배치하는 방식도 있다(Azure: 용량을 보며 스탬프를 미리 늘리고 새 테넌트를 거기로).

## 핵심 문장

- 이중화는 고장 난 노드를 대신하지만, 요청·배포·고객이 원인인 장애는 대신 받은 노드도 쓰러뜨린다. 장애 반경은 나누기로 줄인다.
- 셀은 상태를 공유하지 않는 작업의 완결된 사본이고, 셀 라우터는 파티션 키로 셀을 고르는 가장 얇은 층이다. 남은 공유 구성 요소가 반경의 상한이다.
- 실험에서 작업자 8대 기준 전부 다운된 고객은 공유 풀 100%, 고정 샤드 24.1%, 셔플 샤드 2.4%였다. 셔플 샤딩의 이득은 재시도할 수 있는 클라이언트를 전제로 한다.
- 셀 매핑은 일관 해싱(셀 추가 때 10.2% 이동)이나 매핑 표에 재정의 표를 더해 쓴다. 해시는 고객 수를 나눌 뿐 트래픽을 나누지 않는다.
- 제어 플레인이나 매핑 저장소가 내려가도 살아 있는 셀 라우터(데이터 플레인)는 메모리의 마지막 매핑으로 계속 동작해야 한다(정적 안정성). 라우터 자체는 데이터 플레인이라 여러 대로 둔다.

## 관련 주제·근거

- 선행
  - [25-high-availability-topology](../25-high-availability-topology/2-summary.md) — 이중화·장애 도메인
  - [software-design/49-multi-tenancy](../../software-design/49-multi-tenancy/2-summary.md)
  - [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md) — 커리큘럼 번호 data-structure/23(일관 해싱)의 노트
  - 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §4 「셀 기반 아키텍처」. 참고: 원본은 셀을 "대규모 서비스의 사실상 표준"이라고 적는데, 이 노트가 연 자료에서 확인한 것은 AWS가 10년 넘게 셀 구조를 써 왔다는 것(셀 백서 서론)과 Azure가 패턴으로 권한다는 것까지다. 업계 표준 여부는 확인하지 못했다[?].
- 후속·연결
  - [23-deployment-strategies](../23-deployment-strategies/2-summary.md) — 셀 웨이브 배포
  - [28-bulkhead](../28-bulkhead/2-summary.md) — 한 프로세스 안의 격벽, 셀은 시스템 규모의 격벽
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md), [11-rate-limiter](../11-rate-limiter/2-summary.md) — 셀 한계 지키기
  - [46-disaster-recovery](../46-disaster-recovery/2-summary.md) — 스탬프는 리전 간 중복이 아니다(Azure: 리전 장애 때 그 리전 스탬프의 테넌트는 접속 불가)
  - [database/33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md) — 데이터 분할
- 문서·글
  - AWS Well-Architected, "Reducing the Scope of Impact with Cell-Based Architecture", 2023-09-20 — What is a cell-based architecture, Control plane and data plane, Cell partition, A warning for all mapping approaches, About resilience of the cell router, Cell sizing, Cell placement, Cell migration, Cell deployment, Best practices <https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html>
  - MacCárthaigh, "Workload isolation using shuffle-sharding", Amazon Builders' Library — 8대·28가지·1/28·7배, Route 53 2,048개·4개·7,300억 <https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/>(현재 builder.aws.com으로 이동, 본문은 web.archive.org 사본으로 확인)
  - Microsoft Azure Architecture Center, "Deployment Stamps pattern" <https://learn.microsoft.com/en-us/azure/architecture/patterns/deployment-stamp>, "Geode pattern" <https://learn.microsoft.com/en-us/azure/architecture/patterns/geodes>
- 실험 목록
  - E51: 테넌트 1,000개·작업자 8대(및 16대) — 공유 풀·고정 샤드·셔플 샤드의 장애 반경, 셀 10 → 11 재배치(모듈로 vs 일관 해싱), Zipf 테넌트의 셀 부하와 재정의 표. JDK 21.0.12, 코드 scratchpad `rel/23/e51/BlastRadius.java`, `docker run --rm --cpus=2 eclipse-temurin:21-jdk java BlastRadius.java`
