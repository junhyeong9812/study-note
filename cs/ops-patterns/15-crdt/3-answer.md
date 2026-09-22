# ops-patterns/15-crdt — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 절·번호와 1:1 대응. 질문 하나 = A 하나. -->

### A. 문제 (구현 대상: NaiveCounter TODO 1 · GCounter TODO 2\~4 · OrSet TODO 5\~8)

#### 1. NaiveCounter — merge (TODO 1, 기준선)

**정답 코드** (impl/NaiveCounter.java):

```java
public NaiveCounter merge(NaiveCounter other) {
    // 더한다. 교환법칙과 결합법칙은 성립하는데 멱등성이 없다.
    return new NaiveCounter(value + other.value);
}
```

- **merge 는 무엇을 하고 왜 "고치지 마라"인가?**\
  → 두 값을 그냥 더한다.\
  이 클래스는 정답이 아니라 **기준선**이다 — "멱등성이 없으면 무슨 일이 벌어지는가"를 보여주는 역할이라 고치면 챕터의 비교 대상이 사라진다.
- **있는 성질 둘 / 없는 하나?**\
  → 더하기라서 교환법칙(`a+b = b+a`)과 결합법칙은 성립한다.\
  **멱등성(`merge(a,a) = a`)이 없다** — `a+a = 2a`.\
  앞의 둘만 있어서 얼핏 보면 문제가 없어 보이는 것이 함정.

> **멱등성(idempotency)** — 같은 것을 두 번 합쳐도 결과가 안 변한다. 중복 수신을 무해하게 만드는 성질.\
> 예: `merge(a,a) = a` 여야 하는데 더하기는 `a+a = 2a` 다.

- **한 번 8, 두 번 13?** → merge(3,5) = 8. 같은 B=5 가 또 오면(at-least-once 중복) 8+5 = 13. 같은 것을 또 받았을 뿐인데 늘었다 — 멱등성 부재의 직접 증상.

> **at-least-once(적어도 한 번)** — 메시지가 최소 한 번은 가지만 여러 번 갈 수도 있는 전달 보장. 중복이 정상이라는 뜻.\
> 예: 같은 B=5 가 또 오면 8 이 13 이 된다.

- **그물에서 A의 1이 B에서 2?** →

```
      A(1)
     /    \
    B       C          A 의 상태 1 이 B 로도 직접 오고, C 를 거쳐서도 온다
     \     /
      B 가 두 경로로 받음:  1 + 1 = 2     <- A 는 1만 세었다
```

  같은 정보가 두 경로로 도착했는데 더하기는 그걸 구별 못 하고 두 번 더한다.

> **그물 전파(mesh/gossip)** — 노드들이 서로서로 상태를 주고받는 모양. 같은 정보가 여러 경로로 도착한다.\
> 예: A의 1이 B로도 직접 오고 C를 거쳐서도 와서 B에서 2가 된다.

- **왜 조용한가?**\
  → 예외가 안 난다.\
  타입도 맞고 연산도 성공한다.\
  사고는 **값이 조금씩 큰 것**으로만 나타나고, 어디서 늘었는지 추적할 정보(누가 얼마나 세었는지)를 안 들고 있어서 원인도 못 찾는다.
- **맞게 동작하는 전제?**\
  → 메시지가 **순서대로, 정확히 한 번씩만** 오면 실제로 맞다.\
  분산에서는 그 전제가 성립하지 않는다 — 07번에서 본 대로 중복 발행은 없앨 수 없고(at-least-once 가 최선), 그물 전파에서는 같은 상태가 여러 경로로 온다.

#### 2. GCounter — increment / value / merge (TODO 2\~4)

**정답 코드** (impl/GCounter.java):

```java
public GCounter increment(String node, long amount) {
    if (amount < 0) {
        // 음수를 허용하면 max 합치기가 무너진다.
        throw new IllegalArgumentException("늘기만 하는 카운터다. 음수는 못 넣는다: " + amount);
    }
    Map<String, Long> next = new LinkedHashMap<>(counts);   // TODO 2: 새 상태
    next.merge(node, amount, Long::sum);
    return new GCounter(next);
}

public long value() {
    long total = 0;
    for (long each : counts.values()) {
        total += each;                                      // TODO 3: 읽기는 합
    }
    return total;
}

public GCounter merge(GCounter other) {
    Map<String, Long> next = new LinkedHashMap<>(counts);
    for (Map.Entry<String, Long> e : other.counts.entrySet()) {
        next.merge(e.getKey(), e.getValue(), Math::max);    // TODO 4: 합치기는 max
    }
    return new GCounter(next);
}
```

- **왜 칸을 나누는가?**\
  → 숫자 하나로는 합칠 방법이 없다 — A 가 8 이고 B 가 5 일 때 답이 8인지 13인지 5인지 알 수 없다.\
  **누가 얼마나 세었는지**를 안 들고 있기 때문이다.\
  칸을 나누면 각 칸이 "그 노드가 센 횟수"라는 뜻을 갖고, 그때 비로소 max 가 맞는 합치기가 된다.

> **GCounter(Grow-only Counter)** — 늘기만 하는 카운터. 노드마다 칸, 합치기는 max, 읽기는 합.\
> 예: `{A=3, B=5}` 를 읽으면 8 이다.

- **원본을 고치면 안 되는 이유?**\
  → 고치면 `merge(a,b)` 를 부른 뒤 `a` 가 달라진다.\
  그러면 `merge(a,b)` 와 `merge(b,a)` 를 같은 입력으로 두 번 부를 수 없어 **교환법칙을 확인할 방법이 없어진다.**\
  그래서 increment/merge 모두 새 객체를 반환한다(불변).

> **교환법칙(commutativity)** — 합치는 순서를 바꿔도 결과가 같다.\
> 예: `merge(a,b)` 와 `merge(b,a)` 를 같은 입력으로 두 번 불러 확인한다.

- **음수를 막는 이유?**\
  → "A 가 3 을 뺐다"(칸이 내려감)를 max 로 합치면 상대가 든 옛 큰 값이 이겨서 **빼기가 합치는 순간 사라진다.**\
  늘기만 한다는 전제가 max 합치기의 정당성이다.\
  빼기가 필요하면 PNCounter(GCounter 둘).

> **PNCounter** — 늘기 칸과 줄기 칸, GCounter 둘을 붙여 빼기를 흉내낸 것.\
> 예: 빼기가 필요하면 GCounter 를 둘 쓴다.

- **합치기는 max, 읽기는 합?**\
  → 각 칸의 뜻이 "그 노드가 센 횟수"라서다.\
  합칠 때는 같은 노드 칸에 대해 더 최신 정보(더 큰 값)를 고르는 것이므로 max 가 맞고, 전체 값을 읽을 때는 모든 노드가 센 횟수를 모으는 것이므로 합이 맞다.
- **더하면?**\
  → 같은 상태를 두 번 받았을 때 두 배가 된다 — 나이브 카운터와 똑같아진다.\
  07번 아웃박스의 중복 발행이 그대로 사고가 된다.
- **같은 칸을 두 번 받아도 안 느는 근거?**\
  → `max(x, x) = x`.\
  max 자체가 멱등이라, merge 전체도 멱등이 된다.
- **벡터 시계와의 차이?**\
  → 자료 모양(`{노드=수}` + merge는 칸마다 max)은 같고 **읽는 법**만 다르다.\
  벡터 시계는 칸들을 비교해서 순서(BEFORE/AFTER/CONCURRENT)를 말했고, GCounter 는 칸들을 더해서 값을 말한다.

#### 3. OrSet — add / remove / elements / merge (TODO 5\~8)

**정답 코드** (impl/OrSet.java):

```java
public OrSet<T> add(String node, T element) {
    OrSet<T> next = new OrSet<>(added, removed, nextTag + 1);   // TODO 5: 새 태그
    next.added.computeIfAbsent(element, k -> new TreeSet<>())
            .add(node + ":" + (nextTag + 1));
    return next;
}

public OrSet<T> remove(T element) {
    Set<String> visible = added.get(element);
    if (visible == null || visible.isEmpty()) {
        return this;        // 없는 것을 빼는 것은 아무 일도 아니다
    }
    OrSet<T> next = new OrSet<>(added, removed, nextTag);
    next.removed.computeIfAbsent(element, k -> new TreeSet<>()).addAll(visible);
    return next;            // TODO 6: 지금 보이는 태그만 지움 목록에
}

public Set<T> elements() {  // TODO 7
    Set<T> out = new LinkedHashSet<>();
    for (Map.Entry<T, Set<String>> e : added.entrySet()) {
        Set<String> gone = removed.getOrDefault(e.getKey(), Set.of());
        for (String tag : e.getValue()) {
            if (!gone.contains(tag)) { out.add(e.getKey()); break; }
        }
    }
    return Set.copyOf(out);
}

public OrSet<T> merge(OrSet<T> other) {   // TODO 8
    Map<T, Set<String>> mergedAdded = deepCopy(added);      // 넣은 태그 합집합
    /* ... other.added 를 전부 addAll ... */
    Map<T, Set<String>> mergedRemoved = deepCopy(removed);  // 지운 태그 합집합
    /* ... other.removed 를 전부 addAll ... */
    // 태그 번호도 큰 쪽을 따라간다. 안 그러면 합친 뒤 넣기가 옛 태그를 다시 쓴다.
    return new OrSet<>(mergedAdded, mergedRemoved, Math.max(nextTag, other.nextTag));
}
```

```
관찰한 것만 지운다 : 동시 넣기/빼기에서 넣기가 이기는 이유

  A 가 사과를 넣는다        added:   사과 {A:1}
  B 가 그것을 보고 뺀다     removed: 사과 {A:1}        <- B 가 "본" 태그는 A:1 뿐
  A 가 사과를 또 넣는다     added:   사과 {A:1, A:2}

  merge -> added 사과 {A:1, A:2}, removed 사과 {A:1}
        -> A:2 는 안 지워졌다 -> 사과는 있다
```

- **집합이 어려운 이유?**\
  → A 가 넣고 B 가 뺐을 때 합집합으로 합치면 뺀 것이 되살아나고, 교집합으로 합치면 넣은 것이 사라진다.\
  **넣기와 빼기 중 무엇이 이길지**를 자료구조가 규칙으로 정해야 하고, 그 선택이 이름이 된다(Observed-Remove = 넣기 승).

> **OrSet(Observed-Remove Set)** — "관찰한 것만 지우는" 집합. 동시 넣기/빼기에서 넣기가 이긴다.\
> 예: B 가 본 태그가 `A:1` 뿐이면 나중에 들어온 `A:2` 는 안 지워진다.

- **태그가 고유하지 않으면?**\
  → 같은 번호를 두 번 쓰면 나중 넣기가 앞의 넣기와 구별이 안 된다.\
  앞의 태그를 관찰하고 지운 빼기가 **나중 넣기까지 지운다** — "관찰한 것만 지운다"는 전제가 거짓이 된다.

> **태그(tag)** — 넣기 한 번마다 붙는 고유 표식(`A:1`). 고유하지 않으면 관찰 기록이 거짓이 된다.\
> 예: A 가 사과를 두 번 넣으면 태그가 `A:1`, `A:2` 로 갈린다.

- **원소 자체를 지우면 안 되는 이유?**\
  → 뺀 기록(어떤 태그를 보고 뺐는지)이 안 남는다.\
  그러면 뒤늦게 합쳐질, 빼기가 본 적 없는 새 넣기까지 같이 사라진다.\
  태그 단위로 지워야 "본 것만" 지울 수 있다.
- **없는 원소 remove?** → 아무 일도 아니다 — `this` 를 그대로 반환한다(보이는 태그가 없으니 지울 것도 없다).
- **"있다" 판정?**\
  → 그 원소의 넣은 태그 중 **지워지지 않은 것이 하나라도 있으면** 있다.
- **지움 목록을 안 합치면?**\
  → 남이 지운 기록이 내 복제본에 없으니, 합친 결과에서 남이 지운 원소가 되살아난다.\
  넣기만 합치면 그냥 합집합 집합이 되어 빼기가 무력화된다.
- **태그 번호도 max 를 따라가야 하는 이유?**\
  → 안 따라가면 합친 뒤 add 할 때 상대가 이미 쓴 번호를 다시 쓴다.\
  그 태그는 이미 지움 목록에 있을 수 있어 **새로 넣었는데 아무 일도 안 일어난다.**\
  이 사고는 오래된 복제본(작은 nextTag)에 새 상태를 합친 뒤에만 드러난다.
- **동시 넣기/빼기?**\
  → 넣기가 이긴다.\
  B 가 A1 을 지우는 사이 A 가 A2 를 넣었다면 B 는 A2 를 본 적이 없으므로 못 지운다.\
  버그가 아니라 **정해진 규칙**이다 — 다른 규칙(빼기 승)을 원하면 다른 자료구조를 써야 한다.

### B. 개념

#### 4. 세 성질 — 무엇을 사면 무엇이 공짜인가

- **세 성질?**\
  → 교환법칙 `merge(a,b) = merge(b,a)`(순서를 바꿔도 같다), 결합법칙 `merge(merge(a,b),c) = merge(a,merge(b,c))`(묶는 법을 바꿔도 같다), 멱등성 `merge(a,a) = a`(같은 것을 또 받아도 안 변한다).
- **셋이 있으면?**\
  → 메시지가 **순서 없이(교환·결합), 중복돼서, 여러 번 와도(멱등)** 모든 복제본이 같은 결과에 도달한다.
- **07·08 연결?**\
  → 07번 아웃박스의 중복 발행(at-least-once 라 중복은 못 없앤다)과 08번 사가의 보상 재시도가 멱등성 덕에 공짜로 무해해진다 — 같은 상태가 두 번 와도 결과가 같으니까.
- **멱등만 없으면?**\
  → 나이브 카운터의 모습 — 예외 없이, 값이 조금씩 큰 것으로만 나타나는 조용한 사고.\
  교환·결합이 성립해서 단순 테스트는 다 통과한다.

#### 5. 한계 — 무엇이 안 되는가

- **왜 못 줄이는가?**\
  → 합치기가 max 라서다.\
  칸을 내려도 상대 복제본이 들고 있던 옛 큰 값과 합쳐지는 순간 max 가 옛 값을 되살린다.\
  한 번 올라간 칸은 절대 안 내려간다.
- **빼기가 필요하면?**\
  → GCounter 둘을 붙인 PNCounter — 늘기 칸과 줄기 칸을 따로 세고 읽을 때 차를 구한다.
- **지운 태그를 영원히 드는 이유?**\
  → 버리면 "그 태그를 지웠다"는 기록이 사라져, 뒤늦게 도착한 옛 넣기(그 태그를 든 상태)와 합칠 때 지운 원소가 되살아난다.\
  실제 시스템에서 이것(툼스톤 축적)이 CRDT 의 제일 큰 문제다.

> **툼스톤(tombstone, 지운 태그)** — 지웠다는 기록. 영원히 들고 있어야 옛 넣기의 부활을 막는다 — CRDT 의 제일 큰 비용.\
> 예: 넣고 빼기를 100번 반복하면 원소 0개에 태그 200개가 남는다.

- **100번 반복?**\
  → 원소 0개, 태그 200개(넣기 태그 100 + 지움 태그 100 — `tagCount()` 가 재는 값).
- **잔액이 안 되는 이유?**\
  → 잔액 100에서 A 가 60을 빼고 B 가 70을 빼면 각자에게는 둘 다 유효한데 합치면 -30이다.\
  "0 밑으로 안 내려간다"는 불변식을 합치는 규칙만으로 지킬 방법이 없다 — 빼기 전에 전체가 하나의 값에 동의해야 하고, 그것은 합의(11번 분산 락)의 영역이다.

> **합의(consensus)** — 여러 노드가 하나의 값에 동의하는 것.\
> 예: 잔액은 빼기 전에 전체가 하나의 값에 동의해야 해서 CRDT 로 안 된다.

- **가르는 기준 한 문장?**\
  → **합칠 규칙이 자료의 뜻과 맞아떨어지는가.**\
  조회수·좋아요·장바구니는 되고, 잔액·재고는 안 된다.

#### 6. 연결·검증

- **14번과의 이음새?**\
  → 논리 시계는 "이 둘은 동시다"까지 판정하고 멈췄다 — 동시인 두 값의 처리는 자료의 뜻에 달렸기 때문이다.\
  CRDT 는 그 처리를 자료구조의 merge 규칙으로 미리 정해, 순서를 몰라도(동시여도) 답이 하나로 정해지게 한다.
- **왜 성질 검사인가?**\
  → CRDT 의 계약이 "특정 입력에 특정 출력"이 아니라 "어떤 순서·중복으로 합쳐도 같다"라는 **대수적 성질**이기 때문이다.\
  무작위 순서로 섞어 합쳐도 같은 답인지를 검사한다(34번 의존성 해석기의 방식과 같다).

> **대수적 성질 검사(property-based 검증)** — 특정 입출력이 아니라 "성질이 성립하는가"를 검사하는 테스트 방식.\
> 예: 무작위 순서로 섞어 합쳐도 같은 답인지를 본다.

- **변종이 두 번 살아남은 이유?**\
  → 처음엔 **다른 원소끼리의** 태그 충돌로 판별 테스트를 만들었는데, 지움 목록이 원소별로 갈려 있어서 충돌이 무해했다.\
  **같은 원소**에 같은 태그가 붙는 경우(오래된 복제본에 합친 뒤 add)로 바꿔야 잡혔다 — 판별 테스트도 사고가 나는 바로 그 자리를 겨눠야 한다는 교훈.
- **16번과의 대비?**\
  → 이 챕터는 합치는 규칙으로 순서 문제를 **피했고**(순서가 없어도 되게), 이벤트 소싱은 순서를 **기록으로 남긴다**(사건 목록 자체가 순서다).
