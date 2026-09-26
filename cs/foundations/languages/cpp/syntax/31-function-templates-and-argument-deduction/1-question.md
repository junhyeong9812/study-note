# cpp/syntax/31 — 함수 템플릿과 인자 추론 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「틀(매개변수 꼴)에 인자를 눌렀을 때 틀 밖으로 남는 것이 `T` 다」** 를 칸마다 따라가는 것이다 — 「`T` 는 인자의 타입」으로 뭉개지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux · 대비 rustc 1.92.0.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 두 컴파일러에게 `T` 를 말하게 하는 것이다**(1·2번). ★★ 짝은 **기호표(5번).**
> ★ **「부적용인 창」이 있다** — ASan(추론은 실행 전에 끝난다) · 경고 격자(격자의 모든 칸이 경고 0).
> ★★★ **05편·09편이 잰 것은 다시 묻지 않는다** — `auto` 의 감쇠와 `const` 제거 · `T&&` 의 참조 축약.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 일부러 실패하는 `static_assert` (예측)

```cpp
/* tmpl01.cpp */
// 추론된 T 를 컴파일러가 말하게 한다 — 일부러 실패하는 static_assert
#include <type_traits>

template <class T>
void probe(T) {
    static_assert(std::is_same_v<T, void>, "T 를 보여 달라");
}

int main() {
    const int ci = 1;
    probe(ci);
    probe("hi");
}
```

- ★★★ 두 호출에서 에러가 적어 주는 **`T`** 는 각각 무엇인가?
- ★ 에러는 몇 건인가 — 두 컴파일러가 `T` 를 **어디에** 적나?

### 2. ★★★ 인자 여섯 × 매개변수 꼴 넷 (예측)

```cpp
/* tmpl02.cpp */
// 인자 여섯 × 매개변수 꼴 넷 — 추론된 T 를 컴파일러의 __PRETTY_FUNCTION__ 에서 잘라 찍는다
#include <cstdio>
#include <cstring>

template <class T>
const char* name_of() { return __PRETTY_FUNCTION__; }

// __PRETTY_FUNCTION__ 에서 「T = 」 뒤부터 마지막 「]」 앞까지만 찍는다
void print_T(const char* pf) {
    const char* s = std::strstr(pf, "T = ") + 4;
    const char* e = std::strrchr(pf, ']');
    std::printf("%-22.*s", (int)(e - s), s);
}

template <class T> void by_value(T)       { print_T(name_of<T>()); }
template <class T> void by_ref(T&)        { print_T(name_of<T>()); }
template <class T> void by_cref(const T&) { print_T(name_of<T>()); }
template <class T> void by_fwd(T&&)       { print_T(name_of<T>()); }

void func(int) {}

#define ROW(label, arg)                                    \
    std::printf("%-18s", label);                           \
    by_value(arg); by_ref(arg); by_cref(arg); by_fwd(arg); \
    std::printf("\n");

int main() {
    int arr[3] = {};
    const int ci = 1;
    int i = 2;
    int& ri = i;
    const int& cri = i;
    std::printf("%-18s%-22s%-22s%-22s%-22s\n", "arg", "T", "T&", "const T&", "T&&");
    ROW("int arr[3]", arr)
    ROW("const int ci", ci)
    ROW("int& ri", ri)
    ROW("const int& cri", cri)
    ROW("\"hi\"", "hi")
    ROW("void func(int)", func)
}
```

```bash
# tmpl-grid.sh
# tmpl-grid.sh — 같은 격자를 두 컴파일러로 찍고, 공백을 지운 뒤 칸마다 견준다
g++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o gx && ./gx | tail -n +2 > g.txt
clang++ -std=c++20 -Wall -Wextra -pedantic tmpl02.cpp -o cx && ./cx | tail -n +2 > c.txt
cells() { while IFS= read -r line; do for i in 0 1 2 3; do printf '%s\n' "${line:$((18+22*i)):22}" | tr -d ' '; done; done < "$1"; }
paste -d'|' <(cells g.txt) <(cells c.txt) > both.txt
total=$(wc -l < both.txt)
differ=$(awk -F'|' '$1 != $2' both.txt | wc -l)
ref=$(cut -d'|' -f1 both.txt | grep -c '&')
ptr=$(cut -d'|' -f1 both.txt | grep -c '\*')
echo "두 컴파일러가 다른 T 를 낸 칸 $differ / $total"
echo "T 에 & 가 들어간 칸 $ref / $total · T 에 * 가 생긴 칸 $ptr / $total"
rm -f gx cx g.txt c.txt both.txt
```

- ★★★ 24칸의 `T` 를 채워라 — **감쇠가 일어나는 열**과 **`T` 가 참조가 되는 열**은?
- ★★ `const int ci` 가 `T&` 와 `const T&` 에서 각각 무엇이 되나?
- ★★ 두 컴파일러가 **다른 `T`** 를 내는 칸은 몇 개인가?

### 3. ★★★ 다섯 호출 — 각각 컴파일되나 (예측)

```cpp
/* tmpl03.cpp */
// 다섯 호출 — 각각 T 를 추론할 수 있나
#include <initializer_list>
#include <type_traits>

template <class T> T max_of(T a, T b) { return a < b ? b : a; }
template <class T> T make() { return T{}; }
template <class T> void take(T) {}
template <class T> void exact(std::type_identity_t<T>) {}

int main() {
    max_of(1, 2.0);          // 1. int 와 double
    make();                  // 2. 인자 없이
    take({1, 2, 3});         // 3. 중괄호 목록
    exact(1);                // 4. type_identity_t<T> 매개변수
    int n = make();          // 5. int 변수로 받는다
    (void)n;
}
```

- ★★★ 몇 번 줄이 에러인가 — 두 컴파일러에서 같은가?
- ★★ 1. 의 진단은 무엇을 두 개 적나?
- ★★ 5. 는 **받는 변수의 타입**이 있는데도 결과가 2. 와 같은가?

### 4. ★★ 같은 호출에 `T` 를 적어 준다 (예측)

```cpp
/* tmpl04.cpp */
// 같은 네 호출에 T 를 직접 적는다 — 그리고 auto 는 중괄호 목록을 무엇으로 받나
#include <cstdio>
#include <cstring>
#include <initializer_list>
#include <type_traits>

template <class T>
const char* name_of() { return __PRETTY_FUNCTION__; }

void print_T(const char* label, const char* pf) {
    const char* s = std::strstr(pf, "T = ") + 4;
    const char* e = std::strrchr(pf, ']');
    std::printf("%-44s %.*s\n", label, (int)(e - s), s);
}

template <class T> T max_of(T a, T b) { return a < b ? b : a; }
template <class T> T make() { return T{}; }
template <class T> void take(T) { print_T("  T inside take", name_of<T>()); }
template <class T> void exact(std::type_identity_t<T>) { print_T("  T inside exact", name_of<T>()); }

int main() {
    std::printf("max_of<double>(1, 2.0) = %.1f\n", max_of<double>(1, 2.0));
    std::printf("make<int>() = %d\n", make<int>());
    std::printf("take<std::initializer_list<int>>({1, 2, 3})\n");
    take<std::initializer_list<int>>({1, 2, 3});
    std::printf("exact<long>(1)\n");
    exact<long>(1);
    auto il = {1, 2, 3};
    print_T("auto il = {1, 2, 3};  decltype(il)", name_of<decltype(il)>());
}
```

- ★★ 네 호출은 통과하나 — `take` · `exact` 안의 `T` 는?
- ★★ `auto il = {1, 2, 3};` 의 타입은?

### 5. ★★ 네 인자로 세 함수 템플릿을 부른다 — 기호표 (예측)

```cpp
/* tmpl05.cpp */
// 네 인자로 세 함수 템플릿을 부른다 — 인스턴스는 몇 개 생기나
template <class T> void by_value(T) {}
template <class T> void by_ref(T&) {}
template <class T> void by_fwd(T&&) {}

void call_all() {
    int i = 0;
    const int ci = 0;
    int& ri = i;
    const int& cri = i;
    by_value(i); by_value(ci); by_value(ri); by_value(cri);
    by_ref(i);   by_ref(ci);   by_ref(ri);   by_ref(cri);
    by_fwd(i);   by_fwd(ci);   by_fwd(ri);   by_fwd(cri);
}
```

```bash
# tmpl-inst.sh
# tmpl-inst.sh — 오브젝트 파일의 기호표에서 템플릿마다 인스턴스를 센다
for c in g++ clang++; do
  $c -std=c++20 -c tmpl05.cpp -o t5.o
  printf '%-8s by_value %d개 · by_ref %d개 · by_fwd %d개\n' "$c" \
    "$(nm -C t5.o | grep -c ' by_value<')" "$(nm -C t5.o | grep -c ' by_ref<')" "$(nm -C t5.o | grep -c ' by_fwd<')"
done
nm -C t5.o | grep -E ' W ' | sed 's/^0*//' | sort
rm -f t5.o
```

- ★★★ `by_value` · `by_ref` · `by_fwd` 의 **인스턴스 수**는 각각?

### 6. ★★ 같은 두 호출을 Rust 로 (예측)

```rust
// infer.rs
// C++ 에서 추론이 멈춘 두 자리를 Rust 로 — --cfg 로 하나씩 켠다(mixed · bare). 아무것도 안 켜면 타입을 적은 판
fn max_of<T: PartialOrd>(a: T, b: T) -> T {
    if a < b { b } else { a }
}

fn make<T: Default>() -> T {
    T::default()
}

fn main() {
    #[cfg(mixed)]
    let m = max_of(1, 2.0);
    #[cfg(bare)]
    let m = make();
    #[cfg(not(any(mixed, bare)))]
    let m: i64 = make();
    #[cfg(not(any(mixed, bare)))]
    println!("make() -> {} · max_of(1, 2) -> {}", m, max_of(1, 2));
    #[cfg(any(mixed, bare))]
    let _ = m;
}
```

- ★★ `--cfg mixed` · `--cfg bare` 는 각각 **어떤 에러 코드**를 내나?
- ★★★ 아무 cfg 도 안 켠 판(`let m: i64 = make();`)은 컴파일되나 — C++ 의 3번 5. 와 무엇이 다른가?

### 7. ★★★ 틀이 `const` 를 가져가는 방식 (왜)

- ★★★ 2번에서 `T&` 는 `const` 를 `T` 에 **남기고** `const T&` 는 **안 남긴다** — 왜 그렇게 되나?
- ★★ 그래서 `T&` 매개변수가 `const` 인자를 받으면 함수 안에서 무엇을 못 하나?

### 8. ★★★ 추론과 변환의 순서 (왜)

- ★★★ `max_of(1, 2.0)` 이 `double` 로 맞춰지지 않는 이유는 — 01편의 오버로드 해석과 **어느 단계**가 다른가?

### 9. ★★ 조용한 성공 (경계)

- ★★★ 추론이 **실패하면** 에러가 크게 난다. 추론이 **기대와 다르게 성공하면**(배열 → 포인터) 무엇이 알려 주나 — 그래서 1번의 탐침이 왜 필요한가?

### 10. ★★ `__PRETTY_FUNCTION__` 으로 잰 것의 층 (경계)

- ★★ 2번 격자의 **`T` 자체**와 **그 철자**(`int*` 대 `int *` · `long int` 대 `long`)는 각각 다섯 층 중 어디인가?
- ★ `__PRETTY_FUNCTION__` 은 표준 식별자인가 — `-pedantic` 은 무엇이라 했나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 05편의 `auto a = arr;` · `auto& b = arr;` 결과는 2번 격자의 **어느 두 칸**과 같은가?
- ★ 09편의 「에러가 여섯 줄」과 이 편 5번의 인스턴스 수는 **같은 사실**의 두 얼굴이다 — 무엇인가?
- ★ 「컴파일러가 추론한 타입을 에러로 말하게 하는」 같은 원리의 탐침을 쓰는 다른 갈래는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
