# rust/syntax/39 — `HashMap` 대 `BTreeMap` — 무엇을 고르나, `entry` API — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `HashMap`](https://doc.rust-lang.org/std/collections/struct.HashMap.html)(무작위 씨앗 · 「arbitrary order」 · Usage in const and static) ·
> [std — `BTreeMap`](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html)(「sorted by key」 · `range`) ·
> [std — `std::collections` 모듈 문서](https://doc.rust-lang.org/std/collections/index.html)(When Should You Use Which Collection? · Performance · **Entries**) ·
> [std — `RandomState`](https://doc.rust-lang.org/std/hash/struct.RandomState.html) · [std — `hash_map::Entry`](https://doc.rust-lang.org/std/collections/hash_map/enum.Entry.html).
> ★ 위 문서는 **이 머신의 `rust-docs`(1.92.0) 로컬 사본**을 열어 읽었다. 키 요구 트레이트가 걸린 자리는 같은 사본의 **std 소스 페이지에서 스크립트로 뽑았다**((5)).
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서
> **`rustc --edition 2021 <파일>.rs`** 로 돌려 받은 것이다. 대비는 `Python 3.12.3` · `node v18.19.1`.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다. 소스 펜스도 캡처가 찍었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> ★★★ **이 문서는 속도를 한 번도 재지 않았다.** 「`BTreeMap` 이 느리다」·「`entry` 가 빠르다」는 **이 문서의 주장이 아니다** — 센 것은 **`hash`·`eq`·`cmp` 호출 횟수**와 **순회 순서의 가짓수**뿐이다. 복잡도는 **std 문서의 표를 인용**했다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

```text
===== rustc --version =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
(exit 0)
===== cargo --version =====
cargo 1.92.0 (344c4567c 2025-10-21)
(exit 0)
===== rustup toolchain list =====
stable-x86_64-unknown-linux-gnu (active, default)
(exit 0)
===== g++ --version | head -1 =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
(exit 0)
===== python3 --version =====
Python 3.12.3
(exit 0)
===== node --version =====
v18.19.1
(exit 0)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★★ **흔들린다 — 그래서 싣지 않았다** | `HashMap` 의 **한 판의 순회 순서** | ★ **실행마다 씨앗이 바뀐다**(std — 「randomly seeded」·「each `HashMap` instance uses a different seed」). **한 판의 순서를 싣는 대신 가짓수를 셌다**(규칙 11) |
| 안 흔들린다 | ★★ **300 판의 `sort -u` 가짓수** — `HashMap` 6 · `BTreeMap` 1 | 키 셋(3! = 6)에서 여섯 순서가 **전부** 나왔다 — 300 판에서 한 가지라도 빠질 확률은 무시할 만하다. **가짓수가 결론**이다((1)) |
| 흔들린다 — 싣지 않았다 | 여섯 순서 **각각의 판 수**(분포) | 판마다 다르다. 자릿수조차 이 주제의 결론이 아니다 |
| 안 흔들린다 | `BTreeMap` 의 순회 줄 `fig kiwi plum` | ★ **std 보장** — 키 순서 |
| 안 흔들린다 | ★★★ **`hash`·`eq`·`cmp` 호출 횟수**((2)) | ★ 호출 **횟수**는 씨앗과 무관하다. `eq` 는 씨앗이 바꿀 수 있어(해시가 우연히 겹친 칸) **씨앗을 고정**했다(`BuildHasherDefault<DefaultHasher>` — 28번의 방식) |
| 안 흔들린다 | 에러 번호·제목·`파일:줄:칸`·종료 코드 · std 소스 **줄 번호** | 같은 rustc·`rust-docs` 판에서 고정이다 |

★ 정규화 규칙은 **기본 넷**만 썼다(제출 전 재대조 — 「3-answer」의 실행 검증 표).

## 한눈에 — 쉽게 말하면

**`HashMap` 은 「번호표를 뽑아 그 번호 칸에 넣는 보관소」, `BTreeMap` 은 「가나다순으로 꽂는 책장」이다.
보관소는 **칸 번호 매기는 규칙을 매일 바꾼다**(그래서 둘러보는 순서가 매번 다르다). 책장은 **언제나 가나다순**이고, **「ㄱ부터 ㄹ까지」 한 칸에 뽑을 수 있다.**
그리고 둘 다 「있으면 고치고 없으면 넣기」를 **한 번 찾아서** 끝내는 창구(`entry`)가 따로 있다.**

| 비유 | 실체 |
|---|---|
| 「**매일 바뀌는 번호표 규칙**」 | ★★★ **`RandomState`** — 실행마다 씨앗이 바뀐다. 키 셋 3개를 300 판 → **순서 6 가지**((1)) |
| 「**가나다순 책장**」 | ★★ **`BTreeMap`** — 키 순서. 300 판 → **1 가지**((1)) |
| 「**번호표를 뽑으려면 이름이 있어야 한다**」 | ★★ **`HashMap` 키 = `Hash + Eq`** · `BTreeMap` 키 = `Ord` — `f64` 는 둘 다 못 된다((4)) |
| 「**한 번 찾아서 창구에서 처리**」 | ★★★ **`entry`** — `hash` **1 번**. `contains_key` + `insert` 는 **2 번**((2)) |
| 「**필요할 때만 만든다**」 | ★ **`or_insert_with(\|\| …)`** — 없을 때만 부른다. `or_insert(make())` 는 **있어도 만든다**((3)) |
| 「**ㄱ부터 ㄹ까지 한 칸에**」 | ★ **`BTreeMap::range`** — 범위 조회. `HashMap` 에는 없다((6)) |

- ★★★ **판정은 한 줄이다 — 「순서가 필요하거나 범위로 찾을 거면 `BTreeMap`, 아니면 `HashMap`. 어느 쪽이든 「없으면 넣고 있으면 고치기」는 `entry` 한 번.」**
  **성능이 아니라 요건으로 고른다**((7)의 판단표 — std 모듈 문서의 「When Should You Use Which Collection?」 그대로다).

```text
   ★ 같은 키 셋 {kiwi, fig, plum} — 프로세스를 따로 300 번 ((1)의 블록 그대로)

   HashMap   ─▶ 판마다 씨앗이 다르다 ─▶ 순서 6 가지 (= 3! 전부)        ← 무엇이 나올지 약속 없음 (std: arbitrary order)
   BTreeMap  ─▶ 키를 Ord 로 줄 세운다 ─▶ 순서 1 가지  fig kiwi plum     ← std 보장 (sorted by key)
   (대비) Python dict · JS Map ─▶ 넣은 순서  kiwi fig plum              ← 셋째 규칙이 있다 ((1))
   (대비) Go map — 3 개 키에서 3 가지(회전)     ← Go 갈래 09번의 실측


   ★ 「없으면 0 을 넣고 +1」 — hash 호출 횟수 ((2)의 블록 그대로, 없는 키)

   if !m.contains_key(&k) { m.insert(k, 0); }  *m.get_mut(&k).unwrap() += 1;
        └ hash 1 ┘               └ hash 1 ┘            └ hash 1 ┘                  = 3
   *m.entry(k).or_insert(0) += 1;
        └ hash 1 ┘ ─▶ Vacant ─▶ 그 자리에 넣고 &mut V 를 돌려준다                   = 1
```

> **`RandomState`** — `HashMap` 의 기본 해셔 공장. 만들 때 **무작위 씨앗**을 뽑는다 — std: 「서로 다른 두 `RandomState` 가 만든 해셔는 **같은 값에 같은 결과를 낼 가능성이 낮다**」.\
> 예: 같은 프로그램을 두 번 돌리면 같은 키 셋의 순회 순서가 다를 수 있다((1)).

> **`entry` API** — 키로 **한 번 찾아** `Occupied`(있다) 또는 `Vacant`(없다)를 돌려받고, 그 결과 위에서 넣기·고치기를 하는 것.\
> 예: `*m.entry(w).or_insert(0) += 1` — 단어 세기의 표준형.

> **`Hash`·`Eq`·`Ord`** — 해시값을 내는 트레이트 · 전동치(反射·대칭·推移) 표식 · 전순서. **계약**은 [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)가 정본이다.\
> 예: `f64` 는 `NaN` 때문에 `Eq`·`Ord`·`Hash` 가 없다.

## 이 주제가 답하려는 질문

1. ★★ **둘은 무엇이 다른가 — 순서·키 요구 트레이트·범위 조회로**((1)·(4)·(6)).
2. ★★★ **`entry` 는 정말 한 번만 찾는가** — `contains_key` + `insert` 와 **호출 횟수로** 견주면((2)).
3. ★★ **그래서 무엇을 고르나** — 성능이 아니라 **요건**으로((7)).

★ **선행** — [**38번 주제**](../38-vec-api-capacity-retain-and-drain/)(`Vec` API)의 다음 사슬이다. [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/)의 **`Hash`/`Eq` 계약**(어기면 값이 사라진다)과 **`BTreeMap` 의 `Ord` 요구**, [**29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)의 **`Borrow`**(`HashMap<String, _>` 을 `&str` 로 찾는 이유)를 **인용**한다 — 다시 재지 않았다.
★ **정본 경계** — **해시 테이블의 원리**(해시 함수·충돌·리사이즈)는 [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/2-summary.md)(「동작 — 조회」·「동작 — 리사이즈」 절), **B-트리의 원리**(노드 분할·범위 조회)는 [`data-structure/15-b-tree`](../../../../../data-structure/15-b-tree/2-summary.md)(「동작 — 검색」·「동작 — 범위 조회」 절)가 정본이다.
여기는 **둘 중 무엇을 고르나**와 **`entry`** 만 쓴다.

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② `entry` 호출 계수다

★★★ **본체 창 — ② 키 타입의 `hash`·`eq`·`cmp` 에 계수기를 심어 「몇 번 찾았나」를 센다.** 값으로는 원리상 못 가른다 — 두 판의 결과 맵이 **똑같다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ① ★★ **순회 순서의 `sort -u` 가짓수**(프로세스 300 개) | `HashMap` 의 순서가 **흔들리나** · `BTreeMap` 은 **몇 가지인가**((1)) | 쓴다 — **결정적인 수로 바꿔서** |
| ② ★★★ **`hash`·`eq`·`cmp` 호출 계수기**(`thread_local!` + `Cell`) | `contains_key`+`insert` 와 `entry` 가 **몇 번 찾나**((2)) | ★ **본체** |
| ③ **호출 로그** | `or_insert` 의 인자·`or_insert_with` 의 클로저가 **언제 불리나**((3)) | 쓴다 |
| ④ ★★ **컴파일러 진단 + std 소스의 경계 줄** | `f64` 키가 **어디서·무슨 번호로** 막히나((4)·(5)) | 쓴다 |
| ⑤ **`range` 결과** | 범위 조회((6)) | 쓴다 |
| ⑥ **Python `dict` · JS `Map` 순회** | 셋째 규칙 — **넣은 순서**((1)) | 대비로 쓴다 |
| 실행 시간 | 「`BTreeMap` 이 느리다」·「`entry` 가 빠르다」 | ★ **부적용 — 재지 않는다.** 복잡도는 std 표 인용((7)) |
| 해시값 **자체** | — | ★ **부적용** — 씨앗마다 다르고 이 주제의 질문이 아니다(28번과 같은 선택) |

★ **「같은 질문을 다른 창으로」(제5의 상태)** — 「`entry` 는 한 번만 찾나」를 std 문서에 물으면 **말로** 답한다(「find 뒤 insert 는 **탐색을 두 번** 한다」). 그것을 **② 계수기**로 다시 물어 **수로** 받았다.
★ 계수기가 못 보는 것 — **해시 테이블 안쪽의 탐사(probe) 횟수**. `hash` 는 **키마다 한 번** 불리고, 칸을 몇 개 들여다봤는지는 `eq` 로만 **일부** 보인다(해시가 겹친 후보에서만 `eq` 로 맞춰 본다 — 이 판의 구현 세부).

### (1) ★★ 순회 순서 — `HashMap` 은 몇 가지, `BTreeMap` 은 몇 가지

**언제 쓰나** — 맵을 **돌면서 출력하거나 비교할 때**. 순서에 기대는 테스트를 짤 때.

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

```text
===== bash r39_order.sh =====
hash: distinct orders over 300 runs = 6
btree: distinct orders over 300 runs = 1
btree line: fig kiwi plum
(exit 0)
```

- ★★★ **`HashMap` — 300 판에 6 가지.** 키가 셋이니 **가능한 순서 3! = 6 이 전부** 나왔다. **한 판의 순서는 아무 뜻이 없다** — std: `keys()` 는 「**arbitrary order**」.
  ★ 왜 판마다 다른가 — std: 「**무작위로 씨앗을 뽑는다** … 각 `HashMap` 인스턴스는 **다른 씨앗**을 쓴다」(HashDoS 저항).
- ★★ **`BTreeMap` — 1 가지 · `fig kiwi plum`**(가나다순이 아니라 **바이트 순** — `&str` 의 `Ord`). std: 「keys … **in order by key**」.
- ★★ **Go 와 가짓수가 다르다** — Go 갈래의 [**09번**](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)은 3 개 키 맵에서 600 판 **3 가지**(전부 **회전**)를 셌다. Rust 는 **6 가지 전부**다.
  ★ 두 언어 다 **「순서에 기대지 마라」는 같고, 무작위화의 방식이 다르다** — 그 가짓수 자체가 구현을 드러낸다. 둘 다 **보장이 아니라 관찰**이다.

**셋째 규칙 — 넣은 순서.**

```bash
# r39_contrast.sh
# 넣는 순서 kiwi → fig → plum 을 세 언어의 기본 맵에 — 순회 순서
python3 -c 'd = {}
for k in ["kiwi", "fig", "plum"]: d[k] = 0
print("python dict:", " ".join(d))'
node -e 'const m = new Map(); for (const k of ["kiwi", "fig", "plum"]) m.set(k, 0); console.log("js Map:", [...m.keys()].join(" "))'
```

```text
===== bash r39_contrast.sh =====
python dict: kiwi fig plum
js Map: kiwi fig plum
(exit 0)
```

- ★★ **Python `dict` · JS `Map` 은 넣은 순서 그대로 `kiwi fig plum`** — 파이썬은 3.7 부터 **언어 보장**(Python 갈래의 [**12번**](../../../python/syntax/12-dict-and-key-requirements/)), JS `Map` 도 명세가 삽입 순서를 정한다(JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **23번**).
- ★★★ **Rust std 에는 「넣은 순서」 맵이 없다** — `HashMap`(순서 없음) · `BTreeMap`(키 순서) 둘뿐이다. 파이썬·JS 에서 넘어오면 **여기서 틀린다.** 넣은 순서가 필요하면 `Vec<(K, V)>` 를 곁에 두거나 외부 크레이트다(이 문서는 쓰지 않았다).

### (2) ★★★ `entry` 는 한 번 찾는다 — `hash` 호출 횟수로

**언제 쓰나** — 「**없으면 넣고 있으면 고치기**」 — 단어 세기·그룹 묶기·캐시.

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

```text
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

- ★★★ **없는 키 — `[A]` `contains_key` + `insert` 는 `hash 2`, `[C]` `entry().or_insert()` 는 `hash 1`.** 「있으면 고치기」까지 붙인 `[B]`(+ `get_mut`)는 **`hash 3`** 이다.
- ★★★ **있는 키 — `[A]` `hash 1`(찾았으니 `insert` 를 안 한다) · `[B]` `hash 2` · `[C]` `hash 1`.** `entry` 는 **있든 없든 1** 이다.
  `eq` 도 같은 모양이다 — 있는 키에서 `[B]` 는 **`eq 2`**(두 번 찾아 두 번 맞춰 봤다), `[C]` 는 **`eq 1`**.
- ★★ **`BTreeMap` 도 같다** — `[D]`(세 번 찾기) **`cmp 25`** 대 `[E]`(`entry`) **`cmp 8`**(없는 키) · **`cmp 8`** 대 **`cmp 4`**(있는 키). 트리에서는 「찾기」가 `cmp` 여러 번이라 **차이가 탐색 한 번 분량씩** 벌어진다.
- ★★ std 모듈 문서의 문장이 **수로** 확인됐다 — 「보통은 **find 뒤에 insert** 가 필요해 **삽입마다 탐색을 두 번** 하게 된다. `map.entry(key)` 를 부르면 맵이 키를 **찾고** `Entry` 의 변형을 돌려준다」.
- ★ **이 문서는 시간을 재지 않았다** — 「`entry` 가 빠르다」가 아니라 **「`entry` 는 `hash` 를 한 번 부른다」** 가 결론이다. 그리고 **용량을 64 로 미리 잡아** 재할당(키를 다시 해시할 수 있는 자리)을 **실험에서 뺐다** — 재할당 때의 호출 수는 재지 않았다.

### (3) `or_insert` 대 `or_insert_with` · `and_modify`

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

```text
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

- ★★ **`[1]` `or_insert(make(..))` — `old`(이미 있는 키)에도 `make() called` 가 찍혔다.** 인자는 **호출 전에 평가**되기 때문이다 — `entry` 가 `Occupied` 여도 `make()` 는 **이미 불렸다.**
- ★★ **`[2]` `or_insert_with(|| make(..))` — `new2`(없는 키)에서만** 불렸다. 클로저는 **`Vacant` 일 때만** 부른다. 값을 만드는 데 비용·부수 효과가 있으면 **이쪽**.
- ★ **`[3]` `and_modify(|n| *n += 10).or_insert(1)`** — `a` 는 처음 `1`, 두 번째에 `+10` → **`11`**, `b` 는 **`1`**. 「있으면 이렇게, 없으면 저렇게」를 **한 번 찾아서** 쓴다.

### (4) ★★ 키 요구 트레이트 — `f64` 는 어디서 막히나

**`HashMap<f64, _>` 에 `insert`.**

```rust
// r39_f64.rs
use std::collections::HashMap;

fn main() {
    let mut m: HashMap<f64, &str> = HashMap::new();
    m.insert(0.5, "half");
    println!("{}", m.len());
}
```

```text
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

- ★★★ **E0599 — 「the method `insert` exists … but its trait bounds were not satisfied」** · `note:` **`f64: Eq` · `f64: Hash`** 둘 다. **E0277 이 아니다.**
- ★ **`HashMap::new()` 는 통과했다**(에러는 5줄의 `insert` 한 곳) — `new` 에는 키 경계가 **없다**((5)의 소스).

**같은 키 타입을 `collect` 로 만들면.**

```rust
// r39_f64_collect.rs
use std::collections::HashMap;

fn main() {
    let m: HashMap<f64, &str> = [(0.5, "half")].into_iter().collect();
    println!("{}", m.len());
}
```

```text
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

- ★★ **이번에는 E0277 두 개** — `f64: Eq` · `f64: Hash` 각각, 「required for `HashMap<f64, &str>` to implement **`FromIterator`**」.
  **같은 결함이 부르는 자리에 따라 E0599 와 E0277 로 갈린다** — 왜 그런지는 (5)의 소스가 답한다.
- ★ **`BTreeMap<f64, _>` 의 `insert` 는 E0277 `f64: Ord`** — [**28번 주제**](../28-partialeq-eq-partialord-ord-and-hash-contracts/) (5)의 ④가 이미 받았다(「required by a bound in `BTreeMap::<K, V, A>::insert`」). 여기서 다시 던지지 않았다.
- ★ 왜 `f64` 가 `Eq` 가 아닌가 — `NaN != NaN` 이라 반사성이 깨진다(28번 (5)·(6)). 우회는 28번 (7)의 **`total_cmp`** 를 쓰는 새 타입으로 감싸는 것이다(이 문서는 던지지 않았다).

### (5) ★★ 경계가 「어디에」 걸렸나 — std 소스

```python
# r39_bounds.py
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
```

```text
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

- ★★★ **`HashMap` 은 경계가 `impl` 블록에 걸려 있다** — 765 줄 `impl<K, V, S> HashMap<K, V, S> where K: Eq + Hash, S: BuildHasher {` 안에 `insert`(1207)가 있다(사이에 블록을 닫는 줄 **0**).
  경계가 **블록에** 있으면 경계를 못 채운 타입에게는 **그 메서드가 「있지만 못 쓰는」 것**이 된다 — 그래서 **E0599**(메서드 호출 실패)다.
- ★★★ **`BTreeMap::insert` 는 경계가 메서드에 걸려 있다** — 1046 줄 `pub fn insert(…) where K: Ord`. 메서드는 **있고 경계만 못 채웠으니** **E0277**(트레이트 경계 불만족)이다.
- ★★ **`get` 은 키가 아니라 `Q` 에 경계를 건다** — 909 줄 `get<Q: ?Sized>(&self, k: &Q) where K: Borrow<Q>, Q: Hash + Eq`. 그래서 `HashMap<String, _>` 을 **`&str` 로** 찾는다((6)의 `[5]`).
  `Borrow` 의 계약(빌린 쪽과 원래 쪽의 `Hash`·`Eq` 가 같아야 한다)은 [**29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (8)이 정본이다 — 거기서 계약을 깬 `Borrow` 가 **`None`** 을 냈다.
- ★ **`entry` 는 키를 값(`K`)으로 받는다**(887 줄) — `get` 처럼 `&Q` 가 아니다. `String` 키면 **이미 있어도 `String` 을 만들어 넘겨야** 한다(비용은 재지 않았다).

### (6) `BTreeMap::range` — `HashMap` 에 없는 것

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

```text
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

- ★★ **`[1]` `range(15..35)` → `[(20, "b"), (30, "c")]` · `[2]` `range(..=20)` → `[(10, "a"), (20, "b")]`** — **키 순서로 이어진 구간**을 한 번에 꺼낸다. `HashMap` 에는 이 메서드가 **없다** — 순서가 없으니 「구간」이 성립하지 않는다.
- ★ **`[3]` `first_key_value` / `last_key_value`** — 가장 작은·큰 키. **`[4]` `range(..25).next_back()`** — **25 보다 작은 것 중 가장 큰 키** `(20, "b")`. std 가 `BTreeMap` 을 권하는 네 경우 중 셋이 이것이다((7)).
- ★ **`[5]` `h.get(q)`(`q: &str`) → `Some(1)`** — `String` 키를 `&str` 로 찾았다((5)의 `Borrow<Q>`).

### (7) ★★ 무엇을 고르나 — 요건으로

std 모듈 문서의 「**When Should You Use Which Collection?**」을 **요건 질문**으로 옮긴 판단표다. **성능 칸이 없다** — 이 문서는 재지 않았다.

| 요건 질문 | 예 → | 아니오 → | 근거 |
|---|---|---|---|
| ★★★ **키 순서로 돌아야 하나**(출력·직렬화가 매번 같아야 하나) | `BTreeMap` | 다음 질문 | (1) — `HashMap` 은 6 가지 · `BTreeMap` 1 가지 |
| ★★ **범위·가장 작은/큰 키·「x 보다 작은 것 중 최대」가 필요하나** | `BTreeMap` | 다음 질문 | (6) — `range` · `first_key_value` · `next_back` |
| ★★ **키 타입이 `Hash + Eq` 인가, `Ord` 인가** | 둘 다면 자유 · `Ord` 만이면 `BTreeMap` · `Hash + Eq` 만이면 `HashMap` | 둘 다 없으면(`f64`) **새 타입으로 감싼다** | (4)·(5) · 28번 |
| ★ **넣은 순서가 필요하나** | std 에는 **없다** — `Vec` 을 곁에 | — | (1)의 대비 |
| 그 밖 | ★ **`HashMap`** — std: 「**아마 그냥 `Vec` 이나 `HashMap` 을 쓰면 된다**」 · 「부가 기능 없는 맵이 필요할 때」 | | std 모듈 문서 |

- ★ **복잡도는 std 표 그대로 인용** — `HashMap` 의 get·insert·remove 는 **`O(1)~`**(`~` 는 **기댓값**), `BTreeMap` 은 **`O(log(n))`**, `range` 는 `BTreeMap` 만 **`O(log(n))`**(`HashMap` 은 `N/A`).
  std 는 `HashMap` 이 「이론상 기댓값보다 **훨씬 나쁠 수도** 있다(해시 충돌)」고도 적는다. **이 문서는 둘 중 무엇이 빠른지 재지 않았다** — 표의 기호는 **점근**이지 이 머신의 시간이 아니다.

## 문법 — 형태와 규칙

```text
   형태

   *m.entry(k).or_insert(0) += 1;                     ← 없으면 0 을 넣고, 어느 쪽이든 &mut V
   m.entry(k).or_insert_with(|| 비싼_값());            ← 없을 때만 만든다
   m.entry(k).and_modify(|v| …).or_insert(처음값);     ← 있으면 고치고 없으면 넣는다
   m.get("kiwi")   (HashMap<String, _>)               ← K: Borrow<str> 이라 &str 로 찾는다
   t.range(a..b) / t.first_key_value() / t.range(..x).next_back()   ← BTreeMap 만

   키 요구
   HashMap<K, V>   K: Hash + Eq      (impl 블록에 — 못 채우면 메서드 호출이 E0599)
   BTreeMap<K, V>  K: Ord            (메서드마다 — 못 채우면 E0277)


   금지 사례 — 던져서 받은 것 (번호만)

   HashMap<f64, _>  m.insert(…)             ✘ E0599   note: f64: Eq · f64: Hash
   HashMap<f64, _>  …collect()              ✘ E0277 ×2  (FromIterator 경계)
   BTreeMap<f64, _> m.insert(…)             ✘ E0277   f64: Ord   (28번 주제)
```

**규칙 불릿.**

- ★★★ **`HashMap` 의 순회 순서에 기대지 마라** — 같은 키 셋이 **실행마다** 다르다(6 / 6)((1)).
- ★★★ **「없으면 넣고 있으면 고치기」는 `entry`** — `hash` 1 번(`contains_key` + `insert` 는 2, `get_mut` 까지면 3)((2)).
- ★★ **값을 만드는 비용이 있으면 `or_insert_with`** — `or_insert(f())` 는 있어도 `f` 를 부른다((3)).
- ★★ **`f64` 는 어느 맵의 키도 못 된다** — `HashMap` 은 E0599/E0277, `BTreeMap` 은 E0277((4)).

## 어디서 틀리나

### 1. ★★★ 「내 머신에서 순서가 같았으니 괜찮다」

**300 판에 6 가지다**((1)). 한 판의 순서는 **그 판의 씨앗**일 뿐이다. 순서가 필요하면 `BTreeMap`, 아니면 **정렬해서** 찍어라.

### 2. ★★★ 「`contains_key` 로 확인하고 `insert` 하는 게 정석이다」

**두 번 찾는다**((2) — `hash 2` 대 `1`). 「있으면 고치기」까지 붙이면 **세 번**이다. `entry` 가 **한 번**이다. ★ 「그래서 빠르다」는 이 문서의 주장이 아니다 — **찾는 횟수**가 결론이다.

### 3. ★★ 「`or_insert(new_vec())` 는 없을 때만 `new_vec` 을 부른다」

**있어도 부른다**((3) — `old` 에도 `make() called`). 인자는 호출 전에 평가된다. **`or_insert_with`** 로.

### 4. ★★ 「`f64` 키가 안 되는 건 E0277 이다」

**`HashMap::insert` 는 E0599** 다((4)). 경계가 `impl` 블록에 걸려 있어 **메서드가 「안 보이는」** 쪽으로 진단된다((5)). `collect` 로 만들면 E0277, `BTreeMap` 은 E0277. **번호는 부른 자리에 달렸고, 원인은 하나**(`f64` 에 `Eq`·`Hash`·`Ord` 가 없다)다.

### 5. ★★ 「파이썬 `dict` 처럼 넣은 순서대로 나온다」

**Rust std 에는 그런 맵이 없다**((1)). `HashMap` 은 순서 없음, `BTreeMap` 은 **키 순서**다.

### 6. ★ 「`BTreeMap` 은 느리니까 피한다」

**이 문서는 재지 않았다.** std 표의 `O(log(n))` 대 `O(1)~` 는 점근 기호다. **고르는 기준은 요건**(순서·범위·키 트레이트)이다((7)).

### 7. ★ 「`HashMap<String, _>` 은 `&String` 으로만 찾는다」

**`&str` 로 찾는다**((6)의 `[5]`) — `get` 이 `K: Borrow<Q>` 를 받기 때문이다((5)). 계약은 29번.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| ★★★ `HashMap` 순회 순서가 **정해지지 않은** 것 | ★ **std 의 명시** — 「arbitrary order」 | (1) |
| 기본 해셔가 **실행마다 씨앗이 바뀌는** 것 · 인스턴스마다 다른 것 | ★ **std 의 명시** — 「randomly seeded」·「each `HashMap` instance uses a different seed」 | (1) |
| ★★ **300 판에 6 가지**(3 개 키) | ★ **이 판의 관찰** — std 는 가짓수를 말하지 않는다. Go 는 같은 실험에서 3 가지(09번) | (1) |
| 기본 해시 알고리즘(SipHash 1-3) | ★ **구현 세부** — std: 「currently … **subject to change at any point**」 | 인용만 |
| `BTreeMap` 이 **키 순서로** 도는 것 | ★ **std 보장** — 「in order by key」·「sorted by key」 | (1)·(6) |
| ★★★ `entry` 가 **한 번 찾는** 것 | ★ **std 의 설계 설명**(모듈 문서 Entries 절 — find + insert 는 탐색 두 번) · **호출 횟수는 이 판의 관찰**(`hash 1` · `eq 1`) | (2) |
| `or_insert` 의 인자가 **먼저 평가되는** 것 | ★ **언어 보장** — 함수 인자는 호출 전에 평가된다 | (3) |
| `HashMap` 키 = `Hash + Eq` · `BTreeMap` 키 = `Ord` | ★ **std 의 API** — 문서 「It is required that the keys implement the `Eq` and `Hash` traits」 · (5)의 소스 | (4)·(5) |
| 진단 번호 **E0599 대 E0277** | ★ **컴파일러의 선택** — 경계의 **위치**(impl 블록 대 메서드)가 가른다. 번호 자체는 판마다 바뀔 수 있다 | (4)·(5) |
| 복잡도 `O(1)~` · `O(log(n))` | ★ **std 문서의 표** — 이 문서는 시간을 재지 않았다 | (7) |

## 언제 쓰고 언제 안 쓰나

- ★★ **기본은 `HashMap`** — 순서·범위가 필요 없고 키가 `Hash + Eq` 일 때(std 의 권고).
- ★★ **`BTreeMap`** — 출력이 **매번 같아야** 할 때(스냅샷 테스트·직렬화·로그) · **범위·최소·최대**가 필요할 때 · 키가 `Ord` 만 있을 때((7)).
- ★★★ **`entry` 를 쓴다** — 「없으면 넣고 있으면 고치기」 전부. 값 생성에 비용이 있으면 `or_insert_with`((2)·(3)).
- ★ **`HashMap` 을 돌며 찍어야 하면 정렬해서** — 키를 `Vec` 으로 모아 `sort` 하거나 처음부터 `BTreeMap`.
- ★ **씨앗을 고정해야 하는 테스트** — `BuildHasherDefault<DefaultHasher>` 로 해셔를 바꾼다((2) · 28번의 방식). ★ 운영 코드에서는 **HashDoS 저항을 잃는다**(std).

## 핵심 문장

- ★★★ **같은 키 셋 셋을 프로세스 300 개로 돌리면 `HashMap` 은 순서 6 가지(3! 전부), `BTreeMap` 은 1 가지다**((1)).
- ★★★ **「없으면 0 넣고 +1」 — `contains_key` + `insert` 는 `hash 2`(`get_mut` 까지 3), `entry().or_insert()` 는 `hash 1`. `BTreeMap` 도 `cmp 25` 대 `8`**((2)).
- ★★ **`or_insert(f())` 는 키가 있어도 `f` 를 부르고, `or_insert_with(f)` 는 없을 때만 부른다**((3)).
- ★★ **`f64` 키 — `HashMap::insert` 는 E0599(경계가 impl 블록에), `collect` 는 E0277, `BTreeMap::insert` 는 E0277(경계가 메서드에)**((4)·(5)).
- ★ **고르는 기준은 성능이 아니라 요건 — 순서 · 범위 · 키 트레이트**((7)).

## 관련 자료

- ★★ [`data-structure/05-hashmap`](../../../../../data-structure/05-hashmap/2-summary.md) · [`data-structure/15-b-tree`](../../../../../data-structure/15-b-tree/2-summary.md) — **경계**: 해시 테이블(조회·리사이즈)과 B-트리(검색·범위 조회)의 **원리는 거기**다. 여기는 **둘 중 무엇을 고르나**와 `entry` 로 좁혔다.
- ★★ [**28번 주제** — `Hash`/`Eq`/`Ord` 계약](../28-partialeq-eq-partialord-ord-and-hash-contracts/) — 계약을 어기면 값이 사라진다 · `f64` 가 `Eq`·`Ord` 가 아닌 이유 · `BTreeMap<f64>` 의 E0277. (4)는 그 편의 `HashMap` 쪽 칸만 더 던졌다.
- ★★ [**29번 주제** — `Borrow`](../29-conversion-traits-from-into-tryfrom-asref-borrow/) (8) — `HashMap<String, _>` 을 `&str` 로 찾는 이유와 **계약을 깨면 `None`**.
- [**38번 주제** — `Vec<T>` API](../38-vec-api-capacity-retain-and-drain/) — 이 주제의 앞 사슬. `HashMap` 도 `extract_if`(1.88)·`retain` 을 갖는다(이 문서는 던지지 않았다).
- [**37번 주제** — `IntoIterator` 세 형태](../37-intoiterator-three-forms-iter-iter-mut-into-iter/) (5) — `for (k, v) in &m` 이 `(&K, &V)` 인 것.
- ★ Go 갈래의 [**09번**](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/) — Go 맵의 순회 무작위화. 3 개 키에서 **3 가지**(회전) — (1)의 Rust **6 가지**와 대비.
- ★ Python 갈래의 [**12번**](../../../python/syntax/12-dict-and-key-requirements/) — `dict` 의 **삽입 순서 보장(3.7+)** 과 키 요건.
- ★ JS 갈래 목록([`js/syntax/README.md`](../../../js/syntax/README.md))의 **23번** — `Map` 의 삽입 순서.

## 용어 풀이

- **`HashMap`** — 해시 테이블 맵. 키 `Hash + Eq`. 순회 순서 없음.
- **`BTreeMap`** — B-트리 맵. 키 `Ord`. 키 순서로 돈다. 범위 조회가 된다.
- **`RandomState`** — `HashMap` 의 기본 해셔 공장. 무작위 씨앗.
- **HashDoS** — 해시 충돌을 일부러 일으키는 입력으로 해시 테이블을 느리게 만드는 공격. 무작위 씨앗이 그것을 막는다.
- **`entry`** — 한 번 찾아 `Occupied`/`Vacant` 를 돌려주는 API.
- **`or_insert` / `or_insert_with` / `and_modify`** — 없으면 값을 넣기 / 없으면 클로저로 만들어 넣기 / 있으면 고치기.
- **`range`** — `BTreeMap` 의 범위 조회. 키 순서로 이어진 구간을 이터레이터로 준다.
- **E0599** — 메서드를 부를 수 없다(없거나, 있어도 경계를 못 채웠다).

## 더 들어가면

- **`HashMap` 을 `const`·`static` 에** — `HashMap::new()` 는 씨앗을 뽑아야 해서 `const` 에서 못 쓴다. std 는 `LazyLock` 으로 감싸라고 적는다(목록의 **53번 주제**).
- **재할당 때 키를 다시 해시하나** — (2)는 용량을 64 로 잡아 이 변수를 **뺐다.** 재할당이 끼면 `hash` 호출이 더 늘 수 있다 — 이 문서는 재지 않았다.
- **`HashSet`·`BTreeSet`** — 맵의 키만 쓰는 판. std: 「집합의 모든 연산은 **같은 맵 연산의 비용**」. 36편의 `collect` 격자에 둘 다 나왔다.
- **`BTreeMap::extract_if`(1.91)·`HashMap::extract_if`(1.88)** — 38편의 `Vec::extract_if` 와 같은 모양이 맵에도 안정됐다(릴리스 노트 — 이 문서는 던지지 않았다).
