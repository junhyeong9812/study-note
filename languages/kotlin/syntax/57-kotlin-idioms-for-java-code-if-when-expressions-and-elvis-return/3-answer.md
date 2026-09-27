# kotlin/syntax/57 — Java 코드를 Kotlin 답게 — 식으로서의 `if`/`when`·엘비스 조기 반환 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `diff` 는 **출력 0줄 · `(exit 0)`** · 17행 전부 `true` · **`cells that differ: 0 / 17`** — 넘치는 합(`-294967296`)까지 같다

**출력**

```text
===== java -XshowSettings:properties -version | grep -E 'user\.(language|country) ' =====
    user.country = KR
    user.language = ko
(exit 0)
===== javac -d o57j Legacy57.java =====
(exit 0)
===== kotlinc idiom57.kt -d o57k =====
(exit 0)
===== java -cp o57j Legacy57 > j57.txt =====
(exit 0)
===== java -cp o57k:kotlin-stdlib.jar Idiom57Kt > k57.txt =====
(exit 0)
===== diff j57.txt k57.txt =====
(exit 0)
===== python3 pair57.py j57.txt k57.txt =====
case	input	Java	Kotlin	same
grade	95	A	A	true
grade	90	A	A	true
grade	85	B	B	true
grade	80	B	B	true
grade	70	C	C	true
fee	Card(1000)	30	30	true
fee	Cash(1000)	0	0	true
fee	Transfer(1000)	500	500	true
cityOf	null user	none	none	true
cityOf	null address	none	none	true
cityOf	null city	none	none	true
cityOf	seoul	SEOUL	SEOUL	true
cityOf	incheon	INCHEON	INCHEON	true
total	[]	0	0	true
total	[(100,2) (50,0) (30,-1) (7,3)]	221	221	true
total	[(2000000000,1) (2000000000,1)]	-294967296	-294967296	true
nextId	x3	1 2 3	1 2 3	true
cells that differ: 0 / 17
(exit 0)
```

**왜 그런가**

- ★★★ 다섯 사례 모두 **같은 연산을 같은 타입으로** 한다 — `if` 식은 Java 삼항과 같은 분기(5번), `when` 은 `instanceof` 사슬(9번), `?.`·`?:` 는 null 검사 셋, `sumOf` 는 `Int` 합, `object` 는 정적 상태 하나다.
- ★★ **`total` 의 넘침이 같은 이유** — 람다 `it.price * it.qty` 가 `Int` 라 `Int` 판 `sumOf` 가 골라진다. Java `int sum` 과 똑같이 조용히 넘친다([44번 주제](../44-aggregation-grouping-fold-reduce/) (2)).
- ★ 첫 블록의 `user.language = ko` 가 이 격자의 **환경**이다 — 2번이 그것을 바꾼다.

### 2. ★★ **`cells that differ: 1 / 17`** — `false` 는 **`cityOf incheon`** 한 행(Java `İNCHEON` · Kotlin `INCHEON`) · `keep57.kt` 는 **`INCHEON` / `İNCHEON`**

**출력**

```text
===== java -Duser.language=tr -Duser.country=TR -cp o57j Legacy57 > j57tr.txt =====
(exit 0)
===== java -Duser.language=tr -Duser.country=TR -cp o57k:kotlin-stdlib.jar Idiom57Kt > k57tr.txt =====
(exit 0)
===== python3 pair57.py j57tr.txt k57tr.txt =====
case	input	Java	Kotlin	same
grade	95	A	A	true
grade	90	A	A	true
grade	85	B	B	true
grade	80	B	B	true
grade	70	C	C	true
fee	Card(1000)	30	30	true
fee	Cash(1000)	0	0	true
fee	Transfer(1000)	500	500	true
cityOf	null user	none	none	true
cityOf	null address	none	none	true
cityOf	null city	none	none	true
cityOf	seoul	SEOUL	SEOUL	true
cityOf	incheon	İNCHEON	INCHEON	false
total	[]	0	0	true
total	[(100,2) (50,0) (30,-1) (7,3)]	221	221	true
total	[(2000000000,1) (2000000000,1)]	-294967296	-294967296	true
nextId	x3	1 2 3	1 2 3	true
cells that differ: 1 / 17
(exit 0)
===== kotlinc keep57.kt -d o57kp =====
(exit 0)
===== java -Duser.language=tr -Duser.country=TR -cp o57kp:kotlin-stdlib.jar Keep57Kt =====
uppercase()                    = INCHEON
uppercase(Locale.getDefault()) = İNCHEON
(exit 0)
```

**왜 그런가**

- ★★★ Java `toUpperCase()` 는 **기본 로케일**(여기서는 `tr`)의 규칙을 쓴다 — 터키어에서 `i` 의 대문자는 **점 있는 `İ`** 다. Kotlin `uppercase()` 는 **`Locale.ROOT`** 를 쓴다(7번의 발췌·`javap`).
- ★★ `seoul` 은 `i` 가 없어 같다. 1번에서 0 칸이었던 것은 **입력이 아니라 환경** 때문이다 — 기본 로케일 `ko` 에서는 두 규칙이 같은 답을 낸다.
- ★★ `keep57.kt` — 로케일을 **명시한** `uppercase(Locale.getDefault())` 는 Java 와 같은 `İNCHEON` 을 냈다. 원본 동작을 그대로 옮기려면 이 모양이다.

### 3. ★★★ **둘 다 `exit 1`** — Kotlin 은 「`Add the 'is Refund' branch or an 'else' branch.`」(빠진 타입 이름을 댄다) · Java 는 「`the switch expression does not cover all possible input values`」

```kotlin
// pay57v2.kt
sealed interface Payment
class Card(val amount: Int) : Payment
class Cash(val amount: Int) : Payment
class Transfer(val amount: Int) : Payment
class Refund(val amount: Int) : Payment

fun fee(p: Payment): Int = when (p) {
    is Card -> p.amount * 3 / 100
    is Cash -> 0
    is Transfer -> 500
}

fun main() {
    println(fee(Refund(1000)))
}
```

```java
// PaySwitch57.java
public class PaySwitch57 {
    sealed interface Payment permits Card, Cash, Transfer, Refund {}
    record Card(int amount) implements Payment {}
    record Cash(int amount) implements Payment {}
    record Transfer(int amount) implements Payment {}
    record Refund(int amount) implements Payment {}

    static int fee(Payment p) {
        return switch (p) {
            case Card c -> c.amount() * 3 / 100;
            case Cash c -> 0;
            case Transfer t -> 500;
        };
    }

    public static void main(String[] args) {
        System.out.println(fee(new Refund(1000)));
    }
}
```

**출력**

```text
===== kotlinc pay57v2.kt -d o57p2 =====
pay57v2.kt:7:28: error: 'when' expression must be exhaustive. Add the 'is Refund' branch or an 'else' branch.
fun fee(p: Payment): Int = when (p) {
                           ^^^^
(exit 1)
===== javac -d o57s PaySwitch57.java =====
PaySwitch57.java:9: error: the switch expression does not cover all possible input values
        return switch (p) {
               ^
1 error
(exit 1)
```

**왜 그런가**

- ★★★ 주체가 **봉인 타입**이면 컴파일러가 하위 타입 목록을 알고, `when`·`switch` 가 그것을 다 덮었는지 센다. `Refund` 가 늘었는데 분기는 그대로라 **덮지 못했다.**
- ★★ Kotlin 진단은 **빠진 가지의 이름**(`is Refund`)과 **두 해법**(가지 추가 · `else`)을 말한다. `javac` 는 「다 덮지 못했다」까지만 말한다.
- ★ 이 보호가 분기하는 **모든 자리**에서 동시에 걸리는 것은 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3)이 셌다.

### 4. ★★★ **둘 다 컴파일된다(`exit 0`)** — Java 사슬은 실행에서 **`threw java.lang.IllegalStateException: unknown payment`** · Kotlin `else` 판은 **`Refund(1000) -> 500`**(예외 없이)

**출력**

```text
===== javac -d o57c PayChain57.java =====
(exit 0)
===== java -cp o57c PayChain57 =====
Refund(1000) -> threw java.lang.IllegalStateException: unknown payment
(exit 0)
===== kotlinc pay57e.kt -d o57e =====
(exit 0)
===== java -cp o57e:kotlin-stdlib.jar Pay57eKt =====
Refund(1000) -> 500
(exit 0)
```

**왜 그런가**

- ★★★ Java `instanceof` 사슬은 **완결성 검사 대상이 아니다** — 컴파일러는 `Payment` 가 몇 종류인지 보지 않는다. 사람이 쓴 `else throw` 가 **실행 중에** 새 타입을 만난다.
- ★★★ Kotlin `else ->` 는 **「나머지 전부」** 라는 가지다 — 새 타입도 거기로 흘러가 `Transfer` 의 요금 `500` 을 받았다. 8번이 이 차이를 다룬다.

### 5. ★★ **`true` 는 `Tern57`·`Tern57Kt` 의 `pick`·`grade` 두 쌍뿐** · 마지막 줄 **`pairs with the same opcode sequence: 2 / 6`**

**출력**

```text
===== javac -d o57t Tern57.java =====
(exit 0)
===== kotlinc tern57.kt -d o57u =====
(exit 0)
===== python3 ops57.py o57t:Tern57:pick o57u:Tern57Kt:pick o57t:Tern57:grade o57u:Tern57Kt:grade o57j:Legacy57:grade o57k:Idiom57Kt:grade o57j:Legacy57:fee o57k:Idiom57Kt:fee o57j:Legacy57:cityOf o57k:Idiom57Kt:cityOf o57j:Legacy57:total o57k:Idiom57Kt:total =====
pair	Java ops	Kotlin ops	same sequence
Tern57.pick / Tern57Kt.pick	6	6	true
Tern57.grade / Tern57Kt.grade	12	12	true
Legacy57.grade / Idiom57Kt.grade	16	12	false
  Java  : iload_0 bipush if_icmplt ldc astore_1 goto iload_0 bipush if_icmplt ldc astore_1 goto ldc astore_1 aload_1 areturn
  Kotlin: iload_0 bipush if_icmplt ldc goto iload_0 bipush if_icmplt ldc goto ldc areturn
Legacy57.fee / Idiom57Kt.fee	26	31	false
  Java  : aload_0 instanceof ifeq aload_0 checkcast getfield iconst_3 imul bipush idiv ireturn aload_0 instanceof ifeq iconst_0 ireturn aload_0 instanceof ifeq sipush ireturn new dup ldc invokespecial athrow
  Kotlin: aload_0 ldc invokestatic aload_0 astore_1 aload_1 instanceof ifeq aload_0 checkcast invokevirtual iconst_3 imul bipush idiv goto aload_1 instanceof ifeq iconst_0 goto aload_1 instanceof ifeq sipush goto new dup invokespecial athrow ireturn
Legacy57.cityOf / Idiom57Kt.cityOf	21	20	false
  Java  : aload_0 ifnonnull ldc areturn aload_0 getfield astore_1 aload_1 ifnonnull ldc areturn aload_1 getfield astore_2 aload_2 ifnonnull ldc areturn aload_2 invokevirtual areturn
  Kotlin: aload_0 dup ifnull invokevirtual dup ifnull invokevirtual dup ifnonnull pop ldc areturn astore_1 aload_1 getstatic invokevirtual dup ldc invokestatic areturn
Legacy57.total / Idiom57Kt.total	26	79	false
  Java  : iconst_0 istore_1 aload_0 invokeinterface astore_2 aload_2 invokeinterface ifeq aload_2 invokeinterface checkcast astore_3 aload_3 getfield ifle iload_1 aload_3 getfield aload_3 getfield imul iadd istore_1 goto iload_1 ireturn
  Kotlin: aload_0 ldc invokestatic aload_0 checkcast astore_1 iconst_0 istore_2 aload_1 astore_3 new dup invokespecial checkcast astore iconst_0 istore aload_3 invokeinterface astore aload invokeinterface ifeq aload invokeinterface astore aload checkcast astore iconst_0 istore aload invokevirtual ifle iconst_1 goto iconst_0 ifeq aload aload invokeinterface pop goto aload checkcast nop checkcast astore_1 iconst_0 istore_2 aload_1 invokeinterface astore_3 aload_3 invokeinterface ifeq aload_3 invokeinterface astore iload_2 aload checkcast astore istore iconst_0 istore aload invokevirtual aload invokevirtual imul istore iload iload iadd istore_2 goto iload_2 ireturn
pairs with the same opcode sequence: 2 / 6
(exit 0)
```

```text
===== javap -c -p -cp o57t Tern57 | sed -n '/int pick(/,/ireturn/p' =====
  static int pick(boolean, int, int);
    Code:
       0: iload_0
       1: ifeq          8
       4: iload_1
       5: goto          9
       8: iload_2
       9: ireturn
(exit 0)
===== javap -c -p -cp o57u Tern57Kt | sed -n '/int pick(/,/ireturn/p' =====
  public static final int pick(boolean, int, int);
    Code:
       0: iload_0
       1: ifeq          8
       4: iload_1
       5: goto          9
       8: iload_2
       9: ireturn
(exit 0)
```

**왜 그런가**

- ★★★ **`if` 식 = Java 삼항** — 둘 다 조건 분기 뒤 **값을 스택에 남겨** 바로 반환한다(`iload` · `goto` · `ireturn`). 명령이 한 글자도 같다.
- ★★ **Java `if` 문 대입**(`Legacy57.grade`)은 `astore_1`/`aload_1` 로 **지역 변수 `g`** 를 거친다 — 16 대 12.
- ★★ `fee` 는 Kotlin 에 인자 검사와 끝의 예외 던지기가 더 있고(9번), `cityOf` 는 Kotlin 이 `Locale.ROOT` 를 불러오고 결과 null 검사를 붙이며(7번), `total` 은 `filter` 가 **중간 `ArrayList`** 를 만든다(26 대 79 — [47번 주제](../47-sequences-lazy-evaluation/) (3)).
- ★ 명령 수는 **속도가 아니다** — 시간은 재지 않았다.

### 6. ★★ 네 입력은 `same=true`, **`busan` 만 `early=no code for busan` · `chain=no city` · `false`** · 마지막 줄 **`cells that differ: 1 / 5`**

**출력**

```text
===== kotlinc over57.kt -d o57o =====
(exit 0)
===== java -cp o57o:kotlin-stdlib.jar Over57Kt =====
input	early	chain	same
null user	no city	no city	true
null address	no city	no city	true
null city	no city	no city	true
seoul	seoul:02	seoul:02	true
busan	no code for busan	no city	false
cells that differ: 1 / 5
(exit 0)
```

**왜 그런가**

- ★★★ `chain` 의 `?: "no city"` 는 **사슬 안 어느 `?.let` 이 null 을 내든** 받는다 — `areaCode("busan")` 이 `null` 이라 맨 안쪽 `let` 이 `null` 을 냈고, 그것이 「도시가 없다」로 읽혔다.
- ★★ `early` 는 **실패 이유마다 `?: return` 을 따로** 두었다 — 도시가 없을 때와 번호가 없을 때가 다른 문자열이 된다. 같은 함정의 한 겹짜리 판은 [14번 주제](../14-scope-functions/) (4).

### 7. ★★★ **컴파일 오류** — 「`'fun String.toUpperCase(): String' is deprecated. Use uppercase() instead.`」 · 선언의 `errorSince = "2.1"` · 그래서 고르게 되는 `uppercase()` 는 **`Locale.ROOT`** 라 2번에서 갈렸다

```kotlin
// upper57.kt
fun shout(s: String): String = s.toUpperCase()

fun main() {
    println(shout("incheon"))
}
```

**출력**

```text
===== kotlinc upper57.kt -d o57up =====
upper57.kt:1:34: error: 'fun String.toUpperCase(): String' is deprecated. Use uppercase() instead.
fun shout(s: String): String = s.toUpperCase()
                                 ^^^^^^^^^^^
(exit 1)
===== javap -c -p -cp o57k Idiom57Kt | sed -n '/String cityOf(/,/^$/p' =====
  public static final java.lang.String cityOf(User);
    Code:
       0: aload_0
       1: dup
       2: ifnull        19
       5: invokevirtual #55                 // Method User.getAddress:()LAddress;
       8: dup
       9: ifnull        19
      12: invokevirtual #61                 // Method Address.getCity:()Ljava/lang/String;
      15: dup
      16: ifnonnull     23
      19: pop
      20: ldc           #63                 // String none
      22: areturn
      23: astore_1
      24: aload_1
      25: getstatic     #69                 // Field java/util/Locale.ROOT:Ljava/util/Locale;
      28: invokevirtual #73                 // Method java/lang/String.toUpperCase:(Ljava/util/Locale;)Ljava/lang/String;
      31: dup
      32: ldc           #75                 // String toUpperCase(...)
      34: invokestatic  #78                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullExpressionValue:(Ljava/lang/Object;Ljava/lang/String;)V
      37: areturn
(exit 0)
```

```text
===== unzip -o -q kotlin-stdlib-sources.jar jvmMain/kotlin/text/StringsJVM.kt =====
(exit 0)
===== sed -n '128,134p;136,146p' jvmMain/kotlin/text/StringsJVM.kt =====
/**
 * Returns a copy of this string converted to upper case using the rules of the default locale.
 */
@Deprecated("Use uppercase() instead.", ReplaceWith("uppercase(Locale.getDefault())", "java.util.Locale"))
@DeprecatedSinceKotlin(warningSince = "1.5", errorSince = "2.1")
@kotlin.internal.InlineOnly
public actual inline fun String.toUpperCase(): String = (this as java.lang.String).toUpperCase()
/**
 * Returns a copy of this string converted to upper case using Unicode mapping rules of the invariant locale.
 *
 * This function supports one-to-many and many-to-one character mapping,
 * thus the length of the returned string can be different from the length of the original string.
 *
 * @sample samples.text.Strings.uppercase
 */
@SinceKotlin("1.5")
@kotlin.internal.InlineOnly
public actual inline fun String.uppercase(): String = (this as java.lang.String).toUpperCase(Locale.ROOT)
(exit 0)
```

**왜 그런가**

- ★★★ stdlib 가 옛 `toUpperCase()` 에 **`@DeprecatedSinceKotlin(warningSince = "1.5", errorSince = "2.1")`** 을 달았다 — 2.1 부터 **경고가 아니라 오류**다. 이것은 문법 규칙이 아니라 **라이브러리의 폐기 일정을 컴파일러가 집행**한 것이다.
- ★★★ KDoc 이 두 계약을 가른다 — `toUpperCase()` 「`using the rules of the default locale`」 · `uppercase()` 「`using Unicode mapping rules of the invariant locale`」. 바이트코드에도 `getstatic java/util/Locale.ROOT` 가 박혀 있다(위 덤프의 오프셋 `25`).
- ★★ 그러니 옮기는 사람은 **오류를 없애려고 `uppercase()` 로 바꾸는 순간 동작을 바꾼다** — 기본 로케일이 `tr` 인 환경에서만 드러난다(2번). 원래 동작은 `@Deprecated` 의 `ReplaceWith` 가 적어 둔 `uppercase(Locale.getDefault())` 다.

### 8. ★★ `else ->` 는 **완결성 검사를 그 자리에서 끈다** — 새 타입이 오류 대신 `else` 로 흘러간다 · **Kotlin `else` 판이 더 조용하다**(Java 는 예외라도 난다)

**왜 그런가**

- ★★★ `pay57v2.kt` 는 「덮지 못한 타입」이 있어 오류였다. `pay57e.kt` 는 `else` 가 **남은 전부를 덮으므로** 컴파일러가 셀 것이 없다 — 3번의 보호가 **사라졌다.**
- ★★ Java 원본의 `else { throw … }` 는 적어도 **실행에서 예외**를 낸다. Kotlin `else -> 500` 은 **그럴듯한 값**을 내므로 로그에도 안 남는다 — [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이 인용한 「`A match-all clause risks sweeping exhaustiveness errors under the rug`」의 뜻이 이것이다.
- ★ 그래서 봉인 계층 위의 `when` 에서 **「Kotlin 답게」는 `else` 를 지우는 쪽**이다.

### 9. ★★ Java 는 **사람이 쓴 `new IllegalStateException` · `athrow`**, Kotlin 은 **컴파일러가 쓴 `new kotlin/NoWhenBranchMatchedException` · `athrow`** — 같은 자리 · 도는 때는 **컴파일할 때 몰랐던 하위 타입이 런타임에 들어올 때**

**출력**

```text
===== javap -c -p -cp o57j Legacy57 | sed -n '/int fee(/,/athrow/p' =====
  static int fee(Legacy57$Payment);
    Code:
       0: aload_0
       1: instanceof    #13                 // class Legacy57$Card
       4: ifeq          20
       7: aload_0
       8: checkcast     #13                 // class Legacy57$Card
      11: getfield      #15                 // Field Legacy57$Card.amount:I
      14: iconst_3
      15: imul
      16: bipush        100
      18: idiv
      19: ireturn
      20: aload_0
      21: instanceof    #19                 // class Legacy57$Cash
      24: ifeq          29
      27: iconst_0
      28: ireturn
      29: aload_0
      30: instanceof    #21                 // class Legacy57$Transfer
      33: ifeq          40
      36: sipush        500
      39: ireturn
      40: new           #23                 // class java/lang/IllegalStateException
      43: dup
      44: ldc           #25                 // String unknown payment
      46: invokespecial #27                 // Method java/lang/IllegalStateException."<init>":(Ljava/lang/String;)V
      49: athrow
(exit 0)
===== javap -c -p -cp o57k Idiom57Kt | sed -n '/int fee(/,/ireturn/p' =====
  public static final int fee(Payment);
    Code:
       0: aload_0
       1: ldc           #21                 // String p
       3: invokestatic  #27                 // Method kotlin/jvm/internal/Intrinsics.checkNotNullParameter:(Ljava/lang/Object;Ljava/lang/String;)V
       6: aload_0
       7: astore_1
       8: aload_1
       9: instanceof    #29                 // class Card
      12: ifeq          30
      15: aload_0
      16: checkcast     #29                 // class Card
      19: invokevirtual #33                 // Method Card.getAmount:()I
      22: iconst_3
      23: imul
      24: bipush        100
      26: idiv
      27: goto          62
      30: aload_1
      31: instanceof    #35                 // class Cash
      34: ifeq          41
      37: iconst_0
      38: goto          62
      41: aload_1
      42: instanceof    #37                 // class Transfer
      45: ifeq          54
      48: sipush        500
      51: goto          62
      54: new           #39                 // class kotlin/NoWhenBranchMatchedException
      57: dup
      58: invokespecial #43                 // Method kotlin/NoWhenBranchMatchedException."<init>":()V
      61: athrow
      62: ireturn
(exit 0)
```

**왜 그런가**

- ★★★ `else` 없는 봉인 `when` 도 JVM 에서는 `instanceof` 사슬이라 **「어느 것에도 안 맞음」의 출구**가 필요하다 — 컴파일러가 그 출구를 **예외 던지기로** 채웠다. Java 원본의 `else throw` 를 사람 대신 쓴 셈이다.
- ★★ 같은 모듈을 다시 컴파일하면 3번처럼 **그 전에 오류**가 나므로, 이 명령이 도는 것은 **봉인 계층이 다른 모듈에서 바뀌고 이쪽은 재컴파일되지 않은** 경우다([06번 주제](../06-when-expression/) (7)).
- ★ Kotlin 쪽 앞머리의 `checkNotNullParameter` 는 인자 `p` 가 non-null 이라 붙은 검사다([03번 주제](../03-null-safe-types/) (4)).

### 10. ★★ **증명하지 않는다** — 1번은 **그 17개 입력과 로케일 `ko`** 에서의 0 칸이다 · 2번은 **환경을 바꾸자 1 칸이 갈린 반례**다

**왜 그런가**

- ★★★ 같은 입력에 같은 출력은 **관찰**이다. 「모든 입력·모든 환경에서 같다」는 이 창으로 원리상 못 보인다 — 그래서 2-summary (0)의 **제5의 상태**(실행 창과 바이트코드 창으로 나눠 물었다)로 적었다.
- ★★ 2번의 갈림은 **입력을 늘려서는 절대 안 나온다** — 소스도 입력도 같고 JVM 플래그만 달랐다. 옮긴 코드를 대조할 때 **환경(로케일·시간대)을 한 번 바꿔 보는 것**이 입력을 늘리는 것과 다른 축이다.
- ★ 거꾸로 5번의 「같은 명령 줄」은 **입력과 무관하게** 같다는 강한 근거지만, 같은 쌍은 **2 / 6** 뿐이었다.

### 11. ★★ **관찰이다**(출력이 갈렸다) · 「읽기 어렵다」는 **설계 권고층** — 이 문서는 **규약 문서의 출처를 확인하지 못했다**

**왜 그런가**

- ★★★ `busan` 칸은 **실행 결과**다 — 누가 읽든 `no code for busan` 과 `no city` 는 다르다. 「실패 이유가 뭉개진다」는 판단이 아니라 **출력이 보인 것**이다.
- ★★ 「`?.let` 을 네 겹 겹치면 읽기 어렵다」·「`also`/`apply` 를 사슬로 이으면 `it`/`this` 를 따라가기 힘들다」는 **컴파일러도 실행도 말하지 않는** 사람의 판단이다.
- ★★ 그 판단을 받칠 [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html) 는 **받아 둔 사본이 없고 네트워크를 쓰지 않아** 확인하지 못했다(제3의 상태 — 못 잰 것). 그래서 「규약이 그렇게 권한다」고 적지 않았다.

### 12. ★★ Java 원본은 **봉인되지 않은 인터페이스 + `instanceof` 사슬**이고, 3번의 Java 판은 **`sealed … permits` + 레코드 + 패턴 `switch`** 다 — **Kotlin 만의 것이 아니다**(Java 21 도 잡는다)

**왜 그런가**

- ★★★ 완결성 검사를 켜는 것은 언어 이름이 아니라 **「닫힌 하위 타입 목록 + 그 목록을 세는 분기 문법」** 두 가지다. Java 21 은 `sealed` 와 패턴 `switch` 로 둘 다 갖췄다([Java 23번](../../../java/syntax/23-switch-pattern-matching/) · [Java 15번](../../../java/syntax/15-sealed-classes/)).
- ★★ 그러니 「Java 코드를 Kotlin 답게」의 이득은 **Java 8 식 사슬을 옮길 때** 가장 크다 — 같은 옮김을 Java 21 안에서 해도 같은 보호를 얻는다.
- ★ 이 판에서 잰 차이는 **진단 문구** 하나다 — Kotlin 은 빠진 타입 이름(`is Refund`)을 대고 `javac` 는 안 댄다(3번). 그 밖의 차이(`permits`·`non-sealed`·런타임 안전망)는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이 원고째 정리했다 — 이 문서는 **다시 재지 않았다.**

## 실행 검증

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 실행 시간을 찍지 않았다 | 두 판 격자 · 로케일 판 격자 · 과한 칸 격자 · 갈린 칸 수 |
| ★ 환경에 매인다 — 첫 격자는 **기본 로케일 `ko`/`KR`** 에서 찍었다 | 진단 문구와 `줄:칸` · `javap` 의 명령과 상수 풀 번호 · 명령 비교 수 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.

실측 — `capture.sh blocks` 와 `capture.sh blocks-re` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 — **블록 109개 · 동일 109 · 흔들린 칸 0 · ★고칠 것 0**(54\~58 다섯 주제를 한 캡처로 받았다 — 이 주제 몫은 출력 10 · 소스 13 · 환경 5). 추가한 정규화 규칙은 없다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `Legacy57.java` · `idiom57.kt` · `pair57.py` | ★★★ 두 판 격자 — 사례 5 × 입력 17 | `javac`·`kotlinc` → `java` 두 번(표준 출력을 파일로) → `diff` → `pair57.py`(행마다 칸 수 검사 · 갈린 칸 수를 센다) |
| 같은 둘 + `keep57.kt` | ★★ 로케일 판 격자 | `java -Duser.language=tr -Duser.country=TR` |
| `pay57v2.kt` · `PaySwitch57.java` | ★★ 하위 타입 추가 — 컴파일 오류 | `kotlinc` · `javac` (종료 코드째) |
| `PayChain57.java` · `pay57e.kt` | ★★ 하위 타입 추가 — 조용히 통과 | `javac`·`kotlinc` → `java` |
| `Tern57.java` · `tern57.kt` · `ops57.py` | ★★ 명령 줄 비교 여섯 쌍 | `javac`·`kotlinc` → `ops57.py`(안에서 `javap -c -p` 12회) · 덤프는 `javap` 를 전부 받은 뒤 `sed` |
| `over57.kt` | ★ 과한 칸 격자 | `kotlinc` → `java` |
| `upper57.kt` · `StringsJVM.kt`(stdlib 소스 jar) | ★ `toUpperCase` 오류 · 두 함수의 선언 | `kotlinc` · `unzip` → `sed -n` |

**구현 의존 항목** — 명령 줄의 모양(지역 변수 슬롯 · `NoWhenBranchMatchedException` · 인라인된 `filter`)은 **kotlinc 2.4.20 · javac 21 의 산출물**이다. `toUpperCase()` 가 오류인 것은 **stdlib 2.4.20 의 폐기 표지**다.\
반면 **봉인 주체 `when` 의 완결성 오류** · **`if` 가 식이라는 것** · **`uppercase()` 가 불변 로케일이라는 KDoc 계약**은 판이 올라도 유지되는 쪽이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **두 판을 갈라놓은 것은 입력이 아니라 로케일이었다** — 1번에서 0 칸이던 격자가 JVM 플래그 하나로 1 칸이 됐다. 그리고 **뜻을 바꾼 쪽은 Kotlin 판**이었다(`toUpperCase` 를 글자 그대로 옮기면 컴파일 오류라 `uppercase` 로 바꿀 수밖에 없다).
2. ★★ **`when` + `else` 가 Java `else throw` 보다 더 조용했다** — 「Kotlin 이 더 안전하다」가 `else` 한 줄로 뒤집힌다.
3. ★ **Java 21 패턴 `switch` 도 같은 자리에서 막았다** — 「컴파일러가 새 하위 타입을 잡아 준다」는 Kotlin 고유가 아니었다.
