# math/09-common-distributions — 균등·기하·이항·포아송·지수·정규·멱법칙(Zipf) — 정리 (힌트)

## 해결하는 문제

초당 평균 100건이라 서버를 "포아송이면 p99가 124건"에 맞췄다. 그런데 몇 초에 한 번씩 500건이 몰려 큐가 터진다.

```text
  초당 도착 수 (실험 B)
  포아송(100/s)  ▁▂▅█▅▂▁            분산 ≈ 평균 = 100    p99 124
                 ──┼──
                  100
  버스트(평균 100) █                          ▂          분산 ≈ 22,600   p99 580
                 ─┼──────────────────────────┼──
                  50                        550
```

- 평균이 같아도 분포가 다르면 꼬리가 다르다. 용량·캐시·샤드 설계는 **어떤 분포를 가정했나**에 따라 달라진다.
- 이 노트는 백엔드에서 자주 만나는 분포 일곱 개를 "무엇을 세나"로 묶고, 가정이 깨질 때 보이는 모습을 본다.

쉬운 예: 편의점 손님은 서로 모르는 사람들이 따로 온다. 그래서 몇 분에 몇 명 오는지가 포아송에 가깝다. 출근길 지하철역은 열차가 도착할 때마다 한꺼번에 쏟아진다.

똑같은 구조다.\
독립적인 작은 원천이 많고(각 원천은 드물게 보내고) 합친 도착률이 그 구간에서 일정하면 포아송, 공통 원인(열차 도착, 배치 시작, 푸시 알림)이 있으면 버스트다.

실무 예:
- 부하 테스트 생성기의 도착 간격(지수 분포)과 운영 트래픽(버스트)의 차이.
- 인기 상품 키 하나가 샤드 하나를 태운다(Zipf).
- 재시도 횟수(기하분포)와 지수 백오프.
- Java `HashMap` 소스 주석의 "칸당 원소 수는 포아송(0.5)" 표.

## 동작·원리

### 0. 지도 — 무엇을 세나

| 분포 | 무엇을 세나 | 확률(질량·밀도) | 평균 | 분산 | 운영 예 |
|---|---|---|---|---|---|
| 균등 {1..n} | n개 중 하나를 고르게 | 1/n | (n+1)/2 | (n²−1)/12 | 해시 칸, 지터 |
| 이항(n, p) | n번 시도 중 성공 수 | C(n,k)·p^k·(1−p)^(n−k) | np | np(1−p) | 요청 n건 중 실패 수 |
| 기하(p) | 첫 성공까지 시도 수(1,2,…) | (1−p)^(k−1)·p | 1/p | (1−p)/p² | 재시도 횟수 |
| 포아송(λ) | 단위 시간 사건 수 | e^(−λ)·λ^k / k! | λ | λ | 초당 도착, 해시 칸 길이 |
| 지수(λ) | 다음 사건까지 시간 | λ·e^(−λx), P(X>t)=e^(−λt) | 1/λ | 1/λ² | 도착 간격 |
| 정규(μ, σ²) | 독립인 작은 값 여럿의 합 | 종 모양 | μ | σ² | 표본 평균, 측정 오차 |
| Zipf(s, N) | 순위 k의 빈도 | (1/k^s) / H(N,s) | — | — | 키 인기도, 테넌트 크기 |

- *확률 질량 함수(pmf)*: 이산 변수가 값 k를 가질 확률. *확률 밀도 함수(pdf)*: 연속 변수의 구간 확률을 적분으로 주는 함수.
- 기하분포는 "첫 성공 전 실패 수(0,1,…)"로 정의하는 책도 있다. 이 노트는 OpenIntro 4.2처럼 시도 수(1,2,…)로 쓴다.
- `H(N,s) = Σ_{k=1..N} 1/k^s`. s=1이면 조화수 H_N.
- 출처: OpenIntro 4장(4.1 정규, 4.2 기하, 4.3 이항, 4.5 포아송). 지수 분포는 OpenIntro 4장 목차에 없다. 아래 식은 정의에서 바로 나온다(포아송 과정의 간격).

### 1. 이항 → 포아송 — 해시 칸 길이

```text
  칸 2^20개에 키 2^19개를 균등하게 던진다
  한 칸에 들어가는 키 수 = 이항(n = 524,288, p = 1/2^20)
  n이 크고 p가 작고 np = 0.5 → 포아송(0.5)로 근사

  k     이항 정확값      포아송(0.5)
  0     0.6065305        0.6065307
  1     0.3032655        0.3032653
  2     0.0758163        0.0758163
```

- *포아송 근사*: n이 크고 p가 작으면 이항(n, p) ≈ 포아송(np). 위 표는 Python으로 계산한 두 값이다(소수 7자리까지 거의 같다).
- OpenJDK 21 `HashMap.java` 주석: 무작위 hashCode라면 칸당 원소 수가 "about 0.5" 모수의 포아송을 따르고(리사이즈 임계 0.75 기준, 리사이즈 단위 때문에 분산은 크다), 길이 8은 "0.00000006"이다. 실제 트리화는 이미 8개인 칸에 9번째가 들어올 때 시도되고(`putVal`의 `binCount >= TREEIFY_THRESHOLD - 1`), 테이블이 64칸(`MIN_TREEIFY_CAPACITY`) 미만이면 트리화 대신 리사이즈한다. 그 길이까지 가는 일이 이 표에서 매우 드물어, 주석도 정상 hashCode에서는 "tree bins are rarely used"라 적는다. 충돌 공격으로 이 가정이 깨지는 경우는 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).

### 실험 A: 칸당 원소 수 vs 포아송(0.5)

```java
// scratchpad/math/07/e09/Dist.java 핵심 — 무작위 키의 상위 20비트로 칸 선택
for (int i = 0; i < n; i++) c[(int) (r.nextLong() >>> 44)]++;
```

(실험, OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`, `SplittableRandom` seed 42, 2026-10-07)

```text
(A) 칸 1,048,576개에 키 524,288개(평균 λ=0.5) — 칸당 원소 수 분포
 k   실측 비율     포아송 e^-0.5·0.5^k/k!
 0   0.60665607   0.60653066
 1   0.30316925   0.30326533
 2   0.07571030   0.07581633
 3   0.01264095   0.01263606
 4   0.00164604   0.00157951
 5   0.00016308   0.00015795
 6   0.00001240   0.00001316
 7   0.00000191   0.00000094
 8   0.00000000   0.00000006
최대 칸 길이 = 7
```

- 관찰 1: k ≤ 3에서 차이가 0.0002 이하다(소수 셋째 자리까지 같다). 칸 100만 개 중 길이 7은 2개(0.00000191 × 2^20)뿐이라 k ≥ 6은 표본 오차가 크다.
- 관찰 2: 평균은 0.5인데 최대 칸 길이는 7이다. 평균(선형성, 08)과 최댓값(꼬리)은 다른 질문이다.

### 2. 포아송 도착과 지수 간격 — 그리고 버스트

```text
  포아송 과정: 서로 독립인 작은 원천이 많고 합친 도착률 λ가 일정 → 도착이 고르게 무작위
  시간 ─┬──┬─────┬─┬───────┬──┬───┬────>
        간격 ~ 지수(λ), 서로 독립.  1초 동안 개수 ~ 포아송(λ)

  버스트(두 상태): 평소 50/s, 10%의 초는 550/s
  시간 ─┬────┬─────┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬────┬──────┬───>
                  └─ 공통 원인(배치 시작, 푸시 알림) ─┘
```

- *포아송 과정*: 겹치지 않는 구간의 도착 수가 서로 독립이고, 길이 t 구간의 도착 수가 포아송(λt)인 과정. 도착 간격은 지수(λ)다.
- *분산/평균 비(dispersion index)*: 포아송이면 1. 1보다 훨씬 크면 버스트가 있다.
    - 흔한 오해: "1이면 포아송이다." 1은 필요조건일 뿐이다. 예: 0과 2가 각각 1/2인 분포도 평균·분산이 1이다. 분포 모양과 구간 간 독립도 함께 본다.
- 버스트 모델의 분산(혼합 분포): `Var = E[λ] + Var[λ] = 100 + (0.1·550² + 0.9·50² − 100²) = 22,600`.
- Paxson·Floyd(IEEE/ACM ToN 1995): 광역 트래픽에서 포아송은 사용자 세션 도착(TELNET 접속, FTP 제어 접속 — 시간대별로 고정된 비율일 때)에는 맞지만, 다른 도착 과정(패킷, FTP 데이터 접속 등)에는 맞지 않았다. 원문: "Poisson processes are valid only for modeling the arrival of user sessions".

### 실험 B: 포아송 vs 버스트 — 같은 평균, 다른 p99

```java
// 지수 간격을 1초 동안 더해 개수를 센다 → 포아송(λ)
int k = 0; double t = -Math.log(1 - r.nextDouble()) / lam;
while (t < 1) { k++; t += -Math.log(1 - r.nextDouble()) / lam; }
// 버스트: 초마다 10% 확률로 λ=550, 아니면 λ=50
b[s] = poisson(r, r.nextDouble() < 0.1 ? 550 : 50);
```

(실험, 같은 환경, 10만 초 시뮬레이션, seed 42)

```text
(B) 초당 도착 수, 100,000초 시뮬레이션
모델        평균    분산     p50   p99   p99.9   '포아송 p99 용량' 초과 초 비율
포아송       100.0     99.9    100   124     132     0.89% (용량 124/s)
버스트        99.3  22319.2     51   580     605     9.86% (용량 124/s)
```

- 관찰 1: 평균은 둘 다 약 100이다. 분산은 99.9 vs 22,319(이론 22,600)다.
- 관찰 2: 포아송 p99(124/s)에 맞춘 용량은 포아송 트래픽에서 0.89%의 초만 넘는다. 버스트 트래픽에서는 9.86%의 초가 넘친다. 그 초는 거의 다 버스트 상태(λ=550)라, 처리 용량보다 약 400건 더 들어온다(모델에서 어림한 해석 — 큐 길이는 앞 초의 잔량에 따라 다르다).
- 관찰 3: 버스트의 중앙값(51)은 평균(99)의 절반이다. "평균 100"은 어느 초의 모습도 아니다.
- seed 7 재실행: 포아송 분산 100.0·p99 124, 버스트 분산 22,517·p99 580.

### 3. 기하분포 — 재시도와 무기억성

```text
  시도마다 성공 확률 p, 독립
  P(시도 수 > k) = (1 − p)^k              (k번 연속 실패)
  무기억성: P(시도 > s + t | 시도 > s) = P(시도 > t)
           "이미 3번 실패했다"는 사실이 앞으로의 확률을 바꾸지 않는다
           (재시도에 이 식을 쓰려면 시도들이 독립이고 p가 일정해야 한다)

  지수 분포도 같다: P(X > s + t | X > s) = e^(−λt)
```

- *무기억성(memorylessness)*: 이산에서는 기하, 연속에서는 지수 분포만 가진 성질.
- 운영 의미: 실패가 독립이면 총 3번 시도에 `1 − 0.7^3 = 65.7%`(p = 0.3)가 성공한다(첫 시도 + 재시도 3번 = 총 4번이면 `1 − 0.7^4 = 76.0%`). 실패가 **과부하처럼 상관되어 있으면** 독립이 깨진다. 재시도도 같이 실패하고 부하만 더한다([reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)).
- 지수 백오프의 대기 식과 지터는 reliability/06에 있다. 여기서는 "몇 번 만에 성공하나"가 기하분포라는 것만 본다.

(실험 D, 같은 환경, 100만 회, seed 42)

```text
(D) 시도마다 성공 확률 0.3 — 첫 성공까지 시도 수, 1,000,000회
평균 3.331 (이론 1/p = 3.333)
P(시도>5) = 0.1678 (이론 0.7^5 = 0.1681)
P(시도>8 | 시도>3) = 0.1687 (이론 0.7^5 = 0.1681) ← 무기억성
```

- seed 7 재실행(조건부 확률 줄): 0.1683. 이론 0.1681 근처에서 ±0.001 수준으로 흔들린다.

### 4. 정규분포 — 합에는 맞고, 꼬리가 무거운 값에는 틀린다

```text
  μ ± 1σ: 약 68%    μ ± 2σ: 약 95%    μ ± 3σ: 약 99.7%   (OpenIntro 4.1, 68-95-99.7 규칙)

  로그정규 지연(08 실험 C)에 정규를 잘못 쓰면
    평균 33.0ms, 표준편차 43.2ms
    "p99 ≈ μ + 2.326σ" = 133.5ms        실제 p99 = 204.8ms   (1.5배 과소)
```

- 독립·동일 분포이고 분산이 유한한 값 여럿의 합(표본 평균)은 정규에 가까워진다 — 중심극한정리(분산이 무한하면 성립하지 않는다). 자세히는 [data-analysis/07-sampling-distributions-and-clt](../../data-analysis/07-sampling-distributions-and-clt/2-summary.md).
- 지연·파일 크기처럼 오른쪽 꼬리가 긴 값 자체는 정규가 아니다. 평균+표준편차로 p99를 어림하면 과소평가한다(위 계산, 로그정규 공식에서 해석적으로 구한 값).

### 5. 멱법칙(Zipf) — 인기 키

```text
  순위 k의 빈도 ∝ 1/k^s       (s=1, 키 10만 개)
  빈도
   █ 8.27%   ← 1위 키 하나
   ▅ 4.1%
   ▃ 2.8%
   ▂▂▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁ ... 긴 꼬리 (10만 위까지)
   └─────────────────────> 순위
  log-log 그림에서 기울기 −s의 직선
```

- *멱법칙(power law)*: 빈도가 순위의 거듭제곱에 반비례. *Zipf 분포*는 그 이산·유한판.
- 1위 키 비율 = `1 / H(N,s)`. N = 10만, s = 1이면 `1/12.09 = 8.27%`.
- Breslau 외(INFOCOM 1999)는 웹 프록시 요청의 페이지 인기도가 정확한 Zipf가 아니라 Zipf 꼴(Zipf-like)이고, 지수 s가 트레이스마다 다르다고 보고했다(저자 페이지 초록). 그리고 캐시에 주는 의미를 분석했다.
- 두 얼굴
  - 캐시에는 **좋다**: 소수 키가 요청 대부분이라 작은 캐시도 적중률이 높다.
  - 샤드에는 **나쁘다**: 해시 샤딩만으로는 1위 키 하나를 나눌 수 없다. 해시가 아무리 균등해도 그 키가 간 샤드가 뜨겁다(키 자체를 여러 키로 쪼개야 나뉜다).

### 실험 C: Zipf 접근 — 캐시 적중률과 샤드 부하

```java
// 누적 분포 배열 + 이진 탐색으로 Zipf 순위를 뽑는다
int j = Arrays.binarySearch(cdf, r.nextDouble()); req[i] = j >= 0 ? j : -j - 1;
// LRU = 접근 순서 LinkedHashMap + removeEldestEntry (앞 10% 요청은 데우기로 빼고 셈)
// 샤드 = floorMod(mix(key), 16)
```

(실험, 같은 환경, 키 10만 개, 요청 200만 건, seed 42)

```text
(C) Zipf s=1.0, 키 100,000개, 요청 2,000,000건 — 최상위 키 비율 8.27%
캐시(키 비율)   LRU 적중(실측)   상위 k 확률 합(정적 최적)   균등 가정 k/N
  1,000 ( 1.0%)     50.56%            61.91%                   1.0%
  5,000 ( 5.0%)     66.54%            75.22%                   5.0%
 10,000 (10.0%)     73.77%            80.96%                  10.0%
샤드 16개(키 해시): 최대 샤드 부하 / 평균 = 1.99배 (같은 키 수 균등 접근이면 1.02배)

(C) Zipf s=0.8, 키 100,000개, 요청 2,000,000건 — 최상위 키 비율 2.19%
캐시(키 비율)   LRU 적중(실측)   상위 k 확률 합(정적 최적)   균등 가정 k/N
  1,000 ( 1.0%)     20.51%            33.95%                   1.0%
  5,000 ( 5.0%)     36.99%            50.54%                   5.0%
 10,000 (10.0%)     46.93%            59.50%                  10.0%
샤드 16개(키 해시): 최대 샤드 부하 / 평균 = 1.23배 (같은 키 수 균등 접근이면 1.02배)
```

- 관찰 1: 키의 1%만 캐시해도 s=1에서 요청의 51%가 적중한다. 균등 가정(1%)보다 50배 많다.
- 관찰 2: LRU는 "가장 인기 있는 k개를 고정해 둔 캐시"(정적 최적, 상위 k 확률 합)보다 7~14%p 낮다. LRU는 인기를 모르고 최근성만 본다. 교체 정책 비교는 [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- 관찰 3: s가 1 → 0.8로 조금만 바뀌어도 같은 캐시의 적중률이 51% → 20%로 떨어진다. 캐시 크기를 정할 때 s를 운영 로그로 재야 하는 이유다.
- 관찰 4: 같은 해시로 균등 접근이면 최대 샤드가 평균의 1.02배인데, Zipf(s=1)는 1.99배다. 1위 키(8.27%)만으로 평균 샤드 몫(6.25%)을 넘는다.
- seed 7 재실행: s=1 LRU 적중 50.65·66.57·73.77%, 샤드 1.99배. s=0.8 LRU 적중 20.44·36.93·46.87%, 샤드 1.24배.

## 쓰이는 자료구조·알고리즘

- 해시 칸 길이 포아송 → `HashMap` 트리화 임계: [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
- 지수 백오프·지터: [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md).
- 포아송 도착 생성(역변환 `−ln(1−U)/λ`)과 Zipf 키 샘플링(누적 분포 + 이진 탐색): [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md).
- Zipf와 캐시 적중률·교체 정책: [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md). 핫키·큰 테넌트 분리: [reliability/51-cells-stamps-and-blast-radius](../../reliability/51-cells-stamps-and-blast-radius/2-summary.md), [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
- 이진 탐색(누적 분포에서 표본 뽑기): [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 트래픽이 포아송인지 확인

1. 증상: 평균 부하는 여유인데 짧은 순간 큐·타임아웃이 터진다.
2. 식으로 어림: 초당(또는 100ms당) 도착 수의 분산/평균을 본다. 1 근처면 포아송과 양립(그것만으로 포아송이라 단정하지 않는다), 수십·수백이면 버스트.
3. 코드로 확인:

```java
// 접근 로그의 타임스탬프(ms) → 초당 개수 → 분산/평균, p99
static void dispersion(long[] tsMillis) {
    Map<Long, Integer> perSec = new TreeMap<>();
    for (long t : tsMillis) perSec.merge(t / 1000, 1, Integer::sum);
    double[] c = perSec.values().stream().mapToDouble(Integer::doubleValue).sorted().toArray();
    double m = Arrays.stream(c).average().orElse(0), v = Arrays.stream(c).map(x -> (x - m) * (x - m)).sum() / c.length;
    System.out.printf("mean=%.1f var=%.1f var/mean=%.2f p99=%.0f%n", m, v, v / m, c[(int) Math.ceil(.99 * c.length) - 1]);
}
```

- 빈 초(도착 0)는 위 맵에 안 잡힌다. 실제 분석에서는 구간 전체를 0으로 채운 뒤 센다.

4. 대처: 용량은 평균이 아니라 짧은 구간의 p99·p99.9 도착 수에 맞춘다. 버스트가 공통 원인(배치·푸시·cron 정각)이면 원인을 흩는다(지터, [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md)).

### 2. 키 인기도가 Zipf인지 확인

- 키별 요청 수를 내림차순으로 정렬해 (log 순위, log 빈도)를 그린다. 직선이면 기울기가 −s다.
- 상위 1·10·100개 키의 요청 비율을 지표로 둔다. 1위 키 비율이 `1/샤드 수`를 넘으면 그 키 하나로 샤드 하나가 평균 이상이다.
- 대처: 핫키 복제(읽기 분산), 로컬 캐시, 키 분할(쓰기 카운터를 여러 키로 쪼개 합산), 큰 테넌트 전용 셀.

## 장애 시나리오와 대처

### 1. 트래픽을 포아송으로 가정 → 버스트에서 과부하 (⚠ 커리큘럼)

- 현상: 평균 100/s 기준 p99 124/s 용량으로 잡았다. 몇 초마다 큐가 넘치고 타임아웃이 난다.
- 보이는 형태: 분당 지표는 평온하다. 초 단위 지표에서 스파이크가 보인다. 스레드풀 대기열·`RejectedExecutionException`·503이 특정 초에 몰린다.
- 원인: 도착이 독립이 아니다(배치 시작, 푸시 알림, 정각 cron, 재시도 폭풍). 분산이 평균의 수백 배다(실험 B: 9.86%의 초가 용량 초과).
- 대처: 초 단위 분산/평균을 측정한다. 용량은 짧은 구간 p99에 맞춘다. 공통 원인에 지터를 넣고, 넘치는 순간은 백프레셔·부하 차단([reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md)).

### 2. 핫키(Zipf) 과소평가 → 샤드 과부하 (⚠ 커리큘럼)

- 현상: 샤드 16개 중 하나만 CPU 100%. 샤드를 늘려도 그 샤드는 여전히 뜨겁다.
- 보이는 형태: 샤드별 요청 수가 평균의 2배(실험 C). 그 샤드의 상위 키 하나가 전체의 8%를 차지한다.
- 원인: 해시는 키를 균등하게 나눌 뿐 요청을 균등하게 나누지 않는다. 단일 키로 두는 한 샤딩만으로는 1위 키를 나눌 수 없다.
- 대처: 핫키 감지(상위 키 비율 지표), 읽기 복제·로컬 캐시, 쓰기 키 분할. 샤드 추가는 1위 키 문제를 풀지 못한다.

### 3. 캐시 크기를 다른 s로 정했다

- 현상: 테스트에서 적중률 70%였던 캐시가 운영에서 45%다.
- 보이는 형태: 캐시 미스율·DB QPS가 계획의 두 배 가까이.
- 원인: 적중률은 s에 민감하다. 같은 캐시(키의 10%)가 s=1에서 74%, s=0.8에서 47%다(실험 C). 테스트 데이터가 운영보다 쏠려 있었다.
- 대처: 운영 로그에서 s(또는 상위 k 비율)를 재고 그 분포로 부하 테스트한다([reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md)).

### 4. 정규 가정으로 p99를 어림했다

- 현상: "평균 + 2.33σ"로 타임아웃을 정했는데 타임아웃 비율이 1%를 크게 넘는다.
- 보이는 형태: 계산한 p99 134ms, 실제 p99 205ms(로그정규 예, 4절).
- 원인: 지연은 오른쪽 꼬리가 긴 분포다. 정규의 68-95-99.7은 맞지 않는다.
- 대처: 실측 히스토그램의 백분위를 쓴다. 분포를 가정해야 하면 로그를 취해 정규성을 본다(해석).

### 5. 재시도가 독립이라고 가정했다

- 현상: "실패율 30%니 3번 시도하면 97% 성공"으로 계산했는데, 장애 때 재시도도 다 실패하고 부하만 3배가 됐다.
- 보이는 형태: 재시도 횟수 지표가 상한에 붙는다. 하류 서비스 QPS가 평소의 수 배.
- 원인: 재시도 횟수를 기하분포(무기억성 포함)로 모델링하려면 시도들이 독립이어야 한다. 과부하 실패는 서로 상관된다.
- 대처: 재시도 예산·서킷 브레이커로 상관된 실패에서 재시도를 끊는다([reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md), [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)).

## 핵심 문장

- 분포는 "무엇을 세나"로 고른다: 성공 수(이항), 첫 성공까지(기하), 단위 시간 사건 수(포아송), 사건 간격(지수), 합(정규), 순위별 빈도(Zipf).
- 포아송은 독립인 작은 원천이 많고 도착률이 일정할 때의 모델이다. 분산/평균이 1에서 멀면 버스트이고, 용량은 짧은 구간의 p99로 잡는다.
- 이항(n 크고 p 작음)은 포아송으로 근사된다. Java `HashMap`의 칸 길이 표가 그 예다.
- 무기억성은 기하·지수 분포의 성질이고, 재시도를 기하분포로 보려면 시도들이 독립이어야 한다. 상관된 실패에서 재시도 계산은 낙관적이다.
- Zipf는 캐시에는 이득, 샤드에는 위험이다. 샤드를 늘려도 1위 키 하나는 나뉘지 않는다.

## 관련 주제·근거

선행·후속:
- 선행: [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md)(기댓값·분산·꼬리), [07-probability-and-bayes](../07-probability-and-bayes/2-summary.md).
- 후속: [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md)(분포에서 표본을 뽑는 난수), 큐잉과 Little 법칙([수학 10](../10-queueing-and-littles-law/2-summary.md) — 포아송 도착·지수 서비스의 M/M/1). 원고의 큐잉 절: [systems/server-design/01-scaling-principles.md](../../systems/server-design/01-scaling-principles.md).
- 다른 영역: [reliability/22-capacity-and-load-testing](../../reliability/22-capacity-and-load-testing/2-summary.md), [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md), [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md). 표본 분포·중심극한정리는 [data-analysis/07-sampling-distributions-and-clt](../../data-analysis/07-sampling-distributions-and-clt/2-summary.md).

근거:
- OpenIntro Statistics 4장 Distributions of random variables(4.1 Normal, 4.2 Geometric, 4.3 Binomial, 4.4 Negative binomial, 4.5 Poisson) — https://www.openintro.org/book/os/ 목차(2026-10-07 열람). 68-95-99.7 규칙은 4.1.
- OpenJDK 21 `java/util/HashMap.java` 구현 주석(포아송 0.5 표) — https://github.com/openjdk/jdk21u/blob/master/src/java.base/share/classes/java/util/HashMap.java (2026-10-07 열람).
- V. Paxson, S. Floyd, "Wide Area Traffic: The Failure of Poisson Modeling", IEEE/ACM Transactions on Networking 3(3):226–244, 1995 — https://web.stanford.edu/class/cs244/papers/paxson1995.pdf
- L. Breslau, P. Cao, L. Fan, G. Phillips, S. Shenker, "Web Caching and Zipf-like Distributions: Evidence and Implications", IEEE INFOCOM 1999, 1권 126–134쪽, doi:10.1109/INFCOM.1999.749260(서지는 Crossref, 초록은 저자 페이지 http://pages.cs.wisc.edu/~cao/papers/zipf-implications.html — 본문은 이 노트에서 대조하지 않았다).
- Python 3.12 `random.expovariate` 문서(인자 lambd = 1/원하는 평균) — 지수 간격 생성의 표준 라이브러리 예.

실험 목록:
- 실험 A(칸 길이 vs 포아송)·B(포아송 vs 버스트 초당 도착)·C(Zipf LRU 적중률·샤드 부하, s=1·0.8)·D(기하분포·무기억성): `scratchpad/math/07/e09/Dist.java`, `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) eclipse-temurin:21-jdk java Dist.java 42`(재실행 seed 7). OpenJDK 21.0.12 Temurin, 2026-10-07.
- 계산 보조(이항 vs 포아송 표, 버스트 분산 22,600, 포아송(100) p99 = 124, 로그정규의 정규 근사 133.5ms, H(10⁵) = 12.09): 호스트 Python 3.12.3 표준 라이브러리.
