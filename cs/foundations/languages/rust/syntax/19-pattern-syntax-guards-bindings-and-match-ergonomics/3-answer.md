# rust/syntax/19 — 패턴 문법 전수 — 가드·`@`·or 패턴·구조 분해·매치 인체공학 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 다만 이 주제의 핵심인 **매치 인체공학은 에디션과 무관**하다(1.26.0+).\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 에러 셋 — `&String` · `&mut String` · `String`

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 매치 인체공학 — &Option<String> 을 Some(s) 로 받으면 s 는 무엇인가
// let 로 받으면서 일부러 타입을 틀리게 적어 컴파일러가 실제 타입을 찍게 한다
fn main() {
    let owned: Option<String> = Some(String::from("가나"));

    let r: &Option<String> = &owned;
    match r {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    let mut owned2: Option<String> = Some(String::from("다라"));
    let m: &mut Option<String> = &mut owned2;
    match m {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    match owned2 {
        Some(s) => { let _probe: () = s; }
        None => {}
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:9:39
  |
9 |         Some(s) => { let _probe: () = s; }
  |                                  --   ^ expected `()`, found `&String`
  |                                  |
  |                                  expected due to this

error[E0308]: mismatched types
  --> ex.rs:16:39
   |
16 |         Some(s) => { let _probe: () = s; }
   |                                  --   ^ expected `()`, found `&mut String`
   |                                  |
   |                                  expected due to this

error[E0308]: mismatched types
  --> ex.rs:21:39
   |
21 |         Some(s) => { let _probe: () = s; }
   |                                  --   ^ expected `()`, found `String`
   |                                  |
   |                                  expected due to this

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

**왜 그런가**

- ★★★ **글자가 셋 다 `Some(s)` 인데 타입이 셋 다 다르다.**

| 줄 | 대상 값 | `s` 의 타입 | 매치 뒤 원본 |
|---|---|---|---|
| 9 | `&Option<String>` | **`&String`** | 읽을 수 있다(빌림) |
| 16 | `&mut Option<String>` | **`&mut String`** | 읽을 수 있다(가변 빌림이 끝난 뒤) |
| 21 | `Option<String>` | **`String`** | **못 읽는다**(이동) |

- 셋을 가르는 것은 **패턴이 아니라 대상 값**이다. 패턴은 한 글자도 다르지 않다.
  대상에 **`&` 가 몇 겹 씌워져 있나**가 바인딩에 그대로 옮겨 붙는다 —
  이것을 **기본 바인딩 모드가 `ref`/`ref mut` 로 바뀐다**고 한다.
- ★ **`let _probe: () = s;` 가 하는 일** — 「`s` 를 어떤 것과도 안 맞는 타입에 넣어
  컴파일러가 **실제 타입을 대신 적게** 만드는 것」이다.
  `expected ()`, found `&String` 의 뒤쪽이 답이다. 지어낼 수 없고 독자가 자기 머신에서 재현한다.
- ★ IDE 없이 타입을 캐는 **일반적인 기법**이다. 패턴뿐 아니라 클로저 인자·이터레이터 아이템에도 쓴다.

**찍힌 타입대로 실제로 써 본다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 찍힌 타입대로 써 보면 — &T 는 읽기, &mut T 는 고치기, T 는 가져오기
fn main() {
    let owned: Option<String> = Some(String::from("가나"));
    let r: &Option<String> = &owned;
    match r {
        Some(s) => println!("① {} 길이 {} (s: &String — 읽기만)", s, s.len()),
        None => println!("① 없음"),
    }
    println!("① 뒤 원본 {:?}", owned);

    let mut owned2: Option<String> = Some(String::from("다라"));
    match &mut owned2 {
        Some(s) => { s.push_str("마"); println!("② 고쳤다 {} (s: &mut String)", s); }
        None => println!("② 없음"),
    }
    println!("② 뒤 원본 {:?}", owned2);

    match owned2 {
        Some(s) => println!("③ 가져왔다 {} (s: String)", s),
        None => println!("③ 없음"),
    }
    // ③ 뒤에는 owned2 를 못 읽는다 — 18번 주제의 「묶인 값의 이동」

    // & 를 패턴에 직접 적으면 「벗겨서」 받는다 — 그때는 T 가 Copy 여야 한다
    let nums = vec![1, 2, 3];
    let total: i32 = nums.iter().map(|&n| n).sum();       // n: i32
    let total2: i32 = nums.iter().map(|n| *n).sum();      // n: &i32
    println!("④ {} {}", total, total2);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 가나 길이 6 (s: &String — 읽기만)
① 뒤 원본 Some("가나")
② 고쳤다 다라마 (s: &mut String)
② 뒤 원본 Some("다라마")
③ 가져왔다 다라마 (s: String)
④ 6 6
(종료 코드 0)
```

- ① `&String` — **읽기만** 된다. 매치 뒤 `owned` 가 산다.
- ② `&mut String` — **고칠 수 있다.** `push_str` 이 먹고 원본이 `Some("다라마")` 가 된다.
- ③ `String` — **가져간다.** 그 뒤로 `owned2` 는 못 읽는다.
- ④ **패턴에 `&` 를 적으면 한 겹 벗긴다** — `|&n|` 의 `n` 은 `i32` 다. 그러려면 안쪽이 `Copy` 여야 한다.
  `|n| *n` 과 결과가 같고 벗기는 자리만 다르다.

### 2. ★★ 거부된다 — E0004. **가드는 완전성 계산에 안 들어간다**

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 가드가 붙으면 완전성 검사가 그 팔을 「덮은 것으로 치지 않는다」
fn sign(n: i32) -> &'static str {
    match n {
        x if x < 0 => "음수",
        x if x == 0 => "영",
        x if x > 0 => "양수",
    }
}

fn flag(b: bool) -> &'static str {
    match b {
        true => "참",
        x if !x => "거짓",
    }
}

fn main() {
    println!("{} {}", sign(-1), flag(false));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `i32::MIN..=i32::MAX` not covered
 --> ex.rs:4:11
  |
4 |     match n {
  |           ^ pattern `i32::MIN..=i32::MAX` not covered
  |
  = note: the matched value is of type `i32`
  = note: match arms with guards don't count towards exhaustivity
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
7 ~         x if x > 0 => "양수",
8 ~         i32::MIN..=i32::MAX => todo!(),
  |

error[E0004]: non-exhaustive patterns: `false` not covered
  --> ex.rs:12:11
   |
12 |     match b {
   |           ^ pattern `false` not covered
   |
   = note: the matched value is of type `bool`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
   |
14 ~         x if !x => "거짓",
15 ~         false => todo!(),
   |

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

**왜 그런가**

- 첫 에러는 **`i32::MIN..=i32::MAX` not covered** 다 — **아무것도 안 덮인 것으로 친다.**
- 결정적인 줄은 `= note: match arms with guards don't count towards exhaustivity` 다. 규칙을 그대로 적어 준다.
- ★★ **왜 모르나** — 가드는 **임의의 식**이다. `x < 0`·`x == 0`·`x > 0` 이 합쳐서 전부라는 것을 알려면
  컴파일러가 **산술을 증명**해야 한다. 함수 호출이 든 가드라면 아예 불가능하다.
  그래서 **모르면 안 센다**로 간다 — 안전한 쪽이다.
- `bool` 쪽도 같다. `true` 팔은 세지만 `x if !x` 는 안 세므로 **`false` not covered** 다.
  ★ 값이 둘뿐이어도 예외가 없다 — 규칙이 **값 개수와 무관**하다.
- **처방** — 마지막 팔의 가드를 떼거나(`x => "양수"`) `_` 를 둔다.

### 3. ★★ E0408 **두 개** + E0381 하나

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// or 패턴의 규칙 — 모든 갈래가 「같은 이름들」을 묶어야 한다
enum Shape {
    Circle { r: f64 },
    Square { side: f64 },
    Rect { w: f64, h: f64 },
}

fn main() {
    let s = Shape::Rect { w: 2.0, h: 3.0 };
    let x = match s {
        Shape::Circle { r } | Shape::Square { side } => r,
        Shape::Rect { w, h } => w * h,
    };
    println!("{}", x);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0408]: variable `side` is not bound in all patterns
  --> ex.rs:12:9
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |         ^^^^^^^^^^^^^^^^^^^                   ---- variable not in all patterns
   |         |
   |         pattern doesn't bind `side`

error[E0408]: variable `r` is not bound in all patterns
  --> ex.rs:12:31
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                         -     ^^^^^^^^^^^^^^^^^^^^^^ pattern doesn't bind `r`
   |                         |
   |                         variable not in all patterns

error[E0381]: used binding `r` is possibly-uninitialized
  --> ex.rs:12:57
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                         -                               ^ `r` used here but it is possibly-uninitialized
   |                         |
   |                         binding initialized here in some conditions
   |                         binding declared here but left uninitialized

warning: unused variable: `side`
  --> ex.rs:12:47
   |
12 |         Shape::Circle { r } | Shape::Square { side } => r,
   |                                               ^^^^ help: try ignoring the field: `side: _`
   |
   = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

error: aborting due to 3 previous errors; 1 warning emitted

Some errors have detailed explanations: E0381, E0408.
For more information about an error, try `rustc --explain E0381`.
(종료 코드 1)
```

**왜 그런가**

- **E0408** 이 두 번 나는 이유는 **양쪽에서 한 번씩** 보기 때문이다 —
  「`Circle { r }` 가 `side` 를 안 묶는다」와 「`Square { side }` 가 `r` 을 안 묶는다」.
  진단이 각각 `variable not in all patterns` 와 `pattern doesn't bind …` 로 **두 자리를 짝지어** 짚는다.
- 딸려 오는 **E0381** 은 ``used binding `r` is possibly-uninitialized`` 다 —
  팔의 몸통이 `r` 을 쓰는데 `Square` 로 들어오면 `r` 이 안 채워진 채이기 때문이다.
  `binding initialized here in some conditions` 가 그 사정을 말한다.
- ★ 규칙을 한 문장으로 — **or 패턴의 모든 갈래는 같은 이름 집합을 묶어야 한다.**

**이름을 맞춰도 타입이 갈리면 다른 번호다.**

```text
===== 소스: ex.rs =====
// ex.rs
// 이름은 맞췄는데 타입이 갈리면 — 또 다른 번호가 나온다
enum V {
    A(u32),
    B(String),
}

fn main() {
    let v = V::A(1);
    match v {
        V::A(x) | V::B(x) => println!("{:?}", x),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
  --> ex.rs:11:24
   |
10 |     match v {
   |           - this expression has type `V`
11 |         V::A(x) | V::B(x) => println!("{:?}", x),
   |              -         ^ expected `u32`, found `String`
   |              |
   |              first introduced with type `u32` here
   |
   = note: in the same arm, a binding must have the same type in all alternatives

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

- **E0308** — `` expected `u32`, found `String` ``.
  `= note: in the same arm, a binding must have the same type in all alternatives` 가 규칙이다.
- ★ 진단이 ``first introduced with type `u32` here`` 라고 적는다 — **먼저 나온 갈래가 타입을 정한다.**
  순서를 바꾸면 기대 타입과 발견 타입이 뒤집힌다.

### 4. ★ 거부된다 — E0507 `cannot move out of s in pattern guard`

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 가드는 「빌려서 볼 뿐」이다 — 가드 안에서 값을 가져가려 하면 막힌다
fn main() {
    let v = Some(String::from("가나"));
    fn takes(s: String) -> bool { s.len() > 3 }
    match v {
        Some(s) if takes(s) => println!("길다"),
        _ => println!("짧거나 없다"),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0507]: cannot move out of `s` in pattern guard
 --> ex.rs:7:26
  |
7 |         Some(s) if takes(s) => println!("길다"),
  |                          ^ move occurs because `s` has type `String`, which does not implement the `Copy` trait
  |
  = note: variables bound in patterns cannot be moved from until after the end of the pattern guard
help: consider cloning the value if the performance cost is acceptable
  |
7 |         Some(s) if takes(s.clone()) => println!("길다"),
  |                           ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(종료 코드 1)
```

**왜 그런가**

- **E0507**, 제목은 ``cannot move out of `s` in pattern guard`` 다.
- `= note: variables bound in patterns cannot be moved from until after the end of the pattern guard` —
  **가드가 끝나기 전에는 묶인 값을 못 옮긴다.**
- ★ **왜 필요한가** — 가드가 **거짓이면 다음 팔이 같은 값을 다시 봐야 한다.**
  가드가 값을 가져가 버리면 다음 팔에 볼 것이 없다. 그래서 가드는 **빌려서 보기만** 한다.
- 진단이 제안하는 고침은 **`takes(s.clone())`** 이고,
  ★ **더 싼 고침**은 함수를 `fn takes(s: &String) -> bool` 로 바꿔 **빌려서 보는 것**이다.
  복제는 힙을 한 번 더 잡지만 빌림은 공짜다.

### 5. ★ 거부된다 — E0004 `&[_, _, _, ..]` not covered

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 길이를 모르는 슬라이스는 「몇 개짜리」를 다 덮어야 한다
fn shape(v: &[i32]) -> String {
    match v {
        [] => String::from("빈 것"),
        [only] => format!("하나 {}", only),
        [a, b] => format!("둘 {} {}", a, b),
    }
}

fn arr(a: [i32; 3]) -> i32 {
    match a {
        [x, y, z] => x + y + z,
    }
}

fn main() {
    println!("{} {}", shape(&[1, 2, 3]), arr([1, 2, 3]));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0004]: non-exhaustive patterns: `&[_, _, _, ..]` not covered
 --> ex.rs:4:11
  |
4 |     match v {
  |           ^ pattern `&[_, _, _, ..]` not covered
  |
  = note: the matched value is of type `&[i32]`
help: ensure that all possible cases are being handled by adding a match arm with a wildcard pattern or an explicit pattern as shown
  |
7 ~         [a, b] => format!("둘 {} {}", a, b),
8 ~         &[_, _, _, ..] => todo!(),
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0004`.
(종료 코드 1)
```

**왜 그런가**

- 에러는 **하나**이고, 안 덮인 것은 **`&[_, _, _, ..]`** 다 — 「원소가 셋 이상인 모든 슬라이스」다.
  ★ 길이를 모르는 슬라이스는 **길이 자체가 값 공간**이라 `[]`·`[a]`·`[a, b]` 로는 끝이 없다.
- ★★ **`arr` 는 에러가 안 났다.** `[i32; 3]` 은 **길이가 타입에 박혀 있어** `[x, y, z]` 하나로 완전하다.
  같은 패턴 문법인데 **타입이 길이를 아느냐**로 갈린다.
- **`[head, tail @ ..]` 와 `[]` 두 팔이면 완전하다** — 앞엣것이 「하나 이상 전부」, 뒤엣것이 「빈 것」이다.
  실제로 그렇게 쓴 판이 있다.

```text
===== 소스: ex.rs =====
// ex.rs
// 슬라이스 패턴 — 앞·뒤·가운데를 한 번에 짚는다
fn shape(v: &[i32]) -> String {
    match v {
        [] => String::from("빈 것"),
        [only] => format!("하나 {}", only),
        [a, b] => format!("둘 {} {}", a, b),
        [first, .., last] => format!("셋 이상 처음 {} 끝 {}", first, last),
    }
}

fn head_tail(v: &[i32]) -> String {
    match v {
        [head, tail @ ..] => format!("머리 {} 꼬리 {:?}(길이 {})", head, tail, tail.len()),
        [] => String::from("빈 것"),
    }
}

fn main() {
    for v in [vec![], vec![1], vec![1, 2], vec![1, 2, 3], vec![1, 2, 3, 4, 5]] {
        println!("{:?} | {} | {}", v, shape(&v), head_tail(&v));
    }
    // 고정 길이 배열은 길이를 알아서 `[a, b, c]` 하나로 완전하다
    let arr = [10, 20, 30];
    let [a, b, c] = arr;
    println!("배열 분해 {} {} {}", a, b, c);
    // 문자열 바이트에도 쓴다 — 15번 주제의 &[u8]
    let bytes = "AB가".as_bytes();
    println!("{}", match bytes {
        [b'A', rest @ ..] => format!("A 로 시작, 나머지 {}바이트", rest.len()),
        _ => String::from("그 밖"),
    });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[] | 빈 것 | 빈 것
[1] | 하나 1 | 머리 1 꼬리 [](길이 0)
[1, 2] | 둘 1 2 | 머리 1 꼬리 [2](길이 1)
[1, 2, 3] | 셋 이상 처음 1 끝 3 | 머리 1 꼬리 [2, 3](길이 2)
[1, 2, 3, 4, 5] | 셋 이상 처음 1 끝 5 | 머리 1 꼬리 [2, 3, 4, 5](길이 4)
배열 분해 10 20 30
A 로 시작, 나머지 4바이트
(종료 코드 0)
```

- `..` 는 **한 패턴에 한 번만** 쓸 수 있다. 두 번 쓰면 어디서 끊어야 할지 정해지지 않는다.

### 6. ★ 네 값이 네 팔에 하나씩 걸린다

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 구조 분해 — 구조체·열거형·튜플이 몇 겹이든 한 패턴으로 내려간다
#[derive(Debug)]
struct Point { x: i32, y: i32 }
#[derive(Debug)]
struct Line { from: Point, to: Point, label: Option<String> }

#[derive(Debug)]
enum Shape { Seg(Line), Dot(Point) }

fn read(s: &Shape) -> String {
    match s {
        // 세 겹을 한 줄에 — enum → struct → struct/Option
        Shape::Seg(Line { from: Point { x: x1, y: y1 },
                          to: Point { x: x2, y: y2 },
                          label: Some(name) }) =>
            format!("이름 있는 선 {} ({},{})\u{2192}({},{})", name, x1, y1, x2, y2),
        Shape::Seg(Line { from: Point { x: x1, .. }, label: None, .. }) =>
            format!("이름 없는 선, 시작 x={}", x1),
        Shape::Dot(Point { x: 0, y: 0 }) => String::from("원점"),
        Shape::Dot(Point { x, y }) => format!("점 ({},{})", x, y),
    }
}

fn main() {
    let a = Shape::Seg(Line { from: Point { x: 0, y: 0 }, to: Point { x: 3, y: 4 },
                              label: Some(String::from("빗변")) });
    let b = Shape::Seg(Line { from: Point { x: 7, y: 1 }, to: Point { x: 9, y: 1 }, label: None });
    let c = Shape::Dot(Point { x: 0, y: 0 });
    let d = Shape::Dot(Point { x: 2, y: 5 });
    for s in [&a, &b, &c, &d] { println!("{}", read(s)); }

    // let 도 패턴이다 — 함수 인자·for 도 마찬가지
    let Line { from: Point { x, .. }, .. } = Line {
        from: Point { x: 11, y: 12 }, to: Point { x: 0, y: 0 }, label: None };
    println!("let 으로 뽑은 x={}", x);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
이름 있는 선 빗변 (0,0)→(3,4)
이름 없는 선, 시작 x=7
원점
점 (2,5)
let 으로 뽑은 x=11
(종료 코드 0)
```

**왜 그런가**

- `a`(이름 있는 선) → 첫 팔 · `b`(이름 없는 선) → 둘째 팔 ·
  `c`(원점) → 셋째 팔 · `d`(그 밖의 점) → 넷째 팔. 위에서부터 먼저 맞는 팔이 이긴다.
- ★ **`label: Some(name)` 은 칸의 값에까지 패턴을 건다.** 그래서 같은 `Shape::Seg` 인데도
  「이름이 있나 없나」로 **팔이 둘로 갈린다.** 이것이 중첩 패턴의 값이다.
- **`..` 는 여러 칸, `_` 는 한 칸**이다. `Point { x: x1, .. }` 는 `y` 하나를 건너뛰지만
  칸이 열 개여도 같은 한 글자로 끝난다.
- **값을 그대로 적으면 그 값일 때만 맞는다** — `Point { x: 0, y: 0 }` 은 원점만 잡는다.
  ★ 이것은 바인딩이 아니라 **리터럴 패턴**이다.
- 마지막 `let Line { from: Point { x, .. }, .. } = …;` 은 **`let` 도 패턴을 받는다**는 사실을 보인다.
  단 `let` 은 **반박 불가** 패턴만 받으므로 여기서는 구조체라 통과한다.

### 7. 가드가 보는 것

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 가드 — 패턴 뒤에 붙는 if. 패턴이 못 보는 「값들 사이의 관계」를 본다
fn kind(p: (i32, i32)) -> &'static str {
    match p {
        (x, y) if x == y => "대각선",
        (x, _) if x == 0 => "세로축",
        (_, y) if y == 0 => "가로축",
        _ => "그 밖",
    }
}

fn main() {
    for p in [(0, 0), (3, 3), (0, 5), (5, 0), (2, 7)] {
        println!("{:?} {}", p, kind(p));
    }
    // 가드는 「그 팔의 모든 갈래」에 걸린다 — or 패턴 전체를 덮는다
    let n = 6;
    println!("{}", match n { 4 | 6 | 8 if n > 5 => "5보다 큰 짝수", _ => "그 밖" });
    // 바깥 변수를 가드에서 읽을 수 있다 — 패턴 자리에서는 못 한다
    let limit = 5;
    println!("{}", match n { x if x > limit => "한계 초과", _ => "이내" });
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(0, 0) 대각선
(3, 3) 대각선
(0, 5) 세로축
(5, 0) 가로축
(2, 7) 그 밖
5보다 큰 짝수
한계 초과
(종료 코드 0)
```

**왜 그런가**

- **`(x, x)` 는 못 적는다.** 같은 이름을 두 번 묶는 것이 되어 문법 오류다.
  **관계는 가드로 본다** — `(x, y) if x == y`.
- ★ **가드는 or 패턴 전체에 걸린다.** `4 | 6 | 8 if n > 5` 는 「(4 또는 6 또는 8)이고 5보다 큼」이지
  「4, 6, 또는 (8이고 5보다 큼)」이 아니다. 위 출력에서 `n = 6` 이 잡힌 것이 그 증거다.
- **패턴 자리에 바깥 변수 이름을 쓰면 비교가 아니라 새 바인딩**이다 —
  18번 주제의 E0170 과 같은 뿌리다. 그래서 `limit` 과의 비교는 **가드에서** 한다.
- **가드에서는 바깥 변수를 읽을 수 있다.** 가드는 그냥 식이기 때문이다.

### 8. `@` 와 or 패턴의 버전

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// @ 바인딩 — 「거른 값을 이름으로도 받는다」. 거름과 묶음을 동시에
#[derive(Debug)]
enum Msg { Id(u32), Name(String) }

fn main() {
    for m in [Msg::Id(3), Msg::Id(42), Msg::Id(500), Msg::Name(String::from("가"))] {
        let s = match m {
            Msg::Id(n @ 1..=9) => format!("한 자리 id {}", n),
            Msg::Id(n @ 10..=99) => format!("두 자리 id {}", n),
            Msg::Id(n) => format!("큰 id {}", n),
            Msg::Name(ref s) => format!("이름 {}", s),
        };
        println!("{}", s);
    }
    // 구조체 변형 전체를 @ 로 받으면서 안쪽도 본다
    #[derive(Debug)]
    struct P { x: i32, y: i32 }
    let p = P { x: 3, y: 9 };
    match p {
        P { x: x @ 1..=5, y } => println!("x={} 가 1\u{7e}5 이고 y={}", x, y),
        P { x, y } => println!("그 밖 {} {}", x, y),
    }
    // @ 는 or 패턴도 감쌀 수 있다 (1.65부터)
    let n = 7;
    match n {
        v @ (1 | 3 | 5 | 7 | 9) => println!("홀수 {}", v),
        v => println!("그 밖 {}", v),
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
한 자리 id 3
두 자리 id 42
큰 id 500
이름 가
x=3 가 1~5 이고 y=9
홀수 7
(종료 코드 0)
```

**왜 그런가**

- **`@` 는 「거르기」와 「묶기」를 동시에** 한다. 없으면 둘 중 하나를 포기해야 한다 —
  `Msg::Id(1..=9)` 는 거르지만 값을 못 쓰고, `Msg::Id(n)` 은 값을 쓰지만 안 거른다.
- **중첩 자리의 or 패턴**(`Some(1 | 3)`)은 **1.53.0부터**다. 그 전에는 `Some(1) | Some(3)` 이라야 했다.
- **`@` 가 or 를 감싸는 것**(`v @ (1 | 3 | 5)`)은 **1.65.0부터**다.
- **맨 앞의 `|` 는 써도 된다** — 여러 줄로 늘어놓을 때 모양이 는다.

```text
===== 소스: ex.rs =====
// ex.rs
// or 패턴 — 어느 자리에 쓸 수 있나. 2021 에서는 중첩 자리에도 쓴다
#[derive(Debug)]
enum Key { Up, Down, Left, Right, Esc }

fn axis(k: &Key) -> &'static str {
    match k {
        Key::Up | Key::Down => "세로",
        Key::Left | Key::Right => "가로",
        Key::Esc => "없음",
    }
}

fn main() {
    for k in [Key::Up, Key::Down, Key::Left, Key::Right, Key::Esc] { println!("{:?} {}", k, axis(&k)); }
    // 중첩 자리 — Some(1 | 3) 처럼 안쪽에 쓴다
    for o in [Some(1), Some(2), Some(3), None] {
        println!("{:?} {}", o, match o { Some(1 | 3) => "홀수 후보", Some(_) => "그 밖의 수", None => "없음" });
    }
    // 맨 앞의 | 는 써도 되고 안 써도 된다
    let n = 2;
    println!("{}", match n { | 1 | 2 => "하나나 둘", _ => "그 밖" });
    // let 과 함수 인자 자리에서는? — 거부되지 않는 것만 쓸 수 있다
    let (1 | 2) = n else { unreachable!() };
    println!("let 에서도 or 패턴이 된다");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Up 세로
Down 세로
Left 가로
Right 가로
Esc 없음
Some(1) 홀수 후보
Some(2) 그 밖의 수
Some(3) 홀수 후보
None 없음
하나나 둘
let 에서도 or 패턴이 된다
(종료 코드 0)
```

- **`let` 자리에서도 or 패턴이 된다.** 단 `let` 은 **반박 불가** 패턴만 받으므로
  `let (1 | 2) = n else { … };` 처럼 **`else` 가 필요**하다([목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).

### 9. 매치 인체공학의 경계

- **1.26.0부터**이고 ★★ **에디션과 무관**하다. 2015 에디션에서도 같게 동작한다.
  「2018 에디션 기능」으로 외우면 틀린다.
- **`&&Option<T>` 를 `Some(s)` 로 받으면 `s` 는 `&T`** 다 — 참조 두 겹이 **한 겹으로 접힌다.**
  바인딩 모드는 「몇 겹인지」를 안 세고 **`ref` 냐 `ref mut` 냐**만 기억하기 때문이다.
- **패턴에 `&` 를 직접 적으면 한 겹 벗긴다.** `|&n|` 의 `n` 은 값이다.
  그러려면 **안쪽이 `Copy`** 여야 한다 — 아니면 「빌린 것에서 옮길 수 없다」로 막힌다.

```text
===== 소스: ex.rs =====
// ex.rs
// ref / ref mut — 인체공학이 생기기 전의 도구. 지금은 같은 일을 하는 두 길이 된다
fn main() {
    let owned: Option<String> = Some(String::from("가나"));

    // 옛 방식 — 값을 매치하면서 팔에서 빌린다
    match owned {
        Some(ref s) => println!("① ref {} ({}바이트)", s, s.len()),
        None => println!("① 없음"),
    }
    println!("① 뒤 원본 {:?}", owned);

    // 지금 방식 — 참조를 매치한다. 같은 결과다
    match &owned {
        Some(s) => println!("② 인체공학 {} ({}바이트)", s, s.len()),
        None => println!("② 없음"),
    }
    println!("② 뒤 원본 {:?}", owned);

    // ref mut 도 마찬가지로 &mut 매치로 갈음된다
    let mut v = Some(String::from("다라"));
    match v {
        Some(ref mut s) => s.push('마'),
        None => {}
    }
    println!("③ {:?}", v);

    // ref 가 아직 필요한 자리 — let 에서 일부만 빌려 잡을 때
    let pair = (String::from("바"), String::from("사"));
    let (ref a, b) = pair;          // a 는 빌리고 b 는 가져간다
    println!("④ a={} b={}", a, b);
    println!("④ pair.0 은 아직 읽힌다: {}", pair.0);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① ref 가나 (6바이트)
① 뒤 원본 Some("가나")
② 인체공학 가나 (6바이트)
② 뒤 원본 Some("가나")
③ Some("다라마")
④ a=바 b=사
④ pair.0 은 아직 읽힌다: 바
(종료 코드 0)
```

- **`ref` 가 안 쓰이게 된 이유** — ①과 ②가 **같은 일**을 하는데 ②가 짧고 읽기 쉽다.
  1.26.0 이전에는 ②를 쓰려면 패턴에도 `&Some(ref s)` 를 적어야 했다.
  인체공학이 그 `&`·`ref` 를 지우면서 ①이 남을 이유가 없어졌다.
- ★ **아직 필요한 자리** — `let (ref a, b) = pair;` 처럼 **한 패턴 안에서 칸마다 빌림/이동을 가를 때**다.
  대상이 값이라 인체공학이 안 켜지고, `&pair` 로 바꾸면 `b` 까지 빌림이 된다.
  위 출력의 ④가 그 자리다 — `a` 는 빌렸고 `b` 는 가져갔고 `pair.0` 은 아직 읽힌다.

### 10. 패턴이 쓰이는 자리

**출력**

```text
===== 소스: ex.rs =====
// ex.rs
// 패턴이 쓰이는 자리는 match 만이 아니다 — 여섯 자리를 한 파일에서 본다
struct Pt { x: i32, y: i32 }

fn dist(Pt { x, y }: &Pt) -> f64 {          // ④ 함수 인자
    (((x * x) + (y * y)) as f64).sqrt()
}

fn main() {
    let pts = vec![Pt { x: 3, y: 4 }, Pt { x: 6, y: 8 }];

    let Pt { x, y } = &pts[0];              // ① let
    println!("① {} {}", x, y);

    for Pt { x, y } in &pts {               // ② for
        println!("② {} {}", x, y);
    }

    let f = |Pt { x, .. }: &Pt| *x * 10;    // ③ 클로저 인자
    println!("③ {}", f(&pts[1]));

    println!("④ {}", dist(&pts[0]));

    if let [first, ..] = &pts[..] {         // ⑤ if let
        println!("⑤ {}", first.x);
    }

    let mut it = pts.iter();
    while let Some(Pt { x, y }) = it.next() {   // ⑥ while let
        println!("⑥ {} {}", x, y);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
① 3 4
② 3 4
② 6 8
③ 60
④ 5
⑤ 3
⑥ 3 4
⑥ 6 8
(종료 코드 0)
```

**왜 그런가**

- 여섯 자리 — **① `let` · ② `for` · ③ 클로저 인자 · ④ 함수 인자 · ⑤ `if let` · ⑥ `while let`.**
- **반박 불가 패턴만 받는 것은 ①\~④** 다. 안 맞을 수가 없어야 한다.
  `Some(x)` 처럼 안 맞을 수 있는 것은 ⑤·⑥ 이나 `let else` 자리로 간다([목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).

| 번호 | 언제 나나 |
|---|---|
| **E0408** | or 패턴의 갈래마다 묶는 이름이 다르다 |
| **E0381** | 갈래에 따라 안 채워질 수 있는 바인딩을 썼다(E0408 에 딸려 온다) |
| **E0507** | 가드 안에서 묶인 값을 가져가려 했다 |
| **E0004** | 완전성이 안 찼다 — 가드 때문이거나 슬라이스 길이 때문이거나 |

- ★★ **매치 인체공학이 만들어 내는 것은 빌림**이다. `s: &String` 은 원본을 빌리고 있는 상태라
  그 수명 동안 원본을 가변으로 못 잡는다. 그 규칙의 정본은
  [**10번 주제**](../10-borrowing-and-aliasing-rules/)와 [**11번 주제**](../11-borrow-checker-rejections/)다.
- **완전성 검사의 정본**은 [**18번 주제**](../18-match-and-exhaustiveness/)다.
- **반박 가능한 패턴을 쓰는 자리들**(`if let`·`while let`·`let else`)은 [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)다.
- **슬라이스 자체의 정본**은 [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)다 —
  여기는 **슬라이스를 패턴으로 가르는 법**만 맡는다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` **동일** |
| ★★★ **바인딩 타입 증명** | `b19-09` — `let _probe: () = s;` 세 벌 | 1 | `&String` · `&mut String` · `String` 이 **에러에 찍힘** |
| 찍힌 타입대로 쓰기 | `b19-10` | 1 | 읽기 · 고치기 · 가져가기가 각각 성립 |
| 가드 | `b19-01`(통과) · `b19-02`(E0004 ×2) | 2 | `guards don't count towards exhaustivity` |
| `@` · or 패턴 | `b19-03` · `b19-04` | 2 | `@` 가 or 를 감싸는 판까지 통과 |
| or 패턴의 규칙 | `b19-05`(E0408 ×2 + E0381) · `b19-05b`(E0308) | 2 | 이름·타입 둘 다 맞아야 한다 |
| 구조 분해 | `b19-06` | 1 | 세 겹을 한 패턴으로 |
| 슬라이스 패턴 | `b19-07`(통과) · `b19-08`(E0004) | 2 | 배열은 완전, 슬라이스는 길이도 공간 |
| 가드 안의 이동 | `b19-12`(E0507) | 1 | — |
| `ref` / `ref mut` | `b19-11` | 1 | ①과 ②가 같은 결과 |
| 패턴 자리 여섯 | `b19-13` | 1 | 여섯 자리 전부 동작 |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `let _probe: () = s;` 가 찍어 주는 **메시지 문구** | 진단 품질은 보장이 아니다. 타입 자체는 언어 보장이다 |
| E0408 에 **E0381 이 딸려 오는 것** | 에러 개수는 진단 구현에 달렸다 |
| `help:` 가 주는 고친 코드(`s.clone()`·`ref s`) | 같은 이유 |
| 버전 경계 — 중첩 or(1.53) · `@`+or(1.65) · `rest @ ..`(1.42) | 그 아래 판에서는 안 된다 |
| ★ 매치 인체공학이 **에디션과 무관**한 것 | 2024 에디션이 이 규칙을 한 번 손봤다(목록의 **47번 주제**) — 그쪽은 다시 확인해야 한다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
