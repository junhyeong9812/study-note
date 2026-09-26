# rust/syntax/19 — 패턴 문법 전수 — 가드·`@`·or 패턴·구조 분해·매치 인체공학 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 특히 **바인딩의 타입**을 맞히는 문항이 본체다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.**
> ★ 타입이 궁금할 때 쓰는 기법 하나를 이 주제에서 배운다 — **일부러 틀린 타입을 적어 컴파일러가 찍게 하기**.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 글자가 똑같은 `Some(s)` 셋 (예측)

```rust
// b19-09.rs
// ex.rs
// 매치 인체공학 — &Option<String> 을 Some(s) 로 받으면 s 는 무엇인가
// let 로 받으면서 일부러 타입을 틀리게 적어 컴파일러가 실제 타입을 찍게 한다
fn main() {
    let owned: Option<String> = Some(String::from("가나"));

    let r: &Option<String> = &owned;
    match r {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    let mut owned2: Option<String> = Some(String::from("다라"));
    let m: &mut Option<String> = &mut owned2;
    match m {
        Some(s) => { let _probe: () = s; }
        None => {}
    }

    match owned2 {
        Some(s) => { let _probe: () = s; }
        None => {}
    }
}
```

- 에러가 **몇 개** 나는가?
- 세 `Some(s)` 의 `s` 는 각각 어느 타입으로 찍히는가?
- 셋을 가르는 것은 패턴인가 대상 값인가?
- 이 기법(`let _probe: () = s;`)이 하는 일을 한 문장으로 적을 수 있는가?
- 각 경우에 매치 뒤 원본을 읽을 수 있는가?

### 2. ★★ 가드로 `i32` 전체와 `bool` 전체를 덮으면 (예측)

```rust
// b19-02.rs
// ex.rs
// 가드가 붙으면 완전성 검사가 그 팔을 「덮은 것으로 치지 않는다」
fn sign(n: i32) -> &'static str {
    match n {
        x if x < 0 => "음수",
        x if x == 0 => "영",
        x if x > 0 => "양수",
    }
}

fn flag(b: bool) -> &'static str {
    match b {
        true => "참",
        x if !x => "거짓",
    }
}

fn main() {
    println!("{} {}", sign(-1), flag(false));
}
```

- 컴파일되는가? 안 되면 번호와 **안 덮였다는 것**은 무엇인가?
- 진단의 `= note:` 한 줄이 이유를 그대로 말한다. 그 문장을 적을 수 있는가?
- 왜 컴파일러는 `x < 0`·`x == 0`·`x > 0` 이 전부라는 것을 모르는가?
- `bool` 쪽은 값이 둘뿐인데도 왜 같은 일이 일어나는가?
- 처방은 무엇인가?

### 3. ★★ or 패턴의 갈래마다 다른 이름을 묶으면 (예측)

```rust
// b19-05.rs
// ex.rs
// or 패턴의 규칙 — 모든 갈래가 「같은 이름들」을 묶어야 한다
enum Shape {
    Circle { r: f64 },
    Square { side: f64 },
    Rect { w: f64, h: f64 },
}

fn main() {
    let s = Shape::Rect { w: 2.0, h: 3.0 };
    let x = match s {
        Shape::Circle { r } | Shape::Square { side } => r,
        Shape::Rect { w, h } => w * h,
    };
    println!("{}", x);
}
```

- 에러가 몇 개이며 번호는 각각 무엇인가?
- 같은 번호가 **두 번** 나는 이유는 무엇인가?
- 딸려 오는 다른 번호 하나는 무엇이며 왜 나는가?
- 이름을 맞추되 **타입이 다르면** 어느 번호가 나는가?
- 그때 진단은 **어느 갈래의 타입을 기준**으로 삼는가?

### 4. ★ 가드 안에서 묶인 값을 함수에 넘기면 (예측)

```rust
// b19-12.rs
// ex.rs
// 가드는 「빌려서 볼 뿐」이다 — 가드 안에서 값을 가져가려 하면 막힌다
fn main() {
    let v = Some(String::from("가나"));
    fn takes(s: String) -> bool { s.len() > 3 }
    match v {
        Some(s) if takes(s) => println!("길다"),
        _ => println!("짧거나 없다"),
    }
}
```

- 에러 번호와 제목 줄은 무엇인가?
- `= note:` 가 대는 이유를 적을 수 있는가?
- 왜 그 규칙이 필요한가 — 가드가 거짓이면 무슨 일이 일어나야 하는가?
- 진단이 제안하는 고침은 무엇이고, 더 싼 고침은 무엇인가?

### 5. ★ 길이를 모르는 슬라이스를 셋까지만 덮으면 (예측)

```rust
// b19-08.rs
// ex.rs
// 길이를 모르는 슬라이스는 「몇 개짜리」를 다 덮어야 한다
fn shape(v: &[i32]) -> String {
    match v {
        [] => String::from("빈 것"),
        [only] => format!("하나 {}", only),
        [a, b] => format!("둘 {} {}", a, b),
    }
}

fn arr(a: [i32; 3]) -> i32 {
    match a {
        [x, y, z] => x + y + z,
    }
}

fn main() {
    println!("{} {}", shape(&[1, 2, 3]), arr([1, 2, 3]));
}
```

- 에러가 몇 개이며 **안 덮인 것**을 그대로 적을 수 있는가?
- 아래쪽 `[i32; 3]` 을 받는 `arr` 는 왜 에러가 안 나는가?
- `[head, tail @ ..]` 와 `[]` 두 팔이면 완전한가?
- `..` 를 한 패턴에 두 번 쓸 수 있는가?

### 6. ★ 세 겹 중첩을 한 패턴으로 내려가면 (예측)

```rust
// b19-06.rs
// ex.rs
// 구조 분해 — 구조체·열거형·튜플이 몇 겹이든 한 패턴으로 내려간다
#[derive(Debug)]
struct Point { x: i32, y: i32 }
#[derive(Debug)]
struct Line { from: Point, to: Point, label: Option<String> }

#[derive(Debug)]
enum Shape { Seg(Line), Dot(Point) }

fn read(s: &Shape) -> String {
    match s {
        // 세 겹을 한 줄에 — enum → struct → struct/Option
        Shape::Seg(Line { from: Point { x: x1, y: y1 },
                          to: Point { x: x2, y: y2 },
                          label: Some(name) }) =>
            format!("이름 있는 선 {} ({},{})\u{2192}({},{})", name, x1, y1, x2, y2),
        Shape::Seg(Line { from: Point { x: x1, .. }, label: None, .. }) =>
            format!("이름 없는 선, 시작 x={}", x1),
        Shape::Dot(Point { x: 0, y: 0 }) => String::from("원점"),
        Shape::Dot(Point { x, y }) => format!("점 ({},{})", x, y),
    }
}

fn main() {
    let a = Shape::Seg(Line { from: Point { x: 0, y: 0 }, to: Point { x: 3, y: 4 },
                              label: Some(String::from("빗변")) });
    let b = Shape::Seg(Line { from: Point { x: 7, y: 1 }, to: Point { x: 9, y: 1 }, label: None });
    let c = Shape::Dot(Point { x: 0, y: 0 });
    let d = Shape::Dot(Point { x: 2, y: 5 });
    for s in [&a, &b, &c, &d] { println!("{}", read(s)); }

    // let 도 패턴이다 — 함수 인자·for 도 마찬가지
    let Line { from: Point { x, .. }, .. } = Line {
        from: Point { x: 11, y: 12 }, to: Point { x: 0, y: 0 }, label: None };
    println!("let 으로 뽑은 x={}", x);
}
```

- 네 개의 `Shape` 가 각각 어느 팔에 걸리며 무엇이 찍히는가?
- `label: Some(name)` 은 무엇을 하는가 — 그것이 왜 팔을 둘로 가르나?
- `Point { x: x1, .. }` 의 `..` 와 `_` 는 무엇이 다른가?
- `Shape::Dot(Point { x: 0, y: 0 })` 처럼 **값을 그대로 적는** 것은 무엇을 뜻하는가?
- 마지막 `let Line { … } = …;` 이 보이는 사실은 무엇인가?

### 7. 가드가 보는 것 (왜)

- 패턴으로 `(x, x)` 를 적을 수 있는가? 못 한다면 무엇으로 대신하는가?
- 가드가 or 패턴에 붙으면 **어느 갈래**에 걸리는가?
- 패턴 자리에 바깥 변수 이름을 쓰면 무슨 일이 생기는가?
- 가드에서 바깥 변수를 읽을 수 있는가?

### 8. `@` 와 or 패턴의 버전 (경계)

- `@` 는 무엇을 동시에 하는가 — 없으면 무엇을 포기해야 하는가?
- `Some(1 | 3)` 처럼 **중첩 자리**의 or 패턴은 어느 버전부터인가?
- `v @ (1 | 3)` 처럼 `@` 가 or 를 감싸는 것은 어느 버전부터인가?
- 맨 앞의 `|` 는 써도 되는가?
- `let` 자리에서 or 패턴을 쓸 수 있는가? 조건이 있는가?

### 9. 매치 인체공학의 경계 (경계)

- 이 규칙은 어느 버전부터이며 **에디션과 관계**가 있는가?
- `&&Option<T>` 를 `Some(s)` 로 받으면 `s` 는 무엇인가?
- 패턴에 `&` 를 직접 적으면 무엇이 달라지는가 — 그때 필요한 조건은?
- `ref` / `ref mut` 가 왜 거의 안 쓰이게 됐는가?
- 그런데도 `ref` 가 아직 필요한 자리를 하나 댈 수 있는가?

### 10. 패턴이 쓰이는 자리 (연결)

- 패턴을 받는 자리를 **여섯** 댈 수 있는가?
- 그중 **반박 불가** 패턴만 받는 것은 어느 것들인가?
- E0408 · E0381 · E0507 · E0004 가 각각 어떤 상황에서 나는지 한 줄씩 말할 수 있는가?
- 매치 인체공학이 만들어 내는 것은 무엇이고, 그 규칙의 정본은 몇 번 주제인가?
- 완전성 검사의 정본은 몇 번이고, 반박 가능한 패턴을 쓰는 자리들은 몇 번인가?
- 슬라이스 자체의 정본은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
