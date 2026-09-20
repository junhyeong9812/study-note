# java/syntax/19 — 타입 소거: 런타임에 없는 것·제네릭 배열·브리지 메서드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·바이트코드·에러를 맞힐 수 있는지**를 묻는다.
> 이 주제는 특히 **`javap` 출력을 예측**하는 문항이 많다. 답을 보기 전에 직접 찍어 보라.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 코드의 바이트코드에는 무엇이 있는가 (예측)

```java
List<String> names = new ArrayList<>();

int firstLength() {
    names.add("hello");
    String s = names.get(0);     // 캐스팅을 안 썼다
    return s.length();
}
```

- `javap -c` 로 찍으면 `names` 필드의 타입은 어떻게 나오는가?
- `add` 와 `get` 의 시그니처는 무엇인가?
- 소스에 없던 명령 하나가 들어가는데 무엇인가, 어디에 들어가는가?
- `<T extends Comparable<T>> T max(List<T>)` 의 반환은 무엇으로 소거되는가?

### 2. 그럼 지워지기만 하는가 (예측)

```java
List<String> names;
Map<String, List<Integer>> index;
static <T extends Comparable<T>> T max(List<T> list) { ... }
static class Box<T extends Number> { T value; T get(); void set(T t); }
```

- `javap -v` 로 찍으면 각 필드·메서드에 **두 줄**이 나온다. 무엇과 무엇인가?
- `names` 의 `descriptor` 와 `Signature` 는 각각 무엇인가?
- `Box<T extends Number>` 의 `T value` 는 `descriptor` 가 무엇인가?
- `Signature` 속성은 JVM 이 실행에 쓰는가?

### 3. 리플렉션의 비대칭 (예측)

```java
List<String> names;
Map<String, Integer> count(List<String> in, Set<? extends Number> ns) { ... }

List<String>  strings = new ArrayList<>(List.of("a"));
List<Integer> ints    = new ArrayList<>(List.of(1));
```

- `getDeclaredField("names")` 의 `getType()` 과 `getGenericType()` 은 각각 무엇인가?
- `count` 의 `getParameterTypes()` 와 `getGenericParameterTypes()` 는 각각 무엇인가?
- `strings.getClass() == ints.getClass()` 는 무엇인가?
- `strings.getClass().getTypeParameters()` 는 무엇을 주는가? 그것으로 `String` 을 알 수 있는가?

### 4. 소거된 리스트에 다른 타입을 넣으면 (예측)

```java
List<String> strings = new ArrayList<>(List.of("a"));
List raw = strings;
raw.add(42);
System.out.println(strings);
String bad = strings.get(1);
```

- `raw.add(42)` 는 런타임에 터지는가?
- `System.out.println(strings)` 는 무엇을 찍는가?
- 마지막 줄은 어떻게 되는가, **메시지 전문**은 무엇인가?
- 왜 넣는 자리가 아니라 꺼내는 자리에서 터지는가?

### 5. 런타임에 못 하는 것들 (예측)

```java
static <T> T[] makeArray(int n) { return new T[n]; }          // (A)
static <T> T makeOne() { return new T(); }                    // (B)
static <T> Class<T> clazz() { return T.class; }               // (C)
static <T extends Exception> void c(Runnable r) {
    try { r.run(); } catch (T e) { }                          // (D)
}
static List<String>[] genericArray = new List<String>[3];     // (E)
static List<?>[] wildcardArray = new List<?>[3];              // (F)
static List[] rawArray = new List[3];                         // (G)
```

- 일곱 자리에서 각각 어떤 에러가 나는가? 안 나는 것은 무엇인가?
- (E)와 (F)가 갈리는 기준은 무엇인가?
- 각각의 우회 관용구는 무엇인가?

### 6. `instanceof` 와 캐스팅 (예측)

```java
Object o = new ArrayList<String>();
o instanceof List<String>     // (A)
o instanceof List<?>          // (B)
o instanceof List             // (C)
List<String> l = (List<String>) o;   // (D)
```

- 네 자리에서 각각 어떻게 되는가? (A)의 에러 메시지는 무엇인가?
- (D)는 컴파일되는가? 경고가 난다면 무엇인가?
- (D)가 "성공"했다는 것은 무엇을 뜻하는가? 언제 문제가 드러나는가?

### 7. 소거 후 충돌 (예측)

```java
void print(List<String> l) {}
void print(List<Integer> l) {}                                        // (A)

static class A { Object get() { return null; } }
static class B extends A { String get() { return null; } }            // (B)

static class Both implements Comparable<String>, Comparable<Integer> { ... }   // (C)
```

- (A)(B)(C)에서 각각 어떻게 되는가, 메시지는 무엇인가?
- (B)는 왜 되는가?
- (A)를 피하려면 무엇을 해야 하는가?

### 8. 힙 오염은 어디서 터지는가 (예측)

```java
static <T> void polluteQuietly(List<T>... lists) {
    Object[] objects = lists;
    objects[0] = List.of(42);
    T first = lists[0].get(0);
    System.out.println("first = " + first);
}
static <T> List<T>[] leak(List<T>... lists) { return lists; }

polluteQuietly(List.of("a"), List.of("b"));               // (A)

List<String>[] arr = leak(List.of("a"), List.of("b"));    // (B)
Object[] objs = arr;
objs[0] = List.of(42);
String s = arr[0].get(0);
```

- (A)는 예외를 던지는가? 안 던진다면 무엇이 찍히는가?
- `objects[0] = List.of(42)` 를 배열의 경비원(`aastore`)이 못 막는 이유는 무엇인가?
- (B)의 마지막 줄은 어떻게 되는가?
- 컴파일 경고는 **어느 자리에** 나오는가?

### 9. `@SafeVarargs` (경계)

```java
@SafeVarargs <T> List<T> instanceMethod(List<T>... l) { return l[0]; }        // (A)
@SafeVarargs final <T> List<T> finalMethod(List<T>... l) { return l[0]; }     // (B)
@SafeVarargs static <T> List<T> staticMethod(List<T>... l) { return l[0]; }   // (C)
@SafeVarargs <T> List<T> notVarargs(List<T> l) { return l; }                  // (D)
```

- 넷 중 어디가 컴파일 에러인가, 메시지는 무엇인가?
- 붙일 수 있는 자리가 제한된 이유는 무엇인가?
- `@SafeVarargs` 가 실제로 하는 일은 무엇인가? 안전하게 만들어 주는가?

### 10. 브리지 메서드 (예측)

```java
static class Node<T> { T value; void set(T v) { this.value = v; } T get() { return value; } }
static class StringNode extends Node<String> {
    @Override void set(String v) { this.value = v.toUpperCase(); }
    @Override String get() { return value; }
}
```

- `StringNode.class.getDeclaredMethods()` 는 몇 개를 주는가? 무엇들인가?
- `javap -c` 로 찍으면 소스에 없는 메서드가 나오는데, 각각 무슨 일을 하는가?
- **반환 타입만 다른 메서드 둘**이 한 클래스에 있을 수 있는가?
- 그 브리지를 리플렉션으로 직접 불러 `Integer` 를 넘기면 어떻게 되는가?
- 프레임워크가 메서드를 훑을 때 무엇을 조심해야 하는가?

### 11. `TypeToken` / super type token 은 왜 동작하는가 (왜)

```java
static abstract class TypeRef<T> {
    final Type type;
    protected TypeRef() {
        Type sup = getClass().getGenericSuperclass();
        this.type = ((ParameterizedType) sup).getActualTypeArguments()[0];
    }
}
TypeRef<Map<String, List<Integer>>> ref = new TypeRef<>() {};
static class Raw extends TypeRef {}
```

- `ref.type` 은 무엇인가? 중첩된 타입 인자까지 읽히는가?
- 소거된다면서 어떻게 읽히는가 — 그 정보가 어디에 있는가?
- `new Raw()` 는 어떻게 되는가? `javap` 로 두 클래스를 비교하면 무엇이 다른가?
- `{}` 를 빼면 왜 안 되는가?
- 이 관용구를 쓰는 실제 라이브러리는 무엇인가?

### 12. 가변 인자 배열의 런타임 타입 (예측)

```java
static void whatIsIt(Object... xs)        { System.out.println(xs.getClass().getName()); }
static <T> void whatIsItGeneric(T... xs)  { System.out.println(xs.getClass().getName()); }

whatIsIt("a", "b");
whatIsItGeneric("a", "b");
whatIsItGeneric(1, 2);

static <T> T[] pickTwo(T a, T b, T c) { return (T[]) new Object[]{a, b}; }
String[] picked = pickTwo("a", "b", "c");
Object[] ok     = pickTwo("a", "b", "c");
```

- 세 호출이 각각 무엇을 찍는가? `T...` 가 `Object[]` 가 아닌 이유는?
- `String[] picked = ...` 는 어떻게 되는가, **메시지 전문**은?
- `Object[] ok = ...` 는 되는가? 왜 갈리는가?

### 13. 지역 변수의 제네릭 타입은 어디에 있는가 (경계)

```java
void localGeneric() { List<String> local = new ArrayList<>(); local.add("x"); }
```

- 이 지역 변수의 제네릭 타입이 클래스 파일에 남는가? 어느 속성인가?
- 컴파일 옵션에 따라 달라지는가?
- 리플렉션으로 읽을 수 있는가?

### 14. 다른 주제와 잇기 (연결)

- `new List<String>[3]` 금지가 배열의 어떤 성질과 얽혀 있는가? 그 정본은 어디인가?
- 제네릭이 **불공변**으로 설계된 이유가 이 주제와 어떻게 이어지는가?
- "클래스 파일에 무엇이 남나"를 `javap -v` 로 확인한다는 점에서 구조가 같은 주제는 무엇인가?
- 자바가 소거를 택한 이유는 무엇이었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
