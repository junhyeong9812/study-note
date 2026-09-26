# cpp/syntax/30 — 댕글링 참조와 수명 연장 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 참조 초기화(임시의 수명)](https://en.cppreference.com/w/cpp/language/reference_initialization) · [cppreference — 범위 기반 `for`](https://en.cppreference.com/w/cpp/language/range-for) · [cppreference — C++23 컴파일러 지원표](https://en.cppreference.com/w/cpp/compiler_support/23)\
> ★ **위 cppreference 세 쪽은 이 배치에서 열었다** — (4)의 「연장되지 않는 예외 넷」, (5)의 「`__cpp_range_based_for` 의 C++23 값 `202211L`」과 「P2718 을 구현한 판(GCC 15 · Clang 19)」이 거기서 왔다. **표준 원문은 열지 않았다.**
> **실행 검증** — 이 문서의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 대비 블록은 **rustc 1.92.0** · **go1.27.1** 이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`dang01.cpp` \~ `dang03.cpp` · `dang-grid.sh` · `dang-uar.sh` · `dang-values.sh` · `dangle.rs` · `esc.go`).\
> ★★★ **이 주제는 UB 의 교과서다 — 댕글링을 읽은 값은 「이 판의 한 결과」이고, 이 문서는 그 값에서 아무 규칙도 끌어내지 않는다**(규칙 14). 그래서 탐침은 **값 대신 「42 였나」 한 비트**만 찍는다.\
> ★★★ **ASan 블록은 마커를 `stderr` 로 찍었다** · 자른 블록은 **자르는 명령을 배너에** 적었다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 임시를 `const T&`·`T&&` 에 묶으면 늘어난다는 규칙은 **C++98/11부터** · **괄호 집합체 초기화(`H h(T{8})`)는 C++20부터이고 그 참조 멤버는 늘어나지 않는다** · **범위 `for` 의 임시 수명 연장은 C++23(P2718)** 이다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **[07번](../07-references-vs-pointers/)·[14번](../14-destructors-and-deterministic-destruction/)에서 온다 — 앞 편들이 잰 것은 다시 재지 않고 인용한다.**\
> [07번](../07-references-vs-pointers/) (5) — **`const Noisy& r = make(1);` 은 블록 끝까지 산다**(수명 연장의 기본형) · (7) — **지역 참조·포인터 반환은 g++ 에서 같은 `-Wreturn-local-addr` · `cc exit=0`**.\
> [14번](../14-destructors-and-deterministic-destruction/) (4) — **임시는 전체 식의 끝에서 죽는다 · `std::string("…").c_str()` 는 g++ 침묵, clang 만 `-Wdangling-gsl`**.\
> [08번](../08-value-categories-lvalue-prvalue-xvalue/) (7) — **`T&&` 도 prvalue 를 늘린다 · xvalue 는 늘 것이 없다**(`&r == &local`).\
> [05번](../05-auto-and-decltype-type-deduction/) (6) — **`decltype(auto)` 의 `return (x);` 댕글링 — 두 컴파일러 경고 · `run exit=139`**.\
> ★★ **여기서 새로 묻는 것은 셋이다** — **댕글링 일곱 모양 × 도구 여섯, 잡은 칸은 몇인가** · **수명 연장이 되는 것과 안 되는 것의 경계** · **범위 `for` 의 임시가 C++23 판에서 고쳐졌나(이 두 컴파일러에서)**.
> **경계** — 「**누가 아직 보고 있는가**」의 **논증은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절**이 정본이다(「지역 객체에 대한 포인터·참조 반환은 여전히 컴파일된다」). 여기는 **코드 패턴과 도구의 칸**이다.\
> 「람다 캡처」 전반은 [목록의 **39번 주제**](../39-lambdas-and-captures/), 「`string_view`」는 **46번 주제**, 「이터레이터 무효화」는 **43번 주제**가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **도구 없이 돌린 댕글링 탐침이 42 를 읽었나**((3) — **UB 의 결과**다. 이 판에서는 세 번 돌려 같았지만 성질로 적지 않는다) | ★★★ **격자 칸마다 도구가 댄 이름 · 「잡은 칸 N / 42」**((1)) · **ASan 옵션을 바꿨을 때의 칸**((2)) |
> | ASan 리포트의 **PID**·주소 · 스택 오프셋 | ★★★ **수명 연장 로그의 순서**(소멸자가 「다음 문장」 앞이냐 뒤냐 — (4)) — **표준이 정한 순서**다 |
> | UB 로 죽을 때의 신호 번호(`rc=139`) | ★★ **`__cplusplus` · `__cpp_range_based_for` 값**((5)) · **Rust 에러 코드**((6)) · **Go 의 `moved to heap`**((7)) |

## 한눈에 — 쉽게 말하면

**댕글링 참조는 「철거된 집의 주소가 적힌 명함」이다.**

명함(참조)은 **집(객체)이 철거돼도 멀쩡하다.** 그 주소로 찾아가면 **빈터일 수도, 새 집일 수도, 우연히 옛 집 그대로일 수도** 있다 — 그래서 무서운 것은 「**찾아갔더니 멀쩡했다**」이다((3)).\
**수명 연장은 「철거 예정인 가건물을 명함 주인이 이사 갈 때까지 세워 두는 특례」** 다. 단 **특례가 붙는 모양이 정해져 있다** — 명함을 **직접** 받았을 때만이고, **중개인(함수)을 거쳐 받은 명함에는 안 붙는다**((4)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 철거된 집의 명함 | ★★★ **댕글링 참조·포인터·뷰·람다 캡처** — 일곱 모양 | (1) |
| 명함 검사관들 | ★★★ **g++ 경고 · clang 경고 · 두 ASan(-O0 · -O2)** — **잡은 칸 30 / 42** | (1) |
| 검사관이 쉬는 날 | ★★ **`detect_stack_use_after_return=0` · clang `-O2`** | (1)(2) |
| 찾아갔더니 멀쩡 | ★★★ **도구 없이 42 를 읽은 칸 16 / 28** — UB 의 한 결과 | (3) |
| 가건물 특례 | ★★★ **`const T& r = T{1};` — 블록 끝까지 산다** | (4) |
| 중개인을 거친 명함 | ★★★ **`const T& r = pass(T{2});` — 그 줄에서 죽는다** | (4) |
| 특례의 새 판 | ★★ **범위 `for` 의 임시 — C++23(P2718) · 이 두 판은 미구현** | (5) |

```text
   const T& r = T{1};          const T& r = pass(T{2});
        │                            │
        ▼                            ▼
   [ 임시 T(1) ] ◀── r          [ 임시 T(2) ] ◀── x (pass 의 매개변수) ── return x ──▶ r
   r 이 살아 있는 동안 산다       ;  에서 T(2) 파괴 ── r 은 철거된 집을 가리킨다
   ★ 연장된다                     ★ 연장되지 않는다 — 묶인 것은 x 이지 r 이 아니다
```

## 이 주제가 답하려는 질문

1. ★★★ **댕글링 일곱 모양을 도구가 잡나** — 경고 둘 · ASan 넷, **어느 칸이 비나**((1)(2)).
2. ★★★ **수명 연장은 어디까지인가** — 되는 모양과 안 되는 모양을 **소멸자 로그로**((4)).
3. ★★ **범위 `for` 의 임시는 C++23 에서 고쳐졌나 — 이 두 컴파일러에서는**((5)).
4. ★★ **Rust·Go 는 같은 코드를 어떻게 다루나**((6)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ③ ASan 과 ⑤ 경고를 합친 「댕글링 × 도구」 격자다

★★★ **이 주제의 본체는 격자다** — **탐침 일곱 × 도구 여섯 = 42칸**을 스크립트가 채우고 센다.\
★★ **짝이 소멸자 로그**다 — 수명 연장은 **UB 가 아니라 표준**이라 **로그 순서**가 그대로 근거가 된다((4)).

```text
① 다섯 층 표            수명 연장 규칙은 표준 · 댕글링 읽기는 UB · 범위 for 는 판에 달림     (구현 세부사항 절)
② 두 컴파일러 대조       경고 열이 서로 다른 탐침을 잡는다 · P2718 판별                      (1)(4)(5)
③ ★ ASan                -O0 · -O2 두 판 · detect_stack_use_after_return 켬/끔             (1)(2)
④ 어셈블리(-O0)          g++ 가 지역 참조 반환을 「0 반환」으로 바꾼 것                       (2)
⑤ ★ 경고 격자           -Wall -Wextra 두 컴파일러 — 격자의 두 열                            (1)(4)
⑥ <type_traits>          —                                                                  부적용
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★★ **수명 연장 규칙(표준)과 댕글링 읽기(UB)의 선**을 긋는다 | **쓴다** |
| ② 두 컴파일러 대조 | ★★★ **경고 열이 서로 다른 탐침**을 잡는다 — g++ 는 2·3·6, clang 은 4·5 | **쓴다** |
| ★★★ **③ ASan** | ★★★ **본체** — `-O0` 은 두 컴파일러 **7 / 7**, clang `-O2` 는 **2 / 7** | **쓴다** |
| ④ 어셈블리 | ★★ **탐침 1 의 g++ 판이 왜 SEGV 인가** — `movl $0, %eax` | **쓴다** |
| ★★★ **⑤ 경고 격자** | ★★★ **본체의 두 열** — 탐침 7 은 **두 컴파일러 다 0** | **쓴다** |
| ⑥ `<type_traits>` | ★ **부적용** — 수명은 **타입에 적히지 않는다.** 같은 `const T&` 가 늘어나기도 하고 안 늘어나기도 한다((4)). 물을 트레이트가 없다(18-B 「잴 것이 없다」) | **안 쓴다** |

### (1) ★★★ 댕글링 일곱 모양 × 도구 여섯 — 잡은 칸 N / 42

**언제 쓰나** — 「경고가 안 났다 / ASan 이 조용하다」가 **무엇을 증명하나**를 따질 때.

```cpp
/* dang01.cpp */
// 이미 죽은 것을 가리키는 일곱 모양 — -DPROBE=1..7 으로 하나만 켠다. 읽은 값이 42 인지만 찍는다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <algorithm>
#include <cstdio>
#include <string>
#include <string_view>
#include <vector>

struct S { int v; };

#if PROBE == 1
int& local_ref() { int x = 42; return x; }
#elif PROBE == 2
const S& pass(const S& s) { return s; }
#elif PROBE == 3
struct Box {
    std::vector<int> items_{42, 42, 42};
    const std::vector<int>& items() const { return items_; }
};
Box make_box() { return Box{}; }
#elif PROBE == 4
std::string make_text() { return std::string(40, '*') + "42"; }
#elif PROBE == 5
auto make_reader() {
    int x = 42;
    return [&] { return x; };
}
#elif PROBE == 7
struct View {
    const S& s;
    explicit View(const S& x) : s(x) {}
};
#endif

__attribute__((noinline)) int probe() {
#if PROBE == 1
    int& r = local_ref();
    return r;
#elif PROBE == 2
    const S& r = pass(S{42});
    return r.v;
#elif PROBE == 3
    int last = 0;
    for (int x : make_box().items()) last = x;
    return last;
#elif PROBE == 4
    std::string_view sv = make_text();
    return std::stoi(std::string(sv.substr(40)));
#elif PROBE == 5
    auto read = make_reader();
    return read();
#elif PROBE == 6
    int a = 41;
    const int& r = std::max(a + 1, a);
    return r;
#elif PROBE == 7
    View w(S{42});
    return w.s.v;
#endif
}

int main() {
    std::fprintf(stderr, "(%d) 읽은 값이 42 인가 %d\n", PROBE, (int)(probe() == 42));
}
```

```bash
# dang-grid.sh
# dang-grid.sh — 탐침 일곱 × 도구 여섯. 칸에는 도구가 댄 이름을, 침묵이면 - 를 찍는다
W='-std=c++20 -Wall -Wextra -pedantic'
A='-std=c++20 -fsanitize=address -g'
warn() { local w; w=$($1 $W -DPROBE=$2 -c dang01.cpp -o /dev/null 2>&1 | grep -oE 'warning: .*\[-W[a-z-]+\]' | grep -oE '\-W[a-z-]+' | sort -u | tr '\n' ' '); echo "${w:--}"; }
asan() { local r; $1 $A $3 -DPROBE=$2 dang01.cpp -o gx 2>/dev/null; r=$(./gx 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [A-Za-z-]+' | sed 's/SUMMARY: AddressSanitizer: //'); echo "${r:--}"; }
caught=0; cells=0; segv=0
printf '%-3s %-22s %-22s %-22s %-22s %-22s %-22s\n' '#' 'g++ -Wall' 'clang -Wall' 'g++ ASan -O0' 'clang ASan -O0' 'g++ ASan -O2' 'clang ASan -O2'
for n in 1 2 3 4 5 6 7; do
  row=("$(warn g++ $n)" "$(warn clang++ $n)" "$(asan g++ $n -O0)" "$(asan clang++ $n -O0)" "$(asan g++ $n -O2)" "$(asan clang++ $n -O2)")
  for c in "${row[@]}"; do cells=$((cells+1)); [ "$c" != "-" ] && caught=$((caught+1)); [ "$c" = "SEGV" ] && segv=$((segv+1)); done
  printf '%-3s %-22s %-22s %-22s %-22s %-22s %-22s\n' "$n" "${row[@]}"
done
rm -f gx
echo "잡은 칸 $caught / $cells (그중 SEGV 로 멈춘 칸 $segv)"
```

```text
===== bash dang-grid.sh (exit=0) =====
#   g++ -Wall              clang -Wall            g++ ASan -O0           clang ASan -O0         g++ ASan -O2           clang ASan -O2        
1   -Wreturn-local-addr    -Wreturn-stack-address  SEGV                   stack-use-after-return SEGV                   -                     
2   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
3   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  heap-use-after-free   
4   -                      -Wdangling-gsl         heap-use-after-free    heap-use-after-free    heap-use-after-free    heap-use-after-free   
5   -                      -Wreturn-stack-address  stack-use-after-return stack-use-after-return stack-use-after-scope  -                     
6   -Wdangling-reference   -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
7   -                      -                      stack-use-after-scope  stack-use-after-scope  stack-use-after-scope  -                     
잡은 칸 30 / 42 (그중 SEGV 로 멈춘 칸 2)
```

★ 격자를 손으로 한 장에 접으면(칸의 잡음 여부만 옮겼다 — **원본은 위 캡처**) —

```text
   탐침                                     g++    clang   g++ ASan  clang ASan  g++ ASan  clang ASan
                                            경고   경고    -O0       -O0         -O2       -O2
   1 지역 참조 반환                          O      O      SEGV      O           SEGV      .
   2 const T& 매개변수를 되돌림 + 임시        O      .      O         O           O         .
   3 범위 for — make_box().items()           O      .      O         O           O         O
   4 string_view = 임시 string               .      O      O         O           O         O
   5 람다가 지역을 [&] 로 잡아 반환            .      O      O         O           O         .
   6 std::max(임시, 임시) 를 const int& 로    O      .      O         O           O         .
   7 참조 멤버 — 생성자로 임시를 받음          .      .      O         O           O         .
   ★ 잡은 칸 30 / 42 (그중 SEGV 로 멈춘 칸 2)
```

- ★★★ **두 컴파일러의 경고가 서로 다른 탐침을 잡는다** — g++ 는 **1 · 2 · 3 · 6**(`-Wreturn-local-addr` · `-Wdangling-reference`), clang 은 **1 · 4 · 5**(`-Wreturn-stack-address` · `-Wdangling-gsl`).\
  ★★ **두 경고를 합쳐야 여섯 탐침**이 덮이고, **탐침 7(참조 멤버를 생성자로 받음)은 두 컴파일러 다 0** 이다.
- ★★★ **`-O0` ASan 은 두 컴파일러 다 일곱 탐침을 전부 멈춘다** — 단 **g++ 의 탐침 1 은 댕글링이 아니라 `SEGV`**((2)에 이유).
- ★★★ **clang `-O2` + ASan 은 일곱 중 둘(3 · 4)만** 잡는다 — 힙 메모리를 읽는 두 탐침이다. **스택을 읽는 다섯은 최적화 뒤 ASan 이 볼 접근이 사라졌다**(무엇이 사라졌는지는 **재지 않았다** — 칸만 셌다).\
  ★★ **g++ `-O2` 는 오히려 탐침 5 를 `stack-use-after-scope` 로 이름만 바꿔 잡았다**(인라인되어 「돌아간 프레임」이 「끝난 블록」이 됐다고 읽힌다 — 내 읽기).
- ★★★ **결론 — 「경고 0 · ASan 침묵」은 탐침 7 을 clang `-O2` 로 빌드한 판에서 동시에 성립한다.** 그 판의 댕글링은 **어떤 도구에도 안 보인다.**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DPROBE=7 dang01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
=================================================================
==3378889==ERROR: AddressSanitizer: stack-use-after-scope on address 0x750995200030 at pc 0x57f0af8223d9 bp 0x7ffd3c8eadf0 sp 0x7ffd3c8eade0
READ of size 4 at 0x750995200030 thread T0
    #0 0x57f0af8223d8 in probe() dang01.cpp:58
    #1 0x57f0af822457 in main dang01.cpp:63

Address 0x750995200030 is located in stack of thread T0 at offset 48 in frame
    #0 0x57f0af822298 in probe() dang01.cpp:35

    [48, 52) '<unknown>' <== Memory access at offset 48 is inside this variable
    [64, 72) 'w' (line 57)
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-scope dang01.cpp:58 in probe()
```

- ★★ **탐침 7 을 g++ `-O0` ASan 에게 물으면 `stack-use-after-scope`** — `'<unknown>'` 변수(임시 `S{42}`)의 자리를 읽었다. **경고 두 열이 비어 있는 탐침을 실행이 잡았다.**

### (2) ★★ ASan 이 「돌아간 함수의 스택」을 보는 조건 — 그리고 탐침 1 의 SEGV

**언제 쓰나** — `ASAN_OPTIONS` 를 만질 때 · g++ 판의 탐침 1 이 왜 이름이 다른지 궁금할 때.

```bash
# dang-uar.sh
# dang-uar.sh — 함수가 돌아간 뒤의 스택을 읽는 두 탐침(1 · 5)을 ASan 옵션 하나만 바꿔 다시 돌린다
echo "ASAN_OPTIONS 환경 변수 = ${ASAN_OPTIONS-(설정 안 됨)}"
for n in 1 5; do
  for c in g++ clang++; do
    $c -std=c++20 -fsanitize=address -g -DPROBE=$n dang01.cpp -o gx 2>/dev/null
    for v in 1 0; do
      r=$(ASAN_OPTIONS=detect_stack_use_after_return=$v ./gx 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [A-Za-z-]+|^\([0-9]\) .*' | head -1)
      printf '탐침 %d  %-8s detect_stack_use_after_return=%d  ->  %s\n' "$n" "$c" "$v" "$r"
    done
  done
done
rm -f gx
```

```text
===== bash dang-uar.sh (exit=0) =====
ASAN_OPTIONS 환경 변수 = (설정 안 됨)
탐침 1  g++      detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: SEGV
탐침 1  g++      detect_stack_use_after_return=0  ->  SUMMARY: AddressSanitizer: SEGV
탐침 1  clang++  detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 1  clang++  detect_stack_use_after_return=0  ->  (1) 읽은 값이 42 인가 1
탐침 5  g++      detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 5  g++      detect_stack_use_after_return=0  ->  (5) 읽은 값이 42 인가 1
탐침 5  clang++  detect_stack_use_after_return=1  ->  SUMMARY: AddressSanitizer: stack-use-after-return
탐침 5  clang++  detect_stack_use_after_return=0  ->  (5) 읽은 값이 42 인가 1
```

- ★★★ **이 판에서는 환경 변수 없이(`설정 안 됨`) 이미 켜져 있었다** — 격자 (1)의 `stack-use-after-return` 이 그 증거다. **옵션이 「필요할 수 있다」가 아니라 「끄면 놓친다」였다**.
- ★★★ **`detect_stack_use_after_return=0` 이면 탐침 5 는 두 컴파일러 다, 탐침 1 은 clang 이 — 리포트 없이 `42 인가 1`** 을 찍는다. 돌아간 함수의 스택 칸이 **아직 덮이지 않아 옛 값이 읽혔다.**
- ★★ **g++ 의 탐침 1 은 옵션과 무관하게 `SEGV`** — 이유는 기계어에 있다.

```text
===== g++ -std=c++20 -O0 -S -o - -DPROBE=1 dang01.cpp 2>/dev/null | sed -n '/^_Z9local_refv:/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.cfi' (exit=0) =====
_Z9local_refv:
.LFB2539:
	endbr64
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%fs:40, %rax
	movq	%rax, -8(%rbp)
	xorl	%eax, %eax
	movl	$42, -12(%rbp)
	movl	$0, %eax
	movq	-8(%rbp), %rdx
	subq	%fs:40, %rdx
	je	.L3
	call	__stack_chk_fail@PLT
.L3:
	leave
	ret
```

- ★★★ **`movl $42, -12(%rbp)` 로 지역을 쓰고, 돌려주는 값은 `movl $0, %eax` — 널이다.** g++ 는 **지역의 주소를 돌려주는 대신 0 을 돌려주게** 코드를 만들었다(`-O0` 에서도).\
  ★★ 그래서 g++ 판은 「**돌아간 스택을 읽는다**」가 아니라 「**0 번지를 읽는다**」가 되어 ASan 이 `SEGV` 로 멈춘다. **UB 를 한 구현이 이렇게 처리한 것**이다 — clang 판은 주소를 그대로 돌려줘 `stack-use-after-return` 이 됐다.

### (3) ★★ 도구 없이 돌리면 — 무엇을 읽나 (UB 의 이 판 한 결과)

**언제 쓰나** — 「돌려 봤더니 멀쩡하던데」라는 말을 들었을 때.

```bash
# dang-values.sh
# dang-values.sh — 도구 없이 돌리면 무엇을 읽나. 탐침 일곱 × (두 컴파일러 × -O0 · -O2). 값 대신 「42 였나」와 종료 코드만
same=0; cells=0
printf '%-3s %-16s %-16s %-16s %-16s\n' '#' 'g++ -O0' 'g++ -O2' 'clang++ -O0' 'clang++ -O2'
for n in 1 2 3 4 5 6 7; do
  line=$(printf '%-3s' "$n")
  for c in g++ clang++; do
    for o in -O0 -O2; do
      $c -std=c++20 $o -DPROBE=$n dang01.cpp -o gx 2>/dev/null
      out=$(./gx 2>&1); rc=$?
      case $out in *'42 인가 1'*) v='is42 rc='$rc; same=$((same+1));; *'42 인가 0'*) v='not42 rc='$rc;; *) v='none rc='$rc;; esac
      cells=$((cells+1)); line="$line $(printf '%-16s' "$v")"
    done
  done
  echo "$line"
done
rm -f gx
echo "42 를 읽은 칸 $same / $cells"
```

```text
===== bash dang-values.sh (exit=0) =====
#   g++ -O0          g++ -O2          clang++ -O0      clang++ -O2     
1   none rc=139      none rc=139      is42 rc=0        not42 rc=0      
2   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
3   not42 rc=0       not42 rc=0       not42 rc=0       not42 rc=0      
4   is42 rc=0        is42 rc=0        is42 rc=0        is42 rc=0       
5   is42 rc=0        not42 rc=0       is42 rc=0        not42 rc=0      
6   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
7   is42 rc=0        not42 rc=0       is42 rc=0        is42 rc=0       
42 를 읽은 칸 16 / 28
```

- ★★★ **28칸 중 16칸이 42 를 읽었다** — 이미 죽은 객체를 읽었는데 **기대값**이 나왔다. **이것이 댕글링의 가장 나쁜 얼굴**이다.
- ★★ **같은 탐침이 컴파일러·최적화 수준에 따라 갈린다**(탐침 2·5·6·7 의 g++ `-O0` 대 `-O2`) — 그러나 **어디서 갈릴지는 이 문서가 말하지 않는다**(규칙 14 — UB 가 갈리는 자리에 처방은 없다).
- ★ **이 블록은 흔들리는 칸으로 선언했다** — 세 번 돌려 같았지만(예행), **값이 「그 판의 메모리 상태」라서** 성질로 적지 않는다. 근거로 쓰는 것은 **「42 를 읽은 칸이 있다」** 하나다.

### (4) ★★★ 수명 연장 — 되는 모양과 안 되는 모양을 소멸자 로그로

**언제 쓰나** — 임시를 참조로 받아 두는 코드를 읽을 때마다.\
★ 07편 (5)가 **기본형 한 줄**을, 08편 (7)이 **`T&&` 와 xvalue** 를 쟀다. 여기서는 **일곱 모양을 한 로그에** 세운다. **참조는 한 번도 읽지 않는다** — 소멸자가 「다음 문장」 **앞이냐 뒤냐**만 본다.

```cpp
/* dang02.cpp */
// 임시를 참조에 묶는 일곱 모양 — 임시의 소멸자가 「다음 문장」 표시보다 먼저 찍히나 뒤에 찍히나
// 참조는 한 번도 읽지 않는다 — 소멸자가 찍히는 자리만 본다
#include <cstdio>
#include <utility>

struct T {
    int id;
    int m = 0;
    explicit T(int i) : id(i) {}
    ~T() { std::printf("      ~T(%d)\n", id); }
};

const T& pass(const T& x) { return x; }

struct H { const T& ref; };              // 참조 멤버를 가진 집합체

int main(int argc, char**) {
    bool flag = argc > 0;
    std::printf("(a) const T& r = T{1};\n");
    { const T& r = T{1};                       std::printf("    다음 문장\n"); (void)r; }
    std::printf("(b) const T& r = pass(T{2});\n");
    { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
    std::printf("(c) const int& r = T{3}.m;\n");
    { const int& r = T{3}.m;                   std::printf("    다음 문장\n"); (void)r; }
    std::printf("(d) T&& r = std::move(T{4});\n");
    { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
    std::printf("(e) const T& r = flag ? T{5} : T{6};\n");
    { const T& r = flag ? T{5} : T{6};         std::printf("    다음 문장\n"); (void)r; }
    std::printf("(f) H h{T{7}};\n");
    { H h{T{7}};                               std::printf("    다음 문장\n"); (void)h; }
    std::printf("(g) H h(T{8});\n");
    { H h(T{8});                               std::printf("    다음 문장\n"); (void)h; }
    std::printf("(끝)\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic dang02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang02.cpp: In function ‘int main(int, char**)’:
dang02.cpp:22:16: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   22 |     { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
      |                ^
dang02.cpp:22:24: note: the temporary was destroyed at the end of the full expression ‘pass(T(2))’
   22 |     { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
      |                    ~~~~^~~~~~
dang02.cpp:26:11: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |           ^
dang02.cpp:26:24: note: the temporary was destroyed at the end of the full expression ‘std::move<T>(T(4))’
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ~~~~~~~~~^~~~~~
(a) const T& r = T{1};
    다음 문장
      ~T(1)
(b) const T& r = pass(T{2});
      ~T(2)
    다음 문장
(c) const int& r = T{3}.m;
    다음 문장
      ~T(3)
(d) T&& r = std::move(T{4});
      ~T(4)
    다음 문장
(e) const T& r = flag ? T{5} : T{6};
    다음 문장
      ~T(5)
(f) H h{T{7}};
    다음 문장
      ~T(7)
(g) H h(T{8});
      ~T(8)
    다음 문장
(끝)
```

```text
   모양                                   ~T 가 「다음 문장」보다   연장?   g++ 경고   clang 경고
   (a) const T& r = T{1};                 뒤                        ★ 된다   —          —
   (b) const T& r = pass(T{2});           앞                        ★ 안 됨  O          —
   (c) const int& r = T{3}.m;             뒤                        된다     —          —
   (d) T&& r = std::move(T{4});           앞                        ★ 안 됨  O          O
   (e) const T& r = flag ? T{5} : T{6};   뒤                        된다     —          —
   (f) H h{T{7}};           (중괄호)      뒤                        된다     —          —
   (g) H h(T{8});           (괄호)        앞                        ★ 안 됨  —          —
```

- ★★★ **연장되는 것은 「임시(또는 그 멤버)가 참조에 직접 묶일 때」** — (a) 기본형 · (c) **임시의 멤버**에 묶어도 **임시 전체**가 산다 · (e) 조건 연산자의 결과 · (f) **중괄호 집합체 초기화**의 참조 멤버.
- ★★★ **연장되지 않는 것은 「중간에 무엇이 끼는 것」** — (b) **함수가 참조를 돌려줌**(묶인 것은 `pass` 의 매개변수다) · (d) **`std::move` 가 끼면 xvalue** 가 되어 늘 것이 없다(08편과 같은 이유) · (g) **C++20 괄호 집합체 초기화**.
- ★★★ **(g) 는 두 컴파일러 다 경고 0** — `H h{…}` 와 `H h(…)` 는 **괄호 모양 하나 차이**인데, 한쪽은 블록 끝까지, 한쪽은 그 줄에서 죽는다. cppreference 의 「예외」 목록에 **(since C++20)** 으로 올라 있는 바로 그 항목이다.\
  ★ 같은 목록의 나머지 셋 — **`return` 문에서 묶인 임시**(항상 댕글링) · **함수 매개변수에 묶인 임시**(=(b)) · **`new` 식 초기화자 안의 임시** — 중 이 문서는 **(b)만** 던졌다.
- ★★ **경고** — g++ 는 **(b)·(d)** 를 `-Wdangling-reference`, clang 은 **(d)만** `-Wdangling`(+ `-Wpessimizing-move`) — **(g)는 아무도.** 연장이 안 되는 셋 중 **g++ 2 · clang 1 · 합쳐 2**.
- ★ **clang 로그도 한 글자도 같다**(경고 줄만 다르다) —

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic dang02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang02.cpp:26:25: warning: temporary bound to local reference 'r' will be destroyed at the end of the full-expression [-Wdangling]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |                         ^~~~
dang02.cpp:26:15: warning: moving a temporary object prevents copy elision [-Wpessimizing-move]
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ^
dang02.cpp:26:15: note: remove std::move call here
   26 |     { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
      |               ^~~~~~~~~~    ~
2 warnings generated.
(a) const T& r = T{1};
    다음 문장
      ~T(1)
(b) const T& r = pass(T{2});
      ~T(2)
    다음 문장
(c) const int& r = T{3}.m;
    다음 문장
      ~T(3)
(d) T&& r = std::move(T{4});
      ~T(4)
    다음 문장
(e) const T& r = flag ? T{5} : T{6};
    다음 문장
      ~T(5)
(f) H h{T{7}};
    다음 문장
      ~T(7)
(g) H h(T{8});
      ~T(8)
    다음 문장
(끝)
```

### (5) ★★ 범위 `for` 의 임시 — C++23 에서 고쳐졌나, 이 두 컴파일러에서는

**언제 쓰나** — `for (auto& x : make().items())` 꼴을 볼 때.

```cpp
/* dang03.cpp */
// 범위 for 의 범위 식 안에서 만든 임시는 언제 죽나 — -std=c++20 과 -std=c++23 에 같은 파일을 던진다
// 본문은 x 를 읽지 않고 한 번 들어오면 나간다 — ~Holder 가 찍히는 자리만 본다
#include <cstdio>
#include <vector>

struct Holder {
    std::vector<int> items_{1, 2};
    const std::vector<int>& items() const { return items_; }
    ~Holder() { std::printf("    ~Holder\n"); }
};
Holder make() { return Holder{}; }

int main() {
    std::printf("__cplusplus = %ld · __cpp_range_based_for = %ld\n", __cplusplus, (long)__cpp_range_based_for);
    std::printf("(1) for (int x : make().items())\n");
    for (int x : make().items()) {
        (void)x;
        std::printf("    본문에 들어왔다\n");
        break;
    }
    std::printf("(2) 루프를 나왔다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang03.cpp: In function ‘int main()’:
dang03.cpp:16:31: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   16 |     for (int x : make().items()) {
      |                               ^
dang03.cpp:16:30: note: the temporary was destroyed at the end of the full expression ‘make()().Holder::items()’
   16 |     for (int x : make().items()) {
      |                  ~~~~~~~~~~~~^~
__cplusplus = 202002 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
===== g++ -std=c++23 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dang03.cpp: In function ‘int main()’:
dang03.cpp:16:31: warning: possibly dangling reference to a temporary [-Wdangling-reference]
   16 |     for (int x : make().items()) {
      |                               ^
dang03.cpp:16:30: note: the temporary was destroyed at the end of the full expression ‘make()().Holder::items()’
   16 |     for (int x : make().items()) {
      |                  ~~~~~~~~~~~~^~
__cplusplus = 202100 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
__cplusplus = 202002 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
===== clang++ -std=c++23 -Wall -Wextra -pedantic dang03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
__cplusplus = 202302 · __cpp_range_based_for = 201603
(1) for (int x : make().items())
    ~Holder
    본문에 들어왔다
(2) 루프를 나왔다
```

- ★★★ **네 판 모두 `~Holder` 가 「본문에 들어왔다」보다 먼저** — `-std=c++23` 을 줘도 **임시는 루프 전에 죽었다.** 두 컴파일러 다.
- ★★★ **판별은 매크로가 한다** — 네 판 모두 **`__cpp_range_based_for = 201603`**. cppreference 는 P2718(범위 초기화식 안의 임시 전부 연장)의 값을 **`202211L`** 로 적고, 구현한 판을 **GCC 15 · Clang 19** 로 적는다 — **이 머신의 g++ 13 · clang 18 은 그 전이다.**\
  ★★ **「`-std=c++23` 으로 돌렸다」는 「C++23 의 규칙으로 돌았다」가 아니다** — 규칙 12 의 「`-std=` 는 기본값 선택」과 같은 집안의 새 사례다.
- ★★ **g++ 의 `-std=c++23` 은 `__cplusplus = 202100`** 이다(clang 은 `202302`) — g++ 13 은 C++23 판의 값을 **아직 확정 값으로 내지 않는다.**
- ★★ **경고는 g++ 만**(`-Wdangling-reference` — 두 판 다) · clang 은 0. 격자 (1)의 탐침 3 과 같은 칸이다.
- ★ **본문이 한 번 돈 것은 UB 의 결과**다 — 죽은 `vector` 의 `begin`/`end` 를 읽었다. 이 문서는 **`x` 를 읽지 않았고**, 근거는 **`~Holder` 의 자리**뿐이다.

```text
   for (int x : make().items())             C++20 (그리고 P2718 이전 판의 -std=c++23)
        ├ auto&& __range = make().items();   make() 의 임시 Holder 는 이 문장 끝에서 ~Holder
        └ for (… __range …)                  __range 는 죽은 Holder 의 items_ 를 가리킨다
                                            C++23 + P2718 구현 판 — make() 의 임시도 루프 끝까지
```

### (6) ★★★ Rust — 같은 세 모양이 전부 컴파일 에러

**언제 쓰나** — 「C++ 이 못 막는 것을 다른 언어는 어디서 막나」를 말할 때.

```rust
// dangle.rs
// C++ 의 댕글링 세 모양을 Rust 로 — --cfg 로 하나씩 켠다(local_ref · closure · view)
#[cfg(local_ref)]
fn local_ref<'a>() -> &'a i32 {
    let x = 42;
    &x
}

#[cfg(closure)]
fn make_reader() -> impl Fn() -> i32 {
    let x = 42;
    || x
}

fn main() {
    #[cfg(local_ref)]
    println!("{}", local_ref());
    #[cfg(closure)]
    println!("{}", make_reader()());
    #[cfg(view)]
    {
        let sv: &str = String::from("*42").as_str();
        println!("{}", sv);
    }
}
```

```text
===== rustc --edition 2021 --cfg local_ref dangle.rs -o drx (cc exit=1) =====
error[E0515]: cannot return reference to local variable `x`
 --> dangle.rs:5:5
  |
5 |     &x
  |     ^^ returns a reference to data owned by the current function

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0515`.
```

```text
===== rustc --edition 2021 --cfg closure dangle.rs -o drx (cc exit=1) =====
error[E0373]: closure may outlive the current function, but it borrows `x`, which is owned by the current function
  --> dangle.rs:11:5
   |
11 |     || x
   |     ^^ - `x` is borrowed here
   |     |
   |     may outlive borrowed value `x`
   |
note: closure is returned here
  --> dangle.rs:11:5
   |
11 |     || x
   |     ^^^^
help: to force the closure to take ownership of `x` (and any other referenced variables), use the `move` keyword
   |
11 |     move || x
   |     ++++

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0373`.
```

```text
===== rustc --edition 2021 --cfg view dangle.rs -o drx (cc exit=1) =====
error[E0716]: temporary value dropped while borrowed
  --> dangle.rs:21:24
   |
21 |         let sv: &str = String::from("*42").as_str();
   |                        ^^^^^^^^^^^^^^^^^^^         - temporary value is freed at the end of this statement
   |                        |
   |                        creates a temporary value which is freed while still in use
22 |         println!("{}", sv);
   |                        -- borrow later used here
   |
   = note: consider using a `let` binding to create a longer lived value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0716`.
```

- ★★★ **탐침 1(지역 참조 반환) → `E0515` · 탐침 5(지역을 빌린 클로저 반환) → `E0373` · 탐침 4(임시 `String` 의 뷰) → `E0716`** — 셋 다 **`cc exit=1`**.
- ★★★ **C++ 에서 격자의 칸이 비던 자리가 Rust 에서는 빌드 실패**다 — 빌림 검사기는 **「참조가 가리키는 것보다 오래 살 수 있나」를 타입(수명)으로** 묻는다.
- ★★ **`E0373` 의 `help:` 가 처방까지 말한다**(`move || x`) — C++ 에서는 `[=]` 가 그 자리다([목록의 **39번 주제**](../39-lambdas-and-captures/)).
- ★ `E0106`(수명 표기 누락)·`E0597`(`does not live long enough`)은 Rust 갈래 [11번](../../../rust/syntax/11-borrow-checker-rejections/)·[12번](../../../rust/syntax/12-lifetime-annotations-and-elision/)이 정본이다. `E0515` 는 [13번](../../../rust/syntax/13-struct-references-and-static/)·[14번](../../../rust/syntax/14-string-vs-str/)에도 나온다.

### (7) ★★ Go — 지역의 주소를 돌려줘도 된다

**언제 쓰나** — 「스택 변수의 주소를 돌려주면 안 된다」가 **언어의 성질인지 C++ 의 성질인지** 가를 때.

```go
// esc.go
// C++ 에서 댕글링이 되는 두 모양을 Go 로 — 지역 변수의 주소와 그것을 잡은 클로저를 돌려준다
package main

import "fmt"

func localPtr() *int {
	x := 42
	return &x
}

func makeReader() func() int {
	y := 42
	return func() int { return y }
}

func main() {
	p := localPtr()
	r := makeReader()
	fmt.Println(*p == 42, r() == 42)
}
```

```text
===== go version (exit=0) =====
go version go1.27.1 linux/amd64
===== go build -gcflags='-m -l' -o escx esc.go && ./escx (cc exit=0 · run exit=0) =====
# command-line-arguments
./esc.go:7:2: moved to heap: x
./esc.go:13:9: func literal escapes to heap
./esc.go:19:13: ... argument does not escape
./esc.go:19:17: *p == 42 escapes to heap
./esc.go:19:28: r() == 42 escapes to heap
true true
```

- ★★★ **`moved to heap: x`** — Go 컴파일러가 **탈출 분석**으로 `x` 를 **힙에 놓았다.** 그래서 `*p == 42` 가 **`true`** 이고, 이것은 **UB 가 아니라 언어가 보장하는 동작**이다.
- ★★ **클로저 쪽 `y` 에는 `moved to heap` 이 없다** — 이 클로저는 `y` 를 **바꾸지 않아 값으로** 잡혔다(`func literal escapes to heap` 만). 클로저와 탈출의 정본은 Go 갈래 [13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/)이다.
- ★★★ **세 언어의 선** — **C++ 은 허락하고 도구가 일부를 잡는다 · Rust 는 거부한다 · Go 는 객체를 옮겨서 성립시킨다(GC 가 치운다).**

## 문법 — 형태와 규칙

### 형태

```text
   const T& r = T{};                 연장 — 블록 끝까지
   T&& r = T{};                      연장 (08편)
   const int& m = T{}.member;        연장 — 임시 전체가
   const T& r = f(T{});              ★ 연장 아님 — f 가 참조를 돌려주면 댕글링
   T&& r = std::move(T{});           ★ 연장 아님 — xvalue
   Agg a{T{}};   Agg a(T{});         중괄호는 연장 · ★ 괄호(C++20)는 연장 아님
   for (auto& x : make().items())    ★ C++20 은 make() 가 루프 전에 죽는다 (P2718 이 C++23 에서 바꿈)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (4)(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **연장은 「임시가 참조에 직접 묶일 때」만** — 함수·`std::move`·괄호 집합체가 끼면 안 된다((4)).
- ★★★ **참조·포인터·뷰·`[&]` 람다를 돌려주는 함수는 「가리키는 것이 호출자보다 오래 사나」를 한 문장으로 말할 수 있어야 한다**((1)).
- ★★ **경고는 두 컴파일러를 다 켜야 덮는 칸이 넓어진다** — 그래도 탐침 7 · (g) 는 둘 다 비었다((1)(4)).
- ★★ **ASan 은 `-O0` 으로** — clang `-O2` 판은 스택 탐침 다섯을 놓쳤다((1)). **`detect_stack_use_after_return` 을 끄지 않는다**((2)).
- ★★ **`-std=c++23` 은 P2718 을 뜻하지 않는다** — `__cpp_range_based_for` 로 판별한다((5)).

## 어디서 틀리나

### 1. ★★★ 「경고가 없으면 댕글링이 없다」

(1)이 반증이다 — **탐침 7 은 두 컴파일러 다 경고 0**, (4)의 **(g) 도 0**. 경고 두 열을 합쳐도 **여섯 / 일곱**이다.

### 2. ★★★ 「ASan 을 붙였으니 잡힌다」

(1)(2)가 반증이다 — **clang `-O2` 는 2 / 7**, **`detect_stack_use_after_return=0` 이면 탐침 1(clang)·5(둘 다)를 놓친다.**

### 3. ★★★ 「돌려 봤더니 42 가 나왔으니 괜찮다」

(3)이 반증이다 — **죽은 객체를 읽고도 16 / 28 칸이 42** 였다. 기대값은 **UB 의 한 결과**일 뿐이다.

### 4. ★★★ 「`const T&` 에 묶으면 임시는 늘어난다」

(4)가 반증이다 — **(b) 함수를 거치면 · (d) `std::move` 가 끼면 · (g) 괄호로 집합체를 만들면** 그 줄에서 죽는다. 늘어나는 것은 **직접 묶였을 때**뿐이다.

### 5. ★★ 「`-std=c++23` 이면 범위 `for` 의 임시 문제가 없다」

(5)가 반증이다 — **두 컴파일러 다 `~Holder` 가 먼저**, 매크로 **201603**. P2718 은 **GCC 15 · Clang 19** 부터다(cppreference).

### 6. ★★ 「지역의 주소를 돌려주면 어느 언어든 안 된다」

(7)이 반증이다 — **Go 는 `moved to heap` 으로 성립시킨다.** 안 되는 것은 **C++ 의 자동 저장 기간** 때문이다.

### 7. ★ 「g++ 도 탐침 1 을 `stack-use-after-return` 으로 잡는다」

(2)가 반증이다 — g++ 는 **널을 돌려주게** 만들어 **`SEGV`** 가 됐다. 같은 UB 에 **구현이 서로 다른 코드**를 냈다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 선은 정확히 둘 사이에 있다** — **수명 연장 규칙 자체는 「표준」** 이고(그래서 (4)의 로그 순서는 근거다), **죽은 것을 읽는 것은 「UB」** 다(그래서 (3)의 값은 근거가 아니다).

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **임시는 전체 식 끝에서 죽는다 · 직접 묶이면 참조만큼 산다((a)(c)(e)(f)) · 함수 매개변수·xvalue·괄호 집합체는 안 된다((b)(d)(g))**((4)) | 소멸자 로그 순서 | ★★★ **(g) — 두 컴파일러 경고 0** |
| **조건부 표준** | 특정 판에서만 | ★★★ **괄호 집합체 초기화는 C++20** · ★★★ **범위 `for` 의 임시 연장은 C++23(P2718)** — **이 두 판은 미구현**((5)) | `-std=c++20`/`c++23` · 매크로 | ★★ **`-std=c++23` 이 그 규칙을 켠다고 믿게 한다** |
| **구현 정의** | 문서화 의무 | ★★ **`__cplusplus` 값**(g++ `-std=c++23` 은 `202100`)((5)) · **ASan 옵션의 기본값**((2)) | 출력 · 옵션 격자 | — |
| **미명시** | 몇 가지 중 하나 | ★ 이 주제에는 **결론을 세운 칸이 없다** | — | — |
| **UB** | 아무 일이나 | ★★★ **탐침 일곱 전부 — 죽은 객체를 읽기**((1)) · **g++ 가 지역 참조 반환을 널로 바꾼 것**((2)) · **도구 없이 16 / 28 이 42**((3)) · **범위 `for` 본문이 돈 것**((5)) | ASan 이름 · 어셈블리 | ★★★ **clang `-O2` ASan 이 다섯 탐침에 침묵 · 탐침 7 은 경고 0** |

### 「도구가 못 보는 것」을 층마다

★★★ **이 주제의 결론이 이 표다** — **42칸 중 12칸이 비었고, 모든 도구가 동시에 비는 판이 있다.**

| 사실 | 층 | g++ 경고 | clang 경고 | ASan -O0 (g++ · clang) | ASan -O2 (g++ · clang) |
|---|---|---|---|---|---|
| ★★★ **탐침 7 — 참조 멤버를 생성자로** | UB | ★★★ **0** | ★★★ **0** | 잡음 · 잡음 | 잡음 · ★★★ **침묵** |
| ★★ 탐침 2 · 6 — 참조를 되돌리는 함수 | UB | 잡음 | ★★ **0** | 잡음 · 잡음 | 잡음 · ★★ **침묵** |
| ★★ 탐침 4 · 5 — 뷰 · `[&]` 람다 | UB | ★★ **0** | 잡음 | 잡음 · 잡음 | 잡음 · 4 만 잡음 |
| ★★★ **(g) 괄호 집합체의 참조 멤버** | 표준(연장 안 됨) | ★★★ **0** | ★★★ **0** | (읽지 않았다) | — |
| ★★ **`-std=c++23` 인데 P2718 미구현** | 조건부 표준 | **경고는 댕글링만** | **0** | — | — |
| ★★ **`detect_stack_use_after_return=0`** | 도구 설정 | — | — | 탐침 5 **둘 다 침묵** · 탐침 1 **clang 침묵** | — |

- ★★★ **이 표의 결론** — **어떤 도구도 댕글링의 전부를 보지 않는다.** 경고는 **모양이 뻔한 것**을, ASan 은 **최적화 전 실행이 지나간 것**을 본다. **탐침 7 을 clang `-O2` 로 빌드하면 네 창이 전부 빈다** — 이 주제가 끝내 남기는 것은 **「누가 아직 보고 있는가」는 도구가 아니라 설계가 답해야 한다**는 것이다(`c-cpp-csharp.md` 의 논증).
- ★ 탐침 수 — **탐침 일곱 × 도구 여섯 = 42** · 수명 연장 **일곱 모양** · 범위 `for` **판 넷** · ASan 옵션 **넷 × 2**.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 이 편의 일곱 탐침과 일곱 모양은 **전부 컴파일되는 올바른 문법**이다 — 틀린 것은 **실행 중의 수명**이지 문법이 아니다. `cc exit=0` 으로 조용히 통과한 **ill-formed** 는 없었다.
- ★★ **가장 가까운 자리는 (5)** — `-std=c++23` 으로 빌드한 **`cc exit=0`** 판이 **C++23 의 의미로 돌지 않았다.** ill-formed 가 아니라 **「그 판의 규칙이 아직 없는」** 것이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 함수가 만든 것을 돌려준다 | ★★★ **값으로** 돌려준다 | 탐침 1 · (b) |
| 함수가 인자의 일부를 참조로 돌려준다 | ★★ 호출자에게 **임시를 넘기지 말라**고 적는다 — 또는 값으로 | 탐침 2 · 6 · (b) |
| 임시를 오래 들고 싶다 | ★★ **값으로 받는다** · 참조면 **직접 묶는 모양만** | (4) |
| 참조 멤버를 가진 타입 | ★★ **생성자로 임시를 받지 않게** 설계 · 집합체면 **중괄호** | 탐침 7 · (f)(g) |
| `for (x : make().items())` | ★★ **임시에 이름을 붙여 루프보다 오래 살린다** — cppreference 가 C++20 init-statement 판을 싣는다(**이 문서는 던지지 않았다**) | (5) — P2718 판별 전까지 |
| 람다를 밖으로 돌려준다 | ★★ **`[=]`·초기화 캡처**(이 문서는 던지지 않았다) | 탐침 5 — [목록의 **39번 주제**](../39-lambdas-and-captures/) |
| `string_view` | ★★ **가리키는 `string` 이 더 오래 사는지** 확인 | 탐침 4 — 목록의 **46번 주제** |

## 핵심 문장

- ★★★ **댕글링 일곱 모양 × 도구 여섯에서 잡은 칸은 30 / 42** — 경고 두 열은 **서로 다른 탐침**을 잡고, **탐침 7 은 두 경고 다 0**, **clang `-O2` ASan 은 2 / 7**.
- ★★★ **ASan 의 `detect_stack_use_after_return` 은 이 판에서 기본으로 켜져 있었고, 끄면 탐침 1(clang)·5(둘 다)를 놓친다** · g++ 는 지역 참조 반환을 **널 반환**으로 바꿨다.
- ★★★ **도구 없이 돌리면 28칸 중 16칸이 42 를 읽었다** — 기대값은 **UB 의 한 결과**다.
- ★★★ **수명 연장은 「임시가 참조에 직접 묶일 때」만** — `pass(T{})` · `std::move(T{})` · **괄호 집합체 `H h(T{})`** 는 그 줄에서 죽고, 마지막은 **두 컴파일러 다 경고 0**.
- ★★ **범위 `for` 의 임시 수명(P2718)은 g++ 13 · clang 18 의 `-std=c++23` 에서도 안 고쳐졌다** — `__cpp_range_based_for` 가 **201603**.
- ★★ **Rust 는 같은 세 모양을 `E0515` · `E0373` · `E0716` 으로 거부하고, Go 는 `moved to heap` 으로 성립시킨다.**

## 관련 자료

- [07번](../07-references-vs-pointers/) — (5) 수명 연장 기본형 · (7) 지역 반환의 `-Wreturn-local-addr`. **「참조가 막는 것은 널과 재결합뿐」** 의 정본.
- [14번](../14-destructors-and-deterministic-destruction/) (4) — 임시는 전체 식 끝에서 죽는다 · `c_str()` 댕글링은 **clang 만 경고**.
- [08번](../08-value-categories-lvalue-prvalue-xvalue/) (7) — `T&&` 도 늘린다 · xvalue 는 늘 것이 없다.
- [05번](../05-auto-and-decltype-type-deduction/) (6) — `decltype(auto)` 의 괄호 하나가 만드는 댕글링.
- [목록의 **29번 주제**](../29-new-delete-and-where-raw-pointers-remain/) — `vector` 원소 포인터의 `heap-use-after-free`(재할당이 만든 댕글링).
- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절 — **「RAII는 누가 해제하는가에 답하지만 누가 아직 보고 있는가에는 답하지 않는다」** 의 논증 정본. 이 편 (1)의 빈 칸 12개가 그 문장의 실측이다.
- Rust 갈래 [11번](../../../rust/syntax/11-borrow-checker-rejections/)(E0106 · E0597) · [12번](../../../rust/syntax/12-lifetime-annotations-and-elision/)(수명 표기) — (6)의 정본.
- Go 갈래 [13번](../../../go/syntax/13-closures-variable-capture-and-loop-variable-change/) — 클로저 캡처와 `moved to heap`.
- [목록의 **39번 주제**](../39-lambdas-and-captures/)(람다와 캡처) · **43번 주제**(이터레이터 무효화) · **46번 주제**(`string`·`string_view`).

## 용어 풀이

> **댕글링(dangling)** — 이미 죽은 객체를 가리키는 참조·포인터·뷰. **읽으면 UB 다.**\
> 예: (1)의 일곱 탐침.

> **수명 연장(lifetime extension)** — 임시를 `const T&`·`T&&` 에 **직접** 묶으면 그 참조만큼 사는 규칙.\
> 예: (4)의 (a)(c)(e)(f).

> **전체 식(full-expression)** — 다른 식의 일부가 아닌 식. 임시는 **여기가 끝날 때** 죽는다(대개 세미콜론).\
> 예: (4)의 (b) — `pass(T{2})` 의 끝.

> **`stack-use-after-return` / `stack-use-after-scope`** — ASan 이 **돌아간 함수의 스택 / 끝난 블록의 스택**을 읽은 것을 부르는 이름.\
> 예: (1)의 탐침 1 · 5 와 2 · 3 · 6 · 7.

> **P2718** — 범위 `for` 의 범위 초기화식 안에서 만든 임시를 **루프 끝까지** 살리는 C++23 변경. 매크로 `__cpp_range_based_for` 가 **`202211L`** 이 된다(cppreference).\
> 예: (5)의 `201603`.

> **괄호 집합체 초기화(parenthesized aggregate initialization)** — C++20 부터 집합체를 `A a(x)` 로도 초기화하는 것. **참조 멤버의 임시는 연장되지 않는다.**\
> 예: (4)의 (g).

> **탈출 분석(escape analysis)** — 지역 변수가 함수 밖에서 쓰이는지 컴파일러가 따져 **힙에 놓을지** 정하는 것(Go).\
> 예: (7)의 `moved to heap: x`.

## 더 들어가면

- **`[[clang::lifetimebound]]`** — 「이 매개변수가 반환값보다 오래 살아야 한다」를 표시해 clang 이 (b)·탐침 2 류를 경고하게 하는 속성. 이 문서는 던지지 않았다.
- **C++26 의 「`return` 에서 임시에 묶으면 ill-formed」** — cppreference 의 예외 목록 첫 항목에 **(until C++26)** 표지가 있다. 이 문서는 **그 판을 던지지 않았다**(컴파일러가 없다).
- **GCC 15 · Clang 19 에서 (5)를 다시 던지기** — 이 머신에는 없다. 판이 오르면 **`__cpp_range_based_for` 와 `~Holder` 의 자리**를 다시 본다.
- **`-fsanitize=address` 와 `-O1`** — 이 문서는 `-O0`·`-O2` 만 던졌다.
