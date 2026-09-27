# rust/syntax/48 — 문자열 포맷 `format!` · `Display`/`Debug` 구현 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::fmt`](https://doc.rust-lang.org/std/fmt/index.html)(지정자 문법 · 「정렬은 일부 타입에서 구현되지 않을 수 있다 — 특히 `Debug`」 · 정밀도 「문자열은 최대 폭 · 정수는 무시 · 부동소수는 소수점 아래 자리」 · `0` 플래그는 정수용) ·
> [std — `Debug`](https://doc.rust-lang.org/std/fmt/trait.Debug.html)(§Stability 「**파생 `Debug` 형식은 안정적이지 않다**」) · [std — `Formatter::pad`](https://doc.rust-lang.org/std/fmt/struct.Formatter.html#method.pad) ·
> std 소스 `process.rs` 의 `impl Termination for Result<T, E>`(`Error: {err:?}` — 아래 블록) · 릴리스 노트 1.58.0(이름 캡처 — 아래 블록).
> ★ 전부 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> 블록 배너의 명령(기본 **`rustc --edition 2021`**, 에디션 비교는 `2015`·`2018`)으로 돌려 받은 것이다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★ **속도·할당은 재지 않았다** — `format!` 이 `write!` 보다 비싸다는 식의 말은 이 문서에 없다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ⑩ 포맷 격자(값 일곱 × 지정자 일곱 → 찍힌 글자 · 안 되면 컴파일 에러)다.** 지정자는 **어느 트레이트를 부를지**를 정하므로 「안 되는 칸」은 런타임이 아니라 **컴파일러**가 말하고, 「되는 칸」은 **찍힌 글자**가 말한다 — 한 격자가 두 창을 겸한다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread 'main' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| 안 흔들린다 | ★★★ **격자의 결과 칸과 「컴파일 안 된 칸 18 / 49」** | 같은 판에서 고정이다 — **이 주제의 본체** |
| 안 흔들린다 | E0277 · E0599 · E0117 번호 · `파일:줄:칸` · 종료 코드(`1` · `101`) | 같은 판에서 고정이다 |
| ★ **판이 정한다** | **파생 `Debug` 의 모양**(`P { x: 1, y: 2 }` · `{:#?}` 의 꼬리 쉼표) · std 타입의 `Debug` | ★ std 문서가 **안정이 아니라고** 적었다 — 판이 오르면 바뀔 수 있다 |

★ 정규화 규칙은 **기본 넷**만 쓴다(패닉 스레드 id 가 걸린다).

## 한눈에 — 쉽게 말하면

**`{}` 와 `{:?}` 는 「안내 방송」과 「정비 기록부」다.** 같은 비행기(값)라도 승객에게는 「3번 게이트에서 탑승합니다」(`Display`)라고 말하고, 정비사에게는 부품 목록을 그대로 적는다(`Debug`).
정비 기록부는 양식이 정해져 있어 **자동으로 채울 수 있지만**(`derive(Debug)`), 안내 방송은 **누군가 문장을 써야** 한다 — 그래서 `Display` 는 파생이 없다.
`{:>8}` 같은 칸 맞춤은 **방송 원고에 붙은 메모**일 뿐, 방송하는 사람이 **읽고 지켜야** 적용된다(`f.pad`). 무시하고 읽으면(`write!`) 메모는 버려진다.

| 비유 | 실체 |
|---|---|
| 「**안내 방송 / 정비 기록부**」 | ★★★ **`{}` = `Display`(사람) · `{:?}`·`{:#?}` = `Debug`(개발자)** — 없으면 **컴파일 에러 E0277**((1)) |
| 「**기록부는 자동, 방송은 사람이**」 | ★★★ **`derive(Debug)` 는 있고 `derive(Display)` 는 없다** — `Option` 도 `Display` 가 없다((1)) |
| 「**원고에 붙은 칸 맞춤 메모**」 | ★★★ **`{:>8}` 은 `Formatter` 에 실려 올 뿐** — `write!` 로 쓰면 버려지고 `f.pad` 로 쓰면 적용된다((2)) |
| 「**기록부는 따옴표·특수기호를 그대로 적는다**」 | ★★ **`{:?}` 는 문자열을 `"…"` 로 두르고 `\n`·`\"` 로 이스케이프**((3)) |
| 「**비행기가 멈추면 정비 기록부가 나간다**」 | ★★★ **`main` 이 `Err` 를 돌려주면 `Debug` 가 찍힌다** — `Display` 가 아니다((4)) |
| 「**기록부 양식은 개정될 수 있다**」 | ★★ **파생 `Debug` 형식은 안정 보장이 아니다**((5)) |

```text
   지정자가 부르는 트레이트 — 없으면 컴파일 에러 (1)의 18칸

   {}  {v}  {:>8}  {:08.3}      ──▶  Display::fmt     ← 사람용 · derive 없음
   {:?}  {:#?}                   ──▶  Debug::fmt       ← 개발자용 · #[derive(Debug)]
   {:x}                          ──▶  LowerHex::fmt    ← 정수만
                   │
                   └ 폭 · 채움 · 정밀도는 Formatter 에 실려 간다 → 적용은 구현의 몫 (f.pad) (2)
```

> **`Display`** — 사람에게 보일 문장을 만드는 트레이트. `{}` 가 부른다. **직접 구현해야** 한다.\
> 예: `impl fmt::Display for P { fn fmt(&self, f) -> fmt::Result { write!(f, "({}, {})", self.x, self.y) } }`.

> **`Debug`** — 개발자가 값의 구조를 보는 트레이트. `{:?}`(한 줄) · `{:#?}`(여러 줄)가 부른다. `#[derive(Debug)]` 로 만든다.\
> 예: `#[derive(Debug)] struct P { x: i32, y: i32 }` → `P { x: 1, y: 2 }`.

## 이 주제가 답하려는 질문

1. ★★★ **어떤 값에 어떤 지정자를 쓸 수 있나 — 안 되면 무엇이 막나**((1)).
2. ★★★ **`Display` 를 직접 쓸 때 무엇을 지켜야 하나 — 폭·정렬은 누가 적용하나**((2)).
3. ★★ **오류 타입을 사람이 읽게 하려면 — `main` 이 무엇을 찍나**((4)).

★ **선행** — [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/) — **`derive(Debug)` 가 필드에 요구하는 것** · **`{:?}` 와 `{:#?}` 의 두 얼굴**(그 편 (2)) · 「trait 이 없다」 에러 셋(E0369·E0599·E0277).
★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
[01번](../01-cargo-crates-and-modules/) 5번 — **`fn main` 의 `Err` 는 `Debug` 로 표준 오류에 찍히고 종료 코드 1**(`ParseIntError { kind: InvalidDigit }`) ·
[24번](../24-error-type-design/) 6번 — **손으로 쓴 `Debug` 가 찍히고 `Display` 는 안 쓰인다** · 「`Display` 는 자기 층만 · 원인은 `source()`」 ·
[26번](../26-orphan-rule-and-newtype/) — **E0117 전문이 규칙 그 자체** · newtype 의 대가.
이 편은 그 위에 **일곱 × 일곱 포맷 격자**, **폭을 무시하는 `Display`**, **`{:?}` 의 이스케이프**, **`?` → `Box<dyn Error>` → `main` 의 판**, **`write!` 의 트레이트**, **캡처와 에디션**을 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ⑩ 포맷 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ⑩ ★★★ **포맷 격자**(칸마다 프로그램을 만들어 컴파일·실행) | 찍힌 글자 **또는** 막은 트레이트 | ★ **본체**((1)) |
| ② ★★ **컴파일러 진단** E0277 · E0599 · E0117 | 없는 트레이트 · 스코프에 없는 트레이트 · 고아 규칙 | 쓴다((1)·(3)·(5)) |
| ⑪ ★★ **std 소스 · 릴리스 노트**(로컬 사본) | `main` 이 **어느 지정자로** 찍나 · 캡처가 **언제부터**인가 | 쓴다((4)·(3)) — ★ 출력만으로는 「왜 `Debug` 인가」가 안 보여서 **창을 바꿔** 물었다 |
| 실행 시간 · 할당 수 | — | ★ **부적용** — 이 주제의 질문(무엇이 찍히나 · 무엇이 막히나)에 시간이 답하지 않는다. 비용 주장도 하지 않는다 |
| `{:?}` 의 필드 조건 · 제네릭 경계 | — | ★ **이미 잰 것** — 27번 (3)·(5) |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「`main` 은 왜 `Display` 를 안 쓰나」를 실행 출력(①)으로만 물으면 **「그렇게 찍혔다」까지**다. std 소스(⑪)에 물으니 **`Error: {err:?}` 한 줄**이 답했다 — 경계가 `E: fmt::Debug` 라서 `Display` 는 **요구조차 되지 않는다.**

### (1) ★★★ 일곱 값 × 일곱 지정자 — 마흔아홉 칸

**언제 쓰나** — 로그·메시지를 찍을 때마다. **「이 값에 이 지정자가 되나」를 칸으로 본다.**

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

- ★★★ **「컴파일 안 된 칸 18 / 49」 — 전부 E0277.** `Display` 가 없는 `E`·`Line`·`Option` 이 `{}`·`{:>8}`·`{:08.3}`·`{v}` 에서, `LowerHex` 가 없는 여섯 값이 `{:x}` 에서 막혔다(`i32` 만 `ff`).
- ★★★ **`P` 의 `{:>8}`·`{:08.3}` 은 그대로 `(1, 2)`** — 막히지는 않았는데 **지정자가 무시됐다**((2)). 컴파일러는 「`Display` 가 있나」만 보고, **폭을 지키는지는 안 본다.**
- ★★ **정밀도의 세 얼굴** — 문자열 `{:08.3}` → `a"b     `(최대 폭 3 · `0` 플래그 무시 · 왼쪽 정렬) · 정수 → `00000255`(정밀도 무시) · 부동소수 → `0003.142`(소수점 아래 3). std 문서의 서술 그대로다.
- ★★ **`{:#?}` 는 필드마다 줄을 바꾸고 꼬리 쉼표**를 찍는다(`⏎` 가 줄바꿈 자리). 원시 값에서는 `{:?}` 와 같다.
- ★ **`{v}`(이름 캡처)는 `{}` 와 모든 칸이 같다** — 표기만 다르다.

**E0277 의 전문.**

```text
===== 소스: r48_e0277.rs =====
#[derive(Debug)]
enum E {
    B { n: u8 },
}

fn main() {
    let v = E::B { n: 1 };
    println!("{}", v);
}
===== rustc --edition 2021 r48_e0277.rs =====
error[E0277]: `E` doesn't implement `std::fmt::Display`
 --> r48_e0277.rs:8:20
  |
8 |     println!("{}", v);
  |               --   ^ `E` cannot be formatted with the default formatter
  |               |
  |               required by this formatting parameter
  |
help: the trait `std::fmt::Display` is not implemented for `E`
 --> r48_e0277.rs:2:1
  |
2 | enum E {
  | ^^^^^^
  = note: in format strings you may be able to use `{:?}` (or {:#?} for pretty-print) instead
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ `required by this formatting parameter` 가 **`{}` 칸을** 짚고, `= note:` 가 **`{:?}` (or `{:#?}`)** 를 권한다 — 「사람용이 없으니 개발자용으로라도」.

### (2) ★★★ 폭은 `Formatter` 에 실려 올 뿐 — 적용은 구현의 몫

**언제 쓰나** — `Display` 를 직접 쓸 때. 특히 **표 모양 출력**(`{:>10}`)에 내 타입을 넣을 때.

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

- ★★★ **`write!(f, "{}", self.0)` → `[ab]`(폭 무시) · `f.pad(self.0)` → `[    ab]`(적용)** — `write!` 는 **안쪽에 새 칸(`"{}"`)을 만들어** 바깥의 폭을 잃는다. `f.pad` 는 **`f` 의 폭·정렬·정밀도를 그 문자열에** 적용한다(`{:.1}` → `[a]`).
- ★★ 여러 조각으로 된 출력이라면 **먼저 `String` 으로 만든 뒤 `f.pad(&s)`** — std 문서도 「패딩을 확실히 하려면 먼저 문자열로 만든 뒤 채워라」고 적는다.

### (3) ★★ `{:?}` 는 문자열을 「리터럴처럼」 — 그리고 `write!` 와 캡처

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

- ★★ **`{}` 는 그대로(줄바꿈이 실제로 난다) · `{:?}` 는 `"…"` 로 두르고 `\"` · `\n` · `\\` 로** — `é` 는 그대로, 벨 문자는 `\u{7}`.

**`write!` 는 트레이트 메서드다.**

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

- ★★★ **E0599 `` cannot write into `String` ``** — `write!` 가 펼쳐지는 `.write_fmt()` 는 **`fmt::Write`** 의 메서드라 `use std::fmt::Write;` 가 있어야 보인다. 가져오면 **`fmt::Result` 를 버리지 말라**는 경고가 따라온다(3-answer 5번).

**이름 캡처와 에디션.**

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
===== awk '/^Version 1\./{v=$2} /Format strings can now capture/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.58.0 | - [Format strings can now capture arguments simply by writing `{ident}` in the string.][90473] This works in all macros accepting format strings. Support for this in `panic!` (`panic!("{ident}")`) requires the 2021 edition; panic invocations in previous editions that appear to be trying to use this will result in a warning lint about not having the intended effect.
(exit 0)
```

- ★★★ **`format!("{v}")` 는 2015 부터 `[7]`** — 캡처는 **1.58.0** 의 기능이고 **모든 포맷 매크로**에서 된다. 에디션을 타는 것은 **`panic!("{v}")` 하나**다(2021 이전의 `panic!` 은 인자가 하나면 포맷 문자열로 보지 않는다 — 3-answer 6번의 블록).

### (4) ★★★ 오류 타입 — `Display` + `Error`, 그리고 `main` 이 찍는 것은 `Debug`

**언제 쓰나** — 오류를 사람에게 보여 줄 때. 특히 **`main` 에서 `?` 로 올려 끝낼 때.**

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

- ★★★ **같은 `ConfigError` 인데 첫 판은 `Error: ConfigError { key: "port" }`(Debug), 둘째 판은 `` error: missing key `port` ``(Display).** 가른 것은 **누가 찍었나**다 — `main` 이 `Err` 를 돌려주면 **std 가**, `main` 안에서 `eprintln!("{e}")` 하면 **내가.**

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

- ★★★ **std 의 `Termination for Result<T, E>` 는 `E: fmt::Debug` 만 요구하고 `Error: {err:?}` 로 찍는다** — `Display` 는 **요구조차 안 된다.**

```text
   오류가 사람에게 닿는 두 길

   fn main() -> Result<(), Box<dyn Error>>        fn main() { if let Err(e) = run() { … } }
          │  load()? 가 ConfigError 를 Box 에 담아 올린다     │
          ▼                                                   ▼
   std: eprintln!("Error: {err:?}")               내가: eprintln!("error: {e}") + exit(1)
          │  Debug                                           │  Display
          ▼                                                   ▼
   Error: ConfigError { key: "port" }             error: missing key `port`
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

- ★★ **`Err("empty input".into())` 는 `Box<dyn Error>` 안의 `String`** — `Debug` 라 **따옴표째** `"empty input"`.

### (5) ★★ 경계 — 남의 타입에 `Display`, 그리고 `Debug` 형식의 안정성

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

- ★★ **E0117** — `Display`(std)도 `Vec`(std)도 남의 것([26번](../26-orphan-rule-and-newtype/)). **newtype** 으로 감싸거나 찍는 자리에서 문자열을 만든다.
- ★★★ **std `Debug` §Stability — 「파생 `Debug` 형식은 안정적이지 않다. std 타입의 `Debug` 구현도」.** `{:?}` 문자열을 **테스트 기댓값·파싱 대상**으로 쓰지 않는다 — 비교는 값(`PartialEq`)으로, 기계용 출력은 직접 정한 형식으로.

## 문법 — 형태와 규칙

```text
   {}        Display          {:?}   Debug (한 줄)        {:#?}  Debug (여러 줄)
   {:x}      LowerHex         {:X}   UpperHex             {:b} {:o} {:e}  (이 편은 x 만 던졌다)
   {:>8}     폭 8 · 오른쪽     {:<8}  왼쪽                  {:^8}  가운데
   {:08}     0 채움 (정수·부동소수)                          {:.3}  정밀도 — 문자열 최대 폭 · 정수 무시 · 부동소수 소수점 아래
   {v}  {v:?}  {v:>8}          이름 캡처 (1.58.0 · 모든 에디션의 format!)

   impl fmt::Display for T { fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result { … } }
       write!(f, "…", …)        ← 폭·정렬을 적용하지 않는다
       f.pad(&s)                ← f 의 폭·정렬·정밀도를 s 에 적용한다
   impl std::error::Error for T {}   ← Display + Debug 가 있어야 달 수 있다
```

- ★★★ **지정자 = 트레이트 경계** — 없으면 E0277((1)).
- ★★★ **폭·정렬은 구현이 적용한다**((2)).
- ★★★ **`main` 의 `Err` 는 `Debug`**((4)).
- ★★ **`write!` 는 `fmt::Write`(또는 `io::Write`)를 들여야 하고 `Result` 를 돌려준다**((3)).

## 어디서 틀리나

### 1. ★★★ 「`Display` 를 구현했으니 `{:>10}` 도 된다」

(2) — **`write!` 로 쓰면 폭이 무시된다**(에러도 경고도 없다). `f.pad` 로.

### 2. ★★★ 「`main` 이 `Err` 를 돌려주면 내 `Display` 문장이 나간다」

(4) — **`Debug`** 가 나간다. 사람용 문장은 `main` 안에서 `{}` 로 찍고 `exit(1)`, 또는 `Debug` 를 `Display` 에 위임하도록 **손으로** 쓴다(24번 6번).

### 3. ★★ 「`Option` 은 std 타입이니 `{}` 로 찍힌다」

(1) — **`Display` 가 없다**(E0277). `{:?}` 또는 `match`/`unwrap_or` 로 사람용 값을 고른다.

### 4. ★★ 「`{:08.3}` 은 어디서나 같은 뜻」

(1) — **문자열은 잘라 공백 채움 · 정수는 정밀도 무시 · 부동소수는 소수점 아래.**

### 5. ★★ 「`{name}` 캡처는 2021 에디션부터」

(3) — **`format!` 은 1.58.0 부터 모든 에디션.** 에디션을 타는 것은 **`panic!` 의 한 인자 꼴**뿐이다.

### 6. ★ 「`{:?}` 출력으로 테스트를 짜면 된다」

(5) — **형식이 안정 보장이 아니다.**

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 지정자가 부르는 트레이트 · 없으면 컴파일 에러 | ★ **std 의 `format_args!` 계약**(컴파일러 내장 매크로) | (1) |
| 정밀도·`0` 플래그의 타입별 뜻 | ★ **std 문서**(`std::fmt`) | (1) |
| 폭·정렬을 적용하는 것은 구현(`f.pad`) | ★ **std 문서** — 「일부 타입은 정렬을 구현하지 않을 수 있다」 | (2) |
| 파생 `Debug` 의 모양 · std 타입의 `Debug` | ★ **보장되지 않는다**(std `Debug` §Stability) — 이 판의 관찰 | (1)·(5) |
| `main` 의 `Err` → `Error: {err:?}` · 종료 코드 1 | ★ **std 의 `Termination` 구현**(이 판의 소스) | (4) |
| 이름 캡처 1.58.0 · `panic!` 만 2021 | ★ **릴리스 노트 + 에디션** | (3) |
| 고아 규칙 E0117 | ★ **언어** | (5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 개발자가 값을 들여다본다(디버그 로그) | **`{:?}`**, 구조가 크면 **`{:#?}`** — `#[derive(Debug)]` | (1) |
| 사용자에게 보일 메시지 | **`impl Display`** — `{}` | (1)·(4) |
| 내 타입을 표 모양으로 맞춘다 | **`Display` 안에서 `f.pad`**(조각이 여럿이면 `String` 을 만든 뒤) | (2) |
| 이미 있는 `String` 에 이어 쓴다 | **`write!`** + `use std::fmt::Write` | (3) |
| 새 문자열 | **`format!`** | (3) |
| 오류 타입 | **`Display` + `Debug` + `impl Error`** — `main` 에서 사람에게 보이려면 **직접 `{}`** | (4) |
| 남의 타입을 사람용으로 | **newtype + `Display`** 또는 찍는 자리에서 조립 | (5) |
| 테스트 기댓값 | **값 비교**(`assert_eq!`) — `{:?}` 문자열 비교는 피한다 | (5) |

## 핵심 문장

- ★★★ **지정자는 트레이트를 고른다 — `{}` 는 `Display`, `{:?}` 는 `Debug` — 없으면 컴파일 에러다(49칸 중 18칸이 E0277).**
- ★★★ **`Display` 는 파생이 없다 — 사람에게 할 말은 사람이 정한다. `Option` 도 `Display` 가 없다.**
- ★★★ **폭·정렬은 `Formatter` 에 실려 올 뿐 — `write!` 로 쓰면 버려지고 `f.pad` 로 쓰면 적용된다.**
- ★★★ **`main` 이 `Err` 를 돌려주면 std 가 `Error: {err:?}` — `Debug` 를 찍는다. 사람용 문장은 직접 찍어야 한다.**
- ★★ **파생 `Debug` 의 모양은 안정 보장이 아니다 — `{:?}` 로 테스트하지 않는다.**

## 관련 자료

- [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/) — `derive(Debug)` 의 요구 · `{:?}`/`{:#?}`. **그쪽은 「`Debug` 를 얻는 법」, 여기는 「지정자 전체와 `Display` 를 쓰는 법」.**
- [**24번 주제**](../24-error-type-design/) — 오류 타입의 네 표면 · `source()` 사슬. 여기는 **찍히는 표면**만.
- [**01번 주제**](../01-cargo-crates-and-modules/) 5번 — `main` 의 `Err` 첫 실측.
- [**26번 주제**](../26-orphan-rule-and-newtype/) — E0117 · newtype.
- [**47번 주제**](../47-editions-2021-vs-2024-and-cargo-fix/) — 에디션이 가르는 자리(`panic!` 일관성은 2021 항목).
- Go 갈래 [`42-fmt-verbs-stringer-and-errorf`](../../../go/syntax/42-fmt-verbs-stringer-and-errorf/) — `String()` 이 불리는 동사 · **틀린 동사가 실행 중 글자(`%!d(…)`)로 남는다** — Rust 는 컴파일 에러다.
- Python 갈래 [`08-fstrings-and-format-spec`](../../../python/syntax/08-fstrings-and-format-spec/) · [`30-repr-eq-hash-contracts`](../../../python/syntax/30-repr-eq-hash-contracts/) — `__format__`·`__str__`·`__repr__` — **없으면 기본값으로 조용히** 채운다.

## 용어 풀이

- **`format!` / `write!` / `println!`** — 포맷 문자열을 받는 매크로. 새 `String` / 버퍼에 쓰기 / 표준 출력.
- **지정자(format spec)** — `{` `}` 안의 `:` 뒤 — 채움·정렬·폭·정밀도·타입(`?`·`x`…).
- **`Formatter`** — `fmt` 가 받는 인자. 출력 대상 + 지정자(폭·정렬·정밀도·플래그)를 싣고 온다.
- **`f.pad`** — `Formatter` 의 지정자를 문자열에 적용해 쓰는 메서드.
- **이름 캡처** — `{v}` 가 스코프의 변수 `v` 를 인자로 쓰는 것(1.58.0).
- **`Termination`** — `main` 의 반환 타입이 구현하는 트레이트. `Result` 판은 `Err` 를 `Debug` 로 찍고 실패 코드를 낸다.
- **E0277** — 요구된 트레이트가 없다. **E0599** — 그 메서드가 안 보인다(트레이트가 스코프에 없음 포함). **E0117** — 고아 규칙.

## 더 들어가면

- `f.debug_struct("P").field("x", &self.x).finish()` — `Debug` 를 손으로 쓰되 파생과 같은 모양(그리고 `{:#?}` 지원)을 얻는 빌더. **던지지 않았다.**
- `f.alternate()`(`{:#}` 의 `#`) · `f.width()`/`f.precision()` 을 읽어 직접 분기하기 — **던지지 않았다.**
- `{:1$}`·`{:.*}` 처럼 폭·정밀도를 인자로 받기 · `{:+}`·`{:#x}`·`{:e}` — **던지지 않았다.**
