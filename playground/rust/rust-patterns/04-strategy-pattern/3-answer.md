# rust/rust-patterns/04 — Strategy 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 100000원 · 90000원 · 80000원 · 85000원

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
정가:        100000원
회원 10%:    90000원
VIP 20%:     80000원
15000원 할인: 85000원
```

**왜 그런가**
- `regular_price()` 는 가격을 그대로 돌려준다 — 100000.
- `member_discount(0.1)` 은 `100000 * (1.0 - 0.1)` 이다 — 90000 근처.
- `member_discount(0.2)` 는 `100000 * 0.8` 이다 — 80000 근처.
- `fixed_discount(15_000.0)` 은 `(100000 - 15000).max(0.0)` 이다 — 85000.
- 부동소수 계산이라 소수점 아래 아주 작은 오차가 생길 수 있지만 `{:.0}` 이 소수점 아래 0자리로 찍으므로 정수처럼 보인다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

### 2. 두 번 다 원본을 받아 같은 정렬 결과가 나온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  [BubbleSort] 정렬 시작
  결과: [11, 12, 22, 25, 34, 64, 90]
  [QuickSort] 정렬 시작
  결과: [11, 12, 22, 25, 34, 64, 90]
```

**왜 그런가**
- `Sorter::sort` 는 먼저 `"  [{}] 정렬 시작"` 에 전략의 `name()` 을 넣어 찍고, 그다음 정렬을 전략에 맡긴다.
- 두 번 모두 `data_original.clone()` 으로 새 `data` 를 만들기 때문에, 두 번째 정렬도 원본 `[64, 34, 25, 12, 22, 11, 90]` 을 받는다.
- 버블 정렬과 퀵 정렬은 알고리즘이 달라도 오름차순 결과는 같다.
- 근거: 2-summary 「동작 방식 (3)」.

### 3. 「hi」만 길이 실패, 「invalid」만 패턴 실패

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  'hi' -> 실패: 길이 3~20 필요, 현재: 2
  'hello' -> 유효
  'user@mail.com' -> 유효
  'invalid' -> 실패: '@' 패턴이 포함되어야 합니다
```

**왜 그런가**
- `"hi"` 는 길이 2 라 `min: 3` 에 못 미쳐 `Err` 가 된다.
- `"hello"` 는 길이 5 로 3~20 안이다.
- `"user@mail.com"` 은 `"@"` 를 포함한다.
- `"invalid"` 는 `"@"` 가 없어 `Err` 가 된다.
- `validate_input` 의 `match` 가 `Ok` 면 「유효」, `Err(e)` 면 「실패: e」를 찍는다.
- 근거: 2-summary 「동작 방식 (4)」.

### 4. 괄호가 없으면 「`strategy` 라는 메서드」를 찾기 때문이다

`self.strategy(price)` 는 `strategy` 라는 이름의 메서드 호출로 읽힌다.
`PricingEngine` 에는 그런 메서드가 없으므로 컴파일 오류다.
`(self.strategy)` 로 먼저 필드 값(클로저)을 꺼내고, 그 값에 `(price)` 를 붙여 불러야 한다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. `rate` 는 함수가 끝나면 사라지는데 클로저는 함수 밖으로 나가기 때문이다

`move` 가 없으면 클로저는 매개변수 `rate` 를 빌려 쓴다.
`member_discount` 가 반환하는 순간 `rate` 는 사라지지만 클로저는 살아남아 `PricingEngine` 에 저장된다.
사라진 값을 빌린 클로저를 내보낼 수 없으므로 컴파일러가 막는다.
`move` 를 붙이면 `rate` 값이 클로저 안으로 옮겨 담겨 문제가 없다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 6. 통과한다 — `len()` 이 바이트 수 6 을 돌려주기 때문이다

`LengthValidator` 는 `input.len()` 으로 길이를 잰다.
`len()` 은 글자 수가 아니라 UTF-8 바이트 수이고, 한글 한 글자는 3바이트다.
「가나」는 6바이트로 재어져 3~20 범위 안에 든다.
글자 수로 재려면 `chars().count()` 를 써야 한다.
근거: 2-summary 「어디서 틀리나 5」 · 「구현 세부사항 대 언어 보장」.

### 7. 패닉하지 않는다 — 바깥 반복이 한 번도 돌지 않는다

`n == 0` 이면 바깥 반복 `for i in 0..n` 이 `0..0` 이라 비어 있다.
그래서 안쪽 범위 `0..n - 1 - i` 는 아예 계산되지 않는다.
`n >= 1` 일 때는 `i` 가 최대 `n - 1` 이므로 `n - 1 - i` 는 0 이상이다.
근거: 2-summary 「어디서 틀리나 6」.

### 8. 만들 수 없다 — `impl Fn` 은 한 타입만 숨긴다

클로저는 하나하나가 서로 다른 이름 없는 타입이다.
반환 타입 `impl Fn(f64) -> f64` 는 「어떤 한 구체 타입」을 숨길 뿐이라, 두 갈래가 다른 클로저를 돌려주면 타입이 맞지 않는다.
반환 타입을 `Box<dyn Fn(f64) -> f64>` 로 바꾸고 두 갈래 모두 `Box::new(...)` 로 감싸면 된다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 9. `Vec<Box<dyn Validator>>` — 제네릭 `V` 로는 한 타입만 담긴다

`validate_input<V: Validator>` 의 `V` 는 호출 자리마다 하나의 구체 타입으로 굳는다.
`Vec<V>` 도 마찬가지로 한 타입만 담을 수 있어 `LengthValidator` 와 `PatternValidator` 를 섞을 수 없다.
서로 다른 전략을 한 목록에 담으려면 타입을 지운 트레이트 객체 `Box<dyn Validator>` 를 써야 한다.
그 대가로 호출은 동적 디스패치가 된다.
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「언제 쓰고 언제 안 쓰나」.

### 10. 얻는 것은 `Box` 없는 `match` 분기, 잃는 것은 바깥에서 전략을 새로 보태는 자유다

`enum SortKind { Bubble, Insertion, Quick }` 처럼 나열하고 `match` 로 갈라 부르면 `Box<dyn …>` 가 필요 없다.
원본 팁은 이런 enum 디스패치가 트레이트 객체보다 빠른 경우가 많다고 한다 — 다만 보장이 아니라 경향이다.
대신 전략 종류가 `enum` 정의에 묶여, 새 전략을 보태려면 `enum` 과 모든 `match` 를 고쳐야 한다.
트레이트라면 새 구조체에 트레이트를 구현하기만 하면 된다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 9」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 세 가지 방식의 Strategy 패턴 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 클로저를 `Box<dyn Fn>` 필드에 보관 | `struct PricingEngine { strategy: Box<dyn Fn(f64) -> f64> }` |
| 2. `new` 가 `Box` 로 감싸 저장 | `PricingEngine::new` 의 `Box::new(strategy)` |
| 3. `calculate` 가 클로저 호출 | `(self.strategy)(price)` |
| 4. `set_strategy` 로 교체 | `PricingEngine::set_strategy` 의 `self.strategy = Box::new(strategy)` |
| 5. 클로저 팩토리 셋 | `regular_price` · `member_discount` · `fixed_discount` (`move`, `.max(0.0)`) |
| 6. 네 전략으로 100,000원 계산 | `main` 의 `engine.set_strategy(...)` · `{:.0}원` 출력 네 줄 |
| 7. `SortStrategy` 트레이트 | `trait SortStrategy { fn sort; fn name; }` |
| 8. 세 구조체의 정렬 구현과 `name` | `impl SortStrategy for BubbleSort` · `InsertionSort` · `QuickSort` |
| 9. 퀵 정렬의 분할 · 재귀 · 결합 | `QuickSort::sort` 의 `pivot`, `left` · `mid` · `right`, `self.sort(...)`, `data.clear()` · `data.extend(...)` |
| 10. `Sorter` 의 보관 · 위임 · 교체 | `struct Sorter { strategy: Box<dyn SortStrategy> }`, `Sorter::sort` 의 `println!("  [{}] 정렬 시작", …)`, `Sorter::set_strategy` |
| 11. 원본을 매번 복제해 세 번 정렬 | `main` 의 `data_original.clone()` 과 `sorter.set_strategy(Box::new(...))` |
| 12. `Validator` 트레이트 | `trait Validator { fn validate(...) -> Result<(), String>; }` |
| 13. 길이 검증 | `impl Validator for LengthValidator` 의 `input.len()` 과 `format!("길이 {}~{} 필요, 현재: {}", …)` |
| 14. 패턴 검증 | `impl Validator for PatternValidator` 의 `input.contains(&self.pattern)` |
| 15. 제네릭 검증 함수 | `fn validate_input<V: Validator>` 의 `match` |
| 16. 네 문자열 검사 | `main` 의 `length_check` · `pattern_check` 와 `validate_input` 네 번 |
| 17. 비교 세 줄 | `main` 끝의 `println!("\n=== 비교 ===")` 와 세 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-patterns/reference/strategy-pattern.rs`

```rust
// [패턴 & 관용구] Strategy 패턴
// 설명: 전략 패턴을 클로저와 트레이트 객체로 구현. 런타임 알고리즘 교체
// 팁: 단순한 전략은 클로저로, 복잡한 전략은 트레이트로 구현한다. 성능이 중요하면 제네릭(정적 디스패치)을, 런타임 교체가 필요하면 Box<dyn Trait>(동적 디스패치)를 사용한다. enum 디스패치가 트레이트 객체보다 빠른 경우가 많다.

// === Strategy 패턴: 클로저 기반 + 트레이트 기반 ===

// ===== 1. 클로저 기반 전략 =====

// 가격 계산 엔진: 클로저를 trait object로 보유
struct PricingEngine {
    strategy: Box<dyn Fn(f64) -> f64>,
}

impl PricingEngine {
    // impl Fn으로 다양한 클로저를 받아 Box로 감싸 저장
    fn new(strategy: impl Fn(f64) -> f64 + 'static) -> Self {
        PricingEngine {
            strategy: Box::new(strategy),
        }
    }

    // 전략 호출
    fn calculate(&self, price: f64) -> f64 {
        (self.strategy)(price)
    }

    // 런타임에 전략 교체
    fn set_strategy(&mut self, strategy: impl Fn(f64) -> f64 + 'static) {
        self.strategy = Box::new(strategy);
    }
}

// 전략 생성 함수 (클로저 팩토리)
// 정가 (할인 없음)
fn regular_price() -> impl Fn(f64) -> f64 {
    |price| price
}

// 비율 할인 클로저: rate를 캡처
fn member_discount(rate: f64) -> impl Fn(f64) -> f64 {
    move |price| price * (1.0 - rate)
}

// 정액 할인
fn fixed_discount(amount: f64) -> impl Fn(f64) -> f64 {
    move |price| (price - amount).max(0.0)
}

// ===== 2. 트레이트 기반 전략 =====

// 정렬 전략 인터페이스
trait SortStrategy {
    fn sort(&self, data: &mut Vec<i32>);
    fn name(&self) -> &str;
}

// 구체 전략들 (zero-sized type)
struct BubbleSort;
struct InsertionSort;
struct QuickSort;

// 버블 정렬
impl SortStrategy for BubbleSort {
    fn sort(&self, data: &mut Vec<i32>) {
        let n = data.len();
        for i in 0..n {
            for j in 0..n - 1 - i {
                if data[j] > data[j + 1] {
                    data.swap(j, j + 1);
                }
            }
        }
    }
    fn name(&self) -> &str { "BubbleSort" }
}

// 삽입 정렬
impl SortStrategy for InsertionSort {
    fn sort(&self, data: &mut Vec<i32>) {
        for i in 1..data.len() {
            let key = data[i];
            let mut j = i;
            while j > 0 && data[j - 1] > key {
                data[j] = data[j - 1];
                j -= 1;
            }
            data[j] = key;
        }
    }
    fn name(&self) -> &str { "InsertionSort" }
}

// 퀵 정렬 (단순 구현)
impl SortStrategy for QuickSort {
    fn sort(&self, data: &mut Vec<i32>) {
        if data.len() <= 1 {
            return;
        }
        // 중간값을 피벗으로
        let pivot = data[data.len() / 2];
        // 피벗 기준 분할
        let mut left: Vec<i32> = data.iter().filter(|&&x| x < pivot).copied().collect();
        let mid: Vec<i32> = data.iter().filter(|&&x| x == pivot).copied().collect();
        let mut right: Vec<i32> = data.iter().filter(|&&x| x > pivot).copied().collect();
        // 재귀
        self.sort(&mut left);
        self.sort(&mut right);
        // 결합
        data.clear();
        data.extend(left);
        data.extend(mid);
        data.extend(right);
    }
    fn name(&self) -> &str { "QuickSort" }
}

// 컨텍스트: 전략을 트레이트 객체로 보유
struct Sorter {
    strategy: Box<dyn SortStrategy>,
}

impl Sorter {
    fn new(strategy: Box<dyn SortStrategy>) -> Self {
        Sorter { strategy }
    }

    fn sort(&self, data: &mut Vec<i32>) {
        println!("  [{}] 정렬 시작", self.strategy.name());
        self.strategy.sort(data);
    }

    // 런타임 전략 교체
    fn set_strategy(&mut self, strategy: Box<dyn SortStrategy>) {
        self.strategy = strategy;
    }
}

// ===== 3. 제네릭 전략 (정적 디스패치) =====

// 검증 전략 인터페이스
trait Validator {
    fn validate(&self, input: &str) -> Result<(), String>;
}

// 길이 검증
struct LengthValidator { min: usize, max: usize }
// 패턴 포함 검증
struct PatternValidator { pattern: String }

impl Validator for LengthValidator {
    fn validate(&self, input: &str) -> Result<(), String> {
        let len = input.len();
        if len >= self.min && len <= self.max {
            Ok(())
        } else {
            Err(format!("길이 {}~{} 필요, 현재: {}", self.min, self.max, len))
        }
    }
}

impl Validator for PatternValidator {
    fn validate(&self, input: &str) -> Result<(), String> {
        if input.contains(&self.pattern) {
            Ok(())
        } else {
            Err(format!("'{}' 패턴이 포함되어야 합니다", self.pattern))
        }
    }
}

// 제네릭으로 정적 디스패치 (인라이닝 가능)
fn validate_input<V: Validator>(validator: &V, input: &str) {
    match validator.validate(input) {
        Ok(()) => println!("  '{}' -> 유효", input),
        Err(e) => println!("  '{}' -> 실패: {}", input, e),
    }
}

fn main() {
    println!("=== 1. 클로저 기반 전략 ===");
    // 초기 전략: 정가
    let mut engine = PricingEngine::new(regular_price());
    println!("정가:        {:.0}원", engine.calculate(100_000.0));

    // 전략 교체: 회원 할인
    engine.set_strategy(member_discount(0.1));
    println!("회원 10%:    {:.0}원", engine.calculate(100_000.0));

    engine.set_strategy(member_discount(0.2));
    println!("VIP 20%:     {:.0}원", engine.calculate(100_000.0));

    // 정액 할인으로 교체
    engine.set_strategy(fixed_discount(15_000.0));
    println!("15000원 할인: {:.0}원", engine.calculate(100_000.0));

    println!("\n=== 2. 트레이트 기반 전략 ===");
    // 비교용 원본 데이터
    let data_original = vec![64, 34, 25, 12, 22, 11, 90];

    // 버블 정렬 적용
    let mut sorter = Sorter::new(Box::new(BubbleSort));
    let mut data = data_original.clone();
    sorter.sort(&mut data);
    println!("  결과: {:?}", data);

    // 삽입 정렬로 교체
    sorter.set_strategy(Box::new(InsertionSort));
    let mut data = data_original.clone();
    sorter.sort(&mut data);
    println!("  결과: {:?}", data);

    // 퀵 정렬로 교체
    sorter.set_strategy(Box::new(QuickSort));
    let mut data = data_original.clone();
    sorter.sort(&mut data);
    println!("  결과: {:?}", data);

    println!("\n=== 3. 제네릭 전략 (정적 디스패치) ===");
    let length_check = LengthValidator { min: 3, max: 20 };
    let pattern_check = PatternValidator { pattern: "@".to_string() };

    // 호출마다 타입에 특화된 코드가 사용됨 (인라인 가능)
    validate_input(&length_check, "hi");
    validate_input(&length_check, "hello");
    validate_input(&pattern_check, "user@mail.com");
    validate_input(&pattern_check, "invalid");

    println!("\n=== 비교 ===");
    println!("클로저 전략:   간단한 변환/계산에 적합. 가장 가벼움");
    println!("트레이트 객체: 복잡한 알고리즘, 상태 보유. 동적 디스패치");
    println!("제네릭:        정적 디스패치, 인라이닝 가능. 최고 성능");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 컨텍스트(`PricingEngine` · `Sorter`)는 규격만 알고, 실제 일은 필드에 꽂힌 전략이 한다.
- 클로저 전략은 `Box<dyn Fn(f64) -> f64>` 에 담고 `(self.strategy)(price)` 로 부른다.
- 클로저 팩토리는 `move` 로 `rate` · `amount` 를 담아 함수 밖으로 내보낸다.
- 트레이트 전략은 필드 없는 구조체에 `SortStrategy` 를 구현하고 `Box<dyn SortStrategy>` 로 바꿔 끼운다.
- 제네릭 `validate_input<V: Validator>` 은 교체 대신 컴파일 때 타입을 굳힌다 — 실행 중 교체가 필요 없을 때의 선택이다.
- `main` 은 원본 데이터를 매번 `clone()` 해서 세 정렬이 같은 입력을 받게 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
