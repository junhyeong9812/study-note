# cpp/syntax/25 — 정적 멤버·`inline` 변수(C++17) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 정적 멤버](https://en.cppreference.com/w/cpp/language/static) · [cppreference — 정의와 ODR](https://en.cppreference.com/w/cpp/language/definition) · [cppreference — 정적 초기화 순서 문제](https://en.cppreference.com/w/cpp/language/siof) · [cppreference — `constinit`](https://en.cppreference.com/w/cpp/language/constinit)\
> ★ **이 배치에서는 위 cppreference 네 쪽을 열지 못했다**(웹 도구 한도에 걸렸다). 그래서 이 문서는 **규칙을 한 줄도 문서에서 옮기지 않고**,\
> **전부 두 컴파일러·링커·`nm` 에 던져 본 출력으로** 적었다. 「표준이 이렇게 말한다」라고 적은 곳은 **컴파일러 경고가 스스로 판을 밝힌 것**(`inline variables are a C++17 extension` 등)만이다.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU ld(binutils 2.42)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★ **이 주제는 번역 단위가 둘이어야 선다** — 블록마다 **`-c` 로 따로 컴파일한 뒤 `.o` 를 링크**했다. 한 줄로 `g++ a.cpp b.cpp` 를 하면\
> 링커 진단에 **임시 파일 이름**(`ccXXXX.o`)이 박혀 재현이 안 되기 때문이다.\
> ★ 표준 판이 결론을 가르는 블록은 **`-std=c++14` / `-std=c++17` 을 배너에 적었다.** 나머지는 `-std=c++20` 이다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 정적 데이터 멤버는 **C++98부터**. **`inline` 변수와 「`constexpr` 정적 멤버는 암묵 `inline`」은 C++17부터**, **`constinit` 은 C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **이 편은 C 갈래와 한 문제를 나눠 쓴다** — C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **29번**([`29-scope-and-linkage-static-extern/`](../../../c/syntax/29-scope-and-linkage-static-extern/)) (5)(9)가\
> **잠정 정의 `int t;` 를 두 파일에 두면 `-fcommon` 이면 합쳐지고(`nm` 의 `C`) 기본값이면 깨진다(`B`)** · **C++17 전역 `inline int` 는 g++ `u` · clang++ `V`** 를 이미 쟀다 — 다시 재지 않고 인용한다.\
> ★★ **여기서 새로 묻는 것은 셋이다** — **클래스 안의 정적 데이터 멤버**가 같은 문제를 어떻게 겪나 · **ODR 사용**이면 정의가 왜 필요한가 · **정적 초기화 순서**.
> **경계** — 「정적 멤버의 문법·`this` 가 없다」는 [12번](../12-class-basics-members-access-and-this/) (7)이, 「`static` 은 언제 죽나 · 함수 지역 `static`」은 [14번](../14-destructors-and-deterministic-destruction/) (3)이,\
> 「단일 정의 규칙(ODR) 일반과 모듈」은 목록의 **55번 주제**가 정본이다. 「C 의 링크 셋과 `nm` 글자」는 C 29번이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 링커 진단의 **`.text+0x…` 오프셋** | ★★★ **링크가 되나(`cc exit`)** · **`multiple definition`/`undefined reference` 가 무엇의 이름인가** — 이 주제의 답 자체다 |
> | `nm` 의 **주소 칸** | ★★★ **`nm` 의 글자**(`B`·`u`·`V`·`U`·`C`) · ★★ **초기화 로그의 순서** · **격자의 O/X** · **`__cxa_guard` 호출 수** |
> | — | ★★ **링크 순서에 따른 값**(`0` 대 `42`) — **한 링커 판에서의 관찰**이지만 재실행으로는 안 흔들린다 |

## 한눈에 — 쉽게 말하면

**정적 데이터 멤버는 「동네 게시판」이고, 정의는 「게시판을 세우는 일」이다.**

아파트 동마다 **안내문(헤더)을** 붙인다. 안내문에 「**게시판은 1층에 있습니다**(선언)」라고 적는 것은 몇 장을 붙여도 괜찮다.\
그런데 안내문에 「**여기에 게시판을 세우세요**(정의)」라고 적어 놓으면 — **안내문을 붙인 동마다 게시판을 하나씩 세운다.** 게시판이 **둘**이 되고, 관리실(링커)이 「**어느 게 진짜냐**」며 거부한다.

- **C++14 까지** — 안내문에는 「있습니다」만 적고, **한 동(한 `.cpp`)에만** 「세우세요」를 적어야 했다.
- **C++17 `inline`** — 안내문에 「**세우세요 — 단, 동네에 하나만**」이라고 적는다. 여러 동이 세워도 관리실이 **하나로 합친다.**
- **초기화 순서** — 게시판 둘이 서로의 **첫 글**을 베껴 쓰려 하면, **어느 게시판이 먼저 섰느냐**가 결과를 바꾼다. 그 순서는 **관리실 마음**이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 안내문 | ★★ **헤더** — 여러 번역 단위에 포함된다 | (1) |
| 「게시판은 1층에」 | ★★ **클래스 안의 `static int count;`** — 선언 | (1) |
| 「여기에 세우세요」 | ★★★ **`int Cfg::count = 0;`** — 정의. 헤더에 두면 **포함한 수만큼** 생긴다 | (1) |
| 「세우세요 — 동네에 하나만」 | ★★★ **`static inline int count = 0;`**(C++17) — `nm` 의 **`u`/`V`** | (1)(2) |
| 게시판 주소를 알려 줘야 하는 일 | ★★ **ODR 사용** — 참조로 넘기면 **정의가 있어야** 한다 | (3) |
| 누가 먼저 섰느냐 | ★★★ **정적 초기화 순서** — **링크 순서**가 갈랐다 | (4) |
| 「처음 볼 때 세운다」 | ★★ **함수 지역 `static`** — 순서 문제를 푼다 · **스레드 안전 가드** | (5) |

```text
   cfg.h                          cfg_a.cpp          cfg_b.cpp
   struct Cfg { static int count; };   #include "cfg.h"   #include "cfg.h"
   int Cfg::count = 0;   ← 정의         정의 1개 ─┐        정의 1개 ─┐
                                                  └── 링커 ──┘  ★ multiple definition

   struct Cfg { static inline int count = 0; };   C++17
                                        정의 1개(u/V) ─┐   정의 1개(u/V) ─┐
                                                       └──── 링커 ────┘   ★ 하나로 합친다
```

## 이 주제가 답하려는 질문

1. ★★★ **정적 데이터 멤버의 정의는 어디에 두나** — 헤더에 두면 무엇이 깨지고, C++17 `inline` 은 그것을 `nm` 에서 **무슨 글자로** 바꾸나((1)(2)).
2. ★★ **클래스 안에서 값을 준 `static const`/`static constexpr` 는 정의가 따로 필요한가** — **ODR 사용**과 **판(C++14/17)과** **최적화 수준**에 따라((3)).
3. ★★★ **두 번역 단위의 정적 초기화 순서는 누가 정하나** — 그리고 **함수 지역 `static`** 은 그것을 어떻게 푸나((4)(5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러·링커 대조와 `nm` 이다

★★★ **이 주제의 본체는 ② 링커 진단과 `nm` 이다** — 정의 위치 문제는 **컴파일이 아니라 링크에서** 드러나고, `nm` 이 **그 정의가 어떤 종류의 심볼인지**를 글자로 말한다.

```text
① 초기화 로그           두 번역 단위의 정적 초기화가 어느 순서로 도나           (4)(5)
② ★ 링커 · nm           multiple definition · undefined reference · B/u/V/U/C   (1)(2)(3)
③ ASan                   —                                                        부적용
④ 어셈블리(-O2)          함수 지역 static 의 가드 · __cxa_guard 호출 수           (5)
⑤ 경고 격자              C++14 에서 inline 이 경고만 내나 · -Wdeprecated         (2)(3)
⑥ <type_traits>          —                                                        부적용
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 초기화 로그 | ★★★ **링크 순서만 바꿨는데 `42` 대 `0`** | **쓴다** |
| ★★★ **② 링커 · `nm`** | ★★★ **본체** — 판 격자 8칸 · ODR 격자 24칸 · `nm` 글자 | **쓴다** |
| ③ ASan | ★ **부적용** — 초기화 순서 문제에서 읽은 값은 **0 으로 초기화된 정적 저장소**라 메모리 오류가 아니다 | **안 쓴다** |
| ④ 어셈블리 | ★ `-O2` 에서 **`__cxa_guard_acquire`/`release` 2회**와 **가드 바이트 검사** | **쓴다** |
| ⑤ 경고 격자 | C++14 `inline` **경고 2 · 2** · 중복 `constexpr` 정의는 **`-Wdeprecated` 라야 1 · 1** | **쓴다** |
| ⑥ `<type_traits>` | ★ **부적용** — 정의 위치·링크는 **타입의 성질이 아니다** | **안 쓴다** |

- ★★ **③ 을 부적용으로 둔 이유** — (4)의 순서 문제에서 먼저 읽힌 `Config::base` 는 **정적 저장소라 0 으로 채워진 뒤**에 읽혔다. **UB 가 아니라 「값이 아직 안 들어온 것」이다** — ASan 이 볼 오류가 없다.\
  ★ 대신 **「0 이 들어 있었다」를 로그가 직접 찍는다**(`읽은 값 0`).
- ★ **C 29번의 `nm` 창을 다시 열지 않은 것은 「안 쟀다」가 아니다** — 전역 `inline int` 의 `u`/`V` 는 거기서 쟀고, 여기서는 **클래스 안의 정적 멤버**로 **같은 글자가 나오는지**만 본다.

### (1) ★★★ 헤더에 정의한 정적 데이터 멤버 — 두 번역 단위가 포함하면

**언제 쓰나** — 헤더 하나로 끝나는 라이브러리(헤더 온리)를 만들 때마다. **이 절이 이 주제의 중심이다.**

```cpp
/* cfg.h */
// 정적 데이터 멤버를 헤더 안에서 정의한다. -DASK_INLINE 이면 C++17 inline 판
#pragma once
struct Cfg {
#ifdef ASK_INLINE
    static inline int count = 0;
#else
    static int count;
#endif
    static int bump();
};
#ifndef ASK_INLINE
int Cfg::count = 0;
#endif
```

```cpp
/* cfg_a.cpp */
// 번역 단위 1 — cfg.h 를 포함하고 bump() 를 정의한다
#include "cfg.h"
int Cfg::bump() { return ++count; }
```

```cpp
/* cfg_b.cpp */
// 번역 단위 2 — cfg.h 를 포함하고 main 에서 쓴다
#include <cstdio>
#include "cfg.h"
int main() {
    Cfg::bump();
    Cfg::bump();
    Cfg::count += 10;
    std::printf("count = %d\n", Cfg::count);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex (cc exit=1) =====
/usr/bin/ld: cfg_b.o:(.bss+0x0): multiple definition of `Cfg::count'; cfg_a.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && clang++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && clang++ cfg_a.o cfg_b.o -o ex (cc exit=1) =====
/usr/bin/ld: cfg_b.o:(.bss+0x0): multiple definition of `Cfg::count'; cfg_a.o:(.bss+0x0): first defined here
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★★ **컴파일은 두 번 다 통과하고 링크에서 깨진다** — `multiple definition of 'Cfg::count'` .\
  ★ `int Cfg::count = 0;` 이 **헤더에 있으니** 두 `.cpp` 가 **각자 하나씩** 정의를 갖게 됐다.
```text
===== ld --version | sed -n 1p (exit=0) =====
GNU ld (GNU Binutils for Ubuntu) 2.42
```

- ★★ **두 컴파일러가 같은 링커(GNU ld)를 부르니 첫 줄이 한 글자도 같다** — 뒤의 요약 줄만 다르다(`collect2: error` · `clang++: error: linker command failed`).

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 B Cfg::count

cfg_b.o:
                 U Cfg::bump()
0000000000000000 B Cfg::count
0000000000000000 T main
                 U printf
```

- ★★★ **두 오브젝트 다 `B Cfg::count`** — `B` 는 「**이 파일이 자리를 가진 정의**(0 으로 채워지는 영역)」다. **같은 이름의 `B` 가 둘**이면 링커는 하나를 고를 방법이 없다.
- ★ C 29번 (5)의 **기본값(`-fno-common`) 판과 같은 글자**다.

★★★ **`-DASK_INLINE` 으로 `static inline int count = 0;` 로 바꾸면** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
count = 12
===== nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 u Cfg::count

cfg_b.o:
                 U Cfg::bump()
0000000000000000 u Cfg::count
0000000000000000 T main
                 U printf
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && clang++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
count = 12
===== nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 V Cfg::count

cfg_b.o:
0000000000000000 r .L.str
                 U Cfg::bump()
0000000000000000 V Cfg::count
0000000000000000 T main
                 U printf
```

- ★★★ **링크가 되고 `count = 12`** — `bump()` 두 번 + `10`. **두 번역 단위가 같은 하나를 봤다.**
- ★★★ **글자가 바뀐다 — g++ `u`, clang++ `V`.** `u` 는 GNU 의 **「유일 전역 심볼」**, `V` 는 「**약한 객체**」다.\
  ★ **둘 다 「여러 오브젝트에 있어도 하나로 합쳐라」를** 링커에게 말하는 표시이고, **어느 글자를 쓰나는 구현이 정한다** — C 29번 (9)의 전역 `inline int` 와 **같은 글자·같은 갈림**이다.

```text
                       nm 글자        링커가 하는 일
   int Cfg::count = 0;   B           ★ 이 파일이 가진 정의 — 둘이면 multiple definition
   static inline int …   u (g++)     ★ 유일 전역 — 여럿이어도 하나로
                         V (clang)   ★ 약한 객체 — 여럿이어도 하나로
   (C) int t; -fcommon   C           공용 — 여럿이어도 하나로 (C 29번 (5))

   ★ C 가 컴파일러 확장(-fcommon)으로 하던 일을 C++17 은 언어 문법(inline)으로 약속한다
```

### (2) ★★ 판 격자 — `-std=c++14` 에서 `inline` 을 쓰면

**언제 쓰나** — 「C++17 기능을 썼는데 옛 판으로 빌드되는 저장소」에서.

```bash
# cfg-grid.sh
# cfg-grid.sh — cfg.h 두 판 × 표준 두 판 × 컴파일러 둘. 따로 컴파일한 뒤 링크까지 가나, 경고가 몇 건인가
printf '%-8s %-7s %-16s %-10s %-6s %s\n' "컴파일러" "표준" "cfg.h" "링크" "경고" "nm(cfg_a.o 의 count)"
ok=0; okw=0; n=0
for c in g++ clang++; do
  for s in c++14 c++17; do
    for m in "" -DASK_INLINE; do
      w=$({ $c -std=$s -Wall -Wextra -pedantic $m -c cfg_a.cpp -o cfg_a.o; $c -std=$s -Wall -Wextra -pedantic $m -c cfg_b.cpp -o cfg_b.o; } 2>&1 | grep -c 'warning:')
      if $c cfg_a.o cfg_b.o -o ex >/dev/null 2>&1; then l="O $(./ex)"; else l="X"; fi
      k=$(nm cfg_a.o | grep '_ZN3Cfg5countE' | awk '{print $(NF-1)}')
      printf '%-8s %-7s %-16s %-10s %-6s %s\n' "$c" "$s" "${m:-(클래스 밖 정의)}" "$l" "$w" "$k"
      n=$((n+1)); case $l in O*) ok=$((ok+1)); [ "$w" -gt 0 ] && okw=$((okw+1));; esac
    done
  done
done
echo "링크까지 간 칸 $ok / $n · 그중 경고가 난 칸 $okw"
```

```text
===== bash cfg-grid.sh (exit=0) =====
컴파일러 표준  cfg.h            링크     경고 nm(cfg_a.o 의 count)
g++      c++14   (클래스 밖 정의) X          0      B
g++      c++14   -DASK_INLINE     O count = 12 2      u
g++      c++17   (클래스 밖 정의) X          0      B
g++      c++17   -DASK_INLINE     O count = 12 0      u
clang++  c++14   (클래스 밖 정의) X          0      B
clang++  c++14   -DASK_INLINE     O count = 12 2      V
clang++  c++17   (클래스 밖 정의) X          0      B
clang++  c++17   -DASK_INLINE     O count = 12 0      V
링크까지 간 칸 4 / 8 · 그중 경고가 난 칸 2
```

- ★★★ **클래스 밖 정의 판은 네 칸 다 X** — 판·컴파일러와 **무관하게** 깨진다.
- ★★★ **`inline` 판은 네 칸 다 링크된다 — C++14 판까지.** 그리고 **C++14 칸만 경고 2**(번역 단위마다 1)다.

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && g++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
In file included from cfg_a.cpp:2:
cfg.h:5:12: warning: inline variables are only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^~~~~~
In file included from cfg_b.cpp:3:
cfg.h:5:12: warning: inline variables are only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^~~~~~
count = 12
```

```text
===== clang++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && clang++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && clang++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
In file included from cfg_a.cpp:2:
./cfg.h:5:12: warning: inline variables are a C++17 extension [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^
1 warning generated.
In file included from cfg_b.cpp:3:
./cfg.h:5:12: warning: inline variables are a C++17 extension [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^
1 warning generated.
count = 12
```

```text
===== echo "g++   -std=c++14 -pedantic-errors cfg_a.cpp 에러 $(g++ -std=c++14 -Wall -Wextra -pedantic-errors -DASK_INLINE -c cfg_a.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
g++   -std=c++14 -pedantic-errors cfg_a.cpp 에러 1
===== echo "clang -std=c++14 -pedantic-errors cfg_a.cpp 에러 $(clang++ -std=c++14 -Wall -Wextra -pedantic-errors -DASK_INLINE -c cfg_a.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
clang -std=c++14 -pedantic-errors cfg_a.cpp 에러 1
```

- ★★★ **이 편의 「종료 코드 0인데 ill-formed」** — `inline` 변수는 **C++17 문법**이라 C++14 에서는 ill-formed 인데, 두 컴파일러 다 **경고만 내고**(`only available with '-std=c++17'` · `a C++17 extension`) **`cc exit=0 · run exit=0` 이고 값도 맞다.**
- ★★ **`-pedantic-errors` 라야 에러 1 · 1** — [24번](../24-explicit-and-converting-constructors/) (7)의 `explicit(bool)` 과 **같은 집안**이다.

### (3) ★★ 클래스 안에서 값을 준 상수 — 참조로 넘기면 정의가 필요하다

**언제 쓰나** — `static const int N = 7;` 을 **`std::max`·`std::min`** 처럼 **`const T&` 를 받는 함수**에 넘길 때.

```cpp
/* odr01.cpp */
// 클래스 안에서 값을 준 정적 상수 둘 — 값으로 읽기와 const int& 로 넘기기
// -DASK_REF_A · -DASK_REF_B 로 참조로 넘기는 줄을 하나씩 켠다 · -DASK_DEF_A · -DASK_DEF_B 는 클래스 밖 정의를 더한다
#include <algorithm>
#include <cstdio>

struct K {
    static const int     A = 7;
    static constexpr int B = 9;
};

#ifdef ASK_DEF_A
const int K::A;           // 클래스 밖 정의 — 초기자 없이
#endif
#ifdef ASK_DEF_B
constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
#endif

int main() {
    int x = 8;
    std::printf("값으로 읽기  A+0=%d B+0=%d\n", K::A + 0, K::B + 0);
#ifdef ASK_REF_A
    std::printf("std::max(K::A, x) = %d\n", std::max(K::A, x));
#endif
#ifdef ASK_REF_B
    std::printf("std::max(K::B, x) = %d\n", std::max(K::B, x));
#endif
    (void)x;
}
```

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DASK_REF_B -c odr01.cpp -o odr01.o && g++ odr01.o -o ex (cc exit=1) =====
/usr/bin/ld: odr01.o: warning: relocation against `_ZN1K1BE' in read-only section `.text'
/usr/bin/ld: odr01.o: in function `main':
odr01.cpp:(.text+0x4a): undefined reference to `K::B'
/usr/bin/ld: warning: creating DT_TEXTREL in a PIE
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++14 -Wall -Wextra -pedantic -DASK_REF_B -c odr01.cpp -o odr01.o && clang++ odr01.o -o ex (cc exit=1) =====
/usr/bin/ld: odr01.o: in function `main':
odr01.cpp:(.text+0x2a): undefined reference to `K::B'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★★ **C++14 에서 `std::max(K::B, x)` 가 `undefined reference to 'K::B'`** 로 깨진다 — **`K::B + 0` 처럼 값으로만 읽으면 되던 것**이다.
- ★★★ **이유는 참조다** — `std::max` 는 `const int&` 를 받으므로 **`K::B` 의 주소가 필요**하다. 주소가 필요한 쓰임을 **ODR 사용**이라 하고, ODR 사용하면 **정의가 한 곳에 있어야** 한다.\
  ★ 클래스 안의 `= 9` 는 **값을 알려 주는 선언**일 뿐 **자리를 만들지 않는다**(C++14).
- ★ g++ 판의 `relocation against ... in read-only section` 줄은 **링커가 덧붙인 부수 경고**다 — 근거는 `undefined reference` 줄과 `cc exit=1` 이다.

★★★ **판 · 최적화 · 탐침 · 컴파일러를 전부 던진다.**

```bash
# odr-grid.sh
# odr-grid.sh — odr01.cpp 를 탐침 셋 × 표준 두 판 × 최적화 두 판 × 컴파일러 둘로 링크까지 던진다
printf '%-8s %-7s %-4s %-12s %s\n' "컴파일러" "표준" "-O" "탐침" "링크"
n0=0; n2=0; b0=0; b2=0
for c in g++ clang++; do
  for s in c++14 c++17; do
    for m in "" -DASK_REF_A -DASK_REF_B; do
      for o in -O0 -O2; do
        if $c -std=$s $o $m odr01.cpp -o ex >/dev/null 2>&1; then l="O"; else l="X undefined"; fi
        if [ "$o" = -O0 ]; then n0=$((n0+1)); [ "$l" = O ] || b0=$((b0+1)); else n2=$((n2+1)); [ "$l" = O ] || b2=$((b2+1)); fi
        printf '%-8s %-7s %-4s %-12s %s\n' "$c" "$s" "$o" "${m:-(값만)}" "$l"
      done
    done
  done
done
echo "링크가 깨진 칸  -O0 $b0 / $n0 · -O2 $b2 / $n2"
```

```text
===== bash odr-grid.sh (exit=0) =====
컴파일러 표준  -O   탐침       링크
g++      c++14   -O0  (값만)     O
g++      c++14   -O2  (값만)     O
g++      c++14   -O0  -DASK_REF_A  X undefined
g++      c++14   -O2  -DASK_REF_A  O
g++      c++14   -O0  -DASK_REF_B  X undefined
g++      c++14   -O2  -DASK_REF_B  O
g++      c++17   -O0  (값만)     O
g++      c++17   -O2  (값만)     O
g++      c++17   -O0  -DASK_REF_A  X undefined
g++      c++17   -O2  -DASK_REF_A  O
g++      c++17   -O0  -DASK_REF_B  O
g++      c++17   -O2  -DASK_REF_B  O
clang++  c++14   -O0  (값만)     O
clang++  c++14   -O2  (값만)     O
clang++  c++14   -O0  -DASK_REF_A  X undefined
clang++  c++14   -O2  -DASK_REF_A  O
clang++  c++14   -O0  -DASK_REF_B  X undefined
clang++  c++14   -O2  -DASK_REF_B  O
clang++  c++17   -O0  (값만)     O
clang++  c++17   -O2  (값만)     O
clang++  c++17   -O0  -DASK_REF_A  X undefined
clang++  c++17   -O2  -DASK_REF_A  O
clang++  c++17   -O0  -DASK_REF_B  O
clang++  c++17   -O2  -DASK_REF_B  O
링크가 깨진 칸  -O0 6 / 12 · -O2 0 / 12
```

- ★★★ **`static constexpr` 는 C++14 에서 깨지고 C++17 에서 된다** — `-DASK_REF_B` 의 `-O0` 칸이 **X → O**. **C++17 부터 `constexpr` 정적 데이터 멤버는 암묵 `inline`** 이라 **클래스 안의 한 줄이 곧 정의**가 됐다.
- ★★★ **`static const`(constexpr 아님)는 C++17 에서도 깨진다** — `-DASK_REF_A` 의 `-O0` 칸이 **두 판 다 X**. **암묵 `inline` 은 `constexpr` 에만** 붙는다.
- ★★★ **`-O2` 에서는 12칸 전부 링크된다** — `링크가 깨진 칸 -O0 6 / 12 · -O2 0 / 12`. 최적화가 `std::max` 를 **펼쳐서 참조가 사라지고**, 참조가 사라지니 **심볼을 찾지 않는다.**\
  ★★★ **이것이 이 편의 두 번째 「종료 코드 0인데 ill-formed」다** — 정의 없이 ODR 사용한 프로그램은 **진단이 필요 없는 ill-formed** 이고, **`-O2` 빌드는 그것을 말없이 통과시킨다.**\
  ★ 「릴리스 빌드는 되는데 디버그 빌드만 링크가 깨진다」가 이 모양이다.

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic-errors -O2 -DASK_REF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::B, x) = 9
===== clang++ -std=c++14 -Wall -Wextra -pedantic-errors -O2 -DASK_REF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::B, x) = 9
```

- ★★★ **`-pedantic-errors` 를 켜도 두 컴파일러 다 `cc exit=0 · run exit=0`** — 진단이 필요 없는 규칙이라 **컴파일러가 볼 의무가 없다.** 앞 배치들의 「`-pedantic-errors` 라야 잡힌다」 항목과 **다른 종류**다.

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && nm -C odr01.o | grep 'K::' (exit=0) =====
                 U K::A
0000000000000000 u K::B
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && nm -C odr01.o | grep 'K::' (exit=0) =====
                 U K::A
0000000000000000 V K::B
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && echo "-O2 에서 K:: 심볼 $(nm -C odr01.o | grep -c 'K::')개" (exit=0) =====
-O2 에서 K:: 심볼 0개
```

- ★★ **`nm` 이 판정을 글자로 보인다** — C++17 에서 **`K::A` 는 `U`**(정의되지 않음 — 다른 곳에 있어야 한다), **`K::B` 는 `u`/`V`**(이 파일이 `inline` 정의를 가진다).
- ★ **`-O2` 에서는 `K::` 심볼이 0개** — 참조가 사라져 **아무것도 요구하지 않는다.** 위 격자의 `-O2` 칸이 O 인 이유가 이것이다.

★★ **고치는 법 — 클래스 밖 정의를 하나 더한다**(`-DASK_DEF_A -DASK_DEF_B`).

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -DASK_DEF_A -DASK_DEF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::A, x) = 8
std::max(K::B, x) = 9
===== g++ -std=c++17 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -DASK_DEF_A -DASK_DEF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::A, x) = 8
std::max(K::B, x) = 9
```

```text
===== echo "g++   -std=c++17 기본 플래그 경고 $(g++ -std=c++17 -Wall -Wextra -pedantic -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:') · -Wdeprecated 경고 $(g++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -std=c++17 기본 플래그 경고 0 · -Wdeprecated 경고 1
===== echo "clang -std=c++17 기본 플래그 경고 $(clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:') · -Wdeprecated 경고 $(clang++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -std=c++17 기본 플래그 경고 0 · -Wdeprecated 경고 1
===== g++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null (cc exit=0) =====
odr01.cpp:15:15: warning: redundant redeclaration of ‘constexpr’ static data member ‘K::B’ [-Wdeprecated]
   15 | constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
      |               ^
odr01.cpp:8:26: note: previous declaration of ‘K::B’
    8 |     static constexpr int B = 9;
      |                          ^
===== clang++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null (cc exit=0) =====
odr01.cpp:15:18: warning: out-of-line definition of constexpr static data member is redundant in C++17 and is deprecated [-Wdeprecated-redundant-constexpr-static-def]
   15 | constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
      |                  ^
1 warning generated.
```

- ★★ **C++14 · C++17 둘 다 링크되고 값이 맞다.** `const int K::A;` 는 **초기자 없이** 쓴다(값은 클래스 안에 있다).
- ★★ **C++17 에서 `constexpr int K::B;` 는 쓸데없는 중복이고 폐기 예정(deprecated)** 이다 — 두 컴파일러의 경고가 그렇게 말한다.\
  ★★★ **그런데 `-Wall -Wextra -pedantic` 으로는 0 · 0** 이고 **`-Wdeprecated` 를 켜야 1 · 1** 이다. 옛 판 코드를 C++17 으로 올려도 **아무 말이 없다.**

```text
                          C++14 · -O0         C++17 · -O0          -O2 (두 판)
   static const int A = 7      값: O  참조: X      값: O  참조: X  ★      전부 O  ★ ill-formed 가 통과
   static constexpr int B = 9  값: O  참조: X      값: O  참조: O  ★      전부 O

   ★ C++17 의 암묵 inline 은 constexpr 에만 — const 는 여전히 클래스 밖 정의가 필요하다
```

### (4) ★★★ 정적 초기화 순서 — 링크 순서만 바꿨는데 값이 바뀐다

**언제 쓰나** — 한 파일의 정적 멤버를 **다른 파일의 정적 멤버로** 초기화할 때. **이 편의 두 번째 급소다.**

```cpp
/* siof.h */
// siof.h — 두 번역 단위가 나눠 쓰는 선언
#pragma once
struct Config { static int base; };
struct Report { static int doubled; };
int& lazy_base();
```

```cpp
/* siof_cfg.cpp */
// siof_cfg.cpp — 동적 초기화가 필요한 정적 멤버 하나와, 같은 값을 함수 지역 static 으로 주는 함수
#include <cstdio>
#include "siof.h"

static int read_base() { std::fprintf(stderr, "    [siof_cfg] read_base() 가 돈다\n"); return 21; }

#ifdef ASK_CONSTINIT
constinit int Config::base = read_base();
#else
int Config::base = read_base();
#endif

int& lazy_base() {
    static int b = read_base();       // 처음 부를 때 초기화된다
    return b;
}
```

```cpp
/* siof_use.cpp */
// siof_use.cpp — 다른 번역 단위의 값으로 자기를 초기화한다. -DASK_LAZY 이면 함수를 거친다
#include <cstdio>
#include "siof.h"

static int make_doubled() {
#ifdef ASK_LAZY
    int b = lazy_base();
#else
    int b = Config::base;
#endif
    std::fprintf(stderr, "    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 %d\n", b);
    return b * 2;
}
int Report::doubled = make_doubled();

int main() {
    std::fprintf(stderr, "    [main] Report::doubled = %d\n", Report::doubled);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && g++ -std=c++20 -Wall -Wextra -pedantic -c siof_use.cpp -o siof_use.o && g++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== g++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 0
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 0
```

- ★★★ **`siof_cfg.o siof_use.o` 순서면 `42`, `siof_use.o siof_cfg.o` 순서면 `0`** — 소스도 컴파일러도 오브젝트도 **한 바이트도 안 바꿨다.** 링크 명령의 **순서 두 낱말**만 바꿨다.
- ★★★ **로그가 이유를 보인다** — 뒤 판에서는 `Report::doubled` 가 **먼저** 초기화되면서 `Config::base` 를 읽었고, 그때 **`read_base()` 가 아직 안 돌아** 값이 **0** 이었다.
- ★★ **0 이 들어 있던 이유** — 정적 저장소는 **동적 초기화 전에 0 으로 채워진다.** 그래서 **쓰레기가 아니라 0** 이다(UB 가 아니다).
- ★★★ **층 — 이것은 「미명시」의 교과서다.** 표준은 **서로 다른 번역 단위의 동적 초기화 사이의 순서를 정하지 않는다.**\
  ★★ **「GNU ld 는 명령줄 순서대로 초기화한다」는 이 판의 관찰**이지 약속이 아니다 — 링커·LTO·링크 방식이 바뀌면 달라질 수 있다.
- ★ **clang 도 같은 두 값**이다 — 같은 링커를 부르기 때문이다. **「두 컴파일러에서 같았다」가 보장이 아닌** 자리다.

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c siof_use.cpp -o siof_use.o && clang++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== clang++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 0
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 0
```

```text
   링크 순서            초기화 순서                         Report::doubled
   siof_cfg.o siof_use.o  Config::base = 21  →  doubled = 21*2     42
   siof_use.o siof_cfg.o  doubled = 0*2      →  Config::base = 21   0   ★ 0 은 「아직 안 들어온 값」

   ★ 소스에는 순서가 없다 — 순서는 링커가 정한 것이고, 표준은 그것을 미명시로 둔다
```

### (5) ★★ 함수 지역 `static` 으로 푼다 — 그리고 그 대가인 가드

**언제 쓰나** — (4)의 순서 문제를 **코드로** 없애고 싶을 때(「처음 쓸 때 짓기」 관용구).

★ **「함수 지역 `static` 은 처음 부를 때 생긴다」는 [14번](../14-destructors-and-deterministic-destruction/) (3)이 로그로 쟀다** — 여기서는 그것이 **순서 문제를 푸는지**와 **무엇으로 스레드 안전을 사는지**를 본다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && g++ -std=c++20 -Wall -Wextra -pedantic -DASK_LAZY -c siof_use.cpp -o siof_use.o && g++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== g++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 42
```

- ★★★ **두 링크 순서 다 `42`** — `siof_use.cpp` 가 `Config::base` 대신 **`lazy_base()` 를 부르면**, 그 함수 안의 `static int b` 가 **그 순간 초기화**된다. 누가 먼저 섰느냐와 **무관**하다.
- ★ **`read_base()` 가 두 번 찍힌다** — 한 번은 `Config::base`(여전히 남아 있다), 한 번은 `lazy_base` 안의 `b` 다. **둘은 다른 변수**다.

```text
===== echo "g++   -O2                        __cxa_guard 호출 $(g++ -std=c++20 -O2 -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
g++   -O2                        __cxa_guard 호출 2
===== echo "g++   -O2 -fno-threadsafe-statics __cxa_guard 호출 $(g++ -std=c++20 -O2 -fno-threadsafe-statics -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
g++   -O2 -fno-threadsafe-statics __cxa_guard 호출 0
===== echo "clang -O2                        __cxa_guard 호출 $(clang++ -std=c++20 -O2 -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
clang -O2                        __cxa_guard 호출 2
===== echo "clang -O2 -fno-threadsafe-statics __cxa_guard 호출 $(clang++ -std=c++20 -O2 -fno-threadsafe-statics -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
clang -O2 -fno-threadsafe-statics __cxa_guard 호출 0
```

```text
===== g++ -std=c++20 -O2 -S -o - siof_cfg.cpp | awk '/^_Z9lazy_basev:/,/cfi_endproc/' | grep -E '_ZGV|__cxa_guard|^\.L[0-9]+:|testb|je[[:space:]]|jne[[:space:]]|ret$|movl[[:space:]]+\$21' (exit=0) =====
	movzbl	_ZGVZ9lazy_basevE1b(%rip), %eax
	testb	%al, %al
	je	.L16
	ret
.L16:
	leaq	_ZGVZ9lazy_basevE1b(%rip), %rbx
	call	__cxa_guard_acquire@PLT
	jne	.L17
	ret
.L17:
	movl	$21, _ZZ9lazy_basevE1b(%rip)
	call	__cxa_guard_release@PLT
	ret
.L6:
```

- ★★★ **`-O2` 에서도 `__cxa_guard_acquire`/`release` 호출이 2개** — C++11 부터 함수 지역 `static` 의 초기화는 **스레드 안전**해야 하고, 이 구현은 그것을 **가드 함수**로 산다.
- ★★ **빠른 길이 있다** — 첫 세 줄 `movzbl _ZGV… ; testb ; je` 가 **가드 바이트 하나를 읽고**, 이미 초기화됐으면 **바로 `ret`** 한다. 가드 함수는 **처음 한 번**(또는 경쟁할 때)만 부른다.
- ★ **`-fno-threadsafe-statics` 면 0 · 0** — 스레드 안전을 **끄는 스위치**다. 여러 스레드가 처음 부르면 **두 번 초기화될 수 있게** 된다.
- ★ **시간은 재지 않았다** — 「가드가 느리다」가 아니라 「**가드 바이트 검사 한 번 + 처음에만 함수 호출**」이라는 **명령의 모양**만 적는다.

★★ **C++20 `constinit` 은 다른 길로 푼다** — 「**이 변수는 동적 초기화를 하지 않는다**」를 컴파일러가 강제한다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONSTINIT -c siof_cfg.cpp -o siof_cfg.o (cc exit=1) =====
siof_cfg.cpp:8:15: error: ‘constinit’ variable ‘Config::base’ does not have a constant initializer
    8 | constinit int Config::base = read_base();
      |               ^~~~~~
siof_cfg.cpp:8:39: error: call to non-‘constexpr’ function ‘int read_base()’
    8 | constinit int Config::base = read_base();
      |                              ~~~~~~~~~^~
siof_cfg.cpp:5:12: note: ‘int read_base()’ declared here
    5 | static int read_base() { std::fprintf(stderr, "    [siof_cfg] read_base() 가 돈다\n"); return 21; }
      |            ^~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONSTINIT -c siof_cfg.cpp -o siof_cfg.o (cc exit=1) =====
siof_cfg.cpp:8:23: error: variable does not have a constant initializer
    8 | constinit int Config::base = read_base();
      |                       ^      ~~~~~~~~~~~
siof_cfg.cpp:8:1: note: required by 'constinit' specifier here
    8 | constinit int Config::base = read_base();
      | ^~~~~~~~~
siof_cfg.cpp:8:30: note: non-constexpr function 'read_base' cannot be used in a constant expression
    8 | constinit int Config::base = read_base();
      |                              ^
siof_cfg.cpp:5:12: note: declared here
    5 | static int read_base() { std::fprintf(stderr, "    [siof_cfg] read_base() 가 돈다\n"); return 21; }
      |            ^
1 error generated.
```

- ★★ **`read_base()` 가 `constexpr` 이 아니라 거부된다** — `constinit` 은 **상수 초기화만** 받는다. 받아 주면 그 변수는 **동적 초기화 단계에 아예 참여하지 않으므로** 순서 문제가 원리상 없다.
- ★ 이 문서는 **거부되는 쪽만** 던졌다 — `constinit` 이 받아 주는 판(상수 초기자)의 순서 실험은 **하지 않았다**(상수 초기화는 로그를 찍을 수 없다).

### (6) ★ C 와 나란히 — C++ 에는 잠정 정의가 없다

**언제 쓰나** — C 코드를 C++ 로 옮겼더니 **전역 `int t;` 에서 링크가 깨질 때.**

```cpp
/* tent1.cpp */
int t;
int get1() { return t; }
```

```cpp
/* tent2.cpp */
int t;
int get1();
int main() { t = 5; return get1() - 5; }
```

```text
===== g++ -std=c++17 -fcommon -c tent1.cpp -o tent1.o && g++ -std=c++17 -fcommon -c tent2.cpp -o tent2.o && g++ tent1.o tent2.o -o ex (cc exit=1) =====
/usr/bin/ld: tent2.o:(.bss+0x0): multiple definition of `t'; tent1.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
===== nm tent1.o (exit=0) =====
0000000000000000 T _Z4get1v
0000000000000000 B t
===== gcc -x c -std=c17 -fcommon -c tent1.cpp -o tent1c.o && gcc -x c -std=c17 -fcommon -c tent2.cpp -o tent2c.o && gcc tent1c.o tent2c.o -o ex && ./ex; echo "run=$?"; nm tent1c.o (exit=0) =====
run=0
0000000000000000 T get1
0000000000000004 C t
```

- ★★★ **같은 두 파일인데 C 로 컴파일하면 `-fcommon` 에서 링크되고(`C t`), C++ 로 컴파일하면 `-fcommon` 을 줘도 깨진다(`B t`).**
- ★★ **C++ 에는 잠정 정의라는 개념이 없다** — `int t;` 는 **그냥 정의**다. 그래서 `-fcommon` 이 붙일 「공용」 자리가 처음부터 없다.
- ★ C 29번 (5)는 C 쪽 **세 컴파일러 × 세 플래그**를 쟀다. 여기서 새로 본 것은 「**`-fcommon` 이 C++ 에서는 아무것도 안 바꾼다**」다.

## 문법 — 형태와 규칙

### 형태

```text
   struct S {
       static int a;                    선언 — 정의는 .cpp 한 곳에   int S::a = 0;
       static inline int b = 0;         C++17 — 선언이자 정의, 헤더에 둬도 하나로 합쳐진다
       static const int c = 7;          값을 알려 주는 선언 — ODR 사용하면  const int S::c;  가 필요
       static constexpr int d = 9;      C++17 부터 암묵 inline — 정의까지 된다
   };
   int& lazy() { static int v = init(); return v; }     처음 부를 때 초기화 · 스레드 안전 가드
   constinit int g = 42;                                 C++20 — 상수 초기화만 받는다
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **컴파일·링크한 소스**로 보였다.

### 규칙

- ★★★ **정적 데이터 멤버의 클래스 밖 정의를 헤더에 두지 않는다** — 포함한 번역 단위마다 정의가 생겨 **`multiple definition`**((1)).
- ★★★ **C++17 이면 `static inline` 으로 헤더에 정의한다** — `nm` 이 `u`/`V` 로 바뀌고 링커가 합친다((1)).
- ★★ **`static constexpr` 는 C++17 부터 따로 정의하지 않는다** — 하면 **폐기 예정 중복**이다((3)).
- ★★★ **`static const`(비`constexpr`)를 참조로 넘기면 C++17 에서도 정의가 필요하다** — `-O2` 는 그 누락을 **숨긴다**((3)).
- ★★★ **다른 번역 단위의 정적 변수로 초기화하지 않는다** — 순서가 미명시다. **함수 지역 `static`** 이나 **`constinit`** 으로 푼다((4)(5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| 헤더에 `int Cfg::count = 0;` + 두 번역 단위 | ★★★ **`multiple definition`** · 판 무관 4 / 4 | (1)(2) |
| C++14 에서 `static inline int count = 0;` | ★★ **경고만** · `cc exit=0` · `-pedantic-errors` 로 에러 1 · 1 | (2) |
| C++14 · `-O0` 에서 `std::max(K::B, x)` | ★★ **`undefined reference`** | (3) |
| C++17 · `-O0` 에서 `std::max(K::A, x)`(`static const`) | ★★ **`undefined reference`** | (3) |
| `constinit int Config::base = read_base();` | ★ **에러**(상수 초기자가 아니다) | (5) |
| C++ 에서 두 파일에 `int t;`(+`-fcommon`) | ★ **`multiple definition`** | (6) |

## 어디서 틀리나

### 1. ★★★ 「헤더에 넣으면 알아서 하나가 된다」

(1)이 반증이다 — **`B` 둘에 `multiple definition`**. 하나로 합쳐지는 것은 **`inline`(`u`/`V`)** 이거나 C 의 **`-fcommon` 잠정 정의(`C`)** 뿐이다.

### 2. ★★★ 「`static const int N = 7;` 은 정의다」

(3)이 반증이다 — **참조로 넘기면 `undefined reference`**. C++17 에서도 그렇다. 암묵 `inline` 은 **`constexpr` 에만** 붙는다.

### 3. ★★★ 「릴리스 빌드가 링크되니 코드는 맞다」

(3)이 반증이다 — **`-O2` 는 24칸 중 12칸 전부 통과**했지만 그중 6칸은 `-O0` 에서 깨지는 **ill-formed** 다. 최적화가 **참조를 지워** 누락을 가렸다.

### 4. ★★★ 「정적 변수는 소스에 적은 순서로 초기화된다」

(4)가 반증이다 — **번역 단위가 둘이면 순서는 링커가 정한다.** 이 판에서는 **링크 명령 순서**가 `42` 와 `0` 을 갈랐다. 한 파일 안에서만 적은 순서다([14번](../14-destructors-and-deterministic-destruction/) (3)).

### 5. ★★ 「두 컴파일러에서 같은 값이 나왔으니 이식성 있다」

(4)가 반증이다 — **두 컴파일러가 같은 링커를 부른다.** 갈리는 축은 컴파일러가 아니라 **링크 순서**다.

### 6. ★★ 「함수 지역 `static` 은 공짜다」

(5)가 반쯤 반증이다 — **가드 바이트 검사와 처음 한 번의 `__cxa_guard_*` 호출**이 붙는다. 시간은 안 쟀다 — **명령이 있다**는 것까지만.

### 7. ★ 「C++17 으로 올렸으니 컴파일러가 낡은 정의를 알려 주겠지」

(3)이 반증이다 — **중복 `constexpr` 정의는 `-Wdeprecated` 없이는 0 · 0**.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「미명시」 칸이 결론을 쥔다** — 정적 초기화 순서다. 그리고 **「진단 불필요 ill-formed」** 가 `-O2` 뒤에 숨는다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **정의가 둘이면 ill-formed**((1)) · **ODR 사용에는 정의가 필요**((3)) · **정적 저장소는 동적 초기화 전 0**((4)) · **함수 지역 `static` 은 처음 지날 때 · 스레드 안전**((5)) | 링커 진단 · 초기화 로그 | ★★★ **ODR 누락을 `-O2` 가 통과시킨다**((3)) |
| **조건부 표준** | 특정 판에서만 | ★★★ **`inline` 변수 · `constexpr` 암묵 `inline` 은 C++17** · **`constinit` 은 C++20** · **중복 `constexpr` 정의는 C++17 부터 폐기 예정** | `-std=c++14`/`c++17` 격자 | ★★ **C++14 의 `inline` 이 경고만 내고 통과**((2)) |
| **구현 정의** | 문서화 의무 | ★★ **`nm` 글자 `u`(g++) 대 `V`(clang)**((1)) · **가드를 `__cxa_guard_*` 로 구현**(Itanium ABI)((5)) · 진단 문구 | `nm` · `-O2 -S` | ★ **글자가 다른데 뜻은 같다** |
| **미명시** | 몇 가지 중 하나 | ★★★ **번역 단위 사이의 동적 초기화 순서**((4)) — 이 판에서는 **링크 명령 순서**를 따랐다(관찰) | 링크 순서 두 판 | ★★★ **어느 도구도 경고하지 않는다** — 로그로만 보인다 |
| **UB** | 아무 일이나 | ★ **이 편의 실험에는 없다** — (4)가 읽은 0 은 UB 가 아니다. 단 **`std::string` 같은 객체를 생성 전에 쓰면 UB** 다 — 이 문서는 **던지지 않았다** | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 링커 / 로그 |
|---|---|---|---|---|
| ★★★ **링크 순서로 `42` 대 `0`** | 미명시 | ★★★ **0건** | ★★★ **0건** | ★★★ 로그 **`읽은 값 0`** |
| ★★★ **ODR 누락 + `-O2`** | 표준(진단 불필요) | **0건** · `cc exit=0` | **0건** · `cc exit=0` | ★★ `-O0` 이면 **`undefined reference`** |
| ★★ **C++14 에서 `inline` 변수** | 조건부 | **warning 2** · `cc exit=0` | **warning 2** · `cc exit=0` | 링크 **O** |
| ★ **C++17 의 중복 `constexpr` 정의** | 조건부 | ★ **0건**(`-Wdeprecated` 면 1) | ★ **0건**(`-Wdeprecated` 면 1) | 링크 O |
| 헤더의 클래스 밖 정의 | 표준 | 0건(컴파일) | 0건(컴파일) | ★ **`multiple definition`** |

- ★★ **이 표의 결론** — ★★★ **정의 위치의 사고는 컴파일러가 아니라 링커가 본다. 그리고 링커도 못 보는 둘(순서 · `-O2` 가 지운 참조)이 가장 위험하다.**

### ★ 종료 코드 0인데 ill-formed — 새 항목 둘

- ★★ **`static inline` 을 `-std=c++14` 로** — 두 컴파일러 다 경고 2 · `cc exit=0` · `-pedantic-errors` 로 에러 1 · 1((2)).
- ★★★ **정의 없이 ODR 사용 + `-O2`** — 두 컴파일러 다 **경고 0 · 링크 O**. **`-pedantic-errors` 로도 안 잡힌다** — 진단이 필요 없는 ill-formed 라 **컴파일러가 볼 의무가 없다.** `-O0` 링크만 잡는다((3)).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 헤더 온리 라이브러리의 정적 멤버(C++17+) | ★★★ **`static inline`** | 번역 단위마다 있어도 하나다((1)) |
| 클래스 상수 | ★★★ **`static constexpr`** | C++17 부터 따로 정의 불필요((3)) |
| C++14 저장소의 클래스 상수 | ★★ **`static constexpr` + `.cpp` 한 곳에 `constexpr int K::B;`** | 참조로 넘기면 깨진다((3)) |
| 다른 파일의 정적 값에 기대는 초기화 | ★★★ **함수 지역 `static`**(「처음 쓸 때 짓기」) | 순서 문제가 없다((5)) |
| 상수로 초기화되는 전역·정적 멤버(C++20) | ★★ **`constinit`** | 동적 초기화를 금지해 순서 문제를 원리상 없앤다((5)) |
| 빌드 검증 | ★★ **`-O0` 링크를 CI 에 한 번은 둔다** | `-O2` 는 ODR 누락을 숨긴다((3)) |

## 핵심 문장

- ★★★ **헤더에 정적 데이터 멤버를 정의하면 포함한 번역 단위마다 `B` 가 생겨 `multiple definition`** — C++17 `static inline` 은 그것을 **g++ `u` · clang++ `V`** 로 바꿔 하나로 합친다.
- ★★★ **C++17 의 암묵 `inline` 은 `constexpr` 정적 멤버에만** — `static const` 는 참조로 넘기면 여전히 `undefined reference` 다.
- ★★★ **`-O2` 는 ODR 누락을 숨긴다** — `-O0` 에서 깨지는 6칸이 `-O2` 에서 **0칸**이었다.
- ★★★ **번역 단위 사이의 정적 초기화 순서는 미명시** — 이 판에서는 **링크 명령 순서**만 바꿔 `42` 가 `0` 이 됐다.
- ★★ **함수 지역 `static` 이 순서 문제를 푼다** — 대가는 **가드 바이트 검사 + 처음 한 번 `__cxa_guard_*`**.
- ★ **C++ 에는 잠정 정의가 없다** — `-fcommon` 을 줘도 `int t;` 는 `B` 다.

## 관련 자료

- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **29번**([`29-scope-and-linkage-static-extern/`](../../../c/syntax/29-scope-and-linkage-static-extern/)) — ★★★ **같은 문제의 C 쪽.** 잠정 정의·`-fcommon`·`nm` 글자·전역 `inline int` 는 거기서 쟀다. 여기는 **클래스 정적 멤버·ODR 사용·초기화 순서**.
- [12번](../12-class-basics-members-access-and-this/) (7) — **정적 멤버 문법.** 「정의를 빠뜨리면 링커 에러가 난다(25번 주제)」라고 이 편을 가리킨 자리다.
- [14번](../14-destructors-and-deterministic-destruction/) (3) — **함수 지역 `static` 은 처음 부를 때 생긴다** · 「번역 단위가 둘이면 순서가 미명시 — 안 던져 봤다」. **이 편 (4)가 그 판을 던졌다.**
- [24번](../24-explicit-and-converting-constructors/) (7) — **`explicit(bool)` 을 C++17 로** — (2)와 같은 「종료 코드 0인데 ill-formed」 집안.
- 목록의 **55번 주제** — **모듈·ODR·헤더 배치.** ODR 일반과 모듈이 이 문제를 어떻게 바꾸나는 거기서.

## 용어 풀이

> **정적 데이터 멤버(static data member)** — 객체마다가 아니라 **클래스에 하나** 있는 데이터 멤버. 클래스 안의 `static int a;` 는 **선언**이다.\
> 예: (1)의 `Cfg::count`.

> **`inline` 변수(inline variable)** — C++17. **여러 번역 단위에 같은 정의가 있어도 하나의 객체**로 합쳐지는 변수.\
> 예: (1)의 `static inline int count = 0;` — `nm` 의 `u`/`V`.

> **ODR 사용(odr-use)** — 변수의 **주소가 필요한** 쓰임(참조로 묶기·`&` 등). ODR 사용되는 변수는 **정의가 정확히 하나** 있어야 한다.\
> 예: (3)의 `std::max(K::B, x)`.

> **정적 초기화 순서 문제(static initialization order fiasco)** — 서로 다른 번역 단위의 정적 변수가 **서로의 값으로 동적 초기화**될 때 순서가 미명시라 생기는 문제.\
> 예: (4)의 `42` 대 `0`.

> **「처음 쓸 때 짓기」(construct on first use)** — 전역 대신 **함수 지역 `static`** 을 돌려주는 함수로 바꿔, 처음 부를 때 초기화되게 하는 관용구.\
> 예: (5)의 `lazy_base()`.

> **`constinit`** — C++20. 변수가 **상수 초기화만** 받도록 강제하는 지정자. 동적 초기화가 필요하면 에러다.\
> 예: (5)의 `constinit int Config::base = read_base();` 가 거부됐다.

> **`nm` 글자** — 오브젝트의 심볼 종류. **`B`**(0 으로 채우는 영역의 정의) · **`u`**(GNU 유일 전역) · **`V`**(약한 객체) · **`U`**(정의되지 않음) · **`C`**(공용, C 의 `-fcommon`).\
> 예: (1)(3)(6).

## 더 들어가면

- **정적 파괴 순서** — 초기화의 역순이다([14번](../14-destructors-and-deterministic-destruction/) (3)). 번역 단위가 둘이면 **파괴 순서 문제**도 같은 모양으로 생긴다 — 이 문서는 던지지 않았다.
- **`std::string` 을 생성 전에 쓰는 판** — (4)를 `int` 가 아니라 **비자명 생성자 타입**으로 하면 UB 가 된다. 그때는 ASan 창이 열린다 — 이 문서는 던지지 않았다.
- **모듈(C++20)** — 헤더 대신 모듈을 쓰면 정의 위치 문제의 모양이 바뀐다. 목록의 **55번 주제**다.
- **`-Wl,--warn-common`·`--no-undefined`** — 링커 쪽 경고 스위치들. 이 문서는 링커 기본값만 봤다.
