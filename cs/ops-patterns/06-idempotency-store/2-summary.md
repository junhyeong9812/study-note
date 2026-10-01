# ops-patterns/06-idempotency-store — 정리 (힌트)

## 해결하는 문제

재시도(01)는 "응답을 못 받으면 다시 보낸다"인데, 응답을 못 받았다고 실행이 안 된 것은 아니다.\
받는 쪽에 기억이 없으면 재시도는 곧 두 번 실행이다.

```text
기억 없음:  요청(−1000) --> 실행됨 --> 응답 유실 --> 재시도(−1000) --> 또 실행됨     잔액 −2000
기억 있음:  요청(키 A)  --> 실행됨, 장부에 A 기록 --> 응답 유실
            재시도(키 A) --> 장부에 A 있음 --> 실행 안 함, 저장한 응답만 재생        잔액 −1000
```

쉬운 예: 은행 창구의 접수증 — 직원 대답을 못 들었으면 "아까 3번 접수증 건 어떻게 됐어요?"라고 묻지, 송금을 다시 부탁하지 않는다.\
똑같은 구조다: 클라이언트가 요청마다 번호(키)를 붙이고, 서버는 키로 기록을 남겨 두 번째부터는 **처리 대신 답만 다시 준다**.\
실무 예: 결제 승인 API의 `Idempotency-Key`, 포인트 적립, 쿠폰 발급, 주문 생성 — 재시도가 있는 모든 쓰기.

### 한눈에 — 쉽게 말하면
**멱등성 키 = 접수증 번호.**

- 은행 창구에서 "송금해주세요" 했는데 직원 대답을 못 들었다고 하자.\
  다시 말하면 두 번 보내질까 봐 무섭다.\
  그래서 **접수증 번호**를 들고 가서 "아까 3번 접수증 건, 어떻게 됐어요?"라고 묻는다.

> **멱등성 키(idempotency key)** — 클라이언트가 요청마다 붙이는 고유 번호.\
> 예: 재시도는 같은 키를 다시 쓴다.

- 직원은 장부에서 3번을 찾아 "이미 처리했어요, 결과는 이거예요"라고 **처리를 다시 하지 않고 답만 다시 준다.**\
  똑같은 구조다.

> **멱등성(idempotency)** — 같은 요청을 여러 번 해도 효과는 한 번만 일어나는 성질.\
> 예: 같은 키로 두 번 와도 포인트는 한 번만 깎인다.

> **재생(replay)** — 실행을 다시 하지 않고 저장해둔 응답만 다시 돌려주는 것.\
> 예: 장부에서 3번 접수증을 찾아 그때 답을 그대로 준다.

- 왜 필요한가: **응답을 못 받았다 ≠ 실행이 안 됐다.**\
  포인트는 깎였는데 응답만 사라졌을 수 있다.\
  그 상태에서 재시도하면 두 번 깎인다(`AtLeastOnceTest` — 잔액이 9000이어야 하는데 8000).
- 네트워크가 보장할 수 있는 건 **at-least-once(최소 한 번)** 까지다.\
  **exactly-once(정확히 한 번)** 는 네트워크가 아니라 **받는 쪽이 기록으로 만든다.**\
  그 기록 장부가 멱등성 저장소다.

  > **at-least-once** — 요청이 최소 한 번은 도착하게 한다는 보장 — 대신 두 번 도착할 수도 있다.\
  > 예: 네트워크가 줄 수 있는 보장은 여기까지다.

  > **exactly-once** — 실제 효과(포인트 차감)는 정확히 한 번만 일어난다는 보장.\
  > 예: 네트워크가 아니라 받는 쪽이 기록으로 만든다.

```text
멱등성 없음:  요청 -> 실행(-1000) -> 응답 유실 -> 재시도 -> 또 실행(-1000)   두 번 깎임!
멱등성 있음:  요청(키=A) -> 실행(-1000), 장부에 기록 -> 응답 유실
              재시도(키=A) -> 장부에 A 있네? -> 저장해둔 응답만 재생          한 번만 깎임
```

실무 예: 스트라이프의 `Idempotency-Key` 헤더, 토스페이먼츠, GoCardless, AWS의 client token — 전부 이 모양이다.\
우연이 아니라 그것 말고 맞는 조합이 없다.

## 동작·원리

### 전체 흐름
```text
클라이언트가 키를 만든다  ->  같은 요청은 같은 키로 재시도한다
서버가 키로 기록을 남긴다 ->  이미 처리한 키면 저장해둔 응답을 그대로 돌려준다

IdempotentExecutor.execute(key, 지문, 작업) 의 네 갈래 판정:
  tryBegin 성공(자리 선점)      -> 실제로 실행 -> complete(응답 저장) -> 응답 반환
  기록 있음 + 지문이 다르다     -> KeyReuseException (같은 키, 다른 요청!)
  기록 있음 + COMPLETED         -> 저장된 응답 재생 (실행 안 함)
  기록 있음 + IN_PROGRESS       -> ConflictException (409 — 기다리지 않는다)
  기록 있음 + FAILED            -> 자리를 다시 잡으러 한 바퀴 더 돈다
```

> **지문(fingerprint)** — 그때 요청 내용이 무엇이었는지의 요약.\
> 같은 키로 다른 내용이 오는 것을 잡는다.\
> 예: 1000원 결제에 쓴 키로 50000원 결제가 오면 지문이 달라 걸린다.

### 설계 — 기록(IdempotencyRecord)에는 다섯 조각이 다 필요하다
**언제 쓰나**: "이미 했는지"만 기억하면 될 것 같지만, 그러면 재생을 못 한다.

```text
key             무엇에 대한 기록인가
state           IN_PROGRESS / COMPLETED / FAILED — 셋인 이유는 "지금 하는 중" 때문
response        끝났으면 뭐라고 답했는가. 이게 없으면 재생을 못 한다
fingerprint     그때 요청이 무엇이었는가
expiresAtMillis 언제까지 유효한가. 이게 없으면 저장소가 무한히 커진다
```

- `response`를 빼먹는 설계가 흔하다 — "이미 했다"까진 알아도 결제 승인번호를 재시도에 못 주면 클라이언트는 성공인지 실패인지 끝내 모른다.
- 기록은 **불변 객체**다.\
  상태가 바뀌면 새 기록을 만들어 통째로 갈아끼운다 — 필드를 제자리에서 바꾸면 다른 스레드가 절반만 바뀐 기록을 볼 수 있다.

  > **불변 객체(immutable)** — 만든 뒤엔 내용을 못 바꾸는 객체.\
  > 바꾸려면 새로 만든다.\
  > 예: 상태 전이는 새 객체로 갈아끼운다 — 절반만 바뀐 기록을 아무도 못 본다.

- 만료 판정은 `now >= expiresAt` — `>`로 쓰면 정확히 그 밀리초에 한 번 더 재생된다.\
  어느 쪽이든 "정한 대로"면 되지만, 안 정하면 구현마다 달라진다.

### 설계 — 처리 중일 때 또 오면: 기다리지 않는다
- 첫 요청이 아직 IN_PROGRESS인데 같은 키가 또 오면: 기다릴 것인가, 즉시 알릴 것인가.
- **대기는 자원을 잡는다.**\
  스레드가 묶이고, 몰리면 그 자체가 장애가 된다.\
  스트라이프는 **409 Conflict**를 즉시 준다 — 이 코드도 `ConflictException`을 던진다.

> **409 Conflict** — "지금 처리 중이니 나중에 다시 와라"는 HTTP 응답 코드.\
> 예: 대기 대신 즉시 알림이다.

## 쓰이는 자료구조·알고리즘

- **해시맵의 원자 갱신** — `ConcurrentHashMap.compute`가 "검사 + 기록"을 한 덩어리로 만든다. 해시맵 자체는 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), 원자성은 CAS가 아니라 락에서 온다 — `compute`는 그 키가 든 버킷(bin)의 첫 노드에 `synchronized`를 걸고 함수를 실행한다(빈 버킷이면 예약 노드를 꽂아 잠근다. OpenJDK `ConcurrentHashMap.compute` 소스). 그래서 함수 안에서 오래 걸리는 일을 하면 같은 버킷의 다른 키까지 막힌다.
- **조건부 삭제 `remove(key, value)`** — "내가 본 그 기록일 때만" 지운다. compare-and-delete로 스위퍼와 재선점의 경주를 막는다.
- **요청 지문(fingerprint)** — 요청 본문의 요약. 해시 함수로 만들면 [algorithm/27-string-hashing](../../algorithm/27-string-hashing/2-summary.md)의 재료다.
- **TTL + 스위퍼** — 만료 시각을 기록에 넣고 주기적으로 청소한다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)가 크기로 버리는 것을 여기서는 시간으로 버린다.
- **상태 기계** — IN_PROGRESS → COMPLETED / FAILED. FAILED만 재선점을 허용하는 전이 규칙이 본체다.
- **불변 레코드** — 상태가 바뀌면 새 객체로 갈아끼운다. 절반만 바뀐 기록을 아무도 못 보게 하는 기본 기법.
- 실제 시스템 — Stripe `Idempotency-Key` 헤더(TTL 24시간·409 Conflict), AWS API의 client token, Redis `SET key value NX EX ttl`(선점을 명령 하나로), Kafka idempotent producer(프로듀서 ID + 파티션별 시퀀스 번호로 브로커가 중복을 버린다 — KIP-98).

## 적용 — 풀어나가는 법

### 문제 — 이 챕터가 시키는 것
01번에서 배운 재시도에는 말하지 않은 전제가 있었다 — **응답을 못 받았다고 실행이 안 된 것이 아니다.**\
포인트는 깎였는데 응답만 유실됐으면 재시도가 두 번 깎는다(`AtLeastOnceTest`의 잔액이 9000이 아니라 8000).\
네트워크가 줄 수 있는 것은 at-least-once 까지이므로 **exactly-once 를 수신자 쪽 기록으로 만드는 저장소와 실행기를 구현하라**는 챕터다.\
그리고 일부러 틀린 나이브 버전을 **직접 써서** 그것이 몇 %로 깨지는지 본다.

과제(원본 README "하는 방법" — TODO 5개를 **번호 순서대로**, 1번 직후 `StoreAtomicityTest` 실행):

1. `NonAtomicStore` 의 **TODO 1** `tryBegin` — 일부러 두 단계(get 후 put)로 쓴다.\
   **고치지 마라** — 깨지는 것을 보는 용도다.
2. `InMemoryIdempotencyStore` 의 **TODO 2** `tryBegin` — 이 문제의 전부.\
   `compute` 로 판정과 쓰기를 한 연산에 넣고, 이겼는지는 **람다 안의 플래그**(`boolean[1]`)로 판정한다.

> **선점(tryBegin)** — "이 키는 내가 처리 중"이라고 자리를 먼저 잡는 것.\
> 예: 성공한 하나만 실행한다.

3. **TODO 3** `find` — 만료된 것은 없는 것으로 본다(지우지는 않는다).
4. **TODO 4** `purgeExpired` — 만료 기록을 지우되 `remove(key, value)` 로 "내가 본 그 기록일 때만" 지운다.
5. `IdempotentExecutor` 의 **TODO 5** `execute` — 네 갈래 판정(선점 성공 → 실행 / 지문 불일치 → `KeyReuseException` / COMPLETED → 응답 재생 / IN_PROGRESS → `ConflictException` / FAILED·빈 기록 → 한 바퀴 더).

먼저 읽을 것: `AtLeastOnceTest` — 이 문제가 왜 있는지가 거기 있다.\
시작점: `cd ~/project/myway/ops-patterns && ./run.sh 06` — 81개 중 71개가 실패하는 상태에서 출발한다(통과하는 10개는 미리 채운 생성자·인자 검증·`IdempotencyKey` 테스트다).

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

실제 시스템에 붙일 때의 순서: ① **키의 범위**를 정한다(전역이 아니라 사용자·테넌트 안에서 유일) → ② 지문에 넣을 필드를 정한다(의미 있는 값만, 요청 시각 같은 가변 필드는 제외) → ③ 선점을 원자 연산 하나로 만든다(`compute`·`SET NX`) → ④ 응답까지 저장한다 → ⑤ TTL을 **선택**한다 → ⑥ 처리 중 재요청의 계약(409)을 클라이언트와 합의한다.\
위 「문제」절의 TODO는 ③을 일부러 틀린 판부터 만들어 깨지는 것을 본 뒤 고친 판을 만든다.

## 장애 시나리오와 대처

아래 「실패」·「특히 생각해볼 것」·「한계」절이 다루는 것(동시 같은 키·지문 순서·FAILED 승격·키 생성 주체·소유권 토큰·저장과 작업의 비원자성) 말고, 운영에서 따로 보이는 장애들이다.

**1. 남의 키와 겹친다**

- 현상: 사용자 B가 결제를 했는데 사용자 A의 결제 결과를 받는다. 또는 멀쩡한 첫 요청이 `KeyReuseException`으로 거절된다.
- 보이는 형태: 저장소에 같은 키로 서로 다른 사용자의 기록이 충돌한다. 키 값이 `"1"`, `"order-123"`처럼 클라이언트 안에서만 유일한 값이다.
- 원인: 저장소의 키가 전역 하나인데, 클라이언트는 자기 범위에서만 유일한 값을 만든다. 서로 다른 클라이언트가 같은 문자열을 쓰면 같은 자리를 다툰다.
- 대처: 저장소 키를 `(사용자 또는 테넌트, 클라이언트 키)` 복합키로 만든다. 지문 검사는 그 안에서만 의미가 있다.
  - *테넌트(tenant)*: 한 시스템을 나눠 쓰는 고객 조직 단위.

**2. 정상 재시도가 지문 불일치로 거절된다**

- 현상: 네트워크 타임아웃 뒤의 정상 재시도가 전부 실패한다. 로그에 `KeyReuseException`이 폭증한다.
- 보이는 형태: 같은 키, 같은 금액인데 지문이 다르다. 본문에 `requestedAt`·nonce 같은 값이 들어 있다.
- 원인: 지문에 매 시도마다 바뀌는 필드를 넣었거나, 클라이언트가 재시도할 때 본문을 새로 만든다. 지문은 "같은 요청인가"를 묻는 것인데 "같은 시도인가"를 묻게 됐다.
- 대처: 지문은 의미 있는 필드만 정규화해 만든다(금액·대상·통화). 클라이언트는 요청 단위로 본문을 고정하고 재시도는 바이트 그대로 다시 보낸다.

**3. IN_PROGRESS 좀비가 키를 잠근다**

- 현상: 같은 키로 아무리 다시 보내도 TTL 내내 409 Conflict다. 실제로 결제가 됐는지는 아무도 모른다.
- 보이는 형태: 기록의 상태가 IN_PROGRESS인 채 몇 분째 안 바뀐다. 처리하던 서버는 그 사이 재시작됐다.
- 원인: 실행 중 프로세스가 죽어 `complete`도 `fail`도 못 불렀다. "기다리지 않는다" 설계는 옳지만, 주인이 사라진 자리를 되찾을 규칙이 없다(정답 12번의 한계와 같은 뿌리).
- 대처: IN_PROGRESS에는 작업 시간 상한만큼의 짧은 리스를 두어 그 뒤에는 재선점을 허용한다.\
  재선점하기 전에 실제 결과를 외부(PG·원장)와 대사해 확정한다 — 결과를 모르는 요청의 최종 경로는 대사다.
  - *리스(lease)*: 기한이 있는 소유권. 기한이 지나면 자동으로 풀린다.
  - *대사(reconciliation)*: 내 기록과 상대(PG·은행) 기록을 키로 맞춰 차이를 찾는 일.

### 실패 — 동시에 같은 키가 두 번 오면 (NonAtomicStore)
**언제 실패하나**: 같은 키의 요청 두 개가 거의 동시에 도착할 때.\
"검사"와 "기록" 사이에 틈이 있으면 둘 다 자기가 처음인 줄 안다.

전 상태 — 장부에 키 A 없음, 스레드 두 개가 동시에 진입:

```text
NonAtomicStore.tryBegin (get 후 put — 틈이 있다):

  스레드1: get(A) -> 없네            스레드2: get(A) -> 없네
           ---- 여기가 틈이다 ----
  스레드1: put(A), true 반환         스레드2: put(A), true 반환
                     둘 다 "내가 선점했다"고 믿는다 -> 둘 다 실행 -> 두 번 깎임
```

- **`NonAtomicStore`도 `ConcurrentHashMap`을 쓴다.**\
  get도 put도 각각은 원자적인데 **두 연산 사이가 아니다.**\
  "ConcurrentHashMap 썼는데요"는 답이 아니다.

> **TOCTOU(time-of-check to time-of-use)** — 검사한 시점과 실행한 시점 사이에 세상이 바뀌는 결함.\
> 예: get-후-put 의 틈이 그것이다.

  > **원자적(atomic)** — 중간에 끼어들 수 없는 한 덩어리 동작.\
  > 예: `compute` 가 검사 + 기록을 원자로 만든다.

- 그리고 이 나이브 버전이 **계약 테스트 22개를 전부 통과한다.**\
  순서대로 부르는 테스트로는 틈이 안 보인다 — QA가 아무리 빨리 눌러도 재현이 안 되는 이유다.

후 상태 — 고친 판(`InMemoryIdempotencyStore`)은 검사와 기록을 `compute` 한 번에 넣는다:

```text
compute(A, old -> {
    old 가 살아있고 FAILED 아니면 -> 그대로 둔다 (선점 실패)
    아니면                        -> IN_PROGRESS 새 기록 (선점 성공)
})                 검사+기록이 한 덩어리라 틈이 없다
```

**측정** (500회 경주 반복): compute 판은 승자가 둘 이상인 라운드 **0회**, get-후-put 판은 **17~53회**(3.4~10.6%, 한 라운드 최대 승자 4).

### 비용 — 기억의 대가 (TTL과 청소)
**무엇을 포기하나**: 요청 하나마다 기록 하나가 남는다.

```text
청소 안 함 (요청 1만 건):  보관 10000개, 그중 유효 99개   — 99%가 쓸모없는 기록
TTL + 주기적 청소:         보관 최대 198개, 유효 99개
```

- 재시도는 보통 몇 초 안에 온다.\
  그런데 스트라이프의 TTL은 24시간 — 계산이 아니라 **선택**이다.\
  길면 저장소가 커지고, 짧으면 그 뒤에 온 재시도가 두 번 실행된다.

  > **TTL(time-to-live)** — 기록을 얼마나 오래 유효하게 둘지의 기간.\
  > 예: 지나면 청소 대상이 된다 — 스트라이프는 24시간이다.

- 청소가 정확성을 깨면 안 된다: 만료된 자리를 스위퍼가 지우는 그 순간 남이 같은 자리를 잡을 수 있다(2000회 중 55~60회 재현) — 그래서 `purgeExpired`는 `remove(key, value)`로 "내가 봤던 그 기록일 때만" 지운다.

> **스위퍼(sweeper)** — 만료된 기록을 주기적으로 지우는 청소 루틴.\
> 예: `purgeExpired` 가 그 역할이다.

### 특히 생각해볼 것 (원본 README의 함정 3개)
- **지문 검사가 상태 판정보다 먼저다.**\
  1000원 결제에 쓴 키로 온 50000원 결제에 옛 응답을 주면 클라이언트는 50000원이 결제됐다고 믿는다.\
  로그도 안 남는다.
- **FAILED를 영구 기록으로 두면 일시 장애가 영구 실패로 승격된다.**\
  그래서 FAILED 자리는 재선점을 허용한다 — 판정을 어디서 하느냐가 함정이다.
- **키는 반드시 클라이언트가 만든다.**\
  서버가 만들면 재시도가 언제나 "처음 보는 키"라 저장소가 빈 껍데기가 된다(실행 2회, 재생 0회).\
  클라이언트가 만들어도 **시도마다** 새로 만들면 똑같다 — 키는 요청 단위지 시도 단위가 아니다.

### 한계 (이 구현이 고칠 수 없는 것)
- **소유권 토큰이 없다.**\
  만료된 자리를 남이 가져간 뒤 내가 뒤늦게 `complete` 하면 남의 자리에 내 응답을 쓸 수 있다.\
  펜싱 토큰이 필요하고, 이 문제집은 거기까지 안 간다.

> **펜싱 토큰(fencing token)** — "이 자리의 주인이 아직 나인가"를 증명하는 표.\
> 예: 이 구현엔 없다(한계 1).

- **응답 저장과 실제 작업이 원자적이지 않다.**\
  포인트는 깎였는데 `complete` 직전에 죽으면 기록이 IN_PROGRESS로 남는다 — 07-outbox가 이걸 정면으로 다룬다.

## 핵심 문장

- 응답을 못 받은 것과 실행이 안 된 것은 다르다 — 네트워크는 at-least-once까지고, **exactly-once는 수신자가 기록으로 만든다.**
- 키는 **클라이언트가, 요청 단위로** 만든다 — 서버가 만들거나 시도마다 바꾸면 저장소는 빈 껍데기다.
- 검사와 기록 사이에 틈이 있으면 동시 요청이 둘 다 이긴다 — `ConcurrentHashMap`을 써도 **두 연산 사이는 원자적이지 않다.**
- 지문 검사가 상태 판정보다 먼저다 — 같은 키에 다른 요청이 왔는데 옛 응답을 재생하면 조용히 틀린다.
- TTL은 계산이 아니라 선택이다 — 길면 저장소가 커지고, 짧으면 늦은 재시도가 두 번 실행된다.

## 관련 주제·근거

- 선행 — [01-retry-backoff](../01-retry-backoff/2-summary.md): 재시도의 말하지 않은 전제가 이 노트의 출발점이다.
- 후속 — [07-outbox](../07-outbox/2-summary.md): 응답 저장과 실제 작업의 비원자성(한계 2)을 기록과 발행을 한 트랜잭션에 묶어 다룬다.
- 후속 — [11-distributed-lock](../11-distributed-lock/2-summary.md): 소유권 토큰(펜싱 토큰)의 한계 1이 정면으로 나온다.
- 곁 — [04-rate-limiter](../04-rate-limiter/2-summary.md): 분산 카운터의 get-후-INCR가 같은 TOCTOU다.
- 곁 — [api-design/06-refund](../../api-design/06-refund/2-summary.md): 부분 환불 이중 처리 — 멱등 키가 필요한 자리의 실전 예.
- 영역 표 — [reliability/README.md](../../reliability/README.md) `13-idempotency`.
- 근거 — Stripe 문서 "Idempotent requests" · IETF draft `draft-ietf-httpapi-idempotency-key-header`(초안 — 아직 RFC 아님).
- myway 원본 — `/home/jun/project/myway/ops-patterns/06-idempotency-store/` (README.md · impl/InMemoryIdempotencyStore.java · impl/NonAtomicStore.java · impl/IdempotentExecutor.java · src/test/.../AtLeastOnceTest.java · StoreAtomicityTest.java).

### 관련 자료
- 챕터 안내: `/home/jun/project/myway/ops-patterns/06-idempotency-store/README.md`
- 출발점 테스트(문제의 존재 증명): `/home/jun/project/myway/ops-patterns/06-idempotency-store/src/test/java/com/ops/idempotency/AtLeastOnceTest.java`
- 계약·값 객체: `.../src/main/java/com/ops/idempotency/IdempotencyStore.java`, `IdempotencyKey.java`, `IdempotencyRecord.java`, `RecordState.java`
- 정답 기준 소스: `/home/jun/project/myway/ops-patterns/06-idempotency-store/impl/InMemoryIdempotencyStore.java`, `impl/NonAtomicStore.java`, `impl/IdempotentExecutor.java`
- 테스트: `.../src/test/java/com/ops/idempotency/StoreAtomicityTest.java`(경주), `StoreGrowthTest.java`(보관량), `IdempotencyStoreContractTest.java`, `IdempotentExecutorTest.java`, `RandomOperationTest.java`
- 이웃 주제: `../../debugging/02-toctou-idempotency`(같은 주제를 진단으로), `../../debugging/06-retry-duplication`(소비자 쪽), 다음 챕터 `07-outbox`(기록과 발행을 원자적으로)

### 용어 풀이
- **멱등성(idempotency)**: 같은 요청을 여러 번 해도 효과는 한 번만 일어나는 성질.
- **멱등성 키(idempotency key)**: 클라이언트가 요청마다 붙이는 고유 번호.\
  재시도는 같은 키를 다시 쓴다.
- **at-least-once / exactly-once**: 최소 한 번 도착(중복 가능) / 효과는 정확히 한 번.\
  네트워크는 전자까지만 준다.
- **재생(replay)**: 실행을 다시 하지 않고 저장해둔 응답만 다시 돌려주는 것.
- **지문(fingerprint)**: 요청 내용의 요약.\
  같은 키로 다른 내용이 오는 오용을 잡는다.
- **TOCTOU(time-of-check to time-of-use)**: 검사한 시점과 실행한 시점 사이에 세상이 바뀌는 결함.\
  get-후-put의 틈.
- **원자적(atomic)**: 중간에 끼어들 수 없는 한 덩어리 동작.\
  `compute`가 검사+기록을 원자로 만든다.
- **선점(tryBegin)**: "이 키는 내가 처리 중"이라고 자리를 먼저 잡는 것.\
  성공한 하나만 실행한다.
- **409 Conflict**: "지금 처리 중이니 나중에 다시 와라"는 HTTP 응답 코드.\
  대기 대신 즉시 알림.
- **TTL(time-to-live)**: 기록의 유효 기간.\
  지나면 청소 대상.
- **스위퍼(sweeper)**: 만료된 기록을 주기적으로 지우는 청소 루틴.
- **펜싱 토큰(fencing token)**: "이 자리의 주인이 아직 나인가"를 증명하는 표.\
  이 구현엔 없다(한계 1).
- **불변 객체(immutable)**: 만든 뒤 내용을 못 바꾸는 객체.\
  상태 전이는 새 객체로 갈아끼운다.
