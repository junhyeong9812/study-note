# cpp/syntax/32 — 클래스 템플릿과 CTAD(C++17) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「생성자마다 가상의 함수 템플릿을 세우고 31편의 추론을 돌린다」** 를 칸마다 따라가는 것이다 — 「CTAD 는 알아서 맞는 타입을 고른다」로 뭉개지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13(두 컴파일러 공용) · x86-64 Linux.
> 기본 명령은 `g++ -std=c++17 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`. 판이 결론을 가르는 문항은 `-std=` 를 문항에 적었다.
> ★★★ **이 주제의 본체는 두 컴파일러 × 두 판에게 「무슨 타입이냐」를 묻는 격자다**(2번). ★★ 짝은 **기호표(6번).**
> ★ **「부적용인 창」이 있다** — ASan(CTAD 는 실행 전에 끝난다) · 경고 격자(통과한 칸은 전부 경고 0).
> ★★★ **31편이 잰 것은 다시 묻지 않는다** — 값 매개변수의 감쇠 · `max_of(1, 2.0)` 의 충돌 · 명시 지정.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 같은 소스를 두 판으로 (예측)

```cpp
/* ctad01.cpp */
// 클래스 템플릿 하나 — 템플릿 인자를 적은 선언과, -DOMIT 이면 안 적은 선언
#include <cstdio>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
    T get() const { return v; }
};

int main() {
    Box<int> a(1);
    std::printf("a.get() = %d\n", a.get());
#ifdef OMIT
    Box b(2);
    std::printf("b.get() = %d\n", b.get());
#endif
}
```

- ★★ `-DOMIT` 없이 `-std=c++14` 로 던지면 두 컴파일러는?
- ★★★ `-DOMIT` 를 켜고 `-std=c++14` 로, 그리고 `-std=c++17` 로 던지면 각각?

### 2. ★★★ 선언 11 × 판 2 × 컴파일러 2 (예측)

```cpp
/* ctad02.cpp */
// 선언 하나를 -DCASE=n 으로 골라 컴파일하고, 추론된 타입의 맹글링 이름을 찍는다
#include <array>
#include <cstdio>
#include <typeinfo>
#include <utility>
#include <vector>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
    Box(T x, T) : v(x) {}
};

template <class T, class U> struct Duo {
    T a;
    U b;
    Duo(T x, U y) : a(x), b(y) {}
};

int main() {
    std::vector<int> v2{1, 2};
    (void)v2;
#if CASE == 1
    Box x{1};
#elif CASE == 2
    Box x(1);
#elif CASE == 3
    Box x = 1;
#elif CASE == 4
    Box x{"hi"};
#elif CASE == 5
    Box x{1, 2.0};
#elif CASE == 6
    Duo x{1, 2.0};
#elif CASE == 7
    std::vector x{1, 2};
#elif CASE == 8
    std::vector x{v2};
#elif CASE == 9
    std::vector x{v2, v2};
#elif CASE == 10
    std::pair x{1, "a"};
#elif CASE == 11
    std::array x{1, 2, 3};
#endif
    std::puts(typeid(x).name());
}
```

```bash
# ctad-grid.sh
# ctad-grid.sh — 선언 11개 × 표준 두 판 × 컴파일러 둘. 칸마다 추론된 타입(c++filt -t) 또는 error
decl=('Box x{1};' 'Box x(1);' 'Box x = 1;' 'Box x{"hi"};' 'Box x{1, 2.0};' 'Duo x{1, 2.0};'
      'std::vector x{1, 2};' 'std::vector x{v2};' 'std::vector x{v2, v2};' 'std::pair x{1, "a"};' 'std::array x{1, 2, 3};')
cell() {  # $1 컴파일러 $2 표준 $3 CASE — 칸 하나를 찍는다
  if $1 -std=$2 -DCASE=$3 ctad02.cpp -o gx 2>/dev/null; then ./gx | c++filt -t; else echo error; fi
}
printf '%s\t%s\t%s\t%s\t%s\n' "선언" "g++ c++14" "g++ c++17" "clang++ c++14" "clang++ c++17" > grid.tsv
for n in $(seq 1 ${#decl[@]}); do
  row="${decl[$((n-1))]}"
  for c in g++ clang++; do for s in c++14 c++17; do row="$row"$'\t'"$(cell $c $s $n)"; done; done
  printf '%s\n' "$row" >> grid.tsv
done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 5' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
std_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($2 != $3) + ($4 != $5) } END { print n }')
cc_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($2 != $4) + ($3 != $5) } END { print n }')
echo "c++14 대 c++17 이 갈린 칸 $std_split / $((rows * 2)) · g++ 대 clang++ 가 갈린 칸 $cc_split / $((rows * 2))"
rm -f gx grid.tsv
```

- ★★★ 11행의 c++17 칸을 채워라 — 특히 `Box x{"hi"}` · `Box x{1, 2.0}` · `std::vector x{v2}` · `std::vector x{v2, v2}`.
- ★★ 마지막 줄의 두 숫자는?

### 3. ★★ 가이드 한 줄 (예측)

```cpp
/* ctad03.cpp */
// 추론 가이드 한 줄 — -DWITH_GUIDE 이면 문자열 리터럴을 std::string 으로 받게 한다
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <string>
#include <typeinfo>

template <class T> struct Box {
    T v;
    Box(T x) : v(x) {}
};

#ifdef WITH_GUIDE
Box(const char*) -> Box<std::string>;
#endif

int main() {
    Box x{"hi"};
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(x).name(), nullptr, nullptr, &st);
    std::printf("decltype(x) = %s\n", s);
    std::printf("sizeof(x)   = %zu\n", sizeof(x));
    std::free(s);
}
```

- ★★ 가이드 없이 · `-DWITH_GUIDE` 로 — `decltype(x)` 는 각각?
- ★ `sizeof(x)` 의 두 값 중 **표준이 정한 것**이 있나?

### 4. ★★★ 인자를 일부만 적는다 (예측)

```cpp
/* ctad04.cpp */
// 템플릿 인자를 일부만 적는다 — 함수 템플릿과 클래스 템플릿
#include <cstdio>

template <class T, class U> struct Duo {
    T a;
    U b;
    Duo(T x, U y) : a(x), b(y) {}
};

template <class T, class U> Duo<T, U> make_duo(T x, U y) { return Duo<T, U>(x, y); }

int main() {
    auto f = make_duo<long>(1, 2.0);   // 함수 템플릿 — T 만 적고 U 는 추론
    std::printf("%zu %zu\n", sizeof(f.a), sizeof(f.b));
#ifdef PARTIAL
    Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
    (void)d;
#endif
}
```

- ★★ `-DPARTIAL` 없이는 무엇이 찍히나?
- ★★★ `-DPARTIAL` 을 켜면 두 컴파일러는 무엇이라 하나?

### 5. ★★ 생성자 없는 템플릿 구조체 (예측)

```cpp
/* ctad05.cpp */
// 생성자가 없는 집합체 — 중괄호 목록에서 T 를 추론하나
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <typeinfo>

template <class T> struct Agg {
    T a;
    T b;
};

int main() {
    Agg x{1, 2};
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(x).name(), nullptr, nullptr, &st);
    std::printf("decltype(x) = %s · a + b = %d\n", s, x.a + x.b);
    std::free(s);
}
```

- ★★ `-std=c++17` · `-std=c++20` 에서 각각 컴파일되나 — 두 컴파일러가 같은가?

### 6. ★★★ 성립할 수 없는 몸통을 가진 멤버 (예측)

```cpp
/* ctad06.cpp */
// 클래스 템플릿의 멤버 함수 — 한 멤버는 int 로는 컴파일될 수 없는 몸통을 가졌다
#include <cstdio>

template <class T> struct Box {
    T v;
    T get() const { return v; }
    void odd() const { v.no_such_member(); }
};

int main() {
    Box<int> b{7};
    std::printf("%d\n", b.get());
#ifdef CALL_ODD
    b.odd();
#endif
}
```

- ★★★ `-DCALL_ODD` 없이 `-c` 로 컴파일하면 `exit` 는? `nm -C` 에 `Box` 의 기호는 무엇이 보이나?
- ★★ `-DCALL_ODD` 를 켜면 에러가 **몇 행**을 가리키고, 호출한 14행은 어디에 나오나?

### 7. ★★★ 생성자 말고 하나 더 (왜)

- ★★★ CTAD 가 `Box` 의 두 생성자에서 세우는 후보 말고 **늘 하나 더** 세우는 후보는 무엇인가 — 그것이 2번의 `std::vector x{v2}` 칸과 어떻게 이어지나?

### 8. ★★ CTAD 가 31편을 빌려 쓴다는 증거 (왜)

- ★★ 2번 격자의 **`Box x{"hi"}` 칸**과 **`Box x{1, 2.0}` 칸**은 31편의 어느 칸·어느 문항과 같은 매개변수 꼴인가?

### 9. ★★ 일부만 적기 (경계)

- ★★ 「템플릿 인자를 앞쪽만 적고 나머지는 추론」의 규칙을 함수 템플릿과 클래스 템플릿에서 **각각 한 문장**으로 말하라.

### 10. ★★ 표준 컨테이너 행의 근거 (경계)

- ★★ 2번 격자의 g++ 대 clang++ 비교에서 **`std::` 행**은 무엇까지를 증명하고 무엇은 증명하지 못하나?

### 11. 다른 주제와 잇기 (연결)

- ★★ Java 의 다이아몬드 `new HashMap<>()` 와 C++ CTAD 는 **어느 쪽에서** 타입을 가져오나?
- ★★ C++ 템플릿의 몸통을 검사하는 시점과 Rust 제네릭의 몸통을 검사하는 시점은 어떻게 다른가?
- ★ 6번의 `odd()` 가 들어 있는 클래스를 **명시적 인스턴스화**하면 어떻게 되나 — 어느 편이 던졌나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
