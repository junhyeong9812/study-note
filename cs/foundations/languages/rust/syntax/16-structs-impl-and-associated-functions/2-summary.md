# rust/syntax/16 — 구조체 세 종류·`impl`·연관 함수·`Self` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference — Structs](https://doc.rust-lang.org/reference/items/structs.html) ·
> [Reference — Implementations](https://doc.rust-lang.org/reference/items/implementations.html) ·
> [Reference — Associated Items](https://doc.rust-lang.org/reference/items/associated-items.html) ·
> [Reference — Struct expressions](https://doc.rust-lang.org/reference/expressions/struct-expr.html) ·
> [Reference — Type layout](https://doc.rust-lang.org/reference/type-layout.html) ·
> [`std::mem::size_of`](https://doc.rust-lang.org/std/mem/fn.size_of.html) ·
> `rustc --explain E0599` / `E0592` / `E0034` / `E0063` / `E0560` / `E0616` / `E0603` / `E0411` / `E0423`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다.\
> ★ 단 **한 블록만 예외**다 — `cargo doc` 실험((7))은 `cargo 1.92.0 (344c4567c 2025-10-21)` 로 돌렸고,\
> 그 블록의 소스는 임시 크레이트의 **`src/lib.rs`** 가 된다(배너에 그 변환까지 적어 뒀다).\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — 구조체 세 종류·`impl`·`Self` 는 전부 1.0.0부터다. **필드 초기화 축약**과 **구조체 갱신 문법**도 1.0.0부터다.\
> **연관 상수**(`impl` 안의 `const`)는 **1.20.0**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**구조체는 「서류 양식」이고, `impl` 은 「그 양식에 딸린 업무 매뉴얼」이다.**

양식과 매뉴얼은 **따로 적는다**. 다른 언어의 클래스가 필드와 메서드를 한 괄호에 넣는 것과 여기가 갈린다.

| 비유 | 실체 |
|---|---|
| 칸에 **이름이 적힌** 양식 | **이름 있는 구조체** — `struct Point { x: i32, y: i32 }` |
| 칸에 **번호만** 있는 양식 | **튜플 구조체** — `struct Meters(f64)`. 접근은 `.0` |
| **칸이 아예 없는** 양식 — 도장만 찍는다 | **유닛 구조체** — `struct Marker;`. 크기 **0바이트** |
| 양식과 **따로 묶인 매뉴얼철** | **`impl` 블록**. 한 양식에 **여러 권**을 둘 수 있다 |
| 「서류 **한 장을 들고** 하는 일」 | **메서드** — 첫 인자가 `self`. `p.area()` |
| 「서류 **없이** 창구에서 하는 일」 — 발급 포함 | **연관 함수** — `self` 없음. `Point::new()` |
| 매뉴얼 안에서 「**이 양식**」이라고 줄여 쓰는 말 | **`Self`** — `impl` 대상 타입의 별명 |
| 그 창구에 **들고 온 그 서류** | **`self`** — 리시버. ★ `Self` 와 **다른 것**이다 |
| 서류를 **보여만 준다 / 고쳐 준다 / 맡기고 안 돌려받는다** | **`&self` / `&mut self` / `self`** |
| 「**이 칸은 창구 직원만 본다**」 | **필드 기본 비공개** — 모듈 밖에서는 `pub` 없으면 안 보인다 |

- ★★ **`impl` 은 타입 선언과 분리돼 있다.** 그래서 **블록을 몇 개든 둘 수 있고**, 경계별로 갈라 쓴다((6)).
- ★★ **연관 함수와 메서드를 가르는 것은 이름도 위치도 아니고 「첫 인자가 `self` 인가」 하나**다.
- ★ **유닛 구조체·빈 튜플 구조체는 `size_of` 가 0이다**((8)) — 값이 있는데 메모리를 안 쓴다.

```text
   struct 와 impl 은 따로 있다

   struct Point { x: i32, y: i32 }     ← 양식(데이터 배치)
        │
        ├── impl Point { fn new(..) -> Self }        ← 매뉴얼 1권 (연관 함수)
        ├── impl Point { fn area(&self) -> i32 }     ← 매뉴얼 2권 (메서드)
        └── impl<T: Display> Wrapper<T> { .. }       ← 경계가 붙은 권

   부르는 법이 갈린다
        Point::new(3, 4)     ::  ← 연관 함수. 리시버가 없다
        p.area()             .   ← 메서드. p 가 self 로 들어간다
        Point::area(&p)      ::  ← ★ 이것도 된다(같은 함수의 본래 모습)
```

**컴파일러도 이 구분을 진단 문구로 말한다.** 연관 함수를 `.` 으로 불러 보면 세 구절이 나온다 —
`this is an associated function, not a method` ·
`help: use associated function syntax instead: Counter::new()` ·
`= note: found the following associated functions; to be used as methods, functions must have a self parameter`.
★ **진단 전문과 그 진단을 낸 소스는 (3)에 있다** — 여기서는 문구만 옮겼다.

> **구조체(struct)** — 여러 값을 한 이름으로 묶은 **사용자 정의 타입**.\
> 이름 있는·튜플·유닛 세 형태가 있고, 세 형태 모두 **같은 `impl` 문법**을 쓴다.

> **연관 항목(associated item)** — `impl` 블록(또는 트레이트) 안에 들어가는 것들.\
> **연관 함수**·**연관 상수**·**연관 타입** 셋이다. 「그 타입에 딸린 것」이라는 뜻이다.

> **메서드(method)** — 연관 함수 중 **첫 인자가 리시버(`self`·`&self`·`&mut self`)인 것**.\
> 메서드는 연관 함수의 부분집합이다 — 반대가 아니다.

> **리시버(receiver)** — 메서드가 받는 **자기 자신**. `p.area()` 의 `p` 가 그 자리로 들어간다.

> **`Self`(대문자)** — `impl` 이 대상으로 삼은 **타입의 별명**. 타입 자리에 쓴다.\
> **`self`(소문자)** — 그 타입의 **값**. 값 자리에 쓴다. ★ **둘은 다른 것**이다((4)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **세 형태 중 무엇을 고르나** — 이름 있는·튜플·유닛이 각각 어떤 자리에 맞나. 그리고 **유닛은 왜 0바이트인가**.
2. **`impl` 안의 것을 어떻게 부르나** — 연관 함수와 메서드가 갈리는 지점 하나가 무엇이고, 틀리게 부르면 **어느 진단**이 나오나.
3. **리시버 세 가지 중 무엇을 받나** — `&self`·`&mut self`·`self` 를 고르는 기준과 그 대가.

★ [**09번 주제**](../09-copy-clone-and-drop/)가 「값이 언제 복사되고 언제 죽나」였다면,
여기는 「**그 값을 담을 타입을 내가 직접 만들고 거기에 동작을 붙이는 법**」이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 생성·호출·가시성이 막히는 자리 — E0063·E0599·E0616 | [**11번 주제**](../11-borrow-checker-rejections/)의 「에러도 출력이다」 |
| ★ **진단에게 후보를 나열하게 만들기** | `impl` 이 여럿일 때 컴파일러가 **무엇을 뒤졌나** — `candidate #1`·`#2` | ★ 이 주제의 고유 창 |
| ★ **`cargo doc` 이 만든 HTML 을 기계적으로 세기** | `impl` 블록이 **몇 덩어리로 남는가** | ★ 이 주제의 고유 창 |
| ★ **`size_of`·`align_of` 로 메모리 표면 재기** | 세 형태가 **실제로 몇 바이트인가** | ★ 이 주제의 고유 창 |

★ Rust 에는 `javap -c` 같은 「컴파일러가 한 일을 그대로 보여 주는」 도구가 `impl` 에 대해서는 없다.
**대신 두 가지가 있다** — 진단이 후보를 **번호 매겨 나열**하고, `cargo doc` 이 **블록 경계를 HTML 에 그대로 남긴다**.
둘 다 **지어낼 수 없고 독자가 자기 머신에서 재현한다**.

비용 — 앞의 셋은 컴파일만 하면 된다. `cargo doc` 만 `cargo` 가 필요하다.

### (1) 구조체 세 종류 — 선언·생성·접근·구조 분해

**언제 쓰나** — 타입을 새로 만들 때마다. **셋 중 하나를 고르는 것이 첫 결정**이다.

```text
===== 소스: ex.rs =====
// 구조체 세 종류 — 선언·생성·접근·구조 분해를 한 파일에서 전부 본다
#[derive(Debug)]
struct Point { x: i32, y: i32 }   // 이름 있는 구조체
#[derive(Debug)]
struct Meters(f64);               // 튜플 구조체
#[derive(Debug)]
struct Marker;                    // 유닛 구조체

fn main() {
    // 생성
    let p = Point { x: 3, y: 4 };
    let m = Meters(1.5);
    let k = Marker;

    // 접근 — 이름 / 번호 / 없음
    println!("이름: {} {}", p.x, p.y);
    println!("번호: {}", m.0);
    println!("유닛: {:?}", k);

    // 구조 분해
    let Point { x, y } = p;
    let Meters(len) = m;
    let Marker = k;
    println!("분해: x={} y={} len={}", x, y, len);

    // 일부만 받고 나머지는 버리기
    let q = Point { x: 10, y: 20 };
    let Point { x: only_x, .. } = q;
    println!("일부만: {}", only_x);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
이름: 3 4
번호: 1.5
유닛: Marker
분해: x=3 y=4 len=1.5
일부만: 10
(종료 코드 0)
```

읽는 법.

- **이름 있는 구조체** — 생성도 접근도 분해도 **이름**으로 한다. 칸이 셋 이상이면 대개 이쪽이다.
- **튜플 구조체** — 접근이 **`.0`·`.1`**. 칸이 하나뿐이고 **이름을 붙여도 정보가 안 느는** 자리에 쓴다.
- **유닛 구조체** — **생성이 곧 이름**이다(`let k = Marker;`). 데이터가 없고 **타입 자체가 정보**일 때 쓴다.
- `let Marker = k;` 는 **패턴**이다 — 유닛 구조체는 분해할 것이 없으므로 이름만 적는다.

★ **튜플 구조체의 이름은 함수이기도 하다.** 이름 있는 구조체와 여기서 갈린다.

```text
===== 소스: ex.rs =====
// 튜플 구조체의 이름은 함수이기도 하다 — 이름 있는 구조체와 갈리는 자리
#[derive(Debug)]
struct Meters(f64);

fn main() {
    // 생성자를 값으로 넘긴다
    let v: Vec<Meters> = vec![1.0, 2.5, 3.0].into_iter().map(Meters).collect();
    println!("합계 {}", v.iter().map(|m| m.0).sum::<f64>());
    println!("{:?}", v);

    // 타입을 함수 포인터에 담아 본다 — 진짜 함수라면 담긴다
    let ctor: fn(f64) -> Meters = Meters;
    println!("{:?}", ctor(9.5));

    // 유닛 구조체의 이름은 「그 타입의 유일한 값」이다
    #[derive(Debug)]
    struct Marker;
    let m: Marker = Marker;
    println!("{:?}", m);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
합계 6.5
[Meters(1.0), Meters(2.5), Meters(3.0)]
Meters(9.5)
Marker
(종료 코드 0)
```

★★ **`let ctor: fn(f64) -> Meters = Meters;` 가 통과한다** — 튜플 구조체의 이름은 **그 타입을 만드는 함수**다.
그래서 `.map(Meters)` 처럼 **클로저 없이** 넘길 수 있다. 이름 있는 구조체는 그렇지 않다.

```text
===== 소스: ex.rs =====
// 이름 있는 구조체의 이름은 값이 아니다 — 튜플 구조체와 갈리는 자리
struct Point { x: i32, y: i32 }

fn main() {
    let f = Point;
    let _ = f;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0423]: expected value, found struct `Point`
 --> ex.rs:5:13
  |
2 | struct Point { x: i32, y: i32 }
  | ------------------------------- `Point` defined here
...
5 |     let f = Point;
  |             ^^^^^ help: use struct literal syntax instead: `Point { x: val, y: val }`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0423`.
```

★ **E0423** — 「값을 기대했는데 구조체가 왔다」. 이름 있는 구조체의 이름은 **타입 이름일 뿐**이고,
값을 만들려면 **중괄호 리터럴**이 있어야 한다.

### (2) 필드 초기화 축약과 구조체 갱신 문법 `..other`

**언제 쓰나** — 생성자를 쓸 때(축약)와, 기존 값에서 몇 칸만 바꾼 값을 만들 때(`..other`).

```text
===== 소스: ex.rs =====
// 같은 ..other 인데 필드가 전부 Copy 면? — 그리고 필드 초기화 축약
#[derive(Debug)]
struct Config { retries: u32, verbose: bool }

fn make(retries: u32, verbose: bool) -> Config {
    Config { retries, verbose }   // 필드 초기화 축약 — retries: retries 를 줄인 것
}

fn main() {
    let base = make(3, false);
    let derived = Config { retries: 5, ..base };
    println!("파생: {} {}", derived.retries, derived.verbose);
    println!("원본: {} {}", base.retries, base.verbose);   // Copy 필드뿐이라 원본이 살아 있다
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
파생: 5 false
원본: 3 false
(종료 코드 0)
```

- **필드 초기화 축약** — `retries: retries` 를 `retries` 로 줄인다. **이름이 같을 때만** 된다.
- **`..base`** — 「적지 않은 칸은 `base` 에서 가져온다」. **반드시 마지막**에 오고, 뒤에 쉼표를 붙이지 않는다.

★★ **`..other` 는 복사가 아니라 「필드별 이동」이다.** 위에서는 `u32`·`bool` 이 전부 `Copy` 라 원본이 살아남았을 뿐이다.
**`String` 을 한 칸만 넣어 다시 던지면** 갈린다.

```text
===== 소스: ex.rs =====
// 구조체 갱신 문법 ..other 는 이동인가 복사인가 — String 필드를 두고 원본을 다시 써 본다
#[derive(Debug)]
struct Config { name: String, retries: u32, verbose: bool }

fn main() {
    let base = Config { name: String::from("기본"), retries: 3, verbose: false };
    let derived = Config { retries: 5, ..base };
    println!("{:?}", derived);
    println!("{:?}", base);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of partially moved value: `base`
 --> ex.rs:9:22
  |
7 |     let derived = Config { retries: 5, ..base };
  |                   ----------------------------- value partially moved here
8 |     println!("{:?}", derived);
9 |     println!("{:?}", base);
  |                      ^^^^ value borrowed here after partial move
  |
  = note: partial move occurs because `base.name` has type `String`, which does not implement the `Copy` trait
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

★★ **`partially moved`** 라는 말이 답이다. `..base` 는 구조체를 통째로 옮기는 것이 아니라
**칸마다 따로** 처리한다 — `Copy` 인 칸은 복사하고 아닌 칸은 **옮긴다**.
그래서 `base.retries` 는 그 뒤에도 읽히지만 `base` 전체는 못 읽는다.

```text
   ..base 가 칸마다 하는 일

   base : | name: String | retries: u32 | verbose: bool |
                │              (안 씀)          │
              이동                             복사
                ▼                               ▼
   derived: | name: String | retries: 5   | verbose: bool |

   결과 — base 는 「부분 이동된 값」이 된다.
          base.retries 는 읽히고, base 전체·base.name 은 못 읽는다.
```

★ **09번의 `Copy`/`Clone` 판정이 여기서 칸 단위로 다시 쓰인다** — 규칙은 새 것이 아니다.

### (3) `impl` — 연관 함수 대 메서드

**언제 쓰나** — 타입에 동작을 붙일 때마다. **가르는 기준은 하나뿐**이다.

```text
   fn new()          -> Self     ← 첫 인자가 self 가 아니다 → 연관 함수. Counter::new()
   fn get(&self)     -> u32      ← 첫 인자가 self 다        → 메서드.   c.get()
   fn bump(&mut self)            ← 〃                       → 메서드.   c.bump()
   fn build(self)    -> String   ← 〃                       → 메서드.   c.build()

   ★ 메서드는 연관 함수의 「부분집합」이다. 반대가 아니다.
```

**호출 문법을 바꿔 불러 본다** — 진단이 무엇을 권하는지가 이 절의 본체다.

```text
===== 소스: ex.rs =====
// 연관 함수와 메서드 — 리시버가 있냐 없냐. 호출 문법을 바꿔 불러 본다
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }   // 연관 함수 — self 없음
    fn get(&self) -> u32 { self.n }         // 메서드 — &self 있음
}

fn main() {
    let c = Counter::new();
    println!("{}", c.new());   // 연관 함수를 . 으로
    println!("{}", Counter::get());  // 메서드를 :: 으로
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `new` found for struct `Counter` in the current scope
  --> ex.rs:11:22
   |
 2 | struct Counter { n: u32 }
   | -------------- method `new` not found for this struct
...
11 |     println!("{}", c.new());   // 연관 함수를 . 으로
   |                    --^^^--
   |                    | |
   |                    | this is an associated function, not a method
   |                    help: use associated function syntax instead: `Counter::new()`
   |
   = note: found the following associated functions; to be used as methods, functions must have a `self` parameter
note: the candidate is defined in an impl for the type `Counter`
  --> ex.rs:5:5
   |
 5 |     fn new() -> Self { Counter { n: 0 } }   // 연관 함수 — self 없음
   |     ^^^^^^^^^^^^^^^^

error[E0061]: this function takes 1 argument but 0 arguments were supplied
  --> ex.rs:12:20
   |
12 |     println!("{}", Counter::get());  // 메서드를 :: 으로
   |                    ^^^^^^^^^^^^-- argument #1 of type `&Counter` is missing
   |
note: method defined here
  --> ex.rs:6:8
   |
 6 |     fn get(&self) -> u32 { self.n }         // 메서드 — &self 있음
   |        ^^^ -----
help: provide the argument
   |
12 |     println!("{}", Counter::get(/* &Counter */));  // 메서드를 :: 으로
   |                                 ++++++++++++++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0061, E0599.
For more information about an error, try `rustc --explain E0061`.
```

★★ **두 방향이 대칭이 아니다.** 이것이 이 절에서 제일 중요한 실측이다.

| 틀리게 부른 방향 | 진단 | 무슨 뜻인가 |
|---|---|---|
| 연관 함수를 `.` 으로 | **E0599** `this is an associated function, not a method` | 그런 **메서드가 없다**. 문법을 바꾸라고 한다 |
| 메서드를 `::` 으로 | **E0061** `argument #1 of type &Counter is missing` | ★ 문법은 **맞다**. **인자를 안 줬을 뿐**이다 |

★ **`Counter::get(&c)` 는 올바른 호출**이다 — `c.get()` 이 그것의 **줄임**이다.
진단이 `/* &Counter */` 를 끼워 넣으라고 말하는 것이 그 증거다. **`.` 은 리시버를 첫 인자로 넣어 주는 설탕**이다.

★ `= note: … to be used as methods, functions must have a self parameter` 한 줄이
**연관 함수와 메서드의 정의를 컴파일러 입으로 말한 것**이다.

### (4) ★ `Self` 가 쓰이는 자리 — 넷이 아니라 더 많다

**언제 쓰나** — `impl` 안에서 자기 타입 이름을 적으려 할 때마다.

```text
===== 소스: ex.rs =====
// Self 가 쓰이는 자리를 한 파일에 전부 모은다 — 몇 자리인가
struct Point { x: i32, y: i32 }

impl Point {
    // ① 연관 상수의 타입 자리 + ② 값 자리(구조체 리터럴)
    const ORIGIN: Self = Self { x: 0, y: 0 };

    // ③ 연관 함수의 반환 타입 + ④ 생성자 몸통의 Self { … }
    fn new(x: i32, y: i32) -> Self { Self { x, y } }

    // ⑤ 인자 타입 자리
    fn add(&self, other: &Self) -> Self { Self::new(self.x + other.x, self.y + other.y) }

    // ⑥ 지역 변수 타입 자리 + ⑦ 경로 한정자(Self::연관함수 · Self::연관상수)
    fn doubled(&self) -> Self {
        let base: Self = Self::ORIGIN;
        Self::new(base.x + self.x * 2, base.y + self.y * 2)
    }

    // ⑧ 리시버 타입을 직접 적는 자리 — self: &Self 는 &self 의 원래 형태다
    fn len2(self: &Self) -> i32 { self.x * self.x + self.y * self.y }

    // ⑨ 패턴 자리
    fn parts(&self) -> (i32, i32) {
        let Self { x, y } = *self;
        (x, y)
    }
}

// ⑩ 튜플 구조체에서는 Self 가 생성자 함수 이름으로도 쓰인다
struct Meters(f64);
impl Meters {
    fn zero() -> Self { Self(0.0) }
    fn plus(self, d: f64) -> Self { Self(self.0 + d) }
}

// ⑪ 유닛 구조체에서는 Self 하나가 값이다
struct Marker;
impl Marker {
    fn make() -> Self { Self }
}

// ⑫ 트레이트의 연관 타입 자리
trait Doubler {
    type Out;
    fn twice(self) -> Self::Out;
}
impl Doubler for Point {
    type Out = Self;                    // 연관 타입에 Self
    fn twice(self) -> Self::Out { self.doubled() }
}

fn main() {
    let p = Point::new(3, 4);
    let q = p.add(&Point::ORIGIN);
    println!("add     = ({}, {})", q.x, q.y);
    println!("doubled = ({}, {})", p.doubled().x, p.doubled().y);
    println!("len2    = {}", p.len2());
    println!("parts   = {:?}", p.parts());
    println!("twice   = ({}, {})", p.twice().x, q.y);
    println!("meters  = {}", Meters::zero().plus(2.5).0);
    let _m: Marker = Marker::make();
    println!("marker  = 만들어졌다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
add     = (3, 4)
doubled = (6, 8)
len2    = 25
parts   = (3, 4)
twice   = (6, 4)
meters  = 2.5
marker  = 만들어졌다
(종료 코드 0)
```

★ **한 파일이 통과했다는 것이 열두 자리가 전부 유효하다는 증거**다. 자리를 성격으로 묶으면 **셋**이다.

| 묶음 | 무엇인가 | 위 파일의 자리 |
|---|---|---|
| **타입 자리** | 타입 이름을 적는 모든 곳 | 반환 타입 · 인자 타입 · 지역 변수 타입 · 연관 상수의 타입 · 연관 타입 우변 · 리시버 타입 |
| **값·패턴 자리** | 생성자 표현식과 패턴 | `Self { … }` · `Self(…)` · `Self`(유닛) · `let Self { x, y } = …` |
| **경로 한정자 자리** | `Self::` 로 시작하는 경로 | `Self::new(…)` · `Self::ORIGIN` · `Self::Out` |

★★ **「연관 함수의 반환 타입 · 생성자 몸통 · 타입 이름 대신 · 연관 상수/타입 자리」 넷으로 세면 모자란다.**
**경로 한정자(`Self::`)**·**패턴**·**리시버 타입(`self: &Self`)** 이 빠진다.
**「타입 자리 / 값·패턴 자리 / 경로 한정자 자리」 셋으로 묶는 쪽이 셈이 안 샌다.**

**`Self` 와 `self` 는 다른 것이다** — 자리를 바꿔 써서 확인한다.

```text
===== 소스: ex.rs =====
// 타입 Self 와 리시버 self 는 다른 것이다 — 자리를 바꿔 써 본다
struct Point { x: i32, y: i32 }

impl Point {
    fn new() -> Self { Self }          // 이름 있는 구조체인데 Self 를 값으로
    fn sum(&self) -> i32 { Self.x }    // 리시버 자리에 Self
}

fn main() {
    let p = Point::new();
    println!("{} {}", p.sum(), p.y);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: the `Self` constructor can only be used with tuple or unit structs
 --> ex.rs:5:24
  |
5 |     fn new() -> Self { Self }          // 이름 있는 구조체인데 Self 를 값으로
  |                        ^^^^ help: use curly brackets: `Self { /* fields */ }`

error: the `Self` constructor can only be used with tuple or unit structs
 --> ex.rs:6:28
  |
6 |     fn sum(&self) -> i32 { Self.x }    // 리시버 자리에 Self
  |                            ^^^^ help: use curly brackets: `Self { /* fields */ }`

error: aborting due to 2 previous errors
```

- ★ **이 진단에는 번호가 없다.** `error[E0…]` 가 아니라 그냥 `error:` 다 — 12번에서 만난 부류와 같다.
- `Self` 가 **값**이 되는 것은 **튜플 구조체와 유닛 구조체뿐**이다((4)의 ⑩·⑪).
  이름 있는 구조체에서는 **반드시 중괄호**가 있어야 한다.

**`Self` 는 `impl` 밖에서는 이름이 없다.**

```text
===== 소스: ex.rs =====
// Self 는 impl(과 트레이트) 안에서만 이름이 있다 — 밖에서 쓰면
struct Point { x: i32, y: i32 }

fn make() -> Self { Self { x: 0, y: 0 } }

fn main() {
    let p = make();
    println!("{} {}", p.x, p.y);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0411]: cannot find type `Self` in this scope
 --> ex.rs:4:14
  |
4 | fn make() -> Self { Self { x: 0, y: 0 } }
  |    ----      ^^^^ `Self` is only available in impls, traits, and type definitions
  |    |
  |    `Self` not allowed in a function

error[E0411]: cannot find struct, variant or union type `Self` in this scope
 --> ex.rs:4:21
  |
4 | fn make() -> Self { Self { x: 0, y: 0 } }
  |    ----             ^^^^ `Self` is only available in impls, traits, and type definitions
  |    |
  |    `Self` not allowed in a function

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0411`.
```

★★ 진단 문구 **`Self` is only available in impls, traits, and type definitions** — 컴파일러가 **유효 범위를 한 줄로 말해 준다.**
같은 줄에서 **타입 자리와 값 자리가 각각 따로** 걸려 E0411 이 **둘** 났다는 것도 (4)의 분류와 맞는다.

### (5) `&self` / `&mut self` / `self` — 무엇을 받을지 고르는 기준

**언제 쓰나** — 메서드를 쓸 때마다. **이 선택이 호출하는 쪽의 제약을 정한다.**

| 리시버 | 뜻 | 호출부에 요구하는 것 | 고르는 기준 |
|---|---|---|---|
| **`&self`** | 읽기만 한다 | 아무것도 — 여럿이 동시에 된다 | **기본값.** 먼저 이것으로 쓴다 |
| **`&mut self`** | 고친다 | 바인딩이 `mut` 여야 하고, **그 동안 다른 빌림이 없어야** 한다 | 자기 상태를 바꿀 때 |
| **`self`** | 가져가고 안 돌려준다 | 값이 **이동**한다 — 호출부는 그 뒤로 못 쓴다 | 변환·소비·빌더 |

**`self` 를 두 번 부르면** — 이동이다.

```text
===== 소스: ex.rs =====
// self 를 받는 메서드를 두 번 부르면
struct Builder { parts: Vec<String> }

impl Builder {
    fn new() -> Self { Builder { parts: Vec::new() } }
    fn add(mut self, s: &str) -> Self { self.parts.push(s.to_string()); self }
    fn build(self) -> String { self.parts.join("-") }
}

fn main() {
    let b = Builder::new().add("가").add("나");
    println!("{}", b.build());
    println!("{}", b.build());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: use of moved value: `b`
  --> ex.rs:13:20
   |
11 |     let b = Builder::new().add("가").add("나");
   |         - move occurs because `b` has type `Builder`, which does not implement the `Copy` trait
12 |     println!("{}", b.build());
   |                      ------- `b` moved due to this method call
13 |     println!("{}", b.build());
   |                    ^ value used here after move
   |
note: `Builder::build` takes ownership of the receiver `self`, which moves `b`
  --> ex.rs:7:14
   |
 7 |     fn build(self) -> String { self.parts.join("-") }
   |              ^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

★ `note: Builder::build takes ownership of the receiver self` — **진단이 리시버를 직접 지목한다.**
[**08번 주제**](../08-ownership-and-move/)의 E0382 와 **같은 에러**인데, 이동이 **메서드 호출에서 일어났다**는 것만 다르다.
★ `add(mut self, …)` 의 `mut` 는 **리시버 종류가 아니라 「받은 값을 몸통 안에서 고치겠다」는 바인딩 표시**다 — `&mut self` 와 다르다.

**`&mut self` 인데 `let` 이 `mut` 가 아니면.**

```text
===== 소스: ex.rs =====
// &mut self 메서드를 부르는데 let 이 mut 가 아니면
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
    fn bump(&mut self) { self.n += 1; }
    fn get(&self) -> u32 { self.n }
}

fn main() {
    let c = Counter::new();
    c.bump();
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0596]: cannot borrow `c` as mutable, as it is not declared as mutable
  --> ex.rs:12:5
   |
12 |     c.bump();
   |     ^ cannot borrow as mutable
   |
help: consider changing this to be mutable
   |
11 |     let mut c = Counter::new();
   |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
```

★ **`c.bump()` 한 줄이 `&mut c` 를 만든다** — 점 하나에 빌림이 숨어 있다.
[**02번 주제**](../02-bindings-mut-and-shadowing/)의 `mut` 와 [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 가변 빌림이 **메서드 호출 자리에서 만난다.**

**`&mut self` 가 「전체」를 잡는다** — 10번의 결론이 여기서 그대로 재현된다.

```text
===== 소스: ex.rs =====
// 리시버 세 가지가 호출 자리에 무엇을 요구하나 — &mut self 가 전체를 잡는다
struct Log { lines: Vec<String> }

impl Log {
    fn new() -> Self { Log { lines: Vec::new() } }
    fn first(&self) -> &String { &self.lines[0] }       // 공유 빌림
    fn push(&mut self, s: &str) { self.lines.push(s.to_string()); }   // 가변 빌림
}

fn main() {
    let mut log = Log::new();
    log.push("첫 줄");
    let head = log.first();     // 공유 빌림이 살아 있는 동안
    log.push("둘째 줄");        // 가변 빌림을 요청하면?
    println!("{}", head);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `log` as mutable because it is also borrowed as immutable
  --> ex.rs:14:5
   |
13 |     let head = log.first();     // 공유 빌림이 살아 있는 동안
   |                --- immutable borrow occurs here
14 |     log.push("둘째 줄");        // 가변 빌림을 요청하면?
   |     ^^^^^^^^^^^^^^^^^^^ mutable borrow occurs here
15 |     println!("{}", head);
   |                    ---- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

★★ **`first` 가 읽은 것은 `lines[0]` 하나인데 `log` 전체가 잡혔다.**
메서드 시그니처가 `&self` 라고 말했으므로 빌림 검사는 **필드 단위가 아니라 값 단위**로 본다 —
같은 모양의 처방(분할 빌림·필드 직접 접근)은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다.

### (6) 같은 타입에 `impl` 블록을 여럿 두기

**언제 쓰나** — 제네릭 경계별로 메서드를 가를 때, 그리고 긴 `impl` 을 주제별로 쪼갤 때.

```text
===== 소스: ex.rs =====
// 같은 타입에 impl 블록을 셋 두면 되나 — 이름만 안 겹치면 된다
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
}

impl Counter {
    fn bump(&mut self) -> &mut Self { self.n += 1; self }
}

impl Counter {
    fn get(&self) -> u32 { self.n }
}

fn main() {
    let mut c = Counter::new();
    c.bump().bump().bump();
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
3
(종료 코드 0)
```

★ **된다.** 경고 한 줄도 없다. `impl` 은 타입 선언과 분리돼 있으므로 **몇 개든 상관없다.**

**그럼 왜 그렇게 쓰나** — 경계별로 갈라야 메서드가 **조건부로** 생긴다.

```text
===== 소스: ex.rs =====
// impl 블록을 여럿 두는 실제 이유 — 제네릭 경계별로 가르기
use std::fmt::Display;

struct Wrapper<T> { inner: T }

impl<T> Wrapper<T> {
    fn new(inner: T) -> Self { Wrapper { inner } }     // 경계 없이 늘 된다
}

impl<T: Display> Wrapper<T> {
    fn show(&self) -> String { format!("[{}]", self.inner) }  // Display 일 때만 생긴다
}

struct NoDisplay;

fn main() {
    let a = Wrapper::new(42);
    println!("{}", a.show());

    let b = Wrapper::new(NoDisplay);   // new 는 된다
    let _ = &b.inner;
    println!("{}", b.show());          // show 는?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: the method `show` exists for struct `Wrapper<NoDisplay>`, but its trait bounds were not satisfied
  --> ex.rs:22:22
   |
 4 | struct Wrapper<T> { inner: T }
   | ----------------- method `show` not found for this struct
...
14 | struct NoDisplay;
   | ---------------- doesn't satisfy `NoDisplay: std::fmt::Display`
...
22 |     println!("{}", b.show());          // show 는?
   |                      ^^^^ method cannot be called on `Wrapper<NoDisplay>` due to unsatisfied trait bounds
   |
note: trait bound `NoDisplay: std::fmt::Display` was not satisfied
  --> ex.rs:10:9
   |
10 | impl<T: Display> Wrapper<T> {
   |         ^^^^^^^  ----------
   |         |
   |         unsatisfied trait bound introduced here
note: the trait `std::fmt::Display` must be implemented
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/fmt/mod.rs:1007:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★★ **`the method show exists … but its trait bounds were not satisfied`** — 「없다」가 아니라 「**있는데 조건이 안 맞는다**」다.
그리고 `note:` 가 **어느 `impl` 블록이 그 조건을 만들었는지 줄 번호로 짚어 준다**(`ex.rs:10:9`).
`Wrapper::new` 는 경계 없는 블록에 있으므로 같은 타입에서 **그대로 된다.**

**같은 이름을 두 블록에 두면** — 거기서만 막힌다.

```text
===== 소스: ex.rs =====
// 같은 메서드를 두 impl 블록에 중복 정의하면
struct Counter { n: u32 }

impl Counter {
    fn get(&self) -> u32 { self.n }
}

impl Counter {
    fn get(&self) -> u32 { self.n + 100 }
}

fn main() {
    let c = Counter { n: 1 };
    println!("{}", c.get());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0592]: duplicate definitions with name `get`
 --> ex.rs:5:5
  |
5 |     fn get(&self) -> u32 { self.n }
  |     ^^^^^^^^^^^^^^^^^^^^ duplicate definitions for `get`
...
9 |     fn get(&self) -> u32 { self.n + 100 }
  |     -------------------- other definition for `get`

error[E0034]: multiple applicable items in scope
  --> ex.rs:14:22
   |
14 |     println!("{}", c.get());
   |                      ^^^ multiple `get` found
   |
note: candidate #1 is defined in an impl for the type `Counter`
  --> ex.rs:5:5
   |
 5 |     fn get(&self) -> u32 { self.n }
   |     ^^^^^^^^^^^^^^^^^^^^
note: candidate #2 is defined in an impl for the type `Counter`
  --> ex.rs:9:5
   |
 9 |     fn get(&self) -> u32 { self.n + 100 }
   |     ^^^^^^^^^^^^^^^^^^^^

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0034, E0592.
For more information about an error, try `rustc --explain E0034`.
```

★ **에러가 둘 난다.** **E0592**(정의 쪽 — 중복 정의) 와 **E0034**(호출 쪽 — 어느 것인지 모르겠다)다.
★★ **E0034 가 `candidate #1`·`#2` 로 번호를 매겨 나열한다** — 이것이 (0)에서 말한 **두 번째 창**이다.

### (7) ★ `impl` 블록이 어떻게 보이나 — `cargo doc` 이 만든 HTML 을 기계적으로 센다

**언제 쓰나** — 「내가 나눠 쓴 `impl` 블록이 밖에서 어떻게 보이나」가 궁금할 때.

이 절의 실험만 **`cargo` 를 쓴다.** 아래 소스는 `cargo new --lib` 로 만든 임시 크레이트의 **`src/lib.rs`** 가 된다 —
그래서 명령 배너 첫 줄이 **`ex.rs` 를 `dc/src/lib.rs` 로 옮기고 `Cargo.toml` 을 지은 뒤 `cargo doc` 을 부르는** 한 줄이다.
두 번째 배너가 **생성된 HTML 에서 `impl` 블록의 앵커 id 를 `grep -o` 로 세는** 한 줄이다.

```text
===== 소스: ex.rs =====
//! cargo doc 이 impl 블록을 몇 덩어리로 내놓나 — 이 파일이 크레이트의 src/lib.rs 가 된다
use std::fmt::Display;

/// 경계가 다른 impl 블록을 셋 가진 타입
pub struct Wrapper<T> { pub inner: T }

impl<T> Wrapper<T> {
    /// 경계 없는 블록
    pub fn new(inner: T) -> Self { Wrapper { inner } }
}

impl<T: Display> Wrapper<T> {
    /// Display 경계가 붙은 블록
    pub fn show(&self) -> String { format!("[{}]", self.inner) }
}

impl<T: Clone> Wrapper<T> {
    /// Clone 경계가 붙은 블록
    pub fn duplicate(&self) -> T { self.inner.clone() }
}
===== mkdir -p dc/src && cp ex.rs dc/src/lib.rs && printf '[package]\nname = "dc"\nversion = "0.1.0"\nedition = "2021"\n' > dc/Cargo.toml && (cd dc && cargo doc --no-deps --quiet) =====
===== grep -o 'id="\(impl-Wrapper%3CT%3E[^"]*\|method\.[a-z_]*\)"' dc/target/doc/dc/struct.Wrapper.html =====
id="impl-Wrapper%3CT%3E"
id="method.new"
id="impl-Wrapper%3CT%3E-1"
id="method.show"
id="impl-Wrapper%3CT%3E-2"
id="method.duplicate"
id="method.type_id"
id="method.borrow"
id="method.borrow_mut"
id="method.from"
id="method.into"
id="method.try_from"
id="method.try_into"
(종료 코드 0)
```

★★ **세 덩어리가 그대로 남았다.** `impl-Wrapper%3CT%3E` · `-1` · `-2` 세 앵커가 있고,
**각각 바로 뒤에 그 블록의 메서드가 하나씩** 붙어 있다(`new` · `show` · `duplicate`).
`%3C`·`%3E` 는 `<`·`>` 의 URL 인코딩이다.

- **뒤의 `method.*` 일곱 개**는 내가 안 쓴 것들이다 — `Any`·`Borrow`·`From`·`Into`·`TryFrom` 등
  **표준 라이브러리의 포괄 구현**(blanket impl)이 모든 타입에 딸려 오는 것이다.
- **결론** — `impl` 블록을 나눠 쓰면 **문서에서도 나뉘어 나온다.** 합쳐지지 않는다.
  그래서 「경계별로 가르기」가 **읽는 사람에게도 보이는 설계 선택**이 된다.

```text
   cargo doc 이 만든 페이지의 뼈대 (grep 으로 센 것)

   <h2 id="fields">                       ← pub 필드
   <h2 id="implementations">              ← 내가 쓴 세 블록이 전부 여기 아래
        ├ impl-Wrapper%3CT%3E      : impl<T> Wrapper<T>            → new
        ├ impl-Wrapper%3CT%3E-1    : impl<T: Display> Wrapper<T>   → show
        └ impl-Wrapper%3CT%3E-2    : impl<T: Clone> Wrapper<T>     → duplicate
   <h2 id="synthetic-implementations">    ← Send/Sync/Unpin 등 자동 구현
   <h2 id="blanket-implementations">      ← From/Into/TryFrom 등 포괄 구현
```

★ **「`impl` 이 몇 개냐」는 컴파일 결과에는 남지 않지만 문서에는 남는다.**
같은 메서드 집합을 한 블록에 몰아 쓴 것과 셋으로 나눈 것은 **바이너리에서는 구분되지 않고, 문서에서는 구분된다.**

**진단 쪽은 어떤가** — 없는 메서드를 부르면 **뒤진 `impl` 블록들을 나열해 주지 않는다.**

```text
===== 소스: ex.rs =====
// impl 블록이 셋인 타입에서 없는 메서드를 부르면 진단이 무엇을 나열하나
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
}

impl Counter {
    fn get(&self) -> u32 { self.n }
}

impl Counter {
    fn reset(&mut self) { self.n = 0; }
}

fn main() {
    let mut c = Counter::new();
    c.reset();
    println!("{}", c.get());
    c.increment();
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `increment` found for struct `Counter` in the current scope
  --> ex.rs:20:7
   |
 2 | struct Counter { n: u32 }
   | -------------- method `increment` not found for this struct
...
20 |     c.increment();
   |       ^^^^^^^^^
   |
help: there is a method `reset` with a similar name
   |
20 -     c.increment();
20 +     c.reset();
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`impl` 블록을 셋 뒀는데 진단은 하나도 안 짚는다.** 짚는 것은 **구조체 선언 줄**뿐이고,
나머지는 「비슷한 이름」 제안이다. ★ **진단이 블록을 나열하는 것은 「후보가 실제로 있을 때」뿐**이다 — 아래 둘이 그 경우다.

**후보가 여럿이면 번호를 매겨 나열한다.**

```text
===== 소스: ex.rs =====
// 같은 이름의 연관 함수가 두 impl 에 있으면 진단이 몇 개를 나열하나
struct Counter { n: u32 }

trait Make { fn build() -> Self; }

impl Counter {
    fn build() -> Self { Counter { n: 0 } }
}

impl Make for Counter {
    fn build() -> Self { Counter { n: 9 } }
}

fn main() {
    let c = Counter { n: 1 };
    println!("{}", c.build().n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `build` found for struct `Counter` in the current scope
  --> ex.rs:16:22
   |
 2 | struct Counter { n: u32 }
   | -------------- method `build` not found for this struct
...
16 |     println!("{}", c.build().n);
   |                      ^^^^^ this is an associated function, not a method
   |
   = note: found the following associated functions; to be used as methods, functions must have a `self` parameter
note: candidate #1 is defined in the trait `Make`
  --> ex.rs:4:14
   |
 4 | trait Make { fn build() -> Self; }
   |              ^^^^^^^^^^^^^^^^^^^
note: candidate #2 is defined in an impl for the type `Counter`
  --> ex.rs:7:5
   |
 7 |     fn build() -> Self { Counter { n: 0 } }
   |     ^^^^^^^^^^^^^^^^^^
help: disambiguate the associated function for candidate #1
   |
16 -     println!("{}", c.build().n);
16 +     println!("{}", <Counter as Make>::build().n);
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★★ **`candidate #1` 은 트레이트, `candidate #2` 는 고유 `impl`** 이라고 **자리까지 갈라서** 말한다.
그리고 `<Counter as Make>::build()` 라는 **완전 수식 문법**을 고친 코드로 준다.

**메서드는 `impl` 안에 있는데 트레이트가 스코프에 없으면** — 또 다른 문구가 나온다.

```text
===== 소스: ex.rs =====
// 메서드는 impl 안에 있는데 트레이트가 스코프에 없으면 — 진단이 어느 impl 을 짚나
mod shape {
    pub trait Area { fn area(&self) -> f64; }
    pub struct Square { pub side: f64 }
    impl Area for Square { fn area(&self) -> f64 { self.side * self.side } }
}

use shape::Square;

fn main() {
    let s = Square { side: 3.0 };
    println!("{}", s.area());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `area` found for struct `Square` in the current scope
  --> ex.rs:12:22
   |
 3 |     pub trait Area { fn area(&self) -> f64; }
   |                         ---- the method is available for `Square` here
 4 |     pub struct Square { pub side: f64 }
   |     ----------------- method `area` not found for this struct
...
12 |     println!("{}", s.area());
   |                      ^^^^ method not found in `Square`
   |
   = help: items from traits can only be used if the trait is in scope
help: trait `Area` which provides `area` is implemented but not in scope; perhaps you want to import it
   |
 2 + use crate::shape::Area;
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`the method is available for Square here`** — 「찾았는데 부를 수 없다」다.
★★ **E0599 한 번호에 문구가 넷이었다**(이 문서 실측): `method not found` · `this is an associated function, not a method` ·
`trait bounds were not satisfied` · `items from traits can only be used if the trait is in scope`.
**번호만 외우면 네 가지가 한 덩어리가 된다 — 읽을 것은 문구다.**

### (8) ★ 크기와 정렬 — 0바이트인 것들

**언제 쓰나** — 「유닛 구조체를 만들면 메모리를 얼마나 쓰나」가 궁금할 때, 그리고 newtype 의 대가를 잴 때.

```text
===== 소스: ex.rs =====
// 유닛 구조체·튜플 구조체·이름 있는 구조체의 크기와 정렬을 전부 찍는다
use std::mem::{align_of, size_of};

struct Unit;                       // 유닛 구조체
struct Empty();                    // 빈 튜플 구조체
struct Newtype(u64);               // 필드 하나인 튜플 구조체(newtype)
struct Pair(u8, u32);              // 필드 둘인 튜플 구조체
struct Named { a: u8, b: u32 }     // 이름 있는 구조체
struct Reordered { b: u32, a: u8 } // 같은 필드, 선언 순서만 바꿈

fn row(name: &str, size: usize, align: usize) {
    println!("{:<10} size={} align={}", name, size, align);
}

fn main() {
    row("Unit", size_of::<Unit>(), align_of::<Unit>());
    row("Empty", size_of::<Empty>(), align_of::<Empty>());
    row("Newtype", size_of::<Newtype>(), align_of::<Newtype>());
    row("u64", size_of::<u64>(), align_of::<u64>());
    row("Pair", size_of::<Pair>(), align_of::<Pair>());
    row("Named", size_of::<Named>(), align_of::<Named>());
    row("Reordered", size_of::<Reordered>(), align_of::<Reordered>());
    row("()", size_of::<()>(), align_of::<()>());
    row("[u8; 0]", size_of::<[u8; 0]>(), align_of::<[u8; 0]>());

    // 필드를 실제로 읽어 dead_code 경고를 없앤다
    let n = Newtype(7);
    let p = Pair(1, 2);
    let s = Named { a: 3, b: 4 };
    let r = Reordered { b: 5, a: 6 };
    let _ = (Unit, Empty());
    println!("값 확인: {} {} {} {} {} {}", n.0, p.0, p.1, s.a, s.b, r.a + r.b as u8);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Unit       size=0 align=1
Empty      size=0 align=1
Newtype    size=8 align=8
u64        size=8 align=8
Pair       size=8 align=4
Named      size=8 align=4
Reordered  size=8 align=4
()         size=0 align=1
[u8; 0]    size=0 align=1
값 확인: 7 1 2 3 4 11
(종료 코드 0)
```

읽는 법.

- ★★ **0바이트인 것이 넷이다** — 유닛 구조체 `Unit` · 빈 튜플 구조체 `Empty()` · 유닛 타입 `()` · 빈 배열 `[u8; 0]`.
  **값은 있는데 저장할 것이 없다.** 이런 타입을 **ZST**(zero-sized type)라고 부른다.
- **정렬은 넷 다 `1`** 이다 — `0` 이 아니다. 정렬은 **최소 1**이라 크기가 0이어도 1이 나온다.
- ★ **newtype 은 안쪽 타입과 크기·정렬이 같다** — `Newtype(u64)` 도 `u64` 도 `8/8`.
  **감싸는 비용이 0**이라는 것이 newtype 관용구의 근거다([목록의 **26번 주제**](../26-orphan-rule-and-newtype/)가 정본).
- `Pair(u8, u32)` · `Named { a: u8, b: u32 }` · `Reordered { b: u32, a: u8 }` 가 **전부 `8/4`** 다 —
  이름이 있든 번호든, 선언 순서가 어떻든 **같은 값이 나왔다.**

★★ **그런데 「순서를 바꿔도 크기가 같다」는 언어 보장이 아니라 구현 세부다.** 기본 표현 `repr(Rust)` 는
**필드를 재배치할 수 있다.** 실제로 재배치했다 — 주소를 직접 재서 확인한다.

```text
===== 소스: ex.rs =====
// 필드가 실제로 어느 자리에 놓이나 — repr(Rust) 대 repr(C)
struct Named { a: u8, b: u32 }

#[repr(C)]
struct NamedC { a: u8, b: u32 }

fn main() {
    let s = Named { a: 1, b: 2 };
    let base = &s as *const Named as usize;
    println!("repr(Rust)  size={}  a@{}  b@{}",
             std::mem::size_of::<Named>(),
             (&s.a as *const u8 as usize) - base,
             (&s.b as *const u32 as usize) - base);

    let c = NamedC { a: 1, b: 2 };
    let basec = &c as *const NamedC as usize;
    println!("repr(C)     size={}  a@{}  b@{}",
             std::mem::size_of::<NamedC>(),
             (&c.a as *const u8 as usize) - basec,
             (&c.b as *const u32 as usize) - basec);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
repr(Rust)  size=8  a@4  b@0
repr(C)     size=8  a@0  b@4
(종료 코드 0)
```

★★ **`repr(Rust)` 에서 `a` 가 4번 바이트, `b` 가 0번 바이트에 놓였다** — **선언 순서와 반대**다.
`#[repr(C)]` 를 붙이면 선언 순서대로 `a@0`·`b@4` 가 된다.
**「선언 순서대로 놓인다」고 가정한 코드는 `repr(Rust)` 에서 틀린다.**

> ★ **대조할 것은 숫자가 아니라 「기본 표현에서는 순서가 보장되지 않는다」는 성질이다.**\
> 이 오프셋은 **rustc 판과 대상 플랫폼에 달렸다.** 같은 툴체인·같은 머신에서는 재현되지만,
> **다음 판에서 달라져도 그것은 버그가 아니다.** `repr(C)` 쪽만 고정이다.

```text
   size_of 가 0 인 것들과 그 쓰임

   struct Unit;        0바이트   ← 타입만으로 뜻을 나르는 표식 (상태·단계·권한)
   struct Empty();     0바이트   ← 같은 것. 튜플 문법으로 쓴 것뿐
   ()                  0바이트   ← 「값이 없다」는 값. 함수의 기본 반환 타입
   [u8; 0]             0바이트   ← 길이 0 배열

   Vec<Unit> 를 만들어도 힙 할당이 안 일어난다 — 담을 바이트가 없다.
   HashSet<K> 가 HashMap<K, ()> 로 구현되는 것도 같은 이유다.
```

### (9) 필드는 기본 비공개다

**언제 쓰나** — 타입을 `mod` 로 감싸는 순간부터. **같은 모듈 안에서는 아무 제약이 없다.**

```text
===== 소스: ex.rs =====
// 같은 모듈 안에서는 필드가 다 보이나 — mod 로 감싸면?
mod geo {
    pub struct Point { pub x: i32, y: i32 }   // y 에만 pub 이 없다

    impl Point {
        pub fn new(x: i32, y: i32) -> Self { Point { x, y } }
        pub fn y(&self) -> i32 { self.y }     // 같은 모듈 안에서는 y 가 보인다
    }

    struct Hidden { pub v: i32 }              // 타입 자체에 pub 이 없다
    impl Hidden { pub fn new() -> Self { Hidden { v: 1 } } }
}

fn main() {
    let p = geo::Point::new(1, 2);
    println!("x = {}", p.x);
    println!("y() = {}", p.y());
    println!("y  = {}", p.y);
    let h = geo::Hidden::new();
    println!("{}", h.v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0603]: struct `Hidden` is private
  --> ex.rs:19:18
   |
19 |     let h = geo::Hidden::new();
   |                  ^^^^^^ private struct
   |
note: the struct `Hidden` is defined here
  --> ex.rs:10:5
   |
10 |     struct Hidden { pub v: i32 }              // 타입 자체에 pub 이 없다
   |     ^^^^^^^^^^^^^

error[E0616]: field `y` of struct `Point` is private
  --> ex.rs:18:27
   |
18 |     println!("y  = {}", p.y);
   |                           ^ private field
   |
help: a method `y` also exists, call it with parentheses
   |
18 |     println!("y  = {}", p.y());
   |                            ++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0603, E0616.
For more information about an error, try `rustc --explain E0603`.
```

★ **두 에러가 다른 것을 가린다.**

| 번호 | 무엇이 안 보이나 | 고치는 법 |
|---|---|---|
| **E0603** | **타입 자체**가 비공개 | `pub struct Hidden` |
| **E0616** | 타입은 보이는데 **필드**가 비공개 | `pub y: i32` 또는 **접근자 메서드** |

- ★ `pub struct Point { pub x, y }` 처럼 **칸마다 따로** 정한다. `pub` 을 타입에 붙였다고 필드까지 열리지 않는다.
- ★★ **E0616 의 `help:` 가 같은 이름의 메서드를 권한다** — `p.y` 가 막히자 **`p.y()` 를 쓰라고** 한다.
  이것이 (10)의 「필드와 메서드 동명」과 이어지는 자리다. **접근자를 필드와 같은 이름으로 짓는 관용구**가 여기서 나온다.
- **같은 모듈 안에서는 `y` 가 그냥 보인다** — `impl Point` 의 `pub fn y(&self)` 가 `self.y` 를 읽는 데 아무 표시가 없었다.

★ 모듈 시스템 자체(`pub(crate)`·경로·파일 배치)는 목록의 **45번 주제**가 정본이다.
여기는 **「구조체의 필드가 기본 비공개」까지**만 다룬다.

### (10) 필드와 메서드가 이름이 같아도 되나

**언제 쓰나** — 접근자를 만들 때. **된다** — 이름 공간이 다르기 때문이다.

```text
===== 소스: ex.rs =====
// 필드와 메서드가 이름이 같아도 되나 — 그리고 필드가 클로저일 때는 어떻게 부르나
struct Widget {
    width: u32,
    render: Box<dyn Fn() -> String>,
}

impl Widget {
    fn width(&self) -> u32 { self.width * 2 }       // 필드와 같은 이름
    fn render(&self) -> String { String::from("메서드 render") }
}

fn main() {
    let w = Widget { width: 10, render: Box::new(|| String::from("필드 render")) };

    println!("필드   w.width   = {}", w.width);
    println!("메서드 w.width() = {}", w.width());
    println!("메서드 w.render() = {}", w.render());
    println!("필드   (w.render)() = {}", (w.render)());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
필드   w.width   = 10
메서드 w.width() = 20
메서드 w.render() = 메서드 render
필드   (w.render)() = 필드 render
(종료 코드 0)
```

★★ **된다.** 그리고 **괄호 하나가 둘을 가른다.**

```text
   s.f   와  s.f()  는 서로 다른 이름 공간을 본다

   s.f        → 필드 f
   s.f()      → 메서드 f   ★ 필드가 함수여도 메서드가 이긴다
   (s.f)()    → 필드 f 를 꺼내서 호출   ← 괄호로 「먼저 필드를 읽어라」를 강제
```

**메서드가 없고 클로저 필드만 있을 때 `.` 으로 부르면** — 진단이 괄호를 권한다.

```text
===== 소스: ex.rs =====
// 클로저 필드를 메서드처럼 부르면
struct Widget { render: Box<dyn Fn() -> String> }

fn main() {
    let w = Widget { render: Box::new(|| String::from("필드 render")) };
    println!("{}", w.render());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `render` found for struct `Widget` in the current scope
 --> ex.rs:6:22
  |
2 | struct Widget { render: Box<dyn Fn() -> String> }
  | ------------- method `render` not found for this struct
...
6 |     println!("{}", w.render());
  |                      ^^^^^^ field, not a method
  |
help: to call the trait object stored in `render`, surround the field access with parentheses
  |
6 |     println!("{}", (w.render)());
  |                    +        +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ **`field, not a method`** — (3)의 `associated function, not a method` 와 짝이다.
**E0599 는 「메서드가 아닌 무엇이 그 이름을 쓰고 있다」를 세 가지로 갈라 말한다**(연관 함수 · 필드 · 스코프 밖 트레이트).

### (11) 구조체 생성에서 나는 에러 둘, 그리고 `Debug` 맛보기

**언제 쓰나** — 필드를 더하거나 이름을 바꾼 직후. **컴파일러가 전수로 잡아 준다.**

```text
===== 소스: ex.rs =====
// 필드를 빠뜨리면 · 없는 필드를 주면
struct Point { x: i32, y: i32, z: i32 }

fn main() {
    let a = Point { x: 1 };
    let b = Point { x: 1, y: 2, z: 3, w: 4 };
    println!("{} {}", a.x, b.x);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0063]: missing fields `y` and `z` in initializer of `Point`
 --> ex.rs:5:13
  |
5 |     let a = Point { x: 1 };
  |             ^^^^^ missing `y` and `z`

error[E0560]: struct `Point` has no field named `w`
 --> ex.rs:6:39
  |
6 |     let b = Point { x: 1, y: 2, z: 3, w: 4 };
  |                                       ^ `Point` does not have this field
  |
  = note: all struct fields are already assigned

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0063, E0560.
For more information about an error, try `rustc --explain E0063`.
```

★ **E0063**(빠뜨림)과 **E0560**(없는 필드)이 갈린다. **필드를 하나 더하면 모든 생성 자리가 E0063 으로 깨진다** —
이것이 「불가능한 상태를 컴파일러가 막는다」의 가장 싼 형태다. `..Default::default()` 를 쓰면 그 그물이 사라지므로
**새 필드를 놓치고 싶지 않은 타입에는 안 쓴다.**

**`#[derive(Debug)]` 없이 `{:?}` 를 쓰면.**

```text
===== 소스: ex.rs =====
// derive(Debug) 없이 {:?} 를 쓰면
struct Point { x: i32, y: i32 }

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("{:?}", p);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: `Point` doesn't implement `Debug`
 --> ex.rs:6:22
  |
6 |     println!("{:?}", p);
  |               ----   ^ `Point` cannot be formatted using `{:?}` because it doesn't implement `Debug`
  |               |
  |               required by this formatting parameter
  |
  = help: the trait `Debug` is not implemented for `Point`
  = note: add `#[derive(Debug)]` to `Point` or manually `impl Debug for Point`
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider annotating `Point` with `#[derive(Debug)]`
  |
2 + #[derive(Debug)]
3 | struct Point { x: i32, y: i32 }
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

★ **E0277** — 「트레이트가 구현 안 됐다」다. 이 진단도 **고친 코드를 그대로 준다**(`2 + #[derive(Debug)]`).

**`{:?}` 와 `{:#?}` 의 차이** — 세 형태에 각각 어떻게 나오나.

```text
===== 소스: ex.rs =====
// {:?} 와 {:#?} 는 무엇이 다른가 — 세 종류를 다 찍어 본다
#[derive(Debug)]
struct Point { x: i32, y: i32 }
#[derive(Debug)]
struct Meters(f64);
#[derive(Debug)]
struct Marker;

fn main() {
    let p = Point { x: 1, y: 2 };
    println!("합    {}", p.x + p.y);          // 필드를 실제로 읽는다(dead_code 경고 제거)
    println!("{:?}", p);
    println!("{:#?}", p);
    let m = Meters(1.5);
    println!("안쪽  {}", m.0);
    println!("{:?} / {:#?}", m, Meters(1.5));
    println!("{:?} / {:#?}", Marker, Marker);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
합    3
Point { x: 1, y: 2 }
Point {
    x: 1,
    y: 2,
}
안쪽  1.5
Meters(1.5) / Meters(
    1.5,
)
Marker / Marker
(종료 코드 0)
```

- **`{:?}`** 는 한 줄, **`{:#?}`** 는 **여러 줄에 4칸 들여쓰기 + 꼬리 쉼표**다.
- ★ **세 형태가 각각 다르게 찍힌다** — 이름 있는 것은 `{ }`, 튜플은 `( )`, 유닛은 **이름만**.
  `{:?}` 출력만 봐도 **어느 형태인지 읽을 수 있다.**
- `derive` 자체(무엇을 요구하나·언제 안 되나)는 [목록의 **27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)가 정본이다. 여기는 맛만 본다.

## 문법 — 형태와 규칙

### 형태

```rust
// 1) 이름 있는 구조체 — 칸마다 이름
struct Point { x: i32, y: i32 }
let p = Point { x: 1, y: 2 };
let Point { x, y } = p;

// 2) 튜플 구조체 — 칸마다 번호. 세미콜론이 필요하다
struct Meters(f64);
let m = Meters(1.5);
let Meters(v) = m;

// 3) 유닛 구조체 — 칸이 없다. 세미콜론이 필요하다
struct Marker;
let k = Marker;

// 4) 필드 초기화 축약 — 이름이 같을 때만
fn make(x: i32, y: i32) -> Point { Point { x, y } }

// 5) 구조체 갱신 문법 — 반드시 마지막. 뒤에 쉼표 없음
let q = Point { x: 10, ..p };

// 6) impl — 연관 함수(self 없음)와 메서드(self 있음)
impl Point {
    const ORIGIN: Self = Self { x: 0, y: 0 };   // 연관 상수 (1.20.0부터)
    fn new(x: i32, y: i32) -> Self { Self { x, y } }   // 연관 함수
    fn sum(&self) -> i32 { self.x + self.y }           // 메서드 (&self)
    fn shift(&mut self, d: i32) { self.x += d; }       // 메서드 (&mut self)
    fn into_pair(self) -> (i32, i32) { (self.x, self.y) }  // 메서드 (self)
}

// 7) 호출 — 두 형태는 같은 것이다
let a = Point::new(1, 2);
let s1 = a.sum();
let s2 = Point::sum(&a);       // ★ 완전히 같다

// 8) impl 블록을 여럿 — 경계별로 가른다
struct Wrapper<T> { inner: T }
impl<T> Wrapper<T> { fn new(inner: T) -> Self { Wrapper { inner } } }
impl<T: std::fmt::Display> Wrapper<T> { fn show(&self) -> String { format!("{}", self.inner) } }

// 9) 가시성 — 타입과 필드를 따로 연다
pub struct Config { pub name: String, secret: u32 }
```

### 금지 사례 — 던져서 받은 열둘

| 코드 | 에러 | 한 줄 |
|---|---|---|
| `Point { x: 1 }`(칸 셋짜리) | **E0063** | 빠뜨린 칸을 이름으로 대 준다 |
| `Point { x, y, z, w }` | **E0560** | 없는 필드 |
| `let f = Point;`(이름 있는 구조체) | **E0423** | 이름은 **타입 이름일 뿐**이다 |
| `c.new()`(연관 함수를 `.` 으로) | **E0599** | `this is an associated function, not a method` |
| `Counter::get()`(메서드를 `::` 으로) | **E0061** | ★ 문법은 맞다 — **인자가 빈 것**이다 |
| `c.increment()`(없는 이름) | **E0599** | 비슷한 이름만 제안. `impl` 블록은 안 나열한다 |
| `b.show()`(경계 불만족) | **E0599** | `exists … but its trait bounds were not satisfied` |
| `fn get` 을 두 `impl` 에 | **E0592** (+ 호출부 **E0034**) | 정의 쪽과 호출 쪽이 따로 난다 |
| `w.render()`(클로저 필드) | **E0599** | `field, not a method`. `(w.render)()` 를 권한다 |
| `p.y`(다른 모듈의 비공개 필드) | **E0616** | 같은 이름 메서드를 권한다 |
| `geo::Hidden`(비공개 타입) | **E0603** | 타입 자체가 안 보인다 |
| `println!("{:?}", p)`(derive 없이) | **E0277** | `#[derive(Debug)]` 를 통째로 준다 |
| `fn make() -> Self`(`impl` 밖) | **E0411** | `Self` 는 impl·trait·타입 정의 안에서만 |
| `Self`(이름 있는 구조체의 값 자리) | **번호 없음** | `the Self constructor can only be used with tuple or unit structs` |
| `..base` 뒤에 `base` 를 다시 | **E0382** | `partially moved` — 칸마다 따로 이동한다 |
| `c.bump()`(`mut` 아닌 `let`) | **E0596** | `.` 하나가 `&mut c` 를 만든다 |
| `b.build()` 두 번(`self` 리시버) | **E0382** | `takes ownership of the receiver self` |

### 고를 것을 손으로 돌리는 순서

```text
   새 타입을 만든다
        │
        ▼
   ① 담을 데이터가 있나? ── 아니오 ──▶ 유닛 구조체 `struct X;`  (0바이트)
        │ 예
        ▼
   ② 칸이 하나뿐이고 「무엇인지」가 타입 이름으로 충분한가?
        │ 예 ──▶ 튜플 구조체 `struct X(T);`  (newtype — 안쪽과 같은 크기)
        │ 아니오
        ▼
   ③ 이름 있는 구조체 `struct X { .. }`
        │
        ▼
   ④ 동작을 붙인다 — `impl X { .. }`
        │
        ├ 값을 만들거나 타입 전체에 관한 일이다 ──▶ 연관 함수 (self 없음)
        └ 한 값을 두고 하는 일이다 ──▶ 메서드
              ├ 읽기만    ──▶ &self       (먼저 이것으로 쓴다)
              ├ 고친다    ──▶ &mut self   (호출부에 mut 를 요구한다)
              └ 소비한다  ──▶ self        (호출부가 그 값을 잃는다)
```

## 어디서 틀리나

### 1. ★★ 「메서드와 연관 함수는 이름 규칙이 다르다」

- 아니다. **가르는 것은 「첫 인자가 `self` 인가」 하나뿐**이다. `new` 라는 이름에는 아무 특별함이 없다.
- 실측: `c.new()` 는 **E0599** 로, `Counter::get()` 은 **E0061** 로 갈린다((3)).
- ★ **`Counter::get(&c)` 는 올바른 호출**이다. `c.get()` 이 그 줄임이므로 **두 방향의 에러가 비대칭**이다.

### 2. ★★ 「`Self` 와 `self` 는 대소문자만 다른 같은 것」

- **`Self` 는 타입, `self` 는 값**이다. 자리가 아예 다르다.
- 실측: 이름 있는 구조체에서 `Self` 를 값으로 쓰면 **번호 없는 error** 가 난다((4)).
- ★ `self: &Self` 가 `&self` 의 원래 형태다 — **`Self` 가 리시버 타입 자리에도 나온다**는 것이 둘의 관계를 보여 준다.
- ★ `Self` 는 `impl`·`trait`·타입 정의 **안에서만** 이름이 있다(**E0411**).

### 3. ★★ 「`..other` 는 나머지를 복사한다」

- **칸마다 따로 이동**한다. `Copy` 가 아닌 칸이 하나라도 있으면 원본이 **부분 이동**된다((2)).
- 실측: `String` 칸 하나 때문에 **E0382 `borrow of partially moved value`** 가 났다.
- ★ 그래서 `..base` 뒤에 `base` 를 쓰려면 **`..base.clone()`** 이거나 모든 칸이 `Copy` 여야 한다.

### 4. ★ 「`impl` 은 타입당 하나여야 한다」

- **몇 개든 된다.** 이름만 겹치지 않으면 경고도 없다((6)).
- 겹치면 **정의 쪽 E0592 + 호출 쪽 E0034** 가 같이 난다.
- ★ 여럿 두는 **실제 이유는 제네릭 경계**다 — `impl<T: Display> Wrapper<T>` 의 메서드는 **`T` 가 `Display` 일 때만 생긴다.**

### 5. ★ 「메서드를 못 찾으면 그 이름이 없는 것이다」

- E0599 한 번호에 **문구가 넷**이었다((7)) — 없다 / 연관 함수다 / 경계 불만족 / 트레이트가 스코프 밖.
- 뒤의 셋은 「**있는데 못 쓴다**」이고 처방이 전부 다르다. **번호가 아니라 문구를 읽는다.**
- ★ 진단은 **뒤진 `impl` 블록을 나열해 주지 않는다.** 나열은 **후보가 실제로 있을 때**만 `candidate #N` 으로 나온다.

### 6. ★ 「유닛 구조체는 쓸모없다」

- **0바이트**라서 쓸모가 있다((8)). 타입만으로 뜻을 나르고 **런타임 비용이 없다.**
- 실측: `Unit`·`Empty()`·`()`·`[u8; 0]` 이 전부 `size=0 align=1`.
- ★ `align` 이 **0이 아니라 1**이다 — 정렬의 최솟값이 1이다.

### 7. ★★ 「필드는 선언한 순서대로 메모리에 놓인다」

- **기본 표현 `repr(Rust)` 에서는 보장되지 않는다.** 실측에서 `{ a: u8, b: u32 }` 가 **`a@4`·`b@0`** 으로 뒤집혔다((8)).
- 순서를 고정해야 하면 **`#[repr(C)]`** 를 붙인다 — 붙이면 `a@0`·`b@4` 가 된다.
- ★ 「순서를 바꿔도 크기가 같더라」는 **관찰**이지 보장이 아니다.

### 8. ★ 「필드와 메서드 이름이 같으면 충돌한다」

- **안 한다.** 이름 공간이 다르다 — `s.f` 는 필드, `s.f()` 는 메서드((10)).
- ★ 필드가 클로저면 **`(s.f)()`** 로 괄호를 씌워야 한다. 안 씌우면 **E0599 `field, not a method`** 다.
- ★ 이것이 **접근자를 필드와 같은 이름으로 짓는 관용구**의 근거다. E0616 의 `help:` 도 그 관용구를 권한다.

### 9. `pub struct` 를 썼으니 필드도 열렸다고 생각한다

- **칸마다 따로** 연다. 타입에 `pub` 을 붙여도 필드는 **여전히 비공개**다((9)).
- **E0603**(타입이 비공개)과 **E0616**(필드가 비공개)은 다른 에러다.

### 10. `&mut self` 를 먼저 쓴다

- **`&self` 가 기본값**이다. `&mut self` 를 붙이는 순간 **호출부가 `mut` 바인딩을 갖춰야 하고**(E0596)
  **그 동안 다른 빌림을 못 낸다**(E0502).
- ★ `&self` 메서드 하나가 **값 전체**를 잡는다 — 읽은 것이 필드 하나여도 그렇다((5)).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 구조체가 **세 형태**인 것 | **언어** | Reference — Structs · (1)의 실측 |
| 메서드 = **첫 인자가 `self` 인 연관 함수** | **언어** | Reference — Associated Items · (3)의 `= note:` |
| `a.m()` 와 `T::m(&a)` 가 **같은 것** | **언어** | E0061 이 `argument #1 of type &Counter` 를 요구 |
| `..other` 가 **칸마다 이동**인 것 | **언어** | E0382 `partially moved` 실측 |
| 같은 타입에 **`impl` 이 여럿** 되는 것 | **언어** | (6) 통과 실측 |
| 같은 이름 중복이 **거부되는** 것 | **언어** | E0592 + E0034 |
| 필드와 메서드가 **다른 이름 공간**인 것 | **언어** | (10) 통과 실측 |
| 필드가 **기본 비공개**인 것 | **언어** | E0616 실측 |
| `Self` 가 **impl·trait·타입 정의 안에서만** 있는 것 | **언어** | E0411 의 진단 문구 그대로 |
| 유닛 구조체·`()`·`[u8; 0]` 이 **0바이트** | **언어**(ZST 는 언어 개념) | `size_of` 실측 — 넷 다 `0` |
| newtype 이 **안쪽과 같은 크기**인 것 | ★ **구현**(보장 아님) | `Newtype(u64)` 도 `u64` 도 `8/8` — Reference 는 단일 필드 레이아웃을 **약속하지 않는다** |
| **필드 순서 재배치** | ★ **구현 세부** | `repr(Rust)` 에서 `a@4`·`b@0`. `#[repr(C)]` 면 `a@0`·`b@4` |
| `Named`·`Reordered` 가 **같은 크기**인 것 | ★ **관찰** | 둘 다 `8/4` — 순서 무관이 보장된 것이 아니다 |
| `#[repr(C)]` 의 **선언 순서 유지** | **언어**(그 어트리뷰트의 정의) | Reference — Type layout · `a@0`·`b@4` |
| `align_of` 의 **최솟값이 1** | **언어** | ZST 넷이 전부 `align=1` |
| **에러 번호**가 상황별로 갈리는 것 | **rustc 구현** | 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| ★ **E0599 한 번호에 문구가 넷** | **rustc 구현** | (7) — 없다/연관 함수/경계/스코프 |
| ★ **번호 없는 진단이 있는 것** | **rustc 구현** | `the Self constructor can only be used with …` |
| `candidate #1`·`#2` **나열** | **rustc 의 진단 표기** | E0034 · E0599 |
| `cargo doc` 이 **블록을 안 합치는** 것 | **rustdoc 구현** | 앵커 `impl-Wrapper%3CT%3E`·`-1`·`-2` |
| 앵커 id 의 **`%3C` 인코딩과 `-1` 접미** | **rustdoc 구현** | 판이 바뀌면 달라질 수 있는 표기다 |
| `{:#?}` 의 **4칸 들여쓰기** | **std 의 `Formatter` 구현** | 실측 — 형식은 std 가 정한다 |

★ **「구현 세부」가 이 주제에서 몰리는 곳은 메모리 레이아웃**이다.
`size_of` 값은 재현됐지만 **재현됐다는 것이 보장은 아니다** — `repr(Rust)` 는 재배치할 자유를 명시적으로 갖고 있고,
실제로 **이 실측에서 재배치했다**. 고정이 필요하면 `#[repr(C)]` 를 적는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 칸이 둘 이상이고 뜻이 다르다 | **이름 있는 구조체** | 호출부가 이름으로 읽는다. 순서를 안 외워도 된다 |
| 칸이 하나고 「단위·의미」를 붙이는 것이다 | **튜플 구조체**(newtype) | 크기 비용이 0이고 `.map(Meters)` 로 넘길 수 있다 |
| 담을 데이터가 없다 | **유닛 구조체** | 0바이트. 타입 자체가 정보다 |
| 생성자를 만든다 | **연관 함수 `fn new() -> Self`** | `new` 는 관례일 뿐 특별한 문법이 아니다 |
| 읽기만 하는 동작 | **`&self`** | 기본값. 동시에 여럿 된다 |
| 자기 상태를 고친다 | **`&mut self`** | 호출부가 `mut` 를 갖춰야 한다(E0596) |
| 값을 변환하거나 소비한다 | **`self`** | 빌더·`into_*`. 호출부가 원본을 잃는다 |
| 경계가 있는 메서드를 단다 | **`impl` 블록을 갈라 쓴다** | 경계 밖 타입에서도 나머지 메서드가 산다 |
| 필드를 밖에 연다 | ★ **`pub` 을 칸마다** | 타입의 `pub` 은 필드까지 열지 않는다 |
| 필드를 열되 읽기만 시킨다 | **비공개 필드 + 같은 이름 접근자** | E0616 의 `help:` 가 권하는 관용구 |
| 메모리 배치를 고정해야 한다 | **`#[repr(C)]`** | 기본 표현은 순서를 보장하지 않는다 |
| 필드를 더해도 안 깨지게 하고 싶다 | ★ **쓰지 않는다** | E0063 이 깨뜨려 주는 것이 **안전망**이다 |
| 참조를 필드에 담는다 | [목록의 **13번 주제**](../13-struct-references-and-static/) | `struct X<'a>` 의 제약은 거기가 정본이다 |
| 상속으로 공통 동작을 뽑고 싶다 | ★ **트레이트** | Rust 에 상속은 없다 — [목록의 **25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/) |

판단 규칙 두 줄.

- **먼저 `&self` 로 쓴다.** 컴파일러가 막으면 그때 `&mut self` 로 올리고, 값을 소비해야 할 때만 `self` 로 간다.
- **`impl` 은 나눠도 공짜다.** 합치는 이유는 없고, 나누는 이유는 있다(경계·주제·문서).

## 핵심 문장

- ★★ **구조체와 `impl` 은 분리돼 있다** — 그래서 `impl` 블록을 몇 개든 둘 수 있고, **경계별로 가르면 메서드가 조건부로 생긴다.**
- ★★ **연관 함수와 메서드를 가르는 것은 「첫 인자가 `self` 인가」 하나뿐**이다. 메서드는 연관 함수의 **부분집합**이다.
- ★ **`a.m()` 와 `T::m(&a)` 는 같은 것**이다 — 메서드를 `::` 으로 부르면 **E0061**(인자 부족)이지 문법 에러가 아니다.
- ★★ **`Self` 는 타입, `self` 는 값**이다. `Self` 는 **타입 자리 · 값/패턴 자리 · 경로 한정자 자리** 셋으로 나온다.
- ★ **`..other` 는 칸마다 따로 이동한다** — `Copy` 아닌 칸이 있으면 원본이 **부분 이동**된다(E0382).
- ★★ **유닛 구조체·빈 튜플 구조체·`()`·`[u8; 0]` 은 `size_of` 가 0이다.** 정렬은 1이다.
- ★ **newtype 은 안쪽 타입과 크기가 같았다** — 다만 그것은 **구현 세부**다.
- ★★ **기본 표현 `repr(Rust)` 는 필드를 재배치한다.** 실측에서 `{ a: u8, b: u32 }` 가 `a@4`·`b@0` 으로 뒤집혔다.
- ★ **E0599 는 한 번호에 문구가 넷**이다 — 없다 / 연관 함수다 / 경계 불만족 / 트레이트가 스코프 밖. **번호가 아니라 문구를 읽는다.**
- ★ **필드와 메서드는 이름 공간이 다르다** — `s.f` 와 `s.f()`. 필드가 클로저면 `(s.f)()`.
- **필드는 기본 비공개다** — 타입의 `pub` 과 필드의 `pub` 은 따로다(E0603 대 E0616).
- ★ **`cargo doc` 은 `impl` 블록을 안 합친다** — 나눠 쓴 모양이 문서에 그대로 남는다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 16번)
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — ★ **직접 선행**(README 지정).\
  **그쪽은** 「값이 언제 복사되고 언제 죽나」, **여기는** 「그 값을 담을 타입을 직접 만들고 동작을 붙이는 법」이다.\
  `..other` 가 칸마다 갈리는 근거가 거기 있다
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — **E0382 의 뿌리**.\
  **그쪽은** 이동 일반, **여기는** 그 이동이 **`self` 리시버와 `..other`** 에서 일어나는 모양이다
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`) — **`&self`/`&mut self` 선택의 근거**.\
  **그쪽은** 「한 시점에 누가 몇 명 빌리나」, **여기는** 「그 규칙이 메서드 시그니처가 되는 자리」다
- [**11번 주제**](../11-borrow-checker-rejections/)(빌림 검사기가 거부하는 전형) — **형제**.\
  (5)의 E0502 를 **분할 빌림으로 푸는 처방**은 거기가 정본이다
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기와 생략) — 메서드의 **생략 규칙 3**(`&self` 가 출력 수명을 가져간다)이 거기다.\
  **여기는** 리시버가 **소유권**에 하는 일까지
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(`mut` 와 섀도잉) — E0596 의 `let mut` 가 거기서 나온다
- [`../../../../oop-basics/`](../../../../oop-basics/) — ★ **경계 선언**.\
  **그쪽은** 객체·캡슐화·상속·다형성 **일반**(클래스가 무엇인가, 정보 은닉이 왜 필요한가),\
  **여기는** **Rust 의 구조체 세 종류와 `impl` 문법**이다.\
  ★ Rust 에는 **클래스도 상속도 없다** — 데이터는 `struct`, 동작은 `impl`, 공통 표면은 트레이트로 갈라져 있다
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — Rust 를 **고를 것인가**의 논증은 거기
- [목록의 **13번 주제**](../13-struct-references-and-static/)(구조체에 참조 담기·`'static`) — ★ **참조를 필드로 담는 구조체는 거기가 정본**이다.\
  **여기는** 소유한 값을 담는 구조체까지 — `struct X<'a> { r: &'a str }` 의 제약은 다루지 않는다
- [목록의 **17번 주제**](../17-enums-and-data-carrying-variants/)(열거형) — 구조체가 「**전부 다 있다**」면 열거형은 「**하나만이다**」다
- [목록의 **25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)(트레이트) — `impl Trait for Type` 은 거기. **여기는 고유 `impl`(inherent impl)만**
- [목록의 **26번 주제**](../26-orphan-rule-and-newtype/)(고아 규칙과 newtype) · **27번 주제**(`derive`) · **45번 주제**(모듈·가시성) ·\
  **48번 주제**(`Display`/`Debug` 구현) — 각각 (8)·(11)·(9)·(11)에서 맛만 본 것들의 정본

## 용어 풀이

- **구조체(struct)** — 값 여럿을 한 이름으로 묶은 사용자 정의 타입. 이름 있는·튜플·유닛 세 형태.
- **튜플 구조체(tuple struct)** — 칸에 번호만 있는 구조체. `.0`·`.1` 로 접근한다. **이름이 생성자 함수이기도 하다.**
- **유닛 구조체(unit struct)** — 칸이 없는 구조체. `size_of` 가 0이다.
- **newtype** — 필드가 하나인 튜플 구조체로 다른 타입을 감싸는 관용구. 크기 비용이 0이었다(실측).
- **ZST(zero-sized type)** — 크기가 0인 타입. 유닛 구조체·`()`·`[T; 0]` 등.
- **`impl` 블록(implementation)** — 타입에 연관 항목을 붙이는 블록. 같은 타입에 여럿 둘 수 있다.
- **고유 impl(inherent impl)** — 트레이트 없이 `impl Type { }` 로 쓰는 블록. 이 주제가 다루는 것.
- **연관 항목(associated item)** — `impl`·트레이트 안의 함수·상수·타입.
- **연관 함수(associated function)** — `impl` 안의 함수 전부. `Type::name()` 으로 부른다.
- **메서드(method)** — 연관 함수 중 첫 인자가 리시버인 것. `value.name()` 으로 부른다.
- **리시버(receiver)** — `self`·`&self`·`&mut self`. `self: Self`·`self: &Self` 의 줄임이다.
- **`Self`** — `impl` 대상 타입의 별명. **타입 자리·값 자리·경로 한정자 자리**에 나온다.
- **필드 초기화 축약(field init shorthand)** — `x: x` 를 `x` 로 줄이는 표기.
- **구조체 갱신 문법(struct update syntax)** — `..other`. 적지 않은 칸을 `other` 에서 **칸마다 가져온다**(이동 포함).
- **부분 이동(partial move)** — 값의 일부 칸만 옮겨진 상태. 남은 칸은 읽히고 값 전체는 못 읽는다.
- **`repr(Rust)`** — 기본 메모리 표현. **필드 재배치를 허용한다.** `#[repr(C)]` 는 선언 순서를 지킨다.
- **포괄 구현(blanket impl)** — `impl<T> Trait for T` 꼴. `cargo doc` 이 별도 절로 모아 보여 준다.

---

## 더 들어가면

- ★ **`impl` 이 몇 개인지는 컴파일 결과에 안 남고 문서에는 남는다.** (7)의 앵커 셋이 그 증거다.\
  「블록을 어떻게 나눌 것인가」는 **API 문서의 목차를 짜는 일**에 가깝다.
- ★★ **연관 상수는 1.20.0부터**다. 그 전에는 `impl` 안에 `const` 를 못 넣어 모듈 상수로 뺐다.\
  `Self::ORIGIN` 처럼 **타입에 딸린 상수**를 쓸 수 있게 된 것이 그때다.
- **`Self` 는 제네릭에서 진가가 난다** — `impl<T> Wrapper<T>` 안에서 `Self` 는 `Wrapper<T>` 다.\
  타입 파라미터를 다시 적지 않아도 되므로 **경계를 바꿔도 몸통이 안 깨진다.**
- ★ **ZST 는 컬렉션에서 실제 이득이 된다** — `HashSet<K>` 가 `HashMap<K, ()>` 로 구현되는 것이 대표다.\
  `Vec<Unit>` 는 길이만 세고 **힙 할당을 하지 않는다**([목록의 **38번 주제**](../38-vec-api-capacity-retain-and-drain/)·**39번 주제**).
- ★ **필드 재배치는 「작은 필드를 큰 필드 뒤로」 옮기는 것만이 아니다.** 실측에서는 반대로 갔다(`a@4`·`b@0`).\
  최적화 목표는 **총 크기 최소화**이지 특정 순서가 아니다 — 그래서 **어느 방향인지 예측하지 마라.**
- **`self` 리시버에 다른 타입도 온다** — `self: Box<Self>`·`self: Rc<Self>` 같은 형태가 있다.\
  `dyn Trait` 를 소비하는 메서드에서 쓰인다([목록의 **33번 주제**](../33-dyn-trait-objects-and-object-safety/)·**40번 주제**).
- ★ **구조체에 참조를 담는 순간 이야기가 달라진다** — 수명 파라미터가 타입에 붙고 `impl<'a> X<'a>` 가 된다.\
  거기서부터는 [목록의 **13번 주제**](../13-struct-references-and-static/)가 정본이다. 이 주제의 예제는 **전부 소유한 값만** 담았다.
