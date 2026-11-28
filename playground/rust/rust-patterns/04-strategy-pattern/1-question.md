# rust/rust-patterns/04 — Strategy 패턴 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 가격 엔진의 전략을 네 번 바꿔 가며 계산하면 (예측)

```rust
// 질문용 발췌
let mut engine = PricingEngine::new(regular_price());
println!("정가:        {:.0}원", engine.calculate(100_000.0));
engine.set_strategy(member_discount(0.1));
println!("회원 10%:    {:.0}원", engine.calculate(100_000.0));
engine.set_strategy(member_discount(0.2));
println!("VIP 20%:     {:.0}원", engine.calculate(100_000.0));
engine.set_strategy(fixed_discount(15_000.0));
println!("15000원 할인: {:.0}원", engine.calculate(100_000.0));
```

- 네 줄에 찍히는 금액은 각각 얼마인가?

### 2. 같은 데이터를 세 정렬 전략으로 차례로 정렬하면 (예측)

```rust
// 질문용 발췌
let data_original = vec![64, 34, 25, 12, 22, 11, 90];
let mut sorter = Sorter::new(Box::new(BubbleSort));
let mut data = data_original.clone();
sorter.sort(&mut data);
println!("  결과: {:?}", data);
sorter.set_strategy(Box::new(QuickSort));
let mut data = data_original.clone();
sorter.sort(&mut data);
println!("  결과: {:?}", data);
```

- 화면에 찍히는 네 줄은 무엇인가?
- 두 번째 정렬이 받는 입력은 첫 번째 정렬의 결과인가, 원본인가?

### 3. 검증기 둘로 네 문자열을 검사하면 (예측)

```rust
// 질문용 발췌
let length_check = LengthValidator { min: 3, max: 20 };
let pattern_check = PatternValidator { pattern: "@".to_string() };
validate_input(&length_check, "hi");
validate_input(&length_check, "hello");
validate_input(&pattern_check, "user@mail.com");
validate_input(&pattern_check, "invalid");
```

- 네 줄은 각각 어떻게 찍히는가?

### 4. `calculate` 가 `(self.strategy)(price)` 로 괄호를 두르는 까닭 (왜)
- 괄호 없이 `self.strategy(price)` 라고 쓰면 왜 안 되는가?

### 5. `member_discount` 의 클로저에 `move` 가 붙는 까닭 (왜)
- `move` 를 빼면 왜 컴파일되지 않는가?

### 6. `LengthValidator { min: 3, max: 20 }` 에 한글 두 글자 「가나」 (경계)
- 두 글자인 「가나」는 이 검증을 통과하는가?

### 7. 빈 `Vec` 에 `BubbleSort` 를 쓸 때의 `n - 1 - i` (경계)
- `usize` 인 `n` 이 0 일 때 이 정렬은 패닉하는가?

### 8. `impl Fn` 을 반환하는 함수 하나에서 조건에 따라 다른 클로저 두 개 (경계)
- `if` 의 두 갈래에서 서로 다른 클로저를 돌려주는 `fn pick(vip: bool) -> impl Fn(f64) -> f64` 는 만들 수 있는가?

### 9. 제네릭 `validate_input` 과 여러 검증기를 한 목록에 담기 (연결)
- 길이 검증기와 패턴 검증기를 한 목록에 넣고 차례로 돌리려면 목록의 타입을 무엇으로 해야 하는가?

### 10. 정렬 전략이 셋으로 고정이라면 enum 디스패치 (연결)
- 세 정렬 전략을 `enum` 과 `match` 로 바꾸면 무엇을 얻고 무엇을 잃는가?

## 실습

### 실습 1. 세 가지 방식의 Strategy 패턴 데모 만들기

**만들 것** — 클로저 전략(가격 계산), 트레이트 객체 전략(정렬), 제네릭 전략(입력 검증)을 한 파일에 구현하고, `main` 에서 전략을 바꿔 가며 결과를 찍는다.

**요구 조건**

1단계 — 클로저 기반 전략
1. `PricingEngine` 은 `f64` 를 받아 `f64` 를 돌려주는 클로저를 `Box<dyn Fn(f64) -> f64>` 필드 `strategy` 에 보관한다.
2. `new` 는 `impl Fn(f64) -> f64 + 'static` 클로저를 받아 `Box` 로 감싸 저장한다.
3. `calculate(&self, price)` 는 보관한 클로저를 불러 그 결과를 돌려준다.
4. `set_strategy(&mut self, …)` 는 새 클로저를 `Box` 로 감싸 필드를 바꾼다.
5. 클로저 팩토리 셋을 만든다 — `regular_price()` 는 가격을 그대로, `member_discount(rate)` 는 `price * (1.0 - rate)`, `fixed_discount(amount)` 는 `price - amount` 를 돌려주되 0 아래로 내려가지 않는다. 셋 다 `impl Fn(f64) -> f64` 를 반환한다.
6. `main` 에서 100,000원에 정가 → 회원 10% → VIP 20% → 15,000원 정액 할인 차례로 전략을 바꿔 가며 금액을 소수점 없이 찍는다.

2단계 — 트레이트 기반 전략
7. `SortStrategy` 트레이트는 `sort(&self, data: &mut Vec<i32>)` 와 `name(&self) -> &str` 을 가진다.
8. 필드 없는 구조체 `BubbleSort` · `InsertionSort` · `QuickSort` 가 각각 버블 정렬, 삽입 정렬, 퀵 정렬로 `SortStrategy` 를 구현하고 `name` 은 자기 구조체 이름을 돌려준다.
9. `QuickSort` 는 길이 1 이하면 바로 끝내고, 가운데 원소를 피벗으로 「작은 것 · 같은 것 · 큰 것」 세 `Vec` 으로 나눈 뒤 작은 쪽과 큰 쪽을 재귀로 정렬하고 `data` 를 비워 차례로 이어 붙인다.
10. `Sorter` 는 `Box<dyn SortStrategy>` 를 보관하고, `sort` 는 「  [이름] 정렬 시작」을 찍은 뒤 정렬을 전략에 맡기며, `set_strategy` 로 전략을 바꾼다.
11. `main` 에서 `[64, 34, 25, 12, 22, 11, 90]` 원본을 매번 `clone()` 해 버블 → 삽입 → 퀵 차례로 정렬하고 매번 「  결과: …」를 찍는다.

3단계 — 제네릭 전략
12. `Validator` 트레이트는 `validate(&self, input: &str) -> Result<(), String>` 을 가진다.
13. `LengthValidator { min, max }` 는 `input.len()` 이 범위 안이면 `Ok(())`, 아니면 「길이 min~max 필요, 현재: len」 메시지의 `Err` 를 돌려준다.
14. `PatternValidator { pattern }` 은 `input` 이 `pattern` 을 포함하면 `Ok(())`, 아니면 「'pattern' 패턴이 포함되어야 합니다」 메시지의 `Err` 를 돌려준다.
15. 제네릭 함수 `validate_input<V: Validator>(validator: &V, input: &str)` 는 결과에 따라 「  'input' -> 유효」 또는 「  'input' -> 실패: 메시지」를 찍는다.
16. `main` 에서 `min: 3, max: 20` 검증기로 `"hi"` · `"hello"` 를, `"@"` 패턴 검증기로 `"user@mail.com"` · `"invalid"` 를 검사한다.
17. 마지막에 「=== 비교 ===」 아래로 세 방식을 한 줄씩 비교하는 문장을 찍는다.

**시작 코드**

```rust
// === Strategy 패턴: 클로저 기반 + 트레이트 기반 + 제네릭 ===

// ===== 1. 클로저 기반 전략 =====
struct PricingEngine {
    // TODO: f64 -> f64 클로저를 Box 로 담는 필드 strategy
}

impl PricingEngine {
    fn new(strategy: impl Fn(f64) -> f64 + 'static) -> Self {
        todo!() // TODO: Box 로 감싸 저장
    }

    fn calculate(&self, price: f64) -> f64 {
        todo!() // TODO: 보관한 클로저 호출
    }

    fn set_strategy(&mut self, strategy: impl Fn(f64) -> f64 + 'static) {
        // TODO: 전략 교체
    }
}

// TODO: regular_price() / member_discount(rate) / fixed_discount(amount)
//       — 셋 다 impl Fn(f64) -> f64 를 반환하는 클로저 팩토리

// ===== 2. 트레이트 기반 전략 =====
// TODO: trait SortStrategy { sort, name }

struct BubbleSort;
struct InsertionSort;
struct QuickSort;

// TODO: 세 구조체에 SortStrategy 구현 (버블 · 삽입 · 퀵)

struct Sorter {
    // TODO: 전략을 트레이트 객체로 보유
}

impl Sorter {
    // TODO: new / sort("  [{}] 정렬 시작" 을 찍고 위임) / set_strategy
}

// ===== 3. 제네릭 전략 (정적 디스패치) =====
// TODO: trait Validator { validate(&self, input: &str) -> Result<(), String> }

struct LengthValidator { min: usize, max: usize }
struct PatternValidator { pattern: String }

// TODO: 두 검증기에 Validator 구현
//   길이 실패 메시지: format!("길이 {}~{} 필요, 현재: {}", min, max, len)
//   패턴 실패 메시지: format!("'{}' 패턴이 포함되어야 합니다", pattern)

// TODO: fn validate_input<V: Validator>(validator: &V, input: &str)
//   성공: println!("  '{}' -> 유효", input)
//   실패: println!("  '{}' -> 실패: {}", input, e)

fn main() {
    println!("=== 1. 클로저 기반 전략 ===");
    // TODO: 정가 → 회원 10% → VIP 20% → 15000원 할인, 각각 100_000.0 계산
    //   println!("정가:        {:.0}원", …);
    //   println!("회원 10%:    {:.0}원", …);
    //   println!("VIP 20%:     {:.0}원", …);
    //   println!("15000원 할인: {:.0}원", …);

    println!("\n=== 2. 트레이트 기반 전략 ===");
    let data_original = vec![64, 34, 25, 12, 22, 11, 90];
    // TODO: 버블 → 삽입 → 퀵, 매번 clone 한 데이터를 정렬하고
    //   println!("  결과: {:?}", data);

    println!("\n=== 3. 제네릭 전략 (정적 디스패치) ===");
    // TODO: LengthValidator { min: 3, max: 20 } 로 "hi", "hello"
    //       PatternValidator { pattern: "@" } 로 "user@mail.com", "invalid"

    println!("\n=== 비교 ===");
    println!("클로저 전략:   간단한 변환/계산에 적합. 가장 가벼움");
    println!("트레이트 객체: 복잡한 알고리즘, 상태 보유. 동적 디스패치");
    println!("제네릭:        정적 디스패치, 인라이닝 가능. 최고 성능");
}
```

**확인 방법** — `rustc strategy-pattern.rs && ./strategy-pattern` 으로 돌려, 세 블록의 줄들이 퀴즈 1 · 2 · 3 에서 예측한 내용과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
