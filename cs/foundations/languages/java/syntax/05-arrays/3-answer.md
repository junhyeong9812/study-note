# java/syntax/05 — 배열: 생성·기본값·공변성·`Arrays` 유틸 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·바이트코드는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램은 **17.0.13 · 25.0.1** 에서도 돌렸고, 달라진 것은 **`Object.toString` 의 16진수와 `Arrays.hashCode(int[][])` 값뿐**이었다(둘 다 identity hash 기반).\
> 바이트코드는 `javap -c -p` 출력을, javadoc 은 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 배열은 무엇의 인스턴스인가

**출력** (`Ex.java (05-a)`, JDK 21.0.5)

```text
getClass()        = class [I
getName()         = [I
getSimpleName()   = int[]
superclass        = class java.lang.Object
인터페이스         = [interface java.lang.Cloneable, interface java.io.Serializable]
isArray           = true
toString()        = [I@29453f44
hashCode 는 identity = true
```

**네 줄의 출력**

- `getName()` -> **`[I`**
- `getSuperclass()` -> **`class java.lang.Object`**
- `getInterfaces()` -> **`[interface java.lang.Cloneable, interface java.io.Serializable]`**
- `toString()` -> **`[I@29453f44`** (뒤 16진수는 실행·JDK 마다 다르다)

```text
      Object
        |
   상속 (JLS §10.8)
        |
   +----+--------+
   |             |
  int[]      String[]        <- JVM 이 만들어 주는 클래스. 소스 파일이 없다
   |
   구현: Cloneable, Serializable
   멤버: public final int length
         public Object clone()
```

내부 표기 읽는 법:

| 표기 | 타입 |
|---|---|
| `[I` | `int[]` |
| `[[I` | `int[][]` |
| `[Ljava.lang.String;` | `String[]` |
| `[Z` `[B` `[C` `[D` `[F` `[J` `[S` | `boolean[]` `byte[]` `char[]` `double[]` `float[]` `long[]` `short[]` |

**`length` 는 필드인가 메서드인가**

- **필드**다. `public final int length`.
- `length()` 라고 쓰면 컴파일 에러다. `String` 은 `length()`, `List` 는 `size()`, 배열은 `length` — 셋이 다 다르다.
- 바이트코드에서는 전용 명령 `arraylength` 로 나온다(`Ex.java (05-g)`).

```text
  static int len(int[]);
    Code:
       0: aload_0
       1: arraylength
       2: ireturn
```

**`equals`/`hashCode`/`toString` 은 재정의돼 있는가**

- **아니다.** `Object` 의 것 그대로다.
- 그래서 `equals` 는 참조 비교, `hashCode` 는 identity hash, `toString` 은 `[I@29453f44` 형태다.\
  출력의 `hashCode 는 identity = true` 가 그 확인이다.
- 내용 기반이 필요하면 **`Arrays` 의 정적 메서드**를 써야 한다 — 이것이 5번의 주제다.

### 2. 이 배열들의 내용은 무엇인가

**출력** (`Ex.java (05-a)`)

```text
int[]     기본값 = [0, 0]
boolean[] 기본값 = [false, false]
String[]  기본값 = [null, null]
비정방            = [[1], [1, 2], [1, 2, 3]]
안쪽 미할당        = [null, null]
```

**넷을 찍으면**

| 선언 | 출력 |
|---|---|
| `new int[2]` | `[0, 0]` |
| `new boolean[2]` | `[false, false]` |
| `new String[2]` | `[null, null]` |
| `new int[3][]` | `deepToString` -> `[null, null, null]` |

- 기본형은 0(또는 `false`), 참조는 `null` 로 **채워져서 나온다.**
- `new String[2]` 는 **`String` 객체 두 개가 아니다.** 빈 칸 두 개다.

**`new int[2][3]` 과 `new int[2][]` 의 차이**

```text
new int[2][3]                            new int[2][]

  m ---> +---------+---------+             g ---> +------+------+
         | 참조 #A | 참조 #B |                     | null | null |
         +---------+---------+                     +------+------+
              |         |
              v         v
        +---+---+---+  +---+---+---+       안쪽 배열이 만들어지지 않았다
        | 0 | 0 | 0 |  | 0 | 0 | 0 |
        +---+---+---+  +---+---+---+
```

- 앞은 안쪽까지 만든다 — 바이트코드도 `multianewarray` 하나다.
- 뒤는 **바깥만** 만든다 — `anewarray "[I"` 다. 안쪽은 내가 채워야 한다.
- 뒤의 형태를 쓰면 **행마다 길이를 다르게** 할 수 있다(비정방 배열).

**`jag[0][0] = 1;` 을 하면**

- `jag[0]` 이 `null` 이므로 **`NullPointerException`** 이다.

**출력** (`Ex.java (05-e)`)

```text
미할당 안쪽 -> Cannot store to int array because "<local4>[0]" is null
```

- 메시지가 `"<local4>[0]"` 이라고 **어느 칸이 `null` 인지 짚어 준다**(helpful NPE).
- 단 그 이름은 컴파일 옵션에 따라 달라진다 — 8번에서 다룬다.

### 3. 이 코드는 어디서 터지는가

**출력** (`Ex.java (05-b)`, 17·21·25 에서 **완전히 동일**)

```text
대입 통과. objects.getClass() = [Ljava.lang.String;
String 저장 성공: 문자열은 들어간다
catch  : java.lang.ArrayStoreException: java.lang.Integer
message: java.lang.Integer
```

잡지 않으면 이렇게 죽는다.

```text
Exception in thread "main" java.lang.ArrayStoreException: java.lang.Integer
	at Ex.main(Ex.java:45)
```

**(A)(B)(C) 중 어디가 무엇인가**

| 줄 | 결과 |
|---|---|
| (A) `Object[] objects = strings;` | **통과.** 컴파일도 실행도 문제없다 |
| (B) `objects[0] = "문자열";` | **통과.** 런타임 원소 타입이 `String` 이므로 맞다 |
| (C) `objects[1] = Integer.valueOf(42);` | **런타임 예외** — `ArrayStoreException` |

```text
  컴파일 타임                          런타임
  +----------------------------+      +----------------------------+
  | 정적 타입만 본다             |      | 배열의 런타임 원소 타입과   |
  | Object[] <- String[]       |      | 넣는 값의 타입을 비교한다    |
  | 공변이니 통과               |      | String 전용인데 Integer    |
  | 경고 하나 없다               |      | -> ArrayStoreException     |
  +----------------------------+      +----------------------------+
```

**예외 이름과 메시지 전문**

- `java.lang.ArrayStoreException: java.lang.Integer`
- `getMessage()` 는 **`java.lang.Integer`** — 즉 **넣으려던 값의 타입 이름 하나**뿐이다.
- 배열이 무슨 타입이었는지, 인덱스가 몇이었는지는 **안 알려 준다.** 스택트레이스의 줄 번호로 찾아야 한다.

상속 계층에서도 같다.

```text
Number[] 인 척하는 Integer[] 에 Double -> java.lang.ArrayStoreException: java.lang.Double
```

**`List<String>` / `List<Object>` 로 하면**

**컴파일 에러** (`Ex.java (05-c1)`)

```text
Ex.java:6: error: incompatible types: List<String> cannot be converted to List<Object>
        List<Object> objects = strings;
                               ^
1 error
```

- **대입 자체가 막힌다.** 런타임까지 가지 않는다.
- 배열은 (A)를 통과시키고 (C)에서 터뜨리고, 제네릭은 (A)에서 막는다 — **같은 실수를 언제 잡느냐의 차이**다.

### 4. 공변성의 검사는 누가 언제 하는가

**JLS 의 어느 규칙인가**

- **JLS SE 21 §4.10.3 (Subtyping among Array Types).**\
  `S` 가 `T` 의 하위 타입이면 `S[]` 도 `T[]` 의 하위 타입이다.
- 그래서 `Object[] o = new String[3];` 은 **명세가 허용하는 합법 코드**다. 경고를 내면 오히려 명세 위반이다.
- 실패 시 `ArrayStoreException` 을 던지는 것도 명세가 정한다(JLS §10.10).

**저장 시 검사를 하는 JVM 명령**

**`javap -c -p Ex.class` 출력 그대로** (`Ex.java (05-g)`)

```text
  static void store(java.lang.Object[], java.lang.Object);
    Code:
       0: aload_0
       1: iconst_0
       2: aload_1
       3: aastore              <- 여기서 런타임 타입 검사
       4: return

  static int read(int[], int);
    Code:
       0: aload_0
       1: iload_1
       2: iaload
       3: ireturn
```

- 참조 배열 저장은 **`aastore`**, `int` 배열 저장은 `iastore` 다.
- **`aastore` 만 검사한다.**

**`int[]` 에는 왜 그 검사가 없는가**

```text
참조 배열                                기본형 배열
+-------------------------------+       +-------------------------------+
| Object[] 로 받을 수 있다        |       | int[] 은 Object[] 가 아니다    |
| 그래서 런타임 타입이 정적 타입과 |       | Object 의 하위 타입일 뿐이다    |
| 다를 수 있다                    |       | 정적 타입 = 런타임 타입         |
| -> 매번 확인해야 한다           |       | -> 확인할 것이 없다             |
+-------------------------------+       +-------------------------------+
```

- 확인으로 실제 출력이 있다(`Ex.java (05-b)`).

```text
int[] 를 Object 로는 받는다: true
```

- `int[]` 을 `Object[]` 에 넣으려 하면 컴파일 에러다 — **기본형 배열끼리는 공변 관계가 없다.**

**배열을 공변으로 만든 이유**

- **제네릭이 없던 Java 1.0 에서 범용 메서드를 쓸 방법이 그것뿐이었다.**
- `Arrays.sort(Object[])`, `Collection.toArray(Object[])` 같은 메서드가 모든 참조 배열에 통하려면 공변성이 필요했다.
- 제네릭이 들어온 뒤에도 **호환성 때문에** 배열 규칙은 그대로 남았다.
- *(이 설계 배경은 이 문서의 기준 소스(JLS·javadoc)로 확인한 것이 아니다 — 통설이다. 정확한 설계 논쟁 기록은 확인 필요.)*

**제네릭은 왜 같은 선택을 하지 않았나**

- 제네릭은 **타입 소거**로 구현된다 — 런타임에 `List<String>` 인지 `List<Object>` 인지 구분할 정보가 **없다.**
- 즉 `aastore` 같은 **런타임 검사를 할 수가 없다.** 그러므로 컴파일 타임에 막는 수밖에 없다.
- 대신 필요할 때만 여는 장치로 **와일드카드**(`? extends` / `? super`)를 뒀다(목록의 **18번 주제**).

같은 이유로 제네릭 배열 생성이 금지된다(`Ex.java (05-c2)`).

```text
Ex.java:5: error: generic array creation
        List<String>[] a = new List<String>[3];
                           ^
1 error
```

- 배열은 **런타임에 자기 원소 타입을 알아야** 하는데, 제네릭은 그 시점에 타입 인자가 없다.\
  타입 소거 자체는 목록의 **19번 주제**가 정본이다.

### 5. `Arrays.equals` 와 `deepEquals` 가 갈리는 지점

**출력** (`Ex.java (05-d)`, JDK 21.0.5)

```text
p.equals(q)          = false
Arrays.equals(p,q)   = false
Arrays.deepEquals    = true
1차원 Arrays.equals  = true
p 자체              = [[I@12a3a380
Arrays.toString(p)  = [[I@5cad8086, [I@6e0be858]
Arrays.deepToString = [[1, 2], [3, 4]]
```

**세 결과**

- `p.equals(q)` -> **`false`** (`Object.equals` — 참조 비교)
- `Arrays.equals(p,q)` -> **`false`**
- `Arrays.deepEquals(p,q)` -> **`true`**

```text
Arrays.equals(p, q)                      Arrays.deepEquals(p, q)
+-------------------------------+        +-------------------------------+
| 바깥 원소를 한 겹만 비교한다    |        | 원소가 배열이면 재귀로 내려간다 |
|   p[0].equals(q[0]) ?         |        |   p[0] 과 q[0] 의 내용 비교    |
|   배열의 equals = 참조 비교    |        |   1==1, 2==2 -> true          |
|   -> 다른 객체 -> false       |        |                               |
+-------------------------------+        +-------------------------------+
```

**`Arrays.equals(f1, f2)` 는 왜 다른가**

- **`true`** 다.
- 1차원 `int[]` 의 원소는 `int` 값이므로 **한 겹만 봐도 내용 비교가 된다.**
- 그래서 **1차원에서는 `equals` 와 `deepEquals` 가 같은 답을 낸다.**\
  차원이 늘어나는 순간 조용히 갈린다 — 이것이 이 함정이 안 잡히는 이유다.

**`toString` 과 `deepToString`**

- `Arrays.toString(p)` -> `[[I@5cad8086, [I@6e0be858]` — 원소가 배열이라 주소가 찍힌다.
- `Arrays.deepToString(p)` -> `[[1, 2], [3, 4]]`
- 로그에 `[I@...` 가 보이면 **`deepToString` 을 안 쓴 것**이다.

**배열을 `HashMap` 의 키로 써도 되는가**

**출력** (`Ex.java (05-i)`, 17·21·25 동일)

```text
Arrays.hashCode(p)==Arrays.hashCode(q) = false
Arrays.deepHashCode(p)==deepHashCode(q) = true
deepHashCode 값 = 32833
1차원 Arrays.hashCode 일치 = true / 값 = 30817
f1.hashCode()==f2.hashCode() = false
```

- **안 된다.** 마지막 줄이 이유다 — 내용이 같은 두 배열의 `hashCode()` 가 다르다.
- 배열은 `hashCode`/`equals` 를 **재정의하지 않았으므로** identity 기반이다.\
  `map.put(new int[]{1,2}, v)` 뒤 `map.get(new int[]{1,2})` 는 언제나 `null` 이다.
- 대안: `List.of(1,2)` 를 키로 쓰거나(내용 기반), 문자열로 바꾸거나, 래퍼 클래스를 만들어 `Arrays.hashCode`/`Arrays.equals` 로 구현한다.
- 계약을 깬 키가 `HashMap` 에서 어떻게 사라지는지는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

**주의** — `Arrays.hashCode(int[][])` 의 **구체적 값은 JDK 마다 달랐다**(17·21·25 에서 셋 다 다른 수).\
안쪽 배열의 identity hash 를 쓰기 때문이다. `deepHashCode` 는 내용 기반이라 세 JDK 에서 `32833` 으로 같았다.\
그래도 **"세 곳에서 같았다"는 관찰이지 보장이 아니다.**

### 6. `Arrays.asList` 가 놓는 함정 셋

**출력** (`Ex.java (05-d)`)

```text
asList(int[]) size   = 1
asList(int[]) 원소0  = [I
asList(Integer[]) size = 3
asList 구현 클래스    = java.util.Arrays$ArrayList
set 은 된다           = [A, b, c]
add -> java.lang.UnsupportedOperationException : null
remove -> java.lang.UnsupportedOperationException : null
배열을 고치면 리스트도 = [CHANGED, y]
리스트를 고치면 배열도 = [CHANGED, SET]
List.of 구현 클래스   = java.util.ImmutableCollections$List12
List.of set -> java.lang.UnsupportedOperationException : null
```

**`a.size()` 는 무엇인가**

- **1** 이다. 원소는 `int[]` 객체 하나(`[I`).

```text
Arrays.asList(T... a) 에 무엇이 들어가나

  Integer[] 를 넘기면                     int[] 을 넘기면
  +----------------------------+         +----------------------------+
  | T = Integer                |         | int 는 T 가 될 수 없다      |
  | 가변 인자 셋으로 풀린다      |         | (기본형은 타입 인자 불가)   |
  | size = 3                   |         | 그래서 T = int[]           |
  |                            |         | size = 1                   |
  +----------------------------+         +----------------------------+
```

- `Integer[]` 를 넘기면 3이다 — **박싱 여부 하나로 결과가 갈린다.**
- 뿌리는 **"기본형은 제네릭 타입 인자가 될 수 없다"** 는 규칙이다([`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/)).
- 고치려면 `Arrays.stream(prim).boxed().toList()`.

**`set` 과 `add`**

- `set(0,"A")` -> **된다.** 배열의 칸을 바꾸는 것뿐이다.
- `add("d")` -> **`UnsupportedOperationException`**, `remove(0)` 도 같다.
- **`getMessage()` 는 `null`** 이다 — 메시지가 없다.\
  로그에 `java.lang.UnsupportedOperationException` 한 줄만 남으므로, 스택트레이스에서 `java.util.Arrays$ArrayList` 를 보고 원인을 짚어야 한다.
- javadoc 이 그대로 못박는다 — "Returns a **fixed-size** list backed by the specified array."\
  "The returned list implements the optional `Collection` methods, **except those that would change the size** of the returned list."

**`backing[0] = "CHANGED"` 뒤 `view`**

- **`[CHANGED, y]`** 다. 반대 방향도 통한다 — `view.set(1,"SET")` 뒤 `backing` 은 `[CHANGED, SET]`.
- javadoc: "Changes made to the array will be visible in the returned list, and changes made to the list will be visible in the array."
- **복사가 아니라 뷰**다. 방어적 복사로 착각해 쓰면 그대로 새어 나간다.

**셋을 한꺼번에 피하려면**

- **`List.of(...)`** 를 쓴다.
  - 크기 고정 + `set` 까지 금지 (`UnsupportedOperationException`)
  - 원본 배열과 분리됨 (원소를 복사한다)
  - 가변 인자라 `int[]` 함정은 그대로 남는다 — 기본형은 여전히 `Arrays.stream(...).boxed()` 가 필요하다
- **대가**: `null` 원소를 허용하지 않는다(`NullPointerException`). 그리고 원소 복사 비용 O(n) 이 든다.
- "불변"과 "수정 불가 뷰"의 차이는 목록의 **40번 주제**가 정본이다.

### 7. 복사 수단 넷의 차이

**출력** (`Ex.java (05-d)`)

```text
arraycopy(src,1,dst,0,3) = [2, 3, 4, 0, 0]
copyOf(src, 3)      = [1, 2, 3]
copyOf(src, 8)      = [1, 2, 3, 4, 5, 0, 0, 0]
copyOfRange(src,1,4)= [2, 3, 4]
clone 내용 동일      = true / 같은 객체 = false
```

**넷의 차이**

| 수단 | 목적지 | 길이 | 특징 |
|---|---|---|---|
| `System.arraycopy(src,sp,dst,dp,n)` | **이미 있어야 한다** | 내가 정한다 | 가장 저수준. `ArrayList` 내부가 쓴다. 겹치는 구간도 안전 |
| `Arrays.copyOf(src, n)` | 만들어 준다 | `n` | 길면 기본값으로 채우고 짧으면 자른다 |
| `Arrays.copyOfRange(src, from, to)` | 만들어 준다 | `to - from` | `to` 는 **배타적** |
| `src.clone()` | 만들어 준다 | 원본과 같다 | 한 겹만 복사 |

**`Arrays.copyOf(src, src.length + 3)` 의 뒤 세 칸**

- **기본값**이 들어간다 — `int[]` 이면 `0`, 참조 배열이면 `null`.
- 출력의 `copyOf(src, 8) = [1, 2, 3, 4, 5, 0, 0, 0]` 이 그 확인이다.
- 새 배열을 만들 때의 기본값 규칙(2번)이 그대로 적용된다.

**`clone()` 뒤 `deep[0][0]`**

**출력** (`Ex.java (05-d)`)

```text
얕은 복사 후 원본    = [[99, 2], [3, 4]]
바깥은 다른 객체     = false / 안쪽은 같은 객체 = true
```

- **99 다.** 원본이 오염됐다.

```text
  deep    ---> [ #A , #B ]
                 |    |
                 +----+---- 같은 안쪽 배열 ----+----+
                 |    |                       |    |
  shallow ---> [ #A , #B ]                     v    v
                                          [99, 2]  [3, 4]
```

- `clone()` 은 **바깥 배열만** 새로 만든다. 원소(= 안쪽 배열 참조)는 그대로 복사된다.
- 출력의 `안쪽은 같은 객체 = true` 가 직접 증거다.

**다차원 배열을 방어적으로 복사하려면**

```java
int[][] deepCopy = new int[src.length][];
for (int i = 0; i < src.length; i++) {
    deepCopy[i] = src[i].clone();      // 3차원이면 또 한 겹 들어가야 한다
}
```

- 차원마다 한 겹씩 직접 돌아야 한다. **표준 라이브러리에 "깊은 복사" 메서드는 없다.**
- `Arrays.copyOf(src, src.length)` 도 똑같이 얕다.

### 8. 배열이 던지는 예외들의 메시지

**출력** (`Ex.java (05-e)`, 17·21·25 에서 **완전히 동일**)

```text
a[3]   -> java.lang.ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3
a[-1]  -> java.lang.ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3
a[5]=1 -> java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3
AIOOBE 의 부모 = java.lang.IndexOutOfBoundsException
new int[-1] -> java.lang.NegativeArraySizeException: -1
new int[2][-3] -> java.lang.NegativeArraySizeException: -3
null[0] -> Cannot load from int array because "<local3>" is null
null.length -> Cannot read the array length because "<local3>" is null
미할당 안쪽 -> Cannot store to int array because "<local4>[0]" is null
arraycopy 초과 -> java.lang.ArrayIndexOutOfBoundsException: arraycopy: last destination index 3 out of bounds for int[2]
arraycopy 타입 -> java.lang.ArrayStoreException: arraycopy: type mismatch: can not copy int[] into object array[]
```

잡지 않으면 스택트레이스가 이렇게 나온다.

```text
Exception in thread "main" java.lang.ArrayIndexOutOfBoundsException: Index 10 out of bounds for length 3
	at Ex.deeper(Ex.java:51)
	at Ex.deep(Ex.java:50)
	at Ex.main(Ex.java:48)
```

**다섯 자리의 예외**

| 자리 | 예외 |
|---|---|
| (A) `a[3]` | `ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3` |
| (B) `a[-1]` | `ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3` |
| (C) `new int[-1]` | `NegativeArraySizeException: -1` |
| (D) `nil[0]` | `NullPointerException` (메시지는 조건에 따라 다름) |
| (E) `arraycopy(..., 3)` | `ArrayIndexOutOfBoundsException: arraycopy: last destination index 3 out of bounds for int[2]` |

**(A)와 (B)의 예외 이름은 같은가**

- **같다.** 음수 인덱스도 `ArrayIndexOutOfBoundsException` 이다. 따로 있는 예외가 아니다.
- 부모는 **`java.lang.IndexOutOfBoundsException`** 이다 — `List.get` 이 던지는 것과 같은 부모다.
- **읽기와 쓰기도 같은 예외**다. `a[3]` 도 `a[5] = 1` 도 같다.

**(C)는 컴파일 에러인가 런타임 예외인가**

- **런타임 예외**다. `new int[n]` 의 `n` 은 실행 시점에 평가되므로 컴파일러가 알 수 없다.
- 리터럴로 `new int[-1]` 이라 써도 **컴파일은 된다**(`Ex.java (05-c2)` 에서 확인했다 — 그 파일의 컴파일 에러는 제네릭 배열 쪽 한 건뿐이었다).
- 실제로는 `new int[end - start]` 처럼 **계산해서 넘기는 코드**에서 난다.

**(D)의 메시지는 무엇에 따라 달라지는가**

`Ex.java (05-f)` 를 세 JDK × 세 조건으로 돌렸다. **세 JDK 의 결과가 조건별로 완전히 같았고, 조건이 메시지를 갈랐다.**

```text
javac (기본, -g 없음)                     javac -g
[1] Cannot load from int array           [1] Cannot load from int array
    because "<local1>" is null               because "nil" is null
[2] Cannot read the array length         [2] Cannot read the array length
    because "<local1>" is null               because "nil" is null
[3] Cannot store to int array            [3] Cannot store to int array
    because "<local2>[0]" is null            because "outer[0]" is null

java -XX:-ShowCodeDetailsInExceptionMessages   (셋 다)
[1] null
[2] null
[3] null
```

- **`javac -g` 여부**가 변수 이름을 결정한다. 없으면 `<local1>` 같은 슬롯 번호다.
- **JVM 플래그**로 메시지를 통째로 끌 수 있다 — 그러면 `getMessage()` 가 `null` 이다.
- 그러므로 **NPE 메시지 문구에 의존하는 테스트나 파싱 코드를 쓰면 안 된다.**
- 동작 자체(어느 연산에서 NPE 가 나는가)는 **바뀌지 않는다.** 바뀌는 것은 설명 문구뿐이다.

> **helpful NullPointerException** — NPE 메시지에 "어느 식이 `null` 이었는지"를 적어 주는 기능(JEP 358, Java 14 도입, 15부터 기본 켜짐).\
> 예: `Cannot read the array length because "nil" is null`.

### 9. 배열 길이 0 과 `null`

**`new int[0]` 은 합법인가**

**출력** (`Ex.java (05-a)`)

```text
length 0          = 0 []
```

- **합법이다.** 정상적인 배열 객체이고 `length` 가 0 이다.
- 반복문이 0회 돌 뿐 아무 예외도 안 난다.

**API 가 "결과 없음"을 돌려줄 때**

```text
null 을 돌려주는 API                      길이 0 배열을 돌려주는 API
+-------------------------------+        +-------------------------------+
| String[] r = find(...);       |        | String[] r = find(...);       |
| if (r != null)                |        | for (String s : r) { ... }    |
|     for (String s : r) {...}  |        |                               |
|                               |        | 검사가 필요 없다               |
| 검사를 빠뜨리면 NPE            |        | 빠뜨릴 것이 없다               |
+-------------------------------+        +-------------------------------+
```

- **길이 0 배열이 낫다.** 호출자가 `null` 검사를 안 해도 된다.
- 길이 0 배열은 **불변이나 다름없다**(고칠 칸이 없다). 그래서 `private static final String[] EMPTY = new String[0];` 를 상수로 공유해도 안전하다.
- `Collections.emptyList()` 가 같은 발상이다.

**`toArray` 두 형태의 런타임 타입**

**출력** (`Ex.java (05-h)`)

```text
toArray() 의 런타임 타입 = [Ljava.lang.Object;
toArray(new String[0])   = [Ljava.lang.String;
```

- `toArray()` -> **`Object[]`**. `String[]` 으로 캐스팅하면 `ClassCastException` 이다.
- `toArray(new String[0])` -> **`String[]`**. 인자로 준 배열의 **런타임 타입**으로 만들어 준다.
- 길이 0 배열을 넘기는 관용구가 여기서 나온다 — 어차피 필요한 길이로 새로 만들어 주므로 미리 크게 만들 이유가 없다.

### 10. 배열 대신 `List` 를 써야 하는 자리

**공개 API 의 반환 타입으로 배열을 쓰면**

- **호출자가 내용을 고칠 수 있다.** 배열에는 "수정 불가 뷰"가 없다.
- 돌려줄 때마다 복사본을 만들면 안전하지만 **비용이 든다.**
- `List.of(...)` 로 돌려주면 수정 시도가 `UnsupportedOperationException` 으로 막힌다.

**`public static final int[] PRIMES` 가 상수가 못 되는 이유**

```text
겉보기 — 상수처럼 읽힌다                     실제 — 누구나 고칠 수 있다
+-------------------------------+          +-------------------------------+
| public static final           |          | Other.PRIMES[0] = 999;        |
|   int[] PRIMES = {2, 3, 5};   |          |   -> 컴파일도 되고 실행도 된다 |
+-------------------------------+          +-------------------------------+
```

- `final` 은 **쪽지를 코팅할 뿐 창고를 잠그지 않는다** — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 4번이 정본이다.
- 방어는 `private` 로 두고 `clone()` 을 돌려주는 메서드뿐이다.

**기본형 대량 데이터에서 배열이 유리한 이유**

- **박싱이 없다.** `int[1_000_000]` 은 객체 하나지만 `List<Integer>` 는 원소마다 `Integer` 객체가 필요하다.
- 메모리가 연속이라 순회 시 캐시 지역성이 좋다(1차원 기준).
- 그래서 `ArrayList` 자신도 **내부는 배열**이다.\
  *(구체적인 속도·메모리 수치는 이 문서에서 측정하지 않았다.)*

### 11. 다른 주제와 잇기

**`Arrays.asList(int[])` 함정의 뿌리**

- `Arrays.asList` 의 시그니처는 `static <T> List<T> asList(T... a)` 다.
- **`T` 는 참조 타입만** 될 수 있다 — 제네릭 타입 인자에 기본형을 쓸 수 없기 때문이다.
- `int` 가 `T` 가 못 되니 컴파일러는 **`int[]` 전체를 `T` 하나로** 잡는다. 그래서 원소가 하나다.
- 같은 규칙이 `List<int>` 가 안 되는 이유이고, 그래서 래퍼가 필요하다 — [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) 가 정본이다.

**원소 변경은 보이고 재대입은 안 보이는 이유**

**출력** (`Ex.java (03-a)`)

```text
(F) 배열 원소     arr[0] = 99
(G) 배열 재대입   arr[0] = 99
```

- (F)는 `a[0] = 99` 로 **창고 안을 고쳤다** — 보인다.
- (G)는 `a = new int[]{7,7,7}` 로 **복사된 쪽지를 고쳤다** — 안 보인다(그래서 여전히 99다).
- 배열도 객체이므로 값 전달 규칙이 그대로 적용된다 — [`../03-variables-and-assignment/`](../03-variables-and-assignment/) 가 정본이다.

**`new List<String>[3]` 이 왜 금지인가**

```text
Ex.java:5: error: generic array creation
        List<String>[] a = new List<String>[3];
                           ^
1 error
```

- 배열은 런타임에 **자기 원소 타입을 알고 있어야** `aastore` 검사를 할 수 있다.
- 그런데 제네릭은 **타입 소거**로 런타임에 타입 인자가 사라진다 — `List<String>` 과 `List<Integer>` 가 구분되지 않는다.
- 만들게 뒀다면 공변성과 결합해 **검사가 아무것도 못 잡는 배열**이 생긴다. 그래서 언어가 막았다.
- 정본은 목록의 **19번 주제**(타입 소거)다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (05-a)` | 배열의 클래스·상속·인터페이스, 기본값 여섯, 다차원·비정방, 길이 0 | 17 · 21 · 25 (`toString` 의 16진수만 다름) |
| `Ex.java (05-b)` | 공변 대입 통과, `ArrayStoreException` 넷(직접·상속·메서드 안·uncaught), `int[]` 은 `Object` | 17 · 21 · 25 (동일) |
| `Ex.java (05-c1)` `javac` | `List<String>` -> `List<Object>` 대입 컴파일 에러 | 21 |
| `Ex.java (05-c2)` `javac` | `new List<String>[3]` -> `generic array creation` | 21 |
| `Ex.java (05-d)` | `equals`/`deepEquals`, `toString`/`deepToString`, `asList` 함정 셋, 복사 넷, `sort`/`binarySearch`/`fill`/`compare`/`mismatch` | 17 · 21 · 25 (`Arrays.hashCode(int[][])` 값만 다름) |
| `Ex.java (05-e)` | AIOOBE(읽기·쓰기·음수), `NegativeArraySizeException`, 배열 NPE 셋, `arraycopy` 예외 둘, 스택트레이스 | 17 · 21 · 25 (동일) |
| `Ex.java (05-f)` | NPE 메시지가 `javac -g` 와 `-XX:-ShowCodeDetailsInExceptionMessages` 에 따라 갈림 | 17 · 21 · 25 (조건별로 동일) |
| `Ex.java (05-g)` `javap -c -p` | `newarray`/`anewarray`/`multianewarray`, `aastore` 대 `iastore`, `arraylength` | 21 |
| `Ex.java (05-h)` | `asList` 뷰에서 `ArrayStoreException`, `toArray` 두 형태의 런타임 타입 | 17 · 21 · 25 (동일) |
| `Ex.java (05-i)` | `Arrays.hashCode` 대 `deepHashCode`, 배열이 `HashMap` 키가 못 되는 것 | 17 · 21 · 25 (`deepHashCode` 32833 동일) |
| `Ex.java (05-j)` | 배열 길이 상한 — `Integer.MAX_VALUE` 는 `Requested array size exceeds VM limit`, `-2` 는 `Java heap space` | 17 · 21 · 25 (동일, `-Xmx512m`) |
| `src.zip` 열람 | `Arrays.asList` javadoc, `deepEquals`/`deepToString`/`copyOf`/`compare`/`mismatch` 의 `@since` | 21 |

**구현 의존 항목** — `Arrays$ArrayList`·`ImmutableCollections$List12` 라는 클래스 이름, `ArrayStoreException`·`AIOOBE` 의 메시지 형식, `Arrays.hashCode(int[][])` 의 값, NPE 메시지 문구는 **전부 구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 이 표의 **`(05-e)`·`(05-f)`·`(05-i)`** 셋이다 — 메시지와 해시값이 걸려 있다.\
반면 공변성·`ArrayStoreException` 발생 조건·기본값·배열이 `Object` 를 상속한다는 것은 JLS 가 보장한다.
