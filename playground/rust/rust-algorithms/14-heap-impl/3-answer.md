# rust/rust-algorithms/14 — 힙 구현 & BinaryHeap — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `[1, 3, 8, 5]` — 1 이 두 번 올라가 루트가 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
push 5 → [5]
push 3 → [5, 3] → 3 < 5 swap → [3, 5]
push 8 → [3, 5, 8] → 8 < 3 아님 → 그대로
push 1 → [3, 5, 8, 1] → 1 < 5 swap → [3, 1, 8, 5] → 1 < 3 swap → [1, 3, 8, 5]
```

**왜 그런가**
새 값은 언제나 끝 칸에 들어간 뒤 부모와 비교하며 올라간다.
1 은 index 3 에서 부모 index 1(5), 다시 부모 index 0(3)보다 작아 루트까지 오른다.
8 은 부모 3 보다 커서 제자리에 머문다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 3 — 최대 힙은 작은 세 값을 남긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

마지막 `println!` 은 3 을 찍는다.
끝까지 남는 세 값은 1, 2, 3 이다.

```text
3 → {3}
1 → {3, 1}
5 → {5, 3, 1}
2 → {5, 3, 2, 1} → 가장 큰 5 제거 → {3, 2, 1}
4 → 4 제거 → {3, 2, 1}
8 → 8 제거, 7 → 7 제거, 6 → 6 제거 → {3, 2, 1}
peek → 가장 큰 3
```

**왜 그런가**
`BinaryHeap` 은 최대 힙이라 `pop` 이 가장 큰 값을 버린다.
넘칠 때마다 큰 값이 사라지므로 작은 k개만 남고, `peek` 은 그중 가장 큰 값, 곧 3번째로 **작은** 수를 준다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 3. `Some(1)` 을 돌려주고 배열은 `[2, 3, 8, 5, 4]` 가 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
swap(0, 5)      [8, 3, 2, 5, 4, 1]
Vec::pop        [8, 3, 2, 5, 4]  → min = Some(1)
sift_down(0)    자식 3, 2 중 작은 2 < 8 → swap → [2, 3, 8, 5, 4]
index 2         자식 5, 6 은 len 5 이상 → 멈춤
```

**왜 그런가**
루트(최솟값)를 끝으로 보내 떼어 내고, 끝에 있던 8 을 루트에서 내린다.
8 은 두 자식 중 더 작은 2 와 자리를 바꾸고, 자식이 없는 칸에 닿아 멈춘다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 루트를 지우면 모든 부모·자식 관계가 흐트러진다

루트를 `Vec` 의 0번에서 지우면 뒤 원소가 모두 한 칸씩 앞으로 당겨진다.
그러면 index 로 계산하던 부모 · 자식 관계가 통째로 바뀌어 힙 속성이 대부분 깨진다.
마지막 원소와 바꾼 뒤 끝에서 떼면 다른 원소는 그 자리에 그대로 있어 완전 이진 트리 모양이 유지된다.
깨진 곳은 새 루트 한 자리뿐이라 `sift_down` 한 번(O(log n))으로 되살릴 수 있다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 6」.

### 5. 버릴 후보(가장 작은 값)를 루트에 두어야 하기 때문이다

큰 값 K개를 남기려면, 넘칠 때마다 남은 것 중 **가장 작은** 값을 버려야 한다.
최소 힙은 그 값을 루트에 두므로 `pop` 한 번으로 버릴 수 있고, 끝에 루트가 곧 K번째로 큰 수가 된다.
힙 크기가 언제나 k 정도로 묶여 있어 한 번의 push · pop 이 O(log k) 이고, 원소 n 개를 지나므로 O(n log k) 다.
근거: 2-summary 「동작 방식 (6)」.

### 6. 루트에서의 `0 - 1` 과, 「제자리」 또는 「자식 없음」

`while idx > 0` 이 없으면 루트(`idx == 0`)에서 `(idx - 1) / 2` 를 계산하게 된다.
`usize` 에서 `0 - 1` 은 표현할 수 없는 넘침이다.
`sift_down` 은 `smallest == idx` 일 때 멈춘다.
이것은 두 경우를 다 덮는다 — 자식이 있지만 둘 다 자기보다 작지 않을 때, 그리고 `left` · `right` 가 모두 `len` 이상이라 자식이 없을 때.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 3」.

### 7. 루트만 보장되고, 배열 순서와 형제 순서는 정해지지 않는다

정렬된 순서가 아니다.
`[1, 3, 2, 5, 4, 8]` 에서 3 이 2 보다 앞에 있다.
힙 속성은 부모와 자식 사이의 규칙일 뿐이라 형제끼리의 대소는 정해져 있지 않다.
근거: 2-summary 「한눈에」 그림 · 「동작 방식 (4)」 · 「어디서 틀리나 5」.

### 8. 꺼낼 때마다 그다음 최솟값이 루트로 올라오기 때문이다

pop 은 루트, 곧 남은 것 중 최솟값을 꺼내고 `sift_down` 으로 힙 속성을 되살린다.
되살린 힙의 루트는 다시 남은 것 중 최솟값이므로, 반복하면 작은 값부터 차례로 나온다 — 원본이 「힙 정렬」이라 부르는 것이다.
표준 `BinaryHeap` 은 최대 힙이라 같은 반복이 큰 값부터, 곧 내림차순을 준다(5, 3, 8, 1 을 넣으면 8, 5, 3, 1).
근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 9. 비교 방향만 뒤집고, 패턴이 `Some` 과 `Reverse` 를 차례로 벗긴다

`Reverse` 는 감싼 값의 대소 비교를 거꾸로 만든다.
최대 힙은 「가장 큰」 원소를 루트에 두는데, `Reverse` 끼리는 실제 값이 가장 작은 것이 「가장 크다」 — 그래서 가장 작은 값이 먼저 나온다.
`pop()` 은 `Option<Reverse<i32>>` 를 돌려준다.
`Some(..)` 이 `Option` 을 벗기고, 안쪽 `Reverse(v)` 가 래퍼를 벗겨 `v` 에 `i32` 를 묶는다.
힙이 비어 `None` 이 나오면 패턴이 맞지 않아 반복이 끝난다.
근거: 2-summary 「동작 방식 (5)」 · 「문법」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. 최소 힙을 직접 만들고 표준 BinaryHeap 과 비교하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `data: Vec<i32>` 필드 | `struct MinHeap { data: Vec<i32> }` |
| 2. 빈 힙 만들기 | `fn new()` — `MinHeap { data: Vec::new() }` |
| 3. 끝에 넣고 `sift_up` | `fn push` — `self.data.push(val)` · `self.sift_up(self.data.len() - 1)` |
| 4. 빈 힙 `None`, swap → pop → `sift_down` | `fn pop` — `is_empty()` 검사 · `swap(0, len - 1)` · `self.data.pop()` · `sift_down(0)` |
| 5. 루트 보기 | `fn peek` — `self.data.first()` |
| 6. 부모와 비교하며 올라가기 | `fn sift_up` — `while idx > 0` · `(idx - 1) / 2` · `else { break; }` |
| 7. 더 작은 자식과 바꾸며 내려가기 | `fn sift_down` — `smallest` · `left` · `right` · `if smallest == idx { break; }` |
| 8. 원소 수 | `fn len` — `self.data.len()` |
| 9. 6개 넣고 `peek` | `for &v in &[5, 3, 8, 1, 4, 2]` · `heap.peek()` |
| 10. 빌 때까지 pop | `while heap.len() > 0` · `heap.pop().unwrap()` |
| 11. 표준 최대 힙에 넣고 `peek` | `max_heap.push(5)` … · `max_heap.peek()` |
| 12. `while let Some(v)` | `while let Some(v) = max_heap.pop()` |
| 13. `Reverse` 로 감싸 넣기 | `BinaryHeap<Reverse<i32>>` · `min_heap.push(Reverse(v))` |
| 14. `Reverse` 벗겨 꺼내기 | `while let Some(Reverse(v)) = min_heap.pop()` |
| 15. 크기 k 최소 힙 유지 | `if min_heap.len() > k { min_heap.pop(); }` |
| 16. 배열과 k번째로 큰 수 | `println!("배열: {:?}", nums)` · `min_heap.peek().unwrap().0` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-algorithms/reference/heap-impl.rs`

```rust
// [알고리즘 & 자료구조] 힙 구현 & BinaryHeap
// 설명: 최소 힙 직접 구현과 표준 BinaryHeap 활용법
// 팁: push/pop 시간복잡도: O(log n). BinaryHeap은 최대 힙이다. 최소 힙이 필요하면 Reverse<T>를 사용한다. Top K 문제: 크기 K 최소 힙을 유지하면 O(n log k)로 K번째로 큰 수를 찾을 수 있다. 힙 직접 구현의 핵심은 sift_up(삽입 후 위로)과 sift_down(삭제 후 아래로)이다.

// BinaryHeap: 표준 라이브러리 최대 힙
use std::collections::BinaryHeap;
// Reverse: 비교 순서를 뒤집는 래퍼 (BinaryHeap을 최소 힙으로)
use std::cmp::Reverse;

// 최소 힙 직접 구현
// 배열로 표현되는 완전 이진 트리: 부모 (i-1)/2, 왼자식 2i+1, 오른자식 2i+2
struct MinHeap {
    data: Vec<i32>,
}

impl MinHeap {
    // 빈 힙 생성
    fn new() -> Self {
        MinHeap { data: Vec::new() }
    }

    // 삽입 O(log n): 끝에 추가 후 위로 sift
    fn push(&mut self, val: i32) {
        self.data.push(val);
        // 마지막 인덱스에서 위로 올라가며 힙 속성 복원
        self.sift_up(self.data.len() - 1);
    }

    // 최솟값 제거 O(log n): 루트와 마지막을 swap → pop → 루트에서 아래로 sift
    fn pop(&mut self) -> Option<i32> {
        if self.data.is_empty() { return None; }
        let len = self.data.len();
        // 루트(최솟값)와 마지막 원소 교환
        self.data.swap(0, len - 1);
        // 마지막 원소(=원래 최솟값) 제거하여 반환
        let min = self.data.pop();
        // 새 루트를 알맞은 위치로 내림
        if !self.data.is_empty() {
            self.sift_down(0);
        }
        min
    }

    // 최솟값 조회 O(1): 루트 = data[0]
    fn peek(&self) -> Option<&i32> {
        self.data.first()
    }

    // sift_up: idx 노드를 부모와 비교하며 작으면 swap → 위로 이동
    fn sift_up(&mut self, mut idx: usize) {
        while idx > 0 {
            // 부모 인덱스: (idx - 1) / 2
            let parent = (idx - 1) / 2;
            // 부모보다 작으면 교환
            if self.data[idx] < self.data[parent] {
                self.data.swap(idx, parent);
                idx = parent;
            } else {
                // 힙 속성 만족 → 종료
                break;
            }
        }
    }

    // sift_down: idx 노드를 두 자식 중 더 작은 쪽과 비교 → 자식이 더 작으면 swap → 아래로
    fn sift_down(&mut self, mut idx: usize) {
        let len = self.data.len();
        loop {
            let mut smallest = idx;
            // 왼자식 / 오른자식 인덱스
            let left = 2 * idx + 1;
            let right = 2 * idx + 2;
            // 왼자식이 더 작으면 후보 교체
            if left < len && self.data[left] < self.data[smallest] {
                smallest = left;
            }
            // 오른자식이 더 작으면 후보 교체
            if right < len && self.data[right] < self.data[smallest] {
                smallest = right;
            }
            // 자식 모두 부모보다 크면 → 힙 속성 만족 → 종료
            if smallest == idx { break; }
            self.data.swap(idx, smallest);
            idx = smallest;
        }
    }

    // 원소 수
    fn len(&self) -> usize { self.data.len() }
}

fn main() {
    // === 직접 구현 최소 힙 ===
    println!("=== 최소 힙 (직접 구현) ===");
    let mut heap = MinHeap::new();
    // 임의 순서 삽입
    for &v in &[5, 3, 8, 1, 4, 2] {
        heap.push(v);
    }
    // 최소값은 1
    println!("peek: {:?}", heap.peek()); // Some(1)
    print!("pop 순서: ");
    // pop을 반복하면 오름차순 정렬된 값이 나옴 (힙 정렬)
    while heap.len() > 0 {
        print!("{} ", heap.pop().unwrap());
    }
    println!(); // 1 2 3 4 5 8

    // === BinaryHeap (최대 힙) ===
    println!("\n=== BinaryHeap (최대 힙) ===");
    // 표준 BinaryHeap은 기본이 최대 힙
    let mut max_heap = BinaryHeap::new();
    max_heap.push(5);
    max_heap.push(3);
    max_heap.push(8);
    max_heap.push(1);
    println!("peek: {:?}", max_heap.peek()); // Some(8)
    print!("pop 순서: ");
    // 큰 값부터 나옴
    while let Some(v) = max_heap.pop() {
        print!("{} ", v);
    }
    println!(); // 8 5 3 1

    // === BinaryHeap으로 최소 힙 (Reverse) ===
    println!("\n=== BinaryHeap + Reverse (최소 힙) ===");
    // Reverse로 감싸면 비교가 뒤집혀 최대 힙이 최소 힙처럼 동작
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for &v in &[5, 3, 8, 1, 4] {
        min_heap.push(Reverse(v));
    }
    print!("pop 순서: ");
    // 패턴 매칭으로 Reverse 안의 값 추출
    while let Some(Reverse(v)) = min_heap.pop() {
        print!("{} ", v);
    }
    println!(); // 1 3 4 5 8

    // === Top K 문제: 배열에서 K번째로 큰 수 ===
    println!("\n=== Top K ===");
    let nums = [3, 1, 5, 2, 4, 8, 7, 6];
    let k = 3;
    // 크기 k 최소 힙을 유지: 루트 = K번째로 큰 수
    let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new();
    for &num in &nums {
        // 일단 추가
        min_heap.push(Reverse(num));
        // 크기가 k 초과면 가장 작은 것 제거 → 항상 큰 k개만 유지
        if min_heap.len() > k {
            min_heap.pop();
        }
    }
    println!("배열: {:?}", nums);
    // 최소 힙의 루트 = k개의 큰 값 중 가장 작은 것 = k번째로 큰 수
    println!("{}번째로 큰 수: {}", k, min_heap.peek().unwrap().0); // 6
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 배열 인덱스 공식(부모 `(i-1)/2`, 자식 `2i+1` · `2i+2`) 하나로 트리를 포인터 없이 다룬다.
- `push` 는 끝 + `sift_up`, `pop` 은 루트↔끝 swap + 끝 떼기 + `sift_down` — 깨지는 자리가 한 곳이라 O(log n) 으로 고친다.
- `sift_down` 은 반드시 두 자식 중 **더 작은** 쪽과 바꾸고, `left < len` · `right < len` 으로 범위를 지킨다.
- 표준 `BinaryHeap` 은 최대 힙이므로, 최소 힙이 필요하면 `Reverse` 로 감싸고 꺼낼 때 패턴이나 `.0` 으로 벗긴다.
- Top K 는 「크기 k 의 최소 힙」을 유지해 큰 k개만 남기고, 루트를 K번째로 큰 수로 읽는다 — O(n log k).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
