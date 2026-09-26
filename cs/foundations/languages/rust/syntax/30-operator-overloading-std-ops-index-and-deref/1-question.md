# rust/syntax/30 — 연산자 오버로딩(`std::ops`)·`Index`·`Deref` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs && ./<파일>`. 펜스 첫 줄 `// <파일>.rs` 가 그 파일 이름이다.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.**
> ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **연산자를 보면 메서드 시그니처로 바꿔 읽어라** — `a + b` 는 `Add::add(a, b)` 이고 **`self` 를 무엇으로 받나**가 답의 절반이다.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 다항식을 더한 뒤 왼쪽을 찍으면 (예측)

```rust
// r30_move.rs
// a + b 는 a.add(b) 다 — self 를 값으로 받는다
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>); // 계수 목록 — Copy 가 아니다

impl Add for Poly {
    type Output = Poly;
    fn add(self, rhs: Poly) -> Poly {
        let n = self.0.len().max(rhs.0.len());
        let at = |p: &Poly, i: usize| p.0.get(i).copied().unwrap_or(0);
        Poly((0..n).map(|i| at(&self, i) + at(&rhs, i)).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![10, 20, 30]);
    let c = a + b;
    println!("c = {:?}", c);
    println!("a = {:?}", a);
}
```

- 컴파일되는가? 안 되면 **에러 번호**와, rustc 가 **이동의 원인**으로 가리키는 자리는?
- ★★ `Add::add` 의 **첫 인자는 무엇으로** 받는가 — 그것이 이 에러와 무슨 관계인가?
- `b` 는 어떻게 됐나?

### 2. ★ `Copy` 벡터에 `+`·`+=`·`-` 를 쓰면 (예측)

```rust
// r30_copy.rs
// Copy 타입이면 + 뒤에도 a 가 살아 있다
use std::ops::{Add, AddAssign, Neg};

#[derive(Debug, Clone, Copy, PartialEq)]
struct V2 {
    x: i32,
    y: i32,
}

impl Add for V2 {
    type Output = V2;
    fn add(self, o: V2) -> V2 {
        V2 { x: self.x + o.x, y: self.y + o.y }
    }
}

impl AddAssign for V2 {
    fn add_assign(&mut self, o: V2) {
        self.x += o.x;
        self.y += o.y;
    }
}

impl Neg for V2 {
    type Output = V2;
    fn neg(self) -> V2 {
        V2 { x: -self.x, y: -self.y }
    }
}

fn main() {
    let a = V2 { x: 1, y: 2 };
    let b = V2 { x: 10, y: 20 };
    let c = a + b;
    println!("a + b = {:?}", c);
    println!("a     = {:?}  ★ 복사됐으니 그대로다", a);
    let mut m = a;
    m += b;
    println!("m += b {:?}", m);
    println!("-a    = {:?}", -a);
    println!("a + -a == 0 {}", a + -a == V2 { x: 0, y: 0 });
}
```

- 다섯 줄의 출력은 무엇인가?
- ★ `+` 와 `+=` 는 왼쪽 피연산자를 **각각 무엇으로** 받는가?

### 3. ★★ 참조 판만 있을 때 섞어 쓰면 (예측)

```rust
// r30_mixed.rs
// 참조 판만 있으면 — 값 + 참조, 참조 + 값은
use std::ops::Add;

#[derive(Debug)]
struct Poly(Vec<i32>);

impl Add for &Poly {
    type Output = Poly;
    fn add(self, rhs: &Poly) -> Poly {
        Poly(self.0.iter().zip(&rhs.0).map(|(x, y)| x + y).collect())
    }
}

fn main() {
    let a = Poly(vec![1, 2]);
    let b = Poly(vec![3, 4]);
    let c = &a + &b; // 된다
    let d = &c + b; // 참조 + 값
    let e = a + &c; // 값 + 참조
    println!("{:?} {:?}", d, e);
}
```

- 에러는 **몇 건**이고 번호는 각각 무엇인가?
- ★★ 18행과 19행은 **비대칭인 같은 실수**인데 왜 번호가 다른가?
- ★ 18행의 `help:` 를 그대로 따르면 무엇이 되는가?

### 4. ★ 길이에 수를, 길이에 길이를, 수에 길이를 곱하면 (예측)

```rust
// r30_scalar.rs
// Output 은 연관 타입, Rhs 는 파라미터 — 오른쪽이 다른 타입이어도 된다
use std::ops::Mul;

#[derive(Debug, Clone, Copy)]
struct Meters(f64);

impl Mul<f64> for Meters {
    type Output = Meters; // 길이 × 수 = 길이
    fn mul(self, k: f64) -> Meters {
        Meters(self.0 * k)
    }
}

impl Mul<Meters> for Meters {
    type Output = f64; // ★ 길이 × 길이 = 넓이 — 다른 타입을 돌려준다
    fn mul(self, o: Meters) -> f64 {
        self.0 * o.0
    }
}

impl Mul<Meters> for f64 {
    type Output = Meters; // ★ 왼쪽이 남의 타입(f64)이어도 된다 — Meters 가 내 것이라
    fn mul(self, m: Meters) -> Meters {
        Meters(self * m.0)
    }
}

fn main() {
    let m = Meters(3.0);
    println!("m * 2.0 = {:?}", m * 2.0);
    println!("m * m   = {:?}", m * m);
    println!("2.0 * m = {:?}", 2.0 * m);
}
```

- 세 줄의 출력은 무엇인가? 둘째 줄의 **결과 타입**은?
- ★★ 21행 `impl Mul<Meters> for f64` 는 **왼쪽이 남의 타입**인데 왜 고아 규칙에 안 걸리나?
- 21행을 지우면 `m * 2.0` 과 `2.0 * m` 중 **어느 것이** 깨지는가?

### 5. ★★★ `Deref` 로 상속을 흉내 낸 `Dog` (예측)

```rust
// r30_deref_inherit.rs
// Deref 로 「상속」을 흉내 내면 — 이름이 겹칠 때 누가 이기나
use std::ops::Deref;

struct Animal {
    name: String,
}

impl Animal {
    fn name(&self) -> String {
        format!("Animal({})", self.name)
    }
    fn describe(&self) -> String {
        format!("나는 {}", self.name()) // ★ 이 self 는 Animal 이다
    }
}

struct Dog {
    base: Animal,
}

impl Deref for Dog {
    type Target = Animal;
    fn deref(&self) -> &Animal {
        &self.base
    }
}

impl Dog {
    fn name(&self) -> String {
        format!("Dog({})", self.base.name)
    }
}

fn main() {
    let d = Dog { base: Animal { name: String::from("멍") } };
    println!("d.name()       {}", d.name()); // Dog 의 것이 이긴다
    println!("d.describe()   {}", d.describe()); // ★ 「재정의」가 안 먹는다
    println!("(*d).name()    {}", (*d).name());
}
```

```rust
// r30_deref_trait.rs
// Deref 로는 트레이트 구현이 따라오지 않는다
use std::ops::Deref;

trait Speak {
    fn speak(&self) -> String;
}

struct Animal;

impl Speak for Animal {
    fn speak(&self) -> String {
        String::from("...")
    }
}

struct Dog {
    base: Animal,
}

impl Deref for Dog {
    type Target = Animal;
    fn deref(&self) -> &Animal {
        &self.base
    }
}

fn twice<T: Speak>(x: &T) -> String {
    x.speak() + &x.speak()
}

fn as_animal(a: &Animal) -> String {
    a.speak()
}

fn main() {
    let d = Dog { base: Animal };
    println!("{}", d.speak()); // 메서드 호출 — 자동 역참조로 된다
    println!("{}", as_animal(&d)); // 구체 타입 자리 — 역참조 강제로 된다
    println!("{}", twice(&d)); // 제네릭 경계 — ?
}
```

- 앞 소스의 세 줄 출력은 무엇인가? 특히 **`d.describe()`** 는?
- ★★ 뒤 소스는 컴파일되는가? 안 되면 **37·38·39행 중 어느 줄**이 에러이고 번호는?
- ★★★ 왜 `d.speak()` 는 되는데 `twice(&d)` 는 안 되는가?

### 6. ★★ 인덱스로 꺼내 변수에 담으면 (예측)

```rust
// r30_index_move.rs
// 그 * 때문에 — 인덱스로 꺼내 옮기려 하면
use std::ops::Index;

struct Row(Vec<String>);

impl Index<usize> for Row {
    type Output = String;
    fn index(&self, i: usize) -> &String {
        &self.0[i]
    }
}

fn main() {
    let r = Row(vec![String::from("a")]);
    let s = r[0];
    println!("{}", s);
}
```

- 컴파일되는가? 안 되면 에러 번호와 `help:` 가 권하는 두 처방은?
- ★ `index` 는 `&String` 을 돌려주는데 `r[0]` 은 **왜** `String` 자리처럼 쓰이는가?

### 7. `Add` 의 `Output` 은 연관 타입이고 `Rhs` 는 제네릭 파라미터인 이유 (왜)

- 한 타입에 `Add` 가 **여러 번** 구현돼야 하는 경우는 언제인가?
- 한 구현에 결과 타입이 **둘**일 이유가 있는가?
- ★ `Rhs` 를 안 적으면 무엇이 되는가?

### 8. ★ 어떤 기호가 오버로드되고 어떤 기호는 안 되나 (경계)

- `==`·`<` 는 어느 모듈의 어느 트레이트로 가는가?
- ★★ `&&`·`||`·`=` 에 대응하는 트레이트가 **있는가**? 없다면 **왜** 없을 만한가?
- `&&` 를 `Flag` 에 쓰면 진단은 무엇이라 말하는가 — 「트레이트가 없다」고 말하는가?
- `&`(비트 AND)와 `&&` 는 같은 트레이트인가?

### 9. ★★ `deref()` 는 언제 불리나 (왜)

- `deref()` 를 한 번도 적지 않았는데 불리는 **세 자리**는 어디인가?
- ★ `&Tracked<String>` 을 `&str` 자리에 넣을 때 벗기는 단계는 **몇 번**이고, 그중 **누구의 `deref`** 가 불리는가?
- 그렇다면 `deref` 안에서 비싼 일을 하면 왜 안 되는가?

### 10. ★★ `Rc` 는 왜 `strong_count` 를 메서드로 안 두나 (왜)

- `r.strong_count()` 를 쓰면 무엇이 되는가?
- ★★ 메서드로 뒀다면 **어떤 사고**가 날 수 있는가 — 5번의 어느 현상과 같은가?
- `Rc::clone(&r)` 을 `r.clone()` 보다 권하는 이유는?

### 11. 다른 언어는 이 자리를 어떻게 다루나 (연결)

- ★★ C++ 의 `operator+` 는 관례상 인자를 무엇으로 받는가? 그래서 **이동의 기본값**이 Rust 와 어떻게 다른가?
- Python 은 `2.0 * m` 에서 왼쪽이 모르면 **어디로 넘어가는가**? Rust 는?
- ★★ Go 의 구조체 임베딩은 **인터페이스를 만족하는가**? Rust 의 `Deref` 는 트레이트 경계를 넘는가?
- ★ Kotlin 의 `by` 위임에서 「위임 대상은 내 오버라이드를 모른다」는 5번의 어느 줄과 같은 함정인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
