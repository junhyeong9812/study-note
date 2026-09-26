# rust/syntax/27 — `derive` 매크로(`Debug`·`Clone`·`PartialEq`·`Default`·`Hash`) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ **외부 크레이트를 하나도 쓰지 않는다.** `cargo expand` 도 없다 — 생성된 코드는 **다른 창**으로 본다(7번).
> ★★★ **이 주제는 「무엇이 생성되나」와 「무엇이 요구되나」 둘을 갈라 답하는 주제다.**
> 「된다 / 안 된다」로 끝내지 말고 **에러 번호**와 **진단이 짚는 자리**까지 적어 보라.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 나머지 다섯은 한 줄 질문으로 싸게 늘렸다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 다섯을 한꺼번에 붙이고 하나씩 써 보면 (예측)

```rust
// b27-01.rs
// ex.rs
// 다섯 derive 가 무엇을 만드나 — 하나씩 실제로 써 본다
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::BuildHasherDefault;

#[derive(Debug, Clone, PartialEq, Eq, Default, Hash)]
struct Key {
    id: u32,
    name: String,
}

fn main() {
    let k = Key { id: 7, name: String::from("가") };

    println!("Debug      {:?}", k);
    let c = k.clone();
    println!("Clone      {:?} · 원본도 살아 있다 {:?}", c, k);
    println!("PartialEq  {} {}", k == c, k == Key { id: 8, name: String::from("가") });
    println!("Default    {:?}", Key::default());

    // Hash — HashMap 키로 쓸 수 있다. ★ 순회하지 않고 키로 직접 읽는다
    let mut m: HashMap<Key, &str, BuildHasherDefault<DefaultHasher>> = HashMap::default();
    m.insert(k.clone(), "값");
    println!("Hash       {:?} · len {}", m.get(&c), m.len());
}
```

- 다섯 줄의 출력을 **한 글자도 안 틀리게** 적을 수 있는가?
- ★ `Debug` 가 찍는 **형식**은 무엇인가 — `String` 필드는 어떻게 나오는가?
- ★★ `derive` 목록에 **`Eq` 가 왜 끼어 있는가** — 빼면 어느 줄이 깨지는가?
- `Default` 가 만든 값의 두 필드는 각각 무엇인가?

### 2. ★ `{:?}` 와 `{:#?}` (예측)

```rust
// b27-02.rs
// ex.rs
// Debug 의 두 얼굴 — {:?} 와 {:#?}
#[derive(Debug)]
struct Inner {
    x: i32,
    tags: Vec<&'static str>,
}

#[derive(Debug)]
struct Unit;

#[derive(Debug)]
struct Tup(i32, i32);

#[derive(Debug)]
enum Shape {
    Dot,
    Line(i32),
    Box { w: i32, h: i32 },
}

#[derive(Debug)]
struct Outer {
    name: String,
    inner: Inner,
    unit: Unit,
    tup: Tup,
    shapes: Vec<Shape>,
}

fn main() {
    let o = Outer {
        name: String::from("가"),
        inner: Inner { x: 1, tags: vec!["a", "b"] },
        unit: Unit,
        tup: Tup(3, 4),
        shapes: vec![Shape::Dot, Shape::Line(5), Shape::Box { w: 6, h: 7 }],
    };
    println!("--- {{:?}} ---");
    println!("{:?}", o);
    println!("--- {{:#?}} ---");
    println!("{:#?}", o);
}
```

- 두 형식의 출력이 어떻게 다른가 — **같은 `Debug` 구현**이 둘 다 내는가?
- ★ **유닛 구조체 · 튜플 구조체 · enum 변형 셋**은 각각 어떤 모양으로 찍히는가?
- `{:#?}` 의 들여쓰기는 몇 칸이고, **마지막 항목 뒤에 쉼표**가 붙는가?
- ★ 이 형식을 **파싱해서 써도 되는가**?

### 3. ★★★ 안 붙였을 때와, 붙였는데 필드가 못 따라갈 때 (예측)

```rust
// b27-03.rs
// ex.rs
// derive 를 하나도 안 붙이면 — 다섯 자리가 각각 다른 에러로 막힌다
use std::collections::HashMap;

struct Bare {
    n: i32,
}

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a = Bare { n: 1 };
    println!("{:?}", a);            // Debug
    let _b = dup(&a);               // Clone
    println!("{}", a == a);         // PartialEq
    let _d = Bare::default();       // Default
    let mut m: HashMap<Bare, i32> = HashMap::new();
    m.insert(Bare { n: a.n }, 1);   // Hash + Eq
}
```

```rust
// b27-10.rs
// ex.rs
// derive 는 필드에 그 트레이트를 요구한다 — f64 는 Hash 도 Eq 도 아니다
#[derive(PartialEq, Eq, Hash)]
struct Point {
    x: i32,
    ratio: f64,
}

fn main() {
    let a = Point { x: 1, ratio: 0.5 };
    let b = Point { x: 1, ratio: 0.5 };
    println!("{}", a == b);
}
```

- 앞 소스의 에러는 **몇 건**이고 **에러 번호는 몇 가지**인가?
- ★★ 다섯 자리 중 **연산자**·**메서드**·**경계**가 각각 어느 번호로 갈리는가?
- ★ `help:` 가 제안하는 `derive` 목록에 **`PartialEq` 까지 들어가는 자리**는 어디인가?
- 뒤 소스는 왜 막히는가 — **`PartialEq` 는 되는데 `Eq`·`Hash` 는 안 되는** 이유는?
- ★★ 뒤 소스의 진단에서 `` AssertParamIsEq `` 라는 이름은 **어디서 온 것**인가?

### 4. ★★★ 값이 하나도 안 들었는데 복제가 막힌다 (예측)

```rust
// b27-04.rs
// ex.rs
// derive 가 붙이는 경계가 과하다 — PhantomData<T> 인데 T: Clone 을 요구한다
use std::marker::PhantomData;

#[derive(Clone)]
struct Tagged<T> {
    n: i64,
    p: PhantomData<T>,
}

struct NotClone; // Clone 이 아니다

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a: Tagged<NotClone> = Tagged { n: 1, p: PhantomData };
    let b = a.clone();  // ① 메서드로 바로
    let c = dup(&a);    // ② T: Clone 경계를 통해
    println!("{} {}", b.n, c.n);
}
```

```rust
// b27-05.rs
// ex.rs
// 손으로 구현하면 그 경계가 안 붙는다 — 같은 타입, 같은 쓰임
use std::marker::PhantomData;

struct Tagged<T> {
    n: i64,
    p: PhantomData<T>,
}

impl<T> Clone for Tagged<T> {
    // ★ where T: Clone 이 없다
    fn clone(&self) -> Self {
        Tagged { n: self.n, p: PhantomData }
    }
}

struct NotClone; // 여전히 Clone 이 아니다

fn dup<T: Clone>(x: &T) -> T {
    x.clone()
}

fn main() {
    let a: Tagged<NotClone> = Tagged { n: 1, p: PhantomData };
    let b = a.clone();
    let c = dup(&a);
    println!("메서드로 {} · 경계로 {}", b.n, c.n);
    println!("크기 Tagged<NotClone> {} · i64 {}",
             std::mem::size_of::<Tagged<NotClone>>(),
             std::mem::size_of::<i64>());
}
```

- 앞 소스는 컴파일되는가? **에러 몇 건**이고 **번호**는?
- ★★ 두 에러의 번호가 다르다면 **무엇이 그것을 갈랐는가**?
- ★★★ 진단이 **`#[derive(Clone)]` 줄을 가리키며** 하는 말은 무엇인가?
- 뒤 소스는 **한 가지만** 다르다. 무엇이고, 왜 그것으로 통과하는가?
- `Tagged<NotClone>` 의 **크기**는 얼마인가?

### 5. ★★ 세 번 비교하면 몇 줄이 찍히나 (예측)

```rust
// b27-07.rs
// ex.rs
// 같은 것을 동작으로도 — 필드 순서대로 보고 틀리면 거기서 멈춘다
// ★ 마커도 결과도 전부 표준 오류로 찍는다(섞이지 않게)
struct Probe(u8, &'static str);

impl PartialEq for Probe {
    fn eq(&self, other: &Self) -> bool {
        eprintln!("  비교: {}", self.1);
        self.0 == other.0
    }
}

#[derive(PartialEq)]
struct Row {
    first: Probe,
    second: Probe,
    third: Probe,
}

fn row(a: u8, b: u8, c: u8) -> Row {
    Row {
        first: Probe(a, "first"),
        second: Probe(b, "second"),
        third: Probe(c, "third"),
    }
}

fn main() {
    eprintln!("[1] 전부 같다");
    eprintln!("  결과 {}", row(1, 2, 3) == row(1, 2, 3));
    eprintln!("[2] 첫 필드부터 다르다");
    eprintln!("  결과 {}", row(9, 2, 3) == row(1, 2, 3));
    eprintln!("[3] 둘째 필드가 다르다");
    eprintln!("  결과 {}", row(1, 9, 3) == row(1, 2, 3));
}
```

- 세 묶음이 각각 **몇 줄**을 찍는가? 전체 출력을 적을 수 있는가?
- ★ 이 프로그램이 마커를 **`eprintln!` 로만** 찍는 이유는?
- ★★ 여기서 드러나는 성질 둘은 무엇인가 — 그것이 **뜻**을 바꾸는가 **비용**을 바꾸는가?

### 6. ★★ `derive(Default)` 가 enum 에서만 되묻는다 (예측)

```rust
// b27-08.rs
// ex.rs
// derive(Default) 는 enum 에서만 사람에게 묻는다 — 어느 변형이 기본인가
#[derive(Debug, Default)]
enum Mode {
    // ★ 아무 변형에도 #[default] 가 없다
    Fast,
    Slow,
}

#[derive(Debug, Default)]
enum Level {
    #[default]
    Named(u8), // ★ 유닛 변형이 아니다
    Other,
}

fn main() {
    println!("{:?} {:?}", Mode::default(), Level::default());
}
```

```rust
// b27-09.rs
// ex.rs
// 고쳐서 던지면 — #[default] 는 유닛 변형 하나에만 붙는다
#[derive(Debug, Default)]
enum Mode {
    Fast,
    #[default]
    Slow,
}

#[derive(Debug, Default)]
struct Config {
    name: String,   // ""
    retries: u32,   // 0
    ratio: f64,     // 0.0
    on: bool,       // false
    tags: Vec<u8>,  // []
    mode: Mode,     // ★ 필드 타입의 Default 를 그대로 부른다
    opt: Option<u8>,
}

fn main() {
    println!("변형 둘   {:?} {:?}", Mode::Fast, Mode::Slow);
    println!("기본 변형 {:?}", Mode::default());
    let c = Config::default();
    println!("구조체    {:?}", c);
    println!("필드마다  {:?} {} {} {} {:?} {:?} {:?}",
             c.name, c.retries, c.ratio, c.on, c.tags, c.mode, c.opt);
}
```

- 앞 소스의 에러는 **몇 건**인가? 한 건은 **번호가 없다** — 어느 쪽이고 무엇이라고 하는가?
- ★★ **구조체는 안 묻고 enum 은 묻는** 이유는 무엇인가?
- ★ `help:` 가 **변형마다 따로** 나오는 것은 무엇을 뜻하는가?
- 뒤 소스의 출력 네 줄은 무엇인가 — `Option<u8>` 필드는 무엇이 되는가?

### 7. ★★ 생성된 코드를 볼 수 있나 (경계)

```rust
// b27-06.rs
// ex.rs
// cargo expand 없이 derive 가 만든 것을 보는 길 — 안정판 rustc 의 --emit=mir
#[derive(PartialEq)]
struct P {
    a: u8,
    b: u8,
}

fn main() {
    println!("{}", P { a: 1, b: 2 } == P { a: 1, b: 3 });
}
```

- `cargo expand` 도 나이틀리도 없다. **안정판 rustc 만으로** 생성된 `eq` 를 볼 길이 있는가?
- ★★ 그 출력에서 **필드 순서**와 **단락**을 어떻게 읽어 내는가?
- ★★★ 그렇게 얻은 것은 **생성 소스 그 자체인가**? 아니라면 **무엇을 잰 것이고 무엇은 못 잰 것**인가?
- ★ 진단 쪽에도 생성 결과가 새는 자리가 둘 있다. 어디인가?

### 8. `Copy` 는 왜 혼자 못 붙나 (왜)

- `#[derive(Copy)]` 만 적으면 왜 거부되는가?
- `Clone` 과 `Copy` 의 관계를 한 문장으로 말할 수 있는가?
- `Drop` 이 있는 타입에 `Copy` 를 붙이면 어떻게 되는가?
- ★ 이 주제에서 그 판정의 **정본은 어느 주제**인가?

### 9. 언제 손으로 쓰나 (경계)

- `derive` 를 손 구현으로 바꿔야 하는 경우를 **셋** 댈 수 있는가?
- ★★ 「필드 전부를 보는 것이 틀린 뜻」인 예를 하나 들 수 있는가 — 그때 **함께 손으로 써야 하는 것**은?
- `Debug` 를 일부러 **안 붙이는** 경우는 언제인가?
- 손 구현의 대가는 무엇인가 — 그 실수는 **컴파일로 잡히는가**?

### 10. `derive` 와 고아 규칙 (연결)

- `derive` 는 왜 [**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙에 **원리상 안 걸리는가**?
- newtype 에 `derive` 를 붙이면 **안쪽 타입의 구현이 따라오는가**?
- `#[derive(Debug)]` 를 남의 타입에 붙일 수 있는가?
- ★ newtype 의 `Debug` 출력은 안쪽과 어떻게 달라지는가?

### 11. 다른 언어는 이 자리를 무엇으로 메우나 (연결)

- Kotlin 의 `data class` 와 무엇이 같고 무엇이 다른가 — **고르는 단위**가 어떻게 다른가?
- Java 의 `record` 는 `derive` 와 달리 **무엇을 함께 강제하는가**?
- Go 에는 `derive` 가 없다. 같은 자리를 **무엇 둘**로 메우는가?
- ★ 「생성인가 런타임인가」로 셋을 갈라 세울 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
