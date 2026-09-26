# rust/syntax/43 — `Deref` 강제와 스마트 포인터를 쓰는 감각 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Type coercions](https://doc.rust-lang.org/reference/type-coercions.html)(강제 지점 · 강제 종류 — `&T`/`&mut T` → `&U` · `&mut T` → `&T` · 크기 지우기) ·
> [std — `Deref`](https://doc.rust-lang.org/std/ops/trait.Deref.html)(Deref coercion · **When to implement `Deref` or `DerefMut`**) ·
> [Rust API Guidelines — C-DEREF](https://rust-lang.github.io/api-guidelines/predictability.html#only-smart-pointers-implement-deref-and-derefmut-c-deref)(「Only smart pointers implement `Deref` and `DerefMut`」).
> ★ Reference·std 는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. API Guidelines 는 웹에서 제목·첫 문장을 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(격자는 `--emit=metadata` — 컴파일 통과만 본다).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★ **실행 시간은 재지 않았다.** `deref` 가 **몇 번 불리나**는 [30번 주제](../30-operator-overloading-std-ops-index-and-deref/) (7)이 **세었다**(`deref 호출 횟수 3`) — 인용만 한다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 강제 격자(받는 자리 × 넘기는 것 → 컴파일되나)다.** 강제는 **실행 결과에 아무 흔적도 안 남기므로** 컴파일러의 통과/거절로만 본다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **격자의 `ok`/에러 번호와 「통과 칸 14 / 30」** | 강제 규칙은 언어가 정한다 — **이 주제의 본체** |
| 안 흔들린다 — 단 **std 구현의 이름** | `type_name` 의 출력 `alloc::boxed::Box<alloc::string::String>` | ★ std 문서: 「반환 문자열의 **정확한 내용은 명세되지 않았다**」. 대조할 것은 **`Box` 가 남았나 · 벗겨졌나** 라는 성질이다 |
| 안 흔들린다 | E0308 · E0277 · E0596 번호·`파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 쓴다. 이 편의 블록에는 걸리는 칸이 없었다.

## 한눈에 — 쉽게 말하면

**`Deref` 강제는 「자동 회전문」이다. 문 앞에 「`&str` 만 입장」이라고 적혀 있으면, `&String` 을 든 사람은 회전문이 알아서 한 겹 벗겨 `&str` 로 들여보낸다. `&Box<String>` 은 두 겹을 벗긴다.
그런데 회전문은 **문패가 붙은 문에만** 있다. 「아무나(`T`)」라고 적힌 문은 벗기지 않고 **든 그대로** 들인다. 「`Shout` 할 줄 아는 사람만」이라고 적힌 문도 벗겨 보지 않는다.**

| 비유 | 실체 |
|---|---|
| 「**문패 `&str` 앞의 회전문**」 | ★★★ **강제 지점** — 함수 인자·타입을 적은 `let`·구조체 필드·반환(Reference) — 격자의 `ok` 칸((1)) |
| 「**한 겹 · 두 겹 벗기기**」 | ★★ `&String` → `&str` · `&Box<String>` → `&String` → `&str` · `&Rc<String>` → `&str`((1)) |
| 「**`&[i32; 2]` 도 들어간다 — 다른 문으로**」 | ★ **크기 지우기(unsized) 강제** — `Deref` 가 아니다((1)) |
| 「**아무나 문**」 | ★★★ **`fn f<T>(x: &T)`** — `T` 를 **추론**하므로 안 벗긴다 → `T = Box<String>`((2)) |
| 「**할 줄 아는 사람만 문**」 | ★★ **트레이트 경계 · 경로 호출** `Shout::shout(&s)` → **E0277**((3)) |
| 「**문 대신 이름표 대조**」 | ★★ **`match` 패턴** — `"on"` 을 `&String` 에 대면 **E0308**((4)) |
| 「**메서드를 부르면 직원이 찾아 준다**」 | ★★ **메서드 호출 자동 역참조** — `b.len()` 이 `Box<Rc<String>>` 에서 된다. **강제와 다른 규칙**이다((5)) |

```text
   받는 자리와 넘긴 것 — (1)(2)(3)의 블록 그대로

   받는 자리                       넘긴 것 &Box<String>              결과
   fn f(_: &str)          ─────▶  &Box<String> → &String → &str       ok      ← Deref 를 두 번
   fn f(_: &String)       ─────▶  &Box<String> → &String              ok      ← 한 번
   fn f(_: &[i32])        ─────▶  (String 은 [i32] 로 안 간다)         E0308
   fn generic<T>(_: &T)   ─────▶  T = Box<String>                     ok      ← 벗기지 않았다 (type_name)
   fn loud<T: Shout>(_: &T) ────▶ T = String, String: Shout ?        E0277   ← 벗겨 보지 않는다
```

> **역참조 강제(deref coercion)** — Reference: 「`T` 가 `Deref<Target = U>` 를 구현하면 **`&T` 또는 `&mut T` 를 `&U` 로**」 바꾸는 강제. 컴파일러가 `Deref::deref` 호출을 **조용히 끼운다**(30번 (7)).\
> 예: `fn takes(s: &str)` 에 `&String` 을 넘긴다.

> **강제 지점(coercion site)** — Reference: 「강제는 **정해진 자리에서만** 일어난다 — 대개 **원하는 타입이 명시되어 있거나 명시된 타입에서 전파로 얻을 수 있는** 자리(**타입 추론 없이**)」. 함수 인자 · 타입을 적은 `let` · `static`/`const` · 구조체 필드 · 함수 결과.\
> 예: `let a: &str = &s;` 는 강제 지점이고 `let a = &s;` 는 아니다.

## 이 주제가 답하려는 질문

1. ★★★ **`&Box<T>` 는 왜 `&T` 처럼 쓰이나 — 어느 받는 자리에 무엇을 넘기면 되나**((1)).
2. ★★★ **강제가 안 되는 자리는 어디인가** — 제네릭 · 트레이트 경계 · 경로 호출 · `match` 패턴((2)·(3)·(4)).
3. ★★ **메서드 호출의 자동 역참조는 강제와 무엇이 다르고, 내 타입에 `Deref` 를 달 때는 언제인가**((5)·(6)).

★ **선행** — [**40번 주제**](../40-box-recursive-types-and-dyn/) — `sum(rest)` 에 `&Box<List>` 를 넘긴 자리가 이 주제였다(그쪽 관련 자료가 여기를 가리킨다).
★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
[**14번 주제**](../14-string-vs-str/) (3)·(4) — `&str`/`&String` 두 시그니처가 받는 것 **실측 표** · **강제는 전이적**(`&&&&String` 까지 `&str`) · **`rr == "가나"` 는 E0277**(트레이트 구현을 찾는 자리) · **`map(takes_str)` 는 E0631**(함수를 값으로 넘기는 자리) · 「돈다 / 안 돈다」 그림.
[**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/) (7)·(8)·(9) — **`deref` 가 컴파일러에 의해 세 번 불린다** · **`Deref` 로 상속을 흉내 내면 세 군데서 깨진다**(이름이 겹치면 바깥이 이김 · 「재정의」가 안 먹음 · 트레이트 구현이 안 따라옴 — E0277) · `Rc` 가 메서드를 안 두는 이유.
이 편은 그 위에 **받는 자리 × 넘기는 것의 격자**, **제네릭 추론 자리**, **`match` 패턴**, **값 인자와 메서드 수신자의 차이**, **`DerefMut`** 을 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 강제 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **강제 격자**(칸마다 소스를 만들어 **컴파일만**) | 어느 받는 자리가 어느 넘긴 것을 **받나** | ★ **본체**((1)) |
| ② ★★ **`std::any::type_name`** | 제네릭 `T` 가 **무엇으로 추론됐나**(벗겼나) | 쓴다((2)) |
| ③ ★★ **컴파일러 진단** E0277 · E0308 · E0596 | 강제가 **안 도는 자리**의 이름 | 쓴다((3)·(4)·(5)·(6)) |
| `deref` 호출 횟수 | 컴파일러가 몇 번 끼웠나 | ★ **이미 잰 것** — 30번 (7)의 `Cell` 계수기 |
| 실행 시간 | 「강제는 공짜다 / 비싸다」 | ★ **부적용 — 재지 않는다** |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「여기서 강제가 일어났나」는 **실행 출력으로 물을 수 없다** — 통과한 칸은 결과가 같고, 강제는 아무것도 찍지 않는다. 그래서 질문을 **「컴파일러가 받아 주나」**(①)와 **「`T` 가 무엇이 됐나」**(②)로 바꿔 물었다.
★ 바꾼 창이 **못 보는 것** — `ok` 칸 **안에서 몇 번 벗겼는지**(①은 통과만 말한다). 그 수는 30번 (7)처럼 **`deref` 안에 계수기를 단 내 타입**으로만 셀 수 있다.

### (1) ★★★ 강제 격자 — 받는 자리 셋 × 넘기는 것 열

**언제 쓰나** — 함수 인자를 `&str`·`&[T]` 로 받을지 정할 때, 그리고 「이걸 넘겨도 되나」를 판정할 때.

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

- ★★★ **「통과 칸 14 / 30」.** 넘긴 쪽을 **위 다섯 줄(문자열류)** 과 **아래 넷(정수 슬라이스류)** 으로 가르면 모양이 거울처럼 선다 — `&str`·`&String` 은 문자열류를, `&[i32]` 는 정수류를 다 받고 서로는 **전부 E0308** 이다. **강제는 `Deref` 사슬 위에서만 돈다** — `String` 은 `[i32]` 로 가는 사슬이 없다.
- ★★ **`&Box<String>` · `&Rc<String>`** — `&str` 자리에서 **두 번 벗긴다**(`Box`/`Rc` → `String` → `str`), `&String` 자리에서 **한 번**. **`&Vec<i32>` · `&Box<Vec<i32>>` → `&[i32]`** 도 같은 사슬이다(`Vec<T>: Deref<Target = [T]>`).
- ★★ **`&mut String` 도 `&str` 로 간다** — Reference 의 강제 목록이 역참조 강제를 「**`&T` or `&mut T` to `&U` if `T` implements `Deref<Target = U>`**」로 적는다 — **`&mut` 도 출발점에 들어 있다.** 가변을 불변으로 낮추는 것은 된다(거꾸로는 없다).
- ★★ **`&[i32; 2]` → `&[i32]`** 는 통과하지만 **`Deref` 가 아니다** — Reference 의 **크기 지우기(unsized) 강제**(`[T; n]` → `[T]`)다. 결과가 같아 보여도 규칙이 다르다.
- ★★★ **`String`(`&` 없음)은 세 칸 모두 E0308** — **강제는 `&` 를 붙여 주지 않는다.** `&T` 에서 시작해야 사슬이 돈다. (5)의 메서드 호출과 갈리는 자리다.

```text
   (1)에서 도는 사슬 — Deref 의 Target 을 따라간다

   Box<String> ─Deref─▶ String ─Deref─▶ str          &Box<String>  →  &String  →  &str
   Rc<String>  ─Deref─▶ String ─Deref─▶ str
   Box<Vec<i32>> ─Deref─▶ Vec<i32> ─Deref─▶ [i32]    &Box<Vec<i32>> → &Vec<i32> → &[i32]
   [i32; 2]  ─ Unsize (Deref 아님) ─▶ [i32]
   &mut T  ─ &mut → & 낮추기 ─▶ &T  ─Deref…
```

비용 — 컴파일러가 `deref` 호출을 **끼워 넣는다**(30번 (7)의 `3`). `Box`·`Rc`·`String`·`Vec` 의 `deref` 가 무엇으로 컴파일되는지는 **보지 않았다.**

### (2) ★★★ 제네릭 `T` — 추론이 강제를 이긴다

**언제 쓰나** — `fn f<T>(x: &T)` 에 스마트 포인터를 넘기면서 「안쪽 타입으로 받겠지」라고 기대할 때.

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

- ★★★ **`concrete(&b)` 는 `str`, `generic(&b)` 는 `Box<String>`** — 같은 `&b` 인데 받는 자리가 **구체 타입이면 벗기고, 제네릭이면 추론으로 `T` 를 정해 버린다.**
- ★★ Reference 의 강제 지점 정의가 이유를 적는다 — 「원하는 타입이 **명시되어 있거나 명시된 타입에서 전파로** 얻을 수 있는 자리(**타입 추론 없이**)」. `&T` 의 `T` 는 **추론할 변수**라 원하는 타입이 없다 → **강제가 끼어들 자리가 없다.**
- ★ 원하는 겹을 주려면 **손으로 벗긴다** — `&*b` 는 `String`, `&**b` 는 `str`.
- ★ `type_name` 의 **문자열 자체**(`alloc::boxed::Box<…>`)는 std 가 명세하지 않는다 — 대조할 것은 **`Box` 가 남았다는 성질**이다.

### (3) ★★ 트레이트 경계와 경로 호출 — 벗겨 보지 않는다

**언제 쓰나** — `str` 에만 구현된 트레이트를 `String` 으로 쓰려 할 때.

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

- ★★★ **E0277 — the trait bound `String: Shout` is not satisfied** · `= help:` 「the trait `Shout` is implemented for `str`」. **18행 `loud(&s)`** 에서 막혔다 — `T` 를 **`String` 으로 먼저 정한 뒤** 「`String: Shout` 인가」를 묻는다. 거기서 `str` 로 벗겨 보는 일은 없다.
- ★★ **그런데 17행 `s.shout()` 은 에러가 없다** — 에러가 **18행 하나뿐**이다. 메서드 호출은 **수신자 타입을 벗겨 가며 메서드를 찾는다**((5)). 30번 (8)의 ③(`d.speak()` 는 되고 `twice(&d)` 는 E0277)과 **같은 모양**이다 — 거기는 사용자 `Deref`, 여기는 std 의 `String: Deref<Target = str>`.

**같은 메서드를 경로로 부르면.**

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

- ★★★ **`Shout::shout(&s)` 도 E0277** — **14행 하나뿐**, 13행 `s.shout()` 은 통과. 경로 호출은 **메서드 호출이 아니라 함수 호출**이라 `Self` 를 인자 `&String` 에서 **추론**하고(→ `String`), (2)와 같은 이유로 벗기지 않는다.
- ★ 고치는 법은 둘 다 같다 — `loud(s.as_str())` · `Shout::shout(&*s)` 처럼 **넘기기 전에 `&str` 로** 만든다.

### (4) ★★ `match` 패턴 — 강제 지점이 아니다

**언제 쓰나** — `String` 을 문자열 리터럴 패턴으로 가를 때.

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

- ★★★ **E0308 — expected `&String`, found `&str`.** `= note:` 가 「expected reference `&String` / found reference `&'static str`」. 패턴은 **값의 타입과 맞는지 대조하는 자리**라 강제가 없다.
- ★ 14번 (4)의 「**무엇을 넣는 자리에서는 돌고, 무엇이 무엇인지 판정하는 자리에서는 안 돈다**」에 **`match` 패턴**이 한 줄 더 붙는다.

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

- ★★ **`s.as_str()` 또는 `&*s`** 로 조사 대상을 **`&str` 로 만들어 준다**(`1 1`).

### (5) ★★ 메서드 호출의 자동 역참조 — 강제와 다른 규칙

**언제 쓰나** — `Box<Rc<String>>` 같은 겹친 포인터에서 메서드를 부를 때.

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

- ★★ **`b.len()` · `b.is_empty()` 가 된다** — `Box<Rc<String>>` 에는 `len` 이 없다. 메서드 호출은 수신자를 **`Box` → `Rc` → `String` → `str` 로 벗겨 가며** 이름을 찾는다(`len` 은 `str` 의 메서드다). Reference 의 강제 절도 「메서드 호출의 수신자는 **다르게** 강제된다 — method-call 문서를 보라」고 따로 뺀다.
- ★ `takes(&b)` 는 **인자 자리의 강제**(세 번 벗김), `(**b).len()` 은 **손으로 벗긴 것**. 셋 다 `3` 이다.

**값을 그대로 넘기면.**

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

- ★★★ **7행 `b.len()` 은 되고 8행 `takes(b)` 는 E0308** — `help:` 「consider borrowing here」(`&b`). **메서드 호출은 수신자에 `&` 를 붙여 주지만(자동 참조) 함수 인자는 안 붙인다.** (1)의 `String (no &)` 줄과 같은 사실이다.

| | 함수 인자(강제) | 메서드 수신자(자동 역참조) |
|---|---|---|
| `&` 를 붙여 주나 | ✗ — `takes(b)` E0308 | ✓ — `b.len()` 에 `&b` 가 붙는다 |
| 벗기는 기준 | **받는 자리의 타입**(명시된 것)까지 | **그 이름의 메서드가 나올 때**까지 |
| 제네릭·트레이트 경계 | ✗ — (2)·(3) | ✓ — `s.shout()` 는 된다((3)) |

### (6) ★★ 내 타입에 `Deref`·`DerefMut` 를 달면 — 그리고 언제 다나

**언제 쓰나** — **값을 감싸되 안쪽처럼 쓰이게** 하는 포인터 모양의 타입을 만들 때 — **그때만.**

```text
===== 소스: r43_newtype.rs =====
use std::ops::{Deref, DerefMut};

struct Name(String);

impl Deref for Name {
    type Target = String;
    fn deref(&self) -> &String {
        &self.0
    }
}

impl DerefMut for Name {
    fn deref_mut(&mut self) -> &mut String {
        &mut self.0
    }
}

fn show(s: &str) -> usize {
    s.len()
}

fn grow(s: &mut String) {
    s.push('!');
}

fn main() {
    let mut n = Name(String::from("kim"));
    println!("show(&n)   {}", show(&n));
    n.push_str("-lee");
    grow(&mut n);
    println!("n.0        {}", n.0);
}
===== rustc --edition 2021 r43_newtype.rs =====
(exit 0)
===== ./r43_newtype =====
show(&n)   3
n.0        kim-lee!
(exit 0)
```

- ★★ **`show(&n)`**(인자 강제 `&Name` → `&String` → `&str`) · **`n.push_str`**(자동 역참조 + `DerefMut`) · **`grow(&mut n)`**(`&mut Name` → `&mut String` — `DerefMut` 강제) 전부 된다.

**`DerefMut` 를 빼면.**

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

- ★★★ **E0596 — cannot borrow data in dereference of `Name` as mutable** · `= help:` 「trait `DerefMut` is required to modify through a dereference, but it is not implemented for `Name`」. **`Deref` 만으로는 `&mut` 쪽 사슬이 없다.**
- ★★ **예상과 달랐던 칸 — 경고가 같이 나온다: `variable does not need to be mutable`.** `mut` 는 **고치려고** 붙인 것인데, 컴파일러는 그 고치기가 에러로 끝났으니 `mut` 가 쓸모없다고 본다. **경고의 `help: remove this mut` 를 따르면 안 된다** — 에러의 `help:` 가 진짜 처방이다.

★★★ **설계 권고층 — 언제 `Deref` 를 다나.** 이 층은 **컴파일러가 강제하지 않는다**(위 두 블록 모두 `Deref` 를 다는 것 자체는 막히지 않았다).
- std `Deref` 문서의 「**When to implement `Deref` or `DerefMut`**」 — 달아도 되는 때: 그 타입이 **대상 타입처럼 투명하게** 굴고 · `deref` 가 **싸고** · 강제 동작이 **사용자를 놀라게 하지 않을** 때. 달지 말 때: 실패할 수 있을 때 · **대상 타입의 메서드와 부딪힐 메서드가 있을 때** · 강제를 **공개 API 의 약속으로 삼고 싶지 않을** 때.
- [Rust API Guidelines — C-DEREF](https://rust-lang.github.io/api-guidelines/predictability.html#only-smart-pointers-implement-deref-and-derefmut-c-deref) — 「**Only smart pointers implement `Deref` and `DerefMut`**」.
- ★★ **「`Deref` 로 상속 흉내」는 반관용구다** — 그 증거(세 군데서 깨진다)는 [30번 주제](../30-operator-overloading-std-ops-index-and-deref/) (8)이 에러 전문으로 보였다. 이 편의 `Name` 은 **안쪽 `String` 처럼 쓰이는 것이 목적인** 감싸개라 권고의 「투명하게 군다」에 든다 — 그래도 `Name` 에 `len` 같은 이름을 새로 달면 30번 (8)의 ①(바깥이 이긴다)이 그대로 난다.

## 문법 — 형태와 규칙

```text
   fn takes(s: &str)                  ← 받는 자리를 가장 안쪽 타입으로 — &String · &Box<String> · &Rc<String> · &mut String 이 다 들어온다
   fn takes(s: &[T])                  ← &Vec<T> · &Box<Vec<T>> · &[T; N] 이 다 들어온다

   impl Deref for P { type Target = U; fn deref(&self) -> &U { … } }
   impl DerefMut for P { fn deref_mut(&mut self) -> &mut U { … } }   ← &mut 쪽 사슬 (Deref 필요)

   손으로 벗기기: &*b  &**b  s.as_str()  &v[..]
```

- ★★★ **강제는 강제 지점에서만 — 인자 · 타입 적은 `let` · 필드 · 반환**((1)). **`&` 를 붙여 주지는 않는다.**
- ★★★ **제네릭 · 트레이트 경계 · 경로 호출 · `match` 패턴에서는 안 돈다**((2)·(3)·(4)). 14번의 비교 연산자(E0277)·함수를 값으로(E0631)도 같은 목록이다.
- ★★ **메서드 호출은 다른 규칙이다** — 자동 참조 + 자동 역참조로 이름을 찾는다((5)).
- ★ **`&mut` 로 고치려면 `DerefMut`**((6)).

## 어디서 틀리나

### 1. ★★★ 「`fn f<T>(x: &T)` 에 `&Box<String>` 을 넘기면 `T = String` 이다」

(2) — **`T = Box<String>`**. 추론이 먼저 `T` 를 정한다.

### 2. ★★★ 「`s.shout()` 가 되니 `loud(&s)` 도 된다」

(3) — 메서드 호출은 벗기고 **경계는 안 벗긴다**(E0277). 경로 호출 `Shout::shout(&s)` 도 E0277.

### 3. ★★ 「`match &s { "on" => … }` 는 강제로 맞춰진다」

(4) — **E0308**. 패턴 자리는 강제 지점이 아니다. `s.as_str()`.

### 4. ★★ 「`b.len()` 이 되니 `takes(b)` 도 된다」

(5) — 메서드는 `&` 를 붙여 주고 **함수 인자는 안 붙인다**(E0308 · `help:` 가 `&b`).

### 5. ★★ 「`&[i32; 2]` 가 `&[i32]` 로 가는 것도 `Deref` 다」

(1) — **크기 지우기 강제**다. 배열은 `Deref` 를 구현하지 않는다.

### 6. ★★ 「`Deref` 를 달았으니 `&mut` 도 따라온다」

(6) — **E0596**. `DerefMut` 가 따로 필요하다. 함께 나오는 **`unused_mut` 경고의 `help:` 를 따르지 마라.**

### 7. ★ 「`Deref` 는 상속 대용이다」

(6)의 권고층과 30번 (8) — **스마트 포인터만** 단다(C-DEREF).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 강제가 도는 **자리**와 **종류** | ★ **언어**(Reference — Type coercions) | (1)·(2) |
| `String: Deref<Target = str>` · `Vec<T>: Deref<Target = [T]>` · `Box`·`Rc` 의 `Deref` | ★ **std 의 트레이트 구현** | (1) |
| 메서드 호출의 자동 참조·역참조 | ★ **언어**(Reference — Method-call expressions) | (5) |
| `type_name` 의 출력 문자열 | ★ **std 구현** — 명세되지 않았다 | (2) |
| 「스마트 포인터만 `Deref` 를 단다」 | ★ **설계 권고**(std 문서 · API Guidelines) — **컴파일러는 강제하지 않는다** | (6) |
| E0596 와 함께 `unused_mut` 경고가 나오는 것 | ★ **rustc 진단 구현**(이 판 관찰) | (6) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 문자열을 읽기만 하는 인자 | ★★ **`&str`** — `&String` 이 아니라 | (1) · 14번 (3) |
| 원소를 읽기만 하는 인자 | ★★ **`&[T]`** — `&Vec<T>` 가 아니라 | (1) |
| 여러 타입을 받는 제네릭 인자 | **`T: AsRef<str>`**(29번) 또는 `&str` 로 받기 | (2) — `&T` 는 안 벗긴다 |
| 내 감싸개가 **안쪽처럼** 쓰여야 한다 | `Deref`(+ 고치면 `DerefMut`) | (6) |
| 「부모 타입의 메서드를 물려받고 싶다」 | ★ **`Deref` 말고** 위임 메서드 · 트레이트 | 30번 (8) · C-DEREF |

## 핵심 문장

- ★★★ **`&Box<T>` 가 `&T` 처럼 쓰이는 것은 강제 지점에서 컴파일러가 `Deref` 사슬을 따라 벗기기 때문이다 — `&Vec<T>` → `&[T]`, `&String` → `&str` 도 같은 사슬이다.**
- ★★★ **강제는 원하는 타입이 명시된 자리에서만 돈다 — 제네릭 `T` · 트레이트 경계 · 경로 호출 · `match` 패턴에서는 안 돈다.**
- ★★ **메서드 호출은 강제가 아니라 자동 참조·역참조다 — `b.len()` 은 되고 `takes(b)` 는 E0308 이다.**
- ★★ **`&mut` 로 고치려면 `DerefMut` 가 따로 필요하다(E0596).**
- ★ **`Deref` 는 스마트 포인터만 단다 — 상속 흉내는 반관용구다.**

## 관련 자료

- [**14번 주제**](../14-string-vs-str/) (3)·(4) — 강제의 전이성 · 비교 연산자(E0277) · `map(f)`(E0631). **그쪽은 `String`/`&str` 하나의 축, 여기는 받는 자리 × 넘기는 것 전체.**
- [**30번 주제**](../30-operator-overloading-std-ops-index-and-deref/) (7)·(8)·(9) — `deref` 호출 수 · 상속 흉내의 세 파손 · `Rc` 가 메서드를 안 두는 이유.
- [**29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/) — `AsRef` — 제네릭 자리에서 (2)를 푸는 도구.
- [**40번 주제**](../40-box-recursive-types-and-dyn/) · [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Box`·`Rc` 자체.
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — `Ref`/`RefMut` 가드도 `Deref`/`DerefMut` 로 `&T`/`&mut T` 처럼 쓰인다.
- [**26번 주제**](../26-orphan-rule-and-newtype/) — newtype. (6)의 `Name` 이 그 꼴이다.

## 용어 풀이

- **강제(coercion)** — 컴파일러가 값의 타입을 **암묵적으로** 바꾸는 것. 정해진 자리와 종류만 있다.
- **역참조 강제(deref coercion)** — `&T` → `&U`(`T: Deref<Target = U>`). 전이적이다.
- **크기 지우기 강제(unsized coercion)** — `&[T; N]` → `&[T]`, `&T` → `&dyn Trait` 처럼 크기 정보를 포인터로 옮기는 강제.
- **자동 역참조(auto-deref)** — 메서드 호출에서 수신자를 벗겨 가며 메서드를 찾는 것. 자동 참조(`&`·`&mut` 붙이기)와 함께 돈다.
- **`DerefMut`** — `&mut` 쪽 역참조. `Deref` 를 상위 트레이트로 요구한다.
- **경로 호출(fully qualified / UFCS)** — `Trait::method(&x)` 꼴. 메서드 문법이 아니라 함수 호출이다.

## 더 들어가면

- 강제가 **전파**되는 자리 — 배열 리터럴 · 튜플 · 괄호식 · 블록의 꼬리식(Reference 「coercion-propagating expressions」). **이 문서는 던지지 않았다.**
- 메서드 해석의 정확한 순서(수신자 후보 목록 · 인허런트 먼저 · `&`·`&mut` 순) — Reference 「Method-call expressions」.
