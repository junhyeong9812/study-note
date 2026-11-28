# rust/rust-collections/03 — LinkedList (연결 리스트) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `Some(0)` · `Some(3)` · `[1, 2]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Some(0)
Some(3)
[1, 2]
```

**왜 그런가**
뒤에 1, 2, 3 을 넣고 앞에 0 을 넣으면 리스트는 `[0, 1, 2, 3]` 이다.
`pop_front` 는 맨 앞 0 을 떼어 `Some(0)` 으로, `pop_back` 은 맨 뒤 3 을 떼어 `Some(3)` 으로 돌려준다.
남은 것은 `[1, 2]` 다.
`Option` 으로 감싸 돌려주는 점과 `{:?}` 의 목록 꼴은 2-summary 「동작 방식 (1)」과 「어디서 틀리나 3」에 있다(목록 꼴은 원본 주석 기준).

### 2. `list1` 은 여섯 원소, `list2` 는 비어 있다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
[1, 2, 3, 4, 5, 6]
[]
```

**왜 그런가**
`append` 는 `list2` 의 모든 노드를 `list1` 뒤에 이어 붙인다.
`list2` 는 `&mut` 로 빌려 준 것이라 사라지지 않고 빈 리스트로 남는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 3. 5 부터 1 까지 거꾸로

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
5 4 3 2 1 
```

**왜 그런가**
`collect` 로 `[1, 2, 3, 4, 5]` 가 만들어진다.
노드가 `prev` 도 가진 이중 연결이라 `iter()` 는 `DoubleEndedIterator` 이고, `.rev()` 는 꼬리부터 `prev` 를 따라간다.
`print!("{} ", val)` 이라 값마다 뒤에 공백이 하나 붙는다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 포인터만 이어 붙이고 원소는 옮기지 않기 때문이다

`list1` 의 꼬리 노드와 `list2` 의 머리 노드가 서로를 가리키도록 포인터 몇 개만 고친다.
원소 하나하나를 복사하거나 옮기지 않으니 원소 수와 상관없이 비용이 일정하다.
`Vec` 은 원소를 실제로 옮겨 담아야 해서 비교표에 O(n) 으로 적혀 있다.
근거: 2-summary 「동작 방식 (3)」 · 「문법 — 형태와 규칙」의 비교표.

### 5. 위치를 찾는 데 O(n) 이 들고, 흩어진 노드가 캐시를 못 쓰기 때문이다

끼워 넣는 동작만 O(1) 이고, 그 자리까지 머리부터 한 칸씩 가는 데 O(n) 이 든다.
게다가 노드가 힙에 흩어져 있어 다음 노드를 읽을 때마다 캐시 미스가 나기 쉽고 prefetch 도 어렵다.
`Vec` 은 원소를 미는 일이 O(n) 이어도 붙은 메모리를 다루므로 CPU 캐시 지역성 덕에 실제로는 거의 항상 더 빠르다.
노드마다 포인터를 따로 들어 메모리도 더 쓴다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1 · 2」.

### 6. 커서가 이미 그 위치에 있을 때만이다

비교표의 각주 「\*\* 커서가 위치에 있을 때」가 그 조건이다.
이미 그 자리를 가리키는 커서가 있으면 포인터만 바꿔 O(1) 로 끼워 넣는다.
위치를 처음부터 찾아야 하면 그 탐색에 O(n) 이 든다.
근거: 2-summary 「문법 — 형태와 규칙」의 비교표 각주 · 「어디서 틀리나 1」.

### 7. 바로 꺼낼 수 없고, 머리부터 순회해야 한다

`LinkedList` 에는 `list[i]` 인덱싱 문법이 없다.
원소가 연속 메모리에 있지 않으니 세 번째 원소에 가려면 머리부터 `next` 를 따라 차례로 지나가야 한다 — O(n) 이다.
인덱스 접근이 잦다면 `Vec` 을 쓴다.
근거: 2-summary 「동작 방식 (5)」 · 「문법 — 형태와 규칙」 · 「언제 쓰고 언제 안 쓰나」.

### 8. `VecDeque` — 양쪽 끝 넣기 · 빼기가 O(1) 이면서 배열 기반이라서

큐는 뒤에 넣고 앞에서 빼는 양 끝 작업뿐이라 `LinkedList` 의 강점이 필요 없다.
`VecDeque` 도 양 끝이 O(1) 이고, 노드를 흩어 두지 않는 배열 기반이라 캐시 · 메모리 면에서 낫다.
원본도 큐에는 `VecDeque` 를 권장하고, `while let Some(task) = queue.pop_front()` 로 빌 때까지 꺼내는 꼴을 보인다.
근거: 2-summary 「동작 방식 (6)」 · 「언제 쓰고 언제 안 쓰나」. 배열 기반이라 캐시에 낫다는 부분은 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. `LinkedList` 기능을 훑고 `VecDeque` 큐로 마무리하는 데모

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 빈 리스트, 뒤에 1·2·3, 앞에 0, 전체 출력 | `LinkedList::new()` · `push_back` ×3 · `push_front(0)` · `println!("list: {:?}", list)` |
| 2. 맨 앞 · 맨 뒤 보기, 길이 | `list.front()` · `list.back()` · `list.len()` |
| 3. 양 끝에서 빼고 남은 것 출력 | `list.pop_front()` · `list.pop_back()` · `println!("남은: {:?}", list)` |
| 4. `1..=5` 로 만들어 정방향 · 역방향 출력 | `(1..=5).collect()` · `for val in &list` · `for val in list.iter().rev()` |
| 5. 두 리스트 만들어 합치고 다시 출력 | `list1` · `list2` 의 `collect` · `list1.append(&mut list2)` · `append 후 …` 두 줄 |
| 6. 3 · 9 포함 여부, 비우고 비었는지 출력 | `list1.contains(&3)` · `list1.contains(&9)` · `list1.clear()` · `list1.is_empty()` |
| 7. 비교표와 결론 출력 | `=== 5 ===` · `=== 6 ===` 절의 `println!` 들 |
| 8. `VecDeque<String>` 큐 처리 | `use std::collections::VecDeque` · `push_back(… .to_string())` · `while let Some(task) = queue.pop_front()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-collections/reference/linkedlist.rs`

```rust
// [컬렉션 심화] LinkedList (연결 리스트)
// 설명: LinkedList, 사용 시나리오, Vec과의 비교, 거의 항상 Vec이 나은 이유
// 팁: Rust의 LinkedList는 이중 연결 리스트다. 이론적으로 중간 삽입 O(1)이지만 위치를 찾는데 O(n)이므로 실질적 이점이 적다. CPU 캐시 지역성 때문에 Vec이 거의 항상 더 빠르다. Rust 표준 라이브러리 문서에서도 '대부분 Vec이나 VecDeque를 쓰라'고 안내한다.

// LinkedList: 이중 연결 리스트. 양쪽 끝 push/pop O(1), 인덱싱은 O(n)
use std::collections::LinkedList;

fn main() {
    // === 1. LinkedList 기본 ===
    println!("=== LinkedList 기본 ===");
    let mut list = LinkedList::new();

    // push_back: 뒤에 추가 O(1)
    list.push_back(1);
    list.push_back(2);
    list.push_back(3);
    // push_front: 앞에 추가 O(1) - LinkedList의 강점
    list.push_front(0);
    println!("list: {:?}", list);  // [0, 1, 2, 3]

    // front/back: 양쪽 끝 peek O(1)
    println!("front: {:?}", list.front());  // Some(0)
    println!("back: {:?}", list.back());    // Some(3)
    println!("len: {}", list.len());

    // pop_front/pop_back: 양쪽 끝 제거 O(1)
    println!("pop_front: {:?}", list.pop_front());  // Some(0)
    println!("pop_back: {:?}", list.pop_back());    // Some(3)
    println!("남은: {:?}", list);  // [1, 2]

    // === 2. 순회 ===
    println!("\n=== 순회 ===");
    // collect로 LinkedList 생성
    let list: LinkedList<i32> = (1..=5).collect();
    print!("정방향: ");
    for val in &list {
        print!("{} ", val);
    }
    println!();

    print!("역방향: ");
    // rev: DoubleEndedIterator 활용 (이중 연결이라 양방향 순회 가능)
    for val in list.iter().rev() {
        print!("{} ", val);
    }
    println!();

    // === 3. append: 두 리스트 합치기 O(1) ===
    println!("\n=== append (O(1) 합치기) ===");
    let mut list1: LinkedList<i32> = (1..=3).collect();
    let mut list2: LinkedList<i32> = (4..=6).collect();
    println!("list1: {:?}", list1);
    println!("list2: {:?}", list2);

    // append: 포인터만 연결하므로 O(1) - LinkedList의 큰 장점
    list1.append(&mut list2);  // list2의 모든 노드를 list1 뒤에 O(1)
    println!("append 후 list1: {:?}", list1);
    println!("append 후 list2: {:?}", list2);  // 비어있음

    // === 4. contains, clear ===
    println!("\n=== contains, clear ===");
    // contains: O(n) 선형 탐색
    println!("contains(3): {}", list1.contains(&3));
    println!("contains(9): {}", list1.contains(&9));
    list1.clear();
    println!("clear 후: {:?}, is_empty: {}", list1, list1.is_empty());

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
    // amortized: 평균 O(1)이지만 가끔 재할당 발생
    println!("* amortized, ** 커서가 위치에 있을 때");

    // === 6. 결론: 거의 항상 Vec이 낫다 ===
    println!("\n=== 언제 LinkedList를 쓸까? ===");
    println!("거의 쓰지 않는다! 이유:");
    // 캐시 미스: 노드가 흩어져 있어 prefetch 어려움
    println!("  1. 캐시 미스: 노드가 힙에 흩어져 CPU 캐시 효율 나쁨");
    // 메모리 오버헤드: 노드마다 prev/next 포인터로 16~24바이트 추가
    println!("  2. 메모리 오버헤드: 노드마다 prev/next 포인터 (16바이트)");
    println!("  3. 인덱싱 불가: O(n) 순회 필요");
    println!("  4. Vec의 push_front가 O(n)이어도 실제로 더 빠른 경우 많음");
    println!();
    println!("LinkedList가 적합할 수 있는 드문 경우:");
    println!("  - 리스트 중간에서 대량의 삽입/삭제가 필요할 때");
    println!("  - 두 리스트를 O(1)으로 합쳐야 할 때 (append)");
    println!("  - 원소 수가 많고 랜덤 접근이 불필요할 때");
    println!();
    // 대안: 양쪽 끝 작업은 VecDeque, 그 외는 Vec
    println!("대안: VecDeque (양쪽 끝 O(1)), Vec (대부분의 경우)");

    // === 7. 실제 대안 패턴 ===
    println!("\n=== 실제 대안 패턴 ===");
    // VecDeque로 큐 구현 - LinkedList 대신 권장됨
    use std::collections::VecDeque;
    let mut queue: VecDeque<String> = VecDeque::new();
    queue.push_back("작업1".to_string());
    queue.push_back("작업2".to_string());
    while let Some(task) = queue.pop_front() {
        println!("  처리: {}", task);
    }
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- `front` · `back` 은 `Option<&T>`, `pop_front` · `pop_back` 은 `Option<T>` 를 돌려주므로 `{:?}` 로 찍는다.
- 순회 절에서 `let list` 를 다시 선언해 앞의 `list` 를 가린다(섀도잉) — 새 리스트는 바꾸지 않으므로 `mut` 이 없다.
- 역방향은 이중 연결 덕분에 `iter().rev()` 한 번이면 된다.
- `append` 는 `&mut list2` 를 받으므로 `list2` 도 `mut` 이어야 하고, 합친 뒤 `list2` 는 빈 채로 남는다.
- `contains` 에는 값의 참조(`&3`)를 넘긴다.
- 큐는 `VecDeque` 로 만들고, `while let` 으로 `None` 이 나올 때까지 꺼낸다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
