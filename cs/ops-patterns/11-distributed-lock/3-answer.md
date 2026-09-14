# ops-patterns/11-distributed-lock — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/ops-patterns/11-distributed-lock/impl/`).

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 문제 (NaiveLock · LeaseLock · FencedStore 의 TODO)

#### 1. TODO 1·2 — NaiveLock

정답 코드 (impl/NaiveLock.java):

```java
// TODO 1
String previous = holders.putIfAbsent(key, owner);   // putIfAbsent 는 원자적이다. 여기까지는 맞다
if (previous != null) return Optional.empty();
acquired.incrementAndGet();
// 만료가 없다. 그래서 사실상 영원한 증서다.
return Optional.of(new Lease(key, owner, nextToken.incrementAndGet(), Long.MAX_VALUE));

// TODO 2
// 소유자를 안 본다. 아무나 아무거나 푼다.
return holders.remove(lease.key()) != null;
```

- 만료가 없으면: 잡은 놈이 죽어도 **24시간 뒤에도 A가 들고 있다** — 락이 영원히 안 풀려 작업이 아예 안 돈다.
- 소유자를 안 보면: **아무나 남의 락을 푼다** → A와 B가 같이 일하는데 **예외도 로그도 없다.** 락은 "풀렸다 다시 잡혔다"로만 보이니까 조용하다.
- 시끄러운 쪽/조용한 쪽: 만료 없음 사고는 시끄럽다(작업이 안 도니 바로 보인다), 소유자 없음 사고는 조용하다(둘이 같이 일해도 아무 신호가 없다).
- putIfAbsent 가 맞는 부분: **잡기 자체는 원자적**이다 — 이 기준선의 결함은 원자성이 아니라 만료·소유자 검사의 부재다.

#### 2. TODO 3 — LeaseLock.tryAcquire

정답 코드 (impl/LeaseLock.java):

```java
attempts.incrementAndGet();
long now = ticker.nowMillis();

// 한 연산이다. 보고 쓰는 사이가 없다.
Lease result = leases.compute(key, (k, current) -> {
    if (current != null && !current.isExpiredAt(now)) {
        return current;         // 남이 유효하게 들고 있다. 그대로 둔다
    }
    if (current != null) {
        expiredTakeovers.incrementAndGet();
    }
    return new Lease(k, owner, nextToken.incrementAndGet(), now + ttlMillis);
});

if (!result.owner().equals(owner) || result.isExpiredAt(now)) {
    return Optional.empty();
}
acquired.incrementAndGet();
return Optional.of(result);
```

- 결과가 제일 나쁜 이유: 06번은 중복 처리, 09번은 중복 계산이지만 여기서 깨지면 **상호 배제 그 자체가 깨져 둘이 같이 일한다** — 락이 지키려던 유일한 것이 무너진다.
- 한 연산의 실현: `leases.compute(key, ...)` — "만료됐나 본다"와 "내 것으로 표시한다"가 매핑 함수 안에서 한 번에 일어난다. 보고 쓰는 사이가 없다.
- 한 번으로 안 잡히는 이유: 보기와 쓰기 사이의 창이 **너무 좁아서** 한 번의 실행으로는 거의 안 겹친다. 그래서 테스트가 **500 라운드**를 돌려 확률을 쌓는다.
- 토큰이 매번 커지는 이유: **커지는 것이 계약**이다. 그래야 저장소(FencedStore)가 "낡은 점유의 쓰기"를 크기 비교만으로 가려낼 수 있다. 같은 소유자의 재획득도 새 점유이므로 커져야 한다.

#### 3. TODO 4 — LeaseLock.release

정답 코드:

```java
boolean[] removed = {false};
leases.computeIfPresent(lease.key(), (k, current) -> {
    if (current.owner().equals(lease.owner()) && current.token() == lease.token()) {
        removed[0] = true;
        return null;            // 지운다
    }
    return current;
});
return removed[0];
```

- 이름만 보면 뚫리는 시나리오: **같은 이름으로 재기동한 프로세스**(또는 만료 후 같은 owner 가 다시 잡은 경우)가 **옛 증서**로 release 를 부르면, 이름이 같아서 지금의(남의/새) 점유를 풀어버린다.
- 토큰까지 보면: 옛 증서의 토큰과 현재 점유의 토큰이 다르므로 걸린다 — 토큰이 점유의 정체성이다.
- 던지지 않는 이유: **만료된 뒤 finally 에서 놓으려는 것이 정상 경로**이기 때문이다. 작업이 오래 걸려 락이 만료되고 남이 가져간 뒤에도, 원래 주인은 finally 에서 release 를 부른다 — 거기서 던지면 부르는 쪽이 finally 안에서 예외를 또 다뤄야 한다. 아무 일도 안 하고 false 가 맞다.
- 정상 경로인 이유: `try { 작업 } finally { release }` 는 락 사용의 표준 꼴이고, 만료는 언제든 일어날 수 있는 정의된 상황이지 오류가 아니다.

#### 4. TODO 5·6 — renew / currentHolder

정답 코드:

```java
// renew
leases.computeIfPresent(lease.key(), (k, current) -> {
    if (!current.owner().equals(lease.owner()) || current.token() != lease.token()) {
        return current;         // 내 것이 아니다
    }
    if (current.isExpiredAt(now)) {
        return current;         // 이미 만료됐다. 되살리지 않는다
    }
    // 토큰은 그대로다. 같은 점유의 연장이기 때문이다.
    renewed[0] = new Lease(k, current.owner(), current.token(), now + ttlMillis);
    return renewed[0];
});

// currentHolder
Lease current = leases.get(key);
if (current == null || current.isExpiredAt(ticker.nowMillis())) {
    return Optional.empty();
}
return Optional.of(current);
```

- 만료된 것을 되살리면: 그 사이에 남이 잡았을 수 있다 — 되살리는 순간 **둘이 같이 들게 된다.**
- 갱신이 토큰을 올리면: 저장소가 보기에 **새 점유와 구별이 안 된다.** 낡은 놈의 토큰보다 커져버리면, 펜싱이 막아야 할 "락 잃은 놈의 쓰기"가 통과할 수 있다 — 갱신은 같은 점유의 연장이므로 토큰은 그대로여야 한다.
- currentHolder 가 만료를 안 보면: **대시보드·운영 도구가 그 값을 보여주고 사람이 그걸 믿고 판단한다** — 이미 만료된 소유자를 "지금 들고 있다"고 거짓말하게 된다.
- 안 잡히는 이유: 정작 tryAcquire 는 만료를 제대로 보고 잘 도니까 **기능 테스트 어디서도 안 걸린다** — 조회 전용 경로의 거짓말이다.

#### 5. TODO 7 — FencedStore.write

정답 코드 (impl/FencedStore.java):

```java
Long seen = lastToken.get(key);
if (seen != null && token < seen) {
    // 낡은 토큰이다. 이 쓰기는 락을 잃은 놈이 보낸 것이다.
    rejected.add(key + "@" + token + "(현재 " + seen + ")");
    return false;
}
values.put(key, value);
lastToken.put(key, token);
writes++;
return true;
```

- 락이 못 막는 시나리오: A가 락을 잡음(수명 10초) → A가 **GC로 15초 멈춤** → 락 만료 → B가 잡음 → A가 깨어나 **아직 자기 락이라 믿고** 씀 → A와 B가 동시에 쓴다.
- 쓰기 직전 확인이 소용없는 이유: **확인과 쓰기 사이에 또 멈출 수 있다.** 그 창을 쓰는 쪽에서는 없앨 방법이 없다 — A는 자기가 멈췄다는 것을 알 수 없다.
- 받는 쪽으로 옮기면 창이 사라지는 이유: 저장소 안에서는 **검사와 쓰기가 한 연산**이다(사이에 끼어들 틈이 없다). A는 끝까지 락 잃은 줄 몰라도 쓰기가 튕긴다.
- 같은 토큰을 막으면: **같은 점유가 갱신하며 여러 번 쓰는** 정상 작업이 못 돈다 — 오래 걸리는 작업이 아예 불가능해진다. 그래서 **작을 때만** 막는다.
- 거절 목록의 의미: 비어 있지 않다 = **실제로 두 놈이 같이 일했다는 증거** — 락만 보면 안 보이는 사실이 저장소에 기록으로 남는다.

### B. 개념

#### 6. 셋이 반드시 있어야 한다

- 만료: 잡은 놈이 죽어도 언젠가 풀리게 한다(영구 정지 방지). 소유자(+토큰): 남이 내 락을 못 풀게 한다(조용한 동시 진입 방지). 토큰: **락이 풀린 줄 모르는 놈의 쓰기**를 저장소가 막게 한다.
- 양립: 사고는 전부 "잡은 놈이 죽거나 멈추는" 비정상 상황에서만 터진다 — 평소(정상 경로)에는 셋 다 없어도 잘 돈다. 그래서 조용히 깨진다.
- synchronized 로 안 되는 이유: 그것은 **한 프로세스 안**의 합의다. 두 대의 프로세스는 메모리를 공유하지 않으므로 바깥의 공유 저장소(락 서버)를 통해 합의해야 한다.

#### 7. 잡기의 원자성

- 공통의 자리: **check-then-act** — "본다"와 "표시한다"를 나누면 그 틈에 둘 다 들어간다(06 NonAtomicStore, 09 inFlight, 11 leases).
- 제일 나쁜 이유: 06은 중복 처리, 09는 중복 계산으로 끝나지만 여기서는 **상호 배제 자체가 깨진다** — 정산이 두 번 돌고 돈이 두 번 나간다.
- 한 라운드에서 살아남은 것: 창이 좁아 확률적으로만 터진다 — 06번의 **"QA가 아무리 빨리 눌러도 재현이 안 된다"** 와 같은 현상. 그래서 500 라운드다.

#### 8. 만료와 갱신의 긴장

- 짧으면: 작업이 끝나기 전에 만료돼 남이 가져간다(expiredTakeovers 증가, 둘이 같이 일할 위험). 길면: 잡은 놈이 죽었을 때 그 긴 시간 동안 아무도 못 잡아 작업이 멈춘다. (뒷문장은 원본 서술의 대우 — 내 추론 포함)
- expiredTakeovers 가 크면: **수명이 짧거나 작업이 느린 것**이다(impl 주석 그대로).
- 거절 횟수가 0이 아니면: **실제로 둘이 같이 일했다**는 뜻 — 수명을 늘리거나 **작업을 쪼개야 한다**는 신호다.

#### 9. 펜싱 토큰의 설계

- 두 규칙: ① **작으면 거절** — 낡은 점유(락 잃은 놈)의 쓰기를 막는다. ② **같으면 통과** — 같은 점유의 연속 쓰기(갱신하며 여러 번)는 정상이므로 막으면 안 된다.
- 창이 없는 이유: 검사(`token < seen`)와 쓰기(`values.put`)가 저장소 안의 **한 연산 안**에서 일어난다 — 쓰는 쪽의 "확인 후 쓰기"처럼 사이에 멈출 수 있는 틈이 없다.
- 역할 분담: 락은 **효율**을 준다 — 대부분의 경우 한 놈만 일하게 해서 낭비·충돌을 줄인다. 펜싱은 **정확성**을 지킨다 — 락이 뚫리는 드문 순간(GC 멈춤)에도 데이터가 안 깨지게 한다. 락 없이 펜싱만 있으면 맞긴 한데 다들 일하고 나서 튕긴다. (원본에 근거 없음 — 내 추론; 원본은 "락으로는 못 막는 것을 저장소가 막는다"까지 서술)

#### 10. 연결

- 10번과의 연결: 스케줄러를 **두 대에 띄우면 같은 작업이 두 번 도는** 문제 — 그 "한 대만"을 만드는 것이 분산 락이다.
- 12번으로: 여기서는 **먼저 잡은 놈이 이겼다**(누가 잡아도 상관없음). 리더 선출은 **누가 그 한 대인가**의 선택이 안정적이어야 한다 — 락의 확장이다.
- Redis SET NX PX: `NX`(없을 때만) = 원자적 잡기(compute/putIfAbsent 자리), `PX ttl` = 만료. 값에 소유자를 넣고 Lua 로 검사하며 지우는 것이 release 의 소유자+토큰 검사 자리다. (원본 서머리의 실무 예 — 세부 대응은 내 추론)

## 근거

- 기준 소스: `/home/jun/project/myway/ops-patterns/11-distributed-lock/impl/NaiveLock.java`, `impl/LeaseLock.java`, `impl/FencedStore.java`
- 계약: `src/main/java/com/ops/dlock/DistributedLock.java`, `Lease.java`
- 문제 원문: `src/main/java/com/ops/dlock/` 의 TODO 1~7, `README.md` "특히 생각해볼 것" 1~9
