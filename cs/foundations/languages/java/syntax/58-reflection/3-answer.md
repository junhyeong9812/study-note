# java/syntax/58 — 리플렉션: `Class`·`getDeclared*`·접근 제어 우회의 경계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·예외는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> javadoc 인용은 `lib/src.zip` 의 실파일에서, 클래스 파일 속성은 `javap -v -p` 출력을 그대로 옮겼다.\
> 실행 파일명은 전부 `Ex.java` 로 고정했고, 프로그램이 여럿이라 `Ex.java (58-a)` 처럼 라벨로 구분한다.\
> 모듈 경계 실험은 **플래그 없이 / `--add-opens` / `--add-exports`** 세 조건에서 각각 돌렸고,
> 17.0.13 · 25.0.1 에서도 확인했다 — **세 버전의 동작이 같았다.**
> **★ 측정 조건**(10번) — **JMH 가 아니다.** `System.nanoTime()` 반복 측정이고,
> 머신은 13th Gen Intel Core i7-13700HX · 24 스레드 · Linux 7.0.0-31-generic 이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `Class` 를 얻는 세 가지 길

**출력** (`Ex.java (58-a)`, JDK 21.0.5 — 17 · 25 동일)

```text
--- Class 를 얻는 법 셋
  String.class            = class java.lang.String
  "hi".getClass()         = class java.lang.String
  Class.forName("...")    = class java.lang.String
  셋이 같은 객체?          = true
--- Class.forName 은 초기화를 시킨다
  Holder.class 리터럴만 쓰기 전
  리터럴만 썼다 (static 초기화 안 일어남)
  [Holder static 초기화 실행]
  forName 을 불렀다
  forName(name, false, loader) 로 초기화 끄기:
  Holder2 는 초기화 안 됐다
--- 없는 클래스 이름을 주면
  java.lang.ClassNotFoundException: com.nope.Nope
```

**첫 출력** — `true`. 한 클래스로더가 로드한 타입 하나에 `Class` 객체는 하나다.

**초기화가 찍히는 것 — (나) 뿐이다.**

| | 초기화 |
|---|---|
| (가) `Holder.class` 리터럴 | **안 한다** |
| (나) `Class.forName("Holder")` | **한다** |
| (다) `Class.forName("Holder", false, loader)` | **안 한다**(둘째 인자가 초기화 스위치) |

**JDBC 가 노린 것**

- **static 초기화 블록의 부작용**이다. 드라이버 클래스의 static 블록이\
  `DriverManager.registerDriver(new Driver())` 를 불러 **자기를 등록**했다.
- 지금은 `ServiceLoader`(META-INF/services)로 자동 등록되므로 `Class.forName` 이 필요 없다.

**없는 이름** — `ClassNotFoundException` 이고 **검사 예외**다(`ReflectiveOperationException` 의 하위).

### 2. 이름 세 가지

**출력** (`Ex.java (58-a)`, JDK 21.0.5)

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

**배열의 `getName()`**

- 1차원 `int[]` → **`[I`**
- 2차원 `String[][]` → **`[[Ljava.lang.String;`**
- 대괄호 개수가 차원이고, 참조 타입은 `L...;` 로 감싼다.

**익명 클래스**

- `getSimpleName()` = **빈 문자열**, `getCanonicalName()` = **`null`**, `getName()` = `Ex$1`.

**`Class.forName` 에 다시 넣을 수 있는 것** — **`getName()`** 이다.\
중첩 클래스는 `Ex$Nested` 처럼 `$` 를 쓰고, `getCanonicalName()` 의 `Ex.Nested` 로는 못 찾는다.

**로그에 쓸 것** — **`getName()`**.\
`getSimpleName()` 은 익명 클래스에서 빈칸이 되고, 서로 다른 패키지의 동명 클래스를 구별하지 못한다.

### 3. `getXxx` 대 `getDeclaredXxx`

**출력** (`Ex.java (58-b)`, JDK 21.0.5 — 17 · 25 동일. 목록은 비교를 위해 프로그램에서 정렬했다)

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

**원소**

| | 원소 | 빠진 것과 이유 |
|---|---|---|
| `getFields()` | `basePublic`, `childPublic` | `baseProtected` — **protected 는 public 이 아니다** |
| `getDeclaredFields()` | `childPrivate`, `childPublic` | `basePublic` — **상속받은 것은 "선언된" 것이 아니다** |

**생성자** — `getConstructors()` = **0**, `getDeclaredConstructors()` = **2**.

- `Child()` 가 package-private, `Child(int)` 가 private 이라 **public 생성자가 하나도 없다.**
- 그래서 `getConstructors()` 가 빈 배열이다.

**`basePrivate` 은 `Child.getDeclaredFields()` 에 없다.**\
javadoc 이 그렇게 적는다 — *"This includes public, protected, default (package) access, and private fields, **but excludes inherited fields**."*

**한 번에 주는 메서드는 없다.**

```java
for (Class<?> c = type; c != null; c = c.getSuperclass())
    for (Field f : c.getDeclaredFields()) { ... }
```

- 프레임워크가 이 루프를 직접 들고 있는 이유다.

### 4. 없는 멤버를 찾으면

**출력** (`Ex.java (58-b)`, JDK 21.0.5)

```text
--- 없는 멤버를 찾으면
  java.lang.NoSuchFieldException: nope
  java.lang.NoSuchMethodException: Child.childPrivateM()
```

**둘째 줄의 진짜 이유**

- `getMethod` 는 **public 만** 본다. `childPrivateM` 은 `private` 이라 **"없는" 것으로 취급**된다.
- 찾으려면 `getDeclaredMethod("childPrivateM")` 를 써야 한다.
- 메시지가 "없다"고만 말해서 **오타를 의심하며 시간을 버리기 쉬운 자리**다.

**검사 예외다.** `NoSuchFieldException`·`NoSuchMethodException` 둘 다 `ReflectiveOperationException` 의 하위이고,\
`ReflectiveOperationException` 은 `Exception` 의 하위다 — 그래서 `throws` 나 `try` 가 강제된다.

### 5. ★ `setAccessible` 은 어디까지 통하나

**출력 — 플래그 없이** (`Ex.java (58-c)`, JDK 21.0.5 — 17 · 25 동일)

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

**플래그 없이 성공하는 것 — (가) 와 (마)**

| | 결과 |
|---|---|
| (가) 내 클래스 `Secret.token` | **성공** — 읽기도 쓰기도 |
| (나) `String.value` | `InaccessibleObjectException` |
| (다) `ArrayList.elementData` | `InaccessibleObjectException` |
| (라) `jdk.internal.misc.Unsafe.getUnsafe()` | `InaccessibleObjectException` |
| (마) `String.class.getDeclaredFields()` 목록 | **성공** — 11 개를 다 읽었다 |

**따옴표 안 낱말이 다른 이유**

```text
(나)(다) : module java.base does not "opens java.lang"      -> opens 가 없다
(라)     : module java.base does not "exports jdk.internal.misc"  -> exports 조차 없다
```

- `java.lang`·`java.util` 은 **`exports` 는 돼 있다**(그래서 `String` 을 그냥 쓸 수 있다).\
  다만 **`opens` 는 안 돼 있어** 리플렉션으로 내부를 여는 것만 막힌다.
- `jdk.internal.misc` 는 **`exports` 부터 안 돼 있다** — 그래서 더 강한 벽이다.
- **필요한 플래그가 달라진다**(6번).

**(마) 가 성공한다는 것은**

- **설계도를 읽는 것과 문을 여는 것이 다른 일**이라는 뜻이다.
- 강제 캡슐화가 막는 것은 **접근 검사 무력화(`setAccessible`)** 이지 **메타데이터 조회**가 아니다.
- 그래서 클래스패스 스캐너·문서 생성기 같은 도구는 플래그 없이도 잘 돈다.

**참고** — `setAccessible` **전에** 내 클래스의 private 을 읽어도 `IllegalAccessException` 이 난다.\
이것은 모듈과 무관한, 원래부터 있던 접근 제어다([10 접근 제어자](../10-access-modifiers/)).

### 6. 플래그로 열면

**출력** (`Ex.java (58-c)`, JDK 21.0.5)

```text
##### --add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.util=ALL-UNNAMED
--- java.lang.String 의 private 필드 value 에 setAccessible
  여기까지 오면 열린 것
--- java.util.ArrayList 의 private 필드 elementData 에 setAccessible
  열렸다
--- export 조차 안 된 패키지의 클래스 — jdk.internal.misc.Unsafe
  java.lang.reflect.InaccessibleObjectException
  메시지: Unable to make public static ... does not "exports jdk.internal.misc" to unnamed module @3b07d329

##### --add-exports java.base/jdk.internal.misc=ALL-UNNAMED
--- export 조차 안 된 패키지의 클래스 — jdk.internal.misc.Unsafe
  Class 는 얻었다: class jdk.internal.misc.Unsafe
  열렸다
```

| 플래그 | 열리는 것 |
|---|---|
| `--add-opens java.base/java.lang=ALL-UNNAMED` | (나) |
| `--add-opens java.base/java.util=ALL-UNNAMED` | (다) |
| `--add-exports java.base/jdk.internal.misc=ALL-UNNAMED` | (라) |

**`--add-opens` 로 `exports` 문제는 못 고친다.** 위 첫 실행에서 (라)는 여전히 막혔다.

**플래그의 세 칸**

```text
--add-opens <모듈 이름>/<패키지 이름>=<이 열림을 받을 모듈>
             java.base   java.lang     ALL-UNNAMED
```

**클래스패스에서 실행할 때** — **`ALL-UNNAMED`** 를 적는다.\
클래스패스 코드는 전부 **이름 없는 모듈**에 들어가기 때문이다(예외 메시지에도 `to unnamed module` 이라고 나온다).

- **17 · 21 · 25 에서 전부 같았다.** JDK 25 에서 `--add-opens` 에 경고도 나지 않았다.

### 7. 열고 나면 무슨 일이 생기나

**출력** (`Ex.java (58-d2)`, JDK 21.0.5, `--add-opens java.base/java.lang=ALL-UNNAMED`)

```text
--- 상수 풀 오염 (JDK 21, --add-opens java.base/java.lang=ALL-UNNAMED)
  고치기 전  a=hello b=hello a==b true
  a 만 고쳤는데 b=XXXXX
  a.equals("XXXXX") = true
```

**마지막 줄의 출력** — `XXXXX`.

**`b` 까지 바뀌는 이유**

- `"hello"` 리터럴 둘은 **상수 풀의 같은 객체**다(`a == b` 가 `true`).
- 그 객체 하나의 `value` 배열을 바꿨으니 **`b` 도 같이 바뀐다.**
- 이 규칙의 정본은 [35 `String`](../35-string/) 의 「상수 풀」 절이다 — JLS §3.10.5 가 문자열 리터럴의 인터닝을 보장한다.
- 프로그램 **어디에서든** `"hello"` 를 쓰면 그 객체이므로, 한 번의 쓰기가 **전역에 퍼진다.**

**`final` 인데 써진 이유**

- `setAccessible(true)` 는 **접근 검사를 끄는 것**이고, 그 뒤의 `Field.set` 은 `final` 여부를 다시 막지 않았다.
- 내 클래스의 `private final int` 도 마찬가지로 써졌다 (`Ex.java (58-d)`).

```text
--- final 필드는 --add-opens 로 열어도 쓸 수 있나 (내 클래스)
  읽기 = 10
  쓰기 성공 -> 99
```

**JEP 396/403 에 대해 말해 주는 것**

- **"열면 된다"의 대가가 이것이다.** 열어 둔 채 누군가 실수하면 **디버깅이 불가능한 전역 오염**이 된다.
- 그래서 JDK 16(JEP 396)부터 **기본이 막힘**이 됐고, 여는 것은 **명시적인 플래그**가 됐다.
- 플래그는 "이 프로그램은 이 위험을 알고 감수한다"는 선언이지 무해한 스위치가 아니다.

### 8. ★ 소거됐는데 제네릭이 읽히는 이유

**출력** (`Ex.java (58-e)`, JDK 21.0.5 — 17 · 25 동일)

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
```

**`names`**

- `getType()` = **`List`**(소거된 것), `getGenericType()` = **`java.util.List<java.lang.String>`**.

**`value` 의 `getType()` 은 `Number`**

- 타입 파라미터가 `T extends Number` 라 **바운드로 소거**됐기 때문이다. 바운드가 없으면 `Object` 가 된다.
- 이 규칙은 [19 타입 소거](../19-type-erasure/) 가 정본이다.

**`Integer` 를 꺼내는 법**

```java
ParameterizedType pt = (ParameterizedType) IntHolder.class.getGenericSuperclass();
Type arg = pt.getActualTypeArguments()[0];      // java.lang.Integer
```

- 익명 하위 클래스로 같은 트릭을 쓰는 것이 **TypeToken 관용구**다.

```text
--- 익명 하위 클래스로 제네릭을 잡는 관용구 (TypeToken)
  잡은 타입 = java.util.List<java.util.Map<java.lang.String, java.lang.Integer>>
```

**어느 속성에 남아 있나 — `Signature`**

`javap -v -p Holder.class` (JDK 21.0.5) 실제 출력.

```text
  java.util.List<java.lang.String> names;
    descriptor: Ljava/util/List;
    flags: (0x0000)
    Signature: #33                          // Ljava/util/List<Ljava/lang/String;>;

  T value;
    descriptor: Ljava/lang/Number;
    flags: (0x0000)
    Signature: #37                          // TT;
```

```text
    Signature: #43                          // (Ljava/util/Map<Ljava/lang/String;TT;>;[TT;)Ljava/util/List<Ljava/lang/String;>;
}
Signature: #44                          // <T:Ljava/lang/Number;>Ljava/lang/Object;
```

- **`descriptor` 는 소거된 것**(JVM 이 쓰는 것), **`Signature` 는 선언 그대로**(컴파일러·리플렉션이 쓰는 것)다.
- 필드·메서드·클래스 각각에 `Signature` 가 붙는다.

**19번과 모순인가 — 아니다.**

- **소거는 "값"에서 일어난다.** 런타임의 `ArrayList` 인스턴스에는 `String` 이라는 정보가 없다.\
  그래서 `list.getClass()` 로는 절대 알 수 없다.
- **선언은 남는다.** 필드·메서드 시그니처·상위 클래스의 타입 인자는 `Signature` 에 문자열로 있다.
- 한 문장으로: **"인스턴스는 모르고, 선언은 안다."**

### 9. 애너테이션과 예외 감싸기

**출력** (`Ex.java (58-f)`, JDK 21.0.5)

```text
--- 런타임에 보이는 애너테이션은 RUNTIME 뿐이다
  클래스 : [@Keep("클래스"), @Passed()]
  필드   : [@Keep("필드")]
  @Keep 의 value() = 클래스
--- @Inherited 는 클래스 상속에만 먹는다
  Sub 의 getAnnotations()         = [@Passed()]
  Sub 의 getDeclaredAnnotations() = []
```

**`Marked.class.getAnnotations()`** — **2개**(`@Keep`, `@Passed`).

- `@Gone`(CLASS)·`@Never`(SOURCE)는 **런타임에 아예 없다.** 정본은 [16 애너테이션](../16-annotations/).
- (애너테이션의 `toString` 이 비 ASCII 를 `\uXXXX` 로 이스케이프한다 — 값을 직접 부르면 `클래스` 가 나온다.)

**`Sub`**

- `getAnnotations()` = `[@Passed()]` — `@Inherited` 가 붙은 것만 상속된다.
- `getDeclaredAnnotations()` = `[]` — `Sub` 자신에게는 붙은 게 없다.

**`invoke` 가 던지면**

```text
--- 실제로 잡아야 하는 것
  InvocationTargetException 으로 감싸져 온다
  getCause() = java.lang.IllegalStateException: 안에서 터졌다
```

- 호출부가 받는 것은 **`InvocationTargetException`** 이다. 진짜 예외는 **`getCause()`** 에 있다.
- 이것을 또 감싸면 원인이 두 겹 아래로 내려간다.

```text
--- invoke 안에서 예외가 나면
  던져진 것 : java.lang.RuntimeException / java.lang.reflect.InvocationTargetException
  getCause() : java.lang.reflect.InvocationTargetException / null
```

**인자 타입이 안 맞으면**

```text
--- 인자 타입이 안 맞으면
  java.lang.IllegalArgumentException: argument type mismatch
```

- **비검사 예외**다. 그리고 메시지가 **어느 인자가 문제인지 말해 주지 않는다** — 직접 찍어 봐야 한다.

### 10. 비용

**출력** (`Ex.java (58-f)`, JDK 21.0.5 — 1000만 회 × 5 회, JMH 아님)

```text
  1회차  직접=   21 ms  invoke=  194 ms  setAccessible(true) 후 invoke=  136 ms
  2회차  직접=   33 ms  invoke=  167 ms  setAccessible(true) 후 invoke=  105 ms
  3회차  직접=    3 ms  invoke=   69 ms  setAccessible(true) 후 invoke=   65 ms
  4회차  직접=    3 ms  invoke=  176 ms  setAccessible(true) 후 invoke=   65 ms
  5회차  직접=    2 ms  invoke=   68 ms  setAccessible(true) 후 invoke=   64 ms
--- 필드 조회 자체의 비용 (getDeclaredField 100만 회)
  17 ms
```

**몇 배인가** — 안정 구간에서 **약 20\~30배**(직접 2\~3 ms 대 invoke 65\~69 ms).

- 두 번째 실행에서도 직접 3 ms, invoke 76\~89 ms 로 같은 자릿수였다.
- ★ **주의해서 읽어야 한다.** 이 배수의 대부분은 "리플렉션이 무겁다"보다\
  "**직접 호출이 JIT 인라인으로 거의 사라진다**"에서 온다. 배수를 절대 비용으로 옮겨 읽으면 안 된다.

**`setAccessible(true)` 를 미리 하면** — **조금 빨라진다**(69 → 65 ms 급).\
접근 검사를 매 호출마다 하지 않게 되기 때문이다.

**첫 회차가 느린 이유** — **JIT 웜업**이다. 인터프리터로 돌다가 핫스팟이 네이티브로 컴파일되기 전이다.

**`getDeclaredField` 100만 회 = 17 ms**(두 번째 실행 19 ms).

- 공짜가 아닌 이유: 호출마다 **`Field` 객체를 복사해서** 돌려준다.\
  (내부 캐시는 있지만, 호출자가 `setAccessible` 을 부를 수 있으므로 **복사본**을 준다.)
- 그래서 프레임워크는 `Field`·`Method` 를 **static 맵에 캐시**한다.

**재현되는 것**

| 재현된다 | 재현 안 된다 |
|---|---|
| **20\~30배**라는 자릿수 | 3 ms · 65 ms 같은 절댓값 |
| 세 방식의 **순서** | 회차별 정확한 ms(4회차가 176 ms 로 튀었다) |
| 웜업 전 회차가 느린 **모양** | 웜업이 끝나는 정확한 회차 |

### 11. 무엇이 계약이고 무엇이 구현인가

| 항목 | 계약 / 구현 |
|---|---|
| 예외 **타입** | **계약** — 각 메서드의 `@throws` |
| 예외 **메시지 문구** | **구현** — 17·21·25 에서 같았지만 보장이 아니다 |
| `getXxx`/`getDeclaredXxx` 의 범위 | **계약** |
| `Class.forName` 이 초기화를 시킨다 | **계약** |
| `setAccessible` 이 모듈에 막히는 것 | **언어·JEP 396/403** |
| 리플렉션의 배수 | **JIT·머신** |

**`getDeclaredFields()` 의 순서 — 보장되지 않는다.**

javadoc 원문(JDK 21.0.5 `Class.java`).

```text
The elements in the returned array are not sorted and are not in any
particular order.
```

- 이 문서의 출력은 **프로그램에서 정렬한 것**이다. 정렬하지 않으면 실행·버전마다 달라질 수 있다.
- 필드 순서에 의존하는 직렬화·매핑 코드는 이 문장 때문에 위험하다.

**`unnamed module @2f0e140b` 의 해시**

- **대조에 쓸 수 없다.** 같은 프로그램의 다른 실행에서 `@3b07d329`·`@659e0bfd` 로 계속 달랐다.
- 로그에 남겨도 "어느 모듈인가"를 구별하는 용도로만 쓸 수 있다.

**`InaccessibleObjectException` 이 비검사인 것의 함의**

- **컴파일은 통과하고 실행에서 터진다.** JDK 를 올려도 빌드가 멀쩡하다.
- 그래서 **JDK 업그레이드 시 컴파일 성공이 아무 보증이 아니다** — 통합 테스트로 실제 경로를 밟아야 드러난다.
- 라이브러리 안에서 나면 스택트레이스가 남의 코드라 **원인 파악이 더 늦어진다.**

### 12. 다른 주제와 잇기

**`import` 와 `Class.forName`**

- **아무 관계가 없다.** `import` 는 **컴파일 타임 약칭**이고 `forName` 은 **런타임 문자열**이다.
- `import java.util.List;` 를 아무리 넣어도 `Class.forName("List")` 는 `ClassNotFoundException` 이다.
- 정본은 [34 `import`](../34-imports/).

**`setAccessible` 이 우회하는 것**

- [10 접근 제어자](../10-access-modifiers/) 의 네 단계(`private`·package-private·`protected`·`public`)다.
- **모듈 경계는 그 위에 얹힌 두 번째 벽**이다 — `setAccessible` 은 첫 벽만 넘고, 두 번째 벽은 `opens` 가 필요하다.

**현대적 대안**

- **`MethodHandle`**(7+) · **`VarHandle`**(9+). `Lookup` 을 만들 때 접근 검사를 한 번 하고,\
  이후 호출은 JIT 가 인라인할 수 있어 더 빠르다.
- **모듈 경계는 똑같이 적용된다.** `MethodHandles.privateLookupIn(...)` 도 `opens` 가 있어야 한다.\
  즉 "빠른 리플렉션"이지 "벽을 넘는 리플렉션"이 아니다.
- (이 배치에서 `MethodHandle` 의 성능은 재지 않았다.)

**캐시하는 이유를 수치로**

- `getDeclaredField` 100만 회에 **17 ms** — 한 번이면 무시할 만하다.
- 그러나 요청마다 DTO 필드 20 개를 조회하면 요청당 20 회이고, 트래픽이 곱해진다.\
  여기에 `invoke` 비용(위 표에서 1000만 회에 65\~69 ms)이 더해진다 — **조회와 호출이 각각 쌓인다.**
- 그래서 프레임워크는 **시작할 때 한 번 조회해 `Field[]` 를 캐시**하고, 그 뒤로는 `get`/`set` 만 반복한다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex`(58-a) | `Class` 얻는 법 셋·동일성, `forName` 의 초기화 부작용과 끄는 법, 이름 3종 × 7 타입, `ClassNotFoundException` | 17 · 21 · 25 (**동일**) |
| `Ex`(58-b) | `getFields`/`getDeclaredFields`/`getMethods`/`getDeclaredMethods`/생성자, 상속된 private, `NoSuchField`·`NoSuchMethod`, `Modifier` | 17 · 21 · 25 (**동일**) |
| `Ex`(58-c) | setAccessible — 내 클래스 성공, `String`·`ArrayList`·`Unsafe` 실패, 메타데이터 조회 성공 | 17 · 21 · 25 (**동일**) |
| `Ex`(58-c) + `--add-opens` | `java.lang`·`java.util` 이 열리고 `jdk.internal.misc` 는 여전히 막힘 | 17 · 21 · 25 |
| `Ex`(58-c) + `--add-exports` | `jdk.internal.misc.Unsafe` 가 열림 | 21 |
| `Ex`(58-d) | 내 클래스의 `final` 필드 쓰기, 플래그 없/있 대비 | 21 |
| `Ex`(58-d2) + `--add-opens` | **상수 풀 오염** — `a` 를 고치니 `b` 도 바뀜 | 21 |
| `Ex`(58-e) `javap -v -p` | `getType` 대 `getGenericType`, `ParameterizedType`, `getGenericSuperclass`, **`Signature` 속성** | 17 · 21 · 25 (**동일**) |
| `Ex`(58-f) | 애너테이션 Retention 3종·`@Inherited`, `InvocationTargetException`, `argument type mismatch`, 비용 측정(2 회 실행) | 21 |
| `src.zip` 열람 | `Class.getDeclaredFields` javadoc(순서 미보장·상속 제외) | 21 |

- 프로그램 **7개**, 실행 왕복 **20회**(4개 × 3 JDK + 플래그 조건별 + 측정 반복), `javap -v -p` **1회**.

**구현에 의존하는 항목**

| 항목 | 무엇에 의존하나 |
|---|---|
| 예외 **메시지** | JDK 버전 |
| `unnamed module @...` 해시 | **실행마다 다르다** — 대조 불가 |
| `getDeclaredFields()` 의 **순서** | JDK 구현 — javadoc 이 미보장을 명시 |
| 모든 ms 값 | JIT·머신 — 재현되는 것은 자릿수 |
| `String` 의 선언 필드 11 개 | JDK 버전(내부 구현) |

**버전이 오르면 다시 돌려야 할 것**

- **`--add-opens`/`--add-exports` 가 여전히 동작하는지.** JEP 403 의 방향은 **플래그를 줄이는 쪽**이다.
- 예외 메시지 문구.
- `String` 의 내부 필드 구성(이미 9 에서 `char[]` → `byte[]` 로 바뀌었다).

## 안 돌려 본 것

- **`module-info.java` 를 둔 진짜 모듈**에서의 동작 — 이번 실행은 전부 클래스패스(이름 없는 모듈)다.
- **`MethodHandle`·`VarHandle`** 의 성능과 모듈 경계 — API 문서 수준으로만 적었다.
- `ServiceLoader` 를 통한 프로바이더 로딩.
- `SecurityManager` 가 관여하는 경로 — JDK 17 에서 deprecate 됐고 이 배치의 범위 밖이다.
- `Class.forName` 의 **클래스로더별** 동작(같은 이름이 로더마다 다른 `Class` 가 되는 것) — 정본은 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3.
