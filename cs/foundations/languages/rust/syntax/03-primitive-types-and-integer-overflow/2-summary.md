# rust/syntax/03 — 기본 타입·정수 오버플로·`as` 캐스트 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [The Rust Reference](https://doc.rust-lang.org/reference/) 의 Type cast expressions ·
> Operator expressions(Overflow) · Behavior not considered `unsafe` 절 · [std 문서](https://doc.rust-lang.org/std/)의 `i32`/`u8`/`char`/`mem::size_of`.
> 이 머신의 `rust-docs`(1.92.0)를 열어 확인했고, 인용은 그 판의 원문이다.
> **실행 검증** — 이 문서의 모든 출력은 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서 돌렸다.\
> ★ **오버플로가 걸린 프로그램은 전부 두 번 돌렸다** — `rustc --edition 2021 ex.rs`(디버그)와\
> `rustc --edition 2021 -O ex.rs`(릴리스). **한쪽만 돌린 결과는 이 문서에 없다.**
> **버전** — 정수 오버플로 정책은 1.0부터(RFC 560). `as` 로 부동소수를 정수로 바꿀 때의 **포화**는 **1.45.0**부터.\
> `TryFrom`/`try_into` 는 **1.34.0**부터, `dbg!` 는 **1.32.0**부터, `type_name_of_val` 은 **1.76.0**부터.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**정수 타입은 자릿수가 고정된 주행거리계다. 끝까지 가면 000으로 돈다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 자릿수가 고정된 계기판 | 정수 타입 (`u8` 은 0\~255, `i32` 는 약 ±21억) |
| 999 다음에 000 | **랩어라운드**(wrap-around) — 2의 보수 |
| 계기판에 달린 **경보기** | 디버그 빌드의 오버플로 검사 |
| 경보기를 뗀 계기판 | **릴리스 빌드** — 조용히 돈다 |
| 자릿수 적은 계기판에 옮겨 적기 | `as` 캐스트 — **윗자리를 그냥 버린다** |
| 「넘치면 어떻게 할지」를 미리 고르는 네 손잡이 | `checked_` · `wrapping_` · `saturating_` · `overflowing_` |

- `250u8 + 10` 은 260인데 계기판이 255까지뿐이라 **4로 돈다.**
- 디버그 빌드는 그 순간 **경보를 울리고 차를 세운다**(패닉·종료 코드 101).
- 릴리스 빌드는 **아무 말 없이 4를 준다.** 에러도 경고도 로그도 없다.
- ★ **「릴리스에서 안 터졌다」는 「안전하다」가 아니다.** 터지지 않는 쪽이 **더 위험하다** — 틀린 값이 그대로 흘러간다.

```text
                 250u8 + 10  =  260

  디버그 빌드 (rustc ex.rs)              릴리스 빌드 (rustc -O ex.rs)
  +-----------------------------+       +-----------------------------+
  | x = 250                     |       | x = 250                     |
  | panicked at 'attempt to     |       | y = 4                       |
  |   add with overflow'        |       |                             |
  | 종료 코드 101                |       | 종료 코드 0                  |
  +-----------------------------+       +-----------------------------+
    -> 프로그램이 멈춘다                    -> 틀린 값이 조용히 흘러간다
```

**언어도 똑같은 구조다.** 위 두 블록은 **같은 소스 파일**을 플래그만 바꿔 돌린 실측이다.

> **랩어라운드(wrap-around)** — 표현 범위를 넘으면 반대쪽 끝에서 다시 시작하는 것.\
> 예: `u8` 에서 `255 + 1` 은 0이고 `0 - 1` 은 255다(실측).

> **패닉(panic)** — 복구 불가능한 오류로 판단해 그 스레드를 중단시키는 것.\
> 예: 오버플로·0으로 나누기·배열 범위 초과. 프로세스 종료 코드는 101이다(실측).

> **포화(saturating)** — 범위를 넘으면 **끝값에서 멈추는** 것. 돌지 않는다.\
> 예: `250u8.saturating_add(10)` 은 4가 아니라 **255**다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 같은 소스가 **디버그와 릴리스에서 다른 답을 내는 자리**는 정확히 어디인가 — 그리고 **안 다른 자리**는 어디인가.
2. `as` 는 **무엇을 말없이 하는가** — 정수끼리와 부동소수→정수가 왜 다르게 구는가.
3. 「넘칠 수 있다」를 코드에 적어 두는 방법은 무엇인가 — 네 손잡이와 `TryFrom` 중 언제 무엇을 고르는가.

## 동작 방식

### (1) 정수 타입과 기본값 — 안 적으면 `i32`

**언제 쓰나** — 숫자를 쓰는 모든 자리.

| 계열 | 타입 | 크기(바이트) | 비고 |
|---|---|---|---|
| 부호 있음 | `i8` `i16` `i32` `i64` `i128` `isize` | 1 2 4 8 16 **8** | 기본은 `i32` |
| 부호 없음 | `u8` `u16` `u32` `u64` `u128` `usize` | 1 2 4 8 16 **8** | 인덱스·길이는 `usize` |

`isize`/`usize` 의 8은 **이 머신(64비트)의 값**이다 — 플랫폼에 달렸다.

```text
$ cat ex.rs  (일부)
row("usize", size_of::<usize>(), align_of::<usize>());

usize          size_of=8   align_of=8
이 머신의 포인터 폭 = 64 비트
usize 범위 0 ~ 18446744073709551615
```

기본이 `i32` 라는 것은 **컴파일러가 직접 말해 준다.**

```text
$ cat ex.rs
fn main() {
    let x = 3_000_000_000;
    println!("{x}");
}

error: literal out of range for `i32`
  = note: the literal `3_000_000_000` does not fit into the type `i32` whose range is `-2147483648..=2147483647`
  = note: `#[deny(overflowing_literals)]` on by default
```

그림 해설 (한 단계씩):

- 타입을 한 글자도 안 적었는데 컴파일러가 **`i32` 라는 이름을 댔다.** 이게 기본값의 근거다.
- `overflowing_literals` 는 **기본이 `deny`** 라 경고가 아니라 **에러**다.
- 그래서 **리터럴로 쓴 오버플로는 컴파일 타임에 잡힌다.** 런타임 오버플로와 완전히 다른 층이다((2)번과 대비).

비용 — 없음. 타입 크기는 컴파일 타임 상수다.

### (2) ★ 정수 오버플로 — 디버그와 릴리스가 갈린다

**언제 쓰나** — 덧셈·뺄셈·곱셈이 있는 모든 코드. 즉 거의 전부.

같은 파일을 두 번 돌린다. **리터럴끼리의 식으로 쓰면 안 된다** — 그건 컴파일 타임 린트가 먼저 잡는다((5)번 대비).

```rust
fn add(a: u8, b: u8) -> u8 { a + b }

fn main() {
    let x: u8 = 250;
    println!("x = {x}");
    let y = add(x, 10);
    println!("y = {y}");
}
```

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
x = 250

thread 'main' (1376898) panicked at ex.rs:1:30:
attempt to add with overflow
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)

===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
x = 250
y = 4
(종료 코드 0)
```

**갈리는 것은 최적화가 아니라 검사 플래그다.** 넷을 다 돌려 분리했다.

| 빌드 | 결과 |
|---|---|
| `rustc ex.rs` | **패닉** (종료 101) |
| `rustc -O ex.rs` | `y = 4` (종료 0) |
| `rustc -O -C overflow-checks=on ex.rs` | **패닉** (종료 101) |
| `rustc -C overflow-checks=off ex.rs` | `y = 4` (종료 0) |

```text
        최적화 (-O)         오버플로 검사 (overflow-checks)
              |                        |
              |                        +--> 이것만이 패닉 여부를 정한다
              v
        속도에만 관여
```

그림 해설 (한 단계씩):

- **`-O` 자체가 랩어라운드를 만드는 게 아니다.** `-O` 가 `overflow-checks` 를 기본으로 끌 뿐이다.
- 그래서 릴리스 프로필에서도 `overflow-checks = true` 로 되돌릴 수 있다(`Cargo.toml` 의 `[profile.release]`).
- **디버그에서 통과한 테스트가 릴리스에서 다른 값을 낸다** — 이 주제가 위험한 진짜 이유다.

★ **흔들리는 칸 / 안 흔들리는 칸** — 패닉 메시지를 근거로 쓸 때 어디를 읽을지 미리 정해 둔다.

| 칸 | 흔들리나 | 세 번 돌려 확인한 것 |
|---|---|---|
| `thread 'main'` | 안 흔들림 | 세 판 동일 |
| **괄호 안 번호** `(1376898)` | **매 실행마다 바뀐다** | `1378642` / `1378645` / `1378648` |
| `panicked at ex.rs:1:30` | 안 흔들림 | 소스가 같으면 같다 |
| `attempt to add with overflow` | 안 흔들림 | 세 판 동일 |
| 종료 코드 `101` | 안 흔들림 | 세 판 동일 |

**그래서 이 문서는 괄호 안 번호를 근거로 쓰지 않는다.** 남겨 두는 것은 「출력을 그대로 옮긴다」는 규칙 때문이다.

비용 — 디버그 빌드는 산술마다 검사 분기가 하나씩 붙는다. 릴리스는 붙지 않는다.

### (3) 네 손잡이 — 「넘치면 어떻게 할지」를 코드에 적는다

**언제 쓰나** — 넘칠 수 있다는 것을 **내가 아는** 자리. 전부 `u8` 의 250 기준 실측이다.

| 메서드 | 250 + 10 | 250 + 3 | 0 - 1 | 돌려주는 것 |
|---|---|---|---|---|
| `checked_add` | `None` | `Some(253)` | `None` | `Option<u8>` |
| `wrapping_add` | `4` | `253` | `255` | `u8` |
| `saturating_add` | `255` | `253` | `0` | `u8` |
| `overflowing_add` | `(4, true)` | `(253, false)` | `(255, true)` | `(u8, bool)` |

```text
$ ./ex_dbg                          $ ./ex_rel        (-O 로 빌드)
checked_add    = None               checked_add    = None
checked_add(3) = Some(253)          checked_add(3) = Some(253)
wrapping_add   = 4                  wrapping_add   = 4
saturating_add = 255                saturating_add = 255
overflowing_add= (4, true)          overflowing_add= (4, true)
overflowing(3) = (253, false)       overflowing(3) = (253, false)
0.checked_sub(1)    = None          0.checked_sub(1)    = None
0.wrapping_sub(1)   = 255           0.wrapping_sub(1)   = 255
0.saturating_sub(1) = 0             0.saturating_sub(1) = 0
```

그림 해설 (한 단계씩):

- ★ **왼쪽과 오른쪽이 한 글자도 다르지 않다.** 네 손잡이는 **빌드 프로필에 흔들리지 않는다.**
- 그게 이 넷을 쓰는 이유다 — `+` 는 빌드에 따라 답이 갈리지만 이것들은 안 갈린다.
- 고르는 기준: 「실패를 호출자에게 알릴 것인가」(`checked_`) · 「돌게 할 것인가」(`wrapping_`) ·\
  「끝에서 멈출 것인가」(`saturating_`) · 「값과 넘침 여부를 둘 다 받을 것인가」(`overflowing_`).

비용 — `checked_` 는 `Option` 하나, `overflowing_` 은 튜플 하나. 전부 컴파일 타임에 풀리는 값 타입이라 힙 할당이 없다.

### (4) ★ `as` 캐스트 — 조용히 자른다

**언제 쓰나** — 타입을 억지로 맞출 때. **가장 조심할 연산이다.**

```rust
let n: i32 = 300;
println!("300_i32 as u8   = {}", n as u8);
let m: i32 = -1;
println!("-1_i32 as u8    = {}", m as u8);
println!("-1_i32 as u32   = {}", m as u32);
let big: i64 = 4_294_967_296;
println!("2^32 as u32     = {}", big as u32);
let c: u8 = 200;
println!("200_u8 as i8    = {}", c as i8);
```

```text
===== 디버그 =====                    ===== 릴리스 (-O) =====
300_i32 as u8   = 44                 300_i32 as u8   = 44
-1_i32 as u8    = 255                -1_i32 as u8    = 255
-1_i32 as u32   = 4294967295         -1_i32 as u32   = 4294967295
2^32 as u32     = 0                  2^32 as u32     = 0
200_u8 as i8    = -56                200_u8 as i8    = -56
```

**컴파일 경고는 0줄이었다.** `rustc` 가 낸 진단 줄 수를 세었다.

```text
$ rustc --edition 2021 -W warnings ex.rs -o ex_w 2>&1 | wc -l
0
```

```text
   300 (i32)  =  0000 0000 0000 0000 0000 0001 0010 1100
                                             ^^^^^^^^^^^
   as u8      ->                              0010 1100  = 44
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                 윗 24비트를 그냥 버린다 — 아무도 안 알려 준다
```

그림 해설 (한 단계씩):

- 정수→정수 `as` 는 **비트를 그대로 읽는다.** 자르거나(좁히기) 부호 확장한다(넓히기).
- **에러도 경고도 패닉도 없다.** 디버그든 릴리스든 같다 — **오버플로 검사의 대상이 아니다.**
- 그래서 `as` 는 이 주제에서 **오버플로보다 더 조용한** 사고 경로다.\
  오버플로는 적어도 디버그에서 터지지만, `as` 는 **어느 빌드에서도 안 터진다.**

★ **`rustc` 는 말 안 하지만 `clippy` 는 한다** — 다만 **기본으로 켜져 있지 않다.**

```text
$ cargo clippy -- -W clippy::cast_possible_truncation
warning: casting `i32` to `u8` may truncate the value
 --> src/main.rs:7:13
  |
7 |     let c = n as u8;
  |             ^^^^^^^
  |
  = help: if this is intentional allow the lint with `#[allow(clippy::cast_possible_truncation)]` ...
  = help: for further information visit https://rust-lang.github.io/rust-clippy/rust-1.92.0/index.html#cast_possible_truncation
  = note: requested on the command line with `-W clippy::cast-possible-truncation`
help: ... or use `try_from` and handle the error accordingly
  |
7 -     let c = n as u8;
7 +     let c = u8::try_from(n);
```

비용 — 없음(기계어 한둘). **비용이 0이라서 위험하다.**

### (5) 부동소수 → 정수 `as` 는 다르다 — **포화**한다

**언제 쓰나** — 계산 결과를 정수로 떨굴 때.

```text
  3.9_f64 as i32 = 3                 <- 0 쪽으로 버림
 -3.9_f64 as i32 = -3
  1e30_f64 as i32 = 2147483647       <- i32::MAX 에서 멈춘다 (돌지 않는다)
 -1e30_f64 as i32 = -2147483648      <- i32::MIN
  f64::NAN as i32 = 0                <- NaN 은 0
  f64::INFINITY as i32 = 2147483647
  -1.5_f64 as u8  = 0                <- 음수는 0으로
  1e30_f64 as u8  = 255
i32::MAX = 2147483647 / i32::MIN = -2147483648
```

디버그와 릴리스가 **한 글자도 같았다.**

Reference(Type cast expressions)의 원문:

> Casting from a float to an integer will round the float towards zero
>
> - `NaN` will return `0`
> - Values larger than the maximum integer value, including `INFINITY`, will saturate to the maximum value of the integer type.
> - Values smaller than the minimum integer value, including `NEG_INFINITY`, will saturate to the minimum value of the integer type.

그림 해설 (한 단계씩):

- **정수→정수는 자르고(돌고), 부동→정수는 포화한다.** 같은 `as` 인데 규칙이 다르다.
- 이 포화 동작은 **1.45.0부터**다. 그 전에는 범위 밖 값이 미정의 동작이었다.
- 그래도 **조용하다는 점은 같다** — 1e30이 21억이 되는데 아무 말이 없다.

비용 — 하드웨어가 포화를 직접 지원하지 않으면 분기가 몇 개 붙는다(Reference 각주).

### (6) 안전한 대안 — `TryFrom` / `try_into`

**언제 쓰나** — 좁히는 변환에서 **못 담는 경우를 처리해야 할 때.**

```text
300_i32.try_into::<u8>() = Err(TryFromIntError(()))
200_i32.try_into::<u8>() = Ok(200)
u8::try_from(-1_i32)     = Err(TryFromIntError(()))
실패 — Display: out of range integral type conversion attempted / Debug: TryFromIntError(())
i32::from(200_u8)        = 200
```

```text
  좁히는 변환                          넓히는 변환
  i32 -> u8                           u8 -> i32
       |                                   |
       v                                   v
  못 담을 수 있다                       항상 담긴다
  TryFrom  -> Result                  From     -> 값 그대로
```

그림 해설 (한 단계씩):

- **넓히는 쪽은 `From`** 이라 실패가 없다 — `i32::from(200_u8)` 은 그냥 값이다.
- **좁히는 쪽은 `TryFrom`** 이고 `Result` 를 준다. 실패를 **타입이 강제로 들게** 한다.
- `as` 와의 차이 한 줄: **`as` 는 못 담으면 버리고, `try_into` 는 못 담으면 알려 준다.**
- 트레이트 자체의 정본은 [목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)(변환 트레이트)다. 여기서는 **`as` 의 대안**으로만 본다.

비용 — `Result` 하나. 성공 경로는 `as` 와 같은 기계어로 줄어든다(할당 없음).

### (7) 나머지 기본 타입 — `size_of` 로 재 본다

**언제 쓰나** — 「이게 몇 바이트지?」가 궁금할 때. **외우지 말고 재라.**

```text
i8             size_of=1   align_of=1
i16            size_of=2   align_of=2
i32            size_of=4   align_of=4
i64            size_of=8   align_of=8
i128           size_of=16  align_of=16
u8             size_of=1   align_of=1
usize          size_of=8   align_of=8
isize          size_of=8   align_of=8
f32            size_of=4   align_of=4
f64            size_of=8   align_of=8
bool           size_of=1   align_of=1
char           size_of=4   align_of=4
()             size_of=0   align_of=1
(u8,u8)        size_of=2   align_of=1
(u8,u32)       size_of=8   align_of=4
[u8; 4]        size_of=4   align_of=1
[u32; 4]       size_of=16  align_of=4
&[u8]          size_of=16  align_of=8
&str           size_of=16  align_of=8
```

```text
'a' as u32   = 97
'한' as u32  = 54620
'🦀' as u32  = 129408
"한".len()   = 3 (바이트 수)
"한".chars().count() = 1
97u8 as char = a
true as u8   = 1 / false as u8 = 0
```

그림 해설 (한 단계씩):

- **`char` 는 4바이트**다. C 의 `char`(1바이트)와 이름만 같고 다른 물건이다 — **유니코드 스칼라 값** 하나를 담는다.
- 그래서 `"한".len()` 은 1이 아니라 **3**이다. `len()` 은 UTF-8 **바이트 수**다(정본은 [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)).
- `bool` 은 1바이트이고 `as u8` 로 0/1이 된다.
- `()` 는 **0바이트**다 — 값이 하나뿐이라 담을 정보가 없다(정본은 [**04번 주제**](../04-expressions-and-semicolons/)).
- `(u8, u32)` 가 **8바이트**인 것은 정렬(`align_of=4`) 때문에 패딩이 끼어서다. 2+4=6이 아니다.
- `&[u8]`·`&str` 이 16바이트인 것은 **팻 포인터**(주소+길이)라서다.

비용 — `size_of`·`align_of` 는 컴파일 타임 상수다. 런타임 계산이 없다.

## 문법 — 형태와 규칙

### 숫자 리터럴의 형태

```rust
let a = 42;            // 접미사 없음 -> 추론, 힌트 없으면 i32
let b = 42u8;          // 접미사
let c = 42_u8;         // 밑줄은 어디든 끼워도 된다
let d = 1_000_000;     // 자릿수 구분
let e = 0xff;          // 16진   255
let f = 0o77;          // 8진     63
let g = 0b1010_1010;   // 2진    170
let h = b'A';          // 바이트 리터럴 -> u8  (65)
let i = 3.0f32;        // 부동소수 접미사
```

### 금지 사례 — 컴파일러가 거부하는 것

```rust
let x: u8 = 300;             // error: literal out of range for `u8`  (deny by default)
let y: u8 = 250 + 10;        // error: this arithmetic operation will overflow
let z = 54620u32 as char;    // error[E0604]: only `u8` can be cast as `char`
```

- 앞의 둘은 **런타임이 아니라 컴파일 타임**에 잡힌다. 린트 이름은 `overflowing_literals`·`arithmetic_overflow` 이고 **둘 다 기본이 `deny`** 다.
- `u32 as char` 가 막히는 이유 — `char` 는 서러게이트 구간(`0xD800`\~`0xDFFF`)을 뺀 값만 허용하는데 `u32` 는 그걸 보장 못 한다.\
  `char::from_u32` 가 `Option<char>` 로 돌려주는 안전한 길이다(`rustc --explain E0604` 가 직접 안내한다).

### 관찰 도구 — `{:?}` · `{:#?}` · `dbg!`

```rust
#[derive(Debug)]
struct Point { x: i32, y: u8 }

let p = Point { x: 300, y: 300u32 as u8 };
println!("{:?}", p);
println!("{:#?}", p);
let cut = dbg!(300_i32) as u8;
```

```text
{:?}  -> Point { x: 300, y: 44 }
{:#?} ->
Point {
    x: 300,
    y: 44,
}
[ex.rs:11:15] n = 300
```

- `{}`(Display)는 직접 구현해야 쓸 수 있다. 안 하면 **E0277**(`doesn't implement std::fmt::Display`).
- **`dbg!` 는 표준 에러로 나가고, `-O` 로 빌드해도 사라지지 않는다**(실측 — 릴리스 출력에 그대로 있었다).\
  「릴리스에서는 빠지겠지」로 읽으면 안 된다. 지우는 것은 사람 몫이다.
- `dbg!` 는 값을 **그대로 돌려준다** — 식 한가운데 끼워 넣을 수 있다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 다섯 중 셋은 **아무 출력도 없이** 틀린다.

### 1. ★ 「릴리스에서 안 터졌으니 안전하다」

```text
개발 중 (디버그)                          운영 (릴리스)
+------------------------------+        +------------------------------+
| 테스트 전부 초록              |        | 에러 0 · 경고 0 · 로그 0      |
| 오버플로가 나면 바로 패닉해서  |        | 합계가 4로 나온다             |
| 테스트가 잡아 준다            |        | 아무도 모른다                 |
+------------------------------+        +------------------------------+
  -> 여기서 통과한 코드가                   -> 여기서 조용히 틀린다
```

- **패닉이 없는 쪽이 더 위험하다.** 오류가 값으로 둔갑해 뒤로 흘러간다.
- 「디버그 테스트가 초록이니 오버플로가 없다」도 틀렸다 — **그 경로를 실제로 밟는 입력으로 테스트했을 때만** 참이다.
- 고치는 법은 셋 중 하나다: ① 네 손잡이로 **의도를 코드에 적는다** ② 타입을 넓힌다 ③ 릴리스 프로필에서 `overflow-checks` 를 켠다.

### 2. ★ `as` 는 아무도 안 알려 준다

```text
let n: i32 = 300;   let c = n as u8;   // c == 44

  rustc 경고        : 0줄  (-W warnings 로도 0줄)
  rustc 에러        : 없음
  디버그 패닉       : 없음
  릴리스 동작       : 디버그와 동일
  clippy 기본       : 안 잡는다
  clippy -W cast_possible_truncation : 잡는다
```

- **진단 경로가 전부 침묵한다.** 「돌려 봤는데 안 터지더라」로는 절대 못 찾는다.
- `as` 를 쓸 자리는 실제로 좁다 — **못 담을 수 있으면 `try_into`** 가 맞다.
- 「윗자리를 버려도 된다」가 진짜 의도면 **`wrapping_` 계열이나 주석으로 그 의도를 남긴다.**

### 3. ★ 나눗셈은 릴리스에서도 패닉한다 — 오버플로의 예외

```rust
fn div(a: i32, b: i32) -> i32 { a / b }
println!("i32::MIN / -1 = {}", div(i32::MIN, -1));
```

```text
===== 디버그: rustc --edition 2021 ex.rs =====
시작

thread 'main' (1388859) panicked at ex.rs:1:31:
attempt to divide with overflow
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

```text
===== 릴리스: rustc --edition 2021 -O ex.rs =====
시작

thread 'main' (1388913) panicked at ex.rs:1:31:
attempt to divide with overflow
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

`-C overflow-checks=off` 를 붙여도 **여전히 패닉했다.** 0으로 나누기도 셋 다 패닉했다.

Reference(Operator expressions, Overflow)의 원문:

> Using `/` or `%`, where the left-hand argument is the smallest integer of a signed integer type
> and the right-hand argument is `-1`. **These checks occur even when `-C overflow-checks` is disabled, for legacy reasons.**

- 그래서 **「릴리스는 감싼다」는 `+`·`-`·`*` 이야기**다. `/`·`%` 는 다르다.
- 「릴리스니까 안 터진다」로 외우면 여기서 운영 장애가 난다.
- 나눗셈에도 네 손잡이가 있다 — `checked_div`·`wrapping_div`·`saturating_div`·`overflowing_div`(실측 표는 3-answer 6번).

### 4. `usize` 는 플랫폼에 달렸다

```text
이 머신(x86_64)               32비트 타깃이라면
  size_of::<usize>() = 8        size_of::<usize>() = 4
  최댓값 1844경...               최댓값 약 42억
```

- 인덱스·길이가 `usize` 인 이유는 **주소 폭과 같아야 하기 때문**이다.
- `usize` 로 계산한 값을 `u32` 에 `as` 로 넣는 코드는 **32비트에서는 멀쩡하고 64비트에서만 잘린다.**\
  「내 머신에서 됐다」가 가장 안 통하는 자리다.
- `len()` 이 `usize` 를 돌려주므로 **길이 계산의 뺄셈은 언더플로 후보**다. 빈 문자열로 실측했다.

```rust
fn len_of(s: &str) -> usize { s.len() }
let last = len_of("") - 1;
```

```text
===== 디버그: rustc --edition 2021 ex.rs =====
시작

thread 'main' (1511076) panicked at ex.rs:6:16:
attempt to subtract with overflow
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

```text
===== 릴리스: rustc --edition 2021 -O ex.rs =====
시작
last = 18446744073709551615
(종료 코드 0)
```

  릴리스 쪽 값이 **`usize::MAX`** 다 — 「길이」라는 이름을 단 값이 1844경이 되어 뒤로 흘러간다.\
  이 값으로 인덱싱하면 그때서야 다른 곳에서 터진다. **터지는 자리와 틀린 자리가 멀어진다.**

### 5. 리터럴 오버플로는 컴파일 타임에 잡혀서 **착시를 만든다**

```text
let y: u8 = 250 + 10;
  ->  error: this arithmetic operation will overflow
      attempt to compute `250_u8 + 10_u8`, which would overflow
      = note: `#[deny(arithmetic_overflow)]` on by default
```

- 이건 `-O` 를 붙여도 **똑같이 에러**다(실측). 컴파일 타임 린트라 빌드 프로필과 무관하다.
- 그래서 **상수로 실험하면 「Rust 는 오버플로를 다 잡아 준다」는 인상을 받는다.**
- 실제 사고는 **런타임 값**에서 난다.

★ **경계가 생각보다 좁았다 — 실측으로 확인했다.** 린트가 보는 것은 **그 식 자체의 리터럴**이지 값이 아니다.

```text
let y: u8 = 250 + 10;             -> 컴파일 에러 (arithmetic_overflow)

let x: u8 = 250;                  -> 컴파일 통과
let y = x + 10;                      디버그에서 패닉 / 릴리스에서 y = 4
```

  **`let` 을 한 번만 거쳐도 린트가 못 본다.** 그래서 「상수로 쓰면 다 잡힌다」는 틀린 요약이고,\
  실험할 때 함수로 빼든 `let` 으로 받든 **런타임 경로가 만들어진다.**

## 구현 세부사항 대 언어 보장

이 갈래에서 「구현 세부사항」은 **빌드 프로필·플랫폼·툴체인에 달린 것**이다.

★ 가장 중요한 한 칸 — **「릴리스가 감싼다」는 언어 보장이 아니다.**
Reference(Behavior not considered `unsafe` — Integer overflow)의 원문:

> If a program contains arithmetic overflow, the programmer has made an error. ...
> When the programmer has enabled `debug_assert!` assertions (for example, by enabling a non-optimized build),
> implementations **must** insert dynamic checks that panic on overflow.
> **Other kinds of builds may result in panics or silently wrapped values on overflow, at the implementation's discretion.**
> In the case of implicitly-wrapped overflow, implementations must provide well-defined
> (even if still considered erroneous) results by using two's complement overflow conventions.

읽는 법 세 줄:

- **디버그에서 패닉하는 것은 의무다**(must).
- **릴리스에서 감싸는 것은 재량이다**(may … at the implementation's discretion). 패닉해도 규격 위반이 아니다.
- 감싼다면 **2의 보수로 정의된 값**이어야 한다. 즉 **값은 정의돼 있지만 여전히 오류**다.

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 디버그 빌드가 오버플로에 패닉한다 | **언어**(must) | Reference 위 인용 · 실측 |
| **릴리스 빌드가 감싼다** | **구현 재량** | 위 인용. rustc 는 감싸지만 **보장이 아니다** |
| 감쌀 때 2의 보수 값 | **언어** | 위 인용 · `250+10 -> 4` 실측 |
| `/`·`%` 의 오버플로·0나누기 검사 | **언어** | Reference "even when `-C overflow-checks` is disabled" · 실측 |
| 정수→정수 `as` 가 자른다 | **언어** | Reference(int-truncation) · 실측 |
| 부동→정수 `as` 가 포화한다 | **언어**(1.45.0부터) | Reference(float-as-int) · 실측 |
| `i32`/`f64` 기본 타입 | **언어**(폴백 규칙) | `literal out of range for i32` 에러 |
| **`usize`/`isize` 의 크기** | **타깃 플랫폼** | `size_of::<usize>() == 8`(x86_64) |
| `(u8, u32)` 가 8바이트인 것 | **구현**(기본 레이아웃) | `#[repr(Rust)]` 는 필드 순서·패딩을 보장하지 않는다 |
| 패닉 메시지의 **괄호 안 번호** | **실행마다 다름** | 세 판 전부 다른 값 |
| `dbg!` 가 릴리스에서도 남는 것 | **std 설계** | 실측 — `-O` 출력에 그대로 있었다 |

★ **「안 터졌다」는 「안전하다」가 아니다.** 이 주제에서 그 문장이 성립하는 자리가 셋이다 —
릴리스 오버플로 · 모든 빌드의 `as` · 32비트/64비트가 갈리는 `usize` 계산.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 이유 |
|---|---|---|
| 넘칠 리가 없다고 **확신**한다 | `+` 그대로 | 디버그가 안전망이 된다 |
| 넘칠 수 있고 **호출자가 알아야** 한다 | `checked_*` → `Option` | 실패를 타입에 들려 보낸다 |
| 넘치면 **끝값으로 눌러도** 된다(게이지·비율) | `saturating_*` | 돌면 말이 안 되는 값이 된다 |
| **돌아야** 맞다(해시·체크섬·순환 버퍼) | `wrapping_*` | 의도를 코드에 적는다 |
| 값과 넘침 여부를 **둘 다** 쓴다 | `overflowing_*` | 분기와 값을 한 번에 |
| 타입을 **좁혀야** 한다 | `try_into()` → `Result` | `as` 는 말없이 버린다 |
| 타입을 **넓힌다** | `From`/`i64::from(x)` | 실패가 없으므로 `as` 도 되지만 의도가 덜 보인다 |
| 부동소수를 정수로 | `as`(포화를 알고) 또는 직접 범위 검사 | `as` 는 NaN 을 0으로 만든다 |
| 인덱스·길이 | `usize` | 다른 타입으로 담으면 플랫폼 의존이 생긴다 |

판단 규칙 두 줄.

- **좁히는 변환에 `as` 를 쓰지 않는다.** 쓸 거면 「버려도 된다」는 근거를 주석이나 `wrapping_` 으로 남긴다.
- **릴리스 동작을 근거로 결론을 내지 않는다.** 디버그·릴리스를 **둘 다 돌려 본 것**만 사실로 적는다.

## 핵심 문장

- 같은 소스가 **디버그에서는 패닉하고 릴리스에서는 4를 준다.** 갈리는 것은 `-O` 가 아니라 `overflow-checks` 플래그다.
- **릴리스가 감싸는 것은 언어 보장이 아니라 구현 재량**이다(Reference: "at the implementation's discretion").
- **`/` 와 `%` 는 예외다** — `i32::MIN / -1` 과 0나누기는 `-C overflow-checks=off` 에서도 패닉한다.
- `as` 는 **정수끼리는 자르고 부동→정수는 포화**하며, 어느 쪽도 **경고 한 줄 없다.** `clippy` 도 기본으로는 안 잡는다.
- 좁히는 변환의 안전한 짝은 **`TryFrom`/`try_into`** 다 — 못 담으면 `Err` 로 알려 준다.
- 힌트가 없으면 정수는 `i32`, 부동소수는 `f64`. 리터럴 오버플로는 **컴파일 타임에 `deny`** 라 런타임 사고와 층이 다르다.
- `char` 는 **4바이트 유니코드 스칼라**이고 `()` 는 **0바이트**다. 「외우지 말고 `size_of` 로 재라.」

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 03번)
- [**02번 주제**](../02-bindings-mut-and-shadowing/)(변수 바인딩·타입 추론) — **타입이 어떻게 `i32` 로 정해지는가**는 거기
- [**04번 주제**](../04-expressions-and-semicolons/)(표현식 지향) — **`()` 가 왜 0바이트인가**는 거기
- [**01번 주제**](../01-cargo-crates-and-modules/)(`cargo`·크레이트) — `--release` 와 `rustc -O` 의 관계
- [`../../../data-representation/`](../../../../data-representation/) — **그쪽은 2의 보수·IEEE 754 라는 표현 자체**까지,\
  **여기는 Rust 가 그 위에 얹은 오버플로 「정책」부터**다. 비트 표현의 원리는 여기서 다시 설명하지 않는다.
- [`../../언어-특성/README.md`](../../언어-특성/README.md) — **그쪽은 안전성을 어느 통화로 지불하는가의 논증**,\
  **여기는 그 지불이 산술 한 줄에서 어떤 모양으로 나타나는가**다.
- [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)(슬라이스·UTF-8) — `"한".len() == 3` 의 정본
- [목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)(변환 트레이트) — `From`/`TryFrom` 의 정본. 여기서는 `as` 의 대안으로만 봤다
- [목록의 **07번 주제**](../07-const-static-and-const-fn/)(상수·`const fn`) — 상수 접기와 컴파일 타임 계산
- [목록의 **23번 주제**](../23-panic-vs-result/)(`panic!` 대 `Result`) — 「여기서 끝낼 것인가」의 판단

## 용어 풀이

- **오버플로(overflow)** — 연산 결과가 그 타입의 범위를 벗어나는 것. 언더플로도 같은 규칙으로 다룬다.
- **랩어라운드(wrap-around)** — 범위를 벗어나면 반대쪽 끝에서 다시 세는 것. 2의 보수로 정의된다.
- **포화(saturating)** — 범위를 벗어나면 끝값에서 멈추는 것.
- **패닉(panic)** — 복구 불가능하다고 보고 스레드를 중단하는 것. 프로세스 종료 코드 101.
- **`overflow-checks`** — 산술마다 검사 코드를 넣을지 정하는 rustc 플래그. 디버그 기본 켜짐, 릴리스 기본 꺼짐.
- **린트 `overflowing_literals`** — 리터럴이 타입 범위를 넘을 때. 기본 `deny`.
- **린트 `arithmetic_overflow`** — 상수 식 산술이 넘칠 때. 기본 `deny`.
- **`as` 캐스트** — 강제 변환 연산자. 정수끼리는 비트를 자르고, 부동→정수는 포화한다.
- **`TryFrom`/`try_into`** — 실패할 수 있는 변환. `Result` 를 돌려준다.
- **유니코드 스칼라 값(Unicode scalar value)** — 서러게이트 구간을 뺀 코드 포인트. Rust 의 `char` 가 담는 것.
- **정렬(alignment)** — 그 타입의 값이 놓일 수 있는 주소의 배수 조건. `align_of` 로 잰다.
- **팻 포인터(fat pointer)** — 주소에 길이가 붙은 참조. `&str`·`&[T]` 가 16바이트인 이유.

---

## 더 들어가면

- `Cargo.toml` 의 `[profile.release] overflow-checks = true` 로 릴리스에서도 검사를 켤 수 있다. 실측이다.

```text
--- cargo run --release (기본) ---
x = 250
y = 4

--- [profile.release] overflow-checks = true 를 넣고 다시 ---
x = 250

thread 'main' (1514993) panicked at src/main.rs:1:30:
attempt to add with overflow
```

  `rustc` 쪽 대응은 `-O -C overflow-checks=on` 이고, 그쪽도 **릴리스인데 패닉**했다.
- 반대도 된다 — `rustc -C overflow-checks=off`(최적화 없이)로 **디버그인데 감싸게** 만들 수 있다(실측 `y = 4`).\
  그래서 「디버그/릴리스」가 아니라 「**검사 켜짐/꺼짐**」이 정확한 축이다.
- `saturating_div` 는 조금 특이하다 — `i32::MIN.saturating_div(-1)` 이 `i32::MAX` 다(실측).\
  `wrapping_div` 는 `i32::MIN` 을 그대로 돌려준다.
- `b'A'` 는 `u8` 리터럴이라 `65`다. 문자열 바이트를 다룰 때 쓴다.
- `dbg!` 는 파일·줄·열과 식을 함께 찍는다(`[ex.rs:11:15] n = 300`). **표준 에러**로 나가므로 `2>/dev/null` 로 지워진다(실측).
- `{:#?}` 는 중첩 구조를 들여쓰기해 준다. 구조체가 깊어질수록 `{:?}` 보다 훨씬 읽기 낫다.
