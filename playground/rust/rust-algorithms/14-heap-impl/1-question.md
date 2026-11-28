# rust/rust-algorithms/14 — 힙 구현 & BinaryHeap — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 네 값을 차례로 넣은 뒤의 내부 배열 (예측)

```rust
// 질문용 발췌 — MinHeap 은 원본의 직접 구현
let mut heap = MinHeap::new();
for &v in &[5, 3, 8, 1] {
    heap.push(v);
}
// heap.data 는?
```

- 네 번의 `push` 가 끝난 뒤 `heap.data` 에 담긴 순서는 무엇인가?

### 2. Top K 코드에서 `Reverse` 를 뺀다면 (예측)

```rust
// 질문용 발췌 — 원본 Top K 에서 Reverse 만 뺐다
let nums = [3, 1, 5, 2, 4, 8, 7, 6];
let k = 3;
let mut heap: BinaryHeap<i32> = BinaryHeap::new();
for &num in &nums {
    heap.push(num);
    if heap.len() > k {
        heap.pop();
    }
}
println!("{}", heap.peek().unwrap());
```

- 마지막 `println!` 이 찍는 수는 무엇인가?
- 이 힙에 끝까지 남는 세 값은 무엇인가?

### 3. 여섯 개가 든 최소 힙에서 한 번 꺼내기 (예측)

```rust
// 질문용 발췌 — 6개를 넣은 뒤 heap.data 는 [1, 3, 2, 5, 4, 8]
let min = heap.pop();
// min 은? heap.data 는?
```

- `min` 에 담기는 값은 무엇인가?
- `pop` 이 끝난 뒤 `heap.data` 의 순서는 무엇인가?

### 4. `pop` 이 루트를 바로 지우지 않고 마지막과 바꾸는 까닭 (왜)

- 루트를 `Vec` 에서 곧바로 지우면 무엇이 망가지나?
- 마지막 원소와 바꾼 뒤 끝에서 떼면 무엇이 지켜지나?

### 5. K번째로 큰 수에 최소 힙을 쓰는 까닭 (왜)

- 「큰 값 K개」를 남기려는데 왜 최대 힙이 아니라 최소 힙을 유지하나?
- 이 방법의 시간복잡도가 O(n log n) 이 아니라 O(n log k) 인 까닭은 무엇인가?

### 6. `sift_up` 과 `sift_down` 이 멈추는 자리 (경계)

- `sift_up` 의 `while idx > 0` 조건이 없다면 루트에서 어떤 계산이 문제가 되나?
- `sift_down` 은 어떤 두 경우에 루프를 끝내나?

### 7. 힙이 보장하는 것과 보장하지 않는 것 (경계)

- 힙의 내부 배열을 앞에서부터 읽으면 정렬된 순서인가?
- 형제 노드끼리는 대소가 정해져 있나?

### 8. pop 반복과 정렬의 관계 (연결)

- 최소 힙에서 빌 때까지 pop 을 반복하면 왜 오름차순이 나오나?
- 같은 일을 표준 `BinaryHeap` 에 그대로 하면 어떤 순서가 나오나?

### 9. `Reverse` 와 패턴 매칭 (연결)

- `Reverse` 는 값의 무엇을 바꾸어 최대 힙을 최소 힙처럼 만드나?
- `while let Some(Reverse(v)) = min_heap.pop()` 의 패턴은 두 겹의 포장을 어떻게 벗기나?

## 실습

### 실습 1. 최소 힙을 직접 만들고 표준 BinaryHeap 과 비교하기

**만들 것** — `Vec<i32>` 로 최소 힙 `MinHeap` 을 직접 구현하고, 표준 `BinaryHeap`(최대 힙) · `BinaryHeap<Reverse<i32>>`(최소 힙) · Top K 풀이를 한 `main` 에서 차례로 보여 준다.

**요구 조건**

1단계 — `MinHeap` 구조체
1. `MinHeap` 은 `data: Vec<i32>` 필드 하나를 가진다.
2. `new()` 는 빈 힙을 만든다.
3. `push(val)` 은 값을 끝에 넣고 마지막 인덱스에서 `sift_up` 을 부른다.
4. `pop()` 은 빈 힙이면 `None` 을 돌려주고, 아니면 루트와 마지막을 바꾼 뒤 끝을 떼어 그 값을 돌려준다. 남은 원소가 있으면 0번에서 `sift_down` 을 부른다.
5. `peek()` 은 루트를 `Option<&i32>` 로 돌려준다.
6. `sift_up(idx)` 는 `idx > 0` 인 동안 부모 `(idx - 1) / 2` 보다 작으면 바꾸고 올라가며, 아니면 멈춘다.
7. `sift_down(idx)` 는 왼쪽 `2*idx+1` · 오른쪽 `2*idx+2` 자식 중 범위 안에서 가장 작은 쪽을 고르고, 그것이 자기 자신이면 멈추고 아니면 바꾸고 내려간다.
8. `len()` 은 원소 수를 돌려준다.

2단계 — 직접 구현 힙 써 보기
9. 5, 3, 8, 1, 4, 2 를 차례로 넣고 `peek` 결과를 찍는다.
10. 원소가 남아 있는 동안 pop 한 값을 한 줄에 이어 찍는다.

3단계 — 표준 `BinaryHeap`
11. 5, 3, 8, 1 을 넣고 `peek` 결과를 찍는다.
12. `while let Some(v)` 로 빌 때까지 꺼내 한 줄에 이어 찍는다.

4단계 — `Reverse` 로 최소 힙
13. `BinaryHeap<Reverse<i32>>` 에 5, 3, 8, 1, 4 를 `Reverse` 로 감싸 넣는다.
14. `while let Some(Reverse(v))` 로 꺼내 안의 값을 한 줄에 이어 찍는다.

5단계 — Top K
15. 배열 `[3, 1, 5, 2, 4, 8, 7, 6]` 과 `k = 3` 으로, 넣을 때마다 크기가 k 를 넘으면 pop 하는 최소 힙을 유지한다.
16. 배열과 「k번째로 큰 수」(루트의 `.0`)를 찍는다.

**시작 코드**

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

struct MinHeap {
    data: Vec<i32>,
}

impl MinHeap {
    fn new() -> Self {
        MinHeap { data: Vec::new() }
    }

    fn push(&mut self, val: i32) {
        // TODO: 끝에 넣고 마지막 인덱스에서 sift_up
    }

    fn pop(&mut self) -> Option<i32> {
        // TODO: 비었으면 None
        // TODO: 루트와 마지막 swap → Vec::pop → 남았으면 sift_down(0)
        None
    }

    fn peek(&self) -> Option<&i32> {
        // TODO: 루트 돌려주기
        None
    }

    fn sift_up(&mut self, mut idx: usize) {
        // TODO: idx > 0 인 동안 부모 (idx - 1) / 2 와 비교해 작으면 swap
    }

    fn sift_down(&mut self, mut idx: usize) {
        let len = self.data.len();
        loop {
            // TODO: 왼쪽 2*idx+1, 오른쪽 2*idx+2 중 가장 작은 쪽 고르기
            // TODO: 자기 자신이 가장 작으면 break, 아니면 swap 후 내려가기
            break;
        }
        let _ = (len, &mut idx);
    }

    fn len(&self) -> usize { self.data.len() }
}

fn main() {
    println!("=== 최소 힙 (직접 구현) ===");
    let mut heap = MinHeap::new();
    // TODO: 5, 3, 8, 1, 4, 2 넣기
    println!("peek: {:?}", heap.peek());
    print!("pop 순서: ");
    // TODO: 빌 때까지 pop 해서 찍기
    println!();

    println!("\n=== BinaryHeap (최대 힙) ===");
    // TODO: BinaryHeap 에 5, 3, 8, 1 넣고 peek 찍기
    print!("pop 순서: ");
    // TODO: while let Some(v) 로 꺼내 찍기
    println!();

    println!("\n=== BinaryHeap + Reverse (최소 힙) ===");
    // TODO: BinaryHeap<Reverse<i32>> 에 5, 3, 8, 1, 4 넣기
    print!("pop 순서: ");
    // TODO: while let Some(Reverse(v)) 로 꺼내 찍기
    println!();

    println!("\n=== Top K ===");
    let nums = [3, 1, 5, 2, 4, 8, 7, 6];
    let k = 3;
    // TODO: 크기 k 최소 힙 유지
    println!("배열: {:?}", nums);
    // TODO: "{}번째로 큰 수: {}" 로 루트의 .0 찍기
}
```

**확인 방법** — `rustc heap-impl.rs && ./heap-impl` 로 돌려, 직접 구현 힙의 pop 순서가 오름차순인지, `BinaryHeap` 은 큰 값부터인지, `Reverse` 힙은 작은 값부터인지, Top K 줄이 3번째로 큰 수를 가리키는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
