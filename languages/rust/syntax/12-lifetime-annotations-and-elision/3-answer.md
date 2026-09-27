# rust/syntax/12 — 수명 표기 `'a`와 생략 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 특별히 적지 않은 한 이 문서의 결과는 **2021** 기준이고,\
> 에디션이 갈리는 자리는 **11번 답**에 따로 적었다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.\
> ★ 이 주제의 고유 창은 **함수 포인터 타입에 담아 보기**(2번)와 **오브젝트 파일 대조**(10번)다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 컴파일되지 않는다 — E0106

**출력**

```text
===== 소스: ex.rs =====
// 두 참조 중 하나를 돌려주는 함수 — 수명을 안 적으면?
fn longest(x: &str, y: &str) -> &str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    println!("{}", longest("가나다", "라"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:2:33
  |
2 | fn longest(x: &str, y: &str) -> &str {
  |               ----     ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `x` or `y`
help: consider introducing a named lifetime parameter
  |
2 | fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
  |           ++++     ++          ++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

**왜 그런가**

- **E0106**, 제목은 **`missing lifetime specifier`** 다.
- `^` 는 **반환 타입의 `&`** 자리(2:33)에 붙는다. 입력 두 개에는 `----` 밑줄만 그어 **후보**임을 표시한다.
- ★ `help:` 한 구절이 본체다 — **`the signature does not say whether it is borrowed from x or y`**.\
  못 알아낸 것은 「**출력 참조의 출처**」다.
- ★★ **몸통을 안 읽는다.** 이 함수는 실행하면 항상 둘 중 하나를 돌려주지만,
  빌림 검사는 **시그니처만** 본다. 10번의 「`&mut self` 메서드가 전체를 잡는다」와 **같은 원리**다.
- 생략 규칙 셋을 손으로 돌리면 이렇게 막힌다.

| 규칙 | 적용되나 | 왜 |
|---|---|---|
| 1 — 입력마다 제 이름 | ✓ | `x: &'1 str`, `y: &'2 str` 가 된다 |
| 2 — 입력 수명이 **하나**면 출력에 준다 | ✗ | **둘**이다 |
| 3 — `&self` 가 있으면 self 의 것을 준다 | ✗ | `&self` 가 없다 |

- 마지막 `help:` 의 `++++` 는 **끼워 넣을 자리**다. 그대로 고치면 통과한다.

```text
===== 소스: ex.rs =====
// 같은 함수에 'a 를 붙이면
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    println!("{}", longest("가나다", "라"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다
(종료 코드 0)
```

### 2. ★★ E0308 — 그리고 `= note:` 가 실제 타입을 찍어 준다

**출력**

```text
===== 소스: ex.rs =====
// 그럼 다른 모양에는 안 담기나? — 출력만 'static 으로 바꿔 본다
fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}

fn main() {
    let f: fn(&str) -> &'static str = first_word;
    println!("{}", f("hello rust"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:7:39
  |
7 |     let f: fn(&str) -> &'static str = first_word;
  |            ------------------------   ^^^^^^^^^^ one type is more general than the other
  |            |
  |            expected due to this
  |
  = note: expected fn pointer `for<'a> fn(&'a _) -> &'static _`
                found fn item `for<'a> fn(&'a _) -> &'a _ {first_word}`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **E0308 `mismatched types`** 다. 수명 에러가 아니라 **타입 에러**로 나온다 — 수명이 타입의 일부이기 때문이다.
- `= note:` 두 줄은 각각 이렇다.

| 줄 | 뜻 |
|---|---|
| `expected fn pointer for<'a> fn(&'a _) -> &'static _` | **내가 적은 타입**을 컴파일러가 푼 모양 |
| `found fn item for<'a> fn(&'a _) -> &'a _ {first_word}` | ★ **`first_word` 의 실제 타입** |

- ★★ 그래서 `first_word` 의 실제 타입은 **`for<'a> fn(&'a str) -> &'a str`** 다.\
  생략 규칙 1(입력에 `'a`)과 2(출력에 그 `'a`)가 푼 결과를 **컴파일러가 글자로 찍어 준 것**이다.
- `for<'a>` 는 「어떤 `'a` 에 대해서든」이라는 뜻이다(HRTB). 함수는 호출될 때마다 다른 수명을 받는다.
- 통과시키려면 **`for<'a> fn(&'a str) -> &'a str`** 로 적으면 된다.

```text
===== 소스: ex.rs =====
// 생략형 함수를 「손으로 푼 타입」의 함수 포인터에 담아 본다 — 같은 것이면 통과한다.
fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}

fn main() {
    // 규칙 1+2 가 푼다고 주장하는 모양 그대로
    let f: for<'a> fn(&'a str) -> &'a str = first_word;
    println!("{}", f("hello rust"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
hello
(종료 코드 0)
```

★ **이 수법이 이 주제의 핵심 도구**다. 「생략이 이렇게 풀린다」를 **머릿속 그림이 아니라 컴파일러의 출력**으로 확인한다.
10번의 `let _: () = 식;` 과 같은 계열이고, 여기서는 **수명까지 찍힌다**는 점이 다르다.

### 3. ★ 거부된다 — 그리고 이 에러에는 번호가 없다

**출력**

```text
===== 소스: ex.rs =====
// 규칙 3 이 정말 self 를 고르는가 — 두 번째 인자를 돌려주려 해 본다
struct Parser { text: String }

impl Parser {
    fn head(&self, sep: &str) -> &str {
        let _ = &self.text;
        sep                       // ★ self 가 아니라 sep 을 돌려준다
    }
}

fn main() {
    let p = Parser { text: String::from("a,b,c") };
    println!("{}", p.head(","));
}
===== rustc --edition 2021 ex.rs -o ex =====
error: lifetime may not live long enough
 --> ex.rs:7:9
  |
5 |     fn head(&self, sep: &str) -> &str {
  |             -           - let's call the lifetime of this reference `'1`
  |             |
  |             let's call the lifetime of this reference `'2`
6 |         let _ = &self.text;
7 |         sep                       // ★ self 가 아니라 sep 을 돌려준다
  |         ^^^ method was supposed to return data with lifetime `'2` but it is returning data with lifetime `'1`
  |
help: consider introducing a named lifetime parameter and update trait if needed
  |
5 |     fn head<'a>(&self, sep: &'a str) -> &'a str {
  |            ++++              ++          ++

error: aborting due to 1 previous error
```

**왜 그런가**

- **거부된다.** 시그니처는 생략 규칙 3으로 **`fn head<'a, 'b>(&'a self, sep: &'b str) -> &'a str`** 이 됐는데,
  몸통이 **`'b`(= `sep`)를 돌려주려** 했다.
- ★★ **에러 번호가 없다.** `error[E0…]` 가 아니라 그냥 `error:` 다 —\
  `rustc --explain` 으로 찾아볼 수 없는 부류이고, 마지막 줄의 `For more information…` 안내도 없다.\
  **번호 있는 진단만 있는 게 아니다**를 여기서 배운다.
- `'1`·`'2` 는 **컴파일러가 즉석에서 붙인 이름**이다 — `let's call the lifetime of this reference` 가 그 선언이다.\
  내가 이름을 안 지었으니 컴파일러가 임시 이름을 만들어 설명하는 것이다. **`'2` = self, `'1` = `sep`.**
- `method was supposed to return data with lifetime '2 but it is returning data with lifetime '1` —\
  ★ **`supposed to`** 가 규칙 3의 실증이다. **출력은 이미 self 로 정해져 있었다.**
- 첫 인자를 `this: &Parser` 로 바꾸면 **규칙 3이 안 돈다**(`self` 라는 자리가 아니라 평범한 인자가 된다).\
  그러면 규칙 2도 못 쓰여(입력 수명 둘) **E0106** 이 난다.

```text
===== 소스: ex.rs =====
// 인자가 둘인데 &self 가 없으면 — 규칙 3 이 못 쓰이고 규칙 2 도 못 쓰인다
struct Parser { text: String }

impl Parser {
    fn pick(this: &Parser, other: &str) -> &str {
        if this.text.len() > other.len() { &this.text } else { other }
    }
}

fn main() {
    let p = Parser { text: String::from("a,b,c") };
    println!("{}", Parser::pick(&p, ","));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:5:44
  |
5 |     fn pick(this: &Parser, other: &str) -> &str {
  |                   -------         ----     ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but the signature does not say whether it is borrowed from `this` or `other`
help: consider introducing a named lifetime parameter
  |
5 |     fn pick<'a>(this: &'a Parser, other: &'a str) -> &'a str {
  |            ++++        ++                 ++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

### 4. ★★ 거부되는 것은 `&'static str` 쪽 하나 — 그런데 에러는 둘 난다

**출력**

```text
===== 소스: ex.rs =====
// 같은 String 을 두 자리에 각각 던져 본다
fn needs_static_ref(s: &'static str) { println!("참조: {}", s); }
fn needs_static_bound<T: 'static>(_t: T) { println!("경계: 통과"); }

fn main() {
    let owned = String::from("소유한 문자열");

    needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
    needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `owned` does not live long enough
  --> ex.rs:8:22
   |
 6 |     let owned = String::from("소유한 문자열");
   |         ----- binding `owned` declared here
 7 |
 8 |     needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
   |     -----------------^^^^^^-
   |     |                |
   |     |                borrowed value does not live long enough
   |     argument requires that `owned` is borrowed for `'static`
 9 |     needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
10 | }
   | - `owned` dropped here while still borrowed

error[E0505]: cannot move out of `owned` because it is borrowed
 --> ex.rs:9:24
  |
6 |     let owned = String::from("소유한 문자열");
  |         ----- binding `owned` declared here
7 |
8 |     needs_static_ref(&owned);   // (가) 빌린 것을 &'static 자리에
  |     ------------------------
  |     |                |
  |     |                borrow of `owned` occurs here
  |     argument requires that `owned` is borrowed for `'static`
9 |     needs_static_bound(owned);  // (나) 소유한 것을 T: 'static 자리에
  |                        ^^^^^ move out of `owned` occurs here
  |
help: consider cloning the value if the performance cost is acceptable
  |
8 |     needs_static_ref(&owned.clone());   // (가) 빌린 것을 &'static 자리에
  |                            ++++++++

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0505, E0597.
For more information about an error, try `rustc --explain E0505`.
```

**왜 그런가**

- 진짜로 잘못된 것은 **(가) 하나**다. **에러는 E0597 과 E0505 둘**이 난다.
- **E0597** — 지역 `owned` 에서 빌린 참조를 `&'static str` 자리에 넣었다.\
  라벨 `argument requires that owned is borrowed for 'static` 이 **그 요구가 어디서 왔는지**를 말한다.
- ★ **E0505 는 덤**이다. (가)가 `owned` 를 `'static` 동안 빌렸다고 **가정한 채 검사가 계속되니**,
  9번 줄의 이동이 「빌린 채로 옮긴 것」이 된다. **에러 하나가 다음 에러를 만든다 — 위에서부터 고친다.**
- **(가)를 지우면 남은 코드는 통과한다.** ★ 이것이 이 문항의 핵심이다.

```text
===== 소스: ex.rs =====
// 'static 의 뜻 (1) — 참조 수명. 이 참조는 프로그램 끝까지 유효하다
fn needs_static_ref(s: &'static str) { println!("참조: {}", s); }

// 'static 의 뜻 (2) — 트레이트 경계. 이 타입은 빌린 것을 품고 있지 않다
fn needs_static_bound<T: 'static>(t: T) { println!("경계: {}", std::mem::size_of_val(&t)); }

fn main() {
    let owned = String::from("소유한 문자열");

    needs_static_bound(owned);          // ★ String 은 T: 'static 을 만족한다
    needs_static_bound(42i32);          // i32 도
    needs_static_bound(vec![1, 2, 3]);  // Vec<i32> 도

    needs_static_ref("리터럴");          // &'static str
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
경계: 24
경계: 4
경계: 24
참조: 리터럴
(종료 코드 0)
```

- 같은 글자 `'static` 의 두 뜻.

| 자리 | 뜻 | `String` 은 | 지역 값의 `&` 는 |
|---|---|---|---|
| `&'static T` | **이 참조**가 프로그램 끝까지 유효하다 | 해당 없음(참조가 아니다) | ✗ **E0597** |
| `T: 'static` | **이 타입**이 짧은 빌림을 안 품었다 | ✓ **통과** | ✗ |

- ★★ **`String` 이 `T: 'static` 을 통과한다**는 것이 가장 자주 깨지는 오해다.\
  힙에 있든 방금 만들었든 상관없다 — **빌린 것을 안 품었으면 만족**한다.
- 거부되는 쪽은 **빌린 것을 품은 타입**이다.

```text
===== 소스: ex.rs =====
// T: 'static 이 거부하는 것은 「소유 아님」이 아니라 「빌린 것을 품은 타입」이다
fn needs_static_bound<T: 'static>(_t: T) { println!("통과"); }

struct Holder<'a> { r: &'a str }

fn main() {
    let owned = String::from("가나다");
    let h = Holder { r: &owned };   // 빌린 것을 품은 값
    needs_static_bound(h);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `owned` does not live long enough
  --> ex.rs:8:25
   |
 7 |     let owned = String::from("가나다");
   |         ----- binding `owned` declared here
 8 |     let h = Holder { r: &owned };   // 빌린 것을 품은 값
   |                         ^^^^^^ borrowed value does not live long enough
 9 |     needs_static_bound(h);
   |     --------------------- argument requires that `owned` is borrowed for `'static`
10 | }
   | - `owned` dropped here while still borrowed
   |
note: requirement that the value outlives `'static` introduced here
  --> ex.rs:2:26
   |
 2 | fn needs_static_bound<T: 'static>(_t: T) { println!("통과"); }
   |                          ^^^^^^^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

★ `note: requirement that the value outlives 'static introduced here` 가 **경계 자리를 직접 짚는다.**

### 5. ★ `가나다라마` 가 나올 코드였지만 컴파일되지 않는다 — E0597

**출력**

```text
===== 소스: ex.rs =====
// 'a 가 「수명을 늘려 준다」면 이것이 통과해야 한다
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    let long = String::from("가나다라마");
    let winner;
    {
        let short = String::from("가나");
        winner = longest(&long, &short);
    }
    println!("{}", winner);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `short` does not live long enough
  --> ex.rs:11:33
   |
10 |         let short = String::from("가나");
   |             ----- binding `short` declared here
11 |         winner = longest(&long, &short);
   |                                 ^^^^^^ borrowed value does not live long enough
12 |     }
   |     - `short` dropped here while still borrowed
13 |     println!("{}", winner);
   |                    ------ borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
```

**왜 그런가**

- 실행되면 `가나다라마` 가 나올 코드다(`long` 이 더 길다). 그런데 **컴파일이 거부한다.**
- 에러가 짚는 것은 **`short`** 다 — `^^^^^^` 가 `&short` 에 붙는다.
- ★ 두 입력에 **같은 이름 `'a`** 를 준 것의 뜻 —\
  **「반환값은 `x` 와 `y` **둘 다**가 살아 있는 동안만 유효하다」**. `'a` 는 **교집합**으로 좁혀진다.

```text
   long  ├──────────────────────────────────┤   (바깥 스코프)
   short         ├───────────┤                  (안쪽 스코프)
   'a            └───────────┘                  ← 교집합
   winner        ·············└──?              ← 'a 밖에서 쓰려 하니 E0597
```

- ★★ **`<'a, 'b>` 로 갈라 적어도 이 코드는 통과하지 않는다.** 던져서 확인했다 —\
  이번엔 **호출부가 아니라 몸통**이 막힌다.

```text
===== 소스: ex.rs =====
// 갈라 적은 뒤 짧은 쪽을 돌려주려 하면
fn longest<'a, 'b>(x: &'a str, y: &'b str) -> &'a str {
    if x.len() >= y.len() { x } else { y }
}

fn main() {
    let long = String::from("가나다라마");
    let winner;
    {
        let short = String::from("가나");
        winner = longest(&long, &short);
    }
    println!("{}", winner);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: lifetime may not live long enough
 --> ex.rs:3:40
  |
2 | fn longest<'a, 'b>(x: &'a str, y: &'b str) -> &'a str {
  |            --  -- lifetime `'b` defined here
  |            |
  |            lifetime `'a` defined here
3 |     if x.len() >= y.len() { x } else { y }
  |                                        ^ function was supposed to return data with lifetime `'a` but it is returning data with lifetime `'b`
  |
  = help: consider adding the following bound: `'b: 'a`

error: aborting due to 1 previous error
```

- `help: consider adding the following bound: 'b: 'a` — 시키는 대로 하면 **`'b` 가 `'a` 보다 짧지 않다**가 되어
  결국 **처음의 `'a` 하나로 묶은 것과 같은 제약**이 된다. **표기를 바꿔서 풀 문제가 아니다.**
- 제대로 고치는 길은 **반환을 소유값(`String`)으로 바꾸거나**, `winner` 를 **안쪽 블록에서 쓰는 것**이다.

### 6. ★★ 막힌다 — E0502. NLL 이 못 푸는 알려진 모양이다

**출력**

```text
===== 소스: ex.rs =====
// NLL 이 못 푸는 자리 — 한쪽 갈래에서만 빌림이 반환되는데도 전체가 막힌다
use std::collections::HashMap;

fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
    match map.get(&0) {
        Some(v) => v,
        None => {
            map.insert(0, String::from("기본값"));
            map.get(&0).unwrap()
        }
    }
}

fn main() {
    let mut m: HashMap<u32, String> = HashMap::new();
    println!("{}", get_or_insert(&mut m));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `*map` as mutable because it is also borrowed as immutable
 --> ex.rs:8:13
  |
4 | fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
  |                       - let's call the lifetime of this reference `'1`
5 |     match map.get(&0) {
  |           --- immutable borrow occurs here
6 |         Some(v) => v,
  |                    - returning this value requires that `*map` is borrowed for `'1`
7 |         None => {
8 |             map.insert(0, String::from("기본값"));
  |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ mutable borrow occurs here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**왜 그런가**

- **막힌다. E0502.** `None` 갈래에서 그 빌림을 안 쓰는데도 그렇다.
- `'1` 은 **`map` 인자의 수명** — 즉 **호출자가 정하는 구간**이다(`let's call the lifetime of this reference '1`).
- ★★ 핵심은 6번 줄 라벨이다 — **`returning this value requires that *map is borrowed for '1`**.\
  `Some` 갈래가 빌림을 **밖으로 내보내므로** 그 빌림 구간이 **`'1` 전체**로 고정되고,
  그 안에 있는 `None` 갈래의 `map.insert` 가 충돌한다.

```text
   NLL 이 하는 것과 못 하는 것

   되는 것   — 빌림 구간을 「마지막 사용」까지로 줄인다 (10번의 실측)
   ───────────────────────────────────────────────────────────
   못 하는 것 — 빌림이 「반환값」이 되면 구간이 호출자의 수명('1)으로 고정된다.
                한 갈래만 반환해도 match 전체가 '1 로 잡힌다.
```

- ★★★ **「사람 눈에 안전한데 거부됐다」와 「언어가 금지했다」는 다르다.**\
  이 코드는 **안전하다.** 거부된 이유는 **검사기가 안전을 증명하지 못했기 때문**이고,
  Rust 팀이 「NLL problem case #3」로 부르는 **알려진 한계**다.\
  ★ 「거부됐다 = 위험하다」로 읽으면 이 주제에서 가장 크게 잘못 배운다.
- **처방은 코드를 바꾸는 것**이다 — 빌림을 갈래 밖으로 뺀다. 대가는 **탐색 한 번 더**다.

```text
===== 소스: ex.rs =====
// NLL 이 못 푸는 자리를 사람이 푼다 — 빌림을 갈래 밖으로 뺀다
use std::collections::HashMap;

fn get_or_insert(map: &mut HashMap<u32, String>) -> &String {
    if !map.contains_key(&0) {              // 빌림이 이 줄에서 끝난다
        map.insert(0, String::from("기본값"));
    }
    map.get(&0).unwrap()                    // 새로 빌린다
}

fn main() {
    let mut m: HashMap<u32, String> = HashMap::new();
    println!("{}", get_or_insert(&mut m));
    m.insert(0, String::from("바뀐값"));
    println!("{}", get_or_insert(&mut m));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
기본값
바뀐값
(종료 코드 0)
```

★ 같은 모양의 다른 처방(`entry` API)과 그 밖의 전형은 [**11번 주제**](../11-borrow-checker-rejections/)가 정본이다.

### 7. 생략 규칙 세 개 — 그리고 2와 3은 겹치지 않는다

**출력**

```text
   시그니처를 받았다
        │
        ▼
   ① 출력에 참조가 있나? ── 아니오 ──▶ 끝. 아무것도 안 적어도 된다
        │ 예
        ▼
   ② 입력에 &self / &mut self 가 있나? ── 예 ──▶ 출력 = self 의 수명 (규칙 3). 끝
        │ 아니오
        ▼
   ③ 생략된 입력 수명이 정확히 하나인가? ── 예 ──▶ 출력 = 그 수명 (규칙 2). 끝
        │ 아니오 (0개 또는 2개 이상)
        ▼
   E0106. 직접 적어야 한다.
```

**왜 그런가**

| # | 규칙 | 한 줄 |
|---|------|------|
| **1** | **입력** 자리의 생략된 수명은 **각각 제 이름**을 받는다 | 항상 돈다 |
| **2** | 생략된 입력 수명이 **정확히 하나**면 그것을 **모든 출력**에 준다 | 출력에 참조가 있을 때만 |
| **3** | 입력에 **`&self`·`&mut self`** 가 있으면 **self 의 수명**을 모든 출력에 준다 | 〃 |

- **규칙 1만으로 끝나는 모양** — **출력에 참조가 없는** 시그니처다. 입력 수명이 몇 개든 상관없다.

```text
===== 소스: ex.rs =====
// 생략 규칙 1 — 입력마다 제 수명을 받는다. 출력에 참조가 없으면 그것으로 끝이다.
fn cmp_len(a: &str, b: &str) -> usize { a.len() + b.len() }

// 손으로 푼 것
fn cmp_len_explicit<'a, 'b>(a: &'a str, b: &'b str) -> usize { a.len() + b.len() }

fn main() {
    println!("{} {}", cmp_len("가", "나다"), cmp_len_explicit("가", "나다"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
9 9
(종료 코드 0)
```

- ★ **규칙 2가 세는 것은 인자 개수가 아니라 「생략된 입력 수명」 개수**다.\
  인자가 셋이어도 **참조가 하나면** 규칙 2가 푼다 — `usize`·`char` 에는 수명이 없다.

```text
===== 소스: ex.rs =====
// 입력 참조가 하나뿐이면 다른 인자가 몇 개든 규칙 2 가 푼다
fn take(s: &str, n: usize, pad: char) -> &str {
    let _ = pad;
    &s[..n]
}

fn main() { println!("{}", take("hello", 3, '-')); }
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
hel
(종료 코드 0)
```

- ★★ **「둘 다 쓰일 수 있을 때 어느 쪽이 이기나」는 함정 질문**이다 — **겹치는 자리가 없다.**\
  규칙 2는 **생략된 입력 수명이 정확히 하나**일 때만 돈다. 그 하나가 `&self` 라면 **규칙 3도 같은 답**을 준다.\
  입력 수명이 **둘 이상**이면 규칙 2는 아예 안 돌고 규칙 3만 남는다.\
  그래서 규칙 3은 **규칙 2를 이기는 것이 아니라 규칙 2가 못 맡는 자리를 맡는다.**
- 규칙 3이 자리(`self`)를 본다는 것은 3번 답의 `Parser::pick` 실측이 보여 준다.

### 8. 안 산다 — E0106 이 E0515 로 바뀔 뿐이다

**출력**

```text
===== 소스: ex.rs =====
// 지역 값의 참조를 돌려주려 하면
fn make_ref() -> &String {
    let s = String::from("가나다");
    &s
}

fn main() { println!("{}", make_ref()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:2:18
  |
2 | fn make_ref() -> &String {
  |                  ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value, but there is no value for it to be borrowed from
help: consider using the `'static` lifetime, but this is uncommon unless you're returning a borrowed value from a `const` or a `static`
  |
2 | fn make_ref() -> &'static String {
  |                   +++++++
help: instead, you are more likely to want to return an owned value
  |
2 - fn make_ref() -> &String {
2 + fn make_ref() -> String {
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

`'a` 를 붙이면 이렇게 바뀐다.

```text
===== 소스: ex.rs =====
// 수명을 적어 주면 통과하나 — 'a 를 붙여 본다
fn make_ref<'a>() -> &'a String {
    let s = String::from("가나다");
    &s
}

fn main() { println!("{}", make_ref()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0515]: cannot return reference to local variable `s`
 --> ex.rs:4:5
  |
4 |     &s
  |     ^^ returns a reference to data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

**왜 그런가**

- 처음은 **E0106**(칸이 비었다), `'a` 를 붙이면 **E0515**(적힌 대로면 거짓말이다).
- ★★ 한 문장으로 — **`'a` 는 계약서의 빈 칸을 채우는 것이지 값을 살려 주는 주문이 아니다.**\
  칸을 채우면 검사가 **다음 단계로 넘어갈 뿐**이고, 계약을 못 지키면 거기서 또 막힌다.

```text
   전:  출력 수명 칸이 비었다        -> E0106  「어디서 왔는지 안 적혔다」
   후:  출력 수명 칸에 'a 가 찼다    -> E0515  「적힌 대로면 거짓말이다」
```

- **제대로 고치는 법** — 컴파일러가 두 번째 `help:` 로 이미 알려 줬다.\
  `fn make_ref() -> String` 으로 **소유값을 돌려준다.** 참조를 돌려주려면 **빌려올 입력이 있어야** 한다.

### 9. 같은 E0106 인데 `help:` 가 셋 다 다르다

**출력**

| 상황 | `help:` 의 핵심 구절 | 권하는 고침 |
|---|---|---|
| 입력이 **둘**인 함수 | `does not say whether it is borrowed from x or y` | `<'a>` 를 넣고 셋에 `'a` |
| 입력이 **없는** 함수 | `there is no value for it to be borrowed from` | ★ **`'static`** 또는 **소유값 반환** |
| **구조체 필드** | (이유 구절 없음) `consider introducing a named lifetime parameter` | `struct X<'a>` |

```text
===== 소스: ex.rs =====
// 참조를 필드로 담으면 — 구조체 쪽 E0106 은 문구가 다르다
struct Excerpt { part: &str }

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    let e = Excerpt { part: novel.split('.').next().unwrap() };
    println!("{}", e.part);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:2:24
  |
2 | struct Excerpt { part: &str }
  |                        ^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
2 | struct Excerpt<'a> { part: &'a str }
  |               ++++          ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

**왜 그런가**

- ★ **구조체 필드에는 생략 규칙 2·3이 없다.** 두 규칙은 **함수 시그니처의 입력·출력** 이야기인데,
  구조체 필드에는 「입력」도 「출력」도 없다. **참조를 담으면 항상 수명 파라미터가 필요하다.**
- 그래서 구조체 쪽 진단에는 **이유 구절(`= help:`)이 아예 없다** — 물어볼 후보가 없기 때문이다. 바로 처방만 준다.
- ★★ **「에러 번호가 같으면 원인도 같다」가 여기서 안 통한다.**\
  E0106 은 「수명 칸이 비었다」라는 **증상 하나**에 붙은 번호이고, **원인은 셋 다 다르다.**\
  그래서 이 주제에서는 **번호보다 `help:` 문구를 읽는 것**이 빠르다.
- **`'static` 을 권하는 것은 「입력이 없는 함수」** 뿐이다. 그나마도\
  `but this is uncommon unless you're returning a borrowed value from a const or a static` 라고 **스스로 단서를 단다.**

### 10. 오브젝트 파일이 바이트 단위로 같다

**출력**

```text
===== 소스: ex.rs (생략형) =====
// 수명이 런타임에 남는가 — 생략형과 명시형을 각각 컴파일해 기계어를 비교한다
pub fn first_word(s: &str) -> &str {
    s.split(' ').next().unwrap()
}
fn main() { println!("{}", first_word("hello rust")); }
===== 소스: ex.rs (명시형) =====
// 수명이 런타임에 남는가 — 명시형
pub fn first_word<'a>(s: &'a str) -> &'a str {
    s.split(' ').next().unwrap()
}
fn main() { println!("{}", first_word("hello rust")); }
===== rustc --edition 2021 -O --emit=obj ex.rs -o a_elided.o / a_explicit.o =====
-rw-rw-r-- 1 jun jun 4624  9월 24 03:02 a_elided.o
-rw-rw-r-- 1 jun jun 4624  9월 24 03:02 a_explicit.o
cmp: 바이트 단위로 같다
6ad33506f02a06a39c0b57bc77e3bdbcb938a0c4560232da9337743fbdc2995c  a_elided.o
6ad33506f02a06a39c0b57bc77e3bdbcb938a0c4560232da9337743fbdc2995c  a_explicit.o
```

**왜 그런가**

- ★ **반드시 맞춰야 하는 조건은 「소스 파일 이름」이다.**\
  (`ls -l` 의 날짜·시각은 그 실행의 것이라 다시 찍으면 바뀐다. 근거로 읽을 칸은 **크기와 해시**뿐이다.)\
  ★★ **처음에 `t12-21.rs`·`t12-22.rs` 로 두고 쟀더니 「다르다」가 나왔다** — 921바이트째부터 갈렸다.\
  **파일 이름이 오브젝트 안에 박히기 때문**이다. 둘 다 `ex.rs` 로 맞추니 **sha256 까지 같아졌다.**\
  이 실패를 지우지 않는 이유는 **「다르다」를 그대로 믿었으면 정반대 결론을 적을 뻔했기 때문**이다.
- 결과가 동시에 말해 주는 **두 가지**.

| | 무엇을 말하나 |
|---|---|
| **①** | **생략형과 명시형은 같은 것**이다 — 타입만이 아니라 **생성물까지** 같다 |
| **②** | **수명은 런타임에 아무것도 아니다** — 기계어에 흔적이 없다 |

- 「수명 검사가 런타임 비용을 낸다」는 **거짓**이다. 전부 컴파일 타임 판정이고 **코드 생성에 안 남는다.**\
  10번에서 빌림 검사에 대해 같은 결론을 냈다 — **수명은 그 검사의 표기 층**이다.

### 11. `'_` 는 「참조가 있다」를 눈에 보이게 한다 — 그리고 임시값 스코프는 에디션에 달렸다

**출력**

```text
===== 소스: ex.rs =====
// '_ 를 빼면? — 경로에서 수명을 생략한 것이다
#![deny(elided_lifetimes_in_paths)]
struct Excerpt<'a> { part: &'a str }

fn first_sentence(novel: &str) -> Excerpt {
    Excerpt { part: novel.split('.').next().unwrap() }
}

fn main() {
    let novel = String::from("첫 문장. 둘째 문장.");
    println!("{}", first_sentence(&novel).part);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: hidden lifetime parameters in types are deprecated
 --> ex.rs:5:35
  |
5 | fn first_sentence(novel: &str) -> Excerpt {
  |                                   ^^^^^^^ expected lifetime parameter
  |
note: the lint level is defined here
 --> ex.rs:2:9
  |
2 | #![deny(elided_lifetimes_in_paths)]
  |         ^^^^^^^^^^^^^^^^^^^^^^^^^
help: indicate the anonymous lifetime
  |
5 | fn first_sentence(novel: &str) -> Excerpt<'_> {
  |                                          ++++

warning: hiding a lifetime that's elided elsewhere is confusing
 --> ex.rs:5:26
  |
5 | fn first_sentence(novel: &str) -> Excerpt {
  |                          ^^^^     ^^^^^^^ the same lifetime is hidden here
  |                          |
  |                          the lifetime is elided here
  |
  = help: the same lifetime is referred to in inconsistent ways, making the signature confusing
  = note: `#[warn(mismatched_lifetime_syntaxes)]` on by default
help: use `'_` for type paths
  |
5 | fn first_sentence(novel: &str) -> Excerpt<'_> {
  |                                          ++++

error: aborting due to 1 previous error; 1 warning emitted
```

**왜 그런가**

- **둘 다 컴파일된다.** `#![deny(elided_lifetimes_in_paths)]` 를 **내가 켰을 때만** 에러가 된다\
  (기본은 `allow`). `'_` 를 적은 판은 그냥 돈다 — `첫 문장`.
- ★ **`&str` 에서 생략한 것과 `Excerpt` 에서 생략한 것은 보이는 정도가 다르다.**\
  앞은 `&` 가 있어 「참조구나」가 보이고, **뒤는 타입 이름만 봐서는 참조를 품었는지 모른다.**\
  그래서 `'_` 로 **「여기 수명이 있다」는 표시만이라도 남기라**는 린트가 있다.
- `mismatched_lifetime_syntaxes` 경고는 **기본 켜져 있었다**(이 툴체인 실측).\
  한 시그니처에서 **표기 방식을 섞지 마라**는 뜻이다. ★ 린트는 rustc 판마다 늘고 승격되므로 **버전에 달린 사실**이다.
- ★★ **같은 파일이 2021 에서 거부되고 2024 에서 통과하는 예** — `if let` 의 임시값 스코프다.

```text
===== 소스: ex.rs =====
// 에디션 차이 — if let 의 임시값이 else 갈래까지 사는가
use std::cell::RefCell;

fn main() {
    let c: RefCell<Option<i32>> = RefCell::new(None);
    if let Some(v) = *c.borrow() {
        println!("있음 {}", v);
    } else {
        *c.borrow_mut() = Some(7);        // 빌림 가드가 아직 살아 있나?
        println!("없음 -> 채웠다 {:?}", c);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `c` does not live long enough
  --> ex.rs:6:23
   |
 5 |     let c: RefCell<Option<i32>> = RefCell::new(None);
   |         - binding `c` declared here
 6 |     if let Some(v) = *c.borrow() {
   |                       ^---------
   |                       |
   |                       borrowed value does not live long enough
   |                       a temporary with access to the borrow is created here ...
...
12 | }
   | -
   | |
   | `c` dropped here while still borrowed
   | ... and the borrow might be used here, when that temporary is dropped and runs the destructor for type `Ref<'_, Option<i32>>`
   |
help: consider adding semicolon after the expression so its temporaries are dropped sooner, before the local variables declared by the block are dropped
   |
11 |     };
   |      +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
없음 -> 채웠다 RefCell { value: Some(7) }
(종료 코드 0)
```

- **생략 규칙 자체는 에디션에 안 달렸다.** 같은 파일을 2015·2021·2024 로 던졌더니 **출력이 한 글자도 다르지 않았다**(관찰).\
  ★ 「여러 판에서 같았다」는 보장이 아니므로, **보장 쪽 근거는 Reference 의 Lifetime elision 절이 에디션 조건을 달지 않는다는 것**이다.
- ★ `'_` 자체는 **2018 에디션부터** 쓸 수 있다.

### 12. 에러 번호 지도

**출력**

| 번호 | 언제 나나 | 이 주제의 실측 |
|---|---|---|
| **E0106** | 수명 칸이 비었다 — 생략 규칙이 못 푼다 | 1·3·8·9번 (세 가지 `help:`) |
| **E0597** | 빌린 값이 참조보다 **먼저 죽는다** | 4·5번 · `'static` 자리 · 2021의 `if let` |
| **E0515** | **지역 값**의 참조를 반환한다 | 8번 |
| **E0505** | 빌린 채로 **원본을 옮긴다** | 4번(덤으로 따라옴) |
| **E0716** | **임시값**이 참조보다 먼저 죽는다 | [**11번 주제**](../11-borrow-checker-rejections/)가 정본 |
| **E0499·E0502** | 가변 둘 / 가변+공유가 겹친다 | 6번 · [**10번 주제**](../10-borrowing-and-aliasing-rules/)가 정본 |
| **E0308** | 타입 불일치 — **수명도 타입의 일부**라 여기로 온다 | 2번 |

**왜 그런가**

- ★ **번호가 없는 진단**을 이 주제에서 만났다 — **`error: lifetime may not live long enough`**(3번·5번).\
  `--explain` 으로 찾아볼 수 없고, `'1`·`'2` 같은 **즉석 이름**으로 설명한다.
- **「빌림이 마지막 사용까지만 산다」(NLL)** 는 [**10번 주제**](../10-borrowing-and-aliasing-rules/),\
  「**거부되는 전형과 처방**」은 [**11번 주제**](../11-borrow-checker-rejections/)다.
- **참조를 필드로 담는 타입의 설계**와 `'static` 심화는 [목록의 **13번 주제**](../13-struct-references-and-static/)가 정본이다.\
  여기는 **표기와 생략 규칙까지**만 다룬다.
- ★ **에러 메시지가 고친 코드를 그대로 준 자리** — **E0106 의 `help:`** 다.\
  `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str` 를 `++++` 표시와 함께 통째로 준다.\
  ★ 다만 **8번의 `'static` 권유는 따르면 안 되는 조언**이었다 — 컴파일러도 `this is uncommon` 이라고 단서를 달았고,\
  실제로 맞는 답은 **두 번째 `help:` 의 소유값 반환**이었다. **`help:` 가 여럿이면 다 읽는다.**

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `longest` 수명 없이 | **E0106** + `help:` 가 고친 코드를 통째로 줌 | 1 |
| `longest<'a>` | **통과** — `가나다` | 1 |
| `cmp_len` 생략형·명시형 | **통과** — `9 9`(규칙 1만으로 끝나는 모양) | 7 |
| `take(s: &str, n: usize, pad: char)` | **통과** — `hel`(규칙 2는 참조 개수를 센다) | 7 |
| `for<'a> fn(&'a str) -> &'a str` 에 담기 | **통과** — `hello` | 2 |
| ★ `fn(&str) -> &'static str` 에 담기 | **E0308** + `= note:` 가 **실제 타입**을 찍음 | 2 |
| `&self` 메서드 생략형·명시형 | **통과** — `a a` | 3 |
| ★ `&self` 메서드에서 `sep` 반환 | **번호 없는 error** `lifetime may not live long enough` | 3·12 |
| `this: &Parser` 로 바꾼 연관 함수 | **E0106** — 규칙 3이 안 돈다 | 3 |
| `String`·`i32`·`Vec<i32>` 를 `T: 'static` 에 | **통과** — `24` · `4` · `24` | 4 |
| ★ `&owned` 를 `&'static str` 자리에 | **E0597** + **E0505**(덤) | 4 |
| `Holder<'a>` 를 `T: 'static` 에 | **E0597** + `note: requirement … introduced here` | 4 |
| `longest<'a>` 에 스코프 다른 둘 | **E0597** — `'a` 는 교집합 | 5 |
| ★ `<'a, 'b>` 로 갈라 적기 | **번호 없는 error** + `help: consider adding the following bound: 'b: 'a` | 5 |
| `get_or_insert` (match 반환) | **E0502** — NLL problem case #3 | 6 |
| `contains_key` 선분리 판 | **통과** — `기본값` / `바뀐값` | 6 |
| `fn make_ref() -> &String` | **E0106** — `help:` 둘(`'static` / 소유값) | 8·9 |
| `fn make_ref<'a>() -> &'a String` | **E0515** — 칸은 찼고 계약이 거짓 | 8 |
| `struct Excerpt { part: &str }` | **E0106** — 이유 구절 없이 처방만 | 9 |
| ★ 생략형·명시형 **오브젝트 파일 대조** | **바이트 단위 동일**(sha256 일치) | 10 |
| `-> Excerpt<'_>` | **통과** — `첫 문장` | 11 |
| `#![deny(elided_lifetimes_in_paths)]` | **error** + `mismatched_lifetime_syntaxes` **기본 경고** | 11 |
| ★ `if let` + `RefCell` **2021 / 2024** | **E0597** / **통과**(`Some(7)`) | 11 |
| 같은 파일 **2015 / 2021 / 2024** (E0106) | **출력이 한 글자도 다르지 않음** | 11 |
| `part_elided(&self) -> &str` | **E0597** — 규칙 3이 주는 수명이 짧다 | 2-summary (9) |
| `part(&self) -> &'a str` | **통과** — `첫 문장` 두 번 | 2-summary (9) |
| `pick<'long: 'short, 'short>` | **통과** — `가나다라마바사` | 2-summary (10) |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **에러 번호가 상황별로 갈리는 것** | **rustc 구현**. 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| **번호 없는 진단이 있는 것** | **rustc 구현** |
| `'1`·`'2` 같은 즉석 이름 | **rustc 의 진단 표기** |
| `mismatched_lifetime_syntaxes` 가 **기본 경고** | **rustc 판** — 린트는 판마다 추가·승격된다 |
| **NLL 이 `get_or_insert` 를 못 푸는 것** | **현재 검사기의 한계** — 언어가 금지한 것이 아니다 |
| `if let` 임시값 스코프 | **에디션**(2024에서 변경) |
| 오브젝트 파일 **바이트 동일** | **같은 파일명·같은 플래그**가 전제다(`-O --emit=obj`, 둘 다 `ex.rs`) |
| 오브젝트 파일에 **소스 파일명이 박히는 것** | **rustc·플랫폼 구현** |
| **생략 규칙 3개·`'static` 두 뜻·`'a` 가 수명을 안 늘리는 것** | **전부 언어 보장.** 실측과 Reference 가 일치했다 |
