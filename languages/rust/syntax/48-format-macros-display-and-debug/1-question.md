# rust/syntax/48 — 문자열 포맷 `format!` · `Display`/`Debug` 구현 — 질문

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 일곱 값 × 일곱 지정자 (예측)

```bash
# r48_grid.sh
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
```

- 마흔아홉 행의 셋째 칸(`[결과]` 또는 첫 `error` 줄)을 채워라. 마지막 줄의 `N / 49` 는? 특히 `P` 의 `{:>8}` 칸, 문자열의 `{:08.3}` 칸, 정수의 `{:08.3}` 칸은?

### 2. ★★ 폭을 준 두 `Display` (예측)

```rust
// r48_pad.rs
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
```

- 네 줄의 출력은? 두 구현은 무엇이 달라서 첫 두 줄이 갈리나?

### 3. ★★ 한 문자열을 `{}` 와 `{:?}` 로 (예측)

```rust
// r48_esc.rs
fn main() {
    let s = "say \"hi\"\nnext é \\ end";
    println!("{}", s);
    println!("{:?}", s);
    println!("{:?}", '\'');
    println!("{:?}", "\u{7}");
}
```

- 출력은? `é` 와 `\u{7}` 은 `{:?}` 에서 각각 어떻게 찍히나?

### 4. ★★★ `main` 이 돌려준 오류와 직접 찍은 오류 (예측)

```rust
// r48_err_q.rs
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
```

```rust
// r48_err_report.rs
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
```

```rust
// r48_err_str.rs
use std::error::Error;

fn main() -> Result<(), Box<dyn Error>> {
    let input = "";
    if input.is_empty() {
        return Err("empty input".into());
    }
    Ok(())
}
```

- 세 프로그램의 표준 오류와 종료 코드는? 같은 `ConfigError` 인데 앞의 둘이 **다른 문장**을 찍는다면 무엇이 그것을 가르나?

### 5. ★★ `format!` 말고 `write!` 로 `String` 에 (예측)

```rust
// r48_write.rs
fn main() {
    let mut s = String::new();
    write!(s, "{}-{}", 1, 2);
    println!("{s}");
}
```

```rust
// r48_write_ok.rs
use std::fmt::Write;

fn main() {
    let mut s = String::new();
    write!(s, "{}-{}", 1, 2);
    println!("{s}");
}
```

- 앞 소스는 컴파일되나? 에러라면 번호와 `help:` 는? 뒤 소스는 출력 전에 무엇을 경고하나?

### 6. ★★ 변수 이름을 자리표시자에 — 세 에디션 (예측)

```rust
// r48_capture.rs
fn main() {
    let v = 7;
    let s = format!("{v}");
    println!("[{}]", s);
}
```

```rust
// r48_capture_panic.rs
fn main() {
    let v = 7;
    panic!("{v}");
}
```

- `r48_capture.rs` 를 2015 · 2018 · 2021 로 각각 던지면 출력은? `r48_capture_panic.rs` 를 2015 · 2018 · 2021 로 던지면 패닉 메시지 줄은 각각 무엇인가?

### 7. ★★★ `Debug` 는 `derive` 되는데 `Display` 는 왜 안 되나 (왜)

- `#[derive(Display)]` 가 표준에 없는 이유를 두 트레이트의 **독자**로 설명하라. 1번에서 `E` · `Line` · `Option` 이 `{}` 에서 막힌 것은 그와 어떻게 이어지나?

### 8. ★★ 남의 타입에 `Display` (경계)

- `impl fmt::Display for Vec<i32>` 를 쓰면 무엇이 막나(번호)? [26번](../26-orphan-rule-and-newtype/)의 규칙으로 설명하고, `Vec<i32>` 를 사람에게 읽히려면 어떻게 하나?

### 9. ★★ `{:?}` 의 출력을 파싱해도 되나 (경계)

- `derive(Debug)` 가 만든 문자열(예 — `P { x: 1, y: 2 }`)을 로그 파싱·테스트 기댓값으로 쓰면 무엇이 위험한가? std 문서는 그 형식에 대해 무엇을 약속하고 무엇을 약속하지 않나?

### 10. ★★ 오류 타입의 두 얼굴과 사슬 (연결)

- [24번](../24-error-type-design/)은 「`Display` 는 **자기 층만** 말한다」고 했다. 4번의 `ConfigError` 가 다른 오류를 **원인으로** 품는다면, 사람에게 보일 문장은 무엇으로 만들고 원인은 무엇으로 걸어가나? `main` 이 `Err` 를 돌려줄 때 그 사슬이 찍히나?

### 11. ★ `%v` · `%+v` · `%#v` 와 `__str__` · `__repr__` (연결)

- Go([42번](../../../go/syntax/42-fmt-verbs-stringer-and-errorf/))의 `String()` 메서드와 `%v`/`%#v`, Python([30번](../../../python/syntax/30-repr-eq-hash-contracts/) · [08번](../../../python/syntax/08-fstrings-and-format-spec/))의 `__str__`/`__repr__` 은 Rust 의 `Display`/`Debug` 와 각각 어떻게 짝이 되나? **구현이 없을 때** 셋은 각각 무엇을 하나(컴파일 에러 · 기본 출력)?

## 실행 환경

★ 던지는 법 — `rustc --edition 2021 <파일>.rs`(에디션 비교는 `2015`·`2018`). 격자는 `bash <파일>.sh`. **외부 크레이트를 하나도 쓰지 않는다.**
★★★ **자리표시자를 보면 먼저 물어라** — 「**이 칸은 어느 트레이트를 부르나**」(`{}` = `Display` · `{:?}` = `Debug` · `{:x}` = `LowerHex` …)와 「**폭·채움은 누가 적용하나**」.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
