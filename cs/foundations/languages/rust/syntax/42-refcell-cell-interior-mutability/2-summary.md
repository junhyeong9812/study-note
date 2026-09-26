# rust/syntax/42 — `RefCell`/`Cell` 내부 가변성 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `std::cell` 모듈 문서](https://doc.rust-lang.org/std/cell/index.html)(「dynamic borrowing」 · `Sync` 아님 · 대응하는 `Sync` 판) ·
> [std — `RefCell`](https://doc.rust-lang.org/std/cell/struct.RefCell.html)(`borrow`·`borrow_mut` 의 §Panics · `try_borrow_mut`) ·
> [std — `Cell`](https://doc.rust-lang.org/std/cell/struct.Cell.html)(`get` 은 `T: Copy`) ·
> [Reference — Destructors · Temporary scopes](https://doc.rust-lang.org/reference/destructors.html#temporary-scopes)(2024 에디션의 `if let` 규칙) ·
> std 소스 `core/src/cell.rs`(패닉 문구 — 로컬 `rust-docs` 의 `src/core/cell.rs.html`).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다.
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다(에디션 격자는 2021·2024 둘).\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★★ **속도·크기는 한 번도 재지 않았다** — 「`RefCell` 은 오버헤드가 있다」 류의 문장은 **근거가 없으므로 쓰지 않는다.** 이 문서가 보이는 「대가」는 **패닉이라는 실패 모드**뿐이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

★★★ **본체 창 — ① 런타임 빌림 격자(조합마다 통과 / 패닉)다.** 컴파일러가 하던 판정을 **실행이** 한다 — 그래서 창도 컴파일 로그가 아니라 **실행 결과**다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★ **흔들린다(정규화)** | 패닉 첫 줄의 **스레드 id** `thread 'main' (NNN)` | 실행마다 바뀐다 — 기본 규칙이 `(<tid>)` 로 바꾼다 |
| 안 흔들린다 | ★★★ **격자의 통과/패닉 칸과 「패닉 칸 N / M」** | 빌림 규칙과 임시값 해제 시점은 언어·std 가 정한다 — **이 주제의 본체** |
| 안 흔들린다 — 단 **std 판의 문구** | ★★ 패닉 메시지 `RefCell already borrowed` / `RefCell already mutably borrowed` | ★ **std 구현**이다((4)). 판이 바뀌면 바뀔 수 있다 — **「패닉한다」는 계약, 문구는 구현** |
| 안 흔들린다 | E0502 · E0599 · E0277 번호·`파일:줄:칸` · 종료 코드(`101`) | 같은 rustc 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 쓴다(패닉 스레드 id 가 걸린다). 격자 스크립트는 패닉의 **셋째 줄(메시지)만** 칸에 옮겨 스레드 id 가 들어가지 않는다.

## 한눈에 — 쉽게 말하면

**`&`/`&mut` 는 「입장권 검사를 매표소(컴파일러)에서 끝낸 공연」이고, `RefCell` 은 「입구에서 직원이 손목 도장을 세는 공연」이다.
규칙은 같다 — 구경꾼은 여럿 되고, 무대에 오르는 사람은 혼자여야 하며, 둘은 동시에 못 한다.
다른 것은 **어기는 순간**이다. 매표소는 표를 안 팔고(컴파일 에러), 입구 직원은 공연 도중에 **사람을 끌어낸다**(패닉).**

| 비유 | 실체 |
|---|---|
| 「**구경꾼 도장**」 | ★★ **`c.borrow()`** → `Ref` 가드. 여럿이 동시에 쥘 수 있다((1)의 첫 행) |
| 「**무대 출입증**」 | ★★ **`c.borrow_mut()`** → `RefMut` 가드. 혼자여야 한다 |
| 「**공연 도중 끌어냄**」 | ★★★ **패닉** `RefCell already borrowed` / `already mutably borrowed` — **앞 줄들은 이미 실행됐다**((3)의 `[1]`) |
| 「**도장을 반납하는 때**」 | ★★★ **가드가 `Drop` 될 때** — 스코프 끝·`drop(guard)`·**문장 끝(임시값)**((1)) |
| 「**들어가도 되나 먼저 묻기**」 | ★★ **`try_borrow_mut()`** → `Err(BorrowMutError)`((5)) |
| 「**도장 없이 물건만 바꿔 주는 사물함**」 | ★ **`Cell<T>`** — 빌림이 없다. `get`(복사) · `set` · `replace` · `take`((6)) |
| 「**다른 극장에는 못 간다**」 | ★ **`RefCell: !Sync`** — 스레드끼리 나누면 E0277. `Mutex`/`RwLock`((7)) |

```text
   같은 위반, 다른 발견 시점 — (3)의 한 쌍 그대로

   &v  +  &mut v                            v.borrow()  +  v.borrow_mut()
   ─────────────────────                    ─────────────────────────────
   rustc → E0502 (exit 1)                   rustc → 통과 (exit 0)
   실행 파일이 안 생긴다                     ./r42_pair_cell
                                              [1] first borrow taken, len 3      ← 여기까지는 돈다
                                              7행 19칸에서 패닉 「RefCell already borrowed」 (exit 101)
```

> **내부 가변성(interior mutability)** — **공유 참조(`&T`)만 가지고도** 안을 고칠 수 있게 하는 것. std: 「별칭이 있어도 **통제된 방식으로** 변경을 허용한다」.\
> 예: `fn touch(&self) { self.hits.set(self.hits.get() + 1) }`.

> **동적 빌림(dynamic borrowing)** — std 의 말: 「`RefCell` 의 빌림은 **런타임에** 추적된다. Rust 의 기본 참조가 **컴파일 시점에** 전부 추적되는 것과 다르다」. 규칙을 어기면 **그 스레드가 패닉한다.**\
> 예: `let a = c.borrow(); let b = c.borrow_mut();` → 패닉.

## 이 주제가 답하려는 질문

1. ★★★ **빌림 검사를 런타임으로 옮기면 무엇이 남나** — 같은 규칙, **다른 발견 시점**, 그리고 **부분 실행된 상태**((1)·(3)).
2. ★★★ **가드는 정확히 언제 풀리나** — 스코프·`drop`·**식의 임시값**·`match`·`if`·`if let`(에디션)((1)·(2)).
3. ★★ **패닉을 피하는 길과, `Cell`·`Mutex` 로 가는 갈림**((5)·(6)·(7)).

★ **선행** — [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Rc` 는 `&T` 만 주므로 여럿이 고치려면 `Rc<RefCell<T>>` 가 필요했다((2)의 부모 링크 · (4)의 표).
[**11번 주제**](../11-borrow-checker-rejections/)의 **전형 9**(3-answer 6번)가 `borrow_mut` 두 번 → `RefCell already borrowed` · 반대 방향 → `RefCell already mutably borrowed` · `try_borrow_mut` 처방을 **이미 쟀다** — 이 편은 그것을 **조합 격자로 넓힌다.**
같은 편 **10번**이 `if let` + `else` 의 **E0597**(2021)과 통과(2024)를 보였다 — (2)는 그 **런타임 판**이다.
[**10번 주제**](../10-borrowing-and-aliasing-rules/)가 컴파일 시점 규칙(E0502·E0499)의 정본이다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 런타임 빌림 격자다

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★★ **런타임 빌림 격자**(조합마다 소스를 만들어 **실행**) | 어느 조합이 **패닉**하나 · 가드가 **언제** 풀리나 | ★ **본체**((1)) |
| ② ★★ **에디션 격자**(2021 × 2024) | `if let` 의 가드가 **어느 갈래까지** 사나 | 쓴다((2)) |
| ③ ★★ **컴파일 대 런타임 한 쌍** | 같은 위반이 E0502 로 막히나 · 실행 중 죽나 | 쓴다((3)) |
| ④ ★★ **std 소스 grep** | 패닉 문구가 **어디서 오나** — 언어인가 std 인가 | 쓴다((4)) |
| ⑤ **컴파일러 진단** E0599 · E0277 | `Cell::get` 의 `Copy` 요구 · `!Sync` | 쓴다((6)·(7)) |
| 실행 시간 · `RefCell` 의 크기 | 「오버헤드가 있다」 | ★ **부적용 — 재지 않는다** |
| Miri 로 빌림 위반 탐지 | — | ★ **못 잰 것**이자 **필요 없는 것** — `RefCell` 위반은 UB 가 아니라 **정의된 패닉**이다. 실행이 곧 판정이다(Miri 는 이 머신에 없다 — 41번 머리말 블록) |

★★ **제5의 상태 — 「같은 질문을 다른 창으로」.** 「이 두 빌림은 겹치나」는 원래 **컴파일러의 창**(E0502)이 답한다. `RefCell` 은 그 창을 **닫는다**(통과) — 그래서 같은 질문을 **실행 결과의 창**으로 옮겨 물었다((3)).
★ 바꾼 창이 **못 보는 것** — **안 지나간 경로**. 패닉하는 조합이 `if` 의 한 갈래에만 있으면 그 갈래를 실행하지 않는 한 **영영 모른다.** 컴파일 에러는 모든 경로를 보지만 런타임 검사는 **지나간 경로만** 본다.

### (1) ★★★ 런타임 빌림 격자 — 열두 조합

**언제 쓰나** — `RefCell` 을 쓰는 코드에서 「여기서 패닉할 수 있나」를 판정할 때마다.

```text
===== 소스: r42_grid.sh =====
# RefCell 빌림 조합마다 프로그램을 하나씩 만들어 던진다 — 통과인가, 패닉이면 문구는 무엇인가
T=$'\t'
cases=(
  'shared + shared (both held)|let a = c.borrow(); let b = c.borrow(); let _ = (a.len(), b.len());'
  'shared held + mut|let a = c.borrow(); let mut b = c.borrow_mut(); b.push(a.len());'
  'mut held + shared|let mut a = c.borrow_mut(); let b = c.borrow(); a.push(b.len());'
  'mut held + mut|let mut a = c.borrow_mut(); let mut b = c.borrow_mut(); a.push(1); b.push(2);'
  'mut in inner block, then mut|{ let mut a = c.borrow_mut(); a.push(1); } let mut b = c.borrow_mut(); b.push(2);'
  'mut, drop(guard), then mut|let mut a = c.borrow_mut(); a.push(1); drop(a); let mut b = c.borrow_mut(); b.push(2);'
  'two statements, temporaries only|c.borrow_mut().push(1); c.borrow_mut().push(2);'
  'one statement: mut receiver + shared argument|c.borrow_mut().push(c.borrow().len());'
  'one statement: value first, then mut|let n = c.borrow().len(); c.borrow_mut().push(n);'
  'match on c.borrow() + mut in arm|match c.borrow().len() { n => c.borrow_mut().push(n) }; println!();'
  'if condition c.borrow() + mut in body|if c.borrow().len() < 9 { c.borrow_mut().push(0); }'
  'mut held, try_borrow_mut|let _a = c.borrow_mut(); let r = c.try_borrow_mut(); println!("try_borrow_mut is_err {}", r.is_err());'
)
printf 'case\tresult\n'
p=0; m=0
for spec in "${cases[@]}"; do
  label=${spec%%|*}
  body=${spec#*|}
  printf 'use std::cell::RefCell;\nfn main() {\n    let c = RefCell::new(vec![1, 2, 3]);\n    %s\n}\n' "$body" > g.rs
  rustc --edition 2021 -A unused -o g g.rs 2>cc.txt || { echo "compile failed: $label"; cat cc.txt; exit 1; }
  if ./g >/dev/null 2>err.txt; then
    res=pass
  else
    res="panic: $(sed -n 3p err.txt)"
    p=$((p+1))
  fi
  row="$label${T}$res"
  cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
  [ "$cols" = 2 ] || { echo "column count $cols != 2"; exit 1; }
  printf '%s\n' "$row"
  m=$((m+1))
done
echo "panic cells: $p / $m"
===== bash r42_grid.sh =====
case	result
shared + shared (both held)	pass
shared held + mut	panic: RefCell already borrowed
mut held + shared	panic: RefCell already mutably borrowed
mut held + mut	panic: RefCell already borrowed
mut in inner block, then mut	pass
mut, drop(guard), then mut	pass
two statements, temporaries only	pass
one statement: mut receiver + shared argument	panic: RefCell already mutably borrowed
one statement: value first, then mut	pass
match on c.borrow() + mut in arm	panic: RefCell already borrowed
if condition c.borrow() + mut in body	pass
mut held, try_borrow_mut	pass
panic cells: 5 / 12
(exit 0)
```

- ★★★ **「패닉 칸 5 / 12」.** 규칙 자체는 10번과 같다 — **읽기 + 읽기만 되고**(첫 행), 쓰기가 끼면 겹칠 수 없다(2·3·4행).
- ★★ **문구가 둘이다** — **`borrow_mut` 가 실패하면 `already borrowed`**, **`borrow` 가 실패하면 `already mutably borrowed`**. 「무엇을 **요청했다가** 거절당했나」로 읽는다(11번 6번의 표와 같다).
- ★★★ **가드가 풀리면 다시 된다** — 안쪽 블록이 끝나거나(5행) `drop(a)` 를 하면(6행) 통과. **NLL 이 아니라 가드의 `Drop` 시점**이 기준이다 — 가드는 참조가 아니라 **값**이기 때문이다.
- ★★★ **임시값은 문장 끝에 풀린다** — 7행 `c.borrow_mut().push(1); c.borrow_mut().push(2);` 는 통과. 가드를 **변수에 안 담으면** 그 문장이 끝날 때 반납된다.
- ★★★ **그런데 한 문장 안이면 겹친다** — 8행 `c.borrow_mut().push(c.borrow().len())` 는 **`already mutably borrowed`**. 수신자(`c.borrow_mut()`)가 **먼저** 평가되어 가드가 살아 있는 동안 인자의 `c.borrow()` 가 온다. 9행처럼 **값을 먼저 꺼내 변수에 담으면** 통과.
- ★★★ **`match` 의 조사 대상(scrutinee)은 임시값 스코프가 아니다** — Reference: 「그 임시값은 **문장의 끝까지** 산다」. 10행은 `c.borrow().len()` 이 `usize` 를 넘겼을 뿐인데 **팔 안의 `borrow_mut` 가 패닉**한다. 가드는 `len()` 뒤에 버려지지 않고 `match` 가 든 문장 끝까지 간다.
- ★★ **`if` 의 조건은 다르다** — 11행은 통과. Reference: `if` 의 (패턴이 아닌) 조건식은 **그 자체가 임시값 스코프**라 본문 전에 가드가 풀린다. **`match` 와 `if` 가 반대다** — 겉모양이 비슷해 가장 헷갈리는 자리다.
- ★ 12행 — **`try_borrow_mut` 는 패닉하지 않는다**(`Err`). (5)에서 자세히.

```text
   가드(Ref/RefMut)는 언제 반납되나 — (1)의 통과/패닉이 이 표로 갈린다

   let a = c.borrow_mut();           변수에 담았다     → 스코프 끝(또는 drop(a))까지      2·3·4·5·6행
   c.borrow_mut().push(1);           임시값           → 그 문장의 끝                     7행 통과
   c.borrow_mut().push(c.borrow()…)  한 문장 안에 둘   → 둘 다 문장 끝까지 → 겹친다        8행 패닉
   match c.borrow().len() { … };     scrutinee 임시값  → match 가 든 문장의 끝             10행 패닉
   if c.borrow().len() < 9 { … }     if 조건 임시값    → 조건 평가 직후                   11행 통과
```

비용 — 빌림마다 **카운터를 확인하고 갱신**하는 일이 런타임에 생긴다(std: 「dynamic checks」). **그 시간은 재지 않았다.** 이 문서가 보인 대가는 **패닉 가능성** 하나다.

### (2) ★★ `if let` 의 가드 — 두 소스 × 두 에디션

**언제 쓰나** — `if let Some(x) = cell.borrow()…` 꼴을 쓰는 순간. 에디션에 따라 답이 갈린다.

```text
===== 소스: r42_iflet.sh =====
# if let 의 조건식 임시값(Ref 가드)은 어느 갈래까지 사는가 — 두 소스 × 두 에디션
cat > then.rs <<'RS'
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    if let Some(n) = c.borrow().first().copied() {
        c.borrow_mut().push(n);
    }
    println!("{:?}", c.borrow());
}
RS
cat > else.rs <<'RS'
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    if let Some(n) = c.borrow().get(9).copied() {
        println!("{n}");
    } else {
        c.borrow_mut().push(0);
    }
    println!("{:?}", c.borrow());
}
RS
printf 'source\tedition\tresult\n'
p=0; m=0
for src in then else; do
  for ed in 2021 2024; do
    rustc --edition $ed -o "$src$ed" "$src.rs" || exit 1
    if out=$(./"$src$ed" 2>err.txt); then
      res="pass $out"
    else
      res="panic: $(sed -n 3p err.txt)"; p=$((p+1))
    fi
    row=$(printf '%s\t%s\t%s' "$src" "$ed" "$res")
    cols=$(printf '%s' "$row" | awk -F'\t' '{print NF}')
    [ "$cols" = 3 ] || { echo "column count $cols != 3"; exit 1; }
    printf '%s\n' "$row"
    m=$((m+1))
  done
done
echo "panic cells: $p / $m"
===== bash r42_iflet.sh =====
source	edition	result
then	2021	panic: RefCell already borrowed
then	2024	panic: RefCell already borrowed
else	2021	panic: RefCell already borrowed
else	2024	pass [1, 2, 3, 0]
panic cells: 3 / 4
(exit 0)
```

- ★★★ **「패닉 칸 3 / 4」** — `then`(본문에서 `borrow_mut`)은 **두 에디션 다 패닉**, `else`(else 갈래에서 `borrow_mut`)는 **2021 패닉 · 2024 통과**.
- ★★★ **2024 가 바꾼 것은 「else 갈래 전에 푼다」까지다.** Reference 의 2024 에디션 차이: 「**`if let` 임시값은 `else` 블록 전에 버려진다**」. **then 본문에서는 2024 에서도 가드가 살아 있다** — 「2024 는 `if let` 문제를 고쳤다」로 외우면 then 칸에서 틀린다.
- ★ 조사 대상 `c.borrow().first().copied()` 는 `Option<i32>` — **값을 복사해 꺼냈는데도** 가드는 식의 임시값으로 남는다. (1)의 `match` 10행과 같은 뿌리다.
- ★ [11번 주제](../11-borrow-checker-rejections/) 10번은 같은 모양을 **블록의 꼬리식**으로 두어 2021 에서 **E0597**(컴파일 에러)을 받았다. 여기는 꼬리식이 아니라서 컴파일은 통과하고 **런타임에** 드러났다 — **같은 원인이 자리에 따라 컴파일 에러도 되고 패닉도 된다.**

### (3) ★★★ 컴파일 대 런타임 — 같은 위반의 두 얼굴

**언제 쓰나** — 「`RefCell` 로 바꾸면 에러가 사라진다」는 유혹이 들 때.

**`&` 와 `&mut` 로 쓰면.**

```text
===== 소스: r42_pair_ref.rs =====
fn main() {
    let mut v = vec![1, 2, 3];
    let a = &v;
    let b = &mut v;
    b.push(a.len());
}
===== rustc --edition 2021 r42_pair_ref.rs =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> r42_pair_ref.rs:4:13
  |
3 |     let a = &v;
  |             -- immutable borrow occurs here
4 |     let b = &mut v;
  |             ^^^^^^ mutable borrow occurs here
5 |     b.push(a.len());
  |            - immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
(exit 1)
```

- ★★ **E0502 — cannot borrow `v` as mutable because it is also borrowed as immutable.** 세 표지(immutable borrow occurs here · mutable borrow occurs here · immutable borrow later used here)가 **겹치는 구간**을 짚는다. **실행 파일이 안 생긴다.**

**같은 모양을 `RefCell` 로 쓰면.**

```text
===== 소스: r42_pair_cell.rs =====
use std::cell::RefCell;

fn main() {
    let v = RefCell::new(vec![1, 2, 3]);
    let a = v.borrow();
    println!("[1] first borrow taken, len {}", a.len());
    let mut b = v.borrow_mut();
    println!("[2] second borrow taken");
    b.push(a.len());
}
===== rustc --edition 2021 r42_pair_cell.rs =====
(exit 0)
===== ./r42_pair_cell 2>/dev/null =====
[1] first borrow taken, len 3
===== ./r42_pair_cell 2>&1 >/dev/null =====

thread 'main' (1253729) panicked at r42_pair_cell.rs:7:19:
RefCell already borrowed
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
```

- ★★★ **컴파일 `exit 0`.** 실행하면 **`[1]` 이 먼저 찍히고**(표준 출력) 7행 19칸에서 **`RefCell already borrowed`** 로 죽는다(`exit 101`). **`[2]` 는 안 찍혔다.**
- ★★★ **이것이 「남는 것」이다** — 규칙은 그대로 남고, **발견 시점이 실행 중으로 밀리며**, **그 전의 부작용은 이미 일어났다.** 파일을 반쯤 쓰고 죽는 프로그램이 이 모양이다.
- ★ 두 스트림을 **갈라** 실었다(규칙 18) — `[1]` 은 stdout, 패닉은 stderr.

### (4) ★★ 패닉 문구는 누가 정하나 — std 소스와 판 확인

**언제 쓰나** — 로그에서 패닉 문구를 grep 하거나, 문서의 옛 문구와 대조할 때.

```text
===== grep -o 'RefCell already[^<"]*' "$(rustc --print sysroot)/share/doc/rust/html/src/core/cell.rs.html" | sort -u =====
RefCell already borrowed
RefCell already borrowed; a previous borrow was at {}
RefCell already mutably borrowed
RefCell already mutably borrowed; a previous borrow was at {}
(exit 0)
```

- ★★★ **1.92 의 std 소스에 문구가 넷 있다** — 뒤의 둘(`; a previous borrow was at {}`)은 `Display for BorrowError`/`BorrowMutError` 의 **`#[cfg(feature = "debug_refcell")]`** 갈래다(로컬 `src/core/cell.rs.html` 에서 읽었다). **std 를 그 기능으로 다시 빌드해야** 켜지는 것이라 이 툴체인에서는 앞의 둘만 나온다.
- ★★ **`-C debug-assertions` 로 사용자 코드를 빌드해도 문구는 같다.**

```text
===== 소스: r42_pair_cell.rs =====
use std::cell::RefCell;

fn main() {
    let v = RefCell::new(vec![1, 2, 3]);
    let a = v.borrow();
    println!("[1] first borrow taken, len {}", a.len());
    let mut b = v.borrow_mut();
    println!("[2] second borrow taken");
    b.push(a.len());
}
===== rustc --edition 2021 -C debug-assertions -o r42_pair_cell_da r42_pair_cell.rs =====
(exit 0)
===== ./r42_pair_cell_da 2>/dev/null =====
[1] first borrow taken, len 3
===== ./r42_pair_cell_da 2>&1 >/dev/null =====

thread 'main' (1253800) panicked at r42_pair_cell.rs:7:19:
RefCell already borrowed
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(exit 101)
```

- ★ **한 글자도 같다**(스레드 id 만 다르다) — `debug_refcell` 은 **std 의 빌드 기능**이지 사용자 코드의 플래그가 아니다.
- ★★★ **「`already borrowed: BorrowMutError`」라는 문구를 본 적이 있다면** — 그것은 `expect("already borrowed")` 꼴이 `BorrowMutError` 의 `Debug` 를 붙인 **옛 형식**이다. **1.92 의 패닉에는 `BorrowMutError` 가 안 나온다**(위 두 블록). 그 이름은 (5)의 `Err` 값의 `Debug` 에서만 보인다. 문구가 **어느 판에서 바뀌었는지는 확인하지 못했다**(로컬 릴리스 노트에 항목이 없다) — 「**안 흔들리는 것은 패닉한다는 사실**」이다.

### (5) ★★ `try_borrow_mut` — 패닉 대신 `Err`

```text
===== 소스: r42_try.rs =====
use std::cell::RefCell;

fn main() {
    let c = RefCell::new(String::from("x"));
    let held = c.borrow();
    match c.try_borrow_mut() {
        Ok(_) => println!("[1] Ok"),
        Err(e) => println!("[1] Err  Debug {:?}  Display {}", e, e),
    }
    drop(held);
    match c.try_borrow_mut() {
        Ok(mut g) => {
            g.push('y');
            println!("[2] Ok  now {}", g);
        }
        Err(e) => println!("[2] Err {:?}", e),
    }
    let m = c.borrow_mut();
    println!("[3] try_borrow while mut held  is_err {}", c.try_borrow().is_err());
    drop(m);
}
===== rustc --edition 2021 r42_try.rs =====
(exit 0)
===== ./r42_try =====
[1] Err  Debug BorrowMutError  Display RefCell already borrowed
[2] Ok  now xy
[3] try_borrow while mut held  is_err true
(exit 0)
```

- ★★ **`[1]` `Err`** — `Debug` 는 **`BorrowMutError`**, `Display` 는 **`RefCell already borrowed`**(패닉 문구와 같은 글자다 — 패닉이 이 `Display` 를 쓴다).
- ★★ **`[2]` 가드를 `drop` 한 뒤에는 `Ok`** · **`[3]` 반대 방향 `try_borrow` 는 `BorrowError`**(`is_err true`).
- ★ **언제 쓰나** — 「지금 바쁘면 다음에」가 말이 되는 자리(재진입 가능한 콜백·관찰자 알림). **대부분은 가드 구간을 좁히는 쪽이 맞다**((1)의 9행).

### (6) ★ `Cell` 은 빌림이 없다 — 값을 넣고 뺀다

```text
===== 소스: r42_cell.rs =====
use std::cell::Cell;

struct Counter {
    hits: Cell<u32>,
}

impl Counter {
    fn touch(&self) {
        self.hits.set(self.hits.get() + 1);
    }
}

fn main() {
    let k = Counter { hits: Cell::new(0) };
    let r1 = &k;
    let r2 = &k;
    r1.touch();
    r2.touch();
    k.touch();
    println!("hits {}", k.hits.get());

    let name = Cell::new(String::from("a"));
    let old = name.replace(String::from("b"));
    let now = name.take();
    println!("old {old:?}  taken {now:?}  left {:?}", name.into_inner());
}
===== rustc --edition 2021 r42_cell.rs =====
(exit 0)
===== ./r42_cell =====
hits 3
old "a"  taken "b"  left ""
(exit 0)
```

- ★★ **`&self` 로 카운터를 올렸다**(`hits 3`) — `r1`·`r2`·`k` 셋이 공유 참조인데 된다. **`Cell` 은 참조를 내주지 않는다** — std: 「값을 **안팎으로 옮겨서** 내부 가변성을 구현한다」. 빌림이 없으니 **빌림 패닉도 없다.**
- ★ `Copy` 가 아닌 `String` 도 **`replace`·`take`·`into_inner`** 는 된다(`old "a"  taken "b"  left ""`).

**그런데 `get` 은.**

```text
===== 소스: r42_cell_get.rs =====
use std::cell::Cell;

fn main() {
    let name = Cell::new(String::from("a"));
    let s = name.get();
    println!("{s}");
}
===== rustc --edition 2021 r42_cell_get.rs =====
error[E0599]: the method `get` exists for struct `Cell<String>`, but its trait bounds were not satisfied
 --> r42_cell_get.rs:5:18
  |
5 |     let s = name.get();
  |                  ^^^
  |
  = note: the following trait bounds were not satisfied:
          `String: Copy`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

- ★★ **E0599** — 「the method `get` exists for struct `Cell<String>`, but its trait bounds were not satisfied」 + **`String: Copy`**. `get` 은 **복사해서 돌려주는** 함수라 `T: Copy` 가 필요하다. 참조를 줄 수 없으니(그게 `Cell` 의 약속) 복사 아니면 꺼내기뿐이다.

| | `Cell<T>` | `RefCell<T>` |
|---|---|---|
| 안을 보는 법 | **값**을 복사(`get`, `T: Copy`)하거나 **옮긴다**(`replace`·`take`) | **가드**(`Ref`/`RefMut`)로 **참조**를 빌린다 |
| 규칙 위반 | **없다** — 빌림이 없다 | **패닉**((1)) |
| 알맞은 것 | 작은 `Copy` 값(카운터·플래그) | 큰 값 · `Copy` 아닌 값을 **제자리에서** 고칠 때 |

### (7) ★ `RefCell` 은 `!Sync` — 스레드끼리 나누면

```text
===== 소스: r42_sync.rs =====
use std::cell::RefCell;
use std::sync::Arc;
use std::thread;

fn main() {
    let shared = Arc::new(RefCell::new(0));
    let s2 = Arc::clone(&shared);
    let h = thread::spawn(move || {
        *s2.borrow_mut() += 1;
    });
    h.join().unwrap();
    println!("{}", shared.borrow());
}
===== rustc --edition 2021 r42_sync.rs =====
error[E0277]: `RefCell<i32>` cannot be shared between threads safely
  --> r42_sync.rs:8:27
   |
 8 |       let h = thread::spawn(move || {
   |  _____________-------------_^
   | |             |
   | |             required by a bound introduced by this call
 9 | |         *s2.borrow_mut() += 1;
10 | |     });
   | |_____^ `RefCell<i32>` cannot be shared between threads safely
   |
   = help: the trait `Sync` is not implemented for `RefCell<i32>`
   = note: if you want to do aliasing and mutation between multiple threads, use `std::sync::RwLock` instead
   = note: required for `Arc<RefCell<i32>>` to implement `Send`
note: required because it's used within this closure
  --> r42_sync.rs:8:27
   |
 8 |     let h = thread::spawn(move || {
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

- ★★ **E0277 — `` `RefCell<i32>` cannot be shared between threads safely ``.** `= note:` 사슬이 이유를 준다 — 「required for `Arc<RefCell<i32>>` to implement `Send`」(41번 (3)의 `Arc` 경계 `T: Send + Sync`).
- ★★★ **컴파일러의 처방은 `RwLock` 이다** — 「if you want to do aliasing and mutation between multiple threads, use `std::sync::RwLock` instead」. std `cell` 모듈 문서도 「`RefCell<T>` 에 대응하는 `Sync` 판은 **`RwLock<T>`**」라고 적는다(읽기 여럿 · 쓰기 하나라는 **같은 규칙**이라서다). `Mutex` 도 된다 —

```text
===== 소스: r42_sync_mutex.rs =====
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let shared = Arc::new(Mutex::new(0));
    let s2 = Arc::clone(&shared);
    let h = thread::spawn(move || {
        *s2.lock().unwrap() += 1;
    });
    h.join().unwrap();
    println!("{}", shared.lock().unwrap());
}
===== rustc --edition 2021 r42_sync_mutex.rs =====
(exit 0)
===== ./r42_sync_mutex =====
1
(exit 0)
```

- ★ `Mutex` 는 **읽기도 혼자**라 규칙이 더 좁다. 락의 정본은 목록의 **52번 주제**다. ★ **런타임 비용 비교는 하지 않았다.**

### (8) ★ `Rc<RefCell<T>>` — 여럿이 같은 값을 고친다

```text
===== 소스: r42_rc_refcell.rs =====
use std::cell::RefCell;
use std::rc::Rc;

fn main() {
    let log = Rc::new(RefCell::new(Vec::new()));
    let a = Rc::clone(&log);
    let b = Rc::clone(&log);
    a.borrow_mut().push("from a");
    b.borrow_mut().push("from b");
    println!("strong {}  contents {:?}", Rc::strong_count(&log), log.borrow());
}
===== rustc --edition 2021 r42_rc_refcell.rs =====
(exit 0)
===== ./r42_rc_refcell =====
strong 3  contents ["from a", "from b"]
(exit 0)
```

- ★★ **`strong 3`**(`log` · `a` · `b`) · 두 주인이 넣은 것이 **한 `Vec` 에** 있다. 41번 (4)의 표에서 「모두가 같은 값」 칸이 이것이다.
- ★ 한 줄 요약 — **`Rc` 가 「주인 여럿」을, `RefCell` 이 「공유 참조로 고치기」를** 맡는다. 둘은 서로 모르는 두 도구의 조합이다.

## 문법 — 형태와 규칙

```text
   use std::cell::{Cell, RefCell};

   let c = RefCell::new(v);
   let r  = c.borrow();          // Ref<T>     — 여럿 가능 · 쓰기와 겹치면 패닉
   let mut w = c.borrow_mut();   // RefMut<T>  — 혼자여야 · 겹치면 패닉
   drop(w);                      // 가드를 버리면 반납
   c.try_borrow_mut()            // Result<RefMut<T>, BorrowMutError> — 패닉 대신 Err

   let k = Cell::new(0);
   k.set(k.get() + 1);           // get 은 T: Copy · 참조를 주지 않는다
   k.replace(1); k.take();       // Copy 아니어도 된다 (take 는 T: Default)
```

- ★★★ **규칙은 `&`/`&mut` 와 같다 — 검사가 런타임이고 위반이 패닉이다**((1)·(3)).
- ★★★ **가드는 `Drop` 될 때 반납된다** — 변수면 스코프 끝, 임시값이면 문장 끝, **`match` 조사 대상이면 `match` 가 든 문장 끝**((1)).
- ★★ **`if let` 의 가드는 2024 에서 `else` 전에 풀리고, then 본문에서는 두 에디션 다 살아 있다**((2)).
- ★ **`Cell` 은 빌리지 않는다 · `RefCell`/`Cell` 은 `!Sync`**((6)·(7)).

## 어디서 틀리나

### 1. ★★★ 「`RefCell` 로 바꿨더니 에러가 사라졌다 — 해결했다」

(3) — **컴파일은 통과하고 실행 중에 죽는다.** 11번 3-answer 가 말한 대로 「위험을 미룬 것」이다. 게다가 **안 지나간 경로의 위반은 영영 모른다**((0)).

### 2. ★★★ 「`c.borrow().len()` 은 `usize` 만 남으니 가드는 바로 풀린다」

(1)의 10행 — **`match` 의 조사 대상이면 `match` 가 든 문장 끝까지 산다.** (2)의 `if let` 도 같다. **값을 먼저 `let` 에 담아라**(9행).

### 3. ★★★ 「2024 에디션은 `if let` 의 가드 문제를 고쳤다」

(2) — 고친 것은 **`else` 갈래**다. **then 본문은 여전히 패닉**한다(`then 2024 panic`).

### 4. ★★ 「한 문장에 두 번 빌려도 앞의 것이 끝났으니 괜찮다」

(1)의 8행 — **수신자의 가드가 인자 평가 동안 살아 있다.** `already mutably borrowed`.

### 5. ★★ 「패닉 문구는 `already borrowed: BorrowMutError` 다」

(4) — **1.92 는 `RefCell already borrowed`** 다. 문구는 std 구현이라 판마다 다를 수 있다. **grep 할 때는 문구 전체가 아니라 `already borrowed`·`already mutably borrowed` 로.**

### 6. ★★ 「`Cell<String>` 에서 `get` 으로 꺼내 보면 된다」

(6) — **E0599**(`String: Copy`). `take`·`replace` 로 옮겨 꺼내야 한다.

### 7. ★ 「`RefCell` 은 오버헤드가 있으니 쓰지 마라」

**이 문서는 재지 않았다.** 피할 이유로 적을 수 있는 것은 **패닉 가능성**과 **`!Sync`** 두 가지다 — 둘 다 출력이 있다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 겹치는 빌림이면 **패닉**한다 | ★ **std 의 계약**(`borrow`·`borrow_mut` 의 §Panics) | (1)·(3) |
| 패닉 **문구**(`RefCell already borrowed`) | ★ **std 구현** — `Display for BorrowMutError`. `debug_refcell` 빌드면 위치가 붙는다 | (4) |
| 가드가 **어느 줄에서** 풀리나(임시값 스코프) | ★ **언어**(Reference — Destructors · Temporary scopes) | (1)·(2) |
| `if let` 임시값이 2024 에서 `else` 전에 풀린다 | ★ **언어 · 에디션**(Reference 2024 edition differences) | (2) |
| `Cell::get` 이 `T: Copy` 를 요구한다 | ★ **std 의 시그니처** | (6) E0599 |
| `Cell`·`RefCell` 이 `Sync` 가 아니다 | ★ **std 의 트레이트 구현** — 컴파일러가 강제 | (7) E0277 |
| 빌림 카운터가 **몇 바이트이고 어디** 있나 | ★ **구현 세부** — 공개 API 가 아니다. **재지 않았다** | — |
| 패닉 종료 코드 `101` | ★ **std 런타임의 관행**(이 판 관찰) | (3) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고를 것 | 근거 |
|---|---|---|
| 빌림을 **정적으로** 쓸 수 있다 | ★ **`&`/`&mut`** — 먼저 구조를 고친다(11번의 열쇠 1\~5) | 컴파일러가 모든 경로를 본다 |
| `&self` 메서드 안에서 작은 값을 바꾼다(카운터·캐시 플래그) | **`Cell`** | (6) — 패닉이 없다 |
| 여러 주인이 **같은 큰 값을 고친다**(한 스레드) | **`Rc<RefCell<T>>`** | (8) |
| 스레드를 넘는다 | **`Mutex` / `RwLock`**(`Arc` 로 감싸서) | (7) |
| 재진입이 가능한 콜백 | **`try_borrow_mut`** 로 물어본다 | (5) |
| 가드를 오래 쥐어야 한다 | ★ **구조를 다시 본다** — 가드가 길수록 (1)의 겹침이 는다 | — |

## 핵심 문장

- ★★★ **`RefCell` 은 빌림 규칙을 없애지 않는다 — 검사를 실행 중으로 옮기고, 위반을 패닉으로 바꾼다. 앞 줄들은 이미 실행된 뒤다.**
- ★★★ **가드는 참조가 아니라 값이다 — `Drop` 될 때 반납되고, `match` 의 조사 대상이면 그 문장 끝까지 산다.**
- ★★ **2024 에디션은 `if let` 의 가드를 `else` 전에 풀어 줄 뿐, then 본문에서는 그대로 쥐고 있다.**
- ★★ **`Cell` 은 참조를 내주지 않아 빌림이 없다 — 그래서 `get` 은 `Copy` 를 요구한다.**
- ★ **패닉 문구는 std 구현이다(1.92 — `RefCell already borrowed`) — 기억할 것은 「패닉한다」다.**

## 관련 자료

- [**11번 주제**](../11-borrow-checker-rejections/) — 전형 9(`RefCell` 두 번 빌림)와 10번(`if let` 의 E0597). **그쪽은 「마지막 열쇠」로서의 `RefCell`, 여기는 가드가 언제 풀리나의 격자.**
- [**10번 주제**](../10-borrowing-and-aliasing-rules/) — 컴파일 시점 규칙(E0502·E0499)의 정본.
- [**41번 주제**](../41-rc-arc-shared-ownership-and-weak-cycles/) — `Rc<RefCell<T>>` 의 `Rc` 쪽 · `Arc` 의 `Send + Sync` 경계.
- [**44번 주제**](../44-drop-mem-drop-replace-and-take/) — 가드가 반납되는 순간은 결국 **`Drop` 순서**다. 임시값의 해제 줄이 거기 격자에 있다.
- 목록의 **47번 주제**(에디션 2021 대 2024) · **50번 주제**(`Send`/`Sync`) · **52번 주제**(`Mutex`/`RwLock`).

## 용어 풀이

- **`RefCell<T>`** — 빌림 규칙을 런타임에 검사하는 칸. `borrow`/`borrow_mut` 가 가드를 준다.
- **`Ref<T>` / `RefMut<T>`** — 빌림 가드. `Deref` 로 `&T`/`&mut T` 처럼 쓰이고, `Drop` 될 때 빌림을 반납한다.
- **`Cell<T>`** — 값을 옮겨 넣고 빼는 칸. 참조를 주지 않는다.
- **`BorrowError` / `BorrowMutError`** — `try_borrow`/`try_borrow_mut` 가 실패할 때의 오류 값.
- **조사 대상(scrutinee)** — `match x { … }` 의 `x`, `if let P = x` 의 `x`. 그 식의 임시값은 구문 전체만큼 산다.
- **임시값 스코프(temporary scope)** — 식이 만든 이름 없는 값이 버려지는 지점. 대개 문장 끝이다.
- **`Sync`** — `&T` 를 여러 스레드가 나눠 가져도 되는가를 나타내는 자동 트레이트.

## 더 들어가면

- `RefCell::borrow` 가 돌려주는 `Ref` 는 `Ref::map` 으로 **안쪽 필드만** 빌린 가드로 좁힐 수 있다. **이 문서는 던지지 않았다.**
- `OnceCell`·`LazyCell` — 한 번만 쓰는 칸(대응하는 `Sync` 판은 `OnceLock`·`LazyLock` — std `cell` 모듈 문서). 목록의 **53번 주제**.
