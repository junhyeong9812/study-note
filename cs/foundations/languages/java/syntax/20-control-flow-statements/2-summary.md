# java/syntax/20 — 제어문: 향상된 `for` · 레이블 `break`/`continue` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — JDK 21.0.5 의 `lib/src.zip` 을 **직접 풀어 읽은** javadoc·구현 셋이다.\
> `java.base/java/util/AbstractList.java` — `protected transient int modCount` 의 javadoc(구조적 수정·fail-fast 정의).\
> `java.base/java/util/ConcurrentModificationException.java` — 클래스 javadoc(`best-effort basis` · `should be used only to detect bugs`).\
> `java.base/java/util/ArrayList.java` — `ArrayList.Itr` 의 `hasNext()` · `next()` · `checkForComodification()` 구현.\
> 인용은 **그 파일에서 복사한 것만** 옮겼다. JLS 본문은 열지 않았다.
> **실행 검증** — 이 문서의 모든 출력·에러 메시지는 Temurin JDK 에서 실제로 돌려 얻은 것이다.\
> 프로그램 4개 + 컴파일 에러용 6개. `javac` 24회 · `java` 12회 · `javap` 2회.\
> 도는 프로그램 4개는 **17.0.13 · 21.0.5 · 25.0.1 셋 다**에서 돌렸다 — 출력이 같았던 것과 갈린 것을 나눠 적었다.\
> 역어셈블은 `javap -c -p` 출력을 **그대로** 옮겼다.
> **버전** — 향상된 `for` 는 **Java 5**. 레이블 `break`/`continue` 와 세 칸 `for` 는 **Java 1.0** 부터 있다.\
> 이 주제에는 21·25 에서 새로 생긴 것이 없다. 대신 **21 이후 주제 넷(21·22·23·24)이 전부 이 위에 얹힌다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 `javap` 출력·javac 에러 메시지·`src.zip` 구현으로 접지했다.

## 한눈에 — 쉽게 말하면

**향상된 `for` 는 「컨베이어 벨트」다. 그런데 벨트가 두 종류다.**

하나는 **번호표를 세는 벨트**(배열), 다른 하나는 **다음 상자를 물어보는 벨트**(`Iterable`).\
소스에서는 `for (int x : a)` 로 똑같이 생겼지만, **컴파일되면 완전히 다른 코드**가 된다.\
그 차이가 "왜 배열은 순회 중에 고쳐도 안 터지고 리스트는 터지나"의 답 전부다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 번호표를 세는 벨트 | 배열용 향상된 `for` — 길이를 한 번 재고 인덱스를 센다 |
| 다음 상자를 물어보는 벨트 | `Iterable` 용 향상된 `for` — `iterator()`·`hasNext()`·`next()` |
| 벨트가 "다음 있나요?" 하고 묻는 것 | `hasNext()` |
| 창고에서 상자를 꺼내 주는 것 | `next()` |
| 창고 문에 붙은 **재고 변경 횟수** 게시판 | `modCount` |
| 상자를 꺼낼 때 게시판 숫자를 대조 | `checkForComodification()` |
| 숫자가 달라서 작업을 중단 | `ConcurrentModificationException` |
| 비상구에 붙인 **층 이름표** | 레이블(`search:`) |
| "이 층 말고 건물 밖으로" | `break 레이블` |
| "이 층은 그만 보고 다음 층으로" | `continue 레이블` |

```text
배열용 벨트                              Iterable 용 벨트
+-------------------------------+       +-------------------------------+
| len = a.length   (한 번만)    |       | it = c.iterator()             |
| i = 0                         |       |                               |
| while (i < len) {             |       | while (it.hasNext()) {        |
|     x = a[i];                 |       |     x = it.next();            |
|     ...                       |       |     ...                       |
|     i++;                      |       | }                             |
| }                             |       |                               |
+-------------------------------+       +-------------------------------+
  창고를 안 거친다                        창고(컬렉션)에 매번 물어본다
  -> 게시판(modCount)도 안 본다           -> 게시판이 바뀌면 여기서 터진다
```

**똑같은 구조로** Java 가 이렇게 동작한다: 번호표 = 로컬 인덱스 변수, 게시판 = `AbstractList.modCount`,\
대조 = `ArrayList$Itr.checkForComodification()`, 작업 중단 = `ConcurrentModificationException`.

실무에서 이게 값을 내는 자리는 **"조회하면서 지우는 코드"**다.\
리스트를 돌면서 조건에 맞는 것을 빼는 코드는 거의 항상 이 주제의 함정 위에 서 있다.

> **fail-fast** — 잘못된 상태를 **발견하는 즉시** 예외로 멈추는 설계.\
> 예: 리스트를 순회하는 중에 크기가 바뀌면, 이상한 값을 돌려주는 대신 `next()` 에서 바로 예외를 던진다.

> **구조적 수정(structural modification)** — 컬렉션의 **크기를 바꾸는** 변경.\
> 예: `add`·`remove`·`clear` 는 구조적 수정이고, `set`(같은 자리의 값 교체)은 아니다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 셋을 과녁으로 둔다.

1. 향상된 `for` 한 줄이 **무엇으로 펼쳐지는가** — 배열과 `Iterable` 이 왜 다른 코드가 되는가.
2. 순회 중 수정이 **왜** 터지는가 — 그리고 **왜 어떤 경우엔 안 터지는가**(이쪽이 더 위험하다).
3. 레이블 `break`/`continue` 는 **어느 자리에서만** 다른 수단보다 나은가.

## 동작 방식

### (1) 향상된 `for` 는 두 갈래로 펼쳐진다

**언제 쓰나** — "배열이든 리스트든 똑같이 돌면 되는 거 아닌가"를 따질 때.

`Ex.java (20-a)` — 같은 한 줄을 배열과 `List` 에 각각 쓴다.

```java
import java.util.List;

public class Ex {
    static int sumArray(int[] a) {
        int s = 0;
        for (int x : a) s += x;
        return s;
    }

    static int sumIterable(List<Integer> a) {
        int s = 0;
        for (int x : a) s += x;
        return s;
    }

    public static void main(String[] args) {
        int[] arr = { 5, 2, 8, 1 };
        System.out.println("array    sum = " + sumArray(arr));
        System.out.println("iterable sum = " + sumIterable(List.of(5, 2, 8, 1)));
    }
}
```

**실행 결과** (JDK 21.0.5 — 17.0.13 · 25.0.1 에서도 같았다)

```text
array    sum = 16
iterable sum = 16
```

출력은 같지만 **컴파일 결과가 다르다.** `javap -c -p Ex.class` 로 두 메서드를 나란히 본다.

```text
  static int sumArray(int[]);
    Code:
       0: iconst_0
       1: istore_1
       2: aload_0
       3: astore_2
       4: aload_2
       5: arraylength                  <- 길이를 여기서 한 번만 잰다
       6: istore_3
       7: iconst_0
       8: istore        4              <- 인덱스 i = 0
      10: iload         4
      12: iload_3
      13: if_icmpge     33
      16: aload_2
      17: iload         4
      19: iaload                       <- a[i] 를 직접 읽는다
      20: istore        5
      22: iload_1
      23: iload         5
      25: iadd
      26: istore_1
      27: iinc          4, 1           <- i++
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

그림 해설 (한 단계씩):

- **배열 쪽에는 메서드 호출이 하나도 없다.** `arraylength` 로 길이를 한 번 재고 `iaload` 로 읽을 뿐이다.
- **`Iterable` 쪽은 호출이 셋이다** — `iterator()` · `hasNext()` · `next()`.\
  게다가 `next()` 가 `Object` 를 돌려주므로 `checkcast` 와 `intValue()`(언박싱)가 따라붙는다.
- 배열 쪽 `arraylength` 가 **루프 밖에 한 번만** 있다는 점이 중요하다.\
  루프 안에서 배열의 내용을 바꿔도 **길이는 다시 재지 않는다.**
- ★ 이 차이가 런타임 메시지에서도 그대로 드러난다 — `null` 을 넘겨 보면 된다(「어디서 틀리나」 4번).

**비용** — 배열 쪽은 호출 0회, `Iterable` 쪽은 원소당 호출 2회(`hasNext`+`next`) + 박싱 타입이면 언박싱 1회.\
대신 `Iterable` 쪽은 **어떤 컬렉션이든 같은 코드로 돈다.**

### (2) 순회 중 수정 — `modCount` 가 하는 일

**언제 쓰나** — "왜 리스트를 돌면서 지우면 터지나"를 설명할 때.

근거는 `src.zip` 의 `AbstractList.java` javadoc 이다 (JDK 21.0.5 — 문장 그대로).

```text
    /**
     * The number of times this list has been <i>structurally modified</i>.
     * Structural modifications are those that change the size of the
     * list, or otherwise perturb it in such a fashion that iterations in
     * progress may yield incorrect results.
     *
     * <p>This field is used by the iterator and list iterator implementation
     * returned by the {@code iterator} and {@code listIterator} methods.
     * If the value of this field changes unexpectedly, the iterator (or list
     * iterator) will throw a {@code ConcurrentModificationException} in
     * response to the {@code next}, {@code remove}, {@code previous},
     * {@code set} or {@code add} operations.  This provides
     * <i>fail-fast</i> behavior, ...
     */
    protected transient int modCount = 0;
```

그리고 그것을 실제로 쓰는 쪽이 `ArrayList.Itr` 이다 (같은 `src.zip`).

```text
    private class Itr implements Iterator<E> {
        int cursor;       // index of next element to return
        int lastRet = -1; // index of last element returned; -1 if no such
        int expectedModCount = modCount;
        ...
        public boolean hasNext() {
            return cursor != size;                    <- modCount 를 안 본다
        }

        public E next() {
            checkForComodification();                 <- 여기서만 본다
            ...
        }

        final void checkForComodification() {
            if (modCount != expectedModCount)
                throw new ConcurrentModificationException();
        }
    }
```

```text
  순회 시작                                리스트
  +--------------------------+            +--------------------------+
  | expectedModCount = 4     |  <- 복사 - | modCount = 4             |
  | cursor = 0               |            | [a, b, c, d] size=4      |
  +--------------------------+            +--------------------------+
          |
          | next() -> "a"  (4 == 4 OK)
          | next() -> "b"  (4 == 4 OK)
          | 여기서 list.remove("b")
          v
  +--------------------------+            +--------------------------+
  | expectedModCount = 4     |            | modCount = 5   <- 늘었다 |
  | cursor = 2               |            | [a, c, d] size=3         |
  +--------------------------+            +--------------------------+
          |
          | hasNext() -> cursor(2) != size(3) -> true
          | next()    -> checkForComodification() -> 4 != 5 -> 던진다
          v
     ConcurrentModificationException
```

`Ex.java (20-c)` 의 (1)·(3)·(7) 이 이 경로다.

```java
List<String> l1 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l1) if (s.equals("b")) l1.remove(s);
```

**실행 결과** (JDK 21.0.5 — 예외를 잡지 않고 그대로 둔 것)

```text
Exception in thread "main" java.util.ConcurrentModificationException
	at java.base/java.util.ArrayList$Itr.checkForComodification(ArrayList.java:1095)
	at java.base/java.util.ArrayList$Itr.next(ArrayList.java:1049)
	at Ex.main(Ex.java:64)
```

- 스택의 맨 위가 **`checkForComodification`** 이다 — 위 구현과 정확히 같은 자리다.
- 두 번째 줄이 **`next()`** 다. `hasNext()` 가 아니다. 이것이 (3) 의 원인이 된다.
- ★ **줄 번호는 JDK 판마다 다르다** — 17 에서는 `ArrayList.java:1013` / `:967`,\
  25 에서는 `:1096` / `:1050` 이었다. 클래스와 메서드 이름만 같다.

**비용** — 검사는 `int` 비교 한 번이다. 비용이 아니라 **보호 장치**로 읽는다.

### (3) 조용히 지나가는 경우 — 이쪽이 더 위험하다

**언제 쓰나** — "CME 만 안 나면 안전한 것 아닌가"를 따질 때.

**언제 쓰나**의 답은 아니다. (2) 의 그림에서 `hasNext()` 가 `modCount` 를 **안 본다**는 점이 여기서 터진다.

```text
  끝에서 두 번째("c")를 지웠을 때

  next() -> "c" 를 돌려준 직후          지운 직후
  +--------------------------+         +--------------------------+
  | cursor = 3               |         | cursor = 3               |
  | [a, b, c, d]  size = 4   |         | [a, b, d]     size = 3   |
  +--------------------------+         +--------------------------+
                                              |
                                              | hasNext(): cursor(3) != size(3) -> false
                                              v
                                       루프가 조용히 끝난다 — "d" 는 한 번도 안 본다
```

`Ex.java (20-c)` 의 (2).

```java
List<String> l2 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l2) if (s.equals("c")) l2.remove(s);
System.out.println("예외 없음: " + l2);
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
--- (2) 순회 중 remove — 끝에서 두 번째 원소
예외 없음: [a, b, d]
```

- **예외가 안 난다.** 그리고 `"d"` 는 루프 본문에 한 번도 들어오지 않았다.
- 이것이 **무음 실패**다. CME 는 시끄럽게 실패하지만, 이 경우는 조용히 한 원소를 건너뛴다.
- `ConcurrentModificationException` 의 javadoc 이 이 상황을 직접 경고한다 (JDK 21.0.5 `src.zip`).

```text
 * <p>Note that fail-fast behavior cannot be guaranteed as it is, generally
 * speaking, impossible to make any hard guarantees in the presence of
 * unsynchronized concurrent modification.  Fail-fast operations
 * throw {@code ConcurrentModificationException} on a best-effort basis.
 * Therefore, it would be wrong to write a program that depended on this
 * exception for its correctness: <i>{@code ConcurrentModificationException}
 * should be used only to detect bugs.</i>
```

```text
  터지는 경우 (가운데를 지움)             안 터지는 경우 (끝에서 두 번째를 지움)
  +-----------------------------+       +-----------------------------+
  | 예외가 즉시 난다             |       | 예외가 안 난다               |
  | 스택 트레이스가 자리를 알려줌 |       | 마지막 원소를 조용히 건너뜀   |
  | 테스트에서 바로 잡힌다       |       | 테스트가 4개짜리 데이터면     |
  |                             |       |   통과해 버린다              |
  +-----------------------------+       +-----------------------------+
    -> 고치기 쉽다                         -> 운영에서 데이터가 샌다
```

**비용** — 없다. 비용이 아니라 **설계의 틈**이다.\
`hasNext()` 에 검사를 넣지 않은 것은 성능 선택이고, javadoc 이 "best-effort" 라고 미리 밝혀 둔 범위다.

### (4) 안전하게 지우는 두 가지

**언제 쓰나** — 순회하면서 원소를 빼야 할 때. (2)·(3) 을 피하는 정석이다.

`Ex.java (20-c)` 의 (5).

```java
List<String> l5 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (Iterator<String> it = l5.iterator(); it.hasNext(); )
    if (it.next().equals("b")) it.remove();

List<String> l6 = new ArrayList<>(List.of("a", "b", "c", "d"));
l6.removeIf(s -> s.equals("b"));
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
Iterator.remove : [a, c, d]
removeIf        : [a, c, d]
```

`Itr.remove()` 의 구현을 보면 왜 안전한지가 한 줄로 보인다 (`src.zip`).

```text
        public void remove() {
            if (lastRet < 0)
                throw new IllegalStateException();
            checkForComodification();

            try {
                ArrayList.this.remove(lastRet);
                cursor = lastRet;
                lastRet = -1;
                expectedModCount = modCount;          <- 게시판을 다시 베껴 둔다
            } catch (IndexOutOfBoundsException ex) {
                throw new ConcurrentModificationException();
            }
        }
```

- **`expectedModCount = modCount` 한 줄**이 전부다. 이터레이터가 직접 지웠으니 기대값을 갱신한다.
- `cursor = lastRet` 도 중요하다 — 지운 자리로 커서를 되돌려서 **다음 원소를 건너뛰지 않는다.**\
  (3) 에서 일어난 건너뜀이 여기서는 일어나지 않는 이유다.
- `removeIf` 는 한 줄로 끝나고 **의도가 코드에 드러난다.** 조건이 하나면 이쪽이 낫다.

**비용** — `removeIf` 는 `ArrayList` 에서 한 번 훑고 한 번 압축한다. 반복 `remove(i)` 보다 싸다.\
`Iterator.remove()` 는 지울 때마다 배열을 당기므로 많이 지우면 `removeIf` 쪽이 낫다.

### (5) 레이블 `break` — 중첩 루프의 유일한 출구

**언제 쓰나** — 이중 루프 안에서 찾은 즉시 **바깥까지** 빠져나와야 할 때.

`Ex.java (20-b)` — 같은 격자에서 같은 값을 찾는다. 하나는 레이블이 없고 하나는 있다.

```java
static final int[][] GRID = {
    { 5, 2, 8 },
    { 1, 7, 8 },
    { 3, 8, 4 },
};

static String plainBreak(int target) {
    String hit = "없음";
    int visited = 0;
    for (int r = 0; r < GRID.length; r++) {
        for (int c = 0; c < GRID[r].length; c++) {
            visited++;
            if (GRID[r][c] == target) { hit = "(" + r + "," + c + ")"; break; }
        }
    }
    return hit + " visited=" + visited;
}

static String labeledBreak(int target) {
    String hit = "없음";
    int visited = 0;
    search:
    for (int r = 0; r < GRID.length; r++) {
        for (int c = 0; c < GRID[r].length; c++) {
            visited++;
            if (GRID[r][c] == target) { hit = "(" + r + "," + c + ")"; break search; }
        }
    }
    return hit + " visited=" + visited;
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
plainBreak(8)    = (2,1) visited=8
labeledBreak(8)  = (0,2) visited=3
```

```text
  레이블 없는 break                        레이블 있는 break
  +-----------------------------+         +-----------------------------+
  | 5  2  8 <- 찾음, 안쪽만 탈출 |         | 5  2  8 <- 찾음, 통째로 탈출 |
  | 1  7  8 <- 또 찾음(덮어씀)   |         | -  -  -                     |
  | 3  8  4 <- 또 찾음(덮어씀)   |         | -  -  -                     |
  +-----------------------------+         +-----------------------------+
    visited = 8, 결과 = (2,1)               visited = 3, 결과 = (0,2)
    "첫 번째를 찾았다" 가 거짓이 된다        "첫 번째를 찾았다" 가 참이다
```

그림 해설 (한 단계씩):

- 레이블 없는 `break` 는 **가장 안쪽 루프만** 끊는다. 바깥 `for` 는 계속 돈다.
- 그래서 `hit` 이 **마지막으로 찾은 것**으로 덮어써진다 — 답이 `(0,2)` 가 아니라 `(2,1)` 이 된다.
- 방문 횟수도 8 대 3 이다. 8 은 격자 9칸 중 마지막 행의 셋째 칸 직전까지 전부 본 것이다.
- ★ 이 버그는 **터지지 않는다.** 결과가 그럴듯해서 테스트 데이터에 답이 하나뿐이면 통과한다.

**대안은 셋이다** — 레이블이 항상 최선은 아니다.

| 방법 | 형태 | 언제 낫나 |
|---|---|---|
| 레이블 `break` | `break search;` | 두 겹이고, 찾은 뒤 **같은 메서드에서 이어서** 할 일이 있을 때 |
| 메서드로 빼고 `return` | `return new int[]{r, c};` | 찾는 일 자체가 **독립된 관심사**일 때. 대개 이쪽이 읽기 낫다 |
| 플래그 변수 | `boolean found` + 두 조건 | **쓰지 마라.** 조건이 두 군데로 흩어져 가장 읽기 나쁘다 |

**비용** — 레이블은 런타임 비용이 0이다(점프 목적지만 달라진다).\
비용은 **읽는 사람 쪽**이다 — 레이블이 셋 이상 겹치면 메서드로 빼는 편이 거의 항상 낫다.

### (6) 레이블 `continue` — 바깥 루프의 **다음 회차**로

**언제 쓰나** — 안쪽에서 조건을 발견했을 때 **그 행 전체를 버리고** 다음 행으로 갈 때.

`Ex.java (20-b)` 의 뒷부분.

```java
static String labeledContinue() {
    StringBuilder sb = new StringBuilder();
    rows:
    for (int r = 0; r < GRID.length; r++) {
        for (int c = 0; c < GRID[r].length; c++) {
            if (GRID[r][c] == 8) continue rows;   // 8 을 만나면 이 행은 통째로 버린다
            sb.append(GRID[r][c]).append(' ');
        }
        sb.append("| ");
    }
    return sb.toString();
}
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
plainContinue()  = 5 2 | 1 7 | 3 4 | 
labeledContinue()= 5 2 1 7 3 
```

```text
  plainContinue — 그 칸 하나만 건너뛴다        labeledContinue — 그 행을 버린다
  +-----------------------------+            +-----------------------------+
  | 5 2 [8건너뜀]  -> "5 2 | "  |            | 5 2 [8] -> 행 포기, "| " 없음|
  | 1 7 [8건너뜀]  -> "1 7 | "  |            | 1 7 [8] -> 행 포기          |
  | 3 [8건너뜀] 4  -> "3 4 | "  |            | 3 [8]   -> 행 포기          |
  +-----------------------------+            +-----------------------------+
    행 끝의 "| " 가 항상 찍힌다                "| " 가 한 번도 안 찍힌다
```

- `continue rows` 는 바깥 루프의 **증감식(`r++`)으로 건너뛴다.** 그 뒤의 `sb.append("| ")` 는 실행되지 않는다.
- ★ **`continue` 는 루프 레이블에만 붙는다.** 블록 레이블에 붙이면 컴파일 에러다(「어디서 틀리나」 5번).
- 반면 `break` 는 **아무 레이블 붙은 문**에나 붙는다 — 루프가 아닌 블록에도 된다.

**비용** — `break` 와 같다. 런타임 비용 0, 읽는 비용만 있다.

### (7) `for` 의 세 칸은 전부 비어도 된다

**언제 쓰나** — `while (true)` 대신 `for (;;)` 를 보거나, 두 변수를 양쪽에서 좁힐 때.

`Ex.java (20-b)` 의 마지막 부분.

```java
int n = 0;
for (;;) { n++; if (n == 3) break; }

StringBuilder two = new StringBuilder();
for (int i = 0, j = 10; i < j; i++, j--) two.append(i).append('/').append(j).append(' ');
```

**실행 결과** (JDK 21.0.5 — 17 · 25 에서도 같았다)

```text
for(;;) 로 센 값 = 3
두 변수 for      = 0/10 1/9 2/8 3/7 4/6 
```

```text
  for ( 초기화 ; 조건 ; 증감 ) 본문
        |        |      |
        |        |      +-- 비면: 아무것도 안 한다
        |        +--------- 비면: 항상 참 (무한 루프)
        +------------------ 비면: 아무것도 선언 안 한다
```

- **조건 칸이 비면 `true` 다.** `for (;;)` 가 무한 루프인 이유가 이것이다.
- 초기화·증감 칸에는 **쉼표로 여럿**을 둘 수 있다. 조건 칸에는 못 둔다(식 하나여야 한다).
- 초기화 칸에서 선언한 변수는 **`for` 안에서만** 보인다. 밖에서 쓰려면 밖에서 선언해야 한다.
- ★ 레이블은 **루프가 아닌 블록**에도 붙는다. 그때는 `break` 만 쓸 수 있다.

```java
int x = 7;
block: {
    if (x > 5) { System.out.println("block: 5 보다 커서 빠져나간다"); break block; }
    System.out.println("block: 여기는 안 온다");
}
System.out.println("block 뒤로 이어진다");
```

```text
block: 5 보다 커서 빠져나간다
block 뒤로 이어진다
```

**비용** — 없다. 다만 `for (;;)` 와 `while (true)` 는 같은 바이트코드가 되므로 **팀 관례를 따르면 된다.**

## 문법 — 형태와 규칙

### 형태 다섯

```java
// 1. 기본 for — 세 칸
for (int i = 0; i < n; i++) { ... }

// 2. 향상된 for — 배열 또는 Iterable
for (String s : list) { ... }

// 3. while
while (cond) { ... }

// 4. do-while — 본문이 최소 한 번은 돈다
do { ... } while (cond);

// 5. 레이블
outer:
for (...) {
    for (...) {
        break outer;      // outer 로 표시된 문 전체를 끝낸다
        continue outer;   // outer 루프의 다음 회차로
    }
}
```

### 규칙 불릿

- 향상된 `for` 의 대상은 **배열**이거나 **`java.lang.Iterable` 을 구현한 것**뿐이다.\
  `Map` 은 `Iterable` 이 아니므로 `entrySet()`·`keySet()`·`values()` 를 거쳐야 한다.
- 향상된 `for` 의 **루프 변수는 복사본**이다. 거기에 대입해도 원본 배열·컬렉션은 안 바뀐다.\
  단 변수가 가리키는 **객체 자체**는 바꿀 수 있다(참조 복사이므로).
- 향상된 `for` 는 **인덱스를 주지 않는다.** 인덱스가 필요하면 기본 `for` 를 쓴다.
- `break 레이블` 은 **레이블이 붙은 아무 문**에나 쓸 수 있다(루프·블록·`switch`).
- `continue 레이블` 은 **레이블이 붙은 루프**에만 쓸 수 있다.
- 레이블 이름은 **같은 스코프 안에서 겹칠 수 없다.**
- `break`/`continue` 를 레이블 없이 쓰면 **가장 안쪽** 루프(또는 `switch`)에 걸린다.
- `for` 의 세 칸은 각각 비어도 된다. 초기화·증감 칸만 **쉼표로 여럿**을 허용한다.

### 향상된 `for` 가 무엇과 같은가

| 대상 | 같은 뜻의 기본 루프 |
|---|---|
| 배열 `a` | `for (int i = 0, n = a.length; i < n; i++) { T x = a[i]; ... }` |
| `Iterable c` | `for (Iterator<T> it = c.iterator(); it.hasNext(); ) { T x = it.next(); ... }` |

- 배열 쪽에서 **길이를 루프 밖에서 한 번만 잰다**는 점이 핵심이다(`javap` 의 `arraylength` 위치).
- `Iterable` 쪽에서 **`hasNext()` 와 `next()` 가 매 회차 불린다**는 점이 핵심이다.

## 어디서 틀리나

★ 이 주제의 값은 대부분 여기 있다. **아래 에러 메시지는 전부 JDK 21.0.5 의 실출력이다.**

### 1. 향상된 `for` 로 순회하면서 컬렉션을 고쳤다

`Ex.java (20-c)` 의 (1)·(3).

```java
List<String> l1 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l1) if (s.equals("b")) l1.remove(s);       // 가운데를 지움
List<String> l3 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l3) if (s.equals("a")) l3.add("z");        // 추가도 마찬가지
```

```text
--- (1) 순회 중 remove — 가운데 원소
던짐: java.util.ConcurrentModificationException
--- (3) 순회 중 add
던짐: java.util.ConcurrentModificationException
```

- **추가도 구조적 수정**이다. `remove` 만 조심하면 되는 게 아니다.
- 고치는 법은 「동작 방식」 (4) — `Iterator.remove()` 또는 `removeIf`.

### 2. ★ 끝에서 두 번째를 지웠더니 **예외가 안 났다**

```text
--- (2) 순회 중 remove — 끝에서 두 번째 원소
예외 없음: [a, b, d]
```

- **이것이 이 주제 최대의 함정**이다. CME 가 안 났으니 통과한 것처럼 보인다.
- 실제로는 마지막 원소 `"d"` 가 루프 본문에 **한 번도 안 들어갔다.**
- 원인은 `hasNext()` 가 `cursor != size` 만 보고 `modCount` 를 안 보기 때문이다(「동작 방식」 (2)).
- ★ **"CME 가 안 나면 안전하다"는 판단을 버려야 한다.** javadoc 자신이 `best-effort` 라고 적었다.

### 3. 배열은 순회 중에 고쳐도 안 터진다 — 그래서 습관이 옮는다

`Ex.java (20-c)` 의 (4).

```java
int[] arr = { 5, 2, 8, 1 };
StringBuilder sb = new StringBuilder();
for (int x : arr) { arr[3] = 99; sb.append(x).append(' '); }
```

```text
--- (4) 배열을 순회하면서 그 배열을 고친다
예외 없음: 읽은 값 = 5 2 8 99 / 배열 = [5, 2, 8, 99]
```

- 배열에는 `modCount` 도 이터레이터도 없다. **검사할 것이 없어서 안 터진다.**
- 그리고 `99` 가 **읽힌다** — 값을 매 회차 `iaload` 로 다시 읽기 때문이다.
- ★ 배열에서 통하던 습관을 컬렉션으로 옮기면 (1)·(2) 가 된다. 두 벨트가 다른 물건임을 기억한다.

### 4. `null` 을 순회했다 — 메시지가 배열과 컬렉션에서 다르다

`Ex.java (20-d)` 의 (2).

```java
int[] none = null;
for (int x : none) System.out.println(x);

List<String> none2 = null;
for (String s : none2) System.out.println(s);
```

```text
--- (2) null 을 순회하면
던짐: Cannot read the array length because "<local4>" is null
던짐: Cannot invoke "java.util.List.iterator()" because "<local3>" is null
```

- ★ **이 두 줄이 「동작 방식」 (1) 의 증거다.** 배열 쪽은 `arraylength` 에서, 컬렉션 쪽은 `iterator()` 에서 터진다.
- 도식이 아니라 **런타임 메시지가 컴파일 결과를 그대로 불러 준다.**
- 헬프풀 NPE 메시지(`<local4>`)는 JDK 15 부터 기본 켜짐이다. 17 · 21 · 25 에서 같은 문구가 나왔다 — **관찰이지 보장은 아니다.**

### 5. `continue` 를 블록 레이블에 썼다

`Ex.java (20-e1)`

```java
block: {
    for (int i = 0; i < 3; i++) {
        continue block;      // block 은 루프가 아니다
    }
}
```

```text
Ex.java:5: error: not a loop label: block
                continue block;      // block 은 루프가 아니다
                ^
1 error
```

- 메시지가 규칙을 그대로 말해 준다 — **`continue` 의 레이블은 루프여야 한다.**
- `break block;` 이면 통과한다. `break` 쪽이 더 넓다.

### 6. 루프 밖에서 `break` 를 썼다

`Ex.java (20-e2)`

```java
int x = 1;
if (x > 0) break;
```

```text
Ex.java:4: error: break outside switch or loop
        if (x > 0) break;
                   ^
1 error
```

- 메시지가 `break` 가 걸릴 수 있는 대상을 나열한다 — **`switch` 아니면 루프.**
- `if` 는 `break` 의 대상이 아니다. 블록에 레이블을 붙였다면 그 레이블로 `break` 할 수 있다.

### 7. 레이블 이름을 오타냈다

`Ex.java (20-e3)`

```java
outer:
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < 3; j++) break outr;   // 오타
}
```

```text
Ex.java:5: error: undefined label: outr
            for (int j = 0; j < 3; j++) break outr;   // 오타
                                        ^
1 error
```

- 레이블은 **변수가 아니다.** 이름 공간이 따로라서 같은 이름의 변수가 있어도 충돌하지 않는다.
- 반대로 오타를 내면 "변수를 못 찾음"이 아니라 **`undefined label`** 이 나온다.

### 8. 같은 레이블 이름을 겹쳐 썼다

`Ex.java (20-e5)`

```java
loop:
for (int i = 0; i < 2; i++) {
    loop:
    for (int j = 0; j < 2; j++) break loop;
}
```

```text
Ex.java:5: error: label loop already in use
            loop:
            ^
1 error
```

- 안쪽에서 바깥 레이블을 가리면 `break loop` 가 어느 쪽인지 알 수 없다. 그래서 아예 막는다.
- 변수 섀도잉과 다른 점이다 — 변수는 안쪽 블록에서 같은 이름을 못 쓰지만, 레이블은 **아예 사용 중이면 끝**이다.

### 9. 향상된 `for` 를 `Map` 에 직접 썼다

`Ex.java (20-e6)`

```java
Map<String, Integer> m = Map.of("a", 1);
for (var e : m) System.out.println(e);
```

```text
Ex.java:5: error: for-each not applicable to expression type
        for (var e : m) System.out.println(e);
                     ^
  required: array or java.lang.Iterable
  found:    Map<String,Integer>
1 error
```

- ★ 메시지의 `required: array or java.lang.Iterable` 이 **향상된 `for` 의 조건 전부**다.
- `Map` 은 `Iterable` 이 아니다. `m.entrySet()` · `m.keySet()` · `m.values()` 가 `Iterable` 이다.
- `Map` API 자체는 [**41번 주제**](../41-map-api-merge-compute/)가 정본이다.

### 10. 직접 만든 타입을 순회하려 했다

`Ex.java (20-e4)`

```java
static class Bag { int[] items = {1, 2, 3}; }
Bag b = new Bag();
for (int x : b) System.out.println(x);
```

```text
Ex.java:5: error: for-each not applicable to expression type
        for (int x : b) System.out.println(x);
                     ^
  required: array or java.lang.Iterable
  found:    Bag
1 error
```

- 필드로 배열을 **가지고 있는 것**과 `Iterable` **인 것**은 다르다.
- `implements Iterable<Integer>` 를 붙이고 `iterator()` 를 구현해야 한다.
- 9번과 **같은 에러**다 — 조건이 하나뿐이라 실패 모양도 하나다.

### 11. 루프 변수에 대입해 놓고 원본이 바뀌길 기대했다

`Ex.java (20-d)` 의 (1).

```java
int[] arr = { 5, 2, 8, 1 };
for (int x : arr) x = 0;

List<StringBuilder> list = new ArrayList<>(List.of(new StringBuilder("a"), new StringBuilder("b")));
for (StringBuilder sb : list) sb.append("!");              // 객체를 바꾼다 — 된다
for (StringBuilder sb : list) sb = new StringBuilder("z"); // 칸을 바꾼다 — 안 된다
```

```text
--- (1) 루프 변수에 대입해도 원본은 안 바뀐다
배열 = [5, 2, 8, 1]
리스트 = [a!, b!]
```

- 루프 변수는 **매 회차 새로 만드는 지역 변수**다. 거기 대입해도 원본 칸과 무관하다.
- 반면 `sb.append("!")` 는 **가리키는 객체**를 바꾸므로 반영된다.
- 이 비대칭은 [**03번 주제**](../03-variables-and-assignment/)(전부 값 전달)의 규칙 그대로다.

### 12. 인덱스가 필요한데 향상된 `for` 를 고집했다

```java
String[] names = { "kim", "lee", "park" };
for (int i = 0; i < names.length; i++) System.out.print(i + ":" + names[i] + " ");
```

```text
0:kim 1:lee 2:park 
```

- 향상된 `for` 는 인덱스를 주지 않는다. **바깥에 카운터를 두는 것**이 가장 흔한 우회다.
- 카운터를 둘 거면 **처음부터 기본 `for`** 가 짧고 정확하다. 우회가 원래 형태보다 길어지면 도구 선택이 틀린 것이다.

## 구현 세부사항 대 언어 보장

이 주제는 "언어가 약속한 것"과 "`ArrayList` 가 그렇게 구현한 것"이 섞이기 쉬워 경계가 중요하다.

| 무엇 | 어디에 속하나 | 근거 |
|---|---|---|
| 향상된 `for` 의 대상이 배열 또는 `Iterable` | **언어 보장** | javac 에러 `required: array or java.lang.Iterable` |
| 루프 변수가 복사본이라는 것 | **언어 보장** | 대입해도 원본이 안 바뀐다(20-d 실행) |
| `continue` 의 레이블이 루프여야 한다는 것 | **언어 보장** | javac 에러 `not a loop label` |
| 레이블 중복 금지 | **언어 보장** | javac 에러 `label loop already in use` |
| `modCount` 라는 필드가 있고 fail-fast 를 제공한다 | **API 문서화된 사실** | `AbstractList` javadoc — 단 **"선택적"** 이라고 명시 |
| CME 가 **항상** 난다 | **보장 아님** | CME javadoc — `best-effort basis` |
| 끝에서 두 번째를 지우면 조용히 끝난다는 것 | **구현 세부** | `ArrayList$Itr.hasNext()` 가 `cursor != size` 인 결과 |
| 배열 `for` 가 `arraylength` 를 한 번만 부른다 | **구현 세부** | javac 21 의 코드 생성. 다른 컴파일러는 다를 수 있다 |
| `Iterable for` 가 `iterator()`/`hasNext()`/`next()` 를 부른다 | **언어 보장에 가깝다** | `Iterable` 계약상 그 셋 말고 순회 수단이 없다 |
| 스택 트레이스의 `ArrayList.java:1095` 같은 줄 번호 | **구현 세부** | 17 · 21 · 25 에서 전부 달랐다 |
| 헬프풀 NPE 의 `<local4>` 같은 이름 | **구현 세부** | JVM 이 만드는 문구. 변수명이 없으면 이런 형태가 된다 |
| 에러 메시지의 **문구 자체** | **구현 세부** | javac 의 것이다 |

### `modCount` 는 **의무가 아니다**

`AbstractList` javadoc 이 직접 말한다 (JDK 21.0.5 `src.zip`).

```text
     * <p><b>Use of this field by subclasses is optional.</b> If a subclass
     * wishes to provide fail-fast iterators (and list iterators), then it
     * merely has to increment this field in its {@code add(int, E)} and
     * {@code remove(int)} methods ...  If an implementation
     * does not wish to provide fail-fast iterators, this field may be
     * ignored.
```

```text
  fail-fast 를 제공하는 것                  제공하지 않는 것
  +-----------------------------+          +-----------------------------+
  | ArrayList · HashMap ·       |          | CopyOnWriteArrayList        |
  | LinkedList · TreeMap ...    |          | ConcurrentHashMap           |
  | (java.util 의 범용 구현체)   |          | (java.util.concurrent)      |
  +-----------------------------+          +-----------------------------+
    순회 중 수정 -> CME (대개)               순회 중 수정 -> 예외 없음
                                             스냅샷 또는 약한 일관성으로 돈다
```

- 그래서 **"컬렉션을 순회 중에 고치면 CME 가 난다"는 말은 틀렸다.** 나는 구현이 있을 뿐이다.
- 동시 컬렉션의 순회 계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다. 여기서는 "CME 가 안 나는 구현이 있다"까지만.

## 언제 쓰고 언제 안 쓰나

**향상된 `for` 를 쓴다**

- 전부를 한 번씩 보고 **인덱스가 필요 없을 때.** 기본 `for` 보다 짧고 off-by-one 이 원천적으로 없다.
- 컬렉션 타입이 바뀔 수 있을 때 — `List` 를 `Set` 으로 바꿔도 순회 코드가 그대로다.

**향상된 `for` 를 안 쓴다**

- **인덱스가 필요할 때** — 위치를 출력하거나 두 배열을 나란히 볼 때.
- **순회하면서 지울 때** — `Iterator.remove()` 나 `removeIf` 로 간다.
- **역순으로 돌 때** — 향상된 `for` 는 정방향뿐이다. `List` 면 `listIterator(size)` 나 기본 `for`.
- **중간에 두 원소를 동시에 볼 때**(현재와 다음) — 인덱스가 있어야 한다.

**레이블을 쓴다**

- 중첩 루프에서 **찾은 즉시 전부 끝내야** 하고, 그 뒤에 **같은 메서드에서 이어서 할 일**이 있을 때.
- 안쪽 조건으로 **바깥 회차를 통째로 버려야** 할 때(`continue 레이블`).

**레이블을 안 쓴다**

- 찾는 일이 독립적이면 **메서드로 빼고 `return`** 한다. 대개 이쪽이 읽기 낫다.
- 레이블이 **둘 이상 겹칠 때** — 그 시점에 메서드 분해가 밀린 것이다.
- 스트림으로 표현되는 검색(`findFirst`)이면 그쪽이 의도를 더 드러낸다 — 목록의 [**46번 주제**](../46-terminal-operations/).

**중간 지대**

- `for (;;)` 와 `while (true)` 는 같은 바이트코드가 된다. **팀 관례를 따르면 된다.**
- 플래그 변수(`boolean found`)는 **거의 항상 레이블보다 나쁘다** — 조건이 두 군데로 흩어진다.

## 핵심 문장

1. 향상된 `for` 는 **한 문법 두 구현**이다 — 배열은 인덱스 루프, `Iterable` 은 이터레이터 루프로 펼쳐진다.
2. 그 차이는 `javap` 뿐 아니라 **`null` 을 넣었을 때의 NPE 메시지**로도 드러난다.
3. 순회 중 구조적 수정이 터지는 것은 `next()` 안의 **`modCount` 대조** 때문이다.
4. ★ **`hasNext()` 는 대조하지 않는다** — 그래서 끝에서 두 번째를 지우면 **조용히 한 원소를 건너뛴다.**
5. CME 는 javadoc 이 스스로 `best-effort` 라 적었다. **없다고 안전한 것이 아니다.**
6. 배열에는 `modCount` 가 없다 — 순회 중 고쳐도 안 터지고, 바뀐 값이 그대로 읽힌다.
7. 레이블 없는 `break` 는 **가장 안쪽만** 끊는다. 중첩 루프의 "첫 번째를 찾았다"가 여기서 거짓이 된다.
8. `break` 는 아무 레이블 문에, `continue` 는 **루프 레이블에만** 붙는다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 20번)
- [**21번 주제**](../21-switch-statement-and-expression/)(`switch` 문과 `switch` 식) — **이 주제의 다음 칸.**\
  여기는 반복과 점프까지, **거기는 분기**부터. `break` 가 `switch` 에서 무엇을 하는지는 거기가 정본이다
- [**22번 주제**](../22-instanceof-type-patterns/)(`instanceof` 타입 패턴) — `if` 조건에서 타입을 검사하며 변수를 꺼내는 것.\
  **여기는 `if` 조건의 참·거짓까지, 거기는 그 조건이 변수를 만드는 것부터**
- [**23번 주제**](../23-switch-pattern-matching/) · [**24번 주제**](../24-record-patterns/) — 분기가 패턴으로 넓어진 뒤의 규칙.\
  **제어 흐름의 뼈대는 여기, 분기 안에서 값을 꺼내는 규칙은 거기**
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — 루프 변수가 복사본인 이유(전부 값 전달).\
  **"왜 대입해도 원본이 안 바뀌나"의 정본은 거기**, 여기는 그것이 루프에서 나타나는 모양만
- [`../05-arrays/`](../05-arrays/) — 배열의 언어 규칙(생성·기본값·공변성).\
  **배열 자체는 거기**, 여기는 **배열을 순회하는 문법**만
- [`../26-try-with-resources/`](../26-try-with-resources/) — 블록을 벗어날 때 무엇이 실행되나.\
  **`finally`·자원 닫기 순서는 거기**, 여기는 `break`/`continue` 의 목적지만
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — 동적 배열의 **자료구조**(증폭·상환 분석).\
  **왜 `ArrayList` 가 배열을 들고 있나는 거기**, 여기는 **그것을 순회할 때의 규칙**만
- [`../../../../../data-structure/`](../../../../../data-structure/) — 컬렉션 내부 구조 전반. **여기서는 내부를 설명하지 않는다**
- [**43번 주제**](../43-iterator-and-fail-fast/)(`Iterator`·`ListIterator`·fail-fast) — **`Iterator` API 와 fail-fast 의 정본.**\
  여기서는 **향상된 `for` 를 설명하는 데 필요한 만큼만** 다뤘다(`hasNext`/`next`/`remove` 셋)
- [**41번 주제**](../41-map-api-merge-compute/)(`Map` API) — `entrySet()`·`keySet()` 이 왜 필요한지의 정본
- [**55번 주제**](../55-atomics-and-concurrent-collections/)(원자 변수와 동시 컬렉션) — CME 를 던지지 않는 컬렉션들.\
  **여기는 "안 던지는 구현이 있다"까지**, 그 계약은 거기
- [`../46-terminal-operations/`](../46-terminal-operations/) — `findFirst` 같은 단락 평가.\
  **레이블 `break` 의 대안으로 언급만** 한다. 스트림 규칙은 거기
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — JIT·GC·메모리 모델. **이 주제와 겹치지 않는다**

## 용어 풀이

- **향상된 `for`(enhanced for / for-each)** — `for (T x : c)` 형태. Java 5. 배열과 `Iterable` 에만 쓸 수 있다.
- **`Iterable`** — `iterator()` 하나를 요구하는 인터페이스. 향상된 `for` 의 유일한 비배열 대상.
- **`Iterator`** — `hasNext()` · `next()` · (선택) `remove()` 로 순회를 진행시키는 객체.
- **`modCount`** — 컬렉션이 **구조적으로 몇 번 바뀌었나**를 세는 필드. `AbstractList` 에 `protected` 로 있다.
- **구조적 수정(structural modification)** — 크기를 바꾸는 변경. `set` 은 해당 없음, `add`·`remove` 는 해당.
- **fail-fast** — 잘못된 상태를 발견 즉시 예외로 멈추는 설계. **보장이 아니라 best-effort 다.**
- **`ConcurrentModificationException`** — fail-fast 이터레이터가 `modCount` 불일치를 발견했을 때 던지는 예외. Java 1.2.
- **`checkForComodification()`** — `ArrayList$Itr` 이 `next()`·`remove()` 앞에서 부르는 대조 메서드.
- **레이블(label)** — 문 앞에 붙이는 `이름:` 표시. `break`/`continue` 의 목적지가 된다.
- **`arraylength`** — 배열 길이를 스택에 올리는 JVM 명령. 배열 향상된 `for` 의 표식이다.
- **`checkcast`** — 참조 타입 검사·변환 JVM 명령. `Iterator.next()` 가 `Object` 를 주므로 뒤따른다.
- **헬프풀 NPE(helpful NullPointerException)** — "무엇이 `null` 이었나"를 적어 주는 NPE 메시지. JDK 15 부터 기본 켜짐.
- **무음 실패(silent failure)** — 예외 없이 결과만 틀리는 실패. 이 주제의 2번 함정이 그것이다.

## 더 들어가면

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

  한 바이트도 다르지 않다. 조건 검사가 아예 사라지고 무조건 점프만 남는다. 선택은 순전히 관례 문제다.
- **`do-while` 은 실무에서 드물다.**\
  "최소 한 번"이 필요한 경우가 드물고, 필요해도 첫 회차를 루프 밖에 적는 편이 읽기 쉽다.\
  대표적으로 남는 자리는 **재시도 루프**다 — 한 번은 반드시 시도해야 하기 때문이다.
- **레이블은 Java 에 `goto` 가 없어서 생긴 절충이다.**\
  `goto` 는 **쓸 수 없는데 이름으로도 못 쓴다** — 변수 이름에 넣어 보면 파싱에서 막힌다(`Ex.java (20-e7)`).

  ```text
  Ex.java:4: error: not a statement
          int goto = 2;
          ^
  Ex.java:4: error: ';' expected
          int goto = 2;
             ^
  2 errors
  ```

  `int goto1 = 1;` 은 통과하고 `int goto = 2;` 만 막힌다. 자리를 비워 둔 예약어라는 뜻이다.\
  레이블 `break`/`continue` 는 "뒤로 못 가고 밖으로만 나가는 `goto`" 라고 읽으면 정확하다.
- **컬렉션을 순회하며 고치는 세 번째 방법**이 있다 — **새 리스트를 만든다.**\
  `list.stream().filter(...).toList()` 는 원본을 안 건드리므로 CME 가 원천적으로 없다.\
  원본을 꼭 바꿔야 하는 게 아니라면 이쪽이 가장 안전하다. 스트림 규칙은 [**46번 주제**](../46-terminal-operations/).
- **`CopyOnWriteArrayList` 는 순회 중 수정이 예외가 아니다** — 이터레이터가 **스냅샷**을 들고 돌기 때문이다.\
  대신 순회 중에 추가한 원소는 **그 순회에서 보이지 않는다.** 예외 대신 **낡은 뷰**를 받는 거래다.\
  계약은 [**55번 주제**](../55-atomics-and-concurrent-collections/)가 정본이다 — 여기서는 "fail-fast 가 의무가 아니다"의 예로만 든다.
