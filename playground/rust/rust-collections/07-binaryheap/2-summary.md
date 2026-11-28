# rust/rust-collections/07 — BinaryHeap (이진 힙) — 정리 (힌트)

> 출처 — study-site 항목 `rust/binaryheap`(항목 데이터 `data/rust/collections-deep.json`) · 정답 코드 study-practice `rust/rust-collections/reference/binaryheap.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**`BinaryHeap` 은 「응급실 대기 줄」이다.**
환자는 온 순서대로 진료받지 않는다.
가장 위급한 환자 한 명만 늘 맨 앞에 서 있다.
나머지 환자는 대충의 순서로만 앉아 있다.
새 환자가 오면 위급도를 비교해 자리를 잡는다.
맨 앞 환자가 진료실로 들어가면 남은 사람 가운데 가장 위급한 사람이 앞으로 나온다.
`BinaryHeap` 도 똑같은 구조다.
가장 큰 값 하나만 늘 맨 위(루트)에 있고, 나머지는 「부모가 자식보다 크다」는 규칙만 지킨 채 흩어져 있다.

| 비유 | 실체 |
|---|---|
| 환자 | 힙에 든 원소 |
| 위급도 | 원소의 `Ord` 비교 결과 |
| 맨 앞에 선 환자 | 루트(최대값) — `peek` 이 보는 값 |
| 진료실에 들여보내기 | `pop` |
| 새 환자 접수 | `push` |
| 위급도 기준을 거꾸로 뒤집은 줄 | `Reverse<T>` 로 감싼 최소 힙 |

```text
        9          ← 루트: 늘 가장 큰 값 (peek 이 보는 자리)
      /   \
     4     5       ← 부모 ≥ 자식 규칙만 지킨다
    / \   /
   1   1 3         ← 형제끼리는 순서가 없다
```

## 이 주제가 답하려는 질문

1. 값을 아무 순서로 넣어도 「가장 큰 것부터」 꺼내려면 어떤 자료구조를 쓰나?
2. 기본이 최대 힙인데, 「가장 작은 것부터」 꺼내려면 어떻게 하나?
3. 루트 값을 꺼내지 않고 고치면 힙 규칙은 어떻게 지켜지나?
4. Top-K 나 작업 우선순위 큐 같은 실제 문제에 힙을 어떻게 끼우나?

## 동작 방식

### (1) 최대 힙 — `push` 로 넣고 `pop` 으로 큰 것부터 꺼낸다

**언제 쓰나** — 원소를 계속 넣고 빼면서 「지금 가장 큰 것」만 자꾸 필요할 때 쓴다.
전체를 정렬해 둘 필요는 없을 때 맞다.

> **이진 힙** — 부모가 자식보다 늘 크거나 같은(최대 힙의 경우) 완전 이진 트리를 배열 하나에 담은 자료구조다.\
> 예: `[9, 4, 5, 1, 1, 3]` 은 0번(9)의 자식이 1·2번(4, 5)인 트리를 뜻한다.

> **최대 힙** — 루트에 가장 큰 값이 오는 힙이다.\
> 예: `BinaryHeap::new()` 로 만든 힙.

```text
push 3 → push 1 → push 4 → push 1 → push 5 → push 9
  (새 값은 맨 끝에 붙고, 부모보다 크면 위로 자리를 바꾼다 = sift-up)

마지막 push 9 의 경우 (교과서식 sift-up 으로 그린 예시 — 실제 배치는 구현 세부사항)
 [5,4,3,1,1,9] → 9 와 부모 3 교환 → [5,4,9,1,1,3] → 9 와 부모 5 교환 → [9,4,5,1,1,3]

peek → Some(9)                (루트를 &T 로 빌려 볼 뿐, 빼지 않는다)
pop 반복 → 9, 5, 4, 3, 1, 1   (루트를 빼고 맨 끝 값을 루트에 올린 뒤 아래로 내린다 = sift-down)
```

- 새 값은 배열의 끝에 붙는다.
- 붙은 값이 부모보다 크면 부모와 자리를 바꾸며 올라간다(sift-up).
- `peek` 은 루트를 `Option<&T>` 로 돌려줄 뿐 힙을 바꾸지 않는다.
- `pop` 은 루트를 `Option<T>` 로 꺼내고, 빈 자리를 채운 뒤 아래로 내려 규칙을 되살린다(sift-down).
- 그래서 `pop` 을 되풀이하면 큰 값부터 차례로 나온다.
- 같은 값 1 이 둘이면 둘 다 나온다 — 힙은 중복을 지우지 않는다.

> **sift-up / sift-down** — 규칙이 깨진 원소를 부모 쪽(위)으로 올리거나 자식 쪽(아래)으로 내려 힙 규칙을 되살리는 과정이다.\
> 예: `push` 는 sift-up, `pop` 은 sift-down 을 쓴다.

원본 주석이 적은 비용은 `push` · `pop` 이 O(log n), `peek` 이 O(1) 이다.
트리의 높이만큼만 오르내리기 때문이다.

### (2) 최소 힙 — `Reverse<T>` 로 비교를 뒤집는다

**언제 쓰나** — 「가장 작은 것부터」 꺼내야 할 때 쓴다.
Dijkstra 알고리즘이 대표다 — 아직 처리하지 않은 노드 가운데 거리가 가장 짧은 노드를 먼저 꺼내야 하므로 최소 힙이 필요하다.

> **`Reverse<T>`** — `std::cmp` 에 있는 래퍼로, 안에 든 값의 `Ord` 비교를 거꾸로 뒤집는다.\
> 예: `Reverse(1) > Reverse(3)` 이 참이다.

```text
push Reverse(3), Reverse(1), Reverse(4), Reverse(1), Reverse(5)

비교 뒤집기:  1 < 3  이면  Reverse(1) > Reverse(3)
              → 힙 입장에서 「가장 큰 것」 = Reverse(1)

peek  → Some(Reverse(1))
pop 하며 Some(Reverse(val)) 로 풀기 → 1, 1, 3, 4, 5
```

- 힙 자체는 여전히 최대 힙이다.
- 바뀐 것은 원소의 비교 결과뿐이다.
- 실제 값이 작을수록 `Reverse` 비교에서는 「크다」가 되어 루트로 올라간다.
- `peek` 은 감싼 그대로 `Some(Reverse(1))` 을 돌려준다.
- `while let Some(Reverse(val)) = min_heap.pop()` 처럼 패턴으로 껍데기를 벗기면 원래 값을 얻는다.

### (3) 한꺼번에 만들고, 정렬해 꺼내고, 걸러 낸다 — `from` · `into_sorted_vec` · `retain`

**언제 쓰나** — 값이 이미 `Vec` 에 다 모여 있을 때, 또는 힙의 내용을 한 번에 정렬된 목록으로 바꾸거나 조건으로 거를 때 쓴다.

> **heapify** — 정렬 안 된 배열 전체를 한 번에 힙 규칙에 맞게 재배치하는 일이다.\
> 예: `BinaryHeap::from(vec![5, 3, 8, 1, 9])`.

```text
vec![5, 3, 8, 1, 9]
   └─ BinaryHeap::from ── heapify, O(n) ──→ 힙 (내부 배열 순서는 정렬 순서가 아닐 수 있다)
                                              └─ into_sorted_vec (힙을 소비) ──→ [1, 3, 5, 8, 9]  오름차순

vec![1..=8]
   └─ from → retain(|&x| x % 2 == 0) ──→ 2, 4, 6, 8 만 남은 힙 (재구성됨)
```

- `BinaryHeap::from(vec)` 은 `Vec` 을 받아 O(n) 에 힙을 만든다(원본 주석).
- 하나씩 `push` 하면 n 번 × O(log n) 이라 O(n log n) 이므로, 다 모인 값이면 `from` 이 빠르다.
- `{:?}` 로 힙을 찍으면 내부 배열 순서가 보이므로 정렬된 꼴이 아닐 수 있다.
- `into_sorted_vec` 은 힙을 소비해(그 뒤 힙은 못 쓴다) **오름차순** `Vec` 을 O(n log n) 에 돌려준다.
- 「오름차순」은 원소의 `Ord` 기준이다 — `Reverse` 로 감싼 원소라면 실제 값으로는 내림차순이 된다(아래 (5)).
- `retain` 은 조건이 참인 원소만 남기고 힙을 다시 맞춘다.
- 정렬된 채로 하나씩 빼내는 `drain_sorted` 는 원본에 따르면 nightly 에서만 쓸 수 있어, 대안으로 `into_sorted_vec` 을 쓴다.

### (4) `peek_mut` — 루트를 고치면 가드가 사라질 때 규칙을 되살린다

**언제 쓰나** — 루트 값을 꺼냈다 다시 넣는 대신, 그 자리에서 바로 고치고 싶을 때 쓴다.

> **`PeekMut` 가드** — `peek_mut` 이 돌려주는 값으로, 루트를 가변으로 빌려 주고 자신이 Drop 될 때 힙 규칙을 되살린다.\
> 예: `if let Some(mut top) = heap.peek_mut() { *top = 1; }`.

> **Drop** — 값이 스코프를 벗어나 사라지는 순간 자동으로 불리는 정리 동작이다.\
> 예: `if let` 블록의 닫는 중괄호에서 `top` 이 Drop 된다.

```text
from(vec![10, 5, 8, 3])         peek_mut 로 *top = 1         가드 Drop → sift-down
       10                             1                            8
      /  \                           /  \                         /  \
     5    8          →              5    8            →          5    1
    /                              /                            /
   3                              3  (규칙 깨진 상태)           3
(트리 모양은 교과서식 예시 — 실제 배치는 구현 세부사항)

새 peek → Some(8)
```

- `peek_mut` 은 비어 있으면 `None`, 아니면 `Some(PeekMut)` 를 준다.
- `*top` 으로 루트 값을 읽는다(Deref).
- `*top = 1` 로 루트를 바꾸면 그 순간에는 힙 규칙이 깨져 있다.
- 블록이 끝나 가드가 Drop 될 때 바뀐 값이 sift-down 되어 제자리로 내려간다.
- 그래서 블록 밖에서 `peek` 하면 남은 값 가운데 가장 큰 8 이 보인다.

### (5) Top-K — 크기 k 의 최소 힙을 유지한다

**언제 쓰나** — n 개 가운데 가장 큰 k 개만 필요할 때 쓴다.
전체를 정렬(O(n log n))하지 않고 O(n log k) 에 끝난다.

```text
data = [42, 15, 87, 3, 65, 91, 28, 73, 56, 11],  k = 3
매 값마다: push(Reverse(val)) → 길이 > 3 이면 pop (가장 작은 값이 빠진다)

42,15,87       → {15, 42, 87}
3   push→pop 3 → {15, 42, 87}
65  push→pop 15→ {42, 65, 87}
91  push→pop 42→ {65, 87, 91}
28  push→pop 28→ {65, 87, 91}
73  push→pop 65→ {73, 87, 91}
56  push→pop 56→ {73, 87, 91}
11  push→pop 11→ {73, 87, 91}

into_sorted_vec : Reverse 기준 오름차순 = [Reverse(91), Reverse(87), Reverse(73)]
map(|Reverse(v)| v) → [91, 87, 73]
```

- 힙 크기를 k 로 묶으면 루트는 「지금까지의 Top-K 가운데 가장 작은 값」이다.
- 새 값이 들어와 크기가 k 를 넘으면 가장 작은 값이 빠진다 — 문지기가 가장 약한 후보를 내보내는 꼴이다.
- 그래서 최대 힙이 아니라 최소 힙이 필요하다 — 버릴 후보(가장 작은 값)를 루트에서 바로 꺼내야 하기 때문이다.
- 마지막에 `into_sorted_vec` 은 `Reverse` 기준 오름차순이므로 실제 값으로는 큰 것부터 놓인다.

### (6) 직접 만든 타입 — `Ord` 를 구현해 우선순위를 정한다

**언제 쓰나** — 원소가 숫자가 아니라 「우선순위와 이름을 가진 작업」 같은 구조체일 때 쓴다.

> **`Ord`** — 두 값의 순서를 `Ordering::Less / Equal / Greater` 로 알려 주는 전순서 트레이트다.\
> 예: `self.priority.cmp(&other.priority)`.

```text
struct Task { priority: u32, name: String }
impl Ord for Task  → priority 만 비교
impl PartialOrd    → Some(self.cmp(other))   (Ord 와 같은 답을 주도록)

push: 1 낮은 / 10 긴급 / 5 보통 / 8 중요
pop 순서: 10 긴급 → 8 중요 → 5 보통 → 1 낮은
```

- `BinaryHeap<T>` 은 `T: Ord` 를 요구하므로 `Ord` 를 구현해야 넣을 수 있다.
- `Ord` 는 `Eq` 와 `PartialOrd` 를 함께 요구하므로 `#[derive(Eq, PartialEq)]` 와 `impl PartialOrd` 가 같이 붙는다.
- `cmp` 가 `priority` 만 비교하므로 priority 가 큰 작업이 먼저 `pop` 된다.
- `partial_cmp` 를 `Some(self.cmp(other))` 로 쓰는 것은 두 비교가 서로 다른 답을 내지 않게 하는 관용 패턴이다.

## 문법 — 형태와 규칙

```rust
use std::collections::BinaryHeap;
use std::cmp::Reverse;

fn main() {
    let mut h = BinaryHeap::from(vec![2, 7, 4]);   // 한 번에 힙 만들기
    h.push(9);                                      // 넣기
    println!("{:?}", h.peek());                     // 루트 보기: Option<&i32>
    if let Some(mut t) = h.peek_mut() { *t = 0; }   // 루트 고치기 → Drop 때 복원
    let v = h.into_sorted_vec();                    // 소비 → 오름차순 Vec

    let mut m = BinaryHeap::new();
    m.push(Reverse(5));                             // 최소 힙
    if let Some(Reverse(x)) = m.pop() { println!("{x}"); }
}
```

- `use std::collections::BinaryHeap;` · `use std::cmp::Reverse;` 로 가져온다.
- `BinaryHeap<T>` 의 `T` 는 `Ord` 를 구현해야 한다.
- `push(x)` — 넣는다.
- `pop()` — 루트를 꺼내 `Option<T>` 로 준다(비면 `None`).
- `peek()` — 루트를 `Option<&T>` 로 본다(빼지 않음).
- `peek_mut()` — 루트를 가변으로 빌리는 `Option<PeekMut<T>>` 를 준다.
- `len()` — 원소 개수.
- `BinaryHeap::from(vec)` — `Vec` 에서 한 번에 만든다.
- `into_sorted_vec()` — 힙을 소비하고 오름차순 `Vec` 을 준다.
- `retain(|&x| 조건)` — 조건이 참인 원소만 남긴다.
- 최소 힙은 타입을 `BinaryHeap<Reverse<T>>` 로 두고 `Reverse(x)` 로 감싸 넣는다.
- 꺼낼 때 `Some(Reverse(v))` 패턴이나 `.map(|Reverse(v)| v)` 로 껍데기를 벗긴다.

## 어디서 틀리나

### 1. 기본이 최소 힙이라고 생각한다

`BinaryHeap` 은 기본이 최대 힙이다.
다른 언어의 우선순위 큐를 떠올려 「작은 것부터 나오겠지」 하면 거꾸로 된다.
최소 힙이 필요하면 `Reverse<T>` 로 감싼다.

### 2. `{:?}` 로 찍은 힙을 정렬된 순서로 읽는다

Debug 표현은 내부 배열 순서다.
루트(첫 원소)가 최대라는 것 말고는 정렬을 기대하면 안 된다.
정렬된 목록이 필요하면 `into_sorted_vec` 을 쓰거나 `pop` 을 되풀이한다.

### 3. `peek` 으로 두 번째 값까지 볼 수 있다고 생각한다

즉시 볼 수 있는 것은 루트 하나뿐이다.
두 번째로 큰 값은 루트를 `pop` 해야 루트로 올라온다.

### 4. `peek_mut` 으로 고친 뒤 블록 안에서 힙 순서가 이미 맞다고 생각한다

힙 규칙은 `PeekMut` 가드가 Drop 될 때 되살아난다.
고친 값을 넣은 블록이 끝나야 새 루트가 제자리를 찾는다.

### 5. `Reverse` 힙의 `into_sorted_vec` 을 실제 값의 오름차순으로 읽는다

`into_sorted_vec` 은 원소의 `Ord` 기준으로 오름차순이다.
원소가 `Reverse` 라면 실제 값으로는 내림차순이 된다.
Top-K 예제에서 결과가 `[91, 87, 73]` 처럼 큰 것부터 놓이는 까닭이다.

### 6. `into_sorted_vec` 뒤에 힙을 또 쓴다

`into_sorted_vec` 은 `self` 를 받아 힙을 소비한다.
그 뒤에는 원래 변수를 쓸 수 없다.

### 7. `Ord` 와 derive 한 `PartialEq` 가 서로 다른 말을 한다

원본의 `Task` 는 `PartialEq` · `Eq` 를 derive 해 **두 필드 모두** 같아야 같다고 본다.
그런데 `Ord::cmp` 는 **priority 만** 비교한다.
원본의 주장 — 「PartialOrd: Ord와 일관되게 구현 (관용적 패턴)」 — 은 `PartialOrd` 와 `Ord` 사이에서는 맞다.
의심스러운 곳은 `Ord` 와 `PartialEq` 사이다.
priority 가 같고 이름이 다른 두 작업은 `cmp` 로는 `Equal` 인데 `==` 로는 `false` 다.
표준 라이브러리는 이 둘이 서로 맞기를 요구하므로, 엄밀히는 `PartialEq` 도 priority 만 비교하게 직접 구현하거나 `cmp` 에 `name` 도 넣어 비교해야 한다 (확인 필요).
원본 예제는 priority 가 모두 달라 이 어긋남이 드러나지 않는다.

### 8. `drain_sorted` 를 그냥 쓴다

원본에 따르면 `drain_sorted` 는 nightly 에서만 쓸 수 있다.
안정판에서는 `into_sorted_vec` 이나 `pop` 반복을 쓴다.

### 9. 쓸 자리를 놓친다

팁이 짚은 대로 Top-K 문제와 Dijkstra 알고리즘이 대표적인 자리다.
「매번 가장 큰(작은) 것 하나」가 반복해서 필요하면 힙을 떠올린다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `BinaryHeap` 은 기본이 최대 힙이다 | 표준 라이브러리 API 가 약속한다 |
| `into_sorted_vec` 은 오름차순 `Vec` 을 준다 | 표준 라이브러리 API 가 약속한다 |
| `PeekMut` 가 Drop 될 때 힙 규칙을 되살린다 | 표준 라이브러리 API 가 약속한다 |
| `{:?}` 의 원소 순서 · 트리 그림의 실제 배치 | 아무도 보장하지 않는다 — 내부 배열 배치는 구현 세부사항이다 |
| `push` · `pop` O(log n), `peek` O(1), `from` O(n) | 원본 주석의 주장 — std 문서의 정확한 표기(평균 · 최악 구분)는 (확인 필요) |
| `drain_sorted` 는 nightly 에서만 | 원본의 주장 — Rust 버전에 따라 달라질 수 있다 (확인 필요) |
| `Reverse` 가 비교를 뒤집는다 | 표준 라이브러리(`std::cmp`)가 약속한다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 넣고 빼며 매번 가장 큰 값이 필요하다 | `BinaryHeap` | 매번 `Vec::sort` |
| 매번 가장 작은 값이 필요하다 (Dijkstra 등) | `BinaryHeap<Reverse<T>>` | 최대 힙을 그대로 쓰고 끝에서 뒤집기 |
| n 개 중 큰 k 개만 필요하다 | 크기 k 의 `Reverse` 최소 힙 | 전체 정렬 |
| 값이 이미 `Vec` 에 다 있다 | `BinaryHeap::from` | 하나씩 `push` |
| 루트를 조금 고쳐 다시 넣는다 | `peek_mut` | `pop` 한 뒤 `push` |
| 전체를 정렬된 순서로 한 번 훑는다 | `into_sorted_vec` | `{:?}` 로 찍힌 순서를 믿기 |
| 임의 위치의 원소를 찾거나 고친다 | 다른 컬렉션 (`Vec` · `BTreeMap` 등) | `BinaryHeap` |

## 핵심 문장

1. **`BinaryHeap` 은 루트 하나만 정렬을 보장한다** — 루트가 최대이고 나머지는 「부모 ≥ 자식」만 지킨다.
2. **최소 힙은 힙을 바꾸는 게 아니라 비교를 뒤집는 것이다** — `Reverse<T>` 로 감싸 넣고 패턴으로 벗긴다.
3. **`peek_mut` 은 가드가 Drop 될 때 규칙을 되살린다** — 고친 값은 블록이 끝나야 제자리를 찾는다.
4. **Top-K 는 크기 k 의 최소 힙이다** — 루트에서 가장 약한 후보를 바로 내보낸다.
5. **직접 만든 타입은 `Ord` 가 순서를 정한다** — `Ord` · `PartialOrd` · `PartialEq` 가 같은 말을 해야 한다.

## 관련 자료

- `vecdeque` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `iterator-consumers` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `custom-collection` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/collections-deep.json` 의 `binaryheap`

## 용어 풀이

- **이진 힙** — 부모와 자식 사이의 크기 규칙만 지키는 완전 이진 트리를 배열에 담은 자료구조.
- **최대 힙 / 최소 힙** — 루트에 가장 큰 값 / 가장 작은 값이 오는 힙.
- **우선순위 큐** — 넣은 순서가 아니라 우선순위 순으로 꺼내는 큐.
- **루트** — 트리의 맨 위 원소, 힙에서는 `peek` 이 보는 값.
- **sift-up / sift-down** — 원소를 위로 올리거나 아래로 내려 힙 규칙을 되살리는 과정.
- **heapify** — 배열 전체를 한 번에 힙으로 재배치하는 일.
- **`Reverse<T>`** — 안에 든 값의 비교를 뒤집는 래퍼.
- **`PeekMut`** — `peek_mut` 이 주는 가드, Drop 될 때 힙을 복원한다.
- **Drop** — 값이 스코프를 벗어날 때 자동으로 불리는 정리 동작.
- **Deref** — `*top` 처럼 가드를 통해 안의 값에 닿게 해 주는 트레이트.
- **`Ord` / `PartialOrd` / `PartialEq` / `Eq`** — 순서와 같음을 정하는 비교 트레이트들.
- **Top-K** — n 개 중 가장 큰(또는 작은) k 개를 고르는 문제.
- **Dijkstra 알고리즘** — 거리가 가장 짧은 노드부터 확정해 나가는 최단 경로 알고리즘.
- **nightly** — 아직 안정화되지 않은 기능을 쓸 수 있는 Rust 빌드.

## 더 들어가면

- 같은 우선순위를 가진 원소가 어떤 순서로 나오는지는 정해져 있지 않다 — 힙은 안정(stable)하지 않다 (확인 필요).
- std 문서는 `push` 의 비용을 「평균 O(1), 최악 O(log n)」처럼 나누어 적는 것으로 안다 (확인 필요).
- 힙 안의 원소를 내부 가변성(`Cell` · `RefCell`)으로 고쳐 순서를 바꾸면 논리 오류가 되며, 그 뒤 동작은 정해지지 않는다(메모리 안전성은 유지) (확인 필요).
- `PeekMut::pop(guard)` 처럼 가드에서 바로 루트를 꺼내는 함수도 있다 (확인 필요).
- `into_vec` 은 정렬하지 않고 내부 배열 그대로 `Vec` 을 돌려준다 (확인 필요).
- Dijkstra 에서는 흔히 `Reverse((거리, 노드))` 처럼 튜플을 감싸 거리 기준 최소 힙을 만든다 (확인 필요).
