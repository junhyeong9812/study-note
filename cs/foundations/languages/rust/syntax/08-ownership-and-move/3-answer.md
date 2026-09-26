# rust/syntax/08 — 소유권과 이동(move) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> 주소를 찍는 프로그램(2번)은 **디버그와 릴리스를 둘 다** 돌렸다 — `rustc --edition 2021 -O ex.rs`.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했다. **줄 번호는 그 실험 파일 기준**이라 질문의 발췌와 어긋날 수 있다.\
> ★ **주소값(`0x7ffc...`)은 실행마다 바뀐다**(ASLR). 출력을 그대로 옮기느라 남겨 두었을 뿐,\
> 근거로 읽을 칸은 「**같은가 / 다른가**」뿐이다(릴리스 바이너리를 세 번 돌려 관계가 고정임을 확인했다).\
> ★ 해제 시점은 컴파일러가 말해 주지 않으므로 **`impl Drop` 의 `println!`** 으로 관찰했다. 그것이 이 주제의 창이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 생김새가 같은 두 줄

**출력** — (가) `String`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s1`
 --> ex.rs:4:21
  |
2 |     let s1 = String::from("안녕");
  |         -- move occurs because `s1` has type `String`, which does not implement the `Copy` trait
3 |     let s2 = s1;
  |              -- value moved here
4 |     println!("s1 = {s1} / s2 = {s2}");
  |                     ^^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
3 |     let s2 = s1.clone();
  |                ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**출력** — (나) `i32`

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
n1 = 5 / n2 = 5
(종료 코드 0)
```

**왜 그런가**

- 컴파일되는 것은 **(나)** 뿐이다. (가)는 **E0382**, 제목 줄은 **`borrow of moved value: s1`** 이다.
- 이유 한 구절은 **`which does not implement the Copy trait`** 다.\
  ★ **크기도 힙도 아니다.** 갈리는 기준은 **`Copy` 트레이트를 구현했느냐** 하나뿐이다.
- `let s2 = s1;` 은 복사가 아니라 **이동**이고, 그 순간 `s1` 이라는 **이름이 죽는다.**

```text
   (가) String                         (나) i32
   let s2 = s1;                        let n2 = n1;
   +-------------+                     +-------------+
   | s1  [무효]  |                     | n1    5     |
   | s2  "안녕"  |                     | n2    5     |
   +-------------+                     +-------------+
     이름 하나만 산다  -> E0382           둘 다 산다  -> 통과
```

`rustc --explain E0382`:

> Since `MyStruct` is a type that is not marked `Copy`, the data gets moved out
> of `x` when we set `y`. This is fundamental to Rust's ownership system: outside
> of workarounds like `Rc`, a value cannot be owned by more than one variable.

> **이동(move)** — 소유권이 다른 이름으로 옮겨 가고 원래 이름이 무효가 되는 것.\
> 예: `let s2 = s1;` 뒤의 `s1` 은 「값이 이상한 변수」가 아니라 **쓸 수 없는 이름**이다.

### 2. ★ 이동하면 힙은 어떻게 되나

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
s1: 스택 0x7ffc753136d8 -> 힙 0x652c769e2d00 / len=15 cap=15
String 의 스택 크기 = 24 바이트
s2: 스택 0x7ffc75313830 -> 힙 0x652c769e2d00
힙 주소가 같은가? true  (= 깊은 복사가 없었다)
스택 주소가 같은가? false (= 세 칸이 복사되긴 했다)
s3(clone): 힙 0x652c769e2d20 / s2 와 같은가? false
(종료 코드 0)

===== 릴리스: rustc --edition 2021 -O ex.rs -o ex_rel =====
s1: 스택 0x7ffd60bcdce8 -> 힙 0x5f3165fe2d00 / len=15 cap=15
String 의 스택 크기 = 24 바이트
s2: 스택 0x7ffd60bcdcb0 -> 힙 0x5f3165fe2d00
힙 주소가 같은가? true  (= 깊은 복사가 없었다)
스택 주소가 같은가? false (= 세 칸이 복사되긴 했다)
s3(clone): 힙 0x5f3165fe2d20 / s2 와 같은가? false
(종료 코드 0)
```

**왜 그런가**

- **`p1 == p2` 는 `true`**, **`p2 == p3` 는 `false`** 다.
- `String` 은 스택에서 **24바이트**이고 안에 **포인터·길이·용량** 세 칸이 들어 있다.\
  `"안녕하세요"` 는 한글 다섯 자 × 3바이트라 `len=15 cap=15` 다.
- **릴리스에서도 답이 같았다.** 관계 넷이 한 글자도 안 바뀌었다.

```text
   이동 전                                 이동 후
   스택                 힙                 스택                 힙
   +------------+      +---------+        +------------+      +---------+
   | s1 ptr ----+----> | 안녕하세요|        | s1  [무효] |      | 안녕하세요|
   |    len 15  |      | 15바이트 |        | s2 ptr ----+----> | 15바이트 |
   |    cap 15  |      +---------+        |    len 15  |      +---------+
   +------------+                         |    cap 15  |
    24바이트                               +------------+
                                           힙 주소 동일 = 깊은 복사가 없다
```

```text
   clone() 은 다르다
   | s2 ptr ----+----> [안녕하세요]  0x...2d00
   | s3 ptr ----+----> [안녕하세요]  0x...2d20   <- 새로 할당했다
```

**근거로 읽어도 되는 칸과 안 되는 칸**

| 칸 | 읽어도 되나 | 이유 |
|---|---|---|
| `힙 주소가 같은가? true` | **근거** | 디버그·릴리스·재실행에서 고정 |
| `스택 주소가 같은가? false` | **근거** | 〃 |
| `s3 가 s2 와 같은가? false` | **근거** | 〃 |
| `String 의 스택 크기 = 24` | **근거**(64비트 한정) | 플랫폼 의존이라고 밝히면 된다 |
| `0x7ffc753136d8` 같은 **절댓값** | **아니다** | ASLR 로 실행마다 바뀐다 |

- 결론 — **이동은 스택 24바이트만 베끼고 힙은 안 건드린다.** 비싼 쪽은 `clone()` 이다.

### 3. ★★ 이 프로그램의 출력 순서

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
    블록 끝 직전
        [해제] b
        [해제] a
    drop(c) 호출 직전
        [해제] c
    drop(c) 뒤
    eat(d) 호출 직전
    eat 안: d 를 받았다
    eat 끝
        [해제] d
    eat(d) 뒤
    이동 완료, 블록 끝 직전
        [해제] e
(종료 코드 0)
```

**왜 그런가**

- **`[해제] b` 가 먼저**다. 같은 스코프의 변수는 **선언의 역순**으로 해제된다(LIFO).
- **`[해제] d` 가 `eat(d) 뒤` 보다 먼저** 찍힌다. `eat` 이 주인이 되었으니 **그 함수 몸통 끝**에서 해제된다.
- `[해제] e` 는 **한 번**이다. 이름이 `e1` 에서 `_e2` 로 옮겨 갔을 뿐 값은 하나다.\
  ★ 이것이 **double free 를 막는 자리**다 — 이동한 이름 쪽에서는 해제가 아예 생기지 않는다.

```text
   (1) 스코프 끝 — 선언 역순         (2) drop(c) — 앞으로 당긴다
   let _a = D("a")  +               let c = D("c");
   let _b = D("b")  |  +            drop(c);   --> [해제] c
   }                |  +-> [해제] b  ...
                    +----> [해제] a  }  <- 여기서는 아무 일도 없다
```

```text
   (3) 함수에 넘기면 주인이 바뀐다      (4) 이름만 바꿔도 해제는 한 번
   main            eat                let e1 = D("e");
   d --(이동)-->   d 를 받는다          let _e2 = e1;   <- 꼬리표만 이동
                   "eat 끝"            }
                   } -> [해제] d          -> [해제] e   (e1 쪽에서는 없음)
   "eat(d) 뒤"  <- 그 다음에 찍힌다
```

**해제 시점을 알아내는 방법이 왜 이것뿐인가**

- 이동 위반은 **컴파일러가 말해 준다**(E0382). 그러나 **해제 시점은 아무도 말해 주지 않는다** —\
  에러도 경고도 없고 프로그램은 조용히 잘 돈다.
- 그래서 `impl Drop` 안에 `println!` 을 넣어 **출력 순서로** 드러내는 것이 이 주제의 창이다.
- 락·파일·연결을 쥔 타입을 쓸 때 **이 창이 없으면 「왜 아직 안 풀렸지」를 못 잡는다**(목록의 **52번 주제**).

> **해제(drop)** — 값이 쥔 자원을 반납하는 것. 컴파일러가 스코프 끝에 그 호출을 끼워 넣는다.\
> 예: `String` 의 해제는 힙 버퍼를 반납한다. `Drop` 을 구현하면 그 순간 내 코드가 불린다.

### 4. ★ 섀도잉·대입·임시값의 해제 시점

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
warning: unused variable: `x`
 --> ex.rs:6:11
  |
6 |     { let x = D("첫째"); let x = D("둘째"); println!("    블록 끝 직전"); let _ = &x; }
  |           ^ help: if this is intentional, prefix it with an underscore: `_x`
  |
  = note: `#[warn(unused_variables)]` (part of `#[warn(unused)]`) on by default

warning: value assigned to `y` is never read
 --> ex.rs:7:19
  |
7 |     { let mut y = D("옛값"); println!("    대입 직전"); y = D("새값"); println!("    대입 직후"); let _ = &y; }
  |                   ^^^^^^^^^
  |
  = help: maybe it is overwritten before being read?
  = note: `#[warn(unused_assignments)]` (part of `#[warn(unused)]`) on by default

warning: 2 warnings emitted

    블록 끝 직전
        [해제] 둘째
        [해제] 첫째
    대입 직전
        [해제] 옛값
    대입 직후
        [해제] 새값
        [해제] 이름없음
    다음 줄
        [해제] 밑줄만
    let _ 다음 줄
    let _z 다음 줄
        [해제] 밑줄이름
(종료 코드 0)
```

**왜 그런가**

- **「첫째」는 블록 끝에서** 해제된다. **섀도잉은 앞의 값을 죽이지 않는다** — 이름만 가려진다.\
  그리고 역순이라 **「둘째」가 먼저** 해제된다(정본은 [**02번 주제**](../02-bindings-mut-and-shadowing/)).
- **「옛값」은 대입하는 그 줄에서** 해제된다. 같은 칸을 덮어쓰기 때문이다.
- **해제 시점이 다르다.** `let _ = D("밑줄만");` 은 **바인딩이 아니라 즉시 해제**,\
  `let _z = D("밑줄이름");` 은 **바인딩이라 블록 끝까지** 산다.
- 이름을 아예 안 준 `D("이름없음");` 은 **그 문 끝에서** 죽는다(임시값).

```text
   섀도잉                          대입
   let x = D("첫째");              let mut y = D("옛값");
   let x = D("둘째");  <- 새 칸     y = D("새값");  <- 같은 칸을 덮는다
   }  -> [해제] 둘째                      ^-- 이 줄에서 [해제] 옛값
      -> [해제] 첫째                }  -> [해제] 새값
   둘 다 블록 끝까지 산다             옛값은 대입 순간 죽는다
```

**락 가드에서 왜 사고가 되나 — 던져 보니 답이 반만 맞았다**

의미는 예상대로다. **가드를 즉시 버리면 임계 구역이 생기지 않는다.**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(A) 가드를 즉시 버리면 — drop(m.lock().unwrap())
    같은 스레드에서 try_lock 이 되나? true
(B) 가드를 이름에 묶으면 — let _guard = ...
    같은 스레드에서 try_lock 이 되나? false
(C) 블록을 나온 뒤: try_lock 이 되나? true
(종료 코드 0)
```

```text
   가드를 즉시 버림                      let _guard = m.lock()
   drop(m.lock().unwrap());             let _guard = m.lock().unwrap();
   try_lock -> true                     try_lock -> false   <- 여기부터 임계 구역
   /* 보호되지 않는다 */                 }  -> 가드 해제, try_lock -> true
```

★ **그런데 `let _ = m.lock();` 은 애초에 컴파일이 안 된다.** 던져서 알았다.

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error: non-binding let on a synchronization lock
 --> ex.rs:7:13
  |
7 |         let _ = m.lock().unwrap();
  |             ^ this lock is not assigned to a binding and is immediately dropped
  |
  = note: `#[deny(let_underscore_lock)]` (part of `#[deny(let_underscore)]`) on by default
help: consider binding to an unused variable to avoid immediately dropping the value
  |
7 |         let _unused = m.lock().unwrap();
  |              ++++++
help: consider immediately dropping the value
  |
7 -         let _ = m.lock().unwrap();
7 +         drop(m.lock().unwrap());
  |

error: aborting due to 1 previous error
```

- **`let_underscore_lock` 린트가 `deny` 기본**이라 **에러**다. 동기화 락에 한해 컴파일러가 막아 준다.
- 즉 「글자 하나로 임계 구역이 사라진다」는 **의미로는 맞고, 락에 대해서는 컴파일러가 잡아 준다.**\
  ★ **린트가 없는 다른 `Drop` 타입**(파일 핸들·스팬 가드·임시 디렉터리)에서는 **그대로 조용히 사라진다** — 위험한 쪽은 그쪽이다.
- `let _` 의 해제 시점 자체는 4번 출력의 `[해제] 밑줄만` 이 이미 보여 준다. 락은 그 위에 린트가 한 겹 더 있는 것뿐이다.
- 락의 정본은 목록의 **52번 주제**다.
- ★ 경고도 출력이다 — `unused_variables` 와 `unused_assignments` 가 「가려진 값」·「덮인 값」을 짚어 준다.

### 5. ★ 함수에 넘긴 값

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s`
 --> ex.rs:6:22
  |
4 |     let s = String::from("hello");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
5 |     let n = takes(s);
  |                   - value moved here
6 |     println!("{n} / {s}");
  |                      ^ value borrowed here after move
  |
note: consider changing this parameter type in function `takes` to borrow instead if owning the value isn't necessary
 --> ex.rs:1:13
  |
1 | fn takes(s: String) -> usize { s.len() }
  |    -----    ^^^^^^ this parameter takes ownership of the value
  |    |
  |    in this function
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
5 |     let n = takes(s.clone());
  |                    ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **컴파일되지 않는다. E0382**.
- `note` 는 **함수 선언의 인자 타입**을 가리키며 말한다 —\
  **`this parameter takes ownership of the value`**, 그리고 **`consider changing this parameter type ... to borrow instead`**.\
  ★ 컴파일러가 이미 「**빌려라**」라고 답을 주고 있다.
- `help:` 는 `.clone()` 을 제안하되 **`if the performance cost is acceptable`** 이라는 단서를 단다.\
  **조건 없는 추천이 아니다.**

**소유권을 넘기고도 계속 쓰는 세 길**

| 길 | 대가 |
|---|---|
| ① **빌린다** `fn borrows(s: &String)` | 없음. **이것이 기본값**이다 ([목록의 **10번 주제**](../10-borrowing-and-aliasing-rules/)) |
| ② **돌려받는다** `fn f(s: String) -> (String, usize)` | 반환 타입이 부푼다. 인자가 둘이면 튜플이 셋이 된다 |
| ③ **복제한다** `takes(s.clone())` | 힙 할당 하나. 사본이 따로 살아야 할 때만 |

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
돌려받음: hello / 5
빌려주면 그냥 산다: 5 / hello
(종료 코드 0)
```

```text
   ② 돌려받기                               ① 빌리기
   main --(이동)--> takes_and_gives         main --(&s)--> borrows
        <--(반환)--                              <--------
   반환 타입 (String, usize) 로 부푼다        반환 타입 usize 그대로
   ★ 이 불편함이 10번 빌림의 동기다            main 의 s 는 계속 산다
```

### 6. ★ 구조체에서 필드 하나만 꺼내면

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of partially moved value: `u`
  --> ex.rs:10:31
   |
 7 |     let name = u.name;                 // 필드 하나만 이동
   |                ------ value partially moved here
...
10 |     println!("구조체 전체 = {:?}", u);   // 이건?
   |                                    ^ value borrowed here after partial move
   |
   = note: partial move occurs because `u.name` has type `String`, which does not implement the `Copy` trait
   = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**출력** — 마지막 줄을 지우면 통과한다

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
이동한 필드 = 준
남은 필드 = 30
(종료 코드 0)
```

**왜 그런가**

- 거부되는 줄은 **마지막 줄**(`{:?}` 로 `u` 를 통째로 쓰는 줄)뿐이다. **`u.age` 줄은 통과한다.**
- 꼬리 문구가 다르다 — 1번·5번은 `moved value`, 여기는 **`partially moved value`** 다.
- `u.age` 가 되는 이유 — **이동은 칸 단위**라 빠져나간 칸만 죽고 나머지는 멀쩡하기 때문이다.
- 이 상태의 이름은 **부분 이동**(partial move)이다.

```text
   u                        let name = u.name;        u 를 통째로 쓰면
   +----------------+       +----------------+        +----------------+
   | name: "준"     |  -->  | name: [빠짐]   |        | name: [빠짐]   |  ^
   | age : 30       |       | age : 30  (OK) |        | age : 30       |  | E0382
   +----------------+       +----------------+        +----------------+
                             살아 있는 칸은 그대로      구멍 난 채로는 못 쓴다
```

### 7. `Drop` 을 구현한 타입에서 꺼내면

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0509]: cannot move out of type `Guard`, which implements the `Drop` trait
 --> ex.rs:7:13
  |
7 |     let n = g.name;                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |             ^^^^^^
  |             |
  |             cannot move out of here
  |             move occurs because `g.name` has type `String`, which does not implement the `Copy` trait
  |
help: consider borrowing here
  |
7 |     let n = &g.name;                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |             +
help: consider cloning the value if the performance cost is acceptable
  |
7 |     let n = g.name.clone();                    // Drop 을 구현한 타입에서 필드를 빼내면?
  |                   ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0509`.
```

**왜 그런가**

- **결과가 다르다.** 6번은 E0382(부분 이동한 뒤 전체를 쓸 때)였는데 여기는 **E0509**,\
  그것도 **꺼내는 줄 자체**에서 막힌다. 부분 이동이 **시작조차 안 된다.**
- 이유는 **소멸자**다.

`rustc --explain E0509`:

> Structs implementing the `Drop` trait have an implicit destructor that gets
> called when they go out of scope. This destructor may use the fields of the
> struct, so moving out of the struct could make it impossible to run the
> destructor. Therefore, we must think of all values whose type implements the
> `Drop` trait as single units whose fields cannot be moved.

- 즉 **소멸자가 그 필드를 쓸 수 있으므로** 컴파일러는 `Drop` 타입을 **쪼갤 수 없는 한 덩어리**로 본다.
- 컴파일러가 제안하는 둘 — **`&g.name` 으로 빌리기**와 **`g.name.clone()` 으로 복제하기**.
- 정말로 꺼내야 하면 **`mem::take`/`mem::replace`** 를 쓴다 — 빈 값을 넣어 두고 알맹이를 가져오는 관용구다.\
  정본은 목록의 **44번 주제**다.

```text
   일반 구조체                        Drop 구현체
   +-------------+                   +-------------+
   | name [빠짐] |  가능              | name        |  <- 꺼내려 하면 E0509
   | age  30     |                   +-------------+
   +-------------+                     소멸자가 이 칸을 쓸지도 모른다
     칸 단위                            = 쪼갤 수 없는 한 덩어리
```

### 8. 이동이 일어나는 자리를 전부 짚어라

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
(1) 다른 이름에 대입
    끝
        [해제] 1-대입
(2) 함수 인자
        [해제] 2-인자
    끝
(3) 구조체 필드로
    끝
        [해제] 3-필드
(4) Vec 에 push
    끝
        [해제] 4-push
(5) 튜플에 담기
    끝
        [해제] 5-튜플
(6) match 가 값을 받으면
    match 안 6-match
        [해제] 6-match
    끝
(7) move 클로저 (34번이 정본)
    클로저 안 7-클로저
    끝
        [해제] 7-클로저
(8) main 끝
(종료 코드 0)
```

**왜 그런가**

- **일곱 개 전부 이동이다.**

| 자리 | 해제되는 곳 |
|---|---|
| `let b = a;` | 새 이름의 스코프 끝 |
| `consume(a)` | 받은 함수 안 — 반환값을 아무도 안 받으면 **그 문 끝** |
| `Wrap { inner: a }` | 그 구조체의 스코프 끝 |
| `v.push(a)` | 그 `Vec` 의 스코프 끝 |
| `(a, 1)` | 그 튜플의 스코프 끝 |
| `match a { Some(d) => .. }` | **그 팔의 블록 끝** |
| `move \|\| .. a ..` | 그 클로저의 스코프 끝 |

- **다음 줄보다 먼저 해제되는 둘은 (2)와 (6)** 이다.
  - **(2)** — `consume(a)` 가 돌려준 값을 아무도 안 받아서 **이름 없는 임시값**이 됐다.\
    임시값은 **그 문이 끝나는 자리**에서 죽으므로 `끝` 보다 먼저 찍혔다.
  - **(6)** — `match` 가 값을 받으면 팔 안의 `d` 가 주인이 되고 **팔의 블록 끝**에서 죽는다.
- 한 문장 규칙 — **값을 「값으로」 넘기는 모든 자리가 이동이다.** `&`/`&mut` 를 붙이면 아니다.

```text
   (2) 반환값을 아무도 안 받으면              (6) match 가 값을 받으면
   consume(a);                              match a { Some(d) => { ... } }
        |                                                 |         |
   임시값이 된다 -> 그 문 끝에서 해제           d 가 주인   팔의 블록 끝에서 해제
```

### 9. `for` 와 소유권

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `v`
 --> ex.rs:6:22
  |
2 |     let v = vec![String::from("a"), String::from("b")];
  |         - move occurs because `v` has type `Vec<String>`, which does not implement the `Copy` trait
3 |     for x in v {
  |              - `v` moved due to this implicit call to `.into_iter()`
...
6 |     println!("{:?}", v);
  |                      ^ value borrowed here after move
  |
note: `into_iter` takes ownership of the receiver `self`, which moves `v`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/collect.rs:310:18
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider iterating over a slice of the `Vec<String>`'s content to avoid moving into the `for` loop
  |
3 |     for x in &v {
  |              +
```

**출력** — 배열은 다르다

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
10 20 30 | a = [10, 20, 30]
0 1 2 
v = [1, 2, 3]
(종료 코드 0)
```

**왜 그런가**

- `for x in v` 는 **`v.into_iter()` 를 암묵적으로 부른다** — 컴파일러가 그 이름을 직접 댄다\
  (**`moved due to this implicit call to .into_iter()`**). 그 메서드가 `self` 를 먹는다.
- 세 형태에서 `x` 의 타입은 실측으로 각각 이렇다([**05번 주제**](../05-control-flow-loops-and-labels/)).

```text
   for x in v       -> x : String      v 를 먹는다.  순회 뒤 v 없음
   for x in &v      -> x : &String     빌린다.      v 그대로
   for x in &mut v  -> x : &mut String 빌린다(가변). v 그대로, 고칠 수 있다
```

- **배열은 `for x in a` 뒤에도 `a` 를 쓸 수 있다.** `[i32; 3]` 이 **`Copy`** 라서 `for` 가 **사본을 먹었기** 때문이다.\
  ★ **`Copy` 인지는 컨테이너 타입이 정한다** — `Vec<i32>` 는 원소가 `Copy` 여도 `Copy` 가 아니다.
- 이 셋의 정본은 [목록의 **37번 주제**](../37-intoiterator-three-forms-iter-iter-mut-into-iter/)(`IntoIterator` 세 형태)다.

### 10. 실행되지 않는 갈래와 루프

**출력** — 조건부 이동

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s`
 --> ex.rs:6:16
  |
4 |     let s = String::from("조건부");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
5 |     if cond { eat(s); }                          // 여기서만 이동한다
  |                   - value moved here
6 |     println!("{s}");                             // 실행은 절대 안 먹었는데?
  |                ^ value borrowed here after move
```

**출력** — 루프 안의 이동

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: use of moved value: `s`
 --> ex.rs:5:13
  |
3 |     let s = String::from("한 번뿐");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
4 |     for _ in 0..3 {
  |     ------------- inside of this loop
5 |         eat(s);                 // 루프 안에서 이동하면?
  |             ^ value moved here, in previous iteration of loop
```

**왜 그런가**

- **컴파일되지 않는다.** `cond` 가 절대 참이 안 된다는 사실은 **판정에 아무 영향을 주지 않는다.**
- 그 답이 말하는 것 — **이 검사는 컴파일 타임에 끝난다.**\
  **어떤 경로에서든 이동이 일어나면** 그 뒤의 이름은 죽은 것으로 본다. 런타임 추적이 아니다.
- 루프 쪽은 꼬리 문구가 다르다 — **`value moved here, in previous iteration of loop`**.\
  「첫 바퀴는 성공하는데 두 번째가 안 되는」 모양이라 **이름이 아니라 횟수**가 문제다.

**그런데 실행 시점에는 갈래에 따라 해제가 달라진다**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
--- 인자 없이 실행: ./ex_dbg
cond = false
    스코프 끝 직전
        [해제] 조건부
--- 인자를 주고 실행: ./ex_dbg x
cond = true
    eat 안 조건부
        [해제] 조건부
    스코프 끝 직전
```

- 같은 바이너리가 **두 실행에서 다른 자리에 해제**했다. 이것을 하는 것이 **드롭 플래그**다.
- ★ **보장은 「정확히 한 번 해제된다」까지**이고, **플래그의 존재와 형태는 구현**이다.\
  최적화가 갈래를 확정할 수 있으면 사라질 수도 있다 — **관찰이지 보장이 아니다.**

> **드롭 플래그(drop flag)** — 값이 이동됐는지를 런타임에 기억하는 숨은 1비트.\
> 예: `if cond { eat(d); }` 뒤의 스코프 끝에서 「아직 내 것인가」를 그 비트로 판단한다.

### 11. `clone()` 과 `drop()`

**출력**

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
a = 원본에 덧붙임 / b = 원본
첫째 / 둘째 / v 는 그대로 ["첫째", "둘째"]
(종료 코드 0)
```

**출력** — `drop(s)` 뒤에 `s` 를 쓰면

```text
===== 디버그: rustc --edition 2021 ex.rs -o ex_dbg =====
error[E0382]: borrow of moved value: `s`
 --> ex.rs:4:16
  |
2 |     let s = String::from("자원");
  |         - move occurs because `s` has type `String`, which does not implement the `Copy` trait
3 |     drop(s);
  |          - value moved here
4 |     println!("{s}");
  |                ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
3 |     drop(s.clone());
  |           ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

**왜 그런가**

- **`clone()` 은 힙을 새로 할당해 내용을 베낀다.** 근거는 둘이다.
  - **주소 실측**(2번) — `s3` 의 힙 주소가 `s2` 와 **다르다**.
  - **독립성 실측**(위 출력) — `a` 를 고쳐도 `b` 는 안 변한다. **둘은 남남**이다.
- 제안에 붙은 조건절은 **`if the performance cost is acceptable`** 이다.\
  붙어 있는 이유 — `clone()` 은 **할당을 하나 더 하는 선택**이지 공짜 수선이 아니기 때문이다.\
  컴파일러는 그 비용을 판단할 수 없으니 **판단을 사람에게 돌려준다.**
- **쓰면 안 되는 자리 셋.**
  - **루프 안에서** — 바퀴마다 할당이 는다. 10번 에러의 `eat(s.clone())` 제안이 정확히 그 함정이다.
  - **읽기만 하는데** 복제 — `&` 로 끝나는 자리다.
  - **주인을 안 정한 채** 복제 — 사본이 갈라져 나중에 어느 쪽이 정본인지 모르게 된다.
- **`drop(s)` 뒤에 `s` 를 쓰면 E0382** 다 — 다른 이동과 **완전히 같은 에러**다.\
  ★ 그 번호가 말하는 것은 **`drop` 이 특별한 문법이 아니라 값을 먹는 평범한 함수**라는 것이다.\
  해제가 일어나는 이유도 「`drop` 이라서」가 아니라 「**먹은 쪽의 몸통이 끝나서**」다.

### 12. 다른 주제와 잇기

- **불편함을 푸는 장치** — **빌림** `&`/`&mut`. 정본은 [목록의 **10번 주제**](../10-borrowing-and-aliasing-rules/)다.\
  이 주제의 5번(돌려받기의 반환 타입 팽창)이 그 동기다. 컴파일러도 `to borrow instead` 라고 말한다.
- **`Copy` 판정과 `Drop` 시점의 전수** — [목록의 **09번 주제**](../09-copy-clone-and-drop/)(`Copy`와 `Clone`, 그리고 `Drop` 시점).\
  이 주제에서는 `Drop` 을 **관찰 도구로만** 썼다.
- **런타임 비용을 내고 한 소유자 규칙을 완화하는 도구** — `Rc`/`Arc`, 목록의 **41번 주제**.\
  `--explain E0382` 도 `outside of workarounds like Rc` 라고 그 존재를 가리킨다.
- **모델 자체의 논증** — [`../../언어-특성/README.md`](../../언어-특성/README.md) §2 가 정본이다.\
  「왜 GC 도 수동도 거부했나」·「청구서가 왜 사람의 시간인가」는 거기고,\
  **여기는 그 규칙이 코드에서 어떤 에러와 어떤 해제 순서로 나타나나**다.\
  역사는 [`../../../../../../history/rust/03-소유권-시스템.md`](../../../../../../history/rust/03-소유권-시스템.md).
- **에러가 아니라 출력 순서로만 드러나는 사실** — **해제 시점 전부**다.\
  선언 역순 해제 · `drop()` 이 앞당기는 것 · 이동이 해제를 받은 쪽으로 옮기는 것 ·\
  섀도잉이 앞의 값을 안 죽이는 것 · 대입이 죽이는 것 · `let _` 이 즉시 죽이는 것 · 드롭 플래그.\
  **컴파일러는 이 중 어느 것도 말해 주지 않는다.** `impl Drop` + `println!` 이 유일한 창이다.

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| `let s2 = s1;`(String) | **E0382** + `does not implement the Copy trait` + `help: consider cloning` | 1 |
| `let n2 = n1;`(i32) | **통과** — `n1 = 5 / n2 = 5` | 1 |
| `rustc --explain E0382` | 공식 설명 인용(`a value cannot be owned by more than one variable`) | 1·12 |
| `as_ptr` 비교 + `clone` (디버그·릴리스) | 힙 주소 **같음** / 스택 주소 **다름** / clone 힙 **다름** · `size_of::<String>() = 24` | 2 |
| 릴리스 바이너리 3회 재실행 | 주소 **절댓값은 매번 다르고** 관계는 고정 | 2 |
| `Drop` 4장면(블록·`drop()`·함수 전달·이름 이동) | 역순 해제 · 앞당김 · 함수 안 해제 · **한 번만** 해제 | 3 |
| `Drop` 4장면(섀도잉·대입·임시값·`let _`) | 섀도잉 **안 죽임** / 대입 **죽임** / 임시값 문 끝 / `let _` **즉시** | 4 |
| `let n = takes(s);` | **E0382** + `this parameter takes ownership` + `to borrow instead` | 5 |
| `takes_and_gives` / `borrows(&s)` | `돌려받음: hello / 5` · `빌려주면 그냥 산다: 5 / hello` | 5 |
| `let name = u.name;` 뒤 `u` 전체 사용 | **E0382 `partially moved`** — `u.age` 줄은 **통과** | 6 |
| `Drop` 구현체에서 필드 반출 | **E0509** + `--explain` 인용(소멸자가 필드를 쓸 수 있다) | 7 |
| 이동 7자리 + `Drop` | 전부 이동 · **(2)와 (6)만 다음 줄보다 먼저** 해제 | 8 |
| `for x in v`(Vec\<String\>) | **E0382** + `implicit call to .into_iter()` + `help: &v` | 9 |
| `for x in a`([i32; 3]) | **통과** — `a = [10, 20, 30]` 가 살아 있다 | 9 |
| `if cond { eat(s); }` 뒤 사용 | **E0382** — 실행되지 않는 갈래도 이동 | 10 |
| `for _ in 0..3 { eat(s); }` | **E0382** `in previous iteration of loop` | 10 |
| 같은 바이너리 2회(인자 없이/있게) | 해제 자리가 **갈린다** — 드롭 플래그 | 10 |
| `a.clone()` 뒤 `a` 수정 | `a = 원본에 덧붙임 / b = 원본` — 남남이다 | 11 |
| `drop(s);` 뒤 사용 | **E0382** — 다른 이동과 같은 번호 | 11 |
| `Copy` 8종 대조 + `String` 담은 구조체·튜플 | 8종 전부 원본 생존 · 나머지는 `.clone()` 필요 | 문법 절 |
| `#[derive(Copy)]` + `String` 필드 | **E0204** `this field does not implement Copy` | 문법 절 |
| `let first = v[0];` | **E0507** `cannot move out of index` | 문법 절 |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| **주소 절댓값**(`0x7ffc...`) | **런타임 ASLR** — 실행마다 바뀐다. 근거는 「같은가/다른가」뿐 |
| `String` 의 스택 크기 24바이트 | **플랫폼**(64비트). 포인터 폭이 다르면 달라진다 — 이 머신에서만 잰 값이다 |
| **조건부 이동의 드롭 플래그** | **구현** — 언어는 「한 번만 해제된다」만 보장한다 |
| 이동에서 **스택 24바이트 복사가 실제로 일어나는지** | **최적화** — 의미(힙 미복사)는 보장, 코드 생성은 구현 |
| 에러·경고 **문구와 `help` 제안** | **rustc 구현**. 버전이 오르면 바뀐다 — **에러 번호**가 더 안정적이다 |
| `unused_variables`·`unused_assignments`·`dead_code` 가 **경고**인 것 | **린트 설정**. `-D warnings` 로 에러가 된다 |
| **소유권·이동·해제 순서 규칙 자체** | **전부 언어 보장.** 디버그·릴리스에서 답이 갈린 자리가 **하나도 없었다** |
