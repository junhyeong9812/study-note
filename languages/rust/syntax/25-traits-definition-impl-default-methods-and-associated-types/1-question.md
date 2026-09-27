# rust/syntax/25 — 트레이트 정의·구현·기본 메서드·연관 타입 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ **이 주제는 외부 크레이트를 하나도 쓰지 않는다.**
> ★ 「무엇이 되나」보다 「**어느 쪽이 이기나**」와 「**무엇이 갈리나**」를 묻는 문항이 많다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 한쪽만 덮고 둘 다 불러 보면 (예측)

```rust
// b25-01.rs
// ex.rs
// 트레이트 정의·구현·기본 메서드 — 구현체가 안 덮으면 트레이트의 것이 쓰인다 (정적 디스패치)
trait Greet {
    fn name(&self) -> String;                  // 필수 — 구현체가 반드시 채운다

    fn hello(&self) -> String {                // 기본 메서드 — 안 채워도 된다
        format!("안녕, {} 입니다", self.name())
    }

    fn shout(&self) -> String {                // 기본 메서드가 다른 기본 메서드를 부른다
        format!("{}!!!", self.hello())
    }
}

struct Cat;
struct Dog;

impl Greet for Cat {
    fn name(&self) -> String {
        String::from("고양이")
    }
}

impl Greet for Dog {
    fn name(&self) -> String {
        String::from("개")
    }
    fn hello(&self) -> String {                // hello 만 덮어쓴다. shout 은 안 덮는다
        String::from("멍")
    }
}

fn call_static<T: Greet>(x: &T) {              // 정적 디스패치 — 타입마다 따로 찍힌다
    println!("  name  {}", x.name());
    println!("  hello {}", x.hello());
    println!("  shout {}", x.shout());
}

fn main() {
    println!("Cat — 아무것도 안 덮었다");
    call_static(&Cat);
    println!("Dog — hello 만 덮었다");
    call_static(&Dog);
}
```

- 여섯 줄의 출력을 **한 글자도 안 틀리게** 적을 수 있는가?
- ★★★ `Dog` 은 `shout` 을 **안 덮었다.** 그런데 `shout` 의 답이 `Cat` 과 다른가?
- 만약 다르다면, **그 답을 바꾼 것은 무엇인가**?
- 필수 메서드(`name`)를 안 채운 `impl` 을 쓰면 무슨 일이 생기는가?

### 2. ★★ 같은 트레이트를 상자에 담아 부르면 (예측)

```rust
// b25-02.rs
// ex.rs
// 같은 트레이트를 동적 디스패치로 — 기본 메서드도 같은 자리로 간다
trait Greet {
    fn name(&self) -> String;

    fn hello(&self) -> String {
        format!("안녕, {} 입니다", self.name())
    }

    fn shout(&self) -> String {
        format!("{}!!!", self.hello())
    }
}

struct Cat;
struct Dog;

impl Greet for Cat {
    fn name(&self) -> String {
        String::from("고양이")
    }
}

impl Greet for Dog {
    fn name(&self) -> String {
        String::from("개")
    }
    fn hello(&self) -> String {
        String::from("멍")
    }
}

fn call_dyn(x: &dyn Greet) {                   // 동적 디스패치 — 함수는 한 벌뿐이다
    println!("  hello {}", x.hello());
    println!("  shout {}", x.shout());
}

fn main() {
    let zoo: Vec<Box<dyn Greet>> = vec![Box::new(Cat), Box::new(Dog)];
    for g in &zoo {
        println!("{} (dyn)", g.name());
        call_dyn(g.as_ref());
    }
    println!("포인터 폭");
    println!("  &Cat        {} 바이트", std::mem::size_of::<&Cat>());
    println!("  &dyn Greet  {} 바이트", std::mem::size_of::<&dyn Greet>());
}
```

- 앞 문항의 출력과 **어디가 같고 어디가 다른가**?
- ★ `&Cat` 과 `&dyn Greet` 의 바이트 수는 각각 얼마인가? 그 차이는 무엇을 더 들고 다니는 것인가?
- 기본 메서드는 **표(vtable)에 칸을 차지하는가**?
- 이 수치는 언어 보장인가 구현 세부인가?

### 3. ★★★ 같은 문제를 두 도구로 — 제네릭 파라미터 판 (예측)

```rust
// b25-03.rs
// ex.rs
// 제네릭 파라미터 판 — 한 타입에 여러 번 구현된다. 대신 호출부가 타입을 적어야 한다
trait Extract<T> {
    fn extract(&self) -> T;
}

struct Ticket;

impl Extract<u32> for Ticket {
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract<String> for Ticket {
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    let a: u32 = t.extract();                  // 받는 쪽 타입으로 고른다
    let b: String = t.extract();
    let c = Extract::<u32>::extract(&t);       // 또는 터보피시로 찍어 고른다
    println!("u32    {}", a);
    println!("String {}", b);
    println!("찍어서 {}", c);
}
```

```rust
// b25-06.rs
// ex.rs
// 연관 타입 판 — 같은 타입에 두 번 구현하면
trait Extract {
    type Out;
    fn extract(&self) -> Self::Out;
}

struct Ticket;

impl Extract for Ticket {
    type Out = u32;
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract for Ticket {
    type Out = String;
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    println!("{}", t.extract());
}
```

- 앞 소스는 컴파일되는가? 뒤 소스는?
- ★★★ 둘이 갈리는 **한 문장**을 댈 수 있는가?
- 뒤 소스가 거부된다면 **에러 번호**와 진단 문구는 무엇인가?
- 연관 타입은 **트레이트 이름의 일부인가**?

### 4. ★★ 제네릭 파라미터 판에서 타입을 안 적으면 (예측)

```rust
// b25-04.rs
// ex.rs
// 제네릭 파라미터 판 — 타입을 안 적으면 무엇을 고를지 못 정한다
trait Extract<T> {
    fn extract(&self) -> T;
}

struct Ticket;

impl Extract<u32> for Ticket {
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract<String> for Ticket {
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    let c = t.extract();
    println!("{:?}", c);
}
```

- **에러 번호**와 제목은 무엇인가?
- 진단은 **후보를 몇 개** 짚어 주는가? 어느 줄들을 가리키는가?
- `help:` 가 제안하는 고침안은 무엇인가?
- 구현이 **하나뿐**이었다면 이 코드는 통과했겠는가? 그때 생기는 위험은 무엇인가?

### 5. ★★ 이 트레이트를 `dyn` 으로 만들면 (예측)

```rust
// b25-07.rs
// ex.rs
// 객체 안전성 — dyn 이 될 수 없는 트레이트를 dyn 으로 만들어 본다
trait Spawner {
    fn new_one() -> Self;                      // ① Self 를 돌려준다
    fn tag(&self) -> u8;
    fn feed<T>(&self, item: T);                // ② 제네릭 메서드
}

struct Bee;

impl Spawner for Bee {
    fn new_one() -> Self {
        Bee
    }
    fn tag(&self) -> u8 {
        7
    }
    fn feed<T>(&self, _item: T) {}
}

fn main() {
    let b: Box<dyn Spawner> = Box::new(Bee);
    println!("{}", b.tag());
}
```

- 컴파일되는가? 안 되면 **에러 번호**는?
- ★★★ 진단은 **이유를 몇 개** 대는가? 각각 어느 줄을 짚는가?
- ★ 진단 전문에 **「object safe」라는 말이 나오는가**? 대신 무엇이라고 쓰는가?
- `help:` 두 개는 각각 무엇을 하라고 하는가?

### 6. ★ 반환 자리 `impl Trait` 에 갈래를 넣으면 (예측)

```rust
// b25-09.rs
// ex.rs
// 반환 자리 impl Trait — 두 갈래를 돌려주려 하면
trait Shape {
    fn area(&self) -> f64;
}

struct Square(f64);
struct Circle(f64);

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}

fn make(big: bool) -> impl Shape {
    if big {
        Square(3.0)
    } else {
        Circle(1.0)
    }
}

fn main() {
    println!("{}", make(true).area());
}
```

- 컴파일되는가? 안 되면 **에러 번호**와 제목은?
- ★ `help:` 가 제안하는 것은 무엇인가? **두 단계**로 나뉘어 있는가?
- 반환 자리 `impl Trait` 가 감추는 것은 「타입」인가 「갈래」인가?
- 인자 자리 `impl Trait` 에도 같은 제약이 있는가?

### 7. 연관 타입과 제네릭 파라미터를 무엇으로 고르나 (왜)

- 고르는 기준을 **한 질문**으로 줄일 수 있는가?
- 「연관 타입은 출력, 제네릭 파라미터는 입력」이라는 외움말은 어디서 깨지는가?
- `From<T>` 는 왜 제네릭 파라미터 판인가?
- 연관 타입을 골랐을 때 **호출부가 덜 쓰는 것**은 무엇인가?

### 8. 기본 메서드의 값과 한계 (경계)

- 기본 메서드가 **못 하는 것**은 무엇인가 — 상태를 가질 수 있는가?
- 기본 메서드의 답을 바꾸는 방법은 **몇 가지**인가?
- 슈퍼트레이트(`trait A: B`)는 기본 메서드에 무엇을 주는가?
- 나중에 트레이트에 **기본 메서드를 하나 더** 넣으면 기존 구현체들이 깨지는가?

### 9. 세 가지 부르는 꼴의 분업 (경계)

- `fn f<T: Greet>(x: &T)` · `fn f(x: impl Greet)` · `fn f(x: &dyn Greet)` 는 각각 언제 쓰는가?
- 앞의 둘은 완전히 같은가 — **터보피시**는 어느 쪽에서 되는가?
- `dyn` 이 내는 값(비용)은 무엇무엇인가?
- 갈래가 필요 없는데 `Box<dyn …>` 을 쓰면 무엇을 잃는가?

### 10. 트레이트에서 `Self` 가 오는 자리 (경계)

```rust
// b25-10.rs
// ex.rs
// 트레이트에서 Self 가 오는 자리 — 연관 상수·인자·반환·기본 메서드
trait Unit: Sized + Copy + PartialEq {
    const ZERO: Self;                          // ① 연관 상수의 타입

    fn add(self, other: Self) -> Self;         // ② 인자와 반환

    fn double(self) -> Self {                  // ③ 기본 메서드가 Self 를 돌려준다
        self.add(self)
    }

    fn is_zero(&self) -> bool {                // ④ 기본 메서드가 연관 상수를 읽는다
        *self == Self::ZERO
    }

    fn sum(items: &[Self]) -> Self {           // ⑤ self 가 없는 연관 함수(기본 구현)
        let mut acc = Self::ZERO;
        for it in items {
            acc = acc.add(*it);
        }
        acc
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
struct Won(i64);

impl Unit for Won {
    const ZERO: Self = Won(0);
    fn add(self, other: Self) -> Self {
        Won(self.0 + other.0)
    }
}

fn main() {
    let a = Won(1200);
    println!("ZERO     {:?}", Won::ZERO);
    println!("double   {:?}", a.double());
    println!("is_zero  {} {}", a.is_zero(), Won::ZERO.is_zero());
    println!("sum      {:?}", Won::sum(&[Won(100), Won(20), Won(3)]));
}
```

- `Self` 가 쓰인 자리를 **다섯 군데** 짚을 수 있는가?
- `trait Unit: Sized + Copy + PartialEq` 의 세 슈퍼트레이트는 각각 **무엇 때문에** 필요한가?
- 이 트레이트는 `dyn` 이 될 수 있는가? 왜인가?
- `const ZERO: Self` 를 구현체가 안 채우면 어떻게 되는가?

### 11. 다른 언어의 인터페이스와 잇기 (연결)

- Kotlin 의 인터페이스와 **같은 것**과 **다른 것**을 각각 둘씩 댈 수 있는가?
- Go 는 `implements` 를 안 적는다. 그 선택 때문에 Go 에 **원리상 없는 것**은 무엇인가?
- Java 의 `default` 메서드와 Rust 의 기본 메서드는 같은 것인가?
- C# 의 확장 메서드는 「남의 타입에 메서드를 붙인다」는 점이 비슷한데, **무엇이 결정적으로 다른가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
