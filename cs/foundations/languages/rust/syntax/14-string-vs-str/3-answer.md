# rust/syntax/14 — `String` 대 `&str` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.\
> ★ 이 주제의 고유 창은 **`size_of` 로 스택 칸 세기**(1번)와 **`as_ptr()` 로 힙 주소 대조**(2번)다.\
> ★ **크기·포인터 숫자는 `x86_64` 기준**이고, **주소 절댓값은 다시 돌리면 달라진다**(2번에 그 표시를 달았다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `String` 24 · `&str` 16 · `&String` 8 — 3워드 · 2워드 · 1워드

**출력**

```text
===== 소스: ex.rs =====
// 세 꼴이 스택에서 몇 바이트인가 — 외우지 말고 전부 찍는다
use std::mem::size_of;

fn main() {
    println!("포인터 폭 usize = {}", size_of::<usize>());
    println!("-- 소유하는 것 --");
    println!("String     = {}", size_of::<String>());
    println!("Vec<u8>    = {}", size_of::<Vec<u8>>());
    println!("-- 빌린 것 --");
    println!("&str       = {}", size_of::<&str>());
    println!("&[u8]      = {}", size_of::<&[u8]>());
    println!("&String    = {}", size_of::<&String>());
    println!("&&String   = {}", size_of::<&&String>());
    println!("&&&String  = {}", size_of::<&&&String>());
    println!("&Vec<u8>   = {}", size_of::<&Vec<u8>>());
    println!("&&str      = {}", size_of::<&&str>());
    println!("-- 그 밖 --");
    println!("Box<str>   = {}", size_of::<Box<str>>());
    println!("Box<String>= {}", size_of::<Box<String>>());
    println!("char       = {}", size_of::<char>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
포인터 폭 usize = 8
-- 소유하는 것 --
String     = 24
Vec<u8>    = 24
-- 빌린 것 --
&str       = 16
&[u8]      = 16
&String    = 8
&&String   = 8
&&&String  = 8
&Vec<u8>   = 8
&&str      = 8
-- 그 밖 --
Box<str>   = 16
Box<String>= 8
char       = 4
(종료 코드 0)
```

**왜 그런가**

- **포인터 폭을 같이 찍는 것이 요령**이다. 8이 나왔으므로 나머지를 **워드 수**로 읽을 수 있다 —\
  `String` = 3워드 · `&str` = 2워드 · `&String` = 1워드.
- **`String` 3칸** — 힙 주소(`ptr`) · 지금 바이트 수(`len`) · 잡아 둔 바이트 수(`cap`). **힙을 소유**하므로 해제할 책임이 있고, 그래서 `cap` 이 필요하다.
- **`&str` 2칸** — 가리키는 곳이 **주인이 아니라 바이트 덩어리**라 길이를 **자기가 들고 다녀야** 한다.\
  이것이 **팻 포인터**다. `&[u8]` 이 같은 16인 것도 같은 이유다.
- **`&String` 1칸** — 가리키는 것이 **주인**이다. 길이는 그 주인이 들고 있으니 **한 번 더 건너뛰면 된다.**
- **`&&String` 도 8** — 참조는 안쪽이 얇으면 바깥도 얇다. `&&str` 도 8인데,\
  이쪽은 「**팻 포인터를 가리키는 얇은 포인터**」다. 두 8은 같은 숫자인데 뜻이 다르다.
- **`Box<str>` 16 대 `Box<String>` 8** — `str` 은 **크기 미정 타입**이라 `Box` 가 길이를 같이 든다.\
  `Box<String>` 은 이미 크기가 정해진 것(24바이트)을 가리키니 얇다.
- ★ **외우지 않는 방법이 이 코드 자체**다. `size_of` 는 컴파일 타임 상수라 공짜다([**03번 주제**](../03-primitive-types-and-integer-overflow/)의 도구).

```text
   String                       &str                     &String
   +----------+                 +----------+             +----------+
   | ptr      |--> 힙           | ptr      |--> 힙       | ptr      |--> String 의 스택 3칸
   | len      |                 | len      |             +----------+
   | cap      |                 +----------+              8 = 1 워드
   +----------+                  16 = 2 워드
    24 = 3 워드                                          ← 길이를 안 든다.
   ← 힙을 소유·해제한다          ← 길이를 자기가 든다        가리키는 쪽이 들고 있다
```

### 2. ★★ 앞의 셋은 같은 주소, `clone` 만 다른 주소

**출력**

```text
===== 소스: ex.rs =====
// String -> &str 이 복사인가 — 힙 주소를 직접 찍어 본다
fn main() {
    let s = String::from("가나다라마");
    let c = s.clone();

    println!("s.as_ptr()            = {:p}", s.as_ptr());
    println!("(&s[..]).as_ptr()     = {:p}", (&s[..]).as_ptr());
    println!("s.as_str().as_ptr()   = {:p}", s.as_str().as_ptr());
    println!("(&*s).as_ptr()        = {:p}", (&*s).as_ptr());
    println!("c.as_ptr()  (clone)   = {:p}", c.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_ptr()            = 0x5cdd3af3ed00
(&s[..]).as_ptr()     = 0x5cdd3af3ed00
s.as_str().as_ptr()   = 0x5cdd3af3ed00
(&*s).as_ptr()        = 0x5cdd3af3ed00
c.as_ptr()  (clone)   = 0x5cdd3af3ed20
(종료 코드 0)
```

★★ **대조할 것은 숫자가 아니라 「같다 / 다르다」라는 성질이다.** 주소 절댓값은 다시 돌리면 달라진다.

**왜 그런가**

- ★ **문서에 주소를 그대로 실으면 재대조가 반드시 깨진다.** 그래서 **바로 아래에 저 한 줄**을 붙인다.
- ★ **더 나은 방법은 관계를 출력으로 굳히는 것**이다. 같은 실험을 `assert_eq!` 로 다시 쓰면 **다시 돌려도 한 글자도 안 바뀐다.**

```text
===== 소스: ex.rs =====
// 같은 것을 「숫자」가 아니라 「성질」로 찍는다 — 다시 돌려도 출력이 같다
fn main() {
    let s = String::from("가나다라마");
    let c = s.clone();

    assert_eq!(s.as_ptr(), (&s[..]).as_ptr());
    println!("s.as_ptr() == (&s[..]).as_ptr()    : 같다");

    assert_eq!(s.as_ptr(), s.as_str().as_ptr());
    println!("s.as_ptr() == s.as_str().as_ptr()  : 같다");

    assert_eq!(s.as_ptr(), (&*s).as_ptr());
    println!("s.as_ptr() == (&*s).as_ptr()       : 같다");

    assert_ne!(s.as_ptr(), c.as_ptr());
    println!("s.as_ptr() != c.as_ptr()  (clone)  : 다르다");

    // 길이도 같이 본다 — &str 은 주소와 길이 두 칸이다
    println!("s.len() = {} / (&s[..]).len() = {}", s.len(), (&s[..]).len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_ptr() == (&s[..]).as_ptr()    : 같다
s.as_ptr() == s.as_str().as_ptr()  : 같다
s.as_ptr() == (&*s).as_ptr()       : 같다
s.as_ptr() != c.as_ptr()  (clone)  : 다르다
s.len() = 15 / (&s[..]).len() = 15
(종료 코드 0)
```

- **`&s[..]`·`s.as_str()`·`&*s` 는 셋 다 같은 것**을 만든다 — 표기만 다르다.\
  `as_str()` 은 명시적 메서드, `&*s` 는 `Deref` 를 직접 부른 것, `&s[..]` 는 범위 문법이다.
- **복사가 일어나는 쪽은 `clone()`** 이다. 새 힙 버퍼를 잡았으므로 주소가 다르다.\
  [**08번 주제**](../08-ownership-and-move/)의 「이동은 스택 세 칸만 간다」와 **같은 그림**이다.
- **한 `String` 을 나눠 봐도 할당은 없다.**

```text
===== 소스: ex.rs =====
// &str 은 「주소 + 길이」다 — 한 String 을 두 창이 나눠 본다
fn main() {
    let s = String::from("가나다라");     // 한글 4자 = 12바이트
    let head: &str = &s[..3];             // 첫 글자
    let tail: &str = &s[3..];             // 나머지

    let base = s.as_ptr() as usize;
    println!("s    len={} cap={}", s.len(), s.capacity());
    println!("head 시작 오프셋={} len={} 내용={}", head.as_ptr() as usize - base, head.len(), head);
    println!("tail 시작 오프셋={} len={} 내용={}", tail.as_ptr() as usize - base, tail.len(), tail);
    println!("셋이 같은 힙 버퍼인가: {}", head.as_ptr() == s.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s    len=12 cap=12
head 시작 오프셋=0 len=3 내용=가
tail 시작 오프셋=3 len=9 내용=나다라
셋이 같은 힙 버퍼인가: true
(종료 코드 0)
```

★ **오프셋은 결정적이다** — 주소는 흔들려도 **차이**는 안 흔들린다. 흔들리는 값을 쓸 때의 요령이다.
`3` 이라는 경계가 왜 「글자 하나」인지는 [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)가 정본이다.

### 3. ★★ 리터럴 쪽만 거부된다 — E0308

**출력**

```text
===== 소스: ex.rs =====
// 인자를 &String 으로 받으면 — 리터럴을 넘길 수 있나
fn shout(s: &String) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    println!("{}", shout(&owned));   // 이건 된다
    println!("{}", shout("hello"));  // 리터럴은?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:7:26
  |
7 |     println!("{}", shout("hello"));  // 리터럴은?
  |                    ----- ^^^^^^^ expected `&String`, found `&str`
  |                    |
  |                    arguments to this function are incorrect
  |
  = note: expected reference `&String`
             found reference `&'static str`
note: function defined here
 --> ex.rs:2:4
  |
2 | fn shout(s: &String) -> String { s.to_uppercase() }
  |    ^^^^^ ----------

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **E0308 `mismatched types`.** `&owned` 는 통과하고 **리터럴만 막힌다.**
- ★★ **역참조 강제는 `String` → `str` 한 방향으로만 돈다.** `&String` → `&str` 은 「들고 있는 것을 보여 주는」 것이라 공짜인데,\
  반대는 **없는 `String` 을 새로 만들어야** 하므로 자동으로 해 줄 수 없다.
- ★ `= note:` 두 줄이 **기대한 타입과 실제 타입을 수명까지 붙여** 찍어 준다 —\
  ``expected reference `&String` `` / ``found reference `&'static str` ``.\
  **리터럴이 `&'static str` 이라는 사실이 여기서 드러난다**([**07번 주제**](../07-const-static-and-const-fn/)).
- `note: function defined here` 가 **시그니처를 짚어 준다** — 고칠 곳이 호출부가 아니라 **시그니처**임을 암시한다.
- **호출부가 억지로 맞추려면** `shout(&String::from("hello"))` 를 써야 한다 —\
  **필요 없던 힙 할당 한 번**을 내는 것이다. 그것이 `&String` 시그니처가 강요하는 대가다.
- ★ 「더 구체적이라 더 안전하다」가 틀린 이유 — **좁혀서 막아 주는 잘못된 호출이 하나도 없다.**\
  `&str` 로 열어도 틀린 값이 들어오지 않는다. **좁힌 결과는 호출부의 불편과 할당뿐**이다.

### 4. ★ 여섯은 통과하고 `shout(owned)` 만 거부된다

**출력** — 먼저 **통과하는 여섯**이다.

```text
===== 소스: ex.rs =====
// 인자를 &str 로 받으면 — 무엇까지 넘어오나
fn shout(s: &str) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    let boxed: Box<str> = owned.clone().into_boxed_str();

    println!("리터럴      {}", shout("hello"));
    println!("&String     {}", shout(&owned));
    println!("as_str()    {}", shout(owned.as_str()));
    println!("&owned[..]  {}", shout(&owned[..]));
    println!("&*owned     {}", shout(&*owned));
    println!("&Box<str>   {}", shout(&boxed));
    println!("&&String    {}", shout(&&owned));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
리터럴      HELLO
&String     HELLO
as_str()    HELLO
&owned[..]  HELLO
&*owned     HELLO
&Box<str>   HELLO
&&String    HELLO
(종료 코드 0)
```

거부되는 것은 **소유값을 그대로 넘긴 한 줄**이다.

```text
===== 소스: ex.rs =====
// &str 도 전부 받아 주지는 않는다 — 소유값을 그대로 넘기면
fn shout(s: &str) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    println!("{}", shout(owned));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:6:26
  |
6 |     println!("{}", shout(owned));
  |                    ----- ^^^^^ expected `&str`, found `String`
  |                    |
  |                    arguments to this function are incorrect
  |
note: function defined here
 --> ex.rs:2:4
  |
2 | fn shout(s: &str) -> String { s.to_uppercase() }
  |    ^^^^^ -------
help: consider borrowing here
  |
6 |     println!("{}", shout(&owned));
  |                          +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **일곱 줄 중 거부는 한 줄**(`shout(owned)`)이고, **E0308** 이다.\
  `help: consider borrowing here` 가 **`&` 한 글자**를 그대로 준다 — 호출부가 낼 비용은 그게 전부다.
- **`&String` 이 들어가는 것은 역참조 강제** 덕이다. `String: Deref<Target = str>` 이 std 에 있고,\
  **함수 인자 자리는 강제 지점**이라 컴파일러가 `&String` → `&str` 로 바꿔 넣는다.
- `&Box<str>` 도 같은 장치다(`Box<T>: Deref<Target = T>` → `Box<str>` 은 `str` 로).
- **두 시그니처를 나란히 두면 이렇다.**

| 넘긴 것 | `fn f(s: &str)` | `fn f(s: &String)` |
|---|---|---|
| `"리터럴"` | ✓ | ✗ **E0308** |
| `&owned`(`&String`) | ✓ (강제) | ✓ |
| `&&owned`(`&&String`) | ✓ (강제) | ✓ (강제) |
| `owned.as_str()` | ✓ | ✗ |
| `&owned[..]` | ✓ | ✗ |
| `&*owned` | ✓ | ✗ |
| `&boxed`(`&Box<str>`) | ✓ (강제) | ✗ |
| `owned`(`String` 통째로) | ✗ **E0308**(`&` 하나) | ✗(〃) |

★★ **`&String` 쪽 ✓ 칸이 여덟 중 셋으로 줄고, 그중에 리터럴이 없다.**
**넓힌 것이 하나도 없다** — 그래서 `&String` 인자는 거의 항상 나쁜 선택이다.

### 5. ★ 넷 다 컴파일된다 — 강제는 **전이적**이다

**출력**

```text
===== 소스: ex.rs =====
// 몇 겹까지 벗기나 — 네 겹을 쌓아 본다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;
    let rrr: &&&String = &rr;
    let rrrr: &&&&String = &rrr;

    println!("&String     -> {}", f(r));
    println!("&&String    -> {}", f(rr));
    println!("&&&String   -> {}", f(rrr));
    println!("&&&&String  -> {}", f(rrrr));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
&String     -> 6
&&String    -> 6
&&&String   -> 6
&&&&String  -> 6
(종료 코드 0)
```

**왜 그런가**

- ★★ **넷 다 통과한다.** 「`&&String` 쯤에서 무너지겠지」는 **틀린 예상**이다.
- 한 낱말로 답하면 **전이적**(transitive)이다. 컴파일러는 목표 타입이 나올 때까지 `Deref` 를 계속 따라간다 —\
  `&&&&String` → `&&&String` → `&&String` → `&String` → `&str`.
- **`rr.as_str()`·`&rr[..]` 도 된다.** 다만 이쪽은 강제가 아니라 **메서드 해석의 자동 역참조**다 —\
  수신자를 `&`·`&mut`·`*` 로 조정해 가며 메서드를 찾는 별개의 규칙인데, **결과가 비슷해 보인다.**

```text
===== 소스: ex.rs =====
// as_str() · &*s · &s[..] 는 각각 어디까지 되나 — 되는 것만 모아 본다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;

    println!("s.as_str()   = {}", f(s.as_str()));
    println!("r.as_str()   = {}", f(r.as_str()));
    println!("rr.as_str()  = {}", f(rr.as_str()));
    println!("&*s          = {}", f(&*s));
    println!("&s[..]       = {}", f(&s[..]));
    println!("&r[..]       = {}", f(&r[..]));
    println!("&rr[..]      = {}", f(&rr[..]));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_str()   = 6
r.as_str()   = 6
rr.as_str()  = 6
&*s          = 6
&s[..]       = 6
&r[..]       = 6
&rr[..]      = 6
(종료 코드 0)
```

- ★ **강제를 막는 것은 겹 수가 아니라 「자리」다.** 자세한 것은 12번 답에 있다 —\
  **트레이트 구현을 찾는 자리**(E0277)와 **함수를 값으로 넘기는 자리**(E0631)에는 강제가 없다.

### 6. ★ 컴파일되지 않는다 — E0382, `a` 만 죽는다

**출력**

```text
===== 소스: ex.rs =====
// + 는 왼쪽을 소비한다 — 뒤에서 a 를 쓰면?
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + &b;
    println!("c = {}", c);
    println!("a = {}", a);
    println!("b = {}", b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `a`
 --> ex.rs:7:24
  |
3 |     let a = String::from("가나");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = String::from("다라");
5 |     let c = a + &b;
  |             - value moved here
6 |     println!("c = {}", c);
7 |     println!("a = {}", a);
  |                        ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
5 |     let c = a.clone() + &b;
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **E0382 `borrow of moved value`.** [**08번 주제**](../08-ownership-and-move/)에서 이미 만난 번호다 —\
  **문자열 전용 규칙이 아니라 이동 규칙이 `+` 에서 나타난 것**이다.
- **`a` 만 죽고 `b` 는 산다.** `+` 의 시그니처가 **왼쪽은 `self`(소유), 오른쪽은 `&str`(빌림)** 이기 때문이다.\
  ★ **왼쪽의 힙 버퍼를 물려받아 거기에 이어 붙이는** 구현이라 소유가 필요하다 — 새 할당을 아끼는 설계다.
- **`a + b` 로 바꾸면 E0308 로 바뀐다.**

```text
===== 소스: ex.rs =====
// + 의 오른쪽에 String 을 그대로 두면
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + b;
    println!("{}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:5:17
  |
5 |     let c = a + b;
  |                 ^ expected `&str`, found `String`
  |
help: consider borrowing here
  |
5 |     let c = a + &b;
  |                 +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

- ★ ``expected `&str` `` 가 **시그니처를 그대로 말해 준다.**
- **`&b`(= `&String`)가 통과하는 것은 5번의 강제**다. 연산자의 피연산자도 강제 지점이다.\
  **`&&b` 도 통과한다** — 전이적이기 때문이다.

```text
===== 소스: ex.rs =====
// + 의 오른쪽에 &&String 을 줘도 통과하나 — 강제는 전이적이다
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + &&b;
    println!("{}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다라
(종료 코드 0)
```

- **`format!` 은 아무것도 안 뺏는다** — 둘 다 빌려만 쓰고 **새 `String` 을 만든다.**

```text
===== 소스: ex.rs =====
// + 는 오른쪽에 &String 을 받아 준다 — 강제가 돌기 때문이다. 그리고 format! 은 아무것도 안 뺏는다
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");

    let plus = a.clone() + &b;              // &String 이 &str 로 강제된다
    let fmt = format!("{}{}", a, b);        // a·b 를 빌려만 쓴다

    println!("plus   = {}", plus);
    println!("fmt    = {}", fmt);
    println!("a 살아 = {} / b 살아 = {}", a, b);
    println!("같은 값인가 = {}", plus == fmt);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
plus   = 가나다라
fmt    = 가나다라
a 살아 = 가나 / b 살아 = 다라
같은 값인가 = true
(종료 코드 0)
```

| 표기 | 왼쪽 | 오른쪽 | 뒤에서 원본을 쓸 수 있나 |
|---|---|---|---|
| `a + &b` | **소비**(이동) | `&str`(강제로 `&String` 도) | `a` ✗ · `b` ✓ |
| `format!("{}{}", a, b)` | 빌림 | 빌림 | **둘 다** ✓ |
| `a.push_str(&b)` | `&mut a` | `&str` | `a` ✓ · `b` ✓ |

### 7. 다섯은 서로 다른 트레이트에서 오고, `&str` 위에서만 결과가 같다

**출력**

```text
===== 소스: ex.rs =====
// &str -> String 다섯 가지 — 어느 트레이트에서 오나, 결과가 같은가
fn main() {
    let lit = "가나다";

    // 트레이트 이름을 직접 써서 부른다 — 통과하면 그 트레이트가 출처다
    let a: String = ToString::to_string(lit);
    let b: String = ToOwned::to_owned(lit);
    let c: String = Into::into(lit);
    let d: String = From::from(lit);
    let e: String = format!("{}", lit);

    println!("to_string    {:?} len={} cap={}", a, a.len(), a.capacity());
    println!("to_owned     {:?} len={} cap={}", b, b.len(), b.capacity());
    println!("into         {:?} len={} cap={}", c, c.len(), c.capacity());
    println!("String::from {:?} len={} cap={}", d, d.len(), d.capacity());
    println!("format!      {:?} len={} cap={}", e, e.len(), e.capacity());

    println!("다섯이 같은 값인가: {}", a == b && b == c && c == d && d == e);
    println!("힙 주소가 같은가  : {}", a.as_ptr() == b.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
to_string    "가나다" len=9 cap=9
to_owned     "가나다" len=9 cap=9
into         "가나다" len=9 cap=9
String::from "가나다" len=9 cap=9
format!      "가나다" len=9 cap=9
다섯이 같은 값인가: true
힙 주소가 같은가  : false
(종료 코드 0)
```

**왜 그런가**

- ★ **트레이트 이름을 직접 써서 불러도 전부 통과했다** — 그것이 출처의 실증이다.

| 표기 | 트레이트 | 무엇을 요구하나 |
|---|---|---|
| `x.to_string()` | **`ToString`** | `T: Display` 포괄 구현. `str` 도 `Display` 라 여기에 걸린다 |
| `x.to_owned()` | **`ToOwned`** | `str` 의 `Owned` 가 `String` 이라고 정해져 있다 |
| `x.into()` | **`Into<String>`** | `String: From<&str>` 에서 자동으로 따라온다 |
| `String::from(x)` | **`From<&str>`** | 가장 직접적인 표기 |
| `format!("{}", x)` | **매크로** | 포매팅 기계(`Display`)를 태운다 |

- **값은 다섯이 같고 힙 주소는 전부 다르다** — **다섯 번 따로 할당**했다. 변환은 공짜가 아니다.
- ★★ **`&str` 이 아닌 것을 던지면 갈린다.**

```text
===== 소스: ex.rs =====
// 다섯 변환이 같은 물건이 아니라는 증거 — &str 이 아닌 것을 던져 본다
fn main() {
    let n = 42i32;
    let a: String = n.to_owned();      // ToOwned 는 String 을 안 준다
    let b: String = String::from(n);   // From<i32> for String 이 있나
    println!("{} {}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:4:21
  |
4 |     let a: String = n.to_owned();      // ToOwned 는 String 을 안 준다
  |            ------   ^^^^^^^^^^^^ expected `String`, found `i32`
  |            |
  |            expected due to this
  |
help: try using a conversion method
  |
4 |     let a: String = n.to_owned().to_string();      // ToOwned 는 String 을 안 준다
  |                                 ++++++++++++

error[E0277]: the trait bound `String: From<i32>` is not satisfied
 --> ex.rs:5:21
  |
5 |     let b: String = String::from(n);   // From<i32> for String 이 있나
  |                     ^^^^^^ the trait `From<i32>` is not implemented for `String`
  |
  = help: the following other types implement trait `From<T>`:
            `String` implements `From<&String>`
            `String` implements `From<&mut str>`
            `String` implements `From<&str>`
            `String` implements `From<Box<str>>`
            `String` implements `From<Cow<'_, str>>`
            `String` implements `From<char>`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0277, E0308.
For more information about an error, try `rustc --explain E0277`.
```

- **`42i32.to_owned()` 의 타입은 `i32`** 다. `ToOwned` 는 「빌린 것을 소유값으로」이고 `i32` 는 이미 소유값이다.\
  **`to_owned()` 가 `String` 을 주는 것은 `&str` 일 때뿐**이다.
- **`String::from(42)` 은 없다.** `= help:` 가 **`String` 이 받는 `From` 구현 목록을 통째로** 찍어 준다 —\
  `&String`·`&mut str`·`&str`·`Box<str>`·`Cow<'_, str>`·`char`. **문서를 안 열고도 목록이 나온다.**
- ★★ **「어느 것이 더 느린가」는 이 문서가 안 쟀다.** 근거로 댈 수 있는 것과 없는 것을 가른다.
  - **댈 수 있는 것** — `format!` 만 **포매팅 기계를 통과**한다(다른 넷은 바이트를 베끼는 경로다).\
    다섯 다 **할당을 한 번씩 한다**(주소가 서로 다름).
  - **댈 수 없는 것** — **시간**. 재지 않았으므로 「`format!` 이 N배 느리다」 같은 문장을 적지 않는다.\
    ★ 실제 비용은 벤치로 재야 하고, **여기서는 안 쟀다.**

### 8. `String` 은 E0382, `&str` 은 통과 — 갈리는 것은 `Copy` 하나다

**출력**

```text
===== 소스: ex.rs =====
// 타입만 바꾼 같은 코드 — 한쪽은 거부되고 한쪽은 통과한다
fn main() {
    let a: String = String::from("가나");
    let b = a;
    println!("a={} b={}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `a`
 --> ex.rs:5:27
  |
3 |     let a: String = String::from("가나");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = a;
  |             - value moved here
5 |     println!("a={} b={}", a, b);
  |                           ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
4 |     let b = a.clone();
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

같은 코드에서 **타입만** 바꾼다.

```text
===== 소스: ex.rs =====
// 같은 코드에서 타입만 &str 로 바꾼다
fn main() {
    let a: &str = "가나";
    let b = a;
    println!("a={} b={}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a=가나 b=가나
(종료 코드 0)
```

**왜 그런가**

- **거부되는 쪽은 `String`**, 번호는 **E0382**. 이유 구절은 에러가 직접 말한다 —\
  ``move occurs because `a` has type `String`, which does not implement the `Copy` trait``.
- **`String` 이 `Copy` 가 아닌 것은 힙을 소유하기 때문**이다. 두 이름이 같은 버퍼를 들고 있다가\
  둘 다 해제하면 이중 해제가 된다 — 그래서 언어가 **이름 하나만 남긴다.**
- **`&str` 은 `Copy`** 다(불변 참조). 두 칸을 베끼면 끝이고 해제할 것이 없다.

| | `Copy` 인가 | 대입하면 |
|---|---|---|
| `String` | **아니오** | 이동(E0382) |
| `&str` | **예** | 복사 |
| `&String` | **예** | 복사 |
| `&mut String` | **아니오** | 이동 |

- ★ **판정 규칙의 정본은 [**09번 주제**](../09-copy-clone-and-drop/)** 다 — `Copy` 를 붙일 수 있는 조건,\
  `Copy` 와 `Drop` 이 함께 못 오는 것, `&mut T` 가 `Copy` 가 아닌 것이 전부 거기 있다.

### 9. `len()` 은 **바이트 수**다 — `"가나다"` 가 9다

**출력**

```text
===== 소스: ex.rs =====
// len() 은 무엇을 세나 — 한글로 던진다
fn main() {
    let s = String::from("가나다");
    println!("\"가나다\".len()            = {}", s.len());
    println!("\"가나다\".chars().count()  = {}", s.chars().count());
    println!("\"abc\".len()              = {}", "abc".len());
    println!("\"가나다\".is_empty()       = {}", s.is_empty());
    println!("바이트  = {:?}", s.as_bytes());
    println!("size_of::<char>()        = {}", std::mem::size_of::<char>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
"가나다".len()            = 9
"가나다".chars().count()  = 3
"abc".len()              = 3
"가나다".is_empty()       = false
바이트  = [234, 176, 128, 235, 130, 152, 235, 139, 164]
size_of::<char>()        = 4
(종료 코드 0)
```

**왜 그런가**

- **`len()` 은 UTF-8 바이트 수**다. 한글 한 글자가 3바이트라 `"가나다"` 가 **9**, `chars().count()` 가 **3**이다.\
  `as_bytes()` 가 그 아홉 바이트를 그대로 보여 준다.
- ★★ **`"abc".len()` 이 3이라는 것이 위험하다.** ASCII 로만 테스트하면 「글자 수」로 읽어도 **맞아 보인다.**\
  **한글·이모지로 던져야** 드러난다 — 이 오해가 오래 사는 이유다.
- ★ **`chars().count()` 도 「사람이 보는 글자 수」가 아니다.** `chars()` 가 주는 것은 **유니코드 스칼라 값**이라\
  결합 문자(`e` + 악센트)나 일부 이모지에서 또 갈린다. `size_of::<char>()` 가 **4**인 것이 그 단서다 —\
  `char` 는 **스칼라 값 하나**를 담는 것이지 「사람이 보는 글자」가 아니다.
- **UTF-8 경계·`chars()`/`bytes()`/`char_indices()`·바이트 인덱스 슬라이싱 패닉의 정본은
  [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)** 다. 여기서는 맛만 본다.

### 10. `cap=0` / `len=0` / `0→8→16→32`(구현 세부)

**출력**

```text
===== 소스: ex.rs =====
// len 과 capacity 는 다른 것이다 — 세 가지 만드는 법으로 찍어 본다
fn main() {
    let a = String::new();
    let b = String::with_capacity(16);
    let c = String::from("가나다");

    println!("String::new()            len={} cap={}", a.len(), a.capacity());
    println!("String::with_capacity(16) len={} cap={}", b.len(), b.capacity());
    println!("String::from(\"가나다\")    len={} cap={}", c.len(), c.capacity());

    // 용량 안에서 늘리면 용량이 안 바뀐다
    let mut d = String::with_capacity(16);
    d.push_str("abc");
    println!("with_capacity(16) 뒤 push_str(\"abc\") len={} cap={}", d.len(), d.capacity());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
String::new()            len=0 cap=0
String::with_capacity(16) len=0 cap=16
String::from("가나다")    len=9 cap=9
with_capacity(16) 뒤 push_str("abc") len=3 cap=16
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// push_str 로 늘리면 capacity 가 어떻게 변하나 — ★ 이것은 구현 세부다
fn main() {
    let mut s = String::new();
    println!("시작           len={} cap={}", s.len(), s.capacity());
    for i in 0..10 {
        s.push_str("ab");
        println!("push_str {:>2}번째 len={} cap={}", i + 1, s.len(), s.capacity());
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
시작           len=0 cap=0
push_str  1번째 len=2 cap=8
push_str  2번째 len=4 cap=8
push_str  3번째 len=6 cap=8
push_str  4번째 len=8 cap=8
push_str  5번째 len=10 cap=16
push_str  6번째 len=12 cap=16
push_str  7번째 len=14 cap=16
push_str  8번째 len=16 cap=16
push_str  9번째 len=18 cap=32
push_str 10번째 len=20 cap=32
(종료 코드 0)
```

**왜 그런가**

- **`String::new()` 는 `len=0 cap=0`** — **힙을 아예 안 잡는다.** 빈 문자열을 만드는 데 할당이 없다.
- **`with_capacity(16)` 직후의 `len` 은 0** 이다. 미리 **자리만** 잡아 둔 것이지 내용이 생긴 게 아니다.\
  그 뒤 `push_str("abc")` 를 해도 **`cap` 이 16 그대로**다 — 재할당이 없었다는 뜻이다.
- **수열은 `0 → 8 → 16 → 32`** 였다. ★★ **이것을 본문에 사실로 적으면 안 된다.**\
  **std 의 구현 세부**이고 판이 바뀌면 달라질 수 있다. 보장되는 것은\
  **`capacity() >= len()`** 과 **`with_capacity(n)` 이 최소 `n` 을 확보한다**는 정도다.\
  ★ 숫자가 깔끔하게 두 배씩 늘어 **규칙처럼 보이는 것**이 함정이다 — **보이는 규칙성은 보장의 근거가 아니다.**\
  재할당의 상각 분석은 [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.
- **`&str` 에는 늘리는 메서드가 없다.**

```text
===== 소스: ex.rs =====
// &str 은 늘릴 수 없다 — 소유자가 아니기 때문이다
fn main() {
    let mut s: &str = "가나";
    s.push_str("다");
    println!("{}", s);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `push_str` found for reference `&str` in the current scope
 --> ex.rs:4:7
  |
4 |     s.push_str("다");
  |       ^^^^^^^^ method not found in `&str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`mut` 을 붙여도 안 된다.** `mut s: &str` 은 「**`s` 라는 창을 다른 데로 옮길 수 있다**」는 뜻이지
「창 너머의 바이트를 고칠 수 있다」가 아니다. 늘리려면 **소유자**(`String`)가 있어야 한다.

### 11. 리터럴은 바이너리 안에 산다 — `&'static str`

**출력**

```text
===== 소스: ex.rs =====
// 리터럴은 어디에 사나 — 프로그램이 끝날 때까지 사는 &'static str 이다
const GREET: &str = "안녕";              // 07번: &'static str 로 추론된다

fn literal() -> &'static str { "안녕" }  // 지역이 아니라 바이너리 안의 것을 돌려준다

fn main() {
    let a: &'static str = "안녕";
    let b = literal();

    // 같은 글자의 리터럴 둘이 같은 자리를 가리키나 (★ 구현 세부)
    println!("a 와 b 가 같은 자리 : {}", a.as_ptr() == b.as_ptr());
    println!("a 와 GREET 가 같은 자리 : {}", a.as_ptr() == GREET.as_ptr());

    // String 으로 만들면 힙에 새로 복사된다
    let owned = String::from(a);
    println!("String::from(a) 가 같은 자리 : {}", owned.as_ptr() == a.as_ptr());
    println!("값은 같은가 : {}", owned == a);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a 와 b 가 같은 자리 : true
a 와 GREET 가 같은 자리 : true
String::from(a) 가 같은 자리 : false
값은 같은가 : true
(종료 코드 0)
```

**왜 그런가**

- **`"안녕"` 의 타입은 `&'static str`** 이다. 바이트가 **바이너리의 읽기 전용 영역에 박혀** 있어\
  프로그램이 끝날 때까지 산다 — 그래서 함수에서 그대로 돌려줄 수 있다.
- ★★ **같은 글자 리터럴 셋이 한 자리를 가리킨 것은 구현 세부다.** rustc 가 합쳐 준 것이고 **보장이 아니다** —\
  「주소가 같으니 같은 리터럴」 같은 판정을 하면 안 된다([**07번 주제**](../07-const-static-and-const-fn/)의 `const` 주소 이야기와 같은 계열).
- **지역 `String` 의 창은 밖으로 못 나간다.**

```text
===== 소스: ex.rs =====
// &str 은 남의 바이트를 보는 창이다 — 주인이 죽으면 창도 못 나간다
fn make_view() -> &'static str {
    let s = String::from("가나다");
    &s[..]
}

fn main() { println!("{}", make_view()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0515]: cannot return value referencing local variable `s`
 --> ex.rs:4:5
  |
4 |     &s[..]
  |     ^-^^^^
  |     ||
  |     |`s` is borrowed here
  |     returns a value referencing data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

- ★★ **「왜 대칭이 아닌가」의 두 줄 답.**
  1. **`String` → `&str` 은 이미 있는 힙 버퍼의 주소와 길이를 읽어 두 칸을 만드는 것**이라 할당도 복사도 없다.
  2. **`&str` → `String` 은 주인을 새로 만드는 것**이라 **할당 한 번 + `len` 바이트 복사**가 필요하다.
- 덤으로 **방향에 따라 제약도 다르다** — `&str` 은 주인이 사는 동안만 유효하고(E0515),\
  `String` 은 자기가 주인이라 어디든 나갈 수 있다.
- **`'static` 의 두 뜻**(`&'static T` 와 `T: 'static`)은 [**12번 주제**](../12-lifetime-annotations-and-elision/)가 정본이고,\
  `'static` 심화와 구조체 필드 설계는 [**13번 주제**](../13-struct-references-and-static/)다.

### 12. 강제는 「넣는 자리」에서만 돈다 — E0277 과 E0631

**출력** — 먼저 **비교 연산자**다.

```text
===== 소스: ex.rs =====
// 강제가 도는 자리와 안 도는 자리 — 인자 자리는 되고 트레이트 경계 자리는 안 된다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;

    println!("인자 자리 f(rr)   = {}", f(rr));   // 강제가 돈다
    println!("주석 자리         = {}", { let a: &str = rr; a });
    println!("비교 r == \"가나\"  = {}", r == "가나");
    println!("비교 rr == \"가나\" = {}", rr == "가나");   // ★ 여기서 무너진다
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: can't compare `&String` with `str`
  --> ex.rs:12:41
   |
12 |     println!("비교 rr == \"가나\" = {}", rr == "가나");   // ★ 여기서 무너진다
   |                                             ^^ no implementation for `&String == str`
   |
   = help: the trait `PartialEq<str>` is not implemented for `&String`
   = note: required for `&&String` to implement `PartialEq<&str>`
help: consider dereferencing here
   |
12 |     println!("비교 rr == \"가나\" = {}", *rr == "가나");   // ★ 여기서 무너진다
   |                                          +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

그리고 **함수를 값으로 넘기는 자리**다.

```text
===== 소스: ex.rs =====
// 강제는 「호출 자리」에서만 돈다 — 함수를 값으로 넘기면?
fn takes_str(s: &str) -> usize { s.len() }

fn main() {
    let v = vec![String::from("가나")];
    let n: usize = v.iter().map(takes_str).sum();
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0631]: type mismatch in function arguments
 --> ex.rs:6:33
  |
2 | fn takes_str(s: &str) -> usize { s.len() }
  | ------------------------------ found signature defined here
...
6 |     let n: usize = v.iter().map(takes_str).sum();
  |                             --- ^^^^^^^^^ expected due to this
  |                             |
  |                             required by a bound introduced by this call
  |
  = note: expected function signature `fn(&String) -> _`
             found function signature `fn(&str) -> _`
note: required by a bound in `map`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:773:5
help: consider wrapping the function in a closure
  |
6 |     let n: usize = v.iter().map(|arg0: &String| takes_str(/* &str */)).sum();
  |                                 +++++++++++++++          ++++++++++++

error[E0599]: the method `sum` exists for struct `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>`, but its trait bounds were not satisfied
 --> ex.rs:6:44
  |
6 |     let n: usize = v.iter().map(takes_str).sum();
  |                                            ^^^ method cannot be called due to unsatisfied trait bounds
  |
  = note: the following trait bounds were not satisfied:
          `<for<'a> fn(&'a str) -> usize {takes_str} as FnOnce<(&String,)>>::Output = _`
          which is required by `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          `for<'a> fn(&'a str) -> usize {takes_str}: FnMut<(&String,)>`
          which is required by `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          which is required by `&mut Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0599, E0631.
For more information about an error, try `rustc --explain E0599`.
```

**왜 그런가**

- **`r == "가나"`(`&String` vs `&str`)는 통과한다** — std 가 `String: PartialEq<str>` 을 구현해 뒀기 때문이다.\
  **강제가 해 준 일이 아니라 구현이 있어서 되는 것**이다.
- **`rr`(`&&String`)에서 E0277** 이다. `= note:` 가 사슬을 보여 준다 —\
  「`&&String` 이 `PartialEq<&str>` 이려면 `&String: PartialEq<str>` 이 필요한데 없다」.\
  여기는 **넣는 자리가 아니라 구현을 찾는 자리**라 강제가 안 돈다. `help:` 는 `*rr` 로 한 겹 벗기라고 한다.
- **`map(takes_str)` 은 E0631.** `f(x)` 라고 쓰면 **그 호출 자리**에서 강제가 돌지만,\
  `map(f)` 는 **함수를 값으로 넘기는 것**이라 호출 자리가 없다.\
  `= note:` 가 `expected fn(&String) -> _` / `found fn(&str) -> _` 로 **두 시그니처를 나란히** 찍어 준다.
- ★ **E0599 는 덤으로 따라온 것**이다 — `map` 이 실패했으니 그 결과가 `Iterator` 가 아니고, 그러니 `sum` 도 없다.\
  12번 주제에서 본 「**에러 하나가 다음 에러를 만든다**」와 같은 모양이다. **위에서부터 고친다.**
- **처방** — `help:` 대로 클로저로 감싸면 **그 안이 다시 호출 자리**가 되어 강제가 돈다.

```text
===== 소스: ex.rs =====
// 처방 — 클로저로 감싸면 그 안이 다시 「호출 자리」가 된다
fn takes_str(s: &str) -> usize { s.len() }

fn main() {
    let v = vec![String::from("가나"), String::from("다")];
    let n: usize = v.iter().map(|s| takes_str(s)).sum();
    println!("합계 = {}", n);

    // as_str() 로 미리 &str 을 만들어 줘도 된다
    let m: usize = v.iter().map(String::as_str).map(takes_str).sum();
    println!("합계 = {}", m);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
합계 = 9
합계 = 9
(종료 코드 0)
```

- ★★ **한 문장 기준** — 「**무엇을 넣는 자리**에서는 돌고, **무엇이 무엇인지 판정하는 자리**에서는 안 돈다.」

```text
   돈다    — 함수 「호출」의 인자          f(rr)
   돈다    — 타입 주석이 붙은 let          let a: &str = rr;
   돈다    — 메서드 수신자 자동 역참조     rr.as_str()      (별개 규칙이지만 결과가 비슷하다)
   돈다    — 연산자의 피연산자             a + &b
   ─────────────────────────────────────────────────────────────
   안 돈다 — 트레이트 구현을 찾는 자리     rr == "가나"      E0277
   안 돈다 — 함수를 「값으로」 넘기는 자리  map(takes_str)    E0631
```

- 인자를 더 넓게 여는 **`impl AsRef<str>`·`impl Into<String>` 의 정본은 목록의 29번 주제**다.\
  여기서는 이름만 적는다 — **`&str` 로 받는 것이 기본값**이고, 더 열지 말지는 거기서 판단한다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `size_of` 전수(13종) | `String` 24 · `&str` 16 · `&String` 8 · `&&String` 8 · `Box<str>` 16 · `char` 4 · `usize` 8 | 1 |
| ★ `as_ptr()` 네 표기 + `clone` | **앞의 넷이 같은 주소, `clone` 만 다른 주소**(주소 절댓값은 흔들림) | 2 |
| ★ 같은 실험을 `assert_eq!`/`assert_ne!` 로 | **결정적 출력** — 재대조가 기계적으로 통과 | 2 |
| `&s[..3]` · `&s[3..]` 오프셋 | **오프셋 0 / 3**, 같은 힙 버퍼(`true`) — 할당 없음 | 2 |
| ★ `fn f(s: &String)` 에 리터럴 | **E0308** + `= note:` 가 `&'static str` 을 찍음 | 3 |
| `fn f(s: &str)` 에 일곱 꼴 | **여섯 통과**(리터럴·`&String`·`as_str`·`&s[..]`·`&*s`·`&Box<str>`·`&&String`) | 4 |
| `fn f(s: &str)` 에 `String` 통째로 | **E0308** + `help: consider borrowing here` | 4 |
| ★ `&`·`&&`·`&&&`·`&&&&String` 을 `&str` 자리에 | **넷 다 통과** — 강제는 **전이적** | 5 |
| `as_str()`·`&*s`·`&s[..]` 를 겹친 참조 위에서 | **일곱 줄 전부 통과** | 5 |
| `let c = a + &b;` 뒤 `a` | **E0382** — `+` 가 왼쪽을 소비 | 6 |
| `a + b` | **E0308** `expected &str` | 6 |
| `a + &&b` | **통과** — `가나다라` | 6 |
| `format!("{}{}", a, b)` | **통과** — `a`·`b` 둘 다 살아 있음 | 6 |
| 다섯 변환(`ToString`/`ToOwned`/`Into`/`From`/`format!`) | **값 같음 · 힙 주소 전부 다름** · 트레이트 직접 호출도 통과 | 7 |
| ★ `42i32.to_owned()` · `String::from(42)` | **E0308**(`i32` 가 나옴) + **E0277**(`From` 구현 목록 6개) | 7 |
| `let b = a;` 뒤 `a` — `String` / `&str` | **E0382** / **통과**(`a=가나 b=가나`) | 8 |
| `"가나다"` 의 `len` / `chars().count()` | **9** / **3** · `as_bytes()` 9개 · `size_of::<char>()` **4** | 9 |
| `String::new` / `with_capacity(16)` / `from` | `cap=0` / `cap=16 len=0` / `len=9 cap=9` | 10 |
| ★ `push_str("ab")` × 10 | `cap` **0→8→16→32** — **구현 세부** | 10 |
| `&str` 에 `push_str` | **E0599** `method not found in &str` | 10 |
| 리터럴 주소 대조(`a`·`literal()`·`GREET`) | **셋 다 같은 자리**(★ 구현 세부) · `String::from` 만 다름 | 11 |
| 지역 `String` 의 `&s[..]` 반환 | **E0515** | 11 |
| ★ `&&String == &str` | **E0277** — 트레이트 찾는 자리엔 강제가 없다 | 12 |
| ★ `map(takes_str)` on `Iter<String>` | **E0631** + **E0599**(덤) | 12 |
| 클로저로 감싼 판 · `map(String::as_str)` | **통과** — `합계 = 9` 두 번 | 12 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **크기 숫자 전부**(24·16·8) | **플랫폼의 포인터 폭**. `x86_64` 라 8이다 — 32비트 대상에서는 달라진다 |
| ★ **주소 절댓값** | **런타임·OS**(ASLR·할당기 상태). 근거로 읽을 것은 **같다/다르다**뿐 |
| ★ **`capacity` 증가 수열** `0→8→16→32` | **std 구현 세부**. 보장은 `capacity() >= len()` 과 `with_capacity(n)` 뿐 |
| ★ **같은 글자 리터럴이 한 자리를 쓰는 것** | **rustc 구현 세부**. 합쳐 준 것이지 보장이 아니다 |
| `format!` 의 결과 `cap` 이 `len` 과 같았던 것 | **std 구현 세부**. 포매팅 버퍼의 성장 전략에 달렸다 |
| **에러 번호·`help:` 문구** | **rustc 구현**. 번호는 안정적이고 문구는 판마다 바뀐다 |
| `= help:` 의 **`From` 구현 목록** | **std 의 사실** + **rustc 의 표기**(몇 개까지 보여 줄지는 진단 쪽이다) |
| `note: required by a bound in map` 의 **경로** | **이 툴체인의 커밋 해시**가 경로에 박힌다 |
| **강제가 전이적인 것 · 호출 자리에서만 도는 것** | **언어 보장.** Reference 의 Type coercions 와 실측이 일치했다 |
| **`String`/`&str` 의 `Copy` 여부 · `len()` 이 바이트인 것 · `+` 의 시그니처** | **전부 언어·std 보장** |
