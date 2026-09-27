# rust/syntax/21 — `Option` 과 조합 메서드 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex` 다.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ 이 주제의 절반은 **문법이 아니라 소유권**을 묻는다. 「컴파일이 되나」를 먼저 답하라.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `map` 을 건 뒤에 원본을 한 번 더 쓰면 (예측)

```rust
// b21-05.rs
// ex.rs
// map 은 self 를 소비한다 — 뒤에서 원본을 다시 쓰면
fn main() {
    let name: Option<String> = Some(String::from("postgres"));
    let len = name.map(|s| s.len());
    println!("길이 {:?}", len);
    println!("원본 {:?}", name);
}
```

- 컴파일되는가? 안 되면 **에러 번호**는 무엇인가?
- 진단은 어느 줄을 범인으로 가리키는가 — `map` 줄인가 `println!` 줄인가?
- ★ 진단 안에 `Option::<T>::map` 의 **무엇**이 인용되는가?
- `help` 는 **둘**이다. 각각 무엇이며 왜 하나에는 단서가 붙어 있는가?
- `Option<String>` 이 아니라 `Option<u16>` 이었으면 결과가 달랐겠는가?

### 2. ★★ 빌린 `Option<String>` 에 `map` 을 걸면 (예측)

```rust
// b21-06.rs
// ex.rs
// 빌린 Option 안에서 값을 꺼내려 하면 — as_ref 가 없는 판
fn describe(cfg: &Option<String>) -> usize {
    match cfg {
        Some(s) => s.len(),
        None => 0,
    }
}

fn wrong(cfg: &Option<String>) -> Option<usize> {
    cfg.map(|s| s.len())
}

fn main() {
    let cfg = Some(String::from("postgres"));
    println!("{} {:?}", describe(&cfg), wrong(&cfg));
}
```

- `describe` 와 `wrong` 중 **어느 쪽이** 거부되는가?
- 에러 번호는 1번과 같은가 다른가? 다르다면 **무엇이 다른 상황**인가?
- `match cfg` 는 통과하는데 `cfg.map(…)` 은 안 되는 이유는 무엇인가?
- 처방은 무엇이며, 고친 뒤 반환 타입은 어떻게 되는가?

### 3. ★★ 대체값에 부작용을 달면 몇 번 돌까 (예측)

```rust
// b21-04.rs
// ex.rs
// unwrap_or 와 unwrap_or_else — 언제 대체값을 만드나. 부작용으로 증명한다
fn fallback() -> u16 {
    println!("  [부작용] fallback() 이 돌았다");
    9999
}

fn main() {
    let found: Option<u16> = Some(443);
    let missing: Option<u16> = None;

    println!("A 있음 + unwrap_or(fallback())");
    println!("  결과 {}", found.unwrap_or(fallback()));

    println!("B 있음 + unwrap_or_else(fallback)");
    println!("  결과 {}", found.unwrap_or_else(fallback));

    println!("C 없음 + unwrap_or(fallback())");
    println!("  결과 {}", missing.unwrap_or(fallback()));

    println!("D 없음 + unwrap_or_else(fallback)");
    println!("  결과 {}", missing.unwrap_or_else(fallback));
}
```

- `[부작용]` 줄은 **몇 번** 찍히는가?
- A·B·C·D 중 **어디서** 찍히는가?
- ★ 값이 `Some` 인데도 `fallback()` 이 도는 경우가 있는가 — 있다면 왜인가?
- 그래서 대체값이 **문자열 할당**일 때는 어느 쪽을 써야 하는가?
- 같은 규칙이 적용되는 메서드 쌍을 **셋** 더 댈 수 있는가?

### 4. ★ `?` 를 `Option` 을 돌려주는 함수에서 쓰면 (예측)

```rust
// b21-08.rs
// ex.rs
// ? 는 Option 에서도 된다 — None 이면 그 자리에서 None 을 반환한다
fn first_word(s: &str) -> Option<&str> {
    let head = s.split_whitespace().next()?;
    let first = head.get(0..1)?;
    Some(first)
}

fn both(a: &str, b: &str) -> Option<String> {
    let x = first_word(a)?;
    let y = first_word(b)?;
    Some(format!("{}{}", x, y))
}

fn main() {
    println!("{:?}", both("alpha beta", "gamma"));
    println!("{:?}", both("alpha beta", "   "));
    println!("{:?}", both("", "gamma"));
}
```

- 세 줄의 출력은 각각 무엇인가?
- `both("alpha beta", "   ")` 이 그렇게 되는 이유는 무엇인가?
- ★ `?` 가 `Option` 에서 되는 **조건**은 무엇인가?
- 이 함수의 반환 타입을 `Result<…>` 로 바꾸면 무슨 일이 생기는가?
- `?` 대신 `and_then` 으로 쓰면 코드가 어떻게 달라지는가?

### 5. ★ 봉투를 열었는데 비어 있으면 (예측)

```rust
// b21-01.rs
// ex.rs
// unwrap 이 None 을 만나면 — 마커는 전부 표준 오류로 찍는다
fn find(v: &[i32], t: i32) -> Option<usize> {
    v.iter().position(|&x| x == t)
}

fn main() {
    let table = [10, 20, 30];
    eprintln!("찾음 {:?}", find(&table, 20));
    let i = find(&table, 99).unwrap();
    eprintln!("여기는 안 온다 {}", i);
}
```

- 종료 코드는 얼마인가?
- 패닉 메시지 **본문**을 한 글자도 안 틀리게 적을 수 있는가?
- 그 아래 `note:` 줄에는 무엇이 적히는가?
- 같은 자리를 `expect("표에는 99 가 반드시 …")` 로 바꾸면 **무엇이 달라지고 무엇이 그대로인가**?
- 이 프로그램이 마커를 `eprintln!` 으로 찍은 이유는 무엇인가?

### 6. ★ 빌린 자리에서 소유권을 꺼내면 무엇이 남나 (예측)

```rust
// b21-09.rs
// ex.rs
// take 와 replace — 빌린 자리에서 소유권을 꺼내는 두 가지
#[derive(Debug)]
struct Slot {
    payload: Option<String>,
}

impl Slot {
    fn consume(&mut self) -> Option<String> {
        self.payload.take()
    }
    fn swap(&mut self, next: &str) -> Option<String> {
        self.payload.replace(String::from(next))
    }
}

fn main() {
    let mut slot = Slot { payload: Some(String::from("첫 짐")) };
    println!("처음      {:?}", slot);

    let old = slot.swap("둘째 짐");
    println!("replace 뒤 {:?} · 돌려받은 것 {:?}", slot, old);

    let got = slot.consume();
    println!("take 뒤    {:?} · 꺼낸 것 {:?}", slot, got);

    let again = slot.consume();
    println!("또 take    {:?} · 꺼낸 것 {:?}", slot, again);

    println!("get_or_insert {:?}", slot.payload.get_or_insert(String::from("기본값")));
    println!("끝        {:?}", slot);
}
```

- `take()` 를 **두 번** 부르면 두 번째는 무엇을 돌려주는가?
- `replace("둘째 짐")` 이 돌려주는 것은 무엇인가?
- `take()` 뒤 `slot.payload` 는 어떤 상태인가?
- `get_or_insert` 는 **이미 값이 있으면** 무엇을 하는가?
- 이 세 메서드가 없으면 `&mut self` 메서드 안에서 무엇이 막히는가?

### 7. 조합 메서드가 `None` 을 어떻게 옮기나 (왜)

- `map`·`and_then`·`filter` 에 `None` 을 넣으면 **클로저가 호출되는가**?
- `map` 과 `and_then` 을 가르는 기준은 무엇인가 — 한 줄로.
- `filter` 는 `Some` 을 `None` 으로 만들 수 있는가?
- `ok_or` 는 **무엇을 무엇으로** 바꾸는가? 그 뒤에 이어지는 주제는 몇 번인가?
- `unwrap_or_default()` 가 요구하는 트레이트 경계는 무엇인가?

### 8. `as_ref` 와 `as_mut` 는 왜 있나 (경계)

- `&Option<String>` 과 `Option<&String>` 은 같은 타입인가?
- `as_ref()` 를 부른 뒤 **원본은 살아 있는가**?
- `as_mut()` 으로 할 수 있고 `as_ref()` 로는 못 하는 일은 무엇인가?
- `as_ref().map(…)` 의 결과에서 `Option<T>` 를 얻으려면 무엇을 더 붙이는가?
- 시그니처의 어느 부분만 보면 「빌리나 가져가나」를 알 수 있는가?

### 9. `if let` 과 조합 메서드 중 무엇을 고르나 (경계)

- 같은 일을 네 가지로 쓸 수 있다 — 넷을 댈 수 있는가?
- 값이 **한 줄기로 이어질 때**와 **갈래마다 할 일이 다를 때** 중 조합 메서드가 맞는 쪽은?
- 체인이 몇 겹을 넘으면 되돌리는 것이 나은가?
- `unwrap` 을 쓰면 **타입에서 무엇이 사라지는가**?
- 라이브러리 코드에서 `unwrap`/`expect` 를 피하는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- `Option` 의 **정의**를 직접 적을 수 있는가? 그것이 정본인 주제는 몇 번인가?
- `Option<Box<T>>` 가 `Box<T>` 와 같은 크기인 현상의 이름은 무엇이고, 그것은 **보장인가 관찰인가**?
- `Option::take` 를 일반화한 표준 함수 둘은 무엇이며 정본은 몇 번 주제인가?
- Java 의 `Optional` 과 Rust 의 `Option` 이 **근본적으로 갈리는 지점**은 무엇인가?
- Go 는 「없음」을 무엇으로 표현하는가 — 그리고 그것이 왜 이 주제와 다른 모양이 되는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
