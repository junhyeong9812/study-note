# java/syntax/05 — 배열: 생성·기본값·공변성·`Arrays` 유틸 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·에러를 맞힐 수 있는지**를 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 배열은 무엇의 인스턴스인가 (예측)

```java
int[] a = new int[3];
System.out.println(a.getClass().getName());
System.out.println(a.getClass().getSuperclass());
System.out.println(java.util.Arrays.toString(a.getClass().getInterfaces()));
System.out.println(a.toString());
```

- 네 줄의 출력은 각각 무엇인가?
- `a.length` 는 필드인가 메서드인가?
- 배열이 `Object` 에서 물려받은 `equals`/`hashCode`/`toString` 은 재정의돼 있는가?

### 2. 이 배열들의 내용은 무엇인가 (예측)

```java
int[] i = new int[2];
boolean[] b = new boolean[2];
String[] s = new String[2];
int[][] jag = new int[3][];
```

- 넷을 각각 `Arrays.toString`(또는 `deepToString`)으로 찍으면 무엇이 나오는가?
- `new int[2][3]` 과 `new int[2][]` 는 무엇이 다른가?
- `jag[0][0] = 1;` 을 하면 무슨 일이 생기는가?

### 3. 이 코드는 어디서 터지는가 (예측)

```java
String[] strings = new String[3];
Object[] objects = strings;          // (A)
objects[0] = "문자열";                // (B)
objects[1] = Integer.valueOf(42);    // (C)
```

- (A)(B)(C) 중 어디가 컴파일 에러이고 어디가 런타임 예외인가?
- 터지는 곳의 예외 이름과 **메시지 전문**은 무엇인가?
- 같은 일을 `List<String>` / `List<Object>` 로 하면 어디서 막히는가?

### 4. 공변성의 검사는 누가 언제 하는가 (왜)

- `Object[] o = new String[3];` 이 통과하는 근거는 JLS 의 어느 규칙인가?
- 저장 시 검사를 하는 JVM 명령은 무엇이고, `int[]` 에는 왜 그 검사가 없는가?
- 배열을 공변으로 만든 이유는 무엇이었나?
- 제네릭은 왜 같은 선택을 하지 않았나?

### 5. `Arrays.equals` 와 `deepEquals` 가 갈리는 지점 (예측)

```java
int[][] p = {{1, 2}, {3, 4}};
int[][] q = {{1, 2}, {3, 4}};
int[]   f1 = {1, 2, 3}, f2 = {1, 2, 3};
```

- `p.equals(q)` / `Arrays.equals(p,q)` / `Arrays.deepEquals(p,q)` 의 결과는 각각 무엇인가?
- `Arrays.equals(f1, f2)` 는 무엇인가? 앞의 결과와 왜 다른가?
- `Arrays.toString(p)` 와 `Arrays.deepToString(p)` 는 각각 무엇을 찍는가?
- 배열을 `HashMap` 의 키로 써도 되는가?

### 6. `Arrays.asList` 가 놓는 함정 셋 (예측)

```java
int[] prim = {1, 2, 3};
List<?> a = Arrays.asList(prim);
List<String> fixed = Arrays.asList("a", "b", "c");
String[] backing = {"x", "y"};
List<String> view = Arrays.asList(backing);
```

- `a.size()` 는 무엇인가? 그 이유는?
- `fixed.set(0,"A")` 와 `fixed.add("d")` 중 어느 쪽이 되고 어느 쪽이 터지는가, 예외의 `getMessage()` 는?
- `backing[0] = "CHANGED"` 뒤 `view` 는 무엇인가?
- 셋을 한꺼번에 피하려면 무엇을 쓰는가, 그 대가는?

### 7. 복사 수단 넷의 차이 (경계)

- `System.arraycopy` · `Arrays.copyOf` · `Arrays.copyOfRange` · `clone()` 은 각각 무엇이 다른가?
- `Arrays.copyOf(src, src.length + 3)` 의 뒤 세 칸에는 무엇이 들어가는가?
- `int[][] shallow = deep.clone(); shallow[0][0] = 99;` 뒤 `deep[0][0]` 은 무엇인가?
- 다차원 배열을 방어적으로 복사하려면 무엇을 해야 하는가?

### 8. 배열이 던지는 예외들의 메시지 (예측)

```java
int[] a = new int[3];
a[3];                                  // (A)
a[-1];                                 // (B)
int n = -1; int[] bad = new int[n];    // (C)
int[] nil = null; int v = nil[0];      // (D)
System.arraycopy(a, 0, new int[2], 0, 3);   // (E)
```

- 다섯 자리에서 각각 어떤 예외가 나는가?
- (A)와 (B)의 예외 이름은 같은가? 그 예외의 부모는 무엇인가?
- (C)는 컴파일 에러인가 런타임 예외인가?
- (D)의 메시지는 **무엇에 따라 달라지는가**?

### 9. 배열 길이 0 과 `null` (경계)

- `new int[0]` 은 합법인가, 그것으로 무엇을 할 수 있는가?
- API 가 "결과 없음"을 돌려줄 때 `null` 과 길이 0 배열 중 무엇이 나은가, 왜인가?
- `list.toArray()` 와 `list.toArray(new String[0])` 의 런타임 타입은 각각 무엇인가?

### 10. 배열 대신 `List` 를 써야 하는 자리 (연결)

- 공개 API 의 반환 타입으로 배열을 쓰면 무엇이 새는가?
- `public static final int[] PRIMES` 가 상수가 못 되는 이유는 무엇인가?
- 기본형 대량 데이터에서 배열이 여전히 유리한 이유는 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- `Arrays.asList(int[])` 함정의 뿌리를 기본형/래퍼 규칙으로 설명할 수 있는가?
- 배열을 메서드에 넘겼을 때 원소 변경은 보이고 재대입은 안 보이는 이유는 무엇인가?
- `new List<String>[3]` 이 왜 금지되는가, 그것은 어느 주제의 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
