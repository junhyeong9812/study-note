# rust/syntax/07 — 상수·`static`·`const fn` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **`const` 와 `static` 이 어디서 답을 갈라놓는지**를 맞힐 수 있는지 묻는다.
> ★ 답을 모르겠으면 **던져 보라.** `rustc --edition 2021 ex.rs -o /tmp/ex && /tmp/ex`.
> ★ **이 주제는 한 번 돌려서는 안 된다.** 디버그(`rustc --edition 2021 ex.rs`)와 릴리스(`rustc --edition 2021 -O ex.rs`)를
> 둘 다 돌리고, `static mut` 이 나오면 `--edition 2024` 로 한 번 더 돌린다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★ 같은 카운터를 `const` 와 `static` 에 두고 세 번 올리면 (예측)

```rust
use std::sync::atomic::{AtomicI32, Ordering};

const C_COUNT: AtomicI32 = AtomicI32::new(0);
static S_COUNT: AtomicI32 = AtomicI32::new(0);

fn main() {
    C_COUNT.fetch_add(1, Ordering::SeqCst);
    C_COUNT.fetch_add(1, Ordering::SeqCst);
    C_COUNT.fetch_add(1, Ordering::SeqCst);

    S_COUNT.fetch_add(1, Ordering::SeqCst);
    S_COUNT.fetch_add(1, Ordering::SeqCst);
    S_COUNT.fetch_add(1, Ordering::SeqCst);

    println!("const  세 번 올린 뒤 = {}", C_COUNT.load(Ordering::SeqCst));
    println!("static 세 번 올린 뒤 = {}", S_COUNT.load(Ordering::SeqCst));
}
```

- 두 줄에 각각 무엇이 찍히는가?
- 컴파일러는 무슨 말을 하는가 — 에러인가, 경고인가, 아무것도 없나?
- 릴리스 빌드에서는 달라지는가?
- `clippy` 를 돌리면 달라지는가 — 린트 이름은 무엇인가?

### 2. ★ 같은 항목을 두 번 읽었을 때 나는 해제 줄 (예측)

```rust
struct D(&'static str);
impl Drop for D {
    fn drop(&mut self) { println!("        [해제] {}", self.0); }
}

const  TEMPLATE: D = D("const");
static GLOBAL:   D = D("static");

fn main() {
    println!("(1) const 를 두 번 읽는다");
    println!("    {}", TEMPLATE.0);
    println!("    {}", TEMPLATE.0);

    println!("(2) static 을 두 번 읽는다");
    println!("    {}", GLOBAL.0);
    println!("    {}", GLOBAL.0);

    println!("(3) main 끝");
}
```

- `[해제]` 줄이 각각 몇 번, **어느 자리에** 찍히는가?
- `static` 쪽 값은 프로그램이 끝날 때 해제되는가?
- 그 사실을 규정한 문서 문장을 댈 수 있는가?
- 이 결과가 1번 결과와 같은 이야기인 이유를 한 문장으로 말할 수 있는가?

### 3. `const` 항목에 대입하면 (예측)

```rust
const BUF: [i32; 3] = [0, 0, 0];
fn main() {
    BUF[0] = 9;
    println!("{:?}", BUF);
}
```

- 컴파일되는가 — 에러인가 경고인가?
- 실행되면 무엇이 찍히는가?
- 진단의 `note` 한 줄은 무엇을 말하는가?
- 이것을 에러로 올리는 방법 둘은 무엇인가?

### 4. ★ `&CONST` 와 `&STATIC` 의 주소를 견주면 (예측)

```rust
const LIMIT: i32 = 100;
static TOTAL: i32 = 100;

#[inline(never)]
fn c_addr1() -> usize { &LIMIT as *const i32 as usize }
#[inline(never)]
fn c_addr2() -> usize { &LIMIT as *const i32 as usize }
#[inline(never)]
fn s_addr1() -> usize { &TOTAL as *const i32 as usize }
#[inline(never)]
fn s_addr2() -> usize { &TOTAL as *const i32 as usize }

fn main() {
    let (c1, c2, s1, s2) = (c_addr1(), c_addr2(), s_addr1(), s_addr2());
    println!("const  같은가? {}", c1 == c2);
    println!("static 같은가? {}", s1 == s2);
    println!("const 과 static 이 같은 주소인가? {}", c1 == s1);
}
```

- 세 줄에 각각 무엇이 찍히는가?
- **릴리스에서 달라지는 줄**이 있는가?
- 이 실험에서 **근거로 쓸 수 있는 칸과 쓸 수 없는 칸**은 각각 무엇인가?
- 그래서 「`const` 와 `static` 의 차이」를 주소로 설명해도 되는가?

### 5. ★ `static mut` 을 두 에디션에서 (예측)

```rust
static mut COUNTER: i32 = 0;

fn bump() {
    unsafe { COUNTER += 1; }
}

fn main() {
    bump(); bump(); bump();
    unsafe { println!("COUNTER = {}", COUNTER); }
    let r = unsafe { &COUNTER };
    println!("참조로 읽으면 = {}", r);
}
```

- `--edition 2021` 에서 어떻게 되는가 — 진단은 몇 개이고 등급은 무엇인가?
- `--edition 2024` 에서는 어떻게 되는가?
- `&` 를 한 번만 썼는데 진단이 둘인 이유는 무엇인가?
- 이 코드를 **두 에디션 모두에서 통과**시키려면 무엇을 바꾸는가?

### 6. `const fn` 은 어디까지 쓸 수 있나 (예측)

```rust
const fn square(n: usize) -> usize { n * n }

const SIDE: usize = 4;
const AREA: usize = square(SIDE);
static TABLE: [u8; square(3)] = [1; 9];

fn main() {
    let grid = [0u8; square(SIDE)];
    println!("AREA = {AREA} / grid.len() = {} / TABLE.len() = {}", grid.len(), TABLE.len());
    let n: usize = std::env::args().count();
    println!("런타임 호출 square({n}) = {}", square(n));
}
```

- 이 프로그램은 컴파일되는가? 무엇이 찍히는가?
- `const fn` 을 **보통 `fn`** 으로 바꾸면 어느 줄들이 깨지고 에러 번호는 무엇인가?
- `const fn` 몸통에 `println!` 을 넣으면 어떻게 되는가?
- 「`const fn` 으로 만들면 컴파일 타임에 계산된다」는 요약은 어디가 틀렸는가?

### 7. 같은 `const fn` 이 두 자리에서 0으로 나누면 (경계)

```rust
const fn div(a: i32, b: i32) -> i32 { a / b }

// (가) 상수 자리
const BAD: i32 = div(100, 0);

// (나) 런타임 자리
// let b = 0; println!("{}", div(100, b));
```

- (가)와 (나)는 각각 **어느 층에서** 실패하는가?
- 각각의 에러 번호·종료 코드는 무엇인가?
- 디버그와 릴리스에서 (나)의 결과가 달라지는가?
- 이 갈림을 규정한 문서 문장을 댈 수 있는가?

### 8. 타입 표기와 재정의 (경계)

```rust
const LIMIT = 100;
static TOTAL = 100;
```

```rust
const LIMIT: i32 = 100;
const LIMIT: i32 = 200;
```

- 위 두 묶음은 각각 무슨 에러를 내는가? 에러 번호가 붙는 쪽은 어디인가?
- `const` 와 `static` 의 `help` 문구는 어떻게 다른가?
- `let` 은 왜 타입을 안 적어도 되는가 — 무엇이 다른가?
- 재정의 에러의 `note` 는 **모듈**과 **블록** 중 무엇을 말하는가?

### 9. ★ 상수 이름을 `let` 으로 다시 묶으면 (경계)

```rust
const LIMIT: i32 = 100;
fn main() {
    let LIMIT = 300;
    println!("{LIMIT}");
}
```

- 컴파일되는가? 에러 번호는 무엇인가?
- 그 에러가 **패턴** 이야기를 하는 이유는 무엇인가?
- 안쪽 블록에 `const LIMIT: i32 = 200;` 을 새로 두는 것은 되는가 — 블록을 나오면 어느 값이 보이는가?
- [**02번 주제**](../02-bindings-mut-and-shadowing/)의 섀도잉과 무엇이 다른가?

### 10. `static` 에만 붙는 요구 (경계)

```rust
use std::cell::RefCell;
static CACHE: RefCell<i32> = RefCell::new(0);
```

```rust
use std::cell::RefCell;
const CACHE: RefCell<i32> = RefCell::new(0);
```

- 둘 중 컴파일되는 것은 어느 쪽인가? 안 되는 쪽의 에러 번호와 `note` 는?
- 왜 한쪽에만 그 요구가 붙는가?
- 통과하는 쪽이 **더 안전한가**?
- 이 대비가 1번 결과에 대해 말해 주는 것은 무엇인가?

### 11. `'static` 은 누구의 수명인가 (연결)

- `static TOTAL: i32 = 200;` 에 대해 `&TOTAL` 의 타입을 `&'static i32` 로 쓸 수 있는가?
- `const LIMIT: i32 = 100;` 에 대해 `&LIMIT` 는 어떤가 — 그 장치의 이름은 무엇인가?
- 지역 변수 `let local = 5;` 에 대해 `&local` 을 `&'static i32` 로 쓰면 어떻게 되는가?
- 수명 표기와 `&'static` 대 `T: 'static` 의 정본은 목록의 몇 번 주제인가?

### 12. 다른 주제와 잇기 (연결)

- 전역 카운터가 필요하면 무엇을 쓰는가 — 세 후보와 각각의 정본 주제 번호는?
- `static` 이 `Sync` 를 요구하는 이유의 정본은 목록의 몇 번 주제인가?
- 에디션 변경 전수를 다루는 주제는 몇 번인가?
- 해제 시점 일반론과 `Drop` 의 정본은 각각 어디인가?
- 이 주제에서 **`rustc` 는 침묵하고 다른 도구만 말하는** 자리는 어디였는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
