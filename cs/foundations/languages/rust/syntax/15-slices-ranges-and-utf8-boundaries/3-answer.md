# rust/syntax/15 — 슬라이스 `&[T]`·범위 문법·UTF-8 경계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러·경고·패닉은 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 문서의 결과는 전부 **2021** 기준이다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고, **진단·패닉의 줄 번호는 그 파일 기준**이라\
> 질문 쪽 발췌와 어긋날 수 있다. 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ `rustc --explain` 은 **확인용으로만** 열었고 본문에 옮기지 않았다.
> ★★ **패닉 블록에서 다시 돌리면 바뀌는 칸은 하나다** — `thread 'main' (3085086)` 의 **괄호 안 숫자**(OS 스레드 id).\
> 같은 바이너리를 3회 돌려 셋 다 달랐다. **`ex.rs:줄:칸`·메시지 본문·`note:` 줄·종료 코드는 안 바뀐다.**
> ★ 이 주제의 고유 창은 **바이트 격자**(1·2번)와 **`catch_unwind` 로 패닉 여럿을 한 판에 보기**(4·5번)다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 세 칸이 전부 갈리고, `chars` 도 「글자」가 아니다

**출력**

```text
===== 소스: ex.rs =====
// 같은 글자를 세 가지로 세어 본다 — len()·chars()·bytes() 가 각각 무엇을 세나
fn main() {
    // (사람이 보는 글자 수, 문자열, 설명) — 배열이라 순서가 고정이다
    let samples: [(usize, &str, &str); 7] = [
        (2, "Hi", "ASCII 두 글자"),
        (1, "한", "한글 한 글자(완성형)"),
        (2, "한글", "한글 두 글자(완성형)"),
        (1, "\u{1112}\u{1161}\u{11AB}", "한글 한 글자(조합형 자모 셋)"),
        (1, "e\u{0301}", "e + 결합 악센트"),
        (1, "\u{1F1F0}\u{1F1F7}", "국기 이모지(지역 표시자 둘)"),
        (1, "\u{1F468}\u{200D}\u{1F469}\u{200D}\u{1F467}", "가족 이모지(ZWJ 로 이은 셋)"),
    ];

    println!("{:>4} {:>6} {:>6} {:>6}  {}", "len", "chars", "bytes", "사람", "설명");
    for (human, s, desc) in samples {
        println!("{:>4} {:>6} {:>6} {:>6}  {}",
                 s.len(), s.chars().count(), s.bytes().count(), human, desc);
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
 len  chars  bytes     사람  설명
   2      2      2      2  ASCII 두 글자
   3      1      3      1  한글 한 글자(완성형)
   6      2      6      2  한글 두 글자(완성형)
   9      3      9      1  한글 한 글자(조합형 자모 셋)
   3      2      3      1  e + 결합 악센트
   8      2      8      1  국기 이모지(지역 표시자 둘)
  18      5     18      1  가족 이모지(ZWJ 로 이은 셋)
(종료 코드 0)
```

**왜 그런가**

| 문자열 | `len()` | `chars()` | 사람 | 어긋난 이유 |
|---|---|---|---|---|
| `"Hi"` | 2 | 2 | 2 | ASCII — **셋이 같은 유일한 경우** |
| `"한"`(완성형) | 3 | 1 | 1 | 한글 완성형 한 글자가 **UTF-8 3바이트** |
| `"한글"` | 6 | 2 | 2 | 3 + 3 |
| 조합형 `한`(자모 셋) | 9 | **3** | **1** | 초성·중성·종성이 **각각 다른 `char`** |
| `e` + 악센트 | 3 | **2** | **1** | 결합 문자가 **따로 세어진다** |
| 국기 이모지 | 8 | **2** | **1** | 지역 표시자 **둘**이 한 그림이 된다 |
| 가족 이모지 | 18 | **5** | **1** | 사람 셋 + **ZWJ 둘** |

- **`len()` 과 `bytes().count()` 는 언제나 같다** — 둘 다 UTF-8 바이트 수다.\
  다른 것은 **비용**이다: `len()` 은 O(1)(길이를 들고 있다), `bytes().count()` 는 O(n)(세어 본다).
- ★★ **아래 네 줄이 이 주제의 핵심**이다 — `chars().count()` 가 **사람이 세는 글자 수가 아니다.**\
  `chars()` 가 주는 것은 **유니코드 스칼라 값**이고, 사람이 보는 한 덩어리는 **자소 묶음**(grapheme cluster)이다.
- ★ 「그러면 `chars()` 를 쓰면 되겠지」가 이 주제에서 가장 흔한 두 번째 오해다((2-summary) 「어디서 틀리나 2」).
- ★ 출력 표의 칸이 안 맞아 보이는 것도 같은 집안이다 — **`{:>6}` 은 표시 폭이 아니라 `char` 개수로 채운다.**

### 2. ★★ 컴파일은 통과하고 **실행**에서 패닉한다 — 종료 코드 101

**출력**

```text
===== 소스: ex.rs =====
// UTF-8 경계를 안 맞추고 자르면 — 실행 시점에 패닉한다
fn main() {
    let s = "한글 abc";
    println!("자르기 전: {}", s);
    let first = &s[0..1];
    println!("여기는 안 찍힌다: {}", first);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
자르기 전: 한글 abc

thread 'main' (3085086) panicked at ex.rs:5:19:
byte index 1 is not a char boundary; it is inside '한' (bytes 0..3) of `한글 abc`
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

★ **대조할 것은 괄호 안의 숫자가 아니라 「어느 바이트에서, 어느 문자 경계 때문에 멈췄나」라는 성질이다.**
`(…)` 안의 스레드 id 는 **실행마다 바뀐다**(같은 바이너리를 3회 돌려 전부 달랐다).

**왜 그런가**

- ★★ **컴파일러가 한 마디도 안 했다.** `===== rustc … =====` 배너 아래가 비어 있다 —\
  **이 주제의 사고가 컴파일을 통과한다**는 것이 이 빈 줄의 뜻이다.
- **메시지 한 줄이 네 가지**를 말한다.

```text
   byte index 1 is not a char boundary; it is inside '한' (bytes 0..3) of `한글 abc`
              ^                                      ^^^^^ ^^^^^^^^^^^     ^^^^^^^^^
              |                                        |         |             |
        (가) 어느 바이트가                     (나) 어느 문자 (다) 그 문자가    (라) 어느
             경계가 아닌가                          안이었나     차지한 범위       문자열이었나
```

- ★ **`(다)` 가 곧 처방이다** — `bytes 0..3` 을 읽으면 **0 이나 3 으로 옮기면 된다**는 걸 바로 안다.\
  `&s[0..3]` 은 `"한"` 을 준다(3번 답의 `s.get(0..3)` 참고).
- **「자르기 전」 줄은 찍힌다.** 패닉은 그 줄에서 프로그램을 끝내므로 **다음 줄만** 안 찍힌다.
- **종료 코드는 `101`** 이다(기본 패닉 처리의 값). 쉘에서 `$?` 로 패닉을 가려낼 수 있다.
- **바뀌는 칸은 괄호 안 스레드 id 하나**다. 위치(`ex.rs:5:19`)·본문·`note:` 줄·종료 코드는 고정이다.

### 3. ★ `get` 은 `[]` 가 패닉하는 **모든** 경우에 `None` 을 준다

**출력**

```text
===== 소스: ex.rs =====
// get 은 [] 가 패닉하는 자리에서 무엇을 주나
fn main() {
    let s = "한글 abc";
    let v: Vec<i32> = vec![10, 20, 30];
    let sl: &[i32] = &v[..];

    println!("s.get(0..1)  = {:?}", s.get(0..1));
    println!("s.get(0..3)  = {:?}", s.get(0..3));
    println!("s.get(0..99) = {:?}", s.get(0..99));
    println!("s.get(4..2)  = {:?}", s.get(4..2));
    println!("sl.get(7)    = {:?}", sl.get(7));
    println!("sl.get(1..2) = {:?}", sl.get(1..2));
    println!("sl.get(2..1) = {:?}", sl.get(2..1));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.get(0..1)  = None
s.get(0..3)  = Some("한")
s.get(0..99) = None
s.get(4..2)  = None
sl.get(7)    = None
sl.get(1..2) = Some([20])
sl.get(2..1) = None
(종료 코드 0)
```

**왜 그런가**

| 던진 것 | `[]` 였다면 | `get` 은 | 무엇이 잘못이었나 |
|---|---|---|---|
| `s.get(0..1)` | 패닉(경계 아님) | `None` | **문자 경계 위반** |
| `s.get(0..3)` | `"한"` | `Some("한")` | 정상 — **경계가 맞았다** |
| `s.get(0..99)` | 패닉 | `None` | **길이 초과** |
| `s.get(4..2)` | 패닉 | `None` | **역순 범위** |
| `sl.get(7)` | 패닉 | `None` | 길이 초과(정수 인덱스) |
| `sl.get(1..2)` | `[20]` | `Some([20])` | 정상 |
| `sl.get(2..1)` | 패닉 | `None` | 역순 범위 |

- ★★ **경계 위반·길이 초과·역순 셋 다 `None`** 이다. 예외가 없다.
- **슬라이스의 `get` 도 같은 성질**이고, 인덱스의 **종류에 따라 돌려주는 타입만 다르다** —\
  `sl.get(1)` 은 `Option<&i32>`(원소 하나), `sl.get(1..2)` 는 `Option<&[i32]>`(슬라이스)다.\
  출력에서 `Some(20)` 과 `Some([20])` 의 대괄호가 그 차이다.
- **판단 기준 한 줄** — **인덱스가 밖에서 왔으면 `get`, 내가 방금 만들었으면 `[]`.**\
  `[]` 를 쓸 때는 **왜 안전한지 주석 한 줄**을 남긴다. 그것이 이 선택의 대가다.

### 4. ★★ 컴파일이 거부한다 — 린트 `unconditional_panic`, 기본 `deny`

**출력**

```text
===== 소스: ex.rs =====
// 범위를 벗어난 인덱스 — 배열에서
fn main() {
    let arr = [10, 20, 30, 40, 50];
    let i = 7;
    println!("배열 길이 {}", arr.len());
    println!("{}", arr[i]);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: this operation will panic at runtime
 --> ex.rs:6:20
  |
6 |     println!("{}", arr[i]);
  |                    ^^^^^^ index out of bounds: the length is 5 but the index is 7
  |
  = note: `#[deny(unconditional_panic)]` on by default

error: aborting due to 1 previous error
```

**왜 그런가**

- ★★ **실행까지 가지 않는다.** `let i = 7;` 로 변수에 넣어도 **상수 전파**에 걸린다.
- **경고가 아니라 에러**다 — 린트 이름 **`unconditional_panic`** 이 **기본 `deny`** 다.
- ★ **에러 번호가 없다**(`error[E0…]` 가 아니다) — `--explain` 으로 찾을 수 없는 부류다.\
  12번에서 만난 `error: lifetime may not live long enough` 와 같은 집안이다.

**`Vec` 으로 바꾸면 안 잡힌다** — 길이가 **타입에 없기** 때문이다. `Vec`·슬라이스는 런타임에 길이가 정해진다.
그래서 셋을 나란히 보려면 패닉을 받아 내야 한다.

```text
===== 소스: ex.rs =====
// 배열·Vec·슬라이스의 범위 밖 인덱스를 한 프로그램에서 셋 다 본다
// (패닉은 프로그램을 끝내므로 catch_unwind 로 받아 다음 실험으로 넘어간다)
// ★ 표시줄도 eprintln! 로 낸다 — 패닉 메시지와 같은 stderr 에 실려 순서가 섞이지 않는다
use std::panic::catch_unwind;

fn main() {
    let arr: [i32; 5] = [10, 20, 30, 40, 50];
    let v: Vec<i32> = vec![10, 20, 30, 40, 50];
    let sl: &[i32] = &v[..];
    let i = std::env::args().count() + 6;   // 인자 없이 돌리면 7

    eprintln!("--- 배열 [i32; 5] ---");
    let _ = catch_unwind(|| arr[i]);
    eprintln!("--- Vec<i32> ---");
    let _ = catch_unwind(|| v[i]);
    eprintln!("--- 슬라이스 &[i32] ---");
    let _ = catch_unwind(|| sl[i]);
    eprintln!("--- 셋 다 패닉했고 메시지가 같다 ---");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
--- 배열 [i32; 5] ---

thread 'main' (3400305) panicked at ex.rs:13:29:
index out of bounds: the len is 5 but the index is 7
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
--- Vec<i32> ---

thread 'main' (3400305) panicked at ex.rs:15:30:
index out of bounds: the len is 5 but the index is 7
--- 슬라이스 &[i32] ---

thread 'main' (3400305) panicked at ex.rs:17:29:
index out of bounds: the len is 5 but the index is 7
--- 셋 다 패닉했고 메시지가 같다 ---
(종료 코드 0)
```

★ **대조할 것은 숫자가 아니라 「셋의 메시지가 한 글자도 같다」는 성질이다.**
괄호 안 숫자가 **셋 다 같은 것**이 그 숫자가 **스레드 id** 라는 증거이기도 하다(같은 스레드에서 났다).

- ★ **`note: run with RUST_BACKTRACE=1 …` 줄은 첫 패닉에만 붙는다.** 두 번째부터는 안 나온다.
- ★ 표시줄을 `println!` 로 두면 **stdout 과 stderr 가 갈려 파이프에서 순서가 뒤집힌다.**\
  `eprintln!` 로 같은 stream 에 실어야 **다시 돌려도 순서가 고정**된다(계약의 「순서가 보장 안 되는 출력 금지」).

**같은 파일에 문자열 경계 위반을 함께 두면 — 컴파일러는 배열 쪽만 짚는다.**

```text
===== 소스: ex.rs =====
// 리터럴을 상수 범위로 자르면 컴파일 타임에 잡히나 — 배열의 상수 인덱스와 비교한다
fn main() {
    let a = &"한글"[0..1];          // 경계 아님
    let b = &[10, 20, 30][5];       // 배열 범위 밖
    println!("{} {}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error: this operation will panic at runtime
 --> ex.rs:4:14
  |
4 |     let b = &[10, 20, 30][5];       // 배열 범위 밖
  |              ^^^^^^^^^^^^^^^ index out of bounds: the length is 3 but the index is 5
  |
  = note: `#[deny(unconditional_panic)]` on by default

error: aborting due to 1 previous error
```

★★ **잘못이 둘인데 진단은 하나다.** 배열 줄을 지우면 문자열 줄은 그대로 컴파일되고 **실행에서 죽는다**((2-summary) (6)).

- ★★ **문구가 한 글자 다르다** — **컴파일 타임은 `the length is 5`, 런타임 패닉은 `the len is 5`**.\
  **두 경로가 서로 다른 코드에서 나온다는 증거**다. **메시지 글자로 테스트를 짜면 안 되는 이유**이기도 하다.

### 5. ★ `chunks` 는 꼬리가 짧고 `windows` 는 겹친다 — 크기 0 만 패닉

**출력**

```text
===== 소스: ex.rs =====
// 길이 7 을 3 으로 나누는 여섯 가지
fn main() {
    let v: Vec<i32> = (0..7).collect();
    let s: &[i32] = &v[..];
    println!("split_at(3)     -> {:?}", s.split_at(3));
    println!("chunks(3)       -> {:?}", s.chunks(3).collect::<Vec<_>>());
    println!("chunks_exact(3) -> {:?}", s.chunks_exact(3).collect::<Vec<_>>());
    println!("rchunks(3)      -> {:?}", s.rchunks(3).collect::<Vec<_>>());
    println!("windows(3)      -> {:?}", s.windows(3).collect::<Vec<_>>());
    println!("windows(8)      -> {:?}", s.windows(8).collect::<Vec<_>>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
split_at(3)     -> ([0, 1, 2], [3, 4, 5, 6])
chunks(3)       -> [[0, 1, 2], [3, 4, 5], [6]]
chunks_exact(3) -> [[0, 1, 2], [3, 4, 5]]
rchunks(3)      -> [[4, 5, 6], [1, 2, 3], [0]]
windows(3)      -> [[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6]]
windows(8)      -> []
(종료 코드 0)
```

**왜 그런가**

| 메서드 | 돌려주는 것 | 끝이 안 떨어지면 |
|---|---|---|
| `split_at(n)` | **튜플** `(&[T], &[T])` | 해당 없음 — 딱 둘로 가른다 |
| `chunks(n)` | 이터레이터 | ★ **마지막 조각이 짧다**(`[6]`) |
| `chunks_exact(n)` | 이터레이터 | 짧은 조각을 **버린다**. `remainder()` 로 받는다 |
| `rchunks(n)` | 이터레이터 | ★ **짧은 조각이 앞**에 온다(`[0]`) |
| `windows(n)` | 이터레이터 | 겹치며 민다. 개수 = **`len - n + 1`** |

- **`windows(3)` 의 개수는 `7 - 3 + 1 = 5`** 다. 출력의 다섯 조각이 그것이다.
- **`windows(8)` 은 빈 이터레이터**다 — `n > len` 이면 조각이 없다. **패닉이 아니다.**
- **`chunks_exact(3).remainder()` 는 `[6]`** 을 준다((2-summary) (7) 블록).

**그런데 크기 0 은 패닉이다** — `windows(8)` 과 규칙이 다르다.

```text
===== 소스: ex.rs =====
// chunks(0) · windows(0) · split_at(len+1) 은 무엇을 하나 — 셋 다 던져 본다
// ★ 표시줄을 eprintln! 로 내 패닉 메시지와 같은 stream 에 둔다
use std::panic::catch_unwind;

fn main() {
    let v: Vec<i32> = (0..7).collect();
    let s: &[i32] = &v[..];

    eprintln!("--- chunks(0) ---");
    let _ = catch_unwind(|| s.chunks(0).count());
    eprintln!("--- windows(0) ---");
    let _ = catch_unwind(|| s.windows(0).count());
    eprintln!("--- split_at(8) ---");
    let _ = catch_unwind(|| s.split_at(8).0.len());
    eprintln!("--- 셋 다 패닉 ---");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
--- chunks(0) ---

thread 'main' (3406167) panicked at ex.rs:10:31:
chunk size must be non-zero
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
--- windows(0) ---

thread 'main' (3406167) panicked at ex.rs:12:31:
window size must be non-zero
--- split_at(8) ---

thread 'main' (3406167) panicked at ex.rs:14:31:
mid > len
--- 셋 다 패닉 ---
(종료 코드 0)
```

★ **대조할 것은 숫자가 아니라 세 메시지가 서로 다르다는 성질이다.**

- ★ **`windows(8)` 은 빈 이터레이터인데 `windows(0)` 은 패닉**이다.\
  「범위를 넘으면 빈 것」과 「**0 은 값이 아니라 잘못**」이 **다른 규칙**이다 —\
  0칸 창문은 무한히 많으니 셀 수가 없다.
- `split_at(8)` 의 메시지는 **`mid > len`** 이다 — 인자 이름(`mid`)을 그대로 쓴다.

### 6. ★★ 둘 다 거부된다 — **E0308** 이 두 개

**출력**

```text
===== 소스: ex.rs =====
// &Vec<i32> 를 받는 함수에 배열·배열 슬라이스를 넘기면 — 둘 다 거부된다
fn sum_vec(v: &Vec<i32>) -> i32 { v.iter().sum() }

fn main() {
    let arr: [i32; 3] = [1, 2, 3];
    println!("{}", sum_vec(&arr));
    println!("{}", sum_vec(&arr[..]));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:6:28
  |
6 |     println!("{}", sum_vec(&arr));
  |                    ------- ^^^^ expected `&Vec<i32>`, found `&[i32; 3]`
  |                    |
  |                    arguments to this function are incorrect
  |
  = note: expected reference `&Vec<i32>`
             found reference `&[i32; 3]`
note: function defined here
 --> ex.rs:2:4
  |
2 | fn sum_vec(v: &Vec<i32>) -> i32 { v.iter().sum() }
  |    ^^^^^^^ ------------

error[E0308]: mismatched types
 --> ex.rs:7:28
  |
7 |     println!("{}", sum_vec(&arr[..]));
  |                    ------- ^^^^^^^^ expected `&Vec<i32>`, found `&[i32]`
  |                    |
  |                    arguments to this function are incorrect
  |
  = note: expected reference `&Vec<i32>`
             found reference `&[i32]`
note: function defined here
 --> ex.rs:2:4
  |
2 | fn sum_vec(v: &Vec<i32>) -> i32 { v.iter().sum() }
  |    ^^^^^^^ ------------

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- **E0308 이 두 개**다 — 두 호출이 각각 다른 타입을 들고 왔다(`&[i32; 3]` 과 `&[i32]`).
- `= note:` 두 줄이 **expected / found** 를 나란히 찍어 준다. **기대는 `&Vec<i32>`, 실제는 슬라이스**다.

**시그니처를 `&[i32]` 로 바꾸면 여섯 개가 전부 통과한다.**

```text
===== 소스: ex.rs =====
// &[i32] 를 받는 함수는 어디까지 받나 — 네 가지를 전부 던져 본다
fn sum_slice(s: &[i32]) -> i32 { s.iter().sum() }

fn main() {
    let arr: [i32; 3] = [1, 2, 3];
    let v: Vec<i32> = vec![1, 2, 3, 4];

    println!("&arr      -> {}", sum_slice(&arr));      // &[i32; 3]  (unsized coercion)
    println!("&arr[..]  -> {}", sum_slice(&arr[..]));  // 슬라이싱
    println!("&v        -> {}", sum_slice(&v));        // &Vec<i32>  (Deref 강제)
    println!("&v[..]    -> {}", sum_slice(&v[..]));    // 슬라이싱
    println!("&v[1..3]  -> {}", sum_slice(&v[1..3]));  // 일부만
    println!("&[]       -> {}", sum_slice(&[]));       // 빈 슬라이스
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
&arr      -> 6
&arr[..]  -> 6
&v        -> 10
&v[..]    -> 10
&v[1..3]  -> 5
&[]       -> 0
(종료 코드 0)
```

| 넘기는 것 | `fn f(v: &Vec<i32>)` | `fn f(s: &[i32])` |
|---|---|---|
| `&v`(`&Vec<i32>`) | ✓ | ✓ (`Deref` 강제) |
| `&v[..]` | ✗ E0308 | ✓ |
| `&v[1..3]` | ✗ E0308 | ✓ |
| `&arr`(`&[i32; 3]`) | ✗ E0308 | ✓ (unsized 강제) |
| `&arr[..]` | ✗ E0308 | ✓ |
| `&[]` | ✗ | ✓ |

- ★ **반대 방향은 비어 있다** — `&[T]` 에서 `&Vec<T>` 로 가는 **공짜 강제가 없다.**\
  `to_vec()` 이 있지만 그건 강제가 아니라 **복사(할당)** 다.
- ★★ **이 논리는 [14번 주제](../14-string-vs-str/)의 「인자를 `&String` 이 아니라 `&str` 로 받아라」와 같은 논리다.**\
  `String`:`&str` 자리에 `Vec<T>`:`&[T]` 를 넣으면 문장이 그대로 성립한다 —\
  **소유 타입의 참조 말고 그 뷰 타입을 받아라.** 얻는 것은 없고 **받을 수 있는 것만 줄어든다.**

### 7. 범위는 여섯 타입이고 `..` 만 타입 파라미터가 없다

**출력**

```text
===== 소스: ex.rs =====
// 범위 문법 다섯 꼴이 각각 무슨 타입인가 — 컴파일러에게 이름을 직접 묻는다
use std::any::type_name_of_val;

fn main() {
    println!("2..5   : {}", type_name_of_val(&(2..5)));
    println!("2..=5  : {}", type_name_of_val(&(2..=5)));
    println!("..5    : {}", type_name_of_val(&(..5)));
    println!("2..    : {}", type_name_of_val(&(2..)));
    println!("..     : {}", type_name_of_val(&(..)));
    println!("..=5   : {}", type_name_of_val(&(..=5)));

    // 범위는 그냥 값이다 — 변수에 담아 슬라이싱에 쓸 수 있다
    let v = vec![0, 1, 2, 3, 4, 5, 6, 7];
    let r = 2..5;
    println!("v[r]      = {:?}", &v[r]);
    println!("v[2..=5]  = {:?}", &v[2..=5]);
    println!("v[..3]    = {:?}", &v[..3]);
    println!("v[5..]    = {:?}", &v[5..]);
    println!("v[..]     = {:?}", &v[..]);
    println!("v[..=2]   = {:?}", &v[..=2]);

    // Range 는 이터레이터이기도 하다 — 하지만 RangeFrom 은 끝이 없다
    println!("(2..5).sum::<i32>() = {}", (2..5).sum::<i32>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
2..5   : core::ops::range::Range<i32>
2..=5  : core::ops::range::RangeInclusive<i32>
..5    : core::ops::range::RangeTo<i32>
2..    : core::ops::range::RangeFrom<i32>
..     : core::ops::range::RangeFull
..=5   : core::ops::range::RangeToInclusive<i32>
v[r]      = [2, 3, 4]
v[2..=5]  = [2, 3, 4, 5]
v[..3]    = [0, 1, 2]
v[5..]    = [5, 6, 7]
v[..]     = [0, 1, 2, 3, 4, 5, 6, 7]
v[..=2]   = [0, 1, 2]
(2..5).sum::<i32>() = 9
(종료 코드 0)
```

**왜 그런가**

- ★ **`RangeFull` 만 `<T>` 가 없다.** 끝값도 시작값도 없으니 **담을 것이 없다.**
- ★ **범위는 값이다** — `let r = 2..5;` 로 담아 `&v[r]` 로 쓸 수 있다.\
  다만 `Range` 는 **`Copy` 가 아니라** 한 번 쓰면 **이동**한다([**08번 주제**](../08-ownership-and-move/)).\
  같은 범위를 두 번 쓰려면 `r.clone()` 이나 `2..5` 를 다시 적는다.
- **이터레이터인 것** — `Range`(`2..5`) · `RangeInclusive`(`2..=5`) · `RangeFrom`(`2..`, **무한**).\
  **아닌 것** — `RangeTo`·`RangeToInclusive`·`RangeFull`. **시작을 모르면 돌 수가 없다.**
- `(2..5).sum::<i32>()` 가 **9**(= 2+3+4)인 것이 「범위가 이터레이터이기도 하다」의 실측이다.
- ★ `type_name_of_val` 이 찍는 **경로 문자열**(`core::ops::range::Range<i32>`)은 **rustc 구현**이다 —\
  타입 이름은 언어 보장이지만 **경로 표기는 판마다 바뀔 수 있다.**

### 8. 뚱뚱한 포인터 — 길이가 어디 있느냐로 갈린다

**출력**

```text
===== 소스: ex.rs =====
// 슬라이스 참조는 무엇을 담고 있나 — 크기와 내용
use std::mem::size_of;

fn main() {
    println!("size_of::<&i32>()        = {}", size_of::<&i32>());
    println!("size_of::<&[i32; 5]>()   = {}", size_of::<&[i32; 5]>());
    println!("size_of::<&[i32]>()      = {}", size_of::<&[i32]>());
    println!("size_of::<&mut [i32]>()  = {}", size_of::<&mut [i32]>());
    println!("size_of::<&str>()        = {}", size_of::<&str>());
    println!("size_of::<&Vec<i32>>()   = {}", size_of::<&Vec<i32>>());
    println!("size_of::<Vec<i32>>()    = {}", size_of::<Vec<i32>>());
    println!("size_of::<[i32; 5]>()    = {}", size_of::<[i32; 5]>());

    let arr: [i32; 5] = [10, 20, 30, 40, 50];
    let v: Vec<i32> = vec![10, 20, 30, 40, 50];

    let a: &[i32] = &arr[1..4];      // 배열에서
    let b: &[i32] = &v[1..4];        // Vec 에서
    println!("arr[1..4] = {:?} · len {}", a, a.len());
    println!("v[1..4]   = {:?} · len {}", b, b.len());

    // 포인터와 길이를 직접 꺼내 본다
    println!("a.as_ptr() == &arr[1] : {}", std::ptr::eq(a.as_ptr(), &arr[1]));
    println!("a.len()               : {}", a.len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
size_of::<&i32>()        = 8
size_of::<&[i32; 5]>()   = 8
size_of::<&[i32]>()      = 16
size_of::<&mut [i32]>()  = 16
size_of::<&str>()        = 16
size_of::<&Vec<i32>>()   = 8
size_of::<Vec<i32>>()    = 24
size_of::<[i32; 5]>()    = 20
arr[1..4] = [20, 30, 40] · len 3
v[1..4]   = [20, 30, 40] · len 3
a.as_ptr() == &arr[1] : true
a.len()               : 3
(종료 코드 0)
```

**왜 그런가**

| 타입 | 크기 | 길이가 어디 있나 |
|---|---|---|
| `&i32` | 8 | 길이 개념이 없다 |
| `&[i32; 5]` | 8 | ★ **타입 안**(`; 5`) — 참조가 들 필요가 없다 |
| `&Vec<i32>` | 8 | ★ **가리키는 값 안**(`Vec` 의 `len` 필드) |
| `&[i32]` · `&mut [i32]` · `&str` | **16** | ★ **참조 자신이 든다** — 포인터 8 + 길이 8 |
| `Vec<i32>` | 24 | 자기 자신(ptr·cap·len 세 워드) |
| `[i32; 5]` | 20 | 값 그 자체(`4 × 5`) |

- ★★ **`&[T]` 가 두 워드인 이유** — 「어느 `Vec`/배열에서 왔는지」를 잊고 **주소와 개수만** 들기 때문이다.\
  그래서 배열에서 왔든 `Vec` 에서 왔든 **같은 타입**이 되고, 6번의 표가 성립한다.
- **`a.as_ptr()` 이 `&arr[1]` 과 같다** — **새 버퍼가 아니다.** 슬라이스는 원본을 가리킨다.
- ★ **`8`·`16`·`24` 는 플랫폼(포인터 폭)에 달렸다.** 이 값들은 `x86_64` 기준이고 32비트에서는 절반이다.\
  **`20`(= `4 × 5`)만 플랫폼과 무관**하다 — `i32` 는 어디서나 4바이트다([**03번 주제**](../03-primitive-types-and-integer-overflow/)).

### 9. 한 방향만 공짜다 — `error_len()` 이 두 실패를 가른다

**출력**

```text
===== 소스: ex.rs =====
// &str 과 &[u8] 의 왕복 — 그리고 깨진 바이트를 넣으면 무엇이 나오나
fn main() {
    let s = "한글 abc";
    let bytes: &[u8] = s.as_bytes();
    println!("as_bytes() len = {}", bytes.len());

    // 왕복 — 온전한 바이트열
    match std::str::from_utf8(bytes) {
        Ok(back) => println!("from_utf8(온전) = Ok({:?}) · 원본과 같나 {}", back, back == s),
        Err(e)   => println!("from_utf8(온전) = Err({})", e),
    }

    // 한 글자 가운데서 자른 바이트열 — 0..2 는 '한'(0..3)의 앞 두 바이트다
    let cut: &[u8] = &bytes[0..2];
    match std::str::from_utf8(cut) {
        Ok(back) => println!("from_utf8(잘림) = Ok({:?})", back),
        Err(e) => {
            println!("from_utf8(잘림) = Err");
            println!("  Display        : {}", e);
            println!("  Debug          : {:?}", e);
            println!("  valid_up_to()  : {}", e.valid_up_to());
            println!("  error_len()    : {:?}", e.error_len());
        }
    }

    // UTF-8 에 아예 없는 바이트
    let bad: [u8; 3] = [0x61, 0xFF, 0x62];
    match std::str::from_utf8(&bad) {
        Ok(back) => println!("from_utf8(0xFF) = Ok({:?})", back),
        Err(e) => {
            println!("from_utf8(0xFF) = Err");
            println!("  Display        : {}", e);
            println!("  valid_up_to()  : {}", e.valid_up_to());
            println!("  error_len()    : {:?}", e.error_len());
        }
    }

    // 손상을 허용하고 읽는 길
    println!("from_utf8_lossy(0xFF) = {:?}", String::from_utf8_lossy(&bad));
}
===== rustc --edition 2021 ex.rs -o ex =====
warning: calls to `std::str::from_utf8` with an invalid literal always return an error
  --> ex.rs:28:11
   |
27 |     let bad: [u8; 3] = [0x61, 0xFF, 0x62];
   |                        ------------------ the literal was valid UTF-8 up to the 1 bytes
28 |     match std::str::from_utf8(&bad) {
   |           ^^^^^^^^^^^^^^^^^^^^^^^^^
   |
   = note: `#[warn(invalid_from_utf8)]` on by default

warning: 1 warning emitted

===== ./ex =====
as_bytes() len = 10
from_utf8(온전) = Ok("한글 abc") · 원본과 같나 true
from_utf8(잘림) = Err
  Display        : incomplete utf-8 byte sequence from index 0
  Debug          : Utf8Error { valid_up_to: 0, error_len: None }
  valid_up_to()  : 0
  error_len()    : None
from_utf8(0xFF) = Err
  Display        : invalid utf-8 sequence of 1 bytes from index 1
  valid_up_to()  : 1
  error_len()    : Some(1)
from_utf8_lossy(0xFF) = "a�b"
(종료 코드 0)
```

**왜 그런가**

- **`as_bytes()` 는 실패할 수 없다** — `&str` 은 이미 UTF-8 이므로 **불변식을 버리기만** 한다. 비용도 없다.
- **`from_utf8()` 은 검사한다** — `&[u8]` 에는 아무 보장이 없으니 **불변식을 새로 세워야** 하고, 그래서 `Result` 다.
- ★★ **`error_len()` 이 두 실패를 가른다.**

| 값 | 뜻 | 처방 |
|---|---|---|
| **`None`** | **바이트가 모자란다**(잘린 글자) | 버퍼에 남기고 **더 받는다** — 스트리밍의 신호 |
| **`Some(n)`** | **n 바이트가 아예 틀렸다** | 더 받아도 안 된다. **건너뛴다** |

- **`valid_up_to()`** 는 「여기까지는 옳았다」는 바이트 위치다. `&bytes[..e.valid_up_to()]` 는 **안전하게 자를 수 있다.**
- ★ **경고도 출력이다** — **`invalid_from_utf8`**(기본 `warn`)이 **리터럴 바이트열**이면 컴파일 타임에 잡아 준다.\
  4번의 `unconditional_panic` 과 짝이다 — **상수로 적으면 컴파일러가 미리 본다.**\
  (다만 이쪽은 **경고**, 저쪽은 **에러**다.)
- `from_utf8_lossy` 는 실패 대신 U+FFFD 를 꽂는다 — 출력의 `a?b` 가운데 자리가 그것이다.

### 10. `len` 자리는 경계이고, 역순은 두 문구가 다르며, `s[0]` 은 타입 오류다

**출력**

```text
===== 소스: ex.rs =====
// 경계값 — 빈 범위·끝 범위·len 자리
fn main() {
    let s = "한글 abc";          // len 10
    let v = vec![0, 1, 2, 3, 4];  // len 5

    println!("s[3..3]   = {:?}", &s[3..3]);    // 빈 문자열
    println!("s[10..10] = {:?}", &s[10..10]);  // len 자리도 경계다
    println!("s[..]     = {:?}", &s[..]);
    println!("s[6..]    = {:?}", &s[6..]);

    println!("v[2..2]   = {:?}", &v[2..2]);
    println!("v[5..5]   = {:?}", &v[5..5]);    // len 자리
    println!("v[5..]    = {:?}", &v[5..]);
    println!("v[..0]    = {:?}", &v[..0]);
    println!("s.get(11..11) = {:?}", s.get(11..11));  // len 을 넘으면
    println!("v.get(6..6)   = {:?}", v.get(6..6));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s[3..3]   = ""
s[10..10] = ""
s[..]     = "한글 abc"
s[6..]    = " abc"
v[2..2]   = []
v[5..5]   = []
v[5..]    = []
v[..0]    = []
s.get(11..11) = None
v.get(6..6)   = None
(종료 코드 0)
```

**왜 그런가**

- ★ **`len` 자리는 유효한 경계**다 — `&s[10..10]` 은 `""`, `&v[5..5]` 는 `[]` 다. **`len + 1` 부터가 밖**이다.\
  격자로 보면 당연하다 — 경계는 **칸이 아니라 칸과 칸 사이(테두리)** 이고, 테두리는 `len + 1` 개다.
- **빈 범위는 언제나 빈 슬라이스**다. 패닉이 아니다.

**역순 범위는 `&str` 과 값 슬라이스가 서로 다른 말을 한다.**

```text
===== 소스: ex.rs =====
// 범위를 거꾸로 주면 — 문자열과 값 슬라이스가 서로 다른 말을 한다
// ★ 표시줄을 eprintln! 로 내 패닉 메시지와 같은 stream 에 둔다
use std::panic::catch_unwind;

fn main() {
    let s = "한글 abc";
    let v = vec![10, 20, 30, 40, 50];

    eprintln!("--- &str 에서 7..3 ---");
    let _ = catch_unwind(|| &s[7..3]);
    eprintln!("--- Vec 슬라이스에서 4..2 ---");
    let _ = catch_unwind(|| &v[4..2]);
    eprintln!("--- 둘 다 패닉 ---");
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
--- &str 에서 7..3 ---

thread 'main' (3405980) panicked at ex.rs:10:31:
begin <= end (7 <= 3) when slicing `한글 abc`
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
--- Vec 슬라이스에서 4..2 ---

thread 'main' (3405980) panicked at ex.rs:12:31:
slice index starts at 4 but ends at 2
--- 둘 다 패닉 ---
(종료 코드 0)
```

★ **대조할 것은 숫자가 아니라 「두 타입이 서로 다른 문구를 낸다」는 성질이다.**

- ★ **`&str` 쪽은 「성립했어야 하는 주장」을 적어 준다** — `begin <= end (7 <= 3)`.\
  **괄호 안이 실제 값이고, 그 값으로는 왼쪽 부등식이 거짓**이라는 뜻이다. 읽는 방향이 반대다.
- `windows(8)`(길이 7)은 **빈 이터레이터**이고 `windows(0)` 은 **패닉**이다 — 5번에서 봤듯 **규칙이 다르다.**

**`s[0]` 은 실행까지 가지도 않는다.**

```text
===== 소스: ex.rs =====
// 문자열에 정수 인덱스를 쓰면 — 아예 컴파일이 안 된다
fn main() {
    let s = "한글 abc";
    let c = s[0];
    println!("{}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the type `str` cannot be indexed by `{integer}`
 --> ex.rs:4:15
  |
4 |     let c = s[0];
  |               ^ string indices are ranges of `usize`
  |
  = help: the trait `SliceIndex<str>` is not implemented for `{integer}`
  = note: you can use `.chars().nth()` or `.bytes().nth()`
          for more information, see chapter 8 in The Book: <https://doc.rust-lang.org/book/ch08-02-strings.html#indexing-into-strings>
  = help: the following other types implement trait `SliceIndex<T>`:
            `usize` implements `SliceIndex<ByteStr>`
            `usize` implements `SliceIndex<[T]>`
  = note: required for `str` to implement `Index<{integer}>`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

- **에러 번호는 E0277**(트레이트 미구현)이다 — **타입 오류**이지 범위 오류가 아니다.
- ★★ **`string indices are ranges of usize`** 한 줄이 이 주제의 제목이다.
- ★ **진단이 처방을 둘 준다** — **`.chars().nth()`** 와 **`.bytes().nth()`**.\
  「몇 번째 문자」냐 「몇 번째 바이트」냐를 **네가 골라야 한다**는 뜻이고, 이것이 11번 표의 출발점이다.

### 11. 원본이 바뀐다 — 슬라이스는 복사본이 아니라 빌림이다

**출력**

```text
===== 소스: ex.rs =====
// &mut [T] 로 원소를 바꾸면 원본이 바뀐다 — 슬라이스는 복사본이 아니다
fn double_all(s: &mut [i32]) {
    for x in s.iter_mut() { *x *= 2; }
}

fn main() {
    let mut v: Vec<i32> = vec![1, 2, 3, 4, 5];
    println!("전   {:?}", v);

    double_all(&mut v[1..4]);      // 가운데 세 개만 빌려 준다
    println!("후   {:?}", v);      // 원본이 바뀌어 있다

    // split_at_mut — 한 Vec 을 겹치지 않는 두 가변 슬라이스로 가른다
    let (a, b) = v.split_at_mut(2);
    a[0] = 100;
    b[0] = 200;
    println!("가른 뒤 {:?}", v);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
전   [1, 2, 3, 4, 5]
후   [1, 4, 6, 8, 5]
가른 뒤 [100, 4, 200, 8, 5]
(종료 코드 0)
```

**왜 그런가**

- **`&mut v[1..4]` 로 가운데만 넘겼더니 1·2·3번 칸만 두 배**가 됐다(`2→4`, `3→6`, `4→8`).\
  0번과 4번은 그대로다 — **슬라이스가 가리킨 칸만** 바뀐다.
- **복사본이 아니다.** 8번의 `a.as_ptr() == &arr[1]` 이 같은 사실의 다른 면이다.

**그래서 빌림 규칙이 그대로 적용된다.**

```text
===== 소스: ex.rs =====
// 슬라이스도 빌림이다 — &mut 슬라이스가 살아 있는 동안 원본을 못 읽는다
fn main() {
    let mut v: Vec<i32> = vec![1, 2, 3, 4, 5];
    let part = &mut v[1..4];
    println!("원본 {:?}", v);   // 가변 빌림이 아직 살아 있다
    part[0] = 99;
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0502]: cannot borrow `v` as immutable because it is also borrowed as mutable
 --> ex.rs:5:25
  |
4 |     let part = &mut v[1..4];
  |                     - mutable borrow occurs here
5 |     println!("원본 {:?}", v);   // 가변 빌림이 아직 살아 있다
  |                           ^ immutable borrow occurs here
6 |     part[0] = 99;
  |     ------- mutable borrow later used here
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0502`.
```

- **에러 번호는 E0502** 다 — [**10번 주제**](../10-borrowing-and-aliasing-rules/)의 「가변 하나 + 공유 하나」 충돌 그대로다.
- ★ **`mutable borrow later used here`** 가 NLL 의 표시다. `part[0] = 99;` 줄을 지우면\
  빌림이 `println!` 앞에서 끝나 **통과한다.**
- ★ **`split_at_mut` 이 규칙을 어기지 않는 이유** — **겹치지 않는 두 구간**이라 **별칭이 아니다.**\
  「가변 빌림은 하나뿐」은 **같은 자리**에 대한 규칙이다. 구현은 「겹치지 않음」을 확인하고\
  `unsafe` 로 나누는데, **안전한 추상으로 감싼 `unsafe`** 의 교과서 사례다(목록의 **56번 주제**).
- ★ **`&mut [T]` 로 못 하는 것 — 길이 바꾸기.** `push`·`remove`·`truncate` 는 `Vec` 의 것이다.\
  슬라이스는 **칸의 내용만** 바꾼다. 「길이를 바꾸는 것」과 「내용을 바꾸는 것」을 **타입으로 가른** 설계다.

### 12. 단계 지도 — 어디서 잡히나

**출력**

| 단계 | 무엇 | 이 주제의 실측 |
|---|---|---|
| **컴파일 에러** | **E0277** `str cannot be indexed by {integer}` | 10번 — `s[0]` |
| | **E0308** `mismatched types` | 6번 — `&Vec<i32>` 인자에 슬라이스 |
| | **E0502** 가변+공유 빌림 충돌 | 11번 — `&mut v[..]` 살아 있는데 `v` 읽기 |
| **컴파일 린트** | `unconditional_panic`(기본 **`deny`** = 에러) | 4번 — **배열의 상수 인덱스만** |
| | `invalid_from_utf8`(기본 **`warn`**) | 9번 — 리터럴 바이트열 |
| **런타임 패닉** | `byte index N is not a char boundary` | 2번 — ★ **상수여도 안 잡힌다** |
| | `index out of bounds: the len is …` | 4번 — `Vec`·슬라이스 |
| | `begin <= end (…)` / `slice index starts at …` | 10번 — 역순 범위(문구가 다르다) |
| | `chunk size must be non-zero` 등 | 5번 — 크기 0 |

**왜 그런가**

- ★★ **이 주제의 값은 「컴파일이 통과했다」가 안전을 뜻하지 않는다**는 데 있다.\
  Rust 의 보장은 **메모리 안전**이지 **패닉 안 함**이 아니다.
- **UTF-8 인코딩 자체**(코드 포인트·코드 유닛·무엇이 몇 바이트로 적히나)의 정본은\
  [`../../../../data-representation/`](../../../../data-representation/) 이다.\
  ★ **그쪽은 인코딩 자체, 여기는 그 인코딩 때문에 인덱싱이 패닉하는 자리**다.\
  바이트 격자의 `ED 95 9C` 가 **왜 그 값인지**는 거기서 읽는다.
- **`&Vec<T>` 대신 `&[T]` 를 받는 논리의 문자열판**은 [**14번 주제**](../14-string-vs-str/)다 — **같은 논리**다.
- **슬라이스를 반환할 때 `'a` 가 필요해지는 이야기**는 [**12번 주제**](../12-lifetime-annotations-and-elision/)다.
- **`&v` 가 `&[T]` 자리에 들어가는 강제**는 **`Deref` 강제**이고 정본은 목록의 **43번 주제**다.\
  `&arr`(`&[T; N]` → `&[T]`)는 그것과 다른 **unsized 강제**다 — **이름이 다르다.**
- ★★ **사람이 세는 글자 수는 std 로 못 센다.** std 가 주는 단위는 **바이트**와 **`char`** 둘뿐이다.\
  그 사실을 **요구사항 쪽에 적어야** 한다 — 「앞 10글자」라는 요구는 대개 「너무 길면 줄이기」이고,\
  그건 `char_indices()` 로 충분하다. 이 문서는 기준 소스를 std 로 고정했으므로 **외부 크레이트를 쓰지 않았다.**

---

## 실행 검증

| 실험 (`ex.rs`) | 무엇을 확인했나 | 결과 |
|---|---|---|
| 7종 문자열의 `len`·`chars`·`bytes` | ★ **세 칸이 전부 갈린다** | 1 |
| 기준 문자열 `char_indices` + `is_char_boundary` 전수 | 바이트 격자의 근거(경계 `0·3·6·7·8·9·10`) | 2-summary (3) |
| 가족 이모지 바이트 격자 | **18바이트 · 5 `char` · 사람 1글자** | 2-summary (3) |
| `chars().take(1)` · `chars().rev()` | 국기가 뒤집히고 악센트가 떨어진다 | 2-summary (3) |
| ★ `&s[0..1]` | **패닉** `byte index 1 is not a char boundary` · **종료 코드 101** | 2 |
| `s.get(...)` 네 가지 · `sl.get(...)` 세 가지 | **전부 `None` / 정상만 `Some`** | 3 |
| ★ `arr[i]`(상수 7, `[i32; 5]`) | **컴파일 에러** `unconditional_panic`(기본 `deny`) | 4 |
| `&"한글"[0..1]` + `&[10,20,30][5]` 한 파일 | **배열만 잡히고 문자열은 통과** | 4 |
| `&"한글"[0..1]` 단독 | **컴파일 통과 → 런타임 패닉**(종료 코드 101) | 4 · 2-summary (6) |
| 배열·`Vec`·슬라이스 OOB(`catch_unwind`) | **메시지가 셋 다 같다** · `note:` 는 첫 판만 | 4 |
| `split_at`·`chunks`·`chunks_exact`·`rchunks`·`windows` | `chunks` 꼬리 `[6]` · `rchunks` 앞머리 `[0]` · `windows(8)` 빈 것 | 5 |
| `chunks(0)`·`windows(0)`·`split_at(8)` | **셋 다 패닉이고 문구가 전부 다르다** | 5 |
| ★ `sum_vec(&arr)` · `sum_vec(&arr[..])` | **E0308 두 개** | 6 |
| `sum_slice` 에 여섯 가지 | **여섯 개 전부 통과** | 6 |
| 범위 여섯 꼴 `type_name_of_val` | `Range`·`RangeInclusive`·`RangeTo`·`RangeFrom`·`RangeFull`·`RangeToInclusive` | 7 |
| `(2..5).sum::<i32>()` | **9** — 범위가 이터레이터이기도 하다 | 7 |
| `size_of` 여덟 가지 | `&[i32]`·`&str` **16** · `&Vec<i32>` **8** · `Vec<i32>` **24** | 8 |
| `a.as_ptr() == &arr[1]` | **`true`** — 슬라이스는 복사본이 아니다 | 8 |
| `from_utf8` 왕복 · 잘린 바이트 · `0xFF` | `error_len()` **`None`** 대 **`Some(1)`** | 9 |
| ★ 리터럴 바이트열 `from_utf8` | **컴파일 경고** `invalid_from_utf8`(기본 `warn`) | 9 |
| `s[3..3]`·`s[10..10]`·`v[5..5]`·`v[..0]` | **`len` 자리도 경계** — 빈 슬라이스 | 10 |
| `&s[7..3]` · `&v[4..2]` | **문구가 다르다**(`begin <= end` 대 `slice index starts at`) | 10 |
| `s[0]`(`s: &str`) | **E0277** + `= note:` 가 처방 둘을 준다 | 10 |
| `double_all(&mut v[1..4])` · `split_at_mut(2)` | **원본이 바뀐다** `[1,4,6,8,5]` → `[100,4,200,8,5]` | 11 |
| `&mut v[..]` 살아 있는데 `v` 읽기 | **E0502** + `mutable borrow later used here` | 11 |
| 세 이터레이터 전수 · `find` · `floor_char_boundary` | `char_indices` 만 **자를 위치**를 준다 · 셋 다 `3` | 2-summary (11) |

**구현·설정에 달린 항목**(다시 찍을 자리)

| 항목 | 무엇에 달렸나 |
|---|---|
| ★ 패닉 첫 줄의 **괄호 안 숫자** | **런타임**(OS 스레드 id) — 같은 바이너리 3회에 전부 달랐다 |
| **`the len is` 대 `the length is`** | **rustc·std 구현** — 런타임 경로와 컴파일 경로가 다른 코드다 |
| `unconditional_panic` 이 **기본 `deny`** | **rustc 판** — 린트는 판마다 추가·승격된다 |
| `invalid_from_utf8` 이 **기본 `warn`** | 〃 |
| **상수 배열 인덱스만 잡히는 것** | **rustc 구현**(상수 전파). 문자열 경계는 안 잡혔다 |
| `str::floor_char_boundary` 가 **안정판인 것** | **rustc·std 판** — 이 툴체인(1.92.0)에서 컴파일됨 |
| `type_name_of_val` 의 **경로 문자열** | **rustc 구현** — 타입 이름은 보장, 경로 표기는 아니다 |
| **포인터 8 · `&[T]` 16 · `Vec` 24** | ★ **플랫폼**(포인터 폭). `x86_64` 기준 |
| **종료 코드 101** | **std 구현** — `panic = "abort"` 로 빌드하면 달라진다 |
| `catch_unwind` 로 패닉을 이어 볼 수 있는 것 | **`panic = "unwind"`**(기본). `abort` 면 첫 패닉에서 끝난다 |
| **표시줄을 `eprintln!` 로 낸 것** | ★ **재현 조건**이다 — `println!` 이면 stdout·stderr 가 갈려 순서가 환경에 달린다 |
| **슬라이스·범위 문법·경계 패닉·`get` 의 `None`** | **전부 언어 보장.** 실측과 Reference·std 문서가 일치했다 |
