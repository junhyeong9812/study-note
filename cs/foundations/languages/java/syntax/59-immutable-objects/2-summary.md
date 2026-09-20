# java/syntax/59 — 불변 객체 만들기: 방어적 복사·`record` 와의 조합 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §17.5 `final` Field Semantics](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html) · [Java SE 21 `List.copyOf` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/List.html) · [`Collections.unmodifiableList`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Collections.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/List.java` · `Collections.java` 의 **javadoc 원문**(`lib/src.zip` 에서 직접 읽음).
> **실행 검증** — 이 문서의 모든 출력·예외는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 4개를 **17.0.13 · 21.0.5 · 25.0.1** 에서 전부 돌렸고 **세 버전의 출력이 한 글자도 다르지 않았다.**\
> 다만 이것은 관찰이지 보장이 아니다.\
> `javap -c -p` 로 「동작 방식 (4)」의 **컴파일 타임 상수 인라인**을 확인했다.
> **버전** — 방어적 복사 관용구 자체는 Java 1.0 부터의 이야기다. 도구는 나중에 왔다 —
> `Collections.unmodifiableList` = **1.2** · `Arrays.asList` = **1.2** · `Objects.requireNonNull` = **7** ·
> `List.of` = **9** · **`List.copyOf` = 10** · `record` = **16**(`@since` 는 `src.zip` 직접 확인).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [14 `record`](../14-records/) · [40 `List`·`Set` API 와 불변 팩토리](../40-list-set-and-immutable-factories/).

## 한눈에 — 쉽게 말하면

**불변 객체는 "내용물을 봉인한 상자"다.**\
그런데 **상자 안에 열쇠 꾸러미를 넣어 두면 봉인은 의미가 없다** — 안의 열쇠로 다른 방을 열 수 있기 때문이다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 봉인한 상자 | 불변 객체 — 만들어진 뒤 관측 가능한 상태가 안 바뀐다 |
| 상자에 든 **값** (숫자·글자) | `int`·`String` 같은 불변 값 — 안전하다 |
| 상자에 든 **열쇠** | 가변 객체를 가리키는 참조(`int[]`·`ArrayList`·`Date`) — **새는 통로** |
| 열쇠를 **받을 때** 복사본을 만드는 것 | 생성자의 방어 복사 (**들어올 때**) |
| 열쇠를 **줄 때** 복사본을 주는 것 | getter 의 방어 복사 (**나갈 때**) |
| 상자를 못 열게 봉인 테이프를 붙이는 것 | 필드 `final` |
| 상자를 **복제해 다른 상자로 만들지 못하게** 하는 것 | 클래스 `final` (또는 생성자 비공개) |
| 봉인이 끝나기 전에 상자를 남에게 보여 주는 것 | **`this` 유출** — 아직 미완성인 상태를 노출한다 |

- **불변의 조건은 넷이고, 넷 다 필요하다.** 하나라도 빠지면 "불변인 줄 알았던 것"이 된다.

```text
1. 모든 필드가 final           -> 필드에 담긴 "칸"이 안 바뀐다
2. 클래스가 final (또는 생성자 비공개)  -> 하위 클래스가 약속을 깨지 못한다
3. 가변 필드는 방어 복사 — 들어올 때와 나갈 때 **둘 다**
4. 생성 중에 this 가 밖으로 새지 않는다
```

- **1 과 3 을 헷갈리는 것이 가장 흔하다.** `final List<String> items` 는\
  **"items 가 다른 리스트를 가리키지 못한다"**는 뜻이지 **"그 리스트에 `add` 할 수 없다"**는 뜻이 아니다.

```text
final List<String> items = new ArrayList<>();

  items ──(고정)──> [ArrayList]      <- 화살표는 못 바꾼다 (final)
                       |
                       +-- add("x")  <- 가리켜진 상자의 내용은 바뀐다
```

실무에서 이게 터지는 자리는 **DTO 를 `record` 로 바꾸고 "이제 불변이니 스레드 안전"이라고 적는 순간**이다.\
컴포넌트가 `List<String>` 이면 `record` 는 **참조만** 고정하고, 그 리스트는 밖에서도 안에서도 계속 바뀐다.

> **불변 객체(immutable object)** — 만들어진 뒤 **관측 가능한 상태**가 절대 바뀌지 않는 객체.\
> 예: `String`·`Integer`·`LocalDate`. `s.toUpperCase()` 는 `s` 를 안 바꾸고 새 객체를 준다.

> **방어적 복사(defensive copy)** — 밖에서 받은 가변 객체를 그대로 붙잡지 않고 복사본을 갖는 것,\
> 그리고 밖으로 줄 때도 복사본을 주는 것.\
> 예: 생성자에서 `this.scores = scores.clone()`, getter 에서 `return scores.clone()`.

> **얕은 불변(shallow immutability)** — 필드에 담긴 값은 고정되지만 그 값이 가리키는 객체의 내부는 못 막는 상태.\
> 예: `record Order(String id, List<String> items)` 의 `items` 리스트.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. "불변으로 만들었다"가 **어디서 깨지는가** — 새는 통로가 몇 개인가.
2. `record` 는 **어디까지 해 주고 어디부터 안 해 주는가.**
3. 컬렉션 필드를 담을 때 `List.copyOf` 와 `Collections.unmodifiableList` 중 **무엇을 골라야 하는가.**

## 동작 방식

### (1) 새는 통로는 둘이다 — 들어올 때와 나갈 때

**언제 쓰나** — 가변 필드(배열·컬렉션·`Date`)를 가진 클래스를 불변이라고 부르기 전.

같은 클래스를 세 단계로 만들어 실행했다 (`Ex.java (59-a)`, JDK 21.0.5 — 17 · 25 동일).

```text
1단계 Leaky  : 생성자도 getter 도 그대로 들고/주고
2단계 HalfSafe: 생성자에서만 복사
3단계 Safe    : 생성자와 getter 둘 다
```

```text
                 밖의 원본                       객체 안                    꺼낸 것
1단계 Leaky
   new Leaky(src, tags)      src ────────────────> [배열]  <──────────── scores()
                             tags ───────────────> [리스트] <─────────── tags()
   -> 양쪽 다 같은 객체다. 어느 쪽을 고쳐도 안이 바뀐다.

2단계 HalfSafe
   new HalfSafe(src, tags)   src    [배열]   (복사)  [배열']  <──────────── scores()
   -> 들어오는 통로는 막혔다. 나가는 통로는 그대로다.

3단계 Safe
   new Safe(src, tags)       src    [배열]   (복사)  [배열']  (복사) [배열''] -> scores()
   -> 양쪽 다 막혔다.
```

실행 결과:

```text
--- 1단계: 아무 방어도 없는 Leaky
  만든 직후        : jun [90, 80] [vip]
  들어온 원본을 고침: jun [0, 80] [vip, 해킹됨]   <- 밖에서 바뀌었다
  꺼낸 것을 고침    : jun [0, -1] [vip, 해킹됨, 또]   <- 꺼내서도 바뀌었다
--- 2단계: 들어올 때만 막은 HalfSafe
  원본을 고침      : [90, 80] [vip]   <- 막혔다
  꺼낸 것을 고침    : [90, -1] [vip, 또]   <- 뚫렸다
--- 3단계: 양쪽 다 막은 Safe
  양쪽 다 고쳐 봄  : [90, 80] [vip]   <- 안 바뀐다
  꺼낸 리스트에 add : java.lang.UnsupportedOperationException (메시지 null)
```

그림 해설 (한 단계씩):

- 1단계는 **두 통로가 다 열려 있다.** 생성자에 넘긴 배열을 밖에서 고치면 안이 바뀌고,\
  getter 로 꺼낸 배열을 고쳐도 안이 바뀐다.
- 2단계는 **절반만 막았다.** "생성자에서 복사했으니 됐다"가 가장 흔한 착각이다.
- 3단계는 **양쪽을 다 막았다.** 배열은 `clone()` 을, 리스트는 `List.copyOf` 를 썼다.
- `List.copyOf` 는 **복사본이면서 수정 불가**라 **getter 를 안 고쳐도 된다** — (3) 에서 그 이유를 본다.

비용 — 복사는 O(n) 이다. 큰 컬렉션을 자주 꺼내는 API 는 **복사본 대신 불변 타입으로 아예 바꾸는 것**이 낫다.

### (2) `record` 가 해 주는 것과 안 해 주는 것

**언제 쓰나** — DTO 를 `record` 로 바꿀 때마다.

```text
record 가 해 주는 것                     record 가 안 해 주는 것
+-------------------------------+       +-------------------------------+
| 모든 필드를 private final 로   |       | 가변 컴포넌트의 방어 복사      |
| 클래스를 final 로              |       | (들어올 때도 나갈 때도)        |
| equals/hashCode/toString 생성  |       | 배열 컴포넌트의 equals 를      |
| 접근자 생성                    |       | **내용 비교**로 만드는 것      |
+-------------------------------+       +-------------------------------+
  = 조건 1·2 는 공짜                       = 조건 3 은 직접 해야 한다
```

실행 결과 (`Ex.java (59-c)`, JDK 21.0.5 — 17 · 25 동일):

```text
--- record 가 해 주는 것: 필드 final
  만든 직후 : [책] [1]
--- record 가 안 해 주는 것: 방어 복사
  원본을 고침 : [책, 펜] [99]   <- 새어 나갔다
  꺼내서 고침 : [책, 펜, 또] [-1]   <- 또 새어 나갔다
--- 컴팩트 생성자 + 접근자로 막은 SafeOrder
  양쪽 다 고쳐 봄 : SafeOrder[id=A1, items=[책], counts=[1]]   <- 안 바뀐다
  꺼낸 리스트에 add : UnsupportedOperationException
--- 접근자만 복사하면 record 의 복사 불변식이 깨진다 (14편의 정본)
  s.equals(new SafeOrder(s.id(), s.items(), s.counts())) = true
  (equals 를 배열 내용 비교로 같이 고쳤기 때문에 성립한다)
--- equals 를 안 고쳤다면?
  같은 값으로 만든 record 둘의 equals = false   <- 배열은 참조 비교다
```

막는 코드는 이렇게 생겼다 — **컴팩트 생성자가 들어오는 통로, 접근자가 나가는 통로**다.

```java
record SafeOrder(String id, List<String> items, int[] counts) {
    SafeOrder {                                   // 들어올 때
        Objects.requireNonNull(id);
        items  = List.copyOf(items);
        counts = counts.clone();
    }
    @Override public int[] counts() { return counts.clone(); }   // 나갈 때
    @Override public boolean equals(Object o) { ... Arrays.equals(counts, s.counts); }
    @Override public int hashCode() { return Objects.hash(id, items, Arrays.hashCode(counts)); }
}
```

그림 해설 (한 단계씩):

- **컴팩트 생성자에서는 파라미터에 대입한다.** `this.items = ...` 는 컴파일 에러다([14 `record`](../14-records/) 가 정본).
- `List.copyOf` 하나로 리스트는 **양쪽이 동시에** 막힌다(복사본 + 수정 불가).
- **배열은 그런 팩토리가 없어서** `clone()` 을 **접근자에도** 넣어야 한다.
- ★ **접근자만 고치면 `record` 의 복사 불변식이 깨진다.**\
  `Record` javadoc 이 `r.equals(new R(r.c1(), ..., r.cn()))` 가 반드시 참이어야 한다고 못박는데,\
  접근자가 복사본을 주면 새로 만든 것이 원본과 `equals` 하지 않게 된다.\
  그래서 **방어 복사는 `equals`/`hashCode` 재정의와 한 묶음**이다 — 자세한 것은 [14 `record`](../14-records/).
- 마지막 줄이 그 이유를 보여 준다 — 배열 컴포넌트의 기본 `equals` 는 **참조 비교**라 같은 값이어도 `false` 다.

비용 — 복사 두 번이다. 대신 **`record` 를 `Map` 키·캐시 키로 안전하게 쓸 수 있게 된다.**

### (3) ★ `List.copyOf` 대 `Collections.unmodifiableList` — 뷰인가 복사본인가

**언제 쓰나** — 불변 클래스의 컬렉션 필드를 무엇으로 담을지 고를 때.

```text
Collections.unmodifiableList(origin)        List.copyOf(origin)
+---------------------------------+         +---------------------------------+
| view ──(읽기만)──> [origin]      |         | copy ──> [새 리스트 · 스냅샷]     |
|                      ^           |         |                                 |
|                      |           |         |          [origin] (무관)         |
|              origin 이 여기 있다 |         |                                 |
+---------------------------------+         +---------------------------------+
  origin.add("c") 하면 view 도 바뀐다         origin 을 고쳐도 copy 는 그대로
```

실행 결과 (`Ex.java (59-b)`, JDK 21.0.5 — 17 · 25 동일):

```text
--- 만든 직후
  원본 = [a, b]
  unmodifiableList(원본) = [a, b]
  List.copyOf(원본)      = [a, b]
--- 둘 다 직접 고치는 것은 막힌다
  view.add -> UnsupportedOperationException
  copy.add -> UnsupportedOperationException
--- 그런데 원본을 고치면
  원본 = [a, b, c]
  view = [a, b, c]   <- 같이 바뀐다 (뷰라서)
  copy = [a, b]   <- 안 바뀐다 (복사본이라서)
--- 원본을 비우면
  view = []  size=0
  copy = [a, b]  size=2
--- 구현 클래스 이름
  view.getClass() = java.util.Collections$UnmodifiableRandomAccessList
  copy.getClass() = java.util.ImmutableCollections$List12
  List.of(1,2).getClass() = java.util.ImmutableCollections$List12
```

그림 해설 (한 단계씩):

- **둘 다 `add` 는 막힌다.** 여기까지만 보면 구별이 안 된다 — **그래서 위험하다.**
- **원본을 고치면 뷰는 따라 바뀐다.** `clear()` 하면 뷰의 `size()` 가 0 이 된다.
- 즉 `unmodifiableList` 는 **"내가 못 고친다"**일 뿐 **"아무도 안 고친다"**가 아니다.

javadoc 이 각각 그렇게 적어 놓았다(JDK 21.0.5 `src.zip` 원문).

```text
Collections.unmodifiableList:
  Returns an unmodifiable view of the specified list. Query operations on
  the returned list "read through" to the specified list, ...

List.copyOf:
  ... If the given Collection is subsequently modified, the returned List
  will not reflect such modifications.
```

- **`"read through"`** 와 **`"will not reflect"`** — 계약 문장이 정반대다.

**불변 클래스의 필드로 담을 때의 결론**

| 상황 | 고를 것 |
|---|---|
| 밖에서 받은 리스트를 **필드에 담는다** | **`List.copyOf`** — 복사본이면서 수정 불가 |
| 내가 만든 리스트를 **다 만든 뒤 잠근다** | `List.copyOf` 또는 `List.of` |
| 내부 가변 리스트를 **읽기 전용으로 노출**한다 (스냅샷이 아니라 실시간 뷰가 의도다) | `Collections.unmodifiableList` — **그리고 문서에 "뷰"라고 적는다** |

**두 가지 더 — `copyOf` 의 성질**

```text
--- copyOf 는 이미 불변이면 복사도 안 한다
  List.copyOf(List.of(...)) == 원본 : true
  List.copyOf(뷰) == 뷰           : false
--- null 처리가 다르다
  unmodifiableList(null 포함) = [null]
  List.copyOf(null 포함) -> java.lang.NullPointerException
```

- `List.copyOf` 는 **이미 불변 리스트면 그대로 돌려준다**(javadoc `@implNote` 가 명시).\
  그래서 "혹시 몰라 한 번 더 `copyOf`" 가 공짜에 가깝다.
- **뷰는 불변이 아니므로 복사한다** — `List.copyOf(뷰) == 뷰` 가 `false` 인 것이 그 증거다.\
  뷰를 `copyOf` 로 감싸면 그 순간의 **스냅샷**이 된다.
- **`List.copyOf` 는 `null` 원소를 거부한다.** 방어로 쓸 수 있지만, `null` 이 들어올 수 있는 데이터에는 터진다.\
  (세 팩토리의 `null`·가변·뷰 세 축은 [40 `List`·`Set` API 와 불변 팩토리](../40-list-set-and-immutable-factories/) 가 정본이다.)

**`Arrays.asList` 는 또 다르다 — 배열의 양방향 뷰다.**

```text
--- Arrays.asList 는 또 다르다 (고정 크기 뷰)
  배열을 고치니 asList = [Z, b]
  asList.set 후 배열   = [Z, Y]
  asList.add -> UnsupportedOperationException
```

- `add` 만 막히고 `set` 은 된다. 그리고 **배열과 리스트가 서로를 비춘다.**
- 방어적 복사로 쓰면 **그대로 새어 나간다.**

**그리고 모든 복사는 얕다.**

```text
--- 얕은 복사라는 한계 — 원소 자체가 가변이면
  frozen.get(0) = [999, 2]   <- 원소는 공유된다
```

- `List.copyOf(rows)` 로 리스트를 잠가도 **원소인 `int[]` 는 그대로 공유**된다.
- 진짜 깊은 불변을 원하면 **원소 타입부터 불변**이어야 한다.

비용 — `copyOf` 는 O(n) 이고 `unmodifiableList` 는 O(1) 이다. **비용 차이가 곧 의미 차이**다.

### (4) 조건 2·4 — `final` 클래스와 `this` 유출

**언제 쓰나** — 필드를 다 `final` 로 만들고 방어 복사도 했는데 여전히 불안할 때.

**조건 2 — 클래스가 `final` 이 아니면 하위 클래스가 약속을 깬다.**

```text
class Money {                    class FakeMoney extends Money {
    private final long amount;       private long real;
    long amount() { return amount; } long amount() { return real++; }  // 부를 때마다 달라진다
}                                }
```

```text
--- (3) final 이 아닌 클래스는 불변을 약속할 수 없다
  amount() 를 세 번 : 100 101 102
```

- `Money` 자체는 흠이 없는데 **`Money` 타입으로 받은 쪽**이 당한다.
- 같은 객체의 `amount()` 가 매번 달라지니 **`Map` 키로 쓰면 못 찾는다**([27 `equals`/`hashCode` 계약](../27-equals-hashcode-contract/)).
- 방어: **클래스를 `final` 로** 하거나, 생성자를 `private` 으로 두고 정적 팩토리만 노출한다.\
  (`record` 는 항상 `final` 이라 이 조건이 공짜다.)

**조건 4 — 생성자가 끝나기 전에 `this` 가 나가면 안 된다.**

유출 경로가 둘이다.

```text
경로 A: 생성자가 재정의 가능한 메서드를 부른다
   Base(int size) { this.size = size; describe(); }   // describe 를 Child 가 재정의했다면?
        ↓
   Child 의 필드 초기화가 아직 안 끝난 상태에서 Child.describe() 가 돈다

경로 B: 생성자 안에서 this 를 밖에 등록한다
   Escaper(int v) { Registry.ALL.add(this); this.value = v; }
        ↓
   등록 직후~대입 전 사이에 다른 스레드가 읽으면 value 가 0 이다
```

```text
--- (1) 생성자가 재정의 가능한 메서드를 부르면
    Child.describe label=완성된 라벨 data=null
--- (2) 생성자 안에서 this 를 밖에 넘기면
  생성 전 Registry 크기 = 0
  등록된 것이 같은 객체인가 = true
  (다른 스레드가 그 사이에 읽었다면 value 는 0 이었을 수 있다 — 안전 공개 위반)
```

**★ 경로 A 의 출력이 이상하다 — `data` 는 `null` 인데 `label` 은 값이 있다.**

둘 다 `Child` 의 `final` 필드이고 초기화는 `super(3)` 다음이다. 왜 하나만 `null` 일까.\
`javap -c -p Child.class` 가 답을 준다 (JDK 21.0.5).

```text
  void describe();
    Code:
       0: getstatic     #32                 // Field java/lang/System.out:Ljava/io/PrintStream;
       3: aload_0
       4: getfield      #28                 // Field data:Ljava/util/List;
       7: invokestatic  #38                 // Method java/lang/String.valueOf:(Ljava/lang/Object;)Ljava/lang/String;
      10: invokedynamic #44,  0             // InvokeDynamic #0:makeConcatWithConstants:(Ljava/lang/String;)Ljava/lang/String;
      15: invokevirtual #48                 // Method java/io/PrintStream.println:(Ljava/lang/String;)V
      18: return
```

- **`getfield` 가 `data` 하나뿐이다.** `label` 을 읽는 명령이 아예 없다.
- `label` 은 `private final String label = "완성된 라벨";` — **컴파일 타임 상수**라 값이 호출부에 박혔다.
- 그래서 **실제로 읽은 `data` 만 `null`** 이었다.
- 교훈 둘: **(가) 생성자에서 재정의 가능한 메서드를 부르면 하위 필드가 `null` 이다.**\
  **(나) 그 증상이 "어떤 필드는 멀쩡해 보인다"라서 더 헷갈린다** — 상수 인라인 때문이다.
- 방어: **생성자에서 부르는 메서드는 `private` 또는 `final` 로.**

비용 — 없다. 전부 설계 규칙이다.

### (5) `final` 필드가 주는 또 하나 — 안전 공개

**언제 쓰나** — 불변 객체를 여러 스레드가 공유할 때.

JLS §17.5 가 `final` 필드에 **특별한 보장**을 준다 — 생성자가 끝나는 시점에 `final` 필드가 "얼어붙고",\
그 객체 참조를 본 스레드는 **`final` 필드의 올바른 값을 본다**(데이터 경쟁이 있어도).

```text
final 이 없을 때                        final 일 때
+-----------------------------+        +-----------------------------+
| 스레드 A: obj = new X(5);   |        | 스레드 A: obj = new X(5);   |
| 스레드 B: obj.value 를 읽음 |        | 스레드 B: obj.value 를 읽음 |
|   -> 0 을 볼 수도 있다       |        |   -> 반드시 5 를 본다        |
+-----------------------------+        +-----------------------------+
   (동기화가 없다면)                      (조건 4 를 지켰다면)
```

- **조건 4(`this` 유출 없음)가 이 보장의 전제**다. 생성 중에 참조가 샜다면 보장이 깨진다.
- 이 문서는 이 보장을 **명세 문장으로만** 적는다 — 데이터 경쟁은 재현이 보장되지 않아\
  "돌려 봤더니 괜찮았다"가 근거가 될 수 없기 때문이다.\
  메모리 모델 자체는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 정본이다.

비용 — 없다. **`final` 을 붙이는 것만으로 얻는다.**

## 문법 — 형태와 규칙

### 불변 클래스의 표준 형태

```java
public final class Reservation {                     // 조건 2
    private final String  id;                        // 조건 1
    private final List<String> guests;
    private final int[]   seats;

    public Reservation(String id, List<String> guests, int[] seats) {
        this.id     = Objects.requireNonNull(id);
        this.guests = List.copyOf(guests);           // 조건 3 (들어올 때) — 복사 + 수정 불가
        this.seats  = seats.clone();                 // 조건 3 (들어올 때)
    }                                                // 조건 4: this 를 어디에도 넘기지 않는다

    public String id()             { return id; }
    public List<String> guests()   { return guests; }   // 이미 불변이라 그대로 줘도 된다
    public int[] seats()           { return seats.clone(); }   // 조건 3 (나갈 때)
}
```

### 같은 것을 `record` 로

```java
public record Reservation(String id, List<String> guests, int[] seats) {
    public Reservation {                                     // 조건 3 (들어올 때)
        Objects.requireNonNull(id);
        guests = List.copyOf(guests);
        seats  = seats.clone();
    }
    @Override public int[] seats() { return seats.clone(); } // 조건 3 (나갈 때)
    // 배열 컴포넌트가 있으므로 equals/hashCode 도 내용 비교로 재정의해야 한다 — 14번
}
```

### 필드 타입별 방어법

| 필드 타입 | 들어올 때 | 나갈 때 |
|---|---|---|
| `String`·`int`·`LocalDate`·`BigDecimal`·다른 불변 타입 | 그냥 대입 | 그냥 반환 |
| `List`·`Set`·`Map` | **`List.copyOf` / `Set.copyOf` / `Map.copyOf`** | 그대로 반환해도 된다(이미 불변) |
| 배열 | `clone()` | **`clone()`** |
| 다차원 배열 | 안쪽까지 직접 복사 | 안쪽까지 직접 복사 |
| `Date`·`Calendar` | `new Date(d.getTime())` — 또는 **타입을 `Instant` 로 바꾼다** | 같은 방식 |
| 남이 준 인터페이스 구현체 | 복사할 방법이 없으면 **불변이라는 계약을 문서로 요구**한다 | — |

- ★ **`clone()` 은 한 겹만 복사한다.** 다차원 배열·객체 배열에는 부족하다([05 배열](../05-arrays/) 이 정본).
- `Date` 는 애초에 쓰지 않는 것이 답이다 — `java.time` 타입은 전부 불변이다.

### "불변"이라고 부르기 전 체크리스트

```text
[ ] 모든 필드가 final 인가
[ ] 클래스가 final 인가 (또는 생성자가 비공개인가)
[ ] 가변 필드를 받을 때 복사했나
[ ] 가변 필드를 줄 때 복사했나 (또는 애초에 불변 타입인가)
[ ] 생성자가 재정의 가능한 메서드를 부르지 않는가
[ ] 생성자가 this 를 밖에 등록하지 않는가
[ ] 배열 컴포넌트가 있다면 equals/hashCode 를 내용 비교로 고쳤나
```

## 어디서 틀리나

### 1. `final` 컬렉션 필드를 "불변"이라고 부른다

```java
private final List<String> items = new ArrayList<>();
items.add("x");     // 잘 된다
```

- `final` 은 **참조를 고정**할 뿐이다. 가리켜진 리스트는 자유다.
- 실행으로 본 것 (`Ex.java (59-d)`):

```text
--- (4) 필드가 final 이어도 가리켜진 객체는 자유다
  final StringBuilder 에 append = ab
```

### 2. 생성자에서만 복사하고 getter 를 그대로 둔다

- 「동작 방식 (1)」의 2단계다. **절반만 막은 것**이고, 그 절반이 더 위험하다\
  ("복사했다"는 기억 때문에 의심을 안 하게 된다).

### 3. `Collections.unmodifiableList` 를 스냅샷으로 쓴다

```text
  원본 = [a, b, c]
  view = [a, b, c]   <- 같이 바뀐다 (뷰라서)
  copy = [a, b]   <- 안 바뀐다 (복사본이라서)
```

- **`add` 가 막히는 것만 보고 같다고 믿는 것**이 함정이다.
- 방어: 필드에 담을 때는 **`List.copyOf`**. 뷰가 의도라면 **이름과 문서에 "뷰"라고 적는다.**

### 4. `Arrays.asList` 를 방어적 복사로 쓴다

```text
  배열을 고치니 asList = [Z, b]
  asList.set 후 배열   = [Z, Y]
```

- **양방향 뷰**다. 복사가 전혀 아니다.
- 방어: `List.of(arr)` 는 배열을 복사한다. 또는 `Arrays.stream(arr).toList()`.

### 5. `record` 니까 불변이라고 적는다

```text
  원본을 고침 : [책, 펜] [99]   <- 새어 나갔다
```

- `record` 는 조건 1·2 만 해 준다. **조건 3 은 컴팩트 생성자와 접근자에 직접 쓴다.**

### 6. 생성자에서 재정의 가능한 메서드를 부른다

```text
    Child.describe label=완성된 라벨 data=null
```

- 하위 필드가 `null` 인 상태로 메서드가 돈다.
- **그런데 컴파일 타임 상수 필드는 멀쩡해 보여서** 더 헷갈린다((4) 의 `javap`).
- 방어: 생성자가 부르는 메서드는 `private` 또는 `final` 로.

### 7. 깊은 불변을 기대한다

```text
  frozen.get(0) = [999, 2]   <- 원소는 공유된다
```

- 컬렉션을 아무리 잠가도 **원소가 가변이면 그 안은 자유**다.
- 방어: **원소 타입부터 불변으로** 만든다. 그러지 못하면 "얕은 불변"이라고 문서에 적는다.

### 8. `Date` 를 필드에 담는다

```text
--- (5) 가변 Date 를 담으면 (java.time 을 쓰는 이유)
  밖에서 setTime 한 뒤 h.when().getTime() = 86400000
```

- `record Holder(Date when)` 에 넣고 밖에서 `setTime` 하니 그대로 바뀌었다.
- 방어: **`Instant`·`LocalDateTime` 으로 타입을 바꾼다.** 복사보다 타입 교체가 근본적이다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `final` 필드가 참조만 고정한다 | **언어**(JLS §4.12.4) | (1)·「어디서 틀리나」 1번 |
| `final` 필드의 안전 공개 | **언어**(JLS §17.5) | 명세 문장으로만 적었다 — 실행으로 증명할 수 없다 |
| `unmodifiableList` 가 **뷰**다 | **javadoc 계약** | *"Query operations ... \"read through\" to the specified list"* |
| `copyOf` 가 **스냅샷**이다 | **javadoc 계약** | *"If the given Collection is subsequently modified, the returned List will not reflect such modifications."* |
| `copyOf` 가 이미 불변이면 복사 안 한다 | **javadoc `@implNote`** | *"calling copyOf will generally not create a copy"* — `@implNote` 라 강한 계약은 아니다 |
| `copyOf` 가 `null` 에 NPE | **javadoc 계약**(`@throws`) | |
| `Collections$UnmodifiableRandomAccessList` 같은 클래스 이름 | **구현** | 기대면 안 된다 |
| `record` 가 `final` 이고 필드가 `final` 인 것 | **언어**(JLS §8.10) | |
| `record` 의 복사 불변식 | **javadoc 계약** | `Record` javadoc — [14 `record`](../14-records/) 가 정본 |
| 컴파일 타임 상수가 호출부에 박히는 것 | **언어**(JLS §13.1 — 상수 변수) | (4) 의 `javap` |
| `UnsupportedOperationException` 의 메시지가 `null` 인 것 | **구현** | 메시지에 기대지 말 것 |

## 언제 쓰고 언제 안 쓰나

| 불변으로 만든다 | 안 만든다 |
|---|---|
| 값을 나르는 타입(DTO·VO·설정·좌표·금액) | 정체성이 있고 수명 동안 변하는 엔티티(주문 상태·세션) |
| `Map`·`Set` 의 키 | 큰 데이터를 자주 조금씩 고치는 버퍼(`StringBuilder` 가 있는 이유) |
| 여러 스레드가 공유하는 것 | 프레임워크가 setter 를 요구하는 자리(일부 ORM·직렬화) |
| 캐시에 담는 것 | 복사 비용이 실제로 문제가 되는 핫패스 (측정 후에) |
| 공개 API 의 반환 타입 | |

- 불변을 포기할 때도 **"어디까지 불변인가"를 문서에 적는다.** "얕은 불변"이라고 쓰는 것만으로 사고가 줄어든다.

## 핵심 문장

- **불변의 조건은 넷**이다 — 필드 `final` · 클래스 `final` · **방어 복사(들어올 때와 나갈 때 둘 다)** · `this` 유출 없음.
- **`final` 은 참조를 고정할 뿐** 가리켜진 객체의 내부를 막지 못한다. 이것이 얕은 불변이다.
- **`record` 는 조건 1·2 만 공짜로 준다.** 조건 3 은 컴팩트 생성자와 접근자에 직접 쓴다.
- **`unmodifiableList` 는 뷰이고 `copyOf` 는 스냅샷이다.** 둘 다 `add` 가 막혀서 구별이 안 되는 것이 함정이다.
- **생성자가 재정의 가능한 메서드를 부르면** 하위 필드가 `null` 인 채로 돈다 — 상수 필드는 멀쩡해 보여 더 헷갈린다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 59번)
- [`../14-records/`](../14-records/) — **`record` 문법·컴팩트 생성자·복사 불변식이 정본이다.**\
  **경계: 그쪽은 「`record` 안에서 관용구를 어디에 넣나」까지, 여기는 「그 관용구 자체가 무엇이고 `record` 가 아닌 클래스에서는 어떻게 하나」다.**\
  접근자만 복사했을 때 복사 불변식이 깨지는 증명은 14번에 있다.
- [`../40-list-set-and-immutable-factories/`](../40-list-set-and-immutable-factories/) — **팩토리 API 자체가 정본이다**(`of`/`copyOf`/`unmodifiable*`/`asList`/`subList` 의 `null`·가변·뷰 세 축).\
  **경계: 그쪽은 「어느 팩토리가 무엇을 하나」까지, 여기는 「불변 클래스의 필드로 무엇을 고르나」라는 판단만.**\
  이 문서 (3) 은 그 세 축 중 **뷰/스냅샷 축 하나만** 불변 클래스 설계의 관점에서 다시 본다.
- [`../05-arrays/`](../05-arrays/) — **배열의 `clone()` 이 한 겹만 복사한다는 것이 정본이다.**\
  **경계: 그쪽은 「`clone`·`copyOf` 가 무엇을 하나」, 여기는 「그것을 생성자·getter 어디에 넣나」.**
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — **계약 다섯 조항과 위반 증상이 정본이다.**\
  **경계: 여기는 「불변이 아니면 그 계약을 지킬 수 없다」는 연결만** — `Map` 에서 원소가 사라지는 실험은 그쪽이다.
- [`../35-string/`](../35-string/) — `String` 이 불변이라 얻는 것 넷(공유·스레드 안전·해시 캐시·키 안전)
- [`../06-initialization-order/`](../06-initialization-order/) — **초기화 순서가 정본이다.**\
  (4) 의 `this` 유출이 왜 `null` 을 만드는지의 바탕(하위 필드는 `super()` 뒤에 초기화된다).
- [`../09-inheritance-overriding/`](../09-inheritance-overriding/) — 동적 디스패치. 생성자가 부른 메서드가 왜 하위 것이 되는지
- [`../10-access-modifiers/`](../10-access-modifiers/) — 생성자를 `private` 으로 두고 정적 팩토리만 노출하는 형태
- [`../53-bigdecimal/`](../53-bigdecimal/) · [`../38-optional/`](../38-optional/) — 표준 라이브러리의 불변 값 타입 예
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 — **메모리 모델·happens-before 가 정본이다.**\
  **경계: 여기는 「`final` 이 안전 공개를 준다」는 결론만 쓰고, 왜 그런지는 거기다.**

## 용어 풀이

- **불변 객체(immutable object)** — 만들어진 뒤 관측 가능한 상태가 바뀌지 않는 객체.
- **얕은 불변 / 깊은 불변** — 필드만 고정 / 가리켜진 객체의 내부까지 고정.
- **방어적 복사** — 가변 객체를 받을 때·줄 때 복사본을 쓰는 것. **양쪽 다** 해야 완성이다.
- **뷰(view)** — 원본을 그대로 비추는 래퍼. 원본이 바뀌면 같이 바뀐다.
- **스냅샷(snapshot)** — 그 시점의 복사본. 원본이 바뀌어도 그대로다.
- **`this` 유출(this escape)** — 생성자가 끝나기 전에 객체 참조가 밖으로 나가는 것.
- **안전 공개(safe publication)** — 다른 스레드가 그 객체를 완전히 초기화된 상태로 보게 되는 것.
- **`final` 필드 의미론** — JLS §17.5. 생성자가 끝날 때 `final` 필드가 얼어붙는다는 보장.
- **컴팩트 생성자** — `record` 의 괄호 없는 표준 생성자 표기. 방어 복사의 자리.
- **복사 불변식** — `r.equals(new R(r.c1(), ..., r.cn()))` 가 참이어야 한다는 `record` 의 요구.
- **상수 변수(constant variable)** — `final` 이면서 컴파일 타임 상수로 초기화된 변수. 값이 호출부에 박힌다.
- **정적 팩토리** — 생성자를 감추고 `of`·`valueOf` 같은 static 메서드로 만들게 하는 형태.

## 더 들어가면

- **`List.copyOf` 한 번으로 양쪽이 막히는 것이 관용구의 핵심이다.**\
  복사본이면서 동시에 수정 불가라, **getter 를 손대지 않아도** 나가는 통로가 닫힌다.\
  반대로 **배열은 그런 팩토리가 없어서** 반드시 두 군데(`생성자`·`getter`)에 `clone()` 을 넣어야 한다.\
  — "컬렉션은 한 번, 배열은 두 번"으로 외운다.

- **`UnsupportedOperationException` 의 메시지는 `null` 이다.**

```text
  꺼낸 리스트에 add : java.lang.UnsupportedOperationException (메시지 null)
```

  로그에 `e.getMessage()` 만 찍으면 **`null` 만 남는다.** 스택트레이스를 함께 남겨야 어느 줄인지 안다.

- **불변 클래스에도 "바꾼 사본"을 주는 메서드는 있어야 쓸모가 있다.**\
  `String.toUpperCase()`·`LocalDate.plusDays(1)` 가 그 형태다 — **자기를 안 바꾸고 새 객체를 준다.**\
  `record` 라면 `with...` 류 메서드를 직접 만든다(자바에는 아직 `with` 문법이 없다).

- **생성자를 `private` 으로 두는 쪽이 `final` 클래스보다 유연할 때가 있다.**\
  `final` 은 테스트용 목(mock)까지 막는다. 생성자만 감추면 **같은 패키지·중첩 클래스**로는 확장할 수 있어\
  내부적으로 여러 구현을 두면서도 밖에서는 확장을 막을 수 있다.

- **불변이 성능을 해친다는 통념은 조건부다.**\
  복사 비용이 드는 것은 맞지만, 대신 **방어 복사를 안 해도 되는 자리가 늘고**(불변 타입은 그냥 공유),\
  락이 필요 없어지고, 캐시·해시 자료구조에 안전하게 들어간다.\
  (이 배치에서 불변 대 가변의 성능 비교는 **재지 않았다** — 주장도 하지 않는다.)

- **`Objects.requireNonNull` 은 조건 3 의 일부가 아니라 조건 0 에 가깝다.**\
  방어 복사는 "가변성"을 막고, `requireNonNull` 은 "없는 값"을 막는다. 둘은 다른 축이다 —\
  `null` 다루기의 정본은 [60 `null` 다루기](../60-null-handling/).
