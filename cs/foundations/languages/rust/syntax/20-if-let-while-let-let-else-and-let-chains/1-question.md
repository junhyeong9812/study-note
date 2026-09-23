# rust/syntax/20 — `if let`·`while let`·`let else`(1.65)·`let` 체인(2024 에디션·1.88) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ **이 주제의 문항 절반은 「어느 에디션에서 어떻게 되나」를 묻는다.**
> 에디션을 안 밝힌 답은 이 주제에서 틀린 답이다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex` 와
> `rustc --edition 2024 ex.rs -o ex && ./ex` 를 **둘 다** 던진다.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 이 주제의 절반이 안 돌아간다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 같은 파일을 2021 과 2024 에 각각 던지면 (예측)

```rust
// b20-05.rs
// ex.rs
// let 체인 — if let 을 && 로 잇는다. 어느 에디션에서 되나
fn lookup(k: &str) -> Option<u32> {
    match k { "a" => Some(1), "b" => Some(2), _ => None }
}

fn main() {
    let x = lookup("a");
    let y = lookup("b");
    if let Some(a) = x && let Some(b) = y && a < b {
        println!("둘 다 있고 {} < {}", a, b);
    } else {
        println!("아니다");
    }

    let mut src = vec![Some(1), Some(2), None, Some(3)];
    while let Some(item) = src.pop() && let Some(n) = item {
        println!("꺼냄 {}", n);
    }
    println!("남은 {:?}", src);
}
```

- 2021 에서 컴파일되는가? 안 되면 **에러 문구**는 무엇인가?
- 그 에러에 **번호**가 붙는가? `For more information …` 줄이 나오는가?
- 에러가 **몇 개**이며, 그 개수를 정하는 것은 `&&` 인가 `let` 인가?
- 2024 에서는 어떻게 되며 **출력은 무엇**인가?
- ★ `while let` 쪽 출력에서 **남은 벡터**가 `[Some(1), Some(2)]` 다. 왜 `Some(3)` 이 아니라 그것인가?
- 에디션만 맞으면 되는가, 버전도 필요한가?

### 2. ★★★ `Drop` 이 있는 임시값을 `if let` 조건에 두면 (예측)

```rust
// b20-06.rs
// ex.rs
// if let 의 「조건 자리 임시값」이 언제 죽나 — 에디션으로 갈린다
struct Noisy(&'static str);

impl Drop for Noisy {
    fn drop(&mut self) { println!("   drop {}", self.0); }
}

impl Noisy {
    fn peek(&self) -> Option<u32> { if self.0 == "있음" { Some(1) } else { None } }
}

fn main() {
    println!("A 참 갈래 진입 전");
    if let Some(v) = Noisy("있음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("A if 끝난 뒤");

    println!("B 거짓 갈래 진입 전");
    if let Some(v) = Noisy("없음").peek() {
        println!("   then {}", v);
    } else {
        println!("   else");
    }
    println!("B if 끝난 뒤");

    println!("C match 는 어떤가");
    match Noisy("있음").peek() {
        Some(v) => println!("   then {}", v),
        None => println!("   none"),
    }
    println!("C match 끝난 뒤");
}
```

- 2021 과 2024 의 출력에서 **갈리는 줄**은 몇 개이며 어디인가?
- A(참 갈래)는 두 에디션에서 같은가 다른가?
- B(거짓 갈래)에서 `drop 없음` 과 `else` 중 어느 것이 먼저 찍히는가 — 에디션별로 답하라.
- C(`match`)는 2024 에서 바뀌었는가?
- 그래서 「2024 의 이득을 보려고 `if let` 을 `match` 로 바꾸면」 어떻게 되는가?

### 3. ★★ 조건에서 `RefCell` 을 빌리고 `else` 에서 또 빌리면 (예측)

```rust
// b20-07.rs
// ex.rs
// 임시값이 언제 죽는지가 코드의 성패를 가른다 — 마커는 전부 표준 오류로 찍는다
use std::cell::RefCell;

fn main() {
    let cell = RefCell::new(None::<u32>);
    eprintln!("시작 {:?}", cell);
    if let Some(v) = *cell.borrow() {
        eprintln!("then {}", v);
    } else {
        *cell.borrow_mut() = Some(7);       // 조건의 빌림이 아직 살아 있으면 여기서 터진다
        eprintln!("else 에서 채웠다");
    }
    eprintln!("끝 {:?}", cell);
}
```

- 2021 에서 무슨 일이 일어나는가? 종료 코드는 무엇인가?
- 그때 나오는 메시지 본문을 적을 수 있는가?
- 2024 에서는 어떻게 되며 마지막 줄에 무엇이 찍히는가?
- 이 실험을 `Mutex` 로 했으면 증상이 어떻게 달라졌겠는가 — 왜 `RefCell` 을 썼는가?
- 이 프로그램이 마커를 `eprintln!` 으로 찍은 이유는 무엇인가?

### 4. ★★ `let else` 의 `else` 에 값을 적으면 (예측)

```rust
// b20-04.rs
// ex.rs
// let else 의 else 는 「나가야」 한다 — 값을 내면 거부된다
fn main() {
    let text = "가";
    let Ok(n) = text.parse::<u32>() else {
        0
    };
    println!("{}", n);

    let Some(m) = Some(1) else {
        println!("없다");
    };
    println!("{}", m);
}
```

- 에러가 몇 개이며 번호는 무엇인가?
- 진단이 **기대하는 타입**은 무엇이라고 적히는가?
- 두 에러의 `found` 쪽은 각각 무엇인가 — 둘째는 아무 값도 안 냈는데 왜 걸리는가?
- `= help:` 가 주는 처방은 **둘**이다. 무엇인가?
- 이 요구는 에디션에 달렸는가?

### 5. ★ `if let` 사슬로 열거형을 전부 다룬 뒤 변형을 늘리면 (예측)

```rust
// b20-09a.rs
// ex.rs
// if let 에는 완전성 검사가 없다 — 전. 변형 셋을 if let 사슬로 처리한다
#[derive(Debug)]
enum Event { Click, Key, Scroll }

fn label(e: &Event) -> &'static str {
    if let Event::Click = e { "클릭" }
    else if let Event::Key = e { "키" }
    else { "스크롤" }
}

fn main() {
    for e in [Event::Click, Event::Key, Event::Scroll] {
        println!("{:?} {}", e, label(&e));
    }
}
```

- `Event` 에 `Drag` 를 더하면 에러가 몇 개 나는가? 경고는?
- `Drag` 를 넣어 돌리면 무엇이 찍히는가?
- 같은 일을 `match` + `_` 로 했을 때와 무엇이 같고 무엇이 다른가?
- 그래서 열거형을 전부 다루는 자리에는 무엇을 써야 하는가?

### 6. `let else` 가 다른 둘과 갈리는 점 (왜)

- `let else` 로 꺼낸 값은 **어디에** 남는가? `if let` 과 비교하면?
- 그 차이가 코드 모양에 무엇을 하는가?
- `else` 에 적을 수 있는 것을 **넷** 댈 수 있는가?
- `let else` 는 어느 버전부터이며 에디션과 관계가 있는가?
- `else` 에 `else if` 를 붙일 수 있는가?

### 7. `if let` 이 식이라는 것 (경계)

- `let n = if let … { … } else { … };` 가 되는 조건은 무엇인가?
- `else` 가 없으면 본문의 타입은 무엇이어야 하는가?
- `else if let` 으로 이을 수 있는가? 몇 개까지 이으면 되돌려야 하는가?
- `while let` 에서 조건이 처음부터 안 맞으면 몇 번 도는가?
- `while let` 이 `for` 와 갈리는 자리는 어디인가?

### 8. 무엇을 고르나 (경계)

- `match`·`if let`·`let else`·조합 메서드를 고르는 기준을 각각 한 줄로 댈 수 있는가?
- 접개를 쓸 때 **잃는 것**은 무엇인가?
- `match` 에 `_ => {}` 가 보이면 무엇을 생각해야 하는가?
- 내 열거형을 전부 다루는 자리의 기본값은 무엇인가?

### 9. 에디션 대조 (연결)

- 이 주제에서 에디션으로 갈리는 것을 **둘** 대고, 각각 **어느 쪽이 되고 어느 쪽이 안 되는지** 말하라.
- `let else` 는 에디션으로 갈리는가?
- `rustc` 에 `--edition` 을 안 주면 어느 에디션인가?
- 2024 에디션은 어느 버전에서 안정됐고, `let` 체인은 어느 버전부터인가?
- 에디션 변경 **전수**는 몇 번 주제이고, 에디션 제도의 **역사**는 어디가 정본인가?

### 10. 다른 주제와 잇기 (연결)

- `let else` 가 요구하는 `!` 타입의 정본은 몇 번 주제인가?
- 완전성 검사의 정본은 몇 번이고, 이 주제는 그것과 어떤 관계인가?
- 반박 가능/불가 패턴의 구분은 몇 번 주제에서 나왔는가?
- `while let` 이 얹히는 루프 문법의 정본은 몇 번인가?
- (5)의 임시값 실험이 창으로 쓴 것은 무엇이며 그 정본은 몇 번인가?
- 접개 대신 쓰는 **넷째 길**(조합 메서드)은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
