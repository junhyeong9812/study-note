# rust/syntax/37 — `IntoIterator` 세 형태 — `iter`/`iter_mut`/`into_iter` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::iter` 모듈 문서](https://doc.rust-lang.org/std/iter/index.html)(for 의 탈당 · Iterating by reference) ·
> [std — `std::collections` 모듈 문서](https://doc.rust-lang.org/std/collections/index.html)(Iterators 절 — 「세 가지 주 이터레이터 `iter`·`iter_mut`·`into_iter`」) ·
> [std — `IntoIterator`](https://doc.rust-lang.org/std/iter/trait.IntoIterator.html) ·
> [Edition Guide — 2021 `IntoIterator` for arrays](https://doc.rust-lang.org/edition-guide/rust-2021/IntoIterator-for-arrays.html) ·
> [Edition Guide — 2024 `IntoIterator` for `Box<[T]>`](https://doc.rust-lang.org/edition-guide/rust-2024/intoiterator-box-slice.html) ·
> [Reference — `for` 의 탈당](https://doc.rust-lang.org/reference/expressions/loop-expr.html#iterator-loops).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. std 소스의 `impl` 줄도 같은 사본의 소스 페이지에서 **스크립트로 뽑았다**((3)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **블록마다 배너에 적은 `--edition`** 으로 돌려 받은 것이다(기본 2021, 에디션 격자는 2015·2018·2021·2024).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **속도는 한 번도 재지 않았다.**
> **버전** — 배열의 `IntoIterator` 는 **1.53.0**, `Box<[T]>` 의 `IntoIterator` 는 **1.80.0**, 2021 에디션 **1.56.0**, 2024 에디션 **1.85.0**(아래 블록이 근거).
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
===== awk '/^Version 1\./{v=$2} /Arrays of any length now implement .IntoIterator|impl IntoIterator for Box<\[T\]>|The 2021 Edition is now stable|The 2024 Edition is now stable/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.85.0 | - [The 2024 Edition is now stable.](https://github.com/rust-lang/rust/pull/133349)
1.80.0 | - [`impl IntoIterator for Box<[T]>`](https://doc.rust-lang.org/beta/alloc/boxed/struct.Box.html#impl-IntoIterator-for-Box%3C%5BI%5D,+A%3E)
1.56.0 | - [The 2021 Edition is now stable.][rust#88100]
1.53.0 | - [Arrays of any length now implement `IntoIterator`.][84147]
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 칸마다 `x` 의 타입과 `ok`/`E0382`** · 마지막 줄 `2 / 6` | 같은 판에서 고정이다. **이 주제의 본체** |
| ★★ **에디션이 가른다** | **(2)의 격자** — 같은 소스가 에디션에 따라 `&i32` 와 `i32` 로 갈린다 · 마지막 줄 `2 / 6` | ★ **흔들리는 것이 아니라 에디션이 정한다** — 같은 판·같은 에디션이면 고정이다 |
| 안 흔들린다 | `type_name_of_val` 의 문자열 | 같은 판에서 고정. **형식은 보장되지 않는다**(std) |
| 안 흔들린다 | std 소스 페이지의 **줄 번호**(3733 등) | 같은 `rust-docs` 판에서 고정이다. **판이 오르면 번호가 움직인다** |
| ★ **흔들릴 수 있어 피했다** | `HashMap` 의 **순회 순서** | (5)는 키를 **하나만** 넣어 순서가 문제 되지 않게 했다(규칙 11 — 순서 격자는 [39번 주제](../39-hashmap-vs-btreemap-and-entry-api/)) |
| 안 흔들린다 | 에러·경고 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼다(제출 전 재대조 — 「3-answer」의 실행 검증 표).

## 한눈에 — 쉽게 말하면

**컬렉션을 도는 방법은 세 가지다 — 「진열장 유리 너머로 구경하기」·「장갑 끼고 손질하기」·「통째로 들고 가기」.
앞의 둘은 진열장이 그대로 남고, 마지막은 진열장이 비어 버린다. `for` 는 이 셋 중 **무엇을 넣었느냐**로 고른다.**

| 비유 | 실체 |
|---|---|
| 「**유리 너머 구경**」 | `for x in &v` = `v.iter()` — `x: &T`. 순회 뒤 **`v` 를 그대로 쓴다**((1)) |
| 「**장갑 끼고 손질**」 | `for x in &mut v` = `v.iter_mut()` — `x: &mut T`. 고칠 때는 **`*x`**((4)) |
| 「**통째로 들고 가기**」 | `for x in v` = `v.into_iter()` — `x: T`. 순회 뒤 `v` 는 **E0382**((1)) |
| 「**`for` 는 가게 주인에게 「이걸 어떻게 돌까요」 묻는다**」 | ★★ `for x in E` 는 **`IntoIterator::into_iter(E)`** 로 탈당된다 — 무엇이 나오는지는 **`E` 의 타입에 달린 구현**이 정한다((3)) |
| 「**가게마다 붙은 안내문 셋**」 | ★★ std 가 `Vec<T>` · `&Vec<T>` · `&mut Vec<T>` 각각에 **`impl IntoIterator`** 를 둔다((3)) |
| 「**옛 가게의 간판은 옛 뜻 그대로**」 | ★★★ **배열의 `.into_iter()` 는 2021 부터, `Box<[T]>` 는 2024 부터 `T`** — 그 전 에디션은 `&T`((2)) |

- ★★★ **판정은 한 줄이다 — 「`for` 에 넣은 것이 값이면 옮기고, `&` 면 빌려 읽고, `&mut` 면 빌려 고친다.」**
  `iter()`·`iter_mut()`·`into_iter()` 는 **같은 세 갈래를 메서드로 부르는 이름**이다((1)의 격자 — 여섯 칸이 셋씩 짝이다).

```text
   ★ 세 형태 — (1)의 격자를 그림으로 (칸의 값은 그 블록 그대로)

   for x in  v        ─▶ IntoIterator::into_iter(v)        ─▶ impl … for Vec<T>       ─▶ x: T       ─▶ 뒤에 v.len()  ✘ E0382
   for x in &v        ─▶ IntoIterator::into_iter(&v)       ─▶ impl … for &Vec<T>      ─▶ x: &T      ─▶ 뒤에 v.len()  ✔
   for x in &mut v    ─▶ IntoIterator::into_iter(&mut v)   ─▶ impl … for &mut Vec<T>  ─▶ x: &mut T  ─▶ 뒤에 v.len()  ✔
                                                              └── (3)의 std 소스 3694 · 3733 · 3743 줄 ──┘

   v.iter()      ≡  for x in &v         (impl 이 self.iter() 를 부른다 — 3738 줄)
   v.iter_mut()  ≡  for x in &mut v     (impl 이 self.iter_mut() 를 부른다 — 3748 줄)
   v.into_iter() ≡  for x in v
```

> **`IntoIterator`** — 「이터레이터로 **바뀔 수 있는** 것」의 트레이트. `fn into_iter(self) -> Self::IntoIter` 하나와 연관 타입 `Item`·`IntoIter` 를 갖는다.\
> 예: `Vec<T>` 도, `&Vec<T>` 도, `&mut Vec<T>` 도 각각 **따로** 이것을 구현한다.

> **탈당(desugaring)** — 문법 설탕을 원래 모양으로 푸는 것. Reference 가 `for` 를 `IntoIterator::into_iter(E)` + `loop { match next() … }` 로 적는다.\
> 예: `for x in &v` 는 `IntoIterator::into_iter(&v)` 로 시작한다.

> **에디션(edition)** — 크레이트마다 고르는 「언어 방언」 판. 같은 컴파일러가 에디션에 따라 **같은 소스를 다르게 읽을 수 있다.**\
> 예: `rustc --edition 2018` 과 `--edition 2021` 은 배열의 `.into_iter()` 를 다르게 푼다((2)).

## 이 주제가 답하려는 질문

1. ★★★ **`for x in v` 와 `for x in &v` 는 무엇이 다른가** — `x` 의 타입과 **순회 뒤 `v` 를 쓸 수 있나**로((1)).
2. ★★ **`for x in &v` 는 어떻게 되는가** — 「`&` 를 붙이면 빌린다」는 문법이 아니라 **std 의 `impl`** 이다((3)·(6)).
3. ★★ **`.into_iter()` 는 언제나 `T` 를 내놓는가** — 에디션과 원본 타입에 따라 **아니다**((2)).

★ **선행** — [**36번 주제**](../36-iterator-adapters-laziness-and-collect/)의 **이터레이터**와 (6)의 셋 한 칸(`&String` · `&mut String` · `String` · E0382)이 이 주제의 출발점이다.
여기서는 그 한 칸을 **여섯 형태 격자**로 펴고, 36편이 「더 들어가면」에 남긴 **배열 `into_iter` 의 에디션 차이**를 **네 에디션 × 두 원본 × 세 꼴**로 넓힌다.
[**08번 주제**](../08-ownership-and-move/)의 **이동(E0382)** 과 [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 **빌림**, [**25번 주제**](../25-traits-definition-impl-default-methods-and-associated-types/)의 **연관 타입**이 뼈대다.
★ **정본 경계** — 어댑터·게으름·`collect` 는 36편이 정본이다. 여기는 **순회의 입구(무엇이 나오나 · 원본이 남나)** 만 쓴다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 여섯 형태 격자다

★★★ **본체 창 — ① 「형태 여섯 × (`x` 의 타입 · 순회 뒤 `v.len()`)」을 스크립트가 칸마다 컴파일·실행해 채우는 격자.** 마지막 줄에 **`N / 6`** 을 찍는다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **여섯 형태 격자**(`type_name_of_val` + 컴파일러) | 형태마다 **무엇이 나오나 · 원본이 남나**((1)) | ★ **본체** |
| ② ★★ **에디션 격자 2015 · 2018 · 2021 · 2024** | 같은 소스의 `.into_iter()` 가 **어느 판에서 뜻이 바뀌나**((2)) | 쓴다 — 넷째 축 |
| ③ ★★ **std 소스의 `impl` 줄**(설치된 `rust-docs` 소스 페이지) | `for x in &v` 가 되는 **이유**((3)) | 쓴다 |
| ④ **컴파일러 진단 + `help:` 따라 하기** | E0382 · E0368 · E0277 과 그 처방이 **맞나**((4)·(6)) | 쓴다 |
| ⑤ **`HashMap` 순회의 항목 타입** | `(&K, &V)` · `(&K, &mut V)` · `(K, V)`((5)) | 쓴다 — ①의 규칙이 맵에도 선다 |
| 실행 시간 · 기계어 | 「`iter()` 가 `into_iter()` 보다 빠르다」류 | ★ **부적용 — 재지 않는다.** 이 주제의 질문이 아니다 |
| `HashMap` 순회 **순서** | — | ★ **부적용** — 순서는 [39번 주제](../39-hashmap-vs-btreemap-and-entry-api/)의 본체. 여기는 **키 하나**로 타입만 본다 |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「`&v` 로 돌면 왜 빌리나」를 **① 격자**에 물으면 「`&String` 이 나오고 `v` 가 남는다」까지만 답한다.
**왜**를 물으려면 창을 **③ std 소스**로 바꿔야 한다 — `impl IntoIterator for &'a Vec<T, A>` 가 **`self.iter()` 를 부른다**는 한 줄이 답이다((3)).

### (1) ★★★ 여섯 형태 격자 — 무엇을 내놓나 × 원본을 다시 쓸 수 있나

**언제 쓰나** — 돌고 나서 **원본을 또 쓸지**, 순회 안에서 **고칠지** 정할 때.

```bash
# r37_grid.sh
# 여섯 형태 × (x 의 타입 · 순회 뒤 v.len()) — 형태마다 소스 두 벌을 만들어 던진다
forms=(
  'for x in v'
  'for x in &v'
  'for x in &mut v'
  'for x in v.iter()'
  'for x in v.iter_mut()'
  'for x in v.into_iter()'
)
printf '%-24s | %-28s | %s\n' form 'type of x' 'v.len() after the loop'
bad=0
for f in "${forms[@]}"; do
  body="    let mut v = vec![String::from(\"a\")];
    let mut t = \"\";
    $f { t = std::any::type_name_of_val(&x); }
    println!(\"{t}\");"
  printf 'fn main() {\n%s\n}\n' "$body" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>/dev/null
  ty=$(./g)
  printf 'fn main() {\n%s\n    println!("{}", v.len());\n}\n' "$body" > h.rs
  if out=$(rustc --edition 2021 -A unused -o h h.rs 2>&1); then
    cell=ok
  else
    cell=$(printf '%s\n' "$out" | grep -o 'error\[E[0-9]*\]' | head -1)
    bad=$((bad+1))
  fi
  printf '%-24s | %-28s | %s\n' "$f" "$ty" "$cell"
done
echo "cells where v cannot be used after the loop: $bad / ${#forms[@]}"
```

```text
===== bash r37_grid.sh =====
form                     | type of x                    | v.len() after the loop
for x in v               | alloc::string::String        | error[E0382]
for x in &v              | &alloc::string::String       | ok
for x in &mut v          | &mut alloc::string::String   | ok
for x in v.iter()        | &alloc::string::String       | ok
for x in v.iter_mut()    | &mut alloc::string::String   | ok
for x in v.into_iter()   | alloc::string::String        | error[E0382]
cells where v cannot be used after the loop: 2 / 6
(exit 0)
```

- ★★★ **여섯 칸이 세 짝이다** — `for x in v` ↔ `v.into_iter()`(`String` · **E0382**) · `for x in &v` ↔ `v.iter()`(`&String` · `ok`) · `for x in &mut v` ↔ `v.iter_mut()`(`&mut String` · `ok`).
  **같은 짝은 타입도 결과도 한 글자도 같다.** 메서드 셋은 `for` 의 세 입구를 **이름으로 부르는 것**이다.
- ★★ **`v` 를 못 쓰는 칸 `2 / 6`** — 둘 다 **값으로 넘긴 칸**이다. 원소 `String` 이 `x` 로 **옮겨 나갔으니** `Vec` 이 빈 껍데기가 아니라 **아예 없어졌다**(08번의 이동).
- ★ 원소를 `String` 으로 둔 것은 일부러다 — **원소가 `Copy` 면 달라지나?**

```rust
// r37_copy.rs
// 원소가 Copy 인 i32 일 때
fn main() {
    let v = vec![1, 2];
    for x in v {
        let _ = x;
    }
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r37_copy.rs =====
error[E0382]: borrow of moved value: `v`
 --> r37_copy.rs:7:20
  |
3 |     let v = vec![1, 2];
  |         - move occurs because `v` has type `Vec<i32>`, which does not implement the `Copy` trait
4 |     for x in v {
  |              - `v` moved due to this implicit call to `.into_iter()`
...
7 |     println!("{}", v.len());
  |                    ^ value borrowed here after move
  |
note: `into_iter` takes ownership of the receiver `self`, which moves `v`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/collect.rs:310:18
help: consider iterating over a slice of the `Vec<i32>`'s content to avoid moving into the `for` loop
  |
4 |     for x in &v {
  |              +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

- ★★ **원소가 `i32`(`Copy`)여도 E0382 가 똑같이 난다.** 진단이 「`v` has type **`Vec<i32>`**, which does not implement the `Copy` trait」이라고 적는다 — 옮겨지는 것은 원소가 아니라 **`Vec` 자체**다.

### (2) ★★ 에디션 격자 — `.into_iter()` 는 언제나 `T` 인가

**언제 쓰나** — 배열이나 `Box<[T]>` 에 `.into_iter()` 를 부를 때. **옛 에디션 크레이트를 올릴 때.**

```bash
# r37_ed_grid.sh
# 같은 소스를 네 에디션으로 — 원본 둘(배열 · Box<[i32]>) × 부르는 꼴 셋
exprs=(
  'a.into_iter()'
  'IntoIterator::into_iter(a)'
  'for-in a'
)
srcs=('[1, 2, 3]' 'vec![1, 2, 3].into_boxed_slice()')
names=('array' 'Box<[i32]>')
printf '%-12s %-28s | %-6s | %-6s | %-6s | %s\n' source call 2015 2018 2021 2024
changed=0; total=0
for i in 0 1; do
  for e in "${exprs[@]}"; do
    if [ "$e" = 'for-in a' ]; then
      line="    let mut t = \"\"; for x in a { t = std::any::type_name_of_val(&x); } println!(\"{t}\");"
    else
      line="    let it = $e; let mut t = \"\"; for x in it { t = std::any::type_name_of_val(&x); } println!(\"{t}\");"
    fi
    printf 'fn main() {\n    let a = %s;\n%s\n}\n' "${srcs[$i]}" "$line" > e.rs
    row=()
    for ed in 2015 2018 2021 2024; do
      rustc --edition $ed -A warnings -o e e.rs 2>/dev/null
      row+=("$(./e)")
    done
    total=$((total+1))
    [ "${row[1]}" != "${row[2]}" ] || [ "${row[2]}" != "${row[3]}" ] && changed=$((changed+1))
    printf '%-12s %-28s | %-6s | %-6s | %-6s | %s\n' "${names[$i]}" "$e" "${row[@]}"
  done
done
echo "rows whose item type changes across editions: $changed / $total"
```

```text
===== bash r37_ed_grid.sh =====
source       call                         | 2015   | 2018   | 2021   | 2024
array        a.into_iter()                | &i32   | &i32   | i32    | i32
array        IntoIterator::into_iter(a)   | i32    | i32    | i32    | i32
array        for-in a                     | i32    | i32    | i32    | i32
Box<[i32]>   a.into_iter()                | &i32   | &i32   | &i32   | i32
Box<[i32]>   IntoIterator::into_iter(a)   | i32    | i32    | i32    | i32
Box<[i32]>   for-in a                     | i32    | i32    | i32    | i32
rows whose item type changes across editions: 2 / 6
(exit 0)
```

- ★★★ **바뀐 줄 `2 / 6` — 둘 다 `.into_iter()` 메서드 호출 꼴이다.**
  - **배열** — 2015·2018 은 **`&i32`**, 2021·2024 는 **`i32`**. 경계는 **2018 → 2021**.
  - **`Box<[i32]>`** — 2015·2018·2021 은 **`&i32`**, 2024 는 **`i32`**. 경계는 **2021 → 2024**.
- ★★ **나머지 넷(`IntoIterator::into_iter(a)`·`for x in a`)은 네 에디션 전부 `i32`** 다. 구현은 **모든 에디션에 있다** — 옛 에디션은 **`.into_iter()` 라는 메서드 꼴만** 옛 뜻(`(&a).into_iter()`)으로 푼다.
  Edition Guide 의 말 그대로다 — 「**`array.into_iter()` 메서드 호출 꼴에만** 해당한다. `for e in [1, 2, 3]` · `IntoIterator::into_iter([1, 2, 3])` 같은 다른 꼴은 **모든 에디션에서** 된다」.
- ★ 왜 이런 누더기인가 — **구현을 에디션마다 따로 둘 수 없다**(에디션은 크레이트끼리 섞인다). 그래서 **1.53.0 에 배열 구현을 전 에디션에 넣고**, 옛 에디션의 메서드 꼴에만 옛 해석을 남겼다(Edition Guide). `Box<[T]>` 도 **1.80.0** 에 같은 길을 한 번 더 걸었다((0)의 버전 블록).

**2021 에서 `Box<[i32]>` 에 `.into_iter()` — 경고가 말하는 것.**

```rust
// r37_boxslice.rs
fn main() {
    let b: Box<[i32]> = vec![1, 2, 3].into_boxed_slice();
    let mut t = "";
    for x in b.into_iter() {
        t = std::any::type_name_of_val(&x);
    }
    println!("{t}");
}
```

```text
===== rustc --edition 2021 r37_boxslice.rs =====
warning: this method call resolves to `<&Box<[T]> as IntoIterator>::into_iter` (due to backwards compatibility), but will resolve to `<Box<[T]> as IntoIterator>::into_iter` in Rust 2024
 --> r37_boxslice.rs:4:16
  |
4 |     for x in b.into_iter() {
  |                ^^^^^^^^^
  |
  = warning: this changes meaning in Rust 2024
  = note: for more information, see <https://doc.rust-lang.org/edition-guide/rust-2024/intoiterator-box-slice.html>
  = note: `#[warn(boxed_slice_into_iter)]` (part of `#[warn(rust_2024_compatibility)]`) on by default
help: use `.iter()` instead of `.into_iter()` to avoid ambiguity
  |
4 -     for x in b.into_iter() {
4 +     for x in b.iter() {
  |
help: or remove `.into_iter()` to iterate by value
  |
4 -     for x in b.into_iter() {
4 +     for x in b {
  |

warning: 1 warning emitted

(exit 0)
===== ./r37_boxslice =====
&i32
(exit 0)
```

```text
===== rustc --edition 2024 r37_boxslice.rs =====
(exit 0)
===== ./r37_boxslice =====
i32
(exit 0)
```

- ★★ **2021 은 경고 한 줄 + `&i32`, 2024 는 경고 없이 `i32`.** 경고 「**this changes meaning in Rust 2024**」 · 린트 `boxed_slice_into_iter`.
- ★★ **`help:` 가 두 갈래다** — ① 「**use `.iter()` instead**」(= 지금 뜻 `&i32` 를 **못 박기**) ② 「**or remove `.into_iter()` to iterate by value**」(= `for x in b` — 2024 의 뜻 `i32` 를 **지금 당기기**).
  ②를 따른 꼴이 곧 (2)의 격자 `for-in a` 줄이다 — **네 에디션 전부 `i32`** 로 이미 확인했다. **두 처방이 서로 반대 방향**이라 뜻을 골라서 따라야 한다.
- ★ 배열의 2018 경고(「this changes meaning in Rust 2021」)는 [36번 주제](../36-iterator-adapters-laziness-and-collect/)의 「더 들어가면」 블록에 있다 — 여기서 다시 찍지 않았다.

**에디션 경계를 한 표로** — 이 갈래가 지금까지 **같은 소스를 에디션만 바꿔 던져** 잰 것.

| 경계 | 무엇이 바뀌나 | 어디서 쟀나 |
|---|---|---|
| **2018 → 2021** | ★★ 배열의 `.into_iter()` — `&T` → `T` | 이 편 (2) · [36번 주제](../36-iterator-adapters-laziness-and-collect/) 「더 들어가면」 |
| **2018 → 2021** | ★★ 클로저 포착 — 변수 **통째** → **쓴 자리(필드)만** · 크기 32 → 24 | [34번 주제](../34-closures-fn-fnmut-fnonce-and-move/) (6) — **바뀐 소스 3 / 3** |
| **2021 → 2024** | ★★ `Box<[T]>` 의 `.into_iter()` — `&T` → `T` | 이 편 (2) |
| **2021 → 2024** | 반환 위치 `impl Trait` 의 수명 포착 — 적힌 수명만 → 시야 안 전부 | [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (5) |

- ★ **공통점 — 넷 다 「같은 소스가 컴파일은 되는데 뜻이 바뀌는」 자리**다. 그래서 에디션을 올릴 때 **이전 린트**가 경고로 먼저 알려 준다(`array_into_iter` · `boxed_slice_into_iter` · 34편의 disjoint capture 린트). 에디션 전반은 목록의 **47번 주제**가 정본이다.

### (3) ★★ `for x in &v` 가 되는 이유 — std 소스의 `impl` 셋

**언제 쓰나** — 「`&` 를 붙이면 빌려서 돈다」를 **외우지 않고 유도**하고 싶을 때. 그리고 **내 타입**에서 같은 것을 하고 싶을 때((6)).

```python
# r37_impls.py
# 설치된 rust-docs 의 std 소스 페이지에서 Vec 의 IntoIterator 구현 셋의 머리와 into_iter 몸통만 뽑는다
import html
import re
import subprocess

root = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()
page = root + "/share/doc/rust/html/src/alloc/vec/mod.rs.html"
text = html.unescape(re.sub(r"<[^>]+>", "", open(page, encoding="utf-8").read()))
lines = text.split("\n")
head = re.compile(r"^(\d+)(impl<.*> IntoIterator for .*Vec<T, A> \{)$")

for i, l in enumerate(lines):
    m = head.match(l)
    if not m:
        continue
    k = i
    while re.match(r"^\d+\s*#\[", lines[k - 1]):
        k -= 1
    while True:
        n = re.match(r"^(\d+)(.*)$", lines[k])
        no, code = n.group(1), n.group(2)
        s = code.strip()
        if s and not s.startswith("///") and not s.startswith("//"):
            print(f"{no:>5} {code}")
        if code.startswith("}"):
            break
        k += 1
    print()
```

```text
===== python3 r37_impls.py =====
 3693 #[stable(feature = "rust1", since = "1.0.0")]
 3694 impl<T, A: Allocator> IntoIterator for Vec<T, A> {
 3695     type Item = T;
 3696     type IntoIter = IntoIter<T, A>;
 3714     #[inline]
 3715     fn into_iter(self) -> Self::IntoIter {
 3716         unsafe {
 3717             let me = ManuallyDrop::new(self);
 3718             let alloc = ManuallyDrop::new(ptr::read(me.allocator()));
 3719             let buf = me.buf.non_null();
 3720             let begin = buf.as_ptr();
 3721             let end = if T::IS_ZST {
 3722                 begin.wrapping_byte_add(me.len())
 3723             } else {
 3724                 begin.add(me.len()) as *const T
 3725             };
 3726             let cap = me.buf.capacity();
 3727             IntoIter { buf, phantom: PhantomData, cap, alloc, ptr: buf, end }
 3728         }
 3729     }
 3730 }

 3732 #[stable(feature = "rust1", since = "1.0.0")]
 3733 impl<'a, T, A: Allocator> IntoIterator for &'a Vec<T, A> {
 3734     type Item = &'a T;
 3735     type IntoIter = slice::Iter<'a, T>;
 3737     fn into_iter(self) -> Self::IntoIter {
 3738         self.iter()
 3739     }
 3740 }

 3742 #[stable(feature = "rust1", since = "1.0.0")]
 3743 impl<'a, T, A: Allocator> IntoIterator for &'a mut Vec<T, A> {
 3744     type Item = &'a mut T;
 3745     type IntoIter = slice::IterMut<'a, T>;
 3747     fn into_iter(self) -> Self::IntoIter {
 3748         self.iter_mut()
 3749     }
 3750 }

(exit 0)
```

- ★★★ **세 `impl` 이 세 타입에 따로 있다** — `for Vec<T, A>`(3694) · `for &'a Vec<T, A>`(3733) · `for &'a mut Vec<T, A>`(3743). `for` 는 `E` 의 **타입**으로 이 중 하나를 고른다.
- ★★ **`&Vec` 쪽 몸통은 `self.iter()` 한 줄**(3738), `&mut Vec` 쪽은 **`self.iter_mut()` 한 줄**(3748)이다. 그래서 (1)의 짝이 **한 글자도 같았다** — 같은 함수를 부르기 때문이다.
  std 모듈 문서의 문장 그대로다 — 「컬렉션 `C` 가 `iter()` 를 주면 **보통** `&C` 에도 `IntoIterator` 를 구현하고, 그 구현은 **그냥 `iter()` 를 부른다**」.
- ★ **`Item` 이 답이다** — `type Item = T` · `&'a T` · `&'a mut T`. (1)의 `type of x` 칸이 이 줄에서 나왔다([25번 주제](../25-traits-definition-impl-default-methods-and-associated-types/)의 연관 타입).
- ★ **값 쪽(3694)은 `ManuallyDrop::new(self)`** 로 시작한다 — `self` 를 **값으로 받아** 버퍼를 `IntoIter` 로 **넘긴다**. `Vec` 은 그 자리에서 끝난다 — (1)의 E0382 가 **여기서 온다.**

### (4) 진단 둘 — `into_iter()` 뒤 원본 · `iter_mut` 으로 고치기

**`.into_iter()` 를 부른 뒤 `v` 를 쓰면.**

```rust
// r37_move.rs
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    let it = v.into_iter();
    println!("{}", it.count());
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r37_move.rs =====
error[E0382]: borrow of moved value: `v`
 --> r37_move.rs:5:20
  |
2 |     let v = vec![String::from("a"), String::from("b")];
  |         - move occurs because `v` has type `Vec<String>`, which does not implement the `Copy` trait
3 |     let it = v.into_iter();
  |                ----------- `v` moved due to this method call
4 |     println!("{}", it.count());
5 |     println!("{}", v.len());
  |                    ^ value borrowed here after move
  |
note: `into_iter` takes ownership of the receiver `self`, which moves `v`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/collect.rs:310:18
help: you can `clone` the value and consume it, but this might not be your desired behavior
  |
3 |     let it = v.clone().into_iter();
  |               ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

- ★★ **E0382** — 「**`v` moved due to this method call**」 · `note:` 「**`into_iter` takes ownership of the receiver `self`, which moves `v`**」.
  36편의 `for s in v` 판은 「**implicit call to `.into_iter()`**」라고 했다 — **숨은 호출이냐 보이는 호출이냐**만 다르고 같은 이동이다.
  ★ `note:` 가 짚는 곳이 **`core/src/iter/traits/collect.rs`** 다 — `IntoIterator` 의 **트레이트 정의**가 `self` 를 값으로 받는다.

**`help:` 대로 `clone()` 을 붙이면.**

```rust
// r37_move_help.rs
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    let it = v.clone().into_iter();
    println!("{}", it.count());
    println!("{}", v.len());
}
```

```text
===== rustc --edition 2021 r37_move_help.rs =====
(exit 0)
===== ./r37_move_help =====
2
2
(exit 0)
```

- ★ **통과한다**(`2` · `2`). 그런데 `help:` 스스로 「**this might not be your desired behavior**」라고 적는다 — **원소를 전부 복제**한 것이다.
  원본을 남기려는 뜻이면 **`v.iter()`** 가 맞다((1)의 격자 — 복제 없이 `ok`). **처방은 통과했지만 이 자리의 뜻에는 과했다.**

**`&mut v` 로 돌며 고치기 — `*` 를 빠뜨리면.**

```rust
// r37_mut.rs
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &mut v {
        x *= 10;
    }
    println!("{v:?}");
}
```

```text
===== rustc --edition 2021 r37_mut.rs =====
error[E0368]: binary assignment operation `*=` cannot be applied to type `&mut {integer}`
 --> r37_mut.rs:4:9
  |
4 |         x *= 10;
  |         -^^^^^^
  |         |
  |         cannot use `*=` on type `&mut {integer}`
  |
help: `*=` can be used on `{integer}` if you dereference the left-hand side
  |
4 |         *x *= 10;
  |         +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0368`.
(exit 1)
```

- ★★ **E0368** — 「binary assignment operation `*=` cannot be applied to type `&mut {integer}`」. `x` 는 **숫자가 아니라 숫자를 가리키는 `&mut`** 이다.
  `help:` 는 「**`*x *= 10`**」— 따라 하면:

```rust
// r37_mut_fix.rs
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &mut v {
        *x *= 10;
    }
    println!("{v:?}");
}
```

```text
===== rustc --edition 2021 r37_mut_fix.rs =====
(exit 0)
===== ./r37_mut_fix =====
[10, 20, 30]
(exit 0)
```

- ★ **`[10, 20, 30]`** — 이 `help:` 는 **맞았다.** `iter_mut()` 도 `&mut T` 를 내놓으므로 **같은 `*`** 가 필요하다((1)의 격자).

### (5) `enumerate` 와 `HashMap` — 규칙은 그대로, 항목이 짝일 뿐

```rust
// r37_pairs.rs
use std::any::type_name_of_val;
use std::collections::HashMap;

fn main() {
    let v = vec!['a', 'b'];
    for (i, x) in v.iter().enumerate() {
        println!("[1] {i} {x} : {} , {}", type_name_of_val(&i), type_name_of_val(&x));
    }

    let mut m = HashMap::new();
    m.insert(String::from("k"), 1);
    for (k, n) in &m {
        println!("[2] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
    for (k, n) in &mut m {
        *n += 1;
        println!("[3] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
    for (k, n) in m {
        println!("[4] {k} {n} : {} , {}", type_name_of_val(&k), type_name_of_val(&n));
    }
}
```

```text
===== rustc --edition 2021 r37_pairs.rs =====
(exit 0)
===== ./r37_pairs =====
[1] 0 a : usize , &char
[1] 1 b : usize , &char
[2] k 1 : &alloc::string::String , &i32
[3] k 2 : &alloc::string::String , &mut i32
[4] k 2 : alloc::string::String , i32
(exit 0)
```

- ★ **`[1]` `v.iter().enumerate()` 는 `(usize, &char)`** — 번호는 **값**(`usize`)으로, 원소는 `iter()` 가 준 **`&char`** 그대로 붙는다. `enumerate` 는 원소를 **바꾸지 않고 번호만 얹는다.**
- ★★ **`[2]` `for (k, n) in &m` 은 `(&String, &i32)`** — `&HashMap` 의 `IntoIterator` 가 **`(&K, &V)`** 를 준다. `[3]` `&mut m` 은 **`(&K, &mut V)`** — ★ **키는 `&mut` 가 안 된다.**
  std 모듈 문서의 이유 — 「`HashSet` 의 키를 고치면 **해시가 바뀌어** 컬렉션이 어긋난 상태가 될 수 있어서 `iter()` 만 준다」. 맵도 같은 이유로 값만 고치게 한다.
- ★ **`[4]` `for (k, n) in m` 은 `(String, i32)`** — 값으로 넘겼으니 **옮겨 가진다.** 이 뒤에 `m` 은 (1)의 첫 줄처럼 E0382 다.
- ★ 키를 **하나만** 넣었다 — `HashMap` 의 순회 **순서**는 실행마다 바뀐다([39번 주제](../39-hashmap-vs-btreemap-and-entry-api/)). 여기는 **타입만** 본다.

### (6) 내 타입에 `IntoIterator` 셋 — 그리고 하나가 빠지면

**언제 쓰나** — 내 컬렉션 타입을 `for` 에 **세 형태 다** 넣을 수 있게 하고 싶을 때.

```rust
// r37_own.rs
// 내 타입에 IntoIterator 를 셋 구현한다 — 값 · & · &mut
struct Shelf {
    books: Vec<String>,
}

impl IntoIterator for Shelf {
    type Item = String;
    type IntoIter = std::vec::IntoIter<String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.into_iter()
    }
}

impl<'a> IntoIterator for &'a Shelf {
    type Item = &'a String;
    type IntoIter = std::slice::Iter<'a, String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.iter()
    }
}

impl<'a> IntoIterator for &'a mut Shelf {
    type Item = &'a mut String;
    type IntoIter = std::slice::IterMut<'a, String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.iter_mut()
    }
}

fn main() {
    let mut s = Shelf { books: vec![String::from("dune"), String::from("emma")] };
    for b in &s {
        print!("{b} ");
    }
    println!("| [1] after &s : {}", s.books.len());
    for b in &mut s {
        b.push('!');
    }
    println!("[2] after &mut s : {:?}", s.books);
    let mut got = Vec::new();
    for b in s {
        got.push(b);
    }
    println!("[3] after s : {got:?}");
}
```

```text
===== rustc --edition 2021 r37_own.rs =====
(exit 0)
===== ./r37_own =====
dune emma | [1] after &s : 2
[2] after &mut s : ["dune!", "emma!"]
[3] after s : ["dune!", "emma!"]
(exit 0)
```

- ★★ **`impl` 셋을 쓰면 `for b in &s` · `for b in &mut s` · `for b in s` 가 전부 된다** — (3)의 std 가 `Vec` 에 한 것과 **같은 모양**이다. 몸통은 안쪽 `Vec` 의 `iter()` · `iter_mut()` · `into_iter()` 에 **넘긴다.**
- ★ `[1]` 뒤에 `s.books.len()` 이 `2` · `[2]` 뒤에 `"dune!"` — 앞의 둘은 **원본이 남는다.** `[3]` 은 `s` 를 **옮겼다.**

**값 구현만 두고 `&s` 로 돌면.**

```rust
// r37_own_missing.rs
// 값 구현 하나만 — & 구현은 안 했다
struct Shelf {
    books: Vec<String>,
}

impl IntoIterator for Shelf {
    type Item = String;
    type IntoIter = std::vec::IntoIter<String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.into_iter()
    }
}

fn main() {
    let s = Shelf { books: vec![String::from("dune")] };
    for b in &s {
        println!("{b}");
    }
}
```

```text
===== rustc --edition 2021 r37_own_missing.rs =====
error[E0277]: `&Shelf` is not an iterator
  --> r37_own_missing.rs:16:14
   |
16 |     for b in &s {
   |              ^^ `&Shelf` is not an iterator
   |
   = help: the trait `Iterator` is not implemented for `&Shelf`
   = note: required for `&Shelf` to implement `IntoIterator`
help: consider removing the leading `&`-reference
   |
16 -     for b in &s {
16 +     for b in s {
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277 — `&Shelf` is not an iterator** · `note:` 「required for `&Shelf` to implement `IntoIterator`」. **`&` 를 붙인다고 저절로 빌려 도는 게 아니다** — `&Shelf` 에 대한 **`impl` 이 있어야** 한다((3)).
- ★ `help:` 는 「**consider removing the leading `&`-reference**」— 따라 하면:

```rust
// r37_own_missing_help.rs
// 값 구현 하나만 — help: 대로 & 를 뺐다
struct Shelf {
    books: Vec<String>,
}

impl IntoIterator for Shelf {
    type Item = String;
    type IntoIter = std::vec::IntoIter<String>;
    fn into_iter(self) -> Self::IntoIter {
        self.books.into_iter()
    }
}

fn main() {
    let s = Shelf { books: vec![String::from("dune")] };
    for b in s {
        println!("{b}");
    }
}
```

```text
===== rustc --edition 2021 r37_own_missing_help.rs =====
(exit 0)
===== ./r37_own_missing_help =====
dune
(exit 0)
```

- ★★ **통과한다**(`dune`). 그런데 이제 **`s` 를 옮겨 버린다** — 이 뒤에 `s` 를 쓰면 (1)의 첫 줄처럼 E0382 다.
  **「빌려 돌고 싶다」는 뜻이면 이 처방은 틀렸다** — 맞는 처방은 **`impl IntoIterator for &Shelf` 를 더하는 것**((6)의 첫 블록).

## 문법 — 형태와 규칙

```text
   형태

   for x in v          { … }      x: T        ← v 를 옮긴다. 뒤에 v 는 E0382
   for x in &v         { … }      x: &T       ← = v.iter()
   for x in &mut v     { *x … }   x: &mut T   ← = v.iter_mut(). 고칠 때 *x
   for (i, x) in v.iter().enumerate()          (usize, &T)
   for (k, n) in &m / &mut m / m               (&K, &V) / (&K, &mut V) / (K, V)

   impl IntoIterator for MyT          { type Item = T;        … }   ← 값
   impl<'a> IntoIterator for &'a MyT  { type Item = &'a T;    … }   ← 빌려 읽기
   impl<'a> IntoIterator for &'a mut MyT { type Item = &'a mut T; … } ← 빌려 고치기


   금지 사례 — 던져서 받은 것 (번호만)

   let it = v.into_iter();  v.len()          ✘ E0382   (help: v.clone().into_iter() — 통과하지만 복제)
   for x in &mut v { x *= 10; }              ✘ E0368   (help: *x *= 10 — 맞다)
   for b in &s  (impl 이 값 쪽 하나뿐)          ✘ E0277   (help: & 를 빼라 — 통과하지만 s 를 옮긴다)

   에디션이 뜻을 바꾸는 자리 — 컴파일은 된다

   [1, 2, 3].into_iter()           2015·2018 &i32  │  2021·2024 i32
   boxed_slice.into_iter()         2015~2021 &i32  │  2024 i32
   for x in arr / IntoIterator::into_iter(arr)     전 에디션 i32
```

**규칙 불릿.**

- ★★★ **`for x in E` 는 `IntoIterator::into_iter(E)`** — 나오는 것은 **`E` 의 타입에 달린 `impl`** 이 정한다((3)).
- ★★ **값 → `T` 이고 원본을 옮긴다 · `&` → `&T` · `&mut` → `&mut T`**((1)). `iter`/`iter_mut`/`into_iter` 는 같은 셋의 메서드 이름이다.
- ★★ **배열·`Box<[T]>` 의 `.into_iter()` 는 에디션에 달렸다** — 헷갈리면 **`for x in a`** 나 **`.iter()`** 로 뜻을 적어라((2)).
- ★ **내 타입은 `impl` 셋을 직접 쓴다** — 하나가 빠지면 그 형태만 E0277((6)).

## 어디서 틀리나

### 1. ★★★ 「`for x in v` 뒤에도 `v` 를 쓸 수 있다」

**E0382**((1)) — `for` 가 **`into_iter()`** 를 불러 `v` 를 옮겼다. 남기려면 **`&v`**. ★ 원소가 `Copy`(`i32`)여도 **똑같다**((1)의 `r37_copy`) — 옮겨지는 것은 `Vec` 자체다.

### 2. ★★★ 「`.into_iter()` 는 항상 원소를 값으로 준다」

**배열은 2018 까지, `Box<[T]>` 는 2021 까지 `&T`** 다((2)). **소스가 같아도 에디션이 다르면 타입이 다르다** — 그리고 **컴파일은 된다.** 옛 에디션에서는 경고 한 줄이 유일한 신호다.

### 3. ★★ 「`&` 를 붙이면 무엇이든 빌려서 돈다」

**`&T` 에 대한 `impl IntoIterator` 가 있어야** 한다((6)). 내 타입에 값 구현만 두면 `for b in &s` 는 **E0277**. 그리고 그 `help:`(「`&` 를 빼라」)는 **빌림을 이동으로 바꾸는** 처방이다.

### 4. ★★ 「`&mut` 로 돌면 `x` 가 원소 자체다」

**`x` 는 `&mut T` 다** — 고칠 때 **`*x`**. 빠뜨리면 **E0368**((4)).

### 5. ★ 「`help:` 대로 `clone()` 하면 해결」

**통과는 한다** — 원소를 **전부 복제**해서((4)). 원본을 남기고 **읽기만** 할 거면 `iter()` 가 맞다. `help:` 스스로 「원하는 동작이 아닐 수도」라고 적는다.

### 6. ★ 「`HashMap` 을 `&mut` 로 돌면 키도 고칠 수 있다」

**`(&K, &mut V)`** 다((5)) — 키는 읽기만. 키를 바꾸면 해시가 어긋나기 때문이다(std 모듈 문서).

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ `for` 의 **`IntoIterator::into_iter` 탈당** | ★ **언어 보장** — Reference(`for` 의 탈당) · std 모듈 문서의 탈당 예 | (1)의 E0382 · (4)의 「implicit call」(36편) |
| ★★ `Vec` 의 **`impl` 셋과 `Item`** | ★ **std 의 공개 API** — 문서에 구현 목록으로 실린다. `&Vec` 쪽이 `iter()` 를 부르는 **몸통**은 소스의 한 줄이다 | (3)의 소스 블록 |
| ★★★ **배열·`Box<[T]>` 의 `.into_iter()` 에디션 차이** | ★ **에디션 보장** — Edition Guide 2021·2024 절 | (2)의 격자 `2 / 6` |
| `iter()` 와 `for x in &v` 가 **같은 것** | ★ **std 의 관례** — 모듈 문서 「**보통**(usually)」·「**대개**(generally)」. 모든 타입의 약속이 아니다 — **내 타입은 내가 정한다**((6)) | (1)·(3) |
| `HashMap` 의 `&mut` 순회가 **키를 `&K` 로** 주는 것 | ★ **std 의 API** — `IterMut` 의 `Item` 이 `(&K, &mut V)` | (5) |
| `type_name_of_val` 문자열 | ★ **구현 세부** — std 가 형식을 보장하지 않는다 | (1)·(2)·(5) |
| std 소스의 **줄 번호**·`ManuallyDrop` 몸통 | ★ **구현 세부** — 판마다 바뀐다 | (3) |
| `help:` 처방의 문구·내용 | ★ **구현 세부** — 진단의 제안. **맞은 것(E0368)·과한 것(E0382)·뜻을 바꾼 것(E0277)이 섞였다** | (4)·(6) |

## 언제 쓰고 언제 안 쓰나

- ★★ **읽기만 — `for x in &v`**(또는 `v.iter()`). 원본이 남는다. **기본값으로 둔다.**
- ★★ **고치기 — `for x in &mut v`**(또는 `v.iter_mut()`), 몸통에서 **`*x`**.
- ★ **원본이 더 필요 없고 원소를 가져가야 할 때만 — `for x in v`**(또는 `v.into_iter()`). 원소를 다른 컬렉션으로 **옮길 때**(`extend`)가 대표다.
- ★★ **배열·`Box<[T]>` 에는 `.into_iter()` 대신 뜻이 에디션을 안 타는 꼴을** — 값이면 `for x in a`, 빌림이면 `.iter()`((2)).
- ★ **내 컬렉션 타입은 `impl` 셋을 다 쓴다** — 쓰는 쪽이 세 형태를 기대한다((6)).

## 핵심 문장

- ★★★ **`for x in E` 는 `IntoIterator::into_iter(E)` — 값이면 옮기고, `&` 면 빌려 읽고, `&mut` 면 빌려 고친다**((1) 격자 `2 / 6`).
- ★★ **`for x in &v` 가 되는 것은 문법이 아니라 std 의 `impl IntoIterator for &Vec` 이고, 그 몸통이 `self.iter()` 한 줄이다**((3)).
- ★★★ **배열의 `.into_iter()` 는 2021 부터, `Box<[T]>` 는 2024 부터 `T` — 같은 소스가 에디션에 따라 `&i32` 와 `i32` 로 갈린다**((2) 격자 `2 / 6`).
- ★ **`help:` 셋 중 하나만 뜻에 맞았다** — `*x`(맞다) · `clone()`(과하다) · `&` 빼기(빌림을 이동으로 바꾼다)((4)·(6)).

## 관련 자료

- [**36번 주제** — `Iterator`·어댑터·게으름·`collect`](../36-iterator-adapters-laziness-and-collect/) — **경계**: 어댑터·게으름·`collect` 는 거기. 그 편 (6)의 셋 한 칸과 「더 들어가면」의 배열 한 쌍을 여기서 **격자로 넓혔다.**
- [**34번 주제** — 클로저와 `move`](../34-closures-fn-fnmut-fnonce-and-move/) (6) — **같은 2018 → 2021 경계**의 다른 얼굴(정밀 포착 3 / 3). (2)의 에디션 표.
- [**32번 주제** — `impl Trait` 와 2024 포착](../32-impl-trait-argument-return-position-and-2024-capture/) (5) — **2021 → 2024 경계**의 다른 얼굴.
- [**08번 주제** — 소유권과 이동](../08-ownership-and-move/) · [**10번 주제** — 빌림](../10-borrowing-and-aliasing-rules/) — E0382 와 `&`/`&mut` 의 뿌리.
- [**25번 주제** — 트레이트·연관 타입](../25-traits-definition-impl-default-methods-and-associated-types/) — `type Item`·`type IntoIter`.
- [**38번 주제** — `Vec<T>` API](../38-vec-api-capacity-retain-and-drain/) — 이 주제의 **다음 사슬**. 순회 **중에** `Vec` 을 고치면 무엇이 막히나.
- [**39번 주제** — `HashMap` 대 `BTreeMap`](../39-hashmap-vs-btreemap-and-entry-api/) — (5)에서 피한 **순회 순서**가 거기서 본체가 된다.
- 목록의 **47번 주제** — 에디션 2021 대 2024. (2)의 표가 그 입구다.
- Python 갈래의 [**16번**](../../../python/syntax/16-iterator-protocol/) — 이터레이터 프로토콜. 파이썬의 `for` 는 **리스트를 소비하지 않는다**(돈 뒤에도 리스트가 그대로다 — 소진되는 것은 `iter()` 가 만든 이터레이터 쪽) — Rust 의 「값으로 넘기면 원본이 없어진다」와 대비. 이 문서는 파이썬을 던지지 않았다.

## 용어 풀이

- **`IntoIterator`** — 이터레이터로 바뀔 수 있는 타입의 트레이트. `for` 가 이것을 부른다.
- **`iter()`** — `&T` 를 내놓는 이터레이터. 원본을 빌린다.
- **`iter_mut()`** — `&mut T` 를 내놓는 이터레이터. 원본을 빌려 고친다.
- **`into_iter()`** — `IntoIterator` 의 메서드. **받는 쪽 타입**에 따라 `T`·`&T`·`&mut T` 중 무엇이든 될 수 있다.
- **탈당(desugaring)** — `for x in E` → `IntoIterator::into_iter(E)` + `loop { match next() … }`.
- **에디션(edition)** — 크레이트마다 고르는 언어 판. 2015·2018·2021·2024.
- **이전 린트(migration lint)** — 에디션을 올리면 뜻이 바뀔 자리를 미리 경고하는 린트. `array_into_iter` · `boxed_slice_into_iter`.
- **`type_name_of_val`** — 값의 타입 이름을 문자열로 주는 std 함수(1.76~). 형식은 보장되지 않는다.

## 더 들어가면

- **`extend` 는 `into_iter()` 를 부른다** — std 모듈 문서 「`extend` 는 자동으로 `into_iter` 를 부르고 `T: IntoIterator` 면 무엇이든 받는다」. 그래서 `a.extend(b)` 는 `b` 를 옮기고 `a.extend(&b)` 는 (`Copy` 원소면) 복사한다(이 문서는 던지지 않았다).
- **`IntoIterator` 를 인자 경계로** — `fn f(xs: impl IntoIterator<Item = i32>)` 로 받으면 `Vec`·배열·범위·이터레이터를 **다 받는다.** [**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/)의 인자 위치 `impl Trait` 와 이어진다.
- **`Iterator` 는 `IntoIterator` 다** — std 가 `impl<I: Iterator> IntoIterator for I` 를 둔다. 그래서 `for x in v.iter()` 가 된다(`into_iter` 가 자기 자신을 돌려준다).
- **`drain(..)`** — 「옮겨 가지되 **`Vec` 은 남기는**」 넷째 길. [**38번 주제**](../38-vec-api-capacity-retain-and-drain/)에서 본다.
