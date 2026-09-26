# rust/syntax/38 — `Vec<T>` API와 용량·`retain`·`drain` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `Vec`](https://doc.rust-lang.org/std/vec/struct.Vec.html)(Guarantees 절 · `swap_remove`·`remove`·`retain`·`drain`·`extract_if`·`dedup`·`truncate`·`clear`·`split_off`·`reserve`·`reserve_exact`·`shrink_to_fit`) ·
> [std — `std::collections` 모듈 문서](https://doc.rust-lang.org/std/collections/index.html)(Performance · Cost of Collection Operations).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다. C++ 대비는 `g++ 13.3.0`(`-std=c++20`, AddressSanitizer).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> ★★★ **이 문서는 속도를 한 번도 재지 않았다.** 센 것은 **`capacity()`·`len()`·`size_of`** 뿐이고, 복잡도(`O(1)`·`O(n)`)는 **std 문서의 문장을 인용**했을 뿐이다.
> **버전** — `Vec::extract_if` 는 **1.87.0** 부터 안정이다(아래 블록). 나머지 메서드는 1.0 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== g++ --version | head -1 =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
===== node --version =====
v18.19.1
(exit 0)
```

```text
===== awk '/^Version 1\./{v=$2} /\[.Vec::extract_if.\]/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.87.0 | - [`Vec::extract_if`](https://doc.rust-lang.org/stable/std/vec/struct.Vec.html#method.extract_if)
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | **E0502** 두 블록의 번호·제목·`파일:줄:칸` | 같은 rustc 판에서 고정이다. **이 주제의 첫째 본체** |
| ★★ **판이 바뀌면 바뀔 수 있다** | **용량의 구체적 수치**(`0 → 4 → 8 → 16 …`, 첫 용량 8·4·1, `reserve(1)` 뒤 20) | ★ **std 가 성장 전략을 보장하지 않는다**(§구현 세부). **같은 판에서는 한 글자도 안 흔들린다** — 그래서 싣되 「이 판의 관찰」로 읽는다 |
| 안 흔들린다 | `truncate`·`clear`·`split_off` 뒤 **용량이 그대로인 것** · `with_capacity(10)` 이 10 · `reserve_exact(50)` 뒤 `len + 50` 이상 | ★ **std 문서의 약속**이다(「has no effect on the allocated capacity」 등) |
| 안 흔들린다 | `size_of::<Vec<_>>()` = 24 | 같은 판·같은 타깃에서 고정. **「셋」은 std 보장, 24 는 이 타깃의 결과**(§구현 세부) |
| 안 흔들린다 | `retain`·`drain`·`extract_if`·`swap_remove`·`dedup` 의 **결과 순서** | 결정적 입력 · 문서가 정한 동작 |
| ★ **흔들려서 싣지 않았다** | C++ 판에서 **해제된 메모리를 읽어 찍힌 값** | UB 의 결과라 실행마다 다를 수 있다 — **ASan 의 판정 문구만** 필터로 뽑아 실었다((1)) |
| 안 흔들린다 | ASan 의 `heap-use-after-free` · `READ of size 4` · 종료 코드 1 | 같은 컴파일러·같은 소스에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼다(제출 전 재대조 — 「3-answer」의 실행 검증 표).

## 한눈에 — 쉽게 말하면

**`Vec` 은 「칸 수를 넉넉히 잡아 둔 사물함」이다. 사물함이 꽉 차면 **더 큰 사물함을 새로 얻어 짐을 전부 옮긴다.**
그 순간 옛 사물함 번호를 적어 둔 쪽지는 **빈 곳을 가리키게 된다.** C++ 은 그 쪽지를 들고 가게 두고, Rust 는 **쪽지를 든 채로는 이사를 못 하게** 막는다.**

| 비유 | 실체 |
|---|---|
| 「**사물함 칸 수 / 짐 개수**」 | **`capacity()` / `len()`** — 칸이 남아 있으면 `push` 가 **이사하지 않는다**(std 보장)((2)) |
| 「**꽉 차면 더 큰 사물함으로 이사**」 | **재할당** — 이 판에서는 `4 → 8 → 16 → 32 …`. ★ **몇 배로 늘릴지는 std 가 약속하지 않는다**((2)) |
| 「**옛 사물함 번호를 적은 쪽지**」 | **`let r = &v[0]`** — 원소를 가리키는 참조((1)) |
| 「**쪽지를 든 채 이사 금지**」 | ★★★ **E0502** — 빌림이 살아 있는 동안 `v.push` 는 컴파일이 안 된다((1)) |
| 「**C++ 은 쪽지를 들고 가게 둔다**」 | ★★ `g++ -Wall -Wextra` **경고 0 · exit 0** — ASan 을 붙여야 **heap-use-after-free**((1)) |
| 「**짐을 빼도 사물함은 안 줄인다**」 | `truncate`·`clear`·`split_off` — **용량 그대로**. 줄이려면 `shrink_to_fit`((3)) |
| 「**돌면서 빼기는 관리인에게 맡긴다**」 | ★★ **순회 중 삭제** — `for` 안의 `remove` 는 E0502, **`retain`·`drain`·`extract_if`** 로((4)) |

- ★★★ **판정은 한 줄이다 — 「`&v[i]` 를 쥐고 있는 동안 `v` 의 길이를 바꾸는 호출은 전부 막힌다.」**
  재할당이 **실제로 일어날지**(용량이 남았는지)는 따지지 않는다 — **`&mut self` 를 받는다는 것만으로** 막힌다((1)).

```text
   ★ 같은 한 줄 — 두 언어 ((1)의 블록 그대로)

   int& r = v[0];  v.push_back(40);  print(r)          let r = &v[0];  v.push(40);  println!("{r}")

   g++ -Wall -Wextra      경고 0 · exit 0               rustc                ✘ E0502  (exit 1)
   ./plain                값을 찍고 exit 0 (값은 싣지 않았다)                   ─ 실행 파일이 안 생긴다
   ./asan                 heap-use-after-free · exit 1

   ┌ 옛 버퍼 [10|20|30] ← r 이 가리킴 ┐        빌림(&v[0]) 살아 있음 ──────────── println!("{r}")
   └──── push_back → 새 버퍼로 이사 ──┘ 해제         v.push(40) 는 &mut v 가 필요 ─▶ 두 빌림이 겹친다 ─▶ E0502
```

> **용량(capacity)** — 다시 할당하지 않고 담을 수 있는 원소 수. `len() <= capacity()` 가 늘 참이다.\
> 예: `Vec::with_capacity(10)` 은 `len 0 · cap 10` 이다((3)).

> **재할당(reallocation)** — 칸이 모자라면 **더 큰 버퍼를 얻어 원소를 옮기고 옛 버퍼를 돌려주는 것.** 옛 버퍼를 가리키던 포인터는 **댕글링**이 된다.\
> 예: 이 판에서 `Vec<u64>` 는 `len 5` 가 되는 `push` 에서 `cap 4 → 8` 로 재할당했다((2)).

> **E0502** — 「`v` 를 불변으로 빌린 채 가변으로 빌릴 수 없다」. [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 빌림 규칙(공유 XOR 가변)이 `Vec` 에서 나타난 꼴이다.\
> 예: `let r = &v[0]; v.push(1); use(r)`.

## 이 주제가 답하려는 질문

1. ★★★ **재할당이 참조를 무효화하는 상황을 Rust 는 어떻게 다루나** — C++ 는 무엇을 하고 Rust 컴파일러는 무엇이라고 말하나((1)).
2. ★★ **용량은 언제 바뀌고, 무엇이 그것을 보장하나** — `push` · `with_capacity` · `reserve` · `truncate` · `clear` · `shrink_to_fit`((2)·(3)).
3. ★★ **순회 중 삭제를 안전하게 하려면 무엇을 고르나** — `retain` · `drain` · `extract_if` · `swap_remove`((4)·(5)).

★ **선행** — [**37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)의 **`for x in &v`**(순회가 `v` 를 **빌린다**) — 그래서 (4)의 순회 중 `remove` 가 막힌다.
[**10번 주제**](../10-borrowing-and-aliasing-rules/)의 E0502 가 이 주제의 첫째 진단이다.
★ **정본 경계** — **동적 배열의 증폭·상환(amortized) 분석**은 [`data-structure/01-dynamic-array`](../../../../../data-structure/01-dynamic-array/2-summary.md) 의 「**동작 — 추가**」 절(「꽉 찼을 때 — 2배 배열을 만들어 전부 복사」 · 「상환 O(1)」)이 정본이다.
여기는 **그 원리가 `Vec` API 에서 어떻게 보이나**(무엇이 보장되고 무엇이 관찰인가)와 **재할당이 참조에 미치는 영향**만 쓴다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① E0502 와 ② 용량 격자다

★★★ **본체 창 — ① 컴파일러에게 「재할당이 참조를 무효화한다」를 말하게 하는 E0502** 와 **② `capacity()` 를 찍는 용량 격자.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **컴파일러 진단 E0502** | 빌림이 살아 있는 동안 **길이를 바꾸는 호출이 막히나**((1)·(4)) | ★ **본체** |
| ② ★★ **`capacity()`·`len()` 로그** | 재할당이 **어느 `push` 에서** 일어나나 · 어떤 연산이 용량을 **바꾸고 안 바꾸나**((2)·(3)) | ★ **본체** |
| ③ ★★ **C++ + AddressSanitizer** | 같은 한 줄이 C++ 에서 **컴파일은 되고 실행에서** 무엇이 되나((1)) | 대비로 쓴다 |
| ④ **결과 출력** | `retain`·`drain`·`extract_if`·`swap_remove`·`dedup` 이 **무엇을 남기나**((4)·(5)) | 쓴다 |
| ⑤ **`size_of`** | `Vec` 헤더가 몇 바이트인가((3)) | 쓴다 |
| 실행 시간 | 「`swap_remove` 가 `remove` 보다 빠르다」·「`retain` 이 빠르다」 | ★ **부적용 — 재지 않는다.** 복잡도는 **std 문서 인용**으로만 적는다((5)) |
| 재할당 **횟수의 계측**(할당기 훅) | — | ★ **쓰지 않았다** — `capacity()` 가 바뀐 자리가 곧 재할당 자리다(std 보장 — 「reported capacity is completely accurate」) |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「재할당 뒤 옛 참조는 어떻게 되나」를 Rust 에서는 **실행으로 물을 수가 없다** — 컴파일이 안 되기 때문이다.
그래서 **같은 질문을 C++ + ASan 창**으로 물었다. ★ ASan 은 **메모리만** 본다 — 「읽은 값이 무엇이었나」는 UB 라 답이 아니다(값은 싣지 않았다).

### (1) ★★★ 재할당이 참조를 무효화한다 — 컴파일러가 말하게

**언제 쓰나** — `Vec` 원소를 가리키는 참조를 쥔 채로 **`push`·`insert`·`extend`** 를 하고 싶어질 때.

```rust
// r38_realloc.rs
fn main() {
    let mut v = vec![10, 20, 30];
    let r = &v[0];
    v.push(40);
    println!("{r}");
}
```

```text
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

- ★★★ **E0502 — cannot borrow `v` as mutable because it is also borrowed as immutable.** 세 표지가 **줄마다** 붙는다 —
  `3 | let r = &v[0];` 「immutable borrow occurs here」 · `4 | v.push(40);` 「mutable borrow occurs here」 · `5 | println!("{r}")` 「immutable borrow **later used** here」.
- ★★ **`help:` 가 없다** — 이 자리에는 기계적 처방이 없다. 고치는 길은 **빌림을 먼저 끝내거나**(`println!` 을 `push` 앞으로) **인덱스를 쥐는 것**(`let i = 0; v.push(40); v[i]`)이다.
- ★★ **재할당이 「실제로 일어날지」는 보는가?** — 용량을 100 으로 잡아 **`push` 가 이사할 일이 없게** 하고 다시 던지면:

```rust
// r38_realloc_cap.rs
fn main() {
    let mut v: Vec<i32> = Vec::with_capacity(100);
    v.extend([10, 20, 30]);
    let r = &v[0];
    v.push(40);
    println!("{r}");
}
```

```text
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

- ★★★ **똑같이 E0502 다** — 표지 세 줄도 같다(줄 번호만 한 칸 밀렸다). 컴파일러는 **용량을 보지 않는다.** `push` 가 **`&mut self`** 를 받는다는 **시그니처만으로** 판정한다([**10번 주제**](../10-borrowing-and-aliasing-rules/)의 「공유 XOR 가변」).
  C++ 로 같은 판(`reserve(100)`)을 ASan 에 걸면 **아무것도 안 잡힌다**(아래 (1)의 C++ 둘째 블록) — 그 「실제로는 안전한 경우」까지 Rust 는 **거절한다.** 보수적인 대신 **용량을 따질 필요가 없다.**

**C++ 로 같은 한 줄.**

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

```text
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

- ★★★ **`g++ -Wall -Wextra` 경고 0 · exit 0** — 컴파일러가 **아무 말도 안 했다.** 평범한 실행 파일(`_plain`)도 **값을 찍고 exit 0** 으로 끝났다(찍힌 값은 **해제된 메모리를 읽은 것**이라 흔들린다 — 싣지 않았다).
- ★★★ **ASan 을 붙이면 `heap-use-after-free` · `READ of size 4` · exit 1** — `push_back` 이 새 버퍼로 이사하며 옛 버퍼를 **해제**했고, `r` 은 **그 해제된 곳**을 읽었다.
  (`shrink_to_fit()` 으로 용량을 3 에 맞춰 두어 **이사가 반드시 일어나게** 했다.)
**용량을 넉넉히 잡은 C++ 판.**

```cpp
// r38_realloc_cap.cpp
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
```

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g r38_realloc_cap.cpp -o r38_realloc_cap_asan =====
(exit 0)
===== ./r38_realloc_cap_asan =====
r = 10
(exit 0)
```

- ★★ **ASan 이 조용하고 `r = 10` · exit 0** — 이사가 없으니 `r` 이 가리키는 버퍼가 **살아 있다.** C++ 에서는 **같은 한 줄이 용량에 따라 안전하기도, UB 이기도** 하다. 그 갈림을 **사람이 따져야** 한다.
- ★★ **같은 모양의 버그가 C++ 에서는 「실행해 봐야(그리고 도구를 붙여야) 보이는」 UB 이고, Rust 에서는 「컴파일이 안 되는」 에러다.**
  C++ 표준은 재할당 때 참조·반복자가 **무효가 된다**고 적는다 — 이 문서는 표준 원문을 열지 않았고, 근거는 **위 ASan 블록**이다. `vector` 의 무효화 규칙 정본은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **41번**(순차 컨테이너 선택)이다.
- ★ Go 는 또 다르다 — `append` 가 재할당하면 **옛 슬라이스는 옛 배열을 그대로 가리키고 공유가 끊긴다**(에러도 UB 도 아니고 **조용히 갈라진다**). Go 갈래의 [**06번**](../../../go/syntax/06-len-cap-and-append-reallocation/)이 `cap` 으로 그것을 쟀다.

### (2) ★★ 용량 격자 — `push` 를 하나씩 하며 `capacity()` 가 바뀐 자리

**언제 쓰나** — 「`push` 가 언제 이사하나」를 **보장과 관찰로 갈라** 알고 싶을 때.

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

```text
===== rustc --edition 2021 r38_cap.rs =====
(exit 0)
===== ./r38_cap =====
Vec<u8>         (size    1)  len->cap  0->0  1->8  9->16  17->32  33->64
Vec<u64>        (size    8)  len->cap  0->0  1->4  5->8  9->16  17->32  33->64
Vec<[u8;2000]>  (size 2000)  len->cap  0->0  1->1  2->2  3->4  5->8  9->16  17->32  33->64
(exit 0)
```

- ★★ **세 원소 크기 모두 「꽉 찬 다음 `push`」에서만 바뀌었다** — `Vec<u64>` 는 `len 5`(용량 4 가 꽉 찬 다음) · `9` · `17` · `33`. std 의 약속 그대로다 —
  「**`push` 와 `insert` 는 보고된 용량이 충분하면 절대 (재)할당하지 않고, `len == capacity` 일 때 (재)할당한다.** 보고된 용량은 **완전히 정확**하다」(Vec 문서 Guarantees).
- ★★★ **몇 배로 늘리나 · 처음 몇 칸인가는 약속이 아니다.** 이 판에서는 **두 배씩**이고, 첫 용량이 **원소 크기에 따라 8·4·1** 로 달랐다(`u8` 8 · `u64` 4 · 2000바이트 원소 1).
  std 의 문장 — 「**`Vec` 은 꽉 찬 뒤 재할당할 때도, `reserve` 를 부를 때도 특정 성장 전략을 보장하지 않는다** … 어떤 전략이든 **`push` 의 O(1) 상환**은 보장한다」.
- ★ **`0 → 0`** — `Vec::new()` 는 **할당하지 않는다**(용량 0). std 도 그렇게 적는다(「`Vec::new` … will not allocate memory」).
- ★ 「두 배로 늘리면 상환 O(1)」이 **왜** 성립하는가는 [`data-structure/01-dynamic-array`](../../../../../data-structure/01-dynamic-array/2-summary.md) 「동작 — 추가」가 정본이다. 여기는 **Rust 가 그 배수를 약속하지 않는다**는 것까지만.

### (3) 용량을 정하는 연산 · 줄이지 않는 연산 · 헤더 크기

**언제 쓰나** — 넣을 개수를 **미리 알 때**, 그리고 **지운 뒤 메모리를 돌려줘야 할 때.**

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

```text
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

- ★★ **`with_capacity(10)` → `cap 10` · `extend 10` → `len 10 cap 10`**(꽉 찼지만 재할당 없음) — std: `with_capacity(n)` 은 **정확히 n 개분**을 할당기에 요청한다(Guarantees).
- ★ **`reserve(1)` → `cap 20` · `reserve_exact(50)` → `cap 60`** — `reserve` 는 「**투기적으로 더 잡을 수 있다**」, `reserve_exact` 는 「**일부러 더 잡지는 않는다**」(둘 다 **`len + additional` 이상**만 약속). 20 은 **이 판의 관찰**이다.
- ★★★ **`split_off(4)` · `truncate(1)` · `clear()` 뒤에도 `cap 60`** — **용량을 안 줄인다.** std 가 셋 다 **명문으로** 적는다 —
  `truncate`·`clear` 「**has no effect on the allocated capacity**」 · `split_off` 「**previous capacity unchanged**」 · 그리고 Guarantees 「**`Vec` 은 완전히 비어도 스스로 줄지 않는다**」.
- ★ **`shrink_to_fit()` → `cap 0`** — 돌려줄 때는 **직접 부른다.** 단 std: 「할당기에 달렸고 **여분이 남을 수도** 있다」 — 이 판에서는 0 이 됐다(관찰).
- ★ **떼어 낸 꼬리 `(the tail)` 은 `len 6 cap 6`** — `split_off` 가 돌려준 새 `Vec` 은 **새로 할당**된다(「a newly allocated vector」). 6 은 관찰이다.
- ★★ **`size_of::<Vec<u64>>()` = `Vec<u8>` = 24 · `Option<Vec<u8>>` 도 24.** 원소 타입과 무관하게 **헤더 셋**(포인터·용량·길이)이다.
  std: 「`Vec` 은 **(포인터, 용량, 길이) 세 쌍이고 앞으로도 그렇다. 더도 덜도 아니다.** 필드 순서는 **전혀 정해지지 않았다**」 · 「포인터는 **절대 널이 아니므로** 널 포인터 최적화가 된다」 — 그래서 `Option` 이 공짜다([40번 주제](../40-box-recursive-types-and-dyn/)의 `Option<Box<T>>` 와 같은 규칙).

### (4) ★★ 순회 중 삭제 — `for` 안의 `remove` 는 막힌다

**언제 쓰나** — 조건에 맞는 원소를 **돌면서** 지우고 싶을 때.

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

```text
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

- ★★★ **E0502 — 같은 번호다.** `v.iter().enumerate()` 가 **`v` 를 빌린 채**(37편 — `iter()` 는 `&T`) 몸통에서 `v.remove(i)` 가 **`&mut v`** 를 요구했다.
  표지 두 줄이 **같은 자리**(`for` 의 이터레이터)를 가리킨다 — 「immutable borrow occurs here」 + 「immutable borrow **later used** here」(다음 바퀴의 `next()` 가 그 빌림을 또 쓴다).
- ★★ **다른 언어는 조용하다** — 파이썬은 순회 중 `list.remove` 가 **예외 없이 원소를 건너뛴다**(Python 갈래의 [**18번**](../../../python/syntax/18-loop-control-and-else/)이 `['a','c','d','e']` 로 쟀다).
  Rust 는 그 코드를 **처음부터 안 받는다.** `help:` 도 없다 — 처방은 아래 셋이다.

**안전한 셋 — `retain` · `drain` · `extract_if`.**

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

```text
===== rustc --edition 2021 r38_remove_ways.rs =====
(exit 0)
===== ./r38_remove_ways =====
[1] retain           kept [1, 3, 5]
[2] drain(1..3)      taken [2, 3]  left [1, 4, 5, 6]
[3] extract_if(..)   taken [2, 4, 6]  left [1, 3, 5]
(exit 0)
```

- ★★ **`[1]` `retain(|x| 남길 조건)`** — `[1, 3, 5]` 가 **남았다.** 지운 것은 **버린다.** std: 「각 원소를 **원래 순서로 정확히 한 번** 방문하고, 남긴 것의 **순서를 지킨다**」.
- ★★ **`[2]` `drain(1..3)`** — **범위로** 떼어 내 `[2, 3]` 을 **가져가고**, `[1, 4, 5, 6]` 이 남는다. 조건이 아니라 **자리**로 지운다. `drain(..)` 이면 전부를 가져가고 **`Vec` 은 남는다**(37편의 `into_iter` 와 다른 점 — 용량째 재사용된다).
- ★★★ **`[3]` `extract_if(.., 조건)`** — **조건으로 지우면서 지운 것을 가져간다**: `[2, 4, 6]` 을 가져가고 `[1, 3, 5]` 가 남는다. **`retain` 과 `drain` 의 합**이다.
  **1.92.0 stable 에서 그대로 컴파일됐다** — 1.87.0 에 안정됐다((0)의 버전 블록). ★ **첫 인자가 범위다**(`..` = 전부) — 안정화된 꼴이 범위를 받는다.
  ★ std: 돌려받은 이터레이터를 **끝까지 안 돌리고 버리면** 나머지는 **안 지운다**(「If the returned `ExtractIf` is not exhausted … the remaining elements will be retained」 — 이 문서는 던지지 않았다).

### (5) `remove` 대 `swap_remove` · `dedup` 은 이웃만

```rust
// r38_order_ops.rs
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
```

```text
===== rustc --edition 2021 r38_order_ops.rs =====
(exit 0)
===== ./r38_order_ops =====
[1] remove(1)      -> b  ['a', 'c', 'd', 'e']
[2] swap_remove(1) -> b  ['a', 'e', 'c', 'd']
[3] dedup          [1, 2, 1, 3]
[4] sort + dedup   [1, 2, 3]
(exit 0)
```

- ★★ **`[1]` `remove(1)`** — `b` 를 빼고 `['a', 'c', 'd', 'e']` — **뒤를 한 칸씩 당겨** 순서를 지킨다. **`[2]` `swap_remove(1)`** — `b` 를 빼고 `['a', 'e', 'c', 'd']` — **마지막 원소 `e` 가 그 자리로 온다.** 순서가 깨진다.
  ★ **복잡도는 std 의 말로만** — `swap_remove` 「**순서를 지키지 않지만 O(1)**」 · `remove` 「**뒤 원소를 옮기므로 최악 O(n)**」. **이 문서는 시간을 재지 않았다.**
- ★★ **`[3]` `dedup()` → `[1, 2, 1, 3]`** — **이웃한 중복만** 지운다. 떨어진 `1` 은 남는다. std: 「**연속된** 반복 원소를 지운다. **정렬돼 있으면** 중복을 전부 지운다」 — **`[4]` `sort` + `dedup` → `[1, 2, 3]`**.

## 문법 — 형태와 규칙

```text
   형태

   Vec::with_capacity(n)          cap ≥ n (정확히 n 개분을 요청)
   v.reserve(k) / reserve_exact(k)  cap ≥ len + k   (reserve 는 더 잡을 수 있다)
   v.shrink_to_fit()              남는 칸을 돌려준다 (할당기에 달렸다)
   v.truncate(n) / v.clear()      len 만 줄인다 — cap 그대로
   v.split_off(i)                 뒤를 새 Vec 으로 — 원본 cap 그대로

   v.retain(|x| 남길_조건)         지운 것은 버린다 · 순서 유지
   v.drain(범위)                  범위를 떼어 가져간다 (이터레이터)
   v.extract_if(범위, |x| 뺄_조건)  조건으로 떼어 가져간다 (1.87~)
   v.swap_remove(i)               O(1) · 순서가 깨진다 (std)
   v.remove(i)                    O(n) · 순서 유지 (std)
   v.dedup()                      이웃한 중복만 — 전부 지우려면 sort 먼저


   금지 사례 — 던져서 받은 것 (번호만)

   let r = &v[0];  v.push(40);  println!("{r}")         ✘ E0502   help: 없음
   for (i, x) in v.iter().enumerate() { v.remove(i) }    ✘ E0502   help: 없음
```

**규칙 불릿.**

- ★★★ **원소를 빌린 채 `&mut self` 메서드를 부르면 E0502** — 재할당이 실제로 일어날지와 무관하다((1)·(4)).
- ★★ **`push` 는 `len == capacity` 일 때만 재할당한다(보장) · 몇 배로 늘리는지는 보장이 없다**((2)).
- ★★ **`truncate`·`clear`·`split_off` 는 용량을 안 줄인다** — `shrink_to_fit` 을 직접((3)).
- ★★ **순회 중 삭제는 `retain`(버린다) · `extract_if`(가져간다) · `drain`(범위로)**((4)).

## 어디서 틀리나

### 1. ★★★ 「용량이 남았으니 `push` 해도 참조가 안전하다」

**용량과 무관하게 E0502** 다((1)). 컴파일러는 **시그니처(`&mut self`)** 만 본다. C++ 에서는 **용량이 남아 있으면 실제로 안전하고 모자라면 UB** — 그 갈림을 사람이 따져야 했던 것을 Rust 는 **통째로 막는다.**

### 2. ★★★ 「`Vec` 은 두 배씩 자란다」

**이 판의 관찰이다**((2)). std 는 「**특정 성장 전략을 보장하지 않는다**」고 명문으로 적는다. 첫 용량도 원소 크기에 따라 **8·4·1** 로 달랐다. **보장된 것은 「꽉 차야 재할당한다」와 「상환 O(1)」** 뿐이다.

### 3. ★★ 「`clear()` 하면 메모리가 돌아간다」

**용량 그대로다**((3) — `cap 60`). std: 「**완전히 비어도 스스로 줄지 않는다**」. 돌려주려면 **`shrink_to_fit`**.

### 4. ★★ 「`for` 안에서 `remove` 하면 파이썬처럼 하나를 건너뛴다」

**컴파일이 안 된다**(E0502 — (4)). 파이썬은 건너뛰고(18번), Rust 는 막는다. **`retain` 이나 `extract_if`** 로.

### 5. ★ 「`dedup` 은 중복을 전부 지운다」

**이웃한 것만**((5) — `[1, 2, 1, 3]`). 전부 지우려면 **먼저 정렬**.

### 6. ★ 「`swap_remove` 는 그냥 빠른 `remove` 다」

**순서가 깨진다**((5) — `e` 가 앞으로 온다). 순서가 뜻이 있는 목록(정렬된 것·시간순)에는 못 쓴다. **O(1) 은 std 의 말이고 이 문서는 재지 않았다.**

### 7. ★ 「`extract_if` 는 nightly 전용이다」

**1.87.0 부터 stable** 이고, 1.92.0 stable 에서 **그대로 컴파일됐다**((4)). 옛 글이 nightly 라고 적은 것은 **범위 인자가 붙기 전의 불안정 판**이다(이 문서는 옛 판을 돌려 보지 않았다 — 툴체인이 1.92 하나뿐이다).

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ 빌림 중 `&mut self` 호출이 **막히는** 것 | ★ **언어 보장** — 빌림 규칙(E0502) | (1)·(4) |
| C++ 에서 재할당 뒤 옛 참조 읽기 | ★ **C++ 에서 UB** — 이 문서는 표준 원문을 안 열었다. **ASan 의 `heap-use-after-free` 가 관찰 근거** | (1) |
| `push` 가 **`len == capacity` 일 때만** 재할당 · `capacity()` 가 **정확** | ★ **std 보장** — Guarantees 「completely accurate, and can be relied on」 | (2) |
| ★★ **성장 배수**(두 배) · **첫 용량**(8·4·1) · `reserve(1)` 뒤 20 | ★ **구현 세부 — std 가 보장하지 않는다고 명시** 「does not guarantee any particular growth strategy」 | (2)·(3) |
| `push` 의 **상환 O(1)** | ★ **std 보장** — 같은 문단 「will of course guarantee O(1) amortized push」 | 인용만 |
| `truncate`·`clear`·`split_off` 가 용량을 **안 줄이는** 것 | ★ **std 보장** — 메서드 문서마다 명문 · 「never automatically shrink」 | (3) |
| `shrink_to_fit` 뒤 **0** | ★ **이 판의 관찰** — std: 「여분이 남을 수도 있다」 | (3) |
| `Vec` 이 **(포인터, 용량, 길이) 셋** · 포인터 **널 아님** | ★ **std 보장** — 「No more, no less」 · 「null-pointer-optimized」 | (3) |
| `size_of::<Vec<_>>()` = **24** · 필드 **순서** | ★ **24 는 이 타깃(64비트)의 결과**, 순서는 **「completely unspecified」** · 「the ABI is not stable」 | (3) |
| `swap_remove` O(1) · `remove` O(n) | ★ **std 문서의 복잡도 문장** — 이 문서는 **재지 않았다** | (5) |
| `extract_if` 의 안정 판 | ★ **릴리스 노트** — 1.87.0 | (0) |

## 언제 쓰고 언제 안 쓰나

- ★★ **넣을 개수를 알면 `with_capacity`** — 이사 횟수가 0 이 된다((3) — `extend 10` 뒤에도 `cap 10`).
- ★★ **원소 참조를 오래 쥐어야 하면 인덱스를 쥔다** — `&v[i]` 대신 `i`. 그 사이의 `push` 가 막히지 않는다((1)).
- ★★ **조건으로 지우기** — 버릴 거면 `retain`, 가져갈 거면 `extract_if`. **범위로 지우기**는 `drain`((4)).
- ★ **순서가 상관없는 집합처럼 쓰는 `Vec`** 이면 `swap_remove`. 순서가 뜻이 있으면 `remove`((5)).
- ★ **크게 채웠다가 비운 `Vec` 을 오래 들고 있으면 `shrink_to_fit`** — `clear` 만으로는 안 돌아간다((3)).
- ★ **앞에서 자주 빼면 `Vec` 이 아니다** — std 가 `remove` 문서에서 **`VecDeque::pop_front`** 를 권한다(이 문서는 재지 않았다).

## 핵심 문장

- ★★★ **`let r = &v[0]; v.push(40); use(r)` 는 C++ 에서 경고 0 · ASan `heap-use-after-free` 이고, Rust 에서는 E0502 다** — 컴파일러는 재할당 여부가 아니라 **`&mut self` 시그니처**로 막는다((1)).
- ★★★ **`push` 는 꽉 찼을 때만 재할당한다(보장) — 몇 배로 늘리나는 보장이 아니다(이 판은 두 배, 첫 용량 8·4·1)**((2)).
- ★★ **`truncate`·`clear`·`split_off` 는 용량을 그대로 둔다 — `cap 60` 이 끝까지 남았다**((3)).
- ★★ **순회 중 `remove` 는 E0502 — `retain`(버린다) · `extract_if`(1.87~, 가져간다) · `drain`(범위)**((4)).
- ★ **`dedup` 은 이웃만, `swap_remove` 는 순서를 버린다**((5)).

## 관련 자료

- ★★ [`data-structure/01-dynamic-array`](../../../../../data-structure/01-dynamic-array/2-summary.md) — **경계**: 동적 배열의 **2배 확장과 상환 O(1) 분석**(「동작 — 추가」 절)은 **거기**다. 여기는 `Vec` API 에서 **무엇이 보장되고 무엇이 관찰인가**와 재할당·빌림의 관계로 좁혔다.
- ★ [**10번 주제** — 빌림 규칙](../10-borrowing-and-aliasing-rules/) — E0502 의 뿌리(공유 XOR 가변).
- [**37번 주제** — `IntoIterator` 세 형태](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) — (4)의 `v.iter()` 가 `v` 를 빌리는 이유. `drain(..)` 은 그 편의 `into_iter` 와 달리 **`Vec` 을 남긴다.**
- [**39번 주제** — `HashMap` 대 `BTreeMap`](../39-hashmap-vs-btreemap-and-entry-api/) — 이 주제의 **다음 사슬**. 맵도 순회 중 삽입이 같은 E0502 에 걸린다.
- [**40번 주제** — `Box<T>`](../40-box-recursive-types-and-dyn/) — `Vec` 과 `Box<[T]>` 의 관계(`into_boxed_slice`)와 `Option` 의 널 포인터 최적화.
- ★ Go 갈래의 [**06번**](../../../go/syntax/06-len-cap-and-append-reallocation/) — `append` 의 재할당. **경계**: Go 는 재할당 뒤 옛 슬라이스가 **옛 배열을 계속 본다**(조용히 갈라진다). Go 의 성장 수치도 **구현 세부**로 적었다.
- ★ Python 갈래의 [**18번**](../../../python/syntax/18-loop-control-and-else/) — 순회 중 `list.remove` 가 **예외 없이 건너뛴다.** (4)의 대비.
- ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **41번** — 순차 컨테이너 선택과 **무효화**. (1)의 C++ 블록은 한 칸 대비다.

## 용어 풀이

- **용량(capacity)** — 재할당 없이 담을 수 있는 원소 수. `len <= capacity`.
- **재할당(reallocation)** — 더 큰 버퍼를 얻어 원소를 옮기고 옛 버퍼를 돌려주는 것.
- **성장 전략(growth strategy)** — 재할당 때 새 용량을 얼마로 잡을지의 규칙. **std 가 보장하지 않는다.**
- **상환 O(1)(amortized)** — 가끔의 비싼 재할당을 여러 번의 싼 `push` 에 나눠 평균 낸 비용. 원리는 `data-structure/01-dynamic-array`.
- **무효화(invalidation)** — 재할당·삭제로 옛 참조·반복자가 **더 이상 유효한 원소를 안 가리키게** 되는 것. C++ 에서는 그 뒤의 사용이 UB.
- **UB(정의되지 않은 동작)** — 언어가 결과를 정하지 않은 동작. 무엇이 나와도 「맞는」 결과다.
- **AddressSanitizer(ASan)** — 컴파일러가 메모리 접근마다 검사를 끼워 넣어 **해제 뒤 사용** 등을 실행 중에 잡는 도구.
- **`retain` / `drain` / `extract_if`** — 조건으로 남기기 / 범위로 떼어 가져가기 / 조건으로 떼어 가져가기.
- **널 포인터 최적화(NPO)** — 포인터가 절대 널이 아니면 그 널 자리를 `None` 으로 써서 `Option` 이 크기를 안 늘리는 것.

## 더 들어가면

- **`Vec` ↔ `Box<[T]>`** — std: 「`len == capacity` 면 **재할당·이동 없이** 서로 바꿀 수 있다」. `into_boxed_slice` 는 남는 용량을 먼저 줄인다. [40번 주제](../40-box-recursive-types-and-dyn/)의 큰 배열 대처가 이 길을 쓴다.
- **`mem::take(&mut v)`** — 원본 자리에 빈 `Vec` 을 두고 **내용과 용량을 통째로** 가져간다(std 의 `split_off` 문서가 가리킨다). 목록의 **44번 주제**.
- **`try_reserve`** — 할당 실패를 **패닉 대신 `Result`** 로 받는다(이 문서는 던지지 않았다).
- **`splice`** — 범위를 떼어 내고 **다른 이터레이터로 채워 넣기.** `drain` 의 짝이다.
