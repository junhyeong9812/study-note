# rust/syntax/43 — `Deref` 강제와 스마트 포인터를 쓰는 감각 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `14 / 30` — 문자열류와 정수 슬라이스류가 거울처럼 갈린다

**출력**

```text
===== 소스: r43_grid.sh =====
# 받는 자리 셋 × 넘기는 것 열 — 칸마다 소스를 만들어 컴파일만 한다
T=$'\t'
slots=(
  'fn f(_x: &str) {}'
  'fn f(_x: &[i32]) {}'
  'fn f(_x: &String) {}'
)
slotname=('&str' '&[i32]' '&String')
args=(
  '&String|let v = String::from("a"); f(&v);'
  '&Box<String>|let v = Box::new(String::from("a")); f(&v);'
  '&Rc<String>|let v = std::rc::Rc::new(String::from("a")); f(&v);'
  '&&String|let s = String::from("a"); let v = &s; f(&v);'
  '&mut String|let mut v = String::from("a"); f(&mut v);'
  'String (no &)|let v = String::from("a"); f(v);'
  '&Vec<i32>|let v = vec![1, 2]; f(&v);'
  '&Box<Vec<i32>>|let v = Box::new(vec![1, 2]); f(&v);'
  '&[i32; 2]|let v = [1, 2]; f(&v);'
  '&mut Vec<i32>|let mut v = vec![1, 2]; f(&mut v);'
)
hdr="passed"
for s in "${slotname[@]}"; do hdr="$hdr${T}$s"; done
printf '%s\n' "$hdr"
ok=0; total=0
for a in "${args[@]}"; do
  label=${a%%|*}
  body=${a#*|}
  row="$label"
  for i in 0 1 2; do
    printf '%s\nfn main() {\n    %s\n}\n' "${slots[$i]}" "$body" > g.rs
    if rustc --edition 2021 -A unused --emit=metadata -o g.rmeta g.rs 2>err.txt; then
      cell=ok; ok=$((ok+1))
    else
      cell=$(grep -o '^error\[E[0-9]*\]' err.txt | head -1 | sed 's/^error\[\(.*\)\]/\1/')
    fi
    row="$row${T}$cell"
    total=$((total+1))
  done
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 4 ] || { echo "column count $cols != 4"; exit 1; }
  printf '%s\n' "$row"
done
echo "cells that compile: $ok / $total"
===== bash r43_grid.sh =====
passed	&str	&[i32]	&String
&String	ok	E0308	ok
&Box<String>	ok	E0308	ok
&Rc<String>	ok	E0308	ok
&&String	ok	E0308	ok
&mut String	ok	E0308	ok
String (no &)	E0308	E0308	E0308
&Vec<i32>	E0308	ok	E0308
&Box<Vec<i32>>	E0308	ok	E0308
&[i32; 2]	E0308	ok	E0308
&mut Vec<i32>	E0308	ok	E0308
cells that compile: 14 / 30
(exit 0)
```

**왜 그런가**

- ★★★ **문자열류 다섯 줄**(`&String` · `&Box<String>` · `&Rc<String>` · `&&String` · `&mut String`)은 `&str`·`&String` 칸이 `ok`, `&[i32]` 칸이 E0308. **정수류 네 줄**은 그 반대. `Deref` 사슬이 `String` → `str`, `Vec<i32>` → `[i32]` 로만 가기 때문이다.
- ★★ **`String`(`&` 없음) 줄은 셋 다 E0308** — 강제는 `&` 를 붙여 주지 않는다.
- ★ 5 × 2 + 4 × 1 = 14 는 **스크립트가 센 수**다(마지막 줄).

### 2. ★★★ `str` · `Box<String>` · `String` · `str`

**출력**

```text
===== 소스: r43_generic.rs =====
use std::any::type_name;

fn concrete(_x: &str) -> &'static str {
    type_name::<str>()
}

fn generic<T: ?Sized>(_x: &T) -> &'static str {
    type_name::<T>()
}

fn main() {
    let b = Box::new(String::from("a"));
    println!("concrete(&b)  T = {}", concrete(&b));
    println!("generic(&b)   T = {}", generic(&b));
    println!("generic(&*b)  T = {}", generic(&*b));
    println!("generic(&**b) T = {}", generic(&**b));
}
===== rustc --edition 2021 r43_generic.rs =====
(exit 0)
===== ./r43_generic =====
concrete(&b)  T = str
generic(&b)   T = alloc::boxed::Box<alloc::string::String>
generic(&*b)  T = alloc::string::String
generic(&**b) T = str
(exit 0)
```

**왜 그런가**

- ★★★ **구체 타입 `&str` 자리는 두 번 벗기고, 제네릭 `&T` 자리는 `T = Box<String>` 으로 추론해 버린다.**
- ★ 원하는 겹은 손으로 — `&*b` 는 `String`, `&**b` 는 `str`.

### 3. ★★ 둘 다 E0277 — 에러는 경계 자리(18행) · 경로 호출(14행) 하나씩, `s.shout()` 은 통과

**출력**

```text
===== 소스: r43_bound.rs =====
trait Shout {
    fn shout(&self) -> String;
}

impl Shout for str {
    fn shout(&self) -> String {
        self.to_uppercase()
    }
}

fn loud<T: Shout + ?Sized>(x: &T) -> String {
    x.shout()
}

fn main() {
    let s = String::from("hi");
    println!("{}", s.shout());
    println!("{}", loud(&s));
}
===== rustc --edition 2021 r43_bound.rs =====
error[E0277]: the trait bound `String: Shout` is not satisfied
  --> r43_bound.rs:18:25
   |
18 |     println!("{}", loud(&s));
   |                    ---- ^^ the trait `Shout` is not implemented for `String`
   |                    |
   |                    required by a bound introduced by this call
   |
   = help: the trait `Shout` is implemented for `str`
note: required by a bound in `loud`
  --> r43_bound.rs:11:12
   |
11 | fn loud<T: Shout + ?Sized>(x: &T) -> String {
   |            ^^^^^ required by this bound in `loud`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

```text
===== 소스: r43_ufcs.rs =====
trait Shout {
    fn shout(&self) -> String;
}

impl Shout for str {
    fn shout(&self) -> String {
        self.to_uppercase()
    }
}

fn main() {
    let s = String::from("hi");
    println!("{}", s.shout());
    println!("{}", Shout::shout(&s));
}
===== rustc --edition 2021 r43_ufcs.rs =====
error[E0277]: the trait bound `String: Shout` is not satisfied
  --> r43_ufcs.rs:14:33
   |
14 |     println!("{}", Shout::shout(&s));
   |                    ------------ ^^ the trait `Shout` is not implemented for `String`
   |                    |
   |                    required by a bound introduced by this call
   |
   = help: the trait `Shout` is implemented for `str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**왜 그런가**

- ★★★ **`loud(&s)`**(18행) — `T = String` 을 먼저 정하고 `String: Shout` 를 묻는다 → **E0277**, `= help:` 「implemented for `str`」.
- ★★★ **`Shout::shout(&s)`**(14행) — 경로 호출은 함수 호출이라 `Self` 를 인자에서 추론한다 → **E0277**.
- ★★ **17행·13행의 `s.shout()` 은 에러가 없다** — 메서드 호출은 수신자를 벗겨 가며 `str::shout` 을 찾는다. 30번 (8)의 ③과 같은 모양이다.

### 4. ★★ E0308 — expected `&String`, found `&str` · `s.as_str()` 또는 `&*s`

**출력**

```text
===== 소스: r43_match.rs =====
fn main() {
    let s = String::from("on");
    let n = match &s {
        "on" => 1,
        _ => 0,
    };
    println!("{n}");
}
===== rustc --edition 2021 r43_match.rs =====
error[E0308]: mismatched types
 --> r43_match.rs:4:9
  |
3 |     let n = match &s {
  |                   -- this expression has type `&String`
4 |         "on" => 1,
  |         ^^^^ expected `&String`, found `&str`
  |
  = note: expected reference `&String`
             found reference `&'static str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

```text
===== 소스: r43_match_fix.rs =====
fn main() {
    let s = String::from("on");
    let a = match s.as_str() {
        "on" => 1,
        _ => 0,
    };
    let b = match &*s {
        "on" => 1,
        _ => 0,
    };
    println!("{a} {b}");
}
===== rustc --edition 2021 r43_match_fix.rs =====
(exit 0)
===== ./r43_match_fix =====
1 1
(exit 0)
```

**왜 그런가**

- ★★ **패턴은 값의 타입과 대조하는 자리**라 강제 지점이 아니다. 조사 대상을 **`&str` 로 만들어** 준다 — `s.as_str()` · `&*s`(`1 1`).

### 5. ★★ `3 false 3 3` — 뒤 소스는 8행 `takes(b)` 가 E0308, `help:` 는 `&b`

**출력**

```text
===== 소스: r43_method.rs =====
use std::rc::Rc;

fn takes(s: &str) -> usize {
    s.len()
}

fn main() {
    let b: Box<Rc<String>> = Box::new(Rc::new(String::from("abc")));
    println!("b.len()          {}", b.len());
    println!("b.is_empty()     {}", b.is_empty());
    println!("takes(&b)        {}", takes(&b));
    println!("(**b).len()      {}", (**b).len());
}
===== rustc --edition 2021 r43_method.rs =====
(exit 0)
===== ./r43_method =====
b.len()          3
b.is_empty()     false
takes(&b)        3
(**b).len()      3
(exit 0)
```

```text
===== 소스: r43_value_arg.rs =====
fn takes(s: &str) -> usize {
    s.len()
}

fn main() {
    let b = Box::new(String::from("abc"));
    println!("{}", b.len());
    println!("{}", takes(b));
}
===== rustc --edition 2021 r43_value_arg.rs =====
error[E0308]: mismatched types
 --> r43_value_arg.rs:8:26
  |
8 |     println!("{}", takes(b));
  |                    ----- ^ expected `&str`, found `Box<String>`
  |                    |
  |                    arguments to this function are incorrect
  |
  = note: expected reference `&str`
                found struct `Box<String>`
note: function defined here
 --> r43_value_arg.rs:1:4
  |
1 | fn takes(s: &str) -> usize {
  |    ^^^^^ -------
help: consider borrowing here
  |
8 |     println!("{}", takes(&b));
  |                          +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

**왜 그런가**

- ★★ `b.len()`·`b.is_empty()` — **메서드 호출의 자동 역참조**가 `Box` → `Rc` → `String` → `str` 로 벗겨 찾았다. `takes(&b)` 는 **인자 강제**, `(**b).len()` 은 손으로 벗긴 것.
- ★★★ **7행 `b.len()` 은 되고 8행 `takes(b)` 는 E0308** — 메서드는 수신자에 **`&` 를 붙여 주고**(자동 참조), 함수 인자는 안 붙인다.

### 6. ★★ E0596 — `DerefMut` 가 필요하다 · 그리고 `unused_mut` 경고

**출력**

```text
===== 소스: r43_newtype_nomut.rs =====
use std::ops::Deref;

struct Name(String);

impl Deref for Name {
    type Target = String;
    fn deref(&self) -> &String {
        &self.0
    }
}

fn main() {
    let mut n = Name(String::from("kim"));
    n.push_str("-lee");
    println!("{}", n.0);
}
===== rustc --edition 2021 r43_newtype_nomut.rs =====
warning: variable does not need to be mutable
  --> r43_newtype_nomut.rs:13:9
   |
13 |     let mut n = Name(String::from("kim"));
   |         ----^
   |         |
   |         help: remove this `mut`
   |
   = note: `#[warn(unused_mut)]` (part of `#[warn(unused)]`) on by default

error[E0596]: cannot borrow data in dereference of `Name` as mutable
  --> r43_newtype_nomut.rs:14:5
   |
14 |     n.push_str("-lee");
   |     ^ cannot borrow as mutable
   |
   = help: trait `DerefMut` is required to modify through a dereference, but it is not implemented for `Name`

error: aborting due to 1 previous error; 1 warning emitted

For more information about this error, try `rustc --explain E0596`.
(exit 1)
```

**왜 그런가**

- ★★★ **E0596 — cannot borrow data in dereference of `Name` as mutable**, `= help:` 「trait `DerefMut` is required to modify through a dereference, but it is not implemented for `Name`」. `push_str` 는 `&mut String` 을 요구하는데 `Deref` 는 `&String` 만 준다.
- ★★ **경고 `variable does not need to be mutable`** 이 **에러보다 먼저** 나온다(`1 warning emitted`). 11번에서 풀이.
- ★ `DerefMut` 를 달면 통과한다 — 서머리 (6)의 `r43_newtype`(`kim-lee!`).

### 7. ★★★ 「원하는 타입이 명시되어 있거나 전파로 얻을 수 있는 자리(타입 추론 없이)」

- ★★★ Reference — 강제 지점은 「대개 **원하는 타입이 명시되어 있거나** 명시된 타입에서 **전파로** 얻을 수 있는 자리(**without type inference**)」.
- ★★ `concrete(_x: &str)` 는 원하는 타입이 **명시**되어 있다 → 강제. `generic<T>(_x: &T)` 의 `T` 는 **추론할 변수**다 → 원하는 타입이 없으니 **넘긴 것이 곧 답**이 된다(`T = Box<String>`).

### 8. ★★ 크기 지우기 강제 · `&mut T` → `&U` — `&` 없는 값은 사슬의 시작점이 없다

- ★★ **`&[i32; 2]` → `&[i32]`** — Reference 의 **unsized 강제**(`[T; n]` → `[T]`). 배열은 `Deref` 를 구현하지 않는다.
- ★★ **`&mut String` → `&str`** — Reference 의 강제 목록 「**`&T` or `&mut T` to `&U` if `T` implements `Deref<Target = U>`**」(그리고 `&mut T` → `&T` 낮추기).
- ★★★ **`String` 값** — 강제 목록의 역참조 강제는 **참조에서 참조로**만 간다. 값에 `&` 를 붙이는 강제는 없다 → E0308(`help:` 가 `&` 를 권한다 — 5번).

### 9. ★★ 제네릭 `T` · 트레이트 경계 · 경로 호출 · `match` 패턴 — 「타입을 판정하는 자리」

- ★★ 14번 (4)의 둘 — **비교 연산자**(트레이트 구현을 찾는 자리 · E0277) · **함수를 값으로**(`map(takes_str)` · E0631).
- ★★★ 이 편이 더한 넷 — **제네릭 `&T`**(2번 — 추론) · **트레이트 경계**(3번 `loud` · E0277) · **경로 호출**(3번 `Shout::shout` · E0277) · **`match` 패턴**(4번 · E0308).
- ★★ 한 문장 — **「무엇을 넣을지가 적혀 있는 자리」에서는 돌고, 「넣은 것이 무엇인지 판정하는 자리」에서는 안 돈다**(14번 그림의 요약에 넷을 얹은 것).

### 10. ★★ 투명·저렴·놀라지 않음 — 스마트 포인터만 — 상속 흉내는 「메서드 충돌」에 걸린다

- ★★ std 「When to implement `Deref` or `DerefMut`」 — **달아도 되는 때**: 대상 타입처럼 **투명하게** 굴고 · `deref` 가 **싸고** · 강제 동작이 **사용자를 놀라게 하지 않을** 때. **달지 말 때**: `deref` 가 **실패할 수 있을** 때 · **대상 타입의 메서드와 부딪힐 메서드**가 있을 때 · 강제를 **공개 API 의 약속으로 삼고 싶지 않을** 때.
- ★★ C-DEREF — 「**Only smart pointers implement `Deref` and `DerefMut`**」.
- ★★★ 30번 (8)의 `Dog`/`Animal` 은 `name` 이 **양쪽에 있어** 「부딪힐 메서드」 조건에 그대로 걸렸고(바깥이 이김 · 「재정의」가 안 먹음), 트레이트 구현도 안 따라와 **사용자를 놀라게** 했다(E0277). **컴파일러는 이 권고를 강제하지 않는다** — 두 블록 모두 `Deref` 를 다는 것 자체는 통과했다.

### 11. ★ `mut` 를 지우면 E0596 은 그대로이고 경고만 사라진다 — 처방은 `DerefMut`

- ★★ 경고의 `help: remove this mut` 를 따르면 **에러는 남는다** — 원인이 `mut` 가 아니라 `DerefMut` 부재이기 때문이다.
- ★★ 컴파일러가 「필요 없다」고 본 이유 — `n` 을 **가변으로 쓰는 자리**(`n.push_str`)가 **에러로 끝나** 가변 빌림이 성립하지 않았으니, 이 변수를 가변으로 쓰는 곳이 **하나도 없다**고 센 것으로 **읽힌다** — ★ 이것은 **추정**이다(진단 구현을 읽지 않았다). 확인된 것은 「두 진단이 함께 나온다」는 **출력**뿐이다.
- ★★★ **진단이 둘일 때는 에러의 `help:` 가 처방이다** — `impl DerefMut for Name` 을 달면 `mut` 가 다시 필요해지고 경고도 사라진다(`r43_newtype`).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷 · **고칠 것 0** |
| ★★★ **강제 격자** | `r43_grid.sh` — 서른 칸을 `--emit=metadata` 로 컴파일(탭 구분 · 칸 수 검사) | 30 | **`14 / 30`** |
| 제네릭 추론 | `r43_generic` | 1 | `str` · `Box<String>` · `String` · `str` |
| 안 도는 자리 | `r43_bound` · `r43_ufcs` · `r43_match` · `r43_match_fix` | 4 | **E0277** · **E0277** · **E0308** · `1 1` |
| 메서드 대 인자 | `r43_method` · `r43_value_arg` | 2 | `3 false 3 3` · **E0308** |
| `Deref`·`DerefMut` | `r43_newtype` · `r43_newtype_nomut` | 2 | 통과 · **E0596** + `unused_mut` |
| **안 던진 것** — 실행 시간 · 강제 전파식(배열·튜플) · 메서드 해석 순서의 세부 · `deref` 의 어셈블리 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `type_name` 의 문자열 | ★ std: 「best-effort」 — 명세되지 않았다 |
| E0596 과 `unused_mut` 경고의 동반 | ★ rustc 진단 구현 |
| E0308 의 `help:`(`consider borrowing here`) | ★ 진단 제안은 판에 매인다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
