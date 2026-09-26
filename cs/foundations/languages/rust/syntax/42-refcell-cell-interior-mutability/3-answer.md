# rust/syntax/42 — `RefCell`/`Cell` 내부 가변성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로(에디션 격자는 2021·2024) 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 패닉 첫 줄의 `thread 'main' (NNN)` 은 **실행마다 바뀌는 칸**이다(서머리 머리말의 표).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `5 / 12` — 한 문장 안의 두 빌림과 `match` 의 조사 대상이 함정이다

**출력**

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

**왜 그런가**

- ★★ 2·4행 — `borrow_mut` 가 거절당하면 **`RefCell already borrowed`**, 3행 — `borrow` 가 거절당하면 **`RefCell already mutably borrowed`**.
- ★★ 5·6행 — 가드가 **`Drop`** 되면(블록 끝 · `drop(a)`) 다시 된다.
- ★★★ **7행 대 8행** — 7행은 가드가 **문장마다** 버려져 통과. 8행은 **한 문장 안**에서 수신자 `c.borrow_mut()` 의 가드가 인자 `c.borrow()` 평가 동안 살아 있어 **`already mutably borrowed`**.
- ★★★ **10행 대 11행** — `match` 의 조사 대상은 **임시값 스코프가 아니라** 가드가 **문장 끝까지** 산다 → 팔 안의 `borrow_mut` 패닉. `if` 의 조건식은 **그 자체가 임시값 스코프**라 본문 전에 풀린다 → 통과.
- ★ 12행 — `try_borrow_mut` 는 **`Err` 를 돌려줄 뿐** 패닉하지 않는다.

### 2. ★★ `3 / 4` — 2024 는 `else` 갈래만 살렸다

**출력**

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

**왜 그런가**

- ★★★ **then 본문에서는 두 에디션 다 가드가 살아 있다** → 패닉 둘.
- ★★★ **`else` 갈래는 2021 패닉 · 2024 통과** — Reference 의 2024 차이: 「`if let` 임시값은 **`else` 블록 전에** 버려진다」.
- ★ 조사 대상이 `Option<i32>` 를 **복사해** 꺼냈는데도 가드는 식의 임시값으로 남았다 — 1번 10행과 같은 뿌리다.

### 3. ★★★ E0502 대 `exit 101` — 뒤쪽은 `[1]` 을 찍고 죽는다

**출력**

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

**왜 그런가**

- ★★ 앞 소스 — **E0502**, 실행 파일이 안 생긴다.
- ★★★ 뒤 소스 — **컴파일 `exit 0`.** 표준 출력에 **`[1] first borrow taken, len 3`**, 표준 오류에 **7행 19칸 패닉 `RefCell already borrowed`**, 종료 **`101`**. **`[2]` 는 안 찍혔다.**

### 4. ★★ `Err` 의 `Debug` 는 `BorrowMutError`, `Display` 는 `RefCell already borrowed`

**출력**

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

**왜 그런가**

- ★★ **`[1]`** — `held` 가드가 살아 있어 `Err`. `Debug` 는 타입 이름 **`BorrowMutError`**, `Display` 는 **패닉 문구와 같은 글자**(std 의 `panic_already_borrowed` 가 이 `Display` 를 찍는다 — 로컬 `src/core/cell.rs.html`).
- ★ **`[2]`** — `drop(held)` 뒤에는 `Ok` → `xy`. **`[3]`** — 가변 가드가 살아 있으면 `try_borrow` 도 `Err`.

### 5. ★★ `hits 3` · `old "a"  taken "b"  left ""` — `get` 은 E0599(`String: Copy`)

**출력**

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

**왜 그런가**

- ★★ **공유 참조 셋으로 카운터를 올렸다** — `Cell` 은 참조를 내주지 않고 **값을 옮겨** 넣고 뺀다(std). 빌림이 없으니 패닉도 없다.
- ★★ **`get` 은 복사해서 돌려주므로 `T: Copy`** — `String` 이면 **E0599**, `= note:` 가 **`String: Copy`** 를 짚는다. `replace`·`take`·`into_inner` 는 된다.

### 6. ★★ E0277 — `RefCell<i32>` cannot be shared between threads safely · 권하는 것은 `RwLock`

**출력**

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

**왜 그런가**

- ★★ `= help:` 「the trait `Sync` is not implemented for `RefCell<i32>`」 → `= note:` 「required for `Arc<RefCell<i32>>` to implement `Send`」(`Arc<T>: Send` 는 `T: Send + Sync` 를 요구한다 — 41번).
- ★★★ **컴파일러가 권하는 것은 `std::sync::RwLock`** — `Mutex` 가 아니다. std `cell` 문서도 「`RefCell<T>` 의 `Sync` 판은 `RwLock<T>`」. `Mutex` 로도 통과한다(서머리 (7)의 `r42_sync_mutex` — `1`).

### 7. ★★★ 규칙은 같고, 발견이 실행 중으로 밀리고, 그 전의 부작용은 남는다

- ★★ **같은 것** — 「읽기 여럿 또는 쓰기 하나」라는 규칙(std `cell` 문서가 그대로 적는다).
- ★★★ **달라진 것** — ① **발견 시점**(컴파일 → 실행) ② **실패의 모양**(에러 → 패닉 · `exit 101`) ③ **부분 실행**(3번의 `[1]` 은 이미 찍혔다).
- ★★★ **실행하지 않은 경로** — 컴파일 에러는 **모든 경로**를 보지만 런타임 검사는 **지나간 경로만** 본다. 패닉하는 조합이 드문 갈래에 있으면 테스트가 통과해도 남는다. 그래서 「에러가 사라졌다」는 **위험을 미룬 것**이다(11번 3-answer).

### 8. ★★★ `match` 조사 대상은 문장 끝까지 · `if` 조건은 조건 직후 · 2024 는 `if let` 의 `else` 만

- ★★★ Reference(Destructors · Temporary scopes) — **`if`·`while` 의 (패턴이 아닌) 조건식은 임시값 스코프**다 → 조건 평가가 끝나면 가드가 버려진다.
- ★★★ **`match` 의 조사 대상은 임시값 스코프가 아니다** — 「그 임시값은 **문장의 끝까지** 산다」 → 팔 전체가 가드를 쥔 채 돈다.
- ★★ **2024 가 바꾼 것** — **`if let` 임시값은 `else` 블록 전에** 버려진다. then 본문은 그대로다(2번). 꼬리식 임시값도 2024 에서 좁혀졌다 — [11번 주제](../11-borrow-checker-rejections/) 10번의 E0597 이 그 자리다.

### 9. ★★ `RefCell already borrowed` — 옛 형식은 `expect` 가 붙인 것 · 나머지 둘은 std 의 `debug_refcell` 빌드

- ★★ **1.92 — `RefCell already borrowed`**(3번 · 서머리 (4)의 `-C debug-assertions` 판도 한 글자도 같다).
- ★★★ **`already borrowed: BorrowMutError`** 는 `expect("already borrowed")` 가 오류 값의 `Debug` 를 붙이던 **옛 형식**이다 — **1.92 의 패닉에는 안 나온다.** 그 이름은 4번의 `Debug` 에서만 보인다. **어느 판에서 바뀌었는지는 확인하지 못했다.**
- ★★ std 소스(로컬 `src/core/cell.rs.html`)의 넷 중 **`; a previous borrow was at {}`** 가 붙은 둘은 `#[cfg(feature = "debug_refcell")]` 갈래 — **std 를 그 기능으로 빌드해야** 나온다. **`-C debug-assertions` 는 사용자 코드의 플래그라 안 켜진다**(서머리 (4)).

### 10. ★★ 카운터는 `Cell`, 같은 `Vec` 은 `RefCell` — `Cell<String>` 은 `take`/`replace`

- ★★ **호출 횟수** — 작은 `Copy` 값이라 **`Cell<u32>`**(5번 `hits 3`). 패닉 가능성이 없다.
- ★★ **같은 `Vec` 에 넣기** — **제자리에서** 고쳐야 하므로 **`RefCell<Vec<_>>`**(여러 주인이면 `Rc<RefCell<_>>` — 서머리 (8)).
- ★ **`Cell<String>` 에서 꺼내기** — `take()`(빈 값을 남긴다, `T: Default`) · `replace(new)` · `into_inner()`. `get()` 은 E0599.

### 11. ★ `Rc` 는 「주인 여럿」, `RefCell` 은 「공유 참조로 고치기」 — 스레드면 `Arc` 와 `Mutex`/`RwLock`

- ★★ **`Rc`** 가 여러 주인을, **`RefCell`** 이 `&` 만으로 고치기를 맡는다 — 서로 모르는 두 도구의 조합이다(서머리 (8) `strong 3 · ["from a", "from b"]`).
- ★★ 스레드를 넘으면 **`Rc` → `Arc`**(41번의 E0277), **`RefCell` → `Mutex` 또는 `RwLock`**(6번의 E0277). 컴파일러와 std `cell` 문서는 **`RwLock`** 을 짝으로 댄다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(스레드 id 가 걸린다) · **고칠 것 0** |
| ★★★ **런타임 빌림 격자** | `r42_grid.sh` — 열두 소스를 만들어 컴파일·실행(탭 구분 · 칸 수 검사) | 12 컴파일 · 12 실행 | **`5 / 12`** |
| ★★ **`if let` 에디션 격자** | `r42_iflet.sh` — 두 소스 × 2021·2024 | 4 · 4 | **`3 / 4`** |
| 컴파일 대 런타임 | `r42_pair_ref` · `r42_pair_cell` · `r42_pair_cell_da` | 3 | **E0502** · `101` · `101`(같은 문구) |
| 문구의 출처 | `r42_msg` — std 소스 grep | 1 | 넷(둘은 `debug_refcell`) |
| `try_` · `Cell` · `!Sync` · 조합 | `r42_try` · `r42_cell` · `r42_cell_get` · `r42_sync` · `r42_sync_mutex` · `r42_rc_refcell` | 6 | `Err` · `hits 3` · **E0599** · **E0277** · `1` · `strong 3` |
| **안 던진 것** — 속도 · 크기 · `Ref::map` · `debug_refcell` 로 std 재빌드 · `RwLock` 판 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| 패닉 문구 · `BorrowMutError` 의 `Display` | ★ std 구현 — 판마다 바뀔 수 있다 |
| E0277 의 `= note:`(`use std::sync::RwLock instead`) | ★ rustc 진단의 제안 — 판에 매인다 |
| 종료 코드 `101` | ★ std 런타임의 관행 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
