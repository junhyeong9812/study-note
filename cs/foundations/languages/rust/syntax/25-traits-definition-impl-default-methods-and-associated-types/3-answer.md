# rust/syntax/25 — 트레이트 정의·구현·기본 메서드·연관 타입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★ `rustc --explain E0038` · `E0119` · `E0283` · `E0308` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `shout` 을 안 덮었는데 답이 바뀐다

**출력.**

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

**왜 그런가**

- `Cat` 은 `name` 하나만 채웠는데 `hello`·`shout` 이 나왔다 — **트레이트에 적힌 몸통이 쓰인 것**이다.
- ★★★ `Dog` 은 `hello` 만 덮었는데 **`shout` 까지 `멍!!!` 로 바뀌었다.**
  `shout` 의 몸통은 트레이트의 것 그대로이고, 그 안의 `self.hello()` 가 **`Dog` 의 것으로 풀린** 결과다.
- 그래서 **기본 메서드는 「고정된 답」이 아니라 「구현체를 되부르는 뼈대」다**.
  답을 바꾸는 길이 둘이다 — **그 메서드를 덮거나, 그것이 부르는 메서드를 덮거나**(8번 답).
- 필수 메서드를 안 채우면 **E0046**(`` not all trait items implemented ``)으로 거부된다.
  ★ 이 문서에는 그 블록이 없다 — 「던져 본 것만 싣는다」는 규칙에 따라 **번호만** 적는다.

### 2. ★★ 정적이든 동적이든 규칙이 같다 — 다른 것은 포인터 폭

**출력.**

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

**왜 그런가**

- ★★ **앞 문항의 여섯 줄과 한 글자도 같다.** `Cat` 은 트레이트의 `hello`, `Dog` 은 자기 `hello`,
  둘 다 `shout` 은 트레이트의 것 — **디스패치 방식이 「누가 이기나」를 바꾸지 않는다.**
- **`&Cat` 은 8바이트, `&dyn Greet` 는 16바이트**다. 뒤엣것은 **값의 주소 + 메서드 표의 주소** 둘을 든다.
  그래서 「뚱뚱한 포인터(fat pointer)」라고 부른다.
- **기본 메서드도 표에 칸을 차지한다** — 안 덮었으면 그 칸이 트레이트의 몸통을 가리킬 뿐이다.
  그래서 `dyn` 에서도 덮어쓰기가 그대로 먹는다.
- ★ **16바이트는 구현 세부다.** 뚱뚱한 포인터의 폭은 타깃과 판에 달렸다 — 언어가 약속한 수가 아니다.
  이 수치는 `x86_64-unknown-linux-gnu` · rustc 1.92 의 관찰이다.

### 3. ★★★ 제네릭 파라미터는 되고 연관 타입은 E0119

**출력 — 제네릭 파라미터 판(통과).**

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

**출력 — 연관 타입 판에 두 번 구현(거부).**

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

**왜 그런가**

- ★★★ **갈리는 한 문장** — `` Extract<u32> `` 와 `` Extract<String> `` 은 **서로 다른 트레이트**이고,
  연관 타입 판의 두 `impl` 은 **같은 트레이트의 두 구현**이다.
- 그래서 앞은 통과하고 뒤는 **E0119** `` conflicting implementations of trait `Extract` for type `Ticket` `` 다.
  진단이 `` first implementation here `` 로 **먼저 쓴 쪽을 짚어 준다.**
- ★ **연관 타입은 트레이트 이름의 일부가 아니다.** 이름을 가르는 것은 **제네릭 파라미터뿐**이다.
  이 한 줄이 두 도구의 갈림길 전부다.
- 통과한 쪽의 대가는 출력 셋째 줄에 보인다 — `Extract::<u32>::extract(&t)` 처럼 **호출부가 찍어야** 한다.

### 4. ★★ E0283 — 후보 둘을 그 자리에서 짚어 준다

**출력.**

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

**왜 그런가**

- **E0283** `` type annotations needed ``. 진단이 `` multiple `impl`s satisfying `Ticket: Extract<_>` found `` 로
  **후보 두 개**(9번 줄과 15번 줄)를 짚는다.
- `help:` 는 `` let c: /* Type */ = t.extract(); `` 로 **자리를 만들어 준다.**
- ★★ **구현이 하나뿐이었다면 통과했겠는가** — 통과한다. 하지만 그것이 **위험**이다.
  나중에 두 번째 `impl` 이 생기는 순간 **그 타입을 쓰던 호출부 전부가 한꺼번에 깨진다.**
  연관 타입 판에서는 두 번째 `impl` 자체가 막히므로(3번 답) **그 사고가 원리상 안 난다.**
- ★ 이것이 (3)과 짝을 이루는 **제네릭 파라미터의 고정 비용**이다 — 유연함의 값이다.

### 5. ★★★ E0038 — 이유 둘을 각각 그 줄에서 짚는다

**출력.**

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

**왜 그런가**

- **E0038** — `` the trait `Spawner` is not dyn compatible ``. 진단이 **이유를 둘** 댄다.
  ① `` ...because associated function `new_one` has no `self` parameter `` (4번 줄)
  ② `` ...because method `feed` has generic type parameters `` (6번 줄)
- **`self` 없는 연관 함수** — `dyn Spawner` 는 **어느 구체 타입인지 모르는 값**이다.
  `new_one()` 은 받을 값이 없어 무엇을 만들지 정할 수가 없다.
- **제네릭 메서드** — `feed::<u8>`·`feed::<String>` … 필요한 칸이 **무한히 많아** 표를 못 만든다.
- ★★★ **진단 전문에 「object safe」라는 말이 한 번도 안 나온다.** rustc 는 **1.83** 부터
  「object safety」를 「**dyn compatibility**」로 바꿔 부른다. 한국어 자료는 아직 「객체 안전성」이라고 쓰므로
  **같은 것임을 알고 있어야** 에러를 읽을 수 있다.
- `help:` 둘 — ① `new_one` 에 `&self` 를 붙여 **메서드로 만들라** ②
  `` fn new_one() -> Self where Self: Sized; `` 로 **그 메서드만 트레이트 객체에서 빼라**.
  뒤엣것이 std 가 `Clone`·`Ord` 에서 쓰는 수법이다.

### 6. ★ E0308 — `impl Trait` 는 갈래를 만들지 않는다

**출력.**

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

**왜 그런가**

- **E0308** `` `if` and `else` have incompatible types `` — `` expected `Square`, found `Circle` ``.
  **반환 자리 `impl Trait` 는 「타입 이름을 감추는 것」이지 「여러 타입을 받는 것」이 아니다.**
  감춰진 그 자리에는 **컴파일 때 하나로 정해지는 타입**이 들어간다.
- ★ `help:` 가 **두 단계**로 나온다 — ① 반환 타입을 `` Box<dyn Shape> `` 로 바꾸고
  ② 두 갈래를 각각 `` Box::new(…) `` 로 감싸라. **갈래가 필요하면 그때가 `dyn` 을 쓸 때다.**
- **인자 자리에는 이 제약이 없다.** 인자 자리 `impl Trait` 는 `` fn show<T: Shape>(s: T) `` 의 설탕이라
  호출할 때마다 다른 타입이 들어가도 된다 — **호출마다 따로 찍히기** 때문이다.

### 7. 두 도구를 고르는 한 질문

- ★★★ **「한 타입이 이 트레이트를 여러 번 구현해야 하나?」** — 그래야 하면 **제네릭 파라미터**, 아니면 **연관 타입**.
- 「연관 타입은 출력, 제네릭 파라미터는 입력」이라는 외움말은 **`Add<Rhs = Self>` 에서 깨진다** —
  `Rhs` 는 **입력**인데 제네릭 파라미터다. 이유는 `i32 + i32` 와 `Duration + Duration` 처럼
  **한 타입이 여러 오른쪽 피연산자를 받아야 하기 때문**이다(목록의 **30번 주제**).
- **`From<T>` 도 같은 이유**다 — `String` 은 `From<&str>`·`From<char>` … 여러 번 구현된다
  ([**22번 주제**](../22-result-question-mark-and-from/)의 `?` 가 그 위에서 돈다).
- 연관 타입을 골랐을 때 **호출부가 덜 쓰는 것** — ① `let` 의 타입 주석 ② 제네릭 함수의 타입 파라미터
  (`fn twice<E: Extract>` 하나면 된다) ③ 터보피시. 3번 답의 셋째 출력 줄과 비교하면 보인다.

### 8. 기본 메서드의 값과 한계

- **기본 메서드는 상태를 못 가진다.** 트레이트에는 필드가 없다 — 쓸 수 있는 것은
  **필수 메서드·연관 상수·슈퍼트레이트가 주는 것**뿐이다((7)의 `Self::ZERO` 가 연관 상수를 쓴 예다).
- **답을 바꾸는 방법은 둘이다** — ① 그 기본 메서드를 덮는다 ② 그것이 부르는 **필수 메서드**를 덮는다(1번 답).
- **슈퍼트레이트는 기본 메서드가 쓸 도구를 정한다** — `trait Unit: PartialEq` 라야 기본 메서드 안에서 `==` 를 쓸 수 있다.
  대가는 **구현체가 그것도 구현해야** 한다는 것이다.
- ★ **기본 메서드를 나중에 더해도 기존 구현체는 안 깨진다** — 채울 의무가 없기 때문이다.
  이것이 **트레이트를 넓히는 하위 호환 수단**이다. 반대로 **필수 메서드를 더하면 전부 깨진다.**

### 9. 세 꼴의 분업

- `` fn f<T: Greet>(x: &T) `` — 정적. **단형화**되어 호출이 직접 박힌다. 타입을 이름으로 쓸 수 있다.
- `` fn f(x: impl Greet) `` — 위의 설탕. 짧지만 ★ **터보피시가 안 된다**(`f::<Square>(…)` 로 못 부른다).
  공개 API 라면 **호출자에게서 타입을 찍을 길을 빼앗는 것**이므로 생각하고 쓴다(목록의 **32번 주제**).
- `` fn f(x: &dyn Greet) `` — 동적. **갈래**를 담을 수 있다. 값은 ① 간접 호출(표를 한 번 읽는다)
  ② 인라인이 어려워짐 ③ 뚱뚱한 포인터(2번 답의 16바이트) ④ `Box` 면 힙 할당.
- ★ **갈래가 필요 없는데 `Box<dyn …>` 을 쓰면** 그 값을 다 내면서 **정적 디스패치의 최적화만 잃는다.**
  판정 기준은 하나다 — **한 자리에 서로 다른 타입이 들어와야 하나.**

### 10. `Self` 가 오는 다섯 자리

**출력.**

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

**왜 그런가**

- **다섯 자리** — ① `const ZERO: Self`(연관 상수의 타입) ② `other: Self`(인자)
  ③ `-> Self`(반환) ④ `Self::ZERO`(기본 메서드 몸통 안) ⑤ `items: &[Self]`(연관 함수의 기본 구현).
- **세 슈퍼트레이트의 이유** — `Sized` 는 `Self` 를 **값으로 주고받으려면** 크기를 알아야 해서,
  `Copy` 는 `sum` 이 `*it` 로 **슬라이스에서 값을 꺼내 쓰기** 위해, `PartialEq` 는 `is_zero` 가 **`==` 를 쓰기** 위해서다.
- ★ **이 트레이트는 `dyn` 이 될 수 없다** — `Sized` 를 요구하고 `Self` 를 주고받기 때문이다(5번 답).
  `Copy` 도 `Clone` 을 요구하고 `Clone` 은 `-> Self` 라서, 이 줄기는 **통째로 정적 전용**이다.
- **`const ZERO: Self` 를 안 채우면** 기본값이 없으므로 **E0046** 으로 거부된다
  (연관 상수에 `= 0` 같은 **기본값을 주면** 안 채워도 된다).

### 11. 다른 언어와 잇기

- **Kotlin 의 인터페이스**([`kotlin/syntax/20-interfaces-default-impl-and-super/`](../../../kotlin/syntax/20-interfaces-default-impl-and-super/)) —
  ★ **같은 것 둘**: 기본 구현을 줄 수 있고, 구현체가 덮으면 그쪽이 이긴다.
  ★ **다른 것 둘**: ① Kotlin 은 **같은 시그니처가 둘에서 오면 컴파일러가 거부**하고 사람이 `super<T>` 로 고른다 —
  Rust 는 「한 타입에 한 트레이트는 한 번」이라 그 충돌이 **E0119 라는 다른 모양**으로 온다(3번 답).
  ② Kotlin 은 **클래스 선언에 인터페이스를 적어야** 하고, Rust 는 **나중에 남이 `impl` 을 붙일 수 있다**
  (그래서 [**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙이 필요해진다).
- **Go 의 암묵 인터페이스**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **20번**) —
  ★ **Go 에 원리상 없는 것 둘**: ① **기본 메서드** — 구현을 선언하는 자리가 없으니 「안 채우면 이것」을 적을 곳이 없다.
  ② **고아 규칙** — 「누가 구현했나」라는 개념 자체가 없다.
- **Java 의 `default` 메서드**([`java/syntax/11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) —
  역할은 같다. 다른 것은 Java 가 **클래스가 인터페이스를 이기는 규칙(class wins)을** 두는 것이고,
  Rust 는 **한 타입에 그 트레이트 구현이 하나뿐**이라 그런 우선순위 규칙이 필요 없다.
- **C# 의 확장 메서드**(C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **30번**) —
  ★ **결정적으로 다른 것**: 확장 메서드는 **정적 메서드의 문법 설탕**이라 **다형성이 없다**
  (호출할 메서드가 **정적 타입**으로 정해진다). Rust 의 트레이트 구현은 **진짜 구현**이라
  제네릭 경계(`T: Greet`)와 `dyn Greet` 에 **그대로 쓰인다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서의 모든 블록 | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` — 전 블록 동일 |
| ★★★ **기본 메서드가 어디로 가나** | `b25-01`(정적) · `b25-02`(동적) — **같은 트레이트를 두 꼴로** | 2 | 출력이 **한 글자도 같다** |
| ★★★ **연관 타입 대 제네릭 파라미터** | `b25-03`(통과) · `b25-04`(E0283) · `b25-05`(통과) · `b25-06`(E0119) | 4 | **E0119 와 E0283** 이 갈림길 |
| ★★ **객체 안전성** | `b25-07` — 두 이유를 한 트레이트에 함께 넣어 던짐 | 1 | E0038 · 이유 2개 · 「dyn compatible」 |
| `impl Trait` 인자·반환 | `b25-08`(통과) · `b25-09`(E0308) | 2 | 갈래는 못 넣는다 |
| `Self` 가 오는 자리 | `b25-10` — 다섯 자리를 한 트레이트에 | 1 | 전부 통과 |
| 포인터 폭 | `b25-02` 의 `size_of` | 1 | 8 대 **16** |
| **안 던져 본 것** — E0046 | 1번·10번 답에서 **번호만** 적었다 | 0 | ★ 블록이 없으므로 **번호 외에는 단정하지 않았다** |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `&dyn Greet` 가 **16바이트**인 것 | ★ 타깃·판에 달린 **구현 세부**다 |
| 진단이 「**dyn compatible**」이라고 쓰는 것 | ★ rustc **1.83** 에서 「object safe」에서 바뀌었다. 더 바뀔 수 있다 |
| E0283 이냐 E0282 냐 | 후보가 여럿이라 E0283 이었다 — 추론 경로가 갈린다 |
| `help:` 문구와 제안 코드 | 진단 품질 개선으로 자주 바뀌는 자리다 |
| E0038 이 대는 **이유의 순서** | 진단 생성 순서에 달렸다 |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.
이 주제에는 패닉도 주소도 없으므로 **달라지는 파일이 하나도 없어야** 한다.
