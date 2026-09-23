# kotlin/syntax/04 — 스마트 캐스트와 그것이 깨지는 자리 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 에러·출력은 **kotlinc 2.4.20 (JRE 21.0.5)** 에서 실제로 얻었다.\
> 「깨지는 자리」는 **열한 가지를 따로 던져** 받은 것이고, 동시성 실험은 **20만 회 × 5판**을 돌렸다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 이 여덟 함수 중 컴파일되는 것은 무엇인가

**출력** (`kotlinc break.kt` — 한 파일에 몰아 넣고 한 번에 던졌다)

```text
break.kt:10:47: error: smart cast to 'String' is impossible, because 's' is a mutable property that could be mutated concurrently.
fun f1(o: VarProp) { if (o.s != null) println(o.s.length) }          // var 프로퍼티
                                              ^^^
break.kt:12:52: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun f3(o: CustomGetter) { if (o.s != null) println(o.s.length) }     // 커스텀 getter
                                                   ^^^
break.kt:13:45: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun f4(o: Iface) { if (o.s != null) println(o.s.length) }            // 인터페이스 프로퍼티
                                            ^^^
break.kt:18:29: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    if (v != null) println(v.length)
                            ^
break.kt:28:42: error: smart cast to 'String' is impossible, because 'topLevel' is a mutable property that could be mutated concurrently.
fun f7() { if (topLevel != null) println(topLevel.length) }          // 최상위 var
                                         ^^^^^^^^
break.kt:31:49: error: smart cast to 'String' is impossible, because 's' is a delegated property.
fun f8(o: Delegated) { if (o.s != null) println(o.s.length) }        // 위임 프로퍼티
                                                ^^^
```

**왜 그런가**

| 함수 | 결과 | 메시지 |
|---|---|---|
| `f1` `var` 멤버 프로퍼티 | 에러 | `mutable property that could be mutated concurrently` |
| `f2` 같은 모듈 `val` 프로퍼티 | **통과** | — |
| `f3` 커스텀 getter | 에러 | `property that has an open or custom getter` |
| `f4` 인터페이스 프로퍼티 | 에러 | 같은 문구 |
| `f6` 지역 `var`(람다 없음) | **통과** | — |
| `f7` 최상위 `var` | 에러 | `mutable property … concurrently` |
| `f8` 위임 프로퍼티 | 에러 | `delegated property` |

- **에러 메시지는 세 종류**다(2번의 넷째 종류는 별도).
- `f2` 와 `f1` 을 가르는 것은 **`val` 이냐 `var` 이냐**다. `val` 프로퍼티는 `private final` 필드가 되어\
  누구도 못 바꾼다([01번](../01-val-var-and-basic-types/)의 (2)에서 `javap` 로 확인한 그것).
- `f4`(인터페이스)가 `getter` 쪽 메시지인 이유 — **인터페이스는 필드를 못 가지므로 구현이 getter 일 수밖에 없다.**\
  즉 컴파일러가 보는 것은 "선언에 `val` 이라 적혀 있나" 가 아니라 **"읽을 때 무슨 일이 일어나나"** 다.
- `f6` 이 통과하는 이유 — **지역 `var` 은 이 함수 밖에서 닿을 수 없다.** 다른 스레드도, 다른 코드도 못 바꾼다.\
  `var` 라는 낱말이 문제가 아니라 **누가 바꿀 수 있는가**가 문제다.

### 2. ★★ 이 둘은 어떤 에러를 내는가 — 그리고 왜 메시지가 다른가

**출력** (`kotlinc cap.kt` · `kotlinc more.kt`)

```text
cap.kt:10:29: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    if (v != null) println(v.length)
                            ^
cap.kt:20:35: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
    run { if (v != null) println(v.length) }
                                  ^
```

```text
more.kt:4:39: error: only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.
fun b() { if (f() != null) println(f().length) }            // 함수 호출 결과
                                      ^
```

**왜 그런가**

| | 형태 | 결과 |
|---|---|---|
| `b` | 람다가 `v` 를 **고친다** | 에러 |
| `c` | 람다가 `v` 를 **읽기만 한다** | **통과** |
| `d` | 함수 호출 결과 | 에러 |

- ★ **메시지가 1번의 셋과 다르다.** 1번은 `smart cast to 'String' is impossible, because …` 로\
  **이유가 적혀 있는데**, 여기는 그냥 `only safe (?.) or non-null asserted (!!.) calls are allowed…` 다.
- 메시지가 다른 이유 한 문장 — **1번의 셋은 "이 값이 있긴 한데 안정적이지 않다" 이고, 여기는 「그 값」이라 부를 대상 자체가 없다.**\
  컴파일러 입장에서는 **스마트 캐스트를 시도조차 안 한 것**이므로 "불가능한 이유" 를 댈 것도 없다.\
  그래서 그냥 "타입이 `String?` 이니 `?.` 나 `!!.` 를 쓰라" 는 **기본 규칙**으로 떨어진다.
- 이 문구는 **[03번](../03-null-safe-types/)의 1번 `[B]`** 에서 이미 본 것이다 — `val s: String?` 에 `.length` 를 그냥 부를 때 나온 바로 그 메시지.
- 실무 함의 — **이 두 경우는 메시지가 이유를 안 알려 주므로 직접 찾아야 한다.**\
  "람다가 이 변수를 고치나?" 와 "이게 함수 호출인가?" 두 가지를 본다.
- `c` 가 통과하는 것이 중요하다 — **캡처 자체는 문제가 아니다. 고쳐 쓰는 것이 문제다.**

### 3. ★★ 모듈을 나눠 컴파일하면 무엇이 달라지는가

**출력** (`kotlinc modA/lib.kt -d outA/` → `kotlinc modB/use.kt -cp outA -d outB/`)

```text
modB/use.kt:3:43: error: smart cast to 'String' is impossible, because 's' is a public API property declared in different module.
fun g1(b: Box) { if (b.s != null) println(b.s.length) }
                                          ^^^
modB/use.kt:4:47: error: smart cast to 'String' is impossible, because 's' is a property that has an open or custom getter.
fun g2(b: OpenBox) { if (b.s != null) println(b.s.length) }
                                              ^^^
```

**왜 그런가**

- **둘 다 에러다.** 메시지가 서로 다르다 — `g1` 은 **모듈 경계**, `g2` 는 **`open` 이라 getter 가 오버라이드될 수 있음**.
- `Box.s` 는 분명히 `val` 이고 getter 도 없다. **같은 모듈이었다면 통과했다**(1번의 `f2`).\
  같은 선언이 **모듈 경계를 건너는 순간 거부**된다.

```text
   같은 모듈                          다른 모듈
   +------------------------+         +------------------------------+
   | 컴파일러가 선언을       |         | .class 만 본다               |
   | 직접 본다               |         | 그 모듈은 나중에 val -> var  |
   | -> val 이면 안정        |         | 로 바뀌어 재배포될 수 있다   |
   |                        |         | 내 코드는 재컴파일 안 될 수  |
   |                        |         | 있다 -> 믿을 수 없다         |
   +------------------------+         +------------------------------+
```

- 막으려는 사고는 **바이너리 호환 문제**다. 라이브러리가 `val` 을 `var` 로 바꿔 올리면\
  이미 컴파일된 내 코드는 **좁혀진 타입을 그대로 믿은 채** 돌게 된다.\
  컴파일러는 그 미래를 못 막으므로 **처음부터 안 좁힌다.**
- `g2` 는 모듈과 무관하다 — `open val` 은 같은 모듈에서도 거부된다(하위 클래스가 getter 를 갈아끼울 수 있다).

### 4. ★ `@Volatile` 을 붙이면 풀리는가

**출력** (`kotlinc more.kt`)

```text
more.kt:3:40: error: smart cast to 'String' is impossible, because 's' is a mutable property that could be mutated concurrently.
fun a(o: V) { if (o.s != null) println(o.s.length) }       // @Volatile var
                                       ^^^
```

**출력** (`kotlinc sync.kt` — `synchronized` 로 감싼 판)

```text
sync.kt:5:34: error: smart cast to 'String' is impossible, because 's' is a mutable property that could be mutated concurrently.
        if (o.s != null) println(o.s.length)
                                 ^^^
```

**왜 그런가**

- ★ **둘 다 안 된다.** 메시지도 같다 — `@Volatile` 을 안 붙였을 때와 **한 글자도 다르지 않다.**
- 각각이 주는 것과 요구하는 것이 어긋난다.

| | 보장하는 것 | 스마트 캐스트가 요구하는 것 |
|---|---|---|
| `@Volatile` | **쓰기가 다른 스레드에 즉시 보인다**(가시성) | — |
| `synchronized` | 같은 락을 잡은 코드끼리 배타 실행 | — |
| 요구 | — | **두 번 읽어도 같은 값** |

- `@Volatile` 은 **최신 값을 보게** 해 줄 뿐 **그 값이 안 바뀌게** 해 주지 않는다.\
  오히려 volatile 이면 **더 자주 바뀐 값을 본다.**
- `synchronized` 가 안 되는 이유는 더 단순하다 — **컴파일러가 락을 추론하지 않는다.**\
  `o.s` 를 고치는 쪽이 같은 락을 잡는다는 보장이 어디에도 없고, 그것을 증명하는 기능이 컴파일러에 없다.
- **해법은 하나뿐이다 — 읽기를 한 번으로 줄여 로컬 `val` 에 묶는다**(7번).

### 5. ★★ 커스텀 getter 에 `!!` 를 붙이면 무슨 일이 일어나는가

**출력** (`why.kt`)

```text
--- 커스텀 getter 는 부를 때마다 값이 다를 수 있다 ---
1회: 가   2회: null   3회: 가   4회: null
-> if (f.s != null) 로 통과해도 다음 f.s 는 null 일 수 있다
--- 그래서 !! 로 우회하면 실제로 터진다 ---
g.s!! -> java.lang.NullPointerException (message=null)
```

**왜 그런가**

```text
   if (g.s != null) {      ← 1회 호출: "가"  → 조건 통과
       g.s!!.length        ← 2회 호출: null  → NPE
   }
```

- 네 번 찍으면 `가 / null / 가 / null` 이다 — **getter 안의 `n++` 때문에 호출마다 답이 다르다.**
- 위 두 줄은 **무사히 돌지 않는다.** NPE 가 난다(`message=null` — [03번](../03-null-safe-types/)의 3번대로 `!!` 는 메시지가 없다).
- **스레드가 하나뿐인데도 터지는 이유** — 문제는 동시성이 아니라 **`val` 이라 적힌 것이 값이 아니라 함수**라는 점이다.\
  `val s: String? get() = …` 는 **매번 실행되는 코드**다.
- `if` 의 `g.s` 와 본문의 `g.s` 는 **두 번의 서로 다른 호출**이다. 소스에서 같은 글자로 보일 뿐이다.
- 그래서 1번 `f3` 의 거부는 **컴파일러가 실제 실패를 미리 막은 것**이다. 잔소리가 아니다.

### 6. ★★ `var` 프로퍼티에 `!!` 를 쓰면 실제로 얼마나 터지는가

**출력** (`why.kt` — **5판**)

```text
20만 회 중 !! 가 터진 횟수 = 242
20만 회 중 !! 가 터진 횟수 = 96
20만 회 중 !! 가 터진 횟수 = 252
20만 회 중 !! 가 터진 횟수 = 492
20만 회 중 !! 가 터진 횟수 = 256
```

```text
(같은 실행의 뒷부분 — 로컬 val 스냅샷 판)
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
20만 회 중 터진 횟수 = 0
```

**왜 그런가**

- ★ **`crashed` 는 0이 아니다.** 다섯 판 **전부** 0이 아니었다.
- **다섯 판의 값은 같지 않다** — `96 \~ 492`. 이 수치는 **한 판의 관찰**이고,\
  스케줄링·JIT 상태에 달렸다. **이 숫자로 확률을 말하면 안 된다.**\
  재현되는 것은 **"0이 아니다" 라는 사실 하나**뿐이고, 결론은 그 위에만 세운다.
- ★ **스냅샷 판의 0은 성격이 다르다.** 이것은 "다섯 판 돌려 보니 안 터지더라" 라는 **관찰이 아니라 논증**이다 —\
  `val snap = m2.s` 의 `snap` 은 **지역 변수**라 다른 스레드가 닿을 방법이 아예 없다.\
  (동시성 주제에서 "통과한 실행" 은 대개 가장 약한 근거다. 여기서 0을 근거로 쓸 수 있는 것은\
  **값이 공유되지 않는다는 구조** 때문이지 판 수 때문이 아니다.)
- 이 실험이 컴파일러 에러에 대해 말해 주는 것 — **`mutable property that could be mutated concurrently` 의 `could` 는 실제로 일어난다.**\
  `!!` 로 우회하는 것은 **컴파일 에러를 런타임 예외로 바꾸는 것**이지 문제를 없애는 게 아니다.

### 7. 깨졌을 때 푸는 법 넷은 무엇인가

```kotlin
// 1. 로컬 val 로 받는다 (가장 흔함)
val s = o.s
if (s != null) println(s.length)

// 2. 엘비스 조기 반환 — 그 아래 전부가 좁혀진다
val s = o.s ?: return
println(s.length)

// 3. ?.let — 블록 인자가 곧 안정 값이다
o.s?.let { println(it.length) }

// 4. 안 되면 ?. 를 그냥 쓴다
println(o.s?.length ?: 0)
```

**왜 그런가**

```text
   깨진 자리                        고친 자리
   +--------------------------+     +---------------------------+
   | if (o.s != null)         |     | val s = o.s               |
   |     o.s.length   ERROR   |     | if (s != null)            |
   +--------------------------+     |     s.length     OK       |
                                    +---------------------------+
      두 번 읽는다                      한 번 읽어 고정한다
```

- **공통점 한 문장 — 넷 다 「읽기를 한 번으로 줄여 그 결과를 `val` 에 묶는다」.**\
  4번조차 그렇다 — `o.s?.length` 는 `o.s` 를 **한 번만** 읽는다([03번](../03-null-safe-types/)의 2번 바이트코드가 `aload_0; dup; ifnull` 이었다).
- `?.let { }` 의 `it` 이 자동으로 풀리는 이유 — `let` 의 시그니처가 `inline fun <T, R> T.let(block: (T) -> R): R` 이라\
  **수신자를 파라미터로 한 번 넘긴다.** 그 파라미터가 곧 로컬 `val` 이다. **1번을 문법으로 포장한 것.**
- `!!` 가 해법이 아닌 이유는 5·6번이 증명한다 — **커스텀 getter 면 단일 스레드에서도 터지고,\
  `var` 프로퍼티면 20만 회 중 수백 번 터진다.**

### 8. K2 는 어디까지 따라오는가

**출력** (`k2.kt` — 좁혀지는 형태 11가지를 한 프로그램에 몰아 넣었다. **경고 한 건도 없다.**)

```text
a (boolean val 이 검사를 들고 있음) -> 2
b (|| 오른쪽에서 좁혀짐)        -> 2
c (&& 오른쪽에서 좁혀짐)        -> 마
e (엘비스 조기 반환)            -> 3
g (require 의 contract)         -> 3
h (?.let 의 it)                 -> 2
i (좁혀진 값을 람다가 잡음)     -> 1
j (람다가 읽기만 하는 var)      -> 1, reader()=1
k (인라인 람다 안)              -> 1
l (제네릭 val)                  -> 1
f (when 의 가지) -> f("x")=1, f(1)=2, f(null)=-1, f(1.0)=0
```

**왜 그런가**

- ★ `val isStr = x is String; if (isStr) x.length` — **통과한다**(`a`).\
  검사 결과를 **`Boolean` 변수에 담아 두어도** 컴파일러가 그 변수의 뜻을 따라간다. 이것이 데이터 흐름 분석이다.
- `||` 의 오른쪽도 좁혀진다(`b`) — 왼쪽 `x !is String` 이 거짓이어야 오른쪽이 평가되므로,\
  그 지점에서 `x` 는 이미 `String` 이다.
- 람다가 **읽기만** 하면 람다 안에서도, 람다 밖에서도 좁혀진다(`i`·`j`). 2번의 `c` 와 같은 결론이다.
- ★ **K1 과 비교하지 못했다.**

```text
$ kotlinc -language-version 1.9 k2.kt
error: language version 1.9 is no longer supported; use version 2.0 or greater instead.
```

  **이 컴파일러는 K1 을 돌리지 않는다.** "K2 에서 새로 되는 것" 이라는 문장은 이 문서에서 **실측으로 뒷받침되지 않는다** —\
  확인한 것은 **"2.4.20 에서 이 11가지가 된다" 뿐**이다.

### 9. 어느 것이 언어 규칙이고 어느 것이 컴파일러 능력인가

| 사실 | 어느 쪽 | 근거 |
|---|---|---|
| "안정 값이면 좁힌다" | **언어** | 명세 |
| 로컬 `val` 이 안정이다 | **언어** | 명세 |
| `var` 프로퍼티·위임·다른 모듈이 안정이 아니다 | **언어** | 명세 + 에러 |
| **`val isStr = x is String` 을 거쳐도 좁힌다** | **컴파일러 능력** ★ | 실측 — 명세가 정한 게 아니다 |
| **논리 OR(`\|\|`) 오른쪽에서 좁힌다** | **컴파일러 능력** | 실측 |
| **에러 메시지 문구** | **구현**(이 버전) | 실측 |
| **9·9' 만 일반 문구인 것** | **구현** | 실측 |

- ★ **"이건 원래 안 되는 것" 이라고 외우면 안 되는 이유** —\
  명세가 정한 것은 **"안정 값이면 좁힌다"** 까지이고,\
  **무엇을 안정이라고 증명할 수 있는지는 컴파일러가 얼마나 똑똑한가**에 달렸다.\
  그래서 되는 범위는 **버전이 오르면 늘어난다.** 안 되는 형태를 만나면 **버전을 먼저 확인한다.**
- 뒤집어서, **안 되는 이유가 「명세가 금지해서」인 것**(`var` 프로퍼티·다른 모듈)은 **앞으로도 안 된다.**\
  그건 컴파일러가 똑똑해져서 풀릴 문제가 아니라 **원리상 증명할 수 없는 것**이다.

### 10. 통과하는 다섯 자리는 어디인가

| 자리 | 결과 | 조건 |
|---|---|---|
| **같은 모듈의 `val` 프로퍼티** | 통과 | **커스텀 getter 도 `open` 도 아닐 것** |
| **지역 `var`** | 통과 | **람다가 고쳐 쓰지 않을 것** |
| **람다가 읽기만 하는 지역 `var`** | 통과 | — |
| **인라인 람다(`run { }`) 안** | 통과 | 바깥 변수가 안정이면 |
| **제네릭 `val`**(`class G<T>(val t: T)` 의 `g.t`) | 통과 | `val` 이고 getter 없음 |

- 같은 모듈의 `val` 도 **세 조건 중 하나만 어겨도 깨진다** — getter 가 있거나, `open` 이거나, 위임이거나.\
  1번의 `f2`(통과)와 `f3`·`f4`·`f8`(거부)이 그 차이다.
- 지역 `var` 은 **람다가 고쳐 쓰는 순간** 깨진다(2번의 `b`). 읽기만 하면 안 깨진다(`c`).
- 제네릭이 통과하는 것은 **`T` 가 `String?` 으로 실체화되어도 `val` 이고 getter 가 없기 때문**이다.\
  "제네릭이라 불안정할 것" 이라는 직관이 여기서는 틀린다.

### 11. 다른 주제와 잇기

- **같은 문구** — 2번의 `only safe (?.) or non-null asserted (!!.) calls are allowed on a nullable receiver of type 'String?'.` 은\
  [03번](../03-null-safe-types/)의 **1번 `[B]`** 에서 나온 메시지와 같다.\
  즉 그 경우들은 **"스마트 캐스트가 깨진 것" 이 아니라 애초에 시도되지 않은 것**이다.
- **Java 의 `instanceof` 패턴** — `if (o instanceof String s)` 는 **새 변수 `s` 를 선언**해서\
  "두 번 읽는다" 는 문제를 아예 안 만든다. Kotlin 은 **기존 이름을 좁히는** 쪽을 골랐고 그 대가가 이 문서의 목록이다.\
  정본은 [`../../../java/syntax/22-instanceof-type-patterns/`](../../../java/syntax/22-instanceof-type-patterns/),\
  `switch` 쪽은 [`../../../java/syntax/23-switch-pattern-matching/`](../../../java/syntax/23-switch-pattern-matching/).
- **`require(x is String)`** 이 좁혀 주는 근거는 **contract** 다 — stdlib 함수가\
  "정상 반환하면 이 조건이 참" 을 컴파일러에 선언해 둔 것이다. 정본은 목록의 **51번 주제**(`require`/`check`/`error`).
- **플랫폼 타입([05번](../05-platform-types/))에는 이 문제가 안 생긴다** —\
  Java 에서 온 값은 애초에 non-null 처럼 쓸 수 있어 **검사도 스마트 캐스트도 필요 없다.**\
  ★ **그래서 더 위험하다.** 이 문서에서 컴파일러가 아홉 자리에서 막아 준 그 방어가,\
  05번에서는 **아무것도 안 막고 통과**한다.

---

## 실행 검증

**환경**

```text
info: kotlinc-jvm 2.4.20 (JRE 21.0.5+11-LTS)
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
```

| 프로그램 | 무엇을 확인했나 | 돌린 방법 |
|---|---|---|
| `break.kt` | 깨지는 자리 6 + 통과 2 를 한 번에 | `kotlinc break.kt` (컴파일 실패가 결과) |
| `cap.kt` | 람다가 **고치는** `var` 대 **읽는** `var`, 인라인 람다 안팎 4경우 | `kotlinc cap.kt` |
| `more.kt` | `@Volatile var`, 함수 호출 결과, 제네릭 `val` | `kotlinc more.kt` |
| `sync.kt` | `synchronized` 로 감싸도 안 되는 것 | `kotlinc sync.kt` |
| `modA/lib.kt` + `modB/use.kt` | **모듈 경계** — 따로 컴파일해야만 나오는 에러 | `kotlinc modA/lib.kt -d outA/` → `kotlinc modB/use.kt -cp outA -d outB/` |
| `why.kt` | 커스텀 getter 4회 호출, `!!` NPE, **20만 회 경쟁 실험 + 스냅샷 대조** | `kotlinc` → `java` **5회** |
| `k2.kt` | 좁혀지는 형태 11가지 (라벨을 붙여 한 실행에) | `kotlinc` → `java` |
| `k2.kt` (구버전) | K1 비교 시도 | `kotlinc -language-version 1.9 k2.kt` → **거부** |

**구현 의존 항목** — 에러 메시지 문구 전부, 9·9' 가 일반 문구로 떨어지는 것,
K2 가 `val isStr` 을 따라가는 것, `||` 오른쪽에서 좁히는 것 — **이 컴파일러 버전의 능력**이다.\
반면 "`var` 프로퍼티·위임·다른 모듈은 안정이 아니다"·"안정 값이면 좁힌다" 는 **언어 규칙**이다.

**흔들리는 칸 / 안 흔들리는 칸**

| | 흔들린다 | 안 흔들린다 |
|---|---|---|
| 경쟁 실험 | **터진 횟수**(96 \~ 492, 5판) | **0이 아니라는 사실**(5판 전부) |
| 스냅샷 실험 | — | **0**(구조적으로 공유되지 않는다) |
| 컴파일 에러 | — | 메시지·위치(같은 입력에 같은 출력) |

**제출 직전 재확인** — 경쟁 실험을 한 판 더 돌렸다. **처음 다섯 판의 값을 지우지 않고 나란히 남긴다.**

```text
--- var 프로퍼티: 다른 스레드가 바꾸면 ---
20만 회 중 !! 가 터진 횟수 = 462
--- 로컬 val 로 받으면 안전하다 ---
20만 회 중 터진 횟수 = 0
```

여섯 판의 값은 **242 · 96 · 252 · 492 · 256 · 462** 다.
**움직인다는 사실 자체가 이 절의 결론**이므로 값 하나를 본문의 근거로 쓰지 않았다.
스냅샷 판은 여섯 판 모두 0이다.

**못 잰 것** — **K1(2.0 이전)과의 비교.**
`-language-version 1.9` 가 `language version 1.9 is no longer supported` 로 거부되어
"K2 에서 새로 되는 것" 을 이 머신에서 가를 수 없었다.
그래서 8번의 결론은 **"2.4.20 에서 이 11가지가 된다" 까지**로만 적었다.
옛 컴파일러를 따로 받아야 재는 항목이고, 그것은 도구 설치라 하지 않았다.
