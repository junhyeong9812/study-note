# kotlin/syntax/17 — 위임 프로퍼티: `by lazy`·`observable`·`Map` 위임 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·예외·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javap` 에서 실제로 얻었다.\
> 역어셈블은 **기본 `-jvm-target`(1.8 · `major version: 52`)** 이 정본이고, **stdlib 쪽은 `kotlin-stdlib.jar` 를 풀어 직접 찍었다.**
> ⚠️ **8번 블록은 되풀이 돌리면 달라진다.** 그 자리에 **대조할 것**을 적어 두었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 컴파일된다 — `by` 는 **인터페이스가 아니라 규약**으로 풀린다

**출력** (`java -cp ocustom:kotlin-stdlib.jar CustomKt`)

```text
A 읽는다
   getValue  — thisRef=Screen, property.name=title
   결과 : 처음
B 쓴다
   setValue  — property.name=title, value=바뀜
C 다시 읽는다
   getValue  — thisRef=Screen, property.name=title
   결과 : 바뀜
```

**왜 그런가**

- ★★ `Loud` 는 **아무것도 구현하지 않았다.** `operator fun getValue`/`setValue` 의 **이름과 시그니처만** 맞췄다.\
  Kotlin 은 그것만 본다 — 이것이 연산자 규약이다(전반의 정본은 목록의 **31번 주제**).
- ★ **`thisRef` 가 `Screen`** 이다. 위임 객체는 **누구의 프로퍼티인지** 알 수 있다.\
  최상위·지역 프로퍼티면 **`null`** 이 온다.
- ★★ **`property.name` 이 `"title"`** 이다. 위임 객체 하나를 여러 프로퍼티가 공유해도 구분할 수 있고,\
  `Map` 위임(5번)이 정확히 이 이름을 **키**로 쓴다.
- ★ 읽을 때마다 `getValue` 가 돈다 — **`by` 자체는 캐시가 아니다.** 캐시는 `lazy` 가 하는 일이다.

### 2. ★★★ 필드는 **셋**, 배열 길이는 **1** — `by lazy` 만 `KProperty` 를 안 받는다

**출력** (`javap -p -s odcode/Conf.class`)

```text
Compiled from "dcode.kt"
public final class Conf {
  static final kotlin.reflect.KProperty<java.lang.Object>[] $$delegatedProperties;
    descriptor: [Lkotlin/reflect/KProperty;
  private final kotlin.Lazy url$delegate;
    descriptor: Lkotlin/Lazy;
  private final kotlin.properties.ReadWriteProperty level$delegate;
    descriptor: Lkotlin/properties/ReadWriteProperty;
  public Conf();
    descriptor: ()V

  public final java.lang.String getUrl();
    descriptor: ()Ljava/lang/String;

  public final int getLevel();
    descriptor: ()I

  public final void setLevel(int);
    descriptor: (I)V

  private static final java.lang.String url_delegate$lambda$0();
    descriptor: ()Ljava/lang/String;

  static {};
    descriptor: ()V
}
```

**출력** (`javap -c -p odcode/Conf.class` — 접근자와 정적 초기화)

```text
  public final java.lang.String getUrl();
    Code:
       0: aload_0
       1: getfield      #37                 // Field url$delegate:Lkotlin/Lazy;
       4: astore_1
       5: aload_1
       6: invokeinterface #74,  1           // InterfaceMethod kotlin/Lazy.getValue:()Ljava/lang/Object;
      11: checkcast     #76                 // class java/lang/String
      14: areturn

  public final int getLevel();
    Code:
       0: aload_0
       1: getfield      #60                 // Field level$delegate:Lkotlin/properties/ReadWriteProperty;
       4: aload_0
       5: getstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
       8: iconst_0
       9: aaload
      10: invokeinterface #85,  3           // InterfaceMethod kotlin/properties/ReadWriteProperty.getValue:(Ljava/lang/Object;Lkotlin/reflect/KProperty;)Ljava/lang/Object;
      15: checkcast     #87                 // class java/lang/Number
      18: invokevirtual #90                 // Method java/lang/Number.intValue:()I
      21: ireturn

  public final void setLevel(int);
    Code:
       0: aload_0
       1: getfield      #60                 // Field level$delegate:Lkotlin/properties/ReadWriteProperty;
       4: aload_0
       5: getstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
       8: iconst_0
       9: aaload
      10: iload_1
      11: invokestatic  #49                 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
      14: invokeinterface #96,  4           // InterfaceMethod kotlin/properties/ReadWriteProperty.setValue:(Ljava/lang/Object;Lkotlin/reflect/KProperty;Ljava/lang/Object;)V
      19: return

  private static final java.lang.String url_delegate$lambda$0();
    Code:
       0: ldc           #99                 // String http://x
       2: areturn

  static {};
    Code:
       0: iconst_1
       1: anewarray     #102                // class kotlin/reflect/KProperty
       4: astore_0
       5: aload_0
       6: iconst_0
       7: new           #104                // class kotlin/jvm/internal/MutablePropertyReference1Impl
      10: dup
      11: ldc           #2                  // class Conf
      13: ldc           #106                // String level
      15: ldc           #108                // String getLevel()I
      17: iconst_0
      18: invokespecial #111                // Method kotlin/jvm/internal/MutablePropertyReference1Impl."<init>":(Ljava/lang/Class;Ljava/lang/String;Ljava/lang/String;I)V
      21: aastore
      22: aload_0
      23: putstatic     #82                 // Field $$delegatedProperties:[Lkotlin/reflect/KProperty;
      26: return
}
```

**왜 그런가**

- ★★★ 필드는 `$$delegatedProperties`(static) · `url$delegate` · `level$delegate` **셋**이다.\
  [16번 주제](../16-properties-backing-field-lateinit-const/)의 서랍 자리에 **값이 아니라 위임 객체**가 들어 있다.
- ★★★ **배열 길이가 `1`** 이다 — `static {}` 의 첫 명령이 `iconst_1; anewarray KProperty` 다.\
  위임이 둘인데 하나뿐인 이유는 **`getUrl()` 이 `Lazy.getValue()` 를 인자 없이 부르기 때문**이다.\
  stdlib 의 `Lazy.getValue` 확장이 `inline` 이라 **`this.value` 로 접혔고**, `KProperty` 가 필요 없어졌다.
- ★★ `getLevel()`/`setLevel()` 은 `this` 와 **`$$delegatedProperties[0]`** 을 함께 넘긴다.\
  원소는 `MutablePropertyReference1Impl(Conf.class, "level", "getLevel()I", 0)` 이고,\
  **클래스 초기화(`static {}`) 때 한 번** 만들어진다 — 호출마다 만드는 것이 아니다.
- ★ `getLevel()` 끝에 `checkcast Number; intValue()` 가 붙는다 — **`Int` 가 박싱된다**([12번 주제](../12-reified-type-parameters/)).

### 3. ★★ 기본은 **`kotlin.SynchronizedLazyImpl`** — `B` 는 `true`

**출력** (`java -cp olazy:kotlin-stdlib.jar LazymodeKt`)

```text
A d 의 위임 객체 클래스 : kotlin.SynchronizedLazyImpl
A s 의 위임 객체 클래스 : kotlin.SynchronizedLazyImpl
A p 의 위임 객체 클래스 : kotlin.SafePublicationLazyImpl
A n 의 위임 객체 클래스 : kotlin.UnsafeLazyImpl
B 기본과 SYNCHRONIZED 가 같은 클래스인가 : true
```

**왜 그런가**

- ★★ 인자 없는 `lazy { }` 의 위임 객체 클래스가 **`SYNCHRONIZED` 와 같다.** `B : true` 가 못박는다.\
  즉 **기본이 스레드 안전**이다.
- 세 모드가 **서로 다른 구현 클래스**로 내려간다 — `SynchronizedLazyImpl` · `SafePublicationLazyImpl` · `UnsafeLazyImpl`.
- ★ 필드 이름을 `"$name\$delegate"` 로 만든 근거가 **2번의 `url$delegate`** 다.\
  그 이름 규칙을 모르면 리플렉션으로 꺼낼 수가 없다.
- ★ 문서를 옮겨 적는 대신 **런타임 클래스를 꺼내 이름을 찍은 것**이라, 기본값이 바뀌면 **이 실험이 바로 다른 답을 낸다.**\
  「문서에 그렇게 적혀 있더라」보다 강한 근거다.

### 4. ★ `observable` 은 **뒤**, `vetoable` 은 **앞** — `-1` 은 거부되고 값은 `10` 으로 남는다

**출력** (`java -cp oobs:kotlin-stdlib.jar ObsKt`)

```text
A name 에 대입
   observable — name: '빈칸' -> 'kim'
   지금 값 : kim
B age 에 10
   vetoable   — age: 0 -> 10  (통과? true)
   지금 값 : 10
C age 에 -1 (거부된다)
   vetoable   — age: 10 -> -1  (통과? false)
   지금 값 : 10
D notNull 을 대입 전에 읽으면
   java.lang.IllegalStateException : Property required should be initialized before get.
```

**왜 그런가**

- ★★ **`observable` 의 콜백은 값이 바뀐 뒤에 돈다.** `A` 에서 콜백이 `'빈칸' -> 'kim'` 을 찍고\
  바로 다음 줄의 값이 이미 `kim` 이다. **막을 수 없다 — 통보다.**
- ★★ **`vetoable` 의 콜백은 앞에서 돌고 `Boolean` 을 돌려준다.** `C` 에서 `10 -> -1` 콜백이 **돌았고**,\
  `false` 를 돌려줘 값이 `10` 으로 남았다. ★ **거부된 시도도 관찰된다**는 것이 이 줄의 요점이다.
- ★ `D` 의 예외는 **`java.lang.IllegalStateException`** 이고 메시지는 `Property required should be initialized before get.` 다.\
  **`lateinit` 의 `kotlin.UninitializedPropertyAccessException` 과 다르다** — catch 절을 그대로 쓰면 안 잡힌다([16번 주제](../16-properties-backing-field-lateinit-const/)).

### 5. ★ 생성은 성공하고 **읽을 때** 터진다 — `NoSuchElementException` 과 `ClassCastException`

**출력** (`java -cp omap:kotlin-stdlib.jar MapdelKt`)

```text
E name : kim   age : 30
F 처음 : lee
G 대입 뒤 프로퍼티 : park
H 대입 뒤 맵 자체   : {name=park}
I 키가 없으면
   java.util.NoSuchElementException : Key name is missing in the map.
J 타입이 다르면
   java.lang.ClassCastException : class java.lang.String cannot be cast to class java.lang.Number (java.lang.String and java.lang.Number are in module java.base of loader 'bootstrap')
```

**왜 그런가**

- `E`·`F` 는 맵에서 그대로 읽는다. **키가 프로퍼티 이름**이다(1번의 `property.name`).
- ★ `G`·`H` — `mu.name = "park"` 이 **맵 자체를 바꿨다**(`{name=park}`). `var` 위임은 `MutableMap` 이 필요한 이유다.
- ★★★ **`User(mapOf("age" to 1))` 이라는 줄은 성공한다.** 위임은 **읽을 때** 맵을 본다 —\
  `I` 에서야 `java.util.NoSuchElementException: Key name is missing in the map.` 이 난다.
- ★★ `J` 는 `java.lang.ClassCastException` 이고 메시지가 **`String cannot be cast to Number`** 다.\
  `Int` 가 아니라 **`Number`** 를 말하는 이유는 2번에서 본 **박싱 경로**다 — 위임이 `Any?` 를 돌려주고\
  호출부가 `checkcast Number; intValue()` 로 푼다.
- ★ 그래서 **`Map` 위임은 타입 검사를 런타임으로 미루는 도구**다. 경계에서 한 번 검증하는 코드가 따로 필요하다.

### 6. ★ 된다 — 그리고 **`lazy()` 는 인라인이 아니다**

**출력** (`java -cp olocal:kotlin-stdlib.jar LocalKt`)

```text
K 지역 변수에 by lazy 를 건다
   선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다
   초기화 람다가 돌았다
   첫 번째 읽기 : 값
   두 번째 읽기 : 값
```

**출력** (`javap -c -p olocal/LocalKt.class` — `main()`)

```text
  public static final void main();
    Code:
       0: ldc           #27                 // String K 지역 변수에 by lazy 를 건다
       2: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
       5: swap
       6: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
       9: invokedynamic #45,  0             // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function0;
      14: invokestatic  #51                 // Method kotlin/LazyKt.lazy:(Lkotlin/jvm/functions/Function0;)Lkotlin/Lazy;
      17: astore_0
      18: ldc           #53                 // String    선언만 했을 때 — 위에 아무 줄도 안 찍혔어야 한다
      20: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      23: swap
      24: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      27: new           #55                 // class java/lang/StringBuilder
      30: dup
      31: invokespecial #58                 // Method java/lang/StringBuilder."<init>":()V
      34: ldc           #60                 // String    첫 번째 읽기 :
      36: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      39: aload_0
      40: invokestatic  #68                 // Method main$lambda$1:(Lkotlin/Lazy;)Ljava/lang/String;
      43: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      46: invokevirtual #71                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      49: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      52: swap
      53: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      56: new           #55                 // class java/lang/StringBuilder
      59: dup
      60: invokespecial #58                 // Method java/lang/StringBuilder."<init>":()V
      63: ldc           #73                 // String    두 번째 읽기 :
      65: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      68: aload_0
      69: invokestatic  #68                 // Method main$lambda$1:(Lkotlin/Lazy;)Ljava/lang/String;
      72: invokevirtual #64                 // Method java/lang/StringBuilder.append:(Ljava/lang/String;)Ljava/lang/StringBuilder;
      75: invokevirtual #71                 // Method java/lang/StringBuilder.toString:()Ljava/lang/String;
      78: getstatic     #15                 // Field java/lang/System.out:Ljava/io/PrintStream;
      81: swap
      82: invokevirtual #21                 // Method java/io/PrintStream.println:(Ljava/lang/Object;)V
      85: return

```

**왜 그런가**

- 선언 줄에서는 아무 일도 안 일어난다 — `초기화 람다가 돌았다` 가 **첫 읽기 직전**에 나오고 **한 번만** 나온다.
- ★★ **`$$delegatedProperties` 가 없다.** 지역 변수라 `KProperty` 를 만들 필요가 없고,\
  `Lazy` 객체 하나가 **지역 슬롯**(`astore_0`)에 담길 뿐이다.
- ★★★ **`invokedynamic … Function0` → `invokestatic kotlin/LazyKt.lazy` 가 실제 호출로 남아 있다.**\
  [11번 주제](../11-inline-functions/)의 인라인 함수들과 정반대이고,\
  [14번 주제](../14-scope-functions/)의 scope function 다섯이 **클래스 파일에 `Function1` 을 0회 남긴 것**과 나란히 놓으면 대비가 분명하다.\
  **`by lazy` 는 프로퍼티마다 객체를 만든다.**
- 읽기는 `main$lambda$1(Lkotlin/Lazy;)` 라는 합성 메서드를 거친다 — 지역 위임의 접근자가 그것이다.

### 7. 에러 **2건** — 문구가 **필요한 시그니처를 통째로 적어 준다**

**출력** (`kotlinc badby.kt -d obb`)

```text
===== 소스: badby.kt =====
class Plain(var stored: String)

class Screen {
    var title: String by Plain("x")
}
===== kotlinc badby.kt =====
badby.kt:4:23: error: type 'Plain' has no method 'getValue(Screen, KMutableProperty1<*, *>)', so it cannot serve as a delegate.
    var title: String by Plain("x")
                      ^^
badby.kt:4:23: error: type 'Plain' has no method 'setValue(Screen, KMutableProperty1<*, *>, String)', so it cannot serve as a delegate for var (read-write property).
    var title: String by Plain("x")
                      ^^
(exit 1)
```

**출력** (`kotlinc badby2.kt -d obb2`)

```text
===== 소스: badby2.kt =====
import kotlin.reflect.KProperty

class ReadOnly(private val stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = stored
}

class Screen {
    var title: String by ReadOnly("x")
}
===== kotlinc badby2.kt =====
badby2.kt:8:23: error: type 'ReadOnly' has no method 'setValue(Screen, KMutableProperty1<*, *>, String)', so it cannot serve as a delegate for var (read-write property).
    var title: String by ReadOnly("x")
                      ^^
(exit 1)
```

**왜 그런가**

- ★★ 「그런 메서드가 없다」로 끝나지 않고 **`getValue(Screen, KMutableProperty1<*, *>)`** 처럼\
  **필요한 시그니처를 정확히 불러 준다.** 규약을 외울 필요가 없다 — **던져 보면 알려 준다.**
- ★ `var` 라서 둘 다 필요하다. `getValue` 만 있는 두 번째 파일은 **`setValue` 하나만** 모자란다고 한다.
- ★ `operator` 를 빼면 **같은 「메서드가 없다」 계열 에러**로 보인다 — 이름 오타처럼 읽혀 원인이 잘 안 드러난다.

### 8. ⚠️ 세 성질 — `1/1` · `여러 번/1` · `여러 번/여럿`

**출력** (`java -cp orace2:kotlin-stdlib.jar Race2Kt` — 같은 바이너리를 12판)

```text
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 1 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 6개
   --- 2 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 3 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 4 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 5 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 6 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 7 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 8 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 9 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 8개
   --- 10 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 11 판 끝 ---
   SYNCHRONIZED : 초기화 람다 호출 1회 · 스레드들이 본 서로 다른 객체 1개
   PUBLICATION : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 1개
   NONE : 초기화 람다 호출 8회 · 스레드들이 본 서로 다른 객체 7개
   --- 12 판 끝 ---
```

> ★★ **이 블록은 다시 돌리면 달라진다.** 대조할 것은 숫자가 아니라 **세 성질**이다 —\
> ① `SYNCHRONIZED` — 초기화 **1회**, 모두 **같은 객체**.\
> ② `PUBLICATION` — 초기화가 **여러 번 돌 수 있는데도** 모두 **한 객체**를 본다.\
> ③ `NONE` — 초기화도 여러 번, **본 객체도 여러 개**일 수 있다.

**왜 그런가**

- ★ 흔들린 칸은 **`NONE` 의 「서로 다른 객체 개수」 하나**다 — 12판에서 **8 이 8판 · 7 이 3판 · 6 이 1판**.\
  나머지 칸은 12판 내내 한 글자도 안 갈렸다.
- ★★ **캡처를 두 번 돌려 통틀어 24판**을 얻었다. ①·②는 **24판 전부 같았고**, 갈린 것은 ③뿐이다 —\
  1차 12판은 `8` 이 8판·`7` 이 3판·`6` 이 1판, 2차 12판은 `8` 이 10판·`7` 이 2판이었다.\
  **위 블록은 1차 12판이고, 2차와 다른 줄은 `NONE` 의 객체 수 여섯 줄뿐이다.**
- ★★ **그것이 「보장」의 근거는 아니다.** 보장은 stdlib 구현(9번의 `monitorenter`·CAS)과 문서에서 오고,\
  이 실행은 **그 보장과 어긋나지 않았다**까지다. 「12판 다 같았으니 보장된다」로 읽으면 안 된다.
- ★★★ **`PUBLICATION` 의 핵심**은 「**8번 돌았는데 모두가 같은 객체를 본다**」는 것이다 —\
  「한 번만 돈다」가 아니다. **부수 효과가 있는 초기화에는 못 쓴다.**
- ★★ **`NONE` 은 스레드마다 다른 객체를 본다.** 「여러 번 돈다」보다 이쪽이 훨씬 나쁘다 —\
  `===` 나 캐시를 기대한 코드가 조용히 깨진다.
- ★ 「안 터졌다」가 「안전하다」가 아니다. `NONE` 은 **단일 스레드에서는 아무 문제가 없다** —\
  8스레드를 한 래치에서 동시에 출발시켜야만 드러났다.

### 9. `lock` · `AtomicReferenceFieldUpdater` · **아무것도 없음**

**출력** (`javap -p -s` 세 벌 · `getValue()` 안의 동기화 명령 개수)

```text
$ javap -p -s kotlin/SynchronizedLazyImpl.class   # 필드만
final class kotlin.SynchronizedLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  private kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private volatile java.lang.Object _value;
    descriptor: Ljava/lang/Object;
  private final java.lang.Object lock;
    descriptor: Ljava/lang/Object;
$ javap -p -s kotlin/SafePublicationLazyImpl.class   # 필드만
final class kotlin.SafePublicationLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  public static final kotlin.SafePublicationLazyImpl$Companion Companion;
    descriptor: Lkotlin/SafePublicationLazyImpl$Companion;
  private volatile kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private volatile java.lang.Object _value;
    descriptor: Ljava/lang/Object;
  private final java.lang.Object final;
    descriptor: Ljava/lang/Object;
  private static final java.util.concurrent.atomic.AtomicReferenceFieldUpdater<kotlin.SafePublicationLazyImpl<?>, java.lang.Object> valueUpdater;
    descriptor: Ljava/util/concurrent/atomic/AtomicReferenceFieldUpdater;
$ javap -p -s kotlin/UnsafeLazyImpl.class   # 필드만
public final class kotlin.UnsafeLazyImpl<T> implements kotlin.Lazy<T>, java.io.Serializable {
  private kotlin.jvm.functions.Function0<? extends T> initializer;
    descriptor: Lkotlin/jvm/functions/Function0;
  private java.lang.Object _value;
    descriptor: Ljava/lang/Object;
$ 세 구현의 getValue() 안에 무엇이 있나
SynchronizedLazyImpl     monitorenter 1 · compareAndSet 0
SafePublicationLazyImpl  monitorenter 0 · compareAndSet 1
UnsafeLazyImpl           monitorenter 0 · compareAndSet 0
```

**왜 그런가**

| 구현 | 필드 | `getValue()` 안 | 8번의 어느 성질이 되나 |
|---|---|---|---|
| `SynchronizedLazyImpl` | `initializer` · **`volatile _value`** · **`lock`** | `monitorenter` **1** | 초기화 1회 · 한 객체 |
| `SafePublicationLazyImpl` | **`volatile initializer`** · **`volatile _value`** · `final` · **`AtomicReferenceFieldUpdater`** | CAS **1** | 여러 번 돌 수 있으나 **CAS 가 하나만 채택** |
| `UnsafeLazyImpl` | `initializer` · `_value`(평범) | **둘 다 0** | 아무 보장 없음 |

- ★ `SafePublicationLazyImpl` 은 **CAS 로 `_value` 를 한 번만 확정**한다. 그래서 초기화가 여러 번 돌아도\
  **밖으로 나가는 것은 하나**다 — 8번의 ②가 여기서 나온다.
- ★★ **「`NONE` 이 빠르다」는 이 근거로 말할 수 없다.** 여기서 센 것은 **명령의 유무**이고,\
  이 문서는 **세 모드의 비용을 재지 않았다.** 「동기화 명령이 없다」와 「빠르다」는 다른 주장이다.

### 10. `Lazy.getValue` 확장이 `inline` 이라 **접혔기** 때문이다

**왜 그런가**

- 2번의 배열 길이 `1` 은 **`by lazy` 가 `KProperty` 를 안 받기 때문**이다 —\
  `getUrl()` 이 `invokeinterface kotlin/Lazy.getValue:()Ljava/lang/Object;` 를 **인자 없이** 부른다.
- ★ **직접 만든 위임(1번)은 받는다.** `property.name` 을 실제로 찍어 봤다.
- ★★ 이것은 **최적화**다. 언어 문법은 `operator fun getValue(thisRef, property)` 를 요구하고,\
  stdlib 이 `Lazy` 에 대해 **`inline` 확장**으로 그 규약을 만족시키면서 본문을 `this.value` 로 줄인 것이다.
- ★ 그래서 **`by lazy` 에서는 `property.name` 을 쓸 자리가 없다.** 필요하면 `lazy` 를 감싸는\
  **자기 위임 클래스**를 만들어야 한다(1번의 모양).

### 11. **「서랍은 있는데 값이 아니라 대리인이 들어 있는」 칸**이다

**왜 그런가**

| [16번 주제](../16-properties-backing-field-lateinit-const/)의 축 | 필드 | 안에 든 것 | 예 |
|---|---|---|---|
| 저장하는 프로퍼티 | 있다 | **값** | `var age: Int = 0` |
| 계산 프로퍼티 | 없다 | — | `val full get() = …` |
| 확장 프로퍼티 | 없다 | — | `val Money.label get() = …`([13번 주제](../13-extension-functions-and-properties/)) |
| **위임 프로퍼티** | 있다(`x$delegate`) | **위임 객체** | `val url by lazy { … }` |

- ★ `lateinit` 은 **참조 타입**에, `Delegates.notNull()` 은 **원시 타입**에 쓴다.\
  예외도 다르다 — `kotlin.UninitializedPropertyAccessException` 대 **`java.lang.IllegalStateException`**(4번).\
  그리고 `lateinit` 은 **위임 객체가 안 생긴다** — 필드에 값이 직접 들어간다([16번 주제](../16-properties-backing-field-lateinit-const/)).
- ★ **`class A : B by b` 는 다른 주제다** — 그쪽은 **인터페이스 구현을 통째로 넘기는** 문법이고,\
  정본은 목록의 **21번 주제**다. `by` 라는 낱말만 같다.

## 실행 검증

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

★ **흔들리는 칸과 안 흔들리는 칸**(제출 전 재대조에서 「고칠 것」과 「설계상 다른 것」을 가르는 선언이다)

| 흔들린다 | 안 흔들린다 |
|---|---|
| 8번 `NONE` 의 「**서로 다른 객체 개수**」(1차 12판 8·7·6 · 2차 12판 8·7) | 8번 `SYNCHRONIZED`·`PUBLICATION` 의 모든 칸(**24판 동일**) |
| 스레드 실행 **순서** — 그래서 이 문서는 순서를 싣지 않고 **집계만** 실었다 | `javap` 출력 **전체**(오프셋·상수 풀 번호 포함) |
| (해당 없음 — 이 문서에는 해시코드·시간 수치를 싣지 않았다) | 예외 **타입과 메시지 본문** · 에러 문구 · 종료 코드 |

> 근거 — **캡처 스크립트를 두 번 돌려 블록 82개를 바이트 단위로 대조**했고, **달라진 파일은 `17-race-run` 하나**였다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `custom.kt` | `A`·`B`·`C` — **규약만으로 `by` 가 풀리는 것** · `thisRef` · `property.name` | `kotlinc` → `java` |
| `badby.kt` · `badby2.kt` | 규약 위반 에러 **2건 + 1건**과 그 문구가 시그니처를 불러 주는 것 | `kotlinc` 2회 (컴파일 실패가 결과) |
| `dcode.kt` | **필드 셋 · 배열 길이 1** · `getUrl` 대 `getLevel` 의 호출 모양 · `static {}` | `kotlinc` → `javap -p -s` · `javap -c -p` |
| `lazymode.kt` | `A`·`B` — **기본이 `SynchronizedLazyImpl`** 인 것 | `kotlinc` → `java` |
| `obs.kt` | `A`\~`D` — 콜백 시점 · 거부 · `IllegalStateException` | `kotlinc` → `java` |
| `mapdel.kt` | `E`\~`J` — **읽을 때 터지는 것**과 두 예외 | `kotlinc` → `java` |
| `local.kt` | `K` — 지역 위임 · **`LazyKt.lazy` 가 실제 호출로 남는 것** | `kotlinc` → `java` · `javap -c -p` |
| `formcheck.kt` | 「문법 — 형태와 규칙」의 **일곱 형태가 실제로 컴파일·실행되는 것**(`Z`) | `kotlinc` → `java` |
| `race2.kt` | 세 모드의 **초기화 횟수와 본 객체 수** — **같은 바이너리를 12판** | `kotlinc` → `java` **12회** |
| `kotlin-stdlib.jar` | 세 `Lazy` 구현의 **필드**와 `monitorenter`/CAS 개수 | `unzip` → `javap -p -s` · `javap -c -p` |

```text
===== 소스: formcheck.kt =====
import kotlin.properties.Delegates
import kotlin.reflect.KProperty

class Loud(private var stored: String) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): String = stored
    operator fun setValue(thisRef: Any?, property: KProperty<*>, value: String) { stored = value }
}

class Form2 {
    val a: String by lazy { "x" }
    var b: Int by Delegates.observable(0) { _, _, _ -> }
    var c: Int by Delegates.vetoable(0) { _, _, new -> new >= 0 }
    var d: Int by Delegates.notNull()
    val e: String by mapOf("e" to "x")
    var f: String by mutableMapOf<String, Any?>("f" to "x")
    var g: String by Loud("y")
}

fun main() {
    val o = Form2()
    o.d = 1
    println("Z ${o.a} ${o.b} ${o.c} ${o.d} ${o.e} ${o.f} ${o.g}")
}
===== kotlinc formcheck.kt =====
(exit 0)
===== java -cp ofc:kotlin-stdlib.jar FormcheckKt =====
Z x 0 0 1 x x y
```

**구현 의존 항목** — `x$delegate`·`$$delegatedProperties` 라는 이름, `MutablePropertyReference1Impl`,
`by lazy` 가 `KProperty` 를 안 받는 것, 상수 풀 번호·오프셋, `main$lambda$1` 이라는 합성 메서드 이름,
세 `Lazy` 구현의 필드 구성과 동기화 수단 — **전부 이 컴파일러·stdlib 버전의 산출물**이다.\
반면 **「`by` 가 `getValue`/`setValue` 규약으로 풀린다」·「`val` 은 `getValue` 만, `var` 는 둘 다」·
「`lazy` 의 기본이 `SYNCHRONIZED`」·「`PUBLICATION` 은 한 객체만 노출한다」·「`NONE` 은 아무 보장이 없다」·
「`observable` 은 사후, `vetoable` 은 사전」·「`Map` 위임은 읽을 때 검사한다」**
는 **언어·stdlib 의 계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **`$$delegatedProperties` 의 길이가 위임 개수와 달랐다.** 위임이 둘인데 배열은 **1** 이다.
   「`by` 는 항상 `KProperty` 를 넘긴다」가 **`by lazy` 에서 거짓**이었다 —
   stdlib 의 `Lazy.getValue` 확장이 `inline` 이라 **`this.value` 로 접혀** 인자가 사라진다.
2. ★★ **`PUBLICATION` 이 「가끔 두 번」이 아니었다.** 8스레드가 동시에 들어가면 **매번 8번 전부** 돌았다
   (12판 내내 `8회`). 그런데 **모두가 본 객체는 1개**다 — 이 모드가 보장하는 것은
   **호출 횟수가 아니라 노출되는 값의 유일성**이라는 것이 이 두 숫자의 대비로 드러났다.
3. ★ **`Delegates.notNull()` 의 예외가 `lateinit` 과 달랐다.** `java.lang.IllegalStateException` 이고
   메시지도 `Property required should be initialized before get.` 이다.
   「초기화 전 접근은 `UninitializedPropertyAccessException`」이라고 한 덩어리로 외우면 catch 절에서 샌다.

**안 걸린 것도 출력이다** — `race2.kt` 의 `NONE` 은 **단일 스레드로 돌리면 12판 내내 아무 문제가 없다.**
문제를 드러낸 것은 8스레드를 한 래치에서 동시에 출발시킨 구성이고,
그 구성에서도 **예외는 한 번도 안 났다** — 깨진 것은 **객체 동일성뿐**이라 조용하다.
