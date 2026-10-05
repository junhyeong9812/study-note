# reliability/11-rate-limiter — 토큰 버킷·리키 버킷·고정/슬라이딩 창·분산 제한 — 정리 (힌트)

## 해결하는 문제

서버 용량은 유한한데 부르는 쪽은 그것을 모른다.\
"단위 시간당 N건까지"를 세는 장치가 없으면 두 가지가 무너진다.

```text
 제한 없음   사용자 A가 초당 1만 건 ─> 용량 소진 ─> B·C·D 전부 느려짐        (보호 실패)
             무료 요금제가 유료 요금제 몫을 먹음                              (공정성 실패)
 제한 있음   A는 100건 뒤 429 ─> 나머지는 리미터에서 거절돼 DB까지 안 감 ─> B·C·D 무사
```

- *레이트 리미터(rate limiter)*: 키(사용자·API 키·IP·테넌트)별로 단위 시간당 받는 요청 수에 상한을 거는 장치.
- *429 Too Many Requests*: "주어진 시간에 너무 많이 보냈다"는 HTTP 상태 코드(RFC 6585 §4). `Retry-After`를 **넣을 수 있다**(MAY).

쉬운 예: 놀이공원 입장 제한 "시간당 100명". 매시 정각에 계수기를 0으로 돌리는지, 입장 시각을 다 적는지, 입장권을 미리 나눠 주는지에 따라 실제 들어가는 사람 수가 다르다.\
똑같은 구조다.\
실무 예: 공개 API의 429, 로그인 시도 제한, nginx `limit_req`, Stripe의 사용자별 토큰 버킷.

방향 정리: 06(재시도)은 **우리가 남을 때리는 속도**, 이 노트는 **남이 우리를 때리는 속도**를 다룬다.\
기초(다섯 구현 직접 만들기, 정수 스케일, 시계 되감김 방어, 측정 표)는 원본 [ops-patterns/04-rate-limiter](../../ops-patterns/04-rate-limiter/2-summary.md) 「동작·원리」에 있다.\
이 노트는 경계 2배와 버킷 상한을 다시 실험하고, 실제 제품(nginx·Resilience4j·Stripe·Redis)과 **분산 제한의 경합**을 더한다.

## 동작·원리

### 1. 세는 방법 다섯 — 그림

```text
 고정 창          |--- 창0: count ---|--- 창1: count=0부터 ---|      경계에서 리셋
 슬라이딩 로그     시각 목록 [t1 t2 ... tn]  지금-1초 이전은 버림        정확, 메모리 = 요청 수
 슬라이딩 카운터   추정 = 이전 창 count × (창에서 안 지난 비율) + 현재 count   근사, 저장 2개
 토큰 버킷        [●●●●○○]  시간이 채우고(초당 r) 요청이 꺼냄(1개)        몰림을 b까지 통과
 리키 버킷        요청 → [대기줄] → 초당 r개씩 똑똑                       몰림을 지연으로 바꿈
```

- *창(window)*: 세는 시간 구간.
- *몰림(burst)*: 짧은 순간에 요청이 한꺼번에 오는 것. 실제 트래픽의 기본 모양이다.
- *토큰 버킷(token bucket)*: 용량 b의 통에 초당 r개씩 토큰이 찬다. 요청은 토큰 1개를 쓰고, 없으면 거절한다.
- *리키 버킷(leaky bucket)*: 요청을 대기줄에 세우고 일정 속도로 내보낸다. 줄이 차면 거절한다.

### 실험 A: 경계 2ms 사이의 통과 수

한도 100건/1초. t=999ms에 100건, t=1001ms에 100건을 보낸다.

```java
// 고정 창 (scratchpad/rel/06/e11/Rl.java)
public boolean ok(long t) {
    long w = Math.floorDiv(t, 1000);
    if (w != win) { win = w; cnt = 0; }          // 창이 바뀌면 리셋
    if (cnt < 100) { cnt++; return true; } return false;
}
// 토큰 버킷 (용량 100, 초당 100)
public boolean ok(long t) {
    tok = Math.min(cap, tok + (t - last) * perSec / 1000.0); last = t;
    if (tok >= 1) { tok -= 1; return true; } return false;
}
```

(실험, JDK 21 temurin `--cpus=2`, 시각은 가상 시계(ms), 2026-10-01)

```text
(A) 한도 100/1초. t=999에 100건, t=1001에 100건 → 통과 수
  고정 창                   t=999:100  t=1001:100   2ms 사이 합 200
  슬라이딩 로그                t=999:100  t=1001:  0   2ms 사이 합 100
  슬라이딩 카운터               t=999:100  t=1001:  0   2ms 사이 합 100
  토큰 버킷(100, 100/s)      t=999:100  t=1001:  0   2ms 사이 합 100
```

- 고정 창만 2ms 사이에 **200건**을 통과시켰다. 창이 바뀌는 순간 계수기가 0이 된다.

### 실험 B: 아무 1초 구간의 최대 통과 수

t=900ms부터 1ms마다 10건씩 5초 동안 보낸다. 통과한 시각으로 "아무 1000ms 구간"의 최대를 센다.

(실험, 같은 파일, 2026-10-01)

```text
(B) t=900ms부터 1ms마다 10건씩 5초 홍수 → 아무 1000ms 구간의 최대 통과 수
  고정 창                   최대 200건 (구간 10~1009ms)
  슬라이딩 로그                최대 100건 (구간 0~999ms)
  슬라이딩 카운터               최대 189건 (구간 891~1890ms)
  토큰 버킷(100, 100/s)      최대 199건 (구간 892~1891ms)
```

- "한도 100/초"라는 말이 구현마다 다른 뜻이다.
  - 고정 창: 경계를 낀 구간에서 2배(200).
  - 토큰 버킷: **용량 + 1초 충전량**(100 + 99). 가득 찬 통을 한 번에 쓰고, 이어서 충전분을 쓴다.
  - 슬라이딩 카운터: 이전 창이 고르게 왔다고 가정하는 근사라, 몰림 모양에 따라 한도를 넘긴다(189).
  - 슬라이딩 로그만 어떤 1초 구간에서도 100이다. 대신 키마다 시각을 한도만큼 저장한다.
- 원본 노트의 측정(로그 100, 카운터 101, 고정 창 104, 버킷 199)과 같은 방향이다. 부하 모양이 달라 카운터·고정 창 숫자가 다르다.

### 2. 제품마다 무엇을 쓰나

| 제품 | 방식 | 확인한 것 |
|---|---|---|
| nginx `limit_req` | 리키 버킷. `burst`(기본 0)만큼 줄 세우고 넘치면 거절. `nodelay`면 줄 선 요청을 지연 없이 처리 | 거절 상태 코드 기본 **503**(`limit_req_status 503`) — 429가 아니다 (nginx 모듈 문서) |
| Resilience4j 2.x `RateLimiter` | 주기마다 허가를 `limitForPeriod`로 다시 채움(기본 구현 `AtomicRateLimiter`) — 고정 창 계열 | 기본 `limitForPeriod=50`, `limitRefreshPeriod=500ns`, `timeoutDuration=5s` (아래 실험 C) |
| Stripe (2017) | 사용자별 토큰 버킷, Redis | 리미터 버그·Redis 장애 시 **fail open**(요청을 통과)하도록 모든 층에서 예외를 잡는다. 끄는 스위치(기능 플래그)를 둔다 |
| Redis 문서의 INCR 패턴 | 초 단위 키 + `INCR` + `EXPIRE` = 고정 창 | 단일 카운터 변형은 INCR 뒤 EXPIRE가 빠지면 키가 남는 race가 있어 Lua로 묶으라고 적는다(실험 D의 "GET 후 INCR 초과 허용"과는 다른 race다) |

- *fail open*: 보호 장치가 고장 나면 막지 않고 통과시키는 설계. 반대는 *fail closed*(고장 나면 막음). 리미터에서는 가용성과 보호 중 무엇을 고르느냐다.

### 실험 C: Resilience4j RateLimiter의 주기 경계

(실험, Resilience4j 2.4.0, JDK 21, `limitForPeriod=100`, `limitRefreshPeriod=1s`, `timeoutDuration=0`, 실제 시계, 2026-10-01 — 2회 실행 같은 결과)

```text
(C) Resilience4j 2.4.0 RateLimiterConfig.ofDefaults()
  limitForPeriod=50 limitRefreshPeriod=PT0.0000005S timeoutDuration=PT5S
  생성 후 t=952ms 100건 시도 → 통과 100
  생성 후 t=1051ms 100건 시도 → 통과 100  (약 100ms 사이에 200건)
```

- 주기 경계(생성 후 1초)를 끼고 약 100ms 사이에 200건이 통과했다. 고정 창과 같은 성질이다.
  - 문서는 시간을 `limitRefreshPeriod` 길이의 주기로 나누고 주기 시작마다 허가를 `limitForPeriod`로 되돌린다고 적는다. 이 실험에서 경계는 리미터 생성 시점부터 센 1초였다.
- 기본 `timeoutDuration=5s`: 허가가 없으면 **최대 5초 기다린다**. 요청 스레드가 리미터 앞에서 묶일 수 있다. 서버 보호용이면 0으로 두고 바로 거절하는 편이 낫다(해석).

### 3. 분산 제한 — 서버 여러 대가 한 한도를 나눌 때

```text
 서버1 ─┐                      ① 인스턴스별 로컬 리미터: 한도 / N 씩 — 빠르지만 부하 쏠림에 부정확
 서버2 ─┼─> Redis 카운터 ─┐     ② 중앙 카운터: 정확하지만 왕복 1번 + 원자성 필요
 서버3 ─┘                 │     ③ 로컬 + 주기 동기화: 그 사이 초과 허용
                          └ "읽고 → 비교 → 쓰기"가 원자적이지 않으면 경합으로 한도를 넘긴다
```

### 실험 D: 분산 카운터 경합

Redis 7.4.9 일회용 컨테이너(`--network none`) 안에서 클라이언트 20개가 15번씩(총 300) 보낸다. 한도 100.

```sh
naive() {  # GET → 비교 → INCR (세 단계)
  v=$(redis-cli GET rl:naive); v=${v:-0}
  if [ "$v" -lt $LIMIT ]; then redis-cli INCR rl:naive; ...; fi; }
incr_first() {  # INCR 먼저, 돌아온 값으로 판정
  n=$(redis-cli INCR rl:incr); if [ "$n" -le $LIMIT ]; then ...pass...; fi; }
```

(실험, redis:7-alpine = Redis 7.4.9, `--cpus=2`, `scratchpad/rel/06/e11/race.sh`, 3회 실행, 2026-10-01)

```text
GET-비교-INCR : 통과 105 (한도 100), 카운터 105
INCR 먼저     : 통과 100 (한도 100), 카운터 300
Lua 토큰 버킷(용량100, 충전0): 통과 100
GET-비교-INCR : 통과 108 (한도 100), 카운터 108
INCR 먼저     : 통과 100 (한도 100), 카운터 300
Lua 토큰 버킷(용량100, 충전0): 통과 100
GET-비교-INCR : 통과 106 (한도 100), 카운터 106
INCR 먼저     : 통과 100 (한도 100), 카운터 300
Lua 토큰 버킷(용량100, 충전0): 통과 100
```

- GET 후 INCR: 여러 클라이언트가 같은 값(예: 99)을 읽고 모두 통과시켰다. 집필 3회에서 105~108건, 점검 재실행 3회에서 105~110건 통과. 한도를 넘긴 수는 실행마다 다르다.
- INCR 먼저: 원자 연산 하나의 **반환값**으로 판정하니 정확히 100건. 카운터가 300인 것은 거절된 요청도 올렸기 때문이다(고정 창이면 창이 바뀔 때 키가 만료되니 문제없다).
- Lua 토큰 버킷: 읽기-계산-쓰기를 스크립트 하나로 묶었다. Redis는 스크립트의 원자적 실행을 보장한다(Redis 문서 "Scripting with Lua": "Redis guarantees the script's atomic execution").
  - 이 실험은 충전 0으로 원자성만 봤다. 시각은 `redis-cli TIME`(Redis 서버 시계)으로 받아 클라이언트 시계 차이를 피했다.
  - 충전이 있는 실제 버킷에서는 시각을 스크립트 **안에서** 읽어야 한다(적용 3절). 밖에서 읽으면 읽은 순서와 실행 순서가 어긋날 수 있다.

## 쓰이는 자료구조·알고리즘

- **토큰 버킷** — 원형은 네트워크 트래픽 셰이핑. 재시도 예산(06)이 같은 모양이다. 상한 = 용량 + r × 구간.
- **리키 버킷(큐)** — 몰림을 지연으로 바꾼다. 줄 상한이 없으면 대기도 무제한이다(12 backpressure).
- **덱(Deque) 슬라이딩 로그** — 앞에서 만료 시각을 버리고 뒤에 새 시각을 붙인다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md).
- **슬라이딩 창 카운터** — 가중 평균 근사. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md)(커리큘럼 algorithm/15-sliding-window).
- **키별 카운터 해시** — 키 → 버킷/카운터. 메모리 = 활성 키 수 × 항목 크기. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **원자 증가·CAS·스크립트** — 분산 카운터의 정확성. 실험 D.

## 적용 — 풀어나가는 법

### 1. 순서

1. **제한 키**: 인증된 요청은 사용자·API 키·테넌트, 미인증만 IP. 회사 NAT 뒤 수백 명이 IP 하나를 쓴다.
2. **목적**: 남용 방지(보호용 스로틀) vs 요금제 쿼터(계약). 쿼터는 정확해야 하고(로그·중앙 카운터), 보호용은 근사로 충분하다.
3. **알고리즘**: 몰림 허용이 필요하면 토큰 버킷, 뒷단을 고르게 하려면 리키 버킷, 단순·분산이면 고정 창(경계 2배를 감수).
4. **응답 계약**: 429 + `Retry-After`(RFC 9110 §10.2.3: HTTP-date 또는 초). 남은 한도 헤더는 IETF 초안 `RateLimit-Policy`/`RateLimit`(draft-ietf-httpapi-ratelimit-headers-11, 2026-11-24 만료 예정의 초안 — 표준 아님).
5. **분산**: 중앙 카운터면 원자 연산(INCR 반환값·Lua). 리미터 장애 시 fail open/closed를 정한다.
6. **관측**: 키별 거절 수, 거절률, 리미터 지연.

### 2. 코드 — 키별 토큰 버킷 (Java)

```java
final class TokenBucket {
    private final long capacityMilli, refillPerSecMilli, fillNanos;   // 1/1000 단위 정수
    private long tokensMilli, lastNanos;
    TokenBucket(int capacity, int perSec) {
        capacityMilli = capacity * 1000L; refillPerSecMilli = perSec * 1000L;
        fillNanos = capacityMilli * 1_000_000_000L / refillPerSecMilli;   // 빈 버킷이 가득 차는 시간
        tokensMilli = capacityMilli; lastNanos = System.nanoTime();   // 단조 시계
    }
    synchronized boolean tryAcquire() {
        long now = System.nanoTime();
        long elapsed = Math.min(now - lastNanos, fillNanos);   // 가득 차는 시간으로 잘라 곱셈 오버플로를 막는다
        long add = elapsed * refillPerSecMilli / 1_000_000_000L;   // 곱하기 먼저
        if (add > 0) {
            tokensMilli = Math.min(capacityMilli, tokensMilli + add);
            lastNanos = (elapsed < now - lastNanos) ? now           // 잘랐으면 어차피 가득 참
                      : lastNanos + add * 1_000_000_000L / refillPerSecMilli;   // 버린 나머지 시간은 다음 번으로
        }
        if (tokensMilli < 1000) return false;
        tokensMilli -= 1000; return true;
    }
    synchronized long millisUntilNext() {          // Retry-After 계산용
        long need = 1000 - tokensMilli;
        return need <= 0 ? 0 : (need * 1000 + refillPerSecMilli - 1) / refillPerSecMilli;
    }
}
// 키별: ConcurrentHashMap<String, TokenBucket>.computeIfAbsent(apiKey, k -> new TokenBucket(100, 10))
// 거절 시: 429 + "Retry-After: " + ceil(millisUntilNext()/1000.0)
```

- `(now - last) * rate / 1e9` 순서가 중요하다. 나누기를 먼저 하면 1초 미만 경과가 0이 되어 충전이 멈춘다(원본 「측정」의 정수 나눗셈 함정).
- 곱하기를 먼저 하면 두 함정이 더 생긴다. 둘 다 위 코드에서 막았다.
  - 오버플로: 경과 시간을 자르지 않으면 `perSec=10`에서 약 10.7일 유휴 뒤 곱셈이 `long`을 넘어 음수가 된다.
  - 나머지 유실: `lastNanos = now`로 두면 나눗셈에서 버린 소수 충전분이 사라진다.
- (실험, JDK 21 temurin `--cpus=2`, 시각을 인자로 넣은 같은 클래스, `scratchpad/rel/fa-10/T.java`, 2026-10-02)

```text
150us 간격 100초: 고친 판 통과 1099, 옛 판 통과 766 (기대 ≈ 100 + 10×100 = 1100)
빈 버킷 → 11일 유휴 → 200건: 고친 판 통과 100, 옛 판 통과 0 (기대 100)
```

  - 옛 판(`lastNanos = now`, 자르지 않음)은 150µs마다 부르면 충전이 초당 약 6.7개로 느려졌고, 11일 유휴 뒤에는 오버플로로 한 건도 통과시키지 못했다.

### 3. Redis Lua 토큰 버킷 (실험 D 스크립트를 고친 판)

```lua
local cap=tonumber(ARGV[1]) local rate=tonumber(ARGV[2])       -- rate: 초당 토큰
local t=redis.call("TIME") local now=t[1]*1000+math.floor(t[2]/1000)   -- 스크립트 안에서 서버 시각
local b=redis.call("HMGET",KEYS[1],"tok","ts")
local tok=tonumber(b[1]) or cap local ts=tonumber(b[2]) or now
if now<ts then now=ts end                                        -- 시각이 뒤로 가면 충전 0
tok=math.min(cap, tok+(now-ts)*rate/1000)
local ok=0 if tok>=1 then tok=tok-1 ok=1 end
redis.call("HSET",KEYS[1],"tok",tok,"ts",now)
if rate>0 then redis.call("PEXPIRE",KEYS[1],math.ceil(cap*1000/rate)) end   -- 가득 차는 시간 뒤에만 만료
return ok
```

- 실험 D 판과 다른 점 두 가지.
  - 만료: 실험 D 판은 고정 60초였다. 충전이 느리면(용량 100, 초당 0.1개) 60초 뒤 키가 사라져 다음 요청에 100개가 다시 생긴다. 그래서 가득 차는 시간(`cap/rate`초) 뒤에만 만료시킨다.
  - 시각: 실험 D 판은 시각을 밖에서 `TIME`으로 읽어 인자로 넘겼다. 두 클라이언트가 시각을 읽은 순서와 스크립트가 실행된 순서가 어긋나면 `now < ts`가 되어 토큰이 줄 수 있다. 그래서 스크립트 안에서 읽고, 뒤로 간 시각은 충전에 쓰지 않는다.
- (실험, redis:7-alpine = Redis 7.4.9, `scratchpad/rel/fa-10/tb.lua`, 2026-10-02) 용량 100·초당 0.1로 105건 → 통과 100, `PTTL` 약 1,000,000ms(1000초). 충전 0이면 만료를 걸지 않는다(`PTTL -1`).

### 4. nginx

```nginx
limit_req_zone $binary_remote_addr zone=perip:10m rate=10r/s;
server {
  location /api/ {
    limit_req zone=perip burst=20 nodelay;
    limit_req_status 429;         # 기본은 503
  }
}
```

### 5. 진단

- 거절이 특정 키에 몰렸나(PromQL 예시, 지표 이름은 예시): `topk(10, sum by (key) (rate(ratelimit_rejected_total[5m])))`.
- 429 응답에 `Retry-After`가 있는지 `curl -si`로 본다. 클라이언트가 429 직후 바로 다시 오는지 접근 로그의 같은 키 간격을 본다.
- Redis 카운터가 한도를 넘어 있으면(GET 값 > limit) 판정이 원자적이지 않은지 의심한다(실험 D).

## 장애 시나리오와 대처

### 1. 고정 창 경계에서 2배 버스트 (⚠ 커리큘럼)

- 현상: 한도 100/초인데 하류가 짧은 순간 200/초 가까이를 받아 넘어진다.
- 보이는 형태: 하류 요청률 그래프가 초 경계마다 뾰족하다. 리미터 통계상으로는 "한도 준수".
- 원인: 창이 절대 시각으로 잘려 경계에서 리셋된다. 실험 A: 2ms 사이 200건. Resilience4j RateLimiter도 주기 경계에서 같다(실험 C).
- 대처: 하류가 버틸 수 있는 순간 상한이 중요하면 토큰 버킷(용량을 작게)이나 슬라이딩 로그로. 고정 창을 쓰면 한도를 하류 용량의 절반으로 잡는다.

### 2. 분산 카운터 경합 → 초과 허용 (⚠ 커리큘럼)

- 현상: 서버 여러 대가 Redis 카운터 하나를 보는데 한도 100 사용자가 105~110건을 통과한다.
- 보이는 형태: Redis 카운터 값이 한도를 넘어 있다. 부하가 높을수록 초과분이 커진다.
- 원인: "GET → 비교 → INCR"가 원자적이지 않다(TOCTOU). 실험 D: 집필·점검 6회 실행에서 105~110건.
  - *TOCTOU*: 검사한 시점과 쓰는 시점 사이에 상태가 바뀌는 결함.
- 대처: INCR 먼저 하고 반환값으로 판정, 계산이 끼면 Lua 스크립트. 정확도가 덜 중요하면 로컬 리미터(한도/N)로 왕복을 없앤다.

### 3. 토큰 버킷 용량을 크게 잡아 하류가 몰림을 그대로 맞는다

- 현상: "초당 100"으로 설정했는데 한가한 뒤 첫 1초에 하류가 199건을 받는다.
- 보이는 형태: 조용한 시간 뒤 첫 몰림에서만 하류 지연이 튄다.
- 원인: 버킷의 1초 상한은 용량 + 충전량이다(실험 B: 199).
- 대처: 용량은 "하류가 순간적으로 버틸 수 있는 몰림"으로 정한다. 하류를 고르게 해야 하면 리키 버킷(nginx `limit_req` + burst, `nodelay` 없이).

### 4. IP로 세서 회사 하나가 통째로 막힌다

- 현상: 한 회사 사용자 수백 명이 동시에 429를 받는다.
- 보이는 형태: 429가 한 IP에 몰리고, 그 IP 뒤에 서로 다른 계정이 수백 개.
- 원인: 제한 키가 IP. NAT 뒤에서 IP 하나를 나눠 쓴다.
- 대처: 인증된 요청은 계정·API 키·테넌트 단위로. IP 한도는 미인증 보호용으로 넉넉하게 따로. 계약 쪽 자세한 내용은 [api-design/14-rate-limit-and-quota-contracts](../../api-design/14-rate-limit-and-quota-contracts/2-summary.md).

### 5. 리미터가 고장 나서 전부 막는다 / 리미터 앞에서 스레드가 기다린다

- 현상 A: Redis가 내려가자 모든 API가 에러.
- 원인 A: 리미터 예외가 그대로 요청 실패가 됐다(fail closed).
- 대처 A: Stripe처럼 리미터 오류는 잡아서 통과시키고(fail open) 경보한다. 보안 한도(로그인 시도)는 fail closed가 맞을 수 있다 — 키 종류별로 정한다.
- 현상 B: 리미터를 켠 뒤 요청 스레드가 고갈된다.
- 원인 B: Resilience4j `RateLimiter` 기본 `timeoutDuration=5s`라 허가를 기다리며 스레드를 붙든다(실험 C 기본값).
- 대처 B: 서버 입구 리미터는 `timeoutDuration=0`으로 즉시 거절한다.

### 6. 429가 재시도 폭풍을 부른다

- 현상: 리미터를 켰더니 요청 수가 오히려 는다. 429 비율이 90%를 넘는다.
- 보이는 형태: 같은 클라이언트가 429 직후 즉시 다시 보낸다.
- 원인: `Retry-After`가 없고 클라이언트가 지터 없이 재시도한다.
- 대처: `Retry-After`를 넣고, 클라이언트 SDK에 지수 백오프 + 지터와 재시도 예산(06)을 둔다. nginx는 기본 503이니 의도대로 429로 바꾼다.

## 핵심 문장

- 리미터는 "남이 우리를 때리는 속도"를 키별로 묶는다. 무엇을 키로 셀지가 알고리즘보다 먼저다.
- "한도 100/초"는 구현마다 뜻이 다르다. 실험에서 아무 1초 구간 최대가 로그 100, 카운터 189, 토큰 버킷 199, 고정 창 200이었다.
- 고정 창의 경계 2배는 창을 절대 시각으로 자른 결과다. Resilience4j RateLimiter도 주기 경계에서 100ms 사이 200건을 통과시켰다.
- 분산 카운터는 "읽고-비교-쓰기"를 원자적으로 해야 한다. GET 후 INCR는 105~110건(6회 실행)을 통과시켰고, INCR 반환값 판정과 Lua는 정확히 100건이었다.
- 거절에는 `Retry-After`를 붙이고, 리미터 자체의 고장에 fail open/closed를 미리 정한다. nginx `limit_req`의 기본 거절 코드는 503이다.

## 관련 주제·근거

- 선행
  - [06-retry-backoff-jitter](../06-retry-backoff-jitter/2-summary.md) — 같은 토큰 버킷(재시도 예산), 429를 받는 쪽의 예절
  - [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) — 커리큘럼 algorithm/15-sliding-window
- 원본
  - [ops-patterns/04-rate-limiter](../../ops-patterns/04-rate-limiter/2-summary.md) — 다섯 구현, 정수 나눗셈·오버플로·시계 되감김 함정, WindowBoundaryTest·SustainedLoadTest
- 후속·연결
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) — 같은 슬라이딩 창으로 결과를 센다
  - [28-bulkhead](../28-bulkhead/2-summary.md) — 이미 들어온 요청의 자원을 나눈다
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 리키 버킷의 줄이 무제한일 때, 우선순위 셰딩
  - [api-design/14-rate-limit-and-quota-contracts](../../api-design/14-rate-limit-and-quota-contracts/2-summary.md)
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — Redis 원자 연산·스크립트의 다른 쓰임(락)
- 표준·글·문서
  - RFC 6585 §4 "429 Too Many Requests"(Retry-After MAY, 사용자 식별·계수 방법은 정하지 않음) <https://www.rfc-editor.org/rfc/rfc6585>
  - RFC 9110 §10.2.3 Retry-After(HTTP-date 또는 초) <https://www.rfc-editor.org/rfc/rfc9110>
  - IETF draft-ietf-httpapi-ratelimit-headers-11(초안) <https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/>
  - Paul Tarjan, "Scaling your API with rate limiters", Stripe 블로그 2017-03-30 — 네 종류(요청 속도·동시 요청·전체 사용량 셰더·워커 사용률 셰더), 토큰 버킷 + Redis, fail open, 끄는 스위치 <https://stripe.com/blog/rate-limiters>
  - nginx `ngx_http_limit_req_module` — leaky bucket, burst 기본 0, nodelay, `limit_req_status` 기본 503 <https://nginx.org/en/docs/http/ngx_http_limit_req_module.html>
  - Resilience4j RateLimiter 문서(주기·AtomicRateLimiter·SemaphoreBasedRateLimiter) <https://resilience4j.readme.io/docs/ratelimiter>
  - Redis `INCR` 문서 「Pattern: rate limiter」 1·2(초 단위 키 + MULTI/EXPIRE, 단일 카운터 race → Lua) <https://redis.io/docs/latest/commands/incr/>
  - Redis "Scripting with Lua"(스크립트 원자 실행) <https://redis.io/docs/latest/develop/programmability/eval-intro/>
- 실험 목록 (코드: scratchpad `rel/06/e11/`)
  - A 경계 2ms 사이 통과 수(고정 창 200 vs 나머지 100) — `Rl.java`, JDK 21, 가상 시계
  - B 아무 1초 구간 최대(로그 100, 카운터 189, 버킷 199, 고정 창 200) — 같은 파일
  - C Resilience4j 2.4.0 RateLimiter 기본값 + 주기 경계 200건 — 같은 파일, 실제 시계, 2회
  - D Redis 7.4.9 일회용 컨테이너 `sn-rl-w06-redis`(`--network none`): GET-후-INCR 105~110 vs INCR 반환값 100 vs Lua 100 — `race.sh`, 집필 3회 + 점검 3회
  - E Java 토큰 버킷 옛 판 vs 고친 판(150µs 간격 100초 766 vs 1099, 11일 유휴 뒤 0 vs 100) — `rel/fa-10/T.java`, JDK 21, 가상 시계
  - F 고친 Lua(스크립트 안 `TIME`, 가득 차는 시간 만료) — `rel/fa-10/tb.lua`, Redis 7.4.9 일회용 컨테이너 `sn-rl-a10-redis`(삭제함)
