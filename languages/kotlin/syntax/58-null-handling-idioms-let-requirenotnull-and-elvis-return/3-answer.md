# kotlin/syntax/58 — null 처리 관용구 — `?.let`·`requireNotNull`·엘비스 + `return` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javac`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.
> ★ 소스 펜스의 첫 줄(파일명 주석)은 실파일에 없다 — 줄 번호는 그 다음 줄을 1 로 센다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **계층은 결과를 하나도 안 바꾼다(`0 / 6`)** — `?: return`·`?.let` 은 예외 없이 `null`(`8 / 24`) · `requireNotNull` 은 `IllegalArgumentException` · `checkNotNull`·`?: error()` 는 `IllegalStateException` · `!!` 는 메시지 `null` 인 NPE · 첫 프레임은 **언제나 그 수단이 적힌 줄**

**출력**

```text
===== kotlinc grid58.kt -d o58g =====
(exit 0)
===== java -cp o58g:kotlin-stdlib.jar Grid58Kt =====
layer	means	thrown	message	first frame	caller got
parse	?: return	-	-	-	null
parse	?.let	-	-	-	null
parse	requireNotNull	IllegalArgumentException	not a number: 12x	parseLayer:10	(exception)
parse	checkNotNull	IllegalStateException	not a number: 12x	parseLayer:11	(exception)
parse	!!	NullPointerException	null	parseLayer:12	(exception)
parse	?: error()	IllegalStateException	not a number: 12x	parseLayer:13	(exception)
api	?: return	-	-	-	null
api	?.let	-	-	-	null
api	requireNotNull	IllegalArgumentException	name is required	apiLayer:22	(exception)
api	checkNotNull	IllegalStateException	name is required	apiLayer:23	(exception)
api	!!	NullPointerException	null	apiLayer:24	(exception)
api	?: error()	IllegalStateException	name is required	apiLayer:25	(exception)
core	?: return	-	-	-	null
core	?.let	-	-	-	null
core	requireNotNull	IllegalArgumentException	no price for pear	coreLayer:36	(exception)
core	checkNotNull	IllegalStateException	no price for pear	coreLayer:37	(exception)
core	!!	NullPointerException	null	coreLayer:38	(exception)
core	?: error()	IllegalStateException	no price for pear	coreLayer:39	(exception)
view	?: return	-	-	-	null
view	?.let	-	-	-	null
view	requireNotNull	IllegalArgumentException	nickname missing	viewLayer:50	(exception)
view	checkNotNull	IllegalStateException	nickname missing	viewLayer:51	(exception)
view	!!	NullPointerException	null	viewLayer:52	(exception)
view	?: error()	IllegalStateException	nickname missing	viewLayer:53	(exception)
thrown kinds: none 8 · IllegalArgumentException 4 · IllegalStateException 8 · NullPointerException 4 (of 24)
means whose outcome differs between layers: 0 / 6
cells with no exception: 8 / 24
(exit 0)
```

**왜 그런가**

- ★★★ 수단마다 던지는 예외는 **수단의 정의**(언어 규칙 · KDoc)가 정한다 — 어느 계층의 함수 안에 적혀 있는지는 수단이 모른다. 그래서 같은 행 여섯 개가 네 번 되풀이된다.
- ★★ `requireNotNull`·`checkNotNull`·`error` 는 `inline` 이라 던지는 코드가 **부른 함수 안에 풀린다** — 첫 프레임이 stdlib 가 아니라 `parseLayer:10` 같은 **그 줄**이다.
- ★★ `?: return null` 과 `?.let { … }` 은 둘 다 `null` 을 돌려준다 — **부른 쪽에서는 구별되지 않는다**(7번).
- ★ `!!` 의 메시지가 `null` 인 까닭은 [03번 주제](../03-null-safe-types/) (3) — `Intrinsics.checkNotNull(Object)` 에 메시지 인자가 없다.

### 2. ★★★ `A` 는 **같은 줄**(21), `B` 는 **넘기는 줄**(27, 태어난 줄 26 의 다음), `C` 는 **다른 함수 `firstLength:5`** 에서 JVM 문구로, `D` 는 **안 터진다**

```java
// Store58.java
import java.util.HashMap;
import java.util.Map;

public class Store58 {
    private static final Map<String, String> names = new HashMap<>();
    static { names.put("u1", "kim"); }

    public static String findName(String id) {
        return names.get(id);
    }
}
```

```kotlin
// plat58.kt
// Java 가 준 null 이 어디서 터지나 — 태어난 줄과 터진 줄
fun here(): Int = Throwable().stackTrace[1].lineNumber

fun greet(name: String): String = "hi " + name
fun firstLength(names: List<String>): Int = names[0].length

fun probe(label: String, block: () -> Int) {
    try {
        block()
        println("$label -> no exception")
    } catch (e: Exception) {
        val f = e.stackTrace[0]
        println("$label -> ${e.javaClass.simpleName}: ${e.message}")
        println("    first frame ${f.methodName}:${f.lineNumber}")
    }
}

fun main() {
    var born = 0
    probe("A") {
        born = here(); val n = Store58.findName("u9")!!
        n.length
    }
    println("    null born at line $born")
    probe("B") {
        val n = Store58.findName("u9"); born = here()
        greet(n).length
    }
    println("    null born at line $born")
    probe("C") {
        val n = Store58.findName("u9"); born = here()
        val names = listOf(n)
        firstLength(names)
    }
    println("    null born at line $born")
    probe("D") {
        val n = Store58.findName("u9"); born = here()
        val names: List<String> = listOf(n)
        names.size
    }
    println("    null born at line $born")
}
```

**출력**

```text
===== javac -d o58j Store58.java =====
(exit 0)
===== kotlinc -cp o58j plat58.kt -d o58p =====
(exit 0)
===== java -cp o58p:o58j:kotlin-stdlib.jar Plat58Kt =====
A -> NullPointerException: null
    first frame main$lambda$0:21
    null born at line 21
B -> NullPointerException: null
    first frame main$lambda$1:27
    null born at line 26
C -> NullPointerException: Cannot invoke "String.length()" because the return value of "java.util.List.get(int)" is null
    first frame firstLength:5
    null born at line 31
D -> no exception
    null born at line 37
(exit 0)
```

```text
===== javap -c -p -cp o58p Plat58Kt | grep -E 'private static final int main\$lambda|Store58\.findName|Intrinsics\.checkNotNull:|Method greet|Method firstLength|listOf' =====
  private static final int main$lambda$0(kotlin.jvm.internal.Ref$IntRef);
       9: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      13: invokestatic  #197                // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
  private static final int main$lambda$1(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #197                // Method kotlin/jvm/internal/Intrinsics.checkNotNull:(Ljava/lang/Object;)V
      18: invokestatic  #201                // Method greet:(Ljava/lang/String;)Ljava/lang/String;
  private static final int main$lambda$2(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #207                // Method kotlin/collections/CollectionsKt.listOf:(Ljava/lang/Object;)Ljava/util/List;
      19: invokestatic  #209                // Method firstLength:(Ljava/util/List;)I
  private static final int main$lambda$3(kotlin.jvm.internal.Ref$IntRef);
       2: invokestatic  #194                // Method Store58.findName:(Ljava/lang/String;)Ljava/lang/String;
      14: invokestatic  #207                // Method kotlin/collections/CollectionsKt.listOf:(Ljava/lang/Object;)Ljava/util/List;
(exit 0)
```

**왜 그런가**

- ★★★ `A` 의 `!!` 와 `B` 의 「non-null 인자로 넘김」은 둘 다 **`Intrinsics.checkNotNull`** 이 **그 줄**에 박힌다(`javap` — `main$lambda$0`·`$1`). `B` 의 것은 컴파일러가 넣었다 — 그래서 `greet` 안의 인자 검사까지 **가지도 않는다.**
- ★★★ `C`·`D` 의 `listOf(n)` 에는 검사가 없다 — 원소 타입까지 들여다보지 않는다. `C` 는 `firstLength` 가 **원소를 꺼내 `.length` 를 부를 때** JVM 이 터뜨렸고(helpful NPE — `Store58` 이라는 말이 없다), `D` 는 꺼내지 않아 **끝까지 조용했다.**
- ★ 거리 — `A` 0줄 · `B` 1줄 · `C` **다른 함수** · `D` **무한**. 거리가 멀수록 스택이 원인을 가리키지 않는다.

### 3. ★★ **`B` 만 바뀐다** — `Parameter specified as non-null is null: method Plat58Kt.greet, parameter name` · 첫 프레임 **`greet:-1`**

**출력**

```text
===== kotlinc -Xno-call-assertions -cp o58j plat58.kt -d o58q =====
(exit 0)
===== java -cp o58q:o58j:kotlin-stdlib.jar Plat58Kt =====
A -> NullPointerException: null
    first frame main$lambda$0:21
    null born at line 21
B -> NullPointerException: Parameter specified as non-null is null: method Plat58Kt.greet, parameter name
    first frame greet:-1
    null born at line 26
C -> NullPointerException: Cannot invoke "String.length()" because the return value of "java.util.List.get(int)" is null
    first frame firstLength:5
    null born at line 31
D -> no exception
    null born at line 37
(exit 0)
```

**왜 그런가**

- ★★ `-Xno-call-assertions` 는 2번 `javap` 의 `B` 쪽 `checkNotNull`(**부르는 쪽** 검사)을 뺀다. 그러면 `null` 이 `greet` 안까지 들어가 `greet` 의 `checkNotNullParameter` 에 걸린다 — **메시지에 함수와 인자 이름**이 생겼다([03번 주제](../03-null-safe-types/) (4)의 문구).
- ★ 대신 첫 프레임의 줄 번호가 **`-1`**(줄 정보 없음)이다 — 인자 검사는 소스 줄에 대응하지 않았다(이 판의 관찰).
- ★ `A` 의 `!!` 는 **요청**이라 플래그와 무관하다. `C`·`D` 는 애초에 검사가 없었다.

### 4. ★★ 둘 다 **`3 of 5`** 를 보냈고 **표준 오류는 `B` 의 `skip u2`·`skip u4` 뿐** · `status` 는 **`u1` 만 이메일이 있는데 `no email`**

**출력**

```text
===== kotlinc let58.kt -d o58l =====
(exit 0)
===== java -cp o58l:kotlin-stdlib.jar Let58Kt 2>/dev/null =====
A sent 3 of 5: [a@x, c@x, e@x]
B sent 3 of 5: [a@x, c@x, e@x]
status u1 = no email
status u2 = no email
status u3 = ok
status u4 = no email
status u5 = ok
(exit 0)
===== java -cp o58l:kotlin-stdlib.jar Let58Kt >/dev/null =====
skip u2
skip u4
(exit 0)
```

**왜 그런가**

- ★★★ `A` 의 `?.let` 은 `email` 이 `null` 이면 블록을 **통째로 건너뛴다** — 흔적이 없다. `B` 는 같은 자리에서 **표준 오류로 한 줄**을 남기고 `return` 했다. 결과(보낸 목록)는 한 글자도 같다.
- ★★★ `statusOf(u1)` — `u1.email` 은 `"a@x"` 라 블록이 돌고, `lookup("a@x")` 가 `null` 을 돌려줬다. `?.let { }` 전체가 `null` 이 되니 `?:` 가 **`"no email"`** 을 골랐다. `u2`·`u4` 는 수신자가 `null` 이라 같은 글자다 — **두 까닭이 한 글자로 합쳐진다**(9번).

### 5. ★★ 진단 **하나** — `a` 의 `f.name.length`(4:32) · `smart cast to 'String' is impossible, because 'name' is a mutable property that could be mutated concurrently.` · `b`·`c`·`d` 는 통과

```kotlin
// smart58.kt
class Form(var name: String?, val code: String?)

fun a(f: Form): Int {
    if (f.name != null) return f.name.length
    return 0
}

fun b(f: Form): Int {
    if (f.code != null) return f.code.length
    return 0
}

fun c(f: Form): Int = f.name?.let { it.length } ?: 0

fun d(f: Form): Int {
    val n = f.name ?: return 0
    return n.length
}

fun main() {
    val f = Form("kim", "k1")
    println(listOf(a(f), b(f), c(f), d(f)))
}
```

**출력**

```text
===== kotlinc smart58.kt -d o58s =====
smart58.kt:4:32: error: smart cast to 'String' is impossible, because 'name' is a mutable property that could be mutated concurrently.
    if (f.name != null) return f.name.length
                               ^^^^^^
(exit 1)
```

**왜 그런가**

- ★★ `name` 은 `var` 프로퍼티라 검사(`!= null`)와 사용 사이에 **다른 코드가 바꿀 수 있다** — 컴파일러가 좁혀 주지 않는다. `code` 는 `val` 이라 된다.
- ★★ `c`·`d` 는 프로퍼티를 **한 번만 읽어** 안정된 값(`it` · 지역 `val n`)에 담는다 — 그래서 된다. kotlinc 는 한 번에 모든 에러를 보고하므로 진단이 하나면 나머지는 통과한 것이다.
- ★ 이 거부가 나오는 자리 아홉의 전수는 [04번 주제](../04-smart-casts/) (2).

### 6. ★ `apple x2 left=1` · `pear x1 (gift) left=4` · `rejected: 'apple,x'` · `rejected: ',3'` · `bug: unknown item passed validation: kiwi` · `caller error: qty must be positive: 0`

**출력**

```text
===== kotlinc form58.kt -d o58f =====
(exit 0)
===== java -cp o58f:kotlin-stdlib.jar Form58Kt =====
apple x2 left=1
pear x1 (gift) left=4
rejected: 'apple,x'
rejected: ',3'
bug: unknown item passed validation: kiwi
caller error: qty must be positive: 0
(exit 0)
```

**왜 그런가**

- ★★ `parse` 는 `?: return null` 로 **예외 없이** 거절한다 — `"apple,x"`(숫자 아님)·`",3"`(품목이 빈칸, `takeIf` 가 `null`).
- ★★ `"kiwi,1"` 은 파싱도 인자 계약도 통과하고 **내부**의 `checkNotNull(stock[item])` 에서 `IllegalStateException` → `bug:`. `"pear,0"` 은 **인자 계약**(`require(qty > 0)`)의 `IllegalArgumentException` → `caller error:`.
- ★ `note` 가 없는 줄은 `?.let { " ($it)" } ?: ""` 로 **그 칸만 비었다** — 표시 계층에서는 건너뛰는 것이 정상이다.

### 7. ★★ **멈춘다는 사실이 코드에 보이고, 그 자리에 흔적을 남길 수 있기 때문** — 4번의 표준 오류가 그 「흔적」 쪽을 보여 준다

- ★★ 1번에서 두 수단은 부른 쪽이 받은 값(`null`)이 같다 — **관찰로는 못 가른다.** 차이는 읽는 사람 쪽에 있다. `val n = v ?: return null` 은 「여기서 끝낸다」가 **줄머리의 `return`** 으로 보이고, 뒤 코드가 `n` 을 non-null 로 **들여쓰기 없이** 쓴다. `?.let { … }` 은 끝내는 길이 **`?.` 한 글자 안에 묻힌다.**
- ★★ 그리고 `?:` 의 오른쪽은 **블록**이라 로그를 넣을 자리가 있다(`run { log(…); return }`) — 4번의 `B` 가 `skip u2`·`skip u4` 를 남긴 것이 그것이다. `?.let` 의 「`null` 쪽」에는 **코드를 둘 자리 자체가 없다.**

### 8. ★★ `requireNotNull` → **`IllegalArgumentException`**, `checkNotNull` → **`IllegalStateException`** — 로그에서 클래스가 **「누구 잘못인가」** 로 읽히기 때문

- ★★★ `coreLayer` 의 `null` 은 **맵에 있어야 할 키가 없는 것** — 부른 쪽이 아니라 **내 데이터의 사고**다. 그런데 `requireNotNull` 을 두면 `IllegalArgumentException`(KDoc 이 「인자가 틀렸다」에 붙인 클래스 — [51번 주제](../51-preconditions-require-check-error-todo/))이 나와, 로그를 보는 사람이 **호출자를 의심**한다.
- ★ 1번의 `0 / 6` 이 이 함정의 근거다 — `requireNotNull` 은 **자기가 어디 있는지 모르고** 늘 같은 클래스를 던진다. 클래스를 원인 분류로 쓰려면 **수단을 사람이 골라야** 한다.

### 9. ★★ **아니다** — `?.let { lookup(it) }` 의 **블록 결과가 `null`** 이어도 `?:` 로 간다 · 가르려면 `if (email == null) … else lookup(email) ?: …` 처럼 **두 `null` 을 따로** 다룬다

- ★★★ `x?.let { f(it) } ?: y` 에서 `?:` 가 보는 것은 **`?.let` 식 전체의 값**이다. 그 값이 `null` 이 되는 길이 둘 — 수신자 `x` 가 `null` · **블록 `f(it)` 가 `null`**. `u1` 은 뒤쪽이었다.
- ★ 안전하게 — 블록이 `null` 을 낼 수 없으면 그대로 써도 된다. 낼 수 있으면 `val e = u.email ?: return "no email"` 로 **먼저 수신자를 끝내고**, `lookup(e) ?: "lookup failed"` 로 **다른 글자**를 준다. 두 까닭이 한 글자로 합쳐지지 않게 하는 것이 요점이다.

### 10. ★★ **증명된 것 — 수단마다의 예외 클래스·메시지·첫 프레임·「예외 없음」** · **판단 — 어느 계층에 어느 수단** · `0 / 6` 이 「계층은 결과를 안 바꾼다」를 보여 **짝짓기가 관찰에서 안 나옴**을 증명한다

- ★★★ (5) 표의 오른쪽 칸(`IllegalArgumentException` = 부른 쪽 · 메시지가 남는다 · `?: return` 은 예외 없음 · Java 값은 다른 함수에서 터진다)은 **실행 블록이 근거**다.
- ★★★ 왼쪽 칸(「외부 입력은 `?: return`」·「공개 API 는 `requireNotNull`」·「`!!` 는 쓰지 않는다」)은 **이 문서의 판단**이고, 공식 규약 문서는 **열지 못해 출처 확인 못 함**이다.
- ★ 경계를 긋는 것이 `0 / 6` 이다 — 계층이 결과를 하나라도 바꿨다면 「이 계층에는 이 수단이 **맞다**」가 관찰로 설 수도 있었다. 하나도 안 바꿨으므로 **그 문장은 전부 설계 쪽**이다.

### 11. ★★ **원인 줄인 것 — `!!`(03)·05 의 B(대입)·2번 `A`·`B`** · **아닌 것 — 05 의 A(쓰는 줄 — 대입한 줄이 따로 있다)·2번 `C`(다른 함수)·`D`(안 터짐)**

- ★★ 첫 프레임은 **예외가 만들어진 자리**다. 검사를 **그 줄에** 두면(`!!` · 타입을 적은 대입 · non-null 인자로 넘기기) 그 자리가 원인 근처가 된다.
- ★★★ 검사가 **없는** 경로(플랫폼 타입을 추론에 맡김 · 컬렉션에 담음)는 **값을 쓰는 날** JVM 이 터뜨린다 — 그 줄은 원인이 아니라 **증상**이다. 2번 `C` 는 함수까지 달랐고 메시지에 Java 메서드 이름도 없었다.
- ★ 그래서 [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 의 「경계에서 즉시 검증」은 **스택을 원인 쪽으로 끌어당기는 일**이기도 하다 — 이 연결은 판단이다.

## 실행 검증

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 시간·주소·스레드를 찍지 않았다 | 격자 24행 · 세는 세 줄 · 예외 클래스·메시지·첫 프레임의 메서드와 줄 번호 |
| | 태어난 줄 · helpful NPE 문구(JDK 21.0.5) · 표준 출력/표준 오류 각각의 줄 |
| | `javap` 의 명령·상수 풀 번호 · 진단 문구와 `줄:칸` · 모든 **종료 코드** |

실측 — `capture.sh blocks` 와 `capture.sh blocks-re` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 — **블록 109개 · 동일 109 · 흔들린 칸 0 · ★고칠 것 0**(54\~58 다섯 주제를 한 캡처로 받았다 — 이 주제 몫은 출력 7 · 소스 6 · 환경 5). 추가한 정규화 규칙은 없다.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `grid58.kt` | ★★★ 판별 격자 — 경계 4 × 수단 6 · 세는 줄은 프로그램이 센다 | `kotlinc` → `java` |
| `Store58.java` + `plat58.kt` | ★★★ 태어난 줄 대 터진 줄 네 갈래 | `javac` → `kotlinc -cp` → `java` · `javap -c -p`(전부 받은 뒤 `grep`) |
| `plat58.kt`(`-Xno-call-assertions`) | ★★ 부르는 쪽 검사를 뺀 판 | `kotlinc` → `java` |
| `let58.kt` | ★★ `?.let` 의 무음 건너뜀 · `?.let ?:` | `kotlinc` → `java` 두 번(표준 출력 / 표준 오류를 따로) |
| `smart58.kt` | ★ 스마트 캐스트 거부 | `kotlinc`(`exit 1`) |
| `form58.kt` | 네 계층 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 부르는 쪽 `Intrinsics.checkNotNull` 의 위치 · 인자 검사 프레임의 줄 번호 `-1` · helpful NPE 문구 — 컴파일러·JDK 판의 산출물이다.\
반면 **`?.`·`!!` 의 의미**(언어) · **`require`/`check` 계열의 예외 클래스**(KDoc) · **스마트 캐스트 거부**(진단)는 판이 바뀌어도 그대로여야 하는 쪽이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **플랫폼 값을 non-null 인자로 넘기면 `greet` 안의 인자 검사(「`Parameter specified as non-null is null`」)가 아니라 부르는 줄의 `checkNotNull` 이 먼저 걸렸다** — 메시지가 `null` 이다. 03 편의 좋은 메시지는 **Java 가 부를 때**의 것이었다.
2. ★★ **`val names: List<String> = listOf(플랫폼 값)` 에 검사가 하나도 없었다**(`D`) — 타입을 적으면 검사가 생긴다는 05 편의 규칙이 **원소 자리에는 안 닿는다.**
3. ★ **그 부르는 쪽 검사를 끄자 메시지는 좋아졌는데 줄 번호가 `-1` 이 됐다** — 좋은 메시지와 좋은 줄 번호를 **한 번에 못 얻었다.**
