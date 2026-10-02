# reliability/01-fault-error-failure-availability — 결함·오류·고장의 구분과 가용성 합성 — 정리 (힌트)

## 해결하는 문제

"서버가 죽었다"는 말 하나에 세 가지가 섞여 있다.
원인(디스크 불량), 내부 상태(깨진 캐시 항목), 사용자가 본 결과(500 응답)다.
이 셋을 구분하지 않으면 대처가 엇나간다. 원인을 없애야 할 때 결과만 막거나, 결과가 없는데 원인을 쫓는다.

또 "얼마나 잘 돌아야 하나"를 숫자로 말하지 못하면 약속도 투자도 못 한다.
숫자로 말하려면 부품 여러 개를 묶었을 때 전체 숫자가 어떻게 되는지 계산할 줄 알아야 한다.

쉬운 예: 출근길 지하철 환승이다.
- 1호선이 99.9% 제시간, 2호선도 99.9%, 버스도 99.9%라면, 세 번 다 갈아타야 하는 출근은 셋 다 맞아야 제시간이다.
- 하나라도 늦으면 지각이다. 갈아탈수록 지각 확률이 쌓인다.
- 반대로 "택시 또는 지하철" 중 하나만 되면 되는 길은 둘 다 늦을 때만 지각이다.

똑같은 구조다.\
실무 예: 요청 하나가 게이트웨이 → 주문 → 결제 → 재고 → DB를 차례로 거친다. 각각 99.9%여도 전체는 그보다 낮다.
이것을 모르고 고객에게 "99.9%"를 약속하면, 부품이 다 목표를 지켜도 약속은 깨진다(아래 장애 1).

기초(가용성 표·RTO/RPO·이중화 토폴로지)는 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1에 있다. 이 노트는 그중 「가용성 합성」을 용어 정의부터 다시 세우고, 계산을 실험으로 확인한다.

## 동작·원리

### 1. 결함 → 오류 → 고장의 사슬

Avižienis·Laprie·Randell·Landwehr(2004)의 정의를 그대로 옮긴다.

```text
   부품 A 안                                   부품 A의 경계          부품 B(A를 쓰는 쪽)
 ┌──────────────────────────────────────┐        │
 │ 결함(fault)  ──활성화──>  오류(error)  ──전파──>│ 고장(failure) ──>  B에게는 "외부 결함"
 │ 예: off-by-one 코드     예: 잘못 계산된   │        │ 예: 틀린 잔액 응답      → B 안에서 다시 오류 …
 │     (잠복 중)            잔액이 메모리에   │        │
 └──────────────────────────────────────┘        │
```

- *고장(failure, service failure)*: 시스템이 내보내는 서비스가 올바른 서비스에서 **벗어나는 사건**. 사용자가 본다(논문 2.2절).
- *오류(error)*: 시스템 전체 상태 가운데 **이후 고장으로 이어질 수 있는 부분**. 많은 오류는 바깥 상태에 닿지 못하고 고장이 되지 않는다(2.2절).
- *결함(fault)*: 오류의 원인으로 **판정되거나 가정된 것**. 오류를 만들면 활성(active), 아니면 잠복(dormant)이다(2.2절·3.5절).
- 사슬은 이어진다. A의 고장은 A를 쓰는 B에게 **외부 결함**으로 나타난다(3.5절 "fundamental chain").
  - 그래서 "고장"이냐 "결함"이냐는 **어느 경계에서 보느냐**로 정해진다. 디스크 입장에서 고장인 것이 DB 입장에서는 결함이다.

이 구분이 주는 것은 대처의 위치다.

| 대처 수단(논문 2.4절) | 겨냥하는 칸 | 예 |
|---|---|---|
| fault prevention(결함 예방) | 결함이 생기지 않게 | 코드 리뷰, 타입 |
| fault tolerance(결함 허용) | 결함이 있어도 고장으로 안 가게 | 이중화, 재시도, 체크섬 |
| fault removal(결함 제거) | 있는 결함을 줄인다 | 테스트, 버그 수정 |
| fault forecasting(결함 예측) | 결함의 수·영향을 추정 | 가용성 계산, 장애 주입 |

### 2. 고장의 모양 — 같은 "고장"도 여러 가지다

논문 3.3.1절은 고장을 네 관점으로 나눈다.

```text
 영역      내용 고장(틀린 값)   │ 시간 고장(너무 늦게·일찍)
           둘 다 틀리면 → 정지(halt, 출력이 멈춤, 특수형=침묵 silent) / 엉뚱(erratic, 아무 말이나 함)
 탐지      신호 있는 고장(signaled — 에러 코드·경보) │ 신호 없는 고장(unsignaled — 조용히 틀림)
 일관성    모든 사용자가 똑같이 봄(consistent) │ 사용자마다 다르게 봄(inconsistent = 비잔틴)
 결과      경미(minor) … 치명(catastrophic)
```

- 운영에서 가장 비싼 것은 **신호 없는 고장**이다. 대시보드는 초록인데 값이 틀린다. → [04-failure-modes-catalog](../04-failure-modes-catalog/2-summary.md)의 F-25.
- 분산 알고리즘이 어떤 고장을 가정하는지(crash-stop·crash-recovery·비잔틴)는 [distributed/02](../../distributed/02-system-and-failure-models/2-summary.md)에서 다룬다. 이 노트는 그 고장을 **얼마나 자주, 얼마나 오래** 겪는지를 다룬다.

### 3. 가용성 — 정의와 두 가지 재는 법

- *가용성(availability)*: "올바른 서비스를 내줄 준비가 된 정도"(readiness for correct service). *신뢰성(reliability)*은 "올바른 서비스가 끊기지 않고 이어지는 정도"(continuity)다(논문 2.3절).
  - 둘은 다르다. 1시간에 한 번 1초씩 끊기는 서비스는 가용성은 높고(99.97%), 신뢰성(끊김 없이 이어지는 시간)은 낮다.

SRE 책 3장은 가용성을 재는 식 두 개를 준다.

```text
 시간 기반   가용성 = 가동 시간 / (가동 시간 + 중단 시간)
 요청 기반   가용성 = 성공한 요청 / 전체 요청      ← Google은 전 세계에 퍼진 서비스라 주로 이쪽(3장)
```

- 요청 기반은 "일부만 죽은" 상태를 잡는다. 10대 중 1대가 죽어 10% 요청이 실패하면 시간 기반으로는 "가동 중"이지만 요청 기반으로는 90%다.

"9의 개수"는 허용 중단 시간으로 바꿔 읽는다(SRE 부록 A 표에서 옮김).

| 가용성 | 연간 | 월간 | 주간 | 일간 |
|---|---|---|---|---|
| 99% | 3.65일 | 7.2시간 | 1.68시간 | 14.4분 |
| 99.5% | 1.83일 | 3.6시간 | 50.4분 | 7.20분 |
| 99.9% | 8.76시간 | 43.2분 | 10.1분 | 1.44분 |
| 99.99% | 52.6분 | 4.32분 | 60.5초 | 8.64초 |
| 99.999% | 5.26분 | 25.9초 | 6.05초 | 0.87초 |

- 9가 하나 늘면 허용 비가용 시간이 10분의 1이 된다(SRE 3장 "Each additional nine corresponds to an order of magnitude improvement toward 100%").
- 참고: 원본 §1의 "9가 하나 늘 때마다 비용은 대략 한 자릿수씩 는다"는 SRE 책 표현과 다르다. SRE 3장의 "한 자릿수"(order of magnitude)는 비용이 아니라 비가용성이 10분의 1로 준다는 뜻이다. 비용은 SRE 3장 「Managing Risk」 절이 "신뢰성을 한 단계 올리는 데 앞 단계보다 100배가 들 수도 있다"(may cost 100x more than the previous increment)고 쓴다 — 고정 배수가 아니라 "선형으로 늘지 않는다"는 경험적 말이다(<https://sre.google/sre-book/embracing-risk/>).

### 4. MTTF·MTBF·MTTR — 가용성을 두 손잡이로 나누기

```text
 시간 ─▶  [── 가동 ──][고장][────── 가동 ──────][고장][── 가동 ──] …
           ←─ TTF ─→ ←TTR→ ←────── TTF ──────→ ←TTR→
           ←────── 한 주기(TBF) ──────→
```

- *MTTF(Mean Time To Failure)*: 고장 나기까지 평균 가동 시간.
- *MTTR(Mean Time To Repair/Recover)*: 고장에서 복구까지 평균 시간.
- *MTBF(Mean Time Between Failures)*: 고장과 고장 사이 평균 시간. 수리되는 시스템에서는 MTBF = MTTF + MTTR로 쓰는 관례가 있고, 문헌에 따라 MTTF와 같은 뜻으로 쓰기도 한다. 식을 볼 때 어느 쪽인지 확인한다.
- SRE의 시간 기반 식에 한 주기를 넣으면 **가용성 = MTTF / (MTTF + MTTR)**이 된다.
  - MTTF 999시간·MTTR 1시간 → 99.9%. MTTF 499.5시간·MTTR 0.5시간 → 같은 99.9%(아래 실험의 공식 출력).
  - 즉 **고장을 반으로 줄이는 것과 복구를 두 배 빠르게 하는 것은 가용성에서 같은 값**이다. 사용자 경험(끊김 횟수)은 다르다.

### 5. 합성 — 신뢰도 블록 다이어그램(RBD)

*신뢰도 블록 다이어그램(Reliability Block Diagram)*: "전체가 동작하려면 어떤 부품 조합이 살아 있어야 하나"를 직렬·병렬 블록으로 그린 그림.

```text
 직렬(전부 필요)                     병렬(하나만 살면 됨)
 ──[A]──[B]──[C]──                  ┌─[A]─┐
 A_total = A·B·C                   ─┤     ├─      A_total = 1 − (1−A)(1−B)
                                    └─[B]─┘

 예: LB 2대(각 99.9%, 병렬) → 앱 3대(각 99%, 병렬) → DB 1대(99.95%)
 ──┬─[LB]─┬──┬─[앱]─┬──[DB]──
   └─[LB]─┘  ├─[앱]─┤
             └─[앱]─┘
 = (1−0.001²) × (1−0.01³) × 0.9995 ≈ 99.9498%   ← 병렬 블록이 아무리 좋아도 직렬의 가장 약한 칸(DB)이 상한
```

- 직렬은 곱이라 **떨어지고**, 병렬은 실패 확률의 곱이라 **오른다**.
- 두 식 모두 **부품이 독립적으로 고장 난다**는 가정 위에 있다. 같은 전원·같은 랙·같은 배포·같은 설정을 공유하면 독립이 아니다.
  - *공통 원인 고장(common-mode failure)*: 같은 원인에서 나온 비슷한 오류로 여러 부품이 함께 고장 나는 것. 논문 3.5절은 "비슷한 오류가 일으킨 고장"이라고 정의한다. 이때 병렬 식은 실제보다 훨씬 낙관적이다.

### 실험: 공식 vs 몬테카를로, 그리고 공통 원인

- 부품마다 가동 시간·수리 시간을 지수 분포로 뽑아 1분 단위 up/down 비트열을 만든다(200년치). 직렬은 AND, 병렬은 OR.
- 공통 원인은 "둘을 동시에 쓰러뜨리는 사건"을 별도 타임라인(MTTF 990h·MTTR 1h)으로 두고 병렬 결과에 AND 한다.

```java
// 핵심 부분 (전체: scratchpad/rel/01/e01/Avail.java)
static double serial(double... a)   { double r = 1; for (double x : a) r *= x; return r; }
static double parallel(double... a) { double q = 1; for (double x : a) q *= (1 - x); return 1 - q; }
...
parInd[m]    = a[m] || b[m];                 // 독립 이중화
parCommon[m] = (a[m] || b[m]) && common[m];  // 공통 원인이 둘을 함께 쓰러뜨림
```

(실험, JDK 21 eclipse-temurin, `--cpus=2`, seed 고정, 2026-10-01)

```text
== 1. 공식
직렬 99.9% x5           = 99.5010%
직렬 99.9% x10          = 99.0045%
병렬 99% x2             = 99.9900%
병렬 99% x3             = 99.999900%
RBD [LB 2]→[앱 3]→[DB 1] = 99.9498%  (DB 단독 99.95%가 상한을 정한다)
MTTF 999h, MTTR 1h      = 99.9000%
MTTF 499.5h, MTTR 0.5h  = 99.9000%  (고장 2배 잦고 수리 2배 빠름 → 같은 가용성)
== 2. 시뮬레이션 (200년치, 1분 샘플, 부품 MTTF 999h·MTTR 1h)
부품 하나 실측           = 99.8978%
직렬 5개 실측            = 99.4957%
부품(MTTF 99h,MTTR 1h)   = 99.0019%
병렬 2대 독립 실측        = 99.9903%  (공식 99.9900%)
병렬 2대 + 공통원인 실측  = 99.8856%  (공통원인 단독 99.8953%)
```

- 관찰 1: 99.9% 부품 5개 직렬은 공식 99.5010%, 시뮬레이션 99.4957%. 월 허용 중단이 43.2분에서 약 3.6시간으로 늘어난 셈이다(SRE 부록 A의 99.5% 칸).
- 관찰 2: 독립 이중화는 공식(99.99%)대로 올랐다.
- 관찰 3: 공통 원인이 섞이자 이중화 결과(99.8856%)는 **공통 원인 하나의 가용성(99.8953%) 아래**로 떨어졌다. 99% 부품 둘을 병렬로 둔 효과가 공통 원인의 상한에 막혔다.
- 시뮬레이션 수치는 seed에 따라 달라진다(위 출력은 seed 42). seed 1~5로 다시 돌리면 직렬 5개 99.494~99.504%, 병렬 독립 99.989~99.990%, 병렬+공통원인 99.886~99.893%(공통원인 단독 99.896~99.903%)였다. 공식과의 차이는 표본 오차이고, 공통 원인을 넣은 결과가 공통 원인 단독 아래라는 관계는 다섯 번 모두 같았다.

## 쓰이는 자료구조·알고리즘

- **직렬·병렬 합성 트리** — RBD는 직렬 노드(곱)와 병렬 노드(1−실패곱)로 된 트리다. 재귀로 계산한다. 다리가 엇갈린 그림(bridge)은 트리로 안 풀려 경우의 수를 나눠 계산한다.
- **k-of-n 블록** — "n대 중 k대 이상 살아야 함"(쿼럼·용량). 이항 분포 합 Σ C(n,i)·Aⁱ·(1−A)ⁿ⁻ⁱ (i ≥ k). 쿼럼은 [distributed/09-quorums](../../distributed/09-quorums/2-summary.md).
- **몬테카를로 시뮬레이션** — 확률 분포에서 사건을 뽑아 평균을 낸다. 독립 가정이 깨지는 경우(공통 원인)를 식보다 쉽게 넣을 수 있다.
- **지수 분포** — "고장률이 일정하다"는 가정의 분포. 평균만 맞으면 되는 가용성 계산에는 충분하지만, 실제 고장은 몰려 오기도 한다(배포 직후·노후).
- **비트열 AND/OR** — 분 단위 up/down을 비트로 두면 직렬=AND, 병렬=OR로 합성된다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 요청 경로 하나를 고르고 **동기 의존성**을 끝까지 나열한다(DNS·LB·게이트웨이·서비스·DB·캐시·외부 API·인증).
2. RBD로 그린다. "이것 하나가 죽으면 이 요청이 실패하나?"가 예면 직렬, 대체가 있으면 병렬.
3. 각 블록에 **측정한** 가용성을 넣는다. 제공사 SLA는 하한 약속이지 측정치가 아니다.
4. 계산한 값이 약속하려는 숫자보다 낮으면, 가장 약한 직렬 칸부터 손본다: 이중화, 비동기화(직렬에서 빼기), 폴백(실패해도 요청은 성공).
5. 이중화 칸마다 공통 원인을 묻는다: 같은 AZ? 같은 배포 파이프라인? 같은 설정 저장소? 같은 인증서 만료일?
6. 고객 약속(SLA)은 내부 목표(SLO, [02](../02-slo-sli-error-budget/2-summary.md))보다 느슨하게 둔다.

### 2. 계산기 (Java)

```java
/** RBD 노드: 직렬·병렬·단일 블록. 독립 고장 가정. (모두 class Rbd 안에 둔다 — JDK 21 패턴 매칭 switch) */
sealed interface Block permits Unit, Serial, Parallel {}
record Unit(String name, double a) implements Block {}
record Serial(List<Block> parts) implements Block {}
record Parallel(List<Block> parts) implements Block {}

static double availability(Block b) {
    return switch (b) {
        case Unit u -> u.a();
        case Serial s -> s.parts().stream().mapToDouble(Rbd::availability).reduce(1, (x, y) -> x * y);
        case Parallel p -> 1 - p.parts().stream().mapToDouble(x -> 1 - availability(x)).reduce(1, (x, y) -> x * y);
    };
}
// availability(new Serial(List.of(new Parallel(List.of(lb, lb)), new Parallel(List.of(app, app, app)), db)))
```

### 3. 실제 값을 재는 법

- 요청 기반 가용성(Prometheus, 카운터 `http_server_requests_seconds_count`에 `status` 라벨이 있다고 가정한 예):

```promql
# 30일 요청 기반 가용성 = 5xx가 아닌 요청 / 전체 요청
sum(increase(http_server_requests_seconds_count{job="order", status!~"5.."}[30d]))
/
sum(increase(http_server_requests_seconds_count{job="order"}[30d]))
```

- MTTR은 사고 기록(영향 시작 시각 → 복구 시각)에서 뽑는다. 탐지 시각부터 재면 탐지 전 중단이 빠져 가용성 식에 넣을 값보다 작아진다. 시작 → 탐지 구간은 *MTTD*(Mean Time To Detect, 탐지까지 평균 시간)로 따로 보고, AWS 가용성 백서는 이를 MTTR 안의 한 구간으로 둔다(<https://docs.aws.amazon.com/whitepapers/latest/availability-and-beyond-improving-resilience/understanding-availability.html>). 평균만 보지 말고 분포(중앙값·최댓값)를 같이 본다. 사고 몇 건의 평균은 한 건에 크게 흔들린다.
- 외부 의존성은 호출 쪽에서 잰다(내 클라이언트가 본 성공률). 상대가 발표한 숫자와 다를 수 있다.

## 장애 시나리오와 대처

### 1. 99.9% 서비스 5개 직렬인데 99.9% SLA를 약속 (⚠ 커리큘럼)

- 현상: 모든 팀이 자기 서비스 목표(99.9%)를 지켰는데, 분기 말 고객 SLA 위반 보상이 나간다.
- 보이는 형태: 각 서비스 대시보드는 초록. 게이트웨이에서 잰 종단 성공률은 99.5% 근처. 시간 기반으로 환산하면(전면 중단·고른 요청량을 가정할 때) 월 중단 합이 43분이 아니라 3시간대.
- 원인: 직렬 합성. 0.999⁵ = 0.99501(실험의 공식 출력, 시뮬레이션 99.4957%). 약속은 부품이 아니라 경로 전체에 걸렸다.
- 대처: RBD로 종단 가용성을 계산해 약속을 그 아래로 잡는다. 종단 SLI를 게이트웨이에서 잰다(게이트웨이 앞 DNS·LB에서 난 실패는 게이트웨이가 못 보므로 LB 지표·클라이언트 쪽 측정·합성 프로브로 따로 본다). 직렬 칸을 줄인다(비동기화·캐시 폴백). 부품 목표를 종단 목표보다 높게 잡는다.

### 2. 이중화했는데 둘이 같이 죽었다

- 현상: "Active-Active 2대인데 왜 전면 장애인가".
- 보이는 형태: 두 인스턴스의 에러 시작 시각이 같다. 같은 배포 버전·같은 설정 변경·같은 인증서 만료·같은 AZ 정전과 시각이 겹친다.
- 원인: 공통 원인 고장. 병렬 식의 독립 가정이 깨졌다. 실험 관찰 3에서 이중화 결과가 공통 원인의 가용성 아래로 내려갔다.
- 대처: 공통 원인을 목록으로 만들어 하나씩 떼어 놓는다(다른 AZ, 배포를 순차로, 설정 변경도 단계적으로). 계산할 때는 공통 원인을 별도 직렬 블록으로 넣는다.

### 3. 가용성 지표는 99.99%인데 사용자는 "자주 안 된다"고 한다

- 현상: 시간 기반 지표가 높은데 고객 문의가 많다.
- 보이는 형태: 헬스체크 기반 업타임은 100%에 가깝다. 특정 지역·특정 API·특정 고객만 실패한다.
- 원인: 시간 기반 가용성은 "부분 장애"를 못 본다. 일부 사용자에게만 고장인 inconsistent 고장, 또는 헬스체크가 실제 경로를 타지 않는다.
- 대처: 요청 기반 SLI로 바꾼다(SRE 3장). 핵심 경로별·고객군별로 나눠 잰다. 헬스체크 대신 실제 요청 결과를 센다.

### 4. 오류가 쌓이는데 고장으로 안 잡힌다

- 현상: 몇 주 뒤에 정산이 안 맞아 발견한다.
- 보이는 형태: 에러율 0, 경보 없음. 데이터 대조에서만 차이가 보인다.
- 원인: 오류(error)가 탐지되지 않은 채 쌓이거나(잠재 오류 latent error — 논문 3.4절 "있지만 탐지되지 않은 오류"), 고장이 신호 없이(unsignaled) 나갔다.
- 대처: 상태를 검사하는 장치를 둔다(대조 배치, 불변식 검사, 체크섬). "에러가 없다"를 "틀리지 않았다"로 읽지 않는다. 카탈로그 F-25.

### 5. 고장 줄이기에만 투자해서 가용성이 안 오른다

- 현상: 1년간 안정화 작업을 했는데 가용성 숫자는 그대로다.
- 보이는 형태: 사고 수는 줄었지만 사고당 복구 시간이 길다(탐지 늦음·롤백 수동).
- 원인: 가용성 = MTTF/(MTTF+MTTR). MTTR을 그대로 두면 MTTF만으로는 느리게 오른다.
- 대처: 탐지(SLO 경보, [02](../02-slo-sli-error-budget/2-summary.md))와 복구(자동 롤백, 런북)를 같이 줄인다. 계산: MTTF 999h·MTTR 0.5h와 MTTF 1998h·MTTR 1h는 둘 다 99.95%다 — MTTR을 반으로 줄인 것과 MTTF를 두 배로 늘린 것이 같다.

## 핵심 문장

- 결함은 원인, 오류는 고장으로 이어질 수 있는 내부 상태, 고장은 사용자가 보는 이탈이다. 아래 부품의 고장은 위 시스템의 결함이다.
- 가용성은 시간 기반(가동/전체)과 요청 기반(성공/전체)으로 잰다. 부분 장애는 요청 기반이 잡는다.
- 가용성 = MTTF/(MTTF+MTTR). 복구를 두 배 빠르게 하는 것은 고장을 반으로 줄이는 것과 가용성에서 같다.
- 직렬은 곱해서 떨어진다. 99.9% 다섯 개 직렬은 99.5%다(실험: 공식 99.5010%, 시뮬레이션 99.4957%).
- 병렬 식은 독립 고장 가정이다. 공통 원인이 있으면 이중화 결과는 그 공통 원인의 가용성을 넘지 못한다.

## 관련 주제·근거

- 선행
  - [distributed/02-system-and-failure-models](../../distributed/02-system-and-failure-models/2-summary.md) — 고장 가정(crash-stop·비잔틴), 느림과 죽음의 구분
  - 원본 [systems/server-design/05-ha-topology.md](../../systems/server-design/05-ha-topology.md) §1(가용성 표·합성), §2(이중화), §3(split-brain)
- 후속
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — 가용성 목표를 SLO·에러 버짓으로 운영
  - [03-failure-at-scale](../03-failure-at-scale/2-summary.md) — 규모가 커질 때 고장의 모양이 바뀐다
  - [04-failure-modes-catalog](../04-failure-modes-catalog/2-summary.md) — 신호 없는 고장(F-25) 등 실패 목록
  - [25-high-availability-topology](../25-high-availability-topology/2-summary.md), [46-disaster-recovery](../46-disaster-recovery/2-summary.md)
  - [distributed/09-quorums](../../distributed/09-quorums/2-summary.md) — k-of-n
- 논문·책
  - Avižienis, Laprie, Randell, Landwehr, "Basic Concepts and Taxonomy of Dependable and Secure Computing", IEEE TDSC 1(1), 2004 — 2.2 failure·error·fault 정의, 2.3 availability·reliability, 2.4 네 가지 수단, 3.3.1 고장 모드, 3.5 fault-error-failure 사슬. 열람본: <https://drum.lib.umd.edu/bitstream/1903/6459/1/TR_2004-47.pdf>
  - Google 『Site Reliability Engineering』 3장 "Embracing Risk"(시간 기반·요청 기반 가용성 식, 9의 개수) <https://sre.google/sre-book/embracing-risk/>, 부록 A "Availability Table" <https://sre.google/sre-book/availability-table/>
  - Treynor 외 "The Calculus of Service Availability", ACM Queue 2017 — 의존성 가용성 계산("extra 9" 규칙). 원문 접근이 막혀 내용을 확인하지 못했다 `[?]`
- 실험 목록
  - e01 가용성 합성: 공식(직렬·병렬·RBD·MTTF/MTTR) vs 몬테카를로 200년치, 공통 원인 고장 — JDK 21 eclipse-temurin 컨테이너, `--cpus=2`, 코드 `scratchpad/rel/01/e01/Avail.java`
