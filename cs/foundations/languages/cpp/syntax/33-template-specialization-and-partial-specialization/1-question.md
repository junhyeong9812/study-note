# cpp/syntax/33 — 특수화와 부분 특수화 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「클래스는 맞는 판 중 가장 좁은 것, 함수는 기본 템플릿을 먼저 고르고 그다음 특수화」** 를 칸마다 따라가는 것이다 — 두 규칙을 하나로 뭉개지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(두 컴파일러 공용) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 두 컴파일러에게 「어느 판을 골랐나」를 묻는 격자다**(1번). ★★ 짝은 **기호표(4번).**
> ★ **「부적용인 창」이 있다** — ASan(판 고르기는 실행 전에 끝난다) · 경고 격자(통과한 칸은 전부 경고 0).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 인자 9 × 컴파일러 2 (예측)

```cpp
/* spec01.cpp */
// 기본 템플릿 하나 + 특수화 넷. 인자 타입 하나를 -DARG=… 로 골라 어느 판이 골라졌는지 찍는다
#include <cstddef>
#include <cstdio>

template <class T> struct Pick { static constexpr const char* which = "primary"; };
template <> struct Pick<int> { static constexpr const char* which = "full <int>"; };
template <class T> struct Pick<T*> { static constexpr const char* which = "partial <T*>"; };
template <class T> struct Pick<const T> { static constexpr const char* which = "partial <const T>"; };
template <class T, std::size_t N> struct Pick<T[N]> { static constexpr const char* which = "partial <T[N]>"; };

int main() {
    std::puts(Pick<ARG>::which);
}
```

```bash
# spec-grid.sh
# spec-grid.sh — 인자 타입 9개 × 컴파일러 둘. 칸마다 골라진 판 또는 error
args=('int' 'int*' 'const int*' 'int* const' 'const int' 'char[3]' 'const char[3]' 'double' 'const int* const')
cell() {  # $1 컴파일러 $2 인자 타입
  if $1 -std=c++20 -Wall -Wextra -pedantic "-DARG=$2" spec01.cpp -o gx 2>/dev/null; then ./gx; else echo error; fi
}
printf '%s\t%s\t%s\n' "인자" "g++" "clang++" > grid.tsv
for a in "${args[@]}"; do
  printf '%s\t%s\t%s\n' "$a" "$(cell g++ "$a")" "$(cell clang++ "$a")" >> grid.tsv
done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 3' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
split=$(tail -n +2 grid.tsv | awk -F'\t' '$2 != $3' | wc -l)
err=$(tail -n +2 grid.tsv | awk -F'\t' '$2 == "error"' | wc -l)
echo "g++ 대 clang++ 가 갈린 칸 $split / $rows · error 인 행 $err / $rows"
rm -f gx grid.tsv
```

- ★★★ 9행의 칸을 채워라 — 특히 `const int*` · `int* const` · `const int` · `const char[3]`.
- ★★ 마지막 줄의 두 숫자는?

### 2. ★★★ 함수 템플릿의 `name<T*>` (예측)

```cpp
/* spec02.cpp */
// 함수 템플릿에 부분 특수화를 시도한다
#include <cstdio>

template <class T> void name(T) { std::puts("primary"); }
template <class T> void name<T*>(T*) { std::puts("pointer"); }

int main() {
    int i = 0;
    name(&i);
}
```

- ★★★ 두 컴파일러는 이것을 받나 — 받지 않는다면 **몇 행**에서, 호출이 있든 없든?

### 3. ★★ 두 번째 `name` (예측)

```cpp
/* spec03.cpp */
// 같은 의도를 오버로드로 — 두 번째 함수 템플릿을 하나 더 선언한다
#include <cstdio>

template <class T> void name(T) { std::puts("primary"); }
template <class T> void name(T*) { std::puts("pointer overload"); }

int main() {
    int i = 0;
    const int ci = 0;
    name(i);
    name(&i);
    name(&ci);
    name("hi");
}
```

- ★★ 네 호출이 찍는 줄은?

### 4. ★★★ 세 선언의 순서 (예측)

```cpp
/* spec04.cpp */
// 선언 세 개 — 기본 템플릿 (a), 포인터 오버로드 (b), int* 전체 특수화 (c).
// -DSPEC_FIRST 이면 (c) 를 (b) 보다 앞에 둔다
#include <cstdio>

template <class T> void f(T) { std::puts("(a) f(T)"); }
#ifdef SPEC_FIRST
template <> void f<>(int*) { std::puts("(c) f<>(int*)"); }
template <class T> void f(T*) { std::puts("(b) f(T*)"); }
#else
template <class T> void f(T*) { std::puts("(b) f(T*)"); }
template <> void f<>(int*) { std::puts("(c) f<>(int*)"); }
#endif

int main() {
    int i = 0;
    f(&i);
}
```

```bash
# spec-nm.sh
# spec-nm.sh — spec04.cpp 를 선언 순서 두 판으로. f 의 기호가 무엇으로 생기나(T = 보통 함수 정의 · W = 암묵 인스턴스)
for c in g++ clang++; do for d in '' -DSPEC_FIRST; do
  $c -std=c++20 $d -c spec04.cpp -o s4.o
  printf '== %s %s\n' "$c" "${d:-(기본 순서)}"
  nm -C s4.o | grep ' f<' | sed 's/^0*//'
done; done
rm -f s4.o
```

- ★★★ 기본 순서와 `-DSPEC_FIRST` 에서 `f(&i)` 가 찍는 줄은 각각?
- ★★★ `spec-nm.sh` 가 두 순서에서 찍는 `f` 의 기호는 각각 무엇인가 — 글자(`T`/`W`)까지.

### 5. ★★ `vector<char>` 와 `vector<bool>` (예측)

```cpp
/* spec05.cpp */
// vector<bool> 과 vector<char> — 원소 하나의 주소를 bool* / char* 로 받는다
#include <vector>

int main() {
    std::vector<char> vc{1, 0};
    char* pc = &vc[0];
    (void)pc;
    std::vector<bool> vb{true, false};
    bool* pb = &vb[0];
    (void)pb;
}
```

- ★★ 두 초기화 중 어느 쪽이 에러인가 — 컴파일러마다 몇 건인가?

### 6. ★★ `operator[]` 가 돌려주는 것 (예측)

```cpp
/* spec06.cpp */
// vector<bool>::operator[] 가 돌려주는 것의 타입과 크기
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <type_traits>
#include <typeinfo>
#include <vector>

template <class T> void show(const char* label) {
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(T).name(), nullptr, nullptr, &st);
    std::printf("%-34s %s\n", label, s);
    std::free(s);
}

int main() {
    std::vector<char> vc{1, 0};
    std::vector<bool> vb{true, false};
    show<decltype(vc[0])>("decltype(vc[0])");
    show<decltype(vb[0])>("decltype(vb[0])");
    std::printf("%-34s %d\n", "is_reference of decltype(vb[0])", (int)std::is_reference<decltype(vb[0])>::value);
    std::printf("%-34s %d\n", "is_reference of decltype(vc[0])", (int)std::is_reference<decltype(vc[0])>::value);
}
```

- ★★ 네 줄의 오른쪽 칸은?

### 7. ★★★ `const` 가 붙은 자리 (왜)

- ★★★ 1번의 `const int*` 와 `int* const` 가 각각 어느 판으로 갔는지를 **`T` 가 무엇이 되는지**로 설명하라.

### 8. ★★★ `-DSPEC_FIRST` 판의 `f<>(int*)` (왜)

- ★★★ 4번 `-DSPEC_FIRST` 판의 결과를 **오버로드 해석의 단계**로 설명하라 — 전체 특수화는 어느 단계에서 고려되나?

### 9. ★★ 실행 출력이 못 보는 것 (경계)

- ★★ 4번의 실행 출력만으로 알 수 **없는** 것은 무엇이고, 기호표는 그것을 어떻게 보여 줬나?

### 10. ★★ 부분 특수화의 선언 순서 (경계)

- ★★ 1번의 `<const T>` 와 `<T[N]>` 의 **선언 순서를 바꾸면** `const char[3]` 칸이 달라지리라 보나 — 4번과 무엇이 다른가?

### 11. 다른 주제와 잇기 (연결)

- ★★ 3번의 `name("hi")` 호출에서 인자가 `T*` 꼴에 맞춰지는 과정은 31편의 어느 칸과 같은 현상인가?
- ★ C# 제네릭과 비교하면 C++ 특수화는 무엇을 **할 수 있는** 것인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
