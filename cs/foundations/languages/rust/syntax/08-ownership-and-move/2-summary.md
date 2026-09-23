# rust/syntax/08 — 소유권과 이동(move) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Destructors · Ownership and moves 관련 절 ·
> [The Rust Book ch.4.1](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html) ·
> `rustc --explain E0382` / `E0509` / `E0507` / `E0204`. 이 머신의 `rust-docs`(1.92.0)를 열어 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> 주소를 찍는 프로그램은 **디버그와 릴리스를 둘 다** 돌렸다(`rustc --edition 2021 -O ex.rs`).
> **버전** — 여기 나오는 문법은 전부 1.0부터다. `Copy`·`Drop`·`mem::drop` 은 이 머신의 std 문서에서\
> 「Stable since Rust version **1.0.0**」을 직접 확인했다. `let_underscore_lock` 린트만 **1.65.0**부터다\
> (이 툴체인의 `releases.md` 에서 1.65.0 항목을 직접 확인했다 — 아래 「더 들어가면」·정답 4번).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**값 하나에 주인은 한 명이고, 주인이 방을 나갈 때 값도 같이 사라진다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 물건 | **힙에 있는 값**(`String` 의 글자, `Vec` 의 원소) |
| 물건에 붙은 **꼬리표** | 스택에 있는 **바인딩**(`s1` 이라는 이름) |
| 주인 | **소유자**(owner) — 그 꼬리표를 든 이름 하나 |
| 꼬리표를 남에게 넘김 | **이동**(move) — 대입·인자 전달·반환 |
| 넘기고 난 뒤 내 손 | **무효**가 된 이름. 쓰면 컴파일러가 거부한다 |
| 주인이 방을 나감 | 스코프 끝 — 그 자리에서 **해제**(drop) |
| 물건을 하나 더 만들어 가짐 | **`clone()`** — 힙을 새로 할당한다 |
| 복사해도 원본이 안 상하는 가벼운 물건 | **`Copy`** 타입(`i32`·`bool`·`char`·`&T` …) |

- `let s2 = s1;` 은 **복사가 아니라 꼬리표를 넘긴 것**이다. 그 다음 줄의 `s1` 은 죽는다.
- 같은 모양의 `let n2 = n1;` 은 `i32` 라서 **그냥 복사**되고 `n1` 이 산다.
- 주인이 스코프를 나가면 해제가 **자동으로, 그러나 컴파일 타임에 정해진 자리에서** 일어난다.

```text
   let s1 = String::from("안녕");        let s2 = s1;        println!("{s1}");
                                              |                    |
        [s1] --꼬리표--> (힙: 안녕)           꼬리표가 s2 로        손에 아무것도
                                              넘어간다             없다 -> E0382
```

**언어도 똑같은 구조다.** 실측이 이 그림 그대로다.

```text
error[E0382]: borrow of moved value: `s1`
3 |     let s2 = s1;
  |              -- value moved here
4 |     println!("s1 = {s1} / s2 = {s2}");
  |                     ^^ value borrowed here after move
```

> **소유권(ownership)** — 어떤 값을 누가 책임지고 해제하느냐를 컴파일 타임에 하나로 정해 두는 규칙.\
> 예: `let s = String::from("hi");` 에서 `s` 가 그 힙 버퍼의 소유자이고, `s` 의 스코프 끝에서 해제된다.

> **이동(move)** — 소유권이 다른 이름으로 옮겨 가고 원래 이름이 무효가 되는 것.\
> 예: `let s2 = s1;` 뒤의 `s1` 은 값이 있는 게 아니라 **쓸 수 없는 이름**이다.

> **`Copy` 타입** — 비트를 그대로 베껴도 두 값이 각자 멀쩡한 타입.\
> 예: `i32`·`bool`·`char`·`f64`·`&T`·`Copy` 만 담은 튜플과 배열. `String`·`Vec<T>` 는 아니다.

> **해제(drop)** — 값이 차지하던 자원을 돌려주는 것. `Drop` 을 구현하면 그때 내 코드가 불린다.\
> 예: `String` 의 해제는 힙 버퍼를 반납한다. 이 문서는 그 시점을 `println!` 로 드러낸다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **그 값이 누구 것인가** — 대입·전달이 왜 복사가 아니라 이동인가, 그리고 어디가 이동의 자리인가.
2. **언제 사라지는가** — 해제 시점을 무엇으로 관찰하고, 이동이 그 시점을 어떻게 옮기는가.
3. **막혔을 때 무엇을 고르나** — 돌려받기·`clone()`·빌림 중에서.

★ 04\~07번이 「**값이 어디서 만들어지나**」였다면 이 주제는 「**그 값이 누구 것이고 언제 사라지나**」다.

## 동작 방식

### (0) 이 주제의 두 번째 창 — `Drop` 으로 해제 시점을 출력한다

**언제 쓰나** — 「언제 해제되나」를 물을 때마다. 컴파일러는 이걸 말해 주지 않는다.

이동 에러는 **컴파일러가 직접 말해 준다**(E0382). 하지만 **해제 시점은 아무도 말해 주지 않는다** —
에러도 경고도 없고, 프로그램은 조용히 잘 돈다.
그래서 이 주제에는 창이 하나 더 필요하다.

```rust
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}
```

- `Drop` 을 구현한 타입을 하나 만들어 두고 **해제될 때 이름을 찍게** 한다.
- 그러면 해제 시점이 **출력 순서**로 드러난다. 아래 모든 절이 이 창을 쓴다.
- 이 창은 `String`·`Vec` 자체에는 못 단다(남의 타입이다 — 고아 규칙, 목록의 **26번 주제**).\
  대신 **같은 자리에 `D` 를 놓아** 규칙이 같다는 것을 본다.

비용 — 없음. 관찰용 `println!` 하나뿐이고, 규칙 자체는 컴파일 타임에 끝난다.

### (1) ★ 대입은 복사가 아니라 이동이다

**언제 쓰나** — 값을 다른 이름에 넣는 모든 자리.

```rust
let s1 = String::from("안녕");
let s2 = s1;
println!("s1 = {s1} / s2 = {s2}");
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s1`
 --> ex.rs:4:21
  |
2 |     let s1 = String::from("안녕");
  |         -- move occurs because `s1` has type `String`, which does not implement the `Copy` trait
3 |     let s2 = s1;
  |              -- value moved here
4 |     println!("s1 = {s1} / s2 = {s2}");
  |                     ^^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
3 |     let s2 = s1.clone();
  |                ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

`rustc --explain E0382`:

> Since `MyStruct` is a type that is not marked `Copy`, the data gets moved out
> of `x` when we set `y`. This is fundamental to Rust's ownership system: outside
> of workarounds like `Rc`, a value cannot be owned by more than one variable.

**똑같이 생긴 코드인데 `i32` 면 통과한다.**

```rust
let n1 = 5;
let n2 = n1;
println!("n1 = {n1} / n2 = {n2}");
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
n1 = 5 / n2 = 5
(종료 코드 0)
```

```text
   String (Copy 아님)                     i32 (Copy)
   let s2 = s1;                           let n2 = n1;
   +-----------+                          +-----------+
   | s1  [무효]|                          | n1   5    |
   | s2  안녕  |                          | n2   5    |
   +-----------+                          +-----------+
     이름 하나만 살아남는다                  둘 다 산다
```

그림 해설 (한 단계씩):

- 에러 문장이 이유를 통째로 말한다 — **`which does not implement the Copy trait`**.
- 즉 갈리는 기준은 「크기」도 「힙이냐」도 아니고 **`Copy` 를 구현했느냐** 하나다.
- 컴파일러는 `s1` 을 「값이 이상한 상태」로 두는 게 아니라 **그 이름을 쓰는 것 자체를 거부**한다.

비용 — 없음. 런타임 검사가 아니라 **타입 검사**다.

### (2) ★ 이동은 무엇을 옮기나 — 스택 세 칸만 간다

**언제 쓰나** — 「이동이 비싼가」가 궁금할 때.

```rust
let s1 = String::from("안녕하세요");
let p1 = s1.as_ptr() as usize;                 // 힙 버퍼 주소
let st1 = &s1 as *const String as usize;       // 스택의 세 칸 주소
let s2 = s1;                                   // 이동
let p2 = s2.as_ptr() as usize;
let s3 = s2.clone();                           // 복제
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
s1: 스택 0x7ffc753136d8 -> 힙 0x652c769e2d00 / len=15 cap=15
String 의 스택 크기 = 24 바이트
s2: 스택 0x7ffc75313830 -> 힙 0x652c769e2d00
힙 주소가 같은가? true  (= 깊은 복사가 없었다)
스택 주소가 같은가? false (= 세 칸이 복사되긴 했다)
s3(clone): 힙 0x652c769e2d20 / s2 와 같은가? false
(종료 코드 0)

===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
s1: 스택 0x7ffd60bcdce8 -> 힙 0x5f3165fe2d00 / len=15 cap=15
String 의 스택 크기 = 24 바이트
s2: 스택 0x7ffd60bcdcb0 -> 힙 0x5f3165fe2d00
힙 주소가 같은가? true  (= 깊은 복사가 없었다)
스택 주소가 같은가? false (= 세 칸이 복사되긴 했다)
s3(clone): 힙 0x5f3165fe2d20 / s2 와 같은가? false
(종료 코드 0)
```

★ **주소 절댓값은 실행마다 바뀐다**(ASLR). 근거로 읽을 칸은 「**같은가 / 다른가**」뿐이다.
그 관계는 디버그·릴리스에서 똑같았다.

```text
   이동 전                                 이동 후
   스택                 힙                 스택                 힙
   +------------+      +---------+        +------------+      +---------+
   | s1 ptr ----+----> | 안녕하세요|        | s1  [무효] |      | 안녕하세요|
   |    len 15  |      | 15바이트 |        | s2 ptr ----+----> | 15바이트 |
   |    cap 15  |      +---------+        |    len 15  |      +---------+
   +------------+                         |    cap 15  |
    24바이트                               +------------+
                                           힙은 그대로. 24바이트만 베꼈다
```

```text
   clone()
   스택                 힙
   +------------+      +---------+
   | s2 ptr ----+----> | 안녕하세요|   0x...2d00
   +------------+      +---------+
   +------------+      +---------+
   | s3 ptr ----+----> | 안녕하세요|   0x...2d20   <- 새로 할당했다
   +------------+      +---------+
```

그림 해설 (한 단계씩):

- `String` 은 스택에 **세 칸**(포인터·길이·용량)이고 그 합이 **24바이트**다(실측).
- 이동은 그 **24바이트만 베끼고 힙은 건드리지 않는다** — 힙 주소가 같다는 것이 근거다.
- `clone()` 은 **힙을 새로 할당한다** — 주소가 다르다는 것이 근거다.
- 그래서 「이동이 비싸다」는 오해다. 비싼 것은 `clone()` 쪽이다.

비용 — 이동은 스택 몇 칸 복사. `clone()` 은 **할당 + 원소 복사**.

### (3) ★★ 언제 해제되나 — 출력 순서로 본다

**언제 쓰나** — 자원(파일·락·연결)을 쥔 타입을 쓸 때마다. 이 주제의 도식 본체다.

```rust
fn eat(d: D) {
    println!("    eat 안: {} 를 받았다", d.0);
    println!("    eat 끝");
}                       // d 는 여기서 해제된다
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(1) 블록 끝에서 해제 — 선언 역순
    블록 끝 직전
        [해제] b
        [해제] a
    블록을 나왔다
(2) drop() 으로 앞당기기
    drop(c) 호출 직전
        [해제] c
    drop(c) 뒤 — 이미 해제됐다
(3) 함수에 넘기면 그 함수가 주인이 된다
    eat(d) 호출 직전
    eat 안: d 를 받았다
    eat 끝
        [해제] d
    eat(d) 뒤 — main 끝에서 다시 해제되지 않는다
(4) 다른 이름으로 이동
    e1 -> e2 이동 완료, 블록 끝 직전
        [해제] e
    블록을 나왔다
(5) main 끝
(종료 코드 0)
```

```text
   (1) 스코프 끝 — 선언의 역순(LIFO)
        let _a = D("a");   +-- a 선언
        let _b = D("b");   |   +-- b 선언
        ...                |   |
        }  <-- 블록 끝     |   +-> [해제] b   먼저
                           +-----> [해제] a   나중
```

```text
   (2) drop(c) — 해제를 앞으로 당긴다
        let c = D("c");
        drop(c);      ---> [해제] c        <- 여기서 끝난다
        ...                                  뒤에 c 는 없다
        }  <-- 블록 끝: 아무 일도 없음
```

```text
   (3) 함수에 넘기면 주인이 바뀐다
        main                       eat
        let d = D("d")  --이동-->  d 를 받는다
                                   "eat 끝" 출력
                                   }  --> [해제] d     <- 여기다
        eat(d) 뒤: main 에는 d 가 없다
        }  <-- main 끝: d 를 다시 해제하지 않는다
```

```text
   (4) 이름만 바뀌어도 해제는 한 번
        let e1 = D("e");
        let _e2 = e1;      <- 꼬리표가 옮겨 갔을 뿐
        }  --> [해제] e    <- e2 의 스코프 끝에서 한 번
```

그림 해설 (한 단계씩):

- **스코프 끝 해제는 선언의 역순**이다(`b` 먼저, `a` 나중). 나중에 만든 것이 먼저 죽는다.
- **`drop(c)` 는 특별한 문법이 아니라 그냥 함수**다 — 값을 받아 먹고 자기 몸통 끝에서 해제한다.
- **함수에 넘기면 해제 시점이 그 함수 안으로 옮겨 간다.** `main` 끝에서 두 번 해제되지 않는다.
- 이름만 바꾼 이동도 **해제는 정확히 한 번**이다. 이것이 double free 를 막는 자리다.

비용 — 없음. 해제 코드를 컴파일러가 **컴파일 타임에 정해진 자리**에 끼워 넣는다.

### (4) 섀도잉·대입·임시값은 해제 시점이 서로 다르다

**언제 쓰나** — 같은 이름을 다시 쓰거나, 이름을 안 주거나, `let _` 을 쓸 때.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(A) 섀도잉 — 앞의 값은 언제 해제되나
    둘째까지 만들었다, 블록 끝 직전
        [해제] 둘째
        [해제] 첫째
    블록을 나왔다
(B) 대입 — 앞의 값은 언제 해제되나
    대입 직전
        [해제] 옛값
    대입 직후
        [해제] 새값
    블록을 나왔다
(C) 임시값 — 이름을 안 주면
        [해제] 이름없음
    다음 줄
(D) let _ 과 let _z 는 다르다
        [해제] 밑줄만
    let _ 다음 줄
    let _z 다음 줄
        [해제] 밑줄이름
(E) main 끝
(종료 코드 0)
```

```text
   (A) 섀도잉                          (B) 대입
   let x = D("첫째");                  let mut y = D("옛값");
   let x = D("둘째");   <- 새 바인딩     y = D("새값");   <- 같은 칸을 덮어쓴다
   ...                                 ^
   }  -> [해제] 둘째                    +-- 이 줄에서 [해제] 옛값
      -> [해제] 첫째                    }  -> [해제] 새값
   둘 다 블록 끝까지 산다                옛값은 대입 순간 죽는다
```

그림 해설 (한 단계씩):

- **섀도잉은 앞의 값을 죽이지 않는다.** 이름만 가려질 뿐 값은 블록 끝까지 살아 있다\
  (정본은 [**02번 주제**](../02-bindings-mut-and-shadowing/)).
- **대입은 죽인다.** 같은 칸을 덮어쓰므로 옛값을 그 줄에서 해제한다.
- **이름을 안 주면 그 문 끝에서 죽는다**(`D("이름없음");`).
- ★ **`let _ = 값;` 은 바인딩이 아니다** — 즉시 해제된다. `let _z = 값;` 은 바인딩이라 스코프 끝까지 산다.\
  락에서는 이 한 글자를 **컴파일러가 막는다** — `let_underscore_lock` 이 `deny` 기본이다(아래 「더 들어가면」·정답 4번).

비용 — 없음.

### (5) 함수에 넘기면 잃고, 돌려받으면 되찾는다

**언제 쓰나** — 함수를 부르는 모든 자리.

```rust
fn takes(s: String) -> usize { s.len() }
let s = String::from("hello");
let n = takes(s);
println!("{n} / {s}");
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s`
 --> ex.rs:6:22
  |
4 |     let s = String::from("hello");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
5 |     let n = takes(s);
  |                   - value moved here
6 |     println!("{n} / {s}");
  |                      ^ value borrowed here after move
  |
note: consider changing this parameter type in function `takes` to borrow instead if owning the value isn't necessary
 --> ex.rs:1:13
  |
1 | fn takes(s: String) -> usize { s.len() }
  |    -----    ^^^^^^ this parameter takes ownership of the value
  |    |
  |    in this function
```

돌려주면 되찾는다. 그런데 불편하다.

```rust
fn takes_and_gives(s: String) -> (String, usize) {
    let n = s.len();
    (s, n)                       // 돌려준다
}
fn borrows(s: &String) -> usize { s.len() }   // 10번이 정본
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
돌려받음: hello / 5
빌려주면 그냥 산다: 5 / hello
(종료 코드 0)
```

```text
   소유권을 넘기고 돌려받기                 빌려주기
   main --(이동)--> takes_and_gives        main --(&s)--> borrows
        <--(반환)--                             <--------
   반환 타입이 (String, usize) 로 부푼다      반환 타입은 usize 그대로
   받는 쪽에서 다시 묶어야 한다               main 의 s 는 계속 산다
```

그림 해설 (한 단계씩):

- 소유권을 넘기는 함수는 **쓰고 나서 돌려줘야** 호출자가 계속 쓴다.
- 그러려면 **반환 타입에 값을 얹어야** 하고, 인자가 둘이면 튜플이 셋이 된다.
- ★ **이 불편함이 빌림(`&`)의 동기다.** 정본은 목록의 **10번 주제**.
- 컴파일러도 그렇게 말한다 — `consider changing this parameter type ... to borrow instead`.

비용 — 이동 자체는 싸다. 비싼 것은 **설계가 비틀리는 것**이다.

### (6) 부분 이동 — 구조체는 칸 단위로 빠져나간다

**언제 쓰나** — 구조체에서 필드 하나만 꺼내 쓸 때.

```rust
struct User { name: String, age: u32 }
let u = User { name: String::from("준"), age: 30 };
let name = u.name;                 // 필드 하나만 이동
println!("남은 필드 = {}", u.age);   // 이건 되나?
println!("구조체 전체 = {:?}", u);   // 이건?
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of partially moved value: `u`
  --> ex.rs:10:31
   |
 7 |     let name = u.name;                 // 필드 하나만 이동
   |                ------ value partially moved here
...
10 |     println!("구조체 전체 = {:?}", u);   // 이건?
   |                                    ^ value borrowed here after partial move
   |
   = note: partial move occurs because `u.name` has type `String`, which does not implement the `Copy` trait
```

★ **`u.age` 를 쓰는 줄에는 에러가 안 났다.** 그 줄을 남기고 마지막 줄만 지우면 통과한다.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
이동한 필드 = 준
남은 필드 = 30
(종료 코드 0)
```

```text
   u                        let name = u.name;        u 전체를 쓰려 하면
   +----------------+       +----------------+        +----------------+
   | name: "준"     |  -->  | name: [빠짐]   |        | name: [빠짐]   |  ^
   | age : 30       |       | age : 30  (OK) |        | age : 30       |  |
   +----------------+       +----------------+        +----------------+  E0382
   칸 단위로 빠져나간다        살아 있는 칸은 그대로     구멍 난 채로는 통째로 못 쓴다
```

**`Drop` 을 구현한 타입이면 칸 단위 반출 자체가 금지된다.**

```rust
struct Guard { name: String }
impl Drop for Guard {
    fn drop(&mut self) { println!("[해제] {}", self.name); }
}
let g = Guard { name: String::from("자원") };
let n = g.name;
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0509]: cannot move out of type `Guard`, which implements the `Drop` trait
 --> ex.rs:7:13
  |
7 |     let n = g.name;                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |             ^^^^^^
  |             |
  |             cannot move out of here
  |             move occurs because `g.name` has type `String`, which does not implement the `Copy` trait
  |
help: consider borrowing here
  |
7 |     let n = &g.name;                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |             +
help: consider cloning the value if the performance cost is acceptable
  |
7 |     let n = g.name.clone();                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |                   ++++++++
```

`rustc --explain E0509`:

> Structs implementing the `Drop` trait have an implicit destructor that gets
> called when they go out of scope. This destructor may use the fields of the
> struct, so moving out of the struct could make it impossible to run the
> destructor. Therefore, we must think of all values whose type implements the
> `Drop` trait as single units whose fields cannot be moved.

그림 해설 (한 단계씩):

- 부분 이동은 **칸 단위**다 — 빠져나간 칸만 죽고 나머지는 산다.
- 다만 **구조체 전체를 값으로 쓰는 것**(출력·전달·반환)은 구멍 때문에 거부된다.
- `Drop` 이 붙으면 **소멸자가 그 필드를 쓸 수 있으므로** 아예 못 빼낸다(E0509).
- 그래서 `Drop` 타입에서 알맹이를 꺼내려면 `mem::take`/`replace` 를 쓴다(목록의 **44번 주제**).

비용 — 없음. 전부 컴파일 타임 판정이다.

### (7) 이동이 일어나는 자리 — 일곱 군데를 한 번에

**언제 쓰나** — 「여기서 이동이 나나?」가 궁금할 때마다.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(1) 다른 이름에 대입
    끝
        [해제] 1-대입
(2) 함수 인자
        [해제] 2-인자
    끝
(3) 구조체 필드로
    끝
        [해제] 3-필드
(4) Vec 에 push
    끝
        [해제] 4-push
(5) 튜플에 담기
    끝
        [해제] 5-튜플
(6) match 가 값을 받으면
    match 안 6-match
        [해제] 6-match
    끝
(7) move 클로저 (34번이 정본)
    클로저 안 7-클로저
    끝
        [해제] 7-클로저
(8) main 끝
(종료 코드 0)
```

```text
   이동이 나는 자리                         해제가 일어난 자리
   (1) let _b = a;                         새 이름의 스코프 끝
   (2) consume(a)                          받은 함수 안 (반환값은 그 문 끝)
   (3) Box2 { inner: a }                   그 구조체의 스코프 끝
   (4) v.push(a)                           그 Vec 의 스코프 끝
   (5) (a, 1)                              그 튜플의 스코프 끝
   (6) match a { Some(d) => ... }          그 팔의 블록 끝
   (7) move || ... a ...                   그 클로저의 스코프 끝
```

그림 해설 (한 단계씩):

- **(2)가 특이하다.** `consume(a)` 가 값을 돌려주는데 아무도 안 받으면\
  그 값은 **이름 없는 임시값**이 되어 **그 문 끝에서** 죽는다 — 그래서 `끝` 보다 먼저 찍혔다.
- **(6)이 특이하다.** `match` 가 값을 받으면 그 팔 안의 이름이 주인이 되고 **팔의 블록 끝**에서 죽는다.
- 나머지 다섯은 전부 「**받아 간 쪽의 스코프 끝**」으로 같다.
- ★ 공통 규칙 한 줄 — **값을 「값으로」 넘기는 모든 자리가 이동이다.** `&` 를 붙이면 아니다.

비용 — 없음.

### (8) `for` 루프도 이동시킨다

**언제 쓰나** — 컬렉션을 순회할 때마다. [**05번 주제**](../05-control-flow-loops-and-labels/)와 이어지는 자리다.

```rust
let v = vec![String::from("a"), String::from("b")];
for x in v { println!("{x}"); }
println!("{:?}", v);
```

```text
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
```

```text
   for x in v        -> v 를 먹는다.   x : String      순회 뒤 v 없음
   for x in &v       -> 빌린다.        x : &String     v 그대로
   for x in &mut v   -> 빌린다(가변).   x : &mut String  v 그대로, 고칠 수 있다
```

그림 해설 (한 단계씩):

- `for x in v` 는 **`v.into_iter()` 를 암묵적으로 부른다** — 그 메서드가 `self` 를 먹는다.
- 그래서 순회가 끝나면 `v` 라는 이름이 죽는다. 컴파일러가 **`&v` 를 붙이라고** 직접 제안한다.
- 세 형태의 실측 타입은 각각 `String`·`&String`·`&mut String` 이다\
  ([**05번 주제**](../05-control-flow-loops-and-labels/)의 실측). 정본은 목록의 **37번 주제**.

비용 — 없음. `into_iter` 는 원소를 옮길 뿐 복사하지 않는다.

## 문법 — 형태와 규칙

### 이동인가 복사인가를 가르는 것

| 이동한다 (`Copy` 아님) | 복사된다 (`Copy`) |
|---|---|
| `String` · `Vec<T>` · `Box<T>` | `i32`·`u8`·`f64` 등 수 타입 |
| `HashMap`·`File`·`TcpStream` | `bool` · `char` |
| `Drop` 을 구현한 모든 타입 | `&T`(불변 참조) |
| `Copy` 아닌 필드를 하나라도 가진 구조체·튜플 | `Copy` 만 담은 튜플·배열 |
| — | `#[derive(Copy, Clone)]` 를 붙인 구조체 |

실측으로 확인한 `Copy` 목록이다.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
11 truetrue 가가 1.51.5 (1, true)(1, true) [1, 2, 3][1, 2, 3] 빌린 문자열빌린 문자열 Point { x: 1, y: 2 }Point { x: 1, y: 2 }
Label { text: "라벨" } Label { text: "라벨" }
(1, "섞임") (1, "섞임")
(종료 코드 0)
```

- `i32`·`bool`·`char`·`f64`·`(i32, bool)`·`[i32; 3]`·`&str`·`#[derive(Copy)]` 구조체가 전부 원본을 남겼다.
- `String` 을 담은 구조체와 튜플은 **`.clone()` 으로만** 복제된다.
- ★ **`&mut T` 는 `Copy` 가 아니다** — 그랬다면 가변 별칭이 공짜로 생긴다(정본은 목록의 **10번 주제**).\
  던져서 확인했다 — **`&mut i32` 도 이동한다.**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `r`
 --> ex.rs:6:20
  |
3 |     let r = &mut n;
  |         - move occurs because `r` has type `&mut i32`, which does not implement the `Copy` trait
4 |     let r2 = r;          // &mut 가 Copy 라면 r 도 살아 있어야 한다
  |              - value moved here
5 |     *r2 += 1;
6 |     println!("{}", r);
  |                    ^ value borrowed here after move
```

### 금지 사례 — `Copy` 를 아무 데나 못 붙인다

```text
#[derive(Clone, Copy)]
struct Label { text: String }

error[E0204]: the trait `Copy` cannot be implemented for this type
 --> ex.rs:1:17
  |
1 | #[derive(Clone, Copy)]
  |                 ^^^^
2 | struct Label { text: String }
  |                ------------ this field does not implement `Copy`
```

`rustc --explain E0204`:

> The `Copy` trait was implemented on a type which contains a field that doesn't
> implement the `Copy` trait.

- **필드 하나가 `Copy` 가 아니면 구조체도 못 된다.** 정본은 목록의 **09번 주제**다.

### 금지 사례 — 컬렉션에서 값을 통째로 꺼내기

```text
let v = vec![String::from("첫째"), String::from("둘째")];
let first = v[0];

error[E0507]: cannot move out of index of `Vec<String>`
 --> ex.rs:8:17
  |
8 |     let first = v[0];                  // 벡터에서 하나만 꺼내면?
  |                 ^^^^ move occurs because value has type `String`, which does not implement the `Copy` trait
  |
help: consider borrowing here
  |
8 |     let first = &v[0];                  // 벡터에서 하나만 꺼내면?
  |                 +
help: consider cloning the value if the performance cost is acceptable
  |
8 |     let first = v[0].clone();                  // 벡터에서 하나만 꺼내면?
  |                     ++++++++
```

- 인덱싱은 **빌림**이라 그 안에서 값을 빼낼 수 없다. `&v[0]` 이나 `.clone()` 을 쓴다.
- 진짜로 꺼내야 하면 `v.remove(0)`·`v.swap_remove(0)`·`v.into_iter()` 쪽이다(목록의 **38번 주제**).

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 개가 전부 **E0382 한 번호**로 나온다 — 메시지 꼬리를 읽어야 갈린다.

### 1. ★ 함수에 넘긴 뒤 원래 이름을 쓴다

```text
let n = takes(s);  ->  error[E0382]: borrow of moved value: `s`
                       note: ... `takes` ... this parameter takes ownership of the value
                       help: consider cloning the value if the performance cost is acceptable
```

- **가장 흔한 첫 벽**이다. 고치는 길이 셋이고 **`clone()` 이 가장 나쁜 선택일 때가 많다**(아래 4번).
- 순서는 **① 빌린다(`&`) ② 돌려받는다 ③ 정말 필요하면 복제한다**.

### 2. ★ 루프 안에서 이동한다 — 첫 바퀴는 성공한다

```rust
for _ in 0..3 { eat(s); }
```

```text
error[E0382]: use of moved value: `s`
 --> ex.rs:5:13
  |
3 |     let s = String::from("한 번뿐");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
4 |     for _ in 0..3 {
  |     ------------- inside of this loop
5 |         eat(s);                 // 루프 안에서 이동하면?
  |             ^ value moved here, in previous iteration of loop
```

- 꼬리 문구가 다르다 — **`in previous iteration of loop`**.
- 「한 번은 되는데 두 번째가 안 되는」 코드라 눈으로 안 잡힌다. **이름이 아니라 횟수**가 문제다.

### 3. ★ 조건부 이동 — 그 갈래를 안 타도 거부된다

```rust
let cond = std::env::args().count() > 99;   // 항상 거짓이다
let s = String::from("조건부");
if cond { eat(s); }                          // 여기서만 이동한다
println!("{s}");                             // 실행은 절대 안 먹었는데?
```

```text
error[E0382]: borrow of moved value: `s`
 --> ex.rs:6:16
  |
4 |     let s = String::from("조건부");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
5 |     if cond { eat(s); }                          // 여기서만 이동한다
  |                   - value moved here
6 |     println!("{s}");                             // 실행은 절대 안 먹었는데?
  |                ^ value borrowed here after move
```

- ★ **실행되지 않는 갈래도 이동이다.** 판정이 **컴파일 타임**이라 「실제로 안 탔다」는 항변이 안 통한다.
- 이 대비가 「런타임 검사가 아니다」의 가장 강한 근거다.

### 4. `clone()` 으로 덮는다

- 컴파일러의 `help: consider cloning the value if the performance cost is acceptable` 는\
  **「비용을 감당할 수 있으면」이라는 단서가 붙은 제안**이다. 조건 없는 추천이 아니다.
- 쓰면 안 되는 자리 셋.
  - **루프 안에서** — 바퀴마다 할당이 는다(2번의 `eat(s.clone())` 제안이 정확히 그 함정이다).
  - **읽기만 하는데** 복제 — `&` 로 끝나는 자리다.
  - **「누가 주인인가」를 안 정하고** 복제 — 사본이 갈라져 나중에 어느 쪽이 정본인지 모르게 된다.
- 쓸 만한 자리 — 사본이 **정말로 따로 살아야** 할 때, 그리고 원본을 남겨야 할 때.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
a = 원본에 덧붙임 / b = 원본
첫째 / 둘째 / v 는 그대로 ["첫째", "둘째"]
(종료 코드 0)
```

- `a.clone()` 한 뒤 `a` 를 고쳐도 `b` 는 안 변한다 — **둘은 남남**이다.

### 5. `drop(s)` 를 특별한 문법으로 읽는다

```text
drop(s);
println!("{s}");

error[E0382]: borrow of moved value: `s`
 --> ex.rs:4:16
  |
3 |     drop(s);
  |          - value moved here
4 |     println!("{s}");
  |                ^ value borrowed here after move
```

- `drop` 은 **그냥 값을 먹는 함수**다. 그래서 에러도 다른 이동과 **똑같이 E0382**다.
- 「해제 함수라서 특별하다」가 아니라 「**먹었으니 이름이 죽었다**」가 맞는 읽기다.

### 6. 부분 이동해 놓고 구조체를 통째로 쓴다

```text
let name = u.name;
println!("{:?}", u);   ->  error[E0382]: borrow of partially moved value: `u`
```

- 꼬리 문구가 또 다르다 — **`partially moved`**. `u.age` 는 멀쩡한데 `u` 가 안 된다.
- 필드만 계속 쓸 거면 **필드로 쓰고**, 통째로 쓸 거면 **빼내지 말고 빌린다**(`&u.name`).

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **진단 메시지의 모양**과 **최적화가 지우는 복사**다.
**소유권 규칙 자체는 전부 언어 보장**이고, 빌드 프로필을 바꿔도 답이 안 바뀐다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 값마다 소유자가 하나다 | **언어** | Book ch.4.1 · `--explain E0382`(`a value cannot be owned by more than one variable`) |
| 소유자가 스코프를 나가면 해제된다 | **언어** | Reference(Destructors) · `Drop` 실측 |
| 같은 스코프의 변수는 **선언 역순**으로 해제된다 | **언어** | Reference(Destructors) · 실측 `[해제] b` → `[해제] a` |
| 대입·인자 전달·반환이 이동이다 | **언어** | E0382 · 실측 7자리 |
| `Copy` 타입은 이동하지 않는다 | **언어** | E0382 의 `does not implement the Copy trait` · 실측 |
| `Copy` 아닌 필드가 있으면 `Copy` 를 못 만든다 | **언어** | **E0204** |
| `Drop` 구현체는 부분 이동이 안 된다 | **언어** | **E0509** + explain |
| 인덱스에서 값을 빼낼 수 없다 | **언어** | **E0507** |
| **이동이 힙을 복사하지 않는다** | **언어(의미)** + 구현(코드 생성) | 힙 주소가 같다는 실측. 다만 **스택 24바이트 복사가 실제로 일어나는지는 최적화가 정한다** |
| `String` 의 스택 크기가 24바이트 | **플랫폼** | 64비트 기준. `size_of::<String>()` 실측 |
| **주소 절댓값** | **런타임(ASLR)** | 실행마다 바뀐다. 근거로 읽을 칸은 「같은가/다른가」뿐 |
| **조건부 이동을 런타임 플래그로 처리하는 것** | **구현** | 아래 실측 — 언어는 「한 번만 해제된다」만 보장한다 |
| **에러·경고 메시지의 문구와 `help` 제안** | **rustc 구현** | 버전이 오르면 바뀐다. **에러 번호**가 더 안정적이다 |
| `dead_code`·`unused_variables` 가 경고인 것 | **린트 설정** | `-D warnings` 로 에러가 된다 |

★ **조건부 이동은 런타임 흔적을 남긴다** — 이 주제에서 유일하게 「컴파일 타임에 다 끝나지 않는」 자리다.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
--- 인자 없이 실행: ./ex_dbg
cond = false
    스코프 끝 직전
        [해제] 조건부
--- 인자를 주고 실행: ./ex_dbg x
cond = true
    eat 안 조건부
        [해제] 조건부
```

- 같은 바이너리가 **두 실행에서 다른 자리에 해제**했다. 컴파일러가 **드롭 플래그**를 숨겨 두었기 때문이다.
- 보장되는 것은 「**정확히 한 번 해제된다**」이고, **그 플래그의 존재와 형태는 구현**이다.
- 최적화가 갈래를 확정할 수 있으면 플래그가 사라질 수도 있다 — 그래서 **관찰이지 보장이 아니다**.

> **드롭 플래그(drop flag)** — 값이 이동됐는지를 런타임에 기억해 두는 숨은 1비트.\
> 예: `if cond { eat(d); }` 뒤의 스코프 끝에서 「아직 내 것인가」를 그 비트로 판단한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 값을 읽기만 한다 | `&T` (목록의 **10번 주제**) | 이동이 안 나고 원본이 산다 |
| 값을 고쳐야 한다 | `&mut T` | 소유권을 안 넘기고 변경한다 |
| 받은 쪽이 **끝까지 책임**진다 | 값으로 받는다 (`String`) | 파일·연결·버퍼를 넘겨 주는 자리 |
| 잠깐 넘겼다가 계속 써야 한다 | 빌린다. 그게 안 되면 **돌려받는다** | 반환 타입이 부푸는 것이 신호다 |
| 사본이 **따로 살아야** 한다 | `.clone()` | 원본과 남남이 되는 것이 목적일 때만 |
| 순회한 뒤에도 원본이 필요하다 | `for x in &v` | `for x in v` 는 먹는다 |
| 구조체에서 알맹이를 꺼낸다 | 필드 이동 — 단 `Drop` 이면 `mem::take` | E0509 를 피하는 관용구(목록의 **44번 주제**) |
| 해제를 앞당긴다 | `drop(x)` | 락·파일을 일찍 놓을 때 |
| 해제를 관찰한다 | `impl Drop` + `println!` | 「언제 사라지나」를 보는 유일한 창 |

판단 규칙 두 줄.

- **「이 값의 주인이 누구여야 하나」를 먼저 정하고 타입을 쓴다.** 에러가 나서 고치는 게 아니다.
- **`clone()` 은 답이 아니라 미룸이다.** 붙이기 전에 「빌리면 되나」를 한 번 묻는다.

## 핵심 문장

- 값마다 소유자가 **하나**고, 대입·인자 전달·반환은 **복사가 아니라 이동**이다.
- 이동은 **스택의 몇 칸만 베끼고 힙은 그대로 둔다** — 힙 주소가 같다는 실측이 근거다.
- 이동한 뒤 원래 이름을 쓰면 **E0382** 다. 「값이 이상해진」 게 아니라 **그 이름이 죽은 것**이다.
- `Copy` 를 구현한 타입만 이동하지 않는다 — 갈리는 기준은 크기도 힙도 아니고 **그 트레이트 하나**다.
- 해제는 **소유자의 스코프 끝**, **선언의 역순**이다. 이동하면 해제 시점도 **받은 쪽으로 옮겨 간다**.
- 섀도잉은 앞의 값을 **안 죽이고**, 대입은 **죽인다**. `let _ = 값;` 은 **즉시** 죽인다.
- 구조체는 **칸 단위로 부분 이동**하되, `Drop` 을 구현하면 **통째로만** 다룬다(E0509).
- **실행되지 않는 갈래의 이동도 이동**이다 — 판정이 컴파일 타임이기 때문이다.
- `clone()` 은 힙을 새로 할당한다. **빌릴 수 있으면 빌리는 것이 먼저**다(목록의 **10번 주제**).

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 08번)
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(변수 바인딩·섀도잉) — 섀도잉의 정본.\
  여기서는 **섀도잉이 해제를 앞당기지 않는다**는 실측만 보탰다
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — 블록이 값이라는 것. 이동은 **값이 옮겨 가는 것**이라 그 위에 선다
- [**05번 주제**](../05-control-flow-loops-and-labels/)(제어 흐름) — `for x in v` 가 무엇을 주나의 실측이 거기 있다
- [**06번 주제**](../06-functions-and-never-type/)(함수·반환) — 인자와 반환이 이동의 자리다
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 — **그쪽은** 「**왜 이 모델을 골랐나**」(GC 도 수동도 거부한 논증, 청구서),\
  **여기는** 「**그 규칙이 코드에서 무엇을 하나**」다. 모델의 논증을 여기서 다시 쓰지 않는다
- [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md) — 소유권 모델의 **역사**는 거기
- [`../../../../memory-management/`](../../../../memory-management/) — 스택·힙·할당·해제의 **일반론**은 거기, 여기는 Rust 의 이동 규칙
- 목록의 **09번 주제**(`Copy`/`Clone`/`Drop`) — `Copy` 판정과 `Drop` 시점의 정본. 여기서는 **관찰 도구로만** 썼다
- 목록의 **10번 주제**(빌림 `&`·`&mut`) — 이 주제의 불편함이 거기로 이어진다
- 목록의 **14번 주제**(`String` 대 `&str`) · **37번 주제**(`IntoIterator` 세 형태) · **44번 주제**(`mem::take`) · **41번 주제**(`Rc`/`Arc`)

## 용어 풀이

- **소유권(ownership)** — 값 하나의 해제 책임을 이름 하나에 묶어 두는 규칙.
- **소유자(owner)** — 그 책임을 진 이름. 스코프를 나가면 값이 해제된다.
- **이동(move)** — 소유권이 옮겨 가고 원래 이름이 무효가 되는 것.
- **부분 이동(partial move)** — 구조체·튜플에서 일부 칸만 빠져나간 상태. 남은 칸은 계속 쓸 수 있다.
- **`Copy`** — 비트 복사로 두 값이 각자 유효해지는 타입에 붙는 표식.
- **`Clone`** — 명시적으로 사본을 만드는 트레이트. `String` 은 힙을 새로 할당한다.
- **해제(drop)** — 값이 쥔 자원을 반납하는 것. 컴파일러가 스코프 끝에 끼워 넣는다.
- **`Drop` 트레이트** — 해제 순간에 불릴 코드를 내가 적는 자리.
- **드롭 플래그(drop flag)** — 조건부 이동에서 「아직 내 것인가」를 기억하는 숨은 런타임 비트.
- **double free** — 같은 자원을 두 번 반납하는 버그. 소유자를 하나로 묶어 타입 검사로 지운다.
- **임시값(temporary)** — 이름이 안 붙은 값. 그 문 끝에서 해제된다.
- **`into_iter()`** — `self` 를 먹는 순회. `for x in v` 가 암묵적으로 부른다.

---

## 더 들어가면

- **이동 뒤의 메모리를 지우지 않는다.** 이동은 「원본을 무효화하는 런타임 조작」이 아니라\
  「**그 이름을 더 못 쓰게 하는 컴파일 타임 판정**」이다. 그래서 비용이 0이다.
- ★ **`Vec<i32>` 는 원소가 `Copy` 라도 이동한다**(실측 — [**05번 주제**](../05-control-flow-loops-and-labels/)).\
  `Copy` 인지는 **컨테이너 타입**이 정하지 원소가 정하지 않는다. `[i32; 3]` 은 `Copy` 고 `Vec<i32>` 는 아니다.
- **`let _ = 값;`** 과 **`let _z = 값;`** 의 차이는 락에서 사고가 될 뻔하다가 **린트가 막는다.**\
  `drop(m.lock().unwrap());` 뒤에는 같은 스레드의 `try_lock()` 이 **`true`**, `let _guard = m.lock()` 뒤에는 **`false`** 였다(실측).\
  그런데 `let _ = m.lock();` 자체는 **`let_underscore_lock`(deny 기본) 때문에 컴파일 에러**다 — 정답 4번에 전문을 실었다.\
  ★ **린트가 없는 다른 `Drop` 타입에서는 그대로 조용히 사라진다.** 락의 정본은 목록의 **52번 주제**다.
- **한 소유자 규칙을 런타임 비용으로 푸는 길**이 `Rc`/`Arc` 다(목록의 **41번 주제**).\
  `--explain E0382` 도 같은 말을 한다 — `outside of workarounds like Rc`.
- **소유권을 안 넘기고 알맹이만 바꾸는 관용구**가 `mem::replace`/`mem::take` 다(목록의 **44번 주제**).\
  E0509 로 막힌 자리가 정확히 그 도구의 자리다.
