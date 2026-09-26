# cpp/syntax/34 — 가변 인자 템플릿과 팩 확장 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「`...` 은 앞의 패턴을 원소마다 복제하고, 원소마다 자기 타입과 값 범주를 들고 간다」** 를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++17 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 폴드 식 격자(2번)와 복사·이동 로그(3번)다.**
> ★ **「부적용인 창」이 있다** — ASan · 어셈블리(로그로 바꿨다) · 경고 격자.
> ★★★ **09편이 잰 것은 다시 묻지 않는다** — `std::move`·`std::forward` 가 캐스트라는 것 · 참조 축약 표.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 재귀와 폴드 (예측)

```cpp
/* pack02.cpp */
// 같은 합을 두 방법으로 — 재귀로 한 겹씩 벗기기(C++11) 대 폴드 식(C++17). 그리고 sizeof...
#include <cstdio>

long sum_rec() { return 0; }
template <class T, class... Rest> long sum_rec(T first, Rest... rest) {
    std::printf("  sum_rec: first=%ld, sizeof...(rest)=%zu\n", (long)first, sizeof...(rest));
    return first + sum_rec(rest...);
}

template <class... Ts> long sum_fold(Ts... xs) {
    std::printf("  sum_fold: sizeof...(Ts)=%zu\n", sizeof...(Ts));
    return (0 + ... + xs);
}

int main() {
    std::printf("sum_rec(1, 2, 3) = %ld\n", sum_rec(1, 2, 3));
    std::printf("sum_fold(1, 2, 3) = %ld\n", sum_fold(1, 2, 3));
    std::printf("sum_fold() = %ld\n", sum_fold());
}
```

- ★★ `sum_rec` 이 찍는 `sizeof...(rest)` 세 값은?
- ★★ `sum_fold()` 는 컴파일되나 — 된다면 값은?

### 2. ★★★ 연산자 5 × 꼴 4 × 팩 2 × 컴파일러 2 (예측)

```cpp
/* pack01.cpp */
// 폴드 식 한 칸 — 식은 -DFOLD=… , 넘기는 팩은 -DPACK=… 로 고른다. init 자리는 I
#include <cstdio>
#include <type_traits>

template <class... Ts> auto cell(Ts... xs) {
    constexpr auto I = INIT;
    (void)I;
    return FOLD;
}

template <class F> void run(F f) {
    if constexpr (std::is_void_v<decltype(f())>) {
        f();
        std::puts("void");
    } else {
        std::printf("%lld\n", (long long)f());
    }
}

int main() {
    run([] { return cell(PACK); });
}
```

```bash
# fold-grid.sh
# fold-grid.sh — 연산자 다섯 × 폴드 꼴 넷 × 팩 둘(빈 팩 · 10,3,2) × 컴파일러 둘. 칸마다 값 또는 error
ops=('+' '-' ',' '&&' '||')
inits=('0' '0' '0' 'true' 'false')
forms=('(... OP xs)' '(xs OP ...)' '(I OP ... OP xs)' '(xs OP ... OP I)')
names=('단항 좌' '단항 우' '이항 좌' '이항 우')
cell() {  # $1 컴파일러 $2 식 $3 init $4 팩
  if $1 -std=c++17 -Wall -Wextra -pedantic "-DFOLD=$2" "-DINIT=$3" "-DPACK=$4" pack01.cpp -o gx 2>/dev/null; then ./gx; else echo error; fi
}
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "연산자" "꼴" "g++ 빈 팩" "g++ 10,3,2" "clang++ 빈 팩" "clang++ 10,3,2" > grid.tsv
for k in 0 1 2 3 4; do for j in 0 1 2 3; do
  op="${ops[$k]}"; e="${forms[$j]//OP/"$op"}"
  row="$op"$'\t'"${names[$j]} $e"
  for c in g++ clang++; do for p in '' '10, 3, 2'; do row="$row"$'\t'"$(cell $c "$e" "${inits[$k]}" "$p")"; done; done
  printf '%s\n' "$row" >> grid.tsv
done; done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 6' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
cc_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($3 != $5) + ($4 != $6) } END { print n }')
lr_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ v[NR] = $4 } END { for (i = 1; i <= NR; i += 2) n += (v[i] != v[i+1]); print n }')
errs=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($3 == "error") + ($4 == "error") } END { print n }')
echo "g++ 대 clang++ 가 갈린 칸 $cc_split / $((rows * 2)) · 좌 대 우가 갈린 짝(10,3,2) $lr_split / $((rows / 2)) · error 칸(g++) $errs / $((rows * 2))"
rm -f gx grid.tsv
```

- ★★★ `-` 네 행의 `10,3,2` 칸 값은?
- ★★★ 빈 팩 칸 중 `error` 는 어느 것들인가 — `,` · `&&` · `||` 의 **단항** 빈 팩 칸 값은?
- ★★ `,` 의 이항 두 행(`10,3,2`)은 각각 무엇인가?
- ★★ 마지막 줄의 세 숫자는?

### 3. ★★★ 두 팩토리 (예측)

```cpp
/* pack03.cpp */
// 팩을 받아 T 를 만드는 팩토리 — forward 를 쓴 판과 안 쓴 판. 복사·이동을 로그로 센다
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) {}
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
};

struct Duo {
    Noisy a;
    Noisy b;
    Duo(const Noisy& x, const Noisy& y) : a(x), b(y) { std::puts("    Duo(const&, const&)"); }
    Duo(Noisy&& x, Noisy&& y) : a(std::move(x)), b(std::move(y)) { std::puts("    Duo(&&, &&)"); }
    Duo(const Noisy& x, Noisy&& y) : a(x), b(std::move(y)) { std::puts("    Duo(const&, &&)"); }
};

template <class T, class... Args> T make_fwd(Args&&... args) {
    return T(std::forward<Args>(args)...);
}

template <class T, class... Args> T make_plain(Args&&... args) {
    return T(args...);
}

int main() {
    Noisy n1(1), n2(2);
    std::puts("[1] make_fwd<Duo>(n1, n2)");
    { Duo d = make_fwd<Duo>(n1, n2); (void)d; }
    std::puts("[2] make_fwd<Duo>(Noisy(3), Noisy(4))");
    { Duo d = make_fwd<Duo>(Noisy(3), Noisy(4)); (void)d; }
    std::puts("[3] make_fwd<Duo>(n1, Noisy(5))");
    { Duo d = make_fwd<Duo>(n1, Noisy(5)); (void)d; }
    std::puts("[4] make_plain<Duo>(n1, n2)");
    { Duo d = make_plain<Duo>(n1, n2); (void)d; }
    std::puts("[5] make_plain<Duo>(Noisy(3), Noisy(4))");
    { Duo d = make_plain<Duo>(Noisy(3), Noisy(4)); (void)d; }
    std::puts("[6] make_plain<Duo>(n1, Noisy(5))");
    { Duo d = make_plain<Duo>(n1, Noisy(5)); (void)d; }
}
```

- ★★★ `[2]` 와 `[5]` 가 찍는 줄은 각각?
- ★★ `[3]` 과 `[6]` 은?

### 4. ★★ 점 셋의 자리 (예측)

```cpp
/* pack04.cpp */
// ... 을 어디에 붙이나 — 같은 팩, 두 자리
#include <cstdio>

int g(int x) {
    std::printf("  g(%d)\n", x);
    return x * 10;
}
template <class... Ts> int g(Ts... xs) {
    std::printf("  g(pack of %zu)\n", sizeof...(xs));
    return (0 + ... + xs);
}
template <class... Ts> void f(Ts... xs) {
    std::printf("  f got %zu args:", sizeof...(xs));
    ((std::printf(" %d", xs)), ...);
    std::printf("\n");
}

template <class... Ts> void outside(Ts... args) { f(g(args)...); }
template <class... Ts> void inside(Ts... args) { f(g(args...)); }

int main() {
    std::puts("[1] f(g(args)...) with 1, 2, 3");
    outside(1, 2, 3);
    std::puts("[2] f(g(args...)) with 1, 2, 3");
    inside(1, 2, 3);
}
```

- ★★ `[1]` · `[2]` 에서 `f got N args` 의 `N` 과 값은?
- ★★★ `[1]` 의 `g(…)` 세 줄은 어떤 순서로 찍히나 — 두 컴파일러가 같은가?

### 5. ★★ 원소마다 타입 (예측)

```cpp
/* pack05.cpp */
// 팩의 원소마다 타입을 찍는다 — char · short · float · bool 을 넘긴다
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <typeinfo>

template <class T> void one(const T&) {
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(T).name(), nullptr, nullptr, &st);
    std::printf("  %-6s sizeof=%zu\n", s, sizeof(T));
    std::free(s);
}

template <class... Ts> void each(const Ts&... xs) { (one(xs), ...); }

int main() {
    char c = 'a';
    short s = 2;
    float f = 1.5f;
    bool b = true;
    each(c, s, f, b);
}
```

- ★★ 네 줄의 타입 이름과 `sizeof` 는?

### 6. ★★★ 빈 팩과 단항 폴드 (왜)

- ★★★ 빈 팩에서 단항 폴드가 **되는 연산자와 안 되는 연산자**를 가르는 기준은 무엇인가 — 안 되는 쪽의 처방은?

### 7. ★★★ `forward` 가 필요한 이유 (왜)

- ★★★ 3번의 두 팩토리는 둘 다 `Args&&...` 로 받는다 — 로그가 **갈리는 칸과 안 갈리는 칸**을 가르는 기준은?

### 8. ★★ 인자 계산 순서 (경계)

- ★★ 4번 `[1]` 의 `g(…)` 세 줄의 순서는 다섯 층 중 어디인가 — 순서를 보장하려면 무엇을 쓰나(같은 파일 안에 답이 있다)?

### 9. ★★ 결합 방향 (경계)

- ★★ 2번에서 좌·우 꼴이 **값을 바꾸는 연산자와 안 바꾸는 연산자**를 가르는 성질은? 안 바꾸는 쪽이면 꼴을 아무렇게나 골라도 되나(빈 팩 칸을 보라)?

### 10. 다른 주제와 잇기 (연결)

- ★★ 5번 결과를 C 의 `f(int n, ...)` 에 `char`·`short`·`float`·`_Bool` 을 넘긴 것과 견주면?
- ★ Go 의 `func f(xs ...int)` 는 C 와 C++ 중 어느 쪽에 가깝나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
