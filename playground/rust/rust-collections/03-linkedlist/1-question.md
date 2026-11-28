# rust/rust-collections/03 — LinkedList (연결 리스트) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 앞뒤로 넣은 뒤 양 끝에서 하나씩 빼면 (예측)

```rust
// 질문용 발췌
let mut list = LinkedList::new();
list.push_back(1);
list.push_back(2);
list.push_back(3);
list.push_front(0);
println!("{:?}", list.pop_front());
println!("{:?}", list.pop_back());
println!("{:?}", list);
```

- 세 줄에 각각 무엇이 찍힐까?

### 2. `append` 뒤의 두 리스트 (예측)

```rust
// 질문용 발췌
let mut list1: LinkedList<i32> = (1..=3).collect();
let mut list2: LinkedList<i32> = (4..=6).collect();
list1.append(&mut list2);
println!("{:?}", list1);
println!("{:?}", list2);
```

- `list1` 과 `list2` 는 각각 어떻게 찍힐까?

### 3. `iter().rev()` 로 훑기 (예측)

```rust
// 질문용 발췌
let list: LinkedList<i32> = (1..=5).collect();
for val in list.iter().rev() {
    print!("{} ", val);
}
```

- 어떤 순서로 찍힐까?

### 4. `LinkedList` 의 `append` 가 O(1) 인 이유 (왜)
- `LinkedList` 는 원소가 몇 개든 합치는 비용이 왜 일정한가?

### 5. 이론상 O(1) 중간 삽입이 실제로는 이점이 적은 이유 (왜)
- 끼워 넣기가 O(1) 인데도 `Vec` 이 거의 항상 더 빠른 까닭은 무엇인가?

### 6. 「중간 삽입 O(1)」이 성립하는 조건 (경계)
- 비교표의 「O(1)\*\*」는 어떤 조건에서만 맞는 말인가?

### 7. `LinkedList` 에서 세 번째 원소 얻기 (경계)
- `list[2]` 처럼 바로 꺼낼 수 있는가, 없다면 무엇을 해야 하나?

### 8. 작업 대기열에 맞는 컬렉션 (연결)
- 뒤에 넣고 앞에서 빼는 큐를 만들 때 `LinkedList` 대신 무엇을, 왜 쓰나?

## 실습

### 실습 1. `LinkedList` 기능을 훑고 `VecDeque` 큐로 마무리하는 데모

**만들 것** — `LinkedList` 의 넣기 · 보기 · 빼기 · 순회 · 합치기 · 탐색 · 비우기를 차례로 보여 주고, `Vec` 과의 비교표와 결론을 찍은 뒤 `VecDeque` 로 작업 큐를 처리하는 프로그램.

**요구 조건**

1. 1단계 — 빈 `LinkedList` 를 만들어 뒤에 1, 2, 3 을 넣고 앞에 0 을 넣은 뒤 리스트 전체를 `{:?}` 로 찍는다.
2. 1단계 — 맨 앞 값, 맨 뒤 값(꺼내지 않고 보기)과 길이를 찍는다.
3. 1단계 — 앞에서 하나, 뒤에서 하나를 빼서 그 결과를 찍고, 남은 리스트를 찍는다.
4. 2단계 — 범위 `1..=5` 를 `collect` 해 `LinkedList<i32>` 를 만들고, 정방향으로 한 줄, 역방향으로 한 줄 값을 찍는다.
5. 3단계 — `1..=3` 과 `4..=6` 으로 두 리스트를 만들어 각각 찍고, 둘째를 첫째 뒤에 O(1) 로 합친 다음 두 리스트를 다시 찍는다.
6. 4단계 — 합친 리스트에 3 과 9 가 있는지 찍고, 리스트를 비운 뒤 리스트와 비었는지 여부를 한 줄에 찍는다.
7. 5단계 — `Vec` 과 `LinkedList` 의 비교표와 「언제 `LinkedList` 를 쓸까」 결론 문장을 찍는다(시작 코드에 이미 있다).
8. 6단계 — `VecDeque<String>` 큐에 "작업1", "작업2" 를 뒤로 넣고, 큐가 빌 때까지 앞에서 꺼내며 `처리: …` 를 찍는다.

**시작 코드**

```rust
use std::collections::LinkedList;

fn main() {
    // === 1. LinkedList 기본 ===
    println!("=== LinkedList 기본 ===");
    // TODO: 빈 LinkedList 를 만든다
    // TODO: 뒤에 1, 2, 3 을 넣고 앞에 0 을 넣는다
    // TODO: 리스트 출력 → "list: ..."
    // TODO: 맨 앞 · 맨 뒤 보기, 길이 출력 → "front: ...", "back: ...", "len: ..."
    // TODO: 앞 · 뒤에서 하나씩 빼서 출력 → "pop_front: ...", "pop_back: ..."
    // TODO: 남은 리스트 출력 → "남은: ..."

    // === 2. 순회 ===
    println!("\n=== 순회 ===");
    // TODO: (1..=5) 를 collect 해 LinkedList<i32> 를 만든다
    print!("정방향: ");
    // TODO: 정방향 순회 출력
    println!();

    print!("역방향: ");
    // TODO: 역방향 순회 출력
    println!();

    // === 3. append: 두 리스트 합치기 O(1) ===
    println!("\n=== append (O(1) 합치기) ===");
    // TODO: list1 = 1..=3, list2 = 4..=6 을 만들고 각각 출력
    // TODO: list2 를 list1 뒤에 합친다
    // TODO: "append 후 list1: ...", "append 후 list2: ..." 출력

    // === 4. contains, clear ===
    println!("\n=== contains, clear ===");
    // TODO: "contains(3): ...", "contains(9): ..." 출력
    // TODO: 비운 뒤 "clear 후: ..., is_empty: ..." 출력

    // === 5. Vec vs LinkedList 성능 비교 ===
    println!("\n=== Vec vs LinkedList 비교 ===");
    println!("┌──────────────────┬──────────┬─────────────┐");
    println!("│ 연산             │ Vec      │ LinkedList  │");
    println!("├──────────────────┼──────────┼─────────────┤");
    println!("│ push_back        │ O(1)*    │ O(1)        │");
    println!("│ push_front       │ O(n)     │ O(1)        │");
    println!("│ 인덱스 접근      │ O(1)     │ O(n)        │");
    println!("│ 중간 삽입        │ O(n)     │ O(1)**      │");
    println!("│ 캐시 친화성      │ 매우 좋음│ 나쁨        │");
    println!("│ 메모리 오버헤드  │ 낮음     │ 높음        │");
    println!("│ append           │ O(n)     │ O(1)        │");
    println!("│ split            │ O(n)     │ O(n)        │");
    println!("└──────────────────┴──────────┴─────────────┘");
    println!("* amortized, ** 커서가 위치에 있을 때");

    // === 6. 결론: 거의 항상 Vec이 낫다 ===
    println!("\n=== 언제 LinkedList를 쓸까? ===");
    println!("거의 쓰지 않는다! 이유:");
    println!("  1. 캐시 미스: 노드가 힙에 흩어져 CPU 캐시 효율 나쁨");
    println!("  2. 메모리 오버헤드: 노드마다 prev/next 포인터 (16바이트)");
    println!("  3. 인덱싱 불가: O(n) 순회 필요");
    println!("  4. Vec의 push_front가 O(n)이어도 실제로 더 빠른 경우 많음");
    println!();
    println!("LinkedList가 적합할 수 있는 드문 경우:");
    println!("  - 리스트 중간에서 대량의 삽입/삭제가 필요할 때");
    println!("  - 두 리스트를 O(1)으로 합쳐야 할 때 (append)");
    println!("  - 원소 수가 많고 랜덤 접근이 불필요할 때");
    println!();
    println!("대안: VecDeque (양쪽 끝 O(1)), Vec (대부분의 경우)");

    // === 7. 실제 대안 패턴 ===
    println!("\n=== 실제 대안 패턴 ===");
    // TODO: VecDeque 를 가져와 VecDeque<String> 큐를 만든다
    // TODO: "작업1", "작업2" 를 뒤로 넣는다
    // TODO: 큐가 빌 때까지 앞에서 꺼내며 "  처리: ..." 출력
}
```

**확인 방법** — `rustc linkedlist.rs && ./linkedlist`(또는 `cargo run`)로 돌려, 각 절 제목 아래에 요구 조건의 값들이 차례로 찍히고 마지막에 `처리: 작업1`, `처리: 작업2` 가 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
