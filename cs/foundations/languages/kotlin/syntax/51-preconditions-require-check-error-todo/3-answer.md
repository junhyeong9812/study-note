# kotlin/syntax/51 — 계약 함수 — `require`/`check`/`error`/`TODO` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·에러·바이트코드는 **kotlinc 2.4.20 (JRE 21.0.5)** 과 Temurin **JDK 21.0.5** 의 `java`·`javap` 에서 실제로 얻었다.
> ★★ 아래 블록은 전부 **캡처 스크립트가 파일로 받아** 조립한 것이다 — 사람이 옮겨 적은 자리가 없다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`require` 계열 → `IllegalArgumentException` · `check` 계열·`error` → `IllegalStateException` · `TODO` → `kotlin.NotImplementedError`** · 갈린 행 **2 / 11**(`assert` 둘 — `java` 에서는 아무것도 안 던진다)

**출력**

```text
===== kotlinc throw51.kt -d o51t =====
(exit 0)
```

```text
===== python3 grid51.py =====
thrower	java: class	java: message	java -ea: class	java -ea: message
require(false)	java.lang.IllegalArgumentException	Failed requirement.	java.lang.IllegalArgumentException	Failed requirement.
require(false) { "m" }	java.lang.IllegalArgumentException	m	java.lang.IllegalArgumentException	m
requireNotNull(none)	java.lang.IllegalArgumentException	Required value was null.	java.lang.IllegalArgumentException	Required value was null.
check(false)	java.lang.IllegalStateException	Check failed.	java.lang.IllegalStateException	Check failed.
check(false) { "m" }	java.lang.IllegalStateException	m	java.lang.IllegalStateException	m
checkNotNull(none)	java.lang.IllegalStateException	Required value was null.	java.lang.IllegalStateException	Required value was null.
error("m")	java.lang.IllegalStateException	m	java.lang.IllegalStateException	m
TODO()	kotlin.NotImplementedError	An operation is not implemented.	kotlin.NotImplementedError	An operation is not implemented.
TODO("m")	kotlin.NotImplementedError	An operation is not implemented: m	kotlin.NotImplementedError	An operation is not implemented: m
assert(false)	(nothing thrown)	-	java.lang.AssertionError	Assertion failed
assert(false) { "m" }	(nothing thrown)	-	java.lang.AssertionError	m
classes under java -ea: AssertionError 2 · IllegalArgumentException 3 · IllegalStateException 4 · NotImplementedError 2
rows that differ between java and java -ea: 2 / 11
(exit 0)
```

**왜 그런가**

- ★★★ 클래스는 KDoc 이 약속한 것이다(2-summary (5)) — `require` 「`Throws an [IllegalArgumentException]`」.
- ★★ 기본 메시지는 stdlib 의 상수다 — `Failed requirement.` · `Check failed.` · `Required value was null.` · `An operation is not implemented.` · `Assertion failed`.
- ★★ `assert` 만 `-ea` 에 매인다 — `_Assertions.ENABLED`.

### 2. ★★ `legacy` 는 **안 던지는데 조건은 평가**(`java`) · `jvm` 은 `-ea` 가 없으면 **평가도 안 한다** · `always-enable` 은 늘 던지고 · `always-disable` 은 늘 조용 — **던진 칸 4 / 8 · 평가한 칸 5 / 8**

**출력**

```text
===== python3 grid51a.py =====
-Xassertions	java	java -ea
legacy	nothing thrown	condition evaluated 1	AssertionError	condition evaluated 1
jvm	nothing thrown	condition evaluated 0	AssertionError	condition evaluated 1
always-enable	AssertionError	condition evaluated 1	AssertionError	condition evaluated 1
always-disable	nothing thrown	condition evaluated 0	nothing thrown	condition evaluated 0
cells that threw: 4 / 8
cells that evaluated the condition: 5 / 8
(exit 0)
```

**왜 그런가**

- ★★★ 기본 모드에서 `assert` 는 **보통의 `inline fun`** 이라 인자 `condition()` 이 **부르기 전에** 계산된다 — 선언이 `assert(value: Boolean, …)` 이고 `_Assertions.ENABLED` 는 **몸통 안에서** 본다(2-summary (5)).
- ★★ `-Xassertions=jvm` 은 Java 의 `assert` 문처럼 **조건 계산 자체를 건너뛰는** 꼴로 컴파일한다 — 그 바이트코드는 **보지 않았다**(행동만 봤다).

### 3. ★★★ **막힌 탐침 3 / 9** — `contract-without-opt-in`(3건 · `this declaration needs opt-in …`) · `assert` · `own-no-contract`(둘 다 `only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.`) · 나머지 여섯은 `ok`

**출력**

```kotlin
// contract51.kt
import kotlin.contracts.ExperimentalContracts
import kotlin.contracts.contract

fun ownCheck(ok: Boolean) {
    if (!ok) throw IllegalArgumentException("ownCheck")
}

@OptIn(ExperimentalContracts::class)
fun ownCheckC(ok: Boolean) {
    contract { returns() implies ok }
    if (!ok) throw IllegalArgumentException("ownCheckC")
}

fun ownCheckNoOptIn(ok: Boolean) {
    contract { returns() implies ok }                                        // contract-without-opt-in
    if (!ok) throw IllegalArgumentException("ownCheckNoOptIn")
}

fun p1(s: String?): Int { require(s != null); return s.length }             // require
fun p2(s: String?): Int { check(s != null); return s.length }               // check
fun p3(s: String?): Int { requireNotNull(s); return s.length }              // requireNotNull
fun p4(s: String?): Int { assert(s != null); return s.length }              // assert
fun p5(s: String?): Int { if (s == null) error("none"); return s.length }   // if-error
fun p6(s: String?): Int { ownCheck(s != null); return s.length }            // own-no-contract
fun p7(s: String?): Int { ownCheckC(s != null); return s.length }           // own-with-contract
fun p8(s: String?): Int { val t = s ?: TODO(); return t.length }            // elvis-TODO
```


```text
===== python3 grid51c.py =====
probe	compile
contract-without-opt-in	3 error(s), first: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
require	ok
check	ok
requireNotNull	ok
assert	1 error(s), first: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
if-error	ok
own-no-contract	1 error(s), first: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
own-with-contract	ok
elvis-TODO	ok
exit 1
blocked probes: 3 / 9
(exit 0)
===== kotlinc contract51.kt -d o51c2 =====
contract51.kt:15:5: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
    ^^^^^^^^
contract51.kt:15:16: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
               ^^^^^^^
contract51.kt:15:26: error: this declaration needs opt-in. Its usage must be marked with '@kotlin.contracts.ExperimentalContracts' or '@OptIn(kotlin.contracts.ExperimentalContracts::class)'
    contract { returns() implies ok }                                        // contract-without-opt-in
                         ^^^^^^^
contract51.kt:22:54: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun p4(s: String?): Int { assert(s != null); return s.length }              // assert
                                                     ^
contract51.kt:24:56: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun p6(s: String?): Int { ownCheck(s != null); return s.length }            // own-no-contract
                                                       ^
(exit 1)
```

**왜 그런가**

- ★★★ `require`·`check`·`requireNotNull` 은 `contract { returns() implies … }` 를 단다 — 돌아왔으면 조건이 참이라고 컴파일러가 안다.
- ★★ `if-error`·`elvis-TODO` 는 계약이 아니라 **`Nothing`** 덕분이다(10번).
- ★★ `assert` 에는 계약이 없다 — 꺼져 있으면 조건이 거짓이어도 돌아오기 때문이다(9번).

### 4. `require { }      messages built: 1 for 4 calls` · `requireEager(..) messages built: 4 for 4 calls` · `java.lang.IllegalArgumentException: bad value -7` — **`Function0` 은 안 나온다**

**출력**

```text
===== kotlinc lazy51.kt -d o51l =====
(exit 0)
===== java -cp o51l:kotlin-stdlib.jar Lazy51Kt =====
require { }      messages built: 1 for 4 calls
requireEager(..) messages built: 4 for 4 calls
java.lang.IllegalArgumentException: bad value -7
(exit 0)
===== javap -c -p o51l/Lazy51Kt.class | grep -E 'public static final|IllegalArgumentException."<init>"|Method expensive|Function0' =====
  public static final int getBuilt();
  public static final void setBuilt(int);
  public static final java.lang.String expensive(int);
  public static final void requireEager(boolean, java.lang.String);
      15: invokespecial #51                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
  public static final void viaRequire(int);
      15: invokestatic  #57                 // Method expensive:(I)Ljava/lang/String;
      27: invokespecial #51                 // Method java/lang/IllegalArgumentException."<init>":(Ljava/lang/String;)V
  public static final void viaEager(int);
      10: invokestatic  #57                 // Method expensive:(I)Ljava/lang/String;
  public static final void main();
(exit 0)
```

**왜 그런가**

- ★★★ `require` 의 몸통이 `if (!value) { val message = lazyMessage() … }` — 실패할 때만 람다를 부른다.
- ★★ `inline` 이라 람다 몸통이 `viaRequire` 안에 펼쳐진다 — `expensive` 호출과 `IllegalArgumentException."<init>"` 이 **직접** 보인다.

### 5. **`IllegalArgumentException` 셋**(빈 id · 음수 초깃값 · 금액 0) · **`IllegalStateException` 셋**(잔액 부족 · 닫힌 계좌 · 모르는 종류) · **`ok` 둘**(`70` · `5`)

**출력**

```kotlin
// form51.kt
class Account(val id: String, initial: Long) {
    var balance: Long = initial
        private set
    private var closed = false

    init {
        require(id.isNotBlank()) { "id must not be blank" }
        require(initial >= 0) { "initial must be >= 0, was $initial" }
    }

    fun withdraw(amount: Long) {
        require(amount > 0) { "amount must be > 0, was $amount" }
        check(!closed) { "account $id is closed" }
        check(balance >= amount) { "insufficient balance: $balance < $amount" }
        balance -= amount
    }

    fun close() {
        closed = true
    }
}

fun fee(kind: String): Int = when (kind) {
    "basic" -> 0
    "premium" -> 5
    else -> error("unknown kind: $kind")
}

fun show(label: String, block: () -> Any?) {
    val text = runCatching(block).fold({ "ok $it" }, { "${it::class.simpleName}: ${it.message}" })
    println("$label -> $text")
}

fun main() {
    val acc = Account("a1", 100)
    show("new Account(\" \", 1)") { Account(" ", 1) }
    show("new Account(\"a2\", -5)") { Account("a2", -5) }
    show("withdraw(30)") { acc.withdraw(30); acc.balance }
    show("withdraw(0)") { acc.withdraw(0) }
    show("withdraw(500)") { acc.withdraw(500) }
    acc.close()
    show("withdraw(10) after close") { acc.withdraw(10) }
    show("fee(\"premium\")") { fee("premium") }
    show("fee(\"gold\")") { fee("gold") }
}
```


```text
===== kotlinc form51.kt -d o51f =====
(exit 0)
===== java -cp o51f:kotlin-stdlib.jar Form51Kt =====
new Account(" ", 1) -> IllegalArgumentException: id must not be blank
new Account("a2", -5) -> IllegalArgumentException: initial must be >= 0, was -5
withdraw(30) -> ok 70
withdraw(0) -> IllegalArgumentException: amount must be > 0, was 0
withdraw(500) -> IllegalStateException: insufficient balance: 70 < 500
withdraw(10) after close -> IllegalStateException: account a1 is closed
fee("premium") -> ok 5
fee("gold") -> IllegalStateException: unknown kind: gold
(exit 0)
```

**왜 그런가**

- ★★ 빈 id · 음수 초깃값 · 금액 0 은 **호출자가 넘긴 값**이 틀렸다 → `IllegalArgumentException`.
- ★★ 잔액 부족 · 닫힌 계좌 · 모르는 종류 는 **객체의 지금 상태**(또는 불가능한 가지)다 → `IllegalStateException`.

### 6. `amount` 는 **호출자가 준 값**이고 `closed` 는 **객체의 지금 상태**다 — 클래스만 보고 「**고칠 곳이 호출자인가(`IllegalArgumentException`) · 호출 순서/상태인가(`IllegalStateException`)**」를 안다

**왜 그런가**

- ★★ 같은 `withdraw(10)` 도 닫히기 전에는 되고 닫힌 뒤에는 안 된다(5번) — 값이 아니라 **상태**가 거절한 것이다. 인자 검사를 `check` 로 하면 이 구분이 로그에서 사라진다.

### 7. **못 가른다** — 둘 다 `Required value was null.` · **예외 클래스**(`IllegalArgumentException` 대 `IllegalStateException`)로 가른다

**왜 그런가**

- ★★ 메시지는 stdlib 상수가 **같다**(1번 격자 3행 · 6행). 가르고 싶으면 **메시지 람다**를 주거나(`requireNotNull(x) { "…" }`) 클래스를 본다.

### 8. 컴파일러는 **함수 서명만 보고 몸통을 안 본다** — 계약이 「돌아왔으면 참」을 **서명 쪽에** 적어 준다 · 이 판에서도 **`@OptIn(ExperimentalContracts::class)`** 가 필요하다

**왜 그런가**

- ★★★ `ownCheck` 의 몸통이 `throw` 해도, 호출하는 쪽에서는 그 사실이 **타입에 안 드러난다.** `contract { returns() implies ok }` 가 그 사실을 **선언**한다.
- ★★ `ExperimentalContracts` 가 `@RequiresOptIn` 이라(2-summary (5)) opt-in 없이 쓰면 `contract`·`returns`·`implies` 세 자리가 모두 막힌다(3번).

### 9. **던지지는 않는데 부수 효과는 난다** — 조건이 인자라 먼저 계산된다 · 그래서 `assert` 는 「돌아왔으면 참」을 약속 못 하고, **계약이 없어 스마트 캐스트도 없다**

**왜 그런가**

- ★★★ 2번의 `legacy · java` 칸 — `nothing thrown` 이면서 `condition evaluated 1`. 운영 JVM 은 보통 `-ea` 가 없다.
- ★★ 같은 이유로 `assert(s != null)` 을 지나도 `s` 는 여전히 널일 수 있다 — 컴파일러가 좁히지 않는 것이 **맞다**(3번).

### 10. **`Nothing` 이 모든 타입의 하위 타입**이라 `s ?: TODO()` 의 타입이 `String` 이 된다 · `TODO()` 가 빠져나가는 것은 [49번 주제](../49-result-and-runcatching/) (4)의 **던지기 5 × 잡기 2 격자**(`runCatching` 만 잡은 행 2 / 5)

**왜 그런가**

- ★★ [34번 주제](../34-exceptions-nothing-and-try-expression/) (3)(4) — `String?` 과 `Nothing` 을 합치면 `Nothing` 은 아무것도 보태지 않는다. `error()` 도 반환 타입이 `Nothing` 이다(2-summary (5)의 선언).
- ★ 이 문서는 두 성질을 **다시 재지 않았다.**

## 실행 검증

```text
===== kotlinc -version =====
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
(exit 0)
```

```text
===== java -version =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
(exit 0)
```

```text
===== python3 --version =====
Python 3.12.3
(exit 0)
```

★ **흔들리는 칸과 안 흔들리는 칸**

| 흔들린다 | 안 흔들린다 |
|---|---|
| **없다** — 해시코드·주소·시간·스택 트레이스를 찍지 않았다 | 던지기 격자 11행 × 2벌 · 클래스별 개수 · 갈린 행 수 |
| | `-Xassertions` 격자 4 × 2 · 계약 격자 9탐침 · 진단 문구 |
| | `javap` 발췌 · 소스 발췌 · 모든 **종료 코드** |

> 근거 — 캡처 스크립트를 처음부터 다시 돌려 **블록 전체를 대조**했다.
>
> 실측 — `capture.sh blocks` 와 `capture.sh blocks-recheck` 를 처음부터 따로 돌려 `normalize-shaky.py` 로 대조했다 —\
> **블록 74개 · 동일 74 · 흔들린 칸 0 · ★고칠 것 0**(50\~53 네 주제를 한 캡처로 받았다). 추가한 정규화 규칙은 **없다**.

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `throw51.kt` · `grid51.py` | ★★★ 계약 함수 11가지 → 클래스 · 메시지 × `java`/`java -ea` | 한 번 컴파일 → 스크립트가 두 벌로 돌려 합친다 |
| `assert51.kt` · `grid51a.py` | ★★ `-Xassertions` 4모드 × `-ea` → 던졌나 · 조건을 평가했나 | 스크립트가 모드마다 컴파일 → 두 벌로 실행 |
| `contract51.kt` · `grid51c.py` | ★★★ 스마트 캐스트 9탐침 | 스크립트가 컴파일 · 진단을 줄마다 읽는다 + 같은 파일의 에러 전문 |
| `lazy51.kt` | ★★ 메시지 생성 횟수 · `inline` 펼침 | `kotlinc` → `java` → `javap -c`(전부 받은 뒤 `grep`) |
| stdlib 소스 jar | KDoc · 기본 메시지 · 계약 · `assert` 선언 · opt-in 표지 | `unzip` → `sed -n` |
| `form51.kt` | 형태 한 벌 | `kotlinc` → `java` |

**구현 의존 항목** — 기본 메시지 문자열 · 람다가 펼쳐지는 바이트코드 · `-Xassertions` 모드의 이름 — 이 판의 산출물이다.\
반면 **`require`→`IllegalArgumentException` · `check`→`IllegalStateException`**(KDoc) · **`TODO` 가 `Error`**(선언) · **계약이 스마트 캐스트를 준다**(언어 — 실험적) 는 **계약**이다.

**★ 던져 봤더니 예상과 달랐던 것 — 세 건**

1. ★★★ **기본 모드의 `assert` 는 `-ea` 없이도 조건을 평가했다** — 「꺼져 있으면 아무 일도 없다」가 아니었다. `-Xassertions=jvm` 이라야 그렇다.
2. ★★ **`assert` 에는 계약이 없다** — `require` 와 같은 모양인데 스마트 캐스트가 안 됐다.
3. ★★ **`requireNotNull` 과 `checkNotNull` 의 기본 메시지가 한 글자도 같다** — 클래스로만 갈린다.
