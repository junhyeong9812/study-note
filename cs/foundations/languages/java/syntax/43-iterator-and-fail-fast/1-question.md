# java/syntax/43 — `Iterator`·`ListIterator`·fail-fast 와 `ConcurrentModificationException` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **선행** — [`../39-collections-framework-map/`](../39-collections-framework-map/) 의 질문을 먼저 푼다.
> **향상된 `for` 라는 문법 자체**(배열과의 차이·레이블 `break`·바이트코드)는 여기서 묻지 않는다 —
> [`../20-control-flow-statements/`](../20-control-flow-statements/) 의 질문이다.
> 여기는 **`Iterator` 인터페이스의 계약·`ListIterator`·삭제 셋·fail-fast 의 구현과 한계**를 묻는다.

## 예시 데이터

여러 문항이 이 리스트를 쓴다. **위치가 이름에 박혀 있다.**

```java
List<String> base() { return new ArrayList<>(List.of("e0", "e1", "e2", "e3", "e4")); }
```

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `Iterator` 의 세 메서드 계약 (예측)

```java
Iterator<String> it = new ArrayList<>(List.of("a")).iterator();
it.next(); it.next();                           // (A)

Iterator<String> i2 = new ArrayList<>(List.of("a","b")).iterator();
i2.remove();                                    // (B)
i2.next(); i2.remove(); i2.remove();            // (C)

Iterator<String> i3 = List.of("a","b").iterator();
i3.next(); i3.remove();                         // (D)

Iterator<String> i4 = Arrays.asList("a","b").iterator();
i4.next(); i4.remove();                         // (E)
```

- (A)~(E)는 각각 무엇을 던지는가?
- 네 예외 이름이 각각 **어떤 실수**를 가리키는가?
- (D)와 (E)의 **메시지가 다르다** — 왜인가?
- `remove()` 를 `next()` 한 번당 몇 번 부를 수 있는가, 근거 문장은?

### 2. ★ 어느 원소를 지울 때 터지나 (예측)

```java
for (int k = 0; k < 5; k++) {
    List<String> l = new ArrayList<>(List.of("e0","e1","e2","e3","e4"));
    for (String s : l) if (s.equals("e" + k)) l.remove(s);
}
```

- `k` 가 0~4 일 때 각각 예외가 나는가?
- 예외가 안 나는 `k` 는 무엇이며, **그때 루프 본문에 들어온 원소는 몇 개**인가?
- 그 이유를 `ArrayList$Itr` 의 **어느 메서드 한 줄**로 설명하는가?
- 크기 2 리스트에서 첫 원소를 지우면 어떻게 되는가?
- 이 현상을 부르는 javadoc 의 표현은 무엇인가?

### 3. 같은 일을 세 가지 형태로 쓰면 (예측)

```java
for (String s : l)          if (s.equals("e3")) l.remove(s);   // (A) 향상된 for
l.forEach(s ->            { if (s.equals("e3")) l.remove(s); }); // (B)
l.stream().forEach(s ->   { if (s.equals("e3")) l.remove(s); }); // (C)
```

- 셋은 각각 무엇이 되는가?
- (C)의 예외 **클래스와 메시지 전문**은 무엇인가?
- (B)가 (A)와 다른 이유를 `ArrayList.forEach` 의 구현으로 설명하면?
- 셋 중 가장 나쁜 실패는 무엇이며 왜인가?

### 4. fail-fast 는 어떻게 구현돼 있나 (왜)

- `modCount` 는 어느 클래스의 무슨 필드인가?
- `expectedModCount` 는 어디에 있는가?
- **무엇을 셀 때만** `modCount` 가 오르는가 — `set(i, x)` 는 오르는가?
- `checkForComodification()` 은 어느 메서드들이 부르는가, **`hasNext()` 는 부르는가**?
- `AbstractList` 의 `modCount` javadoc 은 이 필드를 쓰는 것을 **의무**라고 하는가?

### 5. 안전하게 지우는 법 셋 (연결)

```java
// (1)
for (Iterator<String> it = l.iterator(); it.hasNext(); )
    if (it.next().endsWith("1")) it.remove();
// (2)
l.removeIf(s -> s.endsWith("1"));
// (3)
for (String s : new ArrayList<>(l)) if (s.endsWith("1")) l.remove(s);
```

- 셋의 결과는 같은가?
- (1)이 CME 를 안 내는 이유를 **구현의 한 줄**로 말하면?
- (1)에서 `cursor = lastRet` 은 무엇을 막는가?
- (2)는 내부적으로 몇 번 훑는가, 그 이름은 무엇인가?
- (3)의 비용은 무엇인가?
- 셋 중 기본으로 무엇을 쓰는가?

### 6. `removeIf` 안에서 컬렉션을 고치면 (경계)

```java
l.removeIf(s -> { if (s.equals("e2")) l.add("x"); return false; });
```

- 무엇이 되는가?
- `removeIf` 구현의 주석은 읽기와 쓰기를 어떻게 구분하는가?
- `ArrayList.removeIf` 는 `modCount` 를 몇 번 올리는가?

### 7. 맵에서 지우기 (예측)

```java
for (String k : m.keySet()) if (k.equals("k1")) m.remove(k);      // (A)
m.keySet().removeIf(k -> k.equals("k1"));                          // (B)
m.entrySet().removeIf(e -> e.getValue() == 1);                     // (C)
m.values().removeIf(v -> v == 1);                                  // (D)
for (var it = m.entrySet().iterator(); it.hasNext(); )
    if (it.next().getValue() == 1) it.remove();                    // (E)
```

- 다섯은 각각 어떻게 되는가?
- (A)만 다른 이유는 무엇인가?
- 키·값을 다 보면서 지우려면 어느 것을 쓰는가?

### 8. `ListIterator` 의 커서 (예측)

```java
List<String> l = new ArrayList<>(List.of("a", "b", "c"));
ListIterator<String> it = l.listIterator();
// 시작 / next() / next() / previous() 각 시점의
// nextIndex() · previousIndex() · hasNext() · hasPrevious()
```

- 네 시점 × 네 값 = 열여섯 칸은 각각 무엇인가?
- `next()` 로 `b` 를 받은 뒤 바로 `previous()` 를 부르면 무엇이 나오는가, 왜인가?
- 시작 시점의 `previousIndex()` 는 무엇인가?
- 커서는 원소를 가리키는가, 원소 사이를 가리키는가?

### 9. `ListIterator` 의 `set` 과 `add` (예측)

```java
ListIterator<String> i2 = l.listIterator();
i2.next(); i2.set("A");                   // (A) l 은?
i2.next(); i2.previous(); i2.set("B");    // (B) l 은?

for (ListIterator<String> i4 = l3.listIterator(); i4.hasNext(); ) {
    String s = i4.next();
    if (s.equals("b")) i4.add("b2");      // (C) 예외가 나는가? 결과는?
}

i6.next(); i6.add("x"); i6.set("y");      // (D) ?
```

- (A)~(D)는 각각 어떻게 되는가?
- (B)에서 `set` 의 **대상**은 무엇인가?
- (C)가 CME 를 안 내는 이유는 무엇인가?
- (C)에서 방금 넣은 `"b2"` 를 루프가 다시 만나는가?
- (D)가 그렇게 되는 이유를 `add` 구현의 **한 줄**로 말하면?

### 10. 안 던지는 컬렉션 (예측)

```java
List<String> cow = new CopyOnWriteArrayList<>(base());
for (String s : cow) { if (s.equals("e1")) cow.remove(s); }   // (A) 돈 원소는?
Iterator<String> it = cow.iterator(); it.next(); it.remove();  // (B) ?

Map<String,Integer> chm = new ConcurrentHashMap<>();  // k0..k4
for (String k : chm.keySet()) if (k.equals("k1")) chm.remove(k);  // (C)
```

- (A)~(C)는 각각 어떻게 되는가?
- (A)에서 **돈 원소가 몇 개**인가, 왜 그런가?
- (B)가 그렇게 되는 이유는 무엇인가?
- 이 컬렉션들이 안 던지는 것은 **보장인가**?

### 11. 무엇이 보장인가 (경계)

- `next()` 가 끝에서 `NoSuchElementException` 을 던지는 것은?
- 순회 중 수정이 `ConcurrentModificationException` 을 던지는 것은?
- **끝에서 두 번째를 지우면 안 터지는 것**은?
- `removeIf` 가 `modCount` 를 한 번만 올리는 것은?
- `ConcurrentModificationException` 을 `catch` 해서 재시도하는 코드는 왜 틀렸는가 — javadoc 문장은?

### 12. 이 주제의 경계 (연결)

- 「향상된 `for` 가 배열과 컬렉션에서 어떻게 다르게 컴파일되나」는 어느 문서인가?
- 「`ArrayList` 에서 중간 삭제가 왜 O(n) 인가」는 어디인가?
- 「`reversed()` 로 역순 순회하기」는 어디인가?
- 「`compute*` 안에서 맵을 고치면」은 어디인가?
- 「`CopyOnWriteArrayList` 의 동시성 계약」은 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
