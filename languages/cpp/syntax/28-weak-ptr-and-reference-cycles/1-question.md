# cpp/syntax/28 — `weak_ptr` 와 순환 참조 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「확인한 순간과 쓰는 순간 사이에 무엇이 바뀔 수 있나」와 「누가 누구를 소유하나」** 두 가지를 따라가는 것이다 — 「`weak_ptr` 로 순환을 끊는다」에서 멈추지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux · 대비 rustc 1.92.0.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 `-O2` 어셈블리와 N판 실행 판정이다**(1·2번). ★★ 짝은 **ASan(3번) · TSan(1번) · `is_constructible` 격자(5번).**
> ★ **「부적용인 창」이 있다** — 경고 격자. 이 편의 사고는 전부 **규칙대로 된 코드**다. ★ **시간은 한 번도 재지 않았다.**
> ★★★ **27편이 잰 것은 다시 묻지 않는다** — 둘 다 `shared_ptr` 인 순환의 `Indirect leak` 2 · `weak_ptr` 로 누수 0 · clang + ASan 의 판별 흔들림 · `make_shared` 의 늦은 해제.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 확인한 다음 잠근다 — 다른 스레드가 마지막 소유를 놓는 동안 (예측)

```cpp
/* wptr01.cpp */
// expired() 로 살아 있음을 확인한 뒤 lock() 한다 — 그 사이에 다른 스레드가 마지막 shared_ptr 를 놓는다
// 기본은 「확인 → lock」 두 단계, -DASK_ONESTEP 이면 lock() 한 번으로 묻는다
// 판마다 새 shared_ptr 와 새 스레드를 만든다 — 한 판 안에서 두 스레드가 같은 제어 블록을 다툰다
#include <atomic>
#include <cstdio>
#include <memory>
#include <thread>

int main(int argc, char**) {
    const int trials = 20000;
    int said_alive = 0;      // 첫 질문에 「살아 있다」고 답한 판
    int got_null = 0;        // 그런데 손에 쥔 shared_ptr 가 비어 있던 판
    int wrong_value = 0;     // 손에 쥔 shared_ptr 가 가리키는 값이 기대와 다른 판
    for (int i = 0; i < trials; ++i) {
        auto s = std::make_shared<int>(i);
        std::weak_ptr<int> w = s;
        std::atomic<bool> go{false};
        std::thread owner([&] {
            while (!go.load(std::memory_order_acquire)) {}
            s.reset();                                   // 마지막 강한 참조를 놓는다
        });
        go.store(true, std::memory_order_release);
#ifdef ASK_ONESTEP
        if (auto p = w.lock()) {
            ++said_alive;
            if (*p != i) ++wrong_value;
        }
#else
        if (!w.expired()) {
            ++said_alive;
            auto p = w.lock();
            if (!p) ++got_null;
            else if (*p != i) ++wrong_value;
        }
#endif
        owner.join();
    }
    if (argc > 1)                                        // 인자를 주면 수를 그대로 찍는다(판마다 바뀐다)
        std::printf("판 %d · 살아 있다고 답한 판 %d · 그 뒤 빈 shared_ptr %d · 값이 틀린 판 %d\n",
                    trials, said_alive, got_null, wrong_value);
    else
        std::printf("빈 shared_ptr 를 쥔 판이 있었나 %d · 값이 틀린 판이 있었나 %d\n",
                    (int)(got_null > 0), (int)(wrong_value > 0));
}
```

- ★★★ 기본판(두 단계)에서 **「빈 `shared_ptr` 를 쥔 판이 있었나」** 는 0 인가 1 인가 — `-DASK_ONESTEP` 판은?
- ★★ 그 결과는 **몇 번 돌려도 같은 참/거짓**인가 — 2만 판 중 **몇 번**이었는지는 근거로 쓸 수 있나?
- ★★ 같은 소스를 **TSan** 으로 돌리면 무엇을 보고하나?

### 2. ★★★ `expired()` 와 `lock()` 을 `-O2` 로 어셈블한다 (예측)

```cpp
/* wptr02.cpp */
// expired() 와 lock() 이 각각 무슨 명령이 되나 — -DASK_EXPIRED · -DASK_LOCK 로 한 함수만 남긴다
#include <memory>

#if defined(ASK_EXPIRED)
bool ask(const std::weak_ptr<int>& w) { return !w.expired(); }
#elif defined(ASK_LOCK)
std::shared_ptr<int> ask(const std::weak_ptr<int>& w) { return w.lock(); }
#endif
```

```bash
# wptr-asm.sh
# wptr-asm.sh — expired() 판과 lock() 판을 -O2 로 어셈블해 lock 접두 명령과 cmpxchg 를 센다
for c in g++ clang++; do
  for k in EXPIRED LOCK; do
    asm=$($c -std=c++20 -O2 -S -o - -DASK_$k wptr02.cpp)
    printf '%-8s %-8s lock 접두 %d개 · cmpxchg %d개\n' "$c" "$k" \
      "$(printf '%s\n' "$asm" | grep -cE '^[[:space:]]+lock[[:space:]]')" \
      "$(printf '%s\n' "$asm" | grep -cE 'cmpxchg')"
  done
done
```

- ★★★ 두 판의 **`lock` 접두 명령 수와 `cmpxchg` 수**는 — 두 컴파일러에서 같은가?
- ★★ `lock()` 판의 몸통에 **뒤로 돌아가는 점프**가 있다면, 그것은 무엇을 다시 하는가?

### 3. ★★★ 부모 하나 · 자식 둘 — 두 설계 × 무엇을 쥐나 (예측)

```cpp
/* wptr03.cpp */
// 부모 하나 · 자식 둘 — 어느 방향을 weak_ptr 로 두나. 두 설계 × 무엇을 쥐고 있나
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <memory>
#include <vector>

struct A {                                   // 설계 A — 부모 → 자식 shared, 자식 → 부모 weak
    char name;
    std::vector<std::shared_ptr<A>> kids;
    std::weak_ptr<A> parent;
    explicit A(char n) : name(n) {}
    ~A() { std::fprintf(stderr, "      ~A %c\n", name); }
};
struct B {                                   // 설계 B — 부모 → 자식 weak, 자식 → 부모 shared
    char name;
    std::vector<std::weak_ptr<B>> kids;
    std::shared_ptr<B> parent;
    explicit B(char n) : name(n) {}
    ~B() { std::fprintf(stderr, "      ~B %c\n", name); }
};

template <class N>
std::shared_ptr<N> build(bool keep_child) {  // 뿌리 r 과 자식 x · y 를 잇고, 뿌리나 자식 x 하나만 돌려준다
    auto r = std::make_shared<N>('r');
    auto x = std::make_shared<N>('x');
    auto y = std::make_shared<N>('y');
    r->kids = {x, y};
    x->parent = r;
    y->parent = r;
    return keep_child ? x : r;
}

template <class N>
int live_kids(const N& n) {
    int k = 0;
    for (const auto& c : n.kids) {
        if constexpr (std::is_same_v<N, A>) k += c != nullptr;
        else k += !c.expired();
    }
    return k;
}

template <class N>
bool parent_alive(const N& n) {
    if constexpr (std::is_same_v<N, A>) return !n.parent.expired();
    else return n.parent != nullptr;
}

template <class N>
void run(const char* label, bool keep_child) {
    std::fprintf(stderr, "%s\n", label);
    auto held = build<N>(keep_child);
    if (keep_child)
        std::fprintf(stderr, "    쥔 것 = 자식 %c · 그 부모가 살아 있나 %d\n", held->name, (int)parent_alive(*held));
    else
        std::fprintf(stderr, "    쥔 것 = 뿌리 %c · 살아 있는 자식 수 %d\n", held->name, live_kids(*held));
    std::fprintf(stderr, "    쥔 것을 놓는다\n");
}

int main() {
    run<A>("(A1) 설계 A · 뿌리를 쥔다", false);
    run<A>("(A2) 설계 A · 자식 x 를 쥔다", true);
    run<B>("(B1) 설계 B · 뿌리를 쥔다", false);
    run<B>("(B2) 설계 B · 자식 x 를 쥔다", true);
    std::fprintf(stderr, "(끝) main 을 나간다\n");
}
```

- ★★★ `(A1)`·`(A2)`·`(B1)`·`(B2)` 에서 **「쥔 것」 줄의 숫자**와 **소멸자가 찍히는 자리**는?
- ★★ ASan 은 어느 판에서 누수를 보고하나?
- ★★★ 트리라면 **어느 방향을 `weak_ptr` 로** 두어야 하나 — 한 문장 규칙으로?

### 4. ★★ `weak_ptr` 캐시와 구독자 목록 (예측)

```cpp
/* wptr04.cpp */
// weak_ptr 캐시와 관찰자 목록 — 쓰는 쪽이 다 놓으면 캐시·목록은 그것을 어떻게 알아채나
#include <cstdio>
#include <functional>
#include <map>
#include <memory>
#include <vector>

struct Texture {
    int id;
    explicit Texture(int i) : id(i) { std::printf("      [load] %d\n", id); }
    ~Texture() { std::printf("      [drop] %d\n", id); }
};

std::map<int, std::weak_ptr<Texture>> cache;

std::shared_ptr<Texture> get(int id) {
    auto& slot = cache[id];
    if (auto sp = slot.lock()) return sp;            // 아직 누가 쓰고 있다
    auto sp = std::make_shared<Texture>(id);         // 아무도 안 쓴다 — 새로 만든다
    slot = sp;
    return sp;
}

int expired_entries() {
    int n = 0;
    for (const auto& [id, w] : cache) n += w.expired();
    return n;
}

struct Listener {
    char name;
    void on_event() const { std::printf("      %c 가 받았다\n", name); }
};

struct Subject {
    std::vector<std::weak_ptr<Listener>> subs;
    void notify() {
        int dead = 0;
        for (const auto& w : subs) {
            if (auto l = w.lock()) l->on_event();
            else ++dead;
        }
        std::erase_if(subs, [](const std::weak_ptr<Listener>& w) { return w.expired(); });
        std::printf("      죽은 구독자 %d · 남은 구독 %zu\n", dead, subs.size());
    }
};

int main() {
    std::printf("(1) a = get(1); b = get(1);\n");
    auto a = get(1);
    auto b = get(1);
    std::printf("    a 와 b 가 같은 객체인가 %d · use_count %ld\n", (int)(a == b), a.use_count());
    std::printf("(2) a.reset(); b.reset();\n");
    a.reset();
    b.reset();
    std::printf("    캐시 크기 %zu · 만료된 항목 %d\n", cache.size(), expired_entries());
    std::printf("(3) c = get(1);\n");
    auto c = get(1);
    std::printf("(4) get(2) · get(3) 을 받자마자 버린다\n");
    get(2);
    get(3);
    std::printf("    캐시 크기 %zu · 만료된 항목 %d\n", cache.size(), expired_entries());
    std::erase_if(cache, [](const auto& kv) { return kv.second.expired(); });
    std::printf("    만료 항목을 쓸어낸 뒤 캐시 크기 %zu\n", cache.size());

    std::printf("(5) 관찰자 p · q · r 을 구독시키고 q 를 놓는다\n");
    Subject s;
    auto p = std::make_shared<Listener>(Listener{'p'});
    auto q = std::make_shared<Listener>(Listener{'q'});
    auto r = std::make_shared<Listener>(Listener{'r'});
    s.subs = {p, q, r};
    q.reset();
    s.notify();
    std::printf("(6) 한 번 더 알린다\n");
    s.notify();
}
```

- ★★ `(3)` 에서 `[load] 1` 이 **다시** 찍히나?
- ★★★ `(4)` 의 **캐시 크기와 만료된 항목 수**는 — 쓸어낸 뒤에는?
- ★ `(5)`·`(6)` 에서 **죽은 구독자 수**는 각각?

### 5. ★★ `weak_ptr` 를 무엇에서 만들 수 있나 (예측)

```cpp
/* wptr05.cpp */
// weak_ptr 를 unique_ptr 에서 만들 수 있나 · 곧바로 역참조할 수 있나
#include <memory>

int main() {
    auto u = std::make_unique<int>(1);
    auto s = std::make_shared<int>(2);
    std::weak_ptr<int> w1 = s;          // 1. shared_ptr 에서
    std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
    int a = *w1;                        // 3. 역참조
    int b = *w1.lock();                 // 4. lock() 을 거쳐 역참조
    (void)w2; (void)a; (void)b;
}
```

```cpp
/* wptr06.cpp */
// weak_ptr<int> 를 무엇에서 만들 수 있나 — is_constructible 격자와 크기
#include <cstdio>
#include <memory>
#include <type_traits>

struct Base { virtual ~Base() = default; };
struct Derived : Base {};

int ones = 0, cells = 0;

template <class To, class From>
void row(const char* label) {
    bool v = std::is_constructible_v<To, From>;
    ones += v; ++cells;
    std::printf("  %-52s %d\n", label, (int)v);
}

int main() {
    std::printf("sizeof(weak_ptr<int>) = %zu · sizeof(shared_ptr<int>) = %zu · sizeof(unique_ptr<int>) = %zu\n",
                sizeof(std::weak_ptr<int>), sizeof(std::shared_ptr<int>), sizeof(std::unique_ptr<int>));
    std::printf("is_constructible_v<To, From>\n");
    row<std::weak_ptr<int>, const std::shared_ptr<int>&>("weak_ptr<int>    <- const shared_ptr<int>&");
    row<std::weak_ptr<int>, std::shared_ptr<int>&&>("weak_ptr<int>    <- shared_ptr<int>&&");
    row<std::weak_ptr<int>, const std::weak_ptr<int>&>("weak_ptr<int>    <- const weak_ptr<int>&");
    row<std::weak_ptr<Base>, const std::shared_ptr<Derived>&>("weak_ptr<Base>   <- const shared_ptr<Derived>&");
    row<std::weak_ptr<int>, const std::unique_ptr<int>&>("weak_ptr<int>    <- const unique_ptr<int>&");
    row<std::weak_ptr<int>, std::unique_ptr<int>&&>("weak_ptr<int>    <- unique_ptr<int>&&");
    row<std::weak_ptr<int>, int*>("weak_ptr<int>    <- int*");
    row<std::shared_ptr<int>, std::unique_ptr<int>&&>("shared_ptr<int>  <- unique_ptr<int>&&");
    row<std::shared_ptr<int>, const std::weak_ptr<int>&>("shared_ptr<int>  <- const weak_ptr<int>&");
    row<std::unique_ptr<int>, const std::shared_ptr<int>&>("unique_ptr<int>  <- const shared_ptr<int>&");
    std::printf("만들 수 있는 칸 %d / %d\n", ones, cells);

    std::weak_ptr<int> w;
    { auto s = std::make_shared<int>(7); w = s; }
    std::printf("만료된 w 에서 — w.lock() 이 비었나 %d\n", (int)(w.lock() == nullptr));
    try {
        std::shared_ptr<int> s(w);
        std::printf("만료된 w 에서 — shared_ptr<int>(w) 가 비었나 %d\n", (int)(s == nullptr));
    } catch (const std::exception& e) {
        std::printf("만료된 w 에서 — shared_ptr<int>(w) catch: %s\n", e.what());
    }
}
```

- ★★★ `wptr05.cpp` 에서 **몇 행이 에러**인가 — 두 컴파일러가 같은 줄을 막나?
- ★★ `wptr06.cpp` 의 **`sizeof(weak_ptr<int>)`** 와 **「만들 수 있는 칸 N / 10」** 은?
- ★★ 만료된 `w` 에서 **`lock()`** 과 **`shared_ptr<int>(w)`** 는 각각 무엇을 하나?

### 6. ★★ Rust 로 같은 부모·자식을 (예측)

```rust
// rcweak.rs
// 부모 → 자식은 Rc, 자식 → 부모는 Weak — 기본판. --cfg cycle 이면 자식 → 부모도 Rc 로 든다
use std::cell::RefCell;
use std::rc::Rc;
#[cfg(not(cycle))]
use std::rc::Weak;

struct Node {
    name: char,
    kids: RefCell<Vec<Rc<Node>>>,
    #[cfg(not(cycle))]
    parent: RefCell<Weak<Node>>,
    #[cfg(cycle)]
    parent: RefCell<Option<Rc<Node>>>,
}

impl Drop for Node {
    fn drop(&mut self) {
        println!("      drop {}", self.name);
    }
}

fn node(name: char) -> Rc<Node> {
    Rc::new(Node {
        name,
        kids: RefCell::new(vec![]),
        #[cfg(not(cycle))]
        parent: RefCell::new(Weak::new()),
        #[cfg(cycle)]
        parent: RefCell::new(None),
    })
}

fn main() {
    let x;
    {
        let r = node('r');
        x = node('x');
        r.kids.borrow_mut().push(Rc::clone(&x));
        #[cfg(not(cycle))]
        {
            *x.parent.borrow_mut() = Rc::downgrade(&r);
        }
        #[cfg(cycle)]
        {
            *x.parent.borrow_mut() = Some(Rc::clone(&r));
        }
        println!("(1) r: strong {} weak {} · x: strong {} weak {}",
                 Rc::strong_count(&r), Rc::weak_count(&r), Rc::strong_count(&x), Rc::weak_count(&x));
        println!("(2) r 이 스코프를 나간다");
    }
    #[cfg(not(cycle))]
    println!("(3) x 의 부모를 upgrade — {:?}", x.parent.borrow().upgrade().map(|p| p.name));
    #[cfg(cycle)]
    println!("(3) x 의 부모 — {:?}", x.parent.borrow().as_ref().map(|p| p.name));
    println!("(4) main 끝");
}
```

- ★★ 기본판의 `(1)` 계수와 `(3)` 의 `upgrade()` 결과는?
- ★★★ `--cfg cycle` 판은 **컴파일되나** — `drop` 줄은 몇 번 찍히나?

### 7. ★★★ TSan 이 찾는 것과 1번의 틈 (왜)

- ★★★ TSan 은 무엇을 찾는 도구이고, 1번의 틈은 **왜 그 범주에 들지 않나**?
- ★★ 그러면 이 틈은 **어느 창으로** 보았나?

### 8. ★★ 약하게 할 방향 (왜)

- ★★★ 3번의 설계 B 는 **누수가 0** 인데 왜 틀린 설계인가?
- ★★ 「순환만 끊으면 된다」 대신 쓸 규칙은?

### 9. ★★ 캐시의 만료 칸이 붙드는 것 (연결)

- ★★★ 4번의 만료 칸이 **`make_shared` 로 만든 큰 객체**의 `weak_ptr` 라면, 쓸어내기 전까지 **무엇이** 남아 있나 — 27편의 어느 측정과 이어지나?

### 10. ★★ `unique_ptr` 와 `weak_ptr` (왜)

- ★★★ `weak_ptr` 가 `unique_ptr` 에서 **못 만들어지는 이유**를 **메모리의 모양**으로 설명하라.
- ★ `unique_ptr` 가 소유한 것을 관찰해야 한다면 **무엇**을 쓰나 — 그 선택의 대가는 어느 주제에서 잇나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 27편의 「clang + ASan 은 순환을 판마다 놓친다」와 이 편의 「TSan 은 틈에 침묵한다」의 **공통점**은?
- ★ Rust 에서 `Rc` 는 **무엇을** 컴파일에서 막고 **무엇을** 안 막나?
- ★ 「`shared_ptr` 순환은 해제되지 않는다」를 **논증한 문서**와 그 절은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
