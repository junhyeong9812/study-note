# rust/syntax/29 — 변환 트레이트 `From`/`Into`/`TryFrom`/`AsRef`/`Borrow` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs && ./<파일>`. 펜스 첫 줄 `// <파일>.rs` 가 그 파일 이름이다.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 2015 에는 `TryFrom` 이 프렐류드에 없어 **다른 에러**가 난다.
> ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **이 주제의 질문은 전부 「어느 쪽을 구현했나」다.** 답할 때 **화살표를 먼저 그려라** — `From<A> for B` 에서 무엇이 생기나.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ `From` 하나만 쓰고 네 번 부르면 (예측)

```rust
// r29_from.rs
// From 하나만 구현한다 — into() 는 어디서 오나
struct Celsius(f64);
struct Fahrenheit(f64);

impl From<Celsius> for Fahrenheit {
    fn from(c: Celsius) -> Fahrenheit {
        Fahrenheit(c.0 * 1.8 + 32.0)
    }
}

fn report(t: impl Into<Fahrenheit>) {
    let f: Fahrenheit = t.into(); // ★ 이 into() 는 내가 안 썼다
    println!("  report  {}", f.0);
}

fn main() {
    println!("from()    {}", Fahrenheit::from(Celsius(100.0)).0);
    let f: Fahrenheit = Celsius(0.0).into();
    println!("into()    {}", f.0);
    report(Celsius(-40.0));
    report(Fahrenheit(1.0)); // ★ 자기 자신으로도 into 된다
}
```

- 컴파일되는가? 네 줄의 출력은 무엇인가?
- ★★ 12행과 18행의 `into()` 는 **어디에 정의돼 있는가**?
- ★ 21행 `report(Fahrenheit(1.0))` 은 왜 통과하는가 — `Fahrenheit → Fahrenheit` 변환을 누가 썼나?

### 2. ★★★ `Into` 만 쓰고 반대 방향을 부르면 (예측)

```rust
// r29_into_only.rs
// Into 만 구현하면 — From 쪽은 생기나
struct Celsius(f64);
struct Fahrenheit(f64);

impl Into<Fahrenheit> for Celsius {
    fn into(self) -> Fahrenheit {
        Fahrenheit(self.0 * 1.8 + 32.0)
    }
}

fn convert<T, U: From<T>>(t: T) -> U {
    U::from(t)
}

fn main() {
    let a: Fahrenheit = Celsius(100.0).into(); // 직접 쓴 방향
    let b = Fahrenheit::from(Celsius(0.0)); // 반대 방향
    let c: Fahrenheit = convert(Celsius(0.0)); // From 경계
    println!("{} {} {}", a.0, b.0, c.0);
}
```

```rust
// r29_into_try.rs
// Into 만 구현했는데 — try_from 은 된다
use std::convert::Infallible;

struct Celsius(f64);
struct Fahrenheit(f64);

impl Into<Fahrenheit> for Celsius {
    fn into(self) -> Fahrenheit {
        Fahrenheit(self.0 * 1.8 + 32.0)
    }
}

fn main() {
    let r: Result<Fahrenheit, Infallible> = Fahrenheit::try_from(Celsius(100.0));
    match r {
        Ok(f) => println!("try_from Ok {}", f.0),
        Err(never) => match never {},
    }
}
```

- 앞 소스의 에러는 **몇 건**이고 **번호**는 각각 무엇인가? 16행에도 에러가 나는가?
- ★★ 같은 결함인데 번호가 갈린다면 **왜** 갈리는가?
- ★★ 뒤 소스는 컴파일되는가? 된다면 `r` 의 오류 타입 `Infallible` 은 **어디서** 왔나?
- ★ 앞 소스의 `convert` 경계를 어떻게 고치면 `Into` 만 가진 타입도 받는가?

### 3. ★★ `Into` 로 오류 변환을 적고 `?` 를 쓰면 (예측)

```rust
// r29_qmark.rs
// ? 는 From 을 부른다 — Into 만 있으면
use std::num::ParseIntError;

#[derive(Debug)]
struct PortError(String);

impl Into<PortError> for ParseIntError {
    fn into(self) -> PortError {
        PortError(self.to_string())
    }
}

fn port(raw: &str) -> Result<u16, PortError> {
    let n = raw.parse::<u16>()?;
    Ok(n)
}

fn main() {
    println!("{:?}", port("80"));
}
```

- 컴파일되는가? 안 되면 **에러 번호**와, 진단이 이유로 드는 **트레이트 이름**은?
- ★ 7행의 `impl` 은 고아 규칙에 걸리는가?
- 같은 변환을 무엇으로 바꾸면 `?` 가 도는가?

### 4. ★★ 64비트에서 폭을 줄이고 늘리면 (예측)

```rust
// r29_narrow.rs
// 무손실만 From 이다 — u64 에서 u32 로
fn main() {
    let big: u64 = 5_000_000_000;
    let a = u32::from(big);
    let n: u32 = 7;
    let b = usize::from(n);
    println!("{} {}", a, b);
}
```

```rust
// r29_tryfrom.rs
// as 는 자르고 · TryFrom 은 묻고 · From 은 넓힌다
use std::convert::Infallible;

fn main() {
    let big: u64 = 5_000_000_000;
    println!("as u32          {}", big as u32);
    println!("u32::try_from   {:?}", u32::try_from(big));
    println!("u32::try_from 7 {:?}", u32::try_from(7_u64));
    println!("u64::from(7u32) {}", u64::from(7_u32));
    println!("usize try 7u32  {:?}", usize::try_from(7_u32));

    // ★ From 이 있으면 TryFrom 도 생긴다 — 실패할 수 없는 쪽으로
    let r: Result<u64, Infallible> = u64::try_from(7_u32);
    println!("넓히는 try_from {:?}", r);
}
```

- 앞 소스의 에러는 몇 건인가? **6행**(`usize::from(u32)`)은 64비트 머신에서도 에러인가?
- 뒤 소스의 여섯 줄 출력은 무엇인가? 특히 `big as u32` 의 값은?
- ★ 마지막 줄 `u64::try_from(7_u32)` 가 컴파일되는 이유는 — `TryFrom<u32> for u64` 를 누가 썼나?

### 5. ★★★ 빌린 모양으로 찾으면 (예측)

```rust
// r29_borrow.rs
// Borrow — HashMap<String, _> 을 &str 로 찾는 이유
use std::borrow::Borrow;
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};

type Map<K> = HashMap<K, i32, BuildHasherDefault<DefaultHasher>>;

fn hash_of<T: Hash + ?Sized>(x: &T) -> u64 {
    let mut h = DefaultHasher::new();
    x.hash(&mut h);
    h.finish()
}

// ★ Borrow<str> 을 달았는데 Hash 가 str 과 다르다
#[derive(PartialEq, Eq)]
struct Tagged(String);

impl Hash for Tagged {
    fn hash<H: Hasher>(&self, state: &mut H) {
        "tag".hash(state); // ★ 계약 위반 — str 의 해시와 달라진다
        self.0.hash(state);
    }
}

impl Borrow<str> for Tagged {
    fn borrow(&self) -> &str {
        &self.0
    }
}

fn main() {
    let mut m: Map<String> = Map::default();
    m.insert(String::from("kim"), 1);
    println!("String 키를 &str 로  {:?}", m.get("kim"));
    println!("해시 같나(String/str) {}", hash_of(&String::from("kim")) == hash_of("kim"));

    let mut t: Map<Tagged> = Map::default();
    t.insert(Tagged(String::from("kim")), 1);
    println!("Tagged 키를 &str 로  {:?}", t.get("kim"));
    println!("해시 같나(Tagged/str) {}", hash_of(&Tagged(String::from("kim"))) == hash_of("kim"));
    println!("Tagged 로 찾으면     {:?}", t.get(&Tagged(String::from("kim"))));
}
```

- 다섯 줄의 출력은 무엇인가? (해시값은 묻지 않는다 — **같은가 다른가**만)
- ★★ 셋째 줄과 다섯째 줄이 **다르다면** 왜 다른가? 값은 들어 있나?
- ★ 이 계약 위반을 컴파일러가 잡는가?

### 6. ★★ `AsRef` 만 단 키를 `&str` 로 찾으면 (예측)

```rust
// r29_asref_get.rs
// HashMap::get 은 AsRef 가 아니라 Borrow 를 요구한다
use std::collections::HashMap;

struct Name(String);

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

impl PartialEq for Name {
    fn eq(&self, o: &Self) -> bool {
        self.0 == o.0
    }
}
impl Eq for Name {}
impl std::hash::Hash for Name {
    fn hash<H: std::hash::Hasher>(&self, h: &mut H) {
        self.0.hash(h)
    }
}

fn main() {
    let mut m: HashMap<Name, i32> = HashMap::new();
    m.insert(Name(String::from("kim")), 1);
    println!("{:?}", m.get("kim"));
}
```

- 컴파일되는가? 안 되면 에러 번호와, rustc 가 **기대한 인자 타입**은?
- ★ 그 기대 타입은 **어디서** 나왔나 — `Name` 이 가진 `Borrow` 는 무엇인가?

### 7. 왜 std 는 `Into` 가 아니라 `From` 을 구현하라고 하나 (왜)

- 포괄 구현 `impl<T, U> Into<U> for T where U: From<T>` 에서 **조건은 어느 쪽에 걸려 있나**?
- 반대 방향 포괄 구현을 **함께** 두면 무엇이 곤란해지는가?
- ★ 그런데 **제네릭 함수의 경계**에는 왜 `Into` 를 권하나?

### 8. ★ `TryFrom` 의 실패 모양은 왜 연관 타입인가 (경계)

- `TryFrom<i32> for Percent` 에서 `i32` 는 제네릭 파라미터이고 `Error` 는 연관 타입이다. **왜 둘이 다른 도구인가**?
- ★ `From` 을 쓴 타입이 공짜로 받는 `TryFrom` 의 `Error` 는 무엇인가? 그 `Err` 갈래는 탈 수 있나?

### 9. ★★ `AsRef` 와 `Borrow` — 시그니처가 같은데 무엇이 다른가 (경계)

- 두 트레이트의 **계약** 차이를 한 문장으로 말할 수 있는가?
- 구조체의 **필드 하나**를 빌려 주는 것은 어느 쪽이 되고 어느 쪽이 안 되는가?
- ★ `HashMap::get` 이 `AsRef` 가 아니라 `Borrow` 를 요구하는 이유는?

### 10. ★ `impl Into<String>` 인자의 득실 (연결)

- ★★ `&str` 인자로 받아 안에서 `to_string()` 하는 것과 비교해 **무엇을 아끼는가**?
- 무엇을 **더 내는가** — 컴파일러가 이 함수를 몇 벌 만들 수 있는가?
- **읽기만** 하는 함수에도 쓸 만한가?

### 11. 다른 언어는 변환을 어떻게 다루나 (연결)

- ★★ Go 의 `%w` 래핑과 Rust 의 `?` + `From` 은 **언제**(컴파일/런타임) 오류를 바꾸는가? 원인을 **누가** 붙들고 있나?
- C# 의 `implicit` 변환 연산자 같은 **사용자 정의 암묵 변환**이 Rust 에 있는가?
- C++ 의 `{}` 좁히기 금지와 Rust 의 「`From` 이 없다」는 **무엇이 같고 무엇이 다른가**?
- ★ `From<u64> for u32` 를 내가 채우려 하면 무엇이 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
