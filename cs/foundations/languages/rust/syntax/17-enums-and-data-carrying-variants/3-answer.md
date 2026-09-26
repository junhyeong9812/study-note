# rust/syntax/17 — 열거형과 데이터를 담는 변형 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.\
> ★ 크기·배치 값은 **어느 것이 보장이고 어느 것이 이 판의 관찰인지** 3번 답에 표로 갈라 두었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 거부된다 — E0559 `variant has no field named`

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 불가능한 상태 — 후. 열거형으로 바꾸면 그 모순을 「적을 수가 없다」
#[derive(Debug)]
enum Conn {
    Idle,
    Connected { session_id: u32 },
    Failed(String),
}

fn report(c: &Conn) -> String {
    match c {
        Conn::Idle => String::from("대기"),
        Conn::Connected { session_id } => format!("연결됨 세션={}", session_id),
        Conn::Failed(e) => format!("실패 {}", e),
    }
}

fn main() {
    println!("{}", report(&Conn::Idle));
    println!("{}", report(&Conn::Connected { session_id: 7 }));
    println!("{}", report(&Conn::Failed(String::from("타임아웃"))));
    // ★ 앞 판의 모순을 그대로 적어 본다 — 연결됐는데 세션이 없고 에러도 있는 상태
    let bad = Conn::Connected { session_id: 7, error: String::from("타임아웃") };
    println!("{:?}", bad);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0559]: variant `Conn::Connected` has no field named `error`
  --> ex.rs:23:48
   |
23 |     let bad = Conn::Connected { session_id: 7, error: String::from("타임아웃") };
   |                                                ^^^^^ `Conn::Connected` does not have this field
   |
   = note: all struct fields are already assigned

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0559`.
(종료 코드 1)
```

**왜 그런가**

- **E0559**, 제목은 `` variant `Conn::Connected` has no field named `error` `` 다.
- `= note: all struct fields are already assigned` — **세 칸짜리가 아니라 한 칸짜리 변형**이라
  `session_id` 를 주는 순간 「이미 다 채웠다」가 된다. 남은 `error` 는 **줄 자리가 없다.**
- 앞선 세 `report` 호출은 **선언에 있는 모양대로** 적었으니 문제가 없다.
  `Conn::Idle`(단위) · `Conn::Connected { session_id }`(구조체) · `Conn::Failed(String)`(튜플)이 전부 다른 형태다.

**같은 모순을 구조체 + 플래그로 적으면 컴파일러는 아무 말도 안 한다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 불가능한 상태 — 전. 구조체 + 플래그로 표현하면 모순된 상태가 「만들어진다」
#[derive(Debug)]
struct Conn {
    connected: bool,
    session_id: Option<u32>,
    error: Option<String>,
}

fn report(c: &Conn) -> String {
    if c.connected {
        format!("연결됨 세션={:?}", c.session_id)
    } else if let Some(e) = &c.error {
        format!("실패 {}", e)
    } else {
        String::from("대기")
    }
}

fn main() {
    let ok = Conn { connected: true, session_id: Some(7), error: None };
    // ★ 모순 — 연결됐다면서 세션이 없고, 동시에 에러까지 있다
    let bad = Conn { connected: true, session_id: None, error: Some(String::from("타임아웃")) };
    println!("{}", report(&ok));
    println!("{}", report(&bad));
    println!("{:?}", bad);
    // 2^1 * 2 * 2 = 표현 가능한 조합
    println!("이 타입이 표현할 수 있는 모순 조합이 컴파일러에게 막히나: 아니오");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
연결됨 세션=Some(7)
연결됨 세션=None
Conn { connected: true, session_id: None, error: Some("타임아웃") }
이 타입이 표현할 수 있는 모순 조합이 컴파일러에게 막히나: 아니오
(종료 코드 0)
```

- ★★ 이것이 이 주제의 요점이다. `connected: true` 인데 `session_id: None` 이고 `error: Some(..)` 인 값이
  **에러도 경고도 없이 만들어지고**, `report` 가 그것을 「연결됨 세션=None」으로 **조용히** 읽는다.
- **가짓수** — 전 판은 `bool` 2가지 × `Option<u32>`(있음/없음) 2가지 × `Option<String>` 2가지로
  **여덟 갈래**이고 그중 절반 이상이 말이 안 된다. 후 판은 **세 갈래**이고 전부 말이 된다.
- ★ 열거형으로 바꾼 이득은 「실수를 덜 한다」가 아니라 **「그 실수를 적을 수가 없다」** 다.

### 2. ★★ 거부된다 — E0605 가 **두 번**. 판정은 열거형 전체에 걸린다

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 데이터를 담은 변형이 하나라도 있으면 `as` 로 정수를 못 꺼낸다
enum Mixed {
    Zero,
    One(u32),
}

fn main() {
    println!("{}", Mixed::Zero as i32);
    let m = Mixed::One(7);
    println!("{}", m as i32);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0605]: non-primitive cast: `Mixed` as `i32`
 --> ex.rs:9:20
  |
9 |     println!("{}", Mixed::Zero as i32);
  |                    ^^^^^^^^^^^^^^^^^^ an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less
  |
  = note: see https://doc.rust-lang.org/reference/items/enumerations.html#casting for more information

error[E0605]: non-primitive cast: `Mixed` as `i32`
  --> ex.rs:11:20
   |
11 |     println!("{}", m as i32);
   |                    ^^^^^^^^ an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less
   |
   = note: see https://doc.rust-lang.org/reference/items/enumerations.html#casting for more information

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0605`.
(종료 코드 1)
```

**왜 그런가**

- **E0605** `non-primitive cast` 가 **두 줄에서 각각** 난다 — `Mixed::Zero as i32` 와 `m as i32`.
- ★★ **짐이 없는 `Mixed::Zero` 에서도 막힌다.** 판정은 **변형 하나가 아니라 열거형 전체**에 대해 내려진다.
  진단이 그 규칙을 그대로 적는다 —
  ``an `as` expression can be used to convert enum types to numeric types only if the enum type is unit-only or field-less``.
- 두 낱말의 뜻 — **`unit-only`** 는 모든 변형이 단위 변형인 것, **`field-less`** 는 어느 변형에도 칸이 없는 것이다.
  `One(u32)` 하나가 둘 다 깨뜨린다.
- `= note:` 는 Reference 의 casting 절 링크다 — **에러의 원인이 아니라 읽을 곳 안내**다.

**판별값까지 적으면 선언 자체가 막힌다 — E0732 가 추가된다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 판별값을 직접 적으면서 데이터 변형을 두면 선언 자체가 막힌다
enum Mixed {
    Zero = 0,
    One(u32),
}

fn main() {
    let _ = Mixed::Zero;
    let _ = Mixed::One(7);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0732]: `#[repr(inttype)]` must be specified for enums with explicit discriminants and non-unit variants
 --> ex.rs:3:1
  |
3 | enum Mixed {
  | ^^^^^^^^^^
4 |     Zero = 0,
  |            - explicit discriminant specified here
5 |     One(u32),
  |     --- non-unit discriminant declared here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0732`.
(종료 코드 1)
```

- **E0732** — 제목은 `` `#[repr(inttype)]` must be specified for enums with explicit discriminants and non-unit variants `` 다.
  진단이 `explicit discriminant specified here` 와 `non-unit discriminant declared here` 로 **두 자리를 같이 짚는다.**
- ★ `#[repr(u8)]` 을 붙이면 **선언은 통과한다.** 그래도 **`as` 는 여전히 E0605** 다 —
  두 규칙은 서로 다른 것을 본다(선언의 표현 대 캐스팅의 자격).

### 3. ★★ 크기가 같은 것 여덟 · 느는 것 넷 — 니치가 있느냐로 갈린다

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 니치 최적화 — Option 을 씌워도 크기가 안 느는 타입들
use std::num::NonZeroU32;

#[derive(Debug)]
enum Never2 { A(u32), B(u32) }          // 데이터 변형 둘 — 태그가 따로 필요하다

fn row(name: &str, bare: usize, opt: usize) {
    println!("{:<22} {:>3} {:>3}  {}", name, bare, opt,
             if bare == opt { "니치 씀" } else { "태그 따로" });
}

fn main() {
    println!("{:<22} {:>3} {:>3}", "타입", "T", "Option<T>");
    row("Box<i32>",      size_of::<Box<i32>>(),      size_of::<Option<Box<i32>>>());
    row("&i32",          size_of::<&i32>(),          size_of::<Option<&i32>>());
    row("&mut i32",      size_of::<&mut i32>(),      size_of::<Option<&mut i32>>());
    row("String",        size_of::<String>(),        size_of::<Option<String>>());
    row("Vec<u8>",       size_of::<Vec<u8>>(),       size_of::<Option<Vec<u8>>>());
    row("NonZeroU32",    size_of::<NonZeroU32>(),    size_of::<Option<NonZeroU32>>());
    row("char",          size_of::<char>(),          size_of::<Option<char>>());
    row("bool",          size_of::<bool>(),          size_of::<Option<bool>>());
    row("u8",            size_of::<u8>(),            size_of::<Option<u8>>());
    row("u32",           size_of::<u32>(),           size_of::<Option<u32>>());
    row("f64",           size_of::<f64>(),           size_of::<Option<f64>>());
    row("()",            size_of::<()>(),            size_of::<Option<()>>());
    row("Never2",        size_of::<Never2>(),        size_of::<Option<Never2>>());
    let get = |e: &Never2| match e { Never2::A(n) | Never2::B(n) => *n };
    let (a, b) = (Never2::A(1), Never2::B(2));
    println!("{:?}={} {:?}={}", a, get(&a), b, get(&b));
    // 니치가 겹겹이 쌓인다
    println!("Option<Option<bool>> {}  Option<Option<Option<bool>>> {}",
             size_of::<Option<Option<bool>>>(), size_of::<Option<Option<Option<bool>>>>());
    println!("Result<Box<i32>, ()> {}  Result<u32, u32> {}",
             size_of::<Result<Box<i32>, ()>>(), size_of::<Result<u32, u32>>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
타입                       T Option<T>
Box<i32>                 8   8  니치 씀
&i32                     8   8  니치 씀
&mut i32                 8   8  니치 씀
String                  24  24  니치 씀
Vec<u8>                 24  24  니치 씀
NonZeroU32               4   4  니치 씀
char                     4   4  니치 씀
bool                     1   1  니치 씀
u8                       1   2  태그 따로
u32                      4   8  태그 따로
f64                      8  16  태그 따로
()                       0   1  태그 따로
Never2                   8   8  니치 씀
A(1)=1 B(2)=2
Option<Option<bool>> 1  Option<Option<Option<bool>>> 1
Result<Box<i32>, ()> 8  Result<u32, u32> 8
(종료 코드 0)
```

**왜 그런가**

- **크기가 같은 것** — `Box<i32>` · `&i32` · `&mut i32` · `String` · `Vec<u8>` · `NonZeroU32` · `char` · `bool` · `Never2`.
  전부 **자기가 절대 안 쓰는 비트 패턴(니치)** 이 있다. 널이 못 되고, 0이 못 되고, 유효 범위가 좁다.
- **크기가 느는 것** — `u8`(1→2) · `u32`(4→8) · `f64`(8→16) · `()`(0→1).
  ★ 공통점은 **표현 가능한 모든 비트 패턴을 이미 쓰고 있다**는 것이다. 남는 무늬가 없으니 **태그를 따로** 둔다.
  느는 폭이 1바이트가 아니라 정렬 단위인 것은 **태그 뒤에 패딩**이 붙기 때문이다.
- **`Option<()>` 은 1바이트** — `()` 는 0바이트라 담을 자리가 아예 없다. 구별할 것이 둘이면 **자리를 새로 만든다.**
- **`Option<Option<Option<bool>>>` 은 1바이트** — `bool` 이 남긴 254가지 무늬를 한 겹씩 가져다 쓴다. 니치는 겹겹이 쌓인다.

★★ **어느 행이 보장이고 어느 행이 관찰인가.**

| 행 | 성격 |
|---|---|
| `Box<i32>` · `&i32` · `&mut i32` — `Option<T>` 가 같은 크기 | ★ **std 가 문서로 약속한 것**(널 포인터 최적화). 근거로 써도 된다 |
| `NonZeroU32` — `Option<T>` 가 같은 크기 | ★ **std 가 문서로 약속한 것** |
| `String` · `Vec<u8>` · `char` · `bool` · `Never2` · 중첩 `Option` | ★★ **이 판의 관찰**. 니치 선택 규칙은 명세에 없다 |
| `u8` · `u32` · `f64` · `()` 가 느는 폭 | ★★ **이 판의 관찰** |

- ★ 근거로 쓸 때는 **std 가 약속한 두 줄만** 쓴다. 나머지는 「내 머신에서 그랬다」로 적는다.

### 4. ★★ `None` 은 **비어 있던 무늬** 자리에 적힌다

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 태그가 어디 사는가 — 1바이트짜리를 정수로 옮겨 담아 직접 읽는다
use std::num::NonZeroU8;

fn main() {
    // bool 은 0·1 만 쓴다. 남는 값 하나가 None 자리가 된다
    let n: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(None) };
    let f: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(false)) };
    let t: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(true)) };
    println!("Option<bool> 1바이트: None={} Some(false)={} Some(true)={}", n, f, t);

    // NonZeroU8 은 0 을 못 쓴다. 그 0 이 None 자리다
    let n2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(None) };
    let s2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(NonZeroU8::new(200)) };
    println!("Option<NonZeroU8> 1바이트: None={} Some(200)={}", n2, s2);

    // 참조는 널이 될 수 없다. 그 널이 None 자리다 — 널 포인터 최적화
    let x = 41i32;
    let r: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(Some(&x)) };
    let nn: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(None) };
    println!("Option<&i32>: None={} Some(&x)가 &x 주소와 같나={}",
             nn, r == (&x as *const i32 as usize));

    // 니치가 없으면 태그를 따로 둔다 — u8 은 256가지를 다 쓴다
    println!("Option<u8> 크기={} (u8 크기={})", size_of::<Option<u8>>(), size_of::<u8>());
    // 같은 값인데 서로 다른 변형임을 구별하는 표식
    let a: Option<u8> = Some(0);
    let b: Option<u8> = None;
    println!("판별자가 다른가={}",
             std::mem::discriminant(&a) != std::mem::discriminant(&b));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Option<bool> 1바이트: None=2 Some(false)=0 Some(true)=1
Option<NonZeroU8> 1바이트: None=0 Some(200)=200
Option<&i32>: None=0 Some(&x)가 &x 주소와 같나=true
Option<u8> 크기=2 (u8 크기=1)
판별자가 다른가=true
(종료 코드 0)
```

**왜 그런가**

- **`Option<bool>`** — `Some(false)=0` · `Some(true)=1` · **`None=2`**.
  `bool` 은 0과 1만 쓰므로 **2번 무늬가 비어 있다.** 거기에 `None` 을 적는다. 태그가 따로 없다.
- **`Option<NonZeroU8>`** — **`None=0`**. `NonZeroU8` 이 못 쓰는 값이 정확히 0이라 그 자리가 `None` 이다.
- **`Option<&i32>`** — `None` 은 **0**(널), `Some(&x)` 는 **`x` 의 주소 그대로**다.
  C 의 「널이면 없음」과 **메모리에서는 같고 타입에서만 다르다** — 이쪽은 `match` 를 안 하면 못 읽는다.
- **흔들리는 칸** — `Some(&x)` 의 값은 **실행마다 다른 주소**다. 그래서 이 프로그램은 숫자를 안 찍고
  **`&x` 의 주소와 같은지 `true`/`false` 로만** 찍는다. ★ 순서·주소처럼 흔들리는 것은
  **출력 형식을 결정적으로 바꿔** 피하는 쪽이 여러 번 돌려 보는 것보다 싸고 확실하다.
- **`Option<u8>` 은 2바이트**라 1바이트 정수로 옮겨 담을 수가 없다. 그리고 `None` 일 때
  **짐 바이트가 초기화되지 않아** 통째로 읽는 것 자체가 미정의 동작이다 — 그래서 `size_of` 와
  `discriminant` 로만 본다.
- `std::mem::discriminant` 는 **짐을 안 보고 도장만** 비교한다 — `Some(0)` 과 `None` 이 다르다고 답한다.

### 5. ★ 에러 둘 — E0665(`Default`)와 E0204(`Copy`)

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// derive 가 거부되는 두 자리 — Copy 와 Default
#[derive(Clone, Copy)]
enum Payload {
    Num(u32),
    Text(String),      // String 은 Copy 가 아니다
}

#[derive(Default)]
enum Mode {
    Fast,
    Slow,
}

fn main() {
    let _ = Payload::Num(1);
    let _ = Mode::Fast;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0665]: `#[derive(Default)]` on enum with no `#[default]`
  --> ex.rs:9:10
   |
 9 |   #[derive(Default)]
   |            ^^^^^^^
10 | / enum Mode {
11 | |     Fast,
12 | |     Slow,
13 | | }
   | |_- this enum needs a unit variant marked with `#[default]`
   |
help: make this unit variant default by placing `#[default]` on it
   |
11 |     #[default] Fast,
   |     ++++++++++
help: make this unit variant default by placing `#[default]` on it
   |
12 |     #[default] Slow,
   |     ++++++++++

error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:3:17
  |
3 | #[derive(Clone, Copy)]
  |                 ^^^^
...
6 |     Text(String),      // String 은 Copy 가 아니다
  |          ------ this field does not implement `Copy`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0204, E0665.
For more information about an error, try `rustc --explain E0204`.
(종료 코드 1)
```

**왜 그런가**

- **E0204** — ``the trait `Copy` cannot be implemented for this type``.
  ★ 진단이 짚는 것은 **변형이 아니라 칸**이다 — `Text(String)` 의 `String` 에 밑줄을 긋고
  `` this field does not implement `Copy` `` 라고 적는다. **한 칸이 전체를 막는다.**
- **E0665** — 제목은 `` `#[derive(Default)]` on enum with no `#[default]` `` 다.
  ★ `help:` 가 **둘** 나온다 — `Fast` 와 `Slow`, 즉 **단위 변형 개수만큼**이다.
  컴파일러는 어느 것이 기본이어야 하는지 모르므로 후보를 전부 제안한다.
- 고치는 법은 단위 변형 하나에 `#[default]` 를 붙이는 것이고, 그 문법은 **1.62.0부터**다.
- **`Clone` 만 파생하면 통과한다.** `Clone` 은 「복제할 수 있나」이고 `String` 은 복제할 수 있다.
  막힌 것은 **「암묵적으로 복사돼도 되나」를 묻는 `Copy`** 쪽뿐이다(09번 주제).

### 6. ★ 거부된다 — E0072 + E0391 **두 개**

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 재귀 열거형은 크기를 못 정한다
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Tree, Tree),
}

fn main() {
    let t = Tree::Node(Tree::Leaf(1), Tree::Leaf(2));
    println!("{:?}", t);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0072]: recursive type `Tree` has infinite size
 --> ex.rs:4:1
  |
4 | enum Tree {
  | ^^^^^^^^^
5 |     Leaf(i32),
6 |     Node(Tree, Tree),
  |          ---- recursive without indirection
  |
help: insert some indirection (e.g., a `Box`, `Rc`, or `&`) to break the cycle
  |
6 |     Node(Box<Tree>, Tree),
  |          ++++    +

error[E0391]: cycle detected when computing when `Tree` needs drop
 --> ex.rs:4:1
  |
4 | enum Tree {
  | ^^^^^^^^^
  |
  = note: ...which immediately requires computing when `Tree` needs drop again
  = note: cycle used when computing whether `Tree` needs drop
  = note: see https://rustc-dev-guide.rust-lang.org/overview.html#queries and https://rustc-dev-guide.rust-lang.org/query.html for more information

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0072, E0391.
For more information about an error, try `rustc --explain E0072`.
(종료 코드 1)
```

**왜 그런가**

- **E0072** — ``recursive type `Tree` has infinite size``. 진단이 문제의 칸을
  **`recursive without indirection`**(사이에 한 겹이 없다)이라고 부른다.
- `help:` 가 대는 셋은 **`Box`·`Rc`·`&`** 다 — 전부 **「값 대신 포인터를 담아 크기를 끊는」** 도구다.
  제안 코드까지 붙여 준다(`Node(Box<Tree>, Tree)`).
- **E0391**(``cycle detected when computing when `Tree` needs drop``)은 **딸린 에러**다 —
  크기를 못 정했으니 「해제가 필요한 타입인가」도 못 정한다. E0072 를 고치면 같이 사라진다.

**고친 판.**

```text
===== 소스: ex.rs =====
// ex.rs
// Box 로 한 칸 건너뛰면 크기가 정해진다 — 그리고 그 크기를 잰다
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Box<Tree>, Box<Tree>),
}

impl Tree {
    fn sum(&self) -> i32 {
        match self {
            Tree::Leaf(n) => *n,
            Tree::Node(l, r) => l.sum() + r.sum(),
        }
    }
}

fn main() {
    let t = Tree::Node(
        Box::new(Tree::Leaf(1)),
        Box::new(Tree::Node(Box::new(Tree::Leaf(2)), Box::new(Tree::Leaf(3)))),
    );
    println!("{:?}", t);
    println!("합 {}", t.sum());
    println!("Tree {} Box<Tree> {} i32 {}",
             size_of::<Tree>(), size_of::<Box<Tree>>(), size_of::<i32>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Node(Leaf(1), Node(Leaf(2), Leaf(3)))
합 6
Tree 16 Box<Tree> 8 i32 4
(종료 코드 0)
```

- `Tree` 는 **16바이트**다. `Node` 쪽이 `Box` 두 개라 8+8=16 이고, 태그는 **`Box` 의 니치**에 들어가 자리를 안 먹는다
  (`Leaf(i32)` 는 4바이트뿐이라 크기를 정하지 못한다).
- 이 숫자 역시 **이 판의 관찰**이다. `Box` 가 재귀를 어떻게 푸는지의 정본은 [목록의 **40번 주제**](../40-box-recursive-types-and-dyn/)다.

### 7. 변형은 타입이 아니라 값이다

- `Message::Quit` 의 **타입은 `Message`** 다. 변형별 타입은 없다.
- 그래서 `fn f(m: Message::Quit)` 는 **못 쓴다.** 인자 타입 자리에는 `Message` 를 쓰고
  안에서 `match` 로 가른다(다음 주제).
- **튜플 변형의 이름은 함수다** — `Message::Move` 의 타입은 `fn(i32, i32) -> Message` 라
  `.map(Message::Move)` 로 **클로저 없이** 넘길 수 있다. 16번 주제의 튜플 구조체와 같은 성질이다.
- 이름 있는 구조체와 **같은 것** — `impl` 문법·`Self`·연관 함수·연관 상수가 한 글자도 다르지 않다.
  **다른 것** — 구조체는 칸이 **전부** 있고, 열거형은 변형 중 **하나**다.
- ★ `use Message::*;` 를 습관으로 쓰면 변형 이름이 **지역 변수 이름과 같아질 수 있다.**
  그러면 패턴 자리에서 「변형을 짚은 것」이 아니라 「새 변수를 묶은 것」이 된다 —
  다음 주제에서 **E0170** 으로 나온다(18번 답 5).

### 8. 판별값의 규칙

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// C 스타일 열거형 — 판별값을 직접 주고 `as` 로 정수로 꺼낸다
#[derive(Debug, Clone, Copy)]
enum Status {
    Ok = 200,
    NotFound = 404,
    Teapot = 418,
}

#[derive(Debug, Clone, Copy)]
enum Step { A, B, C = 10, D }   // 안 적으면 「앞 값 + 1」

fn main() {
    println!("{} {} {}", Status::Ok as i32, Status::NotFound as i32, Status::Teapot as i32);
    println!("{} {} {} {}", Step::A as u8, Step::B as u8, Step::C as u8, Step::D as u8);
    println!("{:?} {:?}", Status::Teapot, Step::D);
    // 크기 — 판별값만 있는 열거형은 판별값 하나만큼이다
    println!("Status {} Step {}", size_of::<Status>(), size_of::<Step>());
    // 역방향은 공짜가 아니다 — 정수에서 열거형으로 가는 `as` 는 없다
    let n = 404;
    let back = match n { 200 => Some(Status::Ok), 404 => Some(Status::NotFound), _ => None };
    println!("{:?}", back);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
200 404 418
0 1 10 11
Teapot D
Status 2 Step 1
Some(NotFound)
(종료 코드 0)
```

**왜 그런가**

- 안 적으면 **0부터, 앞 값 + 1** 이다. `Step { A, B, C = 10, D }` 에서 `A=0 B=1 C=10` **`D=11`** 이다.
- **크기를 정하는 것은 변형 개수가 아니라 값의 크기**다 — `Status` 는 404·418 때문에 **2바이트**,
  `Step` 은 0\~11 이라 **1바이트**다.
- **정수에서 열거형으로 가는 `as` 는 없다.** `match` 를 손으로 쓰거나 `TryFrom` 을 구현한다
  (위 출력의 `Some(NotFound)` 가 손으로 쓴 쪽이다).
- ★ **판별값을 보장으로 쓸 수 있는 경우** — 내가 `= 200` 처럼 **직접 적었을 때**다.
  안 적고 나온 값(0,1,2…)도 규칙은 정해져 있지만, **변형 순서를 바꾸면 조용히 바뀐다.**
- `as` 는 **정수를 꺼내는 것**이라 단위 변형뿐일 때만 되고,
  `std::mem::discriminant` 는 **비교만 하는 불투명한 표식**이라 **어떤 열거형에도** 쓸 수 있다.
  뒤엣것의 **값 자체는 보장이 없다.**

### 9. `Option` 과 `Result` 는 그냥 `enum` 이다

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// Option 과 Result 도 그냥 열거형이다 — 똑같은 것을 직접 만들어 본다
#[derive(Debug)]
enum MyOption<T> { MyNone, MySome(T) }

#[derive(Debug)]
enum MyResult<T, E> { MyOk(T), MyErr(E) }

use MyOption::{MyNone, MySome};
use MyResult::{MyOk, MyErr};

fn find(v: &[i32], target: i32) -> MyOption<usize> {
    for (i, x) in v.iter().enumerate() {
        if *x == target { return MySome(i); }
    }
    MyNone
}

fn half(n: i32) -> MyResult<i32, String> {
    if n % 2 == 0 { MyOk(n / 2) } else { MyErr(format!("{} 는 홀수", n)) }
}

fn main() {
    let v = [10, 20, 30];
    println!("{:?} {:?}", find(&v, 20), find(&v, 99));
    println!("{:?} {:?}", half(8), half(7));
    // std 것과 크기·모양을 나란히 — 변형 이름만 다르다
    println!("내 것 {} std {}", size_of::<MyOption<i32>>(), size_of::<Option<i32>>());
    println!("std  {:?} {:?}", Some(1usize), None::<usize>);
    // std 의 정의도 이것과 같다: enum Option<T> { None, Some(T) }
    let o: Option<i32> = Some(3);
    println!("{:?}", match o { Some(n) => n * 2, None => -1 });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
MySome(1) MyNone
MyOk(4) MyErr("7 는 홀수")
내 것 8 std 8
std  Some(1) None
6
(종료 코드 0)
```

**왜 그런가**

- 정의는 한 줄이다 — **`enum Option<T> { None, Some(T) }`**. `Result` 는 `enum Result<T, E> { Ok(T), Err(E) }`.
- 내가 만든 `MyOption<i32>` 와 std 의 `Option<i32>` 는 **크기가 8로 같다.** 모양이 같으니 배치도 같다.
- 다른 점 **셋** — ① **prelude 에 있어 `use` 가 필요 없다** ② **`?` 연산자가 붙는다**
  ③ **`map`·`and_then`·`unwrap_or` 같은 조합 메서드가 딸려 있다**([목록의 **21번 주제**](../21-option-and-combinators/)·**22번 주제**).
- **`None` 은 null 과 다르다.** 메모리에서는 같을 수 있다 — `Option<&T>` 의 `None` 은 실제로 0이다(4번 답).
  ★ 다른 것은 **타입**이다. null 은 **모든 참조 타입에 몰래 들어 있는 값**이고,
  `None` 은 **`Option<T>` 라고 적은 자리에만** 있다. 그래서 컴파일러가 **꺼내기 전에 확인하라고 강제**한다.
- **`Result<u32, u32>` 는 8바이트** — 짐이 4바이트 둘인데 둘 다 니치가 없어 **태그 4 + 짐 4** 가 된다(관찰).
- 「Rust 에는 null 이 없다」는 **「없음」을 타입에 적게 강제한다**는 뜻이다.
  1번 답의 설계(불가능한 상태 지우기)가 **표준 라이브러리 수준에서 한 번 더 일어난 것**이다.

### 10. 주석으로 적던 불변식을 타입으로 옮기는 것

- 「이 불리언이 참이면 저 필드는 반드시 있다」는 주석을 봤으면 **그 주석이 곧 열거형 선언**이다.
  플래그 + `Option` 묶음을 **변형으로 접는다**(1번 답의 전/후).
- 이득을 강하게 적으면 — **「그 실수를 적을 수가 없다」** 다. 검사로 막는 것이 아니라 **문법에서 사라진다.**
  E0559 가 그것을 증명한다.
- **대가** — ① 값을 읽을 때마다 `match` 가 필요해 **읽는 코드가 길어진다**
  ② 변형을 하나 늘리면 **모든 `match` 가 깨진다**(다음 주제의 실험) — 이건 대가이자 안전망이다
  ③ 봉투가 **제일 큰 변형**에 맞춰져 **전부가 커진다**.
- **변형이 계속 늘고 남이 추가해야 하면** 열거형이 아니라 **트레이트**가 맞다([목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/)).
  열거형은 **닫힌 집합**이고, 그 닫힘이 다음 주제의 완전성 검사를 가능하게 한다.
- **변형 하나가 유독 크면** 그 변형만 `Box` 로 싼다 — 크기가 포인터 하나로 줄고, 그 대가로 간접 참조가 는다.
  **재어 보고** 한다((7)의 `size_of`).

### 11. 다른 주제와 잇기

| 번호 | 언제 나나 |
|---|---|
| **E0559** | 구조체 변형에 **선언에 없는 칸**을 줬다 |
| **E0605** | 데이터를 담은 변형이 있는 열거형에 **`as`** 를 썼다 |
| **E0732** | **판별값 + 데이터 변형**을 `#[repr(inttype)]` 없이 섞었다 |
| **E0204** | `Copy` 를 파생했는데 어느 칸이 `Copy` 가 아니다 |
| **E0665** | `Default` 를 파생했는데 `#[default]` 변형 표시가 없다 |
| **E0072** | 재귀 타입이라 크기가 무한이다 |
| **E0391** | 위의 딸린 에러 — 크기를 못 정해 드롭 여부도 못 정한다 |

- `impl`·연관 함수·`Self` 의 정본은 [**16번 주제**](../16-structs-impl-and-associated-functions/)다.
  이 주제는 **그 문법을 한 글자도 안 바꾸고 그대로** 쓴다((2)).
- `Copy` 파생이 막히는 이유의 뿌리는 [**09번 주제**](../09-copy-clone-and-drop/)다 —
  「암묵 복사가 안전한 타입인가」. 여기는 **열거형에서 어떻게 나타나나**까지.
- 이 주제가 만든 값을 **꺼내는** 것은 [목록의 **18번 주제**](../18-match-and-exhaustiveness/)(`match` 와 완전성 검사)다.
  그 안전망은 **열거형이 닫힌 집합이라는 사실**에 기댄다 — 그래서 이 주제가 선행이다.
- `Box` 와 재귀 타입의 정본은 [목록의 **40번 주제**](../40-box-recursive-types-and-dyn/)다. 여기서는 **왜 막히나**와 **고치면 몇 바이트인가**까지만 다뤘다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | 재실행 결과가 `diff -rq` 로 **동일** |
| 변형 세 종류 · `impl` | `b17-01` · `b17-02` | 2 | 종료 코드 0 |
| 불가능한 상태 전/후 | `b17-03`(통과) · `b17-04`(E0559) | 2 | 전 판이 **모순 값을 아무 불평 없이 만든다** |
| 판별값 · `as` 금지 | `b17-05` · `b17-06`(E0605 ×2) · `b17-06b`(E0732) | 3 | 판정이 **열거형 전체** 단위임을 확인 |
| `derive` 되는 것/안 되는 것 | `b17-07`(통과) · `b17-08`(E0204·E0665) | 2 | `help:` 가 **단위 변형 수만큼** 나옴 |
| `Option`/`Result` 가 enum | `b17-09` | 1 | 내 것과 std 것이 **크기 8로 같음** |
| `size_of` 니치 표 13행 | `b17-10` | 1 | 같은 것 9 · 느는 것 4 |
| 태그 위치 읽기 | `b17-11` — 1바이트/8바이트 `transmute` | 1 | `None` 이 **비어 있던 무늬**에 적힘 |
| 재귀 타입 | `b17-12`(E0072·E0391) · `b17-13`(16바이트) | 2 | — |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `size_of` 표의 **std 가 약속하지 않은 행** — `String`·`Vec`·`char`·`bool`·`Never2`·중첩 `Option`·`u8`/`u32`/`f64`/`()` | 니치 선택과 배치는 **구현 세부**다 |
| `Option<bool>` 의 `None=2` · `Option<NonZeroU8>` 의 `None=0` | 어느 무늬를 쓸지는 명세에 없다 |
| `Status` 가 2바이트인 것 | 판별값을 담을 정수형 선택이 고정이 아니다 |
| `Tree` 가 16바이트인 것 | 같은 이유 |
| 진단 문구·`help:` 의 제안 코드 | rustc 판마다 달라진다 |
| `#[default]` 가 1.62.0부터인 것 | 그 아래 판에서는 E0665 를 못 고친다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다. 달라진 파일이 곧 고칠 자리다.
