# rust/syntax/28 — `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash` 의 계약 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **`--edition` 을 빼면 에디션 2015 다.** 이 갈래에서 그것은 「안 돌려 본 것」과 같다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).\
> 실험 파일 이름은 전부 **`ex.rs`** 로 고정했고 **진단의 줄 번호는 그 파일 기준**이다.\
> ★★★ **해시값은 한 번도 안 찍었다** — 흔들리는 칸이라 「**같은가 다른가**」만 근거로 쓴다.
> `HashMap` 은 **씨앗을 고정하고 키로 직접 읽으며**, 순회가 필요하면 **정렬해서** 찍는다.\
> ★ 패닉 첫 줄의 **OS 스레드 id 는 실행마다 바뀐다**(아래 6번 답) — `파일:줄:칸`·메시지·종료 코드는 안 바뀐다.
> ★ `rustc --explain E0277` · `E0369` · `E0407` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 채울 것이 없어서 비어 있다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
== 로 비교   true false
T: Eq 경계   2
(종료 코드 0)
```

**왜 그런가**

- **컴파일된다.** 출력은 `` == 로 비교   true false `` 와 `` T: Eq 경계   2 `` 두 줄이다
  (`[Id(1), Id(2), Id(1)]` 을 `HashSet` 에 넣으면 **2** 가 남는다).
- ★★ **몸통이 빈 것은 생략이 아니라 전부다** — **`Eq` 에는 메서드가 하나도 없다.**
  std 문서가 이유까지 적는다: `Eq` 가 더하는 조항은 **반사성(`a == a`)** 인데
  **컴파일러가 그것을 검사할 수 없어서** 메서드 대신 **표시**로 두었다.
- **그래서 `Eq` 가 하는 일은 하나다** — `` T: Eq `` 경계를 통과시키는 것.
  비교의 실체는 전부 `PartialEq::eq` 에 있고, `Eq` 를 달아도 `==` 의 동작은 **한 글자도 안 바뀐다.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0407]: method `eq2` is not a member of trait `Eq`
  --> ex.rs:13:5
   |
13 | /     fn eq2(&self, other: &Self) -> bool {
14 | |         // ★ Eq 에 없는 메서드
15 | |         self.0 == other.0
16 | |     }
   | |_____^ not a member of trait `Eq`

error[E0277]: the trait bound `Loose: Eq` is not satisfied
  --> ex.rs:34:47
   |
34 |     println!("{} {}", strict(&Id(1), &Id(1)), strict(&Loose(1), &Loose(1)));
   |                                               ^^^^^^ the trait `Eq` is not implemented for `Loose`
   |
note: required by a bound in `strict`
  --> ex.rs:29:14
   |
29 | fn strict<T: Eq>(a: &T, b: &T) -> bool {
   |              ^^ required by this bound in `strict`
help: consider annotating `Loose` with `#[derive(Eq)]`
   |
20 + #[derive(Eq)]
21 | struct Loose(u32);
   |

error: aborting due to 2 previous errors

Some errors have detailed explanations: E0277, E0407.
For more information about an error, try `rustc --explain E0277`.
(종료 코드 1)
```

- **에러는 2건**이고 번호는 **E0407** 과 **E0277** 이다.
  - **E0407** — `` method `eq2` is not a member of trait `Eq` ``.
    「**`Eq` 에는 그런 자리가 없다**」를 컴파일러가 직접 말해 준다. 1번 답의 증명이다.
  - **E0277** — `` the trait bound `Loose: Eq` is not satisfied ``.
- ★ **`Loose` 는 `==` 가 된다** — `PartialEq` 가 있기 때문이다. 못 넘는 것은 `` T: Eq `` 경계다.
  **`==` 를 쓸 수 있는 것과 「반사적이라고 약속한 것」은 다른 일**이고, 그 둘을 가르는 것이 이 표식이다.
  `help:` 가 `` consider annotating `Loose` with `#[derive(Eq)]` `` 를 권한다 — **한 줄이면 끝난다.**
- ★★★ **그 한 줄이 곧 약속이고, 컴파일러는 약속을 검사하지 않는다** — 3번 답이 그 증거다.

### 2. ★★★ 같은 키인데 답이 갈린다 — 값이 사라진다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
a == b 인가      true
해시가 같은가    false
넣은 뒤 len      1
a 로 꺼내면      Some(1)
b 로 꺼내면      None
contains_key(b)  false
또 넣은 뒤 len   2
남아 있는 키들   ["KEY", "key"]
a 로 꺼내면      Some(1)
(종료 코드 0)
```

**왜 그런가**

- ★★★ **계약이 깨진 지점은 첫 두 줄이다** — `a == b` 는 `true` 인데 **해시는 다르다**(`false`).
  `Hash` 의 계약은 **`k1 == k2` 이면 `hash(k1) == hash(k2)`** 한 줄이고, 그 한 줄이 여기서 어긋났다.
  `eq` 는 `to_lowercase()` 를 보는데 `hash` 는 **원문**을 섞기 때문이다.
- ★★★ **`m.get(&a)` 는 `Some(1)` 이고 `m.get(&b)` 는 `None` 이다.** `a == b` 인데 답이 갈린다.
  **표가 해시로 칸을 먼저 고르기 때문**이다 — 칸이 다르면 **`eq` 를 부를 기회조차 없다.**
  `contains_key(&b)` 도 같은 이유로 `false` 다.
- ★★ **덮어써지지 않는다.** `KEY` 를 또 넣으니 `len` 이 **2** 가 됐고,
  남은 키가 `` ["KEY", "key"] `` 둘이다. `HashMap` 의 불변식(「같은 키는 하나」)이 **밖에서 깨진 것**이다.
  마지막 줄에서 `` m.get(&a) `` 가 여전히 `Some(1)` 인 것이 그 증거다 — **새 값 `2` 는 다른 칸에 있다.**
- ★ **해시값 대신 「같은가」만 찍은 이유** — 해시값은 **흔들리는 칸**이다.
  기본 `RandomState` 는 프로세스마다 씨앗이 다르고, `DefaultHasher` 의 알고리즘도 안정 보장이 아니다.
  **계약은 값이 아니라** 「**좌변이 참일 때 우변도 참인가**」이므로 논리값만으로 충분하다.
  ★ 표 자체도 `` BuildHasherDefault<DefaultHasher> `` 로 **씨앗을 고정**했고, 순회는 **정렬해서** 찍었다.
- **고치는 곳은 한 줄이다** — `` self.0.hash(state) `` 를 `` self.0.to_lowercase().hash(state) `` 로.
  **`eq` 가 보는 것과 `hash` 가 섞는 것을 같게** 만들면 된다.
  ★ 더 안전한 길은 **생성자에서 소문자로 바꿔 저장**하는 것이다 — 그러면 둘 다 그냥 원문을 보면 되고 **실수할 자리가 없다.**

### 3. ★★★ 넣었는데 영영 못 꺼낸다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
k == k 인가   false
세 번 넣은 뒤 len  3
꺼내 보면          None
contains_key       false
remove             None
remove 뒤 len      3
순회로는 보인다    [1, 2, 3]
(종료 코드 0)
```

**왜 그런가**

- **컴파일된다.** `` impl Eq for Never {} `` 를 컴파일러는 **거부하지 않는다** —
  1번 답에서 본 대로 **검사할 메서드가 없기 때문**이다. `k == k` 가 `false` 인데 **반사적이라고 선언**했다.
- ★★★ **세 번 넣었는데 `len` 이 3 이다.** 같은 값인데 **같은 키로 안 세어진다**(`eq` 가 늘 거짓이라 셋이 다 남는다).
  그리고 `get` 은 `None`, `contains_key` 는 `false`, `remove` 도 `None` 이다.
  **칸은 제대로 찾는데**(해시는 정직하다) **`eq` 가 「아니다」라고 답해** 전부 지나친다.
- ★★ **`remove` 뒤에도 `len` 이 3 이다** — **지울 수조차 없다.**
  넣은 값이 **키로는 영영 닿을 수 없는 상태**로 갇힌다.
- ★ **순회로는 보인다**(`[1, 2, 3]`). **값은 거기 있는데 키로만 못 닿는 것** — 누수의 모양이다.
  ★ 값을 정렬해서 찍었다(순회 순서는 보장이 없다).
- ★★ **`f64` 도 같은 성질을 갖는다** — `NaN != NaN` 이라 반사성이 깨진다.
  그런데 **std 가 `f64` 에 `Eq` 를 주지 않았다.** 거짓말을 하는 대신 **표시를 안 다는 쪽**을 고른 것이다.
  그래서 `f64` 는 **`HashMap` 키가 아예 못 되고**(`Hash` 도 없다), 이 사고가 **언어 차원에서 미리 막힌다.**
  ★ 반대로 **내가 `impl Eq` 를 쓰는 순간 그 안전망을 내 손으로 걷어내는 것**이다.

### 4. ★★ `Ord` 가 없어 네 자리가 한꺼번에 막힌다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0277]: the trait bound `f64: Ord` is not satisfied
 --> ex.rs:9:7
  |
9 |     v.sort(); // ①
  |       ^^^^ the trait `Ord` is not implemented for `f64`
  |
  = help: the following other types implement trait `Ord`:
            i128
            i16
            i32
            i64
            i8
            isize
            u128
            u16
          and 4 others
note: required by a bound in `slice::<impl [T]>::sort`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/alloc/src/slice.rs:129:5

error[E0277]: the trait bound `f64: Ord` is not satisfied
  --> ex.rs:10:40
   |
10 |     println!("{:?}", v.iter().copied().max()); // ②
   |                                        ^^^ the trait `Ord` is not implemented for `f64`
   |
   = help: the following other types implement trait `Ord`:
             i128
             i16
             i32
             i64
             i8
             isize
             u128
             u16
           and 4 others
note: the method call chain might not have had the expected associated types
  --> ex.rs:10:31
   |
 8 |     let mut v = vec![3.0f64, 1.0, 2.0];
   |                 ---------------------- this expression has type `Vec<f64>`
 9 |     v.sort(); // ①
10 |     println!("{:?}", v.iter().copied().max()); // ②
   |                        ------ ^^^^^^^^ `Iterator::Item` changed to `f64` here
   |                        |
   |                        `Iterator::Item` is `&f64` here
note: required by a bound in `std::iter::Iterator::max`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:3163:5

error[E0277]: the trait bound `f64: Ord` is not satisfied
  --> ex.rs:11:24
   |
11 |     println!("{:?}", v.binary_search(&2.0)); // ③
   |                        ^^^^^^^^^^^^^ the trait `Ord` is not implemented for `f64`
   |
   = help: the following other types implement trait `Ord`:
             i128
             i16
             i32
             i64
             i8
             isize
             u128
             u16
           and 4 others
note: required by a bound in `core::slice::<impl [T]>::binary_search`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/slice/mod.rs:2881:5

error[E0277]: the trait bound `f64: Ord` is not satisfied
  --> ex.rs:14:7
   |
14 |     m.insert(1.0, "하나"); // ④
   |       ^^^^^^ the trait `Ord` is not implemented for `f64`
   |
   = help: the following other types implement trait `Ord`:
             i128
             i16
             i32
             i64
             i8
             isize
             u128
             u16
           and 4 others
note: required by a bound in `BTreeMap::<K, V, A>::insert`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/alloc/src/collections/btree/map.rs:1046:5

error: aborting due to 4 previous errors

For more information about this error, try `rustc --explain E0277`.
(종료 코드 1)
```

**왜 그런가**

- **첫 줄은 안 찍힌다** — **컴파일이 실패**하므로 프로그램이 아예 안 돈다.
  (비교 자체는 되는 코드다. `f64` 는 `PartialOrd` 이므로 `<` 도 `partial_cmp` 도 멀쩡하다.)
- **에러는 4건**이고 **전부 E0277**, 전부 같은 문구다 — `` the trait bound `f64: Ord` is not satisfied ``.

| 막힌 것 | 진단이 짚는 경계 |
|---|---|
| `v.sort()` | `` required by a bound in `slice::<impl [T]>::sort` `` |
| `.max()` | `` required by a bound in `std::iter::Iterator::max` `` |
| `binary_search(&2.0)` | `` required by a bound in `core::slice::<impl [T]>::binary_search` `` |
| `BTreeMap::insert` | `` required by a bound in `BTreeMap::<K, V, A>::insert` `` |

- ★★ **공통점은 넷 다** 「**전순서를 전제하는 연산**」이라는 것이다 — 정렬 · 최댓값 · 이분 탐색 · 균형 트리.
  **부분 순서로는 원리상 못 하는 일**이라 std 가 경계로 막았다.
  `NaN` 이 섞이면 「어느 것이 큰가」에 답이 없으므로 이 넷은 **의미가 성립하지 않는다.**
- ★ **진단이 std 소스의 줄까지 짚어 준다** — `` /rustc/ded5c06cf…/library/alloc/src/slice.rs:129:5 `` 처럼.
  「**내가 요구한 게 아니라 std 가 요구한다**」를 보여 주는 자리다.
  ★ 그 경로의 해시는 **이 rustc 판의 커밋**이다(판이 바뀌면 바뀐다).
- ★ **`.max()` 쪽에만 note 가 하나 더** 붙는다 —
  `` the method call chain might not have had the expected associated types `` 와 함께
  `iter()` 가 `&f64` 를 주고 `copied()` 가 `f64` 로 바꾼 지점을 짚어 준다.
  **체인 중간에서 타입이 바뀐 경우를 위한 추론 도우미**이고, 여기서는 오해가 아니었다.
- ★ `` help: the following other types implement trait `Ord` `` 가 **정수 타입 여덟에 `and 4 others`** 를 댄다.
  네 번 다 같은 목록이다.

### 5. ★★ `None` 에 `unwrap` 하면 죽는다 · `total_cmp` 는 정렬용이다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
warning: incorrect NaN comparison, NaN cannot be directly compared to itself
 --> ex.rs:6:37
  |
6 |     eprintln!("NAN == NAN      {}", f64::NAN == f64::NAN);
  |                                     ^^^^^^^^^^^^^^^^^^^^
  |
  = note: `#[warn(invalid_nan_comparisons)]` on by default
help: use `f32::is_nan()` or `f64::is_nan()` instead
  |
6 -     eprintln!("NAN == NAN      {}", f64::NAN == f64::NAN);
6 +     eprintln!("NAN == NAN      {}", f64::NAN.is_nan());
  |

warning: 1 warning emitted
===== ./ex =====
NAN == NAN      false
nan == nan      false
nan < 1.0       false
nan > 1.0       false
nan >= nan      false
partial_cmp     None
-0.0 == 0.0     true
[여기서 sort_by(partial_cmp().unwrap()) 을 던진다]

thread 'main' (875517) panicked at ex.rs:16:39:
called `Option::unwrap()` on a `None` value
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
(종료 코드 101)
```

**왜 그런가**

- **`[여기서 sort_by…]` 까지 찍히고 거기서 멈춘다.** 결과 줄은 **안 찍힌다.**
  종료 코드는 **101**(패닉)이고, 패닉 메시지는
  `` called `Option::unwrap()` on a `None` value `` · 자리는 `` ex.rs:16:39 `` 다.
- **`NaN` 은 네 비교가 전부 `false`** 다 — `==`·`<`·`>`·`>=` 어느 것도 참이 아니다.
  그리고 `partial_cmp` 가 **`None`** 을 낸다. 「모른다」가 아니라 「**비교할 수 없다**」는 답이고,
  `` .unwrap() `` 이 그 `None` 에서 죽는다.
  ★ 이 꼴(`` sort_by(|a, b| a.partial_cmp(b).unwrap()) ``)이 **f64 정렬의 가장 흔한 관용구**다.
- ★ **경고가 난다** — `` incorrect NaN comparison, NaN cannot be directly compared to itself `` 가
  **6번째 줄(`f64::NAN == f64::NAN`)에만** 붙는다.
  ★★ **바로 다음 줄의 `nan == nan` 에는 안 붙는다** — 값이 변수를 거치면 패턴이 안 맞기 때문이다.
  **린트는 계약 검사가 아니라 패턴 검사**이고, 그래서 **믿고 기댈 것이 못 된다.**
- ★ **`-0.0 == 0.0` 은 참이다.** 비트는 다른데 같다고 답한다.
- ★ **마커도 값도 전부 `eprintln!`** 이다 — 패닉이 표준 오류로 나오므로
  `println!` 과 섞으면 **파이프로 받을 때 순서가 갈린다.**
- ★ **패닉 첫 줄의 괄호 안 숫자는 OS 스레드 id 라 실행마다 바뀐다.**
  대조할 것은 **`파일:줄:칸`·메시지 본문·`note:` 줄·종료 코드**다.

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
total_cmp 로 정렬 [NaN, -inf, -0.0, 0.0, 1.0, 3.0, inf, NaN]
-0.0 total_cmp 0.0 Less
-0.0 ==       0.0  true
NAN total_cmp NAN  Equal
max_by(total_cmp)  Some(NaN)
min_by(total_cmp)  Some(NaN)
(종료 코드 0)
```

- ★★ **여덟 개의 순서는 `` [NaN, -inf, -0.0, 0.0, 1.0, 3.0, inf, NaN] ``** 이다.
  **`NaN` 이 양 끝에 하나씩** 있는데, 맨 앞의 것은 `` -f64::NAN ``(부호 비트가 켜진 NaN)이다.
  `total_cmp` 는 IEEE 754 의 `totalOrder` 를 그대로 구현한 것이라 **부호 비트부터** 본다(1.62.0\~).
- ★★★ **갈린다.** `` (-0.0).total_cmp(&0.0) `` 은 **`Less`** 인데 `` -0.0 == 0.0 `` 은 **`true`** 다.
  **같은 두 값에 두 답**이 나온다.
  ★ 그래서 **`Ord` 로 올리면 안 된다** — `Ord` 는 `partial_cmp` 와의 일치를 요구하고
  (`a == b` ⟺ `cmp` 가 `Equal`), 여기서 그 조항이 깨진다.
  **std 가 `f64: Ord` 를 안 주는 것이 잘못이 아니라 정확한 것**이다.
- `` NAN.total_cmp(&NAN) `` 은 **`Equal`** 이다 — `==` 는 `false` 인데.
  **「전순서를 빌려 온다」의 정확한 뜻이 이것**이다: **정렬용 순서이지 같음의 정의가 아니다.**
- ★ `max_by`·`min_by` 도 그 순서를 따르므로 **둘 다 `NaN`** 을 답한다(부호만 다르다).
  값의 최댓값이 필요했다면 이 함수가 아니다.

### 6. ★ 앞자리에서 갈리면 거기서 끝난다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Ver(1,9,9) < Ver(2,0,0)  true
Ver(1,2,3) < Ver(1,2,4)  true
정렬 [Ver(1, 0, 9), Ver(1, 2, 0), Ver(1, 2, 3), Ver(2, 0, 0)]
Low < High               true
정렬 [Low, Mid, High]
정렬 [Ping, Data(1), Data(9), Name("가")]
(종료 코드 0)
```

**왜 그런가**

- ★★ **`` Ver(1,9,9) < Ver(2,0,0) `` 은 참**이다. 정하는 것은 **필드 선언 순서**다 —
  `derive(PartialOrd)`·`derive(Ord)` 는 **사전식**이라 **앞자리부터 견주고 갈리면 거기서 끝낸다.**
  뒤 두 자리가 아무리 커도 첫 자리에서 이미 졌다.
  정렬 결과 `` [Ver(1,0,9), Ver(1,2,0), Ver(1,2,3), Ver(2,0,0)] `` 이 같은 규칙이다.
- ★★★ **[**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)의 `derive(PartialEq)` 와 갈리는 자리**다.
  거기서는 필드 순서가 **비용**만 바꿨는데(`&&` 는 결합적이다), 여기서는 **뜻을 바꾼다.**
  **필드 순서가 의미론이 되는 유일한 자리**이므로 함께 외운다.
- **enum 은 변형 선언 순서**가 먼저다 — `` Low < High `` 이고 정렬하면 `` [Low, Mid, High] `` 다.
  std 문서는 이것을 **판별자(discriminant) 순서**로 규정한다.
- **같은 변형끼리는 담긴 값**으로 갈린다 — `` [Ping, Data(1), Data(9), Name("가")] ``.
  `Data(9)` 가 `Name("가")` 앞인 것은 **값이 아니라 변형 순서** 때문이다.
- ★ **변형 순서를 나중에 바꾸면 정렬 결과가 조용히 바뀐다.** **컴파일은 통과한다** —
  타입도 시그니처도 안 바뀌기 때문이다. 우선순위·상태 등급을 enum 으로 쓰는 코드에서 아픈 자리다.

### 7. ★★ `Ord` 하나를 내고 순서를 받는다 — 그 `Ord` 가 거짓말이면

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
BTreeMap 그대로 {Id(1): "가", Id(2): "나", Id(3): "다"}
첫 · 마지막     Some((Id(1), "가")) Some((Id(3), "다"))
범위 Id(2)..    [(Id(2), "나"), (Id(3), "다")]
HashMap 정렬 후  [(Id(1), "가"), (Id(2), "나"), (Id(3), "다")]
(종료 코드 0)
```

**왜 그런가**

- **`BTreeMap` 이 요구하는 것은 `Ord` 뿐이다.** **`Hash` 는 필요 없다**(예제 타입에 있지만 안 쓴다).
  `HashMap` 쪽은 반대로 `Hash + Eq` 를 요구하고 `Ord` 는 안 쓴다.
- ★ **되돌려받는 것 셋** — ① **순회가 정렬 순서**다(넣은 순서 3·1·2 와 무관하게 `Id(1)`→`Id(2)`→`Id(3)`).
  ② **양 끝을 바로 집는다**(`first_key_value`·`last_key_value`).
  ③ **범위 질의**(`range(Id(2)..)`). **`HashMap` 에는 셋 다 없다.**
- ★★ **그리고 이것은 관찰이 아니라 계약**이다. 같은 프로그램의 `HashMap` 쪽은 **정렬해서 찍어야** 결정적이 된다 —
  그 줄이 이 대비를 보여 주려고 있다.

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
===== ./ex =====
Bad(1) == Bad(1)  true
Bad(1) < Bad(1)   true
세 번 넣은 뒤 len 3
Bad(1) 로 꺼내면  None
Bad(2) 로 꺼내면  None
Bad(3) 로 꺼내면  None
순회하면          [(3, 30), (2, 20), (1, 10)]
(종료 코드 0)
```

- **`cmp` 가 무엇과 견줘도 `Less` 를 낸다.** 그래서 `` Bad(1) == Bad(1) `` 이 `true` 인데
  `` Bad(1) < Bad(1) `` 도 `true` 다 — **전순서의 「정확히 하나」가 깨졌다.**
  ★ `PartialEq` 는 파생하고 `Ord` 만 손으로 쓴 것이 원인이다. **둘이 어긋났다.**
- ★★★ **셋을 넣었는데 `len` 은 3 이고 `get` 은 전부 `None`** 이다.
  트리가 탐색할 때마다 **왼쪽으로만 내려가** 엉뚱한 자리에 닿기 때문이다.
- ★ **순회하면 `` [(3, 30), (2, 20), (1, 10)] ``** — 넣은 **역순**이다.
  「정렬돼 있다」는 계약도 함께 깨졌다(늘 `Less` 라 새 키가 계속 맨 왼쪽으로 들어갔다).
- ★★ **2번·3번 답과 증상이 같다** — **`len` 은 늘고 `get` 은 `None`.**
  자료구조가 다르고 깨진 조항이 다른데 **밖에서 보이는 모양이 같다.**
  ★ 그래서 **「`get` 이 `None` 인데 `len` 은 맞다」를 보면 계약을 먼저 의심**한다.

### 8. ★ 대칭은 두 `impl` 을 쓰라는 계약이다

**출력.**

```text
===== 소스: ex.rs =====
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
===== rustc --edition 2021 ex.rs -o ex =====
error[E0369]: binary operation `==` cannot be applied to type `Cm`
  --> ex.rs:17:29
   |
17 |     println!("{}", Cm(2.54) == Inch(1.0)); // ★ 반대 방향
   |                    -------- ^^ --------- Inch
   |                    |
   |                    Cm
   |
note: an implementation of `PartialEq<Inch>` might be missing for `Cm`
  --> ex.rs:4:1
   |
 4 | struct Cm(f64);
   | ^^^^^^^^^ must implement `PartialEq<Inch>`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0369`.
(종료 코드 1)
```

**왜 그런가**

- **앞줄은 되고 뒷줄은 안 된다.** `` PartialEq<Rhs> `` 는 **다른 타입과의 비교**를 열어 주므로
  `` Inch(1.0) == Cm(2.54) `` 가 성립한다. 반대 방향은 **E0369** 다 —
  `` binary operation `==` cannot be applied to type `Cm` `` ·
  `` an implementation of `PartialEq<Inch>` might be missing for `Cm` ``.
- ★★ **대칭은 사람이 쓴다.** 컴파일러는 `` impl PartialEq<Cm> for Inch `` 에서
  `` impl PartialEq<Inch> for Cm `` 을 **만들어 주지 않는다.**
- ★ **더 나쁜 쪽은 둘 다 쓰되 답을 다르게 쓴 실수**다. 한쪽만 쓴 것은 **E0369 로 드러나지만**,
  둘 다 있고 답이 어긋나면 **컴파일도 통과하고 아무 말도 안 나온다** — 2번·3번 답과 같은 집안이다.
- ★ **std 가 남의 타입에 `PartialEq` 를 구현하지 말라고 권하는 이유**가 이것이다 —
  대칭 짝의 **반대쪽은 남의 크레이트에 있어서 내가 못 쓴다**
  ([**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙이 그 자리를 막는다).
  **반쪽만 있는 대칭**이 되어 계약이 원리상 안 지켜진다.

### 9. 검사할 수 있는 것과 없는 것을 갈랐다

- **합치면 `f64` 를 못 쓴다.** `f64` 는 `==` 가 필요한데 **반사성은 못 지킨다**(`NaN != NaN`).
  한 트레이트뿐이면 **`f64` 에 `==` 를 주려면 거짓말을 해야** 하고,
  안 주면 **부동소수점 비교가 아예 없는 언어**가 된다. 둘로 가르면 **정확히 필요한 만큼만** 줄 수 있다.
- ★ **`Eq` 가 더하는 조항은 하나** — **반사성** `a == a` 다. 대칭·추이는 `PartialEq` 가 이미 요구한다.
- **컴파일러가 못 검사하는 이유** — `eq` 는 **임의의 사용자 코드**다.
  「모든 `a` 에 대해 `a == a` 가 참인가」는 **프로그램의 의미를 증명하는 문제**라 타입 검사로는 안 된다.
  그래서 **메서드 없는 표식**으로 두고 **사람의 선언**을 받는다(1번 답).
- ★ **`PartialOrd`/`Ord` 도 같은 모양**이다 — `Ord` 가 더하는 것은 **전순서**(어느 둘이든 셋 중 정확히 하나)이고,
  그것도 검사가 안 된다. 다만 **`Ord` 에는 `cmp` 라는 메서드가 있다** — `Option` 을 안 내는 형태로 좁혔을 뿐이다.
  ★ **`Eq` 만 메서드가 없다**는 점에서 다섯 중 유일하다.

### 10. ★★ 조항은 여럿, 강제되는 것은 0

| 트레이트 | 약속하는 것 | 컴파일러가 강제하나 |
|---|---|---|
| `PartialEq` | **대칭**(`a == b` ⟺ `b == a`) · **추이**(`a == b`, `b == c` ⟹ `a == c`) | ✘ |
| `Eq` | 위에 더해 **반사**(`a == a`) | ✘ — **메서드가 없다** |
| `PartialOrd` | `partial_cmp` 와 `<`·`>`·`<=`·`>=`·`==` 의 **일관성** · **추이** · **쌍대**(`a < b` ⟺ `b > a`) | ✘ |
| `Ord` | **전순서** — 셋 중 정확히 하나 · `partial_cmp` 와 **일치**(`partial_cmp(a,b) == Some(cmp(a,b))`) | ✘ |
| `Hash` | ★★★ **`k1 == k2` ⟹ `hash(k1) == hash(k2)`** | ✘ |

- ★★★ **컴파일러가 강제하는 것은 0개**다. 강제되는 것은 **`impl` 이 있느냐**뿐이고
  내용은 전부 사람 몫이다. 3번 답이 그 극단이다 — **반사성을 정면으로 어긴 타입이 컴파일을 통과했다.**
- ★★ **std 는 이것을 「논리 오류(logic error)」라 부른다.**
  **동작이 규정되지 않지만 UB 는 아니다** — 문서가 그렇게 못 박고,
  그래서 **`unsafe` 코드가 이 트레이트들의 정확성에 기대면 안 된다**고 따로 적는다.
  ★ **메모리는 안전하고 답만 틀린다.** 크래시가 없으므로 **가장 늦게 발견된다.**
- ★ **「해시가 같으면 값도 같다」는 계약이 아니다.** 한 방향뿐이다 —
  해시가 같아도 값은 다를 수 있고(그것이 충돌이고 표가 `eq` 로 가린다).
  ★ 그래서 **`eq` 가 틀리면 충돌 처리까지 같이 틀린다.**
- ★★ **짝을 맞춰야 하는 두 쌍** — ① **`PartialEq` 와 `Hash`**(2번 답) ·
  ② **`Ord` 와 `PartialOrd`**(7번 답, `` Some(self.cmp(other)) `` 로 잇는다).
  하나를 손으로 쓰기 시작하면 **짝도 손으로** 쓴다.

### 11. 같은 계약, 다른 안전망

- **Java 의 `equals`/`hashCode`**([`java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/)) —
  ★ **계약 내용은 거의 같다**(반사·대칭·추이·일관성 + 「같으면 해시도 같다」).
  ★★ **다른 것은 안전망의 위치**다 — Java 는 `Object` 에 **기본 구현이 있어서**
  안 고쳐도 컴파일되고 실행되며 **참조 동등으로 조용히 동작**한다.
  Rust 는 `impl` 이 없으면 **아예 못 넣는다**(E0599 — 27번 주제의 3번 답).
  ★★★ **「깜빡함」이 Java 에서는 런타임 버그, Rust 에서는 컴파일 에러**다.
  ★ 다만 **「일부러 틀리게 쓴 것」은 두 언어 다 못 막는다** — 이 문서의 2·3·7번 답이 그 자리다.
- **Java 의 `Comparable`/`Comparator`**([`java/syntax/28-comparable-comparator/`](../../../java/syntax/28-comparable-comparator/)) —
  ★ **다른 것**: Java 의 정렬은 전순서 위반을 감지하면
  `` IllegalArgumentException: Comparison method violates its general contract! `` 을 **던져 주기도 한다.**
  ★★ **Rust 의 `BTreeMap` 은 안 던진다** — **조용히 값을 잃는다**(7번 답).
  Rust 쪽이 **더 빠르고 더 조용하다** — 검사 비용을 안 내는 대신 **증상이 늦게 온다.**
- **Kotlin 의 `data class`**([`kotlin/syntax/22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/)) —
  ★ **짝이 자동으로 맞는 이유**: `equals` 와 `hashCode` 를 **같은 목록(주 생성자 프로퍼티)에서 함께 생성**하기 때문이다.
  **한쪽만 고칠 방법이 없다.** Rust 의 `derive` 도 같은 성질이고(27번 주제),
  **사고는 손으로 쓰기 시작할 때만 난다.**
- **Go 의 맵**(Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **09번**) —
  ★ **비교 가능한 타입만 키로 받고 그 비교를 언어가 정한다.**
  사용자가 `Hash`/`Eq` 를 쓸 자리가 아예 없으므로 **이 사고가 원리상 안 난다.**
  ★ **대신 정규화도 못 한다** — 「대소문자 무시 키」 같은 것은 **키 자체를 미리 바꿔 넣는 수밖에** 없다
  (그것이 2번 답에서 권한 길과 같다는 것이 재미있는 자리다).

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` 가 `rustc --edition 2021 ex.rs -o ex` 로 컴파일하고 `./ex` 실행 | 배치 내내 + **제출 전 전수 재실행 1회** | `normalize-shaky.py` — **11블록 중 10 동일 · 1 은 스레드 id 만 다름** |
| ★★ **`Eq` 가 표식인 것** | `b28-01`(빈 `impl` 통과) · `b28-02`(E0407 + E0277) | 2 | `` not a member of trait `Eq` `` |
| ★★★ **`Hash` 계약 위반** | `b28-03` — `eq` 는 소문자, `hash` 는 원문 | 1 | `get(&b)` 이 **`None`** · `len` 이 **2** |
| ★★★ **반사성 위반** | `b28-04` — `eq` 가 늘 거짓 + `impl Eq` | 1 | `len` **3** · `get`·`remove` **전부 실패** |
| ★★ **`f64: Ord` 가 없는 것** | `b28-05` — sort · max · binary_search · BTreeMap | 1 | **E0277 ×4** — 전부 같은 문구 |
| ★ **`NaN` 과 패닉** | `b28-06` — 비교 다섯 + `partial_cmp().unwrap()` 정렬 | 1 | 종료 코드 **101** · 린트는 **리터럴만** 잡는다 |
| ★ **`total_cmp`** | `b28-07` — 여덟 값 정렬 + `-0.0` 대 `0.0` | 1 | `Less` 대 `true` — **두 답이 갈린다** |
| **사전식 순서** | `b28-08` — 구조체 · 유닛 enum · 데이터 enum | 1 | 셋 다 **선언 순서** |
| ★ **`BTreeMap`** | `b28-09`(정렬 순회·범위) · `b28-11`(거짓말하는 `Ord`) | 2 | 뒤엣것은 `len` 3 · `get` **전부 `None`** |
| **대칭** | `b28-10` — 한 방향만 구현 | 1 | **E0369** |
| ★★ **해시값** | **한 번도 안 찍었다** — 「같나 다르나」만 | 0 | ★ **흔들리는 칸이라 근거에서 뺐다** |
| ★ **`HashMap` 순회 순서** | **근거로 안 썼다** — 정렬해서만 찍었다 | 0 | ★ 보장이 없다 |
| **안 던져 본 것** — `f64::max` 의 NaN 처리 | 5번 답에서 **언급만** 했다 | 0 | ★ 블록이 없으므로 단정하지 않았다 |
| 외부 크레이트 | **쓰지 않음** | 0 | std 만 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| ★★ 계약을 어겼을 때 **정확히 어떤 출력이 나오나**(`None` · `len` 증가 · 역순 순회) | ★ std 가 「**동작이 규정되지 않는다**」고 못 박았다. **이 판의 관찰**이지 보장이 아니다 |
| 패닉 첫 줄 괄호 안의 **OS 스레드 id** | ★ 실행마다 바뀐다 — `normalize-shaky.py` 가 정규화한다 |
| `` incorrect NaN comparison `` 린트가 **리터럴만** 잡는 것 | ★ 린트의 패턴이다. 넓어질 수 있다 |
| 진단에 박히는 `/rustc/ded5c06cf…/…` 경로 | ★ **이 rustc 판의 커밋 해시**다 |
| `` help: the following other types implement trait `Ord` `` 의 **목록과 `and 4 others`** | ★ 진단 품질·std 구성에 달렸다 |
| **해시값**과 **`HashMap` 순회 순서** | ★ **보장 없음** — 근거로 쓰지 않았다 |
| `` -f64::NAN `` 이 `total_cmp` 순서에서 **맨 앞**인 것 | ★ 이것은 IEEE 754 `totalOrder` 의 **보장**이다(부호 비트부터 본다) |

★ **다시 찍는 법** — `capture.sh` 를 그대로 돌리고 `normalize-shaky.py` 로 견준다.
**`b28-06` 한 블록만 스레드 id 가 달라져야** 하고(설계상 불일치), 나머지는 한 글자도 같아야 한다.
