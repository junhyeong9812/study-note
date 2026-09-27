# kotlin/syntax/57 — Java 코드를 Kotlin 답게 — 식으로서의 `if`/`when`·엘비스 조기 반환 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — 공식 문서 페이지는 **이 작업에서 열지 않았다**(외부 네트워크를 쓰지 않았다). 근거는 **이 판의 컴파일러 진단 · `javap` · stdlib 소스 jar**(`kotlin-stdlib-sources.jar` 2.4.20 의 `StringsJVM.kt`)뿐이다.\
> ★★ **「Kotlin 답게가 과하다」의 판단 근거로 삼으려던 [Coding conventions](https://kotlinlang.org/docs/coding-conventions.html) 는 받아 둔 사본이 이 머신에 없어 출처를 확인하지 못했다** — 그 자리의 문장은 전부 **이 문서의 권고**이고 규약 인용이 아니다((5)).
> **실행 검증** — 이 문서의 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `javac`·`java`·`javap` 에서 실제로 얻었다.\
> `kotlinc` 7회 · `javac` 4회 · `java` 9회(로케일 확인 1회 포함) · `javap` 5회 + 명령 비교 스크립트 안의 12회 · stdlib 소스 jar 발췌 1곳.\
> ★★ 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적지 않았다. **「갈린 칸 N / M」·「같은 명령 줄 N / M」은 스크립트가 스스로 센 것**이다.
> **버전** — `when` 의 봉인 완결성 검사가 **문에서도 오류**가 된 것은 1.7(정본 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/)) · `String.uppercase()` 는 stdlib 소스에 **`@SinceKotlin("1.5")`**, 옛 `toUpperCase()` 는 **`@DeprecatedSinceKotlin(warningSince = "1.5", errorSince = "2.1")`**((4) — 이 판에서 읽었다). Java 쪽 `switch` 패턴 매칭은 **Java 21**.
> **경계** — ★★★ 「**그래서 Kotlin 을 고를 것인가**」라는 논지(`when` 완결성이 유지보수 장치라는 것 · 컴파일러가 막는 것과 우리가 막아야 하는 것)는 [`../../언어-특성/README.md`](../../언어-특성/README.md) §3·§11 이 정본이다. 문법 하나하나의 정본은 형제 편이다 — `when` 이 식이라는 것과 그 바이트코드는 [06번 주제](../06-when-expression/), **변형을 하나 늘렸을 때 깨지는 자리 전수**는 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3), `?: return` 이 서는 이유(`Nothing`)는 [03번 주제](../03-null-safe-types/) (7)·[34번 주제](../34-exceptions-nothing-and-try-expression/) (3), `sumOf` 가 조용히 넘치는 것은 [44번 주제](../44-aggregation-grouping-fold-reduce/) (2), `object` 가 `INSTANCE` 정적 필드가 되는 것은 [25번 주제](../25-object-declaration-companion-and-object-expression/) (1), `?.let { } ?:` 의 함정은 [14번 주제](../14-scope-functions/) (4). **여기는 「같은 로직을 두 판으로 써서 같은가를 잰다」 하나만 한다.**\
> Java 쪽 — `switch` 식은 [Java 21번](../../../java/syntax/21-switch-statement-and-expression/), 패턴 `switch` 와 완결성은 [Java 23번](../../../java/syntax/23-switch-pattern-matching/), 봉인 클래스는 [Java 15번](../../../java/syntax/15-sealed-classes/), null 방어는 [Java 60번](../../../java/syntax/60-null-handling/)이 정본이다. null 을 **어느 계층에서** 막을지는 [58번 주제](../58-null-handling-idioms-let-requirenotnull-and-elvis-return/)다.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이다** — 「**같은 로직 두 판 격자 — 사례 다섯(분기 대입 · 봉인 다중 분기 · null 조기 반환 · 루프 누적 · 싱글턴) × 입력 17개 → Java 원본(`javac` 로 돌림)과 Kotlin 관용구 판의 출력이 같은가**」. 「Kotlin 답게」를 **맛이나 속도로 재지 않는다** — 재는 것은 **같은 입력에 같은 출력인가**와 **컴파일러가 무엇을 막아 주나**뿐이다.

## 이 주제가 쓰는 네 층

| 층 | 뜻 | 근거로 쓰는 것 |
|---|---|---|
| **언어 보장** | 컴파일러가 하는 것 | ★★★ 봉인 주체 `when` 의 가지 누락은 **컴파일 오류**(「`Add the 'is Refund' branch or an 'else' branch.`」) · `if`·`when` 은 **식**이라 값을 낸다 · `?:` 오른쪽의 `return` 은 `Nothing` |
| **API 계약(stdlib)** | KDoc·선언이 약속한 것 | `uppercase()` 「`using Unicode mapping rules of the invariant locale`」 · 옛 `toUpperCase()` 「`using the rules of the default locale`」·`errorSince = "2.1"` |
| **이 판의 관찰** | kotlinc 2.4.20 · javac 21 에서 이번에 본 것 | 두 판 출력 · `javap` 명령 줄 · `NoWhenBranchMatchedException` 을 컴파일러가 적어 넣는 것 |
| ★ **설계 권고** | **사람의 판단** — 컴파일러도 실행도 말하지 않는 것 | `?.let` 중첩·`also`/`apply` 남용이 「읽기 어렵다」 — ★ **규약 문서 출처를 확인하지 못했다**((5)) |

## 이 판

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== javac -version =====
javac 21.0.5
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | (이 주제에는 없다) | 실행 시간을 찍지 않았다 — 「관용구가 빠르다」는 **재지 않았다** |
| ★ **환경에 매인다** | 첫 격자의 결과 | JVM 기본 로케일이 **`ko`/`KR`** 인 머신에서 찍었다(블록 첫 줄). 기본 로케일이 `tr` 인 머신이면 둘째 격자처럼 갈린다((2)) |
| 안 흔들린다 | 두 판 격자 · 갈린 칸 수 · 과한 칸 격자 | 단일 스레드 · 고정 입력 |
| 안 흔들린다 | 진단 문구와 `줄:칸` · `javap` 의 명령과 상수 풀 번호 · 종료 코드 | 같은 컴파일러면 같다 |

★ 근거 — 캡처 스크립트를 처음부터 두 번 돌려 **블록 전체를 대조**했다(수치는 3-answer 의 「실행 검증」).

## 한눈에 — 쉽게 말하면

**Java 코드를 Kotlin 으로 옮기는 것은 「같은 요리를 다른 조리법으로 다시 적는 것」이다.** 조리법이 짧아졌는지는 보면 안다. 물어야 할 것은 **맛이 같은가**(같은 입력에 같은 출력)와 **새 조리법이 실수를 막아 주는가**(재료가 하나 늘면 조리법이 스스로 빈칸을 알리나)다.
★ 그리고 조리법을 옮기다 **「소금 약간」의 뜻이 바뀌는** 자리가 있다 — Java 의 `toUpperCase()` 는 **부엌(로케일)마다 다르게** 짜고, Kotlin 의 `uppercase()` 는 **어느 부엌에서나 같게** 짠다. 한국 부엌에서 맛보면 같고, 터키 부엌에서 맛보면 갈린다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 같은 요리 두 조리법 | `Legacy57.java` 와 `idiom57.kt` | (1) ★ |
| 맛이 같은가 | 같은 입력 17개에 출력 비교 — 갈린 칸 수 | (1) ★ |
| 부엌마다 뜻이 다른 「소금 약간」 | 기본 로케일을 쓰는 `toUpperCase()` 대 `Locale.ROOT` 의 `uppercase()` | (2)(4) ★ |
| 재료가 늘면 빈칸을 알린다 | 봉인 `when` 은 새 하위 타입에서 **컴파일 오류** | (3) ★ |
| 빈칸을 「기타」로 덮는다 | `else ->` 한 줄 · Java 의 `else throw` | (3) |
| 부엌 도구는 같다 | `if` 식과 Java 삼항 연산자의 **바이트코드가 같다** | (4) |
| 조리법을 너무 줄여 뜻을 잃는다 | `?.let` 중첩이 **실패 이유 둘을 하나로** 뭉갠다 | (5) |

```text
   Java 원본 (Legacy57.java)            Kotlin 관용구 (idiom57.kt)
   ─────────────────────────            ──────────────────────────
   String g; if … g = "A"; …           val g = if (…) "A" else …
   if (p instanceof Card) … else throw  when (p) { is Card -> … }   ← else 없음
   if (u == null) return …; ×3          u?.address?.city ?: return …
   for (i : items) { sum += … }         items.filter { … }.sumOf { … }
   static int next; static nextId()     object Registry { … }
            │                                     │
            └──────── 같은 입력 17개 ──────────────┘
                              │
                     출력을 한 칸씩 대조 → 갈린 칸 N / 17
```

## 이 주제가 답하려는 질문

1. Java 원본과 Kotlin 관용구 판은 **같은 입력에 같은 출력**을 내나 — 그리고 「같다」가 깨지는 자리는 어디인가.
2. 관용구가 **컴파일러에게 무엇을 더 맡기나** — 하위 타입이 하나 늘 때 두 판은 각각 어떻게 반응하나.
3. `if` 식·`when` 식은 **바이트코드로도 같은가** — 그리고 「Kotlin 답게」가 **과해지는** 자리는 어디인가.

## 동작 방식

### (0) ★★★ 이 주제가 쓰는 창 — 그리고 「부적용인 창」

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **두 판 격자(실행 · 결정적)** | 사례 다섯 × 입력 17 → Java 출력 · Kotlin 출력 · 같은가((1)) | ★ **본체 창** |
| ★★ **로케일 판 격자** | 같은 두 판을 `-Duser.language=tr` 로 다시((2)) | 본체 창을 **환경만 바꿔** 다시 연 것 |
| ★★ **컴파일러 진단** | 하위 타입 하나를 늘린 네 판 — `kotlinc` · `javac` 의 오류와 종료 코드((3)) | [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3)이 전수를 쟀다 — 여기는 **Java 원본과의 한 쌍**만 |
| ★★ **`javap -c` 명령 비교** | 여섯 쌍의 명령 줄이 같은가 — **관찰층**((4)) | 바이트코드의 정본은 [06번 주제](../06-when-expression/) (3)\~(6) |
| ★ **stdlib 소스 jar 발췌** | `uppercase()` 와 `toUpperCase()` 의 선언((4)) | — |
| ★ **과한 칸 격자** | 같은 null 로직의 두 관용구 판 — 조기 반환 대 `?.let` 사슬((5)) | [14번 주제](../14-scope-functions/) (4)의 함정을 **실패 이유**로 다시 본 것 |
| **인용 — 다시 안 잰다** | `sumOf` 넘침 · `object` 의 `INSTANCE` · `?:` 의 `Nothing` · 변형 추가 시 깨지는 자리 전수 | [44번 주제](../44-aggregation-grouping-fold-reduce/) (2) · [25번 주제](../25-object-declaration-companion-and-object-expression/) (1) · [34번 주제](../34-exceptions-nothing-and-try-expression/) (3) · [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3) |
| ★ **제5의 상태 — 창을 바꿔 물었다** | 「두 판이 **같은 뜻**인가」는 증명할 창이 없다 — **같은 입력에 같은 출력**(실행)과 **같은 명령 줄**(바이트코드)로 나눠 물었다 | (1)(4) — ★ 이 두 창은 **안 넣어 본 입력과 안 바꿔 본 환경**을 못 본다. 로케일 차이는 첫 격자에서 **0 칸**이었다((2)) |
| ★ **제3의 상태 — 못 잰 것** | 「과하다」의 규약 근거 — 코딩 규약 문서 | **사본이 없고 네트워크를 쓰지 않았다** — 출처 확인 못 함((5)) |
| **부적용 — 실행 시간** | ★★★ 「Kotlin 관용구가 빠르다/느리다」는 **재지 않았다** — (4)의 명령 수는 **속도가 아니다** | — |

### (1) ★★★ 두 판 격자 — 같은 입력에 같은 출력인가

**언제 쓰나** — Java 코드를 Kotlin 으로 옮긴 뒤 「뜻이 바뀌지 않았다」를 보이고 싶을 때.

방법 — 사례 다섯을 Java 원본과 Kotlin 관용구 판으로 **각각 한 프로그램**에 담고, 같은 입력을 같은 순서로 넣어 `사례 · 입력 · 결과` 세 칸(탭 구분)을 찍는다. `pair57.py` 가 두 출력을 **행마다 칸 수를 검사하며** 맞대어 마지막 줄에 갈린 칸 수를 센다. 그 앞의 `diff` 는 두 파일이 **한 바이트도 다르지 않은지**를 따로 본다.

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

- ★★★ **갈린 칸 0 / 17 · `diff` 는 출력 0줄에 `(exit 0)`** — 다섯 사례 모두 두 판이 같은 글자를 냈다. 경계 입력(`90`·`80`) · null 세 갈래 · 빈 리스트 · 음수 수량까지 같다.
- ★★★ **넘치는 합도 같다** — `2000000000 × 2` 가 두 판 모두 **`-294967296`**. Kotlin 의 `sumOf { it.price * it.qty }` 는 람다가 `Int` 를 내므로 **`Int` 판 `sumOf`** 가 골라지고, Java 의 `int sum` 과 똑같이 조용히 넘친다([44번 주제](../44-aggregation-grouping-fold-reduce/) (2)). **관용구로 옮긴다고 넘침이 막히지 않는다.**
- ★★ **`when` 에 `else` 가 없는데 컴파일됐다** — `Payment` 가 `sealed` 이고 세 하위 타입을 다 적었기 때문이다. Java 원본은 `else { throw … }` 를 **사람이** 적었다. 이 차이가 (3)의 본론이다.
- ★★ **null 조기 반환 세 개가 한 줄이 됐다** — `user?.address?.city ?: return "none"`. `?.` 사슬 어디서 끊겨도 `?:` 로 떨어지고, 오른쪽 `return` 의 타입이 `Nothing` 이라 `c` 는 `String` 이 된다([03번 주제](../03-null-safe-types/) (7)).
- ★ 싱글턴 — Java 의 `private` 생성자 + `static` 필드와 Kotlin `object` 가 같은 `1 2 3` 을 냈다. `object` 가 JVM 에서 무엇이 되는지는 [25번 주제](../25-object-declaration-companion-and-object-expression/) (1)이 정본이다.
- ★ **이 0 은 「이 17개 입력에서」의 0 이다** — 두 판이 **모든 입력에서** 같다는 증명이 아니다. 바로 다음 절이 그 틈을 보여 준다.

### (2) ★★ 환경을 바꾸면 — 로케일 판 격자

같은 두 프로그램을 **JVM 기본 로케일만 터키어로** 바꿔 다시 돌린다. 소스는 한 글자도 안 바꿨다. 끝의 `keep57.kt` 는 Kotlin 쪽에서 로케일을 **명시한** 판이다.

```kotlin
// keep57.kt
import java.util.Locale

fun main() {
    val s = "incheon"
    println("uppercase()                    = ${s.uppercase()}")
    println("uppercase(Locale.getDefault()) = ${s.uppercase(Locale.getDefault())}")
}
```

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

- ★★★ **갈린 칸 1 / 17 — `incheon` 한 칸** — Java 는 **`İNCHEON`**(점 있는 대문자 I), Kotlin 은 **`INCHEON`**. `seoul` 은 `i` 가 없어 두 판이 같다.
- ★★★ **원인은 두 함수가 이름만 비슷하고 계약이 다른 것**이다 — Java `String.toUpperCase()` 는 **기본 로케일**을 쓰고, Kotlin `uppercase()` 는 **`Locale.ROOT`** 를 쓴다((4)의 발췌와 `javap`). 그래서 첫 격자(기본 로케일 `ko`)에서는 **0 칸**이었다 — **입력을 늘려서는 못 찾고 환경을 바꿔야 드러난다.**
- ★★ **이번엔 Kotlin 쪽이 「뜻을 바꾼」 쪽이다** — 옮긴 사람이 `toUpperCase()` 를 `uppercase()` 로 바꾼 순간 **로케일 의존이 사라졌다.** 대개는 버그 수정이지만, 원본의 동작을 **그대로** 옮기는 것이 목표라면 `uppercase(Locale.getDefault())` 라야 같다 — `keep57.kt` 가 `tr` 에서 **`İNCHEON`** 을 내 Java 와 같아졌다(이 식은 `toUpperCase()` 의 `@Deprecated` 가 적어 둔 대체 식이다 — (4)).

### (3) ★★★ 하위 타입을 하나 늘리면 — 컴파일러가 막는 자리

(1)의 두 판에 **`Refund`** 하위 타입 하나를 더한 네 판이다. 분기 코드는 **한 글자도 안 바꿨다.**

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

- ★★★ **Kotlin 봉인 `when` 은 오류 · 종료 코드 1** — 「`'when' expression must be exhaustive. Add the 'is Refund' branch or an 'else' branch.`」 **빠진 하위 타입의 이름을 대 준다.** 분기하는 자리가 몇 군데든 **전부 동시에** 깨진다 — 그 전수는 [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3)이 셌다.
- ★★ **Java 21 의 봉인 인터페이스 + 패턴 `switch` 도 오류다** — 「`the switch expression does not cover all possible input values`」. 이 보호는 **Kotlin 만의 것이 아니다** — Java 21 로 **현대식으로** 쓴 판도 같은 자리에서 막힌다(Java 쪽 정본은 [Java 23번](../../../java/syntax/23-switch-pattern-matching/)). ★ 차이는 문구다 — `javac` 는 **빠진 타입 이름을 말하지 않는다.**

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

- ★★★ **Java 원본 모양(`instanceof` 사슬 + `else throw`)은 컴파일이 통과하고(`exit 0`) 실행에서 `IllegalStateException: unknown payment`** 이다. 새 하위 타입은 **운영에서 처음 들어온 날** 드러난다.
- ★★★ **Kotlin 도 `else ->` 한 줄이면 조용히 통과한다** — `Refund(1000) -> 500`. **예외조차 없이 틀린 값**이 나온다 — Java `else throw` 보다 더 조용하다. `else` 가 완결성 검사를 **그 자리에서 꺼 버린 것**이다([`../../언어-특성/README.md`](../../언어-특성/README.md) §3 의 「`A match-all clause risks sweeping exhaustiveness errors under the rug`」).
- ★★ 그래서 「Kotlin 답게」의 알맹이는 **`when` 을 쓰는 것이 아니라 `else` 를 안 쓰는 것**이다 — 봉인 계층 위의 `when` 에서 `else` 를 지우면 컴파일러가 전이표를 대신 지킨다.

```text
   하위 타입 하나 추가            컴파일            실행
   ─────────────────────        ────────        ─────────────────────
   Kotlin when (else 없음)       ✗ exit 1         —
   Java 21 switch (default 없음) ✗ exit 1         —
   Java instanceof 사슬 + throw  ✓ exit 0         예외 (운영에서 발견)
   Kotlin when + else ->         ✓ exit 0         틀린 값, 예외 없음 ★
```

### (4) ★★ 바이트코드는 같은가 — `javap` 명령 비교 (관찰층)

**언제 쓰나** — 「`if` 식은 Java 삼항 연산자와 같은 것인가」·「Kotlin 판이 더 무거운가」를 말하기 전에.

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

- ★★★ **Java 삼항과 Kotlin `if` 식은 명령 줄이 같다 — 두 쌍 모두** (`pick` 6개 · `grade` 12개). `if` 식은 **Java 의 `?:` 연산자에 해당하는 것**이다.
- ★★★ **Java 의 `if` 문 대입(`Legacy57.grade`)과는 다르다** — Java 판에는 **`astore_1`/`aload_1`**(지역 변수 `g` 에 넣었다 꺼내기)이 끼어 16개, Kotlin 은 12개. 뜻은 같고 **값을 담는 자리가 없을 뿐**이다(JIT 뒤의 차이는 재지 않았다).
- ★★ **`fee` 는 모양이 거의 같다** — 둘 다 `instanceof` 사슬이다. Kotlin 은 앞에 **인자 null 검사**(`checkNotNullParameter` — [03번 주제](../03-null-safe-types/) (4))가, 끝에 **`NoWhenBranchMatchedException` 던지기**가 붙는다(아래 덤프).
- ★★ **`cityOf` 는 Kotlin 이 `getstatic Locale.ROOT` 를 넣는다** — (2)의 원인이 바이트코드에 박혀 있다(아래 덤프).
- ★★ **`total` 은 26 대 79** — `filter`·`sumOf` 가 `inline` 이라 본문에 풀리고, `filter` 가 **중간 `ArrayList` 를 하나 만든다**(`new`). Java 루프에는 리스트가 없다. 중간 컬렉션의 정본은 [47번 주제](../47-sequences-lazy-evaluation/) (3). ★ **명령 수는 속도가 아니다** — 이 문서는 시간을 재지 않았다.
- ★ 셈 — **같은 명령 줄 2 / 6**. 같은 두 쌍은 **삼항 대 `if` 식**뿐이다.

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

- ★★★ **Kotlin 컴파일러가 `else` 가지를 스스로 적었다** — 오프셋 `54`\~`61` 의 `new kotlin/NoWhenBranchMatchedException` · `athrow`. Java 원본에서 사람이 쓴 `new IllegalStateException` · `athrow`(오프셋 `40`\~`49`)와 **같은 자리, 같은 모양**이다.
- ★★ 그 가지가 도는 때는 **컴파일할 때 몰랐던 하위 타입이 런타임에 들어올 때**뿐이다(분리 컴파일 — [06번 주제](../06-when-expression/) (7)). 같은 모듈에서 다시 컴파일하면 (3)처럼 **그 전에 오류**가 난다.

```kotlin
// upper57.kt
fun shout(s: String): String = s.toUpperCase()

fun main() {
    println(shout("incheon"))
}
```

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

- ★★★ **Java 코드를 글자 그대로 옮긴 `s.toUpperCase()` 는 2.4.20 에서 컴파일 오류**다 — 「`'fun String.toUpperCase(): String' is deprecated. Use uppercase() instead.`」 선언의 **`errorSince = "2.1"`** 이 그것이다. 옮기는 사람은 **`uppercase()` 로 바꿀 수밖에 없고**, 그 순간 (2)의 로케일 차이가 생긴다.
- ★★ **KDoc 이 두 계약을 글자로 가른다** — `toUpperCase()` 「`using the rules of the default locale`」 · `uppercase()` 「`using Unicode mapping rules of the invariant locale`」. 원래 동작을 지키는 대체 식은 `@Deprecated` 의 `ReplaceWith("uppercase(Locale.getDefault())", …)` 가 적어 둔 그것이다.

### (5) ★ 「Kotlin 답게」가 과한 자리 — 관찰과 판단을 가른다

같은 null 로직을 **조기 반환 판**(`early`)과 **`?.let` 사슬 판**(`chain`)으로 쓴다. 뒤쪽은 「`if` 를 하나도 안 쓴다」는 뜻에서 더 「Kotlin 답게」 보인다.

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

- ★★★ **관찰층 — 갈린 칸 1 / 5 · `busan` 한 칸** — 도시는 있는데 지역 번호가 없는 입력에서 `early` 는 **`no code for busan`**, `chain` 은 **`no city`**. 사슬 끝의 `?: "no city"` 가 **네 군데의 null 을 한 통로로** 받기 때문에 **실패 이유 둘이 하나로 뭉개졌다.** 이것은 판단이 아니라 **출력**이다([14번 주제](../14-scope-functions/) (4)가 같은 함정을 `?.let { } ?:` 한 겹으로 보였다).
- ★★ **설계 권고층 — 「읽기 어렵다」는 이 문서의 판단**이다 — `?.let` 을 네 겹 겹치면 **어느 null 에서 끊겼는지** 코드만 보고 따라가기 어렵고, `also`/`apply` 를 사슬로 이으면 `it`/`this` 가 **겹마다 바뀐다**(가림은 [14번 주제](../14-scope-functions/) (5)). ★ **이 판단을 받쳐 줄 코딩 규약 문장은 출처를 확인하지 못했다** — 규약이 그렇게 말한다고 적지 않는다.
- ★ 권고 한 줄 — **실패 이유가 둘 이상이면 조기 반환(`?: return`)을 이유마다 한 줄씩** 둔다. `?.let` 사슬은 **실패 이유가 하나이고 결과가 null 이어도 되는** 자리에 쓴다.

## 문법 — 형태와 규칙

**형태** — 다섯 사례의 Kotlin 쪽 모양은 (1)의 `idiom57.kt` 가 그대로 형태 한 벌이다(실제로 컴파일되고 돌았다).

**Java 에서 옮길 때의 대응**

| Java 원본 | Kotlin 관용구 | 조심할 것 |
|---|---|---|
| `T x; if (c) x = a; else x = b;` · `c ? a : b` | `val x = if (c) a else b` | `if` 식은 **삼항과 같은 바이트코드**((4)) |
| `instanceof` 사슬 + `else throw` · `switch` + `default` | 봉인 계층 + **`else` 없는** `when` 식 | ★ `else ->` 를 적으면 검사가 꺼진다((3)) |
| `if (x == null) return …;` 여러 번 | `val v = a?.b?.c ?: return …` | 실패 이유가 여럿이면 **이유마다 한 줄**((5)) |
| `for` + 누적 변수 | `sumOf { }` · `fold(초깃값) { }` | `Int` 판은 **똑같이 넘친다**((1)) |
| `private` 생성자 + `static` 상태 | `object` | [25번 주제](../25-object-declaration-companion-and-object-expression/) |
| `s.toUpperCase()` | `s.uppercase()` — ★ **뜻이 바뀐다** | 원래 동작은 `uppercase(Locale.getDefault())`((2)(4)) |

**규칙 불릿**

- **`if`·`when` 은 식이다** — 값을 담을 변수를 먼저 선언하지 않는다((1)(4)).
- **봉인 계층 위 `when` 에는 `else` 를 쓰지 않는다** — 하위 타입이 늘면 컴파일러가 알린다((3)).
- **`?: return`·`?: throw` 는 `Nothing` 덕분에 선다** — 왼쪽의 null 가능성이 벗겨진다([34번 주제](../34-exceptions-nothing-and-try-expression/) (3)).
- **옮긴 뒤에는 같은 입력으로 두 판을 대조한다** — 그리고 **환경(로케일·시간대)도 한 번 바꿔 본다**((2)).

## 어디서 틀리나

1. ★★★ **「Kotlin 으로 옮겼으니 봉인 분기가 안전하다」** — `else ->` 를 한 줄 적으면 Java `else throw` 보다 **더 조용하다**(예외 없이 틀린 값)((3)).
2. ★★★ **`toUpperCase()` → `uppercase()` 를 이름 바꾸기로 본다.** 로케일 의존이 사라진다 — 기본 로케일이 `tr` 이면 출력이 갈린다((2)(4)).
3. ★★ **「같은 입력에 같은 출력」을 「같은 뜻」으로 읽는다.** 0 / 17 은 **그 입력·그 환경에서**의 0 이다((1)(2)).
4. ★★ **`sumOf` 가 넘침을 막아 준다고 본다.** 람다가 `Int` 면 `Int` 로 넘친다((1) · [44번 주제](../44-aggregation-grouping-fold-reduce/) (2)).
5. ★★ **`?.let` 사슬 + `?:` 하나로 null 을 다 처리한다.** 실패 이유가 뭉개진다((5)).
6. ★ **Kotlin `if` 식을 Java `if` 문의 다른 표기로 본다.** 바이트코드로는 **삼항 연산자**다((4)).
7. ★ **명령 수로 속도를 말한다.** `total` 의 26 대 79 는 **중간 리스트가 있다**는 뜻이지 몇 배 느리다는 뜻이 아니다((4)).

## 구현 세부사항 대 언어 보장

| 항목 | 어느 쪽인가 | 근거 |
|---|---|---|
| 봉인 주체 `when` 의 가지 누락이 오류 | ★★★ **언어 보장**(컴파일러 진단) | (3) |
| `if`·`when` 이 식이다 · `?:` 오른쪽 `return` 이 `Nothing` | ★★★ **언어 보장** | (1) · [34번 주제](../34-exceptions-nothing-and-try-expression/) |
| Java 패턴 `switch` 의 완결성 오류 | **Java 언어 보장**(javac 21 진단) | (3) |
| `uppercase()` 가 `Locale.ROOT` · `toUpperCase()` 가 기본 로케일 | ★★ **API 계약(KDoc)** — `Locale.ROOT` 는 구현 줄이기도 하다 | (4) |
| `toUpperCase()` 가 오류 | ★ **stdlib 선언(`errorSince = "2.1"`)을 컴파일러가 집행** — 언어 문법이 아니라 **라이브러리의 폐기 일정** | (4) |
| `if` 식과 삼항의 명령 줄이 같다 · `NoWhenBranchMatchedException` 을 적어 넣는다 | **이 판의 관찰**(kotlinc 2.4.20 · javac 21) | (4) |
| 두 판 출력이 같다(0 / 17) | **관찰 — 입력 17개 · 로케일 `ko`** | (1)(2) |
| 「`?.let` 사슬·`also`/`apply` 남용은 읽기 어렵다」 | ★ **설계 권고** — 규약 출처 확인 못 함 | (5) |
| 「관용구가 빠르다」 | **재지 않았다** | — |

★★ **가장 조심할 자리** — 「`toUpperCase()` 는 오류」는 **언어가 아니라 stdlib 의 폐기 표지**다. 판이 오르면 이런 표지가 늘거나 바뀐다 — 옮긴 코드가 **다음 판에서 조용히 뜻이 바뀌는 것이 아니라 컴파일이 깨진다**는 점에서는 친절한 쪽이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 변수에 분기 결과를 담는다 | `val x = if (…) … else …` | (1)(4) — 삼항과 같다 |
| 닫힌 상태 집합으로 분기한다 | 봉인 계층 + `else` 없는 `when` | (3) — 새 상태가 컴파일 오류가 된다 |
| 상태가 문자열·코드 값이다 | 먼저 **봉인 계층이나 `enum` 으로 바꾼다** | 주체가 무한 타입이면 검사 대상이 아니다([`../../언어-특성/README.md`](../../언어-특성/README.md) §3) |
| null 이면 끝낸다 · 이유가 하나 | `?: return` 한 줄 | (1) |
| null 이면 끝낸다 · 이유가 여럿 | 이유마다 `?: return "…"` | (5) |
| 원본과 **바이트 단위로** 같은 동작이 필요하다(문자열 변환) | 로케일을 **명시**한다(`uppercase(Locale.getDefault())` 등) | (2)(4) |
| 누적이 넘칠 수 있다 | `sumOf { it.toLong() }` 등으로 타입을 넓힌다 | (1) · [44번 주제](../44-aggregation-grouping-fold-reduce/) (2) |

## 핵심 문장

1. Java 원본과 Kotlin 관용구 판은 **입력 17개에서 갈린 칸 0 / 17** 이었다 — 그러나 **기본 로케일을 `tr` 로 바꾸자 1 / 17** 이 됐다(`toUpperCase` 대 `uppercase`).
2. 하위 타입이 하나 늘면 **Kotlin `when`(else 없음)과 Java 21 패턴 `switch` 는 컴파일 오류**, **Java `instanceof` 사슬은 실행에서 예외**, **Kotlin `when` + `else` 는 예외 없이 틀린 값**이다.
3. **`if` 식은 바이트코드로 Java 삼항 연산자와 같다** — Java `if` 문 대입과는 지역 변수 한 칸이 다르다.
4. Kotlin 컴파일러는 `else` 없는 봉인 `when` 끝에 **`NoWhenBranchMatchedException` 던지기를 스스로 적는다** — Java 원본에서 사람이 쓴 `else throw` 의 자리다.
5. **`?.let` 사슬은 실패 이유를 뭉갠다**(관찰) — 「읽기 어렵다」는 **판단**이고, 이 문서는 그 판단의 규약 출처를 확인하지 못했다.

## 관련 자료

- [06번 주제](../06-when-expression/) — ★★★ **선행.** `when` 이 식이라는 것 · 주체 타입이 완결성을 정한다 · 주체별 바이트코드 · 분리 컴파일에서 깨지는 완결성((7)). 그쪽은 **`when` 자체**, 여기는 **Java 원본과의 한 쌍**.
- [34번 주제](../34-exceptions-nothing-and-try-expression/) — ★★ **선행.** `Nothing` 이 `?: return` 을 세운다 · `try` 도 식이다.
- [23번 주제](../23-sealed-classes-and-when-exhaustiveness/) (3) — 변형 하나를 늘렸을 때 깨지는 자리 **전수**. 여기는 그 한 자리를 Java 모양 셋과 견준다.
- [03번 주제](../03-null-safe-types/) (7) · [14번 주제](../14-scope-functions/) (4)(5) · [44번 주제](../44-aggregation-grouping-fold-reduce/) (2) · [25번 주제](../25-object-declaration-companion-and-object-expression/) (1) · [47번 주제](../47-sequences-lazy-evaluation/) (3) — 사례마다의 정본.
- [Java 21번](../../../java/syntax/21-switch-statement-and-expression/) · [Java 23번](../../../java/syntax/23-switch-pattern-matching/) · [Java 15번](../../../java/syntax/15-sealed-classes/) — Java 쪽의 식 `switch` · 패턴 완결성 · 봉인. **Java 21 로 쓰면 (3)의 보호는 Java 에도 있다.**
- [Java 60번](../../../java/syntax/60-null-handling/) — Java 의 null 방어 관용구. null 을 **어느 계층에서** 막을지는 [58번 주제](../58-null-handling-idioms-let-requirenotnull-and-elvis-return/).
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3·§11 — 「`when` 완결성이 유지보수 장치다」·「컴파일러가 막는 것과 우리가 막아야 하는 것」의 **논지**. 그쪽은 **왜 고르나**, 여기는 **옮긴 코드가 같은가**.

## 용어 풀이

> **관용구(idiom)** — 그 언어 사용자들이 같은 일을 할 때 흔히 쓰는 모양. 문법이 허락하는 여러 모양 중 **습관으로 굳은 하나**.\
> 예: Kotlin 에서 null 이면 끝낼 때 `?: return`.

> **식(expression) / 문(statement)** — 값을 내는 것 / 값 없이 일만 하는 것. Kotlin 의 `if`·`when`·`try` 는 식이다.

> **삼항 연산자** — Java 의 `c ? a : b`. 조건에 따라 둘 중 하나의 **값**을 낸다.

> **봉인(sealed) 계층** — 하위 타입 목록이 컴파일 시점에 닫힌 타입. 그래서 `when` 이 「다 덮었나」를 셀 수 있다.

> **완결성(exhaustiveness)** — 분기가 가능한 경우를 **전부** 덮었는가.

> **로케일(locale)** — 언어·지역 설정. 대소문자 변환·숫자 형식이 여기에 따라 달라진다. `Locale.ROOT` 는 **어느 지역에도 묶이지 않은** 기준 로케일.

> **`NoWhenBranchMatchedException`** — 완결한 `when` 이 런타임에 어느 가지에도 안 맞을 때 Kotlin 이 던지는 예외. 컴파일러가 적어 넣는다.

> **조기 반환(early return)** — 조건이 안 맞으면 함수 앞머리에서 바로 돌아가는 모양. 본문의 들여쓰기가 깊어지지 않는다.

## 더 들어가면

- **시간대·숫자 형식** — 로케일처럼 **환경에 매인 API**(`String.format`·`DateTimeFormatter`)도 옮길 때 같은 틈이 있을 것으로 보이지만 **재지 않았다.**
- **`toLowerCase` → `lowercase`** — 같은 폐기 쌍으로 보이지만 **이 판에서 발췌하지 않았다.**
- **`-jvm-target` 을 바꾸면** — 봉인 `when` 이 전혀 다른 코드가 되는 것은 [06번 주제](../06-when-expression/) (6)이 쟀다. (4)의 명령 비교는 기본 대상에서만 찍었다.
- **JIT 뒤의 차이** — (4)의 명령 줄 차이가 기계어에서도 남는지는 재지 않았다.
