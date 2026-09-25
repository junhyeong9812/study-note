# rust/syntax/25 — 트레이트 정의·구현·기본 메서드·연관 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Reference — Traits](https://doc.rust-lang.org/reference/items/traits.html) ·
> [Reference — dyn compatibility](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility) ·
> [Reference — `impl Trait`](https://doc.rust-lang.org/reference/types/impl-trait.html) ·
> [std — `trait Iterator`](https://doc.rust-lang.org/std/iter/trait.Iterator.html).
> ★ `rustc --explain E0038` · `E0119` · `E0283` · `E0308` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — 트레이트·연관 타입·기본 메서드는 **1.0.0**, 인자 자리 `impl Trait` 는 **1.26.0**,
> 반환 자리 `impl Trait` 도 **1.26.0** 부터다. **전부 에디션과 무관하다.**\
> ★ **이 판의 말버릇** — rustc 는 **1.83 부터 「object safe」를 「dyn compatible」로 바꿔 부른다.**
> 그래서 아래 E0038 전문에는 「객체 안전성」이라는 말이 **한 번도 안 나온다**((5)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 OS 스레드 id | 이 주제에는 패닉 블록이 없지만 규칙은 같다 |
| **흔들린다** | `0x…` 주소 | 실행마다 다르다 |
| 안 흔들린다 | **종료 코드 0 · 1** | 컴파일 실패는 1 이다 |
| 안 흔들린다 | 에러 번호·제목·`= note:`·`help:` 줄·`파일:줄:칸` | 같은 rustc 판에서 고정이다 |
| 안 흔들린다 | 기본 메서드가 **누구 것을 부르는지**(출력 문장) | 이 주제의 핵심 근거다 |
| 안 흔들린다 | `&dyn Greet` 가 **16바이트**인 것 | ★ 같은 판·같은 타깃에서 고정이다. **언어 보장은 아니다**(§구현 세부) |

## 한눈에 — 쉽게 말하면

**트레이트는 「이 타입은 이런 일을 할 줄 안다」를 이름 붙여 적어 둔 계약서다.**

| 비유 | 실체 |
|---|---|
| 「**자격증에 적힌 필수 과목**」 | **몸통 없는 메서드** — 구현체가 반드시 채운다((1)) |
| 「**면제 과목 — 안 들으면 표준 교재로 친다**」 | ★ **기본 메서드** — 안 채우면 트레이트에 적힌 것이 쓰인다((1)·(2)) |
| 「**표준 교재가 인용하는 필수 과목 노트**」 | ★★ 기본 메서드가 **덮어쓴 메서드를 부른다** — 그래서 덮으면 기본 메서드의 답도 바뀐다((1)) |
| 「**자격증마다 따로 정하는 전공 분야**」 | ★ **연관 타입** — 구현이 하나 고르면 끝((4)) |
| 「**한 사람이 여러 전공으로 딸 수 있는 자격증**」 | ★ **제네릭 파라미터** — 한 타입에 여러 번 구현된다((3)) |
| 「**자격증만 보고 사람은 안 보는 창구**」 | **`dyn Trait`** — 동적 디스패치. 대신 **창구에 못 들어가는 자격증**이 있다((5)) |
| 「**서류에 이름은 안 적고 자격만 적기**」 | **`impl Trait`** — 타입 하나를 감춘다. **갈래는 못 감춘다**((6)) |

- ★★★ **갈림길은 하나다 — 「한 타입이 이 트레이트를 여러 번 구현할 수 있어야 하나?」**
  그래야 하면 **제네릭 파라미터**, 아니면 **연관 타입**. (3)·(4)가 같은 문제를 둘 다로 써서 갈라 보인다.
- ★★ **기본 메서드는 「구현체가 안 덮으면」 쓰인다** — 정적 디스패치든 동적 디스패치든 **같은 규칙**이다((1)·(2)).
- ★ **`dyn` 이 되는 트레이트와 안 되는 트레이트가 있다.** `Self` 를 돌려주거나 제네릭 메서드가 있으면 안 된다((5)).

```text
   트레이트 하나를 쪼개 보면

   ┌────────────────────────────────────────────────┐
   │  trait Greet                                   │
   │   ├─ fn name(&self) -> String;      ← 필수     │  구현체가 반드시 채운다
   │   ├─ fn hello(&self) -> String {…}  ← 기본     │  안 채우면 이게 쓰인다
   │   └─ fn shout(&self) -> String {…}  ← 기본     │  본문에서 self.hello() 를 부른다
   └────────────────────────────────────────────────┘
                 │                        │
        impl Greet for Cat       impl Greet for Dog
          name 만 채움             name + hello 를 채움
                 │                        │
                 ▼                        ▼
        hello  = 트레이트의 것      hello  = Dog 의 것
        shout  = 트레이트의 것      shout  = 트레이트의 것
                 │                        │
                 └── 같은 코드인데 ────────┘
                     shout 의 답이 다르다 — 안에서 부른 hello 가 다르기 때문


   한 타입에 몇 번 구현되나 — 이것이 두 도구를 가른다

   제네릭 파라미터                        연관 타입
   trait Extract<T>                      trait Extract { type Out; }

   impl Extract<u32>    for Ticket  ✔    impl Extract for Ticket { type Out = u32; }    ✔
   impl Extract<String> for Ticket  ✔    impl Extract for Ticket { type Out = String; } ✘ E0119
        └ 한 타입에 여러 번 된다              └ 한 타입에 한 번뿐이다

   대가                                  값
   호출부가 타입을 적어야 한다 (E0283)    호출부가 아무것도 안 적어도 된다
```

> **트레이트(trait)** — 「이 타입이 무엇을 할 줄 아는가」를 메서드 묶음으로 적어 둔 계약.\
> 예: `Iterator` 를 구현했다는 것은 `next()` 를 부를 수 있다는 뜻이다.

> **기본 메서드(default method)** — 트레이트 안에 **몸통까지** 적어 둔 메서드.\
> 구현체가 같은 이름을 쓰면 그쪽이 이기고, 안 쓰면 트레이트의 것이 쓰인다.

> **연관 타입(associated type)** — 트레이트 안에 자리만 만들어 두고 **구현이 채우는 타입**.\
> 예: `Iterator::Item` — `Vec<u8>` 의 이터레이터는 그 자리를 `&u8` 로 채운다.

> **정적 디스패치 / 동적 디스패치** — 어느 함수를 부를지 **컴파일 때 정하느냐 실행 때 정하느냐**.\
> 예: `fn f<T: Greet>(x: &T)` 는 타입마다 따로 찍히고, `fn f(x: &dyn Greet)` 는 한 벌로 찍혀 표를 보고 고른다.

## 이 주제가 답하려는 질문

1. **기본 메서드는 어디로 가나** — 구현체가 안 덮으면 무엇이 쓰이고, 덮으면 무엇까지 바뀌나((1)·(2)).
2. ★★ **연관 타입과 제네릭 파라미터는 무엇이 갈리나** — 같은 문제를 둘 다로 써 보면 「**한 타입에 몇 번**」에서 갈린다((3)·(4)).
3. **어떤 트레이트가 `dyn` 이 되나** — 그리고 `impl Trait` 는 그 자리를 얼마나 대신하나((5)·(6)).

★ [**16번 주제**](../16-structs-impl-and-associated-functions/)가 「한 타입에 메서드를 붙이는 법」이었다면,
여기는 「**여러 타입에 같은 이름의 능력을 붙이고 그것으로 추상화하는 법**」이다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| **덮은 쪽과 안 덮은 쪽을 나란히 찍기** | 기본 메서드가 **어디로 가나** | 기본 창 |
| ★★ **같은 트레이트를 정적·동적 둘로 던지기** | 규칙이 디스패치 방식에 **안 달렸다**는 것 | ★ 이 주제의 고유 창 |
| ★★★ **같은 문제를 두 도구로 다 써 보기** | 연관 타입과 제네릭 파라미터가 **어디서 갈리나** | ★ 이 주제의 고유 창 |
| ★ **컴파일러에게 `dyn` 을 시켜 보기** | 객체 안전성은 **에러 전문이 정의다** | [**11번 주제**](../11-borrow-checker-rejections/)의 방식 |

★★★ 셋째 창이 본체다. 두 도구를 **말로 비교하면** 「연관 타입은 출력 타입에 쓴다」 같은 외운 문장이 남는데,
**같은 문제에 둘 다 써 보면** 갈리는 자리가 **E0119 와 E0283 딱 두 에러**로 드러난다((3)·(4)).

### (1) 트레이트 정의·구현·기본 메서드 — 덮으면 어디까지 바뀌나

**언제 쓰나** — 여러 타입에 같은 이름의 능력을 붙이고, 그중 **대부분이 같게 동작해도 되는** 메서드가 있을 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 트레이트 정의·구현·기본 메서드 — 구현체가 안 덮으면 트레이트의 것이 쓰인다 (정적 디스패치)
trait Greet {
    fn name(&self) -> String;                  // 필수 — 구현체가 반드시 채운다

    fn hello(&self) -> String {                // 기본 메서드 — 안 채워도 된다
        format!("안녕, {} 입니다", self.name())
    }

    fn shout(&self) -> String {                // 기본 메서드가 다른 기본 메서드를 부른다
        format!("{}!!!", self.hello())
    }
}

struct Cat;
struct Dog;

impl Greet for Cat {
    fn name(&self) -> String {
        String::from("고양이")
    }
}

impl Greet for Dog {
    fn name(&self) -> String {
        String::from("개")
    }
    fn hello(&self) -> String {                // hello 만 덮어쓴다. shout 은 안 덮는다
        String::from("멍")
    }
}

fn call_static<T: Greet>(x: &T) {              // 정적 디스패치 — 타입마다 따로 찍힌다
    println!("  name  {}", x.name());
    println!("  hello {}", x.hello());
    println!("  shout {}", x.shout());
}

fn main() {
    println!("Cat — 아무것도 안 덮었다");
    call_static(&Cat);
    println!("Dog — hello 만 덮었다");
    call_static(&Dog);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Cat — 아무것도 안 덮었다
  name  고양이
  hello 안녕, 고양이 입니다
  shout 안녕, 고양이 입니다!!!
Dog — hello 만 덮었다
  name  개
  hello 멍
  shout 멍!!!
(종료 코드 0)
```

- **필수 메서드**(`name`)는 두 구현이 모두 채웠다. 안 채우면 컴파일이 거부한다.
- **기본 메서드**(`hello`·`shout`)는 `Cat` 이 하나도 안 채웠는데 **그대로 쓰였다** —
  `안녕, 고양이 입니다` 는 트레이트에 적힌 몸통이 만든 문장이다.
- ★★★ **`Dog` 은 `hello` 만 덮었는데 `shout` 의 답까지 바뀌었다** — `멍!!!`.
  `shout` 의 몸통은 **트레이트의 것 그대로**인데, 그 안에서 부른 `self.hello()` 가 `Dog` 의 것이기 때문이다.
  **기본 메서드는 「고정된 답」이 아니라 「구현체를 되부르는 뼈대」다.**
- ★ 그래서 트레이트를 설계할 때 **필수 메서드를 적게 두고 기본 메서드로 넓히는** 꼴이 표준이다.
  `Iterator` 가 `next()` 하나만 요구하고 나머지 수십 개를 기본 메서드로 주는 것이 그 극단이다(목록의 **36번 주제**).

### (2) ★★ 기본 메서드가 어디로 가나 — 동적 디스패치에서도 같다

**언제 쓰나** — 서로 다른 타입을 **한 `Vec` 에 담아** 돌려야 할 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 같은 트레이트를 동적 디스패치로 — 기본 메서드도 같은 자리로 간다
trait Greet {
    fn name(&self) -> String;

    fn hello(&self) -> String {
        format!("안녕, {} 입니다", self.name())
    }

    fn shout(&self) -> String {
        format!("{}!!!", self.hello())
    }
}

struct Cat;
struct Dog;

impl Greet for Cat {
    fn name(&self) -> String {
        String::from("고양이")
    }
}

impl Greet for Dog {
    fn name(&self) -> String {
        String::from("개")
    }
    fn hello(&self) -> String {
        String::from("멍")
    }
}

fn call_dyn(x: &dyn Greet) {                   // 동적 디스패치 — 함수는 한 벌뿐이다
    println!("  hello {}", x.hello());
    println!("  shout {}", x.shout());
}

fn main() {
    let zoo: Vec<Box<dyn Greet>> = vec![Box::new(Cat), Box::new(Dog)];
    for g in &zoo {
        println!("{} (dyn)", g.name());
        call_dyn(g.as_ref());
    }
    println!("포인터 폭");
    println!("  &Cat        {} 바이트", std::mem::size_of::<&Cat>());
    println!("  &dyn Greet  {} 바이트", std::mem::size_of::<&dyn Greet>());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
고양이 (dyn)
  hello 안녕, 고양이 입니다
  shout 안녕, 고양이 입니다!!!
개 (dyn)
  hello 멍
  shout 멍!!!
포인터 폭
  &Cat        8 바이트
  &dyn Greet  16 바이트
(종료 코드 0)
```

- ★★ **(1)과 한 글자도 같은 답이 나왔다.** `Cat` 은 트레이트의 `hello`, `Dog` 은 자기 `hello`,
  둘 다 `shout` 은 트레이트의 것 — **디스패치 방식이 규칙을 바꾸지 않는다.**
- ★ 다른 것은 **어디서 정해지느냐**다. `call_static` 은 타입마다 따로 찍히고(단형화),
  `call_dyn` 은 **함수가 한 벌**이고 실행 때 표를 보고 고른다.
- ★★ **포인터 폭이 그 표의 증거다** — `&Cat` 은 8바이트인데 `&dyn Greet` 는 **16바이트**다.
  뒤엣것은 「값의 주소 + 메서드 표(vtable)의 주소」 둘을 들고 다닌다.
  ★ 이 수치는 **이 판·이 타깃의 관찰**이지 언어 보장이 아니다(§구현 세부).
- ★ 기본 메서드도 **표에 한 칸을 차지한다** — 안 덮었으면 트레이트의 몸통을 가리키는 칸이 들어갈 뿐이다.
  그래서 `dyn` 에서도 덮어쓰기가 그대로 먹는다. 정본은 목록의 **33번 주제**다.

```text
   같은 트레이트, 두 가지 부르는 법

   정적 (fn f<T: Greet>(x: &T))          동적 (fn f(x: &dyn Greet))

   f::<Cat> ─▶ Cat::name                 x ─▶ [값 주소 | 표 주소]
   f::<Dog> ─▶ Dog::name                              │
     └ 함수가 타입 수만큼 찍힌다                       ▼
       부를 곳이 컴파일 때 박힌다          표: [name | hello | shout]
                                          Cat 의 표 → [Cat::name | 트레이트 hello | 트레이트 shout]
                                          Dog 의 표 → [Dog::name | Dog::hello   | 트레이트 shout]
                                            └ 함수는 한 벌. 실행 때 칸을 읽는다
```

### (3) 같은 문제를 제네릭 파라미터로 — 한 타입에 여러 번

**언제 쓰나** — 「이 타입에서 **여러 종류**를 꺼낼 수 있어야 한다」가 요구사항일 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 제네릭 파라미터 판 — 한 타입에 여러 번 구현된다. 대신 호출부가 타입을 적어야 한다
trait Extract<T> {
    fn extract(&self) -> T;
}

struct Ticket;

impl Extract<u32> for Ticket {
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract<String> for Ticket {
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    let a: u32 = t.extract();                  // 받는 쪽 타입으로 고른다
    let b: String = t.extract();
    let c = Extract::<u32>::extract(&t);       // 또는 터보피시로 찍어 고른다
    println!("u32    {}", a);
    println!("String {}", b);
    println!("찍어서 {}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
u32    7
String 칠
찍어서 7
(종료 코드 0)
```

- **한 타입 `Ticket` 에 같은 트레이트가 두 번 구현됐다** — `Extract<u32>` 와 `Extract<String>` 은 **서로 다른 트레이트**다.
- ★ 대가는 **호출부가 어느 쪽인지 적어야 한다**는 것이다. 받는 쪽 타입(`let a: u32`)으로 고르거나
  터보피시(`Extract::<u32>::extract(&t)`)로 찍는다.
- **안 적으면 어떻게 되나** — 다음 블록이 답이다.

```text
===== 소스: ex.rs =====
// ex.rs
// 제네릭 파라미터 판 — 타입을 안 적으면 무엇을 고를지 못 정한다
trait Extract<T> {
    fn extract(&self) -> T;
}

struct Ticket;

impl Extract<u32> for Ticket {
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract<String> for Ticket {
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    let c = t.extract();
    println!("{:?}", c);
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0283]: type annotations needed
  --> ex.rs:23:9
   |
23 |     let c = t.extract();
   |         ^     ------- type must be known at this point
   |
note: multiple `impl`s satisfying `Ticket: Extract<_>` found
  --> ex.rs:9:1
   |
 9 | impl Extract<u32> for Ticket {
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
...
15 | impl Extract<String> for Ticket {
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
help: consider giving `c` an explicit type
   |
23 |     let c: /* Type */ = t.extract();
   |          ++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0283`.
(종료 코드 1)
```

- ★★ **E0283** — `` type annotations needed ``. 진단이 `` multiple `impl`s satisfying `Ticket: Extract<_>` found `` 로
  **후보 두 개를 그 자리에서 짚어 준다.**
- ★ 이것이 제네릭 파라미터의 **고정 비용**이다. 구현이 하나뿐일 때도 **컴파일러는 「하나뿐인지」를 근거로 삼지 않는다.**
  (실제로 구현이 하나면 추론이 되지만, 나중에 하나가 더 생기는 순간 **호출부 전부가 깨진다.**)

### (4) ★★★ 같은 문제를 연관 타입으로 — 한 타입에 한 번

```text
===== 소스: ex.rs =====
// ex.rs
// 연관 타입 판 — 구현이 하나뿐이라 호출부가 타입을 안 적어도 된다
trait Extract {
    type Out;                                  // 구현이 「정해 주는」 타입
    fn extract(&self) -> Self::Out;
}

struct Ticket;

impl Extract for Ticket {
    type Out = u32;
    fn extract(&self) -> u32 {
        7
    }
}

fn twice<E: Extract>(e: &E) -> (E::Out, E::Out) {   // 파라미터가 하나뿐이다
    (e.extract(), e.extract())
}

fn main() {
    let t = Ticket;
    let c = t.extract();                       // 타입 주석이 필요 없다
    println!("주석 없이  {}", c);
    println!("두 번      {:?}", twice(&t));

    // std 가 쓰는 자리 — Iterator::Item 이 그 연관 타입이다
    let v = vec![10u8, 20, 30];
    let mut it = v.iter();
    println!("Iterator::Item {:?} {:?}", it.next(), it.next());
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
주석 없이  7
두 번      (7, 7)
Iterator::Item Some(10) Some(20)
(종료 코드 0)
```

- ★★ **타입 주석이 하나도 없다.** `let c = t.extract();` 가 그냥 통과한다 —
  `Ticket` 의 `Out` 은 **하나로 정해져 있어서** 추론할 것이 없다.
- ★ 제네릭 함수 쪽도 가볍다 — `fn twice<E: Extract>(e: &E) -> (E::Out, E::Out)` 는
  **타입 파라미터가 하나뿐**이다. 제네릭 파라미터 판이었으면 `<E, T>` 두 개를 끌고 다녀야 한다.
- **std 가 이 도구를 쓰는 대표 자리가 `Iterator::Item`** 이다 — `v.iter()` 의 `Item` 은 `&u8` 로 이미 정해져 있어
  `it.next()` 가 `Some(10)` 을 돌려주는 데 아무 주석이 필요 없다.

**그럼 두 번 구현하면?**

```text
===== 소스: ex.rs =====
// ex.rs
// 연관 타입 판 — 같은 타입에 두 번 구현하면
trait Extract {
    type Out;
    fn extract(&self) -> Self::Out;
}

struct Ticket;

impl Extract for Ticket {
    type Out = u32;
    fn extract(&self) -> u32 {
        7
    }
}

impl Extract for Ticket {
    type Out = String;
    fn extract(&self) -> String {
        String::from("칠")
    }
}

fn main() {
    let t = Ticket;
    println!("{}", t.extract());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0119]: conflicting implementations of trait `Extract` for type `Ticket`
  --> ex.rs:17:1
   |
10 | impl Extract for Ticket {
   | ----------------------- first implementation here
...
17 | impl Extract for Ticket {
   | ^^^^^^^^^^^^^^^^^^^^^^^ conflicting implementation for `Ticket`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0119`.
(종료 코드 1)
```

- ★★★ **E0119 — `` conflicting implementations of trait `Extract` for type `Ticket` ``.**
  연관 타입은 트레이트 이름의 일부가 **아니다.** `type Out = u32` 와 `type Out = String` 은
  **같은 트레이트의 두 구현**이라 충돌한다.
- ★ 이 한 줄이 두 도구의 갈림길 전부다 — **제네릭 파라미터는 트레이트 이름을 갈라 주고, 연관 타입은 안 갈라 준다.**

```text
   「한 타입에 몇 번 구현되나」가 두 도구를 가른다

   Extract<u32>    ≠ Extract<String>      ← 이름이 다르다. 둘 다 된다
        │                  │
        └── Ticket ────────┘              호출부: 타입을 적어야 한다 (E0283)

   Extract                                ← 이름이 하나뿐이다
        │
        └── Ticket  (type Out = u32)      호출부: 아무것도 안 적어도 된다
                     두 번째 impl → E0119
```

### (5) ★★ 객체 안전성 — `dyn` 이 될 수 없는 트레이트

**언제 쓰나** — 트레이트를 `Box<dyn …>` 에 담으려는데 거부당할 때.

```text
===== 소스: ex.rs =====
// ex.rs
// 객체 안전성 — dyn 이 될 수 없는 트레이트를 dyn 으로 만들어 본다
trait Spawner {
    fn new_one() -> Self;                      // ① Self 를 돌려준다
    fn tag(&self) -> u8;
    fn feed<T>(&self, item: T);                // ② 제네릭 메서드
}

struct Bee;

impl Spawner for Bee {
    fn new_one() -> Self {
        Bee
    }
    fn tag(&self) -> u8 {
        7
    }
    fn feed<T>(&self, _item: T) {}
}

fn main() {
    let b: Box<dyn Spawner> = Box::new(Bee);
    println!("{}", b.tag());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0038]: the trait `Spawner` is not dyn compatible
  --> ex.rs:22:20
   |
22 |     let b: Box<dyn Spawner> = Box::new(Bee);
   |                    ^^^^^^^ `Spawner` is not dyn compatible
   |
note: for a trait to be dyn compatible it needs to allow building a vtable
      for more information, visit <https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility>
  --> ex.rs:4:8
   |
 3 | trait Spawner {
   |       ------- this trait is not dyn compatible...
 4 |     fn new_one() -> Self;                      // ① Self 를 돌려준다
   |        ^^^^^^^ ...because associated function `new_one` has no `self` parameter
 5 |     fn tag(&self) -> u8;
 6 |     fn feed<T>(&self, item: T);                // ② 제네릭 메서드
   |        ^^^^ ...because method `feed` has generic type parameters
   = help: consider moving `feed` to another trait
   = help: only type `Bee` implements `Spawner`; consider using it directly instead.
help: consider turning `new_one` into a method by giving it a `&self` argument
   |
 4 |     fn new_one(&self) -> Self;                      // ① Self 를 돌려준다
   |                +++++
help: alternatively, consider constraining `new_one` so it does not apply to trait objects
   |
 4 |     fn new_one() -> Self where Self: Sized;                      // ① Self 를 돌려준다
   |                          +++++++++++++++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0038`.
(종료 코드 1)
```

- ★★★ **에러 전문이 곧 정의다.** 진단이 두 이유를 **각각 그 줄을 짚어** 말한다 —
  `` ...because associated function `new_one` has no `self` parameter `` 와
  `` ...because method `feed` has generic type parameters ``.
- ★ **`self` 가 없는 연관 함수**가 왜 막히나 — `dyn Spawner` 는 **어느 구체 타입인지 모르는 값**이다.
  `Spawner::new_one()` 은 받을 값도 없이 「무엇을」 만들지 정할 수가 없다.
- ★ **제네릭 메서드**가 왜 막히나 — `feed::<u8>`·`feed::<String>` … **무한히 많은 칸**이 필요해 표를 못 만든다.
- ★★ **`help:` 두 개가 고치는 법을 준다** — `&self` 를 붙여 메서드로 만들거나,
  `where Self: Sized` 를 달아 **그 메서드만 트레이트 객체에서 빼는 것**이다.
- ★★ **말버릇이 바뀌었다** — 이 진단에는 「object safe」가 한 번도 안 나오고 **`dyn compatible`** 만 나온다.
  rustc **1.83** 에서 용어를 바꿨다. 한국어 문서·책은 아직 「객체 안전성」이라고 쓰므로 **같은 것임을 알아 둬야** 한다.

### (6) `impl Trait` — 인자 자리와 반환 자리

```text
===== 소스: ex.rs =====
// ex.rs
// impl Trait — 인자 자리와 반환 자리
trait Shape {
    fn area(&self) -> f64;
    fn kind(&self) -> &'static str {
        "도형"
    }
}

struct Square(f64);
struct Circle(f64);

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
    fn kind(&self) -> &'static str {
        "정사각형"
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}

fn show(s: impl Shape) {                       // 인자 자리 — <T: Shape> 의 설탕
    println!("  {} 넓이 {}", s.kind(), s.area());
}

fn make(big: bool) -> impl Shape {             // 반환 자리 — 타입 하나를 감춘다
    if big {
        Square(3.0)
    } else {
        Square(1.0)
    }
}

fn main() {
    println!("인자 자리");
    show(Square(2.0));
    show(Circle(1.0));
    println!("반환 자리");
    show(make(true));
    show(make(false));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
인자 자리
  정사각형 넓이 4
  도형 넓이 3
반환 자리
  정사각형 넓이 9
  정사각형 넓이 1
(종료 코드 0)
```

- **인자 자리** `fn show(s: impl Shape)` 는 `fn show<T: Shape>(s: T)` 의 설탕이다. 정적 디스패치다.
- **반환 자리** `fn make(big: bool) -> impl Shape` 는 **구체 타입 하나를 감춘다** —
  호출자는 `Shape` 라는 것만 알고 `Square` 라는 것은 모른다.
- `Circle` 이 `kind()` 를 안 덮어서 `도형` 이 찍힌 것에 주의 — (1)의 규칙이 여기서도 그대로다.

**반환 자리에 갈래를 넣으면?**

```text
===== 소스: ex.rs =====
// ex.rs
// 반환 자리 impl Trait — 두 갈래를 돌려주려 하면
trait Shape {
    fn area(&self) -> f64;
}

struct Square(f64);
struct Circle(f64);

impl Shape for Square {
    fn area(&self) -> f64 {
        self.0 * self.0
    }
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        3.0 * self.0 * self.0
    }
}

fn make(big: bool) -> impl Shape {
    if big {
        Square(3.0)
    } else {
        Circle(1.0)
    }
}

fn main() {
    println!("{}", make(true).area());
}
===== rustc --edition 2021 ex.rs -o ex =====
error[E0308]: `if` and `else` have incompatible types
  --> ex.rs:26:9
   |
23 | /     if big {
24 | |         Square(3.0)
   | |         ----------- expected because of this
25 | |     } else {
26 | |         Circle(1.0)
   | |         ^^^^^^^^^^^ expected `Square`, found `Circle`
27 | |     }
   | |_____- `if` and `else` have incompatible types
   |
help: you could change the return type to be a boxed trait object
   |
22 - fn make(big: bool) -> impl Shape {
22 + fn make(big: bool) -> Box<dyn Shape> {
   |
help: if you change the return type to expect trait objects, box the returned expressions
   |
24 ~         Box::new(Square(3.0))
25 |     } else {
26 ~         Box::new(Circle(1.0))
   |

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
(종료 코드 1)
```

- ★★ **E0308** — `` `if` and `else` have incompatible types ``.
  **반환 자리 `impl Trait` 는 「타입을 감추는 것」이지 「여러 타입을 받는 것」이 아니다.**
  감춘 그 자리에는 **컴파일 때 정해지는 타입 하나**가 들어간다.
- ★ `help:` 가 곧바로 답을 준다 — `Box<dyn Shape>` 로 바꾸고 양쪽을 `Box::new(…)` 로 감싸라.
  **갈래가 필요하면 그때가 `dyn` 을 쓸 때다.**

### (7) 트레이트에서 `Self` 가 오는 자리

```text
===== 소스: ex.rs =====
// ex.rs
// 트레이트에서 Self 가 오는 자리 — 연관 상수·인자·반환·기본 메서드
trait Unit: Sized + Copy + PartialEq {
    const ZERO: Self;                          // ① 연관 상수의 타입

    fn add(self, other: Self) -> Self;         // ② 인자와 반환

    fn double(self) -> Self {                  // ③ 기본 메서드가 Self 를 돌려준다
        self.add(self)
    }

    fn is_zero(&self) -> bool {                // ④ 기본 메서드가 연관 상수를 읽는다
        *self == Self::ZERO
    }

    fn sum(items: &[Self]) -> Self {           // ⑤ self 가 없는 연관 함수(기본 구현)
        let mut acc = Self::ZERO;
        for it in items {
            acc = acc.add(*it);
        }
        acc
    }
}

#[derive(Clone, Copy, PartialEq, Debug)]
struct Won(i64);

impl Unit for Won {
    const ZERO: Self = Won(0);
    fn add(self, other: Self) -> Self {
        Won(self.0 + other.0)
    }
}

fn main() {
    let a = Won(1200);
    println!("ZERO     {:?}", Won::ZERO);
    println!("double   {:?}", a.double());
    println!("is_zero  {} {}", a.is_zero(), Won::ZERO.is_zero());
    println!("sum      {:?}", Won::sum(&[Won(100), Won(20), Won(3)]));
}
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
ZERO     Won(0)
double   Won(2400)
is_zero  false true
sum      Won(123)
(종료 코드 0)
```

- `Self` 는 「**이 트레이트를 구현한 그 타입**」이다. 트레이트를 쓸 때는 아직 무엇인지 모르고,
  `impl Unit for Won` 안에서 `Won` 으로 확정된다.
- **다섯 자리** — ① 연관 상수의 타입(`const ZERO: Self`) ② 인자(`other: Self`) ③ 반환(`-> Self`)
  ④ 기본 메서드 몸통 안의 `Self::ZERO` ⑤ `self` 가 없는 **연관 함수의 기본 구현**(`fn sum(items: &[Self])`).
- ★★ `trait Unit: Sized + Copy + PartialEq` 의 **슈퍼트레이트**에 주목 —
  `Self` 를 값으로 주고받으려면 크기를 알아야 해서 `Sized` 가 필요하고,
  `is_zero` 가 `==` 를 쓰므로 `PartialEq` 가 필요하다. **슈퍼트레이트는 「기본 메서드가 쓸 수 있는 도구」를 정한다.**
- ★ 그 대가로 **`Unit` 은 `dyn` 이 될 수 없다** — `Sized` 를 요구하고 `Self` 를 주고받기 때문이다((5)).

## 문법 — 형태와 규칙

```text
   정의

   trait Greet {
       fn name(&self) -> String;                 ← 필수 (몸통 없음)
       fn hello(&self) -> String { … }           ← 기본 메서드 (몸통 있음)
       const TAG: u8 = 0;                        ← 연관 상수 (기본값 가능)
       type Out;                                 ← 연관 타입
   }

   trait Unit: Sized + Copy { … }                ← 슈퍼트레이트 = 구현체에 거는 추가 요구

   구현

   impl Greet for Cat { fn name(&self) -> String { … } }      ← 필수만 채우면 된다
   impl Extract<u32> for Ticket { … }                         ← 제네릭 파라미터 판: 여러 번 가능
   impl Extract     for Ticket { type Out = u32; … }          ← 연관 타입 판: 한 번만

   쓰는 세 가지 꼴

   fn f<T: Greet>(x: &T)        ← 정적. 단형화된다
   fn f(x: impl Greet)          ← 위의 설탕. 터보피시를 못 쓴다
   fn f(x: &dyn Greet)          ← 동적. 트레이트가 dyn 이 될 수 있어야 한다

   반환 자리

   fn make() -> impl Shape      ← 타입 하나를 감춘다. 갈래는 못 넣는다
   fn make() -> Box<dyn Shape>  ← 갈래를 넣을 수 있다. 힙 할당 + 간접 호출
```

**규칙 불릿.**

- **필수 메서드를 안 채우면 거부된다.** 기본 메서드는 안 채워도 된다.
- ★ **덮어쓴 메서드는 기본 메서드 안에서도 이긴다** — 기본 메서드는 `self` 를 통해 되부른다((1)).
- **연관 타입은 구현당 하나**다. 두 번 채우면 E0119((4)).
- **제네릭 파라미터는 트레이트 이름을 가른다.** 그래서 여러 번 구현되고, 호출부가 고른다((3)).
- ★ **`dyn` 이 되려면** 연관 함수에 `self` 가 있어야 하고, 제네릭 메서드가 없어야 한다((5)).
  그 메서드에 `where Self: Sized` 를 달면 **트레이트 객체에서만 빠진다.**
- ★ **반환 자리 `impl Trait` 는 타입 하나만** 감춘다((6)).

### 금지 사례 — 던져서 받은 다섯

| 던진 것 | 받은 것 |
|---|---|
| 연관 타입 판에 `impl` 두 번 | **E0119** `` conflicting implementations `` |
| 제네릭 파라미터 판에서 타입 주석 생략 | **E0283** `` type annotations needed `` |
| `Self` 반환·제네릭 메서드가 있는 트레이트를 `dyn` 으로 | **E0038** `` is not dyn compatible `` |
| 반환 자리 `impl Trait` 에 두 갈래 | **E0308** `` `if` and `else` have incompatible types `` |
| 필수 메서드를 안 채운 `impl` | **E0046** (`missing … in implementation`) — 이 문서에는 블록이 없다 |

## 어디서 틀리나

### 1. ★★★ 「기본 메서드는 고정된 답이다」

`shout` 을 안 덮었는데 `Dog` 에서 `멍!!!` 이 나왔다((1)).
**기본 메서드는 `self` 를 통해 구현체를 되부르므로, 필수 메서드 하나만 덮어도 파급이 간다.**
거꾸로 말하면 **기본 메서드의 답을 바꾸는 방법이 둘**이다 — 그 메서드를 덮거나, 그것이 부르는 메서드를 덮거나.

### 2. ★★ 「연관 타입은 출력 타입, 제네릭 파라미터는 입력 타입」

외우기는 쉬운데 **판정 기준이 아니다.** 진짜 기준은 **「한 타입이 이 트레이트를 여러 번 구현해야 하나」** 하나다((3)·(4)).
`Add<Rhs = Self>` 는 출력이 아니라 **입력**에 제네릭 파라미터를 쓰는데, `i32 + i32` 와 `Duration + Duration` 처럼
**한 타입이 여러 오른쪽 피연산자를 받아야 하기 때문**이다(목록의 **30번 주제**).

### 3. ★ 「`dyn` 이 안 되면 그 트레이트는 잘못 만든 것이다」

아니다. **`Self` 를 주고받는 트레이트는 원래 `dyn` 이 될 수 없고 그래도 된다**((5)·(7)).
`Clone`·`Ord`·`Default` 가 전부 그렇다. 필요하면 **그 메서드에만 `where Self: Sized`** 를 달아 쪼갠다.

### 4. ★★ 「반환 자리 `impl Trait` 면 아무거나 돌려줄 수 있다」

**반대다.** `impl Trait` 는 **타입을 감추지 갈래를 만들지 않는다**((6)).
갈래가 필요하면 `Box<dyn Trait>` 이고, 그때 **힙 할당과 간접 호출**이라는 값을 낸다.

### 5. ★ 「`impl Trait` 인자와 `<T: Trait>` 는 완전히 같다」

거의 같은데 **터보피시가 안 된다** — `show::<Square>(…)` 로 못 부른다.
공개 API 에서는 **호출자가 타입을 찍을 길을 막는 것**이므로 생각하고 쓴다(목록의 **32번 주제**).

### 6. 슈퍼트레이트를 「상속」으로 읽는다

`trait Unit: Copy` 는 **`Unit` 이 `Copy` 를 물려받는 것이 아니라**,
「`Unit` 을 구현하려면 `Copy` 도 구현돼 있어야 한다」는 **요구**다((7)).
그 대신 **기본 메서드 몸통에서 `Copy` 의 능력을 쓸 수 있게 된다.**

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| 필수 메서드를 안 채우면 거부되는 것 | ★ **언어 보장** | Reference |
| 기본 메서드가 `self` 로 구현체를 되부르는 것 | ★ **언어 보장** | (1)·(2)의 실측 |
| 정적·동적에서 **규칙이 같은 것** | ★ **언어 보장** | (2)의 실측 |
| 연관 타입이 구현당 하나인 것(E0119) | ★ **언어 보장** | (4)의 실측 |
| `dyn` 이 되는 조건 | ★ **언어 보장** — Reference 의 dyn compatibility 절 | (5)의 실측 |
| 반환 자리 `impl Trait` 가 타입 하나인 것 | ★ **언어 보장** | (6)의 실측 |
| **`&dyn Greet` 가 16바이트**인 것 | ★ **구현 세부** — 뚱뚱한 포인터의 폭은 타깃·판에 달렸다 | (2)의 실측 |
| 진단이 「**dyn compatible**」이라고 쓰는 것 | ★ **이 판의 말버릇** — 1.83 에서 「object safe」에서 바뀌었다 | (5)의 실측 |
| 에러 번호가 E0283 이냐 E0282 냐 | ★ **구현 세부** — 후보가 여럿이면 E0283 이었다 | (3)의 실측 |
| `help:` 가 제안하는 고침안의 문구 | ★ **구현 세부** | (5)·(6)의 실측 |

## 언제 쓰고 언제 안 쓰나

- **기본 메서드를 둔다** — 대부분의 구현이 같게 동작해도 될 때. **필수 메서드는 최소로 줄인다.**
- **연관 타입을 쓴다** — 한 타입에 **한 번만** 구현되는 것이 자연스러울 때. 호출부가 가벼워진다.
- **제네릭 파라미터를 쓴다** — 한 타입에 **여러 번** 구현돼야 할 때(`From<T>`·`Add<Rhs>`).
- **`impl Trait` 인자를 쓴다** — 짧게 쓰고 싶고, 호출자가 타입을 찍을 일이 없을 때.
- **`impl Trait` 반환을 쓴다** — 돌려주는 타입이 **하나**이고 그 이름을 감추고 싶을 때(클로저·이터레이터 체인).
- **`dyn Trait` 를 쓴다** — **갈래**가 필요할 때(여러 타입을 한 `Vec` 에). 값은 힙 할당 + 간접 호출이다.
- ★ **`dyn` 을 안 쓴다** — 타입이 컴파일 때 하나로 정해지는데 습관으로 `Box<dyn …>` 을 쓰는 것.

## 핵심 문장

- ★★★ **기본 메서드는 고정된 답이 아니라 구현체를 되부르는 뼈대다.** 필수 메서드 하나를 덮으면 그 답까지 바뀐다.
- ★★ **정적이든 동적이든 규칙은 같다.** 달라지는 것은 「어디서 정해지느냐」와 포인터 폭뿐이다.
- ★★★ **연관 타입과 제네릭 파라미터의 갈림길은 「한 타입에 몇 번 구현되나」 하나다.** E0119 와 E0283 이 그 두 대가다.
- ★★ **객체 안전성의 정의는 에러 전문이다** — `self` 없는 연관 함수와 제네릭 메서드가 표를 못 만든다.
- ★ **`impl Trait` 는 타입을 감추지 갈래를 만들지 않는다.** 갈래가 필요하면 `dyn` 이다.

## 관련 자료

- [**16번 주제** — 구조체·`impl`·연관 함수·`Self`](../16-structs-impl-and-associated-functions/) —
  ★ **경계**: `Self` 와 `impl` 블록의 정본은 거기, 여기는 **그것이 트레이트 안에 들어갔을 때**다.
- [**17번 주제** — 열거형](../17-enums-and-data-carrying-variants/) —
  열거형에도 `impl` 과 트레이트가 붙는다. `derive` 가 열거형에 걸리는 자리는 거기와 [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)다.
- [**26번 주제** — 고아 규칙과 newtype](../26-orphan-rule-and-newtype/) —
  ★ **경계**: 「**누가** 구현할 수 있나」는 거기, 여기는 「**무엇을** 구현하나」다.
- [**22번 주제** — `Result` 와 `?`·`From`](../22-result-question-mark-and-from/) —
  `From<T>` 가 **제네릭 파라미터 판**의 대표 사례다. 한 타입이 여러 번 구현한다.
- 목록의 **31번 주제** — 제네릭과 트레이트 경계·단형화. **경계 문법과 코드 팽창**의 정본이다.
- 목록의 **32번 주제** — `impl Trait` 의 정본. 여기서는 (6)만큼만 닿았다.
- 목록의 **33번 주제** — `dyn Trait` 와 객체 안전성의 정본. (2)의 표(vtable)와 (5)의 조건이 거기서 깊어진다.
- 목록의 **36번 주제** — `Iterator`. **필수 메서드 하나 + 기본 메서드 수십 개**의 극단 사례다.
- [`foundations/oop-basics/`](../../../../oop-basics/) —
  ★ **경계**: 다형성·인터페이스 **일반론**은 거기, 여기는 **트레이트 문법**이다.
- Kotlin 의 인터페이스 — [`kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/).
  ★ **대비**: 기본 구현이 있는 것은 같고, **Kotlin 인터페이스는 상태를 못 가지며**
  **같은 시그니처가 둘에서 오면 컴파일러가 거부**한다. Rust 는 **애초에 「한 타입에 한 트레이트는 한 번」이라** 그 충돌이 다른 모양으로 온다((4)).
- Java 의 `default` 메서드 — [`java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/).
  ★ **대비**: Java 는 **인터페이스를 선언할 때 `implements` 를 적어야** 하고, Rust 는 **나중에 남이 붙일 수 있다**((26번)).
- Go 의 암묵 인터페이스 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**.
  ★ **대비**: Go 는 **구현을 선언하지 않는다**(메서드 집합이 맞으면 끝). Rust 는 `impl … for …` 를 **반드시 적는다** —
  그래서 Rust 에는 **기본 메서드와 고아 규칙이 있을 수 있고**, Go 에는 그 자리가 원리상 없다.
- C# 의 확장 메서드 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **30번**.
  ★ **대비**: 「남의 타입에 메서드를 붙인다」는 목적이 겹치는데, 확장 메서드는 **정적 메서드의 설탕**이라
  **다형성이 없다.** Rust 의 트레이트 구현은 **진짜 구현**이라 제네릭 경계와 `dyn` 에 그대로 쓰인다.

## 용어 풀이

- **트레이트(trait)** — 타입이 무엇을 할 줄 아는지 적어 둔 계약. 다른 언어의 인터페이스 자리.
- **필수 메서드** — 몸통 없이 선언만 한 메서드. 구현체가 반드시 채운다.
- **기본 메서드(default method)** — 트레이트가 몸통까지 준 메서드. 안 덮으면 그것이 쓰인다.
- **연관 타입(associated type)** — 구현이 채우는 타입 자리. 구현당 하나.
- **연관 상수(associated const)** — 구현이 채우는 상수 자리. 기본값을 줄 수 있다.
- **연관 함수(associated function)** — `self` 를 안 받는 함수. `Type::f()` 로 부른다.
- **슈퍼트레이트(supertrait)** — `trait A: B` 의 `B`. 구현체에 거는 추가 요구이자 기본 메서드가 쓸 도구.
- **단형화(monomorphization)** — 제네릭 함수를 **타입마다 따로 찍어 내는 것**. 정적 디스패치의 뒷면이다.
- **트레이트 객체(`dyn Trait`)** — 구체 타입을 지운 값. 값 주소와 메서드 표 주소를 함께 든다.
- **dyn 호환(dyn compatible)** — 트레이트 객체가 될 수 있는 성질. **옛 이름이 「객체 안전(object safe)」이다**.
- **`impl Trait`** — 인자 자리에서는 제네릭의 설탕, 반환 자리에서는 **타입 하나를 감추는 것**.

## 더 들어가면

- **연관 타입에 경계 달기** — `fn f<I: Iterator<Item = u8>>(it: I)` 처럼 **연관 타입을 지정해** 좁힐 수 있다.
- **제네릭 연관 타입(GAT)** — 연관 타입이 자기 수명·타입 파라미터를 가지는 것. **1.65 부터** 안정이다.
- **`where Self: Sized`** — 트레이트 객체에서 특정 메서드만 빼는 장치((5)의 `help:` 가 제안한 것).
- **포괄 구현(blanket impl)** — `impl<T: Display> MyTrait for T` 처럼 **조건에 맞는 모든 타입**에 한 번에 거는 것.
  [**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙과 맞물린다.
- **`Rhs = Self` 같은 기본 타입 파라미터** — 제네릭 파라미터 판에 기본값을 주는 문법(목록의 **30번 주제**).
