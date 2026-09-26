# rust/syntax/32 — `impl Trait` — 인자 위치·반환 위치와 2024의 수명 포착 변화 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs` 와 `rustc --edition 2024 <파일>.rs`. **이 주제는 에디션이 답을 가른다** — 답할 때 **어느 에디션인지를 먼저** 말하라.
> ★★ **`--edition` 을 빼면 에디션 2015 다.** ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **반환 `impl Trait` 를 보면 두 가지를 먼저 물어라** — 「**숨긴 타입이 무엇인가**」와 「**그 봉투가 어떤 수명을 품는다고 보나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 인자 위치 `impl Trait` 에 터보피시 (예측)

```rust
// r32_apit.rs
// 인자 위치 impl Trait — 이름 없는 제네릭 파라미터
use std::fmt::Display;

fn show(x: impl Display) -> String {
    format!("<{}>", x)
}

fn pair<T: Display>(a: T, b: impl Display) -> String {
    format!("{} {}", a, b)
}

fn main() {
    println!("{}", show(1));
    println!("{}", show("a"));
    println!("{}", pair::<u8>(7, "b")); // ★ 이름 있는 T 만 찍는다
}
```

```rust
// r32_apit_turbofish.rs
// impl Trait 자리를 터보피시로 찍으려 하면
use std::fmt::Display;

fn show(x: impl Display) -> String {
    format!("<{}>", x)
}

fn pair<T: Display>(a: T, b: impl Display) -> String {
    format!("{} {}", a, b)
}

fn main() {
    println!("{}", show::<i32>(1));
    println!("{}", pair::<u8, &str>(7, "b"));
}
```

- 앞 소스는 컴파일되는가? 특히 15행 `pair::<u8>(7, "b")` 는?
- 뒤 소스의 에러는 몇 건이고 번호는? `pair` 는 제네릭 인자를 **몇 개** 받는다고 진단이 말하는가?
- ★ `impl Trait` 인자와 `<T: Trait>` 를 서로 바꾸는 것이 왜 **호출자를 깨는 변경**일 수 있나?

### 2. ★★ 숨긴 `String` 에 `.len()` (예측)

```rust
// r32_hide.rs
// 반환 위치 impl Trait 가 감추는 것
use std::fmt::Display;

fn name() -> impl Display {
    String::from("kim")
}

fn main() {
    let n = name();
    println!("{}", n); // Display 는 약속했다
    println!("{}", n.len()); // String 의 메서드는 약속 안 했다
}
```

- 컴파일되는가? 안 되면 번호와, 진단이 `n` 의 타입을 **무엇이라 부르는가**?
- 이 감춤이 라이브러리 작성자에게 주는 **값**은 무엇인가?

### 3. ★★★ 시그니처에 없는 `Send` (예측)

```rust
// r32_leak.rs
// 그런데 새어 나오는 것 — 자동 트레이트와 런타임 타입 이름
use std::fmt::Display;

fn name() -> impl Display {
    String::from("kim")
}

fn need_send<T: Send>(_: T) -> &'static str {
    "Send 통과"
}

fn main() {
    println!("{}", need_send(name())); // ★ 시그니처에는 Send 가 없다
    println!("{}", std::any::type_name_of_val(&name()));
}
```

```rust
// r32_leak_rc.rs
// 숨긴 타입이 Send 가 아니면 — 에러가 무엇을 말하나
use std::fmt::Display;
use std::rc::Rc;

fn shared() -> impl Display {
    Rc::new(5)
}

fn need_send<T: Send>(_: T) -> &'static str {
    "Send 통과"
}

fn main() {
    println!("{}", need_send(shared()));
}
```

- 앞 소스는 컴파일되는가? 두 줄의 출력은?
- ★★ 뒤 소스의 에러 문구는 **어떤 타입의 이름**을 말하는가 — 그 이름은 시그니처에 있는가?
- ★ 그렇다면 몸통만 바꿨는데 **다른 크레이트가 깨지는** 경로는 무엇인가? 어떻게 막나?

### 4. ★★ 두 갈래가 서로 다른 클로저를 돌려주면 (예측)

```rust
// r32_branch_closure.rs
// 두 갈래가 다른 클로저를 돌려주면 — 환경을 잡는 클로저
fn step(k: i32, big: bool) -> impl Fn(i32) -> i32 {
    if big {
        move |x| x + k * 10
    } else {
        move |x| x + k
    }
}

fn main() {
    println!("{}", step(1, true)(1));
}
```

```rust
// r32_branch_fnptr.rs
// 두 갈래가 다른 클로저를 돌려주면 — 아무것도 안 잡는 클로저
fn step(big: bool) -> impl Fn(i32) -> i32 {
    if big {
        |x| x + 10
    } else {
        |x| x + 1
    }
}

fn main() {
    println!("{} {}", step(true)(1), step(false)(1));
    println!("{}", std::any::type_name_of_val(&step(true)));
}
```

- 두 소스 각각 컴파일되는가? 되는 쪽의 출력 두 줄은?
- ★★ 한쪽만 된다면 **무엇이** 둘을 가르는가?

### 5. ★★★ 같은 소스, 두 에디션 — 네 칸 (예측)

```rust
// r32_capture_a.rs
// 같은 소스, 두 에디션 — ① 빌린 것을 돌려주는 반환 impl Trait
fn lens<'a>(v: &'a [String]) -> impl Iterator<Item = usize> {
    v.iter().map(|s| s.len())
}

fn main() {
    let v = vec![String::from("ab"), String::from("cde")];
    let total: usize = lens(&v).sum();
    println!("합 {}", total);
}
```

```rust
// r32_capture_b.rs
// 같은 소스, 두 에디션 — ② 빌리지 않는 값을 돌려주는 반환 impl Trait
fn counter(v: &Vec<i32>) -> impl Fn() -> usize {
    let n = v.len(); // 길이만 복사해 둔다 — v 는 안 잡는다
    move || n
}

fn main() {
    let mut v = vec![1, 2, 3];
    let c = counter(&v);
    v.push(4); // ★ c 가 v 를 빌리고 있나?
    println!("{} {}", c(), v.len());
}
```

- ★★★ 두 소스를 **`--edition 2021`** 과 **`--edition 2024`** 로 각각 컴파일하면 **네 칸**은 각각 통과인가 에러인가? 에러면 번호는?
- ★★ 뒤 소스의 에러가 난다면 **어느 줄**(함수 안인가 호출자인가)에서 나는가?
- ★ 두 소스를 **두 에디션에서 같은 뜻**으로 만들려면 각각 무엇을 한 단어 덧붙이면 되는가?

### 6. ★★ 시그니처가 같은 두 메서드를 2021 로 (예측)

```rust
// r32_rpitit.rs
// 트레이트 안의 impl Trait 반환(RPITIT) — 그리고 같은 모양의 고유 메서드
trait Source {
    fn items(&self) -> impl Iterator<Item = u32>;
}

struct Bag(Vec<u32>);

impl Source for Bag {
    fn items(&self) -> impl Iterator<Item = u32> {
        self.0.iter().copied()
    }
}

impl Bag {
    fn own(&self) -> impl Iterator<Item = u32> {
        self.0.iter().copied()
    }
}

fn main() {
    let b = Bag(vec![1, 2]);
    println!("{:?} {:?}", b.items().collect::<Vec<_>>(), b.own().collect::<Vec<_>>());
}
```

- `--edition 2021` 로 컴파일하면 에러는 **몇 건**이고 **어느 메서드**에서 나는가?
- ★★ 시그니처가 한 글자도 같은데 왜 한쪽만 나는가? 2024 에서는?

### 7. 2024 는 왜 기본값을 바꿨나 (왜)

- 2021 규칙에서 수명이 포착되는 조건은 무엇이었나? 그 규칙이 **어디에만** 있었나?
- ★ 트레이트 안의 `impl Trait`·`async fn` 은 2021 에서 어떻게 포착했나? 2024 는 무엇에 맞춘 것인가?
- 「2024 는 더 관대해졌다」는 맞는 말인가?

### 8. ★★ `use<..>` 로 할 수 있는 것과 없는 것 (경계)

- `use<'a>`·`use<>` 는 각각 무엇을 뜻하는가? 에디션에 매이는가?
- ★★ `use<>` 로 **타입 파라미터**를 포착에서 빼려 하면 무엇이 되는가? 그 에러에 **번호**가 있는가?
- 2021 크레이트에서 2024 로 옮기기 전에 문제 자리를 찾는 **린트 이름**은? 켜면 컴파일이 실패하는가?

### 9. ★ RPITIT 와 `dyn` (경계)

- `impl Trait` 를 돌려주는 트레이트 메서드가 있으면 `Box<dyn Trait>` 가 되는가? 안 되면 번호와 이유는?
- `dyn` 이 필요하면 반환 타입을 무엇으로 바꾸는가 — 그 대가는?

### 10. ★ 인자 위치 `impl Trait` 와 단형화 (연결)

- 인자 위치 `impl Trait` 함수는 호출된 타입마다 **몇 벌** 생길 수 있는가 — 31번의 무엇이 그대로 적용되나?
- 29번의 `impl Into<String>` 인자는 이 주제의 어느 자리인가?

### 11. 이 주제와 에디션 연혁 (연결)

- ★★ `history/rust/02-에디션.md` 가 이미 적은 것과 이 주제가 **더한 것**은 각각 무엇인가?
- 같은 갈래에서 **2024 에디션에서만** 되는 문법이 또 무엇이 있었나?
- ★ 이 주제의 결론 중 **에디션과 무관한 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
