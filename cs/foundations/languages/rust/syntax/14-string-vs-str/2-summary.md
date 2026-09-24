# rust/syntax/14 — `String` 대 `&str` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `String`](https://doc.rust-lang.org/std/string/struct.String.html) ·
> [std — `str`](https://doc.rust-lang.org/std/primitive.str.html) ·
> [std — `Deref` 강제](https://doc.rust-lang.org/std/ops/trait.Deref.html) ·
> [The Rust Reference — Type coercions](https://doc.rust-lang.org/reference/type-coercions.html) ·
> [The Rust Book 4.3](https://doc.rust-lang.org/book/ch04-03-slices.html) ·
> `rustc --explain E0308` / `E0382` / `E0277` / `E0515` / `E0599` / `E0631`.
> ★ `--explain` 은 **확인용으로만 열었고 본문에 옮기지 않았다.** 본문의 진단은 전부 내가 던져서 받은 것이다.
> **실행 검증** — 이 문서의 모든 출력·에러·경고는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 얻은 것이다. `cargo` 는 쓰지 않았다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다.** 이 갈래는 `--edition 2021` 을 반드시 붙인다.\
> 소스 파일 이름은 전부 `ex.rs` 로 고정했고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★ **크기·주소 실측은 `x86_64`(포인터 8바이트) 기준**이다. 32비트 대상에서는 숫자가 달라진다 — 그래서 **폭도 같이 찍었다**.
> **버전** — `String`·`str`·`Deref` 강제는 전부 1.0.0부터다. `String::from`·`to_string`·`to_owned`·`format!` 도 1.0.0부터.\
> `String::into_boxed_str` 는 1.4.0, `str::to_uppercase` 는 1.2.0이다(std 문서의 `since` 표기).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`String` 은 창고를 가진 주인이고, `&str` 은 그 창고를 들여다보는 창이다.**

| 비유 | 실체 |
|---|---|
| **창고를 가진 주인** — 열쇠·재고량·선반 수를 들고 다닌다 | **`String`** — 힙 포인터 · `len` · `cap` **세 칸**(24바이트) |
| **창고를 들여다보는 창** — 「어디서부터 몇 칸」만 적혀 있다 | **`&str`** — 힙 포인터 · `len` **두 칸**(16바이트) |
| **주인을 가리키는 쪽지** — 창고가 아니라 **주인**을 가리킨다 | **`&String`** — 얇은 포인터 **한 칸**(8바이트). 한 번 더 건너뛴다 |
| 창을 낸다고 **물건을 옮기지는 않는다** | `String` → `&str` 은 **복사가 아니다** — 힙 주소가 같다 |
| 창만 보고 **새 창고를 짓는 것** | `&str` → `String` 은 **할당 + 복사**다 |
| 「**어떤 창이든 받습니다**」라고 써 붙인 가게 | `fn f(s: &str)` — `&String`·`&&String`·리터럴이 **다 들어온다** |
| 「**우리 주인만 받습니다**」 | `fn f(s: &String)` — **리터럴이 아예 못 들어온다**(E0308) |
| 창고를 넘기면 **내 손에서 사라진다** | `String` 은 `Copy` 가 아니다 — 이동한다(E0382) |
| 쪽지는 **복사해도 그만**이다 | `&str` 은 `Copy` 다 — 넘겨도 원본이 산다 |

- ★★ **`&str` 은 「짧은 문자열」이 아니라 「남의 바이트를 보는 창」이다.** 길이와 무관하다.
- ★★ **`&String` 은 거의 항상 쓸 이유가 없다.** `&str` 로 받으면 `&String` 도 공짜로 들어오는데, 반대는 안 된다.
- ★ 이 주제의 결론 한 줄 — **인자는 `&str`, 필드·반환은 `String`.**

```text
   let s = String::from("가나다");          // 한글 3자 = UTF-8 9바이트
   let v: &str    = &s;                     // 같은 바이트를 보는 창
   let r: &String = &s;                     // 주인을 가리키는 쪽지

   스택                                     힙
   +--------------------+                   +-------------------------+
   | s   ptr  ----------+-----------------> | 가 나 다   (9 바이트)    |
   |     len  9         |           ^       +-------------------------+
   |     cap  9         |           |
   +--------------------+           |        ← 힙 버퍼는 「하나」뿐이다
    24 바이트 = 3 워드               |
                                    |
   +--------------------+           |
   | v   ptr  ----------+-----------+
   |     len  9         |
   +--------------------+
    16 바이트 = 2 워드   ← &str: 주소 + 길이. 「팻 포인터」

   +--------------------+
   | r   ptr  ----------+---> s 의 스택 세 칸을 가리킨다 (힙이 아니다)
   +--------------------+
     8 바이트 = 1 워드   ← &String: 얇은 포인터. 힙까지 두 번 건너뛴다
```

> **`String`** — 힙에 UTF-8 바이트를 **소유**하는 타입. 스택에 **포인터·길이·용량 세 칸**을 둔다.\
> 늘릴 수 있고(`push_str`), 자기가 죽을 때 힙 버퍼를 해제한다(`Drop`).

> **`str`** — **크기가 고정되지 않은 타입**(unsized). 그래서 변수에 그냥 담지 못하고\
> 항상 `&str`·`Box<str>`처럼 **포인터 뒤에서** 쓴다. 그 포인터가 **길이를 같이 들고 다닌다**.

> **`&str`(문자열 슬라이스)** — 「어느 주소에서 몇 바이트」를 적은 **팻 포인터**. 소유하지 않는다.\
> 그래서 **`&str` 을 만드는 데는 할당이 없다**.

> **역참조 강제(deref coercion)** — `&String` 을 `&str` 이 필요한 자리에 넣으면\
> 컴파일러가 `Deref` 를 따라 **자동으로 바꿔 준다**. ★ **전이적이다** — `&&&String` 도 `&str` 이 된다.

> **팻 포인터(fat pointer)** — 주소 하나에 **메타데이터 한 칸**을 더 붙인 포인터.\
> `&str`·`&[T]` 는 길이를, `&dyn Trait` 는 vtable 주소를 붙인다. 그래서 **두 워드**다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **세 꼴이 각각 무엇인가** — `String`·`&str`·`&String` 이 스택에서 몇 칸이고, 힙을 소유하나.
2. **함수 인자를 어느 쪽으로 받나** — 왜 `&str` 인가. 「호출할 수 있는 타입의 수」로 답할 수 있나.
3. **어느 변환이 공짜이고 어느 쪽이 비싼가** — `String` → `&str` 과 `&str` → `String` 이 왜 대칭이 아닌가.

★ [**08번 주제**](../08-ownership-and-move/)가 「**값을 넘기면 왜 잃나**」였다면, 여기는 **그 규칙이 문자열이라는 한 타입에서 어떤 모양으로 나타나나**다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

**언제 쓰나** — 아래 모든 절이 이 넷 중 하나로 접지한다.

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **일부러 던져서 받는 컴파일 에러** | 「이 자리에 이 타입은 못 온다」 — E0308·E0382·E0631 | 08\~12번에서 이어받음 |
| ★★ **`size_of` 로 스택 칸 수 세기** | `String` 3워드 · `&str` 2워드 · `&String` 1워드 | ★ 이 주제의 고유 창 |
| ★★ **`as_ptr()` 로 힙 주소 대조** | `String` → `&str` 이 **복사가 아니라는 것**을 주소로 증명 | ★ 이 주제의 고유 창 |
| **같은 코드에서 타입만 바꿔 던지기** | `Copy` 여부가 갈리는 자리 — 한쪽 E0382, 한쪽 통과 | [**09번 주제**](../09-copy-clone-and-drop/)에서 이어받음 |

★ **메모리 레이아웃이 이 주제의 도구다.** 「소유한다 / 빌린다」는 말로만 들으면 안 잡히는데,
**스택 칸 수와 힙 주소**를 찍으면 눈에 보인다. 세 꼴이 갈리는 이유가 거기 전부 있다.

비용 — 없음. `size_of` 는 **컴파일 타임 상수**이고, `as_ptr()` 는 스택 칸 하나를 읽는 것이다.

### (1) ★★ 세 꼴은 스택에서 몇 칸인가 — 전부 찍는다

**언제 쓰나** — 「이 타입을 넘기면 뭐가 복사되나」가 궁금할 때. **외우지 말고 잰다.**

```text
===== 소스: ex.rs =====
// 세 꼴이 스택에서 몇 바이트인가 — 외우지 말고 전부 찍는다
use std::mem::size_of;

fn main() {
    println!("포인터 폭 usize = {}", size_of::<usize>());
    println!("-- 소유하는 것 --");
    println!("String     = {}", size_of::<String>());
    println!("Vec<u8>    = {}", size_of::<Vec<u8>>());
    println!("-- 빌린 것 --");
    println!("&str       = {}", size_of::<&str>());
    println!("&[u8]      = {}", size_of::<&[u8]>());
    println!("&String    = {}", size_of::<&String>());
    println!("&&String   = {}", size_of::<&&String>());
    println!("&&&String  = {}", size_of::<&&&String>());
    println!("&Vec<u8>   = {}", size_of::<&Vec<u8>>());
    println!("&&str      = {}", size_of::<&&str>());
    println!("-- 그 밖 --");
    println!("Box<str>   = {}", size_of::<Box<str>>());
    println!("Box<String>= {}", size_of::<Box<String>>());
    println!("char       = {}", size_of::<char>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
포인터 폭 usize = 8
-- 소유하는 것 --
String     = 24
Vec<u8>    = 24
-- 빌린 것 --
&str       = 16
&[u8]      = 16
&String    = 8
&&String   = 8
&&&String  = 8
&Vec<u8>   = 8
&&str      = 8
-- 그 밖 --
Box<str>   = 16
Box<String>= 8
char       = 4
(종료 코드 0)
```

읽는 법 — **포인터 폭이 8이라는 것을 먼저 찍었기 때문에** 나머지 숫자를 워드 수로 읽을 수 있다.

| 타입 | 바이트 | 워드 | 무엇이 들어 있나 | 힙을 소유하나 |
|---|---|---|---|---|
| `String` | **24** | 3 | ptr · len · cap | **예** |
| `&str` | **16** | 2 | ptr · len (**팻 포인터**) | 아니오 |
| `&String` | **8** | 1 | ptr (**얇은 포인터**) | 아니오 |
| `&&String` | **8** | 1 | ptr | 아니오 |
| `Box<str>` | **16** | 2 | ptr · len | **예**(해제한다) |
| `char` | **4** | — | 유니코드 스칼라 값 하나 | 아니오 |

- ★★ **`&String` 이 8이고 `&str` 이 16** 이라는 대비가 이 주제 전체의 그림이다.\
  `&String` 은 **길이를 안 들고 다닌다** — 가리키는 `String` 이 들고 있으니 한 번 더 건너뛰면 된다.\
  `&str` 은 가리키는 곳이 **주인이 아니라 바이트 덩어리**라, 길이를 자기가 들고 다녀야 한다.
- ★ **`&&String` 도 8이다.** 참조를 몇 겹 쌓아도 **참조는 한 워드**다 — 안쪽이 얇으면 바깥도 얇다.\
  반면 `&&str` 도 8이다 — **팻 포인터를 가리키는 얇은 포인터**이기 때문이다.
- `Box<str>` 가 16인 것이 `Box<String>`(8)과 갈린다. **`str` 이 크기 미정 타입**이라 `Box` 가 길이를 같이 든다.
- `Vec<u8>`·`&[u8]` 이 `String`·`&str` 과 **숫자가 똑같다.** `&Vec<T>` 대신 `&[T]` 를 쓰라는 조언이
  `&String` 대신 `&str` 과 **같은 논리**인 이유다 — 실측과 범위 문법은 [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)가 정본이다.

비용 — `size_of` 는 컴파일 타임 상수라 런타임 계산이 없다([**03번 주제**](../03-primitive-types-and-integer-overflow/)에서 쓴 것과 같은 도구다).

### (2) ★★ `String` → `&str` 은 복사가 아니다 — 주소로 증명한다

**언제 쓰나** — 「`&s` 를 넘기면 문자열이 복사되나」가 궁금할 때.

말로 「복사가 아니다」라고 적는 대신 **힙 주소를 직접 찍는다.** 같으면 같은 버퍼다.

```text
===== 소스: ex.rs =====
// String -> &str 이 복사인가 — 힙 주소를 직접 찍어 본다
fn main() {
    let s = String::from("가나다라마");
    let c = s.clone();

    println!("s.as_ptr()            = {:p}", s.as_ptr());
    println!("(&s[..]).as_ptr()     = {:p}", (&s[..]).as_ptr());
    println!("s.as_str().as_ptr()   = {:p}", s.as_str().as_ptr());
    println!("(&*s).as_ptr()        = {:p}", (&*s).as_ptr());
    println!("c.as_ptr()  (clone)   = {:p}", c.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_ptr()            = 0x5cdd3af3ed00
(&s[..]).as_ptr()     = 0x5cdd3af3ed00
s.as_str().as_ptr()   = 0x5cdd3af3ed00
(&*s).as_ptr()        = 0x5cdd3af3ed00
c.as_ptr()  (clone)   = 0x5cdd3af3ed20
(종료 코드 0)
```

★★ **대조할 것은 숫자가 아니라 「같다 / 다르다」라는 성질이다.** 주소 절댓값은 다시 돌리면 달라진다(ASLR·할당기 상태).
위 다섯 줄에서 근거로 읽을 것은 **앞의 넷이 한 값이고 `clone` 만 다른 값**이라는 관계뿐이다.

★ **그래서 같은 실험을 결정적인 출력으로 한 번 더 한다.** 이쪽은 다시 돌려도 한 글자도 안 바뀐다.

```text
===== 소스: ex.rs =====
// 같은 것을 「숫자」가 아니라 「성질」로 찍는다 — 다시 돌려도 출력이 같다
fn main() {
    let s = String::from("가나다라마");
    let c = s.clone();

    assert_eq!(s.as_ptr(), (&s[..]).as_ptr());
    println!("s.as_ptr() == (&s[..]).as_ptr()    : 같다");

    assert_eq!(s.as_ptr(), s.as_str().as_ptr());
    println!("s.as_ptr() == s.as_str().as_ptr()  : 같다");

    assert_eq!(s.as_ptr(), (&*s).as_ptr());
    println!("s.as_ptr() == (&*s).as_ptr()       : 같다");

    assert_ne!(s.as_ptr(), c.as_ptr());
    println!("s.as_ptr() != c.as_ptr()  (clone)  : 다르다");

    // 길이도 같이 본다 — &str 은 주소와 길이 두 칸이다
    println!("s.len() = {} / (&s[..]).len() = {}", s.len(), (&s[..]).len());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_ptr() == (&s[..]).as_ptr()    : 같다
s.as_ptr() == s.as_str().as_ptr()  : 같다
s.as_ptr() == (&*s).as_ptr()       : 같다
s.as_ptr() != c.as_ptr()  (clone)  : 다르다
s.len() = 15 / (&s[..]).len() = 15
(종료 코드 0)
```

- ★ **`assert_eq!` 로 바꾸면 재대조가 기계적으로 통과한다.** 주소를 싣고 싶은 자리에서 쓸 수 있는 수법이다 —\
  「무슨 값이었나」가 아니라 「무슨 관계였나」를 출력으로 굳히는 것이다.
- `&s[..]`·`s.as_str()`·`&*s` **셋 다 같은 것**을 만든다. 표기만 다르다.
- `clone()` 만 **새 힙 버퍼를 할당**한다 — 08번의 「이동은 스택 세 칸만 간다」와 **같은 그림**이다.

**`&str` 이 정말 「주소 + 길이」인지**는 한 `String` 을 두 창이 나눠 보게 해서 확인한다.

```text
===== 소스: ex.rs =====
// &str 은 「주소 + 길이」다 — 한 String 을 두 창이 나눠 본다
fn main() {
    let s = String::from("가나다라");     // 한글 4자 = 12바이트
    let head: &str = &s[..3];             // 첫 글자
    let tail: &str = &s[3..];             // 나머지

    let base = s.as_ptr() as usize;
    println!("s    len={} cap={}", s.len(), s.capacity());
    println!("head 시작 오프셋={} len={} 내용={}", head.as_ptr() as usize - base, head.len(), head);
    println!("tail 시작 오프셋={} len={} 내용={}", tail.as_ptr() as usize - base, tail.len(), tail);
    println!("셋이 같은 힙 버퍼인가: {}", head.as_ptr() == s.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s    len=12 cap=12
head 시작 오프셋=0 len=3 내용=가
tail 시작 오프셋=3 len=9 내용=나다라
셋이 같은 힙 버퍼인가: true
(종료 코드 0)
```

★ **오프셋은 결정적이다** — 주소 자체는 흔들려도 **차이**는 안 흔들린다. 그래서 오프셋으로 찍었다.

```text
   한 힙 버퍼를 두 창이 나눠 본다

   힙:   [ 가 (3) ][ 나 (3) ][ 다 (3) ][ 라 (3) ]     ← base 에서 12바이트
          ^          ^
          |          |
   head:  ptr=base+0  len=3          「가」
   tail:            ptr=base+3  len=9  「나다라」

   ★ 새로 할당된 것은 없다. 창 두 개는 스택에 16바이트씩 놓였을 뿐이다.
   ★ 3 이라는 경계가 왜 「글자 하나」인지 — UTF-8 경계는 15번 주제가 정본이다.
```

### (3) ★★ 인자는 왜 `&str` 로 받나 — 「호출할 수 있는 타입의 수」로 답한다

**언제 쓰나** — 문자열을 받는 함수를 쓸 때마다. **이 절이 이 주제의 결론이다.**

먼저 **`&String` 으로 받으면 무엇을 잃는지** 던져 본다.

```text
===== 소스: ex.rs =====
// 인자를 &String 으로 받으면 — 리터럴을 넘길 수 있나
fn shout(s: &String) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    println!("{}", shout(&owned));   // 이건 된다
    println!("{}", shout("hello"));  // 리터럴은?
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:7:26
  |
7 |     println!("{}", shout("hello"));  // 리터럴은?
  |                    ----- ^^^^^^^ expected `&String`, found `&str`
  |                    |
  |                    arguments to this function are incorrect
  |
  = note: expected reference `&String`
             found reference `&'static str`
note: function defined here
 --> ex.rs:2:4
  |
2 | fn shout(s: &String) -> String { s.to_uppercase() }
  |    ^^^^^ ----------

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

- ★★ **E0308.** 리터럴은 `&str` 이고 `&String` 이 아니다 — **강제는 `String` → `str` 방향으로만 돈다.**\
  없는 `String` 을 만들어 줄 수는 없으니 **반대 방향은 애초에 없다.**
- ★ `= note:` 가 ``found reference `&'static str` `` 이라고 **수명까지 찍어 준다** —\
  리터럴이 `&'static str` 이라는 것이 여기서 드러난다([**07번 주제**](../07-const-static-and-const-fn/)와 잇는다).
- 호출부가 고칠 방법은 **`&String::from("hello")` 를 만드는 것**뿐이다 — **쓸 일 없는 힙 할당**을 강요하는 시그니처다.

**`&str` 로 받으면 무엇이 들어오나** — 전부 던져 본다.

```text
===== 소스: ex.rs =====
// 인자를 &str 로 받으면 — 무엇까지 넘어오나
fn shout(s: &str) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    let boxed: Box<str> = owned.clone().into_boxed_str();

    println!("리터럴      {}", shout("hello"));
    println!("&String     {}", shout(&owned));
    println!("as_str()    {}", shout(owned.as_str()));
    println!("&owned[..]  {}", shout(&owned[..]));
    println!("&*owned     {}", shout(&*owned));
    println!("&Box<str>   {}", shout(&boxed));
    println!("&&String    {}", shout(&&owned));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
리터럴      HELLO
&String     HELLO
as_str()    HELLO
&owned[..]  HELLO
&*owned     HELLO
&Box<str>   HELLO
&&String    HELLO
(종료 코드 0)
```

**`&str` 이라고 아무거나 받는 것은 아니다** — 소유값을 그대로 넘기면 막힌다.

```text
===== 소스: ex.rs =====
// &str 도 전부 받아 주지는 않는다 — 소유값을 그대로 넘기면
fn shout(s: &str) -> String { s.to_uppercase() }

fn main() {
    let owned = String::from("hello");
    println!("{}", shout(owned));
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:6:26
  |
6 |     println!("{}", shout(owned));
  |                    ----- ^^^^^ expected `&str`, found `String`
  |                    |
  |                    arguments to this function are incorrect
  |
note: function defined here
 --> ex.rs:2:4
  |
2 | fn shout(s: &str) -> String { s.to_uppercase() }
  |    ^^^^^ -------
help: consider borrowing here
  |
6 |     println!("{}", shout(&owned));
  |                          +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

★ **`&` 하나를 손으로 붙이는 것까지만 호출부의 일이다.** `help:` 가 그 한 글자를 그대로 준다.

**두 시그니처가 받는 것 — 실측 표**

| 넘긴 것 | `fn f(s: &str)` | `fn f(s: &String)` |
|---|---|---|
| `"리터럴"` | ✓ | ✗ **E0308** |
| `&owned`(`&String`) | ✓ (강제) | ✓ |
| `&&owned`(`&&String`) | ✓ (강제) | ✓ (강제) |
| `owned.as_str()` | ✓ | ✗ |
| `&owned[..]` | ✓ | ✗ |
| `&*owned` | ✓ | ✗ |
| `&boxed`(`&Box<str>`) | ✓ (강제) | ✗ |
| `owned`(`String` 통째로) | ✗ **E0308** (`&` 를 붙이면 된다) | ✗ (〃) |

★★ **`&str` 쪽이 받는 칸이 넓고, `&String` 쪽은 그 부분집합조차 아니다**(리터럴이 빠진다).
**그래서 `&String` 은 「더 구체적이라 더 안전한 것」이 아니라 그냥 호출부를 좁히는 것**이다.

```text
   받는 폭

   fn f(s: &str)      ┌──────────────────────────────────────────┐
                      │ "리터럴" · &String · &&String · &Box<str> │
                      │ as_str() · &s[..] · &*s                  │
                      └──────────────────────────────────────────┘

   fn f(s: &String)                    ┌──────────────────┐
                                       │ &String · &&String│
                                       └──────────────────┘
                      ← 리터럴이 아예 못 들어온다. 넓힌 것이 없다.
```

### (4) ★ 역참조 강제는 전이적이다 — 그리고 어디서 무너지나

**언제 쓰나** — 「참조가 몇 겹이면 안 되나」가 궁금할 때.

먼저 **몇 겹까지 되는지 던져 본다.**

```text
===== 소스: ex.rs =====
// 몇 겹까지 벗기나 — 네 겹을 쌓아 본다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;
    let rrr: &&&String = &rr;
    let rrrr: &&&&String = &rrr;

    println!("&String     -> {}", f(r));
    println!("&&String    -> {}", f(rr));
    println!("&&&String   -> {}", f(rrr));
    println!("&&&&String  -> {}", f(rrrr));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
&String     -> 6
&&String    -> 6
&&&String   -> 6
&&&&String  -> 6
(종료 코드 0)
```

★★ **네 겹도 통과한다.** 「`&&String` 쯤에서 무너지겠지」는 **틀린 예상**이었다 —
**강제는 전이적**이라 `&` 를 쌓는 것으로는 안 깨진다. 컴파일러는 목표 타입이 나올 때까지 `Deref` 를 계속 따라간다.

`as_str()`·`&*s`·`&s[..]` 도 **겹친 참조 위에서 그대로 된다**(메서드 해석도 자동 역참조를 쓴다).

```text
===== 소스: ex.rs =====
// as_str() · &*s · &s[..] 는 각각 어디까지 되나 — 되는 것만 모아 본다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;

    println!("s.as_str()   = {}", f(s.as_str()));
    println!("r.as_str()   = {}", f(r.as_str()));
    println!("rr.as_str()  = {}", f(rr.as_str()));
    println!("&*s          = {}", f(&*s));
    println!("&s[..]       = {}", f(&s[..]));
    println!("&r[..]       = {}", f(&r[..]));
    println!("&rr[..]      = {}", f(&rr[..]));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
s.as_str()   = 6
r.as_str()   = 6
rr.as_str()  = 6
&*s          = 6
&s[..]       = 6
&r[..]       = 6
&rr[..]      = 6
(종료 코드 0)
```

**그럼 무너지는 자리는 어디인가** — ★ **「강제 지점」이 아닌 자리**다.

```text
===== 소스: ex.rs =====
// 강제가 도는 자리와 안 도는 자리 — 인자 자리는 되고 트레이트 경계 자리는 안 된다
fn f(s: &str) -> usize { s.len() }

fn main() {
    let s = String::from("가나");
    let r: &String = &s;
    let rr: &&String = &r;

    println!("인자 자리 f(rr)   = {}", f(rr));   // 강제가 돈다
    println!("주석 자리         = {}", { let a: &str = rr; a });
    println!("비교 r == \"가나\"  = {}", r == "가나");
    println!("비교 rr == \"가나\" = {}", rr == "가나");   // ★ 여기서 무너진다
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: can't compare `&String` with `str`
  --> ex.rs:12:41
   |
12 |     println!("비교 rr == \"가나\" = {}", rr == "가나");   // ★ 여기서 무너진다
   |                                             ^^ no implementation for `&String == str`
   |
   = help: the trait `PartialEq<str>` is not implemented for `&String`
   = note: required for `&&String` to implement `PartialEq<&str>`
help: consider dereferencing here
   |
12 |     println!("비교 rr == \"가나\" = {}", *rr == "가나");   // ★ 여기서 무너진다
   |                                          +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

- ★ **`r == "가나"`(`&String` vs `&str`)는 통과한다.** std 가 `String: PartialEq<str>` 을 구현해 뒀기 때문이다.
- ★★ **`rr`(`&&String`)에서 무너진다.** 여기는 **강제 지점이 아니라 트레이트 구현을 찾는 자리**다 —\
  「`&&String` 이 `PartialEq<&str>` 이려면 `&String: PartialEq<str>` 이 있어야 하는데 없다」고 `= note:` 가 말한다.
- ★ **처방을 컴파일러가 그대로 준다** — `*rr` 로 한 겹 벗기라는 것이다.

**더 중요한 무너짐 — 함수를 「값으로」 넘기는 자리.**

```text
===== 소스: ex.rs =====
// 강제는 「호출 자리」에서만 돈다 — 함수를 값으로 넘기면?
fn takes_str(s: &str) -> usize { s.len() }

fn main() {
    let v = vec![String::from("가나")];
    let n: usize = v.iter().map(takes_str).sum();
    println!("{}", n);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0631]: type mismatch in function arguments
 --> ex.rs:6:33
  |
2 | fn takes_str(s: &str) -> usize { s.len() }
  | ------------------------------ found signature defined here
...
6 |     let n: usize = v.iter().map(takes_str).sum();
  |                             --- ^^^^^^^^^ expected due to this
  |                             |
  |                             required by a bound introduced by this call
  |
  = note: expected function signature `fn(&String) -> _`
             found function signature `fn(&str) -> _`
note: required by a bound in `map`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:773:5
help: consider wrapping the function in a closure
  |
6 |     let n: usize = v.iter().map(|arg0: &String| takes_str(/* &str */)).sum();
  |                                 +++++++++++++++          ++++++++++++

error[E0599]: the method `sum` exists for struct `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>`, but its trait bounds were not satisfied
 --> ex.rs:6:44
  |
6 |     let n: usize = v.iter().map(takes_str).sum();
  |                                            ^^^ method cannot be called due to unsatisfied trait bounds
  |
  = note: the following trait bounds were not satisfied:
          `<for<'a> fn(&'a str) -> usize {takes_str} as FnOnce<(&String,)>>::Output = _`
          which is required by `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          `for<'a> fn(&'a str) -> usize {takes_str}: FnMut<(&String,)>`
          which is required by `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          `Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`
          which is required by `&mut Map<std::slice::Iter<'_, String>, for<'a> fn(&'a str) -> usize {takes_str}>: Iterator`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0599, E0631.
For more information about an error, try `rustc --explain E0599`.
```

- ★★ **`f(x)` 라고 쓰면 그 자리에서 강제가 돌지만, `map(f)` 는 함수를 값으로 넘기는 것**이라 **호출 자리가 없다.**\
  `map` 이 요구하는 것은 `fn(&String) -> _` 인데 내가 준 것은 `fn(&str) -> _` 다.
- ★ **E0599 는 덤으로 따라온 것**이다 — `map` 이 실패했으니 그 결과가 `Iterator` 가 아니고, 그러니 `sum` 도 없다.\
  12번에서 본 「**에러 하나가 다음 에러를 만든다**」와 같은 모양이다. **위에서부터 고친다.**

**처방** — `help:` 가 말한 대로 클로저로 감싸면 그 안이 다시 호출 자리가 된다.

```text
===== 소스: ex.rs =====
// 처방 — 클로저로 감싸면 그 안이 다시 「호출 자리」가 된다
fn takes_str(s: &str) -> usize { s.len() }

fn main() {
    let v = vec![String::from("가나"), String::from("다")];
    let n: usize = v.iter().map(|s| takes_str(s)).sum();
    println!("합계 = {}", n);

    // as_str() 로 미리 &str 을 만들어 줘도 된다
    let m: usize = v.iter().map(String::as_str).map(takes_str).sum();
    println!("합계 = {}", m);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
합계 = 9
합계 = 9
(종료 코드 0)
```

```text
   역참조 강제가 도는 자리 / 안 도는 자리

   돈다    — 함수 「호출」의 인자          f(rr)
   돈다    — 타입 주석이 붙은 let          let a: &str = rr;
   돈다    — 메서드 수신자 자동 역참조     rr.as_str()
   돈다    — 연산자의 피연산자             a + &b   (&String -> &str)
   ─────────────────────────────────────────────────────────────
   안 돈다 — 트레이트 구현을 찾는 자리     rr == "가나"      E0277
   안 돈다 — 함수를 「값으로」 넘기는 자리  map(takes_str)    E0631

   요약: 「무엇을 넣는 자리」에서는 돌고, 「무엇이 무엇인지 판정하는 자리」에서는 안 돈다.
```

★ `impl AsRef<str>`·`impl Into<String>` 으로 인자를 여는 방법이 따로 있다 — 이름만 적어 둔다.
**변환 트레이트 설계는 목록의 29번 주제가 정본**이다.

### (5) `&str` → `String` 다섯 가지 — 어느 트레이트에서 오나

**언제 쓰나** — 문자열을 소유값으로 만들 때. 다섯 표기가 흔히 섞여 쓰인다.

```text
===== 소스: ex.rs =====
// &str -> String 다섯 가지 — 어느 트레이트에서 오나, 결과가 같은가
fn main() {
    let lit = "가나다";

    // 트레이트 이름을 직접 써서 부른다 — 통과하면 그 트레이트가 출처다
    let a: String = ToString::to_string(lit);
    let b: String = ToOwned::to_owned(lit);
    let c: String = Into::into(lit);
    let d: String = From::from(lit);
    let e: String = format!("{}", lit);

    println!("to_string    {:?} len={} cap={}", a, a.len(), a.capacity());
    println!("to_owned     {:?} len={} cap={}", b, b.len(), b.capacity());
    println!("into         {:?} len={} cap={}", c, c.len(), c.capacity());
    println!("String::from {:?} len={} cap={}", d, d.len(), d.capacity());
    println!("format!      {:?} len={} cap={}", e, e.len(), e.capacity());

    println!("다섯이 같은 값인가: {}", a == b && b == c && c == d && d == e);
    println!("힙 주소가 같은가  : {}", a.as_ptr() == b.as_ptr());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
to_string    "가나다" len=9 cap=9
to_owned     "가나다" len=9 cap=9
into         "가나다" len=9 cap=9
String::from "가나다" len=9 cap=9
format!      "가나다" len=9 cap=9
다섯이 같은 값인가: true
힙 주소가 같은가  : false
(종료 코드 0)
```

★ **트레이트 이름을 직접 써서 불러도 전부 통과했다** — 그것이 「어느 트레이트에서 오나」의 실증이다.

| 표기 | 트레이트 | 무엇을 요구하나 | 이 실험에서 |
|---|---|---|---|
| `x.to_string()` | **`ToString`** | `T: Display` 포괄 구현. `str` 도 `Display` 라 여기에 걸린다 | `len=9 cap=9` |
| `x.to_owned()` | **`ToOwned`** | `str` 의 `Owned` 가 `String` 이라고 정해져 있다 | `len=9 cap=9` |
| `x.into()` | **`Into<String>`** | `String: From<&str>` 에서 자동으로 따라온다 | `len=9 cap=9` |
| `String::from(x)` | **`From<&str>`** | 가장 직접적인 표기 | `len=9 cap=9` |
| `format!("{}", x)` | **매크로** | 포매팅 기계(`Display`)를 태운다 | `len=9 cap=9` |

- ★ **결과 값은 다섯이 같고 힙 주소는 전부 다르다.** 다섯 번 **따로 할당**한 것이다 — **변환은 공짜가 아니다.**
- ★★ **「어느 것이 더 느린가」는 안 쟀다.** 이 문서는 시간을 재지 않았으므로 수치를 적지 않는다.\
  다만 **구조상 하는 일이 다르다는 것은 코드로 보인다** — `format!` 만 **포매팅 기계를 통과**하고,\
  나머지 넷은 **길이만큼 바이트를 베끼는 경로**다. 실제 비용 비교는 **벤치로 재야 하고, 여기서는 안 쟀다.**

**다섯이 「같은 물건」은 아니다** — `&str` 이 아닌 것을 던지면 갈린다.

```text
===== 소스: ex.rs =====
// 다섯 변환이 같은 물건이 아니라는 증거 — &str 이 아닌 것을 던져 본다
fn main() {
    let n = 42i32;
    let a: String = n.to_owned();      // ToOwned 는 String 을 안 준다
    let b: String = String::from(n);   // From<i32> for String 이 있나
    println!("{} {}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:4:21
  |
4 |     let a: String = n.to_owned();      // ToOwned 는 String 을 안 준다
  |            ------   ^^^^^^^^^^^^ expected `String`, found `i32`
  |            |
  |            expected due to this
  |
help: try using a conversion method
  |
4 |     let a: String = n.to_owned().to_string();      // ToOwned 는 String 을 안 준다
  |                                 ++++++++++++

error[E0277]: the trait bound `String: From<i32>` is not satisfied
 --> ex.rs:5:21
  |
5 |     let b: String = String::from(n);   // From<i32> for String 이 있나
  |                     ^^^^^^ the trait `From<i32>` is not implemented for `String`
  |
  = help: the following other types implement trait `From<T>`:
            `String` implements `From<&String>`
            `String` implements `From<&mut str>`
            `String` implements `From<&str>`
            `String` implements `From<Box<str>>`
            `String` implements `From<Cow<'_, str>>`
            `String` implements `From<char>`

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0277, E0308.
For more information about an error, try `rustc --explain E0277`.
```

- ★★ **`42i32.to_owned()` 는 `i32` 다** — `ToOwned` 는 「빌린 것을 소유값으로」이고, `i32` 는 이미 소유값이다.\
  **`to_owned()` 가 `String` 을 주는 것은 `&str` 일 때뿐**이다.
- ★ **`String::from(42)` 은 없다.** `= help:` 가 **`String` 이 받는 `From` 구현 목록을 통째로 찍어 준다** —\
  `&String`·`&mut str`·`&str`·`Box<str>`·`Cow<'_, str>`·`char`. **문서를 안 열고도 목록이 나온다.**
- 숫자를 문자열로 만들 때 되는 것은 **`to_string()`**(`Display` 경유)과 `format!` 이다.

### (6) ★ `+` 는 왼쪽을 먹는다

**언제 쓰나** — `a + &b` 를 쓸 때. **한 번 쓰면 `a` 가 사라진다.**

```text
===== 소스: ex.rs =====
// + 는 왼쪽을 소비한다 — 뒤에서 a 를 쓰면?
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + &b;
    println!("c = {}", c);
    println!("a = {}", a);
    println!("b = {}", b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `a`
 --> ex.rs:7:24
  |
3 |     let a = String::from("가나");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = String::from("다라");
5 |     let c = a + &b;
  |             - value moved here
6 |     println!("c = {}", c);
7 |     println!("a = {}", a);
  |                        ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
5 |     let c = a.clone() + &b;
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

★ **08번에서 본 그 E0382 다.** 문자열 전용 규칙이 아니라 **이동 규칙이 `+` 에서 나타난 것**이다.
`+` 가 왼쪽 `String` 의 **힙 버퍼를 물려받아 거기에 이어 붙이기** 때문에 소유가 필요하다.

**오른쪽은 왜 `&str` 인가** — `String` 을 그대로 두면 막힌다.

```text
===== 소스: ex.rs =====
// + 의 오른쪽에 String 을 그대로 두면
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + b;
    println!("{}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: mismatched types
 --> ex.rs:5:17
  |
5 |     let c = a + b;
  |                 ^ expected `&str`, found `String`
  |
help: consider borrowing here
  |
5 |     let c = a + &b;
  |                 +

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

★ **``expected `&str` `` 이 시그니처를 그대로 말해 준다** — `String` 의 `+` 는 오른쪽으로 `&str` 만 받는다.
**오른쪽은 읽기만 하면 되니 소유를 뺏을 이유가 없다.**

**그럼 `&b`(= `&String`)는 왜 통과하나** — (4)의 강제다. 그리고 `format!` 은 아무것도 안 뺏는다.

```text
===== 소스: ex.rs =====
// + 는 오른쪽에 &String 을 받아 준다 — 강제가 돌기 때문이다. 그리고 format! 은 아무것도 안 뺏는다
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");

    let plus = a.clone() + &b;              // &String 이 &str 로 강제된다
    let fmt = format!("{}{}", a, b);        // a·b 를 빌려만 쓴다

    println!("plus   = {}", plus);
    println!("fmt    = {}", fmt);
    println!("a 살아 = {} / b 살아 = {}", a, b);
    println!("같은 값인가 = {}", plus == fmt);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
plus   = 가나다라
fmt    = 가나다라
a 살아 = 가나 / b 살아 = 다라
같은 값인가 = true
(종료 코드 0)
```

★ **강제가 전이적이라 `a + &&b` 도 통과한다** — 오른쪽을 한 겹 더 감싸 따로 던져 봤다.

```text
===== 소스: ex.rs =====
// + 의 오른쪽에 &&String 을 줘도 통과하나 — 강제는 전이적이다
fn main() {
    let a = String::from("가나");
    let b = String::from("다라");
    let c = a + &&b;
    println!("{}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
가나다라
(종료 코드 0)
```

| 표기 | 왼쪽 | 오른쪽 | 뒤에서 원본을 쓸 수 있나 |
|---|---|---|---|
| `a + &b` | **소비**(이동) | `&str`(강제로 `&String` 도) | `a` ✗ · `b` ✓ |
| `format!("{}{}", a, b)` | 빌림 | 빌림 | **둘 다** ✓ |
| `a.push_str(&b)` | `&mut a` | `&str` | `a` ✓(그 자리에서 늘어남) · `b` ✓ |

★ **`+` 를 여러 번 이으면 읽기 힘들어진다**(`a + &b + &c + &d`). **셋 이상이면 `format!` 쪽이 읽힌다.**

### (7) `Copy` 여부가 둘을 가른다 — 타입만 바꿔 던진다

**언제 쓰나** — 「왜 이건 되고 저건 안 되지」 싶을 때. **09번의 판정 기준이 그대로 적용된다.**

```text
===== 소스: ex.rs =====
// 타입만 바꾼 같은 코드 — 한쪽은 거부되고 한쪽은 통과한다
fn main() {
    let a: String = String::from("가나");
    let b = a;
    println!("a={} b={}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0382]: borrow of moved value: `a`
 --> ex.rs:5:27
  |
3 |     let a: String = String::from("가나");
  |         - move occurs because `a` has type `String`, which does not implement the `Copy` trait
4 |     let b = a;
  |             - value moved here
5 |     println!("a={} b={}", a, b);
  |                           ^ value borrowed here after move
  |
  = note: this error originates in the macro `$crate::format_args_nl` which comes from the expansion of the macro `println` (in Nightly builds, run with -Z macro-backtrace for more info)
help: consider cloning the value if the performance cost is acceptable
  |
4 |     let b = a.clone();
  |              ++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

같은 코드에서 **타입만** `&str` 로 바꾼다.

```text
===== 소스: ex.rs =====
// 같은 코드에서 타입만 &str 로 바꾼다
fn main() {
    let a: &str = "가나";
    let b = a;
    println!("a={} b={}", a, b);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a=가나 b=가나
(종료 코드 0)
```

★★ **한 글자 차이로 E0382 와 통과가 갈린다.** 에러가 이유를 직접 말한다 —
``which does not implement the `Copy` trait``. **`&str` 은 불변 참조라 `Copy` 다**(09번의 표).

| | `Copy` 인가 | 대입하면 | 왜 |
|---|---|---|---|
| `String` | **아니오** | **이동**(E0382) | 힙을 소유한다 — 둘이 같은 버퍼를 해제하면 안 된다 |
| `&str` | **예** | 복사 | 불변 참조. 두 칸을 베끼면 끝이고 해제할 것이 없다 |
| `&String` | **예** | 복사 | 〃(한 칸) |
| `&mut String` | **아니오** | 이동 | 가변 참조는 `Copy` 가 아니다(09번) |

### (8) `len()` 은 바이트를 센다 · `capacity()` 는 다른 것이다

**언제 쓰나** — 길이를 쓸 때마다. **한글로 던져야 드러난다.**

```text
===== 소스: ex.rs =====
// len() 은 무엇을 세나 — 한글로 던진다
fn main() {
    let s = String::from("가나다");
    println!("\"가나다\".len()            = {}", s.len());
    println!("\"가나다\".chars().count()  = {}", s.chars().count());
    println!("\"abc\".len()              = {}", "abc".len());
    println!("\"가나다\".is_empty()       = {}", s.is_empty());
    println!("바이트  = {:?}", s.as_bytes());
    println!("size_of::<char>()        = {}", std::mem::size_of::<char>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
"가나다".len()            = 9
"가나다".chars().count()  = 3
"abc".len()              = 3
"가나다".is_empty()       = false
바이트  = [234, 176, 128, 235, 130, 152, 235, 139, 164]
size_of::<char>()        = 4
(종료 코드 0)
```

- ★★ **`len()` 은 UTF-8 바이트 수**다. 한글 한 글자가 3바이트라 `"가나다"` 가 **9**다.
- **`"abc".len()` 은 3** 이라 ASCII 만 쓰면 **틀린 줄도 모르고 지나간다** — 이것이 이 오해가 오래 사는 이유다.
- `chars().count()` 는 **유니코드 스칼라 값**의 개수다. **그것도 「사람이 보는 글자 수」는 아니다** —\
  결합 문자·이모지 때문에 또 갈린다. ★ **`chars()`·`bytes()`·`char_indices()` 와 경계 패닉은
  [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)가 정본**이고, 여기서는 **맛만** 보인다.

**`len()` 과 `capacity()` 는 다른 것이다.**

```text
===== 소스: ex.rs =====
// len 과 capacity 는 다른 것이다 — 세 가지 만드는 법으로 찍어 본다
fn main() {
    let a = String::new();
    let b = String::with_capacity(16);
    let c = String::from("가나다");

    println!("String::new()            len={} cap={}", a.len(), a.capacity());
    println!("String::with_capacity(16) len={} cap={}", b.len(), b.capacity());
    println!("String::from(\"가나다\")    len={} cap={}", c.len(), c.capacity());

    // 용량 안에서 늘리면 용량이 안 바뀐다
    let mut d = String::with_capacity(16);
    d.push_str("abc");
    println!("with_capacity(16) 뒤 push_str(\"abc\") len={} cap={}", d.len(), d.capacity());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
String::new()            len=0 cap=0
String::with_capacity(16) len=0 cap=16
String::from("가나다")    len=9 cap=9
with_capacity(16) 뒤 push_str("abc") len=3 cap=16
(종료 코드 0)
```

- **`len`** — 지금 들어 있는 **바이트 수**. **`capacity`** — 재할당 없이 담을 수 있는 **바이트 수**.
- ★ `String::new()` 는 **힙을 아예 안 잡는다**(`cap=0`). 빈 문자열을 만드는 데 할당이 없다.
- `with_capacity(n)` 은 **미리 잡아 두는 것**이라 `len` 은 그대로 0이다.

**늘려 가며 `capacity` 를 본다** — ★ **이 숫자들은 구현 세부다.**

```text
===== 소스: ex.rs =====
// push_str 로 늘리면 capacity 가 어떻게 변하나 — ★ 이것은 구현 세부다
fn main() {
    let mut s = String::new();
    println!("시작           len={} cap={}", s.len(), s.capacity());
    for i in 0..10 {
        s.push_str("ab");
        println!("push_str {:>2}번째 len={} cap={}", i + 1, s.len(), s.capacity());
    }
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
시작           len=0 cap=0
push_str  1번째 len=2 cap=8
push_str  2번째 len=4 cap=8
push_str  3번째 len=6 cap=8
push_str  4번째 len=8 cap=8
push_str  5번째 len=10 cap=16
push_str  6번째 len=12 cap=16
push_str  7번째 len=14 cap=16
push_str  8번째 len=16 cap=16
push_str  9번째 len=18 cap=32
push_str 10번째 len=20 cap=32
(종료 코드 0)
```

★★ **`0 → 8 → 16 → 32` 는 언어 보장이 아니다.** std 가 약속하는 것은
「**`capacity() >= len()`**」과 「**`with_capacity(n)` 이 최소 `n` 을 확보한다**」 정도이고,
**첫 할당이 8인 것도, 두 배씩 늘어나는 것도 이 판 std 의 구현 세부**다.
★ **이 숫자를 근거로 삼는 코드를 쓰지 마라.** 재할당의 상각 분석은
[`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다.

**`&str` 은 애초에 늘릴 수 없다** — 소유자가 아니기 때문이다.

```text
===== 소스: ex.rs =====
// &str 은 늘릴 수 없다 — 소유자가 아니기 때문이다
fn main() {
    let mut s: &str = "가나";
    s.push_str("다");
    println!("{}", s);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0599]: no method named `push_str` found for reference `&str` in the current scope
 --> ex.rs:4:7
  |
4 |     s.push_str("다");
  |       ^^^^^^^^ method not found in `&str`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
```

★ `mut` 을 붙였는데도 안 된다. **`mut s: &str` 은 「`s` 라는 창을 다른 데로 옮길 수 있다」는 뜻**이지
**「창 너머의 바이트를 고칠 수 있다」가 아니다.**

### (9) 리터럴은 어디에 사나 — `&'static str`

**언제 쓰나** — `"가나"` 를 쓸 때마다. **그 값은 힙에도 스택에도 없다.**

```text
===== 소스: ex.rs =====
// 리터럴은 어디에 사나 — 프로그램이 끝날 때까지 사는 &'static str 이다
const GREET: &str = "안녕";              // 07번: &'static str 로 추론된다

fn literal() -> &'static str { "안녕" }  // 지역이 아니라 바이너리 안의 것을 돌려준다

fn main() {
    let a: &'static str = "안녕";
    let b = literal();

    // 같은 글자의 리터럴 둘이 같은 자리를 가리키나 (★ 구현 세부)
    println!("a 와 b 가 같은 자리 : {}", a.as_ptr() == b.as_ptr());
    println!("a 와 GREET 가 같은 자리 : {}", a.as_ptr() == GREET.as_ptr());

    // String 으로 만들면 힙에 새로 복사된다
    let owned = String::from(a);
    println!("String::from(a) 가 같은 자리 : {}", owned.as_ptr() == a.as_ptr());
    println!("값은 같은가 : {}", owned == a);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a 와 b 가 같은 자리 : true
a 와 GREET 가 같은 자리 : true
String::from(a) 가 같은 자리 : false
값은 같은가 : true
(종료 코드 0)
```

- **리터럴은 바이너리 안에 박혀 있다**(읽기 전용 영역). 그래서 타입이 `&'static str` 이다 —\
  **프로그램이 끝날 때까지 산다**는 뜻이고, `'static` 의 **두 뜻 중 참조 수명 쪽**이다([**12번 주제**](../12-lifetime-annotations-and-elision/)).
- ★ **같은 글자 리터럴 셋이 한 자리를 가리킨 것은 구현 세부다.** rustc 가 합쳐 준 것이고 **언어 보장이 아니다** —\
  「서로 다른 리터럴의 주소가 다르다 / 같다」로 뭘 판정하면 안 된다([**07번 주제**](../07-const-static-and-const-fn/)의 `const` 주소 이야기와 같은 계열).
- ★ **`String::from(a)` 만 새 힙 버퍼다.** 이것이 「`&str` → `String` 이 공짜가 아닌 이유」의 그림이다.

**반대로 지역 `String` 의 창은 함수 밖으로 못 나간다.**

```text
===== 소스: ex.rs =====
// &str 은 남의 바이트를 보는 창이다 — 주인이 죽으면 창도 못 나간다
fn make_view() -> &'static str {
    let s = String::from("가나다");
    &s[..]
}

fn main() { println!("{}", make_view()); }
===== rustc --edition 2021 ex.rs -o ex =====
error[E0515]: cannot return value referencing local variable `s`
 --> ex.rs:4:5
  |
4 |     &s[..]
  |     ^-^^^^
  |     ||
  |     |`s` is borrowed here
  |     returns a value referencing data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

★★ **이 한 쌍이 「왜 대칭이 아닌가」의 답이다.**

```text
   String -> &str                          &str -> String

   힙 버퍼는 이미 있다.                     힙 버퍼가 없다.
   주소와 길이를 「읽어서」                  새로 할당하고 바이트를 「베껴야」
   두 칸을 만들면 끝.                       주인을 만들 수 있다.
   ──────────────────────                  ──────────────────────
   할당 0 · 복사 0                          할당 1 · len 바이트 복사
   as_ptr() 가 같다                         as_ptr() 가 다르다

   ★ 그리고 방향에 따라 「주인이 누구냐」가 갈린다 —
     &str 은 주인이 살아 있는 동안만 유효하다(E0515).
     String 은 자기가 주인이라 어디든 나갈 수 있다.
```

## 문법 — 형태와 규칙

### 형태

```rust
// 1) 만들기
let a: String = String::from("가나");
let b: String = "가나".to_string();
let c: String = "가나".to_owned();
let d: String = "가나".into();
let e: String = format!("{}-{}", "가", "나");
let f: String = String::new();               // 빈 것. 힙 할당 없음
let g: String = String::with_capacity(32);   // 32바이트 미리

// 2) 빌리기 — 셋 다 같은 것을 만든다
let s = String::from("가나");
let v1: &str = &s;          // 역참조 강제
let v2: &str = s.as_str();  // 명시적
let v3: &str = &s[..];      // 범위 문법 (15번)

// 3) 리터럴은 &'static str 이다
let lit: &'static str = "가나";

// 4) 인자는 &str, 반환·필드는 String
fn head(s: &str) -> String { s.chars().take(1).collect() }
struct Row { name: String }

// 5) 늘리기 — 소유자에게만 있다
let mut m = String::new();
m.push_str("가");
m.push('나');
m += "다";                   // += 는 오른쪽이 &str

// 6) 잇기
let x = String::from("가") + "나";              // 왼쪽을 소비한다
let y = format!("{}{}", "가", "나");            // 아무것도 안 뺏는다
```

### 금지 사례 — 던져서 받은 아홉

| 코드 | 에러 | 한 줄 |
|---|---|---|
| `fn f(s: &String)` 에 `"리터럴"` | **E0308** | 강제는 `String`→`str` 한 방향뿐이다 |
| `fn f(s: &str)` 에 `owned`(`String`) | **E0308** | `&` 하나를 붙이면 된다 |
| `String::from(42i32)` | **E0277** | `= help:` 가 `From` 구현 목록을 찍어 준다 |
| `let a: String = 42i32.to_owned();` | **E0308** | `ToOwned` 는 `i32` 를 돌려준다 |
| `let c = a + &b;` 뒤에 `a` | **E0382** | `+` 가 왼쪽을 소비한다 |
| `let c = a + b;` | **E0308** | `+` 의 오른쪽은 `&str` 이다 |
| `let b = a;` 뒤에 `a` (`a: String`) | **E0382** | `String` 은 `Copy` 가 아니다 |
| `(&&String) == "리터럴"` | **E0277** | 트레이트 찾는 자리에는 강제가 없다 |
| `map(takes_str)` 에 `Iter<String>` | **E0631** | 함수를 값으로 넘기면 강제가 없다 |
| `fn f() -> &'static str { &local[..] }` | **E0515** | 창은 주인보다 오래 못 산다 |
| `("가나" as &str).push_str("다")` | **E0599** | `&str` 에는 늘리는 메서드가 없다 |

### 고르는 순서

```text
   문자열을 다루는 자리다
        │
        ▼
   ① 읽기만 하나? ── 예 ──▶ &str 로 받는다. 끝.
        │ 아니오
        ▼
   ② 그 자리에서 고치나(늘리기·비우기)? ── 예 ──▶ &mut String
        │ 아니오
        ▼
   ③ 내가 계속 들고 있어야 하나(필드·반환·컬렉션)? ── 예 ──▶ String
        │ 아니오
        ▼
   ★ &String 이 답인 자리는 사실상 없다.
     (있다면 「이미 &String 만 받는 남의 API 에 그대로 넘겨야 한다」 정도다)
```

## 어디서 틀리나

### 1. ★★ 「`&String` 이 더 구체적이니 더 안전하겠지」

- 실측: `fn f(s: &String)` 은 **리터럴을 아예 못 받는다**(E0308). `&str` 은 `&String` 을 받는다.
- **`&str` 이 받는 칸이 넓고, `&String` 이 그 부분집합**이다 — 좁혀서 얻는 것이 하나도 없다.
- ★ 호출부가 `&String::from("x")` 를 쓰게 만드는 것은 **쓸 필요 없던 힙 할당**을 강요하는 것이다.
- ★ 「`&str` 로 받으면 `String` 을 쪼개 넘기기도 쉽다」는 덤이다 — `&s[..3]` 이 그냥 된다.

### 2. ★★ 「`&str` 은 짧은 문자열, `String` 은 긴 문자열」

- **길이와 아무 상관 없다.** 갈리는 것은 **소유하느냐**다.
- 1기가짜리 `String` 을 통째로 보는 `&str` 도 **16바이트**다(실측: `&str` = 2워드).
- ★ **비슷한 착각** — 「`&str` 은 스택, `String` 은 힙」. `&str` 이 **가리키는 바이트가 힙에 있을 수 있다**\
  (`&s[..]` 가 그렇다). `&str` 자체가 어디 있느냐와 **가리키는 바이트가 어디 있느냐는 다른 질문**이다.

### 3. ★★ 「`String` → `&str` 도 복사겠지」

- 실측: `s.as_ptr()`·`(&s[..]).as_ptr()`·`s.as_str().as_ptr()` 가 **전부 같은 주소**다.
- 복사가 있는 쪽은 **`clone()` 과 `&str` → `String`** 이다(주소가 다르다).
- ★ 그래서 **함수에 `&s` 를 넘기는 것을 아까워할 이유가 없다** — 16바이트를 베끼는 것이다.

### 4. ★ 「`&&String` 은 안 되겠지」

- ★ **틀렸다.** 강제는 **전이적**이라 `&&&&String` 까지 `&str` 자리에 들어간다(실측).
- 무너지는 것은 **겹 수가 아니라 자리**다 — **트레이트 구현을 찾는 자리**(E0277)와\
  **함수를 값으로 넘기는 자리**(E0631)에는 강제가 없다.
- ★ 「`map(takes_str)` 이 안 된다」를 만나면 **클로저로 감싸라** — `help:` 가 그렇게 말한다.

### 5. ★★ 「`s.len()` 은 글자 수」

- **바이트 수**다. `"가나다".len()` 이 **9**다.
- ★ **ASCII 로만 테스트하면 안 걸린다** — `"abc".len()` 은 3이라 맞아 보인다. **한글·이모지로 던져라.**
- `chars().count()` 도 「사람이 보는 글자 수」는 아니다 — 정본은 [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)다.

### 6. ★ `to_string()` 과 `to_owned()` 를 같은 것으로 읽는다

- `&str` 위에서만 결과가 같다. **`42i32.to_owned()` 는 `i32`** 다(실측 E0308).
- `to_string()` 은 **`Display` 가 있으면** 되고, `to_owned()` 는 **`ToOwned` 의 `Owned` 타입**이 정한다.
- ★ 숫자를 문자열로 만들 때 `to_owned()` 를 쓰면 **엉뚱한 타입이 나오고 그제야 에러가 난다.**

### 7. ★ `+` 로 이어 놓고 원본을 다시 쓴다

- **E0382.** `+` 는 왼쪽의 **힙 버퍼를 물려받는다** — 그래서 소유가 필요하다.
- 원본을 살려야 하면 **`format!`** 이나 `a.clone() + &b` 다.
- ★ 루프 안에서 `s = s + &x` 를 돌리면 **매 바퀴 이동이 일어난다** — 그 자리는 `push_str` 이다.

### 8. ★ `capacity()` 의 증가 규칙을 사실로 적는다

- 실측 `0 → 8 → 16 → 32` 는 **이 판 std 의 구현 세부**다. **언어 보장이 아니다.**
- 보장되는 것은 `capacity() >= len()` 과 `with_capacity(n)` 이 최소 `n` 을 잡는다는 것 정도다.

### 9. 지역 `String` 의 `&str` 을 돌려주려 한다

- **E0515.** 창은 주인보다 오래 못 산다.
- 고치는 법은 **`String` 을 돌려주는 것**이다 — 12번의 `make_ref` 와 **같은 처방**이다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 | 근거 |
|---|---|---|
| `String` 이 **ptr·len·cap 세 칸**인 것 | **std 의 문서화된 표현** | `size_of::<String>()` = 24 (8×3) |
| `&str` 이 **팻 포인터**인 것 | **언어**(`str` 은 unsized) | `size_of::<&str>()` = 16 · `&String` = 8 |
| `String: Deref<Target = str>` | **std** | `&*s`·`&s[..]`·`as_str()` 이 같은 주소 |
| **역참조 강제가 전이적**인 것 | **언어** | Reference — Type coercions · `&&&&String` 실측 통과 |
| **강제가 호출 자리에서만 도는 것** | **언어** | `map(takes_str)` → **E0631** |
| `String` → `&str` 에 **할당이 없는 것** | **언어**(`Deref` 의 의미) | `as_ptr()` 동일 |
| `&str` → `String` 이 **할당하는 것** | **std** | `as_ptr()` 상이 · 다섯 변환이 서로도 다른 주소 |
| `String` 이 `Copy` 가 **아닌 것** | **언어**(`Drop` 을 가진 타입) | E0382 `does not implement the Copy trait` |
| `&str` 이 `Copy` 인 것 | **언어**(불변 참조) | 같은 코드가 통과 |
| `len()` 이 **바이트 수**인 것 | **std** | `"가나다".len()` = 9 |
| `+` 가 **왼쪽을 소비**하고 오른쪽이 `&str` 인 것 | **std**(`impl Add<&str> for String`) | E0382 · E0308 `expected &str` |
| 리터럴이 **`&'static str`** 인 것 | **언어** | E0308 의 ``found reference `&'static str` `` |
| 포인터 폭이 **8바이트**인 것 | **플랫폼**(`x86_64`) | `size_of::<usize>()` = 8 — 32비트에서는 달라진다 |
| ★ **`capacity` 증가 수열** `0→8→16→32` | **std 구현 세부** | 판이 바뀌면 달라질 수 있다 |
| ★ **같은 글자 리터럴이 한 자리를 쓰는 것** | **rustc 구현 세부** | 합쳐 준 것이지 보장이 아니다 |
| **주소 절댓값** | **런타임·OS**(ASLR) | 다시 돌리면 달라진다 — 성질만 읽는다 |
| **에러 번호·`help:` 문구** | **rustc 구현** | 번호는 안정적이고 문구는 바뀐다 |
| `= help:` 가 **`From` 구현 목록**을 찍는 것 | **rustc 진단 표기** | 목록 자체는 std 의 사실 |

★ **이 주제에서 「언어 보장」과 「구현 세부」가 가장 헷갈리는 자리는 `capacity`** 다.
숫자가 깔끔하게 두 배씩 늘어나 **규칙처럼 보이기 때문**이다. **보이는 규칙성이 보장의 근거가 아니다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 이유 |
|---|---|---|
| 함수가 문자열을 **읽기만** 한다 | **`&str`** | 리터럴·`&String`·`&Box<str>` 가 전부 들어온다 |
| 함수가 그 자리에서 **늘린다** | **`&mut String`** | `push_str` 은 소유자에게만 있다 |
| 구조체 **필드**에 담는다 | **`String`** | 참조를 담으면 수명 파라미터가 붙는다([**13번 주제**](../13-struct-references-and-static/)) |
| 함수가 **새로 만들어** 돌려준다 | **`String`** | 지역의 창은 못 나간다(E0515) |
| 입력의 **일부를 그대로** 돌려준다 | **`&str`**(수명 표기) | 할당이 없다. 표기는 [**12번 주제**](../12-lifetime-annotations-and-elision/) |
| 고정 문구·설정 키 | **`&'static str`** 또는 `const` | 바이너리 안에 산다([**07번 주제**](../07-const-static-and-const-fn/)) |
| 컬렉션에 담는다(`Vec<_>`·`HashMap` 키) | **`String`** | 원본보다 오래 살아야 한다 |
| 만들어 놓고 **안 바꾼다**, 메모리를 아끼고 싶다 | `Box<str>` | `cap` 한 칸을 안 든다(24 → 16) |
| 두 문자열을 잇는다 | **`format!`** 또는 `push_str` | `+` 는 왼쪽을 먹는다 |
| 인자를 더 넓게 열고 싶다 | `impl AsRef<str>`·`impl Into<String>` | **목록의 29번 주제**가 정본 |
| `&Vec<T>` 로 받고 있다 | **`&[T]`** 로 바꾼다 | `&String`→`&str` 과 **같은 논리** — [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/) |
| `&String` 으로 받고 있다 | ★ **`&str` 로 바꾼다** | 잃는 것이 없고 호출부가 넓어진다 |

판단 규칙 두 줄.

- **읽으면 `&str`, 가지면 `String`.** 이 한 줄로 거의 다 갈린다.
- **`&String` 이 보이면 거의 항상 `&str` 오타다.** 바꿔도 호출부가 안 깨진다(강제가 흡수한다).

## 핵심 문장

- ★★ **`String` 은 주인(ptr·len·cap 3워드), `&str` 은 창(ptr·len 2워드), `&String` 은 주인을 가리키는 쪽지**(1워드)다.
- ★★ **`String` → `&str` 은 복사가 아니다** — `as_ptr()` 가 같다. **`&str` → `String` 은 할당이다** — 주소가 다르다.
- ★★ **인자는 `&str` 로 받는다.** `&String` 으로 받으면 **리터럴이 아예 안 들어온다**(E0308).
- ★ **역참조 강제는 전이적**이라 `&&&&String` 도 `&str` 자리에 들어간다 — 겹 수로는 안 깨진다.
- ★ **강제는 「무엇을 넣는 자리」에서만 돈다.** 트레이트를 찾는 자리(E0277)와 함수를 값으로 넘기는 자리(E0631)에는 없다.
- **`String` 은 `Copy` 가 아니고 `&str` 은 `Copy` 다** — 한 글자 차이로 E0382 와 통과가 갈린다.
- **`+` 는 왼쪽을 소비하고 오른쪽으로 `&str` 을 받는다.** `format!` 은 아무것도 안 뺏는다.
- **`len()` 은 바이트 수**다. `"가나다".len()` 은 9다.
- ★ **`capacity` 의 증가 수열은 구현 세부다** — 규칙처럼 보여도 보장이 아니다.
- **리터럴은 `&'static str`** — 힙도 스택도 아닌 바이너리 안에 산다.

## 관련 자료

- [`../README.md`](../README.md) — Rust 문법·API 주제 목록(이 주제는 14번)
- [**08번 주제**](../08-ownership-and-move/)(소유권과 이동) — ★ **직접 선행**.\
  **그쪽은** 이동 규칙 일반과 「스택 세 칸만 간다」, **여기는** 그 규칙이 **문자열 두 타입**에서 나타나는 모양이다.\
  E0382 의 뿌리가 거기다
- [**09번 주제**](../09-copy-clone-and-drop/)(`Copy`·`Clone`·`Drop`) — ★ **직접 선행**.\
  **그쪽은** 「무엇이 `Copy` 인가」의 판정 규칙, **여기는** 그 판정이 `String`/`&str` 을 가르는 결과다.\
  `clone()` 이 깊은지 얕은지도 거기다
- [**03번 주제**](../03-primitive-types-and-integer-overflow/)(기본 타입·`as` 캐스트) — `size_of` 로 재는 수법과\
  `char` 가 4바이트라는 실측이 거기서 왔다. **그쪽은** 숫자 타입, **여기는** 문자열 두 꼴이다
- [**07번 주제**](../07-const-static-and-const-fn/)(`const`·`static`) — **그쪽은** 「상수가 메모리에서 무엇인가」,\
  **여기는** 「리터럴이 `&'static str` 이라는 것」까지만. `const` 주소가 보장이 아닌 이야기가 거기다
- [**12번 주제**](../12-lifetime-annotations-and-elision/)(수명 표기) — **그쪽은** `&str` 을 **돌려줄 때 수명을 어떻게 적나**,\
  **여기는** `&str` 이 **무엇인가**까지. E0515 의 정본은 그쪽이다
- [**13번 주제**](../13-struct-references-and-static/)(구조체에 참조 담기) — **그쪽은** 필드에 `&'a str` 을 담는 설계,\
  **여기는** 「필드에는 `String`」이라는 기본값까지
- [**15번 주제**](../15-slices-ranges-and-utf8-boundaries/)(슬라이스·범위·UTF-8 경계) — ★ **경계가 가장 붙어 있다.**\
  **그쪽이 정본인 것** — 범위 문법 `&s[a..b]` 의 규칙 · **UTF-8 경계 패닉** · `chars()`/`bytes()`/`char_indices()` ·\
  `&[T]` 슬라이스 일반. **여기가 정본인 것** — `String`/`&str`/`&String` 세 꼴의 **크기·소유·변환**
- [**16번 주제**](../16-structs-impl-and-associated-functions/)(구조체·`impl`) — 필드 타입을 고를 때 이 주제의 판단을 쓴다
- 목록의 **29번 주제**(`From`/`Into`/`AsRef`/`Borrow`) — ★ **`impl AsRef<str>`·`impl Into<String>` 으로 인자를 여는 설계는 거기가 정본**이다.\
  여기서는 **이름만** 언급했다
- 목록의 **43번 주제**(`Deref` 강제와 스마트 포인터) — **그쪽은** `Deref` 라는 장치 자체,\
  **여기는** 그 장치가 `String` → `str` 에서 하는 일까지
- 목록의 **30번 주제**(연산자 오버로딩·`Index`) — `+` 가 왼쪽을 소비하는 **설계 이유**는 거기
- 목록의 **48번 주제**(`format!`·`Display`) — 포매팅 기계의 정본
- [`../../../../../data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — **그쪽은** 용량 증폭의 **상각 분석**,\
  **여기는** `capacity()` 가 `len()` 과 다르다는 것까지
- [`../../../../data-representation/`](../../../../data-representation/) — **그쪽은** UTF-8 **인코딩 자체**, **여기는** 「`len()` 이 바이트다」까지
- [`../../../../memory-management/`](../../../../memory-management/) — 스택·힙 일반론은 거기

## 용어 풀이

- **`String`** — 힙에 UTF-8 바이트를 소유하는 타입. 스택에 ptr·len·cap **세 칸**(24바이트).
- **`str`** — 크기가 고정되지 않은(unsized) 문자열 타입. 항상 포인터 뒤에서 쓴다.
- **`&str`(문자열 슬라이스)** — 주소 + 길이 **두 칸**(16바이트)짜리 팻 포인터. 소유하지 않는다.
- **`&String`** — `String` 을 가리키는 **얇은** 참조 한 칸(8바이트). 힙까지 두 번 건너뛴다.
- **팻 포인터(fat pointer)** — 주소에 메타데이터 한 칸을 더 붙인 포인터. `&str`·`&[T]`·`&dyn Trait`.
- **역참조 강제(deref coercion)** — `&String` 을 `&str` 자리에 넣으면 컴파일러가 바꿔 주는 것. **전이적이다.**
- **강제 지점(coercion site)** — 강제가 도는 자리. 인자·타입 주석·반환 자리 등. **트레이트 찾는 자리는 아니다.**
- **`len()`** — UTF-8 **바이트 수**. 글자 수가 아니다.
- **`capacity()`** — 재할당 없이 담을 수 있는 바이트 수. `len()` 이상이다.
- **`Box<str>`** — 힙을 소유하되 `cap` 을 안 드는 문자열. 다 만들고 안 바꿀 때 한 워드를 아낀다.
- **`&'static str`** — 프로그램이 끝날 때까지 유효한 문자열 슬라이스. 리터럴의 타입이다.

---

## 더 들어가면

- ★ **`str` 이 unsized 라는 것이 모든 것의 출발점이다.** 크기를 모르니 변수에 못 담고,\
  그래서 **포인터가 길이를 들고 다녀야** 한다. `&str` 이 2워드인 것도, `Box<str>` 가 2워드인 것도 거기서 나온다.
- **`Cow<str>`**(clone-on-write)는 「빌린 것일 수도 소유한 것일 수도 있다」를 한 타입에 담는다.\
  `&str` 을 받아 **대부분은 그대로 돌려주고 가끔만 고치는** API 에서 할당을 아낀다.\
  `= help:` 가 찍어 준 `From` 목록에 `Cow<'_, str>` 이 있었던 것이 그 흔적이다.
- ★ **`String` 은 사실 `Vec<u8>` 에 「UTF-8 이다」라는 약속을 씌운 것**이다.\
  `size_of` 가 둘 다 24로 같았던 것이 그 한 면이다. 그 약속을 깨는 길은 `unsafe` 뿐이다(목록의 **56번 주제**).
- **`&mut str`** 이라는 타입도 있다 — 바이트를 **대소문자 변환 같은 길이 보존 연산**으로만 고칠 수 있다.\
  길이를 못 바꾸니 `push_str` 은 여전히 없다.
- ★ **문자열 비교는 바이트 비교다.** `String` 과 `&str` 사이의 `==` 가 되는 것은\
  std 가 **조합마다 `PartialEq` 구현을 따로 써 뒀기** 때문이고, **강제가 해 주는 일이 아니다**((4)의 E0277).\
  그 계약은 목록의 **28번 주제**다.
- ★ **`&str` 인자를 더 열고 싶을 때의 세 단계** — `&str`(기본) → `impl AsRef<str>`(문자열 비슷한 것 전부) →\
  `impl Into<String>`(어차피 소유할 거면). **뒤로 갈수록 호출부가 넓어지고 코드 크기가 늘어난다**(단형화).\
  판단은 목록의 **29번 주제**·**31번 주제**다.
