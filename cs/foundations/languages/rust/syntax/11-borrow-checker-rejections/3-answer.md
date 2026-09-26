# rust/syntax/11 — 빌림 검사기가 거부하는 전형 코드와 고치는 법 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고·패닉은 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 특별히 적지 않은 한 이 문서의 결과는 **2021** 기준이고,\
> 에디션이 갈리는 자리는 **10번 답**에 따로 적었다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ **패닉 메시지의 스레드 id(`(2705109)` 같은 숫자)는 실행마다 바뀐다.** 근거로 읽을 칸이 아니다.\
> ★ 이 주제의 고유 창은 **거부된 판과 통과한 판을 나란히 던지는 것**이다 — 열쇠가 맞는지는 **통과한 판의 출력**으로만 확인된다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 거부된다 — E0502. 그리고 이건 진짜 위험이다

**출력**

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

**왜 그런가**

- **E0502**. `&v` 가 만든 **반복자**가 루프 끝까지 그 빌림을 쓰기 때문이다.
- ★ **같은 줄(4)에 라벨이 둘** 붙었다 — `occurs here` 와 `later used here` 가 **같은 `&v`** 에 붙었다.\
  10번에서 배운 「마지막 사용」이 **루프 전체**로 늘어난 모양이다. 보통은 두 줄에 나뉘어 붙는다.
- ★★ **A 유형**(정말 위험)이다. 근거 — `push` 가 용량을 넘기면 `Vec` 이 **재할당**되고,\
  `x` 가 가리키던 자리가 해제된다. C++ 의 iterator invalidation 과 **같은 사고**다.\
  「이게 통과하면 무슨 사고가 나나」에 **한 문장으로 답이 나온다** — 그게 A 유형의 판별법이다.
- **고치는 길 셋.** 전부 「빌림 구간을 겹치지 않게」 만든 것이고 방법만 다르다.

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

★ 1-a 와 1-b 가 **같은 값**(`[1, 2, 3, 10, 30]`)을 낸다는 것도 같이 확인했다 — 열쇠를 바꿔도 뜻이 안 변해야 한다.

### 2. ★★ 거부된다 — E0499. 그런데 이건 B 유형이다

**출력**

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

**왜 그런가**

- **인덱스가 겹치지 않는데도 거부된다. E0499.**
- ★★ 판정에 쓴 것은 **인덱스 값이 아니라 `IndexMut` 의 시그니처**다 — `fn index_mut(&mut self, ..)`.\
  **`&mut self` 는 컬렉션 전체**다. 게다가 인덱스는 **런타임 값**이라 컴파일러가 「겹치지 않는다」를 증명할 수 없다.
- ★ `= help:` 줄이 **열쇠 이름을 그대로 준다** —\
  **`use .split_at_mut(position) to obtain two mutable non-overlapping sub-slices`**.
- ★★★ **1번과 성격이 다르다.**

| | 1번 (순회 중 `push`) | 2번 (`v[0]`·`v[2]`) |
|---|---|---|
| 통과시키면? | **재할당으로 댕글링** — 사고가 난다 | **아무 일도 안 난다** — 안전하다 |
| 분류 | **A 유형** — 정말 위험 | **B 유형** — 증명 못 했을 뿐 |
| 처방 | **설계를 고친다** | **같은 뜻의 다른 표현**을 찾는다 |

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

- 값만 필요하면 더 싼 열쇠가 있다 — `i32` 는 `Copy` 니까 **빌리지 말고 베낀다**(09번).

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

### 3. ★★ (나)가 통과한다 — 갈린 것은 시그니처다

**출력**

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

**왜 그런가**

- **(나)가 통과한다.** 에러가 짚는 것은 **`d`** 다 — `-` 와 `^` 가 전부 `d` 에 붙었다.
- ★ 이유는 **시그니처**다. `fn title_mut(&mut self)` 의 `&mut self` 는 **`Doc` 전체**다.\
  검사기는 **`title_mut` 의 몸통을 안 읽는다** — 몸통은 `self.title` 만 만지는데도 그렇다(10번의 결론).
- ★★ **캡슐화를 안 깨고 푸는 길이 있다** — **반환 타입을 「겹치지 않는 둘」로 바꾼다.**

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

```text
   검사기가 보는 것

   d.title_mut()      시그니처: &mut self            ──▶ d 전체
   &mut d.title       필드 경로                      ──▶ d.title 칸 하나
   d.parts_mut()      &mut self 를 받아 두 칸을 내준다 ──▶ 반환 타입이 「겹치지 않는 둘」을 약속
```

★ **막는 것이 시그니처니까 푸는 것도 시그니처다.** 라이브러리를 설계할 때 미리 생각할 일이다.

### 4. ★ 거부된다 — E0507. 그리고 컴파일러의 조언은 이 목적에 안 맞다

**출력**

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

**왜 그런가**

- **E0507**, 이유 구절은 **`which is behind a mutable reference`** 다.\
  `&mut self` 는 **빌린 것**이고, 빌린 물건에서 부품을 빼 가면 **돌려줄 때 구멍이 난다.**
- ★★ 컴파일러는 `clone()` 을 권하지만 **이 목적에는 안 맞는다.** 목적이 「비우면서 꺼내기」인데
  `clone()` 은 **비우지 않고 할당만 한 번 더 한다.**\
  ★ **`help:` 는 「컴파일을 통과시키는 법」이지 「올바른 설계」가 아니다.**
- 맞는 답은 `mem::take` 다.

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

- **`남은 것 ""`** 이 `take` 가 무엇을 뒀는지 보여 준다 — **`Default::default()`**, 즉 빈 `String` 이다.
- **밀려난 것 `""`** 는 그 직전 `take` 가 남겨 둔 빈 값이다. 두 줄이 이어져 읽힌다.

| 함수 | 자리에 무엇을 두나 | 요구 경계 | 안정화 |
|---|---|---|---|
| `mem::take(&mut x)` | **`Default::default()`** | **`T: Default`** | 1.40.0 |
| `mem::replace(&mut x, new)` | **내가 준 값** | 없음 | 1.0.0 |
| `mem::swap(&mut a, &mut b)` | 서로의 값 | 없음 | 1.0.0 |

★ `take` 는 `replace(x, Default::default())` 의 줄임이다 — 그래서 **`T: Default` 가 필요**하다.

### 5. ★★★ (가)는 통과한다 — 전제가 뒤집힌 자리다

**출력**

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

**왜 그런가**

- ★★★ **(가)는 통과한다.** 「`get_mut` 으로 보고 없으면 `insert`」가 **안 되는 패턴**으로 널리 알려져 있지만,
  **함수 안에서 끝나면 NLL 이 푼다.** 이 전제는 **던져 보고 뒤집혔다.**
- 갈린 원인은 **패턴의 모양이 아니다** — **빌림이 함수 밖으로 나가느냐**다.\
  6번 줄 라벨이 그것을 말한다: **`returning this value requires that *counts is borrowed for 'm`**.\
  `Some` 갈래가 빌림을 내보내니 구간이 **`'m` 전체**로 고정되고, `None` 갈래의 두 호출이 그 안에서 충돌한다.
- **에러는 두 개**다 — `insert`(가변)에서 **E0499**, `get`(공유)에서 **E0502**. 한 줄에서 둘이 난다.
- **표준 열쇠는 `entry`** 다. 「찾기」와 「넣기」를 **한 빌림 안에서** 끝낸다.

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
> ★ 「세 판 돌려서 같았다」로는 절대 못 잡는다 — 순서가 걸린 출력은 **근거로 쓰지 않는다**([목록의 **39번 주제**](../39-hashmap-vs-btreemap-and-entry-api/)).

★ **교훈** — 「이 패턴은 안 된다」로 외우면 반은 틀린다. **「빌림이 어디까지 가나」로 기억한다.**\
반환하는 판의 이야기는 [**12번 주제**](../12-lifetime-annotations-and-elision/)의 (7)이 정본이다.

### 6. ★ 컴파일은 통과하고 — 첫 줄을 출력한 뒤 죽는다

**출력**

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

**왜 그런가**

- **컴파일은 통과한다.** 같은 위반(10번의 E0499)인데 **발견 시점이 다르다.**
- ★ **출력이 하나 나온다** — `첫 빌림 성공: [1, 2, 3]`.\
  **부분 실행된 상태로 죽는다**는 것이 컴파일 에러와의 결정적 차이다.
- **종료 코드는 101** 이다(패닉의 표준 종료 코드).
- 반대 방향은 **문구가 다르다.**

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

★ **이 문구는 std 판에 달렸다.** 바뀌어 온 이력이 있으므로 **문구가 아니라 「패닉한다」를 기억**한다.

- 열쇠는 **가드 구간을 닫는 것**과 **물어보는 API**다.

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

★ `borrow()` 가 주는 것은 참조가 아니라 **가드**(`Ref`/`RefMut`)다. **가드가 `Drop` 될 때** 빌림이 풀리므로
NLL 이 아니라 **09번의 해제 시점**이 기준이다 — **블록이 다시 의미를 갖는 자리**다.

### 7. 앞엣것은 통과하고 뒤엣것은 E0716 이다

**출력**

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

**왜 그런가**

- ★★ **앞엣것은 통과한다** — `9 라마바`. 「임시값에 참조를 걸면 무조건 죽는다」는 **틀렸다.**\
  `let` 초기화식에 직접 나온 임시값은 **수명이 `let` 과 같아지도록 연장**된다(temporary lifetime extension).
- **갈리는 이유** — 연장은 **초기화식의 모양**을 보고 적용된다.\
  `load().unwrap()` 은 **메서드 호출의 반환값**이고, 거기에 `.as_str()` 이 또 붙었다.\
  그 중간 임시값은 **연장 대상이 아니라 문장 끝에서 죽는다.**

```text
   let r = &String::from("가");        ── 연장된다.  &가 초기화식 맨 바깥에 있다
   let r = &String::from("가")[..];    ── 연장된다.  인덱싱은 확장 대상이다
   let t = load().unwrap().as_str();   ── 안 된다.   메서드 호출의 반환값은 새 임시값이고
                                                     그 임시값이 문장 끝에서 죽는다
```

- **E0716**, 자유 시점은 **`temporary value is freed at the end of this statement`** — **그 문장의 끝**이다.
- ★ **열쇠를 컴파일러가 직접 준다** — `consider using a let binding to create a longer lived value`.\
  고친 코드까지 두 줄로 보여 준다.

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

★ **외울 것은 연장 규칙이 아니라 진단 문구다** — `freed at the end of this statement` 가 보이면 **이름을 준다.**

### 8. 반복 사이의 충돌이다 — E0499

**출력**

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

**왜 그런가**

- 매 회전마다 `&mut v[i]` 가 **컬렉션 전체**를 빌리는데(2번과 같은 이유), 그 빌림이 `held` 에 **쌓여** 살아남는다.
- ★ **라벨이 다른 점** — **`in the previous iteration of the loop`** · **`in later iteration of loop`**.\
  지금까지의 진단은 전부 **줄 번호 둘** 사이의 충돌을 짚었는데, 이것은 **같은 줄과 자기 자신** 사이다.\
  10·12번에서 못 본 모양이라 여기서 처음 만난다.
- ★★ **`Vec<&mut i32>` 라는 타입 자체는 합법**이다. 막힌 것은 **만드는 방법**이었다.\
  `iter_mut` 으로 만들면 같은 타입이 그대로 통과한다.

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

★ `iter_mut` 은 **컬렉션을 한 번만 빌리고** 그 안에서 원소들을 **겹치지 않게 쪼개** 준다.
(2)의 `split_at_mut` 과 **같은 원리** — std 가 「겹치지 않음」을 대신 보장한다.

### 9. E0106 → `'a` 를 붙이면 E0505. A 유형이라 표기로는 못 푼다

**출력**

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

**왜 그런가**

- 처음은 **E0106**, `'a` 를 붙이면 **E0505** 로 바뀐다. **통과하지 않는다.**\
  ★ 12번 (5)의 「E0106 이 E0515 로 바뀔 뿐」과 **같은 교훈**이다 — `'a` 는 칸을 채울 뿐이다.
- ★★ **A 유형인 이유를 한 문장으로** — **구조체가 이동하면 `first` 가 옛 주소를 가리키게 된다.**\
  Rust 에서 값은 **언제든 이동할 수 있다**는 것이 전제이므로, 이 모양은 원리적으로 못 받는다.\
  (컴파일러가 권하는 `d.clone()` 은 **자기 참조가 아니라 다른 값을 가리키는** 구조체를 만든다 — 목적이 달라진다.)
- 표준 라이브러리만으로 푸는 길은 **참조 대신 인덱스(범위)를 담는 것**이다.

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

★ **「어디를 가리키나」를 「몇 번째부터 몇 번째까지」로 바꾼 것**이다. 이동해도 인덱스는 그대로다.
대가는 **인덱스의 유효성을 언어가 안 지켜 준다**는 점이다 — 안전하지만 **틀릴 수는 있다.**

### 10. 2021에서 E0597, 2024에서 통과해 실행된다

**출력**

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

**왜 그런가**

- **한 글자도 안 고친 같은 파일**이다. 2021 에서는 **E0597**, 2024 에서는 **통과해 실행**된다.\
  2024 에디션에서 `if let` 의 **임시값 스코프**가 바뀌었다(README 버전표의 항목).
- 진단이 짚는 것은 **`Ref<'_, Option<i32>>` 가드**다 — `runs the destructor for type Ref<...>` 라고 이름까지 댄다.\
  2021 에서는 그 가드가 **`else` 갈래 끝까지** 살아 있었다.
- ★★ **컴파일 에러인 쪽이 낫다.** 같은 코드가 `RefCell` 이 아니라 **`Mutex` 였다면 런타임 교착**이 될 자리다.\
  **「거부가 선물인」 대표 사례**다 — 다만 2024 에디션은 그 자리를 **아예 안 생기게** 고쳤다.
- ★ **`rustc` 에 `--edition` 을 안 주면 2015** 다. 에디션을 안 밝히고 「이 코드는 안 된다」를 적으면 **절반만 참**이다.

### 11. 열쇠 여섯과 번호별 첫 열쇠

**출력**

```text
   열쇠 여섯

   1. 순서 바꾸기        마지막 사용을 앞으로 · 블록으로 구간 닫기          (NLL)
   2. 쪼개기             필드 직접 · split_at_mut · parts_mut · iter_mut
   3. 값만 가져오기      인덱스로 먼저 읽기 · Copy · clone
   4. 구멍 안 내고 꺼내기 mem::take / replace / swap · Option::take
   5. 자료구조 교체      참조 대신 인덱스·범위 · Rc/Weak
   6. 런타임으로 옮기기  RefCell (마지막) · Arc<Mutex<T>>
```

**왜 그런가**

| 번호 | 무엇이 일어났나 | **첫 번째 열쇠** |
|---|---|---|
| **E0499** | 가변 둘이 겹쳤다 | **순서** → 안 되면 쪼개기(`split_at_mut`·`iter_mut`) |
| **E0502** | 가변과 공유가 겹쳤다 | **순서** → 인덱스 루프 · `entry` |
| **E0505** | 빌린 채로 옮겼다 | **순서** → `clone` |
| **E0506** | 빌린 채로 대입했다 | **순서** |
| **E0507** | 빌린 것에서 꺼냈다 | **`mem::take`** |
| **E0716** | 임시값이 먼저 죽었다 | **이름 주기** |

- ★ **여섯 중 첫 번째(순서)가 가장 자주 통한다.** 10번의 결론 — `later used here` 줄만 앞으로 옮기면 된다.
- ★★ **`clone()` 과 `RefCell` 을 마지막에 꺼내는 이유** — 둘 다 **문제를 없애지 않고 비용으로 바꾼다.**\
  `clone()` 은 **할당**, `RefCell` 은 **런타임 패닉 가능성**으로 바꾼다.\
  특히 `RefCell` 은 **컴파일 에러가 사라져서 해결한 기분이 들지만** 위험을 미룬 것이다.
- ★★★ **「이게 통과하면 무슨 사고가 나나」는 A/B 유형을 가르는 질문**이다.

| 대답이 | 유형 | 처방 |
|---|---|---|
| **나온다**(재할당으로 댕글링 · 구조체 이동으로 옛 주소) | **A — 정말 위험** | **설계를 고친다** |
| **안 나온다**(`v[0]` 과 `v[2]` 는 겹치지 않는다) | **B — 증명 못 했을 뿐** | **같은 뜻의 다른 표현** |

### 12. 다른 주제와 잇기

**출력**

| 무엇 | 정본 |
|---|---|
| 별칭 규칙 자체(E0499·E0502·NLL·재빌림) | [**10번 주제**](../10-borrowing-and-aliasing-rules/) |
| 수명 표기와 생략 규칙 | [**12번 주제**](../12-lifetime-annotations-and-elision/) |
| `RefCell` 내부 가변성 | 목록의 **42번 주제** |
| `mem::replace`/`take`·`Drop` | 목록의 **44번 주제** |
| `HashMap::entry` | [목록의 **39번 주제**](../39-hashmap-vs-btreemap-and-entry-api/) |
| `Vec::retain`·`drain` | [목록의 **38번 주제**](../38-vec-api-capacity-retain-and-drain/) |
| `iter`/`iter_mut`/`into_iter` | [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) |
| `unsafe` 와 안전한 표면 | 목록의 **56번 주제** |

**왜 그런가**

- ★ **12번과의 경계** — **그쪽은 수명을 「적는 법」**(생략 규칙·`'static`·E0106),\
  **여기는 막혔을 때 「손이 어디로 가나」**(열쇠 여섯). 5번의 `bump` 처럼 **겹치는 자리**는
  **표기 쪽은 12번, 처방 쪽은 여기**로 갈라 적었다.
- **`split_at_mut` 이 어떻게 보장하나** — **내부가 `unsafe` 로 구현돼 있고 표면만 안전**하다.\
  「검사기가 증명 못 하는 것을 사람이 한 번 증명하고 안전한 표면으로 가둔다」가 std 가 반복해서 쓰는 수법이고,\
  그 경계 설계가 목록의 **56번 주제**다. `iter_mut` 도 같은 집안이다.
- ★ **컴파일러가 열쇠 이름을 그대로 준 자리 셋.**

| 자리 | 준 것 |
|---|---|
| **E0499**(`v[0]`·`v[2]`) | `= help: use .split_at_mut(position)` — ★ 함수 이름을 그대로 |
| **E0716**(임시값) | `help: consider using a let binding` + 고친 두 줄 |
| **E0597**(2021 `if let`) | `help: consider adding semicolon…` + 세미콜론 위치 |

★ 다만 **4번의 `clone()` 권유는 따르면 안 되는 조언**이었다 — 목적이 「비우기」인데 `clone` 은 비우지 않는다.
**`help:` 는 컴파일을 통과시키는 법이지 올바른 설계가 아니다.**

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `for x in &v { v.push(..) }` | **E0502** + 같은 줄에 라벨 둘 | 1 |
| 인덱스 루프(길이 고정) | **통과** — `[1, 2, 3, 10, 30]` | 1 |
| 읽기/쓰기 분리(`collect`+`extend`) | **통과** — `[1, 2, 3, 10, 30]`(같은 값) | 1 |
| `retain` | **통과** — `[1, 3, 5]` | 1 |
| ★ `&mut v[0]` + `&mut v[2]` | **E0499** + `= help: use .split_at_mut(position)` | 2 |
| `split_at_mut(2)` | **통과** — `[4, 2] [3]` → `[4, 2, 3]` | 2 |
| `let b = v[2]; v[0] += b;` | **통과** — `[4, 2, 3]` | 2 |
| `title_mut()` + `body_mut()` | **E0499** — `d` 전체를 잡는다 | 3 |
| `&mut d.title` + `&mut d.body` | **통과** — `제목! / 본문?` | 3 |
| ★ `parts_mut() -> (&mut, &mut)` | **통과** — `제목! / 본문?` | 3 |
| `fn take_all(&mut self) -> String { self.data }` | **E0507** + `help:` 가 `clone()` 권유 | 4 |
| `mem::take` / `mem::replace` | **통과** — `남은 것 ""` · `밀려난 것 ""` | 4 |
| ★★ `match get_mut / None => insert` (main 안) | **통과** — `{"가": 1}` ★ **전제가 뒤집혔다** | 5 |
| ★ 같은 모양을 **반환하는 함수**로 | **E0499 + E0502**(두 개) | 5 |
| `entry(..).or_insert(0)` | **통과** — `{"가": 2, "나": 1}` | 5 |
| ★ `borrow_mut()` 두 번 | **컴파일 통과** → 첫 줄 출력 후 **패닉**, 종료 코드 **101** | 6 |
| `borrow_mut()` 뒤 `borrow()` | **패닉** — `RefCell already mutably borrowed` | 6 |
| 블록으로 가드 닫기 + `try_borrow_mut` | **통과** — `[1, 2, 3, 4]` · `false` | 6 |
| ★ `&String::from("가나다").len()` | **통과** — `9 라마바`(임시값 수명 연장) | 7 |
| `load().unwrap().as_str()` | **E0716** + `help:` 가 고친 두 줄을 줌 | 7 |
| 임시값에 이름 주기 | **통과** — `가나다` | 7 |
| ★ 루프에서 `held.push(&mut v[i])` | **E0499** — `in the previous iteration of the loop` | 8 |
| `v.iter_mut().collect()` | **통과** — `[2, 3, 4]`(같은 타입인데 통과) | 8 |
| `struct SelfRef { data, first: &str }` | **E0106** | 9 |
| `struct SelfRef<'a>` 로 고침 | **E0505** — 표기로는 못 푼다 | 9 |
| `Range<usize>` 로 교체 | **통과** — `가나다 / 가` | 9 |
| ★★ `if let` + `RefCell` **2021 / 2024** | **E0597** / **통과**(`Some(7)`) | 10 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **에러 번호가 상황별로 갈리는 것** | **rustc 구현**. 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| `= help:` 가 **`split_at_mut` 을 권하는 것** | **rustc 진단 구현** — 유용하지만 **보장이 아니다** |
| ★ **`get_mut`+`insert` 가 함수 안에서 통과하는 것** | **현재 검사기(NLL)** — 옛 자료의 「안 된다」가 뒤집혔다 |
| ★ **같은 모양이 반환하면 막히는 것** | **현재 검사기의 한계** — 언어가 금지한 것이 아니다 |
| ★ **`RefCell` 의 패닉 문구** | **std 판** — 바뀌어 온 이력이 있다 |
| 패닉 메시지의 **스레드 id** | **런타임** — 실행마다 바뀐다. 근거로 읽지 않는다 |
| ★ **`HashMap` 순회 순서** | **std**(보장 없음) — 같은 바이너리 20회에 12 대 8 |
| 패닉 **종료 코드 101** | **std 런타임** |
| `if let` **임시값 스코프** | **에디션**(2024에서 변경) |
| **임시값 수명 연장이 적용되는 모양** | **언어**(Reference — Destructors) |
| `IndexMut` 이 **전체를 빌리는 것** | **std 의 시그니처** — 언어가 아니라 **API 모양** |
| **`mem::take` 가 `Default` 를 두는 것** | **std** — `T: Default` 가 경계다 |
| **A 유형 거부**(순회 중 변경·자기 참조) | **언어 보장.** 통과시키면 메모리 안전이 깨진다 |
