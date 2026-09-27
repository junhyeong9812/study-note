# rust/syntax/17 — 열거형과 데이터를 담는 변형 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 문법을 아는지가 아니라 **컴파일러가 무엇을 거부하고
> 그때 어느 문구를 쓰는지**, 그리고 **봉투가 몇 바이트인지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 다른 언어를 컴파일하는 셈이다.
> ★ 크기·배치를 묻는 문항은 **답이 「언어 보장인가 관찰인가」까지** 답해야 한다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 구조체 변형에 선언에 없는 칸을 적으면 (예측)

```rust
// b17-04.rs
// ex.rs
// 불가능한 상태 — 후. 열거형으로 바꾸면 그 모순을 「적을 수가 없다」
#[derive(Debug)]
enum Conn {
    Idle,
    Connected { session_id: u32 },
    Failed(String),
}

fn report(c: &Conn) -> String {
    match c {
        Conn::Idle => String::from("대기"),
        Conn::Connected { session_id } => format!("연결됨 세션={}", session_id),
        Conn::Failed(e) => format!("실패 {}", e),
    }
}

fn main() {
    println!("{}", report(&Conn::Idle));
    println!("{}", report(&Conn::Connected { session_id: 7 }));
    println!("{}", report(&Conn::Failed(String::from("타임아웃"))));
    // ★ 앞 판의 모순을 그대로 적어 본다 — 연결됐는데 세션이 없고 에러도 있는 상태
    let bad = Conn::Connected { session_id: 7, error: String::from("타임아웃") };
    println!("{:?}", bad);
}
```

- 컴파일되는가? 안 되면 에러 번호와 제목 줄은 무엇인가?
- 진단의 `= note:` 한 줄이 무엇을 말하는가?
- 앞선 세 `report` 호출은 왜 문제가 없는가?
- 같은 모순을 **구조체 + 플래그**로 적으면 어떻게 되는가 — 컴파일러가 막는가?
- 그 두 판이 **표현할 수 있는 값의 가짓수**는 각각 몇인가?

### 2. ★★ 데이터를 담은 변형이 있는 열거형에 `as i32` 를 쓰면 (예측)

```rust
// b17-06.rs
// ex.rs
// 데이터를 담은 변형이 하나라도 있으면 `as` 로 정수를 못 꺼낸다
enum Mixed {
    Zero,
    One(u32),
}

fn main() {
    println!("{}", Mixed::Zero as i32);
    let m = Mixed::One(7);
    println!("{}", m as i32);
}
```

- 에러가 **몇 개** 나며 번호는 무엇인가?
- 짐이 없는 `Mixed::Zero` 에서도 막히는가? 그렇다면 그 판정은 **무엇 단위**로 내려지는가?
- 진단 한 줄이 규칙을 그대로 말한다. 그 문장에 나오는 두 낱말(`unit-only`·`field-less`)은 무엇을 뜻하는가?
- 같은 열거형에 `Zero = 0` 처럼 **판별값까지** 적으면 어느 번호가 추가로 나는가?
- 그 번호가 요구하는 것을 붙이면 `as` 는 통과하는가?

### 3. ★★ `Option` 을 씌웠을 때 크기가 느는 타입과 안 느는 타입 (예측)

```rust
// b17-10.rs
// ex.rs
// 니치 최적화 — Option 을 씌워도 크기가 안 느는 타입들
use std::num::NonZeroU32;

#[derive(Debug)]
enum Never2 { A(u32), B(u32) }          // 데이터 변형 둘 — 태그가 따로 필요하다

fn row(name: &str, bare: usize, opt: usize) {
    println!("{:<22} {:>3} {:>3}  {}", name, bare, opt,
             if bare == opt { "니치 씀" } else { "태그 따로" });
}

fn main() {
    println!("{:<22} {:>3} {:>3}", "타입", "T", "Option<T>");
    row("Box<i32>",      size_of::<Box<i32>>(),      size_of::<Option<Box<i32>>>());
    row("&i32",          size_of::<&i32>(),          size_of::<Option<&i32>>());
    row("&mut i32",      size_of::<&mut i32>(),      size_of::<Option<&mut i32>>());
    row("String",        size_of::<String>(),        size_of::<Option<String>>());
    row("Vec<u8>",       size_of::<Vec<u8>>(),       size_of::<Option<Vec<u8>>>());
    row("NonZeroU32",    size_of::<NonZeroU32>(),    size_of::<Option<NonZeroU32>>());
    row("char",          size_of::<char>(),          size_of::<Option<char>>());
    row("bool",          size_of::<bool>(),          size_of::<Option<bool>>());
    row("u8",            size_of::<u8>(),            size_of::<Option<u8>>());
    row("u32",           size_of::<u32>(),           size_of::<Option<u32>>());
    row("f64",           size_of::<f64>(),           size_of::<Option<f64>>());
    row("()",            size_of::<()>(),            size_of::<Option<()>>());
    row("Never2",        size_of::<Never2>(),        size_of::<Option<Never2>>());
    let get = |e: &Never2| match e { Never2::A(n) | Never2::B(n) => *n };
    let (a, b) = (Never2::A(1), Never2::B(2));
    println!("{:?}={} {:?}={}", a, get(&a), b, get(&b));
    // 니치가 겹겹이 쌓인다
    println!("Option<Option<bool>> {}  Option<Option<Option<bool>>> {}",
             size_of::<Option<Option<bool>>>(), size_of::<Option<Option<Option<bool>>>>());
    println!("Result<Box<i32>, ()> {}  Result<u32, u32> {}",
             size_of::<Result<Box<i32>, ()>>(), size_of::<Result<u32, u32>>());
}
```

- 표의 13행에서 **`T` 와 `Option<T>` 의 크기가 같은 것**을 전부 골라라.
- 크기가 **1 → 2**, **4 → 8**, **8 → 16** 으로 느는 것들의 공통점은 무엇인가?
- `()` 는 0바이트인데 `Option<()>` 은 몇 바이트인가? 왜인가?
- `Option<Option<Option<bool>>>` 은 몇 바이트인가?
- 이 표의 값 중 **std 가 문서로 약속한 것**은 몇 행이고 나머지는 무엇인가?

### 4. ★★ 1바이트짜리 `Option` 을 정수로 옮겨 담아 읽으면 (예측)

```rust
// b17-11.rs
// ex.rs
// 태그가 어디 사는가 — 1바이트짜리를 정수로 옮겨 담아 직접 읽는다
use std::num::NonZeroU8;

fn main() {
    // bool 은 0·1 만 쓴다. 남는 값 하나가 None 자리가 된다
    let n: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(None) };
    let f: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(false)) };
    let t: u8 = unsafe { std::mem::transmute::<Option<bool>, u8>(Some(true)) };
    println!("Option<bool> 1바이트: None={} Some(false)={} Some(true)={}", n, f, t);

    // NonZeroU8 은 0 을 못 쓴다. 그 0 이 None 자리다
    let n2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(None) };
    let s2: u8 = unsafe { std::mem::transmute::<Option<NonZeroU8>, u8>(NonZeroU8::new(200)) };
    println!("Option<NonZeroU8> 1바이트: None={} Some(200)={}", n2, s2);

    // 참조는 널이 될 수 없다. 그 널이 None 자리다 — 널 포인터 최적화
    let x = 41i32;
    let r: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(Some(&x)) };
    let nn: usize = unsafe { std::mem::transmute::<Option<&i32>, usize>(None) };
    println!("Option<&i32>: None={} Some(&x)가 &x 주소와 같나={}",
             nn, r == (&x as *const i32 as usize));

    // 니치가 없으면 태그를 따로 둔다 — u8 은 256가지를 다 쓴다
    println!("Option<u8> 크기={} (u8 크기={})", size_of::<Option<u8>>(), size_of::<u8>());
    // 같은 값인데 서로 다른 변형임을 구별하는 표식
    let a: Option<u8> = Some(0);
    let b: Option<u8> = None;
    println!("판별자가 다른가={}",
             std::mem::discriminant(&a) != std::mem::discriminant(&b));
}
```

- `Option<bool>` 의 세 값은 각각 어느 정수로 나오는가?
- `Option<NonZeroU8>` 의 `None` 은 어느 값인가? 왜 하필 그 값인가?
- `Option<&i32>` 의 `None` 은 무엇이고, `Some(&x)` 는 `x` 의 주소와 같은가?
- 이 중 **실행마다 달라지는 값**은 무엇인가 — 그래서 이 프로그램은 그것을 어떻게 피했는가?
- `Option<u8>` 은 왜 이 방법으로 못 읽는가?

### 5. ★ 이 두 열거형에 `#[derive(Clone, Copy)]` 와 `#[derive(Default)]` 를 붙이면 (예측)

```rust
// b17-08.rs
// ex.rs
// derive 가 거부되는 두 자리 — Copy 와 Default
#[derive(Clone, Copy)]
enum Payload {
    Num(u32),
    Text(String),      // String 은 Copy 가 아니다
}

#[derive(Default)]
enum Mode {
    Fast,
    Slow,
}

fn main() {
    let _ = Payload::Num(1);
    let _ = Mode::Fast;
}
```

- 에러가 몇 개이며 번호는 각각 무엇인가?
- `Copy` 쪽 진단이 **짚는 것**은 변형인가 칸인가?
- `Default` 쪽 진단은 `help:` 를 **몇 개** 주는가? 왜 그 개수인가?
- `Default` 를 파생하려면 무엇을 붙여야 하고, 그것은 **어느 버전부터**인가?
- `Clone` 만 파생하면 통과하는가?

### 6. ★ 열거형이 자기 자신을 담으면 (예측)

```rust
// b17-12.rs
// ex.rs
// 재귀 열거형은 크기를 못 정한다
#[derive(Debug)]
enum Tree {
    Leaf(i32),
    Node(Tree, Tree),
}

fn main() {
    let t = Tree::Node(Tree::Leaf(1), Tree::Leaf(2));
    println!("{:?}", t);
}
```

- 에러 번호는 무엇이며 **몇 개**가 나는가?
- 진단이 「어느 칸이 문제인지」를 무엇이라고 부르는가?
- `help:` 가 대는 세 가지 해결책은 무엇인가?
- 두 번째 에러는 첫 번째와 어떤 관계인가?
- 고친 뒤 그 타입의 `size_of` 는 몇이 되며, 그 숫자는 어디서 왔는가?

### 7. 변형은 타입인가 (왜)

- `Message::Quit` 의 **타입**은 무엇인가?
- `fn f(m: Message::Quit)` 를 쓸 수 있는가?
- 튜플 변형 `Message::Move` 를 `.map(...)` 에 인자 없이 넘길 수 있는가? 왜인가?
- 이름 있는 구조체와 **같은 것**·**다른 것**을 하나씩 대라.
- `use Message::*;` 를 습관으로 쓰면 다음 주제에서 어떤 사고가 나는가?

### 8. 판별값의 규칙 (경계)

- 판별값을 안 적으면 어떤 값이 붙는가 — `enum Step { A, B, C = 10, D }` 에서 `D` 는 몇인가?
- 판별값만 있는 열거형의 `size_of` 는 무엇이 정하는가 — 변형 개수인가 값의 크기인가?
- 정수에서 열거형으로 가는 `as` 가 있는가? 없으면 무엇으로 대신하는가?
- 판별값 자체를 **보장으로** 쓸 수 있는 경우는 언제인가?
- `std::mem::discriminant` 와 `as` 는 무엇이 다른가?

### 9. `Option` 과 `Result` 의 정체 (경계)

- `Option<T>` 의 정의를 `enum` 문법으로 한 줄로 적을 수 있는가?
- 내가 똑같은 것을 만들면 std 것과 다른 점이 **셋** 있다. 무엇인가?
- `None` 이 「null 과 같은 것」인가? 메모리에서는 어떻고 타입에서는 어떤가?
- `Result<u32, u32>` 는 몇 바이트이며 왜 그 값인가?
- 이 사실이 「Rust 에는 null 이 없다」는 말과 어떻게 이어지는가?

### 10. 불가능한 상태를 지우는 설계 (왜)

- 「이 불리언이 참이면 저 필드는 반드시 있다」는 주석을 봤을 때 무엇을 해야 하는가?
- 그 변환이 주는 이득을 **「실수를 덜 한다」보다 강한 말**로 적을 수 있는가?
- 열거형으로 바꾸면 **무엇이 대신 어려워지나** — 대가를 하나 대라.
- 변형이 계속 늘 것 같으면 무엇을 대신 쓰는가?
- 변형 하나가 유독 클 때 생기는 문제와 그 처방은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- E0559 · E0605 · E0732 · E0204 · E0665 · E0072 · E0391 이 각각 어떤 상황에서 나는지 한 줄씩 말할 수 있는가?
- `impl`·연관 함수·`Self` 의 정본은 몇 번 주제인가 — 이 주제는 그것을 어떻게 쓰는가?
- `Copy` 파생이 막히는 이유의 뿌리는 몇 번 주제인가?
- 이 주제가 만든 값을 **꺼내는** 것은 몇 번 주제이고, 그 주제의 안전망은 무엇에 기대는가?
- `Box` 와 재귀 타입의 정본은 몇 번이고, 여기서는 어디까지 다뤘는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
