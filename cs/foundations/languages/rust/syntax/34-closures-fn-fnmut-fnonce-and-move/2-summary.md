# rust/syntax/34 — 클로저 세 종류 `Fn`/`FnMut`/`FnOnce`와 `move` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Closure types](https://doc.rust-lang.org/reference/types/closure.html)(capture modes · call traits · edition 2018 differences) ·
> [Edition Guide — Disjoint capture in closures (2021)](https://doc.rust-lang.org/edition-guide/rust-2021/disjoint-capture-in-closures.html) ·
> [Reference — Type layout(closure)](https://doc.rust-lang.org/reference/type-layout.html#closure-layout).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **블록마다 배너에 적은 `--edition`** 으로 돌려 받은 것이다(기본 2021, 에디션 격자는 2015·2018·2021·2024). 파이썬 대비는 `Python 3.12.3`.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — 클로저·세 트레이트는 1.0 부터 · ★ **정밀 포착(disjoint capture)은 2021 에디션(1.56.0)** 부터. (0)의 블록이 근거다.
> ★ **에디션이 넷째 축**이다 — 결론 하나((6))가 **언어 판**에 매여 있다. **세 트레이트 판정 자체((1)·(2))는 에디션과 무관한 언어 규칙**이다.
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
===== clang++ --version | head -1 =====
Ubuntu clang version 18.1.3 (1ubuntu1)
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **에디션이 가른다** | **(6)의 격자** — 같은 소스가 2018 에서 E0506/E0382, 2021 에서 통과 · 클로저 크기 32 → 24 | **흔들리는 것이 아니라 에디션이 정한다** — 같은 판·같은 에디션이면 고정이다 |
| 안 흔들린다 | 3×3 격자 칸마다의 **진단 코드**와 `rejected cells 3 / 9` | 같은 판에서 고정이다 |
| 안 흔들린다 | `size_of_val` 로 잰 **클로저 크기** | 같은 판·같은 타깃에서 고정이다. ★ **언어 보장은 아니다**(Reference 「클로저는 레이아웃 보장이 없다」) |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼고 **하나도 걸리지 않았다**(제출 전 재대조).

## 한눈에 — 쉽게 말하면

**클로저는 「환경에서 가져온 것을 넣어 둔 익명 구조체 + 부르는 법」이다.
가져온 것을 몸통이 어떻게 다루느냐 — 읽기만 / 고치기 / 옮겨 버리기 — 가 세 트레이트 중 어디까지 되는지를 정한다.
`move` 는 「어떻게 가져오나」를 바꿀 뿐 「무엇이 되나」를 바꾸지 않는다.**

| 비유 | 실체 |
|---|---|
| 「**빌린 책을 읽기만 하는 사람** — 여럿이 동시에 써도 된다」 | ★★ **`Fn`** — `&self` 로 불린다. 몇 번이든, 동시에도((1)) |
| 「**빌린 공책에 적는 사람** — 한 번에 한 사람」 | ★★ **`FnMut`** — `&mut self` 로 불린다. `let mut` 이 필요하다((1)·(5)) |
| 「**받은 선물을 남에게 줘 버리는 사람** — 한 번뿐」 | ★★ **`FnOnce`** — `self` 로 불린다. 두 번 부르면 E0382((5)) |
| 「**택배로 받아 두기**(빌리지 않고 가져오기)」 | ★★★ **`move`** — **포착 방식**만 값으로 바꾼다. 읽기만 하면 **여전히 `Fn`**((3)) |
| 「**서랍 하나만 들고 가기**(책상째가 아니라)」 | ★★ **정밀 포착(2021~)** — `p.name` 만 잡는다. 2018 은 `p` 전체((6)) |

- ★★★ **판정은 한 줄이다 — 「옮겨 버리면 `FnOnce` 만, 고치면 `FnMut` 까지, 읽기만 하면 `Fn` 까지」.** 위 트레이트일수록 아래를 다 구현한다(`Fn` ⊂ `FnMut` ⊂ `FnOnce` 의 자리에 다 들어간다).
  **컴파일러가 3×3 격자로 판정해 준다**((1)) — 거절 칸 **3 / 9**.
- ★★ **`move` 는 트레이트를 안 바꾼다** — Reference 가 직접 적는다 「**클로저가 구현하는 트레이트는 잡은 값으로 무엇을 하느냐로 정해지지, 어떻게 잡느냐로 정해지지 않는다**」((3)).

```text
   3×3 격자 — (1)의 블록 그대로 (✔ 받는다 / ✘ 거절)

                     need(impl Fn())   need(impl FnMut())   need(impl FnOnce())
                     ───────────────   ─────────────────    ──────────────────
   읽기만  s.len()        ✔                  ✔                    ✔
   고치기  s.push(1)      ✘ E0596 / E0525    ✔                    ✔
   옮기기  drop(s)        ✘ E0507 / E0525    ✘ E0507 / E0525      ✔

   ★ 왼쪽 코드 = 부르는 자리에 클로저를 바로 쓸 때 · 오른쪽 코드 = 변수에 묶었다가 넘길 때
     칸의 ✔/✘ 는 두 벌이 같다 — 번호만 다르다(2)
```

> **포착(capture)** — 클로저가 몸통에서 쓴 바깥 변수를 **자기 안에 넣어 두는 것.** 방식은 넷 — 불변 빌림 · 고유 불변 빌림 · 가변 빌림 · 이동(Reference).\
> 예: `|| s.len()` 은 `s` 를 불변 빌림으로, `|| s.push(1)` 은 가변 빌림으로, `|| drop(s)` 는 이동으로 잡는다.

> **`move` 클로저** — **모든 포착을 이동(또는 `Copy` 면 복사)** 으로 바꾸는 표시. 트레이트 판정과는 **별개**다.\
> 예: `move || s.len()` 은 `s` 를 **옮겨 넣지만** 몸통은 읽기만 하므로 `Fn` 이다.

## 이 주제가 답하려는 질문

1. ★★★ **이 클로저는 세 트레이트 중 무엇이 되나** — 몸통이 잡은 것을 읽나·고치나·옮기나로 판정한다((1)·(2)).
2. ★★ **`move` 는 무엇을 바꾸고 무엇을 안 바꾸나** — 그리고 **`move` 가 꼭 필요한 자리**는 어디인가(E0373)((3)·(4)).
3. ★ **클로저는 무엇을 얼마나 잡나** — 크기와, 2021 의 **정밀 포착**이 에디션에 따라 가르는 것((5)·(6)).

★ **선행** — [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 **「불변 빌림 여럿 / 가변 빌림 하나」** 가 그대로 세 트레이트가 된다 — `Fn` 은 불변 빌림처럼 여럿이 불러도 되고, `FnMut` 은 가변 빌림처럼 한 번에 하나다.
[**08번 주제**](../08-ownership-and-move/)의 이동이 `FnOnce` 다.
★ [**32번 주제**](../32-impl-trait-argument-return-position-and-2024-capture/) (4)가 **「환경을 안 잡은 클로저는 함수 포인터로 모인다」** 를 봤다 — 그 강제와 크기 격자는 [**35번 주제**](../35-function-pointers-and-returning-closures/)가 넓힌다. 여기는 **잡는 쪽**이다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 3×3 격자다

★★★ **본체 창 — ① 「몸통 셋 × 받는 함수 셋」을 컴파일러가 칸마다 판정하는 격자.** 스크립트가 마지막 줄에 **`rejected cells N / 9`** 를 찍는다.

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **3×3 격자**(두 벌 — 바로 쓰기 / 변수에 묶기) | 칸마다 **받나 거절하나**, 거절이면 **어느 번호**인가((1)·(2)) | ★ **본체** |
| ② **E0525·E0596·E0507 전문** | 거절 이유를 **컴파일러가 무엇이라 말하나**((2)) | 쓴다 |
| ③ **`size_of_val(&클로저)`** | 무엇을 **어떻게** 잡았나 — 빌림 8 · 값 그대로((5)) | 쓴다 |
| ④ ★★ **에디션 격자 2015 · 2018 · 2021 · 2024** | 정밀 포착이 **어느 판에서** 결과를 바꾸나((6)) | 쓴다 — 넷째 축 |
| ⑤ **파이썬 대비** | 루프에서 모은 함수가 **어느 값을 보나**((7)) | 대비로 쓴다 |
| 실행 시간 | 클로저 호출 비용 | ★ **부적용 — 재지 않는다** |
| 단형화 벌 수 | `impl Fn()` 인자가 클로저마다 찍히는 것 | ★ **부적용 — 31번이 정본**(`impl Trait` 인자도 이름 없는 제네릭 — 32번 (1)) |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「이 클로저는 `s` 를 **빌렸나 옮겼나**」를 타입 검사기에 물으면 **에러가 날 때만** 답한다(E0382 의 「value moved into closure here」).
같은 질문을 ③ **`size_of_val`** 로 물으면 **통과한 판에서도** 답한다 — `String` 을 빌리면 **8**, 옮기면 **24**. ★ **이 창이 못 보는 것** — 크기가 같은 두 방식(가변 빌림과 불변 빌림은 둘 다 8)은 **못 가른다.**

**버전.**

```text
===== awk '/^Version 1\./{v=$2} /The 2021 Edition is now stable/{print v " | " $0}' "$(rustc --print sysroot)/share/doc/rust/html/releases.md" =====
1.56.0 | - [The 2021 Edition is now stable.][rust#88100]
(exit 0)
```

### (1) ★★★ 3×3 격자 — 컴파일러가 판정한다

**언제 쓰나** — 콜백을 받는 함수의 경계를 **`Fn`·`FnMut`·`FnOnce` 중 무엇으로 적을지** 정할 때. 그리고 **넘긴 클로저가 왜 거절되는지** 읽을 때.

```bash
# r34_grid.sh
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
```

```text
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

- ★★★ **거절 칸 3 / 9 — 두 벌 모두.** 받는 칸은 **읽기 × 셋 · 고치기 × `FnMut`·`FnOnce` · 옮기기 × `FnOnce`** 이다.
  **계단 모양**이다 — **`FnOnce` 열은 전부 받고, `Fn` 열은 읽기만 받는다.** Reference 가 적는 대로 **모든 클로저는 `FnOnce`** 이고,
  **옮기지 않으면 `FnMut`** 까지, **고치지도 옮기지도 않으면 `Fn`** 까지 구현한다.
- ★★ **칸의 ✔/✘ 는 두 벌이 같고 번호만 다르다** — 바로 쓰면 **E0596·E0507**, 변수에 묶으면 **E0525**((2)).
- ★ **`FnOnce` 로 받는 쪽이 가장 너그럽고 가장 적게 약속한다** — 받은 함수는 **한 번만** 부를 수 있다. 여러 번 부를 거면 `FnMut`, 동시에 부를 거면 `Fn` 을 **요구해야** 한다.

### (2) ★★ 같은 칸, 다른 번호 — 추론이 어느 쪽에서 오나

**언제 쓰나** — E0525 와 E0596/E0507 중 **무엇을 받았는지로 고칠 자리**를 찾을 때.

**변수에 묶었다가 넘기면 — E0525.**

```rust
// r34_let_mut.rs
// 변수에 묶은 클로저를 impl Fn 자리에
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    let c = || s.push(1);
    need_fn(c);
}
```

```text
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

- ★★ **E0525 — expected a closure that implements the `Fn` trait, but this closure only implements `FnMut`.**
  `let c = || s.push(1);` 에서 클로저의 종류가 **몸통만 보고 먼저** 정해졌다(`FnMut`). 그다음 `need_fn(c)` 가 `Fn` 을 요구해 **트레이트가 안 맞는다.**
  진단이 **이유(「mutates the variable `s` here」)와 요구가 온 자리**를 둘 다 짚는다.

```rust
// r34_let_give.rs
// 옮겨 버리는 클로저를 impl FnMut 자리에
fn need_fnmut(mut f: impl FnMut()) {
    f();
}

fn main() {
    let s = vec![0u8];
    let c = || drop(s);
    need_fnmut(c);
}
```

```text
===== rustc --edition 2021 r34_let_give.rs =====
error[E0525]: expected a closure that implements the `FnMut` trait, but this closure only implements `FnOnce`
 --> r34_let_give.rs:8:13
  |
8 |     let c = || drop(s);
  |             ^^      - closure is `FnOnce` because it moves the variable `s` out of its environment
  |             |
  |             this closure implements `FnOnce`, not `FnMut`
9 |     need_fnmut(c);
  |     ---------- - the requirement to implement `FnMut` derives from here
  |     |
  |     required by a bound introduced by this call
  |
note: required by a bound in `need_fnmut`
 --> r34_let_give.rs:2:27
  |
2 | fn need_fnmut(mut f: impl FnMut()) {
  |                           ^^^^^^^ required by this bound in `need_fnmut`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0525`.
(exit 1)
```

- ★ 옮겨 버리는 쪽도 같은 번호다 — 「**closure is `FnOnce` because it moves the variable `s` out of its environment**」.

**부르는 자리에 바로 쓰면 — E0596.**

```rust
// r34_inline_mut.rs
// 같은 클로저를 부르는 자리에 바로 쓰면
fn need_fn(f: impl Fn()) {
    f();
}

fn main() {
    let mut s = vec![0u8];
    need_fn(|| s.push(1));
}
```

```text
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

- ★★ **E0596 — cannot borrow `s` as mutable, as it is a captured variable in a `Fn` closure.** 이번에는 클로저가 **`Fn` 이라고 이미 정해진 채**(인자 자리의 기대에서 추론) 몸통을 검사해,
  **몸통의 `s.push(1)` 이 틀린 것**으로 나왔다. 같은 사실을 **반대편에서** 본 것이다.
- ★★ **`help:` 가 가리키는 자리도 다르다** — 「**change this to accept `FnMut` instead of `Fn`**」가 **`need_fn` 의 시그니처**를 짚는다. E0525 는 **클로저 몸통**을 짚었다.
  **고칠 곳은 둘 중 하나다** — 받는 쪽 경계를 넓히거나, 클로저가 덜 하게 만들거나.

### (3) ★★★ `move` 는 트레이트를 안 바꾼다

**언제 쓰나** — 「`move` 를 붙였으니 `FnOnce` 겠지」라고 생각할 때.

```rust
// r34_move_fn.rs
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
```

```text
===== rustc --edition 2021 r34_move_fn.rs =====
(exit 0)
===== ./r34_move_fn =====
6
3
(exit 0)
```

- ★★★ **통과 — `6` · `3`.** `move || s.len()` 은 `s` 를 **옮겨 넣었지만** 몸통은 **읽기만** 한다. 그래서 **`Fn`** 이다 — `&impl Fn` 으로 받아 **두 번** 부르고, 밖에서 **또** 불렀다.
  Reference 의 Note 가 그대로다 — 「**`move` 클로저도 `Fn`·`FnMut` 을 구현할 수 있다. 트레이트는 무엇을 하느냐로 정해지지 어떻게 잡느냐로 정해지지 않는다.**」
- ★★ **`move` 가 바꾸는 것은 원래 변수 쪽이다.**

```rust
// r34_move_after.rs
// move 로 잡은 뒤 원래 변수를 쓰면
fn main() {
    let s = String::from("abc");
    let c = move || s.len();
    println!("{}", c());
    println!("{}", s);
}
```

```text
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

- ★★ **E0382 — borrow of moved value: `s`.** `c()` 는 문제없이 불리지만 **`s` 는 이제 클로저 안에 있다.** `move` 는 **「클로저가 몇 번 불리나」가 아니라 「바깥이 그 값을 계속 쓸 수 있나」** 를 바꾼다.
- ★ `help:` 는 「**consider cloning the value before moving it into the closure**」 — 복제해 둔 쪽을 넣으라는 처방이다(`value` 라는 새 이름까지 제안한다).

### (4) ★★ `move` 가 꼭 필요한 자리 — E0373

**언제 쓰나** — 클로저가 **지금 함수보다 오래 살 때** — 스레드에 넘기거나(스레드 쪽 정본은 목록의 **49번 주제**), 함수 밖으로 돌려줄 때(돌려주기는 [**35번 주제**](../35-function-pointers-and-returning-closures/)).

```rust
// r34_thread.rs
// 스레드에 클로저를 넘긴다
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let h = thread::spawn(|| v.len());
    println!("{}", h.join().unwrap());
}
```

```text
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

- ★★★ **E0373 — closure may outlive the current function, but it borrows `v`, which is owned by the current function.**
  `v.len()` 은 읽기뿐이라 **빌림으로 잡혔는데**, `thread::spawn` 이 「**function requires argument type to outlive `'static`**」(`note:`)다 — 새 스레드가 `main` 보다 오래 살 수 있다.
- ★ `help:` — 「**to force the closure to take ownership of `v` … use the `move` keyword**」.

**`help:` 대로 `move` 를 붙이면.**

```rust
// r34_thread_move.rs
// help: 가 권한 대로 move 를 붙이면
use std::thread;

fn main() {
    let v = vec![1, 2, 3];
    let h = thread::spawn(move || v.len());
    println!("{}", h.join().unwrap());
}
```

```text
===== rustc --edition 2021 r34_thread_move.rs =====
(exit 0)
===== ./r34_thread_move =====
3
(exit 0)
```

- ★ **통과 — `3`.** 이번 `help:` 는 **그대로 맞았다.** 그리고 이 클로저도 몸통은 읽기뿐이라 **여전히 `Fn`** 이다(`spawn` 이 요구하는 것은 `FnOnce` 라 어느 쪽이든 받는다).

### (5) 부르는 쪽의 규칙과 클로저의 크기

**`FnOnce` 를 두 번 부르면.**

```rust
// r34_once_twice.rs
// FnOnce 인 클로저를 두 번 부르면
fn main() {
    let s = String::from("abc");
    let c = move || s;
    let a = c();
    let b = c();
    println!("{} {}", a, b);
}
```

```text
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

- ★★ **E0382 — use of moved value: `c`.** `move || s` 는 `s` 를 **돌려주면서 밖으로 옮긴다** — 그래서 `FnOnce` 이고, **부르는 것 자체가 `c` 를 소비한다.**
  두 `note:` 가 이유를 적는다 — 「**closure cannot be invoked more than once because it moves the variable `s` out of its environment**」.

**고치는 클로저를 `mut` 없이 묶으면.**

```rust
// r34_mut_binding.rs
// 고치는 클로저를 mut 없이 묶고 부르면
fn main() {
    let mut n = 0;
    let c = || n += 1;
    c();
    println!("{}", n);
}
```

```text
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

- ★ **E0596 — cannot borrow `c` as mutable.** `FnMut` 은 **`&mut self`** 로 불리므로 **클로저 변수가 `mut`** 이어야 한다(`help:` 가 `let mut c` 를 권한다).

**클로저 하나는 몇 바이트인가.**

```rust
// r34_size.rs
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
```

```text
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

- ★★ **안 잡으면 0**, **빌림 하나면 8**(참조 하나), **빌림 둘이면 16**, **`move` 로 `i32` 를 잡으면 4**(값 그대로), **`String` 을 빌리면 8 · 옮기면 24.**
  **클로저는 잡은 것의 구조체**다 — 크기가 곧 **무엇을 어떻게 잡았나**의 증거다.
- ★ `by_ref` 는 `n + 1` 로 **읽기만** 하므로 `i32`(Copy)도 **빌림으로** 잡혔다(8) — Reference 「Copy 값이 클로저로 옮겨지는 자리도 불변 빌림으로 잡는다」. **`move` 를 붙여야 4 가 된다.**
- ★★ **이 수치는 언어 보장이 아니다** — Reference 가 「**클로저는 레이아웃 보장이 없다**」고 적는다(§구현 세부).

### (6) ★★ 2021 의 정밀 포착 — 에디션 격자

**언제 쓰나** — 구조체의 **필드 하나**만 쓰는 클로저를 두고 **다른 필드**를 건드릴 때. 2018 크레이트를 2021 로 올릴 때.

```rust
// r34_dj_borrow.rs
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
```

```rust
// r34_dj_size.rs
// move 클로저가 p.name 만 쓴다 — 클로저는 몇 바이트인가
struct P {
    name: String,
    age: u32,
}

fn main() {
    let p = P { name: String::from("kim"), age: 30 };
    let c = move || p.name.len();
    println!("P {}, closure {}", std::mem::size_of::<P>(), std::mem::size_of_val(&c));
    println!("{}", c());
}
```

```rust
// r34_dj_after.rs
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
```

**세 소스를 에디션 넷으로.**

```bash
# r34_ed_grid.sh
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
```

```text
===== bash r34_ed_grid.sh =====
source           | 2015                   | 2018                   | 2021                   | 2024
r34_dj_borrow    | E0506                  | E0506                  | kim/31                 | kim/31
r34_dj_size      | P 32, closure 32/3     | P 32, closure 32/3     | P 32, closure 24/3     | P 32, closure 24/3
r34_dj_after     | E0382                  | E0382                  | 3 30                   | 3 30
sources whose cell changes between 2018 and 2021: 3 / 3
(exit 0)
```

- ★★★ **바뀐 소스 3 / 3 — 전부 2018 과 2021 사이에서 갈렸다.** 2015 = 2018, 2021 = 2024 다.
  - `r34_dj_borrow` — 2018 **E0506**(`p.age` 가 빌려져 있다) → 2021 **통과**(`kim` / `31`).
  - `r34_dj_size` — 클로저가 **32 → 24**. 2018 은 `p` **전체**(`P` 32바이트)를, 2021 은 **`p.name` 만**(`String` 24바이트) 옮겨 넣었다.
  - `r34_dj_after` — 2018 **E0382**(`p` 가 통째로 옮겨졌다) → 2021 **통과**(`3 30` — `p.age` 가 남아 있다).
- ★★ **크기가 원인을 말한다** — 셋 다 **한 가지 변화**의 다른 얼굴이다. Reference 의 2018 절 「**클로저는 변수를 통째로 잡는다**」가 2021 에서 「**쓴 자리(place)만 잡는다**」로 바뀌었다.

**2018 의 에러 전문.**

```text
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

- ★ E0506 이 「**`p.age` is borrowed here**」라고 **클로저 전체**를 짚는다 — 클로저가 `p.name` 만 썼는데도 **`p` 를 빌렸기** 때문이다.
- ★ E0382 의 `note:` 는 「**if `P` implemented `Clone`, you could clone the value**」 — **2021 로 올리면 필요 없는 처방**이다. 이 판의 2018 진단은 에디션 차이를 말해 주지 않는다.
- ★ **옮길 때의 도구** — Edition Guide 에 따르면 2021 이전용 린트 `rust_2021_incompatible_closure_captures` 가 드롭 순서·트레이트가 바뀔 자리에 **`let _ = &p;`** 를 넣어 **통째 포착을 강제**한다(`cargo fix --edition` — 목록의 **47번 주제**. 이 문서는 돌리지 않았다).

### (7) 루프에서 모은 클로저 — Rust 와 파이썬, Go

**언제 쓰나** — 루프 변수를 잡는 콜백을 여러 개 만들 때.

```rust
// r34_loop.rs
// 루프에서 클로저를 모은다 — 각 클로저는 어느 i 를 보나
fn main() {
    let mut fs: Vec<Box<dyn Fn() -> i32>> = Vec::new();
    for i in 0..3 {
        fs.push(Box::new(move || i));
    }
    let out: Vec<i32> = fs.iter().map(|f| f()).collect();
    println!("{:?}", out);
}
```

```text
===== rustc --edition 2021 r34_loop.rs =====
(exit 0)
===== ./r34_loop =====
[0, 1, 2]
(exit 0)
```

- `move || i` 는 **회차마다 그 회차의 `i` 를 복사**해 넣는다 — `[0, 1, 2]`.

```rust
// r34_loop_ref.rs
// move 없이 모으면
fn main() {
    let mut fs: Vec<Box<dyn Fn() -> i32>> = Vec::new();
    for i in 0..3 {
        fs.push(Box::new(|| i));
    }
    println!("{}", fs.len());
}
```

```text
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

- ★★ **`move` 를 빼면 E0597 — `i` does not live long enough.** 클로저가 `i` 를 **빌리는데** `i` 는 **회차 끝에 사라진다.** Rust 는 **「모두 같은 변수를 본다」가 되기 전에 컴파일을 거절한다.**

```python
# r34_late.py
# 파이썬 — 루프에서 람다를 모은다. 각 람다는 어느 i 를 보나
fs = []
for i in range(3):
    fs.append(lambda: i)
print([f() for f in fs])
fs2 = [lambda i=i: i for i in range(3)]
print([f() for f in fs2])
```

```text
===== python3 r34_late.py =====
[2, 2, 2]
[0, 1, 2]
(exit 0)
```

- ★★ **파이썬은 `[2, 2, 2]`** — 람다가 **변수 `i` 를 부를 때 읽는다**(늦은 바인딩). 기본 인자로 **정의 때의 값**을 박으면 `[0, 1, 2]`. 정본은 Python 갈래의 [**22번**](../../../python/syntax/22-closures-and-late-binding/).
- ★ **Go 는 1.22 에서 루프 변수를 회차마다 새로 만들도록 언어를 바꿨다** — 그 전에는 파이썬과 같은 증상이었다. 정본은 Go 갈래의 [**13번**](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/)(그 편이 `go.mod` 로 두 판을 나란히 던졌다).
- ★ **세 언어의 자리** — 파이썬은 **늦게 읽고**, Go 는 **변수를 회차마다 새로** 두고, Rust 는 **빌림이면 거절 · `move` 면 복사**다. 같은 버그를 **다른 층**에서 막는다.

## 문법 — 형태와 규칙

```text
   형태

   let c = |x: i32| x + 1;                ← 인자 타입은 대개 추론된다
   let c = || s.len();                    ← s 를 불변 빌림으로 잡는다  → Fn
   let mut c = || s.push(1);              ← 가변 빌림 · 부르려면 let mut  → FnMut
   let c = || drop(s);                    ← 이동 · 한 번만 부른다          → FnOnce
   let c = move || s.len();               ← 이동으로 잡지만 읽기만        → 여전히 Fn
   fn need(f: impl Fn()) / impl FnMut() / impl FnOnce()   ← 받는 쪽이 요구를 적는다
   thread::spawn(move || …)               ← 'static 이 필요한 자리는 move


   금지 사례 — 던져서 받은 것

   변수에 묶은 FnMut 클로저를 impl Fn 에                ✘ E0525
   부르는 자리에 쓴 s.push(1) 클로저를 impl Fn 에          ✘ E0596  "captured variable in a `Fn` closure"
   부르는 자리에 쓴 drop(s) 클로저를 impl FnMut 에         ✘ E0507
   move 뒤에 원래 변수를 씀                             ✘ E0382
   FnOnce 를 두 번 부름                                 ✘ E0382  "cannot be invoked more than once"
   let c = || n += 1; c();                            ✘ E0596  (c 가 mut 아님)
   thread::spawn(|| v.len())                          ✘ E0373
   루프에서 move 없이 || i 를 모음                      ✘ E0597
   2018: 필드 하나 쓰는 클로저 + 다른 필드 대입            ✘ E0506  (2021 은 통과)
```

**규칙 불릿.**

- ★★★ **모든 클로저는 `FnOnce` · 옮기지 않으면 `FnMut` · 고치지도 옮기지도 않으면 `Fn`** — 언어 규칙이다(Reference)((1)).
- ★★ **`move` 는 포착 방식만 바꾼다** — 트레이트는 몸통이 정한다((3)).
- ★★ **클로저가 함수보다 오래 살면 `move`** — 안 그러면 E0373((4)).
- ★ **`FnMut` 은 `let mut` 으로 · `FnOnce` 는 한 번만**((5)).
- ★★ **2021 부터 클로저는 쓴 자리(필드)만 잡는다** — 2018 이하는 변수 전체((6)).

## 어디서 틀리나

### 1. ★★★ 「`move` 를 붙이면 `FnOnce` 가 된다」

**아니다**((3)). `move || s.len()` 은 **`Fn`** 이다 — 두 번, 세 번 불렀다. 트레이트는 **몸통이 잡은 것으로 무엇을 하나**가 정하고, `move` 는 **어떻게 잡나**만 바꾼다(Reference 가 Note 로 직접 경고한다).
★ 반대로 **`move` 없이도 `FnOnce` 가 된다** — `|| drop(s)` 가 그렇다.

### 2. ★★ 「E0525 가 안 나오면 트레이트 문제가 아니다」

**같은 거절이 E0596·E0507 로도 나온다**((2)). **클로저를 부르는 자리에 바로 쓰면** 컴파일러가 기대(`Fn`)부터 정하고 몸통을 탓한다.
★ 번호가 달라도 **격자의 칸은 같다** — 「받는 쪽 경계를 넓히거나, 클로저가 덜 하게」가 공통 처방이다.

### 3. ★★ 「읽기만 하는 클로저는 스레드에 넘길 수 있다」

**E0373**((4)). 읽기뿐이면 **빌림으로** 잡히고, 스레드는 **`'static`** 을 요구한다. `move` 가 필요한 것은 **트레이트 때문이 아니라 수명 때문**이다.

### 4. ★★ 「클로저는 쓴 변수를 통째로 잡는다」

**2018 까지의 이야기다**((6)). 2021 부터는 **필드 하나**만 잡아 E0506·E0382 가 사라지고 **크기도 32 → 24** 로 줄었다. ★ 그래서 **에디션을 올리면 드롭 시점이 바뀔 수 있다** — Edition Guide 가 이전 린트를 둔 이유다.

### 5. ★ 「`move` 클로저의 크기는 잡은 값들의 크기와 같다」

**이 판에서는 그렇게 보였지만 보장이 아니다**((5)) — Reference 「클로저는 레이아웃 보장이 없다」. ★ 그리고 `move` 가 **없으면** `Copy` 값도 **빌림(8)** 으로 잡힌다(`by_ref` 8 대 `by_move` 4).

### 6. ★ 「파이썬처럼 루프 클로저가 전부 마지막 값을 본다」

**Rust 에서는 그 코드가 컴파일되지 않는다**((7)) — `move` 없이 모으면 E0597. `move` 면 회차마다 복사라 `[0, 1, 2]`.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ **세 트레이트 판정**(옮김 → `FnOnce` 만 · 고침 → `FnMut` 까지 · 그 밖 → `Fn` 까지) | ★ **언어 보장** — Reference(Call traits) | (1)의 격자 |
| ★★ **`move` 가 트레이트를 안 바꾸는** 것 | ★ **언어 보장** — Reference 의 Note | (3) |
| 포착 방식 넷과 **「처음 맞는 방식」** 규칙 · Copy 값의 불변 빌림 | ★ **언어 보장** — Reference(Capture modes) | (5)의 `by_ref` |
| ★★ **정밀 포착(필드 단위)** | ★ **에디션 보장** — 2021~ · 2018 이하는 변수 전체(Reference · Edition Guide) | (6)의 격자 |
| 같은 거절이 **E0525 냐 E0596/E0507 이냐** | ★ **구현 세부** — 추론이 어느 쪽에서 먼저 닿나에 따른 진단 선택 | (2) |
| ★★ **클로저 크기**(0 · 4 · 8 · 16 · 24 · 32) | ★ **구현 세부** — Reference 「Closures have no layout guarantees」 | (5)·(6) |
| `help:` 문구(`move` · `let mut` · `FnMut` 으로 넓혀라 · `clone`) | ★ **구현 세부** — 진단의 제안 | (2)·(3)·(4)·(5) |
| 클로저의 `Send`·`Sync`·`Clone`·`Copy` 규칙 | ★ **언어 보장** — Reference(Other traits) | 이 문서는 던지지 않았다 — 36번의 로그 클로저가 `Copy` 로 세 번 쓰였다 |

## 언제 쓰고 언제 안 쓰나

- ★★ **받는 쪽 경계는 「필요한 만큼만」 요구한다** — 한 번만 부르면 **`FnOnce`**(가장 많은 클로저를 받는다), 여러 번이면 **`FnMut`**, 공유·동시 호출이면 **`Fn`**((1)).
- ★★ **`move` 는 수명 때문에 붙인다** — 스레드·반환·`'static` 이 필요한 자리((4)). 트레이트를 바꾸려고 붙이지 않는다((3)).
- ★ **`move` 로 넣되 원본도 쓰고 싶으면** 넣기 전에 **복제**하거나 **`Rc`/`Arc`** 를 복제해 넣는다((3)의 `help:`).
- ★ **2018 코드를 2021 로 올릴 때** — 클로저가 필드 하나만 잡게 되어 **드롭 시점**이 바뀔 수 있다. 의미가 걸리면 `let _ = &p;` 로 통째 포착을 적는다((6)).

## 핵심 문장

- ★★★ **클로저의 트레이트는 몸통이 정한다 — 옮기면 `FnOnce`, 고치면 `FnMut`, 읽기만이면 `Fn`** — 컴파일러의 3×3 격자가 거절 칸 **3 / 9** 로 그렸다((1)).
- ★★★ **`move` 는 「어떻게 잡나」이지 「무엇이 되나」가 아니다** — `move || s.len()` 은 `Fn` 이다((3)).
- ★★ **`move` 가 꼭 필요한 것은 수명 때문이다** — 스레드·반환에서 E0373((4)).
- ★★ **2021 부터 클로저는 필드 하나만 잡는다** — 같은 소스 셋이 2018 과 2021 사이에서 **3 / 3** 갈렸다((6)).
- ★ **클로저의 크기가 무엇을 어떻게 잡았는지 말한다** — 단 그 수치는 보장이 아니다((5)).

## 관련 자료

- ★★ [**10번 주제** — 빌림과 별칭 규칙](../10-borrowing-and-aliasing-rules/) — **경계**: 「불변 여럿 / 가변 하나」의 **규칙과 해결법**은 거기다. 여기는 그 규칙이 **클로저의 세 트레이트로 번역된 모양**만 보였다.
- [**08번 주제** — 소유권과 이동](../08-ownership-and-move/) — `FnOnce`·`move` 의 E0382 는 거기서 본 이동 그대로다.
- [**32번 주제** — `impl Trait`](../32-impl-trait-argument-return-position-and-2024-capture/) (4) — 환경을 안 잡은 클로저가 함수 포인터로 모이는 것. 이 주제의 「잡는 쪽」과 짝이다.
- [**33번 주제** — `dyn Trait`](../33-dyn-trait-objects-and-object-safety/) — (7)의 `Box<dyn Fn() -> i32>` 는 클로저 트레이트의 트레이트 객체다.
- [**35번 주제** — 함수 포인터와 클로저 반환](../35-function-pointers-and-returning-closures/) — 이 주제의 **다음 사슬**. `fn` 으로의 강제 격자와 **반환할 때의 `move`**.
- [**36번 주제** — `Iterator`](../36-iterator-adapters-laziness-and-collect/) — 어댑터가 받는 클로저가 **`FnMut`** 인 이유(여러 번 부르고, 상태를 고칠 수 있게).
- ★ 교차 갈래 — Python 갈래의 [**22번**](../../../python/syntax/22-closures-and-late-binding/)(늦은 바인딩) · Go 갈래의 [**13번**](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/)(1.22 루프 변수) — (7)은 **두 편의 결론을 인용**했고 Go 는 다시 던지지 않았다.
- 목록의 **47번 주제** — 에디션 이전과 `cargo fix --edition`. (6)의 린트가 거기서 절차로 쓰인다.
- 목록의 **49번 주제** — 스레드 `spawn`/`join` 과 `move` 클로저. (4)의 E0373 이 거기서 본체가 된다.
- 목록의 **50번 주제** — `Send`/`Sync`. (4)의 `thread::spawn` 이 요구하는 나머지 절반.

## 용어 풀이

- **클로저(closure)** — 환경을 잡을 수 있는 익명 함수. 타입마다 **이름 없는 고유 타입**이다.
- **포착(capture)** — 클로저가 바깥 변수를 자기 안에 넣는 것. 불변 빌림 · 고유 불변 빌림 · 가변 빌림 · 이동.
- **`Fn` / `FnMut` / `FnOnce`** — 클로저를 `&self` / `&mut self` / `self` 로 부르는 세 트레이트.
- **`move`** — 모든 포착을 이동(Copy 면 복사)으로 바꾸는 표시.
- **정밀 포착(disjoint capture)** — 2021 부터 클로저가 변수 전체가 아니라 **쓴 자리(필드)** 만 잡는 것(RFC 2229).
- **자리(place)** — 메모리 위치를 가리키는 식. `p`·`p.name`·`*r` 같은 것.
- **늦은 바인딩(late binding)** — 이름을 **쓸 때** 값으로 푸는 것(파이썬 클로저).
- **E0525** — 요구한 클로저 트레이트를 그 클로저가 구현하지 않는다.
- **E0373** — 빌린 것을 잡은 클로저가 그 주인보다 오래 살 수 있다.

## 더 들어가면

- **고유 불변 빌림(unique immutable borrow)** — `let r = &mut x; let c = || *r = 1;` 처럼 **가변 참조를 통해 쓰는** 경우의 포착 방식. Reference 에만 나오는 넷째 방식이다(이 문서는 던지지 않았다).
- **클로저의 `Clone`·`Copy`** — 잡은 것이 전부 `Copy` 이고 가변 빌림이 없으면 클로저도 `Copy` 다(Reference). [36번](../36-iterator-adapters-laziness-and-collect/)의 로그 클로저 `map_fn` 이 `&RefCell` 만 잡아 **세 사슬에 거듭 쓰였다**.
- **`async` 클로저와 `AsyncFn*`** — 이 판에 안정돼 있다(Reference 의 async 절). 이 문서는 던지지 않았다 — 목록의 **54번 주제** 근처.
- **HRTB(`for<'a> Fn(&'a T)`)** — 참조를 받는 클로저 경계에 숨어 있는 고차 수명. 이 목록에는 따로 주제가 없다(이 문서는 던지지 않았다).
