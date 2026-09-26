# rust/syntax/38 — `Vec<T>` API와 용량·`retain`·`drain` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(C++ 은 `g++ 13.3.0 -std=c++20`) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ E0502 — 세 줄에 표지, `help:` 는 없다

**출력.**

```text
===== 소스: r38_realloc.rs =====
fn main() {
    let mut v = vec![10, 20, 30];
    let r = &v[0];
    v.push(40);
    println!("{r}");
}
===== rustc --edition 2021 r38_realloc.rs =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> r38_realloc.rs:4:5
  |
3 |     let r = &v[0];
  |              - immutable borrow occurs here
4 |     v.push(40);
  |     ^^^^^^^^^^ mutable borrow occurs here
5 |     println!("{r}");
  |                - immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

**왜 그런가.**

- ★★★ **E0502 — cannot borrow `v` as mutable because it is also borrowed as immutable.** 표지 — `3` 「immutable borrow occurs here」 · `4` 「mutable borrow occurs here」 · `5` 「immutable borrow **later used** here」.
- ★★ **`help:` 가 없다.** 고치는 길은 빌림을 `push` **앞에서 끝내거나**, 참조 대신 **인덱스**를 쥐는 것이다.
- ★ `push` 가 `&mut self` 를 받는데 `r` 이 `&v[0]` 을 **아직 쓴다**(5줄) — 공유 빌림과 가변 빌림이 **겹친다**(10번 주제).

### 2. ★★★ 경고 0 · exit 0 — ASan 을 붙여야 `heap-use-after-free`

**출력.**

```text
===== 소스: r38_realloc.cpp =====
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v{10, 20, 30};
    v.shrink_to_fit();
    int& r = v[0];
    v.push_back(40);
    std::fprintf(stderr, "r = %d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra r38_realloc.cpp -o r38_realloc_plain =====
(exit 0)
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g r38_realloc.cpp -o r38_realloc_asan =====
(exit 0)
===== ./r38_realloc_asan 2>&1 | grep -oE 'AddressSanitizer: [a-z-]+|READ of size [0-9]+' =====
AddressSanitizer: heap-use-after-free
READ of size 4
AddressSanitizer: heap-use-after-free
(exit 1)
```

**왜 그런가.**

- ★★★ **`-Wall -Wextra` 경고 0 · exit 0** — 컴파일러는 **아무 말도 안 한다.**
- ★★★ **ASan — `heap-use-after-free` · `READ of size 4` · exit 1.** `push_back` 이 **새 버퍼로 이사하며 옛 버퍼를 해제**했고, `r` 이 그 해제된 곳을 읽었다.
- ★ **`shrink_to_fit()`** — 용량을 원소 수(3)에 맞춰 **넷째 `push_back` 이 반드시 이사하게** 했다. 용량이 남아 있으면 이사가 없어 ASan 이 조용하다(7번의 C++ 판).
- ★ 평범한 실행 파일(`_plain`)은 **값을 찍고 exit 0** — 그 값은 해제된 메모리라 **흔들려서 싣지 않았다.**

### 3. ★★ 꽉 찬 다음 `push` 에서만 — 첫 용량은 8·4·1, 이 판은 두 배

**출력.**

```text
===== 소스: r38_cap.rs =====
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
===== rustc --edition 2021 r38_cap.rs =====
(exit 0)
===== ./r38_cap =====
Vec<u8>         (size    1)  len->cap  0->0  1->8  9->16  17->32  33->64
Vec<u64>        (size    8)  len->cap  0->0  1->4  5->8  9->16  17->32  33->64
Vec<[u8;2000]>  (size 2000)  len->cap  0->0  1->1  2->2  3->4  5->8  9->16  17->32  33->64
(exit 0)
```

**왜 그런가.**

- ★★ **`Vec<u8>` `0->0 1->8 9->16 17->32 33->64` · `Vec<u64>` `0->0 1->4 5->8 9->16 17->32 33->64` · `Vec<[u8;2000]>` `0->0 1->1 2->2 3->4 5->8 9->16 17->32 33->64`.** 첫 용량이 원소 크기에 따라 **8·4·1** 로 다르다.
- ★★★ **std 가 약속하는 것** — 「**`len == capacity` 일 때만 재할당**」(모든 바뀐 자리가 「꽉 찬 다음 `push`」다) · 「**보고된 용량은 정확**」 · 「**`push` 는 상환 O(1)**」 · 「`Vec::new` 는 할당하지 않는다」(`0->0`).
- ★★★ **이 판의 관찰** — **두 배씩** 늘리는 것과 **첫 용량 8·4·1.** std: 「**특정 성장 전략을 보장하지 않는다**」.

### 4. ★★ 줄이는 것은 `shrink_to_fit` 하나 — 나머지는 `cap 60` 그대로 · 헤더 24

**출력.**

```text
===== 소스: r38_cap_ops.rs =====
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
===== rustc --edition 2021 r38_cap_ops.rs =====
(exit 0)
===== ./r38_cap_ops =====
with_capacity(10)      len   0  cap  10
extend 10              len  10  cap  10
reserve(1)             len  10  cap  20
reserve_exact(50)      len  10  cap  60
split_off(4)           len   4  cap  60
  (the tail)           len   6  cap   6
truncate(1)            len   1  cap  60
clear()                len   0  cap  60
shrink_to_fit()        len   0  cap   0
size_of::<Vec<u64>>() = 24
size_of::<Vec<u8>>()  = 24
size_of::<Option<Vec<u8>>>() = 24
(exit 0)
```

**왜 그런가.**

- ★★ `with_capacity(10)` `0/10` · `extend 10` `10/10` · `reserve(1)` `10/20` · `reserve_exact(50)` `10/60` · **`split_off(4)` `4/60` · `truncate(1)` `1/60` · `clear()` `0/60`** · `shrink_to_fit()` `0/0`. 떼어 낸 꼬리는 `6/6`.
- ★★★ **`split_off`·`truncate`·`clear` 는 전부 `cap 60`** — std 가 셋 다 **명문으로** 「용량에 영향이 없다 / 이전 용량 그대로」라고 적는다. **돌려주는 것은 `shrink_to_fit` 뿐**이다.
- ★ `reserve(1)` 의 20 · `shrink_to_fit` 의 0 · 꼬리의 6 은 **이 판의 관찰**이다(std 는 「**이상**」만 약속한다 — `reserve` 는 「투기적으로 더」, `shrink_to_fit` 은 「여분이 남을 수도」).
- ★ **`size_of` — 24 · 24 · 24** — 원소 타입과 무관하고 `Option` 도 공짜다(11번).

### 5. ★★ E0502 — 표지 둘이 `for` 의 이터레이터를 가리킨다

**출력.**

```text
===== 소스: r38_for_remove.rs =====
fn main() {
    let mut v = vec![1, 2, 3, 4, 5, 6];
    for (i, x) in v.iter().enumerate() {
        if x % 2 == 0 {
            v.remove(i);
        }
    }
    println!("{v:?}");
}
===== rustc --edition 2021 r38_for_remove.rs =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> r38_for_remove.rs:5:13
  |
3 |     for (i, x) in v.iter().enumerate() {
  |                   --------------------
  |                   |
  |                   immutable borrow occurs here
  |                   immutable borrow later used here
4 |         if x % 2 == 0 {
5 |             v.remove(i);
  |             ^^^^^^^^^^^ mutable borrow occurs here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

- ★★★ **E0502.** `v.iter().enumerate()` 가 **`v` 를 빌린 채**(「immutable borrow occurs here」 + 「immutable borrow later used here」 — 둘 다 3줄의 이터레이터) 5줄의 `v.remove(i)` 가 `&mut v` 를 요구했다. **1번과 같은 번호**다.
- ★ `help:` 는 없다 — 처방은 6번의 셋이다.

### 6. ★★ 조건·버림 / 자리·가져감 / 조건·가져감 — `extract_if` 는 1.87.0~

**출력.**

```text
===== 소스: r38_remove_ways.rs =====
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
===== rustc --edition 2021 r38_remove_ways.rs =====
(exit 0)
===== ./r38_remove_ways =====
[1] retain           kept [1, 3, 5]
[2] drain(1..3)      taken [2, 3]  left [1, 4, 5, 6]
[3] extract_if(..)   taken [2, 4, 6]  left [1, 3, 5]
(exit 0)
```

**출력 — 판.**

```text
===== awk '/^Version 1\./{v=$2} /\[.Vec::extract_if.\]/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.87.0 | - [`Vec::extract_if`](https://doc.rust-lang.org/stable/std/vec/struct.Vec.html#method.extract_if)
(exit 0)
```

- ★★ **`[1]` `retain`** — **조건**으로 남기고 지운 것은 **버린다**: `kept [1, 3, 5]`.
- ★★ **`[2]` `drain(1..3)`** — **자리(범위)** 로 떼어 **가져간다**: `taken [2, 3]  left [1, 4, 5, 6]`.
- ★★★ **`[3]` `extract_if(.., 조건)`** — **조건**으로 떼어 **가져간다**: `taken [2, 4, 6]  left [1, 3, 5]`. **1.92.0 stable 에서 컴파일됐고, 1.87.0 부터**다(릴리스 노트).

### 7. ★★ 달라지지 않는다 — 컴파일러는 용량이 아니라 `&mut self` 를 본다

**출력.**

```text
===== 소스: r38_realloc_cap.rs =====
fn main() {
    let mut v: Vec<i32> = Vec::with_capacity(100);
    v.extend([10, 20, 30]);
    let r = &v[0];
    v.push(40);
    println!("{r}");
}
===== rustc --edition 2021 r38_realloc_cap.rs =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> r38_realloc_cap.rs:5:5
  |
4 |     let r = &v[0];
  |              - immutable borrow occurs here
5 |     v.push(40);
  |     ^^^^^^^^^^ mutable borrow occurs here
6 |     println!("{r}");
  |                - immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

**출력 — 같은 판을 C++ 로.**

```text
===== 소스: r38_realloc_cap.cpp =====
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v;
    v.reserve(100);
    v.insert(v.end(), {10, 20, 30});
    int& r = v[0];
    v.push_back(40);
    std::fprintf(stderr, "r = %d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g r38_realloc_cap.cpp -o r38_realloc_cap_asan =====
(exit 0)
===== ./r38_realloc_cap_asan =====
r = 10
(exit 0)
```

- ★★★ **똑같이 E0502** — 용량 100 이라 **이사할 일이 없는데도** 막힌다. 판정 근거는 `push` 의 **시그니처(`&mut self`)** 와 빌림의 **겹침**뿐이다.
- ★★ **C++ 은 이 판에서 ASan 이 조용하고 `r = 10` · exit 0** — 실제로 안전하다. 즉 **C++ 은 용량에 따라 안전·UB 가 갈리고, Rust 는 그 둘을 한꺼번에 거절한다.** 보수적인 대신 사람이 용량을 따질 필요가 없다.

### 8. ★★ 배수는 약속이 아니다 — 약속은 「꽉 찼을 때만 재할당」과 「상환 O(1)」

- ★★★ **약속하지 않는다.** Vec 문서 Guarantees — 「**`Vec` 은 꽉 차서 재할당할 때도, `reserve` 를 부를 때도 특정 성장 전략을 보장하지 않는다.** 지금 전략은 기본적이고 **상수가 아닌 성장 계수**가 바람직할 수도 있다」.
- ★★ **약속하는 것 둘** — **시점**: 「`push`·`insert` 는 **보고된 용량이 충분하면 절대 재할당하지 않고** `len == capacity` 일 때 재할당한다」 · **비용**: 「어떤 전략이든 **O(1) 상환 `push`** 는 보장한다」.
- ★ 3번의 「두 배」는 **이 판의 관찰**이다. 원리(왜 배수 확장이 상환 O(1) 인가)는 [`data-structure/01-dynamic-array`](../../../../../data-structure/01-dynamic-array/2-summary.md) 「동작 — 추가」.

### 9. ★ `[1, 2, 1, 3]` · 정렬 먼저 / `['a', 'e', 'c', 'd']` · std 가 말한다

**출력.**

```text
===== 소스: r38_order_ops.rs =====
fn main() {
    let mut a = vec!['a', 'b', 'c', 'd', 'e'];
    let x = a.remove(1);
    println!("[1] remove(1)      -> {x}  {a:?}");

    let mut b = vec!['a', 'b', 'c', 'd', 'e'];
    let y = b.swap_remove(1);
    println!("[2] swap_remove(1) -> {y}  {b:?}");

    let mut c = vec![1, 1, 2, 1, 1, 3, 3];
    c.dedup();
    println!("[3] dedup          {c:?}");

    let mut d = vec![1, 1, 2, 1, 1, 3, 3];
    d.sort();
    d.dedup();
    println!("[4] sort + dedup   {d:?}");
}
===== rustc --edition 2021 r38_order_ops.rs =====
(exit 0)
===== ./r38_order_ops =====
[1] remove(1)      -> b  ['a', 'c', 'd', 'e']
[2] swap_remove(1) -> b  ['a', 'e', 'c', 'd']
[3] dedup          [1, 2, 1, 3]
[4] sort + dedup   [1, 2, 3]
(exit 0)
```

- ★ **`dedup` → `[1, 2, 1, 3]`** — **이웃한** 중복만. 전부 지우려면 **`sort` 먼저** → `[1, 2, 3]`.
- ★ **`swap_remove(1)` → `['a', 'e', 'c', 'd']`** — 마지막 `e` 가 빈자리로 온다. **O(1)** 은 **std 문서의 문장**(「순서를 지키지 않지만 O(1)」)이다. `remove` 는 「**최악 O(n)**」(같은 문서). **이 문서는 시간을 재지 않았다.**

### 10. ★★ 파이썬은 조용히 건너뛰고, Go 는 조용히 갈라지고, C++ 은 실행해야 보이고, Rust 는 컴파일이 안 된다

- ★★ **Python 18번** — 순회 중 `list.remove` 가 **예외 없이 원소를 건너뛴다**(`['a','c','d','e']`). **Go 06번** — `append` 가 재할당하면 **옛 슬라이스는 옛 배열을 계속 가리키고 공유가 끊긴다**(에러 없음).
- ★★ **에러가 나는 시점으로 줄 세우면**:

| 언어 | 같은 모양의 실수 | 언제 드러나나 |
|---|---|---|
| Rust | 빌린 채 `push` / 순회 중 `remove` | ★★★ **컴파일** — E0502(1·5번) |
| C++ | 참조를 쥔 채 `push_back`(이사가 일어나는 판) | ★★ **실행 + 도구** — ASan `heap-use-after-free`(2번). 도구 없이는 값만 틀린다 |
| Python | 순회 중 `list.remove` | ★ **안 드러난다** — 결과만 틀린다(18번) |
| Go | `append` 재할당 뒤 옛 슬라이스 | ★ **안 드러난다** — 둘이 조용히 갈라진다(06번) |

### 11. ★ 24 · 24 — 「셋」과 「널 아님」은 std 보장, 24 는 이 타깃

- ★ **`size_of::<Vec<u64>>()` = 24 · `size_of::<Option<Vec<u8>>>()` = 24**(4번 블록).
- ★★ **std 보장** — 「`Vec` 은 **(포인터, 용량, 길이) 세 쌍**이고 앞으로도 그렇다. **더도 덜도 아니다**」 · 「포인터는 **절대 널이 아니다** — 널 포인터 최적화가 된다」(그래서 `Option` 이 안 커진다).
- ★ **이 타깃의 결과** — **24**(64비트 포인터·`usize` 셋). **필드 순서**는 「**전혀 정해지지 않았다**」, ABI 도 「안정되지 않았다」.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **재할당 참조** | `r38_realloc` · `r38_realloc_cap` | 2 | **E0502 · E0502**(용량과 무관) |
| ★★ **C++ 대비** | `r38_realloc_cpp`(`-Wall -Wextra` · ASan) · `r38_realloc_cap_cpp` | 2 | **경고 0 → `heap-use-after-free` exit 1** · 용량 넉넉하면 **조용 · exit 0** |
| ★★ **용량 격자** | `r38_cap`(원소 크기 셋) · `r38_cap_ops` | 2 | 첫 용량 **8·4·1**, 이후 두 배 · `truncate`/`clear`/`split_off` 뒤 **`cap 60`** · 헤더 **24** |
| ★★ **순회 중 삭제** | `r38_for_remove` · `r38_remove_ways` | 2 | **E0502** · `retain`/`drain`/`extract_if` 결과 |
| 순서 연산 | `r38_order_ops` | 1 | `swap_remove` 순서 깨짐 · `dedup` 이웃만 |
| `extract_if` 판 | 릴리스 노트 `awk` | 1 | **1.87.0** |
| **안 던진 것** — 속도 · `ExtractIf` 를 끝까지 안 돌리고 버리기 · `try_reserve` · 옛 rustc 판 · 평범한 C++ 실행의 **값** | — | 0 | ★ 「안 던졌다」·「싣지 않았다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| **성장 배수**·**첫 용량**·`reserve` 뒤 수치·`shrink_to_fit` 뒤 0 | ★ **std 가 보장하지 않는다고 명시** — 판이 오르면 바뀔 수 있다 |
| `size_of::<Vec<_>>()` = 24 | ★ 타깃 포인터 폭에 달렸다 |
| ASan 의 판정 문구 | ★ 컴파일러·런타임 판에 달렸다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
