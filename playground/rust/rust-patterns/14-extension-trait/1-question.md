# rust/rust-patterns/14 — 확장 트레이트 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `impl Display for Vec<i32>` 는 거부되는데 `impl StringExt for str` 는 받아들여지는 까닭 (왜)
- 둘 다 표준 라이브러리 타입에 구현하는데, 한쪽만 허용되는 까닭은 무엇인가?

### 2. 본문이 빈 `impl<I: Iterator> IteratorExt for I {}` 로 `tap_each` 를 쓸 수 있는 까닭 (왜)
- `impl` 블록이 비어 있는데도 모든 반복자에서 `tap_each` 를 부를 수 있는 까닭은 무엇인가?
- `IteratorExt` 에 `Sized` 슈퍼트레이트가 필요한 까닭은 무엇인가?

### 3. 28바이트 문장을 15로 자르면 (예측)

```rust
// 질문용 발췌
let text = "Hello World Rust Programming";
println!("잘라내기: '{}'", text.truncate_with_ellipsis(15));
```

- 이 줄은 무엇을 찍는가?

### 4. 같은 벡터를 정렬했을 때와 중복을 뺐을 때 (예측)
- `vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3]` 을 `clone()` 해 `sorted()` 를 부르면 무엇이 나오나?
- 같은 벡터를 `clone()` 해 `unique()` 를 부르면 무엇이 나오나?

### 5. `tap_each` 두 개를 낀 파이프라인의 출력 차례 (예측)

```rust
// 질문용 발췌
let result: Vec<i32> = vec![1, 2, 3, 4, 5].into_iter()
    .tap_each(|x| print!("  처리: {} ->", x))
    .map(|x| x * x)
    .tap_each(|x| println!(" {}", x))
    .collect();
println!("  결과: {:?}", result);
```

- 화면에 찍히는 줄들은 어떤 차례로 나오나?

### 6. 음수 리터럴에 `clamp_to` 부르기 (예측)

```rust
// 질문용 발췌
println!("{}", 150_i32.clamp_to(0, 100));
println!("{}", (-5_i32).clamp_to(0, 100));
println!("{}", -5_i32.clamp_to(0, 100));
```

- 세 줄은 각각 무엇을 찍는가?

### 7. 확장 메서드가 보이는 범위 (경계)
- `StringExt` 를 다른 모듈에 두고 `use` 없이 `"a".is_blank()` 를 부르면 어떻게 되나?
- 확장 메서드와 이름이 같은 고유 메서드가 그 타입에 있으면 어느 쪽이 불리나?

### 8. 빈도 정렬 결과의 순서 (경계)
- 원본 `main` 의 「빈도」 줄에서 개수가 같은 원소들의 순서는 실행할 때마다 같다고 할 수 있나?

### 9. `truncate_with_ellipsis` 가 약속을 어기는 경우 (경계)
- 6글자 한글 문자열 `"가나다라마바"` 에 `truncate_with_ellipsis(10)` 을 부르면 결과는 원래보다 짧아지나?
- `max_len` 이 2 일 때 긴 문자열을 자른 결과는 2글자 이하인가?

### 10. 확장 트레이트와 이미 아는 것들 사이의 다리 (연결)
- 직접 만든 `tap_each` 는 표준 `map` 같은 어댑터와 어떤 점에서 같은 구조인가?
- `str` 에만 구현한 `StringExt` 의 메서드를 `String` 값에서도 부를 수 있는 까닭은 무엇인가?

## 실습

### 실습 1. 문자열 · Vec · Iterator · 숫자에 확장 트레이트 붙이기

**만들 것** — 표준 타입 `str` · `Vec<T>` · 모든 `Iterator` · `f64` · `i32` 에 확장 트레이트로 메서드를 덧붙이고, 시작 코드의 `main` 이 그대로 돌아가게 한다.

**요구 조건**

1단계 — 문자열 확장
1. `str` 에 `StringExt` 를 구현한다.
2. `truncate_with_ellipsis(max_len)` — 바이트 길이가 `max_len` 이하면 그대로 복사하고, 넘으면 앞에서 `max_len - 3` 글자(0 아래로 내려가지 않게)만 남기고 `...` 를 붙인다.
3. `is_blank()` — 앞뒤 공백을 지운 결과가 비었으면 `true`.
4. `to_title_case()` — 공백으로 단어를 나누고, 단어마다 첫 글자는 대문자 · 나머지는 소문자로 바꿔 공백 하나로 다시 잇는다.
5. `repeat_with_separator(n, sep)` — 자기 자신을 `n` 번 반복해 `sep` 으로 잇는다.

2단계 — Vec 확장
6. 제네릭 트레이트 `VecExt<T>` 에 `sorted` · `unique` · `frequencies` 를 선언하고, 메서드마다 필요한 조건(`Ord` / `Eq + Hash + Clone` / `Eq + Hash`)을 `where` 로 붙인다.
7. `sorted` 는 벡터를 받아(소비) 제자리 정렬한 뒤 돌려준다.
8. `unique` 는 벡터를 받아 `HashSet` 으로 본 값을 기록하며, 처음 나온 순서대로 중복을 뺀다.
9. `frequencies` 는 빌려 읽어 원소 참조를 키로, 개수를 값으로 하는 `HashMap` 을 돌려준다.
10. `impl<T> … for Vec<T>` 로 모든 `Vec<T>` 에 구현한다.

3단계 — Iterator 확장
11. `IteratorExt` 는 `Iterator + Sized` 를 슈퍼트레이트로 갖고, `tap_each` 와 `intersperse_with` 를 **기본 메서드**로 가진다(각각 `TapEach` · `IntersperseWith` 구조체를 만들어 돌려준다).
12. blanket impl 한 줄로 모든 `Iterator` 에 `IteratorExt` 를 적용한다.
13. `TapEach` 의 `next` 는 안쪽에서 하나 꺼내 콜백에 참조로 보여 준 뒤 그대로 돌려준다.
14. `IntersperseWith` 의 `next` 는 `needs_sep` · `next_item` 상태로 원소 사이에 구분자 복제본을 끼워 `a, 구분자, b, 구분자, c` 차례로 돌려준다.

4단계 — 숫자 확장
15. `NumExt` 를 `f64` 와 `i32` 에 각각 구현한다.
16. `clamp_to(min, max)` — 범위 밖이면 가까운 경계값, 안이면 자기 자신.
17. `is_between(min, max)` — 양 끝을 포함해 범위 안이면 `true`.

5단계 — 확인
18. 시작 코드의 `main` 을 고치지 않고 컴파일 · 실행되게 한다.

**시작 코드**

```rust
// 확장 트레이트 연습 — TODO 자리를 채운다

// ===== 1. 문자열 확장 =====
trait StringExt {
    fn truncate_with_ellipsis(&self, max_len: usize) -> String;
    fn is_blank(&self) -> bool;
    fn to_title_case(&self) -> String;
    fn repeat_with_separator(&self, n: usize, sep: &str) -> String;
}

// TODO: str 에 StringExt 를 구현한다 (impl 머리줄과 네 메서드 본문)

// ===== 2. Vec 확장 =====
trait VecExt<T> {
    // TODO: sorted · unique · frequencies 시그니처 (메서드마다 where 절)
}

// TODO: 모든 Vec<T> 에 VecExt<T> 를 구현한다

// ===== 3. Iterator 확장 =====
trait IteratorExt: Iterator + Sized {
    // TODO: tap_each — 기본 메서드. TapEach 를 만들어 돌려준다
    // TODO: intersperse_with — 기본 메서드. IntersperseWith 를 만들어 돌려준다
}

// TODO: 모든 Iterator 에 IteratorExt 를 적용하는 blanket impl 한 줄

struct TapEach<I, F> {
    iter: I,
    f: F,
}

// TODO: TapEach 에 Iterator 구현 (콜백에 보여 준 뒤 그대로 넘긴다)

struct IntersperseWith<I: Iterator> where I::Item: Clone {
    iter: I,
    separator: I::Item,
    needs_sep: bool,
    next_item: Option<I::Item>,
}

// TODO: IntersperseWith 에 Iterator 구현

// ===== 4. 숫자 확장 =====
trait NumExt {
    fn clamp_to(self, min: Self, max: Self) -> Self where Self: Sized;
    fn is_between(&self, min: Self, max: Self) -> bool where Self: Sized;
}

// TODO: f64 와 i32 에 NumExt 를 각각 구현한다

fn main() {
    println!("=== 1. 문자열 확장 ===");
    let text = "Hello World Rust Programming";
    println!("원본: '{}'", text);
    println!("잘라내기: '{}'", text.truncate_with_ellipsis(15));
    println!("타이틀: '{}'", "hello WORLD rust".to_title_case());
    println!("빈 문자열: {}", "   ".is_blank());
    println!("반복: '{}'", "ha".repeat_with_separator(3, ", "));

    println!("\n=== 2. Vec 확장 ===");
    let numbers = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3];
    println!("원본: {:?}", numbers);
    println!("정렬: {:?}", numbers.clone().sorted());
    println!("중복제거: {:?}", numbers.clone().unique());

    let freq = numbers.frequencies();
    let mut freq_vec: Vec<_> = freq.iter().collect();
    freq_vec.sort_by_key(|(_, &count)| std::cmp::Reverse(count));
    println!("빈도: {:?}", freq_vec);

    println!("\n=== 3. Iterator 확장: tap_each ===");
    let result: Vec<i32> = vec![1, 2, 3, 4, 5].into_iter()
        .tap_each(|x| print!("  처리: {} ->", x))
        .map(|x| x * x)
        .tap_each(|x| println!(" {}", x))
        .collect();
    println!("  결과: {:?}", result);

    println!("\n=== 4. 숫자 확장 ===");
    println!("clamp 150 to (0, 100): {}", 150_i32.clamp_to(0, 100));
    println!("clamp -5 to (0, 100): {}", (-5_i32).clamp_to(0, 100));
    println!("3.14 is_between(0, 5): {}", 3.14_f64.is_between(0.0, 5.0));
    println!("10.0 is_between(0, 5): {}", 10.0_f64.is_between(0.0, 5.0));

    println!("\n=== 확장 트레이트 규칙 ===");
    println!("1. 고아 규칙: 트레이트나 타입 중 하나는 현재 크레이트에 정의");
    println!("2. use로 트레이트를 가져와야 확장 메서드 사용 가능");
    println!("3. 기존 메서드와 이름 충돌 시 원래 메서드가 우선");
    println!("4. blanket impl (impl<I: Iterator> Ext for I)로 모든 구현체에 적용");
}
```

**확인 방법** — `rustc extension-trait.rs && ./extension-trait` 로 돌려 본다.
「잘라내기」 줄이 15글자로 끝에 `...` 가 붙는지, 「중복제거」가 처음 나온 순서를 지키는지, 「처리」 줄이 원소마다 `n -> n²` 한 줄씩 나오는지, `clamp -5` 가 0 인지 본다.
`intersperse_with` 는 `main` 이 부르지 않으니, 원하면 `vec!["a", "b", "c"].into_iter().intersperse_with("-")` 를 `collect` 해 `a - b - c` 차례인지 따로 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
