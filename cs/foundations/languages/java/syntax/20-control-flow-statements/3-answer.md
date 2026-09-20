# java/syntax/20 — 제어문: 향상된 `for` · 레이블 `break`/`continue` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러 메시지는 Temurin JDK 에서 **실제로 돌려 얻은 것**이다.\
> 기본은 **21.0.5**이고, 도는 프로그램은 **17.0.13 · 25.0.1** 에서도 돌렸다.\
> 세 판에서 같았던 것은 "같았다"라고 **관찰로** 적었다 — 보장이 아니다.\
> 역어셈블은 `javap -c -p` 출력을 그대로 옮겼다.\
> javadoc 인용은 JDK 21.0.5 의 `lib/src.zip` 에서 복사한 것이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 한 줄이 두 가지로 펼쳐진다

**출력** — 실행 결과는 같다.

```text
array    sum = 16
iterable sum = 16
```

**바이트코드는 다르다.** (`javap -c -p Ex.class`, JDK 21.0.5)

```text
  static int sumArray(int[]);
    Code:
       0: iconst_0
       1: istore_1
       2: aload_0
       3: astore_2
       4: aload_2
       5: arraylength
       6: istore_3
       7: iconst_0
       8: istore        4
      10: iload         4
      12: iload_3
      13: if_icmpge     33
      16: aload_2
      17: iload         4
      19: iaload
      20: istore        5
      22: iload_1
      23: iload         5
      25: iadd
      26: istore_1
      27: iinc          4, 1
      30: goto          10
      33: iload_1
      34: ireturn
```

```text
  static int sumIterable(java.util.List<java.lang.Integer>);
    Code:
       0: iconst_0
       1: istore_1
       2: aload_0
       3: invokeinterface #7,  1            // InterfaceMethod java/util/List.iterator:()Ljava/util/Iterator;
       8: astore_2
       9: aload_2
      10: invokeinterface #13,  1           // InterfaceMethod java/util/Iterator.hasNext:()Z
      15: ifeq          38
      18: aload_2
      19: invokeinterface #19,  1           // InterfaceMethod java/util/Iterator.next:()Ljava/lang/Object;
      24: checkcast     #23                 // class java/lang/Integer
      27: invokevirtual #25                 // Method java/lang/Integer.intValue:()I
      30: istore_3
      31: iload_1
      32: iload_3
      33: iadd
      34: istore_1
      35: goto          9
      38: iload_1
      39: ireturn
```

**왜 그런가**

- 향상된 `for` 는 **문법 하나에 구현 둘**이다. 컴파일러가 대상 타입을 보고 갈라 준다.
- 배열 쪽의 특징 명령은 **`arraylength`**(그리고 `iaload`). **메서드 호출이 0회**다.
- `Iterable` 쪽은 원소 하나당 **`hasNext()` 와 `next()` 둘**이 불린다.\
  `iterator()` 는 루프 시작 전 한 번이다.\
  거기에 `next()` 가 `Object` 를 주므로 `checkcast` 가, `int` 로 받으므로 `intValue()`(언박싱)가 붙는다.
- **길이는 루프 밖에서 한 번만** 잰다 — `arraylength` 가 오프셋 5 에 있고, 루프 본체는 10 부터 시작한다.\
  그래서 루프 안에서 배열 변수를 더 긴 배열로 바꿔도 회차가 안 늘어난다(5번).

```text
  for (int x : a)                        for (int x : c)
        |                                      |
        v                                      v
  len = a.length   <- 한 번                it = c.iterator()   <- 한 번
  i = 0                                   while (it.hasNext())  <- 매 회차
  while (i < len)                             x = it.next()     <- 매 회차
      x = a[i]                                ...
      ...                                 (checkcast + intValue 가 뒤따른다)
      i++
```

### 2. `null` 을 순회하면 메시지가 갈린다

**출력** (JDK 21.0.5 — 17.0.13 · 25.0.1 에서도 문구가 같았다)

```text
--- (2) null 을 순회하면
던짐: Cannot read the array length because "<local4>" is null
던짐: Cannot invoke "java.util.List.iterator()" because "<local3>" is null
```

**왜 그런가**

- 둘 다 `NullPointerException` 이지만 **터지는 지점이 다르다.**
- 배열 쪽은 **`arraylength` 에서** 터진다 — 메시지가 `Cannot read the array length` 다.
- 컬렉션 쪽은 **`iterator()` 호출에서** 터진다 — 메시지가 `Cannot invoke ... .iterator()` 다.
- ★ **이 두 줄이 1번의 답을 런타임에서 다시 확인해 준다.**\
  도식으로 그린 것이 아니라 JVM 이 스스로 무엇을 하려다 실패했는지 말해 주는 것이다.
- 이 형태의 메시지(헬프풀 NPE)는 **JDK 15 부터 기본 켜짐**이다.\
  `<local4>` 는 변수 이름이 클래스 파일에 없을 때 JVM 이 붙이는 자리 표시다 — **구현 세부**다.

### 3. 순회 중에 컬렉션을 고치면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
--- (1) 순회 중 remove — 가운데 원소
던짐: java.util.ConcurrentModificationException
--- (3) 순회 중 add
던짐: java.util.ConcurrentModificationException
```

**예외를 잡지 않으면** 이렇게 나온다.

```text
Exception in thread "main" java.util.ConcurrentModificationException
	at java.base/java.util.ArrayList$Itr.checkForComodification(ArrayList.java:1095)
	at java.base/java.util.ArrayList$Itr.next(ArrayList.java:1049)
	at Ex.main(Ex.java:64)
```

**왜 그런가**

- (a)·(b) 둘 다 `java.util.ConcurrentModificationException` 이다.
- 스택 맨 위는 **`checkForComodification`**, 그 아래가 **`next()`** 다. `hasNext()` 가 아니다.
- 던지는 조건은 `ArrayList$Itr` 의 이 한 줄이다 (JDK 21.0.5 `src.zip`).

```text
        final void checkForComodification() {
            if (modCount != expectedModCount)
                throw new ConcurrentModificationException();
        }
```

- ★ **`add` 도 똑같이 위험하다.** 기준은 "지우느냐"가 아니라 **구조적 수정**이냐다.\
  `AbstractList` javadoc 이 정의한다 — `Structural modifications are those that change the size of the list`.
- `list.set(i, v)`(같은 자리의 값 교체)는 크기를 안 바꾸므로 구조적 수정이 아니다. CME 가 안 난다.

### 4. ★ 끝에서 두 번째를 지웠다

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
--- (2) 순회 중 remove — 끝에서 두 번째 원소
예외 없음: [a, b, d]
```

**왜 그런가**

- **예외가 안 난다.** 그리고 루프 본문에 들어온 원소는 **셋**(`a`·`b`·`c`)이다 — `"d"` 는 한 번도 안 들어왔다.
- 원인은 `ArrayList$Itr.hasNext()` 다 (JDK 21.0.5 `src.zip`).

```text
        public boolean hasNext() {
            return cursor != size;
        }
```

- `modCount` 를 **안 본다.** 크기만 본다.

```text
  "c" 를 돌려준 직후          지운 직후
  +---------------------+    +---------------------+
  | cursor = 3          |    | cursor = 3          |
  | size   = 4          |    | size   = 3  <- 줄었다|
  +---------------------+    +---------------------+
                                     |
                                     | hasNext(): 3 != 3 -> false
                                     v
                               루프 종료. next() 를 다시 안 부르므로
                               checkForComodification 도 안 돈다
```

- `next()` 안에서만 대조하는데, `hasNext()` 가 먼저 `false` 를 주니 **대조할 기회가 오지 않는다.**
- `ConcurrentModificationException` javadoc 이 이 상황을 미리 못박아 둔다.

```text
 * <p>Note that fail-fast behavior cannot be guaranteed as it is, generally
 * speaking, impossible to make any hard guarantees in the presence of
 * unsynchronized concurrent modification.  Fail-fast operations
 * throw {@code ConcurrentModificationException} on a best-effort basis.
 * Therefore, it would be wrong to write a program that depended on this
 * exception for its correctness: <i>{@code ConcurrentModificationException}
 * should be used only to detect bugs.</i>
```

- ★ **"CME 가 안 났으니 안전하다"는 추론이 여기서 깨진다.** 3번보다 이쪽이 위험하다 — 무음이기 때문이다.

### 5. 배열을 순회하면서 그 배열을 고치면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
--- (4) 배열을 순회하면서 그 배열을 고친다
예외 없음: 읽은 값 = 5 2 8 99 / 배열 = [5, 2, 8, 99]
```

**왜 그런가**

- **예외가 안 난다.** 배열에는 `modCount` 도 이터레이터도 없어서 **대조할 것이 없다.**
- 읽힌 값은 `5 2 8 99` 다. 1번의 바이트코드에서 `iaload` 가 **매 회차** 도는 것을 봤다 —\
  값은 미리 복사해 두지 않고 그때그때 읽는다.
- **배열을 더 길게 만들 수는 없다.** Java 배열은 길이가 고정이다.\
  변수를 더 긴 새 배열로 바꿔 봐도 회차가 안 늘어난다 — 돌려 확인했다(`Ex.java (20-h)`).

```java
int[] arr = { 5, 2, 8, 1 };
for (int x : arr) {
    sb.append(x).append(' ');
    arr = new int[]{ 0, 0, 0, 0, 0, 0 };   // 변수를 더 긴 배열로 바꿔 본다
}
```

```text
읽은 값 = 5 2 8 1 / 회차 = 4 / 지금 arr 길이 = 6
```

- 회차가 **4** 다. 루프는 시작할 때 배열 참조를 **자기 지역 변수로 복사**해 뒀다(1번의 `astore_2`).\
  변수 `arr` 이 어디를 가리키든 루프는 원래 배열을 계속 본다.
- ★ 어긋나는 지점은 이것이다 — **배열에서 통하던 "돌면서 고쳐도 된다"가 컬렉션에서는 3번·4번이 된다.**\
  같은 문법이 다른 보호 장치를 갖는다는 것이 이 주제의 핵심이다.

### 6. 안전하게 지우는 두 가지

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
Iterator.remove : [a, c, d]
removeIf        : [a, c, d]
```

**왜 그런가**

- `Itr.remove()` 의 구현에서 CME 를 막는 **한 줄**은 이것이다 (JDK 21.0.5 `src.zip`).

```text
        public void remove() {
            if (lastRet < 0)
                throw new IllegalStateException();
            checkForComodification();

            try {
                ArrayList.this.remove(lastRet);
                cursor = lastRet;
                lastRet = -1;
                expectedModCount = modCount;          <- 이 줄
            } catch (IndexOutOfBoundsException ex) {
                throw new ConcurrentModificationException();
            }
        }
```

- 이터레이터가 **자기가 지웠으니** 기대값을 다시 베껴 둔다. 그래서 다음 `next()` 에서 대조가 통과한다.
- ★ **건너뜀 문제도 같이 풀린다.** 바로 위 `cursor = lastRet` 이 그 일을 한다 —\
  지운 자리로 커서를 되돌리므로, 뒤 원소들이 한 칸씩 당겨진 만큼 커서도 당겨진다. 4번의 스킵이 안 생긴다.
- **여러 개를 지울 때는 `removeIf` 가 유리하다.**\
  `Iterator.remove()` 는 `ArrayList.this.remove(lastRet)` 를 부르므로 **지울 때마다 뒤를 당긴다.**\
  `removeIf` 는 표시용 비트 묶음을 만들어 **두 패스**로 처리한다 (JDK 21.0.5 `src.zip`).

```text
    boolean removeIf(Predicate<? super E> filter, int i, final int end) {
        Objects.requireNonNull(filter);
        int expectedModCount = modCount;
        final Object[] es = elementData;
        // Optimize for initial run of survivors
        for (; i < end && !filter.test(elementAt(es, i)); i++)
            ;
        // Tolerate predicates that reentrantly access the collection for
        // read (but writers still get CME), so traverse once to find
        // elements to delete, a second pass to physically expunge.
        if (i < end) {
            final int beg = i;
            final long[] deathRow = nBits(end - beg);
```

  주석이 설계를 그대로 적어 둔다 — **한 번 훑어 지울 것을 표시하고(`deathRow`), 두 번째 패스에서 실제로 치운다.**\
  옮기는 일이 마지막에 한 번뿐이다. 조건이 하나면 코드도 한 줄이다.
- **`next()` 없이 `remove()` 를 부르면** `IllegalStateException` 이다 — 돌려 확인했다(`Ex.java (20-g)`).

```text
--- (1) next() 없이 remove()
던짐: IllegalStateException (message=null)
```

- 위 구현의 첫 두 줄(`if (lastRet < 0) throw new IllegalStateException();`)이 그 자리다.\
  **메시지가 없다**(`null`)는 것도 함께 기억해 둔다 — 로그만 보면 원인이 안 보인다.

### 7. 레이블 없는 `break` 가 만드는 버그

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
plainBreak(8)    = (2,1) visited=8
labeledBreak(8)  = (0,2) visited=3
```

**왜 그런가**

```text
  GRID                 레이블 없는 break          레이블 있는 break
  5  2  8              (0,2) 에서 안쪽만 탈출      (0,2) 에서 통째로 탈출
  1  7  8              (1,2) 에서 또 찾음 -> 덮음   --
  3  8  4              (2,1) 에서 또 찾음 -> 덮음   --
                       결과 (2,1), visited = 8     결과 (0,2), visited = 3
```

- 레이블 없는 `break` 는 **가장 안쪽 루프만** 끊는다. 바깥 `for` 는 계속 돈다.
- 그래서 `hit` 이 **마지막으로 찾은 것**으로 덮인다. "첫 번째를 찾았다"가 **거짓**이 된다.
- 방문 횟수 8 은 0행 3칸 + 1행 3칸 + 2행 2칸이다 — 2행에서 `(2,1)` 을 찾고 그 행의 안쪽만 끊었다.
- ★ **이 버그는 예외를 안 낸다.** 답이 하나뿐인 테스트 데이터에서는 두 코드가 같은 값을 낸다.\
  중복이 있는 데이터가 들어와야 갈린다 — 그래서 운영에서 처음 드러난다.

### 8. `continue` 와 `continue 레이블`

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
plainContinue()  = 5 2 | 1 7 | 3 4 | 
labeledContinue()= 5 2 1 7 3 
```

**왜 그런가**

```text
  continue (레이블 없음)                    continue rows
  +-----------------------------+          +-----------------------------+
  | 그 칸 하나만 건너뛴다         |          | 바깥 for 의 다음 회차로 간다  |
  | 안쪽 루프는 계속 돈다         |          | 안쪽 루프의 나머지도 버린다   |
  | 행 끝의 "| " 는 찍힌다        |          | 행 끝의 "| " 를 못 만난다     |
  +-----------------------------+          +-----------------------------+
    -> "5 2 | 1 7 | 3 4 | "                  -> "5 2 1 7 3 "
```

- (b)에서 `sb.append("| ")` 는 **0번** 실행된다. 세 행 모두 `8` 을 만나 행을 포기했기 때문이다.
- `continue 레이블` 은 그 루프의 **증감식**(여기서는 `r++`)으로 점프한다. 조건 검사는 그 뒤에 온다.
- **붙을 수 있는 대상이 다르다.**

| | `break 레이블` | `continue 레이블` |
|---|---|---|
| 루프(`for`·`while`·`do`) | 된다 | 된다 |
| 레이블 붙은 블록 `{ }` | **된다** | **안 된다** (`not a loop label`) |
| 레이블 붙은 `switch` | 된다 | 안 된다 |

### 9. 레이블의 경계 넷 — 어기면 무엇이 출력되나

**출력** — (a) `continue` 를 블록 레이블에

```text
Ex.java:5: error: not a loop label: block
                continue block;      // block 은 루프가 아니다
                ^
1 error
```

**출력** — (b) 루프 밖에서 `break`

```text
Ex.java:4: error: break outside switch or loop
        if (x > 0) break;
                   ^
1 error
```

**출력** — (c) 레이블 오타

```text
Ex.java:5: error: undefined label: outr
            for (int j = 0; j < 3; j++) break outr;   // 오타
                                        ^
1 error
```

**출력** — (d) 레이블 중복

```text
Ex.java:5: error: label loop already in use
            loop:
            ^
1 error
```

**왜 그런가**

- (a) 에서 **`continue` 를 `break` 로 바꾸면 통과한다.** `break` 는 레이블 붙은 아무 문에나 붙는다.\
  메시지 `not a loop label` 이 규칙을 그대로 말한다.
- (b) 의 메시지 `break outside switch or loop` 가 `break` 의 대상 전부를 나열한다.\
  `if` 는 대상이 아니다 — 블록에 레이블을 붙이면 그 레이블로 나갈 수 있다.
- (c) 가 "변수를 못 찾음"이 아닌 이유: **레이블은 변수와 이름 공간이 다르다.**\
  그래서 같은 이름의 변수가 있어도 충돌하지 않고, 대신 없으면 `undefined label` 이 된다.
- (d) 가 금지된 이유: **안쪽이 바깥을 가리면 `break loop` 가 어느 쪽인지 정할 수 없다.**\
  변수 섀도잉과 달리 레이블은 "사용 중이면 그것으로 끝"이다.

### 10. 향상된 `for` 의 대상 조건

**출력** — (a) `Map`

```text
Ex.java:5: error: for-each not applicable to expression type
        for (var e : m) System.out.println(e);
                     ^
  required: array or java.lang.Iterable
  found:    Map<String,Integer>
1 error
```

**출력** — (b) 직접 만든 타입

```text
Ex.java:5: error: for-each not applicable to expression type
        for (int x : b) System.out.println(x);
                     ^
  required: array or java.lang.Iterable
  found:    Bag
1 error
```

**왜 그런가**

- ★ 두 에러가 **같다.** 조건이 하나(`array or java.lang.Iterable`)뿐이라 실패 모양도 하나다.
- `required:` 줄이 이 문법의 **조건 전부**다. 더 없다.
- (a) 를 고치는 셋 — 전부 돌려 확인했다(`Ex.java (20-g)`).

```java
for (Map.Entry<String, Integer> e : m.entrySet()) ...
for (String k : m.keySet()) ...
for (int v : m.values()) ...
```

```text
--- (3) Map 을 도는 세 가지
a=1 b=2 
a b 
1 2 
```

- (b) 는 **`implements Iterable<Integer>` 를 붙이고 `iterator()` 를 구현**하면 된다 — 돌려 확인했다.

```java
record Bag(int[] items) implements Iterable<Integer> {
    @Override public Iterator<Integer> iterator() {
        return new Iterator<>() {
            int i = 0;
            public boolean hasNext() { return i < items.length; }
            public Integer next() { return items[i++]; }
        };
    }
}
```

```text
--- (4) Iterable 을 직접 구현하면 향상된 for 가 된다
1 2 3 
```

- 필드로 배열을 **가진 것**과 `Iterable` **인 것**은 다르다. 컴파일러는 후자만 본다.

### 11. 루프 변수에 대입하면

**출력** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
--- (1) 루프 변수에 대입해도 원본은 안 바뀐다
배열 = [5, 2, 8, 1]
리스트 = [a!, b!]
```

**왜 그런가**

- 루프 변수는 **매 회차 만들어지는 지역 변수**다. 1번의 바이트코드에서 `istore 5` / `istore_3` 가 그 자리다.
- 거기에 대입하면 **그 지역 변수의 칸**만 바뀐다. 배열 칸이나 리스트 칸과는 무관하다.
- 반면 `sb.append("!")` 는 **변수가 가리키는 객체**를 바꾼다. 리스트가 들고 있는 것도 같은 객체다.

```text
  sb.append("!")                          sb = new StringBuilder("z")
  +---------+        +-----------+        +---------+        +-----------+
  | sb 칸   |------->| "a" 객체  |        | sb 칸   |--X     | "a" 객체  |
  +---------+        +-----------+        +---------+  \     +-----------+
       ^                   ^                   ^        \          ^
  list[0] 칸 -------------+               list[0] 칸 ---+---------+
                                                          \
                                                           +-> 새 "z" 객체
  객체를 고쳤다 -> 리스트에서도 보인다       칸을 바꿨다 -> 리스트는 그대로
```

- 정본은 [**03번 주제**](../03-variables-and-assignment/)(전부 값 전달)다. 여기서는 루프에서의 모양만 다뤘다.
- **`final` 은 붙일 수 있다** — 돌려 확인했다(`Ex.java (20-g)`).

```java
for (final String s : l2) System.out.print(s + " ");
```

```text
--- (2) 향상된 for 의 변수에 final
a b 
```

- 오히려 `final` 을 붙이면 "대입해도 소용없는 자리"에 대입하는 실수를 **컴파일러가 막아 준다.**

### 12. 어디까지가 언어 보장인가

**왜 그런가**

- **"컬렉션을 순회 중에 고치면 CME 가 난다"는 거짓이다.** 두 군데서 깨진다.
  1. 나는 구현에서도 **항상 나지는 않는다** — 4번(끝에서 두 번째)이 그 예다.
  2. **아예 안 내는 구현**이 있다 — `CopyOnWriteArrayList`·`ConcurrentHashMap`.
- `modCount` 를 쓰는 것은 **선택**이다. 근거는 `AbstractList` javadoc 이다 (JDK 21.0.5 `src.zip`).

```text
     * <p><b>Use of this field by subclasses is optional.</b> If a subclass
     * wishes to provide fail-fast iterators (and list iterators), then it
     * merely has to increment this field in its {@code add(int, E)} and
     * {@code remove(int)} methods ...  If an implementation
     * does not wish to provide fail-fast iterators, this field may be
     * ignored.
```

- **줄 번호는 버전마다 달랐다.** 같은 프로그램의 스택 트레이스에서 이렇게 갈렸다.

| JDK | `checkForComodification` | `next` |
|---|---|---|
| 17.0.13 | `ArrayList.java:1013` | `ArrayList.java:967` |
| 21.0.5 | `ArrayList.java:1095` | `ArrayList.java:1049` |
| 25.0.1 | `ArrayList.java:1096` | `ArrayList.java:1050` |

- 같은 것은 **클래스 이름과 메서드 이름**뿐이다. 로그 파싱에 줄 번호를 쓰면 판 올릴 때 깨진다.
- **CME 를 안 내는 컬렉션** 예: `CopyOnWriteArrayList`.\
  이터레이터가 **그 시점의 스냅샷**을 들고 돌기 때문에 원본을 고쳐도 무관하다.\
  대가는 **낡은 뷰**다 — 순회 중 추가한 원소는 그 순회에서 안 보인다. 그리고 쓰기마다 배열을 복사한다.\
  계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다.

### 13. 정본 경계

**왜 그런가**

| 주제 | 그쪽이 다루는 것 | 여기가 다루는 것 |
|---|---|---|
| **43번** `Iterator`·fail-fast | `Iterator`/`ListIterator` API 전체와 fail-fast 계약 | 향상된 `for` 를 설명하는 데 필요한 `hasNext`/`next`/`remove` 셋 |
| [**05번**](../05-arrays/) 배열 | 배열 생성·기본값·공변성·`Arrays` 유틸 | 배열을 **순회하는 문법**과 그때 길이를 언제 재나 |
| [**03번**](../03-variables-and-assignment/) 값 전달 | 대입·참조·`final`·effectively final 의 규칙 | 그 규칙이 **루프 변수에서** 나타나는 모양 |
| [`../../../../../data-structure/`](../../../../../data-structure/) | `ArrayList` 가 왜 배열을 들고 있나(증폭·상환) | 내부를 설명하지 않는다 |
| [**21번**](../21-switch-statement-and-expression/) `switch` | 분기와 `break` 의 `switch` 안에서의 의미 | 반복과 점프까지 |

- **레이블 `break` 의 대안 셋**.

| 수단 | 언제 나은가 |
|---|---|
| 레이블 `break` | 두 겹이고, 찾은 뒤 **같은 메서드에서 이어서** 할 일이 있을 때 |
| 메서드로 빼고 `return` | 찾는 일이 **독립된 관심사**일 때 — 대개 이쪽이 읽기 낫다 |
| 스트림 `findFirst` | 원본이 컬렉션이고 조건을 **식 하나**로 쓸 수 있을 때 ([**46번**](../46-terminal-operations/)) |

- 플래그 변수(`boolean found`)는 셋 어디에도 없다. **조건이 두 군데로 흩어져 가장 읽기 나쁘다.**
- **`for (;;)` 와 `while (true)` 는 같은 바이트코드다** — 돌려 확인했다(`Ex.java (20-f)`, JDK 21.0.5).

```text
  static int a();            <- for (;;)        static int b();            <- while (true)
    Code:                                         Code:
       0: iconst_0                                   0: iconst_0
       1: istore_0                                   1: istore_0
       2: iinc          0, 1                         2: iinc          0, 1
       5: iload_0                                    5: iload_0
       6: iconst_3                                   6: iconst_3
       7: if_icmpne     2                            7: if_icmpne     2
      10: goto          13                          10: goto          13
      13: iload_0                                   13: iload_0
      14: ireturn                                   14: ireturn
```

- **`goto` 는 쓸 수 없고 이름으로도 못 쓴다** — 돌려 확인했다(`Ex.java (20-e7)`).

```text
Ex.java:4: error: not a statement
        int goto = 2;
        ^
Ex.java:4: error: ';' expected
        int goto = 2;
           ^
2 errors
```

- 같은 파일에서 `int goto1 = 1;` 은 통과했다. **`goto` 만 막힌다** — 자리를 비워 둔 예약어라는 뜻이다.\
  레이블 `break`/`continue` 는 "뒤로 못 가고 밖으로만 나가는 `goto`" 로 읽으면 정확하다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex (20-a)` | 배열/`Iterable` 향상된 `for` 의 실행 결과가 같다 | 17 · 21 · 25 (출력 동일) |
| `Ex (20-a)` + `javap -c -p` | 배열 = `arraylength`+`iaload` / `Iterable` = `iterator`·`hasNext`·`next`+`checkcast` | 21 |
| `Ex (20-b)` | 레이블 유무로 `break`/`continue` 결과가 갈린다 · `for(;;)` · 두 변수 `for` · 블록 레이블 | 17 · 21 · 25 (출력 동일) |
| `Ex (20-c)` | 순회 중 `remove`/`add` -> CME · 끝에서 두 번째 -> 무음 스킵 · 배열은 무예외 · `Iterator.remove`/`removeIf` · 불변 리스트 | 17 · 21 · 25 (출력 동일, **스택 트레이스 줄 번호만 다름**) |
| `Ex (20-d)` | 루프 변수 대입은 원본 무영향 · `null` 순회의 두 NPE 메시지 | 17 · 21 · 25 (출력 동일) |
| `Ex (20-e1)` | `continue` 를 블록 레이블에 -> `not a loop label: block` | 21 |
| `Ex (20-e2)` | 루프 밖 `break` -> `break outside switch or loop` | 21 |
| `Ex (20-e3)` | 레이블 오타 -> `undefined label: outr` | 21 |
| `Ex (20-e4)` | `Iterable` 아닌 타입 -> `required: array or java.lang.Iterable` | 21 |
| `Ex (20-e5)` | 레이블 중복 -> `label loop already in use` | 21 |
| `Ex (20-e6)` | `Map` 직접 순회 -> 같은 `for-each not applicable` | 21 |
| `Ex (20-e7)` | `int goto = 2;` -> 파싱 에러 2개 (`goto1` 은 통과) | 21 |
| `Ex (20-f)` + `javap -c -p` | `for(;;)` 와 `while(true)` 의 바이트코드가 한 바이트도 안 다르다 | 21 |
| `Ex (20-g)` | `next()` 없는 `remove()` -> `IllegalStateException(null)` · 향상된 `for` 에 `final` · `Map` 세 가지 순회 · 직접 만든 `Iterable` | 17 · 21 · 25 (출력 동일) |
| `Ex (20-h)` | 순회 중 배열 변수를 더 긴 배열로 바꿔도 회차가 안 늘어난다(4회) | 17 · 21 · 25 (출력 동일) |
| `src.zip` (`AbstractList.java`) | `modCount` javadoc — 구조적 수정 정의 · fail-fast · **"use is optional"** | 21.0.5 |
| `src.zip` (`ConcurrentModificationException.java`) | 클래스 javadoc — `best-effort basis` · `should be used only to detect bugs` | 21.0.5 |
| `src.zip` (`ArrayList.java`) | `Itr.hasNext()`/`next()`/`remove()`/`checkForComodification()` · `removeIf(filter, i, end)` 의 두 패스 구현 | 21.0.5 |

**합계** — 프로그램 15개 · `javac` 24회 · `java` 12회 · `javap` 2회(메서드 6개 덤프).

**구현 의존 항목** — 버전이 오르면 다시 돌려야 하는 것

- **스택 트레이스의 줄 번호**는 17 · 21 · 25 에서 전부 달랐다. 클래스·메서드 이름만 같다.
- **`javap` 의 오프셋 숫자와 명령 배치**는 javac 의 코드 생성 방식이다.\
  외울 것은 명령 이름이 아니라 **"배열은 호출이 0회, `Iterable` 은 원소당 2회"** 라는 성질이다.
- **헬프풀 NPE 의 `<local4>` 같은 이름**은 JVM 이 만드는 문구다.
- **에러 메시지의 문구 자체**는 javac 의 것이다. 다른 컴파일러는 다르게 쓴다.
- 세 JDK 에서 출력이 같았던 것은 **관찰**이다. 보장은 javadoc 과 에러 메시지 쪽에만 있다 —\
  특히 `modCount` 는 javadoc 스스로 **"선택"** 이라 적었으므로, 다른 컬렉션 구현에서는 4번의 결과가 또 다를 수 있다.
