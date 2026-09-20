# java/syntax/16 — 애너테이션: 선언·`@Retention`·`@Target`·메타 애너테이션 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [JLS SE 21 §9.6 Annotation Interfaces](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html) · [§9.7 Annotations](https://docs.oracle.com/javase/specs/jls/se21/html/jls-9.html) · [JVMS SE 21 §4.7.16~4.7.20 (애너테이션 속성)](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html) · [`java.lang.annotation` API 문서](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/annotation/package-summary.html) · JDK 21.0.5 표준 라이브러리 소스 `java.base/java/lang/annotation/*.java`(`lib/src.zip`).
> **실행 검증** — 이 문서의 모든 출력·에러·클래스 파일 덤프는 Temurin **JDK 21.0.5** 에서 실제로 돌려 얻은 것이다.\
> `Ex.java (16-a)` `(16-c)` `(16-e)` `(16-f)` 는 **17.0.13 · 21.0.5 · 25.0.1** 에서 다 돌렸다.\
> 세 JDK 에서 **`Annotation.toString()` 의 형식이 두 번 바뀌었다**(아래 「구현 세부사항 대 언어 보장」). 나머지 출력은 같았다.\
> **"세 곳에서 같았다"는 관찰이지 보장이 아니다** — 보장은 JLS·javadoc 인용으로만 적었다.
> **버전** — 애너테이션 자체는 **Java 5**. `@Repeatable` · `ElementType.TYPE_USE` · `TYPE_PARAMETER` 는 **8**,
> `ElementType.MODULE` 은 **9**, `ElementType.RECORD_COMPONENT` 는 **16** 부터다(`src.zip` 의 `@since` 를 직접 읽었다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 JLS·JVMS·javadoc 으로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**애너테이션은 "코드에 붙이는 포스트잇"이고, `@Retention` 은 그 포스트잇이 언제 떨어지는지를 정한다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 포스트잇 | 애너테이션 한 개 (`@Override`, `@Test` …) |
| 포스트잇에 적힌 칸(제목·기한) | 애너테이션 원소(element) — `name()`·`order()` |
| 포스트잇을 붙일 수 있는 자리(문·서랍·서류) | `@Target` — 클래스·메서드·필드 … |
| 포스트잇이 언제까지 붙어 있나 | `@Retention` — 원고까지 / 사본까지 / 현장까지 |
| 원고 (소스) | `.java` 파일 |
| 복사본 (클래스 파일) | `.class` 파일 |
| 현장에서 읽는 사람 | 런타임의 리플렉션 |
| 포스트잇 양식 자체에 붙인 포스트잇 | 메타 애너테이션 (`@Retention` 은 `@Retention` 에도 붙어 있다) |

- 포스트잇에는 **세 가지 수명**이 있다.\
  `SOURCE` 는 **원고에만** 붙어 있다가 복사할 때 떨어진다.\
  `CLASS` 는 **복사본에는 붙어 가지만** 현장에 가져가지 않는다.\
  `RUNTIME` 은 **현장까지 따라가서** 읽힌다.
- 애너테이션은 **스스로 아무 일도 하지 않는다.** 읽어서 행동하는 쪽(컴파일러·애너테이션 프로세서·프레임워크)이 따로 있다.
- 그래서 `@Retention` 을 잘못 고르면 **에러 한 줄 없이 아무 일도 안 일어난다.**

```text
@Retention 세 값이 각각 어디까지 살아남나

  Ex.java  ──javac──>  Ex.class  ──JVM 로드──>  리플렉션으로 조회

  SOURCE   [O]           [ ]                      [ ]     <- javac 가 버린다
  CLASS    [O]           [O]                      [ ]     <- 파일엔 있는데 못 읽는다
  RUNTIME  [O]           [O]                      [O]     <- 여기까지 온다
```

**똑같은 구조로** Java 가 동작한다: 포스트잇 = 애너테이션, 원고 = `.java`, 복사본 = `.class`, 현장의 독자 = 리플렉션.

실무에서 이게 물리는 자리는 **직접 만든 애너테이션을 프레임워크가 못 읽는** 경우다.\
`@Retention` 을 안 적으면 기본값이 `CLASS` 라서, 클래스 파일에는 멀쩡히 들어 있는데 `getAnnotation()` 이 `null` 을 준다.

> **애너테이션(annotation)** — 선언이나 타입 사용 자리에 붙이는, 프로그램의 동작을 직접 바꾸지 않는 메타데이터.\
> 예: `@Override` 는 실행 코드가 아니라 "이건 재정의다"라는 표시이고, 그것을 읽어 검사하는 쪽은 컴파일러다.

> **메타 애너테이션(meta-annotation)** — 애너테이션 선언에 붙이는 애너테이션.\
> 예: `@Retention`·`@Target` 은 둘 다 자기 자신이 애너테이션이고, 애너테이션 타입 선언 위에만 붙는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. `@Retention` 세 값은 **각각 어디서 사라지고**, 그 사라짐을 어떻게 눈으로 확인하는가.
2. `@Target` 은 **무엇을 막고**, 막혔을 때 어떤 메시지가 나오는가.
3. 애너테이션 원소로 **쓸 수 있는 타입과 없는 타입**은 무엇으로 갈리는가.
4. 같은 애너테이션을 두 번 붙이는 `@Repeatable` 은 **런타임에 무엇으로 보이는가.**

## 동작 방식

### (1) 세 가지 `@Retention` — 실제로 어디까지 가는지 찍어 본다

**언제 쓰나** — 애너테이션을 새로 만들 때 맨 처음 정해야 하는 것. 이것 하나가 "누가 읽을 수 있나"를 정한다.

같은 클래스에 셋을 한꺼번에 붙이고 리플렉션으로 읽었다.

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

셋을 다 붙였는데 **런타임에 보이는 것은 하나뿐**이다. 그럼 나머지 둘은 어디로 갔나 — 클래스 파일을 열어 본다.

**`javap -v -p Ex$Three.class` 출력 그대로** (`Ex.java (16-a)`, JDK 21.0.5)

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

`KeepInSource` 는 **어디에도 없다.** 상수 풀까지 훑어서 확인했다.

```text
$ javap -v -p 'Ex$Three.class' | grep -c 'KeepInSource'
0
```

```text
javac 가 애너테이션 셋을 각각 어디에 적었나

  소스                       Ex$Three.class 의 속성                리플렉션
  ---------------------      ------------------------------      ------------
  @KeepInSource("A")   ->    (없음)                          ->   못 읽는다
  @KeepInClass("B")    ->    RuntimeInvisibleAnnotations     ->   못 읽는다
  @KeepAtRuntime("C")  ->    RuntimeVisibleAnnotations       ->   읽는다
```

그림 해설 (한 단계씩):

- `SOURCE` 는 **javac 가 통째로 버린다.** 클래스 파일에 흔적이 없으니 어떤 도구도 나중에 못 읽는다.\
  javadoc 이 그대로 못박는다 — "Annotations are to be **discarded by the compiler**."
- `CLASS` 는 **`RuntimeInvisibleAnnotations` 속성**으로 들어간다. 파일에는 있지만 JVM 이 리플렉션에 노출하지 않는다.\
  javadoc — "recorded in the class file by the compiler **but need not be retained by the VM at run time**."
- `RUNTIME` 만 **`RuntimeVisibleAnnotations`** 로 들어가고, 이것만 `getAnnotation()` 으로 읽힌다.
- 속성 이름의 `Visible`/`Invisible` 은 **"런타임에 보이나"**를 뜻한다. `javap` 로 바로 구별된다.

비용 — `RUNTIME` 애너테이션은 클래스 파일을 키우고, 조회할 때마다 리플렉션 비용이 든다.\
*(구체적인 크기·속도는 이 문서에서 측정하지 않았다.)*

### (2) `@Retention` 을 안 적으면 — 기본값은 `CLASS` 다

**언제 쓰나** — 애너테이션을 만들었는데 프레임워크가 못 읽을 때 첫 번째로 의심할 것.

**출력** (`Ex.java (16-f)`, JDK 21.0.5)

```text
@Retention 없는 애너테이션을 런타임에 읽으면
  getAnnotations() = []
  즉 기본 보존 정책 = CLASS (javadoc: This is the default behavior)
```

그런데 클래스 파일에는 멀쩡히 들어 있다.

```text
    RuntimeInvisibleAnnotations:
      0: #12(#13=s#14)
        Ex$NoMeta(
          value="on-field"
        )
```

```text
"안 붙였다" 와 "못 읽는다" 는 다르다

  붙이긴 붙었다                          그런데 못 읽는다
  +------------------------------+      +------------------------------+
  | .class 안                    |      | 런타임                        |
  |  RuntimeInvisibleAnnotations |      |  getAnnotations() -> []      |
  |    Ex$NoMeta(value="...")    |      |  isAnnotationPresent -> false|
  +------------------------------+      +------------------------------+
    javap 로는 보인다                      리플렉션으로는 안 보인다
```

그림 해설 (한 단계씩):

- `@Retention` 을 생략하면 **`CLASS`** 다 — javadoc 이 "This is the default behavior" 라고 적어 두었다.
- 그래서 **디버깅이 어렵다.** 오타도 아니고 컴파일 에러도 아니고, 그냥 `null` 이 나온다.
- 직접 만든 애너테이션을 리플렉션으로 읽을 거면 **`@Retention(RetentionPolicy.RUNTIME)` 은 선택이 아니라 필수**다.

비용 — 없다. 한 줄 빠뜨린 것의 대가가 무음 실패라는 것이 문제다.

### (3) `@Target` — 붙일 수 있는 자리를 컴파일에서 막는다

**언제 쓰나** — 애너테이션을 만들 때. 안 적으면 (거의) 어디에나 붙는다.

**`javac` 출력 그대로** (`Ex.java (16-b)`, JDK 21.0.5)

```text
Ex.java:9: error: annotation interface not applicable to this kind of declaration
    @MethodOnly                 // (A) 클래스에 붙였다
    ^
Ex.java:14: error: annotation interface not applicable to this kind of declaration
        @MethodOnly int field;      // (C) 필드에 붙였다
        ^
2 errors
```

`@Target(ElementType.METHOD)` 하나로 (A)와 (C)가 막혔고 (B)만 통과했다.

```text
@Target(METHOD) 을 붙인 애너테이션

  @MethodOnly class Wrong {}        -> 컴파일 에러
  @MethodOnly void m() {}           -> OK
  @MethodOnly int field;            -> 컴파일 에러
```

`@Target` 을 **아예 안 적으면** 어떻게 되나 — 클래스·필드·메서드·파라미터·지역 변수·생성자에 전부 붙였고 **전부 컴파일됐다**(`Ex.java (16-f)`).

> **`ElementType`** — 애너테이션을 붙일 수 있는 자리의 종류를 나열한 enum. `@Target` 의 값으로 쓴다.\
> 예: `ElementType.METHOD` 만 주면 메서드 선언 위에만 붙일 수 있다.

**출력** (`Ex.java (16-e)`, JDK 21.0.5)

```text
[TYPE, FIELD, METHOD, PARAMETER, CONSTRUCTOR, LOCAL_VARIABLE, ANNOTATION_TYPE, PACKAGE, TYPE_PARAMETER, TYPE_USE, MODULE, RECORD_COMPONENT]
```

| `ElementType` | 붙는 자리 | `@since` |
|---|---|---|
| `TYPE` | 클래스·인터페이스·enum·record | 1.5 |
| `FIELD` | 필드 (enum 상수 포함) | 1.5 |
| `METHOD` | 메서드 | 1.5 |
| `PARAMETER` | 메서드·생성자 파라미터 | 1.5 |
| `CONSTRUCTOR` | 생성자 | 1.5 |
| `LOCAL_VARIABLE` | 지역 변수 | 1.5 |
| `ANNOTATION_TYPE` | 애너테이션 선언 (= 메타 애너테이션) | 1.5 |
| `PACKAGE` | `package-info.java` 의 패키지 선언 | 1.5 |
| `TYPE_PARAMETER` | `<T>` 의 T | **1.8** |
| `TYPE_USE` | 타입이 **쓰인** 모든 자리 | **1.8** |
| `MODULE` | `module-info.java` | **9** |
| `RECORD_COMPONENT` | record 의 컴포넌트 | **16** |

`@since` 는 `lib/src.zip` 의 `ElementType.java` 를 직접 읽어 확인한 값이다.

비용 — 없다. `@Target` 은 컴파일 타임에만 쓰인다.

### (4) 애너테이션을 리플렉션으로 읽는 네 자리

**언제 쓰나** — 프레임워크가 "이 클래스의 어느 멤버에 무엇이 붙었나"를 훑을 때.

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

```text
클래스 파일에서 애너테이션이 저장되는 자리가 다르다

  붙인 자리            클래스 파일 속성                        읽는 API
  ----------------     ----------------------------------     -----------------------
  클래스·필드·메서드   RuntimeVisibleAnnotations              getAnnotations()
  파라미터             RuntimeVisibleParameterAnnotations     Parameter.getAnnotations()
  타입 사용(TYPE_USE)  RuntimeVisibleTypeAnnotations          getAnnotatedReturnType()
  지역 변수(선언)      (없음)                                  (없음)
```

그림 해설 (한 단계씩):

- 선언 자리마다 **속성이 따로** 있다. 그래서 읽는 API 도 따로다.
- `TYPE_USE` 애너테이션은 `getAnnotations()` 로 **안 나온다** — 출력의 `t.getAnnotations() = []` 가 그것이다.\
  `getAnnotatedReturnType().getAnnotations()` 처럼 **타입 쪽 API** 로 읽어야 한다.
- **지역 변수에 붙인 선언 애너테이션은 아예 저장되지 않는다.** `@Retention(RUNTIME)` 이어도 그렇다.
- 파라미터 **이름**(`a`·`b`)이 나오려면 `javac -parameters` 가 필요하다. 없으면 `arg0`·`arg1` 이다.

비용 — 리플렉션 조회는 클래스당 한 번 캐시해 두는 것이 보통이다. 프레임워크 기동 비용이 여기서 나온다.

### (5) 지역 변수 애너테이션은 클래스 파일에 없다

**언제 쓰나** — "런타임으로 뒀으니 읽히겠지"라고 생각한 자리를 점검할 때.

`@Retention(RUNTIME) @Target(LOCAL_VARIABLE)` 인 애너테이션을 지역 변수에 붙이고 클래스 파일을 뒤졌다.

```text
$ javap -v -p e/Ex.class | grep -c 'local-var'
0
```

같은 메서드의 파라미터·메서드 애너테이션은 멀쩡히 들어 있다.

```text
같은 메서드 안에서 갈린다 (Ex.java (16-e))

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

**`javap -v` 출력 그대로** (`Ex.java (16-e)`)

```text
      RuntimeVisibleTypeAnnotations:
        0: #165(): LOCAL_VARIABLE, {start_pc=6, length=15, index=4}
          Ex$NonNull
```

그림 해설 (한 단계씩):

- 선언 애너테이션의 저장 자리는 **필드·메서드·클래스·파라미터**뿐이다. 지역 변수용 속성이 없다.
- 그래서 `ElementType.LOCAL_VARIABLE` 은 **컴파일 타임 도구(린터·애너테이션 프로세서)용**이다.
- 반면 `TYPE_USE` 는 `RuntimeVisibleTypeAnnotations` 에 **바이트코드 오프셋과 함께** 저장된다.\
  `start_pc`·`length`·`index` 가 "그 지역 변수 슬롯이 살아 있는 구간"이다.
- 그래도 이것을 읽는 표준 리플렉션 API 는 없다 — 바이트코드를 직접 읽는 도구(널 분석기 등)가 쓴다.

비용 — 없다. 없는 것을 찾느라 쓰는 시간이 비용이다.

### (6) 애너테이션 원소 — 쓸 수 있는 타입이 정해져 있다

**언제 쓰나** — 애너테이션에 값을 담을 때.

**`javac` 출력 그대로** (`Ex.java (16-d1)`, JDK 21.0.5)

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

`int[] ok();` 만 통과했다. 정리하면 이렇다.

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

전부 실행으로 확인했다(`Ex.java (16-c)`).

**출력** (`Ex.java (16-c)`, JDK 21.0.5)

```text
--- 기본값: 이름만 주면 나머지는 선언부의 default 가 들어간다
전체    = @Ex.Meta(handler=java.lang.Object.class, level=LOW, nested=@java.lang.annotation.Retention(CLASS), order=10, tags={}, name="minimal")
name    = minimal
order   = 10
level   = LOW
tags    = []
handler = class java.lang.Object
nested  = @java.lang.annotation.Retention(CLASS)
```

그림 해설 (한 단계씩):

- 원소는 **메서드 모양**으로 선언한다(`String name();`). 필드가 아니다.
- `default` 가 있는 원소는 생략할 수 있고, **없으면 반드시 줘야 한다.**
- 값은 전부 **컴파일 타임 상수**여야 한다 — 그래서 `Date` 나 `new Object()` 를 못 담는다.
- **`Class` 원소는 타입 자체를 담는다.** 출력의 `handler = class java.lang.Object` 가 그것이다.

비용 — 없다. 값은 전부 클래스 파일의 상수 풀에 들어간다.

### (7) 애너테이션 선언의 나머지 제약 — 전부 던져 봤다

**언제 쓰나** — "애너테이션도 인터페이스니까 되겠지"라고 생각한 것을 점검할 때.

**`javac` 출력 그대로** (`Ex.java (16-d2)` `(16-d3)` `(16-d4)`, JDK 21.0.5)

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

| 해 보려 한 것 | 결과 | 메시지 |
|---|---|---|
| 필수 원소를 생략 | 에러 | `missing a default value for the element 'order'` |
| `extends` 로 상속 | 에러 | `'extends' not allowed for @interfaces` |
| `default null` | 에러 | `element value must be a constant expression` |
| 원소 타입이 자기 자신 | 에러 | `type of element Cyclic is cyclic` |
| `throws` 절 | 에러 | `throws clause not allowed in @interface members` |
| 원소에 파라미터 | 에러 | `cannot declare formal parameters` |
| 제네릭 애너테이션 | 에러 | `annotation interface Generic cannot be generic` |

그림 해설 (한 단계씩):

- 애너테이션은 **암묵적으로 `java.lang.annotation.Annotation` 을 확장**한다. 그 외에는 아무것도 상속 못 한다.\
  실행으로 확인했다 — `Meta 가 상속한 것 = [interface java.lang.annotation.Annotation]`.
- `null` 은 기본값이 될 수 없다. **"값 없음"을 표현하려면 빈 문자열·빈 배열·전용 enum 상수**를 쓴다.
- **제네릭이 못 된다**는 것이 19번(타입 소거)과 이어지는 자리다 — 클래스 파일에 상수로 박히는 값에 타입 인자를 줄 방법이 없다.

비용 — 없다. 전부 컴파일 타임 규칙이다.

### (8) `@Repeatable` — 두 번 붙이면 컨테이너가 생긴다

**언제 쓰나** — 같은 애너테이션을 여러 번 붙이고 싶을 때(`@Role("admin") @Role("user")`).

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

```text
javac 가 무엇으로 바꿔 놓나

  소스에 쓴 것                         클래스 파일에 저장된 것
  +-----------------------------+     +---------------------------------+
  | @Role("admin")              |     | @Roles({                        |
  | @Role("user")               | ->  |    @Role("admin"),              |
  | class Repeated {}           |     |    @Role("user") })             |
  +-----------------------------+     +---------------------------------+
    Role 이 두 개인 것처럼 보인다        실제로는 Roles 하나다

  소스에 쓴 것                         클래스 파일에 저장된 것
  +-----------------------------+     +---------------------------------+
  | @Role("single")             | ->  | @Role("single")                 |
  | class Once {}               |     |  (컨테이너로 안 감싼다)           |
  +-----------------------------+     +---------------------------------+
```

그림 해설 (한 단계씩):

- `@Repeatable(Roles.class)` 는 **컴파일러에게 컨테이너를 알려 주는 것**뿐이다. 새 저장 방식이 생긴 게 아니다.
- **두 번 이상 붙으면** javac 가 컨테이너(`@Roles`)로 감싼다 → `getAnnotation(Role.class)` 가 **`null`** 이다.
- **한 번만 붙으면** 감싸지 않는다 → 이번엔 `getAnnotation(Roles.class)` 가 `null` 이다.
- 그래서 **`getAnnotationsByType()` 을 써야** 개수에 상관없이 같은 코드로 읽힌다(Java 8 부터).

비용 — 없다. 문법 설탕이다. **읽는 쪽이 API 를 틀리면 조용히 `null` 이 된다**는 것이 비용이다.

### (9) `@Inherited` — 클래스만, 그것도 상위 클래스만

**언제 쓰나** — 부모에 붙인 표시를 자식에서도 읽고 싶을 때.

**출력** (`Ex.java (16-c)` `(16-f)`, JDK 21.0.5)

```text
--- @Inherited: 자식이 물려받나
Child getAnnotation(Inheritable)    = @Ex.Inheritable("from-parent")
Child getAnnotation(NotInheritable) = null
Child getAnnotations()              = [@Ex.Inheritable("from-parent")]
Child getDeclaredAnnotations()      = []
```

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

그림 해설 (한 단계씩):

- `@Inherited` 는 **`getAnnotation()` 이 상위 클래스를 거슬러 올라가게** 만든다. 자식이 실제로 갖게 되는 게 아니다.\
  그 증거가 `getDeclaredAnnotations() = []` 다 — **선언된 것은 여전히 없다.**
- javadoc 이 범위를 못박는다 — "annotations on **implemented interfaces have no** [effect]".\
  실행으로 확인했다: 인터페이스에 붙인 것은 구현 클래스에서 안 보인다.
- 메서드·필드에는 **애초에 적용되지 않는다** — javadoc: "has no effect if the annotated interface is used to annotate anything other than a class."

비용 — 조회할 때마다 상위 클래스를 거슬러 올라간다. 계층이 깊으면 조회가 길어진다.

### (10) 런타임 애너테이션 인스턴스의 정체 — 동적 프록시

**언제 쓰나** — `getAnnotation()` 이 돌려준 것에 `equals`·`getClass()` 를 해 볼 때.

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

그림 해설 (한 단계씩):

- 애너테이션 타입은 **인터페이스**이고, 리플렉션이 주는 것은 그 인터페이스의 **동적 프록시 인스턴스**다.
- 그래서 `getClass()` 는 `$Proxy1` 이고 `annotationType()` 은 `Ex$KeepAtRuntime` 다 — **둘이 다르다.**\
  애너테이션 타입을 알고 싶으면 `getClass()` 가 아니라 **`annotationType()`** 을 써야 한다.
- `equals` 는 **원소 값들이 같으면 참**이다(javadoc 이 `Annotation.equals` 로 계약을 정의한다).
- 같은 선언을 두 번 조회하면 같은 객체가 나왔다 — **캐싱은 구현 세부이고 계약이 아니다.**

비용 — 프록시 인스턴스 생성 비용이 첫 조회에 든다.

## 문법 — 형태와 규칙

직접 쓴 최소 예제다. 묻는 것 하나만 남겼다.

### 선언의 형태

```java
@Retention(RetentionPolicy.RUNTIME)          // 언제까지 살아남나 (안 적으면 CLASS)
@Target({ElementType.TYPE, ElementType.METHOD})  // 어디에 붙일 수 있나 (안 적으면 거의 어디나)
@Documented                                   // javadoc 에 표시할 것인가
@Inherited                                    // 하위 "클래스"에서 조회될 것인가
@interface Meta {
    String name();                            // 기본값 없음 -> 쓸 때 반드시 줘야 한다
    int order() default 10;                   // 기본값 있음 -> 생략 가능
    Level level() default Level.LOW;          // enum
    String[] tags() default {};               // 1차원 배열
    Class<?> handler() default Object.class;  // Class
    Retention nested() default @Retention(RetentionPolicy.CLASS);  // 다른 애너테이션
}
```

### 사용의 형태

```java
@Meta(name = "full", order = 1, tags = {"a", "b"})   // 이름 = 값
@Meta(name = "minimal")                               // 기본값이 있는 것은 생략
@SuppressWarnings("unchecked")                        // 원소가 value 하나뿐이면 이름 생략 가능
@Override                                             // 원소가 없으면 괄호도 생략 가능
@Deprecated()                                         // 빈 괄호를 써도 된다
```

- **원소가 `value` 하나뿐일 때만** 이름을 생략할 수 있다. 두 개 이상이면 전부 `이름 = 값` 이다.
- 배열 원소는 값이 하나면 중괄호를 생략할 수 있다 — `@Meta(tags = "a")`.

### 표준 애너테이션 — 어디에 쓰이나

**출력** (`Ex.java (16-g)`, JDK 21.0.5 — 표준 애너테이션의 메타 애너테이션을 리플렉션으로 읽었다)

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

| 애너테이션 | 하는 일 | `@since` |
|---|---|---|
| `@Override` | 재정의가 맞는지 컴파일러가 검사 | 1.5 |
| `@Deprecated` | 사용 중단 표시 (`forRemoval`·`since` 원소는 9 에서 추가) | 1.5 |
| `@SuppressWarnings` | 경고 끄기 | 1.5 |
| `@SafeVarargs` | 제네릭 가변 인자 경고 끄기 | 1.7 |
| `@FunctionalInterface` | 추상 메서드가 하나인지 검사 | 1.8 |

`@since` 는 `lib/src.zip` 의 실파일에서 읽었다.

읽어 볼 것이 셋 있다.

- **`@SuppressWarnings` 에는 `@Target` 이 없다.** `src.zip` 의 선언 바로 위에 이유가 주석으로 적혀 있다 —  `// Implicitly target all declaration contexts by omitting a @Target annotation`.  **"안 적으면 전부"**라는 규칙을 표준 라이브러리가 일부러 쓰고 있는 자리다.
- **메타 애너테이션 다섯은 전부 `RUNTIME` 이고 `@Target(ANNOTATION_TYPE)`** 이다. 그래서 위 프로그램처럼 리플렉션으로 읽을 수 있다.
- **`@Override` 와 `@SuppressWarnings` 만 `SOURCE`** 다 — 컴파일러만 읽으면 되기 때문이다.

### 메타 애너테이션 다섯

| 메타 애너테이션 | 정하는 것 | `@since` |
|---|---|---|
| `@Retention` | 언제까지 살아남나 | 1.5 |
| `@Target` | 어디에 붙일 수 있나 | 1.5 |
| `@Documented` | javadoc 에 나오나 | 1.5 |
| `@Inherited` | 하위 **클래스**에서 조회되나 | 1.5 |
| `@Repeatable` | 같은 자리에 여러 번 붙일 수 있나 | **1.8** |

`@since` 는 `lib/src.zip` 의 `java/lang/annotation/*.java` 를 직접 읽어 확인했다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. **넷 다 컴파일은 통과한다.**

### 1. `@Retention` 을 안 적고 리플렉션으로 읽으려 한다

```text
getAnnotations() = []
```

- 기본값이 `CLASS` 라서 **클래스 파일에는 있는데 런타임에 안 보인다.**
- 에러도 경고도 없다. `null` 이 나올 뿐이다.
- `javap -v` 로 `RuntimeInvisibleAnnotations` 가 보이면 **정확히 이 상황**이다.

### 2. `@Repeatable` 애너테이션을 `getAnnotation()` 으로 읽는다

```text
getAnnotation(Role.class)  = null          <- 두 번 붙였을 때
getAnnotation(Roles.class) = null          <- 한 번만 붙였을 때
getAnnotationsByType(Role) = [...]         <- 둘 다 동작
```

- **개수에 따라 저장 형태가 달라진다.** 테스트를 한 개짜리로만 짜면 두 개일 때 터진다(아니, 조용히 `null` 이 된다).
- 읽는 쪽은 **항상 `getAnnotationsByType()`** 을 쓴다.

### 3. 지역 변수에 런타임 애너테이션을 붙이고 읽으려 한다

```text
$ javap -v -p e/Ex.class | grep -c 'local-var'
0
```

- `@Retention(RUNTIME)` 을 붙여도 **클래스 파일에 저장 자리가 없다.**
- `ElementType.LOCAL_VARIABLE` 은 **컴파일 타임 도구용**이다.
- 파라미터(`RuntimeVisibleParameterAnnotations`)와 헷갈리기 쉽다 — 그쪽은 남는다.

### 4. `@Inherited` 를 인터페이스에 붙이고 구현체에서 읽으려 한다

```text
FromInterface getAnnotation(Inh) = null
I 자신 getAnnotation(Inh)        = @Ex.Inh("on-interface")
```

- javadoc 이 "implemented interfaces have no effect" 라고 적어 두었는데도 자주 밟는다.
- 인터페이스 기반 설계에서 `@Inherited` 는 **사실상 쓸 데가 없다.**
- 직접 계층을 훑으려면 `getInterfaces()` 를 재귀로 돌아야 한다.

### 5. 애너테이션의 `toString()` 을 로그·테스트에 쓴다

**출력을 세 JDK 에서 나란히 놓았다** (`Ex.java (16-c)`)

```text
JDK 17.0.13
  @Ex$Meta(handler=java.lang.Object.class, level=LOW, nested=..., order=10, tags={}, name="minimal")

JDK 21.0.5
  @Ex.Meta(handler=java.lang.Object.class, level=LOW, nested=..., order=10, tags={}, name="minimal")

JDK 25.0.1
  @Ex.Meta(handler=java.lang.Object.class, nested=..., level=LOW, tags={}, order=10, name="minimal")
```

- 17 → 21 에서 **이름 표기가 `Ex$Meta` 에서 `Ex.Meta` 로** 바뀌었다.
- 21 → 25 에서 **원소가 찍히는 순서가 바뀌었다.**
- `toString()` 형식은 **구현 세부**다. 파싱하거나 문자열 비교로 단언하면 JDK 를 올릴 때 깨진다.

## 구현 세부사항 대 언어 보장

이 절은 **"어디까지 믿어도 되나"**를 가른다.

| 항목 | 누가 보장하나 | 근거 |
|---|---|---|
| `SOURCE` 애너테이션이 클래스 파일에 없음 | **javadoc (API 계약)** | `RetentionPolicy.SOURCE` — "discarded by the compiler" |
| `CLASS` 가 기본 보존 정책 | **javadoc (API 계약)** | `RetentionPolicy.CLASS` — "This is the default behavior" |
| `RUNTIME` 만 리플렉션으로 읽힘 | **javadoc (API 계약)** | `RetentionPolicy.RUNTIME` |
| `@Inherited` 가 인터페이스에 효과 없음 | **javadoc (API 계약)** | `Inherited` javadoc |
| 애너테이션 원소로 쓸 수 있는 타입 | **JLS (언어 보장)** | JLS §9.6.1 |
| 애너테이션이 `Annotation` 만 확장 | **JLS (언어 보장)** | JLS §9.6 |
| `equals` 가 원소 값 비교 | **javadoc (API 계약)** | `Annotation.equals` |
| 클래스 파일 속성 이름(`RuntimeVisibleAnnotations` 등) | **JVMS (플랫폼 보장)** | JVMS §4.7.16~4.7.20 |
| `getClass()` 가 `$Proxy1` 인 것 | **구현 세부** | 프록시 구현 방식. `annotationType()` 을 써야 한다 |
| 같은 조회가 같은 객체를 돌려주는 것 | **구현 세부** | 관찰값(21.0.5). 캐싱은 계약이 아니다 |
| `toString()` 의 형식과 원소 순서 | **구현 세부** | **17·21·25 에서 두 번 바뀌었다** |
| `javac` 에러 문구 `annotation interface ...` | **구현 세부** | 17 은 `annotation type ...` 이었다 |

### `javac` 메시지도 버전에 갈린다

같은 소스를 세 JDK 에서 컴파일했다(`Ex.java (16-b)`).

```text
JDK 17.0.13
  error: annotation type not applicable to this kind of declaration

JDK 21.0.5 · 25.0.1
  error: annotation interface not applicable to this kind of declaration
```

- **에러 문구를 테스트에 넣지 마라.** 컴파일러 메시지는 계약이 아니다.
- 외울 것은 문구가 아니라 **"`@Target` 이 자리를 막는다"**는 성질이다.

## 언제 쓰고 언제 안 쓰나

| 애너테이션을 읽을 주체 | 골라야 할 `@Retention` | 이유 |
|---|---|---|
| 컴파일러·IDE 린터만 | `SOURCE` | 클래스 파일을 키우지 않는다 |
| 애너테이션 프로세서(APT) | `SOURCE` | 컴파일 중에만 읽는다 |
| 바이트코드 도구(정적 분석·계측) | `CLASS` | 파일에는 있어야 하고 런타임 비용은 없다 |
| 프레임워크·DI·직렬화·테스트 러너 | **`RUNTIME`** | 리플렉션으로 읽는 유일한 방법 |

| 애너테이션을 쓸까 | 판단 |
|---|---|
| "이 메서드는 재정의다" 같은 **컴파일 타임 검사** | 쓴다 — `@Override` 가 그 예다 |
| 설정값을 코드 옆에 두고 싶다 | 쓴다 — 단 **상수만** 담긴다 |
| 값이 런타임에 바뀐다 | 안 쓴다 — 애너테이션 값은 컴파일 타임에 박힌다 |
| 분기 조건으로 쓰고 싶다 | 안 쓴다 — 읽고 행동하는 코드를 따로 써야 한다 |

판단 규칙 두 줄.

- **읽는 사람을 먼저 정하고 `@Retention` 을 고른다.** 거꾸로 하면 무음 실패가 난다.
- **애너테이션은 데이터일 뿐이다.** 동작은 그것을 읽는 코드에 있다.

## 핵심 문장

- `@Retention` 은 **포스트잇이 언제 떨어지는지**를 정한다 — `SOURCE` 는 javac 가 버리고, `CLASS` 는 파일에 남되 안 보이고, `RUNTIME` 만 리플렉션에 노출된다.
- **안 적으면 `CLASS`** 다. 직접 만든 애너테이션이 `null` 로 나오는 사고의 대부분이 여기다.
- `javap -v` 의 **`RuntimeVisibleAnnotations` 대 `RuntimeInvisibleAnnotations`** 가 그 차이를 눈으로 보여 준다.
- `@Target` 은 **붙일 수 있는 자리를 컴파일에서 막는다.** 안 적으면 거의 어디에나 붙는다.
- 애너테이션 원소는 **기본형·`String`·`Class`·enum·애너테이션과 그 1차원 배열**뿐이고, 값은 전부 컴파일 타임 상수다.
- `@Repeatable` 은 **두 번 이상일 때만 컨테이너로 감싼다** — 읽는 쪽은 항상 `getAnnotationsByType()` 을 쓴다.
- 지역 변수에 붙인 선언 애너테이션은 **클래스 파일에 아예 저장되지 않는다.**

## 관련 자료

- [`../README.md`](../README.md) — Java 문법·API 주제 목록(이 주제는 16번)
- [`../19-type-erasure/`](../19-type-erasure/) — **그쪽은 제네릭 타입 인자가 지워지고 `Signature` 속성에 남는 비대칭까지, 여기는 애너테이션이 `Runtime*Annotations` 속성에 남는지부터.**\
  둘 다 "클래스 파일에 무엇이 남나"를 묻지만, 대상이 타입 인자냐 애너테이션이냐로 갈린다
- 목록의 **58번 주제**(리플렉션) — **`getAnnotation` 으로 읽은 다음 무엇을 하나가 그쪽이다.** 여기는 **읽히느냐 마느냐**까지
- [`../11-interfaces-default-methods/`](../11-interfaces-default-methods/) — 애너테이션 타입이 **인터페이스**라는 것. 다만 `default` 메서드도 상속도 못 한다
- [`../13-enum-classes/`](../13-enum-classes/) — 애너테이션 원소로 쓸 수 있는 유일한 "직접 만든 타입"이 enum 이다
- [`../14-records/`](../14-records/) — `ElementType.RECORD_COMPONENT`(16) 가 생긴 이유. record 컴포넌트에 붙인 애너테이션이 필드·접근자·생성자 파라미터로 전파되는 규칙은 그쪽
- [`../17-generic-declarations/`](../17-generic-declarations/) — 애너테이션이 **제네릭이 될 수 없다**는 제약의 뿌리
- [`../../../../../../history/java/java-5.md`](../../../../../../history/java/java-5.md) — 애너테이션이 **언제·왜 들어왔나**가 정본. 여기는 **어떻게 쓰고 무엇을 못 하나**
- 목록의 **34번 주제**(`import`·모듈) — `ElementType.MODULE`(9)·`PACKAGE` 가 붙는 자리(`module-info.java`·`package-info.java`)

## 용어 풀이

- **애너테이션(annotation)** — 선언이나 타입 사용 자리에 붙이는 메타데이터. 스스로 동작하지 않고, 읽는 쪽이 따로 있다.
- **애너테이션 타입(annotation interface)** — `@interface` 로 선언한 타입. 암묵적으로 `java.lang.annotation.Annotation` 을 확장한다.
- **원소(element)** — 애너테이션이 담는 값. 메서드 모양(`String name();`)으로 선언한다.
- **메타 애너테이션** — 애너테이션 선언에 붙이는 애너테이션. `@Retention`·`@Target`·`@Documented`·`@Inherited`·`@Repeatable` 다섯.
- **`@Retention`** — 애너테이션이 어느 단계까지 살아남는지 정하는 메타 애너테이션. 값은 `SOURCE`/`CLASS`/`RUNTIME`.
- **`@Target`** — 애너테이션을 붙일 수 있는 선언의 종류를 제한하는 메타 애너테이션.
- **`RuntimeVisibleAnnotations`** — 런타임에 읽히는 애너테이션이 저장되는 클래스 파일 속성(JVMS §4.7.16).
- **`RuntimeInvisibleAnnotations`** — 클래스 파일에는 있지만 리플렉션에 노출되지 않는 애너테이션이 저장되는 속성(JVMS §4.7.17).
- **선언 애너테이션(declaration annotation)** — 클래스·메서드·필드 같은 **선언**에 붙는 애너테이션. `TYPE_USE` 이전의 모든 애너테이션.
- **타입 애너테이션(type annotation)** — `ElementType.TYPE_USE` 로 선언해 **타입이 쓰인 자리**에 붙는 애너테이션(Java 8).
- **컨테이너 애너테이션(container annotation)** — `@Repeatable` 이 지정한, 반복된 애너테이션들을 배열로 담는 애너테이션.
- **동적 프록시(dynamic proxy)** — 인터페이스만 주면 그 인터페이스를 구현한 객체를 런타임에 만들어 주는 기능. 애너테이션 인스턴스가 이것이다.
- **애너테이션 프로세서(annotation processor)** — 컴파일 중에 애너테이션을 읽어 코드를 생성하거나 검사하는 도구. `SOURCE` 보존이면 이쪽만 읽을 수 있다.

## 더 들어가면

- **`@Documented` 는 javadoc 에만 영향을 준다.** 클래스 파일·리플렉션 동작은 바뀌지 않는다.
- **표준 다섯 중 `@Override`·`@SuppressWarnings` 만 `SOURCE` 인 이유** — 둘 다 **컴파일러만 읽으면 끝나는** 표시다.\
  반면 `@Deprecated` 는 클래스 파일을 나중에 읽는 도구(IDE·바이트코드 분석기)가 봐야 하고,\
  `@FunctionalInterface`·`@SafeVarargs` 도 `RUNTIME` 으로 남아 있다 — 위 `(16-g)` 출력이 그 확인이다.
- **`@Target(TYPE_USE)` 하나만 줘도 클래스·필드·메서드에 붙는다** — 그런데 **읽히는 API 가 자리마다 다르다.**

**출력** (`Ex.java (16-i)`, JDK 21.0.5)

```text
(A) 클래스 getAnnotations()   = [@Ex.TU()]
(B) 필드 getAnnotations()     = []
(C) 메서드 getAnnotations()   = []
(C) 반환 타입 쪽              = [@Ex.TU()]
```

  클래스 선언에서는 **선언 애너테이션처럼** 읽히고, 필드·메서드에서는 **타입 쪽 API** 로만 읽힌다.\
  그리고 **반환 타입이 `void` 면 컴파일 에러**다 — `void` 는 애너테이션을 붙일 수 있는 타입이 아니다.\
  (아래 에러는 `(16-i)` 를 `@TU void method() {}` 로 두고 먼저 컴파일했을 때 나온 것이다.)

```text
Ex.java:9: error: annotation interface not applicable to this kind of declaration
    @TU void method() {}                    // 메서드는?
    ^
```

  널 분석기들이 `TYPE_USE` 하나만 선언하고도 넓게 쓰는 이유가 첫 줄이고, 읽는 쪽이 헷갈리는 이유가 나머지다.

- ★ **기본값은 클래스 파일에 안 박힌다 — 런타임에 애너테이션 타입에서 읽어 온다.**\
  값을 **직접 준 것**만 쓰는 쪽 클래스 파일에 저장된다. 실험으로 갈랐다(`Ex.java (16-j)`).

```text
1) 처음 컴파일
  기본값에 맡긴 쪽 = OLD
  값을 준 쪽       = EXPLICIT
2) Ann 의 default 를 OLD -> NEW 로 바꾸고 **Ann 만** 다시 컴파일
  기본값에 맡긴 쪽 = NEW
  값을 준 쪽       = EXPLICIT
```

  클래스 파일을 열면 이유가 보인다.

```text
-- UsesDefault 의 RuntimeVisibleAnnotations
  0: #14()                     <- 괄호가 비어 있다. 값이 없다
    Ann

-- UsesExplicit 의 RuntimeVisibleAnnotations
  0: #14(#15=s#16)
    Ann(
      value="EXPLICIT"         <- 여기 박혀 있다
    )

-- Ann 자신의 value() 메서드
    AnnotationDefault:
      default_value: s#10
        "NEW"                  <- 기본값은 여기 산다
```

  **기본값을 바꾸면 쓰는 쪽을 다시 컴파일하지 않아도 반영된다.**\
  라이브러리가 애너테이션의 기본값을 바꾸면 **재컴파일 없이 동작이 달라진다**는 뜻이기도 하다.
