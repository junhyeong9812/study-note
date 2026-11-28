# rust/rust-collections/10 — Iterator 심화 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 꼬리표는 요소마다 섞여 찍히고, 결과는 3·6·9 의 제곱이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[원본:1] [원본:2] [원본:3] [필터후:3] [원본:4] [원본:5] [원본:6] [필터후:6] [원본:7] [원본:8] [원본:9] [필터후:9] [원본:10] 
결과: [9, 36, 81]
```

**왜 그런가**

- 어댑터는 지연 평가라서 `collect` 가 요소 하나를 당기면 그 요소가 파이프라인 끝까지 흐른 뒤에 다음 요소가 출발한다.
- 그래서 `[원본:…]` 꼬리표를 다 찍고 나서 `[필터후:…]` 를 찍는 것이 아니라, 3 · 6 · 9 가 `filter` 를 통과할 때마다 그 바로 뒤에 `[필터후:…]` 가 끼어든다.
- 통과한 3 · 6 · 9 가 `map` 에서 제곱되어 `[9, 36, 81]` 이 된다.
- `print!` 는 줄을 바꾸지 않으므로 꼬리표가 한 줄에 이어지고, `println!()` 이 줄을 닫는다.
- 근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (1)」.

### 2. 누적 평균 — 처음부터 지금까지의 평균이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`moving_avg` 는 `[10.0, 15.0, 20.0, 21.25, 20.0, 22.5]` 가 된다.

**왜 그런가**

- 상태 `(sum, count)` 는 처음 `(0.0, 0)` 에서 시작해 줄어드는 일 없이 쌓이기만 한다.
- 계산은 `10/1 = 10`, `30/2 = 15`, `60/3 = 20`, `85/4 = 21.25`, `100/5 = 20`, `135/6 = 22.5` 다.
- 그래서 이름은 「이동 평균」이지만 실제로는 처음부터 지금까지의 평균(누적 평균)이다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」.

### 3. 일곱 개의 3 간격 값, 그리고 `(5, Some(5))`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `StepRange::new(0, 20, 3).collect()` 는 `[0, 3, 6, 9, 12, 15, 18]` 이다.
- 막 만든 `StepRange::new(10, 0, -2)` 의 `size_hint()` 는 `(5, Some(5))` 다.

**왜 그런가**

- 양수 step 은 `current < end` 인 동안 진행하므로 0 부터 3 씩 18 까지 내고, 21 에서 조건이 깨져 `None` 이다.
- 음수 step 의 힌트는 `(current - end + |step| - 1) / |step| = (10 + 2 - 1) / 2 = 11 / 2 = 5` 다.
- 실제로도 10, 8, 6, 4, 2 의 다섯 개를 내고 0 에서 멈춘다(`current > end` 가 거짓).
- 근거: 2-summary 「동작 방식 (3)」.

### 4. `take` 는 이터레이터를 가져가 버리고, `by_ref` 는 빌림만 넘긴다

- `take` 는 이터레이터를 값으로 받는다.
- `iter.take(3)` 이라 쓰면 `iter` 의 소유권이 `take` 로 옮겨가서, 다음 줄의 `iter.collect()` 는 「옮겨진 값을 썼다」는 컴파일 오류가 된다.
- `by_ref()` 는 `&mut iter` 를 돌려준다.
- `&mut` 이터레이터도 이터레이터라서 `take` 는 빌림만 가져가고, 빌림이 끝나면 `iter` 를 다시 쓸 수 있다.
- 이때 `iter` 는 앞 세 개를 이미 내준 상태라 나머지 `[4, …, 10]` 을 이어서 낸다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 6」.

### 5. 넘치는 순간 `next` 가 `None` 을 돌려주므로 `find` 도 결국 멈춘다

- `checked_add` 는 넘치면 `None` 을 돌려주고, 뒤의 `?` 는 그 자리에서 `next` 전체가 `None` 을 돌려주게 한다.
- 그래서 `Fibonacci` 는 무한 수열처럼 보여도 `u64` 가 넘치는 지점에서 끝난다.
- 상태를 바꾸기 전에 빠져나가므로 이후의 호출도 계속 `None` 이다.
- 100만을 넘는 값이 없었다면 `find` 는 끝없이 돌지 않고, 수열이 끝나는 곳에서 `None` 을 돌려줬을 것이다.
- 실제로는 100만을 넘는 값이 있으므로 `find` 는 그 첫 값에서 곧바로 멈춘다.
- 근거: 2-summary 「동작 방식 (2)」.

### 6. 버퍼가 하나씩 줄다가, 빈 버퍼에서 `remove(0)` 이 패닉한다

- 창 네 개 뒤의 호출은 모두 `else` 가지로 간다.
- 그래서 `buffer.remove(0)` 을 먼저 하고, 안쪽 `next()` 가 `None` 이라 `?` 로 빠져나간다.
- 첫 `None` 에서 버퍼는 `[5, 6]`, 다음 호출에서 `[6]`, 그다음에 `[]` 가 된다.
- 창 네 개 뒤 네 번째 호출(첫 `None` 뒤 세 번째 호출)에서 빈 `Vec` 에 `buffer.remove(0)` 을 하게 된다.
- `Vec::remove` 는 범위 밖 위치에서 패닉하므로 그 줄이 프로그램을 멈춘다.
- `collect` 는 첫 `None` 에서 멈추므로 원본 예제에서는 이 문제가 드러나지 않는다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 7. 음수가 아주 큰 `usize` 로 바뀌어 힌트가 실제(0)와 크게 어긋난다

- `end - current = 0 - 5 = -5` 이고, 음수 `i32` 를 `as usize` 로 바꾸면 `usize` 의 최댓값에 가까운 큰 수가 된다.
- 그러면 `size_hint` 는 「거의 무한히 남았다」는 힌트를 돌려준다.
- 그러나 `next` 는 `5 < 0` 이 거짓이라 첫 호출부터 `None` 이다.
- step 이 크면 뒤따르는 덧셈이 넘쳐 디버그 빌드에서 패닉할 수도 있다 (확인 필요).
- 같은 문제는 `0..20 step 3` 이 `current = 21` 까지 간 뒤에도 생긴다.
- 근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」.

### 8. `[1, 3]` 만 모인다 — `None` 이 곧 끝이다

- 상태가 1 이 되어 `Some(1)`, 3 이 되어 `Some(3)` 을 낸다.
- 6 이 되는 순간 5 를 넘으므로 `None` 을 돌려준다.
- `scan` 은 클로저가 `None` 을 돌려주면 그 자리에서 이터레이션을 끝내므로, 뒤의 4 · 5 는 보지도 않는다.
- 결과는 `[1, 3]` 이다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (5)」.

### 9. `Vec` 의 `into_iter()` 는 원래 끝난 뒤 `None` 만 내고, `Windowed` 는 그렇지 않다

- `Vec` 의 `into_iter()` 는 끝난 뒤에도 계속 `None` 을 내므로, `fuse` 를 빼도 다섯 번째까지 같은 결과일 것이다 (확인 필요).
- 그래서 원본 예제로는 `fuse` 가 무엇을 바꾸는지 보이지 않는다.
- `Windowed` 를 `.fuse()` 로 감싸면 첫 `None` 뒤로는 안쪽 `next()` 를 부르지 않는다.
- 그러므로 `buffer.remove(0)` 까지 가지 않고, 6번의 패닉 위험이 사라진다.
- 근거: 2-summary 「동작 방식 (8)」 · 「어디서 틀리나 2」 · 「어디서 틀리나 5」.

### 10. `iter()` 는 참조를, `into_iter()` 는 값 자체를 낸다

- `nums.iter()` 는 벡터를 빌린 채 요소의 참조 `&i32` 를 내므로 `first3` 는 `Vec<&i32>` 다.
- `data.into_iter()` 는 벡터를 써 버리면서 요소 `i32` 자체를 내므로 `Windowed` 의 창은 `Vec<i32>` 다.
- `for x in v` 는 `IntoIterator` 트레이트의 `into_iter()` 를 불러 이터레이터를 얻는다.
- 근거: 2-summary 「동작 방식 (1)」.

## 실습 정답

### 실습 1. 커스텀 이터레이터 셋과 이터레이터 도구 모음 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `Fibonacci` 가 `a` 를 내고 한 칸 민다 | `impl Iterator for Fibonacci` 의 `type Item = u64` · `let result = self.a` · `self.a = self.b; self.b = next;` |
| 2. 넘치면 `None` 으로 끝난다 | `self.a.checked_add(self.b)?` |
| 3. `StepRange` 의 진행 조건 | `StepRange::next` 의 `(self.step > 0 && self.current < self.end) \|\| (self.step < 0 && self.current > self.end)` · `self.current += self.step` |
| 4. `size_hint` 가 `(n, Some(n))` | `StepRange::size_hint` 의 `remaining` 계산과 `(remaining, Some(remaining))` |
| 5. 첫 창 채우기 · 이후 한 칸 밀기 · 복사본 내기 | `Windowed::next` 의 `if self.first { for _ in 0..self.size … }` · `self.buffer.remove(0)` · `Some(self.buffer.clone())` |
| 6. 모자라면 `None` | `self.buffer.push(self.iter.next()?)` |
| 7. 누적합 | `cumsum` 의 `.scan(0, \|state, &x\| { *state += x; Some(*state) })` |
| 8. 누적 평균 | `moving_avg` 의 `.scan((0.0, 0usize), \|(sum, count), &x\| …)` |
| 9. `inspect` 파이프라인 | `result` 의 `.inspect(…).filter(…).inspect(…).map(…)` 와 `println!()` |
| 10. 앞 셋과 나머지 | `iter.by_ref().take(3).collect()` · `iter.collect()` |
| 11. `fuse` 다섯 번 | `data.into_iter().fuse()` 와 `fused.next()` 다섯 개 |
| 12. 피보나치 15개와 100만 초과 첫 값 | `Fibonacci::new().take(15)` · `Fibonacci::new().find(\|&x\| x > 1_000_000)` |
| 13. `StepRange` 두 개 | `by2` · `countdown` |
| 14. 크기 3 의 창 | `Windowed::new(data.into_iter(), 3).collect()` |
| 15. `from_fn` 1~5 | `std::iter::from_fn(\|\| { count += 1; … })` |
| 16. 2 의 거듭제곱 10개 | `std::iter::successors(Some(1u64), \|&prev\| prev.checked_mul(2)).take(10)` |
| 17. `repeat` 4개 | `std::iter::repeat(5).take(4)` |
| 18. 머리글 + 데이터 | `std::iter::once("=== 헤더 ===").chain(["데이터1", "데이터2"].iter().cloned())` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-collections/reference/iterator-advanced.rs`

```rust
// [컬렉션 심화] Iterator 심화
// 설명: scan, inspect, by_ref, fuse, 커스텀 이터레이터 구현 (Iterator trait)
// 팁: 커스텀 이터레이터는 Iterator 트레이트의 next() 메서드만 구현하면 된다. size_hint를 구현하면 collect 시 사전 할당이 가능하다. scan은 상태 있는 map이고, inspect는 디버깅에 유용하다. by_ref는 이터레이터를 빌려서 일부만 소비할 때 쓴다.

// === 커스텀 이터레이터 구현 ===

// 1. 피보나치 이터레이터
// 두 이전 값을 상태로 보관
struct Fibonacci {
    a: u64,
    b: u64,
}

impl Fibonacci {
    fn new() -> Self {
        Fibonacci { a: 0, b: 1 }
    }
}

// Iterator: next()가 핵심. Item 연관 타입으로 요소 타입 지정
impl Iterator for Fibonacci {
    type Item = u64;

    fn next(&mut self) -> Option<Self::Item> {
        let result = self.a;
        // checked_add: 오버플로우 시 None 반환 -> 자연스러운 종료
        let next = self.a.checked_add(self.b)?; // 오버플로우시 None
        self.a = self.b;
        self.b = next;
        Some(result)
    }
}

// 2. Range 이터레이터 (step 포함)
// 양수/음수 step 모두 지원
struct StepRange {
    current: i32,
    end: i32,
    step: i32,
}

impl StepRange {
    fn new(start: i32, end: i32, step: i32) -> Self {
        StepRange { current: start, end, step }
    }
}

impl Iterator for StepRange {
    type Item = i32;

    fn next(&mut self) -> Option<Self::Item> {
        // 양수 step: end 미만일 때 / 음수 step: end 초과일 때 진행
        if (self.step > 0 && self.current < self.end)
            || (self.step < 0 && self.current > self.end) {
            let val = self.current;
            self.current += self.step;
            Some(val)
        } else {
            None
        }
    }

    // size_hint 구현으로 collect 최적화 - Vec 사전 할당 가능
    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = if self.step > 0 {
            ((self.end - self.current) as usize + self.step as usize - 1) / self.step as usize
        } else if self.step < 0 {
            ((self.current - self.end) as usize + (-self.step) as usize - 1) / (-self.step) as usize
        } else {
            0
        };
        // 정확한 크기 알고 있을 땐 (n, Some(n))
        (remaining, Some(remaining))
    }
}

// 3. 윈도우 이터레이터
// 내부 이터레이터 I로부터 size 크기 슬라이딩 윈도우 생성
struct Windowed<I: Iterator> {
    iter: I,
    buffer: Vec<I::Item>,
    size: usize,
    first: bool,
}

impl<I: Iterator> Windowed<I>
where I::Item: Clone {
    fn new(iter: I, size: usize) -> Self {
        Windowed {
            iter,
            buffer: Vec::with_capacity(size),
            size,
            first: true,
        }
    }
}

impl<I: Iterator> Iterator for Windowed<I>
where I::Item: Clone {
    type Item = Vec<I::Item>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.first {
            // 첫 윈도우: size만큼 채우기
            for _ in 0..self.size {
                // ?로 부족하면 None 전파 (이터레이터 끝)
                self.buffer.push(self.iter.next()?);
            }
            self.first = false;
        } else {
            // 이후: 앞 하나 제거, 뒤 하나 추가 (슬라이딩)
            self.buffer.remove(0);
            self.buffer.push(self.iter.next()?);
        }
        Some(self.buffer.clone())
    }
}

fn main() {
    // === 1. scan: 상태 있는 map ===
    println!("=== scan (누적합) ===");
    // scan: 누적 상태(state)를 들고 다니면서 변환
    // map과 달리 외부 상태에 의존 가능
    let cumsum: Vec<i32> = [1, 2, 3, 4, 5].iter()
        .scan(0, |state, &x| {
            *state += x;
            Some(*state)
        })
        .collect();
    println!("cumulative sum: {:?}", cumsum); // [1, 3, 6, 10, 15]

    // scan으로 이동 평균 - 상태로 (sum, count) 튜플 사용
    let data = vec![10.0, 20.0, 30.0, 25.0, 15.0, 35.0];
    let moving_avg: Vec<f64> = data.iter()
        .scan((0.0, 0usize), |(sum, count), &x| {
            *sum += x;
            *count += 1;
            Some(*sum / *count as f64)
        })
        .collect();
    println!("moving average: {:?}", moving_avg);

    // === 2. inspect: 디버깅용 peek ===
    println!("\n=== inspect ===");
    // inspect: 통과하는 요소를 들여다봄 (값 변경 없이 부수효과)
    let result: Vec<i32> = (1..=10)
        .inspect(|x| print!("[원본:{}] ", x))
        .filter(|x| x % 3 == 0)
        .inspect(|x| print!("[필터후:{}] ", x))
        .map(|x| x * x)
        .collect();
    println!();
    println!("결과: {:?}", result);

    // === 3. by_ref: 이터레이터 일부만 소비 ===
    println!("\n=== by_ref ===");
    let nums = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    let mut iter = nums.iter();

    // by_ref: 이터레이터 자체를 빌림 -> take 후에도 원본 사용 가능
    let first3: Vec<&i32> = iter.by_ref().take(3).collect();
    println!("first 3: {:?}", first3);

    // 나머지 계속 사용 - by_ref 덕분에 iter는 살아있음
    let rest: Vec<&i32> = iter.collect();
    println!("rest: {:?}", rest);

    // === 4. fuse: None 이후 항상 None 보장 ===
    println!("\n=== fuse ===");
    // 일부 이터레이터는 None 반환 후 다시 Some을 줄 수 있음
    // fuse()는 첫 None 이후 항상 None 보장 - 안전성 강화
    let data = vec![1, 2, 3];
    let mut fused = data.into_iter().fuse();
    println!("fuse: {:?}, {:?}, {:?}, {:?}, {:?}",
        fused.next(), fused.next(), fused.next(),
        fused.next(), fused.next()); // Some(1), Some(2), Some(3), None, None

    // === 5. 커스텀 이터레이터: Fibonacci ===
    println!("\n=== 커스텀: Fibonacci ===");
    // take(15): 무한 이터레이터지만 처음 15개만 사용
    let fibs: Vec<u64> = Fibonacci::new().take(15).collect();
    println!("피보나치 15개: {:?}", fibs);

    // find: 조건 만족 첫 값 - 발견 즉시 종료 (lazy)
    let big_fib = Fibonacci::new()
        .find(|&x| x > 1_000_000);
    println!("100만 초과 첫 피보나치: {:?}", big_fib);

    // === 6. 커스텀: StepRange ===
    println!("\n=== 커스텀: StepRange ===");
    let by2: Vec<i32> = StepRange::new(0, 20, 3).collect();
    println!("0..20 step 3: {:?}", by2);

    let countdown: Vec<i32> = StepRange::new(10, 0, -2).collect();
    println!("10..0 step -2: {:?}", countdown);

    // === 7. 커스텀: Windowed ===
    println!("\n=== 커스텀: Windowed ===");
    let data = vec![1, 2, 3, 4, 5, 6];
    // 슬라이딩 윈도우 크기 3
    let windows: Vec<Vec<i32>> = Windowed::new(data.into_iter(), 3).collect();
    println!("windows(3): {:?}", windows);

    // === 8. successors / from_fn ===
    println!("\n=== std::iter 함수들 ===");
    // from_fn: 클로저로 이터레이터 생성 (FnMut() -> Option<T>)
    let mut count = 0;
    let counter: Vec<i32> = std::iter::from_fn(|| {
        count += 1;
        if count <= 5 { Some(count) } else { None }
    }).collect();
    println!("from_fn: {:?}", counter);

    // successors: 이전 값으로 다음 값 생성 (lazy 무한열)
    let powers: Vec<u64> = std::iter::successors(Some(1u64), |&prev| {
        prev.checked_mul(2)
    }).take(10).collect();
    println!("successors (2의 거듭제곱): {:?}", powers);

    // repeat, repeat_with - 같은 값 무한 반복
    let fives: Vec<i32> = std::iter::repeat(5).take(4).collect();
    println!("repeat: {:?}", fives);

    // once: 단일 요소 이터레이터, empty: 빈 이터레이터
    let with_header: Vec<&str> = std::iter::once("=== 헤더 ===")
        .chain(["데이터1", "데이터2"].iter().cloned())
        .collect();
    println!("once + chain: {:?}", with_header);
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 세 커스텀 이터레이터는 모두 `type Item` 과 `next` 만으로 `take` · `find` · `collect` 를 쓸 수 있게 된다.
- `Fibonacci` 와 `Windowed` 는 `Option` 에 붙인 `?` 로 「더 낼 것이 없음」을 그대로 `None` 으로 바꾼다.
- `StepRange::size_hint` 는 올림 나눗셈으로 남은 개수를 계산하지만, 차이가 음수인 경우는 다루지 않는다.
- `scan` 은 `&mut` 상태로 누적을 들고 다니고, `inspect` 는 흐름을 바꾸지 않고 요소마다 꼬리표를 찍는다.
- `by_ref` 는 `take` 가 원본을 가져가지 못하게 빌림만 넘겨, 같은 `iter` 로 나머지를 모을 수 있게 한다.
- `from_fn` · `successors` · `repeat` · `once` 는 구조체 없이 이터레이터를 만들고, 끝없는 것은 `take` 와 짝지어 멈춘다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
