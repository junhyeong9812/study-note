# rust/syntax/39 — `HashMap` 대 `BTreeMap` — 무엇을 고르나, `entry` API — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·에러는 **`rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu`** 에서
> **`rustc --edition 2021`** 로 실제로 돌려 받은 것이다(대비는 `Python 3.12.3` · `node v18.19.1`).\
> ★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ 블록 첫 줄 `===== 소스: <파일> =====` 아래가 **컴파일한 소스 전문**이고, **진단의 줄 번호는 그 파일 기준**이다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음). **시간은 한 번도 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `HashMap` 6 가지(3! 전부) · `BTreeMap` 1 가지

**출력.**

```text
===== 소스: r39_order.sh =====
# 프로세스를 따로 300번 띄워 순회 순서가 몇 가지 나오는지 센다
rustc --edition 2021 -o r39_order r39_order.rs
for kind in hash btree; do
  n=$(for i in $(seq 1 300); do ./r39_order $kind; done | sort -u | wc -l)
  echo "$kind: distinct orders over 300 runs = $n"
done
echo "btree line: $(./r39_order btree)"
===== bash r39_order.sh =====
hash: distinct orders over 300 runs = 6
btree: distinct orders over 300 runs = 1
btree line: fig kiwi plum
(exit 0)
```

**왜 그런가.**

- ★★★ **`hash` 6 · `btree` 1 · `btree line: fig kiwi plum`.** 키 셋에서 가능한 순서는 **3! = 6** — `HashMap` 은 **그 전부**를 냈다.
- ★★ `HashMap` 은 **실행마다 씨앗이 바뀐다**(std — 「randomly seeded」 · 「each `HashMap` instance uses a different seed」). 순회는 「**arbitrary order**」.
- ★ `BTreeMap` 은 **키 순서**(`&str` 의 바이트 순) — std 보장. ★ 이 블록은 **한 판의 `HashMap` 순서를 싣지 않는다** — 그것은 흔들린다. **가짓수**가 흔들리지 않는 칸이다.

### 2. ★★★ 없는 키 `2 · 3 · 1` / 있는 키 `1 · 2 · 1` — `BTreeMap` `25 · 8` / `8 · 4`

**출력.**

```text
===== 소스: r39_entry.rs =====
// 키 타입에 계수기를 심어 hash · eq · cmp 가 몇 번 불리는지 센다
use std::cell::Cell;
use std::cmp::Ordering;
use std::collections::hash_map::DefaultHasher;
use std::collections::{BTreeMap, HashMap};
use std::hash::{BuildHasherDefault, Hash, Hasher};

thread_local! {
    static HASH: Cell<u32> = Cell::new(0);
    static EQ: Cell<u32> = Cell::new(0);
    static CMP: Cell<u32> = Cell::new(0);
}

#[derive(Clone, Copy)]
struct K(u32);

impl Hash for K {
    fn hash<H: Hasher>(&self, h: &mut H) {
        HASH.with(|c| c.set(c.get() + 1));
        self.0.hash(h);
    }
}
impl PartialEq for K {
    fn eq(&self, o: &Self) -> bool {
        EQ.with(|c| c.set(c.get() + 1));
        self.0 == o.0
    }
}
impl Eq for K {}
impl PartialOrd for K {
    fn partial_cmp(&self, o: &Self) -> Option<Ordering> {
        Some(self.cmp(o))
    }
}
impl Ord for K {
    fn cmp(&self, o: &Self) -> Ordering {
        CMP.with(|c| c.set(c.get() + 1));
        self.0.cmp(&o.0)
    }
}

fn reset() {
    HASH.with(|c| c.set(0));
    EQ.with(|c| c.set(0));
    CMP.with(|c| c.set(0));
}
fn counts() -> (u32, u32, u32) {
    (HASH.with(|c| c.get()), EQ.with(|c| c.get()), CMP.with(|c| c.get()))
}

type Map = HashMap<K, u32, BuildHasherDefault<DefaultHasher>>;

fn fresh() -> Map {
    let mut m = Map::with_capacity_and_hasher(64, Default::default());
    for i in 0..8 {
        m.insert(K(i), 0);
    }
    m
}

fn fresh_tree() -> BTreeMap<K, u32> {
    (0..8).map(|i| (K(i), 0)).collect()
}

fn main() {
    let absent = K(100);
    let present = K(3);

    for (label, key) in [("absent ", absent), ("present", present)] {
        let mut m = fresh();
        reset();
        if !m.contains_key(&key) {
            m.insert(key, 0);
        }
        let (h, e, _) = counts();
        println!("[A] {label}  HashMap  contains_key + insert             hash {h}  eq {e}");

        let mut m = fresh();
        reset();
        if !m.contains_key(&key) {
            m.insert(key, 0);
        }
        *m.get_mut(&key).unwrap() += 1;
        let (h, e, _) = counts();
        println!("[B] {label}  HashMap  contains_key + insert + get_mut   hash {h}  eq {e}");

        let mut m = fresh();
        reset();
        *m.entry(key).or_insert(0) += 1;
        let (h, e, _) = counts();
        println!("[C] {label}  HashMap  entry().or_insert() += 1          hash {h}  eq {e}");
    }

    for (label, key) in [("absent ", absent), ("present", present)] {
        let mut t = fresh_tree();
        reset();
        if !t.contains_key(&key) {
            t.insert(key, 0);
        }
        *t.get_mut(&key).unwrap() += 1;
        let (_, _, c) = counts();
        println!("[D] {label}  BTreeMap contains_key + insert + get_mut   cmp {c}");

        let mut t = fresh_tree();
        reset();
        *t.entry(key).or_insert(0) += 1;
        let (_, _, c) = counts();
        println!("[E] {label}  BTreeMap entry().or_insert() += 1          cmp {c}");
    }
}
===== rustc --edition 2021 r39_entry.rs =====
(exit 0)
===== ./r39_entry =====
[A] absent   HashMap  contains_key + insert             hash 2  eq 0
[B] absent   HashMap  contains_key + insert + get_mut   hash 3  eq 1
[C] absent   HashMap  entry().or_insert() += 1          hash 1  eq 0
[A] present  HashMap  contains_key + insert             hash 1  eq 1
[B] present  HashMap  contains_key + insert + get_mut   hash 2  eq 2
[C] present  HashMap  entry().or_insert() += 1          hash 1  eq 1
[D] absent   BTreeMap contains_key + insert + get_mut   cmp 25
[E] absent   BTreeMap entry().or_insert() += 1          cmp 8
[D] present  BTreeMap contains_key + insert + get_mut   cmp 8
[E] present  BTreeMap entry().or_insert() += 1          cmp 4
(exit 0)
```

**왜 그런가.**

- ★★★ **없는 키** — `[A]` `hash 2 eq 0`(`contains_key` 1 + `insert` 1) · `[B]` `hash 3 eq 1`(+ `get_mut` 1 — 넣은 것을 찾아 `eq` 1) · **`[C]` `hash 1 eq 0`**.
- ★★★ **있는 키** — `[A]` `hash 1 eq 1`(찾았으니 `insert` 안 함) · `[B]` `hash 2 eq 2` · **`[C]` `hash 1 eq 1`**. **`entry` 는 있든 없든 한 번 찾는다.**
- ★★ **`BTreeMap`** — 없는 키 `[D]` **`cmp 25`** 대 `[E]` **`cmp 8`** · 있는 키 **`cmp 8`** 대 **`cmp 4`**. 찾기 한 번이 `cmp` 여러 번이라 차이가 **탐색 분량씩** 벌어진다.
- ★ **해셔 고정의 이유** — `hash` **횟수**는 씨앗과 무관하지만, **`eq` 횟수는 씨앗이 바꿀 수 있다**(해시가 우연히 겹친 칸마다 `eq` 로 맞춰 본다). 그래서 씨앗을 고정해 `eq` 칸도 **안 흔들리게** 했다([28번 주제](../28-partialeq-eq-partialord-ord-and-hash-contracts/)의 방식). 또 **용량을 64 로 미리 잡아** 재할당을 뺐다.

### 3. ★★ `old`·`new1`·`new2` 세 번 — `or_insert` 는 있어도 만든다

**출력.**

```text
===== 소스: r39_lazy.rs =====
use std::collections::HashMap;

fn make(tag: &str) -> Vec<&'static str> {
    println!("    make() called for {tag}");
    Vec::new()
}

fn main() {
    let mut m: HashMap<&str, Vec<&str>> = HashMap::new();
    m.insert("old", vec!["x"]);

    println!("[1] or_insert(make(..))");
    m.entry("old").or_insert(make("old")).push("a");
    m.entry("new1").or_insert(make("new1")).push("a");

    println!("[2] or_insert_with(|| make(..))");
    m.entry("old").or_insert_with(|| make("old")).push("b");
    m.entry("new2").or_insert_with(|| make("new2")).push("b");

    let mut c: HashMap<&str, i32> = HashMap::new();
    for w in ["a", "b", "a"] {
        c.entry(w).and_modify(|n| *n += 10).or_insert(1);
    }
    println!("[3] and_modify().or_insert()  a={} b={}", c["a"], c["b"]);
    println!("[4] old={:?} new1={:?} new2={:?}", m["old"], m["new1"], m["new2"]);
}
===== rustc --edition 2021 r39_lazy.rs =====
(exit 0)
===== ./r39_lazy =====
[1] or_insert(make(..))
    make() called for old
    make() called for new1
[2] or_insert_with(|| make(..))
    make() called for new2
[3] and_modify().or_insert()  a=11 b=1
[4] old=["x", "a", "b"] new1=["a"] new2=["b"]
(exit 0)
```

- ★★ **`make() called` 는 세 번** — `[1]` 에서 **`old`(이미 있는 키)** 와 `new1`, `[2]` 에서 **`new2` 만**. `or_insert(make(..))` 의 인자는 **호출 전에 평가**되고, `or_insert_with(|| make(..))` 의 클로저는 **`Vacant` 일 때만** 불린다.
- ★ **`[3]` `a=11 b=1`** — `a` 는 처음 `or_insert(1)`, 둘째에 `and_modify` 로 `+10`. **`[4]` `old=["x", "a", "b"] new1=["a"] new2=["b"]`**.

### 4. ★★ E0599 — `f64: Eq` · `f64: Hash`, `new()` 는 통과

**출력.**

```text
===== 소스: r39_f64.rs =====
use std::collections::HashMap;

fn main() {
    let mut m: HashMap<f64, &str> = HashMap::new();
    m.insert(0.5, "half");
    println!("{}", m.len());
}
===== rustc --edition 2021 r39_f64.rs =====
error[E0599]: the method `insert` exists for struct `HashMap<f64, &str>`, but its trait bounds were not satisfied
 --> r39_f64.rs:5:7
  |
5 |     m.insert(0.5, "half");
  |       ^^^^^^
  |
  = note: the following trait bounds were not satisfied:
          `f64: Eq`
          `f64: Hash`

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0599`.
(exit 1)
```

- ★★★ **E0599** — 「the method `insert` exists for struct `HashMap<f64, &str>`, but its trait bounds were not satisfied」 · `note:` **`f64: Eq` · `f64: Hash`**.
- ★ **`HashMap::new()` 줄은 에러가 아니다** — 에러는 5줄의 `insert` 하나뿐이다. `new` 에는 키 경계가 없다.

### 5. ★★ E0277 두 개 — 번호가 다르다, 경계의 「위치」 때문에

**출력.**

```text
===== 소스: r39_f64_collect.rs =====
use std::collections::HashMap;

fn main() {
    let m: HashMap<f64, &str> = [(0.5, "half")].into_iter().collect();
    println!("{}", m.len());
}
===== rustc --edition 2021 r39_f64_collect.rs =====
error[E0277]: the trait bound `f64: Eq` is not satisfied
 --> r39_f64_collect.rs:4:61
  |
4 |     let m: HashMap<f64, &str> = [(0.5, "half")].into_iter().collect();
  |                                                             ^^^^^^^ the trait `Eq` is not implemented for `f64`
  |
  = help: the following other types implement trait `Eq`:
            i128
            i16
            i32
            i64
            i8
            isize
            u128
            u16
          and 4 others
  = note: required for `HashMap<f64, &str>` to implement `FromIterator<(f64, &str)>`
note: required by a bound in `collect`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:2015:5

error[E0277]: the trait bound `f64: Hash` is not satisfied
 --> r39_f64_collect.rs:4:61
  |
4 |     let m: HashMap<f64, &str> = [(0.5, "half")].into_iter().collect();
  |                                                             ^^^^^^^ the trait `Hash` is not implemented for `f64`
  |
  = help: the following other types implement trait `Hash`:
            i128
            i16
            i32
            i64
            i8
            isize
            u128
            u16
          and 4 others
  = note: required for `HashMap<f64, &str>` to implement `FromIterator<(f64, &str)>`
note: required by a bound in `collect`
 --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/core/src/iter/traits/iterator.rs:2015:5

error: aborting due to 2 previous errors

For more information about this error, try `rustc --explain E0277`.
(exit 1)
```

**출력 — 경계가 걸린 자리(std 소스).**

```text
===== 소스: r39_bounds.py =====
# 설치된 rust-docs 의 std 소스 페이지에서 — 키 요구 트레이트가 「어디에」 걸려 있나
import html
import re
import subprocess

root = subprocess.run(["rustc", "--print", "sysroot"], capture_output=True, text=True).stdout.strip()


def lines_of(rel):
    page = root + "/share/doc/rust/html/src/" + rel
    text = html.unescape(re.sub(r"<[^>]+>", "", open(page, encoding="utf-8").read()))
    return text.split("\n")


def show(rel, pattern, nth=1):
    lines = lines_of(rel)
    hit = 0
    for i, l in enumerate(lines):
        m = re.match(r"^(\d+)(.*)$", l)
        if m and re.search(pattern, m.group(2)):
            hit += 1
            if hit < nth:
                continue
            print(f"--- {rel}")
            k = i
            while True:
                no, code = re.match(r"^(\d+)(.*)$", lines[k]).groups()
                print(f"{no:>5} {code}")
                if code.rstrip().endswith("{"):
                    break
                k += 1
            return


show("std/collections/hash/map.rs.html", r"^impl<K, V, S> HashMap<K, V, S>$")
show("std/collections/hash/map.rs.html", r"^    pub fn insert\(&mut self, k: K, v: V\)")
show("std/collections/hash/map.rs.html", r"^    pub fn get<Q: \?Sized>")
show("std/collections/hash/map.rs.html", r"^    pub fn entry\(&mut self, key: K\)")
show("alloc/collections/btree/map.rs.html", r"^    pub fn insert\(&mut self, key: K, value: V\)")

# HashMap::insert 가 765 줄의 impl 블록 「안」에 있나 — 그 사이에 줄 첫 칸의 `}` 가 몇 개인가
lines = lines_of("std/collections/hash/map.rs.html")
nums = [re.match(r"^(\d+)(.*)$", l) for l in lines]
nums = [(int(m.group(1)), m.group(2)) for m in nums if m]
start = next(n for n, c in nums if c == "impl<K, V, S> HashMap<K, V, S>")
ins = next(n for n, c in nums if c.startswith("    pub fn insert(&mut self, k: K, v: V)"))
closes = sum(1 for n, c in nums if start < n < ins and c.startswith("}"))
print(f"top-level '}}' lines between {start} and {ins}: {closes}")
===== python3 r39_bounds.py =====
--- std/collections/hash/map.rs.html
  765 impl<K, V, S> HashMap<K, V, S>
  766 where
  767     K: Eq + Hash,
  768     S: BuildHasher,
  769 {
--- std/collections/hash/map.rs.html
 1207     pub fn insert(&mut self, k: K, v: V) -> Option<V> {
--- std/collections/hash/map.rs.html
  909     pub fn get<Q: ?Sized>(&self, k: &Q) -> Option<&V>
  910     where
  911         K: Borrow<Q>,
  912         Q: Hash + Eq,
  913     {
--- std/collections/hash/map.rs.html
  887     pub fn entry(&mut self, key: K) -> Entry<'_, K, V> {
--- alloc/collections/btree/map.rs.html
 1046     pub fn insert(&mut self, key: K, value: V) -> Option<V>
 1047     where
 1048         K: Ord,
 1049     {
top-level '}' lines between 765 and 1207: 0
(exit 0)
```

- ★★ **E0277 × 2** — `f64: Eq` · `f64: Hash`, 「required for `HashMap<f64, &str>` to implement `FromIterator<(f64, &str)>`」.
- ★★★ **4번(E0599)과 다르다.** `HashMap` 의 `insert` 는 **`impl<K, V, S> HashMap<K, V, S> where K: Eq + Hash` 블록 안**(765 → 1207, 사이에 닫는 줄 0)에 있다 — 블록의 경계를 못 채우면 **메서드 호출 자체가 실패**(E0599)로 진단된다.
  `collect` 쪽은 `FromIterator` **구현의 경계**를 못 채운 것이라 **E0277**(트레이트 경계 불만족)이다.
- ★ 대비 — **`BTreeMap::insert` 는 경계가 메서드의 `where K: Ord`**(1046) 에 있어 **E0277** 이다([28번 주제](../28-partialeq-eq-partialord-ord-and-hash-contracts/) (5)의 ④).

### 6. ★ 구간 · 양 끝 · 「25 보다 작은 것 중 최대」

**출력.**

```text
===== 소스: r39_range.rs =====
use std::collections::{BTreeMap, HashMap};

fn main() {
    let t: BTreeMap<u32, &str> = [(10, "a"), (20, "b"), (30, "c"), (40, "d")].into_iter().collect();
    println!("[1] range(15..35)   {:?}", t.range(15..35).collect::<Vec<_>>());
    println!("[2] range(..=20)    {:?}", t.range(..=20).collect::<Vec<_>>());
    println!("[3] first / last    {:?} {:?}", t.first_key_value(), t.last_key_value());
    println!("[4] below 25        {:?}", t.range(..25).next_back());

    let mut h: HashMap<String, i32> = HashMap::new();
    h.insert(String::from("kiwi"), 1);
    let q: &str = "kiwi";
    println!("[5] get(&str)       {:?}", h.get(q));
}
===== rustc --edition 2021 r39_range.rs =====
(exit 0)
===== ./r39_range =====
[1] range(15..35)   [(20, "b"), (30, "c")]
[2] range(..=20)    [(10, "a"), (20, "b")]
[3] first / last    Some((10, "a")) Some((40, "d"))
[4] below 25        Some((20, "b"))
[5] get(&str)       Some(1)
(exit 0)
```

- ★ **`[1]` `[(20, "b"), (30, "c")]` · `[2]` `[(10, "a"), (20, "b")]` · `[3]` `Some((10, "a")) Some((40, "d"))` · `[4]` `Some((20, "b"))` · `[5]` `Some(1)`.**
- ★ **`[4]` 는 「25 보다 작은 키 중 가장 큰 것」** — `range(..25)` 의 **뒤에서 첫째**(`next_back`). std 가 `BTreeMap` 을 권하는 경우(「어떤 것보다 작은 것 중 가장 큰 키」) 그대로다.

### 7. ★★ 둘 다 넣은 순서 — Rust std 에는 그런 맵이 없다

**출력.**

```text
===== 소스: r39_contrast.sh =====
# 넣는 순서 kiwi → fig → plum 을 세 언어의 기본 맵에 — 순회 순서
python3 -c 'd = {}
for k in ["kiwi", "fig", "plum"]: d[k] = 0
print("python dict:", " ".join(d))'
node -e 'const m = new Map(); for (const k of ["kiwi", "fig", "plum"]) m.set(k, 0); console.log("js Map:", [...m.keys()].join(" "))'
===== bash r39_contrast.sh =====
python dict: kiwi fig plum
js Map: kiwi fig plum
(exit 0)
```

- ★★ **`python dict: kiwi fig plum` · `js Map: kiwi fig plum`** — 넣은 순서. 파이썬은 **3.7 부터 언어 보장**(Python 갈래의 [12번](../../../python/syntax/12-dict-and-key-requirements/)).
- ★★★ **Rust std 에는 없다** — `HashMap`(순서 없음 · 1번의 6 가지)과 `BTreeMap`(키 순서 · `fig kiwi plum`) 둘뿐이다. 넣은 순서가 필요하면 `Vec` 을 곁에 두거나 외부 크레이트다(이 문서는 쓰지 않았다).

### 8. ★★ Go 는 3 가지(회전), Rust 는 6 가지(전부) — 보장은 둘 다 「순서 없음」뿐

- ★★ **Go 09번 — 키 3 개, 600 판에 3 가지, 전부 회전**(`sort -u`). **Rust 1번 — 300 판에 6 가지, 3! 전부.**
- ★★ **보장은 「정해지지 않았다」 하나뿐**이다 — Go 명세도 std 도 **가짓수를 말하지 않는다.** 3 과 6 은 **각 구현의 관찰**이고, 그 차이가 **무작위화 방식이 다르다**는 것을 드러낸다(Go 는 시작점만 흔드는 모양, Rust 는 씨앗째 바꾼다).

### 9. ★ `K: Borrow<Q>, Q: Hash + Eq` — 계약이 깨지면 조회가 `None`

- ★ 5번 블록의 909 줄 — **`get<Q: ?Sized>(&self, k: &Q) where K: Borrow<Q>, Q: Hash + Eq`**. std 가 **`String: Borrow<str>`** 을 주므로 `Q = str` 로 `&str` 를 받는다(6번의 `[5]` — `Some(1)`).
- ★ **계약** — 빌린 쪽(`str`)과 원래 쪽(`String`)의 **`Hash`·`Eq` 가 같아야** 한다. 깨면 **컴파일은 되고 조회가 `None`** 이 된다 — [29번 주제](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (8)이 그렇게 받았다.

### 10. ★★ ① `BTreeMap` ② `BTreeMap` ③ 둘 다 안 된다 — 새 타입으로

| 상황 | 고를 것 | 요건 |
|---|---|---|
| ① 매번 같은 순서의 설정 덤프 | ★★ **`BTreeMap`** | **순서** — `HashMap` 은 실행마다 6 가지(1번) |
| ② 60 이상 80 미만 | ★★ **`BTreeMap`** + `range(60..80)` | **범위 조회** — `HashMap` 에는 `range` 가 없다(6번) |
| ③ `f64` 키 | ★ **어느 쪽도 그대로는 안 된다** — `total_cmp` 로 순서를 준 새 타입(28번 (7))이나 **정수로 바꾼 키** | **키 트레이트** — `f64` 는 `Eq`·`Hash`·`Ord` 가 없다(4·5번) |

- ★ 셋 다 **속도가 아니라 요건**으로 갈렸다. 요건이 없으면 std 의 권고대로 **`HashMap`**.

### 11. ★ 센 것은 호출 횟수와 가짓수 — `O(…)` 는 std 의 표, `~` 는 기댓값

- ★ **센 것** — `hash`·`eq`·`cmp` **호출 횟수**(2번)와 순회 순서의 **가짓수**(1번). **재지 않은 것** — **시간**. 「`entry` 는 한 번 찾는다」는 결론이지 「빠르다」는 결론이 아니다.
- ★ **`O(log(n))`·`O(1)~` 는 std 모듈 문서의 「Cost of Collection Operations」 표**다. **`~` 는 기댓값**(「Operations with an expected cost are suffixed with a ~」) — std 는 해시 충돌로 「**기댓값보다 훨씬 나쁠 수도** 있다」고 적는다. 점근 기호는 **이 머신의 시간이 아니다.**

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 이 문서·서머리의 **모든 블록** | `capture.sh` — 블록마다 명령을 배너에 | 배치 내내 + **제출 전 전수 재실행** | `normalize-shaky.py` — 기본 규칙 넷 · **고칠 것 0** |
| ★★ **순회 순서 가짓수** | `r39_order.sh` — 프로세스 300 개 × 두 맵 → `sort -u` | 1(600 실행) | **`HashMap` 6 · `BTreeMap` 1** |
| ★★★ **`entry` 탐색 횟수** | `r39_entry` — `Hash`·`Eq`·`Ord` 계수기, 씨앗 고정, 용량 64 | 1 | **없는 키 `hash 2·3·1` · 있는 키 `1·2·1` · `cmp 25·8` / `8·4`** |
| 인자 평가 시점 | `r39_lazy` | 1 | `or_insert` 는 있어도 · `or_insert_with` 는 없을 때만 |
| ★★ `f64` 키 | `r39_f64` · `r39_f64_collect` | 2 | **E0599** · **E0277 × 2** |
| std 소스의 경계 | `r39_bounds.py` — 설치된 `rust-docs` 소스 페이지 | 1 | 765(impl 블록) · 909(`get`) · 887(`entry`) · 1046(`BTreeMap::insert`) |
| 범위 조회·`&str` 조회 | `r39_range` | 1 | 다섯 줄 |
| 대비 | `r39_contrast.sh`(Python · node) | 1 | 둘 다 넣은 순서 |
| **안 던진 것** — 속도 · 재할당 때의 `hash` 호출 · `BTreeMap<f64>`(28번이 받았다) · Go 재실행(09번 인용) · `extract_if` | — | 0 | ★ 「안 던졌다」로 표시했다 |

**구현 의존 항목**(버전·환경이 바뀌면 **다시 찍어야 하는** 것).

| 항목 | 왜 |
|---|---|
| `HashMap` 의 **가짓수 6** | ★ 가짓수는 보장이 아니다 — 무작위화 방식이 바뀌면 바뀔 수 있다 |
| `eq` 호출 횟수 | ★ 해셔·테이블 구현에 달렸다(씨앗을 고정한 판의 값이다) |
| E0599 대 E0277 의 갈림 | ★ std 의 경계 배치와 진단 선택에 달렸다 |
| std 소스 줄 번호 | ★ 판마다 움직인다 |

★ **다시 찍는 법** — `capture.sh <새 디렉토리>` 를 그대로 돌리고 `normalize-shaky.py <원본> <새 디렉토리>` 로 견준다.
