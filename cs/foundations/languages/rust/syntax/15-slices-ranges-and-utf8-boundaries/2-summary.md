# rust/syntax/15 — 슬라이스 `&[T]`·범위 문법·UTF-8 경계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Array and slice types](https://doc.rust-lang.org/reference/types/slice.html) ·
> [Reference — Range expressions](https://doc.rust-lang.org/reference/expressions/range-expr.html) ·
> [std — `primitive.slice`](https://doc.rust-lang.org/std/primitive.slice.html) ·
> [std — `primitive.str`](https://doc.rust-lang.org/std/primitive.str.html) ·
> [std — `std::str::from_utf8`](https://doc.rust-lang.org/std/str/fn.from_utf8.html) ·
> `rustc --explain E0308` / `E0277` / `E0502`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고·패닉은 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단·패닉의 줄 번호는 그 파일 기준**이다.
> ★★ **패닉 블록에는 다시 돌리면 바뀌는 칸이 하나 있다.**\
> 흔들리는 칸 — `thread 'main' (3085086)` 의 **괄호 안 숫자**(OS 스레드 id). 같은 바이너리를 3회 돌려 셋 다 달랐다.\
> 안 흔들리는 칸 — `ex.rs:줄:칸` · 메시지 본문 · `note:` 줄 · **종료 코드 101**. **대조할 것은 이쪽이다.**
> **버전** — 슬라이스·범위·`char_indices` 는 1.0.0부터다. `std::any::type_name_of_val`(아래 (2)에서 씀)과\
> `str::floor_char_boundary`(아래 (3))는 **이 툴체인의 안정판에서 컴파일되는 것을 실측**했다(아래 「구현 세부사항 대 언어 보장」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**슬라이스는 「잘라낸 조각」이 아니라 「창문」이다** — 원본을 복사하지 않고 **어디부터 몇 개인지**만 들고 있다.

그리고 **`&str` 의 창틀은 「글자」가 아니라 「바이트」 위에 놓인다.** 이 한 줄이 이 주제의 전부다.

| 비유 | 실체 |
|---|---|
| 벽에 낸 **창문** — 벽을 뜯어 온 게 아니다 | **슬라이스** `&[T]`·`&str` — 원본을 빌린 **뷰** |
| 창틀에 적힌 **「왼쪽 끝 · 가로 칸 수」** | **뚱뚱한 포인터** — 포인터 + 길이. `size_of` 가 **16** 바이트다 |
| 창을 낼 위치를 적은 **쪽지** | **범위**(`2..5`) — 그 자체가 값이고 타입이 있다 |
| 창문으로 손을 넣어 물건을 **바꾸면 방 안이 바뀐다** | `&mut [T]` — 원본이 바뀐다 |
| 벽돌은 **한 칸씩** 세는데 그림은 **여러 벽돌에 걸쳐** 그려져 있다 | **바이트 인덱스** 대 **문자** — `한` 하나가 바이트 3칸 |
| 벽돌 **가운데**를 창틀로 삼으면 창이 안 서고 **무너진다** | ★★ **UTF-8 경계 위반 패닉** — 컴파일이 아니라 **실행**에서 |
| 「무너뜨리지 말고 **안 되면 안 된다고 말해 줘**」 | `get(..)` — 패닉 대신 `None` |

- ★★ **`&[T]` 는 포인터 하나가 아니라 「포인터 + 길이」 두 워드다.** 그래서 `&Vec<i32>`(8바이트)와 **크기부터 다르다**.
- ★★ **문자열 인덱싱은 바이트 단위이고, 경계를 안 맞추면 컴파일은 통과하고 실행에서 죽는다.**\
  같은 파일 안에서 **배열의 상수 인덱스는 컴파일 에러인데 문자열의 상수 경계 위반은 통과한다**(아래 (6)에서 실측).
- ★ **`len()`·`chars().count()`·사람이 세는 글자 수는 셋 다 다른 수**다. 셋이 같아지는 것은 ASCII 뿐이다.

```text
   슬라이스 하나가 메모리에서 무엇인가

   let v: Vec<i32> = vec![10, 20, 30, 40, 50];
   let s: &[i32]   = &v[1..4];

        v (24 바이트: ptr·cap·len)          힙 버퍼
        +--------+--------+--------+        +----+----+----+----+----+
        |  ptr  ---------------------->     | 10 | 20 | 30 | 40 | 50 |
        |  cap 5 |  len 5 |        |        +----+----+----+----+----+
        +--------+--------+--------+           0    1    2    3    4
                                                    ^         ^
        s (16 바이트: ptr·len)                       |         |
        +--------+--------+                         +---------+
        |  ptr  ------------------------------------+   len 3
        |  len 3 |        |
        +--------+--------+

   s 는 새 버퍼를 안 만든다. 같은 버퍼의 1번 칸을 가리키고 「3개」라고 적어 둘 뿐이다.
```

> **슬라이스(slice)** — 연속한 원소 열의 **일부를 빌린 뷰**. 타입은 `[T]`(크기 미정)이고\
> 실제로 쓰는 것은 그 참조인 `&[T]`·`&mut [T]` 다. 문자열판이 `&str` 이다.

> **뚱뚱한 포인터(fat pointer)** — 주소 + 메타데이터(여기서는 **길이**)를 함께 든 참조.\
> `size_of::<&[i32]>()` 가 **16**, `size_of::<&Vec<i32>>()` 가 **8** 인 이유다.

> **바이트 인덱스(byte index)** — `&str` 의 인덱싱 단위. `s[2..5]` 의 2·5는 **바이트 번호**이지\
> 몇 번째 글자가 아니다. `find()`·`char_indices()` 가 돌려주는 수도 전부 바이트 번호다.

> **문자 경계(char boundary)** — 한 `char` 의 UTF-8 인코딩이 **시작하는 바이트 위치**.\
> `s.is_char_boundary(i)` 로 물어볼 수 있고, 여기를 안 맞춘 슬라이싱이 **런타임 패닉**이다.

> **`char`** — 유니코드 **스칼라 값** 하나(4바이트 고정). ★ **사람이 세는 「글자」가 아니다** —\
> 가족 이모지 하나가 `char` 다섯 개다(아래 (3)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **슬라이스는 무엇을 들고 있나** — `&[T]` 가 `&Vec<T>`·`&[T; N]` 과 무엇이 다르고, 함수 인자로 어느 쪽을 받아야 하나.
2. **범위 문법이 무슨 타입이고 어디서 죽나** — `a..b`·`a..=b`·`..b`·`a..`·`..` 가 각각 무엇이며, 밖으로 나가거나 거꾸로면 무엇이 나오나.
3. ★★ **문자열을 자를 때 왜 패닉하나** — `len()`·`chars().count()`·사람이 세는 글자 수가 어긋나는 자리가 정확히 어디인가.

★ [**14번 주제**](../14-string-vs-str/)가 「**`String` 이냐 `&str` 이냐**」였다면 여기는 「**그 `&str` 을 어디서 자를 수 있나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **컴파일 에러** | 타입이 아예 안 맞는 자리 — E0308·E0277·E0502 | 10·12번에서 이어받음 |
| ★ **실행 패닉 전문** | **컴파일을 통과한 뒤에야** 드러나는 자리 | ★ 이 갈래에서 패닉이 주인공인 첫 주제 |
| ★ **`get(..)` 의 `Option`** | 같은 질문을 **죽지 않고** 묻는 길 | [목록의 **21번 주제**](../21-option-and-combinators/)로 이어짐 |
| ★★ **바이트 격자** | **바이트 번호 · 16진값 · 문자 경계 · `chars()` 단위**를 한 그림에 겹친 것 | ★★ **이 주제의 네 번째 창** |

★★ **네 번째 창이 이 주제의 본체다.** 앞의 세 창은 「무엇이 일어났나」를 말해 주지만
**왜 하필 바이트 1에서 죽고 바이트 3에서는 안 죽는지**는 격자를 그려야 보인다.
`len()` 과 `chars().count()` 가 다르다는 사실만 외우면 **어느 인덱스가 안전한지는 여전히 못 고른다.**

비용 — 없음. 전부 컴파일·실행만 하면 된다.

### (1) 슬라이스는 무엇을 들고 있나 — 크기로 확인한다

**언제 쓰나** — 함수 인자를 `&Vec<T>` 로 받을지 `&[T]` 로 받을지 고를 때.

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

읽는 법.

- **`&[i32]` 와 `&mut [i32]` 와 `&str` 이 전부 16바이트**다 — 포인터(8) + 길이(8). **뚱뚱한 포인터**다.
- **`&[i32; 5]` 와 `&Vec<i32>` 는 8바이트**다 — 길이가 **타입 안**(`; 5`)이나 **가리키는 값 안**(`Vec` 의 `len` 필드)에 있어\
  참조가 따로 들고 다닐 필요가 없다.
- **`a.as_ptr()` 이 `&arr[1]` 과 같은 주소**다 — 슬라이스는 **복사본이 아니다.**
- **배열에서 얻든 `Vec` 에서 얻든 같은 `&[i32]`** 가 나온다. 이것이 (8)의 논거다.

```text
   슬라이스를 얻는 네 길 — 셋 다 &[T] 로 모인다

   [T; N]  ──&arr──────▶  &[T; N]  ──(unsized 강제)──▶ &[T]
           ──&arr[..]──────────────────────────────▶ &[T]
   Vec<T>  ──&v────────▶  &Vec<T>  ──(Deref 강제)───▶ &[T]
           ──&v[..]────────────────────────────────▶ &[T]
   String  ──&s────────▶  &String  ──(Deref 강제)───▶ &str
           ──&s[..]────────────────────────────────▶ &str

   ★ 화살표가 한 방향뿐이다 — &[T] 에서 &Vec<T> 로 돌아오는 길은 없다((8)).
```

### (2) 범위 문법 — 여섯 꼴과 그 타입

**언제 쓰나** — `[` 안에 `..` 를 적을 때마다. **범위는 문법이 아니라 값이다.**

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

| 꼴 | 타입 | 포함 관계 | 비고 |
|---|---|---|---|
| `a..b` | `Range<T>` | `a` 포함, `b` 제외 | 가장 흔하다. **이터레이터이기도 하다** |
| `a..=b` | `RangeInclusive<T>` | 양끝 포함 | `..=` 는 **한 토큰**이다 |
| `..b` | `RangeTo<T>` | `b` 제외 | 이터레이터가 **아니다**(시작이 없다) |
| `a..` | `RangeFrom<T>` | `a` 포함, 끝 없음 | 이터레이터지만 **무한**이다 |
| `..` | `RangeFull` | 전부 | 타입에 `<T>` 가 없다 |
| `..=b` | `RangeToInclusive<T>` | `b` 포함 | 슬라이싱에만 쓴다 |

- ★ **`..` 하나만 타입 파라미터가 없다** — 담을 수가 없으니 당연하다.
- ★ **범위는 값이라 변수에 담긴다**(`let r = 2..5; &v[r]`). 다만 `Range` 는 `Copy` 가 아니라 **한 번 쓰면 이동**한다.
- **`(2..5).sum()` 이 `9`** 인 것이 「범위가 이터레이터이기도 하다」의 증거다(`2+3+4`).

### (3) ★★ 바이트 격자 — 같은 글자를 네 층으로 겹쳐 본다

**언제 쓰나** — `&str` 에 숫자를 적기 직전마다. **이 절이 이 주제의 본체다.**

먼저 **세 가지 세는 법이 실제로 어긋나는 것**부터 전수로 찍는다.

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

★★ **세 열이 전부 갈린다.** 특히 마지막 네 줄이 이 주제의 핵심이다 —
**`chars().count()` 조차 사람이 세는 글자 수가 아니다.**

- `len()` 과 `bytes().count()` 는 **항상 같다** — 둘 다 UTF-8 바이트 수다(`len()` 이 O(1), 뒤는 O(n)).
- `chars().count()` 는 **유니코드 스칼라 값**의 개수다. **결합 문자·ZWJ·지역 표시자는 각각 따로 세어진다.**
- **사람이 세는 글자**(자소 묶음, grapheme cluster)는 **std 로는 못 센다** — 아래 「어디서 틀리나 3」에서 다시 본다.
- ★ 출력 표의 칸이 안 맞아 보이는 것도 같은 이유다. **`{:>6}` 은 표시 폭이 아니라 `char` 개수로 채운다** —\
  `사람` 은 2 `char` 라 4칸을 더 채우지만 화면에서는 4칸을 먹는다.

이제 **기준 문자열 하나**를 정해 전수로 찍는다. 이 문자열을 이 문서 내내 쓴다.

```text
===== 소스: ex.rs =====
// 이 주제의 기준 문자열 — 바이트 격자를 전수로 찍는다
fn main() {
    let s = "한글 abc";

    println!("s              = {:?}", s);
    println!("s.len()        = {}", s.len());
    println!("chars().count()= {}", s.chars().count());

    print!("as_bytes() 16진 =");
    for b in s.as_bytes() {
        print!(" {:02X}", b);
    }
    println!();

    println!("-- char_indices() 전수 --");
    for (i, c) in s.char_indices() {
        println!("  바이트 {:>2} : {:?}  U+{:04X}  {}바이트", i, c, c as u32, c.len_utf8());
    }

    println!("-- is_char_boundary(i) 전수 (0..=len) --");
    for i in 0..=s.len() {
        println!("  {:>2} : {}", i, s.is_char_boundary(i));
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s              = "한글 abc"
s.len()        = 10
chars().count()= 6
as_bytes() 16진 = ED 95 9C EA B8 80 20 61 62 63
-- char_indices() 전수 --
  바이트  0 : '한'  U+D55C  3바이트
  바이트  3 : '글'  U+AE00  3바이트
  바이트  6 : ' '  U+0020  1바이트
  바이트  7 : 'a'  U+0061  1바이트
  바이트  8 : 'b'  U+0062  1바이트
  바이트  9 : 'c'  U+0063  1바이트
-- is_char_boundary(i) 전수 (0..=len) --
   0 : true
   1 : false
   2 : false
   3 : true
   4 : false
   5 : false
   6 : true
   7 : true
   8 : true
   9 : true
  10 : true
(종료 코드 0)
```

**이 출력을 한 그림으로 겹치면 이렇게 된다.** 이것이 **바이트 격자**다.

```text
   "한글 abc"      len() = 10 · chars().count() = 6 · 사람이 세는 글자 = 6

byte    :   0    1    2    3    4    5    6    7    8    9
          +----+----+----+----+----+----+----+----+----+----+
hex     : | ED | 95 | 9C | EA | B8 | 80 | 20 | 61 | 62 | 63 |
          +----+----+----+----+----+----+----+----+----+----+
bnd     : o    .    .    o    .    .    o    o    o    o    o
char    :  [---- 1 -----] [---- 2 -----] [ 3 ][ 4 ][ 5 ][ 6 ]

   bnd  : o = is_char_boundary(i) 가 true · . = false (그 자리를 자르면 패닉)
   char : 1='한'(U+D55C) 2='글'(U+AE00) 3=' ' 4='a' 5='b' 6='c'
          ★ bnd 의 o 는 칸이 아니라 「칸과 칸 사이(테두리)」에 찍힌다 — 경계는 위치다.
          ★ 맨 끝 10(len 자리)도 경계다. 그래서 &s[10..10] 은 빈 문자열이고 패닉하지 않는다.
```

**ASCII 만 있으면 격자가 1:1 이 된다** — 셋이 같아지는 유일한 경우다.

```text
   "Hi"      len() = 2 · chars().count() = 2 · 사람이 세는 글자 = 2

byte    :   0    1
          +----+----+
hex     : | 48 | 69 |
          +----+----+
bnd     : o    o    o
char    :  [ 1 ][ 2 ]

   char : 1='H' 2='i'   ★ 모든 자리가 경계다 — ASCII 만 있으면 어디를 잘라도 안 죽는다.
```

★★ **여기서부터가 「`chars()` 도 글자가 아니다」의 자리다.** 같은 「한 글자」를 셋 다 그려 본다.

```text
   조합형 "한" (자모 셋)      len() = 9 · chars().count() = 3 · 사람이 세는 글자 = 1

byte    :   0    1    2    3    4    5    6    7    8
          +----+----+----+----+----+----+----+----+----+
hex     : | E1 | 84 | 92 | E1 | 85 | A1 | E1 | 86 | AB |
          +----+----+----+----+----+----+----+----+----+
bnd     : o    .    .    o    .    .    o    .    .    o
char    :  [---- 1 -----] [---- 2 -----] [---- 3 -----]

   char : 1=U+1112(초성 ㅎ) 2=U+1161(중성 ㅏ) 3=U+11AB(종성 ㄴ)
          ★ 화면에는 「한」 하나로 보이는데 char 가 셋이다.
          ★ 완성형 "한"(U+D55C)은 같은 글자인데 len 3 · chars 1 이다 — 인코딩이 다르다.
```

```text
   "e" + 결합 악센트        len() = 3 · chars().count() = 2 · 사람이 세는 글자 = 1

byte    :   0    1    2
          +----+----+----+
hex     : | 65 | CC | 81 |
          +----+----+----+
bnd     : o    o    .    o
char    :  [ 1 ][-- 2 --]

   char : 1='e'(U+0065) 2=U+0301(결합 악센트)
          ★ 바이트 1 은 경계다 — 자를 수는 있다. 자르면 악센트만 남는다.
          ★ 「자를 수 있다」와 「잘라도 되는 자리다」는 다른 말이다.
```

```text
   국기 이모지 하나          len() = 8 · chars().count() = 2 · 사람이 세는 글자 = 1

byte    :   0    1    2    3    4    5    6    7
          +----+----+----+----+----+----+----+----+
hex     : | F0 | 9F | 87 | B0 | F0 | 9F | 87 | B7 |
          +----+----+----+----+----+----+----+----+
bnd     : o    .    .    .    o    .    .    .    o
char    :  [------- 1 -------] [------- 2 -------]

   char : 1=U+1F1F0(지역 표시자 K) 2=U+1F1F7(지역 표시자 R)
          ★ 바이트 4 는 경계다 — 반으로 자르면 국기가 아니라 글자 두 개가 된다.
```

```text
   가족 이모지 하나          len() = 18 · chars().count() = 5 · 사람이 세는 글자 = 1

byte    :   0    1    2    3    4    5    6    7    8    9    10   11   12   13   14   15   16   17
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
hex     : | F0 | 9F | 91 | A8 | E2 | 80 | 8D | F0 | 9F | 91 | A9 | E2 | 80 | 8D | F0 | 9F | 91 | A7 |
          +----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+----+
bnd     : o    .    .    .    o    .    .    o    .    .    .    o    .    .    o    .    .    .    o
char    :  [------- 1 -------] [---- 2 -----] [------- 3 -------] [---- 4 -----] [------- 5 -------]

   char : 1=U+1F468 2=U+200D(ZWJ) 3=U+1F469 4=U+200D(ZWJ) 5=U+1F467
          ★ 경계가 다섯 군데나 있다 — 전부 「잘라도 패닉은 안 하는」 자리다.
             그런데 어디를 잘라도 사람이 보던 그 그림은 안 남는다.
```

이 마지막 격자를 **코드로 다시 확인**한다.

```text
===== 소스: ex.rs =====
// 가족 이모지 하나의 바이트 격자 — 「한 글자」가 18 바이트 5 char 다
fn main() {
    let s = "\u{1F468}\u{200D}\u{1F469}\u{200D}\u{1F467}";
    println!("len {} · chars {} · 사람이 보는 글자 1", s.len(), s.chars().count());

    print!("16진 :");
    for b in s.as_bytes() { print!(" {:02X}", b); }
    println!();

    for (i, c) in s.char_indices() {
        println!("  바이트 {:>2}..{:<2} U+{:04X} {}바이트 {:?}",
                 i, i + c.len_utf8(), c as u32, c.len_utf8(), c);
    }

    print!("경계 :");
    for i in 0..=s.len() { print!(" {}", if s.is_char_boundary(i) { 'o' } else { '.' }); }
    println!();
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
len 18 · chars 5 · 사람이 보는 글자 1
16진 : F0 9F 91 A8 E2 80 8D F0 9F 91 A9 E2 80 8D F0 9F 91 A7
  바이트  0..4  U+1F468 4바이트 '👨'
  바이트  4..7  U+200D 3바이트 '\u{200d}'
  바이트  7..11 U+1F469 4바이트 '👩'
  바이트 11..14 U+200D 3바이트 '\u{200d}'
  바이트 14..18 U+1F467 4바이트 '👧'
경계 : o . . . o . . o . . . o . . o . . . o
(종료 코드 0)
```

★ **`{:?}` 가 ZWJ 를 `'\u{200d}'` 로 찍어 준다** — 보이지 않는 문자를 **눈에 보이게 만드는 유일한 길**이 `Debug` 다.

★★ **그래서 「앞 한 글자만」이 std 로 안 된다.**

```text
===== 소스: ex.rs =====
// chars() 조차 사람이 세는 글자가 아니다 — 앞 한 「글자」를 잘라 보면 드러난다
fn main() {
    let family = "\u{1F468}\u{200D}\u{1F469}\u{200D}\u{1F467}";  // 가족 이모지 하나
    let flag   = "\u{1F1F0}\u{1F1F7}";                            // 국기 이모지 하나
    let deco   = "e\u{0301}";                                     // e + 결합 악센트

    for (name, s) in [("가족", family), ("국기", flag), ("e+악센트", deco)] {
        let first: String = s.chars().take(1).collect();
        let rev: String = s.chars().rev().collect();
        println!("{:<10} 원본 {:?} · chars {} · 앞 1 char {:?} · 뒤집기 {:?}",
                 name, s, s.chars().count(), first, rev);
    }

    // 바이트로 자르면 더 나쁘다 — 경계를 맞춰도 「글자」가 쪼개진다
    let cut = &family[0..4];
    println!("family[0..4] = {:?} (경계는 맞았다)", cut);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가족         원본 "👨\u{200d}👩\u{200d}👧" · chars 5 · 앞 1 char "👨" · 뒤집기 "👧\u{200d}👩\u{200d}👨"
국기         원본 "🇰🇷" · chars 2 · 앞 1 char "🇰" · 뒤집기 "🇷🇰"
e+악센트      원본 "e\u{301}" · chars 2 · 앞 1 char "e" · 뒤집기 "\u{301}e"
family[0..4] = "👨" (경계는 맞았다)
(종료 코드 0)
```

- **`chars().rev()` 가 국기를 뒤집어 다른 나라를 만든다**(`🇰🇷` → `🇷🇰`).
- **`chars().take(1)`** 이 악센트를 잃고 `"e"` 를 준다.
- ★ **`family[0..4]` 는 패닉하지 않는다** — 경계를 맞췄기 때문이다. **그런데 결과가 가족이 아니다.**\
  「패닉 안 함」이 「맞게 잘림」이 아니다.

★★ **결론 — std 만으로는 「사람이 세는 글자」를 셀 수도 자를 수도 없다.**
표준 라이브러리가 주는 단위는 **바이트**와 **`char`(유니코드 스칼라 값)** 둘뿐이고,
**자소 묶음**(grapheme cluster)은 std 에 없다. 필요하면 외부 크레이트를 써야 하는데
**이 문서는 기준 소스를 std 로 고정했으므로 거기까지만 적는다** — 이 문서에서 외부 크레이트는 쓰지 않았다.

### (4) ★★ UTF-8 경계를 안 맞추면 — 실행에서 죽는다

**언제 쓰나** — `&s[..]` 안에 사람이 고른 숫자를 넣을 때마다.

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

**메시지가 세 가지를 한 줄에 말해 준다.**

```text
   byte index 1 is not a char boundary; it is inside '한' (bytes 0..3) of `한글 abc`
              ^                                      ^^^^^ ^^^^^^^^^^^     ^^^^^^^^^
              |                                        |         |             |
        (가) 어느 바이트가                     (나) 어느 문자 (다) 그 문자가    (라) 어느
             경계가 아닌가                          안이었나     차지한 범위       문자열이었나

   ★ (다) 가 처방이다 — 「bytes 0..3」 을 읽으면 0 이나 3 으로 옮기면 된다는 걸 바로 안다.
   ★ 「컴파일이 아니라 실행」이다. 위 배너에서 rustc 가 아무 말도 안 했다는 점을 보라.
```

★ 「자르기 전」 줄은 **찍히고** 그다음 줄은 **안 찍힌다** — 패닉은 그 자리에서 프로그램을 끝낸다.
★ **종료 코드가 `0` 이 아니라 `101`** 이다. 쉘 스크립트에서 이 코드로 패닉을 가려낼 수 있다.

### (5) `get(..)` — 패닉 대신 `None`

**언제 쓰나** — 인덱스가 **바깥에서 오는 값**일 때. 사용자 입력·파일·네트워크.

```text
===== 소스: ex.rs =====
// 같은 인덱스를 [] 대신 get() 으로 던지면 — 패닉이 아니라 Option 이 온다
fn main() {
    let s = "한글 abc";
    let v: Vec<i32> = vec![10, 20, 30];
    let sl: &[i32] = &v[..];

    println!("s.get(0..1)  = {:?}", s.get(0..1));   // 경계 아님
    println!("s.get(0..3)  = {:?}", s.get(0..3));   // 경계 맞음
    println!("s.get(0..99) = {:?}", s.get(0..99));  // 길이 초과
    println!("s.get(4..2)  = {:?}", s.get(4..2));   // 거꾸로

    println!("sl.get(7)    = {:?}", sl.get(7));
    println!("sl.get(1)    = {:?}", sl.get(1));
    println!("sl.get(1..2) = {:?}", sl.get(1..2));
    println!("sl.get(1..9) = {:?}", sl.get(1..9));
    println!("sl.get(2..1) = {:?}", sl.get(2..1));
    println!("v.get(7)     = {:?}", v.get(7));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.get(0..1)  = None
s.get(0..3)  = Some("한")
s.get(0..99) = None
s.get(4..2)  = None
sl.get(7)    = None
sl.get(1)    = Some(20)
sl.get(1..2) = Some([20])
sl.get(1..9) = None
sl.get(2..1) = None
v.get(7)     = None
(종료 코드 0)
```

★★ **`[]` 가 패닉하는 **모든** 경우에 `get` 은 `None` 을 준다** — 경계 위반·길이 초과·거꾸로 범위 셋 다.
**슬라이스의 `get` 도 같은 성질**이고, 정수 인덱스든 범위든 똑같다(`Some(20)` 대 `Some([20])` — 돌려주는 타입만 다르다).

| 쓴 것 | 되는 자리 | 안 되는 자리 | 대가 |
|---|---|---|---|
| `&s[a..b]` · `v[i]` | 인덱스를 **내가 만들었다** | 밖에서 온 값 | **패닉** — 프로그램이 죽는다 |
| `s.get(a..b)` · `v.get(i)` | 인덱스가 **밖에서 왔다** | — | `Option` 을 풀어야 한다 |

### (6) 범위 밖 인덱스 — 그리고 **컴파일 타임에 잡히는 자리**

**언제 쓰나** — 인덱스가 상수일 때. **여기서 배열과 문자열이 갈린다.**

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

★★ **컴파일이 거부한다.** 린트 이름은 **`unconditional_panic`** 이고 **기본이 `deny`** 라 경고가 아니라 **에러**다.
`let i = 7;` 이라고 변수에 넣어도 상수 전파에 걸린다. ★ **에러 번호가 없다** — `--explain` 으로 찾을 수 없는 부류다.

**그런데 같은 파일에서 문자열 경계 위반은 안 잡힌다.**

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

★★ **한 파일에 잘못이 둘인데 컴파일러는 하나만 짚는다.** 배열 쪽만 잡고 **문자열 쪽은 통과시킨다.**
배열 줄을 지우면 그대로 컴파일되고 **실행에서 죽는다.**

```text
===== 소스: ex.rs =====
// 리터럴을 상수 범위로 잘못 잘라도 컴파일은 통과한다 — 배열 인덱스와 다르다
fn main() {
    let a = &"한글"[0..1];   // 상수인데도 컴파일 타임에 안 잡힌다
    println!("{}", a);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====

thread 'main' (3167448) panicked at ex.rs:3:20:
byte index 1 is not a char boundary; it is inside '한' (bytes 0..3) of `한글`
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

★ **대조할 것은 괄호 안의 숫자가 아니라 「상수인데도 컴파일을 통과하고 실행에서 죽는다」는 성질이다.**

**`Vec` 과 슬라이스는 상수 인덱스도 컴파일 타임에 안 잡힌다** — 길이가 타입에 없기 때문이다.
그래서 셋을 나란히 던지려면 패닉을 받아 내야 한다.

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

- ★ **셋의 메시지가 한 글자도 같다** — `index out of bounds: the len is 5 but the index is 7`.\
  ★ **컴파일 타임 쪽은 `the length is 5` 라고 쓴다** — **`length` 와 `len` 이 다른 문구**다. 두 경로가 다른 코드에서 나온다는 증거다.
- ★ **`note: run with RUST_BACKTRACE=1 …` 줄은 첫 패닉에만 붙는다.** 두 번째부터는 안 나온다.
- ★ 괄호 안 숫자가 **셋 다 같다** — 같은 스레드에서 났기 때문이다. **이것이 그 숫자가 스레드 id 라는 증거**다.
- **대조할 것은 숫자가 아니라 「셋의 메시지가 같다」는 성질이다.**

**범위가 거꾸로면** 또 다른 메시지가 나온다.

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

★ **`&str` 쪽 메시지는 「성립해야 했던 주장」을 적어 준다**(`begin <= end (7 <= 3)`). 읽는 법이 반대다 —
**괄호 안이 실제 값이고, 그 값으로는 왼쪽 부등식이 거짓**이라는 뜻이다.
**대조할 것은 숫자가 아니라 「두 타입이 서로 다른 문구를 낸다」는 성질이다.**

**경계값도 던져 둔다** — 빈 범위와 `len` 자리는 **안 죽는다.**

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

★ **`len` 자리는 유효한 경계다** — 빈 슬라이스가 나온다. **`len + 1` 부터가 밖**이다.

**문자열에 정수 인덱스를 쓰면** 아예 컴파일이 안 된다 — 이건 **실행까지 가지도 않는다.**

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

★★ **`string indices are ranges of usize`** 한 줄이 이 주제의 제목이다.
`&str` 에는 **정수 인덱싱이 아예 구현돼 있지 않고 범위만 있다** — 그래서 `s[0]` 은 「0번 글자」가 아니라 **타입 오류**다.
★ `= note:` 가 **처방까지 준다** — `.chars().nth()` 또는 `.bytes().nth()`. (7)·(9)의 선택 표가 이 한 줄에서 나온다.

### (7) `split_at` · `chunks` · `windows` — 끝이 안 떨어지면

**언제 쓰나** — 슬라이스를 **여러 조각으로 나눠 돌 때.**

```text
===== 소스: ex.rs =====
// split_at · chunks · windows — 각각 무엇을 돌려주나, 끝이 안 떨어지면 어떻게 되나
fn main() {
    let v: Vec<i32> = (0..7).collect();   // 길이 7 — 3 으로 안 떨어진다
    let s: &[i32] = &v[..];
    println!("원본 {:?} · len {}", s, s.len());

    let (left, right) = s.split_at(3);
    println!("split_at(3)  -> {:?} + {:?}", left, right);
    let (l0, r0) = s.split_at(0);
    println!("split_at(0)  -> {:?} + {:?}", l0, r0);
    let (l7, r7) = s.split_at(7);
    println!("split_at(7)  -> {:?} + {:?}", l7, r7);

    println!("chunks(3)       -> {:?}", s.chunks(3).collect::<Vec<_>>());
    println!("chunks(3) 개수  -> {}", s.chunks(3).count());
    println!("chunks_exact(3) -> {:?}", s.chunks_exact(3).collect::<Vec<_>>());
    println!("chunks_exact(3).remainder() -> {:?}", s.chunks_exact(3).remainder());
    println!("rchunks(3)      -> {:?}", s.rchunks(3).collect::<Vec<_>>());

    println!("windows(3)      -> {:?}", s.windows(3).collect::<Vec<_>>());
    println!("windows(3) 개수 -> {}", s.windows(3).count());
    println!("windows(7)      -> {:?}", s.windows(7).collect::<Vec<_>>());
    println!("windows(8)      -> {:?}", s.windows(8).collect::<Vec<_>>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
원본 [0, 1, 2, 3, 4, 5, 6] · len 7
split_at(3)  -> [0, 1, 2] + [3, 4, 5, 6]
split_at(0)  -> [] + [0, 1, 2, 3, 4, 5, 6]
split_at(7)  -> [0, 1, 2, 3, 4, 5, 6] + []
chunks(3)       -> [[0, 1, 2], [3, 4, 5], [6]]
chunks(3) 개수  -> 3
chunks_exact(3) -> [[0, 1, 2], [3, 4, 5]]
chunks_exact(3).remainder() -> [6]
rchunks(3)      -> [[4, 5, 6], [1, 2, 3], [0]]
windows(3)      -> [[0, 1, 2], [1, 2, 3], [2, 3, 4], [3, 4, 5], [4, 5, 6]]
windows(3) 개수 -> 5
windows(7)      -> [[0, 1, 2, 3, 4, 5, 6]]
windows(8)      -> []
(종료 코드 0)
```

```text
   길이 7 을 3 으로 나누는 세 가지

   원본        [0][1][2][3][4][5][6]

   split_at(3) [0][1][2] | [3][4][5][6]        딱 두 조각. 튜플 (&[T], &[T]) 을 돌려준다
                                               ★ 합치면 항상 원본이다 — 겹치지도 빠지지도 않는다

   chunks(3)   [0][1][2] [3][4][5] [6]         겹치지 않는다. ★ 마지막 조각이 짧다 (길이 1)
   chunks_exact[0][1][2] [3][4][5]  ~~[6]~~    짧은 조각을 버린다. 버린 건 remainder() 로 따로 준다
   rchunks(3)  [0] [1][2][3] [4][5][6]         뒤에서부터 자른다 — ★ 짧은 조각이 앞에 온다

   windows(3)  [0][1][2]
                  [1][2][3]
                     [2][3][4]                 한 칸씩 밀며 겹친다. 개수 = len - n + 1 = 5
                        [3][4][5]              ★ n > len 이면 조각이 0 개다 (패닉 아님)
                           [4][5][6]
```

- **`chunks` 의 마지막 조각은 짧을 수 있다** — 「전부 같은 길이」를 기대하면 여기서 틀린다.\
  같은 길이만 원하면 **`chunks_exact`** 를 쓰고, 버려진 꼬리는 **`remainder()`** 로 받는다.
- **`windows(n)` 은 `n > len` 이면 빈 이터레이터**다. 패닉이 아니다.
- **`split_at(0)`·`split_at(len)` 은 한쪽이 빈 슬라이스**로 나온다. 정상이다.

**그럼 0 을 넣으면?** 셋 다 던져 본다.

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

★ **셋 다 패닉하고 메시지가 전부 다르다.** `windows(8)` 은 빈 이터레이터인데 `windows(0)` 은 패닉인 것이
「**크기 0 은 값이 아니라 잘못**」이라는 선언이다(0칸 창문은 무한히 많으니 셀 수가 없다).
**대조할 것은 숫자가 아니라 세 메시지가 서로 다르다는 성질이다.**

### (8) ★ `&Vec<T>` 말고 `&[T]` 를 받아라 — 14번과 같은 논리다

**언제 쓰나** — 함수 시그니처를 쓸 때마다.

[**14번 주제**](../14-string-vs-str/)가 「인자를 `&String` 이 아니라 `&str` 로 받아라」였다.
**여기는 글자 그대로 같은 논리다** — `String`:`&str` 자리에 `Vec<T>`:`&[T]` 를 넣으면 문장이 그대로 성립한다.

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

**`&[i32]` 로 바꾸면 전부 받는다.**

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
| `&v`(`&Vec<i32>`) | ✓ | ✓ (Deref 강제) |
| `&v[..]` | ✗ **E0308** | ✓ |
| `&v[1..3]`(일부만) | ✗ **E0308** | ✓ |
| `&arr`(`&[i32; 3]`) | ✗ **E0308** | ✓ (unsized 강제) |
| `&arr[..]` | ✗ **E0308** | ✓ |
| `&[]`(빈 리터럴) | ✗ | ✓ |

★★ **`&Vec<T>` 를 받으면 얻는 것이 하나도 없고 잃는 것만 다섯이다.** 14번의 결론과 **같은 문장**이다.
★ 반대 방향은 **비어 있다** — `&[T]` 에서 `&Vec<T>` 로 가는 공짜 강제는 없다(`to_vec()` 이라는 **복사**뿐이다).

### (9) `&str` 과 `&[u8]` — 왕복과 그 실패

**언제 쓰나** — 파일·네트워크에서 온 바이트를 문자열로 읽을 때.

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

- ★ **경고도 출력이다** — `invalid_from_utf8` 린트가 **리터럴 바이트열이면 컴파일 타임에** 잡아 준다(경고, 기본 `warn`).\
  (6)의 `unconditional_panic` 과 짝이다 — **상수로 적으면 컴파일러가 미리 본다.**
- ★★ **`error_len()` 이 두 실패를 가른다.**
  - **`None`** = 「**바이트가 모자란다**」 — 더 받으면 성립할 수도 있다(스트리밍에서 **이어 읽어야 하는 신호**).
  - **`Some(n)`** = 「**n 바이트가 아예 틀렸다**」 — 더 받아도 안 된다. 건너뛰어야 한다.
- **`valid_up_to()`** 는 「여기까지는 옳았다」는 바이트 위치다. `&bytes[..e.valid_up_to()]` 는 **안전하게 자를 수 있다.**
- **`from_utf8_lossy`** 는 실패 대신 대체 문자를 꽂아 준다 — 출력의 `a?b` 자리에 U+FFFD 가 들어간 것이다.

```text
   &str 과 &[u8] 의 관계 — 한 방향만 공짜다

   &str  ──as_bytes()──────────▶  &[u8]      공짜(그냥 같은 메모리를 다르게 본다). 실패 없음
   &[u8] ──str::from_utf8()────▶  Result     ★ 검사한다. 실패할 수 있다
         ──String::from_utf8_lossy()─▶ Cow<str>   실패 대신 U+FFFD 로 때운다

   ★ 왜 한쪽만 공짜인가 — &str 은 「UTF-8 이 맞다」는 불변식을 타입으로 들고 있다.
     그 불변식을 버리는 쪽(as_bytes)은 공짜고, 새로 세우는 쪽(from_utf8)은 검사가 필요하다.
```

### (10) `&mut [T]` — 창문으로 손을 넣으면 방 안이 바뀐다

**언제 쓰나** — 컬렉션의 **일부만** 고쳐야 할 때.

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

- **`&mut v[1..4]` 로 가운데만 넘겼더니 원본의 1·2·3번 칸만 두 배**가 됐다. 0번과 4번은 그대로다.
- ★ **`split_at_mut` 은 [10번 주제](../10-borrowing-and-aliasing-rules/)의 「가변 빌림은 하나뿐」을 깨는 것처럼 보이지만 아니다** —\
  **겹치지 않는 두 구간**이라 별칭이 아니다. 「하나뿐」은 **같은 자리**에 대한 규칙이다.

**슬라이스도 빌림이다** — 10번의 규칙이 그대로 적용된다.

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

★ **`mutable borrow later used here`** 가 [10번](../10-borrowing-and-aliasing-rules/)의 NLL 그대로다 —
`part[0] = 99;` 를 지우면 빌림이 `println!` 앞에서 끝나 통과한다.

### (11) 세 이터레이터를 언제 고르나

**언제 쓰나** — 문자열을 **돌 때마다.**

```text
===== 소스: ex.rs =====
// 세 이터레이터가 각각 무엇을 흘리나 — 같은 문자열에 셋을 다 돌린다
fn main() {
    let s = "한글 abc";

    let chars: Vec<char> = s.chars().collect();
    let bytes: Vec<u8> = s.bytes().collect();
    let idx: Vec<(usize, char)> = s.char_indices().collect();

    println!("chars()       ({:>2}개) {:?}", chars.len(), chars);
    println!("bytes()       ({:>2}개) {:?}", bytes.len(), bytes);
    println!("char_indices()({:>2}개) {:?}", idx.len(), idx);

    // 각각의 「앞에서 두 개」는 무엇인가
    let by_char: String = s.chars().take(2).collect();
    println!("chars().take(2)      = {:?}", by_char);
    println!("&s[..2] 은 패닉하지만 char_indices 로 끝을 구하면:");
    let end = s.char_indices().nth(2).map(|(i, _)| i).unwrap_or(s.len());
    println!("  두 char 뒤의 바이트 위치 {} -> {:?}", end, &s[..end]);

    // 바이트 하나만 꺼내는 길
    println!("s.as_bytes()[0]      = {}", s.as_bytes()[0]);
    println!("s.bytes().nth(0)     = {:?}", s.bytes().nth(0));
    println!("s.chars().nth(0)     = {:?}", s.chars().nth(0));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
chars()       ( 6개) ['한', '글', ' ', 'a', 'b', 'c']
bytes()       (10개) [237, 149, 156, 234, 184, 128, 32, 97, 98, 99]
char_indices()( 6개) [(0, '한'), (3, '글'), (6, ' '), (7, 'a'), (8, 'b'), (9, 'c')]
chars().take(2)      = "한글"
&s[..2] 은 패닉하지만 char_indices 로 끝을 구하면:
  두 char 뒤의 바이트 위치 6 -> "한글"
s.as_bytes()[0]      = 237
s.bytes().nth(0)     = Some(237)
s.chars().nth(0)     = Some('한')
(종료 코드 0)
```

| 무엇이 필요한가 | 고를 것 | 왜 |
|---|---|---|
| 문자 단위로 **보거나 바꾸고** 싶다 | **`chars()`** | 유니코드 스칼라를 준다. 인덱스는 안 준다 |
| **자를 위치**(바이트 번호)가 필요하다 | ★ **`char_indices()`** | `(바이트 인덱스, char)` 쌍을 준다 — **슬라이싱과 유일하게 이어지는 것** |
| **바이트 그대로** 다뤄야 한다(프로토콜·해시·I/O) | **`bytes()`** · `as_bytes()` | `u8` 을 준다. `as_bytes()` 는 O(1) 슬라이스 |
| **길이**만 알면 된다 | **`len()`** | O(1). `chars().count()` 는 **O(n)** 이다 |
| 사람이 세는 **글자 수**가 필요하다 | ★ **std 에 없다** | 자소 묶음은 표준 라이브러리 밖이다((3)) |

★★ **`char_indices()` 가 이 주제의 주인공**이다. `chars()` 는 **자를 위치를 안 준다** — 그래서
`chars().take(2)` 로 만든 `String` 은 **새 할당**이고, `&s[..end]` 는 **빌림**이다. 둘은 다른 비용이다.

**안전하게 자르는 법 세 가지**를 나란히 던져 둔다.

```text
===== 소스: ex.rs =====
// 「앞 N 바이트까지 안전하게 자르기」를 std 만으로 하는 법
fn main() {
    let s = "한글 abc";

    // (가) find 가 돌려주는 것은 바이트 인덱스다
    println!("s.find('글') = {:?}", s.find('글'));
    println!("s.find('a')  = {:?}", s.find('a'));

    // (나) char_indices 로 경계를 찾아 자른다
    let limit = 4;                       // 4 바이트까지만 쓰고 싶다
    let end = s.char_indices()
               .map(|(i, c)| i + c.len_utf8())
               .take_while(|&e| e <= limit)
               .last()
               .unwrap_or(0);
    println!("limit {} -> 안전한 끝 {} -> {:?}", limit, end, &s[..end]);

    // (다) is_char_boundary 로 뒤로 물러나며 찾는다
    let mut e = limit;
    while e > 0 && !s.is_char_boundary(e) { e -= 1; }
    println!("is_char_boundary 로 물러나기 -> {} -> {:?}", e, &s[..e]);

    // (라) floor_char_boundary 가 안정화됐나
    println!("floor_char_boundary(4) = {}", s.floor_char_boundary(4));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.find('글') = Some(3)
s.find('a')  = Some(7)
limit 4 -> 안전한 끝 3 -> "한"
is_char_boundary 로 물러나기 -> 3 -> "한"
floor_char_boundary(4) = 3
(종료 코드 0)
```

★ **셋 다 `3` 을 준다.** `find` 가 돌려주는 것도 **바이트 인덱스**라 그대로 슬라이싱에 쓸 수 있다.
★ **`floor_char_boundary` 는 이 툴체인의 안정판에서 컴파일됐다**(실측). 옛 툴체인에서는 나이틀리였으니
**버전에 달린 항목으로 아래 표에 올려 둔다.**

## 문법 — 형태와 규칙

### 형태

```rust
// 1) 슬라이스 타입 — 참조로만 쓴다
let a: &[i32]     = &[1, 2, 3];
let b: &mut [i32] = &mut [1, 2, 3][..];
let c: &str       = "한글";

// 2) 범위 여섯 꼴
let v = vec![0, 1, 2, 3, 4];
let _ = &v[1..3];    // Range            1 포함 3 제외
let _ = &v[1..=3];   // RangeInclusive   양끝 포함
let _ = &v[..3];     // RangeTo
let _ = &v[..=3];    // RangeToInclusive
let _ = &v[1..];     // RangeFrom
let _ = &v[..];      // RangeFull

// 3) 패닉하지 않는 길
let _ = v.get(1..3);   // Option<&[i32]>
let _ = v.get(1);      // Option<&i32>

// 4) 함수 인자는 슬라이스로 받는다
fn f(s: &[i32]) -> i32 { s.iter().sum() }
fn g(s: &str)   -> usize { s.len() }

// 5) 문자열을 도는 세 길
for c in "한글".chars() {}
for b in "한글".bytes() {}
for (i, c) in "한글".char_indices() {}

// 6) 경계를 직접 묻는다
let s = "한글";
let _ = s.is_char_boundary(1);   // false
let _ = s.floor_char_boundary(1);

// 7) 바이트와의 왕복
let _ = s.as_bytes();
let _ = std::str::from_utf8(s.as_bytes());
```

### 금지 사례 — 던져서 받은 여덟

| 코드 | 무엇이 나나 | 언제 잡히나 | 한 줄 |
|---|---|---|---|
| `s[0]`(`s: &str`) | **E0277** | **컴파일** | 문자열 인덱스는 범위뿐이다 |
| `sum_vec(&arr[..])`(`&Vec<i32>` 인자) | **E0308** | **컴파일** | 슬라이스는 `Vec` 이 아니다 |
| `&mut v[..]` 살아 있는데 `v` 읽기 | **E0502** | **컴파일** | 슬라이스도 빌림이다 |
| `arr[7]`(`arr: [i32; 5]`, 상수) | `error: this operation will panic at runtime` | **컴파일**(린트 `unconditional_panic`) | 길이가 타입에 있으면 미리 본다 |
| `v[7]` · `sl[7]` | 패닉 `index out of bounds` | **실행** | `Vec`·슬라이스는 길이가 타입에 없다 |
| `&s[0..1]`(경계 아님) | 패닉 `byte index 1 is not a char boundary` | ★ **실행** | 상수여도 안 잡힌다 |
| `&s[7..3]` · `&v[4..2]` | 패닉(문구가 서로 다르다) | **실행** | 거꾸로 범위 |
| `chunks(0)` · `windows(0)` · `split_at(len+1)` | 패닉(문구가 셋 다 다르다) | **실행** | 크기 0 은 값이 아니다 |

### 자를 위치를 고르는 순서

```text
   &str 에 숫자를 적으려 한다
        │
        ▼
   ① 그 숫자가 어디서 왔나?
        ├─ char_indices()·find()·floor_char_boundary() 가 준 것 ──▶ 그대로 써도 된다
        ├─ 내가 센 「글자 수」                        ──▶ ★ 바이트 수가 아니다. 다시 구해라
        └─ 바깥(입력·설정·파일)                       ──▶ ② 로
        │
        ▼
   ② 죽어도 되나?
        ├─ 아니오 ──▶ s.get(a..b) 를 쓰고 None 을 처리한다
        └─ 예(내 불변식이 보장한다) ──▶ &s[a..b]. ★ 그 불변식을 주석으로 남겨라
        │
        ▼
   ③ 사람이 세는 「글자」 단위로 잘라야 하나?
        └─ 예 ──▶ std 로는 안 된다. 요구사항을 바꾸거나 외부 크레이트를 검토한다
```

## 어디서 틀리나

### 1. ★★ 「`len()` 이 글자 수다」

- `"한글"` 의 `len()` 은 **6** 이다. 한글 한 글자가 UTF-8 **3바이트**다.
- 실측표의 첫 세 줄이 그것이다 — **ASCII 에서만 `len()` = 글자 수**다.
- ★ 더 나쁜 것은 **테스트가 ASCII 로만 짜여 있으면 이 버그가 안 잡힌다**는 점이다.\
  문자열을 자르는 코드의 테스트에는 **반드시 다바이트 문자를 넣는다.**

### 2. ★★ 「그럼 `chars().count()` 를 쓰면 된다」

- 절반만 맞다. `chars()` 는 **유니코드 스칼라**를 세지 **사람이 보는 글자**를 세지 않는다.
- 실측: 가족 이모지 하나가 **`chars` 5개**, 국기 하나가 **2개**, `e` + 악센트가 **2개**, 조합형 `한` 이 **3개**.
- ★ `chars().rev()` 로 문자열을 뒤집으면 **국기가 다른 나라가 되고 악센트가 앞 글자에 붙는다.**
- ★ **`chars().count()` 는 O(n)** 이다 — 길이 검사에 쓰면 조용히 느려진다. 길이는 `len()`.

### 3. ★★ 「std 에 자소 묶음이 있겠지」

- **없다.** std 가 주는 단위는 **바이트**와 **`char`** 둘뿐이다.
- 「앞 10글자만 보여 주기」 같은 요구가 오면 **요구를 먼저 다시 묻는다** —\
  보통 필요한 것은 「10글자」가 아니라 「**너무 길면 줄이기**」이고, 그건 `char_indices()` 로 충분하다.
- ★ 이 문서는 기준 소스를 std 로 고정했으므로 **외부 크레이트를 쓰지 않았다.**\
  「std 만으로는 안 된다」가 이 절의 결론이고, 그 이상은 이 문서의 근거 범위 밖이다.

### 4. ★★ 「컴파일이 통과했으니 인덱스가 맞다」

- 배열의 **상수** 인덱스만 컴파일 타임에 잡힌다(`unconditional_panic`). `Vec`·슬라이스는 안 잡힌다.
- **문자열 경계 위반은 상수여도 안 잡힌다** — 같은 파일에서 배열 쪽만 에러가 났다((6) 실측).
- ★ 「Rust 는 컴파일이 되면 안전하다」의 **정확한 뜻은 「메모리 안전」이지 「패닉 안 함」이 아니다.**

### 5. ★ 「`get` 은 안전하니까 늘 `get` 을 쓴다」

- `get` 은 **`Option` 을 풀어야** 한다. 인덱스를 **내가 방금 만든 자리**에서 쓰면 `unwrap()` 이 늘 뿐이다.
- 기준은 「**이 인덱스가 밖에서 왔나**」다. 밖에서 왔으면 `get` 을, 내가 만들었으면 `[]` 를 쓴다.
- ★ `[]` 를 쓸 때는 **왜 안전한지를 주석 한 줄**로 남긴다 — 그게 이 선택의 대가다.

### 6. ★ 「`chunks` 는 전부 같은 길이다」

- **마지막 조각이 짧을 수 있다**(길이 7 을 3 으로 → `[..3]`, `[3..6]`, `[6..7]`).
- 같은 길이가 필요하면 **`chunks_exact`** 를 쓰고 꼬리는 **`remainder()`** 로 받는다.
- ★ `rchunks` 는 **짧은 조각이 앞**에 온다 — 방향이 바뀐다.

### 7. 「`windows(0)` 은 빈 이터레이터겠지」

- **패닉**이다(`window size must be non-zero`). `windows(8)`(길이보다 큼)은 **빈 이터레이터**인데 0 만 다르다.
- ★ 「범위를 넘으면 빈 것」과 「0 은 잘못」이 **다른 규칙**이라는 것을 여기서 처음 만난다.

### 8. ★ 「인자는 `&Vec<T>` 로 받으면 된다」

- 받는 것이 줄기만 한다 — 배열·부분 슬라이스·빈 리터럴이 **전부 거부**된다((8) 표).
- [**14번 주제**](../14-string-vs-str/)의 `&String` 과 **완전히 같은 논리**다. 외울 것은 하나다 —\
  **「소유 타입의 참조 말고 그 뷰 타입을 받아라」**.

### 9. 「슬라이스는 복사본이다」

- 아니다. `&mut [T]` 로 바꾸면 **원본이 바뀐다**((10)).
- `a.as_ptr()` 이 `&arr[1]` 과 같은 주소라는 실측이 그 증거다((1)).
- ★ 그래서 **슬라이스는 빌림 규칙을 그대로 진다** — E0502 가 나는 이유다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `&[T]`·`&str` 이 **포인터+길이** | **언어** | Reference — Slice types · `size_of` 가 16 |
| `&str` 이 **UTF-8 임이 타입의 불변식** | **언어** | `from_utf8` 이 `Result` 를 돌려주는 것 자체 |
| **바이트 인덱스**로만 슬라이싱되는 것 | **언어** | E0277 `string indices are ranges of usize` |
| 경계 위반이 **패닉**인 것 | **언어** | std 문서의 Panics 절 · 실측 |
| `get` 이 `[]` 와 **같은 조건에서 `None`** | **언어** | 셋(경계·초과·역순) 실측 |
| `chunks` 마지막 조각이 **짧을 수 있는 것** | **언어** | std 문서 · 실측 `[[0,1,2],[3,4,5],[6]]` |
| `windows(0)`·`chunks(0)` 이 **패닉인 것** | **언어** | std 문서의 Panics 절 · 실측 |
| `&Vec<T>` → `&[T]` 강제가 **되는 것** | **언어**(`Deref`) | `sum_slice(&v)` 통과 |
| `&[T]` → `&Vec<T>` 가 **안 되는 것** | **언어** | E0308 |
| **포인터 크기 8·`Vec` 24** | ★ **플랫폼**(포인터 폭) | `x86_64` 기준. 32비트면 절반이다 |
| **패닉 메시지 문구** | **rustc·std 구현** | `the len is` / `the length is` 가 **경로마다 다르다** |
| ★ 패닉 첫 줄의 **괄호 안 숫자** | **런타임**(OS 스레드 id) | 같은 바이너리 3회에 전부 달랐다 |
| `unconditional_panic` 이 **기본 `deny`** | **rustc 판** | 린트는 판마다 추가·승격된다 |
| `invalid_from_utf8` 이 **기본 `warn`** | **rustc 판** | 〃 |
| **상수 배열 인덱스만 잡히는 것** | **rustc 구현**(상수 전파) | 문자열 경계는 같은 파일에서 안 잡혔다 |
| `str::floor_char_boundary` 가 **안정판인 것** | **rustc·std 판** | 이 툴체인(1.92.0)에서 컴파일됨 — 옛 판에서는 나이틀리였다 |
| `type_name_of_val` 의 **출력 문자열** | **rustc 구현** | `core::ops::range::Range<i32>` — **경로 표기는 바뀔 수 있다** |
| **종료 코드 101** | **std 구현**(기본 패닉 처리) | `panic = "abort"` 로 빌드하면 달라진다 |

★ **「언어가 보장한다」와 「이 판이 그렇다」를 가르는 기준** — std 문서의 **Panics 절에 적힌 것**은 계약이고,
**메시지 글자**는 계약이 아니다. 실측이 그 구분을 보여 준다 — 같은 실패가 컴파일 경로에서는 `the length is`,
런타임 경로에서는 `the len is` 였다. **글자로 테스트를 짜면 판이 오를 때 깨진다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 함수 인자로 여러 개를 받는다 | ★ **`&[T]`** · **`&str`** | 배열·`Vec`·부분까지 전부 받는다((8)) |
| 인자를 **고쳐야** 한다 | **`&mut [T]`** | 원본이 바뀐다. 길이는 못 바꾼다 |
| 길이를 **바꿔야** 한다(push·remove) | `&mut Vec<T>` | 슬라이스로는 못 한다 — 길이가 고정이다 |
| 소유권이 필요하다(보관·반환) | `Vec<T>` · `String` | 빌림은 원본보다 오래 못 산다([**12번 주제**](../12-lifetime-annotations-and-elision/)) |
| 인덱스가 **밖에서 왔다** | ★ **`get(..)`** | 패닉 대신 `None` |
| 인덱스를 **내가 방금 만들었다** | `[]` | `unwrap` 이 안 는다. 왜 안전한지 주석 |
| 문자열을 **자를 위치**가 필요하다 | ★ **`char_indices()`** | 바이트 인덱스를 주는 유일한 것 |
| 문자열 **길이**만 필요하다 | `len()` | O(1). `chars().count()` 는 O(n) |
| **문자 단위** 처리가 필요하다 | `chars()` | 단, 자소 묶음이 아니다 |
| **바이트** 그대로 다룬다(I/O·해시) | `as_bytes()` · `bytes()` | `as_bytes()` 는 O(1) |
| 고정 크기 조각으로 나눈다 | `chunks_exact` + `remainder()` | `chunks` 는 꼬리가 짧다 |
| 이웃한 쌍·삼중을 본다 | `windows(n)` | 겹치며 민다 |
| 두 부분을 **동시에 고친다** | `split_at_mut` | 겹치지 않으므로 별칭이 아니다 |
| 사람이 세는 글자 단위 | ★ **요구를 다시 묻는다** | std 에 없다((3)) |

판단 규칙 두 줄.

- **받을 때는 뷰(`&[T]`·`&str`), 담을 때는 소유(`Vec<T>`·`String`).**
- **숫자를 `&str` 에 적기 전에 그 숫자가 바이트 인덱스인지부터 확인한다.** 아니면 `char_indices()` 로 구해 온다.

## 핵심 문장

- ★★ **슬라이스는 복사본이 아니라 「포인터 + 길이」로 된 창문**이다. `size_of::<&[i32]>()` 가 **16**, `size_of::<&Vec<i32>>()` 가 **8** 이다.
- ★★ **`&str` 의 인덱스는 바이트 번호다.** `s[0]` 은 컴파일 에러(**E0277**)이고, `&s[0..1]` 은 **실행 패닉**이다.
- ★★ **`len()` · `chars().count()` · 사람이 세는 글자 수는 셋 다 다르다.** 셋이 같아지는 것은 ASCII 뿐이다.
- ★ **`chars()` 도 「글자」가 아니다** — 가족 이모지 하나가 `char` 다섯이다. **자소 묶음은 std 에 없다.**
- ★ **경계 위반 메시지가 처방까지 준다** — `it is inside '한' (bytes 0..3)` 을 읽으면 0 이나 3 으로 옮기면 된다.
- **`get(..)` 은 `[]` 가 패닉하는 모든 경우에 `None`** 을 준다 — 경계·초과·역순 셋 다. 슬라이스도 같다.
- ★★ **컴파일 타임에 잡히는 것은 배열의 상수 인덱스뿐**이다(`unconditional_panic`). **문자열 경계는 상수여도 안 잡힌다.**
- **범위는 문법이 아니라 값**이다 — 여섯 타입이 있고 변수에 담긴다. `..` 만 타입 파라미터가 없다.
- **`chunks` 는 꼬리가 짧고 `windows` 는 겹친다.** 둘 다 **크기 0 은 패닉**이다.
- ★ **인자는 `&Vec<T>` 가 아니라 `&[T]` 로 받는다** — [**14번 주제**](../14-string-vs-str/)의 `&String` 과 같은 논리다.
- ★ **`&str` → `&[u8]` 은 공짜, 반대는 검사**다. `Utf8Error::error_len()` 이 「모자람」과 「틀림」을 가른다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 15번)
- [**14번 주제**](../14-string-vs-str/)(`String` 대 `&str`) — ★ **직접 선행**.\
  **그쪽은** 「두 타입이 왜 나뉘고 인자를 어느 쪽으로 받나」, **여기는** 「그 `&str` 을 **어디서 자를 수 있나**」다.\
  ★ **`&Vec<T>` 대신 `&[T]` 를 받는 논리는 그쪽의 `&String` 대 `&str` 과 같은 논리다**((8)).
- [**10번 주제**](../10-borrowing-and-aliasing-rules/)(빌림 `&`·`&mut`) — **그쪽은** 별칭 규칙 자체,\
  **여기는** 그 규칙이 **슬라이스에 그대로 적용되는 자리**((10)의 E0502·`split_at_mut`)
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — 슬라이스가 **빌림**이라는 전제가 거기서 온다
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입·정수 오버플로) — **그쪽은** 정수 표현과 오버플로 정책,\
  **여기는** 그 정수가 **인덱스로 쓰일 때** 생기는 일. ★ 둘 다 「디버그에서 패닉」이라는 같은 장치를 쓴다
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기) — 슬라이스를 **반환**할 때 나오는 `'a` 가 거기다
- [**11번 주제**](../11-borrow-checker-rejections/)(거부되는 전형) — `split_at_mut` 이 푸는 「두 자리 동시 가변 빌림」의 정본
- [**13번 주제**](../13-struct-references-and-static/)(구조체에 참조 담기) · [**16번 주제**](../16-structs-impl-and-associated-functions/)(구조체·`impl`) — 이 배치의 형제
- [`../../../../data-representation/`](../../../../data-representation/) — ★ **UTF-8 인코딩 자체의 정본**.\
  **그쪽은** 코드 포인트·코드 유닛·인코딩 방식(**무엇이 몇 바이트로 적히나**),\
  **여기는** **그 인코딩 때문에 인덱싱이 패닉하는 자리**다. 바이트 격자의 16진값이 왜 그 값인지는 거기서 읽는다
- [목록의 **21번 주제**](../21-option-and-combinators/)(`Option` 조합 메서드) — `get(..)` 이 돌려주는 것을 다루는 법
- [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/)(`Iterator`) · **37번 주제**(`IntoIterator`) — `chars()`·`chunks()` 가 이터레이터인 것의 정본
- [목록의 **38번 주제**](../38-vec-api-capacity-retain-and-drain/)(`Vec` API) — `retain`·`drain`·용량 재할당이 참조를 무효화하는 이야기
- [목록의 **43번 주제**](../43-deref-coercion-and-smart-pointers/)(`Deref` 강제) — `&Vec<T>` 가 `&[T]` 처럼 쓰이는 장치의 정본
- 목록의 **48번 주제**(문자열 포맷) — `{:?}` 가 ZWJ 를 `'\u{200d}'` 로 찍어 주는 이야기

## 용어 풀이

- **슬라이스(slice)** — 연속한 원소 열의 일부를 빌린 뷰. 타입은 `[T]`, 실제로 쓰는 것은 `&[T]`·`&mut [T]`.
- **문자열 슬라이스(`&str`)** — UTF-8 임이 보장된 바이트 열의 뷰. `&[u8]` 에 불변식이 하나 더 붙은 것.
- **뚱뚱한 포인터(fat pointer)** — 주소 + 길이를 함께 든 참조. `&[T]`·`&str` 이 그렇다(16바이트).
- **바이트 인덱스(byte index)** — `&str` 슬라이싱·`find`·`char_indices` 가 쓰는 단위. 글자 번호가 아니다.
- **문자 경계(char boundary)** — 한 `char` 의 UTF-8 표현이 시작하는 바이트 위치. `len` 자리도 경계다.
- **`char`** — 유니코드 스칼라 값 하나(4바이트 고정). 사람이 세는 글자가 아니다.
- **자소 묶음(grapheme cluster)** — 사람이 「한 글자」로 보는 단위. ★ **std 에 없다.**
- **결합 문자(combining character)** — 앞 글자에 붙어 하나로 보이는 문자(U+0301 같은 것).
- **ZWJ(zero-width joiner, U+200D)** — 이모지 여럿을 한 그림으로 잇는 보이지 않는 문자.
- **범위(range)** — `a..b` 같은 값. 여섯 타입이 있고 `SliceIndex` 를 구현한 것만 슬라이싱에 쓰인다.
- **패닉(panic)** — 복구 불가로 선언하고 스레드를 되감는 것. 기본 종료 코드 **101**.
- **린트(lint)** — 컴파일러의 선택적 진단. `allow`/`warn`/`deny` 단계가 있다(`unconditional_panic` 은 기본 `deny`).

---

## 더 들어가면

- ★ **`SliceIndex` 트레이트가 이 주제의 뼈대다.** `v[x]` 는 `Index` 를 거쳐 `SliceIndex<[T]>` 로 간다 —\
  `usize` 는 `&[T]` 에 대해 구현돼 있고 `str` 에 대해서는 **안 돼 있다**. E0277 의 `the trait SliceIndex<str> is not implemented` 가 그 말이다.
- **`&mut [T]` 로는 길이를 못 바꾼다** — `push`·`remove` 는 `Vec` 의 것이다. 슬라이스는 **칸의 내용만** 바꾼다.\
  「길이를 바꾸는 것」과 「내용을 바꾸는 것」을 타입으로 가른 설계다.
- ★ **`split_at_mut` 이 별칭 규칙을 어기지 않는 이유**는 「겹치지 않음」을 **런타임에 확인하고** 그 뒤에 `unsafe` 로 나누기 때문이다.\
  안전한 추상으로 감싼 `unsafe` 의 교과서 사례다 — 목록의 **56번 주제**.
- **`chunks_exact` 가 `chunks` 보다 빠를 수 있다** — 길이가 고정이라 컴파일러가 루프를 풀기 쉽다.\
  ★ 다만 이 문서는 **속도를 재지 않았다** — 측정 환경이 필요한 주장이라 여기서는 성질까지만 적는다.
- ★ **`Utf8Error::error_len()` 의 `None` 은 스트리밍의 신호다.** 네트워크로 UTF-8 을 조각내어 받을 때\
  `None` 이면 **버퍼에 남겨 두고 더 받고**, `Some(n)` 이면 **그 n 바이트를 버린다.** 두 실패를 같게 다루면 조용히 데이터를 잃는다.
- **`String::from_utf8`(소유판)은 실패 시 원래 `Vec<u8>` 을 돌려준다**(`FromUtf8Error::into_bytes`) —\
  `str::from_utf8`(빌림판)과 표면이 다르다.
- ★ **바이트 격자는 다른 언어에서도 쓸 수 있는 도구다.** 「인덱스가 무엇의 번호인가」를 묻는 언어는 전부 이 그림이 필요하다 —\
  Java 의 `char` 가 UTF-16 코드 유닛이라 이모지 하나가 둘인 것도 같은 그림으로 읽힌다.
