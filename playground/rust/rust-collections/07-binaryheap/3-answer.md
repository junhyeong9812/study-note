# rust/rust-collections/07 — BinaryHeap (이진 힙) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Some(9)`, 그리고 9 5 4 3 1 1 — 큰 값부터 나온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Some(9)
9 5 4 3 1 1 
```

**왜 그런가**
`BinaryHeap::new()` 는 최대 힙이라 루트에 가장 큰 9 가 있다.
`peek` 은 루트를 `Option<&T>` 로 보여 줄 뿐 빼지 않는다.
`pop` 은 매번 루트(그때의 최대값)를 꺼내고 sift-down 으로 규칙을 되살리므로 큰 값부터 나온다.
힙은 중복을 지우지 않으므로 1 이 두 번 나온다.
원본 주석의 `// Some(9)` · `// 9 5 4 3 1 1` 과도 맞다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `Some(Reverse(1))`, 그리고 1 1 3 4 5 — 작은 값부터 나온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Some(Reverse(1))
1 1 3 4 5 
```

**왜 그런가**
`Reverse` 는 비교를 뒤집어 실제 값이 작을수록 「크다」로 만든다.
그래서 최대 힙의 루트에 `Reverse(1)` 이 오고, `peek` 은 감싼 그대로 보여 준다.
`Some(Reverse(val))` 패턴이 껍데기를 벗기므로 `pop` 은 실제 값의 오름차순으로 찍힌다.
근거: 2-summary 「동작 방식 (2)」.

### 3. `[91, 87, 73]` — 셋은 가장 큰 세 수이고 큰 것부터 놓인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[91, 87, 73]
```

**왜 그런가**
크기를 3 으로 묶은 최소 힙은 넘칠 때마다 가장 작은 값을 내보내므로, 끝에는 73 · 87 · 91 이 남는다.
`into_sorted_vec` 은 원소의 `Ord` 기준 오름차순인데, 원소가 `Reverse` 라서 `Reverse(91) < Reverse(87) < Reverse(73)` 순으로 놓인다.
껍데기를 벗기면 실제 값으로는 내림차순 `[91, 87, 73]` 이다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 4. `Some(8)` — 바뀐 1 은 아래로 내려가고 8 이 루트가 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Some(8)
```

**왜 그런가**
`peek_mut` 은 루트 10 을 가변으로 빌려 주는 `PeekMut` 가드를 준다.
`*top = 1` 직후에는 규칙이 깨져 있지만, 블록이 끝나 가드가 Drop 될 때 1 이 sift-down 된다.
남은 값 5 · 8 · 3 · 1 가운데 가장 큰 8 이 새 루트가 된다.
원본 주석의 `// 8` 과도 맞다(원본 코드는 `{:?}` 로 찍으므로 꼴은 `Some(8)`).
근거: 2-summary 「동작 방식 (4)」.

### 5. Debug 는 내부 배열 순서를 그대로 보여 주기 때문이다

힙은 루트가 최대라는 것과 「부모 ≥ 자식」만 지킨다.
형제끼리나 다른 가지끼리는 순서가 없으므로, 내부 배열을 그대로 찍으면 정렬된 꼴이 아닐 수 있다.
그 배치 자체도 구현 세부사항이라 아무도 보장하지 않는다.
정렬된 목록이 필요하면 `into_sorted_vec` 이나 `pop` 반복을 쓴다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」 · 「구현 세부사항 대 언어 보장」.

### 6. `from` 은 한 번에 heapify 해 O(n) 이고, 하나씩 `push` 하면 O(n log n) 이기 때문이다

`push` 한 번은 O(log n) 이라 n 번이면 O(n log n) 이다.
`BinaryHeap::from(vec)` 은 배열 전체를 한 번에 힙으로 재배치해 O(n) 에 끝난다(원본 주석의 주장).
근거: 2-summary 「동작 방식 (3)」.

### 7. 버려야 할 후보(현재 Top-K 의 가장 작은 값)를 루트에서 바로 꺼내야 하기 때문이다

크기 k 의 최소 힙에서 루트는 「지금까지의 Top-K 가운데 가장 작은 값」이다.
새 값이 들어와 k 를 넘으면 `pop` 한 번으로 그 가장 약한 후보가 빠진다.
최대 힙이었다면 루트가 가장 큰 값이라 정작 지켜야 할 값을 버리게 된다.
힙 크기가 k 로 묶여 전체 비용은 O(n log k) 다.
근거: 2-summary 「동작 방식 (5)」.

### 8. 안 된다 — 곧바로 볼 수 있는 것은 루트 하나뿐이다

`peek` · `peek_mut` 은 루트만 다룬다.
두 번째로 큰 값은 루트를 `pop` 해야 루트 자리로 올라온다.
힙 전체를 정렬된 꼴로 보려면 `into_sorted_vec` 처럼 힙을 소비해야 한다.
근거: 2-summary 「어디서 틀리나 3」 · 「동작 방식 (1)」.

### 9. priority 는 같고 name 이 다른 두 작업에서 어긋난다

`cmp` 는 priority 만 보므로 둘을 `Equal` 이라 한다.
derive 한 `==` 는 두 필드를 다 보므로 `false` 라 한다.
표준 라이브러리는 `Ord` 와 `PartialEq` 가 같은 답을 내기를 요구하므로 이 구현은 엄밀히는 어긋난다.
원본 예제는 priority 가 모두 달라 어긋남이 드러나지 않을 뿐이다.
고치려면 `PartialEq` 를 priority 기준으로 직접 쓰거나 `cmp` 에 name 도 넣는다 (확인 필요).
근거: 2-summary 「어디서 틀리나 7」 · 「동작 방식 (6)」.

### 10. Dijkstra 는 거리가 가장 짧은 노드를 먼저 꺼내야 하는데 `BinaryHeap` 은 기본이 최대 힙이기 때문이다

그대로 넣으면 거리가 가장 먼 노드가 먼저 나온다.
`Reverse` 로 감싸면 비교가 뒤집혀 거리가 가장 짧은 원소가 루트로 오므로, `pop` 이 바로 다음에 확정할 노드를 준다.
팁이 Dijkstra 를 힙의 대표 쓰임으로 꼽는 것도 이 「매번 가장 작은 것 하나」 패턴 때문이다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 9」 (Dijkstra 의 동작 설명은 원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. `BinaryHeap` 일곱 장면 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 — 최대 힙에 push · Debug · peek · pop 반복 | `BinaryHeap::new()` · `heap.push(..)` · `heap.peek()` · `while let Some(val) = heap.pop()` |
| 2단계 — `Reverse` 최소 힙 · peek · 패턴으로 풀며 pop | `BinaryHeap<Reverse<i32>>` · `min_heap.push(Reverse(..))` · `while let Some(Reverse(val)) = min_heap.pop()` |
| 3단계 — `from` 으로 만들고 `into_sorted_vec` | `BinaryHeap::from(vec![5, 3, 8, 1, 9])` · `heap.into_sorted_vec()` |
| 4단계 — `peek_mut` 으로 루트를 1 로 바꾸고 전후 찍기 | `if let Some(mut top) = heap.peek_mut()` · `*top = 1` · 블록 뒤 `heap.peek()` |
| 5단계 — 짝수만 `retain` · 정렬 `Vec<i32>` | `heap.retain(\|&x\| x % 2 == 0)` · `let sorted: Vec<i32> = heap.into_sorted_vec()` |
| 6단계 — 크기 k 최소 힙 유지 · `Reverse` 벗겨 모으기 | `for &val in &data` 안의 `push(Reverse(val))` · `if min_heap.len() > k { min_heap.pop(); }` · `.map(\|Reverse(v)\| v).collect()` |
| 7단계 — `Task` 구조체와 `Ord` · `PartialOrd` 구현 | `#[derive(Debug, Eq, PartialEq)] struct Task` · `impl Ord for Task` 의 `self.priority.cmp(&other.priority)` · `impl PartialOrd` 의 `Some(self.cmp(other))` |
| 7단계(이어서) — 네 작업 push 후 pop 하며 한 줄씩 찍기 | `pq.push(Task { .. })` 넷 · `while let Some(task) = pq.pop()` · `println!("  [우선순위 {}] {}", ..)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-collections/reference/binaryheap.rs`

```rust
// [컬렉션 심화] BinaryHeap (이진 힙)
// 설명: BinaryHeap, 최대힙, 최소힙 트릭(Reverse), peek_mut, into_sorted_vec
// 팁: BinaryHeap은 기본이 최대 힙이다. 최소 힙이 필요하면 Reverse<T>로 감싸면 된다. peek_mut은 최대값을 수정할 수 있고 Drop 시 자동으로 힙 속성을 복원한다. Top-K 문제나 Dijkstra 알고리즘에서 자주 사용된다.

// BinaryHeap: 표준 라이브러리의 이진 힙(우선순위 큐) 컬렉션
// push/pop: O(log n), peek: O(1) - 항상 루트(최대값)만 즉시 접근 가능
use std::collections::BinaryHeap;
// Reverse<T>: Ord 구현을 뒤집는 래퍼. 최대 힙을 최소 힙처럼 사용할 때 쓴다
use std::cmp::Reverse;

fn main() {
    // === 1. BinaryHeap 기본 (최대 힙) ===
    println!("=== BinaryHeap 기본 (최대 힙) ===");
    // 빈 힙 생성. Rust의 BinaryHeap은 기본이 max-heap이다
    let mut heap = BinaryHeap::new();
    // push: O(log n) - 힙 상단으로 sift-up 하며 정렬 유지
    heap.push(3);
    heap.push(1);
    heap.push(4);
    heap.push(1);
    heap.push(5);
    heap.push(9);

    // Debug 출력은 내부 배열 순서이므로 정렬된 순서가 아닐 수 있음
    println!("heap: {:?}", heap);
    // peek: O(1) - 최대값(루트)을 &T로 반환. 제거하지 않음
    println!("peek (최대값): {:?}", heap.peek()); // Some(9)

    // pop: 최대값부터 제거
    print!("pop 순서: ");
    // pop: O(log n) - 최대값 제거 후 sift-down으로 힙 속성 복원
    while let Some(val) = heap.pop() {
        print!("{} ", val);
    }
    println!(); // 9 5 4 3 1 1

    // === 2. 최소 힙 (Reverse 사용) ===
    println!("\n=== 최소 힙 (Reverse) ===");
    // Reverse<i32>로 감싸면 Ord가 뒤집혀 최소값이 "가장 큰" 것이 되어 루트로 옴
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    // 각 값을 Reverse로 래핑하여 push
    min_heap.push(Reverse(3));
    min_heap.push(Reverse(1));
    min_heap.push(Reverse(4));
    min_heap.push(Reverse(1));
    min_heap.push(Reverse(5));

    // peek: 최소값(Reverse로 감싼 최대 비교 결과 = 실제 최소값)
    println!("min peek: {:?}", min_heap.peek()); // Some(Reverse(1))

    print!("min pop 순서: ");
    // 패턴 매칭으로 Reverse를 분해하여 원본 값 추출
    while let Some(Reverse(val)) = min_heap.pop() {
        print!("{} ", val);
    }
    println!(); // 1 1 3 4 5

    // === 3. from, into_sorted_vec ===
    println!("\n=== from, into_sorted_vec ===");
    // From<Vec<T>>: O(n)에 힙 구성(heapify). 하나씩 push하는 O(n log n)보다 빠름
    let heap = BinaryHeap::from(vec![5, 3, 8, 1, 9]);
    println!("heap: {:?}", heap);

    // into_sorted_vec: 오름차순 정렬된 Vec 반환
    // 힙을 소비하여 O(n log n)에 정렬된 Vec 생성
    let sorted = heap.into_sorted_vec();
    println!("into_sorted_vec: {:?}", sorted); // [1, 3, 5, 8, 9]

    // === 4. peek_mut: 최대값 수정 ===
    println!("\n=== peek_mut ===");
    let mut heap = BinaryHeap::from(vec![10, 5, 8, 3]);
    println!("수정 전: {:?}", heap);

    // peek_mut: 최대값을 가변 참조로 빌리는 PeekMut 가드 반환
    if let Some(mut top) = heap.peek_mut() {
        // Deref로 값에 접근
        println!("현재 top: {}", *top);
        *top = 1; // 최대값을 1로 변경
        // PeekMut가 Drop될 때 자동으로 힙 속성 복원
        // -> 변경된 값이 sift-down 되어 올바른 위치로 이동
    }
    println!("수정 후: {:?}", heap);
    println!("새 top: {:?}", heap.peek()); // 8

    // === 5. retain, drain ===
    println!("\n=== retain ===");
    let mut heap = BinaryHeap::from(vec![1, 2, 3, 4, 5, 6, 7, 8]);
    // retain: 조건에 맞는 요소만 유지하고 힙을 재구성
    heap.retain(|&x| x % 2 == 0);
    println!("짝수만 retain: {:?}", heap);

    // drain_sorted (nightly에서만)
    // 대안: into_sorted_vec 사용
    let heap = BinaryHeap::from(vec![3, 1, 4, 1, 5]);
    // 정렬된 Vec으로 변환 (오름차순)
    let sorted: Vec<i32> = heap.into_sorted_vec();
    println!("정렬: {:?}", sorted);

    // === 6. 실용 예: Top-K 문제 ===
    println!("\n=== 실용: Top-K 문제 ===");
    let data = vec![42, 15, 87, 3, 65, 91, 28, 73, 56, 11];
    let k = 3;

    // 최소 힙으로 Top-K 유지 (O(n log k))
    // 최소 힙 크기를 k로 유지하면 루트는 "현재 Top-K의 최솟값"이 된다
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for &val in &data {
        // 일단 push 후 크기가 k 초과면 가장 작은 값 제거
        min_heap.push(Reverse(val));
        if min_heap.len() > k {
            min_heap.pop(); // 가장 작은 값 제거
        }
    }
    // 정렬된 Vec으로 변환 후 Reverse 풀어 원본 값 복원
    let top_k: Vec<i32> = min_heap.into_sorted_vec()
        .into_iter().map(|Reverse(v)| v).collect();
    println!("data: {:?}", data);
    println!("Top-{}: {:?}", k, top_k);

    // === 7. 실용 예: 작업 우선순위 큐 ===
    println!("\n=== 실용: 우선순위 큐 ===");
    // 우선순위 작업을 표현하는 구조체. Eq+Ord를 통해 힙 정렬 기준 정의
    #[derive(Debug, Eq, PartialEq)]
    struct Task {
        priority: u32,
        name: String,
    }

    // Ord 구현: priority 기준으로 비교 -> 큰 priority가 먼저 pop됨
    impl Ord for Task {
        fn cmp(&self, other: &Self) -> std::cmp::Ordering {
            self.priority.cmp(&other.priority)
        }
    }

    // PartialOrd: Ord와 일관되게 구현 (관용적 패턴)
    impl PartialOrd for Task {
        fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
            Some(self.cmp(other))
        }
    }

    // 커스텀 타입 Task의 우선순위 큐
    let mut pq = BinaryHeap::new();
    pq.push(Task { priority: 1, name: "낮은 우선순위 작업".to_string() });
    pq.push(Task { priority: 10, name: "긴급 작업".to_string() });
    pq.push(Task { priority: 5, name: "보통 작업".to_string() });
    pq.push(Task { priority: 8, name: "중요 작업".to_string() });

    println!("우선순위 순서대로 처리:");
    // priority 큰 순서대로 pop (10 -> 8 -> 5 -> 1)
    while let Some(task) = pq.pop() {
        println!("  [우선순위 {}] {}", task.priority, task.name);
    }
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 최대 힙과 최소 힙은 힙 타입이 아니라 원소 타입(`i32` 대 `Reverse<i32>`)으로 갈린다.
- `peek` 은 빌려 보기, `pop` 은 꺼내기, `peek_mut` 은 고치기다 — 고친 뒤 규칙은 가드가 Drop 될 때 되살아난다.
- `into_sorted_vec` 은 힙을 소비하고 원소의 `Ord` 기준 오름차순을 주므로, `Reverse` 힙에서는 실제 값의 내림차순이 된다.
- Top-K 는 「넣고 → 넘치면 가장 작은 것 빼기」 두 줄로 끝나며, 힙 크기가 k 를 넘지 않는다.
- `Task` 처럼 직접 만든 타입은 `Ord` 의 `cmp` 가 꺼내는 순서를 정한다 — priority 가 큰 작업부터 나온다.
- `{:?}` 로 찍은 힙의 순서는 내부 배치라 정렬을 기대하지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
