# rust/rust-patterns/02 — Newtype 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 섞인 수를 정렬 벡터에 담고 2 를 끼우면 (예측)

```rust
// 질문용 발췌
let mut sorted = SortedVec::new(vec![3, 1, 4, 1, 5, 9]);
sorted.insert(2);
println!("2 삽입 후:   {:?}", &*sorted);
println!("길이: {}, 첫 번째: {}", sorted.len(), sorted[0]);
println!("contains 7: {}", sorted.contains(&7));
```

- 세 줄은 각각 무엇을 찍는가?
- `2` 는 몇 번 자리(0부터 셈)에 들어가는가?

### 2. 이메일과 빈 문자열을 검사 생성자에 넣으면 (예측)

```rust
// 질문용 발췌
match Email::new("invalid") {
    Ok(email) => println!("유효한 이메일: {}", email),
    Err(e) => println!("에러: {}", e),
}
println!("빈 문자열: {:?}", NonEmptyString::new(""));
println!("{}", NonEmptyString::new("   ").is_err());
```

- 첫 `println!` 은 어느 갈래에서 무엇을 찍는가?
- 둘째 줄은 `Result` 를 `{:?}` 로 찍을 때 어떤 꼴이 되는가?
- 공백 세 칸을 넣은 셋째 줄은 무엇을 찍는가?

### 3. 사용자 42 의 주문을 `{:?}` 로 찍으면 (예측)

```rust
// 질문용 발췌
let user = UserId(42);
for order in &find_orders_by_user(user) {
    println!("주문 {:?}: {:.0}원", order.id, order.amount);
}
```

- 모두 몇 줄이 찍히고, 첫 줄은 어떤 꼴인가?
- `order.id` 자리에는 숫자만 나오는가, 다른 글자가 붙는가?

### 4. 둘 다 `f64` 인 `Meters` 와 `Kilometers` 를 섞어 쓸 수 없는 까닭 (왜)

- 안의 값이 같은 `f64` 인데 `let wrong: Meters = Kilometers(5.0);` 는 왜 컴파일되지 않는가?
- 이 막힘은 프로그램을 돌릴 때 일어나는가, 만들 때 일어나는가?

### 5. 검증을 생성자 한 곳에 두는 까닭 (왜)

- `Email` 을 인자로 받는 함수는 왜 이메일 꼴을 다시 검사하지 않아도 되는가?
- `new` 가 `Self` 가 아니라 `Result<Self, String>` 을 돌려주는 까닭은 무엇인가?

### 6. 같은 파일 안에서 `Email(...)` 을 바로 쓰면 (경계)

- 예제처럼 한 파일 · 한 모듈에서 `main` 이 `Email("bad".to_string())` 을 쓰면 컴파일되는가?
- 「`new` 로만 만들 수 있다」를 정말 지키려면 구조를 어떻게 바꿔야 하는가?

### 7. `Deref` 로 감싼 `SortedVec` 에서 열리는 것과 닫힌 것 (경계)

- `sorted.len()` 은 `SortedVec` 의 `impl` 에 없는데 어떻게 불리는가?
- `sorted.push(0)` 이나 슬라이스의 `sort` 같은 가변 조작은 이 길로 열리는가?
- 원본 팁이 `Deref` 남용을 경계하는 까닭은 무엇인가?

### 8. `Copy` 를 빼면 `distance` 를 두 번 쓸 수 있나 (경계)

- `Kilometers` 의 `derive` 에서 `Copy` 만 지우면 `distance.to_meters()` 다음 줄의 `distance.to_miles()` 는 어떻게 되는가?
- `Email` 에는 왜 `Copy` 를 달 수 없는가?

### 9. `type Meters = f64;` 와 newtype 의 차이 (연결)

- 타입 별칭으로 `Meters` 와 `Kilometers` 를 만들면 둘을 섞는 실수를 막을 수 있는가?
- newtype 과 타입 별칭은 각각 언제 고르는가?

### 10. 「zero-cost」 와 타입 검사가 일어나는 때 (연결)

- 원본 팁이 newtype 을 런타임 비용이 없다고 말할 수 있는 까닭을 타입 검사의 시점과 이어 설명하면?
- `Email::new` 안의 `contains` 검사도 newtype 의 비용이라고 봐야 하는가?

## 실습

### 실습 1. 단위 · ID · 검증 · 정렬 벡터를 newtype 으로 만들기

**만들 것** — 같은 원시 타입을 뜻별로 가르는 newtype 네 묶음(단위, ID, 검증 문자열, 정렬 벡터)을 만들고, 미리 채워 둔 `main` 이 그것들을 차례로 써 보게 한다.

**요구 조건**

1단계 — 단위
1. `f64` 를 감싼 `Meters` · `Kilometers` · `Miles` 를 만들고 `Debug, Clone, Copy, PartialEq` 를 파생한다.
2. `Meters::to_kilometers(self)` 는 1000 으로 나눠 `Kilometers` 를 돌려준다.
3. `Kilometers::to_meters(self)` 는 1000 을 곱해 `Meters` 를, `to_miles(self)` 는 `0.621371` 을 곱해 `Miles` 를 돌려준다.
4. 세 타입에 `fmt::Display` 를 구현한다 — `Meters` 는 소수 한 자리 + `m`, `Kilometers` 는 소수 두 자리 + `km`, `Miles` 는 소수 두 자리 + `mi`.

2단계 — ID
5. `u64` 를 감싼 `UserId` · `OrderId` 를 만들고 `Debug, Clone, Copy, PartialEq, Eq, Hash` 를 파생한다.
6. `find_orders_by_user(user_id: UserId)` 는 받은 `user_id` 로 주문 두 개 — `OrderId(1001)` 금액 `29900.0`, `OrderId(1002)` 금액 `15000.0` — 를 `Order::new` 로 만들어 `Vec` 으로 돌려준다.

3단계 — 검증 newtype
7. `Email::new(&str) -> Result<Self, String>` 은 `'@'` 와 `'.'` 이 모두 들어 있으면 `Ok(Email(...))`, 아니면 `Err("유효하지 않은 이메일: <입력>")` 을 돌려준다.
8. `Email::as_str` 는 안의 문자열을 `&str` 로 빌려주고, `Display` 는 안의 문자열을 그대로 찍는다.
9. `NonEmptyString::new(&str)` 는 앞뒤 공백을 자른 결과가 비었으면 `Err("빈 문자열은 허용되지 않습니다")`, 아니면 **원래 입력 그대로** 감싼 `Ok` 를 돌려주고, `as_str` 로 읽게 한다.

4단계 — `Deref` 로 감싼 정렬 벡터
10. `SortedVec::new(Vec<T>)` 는 받은 벡터를 정렬해 감싼다.
11. `SortedVec::insert(&mut self, item)` 은 `binary_search` 로 자리를 찾아(찾았든 못 찾았든 그 위치) 그 자리에 끼워 정렬을 유지한다.
12. `Deref` 를 구현하되 `Target` 은 `[T]` 로 하여, `len` · 인덱싱 · `contains` 를 슬라이스에서 빌려 쓰게 한다.

**시작 코드**

```rust
use std::fmt;
use std::ops::Deref;

// ── 1단계: 단위 ──
// TODO: f64 를 감싼 Meters · Kilometers · Miles 선언 (Debug, Clone, Copy, PartialEq 파생)

impl Meters {
    fn to_kilometers(self) -> Kilometers {
        todo!() // TODO: 1km = 1000m
    }
}

impl Kilometers {
    fn to_meters(self) -> Meters {
        todo!()
    }

    fn to_miles(self) -> Miles {
        todo!() // TODO: 1km = 0.621371mi
    }
}

// TODO: Meters · Kilometers · Miles 에 fmt::Display 구현

// ── 2단계: ID ──
// TODO: u64 를 감싼 UserId · OrderId 선언 (Debug, Clone, Copy, PartialEq, Eq, Hash 파생)

#[derive(Debug)]
struct Order {
    id: OrderId,
    user_id: UserId,
    amount: f64,
}

impl Order {
    fn new(id: OrderId, user_id: UserId, amount: f64) -> Self {
        Order { id, user_id, amount }
    }
}

fn find_orders_by_user(user_id: UserId) -> Vec<Order> {
    // TODO: 주문 두 개를 만들어 돌려준다
    todo!()
}

// ── 3단계: 검증 newtype ──
#[derive(Debug, Clone, PartialEq)]
struct Email(String);

impl Email {
    fn new(value: &str) -> Result<Self, String> {
        todo!() // TODO: '@' 와 '.' 검사
    }

    fn as_str(&self) -> &str {
        todo!()
    }
}

// TODO: Email 에 fmt::Display 구현

#[derive(Debug, Clone, PartialEq)]
struct NonEmptyString(String);

impl NonEmptyString {
    fn new(value: &str) -> Result<Self, String> {
        todo!() // TODO: trim 뒤 비었는지 검사
    }

    fn as_str(&self) -> &str {
        todo!()
    }
}

// ── 4단계: Deref 로 감싼 정렬 벡터 ──
#[derive(Debug)]
struct SortedVec<T: Ord>(Vec<T>);

impl<T: Ord> SortedVec<T> {
    fn new(mut items: Vec<T>) -> Self {
        todo!() // TODO: 정렬한 뒤 감싼다
    }

    fn insert(&mut self, item: T) {
        todo!() // TODO: binary_search 로 자리 찾기 → 끼우기
    }
}

// TODO: SortedVec 에 Deref 구현 (Target = [T])

fn main() {
    println!("=== 1. 단위 구분 ===");
    let distance = Kilometers(42.195);
    println!("마라톤: {}", distance);
    println!("미터:   {}", distance.to_meters());
    println!("마일:   {}", distance.to_miles());
    // let wrong: Meters = Kilometers(5.0); // 주석을 풀면 타입 불일치

    println!("\n=== 2. ID 타입 구분 ===");
    let user = UserId(42);
    let orders = find_orders_by_user(user);
    for order in &orders {
        println!("주문 {:?}: {:.0}원", order.id, order.amount);
    }
    // find_orders_by_user(OrderId(1)); // 주석을 풀면 타입 불일치

    println!("\n=== 3. 유효성 검사 Newtype ===");
    match Email::new("user@example.com") {
        Ok(email) => println!("유효한 이메일: {}", email),
        Err(e) => println!("에러: {}", e),
    }
    match Email::new("invalid") {
        Ok(email) => println!("유효한 이메일: {}", email),
        Err(e) => println!("에러: {}", e),
    }
    let name = NonEmptyString::new("Alice").unwrap();
    println!("이름: {}", name.as_str());
    println!("빈 문자열: {:?}", NonEmptyString::new(""));

    println!("\n=== 4. Deref를 통한 투명 래핑 ===");
    let mut sorted = SortedVec::new(vec![3, 1, 4, 1, 5, 9]);
    println!("정렬된 벡터: {:?}", &*sorted);
    sorted.insert(2);
    println!("2 삽입 후:   {:?}", &*sorted);
    println!("길이: {}, 첫 번째: {}", sorted.len(), sorted[0]);
    println!("contains 7: {}", sorted.contains(&7));
}
```

**확인 방법** — `rustc newtype-pattern.rs && ./newtype-pattern` 으로 돌려, 네 묶음의 줄이 퀴즈 1~3 의 정답과 같은 꼴인지 본다. 이어서 `main` 의 주석 두 줄을 하나씩 풀어 컴파일러가 타입 불일치로 거절하는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
