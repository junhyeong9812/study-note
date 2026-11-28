# rust/rust-collections/07 — BinaryHeap (이진 힙) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 여섯 값을 넣고 `pop` 을 되풀이하면 (예측)

```rust
// 질문용 발췌
let mut heap = BinaryHeap::new();
for v in [3, 1, 4, 1, 5, 9] { heap.push(v); }
println!("{:?}", heap.peek());
while let Some(val) = heap.pop() { print!("{} ", val); }
```

- `peek` 줄은 무엇을 찍나?
- `while let` 이 찍는 수의 순서는?

### 2. `Reverse` 로 감싼 힙의 `peek` 과 `pop` (예측)

```rust
// 질문용 발췌
let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
for v in [3, 1, 4, 1, 5] { min_heap.push(Reverse(v)); }
println!("{:?}", min_heap.peek());
while let Some(Reverse(val)) = min_heap.pop() { print!("{} ", val); }
```

- `peek` 줄은 Debug 로 어떤 꼴을 찍나?
- 이어서 찍히는 수의 순서는?

### 3. Top-K 결과의 원소와 순서 (예측)

```rust
// 질문용 발췌
let data = vec![42, 15, 87, 3, 65, 91, 28, 73, 56, 11];
let k = 3;
let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
for &val in &data {
    min_heap.push(Reverse(val));
    if min_heap.len() > k { min_heap.pop(); }
}
let top_k: Vec<i32> = min_heap.into_sorted_vec().into_iter().map(|Reverse(v)| v).collect();
```

- `top_k` 에는 어떤 세 수가 어떤 순서로 들어 있나?

### 4. `peek_mut` 으로 루트를 바꾼 뒤의 새 루트 (예측)

- `BinaryHeap::from(vec![10, 5, 8, 3])` 의 루트를 `peek_mut` 으로 1 로 바꾸고 블록을 벗어난 뒤 `peek` 하면 무엇이 나오나?

### 5. Debug 로 찍은 힙이 정렬된 꼴이 아닌 까닭 (왜)

- `println!("{:?}", heap)` 이 큰 순서나 작은 순서로 찍힌다고 기대할 수 없는 까닭은 무엇인가?

### 6. `from` 이 하나씩 `push` 하기보다 나은 까닭 (왜)

- 값이 이미 `Vec` 에 다 있을 때 `BinaryHeap::from` 을 쓰는 편이 나은 까닭은 무엇인가?

### 7. Top-K 에 최대 힙이 아니라 최소 힙을 쓰는 까닭 (왜)

- 가장 큰 k 개를 고르는데 왜 크기 k 의 최소 힙을 유지하나?

### 8. 힙에서 곧바로 볼 수 있는 범위 (경계)

- 원소를 하나도 꺼내지 않고 두 번째로 큰 값을 알아낼 수 있나?

### 9. `Task` 의 `Ord` 와 derive 한 `PartialEq` 가 어긋나는 자리 (경계)

- priority 만 비교하는 `cmp` 와 두 필드를 모두 비교하는 `==` 는 어떤 두 작업에서 서로 다른 답을 내나?

### 10. Dijkstra 와 `Reverse` 의 다리 (연결)

- Dijkstra 알고리즘에 `BinaryHeap` 을 쓸 때 원소를 `Reverse` 로 감싸야 하는 까닭은 무엇인가?

## 실습

### 실습 1. `BinaryHeap` 일곱 장면 데모 만들기

**만들 것** — 최대 힙 · 최소 힙 · `from`/`into_sorted_vec` · `peek_mut` · `retain` · Top-K · 작업 우선순위 큐를 차례로 보여 주는 Rust 프로그램 하나를 만든다.

**요구 조건**

1. 1단계 — 빈 최대 힙에 3, 1, 4, 1, 5, 9 를 `push` 하고, 힙을 Debug 로 찍고, `peek` 결과를 찍은 뒤, `while let` 으로 `pop` 하며 값을 한 줄에 이어 찍는다.
2. 2단계 — `BinaryHeap<Reverse<i32>>` 에 3, 1, 4, 1, 5 를 `Reverse` 로 감싸 넣고, `peek` 결과를 찍은 뒤, `Some(Reverse(val))` 패턴으로 풀며 `pop` 한 값을 한 줄에 찍는다.
3. 3단계 — `BinaryHeap::from` 으로 `[5, 3, 8, 1, 9]` 의 힙을 만들어 찍고, `into_sorted_vec` 결과를 찍는다.
4. 4단계 — `[10, 5, 8, 3]` 으로 힙을 만들어 수정 전 모습을 찍고, `peek_mut` 으로 현재 루트를 찍은 뒤 1 로 바꾸고, 블록 밖에서 수정 후 힙과 새 `peek` 을 찍는다.
5. 5단계 — `[1, 2, 3, 4, 5, 6, 7, 8]` 의 힙에서 `retain` 으로 짝수만 남겨 찍고, `[3, 1, 4, 1, 5]` 의 힙을 `into_sorted_vec` 으로 바꿔 `Vec<i32>` 로 찍는다.
6. 6단계 — 주어진 `data` 와 `k = 3` 으로, 각 값을 `Reverse` 로 넣고 길이가 k 를 넘으면 `pop` 하는 최소 힙을 유지한 뒤, `into_sorted_vec` 결과에서 `Reverse` 를 벗겨 `Vec<i32>` 로 모아 `data` 와 함께 찍는다.
7. 7단계 — `priority: u32` 와 `name: String` 을 가진 `Task` 구조체에 `Debug` · `Eq` · `PartialEq` 를 derive 하고, `priority` 만 비교하는 `Ord` 와 그 `cmp` 를 그대로 쓰는 `PartialOrd` 를 구현한다.
8. 7단계(이어서) — 우선순위 1 · 10 · 5 · 8 의 작업 넷을 넣고, `pop` 하며 각 작업의 우선순위와 이름을 한 줄씩 찍는다.

**시작 코드**

```rust
// TODO: BinaryHeap 과 Reverse 를 가져온다

fn main() {
    // === 1. BinaryHeap 기본 (최대 힙) ===
    println!("=== BinaryHeap 기본 (최대 힙) ===");
    // TODO: 빈 힙을 만들고 3, 1, 4, 1, 5, 9 를 push
    // TODO: println!("heap: {:?}", heap);
    // TODO: println!("peek (최대값): {:?}", ...);
    print!("pop 순서: ");
    // TODO: while let 으로 pop 하며 print!("{} ", val);
    println!();

    // === 2. 최소 힙 (Reverse 사용) ===
    println!("\n=== 최소 힙 (Reverse) ===");
    // TODO: BinaryHeap<Reverse<i32>> 에 3, 1, 4, 1, 5 를 감싸 push
    // TODO: println!("min peek: {:?}", ...);
    print!("min pop 순서: ");
    // TODO: Some(Reverse(val)) 패턴으로 pop
    println!();

    // === 3. from, into_sorted_vec ===
    println!("\n=== from, into_sorted_vec ===");
    // TODO: vec![5, 3, 8, 1, 9] 로 힙 만들고 "heap: {:?}" 로 찍기
    // TODO: into_sorted_vec 결과를 "into_sorted_vec: {:?}" 로 찍기

    // === 4. peek_mut: 최대값 수정 ===
    println!("\n=== peek_mut ===");
    // TODO: vec![10, 5, 8, 3] 로 힙 만들고 "수정 전: {:?}"
    // TODO: peek_mut 으로 "현재 top: {}" 를 찍고 1 로 바꾸기
    // TODO: "수정 후: {:?}" 와 "새 top: {:?}" 찍기

    // === 5. retain, drain ===
    println!("\n=== retain ===");
    // TODO: vec![1, 2, 3, 4, 5, 6, 7, 8] 에서 짝수만 남기고 "짝수만 retain: {:?}"
    // TODO: vec![3, 1, 4, 1, 5] 를 정렬된 Vec<i32> 로 바꿔 "정렬: {:?}"

    // === 6. 실용 예: Top-K 문제 ===
    println!("\n=== 실용: Top-K 문제 ===");
    let data = vec![42, 15, 87, 3, 65, 91, 28, 73, 56, 11];
    let k = 3;
    // TODO: 크기 k 의 최소 힙 유지
    // TODO: top_k: Vec<i32> 만들기 (Reverse 벗기기)
    println!("data: {:?}", data);
    // TODO: println!("Top-{}: {:?}", k, top_k);

    // === 7. 실용 예: 작업 우선순위 큐 ===
    println!("\n=== 실용: 우선순위 큐 ===");
    #[derive(Debug, Eq, PartialEq)]
    struct Task {
        priority: u32,
        name: String,
    }

    // TODO: impl Ord for Task (priority 만 비교)
    // TODO: impl PartialOrd for Task (cmp 를 그대로)

    // TODO: 빈 힙 pq 를 만들고 아래 네 작업을 push
    //   (1, "낮은 우선순위 작업") (10, "긴급 작업") (5, "보통 작업") (8, "중요 작업")

    println!("우선순위 순서대로 처리:");
    // TODO: pop 하며 println!("  [우선순위 {}] {}", task.priority, task.name);
}
```

**확인 방법** — `rustc binaryheap.rs && ./binaryheap` (또는 `cargo run`)으로 돌려, 각 단계의 pop · 정렬 순서와 새 top · Top-K · 작업 처리 순서가 정리에서 따라간 값과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
