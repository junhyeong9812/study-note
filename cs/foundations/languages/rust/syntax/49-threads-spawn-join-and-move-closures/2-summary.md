# rust/syntax/49 — 스레드 `spawn`/`join` 과 `move` 클로저 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `thread::spawn`](https://doc.rust-lang.org/std/thread/fn.spawn.html)(시그니처 `F: FnOnce() -> T + Send + 'static, T: Send + 'static` · 「`'static` 제약」 절) ·
> [std — `thread::scope`](https://doc.rust-lang.org/std/thread/fn.scope.html)(「자동으로 join 된다」 · §Panics) ·
> [std — `JoinHandle`](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html)(「버려지면 스레드를 detach 한다」 · `join` 의 `Result`) ·
> [std — `std::thread` 모듈 문서](https://doc.rust-lang.org/std/thread/index.html)(「main 스레드가 끝나면 프로그램 전체가 끝난다」) ·
> [Reference — Closure types · Capture precision](https://doc.rust-lang.org/reference/types/closure.html)(`[type.closure.capture.precision.dereference-shared]` 「Rightmost shared reference truncation」).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(에디션 탐침 하나는 2018·2021·2024 셋).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★★ **스레드를 만드는 비용·속도는 한 번도 재지 않았다** — 「스레드는 무겁다」 류의 문장은 근거가 없으므로 쓰지 않는다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① `move` 필요 격자(스레드에 넘기는 값마다 컴파일되나 / 첫 진단 줄)다.** 스레드에 무엇을 넘길 수 있는가는 **실행이 아니라 컴파일러가** 판정한다 — 그래서 창도 컴파일 로그다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread '<unnamed>' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| ★ **흔들릴 수 있다(선언)** | detach 탐침의 **판 수** `runs with child line N / 20` | 자식이 50ms 자고, main 이 0ms 또는 300ms 기다린다 — **시간 여유**에 기대는 칸이다. 이 머신에서 두 번의 캡처가 같았지만 보장이 아니다 |
| 안 흔들린다 | ★★★ **격자의 컴파일 칸과 「`compiling cells: 7 / 13`」** | 캡처·빌림 규칙은 언어가 정한다 — **이 주제의 본체** |
| 안 흔들린다 | E0373 · E0382 · E0597 · E0499 · E0502 번호·`파일:줄:칸` · 종료 코드 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 스레드 id **비교 결과**(`true`/`false`) · 스레드 이름 | 숫자 자체는 싣지 않는다 — 「같은가」만 찍는다 |
| 안 흔들린다 | `thread::scope` 의 순서 로그 | 자식이 100ms 자고 main 은 기다리므로 **scope 끝의 join 이 순서를 정한다** |

★ 정규화 규칙은 **기본 넷**만 쓴다(패닉 스레드 id 가 걸린다). detach 판 수는 정규화하지 않는다 — 달라지면 **고칠 것이 아니라 이 칸이 흔들린 것**이고, 그때는 본문의 「시간 여유」 문장을 다시 본다.

## 한눈에 — 쉽게 말하면

**스레드에 클로저를 넘기는 것은 「택배로 짐을 부치는 것」이다.
내 방에 있는 물건을 **가리키는 쪽지**(빌림)만 넣어 보내면, 받는 사람이 열어 볼 때쯤 내가 이사 가고 없을 수 있다.
그래서 택배 회사(`thread::spawn`)는 **물건 자체를 넣어라**(`move`)거나 **영원히 그 자리에 있는 것만 가리켜라**(`'static`)고 요구한다.
`thread::scope` 는 「**택배가 돌아올 때까지 나는 이 방을 안 나간다**」고 약속하는 것이다 — 그러면 쪽지만 보내도 된다.**

| 비유 | 실체 |
|---|---|
| 「**쪽지만 넣은 택배**」 | ★★ **빌림으로 잡힌 클로저** — `thread::spawn(\|\| v.len())` → **E0373**((1)의 1행) |
| 「**물건째 넣은 택배**」 | ★★ **`move` 클로저** — `v` 가 스레드로 **이동**한다((1)의 2행). 그 뒤 main 은 `v` 를 못 쓴다(3행 E0382) |
| 「**택배사 규정: 영원히 있는 것만**」 | ★★★ **`spawn` 의 `F: 'static`** — 스레드가 **자기를 만든 함수보다 오래 살 수 있어서**다(std) |
| 「**쪽지를 물건째 넣어도 안 된다**」 | ★★ **참조를 `move` 해도** 그 참조가 가리키는 것은 여전히 지역 변수 — **E0597**((2)) |
| 「**돌아올 때까지 방을 안 나간다는 약속**」 | ★★★ **`thread::scope`** — 스코프 끝에서 **자동 join**. 그래서 **빌림이 허용된다**((1)의 10·11행 · (5)) |
| 「**배송 결과 통지서**」 | ★★ **`join()` 의 `Result`** — 스레드가 패닉하면 `Err(패닉 값)`((3)) |
| 「**송장을 버린 택배**」 | ★ **`JoinHandle` 을 버림 = detach** — 기다릴 방법이 없다. main 이 먼저 끝나면 **프로그램째 끝난다**((4)) |

```text
   같은 v.len(), 넘기는 방법만 다르다 — (1)의 행 그대로

   thread::spawn(|| v.len())                  thread::spawn(move || v.len())          thread::scope(|s| s.spawn(|| v.len()))
   ───────────────────────────                ─────────────────────────────           ──────────────────────────────────────
   클로저가 &v 를 쥔다                          클로저가 v 를 쥔다(이동)                  클로저가 &v 를 쥔다
   spawn 은 'static 을 요구 → E0373            'static 만족 → 통과                      scope 가 끝나기 전에 join → 통과
   (main 보다 오래 살 수 있으니까)              main 은 v 를 더 못 쓴다(E0382)           main 은 scope 뒤에도 v 를 쓴다
```

> **`'static` 경계** — 「이 값은 **프로그램이 끝날 때까지** 유효해도 된다」는 약속. 빌린 참조를 품은 값은 대개 이것을 못 지킨다.\
> 예: `String` 을 소유한 클로저는 `'static` 이고, `&v` 를 쥔 클로저는 아니다.

> **scoped thread(스코프 스레드)** — `thread::scope` 안에서 만든 스레드. std: 「스코프 안에서 만든 스레드 중 **직접 join 하지 않은 것은 이 함수가 돌아오기 전에 자동으로 join 된다**」.\
> 예: `thread::scope(|s| { s.spawn(|| v.push(4)); });` 뒤에 `v` 를 그대로 쓴다.

## 이 주제가 답하려는 질문

1. ★★★ **스레드에 데이터를 넘길 때 왜 `move` 가 필요한가 — 수명으로** — `'static` 요구, 그리고 `move` 가 **충분조건도 필요조건도 아닌** 자리((1)·(2)).
2. ★★★ **`thread::scope` 는 그 제약을 어떻게 푸나** — 「끝나기 전에 반드시 join」이라는 약속을 **타입(`'scope`)으로** 건다((1)의 10\~13행 · (5)).
3. ★★ **`join` 이 돌려주는 것, 그리고 `join` 하지 않은 스레드의 운명**((3)·(4)).

★ **선행** — [**34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/) (4)가 `thread::spawn(|| v.len())` 의 **E0373 전문**과 `help:` 대로 `move` 를 붙인 통과를 **이미 쟀다** — 이 편은 그것을 **넘기는 값의 격자**로 넓힌다.
같은 편 (6)이 **2021 정밀 포착**(에디션 격자)을 보였다 — (1)의 `&'static str` 행은 그 규칙의 **다른 조항**이다.
[**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) (3)이 `Rc` 를 스레드로 보내면 **E0277**, `Arc` 로 바꾸면 통과하고 strong count 가 **2 → 1** 로 돌아오는 것을 쟀다 — (1)의 `Arc` 행은 그 판이다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① `move` 필요 격자다

**쓰는 창 / 부적용인 창**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **`move` 필요 격자**(넘기는 값마다 소스를 만들어 **컴파일**) | 어느 모양이 통과하나 · 막히면 **무슨 번호로** | ★ **본체**((1)) |
| ② ★★ **에디션 탐침**(2018 × 2021 × 2024) | 같은 소스의 캡처가 에디션마다 다른가 | 쓴다((1)의 `&'static str` 행) |
| ③ ★★ **`join` 의 반환값 로그** | 패닉이 `Err` 로 오나 · 패닉 값의 타입 | 쓴다((3)) |
| ④ ★ **판 수 격자**(같은 바이너리 × 20판) | detach 한 자식의 출력이 **몇 판에서** 살아남나 | 쓴다((4)) |
| ⑤ **스레드 id 비교 · 이름** | 서로 다른 스레드인가 | 쓴다((6)) — **숫자는 싣지 않는다** |
| 스레드 생성 비용 · 속도 | 「스레드는 무겁다」 | ★ **부적용 — 재지 않는다** |
| 데이터 레이스 탐지(TSan · Miri) | — | ★ **잴 것이 없다** — 이 편의 탐침은 **공유 가변 상태가 없다.** 공유는 [50번 주제](../50-send-sync-in-compiler-errors/)·[52번 주제](../52-mutex-rwlock-arc-and-poisoning/)의 몫 |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「main 이 먼저 끝나면 자식은 어떻게 되나」는 원래 **프로세스·스레드 상태**를 봐야 답하는 질문이다(OS 의 창). 그 창은 이 문서에 없다 — 같은 질문을 **「자식의 출력이 몇 판에서 찍혔나」라는 판 수 창**으로 옮겨 물었다((4)).
★ 바꾼 창이 **못 보는 것** — 자식이 **출력 전에 무엇을 하고 있었는지**. 판 수는 「찍혔나」만 말한다. 파일 쓰기처럼 **반쯤 된 부작용**은 이 창에 안 보인다.

### (1) ★★★ `move` 필요 격자 — 열세 가지 넘기기

**언제 쓰나** — `thread::spawn` 에 클로저를 넘기다 E0373 을 만났을 때, 「`move` 만 붙이면 되나」를 판정할 때마다.

```text
===== 소스: r49_grid.sh =====
# 스레드에 넘기는 값마다 프로그램을 하나씩 만들어 던진다 — 컴파일되나, 안 되면 첫 진단 줄은 무엇인가
S=$'\x1f'
cases=(
  "local Vec, no move${S}let v = vec![1, 2, 3]; let h = thread::spawn(|| v.len()); println!(\"{}\", h.join().unwrap());"
  "local Vec, move${S}let v = vec![1, 2, 3]; let h = thread::spawn(move || v.len()); println!(\"{}\", h.join().unwrap());"
  "local Vec, move, then v.len() in main${S}let v = vec![1, 2, 3]; let h = thread::spawn(move || v.len()); println!(\"{} {}\", h.join().unwrap(), v.len());"
  "Arc clone, move${S}let a = Arc::new(vec![1, 2, 3]); let b = Arc::clone(&a); let h = thread::spawn(move || b.len()); println!(\"{} {}\", h.join().unwrap(), a.len());"
  "Arc, no move${S}let a = Arc::new(vec![1, 2, 3]); let h = thread::spawn(|| a.len()); println!(\"{}\", h.join().unwrap());"
  "local of type &'static str, no move${S}let s: &'static str = \"abc\"; let h = thread::spawn(|| s.len()); println!(\"{}\", h.join().unwrap());"
  "string literal inside the closure${S}let h = thread::spawn(|| \"abc\".len()); println!(\"{}\", h.join().unwrap());"
  "static item, no move${S}let h = thread::spawn(|| V.len()); println!(\"{}\", h.join().unwrap());"
  "reference to local Vec, move${S}let v = vec![1, 2, 3]; let r = &v; let h = thread::spawn(move || r.len()); println!(\"{}\", h.join().unwrap());"
  "scope: shared borrow${S}let v = vec![1, 2, 3]; let n = thread::scope(|s| s.spawn(|| v.len()).join().unwrap()); println!(\"{} {}\", n, v.len());"
  "scope: one mutable borrow${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.push(4)); }); println!(\"{}\", v.len());"
  "scope: two mutable borrows${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.push(4)); s.spawn(|| v.push(5)); }); println!(\"{}\", v.len());"
  "scope: shared + mutable${S}let mut v = vec![1, 2, 3]; thread::scope(|s| { s.spawn(|| v.len()); s.spawn(|| v.push(5)); }); println!(\"{}\", v.len());"
)
printf 'case\tcompiles\tfirst diagnostic line / stdout\n'
ok=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%"$S"*}
  body=${spec#*"$S"}
  printf 'use std::sync::Arc;\nuse std::thread;\nstatic V: [i32; 3] = [1, 2, 3];\nfn main() {\n    %s\n}\n' "$body" > g.rs
  if rustc --edition 2021 -A unused -o g g.rs 2>cc.txt; then
    out=$(./g 2>&1 | tr '\n' ' ')
    row="$label${S}yes${S}stdout: ${out% }"
    ok=$((ok+1))
  else
    row="$label${S}no${S}$(grep -m1 '^error' cc.txt)"
  fi
  cols=$(printf '%s' "$row" | awk -F"$S" '{print NF}')
  [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
  printf '%s\n' "$row" | tr "$S" '\t'
  m=$((m+1))
done
echo "compiling cells: $ok / $m"
===== bash r49_grid.sh =====
case	compiles	first diagnostic line / stdout
local Vec, no move	no	error[E0373]: closure may outlive the current function, but it borrows `v`, which is owned by the current function
local Vec, move	yes	stdout: 3
local Vec, move, then v.len() in main	no	error[E0382]: borrow of moved value: `v`
Arc clone, move	yes	stdout: 3 3
Arc, no move	no	error[E0373]: closure may outlive the current function, but it borrows `a`, which is owned by the current function
local of type &'static str, no move	yes	stdout: 3
string literal inside the closure	yes	stdout: 3
static item, no move	yes	stdout: 3
reference to local Vec, move	no	error[E0597]: `v` does not live long enough
scope: shared borrow	yes	stdout: 3 3
scope: one mutable borrow	yes	stdout: 4
scope: two mutable borrows	no	error[E0499]: cannot borrow `v` as mutable more than once at a time
scope: shared + mutable	no	error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
compiling cells: 7 / 13
(exit 0)
```

- ★★★ **「`compiling cells: 7 / 13`」.** 막힌 여섯 칸이 **네 가지 번호**로 갈린다 — E0373(1·5행) · E0382(3행) · E0597(9행) · E0499·E0502(12·13행).
- ★★★ **1행 대 2행 — `move` 가 푸는 것.** 1행의 클로저는 `v.len()` 이 읽기뿐이라 `v` 를 **빌림으로** 잡는다. `spawn` 은 `F: 'static` 을 요구하는데 `&v` 는 `main` 의 지역 변수를 가리킨다 — **E0373 「closure may outlive the current function」**. `move` 는 `v` 를 클로저 **안으로 옮겨** 클로저가 빌림을 하나도 안 품게 만든다.
- ★★ **3행 — 옮겼으면 main 에는 없다.** `move` 뒤에 main 이 `v.len()` 을 부르면 **E0382 「borrow of moved value」**. 스레드와 main 이 **둘 다** 쓰려면 4행처럼 **`Arc` 를 복제해 복제본을 옮긴다**(`stdout: 3 3`) — 41번 (3)의 판이다.
- ★★ **5행 — `Arc` 라고 저절로 되지 않는다.** `move` 없이 `a.len()` 을 부르면 `Arc` 도 **빌림으로** 잡혀 E0373. **`Arc` 가 해 주는 것은 「주인 여럿」이지 「빌림을 안 한다」가 아니다.**
- ★★★ **6행 — `move` 가 없어도 통과한 칸.** 지역 변수 `s` 의 타입이 `&'static str` 이면 `|| s.len()` 이 **`move` 없이 컴파일된다.** 아래 (1-1)에서 에디션을 바꿔 확인한다.
- ★ 7·8행 — 문자열 리터럴·`static` 항목은 처음부터 `'static` 이라 **잡을 지역 변수가 없다.**
- ★★★ **9행 — `move` 해도 안 되는 칸.** `r = &v` 를 옮기면 클로저는 **참조를 소유**할 뿐, 그 참조가 가리키는 `v` 는 여전히 main 의 지역 변수다 — **E0597** ((2)).
- ★★★ **10\~13행 — `thread::scope` 는 빌림을 허용한다.** 공유 빌림(10행) · 가변 빌림 하나(11행, `stdout: 4`)가 통과하고, **빌림 규칙은 그대로 남는다** — 가변 둘은 E0499(12행), 공유+가변은 E0502(13행). 스레드가 둘이어도 **한 함수 안의 두 빌림**과 똑같이 검사된다.

```text
   spawn 이 받는 클로저가 품은 것 — (1)의 통과/막힘이 이 표로 갈린다

   품은 것                             'static 인가       결과
   ────────────────────────────────    ──────────────    ───────────────────────────
   &v   (빌림으로 잡힘)                  아니다             E0373               1·5행
   v    (move 로 이동)                   그렇다             통과 — main 은 v 를 잃는다  2·3행
   Arc 복제본 (move 로 이동)             그렇다             통과 — 둘 다 쓴다         4행
   &*s  (s: &'static str, 2021 정밀 포착) 그렇다             통과                     6행
   &v 를 담은 r (move 로 이동)           아니다             E0597                    9행
   scope 안의 &v / &mut v                'scope 면 된다     통과 — 빌림 규칙은 그대로  10~13행
```

#### (1-1) ★★ `&'static str` 행 — 에디션을 바꾸면

```text
===== 소스: r49_static_str.rs =====
use std::thread;

fn main() {
    let s: &'static str = "abc";
    let h = thread::spawn(|| s.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r49_static_str.rs =====
(exit 0)
===== ./r49_static_str =====
3
(exit 0)
```

```text
===== 소스: r49_static_str_ed.sh =====
# 같은 소스를 세 에디션으로 — 컴파일되나
for e in 2018 2021 2024; do
  if rustc --edition "$e" -o s_$e r49_static_str.rs 2>cc.txt; then
    echo "edition $e: compiles, stdout $(./s_$e)"
  else
    echo "edition $e: $(grep -m1 '^error' cc.txt)"
  fi
done
===== bash r49_static_str_ed.sh =====
edition 2018: error[E0373]: closure may outlive the current function, but it borrows `s`, which is owned by the current function
edition 2021: compiles, stdout 3
edition 2024: compiles, stdout 3
(exit 0)
```

- ★★★ **2018 은 E0373, 2021·2024 는 통과.** 2018 의 클로저는 **변수 `s` 를 통째로** 빌린다(`&s` — main 의 지역 변수를 가리키는 참조). 2021 의 클로저는 **쓴 자리(`*s`)만** 잡는데, Reference 가 여기에 조항 하나를 둔다 —
  **「Rightmost shared reference truncation」** — 캡처 경로가 **공유 참조를 역참조**하면 그 역참조에서 잘라 잡는다(`[type.closure.capture.precision.dereference-shared]`). 그 결과 클로저가 쥔 것은 `&'static str` 을 **다시 빌린 `'static` 참조**가 되고 `'static` 요구를 만족한다.
- ★ Reference 가 든 이유 — 「**필요 이상으로 짧은 수명을 피하려고**」. 이 칸이 정확히 그 효과다.
- ★ 그래서 「**`'static` 문자열도 스레드에 넘기려면 `move` 가 필요하다**」는 **2018 에서만 참**이다. 34번 (6)의 정밀 포착 격자와 같은 뿌리 — **2021 캡처는 변수가 아니라 자리(place)를 잡는다.**

### (2) ★★ 참조를 `move` 해도 — E0597

**언제 쓰나** — 「`move` 를 붙였는데 왜 아직도 수명 에러인가」.

```text
===== 소스: r49_e0597.rs =====
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let r = &v;
    let h = thread::spawn(move || r.len());
    println!("{}", h.join().unwrap());
}
===== rustc --edition 2021 r49_e0597.rs =====
error[E0597]: `v` does not live long enough
 --> r49_e0597.rs:5:13
  |
4 |     let v = vec![1, 2, 3];
  |         - binding `v` declared here
5 |     let r = &v;
  |             ^^ borrowed value does not live long enough
6 |     let h = thread::spawn(move || r.len());
  |             ------------------------------ argument requires that `v` is borrowed for `'static`
7 |     println!("{}", h.join().unwrap());
8 | }
  | - `v` dropped here while still borrowed
  |
note: requirement that the value outlives `'static` introduced here
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:728:15

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
(exit 1)
```

- ★★★ **E0597 — `` `v` does not live long enough ``.** 표지 셋이 사슬을 이룬다 — 「borrowed value does not live long enough」(5행 `&v`) · 「**argument requires that `v` is borrowed for `'static`**」(6행 `spawn`) · 「`v` dropped here while still borrowed」(8행 `}`).
- ★★ `note:` 가 **요구의 출처**를 std 소스(`thread/mod.rs`)로 짚는다 — `spawn` 시그니처의 `'static` 이다.
- ★★★ **`move` 는 「무엇을 옮기나」를 바꿀 뿐 「그것이 무엇을 가리키나」는 못 바꾼다.** 옮긴 것이 참조면 수명 문제는 그대로다 — 34번 (4)의 E0373 과 **번호만 다른 같은 원인**이다.

### (3) ★★ `join` 은 `Result` 를 돌려준다 — 패닉은 `Err` 가 된다

**언제 쓰나** — 자식 스레드의 패닉을 main 이 알아야 할 때. `join().unwrap()` 을 습관처럼 쓰기 전에.

```text
===== 소스: r49_join.rs =====
use std::thread;

fn main() {
    let ok = thread::spawn(|| 40 + 2).join();
    println!("[1] join is_ok {}  value {:?}", ok.is_ok(), ok.as_ref().ok());

    let bad = thread::spawn(|| {
        let v: Vec<i32> = Vec::new();
        v[0]
    })
    .join();
    println!("[2] join is_err {}", bad.is_err());
    let p = bad.unwrap_err();
    println!("[3] payload String {}  &str {}  text {:?}", p.is::<String>(), p.is::<&str>(), p.downcast_ref::<String>());

    let lit = thread::spawn(|| -> i32 { panic!("fixed text") }).join();
    let p = lit.unwrap_err();
    println!("[4] payload String {}  &str {}  text {:?}", p.is::<String>(), p.is::<&str>(), p.downcast_ref::<&str>());
    println!("[5] main still running");
}
===== rustc --edition 2021 r49_join.rs =====
(exit 0)
===== ./r49_join 2>/dev/null =====
[1] join is_ok true  value Some(42)
[2] join is_err true
[3] payload String true  &str false  text Some("index out of bounds: the len is 0 but the index is 0")
[4] payload String false  &str true  text Some("fixed text")
[5] main still running
===== ./r49_join 2>&1 >/dev/null =====

thread '<unnamed>' (3307726) panicked at r49_join.rs:9:10:
index out of bounds: the len is 0 but the index is 0
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

thread '<unnamed>' (3307727) panicked at r49_join.rs:16:41:
fixed text
(exit 0)
```

- ★★★ **표준 출력과 표준 오류를 갈라 실었다**(규칙 18). 표준 출력에는 `[1]`\~`[5]` 가 **전부** 있다 — **자식이 패닉해도 main 은 계속 돈다**(`[5] main still running`, 종료 `0`). 표준 오류에는 **자식 스레드 둘의 패닉 메시지**가 `thread '<unnamed>'` 로 찍혔다(이름 없는 스레드).
- ★★ **`[1]` 정상 종료는 `Ok(값)`** — 클로저의 반환값 `42` 가 `join` 으로 돌아온다(`T: Send + 'static` 이 **반환값에도** 걸리는 이유).
- ★★★ **`[2]` 패닉은 `Err(패닉 값)`** — std: `join` 은 「스레드가 패닉했으면 `Err` 를 돌려준다」. 패닉이 **스레드 경계에서 멈추고 값으로 바뀐다.**
- ★★ **`[3]`·`[4]` 패닉 값의 타입이 둘이다** — 인덱스 범위 밖 패닉은 메시지를 **만들어 넣어서 `String`**, `panic!("fixed text")` 처럼 **리터럴 하나면 `&str`**. `downcast_ref` 는 **타입을 맞혀야** 꺼내진다 — 둘 다 시도하는 것이 관용이다.
- ★ `join().unwrap()` 은 자식의 패닉을 **main 의 패닉으로 옮긴다.** 되살릴 수 있는 실패면 `match` 로 받는다.

### (4) ★ `JoinHandle` 을 버리면 — detach, 그리고 main 이 먼저 끝나면

**언제 쓰나** — 「백그라운드로 돌려 두고 잊는」 스레드를 만들 때.

```text
===== 소스: r49_detach.rs =====
use std::env;
use std::thread;
use std::time::Duration;

fn main() {
    let wait_ms: u64 = env::args().nth(1).unwrap().parse().unwrap();
    let _ = thread::spawn(|| {
        thread::sleep(Duration::from_millis(50));
        println!("child line");
    });
    thread::sleep(Duration::from_millis(wait_ms));
    println!("main line");
}
===== rustc --edition 2021 r49_detach.rs =====
(exit 0)
```

```text
===== 소스: r49_detach.sh =====
# JoinHandle 을 버린 자식 — main 이 먼저 끝나는 판과 늦게 끝나는 판을 20번씩
rustc --edition 2021 -o r49_detach r49_detach.rs || exit 1
for w in 0 300; do
  child=0; mainl=0
  for i in $(seq 20); do
    out=$(./r49_detach "$w")
    case $out in *"child line"*) child=$((child+1)) ;; esac
    case $out in *"main line"*) mainl=$((mainl+1)) ;; esac
  done
  echo "main waits ${w}ms: runs with child line $child / 20, runs with main line $mainl / 20"
done
===== bash r49_detach.sh =====
main waits 0ms: runs with child line 0 / 20, runs with main line 20 / 20
main waits 300ms: runs with child line 20 / 20, runs with main line 20 / 20
(exit 0)
```

- ★★★ **`main waits 0ms` → `runs with child line 0 / 20`.** 자식은 50ms 잔 뒤 찍는데 main 은 바로 끝났다 — **20판 전부에서 자식 줄이 없다.** std 모듈 문서: 「**main 스레드가 끝나면 다른 스레드가 돌고 있어도 프로그램 전체가 끝난다**」.
- ★★ **`main waits 300ms` → `20 / 20`.** 자식에게 시간이 남으면 찍힌다. **달라진 것은 main 이 기다린 시간뿐**이다 — 즉 detach 한 스레드의 출력은 **시간 여유에 기댄다.**
- ★★★ **이 판 수는 「흔들릴 수 있는 칸」이다**(머리말 표). 50ms 대 300ms 는 여유가 커서 두 캡처가 같았지만, **순서를 정하는 것은 시계지 동기화가 아니다.** 반드시 찍혀야 하면 **`join` 하거나 `thread::scope` 를 쓴다.**
- ★ std `JoinHandle`: 「**버려질 때 스레드를 detach 한다** — 더 이상 그 스레드를 join 할 방법이 없다」. 소스의 `let _ = thread::spawn(…)` 이 그 모양이다(44번의 `let _` 은 **바로 버린다** — 여기서도 핸들이 그 문장 끝에 버려진다).
- ★ Go 는 `main` 이 반환하는 순간 고루틴을 기다리지 않는다([Go 28번 주제](../../../go/syntax/28-goroutines-go-statement-cost-and-termination/)) — 모양이 같다.

### (5) ★★★ `thread::scope` — 스코프 끝에서 자동 join

**언제 쓰나** — 지역 데이터를 **복사·`Arc` 없이** 여러 스레드가 나눠 보거나 고칠 때(1.63 부터 — std 표지 `1.63.0`).

```text
===== 소스: r49_scope.rs =====
use std::thread;

fn main() {
    let mut v = vec![1, 2, 3];
    let total: i32 = v.iter().sum();
    thread::scope(|s| {
        s.spawn(|| {
            thread::sleep(std::time::Duration::from_millis(100));
            v.push(total);
            eprintln!("[child] pushed");
        });
        eprintln!("[main] end of scope closure");
    });
    eprintln!("[main] after scope, v = {:?}", v);
}
===== rustc --edition 2021 r49_scope.rs =====
(exit 0)
===== ./r49_scope =====
[main] end of scope closure
[child] pushed
[main] after scope, v = [1, 2, 3, 6]
(exit 0)
```

- ★★★ **순서 로그가 약속을 보여 준다** — `[main] end of scope closure` 가 먼저 찍히고(스코프 **클로저**는 끝났다), 100ms 잔 자식의 `[child] pushed` 가 찍힌 **다음에야** `[main] after scope` 가 온다. **`thread::scope` 함수가 자식을 기다린 뒤에 돌아왔다.**
- ★★ **그래서 빌림이 된다** — 자식은 `v` 를 **가변으로 빌렸고**(`push`) `total` 을 공유로 빌렸다. `move` 도 `Arc` 도 없다. main 은 스코프 뒤에 `v` 를 그대로 읽는다(`[1, 2, 3, 6]`).
- ★★ **타입으로 건 약속이다** — 스코프 스레드의 클로저는 `'static` 이 아니라 **`'scope`** 만 요구한다. 스코프가 끝나기 전에 join 되는 것이 보장되므로, 스코프보다 오래 사는 빌림(스코프 밖 지역 변수)이면 된다. **(1)의 10\~13행은 그래서 E0373 이 아니라 평범한 빌림 에러(E0499·E0502)로 갈렸다.**

**자식이 패닉하면.**

```text
===== 소스: r49_scope_panic.rs =====
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let r = std::panic::catch_unwind(|| {
        thread::scope(|s| {
            s.spawn(|| v[10]);
        });
    });
    eprintln!("[main] scope returned is_err {}", r.is_err());
}
===== rustc --edition 2021 r49_scope_panic.rs =====
(exit 0)
===== ./r49_scope_panic =====

thread '<unnamed>' (3308568) panicked at r49_scope_panic.rs:7:25:
index out of bounds: the len is 3 but the index is 10
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace

thread 'main' (3308567) panicked at r49_scope_panic.rs:6:9:
a scoped thread panicked
[main] scope returned is_err true
(exit 0)
```

- ★★★ **표준 오류에 패닉이 둘** — 자식의 `index out of bounds` 다음에 **`thread 'main'` 의 `a scoped thread panicked`**. std `scope` §Panics: 「**자동으로 join 된 스레드 중 하나라도 패닉했으면 이 함수가 패닉한다**」. (3)의 `spawn` 은 패닉을 `Err` 로 **삼켜 주는데**, 스코프는 **main 으로 옮긴다.**
- ★ 이 탐침은 그 패닉을 `catch_unwind` 로 받아 `is_err true` 를 찍었다. 받고 싶지 않으면 스코프 안에서 **`s.spawn(…).join()`** 으로 직접 join 해 `Result` 를 받는다(std 가 권하는 길).

### (6) ★ 스레드 id 와 이름 — 「같은가」만 본다

```text
===== 소스: r49_ids.rs =====
use std::thread;

fn main() {
    let main_id = thread::current().id();
    let h = thread::spawn(|| (thread::current().id(), thread::current().name().map(String::from)));
    let handle_id = h.thread().id();
    let (child_id, child_name) = h.join().unwrap();
    println!("[1] main id == child id        {}", main_id == child_id);
    println!("[2] handle id == child id      {}", handle_id == child_id);
    println!("[3] main name                  {:?}", thread::current().name());
    println!("[4] unnamed child name         {:?}", child_name);

    let named = thread::Builder::new()
        .name("worker-1".into())
        .spawn(|| thread::current().name().map(String::from))
        .unwrap();
    println!("[5] Builder name               {:?}", named.join().unwrap());
}
===== rustc --edition 2021 r49_ids.rs =====
(exit 0)
===== ./r49_ids =====
[1] main id == child id        false
[2] handle id == child id      true
[3] main name                  Some("main")
[4] unnamed child name         None
[5] Builder name               Some("worker-1")
(exit 0)
```

- ★★ **`[1]` main 과 자식의 id 는 다르다 · `[2]` 핸들이 가리키는 id 와 자식이 스스로 본 id 는 같다.** `ThreadId` 는 **실행 중인 스레드마다 고유한 식별자**(std). 숫자 자체는 판마다 달라질 수 있어 **싣지 않았다.**
- ★★ **`[3]` main 의 이름은 `Some("main")` · `[4]` 그냥 `spawn` 한 스레드는 `None` · `[5]` `Builder::name` 을 주면 `Some("worker-1")`.** (3)의 패닉 메시지에 `thread '<unnamed>'` 가 찍힌 까닭이 `[4]` 다 — 이름을 주면 패닉 메시지가 **그 이름을 찍는다**(이 편은 그 판을 던지지 않았다).
- ★ 머리말의 「흔들리는 칸」이 가리키는 숫자는 **패닉 첫 줄 괄호 안의 OS 스레드 id** 다 — `ThreadId` 와 **다른 것**이다.

## 문법 — 형태와 규칙

```text
   use std::thread;

   let h = thread::spawn(move || expr);   // F: FnOnce() -> T + Send + 'static,  T: Send + 'static
   let r: Result<T, _> = h.join();        // 패닉이면 Err(Box<dyn Any + Send>)
   drop(h);  /  let _ = thread::spawn(…); // JoinHandle 을 버리면 detach

   thread::scope(|s| {                    // 1.63
       s.spawn(|| uses(&local));          // 'scope 만 요구 — 지역 빌림 가능
   });                                    // 여기서 전부 join. 하나라도 패닉했으면 여기서 패닉

   thread::Builder::new().name("worker-1".into()).spawn(f)   // io::Result<JoinHandle<T>>
```

- ★★★ **`spawn` 은 `'static` 을 요구한다 — 스레드가 자기를 만든 함수보다 오래 살 수 있어서다**(std 「`'static` 제약」 절).
- ★★★ **`move` 는 잡은 것을 클로저 안으로 옮긴다 — 옮긴 것이 참조면 수명은 그대로다**((1)의 9행 · (2)).
- ★★ **2021 캡처는 자리(place)를 잡고, 공유 참조 역참조에서 자른다** — `&'static str` 변수는 `move` 없이 된다((1-1)).
- ★★ **`thread::scope` 는 `'static` 을 `'scope` 로 낮춘다 — 대가는 「스코프 끝에서 반드시 기다린다」다**((5)).
- ★ **`join` 은 `Result`, `scope` 는 패닉을 옮긴다**((3)·(5)).

## 어디서 틀리나

### 1. ★★★ 「스레드에 넘길 때는 `move` 만 붙이면 된다」

(1)의 9행 · (2) — **참조를 옮기면 E0597.** `move` 는 수명을 늘려 주지 않는다. 가리키는 값을 옮기거나(`move` + 소유 값), 복제하거나(`Arc`), 기다려라(`scope`).

### 2. ★★★ 「`Arc` 로 감쌌으니 `move` 는 필요 없다」

(1)의 5행 — **`Arc` 도 빌림으로 잡히면 E0373.** `Arc::clone` 을 **먼저 하고 그 복제본을 `move`** 해야 한다(4행).

### 3. ★★ 「`'static` 문자열도 지역 변수에 담았으면 `move` 가 필요하다」

(1-1) — **2018 에서만 참.** 2021 부터는 공유 참조 역참조에서 캡처가 잘려 `move` 없이 통과한다. **에디션을 모르고 「이건 원래 안 된다」고 외우면 틀린다.**

### 4. ★★ 「자식이 패닉하면 프로그램이 죽는다」

(3) — **`spawn` 한 스레드의 패닉은 `join` 의 `Err` 가 되고 main 은 계속 돈다.** 죽는 것은 main 이 `unwrap()` 할 때다. 반대로 **`thread::scope` 는 main 에서 패닉한다**((5)).

### 5. ★★ 「스레드를 만들어 두면 알아서 끝까지 돈다」

(4) — **main 이 끝나면 프로그램째 끝난다**(`0 / 20`). detach 한 스레드의 일은 **보장되지 않는다.**

### 6. ★ 「`thread::scope` 는 `move` 를 대신해 주는 문법 설탕이다」

(1)의 12·13행 — 빌림을 **허용할 뿐 검사를 끄지 않는다.** 두 스레드가 같은 `Vec` 을 가변으로 빌리면 E0499 다. 여럿이 고치려면 [52번 주제](../52-mutex-rwlock-arc-and-poisoning/)의 `Mutex` 가 필요하다.

### 7. ★ 「스레드는 무거우니 쓰지 마라 / 가벼우니 막 써라」

**이 문서는 재지 않았다.** 이 편이 근거로 보인 것은 **수명·패닉·detach** 세 가지 규칙뿐이다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `spawn` 이 `F: Send + 'static`, `T: Send + 'static` 을 요구한다 | ★ **std 의 시그니처** — 컴파일러가 강제 | (1) E0373 · (2) E0597 의 `note:` |
| 2021 캡처가 공유 참조 역참조에서 잘린다 | ★ **언어 · 에디션**(Reference — Capture precision) | (1-1) |
| `scope` 가 끝나기 전에 전부 join 한다 · 패닉하면 `scope` 가 패닉 | ★ **std 의 계약**(`scope` 문서 · §Panics) | (5) |
| `join` 이 패닉을 `Err` 로 돌려준다 | ★ **std 의 계약**(`JoinHandle::join`) | (3) |
| 패닉 값이 `String` 인가 `&str` 인가 | ★ **std 의 패닉 기계의 관찰** — 포맷된 메시지냐 리터럴이냐 | (3)의 `[3]`·`[4]` |
| main 이 끝나면 프로그램 전체가 끝난다 | ★ **std 의 문서화된 동작**(모듈 문서) | (4) |
| detach 한 자식이 **몇 판에서** 찍히나 | ★ **관찰** — 시간 여유와 OS 스케줄링 | (4) — 흔들릴 수 있는 칸 |
| 스레드 이름 `main` · 무명 스레드의 `<unnamed>` 표기 | ★ **std 구현** | (6) · (3) |
| 패닉 첫 줄의 OS 스레드 id | ★ **실행마다 다르다** — 정규화 대상 | (3)·(5) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 스레드가 값을 **혼자** 쓴다 | ★ **`move` + 소유 값** | (1)의 2행 |
| main 과 스레드가 **같은 읽기 전용 값**을 쓴다 | **`Arc` 복제 + `move`** · 또는 **`thread::scope`** | (1)의 4행 · 10행 |
| 지역 데이터를 여러 스레드가 **나눠 처리**하고 결과를 모은다 | ★ **`thread::scope`** — `Arc` 가 필요 없다 | (5) |
| 스레드가 **함수보다 오래** 산다(서버 루프·백그라운드) | **`spawn` + 핸들을 어딘가 보관**해 끝날 때 join | (4) |
| 자식의 실패를 main 이 **처리**해야 한다 | **`join()` 을 `match`** 로 받는다 | (3) |
| 여럿이 **같은 값을 고친다** | ★ `move` 로는 안 된다 — [52번 주제](../52-mutex-rwlock-arc-and-poisoning/) · 소유권을 넘기면 [51번 주제](../51-mpsc-channels-and-sender-drop/) | (1)의 12행 |

## 핵심 문장

- ★★★ **`spawn` 이 `'static` 을 요구하는 것은 스레드가 자기를 만든 함수보다 오래 살 수 있기 때문이고, `move` 는 빌림을 소유로 바꿔 그 요구를 맞춘다.**
- ★★★ **`move` 는 참조를 옮길 수는 있어도 참조가 가리키는 값의 수명은 못 늘린다 — 그래서 `move` 한 `&v` 는 E0597 이다.**
- ★★★ **`thread::scope` 는 「끝나기 전에 반드시 join」을 약속하고 그 대가로 빌림을 허용한다 — 빌림 규칙 자체는 그대로 검사된다.**
- ★★ **`join` 은 자식의 패닉을 `Err` 로 받게 해 주지만, 핸들을 버리면 기다릴 방법이 없고 main 이 끝나면 프로그램째 끝난다.**
- ★ **2021 캡처는 공유 참조를 역참조한 자리에서 잘리므로 `&'static str` 변수는 `move` 없이도 넘어간다.**

## 관련 자료

- [**34번 주제**](../34-closures-fn-fnmut-fnonce-and-move/) — E0373 전문과 `move` 의 정의 · 2021 정밀 포착. **그쪽은 클로저가 무엇을 잡나, 여기는 스레드가 그것에 무엇을 요구하나.**
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Rc` 의 E0277 과 `Arc` 의 strong count. (1)의 4행이 그 판이다.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — `let _ =` 는 그 문장 끝에 버린다. (4)의 핸들이 그렇게 버려진다.
- [**50번 주제**](../50-send-sync-in-compiler-errors/) — `spawn` 의 **다른 절반**인 `Send` 경계. 이 편은 `'static` 쪽만 다뤘다.
- [**51번 주제**](../51-mpsc-channels-and-sender-drop/) · [**52번 주제**](../52-mutex-rwlock-arc-and-poisoning/) · [**53번 주제**](../53-atomics-oncelock-and-lazylock/) — 스레드끼리 값을 넘기고 나누는 세 방법.
- [`process-thread/`](../../../../process-thread/) — 프로세스·스레드·TCB·경쟁 조건의 **원리는 거기**, 여기는 Rust 의 `spawn`/`scope` 가 수명으로 무엇을 요구하나로 좁힌다.
- [Go 28번 주제](../../../go/syntax/28-goroutines-go-statement-cost-and-termination/) — `main` 이 반환하면 고루틴을 기다리지 않는다(같은 모양).
- 목록의 **47번 주제**(에디션 2021 대 2024) — (1-1)의 에디션 차이는 2018→2021 쪽이다.

## 용어 풀이

- **`thread::spawn`** — 새 OS 스레드를 만들어 클로저를 돌리고 `JoinHandle` 을 돌려준다.
- **`JoinHandle<T>`** — 그 스레드를 기다릴(join) 권리. `join()` 이 `Result<T, _>` 를 준다. 버리면 detach.
- **join** — 스레드가 끝날 때까지 기다리고 결과를 받는 것.
- **detach** — 기다릴 권리를 버린 것. 스레드는 계속 돌지만 main 이 끝나면 함께 끝난다.
- **`'static` 경계** — 프로그램 끝까지 유효해도 되는 값이라는 약속. 빌림을 품은 값은 대개 아니다.
- **`thread::scope` / scoped thread** — 스코프 끝에서 자동 join 되는 스레드. `'scope` 만 요구해 지역 빌림을 허용한다.
- **패닉 값(payload)** — 패닉이 실어 나르는 값. `join` 의 `Err` 안에 `Box<dyn Any + Send>` 로 온다.
- **`ThreadId`** — 실행 중인 스레드마다 고유한 식별자. OS 스레드 id 와 다르다.
- **캡처 자리(place)** — 클로저가 잡는 대상. 2021 부터는 변수 전체가 아니라 쓴 필드·역참조 자리다.

## 더 들어가면

- `thread::Builder::stack_size` · `available_parallelism` — 이 문서는 던지지 않았다.
- `JoinHandle::is_finished`(1.61) — join 하지 않고 끝났는지 묻는다. 이 문서는 던지지 않았다.
- 스레드 이름을 준 스레드가 패닉하면 메시지가 그 이름을 찍는다 — (6)에서 말했지만 **던지지 않았다.**
- 스레드마다 따로 가지는 값(`thread_local!`)은 이 목록에 없다.
