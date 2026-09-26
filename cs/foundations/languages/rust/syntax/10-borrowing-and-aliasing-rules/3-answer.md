# rust/syntax/10 — 빌림 `&`와 `&mut`, 별칭 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ **주소 절댓값은 실행마다 바뀐다**(ASLR). 근거로 읽을 칸은 「**같은가 / 다른가**」뿐이다.\
> ★ 이 주제의 고유 창은 **같은 코드의 순서만 바꿔 두 번 던지는 것**이다(3번).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 읽기 하나와 쓰기 하나

**출력**

```text
===== 소스: ex.rs =====
// 공유 빌림이 살아 있는데 가변 빌림을 만들면?
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];        // 공유 빌림
    v.push(4);                // 가변 빌림 (push 가 &mut self 를 받는다)
    println!("첫 원소 = {}", first);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:5
  |
4 |     let first = &v[0];        // 공유 빌림
  |                  - immutable borrow occurs here
5 |     v.push(4);                // 가변 빌림 (push 가 &mut self 를 받는다)
  |     ^^^^^^^^^ mutable borrow occurs here
6 |     println!("첫 원소 = {}", first);
  |                              ----- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**왜 그런가**

- **컴파일되지 않는다. E0502**, 제목은\
  **`cannot borrow v as mutable because it is also borrowed as immutable`** 이다.
- `v.push(4)` 가 가변 빌림인 근거는 **`push` 의 시그니처**다 — `fn push(&mut self, value: T)`.\
  ★ 메서드 호출의 빌림 종류는 **리시버(`self`) 자리에 무엇이 적혔는지**로 판정한다.
- 라벨 셋을 순서대로 읽는다.

| 줄 | 라벨 | 뜻 |
|---|---|---|
| 4 | `immutable borrow occurs here` | 공유 빌림이 **시작**된 자리 |
| 5 | `mutable borrow occurs here` | 충돌을 **일으킨** 자리(`^^^`) |
| 6 | `immutable borrow later used here` | ★ 그 공유 빌림의 **마지막 사용** = **만료 지점** |

- ★ **한 글자도 안 지우고 통과시킬 수 있다** — **6번 줄을 5번 줄 위로 옮기면** 된다.\
  대출이 5번 줄 전에 끝나기 때문이다. 정본은 3번 답이다.

```text
   v ──┬── &v ── first   (읽기)        ← 4번 줄에서 시작
       └── &mut v ── push (쓰기)       ← 5번 줄에서 충돌
   first 가 6번 줄에서 또 쓰이므로 4~6 이 대출 구간이고
   5번 줄이 그 안에 있다 -> E0502
```

### 2. ★ 쓰기 둘

**출력**

```text
===== 소스: ex.rs =====
// 가변 빌림을 둘 만들면?
fn main() {
    let mut s = String::from("안녕");
    let a = &mut s;
    let b = &mut s;
    a.push('!');
    b.push('?');
    println!("{a} {b}");
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0499]: cannot borrow `s` as mutable more than once at a time
 --> ex.rs:5:13
  |
4 |     let a = &mut s;
  |             ------ first mutable borrow occurs here
5 |     let b = &mut s;
  |             ^^^^^^ second mutable borrow occurs here
6 |     a.push('!');
  |     - first borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0499`.
```

**왜 그런가**

- **E0499** 다. 1번과 번호가 다른 이유 — **E0502 는 종류가 다른 둘이 섞인 것**이고,\
  **E0499 는 가변이 둘인 것**이다. 컴파일러가 두 위반을 갈라서 번호를 준다.

`rustc --explain E0499`:

> Please note that in Rust, you can either have many immutable references, or one
> mutable reference.

```text
   허용                                  금지
   (가) 공유 여럿                        (다) 공유 + 가변      E0502
   s ──┬── &s ── r1                     s ──┬── &s     ── r
       ├── &s ── r2                         └── &mut s ── w
       └── s 로 읽기도 OK
                                        (라) 가변 + 가변      E0499
   (나) 가변 하나                        s ──┬── &mut s ── a
   s ─── &mut s ── w                        └── &mut s ── b
         그동안 s 도 못 쓴다
```

- ★ **`a.push('!')` 를 `let b = &mut s;` 위로 올리면 통과한다.** 실측이다.

```text
===== 소스: ex.rs =====
// E0499 도 마찬가지다 — 첫 빌림의 마지막 사용만 앞으로 옮긴다
fn main() {
    let mut s = String::from("안녕");
    let a = &mut s;
    a.push('!');          // ★ a 의 마지막 사용이 여기로 왔다
    let b = &mut s;
    b.push('?');
    println!("{b}");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
안녕!?
(종료 코드 0)
```

### 3. ★★ 같은 네 줄, 순서만 다르다

**출력** — (가) 마지막 사용이 `push` 앞

```text
===== 소스: ex.rs =====
// NLL — 같은 세 줄, 순서만 바꾼다 (가) 마지막 사용이 push 앞
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];               // 공유 빌림 시작
    println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림은 여기서 끝난다
    v.push(4);                       // 가변 빌림
    println!("v = {:?}", v);
}                                    // first 라는 이름은 여기까지 스코프에 있다
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
첫 원소 = 1
v = [1, 2, 3, 4]
(종료 코드 0)
```

**출력** — (나) 마지막 사용이 `push` 뒤

```text
===== 소스: ex.rs =====
// NLL — 같은 세 줄, 순서만 바꾼다 (나) 마지막 사용이 push 뒤
fn main() {
    let mut v = vec![1, 2, 3];
    let first = &v[0];               // 공유 빌림 시작
    v.push(4);                       // 가변 빌림
    println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림이 여기까지 산다
    println!("v = {:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as mutable because it is also borrowed as immutable
 --> ex.rs:5:5
  |
4 |     let first = &v[0];               // 공유 빌림 시작
  |                  - immutable borrow occurs here
5 |     v.push(4);                       // 가변 빌림
  |     ^^^^^^^^^ mutable borrow occurs here
6 |     println!("첫 원소 = {}", first); // ★ first 의 마지막 사용 — 빌림이 여기까지 산다
  |                              ----- immutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**왜 그런가**

- **(가)만 컴파일된다.** 두 파일은 **같은 네 줄이고 순서만 다르다.**
- ★ **`first` 이름의 스코프는 두 파일이 똑같다** — 둘 다 `main` 의 블록 끝까지다.\
  그러니 **스코프가 가른 것이 아니다.**
- 가른 것은 **마지막 사용 위치**다. 빌림은 **마지막 사용에서 끝난다** —\
  이 규칙의 이름이 **NLL**(non-lexical lifetimes)이다.

```text
   (가) 통과                             (나) 거부

   4  let first = &v[0];   ┐             4  let first = &v[0];   ┐
   5  println!("{first}"); ┘ 대출 4~5    5  v.push(4);           │ 대출 4~6
   6  v.push(4);             ← 밖        6  println!("{first}"); ┘  ← 5가 안에 있다
   7  println!("{v:?}");                 7  println!("{v:?}");
   8  }  ← first 는 여기까지 스코프        8  }  ← 스코프는 (가)와 동일

   스코프(lexical)  : 두 파일이 같다
   대출 구간(NLL)   : 마지막 사용까지 — 여기가 다르다
```

- ★ 에러가 그 사실을 **직접 말한다** — 6번 줄에 붙은 **`immutable borrow later used here`** 라벨이\
  「이 빌림은 **여기까지** 쓰인다」는 선언이다. **그 줄이 대출 만료일**이다.
- **블록으로 감싸는 처방**(`{ let first = &v[0]; println!("{first}"); }`)은\
  **마지막 사용을 강제로 앞당기는 일**을 하는 것이다 — NLL 로 보면 순서 바꾸기와 **같은 조작**이다.\
  ★ 그래서 NLL 이 있는 지금은 **블록이 꼭 필요하지는 않다.** 순서만 바꿔도 된다.

> **NLL(non-lexical lifetimes)** — 빌림 구간을 중괄호가 아니라 **마지막 사용 지점**으로 정하는 규칙.\
> 예: 위 (가)에서 `first` 의 대출은 `println!` 에서 끝나 그 뒤의 `push` 와 충돌하지 않는다.

### 4. ★ `&mut` 를 함수에 두 번 넘기면

**출력**

```text
===== 소스: ex.rs =====
// &mut 재빌림(reborrow) — 함수에 넘겨도 왜 안 죽나
fn bump(r: &mut i32) { *r += 1; }

fn main() {
    println!("(1) &mut 를 함수에 두 번 넘긴다 — 이동이면 두 번째가 막혀야 한다");
    let mut n = 0;
    let r = &mut n;
    bump(r);
    bump(r);
    println!("    n = {}", *r);

    println!("(2) 명시적 재빌림 &mut *r — 안쪽 빌림이 끝나면 바깥이 되살아난다");
    let mut m = 10;
    let outer = &mut m;
    {
        let inner = &mut *outer;    // outer 를 재빌림
        *inner += 5;
        println!("    inner 로 고친 뒤 = {}", *inner);
    }
    *outer += 1;                    // inner 의 마지막 사용이 지났으므로 outer 가 다시 쓰인다
    println!("    outer 로 고친 뒤 = {}", *outer);

    println!("(3) 재빌림 중에 바깥을 쓰면?");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) &mut 를 함수에 두 번 넘긴다 — 이동이면 두 번째가 막혀야 한다
    n = 2
(2) 명시적 재빌림 &mut *r — 안쪽 빌림이 끝나면 바깥이 되살아난다
    inner 로 고친 뒤 = 15
    outer 로 고친 뒤 = 16
(3) 재빌림 중에 바깥을 쓰면?
(종료 코드 0)
```

**출력** — 재빌림 중에 바깥을 쓰면

```text
===== 소스: ex.rs =====
// 재빌림 중에 바깥 참조를 쓰면?
fn main() {
    let mut k = 0;
    let out = &mut k;
    let inn = &mut *out;      // out 을 재빌림
    *out += 1;                // inn 이 아직 살아 있는데 out 을 쓴다
    *inn += 1;
    println!("{}", k);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0503]: cannot use `*out` because it was mutably borrowed
 --> ex.rs:6:5
  |
5 |     let inn = &mut *out;      // out 을 재빌림
  |               --------- `*out` is borrowed here
6 |     *out += 1;                // inn 이 아직 살아 있는데 out 을 쓴다
  |     ^^^^^^^^^ use of borrowed `*out`
7 |     *inn += 1;
  |     --------- borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0503`.
```

**왜 그런가**

- 두 번째 `bump(r)` 이 막히지 않는 이유는 **재빌림**(reborrow)이다. **복사도 이동도 아니다.**
- 컴파일러는 `bump(r)` 을 사실상 **`bump(&mut *r)`** 로 읽는다 —\
  `r` 을 빌려 만든 **새 `&mut`** 가 그 호출 동안만 살고 끝난다. `r` 자체는 그대로 있다.

```text
   이동이라면 (실제로는 아니다)          재빌림 (실제)
   let r = &mut n;                      let r = &mut n;
   bump(r);   <- r 이 죽는다             bump(&mut *r);  <- 컴파일러가 이렇게 읽는다
   bump(r);   <- E0382                          |
                                                +-- 그 호출 동안만 사는 새 빌림
                                        bump(r);  <- r 은 살아 있다
```

```text
   재빌림의 계층
   k (원본)
    └── out : &mut k              out 이 사는 동안 k 를 못 쓴다
          └── inn : &mut *out      inn 이 사는 동안 out 도 못 쓴다  ← E0503
                |
          inn 의 마지막 사용이 지나면 out 이 되살아난다
```

- `let inn = &mut *out;` 뒤에 `*out += 1;` 을 쓰면 **E0503**(`cannot use *out because it was mutably borrowed`)이다.
- **안쪽 빌림이 끝나면 바깥은 다시 쓸 수 있다** — (2)의 `*outer += 1` 이 통과했다(`15` → `16`).\
  여기서도 끝나는 기준은 **마지막 사용**이다(3번의 NLL).

### 5. ★ 참조를 다른 이름에 담으면

**출력**

```text
===== 소스: ex.rs =====
// & 는 Copy, &mut 는 아니다 — 같은 모양의 두 블록을 던진다
fn main() {
    println!("(가) &T 를 두 이름에 나눠 담는다");
    let n = 1;
    let r1 = &n;
    let r2 = r1;              // 복사인가 이동인가?
    println!("    r1 = {}, r2 = {}", r1, r2);

    println!("(나) &mut T 를 두 이름에 나눠 담는다");
    let mut m = 1;
    let w1 = &mut m;
    let w2 = w1;              // 여기가 갈린다
    *w2 += 1;
    println!("    w1 = {}, w2 = {}", w1, w2);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `w1`
  --> ex.rs:14:38
   |
11 |     let w1 = &mut m;
   |         -- move occurs because `w1` has type `&mut i32`, which does not implement the `Copy` trait
12 |     let w2 = w1;              // 여기가 갈린다
   |              -- value moved here
13 |     *w2 += 1;
14 |     println!("    w1 = {}, w2 = {}", w1, w2);
   |                                      ^^ value borrowed here after move
   |
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **거부되는 쪽은 (나)** 이고 에러는 **E0382** 다. ★ **(가) 쪽 줄에는 에러가 하나도 안 났다.**
- 이유 한 구절은 **`which does not implement the Copy trait`** 다 — 08번·09번과 **같은 문장**이다.
- **`&T` 를 `Copy` 로 둬도 안전한 이유** — 복사해 봐야 **공유 빌림이 하나 더 생길 뿐**이고,\
  「공유 여럿」은 별칭 규칙이 **이미 허용한 상태**다.
- **`&mut T` 가 `Copy` 였다면** `let w2 = w1;` 한 줄로 **가변 빌림이 둘**이 된다.\
  그러면 E0499 로 막던 상태가 **대입 한 줄로 공짜로** 만들어진다 — **별칭 규칙 전체가 무너진다.**

```text
   &T 가 Copy 여도 안전                   &mut T 가 Copy 라면 (그래서 아니다)
   n ──┬── r1 (읽기)                      m ──┬── w1 (쓰기)
       └── r2 (읽기)                          └── w2 (쓰기)
   = 별칭 규칙의 «공유 여럿»               = 별칭 규칙의 «가변 둘» 이 공짜로 생긴다
```

- 09번이 인용한 `--explain E0204` 가 같은 말을 한다 —\
  `&mut T` is not `Copy`, even when `T` is `Copy` (this differs from the behavior for `&T`).
- 그래서 **`&mut` 를 여러 곳에 주려면 대입이 아니라 재빌림**을 쓴다(4번).

### 6. ★ 두 필드를 동시에 만지면

**출력** — (가) 필드를 직접 짚으면

```text
===== 소스: ex.rs =====
// 필드별 빌림 (가) 필드를 직접 짚으면
struct S { a: String, b: String }

fn main() {
    let mut s = S { a: String::from("A"), b: String::from("B") };
    let ra = &mut s.a;          // a 만 가변 빌림
    let rb = &s.b;              // b 는 공유 빌림
    ra.push('!');
    println!("a = {} / b = {}", ra, rb);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a = A! / b = B
(종료 코드 0)
```

**출력** — (나) 같은 일을 메서드로 하면

```text
===== 소스: ex.rs =====
// 필드별 빌림 (나) 같은 일을 메서드로 하면
struct S { a: String, b: String }

impl S {
    fn a_mut(&mut self) -> &mut String { &mut self.a }
    fn b_ref(&self) -> &String { &self.b }
}

fn main() {
    let mut s = S { a: String::from("A"), b: String::from("B") };
    let ra = s.a_mut();         // &mut self — 구조체 전체를 가변 빌림
    let rb = s.b_ref();         // &self    — 구조체 전체를 공유 빌림
    ra.push('!');
    println!("a = {} / b = {}", ra, rb);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `s` as immutable because it is also borrowed as mutable
  --> ex.rs:12:14
   |
11 |     let ra = s.a_mut();         // &mut self — 구조체 전체를 가변 빌림
   |              - mutable borrow occurs here
12 |     let rb = s.b_ref();         // &self    — 구조체 전체를 공유 빌림
   |              ^ immutable borrow occurs here
13 |     ra.push('!');
   |     -- mutable borrow later used here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

**왜 그런가**

- **통과하는 쪽은 (가)** 다. 필드를 직접 짚으면 검사기가 **칸 단위**로 본다 —\
  `s.a` 와 `s.b` 는 **겹치지 않는 자리**이므로 하나는 가변, 하나는 공유로 동시에 빌릴 수 있다.
- **(나)는 E0502** 다. 갈리는 이유는 **시그니처**다.

```text
   &mut s.a        : 「s 의 a 칸」을 빌린다       -> 칸 하나
   s.a_mut()       : fn a_mut(&mut self)        -> s 전체
                              ^^^^^^^^^
                     반환값이 a 뿐이어도 «받은 것» 은 전체다
```

- ★ **빌림 검사기는 `a_mut` 의 몸통을 보지 않는다.** 함수 단위로 분석하고 **시그니처만 계약으로 읽는다.**\
  그래서 「사실 `a` 만 건드리는데?」는 판정에 반영되지 않는다.
- ★ 그 결과 **리팩터링이 새 에러를 만든다** — 잘 돌던 코드를 메서드로 빼는 순간 E0499/E0502 가 난다.\
  버그가 아니라 **계약 단위가 함수라는 사실**의 결과다.

**푸는 길 셋**

| 길 | 어떻게 | 대가 |
|---|---|---|
| ① **필드를 직접 쓴다** | `&mut s.a` · `&s.b` | 캡슐화가 열린다 |
| ② **한 번에 둘을 돌려주는 메서드** | `fn split(&mut self) -> (&mut String, &String)` | API 가 늘어난다 |
| ③ **구조체를 쪼갠다** | `a` 와 `b` 를 다른 타입으로 | 설계 변경 |

- 전형과 처방의 전수는 [**11번 주제**](../11-borrow-checker-rejections/)가 모은다.

### 7. 가변 빌림 중에 원본 이름을 쓰면

**출력**

```text
===== 소스: ex.rs =====
// 가변 빌림이 사는 동안 원본 이름을 쓰면?
fn main() {
    let mut s = String::from("안녕");
    let r = &mut s;
    println!("원본 이름으로 읽기 = {}", s);
    r.push('!');
    println!("{}", r);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `s` as immutable because it is also borrowed as mutable
 --> ex.rs:5:33
  |
4 |     let r = &mut s;
  |             ------ mutable borrow occurs here
5 |     println!("원본 이름으로 읽기 = {}", s);
  |                                         ^ immutable borrow occurs here
6 |     r.push('!');
  |     - mutable borrow later used here
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error
```

**출력** — `mut` 이 아닌 바인딩을 가변 빌림하면(번호가 다르다)

```text
===== 소스: ex.rs =====
// mut 이 아닌 바인딩을 가변 빌림하면?
fn main() {
    let s = String::from("불변");
    let r = &mut s;
    r.push('!');
    println!("{}", r);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0596]: cannot borrow `s` as mutable, as it is not declared as mutable
 --> ex.rs:4:13
  |
4 |     let r = &mut s;
  |             ^^^^^^ cannot borrow as mutable
  |
help: consider changing this to be mutable
  |
3 |     let mut s = String::from("불변");
  |         +++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0596`.
```

**왜 그런가**

- **통과하지 않는다.** `println!("{}", s)` 가 **`s` 를 공유 빌림**하기 때문이다.
- 「주인이니까 읽는 건 되겠지」가 안 통하는 이유 — **읽기도 빌림**이다.\
  `&mut` 가 나가 있는 동안에는 **그 값에 닿는 다른 길이 하나도 없어야** 한다.\
  ★ 이것이 `&mut` 를 「mutable」보다 「**exclusive(배타)**」로 읽어야 하는 이유다.
- 에러 번호는 **1번과 같은 E0502** 다(종류가 다른 둘이 섞였다). 2번의 E0499 가 아니다.
- **`mut` 없는 바인딩에 `&mut` 를 하면 E0596** 으로 **또 다른 번호**다.\
  ★ 이건 별칭 문제가 아니라 **`let mut` 이 빠진 것**이다. `help` 가 `+++` 로 `mut` 을 넣으라고 직접 말한다.

```text
   E0502 : 두 빌림의 «종류» 가 섞였다      -> 순서·스코프를 고친다
   E0499 : 가변 빌림이 «둘» 이다           -> 순서·스코프를 고친다
   E0596 : 원본이 «mut 이 아니다»          -> 선언에 mut 을 붙인다 (별칭과 무관)
```

### 8. `*` 는 언제 필요한가

**출력**

```text
===== 소스: ex.rs =====
// 역참조 * 와 자동 역참조(메서드 호출)
fn main() {
    let mut n = 10;
    let r = &mut n;

    println!("(1) 읽고 쓸 때는 * 가 필요하다");
    println!("    *r = {}", *r);
    *r += 5;
    println!("    *r += 5 뒤 = {}", *r);

    println!("(2) 메서드 호출은 * 를 안 써도 된다 — 몇 겹이든 벗겨 준다");
    let s = String::from("안녕하세요");
    let rs: &String = &s;
    let rrs: &&String = &rs;
    let rrrs: &&&String = &rrs;
    println!("    s.len()       = {}", s.len());
    println!("    rs.len()      = {}", rs.len());
    println!("    rrs.len()     = {}", rrs.len());
    println!("    rrrs.len()    = {}", rrrs.len());
    println!("    (***rrrs).len() = {}", (***rrrs).len());

    println!("(3) 연산자는 한 겹까지만 — 자동 역참조가 아니라 std 의 impl 이다");
    let a = &5;
    let b = &7;
    println!("    a + b   = {}", a + b);      // impl Add<&i32> for &i32 가 있다
    println!("    *a + *b = {}", *a + *b);

    println!("(4) 비교는 참조끼리도 되지만 뜻이 다르다");
    let x = String::from("같다");
    let y = String::from("같다");
    println!("    x == y             {}", x == y);
    println!("    &x == &y           {}", &x == &y);              // 내용 비교
    println!("    ptr::eq(&x, &y)    {}", std::ptr::eq(&x, &y));  // 주소 비교
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) 읽고 쓸 때는 * 가 필요하다
    *r = 10
    *r += 5 뒤 = 15
(2) 메서드 호출은 * 를 안 써도 된다 — 몇 겹이든 벗겨 준다
    s.len()       = 15
    rs.len()      = 15
    rrs.len()     = 15
    rrrs.len()    = 15
    (***rrrs).len() = 15
(3) 연산자는 한 겹까지만 — 자동 역참조가 아니라 std 의 impl 이다
    a + b   = 12
    *a + *b = 12
(4) 비교는 참조끼리도 되지만 뜻이 다르다
    x == y             true
    &x == &y           true
    ptr::eq(&x, &y)    false
(종료 코드 0)
```

**출력** — 연산자에 한 겹 더 씌우면

```text
===== 소스: ex.rs =====
// 연산자에는 자동 역참조가 없다 — 한 겹 더 씌우면 드러난다
fn main() {
    let a = &5;
    let b = &7;
    println!("&i32 + &i32   = {}", a + b);     // std 가 impl Add<&i32> for &i32 를 준다
    let aa = &a;
    let bb = &b;
    println!("&&i32 + &&i32 = {}", aa + bb);   // 이건?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0369]: cannot add `&&{integer}` to `&&{integer}`
 --> ex.rs:8:39
  |
8 |     println!("&&i32 + &&i32 = {}", aa + bb);   // 이건?
  |                                    -- ^ -- &&{integer}
  |                                    |
  |                                    &&{integer}

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0369`.
```

**왜 그런가**

- **`*r += 1` 만 된다.** `r += 1` 은 `&mut i32` 에 정수를 더하는 꼴이라 타입이 안 맞는다.
- **`&&&String` 에 `.len()` 이 그대로 불린다** — 실측에서 **세 겹까지** 벗겨 줬다.\
  메서드를 찾을 때 컴파일러가 `*` 를 알아서 붙여 가는 것이 **자동 역참조**다.
- ★ **연산자는 다르다.** `&i32 + &i32` 가 되는 것은 **std 가 `impl Add<&i32> for &i32` 를 써 뒀기 때문**이고,\
  한 겹 더 씌운 `&&i32 + &&i32` 는 **E0369** 로 막힌다.
- 그 차이가 말해 주는 것 — **연산자는 자동 역참조를 하지 않는다.**\
  「되는 만큼만 미리 구현돼 있다」가 맞는 읽기다.

```text
   메서드 호출 — 겹을 벗겨 가며 찾는다     연산자 — 미리 써 둔 impl 만
   &&&String.len()                       &i32 + &i32    -> impl 있음
      +-> &&String                       &&i32 + &&i32  -> impl 없음 -> E0369
      +-> &String
      +-> String  ── len() 발견
```

| 자리 | `*` 필요? |
|---|---|
| 메서드 호출 `r.len()` | **불필요** |
| `println!("{}", r)` | **불필요**(`&T` 에도 `Display` 가 있다) |
| 산술·대입 `*r += 1` | **필요** |
| 값 자체 꺼내기 `let v = *r;` | **필요**(그리고 `T: Copy` 여야 한다) |
| 연산자 `a + b` | **불필요 — 단 std 가 그 impl 을 준 만큼만** |

### 9. 여섯 식의 타입

**출력**

```text
===== 소스: ex.rs =====
// 타입을 컴파일러에게 묻는다 — let _: () = 식;
fn main() {
    let mut v = vec![1, 2, 3];
    let s = String::from("hi");
    let _: () = &v;
    let _: () = &mut v;
    let _: () = &v[0];
    let _: () = &s;
    let _: () = &&s;
    let _: () = &*s;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:5:17
  |
5 |     let _: () = &v;
  |            --   ^^ expected `()`, found `&Vec<{integer}>`
  |            |
  |            expected due to this
  |
  = note: expected unit type `()`
             found reference `&Vec<{integer}>`

error[E0308]: mismatched types
 --> ex.rs:6:17
  |
6 |     let _: () = &mut v;
  |            --   ^^^^^^ expected `()`, found `&mut Vec<{integer}>`
  |            |
  |            expected due to this
  |
  = note:      expected unit type `()`
          found mutable reference `&mut Vec<{integer}>`

error[E0308]: mismatched types
 --> ex.rs:7:17
  |
7 |     let _: () = &v[0];
  |            --   ^^^^^ expected `()`, found `&{integer}`
  |            |
  |            expected due to this

error[E0308]: mismatched types
 --> ex.rs:8:17
  |
8 |     let _: () = &s;
  |            --   ^^ expected `()`, found `&String`
  |            |
  |            expected due to this

error[E0308]: mismatched types
 --> ex.rs:9:17
  |
9 |     let _: () = &&s;
  |            --   ^^^ expected `()`, found `&&String`
  |            |
  |            expected due to this

error[E0308]: mismatched types
  --> ex.rs:10:17
   |
10 |     let _: () = &*s;
   |            --   ^^^ expected `()`, found `&str`
   |            |
   |            expected due to this

error: aborting due to 6 previous errors

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- `let _: () = 식;` 은 **타입이 안 맞는다는 에러를 일부러 내서** `found ...` 칸으로 답을 얻는 수법이다\
  ([**04번 주제**](../04-expressions-and-semicolons/)가 세웠다).

| 식 | 타입 |
|---|---|
| `&v` | `&Vec<{integer}>` |
| `&mut v` | `&mut Vec<{integer}>` |
| `&v[0]` | `&{integer}` |
| `&s` | `&String` |
| `&&s` | `&&String` |
| `&*s` | **`&str`** |

- **`&str` 이 나오는 것은 `&*s`** 다. `*s` 가 `String` 을 `str` 로 벗기고, 거기에 `&` 를 붙인다.\
  ★ 이것이 **`Deref` 강제**의 맨얼굴이다(정본은 [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/), `String`/`&str` 선택은 **14번 주제**).
- ★ **여섯 줄이 빌림 충돌을 안 낸 이유는 NLL** 이다 — 각 임시 빌림이 **그 줄에서 끝난다.**\
  `&mut v` 다음 줄에 `&v[0]` 이 와도 문제가 없다. 3번의 규칙이 여기서도 작동한다.
- `{integer}` 는 **아직 확정 안 된 정수 타입**을 뜻한다(추론 변수). `i32` 로 고정되기 전 상태다.

### 10. `&s`·`&mut s` 를 쓴 뒤의 원본

**출력**

```text
===== 소스: ex.rs =====
// 빌림의 기본 — 넘겨도 안 잃는다, 공유는 여럿이 된다
fn borrow_len(s: &String) -> usize { s.len() }
fn append(s: &mut String) { s.push_str("!!"); }

fn main() {
    println!("(1) & 로 넘기면 원본이 산다 — 08 의 takes(s) 와 대비");
    let s = String::from("hello");
    let n = borrow_len(&s);
    println!("    길이 {} / 원본 {}", n, s);

    println!("(2) 공유 빌림은 여럿이 공존한다");
    let r1 = &s;
    let r2 = &s;
    let r3 = &s;
    println!("    {} {} {} / 원본 {}", r1, r2, r3, s);

    println!("(3) 가변 빌림은 하나만 — 그 동안 원본 이름도 못 쓴다");
    let mut t = String::from("bye");
    append(&mut t);
    println!("    {}", t);

    println!("(4) 참조가 가리키는 주소는 원본 그대로다");
    let p_owner = &t as *const String as usize;
    let rt = &t;
    let p_ref = rt as *const String as usize;
    println!("    같은 자리를 가리키나? {}", p_owner == p_ref);
    println!("    &String 자체의 크기 = {} 바이트", size_of::<&String>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
(1) & 로 넘기면 원본이 산다 — 08 의 takes(s) 와 대비
    길이 5 / 원본 hello
(2) 공유 빌림은 여럿이 공존한다
    hello hello hello / 원본 hello
(3) 가변 빌림은 하나만 — 그 동안 원본 이름도 못 쓴다
    bye!!
(4) 참조가 가리키는 주소는 원본 그대로다
    같은 자리를 가리키나? true
    &String 자체의 크기 = 8 바이트
(종료 코드 0)
```

**왜 그런가**

- **반환 타입이 안 부푼다.** 08번은 소유권을 돌려받으려고 `-> (String, usize)` 가 됐는데,\
  빌리면 **`-> usize`** 그대로다.

```text
   08번 — 돌려받기                        10번 — 빌리기
   fn takes_and_gives(s: String)          fn borrow_len(s: &String) -> usize
       -> (String, usize)                        ^^^^^^^
          ^^^^^^^^^^^^^^^                 반환 타입에 값을 얹을 필요가 없다
   인자가 둘이면 튜플이 셋이 된다            main 의 s 는 계속 산다
```

- **참조는 원본과 같은 자리를 가리킨다**(`true`). 사본이 아니다.\
  근거는 `&t` 를 주소로 바꾼 값과 `rt` 를 주소로 바꾼 값이 **같다**는 것이다.
- **참조 하나의 크기는 8바이트**(이 머신).
- 그 수치는 **플랫폼의 포인터 폭**에 달려 있다 — 64비트라 8이다. 32비트 타깃이면 4가 된다.\
  ★ **이 머신에서만 잰 값**으로 읽어야 한다. 주소 절댓값은 ASLR 로 매번 바뀌므로 근거가 아니다.

### 11. 에러 번호 지도

**왜 그런가**

| 번호 | 언제 나나 | 고치는 방향 |
|---|---|---|
| **E0499** | **가변 빌림이 둘** 이상 겹친다 | 마지막 사용을 앞으로 · 스코프 쪼개기 · `split_at_mut` |
| **E0502** | **공유와 가변이 섞인다**(어느 쪽이 먼저든) | 〃 |
| **E0503** | **재빌림 중에 바깥 참조를 쓴다** | 안쪽 빌림의 마지막 사용 뒤로 미룬다 |
| **E0596** | 원본이 **`mut` 바인딩이 아니다** | ★ 선언에 `mut` 을 붙인다 |
| **E0382** | **이동한 값을 쓴다** — `&mut` 를 대입한 경우 포함 | 재빌림(`&mut *w`)으로 바꾼다 |

- ★ **별칭 규칙과 무관한 번호는 E0596** 이다. 그건 **바인딩 선언 문제**다([**02번 주제**](../02-bindings-mut-and-shadowing/)).
- `&mut` 를 다른 이름에 대입했을 때 나는 번호는 **E0382** —\
  [**08번 주제**](../08-ownership-and-move/)의 `let s2 = s1;`(String)과 **완전히 같은 번호**다.\
  ★ 그래서 `&mut` 는 「**참조인데도 이동하는 값**」으로 읽어야 한다.
- 기억에 남겨야 하는 것은 **번호**다. **문구와 `help` 제안은 rustc 버전이 오르면 바뀐다.**\
  이 문서의 실측 문구도 **1.92.0 기준**이다.

### 12. 다른 주제와 잇기

- **전형 코드와 처방의 모음** — [**11번 주제**](../11-borrow-checker-rejections/).\
  순회 중 변경 · 두 번 가변 빌림 · 이동 뒤 사용 · 지역 참조 반환 · 벡터 두 원소 · `self` 를 빌린 채 메서드 호출.
- **「빌린 것이 원본보다 오래 살면 안 된다」의 표기** — [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 `'a` 와 생략 규칙).\
  이 주제가 「**동시에 몇 개인가**」였다면 12번은 「**언제까지인가**」다.
- **런타임 비용을 내고 완화하는 도구** — `RefCell`/`Cell`, [목록의 **42번 주제**](../42-refcell-cell-interior-mutability/).\
  ★ 규칙이 사라지는 게 아니라 **위반이 컴파일 에러에서 패닉으로 바뀐다**(11번에 실측이 있다).\
  스레드까지 가면 `Arc<Mutex<T>>`(목록의 **52번 주제**)가 같은 일을 한다.
- **모델 자체의 논증** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §3 이 정본이다.\
  「왜 별칭과 변경을 동시에 안 주나」는 거기고, **여기는 그 규칙이 어떤 에러로 나타나고 무엇으로 고치나**다.\
  역사는 [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md).
- **에러 메시지 자체가 답을 알려 준 자리** — ★ **`borrow later used here` 라벨**이다.\
  그 줄이 **빌림의 만료 지점**이고, 그것만 앞으로 옮기면 대부분의 E0499/E0502 가 사라진다.\
  3번의 두 파일이 그 하나의 사실로 갈렸다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `&v[0]` 뒤 `v.push(4)` | **E0502** + 라벨 셋(`occurs`·`occurs`·`later used here`) | 1·3 |
| ★ 같은 네 줄, **순서만 바꾼 두 파일** | (가) **통과** / (나) **E0502** — 스코프는 동일, 마지막 사용만 다르다 | 3 |
| 같은 파일을 **`--edition 2015`** 로 | (가)가 **그대로 통과** — NLL 이 에디션과 무관 | 3 |
| `&mut s` 두 번 | **E0499** + `--explain` 의 별칭 규칙 문장 | 2 |
| `a.push()` 를 위로 올린 판 | **통과** — `안녕!?` | 2 |
| `bump(r)` 두 번 | **통과** — `n = 2`(재빌림) | 4 |
| `&mut *outer` 블록 뒤 `*outer += 1` | **통과** — `15` → `16` | 4 |
| `&mut *out` 뒤 `*out += 1` | **E0503** `cannot use *out because it was mutably borrowed` | 4 |
| `let r2 = r1;`(`&i32`) | **통과** — 둘 다 산다 | 5 |
| `let w2 = w1;`(`&mut i32`) | **E0382** `does not implement the Copy trait` | 5 |
| `&mut s.a` + `&s.b` | **통과** — `a = A! / b = B` | 6 |
| `s.a_mut()` + `s.b_ref()` | **E0502** — 시그니처가 전체를 잡는다 | 6 |
| `&mut s` 뒤 `println!("{s}")` | **E0502** — 읽기도 빌림이다 | 7 |
| `mut` 없는 바인딩에 `&mut` | **E0596** + `help:` 가 `mut` 을 넣으라고 함 | 7·11 |
| `&&&String` 에 `.len()` | **통과**(15) — 세 겹까지 자동 역참조 | 8 |
| `&i32 + &i32` / `&&i32 + &&i32` | **통과**(12) / **E0369** `cannot add` | 8 |
| `x == y` · `&x == &y` · `ptr::eq` | `true` · `true` · **`false`** | 8 |
| `let _: () = 식;` 여섯 줄 | **E0308 여섯 개** — `&Vec`·`&mut Vec`·`&{integer}`·`&String`·`&&String`·**`&str`** | 9 |
| `&t` 와 `rt` 의 주소 비교 | **같음**(`true`) · `size_of::<&String>()` = **8** | 10 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **주소 절댓값** | **런타임 ASLR** — 근거는 「같은가/다른가」뿐 |
| 참조 하나의 **8바이트** | **플랫폼**(64비트 포인터 폭) |
| **`&i32 + &i32` 가 되는 것** | **std 가 준 impl 범위** — 언어의 자동 역참조가 아니다 |
| **에러 번호가 상황별로 갈리는 것** | **rustc 구현**. 번호는 안정적이고 **문구·`help` 는 바뀐다** |
| **NLL 이 에디션과 무관한 것** | **컴파일러 버전** — `releases.html` 1.36.0 항목 + `--edition 2015` 실측 |
| `{integer}` 표기 | **rustc 의 추론 변수 표기** — 확정 전 상태를 보여 주는 것 |
| **별칭 규칙·재빌림·자동 역참조 규칙 자체** | **전부 언어 보장.** 실측과 Reference 가 일치했다 |
