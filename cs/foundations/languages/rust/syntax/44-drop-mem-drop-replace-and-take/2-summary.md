# rust/syntax/44 — `Drop` · `mem::drop` · `mem::replace`/`take` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Destructors](https://doc.rust-lang.org/reference/destructors.html)(drop 스코프 · 임시값 스코프 · 임시값 수명 연장 · 되감기 없는 종료) ·
> [Reference — Wildcard pattern](https://doc.rust-lang.org/reference/patterns.html#wildcard-pattern)(「it does not copy, move or borrow the value it matches」) ·
> [std — `Drop`](https://doc.rust-lang.org/std/ops/trait.Drop.html) · [std — `mem::take`](https://doc.rust-lang.org/std/mem/fn.take.html) · [std — `mem::forget`](https://doc.rust-lang.org/std/mem/fn.forget.html)(§Safety) ·
> [cppreference — throw](https://en.cppreference.com/w/cpp/language/throw)(잡히지 않은 예외의 되감기는 **구현 정의**).
> ★ Reference·std 는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. cppreference 는 웹에서 해당 문장을 확인했다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로(`-C panic=abort` 판 하나) 돌려 받은 것이다. C++ 대비는 `g++ 13.3.0 -std=c++20 -Wall -Wextra -pedantic`.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★ **속도·메모리는 재지 않았다.**
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① `Drop` 순서 로그의 격자(문장마다 「어디서 `drop` 줄이 찍히나」)다.** 해제 시점은 컴파일러가 말해 주지 않으므로 **출력 순서**로 본다(09번의 창).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread 'main' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| 안 흔들린다 | ★★★ **격자의 「어디서」 칸과 「다음 문장 전에 풀린 칸 5 / 12」** | 해제 시점은 **언어가 정한다**(Reference — Destructors) — **이 주제의 본체** |
| 안 흔들린다 | E0509 · E0507 · E0382 · E0308 번호·`파일:줄:칸` · 종료 코드(`101` · `134`) | 같은 rustc·g++ 판에서 고정이다 |
| ★ **구현이 정한다** | C++ 에서 잡히지 않은 예외가 **되감나** | ★ 표준이 **구현 정의**로 남긴 칸 — 이 판(libstdc++)의 관찰이다((5)) |

★ 정규화 규칙은 **기본 넷**만 쓴다(패닉 스레드 id 가 걸린다). ★ 셸이 시그널 종료에 붙이는 「`Aborted (core dumped)`」 줄은 **프로그램의 출력이 아니어서** 싣지 않았다 — 캡처가 한 낱말짜리 명령을 `exec` 로 돌려 그 줄을 블록 밖으로 뺐다.

## 한눈에 — 쉽게 말하면

**`Drop` 은 「퇴실 청소」다. 방(값)의 주인이 떠나는 순간 청소가 자동으로 돈다 — 주인이 떠나는 순간이 **언제냐**만 알면 된다.
이름표를 단 손님(`let _x`)은 체크아웃 날(블록 끝)에 떠나고, 이름표 없이 잠깐 들른 손님(임시값·`let _ =`)은 **그 문장이 끝나자마자** 떠난다.
청소 중인 방에서 가구를 들고 나갈 수는 없다(E0509) — 대신 **빈 가구를 넣어 두고 바꿔 들고 나가는 것**(`mem::take`/`replace`)은 된다.**

| 비유 | 실체 |
|---|---|
| 「**체크아웃 날 떠나는 손님**」 | ★★ **`let _x = D(..)`** — 블록 끝에서 `drop`((1)) |
| 「**잠깐 들른 손님**」 | ★★★ **`let _ = D(..)` · `D(..);` · `D(..).0.len()`** — **다음 문장 전에** `drop`((1)) |
| 「**이미 방이 있는 손님에게 `_` 를 붙여도**」 | ★★★ **`let x = D(..); let _ = x;`** — **이동하지 않는다.** `x` 는 블록 끝까지 살고 **그 뒤에도 쓸 수 있다**((1)·(2)) |
| 「**같은 이름의 새 손님**」 | ★★ **섀도잉 `let x = D("a"); let x = D("b");`** — 가려진 `a` 는 **블록 끝까지 산다**(그리고 `b` 뒤에 떠난다)((1)) |
| 「**방을 새 손님에게 넘김**」 | ★★ **대입 `x = D("b")`** — 옛 값 `a` 는 **그 자리에서** `drop`((1)) |
| 「**청소 중인 방의 가구**」 | ★★★ **`Drop` 을 단 타입에서 필드 이동 → E0509** → `mem::take`·`replace`·`Option::take`((3)) |
| 「**빌린 방의 가구**」 | ★★ **`&mut self` 에서 필드 이동 → E0507** → `mem::replace`((4)) |
| 「**화재 대피 중에도 청소는 돈다**」 | ★★ **패닉 되감기 중 `drop` 이 불린다** — `-C panic=abort` 면 안 불린다((5)) |
| 「**청소하지 말라는 쪽지**」 | ★ **`mem::forget`** — `drop` 이 안 불린다. **안전 함수**다((6)) |

```text
   (1)의 격자를 한 장으로 — 「drop a」가 찍힌 자리

   {
       <문장>                   let _ = D("a")    D("a");    D("a").0.len()    x = D("b")    drop(x)   ─▶ 여기서 (다음 문장 전)
       println!("<next …>")
       println!("<block end>")
   }                            let _x = D("a")   let _ = x   let _y = x   let r = &D("a")   섀도잉   vec![D("a")]  ─▶ 여기서 (블록 끝)
                                std::mem::forget(D("a"))                                                              ─▶ 끝내 안 찍힘
```

> **drop 스코프(drop scope)** — Reference: 값이 버려지는 지점을 정하는 범위. 변수는 **자기를 선언한 블록의 끝**, 임시값은 **대개 그 문장의 끝**에서 버려진다.\
> 예: `let _x = D("a");` 는 블록 끝, `D("a");` 는 그 문장 끝.

> **임시값 수명 연장(temporary lifetime extension)** — `let r = &D("a");` 처럼 **`let` 의 초기식에서 곧장 빌린** 임시값은 **블록 끝까지** 산다(Reference).\
> 예: (1)의 `let r = &D("a");` 행이 「at block end」인 이유.

## 이 주제가 답하려는 질문

1. ★★★ **값은 정확히 어느 줄에서 버려지나** — 변수 · 임시값 · `_` · 섀도잉 · 대입 · `mem::drop` · `mem::forget`((1)·(2)).
2. ★★★ **소유권 때문에 필드를 못 꺼내는 자리를 어떻게 푸나** — `Drop` 을 단 타입(E0509)과 `&mut self`(E0507)((3)·(4)).
3. ★★ **패닉이 나도 정리되나 — C++ 와 무엇이 다른가**((5)·(6)).

★ **선행** — [**09번 주제**](../09-copy-clone-and-drop/)가 이 주제의 뿌리다. ★★★ **이미 잰 것 — 다시 재지 않고 인용한다.**
09번 (6) — **지역 변수는 선언 역순 · 구조체 필드는 선언 순 · `Drop` 을 단 구조체는 본체 먼저 · 튜플·`Vec` 원소는 앞에서부터 · 함수 인자는 역순**.
09번 (3) — **`Copy` 와 `Drop` 은 함께 못 단다(E0184 — `the type has a destructor`)** · (7) — **`d.drop()` 은 E0040, `drop(d)` 는 빈 몸통 함수**.
[**08번 주제**](../08-ownership-and-move/) — **E0509**(그쪽 관련 자료가 「`Drop` 이면 `mem::take` — 목록의 **44번 주제**」라고 이 편을 가리킨다).
[**11번 주제**](../11-borrow-checker-rejections/) 3-answer 5번 — **`&mut self` 에서 필드를 꺼내면 E0507 → `mem::take`** 와 `take`·`replace`·`swap` 표(요구 경계 · 안정화 판).
이 편은 그 위에 **문장 단위의 해제 격자**, **`let _` 판별**, **E0509 → `take` 의 전 과정**, **열거형 상태 전이의 E0507**, **패닉 전략**, **`forget`** 을 더한다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① `Drop` 순서 로그의 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **`impl Drop` + `println!` 격자**(문장마다 소스를 만들어 실행) | 그 값이 **어느 표지 앞에서** 버려지나 | ★ **본체**((1)) |
| ② ★★ **컴파일러 진단** E0382 · E0509 · E0507 · E0308 · `let_underscore_lock` | `_` 가 이동하나 · 락 가드를 `_` 로 받으면 · 필드를 꺼낼 수 있나 | 쓴다((2)·(3)·(4)) |
| ③ ★★ **패닉 전략 × 종료 코드** | 되감기 중 `drop` 이 도나(`101` 대 `134`) | 쓴다((5)) |
| ④ ★ **C++ `g++` 대비** | 잡히지 않은 예외에서 소멸자가 도나 | 쓴다((5)) |
| 지역·필드·튜플·`Vec`·인자 순서 | — | ★ **이미 잰 것** — 09번 (6) |
| `Copy` + `Drop` | — | ★ **이미 잰 것** — 09번 (3)의 E0184 |
| 메모리가 반납됐나 | 「`forget` 은 샌다」의 바이트 | ★ **못 잰 것** — 메모리 도구가 없다(41번 머리말 블록). **`drop` 줄이 안 찍혔다**까지만 말한다 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「`let _ = x` 는 `x` 를 버리나」를 `drop` 로그로만 물으면 **「블록 끝에 찍혔다」는 답이 `let _y = x`(이동)와 똑같다** — 로그가 둘을 못 가른다. 그래서 질문을 **「그 뒤에 `x` 를 쓸 수 있나」** 로 바꿔 **컴파일러**(②)에게 물었다((2)).

### (1) ★★★ 문장마다 `drop` 이 어디서 찍히나 — 열두 칸 격자

**언제 쓰나** — 락 가드·파일·트랜잭션처럼 **정리 시점이 곧 의미**인 값을 다룰 때마다.

```text
===== 소스: r44_grid.sh =====
# 문장 하나마다 프로그램을 만들어 D("a") 의 drop 이 어디서 찍히는지 본다 — 다음 문장 전 / 블록 끝 / 끝내 안 찍힘
T=$'\t'
cases=(
  'let _ = D("a");'
  'let _x = D("a");'
  'D("a");'
  'let x = D("a"); let _ = x;'
  'let x = D("a"); let _y = x;'
  'let x = D("a"); drop(x);'
  'let x = D("a"); let x = D("b");'
  'let mut x = D("a"); x = D("b");'
  'let n = D("a").0.len();'
  'let r = &D("a");'
  'let v = vec![D("a")]; let _ = v.len();'
  'std::mem::forget(D("a"));'
)
printf 'statement\twhere "drop a" appears\n'
early=0; total=0
for s in "${cases[@]}"; do
  printf 'struct D(&'"'"'static str);\nimpl Drop for D { fn drop(&mut self) { println!("drop {}", self.0); } }\nfn main() {\n    {\n        %s\n        println!("<next statement>");\n        println!("<block end>");\n    }\n    println!("<after block>");\n}\n' "$s" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>err.txt || { echo "compile failed: $s"; cat err.txt; exit 1; }
  out=$(./g) || exit 1
  pos=$(printf '%s\n' "$out" | awk '/^drop a$/{print prev; found=1; exit} {prev=$0} END{if(!found) print "none"}')
  case $pos in
    '') where='before <next statement>'; early=$((early+1)) ;;
    '<next statement>') where='before <next statement>'; early=$((early+1)) ;;
    '<block end>') where='at block end' ;;
    none) where='never' ;;
    *) where="after: $pos" ;;
  esac
  [ "$pos" = 'drop b' ] && { where='at block end (after drop b)'; }
  row="$s${T}$where"
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 2 ] || { echo "column count $cols != 2"; exit 1; }
  printf '%s\n' "$row"
  total=$((total+1))
done
echo "cells dropped before the next statement: $early / $total"
===== bash r44_grid.sh =====
statement	where "drop a" appears
let _ = D("a");	before <next statement>
let _x = D("a");	at block end
D("a");	before <next statement>
let x = D("a"); let _ = x;	at block end
let x = D("a"); let _y = x;	at block end
let x = D("a"); drop(x);	before <next statement>
let x = D("a"); let x = D("b");	at block end (after drop b)
let mut x = D("a"); x = D("b");	before <next statement>
let n = D("a").0.len();	before <next statement>
let r = &D("a");	at block end
let v = vec![D("a")]; let _ = v.len();	at block end
std::mem::forget(D("a"));	never
cells dropped before the next statement: 5 / 12
(exit 0)
```

- ★★★ **「다음 문장 전에 풀린 칸 5 / 12」** — `let _ = D("a")` · `D("a");` · `drop(x)` · **대입 `x = D("b")`** · `D("a").0.len()`.
- ★★★ **`let _ = D("a")` 는 바로 버려지고 `let _x = D("a")` 는 블록 끝까지 산다.** `_` 는 **이름을 묶지 않는 패턴**이라 값이 **임시값으로 남아 문장 끝에** 버려진다. `_x` 는 **보통 이름**이다 — 밑줄은 「안 쓴다는 경고를 끄는 관례」일 뿐이다.
- ★★★ **그런데 `let x = D("a"); let _ = x;` 는 블록 끝** — `x` 는 **이미 이름이 있는 자리(place)** 라 `_` 가 **옮겨 가지 않는다.** Reference: 와일드카드는 「**복사하지도, 이동하지도, 빌리지도 않는다**」. 그래서 `x` 가 자기 블록 끝에 버려진다((2)에서 확인).
- ★★ **섀도잉 — `a` 는 블록 끝, 그것도 `drop b` 뒤에** 찍혔다. 가려졌을 뿐 **변수는 살아 있고**, 지역 변수는 선언 역순이므로(09번 (6)) 나중의 `b` 가 먼저 간다.
- ★★ **대입 `x = D("b")` — 옛 값 `a` 가 그 자리에서** 버려진다. 새 값이 들어오기 전에 옛 값을 정리하는 것이다.
- ★★ **`let r = &D("a")` — 블록 끝**(임시값 수명 연장). **`D("a").0.len()` — 다음 문장 전**(연장이 없다 — 빌린 결과가 아니라 `usize` 를 남긴다).
- ★ **`vec![D("a")]` 뒤 `let _ = v.len()`** — `v` 가 원소를 쥐고 있으니 블록 끝. **`mem::forget(D("a"))` — 끝내 안 찍혔다**((6)).

비용 — `drop` 호출은 컴파일러가 **컴파일 시점에 정해진 자리**에 끼운다(09번 (6)). 시간은 재지 않았다.

### (2) ★★★ `let _ = x` 대 `let _y = x` — 이동하나

**`_` 로 받은 뒤 `x` 를 쓰면.**

```text
===== 소스: r44_let_underscore.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let x = D("x");
    let _ = x;
    println!("still usable: {}", x.0);
}
===== rustc --edition 2021 r44_let_underscore.rs =====
(exit 0)
===== ./r44_let_underscore =====
still usable: x
drop x
(exit 0)
```

- ★★★ **컴파일되고 `still usable: x` 다음에 `drop x`** — `x` 는 **이동하지 않았다**. `drop` 도 **`x` 의 블록 끝**에서 한 번.

**이름(`_y`)으로 받은 뒤 `x` 를 쓰면.**

```text
===== 소스: r44_let_named.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let x = D("x");
    let _y = x;
    println!("still usable: {}", x.0);
}
===== rustc --edition 2021 r44_let_named.rs =====
error[E0382]: borrow of moved value: `x`
  --> r44_let_named.rs:11:34
   |
 9 |     let x = D("x");
   |         - move occurs because `x` has type `D`, which does not implement the `Copy` trait
10 |     let _y = x;
   |              - value moved here
11 |     println!("still usable: {}", x.0);
   |                                  ^^^ value borrowed here after move
   |
note: if `D` implemented `Clone`, you could clone the value
  --> r44_let_named.rs:1:1
   |
 1 | struct D(&'static str);
   | ^^^^^^^^ consider implementing `Clone` for this type
...
10 |     let _y = x;
   |              - you could clone this value
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(exit 1)
```

- ★★★ **E0382 — borrow of moved value: `x`** · 표지 「value moved here」가 **10행 `let _y = x;`** 를 짚는다. **`_y` 는 보통 변수라 이동이 일어난다.**
- ★★ **판별 한 줄** — **`_` 는 패턴이고 `_y` 는 이름이다.** `let _ = 식` 에서 식이 **값(임시값)** 이면 문장 끝에 버려지고, **자리(변수·필드)** 면 **아무 일도 안 일어난다.** 「`_` 는 바로 drop 한다」는 **절반만 참**이다.

**가드를 `_` 로 받으면 — 락과 `RefCell` 이 갈린다.**

```text
===== 소스: r44_lock.rs =====
use std::sync::Mutex;
fn main() {
    let m = Mutex::new(0);
    let _ = m.lock().unwrap();
    println!("{}", m.try_lock().is_ok());
}
===== rustc --edition 2021 r44_lock.rs =====
error: non-binding let on a synchronization lock
 --> r44_lock.rs:4:9
  |
4 |     let _ = m.lock().unwrap();
  |         ^ this lock is not assigned to a binding and is immediately dropped
  |
  = note: `#[deny(let_underscore_lock)]` (part of `#[deny(let_underscore)]`) on by default
help: consider binding to an unused variable to avoid immediately dropping the value
  |
4 |     let _unused = m.lock().unwrap();
  |          ++++++
help: consider immediately dropping the value
  |
4 -     let _ = m.lock().unwrap();
4 +     drop(m.lock().unwrap());
  |

error: aborting due to 1 previous error

(exit 1)
```

- ★★★ **컴파일 에러다 — `non-binding let on a synchronization lock`**(`#[deny(let_underscore_lock)]` 가 **기본으로 켜져 있다**). 표지 「this lock is not assigned to a binding and is **immediately dropped**」 · `help:` 둘 — `let _unused = …`(블록 끝까지 쥐기) · `drop(…)`(지금 버린다고 적기). **컴파일러가 (1)의 1행을 락에 대해서만은 막는다.**

```text
===== 소스: r44_refcell_guard.rs =====
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(0);
    let _ = c.borrow_mut();
    println!("{}", c.try_borrow_mut().is_ok());
}
===== rustc --edition 2021 r44_refcell_guard.rs =====
(exit 0)
===== ./r44_refcell_guard =====
true
(exit 0)
```

- ★★★ **`RefCell` 가드는 막지 않는다** — `exit 0`, 그리고 곧장 `try_borrow_mut` 가 **`true`**(가드가 이미 반납됐다). **같은 실수가 `Mutex` 면 에러, `RefCell` 이면 조용한 즉시 해제**다. 이 린트는 **동기화 락**만 본다(린트 이름 그대로).

### (3) ★★★ `Drop` 을 단 타입에서 필드를 꺼내면 — E0509, 그리고 `take`

**언제 쓰나** — 정리 로직이 있는 타입(가드·핸들)에서 **알맹이만 빼 가고** 싶을 때.

```text
===== 소스: r44_e0509.rs =====
struct Job {
    name: String,
}

impl Drop for Job {
    fn drop(&mut self) {
        println!("drop job {:?}", self.name);
    }
}

fn main() {
    let j = Job { name: String::from("build") };
    let n = j.name;
    println!("{n}");
}
===== rustc --edition 2021 r44_e0509.rs =====
error[E0509]: cannot move out of type `Job`, which implements the `Drop` trait
  --> r44_e0509.rs:13:13
   |
13 |     let n = j.name;
   |             ^^^^^^
   |             |
   |             cannot move out of here
   |             move occurs because `j.name` has type `String`, which does not implement the `Copy` trait
   |
help: consider borrowing here
   |
13 |     let n = &j.name;
   |             +
help: consider cloning the value if the performance cost is acceptable
   |
13 |     let n = j.name.clone();
   |                   ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0509`.
(exit 1)
```

- ★★★ **E0509 — cannot move out of type `Job`, which implements the `Drop` trait.** 이유 — 나중에 `drop(&mut self)` 가 **`self.name` 을 읽을 수 있어야** 하는데 빼 가면 구멍이 난다(09번 (6)의 「본체 먼저, 필드 나중」과 같은 사실).
- ★★ **`help:` 둘 — `&j.name`(빌리기) · `j.name.clone()`(복제).** **둘 다 「빼 가기」가 아니다** — 구멍 없이 옮기는 도구는 `help:` 에 없다.

**자리에 무언가를 남기고 빼 가면.**

```text
===== 소스: r44_e0509_take.rs =====
use std::mem;

struct Job {
    name: String,
    token: Option<Box<u32>>,
}

impl Drop for Job {
    fn drop(&mut self) {
        println!("drop job name={:?} token={:?}", self.name, self.token);
    }
}

fn main() {
    let mut j = Job { name: String::from("build"), token: Some(Box::new(7)) };
    let n = mem::take(&mut j.name);
    let t = j.token.take();
    let old = mem::replace(&mut j.name, String::from("placeholder"));
    println!("took name={n:?} token={t:?} replaced={old:?}");
}
===== rustc --edition 2021 r44_e0509_take.rs =====
(exit 0)
===== ./r44_e0509_take =====
took name="build" token=Some(7) replaced=""
drop job name="placeholder" token=None
(exit 0)
```

- ★★★ **통과** — `mem::take(&mut j.name)` 가 `"build"` 를 빼 가고 **빈 `String`(`Default`)을 남겼다**, `j.token.take()`(`Option::take`)가 `Some(7)` 을 빼 가고 **`None` 을 남겼다**, `mem::replace` 가 그 빈 값을 **`"placeholder"` 로 바꾸며** 빈 값을 돌려줬다(`replaced=""`).
- ★★★ **`drop` 은 여전히 한 번 돈다 — 남겨 둔 값으로**(`drop job name="placeholder" token=None`). **구멍이 없으니 소멸자가 읽을 것이 있다** — 이것이 E0509 를 푸는 원리다.

| 도구 | 자리에 남기는 것 | 요구 | 안정화 |
|---|---|---|---|
| `mem::take(&mut x)` | `Default::default()` | `T: Default` | 1.40.0 |
| `mem::replace(&mut x, v)` | 내가 준 `v` | 없음 | 1.0.0 |
| `opt.take()`(`Option`) | `None` | 없음 | 1.0.0 |

★ 앞 두 줄의 판은 [11번 주제](../11-borrow-checker-rejections/) 3-answer 5번의 표에서 인용했다.

### (4) ★★ `&mut self` 에서 상태를 옮기려다 E0507 — 열거형 상태 전이

**언제 쓰나** — `Draft(body)` → `Sent(body)` 처럼 **값을 들고 다음 상태로** 넘어가는 상태 기계.

```text
===== 소스: r44_state.rs =====
enum State {
    Draft(String),
    Sent(String),
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match self.state {
            State::Draft(body) => State::Sent(body),
            State::Sent(body) => State::Sent(body),
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
}
===== rustc --edition 2021 r44_state.rs =====
error[E0507]: cannot move out of `self.state` as enum variant `Draft` which is behind a mutable reference
  --> r44_state.rs:12:28
   |
12 |         self.state = match self.state {
   |                            ^^^^^^^^^^
13 |             State::Draft(body) => State::Sent(body),
   |                          ---- data moved here
14 |             State::Sent(body) => State::Sent(body),
   |                         ---- ...and here
   |
   = note: move occurs because these variables have types that don't implement the `Copy` trait
help: consider borrowing here
   |
12 |         self.state = match &self.state {
   |                            +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(exit 1)
```

- ★★ **E0507 — cannot move out of `self.state` as enum variant `Draft` which is behind a mutable reference.** `&mut self` 는 **빌린 것**이라 `self.state` 를 통째로 옮길 수 없다(11번 5번의 필드판과 같은 번호).
- ★★ **`help:` 는 `match &self.state`** — 따라가 보면:

```text
===== 소스: r44_state_help.rs =====
enum State {
    Draft(String),
    Sent(String),
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match &self.state {
            State::Draft(body) => State::Sent(body),
            State::Sent(body) => State::Sent(body),
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
}
===== rustc --edition 2021 r44_state_help.rs =====
error[E0308]: mismatched types
  --> r44_state_help.rs:13:47
   |
13 |             State::Draft(body) => State::Sent(body),
   |                                   ----------- ^^^^ expected `String`, found `&String`
   |                                   |
   |                                   arguments to this enum variant are incorrect
   |
note: tuple variant defined here
  --> r44_state_help.rs:3:5
   |
 3 |     Sent(String),
   |     ^^^^
help: try using a conversion method
   |
13 |             State::Draft(body) => State::Sent(body.to_string()),
   |                                                   ++++++++++++

error[E0308]: mismatched types
  --> r44_state_help.rs:14:46
   |
14 |             State::Sent(body) => State::Sent(body),
   |                                  ----------- ^^^^ expected `String`, found `&String`
   |                                  |
   |                                  arguments to this enum variant are incorrect
   |
note: tuple variant defined here
  --> r44_state_help.rs:3:5
   |
 3 |     Sent(String),
   |     ^^^^
help: try using a conversion method
   |
14 |             State::Sent(body) => State::Sent(body.to_string()),
   |                                                  ++++++++++++

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
(exit 1)
```

- ★★★ **E0308 두 개 — expected `String`, found `&String`**(각 팔의 `body` 가 이제 참조다). `help:` 는 **변환 메서드**(`to_string()` 류 — 복제)를 권한다. **빌리면 옮길 수 없고, 옮기려면 복제해야 한다** — `help:` 사슬은 복제로 끝난다.
- ★★★ **복제 없이 옮기는 길 — 잠깐 다른 값을 넣어 두고 꺼낸다.**

```text
===== 소스: r44_state_fix.rs =====
use std::mem;

enum State {
    Draft(String),
    Sent(String),
    Empty,
}

struct Mail {
    state: State,
}

impl Mail {
    fn send(&mut self) {
        self.state = match mem::replace(&mut self.state, State::Empty) {
            State::Draft(body) => State::Sent(body),
            other => other,
        };
    }
}

fn main() {
    let mut m = Mail { state: State::Draft(String::from("hi")) };
    m.send();
    match &m.state {
        State::Sent(b) => println!("sent {b}"),
        State::Draft(_) => println!("draft"),
        State::Empty => println!("empty"),
    }
}
===== rustc --edition 2021 r44_state_fix.rs =====
(exit 0)
===== ./r44_state_fix =====
sent hi
(exit 0)
```

- ★★ **`mem::replace(&mut self.state, State::Empty)`** 가 옛 상태를 **소유권째** 돌려주고 자리에 `Empty` 를 남긴다 → `match` 가 `body` 를 **옮겨** 새 상태를 만들고 → 대입이 `Empty` 를 덮는다(`sent hi`). `State: Default` 가 없어서 `take` 대신 `replace` 를 썼다.
- ★ **대가** — 「비어 있는 상태」라는 변형(`Empty`)이 타입에 하나 생긴다. `match` 가 그 변형을 다뤄야 한다(`State::Empty => …`).

### (5) ★★ 패닉 중에도 `drop` 은 불린다 — 전략과 언어를 바꿔 보면

**기본(되감기, unwind).**

```text
===== 소스: r44_panic.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        eprintln!("drop {}", self.0);
    }
}

fn inner() {
    let _i = D("inner");
    panic!("stop");
}

fn main() {
    let _m = D("main");
    eprintln!("[1] calling inner");
    inner();
    eprintln!("[2] after inner");
}
===== rustc --edition 2021 r44_panic.rs =====
(exit 0)
===== ./r44_panic =====
[1] calling inner

thread 'main' (1257992) panicked at r44_panic.rs:10:5:
stop
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
drop inner
drop main
(exit 101)
```

- ★★★ **패닉 메시지 뒤에 `drop inner` → `drop main`** — 되감기가 **안쪽 프레임부터** 지역 값을 정리했다. **`[2]` 는 안 찍혔다.** 종료 **`101`**.
- ★ 마커를 전부 **표준 오류**로 찍었다(규칙 18) — 패닉 메시지와 한 스트림이라 순서가 고정된다.

**같은 소스를 `-C panic=abort` 로.**

```text
===== 소스: r44_panic.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        eprintln!("drop {}", self.0);
    }
}

fn inner() {
    let _i = D("inner");
    panic!("stop");
}

fn main() {
    let _m = D("main");
    eprintln!("[1] calling inner");
    inner();
    eprintln!("[2] after inner");
}
===== rustc --edition 2021 -C panic=abort -o r44_panic_abort r44_panic.rs =====
(exit 0)
===== ./r44_panic_abort =====
[1] calling inner

thread 'main' (1258068) panicked at r44_panic.rs:10:5:
stop
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 134)
```

- ★★★ **`drop` 줄이 하나도 없다 · 종료 `134`**(`SIGABRT`). Reference: 「**패닉 처리기가 abort 로 설정되어 있으면** 패닉은 되감기 없이 프로세스를 끝낸다 — **소멸자가 실행되지 않는다**」. 되감기는 **언어의 보장이 아니라 패닉 전략의 성질**이다.

**C++ — 잡히지 않은 예외.**

```text
===== 소스: r44_uncaught.cpp =====
#include <cstdio>
#include <stdexcept>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) {}
    ~D() { std::fprintf(stderr, "~D %s\n", tag); }
};

void inner() {
    D i{"inner"};
    throw std::runtime_error("stop");
}

int main() {
    D m{"main"};
    std::fprintf(stderr, "[1] calling inner\n");
    inner();
    std::fprintf(stderr, "[2] after inner\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic r44_uncaught.cpp -o r44_uncaught =====
(exit 0)
===== ./r44_uncaught =====
[1] calling inner
terminate called after throwing an instance of 'std::runtime_error'
  what():  stop
(exit 134)
```

- ★★★ **소멸자 줄 `~D` 가 하나도 없다 · `terminate called after throwing …` · `134`.** cppreference: 「잡히지 않은 예외에서 **되감기가 일어나는지는 구현 정의**」 — 이 판(g++ 13 · libstdc++)은 **되감지 않았다.**

```text
===== 소스: r44_caught.cpp =====
#include <cstdio>
#include <stdexcept>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) {}
    ~D() { std::fprintf(stderr, "~D %s\n", tag); }
};

void inner() {
    D i{"inner"};
    throw std::runtime_error("stop");
}

int main() {
    D m{"main"};
    std::fprintf(stderr, "[1] calling inner\n");
    try {
        inner();
    } catch (const std::exception& e) {
        std::fprintf(stderr, "[catch] %s\n", e.what());
    }
    std::fprintf(stderr, "[2] after inner\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic r44_caught.cpp -o r44_caught =====
(exit 0)
===== ./r44_caught =====
[1] calling inner
~D inner
[catch] stop
[2] after inner
~D main
(exit 0)
```

- ★★ **잡으면 전부 돈다** — `~D inner` → `[catch]` → … → `~D main`. C++ 갈래 [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/2-summary.md) (2)가 세 층을 지나는 되감기를 전수로 쟀다.

| | Rust `panic=unwind`(기본) | Rust `panic=abort` | C++ 잡힘 | C++ 안 잡힘(g++ 13) |
|---|---|---|---|---|
| 정리 코드 | ★ **돈다** | **안 돈다** | 돈다 | ★ **안 돈다**(구현 정의) |
| 종료 코드 | `101` | `134` | `0` | `134` |

★★ **대비의 요지** — Rust 는 **`main` 을 빠져나가는 패닉도 되감는다**(잡는 코드가 없어도). C++ 은 **잡는 `catch` 가 없으면 되감기 여부를 구현에 맡긴다.** RAII 의 「경로와 무관하게 정리된다」는 약속([C++ 15번](../../../cpp/syntax/15-raii-resources-as-types/2-summary.md))이 **잡히지 않은 예외 한 칸에서는 이 판에서 깨졌다.**

### (6) ★ `mem::forget` — 안전 함수인데 `drop` 을 안 부른다

```text
===== 소스: r44_forget.rs =====
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) {
        println!("drop {}", self.0);
    }
}

fn main() {
    let a = D("a");
    let b = D("b");
    std::mem::forget(a);
    println!("[1] after forget(a)");
    drop(b);
    println!("[2] end of main");
}
===== rustc --edition 2021 r44_forget.rs =====
(exit 0)
===== ./r44_forget =====
[1] after forget(a)
drop b
[2] end of main
(exit 0)
```

- ★★ **`drop b` 는 찍히고 `drop a` 는 끝내 안 찍힌다.** `forget` 은 값을 먹고 **소멸자를 부르지 않는다.**
- ★★★ **`unsafe` 블록이 없다** — std §Safety: 「**Rust 의 안전성 보장에는 소멸자가 반드시 실행된다는 보장이 들어 있지 않다.** `Rc` 로 순환을 만들거나 `process::exit` 로 끝낼 수 있다. 그래서 안전한 코드에서 `mem::forget` 을 허용해도 보장이 근본적으로 바뀌지 않는다」.
- ★★ **층 가르기** — **「`drop` 이 불린다」는 정상 경로의 언어 규칙**(스코프 끝·대입·되감기)이고, **「반드시 불린다」는 언어 보장이 아니다**(`forget` · [41번](../41-rc-arc-shared-ownership-and-weak-cycles/)의 순환 · `panic=abort`). 그래서 **`Drop` 에 안전성을 걸면 안 된다** — `unsafe` 코드는 `forget` 이 가능하다는 전제 위에서 짜야 한다(std).

## 문법 — 형태와 규칙

```text
   impl Drop for T { fn drop(&mut self) { … } }     ← 직접 부르지 않는다 (x.drop() 은 E0040 — 09번 (7))
   drop(x);                                          ← 소유권을 먹는 빈 몸통 함수 — 그 자리에서 버린다
   std::mem::forget(x);                              ← 버리지 않고 잊는다 (안전 함수)
   std::mem::take(&mut slot)                         ← 빼 가고 Default 를 남긴다   (T: Default)
   std::mem::replace(&mut slot, v)                   ← 빼 가고 v 를 남긴다
   opt.take()                                        ← Option 에서 빼 가고 None 을 남긴다
   let _ = 식;    let _name = 식;                    ← _ 는 묶지 않는다 · _name 은 묶는다(이동)
```

- ★★★ **변수는 블록 끝(선언 역순), 임시값은 문장 끝, `let` 에서 빌린 임시값은 블록 끝**((1)).
- ★★★ **`_` 는 이동하지 않는다 — 값 식이면 문장 끝에 버려지고, 자리 식이면 아무 일도 없다**((2)).
- ★★★ **`Drop` 을 단 타입과 `&mut` 뒤의 값에서는 옮길 수 없다 — 자리에 무언가를 남기고 바꿔 들고 나온다**((3)·(4)).
- ★★ **되감기는 패닉 전략의 성질이다 — `panic=abort` 면 `drop` 이 없다**((5)).

## 어디서 틀리나

### 1. ★★★ 「`let _ = x;` 는 `x` 를 바로 버린다」

(1)·(2) — **이동하지 않는다.** `x` 는 블록 끝까지 살고 **그 뒤에도 쓸 수 있다.** 바로 버려지는 것은 `let _ = D("a")` 처럼 **값을 새로 만든** 경우다.

### 2. ★★★ 「`let _guard = lock()` 과 `let _ = lock()` 은 같다」

(1)의 1·2행 — **`_guard` 는 블록 끝, `_` 는 그 문장 끝.** ★ `Mutex` 가드는 rustc 가 **기본 거부 린트**(`let_underscore_lock`)로 막아 준다((2)). **`RefCell` 가드는 안 막는다** — 에러도 경고도 없이 그 자리에서 반납된다((2)의 `r44_refcell_guard`).

### 3. ★★ 「섀도잉하면 앞의 값은 바로 버려진다」

(1) — **블록 끝까지 산다**(그리고 뒤의 값보다 늦게 간다). 바로 버리고 싶으면 **대입**이나 `drop`.

### 4. ★★ 「E0509 는 `clone()` 으로 푼다」

(3) — `help:` 가 권하지만 **복제는 빼 가기가 아니다.** 옮기려면 **`take`·`replace`·`Option::take`**.

### 5. ★★ 「E0507 의 `help:`(빌리기)를 따르면 된다」

(4) — **E0308 두 개**가 이어진다. 빌리면 옮길 수 없다 — **`mem::replace` 로 임시 값을 넣고 꺼낸다.**

### 6. ★★ 「패닉이 나면 정리 코드가 안 돈다」 / 「반드시 돈다」

(5) — **기본(unwind)은 돈다, `panic=abort` 는 안 돈다.** 둘 다 참이 아니다 — **전략이 정한다.**

### 7. ★ 「`mem::forget` 은 위험하니 `unsafe` 다」

(6) — **안전 함수**다. 안 불리는 소멸자는 **안전성 위반이 아니다**(std).

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 변수·임시값·`let` 빌림 임시값이 버려지는 자리 | ★ **언어**(Reference — Destructors) | (1) |
| 와일드카드 `_` 는 이동·복사·빌림을 안 한다 | ★ **언어**(Reference — Patterns) | (2) |
| `Drop` 구현체에서 필드 이동 금지 | ★ **언어** | (3) E0509 |
| `take`/`replace`/`Option::take` 의 동작 | ★ **std 의 API** | (3)·(4) |
| 되감기 중 `drop` 이 불린다 | ★ **`panic=unwind` 전략의 성질** — `abort` 면 아니다(Reference) | (5) |
| 소멸자가 **반드시** 불린다 | ★ **보장되지 않는다**(std `forget` §Safety) | (6) |
| 패닉 종료 코드 `101` · abort `134` | ★ **std 런타임 관행 · OS 시그널**(이 판 관찰) | (5) |
| C++ 잡히지 않은 예외의 되감기 | ★ **구현 정의** — g++ 13 은 안 되감았다(관찰) | (5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 정리를 **지금** 하고 싶다 | **`drop(x)`** | (1) |
| 가드·핸들을 스코프 끝까지 쥐어야 한다 | **`let _guard = …`** — `let _ =` 아님(락이면 린트가 막고, `RefCell` 이면 안 막는다) | (1)·(2) |
| `Drop` 타입에서 알맹이를 빼 간다 | **`mem::take`**(`Default` 있으면) · **`replace`** · **`Option::take`** | (3) |
| `&mut self` 에서 상태를 넘긴다 | **`mem::replace(&mut self.s, 빈 상태)`** | (4) |
| 정리를 **하지 않아야** 한다(FFI 로 소유권을 넘김) | `mem::forget` / `ManuallyDrop` | (6) · std |
| 패닉 때도 정리가 필요하다 | 기본 `panic=unwind` 를 유지 — **`abort` 를 켜면 `drop` 이 없다** | (5) |

## 핵심 문장

- ★★★ **변수는 블록 끝에, 임시값은 문장 끝에 버려진다 — `let _ = 값` 은 바로, `let _x = 값` 은 블록 끝.**
- ★★★ **`_` 는 이동하지 않는다 — `let _ = x;` 뒤에도 `x` 는 살아 있다(E0382 가 안 난다).**
- ★★★ **`Drop` 을 단 타입(E0509)과 `&mut` 뒤(E0507)에서는 옮길 수 없다 — `take`/`replace` 로 자리에 값을 남기고 꺼낸다. 소멸자는 남긴 값으로 돈다.**
- ★★ **되감기 중에도 `drop` 은 돈다 — 단 `panic=abort` 면 아니고, C++ 의 잡히지 않은 예외는 구현이 정한다(g++ 13 은 안 돌았다).**
- ★ **`mem::forget` 은 안전 함수다 — 소멸자 실행은 Rust 의 안전성 보장이 아니다.**

## 관련 자료

- [**09번 주제**](../09-copy-clone-and-drop/) — 지역·필드·튜플·`Vec`·인자 순서 · E0184 · E0040. **그쪽은 「어떤 순서로」, 여기는 「문장 단위로 언제」와 「막힌 자리를 푸는 법」.**
- [**08번 주제**](../08-ownership-and-move/) — E0509 의 첫 등장.
- [**11번 주제**](../11-borrow-checker-rejections/) — `mem::take`·`replace`·`swap` 표 · 필드판 E0507.
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — 순환이 `drop` 을 막는 다른 길.
- [**42번 주제**](../42-refcell-cell-interior-mutability/) — 가드가 반납되는 순간이 곧 이 편의 해제 시점이다.
- C++ 갈래 [`14-destructors-and-deterministic-destruction`](../../../cpp/syntax/14-destructors-and-deterministic-destruction/2-summary.md) · [`15-raii-resources-as-types`](../../../cpp/syntax/15-raii-resources-as-types/2-summary.md) — **C++ 멤버는 선언 역순**(14번 (1)) — Rust 필드는 **선언 순**(09번 (6)) — 방향이 반대다.

## 용어 풀이

- **`Drop`** — 값이 버려질 때 한 번 불리는 정리 코드를 다는 트레이트.
- **`mem::drop`** — 값을 먹고 아무것도 안 하는 함수. 먹는 순간 스코프가 끝나 버려진다.
- **`mem::forget`** — 값을 먹고 **소멸자를 부르지 않는** 함수.
- **`mem::take` / `mem::replace`** — `&mut` 자리에서 값을 빼 가고 기본값 / 준 값을 남긴다.
- **되감기(unwinding)** — 패닉이 스택을 거슬러 올라가며 각 프레임의 값을 버리는 것.
- **자리 식(place expression)** — 메모리 위치를 가리키는 식(변수·필드·`*p`). 값 식(value expression)과 짝.
- **와일드카드 패턴 `_`** — 무엇이든 맞지만 **묶지 않는** 패턴.

## 더 들어가면

- `ManuallyDrop<T>` — `forget` 을 값의 타입으로 옮긴 것(필드 단위로 소멸자를 끈다). **이 문서는 던지지 않았다.**
- 패닉 중 `drop` 에서 **또 패닉하면** 프로세스가 abort 된다(std `Drop` 문서의 Panics 절). **던지지 않았다.**
- 2024 에디션의 **꼬리식 임시값** 규칙 변화 — [42번](../42-refcell-cell-interior-mutability/) (2)와 [11번](../11-borrow-checker-rejections/) 10번.
