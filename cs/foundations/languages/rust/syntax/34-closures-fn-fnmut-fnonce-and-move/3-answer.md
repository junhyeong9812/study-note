# rust/syntax/34 — 클로저 세 종류 `Fn`/`FnMut`/`FnOnce`와 `move` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **배너에 적은 `--edition`** 으로 실제로 돌려 받은 것이다(파이썬 블록은 `Python 3.12.3`).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 거절 칸 3 / 9 — 두 벌 모두, 계단 모양

**출력.**

```text
===== 소스: r34_grid.sh =====
# 클로저 몸통 셋 × 받는 함수 셋 — 컴파일러가 칸마다 받나 거절하나
# 두 벌로 던진다: inline = 부르는 자리에 클로저를 바로 쓴다 · let = 변수에 묶었다가 넘긴다
# 칸: 통과면 ok, 에러면 진단 코드
bodies=(
  'read|println!("{}", s.len())'
  'mutate|s.push(1)'
  'give_away|drop(s)'
)
needs=(Fn FnMut FnOnce)
for layout in inline let; do
  rejected=0 total=0
  echo "== $layout"
  printf '%-10s | %-6s | %-6s | %s\n' body Fn FnMut FnOnce
  for b in "${bodies[@]}"; do
    name=${b%%|*} body=${b#*|} line=""
    for t in "${needs[@]}"; do
      if [ $layout = inline ]; then
        call="need(|| $body);"
      else
        call="let c = || $body;
    need(c);"
      fi
      printf 'fn need(f: impl %s()) {\n    let _ = f;\n}\nfn main() {\n    let mut s = vec![0u8];\n    %s\n}\n' "$t" "$call" >g.rs
      if rustc --edition 2021 -A warnings --crate-name g g.rs -o g 2>g.err; then
        c=ok
      else
        c=$(grep -m1 -oE '^error\[E[0-9]+\]' g.err | sed -E 's/error\[(.*)\]/\1/')
        rejected=$((rejected + 1))
      fi
      total=$((total + 1))
      line+=$(printf ' | %-6s' "$c")
    done
    printf '%-10s%s\n' "$name" "$line"
  done
  echo "rejected cells ($layout): $rejected / $total"
done
rm -f g.rs g.err g
===== bash r34_grid.sh =====
== inline
body       | Fn     | FnMut  | FnOnce
read       | ok     | ok     | ok    
mutate     | E0596  | ok     | ok    
give_away  | E0507  | E0507  | ok    
rejected cells (inline): 3 / 9
== let
body       | Fn     | FnMut  | FnOnce
read       | ok     | ok     | ok    
mutate     | E0525  | ok     | ok    
give_away  | E0525  | E0525  | ok    
rejected cells (let): 3 / 9
(exit 0)
```

**왜 그런가.**

| | `Fn` | `FnMut` | `FnOnce` |
|---|---|---|---|
| 읽기 `s.len()` | ✔ | ✔ | ✔ |
| 고치기 `s.push(1)` | ✘ E0596 / E0525 | ✔ | ✔ |
| 옮기기 `drop(s)` | ✘ E0507 / E0525 | ✘ E0507 / E0525 | ✔ |

- ★★★ **두 표 다 `rejected cells 3 / 9`.** ✔/✘ 는 **한 칸도 안 다르고**, 다른 것은 **번호**뿐이다(`inline` 은 E0596·E0507, `let` 은 E0525).
- ★★ **계단** — **`FnOnce` 열은 전부 받고 `Fn` 열은 읽기만 받는다.** Reference: 모든 클로저는 `FnOnce`, **옮기지 않으면** `FnMut`, **고치지도 옮기지도 않으면** `Fn`.

### 2. ★★ E0525 는 클로저를, E0596 은 시그니처를 짚는다

**출력 — 변수에 묶었다가.**

```text
===== 소스: r34_let_mut.rs =====
// 변수에 묶은 클로저를 impl Fn 자리에
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    let c = || s.push(1);
    need_fn(c);
}
===== rustc --edition 2021 r34_let_mut.rs =====
error[E0525]: expected a closure that implements the `Fn` trait, but this closure only implements `FnMut`
 --> r34_let_mut.rs:8:13
  |
8 |     let c = || s.push(1);
  |             ^^ - closure is `FnMut` because it mutates the variable `s` here
  |             |
  |             this closure implements `FnMut`, not `Fn`
9 |     need_fn(c);
  |     ------- - the requirement to implement `Fn` derives from here
  |     |
  |     required by a bound introduced by this call
  |
note: required by a bound in `need_fn`
 --> r34_let_mut.rs:2:20
  |
2 | fn need_fn(f: impl Fn()) {
  |                    ^^^^ required by this bound in `need_fn`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0525`.
(exit 1)
```

**출력 — 부르는 자리에 바로.**

```text
===== 소스: r34_inline_mut.rs =====
// 같은 클로저를 부르는 자리에 바로 쓰면
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    need_fn(|| s.push(1));
}
===== rustc --edition 2021 r34_inline_mut.rs =====
error[E0596]: cannot borrow `s` as mutable, as it is a captured variable in a `Fn` closure
 --> r34_inline_mut.rs:8:16
  |
2 | fn need_fn(f: impl Fn()) {
  |               --------- change this to accept `FnMut` instead of `Fn`
...
8 |     need_fn(|| s.push(1));
  |     ------- -- ^ cannot borrow as mutable
  |     |       |
  |     |       in this closure
  |     expects `Fn` instead of `FnMut`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
(exit 1)
```

**왜 그런가.**

- ★★ **앞은 E0525** — 「expected a closure that implements the `Fn` trait, but this closure only implements `FnMut`」. **클로저 몸통**(「mutates the variable `s` here」)과 **요구가 온 자리**를 짚는다.
- ★★ **뒤는 E0596** — 「cannot borrow `s` as mutable, as it is a captured variable in a `Fn` closure」. `help:` 가 **`need_fn` 의 시그니처**(「change this to accept `FnMut` instead of `Fn`」)를 짚는다.
- ★ **추론의 순서** — `let c = || …` 는 **몸통만 보고 종류가 먼저** 정해지고(`FnMut`) 나중에 요구와 부딪힌다. 인자 자리에 바로 쓰면 **기대(`Fn`)가 먼저** 닿아 클로저를 `Fn` 으로 두고 **몸통을 탓한다.** 어느 번호를 내는지는 **진단의 선택(구현)** 이고, 거절 자체는 **언어 규칙**이다.

### 3. ★★★ `move` 해도 `Fn` 이다 — 바뀌는 것은 바깥

**출력 — 읽기만 하는 `move` 클로저.**

```text
===== 소스: r34_move_fn.rs =====
// move 로 잡았지만 읽기만 하는 클로저
fn need_fn(f: &impl Fn() -> usize) -> usize {
    f() + f()
}

fn main() {
    let s = String::from("abc");
    let c = move || s.len();
    println!("{}", need_fn(&c));
    println!("{}", c());
}
===== rustc --edition 2021 r34_move_fn.rs =====
(exit 0)
===== ./r34_move_fn =====
6
3
(exit 0)
```

**출력 — 그 뒤 원래 변수를 쓰면.**

```text
===== 소스: r34_move_after.rs =====
// move 로 잡은 뒤 원래 변수를 쓰면
fn main() {
    let s = String::from("abc");
    let c = move || s.len();
    println!("{}", c());
    println!("{}", s);
}
===== rustc --edition 2021 r34_move_after.rs =====
error[E0382]: borrow of moved value: `s`
 --> r34_move_after.rs:6:20
  |
3 |     let s = String::from("abc");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
4 |     let c = move || s.len();
  |             ------- - variable moved due to use in closure
  |             |
  |             value moved into closure here
5 |     println!("{}", c());
6 |     println!("{}", s);
  |                    ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value before moving it into the closure
  |
4 ~     let value = s.clone();
5 ~     let c = move || value.len();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**왜 그런가.**

- ★★★ **앞은 통과 — `6` · `3`.** `&impl Fn` 으로 받아 **두 번** 부르고 밖에서 **또** 불렀다 — **`Fn`** 이다(그러니 `FnMut`·`FnOnce` 도 된다).
- ★★ **뒤는 E0382** — 「borrow of moved value: `s`」, 「**value moved into closure here**」. 클로저는 멀쩡히 불리고 **`s` 가 클로저 안으로 옮겨졌다.**
- ★★★ **「`move` 면 `FnOnce`」는 틀리다.** Reference 의 Note — 「**`move` 클로저도 `Fn`·`FnMut` 을 구현할 수 있다. 트레이트는 잡은 값으로 무엇을 하느냐로 정해지지, 어떻게 잡느냐로 정해지지 않는다.**」

### 4. ★★ E0373 — `'static` 이 요구다, `move` 로 풀린다

**출력.**

```text
===== 소스: r34_thread.rs =====
// 스레드에 클로저를 넘긴다
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let h = thread::spawn(|| v.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r34_thread.rs =====
error[E0373]: closure may outlive the current function, but it borrows `v`, which is owned by the current function
 --> r34_thread.rs:6:27
  |
6 |     let h = thread::spawn(|| v.len());
  |                           ^^ - `v` is borrowed here
  |                           |
  |                           may outlive borrowed value `v`
  |
note: function requires argument type to outlive `'static`
 --> r34_thread.rs:6:13
  |
6 |     let h = thread::spawn(|| v.len());
  |             ^^^^^^^^^^^^^^^^^^^^^^^^^
help: to force the closure to take ownership of `v` (and any other referenced variables), use the `move` keyword
  |
6 |     let h = thread::spawn(move || v.len());
  |                           ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0373`.
(exit 1)
```

**출력 — `help:` 대로 `move`.**

```text
===== 소스: r34_thread_move.rs =====
// help: 가 권한 대로 move 를 붙이면
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let h = thread::spawn(move || v.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r34_thread_move.rs =====
(exit 0)
===== ./r34_thread_move =====
3
(exit 0)
```

- ★★ **E0373** — 「closure may outlive the current function, but it borrows `v`」. `note:` 가 요구를 적는다 — 「**function requires argument type to outlive `'static`**」.
- ★ **`help:` 대로 `move` 를 붙이면 통과 — `3`.** 이 처방은 **맞았다.** 몸통은 여전히 읽기뿐이라 **여전히 `Fn`** 이다.

### 5. ★★ 0 · 8 · 16 · 4 · 8 · 24 — 보장은 아니다

**출력.**

```text
===== 소스: r34_size.rs =====
// 클로저 하나는 몇 바이트인가 — 무엇을 어떻게 잡았나에 따라
use std::mem::size_of_val;

fn main() {
    let n: i32 = 7;
    let m: i32 = 8;
    let s = String::from("abc");
    let none = || 1;
    let by_ref = || n + 1;
    let two_refs = || n + m;
    let by_move = move || n + 1;
    let string_ref = || s.len();
    println!("none        {}", size_of_val(&none));
    println!("by_ref      {}", size_of_val(&by_ref));
    println!("two_refs    {}", size_of_val(&two_refs));
    println!("by_move     {}", size_of_val(&by_move));
    println!("string_ref  {}", size_of_val(&string_ref));
    let string_move = move || s.len();
    println!("string_move {}", size_of_val(&string_move));
    println!("{}", none() + by_ref() + two_refs() + by_move() + string_move() as i32);
}
===== rustc --edition 2021 r34_size.rs =====
(exit 0)
===== ./r34_size =====
none        0
by_ref      8
two_refs    16
by_move     4
string_ref  8
string_move 24
35
(exit 0)
```

- ★★ **`none` 0 · `by_ref` 8 · `two_refs` 16 · `by_move` 4 · `string_ref` 8 · `string_move` 24.** 잡은 것이 **참조면 8 씩**, **값이면 그 값의 크기**다.
- ★ **`by_ref` 는 `i32` 인데도 8** — `n + 1` 은 읽기뿐이라 **불변 빌림**으로 잡혔다(Reference 「Copy 값도 불변 빌림으로」). `move` 를 붙인 `by_move` 만 **4**.
- ★★ **보장이 아니다** — Reference 「**Closures have no layout guarantees**」. 이 판의 관찰이다.

### 6. ★★★ 3 / 3 — 전부 2018 과 2021 사이

**출력.**

```text
===== 소스: r34_ed_grid.sh =====
# 세 소스를 에디션 넷으로 — 칸: 통과면 실행 출력(한 줄로), 에러면 진단 코드
changed=0
printf '%-16s | %-22s | %-22s | %-22s | %s\n' source 2015 2018 2021 2024
for f in r34_dj_borrow r34_dj_size r34_dj_after; do
  row=()
  for e in 2015 2018 2021 2024; do
    if rustc --edition $e -A warnings $f.rs -o $f.$e 2>$f.err; then
      row+=("$(./$f.$e | paste -sd '/')")
    else
      row+=("$(grep -m1 -oE '^error\[E[0-9]+\]' $f.err | sed -E 's/error\[(.*)\]/\1/')")
    fi
    rm -f $f.$e $f.err
  done
  printf '%-16s | %-22s | %-22s | %-22s | %s\n' $f "${row[@]}"
  [ "${row[1]}" != "${row[2]}" ] && changed=$((changed + 1))
done
echo "sources whose cell changes between 2018 and 2021: $changed / 3"
===== bash r34_ed_grid.sh =====
source           | 2015                   | 2018                   | 2021                   | 2024
r34_dj_borrow    | E0506                  | E0506                  | kim/31                 | kim/31
r34_dj_size      | P 32, closure 32/3     | P 32, closure 32/3     | P 32, closure 24/3     | P 32, closure 24/3
r34_dj_after     | E0382                  | E0382                  | 3 30                   | 3 30
sources whose cell changes between 2018 and 2021: 3 / 3
(exit 0)
```

**출력 — 2018 의 전문 둘.**

```text
===== 소스: r34_dj_borrow.rs =====
// 클로저가 p.name 을 읽는 동안 p.age 를 고친다
struct P {
    name: String,
    age: u32,
}

fn main() {
    let mut p = P { name: String::from("kim"), age: 30 };
    let c = || println!("{}", p.name);
    p.age += 1;
    c();
    println!("{}", p.age);
}
===== rustc --edition 2018 r34_dj_borrow.rs =====
error[E0506]: cannot assign to `p.age` because it is borrowed
  --> r34_dj_borrow.rs:10:5
   |
 9 |     let c = || println!("{}", p.name);
   |             --                ------ borrow occurs due to use in closure
   |             |
   |             `p.age` is borrowed here
10 |     p.age += 1;
   |     ^^^^^^^^^^ `p.age` is assigned to here but it was already borrowed
11 |     c();
   |     - borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0506`.
(exit 1)
```

```text
===== 소스: r34_dj_after.rs =====
// move 클로저가 p.name 만 쓴 뒤 p.age 를 읽는다
struct P {
    name: String,
    age: u32,
}

fn main() {
    let p = P { name: String::from("kim"), age: 30 };
    let c = move || p.name.len();
    println!("{} {}", c(), p.age);
}
===== rustc --edition 2018 r34_dj_after.rs =====
error[E0382]: borrow of moved value: `p`
  --> r34_dj_after.rs:10:28
   |
 8 |     let p = P { name: String::from("kim"), age: 30 };
   |         - move occurs because `p` has type `P`, which does not implement the `Copy` trait
 9 |     let c = move || p.name.len();
   |             ------- ------ variable moved due to use in closure
   |             |
   |             value moved into closure here
10 |     println!("{} {}", c(), p.age);
   |                            ^^^^^ value borrowed here after move
   |
note: if `P` implemented `Clone`, you could clone the value
  --> r34_dj_after.rs:2:1
   |
 2 | struct P {
   | ^^^^^^^^ consider implementing `Clone` for this type
...
 9 |     let c = move || p.name.len();
   |                     ------ you could clone this value
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**왜 그런가.**

| | 2015 | 2018 | 2021 | 2024 |
|---|---|---|---|---|
| `r34_dj_borrow` | E0506 | E0506 | `kim` / `31` | `kim` / `31` |
| `r34_dj_size` 의 클로저 | 32 | 32 | **24** | **24** |
| `r34_dj_after` | E0382 | E0382 | `3 30` | `3 30` |

- ★★★ **세 소스 전부 2018 → 2021 에서 갈렸다**(2015 = 2018, 2021 = 2024). 2018 이하의 클로저는 **변수를 통째로** 잡고, 2021 부터 **쓴 자리(`p.name`)만** 잡는다(Reference · Edition Guide).
- ★★ **32 는 `P` 전체**(`String` 24 + `u32` 4 + 패딩 — 같은 줄의 `P 32`), **24 는 `String` 하나.** 크기가 원인을 그대로 말한다.
- ★ 2018 의 E0382 `note:` 는 「`P` 에 `Clone` 을 구현하면 복제할 수 있다」고 권한다 — **2021 로 올리면 필요 없는 처방**이다.

### 7. E0382 와 E0596 — 한 단어는 `mut`

**출력 — `FnOnce` 를 두 번.**

```text
===== 소스: r34_once_twice.rs =====
// FnOnce 인 클로저를 두 번 부르면
fn main() {
    let s = String::from("abc");
    let c = move || s;
    let a = c();
    let b = c();
    println!("{} {}", a, b);
}
===== rustc --edition 2021 r34_once_twice.rs =====
error[E0382]: use of moved value: `c`
 --> r34_once_twice.rs:6:13
  |
5 |     let a = c();
  |             --- `c` moved due to this call
6 |     let b = c();
  |             ^ value used here after move
  |
note: closure cannot be invoked more than once because it moves the variable `s` out of its environment
 --> r34_once_twice.rs:4:21
  |
4 |     let c = move || s;
  |                     ^
note: this value implements `FnOnce`, which causes it to be moved when called
 --> r34_once_twice.rs:5:13
  |
5 |     let a = c();
  |             ^

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

**출력 — `mut` 없는 `FnMut`.**

```text
===== 소스: r34_mut_binding.rs =====
// 고치는 클로저를 mut 없이 묶고 부르면
fn main() {
    let mut n = 0;
    let c = || n += 1;
    c();
    println!("{}", n);
}
===== rustc --edition 2021 r34_mut_binding.rs =====
error[E0596]: cannot borrow `c` as mutable, as it is not declared as mutable
 --> r34_mut_binding.rs:5:5
  |
4 |     let c = || n += 1;
  |                - calling `c` requires mutable binding due to mutable borrow of `n`
5 |     c();
  |     ^ cannot borrow as mutable
  |
help: consider changing this to be mutable
  |
4 |     let mut c = || n += 1;
  |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
(exit 1)
```

- ★★ **E0382 — use of moved value: `c`** — 「**closure cannot be invoked more than once because it moves the variable `s` out of its environment**」. **부르는 것이 `c` 를 소비한다.**
- ★ **E0596** — `FnMut` 은 `&mut self` 로 불리므로 **`let mut c`** 가 필요하다(`help:` 가 그대로 권한다).

### 8. 한 번이면 `FnOnce`, 여러 번이면 `FnMut`

- ★★ **한 번만 부르면 `FnOnce`** — 1번 답의 격자에서 **`FnOnce` 열이 전부 받는다.** 여러 번 부르면 **`FnMut`**(옮기기만 빠진다), **공유·동시에** 부르면 **`Fn`**.
- ★ **`Fn` 이 `FnMut` 자리에 들어가는 이유** — `&mut self` 로 부를 수 있는 자리면 **`&self` 로도 부를 수 있다**(가변 빌림을 쥐었으면 그것으로 읽기도 된다). 그래서 **`Fn` ⊂ `FnMut` ⊂ `FnOnce`** 자리 관계가 된다.

### 9. ★★ Rust `[0, 1, 2]` 또는 E0597 · 파이썬 `[2, 2, 2]`

**출력 — Rust, `move`.**

```text
===== 소스: r34_loop.rs =====
// 루프에서 클로저를 모은다 — 각 클로저는 어느 i 를 보나
fn main() {
    let mut fs: Vec<Box<dyn Fn() -> i32>> = Vec::new();
    for i in 0..3 {
        fs.push(Box::new(move || i));
    }
    let out: Vec<i32> = fs.iter().map(|f| f()).collect();
    println!("{:?}", out);
}
===== rustc --edition 2021 r34_loop.rs =====
(exit 0)
===== ./r34_loop =====
[0, 1, 2]
(exit 0)
```

**출력 — Rust, `move` 없이.**

```text
===== 소스: r34_loop_ref.rs =====
// move 없이 모으면
fn main() {
    let mut fs: Vec<Box<dyn Fn() -> i32>> = Vec::new();
    for i in 0..3 {
        fs.push(Box::new(|| i));
    }
    println!("{}", fs.len());
}
===== rustc --edition 2021 r34_loop_ref.rs =====
error[E0597]: `i` does not live long enough
 --> r34_loop_ref.rs:5:29
  |
4 |     for i in 0..3 {
  |         - binding `i` declared here
5 |         fs.push(Box::new(|| i));
  |         --               -- ^ borrowed value does not live long enough
  |         |                |
  |         |                value captured here
  |         borrow later used here
6 |     }
  |     - `i` dropped here while still borrowed

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
(exit 1)
```

**출력 — 파이썬.**

```text
===== 소스: r34_late.py =====
# 파이썬 — 루프에서 람다를 모은다. 각 람다는 어느 i 를 보나
fs = []
for i in range(3):
    fs.append(lambda: i)
print([f() for f in fs])
fs2 = [lambda i=i: i for i in range(3)]
print([f() for f in fs2])
===== python3 r34_late.py =====
[2, 2, 2]
[0, 1, 2]
(exit 0)
```

- ★★ **Rust** — `move` 면 회차마다 **그 회차의 `i` 를 복사**해 `[0, 1, 2]`. **`move` 를 빼면 E0597** — 클로저가 **회차 끝에 사라지는 `i` 를 빌린다.** 「전부 같은 변수를 본다」가 되기 전에 거절된다.
- ★★ **파이썬** — 람다가 **부를 때 `i` 를 읽는다**(늦은 바인딩) → 루프가 끝난 뒤의 `2`. 기본 인자로 박으면 `[0, 1, 2]`([Python 22번](../../../python/syntax/22-closures-and-late-binding/)).
- ★ **Go 1.22** — 루프 변수가 **회차마다 새 변수**가 되도록 **언어 판**을 바꿨다([Go 13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) — 이 문서는 다시 던지지 않았다).

### 10. ★ 수명 때문이다

- **수명.** 읽기뿐인 클로저는 **빌림으로** 잡히고 트레이트는 `Fn` 이다. `thread::spawn` 이 요구하는 것은 **`'static`**(그리고 `FnOnce`)이고, **빌림은 `'static` 이 아니다.** `move` 는 **소유를 옮겨** 수명 요구를 맞춘다 — 트레이트는 그대로 `Fn` 이다(4번 답).

### 11. 불변 여럿 = `Fn`, 가변 하나 = `FnMut`, 이동 = `FnOnce`

- ★★ **`Fn`** 은 `&self` 로 불린다 — **불변 빌림 여럿**처럼 여러 곳에서 동시에 불러도 된다. **`FnMut`** 은 `&mut self` — **가변 빌림 하나**처럼 한 번에 한 곳, 그리고 `let mut` 이 필요하다(7번 답).
- **`FnOnce`** 는 `self` — [08번](../08-ownership-and-move/)의 **이동**이다. 불렀으면 끝이다(E0382).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 `--edition` 을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — **흔들린 칸 0 · 고칠 것 0** |
| ★★★ **3×3 격자** | `r34_grid` — 두 벌(`inline` / `let`) × 9 | 18 컴파일 | **거절 3 / 9 · 3 / 9** |
| 거절 전문 | `r34_let_mut` · `r34_let_give` · `r34_inline_mut` | 3 | **E0525 · E0525 · E0596** |
| ★★ `move` | `r34_move_fn` · `r34_move_after` | 2 | 통과 `6 3` · **E0382** |
| E0373 | `r34_thread` · `r34_thread_move` | 2 | **E0373** · `help:` 대로 통과 |
| 부르는 쪽 | `r34_once_twice` · `r34_mut_binding` | 2 | **E0382 · E0596** |
| 크기 | `r34_size` | 1 | 0 · 8 · 16 · 4 · 8 · 24 |
| ★★★ **에디션 격자** | `r34_ed_grid` — 소스 셋 × 2015·2018·2021·2024 | 12 컴파일 | **바뀐 소스 3 / 3**(2018 ↔ 2021) |
| 2018 전문 | `r34_dj_borrow18` · `r34_dj_after18` | 2 | **E0506 · E0382** |
| 루프 | `r34_loop` · `r34_loop_ref` · `r34_late.py` | 3 | `[0, 1, 2]` · **E0597** · 파이썬 `[2, 2, 2]` / `[0, 1, 2]` |
| **안 던진 것** — Go 1.22 판 · `cargo fix --edition` · 고유 불변 빌림 · `AsyncFn*` · 실행 시간 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★ **클로저 크기** | ★ Reference 「클로저는 레이아웃 보장이 없다」 |
| 같은 거절이 **E0525 냐 E0596/E0507 이냐** | ★ 진단 선택은 판마다 바뀔 수 있다 |
| `help:` 문구 | ★ 진단의 제안 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
