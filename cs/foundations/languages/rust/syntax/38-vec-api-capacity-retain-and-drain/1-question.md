# rust/syntax/38 — `Vec<T>` API와 용량·`retain`·`drain` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. C++ 대비는 `g++ -std=c++20`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **`Vec` 을 고치는 호출을 보면 먼저 물어라** — 「**지금 누가 이 `Vec` 의 원소를 빌리고 있나**」와 「**이 수치는 std 가 약속한 것인가**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 원소를 쥔 채 `push` (예측)

```rust
// r38_realloc.rs
fn main() {
    let mut v = vec![10, 20, 30];
    let r = &v[0];
    v.push(40);
    println!("{r}");
}
```

- 컴파일되는가? 에러라면 번호와, 진단이 **어느 세 줄**에 무엇이라고 표지를 붙이나?
- ★ `help:` 가 있는가?

### 2. ★★★ 같은 한 줄을 C++ 로 (예측)

```cpp
// r38_realloc.cpp
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30};
    v.shrink_to_fit();
    int& r = v[0];
    v.push_back(40);
    std::fprintf(stderr, "r = %d\n", r);
}
```

- `g++ -std=c++20 -Wall -Wextra` 로 컴파일하면 경고는 몇 개이고 종료 코드는?
- ★★ `-fsanitize=address` 를 붙여 실행하면 무엇이 보고되고 종료 코드는? `shrink_to_fit()` 줄은 왜 넣었을까?

### 3. ★★ `push` 를 하나씩 — 용량이 바뀐 자리 (예측)

```rust
// r38_cap.rs
// push 를 하나씩 하며 capacity() 가 바뀐 자리만 찍는다 — 원소 크기 셋
fn trace<T: Clone>(name: &str, x: T) {
    let mut v: Vec<T> = Vec::new();
    let mut last = v.capacity();
    let mut marks = vec![format!("{}->{}", v.len(), last)];
    for _ in 0..40 {
        v.push(x.clone());
        if v.capacity() != last {
            last = v.capacity();
            marks.push(format!("{}->{}", v.len(), last));
        }
    }
    println!("{name:<15} (size {:>4})  len->cap  {}", std::mem::size_of::<T>(), marks.join("  "));
}

fn main() {
    trace("Vec<u8>", 0u8);
    trace("Vec<u64>", 0u64);
    trace("Vec<[u8;2000]>", [0u8; 2000]);
}
```

- 세 줄 각각의 `len->cap` 기록은? ★ 첫 용량이 원소 크기에 따라 다른가?
- ★★ 이 수치들 중 **std 가 약속하는 것**과 **이 판의 관찰**을 가르면?

### 4. ★★ 용량에 손대는 연산들 (예측)

```rust
// r38_cap_ops.rs
// 용량에 손대는 연산들 — 차례로
fn show(tag: &str, v: &Vec<u64>) {
    println!("{tag:<22} len {:>3}  cap {:>3}", v.len(), v.capacity());
}

fn main() {
    let mut v: Vec<u64> = Vec::with_capacity(10);
    show("with_capacity(10)", &v);
    v.extend(0..10);
    show("extend 10", &v);
    v.reserve(1);
    show("reserve(1)", &v);
    v.reserve_exact(50);
    show("reserve_exact(50)", &v);
    let tail = v.split_off(4);
    show("split_off(4)", &v);
    println!("{:<22} len {:>3}  cap {:>3}", "  (the tail)", tail.len(), tail.capacity());
    v.truncate(1);
    show("truncate(1)", &v);
    v.clear();
    show("clear()", &v);
    v.shrink_to_fit();
    show("shrink_to_fit()", &v);
    println!("size_of::<Vec<u64>>() = {}", std::mem::size_of::<Vec<u64>>());
    println!("size_of::<Vec<u8>>()  = {}", std::mem::size_of::<Vec<u8>>());
    println!("size_of::<Option<Vec<u8>>>() = {}", std::mem::size_of::<Option<Vec<u8>>>());
}
```

- 아홉 줄의 `len`·`cap` 과 `size_of` 세 줄은?
- ★★ `split_off(4)` · `truncate(1)` · `clear()` 뒤의 `cap` 은 각각 얼마인가?

### 5. ★★ 돌면서 짝수를 지우기 (예측)

```rust
// r38_for_remove.rs
fn main() {
    let mut v = vec![1, 2, 3, 4, 5, 6];
    for (i, x) in v.iter().enumerate() {
        if x % 2 == 0 {
            v.remove(i);
        }
    }
    println!("{v:?}");
}
```

- 컴파일되는가? 에러라면 번호와, 진단의 표지가 가리키는 곳은?

### 6. ★★ 지우는 셋 (예측)

```rust
// r38_remove_ways.rs
// 순회 중 삭제를 안전하게 — 셋
fn main() {
    let mut a = vec![1, 2, 3, 4, 5, 6];
    a.retain(|x| x % 2 != 0);
    println!("[1] retain           kept {a:?}");

    let mut b = vec![1, 2, 3, 4, 5, 6];
    let taken: Vec<i32> = b.drain(1..3).collect();
    println!("[2] drain(1..3)      taken {taken:?}  left {b:?}");

    let mut c = vec![1, 2, 3, 4, 5, 6];
    let evens: Vec<i32> = c.extract_if(.., |x| *x % 2 == 0).collect();
    println!("[3] extract_if(..)   taken {evens:?}  left {c:?}");
}
```

- 세 줄의 출력은? `[1]`·`[2]`·`[3]` 은 각각 **무엇으로**(조건 · 자리) 지우고, 지운 것을 **버리나 가져가나**?
- ★ `extract_if` 는 1.92.0 stable 에서 되는가? 된다면 몇 판부터인가?

### 7. ★★ 용량이 넉넉하다면 (경계)

- 1번 소스의 `vec![10, 20, 30]` 을 `Vec::with_capacity(100)` 에 셋을 넣은 것으로 바꾸면 — `push` 가 **이사할 일이 없는데도** 1번의 결과가 달라지나? 컴파일러는 무엇을 보고 판정하나?

### 8. ★★ 몇 배로 늘리나 (왜)

- `Vec` 의 성장 배수는 **std 가 약속하는가**? 약속하는 것이 있다면 무엇과 무엇인가(재할당 시점 · 비용)?

### 9. ★ 이웃과 끝 (경계)

- `vec![1, 1, 2, 1, 1, 3, 3]` 에 `dedup()` 을 부르면? 중복을 전부 지우려면?
- `vec!['a', 'b', 'c', 'd', 'e']` 에 `swap_remove(1)` 을 부르면 남는 순서는? 그 복잡도는 **누가** 말하나?

### 10. ★★ 세 언어의 순회 중 삭제·재할당 (연결)

- Python 갈래의 [18번](../../../python/syntax/18-loop-control-and-else/)은 순회 중 `list.remove` 에서 **무엇이 일어난다고** 쟀나? Go 갈래의 [06번](../../../go/syntax/06-len-cap-and-append-reallocation/)은 `append` 재할당 뒤 **옛 슬라이스**가 어떻게 된다고 했나?
- ★ 그 둘과 C++ · Rust 를 「**에러가 나는 시점**」(컴파일 · 실행 · 안 남)으로 줄 세우면?

### 11. ★ `Vec` 헤더 (경계)

- `size_of::<Vec<u64>>()` 와 `size_of::<Option<Vec<u8>>>()` 는? 그중 **std 가 보장하는 것**은 무엇이고 **이 타깃의 결과**는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
