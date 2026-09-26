# cpp/syntax/26 — `unique_ptr` 와 소유권 이동 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「열쇠가 지금 누구 손에 있나」를 맞히는 것**이 절반이다 — 「스마트 포인터니까 알아서 된다」로 뭉개지 말고
> **어느 줄에서 소유권이 넘어가고, 넘어간 뒤 원본에 무엇이 남나**를 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 둘이다** — 「복사가 안 된다」의 **에러 전문**(1번)과 「삭제자가 어디 사나」의 **`sizeof` 격자**(4번).
> ★ **「부적용인 창」이 하나 있다** — `-O2` 어셈블리. 비용은 `sizeof` 가 이미 말하고, 원자 명령 세기는 27번이 `UNIQUE` 판으로 같이 본다.
> ★★★ **15·17·20편이 잰 것은 다시 묻지 않는다** — 삭제자 호출 횟수(0 · 0 · 2) · 이동 후 `nullptr` 의 층 · `unique_ptr<Base>` 의 `~Base`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ `unique_ptr` 를 복사하려는 세 자리 (예측)

```cpp
/* uptr01.cpp */
// unique_ptr 를 복사하려는 세 자리 — 변수로 받기 · 값 인자로 넘기기 · 대입
#include <memory>
#include <utility>

void sink(std::unique_ptr<int> p) { (void)p; }

int main() {
    std::unique_ptr<int> a = std::make_unique<int>(1);
    std::unique_ptr<int> c;
    std::unique_ptr<int> b = a;       // 1. 복사 초기화
    sink(a);                          // 2. 값 인자
    c = a;                            // 3. 대입
    sink(std::move(a));               // 4. std::move 로 넘긴다
    (void)b;
}
```

- 1\~4번 중 **어느 줄이 에러**인가?
- ★★ 두 컴파일러의 진단을 `use of deleted function` 으로 grep 하면 각각 몇 건이 잡히나?
- ★ 진단이 인용하는 헤더 줄에는 무엇이 적혀 있나?

### 2. ★★ 소유권을 `<type_traits>` 로 묻는다 (예측)

```cpp
/* uptr02.cpp */
// 소유권을 <type_traits> 로 묻는다 — 다섯 타입 × 다섯 특성
#include <cstdio>
#include <memory>
#include <type_traits>

template <class T>
int row(const char* name) {
    int v[5] = {(int)std::is_copy_constructible_v<T>, (int)std::is_move_constructible_v<T>,
                (int)std::is_copy_assignable_v<T>,    (int)std::is_move_assignable_v<T>,
                (int)std::is_nothrow_move_constructible_v<T>};
    std::printf("%-20s %d      %d      %d      %d      %d\n", name, v[0], v[1], v[2], v[3], v[4]);
    return v[0] << 4 | v[1] << 3 | v[2] << 2 | v[3] << 1 | v[4];
}

int main() {
    std::printf("%-20s 복사생 이동생 복사대 이동대 noexcept이동\n", "type");
    row<int*>("int*");
    int u = row<std::unique_ptr<int>>("unique_ptr<int>");
    row<std::unique_ptr<int[]>>("unique_ptr<int[]>");
    int s = row<std::shared_ptr<int>>("shared_ptr<int>");
    row<std::weak_ptr<int>>("weak_ptr<int>");
    int split = 0;
    for (int i = 0; i < 5; ++i) split += ((u >> i) & 1) != ((s >> i) & 1);
    std::printf("unique_ptr<int> 와 shared_ptr<int> 가 갈린 칸 %d / 5\n", split);
}
```

- ★★ `unique_ptr<int>` 의 다섯 칸은 각각 0 인가 1 인가?
- ★ `unique_ptr<int>` 와 `shared_ptr<int>` 가 **갈린 칸**은 몇 개이고 어느 것인가?

### 3. ★★★ 팩토리가 돌려준 `unique_ptr` — 삭제자가 몇 번 옮겨지나 (예측)

```cpp
/* uptr03.cpp */
// 팩토리가 unique_ptr 를 돌려준다 — 삭제자의 이동 생성자에 로그를 심어 몇 번 옮겨졌나 센다
#include <cstdio>
#include <memory>
#include <utility>

static int moves = 0;

struct Del {
    Del() = default;
    Del(Del&&) noexcept { ++moves; }
    Del& operator=(Del&&) noexcept { ++moves; return *this; }
    void operator()(int* p) const { delete p; }
};
using Up = std::unique_ptr<int, Del>;

Up make_prvalue()  { return Up(new int(1)); }            // 이름 없는 임시를 돌려준다
Up make_named()    { Up p(new int(2)); return p; }         // 이름 있는 지역을 돌려준다
Up make_moved()    { Up p(new int(3)); return std::move(p); }

int main() {
    moves = 0; { Up a = make_prvalue(); } std::printf("(1) 임시를 돌려준다          삭제자 이동 %d회\n", moves);
    moves = 0; { Up b = make_named();   } std::printf("(2) 이름 있는 지역을 돌려준다 삭제자 이동 %d회\n", moves);
    moves = 0; { Up c = make_moved();   } std::printf("(3) std::move 로 돌려준다    삭제자 이동 %d회\n", moves);
    moves = 0; { Up d = make_prvalue(); Up e = std::move(d);
                 std::printf("(4) 받은 뒤 한 번 더 옮긴다   삭제자 이동 %d회 · d.get()==nullptr %d\n", moves, (int)(d.get() == nullptr)); }
}
```

- ★★ 기본 빌드(C++20)에서 `(1)`\~`(4)` 의 이동 횟수는?
- ★★★ `-fno-elide-constructors` 를 켜면 **어느 칸이 움직이고 어느 칸이 안 움직이나**?
- ★★ 같은 것을 `-std=c++14 -fno-elide-constructors` 로 던지면 `(1)` 은?

### 4. ★★★ 삭제자 열 종류 × `sizeof` (예측)

```cpp
/* uptr04.cpp */
// 삭제자의 종류 × sizeof(unique_ptr<int, D>) — 삭제자가 어디에 사나
#include <cstdio>
#include <functional>
#include <memory>

struct EmptyDel { void operator()(int* p) const { delete p; } };
struct IntDel   { int tag = 0; void operator()(int* p) const { delete p; } };
struct FatDel   { char buf[24] = {}; void operator()(int* p) const { delete p; } };
void free_fn(int* p) { delete p; }

int main() {
    int k = 1;
    int* kp = &k;
    auto lam0 = [](int* p) { delete p; };
    auto lam1 = [k](int* p) { (void)k; delete p; };
    auto lam2 = [kp](int* p) { (void)kp; delete p; };

    struct Row { const char* name; std::size_t del, up; };
    const Row rows[] = {
        {"default_delete<int>",  sizeof(std::default_delete<int>), sizeof(std::unique_ptr<int>)},
        {"EmptyDel",             sizeof(EmptyDel),                 sizeof(std::unique_ptr<int, EmptyDel>)},
        {"[](int*){}",           sizeof(lam0),                     sizeof(std::unique_ptr<int, decltype(lam0)>)},
        {"void(*)(int*)",        sizeof(&free_fn),                 sizeof(std::unique_ptr<int, void (*)(int*)>)},
        {"IntDel",               sizeof(IntDel),                   sizeof(std::unique_ptr<int, IntDel>)},
        {"[k](int*){}",          sizeof(lam1),                     sizeof(std::unique_ptr<int, decltype(lam1)>)},
        {"[kp](int*){}",         sizeof(lam2),                     sizeof(std::unique_ptr<int, decltype(lam2)>)},
        {"FatDel",               sizeof(FatDel),                   sizeof(std::unique_ptr<int, FatDel>)},
        {"EmptyDel&",            sizeof(EmptyDel&),                sizeof(std::unique_ptr<int, EmptyDel&>)},
        {"function<void(int*)>", sizeof(std::function<void(int*)>), sizeof(std::unique_ptr<int, std::function<void(int*)>>)},
    };
    std::printf("%-22s sizeof(D)  sizeof(unique_ptr<int, D>)\n", "D");
    int grew = 0, n = 0;
    for (const Row& r : rows) {
        std::printf("%-22s %-10zu %zu\n", r.name, r.del, r.up);
        ++n;
        if (r.up != sizeof(int*)) ++grew;
    }
    std::printf("int* 한 개(%zu)보다 커진 칸 %d / %d\n", sizeof(int*), grew, n);
}
```

- ★★ 열 줄의 `sizeof(unique_ptr<int, D>)` 는 각각 얼마인가 — 8 보다 커지는 칸은 몇 개인가?
- ★★★ `[](int*){}` 와 `void(*)(int*)` 는 같은 일을 하는데 크기가 같은가?
- ★ `EmptyDel&` 줄의 `sizeof(D)` 칸과 `sizeof(unique_ptr<…>)` 칸은 어떤 관계인가?

### 5. ★★ 배열을 `T` 판에 맡기면 (예측)

```cpp
/* uptr05.cpp */
// 배열을 unique_ptr 에 맡긴다 — 인자 a 는 unique_ptr<Cell[]>, s 는 unique_ptr<Cell>, i 는 unique_ptr<int>
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstring>
#include <memory>

struct Cell {
    int id = 0;
    ~Cell() { std::fprintf(stderr, "      ~Cell\n"); }
};

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "a";
    if (std::strcmp(m, "a") == 0) {
        std::fprintf(stderr, "(a) unique_ptr<Cell[]>(new Cell[3])\n");
        std::unique_ptr<Cell[]> p(new Cell[3]);
        p[1].id = 7;
        std::fprintf(stderr, "    p[1].id = %d\n", p[1].id);
    } else if (std::strcmp(m, "s") == 0) {
        std::fprintf(stderr, "(s) unique_ptr<Cell>(new Cell[3])\n");
        std::unique_ptr<Cell> p(new Cell[3]);
    } else {
        std::fprintf(stderr, "(i) unique_ptr<int>(new int[3])\n");
        std::unique_ptr<int> p(new int[3]);
    }
    std::fprintf(stderr, "    블록을 나왔다\n");
}
```

- ★★ 인자 `a` 로 돌리면 `~Cell` 이 몇 번 찍히나?
- ★★★ 인자 `s`(`Cell` 배열)와 `i`(`int` 배열)를 ASan 으로 돌리면 **오류 이름이 같은가**?
- ★ `s` 에서 `~Cell` 은 몇 번 찍히나?

### 6. ★★ 함수에 넘기는 네 모양 (예측)

```cpp
/* uptr07.cpp */
// unique_ptr 를 함수에 넘기는 네 모양 — 함수가 무엇을 할 수 있고, 부른 쪽에 무엇이 남나
#include <cstdio>
#include <memory>
#include <utility>

struct Res {
    int v;
    explicit Res(int x) : v(x) {}
    ~Res() { std::printf("      ~Res(%d)\n", v); }
};
using Up = std::unique_ptr<Res>;

void by_value(Up p)          { std::printf("      by_value: v=%d\n", p->v); }
void by_ref(Up& p)           { p.reset(new Res(p->v + 100)); std::printf("      by_ref: reset 했다\n"); }
void by_cref(const Up& p)    { p->v += 1; std::printf("      by_cref: *p 를 바꿨다 v=%d\n", p->v); }
void by_raw(Res* r)          { std::printf("      by_raw: v=%d\n", r->v); }

int main() {
    Up a = std::make_unique<Res>(1);
    std::printf("(1) by_value(std::move(a))\n");
    by_value(std::move(a));
    std::printf("    돌아온 뒤 a 가 비었나 %d\n", (int)(a == nullptr));

    Up b = std::make_unique<Res>(2);
    std::printf("(2) by_ref(b)\n");
    by_ref(b);
    std::printf("    돌아온 뒤 b->v %d\n", b->v);

    Up c = std::make_unique<Res>(3);
    std::printf("(3) by_cref(c)\n");
    by_cref(c);
    std::printf("    돌아온 뒤 c->v %d\n", c->v);

    Up d = std::make_unique<Res>(5);
    std::printf("(4) by_raw(d.get())\n");
    by_raw(d.get());
    std::printf("(5) main 끝\n");
}
```

- ★★ `(1)`\~`(4)` 가 끝난 뒤 `a`·`b`·`c` 에는 각각 무엇이 남나?
- ★★★ `by_cref` 는 `const` 로 받았는데 `c->v` 는 바뀌나?
- ★ 마지막 세 줄의 `~Res` 는 어떤 순서로 무엇을 찍나?

### 7. ★★★ `p.release();` 한 줄 (경계)

- ★★ 반환값을 버리면 두 컴파일러가 **경고**를 내나?
- ★★ ASan 은 무엇을 보고하나 — 그때 `p.get()` 은?
- ★ 해제하려는 의도였다면 무엇을 불렀어야 하나?

### 8. ★★ `const unique_ptr&` 로 받은 함수 (경계)

- ★★ 그 함수 안에서 `p.reset()` · `std::unique_ptr<int> q = std::move(p);` · `*p = 5;` 중 무엇이 막히나?
- ★ `std::move(p)` 가 막히는 이유는 17편의 어느 절인가?

### 9. ★★ `f(std::unique_ptr<W>(new W), g())` 를 C++14 로 (경계)

- ★★ `g()` 가 던질 때 두 컴파일러 판에서 `W` 가 새나 — 평가 순서는 같은가?
- ★★ 새지 않는다면 「C++14 에서는 샌다」는 걱정은 틀렸나 — 무엇으로 확인하나?
- ★ C++11 에서 `std::make_unique` 를 쓰면?

### 10. ★★ 이동 후 `nullptr` 은 왜 「표준」 칸인가 (왜)

- ★★ `unique_ptr` 의 이동 후 상태와 `std::string` 의 이동 후 상태는 **어느 층**에 있나 — 무엇이 다른가?
- ★ 그래서 코드에서 이동한 `unique_ptr` 에 해도 되는 것은?

### 11. 다른 주제와 잇기 (연결)

- ★★★ 「소유권이 타입에 있다」의 **논증**은 어느 문서가 정본인가 — 그 문서는 `unique_ptr` 가 **무엇에는 답하지 못한다**고 하나?
- ★★ 소유자가 여럿이면 무엇을 치르나 — 몇 번 주제인가?
- ★ Rust 는 이동 후 원본을 어떻게 다루나 — 그 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
