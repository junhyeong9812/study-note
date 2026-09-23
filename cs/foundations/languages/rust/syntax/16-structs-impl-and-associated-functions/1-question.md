# rust/syntax/16 — 구조체 세 종류·`impl`·연관 함수·`Self` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 문법을 아는지가 아니라 **컴파일러가 무엇을 거부하고
> 거부할 때 어느 문구를 쓰는지**, 그리고 **세 형태가 메모리에서 몇 바이트인지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.**
> ★ 이 주제의 진단은 **번호보다 문구가 정보가 많다** — 같은 **E0599** 가 네 가지 뜻으로 나온다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 구조체 갱신 문법 `..base` 를 쓴 뒤 원본을 다시 읽으면 (예측)

```rust
#[derive(Debug)]
struct Config { name: String, retries: u32, verbose: bool }

fn main() {
    let base = Config { name: String::from("기본"), retries: 3, verbose: false };
    let derived = Config { retries: 5, ..base };
    println!("{:?}", derived);
    println!("{:?}", base);
}
```

- 컴파일되는가? 안 되면 에러 번호와 제목 줄은 무엇인가?
- 진단에 나오는 낱말 하나가 `..base` 가 **무엇을 하는지** 그대로 말해 준다. 무엇인가?
- `= note:` 가 짚는 필드는 셋 중 어느 것이고 왜 그것만 짚는가?
- 세 필드를 전부 `Copy` 타입으로 바꾸면 같은 코드가 통과하는가?
- `base.retries` 하나만 읽는 것은 되는가?

### 2. ★★ 연관 함수를 `.` 으로, 메서드를 `::` 으로 불러 보면 (예측)

```rust
struct Counter { n: u32 }

impl Counter {
    fn new() -> Self { Counter { n: 0 } }
    fn get(&self) -> u32 { self.n }
}

fn main() {
    let c = Counter::new();
    println!("{}", c.new());
    println!("{}", Counter::get());
}
```

- 에러가 몇 개 나며 각각 번호는 무엇인가?
- 두 에러의 **성격이 다르다.** 어떻게 다른가 — 한쪽은 「문법이 틀렸다」고 하고 다른 쪽은 무엇이라고 하는가?
- `Counter::get(&c)` 는 컴파일되는가?
- 진단의 `= note:` 한 줄이 **연관 함수와 메서드의 정의**를 말한다. 그 문장을 적을 수 있는가?

### 3. ★★ 유닛 구조체·빈 튜플 구조체·newtype·`()`·`[u8; 0]` 의 `size_of` 를 찍어 보면 (예측)

```rust
struct Unit;
struct Empty();
struct Newtype(u64);
struct Named { a: u8, b: u32 }
struct Reordered { b: u32, a: u8 }
// size_of 와 align_of 를 위 다섯과 () · [u8; 0] 에 대해 전부 찍는다
```

- 일곱 개의 `size_of` 를 각각 적을 수 있는가?
- 그중 **크기가 0**인 것을 전부 대라. 그것들의 `align_of` 는 얼마인가?
- `Newtype(u64)` 와 `u64` 의 크기·정렬을 비교하면 어떻게 되는가?
- `Named` 와 `Reordered` 는 크기가 같은가? 같다면 그것은 **언어 보장인가 구현 세부인가**?
- 필드가 메모리 **어느 자리**에 놓이는지 직접 재면 선언 순서와 같은가?

### 4. ★ 필드와 메서드 이름이 같을 때 `s.f` 와 `s.f()` (예측)

```rust
struct Widget {
    width: u32,
    render: Box<dyn Fn() -> String>,
}

impl Widget {
    fn width(&self) -> u32 { self.width * 2 }
    fn render(&self) -> String { String::from("메서드 render") }
}

fn main() {
    let w = Widget { width: 10, render: Box::new(|| String::from("필드 render")) };
    println!("{} {} {} {}", w.width, w.width(), w.render(), (w.render)());
}
```

- 컴파일되는가? 된다면 네 값은 각각 무엇인가?
- `w.render()` 는 **필드의 클로저**를 부르는가 **메서드**를 부르는가?
- `(w.render)()` 의 괄호는 무엇을 강제하는가?
- 메서드를 지우고 클로저 필드만 남긴 채 `w.render()` 를 부르면 무엇이 나오는가?

### 5. ★ `self` 를 받는 메서드를 두 번 부르면 · `&mut self` 를 `mut` 아닌 바인딩에서 부르면 (예측)

```rust
struct Builder { parts: Vec<String> }

impl Builder {
    fn new() -> Self { Builder { parts: Vec::new() } }
    fn add(mut self, s: &str) -> Self { self.parts.push(s.to_string()); self }
    fn build(self) -> String { self.parts.join("-") }
}

fn main() {
    let b = Builder::new().add("가").add("나");
    println!("{}", b.build());
    println!("{}", b.build());
}
```

- 이 코드의 에러 번호는 무엇인가?
- 진단의 `note:` 가 짚는 것은 함수 이름인가, 리시버인가, 호출 자리인가?
- `fn add(mut self, ...)` 의 `mut` 는 `&mut self` 와 같은 것인가?
- 리시버가 `&mut self` 인 메서드를 `let c = …` (즉 `mut` 없음)에서 부르면 어느 에러가 나는가?
- 그 에러의 `help:` 는 **어느 줄**을 고치라고 하는가?

### 6. ★★ 같은 이름의 연관 함수가 고유 `impl` 과 트레이트에 하나씩 있을 때 (예측)

```rust
struct Counter { n: u32 }

trait Make { fn build() -> Self; }

impl Counter {
    fn build() -> Self { Counter { n: 0 } }
}

impl Make for Counter {
    fn build() -> Self { Counter { n: 9 } }
}

fn main() {
    let c = Counter { n: 1 };
    println!("{}", c.build().n);
}
```

- 에러 번호는 무엇인가?
- 진단이 후보를 **몇 개** 나열하며 그 표기는 어떤 모양인가?
- 두 후보를 각각 **무엇이라고** 부르는가 — 둘의 설명 문구가 다르다.
- `help:` 가 주는 고친 코드는 어떤 문법인가?
- 같은 이름을 **고유 `impl` 두 블록**에 두면 대신 어느 번호가 나오는가?

### 7. `Self` 가 쓰이는 자리 (왜)

- `Self` 와 `self` 는 무엇이 다른가 — 한 문장으로 가를 수 있는가?
- `Self` 가 나오는 자리를 **성격별로 묶으면 몇 갈래**인가? 각 갈래에 예를 하나씩 들 수 있는가?
- `self: &Self` 와 `&self` 는 같은 것인가?
- 이름 있는 구조체에서 `fn new() -> Self { Self }` 는 왜 안 되는가? 튜플·유닛 구조체에서는?
- `impl` 밖의 자유 함수에 `-> Self` 를 적으면 어느 에러가 나며, 그 진단이 말하는 **유효 범위**는 어디까지인가?

### 8. 같은 타입에 `impl` 블록을 여럿 두기 (경계)

- 되는가? 된다면 개수 제한이 있는가?
- 실제로 나눠 쓰는 **이유**를 하나 대라 — 나눠야만 되는 것이 무엇인가?
- 경계 때문에 안 생긴 메서드를 부르면 진단이 「없다」고 하는가, 다른 말을 하는가?
- 그 진단은 **어느 줄**을 짚어 주는가?
- 나눠 쓴 것이 **컴파일 결과**에 남는가? **문서**에는 남는가?

### 9. `E0599` 의 네 얼굴 (경계)

- 같은 번호로 나오는 서로 다른 상황을 **넷** 대라.
- 그중 「그 이름이 아예 없다」는 어느 것이고, 나머지 셋은 각각 무엇이 문제인가?
- 진단이 `candidate #1`·`#2` 로 나열하는 것은 **어느 경우**인가 — 늘 나열하는가?
- 없는 메서드를 불렀을 때 진단은 **뒤진 `impl` 블록들**을 알려 주는가?

### 10. 필드 가시성과 생성 에러 (경계)

- 같은 모듈 안에서는 `pub` 없는 필드가 보이는가?
- `mod` 밖에서 `pub` 없는 필드를 읽으면 어느 번호이고, **타입 자체**에 `pub` 이 없으면 어느 번호인가?
- `pub struct` 를 쓰면 필드도 함께 열리는가?
- 비공개 필드를 읽으려다 막혔을 때 진단이 권하는 **관용구**는 무엇인가?
- 구조체 생성에서 필드를 빠뜨리면 · 없는 필드를 주면 각각 어느 번호인가?

### 11. `cargo doc` 이 `impl` 블록을 어떻게 내놓나 (왜)

- 경계가 다른 `impl` 블록 셋을 쓰고 문서를 만들면 **몇 덩어리**로 나오는가?
- 생성된 HTML 에서 그것을 **기계적으로 세는** 방법을 하나 대라.
- 내가 쓰지 않은 메서드들이 문서에 따라 붙는다. 그것들은 무엇이며 어느 절에 모이는가?
- `#[derive(Debug)]` 없이 `{:?}` 를 쓰면 어느 번호가 나며, `{:?}` 와 `{:#?}` 는 출력이 어떻게 다른가?

### 12. 다른 주제와 잇기 (연결)

- E0063 · E0560 · E0592 · E0034 · E0596 · E0616 · E0603 · E0411 · E0423 이 각각 어떤 상황에서 나는지 한 줄씩 말할 수 있는가?
- 이 주제에서 **번호가 없는** 진단을 하나 만났다. 무엇이었나?
- `&self` 메서드 하나가 값 **전체**를 잡는 이유를 다룬 주제는 몇 번이고, 그 처방을 모은 주제는 몇 번인가?
- **참조를 필드로 담는 구조체**는 목록의 몇 번이 정본인가?
- 객체·캡슐화 **일반**은 어느 갈래가 정본이고, 이 주제는 어디부터인가?
- `impl Trait for Type`(트레이트 구현)은 목록의 몇 번인가 — 이 주제가 다룬 `impl` 은 무엇이라 부르나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
