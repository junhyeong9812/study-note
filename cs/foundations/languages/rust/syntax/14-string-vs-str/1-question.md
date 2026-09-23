# rust/syntax/14 — `String` 대 `&str` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **스택에 몇 칸이 놓이고 힙 주소가 같은지**와
> **어느 시그니처가 어떤 호출을 거부하는지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.** 에디션을 안 밝힌 결과는 근거가 못 된다.
> ★ 크기·주소를 묻는 문항은 **`x86_64`(포인터 8바이트) 기준**이다. 다른 대상에서는 숫자가 달라진다.
> ★ 주소를 찍는 문항에서 맞혀야 하는 것은 **숫자가 아니라 「같은가 다른가」라는 성질**이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 세 꼴이 스택에서 몇 바이트인가 (예측)

```rust
use std::mem::size_of;

fn main() {
    println!("{}", size_of::<usize>());
    println!("{}", size_of::<String>());
    println!("{}", size_of::<&str>());
    println!("{}", size_of::<&String>());
    println!("{}", size_of::<&&String>());
    println!("{}", size_of::<Box<str>>());
    println!("{}", size_of::<char>());
}
```

- 일곱 줄에 각각 무엇이 찍히는가?
- `&str` 과 `&String` 이 왜 다른 숫자인가 — 한 문장으로 말할 수 있는가?
- `&&String` 이 `&String` 과 같은 숫자인 이유는 무엇인가?
- `Box<str>` 와 `Box<String>` 중 큰 쪽은 어느 것이고 왜인가?
- 이 숫자들을 **외우지 않고 얻는** 방법은 무엇인가?

### 2. ★★ `String` 에서 창을 꺼냈을 때의 힙 주소 (예측)

```rust
fn main() {
    let s = String::from("가나다라마");
    let c = s.clone();
    println!("{:p}", s.as_ptr());
    println!("{:p}", (&s[..]).as_ptr());
    println!("{:p}", s.as_str().as_ptr());
    println!("{:p}", c.as_ptr());
}
```

- 네 주소 중 **같은 것은 몇 개**이고 다른 것은 몇 개인가?
- 이 출력을 **문서에 그대로 실으면** 무엇이 문제이고, 무엇이라고 한 줄 적어야 하는가?
- 같은 실험을 **다시 돌려도 출력이 안 바뀌게** 쓰려면 어떻게 하는가?
- `&s[..]`·`s.as_str()`·`&*s` 세 표기의 차이는 무엇인가?
- 한 `String` 을 `&s[..3]` 과 `&s[3..]` 로 나눠 보면 새로 할당되는 것이 있는가?

### 3. ★★ 인자를 `&String` 으로 받은 함수에 리터럴 (예측)

```rust
fn shout(s: &String) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    println!("{}", shout(&owned));
    println!("{}", shout("hello"));
}
```

- 두 호출 중 거부되는 것은 어느 쪽이고, 에러 번호는 무엇인가?
- `= note:` 두 줄이 각각 무엇을 말하는가 — 리터럴의 **수명**까지 읽어 낼 수 있는가?
- 호출부가 이 함수를 리터럴로 부르려면 무엇을 해야 하는가? 그 대가는?
- 「`&String` 이 더 구체적이니 더 안전하다」가 왜 틀린 말인가?

### 4. ★ 인자를 `&str` 로 받으면 무엇이 들어오나 (예측)

```rust
fn shout(s: &str) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    let boxed: Box<str> = owned.clone().into_boxed_str();
    // 아래 일곱 중 컴파일되는 것은?
    shout("hello");
    shout(&owned);
    shout(owned.as_str());
    shout(&owned[..]);
    shout(&*owned);
    shout(&boxed);
    shout(owned);
}
```

- 일곱 줄 중 **거부되는 것은 몇 줄**이고 어느 줄인가?
- 거부된 줄의 에러 번호는 무엇이고, `help:` 는 무엇을 하라고 하는가?
- `&String` 이 들어가는 것은 **무슨 장치** 때문인가?
- 같은 표를 `fn shout(s: &String)` 으로 만들면 ✓ 칸이 몇 개로 줄어드는가?

### 5. ★ 참조를 네 겹 쌓아 넘기면 (예측)

```rust
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;
    let rrr: &&&String = &rr;
    let rrrr: &&&&String = &rrr;
    println!("{} {} {} {}", f(r), f(rr), f(rrr), f(rrrr));
}
```

- 네 호출 중 **컴파일되는 것은 몇 개**인가?
- 그 답이 말해 주는 역참조 강제의 성질은 무엇인가 — 한 낱말로?
- `rr.as_str()`·`&rr[..]` 도 되는가? 그것은 강제인가 다른 장치인가?
- 그럼 **겹 수가 아니라 무엇이** 강제를 막는가?

### 6. ★ `a + &b` 뒤의 `a` (예측)

```rust
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + &b;
    println!("{} {} {}", c, a, b);
}
```

- 컴파일되는가? 안 되면 에러 번호와 그 번호를 이미 만난 주제는 몇 번인가?
- `a` 와 `b` 중 살아남는 쪽은 어느 것이고 왜 갈리는가?
- `a + b` 로 바꾸면 어느 에러로 **바뀌는가**?
- `&b` 는 `&String` 인데 어떻게 통과하는가? `&&b` 는 어떤가?
- 같은 일을 `format!` 로 하면 무엇이 달라지는가?

### 7. `&str` → `String` 다섯 표기 (왜)

- `to_string()` · `to_owned()` · `into()` · `String::from()` · `format!()` 가 **각각 어디서 오는가**?
- 다섯의 결과 값은 같은가? **힙 주소**도 같은가?
- `42i32.to_owned()` 의 타입은 무엇인가 — `String` 인가?
- `String::from(42i32)` 는 되는가? 안 되면 진단이 **무슨 목록**을 찍어 주는가?
- 다섯 중 「더 느릴 수 있는 것」을 고를 때, **이 문서가 근거로 댈 수 있는 것과 없는 것**은 각각 무엇인가?

### 8. `Copy` 여부가 가르는 자리 (연결)

- `let b = a;` 뒤에 `a` 를 쓰는 같은 코드가 **한쪽은 거부되고 한쪽은 통과**한다. 타입이 각각 무엇인가?
- 거부되는 쪽의 에러 번호와, 에러가 대는 이유 한 구절은 무엇인가?
- `&String` 은 `Copy` 인가? `&mut String` 은?
- 이 판정 규칙의 정본은 몇 번 주제인가?

### 9. `s.len()` 이 세는 것 (경계)

- `String::from("가나다").len()` 은 얼마인가? `chars().count()` 는?
- `"abc".len()` 은 얼마인가 — 이 값이 왜 위험한가?
- `chars().count()` 를 「사람이 보는 글자 수」로 읽어도 되는가?
- UTF-8 경계와 `char_indices()` 의 정본은 몇 번 주제인가?

### 10. `len()` 과 `capacity()` (경계)

- `String::new()` 의 `len` 과 `cap` 은 각각 얼마인가?
- `String::with_capacity(16)` 직후의 `len` 은 얼마인가?
- `String::new()` 에 `push_str("ab")` 를 열 번 돌리면 `capacity()` 가 어떤 수열로 변하는가?
- ★ 그 수열을 **본문에 사실로 적어도 되는가** — 누가 보장하는 것인가?
- `&str` 에 `push_str` 을 부르면 무엇이 나는가? `mut` 을 붙이면 달라지는가?

### 11. 리터럴이 사는 곳 (연결)

- `"안녕"` 의 타입을 수명까지 붙여 적을 수 있는가?
- 같은 글자의 리터럴 두 개가 **같은 주소**를 가리키는가 — 그것은 보장인가?
- 지역 `String` 의 `&s[..]` 를 함수 밖으로 돌려주면 무엇이 나는가?
- 「`String` → `&str` 은 공짜인데 `&str` → `String` 은 왜 아닌가」를 **두 줄**로 답할 수 있는가?
- `'static` 의 **두 뜻**을 다룬 주제는 몇 번인가?

### 12. 강제가 안 도는 자리 (경계)

- `&&String` 과 `&str` 을 `==` 로 비교하면 무엇이 나는가? `&String` 과 비교하면?
- `v.iter().map(takes_str)`(여기서 `v: Vec<String>`, `takes_str: fn(&str) -> usize`)는 컴파일되는가?
- 그 진단에서 **덤으로 따라온 두 번째 에러**는 무엇이고 왜 생겼는가?
- `help:` 가 주는 처방은 무엇인가 — 그것이 왜 통하는가?
- 「강제가 도는 자리 / 안 도는 자리」를 **한 문장으로 가르는 기준**을 말할 수 있는가?
- 인자를 더 넓게 여는 `impl AsRef<str>`·`impl Into<String>` 의 정본은 목록의 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
