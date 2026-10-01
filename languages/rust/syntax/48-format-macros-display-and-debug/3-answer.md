# rust/syntax/48 — 문자열 포맷 `format!` · `Display`/`Debug` 구현 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `18 / 49` — `P` 의 `{:>8}` 은 **채움 없음** · 문자열 `{:08.3}` 은 `a"b     ` · 정수 `{:08.3}` 은 `00000255`

**출력**

```text
===== 소스: r48_grid.sh =====
# 값 하나 × 지정자 하나마다 프로그램을 만들어 format! 결과를 찍는다 — 컴파일이 안 되면 첫 에러 줄
# 줄바꿈이 든 결과는 ⏎ 로 이어 한 줄에 찍는다
T=$'\t'
prelude='use std::fmt;
#[derive(Debug)]
struct P { x: i32, y: i32 }
impl fmt::Display for P {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}
#[derive(Debug)]
enum E { B { n: u8 } }
#[derive(Debug)]
struct Line { from: P, tags: Vec<&'"'"'static str> }'
values=(
  'P { x: 1, y: 2 }'
  'E::B { n: 1 }'
  'Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }'
  'Some(3)'
  '"a\"b"'
  '3.14159_f64'
  '255_i32'
)
specs=('{}' '{:?}' '{:#?}' '{:>8}' '{:08.3}' '{:x}' '{v}')
printf 'value\tspec\tresult\n'
err=0; total=0
for v in "${values[@]}"; do
  for s in "${specs[@]}"; do
    if [ "$s" = '{v}' ]; then call='format!("{v}")'; else call="format!(\"$s\", v)"; fi
    printf '%s\n#[allow(unused)]\nfn main() {\n    let v = %s;\n    let s = %s;\n    print!("{}", s);\n}\n' "$prelude" "$v" "$call" > c.rs
    if rustc --edition 2021 -o c c.rs 2>err.txt; then
      r="[$(./c | awk 'NR>1{printf "⏎"} {printf "%s", $0}')]"
    else
      r=$(grep -m1 '^error' err.txt); err=$((err+1))
    fi
    row="$v$T$s$T$r"
    n=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
    [ "$n" = 3 ] || { echo "column count $n != 3"; exit 1; }
    printf '%s\n' "$row"
    total=$((total+1))
  done
done
echo "cells that did not compile: $err / $total"
===== bash r48_grid.sh =====
value	spec	result
P { x: 1, y: 2 }	{}	[(1, 2)]
P { x: 1, y: 2 }	{:?}	[P { x: 1, y: 2 }]
P { x: 1, y: 2 }	{:#?}	[P {⏎    x: 1,⏎    y: 2,⏎}]
P { x: 1, y: 2 }	{:>8}	[(1, 2)]
P { x: 1, y: 2 }	{:08.3}	[(1, 2)]
P { x: 1, y: 2 }	{:x}	error[E0277]: the trait bound `P: LowerHex` is not satisfied
P { x: 1, y: 2 }	{v}	[(1, 2)]
E::B { n: 1 }	{}	error[E0277]: `E` doesn't implement `std::fmt::Display`
E::B { n: 1 }	{:?}	[B { n: 1 }]
E::B { n: 1 }	{:#?}	[B {⏎    n: 1,⏎}]
E::B { n: 1 }	{:>8}	error[E0277]: `E` doesn't implement `std::fmt::Display`
E::B { n: 1 }	{:08.3}	error[E0277]: `E` doesn't implement `std::fmt::Display`
E::B { n: 1 }	{:x}	error[E0277]: the trait bound `E: LowerHex` is not satisfied
E::B { n: 1 }	{v}	error[E0277]: `E` doesn't implement `std::fmt::Display`
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{}	error[E0277]: `Line` doesn't implement `std::fmt::Display`
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{:?}	[Line { from: P { x: 0, y: 0 }, tags: ["a"] }]
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{:#?}	[Line {⏎    from: P {⏎        x: 0,⏎        y: 0,⏎    },⏎    tags: [⏎        "a",⏎    ],⏎}]
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{:>8}	error[E0277]: `Line` doesn't implement `std::fmt::Display`
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{:08.3}	error[E0277]: `Line` doesn't implement `std::fmt::Display`
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{:x}	error[E0277]: the trait bound `Line: LowerHex` is not satisfied
Line { from: P { x: 0, y: 0 }, tags: vec!["a"] }	{v}	error[E0277]: `Line` doesn't implement `std::fmt::Display`
Some(3)	{}	error[E0277]: `Option<{integer}>` doesn't implement `std::fmt::Display`
Some(3)	{:?}	[Some(3)]
Some(3)	{:#?}	[Some(⏎    3,⏎)]
Some(3)	{:>8}	error[E0277]: `Option<{integer}>` doesn't implement `std::fmt::Display`
Some(3)	{:08.3}	error[E0277]: `Option<{integer}>` doesn't implement `std::fmt::Display`
Some(3)	{:x}	error[E0277]: the trait bound `Option<{integer}>: LowerHex` is not satisfied
Some(3)	{v}	error[E0277]: `Option<{integer}>` doesn't implement `std::fmt::Display`
"a\"b"	{}	[a"b]
"a\"b"	{:?}	["a\"b"]
"a\"b"	{:#?}	["a\"b"]
"a\"b"	{:>8}	[     a"b]
"a\"b"	{:08.3}	[a"b     ]
"a\"b"	{:x}	error[E0277]: the trait bound `str: LowerHex` is not satisfied
"a\"b"	{v}	[a"b]
3.14159_f64	{}	[3.14159]
3.14159_f64	{:?}	[3.14159]
3.14159_f64	{:#?}	[3.14159]
3.14159_f64	{:>8}	[ 3.14159]
3.14159_f64	{:08.3}	[0003.142]
3.14159_f64	{:x}	error[E0277]: the trait bound `f64: LowerHex` is not satisfied
3.14159_f64	{v}	[3.14159]
255_i32	{}	[255]
255_i32	{:?}	[255]
255_i32	{:#?}	[255]
255_i32	{:>8}	[     255]
255_i32	{:08.3}	[00000255]
255_i32	{:x}	[ff]
255_i32	{v}	[255]
cells that did not compile: 18 / 49
(exit 0)
```

**왜 그런가**

- ★★★ **「컴파일 안 된 칸 18 / 49」 — 전부 E0277** 이다. `{}`·`{:>8}`·`{:08.3}`·`{v}` 는 **`Display`** 를, `{:x}` 는 **`LowerHex`** 를 부르고, 그 트레이트가 없는 값에서 막혔다. 막힌 칸은 **런타임이 아니라 컴파일 시점**이다.
- ★★★ **`P` 의 `{:>8}` → `[(1, 2)]`(채움 없음)** — `P` 의 `Display` 는 `write!(f, "({}, {})", …)` 라 **폭·정렬을 무시한다.** 지정자는 `Formatter` 에 **실려 올 뿐**이고, 적용은 **구현이 한다**(2번). `{:08.3}` 도 같은 이유로 그대로다.
- ★★ **문자열 `{:08.3}` → `[a"b     ]`** — `.3` 은 문자열에서 **최대 폭**(3자로 자름 — 이 값은 딱 3자), `0` 플래그는 **정수용**이라 무시, 폭 8 은 **문자열 기본 정렬(왼쪽)** 으로 공백을 채운다.
- ★★ **정수 `{:08.3}` → `[00000255]`** — **정수에서 정밀도는 무시**되고 `0` 플래그가 0 으로 채운다. **부동소수 `{:08.3}` → `[0003.142]`**(소수점 아래 3자리 + 0 채움).
- ★★ **`{:#?}` 는 줄을 바꾸고 들여쓴다** — 구조체는 필드마다 한 줄, **꼬리 쉼표**까지 찍는다(`y: 2,⏎}`). 원시 값(`f64`·`i32`·`&str`)은 `{:?}` 와 같다.
- ★ **`{v}` 는 `{}` 와 한 칸도 다르지 않다** — 캡처는 **이름을 인자로 넘기는 표기**일 뿐 트레이트가 같다(`E` 등에서 같이 E0277).

### 2. ★★ `[ab]` · `[    ab]` · `[    ab]` · `[a]` — `write!` 는 폭을 버리고 `f.pad` 는 쓴다

**출력**

```text
===== 소스: r48_pad.rs =====
use std::fmt;

struct ViaWrite(&'static str);
struct ViaPad(&'static str);

impl fmt::Display for ViaWrite {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl fmt::Display for ViaPad {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        f.pad(self.0)
    }
}

fn main() {
    println!("[{:>6}]", ViaWrite("ab"));
    println!("[{:>6}]", ViaPad("ab"));
    println!("[{:>6}]", "ab");
    println!("[{:.1}]", ViaPad("ab"));
}
===== rustc --edition 2021 r48_pad.rs =====
(exit 0)
===== ./r48_pad =====
[ab]
[    ab]
[    ab]
[a]
(exit 0)
```

**왜 그런가**

- ★★★ **`write!(f, "{}", self.0)` 는 새 포맷 요청을 만든다** — 바깥의 `{:>6}` 은 `f` 에 실려 왔지만 안쪽 `"{}"` 는 **폭 없는 새 칸**이라 적용되지 않는다(`[ab]`).
- ★★★ **`f.pad(s)` 는 `f` 의 폭·정렬·정밀도를 `s` 에 적용한다** — `&str` 의 `{:>6}` 과 같은 `[    ab]` 가 나왔고, `{:.1}` 은 **최대 폭 1** 로 잘라 `[a]`.
- ★ std 문서 — 「정렬은 **일부 타입에서 구현되지 않을 수 있다** — 특히 `Debug` 는 대개 구현하지 않는다. 패딩을 확실히 하려면 먼저 문자열로 만든 뒤 그것을 채워라」(`format!("{:^15}", format!("{:?}", …))`).

### 3. ★★ `{:?}` 는 따옴표를 두르고 큰따옴표 · 줄바꿈 · 역슬래시를 이스케이프 — `é` 는 그대로, `\u{7}` 은 이스케이프

**출력**

```text
===== 소스: r48_esc.rs =====
fn main() {
    let s = "say \"hi\"\nnext é \\ end";
    println!("{}", s);
    println!("{:?}", s);
    println!("{:?}", '\'');
    println!("{:?}", "\u{7}");
}
===== rustc --edition 2021 r48_esc.rs =====
(exit 0)
===== ./r48_esc =====
say "hi"
next é \ end
"say \"hi\"\nnext é \\ end"
'\''
"\u{7}"
(exit 0)
```

**왜 그런가**

- ★★ **`{}`(Display)는 문자열을 그대로** 내보낸다 — 줄바꿈이 **실제 줄바꿈**이 되어 두 줄이다.
- ★★★ **`{:?}`(Debug)는 「Rust 리터럴처럼」** — 큰따옴표로 두르고 `\"` · `\n` · `\\` 로 적는다. **`é` 는 그대로**(출력 가능한 글자), **벨 문자 `\u{7}` 은 `"\u{7}"`** 로 적힌다. 문자 `'\''` 는 작은따옴표를 이스케이프한다.
- ★ 그래서 **로그에 `{:?}` 로 사용자 입력을 찍으면** 줄바꿈·제어문자가 한 줄 안에 보인다 — 로그 위조(줄 끼워 넣기)를 막는 데 쓸 수 있는 성질이지만, **형식 자체는 안정 보장이 아니다**(9번).

### 4. ★★★ `Error: ConfigError { key: "port" }`(1) · `` error: missing key `port` ``(1) · `Error: "empty input"`(1) — `main` 이 `Err` 를 받으면 **`Debug`**

**출력**

```text
===== 소스: r48_err_q.rs =====
use std::error::Error;
use std::fmt;

#[derive(Debug)]
struct ConfigError {
    key: &'static str,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "missing key `{}`", self.key)
    }
}

impl Error for ConfigError {}

fn load(key: &'static str) -> Result<u16, ConfigError> {
    Err(ConfigError { key })
}

fn main() -> Result<(), Box<dyn Error>> {
    let port = load("port")?;
    println!("port {port}");
    Ok(())
}
===== rustc --edition 2021 r48_err_q.rs =====
(exit 0)
===== ./r48_err_q =====
Error: ConfigError { key: "port" }
(exit 1)
```

```text
===== 소스: r48_err_report.rs =====
use std::error::Error;
use std::fmt;

#[derive(Debug)]
struct ConfigError {
    key: &'static str,
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "missing key `{}`", self.key)
    }
}

impl Error for ConfigError {}

fn load(key: &'static str) -> Result<u16, ConfigError> {
    Err(ConfigError { key })
}

fn run() -> Result<(), Box<dyn Error>> {
    let port = load("port")?;
    println!("port {port}");
    Ok(())
}

fn main() {
    if let Err(e) = run() {
        eprintln!("error: {e}");
        std::process::exit(1);
    }
}
===== rustc --edition 2021 r48_err_report.rs =====
(exit 0)
===== ./r48_err_report =====
error: missing key `port`
(exit 1)
```

```text
===== 소스: r48_err_str.rs =====
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    let input = "";
    if input.is_empty() {
        return Err("empty input".into());
    }
    Ok(())
}
===== rustc --edition 2021 r48_err_str.rs =====
(exit 0)
===== ./r48_err_str =====
Error: "empty input"
(exit 1)
```

**왜 그런가**

- ★★★ **`main` 이 `Err` 를 돌려주면 std 가 `Error: {err:?}` 로 찍는다 — `Display` 가 아니라 `Debug`.** 근거를 std 소스에서 직접 봤다 —

```text
===== sed -e "s/<[^>]*>//g; s/&lt;/</g; s/&gt;/>/g" "$(rustc --print sysroot)/share/doc/rust/html/src/std/process.rs.html" | grep -A8 "Termination for Result<T, E>" | sed -E "s/^[0-9]+//" =====
impl<T: Termination, E: fmt::Debug> Termination for Result<T, E> {
    fn report(self) -> ExitCode {
        match self {
            Ok(val) => val.report(),
            Err(err) => {
                io::attempt_print_to_stderr(format_args_nl!("Error: {err:?}"));
                ExitCode::FAILURE
            }
        }
(exit 0)
```

- ★★★ 그래서 **`?` 로 `Box<dyn Error>` 에 담아 `main` 까지 올리면**, 정성껏 쓴 `Display`(`` missing key `port` ``)가 아니라 **`derive(Debug)` 의 구조체 모양**이 나간다(첫 프로그램). **사람에게 보일 문장을 원하면 `main` 안에서 `{}` 로 찍고 `process::exit(1)`**(둘째 프로그램).
- ★★ **`Err("empty input".into())` 는 `Box<dyn Error>` 안에 `String` 을 담은 것** — 그 `Debug` 가 **따옴표째** `"empty input"` 이다(3번의 문자열 `Debug`).
- ★ 종료 코드는 셋 다 **1**. 같은 사실(`main` 의 `Err` = `Debug`)을 [01번](../01-cargo-crates-and-modules/) 5번(`ParseIntError`)과 [24번](../24-error-type-design/) 6번(손으로 쓴 `Debug`)이 이미 쟀다 — 이 편은 **`Box<dyn Error>` 와 `?` 를 거친 판**과 **문자열 오류**를 더했다.

### 5. ★★ E0599 `` cannot write into `String` `` — `help:` 는 `use std::fmt::Write;` · 가져오면 **`` unused `Result` ``** 경고 뒤 `1-2`

**출력**

```text
===== 소스: r48_write.rs =====
fn main() {
    let mut s = String::new();
    write!(s, "{}-{}", 1, 2);
    println!("{s}");
}
===== rustc --edition 2021 r48_write.rs =====
error[E0599]: cannot write into `String`
 --> r48_write.rs:3:12
  |
3 |     write!(s, "{}-{}", 1, 2);
  |            ^
  |
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/fmt/mod.rs:210:8
  |
  = note: the method is available for `String` here
note: must implement `io::Write`, `fmt::Write`, or have a `write_fmt` method
 --> r48_write.rs:3:12
  |
3 |     write!(s, "{}-{}", 1, 2);
  |            ^
  = help: items from traits can only be used if the trait is in scope
help: trait `Write` which provides `write_fmt` is implemented but not in scope; perhaps you want to import it
  |
1 + use std::fmt::Write;
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

```text
===== 소스: r48_write_ok.rs =====
use std::fmt::Write;

fn main() {
    let mut s = String::new();
    write!(s, "{}-{}", 1, 2);
    println!("{s}");
}
===== rustc --edition 2021 r48_write_ok.rs =====
warning: unused `Result` that must be used
 --> r48_write_ok.rs:5:5
  |
5 |     write!(s, "{}-{}", 1, 2);
  |     ^^^^^^^^^^^^^^^^^^^^^^^^
  |
  = note: this `Result` may be an `Err` variant, which should be handled
  = note: `#[warn(unused_must_use)]` (part of `#[warn(unused)]`) on by default
help: use `let _ = ...` to ignore the resulting value
  |
5 |     let _ = write!(s, "{}-{}", 1, 2);
  |     +++++++

warning: 1 warning emitted

(exit 0)
===== ./r48_write_ok =====
1-2
(exit 0)
```

**왜 그런가**

- ★★★ **`write!` 는 `.write_fmt(..)` 메서드 호출로 펼쳐진다** — `String` 의 `write_fmt` 는 트레이트 **`fmt::Write`** 의 메서드라 **스코프에 들여야** 보인다(`` help: trait `Write` … is implemented but not in scope ``). 진단이 「`io::Write`, `fmt::Write`, 또는 `write_fmt` 메서드」 셋을 후보로 적는다.
- ★★ **`write!` 는 `fmt::Result` 를 돌려준다** — 버리면 `unused_must_use` 경고. `format!` 은 **새 `String` 을 만들어 돌려주고** 실패를 돌려주지 않는다. **이미 있는 버퍼에 이어 쓰려면 `write!`**, 새 문자열이면 `format!`.
- ★ `Display` 구현 안의 `write!(f, …)` 도 같은 매크로다 — 대상이 `Formatter` 이고, `?` 로 올리거나 그대로 돌려준다.

### 6. ★★ `format!("{v}")` 는 **2015 부터** `[7]` — 2015 의 `panic!("{v}")` 만 **`{v}` 를 글자 그대로**

**출력**

```text
===== 소스: r48_capture.rs =====
fn main() {
    let v = 7;
    let s = format!("{v}");
    println!("[{}]", s);
}
===== rustc --edition 2015 -o cap15 r48_capture.rs =====
(exit 0)
===== ./cap15 =====
[7]
(exit 0)
===== rustc --edition 2018 -o cap18 r48_capture.rs =====
(exit 0)
===== ./cap18 =====
[7]
(exit 0)
===== rustc --edition 2021 -o cap21 r48_capture.rs =====
(exit 0)
===== ./cap21 =====
[7]
(exit 0)
```

```text
===== 소스: r48_capture_panic.rs =====
fn main() {
    let v = 7;
    panic!("{v}");
}
===== rustc --edition 2015 -o p15 r48_capture_panic.rs =====
warning: unused variable: `v`
 --> r48_capture_panic.rs:2:9
  |
2 |     let v = 7;
  |         ^
3 |     panic!("{v}");
  |     ------------- you might have meant to use string interpolation in this string literal
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default
help: if this is intentional, prefix it with an underscore
  |
2 |     let _v = 7;
  |         +

warning: panic message contains an unused formatting placeholder
 --> r48_capture_panic.rs:3:13
  |
3 |     panic!("{v}");
  |             ^^^
  |
  = note: this message is not used as a format string when given without arguments, but will be in Rust 2021
  = note: `#[warn(non_fmt_panics)]` (part of `#[warn(rust_2021_compatibility)]`) on by default
help: add the missing argument
  |
3 |     panic!("{v}", ...);
  |                 +++++
help: or add a "{}" format string to use the message literally
  |
3 |     panic!("{}", "{v}");
  |            +++++

warning: 2 warnings emitted

(exit 0)
===== ./p15 =====

thread 'main' (3386479) panicked at r48_capture_panic.rs:3:5:
{v}
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
===== rustc --edition 2018 -o p18 r48_capture_panic.rs =====
warning: unused variable: `v`
 --> r48_capture_panic.rs:2:9
  |
2 |     let v = 7;
  |         ^
3 |     panic!("{v}");
  |     ------------- you might have meant to use string interpolation in this string literal
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default
help: if this is intentional, prefix it with an underscore
  |
2 |     let _v = 7;
  |         +

warning: panic message contains an unused formatting placeholder
 --> r48_capture_panic.rs:3:13
  |
3 |     panic!("{v}");
  |             ^^^
  |
  = note: this message is not used as a format string when given without arguments, but will be in Rust 2021
  = note: `#[warn(non_fmt_panics)]` (part of `#[warn(rust_2021_compatibility)]`) on by default
help: add the missing argument
  |
3 |     panic!("{v}", ...);
  |                 +++++
help: or add a "{}" format string to use the message literally
  |
3 |     panic!("{}", "{v}");
  |            +++++

warning: 2 warnings emitted

(exit 0)
===== ./p18 =====

thread 'main' (3386539) panicked at r48_capture_panic.rs:3:5:
{v}
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
===== rustc --edition 2021 -o p21 r48_capture_panic.rs =====
(exit 0)
===== ./p21 =====

thread 'main' (3386599) panicked at r48_capture_panic.rs:3:5:
7
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
```

**왜 그런가**

- ★★★ **`format!` 의 이름 캡처(`{v}`)는 세 에디션 모두 `[7]`** — 캡처는 **1.58.0 의 기능**이고 에디션과 무관하다. 「`{name}` 캡처는 2021+」는 **`format!` 에 대해서는 틀렸다.** 릴리스 노트가 두 사실을 한 문장에 적었다 —

```text
===== awk '/^Version 1\./{v=$2} /Format strings can now capture/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.58.0 | - [Format strings can now capture arguments simply by writing `{ident}` in the string.][90473] This works in all macros accepting format strings. Support for this in `panic!` (`panic!("{ident}")`) requires the 2021 edition; panic invocations in previous editions that appear to be trying to use this will result in a warning lint about not having the intended effect.
(exit 0)
```

- ★★★ **갈린 것은 `panic!` 이다** — 2015·2018 의 `panic!` 은 **인자가 문자열 하나뿐이면 포맷 문자열로 보지 않는다** → 메시지가 **`{v}` 글자 그대로**. 경고 `non_fmt_panics` 가 「Rust 2021 에서는 포맷 문자열이 된다」고 말하고, 2021 에서는 `7` 이다.
- ★ 이것이 에디션 2021 의 **`panic!` 일관성** 항목이다([`history/rust/02-에디션.md`](../../../../history/rust/02-에디션.md) · [47번](../47-editions-2021-vs-2024-and-cargo-fix/)).

### 7. ★★★ `Debug` 의 독자는 **개발자**라 구조에서 기계적으로 나오고, `Display` 의 독자는 **사람**이라 문장을 고를 사람이 있어야 한다

- ★★★ `Debug` 는 「이 값의 **구조**를 보여 줘라」 — 필드 이름과 값이 곧 답이라 **파생이 한 가지로 정해진다**(1번 `P { x: 1, y: 2 }`). `Display` 는 「이 값을 **사람에게 말하라**」 — `P` 를 `(1, 2)` 로 쓸지 `x=1, y=2` 로 쓸지 **정답이 없다.** 그래서 std 가 파생을 주지 않는다.
- ★★ 1번에서 **`E` · `Line` · `Option<i32>` 가 `{}` 에서 막힌 것**이 그 결과다 — 모두 `Debug` 만 있다. 특히 **`Option<T>` 는 std 타입인데도 `Display` 가 없다** — `None` 을 사람에게 어떻게 말할지 std 가 정하지 않았다.
- ★ E0277 의 `= note:` 가 **`{:?}` (or `{:#?}`)** 를 권한다(서머리 (1)의 전문) — 「사람용이 없으니 개발자용으로라도」.

### 8. ★★ E0117 — 트레이트(`Display`)도 타입(`Vec`)도 남의 것 · newtype 으로 감싸거나 문자열로 만들어 찍는다

```text
===== 소스: r48_orphan.rs =====
use std::fmt;

impl fmt::Display for Vec<i32> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{} items", self.len())
    }
}

fn main() {
    println!("{}", vec![1, 2]);
}
===== rustc --edition 2021 r48_orphan.rs =====
error[E0117]: only traits defined in the current crate can be implemented for types defined outside of the crate
 --> r48_orphan.rs:3:1
  |
3 | impl fmt::Display for Vec<i32> {
  | ^^^^^^^^^^^^^^^^^^^^^^--------
  |                       |
  |                       `Vec` is not defined in the current crate
  |
  = note: impl doesn't have any local type before any uncovered type parameters
  = note: for more information see https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules
  = note: define and implement a trait or new type instead

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0117`.
(exit 1)
```

- ★★★ **고아 규칙** — 「남의 트레이트 × 남의 타입」 한 칸이 막힌다([26번](../26-orphan-rule-and-newtype/)). `Display` 는 std 의 것, `Vec<i32>` 도 std 의 것이다. `note:` 가 처방(「트레이트나 **새 타입**을 정의해 구현하라」)을 적는다.
- ★★ 처방 둘 — ① **newtype** `struct Items(Vec<i32>);` 에 `impl Display` · ② 찍는 자리에서 **문자열로 만든다**(`v.iter().map(…).collect::<Vec<_>>().join(", ")`). 26번이 ①의 대가(안쪽 메서드를 잃는다)를 쟀다.

### 9. ★★ 형식은 **안정 보장이 아니다** — 파생 `Debug` 도, std 타입의 `Debug` 도

- ★★★ std `Debug` 문서 §Stability — 「**파생 `Debug` 형식은 안정적이지 않다** — 앞으로의 Rust 판에서 바뀔 수 있다. std 가 제공하는 타입의 `Debug` 구현도 그렇다」.
- ★★ 그래서 `{:?}` 문자열을 **테스트 기댓값·로그 파싱의 계약**으로 쓰면 컴파일러를 올리는 것만으로 깨질 수 있다. 비교는 **값으로**(`assert_eq!(p, P { … })` — `PartialEq` 는 [27번](../27-derive-macros-debug-clone-partialeq-default-hash/)), 기계가 읽을 출력은 **직접 정한 형식**(`Display` 또는 직렬화)으로.
- ★ 이 판에서 관찰한 형식(`P { x: 1, y: 2 }` · `{:#?}` 의 꼬리 쉼표)은 **관찰**이다.

### 10. ★★ 사람의 문장은 층마다 **`Display`**, 원인은 **`source()`** 로 걸어간다 — `main` 의 `Err` 는 **`Debug` 한 번**뿐이라 사슬이 안 찍힌다

- ★★★ [24번](../24-error-type-design/) — **`Display` 는 자기 층만 말한다.** 원인은 `std::error::Error::source()` 로 **직접 걸어야** 보이고 std 가 대신 찍어 주지 않는다.
- ★★ 4번의 첫 프로그램처럼 `main` 이 돌려주면 **`Error: {err:?}` 한 줄**(std 소스) — `derive(Debug)` 라면 원인이 **필드로** 보일 수는 있어도 **사람의 문장 사슬**은 아니다. 사람에게 보이려면 4번의 둘째 프로그램처럼 `main` 안에서 `{}` 로 찍고 `source()` 를 따라 한 줄씩 덧붙인다.

### 11. ★ `String()` ↔ `Display` · `%#v` ↔ `Debug` · `__str__` ↔ `Display` · `__repr__` ↔ `Debug` — **없을 때**: Rust 는 컴파일 에러, Go 는 기본 형식, Python 은 `__repr__` 으로 떨어진다

| | 사람용 | 개발자용 | 구현이 없으면 |
|---|---|---|---|
| Rust | `Display`(`{}`) | `Debug`(`{:?}` · `{:#?}`) | ★★★ **컴파일 에러 E0277**(1번 18칸) |
| Go([42번](../../../go/syntax/42-fmt-verbs-stringer-and-errorf/)) | `String()` — `%v`·`%s` 에서 불린다 | `%#v`(Go 문법 모양) — `String()` 을 **안 부른다** | 기본 형식으로 찍힌다 · **틀린 동사도 실행 중 `%!d(string=hi)` 글자로만** 남는다 |
| Python([30번](../../../python/syntax/30-repr-eq-hash-contracts/) · [08번](../../../python/syntax/08-fstrings-and-format-spec/)) | `__str__` | `__repr__` | `__str__` 없으면 **`__repr__`**, 그것도 없으면 `<… object at 0x…>` |

- ★★ **Rust 만 「없음」을 컴파일 시점에 막는다** — 지정자가 곧 트레이트 경계라서다(1번). Go 는 **`vet`** 이 상수 서식 문자열만 검사하고(Go 42번), Python 은 기본값으로 **조용히** 채운다.
- ★ Python 08번 — f-string 의 `{p}` 는 `__str__` 이 아니라 **`__format__`** 을 부른다. Rust 의 `{}` 는 **`Display::fmt`** 를 부르고, 폭·정렬은 그 구현이 `f.pad` 등으로 **직접 적용해야** 한다(2번) — 둘 다 「포맷 스펙은 값 쪽이 해석한다」는 같은 모양이다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(패닉 스레드 id 가 걸린다) · **고칠 것 0** |
| ★★★ **포맷 격자** | `r48_grid.sh` — 일곱 값 × 일곱 지정자, 칸마다 프로그램을 만들어 컴파일·실행(탭 구분 · 칸 수 검사 · 줄바꿈은 `⏎`) | 49 | **`18 / 49`**(전부 E0277) |
| 폭과 `pad` | `r48_pad` | 1 | `[ab]` 대 `[    ab]` |
| 이스케이프 | `r48_esc` | 1 | `\"` · `\n` · `\\` · `é` · `\u{7}` |
| ★★ **`main` 의 `Err`** | `r48_err_q` · `r48_err_report` · `r48_err_str` + std 소스 `r48_termination` | 4 | **`Debug`** · `Display` · `"empty input"` · `Error: {err:?}` |
| `write!` | `r48_write` · `r48_write_ok` | 2 | E0599 · 경고 + `1-2` |
| 캡처와 에디션 | `r48_capture`(2015·2018·2021) · `r48_capture_panic`(2015·2021) | 5 | `[7]` × 3 · `{v}` 대 `7` |
| 고아 규칙 | `r48_orphan` | 1 | E0117 |
| **안 던진 것** — `{:#x}`·`{:+}`·`{:e}` · `{:1$}` 폭 인자 · `f.alternate()` · `f.debug_struct()` 손 구현 · `Formatter` 의 `sign_plus` 등 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| 파생 `Debug` 의 형식(`P { x: 1, y: 2 }` · `{:#?}` 의 꼬리 쉼표) · std 타입의 `Debug` | ★ std 문서가 **안정이 아니라고** 적었다 |
| `main` 의 `Err` 가 `Error: {err:?}` 로 찍힌다 | ★ std 의 `Termination` 구현(이 판의 소스) |
| 진단 문구(`cannot write into` · `help:` 후보) | ★ rustc 판 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.

## 실행 환경

이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
블록 배너의 명령(기본 `rustc --edition 2021`, 에디션 비교는 `2015`·`2018`)으로 실제로 돌려 받은 것이다.\
★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다(격자가 만드는 `c.rs` 는 스크립트 안에서 생긴다).\
★ 패닉 첫 줄의 `thread 'main' (NNN)` 은 **실행마다 바뀌는 칸**이다(서머리 맨 위 부분의 표).
