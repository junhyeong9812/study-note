# rust/syntax/33 — `dyn Trait` 트레이트 객체와 객체 안전성 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`dyn` 을 보면 두 가지를 먼저 물어라** — 「**포인터에 무엇이 붙어 다니나**」와 「**이 트레이트의 모든 항목이 vtable 한 칸에 들어가나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 포인터 하나의 크기 (예측)

```rust
// r33_size.rs
// 포인터 하나의 크기 — 가리키는 타입에 따라
use std::fmt::Display;
use std::mem::{align_of_val, size_of, size_of_val};

trait Shape {
    fn area(&self) -> f64;
}
struct Sq(f64);
struct Rect(f64, f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

fn main() {
    println!("&Sq              {}", size_of::<&Sq>());
    println!("&dyn Shape       {}", size_of::<&dyn Shape>());
    println!("Box<Sq>          {}", size_of::<Box<Sq>>());
    println!("Box<dyn Shape>   {}", size_of::<Box<dyn Shape>>());
    println!("&[u8]            {}", size_of::<&[u8]>());
    println!("&str             {}", size_of::<&str>());
    println!("*const dyn Shape {}", size_of::<*const dyn Shape>());
    println!("&dyn Display     {}", size_of::<&dyn Display>());
    println!("Option<&dyn Shape> {}", size_of::<Option<&dyn Shape>>());
    let a: &dyn Shape = &Sq(1.0);
    let b: &dyn Shape = &Rect(1.0, 2.0);
    println!("size_of_val  a={} b={}", size_of_val(a), size_of_val(b));
    println!("align_of_val a={} b={}", align_of_val(a), align_of_val(b));
    println!("area {}", a.area() + b.area());
}
```

- 앞의 아홉 줄은 각각 몇인가? 어느 줄들이 같은 값을 내는가?
- ★★ `a`·`b` 는 같은 타입(`&dyn Shape`)인데 `size_of_val` 은 같은 값인가? 다르다면 **그 값은 어디서 읽혀 오는가**?
- ★ `size_of::<dyn Shape>()` 를 직접 부르면 무엇이 되는가?

### 2. ★★★ `A`·`B`·`C`·`D` 를 `dyn` 으로 (예측)

```rust
// r33_violations.rs
// 네 트레이트를 각각 dyn 으로 만들어 본다
trait A {
    fn pick<U>(&self, u: U) -> U;
}
trait B {
    fn dup(&self) -> Self;
}
trait C {
    const N: u32;
}
trait D: Sized {
    fn area(&self) -> f64;
}

struct S;
impl A for S {
    fn pick<U>(&self, u: U) -> U {
        u
    }
}
impl B for S {
    fn dup(&self) -> Self {
        S
    }
}
impl C for S {
    const N: u32 = 1;
}
impl D for S {
    fn area(&self) -> f64 {
        1.0
    }
}

fn main() {
    let _a: &dyn A = &S;
    let _b: &dyn B = &S;
    let _c: &dyn C = &S;
    let _d: &dyn D = &S;
}
```

- 에러는 몇 건이고 번호는? 각 트레이트에 대해 `note:` 는 **무엇을 이유로** 드는가?
- ★ 네 이유를 **한 문장**으로 묶으면? 진단의 첫 `note:` 가 그것을 어떻게 적는가?

### 3. ★★★ 항목 하나씩 — `where Self: Sized` 를 붙였다 뗐다 (예측)

```bash
# r33_grid.sh
# 트레이트 항목 하나씩을 두 벌(그대로 / `where Self: Sized` 를 붙여)로 넣고 dyn 을 만들어 본다
# 칸마다: 통과면 ok, 에러면 진단 코드(번호 없는 에러는 첫 줄 앞부분)
row() {  # row <이름> <트레이트 항목(끝 ; 없이)> <impl 몸통>
  local name=$1 item=$2 body=$3 out=() k
  for k in plain sized; do
    local w=""
    [ $k = sized ] && w=" where Self: Sized"
    printf 'trait T {\n    %s%s;\n}\nstruct S;\nimpl T for S {\n    %s\n}\nfn main() {\n    let _b: Box<dyn T> = Box::new(S);\n}\n' \
      "$item" "$w" "$body" >g.rs
    if rustc --edition 2021 -A warnings --crate-name g g.rs -o g 2>g.err; then
      out+=(ok)
    else
      out+=("$(grep -m1 -oE '^error(\[E[0-9]+\])?: .{0,28}' g.err | sed -E 's/^error\[(E[0-9]+)\].*/\1/')")
    fi
  done
  printf '%-10s %-46s | %-8s | %s\n' "$name" "$item" "${out[0]}" "${out[1]}"
  [ "${out[0]}" != "${out[1]}" ] && flips=$((flips + 1))
  total=$((total + 1))
}
flips=0 total=0
printf '%-10s %-46s | %-8s | %s\n' case item plain '+ where Self: Sized'
row control  'fn area(&self) -> f64'            'fn area(&self) -> f64 { 1.0 }'
row generic  'fn pick<U>(&self, u: U) -> U'     'fn pick<U>(&self, u: U) -> U { u }'
row ret_self 'fn dup(&self) -> Self'            'fn dup(&self) -> Self { S }'
row arg_self 'fn same(&self, o: &Self) -> bool' 'fn same(&self, _o: &Self) -> bool { true }'
row no_recv  'fn make() -> u32'                 'fn make() -> u32 { 1 }'
row rpitit   'fn items(&self) -> impl Iterator<Item = u32>' 'fn items(&self) -> impl Iterator<Item = u32> { 0..1 }'
row by_value 'fn consume(self) -> u32'          'fn consume(self) -> u32 { 1 }'
row gat      'type Out<U>'                      'type Out<U> = U;'
row const    'const N: u32'                     'const N: u32 = 1;'
rm -f g.rs g.err g
echo "cells that differ between the two columns: $flips / $total"
```

- 아홉 줄 각각 왼쪽 열(`plain`)과 오른쪽 열(`+ where Self: Sized`)은 `ok` 인가, 무슨 코드인가?
- ★★ `by_value` 줄의 왼쪽 열은? 그 이유를 Reference 는 어떻게 적는가?
- ★★ 마지막 줄의 갈린 칸 수는? **갈리지 않는 줄**은 어느 것이고 왜인가?

### 4. ★★ 뺀 메서드를 `dyn` 에서 부르면 (예측)

```rust
// r33_where_call.rs
// where Self: Sized 를 단 메서드 — dyn 으로 만들고, 그 메서드를 dyn 에서 부른다
trait Shape {
    fn area(&self) -> f64;
    fn scaled(&self, k: f64) -> Self
    where
        Self: Sized;
}

struct Sq(f64);
impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn scaled(&self, k: f64) -> Self {
        Sq(self.0 * k)
    }
}

fn main() {
    let s = Sq(1.0);
    println!("{}", s.scaled(3.0).area());
    let d: &dyn Shape = &s;
    println!("{}", d.area());
    let e = d.scaled(2.0);
}
```

- 컴파일되는가? 에러면 **어느 줄**이고 번호는? 20행·22행은?
- ★ 이 에러의 형식에서 **무엇이 빠져 있는가**?

### 5. ★★ `Sq` 와 `Tagged` 의 vtable (예측)

```rust
// r33_vt.rs
// vtable 에 무엇이 들어가나 — 드롭할 것이 있는 타입과 없는 타입
trait Shape {
    fn area(&self) -> f64;
    fn label(&self) -> usize;
}

struct Sq(f64);
struct Tagged {
    tag: String,
    w: f64,
}

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn label(&self) -> usize {
        0
    }
}
// impl 에서는 label 을 먼저 적었다
impl Shape for Tagged {
    fn label(&self) -> usize {
        self.tag.len()
    }
    fn area(&self) -> f64 {
        self.w
    }
}

fn run(v: &[Box<dyn Shape>]) -> f64 {
    v.iter().map(|s| s.area() + s.label() as f64).sum()
}

fn main() {
    let v: Vec<Box<dyn Shape>> = vec![
        Box::new(Sq(2.0)),
        Box::new(Tagged { tag: String::from("ab"), w: 1.0 }),
    ];
    println!("{}", run(&v));
}
```

- `--emit=llvm-ir` 로 뽑은 `@vtable` 중 **`Sq` 의 표와 `Tagged` 의 표**는 칸이 각각 몇이고, **첫 칸**에 무엇이 드는가?
- ★★ `Tagged` 의 `impl` 은 `label` 을 먼저 적었다. 표에서 메서드 순서는?
- ★ `Tagged` 의 크기는 표의 어느 칸에 **어떤 글자로** 보일까?

### 6. ★★ 빌린 값을 `Box<dyn Display>` 에 (예측)

```rust
// r33_static.rs
// Box<dyn Display> 에 빌린 값을 넣는 함수
use std::fmt::Display;

fn keep(v: &mut Vec<Box<dyn Display>>, s: &str) {
    v.push(Box::new(s));
}

fn main() {
    let mut v = Vec::new();
    let owned = String::from("hi");
    keep(&mut v, &owned);
    println!("{}", v.len());
}
```

- 컴파일되는가? 에러라면 진단이 말하는 **수명**은 무엇인가 — 그 수명은 시그니처에 적혀 있는가?
- ★ 이 에러에 `E` 번호가 있는가?

### 7. ★★ `dyn` 에 트레이트를 둘 (경계)

- `Box<dyn Display + Send>` 와 `Box<dyn Display + Debug>` 는 각각 되는가? 안 되는 쪽의 번호는?
- ★★ 진단의 `help:` 가 권하는 처방은? **그대로 따르면** 끝나는가 — 무엇이 더 필요한가?

### 8. ★ 업캐스팅과 다운캐스트 (경계)

- `trait Named: Debug` 일 때 `&dyn Named` 를 `&dyn Debug` 로 넘길 수 있는가? **몇 판부터**인가?
- `&dyn Shape` 를 `as &Sq` 로 되돌릴 수 있는가? 안 되면 번호와 **대신 쓰는 길**은? 그 길의 조건은?

### 9. ★★ 표를 어디에 두나 — C++ 와 (왜)

- C++ 에서 가상 함수가 있는 클래스 `Shape { double w; }` 의 `sizeof` 와 `Shape*` 의 크기는? Rust 의 `Sq(f64)` 와 `&dyn Shape` 는?
- ★ 그 차이가 「**`dyn` 으로 안 쓰는 자리의 비용**」에 무엇을 뜻하는가?

### 10. ★★ 16바이트는 누가 보장하나 (경계)

- `&dyn Trait` 가 16바이트라는 것은 **언어 보장**인가? Reference 의 **두 절이 무엇을 다르게** 적는가?
- vtable 의 **칸 배치**는 누가 정하는가?

### 11. 정적 대 동적 (연결)

- [31번 주제](../31-generics-trait-bounds-where-and-monomorphization/)가 센 것과 이 주제가 센 것은 각각 무엇인가? 「**`dyn` 은 느리다**」를 이 두 문서가 주장하는가?
- [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/)의 RPITIT E0038 은 이 주제의 격자에서 **어느 줄**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
