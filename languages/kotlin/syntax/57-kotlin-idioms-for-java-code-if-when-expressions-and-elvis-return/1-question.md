# kotlin/syntax/57 — Java 코드를 Kotlin 답게 — 식으로서의 `if`/`when`·엘비스 조기 반환 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 선행은 [06번 주제](../06-when-expression/)(`when` 식)와 [34번 주제](../34-exceptions-nothing-and-try-expression/)(`Nothing`)다.
> 문항 12개 중 예측형은 6개이고, 여섯 모두 코드블록이 붙는다.
> 이 주제의 모든 답은 **kotlinc 2.4.20 · Temurin JDK 21.0.5(`javac`·`java`·`javap`)** 에서 실제로 던져 받은 것이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 로직 두 판 (예측)

```java
// Legacy57.java
import java.util.List;

public class Legacy57 {
    // (a) 분기 대입
    static String grade(int score) {
        String g;
        if (score >= 90) {
            g = "A";
        } else if (score >= 80) {
            g = "B";
        } else {
            g = "C";
        }
        return g;
    }

    // (b) 다중 분기 — 하위 타입마다
    interface Payment {}
    static final class Card implements Payment { final int amount; Card(int a) { amount = a; } }
    static final class Cash implements Payment { final int amount; Cash(int a) { amount = a; } }
    static final class Transfer implements Payment { final int amount; Transfer(int a) { amount = a; } }

    static int fee(Payment p) {
        if (p instanceof Card) {
            return ((Card) p).amount * 3 / 100;
        } else if (p instanceof Cash) {
            return 0;
        } else if (p instanceof Transfer) {
            return 500;
        } else {
            throw new IllegalStateException("unknown payment");
        }
    }

    // (c) null 조기 반환
    static final class Address { final String city; Address(String c) { city = c; } }
    static final class User { final Address address; User(Address a) { address = a; } }

    static String cityOf(User user) {
        if (user == null) {
            return "none";
        }
        Address a = user.address;
        if (a == null) {
            return "none";
        }
        String c = a.city;
        if (c == null) {
            return "none";
        }
        return c.toUpperCase();
    }

    // (d) 루프 누적
    static final class Item { final int price; final int qty; Item(int p, int q) { price = p; qty = q; } }

    static int total(List<Item> items) {
        int sum = 0;
        for (Item i : items) {
            if (i.qty > 0) {
                sum += i.price * i.qty;
            }
        }
        return sum;
    }

    // (e) 싱글턴 · 정적 상태
    static final class Registry {
        private static int next = 0;
        private Registry() {}
        static int nextId() { return ++next; }
    }

    public static void main(String[] args) {
        for (int s : new int[] {95, 90, 85, 80, 70}) {
            System.out.println("grade\t" + s + "\t" + grade(s));
        }
        System.out.println("fee\tCard(1000)\t" + fee(new Card(1000)));
        System.out.println("fee\tCash(1000)\t" + fee(new Cash(1000)));
        System.out.println("fee\tTransfer(1000)\t" + fee(new Transfer(1000)));
        System.out.println("cityOf\tnull user\t" + cityOf(null));
        System.out.println("cityOf\tnull address\t" + cityOf(new User(null)));
        System.out.println("cityOf\tnull city\t" + cityOf(new User(new Address(null))));
        System.out.println("cityOf\tseoul\t" + cityOf(new User(new Address("seoul"))));
        System.out.println("cityOf\tincheon\t" + cityOf(new User(new Address("incheon"))));
        System.out.println("total\t[]\t" + total(List.of()));
        System.out.println("total\t[(100,2) (50,0) (30,-1) (7,3)]\t"
                + total(List.of(new Item(100, 2), new Item(50, 0), new Item(30, -1), new Item(7, 3))));
        System.out.println("total\t[(2000000000,1) (2000000000,1)]\t"
                + total(List.of(new Item(2000000000, 1), new Item(2000000000, 1))));
        System.out.println("nextId\tx3\t" + Registry.nextId() + " " + Registry.nextId() + " " + Registry.nextId());
    }
}
```

```kotlin
// idiom57.kt
// (a) 분기 대입
fun grade(score: Int): String =
    if (score >= 90) "A" else if (score >= 80) "B" else "C"

// (b) 다중 분기 — 하위 타입마다
sealed interface Payment
class Card(val amount: Int) : Payment
class Cash(val amount: Int) : Payment
class Transfer(val amount: Int) : Payment

fun fee(p: Payment): Int = when (p) {
    is Card -> p.amount * 3 / 100
    is Cash -> 0
    is Transfer -> 500
}

// (c) null 조기 반환
class Address(val city: String?)
class User(val address: Address?)

fun cityOf(user: User?): String {
    val c = user?.address?.city ?: return "none"
    return c.uppercase()
}

// (d) 루프 누적
class Item(val price: Int, val qty: Int)

fun total(items: List<Item>): Int =
    items.filter { it.qty > 0 }.sumOf { it.price * it.qty }

// (e) 싱글턴 · 정적 상태
object Registry {
    private var next = 0
    fun nextId(): Int = ++next
}

fun main() {
    for (s in intArrayOf(95, 90, 85, 80, 70)) {
        println("grade\t$s\t${grade(s)}")
    }
    println("fee\tCard(1000)\t${fee(Card(1000))}")
    println("fee\tCash(1000)\t${fee(Cash(1000))}")
    println("fee\tTransfer(1000)\t${fee(Transfer(1000))}")
    println("cityOf\tnull user\t${cityOf(null)}")
    println("cityOf\tnull address\t${cityOf(User(null))}")
    println("cityOf\tnull city\t${cityOf(User(Address(null)))}")
    println("cityOf\tseoul\t${cityOf(User(Address("seoul")))}")
    println("cityOf\tincheon\t${cityOf(User(Address("incheon")))}")
    println("total\t[]\t${total(listOf())}")
    println("total\t[(100,2) (50,0) (30,-1) (7,3)]\t" +
        total(listOf(Item(100, 2), Item(50, 0), Item(30, -1), Item(7, 3))))
    println("total\t[(2000000000,1) (2000000000,1)]\t" +
        total(listOf(Item(2000000000, 1), Item(2000000000, 1))))
    println("nextId\tx3\t${Registry.nextId()} ${Registry.nextId()} ${Registry.nextId()}")
}
```

```python
# pair57.py
import sys

def rows(path):
    out = []
    for n, line in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        cells = line.split("\t")
        if len(cells) != 3:
            sys.exit(f"{path}:{n}: expected 3 tab-separated cells, got {len(cells)}")
        out.append(cells)
    return out

java, kotlin = rows(sys.argv[1]), rows(sys.argv[2])
if len(java) != len(kotlin):
    sys.exit(f"row count differs: {len(java)} vs {len(kotlin)}")
print("case\tinput\tJava\tKotlin\tsame")
diff = 0
for (jc, ji, jr), (kc, ki, kr) in zip(java, kotlin):
    if (jc, ji) != (kc, ki):
        sys.exit(f"row key differs: {jc} {ji} vs {kc} {ki}")
    same = jr == kr
    diff += not same
    print(f"{jc}\t{ji}\t{jr}\t{kr}\t{str(same).lower()}")
print(f"cells that differ: {diff} / {len(java)}")
```

- 두 프로그램을 돌린 출력에 `diff` 를 걸면 무엇이 나오나? `pair57.py` 의 각 행 `same` 칸과 마지막 줄의 `N / M` 은?

### 2. ★★ JVM 에 `-Duser.language=tr -Duser.country=TR` 를 붙여 다시 돌리면 (예측)

```kotlin
// keep57.kt
import java.util.Locale

fun main() {
    val s = "incheon"
    println("uppercase()                    = ${s.uppercase()}")
    println("uppercase(Locale.getDefault()) = ${s.uppercase(Locale.getDefault())}")
}
```

- 1번의 두 프로그램을 이 플래그로 돌려 `pair57.py` 에 넣으면 마지막 줄은 무엇이고, `false` 인 행이 있다면 어느 것인가? 같은 플래그로 `keep57.kt` 를 돌리면 두 줄은 무엇인가?

### 3. ★★★ 하위 타입을 하나 더한 두 판 (예측)

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

- `kotlinc pay57v2.kt` 와 `javac PaySwitch57.java` 의 종료 코드는 각각 무엇이고, 진단이 있다면 무엇이라고 말하나?

### 4. ★★ 같은 추가, 다른 두 모양 (예측)

```java
// PayChain57.java
public class PayChain57 {
    interface Payment {}
    static final class Card implements Payment { final int amount; Card(int a) { amount = a; } }
    static final class Cash implements Payment { final int amount; Cash(int a) { amount = a; } }
    static final class Transfer implements Payment { final int amount; Transfer(int a) { amount = a; } }
    static final class Refund implements Payment { final int amount; Refund(int a) { amount = a; } }

    static int fee(Payment p) {
        if (p instanceof Card) {
            return ((Card) p).amount * 3 / 100;
        } else if (p instanceof Cash) {
            return 0;
        } else if (p instanceof Transfer) {
            return 500;
        } else {
            throw new IllegalStateException("unknown payment");
        }
    }

    public static void main(String[] args) {
        try {
            System.out.println("Refund(1000) -> " + fee(new Refund(1000)));
        } catch (RuntimeException e) {
            System.out.println("Refund(1000) -> threw " + e);
        }
    }
}
```

```kotlin
// pay57e.kt
sealed interface Payment
class Card(val amount: Int) : Payment
class Cash(val amount: Int) : Payment
class Transfer(val amount: Int) : Payment
class Refund(val amount: Int) : Payment

fun fee(p: Payment): Int = when (p) {
    is Card -> p.amount * 3 / 100
    is Cash -> 0
    else -> 500
}

fun main() {
    println("Refund(1000) -> ${fee(Refund(1000))}")
}
```

- 두 파일은 컴파일되나? 된다면 실행하면 각각 무엇이 찍히나?

### 5. ★★ 명령 줄 비교 (예측)

```java
// Tern57.java
public class Tern57 {
    static int pick(boolean b, int x, int y) {
        return b ? x : y;
    }

    static String grade(int score) {
        return score >= 90 ? "A" : score >= 80 ? "B" : "C";
    }
}
```

```kotlin
// tern57.kt
fun pick(b: Boolean, x: Int, y: Int): Int = if (b) x else y

fun grade(score: Int): String = if (score >= 90) "A" else if (score >= 80) "B" else "C"
```

```python
# ops57.py
import re, subprocess, sys

# 인자: <클래스경로>:<클래스>:<메서드> 두 개를 한 쌍으로, 여러 쌍.
OP = re.compile(r"^\s+\d+: (\w+)")

def opcodes(spec):
    cp, cls, method = spec.split(":")
    out = subprocess.run(["javap", "-c", "-p", "-cp", cp, cls],
                         capture_output=True, text=True, check=True).stdout
    ops, inside = [], False
    for line in out.splitlines():
        if re.match(r"^  \S.*\b" + re.escape(method) + r"\(", line):
            inside = True
            continue
        if inside:
            m = OP.match(line)
            if m:
                ops.append(m.group(1))
            elif line.strip() == "" or line.startswith("  ") and not line.startswith("    "):
                if ops:
                    break
    if not ops:
        sys.exit(f"no code found for {spec}")
    return ops

args = sys.argv[1:]
print("pair\tJava ops\tKotlin ops\tsame sequence")
same_n = 0
for j, k in zip(args[0::2], args[1::2]):
    a, b = opcodes(j), opcodes(k)
    same = a == b
    same_n += same
    name = j.split(":")[1] + "." + j.split(":")[2] + " / " + k.split(":")[1] + "." + k.split(":")[2]
    print(f"{name}\t{len(a)}\t{len(b)}\t{str(same).lower()}")
    if not same:
        print(f"  Java  : {' '.join(a)}")
        print(f"  Kotlin: {' '.join(b)}")
print(f"pairs with the same opcode sequence: {same_n} / {len(args) // 2}")
```

- 여섯 쌍(`Tern57`·`Tern57Kt` 의 `pick`·`grade` · 1번 두 프로그램의 `grade`·`fee`·`cityOf`·`total`)에서 `same sequence` 가 `true` 인 쌍은 어느 것인가? 마지막 줄의 `N / M` 은?

### 6. ★★ 같은 null 로직의 두 관용구 판 (예측)

```kotlin
// over57.kt
class Address(val city: String?)
class User(val address: Address?)

fun areaCode(city: String): String? = if (city == "seoul") "02" else null

fun early(u: User?): String {
    val city = u?.address?.city ?: return "no city"
    val code = areaCode(city) ?: return "no code for $city"
    return "$city:$code"
}

fun chain(u: User?): String =
    u?.let { user ->
        user.address?.let { addr ->
            addr.city?.let { city ->
                areaCode(city)?.let { code -> "$city:$code" }
            }
        }
    } ?: "no city"

fun main() {
    val inputs = listOf(
        "null user" to null,
        "null address" to User(null),
        "null city" to User(Address(null)),
        "seoul" to User(Address("seoul")),
        "busan" to User(Address("busan")),
    )
    println("input\tearly\tchain\tsame")
    var diff = 0
    for ((label, u) in inputs) {
        val a = early(u)
        val b = chain(u)
        if (a != b) diff++
        println("$label\t$a\t$b\t${a == b}")
    }
    println("cells that differ: $diff / ${inputs.size}")
}
```

- 다섯 입력 각각의 `early`·`chain`·`same` 은 무엇인가? 마지막 줄의 `N / M` 은?

### 7. Java 의 `s.toUpperCase()` 를 Kotlin 으로 글자 그대로 옮기면 (왜)

- 2.4.20 에서 그 줄은 어떻게 되고, 왜 그런가? 옮기는 사람이 그 결과로 고르게 되는 함수는 2번의 결과와 어떻게 이어지나?

### 8. `when` 에 `else ->` 한 줄이 하는 일 (왜)

- 4번의 `pay57e.kt` 가 3번의 `pay57v2.kt` 와 다르게 끝나는 이유는 무엇인가? Java 원본의 `else { throw … }` 와 견주면 어느 쪽이 더 조용한가?

### 9. 5번의 `fee` 쌍을 덤프로 펼치면 (왜)

- 두 판의 `fee` 덤프에서 마지막 가지 자리에는 각각 무엇이 있나? Kotlin 쪽의 그 명령이 실제로 도는 때는 언제인가?

### 10. 두 판 격자가 증명하는 범위 (경계)

- 1번의 결과는 「두 판이 같은 뜻이다」를 증명하나? 2번은 그 판단에 무엇을 보태나?

### 11. 「Kotlin 답게」가 과하다는 말의 근거 (경계)

- 6번에서 갈린 칸은 **관찰**인가 **판단**인가? 「`?.let` 을 겹겹이 쓰면 읽기 어렵다」는 어느 층의 말이고, 이 문서는 그 근거를 어디까지 확인했나?

### 12. Java 21 `switch` 와 견주면 (연결)

- 3번의 Java 판과 1번의 Java 원본은 무엇이 다른가? 「새 하위 타입을 컴파일러가 잡아 준다」는 Kotlin 만의 것인가 — [Java 23번](../../../java/syntax/23-switch-pattern-matching/)과 이어서 답하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
