# rust/syntax/03 — 기본 타입·정수 오버플로·`as` 캐스트 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서 실제로 돌려 얻은 것이다.\
> ★ **오버플로가 걸린 프로그램은 전부 두 번 돌렸다** — `rustc --edition 2021 ex.rs`(디버그)와 `rustc --edition 2021 -O ex.rs`(릴리스).\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다 — 패닉 메시지의 `panicked at ex.rs:N:C` 가 그래서 같은 이름이다.\
> ★ 패닉 메시지 **괄호 안 번호**(`(1376898)`)는 **실행마다 바뀐다.** 출력을 그대로 옮기느라 남겨 두었을 뿐,\
> 근거로 읽을 칸이 아니다(세 판을 돌려 `1378642`/`1378645`/`1378648` 로 다름을 확인했다).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 이 프로그램을 두 빌드로 돌리면

**출력**

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

**왜 그런가**

- 디버그는 **`x = 250` 까지만 찍고 패닉**한다. 종료 코드 **101**.
- 릴리스는 **`y = 4`** 를 찍고 정상 종료한다. 종료 코드 **0**.\
  260을 256으로 나눈 나머지가 4다(2의 보수 랩어라운드).
- 패닉 문장은 문자 그대로 **`attempt to add with overflow`** 다.\
  `panicked at ex.rs:1:30` 은 **함수 `add` 안의 `a + b`** 를 가리킨다 — `main` 이 아니다.

```text
                250u8 + 10 = 260  (u8 범위는 0~255)

  디버그                                  릴리스
  검사 코드가 산술마다 붙어 있다            검사 코드가 없다
        |                                       |
        v                                       v
  넘쳤다 -> panic!                         넘친 비트를 그냥 버린다
  종료 101                                 260 & 0xFF = 4, 종료 0
```

**`add` 를 함수로 빼지 않고 `let y = x + 10;` 로 썼으면**

- **아무것도 안 달라진다.** 실측했다 — 디버그에서 패닉(`panicked at ex.rs:4:13`), 릴리스에서 `y = 4`.
- 컴파일 타임 린트는 **`let` 을 한 번만 거쳐도 못 본다.**

**`let y: u8 = 250 + 10;` 로 썼으면**

```text
error: this arithmetic operation will overflow
 --> ex.rs:2:17
  |
2 |     let y: u8 = 250 + 10;
  |                 ^^^^^^^^ attempt to compute `250_u8 + 10_u8`, which would overflow
  |
  = note: `#[deny(arithmetic_overflow)]` on by default
```

- 이건 **컴파일 에러**다. 실행까지 가지 않는다(8번).
- 즉 린트가 보는 것은 **그 식에 직접 적힌 리터럴**이지 값이 아니다. 경계가 생각보다 좁다.

> **랩어라운드(wrap-around)** — 범위를 넘으면 반대쪽 끝에서 다시 세는 것.\
> 예: `u8` 에서 260은 260 − 256 = 4가 된다.

### 2. 네 손잡이의 결과를 채워라

**출력** (왼쪽 디버그 / 오른쪽 `-O` — **한 글자도 다르지 않았다**)

```text
$ ./ex_dbg                          $ ./ex_rel
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

**왜 그런가**

| # | 식 | 값 | 타입 |
|---|---|---|---|
| (1) | `250u8.checked_add(10)` | `None` | `Option<u8>` |
| (2) | `250u8.checked_add(3)` | `Some(253)` | `Option<u8>` |
| (3) | `250u8.wrapping_add(10)` | `4` | `u8` |
| (4) | `250u8.saturating_add(10)` | `255` | `u8` |
| (5) | `250u8.overflowing_add(10)` | `(4, true)` | `(u8, bool)` |
| (6) | `0u8.wrapping_sub(1)` | `255` | `u8` |
| (7) | `0u8.saturating_sub(1)` | `0` | `u8` |

- ★ **디버그와 릴리스가 같다.** 이 넷은 **빌드 프로필에 흔들리지 않는다.**
- 그게 이 넷을 쓰는 이유다 — `+` 는 빌드에 따라 「패닉이냐 4냐」가 갈리지만,\
  `wrapping_add` 는 **어디서든 4**이고 `checked_add` 는 **어디서든 `None`** 이다.\
  **의도가 코드에 적혀 있으니 빌드가 뜻을 바꾸지 못한다.**
- 고르는 기준:
  - 「넘치면 **호출자가 알아야** 한다」 → **`checked_*`**(`Option`). `?` 나 `match` 로 이어 붙인다.
  - 「넘치면 **끝값에서 멈춰야** 한다」(게이지·비율·클램프) → **`saturating_*`**.
  - 「**돌아야** 맞다」(해시·체크섬·순환 버퍼) → **`wrapping_*`**.
  - 「값과 넘침 여부를 **둘 다**」 → **`overflowing_*`**.

```text
        250 + 10 = 260 을 u8 에 담아야 한다

  checked_    -> None            "못 담아요" 라고 말한다
  wrapping_   -> 4               "돌려서 담을게요"
  saturating_ -> 255             "끝까지만 담을게요"
  overflowing_-> (4, true)       "4로 담았는데 넘쳤어요"
```

### 3. ★ 이 다섯 줄의 출력과 진단을 예측하라

**출력**

```text
===== 디버그 =====                    ===== 릴리스 (-O) =====
300_i32 as u8   = 44                 300_i32 as u8   = 44
-1_i32 as u8    = 255                -1_i32 as u8    = 255
-1_i32 as u32   = 4294967295         -1_i32 as u32   = 4294967295
2^32 as u32     = 0                  2^32 as u32     = 0
200_u8 as i8    = -56                200_u8 as i8    = -56
```

**진단**

```text
$ rustc --edition 2021 ex.rs -o ex_dbg
(아무 줄도 없음)

$ rustc --edition 2021 -W warnings ex.rs -o ex_w2 2>&1 | wc -l
0
```

**왜 그런가**

- 다섯 값은 `44` · `255` · `4294967295` · `0` · `-56` 이다.
- **디버그와 릴리스가 같다.** `as` 는 **오버플로 검사의 대상이 아니다.**
- **컴파일 경고는 0줄**이다. `-W warnings` 로 올려도 0줄이었다.

```text
   300 (i32)  =  0000 0000 0000 0000 0000 0001 0010 1100
   as u8      ->                              0010 1100  = 44
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                 윗 24비트를 그냥 버린다

   -1 (i32)   =  1111 1111 1111 1111 1111 1111 1111 1111
   as u8      ->                              1111 1111  = 255
   as u32     =  1111 ... 1111                           = 4294967295

   200 (u8)   =  1100 1000
   as i8      ->  최상위 비트를 부호로 읽는다             = -56
```

- 정수끼리의 `as` 는 **비트를 그대로 읽는 연산**이다. 좁히면 자르고, 넓히면 부호에 맞춰 늘린다.
- `200u8 as i8` 이 `-56` 인 것은 값이 아니라 **해석**이 바뀐 것이다(비트는 그대로 `1100 1000`).

**`clippy` 는 잡는가**

- **기본으로는 안 잡는다.** 같은 코드에 `cargo clippy` 를 그냥 돌리면 `needless_return` 만 나왔다.
- 켜면 잡는다.

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

- 정리하면 — **모든 기본 진단 경로가 침묵한다.** 「돌려 봤는데 안 터지더라」로는 절대 못 찾는다.\
  `as` 가 이 주제에서 **오버플로보다 조용한** 사고 경로인 이유다.

### 4. 부동소수를 정수로 떨구면

**출력** (디버그·릴리스 동일)

```text
  3.9_f64 as i32 = 3
 -3.9_f64 as i32 = -3
  1e30_f64 as i32 = 2147483647
 -1e30_f64 as i32 = -2147483648
  f64::NAN as i32 = 0
  f64::INFINITY as i32 = 2147483647
  -1.5_f64 as u8  = 0
  1e30_f64 as u8  = 255
i32::MAX = 2147483647 / i32::MIN = -2147483648
```

**왜 그런가**

- **규칙이 다르다.** 정수→정수는 **자르고(돌고)**, 부동→정수는 **포화한다**(끝값에서 멈춘다).
- `NaN` 은 **0**이다.

```text
  정수 -> 정수 (3번)                   부동소수 -> 정수 (이 문항)
  +---------------------------+       +---------------------------+
  | 300 as u8   ->  44        |       | 1e30 as i32 -> i32::MAX   |
  | 넘친 비트를 버린다          |       | 끝값에서 멈춘다            |
  | 값이 작아질 수도 커질 수도  |       | 절대 넘어가지 않는다        |
  +---------------------------+       +---------------------------+
     "돈다"                              "포화한다"
```

Reference(Type cast expressions)의 원문:

> Casting from a float to an integer will round the float towards zero
>
> - `NaN` will return `0`
> - Values larger than the maximum integer value, including `INFINITY`, will saturate to the maximum value of the integer type.
> - Values smaller than the minimum integer value, including `NEG_INFINITY`, will saturate to the minimum value of the integer type.

- 「towards zero」라서 `-3.9` 가 `-4` 가 아니라 **`-3`** 이다. 버림이지 내림이 아니다.
- 이 포화 동작은 **1.45.0부터**다. 그 전에는 범위 밖 값이 미정의 동작이었다.
- 그래도 **조용하다는 점은 정수 쪽과 같다** — 1e30이 21억이 되는데 아무 진단이 없다.

### 5. 나눗셈은 어떤가

**출력**

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

`-C overflow-checks=off` 를 붙여도 —

```text
$ rustc --edition 2021 -O -C overflow-checks=off ex.rs -o ex_off && ./ex_off
시작

thread 'main' (1390460) panicked at ex.rs:1:31:
attempt to divide with overflow
(종료 101)
```

0으로 나누기는 **세 빌드 전부** 같았다 — `rustc ex.rs` · `rustc -O ex.rs` · `rustc -O -C overflow-checks=off ex.rs`.
셋 다 아래와 같았고 종료 코드는 101이었다.

```text
시작

thread 'main' (1390295) panicked at ex.rs:1:33:
attempt to divide by zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

**왜 그런가**

- 디버그도 릴리스도 **똑같이 패닉**한다. `-C overflow-checks=off` 로도 **안 꺼진다.**
- 기준 소스가 그 예외를 명시한다. Reference(Operator expressions — Overflow):

  > Using `/` or `%`, where the left-hand argument is the smallest integer of a signed integer type
  > and the right-hand argument is `-1`. **These checks occur even when `-C overflow-checks` is disabled, for legacy reasons.**

- 그래서 요약을 이렇게 고쳐야 한다:\
  ~~「릴리스는 감싼다」~~ → **「릴리스는 `+`·`-`·`*` 를 감싼다. `/`·`%` 는 감싸지 않는다.」**
- 이유를 한 줄로 — `i32::MIN / -1` 의 참값(21억 4748만 3648)은 `i32` 에 **담을 수 없고**,\
  0으로 나누기는 **정의된 값이 아예 없다.** 감쌀 값 자체가 없으니 검사를 끌 수가 없다.
- 나눗셈에도 네 손잡이가 있다(실측).

```text
i32::MIN.wrapping_div(-1)   = -2147483648
i32::MIN.checked_div(-1)    = None
10i32.checked_div(0)        = None
i32::MIN.overflowing_div(-1)= (-2147483648, true)
i32::MIN.saturating_div(-1) = 2147483647
```

- `saturating_div` 만 **`i32::MAX`** 를 준다 — 「넘칠 수 없는 값으로 눌렀다」는 뜻이다.

### 6. 크기를 맞혀라

**출력**

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

**왜 그런가**

| 물은 것 | 값 |
|---|---|
| `bool` | **1** |
| `char` | **4** |
| `()` | **0** |
| `(u8, u8)` | **2** |
| `(u8, u32)` | **8** |
| `[u8; 4]` | **4** |
| `&str` | **16** |
| `usize` | **8**(이 머신) |

- **`char` 가 4바이트인 이유** — 유니코드 **스칼라 값 하나**를 담기 때문이다.\
  최대가 `0x10FFFF` 라 21비트가 필요하고, 그걸 담는 가장 작은 정렬 단위가 4바이트다.\
  C 의 `char`(1바이트)와 이름만 같고 다른 물건이다.

```text
'a'  as u32 = 97          한 글자 = 한 스칼라 값
'한' as u32 = 54620
'🦀' as u32 = 129408      0x1F980 — 1바이트로는 어림도 없다

"한".len() = 3            문자열은 UTF-8 "바이트" 수
"한".chars().count() = 1  글자 수는 이쪽
```

- **`(u8, u32)` 가 8인 이유** — `u32` 의 정렬이 4라서 `u8` 뒤에 **패딩 3바이트**가 끼고, 전체도 4의 배수로 맞춰진다.\
  1 + 3(패딩) + 4 = 8. 5나 6이 아니다.

```text
  (u8, u32)  메모리 배치 (align_of = 4)

  offset:  0    1    2    3    4    5    6    7
          +----+----+----+----+----+----+----+----+
          | u8 |   패딩       |       u32         |
          +----+----+----+----+----+----+----+----+
          size_of = 8
```

- **`&str` 이 16인 이유** — **팻 포인터**이기 때문이다. 주소 8바이트 + 길이 8바이트.\
  `&[u8]` 도 같은 이유로 16이다. 길이를 들고 다녀야 슬라이싱과 경계 검사가 된다.
- `()` 가 **0바이트**인 것은 값이 하나뿐이라 담을 정보가 없어서다(정본은 [**04번 주제**](../04-expressions-and-semicolons/)).
- `[u8; 4]` 가 4인 것은 배열이 **원소를 빈틈없이 잇는 것**이기 때문이다. 길이는 타입에 박혀 있어 값에 안 들어간다.

### 7. 타입을 안 적으면

**출력**

```text
42 의 타입    = i32
4.2 의 타입   = f64
'가' 의 타입  = char
"가" 의 타입 = &str
(1,2) 의 타입 = (i32, i32)
[1,2] 의 타입 = [i32; 2]
() 의 타입    = ()
```

**왜 그런가**

- `let x = 42;` 는 **`i32`** 다. 힌트가 전혀 없을 때의 **타입 폴백**이다.
- 위 출력은 `type_name_of_val`(1.76.0부터)로 얻은 **관찰**이다. std 문서가 이 문자열을 보장하지 않는다.

**`type_name` 에 기대지 않고 증명하려면** — 범위를 넘겨 보고 컴파일러가 이름을 대게 한다.

```text
$ cat ex.rs
fn main() {
    let x = 3_000_000_000;
    println!("{x}");
}

error: literal out of range for `i32`
 --> ex.rs:2:13
  |
2 |     let x = 3_000_000_000;
  |             ^^^^^^^^^^^^^
  |
  = note: the literal `3_000_000_000` does not fit into the type `i32` whose range is `-2147483648..=2147483647`
  = help: consider using the type `u32` instead
  = note: `#[deny(overflowing_literals)]` on by default
```

- **「does not fit into the type `i32`」** — 컴파일러가 직접 이름을 댔다. 이쪽이 언어 규칙 쪽 근거다.
- `'a'` 는 **`char`**, `"a"` 는 **`&str`** 이다. 작은따옴표와 큰따옴표가 **다른 타입**을 만든다.

**`54620u32 as char`**

```text
error[E0604]: only `u8` can be cast as `char`, not `u32`
 --> ex.rs:3:20
  |
3 |     println!("{}", n as char);
  |                    ^^^^^^^^^ invalid cast
  |
help: consider using `char::from_u32` instead
  |
3 -     println!("{}", n as char);
3 +     println!("{}", char::from_u32(n));
```

`rustc --explain E0604` 의 설명:

> `char` is a Unicode Scalar Value, an integer value from 0 to 0xD7FF and
> 0xE000 to 0x10FFFF. (The gap is for surrogate pairs.) Only `u8` always fits in
> those ranges so only `u8` may be cast to `char`.

- **컴파일되지 않는다.** 에러 번호는 **E0604**, 대안은 **`char::from_u32`**(`Option<char>` 을 돌려준다).
- 반대 방향(`97u8 as char`)은 된다 — `u8` 은 **항상** 유효한 스칼라 값이기 때문이다(실측 `a`).
- 여기가 이 주제에서 **`as` 가 거부당하는 거의 유일한 자리**다. 나머지 `as` 는 다 통과한다.

### 8. 이 두 줄은 어디서 잡히는가

**출력**

```text
$ cat ex.rs
fn main() {
    let x: u8 = 300;
    println!("{x}");
}

error: literal out of range for `u8`
 --> ex.rs:2:17
  |
2 |     let x: u8 = 300;
  |                 ^^^
  |
  = note: the literal `300` does not fit into the type `u8` whose range is `0..=255`
  = note: `#[deny(overflowing_literals)]` on by default
```

```text
$ cat ex.rs
fn main() {
    let x: u8 = 250 + 10;
    println!("{x}");
}

error: this arithmetic operation will overflow
 --> ex.rs:2:17
  |
2 |     let x: u8 = 250 + 10;
  |                 ^^^^^^^^ attempt to compute `250_u8 + 10_u8`, which would overflow
  |
  = note: `#[deny(arithmetic_overflow)]` on by default
```

**왜 그런가**

- 둘 다 **컴파일 타임**에 잡힌다. 실행까지 가지 않는다.
- 린트 이름은 **`overflowing_literals`** 와 **`arithmetic_overflow`** 이고, **둘 다 기본 수준이 `deny`** 다.\
  그래서 경고가 아니라 **에러**다.
- `-O` 를 붙여도 **똑같이 에러**다(실측). 컴파일 타임 린트라 빌드 프로필과 무관하다.

**이 사실이 만드는 착시**

```text
  상수로 실험하면                          실제 코드에서는
  +----------------------------+         +----------------------------+
  | let x: u8 = 250 + 10;      |         | let y = add(x, 10);        |
  | -> 컴파일 에러              |         | -> 디버그 패닉 / 릴리스 4   |
  |                            |         |                            |
  | "Rust 가 다 잡아 주는구나"  |         | 컴파일러는 아무 말도 안 했다 |
  +----------------------------+         +----------------------------+
```

- **린트가 보는 것은 그 식에 직접 적힌 리터럴**이다. `let` 을 한 번만 거쳐도 못 본다(1번 실측).
- 그래서 1번 질문은 값을 **함수 인자로 넘겨** 런타임 경로를 확실히 만들었다.\
  실은 `let x: u8 = 250; let y = x + 10;` 도 런타임이었다 — **경계가 생각보다 좁다.**

### 9. 릴리스가 감싸는 것은 보장인가

**기준 소스 원문** — Reference, Behavior not considered `unsafe` — Integer overflow

> If a program contains arithmetic overflow, the programmer has made an error. In the following
> discussion, we maintain a distinction between arithmetic overflow and wrapping arithmetic.
> The first is erroneous, while the second is intentional.
>
> When the programmer has enabled `debug_assert!` assertions (for example, by enabling a
> non-optimized build), implementations **must** insert dynamic checks that panic on overflow.
> Other kinds of builds **may** result in panics or silently wrapped values on overflow,
> **at the implementation's discretion**.
>
> In the case of implicitly-wrapped overflow, implementations **must** provide well-defined
> (even if still considered erroneous) results by using two's complement overflow conventions.

**왜 그런가**

- **언어가 의무로 요구하는 쪽은 「디버그에서 패닉」이다** — `must insert dynamic checks that panic`.
- 릴리스 쪽에는 **`may`** 와 **`at the implementation's discretion`** 을 쓴다.\
  즉 **릴리스에서 패닉해도 규격 위반이 아니다.** rustc 가 감싸는 것은 **이 구현의 선택**이다.
- 감쌀 때의 **값은 보장된다** — 2의 보수 규약을 따라야 한다(`must provide well-defined … results`).
- 첫 문장이 이 절의 결론이다: **「If a program contains arithmetic overflow, the programmer has made an error.」**\
  값이 정의돼 있다는 것과 그게 **옳은 동작이라는 것은 다른 말**이다.

```text
                         오버플로가 났다
                               |
            +------------------+------------------+
            |                                     |
      디버그 빌드                            릴리스 빌드
      must panic                            may panic  또는  may wrap
      (언어의 의무)                          (구현의 재량 — rustc 는 wrap)
            |                                     |
            +------------------+------------------+
                               |
                   어느 쪽이든 "프로그래머의 오류"다
                   감싼 값이 "정답"이 되는 게 아니다
```

- 실무 함의 한 줄 — **릴리스 동작을 설계의 근거로 삼지 않는다.**\
  돌아야 맞는 자리면 `wrapping_*` 로 **적어 둔다**. 그래야 빌드가 뜻을 바꾸지 못한다(2번).

### 10. `usize` 와 플랫폼

**출력**

```text
usize          size_of=8   align_of=8
isize          size_of=8   align_of=8
usize 범위 0 ~ 18446744073709551615
이 머신의 포인터 폭 = 64 비트
```

**왜 그런가**

- 이 머신(`x86_64-unknown-linux-gnu`)에서 **8**이다. `rustc --print cfg` 도 `target_pointer_width="64"` 를 말한다.
- **32비트 타깃이라면 4**다. 범위도 0\~약 42억으로 줄어든다.\
  *(32비트 타깃은 이 머신에 설치돼 있지 않아 직접 안 돌렸다 — 「안 돌려 봄」이 아니라 **환경이 없어 못 돌림**이다.)*
- `usize` 가 인덱스·길이의 타입인 이유는 **주소 폭과 같아야 하기 때문**이다.

**빈 문자열에 `s.len() - 1`**

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

- 디버그는 **`attempt to subtract with overflow`** 로 패닉한다.
- 릴리스는 **`18446744073709551615`**(= `usize::MAX`)를 돌려준다.
- **릴리스 쪽이 특히 위험한 이유** — 「길이」라는 이름을 단 값이 1844경이 되어 **다음 코드로 흘러간다.**\
  그 값으로 인덱싱하거나 반복 횟수로 쓰면 **엉뚱한 곳에서 터진다.**\
  **틀린 자리와 터지는 자리가 멀어지는 것**이 이 주제에서 가장 비싼 대가다.
- 고치는 법은 `checked_sub(1)` 로 `Option` 을 받거나, `s.len()` 이 0인지를 먼저 보는 것이다.

### 11. 다른 주제와 잇기

**좁히는 변환의 안전한 대안**

```text
300_i32.try_into::<u8>() = Err(TryFromIntError(()))
200_i32.try_into::<u8>() = Ok(200)
u8::try_from(-1_i32)     = Err(TryFromIntError(()))
실패 — Display: out of range integral type conversion attempted / Debug: TryFromIntError(())
```

- **`TryFrom`/`try_into`**(1.34.0부터)이고 **`Result<T, TryFromIntError>`** 를 돌려준다.
- `as` 와의 차이 한 줄: **`as` 는 못 담으면 버리고, `try_into` 는 못 담으면 알려 준다.**
- 실패 값의 `Display` 가 사람이 읽을 문장이다 — `out of range integral type conversion attempted`.

**넓히는 변환**

```text
i32::from(200_u8) = 200
```

- **`From`/`Into`** 를 쓴다. `u8` 의 모든 값이 `i32` 에 들어가므로 **실패가 없다.**\
  그래서 `Result` 가 아니라 값을 그대로 준다.
- 트레이트 자체의 정본은 목록의 **29번 주제**다.

**`"한".len()`**

- **3**이다(UTF-8 바이트 수). 글자 수는 `chars().count()` 로 **1**.
- 정본은 [목록의 **15번 주제**](../15-slices-ranges-and-utf8-boundaries/)(슬라이스·범위 문법·UTF-8 경계)다.

**`()` 가 0바이트인 이유**

- 값이 하나뿐이라 구별할 정보가 없기 때문이다. 정본은 [**04번 주제**](../04-expressions-and-semicolons/)다.

**릴리스에서 오버플로 검사를 켜려면**

```toml
[profile.release]
overflow-checks = true
```

실측 — 이 두 줄을 넣기 전과 후.

```text
--- cargo run --release (기본) ---
x = 250
y = 4

--- overflow-checks = true 를 넣고 다시 ---
x = 250

thread 'main' (1514993) panicked at src/main.rs:1:30:
attempt to add with overflow
```

- `rustc` 쪽 대응은 `-O -C overflow-checks=on` 이다. 「디버그/릴리스」가 아니라 「**검사 켜짐/꺼짐**」이 정확한 축이다.

---

## 실행 검증

| 실험 (`ex.rs`) | 디버그 | 릴리스 `-O` | 문항 |
|---|---|---|---|
| `u8` 250 + 10 (함수 인자) | **패닉** `attempt to add with overflow` · 101 | `y = 4` · 0 | 1 |
| 같은 것, `-C overflow-checks=on` / `off` 교차 | `off` → `y = 4` | `on` → **패닉** | 1 |
| `let x: u8 = 250; let y = x + 10;` | **패닉** | `y = 4` | 1 |
| `let y: u8 = 250 + 10;` | **컴파일 에러** `arithmetic_overflow` | **같은 에러** | 1·8 |
| `checked_/wrapping_/saturating_/overflowing_` 9식 | 표 그대로 | **한 글자도 동일** | 2 |
| 정수 `as` 5식 | `44 255 4294967295 0 -56` | **동일** | 3 |
| 같은 파일 `-W warnings` 진단 줄 수 | **0줄** | — | 3 |
| `cargo clippy`(기본) / `-W cast_possible_truncation` | 안 잡음 / 잡음 | — | 3 |
| 부동→정수 `as` 8식 | 포화 · `NaN -> 0` | **동일** | 4 |
| `i32::MIN / -1` | **패닉** `divide with overflow` | **패닉(동일)** | 5 |
| 같은 것 `-O -C overflow-checks=off` | — | **여전히 패닉** | 5 |
| `10 / 0` | **패닉** `divide by zero` | **패닉(동일)** · `off` 에서도 패닉 | 5 |
| `checked_div`/`wrapping_div`/`saturating_div`/`overflowing_div` | 표 그대로 | — | 5 |
| `size_of`·`align_of` 19종 | 표 그대로 | — | 6 |
| `'a'`·`'한'`·`'🦀'` 의 `as u32` · `"한".len()` | `97` `54620` `129408` · `3` | — | 6 |
| `type_name_of_val` 7종 | `i32` `f64` `char` `&str` … (**관찰**) | — | 7 |
| `let x = 3_000_000_000;` | **컴파일 에러** `literal out of range for i32` | — | 7·8 |
| `54620u32 as char` | **E0604** + `char::from_u32` 권고 | — | 7 |
| `97u8 as char` | `a` | — | 7 |
| `let x: u8 = 300;` | **컴파일 에러** `overflowing_literals` | — | 8 |
| `"".len() - 1` | **패닉** `subtract with overflow` | `18446744073709551615` | 10 |
| `try_into`/`try_from`/`i32::from` 5식 | 표 그대로 | — | 11 |
| `[profile.release] overflow-checks = true` | — | **패닉으로 바뀜** | 11 |
| `{:?}` `{:#?}` `dbg!` | 출력 그대로 · `dbg!` 는 stderr | **`dbg!` 가 그대로 남음** | 2-summary |
| `rustc --explain E0604` | 공식 설명 인용 | — | 7 |

**구현·환경에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **릴리스에서 감싸는 동작** | **구현 재량**(Reference: `at the implementation's discretion`). 보장이 아니다 |
| 패닉 메시지의 괄호 안 번호 | **실행마다 다르다**(세 판 확인). 근거로 읽지 않는다 |
| `size_of::<usize>() == 8` · `&str == 16` | **타깃 플랫폼**(64비트) |
| `(u8, u32) == 8` 의 패딩 배치 | **기본 레이아웃**(`repr(Rust)`)은 필드 순서·패딩을 보장하지 않는다 |
| `type_name_of_val` 의 문자열 | **보장 없음** — std 문서가 명시 |
| `clippy` 린트 이름·기본 수준 | **clippy 버전**(0.1.92) |
| 32비트에서의 `usize` | **못 돌렸다** — 이 머신에 32비트 타깃이 없다. 「안 돌려 봄」이 아니라 「환경이 없어 못 잼」이다 |
