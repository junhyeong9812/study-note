# rust/syntax/37 — `IntoIterator` 세 형태 — `iter`/`iter_mut`/`into_iter` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **블록마다 배너에 적은 `--edition`** 으로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 셋씩 짝 — 값으로 넘긴 둘만 E0382 · `2 / 6`

**출력.**

```text
===== 소스: r37_grid.sh =====
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

**왜 그런가.**

- ★★★ **`for x in v` · `v.into_iter()` → `String` · E0382** / **`for x in &v` · `v.iter()` → `&String` · `ok`** / **`for x in &mut v` · `v.iter_mut()` → `&mut String` · `ok`.** 마지막 줄 **`2 / 6`**.
- ★★ **짝** — `v` ↔ `v.into_iter()` · `&v` ↔ `v.iter()` · `&mut v` ↔ `v.iter_mut()`. 짝끼리 **타입도 칸도 한 글자도 같다**(7번 — 같은 함수를 부른다).
- ★ E0382 칸은 **값으로 넘긴 칸**뿐이다. `for` 가 `IntoIterator::into_iter(v)` 를 불러 `Vec` 을 **옮겼다.**

### 2. ★★ 메서드 꼴 두 줄만 바뀐다 — 배열은 2021, `Box<[i32]>` 는 2024

**출력.**

```text
===== 소스: r37_ed_grid.sh =====
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

**왜 그런가.**

- ★★★ **바뀐 줄 `2 / 6`** — 둘 다 **`a.into_iter()` 메서드 꼴**이다.
  배열은 **2015·2018 `&i32` → 2021·2024 `i32`**(경계 2018 → 2021), `Box<[i32]>` 는 **2015·2018·2021 `&i32` → 2024 `i32`**(경계 2021 → 2024). **같은 경계가 아니다.**
- ★★ `IntoIterator::into_iter(a)` 와 `for x in a` 는 **네 에디션 전부 `i32`** — 구현은 전 에디션에 있고, 옛 에디션은 **메서드 꼴만** `(&a).into_iter()` 로 푼다(8번).
- ★ 2021 의 `Box<[i32]>` 쪽은 **경고**가 붙는다(서머리 (2)의 `r37_boxslice21` — `boxed_slice_into_iter`, 「this changes meaning in Rust 2024」).

### 3. ★ E0382 — `Copy` 가 아닌 것은 `Vec` 이다

**출력.**

```text
===== 소스: r37_copy.rs =====
// 원소가 Copy 인 i32 일 때
fn main() {
    let v = vec![1, 2];
    for x in v {
        let _ = x;
    }
    println!("{}", v.len());
}
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

- ★★ **E0382.** 「move occurs because `v` has type **`Vec<i32>`**, which does not implement the `Copy` trait」 — 원소 `i32` 가 `Copy` 여도 **`Vec` 은 `Copy` 가 아니고, 옮겨진 것은 `Vec`** 이다.

### 4. ★★ E0368 — `*x` 로 (이 `help:` 는 맞다)

**출력.**

```text
===== 소스: r37_mut.rs =====
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &mut v {
        x *= 10;
    }
    println!("{v:?}");
}
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

**출력 — `help:` 대로 `*x`.**

```text
===== 소스: r37_mut_fix.rs =====
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &mut v {
        *x *= 10;
    }
    println!("{v:?}");
}
===== rustc --edition 2021 r37_mut_fix.rs =====
(exit 0)
===== ./r37_mut_fix =====
[10, 20, 30]
(exit 0)
```

- ★★ **E0368** — `x` 는 `&mut {integer}` 라 `*=` 가 안 된다. `help:` 「**`*x *= 10`**」 — 따르면 **`[10, 20, 30]`**. 이 처방은 **맞았다.**

### 5. ★★ `(usize, &char)` · `(&String, &i32)` · `(&String, &mut i32)` · `(String, i32)`

**출력.**

```text
===== 소스: r37_pairs.rs =====
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

- ★★ **`[1]` `usize , &char`** — `enumerate` 는 번호(값)를 얹을 뿐 원소는 `iter()` 의 `&char` 그대로.
- ★★ **`[2]` `&alloc::string::String , &i32`** · **`[3]` `&alloc::string::String , &mut i32`** · **`[4]` `alloc::string::String , i32`** — `&m` / `&mut m` / `m` 이 (1)의 세 형태를 **짝 단위로** 그대로 따른다.
- ★ **`[3]` 의 키가 `&String` 인 이유** — 키를 고치면 **해시가 바뀌어** 맵이 어긋나기 때문이다. std 모듈 문서가 「`HashSet<T>` 의 키를 고치면 해시가 바뀌어 컬렉션이 **일관되지 않은 상태**가 될 수 있어 **`iter()` 만** 준다」고 적는다. 맵은 **값만** `&mut` 로 준다.

### 6. ★★ E0277 — `help:` 대로 하면 통과하지만 뜻이 바뀐다

**출력.**

```text
===== 소스: r37_own_missing.rs =====
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

**출력 — `help:` 대로 `&` 를 빼면.**

```text
===== 소스: r37_own_missing_help.rs =====
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
===== rustc --edition 2021 r37_own_missing_help.rs =====
(exit 0)
===== ./r37_own_missing_help =====
dune
(exit 0)
```

- ★★ **E0277 — `&Shelf` is not an iterator** · 「required for `&Shelf` to implement `IntoIterator`」. `&Shelf` 에 대한 `impl` 이 **없다.**
- ★★ **`help:` 대로 `for b in s` 로 바꾸면 통과**(`dune`) — 그러나 **`s` 를 옮긴다.** 빌려 돌려는 뜻이면 **틀린 처방**이고, 맞는 처방은 **`impl<'a> IntoIterator for &'a Shelf` 를 더하는 것**이다(서머리 (6)의 `r37_own` — 세 형태가 다 된다).

### 7. ★★★ 적힌 코드다 — std 의 `impl` 셋, `&Vec` 쪽 몸통은 `self.iter()`

**출력.**

```text
===== 소스: r37_impls.py =====
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

- ★★★ **문법 규칙이 아니라 std 의 `impl` 셋**이다 — `for Vec<T, A>`(3694) · `for &'a Vec<T, A>`(3733) · `for &'a mut Vec<T, A>`(3743).
- ★★ **`&Vec` 쪽 `into_iter` 의 몸통은 `self.iter()` 한 줄**(3738), `&mut Vec` 쪽은 `self.iter_mut()`(3748). 그래서 1번의 짝이 한 글자도 같다.
- ★ `Item` 줄 — `T` · `&'a T` · `&'a mut T` — 이 1번 `type of x` 칸의 출처다.

### 8. ★★ 차이는 「메서드 호출 꼴의 해석」에 산다 — 구현은 에디션을 섞는 크레이트끼리 공유된다

- ★★ **구현은 하나이고 전 에디션에 있다** — 차이는 **컴파일러가 옛 에디션의 `a.into_iter()` 메서드 꼴을 `(&a).into_iter()` 로 푸는 것**에만 산다(2번의 격자 — 다른 두 꼴은 전 에디션 `i32`).
- ★★ **따로 못 둔 이유** — Edition Guide: 「**트레이트 구현이 한 에디션에는 있고 다른 에디션에는 없게 할 수는 없다. 에디션은 섞일 수 있기 때문이다**」. 2018 크레이트와 2021 크레이트가 한 프로그램에 링크되면 **구현은 하나**여야 한다.
- ★ 왜 굳이 그렇게 했나 — 1.53 전에 이미 `array.into_iter()` 가 (자동 참조로) **`(&array).into_iter()` 로 컴파일되던 코드가 너무 많아서**, 그대로 구현을 더하면 그 코드들의 뜻이 **조용히** 바뀌었을 것이다(같은 문서).

### 9. ★ E0382 — `clone()` 은 통과하지만 원본을 남기려면 `iter()`

**출력.**

```text
===== 소스: r37_move.rs =====
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    let it = v.into_iter();
    println!("{}", it.count());
    println!("{}", v.len());
}
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

**출력 — `help:` 대로 `clone()`.**

```text
===== 소스: r37_move_help.rs =====
fn main() {
    let v = vec![String::from("a"), String::from("b")];
    let it = v.clone().into_iter();
    println!("{}", it.count());
    println!("{}", v.len());
}
===== rustc --edition 2021 r37_move_help.rs =====
(exit 0)
===== ./r37_move_help =====
2
2
(exit 0)
```

- ★ **E0382** — 「`v` moved due to this method call」 · `note:` 「**`into_iter` takes ownership of the receiver `self`**」.
- ★ `help:` 의 `v.clone().into_iter()` 는 **통과**(`2` · `2`) — 대신 **원소를 전부 복제**한다(`help:` 스스로 「might not be your desired behavior」). **읽기만** 할 거면 **`v.iter()`** — 복제 없이 원본이 남는다(1번의 `ok` 칸).

### 10. ★★ 배열 쪽이 34편과 같은 2018 → 2021 — 공통점은 「컴파일은 되는데 뜻이 바뀐다」

| 경계 | 무엇이 바뀌나 | 어디서 쟀나 |
|---|---|---|
| **2018 → 2021** | 배열의 `.into_iter()` — `&T` → `T` | 이 편 2번 |
| **2018 → 2021** | 클로저 포착 — 변수 통째 → 쓴 자리만 | [34번 주제](../34-closures-fn-fnmut-fnonce-and-move/) (6) — 바뀐 소스 **3 / 3** |
| **2021 → 2024** | `Box<[T]>` 의 `.into_iter()` — `&T` → `T` | 이 편 2번 |
| **2021 → 2024** | 반환 위치 `impl Trait` 의 수명 포착 | [32번 주제](../32-impl-trait-argument-return-position-and-2024-capture/) (5) |

- ★★ **배열의 `.into_iter()` 와 클로저 정밀 포착이 같은 2018 → 2021 경계**에서 바뀌었다. `Box<[T]>` 는 **한 에디션 늦게**(2021 → 2024) 같은 길을 걸었다.
- ★★ **공통점 — 같은 소스가 양쪽 에디션에서 다 컴파일된다.** 에러로는 안 드러나고 **값·타입·드롭 시점**만 바뀐다. 그래서 에디션을 올리기 전에 **이전 린트**(`array_into_iter` · `boxed_slice_into_iter` · 34편의 포착 린트)가 경고로 먼저 알린다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **여섯 형태 격자** | `r37_grid.sh` — 형태마다 소스 두 벌을 만들어 컴파일·실행 | 1 | **`2 / 6`** — 값으로 넘긴 두 칸만 E0382 |
| ★★ **에디션 격자** | `r37_ed_grid.sh` — 여섯 소스 × 2015·2018·2021·2024 | 1(24 컴파일) | **`2 / 6`** — 배열 2018→2021 · `Box<[i32]>` 2021→2024 |
| `Box<[T]>` 경고 | `r37_boxslice` 를 2021·2024 로 | 2 | 경고 + `&i32` · 경고 없이 `i32` |
| ★★ std 소스의 `impl` 셋 | `r37_impls.py` — 설치된 `rust-docs` 소스 페이지 | 1 | 3694 · 3733 · 3743 줄 |
| 진단 | `r37_copy` · `r37_move` · `r37_mut` · `r37_own_missing` | 4 | **E0382 · E0382 · E0368 · E0277** |
| `help:` 따라 하기 | `r37_move_help` · `r37_mut_fix` · `r37_own_missing_help` | 3 | 통과(복제) · 통과(맞다) · 통과(**뜻이 바뀐다**) |
| 짝 항목 | `r37_pairs` · `r37_own` | 2 | `(usize, &char)` 등 · 세 `impl` |
| **안 던진 것** — 속도 · `extend` 의 이동 · 파이썬 대비 · 옛 rustc 판 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| std 소스의 **줄 번호**와 `Vec` 값 쪽 몸통 | ★ 판마다 움직인다 |
| `type_name_of_val` 문자열 | ★ std 가 형식을 보장하지 않는다 |
| `help:`·경고 문구 | ★ 진단의 제안은 판마다 바뀐다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
