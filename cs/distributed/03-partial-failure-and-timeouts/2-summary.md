# distributed/03-partial-failure-and-timeouts — 부분 실패, "모름"이라는 세 번째 결과, 타임아웃 고르기 — 정리 (힌트)

## 해결하는 문제

원격 호출의 결과는 성공·실패 둘이 아니라 **셋**이다.

```text
  로컬 호출                         원격 호출
  ──────────                        ─────────────────────────────
  성공 ─ 반환값                      성공 ─ 응답을 받았다
  실패 ─ 예외                        실패 ─ 오류 응답을 받았다(예: 400, 잔액 부족)
                                    모름 ─ 응답을 못 받았다(타임아웃·연결 끊김)
                                          → 상대는 했을 수도, 안 했을 수도 있다
```

- *부분 실패(partial failure)*: 시스템의 일부가 예측할 수 없게 고장 난 상태. 핵심은 **비결정적**이라는 것이다. 같은 일을 해도 어떤 때는 되고 어떤 때는 안 된다. 됐는지조차 모를 수 있다(DDIA 1판 8장).
- *타임아웃(timeout)*: 일정 시간 뒤 기다림을 포기하는 것. 포기했다고 상대가 요청을 안 받았다는 뜻은 아니다(같은 장).

이 셋째 결과를 "실패"로 처리하면 데이터가 어긋나고, 덮어놓고 재시도하면 일이 두 번 된다.

쉬운 예: 택배 반품을 접수하려고 고객센터에 전화했다. "접수하겠습니다" 하는 순간 전화가 끊겼다.
- 접수가 됐나? 다시 전화해서 "반품 접수해 주세요"라고 하면 두 건이 될 수도 있다.
- 다시 전화해서 "**주문번호 123** 반품 접수 됐나요?"라고 물으면 안전하다.

똑같은 구조다.\
"모름"은 **같은 요청임을 알아볼 표식(멱등 키)**과 **나중에 확인하는 길(조회·대사)**로 다룬다.\
그리고 "얼마나 기다리고 포기할지(타임아웃)"는 측정으로 정한다.

실무 예:
- PG 승인 API가 타임아웃 났다. 주문은 "결제 실패"로 표시했는데 고객 카드는 결제됐다. 고객이 다시 결제해 두 번 빠졌다.
- DB 헬스 체크 타임아웃을 짧게 잡았더니, 잠깐 느려진 주 DB를 죽었다고 판단해 페일오버했다. 옛 주 DB에는 아직 복제되지 않은 쓰기가 남아 있었다(예시. 짧은 끊김이 페일오버로 이어진 실제 사례는 장애 2의 GitHub).

이 노트는 기존 노트 [ops-patterns/failure-at-scale](../../ops-patterns/failure-at-scale/2-summary.md)의 「양상 1 — 부분 실패가 정상 상태가 된다」를 이어받는다. 원본은 "규모가 크면 장애가 사건이 아니라 배경이 되므로 분포(p50·p99)로 관제한다"는 운영 관점을 다룬다. 여기서는 그 아래층, **호출 하나의 결과를 모르는 상태**와 타임아웃 선택을 다룬다.
- 참고: 원본 「어느 양상이 실제로 걸리는지 세라」의 "양상 1(부분 실패 정상화)은 진짜 대규모에서만 치명적이다"는 "장애를 분포로 관제해야 하는 상황"에 대한 말이다. 호출 하나의 결과를 모르는 부분 실패는 노드 둘 사이에서도 생긴다. DDIA 8장은 "노드가 몇 개뿐인 작은 시스템에서도 부분 실패를 고려하는 것이 중요하다"고 쓴다.

## 동작·원리

### 1. 응답이 없는 여섯 경우와 "모름"

```text
  호출자 A                              피호출자 B
  ① 요청 ──X                                          B는 모른다       → 안 함
  ② 요청 ──[대기]──────────────→ 처리                늦게 받아 처리   → 나중에 함
  ③ 요청 ───────────────────→ ✝                      B가 죽음          → 안 함
  ④ 요청 ───────────────────→ (멈춤) … 처리           멈췄다 처리      → 나중에 함
  ⑤ 요청 ───────────────────→ 처리 ── 응답 X          응답 유실         → 이미 함
  ⑥ 요청 ───────────────────→ 처리 ── 응답 [대기]     응답 지연         → 이미 함
            ↑
     A의 타임아웃은 여기서 울린다. A가 아는 것: "아직 응답 없음"
```

- 01번 그림을 "B가 일을 했나" 관점으로 다시 본 것이다.
- ①·③만 "안 함"이 확실하다. ②·④는 **타임아웃 뒤에** 일이 일어날 수 있다. ⑤·⑥은 이미 일어났다.
- MIT 6.5840 L2(RPC) 노트도 같은 결론이다. 클라이언트는 서버가 요청을 봤는지 모른다. 서버가 처리하고 응답 직전에 죽었을 수도, 응답이 네트워크에서 사라졌을 수도 있다.

### 2. "모름"을 다루는 세 가지 길

```text
               타임아웃 = 모름
           ┌──────────┼──────────────────┐
           ▼          ▼                  ▼
   (a) 같은 요청을    (b) 결과를          (c) 나중에 양쪽 기록을
       다시 보낸다       물어본다             맞춰 본다(대사)
       + 멱등 키        GET /payments/{키}   외부 정산 파일 ↔ 내부 원장
           │          │                  │
   "두 번 보내도      "했나?"에 답할       "결국 어느 쪽이
    한 번만 한다"      조회 API가 필요     맞나"를 확정
```

- (a) *재시도 + 멱등 키*: 요청마다 고유 키를 붙이고, 서버는 키별 첫 결과를 저장했다가 같은 키가 오면 저장된 결과를 돌려준다.
  - *멱등(idempotent)*: 여러 번 해도 한 번 한 것과 결과가 같은 성질.
  - Stripe API 문서: 키별로 첫 요청의 상태 코드와 본문을 저장하고, 같은 키의 후속 요청에는 같은 결과를 돌려준다. 성공·실패와 무관하다. 키는 최대 255자이고, 24시간 이상 지난 키는 지울 수 있다. 같은 키에 파라미터가 다르면 오류를 낸다. 단, 결과는 엔드포인트 실행이 시작된 뒤에만 저장한다 — 파라미터 검증 실패나 **같은 키로 동시에 실행 중인 요청과 충돌**한 경우는 저장하지 않고, 다시 보내도 된다고 적는다(아래 실험 A의 서버처럼 "앞 요청이 끝나길 기다려 같은 결과를 준다"는 Stripe의 동작이 아니다).
  - HTTP 헤더 표준화는 IETF httpapi WG 초안 `draft-ietf-httpapi-idempotency-key-header`로 시도됐다. 2026-10-01 기준 마지막 판은 -07이고 datatracker 상태는 "Expired"(2026-04 만료)다. RFC가 되지 않았다.
- (b) *조회로 확인*: 키나 거래 ID로 상태를 물어본다. 상대가 조회 API를 줘야 한다.
- (c) *대사(reconciliation)*: 내부 기록과 외부 기록을 키로 맞춰 차이를 찾는다. 타임아웃으로 결과를 모르는 요청의 **최종 확정 경로**다.

### 3. 타임아웃은 얼마로? — 측정이 답이다

```text
  응답 시간 분포 (살아 있는 서버)
   건수
    │█
    │██
    │████
    │██████▇▅▃▂▁ ▁    ▁                 ▁
    └──────┬──────┬─────────┬──────────────→ 지연
          p50    p99      p99.9          최대
           ↑      ↑         ↑
  여기서 끊으면 → 살아 있는 서버의 응답 중 이만큼을 "모름"으로 만든다
                    50%        1%       0.1%
```

- DDIA 8장: 지연 상한 d가 보장되고 처리 시간 상한 r이 보장되면 타임아웃은 `2d + r`이면 된다. 그러나 비동기 네트워크에는 그런 상한이 없다.
- 그래서 **실험으로** 정한다. 여러 기계에서 오래 RTT 분포를 재고, "장애를 늦게 아는 비용"과 "살아 있는 상대를 죽었다고 보는 비용"을 비교한다(DDIA 8장 "Network congestion and queueing").
- 더 나은 방법은 응답 시간과 흔들림(jitter)을 계속 재서 타임아웃을 자동으로 맞추는 것이다. 예: TCP 재전송 타이머(network/16)는 RTT를 재서 맞춘다.
- 같은 생각을 **노드 장애 탐지**에 쓴 것이 φ accrual 탐지기(02번)다. 이것은 RPC 응답 시간이 아니라 **하트비트 도착 간격** 분포로 "저 노드가 죽었나"의 의심 정도를 낸다.

| 타임아웃이 | 좋은 점 | 나쁜 점 |
|---|---|---|
| 짧다 | 고장을 빨리 안다, 스레드를 빨리 돌려받는다 | 살아 있는 상대를 죽었다고 본다 → 중복 실행, 불필요한 페일오버, 이미 바쁜 노드들에 짐 이전 → 연쇄 장애(DDIA 8장) |
| 길다 | 오판이 적다 | 사용자가 오래 기다린다, 스레드·연결을 오래 쥔다 |

### 실험 A: 타임아웃이 났는데 서버에서는 결제가 됐다

서버는 결제를 마친 뒤 1.5초 있다가 응답한다(⑥ 응답 지연). 클라이언트 타임아웃은 1초, 최대 3번 시도한다.

```java
// 서버: 멱등 키가 있으면 키별 첫 결과(진행 중이면 그 Future)를 공유한다
CompletableFuture<String> mine = new CompletableFuture<>();
CompletableFuture<String> prev = byKey.putIfAbsent(key, mine);       // 원자적으로 "처음인가"를 정한다
if (prev == null) { mine.complete(doCharge()); body = mine.join(); }  // 처음: 실제 결제
else body = prev.join() + " (같은 키의 저장된 결과 재사용)";           // 재시도: 기다렸다 같은 결과

// 클라이언트: 1초 타임아웃, 최대 3번
HttpRequest.Builder b = HttpRequest.newBuilder(uri).timeout(Duration.ofMillis(1000))
        .POST(HttpRequest.BodyPublishers.ofString("amount=10000"));
if (key != null) b.header("Idempotency-Key", key);
```

(실험, Temurin 21.0.12, `com.sun.net.httpserver` 서버와 `java.net.http` 클라이언트를 한 프로세스에서, 2026-10-01)

```text
== 1) 멱등 키 없이: 타임아웃 1초, 최대 3번 시도 (서버는 결제 후 1.5초 뒤 응답)
   시도 1: 1012 ms 뒤 타임아웃 → 결과 모름, 재시도
   시도 2: 1000 ms 뒤 타임아웃 → 결과 모름, 재시도
   시도 3: 1000 ms 뒤 타임아웃 → 결과 모름
   포기: 클라이언트는 '실패'로 기록했다
   서버에서 실제 결제된 횟수 = 3
== 2) 멱등 키 order-42: 같은 조건
   시도 1: 1000 ms 뒤 타임아웃 → 결과 모름, 재시도
   시도 2: 523 ms 뒤 성공 → charged #1 (같은 키의 저장된 결과 재사용)
   서버에서 실제 결제된 횟수 = 1
== 3) 멱등 키 + 타임아웃 3초(서버 처리시간보다 길게)
   시도 1: 1504 ms 뒤 성공 → charged #1
   서버에서 실제 결제된 횟수 = 1
```

- 관찰
  - 1): 클라이언트 기록은 "실패", 서버 기록은 "결제 3번". 기록이 정반대로 어긋났다. 이것이 커리큘럼 ⚠의 **"타임아웃 났는데 실제론 성공 → 재시도로 중복 결제"**다.
  - 2): 같은 키의 두 번째 시도는 첫 결제가 끝나기를 기다렸다가 같은 결과를 받았다(523 ms). 결제는 1번.
  - 3): 타임아웃을 처리 시간보다 길게 잡으면 첫 시도에 성공했다. 타임아웃 선택과 멱등 키는 서로를 대신하지 않는다. 둘 다 필요하다.
- 한계: 이 서버는 키를 메모리 맵에 둔다. 실제로는 결제 기록과 같은 트랜잭션으로 DB에 유일 제약을 걸어 저장해야 서버 재시작·다중 인스턴스에서도 막힌다([ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)).

### 실험 B: 실제 왕복 분포로 타임아웃 후보 비교

같은 호스트 Docker 브리지에서 Redis에 `PING` 2만 번을 보내 왕복 시간을 쟀다. 그리고 타임아웃 후보마다 "살아 있는 서버인데 타임아웃이 났을" 건수를 셌다.

(실험, Temurin 21.0.12 컨테이너 → Redis 7.4.9 컨테이너, 2026-10-01)

```text
PING 20000회 왕복(µs): 평균 35 | p50 28 | p90 51 | p99 123 | p99.9 290 | 최대 2182
  타임아웃 = 평균×2   (   70 µs) → 살아 있는 서버에 대한 오탐 800건 / 20000 (4.00%)
  타임아웃 = p99    (  123 µs) → 살아 있는 서버에 대한 오탐 200건 / 20000 (1.00%)
  타임아웃 = p99.9  (  290 µs) → 살아 있는 서버에 대한 오탐 19건 / 20000 (0.10%)
  타임아웃 = 최대×2   ( 4364 µs) → 살아 있는 서버에 대한 오탐 0건 / 20000 (0.00%)
```

- 관찰
  - 분포의 꼬리가 길다. 최대(2182 µs)가 p50(28 µs)의 약 78배다.
  - "평균의 2배"는 그럴듯해 보이지만 이 실행에서 살아 있는 서버의 요청 4%를 "모름"으로 만들었다. 그 4%가 재시도되면 부하도 4% 늘어난다. 사실 점검 때 다시 돌린 세 번은 5.6~8.1%였다(꼬리 모양에 따라 달라진다).
  - p99로 잡으면 정의상 약 1%가 타임아웃이다. 호출이 여러 단계로 이어지면 단계마다 1%씩 쌓인다(계산).
  - 값은 실행마다 다르다. 다시 돌렸을 때 p99 153 µs, p99.9 519 µs, 최대 1806 µs였다. 사실 점검 때 다시 돌린 세 번은 p99 176~373 µs, p99.9 390~1631 µs였다(호스트 부하가 클 때 더 컸다). 꼬리가 길다는 경향과 p99=1.00%·p99.9=0.10%는 같았다.
- 해석: 타임아웃은 "고장 판정"이 아니라 **"살아 있는 상대의 응답 중 몇 %를 모름으로 만들지"의 선택**이다. 그 비율과 모름 처리 비용(재시도·조회·대사)을 같이 정한다.

### 4. 타임아웃은 층마다 있고, 바깥이 더 길어야 한다

```text
  사용자 ─ 게이트웨이(3 s) ─ 주문 서비스(2 s) ─ 결제 서비스(1.5 s) ─ PG
            바깥이 길고 ───────────────────────→ 안쪽이 짧다
  거꾸로면: 게이트웨이가 3 s에 포기했는데 안쪽은 5 s까지 일한다 → 결과를 받을 사람이 없는 헛일
```

- 층별 타임아웃 정렬과 데드라인(절대 시각) 전파는 [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md)에 자세하다.
- DB 쪽 타임아웃(`statement_timeout` 등)은 [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **멱등 키 저장소**: 키 → (상태: 진행 중/완료, 저장된 응답, 요청 해시). 동시에 같은 키가 오면 **원자적 삽입**(`putIfAbsent`, DB 유일 제약) 하나만 이기게 한다. 만료 시각을 두고 청소한다.
- **백분위 계산**: 정렬 배열(실험 B), 운영에서는 고정 버킷 히스토그램(예: HdrHistogram, Prometheus histogram)으로 근사한다.
- **지수 백오프 + 지터**: 재시도 간격을 2배씩 늘리고 무작위를 섞는다([ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md)).
- **데드라인**: 상대 시간 대신 절대 만료 시각을 요청에 실어 나른다. 남은 예산 = 만료 − 지금(단조 시계로 잰 경과를 빼서 전파하면 시계 어긋남을 피한다 — 04번).
- **대사**: 내부·외부 기록을 키로 정렬 병합해 누락·중복·불일치를 분류한다.
- **φ accrual**: 하트비트 도착 간격 분포로 노드 장애의 의심 정도를 낸다(02번).

## 적용 — 풀어나가는 법

1. **호출의 결과를 셋으로 모델링한다.** `SUCCEEDED`·`FAILED`·`UNKNOWN`. 타임아웃·연결 끊김은 `UNKNOWN`이다.
2. **바꾸는 호출에는 멱등 키를 붙인다.** 키는 업무 키(주문 ID + 시도 목적)에서 만들거나 UUID를 만들어 **재시도 전에 저장**해 둔다. 재시도할 때 새 키를 만들면 의미가 없다.
3. **`UNKNOWN`을 확정하는 경로를 만든다.** 조회 API로 재확인, 안 되면 대사 배치로 확정.
4. **타임아웃을 분포에서 고른다.** p99·p99.9를 재고, 오탐 비율과 대기 비용을 비교한다. 층마다 바깥이 더 길게.
5. **재시도에 상한을 둔다.** 횟수·전체 예산·백오프·지터. 재시도가 부하를 키우지 않게.

```java
enum Outcome { SUCCEEDED, FAILED, UNKNOWN }

Outcome charge(Order order) {
    String key = order.paymentIdempotencyKey();            // 주문 생성 때 만들어 DB에 이미 저장해 둔 키
    for (int attempt = 1; attempt <= 3; attempt++) {
        try {
            HttpResponse<String> r = client.send(chargeRequest(order, key, Duration.ofSeconds(3)), ofString());
            if (r.statusCode() == 200) return Outcome.SUCCEEDED;
            int sc = r.statusCode();
            if (sc / 100 == 4 && sc != 408 && sc != 409 && sc != 429)
                return Outcome.FAILED;                              // 거절(예: 400, 잔액 부족) — 재시도해도 같다
        } catch (HttpTimeoutException | ConnectException e) {
            // 모름: 같은 키로 다시 보낸다(서버가 키로 중복을 막는다)
        }
        sleepWithJitter(attempt);
    }
    paymentRepo.markUnknown(order.id(), key);              // 실패로 단정하지 않는다 → 조회·대사가 확정
    return Outcome.UNKNOWN;
}
```

- 4xx라고 모두 확정 실패는 아니다. RFC 9110 §15.5: 408은 클라이언트가 요청을 다시 보내도 되고, 409는 충돌을 풀고 다시 낼 수 있다. 429(RFC 6585)는 잠시 뒤 재시도하라는 뜻이다. 위 코드는 이 셋을 재시도로 돌린다. 나머지 4xx의 의미는 상대 API 문서로 확인한다.
- 5xx를 받은 경우는 서비스마다 의미가 다르다. 처리 도중 실패일 수 있으므로 `UNKNOWN`처럼 다루는 편이 안전하다(멱등 키로 재시도).
- `ConnectException`은 연결 자체가 안 된 것이라 요청이 안 갔을 가능성이 크다. 그래도 같은 키로 재시도하면 안전하다.

진단 명령·지표:
- 지연 분포: 하류 호출별 히스토그램(p50·p99·p99.9)과 타임아웃 횟수를 같은 대시보드에 둔다.
- 구간별 시간: `curl -o /dev/null -s -w 'connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total}\n' <url>`
- 중복 탐지: `SELECT idempotency_key, count(*) FROM payments GROUP BY 1 HAVING count(*) > 1;`(유일 제약이 없을 때 사후 확인용)
- `UNKNOWN` 적체: `SELECT count(*) FROM payments WHERE status = 'UNKNOWN' AND created_at < now() - interval '10 minutes';`

## 장애 시나리오와 대처

### 1. 타임아웃을 실패로 보고 재시도 → 중복 결제 (⚠ 커리큘럼)

- **현상**: 고객 카드가 두 번(또는 세 번) 결제됐다. 내부 주문은 "결제 실패" 하나뿐이다.
- **보이는 형태**: 결제사 정산 파일에 같은 금액·같은 카드 승인이 몇 초 간격으로 여러 건. 내부 로그에는 `HttpTimeoutException` 뒤 재시도 로그.
- **원인**: 응답 지연(⑥)·응답 유실(⑤)인데 실패로 단정하고, 멱등 키 없이 다시 보냈다(실험 A의 1: 클라이언트 "실패", 서버 "3번 결제").
- **대처**: 바꾸는 호출에 멱등 키, 재시도에도 같은 키. 타임아웃은 `UNKNOWN`으로 기록하고 조회·대사로 확정. 이미 난 중복은 대사로 찾아 환불.

### 2. 너무 짧은 타임아웃 → 오탐 페일오버 (⚠ 커리큘럼)

- **현상**: 주 DB가 잠깐 느려졌거나 짧게 끊겼을 뿐인데 자동 페일오버가 일어났다. 옛 주 DB의 복제 안 된 쓰기가 갈 곳을 잃는다.
- **보이는 형태**: 페일오버 로그, 옛 주 DB와 새 주 DB 양쪽에만 있는 쓰기, 복구에 수작업.
- **실제 사례(GitHub 2018-10-21 사고 보고서 원문)**: 22:52 UTC, 장비 교체 작업으로 미국 동부 네트워크 허브와 동부 주 데이터센터 사이 연결이 끊겼다. 연결은 **43초 만에** 복구됐다. 그러나 그 사이 MySQL 토폴로지를 관리하는 Orchestrator(Raft로 합의)가 서부 데이터센터로 페일오버를 진행했다. 동부에는 서부로 복제되지 않은 몇 초 분량의 쓰기가 남았고, 서비스 저하는 **24시간 11분** 이어졌다.
  - 보고서의 원인 진술: Orchestrator는 "설정된 대로" 동작했지만, 애플리케이션 계층은 리전을 넘는 주 DB 승격(대륙 횡단 지연)을 감당하지 못했다. 후속 조치도 "리전 경계를 넘는 승격을 막도록 Orchestrator 설정 조정"이다. 보고서는 탐지 타임아웃이 짧았다고 하지 않는다.
  - 해석: 43초 끊김만으로 되돌리기 어려운 페일오버가 시작될 수 있었고, 그 순간 짧은 장애가 긴 복구로 바뀌었다. 탐지 문턱만이 아니라 "페일오버가 어디로, 무엇을 대가로 일어나나"를 함께 봐야 한다.
- **원인**: 일반적으로는 탐지 타임아웃이 실제 지연·단절 분포의 꼬리보다 짧은 경우다. GitHub 사례에서는 페일오버 설정(리전 간 승격)과 애플리케이션이 감당할 수 있는 토폴로지가 어긋났다. 어느 쪽이든 페일오버는 되돌리기 어려운 작업이다.
- **대처**: 탐지 문턱을 측정으로 고른다(실험 B). 페일오버 대상(리전 등)을 애플리케이션이 감당할 수 있는 범위로 제한한다. 되돌리기 어려운 동작(페일오버·데이터 이동)은 더 긴 문턱이나 사람 확인을 둔다. 페일오버 뒤 옛 주인의 쓰기를 막는 펜싱(02·12번).

### 3. 짧은 타임아웃 + 재시도 → 부하 증폭

- **현상**: 하류가 조금 느려지자 요청 수가 오히려 늘고 결국 하류가 쓰러진다.
- **보이는 형태**: 하류 요청률이 상류 요청률의 몇 배. 타임아웃 비율과 재시도 비율이 같이 오른다.
- **원인**: 타임아웃이 꼬리 지연보다 짧으면 살아 있는 응답이 "모름"이 되고(실험 B: 평균×2면 실행에 따라 4~8%), 그만큼 재시도가 붙는다. 느려질수록 더 많이 재시도한다.
- **대처**: 재시도 예산·지수 백오프·지터·서킷 브레이커. 원본 [failure-at-scale](../../ops-patterns/failure-at-scale/2-summary.md) 「양상 2」와 [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md).

### 4. 타임아웃 계층 역전 → 아무도 안 받는 헛일

- **현상**: 사용자는 이미 오류를 봤는데 안쪽 서비스와 DB는 계속 일한다. 부하가 실제 요청보다 크다.
- **보이는 형태**: 게이트웨이 504와 동시에 안쪽에서 수 초 뒤 "완료" 로그. DB에 클라이언트가 떠난 쿼리.
- **원인**: 안쪽 타임아웃이 바깥보다 길다. 취소가 전파되지 않는다.
- **대처**: 바깥 > 안쪽 정렬, 데드라인 전파, DB `statement_timeout`([ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md), [database/22](../../database/22-database-side-timeouts/2-summary.md)).

### 5. 멱등 키를 붙였는데도 중복

- **현상**: 멱등 키가 있는데도 두 번 처리된 건이 나온다.
- **보이는 형태**: 같은 키가 저장소에 두 줄, 또는 키는 다른데 내용이 같은 요청 두 건.
- **원인**
  - 재시도할 때 키를 새로 만들었다.
  - "조회 후 없으면 삽입"이라 동시에 온 두 요청이 둘 다 "없음"을 봤다(원자적 삽입이 아님).
  - 처리 결과와 키 기록을 다른 트랜잭션으로 썼다. 사이에서 죽으면 기록 없이 처리만 남는다.
  - 키 보존 기간이 재시도 기간보다 짧다(Stripe는 24시간 이상 지난 키를 지울 수 있다고 명시한다).
- **대처**: 키는 재시도 전에 만들어 저장, 유일 제약으로 원자적 삽입, 결과와 키를 같은 트랜잭션에, 보존 기간 ≥ 최대 재시도 기간.

## 핵심 문장

- 원격 호출의 결과는 성공·실패·모름 셋이다. 타임아웃은 "실패"가 아니라 "모름"이다.
- 모름은 같은 요청을 알아보는 멱등 키, 결과를 묻는 조회, 양쪽 기록을 맞추는 대사로 다룬다.
- 실험에서 멱등 키 없는 재시도는 클라이언트 "실패" vs 서버 "결제 3번"을 만들었고, 멱등 키는 이를 1번으로 줄였다.
- 타임아웃은 "살아 있는 상대의 응답 중 몇 %를 모름으로 만들지"의 선택이다. 고정 공식이 아니라 지연 분포를 재서 정한다.
- 너무 짧으면 오탐 페일오버·중복·부하 증폭, 너무 길면 대기와 자원 점유. 되돌리기 어려운 동작일수록 문턱을 길게.

## 관련 주제·근거

- 선행
  - [02-system-and-failure-models](../02-system-and-failure-models/2-summary.md) — 느린 것과 죽은 것, φ accrual
  - [01-why-distributed-and-fallacies](../01-why-distributed-and-fallacies/2-summary.md) — 응답이 없는 여섯 경우
- 기존 노트(이어받음)
  - [ops-patterns/failure-at-scale](../../ops-patterns/failure-at-scale/2-summary.md) — 양상 1 부분 실패의 상시화, 양상 2 재시도 증폭
- 후속·연결
  - reliability 영역 [05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)·[07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md)·[08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md)·[13-idempotency](../../reliability/13-idempotency/2-summary.md). 05·13은 아래 ops-patterns 노트로 이어진다
  - [ops-patterns/deadline-propagation](../../ops-patterns/deadline-propagation/2-summary.md) · [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md) · [ops-patterns/01-retry-backoff](../../ops-patterns/01-retry-backoff/2-summary.md) · [ops-patterns/failure-modes](../../ops-patterns/failure-modes/2-summary.md)(F-16 타임아웃 계층 역전, F-20 이중 결제)
  - [network/16-tcp-reliability-retransmission](../../network/16-tcp-reliability-retransmission/2-summary.md) — RTT를 재서 재전송 타이머를 맞추는 같은 생각
  - [database/22-database-side-timeouts](../../database/22-database-side-timeouts/2-summary.md)
  - [25-impossibility-results](../25-impossibility-results/2-summary.md) — 두 장군: 왜 "모름"을 없앨 수 없나
- 근거
  - DDIA 1판 8장 "Faults and Partial Failures", "Unreliable Networks" — "Detecting Faults", "Timeouts and Unbounded Delays"(2d + r, 실험으로 고르기, 연쇄 장애), "Network congestion and queueing"
  - MIT 6.5840 Spring 2026 Lecture 2 노트 "RPC problem: what to do about failures?" <https://pdos.csail.mit.edu/6.824/notes/l-rpc.txt>
  - Stripe API Reference "Idempotent requests" <https://docs.stripe.com/api/idempotent_requests>
  - IETF 초안 "The Idempotency-Key HTTP Header Field", draft-ietf-httpapi-idempotency-key-header-07(Expired) <https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/>
  - GitHub, "October 21 post-incident analysis"(2018-10-30 게시) <https://github.blog/news-insights/company-news/oct21-post-incident-analysis/>
  - Java SE 21 API `HttpRequest.Builder.timeout`
- 실험 목록
  - `TimeoutRetry.java` — 결제 후 1.5초 뒤 응답하는 서버에 1초 타임아웃·3회 재시도(멱등 키 없음/있음/타임아웃 3초). Temurin 21.0.12, 한 프로세스 안 HTTP 서버·클라이언트.
  - `LatencyDist.java` — Redis 7.4.9(`sn-dw-redis`)에 `PING` 2만 회, 백분위와 타임아웃 후보별 오탐 수. 같은 호스트 Docker 브리지. 키는 만들지 않음.
