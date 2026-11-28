# rust/rust-project-structures/10 — 테스트 패턴 — 정리 (힌트)

> 출처 — study-site 항목 `rust/testing-patterns`(항목 데이터 `data/rust/project-structures.json`) · 정답 코드 study-practice `rust/rust-project-structures/reference/testing-patterns.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**Rust 의 테스트는 「공장 안의 검수실」이다.**
검수실은 출하할 제품(배포용 바이너리)에는 실리지 않고, 검수할 때만 문을 연다.
검수실 안에서는 진짜 부품 대신 **모형 부품**(mock)을 끼워 기계가 제대로 도는지 본다.
「불량을 넣으면 반드시 경보가 울려야 한다」는 검사도 있고(`should_panic`), 공장 밖 손님 자리에서 완제품만 써 보는 검사도 있다(통합 테스트).
Rust 테스트도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 검수실 | `#[cfg(test)] mod tests { … }` |
| 검수 항목 하나 | `#[test]` 가 붙은 함수 |
| 합격 기준 | `assert!` · `assert_eq!` |
| 경보가 울려야 합격 | `#[should_panic(expected = "…")]` |
| 모형 부품 | trait 을 구현한 테스트용 구조체 (`MockPriceRepo`) |
| 손님 자리 검사 | `tests/` 디렉토리의 통합 테스트 |
| 여러 재료로 같은 성질 확인 | 프로퍼티 기반 테스트 |

```text
 src/main.rs (또는 lib.rs)
 ┌───────────────────────────────┐
 │ Money, PriceService …  (제품) │ ← cargo build / cargo run 에 실림
 │ #[cfg(test)] mod tests {      │
 │    #[test] fn …               │ ← cargo test 때만 컴파일
 │    struct MockPriceRepo       │
 │ }                             │
 └───────────────────────────────┘
 tests/integration.rs              ← 따로 컴파일되는 손님. pub API 만 쓴다
```

## 이 주제가 답하려는 질문

1. 테스트 코드를 같은 파일에 두면서 어떻게 배포 바이너리에서 빼나?
2. 데이터베이스처럼 테스트에서 쓰기 곤란한 의존성을 어떻게 가짜로 바꿔 끼우나?
3. 「실패해야 맞는」 경우와 「어떤 입력에도 성립해야 하는 성질」은 어떻게 검사하나?
4. 단위 테스트와 통합 테스트는 어디에 두고, 어떻게 골라서 돌리나?

## 동작 방식

### (1) 단위 테스트 — `#[cfg(test)]` 검수실

**언제 쓰나** — 함수 하나, 메서드 하나가 기대한 값을 내는지 바로 옆에서 확인할 때 쓴다.

```text
 #[cfg(test)]                 cargo test       →  --test 빌드: cfg(test) 가 참
 mod tests {                                       tests 모듈 컴파일
     use super::*;                                 #[test] 함수를 모아 하나씩 실행
     #[test]                  cargo build/run  →  cfg(test) 가 거짓
     fn test_money_multiply()                      tests 모듈 통째로 빠짐
       { assert_eq!(…) }
 }
                         결과: 테스트마다 ok / FAILED
```

- `#[cfg(test)]` 는 「테스트 빌드일 때만 이 항목을 컴파일하라」는 조건부 컴파일 표시다.
- `cargo test` 는 테스트 빌드를 만들고, `#[test]` 가 붙은 함수를 모아 하나씩 부른다.
- `cargo build` · `cargo run` 에서는 `tests` 모듈이 아예 없는 것처럼 컴파일된다.
- `use super::*;` 는 부모 모듈(테스트 대상 코드가 있는 곳)의 항목을 모두 끌어온다.
- 그래서 `Money` 처럼 `pub` 이 아닌 항목도 단위 테스트에서 바로 쓸 수 있다.
- 테스트 함수가 패닉 없이 끝나면 통과, 패닉하면 실패다.

> **조건부 컴파일** — 설정 값(`cfg`)이 참일 때만 그 코드를 컴파일하는 것.\
> 예: `#[cfg(test)]` 는 테스트 빌드에서만 참이다.

판정에 쓰는 매크로는 둘이다.

- `assert!(조건)` — 조건이 `false` 면 패닉한다. `a.add(&b).is_err()` 처럼 참·거짓을 볼 때 쓴다.
- `assert_eq!(왼쪽, 오른쪽)` — 둘이 `==` 로 같지 않으면 패닉하고, 두 값을 `{:?}` 로 찍어 보여 준다.
- 그래서 `assert_eq!` 에 넣는 타입은 `PartialEq`(비교)와 `Debug`(출력)를 구현해야 한다 — `Money` 가 `#[derive(Debug, PartialEq, Clone)]` 를 단 까닭이다.
- 두 매크로 모두 마지막에 메시지 형식 문자열을 더 줄 수 있다: `assert_eq!(x, y, "교환법칙 실패: {} + {}", a_val, b_val)`.

> **단위 테스트** — 모듈 안의 작은 단위(함수 · 메서드)를 그 모듈 곁에서 검사하는 테스트.\
> 예: `test_money_multiply` 는 `Money::multiply` 하나만 본다.

### (2) `#[should_panic]` — 경보가 울려야 합격

**언제 쓰나** — 잘못된 입력에서 반드시 패닉해야 하는 코드를 검사할 때 쓴다.

```text
 #[test]
 #[should_panic(expected = "통화 불일치")]
 fn … { a.add(&b).unwrap(); }       a: KRW, b: USD
          │
          ▼
 add → Err("통화 불일치: KRW vs USD")
          │ unwrap()
          ▼
 패닉! 메시지에 "통화 불일치" 포함   → 통과
 (패닉 없이 끝나면)                  → 실패
 (패닉했지만 메시지에 문자열 없음)    → 실패
```

- `Result` 의 `unwrap()` 은 `Err` 를 만나면 패닉한다.
- `#[should_panic]` 은 판정을 뒤집는다: 패닉하면 통과, 패닉하지 않으면 실패다.
- `expected = "…"` 를 붙이면 패닉 메시지에 그 문자열이 **들어 있는지**까지 본다.
- `expected` 가 없으면 어떤 패닉이든 통과한다 — 엉뚱한 곳에서 터져도 통과해 버린다.

> **패닉** — 복구하지 않고 현재 스레드를 멈추는 Rust 의 오류 처리.\
> 예: `Err(…)` 에 `.unwrap()` 을 부르면 패닉한다.

### (3) Mock — trait 으로 추상화하고 가짜를 끼운다

**언제 쓰나** — 테스트할 로직이 DB · 네트워크 같은 바깥 의존성을 부를 때, 그 의존성을 정해진 값만 돌려주는 가짜로 바꾸고 싶을 때 쓴다.

```text
 trait PriceRepository { fn get_price(&self, item) -> Option<Money>; }
             ▲                                 ▲
     impl (운영) 실 DB 저장소         impl (테스트) MockPriceRepo
                                        HashMap: coffee→4500, bread→3000
             │                                 │
             └──────── PriceService<R> ────────┘
                       repo: R  (어느 쪽이든 받음)

 calculate_total(&[("coffee",2), ("bread",1)])
   coffee → 4500 ×2 = 9000   total 0+9000   = 9000
   bread  → 3000 ×1 = 3000   total 9000+3000 = 12000
   → Ok(Money { 12000, KRW })
 calculate_total(&[("unknown",1)])
   get_price → None → ok_or → Err("가격 없음: unknown") → ? 로 바로 반환
```

- `PriceRepository` trait 은 「가격을 물으면 `Option<Money>` 를 준다」는 약속만 정한다.
- `PriceService<R: PriceRepository>` 는 구체 저장소가 아니라 그 약속을 지키는 아무 `R` 이나 받는다.
- 바깥에서 의존성을 넣어 주는 이 방식을 의존성 주입(DI)이라 부른다.
- 테스트 모듈은 `MockPriceRepo` 를 만들어 `HashMap` 에 고정 가격을 넣고, `get_price` 를 `self.prices.get(item).cloned()` 로 구현한다.
- `.cloned()` 는 `Option<&Money>` 를 `Option<Money>` 로 복제한다 — `Money` 가 `Clone` 을 derive 한 까닭이다.
- `calculate_total` 은 `ok_or(…)` 로 `None` 을 `Err(String)` 으로 바꾸고, `?` 로 에러를 곧바로 돌려준다.
- 합계는 언제나 `Money::new(0, "KRW")` 에서 시작하므로, 저장소가 다른 통화를 주면 `total.add(&subtotal)?` 가 「통화 불일치」 에러를 낸다.
- `main` 의 `TestRepo` 처럼 `match` 로 값 하나만 돌려주는 더 작은 가짜(스텁)도 같은 원리다.
- `mockall` 크레이트를 쓰면 trait 에 `#[automock]` 을 달아 이런 가짜 구조체를 자동으로 만들 수 있다.

> **Mock(목)** — 테스트에서 진짜 의존성 대신 끼우는 가짜 구현.\
> 예: 실 DB 대신 `HashMap` 에서 가격을 꺼내는 `MockPriceRepo`.

> **의존성 주입(DI)** — 객체가 쓸 의존성을 안에서 만들지 않고 바깥에서 넣어 받는 방식.\
> 예: `PriceService::new(MockPriceRepo::new())`.

### (4) 프로퍼티 기반 테스트 — 값이 아니라 성질을 검사한다

**언제 쓰나** — 「`a + b == b + a`」「`m × 1 == m`」처럼 어떤 입력에도 성립해야 하는 성질이 있을 때 쓴다.

```text
 for a_val in [0, 100, -50, i64::MAX/2]
   for b_val in [0, 200, -100, 1]          → 4 × 4 = 16 쌍
     assert_eq!(a.add(&b), b.add(&a), "교환법칙 실패: {} + {}", a_val, b_val)

 for val in [0, 100, -50, 999999]          → 4 개
     assert_eq!(m.multiply(1), m)
                          결과: 한 쌍이라도 어긋나면 그 값이 메시지에 찍히며 실패
```

- 예제 코드는 정해 둔 몇 개의 값을 반복문으로 돌려 성질을 확인한다 — `proptest` 를 흉내 낸 「수동」 판이다.
- 진짜 `proptest` 는 입력을 랜덤으로 만들어 훨씬 많은 경우를 시도한다.
- 수동 판은 고른 값만 본다: 넘침이 나는 큰 값처럼 목록에 없는 입력은 검사하지 않는다.
- 실패 메시지에 입력 값을 넣어 두면 어느 쌍에서 깨졌는지 바로 안다.

> **프로퍼티(성질)** — 입력이 무엇이든 참이어야 하는 관계.\
> 예: 교환법칙 `a + b == b + a`.

### (5) 통합 테스트와 `cargo test` 실행

**언제 쓰나** — 크레이트를 바깥 사용자처럼 쓰는 시나리오를 검사할 때, 그리고 테스트를 골라 돌릴 때 쓴다.

```text
 my_crate/
 ├─ src/lib.rs        #[cfg(test)] mod tests { }   ← 단위 테스트 (비공개 항목도 접근)
 ├─ tests/
 │   └─ integration.rs                              ← 독립 바이너리, pub API 만 사용
 ├─ examples/ , benches/                            ← 비슷한 구조
 └─ Cargo.toml  [dev-dependencies] mockall …        ← 테스트 전용 크레이트

 cargo test                        모든 테스트
 cargo test test_money_add         이름에 test_money_add 가 들어간 테스트만
 cargo test -- --nocapture         테스트 안의 println! 을 보여 줌
 cargo test -- --test-threads=1    한 번에 하나씩 직렬 실행
```

- `tests/` 의 `.rs` 파일은 각각 따로 컴파일되는 독립 바이너리다.
- 통합 테스트는 크레이트를 바깥에서 가져다 쓰므로 라이브러리(`lib`)의 `pub` 항목만 쓸 수 있다.
- `mockall` · `proptest` 처럼 테스트에서만 쓰는 크레이트는 `[dev-dependencies]` 에 넣어 배포 빌드와 분리한다.
- `cargo test` 뒤의 이름은 걸러 내기용이다 — 이름에 그 문자열이 들어간 테스트만 돈다.
- `--` 뒤의 옵션은 cargo 가 아니라 테스트 바이너리에 넘어간다.
- 테스트 안의 `println!` 은 기본으로 감춰지고, `--nocapture` 를 주면 보인다.
- `--test-threads=1` 은 테스트를 하나씩 차례로 돌린다 — 기본은 여러 스레드에서 함께 돈다.
- 예제의 `main` 은 `cargo test` 없이도 동작을 눈으로 보도록 같은 호출을 `println!` 으로 찍는 시뮬레이션이다.

> **통합 테스트** — 크레이트를 바깥 사용자처럼 공개 API 로만 쓰며 여러 부분을 함께 검사하는 테스트.\
> 예: `tests/integration.rs`.

## 문법 — 형태와 규칙

```rust
pub fn half(x: i32) -> i32 {
    if x % 2 != 0 { panic!("홀수는 반으로 못 나눔: {}", x); }
    x / 2
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn half_of_even() {
        assert_eq!(half(10), 5);
    }

    #[test]
    #[should_panic(expected = "홀수")]
    fn half_of_odd_panics() {
        half(3);
    }
}
```

- 테스트 모듈: `#[cfg(test)] mod tests { use super::*; … }` 이 관례다.
- 테스트 함수: `#[test] fn 이름() { … }` — 인자 없이, 패닉하면 실패.
- 패닉 예상: `#[test]` 아래에 `#[should_panic]` 또는 `#[should_panic(expected = "부분 문자열")]`.
- 비교: `assert!(bool)` · `assert_eq!(a, b)` — 뒤에 형식 문자열과 인자를 덧붙일 수 있다.
- `assert_eq!` 의 값 타입은 `PartialEq + Debug` 가 필요하다.
- Mock 준비: 의존성을 `trait` 으로 정의 → 서비스를 `struct S<R: Trait> { repo: R }` 로 만든다 → 테스트 모듈 안에 `impl Trait for MockX` 를 둔다.
- 통합 테스트: 크레이트 뿌리의 `tests/*.rs`, `pub` API 만.
- 실행: `cargo test [이름 필터] [-- 테스트 옵션]`.

## 어디서 틀리나

### 1. `#[cfg(test)]` 를 빼먹는다

`#[cfg(test)]` 없이 `mod tests` 만 두면 테스트 도우미(`MockPriceRepo` 등)가 배포 빌드에도 컴파일된다.
`#[test]` 함수 자체는 테스트 빌드가 아니면 실행되지 않지만, 모듈 안의 다른 항목은 실린다.
그래서 「테스트 코드를 컴파일 시 분리한다」는 팁대로 모듈째 `#[cfg(test)]` 로 감싼다.
반대로 `cfg(test)` 안의 `MockPriceRepo` 는 `main` 에서 쓸 수 없다 — 예제의 `main` 이 `TestRepo` 를 따로 정의한 까닭이다.

### 2. `#[should_panic]` 에 `expected` 를 안 붙인다

`expected` 가 없으면 어떤 패닉이든 통과로 친다.
테스트 준비 단계에서 엉뚱한 패닉이 나도 초록불이 켜진다.
예제처럼 `expected = "통화 불일치"` 로 「어떤 이유로 패닉해야 하나」를 못 박는다.
`expected` 는 메시지 전체가 아니라 들어 있어야 할 부분 문자열이다.

### 3. 의존성을 구체 타입으로 박아 둔다

`PriceService` 가 실 DB 타입을 필드로 직접 들고 있으면 테스트에서 바꿔 끼울 길이 없다.
팁대로 trait 으로 추상화하고(`PriceRepository`), 서비스는 제네릭 `R` 로 받아야 테스트용 구현을 만들 수 있다.
손으로 가짜를 쓰기 번거로우면 `mockall` 의 `#[automock]` 이 trait 에서 Mock 을 자동 생성한다.

### 4. 통합 테스트에서 비공개 항목을 부르려 한다

`tests/` 는 크레이트 바깥이므로 라이브러리의 `pub` API 만 보인다.
예제의 `Money` · `PriceService` 처럼 `pub` 이 없는 항목은 통합 테스트에서 쓸 수 없다.
비공개 세부는 단위 테스트(`use super::*`)에서, 공개 동작은 통합 테스트에서 검사한다.

### 5. 수동 프로퍼티 테스트를 「충분하다」고 믿는다

예제의 교환법칙 테스트는 16쌍, 항등법칙 테스트는 4개 값만 본다.
`proptest` 처럼 랜덤 입력을 만들지 않으므로 목록 밖의 값은 검사되지 않는다.
예를 들어 `multiply` 에 아주 큰 값을 넣어 `i64` 가 넘치는 경우는 이 목록으로는 드러나지 않는다.
`i64::MAX / 2` 에 200 을 더하는 정도는 넘치지 않지만, 곱셈은 쉽게 넘친다.

### 6. 테스트 안의 `println!` 이 안 보인다고 당황한다

`cargo test` 는 기본으로 테스트의 표준 출력을 가둔다.
보려면 `cargo test -- --nocapture` 를 쓴다.

### 7. 테스트끼리 상태를 나눠 쓴다

테스트는 기본으로 여러 스레드에서 동시에 돈다.
같은 파일 · 전역 값을 건드리는 테스트끼리는 순서에 따라 결과가 흔들린다.
급하면 `-- --test-threads=1` 로 직렬로 돌리지만, 테스트마다 자기 데이터를 쓰게 만드는 편이 근본 해결이다.

### 8. 테스트되지 않은 메서드가 남는다

예제의 `is_positive` 는 어떤 테스트도 부르지 않는다.
`main` 에서도 안 쓰이므로 컴파일러가 「쓰이지 않는 코드」 경고를 낼 수 있다(확인 필요).
테스트 목록을 볼 때 공개 동작마다 테스트가 있는지 짚어 본다.

### 9. 합계가 KRW 로 고정돼 있다

`calculate_total` 은 `Money::new(0, "KRW")` 에서 시작한다.
Mock 이 `USD` 가격을 주면 첫 덧셈에서 「통화 불일치」 에러가 난다.
Mock 데이터를 만들 때 서비스가 가정하는 통화를 맞춘다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `#[cfg(test)]` 항목은 테스트 빌드에서만 컴파일된다 | rustc 의 조건부 컴파일 — `test` 설정은 테스트 하니스로 빌드할 때 켜진다 |
| `#[test]` · `#[should_panic]` 함수를 모아 실행·판정한다 | 표준 테스트 하니스(libtest) |
| 테스트가 기본으로 여러 스레드에서 돈다 · `--test-threads` · `--nocapture` · 이름 필터 | 표준 테스트 하니스의 동작 (언어 보장 아님) |
| `tests/` 의 각 파일이 독립 바이너리가 된다 · `[dev-dependencies]` | Cargo 의 디렉토리 관례 |
| 통합 테스트는 `pub` API 만 쓸 수 있다 | 언어의 가시성 규칙 — `tests/` 가 바깥 크레이트로 컴파일되기 때문 |
| `#[automock]` · 랜덤 입력 생성 | 외부 크레이트 `mockall` · `proptest` (지원 범위는 버전에 따라 다름, 확인 필요) |
| `i64` 넘침 때 패닉하거나 값이 감긴다 | 언어가 정의한 동작이지만 어느 쪽인지는 빌드 설정(넘침 검사 켜짐 여부)에 따른다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 메서드 하나의 결과 확인 | `#[cfg(test)] mod tests` 안의 `#[test]` + `assert_eq!` | `main` 에 `println!` 찍어 눈으로 비교 |
| 잘못된 입력에서 패닉해야 함 | `#[should_panic(expected = "…")]` | `expected` 없는 `#[should_panic]` |
| 에러를 `Result` 로 돌려주는지 확인 | `assert!(r.is_err())` · `unwrap_err().contains(…)` | 패닉 테스트로 바꿔 검사 |
| DB · 네트워크에 기대는 로직 | trait + 제네릭 주입 + 테스트용 구현(또는 `#[automock]`) | 구체 저장소 타입을 필드에 박기 |
| 어떤 입력에도 성립할 성질 | 프로퍼티 테스트(`proptest`, 급하면 값 목록 반복) | 값 하나짜리 테스트만 두기 |
| 크레이트를 바깥 사용자처럼 검사 | `tests/*.rs` 통합 테스트 | 통합 테스트에서 비공개 항목 접근 시도 |
| 테스트 전용 크레이트 | `[dev-dependencies]` | `[dependencies]` 에 넣어 배포 빌드에 섞기 |

## 핵심 문장

1. **`#[cfg(test)] mod tests` 는 테스트 빌드에서만 컴파일되는 검수실이다** — `use super::*` 로 부모의 비공개 항목까지 쓴다.
2. **`#[should_panic(expected = "…")]` 는 「이 이유로 패닉해야 통과」다** — `expected` 가 판정을 날카롭게 만든다.
3. **Mock 의 핵심은 trait 추상화와 제네릭 주입이다** — 서비스가 trait 만 알면 테스트에서 가짜를 끼울 수 있다.
4. **프로퍼티 테스트는 값이 아니라 성질을 검사한다** — 값 목록 반복은 흉내일 뿐, 랜덤 입력은 `proptest` 가 맡는다.
5. **통합 테스트는 `tests/` 의 독립 바이너리이고 `pub` API 만 본다.**

## 관련 자료

- `error-handling-app` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `crud-service` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `rest-api-axum` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/project-structures.json` 의 `testing-patterns`

## 용어 풀이

- **단위 테스트** — 함수 · 메서드 같은 작은 단위를 그 모듈 곁에서 검사하는 테스트.
- **통합 테스트** — 크레이트를 공개 API 로만 쓰며 여럿을 함께 검사하는 테스트, `tests/` 에 둔다.
- **조건부 컴파일** — `cfg` 설정이 참일 때만 코드를 컴파일하는 것.
- **`#[cfg(test)]`** — 테스트 빌드에서만 컴파일하라는 표시.
- **`#[test]`** — 테스트 하니스가 실행할 테스트 함수 표시.
- **`#[should_panic]`** — 패닉해야 통과하는 테스트 표시, `expected` 로 메시지 부분 문자열을 지정한다.
- **`assert!` / `assert_eq!`** — 조건 · 동등이 깨지면 패닉해 테스트를 실패시키는 매크로.
- **패닉** — 복구하지 않고 현재 스레드를 멈추는 오류 처리.
- **Mock(목)** — 진짜 의존성 대신 끼우는 테스트용 가짜 구현.
- **스텁** — 정해진 값만 돌려주는 아주 단순한 가짜, 예제 `main` 의 `TestRepo`.
- **의존성 주입(DI)** — 의존성을 바깥에서 넣어 받는 방식.
- **trait** — 타입이 구현해야 할 메서드 묶음을 정한 약속.
- **제네릭 트레이트 경계** — `R: PriceRepository` 처럼 타입 매개변수가 지킬 trait 을 정한 것.
- **프로퍼티 기반 테스트** — 여러 입력에서 성질이 성립하는지 확인하는 테스트.
- **`mockall`** — `#[automock]` 으로 Mock 을 자동 생성하는 크레이트.
- **`proptest`** — 랜덤 입력 기반 프로퍼티 테스트 크레이트.
- **`rstest`** — `#[rstest]` 로 매개변수화 테스트를 쓰는 크레이트.
- **`test-case`** — 테이블 기반 테스트 크레이트.
- **`[dev-dependencies]`** — 테스트 · 예제 · 벤치에서만 쓰는 의존성 목록.
- **`--nocapture`** — 테스트의 표준 출력을 감추지 않게 하는 옵션.
- **`--test-threads=1`** — 테스트를 한 스레드에서 차례로 돌리게 하는 옵션.

## 더 들어가면

- 테스트 함수는 `Result<(), E>` 를 돌려줄 수도 있어, 본문에서 `?` 를 쓸 수 있다 — 이 경우 `#[should_panic]` 과 함께 쓸 수 없다 (확인 필요).
- `#[ignore]` 를 붙인 테스트는 기본 실행에서 빠지고 `cargo test -- --ignored` 로 따로 돌린다 (확인 필요).
- 문서 주석 안의 코드 블록도 `cargo test` 가 문서 테스트로 실행한다 (확인 필요).
- `ok_or(format!(…))` 는 성공일 때도 문자열을 먼저 만든다; `ok_or_else(|| format!(…))` 는 실패일 때만 만든다 (확인 필요).
- `proptest` 는 실패한 입력을 더 작은 입력으로 줄여(축소, shrinking) 보여 준다 (확인 필요).
- `unwrap()` 의 패닉 메시지는 `Err` 값을 `{:?}` 로 찍어 포함하므로, `expected` 부분 문자열 비교가 그 안에서 이뤄진다 (확인 필요).
