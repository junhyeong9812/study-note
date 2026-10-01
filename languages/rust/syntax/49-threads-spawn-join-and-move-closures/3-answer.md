# rust/syntax/49 — 스레드 `spawn`/`join` 과 `move` 클로저 — 정답

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `7 / 13` — `move` 가 필요 없는 칸도, `move` 로 안 되는 칸도 있다

**출력**

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

**왜 그런가**

- ★★ 1·5행 **E0373** — 클로저가 `v`·`a` 를 **빌림으로** 잡았고 `spawn` 은 `'static` 을 요구한다. `Arc` 도 `move` 없이는 빌림이다(5행).
- ★★ 3행 **E0382** — `move` 로 `v` 가 스레드로 갔으니 main 에는 없다. 4행처럼 **복제본을 옮기면** 둘 다 쓴다.
- ★★★ 6행 — **`move` 없이 통과.** `s: &'static str` 이면 2021 캡처가 `*s` 자리에서 잘려 `'static` 참조를 잡는다(2번).
- ★★★ **2행 대 9행** — 2행은 **값 `v`** 를 옮겼고, 9행은 **참조 `r = &v`** 를 옮겼다. 옮긴 참조가 가리키는 `v` 는 여전히 main 의 지역 변수라 **E0597**(3번).
- ★★★ 10\~13행 — `thread::scope` 안에서는 빌림이 되고, **빌림 규칙은 그대로다** — 가변 둘 **E0499**, 공유+가변 **E0502**.

### 2. ★★ 2018 은 E0373, 2021·2024 는 `3` — 2021 캡처가 공유 참조 역참조에서 잘린다

**출력**

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

**왜 그런가**

- ★★ **2018** — 클로저가 **변수 `s` 를 통째로** 빌린다(`&s`, main 의 지역 변수를 가리킨다) → E0373.
- ★★★ **2021·2024** — 클로저는 쓴 자리 `*s` 를 잡는데, Reference 「**Rightmost shared reference truncation**」(`[type.closure.capture.precision.dereference-shared]`)이 공유 참조의 역참조에서 경로를 자른다. 그 결과 잡힌 것은 `&'static str` 을 다시 빌린 **`'static` 참조** — `spawn` 의 요구를 만족한다. Reference 의 이유는 「필요 이상으로 짧은 수명을 피하려고」다.

### 3. ★★ E0597 — `v` 를 `'static` 동안 빌려야 한다는 요구

**출력**

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

**왜 그런가**

- ★★★ 표지 「**argument requires that `v` is borrowed for `'static`**」 — `r` 을 스레드로 옮겼지만 `r` 이 가리키는 `v` 는 8행 `}` 에서 버려진다(「dropped here while still borrowed」).
- ★ `note:` 가 요구의 출처를 std `thread/mod.rs` 로 짚는다 — `spawn` 시그니처의 `'static` 이다. **`move` 는 수명을 늘리지 않는다.**

### 4. ★★★ 표준 출력 다섯 줄 전부 · 표준 오류에 패닉 둘 · `exit 0` — `String` 과 `&str`

**출력**

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

**왜 그런가**

- ★★★ **자식의 패닉은 `join` 의 `Err` 가 된다** — main 은 `[5]` 까지 돌고 종료 코드 `0`. 표준 오류의 두 덩어리는 **자식 스레드 둘**의 패닉 메시지다(`thread '<unnamed>'` — 이름 없는 스레드).
- ★★ `[1]` 정상 종료 → `Ok(42)`. 반환값이 `join` 으로 돌아온다.
- ★★★ `[3]` 인덱스 범위 밖 패닉은 메시지를 **포맷해 만들어서 `String`**, `[4]` `panic!("fixed text")` 는 **리터럴 그대로라 `&str`**. `downcast_ref` 는 타입을 맞혀야 꺼내진다.

### 5. ★★ `0 / 20` 과 `20 / 20` — 보장이 아니라 시간 여유의 관찰

**출력**

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

**왜 그런가**

- ★★★ **0ms** — main 이 자식(50ms 잠)보다 먼저 끝나 **20판 전부에서 자식 줄이 없다.** std 모듈 문서: 「main 스레드가 끝나면 다른 스레드가 돌고 있어도 프로그램 전체가 끝난다」.
- ★★ **300ms** — 여유가 있어 20판 전부 찍혔다.
- ★★★ **보장이 아니다** — 순서를 정한 것은 `sleep` 의 시계지 동기화가 아니다. 반드시 찍혀야 하면 `join` 하거나 `thread::scope` 를 쓴다. 이 칸은 서머리 맨 위 부분에 **흔들릴 수 있는 칸**으로 선언했다.

### 6. ★★★ `end of scope closure` → `pushed` → `after scope` · `[1, 2, 3, 6]`

**출력**

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

**왜 그런가**

- ★★★ 스코프 **클로저**가 먼저 끝나 `[main] end of scope closure` 가 찍히지만, **`thread::scope` 함수는 자식을 join 한 뒤에야** 돌아온다 — 그래서 100ms 잔 자식의 `[child] pushed` 가 `[main] after scope` 보다 앞선다.
- ★★ 자식은 `v` 를 **가변 빌림**으로, `total` 을 공유 빌림으로 잡았다. 스코프 스레드는 `'static` 이 아니라 **`'scope`** 만 요구하므로 스코프 밖 지역 변수의 빌림이면 된다. `v` 는 `1+2+3 = 6` 이 붙어 `[1, 2, 3, 6]`.

### 7. ★★★ `F: FnOnce() -> T + Send + 'static`, `T: Send + 'static` — 스레드가 만든 함수보다 오래 살 수 있어서

- ★★ std `spawn` 의 「`'static` 제약」 절 — 「**클로저와 그 반환값은 프로그램 실행 전체만큼의 수명을 가져야 한다.** 스레드는 자기가 만들어진 수명보다 **오래 살 수 있기** 때문이다」. 언제 끝날지 모르므로 끝까지 유효해야 한다.
- ★★★ **`move` 가 맞추는 것** — 빌림으로 잡힐 값을 **소유로 옮겨** 클로저가 지역 참조를 품지 않게 한다(1번 2행).
- ★★★ **못 맞추는 것** — 옮긴 것이 **참조**면 그 참조의 대상 수명은 그대로다(3번 E0597). 반환값 `T` 도 같은 경계라 **지역을 빌린 값을 돌려줄 수도 없다.**
- ★ `Send` 쪽 절반은 [50번 주제](../50-send-sync-in-compiler-errors/)의 몫이다.

### 8. ★★★ `'scope` 만 요구 · 대가는 「스코프 끝에서 전부 join」 · 가변 둘이면 E0499(12행)

- ★★★ std `scope`: 「스코프 안에서 만든 스레드 중 직접 join 하지 않은 것은 **이 함수가 돌아오기 전에 자동으로 join 된다**」 — 그래서 클로저는 **스코프보다 오래 사는 빌림**이면 된다(`'static` 불필요).
- ★★ **안 푸는 것 — 빌림 규칙.** 두 스코프 스레드가 같은 `Vec` 을 가변으로 빌리면 한 함수 안의 두 `&mut` 과 같이 **E0499**(1번 12행), 공유+가변은 **E0502**(13행). 여럿이 고치려면 [52번 주제](../52-mutex-rwlock-arc-and-poisoning/)의 `Mutex`.

### 9. ★★ `spawn` 은 `Err` 로, `scope` 는 main 의 패닉으로 — 직접 `join()` 하면 `Result`

- ★★ **`spawn`** — 패닉은 스레드 경계에서 멈춰 `join()` 의 **`Err(패닉 값)`** 이 된다(4번). main 은 계속 돈다.
- ★★★ **`scope`** — std §Panics: 「자동으로 join 된 스레드 중 하나라도 패닉했으면 **이 함수가 패닉한다**」. 서머리 (5)의 `r49_scope_panic` 에서 표준 오류에 자식 패닉 다음 **`thread 'main'` 의 `a scoped thread panicked`** 가 찍혔다.
- ★ **받고 싶으면** 스코프 안에서 `s.spawn(…)` 의 핸들을 **직접 `join()`** 해 `Result` 를 받는다 — 직접 join 한 스레드는 자동 join 대상이 아니다.

### 10. ★★ 버리면 detach · main 이 끝나면 프로그램째 끝난다 · 판 수는 「찍혔나」만 본다

- ★★ std `JoinHandle`: 「**버려질 때 연관된 스레드를 detach 한다** — 더 이상 그 스레드를 join 할 방법이 없다」. `let _ = thread::spawn(…)` 은 그 문장 끝에 핸들을 버린다([44번 주제](../44-drop-mem-drop-replace-and-take/)의 `let _`).
- ★★★ std 모듈 문서: 「main 스레드가 끝나면 **다른 스레드가 돌고 있어도 프로그램 전체가 끝난다**」 — 도는 스레드는 **정리 없이** 사라진다.
- ★ 판 수 창이 **못 보는 것** — 자식이 출력 전에 하던 **반쯤 된 부작용**(파일을 반만 썼는지 등). 「찍혔나」만 센다(서머리 (0)의 제5의 상태).

### 11. ★ `Arc` 복제본을 `move` 하거나 `thread::scope` — `Rc` 는 `Send` 경계에서 E0277

- ★★ **방법 하나** — `let b = Arc::clone(&a);` 후 `move || b.len()`(1번 4행 `stdout: 3 3`). **방법 둘** — `thread::scope` 안에서 빌림(1번 10행 `stdout: 3 3`) — 복제도 없다.
- ★★ [41번 주제](../41-rc-arc-shared-ownership-and-weak-cycles/) (3) — `Rc` 복제본을 `move` 하면 **E0277** 「`Rc<String>` cannot be sent between threads safely」. 이것은 `'static` 이 아니라 **`F: Send`** 경계에서 온다 — `Rc` 는 `'static` 이지만 `Send` 가 아니다. 그 절반의 정본은 [50번 주제](../50-send-sync-in-compiler-errors/)다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` 기본 규칙 넷(스레드 id 가 걸린다) · **고칠 것 0** |
| ★★★ **`move` 필요 격자** | `r49_grid.sh` — 열세 소스를 만들어 컴파일(통과하면 실행) · `\x1f` 구분 · 칸 수 검사 | 13 컴파일 · 7 실행 | **`7 / 13`** |
| ★★ **에디션 탐침** | `r49_static_str_ed.sh` — 한 소스 × 2018·2021·2024 | 3 | **E0373 · 통과 · 통과** |
| E0597 | `r49_e0597` | 1 | **E0597** |
| `join` 의 `Result` | `r49_join` — 두 스트림을 갈라 받음 | 1 | `Ok(42)` · `Err` · `String` / `&str` · `exit 0` |
| ★ **detach 판 수** | `r49_detach.sh` — 대기 0ms·300ms × 20판 | 40 | **`0 / 20` · `20 / 20`** — 흔들릴 수 있는 칸 |
| id · 이름 | `r49_ids` | 1 | `false` · `true` · `main` · `None` · `worker-1` |
| `scope` 순서 · 패닉 | `r49_scope` · `r49_scope_panic` | 2 | 순서 로그 · `a scoped thread panicked` |
| **안 던진 것** — 스레드 생성 비용 · `stack_size` · `is_finished` · 이름 준 스레드의 패닉 메시지 | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| detach 판 수(`0 / 20` · `20 / 20`) | ★ 시간 여유와 OS 스케줄링 — 머신이 느리거나 바쁘면 움직일 수 있다 |
| 패닉 값의 타입(`String` / `&str`) | ★ std 패닉 기계의 관찰 |
| 무명 스레드의 `<unnamed>` 표기 · 패닉 문구 | ★ std 구현 |
| E0373·E0597 의 `note:` 가 가리키는 std 소스 줄 번호 | ★ 판마다 바뀐다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.

## 실행 환경

이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
**`rustc --edition 2021`** 로(에디션 탐침은 2018·2021·2024) 실제로 돌려 받은 것이다.\
★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **돌린 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
★ 패닉 첫 줄의 `thread '<unnamed>' (NNN)` 은 **실행마다 바뀌는 칸**이고, 5번의 판 수는 **시간 여유에 기대는 칸**이다(서머리 맨 위 부분의 표).
