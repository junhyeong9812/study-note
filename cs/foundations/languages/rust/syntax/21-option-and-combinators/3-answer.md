# rust/syntax/21 — `Option` 과 조합 메서드 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ 패닉 첫 줄의 `thread 'main' (…)` 괄호 안 숫자는 **실행마다 다른 OS 스레드 id** 다 — 대조할 칸이 아니다.\
> ★ `rustc --explain E0382` · `E0507` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ E0382 — `map` 이 봉투를 가져갔다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// map 은 self 를 소비한다 — 뒤에서 원본을 다시 쓰면
fn main() {
    let name: Option<String> = Some(String::from("postgres"));
    let len = name.map(|s| s.len());
    println!("길이 {:?}", len);
    println!("원본 {:?}", name);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `name`
 --> ex.rs:7:25
  |
4 |     let name: Option<String> = Some(String::from("postgres"));
  |         ---- move occurs because `name` has type `Option<String>`, which does not implement the `Copy` trait
5 |     let len = name.map(|s| s.len());
  |               ---- ---------------- `name` moved due to this method call
  |               |
  |               help: consider calling `.as_ref()` or `.as_mut()` to borrow the type's contents
6 |     println!("길이 {:?}", len);
7 |     println!("원본 {:?}", name);
  |                           ^^^^ value borrowed here after move
  |
note: `Option::<T>::map` takes ownership of the receiver `self`, which moves `name`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/option.rs:1159:28
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: you can `clone` the value and consume it, but this might not be your desired behavior
  |
5 |     let len = name.clone().map(|s| s.len());
  |                   ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
(종료 코드 1)
```

**왜 그런가**

- **`Option::map` 의 첫 인자는 `self` 다.** 값으로 받으므로 호출하는 순간 `name` 의 소유권이 넘어간다.
  `Option<String>` 은 `Copy` 가 아니므로 **복사가 아니라 이동**이다([**08번 주제**](../08-ownership-and-move/)).
- 진단이 범인으로 가리키는 곳은 **`println!` 줄(7:25)** 이다 — 「이동한 뒤에 빌렸다」는 것이 에러이므로
  **에러 지점은 나중에 쓴 자리**다. 이동한 자리(5줄)는 `---- ----------------` 로 **보조 표시**된다.
- ★★ 인용되는 것은 이 한 줄이다 — `` note: `Option::<T>::map` takes ownership of the receiver `self`, which moves `name` ``.
  **시그니처를 안 열어 봐도 컴파일러가 소유권 성질을 이름까지 대며 말해 준다.**
- `help` 가 둘인 이유 —
  - `` consider calling `.as_ref()` or `.as_mut()` to borrow the type's contents `` — **제대로 된 처방**이다.
  - `` you can `clone` the value and consume it, but this might not be your desired behavior `` —
    ★ 뒤에 **「원하는 동작이 아닐 수 있다」가 붙어 있다.** 컴파일러도 `clone` 이 회피책임을 안다.
- ★ **`Option<u16>` 이었으면 에러가 안 난다.** `u16` 은 `Copy` 이고 `Option<T: Copy>` 도 `Copy` 라
  `map` 에 넘어가는 것이 **복사본**이기 때문이다([**09번 주제**](../09-copy-clone-and-drop/)).
  **같은 메서드가 타입에 따라 되고 안 되는 것**이 이 함정의 정체다.

### 2. ★★ E0507 — 남의 봉투는 애초에 옮길 수가 없다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 빌린 Option 안에서 값을 꺼내려 하면 — as_ref 가 없는 판
fn describe(cfg: &Option<String>) -> usize {
    match cfg {
        Some(s) => s.len(),
        None => 0,
    }
}

fn wrong(cfg: &Option<String>) -> Option<usize> {
    cfg.map(|s| s.len())
}

fn main() {
    let cfg = Some(String::from("postgres"));
    println!("{} {:?}", describe(&cfg), wrong(&cfg));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0507]: cannot move out of `*cfg` which is behind a shared reference
  --> ex.rs:11:5
   |
11 |     cfg.map(|s| s.len())
   |     ^^^ ---------------- `*cfg` moved due to this method call
   |     |
   |     help: consider calling `.as_ref()` or `.as_mut()` to borrow the type's contents
   |     move occurs because `*cfg` has type `Option<String>`, which does not implement the `Copy` trait
   |
note: `Option::<T>::map` takes ownership of the receiver `self`, which moves `*cfg`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/option.rs:1159:28
help: you can `clone` the value and consume it, but this might not be your desired behavior
   |
11 |     <Option<String> as Clone>::clone(&cfg).map(|s| s.len())
   |     ++++++++++++++++++++++++++++++++++   +
help: consider cloning the value if the performance cost is acceptable
   |
11 |     cfg.clone().map(|s| s.len())
   |        ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
(종료 코드 1)
```

**왜 그런가**

- 거부된 것은 **`wrong` 쪽뿐**이다. `describe` 는 통과한다.
- ★ 번호가 다르다 — 1번은 **E0382**(내 것을 이미 넘겼다), 이쪽은 **E0507**(남의 것이라 넘길 수가 없다).
  `cannot move out of *cfg which is behind a shared reference` 가 그 문장이다.
  ★ **상황이 다르다**: 앞엣것은 *순서* 문제(뒤에서 쓰지만 않으면 된다), 이쪽은 *권한* 문제(순서와 무관하게 안 된다).
- ★★ `match cfg` 가 통과하는 이유는 **매치 인체공학** 때문이다 — 매치 대상이 참조면 바인딩에 자동으로 `&` 가 붙어
  `s` 가 `&String` 이 된다([**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)). **아무것도 옮기지 않는다.**
  반면 `map` 은 **메서드 호출**이라 그 규칙이 없고, `self` 를 요구한다.
- 처방은 `.as_ref()` 다. 붙이면 `cfg.as_ref()` 가 `Option<&String>` 이 되고 `map` 이 그것을 소비해도
  **원본 봉투는 건드리지 않는다.** 반환 타입은 그대로 `Option<usize>` 다(8번 답의 블록이 그 판이다).

### 3. ★★ 네 번 중 세 번 — `unwrap_or` 는 있어도 계산한다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// unwrap_or 와 unwrap_or_else — 언제 대체값을 만드나. 부작용으로 증명한다
fn fallback() -> u16 {
    println!("  [부작용] fallback() 이 돌았다");
    9999
}

fn main() {
    let found: Option<u16> = Some(443);
    let missing: Option<u16> = None;

    println!("A 있음 + unwrap_or(fallback())");
    println!("  결과 {}", found.unwrap_or(fallback()));

    println!("B 있음 + unwrap_or_else(fallback)");
    println!("  결과 {}", found.unwrap_or_else(fallback));

    println!("C 없음 + unwrap_or(fallback())");
    println!("  결과 {}", missing.unwrap_or(fallback()));

    println!("D 없음 + unwrap_or_else(fallback)");
    println!("  결과 {}", missing.unwrap_or_else(fallback));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
A 있음 + unwrap_or(fallback())
  [부작용] fallback() 이 돌았다
  결과 443
B 있음 + unwrap_or_else(fallback)
  결과 443
C 없음 + unwrap_or(fallback())
  [부작용] fallback() 이 돌았다
  결과 9999
D 없음 + unwrap_or_else(fallback)
  [부작용] fallback() 이 돌았다
  결과 9999
(종료 코드 0)
```

**왜 그런가**

- `[부작용]` 은 **세 번** 찍힌다 — **A·C·D** 다. **B 에서는 안 찍힌다.**
- ★★★ **A 가 결론이다.** `found` 는 `Some(443)` 인데도 `fallback()` 이 돌았다.
  `unwrap_or(fallback())` 은 **보통의 함수 호출**이라 인자가 **먼저 계산되어** `unwrap_or` 에 넘어간다.
  「없을 때만 쓰는 값」이 아니라 「**이미 만들어 두고 안 쓸 수도 있는 값**」이다.
- B 는 `unwrap_or_else(fallback)` 이다. **함수 자체**를 넘기므로 `None` 일 때만 호출된다 — 그래서 조용하다.
- ★ 그러므로 대체값이 **문자열 할당**(`String::from("기본")`)이면 `unwrap_or_else(|| String::from("기본"))` 라야 한다.
  할당은 부작용이 안 보일 뿐 **매번 실제로 일어난다**.
- 같은 규칙의 쌍 — **`or`/`or_else` · `ok_or`/`ok_or_else` · `map_or`/`map_or_else`**.
  ★ **`_else` 가 붙은 쪽은 전부 게으르다**는 한 문장으로 외운다.

### 4. ★ `?` 는 `Option` 에서도 된다 — 함수가 `Option` 을 돌려줄 때만

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// ? 는 Option 에서도 된다 — None 이면 그 자리에서 None 을 반환한다
fn first_word(s: &str) -> Option<&str> {
    let head = s.split_whitespace().next()?;
    let first = head.get(0..1)?;
    Some(first)
}

fn both(a: &str, b: &str) -> Option<String> {
    let x = first_word(a)?;
    let y = first_word(b)?;
    Some(format!("{}{}", x, y))
}

fn main() {
    println!("{:?}", both("alpha beta", "gamma"));
    println!("{:?}", both("alpha beta", "   "));
    println!("{:?}", both("", "gamma"));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Some("ag")
None
None
(종료 코드 0)
```

**왜 그런가**

- 첫 줄은 `Some("ag")` 다 — `"alpha beta"` 의 첫 낱말 `"alpha"` 의 첫 글자 `"a"`, `"gamma"` 의 `"g"`.
- ★ `both("alpha beta", "   ")` 이 `None` 인 이유 — 공백뿐인 문자열은 `split_whitespace()` 가 **아무것도 내지 않아서**
  `next()` 가 `None` 이고, `?` 가 그 자리에서 함수를 끝낸다. `both("", "gamma")` 도 같은 이유로 `None` 이다.
- ★★ **조건은 하나다 — 함수의 반환 타입도 `Option` 이라야 한다.**
  `?` 는 「실패를 함수 밖으로 던진다」인데, **던질 곳(반환 타입)이 같은 세계라야** 한다.
- 반환 타입을 `Result<…>` 로 바꾸면 **컴파일이 거부한다** —
  `` the `?` operator can only be used on `Result`s, not `Option`s, in a function that returns `Result` ``.
  ★ 그 진단 전문은 [**22번 주제**](../22-result-question-mark-and-from/) 5번 답에 실려 있다.
- `and_then` 으로 쓰면 `first_word(a).and_then(|x| first_word(b).map(|y| format!("{}{}", x, y)))` 처럼
  **중첩이 생긴다.** `?` 는 그것을 평평하게 편다.

### 5. ★ 종료 코드 101 — `unwrap` 과 `expect` 는 문장만 다르다

**출력** — `unwrap` 판.

```text
===== 소스: ex.rs =====
// ex.rs
// unwrap 이 None 을 만나면 — 마커는 전부 표준 오류로 찍는다
fn find(v: &[i32], t: i32) -> Option<usize> {
    v.iter().position(|&x| x == t)
}

fn main() {
    let table = [10, 20, 30];
    eprintln!("찾음 {:?}", find(&table, 20));
    let i = find(&table, 99).unwrap();
    eprintln!("여기는 안 온다 {}", i);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
찾음 Some(1)

thread 'main' (868950) panicked at ex.rs:10:30:
called `Option::unwrap()` on a `None` value
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**같은 자리, `expect` 판.**

```text
===== 소스: ex.rs =====
// ex.rs
// expect 는 같은 자리에서 「무엇이 깨졌나」를 적는다
fn find(v: &[i32], t: i32) -> Option<usize> {
    v.iter().position(|&x| x == t)
}

fn main() {
    let table = [10, 20, 30];
    eprintln!("찾음 {:?}", find(&table, 20));
    let i = find(&table, 99).expect("표에는 99 가 반드시 들어 있어야 한다 — 표 생성기가 깨졌다");
    eprintln!("여기는 안 온다 {}", i);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
찾음 Some(1)

thread 'main' (869055) panicked at ex.rs:10:30:
표에는 99 가 반드시 들어 있어야 한다 — 표 생성기가 깨졌다
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**왜 그런가**

- **종료 코드는 둘 다 101** 이다. 패닉으로 끝난 프로세스의 고정 코드이고,
  `std::process::exit` 로 내가 정하는 코드와는 다른 경로다([**23번 주제**](../23-panic-vs-result/)).
- 메시지 본문 —
  - `unwrap` — `` called `Option::unwrap()` on a `None` value `` (std 가 정한 문장).
  - `expect` — `표에는 99 가 반드시 들어 있어야 한다 — 표 생성기가 깨졌다` (내가 적은 문장).
- `note:` 줄은 둘 다 `` note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace `` 다.
- ★★ **달라지는 것은 메시지 한 줄뿐**이다. `파일:줄:칸`(`ex.rs:10:30`)도, `note:` 줄도, 종료 코드도 같다.
  그래서 `expect` 는 **비용 없이 정보를 더하는 것**이다 — 「무엇이 깨졌길래 여기 왔나」를 적는 자리다.
- ★ 마커를 `eprintln!` 으로 찍은 이유 — **패닉은 표준 오류로 나간다.** 표준 출력과 섞으면
  터미널에서 본 순서와 파이프로 받은 순서가 갈릴 수 있다. **한 블록 안에서는 한쪽 스트림으로 통일한다.**

### 6. ★ `take` 는 빈 봉투를 두고 물건만 가져온다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// take 와 replace — 빌린 자리에서 소유권을 꺼내는 두 가지
#[derive(Debug)]
struct Slot {
    payload: Option<String>,
}

impl Slot {
    fn consume(&mut self) -> Option<String> {
        self.payload.take()
    }
    fn swap(&mut self, next: &str) -> Option<String> {
        self.payload.replace(String::from(next))
    }
}

fn main() {
    let mut slot = Slot { payload: Some(String::from("첫 짐")) };
    println!("처음      {:?}", slot);

    let old = slot.swap("둘째 짐");
    println!("replace 뒤 {:?} · 돌려받은 것 {:?}", slot, old);

    let got = slot.consume();
    println!("take 뒤    {:?} · 꺼낸 것 {:?}", slot, got);

    let again = slot.consume();
    println!("또 take    {:?} · 꺼낸 것 {:?}", slot, again);

    println!("get_or_insert {:?}", slot.payload.get_or_insert(String::from("기본값")));
    println!("끝        {:?}", slot);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
처음      Slot { payload: Some("첫 짐") }
replace 뒤 Slot { payload: Some("둘째 짐") } · 돌려받은 것 Some("첫 짐")
take 뒤    Slot { payload: None } · 꺼낸 것 Some("둘째 짐")
또 take    Slot { payload: None } · 꺼낸 것 None
get_or_insert "기본값"
끝        Slot { payload: Some("기본값") }
(종료 코드 0)
```

**왜 그런가**

- ★★ `take()` 를 두 번 부르면 두 번째는 **`None`** 이다. 첫 번째가 그 자리에 `None` 을 **두고** 갔기 때문이다.
  출력의 `take 뒤    Slot { payload: None }` 이 그 증거다.
- `replace("둘째 짐")` 은 **옛 값** `Some("첫 짐")` 을 돌려준다. 새 값은 그 자리에 들어간다.
  ★ `take()` 는 **`replace(None)` 의 특수형**으로 읽으면 외울 것이 하나 준다.
- `get_or_insert` 는 **비어 있을 때만** 채우고, 어느 쪽이든 **안쪽에 대한 `&mut`** 를 돌려준다.
  마지막 줄에서 `payload` 가 `Some("기본값")` 이 된 것이 그것이다.
- ★ 이 셋이 없으면 `&mut self` 메서드 안에서 **필드를 통째로 옮길 수 없어** 막힌다 —
  `self.payload` 를 `map` 에 넘기려는 순간 「빌린 것 뒤에서 옮길 수 없다」가 된다([**11번 주제**](../11-borrow-checker-rejections/)).
  일반화한 도구는 `std::mem::take`/`std::mem::replace` 이고 정본은 목록의 **44번 주제**다.

### 7. `None` 은 대부분 그대로 통과한다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 조합 메서드 한 바퀴 — 같은 입력 둘(있음·없음)에 전부 걸어 본다
fn port_of(name: &str) -> Option<u16> {
    match name {
        "http" => Some(80),
        "https" => Some(443),
        _ => None,
    }
}

fn label(p: u16) -> Option<&'static str> {
    if p < 1024 { Some("well-known") } else { None }
}

fn show(name: &str) {
    let p = port_of(name);
    println!("입력 {:?}  ->  {:?}", name, p);
    println!("  map(|x| x * 2)        {:?}", p.map(|x| x * 2));
    println!("  and_then(label)       {:?}", p.and_then(label));
    println!("  filter(|x| *x < 100)  {:?}", p.filter(|x| *x < 100));
    println!("  ok_or(\"없다\")          {:?}", p.ok_or("없다"));
    println!("  unwrap_or(0)          {:?}", p.unwrap_or(0));
    println!("  unwrap_or_default()   {:?}", p.unwrap_or_default());
    println!("  is_some/is_none       {} {}", p.is_some(), p.is_none());
}

fn main() {
    show("https");
    show("gopher");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
입력 "https"  ->  Some(443)
  map(|x| x * 2)        Some(886)
  and_then(label)       Some("well-known")
  filter(|x| *x < 100)  None
  ok_or("없다")          Ok(443)
  unwrap_or(0)          443
  unwrap_or_default()   443
  is_some/is_none       true false
입력 "gopher"  ->  None
  map(|x| x * 2)        None
  and_then(label)       None
  filter(|x| *x < 100)  None
  ok_or("없다")          Err("없다")
  unwrap_or(0)          0
  unwrap_or_default()   0
  is_some/is_none       false true
(종료 코드 0)
```

**왜 그런가**

- ★ **`None` 에서는 클로저가 아예 호출되지 않는다.** `map`·`and_then`·`filter` 의 `None` 줄이 전부 `None` 인 것이 그 결과다.
  「빈 봉투에는 할 일이 없다」가 `Option` 조합 메서드의 기본 규칙이다.
- **`map` 과 `and_then` 의 기준** — **클로저가 `Option` 을 돌려주면 `and_then`, 아니면 `map`이다.**
  `and_then(label)` 을 `map(label)` 로 했으면 `Option<Option<&str>>` 이 나왔을 것이다.
- ★ **`filter` 는 `Some` 을 `None` 으로 떨어뜨릴 수 있다.** `Some(443).filter(|x| *x < 100)` 이 `None` 이다.
  반대 방향(`None` → `Some`)은 못 한다 — 그쪽은 `or`/`or_else` 다.
- **`ok_or` 는 `Option<T>` 를 `Result<T, E>` 로** 바꾼다. 출력에서 `Ok(443)` 과 `Err("없다")` 로 갈린 것이 그것이고,
  이어지는 주제는 [**22번**](../22-result-question-mark-and-from/)이다.
- `unwrap_or_default()` 는 **`T: Default`** 를 요구한다. `u16` 의 기본값이 `0` 이라 `unwrap_or(0)` 과 같은 답이 나왔다.

### 8. `as_ref` 는 「봉투는 두고 안쪽만 빌린 새 봉투」다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// as_ref 와 as_mut — 봉투는 빌린 채로 안쪽만 빌린다
fn right(cfg: &Option<String>) -> Option<usize> {
    cfg.as_ref().map(|s| s.len())
}

fn main() {
    let mut cfg = Some(String::from("postgres"));
    println!("as_ref  {:?}", right(&cfg));
    println!("원본 그대로 {:?}", cfg);

    if let Some(s) = cfg.as_mut() {
        s.push_str("ql");
    }
    println!("as_mut 뒤 {:?}", cfg);

    let borrowed: Option<&String> = cfg.as_ref();
    println!("as_ref 의 타입은 Option<&String> {:?}", borrowed);
    let copied: Option<usize> = cfg.as_ref().map(|s| s.len());
    println!("길이 {:?} · 원본 살아 있음 {:?}", copied, cfg);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
as_ref  Some(8)
원본 그대로 Some("postgres")
as_mut 뒤 Some("postgresql")
as_ref 의 타입은 Option<&String> Some("postgresql")
길이 Some(10) · 원본 살아 있음 Some("postgresql")
(종료 코드 0)
```

**왜 그런가**

- ★★ **`&Option<String>` 과 `Option<&String>` 은 다른 타입이다.**
  앞엣것은 「봉투에 대한 참조」이고 뒤엣것은 「참조를 담은 봉투」다. **조합 메서드가 먹는 쪽은 뒤엣것**이고,
  그 변환을 해 주는 것이 `as_ref()` 다.
- **원본은 살아 있다.** `as_ref().map(…)` 을 세 번 걸고도 마지막 줄에서 `cfg` 가 `Some("postgresql")` 로 찍힌다.
- **`as_mut()` 으로만 되는 일** — 안쪽 값을 **고치는 것**이다. `Option<&mut String>` 이라 `push_str` 이 먹는다
  (출력의 `as_mut 뒤 Some("postgresql")`).
- `as_ref().map(…)` 의 결과에서 `Option<T>` 를 얻으려면 **`copied()`**(`T: Copy`) 또는 **`cloned()`**(`T: Clone`)를 붙인다.
- ★ 시그니처에서 볼 곳은 **첫 인자 하나**다 — `self` 면 가져가고, `&self`/`&mut self` 면 빌린다.
  `map(self, …)` · `as_ref(&self)` · `take(&mut self)` 가 그 세 꼴이다.

### 9. 넷이 한 글자도 같은 답을 낸다 — 그러니 읽기 쉬움으로 고른다

**출력.**

```text
===== 소스: ex.rs =====
// ex.rs
// 같은 일을 네 가지로 — if let · match · 조합 메서드 · let else
fn port_of(name: &str) -> Option<u16> {
    if name == "https" { Some(443) } else { None }
}

fn by_if_let(name: &str) -> String {
    if let Some(p) = port_of(name) {
        format!("{}:{}", name, p)
    } else {
        format!("{}:알수없음", name)
    }
}

fn by_match(name: &str) -> String {
    match port_of(name) {
        Some(p) => format!("{}:{}", name, p),
        None => format!("{}:알수없음", name),
    }
}

fn by_combinator(name: &str) -> String {
    port_of(name)
        .map(|p| format!("{}:{}", name, p))
        .unwrap_or_else(|| format!("{}:알수없음", name))
}

fn by_let_else(name: &str) -> String {
    let Some(p) = port_of(name) else {
        return format!("{}:알수없음", name);
    };
    format!("{}:{}", name, p)
}

fn main() {
    for n in ["https", "gopher"] {
        println!("{} | {} | {} | {}",
                 by_if_let(n), by_match(n), by_combinator(n), by_let_else(n));
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
https:443 | https:443 | https:443 | https:443
gopher:알수없음 | gopher:알수없음 | gopher:알수없음 | gopher:알수없음
(종료 코드 0)
```

**왜 그런가**

- 네 판(`if let` · `match` · 조합 메서드 · `let else`)이 **같은 문자열**을 냈다. 정답이 하나가 아니라는 뜻이다.
- 고르는 기준 —
  - **값이 한 줄기로 이어진다** → 조합 메서드. `map(...).unwrap_or_else(...)` 가 한 식으로 끝난다.
  - **갈래마다 할 일이 다르다** → `match`. 갈래가 늘어날 여지가 있으면 더욱 그렇다([**18번 주제**](../18-match-and-exhaustiveness/)).
  - **실패하면 나가야 한다** → `let else`. 성공 경로가 평평하게 남는다([**20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).
  - **한 갈래만 보고 지나간다** → `if let`.
- ★ **체인이 세 겹을 넘으면 되돌린다.** `as_ref().and_then().filter().map().unwrap_or_else()` 는
  읽는 사람이 타입을 머릿속에서 다섯 번 바꿔야 한다.
- ★★ **`unwrap` 을 쓰면 타입에서 「실패할 수 있음」이 사라진다.** 남는 것은 패닉뿐이고,
  그것은 **호출자가 손쓸 수 없는 실패**다. 그래서 라이브러리 코드는 `unwrap`/`expect` 를 피한다
  — 그 판단의 정본이 [**23번 주제**](../23-panic-vs-result/)다.

### 10. 다른 주제와 잇기

- **`Option` 의 정의**는 `enum Option<T> { None, Some(T) }` 다.
  정본은 [**17번 주제**](../17-enums-and-data-carrying-variants/) (6)이고, 거기서 `MyOption` 을 직접 만들어
  std 의 것과 **크기까지 같다**는 것을 확인했다.
- **니치 최적화(niche optimization)** 다. `Option<Box<T>>` 가 `Box<T>` 와 같은 크기인 것은
  ★ **보장이 아니라 관찰**이다 — 17번 (7)이 `size_of` 와 `transmute` 로 직접 읽었고,
  같은 주제의 「구현 세부사항 대 언어 보장」 절이 그것을 **레이아웃 보장 아님**으로 못박았다.
- **`std::mem::take` 와 `std::mem::replace`** 다. 정본은 목록의 **44번 주제**이며,
  `Option::take`/`replace` 는 그 일반형의 `Option` 전용판이다.
- ★ **Java 의 `Optional` 과 갈리는 지점** — Java 에는 **`null` 이 여전히 있다.**
  `Optional` 은 그 위에 얹힌 **선택적 관용구**라 필드·파라미터에 쓰면 안 된다는 안티패턴 절이 따로 필요하다
  ([`java/syntax/38-optional/`](../../../java/syntax/38-optional/)). Rust 의 `Option` 은 **「없음」의 유일한 표면**이고
  컴파일러가 검사를 강제한다 — 그래서 안티패턴이 아니라 **기본형**이다.
- ★ **Go 는 제로값과 `(T, ok)`·`(T, error)` 로 표현한다**
  (Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **12번**·**23번**).
  「없음」이 **타입이 아니라 관례**라서 **검사를 잊어도 컴파일된다** — 그 대비가
  [**23번 주제**](../23-panic-vs-result/)에서 다시 나온다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `diff -rq` — 패닉 블록의 스레드 id만 달라짐 |
| ★★ **소비 대 빌림** | `b21-05`(E0382) · `b21-06`(E0507) · `b21-07`(고친 판) | 3 | 진단이 `map` 의 `self` 를 직접 인용 |
| ★★ **평가 시점** | `b21-04` — 부작용 줄 개수로 판정 | 1 | 네 자리 중 **세 곳**에서 호출 |
| `unwrap` 대 `expect` | `b21-01` · `b21-02` — 같은 줄·칸, 메시지만 다름 | 2 | 둘 다 종료 코드 101 |
| 조합 메서드 일곱 | `b21-03` — 있음·없음 두 입력에 전수 | 1 | `None` 은 통과, 클로저 미호출 |
| `?` 가 `Option` 에서 | `b21-08` | 1 | 세 줄 전부 예상대로 |
| `take`/`replace`/`get_or_insert` | `b21-09` | 1 | 두 번째 `take` 가 `None` |
| 네 길의 동치 | `b21-10` | 1 | 네 문자열이 한 글자도 같음 |

**구현 의존 항목**(버전이 오르면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `unwrap` 의 패닉 **메시지 문구** | std 의 문장이고 계약이 아니다 |
| 에러 번호(E0382·E0507)와 `help` **제안 문구** | 진단 구현에 달렸다 |
| 진단이 가리키는 `/rustc/<해시>/library/core/src/option.rs:1159:28` | ★ 판이 바뀌면 해시도 줄 번호도 바뀐다 |
| 패닉 첫 줄의 **스레드 id** | ★ **실행마다 다르다** — 대조 대상이 아니다 |
| 니치 최적화로 `Option<Box<T>>` 가 안 커지는 것 | 레이아웃은 보장이 아니다(17번이 정본) |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `diff -rq` 한다.
달라지는 파일은 **패닉이 있는 `b21-01`·`b21-02` 둘**이고, 그 차이는 **스레드 id 한 칸**이라야 한다.
