# rust/syntax/05 — 제어 흐름: `loop`·`while`·`for`·라벨 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Loop expressions
> (`loop`/`while`/`for`/Labelled block expressions/`break`/`continue`) 절 ·
> [std 문서](https://doc.rust-lang.org/std/)의 `primitive.array`(Editions 절) ·
> `rustc --explain E0571` / `E0268` / `E0382` / `E0308`.
> 이 머신의 `rust-docs`(1.92.0)를 열어 확인했고, 인용은 그 판의 원문이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **에디션이 답을 바꾸는 실험 한 건**(`a.into_iter()`)은 **2018 과 2021 을 둘 다** 돌렸다.
> **버전** — `loop`/`while`/`for`/라벨은 1.0부터. 아래 셋은 이 머신의 `rust-docs` 안\
> `html/releases.md`(공식 릴리스 노트)에서 **해당 절을 찾아 확인한 것**이다.\
> **라벨 있는 블록**(`'blk: { ... }`)은 **1.65.0 (2022-11-03)** — 「Stabilize `break`ing from arbitrary labeled blocks」.\
> **배열의 `IntoIterator`** 는 **1.53.0 (2021-06-17)** — 「Arrays of any length now implement `IntoIterator`」.\
> 단 **2015·2018 에디션에는 적용되지 않는다**(std 문서 `primitive.array` Editions 절).\
> **`unused_labels` 경고**는 **1.41.0 (2020-01-30)** — 「Rustc will now warn if you have unused loop `'label`s」.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**세 반복문은 「누가 멈추라고 말하나」가 다르고, 그중 하나만 결과물을 들고 나온다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 「내가 됐다고 할 때까지」 — 멈추는 사람이 나다 | `loop` |
| 「비가 오는 동안」 — 바깥 조건이 멈춘다 | `while` |
| 「받은 명단이 끝날 때까지」 — 명단이 멈춘다 | `for` |
| 일을 끝내고 **결과물을 손에 들고 나오는 것** | `break 값` — **`loop` 에서만** 된다 |
| 명단을 **통째로 받아 가는 것**(원본이 사라진다) | `for x in v` |
| 명단을 **어깨너머로 읽는 것** | `for x in &v` |
| 명단에 **연필로 고쳐 쓰는 것** | `for x in &mut v` |
| 여러 겹 상자에서 **바깥까지 한 번에 나가는 비상구** | 라벨 — `'outer: ... break 'outer` |

- `loop` 는 출구를 내가 만든다. 그래서 **나올 때 값을 들고 나올 수 있다**(`break i`).
- `while`·`for` 는 멈추는 조건이 밖에 있다. 그래서 **늘 빈손**이다 — 타입이 `()` 다.
- ★ 이 한 줄이 이 주제의 절반이다: **값을 내는 반복은 `loop` 뿐이다.**

```text
           loop                 while                  for
             |                    |                     |
     "내가 멈출 때까지"     "조건이 참인 동안"    "명단이 끝날 때까지"
             |                    |                     |
      break 값  가능          break 만            break 만
             |                    |                     |
             v                    v                     v
       타입 = break 값의 타입    타입 = ()             타입 = ()
       break 가 없으면 !
```

**언어도 똑같은 구조다.** 컴파일러에게 셋의 타입을 물어본 실측이 그림 그대로다.

```text
===== 소스: ex.rs =====
fn main() {
    let mut i = 0;
    let a: i32 = while i < 3 { i += 1; };
    let b: i32 = for _ in 0..3 { };
    println!("{a} {b}");
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

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
```

★ **두 메시지가 대칭이 아니다.** `for` 쪽에만 「**`for` loops evaluate to unit type `()`**」라는 `note` 가 붙는다.
`while` 쪽은 같은 사실인데 그 줄이 없다 — **메시지 모양은 규칙이 아니라 rustc 구현**이라는 증거다.

> **식(expression)** — 값으로 평가되는 것. 셋 다 식이다.\
> 예: `while`·`for` 도 식이지만 그 값이 늘 `()` 라서 값으로 못 쓴다([**04번 주제**](../04-expressions-and-semicolons/)가 정본).

> **유닛 타입 `()`** — 값이 하나뿐인 타입. 크기 0바이트. 「의미 있는 값이 없다」를 나타낸다.\
> 예: `for` 루프 전체의 값이 `()` 다. 그래서 `let b: i32 = for ...` 가 거부된다.

> **발산 타입 `!`** — 값을 절대 내지 않는 것의 타입.\
> 예: `break` 가 하나도 없는 `loop {}` 가 그렇다. 정본은 [**06번 주제**](../06-functions-and-never-type/).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **세 반복문은 무엇이 다른가** — 특히 **어느 것이 값을 낼 수 있는가**, 그리고 안 되는 쪽은 어떤 에러로 거부되는가.
2. **`for` 는 내 컬렉션을 어떻게 받아 가는가** — `v`·`&v`·`&mut v` 가 각각 무엇을 주고, 순회 뒤에 원본이 남는가.
3. **라벨은 정확히 무엇을 가리키는가** — 값을 낼 수 있는 `break` 와 없는 `break` 는 어디서 갈리는가.

## 동작 방식

### (1) 셋을 나란히 돌려 본다 — 무엇이 멈추나

**언제 쓰나** — 반복을 쓸 때마다. 고르는 기준은 **「멈추는 조건이 어디 있나」** 하나다.

```text
   loop { ... break 값; }        while 조건 { ... }        for 이름 in 이터러블 { ... }
        |                              |                            |
   몸통 안에서 내가 멈춘다        매 바퀴 앞에서 조건을 본다     명단에서 하나씩 꺼낸다
        |                              |                            |
   멈출 때 값을 낼 수 있다         멈추면 그냥 끝               다 꺼내면 끝
```

```text
===== 소스: ex.rs =====
fn main() {
    // loop: break 로 값을 낸다
    let mut i = 0;
    let found = loop {
        i += 1;
        if i * i > 50 { break i; }
    };
    println!("found = {found}");

    // while: 조건이 거짓이 될 때까지
    let mut n = 3;
    while n > 0 {
        print!("{n} ");
        n -= 1;
    }
    println!();

    // for: 이터레이터를 끝까지
    for k in 0..4 { print!("{k} "); }
    println!();

    let v = vec![10, 20, 30];
    for x in &v { print!("{x} "); }
    println!();
    println!("v 는 그대로 = {:?}", v);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
found = 8
3 2 1 
0 1 2 3 
10 20 30 
v 는 그대로 = [10, 20, 30]
(종료 코드 0)
```

그림 해설 (한 단계씩):

- `loop` 는 **조건 자리가 없다.** 몸통 안의 `break` 가 유일한 출구다.
- `found = 8` — `i * i > 50` 이 처음 참이 되는 `i` 가 8이다(64 > 50, 49는 아니다).
- `while` 은 **매 바퀴 시작 전에** 조건을 본다. 값은 안 낸다.
- `for` 는 범위(`0..4`)든 컬렉션(`&v`)이든 **이터레이터로 바꿔** 하나씩 꺼낸다.

비용 — 셋 다 런타임 비용이 같다. 고르는 기준은 성능이 아니라 **멈추는 조건이 어디 있나**다.

### (2) ★ 값을 내는 반복은 `loop` 뿐이다

**언제 쓰나** — 「찾을 때까지 돌다가 찾은 것을 돌려받고 싶을 때」.

`while`·`for` 안에서 `break` 에 값을 붙이면 **전용 에러 번호**가 나온다.

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

`rustc --explain E0571` 이 규칙을 한 문단으로 말한다.

> The `break` statement can take an argument (which will be the value of the loop
> expression if the `break` statement is executed) in `loop` loops, but not
> `for`, `while`, or `while let` loops.

반대로 `loop` 에서 **값 없는 `break`** 를 쓰면 그 `loop` 의 값은 `()` 다.

```text
===== 소스: ex.rs =====
fn main() {
    let c: i32 = loop { break; };
    println!("{c}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0308]: mismatched types
 --> ex.rs:2:25
  |
2 |     let c: i32 = loop { break; };
  |         -        ----   ^^^^^ expected `i32`, found `()`
  |         |        |
  |         |        this loop is expected to be of type `i32`
  |         expected because of this assignment
  |
help: give the `break` a value of the expected type
  |
2 |     let c: i32 = loop { break 42; };
  |                               ++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

```text
   loop { break 7; }      loop { break; }       while ... { break 7; }
          |                      |                        |
       값 7 을 낸다           값이 () 다              아예 문법 위반
          |                      |                        |
          v                      v                        v
      타입 = i32              타입 = ()                  E0571
```

그림 해설 (한 단계씩):

- **E0571 은 타입 에러가 아니다.** 「이 종류의 루프에서는 값을 못 낸다」는 **문법 층의 거부**다.
- `loop` 에서 값 없는 `break` 는 타입이 `()` 라 **E0308** — 다른 층의 에러다. 두 에러를 섞지 마라.
- `help:` 가 양쪽 다 고칠 글자를 짚는다 — `break;` 로 줄이거나 `break 42;` 로 늘리거나.

비용 — 없음. 전부 컴파일 타임 판정이다.

### (3) ★ `for` 가 원본을 어떻게 받아 가나 — 세 형태

**언제 쓰나** — 컬렉션을 도는 모든 자리. **이 절이 [**08번 주제**](../08-ownership-and-move/)와 직결된다.**

먼저 셋이 **무엇을 주는지** 컴파일러에게 물어본다(일부러 틀린 타입을 준다).

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

세 형태를 제대로 쓰면 이렇게 된다.

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

```text
   for x in &v          for x in &mut v         for x in v
        |                     |                      |
    x: &i32               x: &mut i32              x: i32
    읽기만                 *x 로 고친다           값을 가져간다
        |                     |                      |
        v                     v                      v
   v 는 그대로            v 가 바뀌어 남는다        v 가 사라진다
   [10,20,30]             [11,21,31]           (다음 줄에서 에러)
```

그림 해설 (한 단계씩):

- `&v` 는 **참조**를 준다 — `&i32`. 원본은 손대지 않고 끝난다.
- `&mut v` 는 **가변 참조**를 준다 — `*x += 1` 로 원본을 고친다. 순회 뒤 `v` 는 바뀐 채 남는다.
- `v` 를 그대로 쓰면 **값 자체**를 준다 — `i32`. 그리고 **`v` 를 가져간다.**

`v` 를 그대로 쓴 뒤 `v` 를 다시 만지면 거부된다.

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

`rustc --explain E0382` 의 첫 줄과 핵심 문장:

> A variable was used after its contents have been moved elsewhere.
> (…) This is fundamental to Rust's ownership system: outside
> of workarounds like `Rc`, a value cannot be owned by more than one variable.

- 메시지가 **보이지 않는 호출을 이름으로 불러 준다** — 「`v` moved due to this **implicit call to `.into_iter()`**」.
- `for` 가 `IntoIterator` 규약으로 돈다는 사실이 **에러 메시지로 드러난다.**\
  규약 전수(어느 타입이 무엇을 주나)는 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)가 정본이고, 여기서는 **현상까지**다.
- `help:` 가 고칠 글자 하나를 짚는다 — `&` 를 붙이라는 것.

비용 — `&v`/`&mut v` 는 포인터 하나. `v` 는 소유권 이동이라 **깊은 복사가 아니다**([**08번 주제**](../08-ownership-and-move/)).

### (4) ★ 배열은 안 사라진다 — `Vec` 과 갈리는 자리

**언제 쓰나** — 위 규칙을 배열에 그대로 적용하려 할 때. **여기서 직관이 깨진다.**

```text
===== 소스: ex.rs =====
fn main() {
    // 배열은 Copy 다 — for 가 "먹어도" 원본이 남는다
    let a = [10, 20, 30];
    for x in a { print!("{x} "); }
    println!("| a = {:?}", a);

    // Vec 은 Copy 가 아니다 — 위와 같은 코드가 거부된다 (앞 절 참고)

    // 범위도 이터레이터다
    let r = 0..3;
    for x in r { print!("{x} "); }
    println!();

    // v.iter() 는 &v 와 같은 것을 준다
    let v = vec![1, 2, 3];
    for x in v.iter() { let _ = x; }
    for x in &v { let _ = x; }
    println!("v = {:?}", v);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
10 20 30 | a = [10, 20, 30]
0 1 2 
v = [1, 2, 3]
(종료 코드 0)
```

```text
   for x in v   (v: Vec<i32>)          for x in a   (a: [i32; 3])
          |                                     |
    Vec 은 Copy 가 아니다                 [i32; 3] 은 Copy 다
          |                                     |
    소유권이 for 로 넘어간다              한 벌이 복사돼 넘어간다
          |                                     |
          v                                     v
     다음 줄에서 E0382                    a 는 그대로 살아 있다
```

그림 해설 (한 단계씩):

- **`for x in <값>` 은 늘 그 값을 가져간다.** 규칙은 하나다.
- 다만 **가져간 것이 원본인지 사본인지**가 타입에 달렸다 — `Copy` 면 사본이라 원본이 남는다.
- 그래서 **같은 모양의 코드가 배열에서는 통과하고 `Vec` 에서는 거부된다.**\
  「`for` 가 원본을 먹는다」로만 외우면 이 자리에서 어긋난다.
- `Copy` 판정의 정본은 [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`와 `Clone`)다.

비용 — 배열은 **원소 수만큼 복사**된다(`[i32; 3]` 이면 12바이트). `Vec` 은 이동이라 복사가 없다.

### (5) 라벨 — 「어느 루프를 가리키나」가 전부다

**언제 쓰나** — 중첩 루프에서 **안쪽이 아니라 바깥을** 끝내고 싶을 때.

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

```text
   'outer: for a { for b { break; } }        'outer: for a { for b { break 'outer; } }
                        |                                            |
              안쪽 for 만 끝난다                           바깥 for 까지 끝난다
                        |                                            |
                        v                                            v
        [(0,0), (1,0), (2,0)]  — a 는 계속 돈다        [(0,0),(0,1),(0,2),(1,0)]  — 거기서 전부 끝
```

그림 해설 (한 단계씩):

- 라벨 없는 `break` 는 **가장 안쪽 루프**만 끝낸다. `a` 는 0·1·2 를 다 돈다.
- `break 'outer` 는 **라벨이 붙은 루프**를 끝낸다. `(1,1)` 에 닿는 순간 전부 끝난다.
- `continue 'row` 는 **그 라벨 루프의 다음 바퀴**로 간다. 결과가 1번과 **글자까지 같지만 같은 동작이 아니다** —\
  이 예제는 안쪽 `for` 뒤에 문장이 없어서 우연히 같아졌다. **문장을 하나 넣어 던져서 갈랐다.**

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

  ★ **같은 출력을 근거로 「같다」고 적을 뻔한 자리다.** 둘을 가르는 것은 **바깥 몸통의 나머지**를 지나느냐다.
- ★ 4번이 이 절의 핵심이다 — **`break 'search a` 가 `for` 문 안에 있는데도 값을 냈다.**\
  가리키는 라벨이 `loop` 에 붙어 있기 때문이다. 23이 나온 것은 23² = 529 > 500 이라서다.

비용 — 없음. 라벨은 **컴파일 타임 이름표**이고 기계어에 남지 않는다.

### (6) ★ `break` 없는 `loop` 의 타입은 `!`

**언제 쓰나** — 서버 루프·이벤트 루프처럼 **끝나지 않는** 함수를 쓸 때.

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

```text
   loop { }                     loop { break; }
      |                                |
  나올 길이 없다                    나올 길이 있다
      |                                |
      v                                v
   타입 = !                        타입 = ()
      |                                |
  어떤 타입 자리에도 들어간다        () 자리에만 들어간다
  i32 도 String 도 통과            i32 자리에 두면 E0308
```

그림 해설 (한 단계씩):

- `loop {}` 는 **값을 낼 길이 없다.** 그 사실 자체가 타입이 되는 것이 `!` 다.
- `!` 는 **어떤 타입으로도 강제**되므로 `i32` 갈래에도 `String` 갈래에도 들어간다(실측 — 둘 다 통과).
- `break;` 가 하나라도 있으면 타입은 `()` 가 된다 — 그때부터는 `i32` 자리에 못 들어간다((2)번의 E0308).
- **`!` 의 정본은 [**06번 주제**](../06-functions-and-never-type/)**(함수·반환·발산 타입)다. 여기서는 **이 자리까지**만.

비용 — 없음. 컴파일 타임 타입이다.

## 문법 — 형태와 규칙

### 형태

```rust
loop { ... }                       // 무한. break 로만 나온다
loop { ... break 값; }             // 값을 내는 유일한 반복
while 조건 { ... }                 // 매 바퀴 앞에서 조건 검사
for 패턴 in 이터러블 { ... }        // IntoIterator 를 부른다

'라벨: loop { ... }                // 라벨은 작은따옴표 + 콜론
'라벨: while 조건 { ... }
'라벨: for 패턴 in 이터러블 { ... }
'라벨: { ... break '라벨 값; }      // 라벨 있는 블록 (1.65.0부터)

break;            break 값;        break '라벨;      break '라벨 값;
continue;                          continue '라벨;
```

### 어디에 무엇이 되나

| | 타입 | `break` | `break 값` | `continue` | 라벨 |
|---|---|---|---|---|---|
| `loop` | `break` 값의 타입 / 없으면 `!` | 된다 | **된다** | 된다 | 된다 |
| `while` | 항상 `()` | 된다 | **안 된다**(E0571) | 된다 | 된다 |
| `for` | 항상 `()` | 된다 | **안 된다**(E0571) | 된다 | 된다 |
| 라벨 있는 블록 | `break` 값의 타입 | — | **된다** | **안 된다**(E0696) | 필수 |

- ★ **`break 값` 이 되는지는 「`break` 가 어디 쓰였나」가 아니라 「어느 루프를 가리키나」로 갈린다.**\
  `for` 안의 `break 'search a` 가 통과한 것((5)번 4)과 라벨이 `for` 에 붙어 거부된 것(아래)이 그 짝이다.
- `while let` 은 이 표에서 `while` 과 같은 칸이다. 정본은 [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)이고 여기서는 **이름까지**만 댄다.

### 금지 사례 — 라벨이 `for` 에 붙어 있으면 값을 못 낸다

```text
===== 소스: ex.rs =====
fn main() {
    // 라벨이 for 에 붙어 있으면 값을 못 낸다
    let x = 'outer: for a in 0..3 {
        for b in 0..3 {
            if b == 1 { break 'outer a; }
        }
    };
    println!("{x:?}");
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0571]: `break` with value from a `for` loop
 --> ex.rs:5:25
  |
3 |     let x = 'outer: for a in 0..3 {
  |             --------------------- you can't `break` with a value in a `for` loop
4 |         for b in 0..3 {
5 |             if b == 1 { break 'outer a; }
  |                         ^^^^^^^^^^^^^^ can only break with a value inside `loop` or breakable block
  |
help: use `break` on its own without a value inside this `for` loop
  |
5 -             if b == 1 { break 'outer a; }
5 +             if b == 1 { break 'outer; }
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0571`.
```

- **`break` 는 `for` 안에 있고, 라벨도 `for` 에 붙어 있다** → 거부.
- 앞 절의 통과한 코드는 **`break` 는 `for` 안에 있지만 라벨이 `loop` 에 붙어 있었다** → 통과.
- 두 출력을 나란히 놓으면 판정 기준이 **목표 루프의 종류**라는 것이 남는다.

### 금지 사례 — 루프 밖의 `break`·없는 라벨

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

`rustc --explain E0268`:

> A loop keyword (`break` or `continue`) was used outside of a loop.
> (…) Without a loop to break out of or continue in, no sensible action can be taken.
> Please verify that you are using `break` and `continue` only in loops.

- ★ **라벨을 붙여 놓고 안 쓰면 `unused_labels` 경고가 난다.** 에러가 아니라 경고라서 **안 읽으면 모른다.**
- 리팩터링으로 `break 'outer` 를 지우고 라벨만 남기는 사고가 이 경고에 걸린다.

### 금지 사례 — `continue` 에는 값을 못 붙인다

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

- **에러 번호가 없다** — 파서가 거부하는 **문법 층**의 에러다(E0571 보다 더 앞단).
- `continue` 뒤에 올 수 있는 것은 **라벨뿐**이다. 「다음 바퀴에 값을 넘긴다」는 개념 자체가 없다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. **일곱 중 둘은 에러가 아니라 경고로만 드러난다.**

### 1. ★ `while`·`for` 에서 값을 꺼내려 한다

```text
let x: i32 = while i < 3 { i += 1; };   ->  E0308 expected `i32`, found `()`
let a = while i < 3 { break 7; };       ->  E0571 `break` with value from a `while` loop
```

- **두 에러가 다른 층이다.** 앞엣것은 타입, 뒤엣것은 문법이다.
- 값을 내는 반복은 **`loop` + `break 값`** 뿐이다. 값을 **모으고** 싶으면 이터레이터로 간다([목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)).

### 2. ★ `for x in v` 로 원본을 잃는다

```text
for x in v { ... }
println!("{:?}", v);     ->  E0382 borrow of moved value: `v`
                             `v` moved due to this implicit call to `.into_iter()`
```

- 고치는 법은 **`&` 하나**다 — `help:` 가 그것을 정확히 짚는다.
- 「읽기만 할 건데 왜 사라지지?」가 아니라 「`for` 에 값을 줬으니 **가져간 것**」으로 읽는다.

### 3. ★ 배열에서는 같은 코드가 통과한다 — 더 헷갈린다

```text
let a = [10, 20, 30];
for x in a { ... }
println!("{:?}", a);     ->  통과. a = [10, 20, 30]
```

- **에러가 안 나서 더 나쁘다.** 「`for` 는 원본을 안 먹는구나」로 잘못 배운다.
- 그 상태로 `Vec` 을 쓰면 2번에서 막히고, **왜 막히는지 모르게 된다.**
- 갈림의 근거는 `for` 가 아니라 **그 타입이 `Copy` 인가**다.

### 4. 라벨을 `for` 에 붙여 놓고 값을 내려 한다

```text
let x = 'outer: for a in 0..3 { ... break 'outer a; };
  ->  E0571 you can't `break` with a value in a `for` loop
```

- 「라벨을 붙였으니 값이 나오겠지」가 아니다. **라벨이 붙은 루프가 `loop` 여야** 한다.
- 고치는 법 둘 — 바깥을 `loop` 로 바꾸거나, **라벨 있는 블록**(`'blk: { ... }`)으로 감싼다.

### 5. 라벨을 지우다 이름표만 남긴다 — **경고만 난다**

```text
'a: for _ in 0..1 {}

warning: unused label
  = note: `#[warn(unused_labels)]` (part of `#[warn(unused)]`) on by default
```

- 컴파일은 통과한다. **경고를 안 읽으면 죽은 이름표가 남는다.**
- `-D warnings` 로 올리면 에러가 된다.

### 6. 순회 중에 원본을 바꾼다

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
```

- 다른 언어의 `ConcurrentModificationException` 자리를 **컴파일 타임에** 막는다.
- 규칙과 해결법의 정본은 [목록의 **10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림)와 **11번 주제**(빌림 검사기 전형)다. 여기서는 **현상까지**.

### 7. ★ 에디션을 안 고정하고 `a.into_iter()` 를 쓴다 — **2018 에서는 경고만 난다**

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

- ★★ **출력이 같다.** `sum = 60` 이 양쪽에서 한 글자도 다르지 않다 — **결과만 보면 아무 문제가 없어 보인다.**
- 갈린 것은 **`x` 의 타입**이다. 같은 파일을 타입 탐침으로 다시 던지면 드러난다.

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

- 2018 에서는 `x: &{integer}`, 2021 에서는 `x: integer` 다. **원소가 `Copy` 라서 합이 우연히 같았을 뿐이다.**
- 원소가 `String` 이면 이 차이가 **컴파일 여부**를 바꾼다.
- ★ **그래서 이 묶음의 모든 실험은 `--edition 2021` 로 고정한다.** `rustc ex.rs` 는 **2015 에디션**을 쓴다.

## 구현 세부사항 대 언어 보장

이 갈래에서 갈리는 축은 **디버그/릴리스가 아니라 에디션과 린트 설정**이다.
[**03번 주제**](../03-primitive-types-and-integer-overflow/)처럼 빌드 프로필에 따라 답이 갈리는 자리는 이 주제에 **없다** —
반복문의 타입 규칙은 전부 컴파일 타임에 끝난다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `loop` 만 `break 값` 으로 값을 낸다 | **언어** | E0571 · `--explain E0571` 이 명시 |
| `while`·`for` 의 타입이 항상 `()` | **언어** | E0308 · `note: for loops evaluate to unit type ()` |
| `break` 없는 `loop` 의 타입이 `!` | **언어** | `fn forever() -> i32 { loop {} }` 가 컴파일됨 |
| `break 값` 가부가 **목표 루프의 종류**로 갈린다 | **언어** | 통과 사례와 E0571 사례를 나란히 실측 |
| `for` 가 `IntoIterator` 를 부른다 | **언어** | E0382 의 `implicit call to .into_iter()` |
| `for x in v` 가 `v` 를 가져간다 | **언어** | E0382 |
| 배열에서 원본이 남는 것 | **언어** | `[T; N]` 이 `Copy` 라서. 정본은 [목록의 **09번 주제**](../09-copy-clone-and-drop/) |
| **`a.into_iter()` 가 무엇을 주나** | **에디션** | 2018 = `&T` / 2021 = `T`. 배열의 `IntoIterator` 는 **1.53.0 (2021-06-17)**, 2015·2018 은 제외(std 문서) |
| 라벨 있는 블록(`'blk: { }`) | **버전** | **1.65.0 (2022-11-03)** — `releases.md` 에서 확인 |
| **`unused_labels` 가 경고인 것** | **린트 설정** | **1.41.0**부터 있는 린트. `-D warnings`·`#[deny]` 로 에러가 된다 |
| **`array_into_iter` 가 경고인 것** | **린트 설정** | `rust_2021_compatibility` 묶음 |
| **에러·경고 메시지의 문구와 화살표 배치** | **rustc 구현** | `while` 에는 없는 `note` 가 `for` 에만 붙는다. **에러 번호**가 더 안정적이다 |

std 문서(`primitive.array`, Editions 절)의 원문:

> Prior to Rust 1.53, arrays did not implement `IntoIterator` by value, so the method call
> `array.into_iter()` auto-referenced into a slice iterator. Right now, the old behavior is
> preserved in the 2015 and 2018 editions of Rust for compatibility, ignoring `IntoIterator` by value.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 찾을 때까지 돌다가 **찾은 것을 받는다** | `loop` + `break 값` | 값을 내는 유일한 반복이다 |
| 끝나지 않는 서버·이벤트 루프 | `loop {}` | 타입이 `!` 라 어떤 반환 타입에도 맞는다 |
| 조건이 거짓이 될 때까지 | `while` | 조건이 몸통 밖에 있을 때 읽기 쉽다 |
| 컬렉션·범위를 끝까지 | `for` | 인덱스 계산이 사라져 off-by-one 이 없다 |
| 순회하되 **원본을 계속 쓴다** | `for x in &v` | 이것이 기본값이다 |
| 순회하며 **원소를 고친다** | `for x in &mut v` + `*x` | 원본이 바뀐 채 남는다 |
| 순회하며 **원소를 가져간다** | `for x in v` | 뒤에서 `v` 를 안 쓸 때만 |
| 중첩 루프의 **바깥**을 끝낸다 | 라벨 + `break 'outer` | 플래그 변수를 안 만들어도 된다 |
| 조건 만족 시 **블록 하나를 일찍 끝낸다** | `'blk: { ... break 'blk 값 }` | 1.65.0부터. 함수로 쪼개지 않아도 된다 |
| 순회 결과를 **모은다** | 이터레이터 `map`/`filter`/`collect` | [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/) |

판단 규칙 두 줄.

- **반복문을 고를 때 먼저 묻는다: 「멈추는 조건이 몸통 안에 있나 밖에 있나.」** 안이면 `loop`, 밖이면 `while`/`for` 다.
- **`for` 에 무엇을 줄지는 「순회 뒤에 원본을 쓸 것인가」로 정한다.** 쓸 거면 `&`, 고칠 거면 `&mut`, 안 쓸 거면 그냥 값.

## 핵심 문장

- 세 반복문 중 **값을 내는 것은 `loop` 뿐**이다. `while`·`for` 는 타입이 늘 `()` 다.
- `break` 에 값을 붙일 수 있는지는 **`break` 의 위치가 아니라 목표 루프의 종류**로 갈린다 — **E0571**.
- **`break` 가 하나도 없는 `loop` 의 타입은 `!`** 라 어떤 타입 자리에도 들어간다(정본은 [**06번 주제**](../06-functions-and-never-type/)).
- `for x in v` 는 **`v.into_iter()` 를 부르며 `v` 를 가져간다** — 그 사실이 **E0382** 메시지에 적혀 있다.
- `&v` 는 `&T` 를, `&mut v` 는 `&mut T` 를, `v` 는 `T` 를 준다. **순회 뒤 원본이 남는지가 여기서 갈린다**([**08번 주제**](../08-ownership-and-move/)).
- **배열은 `Copy` 라 `for x in a` 뒤에도 원본이 산다** — 「`for` 가 먹는다」로만 외우면 이 자리에서 틀린다.
- 라벨은 컴파일 타임 이름표다. **안 쓰면 `unused_labels` 경고**가 나고, 루프 밖의 `break` 는 **E0268**이다.
- **`a.into_iter()` 는 에디션에 따라 다른 것을 준다**(2018 = `&T`, 2021 = `T`). 출력이 같아도 타입이 다르다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 05번)
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — **직접 선행.** 「블록이 값이다」·`()`·꼬리 표현식이 거기 정본이다
- [**06번 주제**](../06-functions-and-never-type/)(함수·반환·발산 타입 `!`) — `!` 의 정본. 여기서는 `loop {}` 의 타입까지만 닿았다
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — `for x in v` 가 **왜** 원본을 가져가는지는 거기가 정본이다
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입) — 디버그/릴리스가 갈리는 갈래의 대비
- [**01번 주제**](../01-cargo-crates-and-modules/)(`cargo`·크레이트) — 이 문서의 예제를 돌리는 방법
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — 그쪽은 「**왜 이 언어인가**」(소유권 모델의 논증·청구서)이고,\
  여기는 「**이 문법이 실제로 무엇을 하나**」다. 이 문서는 모델을 논증하지 않고 **에러 메시지만** 읽는다
- [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`와 `Clone`) — 배열이 왜 남고 `Vec` 이 왜 사라지는지의 판정 기준
- [목록의 **10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림) · **11번 주제**(빌림 검사기 전형) — 순회 중 변경(E0502)의 정본
- [목록의 **20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)(`if let`·`while let`) — `while let` 의 정본. 여기서는 **이름만** 댔다
- [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)(`Iterator`) — 반복 결과를 **모으는** 관용
- [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)(`IntoIterator` 세 형태) — `iter`/`iter_mut`/`into_iter` 규약의 정본

## 용어 풀이

- **`loop`** — 조건 없는 반복. `break` 로만 나오고, **값을 낼 수 있는 유일한 반복문**이다.
- **`while`** — 매 바퀴 앞에서 조건을 보는 반복. 전체 타입은 늘 `()` 다.
- **`for`** — 이터러블을 끝까지 도는 반복. 내부적으로 `IntoIterator::into_iter` 를 부른다.
- **`break 값`** — 루프를 끝내며 그 루프 전체의 값을 정하는 것. `loop` 와 라벨 있는 블록에서만 된다.
- **라벨(label)** — 루프·블록에 붙이는 이름표. `'outer:` 처럼 작은따옴표로 시작한다. 컴파일 타임에만 존재한다.
- **라벨 있는 블록(labelled block)** — `'blk: { ... }`. 루프가 아니면서 `break '라벨 값` 으로 나올 수 있는 블록. **1.65.0**부터. `continue` 는 못 쓴다(E0696).
- **`IntoIterator`** — 「이터레이터로 바뀔 수 있다」는 트레이트. `for` 가 자동으로 부른다.
- **이동(move)** — 값의 소유권이 넘어가 원래 이름을 못 쓰게 되는 것. `for x in v` 가 그렇다.
- **`Copy`** — 대입·전달 때 이동 대신 **복사**되는 성질. 배열과 `Vec` 이 갈리는 이유다.
- **유닛 타입 `()`** — 값이 하나뿐인 타입. `while`·`for` 의 타입이다.
- **발산 타입 `!`** — 값을 절대 내지 않는 것의 타입. `break` 없는 `loop` 가 그렇다.
- **`unused_labels`** — 선언만 하고 쓰지 않은 라벨에 붙는 기본 경고.
- **`array_into_iter`** — 2015·2018 에디션에서 `배열.into_iter()` 의 뜻이 2021 과 달라진다고 알리는 기본 경고.

---

## 더 들어가면

- **라벨 있는 블록**(1.65.0부터)은 루프가 아닌데도 값을 내고 나올 수 있다. E0571 메시지의\
  「can only break with a value inside `loop` **or breakable block**」이 이것을 가리킨다(실측).

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

- 「찾으면 그 값, 못 찾으면 기본값」을 **함수로 쪼개지 않고** 쓰는 관용이다.\
  같은 일을 이터레이터로도 쓸 수 있다 — **두 결과가 같은지 던져서 확인했다**(정본은 [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)).

```text
===== 소스: ex.rs =====
fn main() {
    let v = vec![3, 9, 4];
    let a = 'blk: {
        for x in &v {
            if x % 2 == 0 { break 'blk Some(*x); }
        }
        None
    };
    let b = v.iter().find(|x| *x % 2 == 0).copied();
    println!("라벨 블록 = {a:?} / 이터레이터 = {b:?} / 같은가? {}", a == b);
}
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
라벨 블록 = Some(4) / 이터레이터 = Some(4) / 같은가? true
(종료 코드 0)
```

- ★ **라벨 있는 블록에는 `continue` 를 못 쓴다** — 루프가 아니라 돌아갈 「다음 바퀴」가 없기 때문이다.\
  전용 에러 번호가 따로 있다(실측).

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

- `continue` 에 **값**을 붙이는 문법은 **없다.** 파서가 먼저 막는다(에러 번호도 없다).
- `v.iter()` 와 `&v` 는 같은 것을 준다(실측 — 둘 다 컴파일되고 `v` 가 그대로 남는다).\
  둘 중 무엇을 쓸지는 취향이지만, **`for` 에서는 `&v` 가 짧고 체인에서는 `.iter()` 가 이어 쓰기 좋다.**
- `for` 의 왼쪽은 이름이 아니라 **패턴**이다 — `for (i, x) in v.iter().enumerate()` 가 그래서 된다.\
  패턴 문법의 정본은 [목록의 **19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)다.
