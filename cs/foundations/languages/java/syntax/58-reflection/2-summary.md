# java/syntax/58 — 리플렉션: `Class`·`getDeclared*`·접근 제어 우회의 경계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Java SE 21 `Class` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Class.html) · [`AccessibleObject.setAccessible`](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/AccessibleObject.html) · [JEP 396: Strongly Encapsulate JDK Internals by Default](https://openjdk.org/jeps/396) · [JEP 403: Strongly Encapsulate JDK Internals](https://openjdk.org/jeps/403).
> **실행 검증** — 이 문서의 모든 출력·예외는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> 프로그램 7개를 돌렸고, 그중 넷은 **17.0.13 · 21.0.5 · 25.0.1** 에서 전부 돌려 **출력이 같은 것을 확인**했다.\
> 모듈 경계 실험은 **플래그 없이 / `--add-opens` / `--add-exports`** 세 조건에서 각각 돌렸다.\
> `javap -v -p` 로 `Signature` 속성을 읽어 **19번(타입 소거)과 잇는 근거**로 썼다.
> **★ 측정 조건**(「동작 방식 (6)」) — **JMH 가 아니다.** `System.nanoTime()` 반복 측정이고,
> 머신은 13th Gen Intel Core i7-13700HX · 24 스레드 · Linux 7.0.0-31-generic 이다.\
> **재현되는 것은 절댓값이 아니라 자릿수(20~30배)다.** 웜업 전 회차를 함께 싣는다.
> **버전** — 리플렉션 자체는 **1.1**. 제네릭 정보(`getGenericType`·`ParameterizedType`)는 **5**,
> `InaccessibleObjectException` 과 모듈 경계는 **9**, **기본 강제 캡슐화는 16**(JEP 396)부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> 선행: [16 애너테이션](../16-annotations/) · [19 타입 소거](../19-type-erasure/).

## 한눈에 — 쉽게 말하면

**리플렉션은 "건물 설계도를 런타임에 펼쳐 보고, 그 설계도로 문을 여는 것"이다.**\
그리고 **Java 9 이후 남의 건물(JDK 모듈)은 설계도는 보여 줘도 문은 안 열어 준다** — 주인이 `opens` 해야 열린다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 설계도 한 장 | `Class<?>` 객체 — 타입 하나에 딱 하나 |
| 설계도를 꺼내는 세 가지 길 | `String.class` / `obj.getClass()` / `Class.forName("...")` |
| 설계도에 그려진 방·문 목록 | `getDeclaredFields()`·`getDeclaredMethods()`·`getDeclaredConstructors()` |
| 밖에서도 보이는 방만 적힌 목록 | `getFields()`·`getMethods()` — **public + 상속받은 것** |
| 잠긴 문을 여는 마스터키 | `setAccessible(true)` |
| 건물 주인이 "이 층은 열어 준다"고 선언하는 것 | 모듈의 `opens` — 없으면 마스터키가 안 먹는다 |
| 주인이 "이 층은 보여만 준다"고 선언하는 것 | 모듈의 `exports` |
| 세입자가 주인에게 받아 오는 임시 허가증 | `--add-opens` · `--add-exports` 실행 플래그 |
| 설계도를 읽는 것 자체 | **언제나 된다** — 막히는 것은 "문을 여는 것"뿐 |

- **설계도를 보는 것과 문을 여는 것은 다른 일**이다.\
  `String.class.getDeclaredFields()` 는 언제나 되지만, 그 필드에 `setAccessible(true)` 는 막힌다.
- 막힐 때 나는 것이 **`InaccessibleObjectException`** 이고, 메시지가 **무엇이 부족한지 정확히 말해 준다.**
- **내 코드(클래스패스의 이름 없는 모듈)끼리는 다 열린다.** 그래서 프레임워크가 내 DTO 는 채울 수 있다.

```text
내 클래스                         JDK 클래스 (java.base 모듈)
+---------------------------+     +----------------------------------+
| class Secret {            |     | class java.lang.String {         |
|   private String token;   |     |   private final byte[] value;    |
| }                         |     | }                                |
+---------------------------+     +----------------------------------+
   getDeclaredField("token")         getDeclaredField("value")
        -> 된다                          -> 된다  (설계도는 보인다)
   setAccessible(true)               setAccessible(true)
        -> 된다                          -> InaccessibleObjectException
   f.get(s) -> "비밀"                     "module java.base does not
                                           \"opens java.lang\" to unnamed module"
```

실무에서 이게 터지는 자리는 **JDK 를 8 에서 17 이상으로 올린 직후**다.\
ORM·직렬화·모킹 라이브러리가 `java.util`·`java.lang` 내부를 `setAccessible` 하던 코드가 한꺼번에 죽고,\
`--add-opens` 플래그를 기동 스크립트에 붙이는 것으로 임시 연명하게 된다.

> **리플렉션(reflection)** — 실행 중에 타입의 구조(필드·메서드·애너테이션)를 조회하고 다루는 기능.\
> 예: 프레임워크가 `@Autowired` 가 붙은 필드를 찾아 값을 채워 넣는 것.

> **강제 캡슐화(strong encapsulation)** — 모듈이 열어 주지 않은 내부에 리플렉션으로도 못 들어가게 막는 것.\
> 예: `java.base` 가 `opens java.lang` 을 안 했으므로 `String.value` 를 못 연다.

> **이름 없는 모듈(unnamed module)** — 클래스패스에 올린 코드가 들어가는 가상의 모듈.\
> 예: `Ex.java` 를 `javac`·`java` 로 그냥 돌리면 내 클래스는 전부 여기 있다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `Class` 를 얻는 세 가지 길은 **무엇이 다른가** — 부작용이 있는 것은 어느 것인가.
2. `getXxx` 와 `getDeclaredXxx` 는 **각각 무엇을 주는가** — 상속과 `private` 을 어떻게 가르는가.
3. `setAccessible(true)` 는 **어디까지 통하는가** — 막히면 무엇이 나오고 어떻게 여는가.

## 동작 방식

### (1) `Class` 를 얻는 세 가지 길

**언제 쓰나** — 리플렉션의 모든 출발점. 셋 중 무엇을 쓸지가 곧 "이름을 컴파일 타임에 아는가"다.

```text
String.class                    <- 컴파일 타임에 이름을 안다. 가장 싸고 안전하다
"hi".getClass()                 <- 객체가 있다. 선언 타입이 아니라 실제 타입을 준다
Class.forName("java.lang.String")  <- 이름이 문자열이다. 없으면 ClassNotFoundException
```

실행 결과 (`Ex.java (58-a)`, JDK 21.0.5 — 17 · 25 동일):

```text
--- Class 를 얻는 법 셋
  String.class            = class java.lang.String
  "hi".getClass()         = class java.lang.String
  Class.forName("...")    = class java.lang.String
  셋이 같은 객체?          = true
--- 선언 타입이 아니라 실제 타입이 나온다
  선언은 Object, getClass() = java.util.ArrayList
```

그림 해설 (한 단계씩):

- 셋이 **같은 객체**다(`==` 가 true). 한 클래스로더가 로드한 타입 하나에 `Class` 객체 하나다.
- `getClass()` 는 **선언 타입이 아니라 실제 타입**을 준다 — `Object o = new ArrayList<>()` 에서 `java.util.ArrayList` 가 나온다.

**★ `Class.forName` 에만 부작용이 있다 — 클래스를 초기화한다.**

```text
--- Class.forName 은 초기화를 시킨다
  Holder.class 리터럴만 쓰기 전
  리터럴만 썼다 (static 초기화 안 일어남)
  [Holder static 초기화 실행]
  forName 을 불렀다
  forName(name, false, loader) 로 초기화 끄기:
  Holder2 는 초기화 안 됐다
```

- `Holder.class` 리터럴만 써서는 **static 초기화 블록이 안 돈다.**
- `Class.forName("Holder")` 를 부르는 순간 **돈다.**
- `Class.forName(name, false, loader)` 는 **초기화를 끈 채로** 로드한다.
- (옛날 JDBC 의 `Class.forName("com.mysql.jdbc.Driver")` 가 이 부작용을 이용한 것이다 —\
  드라이버의 static 블록이 `DriverManager` 에 자기를 등록했다.)

```text
--- 없는 클래스 이름을 주면
  java.lang.ClassNotFoundException: com.nope.Nope
```

**이름 세 가지도 다르다.**

```text
--- 이름 세 가지
  getName=int                    getSimpleName=int          getCanonicalName=int
  getName=[I                     getSimpleName=int[]        getCanonicalName=int[]
  getName=[[Ljava.lang.String;   getSimpleName=String[][]   getCanonicalName=java.lang.String[][]
  getName=Ex$Nested              getSimpleName=Nested       getCanonicalName=Ex.Nested
  getName=java.util.ArrayList    getSimpleName=ArrayList    getCanonicalName=java.util.ArrayList
  getName=Ex$Inner               getSimpleName=Inner        getCanonicalName=Ex.Inner
  getName=Ex$1                   getSimpleName=""           getCanonicalName=null
```

- **`getName()` 이 `Class.forName` 에 다시 넣을 수 있는 이름**이다. 배열은 `[I`·`[[Ljava.lang.String;` 꼴이다.
- **익명 클래스는 `getSimpleName()` 이 빈 문자열, `getCanonicalName()` 이 `null`** 이다 —\
  로그에 `getSimpleName()` 을 쓰면 익명 클래스에서 빈칸이 찍힌다.

비용 — `X.class` 는 사실상 0(상수 풀 참조). `getClass()` 도 싸다. **`Class.forName` 은 로딩·초기화라 비싸다.**

### (2) `getXxx` 대 `getDeclaredXxx` — 축이 둘이다

**언제 쓰나** — "왜 내 `private` 필드가 안 보이지" 또는 "왜 상속받은 게 없지"를 물을 때.

```text
                  public 만          전부 (private 포함)
              +------------------+---------------------+
 이 클래스만  |                  |  getDeclaredFields  |
              |                  |  getDeclaredMethods |
              +------------------+---------------------+
 상속 포함    |  getFields       |   (없다)            |
              |  getMethods      |                     |
              +------------------+---------------------+
```

- **두 축이 한꺼번에 바뀐다.** `getFields` = public + 상속, `getDeclaredFields` = 전부 + **이 클래스만**.
- **"상속받은 private" 을 한 번에 주는 메서드는 없다.** 상위 클래스로 올라가며 직접 모아야 한다.

실행 결과 (`Ex.java (58-b)`, JDK 21.0.5 — 17 · 25 동일). `Child extends Base` 이고 양쪽에 public/private 멤버가 있다.

```text
--- 필드
  getFields()         (public + 상속) = [basePublic, childPublic]
  getDeclaredFields() (이 클래스 전부) = [childPrivate, childPublic]
--- 메서드
  getMethods()         (public + 상속, Object 것 제외해 표시) = [basePublicM, childPublicM]
  getDeclaredMethods() (이 클래스 전부)                      = [childPrivateM, childPublicM]
--- 생성자
  getConstructors()         = 0개
  getDeclaredConstructors() = 2개
--- 상속된 private 은 getDeclared* 로도 안 보인다
  Child.getDeclaredFields 에 basePrivate 있나? = false
  Base.getDeclaredFields  에 basePrivate 있나? = true
```

그림 해설 (한 단계씩):

- `getFields()` 에 `baseProtected` 가 **없다** — `protected` 도 public 이 아니다.
- `getDeclaredFields()` 에 `basePublic` 이 **없다** — 상속받은 것은 "선언된" 것이 아니다.
- `getConstructors()` 가 **0개**인데 `getDeclaredConstructors()` 는 2개다 —\
  `Child()` 가 package-private 이고 `Child(int)` 가 private 이라 **public 생성자가 없다.**
- 그래서 **프레임워크는 거의 언제나 `getDeclared*` + `setAccessible`** 을 쓴다.

**없는 멤버를 찾으면 예외다.**

```text
--- 없는 멤버를 찾으면
  java.lang.NoSuchFieldException: nope
  java.lang.NoSuchMethodException: Child.childPrivateM()
```

- `getMethod("childPrivateM")` 은 **`private` 이라 "없는" 것으로 취급**된다 — `getDeclaredMethod` 를 써야 한다.
- `NoSuchFieldException`·`NoSuchMethodException` 은 **검사 예외**다(`ReflectiveOperationException` 의 하위).

비용 — `getDeclaredFields()` 는 호출마다 **배열과 `Field` 객체를 복사해 돌려준다.** 100만 회에 17~29 ms 였다((6)).

### (3) ★ `setAccessible` 과 모듈 경계 — 내 것은 열리고 JDK 것은 막힌다

**언제 쓰나** — `InaccessibleObjectException` 을 만났을 때. JDK 를 올린 직후 가장 자주 본다.

```text
                  setAccessible(true) 대상
                            |
        +-------------------+-------------------+
        |                                       |
 내 클래스 (이름 없는 모듈)               JDK 클래스 (java.base)
        |                                       |
      열린다                          java.base 가 opens 했나?
   private 도 읽고 쓴다                    |            |
                                       했다          안 했다
                                        |              |
                                      열린다   InaccessibleObjectException
                                               (--add-opens 로 열 수 있다)
```

실행 결과 — **플래그 없이** (`Ex.java (58-c)`, JDK 21.0.5):

```text
--- 내 클래스의 private 필드 읽기·쓰기
  setAccessible 전 f.get() 시도:
    IllegalAccessException: class Ex cannot access a member of class Secret with modifiers "private"
  setAccessible(true) 후 : 비밀
  값을 바꾼 뒤          : 바꿔치기
--- 내 클래스의 private 메서드 부르기
  jun 에게만: 비밀
--- java.lang.String 의 private 필드 value 에 setAccessible
  getDeclaredField 까지는 됐다: private final byte[] java.lang.String.value
  java.lang.reflect.InaccessibleObjectException
  메시지: Unable to make field private final byte[] java.lang.String.value accessible: module java.base does not "opens java.lang" to unnamed module @2f0e140b
--- java.util.ArrayList 의 private 필드 elementData 에 setAccessible
  java.lang.reflect.InaccessibleObjectException
  메시지: Unable to make field transient java.lang.Object[] java.util.ArrayList.elementData accessible: module java.base does not "opens java.util" to unnamed module @2f0e140b
--- java.util.ArrayList 의 private 필드를 setAccessible 없이 읽기
  java.lang.IllegalAccessException
  메시지: class Ex cannot access a member of class java.util.ArrayList (in module java.base) with package access
--- export 조차 안 된 패키지의 클래스 — jdk.internal.misc.Unsafe
  Class 는 얻었다: class jdk.internal.misc.Unsafe
  java.lang.reflect.InaccessibleObjectException
  메시지: Unable to make public static jdk.internal.misc.Unsafe jdk.internal.misc.Unsafe.getUnsafe() accessible: module java.base does not "exports jdk.internal.misc" to unnamed module @2f0e140b
--- 메타데이터 읽기는 막히지 않는다
  String 의 선언 필드 수 = 11
    private byte[] value
    private byte coder
    private int hash
    private boolean hashIsZero
```

그림 해설 (한 단계씩):

- **`setAccessible` 전에는 내 클래스의 `private` 도 못 읽는다** — `IllegalAccessException`.\
  이것은 모듈과 무관한, 원래부터 있던 접근 제어다.
- **내 클래스는 `setAccessible(true)` 로 열린다.** 읽기도 쓰기도 된다.
- **JDK 내부는 `InaccessibleObjectException`** 이다. 메시지가 세 가지를 정확히 말한다.

```text
Unable to make <무엇을> accessible: module <어느 모듈이> does not "opens <어느 패키지를>" to <누구에게>
```

- **`exports` 조차 안 된 패키지**(`jdk.internal.misc`)는 메시지가 `"exports ..."` 로 바뀐다.\
  `opens` 가 아니라 `exports` 가 없다는 뜻이다 — **필요한 플래그도 `--add-exports` 로 달라진다.**
- **메타데이터 읽기는 전혀 막히지 않는다.** `String` 의 선언 필드 11 개를 이름·타입까지 다 읽었다.\
  막히는 것은 **값을 읽고 쓰는 것**(=`setAccessible`)뿐이다.

**`--add-opens` 로 열면 된다.**

```text
##### --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED
--- java.lang.String 의 private 필드 value 에 setAccessible
  getDeclaredField 까지는 됐다: private final byte[] java.lang.String.value
  여기까지 오면 열린 것
--- java.util.ArrayList 의 private 필드 elementData 에 setAccessible
  열렸다
--- export 조차 안 된 패키지의 클래스 — jdk.internal.misc.Unsafe
  java.lang.reflect.InaccessibleObjectException
  메시지: Unable to make public static ... does not "exports jdk.internal.misc" to unnamed module @3b07d329
```

```text
##### --add-exports java.base/jdk.internal.misc=ALL-UNNAMED
--- export 조차 안 된 패키지의 클래스 — jdk.internal.misc.Unsafe
  Class 는 얻었다: class jdk.internal.misc.Unsafe
  열렸다
```

- 플래그의 모양은 `--add-opens <모듈>/<패키지>=<받는 쪽>` 이고, 클래스패스 코드는 `ALL-UNNAMED` 다.
- **`--add-opens` 로는 `exports` 문제를 못 고치고, 그 반대도 마찬가지다.** 메시지의 따옴표 안을 보고 고른다.
- **17 · 21 · 25 에서 전부 같은 동작**이었다(메시지의 `@2f0e140b` 같은 해시만 실행마다 다르다).

비용 — `setAccessible(true)` 는 한 번만 부르면 된다. `Field`·`Method` 객체에 상태로 남는다.

### (4) 열었을 때 실제로 무슨 일이 생기나 — 상수 풀 오염

**언제 쓰나** — "`--add-opens` 를 붙이면 되니까 괜찮다"고 말하기 전에.

`--add-opens java.base/java.lang=ALL-UNNAMED` 를 붙이고 `String` 의 `value` 를 바꿔 봤다 (`Ex.java (58-d2)`).

```java
String a = "hello";
String b = "hello";          // 같은 리터럴 -> 상수 풀의 같은 객체
Field v = String.class.getDeclaredField("value");
v.setAccessible(true);
v.set(a, new byte[]{'X','X','X','X','X'});
```

```text
--- 상수 풀 오염 (JDK 21, --add-opens java.base/java.lang=ALL-UNNAMED)
  고치기 전  a=hello b=hello a==b true
  a 만 고쳤는데 b=XXXXX
  a.equals("XXXXX") = true
```

```text
열기 전                              연 뒤 a 의 value 를 바꾸면
+---------------------------+       +---------------------------+
| a --+                     |       | a --+                     |
|     +--> ["hello"]        |       |     +--> ["XXXXX"]        |
| b --+                     |       | b --+                     |
+---------------------------+       +---------------------------+
  두 변수가 같은 객체를 본다            b 도 같이 바뀐다 — 고치지 않았는데
```

- **`b` 를 건드리지도 않았는데 바뀌었다.** 리터럴이 상수 풀에서 같은 객체이기 때문이다([35 `String`](../35-string/) 의 규칙).
- 프로그램 어디에서 `"hello"` 를 쓰든 그 객체를 공유하므로, **한 번의 쓰기가 전역에 퍼진다.**
- `final` 필드라도 `setAccessible(true)` 뒤에는 **쓰기가 됐다**(내 클래스의 `final` 필드도 마찬가지 — `Ex.java (58-d)`).
- 이것이 **JEP 396/403 이 기본을 막아 놓은 이유**다. "열면 된다"는 말의 대가가 이것이다.

비용 — 열어 놓은 채 잘못 쓰면 **디버깅이 불가능한 전역 오염**이다.

### (5) ★ 19번과 잇기 — 소거됐는데 제네릭이 읽히는 이유

**언제 쓰나** — "제네릭은 런타임에 지워진다는데 어떻게 `List<String>` 을 알아내지"를 물을 때.

[19 타입 소거](../19-type-erasure/) 가 정본으로 말하듯 **값에서는 타입 인자가 지워진다.**\
그런데 **선언에는 남는다** — 클래스 파일의 `Signature` 속성이다.

```text
필드 선언  List<String> names;
                |
     +----------+----------+
     |                     |
 descriptor            Signature
 Ljava/util/List;      Ljava/util/List<Ljava/lang/String;>;
     |                     |
 getType()            getGenericType()
 -> List              -> java.util.List<java.lang.String>
```

`javap -v -p Holder.class` (JDK 21.0.5) — 실제 출력 그대로다.

```text
  java.util.List<java.lang.String> names;
    descriptor: Ljava/util/List;
    flags: (0x0000)
    Signature: #33                          // Ljava/util/List<Ljava/lang/String;>;

  java.util.Map<java.lang.String, java.util.List<java.lang.Integer>> deep;
    descriptor: Ljava/util/Map;
    flags: (0x0000)
    Signature: #34                          // Ljava/util/Map<Ljava/lang/String;Ljava/util/List<Ljava/lang/Integer;>;>;

  T value;
    descriptor: Ljava/lang/Number;
    flags: (0x0000)
    Signature: #37                          // TT;

  java.util.List<? extends java.lang.Number> wild;
    descriptor: Ljava/util/List;
    flags: (0x0000)
    Signature: #38                          // Ljava/util/List<+Ljava/lang/Number;>;
```

리플렉션이 읽는 것이 바로 이 `Signature` 다 (`Ex.java (58-e)`, JDK 21.0.5 — 17 · 25 동일):

```text
--- getType 은 소거된 타입, getGenericType 은 선언 그대로
  names   getType=List                   getGenericType=java.util.List<java.lang.String>
  deep    getType=Map                    getGenericType=java.util.Map<java.lang.String, java.util.List<java.lang.Integer>>
  value   getType=Number                 getGenericType=T
  wild    getType=List                   getGenericType=java.util.List<? extends java.lang.Number>
  arr     getType=String[]               getGenericType=java.lang.String[]
--- ParameterizedType 으로 실제 인자 꺼내기
  raw  = java.util.Map
  args = [class java.lang.String, java.util.List<java.lang.Integer>]
  둘째 인자의 raw = java.util.List
--- 타입 파라미터와 바운드
  T extends [class java.lang.Number]
--- 상위 클래스의 실제 타입 인자 (이 트릭이 프레임워크의 밥줄이다)
  IntHolder.getGenericSuperclass() = Holder<java.lang.Integer>
  실제 인자 = java.lang.Integer
--- 메서드의 제네릭 정보
  getReturnType        = java.util.List
  getGenericReturnType = java.util.List<java.lang.String>
  getParameterTypes    = [interface java.util.Map, class [Ljava.lang.Number;]
  getGenericParameterTypes = [java.util.Map<java.lang.String, T>, T[]]
  isVarArgs = true
--- 익명 하위 클래스로 제네릭을 잡는 관용구 (TypeToken)
  잡은 타입 = java.util.List<java.util.Map<java.lang.String, java.lang.Integer>>
```

그림 해설 (한 단계씩):

- `T value` 의 `getType()` 이 **`Number`** 다 — 바운드로 소거된 것이고, 19번의 규칙 그대로다.
- `getGenericSuperclass()` 로 **하위 클래스가 고정한 실제 인자**(`Integer`)를 읽을 수 있다.\
  Jackson 의 `TypeReference`, Guava 의 `TypeToken`, Spring 의 `ParameterizedTypeReference` 가 전부 이 트릭이다.
- **소거는 "값"에서 일어나고, "선언"에는 `Signature` 로 남는다** — 이 한 문장이 19번과 이 주제를 잇는다.

비용 — `getGenericType()` 은 `Signature` 문자열을 **파싱**한다. `getType()` 보다 비싸다.

### (6) 애너테이션 읽기 · 예외 감싸기 · 비용

**언제 쓰나** — 프레임워크가 하는 일을 흉내 낼 때.

**애너테이션은 `RUNTIME` 만 보인다** ([16 애너테이션](../16-annotations/) 이 정본). `Ex.java (58-f)`, JDK 21.0.5:

```text
--- 런타임에 보이는 애너테이션은 RUNTIME 뿐이다
  클래스 : [@Keep("클래스"), @Passed()]
  필드   : [@Keep("필드")]
  @Keep 의 value() = 클래스
--- @Inherited 는 클래스 상속에만 먹는다
  Sub 의 getAnnotations()         = [@Passed()]
  Sub 의 getDeclaredAnnotations() = []
```

- `@Gone`(CLASS)·`@Never`(SOURCE)는 **목록에 아예 없다.**
- `@Inherited` 가 붙은 `@Passed` 만 `Sub` 의 `getAnnotations()` 에 나오고, `getDeclaredAnnotations()` 에는 없다.
- **애너테이션의 `toString` 은 비 ASCII 를 `\uXXXX` 로 이스케이프한다** — 위 출력의 `클...` 가 그것이다.\
  `value()` 를 직접 부르면 한글 그대로 나온다.

**`invoke` 안의 예외는 감싸져 온다.**

```text
--- 실제로 잡아야 하는 것
  InvocationTargetException 으로 감싸져 온다
  getCause() = java.lang.IllegalStateException: 안에서 터졌다
--- 인자 타입이 안 맞으면
  java.lang.IllegalArgumentException: argument type mismatch
```

- 대상 메서드가 던진 예외는 **`InvocationTargetException` 에 싸여** 온다. **`getCause()` 를 보지 않으면 원인이 사라진다.**
- 프레임워크의 스택트레이스가 길고 읽기 어려운 이유 중 하나가 이것이다.

**비용 — 자릿수로 20~30배** (`Ex.java (58-f)`, 1000만 회 × 5 회, JMH 아님).

```text
  1회차  직접=   21 ms  invoke=  194 ms  setAccessible(true) 후 invoke=  136 ms
  2회차  직접=   33 ms  invoke=  167 ms  setAccessible(true) 후 invoke=  105 ms
  3회차  직접=    3 ms  invoke=   69 ms  setAccessible(true) 후 invoke=   65 ms
  4회차  직접=    3 ms  invoke=  176 ms  setAccessible(true) 후 invoke=   65 ms
  5회차  직접=    2 ms  invoke=   68 ms  setAccessible(true) 후 invoke=   64 ms
--- 필드 조회 자체의 비용 (getDeclaredField 100만 회)
  17 ms
```

- **직접 호출은 JIT 가 인라인해 거의 사라진다**(2~3 ms). 그래서 배수는 "리플렉션이 느리다"보다\
  **"직접 호출이 공짜가 된다"**에 가깝다 — 그것이 핵심이다.
- `setAccessible(true)` 를 미리 해 두면 **접근 검사를 건너뛰어** 조금 빨라진다(69 → 65 ms 급).
- `getDeclaredField` 100만 회가 17 ms(두 번째 실행 19 ms)였다 — **호출마다 `Field` 객체를 새로 복사해** 준다.\
  프레임워크가 `Field` 를 캐시하는 이유다.

비용 정리 — **루프 안에서 리플렉션을 쓰지 않는다.** 시작할 때 한 번 조회해 캐시하고, 호출만 반복한다.

## 문법 — 형태와 규칙

```java
Class<?> c = Target.class;                                  // 또는 obj.getClass() / Class.forName(...)

Field  f = c.getDeclaredField("token");     f.setAccessible(true);
Method m = c.getDeclaredMethod("hi", String.class);  m.setAccessible(true);
Constructor<?> ctor = c.getDeclaredConstructor();    ctor.setAccessible(true);

Object obj  = ctor.newInstance();
Object val  = f.get(obj);      f.set(obj, "새 값");
Object ret  = m.invoke(obj, "인자");
```

| 얻는 것 | public + 상속 | 전부 + 이 클래스만 |
|---|---|---|
| 필드 | `getFields()` / `getField(name)` | `getDeclaredFields()` / `getDeclaredField(name)` |
| 메서드 | `getMethods()` / `getMethod(name, types)` | `getDeclaredMethods()` / `getDeclaredMethod(...)` |
| 생성자 | `getConstructors()` / `getConstructor(types)` | `getDeclaredConstructors()` / `getDeclaredConstructor(...)` |
| 중첩 타입 | `getClasses()` | `getDeclaredClasses()` |

- **생성자는 상속되지 않는다** — `getConstructors()` 도 이 클래스 것만 준다(public 만 거를 뿐).
- `Modifier.toString(f.getModifiers())` 로 제어자를 읽는다.

```text
--- 제어자 읽기
  childPublic -> public int
  childPrivate -> private int
```

| 예외 | 언제 |
|---|---|
| `ClassNotFoundException` | `Class.forName` 의 이름이 없다 (**검사 예외**) |
| `NoSuchFieldException` / `NoSuchMethodException` | 그 이름의 멤버가 없다 (**검사 예외**) |
| `IllegalAccessException` | `setAccessible` 없이 안 보이는 멤버를 건드렸다 (**검사 예외**) |
| `InaccessibleObjectException` | 모듈이 안 열어 줬다 (**비검사** — `RuntimeException`) |
| `InvocationTargetException` | 대상 메서드가 예외를 던졌다. `getCause()` 로 꺼낸다 (**검사 예외**) |
| `IllegalArgumentException` | `invoke` 의 인자 타입·개수가 안 맞는다 (**비검사**) |

- **`InaccessibleObjectException` 만 비검사**다 — 그래서 JDK 를 올렸을 때 **컴파일은 통과하고 실행에서 터진다.**

## 어디서 틀리나

### 1. `getMethod` 로 `private` 메서드를 찾는다

```text
  java.lang.NoSuchMethodException: Child.childPrivateM()
```

- `getMethod` 는 **public 만** 본다. `getDeclaredMethod` 를 써야 한다.
- 메시지가 "없다"고 말해서 **오타를 의심하다 시간을 버린다.**

### 2. 상속받은 `private` 을 `getDeclaredFields` 로 찾는다

```text
  Child.getDeclaredFields 에 basePrivate 있나? = false
  Base.getDeclaredFields  에 basePrivate 있나? = true
```

- **"상속 + private"을 한 번에 주는 메서드가 없다.** `getSuperclass()` 로 올라가며 모아야 한다.
- 프레임워크가 상위 클래스까지 훑는 코드를 직접 들고 있는 이유다.

### 3. `InvocationTargetException` 을 그대로 로그에 찍는다

```text
--- invoke 안에서 예외가 나면
  던져진 것 : java.lang.RuntimeException / java.lang.reflect.InvocationTargetException
  getCause() : java.lang.reflect.InvocationTargetException / null
```

- 위는 `InvocationTargetException` 을 또 `RuntimeException` 으로 감싼 경우다 — **원인이 두 겹 아래로 내려갔다.**
- 방어: `catch (InvocationTargetException e) { throw e.getCause(); }` 처럼 **껍질을 벗겨서** 던진다.

### 4. `--add-opens` 로 `exports` 문제를 고치려 한다

```text
module java.base does not "opens java.lang" to unnamed module      -> --add-opens
module java.base does not "exports jdk.internal.misc" to unnamed   -> --add-exports
```

- 메시지의 **따옴표 안 낱말**이 어느 플래그인지 말해 준다. 그대로 읽으면 된다.

### 5. 리플렉션을 루프 안에서 조회한다

- `getDeclaredField` 100만 회에 17 ms — 한 번이면 무시할 만하지만 **요청마다 수십 번이면 쌓인다.**
- 방어: `Field`·`Method` 를 **static 캐시**에 담는다. `setAccessible(true)` 도 그때 한 번만.

### 6. 리플렉션으로 `final` 을 바꿔 놓고 "됐다"고 믿는다

- (4) 에서 본 대로 **상수 풀이 오염**된다.
- 그리고 **컴파일 타임 상수**(`static final int X = 10;` 같은 것)는 호출부에 값이 박혀 있어,\
  필드를 바꿔도 **읽는 쪽이 안 바뀐다.** 리플렉션으로 상수를 바꾸는 코드는 대체로 틀린다.

## 구현 세부사항 대 언어 보장

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `X.class`·`getClass`·`forName` 이 같은 객체 | **언어** — 클래스로더 하나당 타입 하나 | (1) 의 `==` |
| `Class.forName` 이 초기화를 시킨다 | **javadoc 계약** | (1) 의 실행 |
| `getXxx` / `getDeclaredXxx` 의 범위 | **javadoc 계약** | (2) |
| `setAccessible` 이 모듈에 막히는 것 | **언어·JEP 396/403** | (3) 의 예외 |
| 예외 **타입** | **javadoc 계약** | 위 표 |
| 예외 **메시지 문구** | **구현** | 17·21·25 에서 같았지만 보장이 아니다 |
| `unnamed module @2f0e140b` 의 해시 | **실행마다 다르다** | 대조에 쓸 수 없다 |
| 제네릭이 `Signature` 로 남는 것 | **클래스 파일 명세** | (5) 의 `javap -v` |
| 리플렉션이 느린 배수 | **JIT·머신** | 재현되는 것은 자릿수 |
| `String.value` 를 바꿔 `b` 까지 바뀌는 것 | **구현에 기댄 동작** — 애초에 해서는 안 되는 일 | (4) |

## 언제 쓰고 언제 안 쓰나

| 쓴다 | 안 쓴다 |
|---|---|
| 프레임워크·라이브러리(DI·ORM·직렬화·테스트 러너) | 애플리케이션 도메인 로직 |
| 플러그인 로딩 — 이름이 **설정에 있는** 경우 | 컴파일 타임에 타입을 아는 경우 (그냥 부르면 된다) |
| 애너테이션 기반 자동 배선 | 성능이 중요한 루프 안 |
| 테스트에서 private 상태 확인 (최후 수단) | `private` 을 "잠깐 열어" 우회하는 프로덕션 코드 |
| 진단·디버깅 도구 | JDK 내부 — `--add-opens` 없이는 막히고, 붙여도 다음 LTS 에서 또 막힐 수 있다 |

- 대안: **`MethodHandle`/`VarHandle`**(7·9+)은 같은 일을 더 빠르게 한다(JIT 가 인라인할 수 있다).\
  다만 접근 검사는 `Lookup` 을 만들 때 하므로 **모듈 경계는 똑같이 적용된다.**

## 핵심 문장

- **설계도를 읽는 것(`getDeclared*`)은 언제나 되고, 문을 여는 것(`setAccessible`)이 모듈에 막힌다.**
- 막히면 **`InaccessibleObjectException`** 이고, 메시지가 `opens` 인지 `exports` 인지까지 말해 준다 — 플래그를 그대로 고르면 된다.
- `getXxx` = **public + 상속**, `getDeclaredXxx` = **전부 + 이 클래스만**. "상속된 private"은 직접 올라가며 모은다.
- **소거는 값에서 일어나고 선언에는 `Signature` 로 남는다** — `getGenericType()` 이 읽는 것이 그것이다(19번과 잇는 자리).
- 리플렉션은 **자릿수로 20~30배 느리고**, 그 대부분은 **직접 호출이 JIT 로 공짜가 되기 때문**이다. `Field`·`Method` 는 캐시한다.

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 58번)
- [`../19-type-erasure/`](../19-type-erasure/) — **소거의 규칙 자체가 정본이다**(`new T[]` 금지·브리지 메서드·`instanceof List<String>`).\
  **경계: 그쪽은 「무엇이 지워지나」까지, 여기는 「지워지고 남은 `Signature` 를 런타임에 어떻게 읽나」부터다.**
- [`../16-annotations/`](../16-annotations/) — **`@Retention`·`@Target`·메타 애너테이션이 정본이다.**\
  **경계: 그쪽은 「무엇이 언제까지 남나」까지, 여기는 「남은 것을 `getAnnotations()` 로 어떻게 꺼내나」부터다.**
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 — **클래스로더·JVM 내부가 정본이다.**\
  **경계: 「클래스가 어떻게 로드되나」는 거기, 「로드된 것을 `Class` 로 어떻게 다루나」가 여기다.**
- [`../34-imports/`](../34-imports/) — **경계: `Class.forName("java.util.List")` 은 `import` 와 무관하다.**\
  `import` 는 컴파일 타임 약칭, `forName` 은 런타임 문자열이다.
- [`../../../../../../history/java/java-9.md`](../../../../../../history/java/java-9.md) — **모듈 시스템(JPMS)이 왜 나왔나가 정본**(`sun.misc.Unsafe` 이야기 포함)
- [`../35-string/`](../35-string/) — (4) 의 상수 풀 오염이 왜 전역에 퍼지는지의 규칙
- [`../10-access-modifiers/`](../10-access-modifiers/) — `setAccessible` 이 우회하는 바로 그 네 단계
- [`../25-exceptions/`](../25-exceptions/) — `ReflectiveOperationException` 계열이 **검사 예외**인 것과 그 함의
- [`../14-records/`](../14-records/) — `record` 의 컴포넌트가 `Record` 속성으로 런타임에 남는 것(리플렉션으로 읽힌다)

## 용어 풀이

- **리플렉션** — 실행 중에 타입 구조를 조회·조작하는 기능. `java.lang.reflect` 패키지.
- **`Class<?>`** — 타입 하나를 나타내는 객체. 클래스로더당 타입당 하나.
- **`getDeclared*` / `get*`** — 이 클래스에 선언된 전부 / public + 상속받은 것.
- **`setAccessible(true)`** — 접근 검사를 끄라고 요청하는 것. 모듈이 허락해야 성공한다.
- **강제 캡슐화(strong encapsulation)** — 모듈이 열지 않은 내부를 리플렉션으로도 막는 것. JDK 16(JEP 396)부터 기본.
- **`opens` / `exports`** — 리플렉션까지 열어 주는 선언 / 컴파일·참조만 열어 주는 선언.
- **이름 없는 모듈(unnamed module)** — 클래스패스에 올린 코드가 속하는 가상 모듈. `ALL-UNNAMED` 가 이것을 가리킨다.
- **`--add-opens` / `--add-exports`** — 실행 시점에 `opens`/`exports` 를 덧붙이는 플래그.
- **`InaccessibleObjectException`** — `setAccessible` 이 모듈 경계에 막혔을 때의 비검사 예외.
- **`InvocationTargetException`** — `invoke` 한 메서드가 던진 예외를 감싼 껍질. `getCause()` 가 진짜다.
- **`Signature` 속성** — 클래스 파일에 제네릭 선언을 문자열로 남기는 속성. `getGenericType()` 이 이것을 읽는다.
- **`ParameterizedType`** — `List<String>` 같은 "인자 붙은 타입"을 나타내는 리플렉션 타입.
- **TypeToken 관용구** — 익명 하위 클래스를 만들어 `getGenericSuperclass()` 로 타입 인자를 잡는 기법.

## 더 들어가면

- **익명 클래스의 이름은 `Ex$1` 이다.**\
  `getSimpleName()` 이 빈 문자열, `getCanonicalName()` 이 `null` 이다 —\
  로깅·에러 메시지에 `getSimpleName()` 을 쓰면 람다·익명 클래스에서 빈칸이 나온다. `getName()` 을 쓴다.

- **`Class.forName(name, false, loader)` 의 두 번째 인자가 초기화 스위치다.**\
  스캐너·클래스패스 탐색기는 이것을 `false` 로 둔다 — 안 그러면 **스캔하는 것만으로 남의 static 블록이 전부 돈다.**

- **`getDeclaredFields()` 의 순서는 보장되지 않는다.**\
  javadoc 이 *"The elements in the returned array are not sorted and are not in any particular order"* 라고 적는다.\
  이 문서의 출력은 비교를 위해 **프로그램에서 정렬한 것**이다.

- **`record` 는 리플렉션 친화적이다.**\
  컴포넌트 이름이 `Record` 속성으로 남아 `getRecordComponents()` 로 읽힌다 — 파라미터 이름과 달리 `-parameters` 플래그가 필요 없다.\
  자세한 것은 [14 `record`](../14-records/).

- **`MethodHandle`·`VarHandle` 이 현대적 대안이다.**\
  `Lookup` 을 만들 때 한 번 접근 검사를 하고, 그 뒤 호출은 JIT 가 인라인할 수 있다.\
  다만 **모듈 경계는 똑같이 적용된다** — `privateLookupIn` 도 `opens` 가 있어야 한다.\
  (이 배치에서 `MethodHandle` 의 성능은 재지 않았다.)

- **`--add-opens` 를 붙여도 JDK 25 에서 경고가 나지 않았다**(돌려 확인).\
  다만 `sun.misc.Unsafe` 의 메모리 접근 메서드처럼 **별도 JEP 로 경고가 붙은 영역**이 따로 있다.\
  "플래그를 붙였으니 영구히 안전"은 아니라는 뜻이다 — 플래그 자체가 언젠가 사라질 수 있다.
