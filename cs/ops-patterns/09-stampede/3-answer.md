# ops-patterns/09-stampede — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/ops-patterns/09-stampede/impl/`).

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 문제 (NaiveCache · SingleFlightCache · RefreshAheadCache 의 TODO)

#### 1. TODO 1 — NaiveCache.get

- 잠금을 걸면: 스탬피드가 안 일어나서 "막지 않으면 무슨 일이 벌어지는가"를 보여줄 수 없다 — 비교 기준선이 사라진다.

> **캐시 스탬피드(cache stampede)** — 인기 키의 캐시가 만료되는 순간 동시 요청이 전부 원본(DB)으로 몰리는 폭주.\
> 예: 동시 100개가 전부 빈 캐시를 보고 전부 loader 로 간다.

- 동시 100개 → loader **100번**.\
  전부 빈 캐시를 보고 전부 loader 로 간다.
- miss 만 세면: 싱글플라이트도 miss 는 100이라(캐시가 비어 있던 건 사실이니까) **막았는지 안 막았는지 구별이 안 된다.**

> **캐시 적중/미스(hit/miss)** — 캐시에 값이 있어서 바로 줌 / 없어서 원본에 가야 함.\
> 예: 나이브도 싱글플라이트도 miss 는 똑같이 100이다.

- 이 상자의 자: **peakConcurrentLoads** (동시에 loader 안에 있던 최대 개수) — 보조로 loads(호출 수).

> **peakConcurrentLoads** — 동시에 돌던 loader 의 최대 개수.\
> 예: 스탬피드를 보이게 하는 자다 — 100 vs 1 로 갈린다.

> **loader** — 캐시가 비었을 때 실제 값을 만들어 오는 비싼 함수(DB 조회 등).\
> 예: 이 상자가 세는 것이 이 함수의 호출 수다.

#### 2. TODO 2 — SingleFlightCache.get

정답 코드 골자 (impl/SingleFlightCache.java):

```java
Entry<V> found = map.get(key);
if (found != null && ticker.nowMillis() < found.expiresAt()) {
    hits.incrementAndGet();
    return found.value();
}
misses.incrementAndGet();

// 자리를 잡는다. 매핑 함수는 같은 키에 대해 한 번만 불린다.
boolean[] mine = {false};
CompletableFuture<V> promise = inFlight.computeIfAbsent(key, k -> {
    mine[0] = true;
    return new CompletableFuture<>();
});

if (!mine[0]) {                 // 남이 이미 잡았다. 그 결과를 기다린다.
    waits.incrementAndGet();
    return promise.get();       // (ExecutionException 이면 cause 를 꺼내 던진다)
}

int now = running.incrementAndGet();
peak.accumulateAndGet(now, Math::max);
try {
    loads.incrementAndGet();
    V value = loader.load(key);
    map.put(key, new Entry<>(value, ticker.nowMillis() + ttlMillis));   // 1. 값을 담는다
    promise.complete(value);
    return value;
} catch (Exception e) {
    promise.completeExceptionally(e);   // 2. 기다리던 쪽에도 실패를 알린다
    throw e;
} finally {
    running.decrementAndGet();
    inFlight.remove(key, promise);      // 3. 성공이든 실패든 자리를 비운다
}
```

- 한 연산의 실현: `inFlight.computeIfAbsent(key, ...)` — **같은 키에 대해 매핑 함수가 한 번만 불리는 것이 보장**되는 원자 연산이다.

> **computeIfAbsent** — 키가 없을 때만 매핑 함수를 딱 한 번 불러 넣어주는 원자 연산.\
> 예: 자리 잡기의 핵심이다.

> **싱글플라이트(single-flight)** — 같은 키의 계산을 동시에 하나만 날리고 나머지는 그 결과를 공유하는 기법.\
> 예: 대표 한 명이 물으러 가고 99명은 그 답을 받아 적는다.

- 나누면: A가 "계산 중인가?"\
  본다(없음) → B도 본다(없음) → A 표시 → B 표시 — 그 틈에 **둘 다** 자리를 잡아 둘 다 loader 로 간다.\
  아무것도 안 막은 것이다.
- ConcurrentHashMap 을 "쓰는 것"으로 안 되는 이유: 맵의 get 과 put 각각은 안전해도 **get 하고 put 하는 두 연산 사이**는 아무도 안 지켜준다.\
  원자성은 자료구조가 아니라 연산 단위의 문제다(06번 NonAtomicStore 와 같은 자리).
- 담는 것: 값이 아니라 **약속(CompletableFuture)** — "앞으로 값이 될 것".\
  자리를 잡는 시점엔 값이 아직 없기 때문이다.

> **약속(CompletableFuture)** — 나중에 채워질 값의 그릇.\
> 예: 자리 잡는 시점엔 값이 없어서 값 대신 이것을 담는다.

> **in-flight** — 지금 계산이 날아가는 중(진행 중)이라는 표시.\
> 예: `inFlight` 맵에 약속이 들어 있으면 누군가 계산 중이라는 뜻이다.

- 못 잡은 99개: `waits` 를 세고 `promise.get()` 으로 **그 하나의 결과를 기다린다.**\
  잠금을 직접 안 잡으니 계산 동안 맵 전체가 묶이지 않는다.
- 담당 판별: 매핑 함수 안에서 `mine[0] = true` 를 켠다 — 매핑 함수는 자리를 실제로 만든 스레드에서만 불리므로, mine 이 참인 하나만 계산 담당이다.
- 값을 map 에 안 담으면: 동시 요청은 약속으로 막히니 **스탬피드 테스트는 통과**한다.\
  그런데 다음(순차) 요청이 또 miss 라 **매번 DB 로 간다** — 싱글플라이트만 동작하고 캐시는 아무 일도 안 한다.\
  두 번 연속 호출하는 테스트가 따로 필요하다.
- 실패를 안 알리면: 99개가 채워지지 않을 약속을 들고 **영원히 기다린다.**\
  그게 더 나쁘다(README 생각해볼 것 3).
- 실패한 약속을 남기면: 그 뒤 모든 요청이 computeIfAbsent 에서 그 약속을 받아 **같은 실패를 영원히 받는다.**\
  원인이 사라져도 안 낫는다 — 캐시가 실패를 캐시하는 상태.

> **부정 캐시 사고(실패를 캐시)** — 실패한 약속이 맵에 남아 이후 모든 요청이 같은 실패를 받는 상태.\
> 예: 자리를 안 비워서 생긴다.

- 자리 비우기 위치: **finally** — 성공·실패 어느 경로로 빠져도 반드시 비워지는 블록.\
  `inFlight.remove(key, promise)` 로 내 약속일 때만 지운다.

#### 3. TODO 3 — RefreshAheadCache.get

정답 코드 골자 (impl/RefreshAheadCache.java):

```java
Entry<V> found = map.get(key);
long now = ticker.nowMillis();

if (found != null && now < found.expiresAt()) {
    hits.incrementAndGet();
    long age = now - found.createdAt();
    if (age >= (long) (ttlMillis * refreshAt)) {
        staleServed.incrementAndGet();   // 낡은 값을 줬다 — 파는 것의 양
        triggerRefresh(key);             // 뒤에서 갱신. 기다리지 않는다
    }
    return found.value();                // 어쨌든 지금 값을 준다
}

misses.incrementAndGet();
return loadNow(key);                     // 없거나 만료 — 싱글플라이트 방식으로
```

- 구간별 동작: 0~800ms 그냥 준다 / 800~1000ms **주면서** 뒤에서 갱신을 건다(아무도 안 기다린다) / 1000ms 이후 값이 없다 — loadNow 로 하나만 계산하고 나머지는 기다린다.

> **미리 갱신(refresh-ahead)** — 수명이 다 되기 전에(예: 80% 지점) 옛 값을 주면서 뒤에서 새 값을 받아두는 기법.\
> 예: 만료 직후의 기다림조차 없앤다.

> **TTL(time-to-live)** — 캐시 값의 수명.\
> 예: 지나면 만료다 — 여기서는 1000ms 다.

- 갱신을 기다리면: 결국 "만료 근처에서 한 명이 계산하고 나머지가 기다리는" 싱글플라이트와 같아진다 — 기다림을 없앤다는 존재 이유가 사라진다.
- 만료 뒤에 기다리는 이유: **줄 값이 아예 없다.**\
  낡은 값조차 없으면 기다리는 것 말고 방법이 없다.
- age = `now - found.createdAt()` — 지금 시각에서 값이 만들어진 시각을 뺀 것.\
  `age >= ttlMillis * refreshAt` 이면 갱신을 건다.

#### 4. TODO 4 — RefreshAheadCache.triggerRefresh

정답 코드 골자:

```java
boolean[] mine = {false};
CompletableFuture<V> promise = refreshing.computeIfAbsent(key, k -> {
    mine[0] = true;
    return new CompletableFuture<>();
});
if (!mine[0]) {
    return;     // 남이 이미 갱신 중이다. 기다리지 않고 옛 값을 준다
}
try {
    ... loader.load(key); map.put(...); promise.complete(value);
} catch (Exception e) {
    // 갱신 실패는 조용히 넘긴다. 옛 값이 아직 유효하기 때문이다.
    promise.completeExceptionally(e);
} finally {
    running.decrementAndGet();
    refreshing.remove(key, promise);
}
```

- 원자적으로 안 잡으면: 800ms 지점에 온 요청 100개가 **전부 갱신을 걸어** loader 100회 — 만료 시점의 스탬피드를 갱신 시점으로 **뒤로 옮긴 것**뿐이다.
- 기다리지 않는 이유: 부르는 쪽은 아직 유효한 옛 값을 받으면 된다 — **아무도 안 기다리는 게 이 구현의 요점**이다.
- 갱신 실패를 조용히: 옛 값이 아직 유효하므로 요청은 성공해야 한다 — 여기서 던지면 **멀쩡한 값을 들고도 요청이 실패한다.**\
  만료 뒤(loadNow)에는 줄 값이 없으므로 실패를 던진다 — **같은 실패도 자리에 따라 처리가 다르다.**

### B. 개념

#### 5. 캐시가 있어서 죽는다

- 과정: 평소엔 캐시가 다 받아줘 DB 는 초당 1회만 본다 → 인기 키 만료 → 그 키를 찾던 동시 요청 100개가 전부 빈 캐시를 보고 전부 DB 로 → DB 호출 순간 100회.
- 전제: **DB 용량이 "캐시가 받아준 뒤의 부하" 기준으로 잡혀 있다.**\
  캐시가 없었으면 애초에 DB가 그 부하를 감당하게 설계됐을 것이다 — 그래서 "캐시가 있어서 죽는다".
- 되먹임: DB가 느려지면 그 100개가 더 오래 걸리고, 끝나기 전에 또 100개가 쌓인다 — 폭주가 폭주를 키운다.

#### 6. 적중률만 보면 안 보인다

- miss 가 똑같은 이유: 두 구현 다 그 순간 **캐시가 비어 있던 건 사실**이라 100개 전부 miss 로 센다.\
  막았느냐는 miss 이후의 일이다.
- 세야 하는 것: **loads(loader 호출 수)** — 100 vs 1로 갈린다.
- peakConcurrentLoads 가 자인 이유: DB를 죽이는 건 총 호출 수보다 **동시에 몇 개가 들이닥치는가**다.\
  순간 폭주를 직접 재는 지표라 이 상자의 결론이 이 수다.

#### 7. 값이 아니라 약속을 담는다

- 이유: 자리를 잡는 순간엔 계산이 아직 안 끝나 값이 없다.\
  약속을 담으면 **자리 잡기(원자)와 계산(오래 걸림)을 분리**할 수 있다.
- 잠금 방식과 비교: loader 호출 전체를 synchronized 로 감싸면 계산하는 동안 **맵 전체(또는 그 키 접근 전체)가 묶인다.**\
  약속 방식은 잠금을 직접 안 잡아 다른 키는 그대로 흐르고, 기다리는 쪽도 그릇이 채워지길 기다릴 뿐이다.
- 06번과 같은 점: "있는지 본다"와 "넣는다"를 나누면 그 틈에 둘 다 들어간다 — **check-then-act 를 한 연산으로 합쳐야 한다**는 같은 교훈이다.

#### 8. 정상 경로를 통과하는 결함들

- "값을 안 담는다"가 통과하는 이유: 스탬피드 테스트는 **동시** 요청만 본다 — 동시 요청은 약속으로 막히므로 loads=1 이 나온다.\
  캐시 저장 여부는 그 테스트에 안 보인다.
- 잡는 테스트: **두 번 연속(순차) 호출** — 두 번째가 hit 이어야 하는데 매번 loader 로 가면 잡힌다.
- 실패 캐시가 제일 조용하고 오래 가는 이유: 예외는 나는데(요청은 실패로 응답) 캐시 코드 자체는 멀쩡해 보이고, **원인(DB 장애)이 복구돼도 낫지 않는다** — 실패한 약속이 맵에 남아 있는 한 영원히 그 실패를 준다.
- 살아남은 셋("값을 안 담는다"·"갱신 중에 기다린다"·"갱신 실패를 던진다")의 공통점: **정상 경로와 스탬피드 테스트를 그대로 통과한다** — 겨냥한 판별 테스트를 각각 따로 만들어야 잡힌다.

#### 9. 미리 갱신이 파는 것

- 싱글플라이트가 못 없앤 것: **기다림.**\
  99개는 여전히 한 명의 계산을 기다린다.\
  미리 갱신은 옛 값을 즉시 주므로 (만료 전이면) 아무도 안 기다린다.
- 파는 것: **신선함.**\
  수명 1000ms·refreshAt 0.8 이면 값이 **최대 200ms(수명의 20%) 낡을 수 있다.**\
  staleServed 가 그 양이다.

> **stale(낡은 값)** — 아직 유효하지만 곧 만료될, 최신이 아닐 수 있는 값.\
> 예: `staleServed` 가 그걸 준 횟수 — 이 구현이 파는 것의 양이다.

- 재고 수량에 안 되는 이유: 낡은 재고 수를 주면 없는 재고를 팔 수 있다 — 낡으면 안 되는 값이다.\
  무엇을 파는지 알고 사야 한다.
- "읽는 김에"인 이유: 갱신이 **읽기 경로에서만** 걸린다 — 800~1000ms 사이에 아무도 안 읽으면 그냥 만료된다.\
  진짜 미리 하려면 **백그라운드 스케줄러**가 필요하고 그게 10번이다.

#### 10. 연결

- 자리 잡기 원자성: **06-idempotency-store 의 NonAtomicStore** 와 정확히 같은 자리(check-then-act).
- 다음 챕터: **10-scheduler** — "읽는 김에"로 흉내낸 것을 진짜 백그라운드 작업으로 만든다.
- 문제의 전환: 06~08은 "**한 번만** 실행되게"(중복·실패 처리)였고, 09는 "**여럿이 같은 것을 원할 때** 같은 계산을 동시에 하지 않는" 문제다.

## 근거

- 기준 소스: `/home/jun/project/myway/ops-patterns/09-stampede/impl/NaiveCache.java`, `impl/SingleFlightCache.java`, `impl/RefreshAheadCache.java`
- 문제 원문: `src/main/java/com/ops/stampede/NaiveCache.java`(TODO 1), `SingleFlightCache.java`(TODO 2), `RefreshAheadCache.java`(TODO 3·4), `README.md` "특히 생각해볼 것" 1~8
