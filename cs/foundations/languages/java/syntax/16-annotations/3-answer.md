# java/syntax/16 — 애너테이션: 선언·`@Retention`·`@Target`·메타 애너테이션 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·클래스 파일 덤프는 **Temurin JDK 21.0.5 에서 실제로 돌려 얻은 것**이다.\
> 실행 프로그램은 **17.0.13 · 25.0.1** 에서도 돌렸고, 달라진 것은 **`Annotation.toString()` 의 형식**뿐이었다(11번).\
> 클래스 파일 덤프는 `javap -v -p` 출력을, javadoc 은 `lib/src.zip` 의 실파일을 그대로 옮겼다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 `@Retention` 은 각각 어디까지 살아남는가

**출력** (`Ex.java (16-a)`, JDK 21.0.5)

```text
--- getAnnotations() 가 실제로 돌려준 것
개수 = 1
  @Ex.KeepAtRuntime("C")
--- 하나씩 조회
SOURCE  -> null
CLASS   -> null
RUNTIME -> @Ex.KeepAtRuntime("C")
--- isAnnotationPresent
SOURCE  = false
CLASS   = false
RUNTIME = true
```

**왜 그런가**

셋을 다 붙였는데 런타임에 보이는 것은 **하나**다. 클래스 파일을 열면 나머지 둘의 행방이 갈린다.

**`javap -v -p Ex$Three.class` 출력 그대로**

```text
RuntimeVisibleAnnotations:
  0: #14(#15=s#16)
    Ex$KeepAtRuntime(
      value="C"
    )
RuntimeInvisibleAnnotations:
  0: #18(#15=s#19)
    Ex$KeepInClass(
      value="B"
    )
```

```text
              Ex.java   ──javac──>   Ex$Three.class            ──리플렉션──>
  SOURCE      @KeepInSource("A")     (아무 속성에도 없다)          못 읽는다
  CLASS       @KeepInClass("B")      RuntimeInvisibleAnnotations  못 읽는다
  RUNTIME     @KeepAtRuntime("C")    RuntimeVisibleAnnotations    읽는다
```

**`KeepInSource` 가 클래스 파일에 남아 있는가** — 아니다. 상수 풀까지 훑었다.

```text
$ javap -v -p 'Ex$Three.class' | grep -c 'KeepInSource'
0
```

- `SOURCE` 는 javac 가 **버린다** — javadoc: "Annotations are to be discarded by the compiler."
- `CLASS` 는 **파일에는 남되 JVM 이 노출하지 않는다** — javadoc: "recorded in the class file by the compiler but need not be retained by the VM at run time."
- 속성 이름의 `Visible`/`Invisible` 은 **런타임 가시성**을 뜻한다. 이 둘이 이 주제의 핵심 증거다.

애너테이션 **타입 자체**는 셋 다 살아 있다 — 지워지는 것은 **붙인 흔적**이지 타입이 아니다.

```text
KeepInSource.class  = interface Ex$KeepInSource
KeepInClass.class   = interface Ex$KeepInClass
KeepAtRuntime.class = interface Ex$KeepAtRuntime
isAnnotation = true
KeepInSource 의 @Retention = @java.lang.annotation.Retention(SOURCE)
```

### 2. `@Retention` 을 안 적으면 무슨 일이 생기나

**출력** (`Ex.java (16-f)`, JDK 21.0.5)

```text
@Retention 없는 애너테이션을 런타임에 읽으면
  getAnnotations() = []
  즉 기본 보존 정책 = CLASS (javadoc: This is the default behavior)
@Target 없는 애너테이션은 어디에 붙었나 = 클래스·필드·메서드·파라미터·지역변수·생성자 전부 컴파일됐다
```

**왜 그런가**

**`javap -v -p Ex$C.class` 출력 그대로**

```text
    RuntimeInvisibleAnnotations:
      0: #12(#13=s#14)
        Ex$NoMeta(
          value="on-field"
        )
```

- 기본값이 **`CLASS`** 다 — `RetentionPolicy.CLASS` javadoc 이 "This is the default behavior" 라고 적었다.
- 그래서 **클래스 파일에는 멀쩡히 들어 있고**(`RuntimeInvisibleAnnotations`) **리플렉션만 못 읽는다.**

```text
"안 붙였다" 와 "못 읽는다" 는 다르다

  javap 로 보면                          리플렉션으로 보면
  +------------------------------+      +------------------------------+
  | RuntimeInvisibleAnnotations  |      | getAnnotations() -> []       |
  |   Ex$NoMeta(value="on-field")|      | isAnnotationPresent -> false |
  +------------------------------+      +------------------------------+
     붙어 있다                              없는 것과 구별이 안 된다
```

**`@Target` 을 안 적으면** — 클래스·필드·메서드·파라미터·지역 변수·생성자 여섯 자리에 붙였고 **전부 컴파일됐다.**

**어느 위치에 남았나** — 세 자리를 세어 확인했다.

```text
$ javap -v -p 'Ex$C.class' | grep -c 'on-local'   ->  0
$ javap -v -p 'Ex$C.class' | grep -c 'on-param'   ->  2
$ javap -v -p 'Ex$C.class' | grep -c 'on-ctor'    ->  2
```

**무음 실패가 되는 이유** — 오타도, 컴파일 에러도, 경고도 없다.\
`getAnnotation()` 이 `null` 을 돌려주고, 프레임워크는 "이 클래스에는 표시가 없구나"라고 정상 동작한다.\
`javap -v` 로 `RuntimeInvisibleAnnotations` 가 보이면 **정확히 이 상황**이다.

### 3. `@Target` 이 막는 것

**출력** (`Ex.java (16-b)` `javac`, JDK 21.0.5)

```text
Ex.java:9: error: annotation interface not applicable to this kind of declaration
    @MethodOnly                 // (A) 클래스에 붙였다
    ^
Ex.java:14: error: annotation interface not applicable to this kind of declaration
        @MethodOnly int field;      // (C) 필드에 붙였다
        ^
2 errors
```

**왜 그런가**

- (A) 클래스와 (C) 필드가 막히고 **(B) 메서드만 통과**했다. `@Target(ElementType.METHOD)` 하나가 한 일이다.
- `@Target` 은 **컴파일 타임 검사**다. 런타임 동작과는 무관하다.

**JDK 17 과 21 에서 같은가** — 아니다.

```text
JDK 17.0.13
  error: annotation type not applicable to this kind of declaration

JDK 21.0.5 · 25.0.1
  error: annotation interface not applicable to this kind of declaration
```

**`ElementType` 의 상수와 도입 버전** (`Ex.java (16-e)` 출력 + `src.zip` 의 `@since`)

```text
[TYPE, FIELD, METHOD, PARAMETER, CONSTRUCTOR, LOCAL_VARIABLE, ANNOTATION_TYPE, PACKAGE, TYPE_PARAMETER, TYPE_USE, MODULE, RECORD_COMPONENT]
```

| 상수 | `@since` |
|---|---|
| `TYPE` `FIELD` `METHOD` `PARAMETER` `CONSTRUCTOR` `LOCAL_VARIABLE` `ANNOTATION_TYPE` `PACKAGE` | 1.5 |
| `TYPE_PARAMETER` `TYPE_USE` | **1.8** |
| `MODULE` | **9** |
| `RECORD_COMPONENT` | **16** |

**12개**이고, Java 5 이후에 넷이 추가됐다. `@since` 는 `ElementType.java` 실파일에서 읽었다.

### 4. 애너테이션 원소로 쓸 수 있는 타입

**출력** (`Ex.java (16-d1)` `javac`, JDK 21.0.5)

```text
Ex.java:6: error: invalid type for annotation interface element
        List<String> names();     // (A) 컬렉션은 되나?
            ^
Ex.java:7: error: invalid type for annotation interface element
        Object any();             // (B) Object 는?
        ^
Ex.java:9: error: invalid type for annotation interface element
        String[][] deep();        // (D) 2차원 배열은?
              ^
3 errors
```

**왜 그런가**

(A)(B)(D)가 에러이고 **(C) `int[]` 만 통과**했다.

```text
애너테이션 원소로 쓸 수 있는 타입 (JLS §9.6.1)

  +--------------------------------+        +--------------------------------+
  | 된다                            |        | 안 된다                         |
  | - 기본형 (int, boolean, ...)    |        | - Object                       |
  | - String                       |        | - List<String> 같은 컬렉션      |
  | - Class 또는 Class<?>          |        | - 임의의 클래스 (Date 등)       |
  | - enum 타입                    |        | - 2차원 이상 배열               |
  | - 다른 애너테이션 타입          |        | - 자기 자신을 순환 참조         |
  | - 위 여섯의 **1차원** 배열      |        |                                |
  +--------------------------------+        +--------------------------------+
```

여섯 종류를 다 담은 애너테이션을 실제로 만들어 돌렸다(`Ex.java (16-c)`).

```text
name    = minimal
order   = 10
level   = LOW
tags    = []
handler = class java.lang.Object
nested  = @java.lang.annotation.Retention(CLASS)
```

**왜 그 목록으로 제한되는가**

- 애너테이션 값은 **클래스 파일의 상수 풀에 그대로 박힌다.** 실행 코드가 아니라 상수다.
- 상수 풀에 표현할 수 있는 것은 **수·문자열·클래스 참조·enum 상수·중첩 애너테이션**뿐이다.
- 그래서 `new Object()` 처럼 **런타임에 만들어야 하는 값**은 못 담는다.
- 2차원 배열이 안 되는 것도 같은 이유다 — 클래스 파일의 `element_value` 배열은 **한 겹**만 정의돼 있다(JVMS §4.7.16.1).

### 5. 애너테이션 선언에서 안 되는 것들

**출력** (`Ex.java (16-d2)` `(16-d3)` `(16-d4)` `javac`, JDK 21.0.5)

```text
Ex.java:3: error: annotation @Need is missing a default value for the element 'order'
    @Need("x")                    // order 를 안 줬다
    ^
1 error
```

```text
Ex.java:3: error: 'extends' not allowed for @interfaces
    @interface Derived extends Base { }     // 애너테이션이 상속할 수 있나
                               ^
1 error
```

```text
Ex.java:3: error: element value must be a constant expression
    @interface DefaultNull { String v() default null; }
                                                ^
Ex.java:2: error: type of element Cyclic is cyclic
    @interface Cyclic { Cyclic self(); }    // 자기 자신을 원소로
                               ^
Ex.java:4: error: throws clause not allowed in @interface members
    @interface Thrown { String v() throws Exception; }
                                          ^
Ex.java:5: error: elements in annotation interface declarations cannot declare formal parameters
    @interface Param { String v(int i); }
                                    ^
Ex.java:6: error: annotation interface Generic cannot be generic
    @interface Generic<T> { String v(); }
                       ^
5 errors
```

**왜 그런가**

| 자리 | 결과 | 핵심 |
|---|---|---|
| (A) 필수 원소 생략 | 에러 | `default` 가 없는 원소는 **사용할 때 반드시** 준다 |
| (B) `extends` | 에러 | 애너테이션은 상속 계층을 만들 수 없다 |
| (C) `default null` | 에러 | 기본값도 **컴파일 타임 상수**여야 한다 |
| (D) 순환 참조 | 에러 | 값이 상수 풀에 유한하게 박혀야 한다 |
| (E) `throws` | 에러 | 원소는 메서드처럼 생겼지만 **호출되는 코드가 아니다** |
| (F) 파라미터 | 에러 | 같은 이유 — 값을 꺼내는 이름일 뿐이다 |
| (G) 제네릭 | 에러 | 타입 인자를 상수로 박을 방법이 없다 → [`../19-type-erasure/`](../19-type-erasure/) 와 이어진다 |

**무엇을 상속하는가** — `java.lang.annotation.Annotation` 하나다. 실행으로 확인했다.

```text
Meta 가 상속한 것  = [interface java.lang.annotation.Annotation]
```

**"값 없음"을 표현하려면** — `null` 을 못 쓰므로 다음 중 하나를 쓴다.

- 빈 문자열 `default ""`
- 빈 배열 `default {}`
- 전용 enum 상수 (`Level.UNSET` 같은 것)
- 표준 라이브러리가 쓰는 관용구 — `Class<?> handler() default Object.class;` 처럼 **"의미 없는 기본 타입"**

### 6. `@Repeatable` 을 두 번 붙이면 런타임에 무엇으로 보이나

**출력** (`Ex.java (16-c)`, JDK 21.0.5)

```text
--- @Repeatable: 두 번 붙이면 무엇이 저장되나
getAnnotation(Role.class)  = null
getAnnotation(Roles.class) = @Ex.Roles({@Ex.Role("admin"), @Ex.Role("user")})
getAnnotationsByType(Role) = [@Ex.Role("admin"), @Ex.Role("user")]
getAnnotations() 전체      = [@Ex.Roles({@Ex.Role("admin"), @Ex.Role("user")})]
--- 한 번만 붙이면
getAnnotation(Role.class)  = @Ex.Role("single")
getAnnotation(Roles.class) = null
getAnnotationsByType(Role) = [@Ex.Role("single")]
```

**왜 그런가**

```text
개수에 따라 저장 형태가 갈린다

  두 번 붙였을 때                       한 번 붙였을 때
  +-----------------------------+      +-----------------------------+
  | @Role("admin")              |      | @Role("single")             |
  | @Role("user")               |      |                             |
  |          |                  |      |          |                  |
  |          v javac            |      |          v javac            |
  | @Roles({@Role, @Role})      |      | @Role("single")             |
  |   Role 은 직접 없다          |      |   Roles 는 없다              |
  +-----------------------------+      +-----------------------------+
    getAnnotation(Role) -> null          getAnnotation(Roles) -> null
```

- `@Repeatable(Roles.class)` 는 **javac 에게 컨테이너를 알려 주는 것**이다. 새 저장 방식이 생긴 게 아니다.
- **두 번 이상**이면 컨테이너로 감싸고, **한 번**이면 안 감싼다.
- 그래서 `getAnnotation()` 은 **어느 쪽을 물어도 절반은 `null`** 이다.

**읽는 코드가 써야 할 API** — **`getAnnotationsByType(Role.class)`**(Java 8, `@since 1.8` 을 `AnnotatedElement.java` 에서 확인).\
개수에 상관없이 `Role[]` 을 돌려준다. 위 출력에서 두 경우 다 제대로 나왔다.

### 7. `@Inherited` 는 어디까지 도는가

**출력** (`Ex.java (16-c)`, JDK 21.0.5)

```text
--- @Inherited: 자식이 물려받나
Child getAnnotation(Inheritable)    = @Ex.Inheritable("from-parent")
Child getAnnotation(NotInheritable) = null
Child getAnnotations()              = [@Ex.Inheritable("from-parent")]
Child getDeclaredAnnotations()      = []
```

**왜 그런가**

- `getAnnotation()` 은 찾고 `getDeclaredAnnotations()` 는 **빈 배열**이다 — 자식이 실제로 가진 게 아니라 **조회가 거슬러 올라간 것**이다.
- javadoc 이 그 동작을 그대로 적어 두었다 — "the class's superclass will automatically be queried for the annotation interface. This process will be repeated until ... the top of the class hierarchy (Object) is reached."

**인터페이스에서는** (`Ex.java (16-f)`)

```text
@Inherited 가 인터페이스에서도 도나
  FromInterface getAnnotation(Inh) = null
  I 자신 getAnnotation(Inh)        = @Ex.Inh("on-interface")
```

```text
상속 경로 두 개 — 한쪽만 통한다

  @Inheritable                          @Inh (인터페이스에 붙임)
  class Parent                          interface I
      ^                                     ^
      | extends                             | implements
      |                                      |
  class Child                           class FromInterface

  Child.getAnnotation      -> 찾는다     FromInterface.getAnnotation -> null
```

javadoc 이 못박는다 — "annotations on **implemented interfaces have no** [effect]."

**메서드에 붙인 애너테이션에 `@Inherited` 를 달면** (`Ex.java (16-h)`)

```text
Child 가 물려받은 m() 을 찾으면
  선언 클래스 = Parent
  애너테이션  = [@Ex.InhMethod("from-parent-method")]
재정의한 쪽의 m()
  애너테이션  = []
```

- 앞 줄의 애너테이션은 **`@Inherited` 덕이 아니다.** `Child.class.getMethod("m")` 이 돌려준 `Method` 객체의 선언 클래스가 **`Parent`** 이기 때문이다.
- 재정의한 쪽(`Override2.m()`)에는 **아무것도 안 붙는다** — 애너테이션은 재정의로 전파되지 않는다.
- javadoc: "has no effect if the annotated interface is used to annotate **anything other than a class**."

### 8. 지역 변수에 붙인 런타임 애너테이션은 읽히는가

**출력** (`Ex.java (16-e)`, `javac -parameters`, JDK 21.0.5)

```text
--- 필드
field 애너테이션 = [@Ex.Mark("field")]
--- 메서드와 파라미터
method 애너테이션 = [@Ex.Mark("method")]
  a -> [@Ex.Mark("param")]
  b -> []
--- 지역 변수 애너테이션을 리플렉션으로 읽는 API 가 있나
Method 에 getLocalVariable* 메서드 개수 = 0
--- TYPE_USE 는 따로 읽는다
반환 타입 = @Ex.NonNull() java.lang.String
반환 타입의 애너테이션 = [@Ex.NonNull()]
t.getAnnotations() = []
```

**왜 그런가**

**읽히는 것은 필드·메서드·파라미터 셋**이고 **지역 변수는 아니다.** 클래스 파일을 세어 확인했다.

```text
$ javap -v -p e/Ex.class | grep -c 'local-var'
0
```

```text
같은 메서드 안에서 갈린다

    @Mark("method")
    void work(@Mark("param") int a, int b) {
        @Mark("local-var") int x = 1;        <- 클래스 파일에 없다
        @NonNull String s = "";              <- TYPE_USE 라서 남는다
    }

  RuntimeVisibleAnnotations:          value="method"    남음
  RuntimeVisibleParameterAnnotations: value="param"     남음
  (지역 변수 선언 애너테이션)                             없음
  RuntimeVisibleTypeAnnotations:      LOCAL_VARIABLE     남음  <- TYPE_USE 쪽
```

**각각 어느 속성인가**

| 붙인 자리 | 클래스 파일 속성 | 읽는 API |
|---|---|---|
| 클래스·필드·메서드·생성자 | `RuntimeVisibleAnnotations` | `getAnnotations()` |
| 파라미터 | `RuntimeVisibleParameterAnnotations` | `Parameter.getAnnotations()` |
| 타입 사용(`TYPE_USE`) | `RuntimeVisibleTypeAnnotations` | `getAnnotatedReturnType()` 등 |
| 지역 변수 **선언** | **(없음)** | **(없음)** |

**`@Target(TYPE_USE)` 를 지역 변수 타입에 붙이면**

```text
      RuntimeVisibleTypeAnnotations:
        0: #165(): LOCAL_VARIABLE, {start_pc=6, length=15, index=4}
          Ex$NonNull
```

- **바이트코드 오프셋과 함께 남는다.** `start_pc`·`length`·`index` 가 그 지역 변수 슬롯이 살아 있는 구간이다.
- 다만 이것을 읽는 **표준 리플렉션 API 는 없다.** 바이트코드를 직접 읽는 도구(널 분석기 등)가 쓴다.
- 그리고 `TYPE_USE` 애너테이션은 `getAnnotations()` 로 **안 나온다** — 출력의 `t.getAnnotations() = []` 가 그 확인이다.

**파라미터 이름이 `a` 로 나오려면** — `javac -parameters` 로 컴파일해야 한다(그러면 `MethodParameters` 속성이 생긴다).\
없으면 `arg0`·`arg1` 로 나온다.

### 9. `getAnnotation()` 이 돌려준 객체의 정체

**출력** (`Ex.java (16-a)` `(16-c)`, JDK 21.0.5)

```text
value()        = C
k.getClass()   = $Proxy1
annotationType = interface Ex$KeepAtRuntime
k instanceof KeepAtRuntime = true
```

```text
--- 애너테이션 인스턴스의 equals/hashCode
같은 객체 = true
equals    = true
hashCode 같음 = true
MinimalUse.equals(FullUse) = false
```

**왜 그런가**

```text
애너테이션 타입은 인터페이스다

  interface Ex$KeepAtRuntime  extends  java.lang.annotation.Annotation
        ^
        | 구현
  class $Proxy1               <- 리플렉션이 런타임에 만들어 주는 동적 프록시

  k.getClass()      -> class $Proxy1          (구현 클래스)
  k.annotationType()-> interface Ex$KeepAtRuntime  (애너테이션 타입)
```

- 애너테이션 타입을 알고 싶으면 **`getClass()` 가 아니라 `annotationType()`** 을 써야 한다.\
  프레임워크 코드가 `getClass()` 로 분기하면 `$Proxy1`·`$Proxy2` … 가 나와 전부 빗나간다.
- `instanceof` 는 정상 동작한다 — 프록시가 그 인터페이스를 구현하기 때문이다.

**같은 조회를 두 번 하면 `==` 가 참인가** — 이 실행에서는 참이었다.\
**그러나 믿으면 안 된다.** 캐싱은 `java.lang.Class` 의 구현 세부이고, javadoc 이 동일 인스턴스를 보장하지 않는다.\
비교는 항상 `equals` 로 한다.

**`equals` 가 비교하는 것** — **원소 값들**이다. `Annotation.equals` javadoc 이 계약으로 정의한다.\
출력의 마지막 줄이 그 확인이다 — 같은 타입이지만 원소 값이 다른 `MinimalUse`/`FullUse` 의 애너테이션은 `false` 다.

### 10. 표준 애너테이션들의 `@Retention`

**출력** (`Ex.java (16-g)`, JDK 21.0.5)

```text
@Override              @Retention=SOURCE   @Target=[METHOD]
@Deprecated            @Retention=RUNTIME  @Target=[CONSTRUCTOR, FIELD, LOCAL_VARIABLE, METHOD, PACKAGE, MODULE, PARAMETER, TYPE]
@SuppressWarnings      @Retention=SOURCE   @Target=(없음)
@SafeVarargs           @Retention=RUNTIME  @Target=[CONSTRUCTOR, METHOD]
@FunctionalInterface   @Retention=RUNTIME  @Target=[TYPE]
@Retention             @Retention=RUNTIME  @Target=[ANNOTATION_TYPE]
@Target                @Retention=RUNTIME  @Target=[ANNOTATION_TYPE]
@Documented            @Retention=RUNTIME  @Target=[ANNOTATION_TYPE]
@Inherited             @Retention=RUNTIME  @Target=[ANNOTATION_TYPE]
@Repeatable            @Retention=RUNTIME  @Target=[ANNOTATION_TYPE]
```

**왜 그런가**

- **`@Override`·`@SuppressWarnings` 만 `SOURCE`** 다 — 둘 다 **컴파일러만 읽으면 끝나는** 표시다.
- `@Deprecated`·`@SafeVarargs`·`@FunctionalInterface` 는 `RUNTIME` 이라 위처럼 리플렉션으로 읽힌다.

**`@SuppressWarnings` 의 `@Target` 이 없는 이유** — 일부러다. `src.zip` 의 선언 바로 위에 주석이 있다.

```java
// Implicitly target all declaration contexts by omitting a @Target annotation
@Retention(RetentionPolicy.SOURCE)
public @interface SuppressWarnings {
```

2번에서 본 **"`@Target` 을 안 적으면 거의 어디에나 붙는다"**는 규칙을 표준 라이브러리가 일부러 쓰고 있는 자리다.

**메타 애너테이션 다섯** — 전부 `@Retention(RUNTIME)` + `@Target(ANNOTATION_TYPE)` 이다.\
그래서 애너테이션 타입 선언에만 붙고, 위 프로그램처럼 런타임에 읽을 수 있다.

### 11. 애너테이션의 `toString()` 을 믿어도 되는가

**출력** (`Ex.java (16-c)`, 세 JDK 를 나란히)

```text
JDK 17.0.13
  @Ex$Meta(handler=java.lang.Object.class, level=LOW, nested=@java.lang.annotation.Retention(CLASS), order=10, tags={}, name="minimal")

JDK 21.0.5
  @Ex.Meta(handler=java.lang.Object.class, level=LOW, nested=@java.lang.annotation.Retention(CLASS), order=10, tags={}, name="minimal")

JDK 25.0.1
  @Ex.Meta(handler=java.lang.Object.class, nested=@java.lang.annotation.Retention(CLASS), level=LOW, tags={}, order=10, name="minimal")
```

**왜 그런가**

- 17 → 21 에서 **타입 이름 표기**가 `Ex$Meta` → `Ex.Meta` 로 바뀌었다(내부 이름 → canonical 이름).
- 21 → 25 에서 **원소가 찍히는 순서**가 바뀌었다.
- 나머지 출력(값 자체, `getAnnotation` 의 결과, `javap` 의 속성 이름)은 세 JDK 에서 같았다.\
  **관찰이지 보장이 아니다.**

**그래서 하면 안 되는 것**

- `toString()` 을 **파싱**하는 것.
- 테스트에서 `assertEquals("@Meta(...)", ann.toString())` 처럼 **문자열로 단언**하는 것.
- 로그 포맷을 `toString()` 에 의존해 **고정으로 가정**하는 것.

값이 필요하면 **원소 메서드를 직접 부른다**(`ann.name()`). 비교가 필요하면 `equals` 를 쓴다.

한 가지 더 — 애너테이션 값에 **비 ASCII 문자**가 들어 있으면 `toString()` 이 `\uXXXX` 로 이스케이프해서 찍는다.\
한글 값을 넣고 로그를 읽으면 사람이 못 읽는다는 뜻이다(이 문서의 예제는 그래서 값을 전부 ASCII 로 썼다).

### 12. 무엇을 골라야 하나

| 읽을 주체 | `@Retention` | 이유 |
|---|---|---|
| 프레임워크·DI·직렬화·테스트 러너 (리플렉션) | **`RUNTIME`** | 리플렉션이 읽는 유일한 정책 |
| 애너테이션 프로세서(APT) | **`SOURCE`** | 컴파일 중에만 읽는다. 클래스 파일을 안 키운다 |
| 바이트코드 분석기·계측 도구 | **`CLASS`** | 파일에는 있어야 하고 런타임 노출은 필요 없다 |
| 컴파일러·IDE 린터만 | **`SOURCE`** | `@Override` 가 그 예다 |

**애너테이션에 런타임에 바뀌는 값을 담을 수 있는가** — 못 담는다.

- 4번에서 본 대로 값은 **컴파일 타임 상수**여야 하고 **클래스 파일의 상수 풀에 박힌다.**
- 그래서 `default null` 도 안 되고(`element value must be a constant expression`), `new Date()` 같은 것도 안 된다.
- 바뀌는 값이 필요하면 **애너테이션에는 키만 담고**, 값은 설정 파일·환경 변수에서 읽는다.

### 13. 다른 주제와 잇기

**애너테이션이 제네릭이 될 수 없는 이유**

```text
Ex.java:6: error: annotation interface Generic cannot be generic
    @interface Generic<T> { String v(); }
                       ^
```

- 애너테이션은 **값이 클래스 파일에 상수로 박히는 것**이고, 타입 인자는 **클래스 파일에서 지워지는 것**이다.
- 둘은 정반대 성질이라 같이 설 수 없다. 정본은 [`../19-type-erasure/`](../19-type-erasure/) 다.

**"지워지는 것"과 "속성으로 남는 것"이라는 구조를 공유하는 주제**

- [`../19-type-erasure/`](../19-type-erasure/) 다. 구조가 정확히 같다.

```text
같은 질문, 다른 대상

  16 애너테이션                          19 타입 소거
  +------------------------------+      +------------------------------+
  | 소스에 @Foo 를 썼다           |      | 소스에 List<String> 을 썼다   |
  |   |                          |      |   |                          |
  |   v javac                    |      |   v javac                    |
  | RuntimeVisibleAnnotations?   |      | descriptor 는 List (지워짐)   |
  |   또는 아무것도 없음          |      | Signature 에는 List<String>  |
  +------------------------------+      +------------------------------+
    @Retention 이 갈림길              항상 둘 다 (descriptor + Signature)
```

- 둘 다 **"javac 가 클래스 파일에 무엇을 적었나"**로 답이 나온다. 확인 도구도 같은 `javap -v` 다.
- 그리고 **둘 다 리플렉션에서 만난다** — 목록의 **58번 주제**(리플렉션)가 그 합류 지점이다.

**`ElementType.RECORD_COMPONENT` 가 16에서 생긴 이유**

- `record` 자체가 **Java 16 에서 정식화**됐다(`@since 16` 을 `ElementType.java` 에서 확인).
- record 컴포넌트는 필드도 파라미터도 메서드도 아닌 **새로운 선언 종류**라, 붙일 자리를 나타내는 상수가 새로 필요했다.
- record 쪽 정본은 [`../14-records/`](../14-records/) 이고, 도입 연혁은 [`../../../../../../history/java/java-16.md`](../../../../../../history/java/java-16.md) 다.

---

## 이 주제를 확인한 실행 목록

| 프로그램 | 무엇을 확인했나 | 돌린 JDK |
|---|---|---|
| `Ex.java (16-a)` | 세 `@Retention` 의 리플렉션 조회, 애너테이션 타입 자신은 남는 것, 프록시 정체 | 17 · 21 · 25 (`toString` 표기만 다름) |
| `Ex.java (16-a)` `javap -v -p` | `RuntimeVisibleAnnotations` 대 `RuntimeInvisibleAnnotations`, `SOURCE` 가 상수 풀에도 없는 것 | 21 |
| `Ex.java (16-b)` `javac` | `@Target(METHOD)` 위반 두 자리의 에러 메시지 | 17 · 21 · 25 (**17 만 문구가 다름**) |
| `Ex.java (16-c)` | 원소 여섯 종류와 기본값, `@Repeatable` 의 개수별 저장, `@Inherited`, `equals`/`hashCode`, 메타 애너테이션 조회 | 17 · 21 · 25 (`toString` 표기·원소 순서만 다름) |
| `Ex.java (16-d1)` `javac` | 원소 타입 제한 — `List`·`Object`·2차원 배열이 에러, `int[]` 는 통과 | 21 |
| `Ex.java (16-d2)` `javac` | 필수 원소 누락 | 21 |
| `Ex.java (16-d3)` `javac` | `extends` 금지 | 21 |
| `Ex.java (16-d4)` `javac` | `default null`·순환 참조·`throws`·파라미터·제네릭 금지 | 21 |
| `Ex.java (16-e)` | 필드·메서드·파라미터·`TYPE_USE` 조회, `ElementType`·`RetentionPolicy` 전체 목록 | 17 · 21 · 25 (`toString` 표기만 다름) |
| `Ex.java (16-e)` `javap -v -p` | 네 종류 속성의 위치, 지역 변수 선언 애너테이션이 **없는** 것, `TYPE_USE` 의 `LOCAL_VARIABLE` 타깃 | 21 |
| `Ex.java (16-f)` | `@Retention` 기본값이 `CLASS`, `@Target` 없으면 여섯 자리에 다 붙는 것, `@Inherited` 가 인터페이스에 무효 | 17 · 21 · 25 (`toString` 표기만 다름) |
| `Ex.java (16-g)` | 표준 애너테이션 다섯 + 메타 애너테이션 다섯의 `@Retention`·`@Target` | 21 |
| `Ex.java (16-h)` | `@Inherited` 를 메서드 애너테이션에 달았을 때 — 재정의로는 전파되지 않음 | 21 |
| `Ex.java (16-i)` `javac` + 실행 | `@Target(TYPE_USE)` 만 준 애너테이션이 클래스·필드·메서드에서 각각 어느 API 로 읽히나, `void` 반환에는 못 붙는 것 | 21 |
| `Ex.java (16-j)` + `javap -v -p` | 기본값은 `AnnotationDefault` 에 살고 쓰는 쪽에는 안 박히는 것(애너테이션만 재컴파일해도 반영된다), 직접 준 값은 쓰는 쪽에 박히는 것 | 21 |
| `src.zip` 열람 | `java/lang/annotation/*.java` 의 `@since`, `ElementType` 상수별 `@since`, `RetentionPolicy`·`Inherited` javadoc, `SuppressWarnings` 의 `@Target` 생략 주석 | 21 |

**구현 의존 항목** — `Annotation.toString()` 의 형식과 원소 순서, `getClass()` 가 `$Proxy1` 인 것, 같은 조회가 같은 객체를 주는 것, `javac` 에러 문구는 **전부 구현 세부**다.\
버전이 올랐을 때 다시 돌려 볼 것은 이 표의 **`(16-b)`·`(16-c)`** 둘이다 — 에러 문구와 `toString` 형식이 걸려 있다.\
반면 `@Retention` 세 값의 의미, `@Target` 이 자리를 막는 것, 원소 타입 제한, `@Inherited` 의 범위는 JLS·javadoc·JVMS 가 보장한다.
