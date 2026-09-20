# java/syntax/59 — 불변 객체 만들기: 방어적 복사·`record` 와의 조합 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 `lib/src.zip` 의 실파일에서, 바이트코드는 `javap -c -p` 출력을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했고, 프로그램이 여럿이라 `Ex.java (59-a)` 처럼 라벨로 구분한다.\
> 17.0.13 · 25.0.1 에서도 같은 프로그램을 돌렸고 **출력이 한 글자도 다르지 않았다** — 다만 관찰이지 보장이 아니다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 불변의 조건

**넷이다.**

```text
1. 모든 필드가 final
2. 클래스가 final (또는 생성자를 비공개로 두고 정적 팩토리만 노출)
3. 가변 필드는 방어 복사 — 들어올 때와 나갈 때 **둘 다**
4. 생성 중에 this 가 밖으로 새지 않는다
```

**`record` 가 공짜로 주는 것 — 1 과 2.**

- 컴포넌트는 `private final` 필드가 되고, `record` 클래스는 언제나 `final` 이다(JLS §8.10).
- **3 과 4 는 직접 해야 한다.**

**방어 복사는 두 군데** — 생성자(들어올 때)와 접근자/getter(나갈 때).

**조건을 빼먹었을 때의 증상**

| 빠진 조건 | 증상 |
|---|---|
| 1 (필드 `final`) | 내부 코드가 나중에 필드를 갈아 끼운다. 안전 공개 보장도 사라진다 |
| 2 (클래스 `final`) | 하위 클래스가 getter 를 재정의해 **부를 때마다 값이 달라진다**(7번) |
| 3 (들어올 때) | 생성자에 넘긴 객체를 밖에서 고치면 안이 바뀐다 |
| 3 (나갈 때) | getter 로 꺼낸 것을 고치면 안이 바뀐다 |
| 4 (`this` 유출) | 미완성 상태가 노출된다 — 필드가 `null`·`0` 으로 보인다(8·9번) |

### 2. 세 단계 클래스의 출력

**출력** (`Ex.java (59-a)`, JDK 21.0.5 — 17 · 25 동일)

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

**세 클래스의 상태**

| | (ㄱ) 원본 수정 후 | (ㄴ) 꺼낸 것 수정 후 |
|---|---|---|
| `Leaky` | **바뀐다** | **바뀐다** |
| `HalfSafe` | 안 바뀐다 | **바뀐다** |
| `Safe` | 안 바뀐다 | 안 바뀐다 |

**`Safe.tags().add("또")`**

- **`UnsupportedOperationException`** 이고, **메시지는 `null`** 이다.
- 로그에 `e.getMessage()` 만 찍으면 `null` 하나만 남는다 — 스택트레이스를 함께 남겨야 한다.

**`Safe` 가 `tags()` 에서 복사를 안 해도 되는 이유**

- 생성자에서 **`List.copyOf`** 를 썼기 때문이다. 그 결과물은 **복사본이면서 동시에 수정 불가**다.
- 즉 `List.copyOf` 한 번이 **두 통로를 동시에** 막는다.
- **배열은 그런 팩토리가 없다** — 그래서 `Safe.scores()` 에는 `clone()` 이 들어 있다.\
  **"컬렉션은 한 번, 배열은 두 번"**으로 외운다.

### 3. ★ `List.copyOf` 대 `Collections.unmodifiableList`

**출력** (`Ex.java (59-b)`, JDK 21.0.5 — 17 · 25 동일)

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

| | 결과 |
|---|---|
| (가) `view.add("x")` | `UnsupportedOperationException` |
| (나) `copy.add("x")` | `UnsupportedOperationException` |
| (다) `origin.add("c")` 뒤 `view` | **`[a, b, c]`** — 따라 바뀐다 |
| (라) 같은 시점 `copy` | `[a, b]` — 그대로 |
| (마) `origin.clear()` 뒤 크기 | **`0 2`** |

- **(가)·(나) 가 같아서** 두 개를 같은 것으로 착각하게 된다. 차이는 **(다)~(마) 에서만** 드러난다.

**javadoc 의 낱말** (JDK 21.0.5 `src.zip` 원문)

```text
Collections.unmodifiableList:
  Returns an unmodifiable view of the specified list. Query operations on
  the returned list "read through" to the specified list, and attempts to
  modify the returned list, whether direct or via its iterator, result in
  an UnsupportedOperationException.

List.copyOf:
  Returns an unmodifiable List containing the elements of the given
  Collection, in its iteration order. ... If the given Collection is
  subsequently modified, the returned List will not reflect such modifications.
```

- **`"read through"`** 대 **`"will not reflect such modifications"`** — 정반대의 계약이다.

**필드에 담을 때 — `List.copyOf`**

- 불변 클래스의 필드는 **스냅샷**이어야 한다. 뷰를 담으면 밖에서 원본을 쥔 사람이 내부를 계속 바꾼다.

**`unmodifiableList` 가 맞는 자리**

- **의도가 "실시간 읽기 전용 뷰"일 때**다. 내부 가변 컬렉션을 외부에 읽기 전용으로 계속 비춰 주고 싶을 때.
- 그때는 **이름과 문서에 "뷰"라고 적는다.** 받는 쪽이 스냅샷으로 오해하면 그게 버그다.

### 4. `copyOf` 의 성질

**출력** (`Ex.java (59-b)`, JDK 21.0.5)

```text
--- copyOf 는 이미 불변이면 복사도 안 한다
  List.copyOf(List.of(...)) == 원본 : true
  List.copyOf(뷰) == 뷰           : false
--- null 처리가 다르다
  unmodifiableList(null 포함) = [null]
  List.copyOf(null 포함) -> java.lang.NullPointerException
```

**첫 줄 — 복사하지 않는다.** 같은 인스턴스가 돌아온다.

javadoc `@implNote` 가 그렇게 적는다.

```text
@implNote
If the given Collection is an unmodifiable List,
calling copyOf will generally not create a copy.
```

**뷰를 넘기면 복사한다.**

- **뷰는 "unmodifiable List" 가 아니다.** 안이 바뀔 수 있으므로 그대로 돌려주면 스냅샷 계약이 깨진다.
- 그래서 `List.copyOf(뷰) == 뷰` 가 `false` 다 — 이 한 줄이 **뷰와 불변을 가르는 실측 증거**다.
- 거꾸로 **뷰를 `copyOf` 로 감싸면 그 시점의 스냅샷**이 된다. 경계를 넘길 때 쓰는 관용구다.

**`null` 이 들어 있으면 — `NullPointerException`.**\
`unmodifiableList` 는 **그대로 통과**시킨다(`[null]`).

- `List.copyOf` 는 방어로도 쓸 수 있지만, `null` 이 섞일 수 있는 데이터에서는 터진다.
- 세 팩토리의 `null` 축 전체는 [40 `List`·`Set` API 와 불변 팩토리](../40-list-set-and-immutable-factories/) 가 정본이다.

### 5. `Arrays.asList` 와 얕은 복사

**출력** (`Ex.java (59-b)`, JDK 21.0.5)

```text
--- Arrays.asList 는 또 다르다 (고정 크기 뷰)
  배열을 고치니 asList = [Z, b]
  asList.set 후 배열   = [Z, Y]
  asList.add -> UnsupportedOperationException
--- 얕은 복사라는 한계 — 원소 자체가 가변이면
  frozen.get(0) = [999, 2]   <- 원소는 공유된다
```

| | 결과 |
|---|---|
| (가) `arr[0]="Z"` 뒤 `asList` | **`[Z, b]`** |
| (나) `asList.set(1,"Y")` 뒤 `arr[1]` | **`Y`** |
| (다) `asList.add("c")` | `UnsupportedOperationException` |
| (라) `rows.get(0)[0]=999` 뒤 `frozen.get(0)[0]` | **`999`** |

**`Arrays.asList` 를 방어적 복사로 쓰면 안 되는 이유**

- **배열의 양방향 뷰**다. 배열을 고치면 리스트가 바뀌고, 리스트를 `set` 하면 배열이 바뀐다.
- `add` 만 막히니 **"불변인가 보다" 하고 넘어가기 쉽다.**
- 대안: `List.of(arr)`(배열을 복사한다) 또는 `Arrays.stream(arr).toList()`.

**(라) 가 보여 주는 한계 — 얕은 복사(shallow copy) / 얕은 불변.**

- 리스트를 아무리 잠가도 **원소인 `int[]` 는 그대로 공유**된다.
- 깊은 불변을 원하면 **원소 타입부터 불변**이어야 한다.

### 6. `record` 는 어디까지 해 주나

**출력** (`Ex.java (59-c)`, JDK 21.0.5 — 17 · 25 동일)

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

- (가) `[책, 펜] [99]` — 생성자에 넘긴 원본을 고치니 새어 들어왔다.
- (나) `[책, 펜, 또] [-1]` — 접근자로 꺼낸 것을 고치니 또 새어 들어왔다.
- (다) **`false`**.

**(다) 의 이유**

- `record` 의 자동 `equals` 는 **컴포넌트별로 비교**하는데, **배열 컴포넌트는 참조 비교**가 된다.\
  (배열은 `equals` 를 재정의하지 않아 `Object.equals`, 곧 `==` 와 같기 때문이다 — 자세한 것은 [14 `record`](../14-records/).)
- `List.of("책")` 끼리는 내용 비교로 같지만, `new int[]{1}` 둘은 **다른 객체**라 `false` 가 된다.

**막는 코드**

```java
record SafeOrder(String id, List<String> items, int[] counts) {
    SafeOrder {                                   // 컴팩트 생성자 — 들어올 때
        Objects.requireNonNull(id);
        items  = List.copyOf(items);
        counts = counts.clone();
    }
    @Override public int[] counts() { return counts.clone(); }   // 접근자 — 나갈 때
    @Override public boolean equals(Object o) { ... Arrays.equals(counts, s.counts); }
    @Override public int hashCode() { return Objects.hash(id, items, Arrays.hashCode(counts)); }
}
```

- 컴팩트 생성자에서는 **파라미터에 대입**한다(`this.items = ...` 는 컴파일 에러).
- `items` 는 `List.copyOf` 하나로 끝나고, `counts` 는 **접근자에도** `clone()` 이 필요하다.

**접근자만 복사하면 깨지는 불변식 — 복사 불변식**

- `Record` javadoc 이 `r.equals(new R(r.c1(), ..., r.cn()))` 가 **반드시 참**이어야 한다고 적는다.
- 접근자가 복사본을 주면 새로 만든 것의 배열이 다른 객체가 되어, **자동 `equals` 기준으로는 `false`** 가 된다.
- 그래서 **방어 복사는 `equals`/`hashCode` 재정의와 한 묶음**이다.\
  위 실행에서 `true` 가 나온 것은 `equals` 를 `Arrays.equals` 로 **같이 고쳤기 때문**이다.
- 이 불변식의 증명과 자세한 내용은 [14 `record`](../14-records/) 가 정본이다.

### 7. `final` 클래스가 아니면

**출력** (`Ex.java (59-d)`, JDK 21.0.5 — 17 · 25 동일)

```text
--- (3) final 이 아닌 클래스는 불변을 약속할 수 없다
  amount() 를 세 번 : 100 101 102
```

**`Money` 자신은 흠이 없는데 왜 문제인가**

- 밖에서는 **`Money` 타입으로** 받는다. `Money` 의 javadoc 에 "불변"이라고 적혀 있으면 그것을 믿는다.
- 그런데 실제 객체는 `FakeMoney` 이고, **동적 디스패치**로 재정의된 `amount()` 가 불린다\
  ([09 상속과 오버라이딩](../09-inheritance-overriding/)).
- 즉 **불변은 클래스 하나의 성질이 아니라 타입 계층 전체의 성질**이어야 한다.

**`Map` 키로 쓰면**

- 넣을 때와 찾을 때 **`hashCode` 가 달라져** 못 찾는다(계약의 "일관성" 위반).
- 증상과 실험은 [27 `equals`/`hashCode` 계약](../27-equals-hashcode-contract/) 이 정본이다.

**막는 방법 둘**

1. **클래스를 `final` 로.** 가장 단순하고 확실하다(`record` 는 이것이 강제다).
2. **생성자를 `private` 으로** 두고 정적 팩토리만 노출한다. 밖에서는 상속할 수 없고,\
   같은 패키지·중첩 클래스로는 여러 구현을 둘 수 있어 더 유연하다.

### 8. ★ 생성자가 재정의 가능한 메서드를 부르면

**출력** (`Ex.java (59-d)`, JDK 21.0.5 — 17 · 25 동일)

```text
--- (1) 생성자가 재정의 가능한 메서드를 부르면
    Child.describe label=완성된 라벨 data=null
```

- **`Base.describe` 가 아니라 `Child.describe` 가 돌았다** — 동적 디스패치라 그렇다.
- 그리고 **`data` 가 `null`** 이다. `Child` 의 필드 초기화는 `super(3)` 이 **끝난 뒤에** 일어나기 때문이다\
  ([06 초기화 순서](../06-initialization-order/)).

**`null` 인 쪽은 `data`, 멀쩡한 쪽은 `label` — 왜 다른가**

- `label` 은 `private final String label = "완성된 라벨";` — **컴파일 타임 상수**(상수 변수)다.
- 상수 변수는 **읽는 자리에 값이 박힌다**(JLS §13.1). 즉 **필드를 읽지 않는다.**
- `data` 는 `new ArrayList<>(...)` 라 상수가 아니므로 **진짜로 필드를 읽고**, 그 시점에 아직 `null` 이다.

**`javap -c` 로 확인**

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

- **`getfield` 가 `data` 하나뿐**이다. `label` 을 읽는 명령이 없다 — 문자열이 concat 레시피에 상수로 들어갔다.
- 외울 것은 명령 이름이 아니라 **"상수 변수는 필드를 읽지 않는다"**는 성질이다.

**특히 헷갈리는 이유**

- **어떤 필드는 멀쩡해 보이고 어떤 필드만 `null`** 이라서, "초기화가 안 됐다"는 가설이 서지 않는다.
- 실제 코드에서는 `String` 상수 필드가 많아 **일부만 `null`** 인 그림이 자주 나온다.
- 방어: **생성자가 부르는 메서드는 `private` 또는 `final` 로.**

### 9. `this` 유출의 다른 경로

**출력** (`Ex.java (59-d)`, JDK 21.0.5)

```text
--- (2) 생성자 안에서 this 를 밖에 넘기면
  생성 전 Registry 크기 = 0
  등록된 것이 같은 객체인가 = true
  (다른 스레드가 그 사이에 읽었다면 value 는 0 이었을 수 있다 — 안전 공개 위반)
```

**같은 객체다** — `Registry.ALL.get(0) == e` 가 `true`.

**무엇이 위험한가**

- **단일 스레드에서도 문제가 된다.** 등록 직후 누군가 그 객체의 메서드를 부르면\
  아직 `value` 가 0 인(=기본값) 상태를 본다. 위 코드에서는 등록이 대입보다 먼저다.
- **여러 스레드면 더 나쁘다.** 다른 스레드가 `Registry.ALL` 을 통해 그 참조를 보게 되는데,\
  생성자가 끝나기 전이라 **`final` 필드의 안전 공개 보장이 성립하지 않는다.**

**`final` 필드가 주는 보장**

- 생성자가 정상적으로 끝나면 `final` 필드가 "얼어붙고", **그 객체 참조를 본 스레드는 `final` 필드의 올바른 값을 본다.**\
  동기화 없이도 그렇다.
- **전제는 "생성 중에 참조가 새지 않았을 것"**이다. `this` 가 먼저 나가면 이 보장이 깨진다.

**어느 문서 어느 절** — **JLS §17.5 `final` Field Semantics** 다.

- 이 문서는 이 보장을 **명세 문장으로만** 적는다 — 데이터 경쟁은 재현이 보장되지 않아\
  "돌려 봤더니 괜찮았다"가 근거가 될 수 없기 때문이다.
- 메모리 모델 자체는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §9 가 정본이다.

### 10. 필드 타입별 방어법

**불변 타입에는 필요 없다** — `String`·`Integer`·`LocalDate`·`BigDecimal`·`Instant` 등.\
그냥 대입하고 그냥 반환한다.

**`List` 는 한 군데, 배열은 두 군데**

| | 생성자 | getter | 왜 |
|---|---|---|---|
| `List`/`Set`/`Map` | `List.copyOf(x)` | **그대로 반환** | `copyOf` 결과가 **복사본이면서 수정 불가**라 이미 막혀 있다 |
| 배열 | `x.clone()` | **`x.clone()`** | 배열에는 "수정 불가 배열"이라는 것이 없다 |

**다차원 배열에 `clone()` 은 부족하다**

- `clone()` 은 **한 겹만** 복사한다. 바깥 배열은 새것이지만 **안쪽 배열은 공유**된다.
- 안쪽까지 직접 돌며 복사해야 한다. 정본은 [05 배열](../05-arrays/).

**`Date` 필드**

- 복사(`new Date(d.getTime())`)로 막을 수는 있지만 **최선이 아니다.**
- 실행으로 본 증상 (`Ex.java (59-d)`):

```text
--- (5) 가변 Date 를 담으면 (java.time 을 쓰는 이유)
  밖에서 setTime 한 뒤 h.when().getTime() = 86400000
```

- **근본 해결은 타입 교체**다 — `Instant`·`LocalDateTime` 은 전부 불변이라 방어 복사 자체가 필요 없다.
- "복사로 막는다"보다 **"복사가 필요 없는 타입을 쓴다"**가 한 단계 위의 설계다.

### 11. 무엇이 계약이고 무엇이 구현인가

| 항목 | 계약 / 구현 | 근거 |
|---|---|---|
| `unmodifiableList` 가 **뷰** | **계약** | javadoc 본문의 `"read through"` |
| `copyOf` 가 **스냅샷** | **계약** | javadoc 본문의 `"will not reflect such modifications"` |
| `copyOf` 가 이미 불변이면 복사 안 함 | **`@implNote`** | 구현 참고사항 — 강한 계약이 아니다. 성능 최적화로만 믿는다 |
| `copyOf` 가 `null` 에 NPE | **계약** | `@throws NullPointerException` |
| `view.getClass()` 이름 | **구현** | `Collections$UnmodifiableRandomAccessList` 는 내부 클래스다 |
| `UnsupportedOperationException` 메시지 | **구현** | 실측에서 **`null`** 이었다 |
| `final` 필드의 안전 공개 | **언어**(JLS §17.5) | |
| 상수 변수가 호출부에 박히는 것 | **언어**(JLS §13.1) | 8번의 `javap` |

**클래스 이름에 기대면 안 된다.**

- `instanceof ImmutableCollections.List12` 같은 코드는 **내부 클래스**에 기대는 것이고, 애초에 접근도 안 된다.
- "불변인지" 판정하는 표준 API 는 없다 — **타입이 아니라 계약으로 다뤄야 한다.**

**메시지에도 기대면 안 된다.** 실측에서 `null` 이었고, 이는 구현의 자유다.

### 12. 다른 주제와 잇기

**불변이 아니면 `equals`/`hashCode` 계약에서 깨지는 것**

- **일관성(consistency)** 이다 — 같은 객체를 여러 번 비교하면 같은 답이 나와야 하는데,\
  상태가 바뀌면 답이 바뀐다.
- `HashMap` 에 넣은 뒤 키의 상태를 바꾸면 **버킷이 달라져 못 찾는다.**\
  실험과 다섯 조항은 [27 `equals`/`hashCode` 계약](../27-equals-hashcode-contract/) 이 정본이다.

**`String` 이 불변이라 얻는 것 넷**

1. **공유해도 안전** — 상수 풀이 성립한다.
2. **스레드 안전** — 동기화 없이 읽어도 된다.
3. **해시 캐시** — `hashCode` 를 한 번 계산해 필드에 저장한다.
4. **`Map` 키로 안전** — 넣은 뒤 내용이 바뀌어 못 찾는 일이 없다.

- 정본은 [35 `String`](../35-string/).

**"바꾼 사본"을 주는 메서드 둘**

- `String.toUpperCase()` — 자기를 안 바꾸고 대문자 새 문자열을 준다.
- `LocalDate.plusDays(1)` — 자기를 안 바꾸고 하루 뒤 날짜를 준다.
- (`BigDecimal.setScale(...)`·`Optional.map(...)` 도 같은 형태다.)

**불변으로 만들면 안 되는(또는 어려운) 자리**

| 자리 | 이유 |
|---|---|
| 정체성이 있고 계속 변하는 엔티티(주문·세션) | 변화 자체가 도메인이다 |
| 큰 데이터를 조금씩 고치는 버퍼 | 복사 비용 — `StringBuilder` 가 존재하는 이유 |
| setter 를 요구하는 프레임워크 | ORM·일부 직렬화. `record` 지원 여부를 먼저 확인한다 |
| 측정으로 확인된 핫패스 | **측정 후에만** 포기한다. 짐작으로 포기하지 않는다 |

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(59-a) | 방어 없음/절반/양쪽 세 단계, 배열·리스트 양쪽 통로, `UnsupportedOperationException` 메시지 | 17 · 21 · 25 (**동일**) |
| `Ex`(59-b) | `unmodifiableList` 뷰 대 `copyOf` 스냅샷(추가·비우기), 구현 클래스 이름, `copyOf` 의 동일성·뷰·`null`, `Arrays.asList` 양방향, 얕은 복사 | 17 · 21 · 25 (**동일**) |
| `Ex`(59-c) | `record` 의 얕은 불변, 컴팩트 생성자 + 접근자 방어, 복사 불변식, 배열 컴포넌트의 `equals` | 17 · 21 · 25 (**동일**) |
| `Ex`(59-d) `javap -c -p` | 생성자의 재정의 메서드 호출(`data=null`·`label` 상수 인라인), `this` 등록, `final` 아닌 클래스, `final` 참조, 가변 `Date` | 17 · 21 · 25 (**동일**) |
| `src.zip` 열람 | `Collections.unmodifiableList` javadoc(`read through`), `List.copyOf` javadoc + `@implNote`, 각 `@since` | 21 |

- 프로그램 **4개**, 실행 왕복 **12회**(4 × 3 JDK), `javap -c -p` **1회**.

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| `Collections$UnmodifiableRandomAccessList`·`ImmutableCollections$List12` | JDK 내부 구현 — 기대면 안 된다 |
| `UnsupportedOperationException` 의 메시지가 `null` | 구현 |
| `copyOf` 가 이미 불변이면 복사 안 하는 것 | `@implNote` — 계약보다 약하다 |
| `label` 이 `null` 이 아닌 것 | **언어 규칙**(상수 변수)이지만 `javap` 로 확인해야 납득된다 |

**버전이 오르면 다시 돌려야 할 것**

- `List.copyOf` 의 `@implNote`(동일 인스턴스 반환)가 유지되는지.
- `record` 에 `with` 류 문법이 생기면 방어 복사의 자리가 늘어난다.
- 나머지(뷰/스냅샷·`final` 의미론·상수 변수)는 **계약과 언어 규칙**이라 바뀌면 그것이 사건이다.

## 안 돌려 본 것

- **여러 스레드에서의 안전 공개** — 데이터 경쟁은 재현이 보장되지 않아 관찰로 쓰면 오히려 위험하다.\
  JLS §17.5 의 **명세 문장으로만** 적었다.
- **불변 대 가변의 성능 비교** — 재지 않았고 주장도 하지 않았다.
- `Map.copyOf`·`Set.copyOf` — `List.copyOf` 와 같은 계약이라 하나만 돌렸다(각 javadoc 은 읽었다).
- **직렬화·역직렬화에서 방어 복사가 우회되는 문제** — 일반 클래스는 생성자를 건너뛴다.\
  `record` 는 표준 생성자를 거치므로 안전하다는 실험이 [14 `record`](../14-records/) 에 있다.
- 프레임워크(Jackson·JPA)가 `record` 를 다루는 방식 — 라이브러리 층이라 이 배치의 범위 밖이다.
