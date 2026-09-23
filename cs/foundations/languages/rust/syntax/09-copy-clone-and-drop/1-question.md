# rust/syntax/09 — `Copy`와 `Clone`, 그리고 `Drop` 시점 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **컴파일러가 어느 조합을 거부하는지**와
> **값이 정확히 어느 순서로 사라지는지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o /tmp/ex && /tmp/ex`.
> ★ **`--edition` 을 빼면 에디션 2015 로 돌아간다.** 반드시 붙인다.
> ★ 해제 시점이 궁금하면 **`impl Drop` 에 `println!` 을 넣어라** — [**08번 주제**](../08-ownership-and-move/)가 세운 창이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 파생을 하나만 붙이면 (예측)

```rust
#[derive(Copy)]
struct P { x: i32, y: i32 }

fn main() {
    let a = P { x: 1, y: 2 };
    let b = a;
    println!("{} {} / {} {}", a.x, a.y, b.x, b.y);
}
```

- 컴파일되는가? 안 되면 에러 번호는 무엇인가?
- 에러의 `note:` 가 가리키는 곳은 어디인가?
- `Copy` 의 선언은 std 에서 어떻게 생겼기에 이 에러가 나는가?
- 거꾸로 `#[derive(Clone)]` 만 붙이면 통과하는가?

### 2. ★ `String` 이 든 구조체에 `Copy` 를 던지면 (예측)

```rust
#[derive(Clone, Copy)]
struct Label { text: String }
```

- 에러 번호는 무엇이고, 컴파일러가 **밑줄을 긋는 곳**은 어디인가?
- 필드가 열 개인데 아홉이 `Copy` 면 어떻게 되는가?
- `rustc --explain` 이 이 에러 설명에 덤으로 얹는 **참조에 관한 한 문장**은 무엇인가?
- 그 문장이 갈라 주는 두 타입은 무엇인가?

### 3. ★★ 둘을 같이 달면 (예측)

```rust
#[derive(Clone, Copy)]
struct Tag(i32);

impl Drop for Tag {
    fn drop(&mut self) { println!("[해제] Tag({})", self.0); }
}
```

- 컴파일되는가? 에러 번호와 제목 줄은 무엇인가?
- **왜 막는가** — 08번 주제의 「해제는 정확히 한 번」으로 설명할 수 있는가?
- 이 규칙을 뒤집어 읽으면 `Copy` 타입에 대해 무엇을 말하게 되는가?
- `rustc --explain` 의 문장에서 **이것이 영구 규칙이 아닐 수 있다**는 신호는 어느 낱말인가?

### 4. ★ 두 `clone()` 의 결과 (예측)

```rust
use std::rc::Rc;

let v1 = vec![1u8, 2, 3];
let v2 = v1.clone();
// v1 의 버퍼와 v2 의 버퍼는 같은 주소인가?

let r1 = Rc::new(vec![1u8, 2, 3]);
let r2 = Rc::clone(&r1);
// r1 속 버퍼와 r2 속 버퍼는 같은 주소인가? strong_count 는 얼마인가?
```

- 위 두 물음의 답은 각각 무엇인가?
- `drop(r2)` 뒤 `strong_count` 는 얼마가 되는가?
- `(*r1).clone()` 은 어느 쪽 동작을 하는가?
- 「`clone()` 은 깊은 복사다」라는 문장은 맞는가 틀리는가 — 그 깊이를 누가 정하는가?

### 5. `derive(Clone)` 이 붙이는 것 (예측)

```rust
use std::rc::Rc;

#[derive(Clone)]
struct Derived<T>(Rc<T>);

struct Manual<T>(Rc<T>);
impl<T> Clone for Manual<T> {
    fn clone(&self) -> Self { Manual(Rc::clone(&self.0)) }
}

struct NotClone;
// Manual(Rc::new(NotClone)).clone() 과 Derived(Rc::new(NotClone)).clone() 중 어느 쪽이 막히나?
```

- 둘 중 거부되는 쪽은 어느 것이고 에러 번호는 무엇인가?
- 에러의 `note:` 가 **누가 그 경계를 넣었다**고 말하는가?
- `Rc<T>` 는 `T` 가 `Clone` 이 아니어도 `Clone` 인데 왜 이런 일이 생기는가?
- 라이브러리 경계에서 이 차이가 왜 문제가 되는가?

### 6. ★★ 이 프로그램의 출력 순서 (예측)

```rust
struct D(&'static str);
impl Drop for D { fn drop(&mut self) { println!("        [해제] {}", self.0); } }

struct Pair { first: D, second: D }
impl Drop for Pair { fn drop(&mut self) { println!("    [해제] Pair 본체 먼저"); } }

struct Plain { a: D, b: D }

fn main() {
    { let _x = D("지역-1번째"); let _y = D("지역-2번째"); let _z = D("지역-3번째"); }
    { let _p = Plain { a: D("필드-a"), b: D("필드-b") }; }
    { let _p = Pair { first: D("필드-first"), second: D("필드-second") }; }
    { let _t = (D("튜플-0"), D("튜플-1"), D("튜플-2")); }
    { let _v = vec![D("벡터-0"), D("벡터-1"), D("벡터-2")]; }
    fn two(_p: D, _q: D) {}
    two(D("인자-앞"), D("인자-뒤"));
}
```

- 지역 변수 셋은 어느 순서로 해제되는가?
- 구조체 필드 둘은 어느 순서인가 — 지역 변수와 **같은 방향인가 반대 방향인가**?
- `Pair` 는 본체(`Drop::drop`)와 필드 중 누가 먼저인가, 그리고 **왜 그럴 수밖에 없는가**?
- 튜플·`Vec` 원소·함수 인자는 각각 어느 쪽 규칙을 따르는가?

### 7. `d.drop()` 을 부르면 (경계)

- `Drop` 을 구현한 값 `d` 에 대해 `d.drop();` 을 쓰면 무엇이 나는가 — 에러 번호는?
- `rustc --explain` 이 대신 쓰라고 하는 것은 무엇인가?
- `drop(d)` 와 `d.drop()` 의 결정적 차이를 **소유권** 한 낱말로 말할 수 있는가?
- `std::mem::drop` 의 몸통은 무엇이 들어 있는가?

### 8. `Copy` 값을 `drop()` 하면 (경계)

- `let n = 7i32; drop(n); println!("{}", n);` 은 컴파일되는가?
- 실행하면 `n` 은 어떻게 되는가?
- 컴파일러가 아무 말도 안 하는가 — 한다면 **무슨 이름의 린트**인가?
- 그 린트가 제안하는 대안 문장은 무엇인가?

### 9. `Copy` 와 `Clone` 의 관계 (왜)

- 둘 중 **부분집합**인 쪽은 어느 것인가?
- `Copy` 는 암묵적이고 `Clone` 은 명시적이다 — 이 차이가 코드에서 어떻게 드러나는가?
- `String` 은 `Clone` 인데 `Copy` 가 아니다. 반대로 `Copy` 인데 `Clone` 이 아닌 타입이 있을 수 있는가?
- `Copy` 를 「싸다」는 뜻으로 읽으면 어디서 틀리는가?

### 10. 크기와 `Copy` 판정 (경계)

- `[i32; 3]`(12바이트)과 `Vec<i32>`(24바이트) 중 `Copy` 인 쪽은 어느 것인가?
- 이 대비가 무엇을 반증하는가?
- `size_of::<String>()` 과 `size_of::<Vec<i32>>()` 는 이 머신에서 각각 얼마인가?
- 그 수치는 무엇에 달려 있어서 다른 머신에서 달라질 수 있는가?

### 11. 다른 주제와 잇기 (연결)

- `Rc::clone` 이 카운트만 올리는 것의 **정본**은 목록의 몇 번 주제인가?
- `Drop` 으로 막힌 자리를 푸는 `mem::take`/`replace` 의 정본은 몇 번인가?
- `&T` 는 `Copy` 이고 `&mut T` 는 아니다 — 그 정본은 몇 번인가, 그리고 왜 그렇게 정했겠는가?
- 08번 주제의 **E0509**(`Drop` 구현체는 부분 이동 금지)와 이 주제의 **해제 순서** 사실은 어떻게 이어지는가?
- 이 주제에서 **에러가 아니라 출력 순서로만** 드러나는 사실은 무엇이었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
