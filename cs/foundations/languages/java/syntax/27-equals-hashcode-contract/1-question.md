# java/syntax/27 — `equals`/`hashCode`/`toString` 계약 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **어느 호출이 어떤 답을 내는지**를 묻는다.
> 해시 테이블이 어떻게 동작하는지는 [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/) 의 질문이다. 여기서는 **계약 위반의 증상**만 묻는다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `equals` 만 재정의한 클래스의 여섯 줄을 예측하라 (예측)

```java
class PointA {                        // equals 만 재정의, hashCode 는 안 함
    final int x, y;
    @Override public boolean equals(Object o) {
        return o instanceof PointA p && p.x == x && p.y == y;
    }
}
PointA a1 = new PointA(1, 2), a2 = new PointA(1, 2);
```

- `a1.equals(a2)` 는 무엇인가?
- `a1.hashCode() == a2.hashCode()` 는 무엇인가?
- `map.put(a1, "값")` 뒤의 `map.get(a2)` 는 무엇인가?
- `List.of(a1).contains(a2)` 는 무엇인가?
- 앞 두 줄과 마지막 줄의 답이 갈리는 이유는 무엇인가?
- `new HashSet<>(List.of(a1, a2)).size()` 는 무엇인가?

### 2. 계약의 조항을 세어 보라 (왜)

- `equals` 의 javadoc 계약은 몇 조항이고 각각 무엇인가?
- `hashCode` 의 javadoc 계약은 몇 조항이고 각각 무엇인가?
- 두 계약을 잇는 조항은 어느 방향으로 성립하는가?
- 반대 방향(해시가 같으면 equals 도 같다)이 요구되지 **않는** 이유는 무엇인가?
- `equals` 계약에서 `null` 조항이 따로 있는 이유는 무엇인가?

### 3. 넣어 둔 키의 필드를 바꾸면 (예측)

```java
class Tag { String name; /* equals·hashCode 를 name 으로 재정의 */ }

Tag key = new Tag("a");
map.put(key, "값");
key.name = "b";               // 넣은 뒤에 바꿨다
```

- `key.hashCode()` 는 바꾸기 전과 후에 각각 무엇인가(`Objects.hash` 를 썼을 때)?
- `map.get(key)` 는 무엇인가?
- `map.get(new Tag("b"))` 는 무엇인가?
- `map.size()` 와 `map.toString()` 은 무엇을 보여 주는가?
- `map.remove(key)` 는 성공하는가?
- 이 상태를 뭐라고 부르며, 왜 메모리 누수인가?

### 4. `java.util.Date` 와 `java.sql.Timestamp` (예측)

```java
Date d = new Date(1000L);
Timestamp t = new Timestamp(1000L);
```

- `d.equals(t)` 와 `t.equals(d)` 는 각각 무엇인가?
- `d.hashCode() == t.hashCode()` 는 무엇인가?
- `List.of(d).contains(t)` 와 `List.of(t).contains(d)` 는 각각 무엇인가?
- `HashSet` 에 `d` 를 먼저 넣고 `t` 를 넣었을 때와, 순서를 바꿨을 때의 `size()` 는 각각 무엇인가?
- 어느 계약 조항이 깨졌으며, 그 원인이 되는 코딩 패턴은 무엇인가?
- 이 패턴을 피하는 방법 두 가지는 무엇인가?

### 5. 매개변수 타입을 잘못 쓰면 (예측)

```java
class Id {
    final int v;
    public boolean equals(Id other) { return other != null && other.v == v; }
    @Override public int hashCode() { return v; }
}
Id a = new Id(1), b = new Id(1);
```

- `a.equals(b)` 는 무엇인가?
- `Object bo = b; a.equals(bo)` 는 무엇인가?
- 두 답이 갈리는 이유는 무엇인가?
- 컬렉션에서는 어느 쪽이 불리는가?
- 이 실수를 컴파일 에러로 바꾸는 방법은 무엇인가?

### 6. `toString` 은 무엇을 보장하는가 (경계)

- `Object.toString()` 의 기본 구현은 정확히 무엇을 돌려주는가?
- javadoc 은 `toString` 의 결과에 대해 어떤 보장을 **명시적으로 부정**하는가?
- 로그에 찍힌 `Plain@776ec8df` 에서 `776ec8df` 는 무엇인가?
- `toString` 결과를 파싱하거나 비교에 쓰면 안 되는 이유는 무엇인가?
- `toString` 은 계약인가 권고인가?

### 7. `record` 는 무엇을 해결하는가 (연결)

- `record Pt(int x, int y) {}` 가 자동으로 만드는 메서드는 무엇인가?
- `new Pt(1,2).toString()` 의 형태는 무엇인가?
- `record` 의 `equals` 는 `instanceof` 를 쓰는데 왜 대칭성 문제가 없는가?
- 컴포넌트를 하나 추가했을 때 손으로 쓴 클래스와 `record` 의 차이는 무엇인가?

### 8. 어디까지가 이 주제이고 어디부터가 다른 주제인가 (경계)

- "버킷을 어떻게 고르고 충돌을 어떻게 처리하나"는 어느 문서가 정본인가?
- `TreeMap`/`TreeSet` 은 같음을 무엇으로 판정하는가, 그러면 `equals` 는 어떻게 되는가?
- `hashCode` 를 `return 1;` 로 쓰면 계약을 어기는가, 무엇이 나빠지는가?
- 서비스 클래스·컨트롤러에 `equals` 를 재정의해야 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
