# rust/syntax/21 — `Option` 과 조합 메서드 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `enum Option`](https://doc.rust-lang.org/std/option/enum.Option.html) ·
> [std — `Option::map`](https://doc.rust-lang.org/std/option/enum.Option.html#method.map) ·
> [std — `Option::as_ref`](https://doc.rust-lang.org/std/option/enum.Option.html#method.as_ref) ·
> [The Rust Reference — The question mark operator](https://doc.rust-lang.org/reference/expressions/operator-expr.html#the-question-mark-operator).
> ★ `rustc --explain E0382` · `E0507` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.
> **버전** — `Option` 과 `map`·`and_then`·`unwrap_or_else`·`take`·`replace`·`as_ref` 는 **1.0.0** 부터다.\
> **`?` 가 `Option` 에도 되는 것은 1.22.0** 부터이고 에디션과 무관하다. `Option::replace` 는 1.31.0 부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 실행마다 커널이 주는 번호다 — (5)의 두 블록에 나온다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | 패닉 **메시지 본문**·`파일:줄:칸`·`note: run with RUST_BACKTRACE=1 …` | 같은 소스·같은 판에서 고정이다 |
| 안 흔들린다 | **종료 코드 101**(패닉) · `0` · `1` | 고정이다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄 | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 진단이 가리키는 std 경로 `/rustc/ded5c06…/library/core/src/option.rs:1159:28` | **이 판**에서는 고정이다(판이 바뀌면 바뀐다 — 아래 §구현 세부) |

## 한눈에 — 쉽게 말하면

**「값이 없을 수도 있다」를 타입에 적어 두고, 꺼내지 않은 채로 일을 시키는 것이다.**

다른 언어에서 「없음」은 **제어 흐름**이다 — `null` 을 만나면 터지거나, `if (x != null)` 로 막는다.
Rust 에서 「없음」은 **값**이다. `Option<T>` 라는 봉투에 들어 있고, 봉투를 여는 것과 봉투째 일을 시키는 것이 갈린다.

| 비유 | 실체 |
|---|---|
| 「**안에 물건이 있을 수도, 빈 봉투일 수도 있다**」 | **`Option<T>`** — `Some(T)` 아니면 `None` |
| 봉투를 **찢어서** 꺼낸다 — 비었으면 사고 | **`unwrap`·`expect`** — 없으면 패닉((5)) |
| 봉투 **안쪽 물건만 바꿔치기**하고 다시 봉한다 | **`map`** — `Option<A>` → `Option<B>` |
| 안쪽 작업이 **또 빈 봉투를 낼 수 있다** | **`and_then`** — 봉투가 두 겹이 되지 않게 납작하게 |
| 빈 봉투를 **영수증(오류)** 으로 바꾼다 | **`ok_or`·`ok_or_else`** — `Option` → `Result`([**22번 주제**](../22-result-question-mark-and-from/)) |
| 비었으면 **대신 쓸 것** | `unwrap_or` · `unwrap_or_else` · `unwrap_or_default` |
| ★ 봉투를 **건네주지 않고 안만 들여다본다** | **`as_ref`·`as_mut`** — 이것이 없으면 소유권에서 막힌다((3)) |
| ★ 남의 자리에 있는 봉투에서 **물건만 빼 온다** | **`take`·`replace`** — 빈 봉투를 두고 온다((7)) |

- ★★ **`Option` 은 언어 기능이 아니라 그냥 열거형이다.** [**17번 주제**](../17-enums-and-data-carrying-variants/) (6)에서 직접 만들어 본 그것이고,
  `enum Option<T> { None, Some(T) }` 한 줄이 std 에 적혀 있을 뿐이다. 그래서 `match` 도 되고 패턴도 된다.
- ★★ **조합 메서드는 「`match` 를 안 쓰기 위한 것」이 아니라 「봉투를 안 열기 위한 것」이다.**
  여는 순간(`unwrap`) 실패 가능성이 타입에서 사라지고 **패닉으로만 남는다**.
- ★★★ **이 주제의 함정은 문법이 아니라 소유권이다.** `map` 은 `self` 를 **소비**한다 — 빌린 `Option` 에 걸면 컴파일이 거부한다((3)).

```text
   Option<T> 를 다루는 네 갈래 — 무엇이 남나

   opt.unwrap()        opt.map(f)          opt.as_ref()        match opt
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ T 가 나온다   │    │ Option<U>    │    │ Option<&T>   │    │ 갈래 전부    │
   │ None 이면     │    │ opt 는 소비  │    │ opt 는 그대로│    │ 값은 내가    │
   │ ★ 패닉 101   │    │ ★ 뒤에서 못씀│    │ ★ 뒤에서 씀  │    │ 꺼내 쓴다    │
   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘


   같은 실패를 어디서 끝내나 — 이 묶음의 지도

     Option<T>  ──ok_or/ok_or_else──▶  Result<T, E>  ──?──▶  호출자에게
        │                                   │
        │ unwrap/expect                     │ unwrap/expect
        ▼                                   ▼
     여기서 프로그램이 끝난다 (패닉 101 — 23번 주제)
```

> **`Option<T>`** — 값이 있으면 `Some(T)`, 없으면 `None` 인 표준 열거형.\
> `null` 이 없는 언어에서 「없음」을 표현하는 유일한 관용 표면이다.

> **조합 메서드(combinator)** — 봉투를 열지 않고 `Option` 을 다른 `Option`·`Result`·값으로 옮기는 메서드들.\
> `map`·`and_then`·`filter`·`or_else`·`ok_or` 가 대표다.

> **소비(consume)** — 메서드가 `self` 를 값으로 받아 **소유권을 가져가는** 것.\
> 시그니처의 `fn map(self, …)` 가 그 표시다([**08번 주제**](../08-ownership-and-move/)).

> **게으른 평가(lazy)** — 필요할 때만 계산하는 것. `unwrap_or_else(f)` 는 **없을 때만** `f` 를 부르고,\
> `unwrap_or(v)` 의 `v` 는 **부르기 전에 이미 계산되어 있다**((4)).

## 이 주제가 답하려는 질문

1. **봉투를 안 열고 어디까지 갈 수 있나** — 일곱 메서드가 같은 두 입력에 무엇을 내는가((2)).
2. ★★ **어떤 메서드가 봉투를 가져가고 어떤 메서드가 빌리기만 하나** — 이것을 컴파일 에러로 가른다((3)).
3. **언제 봉투를 열어야 하나** — 열었다가 없으면 무엇이 남는가, 그리고 그 실패를 위로 올리려면((5)·(6)).

★ [**18번 주제**](../18-match-and-exhaustiveness/)가 「갈래를 빠짐없이 적는 법」이었다면 여기는 **갈래를 적지 않고 지나가는 법**이다.
갈래를 안 적어도 되는 이유는 `Option` 의 갈래가 **둘뿐이고 그 둘의 조합이 표준 메서드로 이미 다 적혀 있기** 때문이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **같은 입력 둘(있음·없음)에 전부 걸어 보기** | 메서드가 `None` 을 어떻게 옮기나 — 대부분 **그대로 통과**시킨다 | 이 주제의 기본 창 |
| ★★ **일부러 던져서 받는 E0382·E0507** | 그 메서드가 **소비하나 빌리나** — 시그니처를 읽는 것보다 빠르다 | [**11번 주제**](../11-borrow-checker-rejections/) |
| ★ **부작용으로 평가 시점 재기** | 인자가 **언제** 계산되나 — `unwrap_or` 대 `unwrap_or_else` | ★ 이 주제의 고유 창 |
| ★ **패닉 메시지 전문과 종료 코드** | 봉투를 열었다가 없었을 때 **무엇이 남나** | [**23번 주제**](../23-panic-vs-result/)로 이어진다 |

★★ 둘째 창이 이 주제의 고유한 값이다. std 문서의 시그니처(`fn map(self, …)` 대 `fn as_ref(&self, …)`)를 읽어도 되지만,
**컴파일러가 「이 메서드가 receiver 의 소유권을 가져간다」고 이름까지 대며 말해 주는 쪽**이 훨씬 강하다.
실제로 진단 안에 `` note: `Option::<T>::map` takes ownership of the receiver `self` `` 가 박혀 나온다((3)).

### (1) `Option` 은 그냥 열거형이다 — 17번에서 이어받는 것

[**17번 주제**](../17-enums-and-data-carrying-variants/)가 세운 결론 셋을 여기서 그대로 쓴다. **다시 증명하지 않는다.**

- `Option<T>` 의 정의는 `enum Option<T> { None, Some(T) }` 다. 언어 기능이 아니라 std 의 선언이다.
- 그래서 `match`·`if let`·패턴이 전부 그대로 먹는다([**18번**](../18-match-and-exhaustiveness/)·[**19번**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)·[**20번**](../20-if-let-while-let-let-else-and-let-chains/)).
- ★ **니치 최적화** — `Option<Box<T>>` 가 `Box<T>` 와 **같은 크기**인 것은 17번 (7)에서 `size_of` 로 직접 재고
  `transmute` 로 태그 자리까지 읽어 확인했다. **거기가 정본이므로 여기서는 결론만 되짚는다** —
  「`Option` 을 씌우는 값 비용이 0인 타입이 있다. 참조·`Box`·`NonZero` 계열이 그렇고, `u32` 같은 것은 아니다.」
  ★★ 그리고 그것은 **언어 보장이 아니라 이 판의 관찰**이다(17번 §구현 세부에 그렇게 적혀 있다).

> **경계 선언** — 「`Option` 이 무엇으로 만들어졌나」(열거형·크기·태그·니치)는 **17번이 정본**이다.\
> 여기는 「**그 열거형에 std 가 붙여 둔 메서드를 어떻게 고르나**」만 다룬다.

### (2) 조합 메서드 한 바퀴 — 같은 입력 둘에 전부 걸기

**언제 쓰나** — 각 메서드가 `None` 을 어떻게 옮기는지 한 번에 보고 싶을 때.

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

- ★ **대부분의 조합 메서드는 `None` 을 그대로 통과시킨다.** `map`·`and_then`·`filter` 의 `None` 줄이 전부 `None` 이다 —
  **함수는 아예 호출되지 않는다**(「빈 봉투에는 할 일이 없다」).
- ★★ **`map` 과 `and_then` 의 차이는 「함수가 무엇을 돌려주나」다.** `and_then(label)` 에서 `label` 은 `Option` 을 돌려준다.
  이것을 `map` 으로 했으면 `Option<Option<&str>>` 이 됐을 것이다 — `and_then` 이 **납작하게** 만든다.
- ★ **`filter` 는 조건이 거짓이면 `Some` 을 `None` 으로 떨어뜨린다.** `443` 은 `< 100` 이 거짓이라 `None` 이 됐다.
- **`ok_or` 는 세계를 바꾼다** — `Option<u16>` 이 `Result<u16, &str>` 이 된다. 여기서 [**22번 주제**](../22-result-question-mark-and-from/)로 넘어간다.
- `unwrap_or_default()` 는 `T: Default` 를 요구한다. `u16` 의 기본값이 `0` 이라 `unwrap_or(0)` 과 같은 답이 나왔다.

### (3) ★★ 소비냐 빌림이냐 — 컴파일 에러로 가른다

**언제 쓰나** — `map` 한 줄을 넣었더니 그 아래 멀쩡하던 줄이 빨개질 때.

**전** — `map` 을 걸고 나서 원본을 또 쓴다.

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

- ★★ 진단의 핵심은 **두 줄**이다 — `` `name` moved due to this method call `` 과
  `` note: `Option::<T>::map` takes ownership of the receiver `self`, which moves `name` ``.
  **「메서드 호출 때문에 이동했다」** 고 컴파일러가 직접 말한다.
- ★ `` help: consider calling `.as_ref()` or `.as_mut()` to borrow the type's contents `` — 처방까지 준다.
- ★ 두 번째 `help` 는 `.clone()` 인데, **그 뒤에 「하지만 원하는 동작이 아닐 수 있다」가 붙어 있다.** 컴파일러도 안다.

**같은 함정이 빌린 `Option` 에서는 다른 번호로 난다.** 남의 것을 빌려 왔으니 애초에 옮길 수 없다.

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

- ★ **E0382 와 E0507 이 갈리는 자리** — 앞엣것은 「내 것을 이미 넘겼다」이고, 뒤엣것은 「남의 것이라 넘길 수가 없다」다.
  ★ **처방은 같다** — `.as_ref()`.
- `describe` 함수는 **아무 에러도 안 낸다.** `match cfg` 는 매치 인체공학 덕분에 `s` 를 `&String` 으로 묶기 때문이다
  ([**19번 주제**](../19-pattern-syntax-guards-bindings-and-match-ergonomics/)). **`match` 는 되는데 `map` 은 안 되는** 이 비대칭이 초심자를 잡는다.

**후** — `as_ref` 를 끼우면 통과한다. `as_mut` 은 안쪽을 고칠 수 있게 해 준다.

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

- ★★ `as_ref()` 의 타입은 `Option<&String>` 이다 — **봉투는 그대로 두고 안쪽만 빌린 새 봉투**를 만든다.
  `&Option<String>` 과 `Option<&String>` 은 다른 타입이고, **조합 메서드가 먹는 쪽은 뒤엣것**이다.
- `as_mut()` 은 `Option<&mut String>` 이라 `push_str` 로 **안쪽을 고칠 수 있다**. 봉투의 소유권은 여전히 원래 자리에 있다.
- ★ 마지막 두 줄이 요점이다 — `as_ref().map(…)` 을 세 번 걸어도 **원본은 계속 살아 있다.**

### (4) ★ 평가 시점 — `unwrap_or` 와 `unwrap_or_else`

**언제 쓰나** — 대체값을 만드는 데 비용이 들거나 부작용이 있을 때.

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

- ★★★ **A 가 이 실험의 결론이다.** 값이 **있는데도** `fallback()` 이 돌았다.
  `unwrap_or(fallback())` 은 **인자를 먼저 계산해서 넘기는 보통의 함수 호출**이기 때문이다 — 「없을 때만」이 아니다.
- **B 는 안 돌았다.** `unwrap_or_else` 는 **클로저를 받아** 두었다가 `None` 일 때만 부른다.
- C·D 는 둘 다 돌았다 — 없으면 어느 쪽이든 대체값이 필요하다.
- ★ 그래서 규칙은 이렇다: **대체값이 상수·리터럴이면 `unwrap_or`, 계산·할당·I/O·부작용이면 `unwrap_or_else`.**
  `unwrap_or(String::from("기본"))` 처럼 **할당이 들어가는 것도 매번 돈다.**
- ★ 같은 규칙이 `or`/`or_else`·`ok_or`/`ok_or_else`·`map_or`/`map_or_else` 쌍에 그대로 적용된다.
  **`_else` 가 붙은 쪽은 전부 게으르다.**

### (5) 봉투를 열었는데 비었으면 — `unwrap` 과 `expect`

**언제 쓰나** — 「여기서는 절대 `None` 이 아니다」라고 단언할 때. 틀리면 프로그램이 끝난다.

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

**같은 자리, `expect` 로 바꾼 것.**

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

- ★★ **두 블록의 차이는 패닉 메시지 한 줄뿐이다.** `파일:줄:칸`(`ex.rs:10:30`)도 종료 코드 101 도 같다.
- `unwrap` 은 **std 가 정한 문장**(`` called `Option::unwrap()` on a `None` value ``)을 찍는다 —
  **어느 `unwrap` 인지는 줄 번호로만 안다.**
- ★★ `expect` 는 **내가 적은 문장**을 그 자리에 찍는다. 그래서 `expect` 의 메시지는
  「무엇을 기대했나」가 아니라 **「무엇이 깨졌길래 여기에 왔나」** 를 적는 자리다([**23번 주제**](../23-panic-vs-result/)에서 다시 다룬다).
- ★ 마커를 `eprintln!` 으로 찍은 이유 — **패닉은 표준 오류로 나간다.** `println!` 과 섞으면
  터미널에서 본 순서와 파이프로 받은 순서가 달라질 수 있다. **한 블록 안에서는 한쪽으로 통일한다.**

### (6) ★ `?` 는 `Option` 에서도 된다

**언제 쓰나** — `None` 이면 **그 자리에서 `None` 을 반환**하고 끝내고 싶을 때.

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

- ★ `s.split_whitespace().next()?` 는 「없으면 이 함수는 여기서 `None` 을 반환한다」로 읽는다.
  **`and_then` 사슬을 평평하게 펴는 것**과 같은 일이다.
- ★★ **`?` 가 `Option` 에서 되는 조건은 딱 하나 — 함수의 반환 타입도 `Option` 이라야 한다.**
  `Result` 를 반환하는 함수에서 `Option` 에 `?` 를 붙이면 거부된다([**22번 주제**](../22-result-question-mark-and-from/)에서 그 진단 전문을 던진다).
- `both("alpha beta", "   ")` 이 `None` 인 이유 — 공백뿐인 문자열은 `split_whitespace` 가 아무것도 안 낸다.

### (7) 남의 자리에 있는 봉투 — `take` 와 `replace`

**언제 쓰나** — `&mut self` 메서드 안에서 필드의 `Option` 을 **소유한 채로** 꺼내야 할 때.

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

- ★★ **`take()` 는 그 자리에 `None` 을 두고 안에 있던 것을 가져온다.** 「빌린 자리에서 소유권을 꺼내는」 표준 관용구다.
  두 번째 `take` 가 `None` 을 돌려준 것이 그 증거다.
- **`replace(v)` 는 새 값을 두고 옛 값을 가져온다.** `take()` 는 `replace(None)` 과 같은 일을 하는 특수형이다.
- `get_or_insert(v)` 는 **비어 있을 때만 채우고** 안쪽에 대한 `&mut` 를 돌려준다.
- ★ 이 셋이 없으면 `self.payload` 를 통째로 옮길 수 없어 [**11번 주제**](../11-borrow-checker-rejections/)의 전형적인 거부에 걸린다.
  일반화한 도구가 `std::mem::take`/`replace` 이고 그쪽 정본은 목록의 **44번 주제**다.

### (8) 무엇을 고르나 — 같은 답을 네 가지로

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

- 네 판이 **한 글자도 같은 문자열**을 냈다. 그러니 선택은 **정답이 아니라 읽기 쉬움**의 문제다.
- ★ 기준은 (6)에서 이어진다 — **값이 이어지면 조합 메서드, 갈래마다 할 일이 다르면 `match`,
  실패하면 나가야 하면 `let else`, 한 갈래만 보고 지나가면 `if let`.**

## 문법 — 형태와 규칙

```text
   시그니처를 읽는 법 — 첫 인자가 전부를 정한다

   fn unwrap(self) -> T                     self      → 봉투를 가져간다(뒤에서 못 씀)
   fn map<U>(self, f: impl FnOnce(T) -> U)  self      → 가져간다
   fn as_ref(&self) -> Option<&T>           &self     → 빌린다(뒤에서 씀)
   fn as_mut(&mut self) -> Option<&mut T>   &mut self → 빌린다(고칠 수 있다)
   fn take(&mut self) -> Option<T>          &mut self → 빌린 자리에서 ★ 소유권을 꺼낸다
   fn is_some(&self) -> bool                &self     → 빌린다

   대표 메서드 지도

   Option<T> ──map(T→U)────────▶ Option<U>
             ──and_then(T→Option<U>)▶ Option<U>      (납작하게)
             ──filter(&T→bool)──▶ Option<T>
             ──or(Option<T>)────▶ Option<T>          (빈 봉투를 대체 봉투로)
             ──ok_or(E)─────────▶ Result<T, E>       (22번으로 넘어가는 다리)
             ──unwrap_or(T)─────▶ T                  (★ 인자를 먼저 계산한다)
             ──unwrap_or_else(||T)▶ T                (★ 없을 때만 계산한다)
             ──unwrap()/expect(&str)▶ T              (★ 없으면 패닉 101)
             ──?────────────────▶ T                  (★ 없으면 None 을 반환 — 함수가 Option 이라야)
```

- **`Some`·`None` 은 prelude 에 있다.** `Option::Some` 이라고 안 써도 된다.
- **`unwrap_or_default()` 는 `T: Default`** 를 요구한다. 없으면 컴파일이 거부한다.
- ★ **`copied()`·`cloned()`** 는 `Option<&T>` 를 `Option<T>` 로 내린다. `as_ref()` 다음에 자주 붙는다.
- ★ `Option<&T>` 와 `&Option<T>` 는 **다른 타입**이다. 조합 메서드를 체인으로 이으려면 앞엣것이라야 한다.
- **`?` 는 `Option` 과 `Result` 를 섞지 못한다.** 함수 반환 타입과 같은 세계라야 한다.

## 어디서 틀리나

| 증상 | 진짜 원인 | 고치는 법 |
|---|---|---|
| `map` 을 넣었더니 **아래 줄**이 E0382 로 빨개진다 | `map` 이 `self` 를 소비했다 | `as_ref()` 를 끼운다((3)) |
| 빌린 `&Option<String>` 에서 E0507 | 남의 봉투라 옮길 수 없다 | `as_ref()`. `match` 는 되는데 `map` 이 안 되는 것이 단서 |
| `unwrap_or` 를 썼는데 **로그가 두 배**로 찍힌다 | 인자가 **있든 없든** 계산된다 | `unwrap_or_else` 로 바꾼다((4)) |
| `map` 을 이었더니 `Option<Option<T>>` | 클로저가 `Option` 을 돌려준다 | `and_then` |
| ★ `?` 가 「`Option` 이 아니다」로 거부된다 | 함수 반환 타입이 `Result` 다 | `ok_or(…)?` 로 세계를 맞춘다([**22번**](../22-result-question-mark-and-from/)) |
| `unwrap()` 패닉인데 **어디인지 모르겠다** | `unwrap` 은 std 문장만 찍는다 | `expect` 로 바꿔 「무엇이 깨졌나」를 적는다((5)) |
| `self.field.map(…)` 이 `&mut self` 메서드에서 거부된다 | 필드를 통째로 옮기려 했다 | `take()`·`as_ref()`·`as_mut()`((7)) |
| ★ 「`None` 이면 기본값」을 `if let` 으로 7줄 쓴다 | 조합 메서드를 모르는 것 | `unwrap_or_else` 한 줄((8)) |

★★ **가장 흔한 사고는 「`None` 검사를 안 한 것」이 아니다** — 그건 컴파일러가 막는다.
**타입이 강제하는 검사를 `unwrap` 으로 꺼 버리는 것**이 실제 사고다. 그래서 `unwrap` 을 어디에 써도 되는지가
[**23번 주제**](../23-panic-vs-result/)의 본문이 된다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `enum Option<T> { None, Some(T) }` 라는 **정의** | **std 의 공개 계약** — 변형 이름과 개수는 바뀌지 않는다 | std 문서 |
| `map` 이 `self` 를, `as_ref` 가 `&self` 를 받는 것 | **공개 시그니처** — 계약이다 | std 문서 |
| `unwrap_or_else` 가 `None` 일 때만 클로저를 부르는 것 | **문서화된 계약**(「lazily evaluated」) | std 문서 + (4)의 실측 |
| `unwrap` 의 **패닉 메시지 문구** | ★ **구현 세부** — 바뀔 수 있다 | (5)의 실측 |
| 진단 문구·`help` 제안·에러 번호(E0382·E0507) | ★ **구현 세부** — rustc 판에 달렸다 | (3)의 실측 |
| 진단이 가리키는 `/rustc/<해시>/library/core/src/option.rs:1159:28` | ★ **구현 세부** — 판이 바뀌면 해시도 줄 번호도 바뀐다 | (3)의 실측 |
| ★ **니치 최적화로 `Option<Box<T>>` 가 안 커지는 것** | ★ **구현 세부** — 레이아웃은 보장이 아니다 | [**17번 주제**](../17-enums-and-data-carrying-variants/) (7) |
| **종료 코드 101** | 패닉으로 끝난 프로세스의 코드 — 고정이다 | [**23번 주제**](../23-panic-vs-result/)에서 다시 던진다 |

## 언제 쓰고 언제 안 쓰나

- **`Option` 을 쓴다** — 「없음」이 **정상 상태**일 때. 검색 결과 없음, 선택 설정 미지정, 리스트의 첫 원소.
- **`Result` 를 쓴다** — 「왜 없는지」를 호출자에게 말해야 할 때. `Option` 은 **이유를 못 담는다**([**22번**](../22-result-question-mark-and-from/)).
- **`unwrap` 을 쓴다** — 그 줄 **위에서** 불변식이 보장될 때만. 상수 리터럴 파싱, 방금 넣은 값, 비지 않음을 확인한 직후.
- **`expect` 를 쓴다** — 위와 같되, **깨졌을 때 사람이 읽을 문장**이 있을 때. 라이브러리 코드라면 애초에 둘 다 안 쓴다.
- **조합 메서드를 쓴다** — 값이 **한 줄기로 이어질 때**. 갈래마다 할 일이 다르면 `match` 가 읽기 쉽다.
- ★ **체인이 세 겹을 넘으면 되돌린다** — `opt.as_ref().and_then(…).filter(…).map(…).unwrap_or_else(…)` 는
  `let else` 두 줄이 더 읽기 쉬운 경우가 많다([**20번 주제**](../20-if-let-while-let-let-else-and-let-chains/)).

## 핵심 문장

- **`Option` 은 문법이 아니라 열거형이다** — 17번에서 직접 만들어 봤고, 여기서는 std 가 붙여 둔 메서드만 고른다.
- **봉투를 여는 것과 봉투째 일을 시키는 것이 갈린다.** 여는 순간 실패 가능성이 타입에서 사라지고 패닉만 남는다.
- ★★ **메서드가 `self` 를 받나 `&self` 를 받나가 이 주제의 절반이다.** `map` 뒤에 원본을 쓰면 E0382 가 그것을 알려 준다.
- ★ **`_else` 가 붙은 메서드는 게으르다.** `unwrap_or(비싼_계산())` 은 **있을 때도** 계산한다.
- **`?` 는 `Option` 에서도 된다** — 단 함수 반환 타입이 `Option` 일 때만. 여기서 22번으로 넘어간다.

## 관련 자료

- [**17번 주제** — 열거형과 데이터를 담는 변형](../17-enums-and-data-carrying-variants/) —
  ★ **경계**: `Option` 이 **무엇으로 만들어졌나**(정의·크기·태그·니치)는 거기가 정본이고, 여기는 **그 위의 메서드 선택**만이다.
- [**18번 주제** — `match` 와 완전성 검사](../18-match-and-exhaustiveness/) — 갈래를 빠짐없이 적는 쪽. 여기는 **적지 않고 지나가는** 쪽이다.
- [**20번 주제** — `if let`·`let else`](../20-if-let-while-let-let-else-and-let-chains/) —
  ★ **경계**: 「조건에서 꺼내 쓰는 문법」은 거기, 여기는 「꺼내지 않고 옮기는 메서드」다. (8)이 둘을 나란히 놓았다.
- [**22번 주제** — `Result` 와 `?`·`From` 변환](../22-result-question-mark-and-from/) — `ok_or` 로 건너가는 쪽. 「없음」에 **이유**를 붙인다.
- [**23번 주제** — `panic!` 대 `Result`](../23-panic-vs-result/) — `unwrap` 을 **어디에 써도 되는가**의 정본.
- 목록의 **44번 주제** — `mem::take`/`replace`. (7)의 `Option::take` 를 일반화한 것.
- Java 의 `Optional` — [`java/syntax/38-optional/`](../../../java/syntax/38-optional/). **필드·파라미터에 두면 안 되는 이유**가 거기 있다.
  ★ **대비**: Rust 의 `Option` 은 **`null` 이 없어서 유일한 표면**이고, Java 의 `Optional` 은 `null` 과 **공존한다** — 그래서 안티패턴 절이 필요하다.
- [std — `Option` 전체 메서드 목록](https://doc.rust-lang.org/std/option/enum.Option.html)

## 용어 풀이

- **`Option<T>`** — 값이 있으면 `Some(T)`, 없으면 `None` 인 표준 열거형.
- **조합 메서드(combinator)** — 봉투를 열지 않고 다른 값으로 옮기는 메서드. `map`·`and_then`·`filter` 등.
- **소비(consume)** — 메서드가 `self` 를 값으로 받아 소유권을 가져가는 것.
- **니치(niche)** — 그 타입이 절대 갖지 않는 비트 패턴. 태그를 그 자리에 숨기는 최적화의 재료(17번).
- **게으른 평가(lazy)** — 필요할 때만 계산하는 것. `_else` 계열이 그렇다.
- **매치 인체공학(match ergonomics)** — 참조를 매치할 때 바인딩에 자동으로 `&` 가 붙는 규칙(19번).
- **패닉(panic)** — 복구 불가로 판단해 스택을 되감으며 끝내는 것. 종료 코드 101(23번).

## 더 들어가면

- **`zip`·`unzip`·`flatten`** — `Option<(A, B)>` 와 `(Option<A>, Option<B>)` 를 오간다. `flatten` 은 `and_then(|x| x)` 와 같다.
- **`Option<&mut T>` 의 재빌림** — `as_mut()` 로 얻은 것을 두 번 쓰려면 수명이 걸린다([**12번 주제**](../12-lifetime-annotations-and-elision/)).
- **`iter()`/`into_iter()`** — `Option` 은 원소가 0개 또는 1개인 이터레이터다. `Vec<Option<T>>` 를 `flatten()` 하면 `None` 이 사라진다.
- **`Option<T>` 를 반환하는 트레이트 메서드** — `Iterator::next` 가 대표다(목록의 **36번 주제**).
- **`matches!` 매크로** — `matches!(opt, Some(x) if x > 3)` 으로 조건까지 한 줄에 판정한다.
