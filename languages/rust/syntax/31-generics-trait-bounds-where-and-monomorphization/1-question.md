# rust/syntax/31 — 제네릭과 트레이트 경계·`where`·단형화 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs && ./<파일>`. 벌 수를 셀 때는 **`-C opt-level=N -C symbol-mangling-version=v0`** 을 붙이고 `nm -C` 로 본다.
> C++ 는 `g++`/`clang++ -std=c++20 -Wall -Wextra -c <파일>.cpp`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.** ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **벌 수를 답할 때는 반드시 「어느 `opt-level` 에서」를 붙여라** — 판이 없는 벌 수는 답이 아니다.
> ★★★ **속도는 묻지 않는다** — 이 주제는 속도를 재지 않았다.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 아무도 안 부르는 제네릭 함수 (예측)

```rust
// r31_nobound.rs
// 경계 없이 메서드를 부르면 — 호출이 하나도 없어도
trait Shape {
    fn area(&self) -> f64;
}

fn total<T>(items: &[T]) -> f64 {
    items.iter().map(|it| it.area()).sum()
}

fn main() {}
```

- 컴파일되는가? `main` 이 비어 있는데도 에러가 난다면 **번호**는?
- ★★ 호출이 없는데 왜 검사되는가 — 몸통은 `T` 에 대해 **무엇만** 아는가?

### 2. ★ 경계 둘 중 하나가 빠진 타입으로 부르면 (예측)

```rust
// r31_missing.rs
// 여러 경계 중 하나가 빠지면 — 호출 자리의 에러
use std::fmt::Debug;

trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64); // ★ Debug 가 없다

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

fn a<T: Shape + Debug>(x: &T) -> String {
    format!("{:?}={}", x, x.area())
}

fn main() {
    println!("{}", a(&Sq(2.0)));
}
```

- 에러 번호는? ★ **주 진단의 밑줄**은 16행(경계)과 21행(호출) 중 어디에 그어지는가?
- 1번과 합치면 Rust 는 **몇 자리에서** 막는가?

### 3. ★ `&T` 로 받는 함수에 `str` 을 넣으면 (예측)

```rust
// r31_sized.rs
// 숨어 있는 경계 Sized — str 을 T 로 받으려 하면
use std::fmt::Display;

fn plain<T: Display>(x: &T) -> String {
    format!("[{}]", x)
}

fn relaxed<T: Display + ?Sized>(x: &T) -> String {
    format!("[{}]", x)
}

fn main() {
    let s: &str = "hi";
    println!("{}", relaxed(s)); // T = str
    println!("{}", plain(&s)); // T = &str — 크기가 있다
    println!("{}", plain(s)); // T = str
}
```

- 14·15·16행 중 **어느 줄이** 에러인가? 번호와, `note:` 가 짚는 **경계의 이름**은?
- ★ 4행에 없는 경계가 어디서 왔나? 어떻게 푸는가?

### 4. ★★ 같은 모양의 C++ 템플릿을 두 컴파일러로 (예측)

```cpp
// r31_tmpl.cpp
// C++ 템플릿 — 몸통을 언제 검사하나
template <class T>
double total(const T& x) {
    return x.area(); // T 가 area 를 가지는지 이 자리에서는 모른다
}

int main() {
    return 0; // ★ 한 번도 인스턴스화하지 않는다
}
```

```cpp
// r31_tmpl_int.cpp
// 인스턴스화하는 순간 — int 로 부르면
template <class T>
double total(const T& x) {
    return x.area();
}

int main() {
    return total(3) == 0.0 ? 0 : 1;
}
```

- 앞 파일을 `g++`·`clang++` 로 컴파일하면 **종료 코드와 진단 줄 수**는? 1번 Rust 와 무엇이 다른가?
- 뒤 파일에서 에러는 **몇 행**에서 나는가 — 템플릿 몸통인가 호출 자리인가?
- ★ C++20 콘셉트로 요구를 선언하면 에러 자리는 어디로 옮겨 가는가? **그래도 남는 차이**는?

### 5. ★★★ 세 타입으로 부른 `total` 은 몇 벌인가 (예측)

```rust
// r31_mono.rs
// 같은 제네릭 함수를 세 타입으로 부른다 — 몇 벌 생기나
trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64);
struct Circle(f64);
struct Rect(f64, f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

fn total<T: Shape>(items: &[T]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn total_dyn(items: &[&dyn Shape]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn main() {
    let g = total(&[Sq(1.0), Sq(2.0)]) + total(&[Circle(1.0)]) + total(&[Rect(1.0, 2.0)]);
    let (s1, s2, c, r) = (Sq(1.0), Sq(2.0), Circle(1.0), Rect(1.0, 2.0));
    let d = total_dyn(&[&s1, &s2, &c, &r]);
    println!("{} {}", g, d);
}
```

- ★★ `--emit=mir` 로 보면 `total` 은 **몇 줄**로 나오는가?
- ★★★ `-C opt-level=0 -C symbol-mangling-version=v0` 로 빌드하고 `nm -C` 로 보면 `total::<…>` 는 **몇 벌**인가? `total_dyn` 은?
- ★★ 같은 것을 `opt-level=3` 으로 빌드하면?
- ★ `total` 말고 **타입마다 따로 찍히는 std 함수**가 있는가?

### 6. ★★★ 인라인을 막고, 몸이 같은 타입을 섞어, 판 넷으로 (예측)

```rust
// r31_keep.rs
// 인라인을 막고 세면 — 그리고 몸이 같은 두 벌은
use std::hint::black_box;

trait Shape {
    fn area(&self) -> f64;
}

struct Sq(f64);
struct Tile(f64); // ★ Sq 와 모양도 area 몸통도 같다
struct Rect(f64, f64);

impl Shape for Sq {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Tile {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}
impl Shape for Rect {
    fn area(&self) -> f64 {
        self.0 * self.1
    }
}

#[inline(never)]
fn total<T: Shape>(items: &[T]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

#[inline(never)]
fn total_dyn(items: &[&dyn Shape]) -> f64 {
    let mut s = 0.0;
    for it in items {
        s += it.area();
    }
    s
}

fn main() {
    let a = [Sq(1.0), Sq(2.0)];
    let b = [Tile(1.0)];
    let c = [Rect(1.0, 2.0)];
    let g = total(black_box(&a)) + total(black_box(&b)) + total(black_box(&c));
    let d: [&dyn Shape; 3] = [&Sq(1.0), &Tile(1.0), &Rect(1.0, 2.0)];
    println!("{} {}", g, total_dyn(black_box(&d)));
}
```

```bash
# r31_grid.sh
# r31_keep.rs 를 opt-level 넷으로 빌드하고, 함수 심볼의 벌 수와 바이트(nm -S)를 센다
for o in 0 1 2 3; do
  rustc --edition 2021 -C opt-level=$o -C symbol-mangling-version=v0 r31_keep.rs -o k$o
  echo "== opt-level=$o"
  nm -C -S -t d k$o | awk '
    /r31_keep::total::</ { g++; gb += $2; print "   " $2 + 0 "B  " $4 }
    /r31_keep::total_dyn/ { d++; db += $2; print "   " $2 + 0 "B  " $4 }
    / as r31_keep::Shape>::area/ { a++ }
    END { printf "   제네릭 total %d 벌 %dB · dyn total %d 벌 %dB · area 몸통 %d 벌\n", g, gb, d, db, a }'
done
```

- `opt-level` 0·1·2·3 에서 `total::<…>` 의 **벌 수**는 각각 몇인가?
- ★★ 어느 판에서 **한 벌이 사라진다면** 누가 사라지고 왜인가?
- ★ 제네릭 쪽 바이트 합과 `total_dyn` 의 바이트 중 **어느 쪽이 큰가** — 모든 판에서 같은가?

### 7. `where` 에만 쓸 수 있는 경계 (왜)

- `T: Shape + Debug` 를 꺾쇠 안에 쓰는 것과 `where` 에 쓰는 것은 **뜻이 다른가**?
- ★ `Vec<T>: Debug` 나 `I::Item: Display` 는 **왜** 꺾쇠 안에 못 쓰는가?

### 8. ★ E0277 과 E0271 (경계)

- `fn checksum<I: Iterator<Item = u8>>` 에 `u16` 을 내는 이터레이터를 넘기면 번호는 무엇인가?
- 그 번호가 E0277 이 **아닌** 이유는 — 그 이터레이터는 `Iterator` 인가?

### 9. ★★★ 벌 수는 누가 정하나 (경계)

- 「제네릭 함수는 타입마다 한 벌씩 생긴다」는 **언어 보장**인가?
- ★★ 벌 수를 바꾸는 최적화 **둘**은 무엇인가? 이 판에서 각각 무엇을 했나?
- ★ MIR 창과 `-Z print-mono-items` 창은 왜 이 질문에 **못 쓰였나** — 대신 무엇으로 물었나? 그 창이 **못 보는 것**은?

### 10. ★★ 명목이냐 구조냐 (연결)

- ★★ TS 20번이 rustc 로 던져 뒤집은 요약 「Rust 는 정의 자리, TS 는 사용 자리」 대신 **진짜 축**은 무엇이었나?
- `struct Loud` 에 `fmt` 메서드가 있는데 `T: Display` 를 못 넘는 이유는?
- Go 의 암묵 구현·Python 의 `Protocol`/`ABC` 는 그 축의 어느 쪽인가?
- ★ C++20 콘셉트는 어느 쪽이고, 콘셉트를 달아도 몸통이 콘셉트 밖 능력을 쓰면 어떻게 되나?

### 11. 단형화의 청구서 (연결)

- ★★ 「제로 코스트」의 논증은 어디가 정본이고, 이 주제는 그중 **무엇을 세었나**?
- `dyn` 판은 단형화 대신 **무엇을** 만드는가 — 타입이 늘면 무엇이 느는가?
- Java 의 타입 소거는 벌 수 축에서 **어느 끝**인가?
- ★ std 의 `fs::read<P: AsRef<Path>>` 는 팽창을 줄이려고 **어떤 모양**을 쓰는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
