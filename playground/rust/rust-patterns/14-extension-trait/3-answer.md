# rust/rust-patterns/14 — 확장 트레이트 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 고아 규칙 — 트레이트나 타입 중 하나가 내 것이어야 한다

`impl Display for Vec<i32>` 는 트레이트(`Display`)와 타입(`Vec<i32>`)이 모두 표준 라이브러리 소속이라 고아 규칙에 걸린다.
`impl StringExt for str` 는 타입은 남의 것이지만 트레이트 `StringExt` 를 현재 크레이트에서 정의했으므로 규칙을 만족한다.
트레이트를 새로 만들어 「내 것」 자리를 채우는 것이 확장 트레이트의 우회 방법이다.

근거 — 2-summary 「동작 방식 (1)」의 허용표.

### 2. 기본 메서드를 blanket impl 이 물려받는다

`tap_each` 와 `intersperse_with` 는 `IteratorExt` 정의 안에 본문까지 적힌 기본 메서드다.
`impl<I: Iterator> IteratorExt for I {}` 는 `Iterator` 를 구현한 모든 타입에 이 트레이트를 구현하고, 본문이 비어 있으니 기본 메서드를 그대로 쓴다.
`Sized` 가 필요한 까닭은 두 메서드가 `self` 를 값으로 받아 `TapEach { iter: self, … }` 처럼 구조체 필드에 담기 때문이다 — 크기가 정해진 타입이어야 값으로 옮길 수 있다.

근거 — 2-summary 「동작 방식 (5)」 그림과 해설.

### 3. `잘라내기: 'Hello World ...'`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
잘라내기: 'Hello World ...'
```

**왜 그런가**
- `"Hello World Rust Programming"` 은 5 + 1 + 5 + 1 + 4 + 1 + 11 = 28바이트다(모두 ASCII 라 문자 수도 28).
- 28 > 15 이므로 else 쪽으로 간다.
- `15.saturating_sub(3)` = 12 이므로 앞 12글자 `"Hello World "` 를 남긴다 — 12번째 글자는 공백이다.
- 거기에 `...` 를 붙여 `"Hello World ..."`(15글자)가 된다. `World` 와 `...` 사이에 공백이 하나 끼어 있다.

근거 — 2-summary 「동작 방식 (3)」.

### 4. 정렬은 오름차순 전체, 중복 제거는 처음 나온 순서 유지

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `sorted()` → `[1, 1, 2, 3, 3, 4, 5, 5, 6, 9]`
- `unique()` → `[3, 1, 4, 5, 9, 2, 6]`

**왜 그런가**
- `sorted` 는 `sort()` 로 제자리 정렬한 뒤 그대로 돌려주므로 중복은 남는다.
- `unique` 는 앞에서부터 `seen.insert(item.clone())` 가 `true`(처음 본 값)인 것만 통과시킨다.
- 두 번째 `1`, 두 번째 `5`, 두 번째 `3` 이 `false` 로 걸러지고, 나머지는 처음 나온 순서 그대로 남는다.
- 둘 다 `self` 를 소비하므로 원본 `numbers` 를 지키려고 `clone()` 을 먼저 부른다.

근거 — 2-summary 「동작 방식 (4)」.

### 5. 원소마다 「처리: n -> n²」 한 줄씩, 마지막에 결과

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  처리: 1 -> 1
  처리: 2 -> 4
  처리: 3 -> 9
  처리: 4 -> 16
  처리: 5 -> 25
  결과: [1, 4, 9, 16, 25]
```

**왜 그런가**
- `tap_each` · `map` 은 반복자를 감쌀 뿐이고, `collect` 가 `next()` 를 부를 때 비로소 일한다.
- `collect` 의 `next()` 한 번에 원소 하나가 첫 `tap_each`(`print!` 로 줄바꿈 없이 「처리: 1 ->」) → `map`(제곱) → 두 번째 `tap_each`(`println!` 로 「 1」과 줄바꿈)까지 끝까지 흐른다.
- 그래서 첫 탭이 다섯 번 먼저 찍히는 것이 아니라, 원소마다 두 탭의 출력이 한 줄로 이어진다.
- `TapEach::next` 는 값을 바꾸지 않으므로 결과는 제곱값만 담는다.

근거 — 2-summary 「동작 방식 (5)」 그림, 「어디서 틀리나 9」.

### 6. 100, 0, -5

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
100
0
-5
```

**왜 그런가**
- `150 > 100` 이므로 경계값 100.
- `(-5_i32)` 는 괄호 덕에 `-5` 에 대해 부르고, `-5 < 0` 이므로 0.
- 괄호가 없으면 점 호출이 단항 마이너스보다 먼저 묶여 `-(5_i32.clamp_to(0, 100))` 이 된다. 5는 범위 안이라 5, 거기에 `-` 를 붙여 -5 다.

근거 — 2-summary 「동작 방식 (6)」, 「어디서 틀리나 8」.

### 7. `use` 가 없으면 컴파일 오류, 이름이 겹치면 고유 메서드

- 트레이트가 범위에 없으면 컴파일러가 그 메서드를 찾지 못해 컴파일 오류가 난다 — `impl` 이 있어도 마찬가지다.
- 이름이 같은 고유 메서드가 있으면 고유 메서드가 먼저 불린다 — 오류 없이 내 메서드가 무시될 수 있으므로 이름을 겹치지 않게 짓는다.

근거 — 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1 · 3」, 원본 `main` 의 규칙 2 · 3.

### 8. 같다고 할 수 없다

- 개수 2인 `3` · `1` · `5` 가 먼저, 개수 1인 `4` · `9` · `2` · `6` 이 뒤에 온다는 것까지는 정해진다.
- 그러나 개수가 같은 원소끼리의 순서는 `HashMap` 순회 순서를 따르고, 그 순서는 표준 라이브러리가 약속하지 않는다.
- `sort_by_key` 는 안정 정렬이라 그 무보장 순서를 그대로 지킨다 — 그래서 동점끼리의 순서는 실행마다 달라질 수 있다.

근거 — 2-summary 「동작 방식 (4)」, 「구현 세부사항 대 언어 보장」 표.

### 9. 둘 다 아니다 — 한글은 오히려 길어지고, `max_len` 2 는 3글자가 된다

- `"가나다라마바"` 는 6글자지만 한 글자가 여러 바이트라 `len()` 이 10을 넘는다. 그래서 잘리는 쪽으로 들어간다.
- 거기서는 `chars().take(7)` 로 문자 7개를 가져오는데, 문자는 6개뿐이라 전부 남는다. 결과는 `"가나다라마바..."` 로 원래보다 길어진다 (한 글자의 바이트 수는 원본에 근거 없음 — 추론).
- `max_len` 이 2 면 `2.saturating_sub(3)` = 0 이라 `take(0)` 이 되고, 결과는 `"..."` 세 글자로 `max_len` 보다 길다.

근거 — 2-summary 「어디서 틀리나 4 · 5」.

### 10. 감싸는 구조체 + `Iterator` 구현, 그리고 자동 역참조

- `tap_each` 는 `map` 처럼 안쪽 반복자를 구조체(`TapEach`)에 담아 돌려주고, 그 구조체가 다시 `Iterator` 를 구현한다. 그래서 `.map(…)` 처럼 다른 어댑터와 사슬로 이을 수 있다. 소비될 때까지 아무것도 하지 않는 지연 동작도 같다.
- `String` 값에 메서드를 부르면 컴파일러가 자동 역참조로 `str` 까지 살펴보므로, `str` 에 구현한 확장 메서드가 찾아진다.

근거 — 2-summary 「동작 방식 (2)」 마지막 불릿, 「동작 방식 (5)」.

## 실습 정답

### 실습 1. 문자열 · Vec · Iterator · 숫자에 확장 트레이트 붙이기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `str` 에 `StringExt` 구현 | `impl StringExt for str` |
| 2. 길이 넘으면 `max_len - 3` 글자 + `...` | `truncate_with_ellipsis` — `self.len() <= max_len`, `max_len.saturating_sub(3)`, `format!("{}...", truncated)` |
| 3. 공백만이면 `true` | `is_blank` — `self.trim().is_empty()` |
| 4. 단어별 첫 글자 대문자 · 나머지 소문자 | `to_title_case` — `split_whitespace`, `first.to_uppercase()`, `rest.to_lowercase()`, `.join(" ")` |
| 5. n번 반복해 구분자로 잇기 | `repeat_with_separator` — `(0..n).map(…).collect::<Vec<_>>().join(sep)` |
| 6. 메서드별 `where` 조건 | `trait VecExt<T>` 의 세 시그니처 |
| 7. 소비해 정렬 후 반환 | `fn sorted(mut self)` — `self.sort(); self` |
| 8. 처음 나온 순서로 중복 제거 | `fn unique` — `HashSet::new()`, `filter(|item| seen.insert(item.clone()))` |
| 9. 참조 키 빈도 맵 | `fn frequencies(&self)` — `*freq.entry(item).or_insert(0) += 1` |
| 10. 모든 `Vec<T>` 에 구현 | `impl<T> VecExt<T> for Vec<T>` |
| 11. 슈퍼트레이트 + 기본 메서드 둘 | `trait IteratorExt: Iterator + Sized` 안의 `tap_each` · `intersperse_with` 본문 |
| 12. blanket impl | `impl<I: Iterator> IteratorExt for I {}` |
| 13. 콜백에 보여 주고 그대로 반환 | `impl … Iterator for TapEach<I, F>` — `(self.f)(&item); item` |
| 14. 원소 사이에 구분자 | `impl … Iterator for IntersperseWith<I>` — `needs_sep`, `next_item.take()`, `self.separator.clone()` |
| 15. `f64` · `i32` 에 각각 구현 | `impl NumExt for f64` · `impl NumExt for i32` |
| 16. 범위 밖이면 경계값 | `clamp_to` — `if self < min { min } else if self > max { max } else { self }` |
| 17. 양 끝 포함 범위 검사 | `is_between` — `*self >= min && *self <= max` |
| 18. `main` 그대로 실행 | `fn main` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-patterns/reference/extension-trait.rs`

```rust
// [패턴 & 관용구] 확장 트레이트
// 설명: 외부 타입에 메서드를 추가하는 확장 트레이트 패턴
// 팁: 고아 규칙(orphan rule) 때문에 외부 타입에 외부 트레이트를 직접 구현할 수 없다. 확장 트레이트를 만들면 우회할 수 있다. use를 빼먹으면 확장 메서드가 보이지 않으므로 주의한다. blanket impl으로 모든 구현체에 일괄 적용 가능하다.

// === 확장 트레이트: 외부 타입에 메서드 추가 ===

// ===== 1. 문자열 확장 =====
// str에 새 메서드들을 추가하기 위한 확장 트레이트
trait StringExt {
    // 최대 길이 초과 시 말줄임표 부착
    fn truncate_with_ellipsis(&self, max_len: usize) -> String;
    // 공백만 있는지 검사
    fn is_blank(&self) -> bool;
    // 단어별 첫글자 대문자로 변환
    fn to_title_case(&self) -> String;
    // 자기 자신을 n번 반복하여 구분자로 결합
    fn repeat_with_separator(&self, n: usize, sep: &str) -> String;
}

// 외부 타입(str)에 우리 트레이트 구현 (orphan rule 우회)
impl StringExt for str {
    fn truncate_with_ellipsis(&self, max_len: usize) -> String {
        // 길이 이하면 그대로
        if self.len() <= max_len {
            self.to_string()
        } else {
            // "..." 3글자를 위한 공간 확보
            let truncated: String = self.chars().take(max_len.saturating_sub(3)).collect();
            format!("{}...", truncated)
        }
    }

    fn is_blank(&self) -> bool {
        // trim 후 비어있으면 blank
        self.trim().is_empty()
    }

    fn to_title_case(&self) -> String {
        // 공백 단위로 분할
        self.split_whitespace()
            // 각 단어 처리
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => {
                        // 첫 글자 대문자
                        let upper: String = first.to_uppercase().collect();
                        // 나머지는 소문자
                        let rest: String = chars.collect();
                        format!("{}{}", upper, rest.to_lowercase())
                    }
                }
            })
            // 다시 공백으로 결합
            .collect::<Vec<_>>()
            .join(" ")
    }

    fn repeat_with_separator(&self, n: usize, sep: &str) -> String {
        // n번 반복하여 구분자로 join
        (0..n)
            .map(|_| self.to_string())
            .collect::<Vec<_>>()
            .join(sep)
    }
}

// ===== 2. Vec 확장 =====
// 제네릭 Vec<T>에 추가할 메서드들
trait VecExt<T> {
    // 정렬된 Vec 반환 (소유권 이동)
    fn sorted(self) -> Self where T: Ord;
    // 중복 제거 (해시 기반)
    fn unique(self) -> Self where T: Eq + std::hash::Hash + Clone;
    // 빈도 맵 반환 (참조)
    fn frequencies(&self) -> std::collections::HashMap<&T, usize> where T: Eq + std::hash::Hash;
}

// Vec<T>에 대한 확장 구현
impl<T> VecExt<T> for Vec<T> {
    fn sorted(mut self) -> Self where T: Ord {
        // in-place 정렬 후 반환
        self.sort();
        self
    }

    fn unique(self) -> Self where T: Eq + std::hash::Hash + Clone {
        // 본 적 있는 요소를 추적하기 위한 HashSet
        let mut seen = std::collections::HashSet::new();
        // insert가 true인 경우(처음 본 요소)만 통과
        self.into_iter()
            .filter(|item| seen.insert(item.clone()))
            .collect()
    }

    fn frequencies(&self) -> std::collections::HashMap<&T, usize> where T: Eq + std::hash::Hash {
        // 항목별 카운트
        let mut freq = std::collections::HashMap::new();
        for item in self {
            *freq.entry(item).or_insert(0) += 1;
        }
        freq
    }
}

// ===== 3. Iterator 확장 =====
// 모든 Iterator에 추가 어댑터를 주는 확장 트레이트
trait IteratorExt: Iterator + Sized {
    // 각 요소를 통과시키며 부수효과 함수 호출 (디버깅용 tap)
    fn tap_each<F>(self, f: F) -> TapEach<Self, F>
    where
        F: FnMut(&Self::Item),
    {
        TapEach { iter: self, f }
    }

    // 요소 사이에 구분 요소를 삽입
    fn intersperse_with(self, separator: Self::Item) -> IntersperseWith<Self>
    where
        Self::Item: Clone,
    {
        IntersperseWith {
            iter: self,
            separator,
            needs_sep: false,
            next_item: None,
        }
    }
}

// blanket impl: 모든 Iterator에 일괄 적용
impl<I: Iterator> IteratorExt for I {}

// TapEach 어댑터: 내부 이터레이터와 콜백을 보유
struct TapEach<I, F> {
    iter: I,
    f: F,
}

// TapEach가 다시 Iterator로 동작하도록 구현
impl<I: Iterator, F: FnMut(&I::Item)> Iterator for TapEach<I, F> {
    type Item = I::Item;

    fn next(&mut self) -> Option<Self::Item> {
        // 다음 요소를 받아 콜백을 호출하고 그대로 반환
        self.iter.next().map(|item| {
            (self.f)(&item);
            item
        })
    }
}

// IntersperseWith 어댑터: 구분자 삽입을 위한 상태 보유
struct IntersperseWith<I: Iterator> where I::Item: Clone {
    iter: I,
    separator: I::Item,
    // 다음 호출에 구분자를 내보내야 하는지 여부
    needs_sep: bool,
    // 미리 가져온 다음 아이템
    next_item: Option<I::Item>,
}

impl<I: Iterator> Iterator for IntersperseWith<I> where I::Item: Clone {
    type Item = I::Item;

    fn next(&mut self) -> Option<Self::Item> {
        if self.needs_sep {
            self.needs_sep = false;
            // 보관된 아이템이 있으면 구분자를 반환하고 아이템을 다시 보관
            self.next_item.take().map(|item| {
                self.needs_sep = false;
                // 세퍼레이터 반환 전에 다음 아이템을 다시 준비
                let sep = self.separator.clone();
                self.next_item = Some(item);
                self.needs_sep = false;
                sep
            }).or_else(|| self.iter.next())
        } else {
            match self.next_item.take() {
                Some(item) => {
                    // 다음에 구분자 차례
                    self.needs_sep = true;
                    self.next_item = self.iter.next();
                    Some(item)
                }
                None => {
                    // 처음 호출 시 첫 아이템 가져옴
                    self.iter.next().map(|item| {
                        self.needs_sep = true;
                        self.next_item = self.iter.next();
                        item
                    })
                }
            }
        }
    }
}

// ===== 4. 숫자 확장 =====
// 숫자 타입에 clamp/is_between 추가
trait NumExt {
    fn clamp_to(self, min: Self, max: Self) -> Self where Self: Sized;
    fn is_between(&self, min: Self, max: Self) -> bool where Self: Sized;
}

// f64에 대한 구현
impl NumExt for f64 {
    fn clamp_to(self, min: f64, max: f64) -> f64 {
        // 범위 밖이면 경계값으로 보정
        if self < min { min } else if self > max { max } else { self }
    }

    fn is_between(&self, min: f64, max: f64) -> bool {
        *self >= min && *self <= max
    }
}

// i32에 대한 구현
impl NumExt for i32 {
    fn clamp_to(self, min: i32, max: i32) -> i32 {
        if self < min { min } else if self > max { max } else { self }
    }

    fn is_between(&self, min: i32, max: i32) -> bool {
        *self >= min && *self <= max
    }
}

fn main() {
    println!("=== 1. 문자열 확장 ===");
    // str에 새 메서드들이 마치 원래 있던 것처럼 사용됨
    let text = "Hello World Rust Programming";
    println!("원본: '{}'", text);
    println!("잘라내기: '{}'", text.truncate_with_ellipsis(15));
    println!("타이틀: '{}'", "hello WORLD rust".to_title_case());
    println!("빈 문자열: {}", "   ".is_blank());
    println!("반복: '{}'", "ha".repeat_with_separator(3, ", "));

    println!("\n=== 2. Vec 확장 ===");
    // Vec에도 사용자 정의 메서드 적용
    let numbers = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3];
    println!("원본: {:?}", numbers);
    println!("정렬: {:?}", numbers.clone().sorted());
    println!("중복제거: {:?}", numbers.clone().unique());

    // 빈도 계산 후 내림차순 정렬
    let freq = numbers.frequencies();
    let mut freq_vec: Vec<_> = freq.iter().collect();
    freq_vec.sort_by_key(|(_, &count)| std::cmp::Reverse(count));
    println!("빈도: {:?}", freq_vec);

    println!("\n=== 3. Iterator 확장: tap_each ===");
    // tap_each로 파이프라인 중간 상태를 관찰
    let result: Vec<i32> = vec![1, 2, 3, 4, 5].into_iter()
        .tap_each(|x| print!("  처리: {} ->", x))
        .map(|x| x * x)
        .tap_each(|x| println!(" {}", x))
        .collect();
    println!("  결과: {:?}", result);

    println!("\n=== 4. 숫자 확장 ===");
    // i32, f64에 모두 적용
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

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 모든 확장의 뼈대는 「내 트레이트 정의 → `impl 내트레이트 for 외부타입`」 두 단계다 — 트레이트가 내 것이라 고아 규칙을 통과한다.
- `VecExt<T>` 는 조건을 메서드마다 `where` 로 걸어, 구현은 모든 `Vec<T>` 에 넓게 두고 호출만 좁힌다.
- `IteratorExt` 는 기본 메서드에 본문을 두었기 때문에 blanket impl 의 본문을 비울 수 있다.
- 어댑터는 「구조체에 안쪽 반복자 담기 → 그 구조체에 `Iterator` 구현」이며, `next` 가 불릴 때만 일한다.
- 정답 코드의 `truncate_with_ellipsis` 는 바이트 길이와 문자 수를 섞어 여러 바이트 문자 · 작은 `max_len` 에서 결과 길이 약속을 어긴다 — 따라 쓰되 이 경계는 알고 쓴다.
- `main` 이 쓰는 메서드 이름(`clamp_to` · `is_between` 등)은 표준 메서드와 겹치지 않게 지어져 있다 — 겹치면 고유 메서드가 먼저 불린다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
