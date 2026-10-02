# reliability/20-performance-method-and-amdahl — 성능 작업 방법론·Amdahl의 법칙·병목 이동 — 정리 (힌트)

## 해결하는 문제

성능 문제를 받으면 손이 먼저 가는 곳이 있다. 익숙한 도구, 인터넷에서 본 JVM 플래그, 의심 가는 코드다.\
그렇게 고치면 (1) 병목이 아닌 곳을 고치느라 시간을 쓰고, (2) 여러 개를 한꺼번에 바꿔서 무엇이 효과였는지 모르게 된다.

```text
 안티 방법론                          방법론
 감으로 고른 곳을 고친다                측정 → 병목 특정 → 한 가지만 바꾼다 → 재측정
 플래그 5개를 한 번에 바꾼다            바꾼 것 1개 ↔ 효과 1개가 대응
 "좀 빨라진 것 같다"                    같은 조건 재측정, 실행 간 잡음보다 큰가 확인
```

- *병목(bottleneck)*: 전체 처리 속도를 제한하는 가장 좁은 자원·구간. 병원 접수 창구가 1개면 의사가 10명이어도 시간당 환자 수는 창구가 정한다.
- *Amdahl의 법칙*: 일부만 빨라질 때 전체가 얼마나 빨라지는지의 상한을 주는 식.

쉬운 예: 출근 시간 60분 중 엘리베이터 대기가 3분(5%)이다.
- 엘리베이터를 2배 빠르게 해도 1.5분만 준다. 전체는 2.5% 짧아질 뿐이다.
- 지하철 구간 50분을 줄이는 쪽이 효과가 크다. 먼저 "어디에 시간이 쓰이나"를 재야 그것을 안다.

똑같은 구조다.\
실무 예: API 응답 시간 중 DB 대기가 80%인데 JSON 직렬화 최적화부터 하는 것, GC 플래그·스레드 수·커넥션 풀 크기를 한 번에 바꾸고 "좋아졌다"고 배포하는 것.\
원칙 한 줄 버전은 원본 [engineering-axes/performance.md](../../engineering/engineering-axes/performance.md) 「대원칙 ②·③」에 있다. 이 노트는 그 절차와 수식, 실측을 다룬다.

## 동작·원리

### 1. 작업 순서 — 한 바퀴

```text
 ① 문제 정의 ──> ② 측정(기준선) ──> ③ 병목 특정 ──> ④ 가설 하나 + 변경 하나
       ^                                                        │
       └──────── ⑥ 기록, 병목이 옮겨 갔으면 다시 ③ <── ⑤ 같은 조건 재측정
```

- ① 문제 정의: Gregg의 Problem Statement Method 질문들 — 성능 문제라고 보는 근거는? 이 시스템이 잘 돌던 적이 있나? 최근 무엇이 바뀌었나(소프트웨어·하드웨어·부하)? 지연이나 실행 시간으로 표현할 수 있나? 다른 사용자·앱도 겪나? 환경·버전·설정은?
- ② 측정: 지연 분포와 처리량을 제대로 잰다(→ [19-performance-measurement](../19-performance-measurement/2-summary.md)).
- ③ 병목 특정: 자원마다 사용률·포화·에러를 본다(USE 방법 — 다음 절). 코드 안이면 프로파일러(→ [36-profiling](../36-profiling/2-summary.md)).
- ④ 한 가지만 바꾼다: Gregg의 Scientific Method(질문 → 가설 → 예측 → 시험 → 분석). 예측을 먼저 적어 둔다.
- ⑤ 재측정: ②와 같은 조건. 차이가 실행 간 잡음보다 커야 효과다(아래 실험의 5% 구간 사례).

### 2. 병목 탐색 순서 — USE 체크리스트

```text
 자원(CPU·메모리·디스크·네트워크·커넥션 풀·스레드 풀·락)마다
   U 사용률(utilization)  얼마나 바빴나        예: CPU 95%
   S 포화(saturation)     줄 선 일이 있나      예: run queue 길이, 풀 대기 스레드 수
   E 에러(errors)         실패가 있나          예: 재전송, 풀 획득 타임아웃
```

- USE 방법(Gregg): 모든 자원에 대해 세 가지를 확인한다. 포화(대기열)가 병목의 가장 직접적인 신호다. OS 도구 대응은 [os/31-os-observability-tools](../../os/31-os-observability-tools/2-summary.md) 「USE 방법론」.
- 소프트웨어 자원(커넥션 풀·스레드 풀·세마포어)도 자원이다. 아래 병목 이동 실험의 병목은 CPU가 아니라 커넥션 4개짜리 풀이었다.

### 3. Amdahl의 법칙

```text
 전체 시간 = 1 (정규화)
 ┌────────── 개선 안 되는 부분 (1 - p) ──────────┬── 개선되는 부분 p ──┐
 개선 후:
 ┌────────── (1 - p) 그대로 ─────────────────────┬ p / s ┐

 속도향상 = 1 / ((1 - p) + p / s)        s → ∞ 이어도 상한 = 1 / (1 - p)
```

- p: 개선 대상이 전체에서 차지하는 비율. s: 그 부분을 몇 배 빠르게 했나.
- 병렬화에 쓰면 p = 병렬 가능 비율, s = 프로세서 수 N. 직렬 부분이 10%면 N을 무한히 늘려도 10배가 상한이다.
- 커리큘럼의 예: 전체의 5%인 구간을 2배 빠르게 하면 1 / (0.95 + 0.025) ≈ 1.026배. 실행 시간으로는 2.5% 줄어든다. 95% 구간을 2배 빠르게 하면 1 / (0.05 + 0.475) ≈ 1.9배, 47.5% 줄어든다.
- 출처: Amdahl, "Validity of the single processor approach to achieving large scale computing capabilities", AFIPS SJCC 1967. 원문은 직렬로 남는 "데이터 관리(housekeeping)" 부담이 병렬 처리의 이득을 제한한다는 산문 논증이다. 지금 쓰는 식은 그 논증을 후대에 식으로 정리한 것이다 [?] — 원문 PDF를 열지 못해 "원문에 식이 없다"는 점은 2차 출처로만 확인했다.
- 한계: 직렬 부분 외에 참여자 **쌍마다** 생기는 **조율 비용**(캐시 일관성·노드 간 동기화)이 있으면 N이 커질 때 오히려 느려질 수 있다. 그것은 USL이 다룬다. USL에서 락 경합 같은 줄서기는 α(포화의 원인), 역행은 β(일관성 비용)로 나뉜다(→ [21-scaling-principles](../21-scaling-principles/2-summary.md)).

### 실험 1: Amdahl 예측 vs 실측 (코어 2개)

- CPU만 쓰는 일(64비트 곱셈·덧셈 반복)을 직렬 비율 s만큼 한 스레드로, 나머지를 P개 스레드로 나눠 실행한다. 7회 중앙값.

```java
static double run(double s, int p, long total) throws Exception {
    long serial = Math.round(total * s), par = total - serial;
    ExecutorService ex = Executors.newFixedThreadPool(p);
    long t0 = System.nanoTime();
    sink = work(serial);                                   // 직렬 부분
    List<Future<Long>> fs = new ArrayList<>();
    for (int i = 0; i < p; i++) { long u = par / p; fs.add(ex.submit(() -> work(u))); }
    for (Future<Long> f : fs) sink ^= f.get();             // 병렬 부분
    double ms = (System.nanoTime() - t0) / 1e6;
    ex.shutdown();
    return ms;
}
```

(실험, Docker eclipse-temurin:21-jdk(Temurin 21.0.12) `--cpus=2 --cpuset-cpus=6,7`, 호스트 24코어·다른 작업으로 부하 평균 약 14, 2026-10-01 — 2회 실행)

```text
availableProcessors=2
직렬비율 s=0.0  P=1:    524ms  P=2:    271ms  실측 속도향상 1.93배  Amdahl 예측 2.00배
직렬비율 s=0.1  P=1:    554ms  P=2:    295ms  실측 속도향상 1.88배  Amdahl 예측 1.82배
직렬비율 s=0.5  P=1:    518ms  P=2:    383ms  실측 속도향상 1.35배  Amdahl 예측 1.33배
```

두 번째 실행: 1.95배 / 1.81배 / 1.42배(예측 2.00 / 1.82 / 1.33).

- 관찰: 직렬 비율이 0.5면 코어를 2배로 해도 약 1.3~1.4배에 그친다. (사실 점검 재실행 2회: 2.04·1.80·1.32배 / 1.94·1.74·1.34배.) 예측과 실측의 차이는 실행마다 ±0.1배 안팎이었다.
- 참고: 코어를 고정(`--cpuset-cpus`)하기 전, `--cpus=2`만 준 첫 시도에서는 s=0일 때 1.54배밖에 안 나왔다. CPU 할당량 제한에서 다른 스레드(JIT·GC)와 시간을 나눠 쓴 영향으로 보인다(해석). 측정 환경 자체가 결과를 바꾼다는 예다.

### 실험 2: 5% 구간을 2배 vs 95% 구간을 2배

- 같은 프로그램 안에서 일 1900단위(95%) + 100단위(5%)를 기준으로, 5% 쪽만 절반(50)으로 줄인 경우와 95% 쪽만 절반(950)으로 줄인 경우를 11회씩 재 중앙값을 비교한다.

(실험, 같은 환경, 3회 실행)

```text
기준(95%+5%)            257ms
5% 구간만 2배 빠르게      269ms  (-4.8% 단축, 예측 2.5%)
95% 구간만 2배 빠르게     141ms  (45.2% 단축, 예측 47.5%)
기준(95%+5%)            260ms
5% 구간만 2배 빠르게      254ms  (2.4% 단축, 예측 2.5%)
95% 구간만 2배 빠르게     138ms  (46.9% 단축, 예측 47.5%)
기준(95%+5%)            268ms
5% 구간만 2배 빠르게      265ms  (1.3% 단축, 예측 2.5%)
95% 구간만 2배 빠르게     143ms  (46.6% 단축, 예측 47.5%)
```

- 관찰 1: 95% 구간 개선은 세 번 모두 45~47% 단축으로 예측(47.5%)에 가깝다.
- 관찰 2: 5% 구간 개선은 −4.8% ~ +2.4%로 흩어졌다. 반복 횟수 5회짜리 이전 실행 두 번에서도 −3.7%, +4.7%였다. 사실 점검 재실행 2회(같은 설정)에서는 +1.6%, +1.4%였다. **예측 효과(2.5%)가 이 환경의 실행 간 잡음보다 작다.**
- 해석: 작은 구간을 고치면 이득이 작을 뿐 아니라 **측정으로 확인하기도 어렵다.** "좋아졌다"는 보고가 잡음일 수 있다.

### 4. 병목 이동

```text
 요청 = 앱 처리 5ms(워커 점유) → DB 호출 10ms(커넥션 4개 풀)
 워커 수 W를 늘리면
   W 작음:  병목 = 워커       처리량 ≈ W / 15ms
   W 큼:    병목 = DB 풀      처리량 ≈ 4 / 10ms = 400건/s 에서 멈춤, 늘린 워커는 풀 앞에서 줄 선다
```

- 한 병목을 풀면 다음으로 좁은 곳이 병목이 된다. 그래서 ⑤ 재측정 뒤 ③으로 돌아간다.
- *Little's Law*: 시스템 안의 평균 건수 = 도착률 × 평균 체류 시간(L = λW). 처리량이 고정된 상태에서 동시 요청(워커)을 늘리면 늘어난 만큼 체류 시간이 길어진다(→ [21-scaling-principles](../21-scaling-principles/2-summary.md)).

### 실험 3: 워커를 늘려도 처리량이 멈추는 지점

```java
Thread.sleep(5);                                  // 앱 처리
long w0 = System.nanoTime();
db.acquire();                                     // 커넥션 4개짜리 세마포어
waitNs.addAndGet(System.nanoTime() - w0);
try { Thread.sleep(10); } finally { db.release(); }
```

(실험, 같은 컨테이너 설정에서 `--cpus=2`만, 워커 수마다 3초)

```text
워커  2: 처리량  131건/s  요청당 평균  15.3ms (그중 DB 풀 대기   0.0ms)
워커  4: 처리량  263건/s  요청당 평균  15.2ms (그중 DB 풀 대기   0.0ms)
워커  8: 처리량  394건/s  요청당 평균  20.4ms (그중 DB 풀 대기   5.1ms)
워커 16: 처리량  396건/s  요청당 평균  40.6ms (그중 DB 풀 대기  25.4ms)
워커 32: 처리량  403건/s  요청당 평균  80.4ms (그중 DB 풀 대기  65.2ms)
```

- 관찰: 워커 8부터 처리량이 약 400건/s(= 4 / 10ms)에서 멈췄다. 그 뒤로 워커를 늘린 만큼 **DB 풀 대기만 늘었다**(16 → 25ms, 32 → 65ms).
- Little's Law로 확인: 워커 32, 처리량 403건/s → 체류 시간 ≈ 32 / 403 ≈ 79ms. 실측 평균 80.4ms와 맞다.
- 이 상태에서 "CPU를 더 주자", "워커를 더 늘리자"는 효과가 없다. 병목은 풀 크기(또는 DB 처리 시간)다. 반대로 DB 풀을 키우면 병목이 DB 서버 자원으로 옮겨 간다.

### 5. 안티 방법론 — 이름을 알면 피하기 쉽다

Gregg의 methodology 페이지(brendangregg.com/methodology.html)가 이름 붙인 것들이다.

| 이름 | 하는 일 | 왜 문제인가 |
|---|---|---|
| Streetlight(가로등 효과) | 익숙한 도구·인터넷에서 본 도구·아무 도구를 돌려 눈에 띄는 것만 본다 | 밝은 곳만 찾는다. 도구가 못 보는 자원은 영영 안 본다 |
| Drunk Man | 문제가 사라질 때까지 무작위로 바꾼다 | 원인을 모른 채 끝난다 |
| Random Change | 기준선 측정 → 무작위 설정 하나를 위·아래로 바꿔 측정 → 좋으면 유지 → 반복 | 측정은 하지만 가설이 없다. 잡음을 효과로 착각하고, 상호작용을 놓친다 |
| Blame-Someone-Else | 내 책임이 아닌 구성 요소를 의심해 다른 팀에 넘긴다 | 틀리면 다시 1번 |
| Passive Benchmarking | 도구를 여러 옵션으로 돌리고 결과 슬라이드를 만든다 | 무엇이 결과를 제한했는지(병목) 분석하지 않는다 |
| Traffic Light | 대시보드가 다 초록이면 괜찮다고 가정 | 문턱이 틀리면 놓친다 |

## 쓰이는 자료구조·알고리즘

- **Amdahl 식**: `1 / ((1 − p) + p / s)`. 상한 `1 / (1 − p)`. 어디부터 고칠지 고를 때 "이 구간을 0으로 만들면 최대 얼마"를 먼저 계산한다.
- **USE 체크리스트**: 자원 목록 × (U, S, E) 표. 표를 채워 가는 탐색이 곧 병목 탐색 순서다.
- **드릴다운(drill-down)**: 위 단계(서비스 전체 지연)에서 가장 큰 구간을 골라 한 단계씩 내려간다. 트레이스 스팬 트리(→ [17-distributed-tracing](../17-distributed-tracing/2-summary.md))가 그 구조다.
- **대기열 모델(Little's Law)**: L = λW. 처리량·동시성·체류 시간 중 둘을 알면 셋째를 얻는다. 실험 3의 검산에 썼다.
- **이분 탐색(bisect)**: 회귀가 언제 들어왔는지 모를 때 변경 이력을 반씩 잘라 재측정한다(`git bisect`). "한 번에 하나만 바꾸기"가 지켜졌을 때만 쓸 수 있다.

## 적용 — 풀어나가는 법

### 1. 작업 기록 양식

```text
문제:      주문 API p99 1.2s (SLO 400ms), 2026-09-28 배포 이후
기준선:    k6 open 200 rps, 10분, p50 80ms / p99 1.2s / 오류 0.1%  (환경: …)
USE 결과:  CPU 40%, DB 풀 활성 20/20 + 대기 스레드 35 (포화), GC 멈춤 p99 15ms
가설:      DB 풀 포화가 p99를 만든다. 풀 대기 시간 ≈ p99 - p50
예측:      느린 쿼리 X(전체 DB 시간의 70%)를 인덱스로 5배 빠르게 → DB 시간 56% 감소
변경 1개:  인덱스 추가(그 외 동일)
재측정:    같은 조건 3회 — p99 범위 …, 기준선 범위 …
다음 병목: …
```

- 수치는 예시다. 핵심은 **바꾼 것 1개**와 **예측**을 측정 전에 적는 것이다.

### 2. 진단 명령 (병목 위치 찾기)

```bash
# 시스템 자원 USE — 60초 체크리스트의 일부(os/31 참고)
vmstat 1          # r(실행 중 + 실행 대기)이 CPU 수보다 크면 CPU 포화, si/so = 스왑
iostat -xz 1      # %util, aqu-sz(대기열) = 디스크 포화
pidstat -t -p <pid> 1
# JVM 안 — 스레드가 어디서 기다리나
jcmd <pid> Thread.print | grep -A3 'WAITING\|BLOCKED' | head
```

```promql
# HikariCP 풀 포화(Micrometer 지표 예): 대기 스레드 수, 획득 시간 p99
hikaricp_connections_pending
histogram_quantile(0.99, sum by (le) (rate(hikaricp_connections_acquire_seconds_bucket[5m])))
```

- 위 HikariCP 지표 이름은 Micrometer 연동 기준의 예다. 히스토그램 버킷 노출 여부는 설정에 따른다 [?].
- 풀 크기와 타임아웃의 기초는 [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md).

### 3. 어디부터 고칠지 — Amdahl로 순위 매기기

```java
// 구간별 시간 비율 p와 기대 배율 s로 "전체 단축률"을 계산해 큰 순서로
record Stage(String name, double p, double s) {
    double saving() { return 1 - ((1 - p) + p / s); }       // 전체 시간 단축 비율
}
List<Stage> stages = List.of(new Stage("DB 쿼리", 0.70, 5), new Stage("JSON 직렬화", 0.05, 3),
                             new Stage("외부 API", 0.20, 1.5));
stages.stream().sorted(Comparator.comparingDouble(Stage::saving).reversed())
      .forEach(st -> System.out.printf("%s: 전체 %.1f%% 단축%n", st.name(), st.saving() * 100));
// DB 쿼리: 56.0%, 외부 API: 6.7%, JSON 직렬화: 3.3%  (예시 수치)
```

### 4. 설정 변경 규칙

- JVM·커널 플래그는 **한 번에 하나**. 커밋·배포 단위도 하나.
- 변경마다 "되돌리는 방법"을 함께 적는다. 회귀가 나면 하나씩 되돌려 원인을 찾을 수 있다.
- 효과가 실행 간 잡음 범위 안이면 "효과 없음"으로 기록하고 되돌린다. 복잡도만 늘리지 않는다.

## 장애 시나리오와 대처

### 1. 전체의 5%인 구간을 최적화하고 "빨라졌다"

- 현상: 직렬화 라이브러리를 바꿔 그 구간이 2배 빨라졌다. 대시보드 p99는 그대로다.
- 보이는 형태: 마이크로벤치마크로는 2배, 서비스 지연은 변화 없음 또는 잡음 수준.
- 원인: Amdahl — 그 구간이 5%면 전체는 약 2.5% 줄어든다. 실험 2에서 이 크기의 효과는 실행 간 잡음(±5%)에 묻혔다.
- 대처: 착수 전에 구간별 비율을 재고 "최대 단축률"을 계산한다. 가장 큰 구간부터 고친다.

### 2. JVM·커널 플래그를 여러 개 한꺼번에 바꿈

- 현상: GC 알고리즘·힙 크기·스레드 수·`net.core.somaxconn`을 한 배포에서 바꿨다. 일주일 뒤 p99 회귀가 났는데 무엇 때문인지 모른다.
- 보이는 형태: 변경 기록이 "튜닝" 한 줄. 되돌리려면 전부 되돌려야 한다. 회귀를 다른 환경에서 재현하지 못한다.
- 원인: 변경과 효과의 대응이 깨졌다. 두 변경이 서로 상쇄하거나 상호작용했을 수도 있다.
- 대처: 하나씩 다시 적용하며 재측정한다(또는 bisect). 앞으로는 변경 1개 = 측정 1회 = 기록 1줄.

### 3. 워커·스레드를 늘렸는데 처리량은 그대로, 지연만 증가

- 현상: 톰캣 스레드를 200 → 400으로 올렸다. 처리량은 같고 p99는 2배가 됐다.
- 보이는 형태: 실험 3처럼 처리량 고정, 커넥션 풀 대기 시간 증가, 풀 활성 수 = 최대치.
- 원인: 병목이 하류 풀(또는 DB)로 옮겨 갔다. 늘린 스레드는 그 앞에서 줄을 선다(Little's Law).
- 대처: USE로 포화된 자원을 찾는다. 그 자원의 처리 시간을 줄이거나 용량을 늘린다. 위쪽 동시성은 하류 용량에 맞춰 제한한다(→ [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md), [28-bulkhead](../28-bulkhead/2-summary.md)).

### 4. 가로등 효과 — 익숙한 도구로만 봄

- 현상: `top`에 CPU가 30%라 "서버는 여유 있다"고 결론. 지연 원인은 디스크 대기열이었다.
- 보이는 형태: CPU 그래프만 있는 대시보드. `iostat`의 대기열·`vmstat`의 `b`(블록된 프로세스)는 아무도 안 봤다.
- 원인: 도구가 보여 주는 자원만 봤다(Streetlight Anti-Method).
- 대처: 도구가 아니라 **자원 목록**에서 출발한다(USE). 목록에 있는데 볼 도구가 없는 자원은 그 사실을 기록한다.

## 핵심 문장

- 성능 작업은 측정 → 병목 특정 → 한 가지만 바꾸기 → 같은 조건 재측정의 반복이다.
- Amdahl: 전체의 비율 p인 구간을 s배 빠르게 하면 속도향상은 1 / ((1 − p) + p/s), 상한은 1 / (1 − p)다. 5% 구간을 2배로 해도 전체는 2.5% 준다.
- 작은 구간 개선은 이득이 작을 뿐 아니라 잡음에 묻혀 확인도 어렵다(실험: 예측 2.5%, 실측 −4.8% ~ +4.7%).
- 병목을 풀면 다음 병목이 나타난다. 하류 풀이 병목이면 위쪽 동시성을 늘려도 대기 시간만 는다(실험: 400건/s에서 멈춤).
- 가로등 효과·무작위 변경을 피하려면 도구가 아니라 자원 목록(USE)과 가설에서 출발한다.

## 관련 주제·근거

- 선행
  - [os/31-os-observability-tools](../../os/31-os-observability-tools/2-summary.md) — USE 방법론, vmstat·iostat·pidstat
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 제대로 재기
  - 원본 [engineering-axes/performance.md](../../engineering/engineering-axes/performance.md) — 대원칙 ②·③, 성능 작업의 함정
- 후속·연결
  - [21-scaling-principles](../21-scaling-principles/2-summary.md) — Little's Law·USL (USL 식·α/β 구분: <http://www.perfdynamics.com/Manifesto/USLscalability.html>)
  - [36-profiling](../36-profiling/2-summary.md) — 코드 안 병목
  - [38-microbenchmarking](../38-microbenchmarking/2-summary.md) — 변경 전후 비교의 통계
  - [database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md) — 풀이 병목일 때
- 논문·책·글
  - Amdahl, "Validity of the single processor approach to achieving large scale computing capabilities", AFIPS Spring Joint Computer Conference 1967, pp. 483–485 <https://dl.acm.org/doi/10.1145/1465482.1465560>
  - Gregg, "Performance Analysis Methodology" — Problem Statement·Scientific Method·USE·Drill-Down, Streetlight·Drunk Man·Random Change·Blame-Someone-Else·Passive Benchmarking·Traffic Light 안티 방법론 <https://www.brendangregg.com/methodology.html>
  - Gregg 『Systems Performance』 2판 2장 Methodology(목차는 <https://www.brendangregg.com/systems-performance-2nd-edition-book.html>에서 확인, 장 내부 절 번호는 [?])
  - Gregg, "The USE Method" <https://www.brendangregg.com/usemethod.html>
- 실험 목록
  - Amdahl.java — 직렬 비율 0/0.1/0.5에서 P=1·2 속도향상, 5%·95% 구간 2배 개선. Docker eclipse-temurin:21-jdk `--cpus=2 --cpuset-cpus=6,7`
  - Shift.java — 워커 2~32, DB 풀 4개(세마포어) 처리량·대기. `--cpus=2`, 워커 수마다 3초
