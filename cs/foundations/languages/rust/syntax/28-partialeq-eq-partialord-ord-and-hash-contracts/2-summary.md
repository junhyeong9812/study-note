# rust/syntax/28 — `PartialEq`/`Eq`/`PartialOrd`/`Ord`/`Hash` 의 계약 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [std — `trait PartialEq`](https://doc.rust-lang.org/std/cmp/trait.PartialEq.html) ·
> [`trait Eq`](https://doc.rust-lang.org/std/cmp/trait.Eq.html) ·
> [`trait PartialOrd`](https://doc.rust-lang.org/std/cmp/trait.PartialOrd.html) ·
> [`trait Ord`](https://doc.rust-lang.org/std/cmp/trait.Ord.html) ·
> [`trait Hash`](https://doc.rust-lang.org/std/hash/trait.Hash.html).
> ★ 버전은 **이 머신에 설치된 `rust-docs` 의 `@since` 배지와 `releases.md` 를 직접 읽어** 확인했다(기억으로 쓰지 않았다).
> ★ `rustc --explain E0277` · `E0369` · `E0407` 은 **확인용으로만 열었고 본문에 옮기지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·에러는 `rustc 1.92.0 (ded5c06cf 2025-12-08)` · `x86_64-unknown-linux-gnu` 에서\
> **`rustc --edition 2021 ex.rs -o ex`** 로 실제로 돌려 받은 것이다.\
> ★★ **`rustc ex.rs` 만 쓰면 에디션 2015 다** — 에디션을 안 밝힌 결과는 다른 언어를 컴파일한 것과 같다.\
> ★★★ **손으로 옮겨 적은 출력은 한 줄도 없다** — 캡처가 블록을 파일로 받고 조립기가 끼워 넣었다.\
> ★★ **외부 크레이트를 하나도 쓰지 않았다**(네트워크 없음).
> **버전** — 다섯 트레이트는 전부 1.0.0 부터다. **`f64::total_cmp` 는 1.62.0 부터**이고
> (같은 판에서 **`enum` 의 `#[derive(Default)]`** 도 들어왔다), `std::hash::DefaultHasher` 재수출은 1.76.0 부터다.
> 이 문서는 **`std::collections::hash_map::DefaultHasher`** 쪽 경로를 쓴다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| ★★★ **흔들린다** | **해시값 자체** | 기본 `RandomState` 는 **프로세스마다 씨앗이 다르다.** 게다가 `DefaultHasher` 의 알고리즘도 보장이 아니다 |
| ★★★ **흔들린다** | `HashMap`·`HashSet` 의 **순회 순서** | 위와 같은 이유 |
| **흔들린다** | 패닉 첫 줄 `thread 'main' (…)` 괄호 안의 **OS 스레드 id** | 실행마다 다르다 |
| 안 흔들린다 | **두 해시가 같은가 다른가** | ★ 이 문서는 **값 대신 이 논리값만** 찍는다 |
| 안 흔들린다 | **종료 코드 0 · 1 · 101** | 101 은 패닉이다 |
| 안 흔들린다 | 패닉의 **`파일:줄:칸` · 메시지 본문 · `note: run with RUST_BACKTRACE=1 …` 줄** | 같은 판에서 고정이다 |
| 안 흔들린다 | `BTreeMap` 의 **순회 순서** | ★ **정렬이 계약**이다 — 이 주제의 대비 축이다 |
| 안 흔들린다 | 진단의 **제목 · 번호 · 밑줄 위치** | 같은 rustc 판에서 고정이다 |

★★★ **이 주제는 해시값을 찍고 싶어지는 주제다.** 값은 흔들리므로 **「같나 다르나」로만** 찍는다.
★★ `HashMap` 을 쓰는 블록은 **`BuildHasherDefault<DefaultHasher>`** 로 씨앗을 고정하고
**키로 직접 읽는다.** 순회가 필요하면 **정렬해서** 찍는다.

## 한눈에 — 쉽게 말하면

**이 다섯은 「비교할 줄 안다」가 아니라 「무엇을 약속했나」를 타입으로 적어 둔 것이다.**

| 비유 | 실체 |
|---|---|
| 「같은지 **물어볼 수는 있다**」 | **`PartialEq`** — `==` 가 생긴다. 대칭·추이만 약속한다 |
| 「**자기 자신과는 반드시 같다**는 도장」 | ★★ **`Eq`** — **메서드가 없다.** 반사성 하나를 표시할 뿐((1)) |
| 「**줄 세울 수는 있는데 빠지는 것이 있다**」 | **`PartialOrd`** — `<`·`>`. `f64` 가 여기서 멈춘다((5)) |
| 「**빠짐없이 한 줄로 세운다**는 도장」 | **`Ord`** — `sort`·`BTreeMap` 이 이것을 요구한다((5)·(9)) |
| 「같으면 **반드시 같은 칸에 넣는다**는 약속」 | ★★★ **`Hash`** — 어기면 **값이 사라진다**((3)) |
| 「도장은 찍었는데 **거짓말이면**」 | ★★★ **논리 오류** — 컴파일러가 못 막고 **자료구조가 조용히 망가진다**((3)·(4)·(9)) |

- ★★★ **판정은 한 줄이다 — 「컴파일러가 강제하는 것은 `impl` 의 존재뿐이고, 계약은 사람이 지킨다.」**
  `Eq` 를 달았는데 `a == a` 가 거짓이어도 **컴파일은 통과한다.** 대가는 **런타임에 값이 사라지는 것**이다((4)).
- ★★ **std 는 이것을 「논리 오류(logic error)」라고 부른다** — 동작이 **규정되지 않지만**
  **미정의 동작(UB)은 아니다.** 메모리는 안전하고 **답만 틀린다.** 그래서 **더 안 보인다.**
- ★ **`f64` 가 `Eq` 도 `Ord` 도 아닌 것은 std 가 거짓말을 거부한 결과**다 — `NaN != NaN` 이라
  반사성이 깨지므로 **`Eq` 를 안 준다.** 그래서 `f64` 는 **`HashMap` 키가 못 되고 `sort()` 도 못 한다**((5)).

```text
   다섯의 계보 — 슈퍼트레이트 사슬

   PartialEq ─────▶ Eq            (Eq: PartialEq + 반사성)
       │             │
       ▼             ▼
   PartialOrd ────▶ Ord           (Ord: Eq + PartialOrd + 전순서)

   Hash                            (독립. 단 Eq 와 짝을 맞춰야 한다)


   누가 무엇을 요구하나

   HashMap<K, V>   ──▶  K: Hash + Eq        ★ 둘 다 있어야 한다
   HashSet<T>      ──▶  T: Hash + Eq
   BTreeMap<K, V>  ──▶  K: Ord              ★ Hash 는 필요 없다
   [T]::sort()     ──▶  T: Ord
   [T]::sort_by()  ──▶  (아무것도)          ★ 비교를 내가 넘긴다

   f64 는 어디까지 오나

   PartialEq  ✔      Eq   ✘   ← NaN != NaN 이라 반사성이 깨진다
   PartialOrd ✔      Ord  ✘   ← NaN 은 어느 쪽으로도 안 놓인다
                     └─ 그래서 sort()·max()·binary_search()·BTreeMap 이 전부 막힌다 (5)
                        대신 total_cmp 로 전순서를 빌려 온다 (7)


   계약을 어기면 — 컴파일은 통과하고 값이 사라진다

   a == b 인데 hash(a) != hash(b)      ──▶  다른 칸을 뒤진다 ──▶ get() 이 None (3)
   a == a 가 거짓                       ──▶  자기 칸을 찾아도 못 알아본다 ──▶ None (4)
   cmp 가 늘 Less                       ──▶  BTreeMap 이 엉뚱한 가지로 내려간다 ──▶ None (9)
```

> **논리 오류(logic error)** — 계약을 어겼을 때 std 가 쓰는 말. **동작이 규정되지 않지만 UB 는 아니다.**\
> 예: `Hash` 와 `Eq` 가 어긋난 키를 `HashMap` 에 넣으면 값이 사라지지만 메모리는 안전하다.

> **표식 트레이트(marker trait)** — 메서드가 없고 **성질만 표시**하는 트레이트.\
> 예: `Eq` — std 문서가 「**메서드가 없는 트레이트**」라고 못 박는다(컴파일러가 반사성을 검사할 수 없어서다).

> **전순서(total order)** — 어느 두 값을 집어도 **`<`·`==`·`>` 중 정확히 하나**가 성립하는 관계.\
> 예: `i32` 는 전순서이고 `f64` 는 아니다(`NaN` 이 셋 다 거짓을 낸다).

> **사전식(lexicographic)** — 앞자리부터 견주고 **갈리면 거기서 끝내는** 비교.\
> 예: `Ver(1,9,9) < Ver(2,0,0)` — 첫 자리에서 이미 갈린다((8)).

## 이 주제가 답하려는 질문

1. ★★★ **계약을 어기면 정확히 무엇이 망가지나** — `HashMap` 에 넣은 **값이 사라진다**((3)·(4)).
   이 주제의 본체가 여기다. 「지켜야 한다」가 아니라 「**안 지키면 이 출력이 나온다**」로 안다.
2. ★★ **누가 무엇을 요구하나** — `HashMap` 은 `Hash + Eq`, `BTreeMap` 과 `sort` 는 `Ord`((5)·(9)).
3. ★★ **`f64` 는 왜 거기서 멈추나** — 그리고 **어떻게 우회하나**(`total_cmp`)((5)·(6)·(7)).

★ [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)가 「**무엇이 생성되나**」였다면
여기는 「**그 생성물이 무엇을 약속한 것인가**」다.
★★ **해시 테이블의 원리**(버킷·충돌·적재율·재해싱)는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)가 정본이다 —
**거기는 「해시 표가 어떻게 도나」, 여기는** 「**Rust 가 그 요구를 타입으로 어떻게 묶나**」다.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 어디서 왔나 |
|---|---|---|
| ★★★ **계약을 일부러 깨고 자료구조에 넣기** | **값이 사라지는 것**((3)·(4)·(9)) | ★ 이 주제의 본체 |
| **경계에 넘겨 보기** | 누가 무엇을 요구하나 — E0277((2)·(5)) | 「에러도 출력이다」 |
| ★★ **해시를 「같나 다르나」로만 찍기** | 계약의 좌변·우변((3)) | ★ 값은 흔들리므로 |
| ★ **`BTreeMap` 과 나란히 놓기** | 순서 보장의 유무((9)) | 대비 창 |

★★ **「부적용인 창」도 있다** — **해시값 자체**와 **`HashMap` 순회 순서**는 이 주제에서 **근거로 안 쓴다.**
흔들려서가 아니라 **흔들리는 것을 근거로 삼으면 결론이 한 판짜리**가 되기 때문이다.

### (1) ★★ `Eq` 는 메서드가 없는 표식이다

**언제 쓰나** — `PartialEq` 를 손으로 쓴 타입을 `HashMap` 키로 넣으려 할 때. `Eq` 가 함께 필요해진다.

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

- ★★ **`impl Eq for Id {}` 의 몸통이 비어 있다.** 채울 것이 없다 — **`Eq` 에는 메서드가 없다.**
  std 문서가 그 이유를 못 박는다: **반사성(`a == a`)은 컴파일러가 검사할 수 없어서** 메서드 대신 **표시**로 둔 것이다.
- **그래서 `Eq` 가 하는 일은 하나다** — `` T: Eq `` 라는 경계를 통과시키는 것.
  `dedup` 의 `HashSet` 이 그 경계를 요구했고, `Id` 는 표시를 달았으므로 통과한다(`[1,2,1]` → **2**).
- ★ **비교의 실체는 전부 `PartialEq::eq` 에 있다.** `Eq` 를 달아도 `==` 의 동작은 한 글자도 안 바뀐다.

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

- ★ **메서드를 넣으면 E0407** — `` method `eq2` is not a member of trait `Eq` ``.
  「**`Eq` 에는 그런 자리가 없다**」를 컴파일러가 직접 말해 준다.
- **표시를 안 달면 E0277** — `` the trait bound `Loose: Eq` is not satisfied ``.
  `Loose` 는 `PartialEq` 가 있어서 `==` 는 되는데 **`T: Eq` 경계는 못 넘는다.**
  ★ `help:` 가 `` consider annotating `Loose` with `#[derive(Eq)]` `` 를 권한다 — **한 줄이면 끝나는 일**이다.
- ★★★ **그 한 줄이 곧** 「**약속**」이다. 컴파일러는 **약속을 지켰는지 검사하지 않는다** — (4)가 그 증거다.

### (2) 계약 전수 — 무엇이 강제되고 무엇이 안 되나

| 트레이트 | 약속하는 것 | 컴파일러가 강제하나 |
|---|---|---|
| `PartialEq` | **대칭**(`a == b` ⟺ `b == a`) · **추이**(`a == b`, `b == c` ⟹ `a == c`) | ✘ — 사람이 지킨다 |
| `Eq` | 위에 더해 **반사**(`a == a`) | ✘ — **메서드가 없다**((1)) |
| `PartialOrd` | `partial_cmp` 와 `<`·`>`·`==` 의 **일관성** · **추이** · **쌍대**(`a < b` ⟺ `b > a`) | ✘ |
| `Ord` | **전순서** — 어느 둘이든 `<`·`==`·`>` 중 **정확히 하나** · `partial_cmp` 와 **일치** | ✘ |
| `Hash` | ★★★ **`k1 == k2` 이면 `hash(k1) == hash(k2)`** | ✘ |

- ★★★ **강제되는 것은 「`impl` 이 있느냐」뿐이다.** 내용은 전부 사람 몫이다.
- ★★ **어긴 결과를 std 는 「논리 오류」라 부른다** — **동작이 규정되지 않지만 UB 는 아니다.**
  그래서 `unsafe` 코드가 이 트레이트들의 정확성에 기대면 안 된다고 문서가 따로 적어 둔다.
  ★ **메모리는 안전하고 답만 틀린다** — 크래시가 안 나므로 **가장 늦게 발견된다.**
- ★ **역방향은 계약이 아니다** — 해시가 같다고 값이 같을 필요는 없다(그것이 충돌이고, 표가 처리한다).
  **한 방향만** 약속이다.
- ★ **`derive` 로 다섯을 함께 파생하면 이 계약이 공짜로 지켜진다.** 손으로 쓰기 시작하는 순간부터 내 책임이다
  ([**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)).

### (3) ★★★ `Hash` 와 `Eq` 가 어긋나면 — 값이 사라진다

**언제 쓰나** — 이 절이 이 주제의 본체다. 「대소문자를 무시해서 비교하자」는 **아주 흔한 요구**이고,
`PartialEq` 만 고치고 `Hash` 를 안 고치면 바로 이 모양이 된다.

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

- **좌변은 참, 우변은 거짓이다** — `a == b` 가 `true` 인데 **해시는 다르다.** 계약이 깨진 지점이 이 두 줄이다.
  ★ **해시값은 안 찍었다** — 흔들리는 칸이라 **「같은가」라는 논리값만** 근거로 쓴다.
- ★★★ **넣은 값을 같은 키로 못 꺼낸다.** `` m.get(&a) `` 는 `Some(1)` 인데 **`` m.get(&b) `` 는 `None`** 이다.
  `a == b` 인데 답이 갈린다. `contains_key` 도 `false` 다.
  **표가 해시로 칸을 먼저 고르기 때문**이다 — 칸이 다르면 `eq` 를 **부를 기회조차 없다.**
- ★★ **같은 키가 둘이 된다.** `KEY` 를 또 넣으니 `len` 이 **2** 가 됐다.
  `HashMap` 의 불변식(「같은 키는 하나」)이 **밖에서 깨진 것**이다.
  ★ 그래서 마지막 줄에서 `` m.get(&a) `` 가 여전히 `Some(1)` 이다 — **덮어쓰기가 안 일어났다.**
- ★ **순회는 정렬해서 찍었다** — `HashMap` 의 순회 순서는 보장이 없다.
- **처방은 하나다** — **`eq` 가 보는 것과 `hash` 가 섞는 것을 같게** 한다.
  여기서는 `` self.0.to_lowercase().hash(state) `` 였다.

### (4) ★★★ 반사성을 깨면 — 넣은 값을 영영 못 꺼낸다

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

- **`k == k` 가 `false` 다.** 그런데 `` impl Eq for Never {} `` 한 줄이 **「반사적이다」라고 선언**했고
  **컴파일러는 그대로 믿는다.** 이것이 (1)에서 말한 「표시는 검사되지 않는다」의 실측이다.
- ★★★ **세 번 넣었는데 `len` 이 3 이다.** 같은 값인데 **같은 키로 안 세어진다.**
  그리고 **`get` 도 `contains_key` 도 `remove` 도 전부 실패**한다 —
  칸은 제대로 찾는데(해시는 정직하다) **`eq` 가 「아니다」라고 답해** 지나친다.
- ★★ **`remove` 뒤에도 `len` 이 3 이다.** 지울 수조차 없다 — **넣은 값이 영영 갇힌다.**
- ★ **그런데 순회로는 보인다**(`[1, 2, 3]`). **값은 거기 있는데 키로만 못 닿는다** — 누수의 모양이다.
- ★★ **이것이 `f64` 가 `Eq` 를 못 받는 이유다.** `NaN != NaN` 이라 **같은 성질**을 갖는데,
  std 는 거짓말하는 대신 **`Eq` 를 안 주는 쪽**을 골랐다. 그래서 `f64` 는 **`HashMap` 키가 아예 못 된다** —
  **언어가 이 사고를 미리 막아 준 것**이다((5)).

### (5) ★★ `f64` — `PartialOrd` 까지만 온다

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

- **비교는 된다** — `` 1.0 < 2.0 `` 도 `partial_cmp` 도 멀쩡하다. `f64` 는 `PartialOrd` 다.
- ★★ **`Ord` 가 없어 네 자리가 한꺼번에 막힌다** — 전부 **E0277** `` the trait bound `f64: Ord` is not satisfied `` 다.

| 막힌 것 | 진단이 짚는 경계 |
|---|---|
| `v.sort()` | `` required by a bound in `slice::<impl [T]>::sort` `` |
| `.max()` | `` required by a bound in `std::iter::Iterator::max` `` |
| `binary_search(&2.0)` | `` required by a bound in `core::slice::<impl [T]>::binary_search` `` |
| `BTreeMap::insert` | `` required by a bound in `BTreeMap::<K, V, A>::insert` `` |

- ★ **진단이 std 소스의 줄까지 짚어 준다**(`` /rustc/ded5c06cf…/library/alloc/src/slice.rs:129:5 ``).
  「**내가 요구한 게 아니라 std 가 요구한다**」를 보여 주는 자리다.
- ★ `.max()` 쪽에만 note 가 하나 더 붙는다 — `` the method call chain might not have had the expected associated types ``.
  `iter()` 가 `&f64` 를 주고 `copied()` 가 `f64` 로 바꾼 것을 짚어 주는 **추론 도우미**다.
- ★★ **막힌 것이 전부** 「**전순서를 전제하는 연산**」이다 — 정렬·최댓값·이분 탐색·균형 트리.
  **부분 순서로는 원리상 못 하는 일**이라 std 가 경계로 막았다.

### (6) ★ `NaN` 이 하는 일 · `partial_cmp().unwrap()` 의 끝

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

- **`NaN` 은 네 비교가 전부 `false` 다** — `==` 도 `<` 도 `>` 도 `>=` 도.
  `partial_cmp` 는 **`None`** 을 낸다. 「모른다」가 아니라 「**비교할 수 없다**」는 답이다.
- ★★ **그래서 `.unwrap()` 이 패닉한다.** `` called `Option::unwrap()` on a `None` value `` ·
  종료 코드 **101**. 정렬 도중이라 **결과 줄은 아예 안 찍힌다.**
  ★ 이 꼴(`` sort_by(|a, b| a.partial_cmp(b).unwrap()) ``)이 **f64 정렬의 가장 흔한 관용구**이고,
  **NaN 하나에 프로그램이 죽는다.**
- ★ **경고도 출력이다** — rustc 가 `` incorrect NaN comparison `` 린트를 낸다.
  ★★ 그런데 **리터럴(`f64::NAN == f64::NAN`)만 잡고 변수(`nan == nan`)는 안 잡는다**(둘 다 이 블록에 있다).
  **린트는 계약 검사가 아니라 패턴 검사**다.
- ★ **`-0.0 == 0.0` 은 참이다.** 비트는 다른데 같다고 답한다 — (7)에서 이것이 갈린다.
- ★ **마커도 값도 전부 `eprintln!`** 이다. 패닉이 표준 오류로 나오므로 **섞으면 순서가 갈린다.**

### (7) ★ `total_cmp` — 전순서를 빌려 온다

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

- **`f64::total_cmp` 는 IEEE 754 의 `totalOrder` 를 그대로 구현한 것**이다(1.62.0\~).
  `Ord` 를 **구현하지는 않고**, **비교 함수로 넘길 수 있게만** 해 준다 — `` v.sort_by(f64::total_cmp) ``.
- **순서가 이렇게 나온다** — `` [NaN, -inf, -0.0, 0.0, 1.0, 3.0, inf, NaN] ``.
  ★ **`NaN` 이 양 끝에 하나씩** 있다. `` -f64::NAN `` 은 **부호 비트가 켜진 NaN** 이라 **맨 앞**으로 간다.
- ★★ **`-0.0` 과 `0.0` 이 갈린다** — `` total_cmp `` 는 `Less`, `` == `` 는 `true`.
  **같은 두 값에 두 답**이 나오는 것이다. 그래서 `total_cmp` 를 `Ord` 로 **승격시키면 안 된다** —
  `Ord` 는 `PartialEq` 와의 일관성을 요구하는데 **여기서 어긋난다.**
- ★ `` NAN.total_cmp(&NAN) `` 은 `Equal` 이다 — `==` 는 `false` 인데.
  **이것이 「전순서를 빌려 온다」의 정확한 뜻**이다: 정렬용 순서이지 **같음의 정의가 아니다.**
- ★ `max_by`·`min_by` 도 그 순서를 따르므로 **둘 다 `NaN`** 을 답한다(부호만 다르다).
  **값의 최댓값을 원했다면 이 함수가 아니다** — `` f64::max `` 는 NaN 을 무시한다(이 문서에서는 안 던졌다).

### (8) `derive(PartialOrd)`·`derive(Ord)` 는 사전식이다

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

- ★★ **구조체는 필드 선언 순서대로** 견주고 **갈리면 거기서 끝**이다 —
  `` Ver(1,9,9) < Ver(2,0,0) `` 이 `true` 다. 뒤 두 자리가 아무리 커도 **첫 자리에서 이미 졌다.**
  ★ [**27번 주제**](../27-derive-macros-debug-clone-partialeq-default-hash/)의 `derive(PartialEq)` 에서는
  순서가 **비용**만 바꿨는데, 여기서는 **뜻을 바꾼다.** 필드 순서가 **의미론**이 되는 자리다.
- **enum 은 변형 선언 순서**가 먼저다 — `` Low < High `` 이고 정렬하면 `` [Low, Mid, High] `` 다.
  std 문서는 이것을 **판별자(discriminant) 순서**로 규정한다. 판별자를 손으로 지정하면 그 값이 이긴다.
- ★ **같은 변형끼리는 담긴 필드로** 갈린다 — `` [Ping, Data(1), Data(9), Name("가")] ``.
  `Data(9)` 가 `Name("가")` 보다 앞인 것은 **값이 아니라 변형 순서** 때문이다.
- ★ **그래서 enum 변형의 순서를 나중에 바꾸면 정렬 결과가 조용히 바뀐다.** 컴파일은 통과한다.

### (9) `BTreeMap` 은 `Ord` 를 요구한다 — 그 대신 순서를 돌려준다

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

- **순회가 정렬 순서**다 — 넣은 순서(3·1·2)와 무관하게 `` {Id(1): "가", Id(2): "나", Id(3): "다"} `` 다.
  ★★ **이것은 관찰이 아니라 계약**이다. `HashMap` 쪽은 **정렬해서 찍어야** 결정적이 된다.
- **`Ord` 가 있으니 딸려 오는 것들** — `first_key_value`·`last_key_value`·`range(Id(2)..)`.
  **`HashMap` 에는 없는 표면**이고, 그것이 `Ord` 를 요구한 대가다.
- ★ **`BTreeMap` 은 `Hash` 를 요구하지 않는다.** 키가 `Hash` 여도 안 쓴다.

그리고 **그 `Ord` 가 거짓말이면** — (3)·(4)와 같은 일이 트리에서 일어난다.

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

- **`cmp` 가 늘 `Less` 다.** 그래서 `` Bad(1) < Bad(1) `` 이 `true` 인데 `` Bad(1) == Bad(1) `` 도 `true` 다 —
  **전순서의 「정확히 하나」가 깨졌다.** ★ `PartialEq` 는 파생했고 `Ord` 만 손으로 썼다 — **둘이 어긋난 것**이다.
- ★★★ **셋을 넣었는데 하나도 못 꺼낸다.** `len` 은 3 인데 `get` 이 전부 `None` 이다.
  트리가 **탐색할 때마다 왼쪽으로만 내려가** 엉뚱한 자리에 도달하기 때문이다.
- ★ **순회하면 `[(3,30), (2,20), (1,10)]`** — 넣은 **역순**이다. 「정렬돼 있다」는 계약도 같이 깨졌다.
- ★★ **이것이 `HashMap` 사고와 같은 집안**이라는 것이 요점이다 —
  **자료구조가 다르고 깨진 계약이 다른데 증상이 같다**(`len` 은 늘고 `get` 은 `None`).

### (10) ★ 대칭은 계약이지 문법이 아니다

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

- **`PartialEq<Rhs>` 는 다른 타입과도 비교하게 해 준다** — `` Inch(1.0) == Cm(2.54) `` 가 성립한다.
- ★★ **그런데 반대 방향은 자동으로 안 생긴다** — **E0369** `` binary operation `==` cannot be applied to type `Cm` `` ·
  `` an implementation of `PartialEq<Inch>` might be missing for `Cm` ``.
- ★★★ **대칭은 「두 `impl` 을 다 쓰라」는 계약이지 컴파일러가 만들어 주는 것이 아니다.**
  한쪽만 쓰면 **에러로 드러나므로 그나마 낫고**, 둘 다 쓰되 **답을 다르게 쓰면 조용히 어긋난다.**
- ★ std 문서는 **남의 타입에 `PartialEq` 를 구현하지 말라**고 권한다 —
  대칭 짝을 내가 다 못 쓰기 때문이다([**26번 주제**](../26-orphan-rule-and-newtype/)의 고아 규칙과 같은 자리다).

## 문법 — 형태와 규칙

```text
   형태 — 파생과 손 구현

   #[derive(PartialEq, Eq, Hash)]        ← 셋을 함께. 계약이 공짜로 지켜진다
   #[derive(PartialEq, Eq, PartialOrd, Ord)]   ← 사전식 순서를 얻는다

   impl PartialEq for Id {               ← 손으로 쓰면 여기부터 내 책임
       fn eq(&self, other: &Self) -> bool { … }
   }
   impl Eq for Id {}                     ← ★ 몸통이 없다 (표식)
   impl Hash for Id {
       fn hash<H: Hasher>(&self, state: &mut H) { … }   ← eq 가 보는 것과 같아야 한다
   }
   impl Ord for Id { fn cmp(&self, o: &Self) -> Ordering { … } }
   impl PartialOrd for Id {
       fn partial_cmp(&self, o: &Self) -> Option<Ordering> { Some(self.cmp(o)) }
   }                                     ← ★ Ord 가 있으면 PartialOrd 는 이 한 줄이 정석

   금지 사례 — 던져서 받은 것

   impl Eq for Id { fn eq2(…) {…} }      ✘ E0407  Eq 에는 그런 자리가 없다
   fn f<T: Eq>(…)  에  PartialEq 만 있는 타입   ✘ E0277
   vec![f64].sort()                       ✘ E0277  f64: Ord 가 없다
   BTreeMap<f64, _>::insert               ✘ E0277
   Cm == Inch  (한쪽만 구현)              ✘ E0369
```

**규칙 불릿.**

- ★★★ **`k1 == k2` 이면 `hash(k1) == hash(k2)`** — `HashMap`·`HashSet` 이 이것에 기댄다((3)).
- ★★★ **`Eq` 는 메서드가 없다** — 반사성을 컴파일러가 검사할 수 없기 때문이다((1)).
- ★★ **어긴 것은 「논리 오류」다** — 동작이 규정되지 않지만 **UB 는 아니다.** 답만 틀린다((2)).
- **`HashMap` 은 `Hash + Eq`, `BTreeMap` 과 `sort()` 는 `Ord`** 를 요구한다((5)·(9)).
- **`f64` 는 `PartialEq`·`PartialOrd` 까지만** 온다. `total_cmp` 로 **비교 함수만** 빌려 쓴다((7)).
- **`derive(PartialOrd)`·`derive(Ord)` 는 사전식**이다 — 구조체는 필드 순서, enum 은 변형 순서((8)).
- ★ **`Ord` 를 손으로 썼으면 `PartialOrd` 는 `Some(self.cmp(other))` 로 잇는다** — 안 그러면 둘이 어긋난다((9)).

## 어디서 틀리나

### 1. ★★★ 「`PartialEq` 만 고치면 된다」

**`Hash` 를 같이 고쳐야 한다**((3)). 대소문자를 무시하는 `eq` 를 쓰고 `hash` 를 그대로 두면
**같은 키로 넣은 값이 안 나오고, 같은 키가 둘이 된다.** 컴파일러는 한 마디도 안 한다.

### 2. ★★★ 「계약을 어기면 어디선가 터지겠지」

**안 터진다**((3)·(4)·(9)). std 는 이것을 **논리 오류**라 부르고 **UB 가 아니라고** 못 박는다.
메모리는 안전하고 **`get` 이 `None` 을 낼 뿐**이다. **크래시가 없어서 가장 늦게 발견된다.**

### 3. ★★ 「`Eq` 를 달았으니 반사적이다」

**`Eq` 는 아무것도 검사하지 않는다**((1)·(4)). 빈 `impl` 한 줄이 **선언**일 뿐이다.
실측에서 `a == a` 가 거짓인 타입이 **컴파일을 통과했고**, 넣은 값을 **영영 못 꺼냈다.**

### 4. ★★ 「`f64` 를 `sort()` 로 정렬하면 된다」

**E0277 이다**((5)). 흔한 우회 `` sort_by(|a, b| a.partial_cmp(b).unwrap()) `` 는
**`NaN` 이 섞이면 패닉**한다((6)). 정답은 **`sort_by(f64::total_cmp)`**((7)).

### 5. ★ 「`total_cmp` 는 `f64` 의 `Ord` 다」

**아니다**((7)). `` -0.0 `` 과 `` 0.0 `` 을 `Less` 로 가르는데 `` == `` 는 `true` 다 —
**`Ord` 가 요구하는 `PartialEq` 와의 일관성이 깨진다.** 그래서 std 도 `Ord` 로 안 올린다.
**정렬용 비교 함수**로만 쓴다.

### 6. ★ 「enum 변형 순서는 스타일이다」

**정렬 결과를 정한다**((8)). 변형을 위아래로 옮기면 **`sort()` 의 답이 조용히 바뀐다** —
컴파일은 통과하고 테스트만 깨진다(테스트가 있으면).

### 7. ★★ 「해시가 같으면 같은 값이다」

**역방향은 계약이 아니다**((2)). 해시가 같아도 값은 다를 수 있고(충돌), 표가 그때 `eq` 로 가린다.
★ 그래서 **`eq` 가 틀리면 충돌 처리까지 같이 틀린다** — 두 트레이트가 **한 몸**인 이유다.

### 8. ★ 「`Ord` 를 손으로 쓰면 `PartialOrd` 는 파생해도 된다」

**어긋난다**((9)). 파생된 `partial_cmp` 는 **필드 사전식**인데 손으로 쓴 `cmp` 는 다른 답을 낼 수 있다.
**`Some(self.cmp(other))` 로 잇는 것**이 정석이다.

## 구현 세부사항 대 언어 보장

| 항목 | 무엇인가 | 근거 |
|---|---|---|
| `k1 == k2` ⟹ `hash(k1) == hash(k2)` | ★ **계약**(std 문서가 규정) — 컴파일러 강제는 **없다** | (3)의 실측 |
| `Eq` 에 **메서드가 없는** 것 | ★ **언어·라이브러리 보장** — 문서가 이유까지 적는다 | (1)의 실측(E0407) |
| 계약 위반이 **UB 가 아닌** 것 | ★ **보장** — std 가 「논리 오류」라고 명시한다 | (2)·(4) |
| ★★ 계약을 어겼을 때 **정확히 무엇이 나오나** | ★ **구현 세부** — `` 동작이 규정되지 않는다 ``. `None`·`len` 증가는 **이 판의 관찰**이다 | (3)·(4)·(9)의 실측 |
| `BTreeMap` 의 **순회가 정렬 순서**인 것 | ★ **계약** | (9)의 실측 |
| `HashMap` 의 **순회 순서** | ★ **보장 없음** — 씨앗이 프로세스마다 다르다 | ★ 근거로 쓰지 않았다 |
| **해시값 자체** | ★ **보장 없음** — `DefaultHasher` 의 알고리즘도 안정 보장이 아니다 | ★ 「같나 다르나」만 썼다 |
| `total_cmp` 의 **순서**(`-0.0` < `0.0`, NaN 이 양 끝) | ★ **보장** — IEEE 754 `totalOrder` 를 따른다 | (7)의 실측 |
| `derive(Ord)` 가 **사전식**인 것 | ★ **보장** — std 문서가 선언 순서로 규정한다 | (8)의 실측 |
| `` incorrect NaN comparison `` 린트가 **리터럴만** 잡는 것 | ★ **구현 세부** — 린트의 패턴이다 | (6)의 실측 |
| 진단에 박히는 `/rustc/ded5c06cf…/…` 경로 | ★ **이 rustc 판의 커밋 해시** | (5)의 관찰 |

## 언제 쓰고 언제 안 쓰나

- **다섯을 함께 파생한다** — 기본값이다. `#[derive(PartialEq, Eq, Hash)]` 면 계약이 공짜로 지켜진다.
- ★★ **손으로 쓸 거면 짝을 맞춰 쓴다** — `PartialEq` 를 손으로 썼으면 **`Hash` 도** 손으로,
  `Ord` 를 손으로 썼으면 **`PartialOrd` 는 `Some(self.cmp(other))`** 로.
- ★ **정규화가 필요하면 값을 정규화한다** — 대소문자 무시가 필요하면
  **생성자에서 소문자로 바꿔 저장**하는 쪽이 `eq`/`hash` 를 둘 다 고치는 것보다 안전하다(실수할 자리가 없다).
- **`f64` 를 키로 쓰고 싶으면** — 정수로 바꾸거나(고정소수점), `` u64 `` 비트로 바꾸거나,
  **newtype 으로 감싸고 계약을 지켜 손으로 쓴다**([**26번 주제**](../26-orphan-rule-and-newtype/)).
- **`BTreeMap` 을 고른다** — 순서가 필요하거나 범위 질의가 필요할 때. `Ord` 만 있으면 된다.
- **`HashMap` 을 고른다** — 순서가 필요 없고 조회가 잦을 때. `Hash + Eq` 가 필요하다.
  ★ 자료구조 선택의 일반론은 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)가 정본이다.

## 핵심 문장

- ★★★ **컴파일러가 강제하는 것은 `impl` 의 존재뿐이고 계약은 사람이 지킨다** — `Eq` 는 **메서드조차 없다**((1)).
- ★★★ **어기면 터지는 게 아니라 값이 사라진다** — `len` 은 늘고 `get` 은 `None` 이다((3)·(4)·(9)).
- ★★ **`Hash` 와 `Eq` 는 한 몸**이다 — 한쪽만 고치는 것이 이 주제 최다 사고다((3)).
- ★★ **`f64` 는 `Eq`·`Ord` 를 안 받는다** — std 가 거짓말을 거부한 결과이고, **덕분에 그 사고가 미리 막힌다**((4)·(5)).
- ★ **`total_cmp` 는 정렬용 순서이지 같음의 정의가 아니다**((7)).
- ★ **`derive` 의 순서가 뜻을 정하는 자리는 여기다** — 27번의 `PartialEq` 는 비용만 바꿨다((8)).

## 관련 자료

- ★★ [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) —
  **경계**: **해시 표의 원리**(해시 함수·버킷·충돌 해결·적재율·재해싱·분할 상환 비용)는 **거기**다.
  **여기는** 「**Rust 가 그 요구를 `Hash`·`Eq` 라는 타입으로 어떻게 묶나**」와
  「**묶인 약속을 어기면 무슨 출력이 나오나**」만 다룬다. 원리는 옮겨 적지 않았다.
- [**27번 주제** — `derive` 매크로](../27-derive-macros-debug-clone-partialeq-default-hash/) —
  ★ **경계**: **무엇이 생성되나**는 거기, **그 생성물이 무엇을 약속한 것인가**는 여기다.
- [**26번 주제** — 고아 규칙과 newtype](../26-orphan-rule-and-newtype/) —
  `f64` 를 키로 쓰려면 **감싸야** 하고, 남의 타입에 `PartialEq` 를 붙이지 말라는 권고도 같은 자리다((10)).
- [**25번 주제** — 트레이트 정의·구현](../25-traits-definition-impl-default-methods-and-associated-types/) —
  ★ **경계**: **슈퍼트레이트** 문법은 거기, 여기는 그 사슬이 **계약을 어떻게 쌓나**다.
- [**21번 주제** — `Option` 과 조합 메서드](../21-option-and-combinators/) —
  `partial_cmp` 가 `Option<Ordering>` 을 내는 이유와 `unwrap` 의 대가((6)).
- [목록의 **39번 주제**](../39-hashmap-vs-btreemap-and-entry-api/) — `HashMap`·`BTreeMap` 등 컬렉션. **어느 것을 고르나**의 정본이다.
- [목록의 **36번 주제**](../36-iterator-adapters-laziness-and-collect/) — `Iterator` 와 어댑터. `max_by`·`min_by` 가 비교 함수를 받는 자리다.
- Java 의 `equals`/`hashCode` 계약 — [`java/syntax/27-equals-hashcode-contract/`](../../../java/syntax/27-equals-hashcode-contract/).
  ★ **대비**: **계약의 내용이 거의 같다.** 다른 것은 **표면**이다 —
  Java 는 `Object` 에 **기본 구현이 있어** 안 고쳐도 컴파일·실행이 되고(참조 동등으로 조용히 동작),
  Rust 는 **`impl` 이 없으면 아예 못 넣는다**(E0599). **「깜빡함」이 Java 에서는 런타임 버그, Rust 에서는 컴파일 에러**다.
- Java 의 `Comparable`/`Comparator` — [`java/syntax/28-comparable-comparator/`](../../../java/syntax/28-comparable-comparator/).
  ★ **대비**: 전순서 계약을 어기면 Java 는 `` IllegalArgumentException: Comparison method violates its general contract! `` 로
  **던져 주는 경우가 있고**, Rust 의 `BTreeMap` 은 **조용히 값을 잃는다**((9)).
- Kotlin 의 `data class` — [`kotlin/syntax/22-data-class-generated-members/`](../../../kotlin/syntax/22-data-class-generated-members/).
  ★ **대비**: 생성 범위가 **주 생성자 프로퍼티만**이라 **`equals` 와 `hashCode` 가 같은 필드를 본다**(짝이 자동으로 맞는다).
- C# 의 동등성 규칙 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **19번**.
- Go 의 맵 — Go 갈래 목록([`go/syntax/README.md`](../../../go/syntax/README.md))의 **09번**.
  ★ **대비**: Go 는 **비교 가능한 타입만 키로 받고** 그 비교를 **언어가 정한다** —
  사용자가 `Hash`/`Eq` 를 쓸 자리가 없어 **이 사고 자체가 안 난다.** 대신 **정규화도 못 한다.**

## 용어 풀이

- **계약(contract)** — 트레이트를 구현하는 쪽이 지키겠다고 약속한 성질. 컴파일러는 검사하지 않는다.
- **논리 오류(logic error)** — 계약을 어겼을 때 std 가 쓰는 말. 동작이 규정되지 않지만 **UB 는 아니다.**
- **표식 트레이트(marker trait)** — 메서드가 없고 성질만 표시하는 트레이트. `Eq` 가 그렇다.
- **반사(reflexive)** — `a == a`. **`Eq` 가 `PartialEq` 에 더하는 조항**이다.
- **대칭(symmetric)** — `a == b` 이면 `b == a`.
- **추이(transitive)** — `a == b` 이고 `b == c` 이면 `a == c`.
- **전순서(total order)** — 어느 둘이든 `<`·`==`·`>` 중 정확히 하나가 성립하는 관계.
- **부분 순서(partial order)** — 비교할 수 없는 짝이 있어도 되는 관계. `f64` 가 그렇다(`NaN`).
- **사전식(lexicographic)** — 앞자리부터 견주고 갈리면 끝내는 비교.
- **`totalOrder`** — IEEE 754 가 정한 부동소수점 전순서. `f64::total_cmp` 가 그것이다.
- **씨앗(seed)** — 해시 함수에 섞는 임의 값. `RandomState` 는 프로세스마다 새로 고른다.

## 더 들어가면

- **`Borrow` 와 조회 키** — `HashMap<String, V>` 를 `&str` 로 조회할 수 있는 것은 `Borrow` 덕분인데,
  **`Borrow` 도 「같으면 해시도 같아야 한다」는 계약을 요구한다**([목록의 **29번 주제**](../29-conversion-traits-from-into-tryfrom-asref-borrow/)).
- **`Hasher` 를 바꾸기** — `BuildHasher` 를 갈아 끼우면 해시 함수를 바꿀 수 있다.
  이 문서는 **씨앗 고정**을 위해 그 자리를 썼다.
- **HashDoS 와 `RandomState`** — 씨앗을 매번 새로 고르는 이유가 **공격자가 충돌을 몰아넣는 것**을 막기 위해서다.
  그 대가가 **순회 순서의 비결정성**이다. 원리는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/).
- **`Ordering` 의 조합** — `` cmp(a,b).then_with(|| …) `` 로 다단 정렬을 쓴다. 사전식을 손으로 쓰는 꼴이다.
- **`Reverse`** — `` std::cmp::Reverse(x) `` 로 감싸면 순서가 뒤집힌다. **newtype 의 std 판 사례**다((26번 주제)).
