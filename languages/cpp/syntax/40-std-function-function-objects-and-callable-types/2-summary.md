# cpp/syntax/40 — `std::function`·함수 객체·호출 가능 타입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::function`](https://en.cppreference.com/w/cpp/utility/functional/function) · [`std::function` 생성자](https://en.cppreference.com/w/cpp/utility/functional/function/function) · [`std::bad_function_call`](https://en.cppreference.com/w/cpp/utility/functional/bad_function_call)\
> ★ 이 배치에서 **위 cppreference 세 쪽을 열어 확인했다** — `std::function` 은 「**can store, copy, and invoke any CopyConstructible Callable target -- functions (via pointers thereto), lambda expressions, bind expressions, or other function objects, as well as pointers to member functions**」 · 「**Invoking the target of an empty std::function results in std::bad_function_call exception being thrown.**」 · 생성자 쪽의 「**When the target is a function pointer or a std::reference_wrapper, small object optimization is guaranteed … no dynamic allocation takes place.**」 · 「**Other large objects may be constructed in dynamic allocated storage**」(★ **「may」 — 어디서부터 힙인지는 적혀 있지 않다**).
> **실행 검증** — 이 문서의 모든 출력·진단·역어셈블은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★★ **clang 도 같은 라이브러리** — `std::function` 의 크기·할당 칸은 **한 구현**이다. `-stdlib=libc++` 는 이 머신에 libc++ 가 없어 링크에서 막힌다 — 두 번째 구현은 **못 잰 것**) · GNU objdump 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`hold01.cpp`·`sbo01.cpp`·`ind01.cpp`·`empty01.cpp`·`ctx01.cpp`·`hold-grid.sh`·`sbo-grid.sh`·`ind-grid.sh`). 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — `std::function`·`std::bind`·람다는 **C++11**, `std::invoke` 는 **C++17**, `std::move_only_function` 은 **C++23** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[39번](../39-lambdas-and-captures/)에서 온다 — 앞 편이 잰 것은 다시 재지 않는다.**\
> [39번](../39-lambdas-and-captures/) (4)(6) — **람다 타입은 식마다 고유(`same type = 0`)** · **`sizeof` 가 캡처 크기**(`[]` 1 · `[x]` 4 · `[x, d]` 16) · **캡처 없는 람다는 함수 포인터로 바뀐다** · **move-only 람다는 `std::function` 에 못 담는다(`std::function target must be copy-constructible`) · C++23 `std::move_only_function` 은 담는다.**\
> ★★ **여기서 새로 묻는 것은 셋이다** — ① **일곱 가지 호출 가능 × 받는 자리 넷** 전체 격자 · ② **담을 때 힙을 쓰나**(할당 횟수) · ③ **부를 때 간접 호출이 남나**(역어셈블).
> **C 갈래와 잇기** — [C 갈래 35번](../../../c/syntax/35-function-pointers-and-callback-tables/)(함수 포인터와 콜백 테이블)이 **테이블 호출은 `-O2` 에서 `jmp [rdx+rax*8]` 한 줄**임을 보였다. 여기서는 **C 식 `void*` 문맥 콜백**과 `std::function` 을 나란히 놓는다((5)).
> **경계** — 「람다의 캡처와 수명」은 [39번](../39-lambdas-and-captures/), 「템플릿 인자 추론」은 [31번](../31-function-templates-and-argument-deduction/), 「`unique_ptr` 의 복사 금지」는 [26번](../26-unique-ptr-and-ownership-transfer/)이 정본이다.
> ★★★ **「`std::function` 은 느리다」는 이 문서가 싣지 않는다 — 시간을 재지 않았다.** 실은 것은 **할당 횟수 · `sizeof` · 역어셈블의 간접 분기 수**라는 **결정적 칸**뿐이다(규칙 24).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 역어셈블의 **오프셋·명령 줄 수**(판마다 다르다) · 진단의 **총 줄 수** | ★★★ **담기 격자의 통과 칸** · **할당 횟수(네 판 동일)** · **간접 분기가 남았나(0 / 1)** · **`cc exit`/`run exit`** · **격자의 마지막 줄** |
> | ★ `sizeof` 와 **힙으로 가는 문턱(16 바이트)** — **libstdc++ 13 의 관찰**(표준은 정하지 않는다) | ★★★ **함수 포인터·`std::reference_wrapper` 는 힙 0 회** — 이것만은 **cppreference 가 「guaranteed」** 라고 적는다 |

## 한눈에 — 쉽게 말하면

**`std::function` 은 「만능 콘센트 어댑터」다.** 벽에 꽂는 쪽은 **모양이 하나**(`int(int)`)이고, 반대쪽에는 **어떤 플러그든** 꽂힌다.

- **함수 포인터** — **맨 전선.** 모양이 딱 맞는 것만 들어간다(캡처 없는 람다까지). 상태를 실을 자리가 없다.
- **템플릿 `F&&`** — 기기마다 **전용 콘센트를 새로 만든다.** 무엇이든 받지만 기기마다 코드가 따로 생긴다 — 그래서 **컴파일러가 끝까지 들여다보고 녹여 버릴 수 있다**((4)의 `use_tpl` 이 명령 두 줄).
- **`std::function`** — **어댑터 한 개**로 모든 플러그를 받는다. 대신 어댑터 안에 **작은 칸**이 있어서 **작은 플러그는 칸에 넣고, 큰 플러그는 창고(힙)에 맡긴다**((3)). 그리고 부를 때 **어댑터가 안쪽 플러그를 한 번 더 찾아간다**(간접 호출 — (4)).
- **복사되지 않는 플러그**(move-only 람다)는 **이 어댑터에 안 들어간다** — 어댑터 자체가 복사되는 물건이라서다(39편 (4)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 맨 전선 | ★★ **함수 포인터 `R(*)(Args)`** — 캡처 없는 것만 | (1) **2 / 7** |
| 기기마다 전용 콘센트 | ★★ **템플릿 `F&&`** — 멤버 함수 포인터만 못 받는다 | (1) **6 / 7** |
| 만능 어댑터 | ★★★ **`std::function`** — 복사 안 되는 것만 못 받는다 | (1) **6 / 7** |
| 무엇이든 부르는 법 | ★★ **`std::invoke`** — 일곱 다 | (1) **7 / 7** |
| 어댑터 안의 작은 칸 | ★★★ **작은 버퍼 최적화(SBO)** — 이 판은 **16 바이트 · trivially copyable** 까지 | (3) |
| 어댑터가 한 번 더 찾아감 | ★★★ **간접 호출 `call *0x18(%rdi)`** | (4) |

```text
   호출 가능                  받는 자리                   이 판에서 무엇이 되나
   ─────────────────         ─────────────────           ─────────────────────────────────────
   함수 포인터 · 빈 람다  ─▶  int(*)(Obj&, int)      ─▶   주소 하나 · 부를 때 jmp *%rax
   캡처 · 함수 객체 · bind ─▶  std::function<…>      ─▶   16 바이트 이하면 안에 · 넘으면 new 1 회 · call *
   무엇이든              ─▶  template <class F>     ─▶   타입마다 새 함수 · -O2 에서 몸통이 녹는다
```

## 이 주제가 답하려는 질문

1. ★★★ **어떤 호출 가능을 어떤 자리가 받나 — 하나의 「호출 가능」으로 묶는 것은 누구인가**((1)(2)).
2. ★★★ **`std::function` 에 담으면 힙을 쓰나 — 몇 바이트부터, 무엇이 문턱을 바꾸나**((3)).
3. ★★★ **부를 때 무엇이 남나 — 간접 호출은 언제 사라지나**((4)).
4. ★★ **비어 있으면 · C 의 콜백과는 무엇이 다른가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ④ 할당 계수기와 ⑤ 역어셈블이다

★★★ **「타입 소거 비용」을 시간으로 재지 않는다** — 시간은 판마다 흔들린다(규칙 24). 대신 **비용의 원인** 둘을 **결정적으로 센다** — **힙 할당이 일어났나**(전역 `operator new` 를 가로채 횟수) · **간접 분기가 남았나**(`objdump -dr` 로 명령 수).

```text
① 다섯 층 표            담기 규칙은 표준 · SBO 문턱은 libstdc++ · 인라인은 컴파일러            (구현 세부사항 절)
② ★ 두 컴파일러          담기 격자 · 함수 포인터 변환 에러 전문                                (1)(2)
③ 실행 출력             bad_function_call · C 식 콜백과 합                                     (5)
④ ★★★ 할당 계수기        operator new 가로채기 — 캡처 크기별 담기·복사의 new 횟수              (3)
⑤ ★★★ 역어셈블          objdump -dr — 함수마다 간접 분기 수 · __throw_bad_function_call 재배치  (4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **무엇을 담을 수 있나는 표준 · 문턱은 구현 · 인라인은 최적화기** | **쓴다** |
| ★★ **② 두 컴파일러** | ★★★ 담기 격자 **56 칸 중 통과 42 · 컴파일러 사이 갈린 행 0 / 28** | **쓴다** |
| ③ 실행 출력 | `bad_function_call` 전문 · C 식 콜백 | **쓴다** |
| ★★★ **④ 할당 계수기** | ★★★ **본체** — **힙에 담긴 것 4 / 9 · 네 판 사이 갈린 줄 0** | **쓴다** |
| ★★★ **⑤ 역어셈블** | ★★★ **본체** — **간접 분기가 남은 칸 4 / 8(`-O2`)** · 컴파일러 사이 갈린 함수 0 / 4 | **쓴다** |
| 시간 측정 | 「`std::function` 은 느리다」 | ★ **안 쟀다**(규칙 24 — 원인 둘을 결정적 칸으로 대신 셌다) |
| ★ 두 번째 표준 라이브러리 | libc++ 의 SBO 문턱 | ★ **못 잰 것** — libc++ 가 이 머신에 없다(링크에서 막힘) |

### (1) ★★★ 담기 격자 — 호출 가능 일곱 × 받는 자리 넷

**언제 쓰나** — 콜백을 받는 함수의 **매개변수 타입**을 정할 때마다. 무엇을 넘겨 올지에 따라 **받을 수 있는 자리가 다르다.**

```cpp
/* hold01.cpp */
// 호출 가능 일곱(-DCALLABLE=1..7) × 받는 자리 넷(-DRECV=1..4). 서명은 모두 int(Obj&, int)
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

struct Obj {
    int base = 1;
    int add(int x) { return base + x; }
};
int add_free(Obj& o, int x) { return o.base + x; }
struct Adder {
    int operator()(Obj& o, int x) const { return o.base + x; }
};

using FnPtr = int (*)(Obj&, int);
int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
int recv_function(std::function<int(Obj&, int)> f, Obj& o, int x) { return f(o, x); }
template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
template <class F> int recv_invoke(F&& f, Obj& o, int x) { return std::invoke(std::forward<F>(f), o, x); }

int main() {
    Obj o;
    int k = 1;
    auto p = std::make_unique<int>(1);
    (void)k; (void)p;
#if CALLABLE == 1
    auto c = &add_free;
#elif CALLABLE == 2
    auto c = [](Obj& ob, int x) { return ob.base + x; };
#elif CALLABLE == 3
    auto c = [k](Obj& ob, int x) { return ob.base + x + k - 1; };
#elif CALLABLE == 4
    auto c = Adder{};
#elif CALLABLE == 5
    auto c = &Obj::add;
#elif CALLABLE == 6
    auto c = std::bind(add_free, std::placeholders::_1, std::placeholders::_2);
#elif CALLABLE == 7
    auto c = [q = std::move(p)](Obj& ob, int x) { return ob.base + x + *q - 1; };
#endif
#if RECV == 1
    std::printf("%d\n", recv_ptr(std::move(c), o, 41));
#elif RECV == 2
    std::printf("%d\n", recv_function(std::move(c), o, 41));
#elif RECV == 3
    std::printf("%d\n", recv_template(std::move(c), o, 41));
#elif RECV == 4
    std::printf("%d\n", recv_invoke(std::move(c), o, 41));
#endif
}
```

- ★★ **서명은 일곱 다 `int(Obj&, int)`** 다 — 그래야 **멤버 함수 `Obj::add(int)`** 도 같은 줄에 선다(멤버 함수는 **객체를 첫 인자로** 받는 셈이다).

```bash
# hold-grid.sh
# hold-grid.sh — 호출 가능 일곱 × 받는 자리 넷 × 컴파일러 둘. 칸에는 컴파일되면 찍힌 값, 안 되면 「에러」
calls=('1 함수 포인터' '2 캡처 없는 람다' '3 캡처 있는 람다' '4 함수 객체' '5 멤버 함수 포인터' '6 std::bind 결과' '7 move-only 람다')
recvs=('1 R(*)(Args)' '2 std::function' '3 템플릿 F&&' '4 std::invoke')
cell() {
  if ! $1 -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=$2 -DRECV=$3 hold01.cpp -o hx 2>/dev/null; then printf '에러'; return; fi
  printf '%s' "$(./hx)"
}
printf '%s\t%s\t%s\t%s\n' "호출 가능" "받는 자리" "g++" "clang++" > t.tsv
for c in "${calls[@]}"; do
  for r in "${recvs[@]}"; do
    printf '%s\t%s\t%s\t%s\n' "$c" "$r" "$(cell g++ ${c%% *} ${r%% *})" "$(cell clang++ ${c%% *} ${r%% *})" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
pass=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i != "에러") n++ } END { print n+0 }')
split=$(tail -n +2 t.tsv | awk -F'\t' '$3 != $4' | wc -l)
for r in "${recvs[@]}"; do
  n=$(tail -n +2 t.tsv | awk -F'\t' -v r="$r" '$2 == r && $3 != "에러"' | wc -l)
  printf '받는 자리 %s — 통과 %d / %d\n' "$r" "$n" "${#calls[@]}"
done
echo "통과 칸 $pass / $(( rows * 2 )) · 컴파일러 사이 갈린 행 $split / $rows"
rm -f hx t.tsv
```

```text
===== bash hold-grid.sh (exit=0) =====
호출 가능	받는 자리	g++	clang++
1 함수 포인터	1 R(*)(Args)	42	42
1 함수 포인터	2 std::function	42	42
1 함수 포인터	3 템플릿 F&&	42	42
1 함수 포인터	4 std::invoke	42	42
2 캡처 없는 람다	1 R(*)(Args)	42	42
2 캡처 없는 람다	2 std::function	42	42
2 캡처 없는 람다	3 템플릿 F&&	42	42
2 캡처 없는 람다	4 std::invoke	42	42
3 캡처 있는 람다	1 R(*)(Args)	에러	에러
3 캡처 있는 람다	2 std::function	42	42
3 캡처 있는 람다	3 템플릿 F&&	42	42
3 캡처 있는 람다	4 std::invoke	42	42
4 함수 객체	1 R(*)(Args)	에러	에러
4 함수 객체	2 std::function	42	42
4 함수 객체	3 템플릿 F&&	42	42
4 함수 객체	4 std::invoke	42	42
5 멤버 함수 포인터	1 R(*)(Args)	에러	에러
5 멤버 함수 포인터	2 std::function	42	42
5 멤버 함수 포인터	3 템플릿 F&&	에러	에러
5 멤버 함수 포인터	4 std::invoke	42	42
6 std::bind 결과	1 R(*)(Args)	에러	에러
6 std::bind 결과	2 std::function	42	42
6 std::bind 결과	3 템플릿 F&&	42	42
6 std::bind 결과	4 std::invoke	42	42
7 move-only 람다	1 R(*)(Args)	에러	에러
7 move-only 람다	2 std::function	에러	에러
7 move-only 람다	3 템플릿 F&&	42	42
7 move-only 람다	4 std::invoke	42	42
받는 자리 1 R(*)(Args) — 통과 2 / 7
받는 자리 2 std::function — 통과 6 / 7
받는 자리 3 템플릿 F&& — 통과 6 / 7
받는 자리 4 std::invoke — 통과 7 / 7
통과 칸 42 / 56 · 컴파일러 사이 갈린 행 0 / 28
```

- ★★★ **통과 칸 42 / 56 · 컴파일러 사이 갈린 행 0 / 28** — 두 컴파일러가 **같은 칸에서** 막혔다. 막히는 이유가 **언어 규칙**이라는 뜻이다(구현 품질이 아니라).
- ★★★ **`R(*)(Args)` 는 2 / 7** — **함수 포인터와 캡처 없는 람다만.** 캡처가 있든(3) 함수 객체든(4) **상태를 가진 것**은 주소 하나로 못 바뀐다.
- ★★★ **`std::function` 은 6 / 7** — **move-only 람다만 못 받는다**(39편 (4)의 `target must be copy-constructible`). **멤버 함수 포인터도 받는다**(5행) — 첫 인자 `Obj&` 를 객체로 쓴다.
- ★★★ **템플릿 `F&&` 는 6 / 7** — **move-only 도 받지만 멤버 함수 포인터는 못 받는다.** 몸통이 `f(o, x)` 라고 **괄호로 부르는데**, 멤버 함수 포인터는 **괄호로 불리지 않는다**((2)).
- ★★★ **`std::invoke` 는 7 / 7** — **「부르는 법」을 하나로 묶는 것은 `std::invoke` 다.** `std::function` 이 멤버 함수 포인터를 받는 것도 **안에서 같은 규칙(INVOKE)** 으로 부르기 때문이다.

```text
                         R(*)(Args)   std::function   템플릿 F&&   std::invoke
   함수 포인터              O             O              O            O
   캡처 없는 람다           O             O              O            O
   캡처 있는 람다           ✘             O              O            O
   함수 객체                ✘             O              O            O
   멤버 함수 포인터         ✘             O              ✘            O
   std::bind 결과           ✘             O              O            O
   move-only 람다           ✘             ✘              O            O
   ★ 위 격자에서 옮긴 요약이다 — 원본은 캡처. ✘ 의 이유가 셋이다: 상태 · 복사 · 괄호 호출
```

### (2) ★★ 막힌 칸의 에러 — 두 가지 다른 이유

**캡처 있는 람다 → 함수 포인터**(3행 × 1열):

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=3 -DRECV=1 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp: In function ‘int main()’:
hold01.cpp:43:43: error: cannot convert ‘std::remove_reference<main()::<lambda(Obj&, int)>&>::type’ {aka ‘main()::<lambda(Obj&, int)>’} to ‘FnPtr’ {aka ‘int (*)(Obj&, int)’}
   43 |     std::printf("%d\n", recv_ptr(std::move(c), o, 41));
      |                                  ~~~~~~~~~^~~
      |                                           |
      |                                           std::remove_reference<main()::<lambda(Obj&, int)>&>::type {aka main()::<lambda(Obj&, int)>}
hold01.cpp:17:20: note:   initializing argument 1 of ‘int recv_ptr(FnPtr, Obj&, int)’
   17 | int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
      |              ~~~~~~^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=3 -DRECV=1 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp:43:25: error: no matching function for call to 'recv_ptr'
   43 |     std::printf("%d\n", recv_ptr(std::move(c), o, 41));
      |                         ^~~~~~~~
hold01.cpp:17:5: note: candidate function not viable: no known conversion from 'typename std::remove_reference<(lambda at hold01.cpp:32:14) &>::type' (aka '(lambda at hold01.cpp:32:14)') to 'FnPtr' (aka 'int (*)(Obj &, int)') for 1st argument
   17 | int recv_ptr(FnPtr f, Obj& o, int x) { return f(o, x); }
      |     ^        ~~~~~~~
1 error generated.
```

- ★★★ **g++ `cannot convert … to ‘FnPtr’` · clang `no known conversion from '(lambda at …)' to 'FnPtr'`** — **변환 연산자 자체가 없다.** 캡처 없는 람다의 클로저 타입에만 **함수 포인터로 바뀌는 변환 함수**가 있다(39편 (6)의 `fp() = 1`).
- ★★ **두 컴파일러 다 첫 에러가 호출 줄(43행)** 을 가리킨다 — 템플릿 안이 아니라 **내 줄**이다(35편의 O/X 로 읽으면 O).

**멤버 함수 포인터 → 템플릿 `F&&`**(5행 × 3열):

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=5 -DRECV=3 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp: In instantiation of ‘int recv_template(F&&, Obj&, int) [with F = int (Obj::*)(int)]’:
hold01.cpp:47:38:   required from here
hold01.cpp:19:70: error: must use ‘.*’ or ‘->*’ to call pointer-to-member function in ‘f (...)’, e.g. ‘(... ->* f) (...)’
   19 | template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
      |                                                                     ~^~~~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCALLABLE=5 -DRECV=3 hold01.cpp -o ex (cc exit=1) =====
hold01.cpp:19:69: error: called object type 'int (Obj::*)(int)' is not a function or function pointer
   19 | template <class F> int recv_template(F&& f, Obj& o, int x) { return f(o, x); }
      |                                                                     ^
hold01.cpp:47:25: note: in instantiation of function template specialization 'recv_template<int (Obj::*)(int)>' requested here
   47 |     std::printf("%d\n", recv_template(std::move(c), o, 41));
      |                         ^
1 error generated.
```

- ★★★ **g++ `must use ‘.*’ or ‘->*’ to call pointer-to-member function` · clang `called object type 'int (Obj::*)(int)' is not a function or function pointer`** — **첫 에러가 템플릿 몸통(19행)** 이다. 템플릿은 **넘어온 것을 괄호로 부른다고 가정**했고, 그 가정이 인스턴스화에서 깨졌다(35편의 「제약 없는 템플릿은 몸통에서 터진다」).
- ★★ **고치는 법 한 줄** — 몸통을 `std::invoke(f, o, x)` 로 바꾸면 된다. (1)의 넷째 열이 그 판이다.

### (3) ★★★ 담을 때 힙을 쓰나 — 할당 계수기

**언제 쓰나** — `std::function` 을 **자주 만들거나 복사하는 자리**(이벤트 등록 · 작업 큐)에서 비용을 짐작할 때.

```cpp
/* sbo01.cpp */
// std::function 에 담을 때 operator new 가 몇 번 불리나 — 담는 것의 크기와 종류를 바꿔 가며 센다
#include <array>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <new>
#include <type_traits>

static int g_news = 0;
void* operator new(std::size_t n) {
    ++g_news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct Loud {                       // 8 바이트 · 복사 생성자를 직접 썼다
    long v = 1;
    Loud() = default;
    Loud(const Loud& o) : v(o.v) {}
};
int plain(int x) { return x + 1; }

template <class F>
void row(const char* name, F f) {
    int before = g_news;
    std::function<int(int)> fn = f;
    int made = g_news - before;
    before = g_news;
    std::function<int(int)> copy = fn;
    int copied = g_news - before;
    std::printf("%s\t%zu\t%d\t%d\t%d\t%d\n",
                name, sizeof(F), (int)std::is_trivially_copyable_v<F>, made, copied, copy(1));
}

int main() {
    std::printf("sizeof(std::function<int(int)>) = %zu\n", sizeof(std::function<int(int)>));
    std::printf("담는 것\tsizeof\ttrivially_copyable\tnew(담기)\tnew(복사)\tcall\n");
    std::array<char, 8> a8{};
    std::array<char, 16> a16{};
    std::array<char, 17> a17{};
    std::array<char, 24> a24{};
    std::array<char, 64> a64{};
    Loud loud;
    auto big = [a64](int x) { return x + a64[0] + 1; };
    row("함수 포인터", &plain);
    row("캡처 없는 람다", [](int x) { return x + 1; });
    row("캡처 8 바이트", [a8](int x) { return x + a8[0] + 1; });
    row("캡처 16 바이트", [a16](int x) { return x + a16[0] + 1; });
    row("캡처 17 바이트", [a17](int x) { return x + a17[0] + 1; });
    row("캡처 24 바이트", [a24](int x) { return x + a24[0] + 1; });
    row("캡처 64 바이트", big);
    row("캡처 Loud(8 바이트)", [loud](int x) { return x + (int)loud.v; });
    row("std::ref(64 바이트 람다)", std::ref(big));
}
```

```bash
# sbo-grid.sh
# sbo-grid.sh — sbo01.cpp 를 컴파일러 둘 × 최적화 둘 로 빌드해 돌리고, 네 판의 줄을 견준다
out=""
for c in g++ clang++; do
  for o in -O0 -O2; do
    $c -std=c++20 -Wall -Wextra -pedantic $o sbo01.cpp -o sx || { echo "cc 에러 $c $o"; exit 1; }
    ./sx > "run$c$o.txt" || exit 1
  done
done
cat "rung++-O0.txt"
bad=$(tail -n +2 "rung++-O0.txt" | awk -F'\t' 'NF != 6' | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
lines=$(wc -l < "rung++-O0.txt")
diffs=0
for f in "rung++-O2.txt" "runclang++-O0.txt" "runclang++-O2.txt"; do
  d=$(diff "rung++-O0.txt" "$f" | grep -c '^<')
  diffs=$(( diffs + d ))
done
heap=$(tail -n +3 "rung++-O0.txt" | awk -F'\t' '$4 > 0' | wc -l)
echo "힙에 담긴 것 $heap / $(( lines - 2 )) · 판 네 개 중 g++ -O0 과 갈린 줄 $diffs / $(( lines * 3 ))"
rm -f sx run*.txt
```

```text
===== bash sbo-grid.sh (exit=0) =====
sizeof(std::function<int(int)>) = 32
담는 것	sizeof	trivially_copyable	new(담기)	new(복사)	call
함수 포인터	8	1	0	0	2
캡처 없는 람다	1	1	0	0	2
캡처 8 바이트	8	1	0	0	2
캡처 16 바이트	16	1	0	0	2
캡처 17 바이트	17	1	1	1	2
캡처 24 바이트	24	1	1	1	2
캡처 64 바이트	64	1	1	1	2
캡처 Loud(8 바이트)	8	0	1	1	2
std::ref(64 바이트 람다)	8	1	0	0	2
힙에 담긴 것 4 / 9 · 판 네 개 중 g++ -O0 과 갈린 줄 0 / 33
```

- ★★★ **`sizeof(std::function<int(int)>) = 32`** — **담는 것이 64 바이트여도 32** 다. 크기가 안 바뀌니 **큰 것은 어딘가 다른 곳**에 있어야 한다.
- ★★★ **캡처 16 바이트까지 `new` 0 회 · 17 바이트부터 1 회** — **이 판의 문턱은 16 바이트**다. 담을 때 1 회, **복사할 때 또 1 회**(복사본도 자기 창고를 따로 잡는다).
- ★★★ **8 바이트짜리 `Loud` 도 1 회** — 크기는 문턱 안인데 **`trivially_copyable = 0`** 이다(복사 생성자를 직접 썼다). **문턱은 크기 하나가 아니다.** libstdc++ 13 은 **「작고 · trivially copyable 한 것」만 안에 넣는다**(이 판의 관찰 — 표준 문장이 아니다).
- ★★★ **함수 포인터 · `std::ref(64 바이트 람다)` 는 0 회** — **이 둘만은 cppreference 가 「guaranteed」** 라고 적은 칸이다. `std::ref` 는 **큰 람다를 참조로 감싸 8 바이트로 만든다** — 대신 **원본 람다가 살아 있어야** 한다(39편 (1)의 참조 캡처와 같은 수명 문제).
- ★★ **네 판(g++·clang × `-O0`·`-O2`) 사이 갈린 줄 0 / 33** — 할당 횟수는 **최적화 수준을 타지 않았다**(규칙 24 의 「계수는 판을 잘 안 탄다」). ★ 두 컴파일러가 **같은 libstdc++** 라 이 0 은 **「한 구현이라 같다」** 이다 — 구현이 다르면 문턱도 다를 수 있다(**못 잰 것** — libc++ 없음).

```text
   std::function<int(int)> (32 바이트)
   ┌──────────────────────────────┬──────────────┬──────────────┐
   │ 안쪽 칸 16 바이트              │ 관리 함수     │ 호출 함수     │
   └──────────────────────────────┴──────────────┴──────────────┘
      │
      ├─ 캡처 ≤ 16 바이트 · trivially copyable   →  칸 안에 그대로        new 0 회
      ├─ 함수 포인터 · std::ref                    →  칸 안에 (보장)        new 0 회
      └─ 그 밖(17 바이트 이상 · Loud)              →  칸에는 주소만, 몸은 힙  new 1 회 (복사마다 또 1 회)
   ★ 칸의 배치(16 · 관리 · 호출)는 libstdc++ 13 의 것이다 — 32 = 16 + 8 + 8 이 이 판에서 맞는다는 관찰
```

### (4) ★★★ 부를 때 간접 호출이 남나 — 역어셈블

**언제 쓰나** — 콜백이 **뜨거운 루프 안**에서 불릴 때. 「인라인될 수 있나」는 **호출 자리에서 컴파일러가 무엇을 보나**에 달렸다.

```cpp
/* ind01.cpp */
// 같은 「두 배」를 세 가지 자리로 받는다 — 템플릿 · std::function · 함수 포인터. -O2 -c 로 빌드해 역어셈블한다
#include <functional>

template <class F> int apply_tpl(F&& f, int x) { return f(x); }

int use_tpl(int x) { return apply_tpl([](int v) { return v * 2; }, x); }
int use_function(const std::function<int(int)>& f, int x) { return f(x); }
int use_ptr(int (*f)(int), int x) { return f(x); }
int use_local(int x) {
    std::function<int(int)> f = [](int v) { return v * 2; };
    return f(x);
}
```

```text
===== g++ -std=c++20 -O2 -c ind01.cpp -o ind.o && objdump -dr --no-show-raw-insn -C ind.o (exit=0) =====

ind.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_invoke(std::_Any_data const&, int&&)>:
   0:	endbr64
   4:	mov    (%rsi),%eax
   6:	add    %eax,%eax
   8:	ret
   9:	nopl   0x0(%rax)

0000000000000010 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)>:
  10:	endbr64
  14:	test   %edx,%edx
  16:	je     30 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x20>
  18:	cmp    $0x1,%edx
  1b:	je     20 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x10>
  1d:	xor    %eax,%eax
  1f:	ret
  20:	mov    %rsi,(%rdi)
  23:	xor    %eax,%eax
  25:	ret
  26:	cs nopw 0x0(%rax,%rax,1)
  30:	lea    0x0(%rip),%rax        # 37 <std::_Function_handler<int (int), use_local(int)::{lambda(int)#1}>::_M_manager(std::_Any_data&, std::_Any_data const&, std::_Manager_operation)+0x27>
			33: R_X86_64_PC32	.data.rel.ro-0x4
  37:	mov    %rax,(%rdi)
  3a:	xor    %eax,%eax
  3c:	ret
  3d:	nopl   (%rax)

0000000000000040 <use_tpl(int)>:
  40:	endbr64
  44:	lea    (%rdi,%rdi,1),%eax
  47:	ret
  48:	nopl   0x0(%rax,%rax,1)

0000000000000050 <use_function(std::function<int (int)> const&, int)>:
  50:	endbr64
  54:	sub    $0x18,%rsp
  58:	mov    %fs:0x28,%rax
  61:	mov    %rax,0x8(%rsp)
  66:	xor    %eax,%eax
  68:	cmpq   $0x0,0x10(%rdi)
  6d:	mov    %esi,0x4(%rsp)
  71:	je     90 <use_function(std::function<int (int)> const&, int)+0x40>
  73:	lea    0x4(%rsp),%rsi
  78:	call   *0x18(%rdi)
  7b:	mov    0x8(%rsp),%rdx
  80:	sub    %fs:0x28,%rdx
  89:	jne    a5 <use_function(std::function<int (int)> const&, int)+0x55>
  8b:	add    $0x18,%rsp
  8f:	ret
  90:	mov    0x8(%rsp),%rax
  95:	sub    %fs:0x28,%rax
  9e:	jne    a5 <use_function(std::function<int (int)> const&, int)+0x55>
  a0:	call   a5 <use_function(std::function<int (int)> const&, int)+0x55>
			a1: R_X86_64_PLT32	std::__throw_bad_function_call()-0x4
  a5:	call   aa <use_function(std::function<int (int)> const&, int)+0x5a>
			a6: R_X86_64_PLT32	__stack_chk_fail-0x4
  aa:	nopw   0x0(%rax,%rax,1)

00000000000000b0 <use_ptr(int (*)(int), int)>:
  b0:	endbr64
  b4:	mov    %rdi,%rax
  b7:	mov    %esi,%edi
  b9:	jmp    *%rax
  bb:	nopl   0x0(%rax,%rax,1)

00000000000000c0 <use_local(int)>:
  c0:	endbr64
  c4:	lea    (%rdi,%rdi,1),%eax
  c7:	ret
```

- ★★★ **`use_tpl` 은 `lea (%rdi,%rdi,1),%eax` · `ret`** — 템플릿이 람다 타입마다 새 함수를 만들었고, `-O2` 가 **호출을 통째로 녹였다**(`v * 2` 가 `x + x` 로).
- ★★★ **`use_function` 은 `cmpq $0x0,0x10(%rdi)` → `je` → `call *0x18(%rdi)`** — ① **비어 있나를 먼저 본다**(비었으면 `std::__throw_bad_function_call()` 로 — **이 호출은 `-dr` 의 재배치 줄로만 이름이 보인다**) ② **객체 안 `0x18` 자리에 든 주소로 간접 호출**한다. (3)의 그림에서 **「호출 함수」 칸**이 그 자리다.
- ★★ **`use_ptr` 은 `jmp *%rax`** — 함수 포인터도 **간접 분기**다(꼬리 호출이라 `call` 이 아니라 `jmp`). C 갈래 35번의 테이블 호출 `jmp [rdx+rax*8]` 과 같은 모양이다.
- ★★★ **`use_local` 은 `use_tpl` 과 같은 두 줄** — **`std::function` 도 만든 자리와 부르는 자리가 한 함수 안에 보이면 간접 호출이 사라졌다.** 간접 호출이 남는 것은 **`std::function` 이라서가 아니라 「무엇이 들었는지 호출 자리에서 모를 때」** 다.

```text
===== clang++ -std=c++20 -O2 -c ind01.cpp -o ind.o && objdump -dr --no-show-raw-insn -C ind.o (exit=0) =====

ind.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <use_tpl(int)>:
   0:	lea    (%rdi,%rdi,1),%eax
   3:	ret
   4:	data16 data16 cs nopw 0x0(%rax,%rax,1)

0000000000000010 <use_function(std::function<int (int)> const&, int)>:
  10:	push   %rax
  11:	mov    %esi,0x4(%rsp)
  15:	cmpq   $0x0,0x10(%rdi)
  1a:	je     26 <use_function(std::function<int (int)> const&, int)+0x16>
  1c:	lea    0x4(%rsp),%rsi
  21:	call   *0x18(%rdi)
  24:	pop    %rcx
  25:	ret
  26:	call   2b <use_function(std::function<int (int)> const&, int)+0x1b>
			27: R_X86_64_PLT32	std::__throw_bad_function_call()-0x4
  2b:	nopl   0x0(%rax,%rax,1)

0000000000000030 <use_ptr(int (*)(int), int)>:
  30:	mov    %rdi,%rax
  33:	mov    %esi,%edi
  35:	jmp    *%rax
  37:	nopw   0x0(%rax,%rax,1)

0000000000000040 <use_local(int)>:
  40:	lea    (%rdi,%rdi,1),%eax
  43:	ret
```

```bash
# ind-grid.sh
# ind-grid.sh — ind01.cpp 의 네 함수 × 컴파일러 둘, -O2 -c. objdump -dr 로 함수 몸통마다 센다
# 칸: 간접 분기(call *·jmp *) 수 / 직접 call 수 / __throw_bad_function_call 재배치가 있나 / 명령 줄 수
funcs=(use_tpl use_function use_ptr use_local)
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "함수" "컴파일러" "간접 분기" "직접 call" "bad_function_call 재배치" "명령 줄 수" > t.tsv
for f in "${funcs[@]}"; do
  for c in g++ clang++; do
    $c -std=c++20 -O2 -c ind01.cpp -o ind.o || { echo "cc 에러"; exit 1; }
    objdump -dr --no-show-raw-insn -C ind.o > dump.txt || exit 1
    body=$(awk -v f="$f" '/^[0-9a-f]+ </ { on = ($0 ~ ("^[0-9a-f]+ <" f "\\(") && $0 !~ /\)::/); next } on' dump.txt)
    ind=$(printf '%s\n' "$body" | grep -cE '(call|jmp) +\*')
    dir=$(printf '%s\n' "$body" | grep -E 'call +[0-9a-f]+ ' | wc -l)
    thr=$(printf '%s\n' "$body" | grep -q '__throw_bad_function_call' && echo O || echo X)
    n=$(printf '%s\n' "$body" | grep -cE '^ +[0-9a-f]+:')
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$f" "$c" "$ind" "$dir" "$thr" "$n" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 6' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
ind=$(tail -n +2 t.tsv | awk -F'\t' '$3 > 0' | wc -l)
split=$(tail -n +2 t.tsv | awk -F'\t' '{ k[$1] = k[$1] "|" $3 $5 } END { for (f in k) { split(k[f], a, "|"); if (a[2] != a[3]) n++ } print n+0 }')
echo "간접 분기가 남은 칸 $ind / $rows · 간접 분기 수·재배치가 컴파일러 사이 갈린 함수 $split / $(( rows / 2 ))"
rm -f ind.o dump.txt t.tsv
```

```text
===== bash ind-grid.sh (exit=0) =====
함수	컴파일러	간접 분기	직접 call	bad_function_call 재배치	명령 줄 수
use_tpl	g++	0	0	X	4
use_tpl	clang++	0	0	X	3
use_function	g++	1	2	O	21
use_function	clang++	1	1	O	10
use_ptr	g++	1	0	X	5
use_ptr	clang++	1	0	X	4
use_local	g++	0	0	X	3
use_local	clang++	0	0	X	2
간접 분기가 남은 칸 4 / 8 · 간접 분기 수·재배치가 컴파일러 사이 갈린 함수 0 / 4
```

- ★★★ **간접 분기가 남은 칸 4 / 8 · 컴파일러 사이 갈린 함수 0 / 4** — **`use_function`·`use_ptr` 은 두 컴파일러 다 1**, **`use_tpl`·`use_local` 은 둘 다 0.** `__throw_bad_function_call` 재배치도 **`use_function` 두 칸에만** 있다.
- ★ **명령 줄 수**(g++ 21 대 clang 10 등)는 **흔들리는 칸**이다 — 스택 보호(`%fs:0x28`)·`endbr64` 같은 **그 판의 기본 옵션**이 섞인다. 근거로 쓰는 것은 **간접 분기가 0 이냐 1 이냐**뿐이다.

### (5) ★★ 비어 있으면 · C 의 콜백과 견주면

```cpp
/* empty01.cpp */
// 비어 있는 std::function 을 부르면 — 기본은 잡아서 찍고, -DUNCAUGHT 이면 잡지 않는다. 찍는 것은 표준 오류로
#include <cstdio>
#include <functional>

int main() {
    std::function<int(int)> f;
    std::fprintf(stderr, "bool(f) = %d\n", static_cast<bool>(f));
#ifdef UNCAUGHT
    return f(1);
#else
    try {
        f(1);
    } catch (const std::bad_function_call& e) {
        std::fprintf(stderr, "잡은 예외 what() = %s\n", e.what());
    }
    f = nullptr;
    std::fprintf(stderr, "nullptr 대입 후 bool(f) = %d\n", static_cast<bool>(f));
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic empty01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bool(f) = 0
잡은 예외 what() = bad_function_call
nullptr 대입 후 bool(f) = 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic empty01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
bool(f) = 0
잡은 예외 what() = bad_function_call
nullptr 대입 후 bool(f) = 0
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUNCAUGHT empty01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
bool(f) = 0
terminate called after throwing an instance of 'std::bad_function_call'
  what():  bad_function_call
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUNCAUGHT empty01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
bool(f) = 0
terminate called after throwing an instance of 'std::bad_function_call'
  what():  bad_function_call
```

- ★★★ **잡으면 `what() = bad_function_call` · 안 잡으면 `terminate called after throwing an instance of 'std::bad_function_call'` · `run exit=134`**(`abort`). (4)의 `cmpq $0x0` → `__throw_bad_function_call` 이 **이 예외의 출처**다.
- ★★ **`bool(f) = 0`** — 기본 생성 · `nullptr` 대입 뒤 둘 다 **비어 있다.** 부르기 전에 `if (f)` 로 물을 수 있다.
- ★ 찍는 것을 **표준 오류로** 보냈다 — `abort` 로 끝나는 판에서 **표준 출력 버퍼가 사라지는 것**을 피하려고(규칙 19-A).

```cpp
/* ctx01.cpp */
// C 식 콜백(함수 포인터 + void* 문맥)과 std::function 콜백 — 같은 합을 두 방식으로 모은다
#include <cstdio>
#include <functional>

// C 식: 상태를 넘길 자리가 따로 있어야 한다
void each_c(const int* a, int n, void (*cb)(int, void*), void* ctx) {
    for (int i = 0; i < n; ++i) cb(a[i], ctx);
}
// C++ 식: 상태는 호출 가능한 것 안에 들어 있다
void each_fn(const int* a, int n, const std::function<void(int)>& cb) {
    for (int i = 0; i < n; ++i) cb(a[i]);
}

struct Sum { int total = 0; };

int main() {
    const int a[] = {1, 2, 3, 4};
    Sum s1;
    each_c(a, 4, [](int v, void* c) { static_cast<Sum*>(c)->total += v; }, &s1);
    int s2 = 0;
    each_fn(a, 4, [&s2](int v) { s2 += v; });
    std::printf("C 식 합 = %d · std::function 합 = %d\n", s1.total, s2);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ctx01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
C 식 합 = 10 · std::function 합 = 10
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctx01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
C 식 합 = 10 · std::function 합 = 10
```

- ★★★ **같은 합 10** — C 식은 **상태를 `void* ctx` 로 따로 넘기고 콜백 안에서 캐스트**한다. `std::function` 식은 **상태가 호출 가능한 것 안에 들어 있다**(`[&s2]`).
- ★★ **C 식 콜백 자리에 캡처 없는 람다가 들어갔다** — (1)의 1열 규칙 그대로다. **C API 에 C++ 상태를 넘기는 표준 관용구**가 「캡처 없는 람다 + `void*`」다.
- ★ C 갈래 35번은 **서명이 어긋난 함수 포인터 호출을 clang `-fsanitize=function` 으로** 잡았다. `std::function` 에서는 **서명이 안 맞으면 담는 순간 컴파일 에러**라 그 사고가 **컴파일 단계로 올라온다.**

## 문법 — 형태와 규칙

### 형태

```text
   int (*fp)(int) = f;                       함수 포인터 — 캡처 없는 람다도 된다
   std::function<int(int)> fn = callable;    무엇이든(복사 가능한 것) · 비면 bad_function_call
   template <class F> void g(F&& f)          타입마다 새 함수 — 인라인 여지가 가장 크다
   std::invoke(f, args...)                   멤버 함수 포인터까지 한 규칙으로 부른다 (C++17)
   std::function<int(int)> fn = std::ref(big);   큰 것을 참조로 — 힙 0 회 보장 · 원본 수명 주의
   std::move_only_function<int()> m = …;     move-only 까지 (C++23 · 39편 (4))
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **함수 포인터 자리는 캡처 없는 것만**((1) 2 / 7 · (2)의 변환 에러).
- ★★★ **`std::function` 은 복사 가능한 것 전부 — 멤버 함수 포인터 포함, move-only 제외**((1) 6 / 7).
- ★★★ **템플릿으로 받을 때 몸통은 `std::invoke` 로 불러라** — 괄호로 부르면 멤버 함수 포인터에서 터진다((2)).
- ★★★ **`std::function` 의 힙 할당은 구현 문턱에 달렸다** — 이 판은 **16 바이트 · trivially copyable**. 함수 포인터 · `std::reference_wrapper` 만 **보장**((3)).
- ★★ **간접 호출은 「호출 자리에서 대상을 모를 때」 남는다**((4)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| 캡처 있는 람다를 `int(*)(Obj&, int)` 에 | `cannot convert … to ‘FnPtr’` | `no known conversion from '(lambda …)' to 'FnPtr'` | (2) |
| 멤버 함수 포인터를 `f(o, x)` 로 부르는 템플릿에 | `must use ‘.*’ or ‘->*’ to call pointer-to-member function` | `called object type 'int (Obj::*)(int)' is not a function or function pointer` | (2) |
| move-only 람다를 `std::function` 에 | `std::function target must be copy-constructible` | 같은 단언 | 39편 (4) |

## 어디서 틀리나

### 1. ★★★ 「`std::function` 은 항상 힙을 쓴다」 / 「절대 안 쓴다」

(3)이 둘 다 반증한다 — **9 가지 중 4 가지만 1 회.** 문턱은 **크기(16)와 종류(trivially copyable)** 둘이고, **이 판의 것**이다.

### 2. ★★★ 「작으면 힙을 안 쓴다」

(3)의 **`Loud`(8 바이트) 가 1 회**다. **복사 생성자를 직접 쓴 캡처**는 작아도 창고로 간다(이 판).

### 3. ★★★ 「`std::function` 은 항상 간접 호출이다」

(4)의 **`use_local` 이 두 줄**이다. 남는 것은 **대상이 호출 자리에서 안 보일 때**다 — `use_function` 처럼 **참조로 넘겨받은** 경우.

### 4. ★★ 「함수 포인터는 직접 호출이다」

(4)의 **`use_ptr` 은 `jmp *%rax`** — **간접 분기**다. 대상이 안 보이면 함수 포인터도 `std::function` 과 같은 처지다.

### 5. ★★ 「템플릿으로 받으면 무엇이든 받는다」

(1)(2) — **멤버 함수 포인터는 괄호로 안 불린다.** `std::invoke` 로 불러야 7 / 7 이다.

### 6. ★ 「`std::ref` 로 감싸면 공짜다」

(3) — 할당은 0 회지만 **원본의 수명**을 떠안는다. 원본이 먼저 죽으면 39편 (1)의 참조 캡처와 같은 댕글링이다(이 편은 그 칸을 던지지 않았다).

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 비용 칸은 거의 전부 「구현」 층**에 산다 — 표준은 **무엇을 담을 수 있나**를 정하고, **어떻게 담나(힙 · 칸 크기)** 는 두 줄(함수 포인터 · `reference_wrapper`)만 정한다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **담을 수 있는 것(CopyConstructible Callable) · 비면 `bad_function_call` · 캡처 없는 람다만 함수 포인터 변환 · INVOKE 규칙 · 함수 포인터·`reference_wrapper` 는 힙 없음** | 두 컴파일러 · cppreference | — |
| **조건부 표준** | 특정 판에서만 | ★★ **`std::invoke` C++17 · `std::move_only_function` C++23** | 39편 (4) | — |
| **구현 정의 · 라이브러리** | 문서화 의무 없음 | ★★★ **`sizeof = 32` · 안쪽 칸 16 바이트 · trivially copyable 조건** | 할당 계수기((3)) | ★★ **두 컴파일러가 같은 libstdc++ 라 「구현이 바뀌면」은 못 잰 것** |
| **컴파일러의 것** | 표준 밖 | ★★★ **인라인 · 간접 호출 제거**((4)) · 스택 보호·`endbr64` | `objdump -dr` | ★ **호출 자리가 다른 번역 단위면** 이 결과는 안 나온다(던지지 않았다) |
| **UB** | 아무 일이나 | ★ 이 편에서는 **던진 칸이 없다** — 비어 있는 호출은 **UB 가 아니라 예외**다((5)) | — | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| C API 에 콜백을 넘긴다 | ★★★ **캡처 없는 람다 + `void*` 문맥** | (1) 1열 · (5) |
| 부르는 함수를 헤더에 둘 수 있다 · 뜨거운 루프 | ★★★ **템플릿 `F&&` + `std::invoke`** | (4) 인라인 · (1) 7 / 7 |
| 콜백을 **저장**한다(멤버 · 컨테이너) · 타입이 여럿 | ★★★ **`std::function`** — 캡처를 16 바이트 이하로 두면 이 판에서 힙 0 | (3) |
| 저장할 것이 move-only | ★★ **`std::move_only_function`(C++23)** | 39편 (4) |
| 큰 함수 객체를 복사 없이 저장 | ★ **`std::ref`** — 원본 수명을 책임진다 | (3) |
| 저장할 것이 멤버 함수 | ★★ **`std::function` 이 직접 받는다** 또는 람다로 감싼다 | (1) 5행 |

## 핵심 문장

- ★★★ **호출 가능 일곱 × 받는 자리 넷에서 통과 42 / 56 · 컴파일러 사이 갈린 행 0** — 함수 포인터 2 / 7 · `std::function` 6 / 7(move-only 제외) · 템플릿 6 / 7(멤버 함수 포인터 제외) · **`std::invoke` 7 / 7**.
- ★★★ **`std::function<int(int)>` 은 32 바이트 — 이 판(libstdc++ 13)은 캡처 16 바이트 · trivially copyable 까지 힙 0 회, 넘으면 담기 1 회 · 복사 1 회.** 함수 포인터·`std::ref` 의 0 회만 **보장**이다.
- ★★★ **`-O2` 에서 간접 분기가 남은 것은 대상을 모르는 두 함수(`std::function` 참조 · 함수 포인터)뿐 — 한 함수 안에서 만든 `std::function` 은 템플릿처럼 녹았다.**
- ★★ **비어 있는 `std::function` 호출은 `bad_function_call` — 부를 때마다 비었나를 먼저 보는 `cmpq $0x0` 가 그 값이다.**
- ★★ **「느리다」는 싣지 않았다 — 비용의 원인(할당 · 간접 분기)을 결정적 칸으로만 셌다.**

## 관련 자료

- [39번](../39-lambdas-and-captures/) (4)(6) — ★★★ **move-only 람다와 `std::function` · 람다 타입의 고유성 · `sizeof`** — 여기서는 그 위에 **담기 격자 · 할당 · 간접 호출**을 얹었다.
- [31번](../31-function-templates-and-argument-deduction/) — 템플릿 `F&&` 가 타입마다 새 함수를 만드는 것((4)의 `use_tpl`).
- [35번](../35-instantiation-header-placement-and-reading-errors/) — ★ **첫 에러가 호출 줄인가(O/X)** — (2)의 두 에러가 O 와 X 로 갈린다.
- [26번](../26-unique-ptr-and-ownership-transfer/) — move-only 의 출처.
- C 갈래 [35번](../../../c/syntax/35-function-pointers-and-callback-tables/) — ★★ **테이블 호출 `jmp [rdx+rax*8]` · 서명 불일치 호출은 clang `-fsanitize=function`** — 여기의 `use_ptr` 과 `void*` 콜백이 그 짝이다. **그쪽은 함수 포인터의 선언·섹션까지, 여기는 C++ 가 그것을 무엇으로 감싸나.**
- Rust 갈래 [35번](../../../rust/syntax/35-function-pointers-and-returning-closures/) — ★★ **잡은 것이 없는 클로저만 `fn` 포인터가 된다 · 갈래마다 다른 클로저는 `Box<dyn Fn>`** — C++ 의 `std::function` 자리가 `Box<dyn Fn>` 이다.

## 용어 풀이

> **호출 가능(Callable)** — `std::invoke(f, args…)` 로 부를 수 있는 것. 함수 포인터 · 함수 객체(람다 포함) · 멤버 함수 포인터 · 멤버 데이터 포인터.\
> 예: (1)의 넷째 열 7 / 7.

> **함수 객체(function object)** — `operator()` 를 가진 클래스의 객체. 람다의 클로저도 함수 객체다.\
> 예: (1)의 `Adder`.

> **타입 소거(type erasure)** — 서로 다른 타입을 **하나의 겉모양**(`std::function<int(int)>`) 뒤에 숨기는 기법. 대가로 **저장 자리(칸 또는 힙)** 와 **간접 호출**이 생긴다.\
> 예: (3)(4).

> **작은 버퍼 최적화(SBO, small buffer optimization)** — 작은 대상은 객체 안의 칸에, 큰 대상은 힙에 두는 방식.\
> 예: (3)의 16 바이트 문턱.

> **간접 호출(indirect call)** — 부를 주소를 **실행 중에 메모리·레지스터에서 읽어** 가는 호출(`call *0x18(%rdi)` · `jmp *%rax`).\
> 예: (4).

> **`std::bad_function_call`** — 비어 있는 `std::function` 을 부르면 던지는 예외.\
> 예: (5).

## 더 들어가면

- **`std::move_only_function` 의 크기와 문턱** — 이 편은 **재지 않았다.** 같은 할당 계수기로 `-std=c++23` 을 던지면 된다.
- **번역 단위를 넘은 호출** — `use_function` 을 다른 `.cpp` 에서 부르면 LTO 없이는 (4)의 `use_local` 같은 제거가 안 된다고 예상되지만 **던지지 않았다.**
- **libc++ 의 SBO** — 이 머신에 libc++ 가 없어 **못 잰 것**이다.
