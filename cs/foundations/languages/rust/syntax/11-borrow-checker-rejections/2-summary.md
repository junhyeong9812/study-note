# rust/syntax/11 — 빌림 검사기가 거부하는 전형 코드와 고치는 법 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std `mem::take`](https://doc.rust-lang.org/std/mem/fn.take.html) ·
> [std `mem::replace`](https://doc.rust-lang.org/std/mem/fn.replace.html) ·
> [std `slice::split_at_mut`](https://doc.rust-lang.org/std/primitive.slice.html#method.split_at_mut) ·
> [std `HashMap::entry`](https://doc.rust-lang.org/std/collections/struct.HashMap.html#method.entry) ·
> [std `Vec::retain`](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.retain) ·
> [std `RefCell`](https://doc.rust-lang.org/std/cell/struct.RefCell.html) ·
> [Reference — Destructors(임시값 수명 연장)](https://doc.rust-lang.org/reference/destructors.html) ·
> `rustc --explain E0499` / `E0502` / `E0505` / `E0506` / `E0507` / `E0716`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고·패닉은 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다 —\
> 이 주제에는 **2021 에서 거부되고 2024 에서 통과해 실행되는 파일**이 실제로 있다(아래 (11)).\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.
> **버전** — `mem::take` 는 **1.40.0**, `mem::replace`·`split_at_mut`·`HashMap::entry`·`Vec::retain`·`RefCell` 은 **1.0.0** 부터다(std 문서의 Stable since 확인).\
> `RefCell` 의 **패닉 문구**는 rustc·std 판에 달렸다(아래 「구현 세부사항 대 언어 보장」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**막히는 자리는 몇 개 안 된다. 그리고 자리마다 정해진 열쇠가 있다.**

[**10번 주제**](../10-borrowing-and-aliasing-rules/)가 **규칙**이었다면, 이 주제는 그 규칙에 **실제로 걸리는 코드 모음**과
**각각의 처방**이다. 규칙을 외운다고 코드가 통과하지는 않는다 — **어느 열쇠를 꺼낼지**가 이 주제다.

| 비유 | 실체 |
|---|---|
| 책을 읽으면서 그 책장에 책을 꽂는다 | **순회 중 변경** — `for x in &v { v.push(..) }` → E0502 |
| 한 서랍의 두 칸을 양손으로 동시에 연다 | **원소 둘 동시 `&mut`** → E0499. 열쇠는 `split_at_mut` |
| 서랍 전체를 잠근 채 옆 칸을 열려 한다 | **메서드를 거친 필드 접근** → E0499. 열쇠는 **필드 직접 짚기** |
| 남의 가방에서 물건을 꺼내 간다 | **`&mut self` 에서 값 꺼내기** → E0507. 열쇠는 `mem::take` |
| 빌려준 물건을 팔아 버린다 | **빌린 채로 이동** → E0505 |
| 영수증만 들고 나왔는데 가게가 문을 닫았다 | **임시값 참조** → E0716 |
| 검사를 **경비원에게 맡긴다** — 대신 걸리면 그 자리에서 쫓겨난다 | **`RefCell`** — 컴파일 에러가 **런타임 패닉**이 된다 |

- ★★ **거부는 「이 코드가 위험하다」가 아니라 「검사기가 안전을 증명 못 했다」일 수도 있다.**\
  둘을 가르는 것이 이 주제의 값이고, **처방이 달라진다** — 앞은 설계를 고치고, 뒤는 **같은 뜻의 다른 표현**을 찾는다.
- ★ **열쇠는 여섯 개뿐이다** — 순서 바꾸기 · 쪼개기 · 인덱스로 · `mem::take` · 자료구조 바꾸기 · `RefCell`.
- **컴파일러가 열쇠 이름을 대 주는 자리도 있다** — E0499 가 `split_at_mut` 을 직접 권한다(아래 (2)).

```text
   거부당했다 — 무엇부터 보나

   ① 에러 번호를 본다        E0499/E0502 = 겹쳤다 · E0505/E0507 = 옮겼다 · E0596 = mut 이 없다
   ② `later used here` 를 본다  그 줄이 빌림의 만료 지점이다 (10번)
   ③ 그 줄을 앞으로 옮길 수 있나?  ── 예 ──▶ 끝. 열쇠 1(순서)
        │ 아니오
   ④ 서로 다른 칸을 만지나?      ── 예 ──▶ 열쇠 2(쪼개기: 필드 직접·split_at_mut·parts_mut)
        │ 아니오
   ⑤ 값만 있으면 되나?           ── 예 ──▶ 열쇠 3(인덱스·복사·clone)
        │ 아니오
   ⑥ 꺼내서 채워 넣으면 되나?     ── 예 ──▶ 열쇠 4(mem::take / replace / swap)
        │ 아니오
   ⑦ 모양 자체가 안 되나?         ── 예 ──▶ 열쇠 5(자료구조 교체: 인덱스·Rc) 또는 열쇠 6(RefCell)
```

**언어도 똑같은 구조다.** 컴파일러가 열쇠를 직접 말해 준 실측이다.

```text
error[E0499]: cannot borrow `v` as mutable more than once at a time
 --> ex.rs:5:18
  |
  = help: use `.split_at_mut(position)` to obtain two mutable non-overlapping sub-slices
```

> **전형(pattern)** — 서로 다른 코드인데 **같은 이유로 같은 에러**가 나는 모양.\
> 이 주제는 그 모양 12개와 각각의 열쇠를 모은다.

> **분할 빌림(split borrow)** — 한 값의 **서로 다른 칸**을 각각 따로 빌리는 것.\
> 예: `&mut d.title` 과 `&mut d.body` 는 공존한다. 단 **메서드를 거치면 안 된다.**

> **`mem::take`** — 자리에 **`Default` 값**을 두고 알맹이를 꺼내는 함수.\
> 예: `mem::take(&mut self.data)` 는 `self.data` 를 `String::new()` 로 만들고 원래 값을 돌려준다.

> **내부 가변성(interior mutability)** — `&T` 만 있어도 속을 고칠 수 있게 해 주는 장치.\
> `RefCell` 이 대표. **규칙이 없어지는 게 아니라 검사 시점이 런타임으로 옮겨간다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **어떤 코드가 반복해서 막히나** — 이름을 붙일 수 있는 모양이 몇 개이고 각각 어느 에러인가.
2. **그 각각에 어떤 열쇠가 맞나** — 왜 그 열쇠인지 시그니처·소유권으로 설명할 수 있나.
3. **「안전한데 거부된 것」과 「정말 위험한 것」을 어떻게 가르나** — 가른 다음 처방이 어떻게 갈리나.

★ 10번이 「**규칙이 무엇인가**」였고 [**12번**](../12-lifetime-annotations-and-elision/)이 「**수명을 어떻게 적나**」라면,
여기는 「**막혔을 때 손이 어디로 가야 하나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 세 창

**언제 쓰나** — 아래 모든 절이 이 셋 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **거부된 판과 통과한 판을 나란히 던지기** | 열쇠가 **정말 그 자리를 여는지** | ★ 이 주제의 기본형 |
| **컴파일러의 `help:` 줄** | ★ 열쇠 이름을 **컴파일러가 대 준다** | 10·12번에서 이어받음 |
| **런타임 패닉** | `RefCell` — 검사가 **어디로 옮겨갔나** | ★ 이 주제에서 처음 |

★ 앞 두 주제와 다른 점 — **여기서는 거부 전문만큼 「통과한 판」이 중요하다.**
열쇠가 맞는지는 **통과한 판의 실행 출력**으로만 확인된다.

비용 — 없음. 전부 컴파일·실행만 해 보면 된다.

### (1) 전형 1 — 순회하면서 그 컬렉션을 고친다

**언제 쓰나** — `for` 안에서 `push`·`remove`·`insert` 를 쓰고 싶을 때.

```text
===== 소스: ex.rs =====
// 전형 1 — 순회하면서 그 컬렉션을 고친다
fn main() {
    let mut v = vec![1, 2, 3];
    for x in &v {
        if *x % 2 == 1 { v.push(*x * 10); }
    }
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:26
  |
4 |     for x in &v {
  |              --
  |              |
  |              immutable borrow occurs here
  |              immutable borrow later used here
5 |         if *x % 2 == 1 { v.push(*x * 10); }
  |                          ^^^^^^^^^^^^^^^ mutable borrow occurs here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

- ★ **같은 줄(4)에 라벨이 둘** 붙는다 — `occurs here` 와 `later used here` 가 **같은 `&v`** 에 붙었다.\
  반복자가 **루프 끝까지** 그 빌림을 쓰기 때문이다. 10번에서 배운 「마지막 사용」이 **루프 전체**로 늘어난 것이다.
- ★★ **이건 「검사기가 소심한 것」이 아니라 진짜 위험**이다. `push` 가 재할당을 일으키면 `x` 가 가리키던 자리가 없어진다.\
  C++ 의 iterator invalidation 과 **같은 사고**를 컴파일 타임에 막은 것이다.

**열쇠 세 개** — 셋 다 던져 봤다.

```text
===== 소스: ex.rs =====
// 처방 1-a — 인덱스로 돈다. 길이를 먼저 고정한다
fn main() {
    let mut v = vec![1, 2, 3];
    let n = v.len();
    for i in 0..n {
        if v[i] % 2 == 1 { v.push(v[i] * 10); }
    }
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[1, 2, 3, 10, 30]
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// 처방 1-b — 읽기 구간과 쓰기 구간을 나눈다
fn main() {
    let mut v = vec![1, 2, 3];
    let extra: Vec<i32> = v.iter().filter(|x| *x % 2 == 1).map(|x| x * 10).collect();
    v.extend(extra);
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[1, 2, 3, 10, 30]
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// 처방 1-c — 지우는 쪽이면 retain 하나로 끝난다
fn main() {
    let mut v = vec![1, 2, 3, 4, 5];
    v.retain(|x| x % 2 == 1);
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[1, 3, 5]
(종료 코드 0)
```

| 열쇠 | 무엇을 하나 | 대가 |
|---|---|---|
| **인덱스 루프** | 빌림을 `v[i]` 한 줄로 **짧게** 만든다 | 경계 검사 · 길이를 손으로 고정해야 한다 |
| **읽기/쓰기 분리** | 중간 `Vec` 을 만들어 **구간을 뗀다** | 할당 한 번 |
| **`retain`** | 순회와 삭제를 **std 안**에서 한다 | 삭제에만 쓸 수 있다 |

★ **셋 다 「빌림 구간을 겹치지 않게 만든 것」이고 방법만 다르다.**

### (2) ★ 전형 2 — 한 컬렉션의 원소 둘을 동시에 `&mut`

**언제 쓰나** — `v[i]` 와 `v[j]` 를 맞바꾸거나 서로 참조해 고칠 때.

```text
===== 소스: ex.rs =====
// 전형 2 — 한 Vec 의 원소 둘을 동시에 가변으로 빌린다
fn main() {
    let mut v = vec![1, 2, 3];
    let a = &mut v[0];
    let b = &mut v[2];
    *a += *b;
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `v` as mutable more than once at a time
 --> ex.rs:5:18
  |
4 |     let a = &mut v[0];
  |                  - first mutable borrow occurs here
5 |     let b = &mut v[2];
  |                  ^ second mutable borrow occurs here
6 |     *a += *b;
  |     -------- first borrow later used here
  |
  = help: use `.split_at_mut(position)` to obtain two mutable non-overlapping sub-slices

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
```

- ★★ **`0` 과 `2` 는 겹치지 않는데도 거부된다.** `IndexMut` 이 **`&mut self`**(컬렉션 전체)를 받기 때문이다.\
  인덱스 값은 **런타임 값**이라 컴파일러가 「겹치지 않는다」를 증명할 수 없다.\
  **안전한 코드인데 거부된 것**이다 — (6)의 분류로는 **B 유형**이다.
- ★ **`= help:` 가 열쇠 이름을 그대로 준다** — `use .split_at_mut(position)`.

```text
===== 소스: ex.rs =====
// 처방 2-a — split_at_mut 로 슬라이스를 둘로 가른다
fn main() {
    let mut v = vec![1, 2, 3];
    let (left, right) = v.split_at_mut(2);
    let a = &mut left[0];
    let b = &mut right[0];
    *a += *b;
    println!("{:?} {:?}", left, right);
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[4, 2] [3]
[4, 2, 3]
(종료 코드 0)
```

- `split_at_mut` 은 **겹치지 않는 두 슬라이스**를 돌려준다. 그 안에서는 각각 마음대로 `&mut` 를 만든다.
- ★ **std 가 이 함수를 `unsafe` 로 구현하고 안전한 표면만 내준다.** 「검사기가 증명 못 하는 것을 사람이 한 번 증명하고 가둔 것」이 이 함수의 정체다(목록의 **56번 주제**).

값만 필요하면 더 싼 열쇠가 있다.

```text
===== 소스: ex.rs =====
// 처방 2-b — 값만 필요하면 먼저 읽어 복사한다
fn main() {
    let mut v = vec![1, 2, 3];
    let b = v[2];          // i32 는 Copy — 빌림이 이 줄에서 끝난다
    v[0] += b;
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[4, 2, 3]
(종료 코드 0)
```

★ **`Copy` 타입이면 「빌리지 말고 베껴라」가 거의 항상 정답**이다(09번). `String` 이면 `clone()` 이 같은 자리를 맡는다.

### (3) ★★ 전형 3 — 메서드를 거쳐 두 필드를 잡는다

**언제 쓰나** — 접근자(`fn x_mut(&mut self)`)를 만들어 놓고 둘을 같이 쓸 때.

```text
===== 소스: ex.rs =====
// 전형 3 — 메서드를 거쳐 두 필드를 동시에 잡는다
struct Doc { title: String, body: String }

impl Doc {
    fn title_mut(&mut self) -> &mut String { &mut self.title }
    fn body_mut(&mut self) -> &mut String { &mut self.body }
}

fn main() {
    let mut d = Doc { title: String::from("제목"), body: String::from("본문") };
    let t = d.title_mut();
    let b = d.body_mut();
    t.push('!');
    b.push('?');
    println!("{} / {}", d.title, d.body);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `d` as mutable more than once at a time
  --> ex.rs:12:13
   |
11 |     let t = d.title_mut();
   |             - first mutable borrow occurs here
12 |     let b = d.body_mut();
   |             ^ second mutable borrow occurs here
13 |     t.push('!');
   |     - first borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
```

- ★ 에러가 짚는 것은 `d` 지 `d.title` 이 아니다. **시그니처가 `&mut self` 라 전체를 잡았다.**
- **빌림 검사기는 `title_mut` 의 몸통을 안 본다**(10번의 결론). 몸통을 보면 `self.title` 만 만지는데도 그렇다.

**열쇠 둘.**

```text
===== 소스: ex.rs =====
// 처방 3-a — 필드를 직접 짚으면 칸 단위로 빌린다
struct Doc { title: String, body: String }

fn main() {
    let mut d = Doc { title: String::from("제목"), body: String::from("본문") };
    let t = &mut d.title;
    let b = &mut d.body;
    t.push('!');
    b.push('?');
    println!("{} / {}", d.title, d.body);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목! / 본문?
(종료 코드 0)
```

```text
===== 소스: ex.rs =====
// 처방 3-b — 한 메서드가 두 칸을 한꺼번에 내준다
struct Doc { title: String, body: String }

impl Doc {
    fn parts_mut(&mut self) -> (&mut String, &mut String) {
        (&mut self.title, &mut self.body)
    }
}

fn main() {
    let mut d = Doc { title: String::from("제목"), body: String::from("본문") };
    let (t, b) = d.parts_mut();
    t.push('!');
    b.push('?');
    println!("{} / {}", d.title, d.body);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
제목! / 본문?
(종료 코드 0)
```

★★ **3-b 가 이 주제에서 가장 쓸모 있는 한 수**다. 메서드가 막는 이유가 **시그니처**니까,
**시그니처를 「둘을 같이 내준다」로 바꾸면** 된다. 캡슐화를 안 깨고 푸는 유일한 길이다.

```text
   왜 3-a 는 되고 3-b 가 필요한가

   d.title_mut()      시그니처: &mut self  ──▶ 검사기가 보는 것: d 전체
   &mut d.title       필드 경로            ──▶ 검사기가 보는 것: d.title 칸 하나
   d.parts_mut()      시그니처: &mut self 를 받아 두 칸을 내준다
                                          ──▶ 반환 타입이 「겹치지 않는 둘」을 약속한다
```

### (4) 전형 4 — `&mut self` 에서 값을 꺼낸다

**언제 쓰나** — 버퍼를 비우면서 내용을 돌려주는 메서드를 쓸 때.

```text
===== 소스: ex.rs =====
// 전형 4 — &mut self 에서 값을 꺼내려 한다
struct Buf { data: String }

impl Buf {
    fn take_all(&mut self) -> String {
        self.data
    }
}

fn main() {
    let mut b = Buf { data: String::from("내용") };
    println!("{} / 남은 것 {:?}", b.take_all(), b.data);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0507]: cannot move out of `self.data` which is behind a mutable reference
 --> ex.rs:6:9
  |
6 |         self.data
  |         ^^^^^^^^^ move occurs because `self.data` has type `String`, which does not implement the `Copy` trait
  |
help: consider cloning the value if the performance cost is acceptable
  |
6 |         self.data.clone()
  |                  ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0507`.
```

- **E0507** — 「빌린 것 뒤에 있는 값을 옮길 수 없다」. 옮기면 **`self` 에 구멍이 생긴다.**
- `&mut self` 는 **빌린 것**이다. 빌린 물건에서 부품을 빼 가면 돌려줄 때 물건이 온전하지 않다.
- 컴파일러는 `clone()` 을 권하지만, **비우는 게 목적이면 `mem::take` 가 정답**이다.

```text
===== 소스: ex.rs =====
// 처방 4 — mem::take 가 빈 값을 두고 알맹이를 꺼낸다
use std::mem;

struct Buf { data: String }

impl Buf {
    fn take_all(&mut self) -> String {
        mem::take(&mut self.data)
    }
    fn replace_with(&mut self, s: String) -> String {
        mem::replace(&mut self.data, s)
    }
}

fn main() {
    let mut b = Buf { data: String::from("내용") };
    let got = b.take_all();
    println!("꺼낸 것 {:?} / 남은 것 {:?}", got, b.data);
    let old = b.replace_with(String::from("새 내용"));
    println!("밀려난 것 {:?} / 지금 {:?}", old, b.data);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
꺼낸 것 "내용" / 남은 것 ""
밀려난 것 "" / 지금 "새 내용"
(종료 코드 0)
```

| 함수 | 자리에 무엇을 두나 | 요구 조건 | 안정화 |
|---|---|---|---|
| `mem::take(&mut x)` | **`Default::default()`** | `T: Default` | 1.40.0 |
| `mem::replace(&mut x, new)` | **내가 준 값** | 없음 | 1.0.0 |
| `mem::swap(&mut a, &mut b)` | 서로의 값 | 없음 | 1.0.0 |

★ **셋 다 「구멍을 안 내고 옮기는」 같은 일**을 한다. `take` 는 `replace(x, Default::default())` 의 줄임이다.

### (5) 전형 5·6·7 — 옮기기·대입·클로저

**언제 쓰나** — 빌림을 잡아 둔 채로 원본을 건드릴 때. 세 모양이 번호만 다르다.

```text
===== 소스: ex.rs =====
// 전형 6 — 빌린 채로 원본을 옮긴다
fn consume(s: String) -> usize { s.len() }

fn main() {
    let s = String::from("가나다");
    let r = &s;
    let n = consume(s);
    println!("{} {}", r, n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0505]: cannot move out of `s` because it is borrowed
 --> ex.rs:7:21
  |
5 |     let s = String::from("가나다");
  |         - binding `s` declared here
6 |     let r = &s;
  |             -- borrow of `s` occurs here
7 |     let n = consume(s);
  |                     ^ move out of `s` occurs here
8 |     println!("{} {}", r, n);
  |                       - borrow later used here
  |
help: consider cloning the value if the performance cost is acceptable
  |
6 |     let r = &s.clone();
  |               ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0505`.
```

```text
===== 소스: ex.rs =====
// 전형 7 — 빌린 채로 원본에 대입한다
fn main() {
    let mut s = String::from("가나다");
    let r = &s;
    s = String::from("라마바");
    println!("{}", r);
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: variable does not need to be mutable
 --> ex.rs:3:9
  |
3 |     let mut s = String::from("가나다");
  |         ----^
  |         |
  |         help: remove this `mut`
  |
  = note: `#[warn(unused_mut)]` (part of `#[warn(unused)]`) on by default

error[E0506]: cannot assign to `s` because it is borrowed
 --> ex.rs:5:5
  |
4 |     let r = &s;
  |             -- `s` is borrowed here
5 |     s = String::from("라마바");
  |     ^ `s` is assigned to here but it was already borrowed
6 |     println!("{}", r);
  |                    - borrow later used here

warning: value assigned to `s` is never read
 --> ex.rs:5:5
  |
5 |     s = String::from("라마바");
  |     ^
  |
  = help: maybe it is overwritten before being read?
  = note: `#[warn(unused_assignments)]` (part of `#[warn(unused)]`) on by default

error: aborting due to 1 previous error; 2 warnings emitted

For more information about this error, try `rustc --explain E0506`.
```

★ **경고도 출력이다.** `unused_mut` 이 붙은 것이 힌트다 — 컴파일러는 **대입이 성립하지 않는다고 이미 보고** 있다.

```text
===== 소스: ex.rs =====
// 전형 8 — 클로저가 환경을 잡은 채로 원본을 만진다
fn main() {
    let mut v = vec![1, 2, 3];
    let show = || println!("{:?}", v);
    v.push(4);
    show();
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:5
  |
4 |     let show = || println!("{:?}", v);
  |                --                  - first borrow occurs due to use of `v` in closure
  |                |
  |                immutable borrow occurs here
5 |     v.push(4);
  |     ^^^^^^^^^ mutable borrow occurs here
6 |     show();
  |     ---- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

- ★ 클로저는 「**환경을 빌린 값**」이다. 라벨 `first borrow occurs due to use of v in closure` 가 그것을 말한다.\
  `show` 를 만든 줄에서 빌림이 시작되고 **`show()` 를 부르는 줄까지** 산다.
- **열쇠는 셋 다 같다** — **마지막 사용을 앞으로 옮기거나, 블록으로 구간을 닫거나, `clone` 한다.**\
  클로저 쪽은 `move ||` 로 **아예 소유를 넘기는** 길이 하나 더 있다(목록의 **34번 주제**).

| 번호 | 무엇을 했나 | 한 줄 |
|---|---|---|
| **E0505** | 빌린 채로 **옮겼다** | `consume(s)` |
| **E0506** | 빌린 채로 **대입했다** | `s = ...` |
| **E0502** | 빌린 채로 **가변 빌림**을 만들었다 | `v.push(4)` |

★ 셋이 같은 집안이다 — **「대출 중인 물건을 건드렸다」**. `later used here` 줄만 앞으로 옮기면 대개 풀린다.

### (6) ★★★ 같은 모양인데 하나는 통과한다 — 「거부 = 위험」이 아니다

**언제 쓰나** — 「이건 원래 안 되는 패턴」이라고 외우기 전에.

「`get_mut` 으로 보고 없으면 `insert`」는 **안 되는 패턴**으로 널리 알려져 있다. **던져 봤다.**

```text
===== 소스: ex.rs =====
// 전형 5 — 「있으면 고치고 없으면 넣기」를 get_mut 로 쓴다
use std::collections::HashMap;

fn main() {
    let mut counts: HashMap<&str, i32> = HashMap::new();
    match counts.get_mut("가") {
        Some(c) => *c += 1,
        None => { counts.insert("가", 1); }
    }
    println!("{:?}", counts);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
{"가": 1}
(종료 코드 0)
```

★★ **통과한다.** NLL 이 `Some` 갈래의 빌림을 **그 갈래 안에서 끝난 것**으로 보기 때문이다.
**「이 패턴은 안 된다」는 전제가 뒤집혔다.**

빌림이 **함수 밖으로 나가는 순간** 같은 모양이 막힌다.

```text
===== 소스: ex.rs =====
// 같은 모양인데 빌림이 함수 밖으로 나가면 — 갈래 하나에서만 반환해도 전체가 막힌다
use std::collections::HashMap;

fn bump<'m>(counts: &'m mut HashMap<&'static str, i32>, k: &'static str) -> &'m i32 {
    match counts.get_mut(k) {
        Some(c) => { *c += 1; c }
        None => { counts.insert(k, 1); counts.get(k).unwrap() }
    }
}

fn main() {
    let mut m: HashMap<&'static str, i32> = HashMap::new();
    println!("{}", bump(&mut m, "가"));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `*counts` as mutable more than once at a time
 --> ex.rs:7:19
  |
4 | fn bump<'m>(counts: &'m mut HashMap<&'static str, i32>, k: &'static str) -> &'m i32 {
  |         -- lifetime `'m` defined here
5 |     match counts.get_mut(k) {
  |           ------ first mutable borrow occurs here
6 |         Some(c) => { *c += 1; c }
  |                               - returning this value requires that `*counts` is borrowed for `'m`
7 |         None => { counts.insert(k, 1); counts.get(k).unwrap() }
  |                   ^^^^^^ second mutable borrow occurs here

error[E0502]: cannot borrow `*counts` as immutable because it is also borrowed as mutable
 --> ex.rs:7:40
  |
4 | fn bump<'m>(counts: &'m mut HashMap<&'static str, i32>, k: &'static str) -> &'m i32 {
  |         -- lifetime `'m` defined here
5 |     match counts.get_mut(k) {
  |           ------ mutable borrow occurs here
6 |         Some(c) => { *c += 1; c }
  |                               - returning this value requires that `*counts` is borrowed for `'m`
7 |         None => { counts.insert(k, 1); counts.get(k).unwrap() }
  |                                        ^^^^^^ immutable borrow occurs here

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0499, E0502.
For more information about an error, try `rustc --explain E0499`.
```

- 갈린 것은 모양이 아니라 「**빌림이 반환값이 되느냐**」다. 6번 줄 라벨이 그것을 말한다 —\
  `returning this value requires that *counts is borrowed for 'm`.
- ★★★ **거부를 두 갈래로 나눠 읽는다.**

| 유형 | 무엇인가 | 예 | 처방 |
|---|---|---|---|
| **A — 정말 위험** | 통과시키면 메모리 안전이 깨진다 | (1) 순회 중 `push` | **설계를 고친다** |
| **B — 증명 못 했을 뿐** | 안전한데 검사기가 못 본다 | (2) `v[0]`·`v[2]` · (6) 반환 갈래 | **같은 뜻의 다른 표현**을 찾는다 |

- **B 유형은 「내 코드가 틀렸다」가 아니다.** `split_at_mut` 처럼 **std 가 미리 열쇠를 만들어 둔** 자리가 많다.
- `entry` API 가 (6)의 열쇠다 — **탐색 한 번으로 「없으면 넣고 있으면 고치기」를 한다.**

```text
===== 소스: ex.rs =====
// 처방 5 — entry 는 한 번의 탐색으로 끝난다
use std::collections::HashMap;

fn main() {
    let mut counts: HashMap<&str, i32> = HashMap::new();
    *counts.entry("가").or_insert(0) += 1;
    *counts.entry("가").or_insert(0) += 1;
    *counts.entry("나").or_insert(0) += 1;
    // ★ HashMap 의 순회 순서는 실행마다 바뀐다 — 키로 직접 읽는다
    println!("가={} 나={}", counts["가"], counts["나"]);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가=2 나=1
(종료 코드 0)
```

> ★★ **처음에는 `println!("{:?}", counts)` 로 적었다가 제출 전 재대조에서 걸렸다.**\
> 한 번은 `{"가": 2, "나": 1}`, 다시 던지니 `{"나": 1, "가": 2}` 였다.\
> **같은 바이너리를 20번 돌려 12 대 8** 로 갈렸다 — `HashMap` 의 순회 순서는 **실행마다 바뀐다**\
> (std 가 `RandomState` 로 해시 씨앗을 실행마다 새로 잡는다 — std 문서가 **순회 순서를 보장하지 않는다**고 못 박는다).\
> 그래서 **키로 직접 읽는 판**으로 바꿨다.\
> ★ 「세 판 돌려서 같았다」로는 절대 못 잡는다 — 순서가 걸린 출력은 **근거로 쓰지 않는다**(목록의 **39번 주제**).

★ `entry` 는 **빌림을 하나로 합쳐** 준다 — 「찾기」와 「넣기」가 한 빌림 안에서 끝나니 겹칠 일이 없다.
자세한 것은 목록의 **39번 주제**.

### (7) 전형 9 — 루프에서 `&mut` 를 밖에 모은다

**언제 쓰나** — 여러 원소의 가변 참조를 한 자료구조에 담고 싶을 때.

```text
===== 소스: ex.rs =====
// 전형 12 — 루프에서 &mut 를 밖에 모아 둔다
fn main() {
    let mut v = vec![1, 2, 3];
    let mut held: Vec<&mut i32> = Vec::new();
    for i in 0..v.len() {
        held.push(&mut v[i]);
    }
    for r in held { *r += 1; }
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `v` as mutable more than once at a time
 --> ex.rs:6:24
  |
6 |         held.push(&mut v[i]);
  |         ----           ^ `v` was mutably borrowed here in the previous iteration of the loop
  |         |
  |         first borrow used here, in later iteration of loop

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
```

- ★ 라벨이 **`in the previous iteration of the loop`** 다. 한 줄에서 난 충돌이 아니라 **반복 사이**의 충돌이다.\
  10번·12번에서 못 본 모양이라 이 주제에서 처음 만난다.
- 열쇠는 **`iter_mut`** — 컬렉션을 **한 번만** 빌리고, 그 안에서 원소들을 겹치지 않게 쪼개 준다.

```text
===== 소스: ex.rs =====
// 처방 12 — iter_mut 는 컬렉션을 한 번만 빌린다
fn main() {
    let mut v = vec![1, 2, 3];
    let held: Vec<&mut i32> = v.iter_mut().collect();
    for r in held { *r += 1; }
    println!("{:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[2, 3, 4]
(종료 코드 0)
```

★ **`&mut i32` 를 `Vec` 에 담는 것 자체는 합법**이다. 막힌 것은 **만드는 방법**이었다.
(2)의 `split_at_mut` 과 **같은 원리** — std 가 「겹치지 않음」을 대신 보장한다.

### (8) 전형 10 — 자기 자신을 가리키는 구조체

**언제 쓰나** — 문자열과 그 안의 슬라이스를 한 구조체에 담고 싶을 때.

```text
===== 소스: ex.rs =====
// 전형 10 — 자기 자신을 가리키는 구조체
struct SelfRef {
    data: String,
    first: &str,
}

fn main() {
    let d = String::from("가나다");
    let s = SelfRef { first: &d[..3], data: d };
    println!("{} {}", s.data, s.first);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0106]: missing lifetime specifier
 --> ex.rs:4:12
  |
4 |     first: &str,
  |            ^ expected named lifetime parameter
  |
help: consider introducing a named lifetime parameter
  |
2 ~ struct SelfRef<'a> {
3 |     data: String,
4 ~     first: &'a str,
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0106`.
```

시키는 대로 `'a` 를 붙이면 **다음 벽**이 나온다.

```text
===== 소스: ex.rs =====
// 수명을 붙여 보면 — 같은 값을 빌리면서 옮기게 된다
struct SelfRef<'a> {
    data: String,
    first: &'a str,
}

fn main() {
    let d = String::from("가나다");
    let s = SelfRef { first: &d[..3], data: d };
    println!("{} {}", s.data, s.first);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0505]: cannot move out of `d` because it is borrowed
 --> ex.rs:9:45
  |
8 |     let d = String::from("가나다");
  |         - binding `d` declared here
9 |     let s = SelfRef { first: &d[..3], data: d };
  |                               -             ^ move out of `d` occurs here
  |                               |
  |                               borrow of `d` occurs here
  |
help: consider cloning the value if the performance cost is acceptable
  |
9 |     let s = SelfRef { first: &d.clone()[..3], data: d };
  |                                ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0505`.
```

- ★★ **이것은 A 유형**(정말 위험)이다. 구조체가 **이동하면** `first` 가 옛 주소를 가리키게 된다.\
  Rust 는 **값이 이동해도 참조가 살아 있어야 한다**는 전제 위에 서 있으므로 이 모양을 원리적으로 못 받는다.
- ★ **`'a` 를 붙이는 것으로는 못 푼다** — E0106 이 E0505 로 바뀔 뿐이다(12번 (5)와 같은 교훈).
- 열쇠는 **참조 대신 인덱스**를 담는 것이다. 이동해도 인덱스는 그대로다.

```text
===== 소스: ex.rs =====
// 처방 10 — 참조 대신 인덱스(범위)를 담는다
struct Sliced {
    data: String,
    first: std::ops::Range<usize>,
}

impl Sliced {
    fn first(&self) -> &str { &self.data[self.first.clone()] }
}

fn main() {
    let s = Sliced { data: String::from("가나다"), first: 0..3 };
    println!("{} / {}", s.data, s.first());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다 / 가
(종료 코드 0)
```

★ **참조를 「어디를 가리키나」에서 「몇 번째부터 몇 번째까지」로 바꾼 것**이다.
이 교체가 이 주제의 **열쇠 5**(자료구조 바꾸기)의 대표다 — 그래프·트리에서 `Rc` 대신 인덱스를 쓰는 설계도 같은 수다.

### (9) 전형 11 — 임시값에 참조를 걸어 둔다

**언제 쓰나** — 메서드 체인 끝에 `&`·`as_str()`·`[..]` 를 붙일 때.

★ **먼저 전제를 뒤집는다** — 「임시값에 참조를 걸면 무조건 죽는다」가 **틀렸다.**

```text
===== 소스: ex.rs =====
// 전형 11 — 임시값에 참조를 걸어 둔다
fn main() {
    let r = &String::from("가나다").len();
    let t = &String::from("라마바")[..];
    println!("{} {}", r, t);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
9 라마바
(종료 코드 0)
```

★★ **둘 다 통과한다.** `let` 의 초기화식에 직접 나온 임시값은 **수명이 `let` 과 같아지도록 연장**된다
(Reference 의 temporary lifetime extension). **연장되는 자리와 안 되는 자리를 가르는 것**이 이 절의 값이다.

연장이 **안 되는** 자리 — 임시값이 **메서드 호출을 한 번 거치면** 끝난다.

```text
===== 소스: ex.rs =====
// 전형 11 — 메서드 체인 끝에 참조를 남긴다
fn load() -> Option<String> { Some(String::from("가나다")) }

fn main() {
    let t: &str = load().unwrap().as_str();
    println!("{}", t);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0716]: temporary value dropped while borrowed
 --> ex.rs:5:19
  |
5 |     let t: &str = load().unwrap().as_str();
  |                   ^^^^^^^^^^^^^^^         - temporary value is freed at the end of this statement
  |                   |
  |                   creates a temporary value which is freed while still in use
6 |     println!("{}", t);
  |                    - borrow later used here
  |
help: consider using a `let` binding to create a longer lived value
  |
5 ~     let binding = load().unwrap();
6 ~     let t: &str = binding.as_str();
  |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0716`.
```

- **E0716** — 「임시값이 빌린 채로 죽었다」. `temporary value is freed at the end of this statement` 가 시점이다.
- ★ `help:` 가 **열쇠를 그대로 준다** — **임시값에 이름을 준다.**

```text
===== 소스: ex.rs =====
// 처방 11 — 임시값에 이름을 준다. 한 줄 늘어나는 대신 스코프가 생긴다
fn load() -> Option<String> { Some(String::from("가나다")) }

fn main() {
    let owned = load().unwrap();
    let t: &str = owned.as_str();
    println!("{}", t);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다
(종료 코드 0)
```

```text
   연장되나 안 되나

   let r = &String::from("가");        ── 연장된다.  &가 초기화식 맨 바깥에 있다
   let r = &String::from("가")[..];    ── 연장된다.  인덱싱은 확장 대상이다
   let t = load().unwrap().as_str();   ── 안 된다.   메서드 호출의 반환값은 새 임시값이다
                                                     그 임시값이 문장 끝에서 죽는다
```

★ **외울 것은 규칙이 아니라 진단이다** — `temporary value is freed at the end of this statement` 가 보이면 **이름을 준다.**

### (10) 전형 12 — `RefCell` 로 옮기면 검사가 런타임으로 간다

**언제 쓰나** — 컴파일 타임에 도저히 증명이 안 되는 공유 구조를 쓸 때.

★ 10번에서 「위반이 컴파일 에러에서 패닉으로 바뀐다」고만 적었다. **실측이 여기 있다.**

```text
===== 소스: ex.rs =====
// 전형 9 — RefCell 은 규칙을 런타임으로 옮긴다
use std::cell::RefCell;

fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    let a = c.borrow_mut();
    println!("첫 빌림 성공: {:?}", *a);
    let b = c.borrow_mut();      // ★ 컴파일은 통과한다
    println!("{:?}", *b);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
첫 빌림 성공: [1, 2, 3]

thread 'main' (2705109) panicked at ex.rs:8:15:
RefCell already borrowed
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

★★ **컴파일은 통과하고 첫 줄까지 출력된 뒤 죽는다.** 10번의 E0499 와 **같은 위반**인데
**발견 시점이 다르다** — 그리고 **첫 출력이 이미 나온 뒤**라 부분 실행된 상태로 죽는다.

반대 방향(가변 중 공유 요청)은 **문구가 다르다.**

```text
===== 소스: ex.rs =====
// RefCell — 가변 빌림 중에 공유 빌림을 요청하면 메시지가 다르다
use std::cell::RefCell;

fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    let _a = c.borrow_mut();
    let b = c.borrow();
    println!("{:?}", *b);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====

thread 'main' (2706968) panicked at ex.rs:7:15:
RefCell already mutably borrowed
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

| 요청 | 이미 걸린 것 | 패닉 문구(이 툴체인) |
|---|---|---|
| `borrow_mut()` | 가변 | `RefCell already borrowed` |
| `borrow()` | 가변 | `RefCell already mutably borrowed` |

열쇠는 **가드의 구간을 닫는 것**, 그리고 **물어보는 API**다.

```text
===== 소스: ex.rs =====
// RefCell 처방 — 빌림 구간을 블록으로 닫는다. try_borrow_mut 로 물어볼 수도 있다
use std::cell::RefCell;

fn main() {
    let c = RefCell::new(vec![1, 2, 3]);
    {
        let mut a = c.borrow_mut();
        a.push(4);
    }                                   // 여기서 가드가 풀린다
    println!("{:?}", c.borrow());
    let _held = c.borrow_mut();
    println!("두 번째 요청: {:?}", c.try_borrow_mut().is_ok());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
[1, 2, 3, 4]
두 번째 요청: false
(종료 코드 0)
```

- ★ `borrow()` 가 돌려주는 것은 참조가 아니라 **가드**(`Ref`/`RefMut`)다. **가드가 죽어야 빌림이 풀린다** —\
  그래서 NLL 이 아니라 **`Drop` 시점**(09번)이 기준이다. 블록이 다시 의미를 갖는 자리다.
- `try_borrow_mut()` 은 **패닉 대신 `Result`** 를 준다. 실측에서 `false` 가 나왔다 — **물어볼 수 있다.**
- ★★ **`RefCell` 은 마지막 열쇠다.** 컴파일 에러를 없애 주는 게 아니라 **런타임 위험으로 바꾼다.**\
  앞의 열쇠 다섯이 다 안 맞을 때만 쓴다. 자세한 것은 목록의 **42번 주제**.

### (11) ★ 같은 파일이 에디션에 따라 갈린다

**언제 쓰나** — `if let` 안에서 `borrow()`·`lock()` 같은 **가드를 만드는** 식을 쓸 때.

```text
===== 소스: ex.rs =====
// 에디션 차이 — if let 의 임시값이 else 갈래까지 사는가
use std::cell::RefCell;

fn main() {
    let c: RefCell<Option<i32>> = RefCell::new(None);
    if let Some(v) = *c.borrow() {
        println!("있음 {}", v);
    } else {
        *c.borrow_mut() = Some(7);        // 빌림 가드가 아직 살아 있나?
        println!("없음 -> 채웠다 {:?}", c);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0597]: `c` does not live long enough
  --> ex.rs:6:23
   |
 5 |     let c: RefCell<Option<i32>> = RefCell::new(None);
   |         - binding `c` declared here
 6 |     if let Some(v) = *c.borrow() {
   |                       ^---------
   |                       |
   |                       borrowed value does not live long enough
   |                       a temporary with access to the borrow is created here ...
...
12 | }
   | -
   | |
   | `c` dropped here while still borrowed
   | ... and the borrow might be used here, when that temporary is dropped and runs the destructor for type `Ref<'_, Option<i32>>`
   |
help: consider adding semicolon after the expression so its temporaries are dropped sooner, before the local variables declared by the block are dropped
   |
11 |     };
   |      +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0597`.
===== rustc --edition 2024 ex.rs -o ex =====
===== ./ex =====
없음 -> 채웠다 RefCell { value: Some(7) }
(종료 코드 0)
```

★★ **한 글자도 안 고친 같은 파일이 2021 에서 거부되고 2024 에서 통과해 실행된다.**
2024 에디션에서 `if let` 의 임시값 스코프가 바뀌었다(README 버전표의 항목).

- ★ **2021 에서는 컴파일 에러로 잡혔지만, 같은 코드가 `Mutex` 였다면 런타임 교착**이 될 자리다.\
  「거부가 선물인」 대표 사례다.
- **에디션을 안 밝히고 「이 코드는 안 된다」를 적으면 그 문장은 절반만 참이다.**

## 문법 — 형태와 규칙

### 형태 — 열쇠 여섯

```rust
use std::mem;
use std::cell::RefCell;

// 열쇠 1 — 순서: 마지막 사용을 앞으로 옮긴다 (NLL)
let a = &mut n; *a += 1; let b = &mut n;

// 열쇠 2 — 쪼개기: 필드 직접 · split_at_mut · 두 칸을 같이 내주는 메서드
let (t, b) = (&mut d.title, &mut d.body);
let (left, right) = v.split_at_mut(2);
fn parts_mut(&mut self) -> (&mut String, &mut String) { (&mut self.a, &mut self.b) }

// 열쇠 3 — 값만 가져오기: 인덱스 · Copy · clone
let b = v[2];              // Copy
let b = v[2].clone();      // 그 외

// 열쇠 4 — 구멍 안 내고 꺼내기
let old = mem::take(&mut self.data);            // Default 를 두고 꺼낸다
let old = mem::replace(&mut self.data, new);    // 내가 준 값을 두고 꺼낸다
mem::swap(&mut a, &mut b);

// 열쇠 5 — 자료구조 교체: 참조 대신 인덱스/범위
struct Sliced { data: String, first: std::ops::Range<usize> }

// 열쇠 6 — 런타임으로 옮기기 (마지막 수단)
let c = RefCell::new(v);
{ let mut g = c.borrow_mut(); g.push(4); }      // 가드 구간을 블록으로 닫는다
if let Ok(mut g) = c.try_borrow_mut() { g.push(5); }
```

### 금지 사례 — 던져서 받은 일곱

| 코드 | 에러 | 열쇠 |
|---|---|---|
| `for x in &v { v.push(..) }` | **E0502** | 인덱스 루프 · 읽기/쓰기 분리 · `retain` |
| `&mut v[0]` + `&mut v[2]` | **E0499** | `split_at_mut`(컴파일러가 직접 권함) |
| `d.title_mut()` + `d.body_mut()` | **E0499** | 필드 직접 · `parts_mut` |
| `fn take(&mut self) -> String { self.data }` | **E0507** | `mem::take` |
| `let r = &s; consume(s);` | **E0505** | 순서 · `clone` |
| `let r = &s; s = ...;` | **E0506** | 순서 |
| `let t = load().unwrap().as_str();` | **E0716** | 임시값에 이름 주기 |

### 에러 번호에서 열쇠로 — 진단 표

```text
   E0499  가변 둘이 겹쳤다          ──▶ 순서 · 쪼개기 · split_at_mut · iter_mut
   E0502  가변과 공유가 겹쳤다      ──▶ 순서 · 인덱스 루프 · entry
   E0505  빌린 채로 옮겼다          ──▶ 순서 · clone
   E0506  빌린 채로 대입했다        ──▶ 순서
   E0507  빌린 것에서 꺼냈다        ──▶ mem::take / replace / clone
   E0596  mut 이 아닌 것에 &mut     ──▶ let mut (10번·02번)
   E0716  임시값이 먼저 죽었다      ──▶ 임시값에 이름 주기
   E0106  수명 칸이 비었다          ──▶ 12번 주제
   패닉   RefCell already borrowed  ──▶ 가드 구간을 닫는다 · try_borrow_mut
```

## 어디서 틀리나

### 1. ★★★ 「거부됐으니 내 코드가 위험하다」

- **B 유형**(안전한데 증명 못 함)이 실제로 있다 — `&mut v[0]` + `&mut v[2]` 가 대표다.
- 가르는 법 — **「이 코드가 통과하면 어떤 메모리 사고가 나나」를 한 문장으로 댈 수 있나.**\
  못 대면 B 유형이고, **표현을 바꾸면 통과한다.**
- ★ B 유형에는 **std 가 이미 열쇠를 만들어 뒀다**(`split_at_mut`·`iter_mut`·`entry`). 내가 `unsafe` 를 쓸 자리가 아니다.

### 2. ★★ 「이 패턴은 원래 안 된다」를 외운다

- 실측: `match map.get_mut(k) { .. None => map.insert(..) }` 가 **함수 안에서는 통과했다**((6)).\
  막힌 것은 **빌림을 반환할 때**였다.
- ★ **「안 되는 패턴」이 아니라 「빌림이 어디까지 가나」로 기억한다.** 패턴 이름으로 외우면 반은 틀린다.

### 3. ★ 「`'a` 를 붙이면 자기 참조 구조체가 된다」

- E0106 이 **E0505 로 바뀔 뿐**이다((8)). 이건 **A 유형**이라 표기로 못 푼다.
- 열쇠는 **인덱스로 바꾸는 것**이다. 표준 라이브러리만으로는 자기 참조를 못 만든다.

### 4. 접근자 메서드를 만들어 놓고 막힌다

- `&mut self` 가 **전체를 잡는다.** 필드를 직접 짚거나 **두 칸을 같이 내주는 메서드**를 만든다((3)).
- ★ 라이브러리를 설계할 때 미리 생각할 일이다 — **`parts_mut` 같은 메서드를 처음부터 둔다.**

### 5. `mem::take` 를 `clone` 으로 때운다

- 컴파일러가 `clone()` 을 권해서 그대로 따르는 실수. **비우는 게 목적이면 `take` 가 맞다** — 할당이 없다.
- ★ **컴파일러의 `help:` 는 「컴파일을 통과시키는 법」이지 「올바른 설계」가 아니다.**

### 6. ★ 임시값이 연장되는 자리를 모른다

- 실측: `let r = &String::from("가").len();` 은 **통과한다**((9)). 「임시값 참조는 다 죽는다」가 틀렸다.
- 메서드 호출을 거치면 안 된다. **진단 문구를 기준으로 삼는다** — `freed at the end of this statement`.

### 7. `RefCell` 을 먼저 꺼낸다

- 컴파일 에러가 사라지니 **해결한 기분**이 든다. 실제로는 **런타임 패닉으로 미룬 것**이다((10)).
- ★ `RefCell` 은 열쇠 여섯 중 **마지막**이다. 앞의 다섯을 먼저 시도한다.

### 8. 에디션을 안 밝히고 결론을 적는다

- 실측: `if let` + `RefCell` 한 파일이 **2021 E0597 / 2024 통과**였다((11)).
- ★ `rustc` 의 **기본 에디션은 2015** 다. `--edition` 없이 잰 결과는 2021 의 근거가 아니다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| 순회 중 변경이 **막히는 것** | **언어** | E0502. 통과하면 진짜 위험(A 유형) |
| `IndexMut` 이 **전체를 빌리는 것** | **std 의 시그니처** | `fn index_mut(&mut self, ..)` — 언어가 아니라 **API 모양** |
| `&mut self` 메서드가 **전체를 잡는 것** | **언어**(시그니처가 계약) | (3)의 E0499 |
| **필드별 빌림**이 되는 것 | **언어** | (3)-a 통과 |
| `split_at_mut`·`iter_mut` 이 **겹치지 않음을 보장** | **std** | 내부는 `unsafe`, 표면은 안전 |
| `mem::take` 가 **`Default` 를 둔다** | **std** | `""` 가 남은 것을 실측 |
| `entry` 가 **한 빌림으로 끝나는 것** | **std API 설계** | (6) 통과 |
| ★ `get_mut`+`insert` 가 **함수 안에서 통과하는 것** | **현재 검사기(NLL)** | 실측. 옛 자료의 「안 된다」가 뒤집혔다 |
| ★ 같은 모양이 **반환하면 막히는 것** | **현재 검사기의 한계** | 언어가 금지한 게 아니다(12번 (7)) |
| 자기 참조 구조체가 **안 되는 것** | **언어**(이동 가능성이 전제) | E0505 — A 유형 |
| **임시값 수명 연장** | **언어** | Reference — Destructors. `let` 초기화식의 모양에 달렸다 |
| `RefCell` 위반이 **패닉인 것** | **std** | 규칙은 그대로, **검사 시점**만 런타임 |
| ★ `RefCell` 의 **패닉 문구** | **std 판** | `RefCell already borrowed` / `already mutably borrowed` — 판마다 바뀌어 왔다 |
| 패닉 **종료 코드 101** | **std 런타임** | 실측 |
| ★ **`HashMap` 순회 순서** | **std**(보장 없음) | 같은 바이너리 20회에 **12 대 8** 로 갈렸다 — 근거로 쓰지 않는다 |
| 패닉 메시지의 **스레드 id `(2705109)`** | **런타임** | 실행마다 바뀐다. 근거로 읽지 않는다 |
| **에러 번호**가 상황별로 갈리는 것 | **rustc 구현** | 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| `= help:` 가 **`split_at_mut` 을 권하는 것** | **rustc 진단 구현** | 유용하지만 **보장이 아니다** |
| `if let` 임시값 스코프 | **에디션**(2024에서 변경) | 같은 파일 2021 E0597 / 2024 통과 |

★★ **「검사기가 못 푼다」와 「언어가 금지한다」를 표에서도 갈라 적었다.**
앞엣것은 **rustc 판이 오르면 바뀔 수 있는 줄**이고, 뒤엣것은 안 바뀐다.

## 언제 쓰고 언제 안 쓰나

| 막힌 모양 | 첫 번째 열쇠 | 안 되면 |
|---|---|---|
| 빌림 둘의 **구간이 겹쳤다** | **마지막 사용을 앞으로** | 블록으로 감싸기 |
| **서로 다른 칸**을 만진다 | **필드를 직접 짚는다** | `parts_mut` · `split_at_mut` |
| 컬렉션 **원소 여럿**을 고친다 | **`iter_mut`** | `split_at_mut` · 인덱스 루프 |
| 순회하며 **지운다** | **`retain`** | `drain` (목록의 **38번 주제**) |
| 순회하며 **넣는다** | **읽기/쓰기 분리** | 인덱스 루프(길이 고정) |
| 맵에 **있으면 고치고 없으면 넣기** | **`entry`** | `contains_key` 선분리 |
| **값만** 필요하다 | **`Copy` 면 그냥 읽기** | `clone()` |
| `&mut self` 에서 **꺼낸다** | **`mem::take`** | `mem::replace` · `Option::take` |
| **자기 참조**가 필요하다 | **인덱스·범위로 바꾼다** | `Rc`+`Weak`(목록의 **41번 주제**) |
| **임시값**이 먼저 죽는다 | **이름을 준다** | 소유값으로 받는다 |
| 위의 어느 것도 안 맞는다 | ★ **`RefCell`**(마지막) | `Arc<Mutex<T>>`(스레드까지 가면) |

판단 규칙 두 줄.

- ★ **먼저 「이게 통과하면 무슨 사고가 나나」를 물어본다.** 대답이 나오면 설계를 고치고, 안 나오면 표현을 바꾼다.
- ★ **`clone()` 과 `RefCell` 은 마지막에 꺼낸다.** 둘 다 **문제를 없애지 않고 비용으로 바꾼다.**

## 핵심 문장

- ★★★ **거부에는 두 종류가 있다** — **정말 위험한 것**과 **검사기가 증명 못 한 것**. 처방이 다르다.
- **열쇠는 여섯** — 순서 바꾸기 · 쪼개기 · 값만 가져오기 · `mem::take` · 자료구조 교체 · `RefCell`.
- **에러 번호가 곧 열쇠 이름표**다 — E0499/E0502는 겹침, E0505/E0506/E0507은 옮김, E0716은 임시값.
- ★ **컴파일러가 열쇠를 대 주는 자리가 있다** — E0499 의 `= help: use .split_at_mut(position)`.
- **`&mut self` 메서드는 전체를 잡는다.** 필드를 직접 짚거나 **두 칸을 같이 내주는 메서드**를 만든다.
- ★★ **「이 패턴은 안 된다」를 외우지 마라** — `get_mut`+`insert` 는 **함수 안에서는 통과**한다.\
  갈리는 것은 패턴이 아니라 **빌림이 함수 밖으로 나가느냐**다.
- **임시값은 연장되기도 한다** — `let r = &String::from("가").len();` 은 통과한다.\
  메서드 호출을 거치면 안 된다. 기준은 진단 문구 `freed at the end of this statement`.
- ★ **`RefCell` 은 규칙을 없애지 않는다** — 컴파일 에러를 **런타임 패닉**으로 옮긴다(종료 코드 101).
- **`'a` 로는 자기 참조 구조체를 못 만든다** — E0106 이 E0505 로 바뀔 뿐이다.
- ★ **`rustc` 의 기본 에디션은 2015** 다. 같은 파일이 2021 에서 거부되고 2024 에서 실행된 실측이 있다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 11번)
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`·별칭 규칙) — ★ **직접 선행**.\
  **그쪽은** 규칙 자체(E0499·E0502·NLL·재빌림), **여기는** 그 규칙에 걸리는 **코드와 처방**이다.\
  10번이 「11번에 실측이 있다」고 적은 **`RefCell` 패닉**이 (10)에 있다
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기 `'a`) — **형제**.\
  **그쪽은** 수명을 **적는 법**, **여기는** 막혔을 때 **손이 어디로 가나**다.\
  (6)의 반환 갈래 이야기는 그쪽 (7)이 정본이다
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — `RefCell` 가드가 **언제 풀리나**가 거기다.\
  `Copy` 면 빌리지 말고 베끼라는 판단도 거기서 온다
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — E0505·E0507 의 뿌리
- 목록의 **38번 주제**(`Vec` API — `retain`·`drain`) · **39번 주제**(`HashMap` 의 `entry`) ·\
  **37번 주제**(`iter`/`iter_mut`/`into_iter`) · **34번 주제**(클로저와 `move`) ·\
  **41번 주제**(`Rc`/`Weak`) · **42번 주제**(`RefCell` 내부 가변성 — ★ 정본) ·\
  **44번 주제**(`mem::replace`/`take` — ★ 정본) · **56번 주제**(`unsafe` 와 안전한 표면)
- [`../../언어-특성/README.md`](../../언어-특성/README.md) §3·§7 — **그쪽은** 「왜 이 규칙인가」와 **청구서**(설계 반복의 비용),\
  **여기는** 「그 청구서가 날아왔을 때 무엇을 하나」다
- [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md) — 모델의 **역사**는 거기

## 용어 풀이

- **전형(pattern)** — 다른 코드인데 **같은 이유로 같은 에러**가 나는 모양.
- **분할 빌림(split borrow)** — 한 값의 **서로 다른 칸**을 각각 따로 빌리는 것. 필드 경로에서만 된다.
- **`split_at_mut`** — 슬라이스를 **겹치지 않는 두 조각**으로 가르고 각각 `&mut` 를 준다.
- **`mem::take`** — 자리에 `Default` 값을 두고 알맹이를 꺼낸다. `replace(x, Default::default())` 의 줄임.
- **`entry` API** — 맵에서 「찾기」와 「넣기」를 **한 빌림 안에서** 끝내는 표면.
- **임시값(temporary)** — 이름 없는 중간 값. `let` 초기화식의 모양에 따라 **수명이 연장되기도** 한다.
- **임시값 수명 연장(temporary lifetime extension)** — 그 연장 규칙. Reference 의 Destructors 절.
- **내부 가변성(interior mutability)** — `&T` 만으로 속을 고치게 해 주는 장치. `Cell`·`RefCell`.
- **가드(guard)** — `borrow()` 가 돌려주는 `Ref`/`RefMut`. **가드가 죽어야 빌림이 풀린다.**
- **A 유형 / B 유형** — ★ 이 문서의 용어. **정말 위험해서 막힌 것** / **안전한데 증명 못 해 막힌 것**.

---

## 더 들어가면

- ★ **B 유형을 줄이는 작업이 Rust 팀의 숙제**다. NLL(1.31/1.36)이 한 번 크게 줄였고,
  (6)의 모양은 **Polonius** 라는 이름으로 계속 다뤄지고 있다. **이 문서는 안정판에서 되는 것만 실었다.**
- **`split_at_mut` 은 `unsafe` 로 구현돼 있다.** 「검사기가 증명 못 하는 것을 **사람이 한 번 증명하고 안전한 표면으로 가둔다**」가
  std 가 반복해서 쓰는 수법이고, 그 경계 설계가 목록의 **56번 주제**다.
- **`Option::take()`** 는 `mem::take` 의 특수형이다 — `Option<T>` 를 `None` 으로 만들고 알맹이를 꺼낸다.\
  연결 리스트·트리에서 노드를 떼어 낼 때 이것 하나로 대부분 풀린다(목록의 **40번 주제**).
- ★ **인덱스로 바꾸는 설계**는 그래프·트리에서 정석이다. 참조 대신 `usize` 를 담으면
  **자기 참조도 되고 `Clone` 도 되고 직렬화도 된다.** 대가는 **인덱스가 가리키는 것을 언어가 안 지켜 준다**는 점이다
  (지운 자리의 인덱스를 들고 있어도 컴파일러가 안 막는다 — **안전하지만 틀릴 수 있다**).
- **스레드까지 가면 같은 구조가 한 층 올라간다** — `RefCell` 자리에 `Mutex`, 패닉 자리에 **교착**이 온다.\
  `Mutex` 는 `try_lock` 이 `try_borrow_mut` 과 같은 자리를 맡는다(목록의 **52번 주제**).
- ★ **막혔을 때 가장 싼 진단은 「마지막 사용이 어디인가」를 보는 것**이다(10번).\
  이 문서의 열쇠 여섯 중 첫 번째가 그것이고, 실측에서도 **가장 자주 통했다.**
