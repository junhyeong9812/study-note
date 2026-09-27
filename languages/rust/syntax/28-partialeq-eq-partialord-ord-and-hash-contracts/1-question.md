# rust/syntax/28 — `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash` 의 계약 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 ex.rs -o ex && ./ex`.
> ★★ **`--edition` 을 빼면 에디션 2015 로 돌아간다** — 답을 맞춰도 다른 언어를 컴파일한 것이다.
> ★★ **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **이 주제는 계약형 주제다.** 「지켜야 한다」로 답하지 말고
> 「**어기면 무슨 출력이 나오나**」로 답하라 — 그래서 (경계) 문항에도 코드가 붙는다.
> ★★★ **해시값을 외우려 들지 마라.** 값은 실행마다 바뀐다 — 답할 것은 「**같은가 다른가**」다.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다.

> ★ 아래 코드 펜스의 **첫 줄 `// bNN-….rs` 는 캡처 원본 파일 이름**이고, 그 아래 `// ex.rs` 가 **컴파일할 때의 이름**이다.
> 캡처 스크립트가 원본을 `ex.rs` 로 복사해 던지므로 **진단에 박히는 파일명은 언제나 `ex.rs`** 다.
> 펜스가 실파일과 한 글자도 같은지는 `check-source-fences.py` 가 기계로 대조했다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 몸통이 빈 `impl` 과, 거기에 메서드를 넣으면 (예측)

```rust
// b28-01.rs
// ex.rs
// Eq 는 메서드가 없는 표식 트레이트다 — impl 의 몸통이 비어 있다
use std::collections::HashSet;
use std::collections::hash_map::DefaultHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};

#[derive(Debug, Clone)]
struct Id(u32);

impl PartialEq for Id {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0 // ★ 메서드는 여기에만 있다
    }
}

impl Eq for Id {} // ★ 몸통이 비어 있다 — 채울 것이 없다

impl Hash for Id {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.hash(state);
    }
}

fn dedup<T: Eq + Hash + Clone>(items: &[T]) -> usize {
    let mut s: HashSet<T, BuildHasherDefault<DefaultHasher>> = HashSet::default();
    for it in items {
        s.insert(it.clone());
    }
    s.len()
}

fn main() {
    println!("== 로 비교   {} {}", Id(1) == Id(1), Id(1) == Id(2));
    println!("T: Eq 경계   {}", dedup(&[Id(1), Id(2), Id(1)]));
}
```

```rust
// b28-02.rs
// ex.rs
// 표식 트레이트에 메서드를 넣어 보면 · 표식을 안 달고 T: Eq 를 쓰면
#[derive(Debug)]
struct Id(u32);

impl PartialEq for Id {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0
    }
}

impl Eq for Id {
    fn eq2(&self, other: &Self) -> bool {
        // ★ Eq 에 없는 메서드
        self.0 == other.0
    }
}

#[derive(Debug)]
struct Loose(u32);

impl PartialEq for Loose {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0
    }
}
// ★ impl Eq for Loose 가 없다

fn strict<T: Eq>(a: &T, b: &T) -> bool {
    a == b
}

fn main() {
    println!("{} {}", strict(&Id(1), &Id(1)), strict(&Loose(1), &Loose(1)));
}
```

- 앞 소스는 컴파일되는가? 두 줄의 출력은 무엇인가?
- ★★ `` impl Eq for Id {} `` 의 몸통이 **비어 있는 이유**는 무엇인가 — 채울 것이 **정말 없는가**?
- 뒤 소스의 에러는 **몇 건**이고 **번호**는 무엇인가?
- ★ `Loose` 는 `==` 가 되는데 왜 `` T: Eq `` 경계를 못 넘는가?

### 2. ★★★ 대소문자를 무시하게 고쳤더니 (예측)

```rust
// b28-03.rs
// ex.rs
// ★ 계약 위반 ① — k1 == k2 인데 hash(k1) != hash(k2) 이면 값이 사라진다
// 해시 씨앗을 고정한다(기본 RandomState 는 실행마다 달라진다)
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};

#[derive(Debug)]
struct CaseKey(String);

impl PartialEq for CaseKey {
    fn eq(&self, other: &Self) -> bool {
        self.0.to_lowercase() == other.0.to_lowercase() // 대소문자를 무시한다
    }
}

impl Eq for CaseKey {}

impl Hash for CaseKey {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.hash(state); // ★ 원문 그대로 — 여기가 계약 위반이다
    }
}

type Map = HashMap<CaseKey, i32, BuildHasherDefault<DefaultHasher>>;

fn same_hash(a: &CaseKey, b: &CaseKey) -> bool {
    // ★ 해시값은 안 찍는다 — 「같나 다르나」만 본다
    let mut ha = DefaultHasher::new();
    let mut hb = DefaultHasher::new();
    a.hash(&mut ha);
    b.hash(&mut hb);
    ha.finish() == hb.finish()
}

fn main() {
    let a = CaseKey(String::from("key"));
    let b = CaseKey(String::from("KEY"));
    println!("a == b 인가      {}", a == b);
    println!("해시가 같은가    {}", same_hash(&a, &b));

    let mut m: Map = Map::default();
    m.insert(CaseKey(String::from("key")), 1);
    println!("넣은 뒤 len      {}", m.len());
    println!("a 로 꺼내면      {:?}", m.get(&a));
    println!("b 로 꺼내면      {:?}", m.get(&b)); // ★ 같은 키인데
    println!("contains_key(b)  {}", m.contains_key(&b));

    m.insert(CaseKey(String::from("KEY")), 2);
    println!("또 넣은 뒤 len   {}", m.len()); // ★ 같은 키가 둘
    let mut keys: Vec<String> = m.keys().map(|k| k.0.clone()).collect();
    keys.sort(); // ★ 순회 순서는 보장이 없으므로 정렬해서 찍는다
    println!("남아 있는 키들   {:?}", keys);
    println!("a 로 꺼내면      {:?}", m.get(&a));
}
```

- 아홉 줄의 출력을 **한 글자도 안 틀리게** 적을 수 있는가?
- ★★★ `a == b` 인데 **`m.get(&a)` 와 `m.get(&b)` 의 답이 갈리는가**? 갈린다면 왜인가?
- ★★ 같은 키를 또 넣었을 때 `len` 은 얼마가 되는가 — **덮어써지는가**?
- ★ 이 프로그램이 **해시값 대신 「같은가」만** 찍는 이유는?
- 고치려면 **어느 한 줄**을 어떻게 바꾸는가?

### 3. ★★★ 자기 자신과 다르다고 답하는 타입 (예측)

```rust
// b28-04.rs
// ex.rs
// ★ 계약 위반 ② — 반사성을 깨면 넣은 값을 영영 못 꺼낸다
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{BuildHasherDefault, Hash, Hasher};

#[derive(Debug)]
struct Never(u32);

impl PartialEq for Never {
    fn eq(&self, _other: &Self) -> bool {
        false // ★ 자기 자신과도 다르다 — a == a 가 거짓
    }
}

impl Eq for Never {} // ★ 거짓말이다. 컴파일러는 못 막는다

impl Hash for Never {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.0.hash(state); // 해시는 정직하다
    }
}

type Map = HashMap<Never, i32, BuildHasherDefault<DefaultHasher>>;

fn main() {
    let k = Never(7);
    println!("k == k 인가   {}", k == k);

    let mut m: Map = Map::default();
    m.insert(Never(7), 1);
    m.insert(Never(7), 2);
    m.insert(Never(7), 3);
    println!("세 번 넣은 뒤 len  {}", m.len());
    println!("꺼내 보면          {:?}", m.get(&k));
    println!("contains_key       {}", m.contains_key(&k));
    println!("remove             {:?}", m.remove(&k));
    println!("remove 뒤 len      {}", m.len());

    let mut vals: Vec<i32> = m.values().copied().collect();
    vals.sort();
    println!("순회로는 보인다    {:?}", vals);
}
```

- 컴파일되는가? `` impl Eq for Never {} `` 를 컴파일러가 **거부하는가**?
- ★★★ 세 번 넣은 뒤 `len` 은? `get`·`contains_key`·`remove` 는 각각 무엇을 답하는가?
- ★★ `remove` 뒤의 `len` 은 얼마인가 — **지울 수는 있는가**?
- ★ 순회하면 값이 보이는가? 보인다면 그것은 무슨 상태인가?
- ★★ `f64` 가 **같은 성질**을 가졌는데 이 사고가 안 나는 이유는?

### 4. ★★ `f64` 를 정렬하려 하면 (예측)

```rust
// b28-05.rs
// ex.rs
// f64 는 PartialOrd 는 되고 Ord 는 안 된다 — 네 자리가 한꺼번에 막힌다
use std::collections::BTreeMap;

fn main() {
    println!("비교는 된다 {} {}", 1.0f64 < 2.0f64, 1.0f64.partial_cmp(&2.0) == Some(std::cmp::Ordering::Less));

    let mut v = vec![3.0f64, 1.0, 2.0];
    v.sort(); // ①
    println!("{:?}", v.iter().copied().max()); // ②
    println!("{:?}", v.binary_search(&2.0)); // ③

    let mut m: BTreeMap<f64, &str> = BTreeMap::new();
    m.insert(1.0, "하나"); // ④
    println!("{:?}", m);
}
```

- 첫 줄은 찍히는가? 에러는 **몇 건**이고 **번호**는?
- ★★ 막힌 네 자리는 각각 무엇이며, **공통점**은 무엇인가?
- ★ 진단이 「누가 그 경계를 요구했는지」를 어떻게 보여 주는가?
- `.max()` 쪽에만 붙는 `note:` 는 무엇을 말하는가?

### 5. ★★ `NaN` 을 섞어 정렬하면 · 전순서를 빌려 오면 (예측)

```rust
// b28-06.rs
// ex.rs
// NaN 이 하는 일 · partial_cmp().unwrap() 으로 정렬하면
// ★ 마커도 값도 전부 표준 오류로 찍는다(패닉과 섞이지 않게)
fn main() {
    let nan = f64::NAN;
    eprintln!("NAN == NAN      {}", f64::NAN == f64::NAN);
    eprintln!("nan == nan      {}", nan == nan);
    eprintln!("nan < 1.0       {}", nan < 1.0);
    eprintln!("nan > 1.0       {}", nan > 1.0);
    eprintln!("nan >= nan      {}", nan >= nan);
    eprintln!("partial_cmp     {:?}", nan.partial_cmp(&1.0));
    eprintln!("-0.0 == 0.0     {}", -0.0f64 == 0.0f64);

    let mut v = vec![3.0f64, f64::NAN, 1.0];
    eprintln!("[여기서 sort_by(partial_cmp().unwrap()) 을 던진다]");
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    eprintln!("[이 줄은 안 찍힌다] {:?}", v);
}
```

```rust
// b28-07.rs
// ex.rs
// total_cmp — 전순서를 빌려 와 정렬한다
fn main() {
    let mut v = vec![
        3.0f64,
        f64::NAN,
        1.0,
        -0.0,
        0.0,
        f64::NEG_INFINITY,
        f64::INFINITY,
        -f64::NAN,
    ];
    v.sort_by(f64::total_cmp);
    println!("total_cmp 로 정렬 {:?}", v);
    println!("-0.0 total_cmp 0.0 {:?}", (-0.0f64).total_cmp(&0.0));
    println!("-0.0 ==       0.0  {}", -0.0f64 == 0.0f64);
    println!("NAN total_cmp NAN  {:?}", f64::NAN.total_cmp(&f64::NAN));
    println!("max_by(total_cmp)  {:?}", v.iter().copied().max_by(f64::total_cmp));
    println!("min_by(total_cmp)  {:?}", v.iter().copied().min_by(f64::total_cmp));
}
```

- 앞 소스는 **어디까지 찍히고** 어디서 멈추는가? **종료 코드**는?
- ★ 컴파일 경고가 나는가? 난다면 **어느 줄**에 나고 **어느 줄에는 안 나는가**?
- ★★ 뒤 소스의 정렬 결과 **여덟 개의 순서**를 적을 수 있는가?
- ★★★ `` -0.0 `` 과 `` 0.0 `` 에 대해 `total_cmp` 와 `==` 의 답이 **갈리는가**?
  갈린다면 `total_cmp` 를 `Ord` 로 올려도 되는가?
- `` NAN.total_cmp(&NAN) `` 은 무엇인가?

### 6. ★ 세 가지를 정렬하면 (예측)

```rust
// b28-08.rs
// ex.rs
// derive(PartialOrd)·derive(Ord) 는 사전식이다 — 구조체는 필드 순서, enum 은 변형 순서
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
struct Ver(u32, u32, u32);

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
enum Level {
    Low,
    Mid,
    High,
}

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
enum Msg {
    Ping,
    Data(u32),
    Name(String),
}

fn main() {
    println!("Ver(1,9,9) < Ver(2,0,0)  {}", Ver(1, 9, 9) < Ver(2, 0, 0));
    println!("Ver(1,2,3) < Ver(1,2,4)  {}", Ver(1, 2, 3) < Ver(1, 2, 4));
    let mut v = vec![Ver(1, 2, 3), Ver(1, 0, 9), Ver(2, 0, 0), Ver(1, 2, 0)];
    v.sort();
    println!("정렬 {:?}", v);

    println!("Low < High               {}", Level::Low < Level::High);
    let mut l = vec![Level::High, Level::Low, Level::Mid];
    l.sort();
    println!("정렬 {:?}", l);

    // 변형 순서가 먼저, 같은 변형 안에서는 담긴 값
    let mut m = vec![
        Msg::Data(9),
        Msg::Ping,
        Msg::Name(String::from("가")),
        Msg::Data(1),
    ];
    m.sort();
    println!("정렬 {:?}", m);
}
```

- 여섯 줄의 출력을 적을 수 있는가?
- ★★ `` Ver(1,9,9) < Ver(2,0,0) `` 은 참인가 거짓인가 — **무엇이 그것을 정하는가**?
- enum 셋은 무엇을 기준으로 줄을 서는가 — **담긴 값인가 변형 순서인가**?
- ★ 변형 순서를 나중에 바꾸면 무엇이 일어나는가? **컴파일은 통과하는가**?

### 7. ★★ `BTreeMap` 이 요구하는 것과, 그 요구가 거짓말이면 (경계)

```rust
// b28-09.rs
// ex.rs
// BTreeMap 은 Ord 를 요구하고, 그 대가로 순회가 결정적이다
use std::collections::{BTreeMap, HashMap};

#[derive(Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Clone, Copy)]
struct Id(u32);

fn main() {
    let mut b: BTreeMap<Id, &str> = BTreeMap::new();
    for (k, v) in [(3, "다"), (1, "가"), (2, "나")] {
        b.insert(Id(k), v);
    }
    println!("BTreeMap 그대로 {:?}", b);
    println!("첫 · 마지막     {:?} {:?}", b.first_key_value(), b.last_key_value());
    println!("범위 Id(2)..    {:?}", b.range(Id(2)..).collect::<Vec<_>>());

    let mut h: HashMap<Id, &str> = HashMap::new();
    for (k, v) in [(3, "다"), (1, "가"), (2, "나")] {
        h.insert(Id(k), v);
    }
    // ★ HashMap 의 순회 순서는 보장이 없다 — 정렬해서 찍는다
    let mut items: Vec<(Id, &str)> = h.into_iter().collect();
    items.sort();
    println!("HashMap 정렬 후  {:?}", items);
}
```

```rust
// b28-11.rs
// ex.rs
// ★ 계약 위반 ③ — Ord 가 거짓말을 하면 BTreeMap 에서도 값이 사라진다
use std::cmp::Ordering;
use std::collections::BTreeMap;

#[derive(Debug, PartialEq, Eq)]
struct Bad(u32);

impl Ord for Bad {
    fn cmp(&self, _other: &Self) -> Ordering {
        Ordering::Less // ★ 무엇과 견줘도 「작다」 — 전순서가 아니다
    }
}

impl PartialOrd for Bad {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn main() {
    println!("Bad(1) == Bad(1)  {}", Bad(1) == Bad(1));
    println!("Bad(1) < Bad(1)   {}", Bad(1) < Bad(1));

    let mut m: BTreeMap<Bad, i32> = BTreeMap::new();
    m.insert(Bad(1), 10);
    m.insert(Bad(2), 20);
    m.insert(Bad(3), 30);
    println!("세 번 넣은 뒤 len {}", m.len());
    println!("Bad(1) 로 꺼내면  {:?}", m.get(&Bad(1)));
    println!("Bad(2) 로 꺼내면  {:?}", m.get(&Bad(2)));
    println!("Bad(3) 로 꺼내면  {:?}", m.get(&Bad(3)));
    println!("순회하면          {:?}", m.iter().map(|(k, v)| (k.0, *v)).collect::<Vec<_>>());
}
```

- `BTreeMap` 은 무엇을 요구하는가 — `Hash` 도 필요한가?
- ★ `Ord` 를 요구한 대가로 **되돌려받는 것 셋**은 무엇인가?
- ★★★ 뒤 소스에서 셋을 넣은 뒤 `len` 은? `get` 은 무엇을 답하는가?
- ★★ 순회하면 어떤 순서로 나오는가 — 2번·3번 답과 **증상이 같은가**?

### 8. ★ 다른 타입끼리 비교하면 (경계)

```rust
// b28-10.rs
// ex.rs
// 대칭은 계약이지 문법이 아니다 — 한쪽만 구현하면 반대 방향이 없다
#[derive(Debug)]
struct Cm(f64);

#[derive(Debug)]
struct Inch(f64);

impl PartialEq<Cm> for Inch {
    fn eq(&self, other: &Cm) -> bool {
        (self.0 * 2.54 - other.0).abs() < 1e-9
    }
}

fn main() {
    println!("{}", Inch(1.0) == Cm(2.54));
    println!("{}", Cm(2.54) == Inch(1.0)); // ★ 반대 방향
}
```

- 앞줄은 컴파일되는가? 뒷줄은?
- ★★ **대칭**은 컴파일러가 만들어 주는가, 사람이 쓰는가?
- ★ 한쪽만 쓴 실수와 **둘 다 쓰되 답을 다르게 쓴** 실수 중 어느 쪽이 더 나쁜가?
- std 문서가 **남의 타입에 `PartialEq` 를 구현하지 말라**고 권하는 이유는?

### 9. 왜 `PartialEq` 와 `Eq` 를 갈랐나 (왜)

- 한 트레이트로 합치면 무엇이 곤란해지는가?
- ★ `Eq` 가 더하는 조항은 **하나**다. 무엇인가?
- 그 조항을 **컴파일러가 검사할 수 없는** 이유는?
- `PartialOrd` 와 `Ord` 의 갈림도 같은 모양인가?

### 10. ★★ 계약 전수 — 무엇이 강제되나 (경계)

- 다섯 트레이트가 약속하는 조항을 **전부** 셀 수 있는가?
- ★★★ 그중 **컴파일러가 강제하는 것은 몇 개**인가?
- ★★ 어긴 결과를 std 는 무엇이라 부르는가 — 그것은 **UB 인가**?
- ★ 「해시가 같으면 값도 같다」는 계약인가?
- 손으로 쓸 때 **짝을 맞춰야 하는 두 쌍**은 무엇과 무엇인가?

### 11. 다른 언어는 이 계약을 어떻게 다루나 (연결)

- Java 의 `equals`/`hashCode` 와 계약 **내용**이 다른가? 다른 것은 무엇인가?
- ★★ 「깜빡하고 안 고쳤을 때」 Java 와 Rust 에서 **무엇이 다른가**?
- Java 의 `Comparable` 은 전순서 위반을 **던져 주기도 한다**. Rust 의 `BTreeMap` 은?
- Kotlin 의 `data class` 는 왜 이 짝이 **자동으로 맞는가**?
- Go 의 맵에는 왜 이 사고가 **원리상 안 나는가** — 대신 무엇을 못 하는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
