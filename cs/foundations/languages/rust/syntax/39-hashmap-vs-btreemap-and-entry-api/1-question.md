# rust/syntax/39 — `HashMap` 대 `BTreeMap` — 무엇을 고르나, `entry` API — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ 던지는 법 — `rustc --edition 2021 <파일>.rs`. **외부 크레이트를 하나도 쓰지 않는다.**
> ★★★ **맵을 고를 때 먼저 물어라** — 「**순서가 필요한가 · 범위로 찾는가 · 키가 `Hash + Eq` 인가 `Ord` 인가**」. 속도는 그다음이고, 이 주제는 재지 않았다.
> ★ **문항 11개 중 코드가 붙은 예측형은 6개**다. 소스 펜스는 캡처가 실파일에서 찍었다(`check-source-fences.py` 대조).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 키 셋을 프로세스 300 개로 (예측)

```rust
// r39_order.rs
// 같은 키 셋을 넣고 순회한 순서를 한 줄로 찍는다
use std::collections::{BTreeMap, HashMap};

fn main() {
    let which = std::env::args().nth(1).unwrap_or_default();
    let keys = ["kiwi", "fig", "plum"];
    let line: Vec<&str> = if which == "hash" {
        let m: HashMap<&str, i32> = keys.iter().map(|k| (*k, 0)).collect();
        m.keys().copied().collect()
    } else {
        let m: BTreeMap<&str, i32> = keys.iter().map(|k| (*k, 0)).collect();
        m.keys().copied().collect()
    };
    println!("{}", line.join(" "));
}
```

```bash
# r39_order.sh
# 프로세스를 따로 300번 띄워 순회 순서가 몇 가지 나오는지 센다
rustc --edition 2021 -o r39_order r39_order.rs
for kind in hash btree; do
  n=$(for i in $(seq 1 300); do ./r39_order $kind; done | sort -u | wc -l)
  echo "$kind: distinct orders over 300 runs = $n"
done
echo "btree line: $(./r39_order btree)"
```

- ★★ `hash` 줄과 `btree` 줄의 **가짓수**는 각각? 가능한 최대 가짓수는 몇인가?
- `btree line` 은?

### 2. ★★★ 없으면 넣고 +1 — 찾는 횟수 (예측)

```rust
// r39_entry.rs
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
```

- ★★★ `[A]`·`[B]`·`[C]` 여섯 줄의 `hash`·`eq` 는? `[D]`·`[E]` 네 줄의 `cmp` 는?
- ★ 해셔를 `BuildHasherDefault<DefaultHasher>` 로 **고정**한 이유는(어느 칸이 흔들릴 수 있어서)?

### 3. ★★ 기본값을 만드는 두 가지 (예측)

```rust
// r39_lazy.rs
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
```

- `make() called for …` 줄은 **몇 번, 어느 키**에서 찍히나?
- `[3]` 의 `a`·`b` 는? `[4]` 의 세 값은?

### 4. ★★ `f64` 를 `HashMap` 키로 (예측)

```rust
// r39_f64.rs
use std::collections::HashMap;

fn main() {
    let mut m: HashMap<f64, &str> = HashMap::new();
    m.insert(0.5, "half");
    println!("{}", m.len());
}
```

- 컴파일되는가? 에러라면 번호와, `note:` 가 적는 **만족 못 한 경계**는? `HashMap::new()` 줄도 에러인가?

### 5. ★★ 같은 키 타입을 `collect` 로 (예측)

```rust
// r39_f64_collect.rs
use std::collections::HashMap;

fn main() {
    let m: HashMap<f64, &str> = [(0.5, "half")].into_iter().collect();
    println!("{}", m.len());
}
```

- 에러라면 번호와 개수는?
- ★★ 4번과 번호가 같은가? 다르다면 **std 소스의 어디**가 그 차이를 만드는가(경계가 무엇에 걸려 있나)?

### 6. ★ 범위로 찾기 (예측)

```rust
// r39_range.rs
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
```

- 다섯 줄의 출력은? `[4]` 는 **무엇을** 찾은 것인가?

### 7. ★★ 넣은 순서 (경계)

- 파이썬 `dict` 와 JS `Map` 에 `kiwi` → `fig` → `plum` 순으로 넣고 돌면 순서는? Rust std 에 **넣은 순서로 도는 맵**이 있는가?

### 8. ★★ Go 맵과 가짓수 (연결)

- Go 갈래의 [09번](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)은 **키 3 개** 맵을 600 판 돌려 몇 가지를 셌고, 그 가짓수는 어떤 모양이었나(회전·전부)? 1번의 Rust 와 견주면? 둘 중 **보장**은 무엇인가?

### 9. ★ `&str` 로 찾기 (왜)

- `HashMap<String, i32>` 을 `h.get("kiwi")` 처럼 **`&str`** 로 찾을 수 있는 이유는 `get` 의 어떤 경계 때문인가? 그 경계의 **계약**이 깨지면 무엇이 되나([29번 주제](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (8))?

### 10. ★★ 무엇을 고르나 (경계)

- 다음 셋에 각각 무엇을 고르고 **그 이유(요건)** 는? ① 매번 같은 순서로 찍혀야 하는 설정 덤프 ② 「점수 60 이상 80 미만」 학생 목록 ③ 키가 `f64` 인 측정값.

### 11. ★ 이 주제가 「`entry` 가 빠르다」고 하지 않는 이유 (왜)

- 이 주제는 무엇을 **세었고**, 무엇을 **재지 않았나**? `BTreeMap` 의 `O(log(n))` 과 `HashMap` 의 `O(1)~` 은 **누가** 한 말이고, `~` 는 무슨 뜻인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
