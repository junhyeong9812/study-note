# rust/rust-project-structures/10 — 테스트 패턴 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 이름에 `test_money_add` 가 들어간 두 개만 돈다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`test_money_add_same_currency` 와 `test_money_add_different_currency` 두 개만 실행된다.

**왜 그런가**
`cargo test` 뒤의 이름은 걸러 내기용이라, 이름에 그 문자열이 들어간 테스트만 돈다.
`test_add_panics_on_different_currency` 나 `test_money_multiply` 는 `test_money_add` 를 품지 않아 빠진다.
근거: 2-summary 「동작 방식 (5)」.

### 2. `Ok(Money { … })` 와 `Err("통화 불일치: KRW vs USD")`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
add: Ok(Money { amount: 3000, currency: "KRW" })
다른 통화: Err("통화 불일치: KRW vs USD")
```

**왜 그런가**
`add` 는 통화가 같으면 합을 `Ok` 로, 다르면 `format!("통화 불일치: {} vs {}", …)` 를 `Err` 로 돌려준다.
`{:?}` 는 `Result` 와 derive 된 `Debug` 로 구조체 이름 · 필드 이름 · 따옴표 친 문자열을 찍는다.
근거: 2-summary 「동작 방식 (1)」(derive 와 `Debug`) · 「동작 방식 (3)」. 정확한 Debug 표기 꼴은 derive 의 일반 형식에서 추론한 것이다 (원본에 근거 없음 — 추론).

### 3. 통과한다 — 같은 통화로 바꾸면 실패한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
지금 코드는 통과한다.
둘 다 `"KRW"` 면 실패한다.

**왜 그런가**
KRW + USD 는 `Err("통화 불일치: KRW vs USD")` 이고, `unwrap()` 이 이 `Err` 에서 패닉한다.
패닉 메시지에 「통화 불일치」가 들어 있으므로 `expected` 조건까지 맞아 통과다.
통화가 같으면 `add` 가 `Ok` 라서 `unwrap()` 이 패닉하지 않고, `#[should_panic]` 테스트는 「패닉하지 않음」을 실패로 판정한다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 배포 빌드에서 테스트 모듈이 통째로 빠진다

`#[cfg(test)]` 가 붙은 모듈은 테스트 빌드일 때만 컴파일되고, `cargo build` · `cargo run` 에서는 없는 것처럼 빠진다.
그래서 `MockPriceRepo` 도 `cargo run` 에서 쓰는 `main` 에서는 존재하지 않는다.
`main` 이 가짜 저장소를 쓰려면 `cfg(test)` 바깥, 즉 `main` 안에 `TestRepo` 를 따로 정의해야 했다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. `assert_eq!` 와 `.cloned()` 때문이다

- `PartialEq` — `assert_eq!(a.add(&b).unwrap(), Money::new(3000, "KRW"))` 처럼 두 `Money` 를 `==` 로 비교하려면 필요하다.
- `Debug` — `assert_eq!` 가 실패할 때 두 값을 `{:?}` 로 찍고, `main` 의 `println!("{:?}", …)` 도 쓴다.
- `Clone` — `MockPriceRepo::get_price` 의 `self.prices.get(item).cloned()` 가 `Option<&Money>` 를 `Option<Money>` 로 복제한다.

근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 6. 가짜 저장소를 끼울 자리가 없어진다

`PriceService` 가 trait 만 알면, 테스트에서 `MockPriceRepo` 처럼 정해진 가격을 주는 구현을 넣어 `calculate_total` 의 합산 로직만 검사할 수 있다.
구체 저장소 타입을 필드로 박아 두면 테스트도 진짜 DB 같은 의존성을 부를 수밖에 없어, 준비가 무겁고 결과가 바깥 상태에 흔들린다.
이것이 trait 추상화 + 의존성 주입이다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 7. 부를 수 없다 — `pub` 도 아니고 라이브러리도 아니다

`tests/` 의 파일은 크레이트 바깥에서 컴파일되는 독립 바이너리라 라이브러리의 `pub` API 만 쓸 수 있다.
예제의 `Money` 와 `new` 에는 `pub` 이 없으므로 통합 테스트에서 보이지 않는다.
이런 비공개 항목은 같은 파일의 `#[cfg(test)] mod tests` 에서 `use super::*` 로 검사한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 8. 목록 밖의 입력을 아예 보지 않는다

두 테스트는 미리 고른 값(16쌍, 4개)만 반복한다.
`proptest` 는 랜덤 입력을 만들어 훨씬 많은 경우를 시도하므로, 고른 목록에 없는 값에서 깨지는 성질을 찾을 수 있다.
예를 들어 큰 값에서 `i64` 가 넘치는 경우는 이 목록으로 드러나지 않는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 9. 손으로 쓴 `MockPriceRepo` 를 자동으로 만들어 준다 — trait 추상화는 여전히 필요하다

`#[automock]` 은 trait 에 달아 Mock 구조체를 자동 생성하므로, `MockPriceRepo` 와 그 `impl PriceRepository` 를 손으로 쓰는 수고를 덜어 준다.
그래도 의존성이 trait(`PriceRepository`)으로 추상화되어 있고, 서비스가 그 trait 을 제네릭으로 받아야 생성된 Mock 을 끼울 수 있다.
테스트 전용 크레이트이므로 `[dev-dependencies]` 에 넣는다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」 · 「어디서 틀리나 3」.

## 실습 정답

### 실습 1. 금액 계산 코드와 테스트 묶음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 필드와 derive | `#[derive(Debug, PartialEq, Clone)] struct Money` |
| 2. 생성자 | `Money::new` |
| 3. 통화 검사 덧셈 | `Money::add` 의 `if self.currency != other.currency { return Err(…) }` |
| 4. 곱셈 · 양수 여부 | `Money::multiply` · `Money::is_positive` |
| 5. 저장소 trait | `trait PriceRepository { fn get_price … }` |
| 6. 제네릭 서비스 | `struct PriceService<R: PriceRepository> { repo: R }` · `PriceService::new` |
| 7. 합계 계산 | `calculate_total` 의 `Money::new(0, "KRW")` · `ok_or(format!("가격 없음: {}", item))?` · `multiply` · `add(…)?` |
| 8. 같은 통화 덧셈 | `test_money_add_same_currency` |
| 9. 다른 통화 에러 | `test_money_add_different_currency` |
| 10. 곱셈 두 경우 | `test_money_multiply` · `test_money_multiply_zero` |
| 11. 패닉 예상 | `#[should_panic(expected = "통화 불일치")] test_add_panics_on_different_currency` |
| 테스트 모듈 분리 | `#[cfg(test)] mod tests` · `use super::*;` |
| 12. Mock 초기화 | `MockPriceRepo::new` 의 `prices.insert("coffee"…)` · `insert("bread"…)` |
| 13. Mock 구현 | `impl PriceRepository for MockPriceRepo` 의 `self.prices.get(item).cloned()` |
| 14. 합계 12000 | `test_calculate_total` |
| 15. 없는 항목 | `test_calculate_total_unknown_item` 의 `is_err()` · `unwrap_err().contains("가격 없음")` |
| 16. 교환법칙 | `test_add_is_commutative` 의 이중 `for` 와 메시지 `"교환법칙 실패: {} + {}"` |
| 17. 항등법칙 | `test_multiply_by_one_is_identity` |
| 18. 덧셈 시뮬레이션 | `main` 의 `"add: {:?}"` · `"다른 통화: {:?}"` |
| 19. 스텁 서비스 | `main` 안의 `struct TestRepo` · `match item { "apple" => …, _ => None }` · `"사과 2개"` · `"없는 상품"` |
| 20. 안내 줄 | `main` 끝의 `println!` 묶음 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-project-structures/reference/testing-patterns.rs`

```rust
// [실무 프로젝트 구조] 테스트 패턴
// 설명: #[test], mock, 통합 테스트, 프로퍼티 기반 테스트 패턴
// 팁: #[cfg(test)]로 테스트 코드를 컴파일 시 분리한다. #[should_panic]으로 패닉을 예상하는 테스트를 작성한다. Mock: trait으로 추상화하고 테스트용 구현을 만든다. mockall 크레이트는 #[automock]으로 자동 Mock을 생성한다. 통합 테스트는 tests/ 디렉토리에 두며, 공개 API만 테스트한다. proptest로 랜덤 입력 기반 프로퍼티 테스트를 작성한다.
// Rust 모듈 시스템 특징: 단위 테스트는 #[cfg(test)] mod tests {} 로 같은 파일 내 분리(use super::*;로 부모 항목 접근). 통합 테스트는 tests/ 디렉토리의 각 .rs 파일이 독립 바이너리로 컴파일된다. tests/는 lib의 pub API만 사용 가능. examples/, benches/도 비슷한 구조. dev-dependencies로 mockall 같은 테스트 전용 크레이트 분리.

// === 테스트 대상 코드 ===
// 도메인 값 객체: 통화 단위 금액
#[derive(Debug, PartialEq, Clone)]
struct Money {
    amount: i64,   // 센트 단위
    currency: String,
}

// Money의 도메인 메서드
impl Money {
    // 생성자
    fn new(amount: i64, currency: &str) -> Self {
        Money { amount, currency: currency.to_string() }
    }

    // 통화가 같을 때만 덧셈
    fn add(&self, other: &Money) -> Result<Money, String> {
        if self.currency != other.currency {
            return Err(format!("통화 불일치: {} vs {}", self.currency, other.currency));
        }
        Ok(Money::new(self.amount + other.amount, &self.currency))
    }

    // 정수배 곱셈
    fn multiply(&self, factor: i64) -> Money {
        Money::new(self.amount * factor, &self.currency)
    }

    // 양수 여부
    fn is_positive(&self) -> bool {
        self.amount > 0
    }
}

// trait으로 추상화 (mock 가능)
// 가격 조회를 추상화 → 테스트에서 가짜 구현으로 교체 가능 (DI)
trait PriceRepository {
    fn get_price(&self, item: &str) -> Option<Money>;
}

// 제네릭 R: PriceRepository로 의존성 주입
struct PriceService<R: PriceRepository> {
    repo: R,
}

// 합계 계산 비즈니스 로직
impl<R: PriceRepository> PriceService<R> {
    fn new(repo: R) -> Self {
        PriceService { repo }
    }

    // 항목 리스트 받아 총액 계산
    fn calculate_total(&self, items: &[(&str, i64)]) -> Result<Money, String> {
        let mut total = Money::new(0, "KRW");
        for (item, qty) in items {
            // 가격 없으면 에러
            let price = self.repo.get_price(item)
                .ok_or(format!("가격 없음: {}", item))?;
            let subtotal = price.multiply(*qty);
            total = total.add(&subtotal)?;
        }
        Ok(total)
    }
}

// === 테스트 모듈 ===
// #[cfg(test)]: 테스트 빌드에서만 컴파일
#[cfg(test)]
mod tests {
    // 부모 모듈의 모든 항목을 가져옴
    use super::*;

    // --- 단위 테스트 ---
    // 같은 통화 덧셈은 성공해야 함
    #[test]
    fn test_money_add_same_currency() {
        let a = Money::new(1000, "KRW");
        let b = Money::new(2000, "KRW");
        assert_eq!(a.add(&b).unwrap(), Money::new(3000, "KRW"));
    }

    // 다른 통화 덧셈은 에러
    #[test]
    fn test_money_add_different_currency() {
        let a = Money::new(1000, "KRW");
        let b = Money::new(10, "USD");
        assert!(a.add(&b).is_err());
    }

    // 곱셈 테스트
    #[test]
    fn test_money_multiply() {
        let m = Money::new(500, "KRW");
        assert_eq!(m.multiply(3), Money::new(1500, "KRW"));
    }

    // 0배 곱셈 테스트
    #[test]
    fn test_money_multiply_zero() {
        let m = Money::new(500, "KRW");
        assert_eq!(m.multiply(0), Money::new(0, "KRW"));
    }

    // 패닉 예상 테스트
    // unwrap()이 패닉을 일으키면 정상으로 간주
    #[test]
    #[should_panic(expected = "통화 불일치")]
    fn test_add_panics_on_different_currency() {
        let a = Money::new(100, "KRW");
        let b = Money::new(100, "USD");
        a.add(&b).unwrap(); // panic!
    }

    // --- Mock 테스트 ---
    // 테스트용 가짜 저장소
    struct MockPriceRepo {
        prices: std::collections::HashMap<String, Money>,
    }

    impl MockPriceRepo {
        // 미리 정의된 가격으로 초기화
        fn new() -> Self {
            let mut prices = std::collections::HashMap::new();
            prices.insert("coffee".into(), Money::new(4500, "KRW"));
            prices.insert("bread".into(), Money::new(3000, "KRW"));
            MockPriceRepo { prices }
        }
    }

    // PriceRepository trait 구현 (실 DB 대신)
    impl PriceRepository for MockPriceRepo {
        fn get_price(&self, item: &str) -> Option<Money> {
            self.prices.get(item).cloned()
        }
    }

    // 정상 합계 계산 테스트
    #[test]
    fn test_calculate_total() {
        let service = PriceService::new(MockPriceRepo::new());
        let total = service.calculate_total(&[
            ("coffee", 2),
            ("bread", 1),
        ]).unwrap();
        assert_eq!(total, Money::new(12000, "KRW")); // 4500*2 + 3000*1
    }

    // 가격 없는 항목 에러 테스트
    #[test]
    fn test_calculate_total_unknown_item() {
        let service = PriceService::new(MockPriceRepo::new());
        let result = service.calculate_total(&[("unknown", 1)]);
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("가격 없음"));
    }

    // --- 프로퍼티 기반 테스트 (수동) ---
    // 교환법칙: a + b == b + a (proptest 흉내)
    #[test]
    fn test_add_is_commutative() {
        // a + b == b + a
        for a_val in [0, 100, -50, i64::MAX / 2] {
            for b_val in [0, 200, -100, 1] {
                let a = Money::new(a_val, "KRW");
                let b = Money::new(b_val, "KRW");
                assert_eq!(a.add(&b).unwrap(), b.add(&a).unwrap(),
                    "교환법칙 실패: {} + {}", a_val, b_val);
            }
        }
    }

    // 1배 항등법칙: m * 1 == m
    #[test]
    fn test_multiply_by_one_is_identity() {
        for val in [0, 100, -50, 999999] {
            let m = Money::new(val, "KRW");
            assert_eq!(m.multiply(1), m);
        }
    }
}

// === main에서 테스트 결과 시뮬레이션 ===
// 진입점: cargo test 실행 없이 동작 확인
fn main() {
    println!("=== Rust 테스트 패턴 ===");

    // 수동으로 테스트 실행
    let a = Money::new(1000, "KRW");
    let b = Money::new(2000, "KRW");
    println!("add: {:?}", a.add(&b));

    let c = Money::new(10, "USD");
    println!("다른 통화: {:?}", a.add(&c));

    // Mock 서비스 테스트
    println!("\n--- Mock 서비스 ---");
    // main 안에서 정의한 작은 테스트 스텁
    struct TestRepo;
    impl PriceRepository for TestRepo {
        fn get_price(&self, item: &str) -> Option<Money> {
            match item {
                "apple" => Some(Money::new(1000, "KRW")),
                _ => None,
            }
        }
    }
    let service = PriceService::new(TestRepo);
    println!("사과 2개: {:?}", service.calculate_total(&[("apple", 2)]));
    println!("없는 상품: {:?}", service.calculate_total(&[("????", 1)]));

    println!("\n=== 테스트 실행 방법 ===");
    println!("cargo test                    # 전체 테스트");
    println!("cargo test test_money_add     # 이름 매칭");
    println!("cargo test -- --nocapture     # println! 출력");
    println!("cargo test -- --test-threads=1 # 직렬 실행");

    println!("\n=== 테스트 구조 ===");
    println!("tests/          # 통합 테스트 디렉토리");
    println!("  integration.rs # 각 파일이 독립 바이너리");
    println!("src/");
    println!("  lib.rs        # #[cfg(test)] mod tests {{ }}");

    println!("\n=== 유용한 크레이트 ===");
    println!("mockall:    자동 Mock 생성 (#[automock])");
    println!("proptest:   프로퍼티 기반 테스트");
    println!("rstest:     매개변수화 테스트 (#[rstest])");
    println!("test-case:  테이블 기반 테스트");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 테스트 모듈 전체를 `#[cfg(test)]` 로 감싸 Mock 까지 배포 빌드에서 빼고, `use super::*` 로 비공개 `Money` 를 그대로 쓴다.
- `assert_eq!` 와 `.cloned()` 가 각각 `PartialEq + Debug` 와 `Clone` 을 요구하므로 derive 가 먼저다.
- `calculate_total` 은 `ok_or` + `?` 로 「가격 없음」을, `add(…)?` 로 「통화 불일치」를 그대로 위로 올린다.
- 패닉 테스트는 `expected` 로 패닉 이유까지 못 박는다 — 에러를 `Result` 로 확인하는 테스트(`is_err`)와 둘 다 둔다.
- 프로퍼티 테스트는 값 목록 반복이라 흉내일 뿐이며, 실패 메시지에 입력 값을 넣어 어느 쌍에서 깨졌는지 보이게 한다.
- `main` 의 `TestRepo` 는 `cfg(test)` 밖에서 쓸 수 있는 작은 스텁으로, 같은 trait 덕분에 `PriceService` 에 그대로 들어간다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
