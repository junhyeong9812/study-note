# rust/syntax/05 — 제어 흐름: `loop`·`while`·`for`·라벨 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **10번 문항만 `--edition 2018` 과 `--edition 2021` 을 둘 다** 돌렸다(그 문항이 에디션 차이를 묻는다).\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다. **줄 번호는 그 실험 파일 기준**이라 질문의 발췌와 어긋날 수 있다.\
> 버전 사실(1.41.0·1.53.0·1.65.0)은 이 머신 `rust-docs` 의 `html/releases.md` 에서 해당 절을 찾아 확인했다.\
> 타입의 근거는 **컴파일 에러**다 — `let _: () = 식;` 으로 일부러 틀린 타입을 줘 물어보는 수법([**04번 주제**](../04-expressions-and-semicolons/) 8번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 세 반복문을 값 자리에 놓으면

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    let mut i = 0;
    let a: i32 = while i < 3 { i += 1; };
    let b: i32 = for _ in 0..3 { };
    let c: i32 = loop { break; };
    println!("{a} {b} {c}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:3:18
  |
3 |     let a: i32 = while i < 3 { i += 1; };
  |            ---   ^^^^^^^^^^^^^^^^^^^^^^^ expected `i32`, found `()`
  |            |
  |            expected due to this

error[E0308]: mismatched types
 --> ex.rs:4:18
  |
4 |     let b: i32 = for _ in 0..3 { };
  |                  ^^^^^^^^^^^^^^^^^ expected `i32`, found `()`
  |
  = note: `for` loops evaluate to unit type `()`

error[E0308]: mismatched types
 --> ex.rs:5:25
  |
5 |     let c: i32 = loop { break; };
  |         -        ----   ^^^^^ expected `i32`, found `()`
  |         |        |
  |         |        this loop is expected to be of type `i32`
  |         expected because of this assignment
  |
help: give the `break` a value of the expected type
  |
5 |     let c: i32 = loop { break 42; };
  |                               ++

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **세 줄 다 거부된다.** 에러 번호는 **셋 다 E0308**(mismatched types)이고, 전부 `found ()` 다.
- ★ `note` 가 붙는 것은 **`for` 줄 하나뿐**이다 — 「**`for` loops evaluate to unit type `()`**」.\
  `while` 도 같은 사실인데 그 줄이 없다. **메시지 모양은 언어 규칙이 아니라 rustc 구현**이라는 증거다.
- `c` 줄의 `help:` 는 **`break` 에 값을 주라**고 한다 — `break 42;` 로 `++` 를 붙여 보여 준다.

```text
   while ... { }        for ... { }          loop { break; }
        |                    |                     |
      타입 ()              타입 ()               타입 ()
        |                    |                     |
        +--------------------+---------------------+
                             v
                      i32 자리에 못 들어간다 -> E0308 ×3
```

- 앞의 둘은 **고칠 길이 없다**(그 루프는 원래 값을 못 낸다). 셋째만 `break 42` 로 고쳐진다.
- 그래서 **값을 내는 반복은 `loop` 뿐**이라는 결론이 이 한 파일에 다 들어 있다.

> **유닛 타입 `()`** — 값이 하나뿐인 타입. 크기 0바이트.\
> 예: `while`·`for` 루프 전체의 값이 `()` 라서 `let a: i32 = while ...` 이 거부된다.

### 2. ★ `break` 에 값을 붙이면

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    let mut i = 0;
    let a = while i < 3 { i += 1; break 7; };
    let b = for k in 0..3 { break k; };
    println!("{a:?} {b:?}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0571]: `break` with value from a `while` loop
 --> ex.rs:3:35
  |
3 |     let a = while i < 3 { i += 1; break 7; };
  |             -----------           ^^^^^^^ can only break with a value inside `loop` or breakable block
  |             |
  |             you can't `break` with a value in a `while` loop
  |
help: use `break` on its own without a value inside this `while` loop
  |
3 -     let a = while i < 3 { i += 1; break 7; };
3 +     let a = while i < 3 { i += 1; break; };
  |

error[E0571]: `break` with value from a `for` loop
 --> ex.rs:4:29
  |
4 |     let b = for k in 0..3 { break k; };
  |             -------------   ^^^^^^^ can only break with a value inside `loop` or breakable block
  |             |
  |             you can't `break` with a value in a `for` loop
  |
help: use `break` on its own without a value inside this `for` loop
  |
4 -     let b = for k in 0..3 { break k; };
4 +     let b = for k in 0..3 { break; };
  |

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0571`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0571** — 1번의 E0308과 **다른 번호**다.
- `^^^` 자리의 한 줄은 「**can only break with a value inside `loop` or breakable block**」이다.
- `help:` 는 **값을 떼라**고 한다 — `break 7;` → `break;`.
- 1번과 층이 다르다는 것이 요점이다.

```text
   let a: i32 = while ... { };        let a = while ... { break 7; };
             |                                       |
      "타입이 안 맞는다"                    "이 루프에서는 값을 못 낸다"
             |                                       |
             v                                       v
          E0308 (타입 층)                        E0571 (문법 층)
```

`rustc --explain E0571` 이 어느 루프들인지 이름으로 지목한다.

> The `break` statement can take an argument (which will be the value of the loop
> expression if the `break` statement is executed) in `loop` loops, but not
> `for`, `while`, or `while let` loops.

- **`while let` 까지 이름으로 적혀 있다.** `while let` 의 정본은 [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)다.

### 3. ★ 순회한 뒤에 원본이 남는가

**출력** — (가) `Vec<String>`

```text
===== 소스: ex.rs =====
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    for x in v {
        println!("{x}");
    }
    println!("{:?}", v);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `v`
 --> ex.rs:6:22
  |
2 |     let v = vec![String::from("a"), String::from("b")];
  |         - move occurs because `v` has type `Vec<String>`, which does not implement the `Copy` trait
3 |     for x in v {
  |              - `v` moved due to this implicit call to `.into_iter()`
...
6 |     println!("{:?}", v);
  |                      ^ value borrowed here after move
  |
note: `into_iter` takes ownership of the receiver `self`, which moves `v`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/collect.rs:310:18
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider iterating over a slice of the `Vec<String>`'s content to avoid moving into the `for` loop
  |
3 |     for x in &v {
  |              +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**출력** — (나) `[i32; 3]`

```text
===== 소스: ex.rs =====
fn main() {
    let a = [10, 20, 30];
    for x in a { print!("{x} "); }
    println!("| a = {:?}", a);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
10 20 30 | a = [10, 20, 30]
(종료 코드 0)
```

**왜 그런가**

- 컴파일되는 것은 **(나)** 다. (가)는 **E0382**로 거부된다.
- 보이지 않는 호출의 이름은 **`.into_iter()`** 다 — 「`v` moved due to this **implicit call to `.into_iter()`**」.\
  `for` 가 `IntoIterator` 규약으로 돈다는 사실이 **에러 메시지에 적혀 나온다.**\
  규약 전수는 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)가 정본이고, 여기서는 **이 현상까지**다.
- `help:` 가 제안하는 수정은 **글자 하나** — `for x in &v` 의 `&` 다.
- ★ **두 쪽이 갈리는 근거는 `for` 에 있지 않다.**

```text
        규칙은 하나다: for x in <값> 은 그 값을 가져간다
                            |
            +---------------+---------------+
            |                               |
     Vec<String> 은 Copy 가 아니다      [i32; 3] 은 Copy 다
            |                               |
      원본이 넘어간다                   사본이 넘어간다
            |                               |
            v                               v
     다음 줄에서 E0382                 a 는 그대로 [10, 20, 30]
```

- 갈림의 근거는 **그 타입이 `Copy` 인가**다. 판정의 정본은 [목록의 **09번 주제**](../09-copy-clone-and-drop/)다.
- ★ **이 자리가 이 주제에서 제일 잘 헷갈린다** — 배열로 배우면 에러를 한 번도 안 보고 잘못된 규칙을 갖게 된다.

> **이동(move)** — 값의 소유권이 넘어가 원래 이름을 못 쓰게 되는 것.\
> 예: `for x in v` 뒤의 `v`. 정본은 [**08번 주제**](../08-ownership-and-move/).

### 4. 순회 형태 셋이 각각 주는 것

**출력** — 타입을 물어본다

```text
===== 소스: ex.rs =====
fn main() {
    let mut v = vec![10, 20, 30];
    for x in &v      { let _: () = x; }
    for x in &mut v  { let _: () = x; }
    for x in v       { let _: () = x; }
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:3:36
  |
3 |     for x in &v      { let _: () = x; }
  |                               --   ^ expected `()`, found `&{integer}`
  |                               |
  |                               expected due to this

error[E0308]: mismatched types
 --> ex.rs:4:36
  |
4 |     for x in &mut v  { let _: () = x; }
  |                               --   ^ expected `()`, found `&mut {integer}`
  |                               |
  |                               expected due to this

error[E0308]: mismatched types
 --> ex.rs:5:36
  |
5 |     for x in v       { let _: () = x; }
  |                               --   ^ expected `()`, found integer
  |                               |
  |                               expected due to this

error: aborting due to 3 previous errors

For more information about this error, try `rustc --explain E0308`.
```

**출력** — 제대로 쓰면

```text
===== 소스: ex.rs =====
fn main() {
    let mut v = vec![10, 20, 30];

    for x in &v { print!("{x} "); }          // x: &i32
    println!("| &v 뒤에도 v = {:?}", v);

    for x in &mut v { *x += 1; }             // x: &mut i32
    println!("| &mut v 뒤에 v = {:?}", v);

    let mut sum = 0;
    for x in v { sum += x; }                 // x: i32 — v 를 먹는다
    println!("| v 를 먹고 합 = {sum}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
10 20 30 | &v 뒤에도 v = [10, 20, 30]
| &mut v 뒤에 v = [11, 21, 31]
| v 를 먹고 합 = 63
(종료 코드 0)
```

**왜 그런가**

- 타입은 각각 **`&{integer}`** · **`&mut {integer}`** · **`integer`** 다.\
  (`{integer}` 는 아직 `i32` 로 확정되기 전의 정수 추론 변수라는 표시다.)
- 둘째 형태로 원소를 고치려면 몸통에 **역참조 `*`** 를 쓴다 — `*x += 1`. 실측에서 `[11, 21, 31]` 이 됐다.
- 순회 뒤 `v` 를 다시 쓸 수 있는 것은 **둘**이다(`&v`·`&mut v`). 셋째는 `v` 를 가져간다.
- `v.iter()` 는 **`&v` 와 같은 것**을 준다(실측 — 둘 다 컴파일되고 `v` 가 남는다).

```text
     for x in &v        for x in &mut v       for x in v
          |                   |                    |
       &i32                &mut i32               i32
      읽기만              *x 로 고친다          가져간다
          |                   |                    |
          v                   v                    v
    [10,20,30] 그대로    [11,21,31] 로 남는다    v 가 사라진다
```

### 5. 라벨을 붙이면 무엇이 달라지나

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    // 1) 라벨 없는 break 는 가장 안쪽만 빠져나온다
    let mut hit = Vec::new();
    for a in 0..3 {
        for b in 0..3 {
            if b == 1 { break; }
            hit.push((a, b));
        }
    }
    println!("라벨 없음: {:?}", hit);

    // 2) 라벨 break 는 바깥까지 빠져나온다
    let mut hit2 = Vec::new();
    'outer: for a in 0..3 {
        for b in 0..3 {
            if a == 1 && b == 1 { break 'outer; }
            hit2.push((a, b));
        }
    }
    println!("라벨 break: {:?}", hit2);

    // 3) 라벨 continue
    let mut hit3 = Vec::new();
    'row: for a in 0..3 {
        for b in 0..3 {
            if b == 1 { continue 'row; }
            hit3.push((a, b));
        }
    }
    println!("라벨 continue: {:?}", hit3);

    // 4) 라벨 있는 loop 는 값을 낸다
    let target = 'search: loop {
        for a in 1..100 {
            if a * a > 500 { break 'search a; }
        }
        break 0;
    };
    println!("라벨 break 값 = {target}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
라벨 없음: [(0, 0), (1, 0), (2, 0)]
라벨 break: [(0, 0), (0, 1), (0, 2), (1, 0)]
라벨 continue: [(0, 0), (1, 0), (2, 0)]
라벨 break 값 = 23
(종료 코드 0)
```

**왜 그런가**

- `hit` = **`[(0, 0), (1, 0), (2, 0)]`** — 안쪽만 끝나므로 `a` 가 0·1·2 를 다 돈다.
- `hit2` = **`[(0, 0), (0, 1), (0, 2), (1, 0)]`** — `(1,1)` 에 닿는 순간 **바깥까지 끝난다.**
- ★ (3)은 **컴파일되고 값이 23**이다. `break 'search a` 가 **`for` 문 안에 있는데도** 값을 냈다.\
  23² = 529 > 500 이고 22² = 484 라서 23이다.

**한 기준으로 묶으면 — 「어디서 `break` 하나」가 아니라 「무엇을 가리키나」다**

```text
   'search: loop {  for a { break 'search a; }  }     'outer: for a {  for b { break 'outer a; }  }
       |                        |                          |                       |
   라벨이 loop 에 붙었다     break 는 for 안        라벨이 for 에 붙었다      break 는 for 안
       |                        |                          |                       |
       +-----------+------------+                          +-----------+-----------+
                   v                                                   v
            통과 — 값 23 이 나온다                                  E0571 거부
```

- **`break` 의 위치는 둘 다 `for` 안으로 같다.** 갈린 것은 **라벨이 붙은 루프의 종류**뿐이다.
- `continue 'row` 는 **그 라벨 루프의 다음 바퀴**로 간다 — 안쪽을 끝내는 것이 아니라 바깥을 한 바퀴 넘긴다.\
  위 실측에서 `hit3` 가 `hit` 와 같아 보이는 것은 **우연**이다. 안쪽 `for` 뒤에 문장을 하나 두면 갈린다.

```text
===== 소스: ex.rs =====
fn main() {
    // 안쪽 for 뒤에 문장을 하나 두면 break 와 continue '라벨 이 갈린다
    let mut tail1 = Vec::new();
    for a in 0..3 {
        for b in 0..3 {
            if b == 1 { break; }
        }
        tail1.push(a);              // 라벨 없는 break 는 여기를 지난다
    }
    println!("break       뒤 바깥 몸통: {:?}", tail1);

    let mut tail2 = Vec::new();
    'row: for a in 0..3 {
        for b in 0..3 {
            if b == 1 { continue 'row; }
        }
        tail2.push(a);              // continue 'row 는 여기를 건너뛴다
    }
    println!("continue 'row 뒤 바깥 몸통: {:?}", tail2);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
break       뒤 바깥 몸통: [0, 1, 2]
continue 'row 뒤 바깥 몸통: []
(종료 코드 0)
```

- ★ **같은 출력을 근거로 「같은 동작」이라고 적을 뻔한 자리다.** 둘을 가르는 것은 **바깥 몸통의 나머지**를 지나느냐다.

### 6. 루프 밖의 `break` 와 없는 라벨

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    break;
    'a: for _ in 0..1 {}
    for _ in 0..1 { break 'nope; }
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0426]: use of undeclared label `'nope`
 --> ex.rs:4:27
  |
4 |     for _ in 0..1 { break 'nope; }
  |                           ^^^^^ undeclared label `'nope`

warning: unused label
 --> ex.rs:3:5
  |
3 |     'a: for _ in 0..1 {}
  |     ^^
  |
  = note: `#[warn(unused_labels)]` (part of `#[warn(unused)]`) on by default

error[E0268]: `break` outside of a loop or labeled block
 --> ex.rs:2:5
  |
2 |     break;
  |     ^^^^^ cannot `break` outside of a loop or labeled block

error: aborting due to 2 previous errors; 1 warning emitted

Some errors have detailed explanations: E0268, E0426.
For more information about an error, try `rustc --explain E0268`.
```

**왜 그런가**

- 에러 둘은 **E0426**(use of undeclared label `'nope`)과 **E0268**(`break` outside of a loop or labeled block)이다.
- 경고 하나는 **`unused_labels`** 이고, 지적 대상은 **선언만 하고 아무도 안 가리키는 라벨 `'a`** 다.
- ★ **경고가 유용한 자리** — 리팩터링으로 `break 'outer` 를 지우고 **이름표만 남겼을 때**다.\
  컴파일은 통과하므로 **경고를 안 읽으면 죽은 라벨이 계속 남는다.**
- 에러로 올리는 법 — `-D warnings` 또는 `#![deny(unused_labels)]`.
- 이 린트는 **1.41.0 (2020-01-30)** 부터 있다(`releases.md` — 「Rustc will now warn if you have unused loop `'label`s」).

`rustc --explain E0268`:

> A loop keyword (`break` or `continue`) was used outside of a loop.
> (…) Without a loop to break out of or continue in, no sensible action can be taken.
> Please verify that you are using `break` and `continue` only in loops.

### 7. `break` 가 하나도 없는 `loop`

**출력**

```text
===== 소스: ex.rs =====
fn forever() -> i32 {
    loop {}                 // 타입이 ! 라 i32 자리에 그대로 들어간다
}
fn main() {
    let a: i32 = if false { forever() } else { 1 };
    let b: String = if false { loop {} } else { String::from("s") };
    let c: () = loop { break; };
    println!("a = {a} / b = {b} / c = {c:?}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
a = 1 / b = s / c = ()
(종료 코드 0)
```

**왜 그런가**

- `fn forever() -> i32 { loop {} }` 가 컴파일되는 이유는 **`loop {}` 의 타입이 `!`**(발산)이기 때문이다.\
  「값을 낼 길이 없다」는 사실 자체가 타입이고, **`!` 는 어떤 타입으로도 강제된다.**
- `String` 을 기대하는 자리에 둬도 **그대로 통과한다**(실측 — `b = s`). `i32` 전용 성질이 아니다.
- `loop { break; }` 로 바꾸면 **타입이 `()` 가 된다.** 그때부터 `i32` 자리에는 못 들어간다(1번의 셋째 에러).

```text
      loop { }                  loop { break; }
         |                             |
    나올 길이 없다                 나올 길이 있다
         |                             |
      타입 !                        타입 ()
         |                             |
  i32·String 어디든 통과          () 자리에만 통과
```

- **정본은 [**06번 주제**](../06-functions-and-never-type/)**(함수·반환·발산 타입 `!`)다.\
  이 주제는 **`loop {}` 의 타입이 `!` 라는 자리까지**만 다룬다 — `panic!`·`process::exit`·`-> !` 함수는 거기다.

> **발산 타입 `!`** — 값을 절대 내지 않는 것의 타입.\
> 예: `break` 없는 `loop {}`. 어떤 타입 자리에도 들어간다.

### 8. 라벨 있는 블록

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    let v = vec![3, 9, 4];
    let first_even = 'blk: {
        for x in &v {
            if x % 2 == 0 { break 'blk Some(*x); }
        }
        None
    };
    println!("{first_even:?}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
Some(4)
(종료 코드 0)
```

**왜 그런가**

- **된다.** `'blk: { ... }` 는 루프가 아닌데도 `break '라벨 값` 으로 빠져나오며 값을 낸다.
- **1.65.0 (2022-11-03)** 부터다 — `releases.md` 의 「Stabilize `break`ing from arbitrary labeled blocks ("label-break-value")」.
- ★ E0571 메시지의 「can only break with a value inside `loop` **or breakable block**」에서\
  **`breakable block`** 이 바로 이 문법을 가리킨다. **에러 메시지가 다른 문법의 존재를 알려 준다.**
- 쓰는 자리는 **「찾으면 그 값, 못 찾으면 기본값」** 이다. 이걸 쓰려고 함수를 따로 만들지 않아도 된다.
- **`continue` 는 안 된다** — 전용 에러 번호가 따로 있다.

```text
===== 소스: ex.rs =====
fn main() {
    let x = 'blk: {
        continue 'blk;
    };
    println!("{x:?}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0696]: `continue` pointing to a labeled block
 --> ex.rs:3:9
  |
2 |       let x = 'blk: {
  |  _____________-
3 | |         continue 'blk;
  | |         ^^^^^^^^^^^^^ labeled blocks cannot be `continue`'d
4 | |     };
  | |_____- labeled block the `continue` points to

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0696`.
```

- **E0696** — 「labeled blocks cannot be `continue`'d」. 루프가 아니니 **돌아갈 「다음 바퀴」가 없다.**

### 9. `continue` 에 값을 붙이면

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    let x = loop {
        continue 5;
    };
    println!("{x}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error: expected one of `.`, `;`, `?`, `}`, or an operator, found `5`
 --> ex.rs:3:18
  |
3 |         continue 5;
  |                  ^ expected one of `.`, `;`, `?`, `}`, or an operator

warning: unreachable statement
 --> ex.rs:5:5
  |
2 |       let x = loop {
  |  _____________-
3 | |         continue 5;
4 | |     };
  | |_____- any code following this expression is unreachable
5 |       println!("{x}");
  |       ^^^^^^^^^^^^^^^ unreachable statement
  |
  = note: `#[warn(unreachable_code)]` (part of `#[warn(unused)]`) on by default
  = note: this warning originates in the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error; 1 warning emitted
```

**왜 그런가**

- **컴파일되지 않는다.** 그리고 ★ **에러 번호가 없다.**
- 번호가 없다는 것은 **파서가 거부했다**는 뜻이다 — 문장을 읽는 단계에서 이미 틀렸다.\
  E0571 은 문장은 읽혔고 **의미 검사**에서 거부된 것이라 번호가 있다. **거부된 단계가 다르다.**
- `continue` 뒤에 올 수 있는 것은 **라벨뿐**이다. 「다음 바퀴에 값을 넘긴다」는 개념 자체가 언어에 없다.
- 덤으로 `unreachable_code` 경고가 붙는다 — `loop` 가 값을 낼 길이 없어 뒷줄에 못 닿기 때문이다(7번과 같은 성질).

```text
   continue 5;          break 7;  (while 안)
        |                     |
   파서가 막는다          파서는 통과, 의미 검사가 막는다
        |                     |
        v                     v
   번호 없는 error          error[E0571]
```

### 10. ★ 같은 파일, 다른 에디션

**출력** — 실행

```text
===== 소스: ex.rs =====
fn main() {
    let a = [10, 20, 30];
    let mut sum = 0;
    for x in a.into_iter() {
        sum += x;
    }
    println!("sum = {sum}");
}
===== 2018: rustc --edition 2018 ex.rs -o e18 =====
warning: this method call resolves to `<&[T; N] as IntoIterator>::into_iter` (due to backwards compatibility), but will resolve to `<[T; N] as IntoIterator>::into_iter` in Rust 2021
 --> ex.rs:4:16
  |
4 |     for x in a.into_iter() {
  |                ^^^^^^^^^
  |
  = warning: this changes meaning in Rust 2021
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2021/IntoIterator-for-arrays.html>
  = note: `#[warn(array_into_iter)]` (part of `#[warn(rust_2021_compatibility)]`) on by default
help: use `.iter()` instead of `.into_iter()` to avoid ambiguity
  |
4 -     for x in a.into_iter() {
4 +     for x in a.iter() {
  |
help: or remove `.into_iter()` to iterate by value
  |
4 -     for x in a.into_iter() {
4 +     for x in a {
  |

warning: 1 warning emitted

sum = 60
(종료 코드 0)
===== 2021: rustc --edition 2021 ex.rs -o e21 =====
sum = 60
(종료 코드 0)
```

**출력** — 타입을 물어보면

```text
===== 소스: ex.rs =====
fn main() {
    let a = [10, 20, 30];
    for x in a.into_iter() {
        let _: () = x;          // x 의 진짜 타입을 컴파일러에게 물어본다
    }
}
===== 2018: rustc --edition 2018 ex.rs -o e18 =====
error[E0308]: mismatched types
 --> ex.rs:4:21
  |
4 |         let _: () = x;          // x 의 진짜 타입을 컴파일러에게 물어본다
  |                --   ^ expected `()`, found `&{integer}`
  |                |
  |                expected due to this

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
===== 2021: rustc --edition 2021 ex.rs -o e21 =====
error[E0308]: mismatched types
 --> ex.rs:4:21
  |
4 |         let _: () = x;          // x 의 진짜 타입을 컴파일러에게 물어본다
  |                --   ^ expected `()`, found integer
  |                |
  |                expected due to this

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- ★★ **출력은 같다.** 양쪽 다 `sum = 60` 이고 **한 글자도 다르지 않다.**
- 2018 에서만 나는 경고의 린트 이름은 **`array_into_iter`** 다(`rust_2021_compatibility` 묶음).
- `x` 의 타입은 **2018 에서 `&{integer}`**, **2021 에서 `integer`** 다.\
  확인하는 법은 **`let _: () = x;` 로 일부러 틀린 타입을 주는 것**이다 — 실행 결과로는 안 갈린다.
- 원소가 `String` 이었다면 **컴파일 여부가 갈렸을 것**이다.\
  2018 은 `&String` 을 주므로 소유권이 필요한 연산이 막히고, 2021 은 `String` 자체를 준다.\
  여기서는 원소가 `i32`(`Copy`)라 합이 우연히 같았다.

```text
      같은 ex.rs, 같은 rustc 1.92.0
                  |
      +-----------+-----------+
      |                       |
   --edition 2018         --edition 2021
      |                       |
  x: &{integer}           x: integer
  경고 array_into_iter     경고 없음
      |                       |
      +-----------+-----------+
                  v
            sum = 60 (양쪽 동일)
      -> 실행 출력으로는 절대 안 갈린다
```

- 배열의 `IntoIterator` 는 **1.53.0 (2021-06-17)** 부터이고(`releases.md` — 「Arrays of any length now implement `IntoIterator`」),\
  std 문서가 에디션 예외를 못박는다.

  > Prior to Rust 1.53, arrays did not implement `IntoIterator` by value, so the method call
  > `array.into_iter()` auto-referenced into a slice iterator. Right now, the old behavior is
  > preserved in the 2015 and 2018 editions of Rust for compatibility, ignoring `IntoIterator` by value.

- ★ **`rustc ex.rs` 는 2015 에디션**이다. 그래서 이 묶음의 모든 실험은 **`--edition 2021` 로 고정**한다.

### 11. 순회하면서 원본을 바꾸면

**출력**

```text
===== 소스: ex.rs =====
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &v {
        if *x == 2 { v.push(99); }
    }
    println!("{:?}", v);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:4:22
  |
3 |     for x in &v {
  |              --
  |              |
  |              immutable borrow occurs here
  |              immutable borrow later used here
4 |         if *x == 2 { v.push(99); }
  |                      ^^^^^^^^^^ mutable borrow occurs here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**왜 그런가**

- **컴파일되지 않는다.** 에러 번호는 **E0502** 다.
- 다른 언어에서 이 상황은 보통 **실행 중에** 드러난다(자바의 `ConcurrentModificationException` 이 그 자리다).\
  Rust 는 **컴파일 타임에** 막는다 — 테스트가 그 경로를 안 밟아도 잡힌다.
- 이 규칙(불변 빌림 여럿 ↔ 가변 빌림 하나)의 정본은 [목록의 **10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`)이고,\
  고치는 관용(인덱스·`retain`·`mem::take`)은 [목록의 **11번 주제**](../11-borrow-checker-rejections/)다. 여기서는 **현상까지**다.

### 12. 다른 주제와 잇기

- **`while let`** — [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)(`if let`·`while let`·`let else`·`let` 체인).\
  이 주제에서는 `rustc --explain E0571` 이 이름을 대는 자리까지만 닿았다.
- **`iter`/`iter_mut`/`into_iter` 규약 전수** — [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)(`IntoIterator` 세 형태).
- **순회 결과를 모으는 관용** — [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)(`Iterator` 와 어댑터·`collect`).
- **`Copy` 판정** — [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`와 `Clone`, `Drop` 시점).\
  3번에서 배열과 `Vec` 이 갈린 근거가 그것이다.
- **에러가 아니라 경고로만 드러나는 자리** — 둘이다.
  - **`unused_labels`**(6번) — 라벨만 남기고 아무도 안 가리킬 때.
  - **`array_into_iter`**(10번) — 2018 에서 `배열.into_iter()` 를 쓸 때.
- ★ **그중 출력까지 같았던 것은 `array_into_iter`(10번)다.**\
  `sum = 60` 이 두 에디션에서 한 글자도 같아서, **실행 결과만 보면 아무 차이가 없다.**\
  타입 탐침(`let _: () = x;`)을 던져야만 `&{integer}` ↔ `integer` 로 갈린다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 문항 |
|---|---|---|
| `loop`/`while`/`for` 기본 3종 | `found = 8` · `3 2 1` · `0 1 2 3` · `v` 가 남음 | 1·4 |
| `let a: i32 = while` / `for` / `loop { break; }` | **E0308 ×3** · `for` 에만 `note` · `help: give the break a value` | 1 |
| `while`/`for` 안의 `break 값` | **E0571** ×2 + `help: use break on its own` | 2 |
| `rustc --explain E0571` | `loop` 만 되고 `for`·`while`·`while let` 은 안 된다는 공식 설명 | 2 |
| `for x in v` (`Vec<String>`) 뒤 `v` 사용 | **E0382** + `implicit call to .into_iter()` + `help: &v` | 3 |
| `rustc --explain E0382` | 「a value cannot be owned by more than one variable」 | 3 |
| `for x in a` (`[i32; 3]`) 뒤 `a` 사용 | **통과** — `a = [10, 20, 30]` | 3 |
| `for x in &v` / `&mut v` / `v` 타입 탐침 | `&{integer}` / `&mut {integer}` / `integer` | 4 |
| 같은 셋을 제대로 실행 | `[10,20,30]` → `[11,21,31]` → 합 `63` | 4 |
| `v.iter()` 와 `&v` | 둘 다 통과, `v = [1, 2, 3]` 남음 | 4 |
| 라벨 4종(`break`/`break 'outer`/`continue 'row`/`break 'search a`) | `[(0,0),(1,0),(2,0)]` · `[(0,0),(0,1),(0,2),(1,0)]` · 같은 값 · **23** | 5 |
| 안쪽 `for` 뒤 문장을 둔 `break` ↔ `continue 'row` | `[0, 1, 2]` ↔ `[]` — **둘이 갈린다** | 5 |
| 라벨이 `for` 에 붙은 `break 'outer a` | **E0571** — 목표 루프가 `for` 라서 | 5 |
| `break;` / `'a:` 미사용 / `break 'nope` | **E0268** · **E0426** · **`unused_labels` 경고** | 6 |
| `rustc --explain E0268` | 루프 밖 `break`/`continue` 공식 설명 | 6 |
| `fn forever() -> i32 { loop {} }` · `String` 자리의 `loop {}` | **컴파일 성공** — `a = 1 / b = s / c = ()` | 7 |
| `'blk: { ... break 'blk Some(*x) ... }` | `Some(4)` | 8 |
| 라벨 블록 + 이터레이터 `find().copied()` | `Some(4)` / `Some(4)` / 같은가? `true` | 8 |
| `continue 'blk;` (라벨 블록) | **E0696** `labeled blocks cannot be continue'd` | 8 |
| `continue 5;` | **번호 없는 파서 에러** + `unreachable_code` 경고 | 9 |
| `a.into_iter()` 를 2018·2021 에서 실행 | **양쪽 `sum = 60`** · 2018 에만 `array_into_iter` 경고 | 10 |
| `a.into_iter()` 를 2018·2021 에서 타입 탐침 | `&{integer}` ↔ `integer` | 10 |
| `for x in &v { v.push(99); }` | **E0502** | 11 |
| `releases.md` 의 1.41.0·1.53.0·1.65.0 절 | `unused_labels` · 배열 `IntoIterator` · 라벨 있는 블록 | 6·8·10 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **`a.into_iter()` 가 `&T` 를 주나 `T` 를 주나** | **에디션.** 2015·2018 ↔ 2021 이후. **이 주제에서 답이 갈리는 유일한 축이다** |
| 에러·경고 **문구와 화살표 배치** | rustc 구현. `for` 에만 붙는 `note` 가 대표다. **에러 번호**가 더 안정적이다 |
| `unused_labels` 가 **경고**인 것 | 린트 설정. `-D warnings`·`#[deny]` 로 에러가 된다 |
| `array_into_iter` 가 **경고**인 것 | 린트 설정(`rust_2021_compatibility` 묶음) |
| `{integer}` 라는 타입 표기 | rustc의 추론 변수 표시. 확정 뒤에는 `i32` 로 보인다 |
| 라벨 있는 블록·`unused_labels`·배열 `IntoIterator` 의 **도입 버전** | **rustc 버전.** 1.65.0 · 1.41.0 · 1.53.0 — `releases.md` 가 정본 |
| **`loop`/`while`/`for` 의 타입 규칙과 `break 값` 규칙** | **전부 언어 보장.** 빌드 프로필(디버그/릴리스)·플랫폼에 흔들리지 않는다 |
