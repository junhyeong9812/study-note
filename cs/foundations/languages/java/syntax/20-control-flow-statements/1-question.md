# java/syntax/20 — 제어문: 향상된 `for` · 레이블 `break`/`continue` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「예측형」과 「어기면 무엇이 출력되나」형**이 반반이다.
> 제어문은 문법이 단순해서, 지식의 대부분이 **"안 터지는데 틀리는 자리"**에 있다.
> 모든 코드는 Temurin **JDK 21.0.5** 기준이다(17·25 에서 갈리는 것은 그 문항에 적었다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 한 줄이 두 가지로 펼쳐진다 (예측)

```java
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
```

- 두 메서드의 **바이트코드는 같은가 다른가**?
- `javap -c -p` 로 찍으면 배열 쪽에 나타나는 특징적인 명령 하나는 무엇인가?
- `Iterable` 쪽에서 원소 하나당 불리는 **메서드는 몇 개**이며 각각 무엇인가?
- 배열 쪽에서 **길이는 몇 번** 재는가 — 루프 안인가 밖인가?

### 2. `null` 을 순회하면 메시지가 갈린다 (예측)

```java
int[] none = null;
for (int x : none) System.out.println(x);

List<String> none2 = null;
for (String s : none2) System.out.println(s);
```

- 두 줄은 각각 무엇을 던지는가?
- **메시지가 서로 다른가** — 다르다면 각각 어떤 문구인가?
- 그 차이는 1번의 답과 어떻게 이어지는가?
- 이 메시지는 어느 JDK 버전부터 이런 형태인가?

### 3. 순회 중에 컬렉션을 고치면 (예측)

```java
List<String> l = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l) if (s.equals("b")) l.remove(s);     // (a)

List<String> l3 = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l3) if (s.equals("a")) l3.add("z");    // (b)
```

- (a)와 (b)는 각각 무엇이 일어나는가?
- 예외라면 **정확한 클래스 이름**과 스택 트레이스 **맨 윗줄의 메서드 이름**은 무엇인가?
- 그 예외를 던지는 조건을 코드 한 줄로 쓰면 무엇인가?
- `remove` 만 위험한가, 아니면 `add` 도 위험한가 — 그 기준을 무엇이라 부르는가?

### 4. ★ 끝에서 두 번째를 지웠다 (예측)

```java
List<String> l = new ArrayList<>(List.of("a", "b", "c", "d"));
for (String s : l) if (s.equals("c")) l.remove(s);
System.out.println(l);
```

- 이것은 예외를 던지는가?
- 마지막 출력은 무엇인가?
- **루프 본문에 들어온 원소는 몇 개**인가 — `"d"` 는 들어왔는가?
- 3번은 터지는데 이것은 안 터지는 **정확한 이유**는 무엇인가(`ArrayList$Itr` 의 어느 메서드 때문인가)?
- `ConcurrentModificationException` 의 javadoc 은 이 상황에 대해 무엇이라 적었는가?

### 5. 배열을 순회하면서 그 배열을 고치면 (예측)

```java
int[] arr = { 5, 2, 8, 1 };
StringBuilder sb = new StringBuilder();
for (int x : arr) { arr[3] = 99; sb.append(x).append(' '); }
System.out.println(sb + "/ " + Arrays.toString(arr));
```

- 예외가 나는가?
- 읽힌 값들은 `5 2 8 1` 인가 `5 2 8 99` 인가 — 왜인가?
- 루프 안에서 배열을 **더 길게** 만들 수는 있는가?
- 이 동작이 컬렉션에서의 습관과 어긋나는 지점은 어디인가?

### 6. 안전하게 지우는 두 가지 (왜)

```java
for (Iterator<String> it = l.iterator(); it.hasNext(); ) if (it.next().equals("b")) it.remove();
l2.removeIf(s -> s.equals("b"));
```

- `Iterator.remove()` 가 CME 를 안 내는 이유를 **그 구현의 한 줄**로 말하면 무엇인가?
- `Iterator.remove()` 는 4번의 **건너뜀 문제**도 함께 푸는가 — 그 이유는 무엇인가?
- 여러 원소를 지울 때 `Iterator.remove()` 와 `removeIf` 중 어느 쪽이 유리한가?
- `it.remove()` 를 `it.next()` 없이 먼저 부르면 무엇이 나오는가?

### 7. 레이블 없는 `break` 가 만드는 버그 (예측)

```java
static final int[][] GRID = { {5,2,8}, {1,7,8}, {3,8,4} };

static String plainBreak(int target) {          // break;
    String hit = "없음"; int visited = 0;
    for (int r = 0; r < GRID.length; r++)
        for (int c = 0; c < GRID[r].length; c++) {
            visited++;
            if (GRID[r][c] == target) { hit = "(" + r + "," + c + ")"; break; }
        }
    return hit + " visited=" + visited;
}
```

- `plainBreak(8)` 의 출력은 무엇인가?
- `break;` 를 `break search;`(바깥 `for` 에 `search:` 를 붙이고) 로 바꾸면 출력이 어떻게 바뀌는가?
- 두 출력의 **방문 횟수**는 각각 몇인가?
- 이 버그가 테스트를 통과해 버리는 조건은 무엇인가?

### 8. `continue` 와 `continue 레이블` (예측)

```java
// (a)
for (int r = 0; r < GRID.length; r++) {
    for (int c = 0; c < GRID[r].length; c++) {
        if (GRID[r][c] == 8) continue;
        sb.append(GRID[r][c]).append(' ');
    }
    sb.append("| ");
}

// (b) 바깥 for 에 rows: 를 붙이고 continue rows;
```

- (a)와 (b)의 출력은 각각 무엇인가(`GRID` 는 7번과 같다)?
- (b)에서 `sb.append("| ")` 는 몇 번 실행되는가?
- `continue 레이블` 은 바깥 루프의 **어느 지점**으로 가는가?
- `break 레이블` 과 `continue 레이블` 이 붙을 수 있는 대상의 **차이**는 무엇인가?

### 9. 레이블의 경계 넷 — 어기면 무엇이 출력되나 (경계)

```java
// (a)
block: { for (int i = 0; i < 3; i++) { continue block; } }

// (b)
int x = 1; if (x > 0) break;

// (c)
outer: for (int i = 0; i < 3; i++) { for (int j = 0; j < 3; j++) break outr; }

// (d)
loop: for (int i = 0; i < 2; i++) { loop: for (int j = 0; j < 2; j++) break loop; }
```

- (a)~(d)는 각각 **어떤 에러 메시지**를 내는가?
- (a)에서 `continue` 를 `break` 로 바꾸면 통과하는가?
- (c)의 에러가 "변수를 못 찾음"이 아닌 이유는 무엇인가?
- (d)가 금지된 이유를 한 문장으로 말하면 무엇인가?

### 10. 향상된 `for` 의 대상 조건 (경계)

```java
// (a)
Map<String, Integer> m = Map.of("a", 1);
for (var e : m) System.out.println(e);

// (b)
static class Bag { int[] items = {1, 2, 3}; }
for (int x : new Bag()) System.out.println(x);
```

- (a)와 (b)는 각각 컴파일되는가?
- 안 된다면 **에러 메시지의 `required:` 줄**에는 무엇이 적히는가?
- (a)를 고치는 방법 셋은 무엇인가?
- (b)의 `Bag` 을 순회 가능하게 만들려면 무엇을 해야 하는가?

### 11. 루프 변수에 대입하면 (예측)

```java
int[] arr = { 5, 2, 8, 1 };
for (int x : arr) x = 0;

List<StringBuilder> list = new ArrayList<>(List.of(new StringBuilder("a"), new StringBuilder("b")));
for (StringBuilder sb : list) sb.append("!");
for (StringBuilder sb : list) sb = new StringBuilder("z");
```

- 세 루프를 돈 뒤 `arr` 과 `list` 는 각각 무엇인가?
- `sb.append("!")` 는 반영되는데 `sb = new StringBuilder("z")` 는 반영되지 않는 이유는 무엇인가?
- 이 비대칭을 설명하는 정본 주제는 어디인가?
- `for (final String s : list)` 처럼 `final` 을 붙일 수 있는가?

### 12. 어디까지가 언어 보장인가 (경계)

- "컬렉션을 순회 중에 고치면 `ConcurrentModificationException` 이 난다" — 이 문장은 참인가?
- `modCount` 를 쓰는 것은 **의무인가 선택인가** — 근거는 어디에 있는가?
- 스택 트레이스의 `ArrayList.java:1095` 같은 **줄 번호**는 버전 간에 같았는가?
- CME 를 던지지 **않는** 컬렉션을 하나 들면 무엇이며, 그 대가는 무엇인가?

### 13. 정본 경계 (연결)

- 이 주제와 **43번**(`Iterator`·fail-fast)·**05번**(배열)·**03번**(값 전달)의 경계는 각각 어디인가?
- 레이블 `break` 대신 쓸 수 있는 수단 셋은 무엇이며, 각각 언제 나은가?
- `for (;;)` 와 `while (true)` 는 같은 바이트코드가 되는가?
- Java 에 `goto` 는 있는가 — 변수 이름으로는 쓸 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
