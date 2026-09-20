# java/syntax/05 — 배열: 생성·기본값·공변성·`Arrays` 유틸 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §10 Arrays](https://docs.oracle.com/javase/specs/jls/se21/html/jls-10.html) · [§4.10.3 Subtyping among Array Types](https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html) · [`java.util.Arrays` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/Arrays.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/util/Arrays.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (05-a)` `(05-d)` `(05-e)` `(05-h)` `(05-i)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 돌렸다.\
> 세 JDK 에서 **달라진 것은 `Object.toString` 의 16진수와 `Arrays.hashCode(int[][])` 값뿐**이고(둘 다 identity hash 기반), 나머지는 같았다.\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — 배열 자체는 Java 1.0. `Arrays.deepEquals`/`deepToString` 은 **5**, `Arrays.copyOf`/`copyOfRange` 는 **6**, `Arrays.compare`/`mismatch` 는 **9** 부터다(`src.zip` 의 `@since` 를 직접 읽었다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·javadoc 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**배열은 "칸 수가 적힌 채 봉인된 사물함 줄"이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 사물함 줄 | 배열 객체 (힙에 있는 객체 하나) |
| 줄에 박힌 칸 수 팻말 | `length` 필드 — 만들 때 정해지고 못 바꾼다 |
| 칸 하나 | 원소 하나 |
| 줄 입구에 적힌 "여기는 `String` 전용" | **런타임 원소 타입** — 배열이 자기 안에 들고 있다 |
| 입구 경비원 | 저장할 때마다 타입을 검사하는 `aastore` 명령 |
| 줄 전체를 가리키는 쪽지 | 배열 참조 |

- 사물함 줄은 **만들 때 칸 수가 정해지고 절대 안 늘어난다.**\
  늘리려면 더 긴 줄을 새로 만들어 옮겨 담아야 한다 — 그게 `Arrays.copyOf` 다.
- 새로 만든 줄의 칸은 **비어 있지 않다.** 숫자 줄이면 0, `boolean` 줄이면 `false`, 객체 줄이면 `null` 이 미리 들어 있다.
- **입구에 "여기는 `String` 전용"이라고 적혀 있다.**\
  그런데 자바는 그 줄을 "아무거나 넣는 줄"이라고 **부르는 것만은 허락한다.**\
  부르는 것은 허락하고 **넣을 때 경비원이 막는다** — 이것이 공변성이 런타임 예외로 새는 경로다.

```text
String[] strings = new String[3];
Object[] objects = strings;            <- 부르는 것은 통과 (컴파일 OK)

  strings ---+
             +---> +-----------------------------+
  objects ---+     | 입구 팻말: String 전용       |
                   | [0] [1] [2]   length = 3    |
                   +-----------------------------+

objects[0] = "문자열";        -> 경비원 통과
objects[1] = Integer.valueOf(42);
                              -> 경비원이 막는다
                              -> java.lang.ArrayStoreException: java.lang.Integer
```

**똑같은 구조로** 자바가 동작한다: 사물함 줄 = 배열 객체, 팻말 = `length`, 경비원 = `aastore` 의 런타임 검사.

실무에서 이게 터지는 자리는 **`Object[]` 나 상위 타입 배열을 받는 유틸 메서드**다.\
호출부는 컴파일 경고 하나 없이 통과하고, 유틸이 값을 채워 넣는 순간 운영에서 `ArrayStoreException` 이 난다.

> **공변성(covariance)** — `S` 가 `T` 의 하위 타입이면 `S[]` 도 `T[]` 의 하위 타입으로 취급하는 규칙(JLS §4.10.3).\
> 예: `String` 이 `Object` 의 하위 타입이므로 `String[]` 을 `Object[]` 변수에 대입할 수 있다.

> **런타임 원소 타입(runtime component type)** — 배열 객체가 실제로 들고 있는 "이 줄에 넣을 수 있는 타입".\
> 예: `Object[] objects = new String[3];` 에서 정적 타입은 `Object[]` 지만 런타임 원소 타입은 `String` 이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 배열은 객체인가 아닌가 — 그렇다면 **어떤 클래스의 인스턴스이고 무엇을 상속하는가.**
2. 공변성은 **어느 검사를 컴파일에서 런타임으로 미뤘고**, 제네릭은 왜 그러지 않는가.
3. `Arrays` 유틸의 이름이 비슷한 짝들(`equals`/`deepEquals`, `toString`/`deepToString`)은 **무엇이 다르고 언제 갈리는가.**

## 동작 방식

### (1) 배열은 객체다 — 그런데 소스에 클래스가 없다

**언제 쓰나** — 배열에 `.` 을 찍는 모든 자리. `length`·`clone()`·`getClass()`.

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

```text
      Object
        |
   상속 (JLS §10.8)
        |
   +----+----+----+
   |         |    |
  int[]  String[] ...        <- 소스에 선언문이 없는, JVM 이 만들어 주는 클래스
   |
   구현: Cloneable, Serializable
   멤버: public final int length
         public Object clone()
         Object 에서 물려받은 것 전부
```

그림 해설 (한 단계씩):

- 배열 타입은 **JVM 이 만들어 주는 클래스**다. `int[].java` 같은 소스 파일은 없다.
- 그래서 `getName()` 이 `[I` 처럼 **내부 표기**로 나온다(`[` = 배열 한 겹, `I` = `int`).\
  `String[]` 은 `[Ljava.lang.String;`, `int[][]` 은 `[[I` 다.
- `Object` 를 상속하므로 `equals`·`hashCode`·`toString` 이 **재정의되지 않은 채** 있다.\
  그래서 `arr.equals(other)` 는 참조 비교이고 `arr.toString()` 은 `[I@29453f44` 다.
- `length` 는 **메서드가 아니라 필드**다. 괄호를 붙이면 컴파일 에러다.

비용 — 배열 생성은 `length` 에 비례(메모리를 0으로 밀어야 한다). `length` 읽기는 명령 하나(`arraylength`).

### (2) 기본값 — 새 배열은 비어 있지 않다

**언제 쓰나** — `new T[n]` 을 쓰는 모든 자리.

**출력** (`Ex.java (05-a)`)

```text
int[]     기본값 = [0, 0]
long[]    기본값 = [0, 0]
double[]  기본값 = [0.0, 0.0]
boolean[] 기본값 = [false, false]
char[]    기본값 = 0 (숫자로 찍은 것)
String[]  기본값 = [null, null]
```

```text
new int[3]                        new String[3]

+-----+-----+-----+               +------+------+------+
|  0  |  0  |  0  |               | null | null | null |
+-----+-----+-----+               +------+------+------+
  쓸 준비가 끝난 상태               "아직 안 채웠다"가 null 로 표현된다
```

그림 해설 (한 단계씩):

- 기본형 배열은 **0(또는 `false`)으로 채워진 상태로 나온다.** 따로 초기화할 필요가 없다.
- 참조 배열은 `null` 로 채워진다 — **객체가 만들어지지는 않는다.**\
  `new Point[3]` 은 `Point` 객체 셋이 아니라 **빈 칸 셋**이다.
- 이 규칙은 필드의 기본값 규칙과 같다([`../03-variables-and-assignment/`](../03-variables-and-assignment/) 9번).\
  지역 변수만 확정 대입 검사를 받고, **배열 원소는 안 받는다.**

비용 — `new` 시점에 `length` 칸을 전부 0으로 미는 비용. 큰 배열이면 이것이 실제 비용이다.

### (3) 다차원 배열은 "배열의 배열"이다

**언제 쓰나** — 격자·행렬·인접 리스트.

**출력** (`Ex.java (05-a)`)

```text
int[][] 의 원소    = [I
m                 = [[I@6e0be858, [I@61bbe9ba]
m (deep)          = [[0, 0, 0], [0, 0, 0]]
비정방            = [[1], [1, 2], [1, 2, 3]]
안쪽 미할당        = [null, null]
```

```text
int[][] m = new int[2][3];

  m ---> +----------+----------+
         | 참조 #A  | 참조 #B  |     <- 바깥 배열의 원소는 "안쪽 배열 참조"다
         +----------+----------+
              |          |
              v          v
        +---+---+---+  +---+---+---+
        | 0 | 0 | 0 |  | 0 | 0 | 0 |
        +---+---+---+  +---+---+---+

int[][] jag = new int[3][];      <- 안쪽을 안 만든다

  jag --> +------+------+------+
          | null | null | null |
          +------+------+------+
```

그림 해설 (한 단계씩):

- 자바에 **진짜 2차원 배열은 없다.** `int[][]` 의 원소 타입은 `int[]` 다(출력의 `[I`).
- 그래서 **행마다 길이가 달라도 된다**(비정방 배열).
- `new int[3][]` 은 안쪽을 만들지 않는다 — 원소가 `null` 이다. 그대로 `jag[0][0]` 을 하면 NPE 다.
- 메모리도 연속이 아니다. 안쪽 배열 셋이 힙 어디에 있든 상관없다.

비용 — 행 접근마다 **참조 한 번 더 따라가기**(포인터 추적). 캐시 지역성은 1차원보다 나쁘다.\
자료구조로서의 배열(증폭·상환 분석)은 [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) 가 정본이다.

### (4) 공변성 — 컴파일러가 통과시키고 경비원이 막는다

**언제 쓰나** — 배열을 상위 타입으로 받는 모든 자리. `Object[]` 파라미터가 대표적이다.

**출력** (`Ex.java (05-b)`, 17·21·25 에서 동일)

```text
대입 통과. objects.getClass() = [Ljava.lang.String;
String 저장 성공: 문자열은 들어간다
catch  : java.lang.ArrayStoreException: java.lang.Integer
message: java.lang.Integer
Integer[] 에 Integer 저장 성공
Number[] 인 척하는 Integer[] 에 Double -> java.lang.ArrayStoreException: java.lang.Double
메서드 안에서 터짐 -> java.lang.ArrayStoreException: java.lang.Integer
```

잡지 않으면 이렇게 죽는다.

```text
Exception in thread "main" java.lang.ArrayStoreException: java.lang.Integer
	at Ex.main(Ex.java:45)
```

```text
검사가 어디로 밀렸나

  컴파일 타임                          런타임
  +----------------------------+      +----------------------------+
  | Object[] o = stringArray;  |      | o[1] = Integer.valueOf(42);|
  |   정적 타입만 본다           |      |   배열의 런타임 원소 타입과 |
  |   Object[] <- String[]     |      |   넣는 값의 타입을 비교한다  |
  |   공변이니 OK               |      |   String 전용인데 Integer  |
  |                            |      |   -> ArrayStoreException   |
  +----------------------------+      +----------------------------+
      경고 하나 없다                        여기서 처음 터진다
```

그림 해설 (한 단계씩):

- **대입은 통과한다.** 공변성이 JLS §4.10.3 에 명시된 규칙이기 때문이다.
- **저장할 때 검사한다.** 배열 객체가 자기 원소 타입을 들고 있으므로 런타임에 비교할 수 있다.
- 검사 주체는 **`aastore` 명령**이다 — `javap` 로 확인했다(아래 (5)).
- 예외 메시지는 **넣으려던 값의 타입 이름 하나**뿐이다(`java.lang.Integer`).\
  배열이 무슨 타입이었는지, 어느 인덱스였는지는 **안 알려 준다.** 그래서 원인 추적이 어렵다.

비용 — **참조 배열에 값을 넣을 때마다 타입 검사 1회.** 기본형 배열에는 이 비용이 없다.

### (5) 그 경비원의 정체 — `aastore` 대 `iastore`

**언제 쓰나** — "왜 `int[]` 에는 이 문제가 없나"를 판단할 때.

**`javap -c -p Ex.class` 출력 그대로** (`Ex.java (05-g)`, JDK 21.0.5)

```text
  static int[] prim();                     static java.lang.String[] ref();
    Code:                                    Code:
       0: iconst_3                              0: iconst_3
       1: newarray       int                    1: anewarray     #7   // class java/lang/String
       3: areturn                               4: areturn

  static void store(java.lang.Object[], java.lang.Object);
    Code:
       0: aload_0
       1: iconst_0
       2: aload_1
       3: aastore              <- 여기서 런타임 타입 검사가 일어난다
       4: return

  static int read(int[], int);             static int len(int[]);
    Code:                                    Code:
       0: aload_0                               0: aload_0
       1: iload_1                               1: arraylength
       2: iaload                                2: ireturn
       3: ireturn
```

그림 해설 (한 단계씩):

- 기본형 배열 생성은 `newarray`, 참조 배열 생성은 `anewarray` — **명령 자체가 다르다.**
- 저장도 다르다: 참조는 `aastore`, `int` 는 `iastore`.
- **`aastore` 만 타입 검사를 한다.** `iastore` 는 검사할 것이 없다 — `int[]` 에는 `int` 밖에 못 넣는다.
- 그래서 **공변성 문제는 참조 배열에만 있다.**\
  `int[]` 은 애초에 `Object[]` 의 하위 타입이 아니고, `Object` 의 하위 타입일 뿐이다(출력: `int[] 를 Object 로는 받는다: true`).

다차원 생성은 또 다른 명령이다.

```text
  static int[][] two();                    static int[][] jagged();
    Code:                                    Code:
       0: iconst_2                              0: iconst_2
       1: iconst_3                              1: anewarray     #11  // class "[I"
       2: multianewarray #9,  2                 4: areturn
       6: areturn
```

- `new int[2][3]` 은 `multianewarray` 하나로 **안쪽까지 한 번에** 만든다.
- `new int[2][]` 는 그냥 `anewarray "[I"` 다 — **`int[]` 을 원소로 갖는 배열**을 만들 뿐이고 안쪽은 `null` 이다.

비용 — 생성 명령 하나. 저장 시 `aastore` 만 추가 검사.

### (6) 제네릭과의 대비 — 같은 실수를 컴파일에서 잡는다

**언제 쓰나** — "배열 대신 `List` 를 쓰라"는 조언의 근거를 판단할 때.

전/후를 나란히 놓으면 이렇게 된다.

```text
배열 (공변) — 런타임에 터진다                제네릭 (불공변) — 컴파일에서 막힌다
+-----------------------------------+      +-----------------------------------+
| String[] s = new String[3];       |      | List<String> s = new ArrayList<>();|
| Object[] o = s;          // OK    |      | List<Object> o = s;      // 에러   |
| o[0] = 42;               // 런타임 |      |                                   |
|                                   |      | error: incompatible types:        |
| ArrayStoreException               |      |   List<String> cannot be          |
|   at Ex.main(Ex.java:45)          |      |   converted to List<Object>       |
+-----------------------------------+      +-----------------------------------+
  테스트에서 안 걸리면 운영에서 터진다         컴파일이 안 되므로 배포가 안 된다
```

그림 해설 (한 단계씩):

- 두 코드가 **하려는 일은 똑같다.** 다른 것은 **언제 막히느냐**뿐이다.
- 제네릭은 **불공변**(invariant)이라 `List<String>` 을 `List<Object>` 에 못 넣는다.
- 그 대신 제네릭에는 **와일드카드**가 있다 — `List<? extends Object>` 로 받으면 읽기는 되고 쓰기가 막힌다([**18번 주제**](../18-wildcards-pecs/)).
- 왜 배열만 공변으로 만들었나: **제네릭이 없던 Java 1.0 에서 `Arrays.sort(Object[])` 같은 범용 메서드를 쓰려면** 공변성이 필요했다.\
  제네릭이 들어온 뒤에도 배열의 규칙은 호환성 때문에 그대로다.

제네릭 배열을 만들려 하면 또 다른 에러가 난다(`Ex.java (05-c2)`).

```text
Ex.java:5: error: generic array creation
        List<String>[] a = new List<String>[3];
                           ^
1 error
```

- 이유는 타입 소거다 — 배열은 런타임에 원소 타입을 알아야 하는데 제네릭은 그때 그 정보가 없다.\
  타입 소거 자체는 [**19번 주제**](../19-type-erasure/)가 정본이다.

비용 — 없다. 설계 판단이다.

> **불공변(invariant)** — `S` 가 `T` 의 하위 타입이어도 `G<S>` 와 `G<T>` 사이에 하위 타입 관계가 없는 것.\
> 예: `String` 이 `Object` 의 하위 타입이지만 `List<String>` 은 `List<Object>` 의 하위 타입이 아니다.

### (7) `Arrays` 의 "deep" 짝 — 한 겹인가 끝까지인가

**언제 쓰나** — 다차원 배열을 비교하거나 찍을 때. 1차원에서는 차이가 없어서 **2차원이 되는 순간 조용히 틀린다.**

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

```text
int[][] p = {{1,2},{3,4}};   int[][] q = {{1,2},{3,4}};

Arrays.equals(p, q)                      Arrays.deepEquals(p, q)
+-------------------------------+        +-------------------------------+
| 바깥 원소를 == 로 비교한다      |        | 원소가 배열이면 재귀로 들어간다 |
|   p[0] == q[0] ?  (참조)      |        |   p[0] 과 q[0] 의 내용 비교    |
|   -> 다른 객체 -> false       |        |   1==1, 2==2 -> true          |
+-------------------------------+        +-------------------------------+
```

그림 해설 (한 단계씩):

- `Arrays.equals` 는 **한 겹만** 본다. 원소가 참조면 원소의 `equals` 를 부르는데, 배열의 `equals` 는 참조 비교다.
- `Arrays.deepEquals` 는 원소가 배열이면 **재귀로 내려간다.**
- `Arrays.toString` 도 같다 — 원소가 배열이면 `[I@...` 이 그대로 찍힌다.
- **1차원에서는 둘이 같은 답을 내므로** 2차원으로 바꾸는 순간 조용히 틀린다.

해시도 같은 짝이 있다(`Ex.java (05-i)`, 17·21·25 동일).

```text
Arrays.hashCode(p)==Arrays.hashCode(q) = false
Arrays.deepHashCode(p)==deepHashCode(q) = true
deepHashCode 값 = 32833
1차원 Arrays.hashCode 일치 = true / 값 = 30817
f1.hashCode()==f2.hashCode() = false
```

- `Arrays.hashCode(int[][])` 는 안쪽 배열의 **identity hash** 를 쓰므로 내용이 같아도 값이 다르다.\
  그 값은 JDK 마다 달랐다(17·21·25 에서 각각 다른 수) — **identity hash 기반이라 의존하면 안 되는 값**이다.
- `deepHashCode` 는 내용 기반이라 세 JDK 에서 `32833` 으로 같았다.
- 배열을 `HashMap` 키로 쓰면 안 되는 이유가 마지막 줄이다 — `f1.hashCode() != f2.hashCode()`.\
  `equals`/`hashCode` 계약 자체는 [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) 가 정본이다.

비용 — `deep*` 은 전체 원소 수에 비례. 순환 참조는 `deepToString` 이 `[...]` 로 끊는다.

### (8) 복사 — 네 가지 수단과 그 얕음

**언제 쓰나** — 배열을 늘리거나, 일부를 떼거나, 방어적 복사본을 만들 때.

**출력** (`Ex.java (05-d)`)

```text
arraycopy(src,1,dst,0,3) = [2, 3, 4, 0, 0]
copyOf(src, 3)      = [1, 2, 3]
copyOf(src, 8)      = [1, 2, 3, 4, 5, 0, 0, 0]
copyOfRange(src,1,4)= [2, 3, 4]
clone 내용 동일      = true / 같은 객체 = false
얕은 복사 후 원본    = [[99, 2], [3, 4]]
바깥은 다른 객체     = false / 안쪽은 같은 객체 = true
```

```text
src = [1, 2, 3, 4, 5]

System.arraycopy(src, 1, dst, 0, 3)      Arrays.copyOf(src, 8)
  기존 배열에 "쏟아붓는다"                  새 배열을 "만들어 준다"
  dst 가 이미 있어야 한다                   길이가 길면 뒤를 기본값으로 채운다
  +---+---+---+---+---+                   +---+---+---+---+---+---+---+---+
  | 2 | 3 | 4 | 0 | 0 |                   | 1 | 2 | 3 | 4 | 5 | 0 | 0 | 0 |
  +---+---+---+---+---+                   +---+---+---+---+---+---+---+---+
```

```text
clone 은 한 겹만 복사한다

  deep    ---> [ #A , #B ]           shallow ---> [ #A , #B ]
                 |    |                             |    |
                 +----+------ 같은 안쪽 배열 -------+----+
                      v
              [99, 2]   <- shallow[0][0] = 99 를 하면 deep 에도 보인다
```

그림 해설 (한 단계씩):

- `System.arraycopy` 는 **목적지 배열이 이미 있어야 한다.** 가장 저수준이고 `ArrayList` 내부가 이것을 쓴다.
- `Arrays.copyOf` 는 **새 배열을 만들어 돌려준다.** 길이를 줄이면 자르고, 늘리면 기본값으로 채운다.
- `Arrays.copyOfRange(a, from, to)` 는 `to` 가 **배타적**이다(`[from, to)`).
- `clone()` 은 같은 길이의 새 배열 — 그러나 **한 겹만** 복사한다.\
  다차원 배열의 방어적 복사에는 부족하다. 안쪽까지 복사하려면 직접 돌아야 한다.

비용 — 전부 `O(복사 길이)`. `System.arraycopy` 는 네이티브 메서드라 루프보다 빠른 경우가 많지만, **그 수치는 이 문서에서 측정하지 않았다.**

### (9) `Arrays.asList` — 세 개의 함정이 한 메서드에

**언제 쓰나** — 배열을 리스트로 바꿔 쓰고 싶을 때. 거의 매번 함정 중 하나를 밟는다.

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

**함정 1 — `int[]` 을 넘기면 원소가 하나가 된다**

```text
Arrays.asList(T... a) 의 시그니처를 기억하라

  Integer[] 를 넘기면                     int[] 을 넘기면
  +----------------------------+         +----------------------------+
  | T = Integer                |         | T = int[]  (int 는 T 가    |
  | 가변 인자 셋으로 풀린다      |         |   못 되므로 배열 통째로)    |
  | size = 3                   |         | size = 1                   |
  | [1, 2, 3]                  |         | [ int[] 객체 하나 ]         |
  +----------------------------+         +----------------------------+
```

- `T` 는 **참조 타입만** 될 수 있다. `int` 는 못 되므로 컴파일러가 `int[]` 자체를 `T` 로 잡는다.
- 결과는 **원소 하나짜리 `List<int[]>`** 다. 에러가 안 난다 — `size()` 를 찍어 보기 전에는 모른다.
- 고치려면 `Arrays.stream(prim).boxed().toList()` 를 쓴다.

**함정 2 — 고정 크기다**

```text
Arrays.asList 로 만든 리스트

  set(i, v)     -> 된다   (배열의 칸을 바꾸는 것)
  add(v)        -> UnsupportedOperationException
  remove(i)     -> UnsupportedOperationException
```

- javadoc 이 그대로 못박는다 — "Returns a **fixed-size** list backed by the specified array."\
  그리고 "The returned list implements the optional `Collection` methods, **except those that would change the size**."
- 예외 메시지가 **`null`** 이라 로그만 보면 원인을 알 수 없다. 스택트레이스의 `Arrays$ArrayList` 를 봐야 한다.

**함정 3 — 원본 배열과 연결돼 있다**

```text
String[] backing = {"x", "y"};
List<String> view = Arrays.asList(backing);

  backing[0] = "CHANGED"   ->  view  == [CHANGED, y]
  view.set(1, "SET")       ->  backing == [CHANGED, SET]
```

- javadoc: "Changes made to the array will be visible in the returned list, and changes made to the list will be visible in the array."
- **뷰**다. 복사가 아니다. 방어적 복사로 착각해 쓰면 그대로 새어 나간다.

셋 다 피하려면 **`List.of(...)`** 를 쓴다 — 크기 고정 + 수정 전면 금지 + 원본과 분리.\
단 `List.of` 는 `null` 원소를 허용하지 않는다. 둘의 차이는 [**40번 주제**](../40-list-set-and-immutable-factories/)가 정본이다.

비용 — `asList` 는 배열을 감싸기만 하므로 O(1). `List.of` 는 원소를 복사하므로 O(n).

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 선언과 생성의 형태

```java
int[] a;                 // 권장 — 타입에 붙인다
int b[];                 // 된다 — C 스타일. 읽기 나쁘다
int[] c = new int[3];    // 길이만 주고 기본값으로
int[] d = {1, 2, 3};     // 선언과 동시에만 쓸 수 있는 축약형
int[] e = new int[]{1, 2, 3};   // 어디서든 쓸 수 있는 형태
int[][] f = new int[2][3];      // 안쪽까지
int[][] g = new int[2][];       // 바깥만 — 안쪽은 null
int[] h = new int[0];           // 길이 0 — 정상이다. null 대신 쓴다
```

- `int[] d = {1, 2, 3};` 는 **선언문에서만** 쓸 수 있다. `d = {1,2,3};` 는 컴파일 에러다.
- **길이 0 배열은 `null` 의 좋은 대안**이다. 호출자가 `null` 검사를 안 해도 된다.\
  `List.toArray(new String[0])` 관용구가 이것을 쓴다.

### 배열이 가진 멤버 전부

| 멤버 | 정체 | 비고 |
|---|---|---|
| `length` | `public final int` **필드** | `length()` 가 아니다 |
| `clone()` | `public` 메서드 | 반환 타입이 그 배열 타입으로 공변 |
| `equals`/`hashCode`/`toString` | `Object` 의 것 그대로 | 재정의 안 됨 — 참조 기반 |
| `getClass()` | `Object` 의 것 | `isArray()` 가 `true` |

그 밖에는 없다. `sort`·`contains` 같은 것은 **전부 `Arrays` 의 정적 메서드**다.

### 자주 쓰는 `Arrays` 메서드

| 메서드 | 하는 일 | `@since` |
|---|---|---|
| `toString` / `deepToString` | 한 겹 / 끝까지 문자열화 | 1.5(deep) |
| `equals` / `deepEquals` | 한 겹 / 끝까지 비교 | 1.5(deep) |
| `hashCode` / `deepHashCode` | 한 겹 / 끝까지 해시 | 1.5(deep) |
| `copyOf` / `copyOfRange` | 새 배열로 복사 (뒤는 기본값) | 1.6 |
| `sort` / `binarySearch` | 정렬 / 정렬된 배열 탐색 | 1.2 |
| `fill` | 전부 한 값으로 | 1.2 |
| `stream` | 스트림으로 | 1.8 |
| `compare` / `mismatch` | 사전식 비교 / 첫 불일치 위치 | 9 |

`@since` 는 `lib/src.zip` 의 `Arrays.java` 를 직접 읽어 확인한 값이다.

**출력** (`Ex.java (05-d)`)

```text
sort                = [1, 2, 3, 4, 5]
binarySearch(4)     = 3
binarySearch(10)    = -6
fill                = [7, 7, 7, 7, 7]
stream().sum()      = 15
compare             = -1
mismatch            = 1
```

- `binarySearch` 가 못 찾으면 **`-(삽입 위치) - 1`** 을 돌려준다. `10` 은 끝(인덱스 5)에 들어가므로 `-6`.
- `binarySearch` 는 **정렬돼 있어야** 의미가 있다. 아니면 결과가 정의되지 않는다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 다 **컴파일은 통과한다.**

### 1. 공변성을 믿고 `Object[]` 파라미터를 만든다

```java
static void fill(Object[] a) { a[2] = 123; }
// 호출: fill(new String[3]);
```

**출력** (`Ex.java (05-b)`)

```text
메서드 안에서 터짐 -> java.lang.ArrayStoreException: java.lang.Integer
```

- **호출부에는 경고가 없다.** `String[]` 을 `Object[]` 에 넘기는 것은 합법이다.
- 터지는 곳은 유틸 안쪽이라 **스택트레이스가 호출자 코드를 가리키지 않는다.**
- 방어는 제네릭 메서드(`<T> void fill(T[] a, T v)`) 또는 `List<T>` 다.

### 2. `Arrays.equals` 로 2차원을 비교한다

```text
1차원                                       2차원
+-------------------------------+          +-------------------------------+
| int[] a = {1,2}, b = {1,2};   |          | int[][] p = {{1,2}};          |
| Arrays.equals(a, b) -> true   |          | int[][] q = {{1,2}};          |
| 기대대로 동작한다              |          | Arrays.equals(p, q) -> false  |
|                               |          | 에러 없이 틀린 답             |
+-------------------------------+          +-------------------------------+
```

- **1차원에서 잘 돌던 코드가 차원이 늘면 조용히 틀린다.**
- 테스트 데이터가 1차원이면 초록인 채로 배포된다.

### 3. `Arrays.asList(intArray)` 를 쓴다

```text
asList(int[]) size   = 1
asList(int[]) 원소0  = [I
```

- **에러가 없다.** `size()` 가 1이라는 것을 확인하기 전에는 모른다.
- 뒤이은 `stream()`·`forEach` 가 전부 "원소 하나"에 대해 돌아간다.
- `Integer[]` 를 넘기면 3이 된다 — **박싱 여부 하나로 결과가 갈린다.**

### 4. `clone()` 으로 다차원 배열을 방어한다

```text
얕은 복사 후 원본    = [[99, 2], [3, 4]]
바깥은 다른 객체     = false / 안쪽은 같은 객체 = true
```

- `shallow[0][0] = 99` 가 **원본 `deep` 에 보인다.**
- "복사했으니 안전하다"는 착각이 여기서 깨진다.
- 깊은 복사는 직접 돌아야 한다.

```java
int[][] deepCopy = new int[src.length][];
for (int i = 0; i < src.length; i++) deepCopy[i] = src[i].clone();
```

### 5. 인덱스·길이 예외의 메시지를 잘못 읽는다

**출력** (`Ex.java (05-e)`, 17·21·25 에서 **완전히 동일했다**)

```text
a[3]   -> java.lang.ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3
a[-1]  -> java.lang.ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3
a[5]=1 -> java.lang.ArrayIndexOutOfBoundsException: Index 5 out of bounds for length 3
AIOOBE 의 부모 = java.lang.IndexOutOfBoundsException
new int[-1] -> java.lang.NegativeArraySizeException: -1
new int[2][-3] -> java.lang.NegativeArraySizeException: -3
arraycopy 초과 -> java.lang.ArrayIndexOutOfBoundsException: arraycopy: last destination index 3 out of bounds for int[2]
arraycopy 타입 -> java.lang.ArrayStoreException: arraycopy: type mismatch: can not copy int[] into object array[]
```

- **읽기와 쓰기가 같은 예외**다. `a[3]` 도 `a[5] = 1` 도 `ArrayIndexOutOfBoundsException` 이다.
- `new int[-1]` 은 **컴파일 에러가 아니다.** 런타임에 `NegativeArraySizeException` 이다.\
  길이를 계산해서 넘기는 코드(`new int[end - start]`)에서 실제로 난다.
- `System.arraycopy` 의 메시지는 **형태가 다르다** — `arraycopy:` 접두어가 붙고 대상 배열 타입까지 알려 준다.

NPE 도 배열에서 형태가 여럿이다(`Ex.java (05-f)`, 아래 절에서 조건과 함께).

```text
Cannot load from int array because "nil" is null
Cannot read the array length because "nil" is null
Cannot store to int array because "outer[0]" is null
```

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| 배열이 `Object` 를 상속하고 `Cloneable`·`Serializable` 을 구현 | **JLS (언어 보장)** | JLS §10.8 |
| `S[]` 가 `T[]` 의 하위 타입 (공변) | **JLS (언어 보장)** | JLS §4.10.3 |
| 잘못된 저장이 `ArrayStoreException` | **JLS (언어 보장)** | JLS §10.10 |
| 새 배열이 기본값으로 초기화 | **JLS (언어 보장)** | JLS §10.3 |
| `asList` 가 고정 크기이고 원본과 연결됨 | **javadoc (API 계약)** | `Arrays.asList` javadoc |
| `asList` 의 구현 클래스가 `java.util.Arrays$ArrayList` | **구현 세부** | 관찰값. 계약이 아니다 |
| `List.of` 의 구현 클래스가 `ImmutableCollections$List12` | **구현 세부** | 원소 수에 따라 다른 클래스가 나온다 |
| `ArrayStoreException` 메시지가 타입 이름 하나 | **구현 세부** | 관찰값(17·21·25 동일) |
| `AIOOBE` 메시지의 `Index N out of bounds for length L` 형식 | **구현 세부** | 관찰값(17·21·25 동일) |
| `Arrays.hashCode(int[][])` 의 구체적 값 | **구현 세부** | identity hash 기반 — **JDK 마다 달랐다** |
| NPE 메시지에 변수 이름이 나오는 것 | **구현 세부 + 컴파일 옵션** | 아래 참조 |

### NPE 메시지는 버전이 아니라 **플래그**에 갈린다

`Ex.java (05-f)` 를 같은 소스로 세 JDK × 세 조건에서 돌렸다. **세 JDK 의 결과가 조건별로 완전히 같았다.**

```text
javac (기본, -g 없음)                     javac -g
[1] Cannot load from int array           [1] Cannot load from int array
    because "<local1>" is null               because "nil" is null
[2] Cannot read the array length         [2] Cannot read the array length
    because "<local1>" is null               because "nil" is null
[3] Cannot store to int array            [3] Cannot store to int array
    because "<local2>[0]" is null            because "outer[0]" is null

java -XX:-ShowCodeDetailsInExceptionMessages
[1] null
[2] null
[3] null
```

- **변수 이름이 나오려면 `javac -g`(또는 `-g:vars`)로 컴파일돼 있어야 한다.**\
  없으면 `<local1>` 처럼 슬롯 번호로 나온다. 빌드 설정에 따라 운영 로그의 모양이 달라진다.
- **JVM 플래그 하나로 메시지가 통째로 사라진다.** `-XX:-ShowCodeDetailsInExceptionMessages` 를 켜면 `getMessage()` 가 `null` 이다.
- 그러므로 **NPE 메시지의 문구에 의존하는 코드·테스트를 쓰면 안 된다.**\
  이 문서의 메시지도 "이 조건에서 이렇게 나왔다"는 관찰이다.

> **helpful NullPointerException** — NPE 메시지에 "어느 식이 `null` 이었는지"를 적어 주는 기능(JEP 358, Java 14. 15부터 기본 켜짐).\
> 예: `Cannot read the array length because "nil" is null`.

## 언제 쓰고 언제 안 쓰나

| 상황 | 배열 | `List` |
|---|---|---|
| 크기가 고정이고 기본형 대량 | **쓴다** (박싱 없음) | 원소마다 객체가 생긴다 |
| 크기가 변한다 | 매번 새로 만들어야 한다 | **쓴다** |
| 타입 안전이 중요하다 | 공변성이 런타임으로 샌다 | **쓴다** (컴파일에서 막힌다) |
| API 의 반환 타입 | 호출자가 고칠 수 있다 | **쓴다** (불변 리스트로) |
| 가변 인자(`T...`) | 배열로 구현된다 | — |
| 성능이 걸린 내부 구현 | **쓴다** — `ArrayList` 내부가 배열이다 | — |
| `HashMap` 의 키 | **못 쓴다** — 내용 기반 해시가 아니다 | 쓴다 (`List.of` 는 내용 기반) |

판단 규칙 두 줄.

- **바깥으로 내보내는 것은 `List`, 안에서 도는 것은 배열.**
- **배열을 노출해야 하면 복사본을 준다** — `clone()`(1차원) 또는 깊은 복사(다차원).

## 핵심 문장

- 배열은 **JVM 이 만들어 주는 클래스의 인스턴스**다. `Object` 를 상속하고 `length` 필드와 `clone()` 을 갖는다.
- 새 배열은 **비어 있지 않다** — 기본형은 0, 참조는 `null` 로 채워져 나온다.
- 공변성은 **대입을 컴파일에서 통과시키고 저장을 런타임에 검사한다.** 그 검사 주체가 `aastore` 이고, 실패가 `ArrayStoreException` 이다.
- 제네릭은 불공변이라 **같은 실수를 컴파일 에러로 잡는다** — 배열 대신 `List` 를 권하는 근거가 이것이다.
- `equals`/`toString`/`hashCode` 는 **한 겹만** 본다. 다차원이면 `deep*` 을 써야 하고, 1차원에서는 차이가 안 보여서 조용히 틀린다.
- `Arrays.asList` 는 **고정 크기 + 원본과 연결된 뷰 + `int[]` 을 넘기면 원소 하나**라는 함정 셋을 한꺼번에 갖고 있다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 05번)
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — **그쪽은 동적 배열이라는 자료구조(2배 증폭·상환 분석·`ArrayList` 의 내부)까지, 여기는 자바 배열의 언어 표면(공변성·기본값·`Arrays` 유틸)부터.**\
  "왜 2배씩 늘리나"는 그쪽, "`copyOf` 가 무엇을 하나"는 여기다
- [`../01-primitives-and-wrappers/`](../01-primitives-and-wrappers/) — `int[]` 과 `Integer[]` 의 차이. `asList(int[])` 함정의 뿌리가 "기본형은 타입 인자가 못 된다"는 규칙이다
- [`../03-variables-and-assignment/`](../03-variables-and-assignment/) — 배열이 객체라 **원소 변경은 호출자에게 보이고 재대입은 안 보인다.** `final` 배열 상수가 왜 안전하지 않은지도 그쪽
- [`../27-equals-hashcode-contract/`](../27-equals-hashcode-contract/) — 배열을 `HashMap` 키로 쓰면 안 되는 이유(계약을 재정의하지 않았다)
- [**17번 주제**](../17-generic-declarations/)(제네릭 선언)·**18번 주제**(와일드카드와 PECS) — **불공변과 와일드카드의 정본.** 여기서는 배열과의 대비까지만
- [**19번 주제**](../19-type-erasure/)(타입 소거) — `new List<String>[3]` 이 왜 금지인가의 정본
- [**40번 주제**](../40-list-set-and-immutable-factories/)(`List.of`·`copyOf`·`unmodifiable*`) — `asList` 의 대안과 "불변 대 수정 불가 뷰"의 정본
- [**43번 주제**](../43-iterator-and-fail-fast/)(`Iterator`·fail-fast) — 리스트 순회 중 수정. 배열에는 이 개념이 없다
- [`../44-stream-creation/`](../44-stream-creation/) — `Arrays.stream(int[])` 과 `Stream.of(T...)` 가 갈리는 자리

## 용어 풀이

- **배열(array)** — 같은 타입의 원소를 고정 개수만큼 담는 객체. 길이는 생성 시 정해지고 바뀌지 않는다.
- **원소 타입(component type)** — 배열 한 겹을 벗긴 타입. `int[][]` 의 원소 타입은 `int[]` 다.
- **공변성(covariance)** — 하위 타입 관계가 배열 타입에도 그대로 이어지는 규칙. `String[]` 은 `Object[]` 의 하위 타입이다.
- **불공변(invariant)** — 타입 인자가 달라지면 하위 타입 관계가 없는 것. 제네릭이 이쪽이다.
- **런타임 원소 타입** — 배열 객체가 실제로 들고 있는 "넣을 수 있는 타입". 정적 타입과 다를 수 있다.
- **`ArrayStoreException`** — 배열의 런타임 원소 타입과 맞지 않는 값을 저장할 때 던져지는 unchecked 예외.
- **`aastore` / `iastore`** — 참조 배열 / `int` 배열에 저장하는 JVM 명령. 앞의 것만 런타임 타입 검사를 한다.
- **`newarray` / `anewarray` / `multianewarray`** — 기본형 배열 / 참조 배열 / 다차원 배열을 만드는 JVM 명령.
- **비정방 배열(jagged array)** — 행마다 길이가 다른 다차원 배열. 자바의 다차원 배열이 "배열의 배열"이라 가능하다.
- **얕은 복사(shallow copy)** — 한 겹만 복사하고 안쪽 객체는 공유하는 복사. `clone()` 이 이것이다.
- **뷰(view)** — 원본을 감싸서 다른 인터페이스로 보여 주는 객체. 원본이 바뀌면 뷰에도 보인다. `Arrays.asList` 가 이것이다.
- **가변 인자(varargs)** — `T...` 형태의 파라미터. 호출부의 인자들이 배열로 묶여 전달된다.
- **helpful NullPointerException** — NPE 메시지에 어느 식이 `null` 이었는지 적어 주는 기능(Java 14 도입, 15부터 기본).

## 더 들어가면

- **`Arrays.asList` 의 javadoc 이 `ArrayStoreException` 을 직접 경고한다.**\
  "If the specified array's actual component type differs from the type parameter T, this can result in operations on the returned list throwing an `ArrayStoreException`."\
  실제로 확인했다(`Ex.java (05-h)`) — `Object[] backing = new String[]{...}` 를 감싼 리스트에 `set(0, Integer)` 를 하면 터진다.

```text
List.set 에서 -> java.lang.ArrayStoreException: java.lang.Integer
```

- **`toArray()` 와 `toArray(T[])` 의 런타임 타입이 다르다.**

```text
toArray() 의 런타임 타입 = [Ljava.lang.Object;
toArray(new String[0])   = [Ljava.lang.String;
```

  `List<String>.toArray()` 의 결과를 `String[]` 으로 캐스팅하면 `ClassCastException` 이 난다 — 런타임 타입이 `Object[]` 이기 때문이다.\
  `toArray(new String[0])` 을 쓰면 `String[]` 이 나온다.

- **`deepToString` 은 순환 참조를 끊는다.** 자기 자신을 원소로 가진 배열을 찍으면 `[...]` 로 표시하고 무한 재귀에 빠지지 않는다(javadoc 에 명시).
- **배열 길이의 상한은 `Integer.MAX_VALUE` 보다 작다.** 실행으로 확인했다(`Ex.java (05-j)`, `-Xmx512m`, 17·21·25 동일).

```text
new int[Integer.MAX_VALUE] -> java.lang.OutOfMemoryError: Requested array size exceeds VM limit
new int[Integer.MAX_VALUE - 2] -> java.lang.OutOfMemoryError: Java heap space
```

  **두 메시지가 다르다는 것이 요점이다.** 앞은 *VM 의 구조적 한계*에 걸린 것이고(힙을 아무리 늘려도 안 된다),\
  뒤는 *힙이 모자란* 것이다(더 주면 된다). 정확한 경계는 JVM·헤더 크기에 따라 달라지며 이 문서에서 좁히지 않았다.\
  그래서 `Arrays.copyOf` 로 계속 늘리는 코드는 언젠가 앞의 에러를 만난다 — `ArrayList` 가 최대 크기를 따로 두는 이유다.
