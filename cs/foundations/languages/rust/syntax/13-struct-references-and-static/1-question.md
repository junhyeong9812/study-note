# rust/syntax/13 — 구조체에 참조 담기·`'static`의 두 의미 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **참조 필드 하나가 타입 전체에 무엇을 하는지**와
> **어느 자리에서 어느 번호가 나는지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o /tmp/ex && /tmp/ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.**
> ★ 이 주제의 진단은 **번호가 넷으로 갈린다.** 「수명이 없다」 한 가지를 묻는 것이 아니라
> **어느 자리에서 없느냐**를 묻는 것이니, 답할 때 **번호와 자리를 같이** 대라.
> ★ `'static` 의 **두 뜻**은 [**12번 주제**](../12-lifetime-annotations-and-elision/)가 정본이다 —
> 여기서는 **필드 자리에서 무엇이 되나**만 묻는다(11번 문항).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 참조 필드 구조체에 `impl` 을 수명 없이 적으면 (예측)

```rust
struct Tag<'a> {
    name: &'a str,
}

impl Tag {
    fn name(&self) -> &str { self.name }
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s };
    println!("{}", t.name());
}
```

- 컴파일되는가? 안 되면 **에러 번호와 제목 줄**은 무엇인가?
- 그 번호가 **E0106 이 아니라면** 무엇이 다른 것인가 — 한 문장으로 적어 보라.
- `impl<'a> Tag<'a>` 와 `impl Tag<'_>` 는 **둘 다** 되는가?
- 그 둘은 **같은 것**인가 — `impl Tag<'_>` 안에서 `fn name(&self) -> &'a str` 를 적으면 무엇이 나오는가?

### 2. ★★ 참조 필드 구조체를 반환하는 함수의 수명 칸 (예측)

```rust
struct Tag<'a> {
    name: &'a str,
}

fn tag_of(s: &str) -> Tag {
    Tag { name: s }
}

fn longer_tag(a: &str, b: &str) -> Tag<'_> {
    if a.len() >= b.len() { Tag { name: a } } else { Tag { name: b } }
}

fn main() {
    let x = String::from("가나다");
    let y = String::from("라");
    println!("{} {}", tag_of(&x).name, longer_tag(&x, &y).name);
}
```

- 두 함수 중 **막히는 것은 어느 쪽**이고, 나머지 쪽에서는 무엇이 나오는가?
- `-> Tag` 는 **컴파일되는가** — 그렇다면 `impl Tag` 가 거부된 것과 왜 다른가?
- `'_` 를 적었는데도 막히는 이유를 한 문장으로 적을 수 있는가?
- 이 파일에서 **인자 자리**의 `&str` 들은 왜 아무 말도 안 듣는가?

### 3. ★★ 연관 함수 `new` 의 인자 수명 (예측)

```rust
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Tag<'a> {
    fn new(name: &str) -> Self {
        Tag { name }
    }
}

fn main() {
    let s = String::from("제목");
    println!("{}", Tag::new(&s).name);
}
```

- 컴파일되는가? 안 되면 **에러 번호**는 무엇인가?
- `Self` 가 여기서 가리키는 **정확한 타입**을 적어 보라.
- `&self` 가 있는 메서드였다면 **왜 이 일이 안 일어나는가**?
- 같은 일을 **자유 함수** `fn tag_of(name: &str) -> Tag<'_>` 로 쓰면 통과하는가 — 왜인가?

### 4. ★★ 참조 필드 구조체에 `derive(Debug, Clone, Copy)` (예측)

```rust
#[derive(Debug, Clone, Copy)]
struct Tag<'a> {
    name: &'a str,
    hits: u32,
}

fn main() {
    let s = String::from("제목");
    let t = Tag { name: &s, hits: 3 };
    let u = t;
    println!("{:?} / {:?}", t, u);
    println!("{} {}", t.name.len(), u.hits);
    println!("size_of = {}", std::mem::size_of::<Tag>());
}
```

- 컴파일되는가? `let u = t;` 다음 줄에서 `t` 를 쓸 수 있는가?
- 된다면 `size_of` 는 몇이 찍히며 그 숫자는 **무엇 무엇의 합**인가?
- 같은 구조체의 필드를 `String` 으로 바꾸면 어떻게 되는가 — **번호까지** 대라.
- 필드를 `&'a mut u32` 로 바꾸면 **에러가 몇 개** 나는가? 그중 `Clone` 쪽 `= note:` 는 무엇을 말하는가?

### 5. ★★ 자기 참조 구조체를 `fn new` 로 만들면 (예측)

```rust
struct SelfRef<'a> {
    data: String,
    first: &'a str,
}

impl<'a> SelfRef<'a> {
    fn new(data: String) -> Self {
        let first = &data[..3];
        SelfRef { data, first }
    }
}

fn main() {
    let s = SelfRef::new(String::from("가나다"));
    println!("{} {}", s.data, s.first);
}
```

- 에러가 **몇 개** 나고 번호는 각각 무엇인가?
- 진단에 `lifetime 'a defined here` 가 **어느 줄**을 가리키는가 — 그 줄이 뜻하는 것은?
- `returning this value requires that data is borrowed for 'a` 를 **평서문 한 문장**으로 옮겨 보라.
- `first` 를 **바깥 문자열**로 돌리면(예: 다른 변수의 슬라이스) 같은 타입이 컴파일되는가?

### 6. ★ 같은 코드에 `Drop` 만 달면 (예측)

```rust
struct Tag<'a> {
    name: &'a str,
}

impl<'a> Drop for Tag<'a> {
    fn drop(&mut self) { println!("Tag 해제: {}", self.name); }
}

fn main() {
    let t;
    let s = String::from("제목");
    t = Tag { name: &s };
    println!("{}", t.name);
}
```

- `impl Drop` 블록을 **지우면** 이 코드는 통과하는가?
- 안 지우면 무엇이 나오는가 — **번호와 마지막 `= note:` 한 줄**까지 대라.
- `Drop` 이 왜 빌림 검사를 **더 엄하게** 만드는가?
- 이 코드를 고치는 가장 짧은 방법은 무엇인가 — 표기를 고치는가, 다른 것을 고치는가?

### 7. 수명 파라미터가 어디까지 번지나 (왜)

- 필드 하나를 `&'a str` 로 두면 `<'a>` 를 적어야 하는 자리를 **일곱 개** 셀 수 있는가?
- `struct Doc { tags: Vec<Tag> }` 에는 `&` 가 한 글자도 없다. 그런데 왜 막히는가?
- **전파가 멈추는 자리**가 하나 있다 — `struct Wrapper<T> { inner: T }` 는 왜 `<'a>` 가 필요 없는가?
- 그렇다면 `Vec<T>`·`Option<T>` 의 선언에 수명이 없는데도 `Vec<Tag<'a>>` 가 되는 것은 같은 이유인가?

### 8. ★★ 같은 프로그램 두 판에서 `'a` 를 세면 (경계)

구조체 둘(`Tag`·`Doc`) · `impl` 둘 · 자유 함수 하나 · `main` 으로 된 **36줄짜리 같은 프로그램**을
① 필드를 **참조**로 둔 판과 ② 필드를 **`String`** 으로 둔 판, 두 벌로 쓴다. 출력은 한 글자도 같다.

- 두 판의 **줄 수**와 **출력**이 같다면, 무엇이 달라진 것인가?
- `grep -o "'a" ex.rs | wc -l` 로 세면 두 판의 숫자는 각각 대략 몇인가 — **자릿수라도** 맞혀 보라.
- ★ **`grep -c` 를 쓰면 왜 다른 숫자가 나오는가**?
- 판 ②에서 **참조가 사라진 것**인가? `fn name(&self) -> &str` 은 여전히 참조를 돌려주는데?

### 9. 수명 하나로 묶기 대 둘로 가르기 (경계)

- `struct Pair<'a> { key: &'a str, val: &'a str }` 에서 `'a` 는 두 입력의 무엇이 되는가?
- 몸통을 **한 글자도 안 고치고** `<'a, 'b>` 로만 바꿨더니 통과했다 — 무엇이 풀린 것인가?
- 그렇다면 **처음부터 갈라 적는 것**이 늘 이득인가?
- 12번의 `'long: 'short` 는 이 이야기의 **어느 다음 수**인가?

### 10. 선언만 하고 안 쓰는 수명 파라미터 (경계)

- `struct Tag<'a> { name: String }` 은 **경고인가 에러인가**? 번호까지 대라.
- 언어가 이것을 금지하는 이유를 **변성·drop check** 라는 말로 한 줄 적을 수 있는가?
- 그 진단의 `help:` 가 제안하는 **세 가지**는 무엇인가?
- 참조 필드를 소유 필드로 되돌리는 리팩토링에서 **가장 먼저 지워야 할 것**은 어디인가?

### 11. 필드 자리의 `'static` (경계)

- `struct Label { text: &'static str }` 에는 왜 `<'a>` 가 없는가?
- 여기에 지역 `String` 의 참조를 넣으면 무엇이 나오는가 — 번호와 **라벨 한 줄**까지.
- `&'static str` 필드 · `&'a str` 필드 · `String` 필드 — 셋을 **「넣을 수 있는 값」과 「전파」** 두 칸으로 갈라 적어 보라.
- ★ `T: 'static`(트레이트 경계)은 이 표의 어느 칸인가 — **정본은 몇 번 주제**인가?

### 12. 다른 주제와 잇기 (연결)

- E0106 · E0726 · E0261 · E0621 · E0392 가 각각 **어느 자리**에서 나는지 한 줄씩 말할 수 있는가?
- 자기 참조의 **처방**은 몇 번 주제가 정본이고, 이 주제는 그 위에 **무엇을 더했는가**?
- `&T` 는 `Copy` 이고 `&mut T` 는 아니라는 사실의 **정본**은 몇 번인가?
- 값이 이동하면 **바이트가 복사된다**는 전제의 정본은 몇 번인가?
- 참조 필드 구조체를 **함수 인자로 받을 때** `String` 과 `&str` 중 무엇을 고르나 — 그 이야기는 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
