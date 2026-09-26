# rust/syntax/44 — `Drop` · `mem::drop` · `mem::replace`/`take` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`(패닉 전략 비교는 `-C panic=abort` 를 더한다). 격자는 `bash <파일>.sh`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **값을 보면 먼저 물어라** — 「**이 값에 이름이 붙었나(이동했나)**」와 「**그 이름의 블록은 어디서 끝나나**」.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 열두 문장 — `drop a` 는 어디서 (예측)

```bash
# r44_grid.sh
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
```

- 열두 행의 둘째 칸(`before <next statement>` · `at block end` · `never` 중 하나 — 섀도잉 행은 `drop b` 와의 앞뒤까지)을 채워라. 마지막 줄의 `N / 12` 는?

### 2. ★★★ 밑줄 하나와 밑줄 붙은 이름 (예측)

```rust
// r44_let_underscore.rs
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
```

```rust
// r44_let_named.rs
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
```

- 각각 컴파일되는가? 된다면 출력을, 안 된다면 에러 번호와 **어느 행을 짚는지**를 적어라.

### 3. ★★★ 정리 코드가 있는 타입의 필드 (예측)

```rust
// r44_e0509.rs
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
```

```rust
// r44_e0509_take.rs
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
```

- 앞 소스는 컴파일되는가? 에러라면 번호와 `help:` 둘은? 뒤 소스의 **두 줄** 출력은 — 특히 `drop job` 줄에는 무엇이 찍히나?

### 4. ★★ `&mut self` 에서 상태 넘기기 (예측)

```rust
// r44_state.rs
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
```

- 컴파일되는가? 에러라면 번호와 `help:` 는? 그 `help:` 를 따르면 **다음에** 무슨 에러가 나오나?

### 5. ★★ 패닉이 지나가는 두 프레임 (예측)

```rust
// r44_panic.rs
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
```

- 기본으로 빌드했을 때 표준 오류 전체와 종료 코드는? 같은 소스를 `-C panic=abort` 로 빌드하면 무엇이 달라지나?

### 6. ★★ 가드를 밑줄로 받기 — 락과 `RefCell` (예측)

```rust
// r44_lock.rs
use std::sync::Mutex;
fn main() {
    let m = Mutex::new(0);
    let _ = m.lock().unwrap();
    println!("{}", m.try_lock().is_ok());
}
```

```rust
// r44_refcell_guard.rs
use std::cell::RefCell;
fn main() {
    let c = RefCell::new(0);
    let _ = c.borrow_mut();
    println!("{}", c.try_borrow_mut().is_ok());
}
```

- 각각 컴파일되는가? 안 된다면 무엇이 막나(번호가 없다면 이름)? 된다면 출력은?

### 7. ★★ 잡히지 않은 예외와 패닉 (연결)

- 5번과 같은 모양을 C++ 로(`D` 의 소멸자가 표준 오류에 찍고, `inner` 가 `throw`, `main` 은 안 잡음) `g++ 13` 에서 돌리면 소멸자 줄이 찍히나? 표준은 그것을 어떻게 정하나? `try`/`catch` 로 잡으면?

### 8. ★★★ 소멸자를 안 부르는데 안전한 함수 (왜)

- `mem::forget(a)` 는 `unsafe` 블록 없이 불린다. 왜 그래도 되나 — std 의 §Safety 는 무엇을 근거로 드나? 「`drop` 이 불린다」와 「`drop` 이 반드시 불린다」는 각각 누가 보장하나?

### 9. ★★ 섀도잉과 대입 (경계)

- 1번의 `let x = D("a"); let x = D("b");` 와 `let mut x = D("a"); x = D("b");` 는 `a` 를 버리는 시점이 다르다. 각각 언제이고 왜 다른가?

### 10. ★★ 필드 순서 — Rust 와 C++ (연결)

- [09번 주제](../09-copy-clone-and-drop/) (6)은 Rust 구조체 필드가 **어느 순서로** 버려진다고 쟀나? C++ 갈래 [14번](../../../cpp/syntax/14-destructors-and-deterministic-destruction/2-summary.md) (1)의 멤버는? `Drop` 을 단 구조체에서 본체와 필드 중 무엇이 먼저인가 — 그것이 3번의 E0509 와 어떻게 이어지나?

### 11. ★ 자리에 무엇을 남기나 (경계)

- `mem::take` · `mem::replace` · `Option::take` 는 각각 자리에 무엇을 남기고 무엇을 요구하나? 4번을 `take` 가 아니라 `replace` 로 푼 이유는? 그 대가로 타입에 무엇이 생기나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
