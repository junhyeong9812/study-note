# rust/rust-collections/10 — Iterator 심화 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `inspect` 두 개를 끼운 파이프라인 (예측)

```rust
// 질문용 발췌
let result: Vec<i32> = (1..=10)
    .inspect(|x| print!("[원본:{}] ", x))
    .filter(|x| x % 3 == 0)
    .inspect(|x| print!("[필터후:{}] ", x))
    .map(|x| x * x)
    .collect();
println!();
println!("결과: {:?}", result);
```

- 첫 줄의 꼬리표들은 어떤 차례로 찍히나?
- 둘째 줄의 `result` 는 무엇인가?

### 2. 튜플 상태를 든 `scan` (예측)

```rust
// 질문용 발췌
let data = vec![10.0, 20.0, 30.0, 25.0, 15.0, 35.0];
let moving_avg: Vec<f64> = data.iter()
    .scan((0.0, 0usize), |(sum, count), &x| {
        *sum += x;
        *count += 1;
        Some(*sum / *count as f64)
    })
    .collect();
```

- `moving_avg` 에는 어떤 값들이 들어가나?
- 이 값들은 「최근 몇 개」의 평균인가, 「처음부터 지금까지」의 평균인가?

### 3. `StepRange` 두 개의 값과 힌트 (예측)

- `StepRange::new(0, 20, 3).collect()` 는 어떤 벡터를 만드나?
- 막 만든 `StepRange::new(10, 0, -2)` 에 `size_hint()` 를 부르면 무엇을 돌려주나?

### 4. `take` 앞에 `by_ref()` 를 끼우는 까닭 (왜)

- `iter.by_ref().take(3)` 을 `iter.take(3)` 으로 바꾸면 다음 줄 `iter.collect()` 에서 무엇이 문제가 되나?
- `by_ref()` 는 무엇을 넘기길래 그 문제를 피하나?

### 5. `checked_add(...)?` 가 `Fibonacci` 의 종료 장치인 까닭 (왜)

- `Fibonacci::next` 에서 덧셈이 넘치면 `?` 때문에 무슨 일이 일어나나?
- 100만을 넘는 값이 영영 없었다면 `Fibonacci::new().find(...)` 는 끝없이 돌았을까?

### 6. 다 떨어진 `Windowed` 를 계속 부르면 (경계)

- 창 네 개를 낸 `Windowed::new(vec![1, 2, 3, 4, 5, 6].into_iter(), 3)` 에 `next()` 를 계속 부르면 `buffer` 는 어떻게 변하나?
- 그러다 어느 호출에서, 어느 줄이 프로그램을 멈추게 하나?

### 7. 처음부터 빈 `StepRange` 의 `size_hint` (경계)

- `StepRange::new(5, 0, 1)` 의 `size_hint` 계산에서 `end - current` 를 `usize` 로 바꾸면 힌트가 어떻게 되나?

### 8. `scan` 클로저가 `None` 을 돌려주면 (경계)

- 누적합 `scan` 을 「합이 5 를 넘으면 `None`」으로 바꿔 `[1, 2, 3, 4, 5]` 에 걸면 무엇이 모이나?

### 9. `fuse` 가 실제로 쓸모 있는 곳 (연결)

- 원본의 `vec![1, 2, 3].into_iter().fuse()` 예제가 `fuse` 의 효과를 보여 주지 못하는 까닭은 무엇인가?
- 6번의 `Windowed` 를 `.fuse()` 로 감싸면 그 위험은 어떻게 되나?

### 10. `iter()` 와 `into_iter()` 가 내는 것의 차이 (연결)

- `first3` 는 `Vec<&i32>` 인데 `windows` 의 안쪽은 `Vec<i32>` 인 까닭은 무엇인가?
- `for x in v` 는 어떤 트레이트의 어떤 메서드로 이터레이터를 얻나?

## 실습

### 실습 1. 커스텀 이터레이터 셋과 이터레이터 도구 모음 만들기

**만들 것** — 피보나치 · 간격 있는 범위 · 슬라이딩 윈도우 이터레이터를 직접 구현하고, `main` 에서 `scan` · `inspect` · `by_ref` · `fuse` · `std::iter` 생성 함수와 함께 써서 결과를 찍는 프로그램이다.

**요구 조건**

1단계 — 커스텀 이터레이터 셋

1. `Fibonacci` 는 `a`, `b` 두 값을 상태로 들고, `next()` 마다 `a` 를 내고 한 칸 밀어 0, 1, 1, 2, 3, … 을 낸다(요소 타입 `u64`).
2. `Fibonacci` 는 다음 값을 `checked_add` 로 구하고, 넘치면 `?` 로 `None` 을 돌려 끝난다.
3. `StepRange::new(start, end, step)` 는 step 이 양수면 `end` 미만, 음수면 `end` 초과인 동안 `step` 씩 움직이며 값을 내고, 그 밖에는 `None` 을 낸다.
4. `StepRange` 는 `size_hint` 를 구현해 남은 개수 n 을 `(n, Some(n))` 으로 돌려주고, step 이 0 이면 0 을 쓴다.
5. `Windowed` 는 안쪽 이터레이터를 품고, 첫 호출에는 `size` 개를 채운 창을, 이후에는 앞 하나를 빼고 뒤 하나를 더한 창을 `Vec` 복사본으로 낸다.
6. `Windowed` 는 안쪽 이터레이터가 모자라면 `?` 로 `None` 을 돌린다.

2단계 — 표준 어댑터

7. `scan` 으로 `[1, 2, 3, 4, 5]` 의 누적합 `[1, 3, 6, 10, 15]` 를 모아 찍는다.
8. `scan` 의 상태를 `(합, 개수)` 튜플로 두고 `[10.0, 20.0, 30.0, 25.0, 15.0, 35.0]` 의 처음부터 지금까지의 평균을 모아 찍는다.
9. `1..=10` 에 `inspect`(원본 꼬리표) → `filter`(3의 배수) → `inspect`(필터후 꼬리표) → `map`(제곱)을 이어 꼬리표를 한 줄에 찍고, 줄을 바꾼 뒤 결과를 찍는다.
10. 1~10 벡터의 `iter()` 에서 `by_ref().take(3)` 으로 앞 셋을 모으고, 같은 이터레이터로 나머지를 모아 둘 다 찍는다.
11. `vec![1, 2, 3]` 을 `into_iter().fuse()` 로 감싸 `next()` 다섯 번의 결과를 한 줄에 찍는다.

3단계 — 커스텀 이터레이터 쓰기

12. `Fibonacci` 의 처음 15개를 `take` 로 모아 찍고, 100만을 넘는 첫 값을 `find` 로 찾아 찍는다.
13. `StepRange::new(0, 20, 3)` 과 `StepRange::new(10, 0, -2)` 를 각각 모아 찍는다.
14. `Windowed::new(vec![1, 2, 3, 4, 5, 6].into_iter(), 3)` 의 창들을 모아 찍는다.

4단계 — `std::iter` 생성 함수

15. `from_fn` 으로 바깥 변수 `count` 를 하나씩 늘려 1~5 를 내고 모아 찍는다.
16. `successors` 로 `1u64` 에서 시작해 `checked_mul(2)` 로 다음 값을 만들고, 처음 10개를 모아 찍는다.
17. `repeat(5)` 의 처음 4개를 모아 찍는다.
18. `once("=== 헤더 ===")` 뒤에 `chain` 으로 `"데이터1"`, `"데이터2"` 를 이어 모아 찍는다.

**시작 코드**

```rust
// 실습 시작 코드 — TODO 자리를 채운다

struct Fibonacci {
    a: u64,
    b: u64,
}

impl Fibonacci {
    fn new() -> Self {
        Fibonacci { a: 0, b: 1 }
    }
}

impl Iterator for Fibonacci {
    // TODO: 요소 타입을 정한다
    fn next(&mut self) -> Option<Self::Item> {
        // TODO: a 를 낼 값으로 잡고, checked_add + ? 로 다음 값을 구해 한 칸 민다
        todo!()
    }
}

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
        // TODO: step 부호에 따라 계속할지 정하고, 값을 낸 뒤 current 를 step 만큼 옮긴다
        todo!()
    }

    // TODO: size_hint 를 구현해 남은 개수 n 을 (n, Some(n)) 으로 돌려준다
}

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
        // TODO: 첫 호출이면 size 개를 채우고, 아니면 앞 하나를 빼고 뒤 하나를 더한다 (모자라면 ?)
        // TODO: 버퍼의 복사본을 Some 으로 낸다
        todo!()
    }
}

fn main() {
    println!("=== scan (누적합) ===");
    // TODO: 누적합 cumsum 을 scan 으로 모은다
    // println!("cumulative sum: {:?}", cumsum);

    let data = vec![10.0, 20.0, 30.0, 25.0, 15.0, 35.0];
    // TODO: (합, 개수) 상태의 scan 으로 moving_avg 를 모은다
    // println!("moving average: {:?}", moving_avg);

    println!("\n=== inspect ===");
    // TODO: inspect → filter → inspect → map 파이프라인으로 result 를 모은다
    println!();
    // println!("결과: {:?}", result);

    println!("\n=== by_ref ===");
    let nums = vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
    let mut iter = nums.iter();
    // TODO: 앞 3개를 first3 로, 나머지를 rest 로 모은다
    // println!("first 3: {:?}", first3);
    // println!("rest: {:?}", rest);

    println!("\n=== fuse ===");
    let data = vec![1, 2, 3];
    // TODO: fused 를 만들고 next() 다섯 번을 한 줄에 찍는다
    // println!("fuse: {:?}, {:?}, {:?}, {:?}, {:?}", …);

    println!("\n=== 커스텀: Fibonacci ===");
    // TODO: fibs (처음 15개) 와 big_fib (100만 초과 첫 값)
    // println!("피보나치 15개: {:?}", fibs);
    // println!("100만 초과 첫 피보나치: {:?}", big_fib);

    println!("\n=== 커스텀: StepRange ===");
    // TODO: by2 와 countdown
    // println!("0..20 step 3: {:?}", by2);
    // println!("10..0 step -2: {:?}", countdown);

    println!("\n=== 커스텀: Windowed ===");
    let data = vec![1, 2, 3, 4, 5, 6];
    // TODO: 크기 3 의 창들을 windows 로 모은다
    // println!("windows(3): {:?}", windows);

    println!("\n=== std::iter 함수들 ===");
    let mut count = 0;
    // TODO: from_fn 으로 counter 를 모은다
    // println!("from_fn: {:?}", counter);
    // TODO: successors 로 powers 를 모은다
    // println!("successors (2의 거듭제곱): {:?}", powers);
    // TODO: repeat 으로 fives 를 모은다
    // println!("repeat: {:?}", fives);
    // TODO: once + chain 으로 with_header 를 모은다
    // println!("once + chain: {:?}", with_header);
}
```

**확인 방법** — `rustc iterator-advanced.rs && ./iterator-advanced` 로 컴파일해 돌리고, 각 줄이 요구 조건에 적은 값(누적합 `[1, 3, 6, 10, 15]`, `fuse` 의 `Some(1), Some(2), Some(3), None, None` 등)과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
