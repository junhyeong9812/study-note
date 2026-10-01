# c/syntax/45 — 번역 단위와 링크 오류 읽기: 「**링크 에러는 「이 이름의 정의가 몇 개인가」에 대한 링커의 대답이다 — 문구에서 원인으로 거꾸로 걸어가는 길은 `nm` 이 깐다**」 — 정리 (힌트)

★★★ **본체는 넷째 창 — 링크 결과 + `nm` 이다.** 이 편의 파일은 **전부 `-c` 가 통과한다.** 원인은 링크에서만 드러나고, **어느 파일의 무엇인지**는 `nm` 이 말한다.
★★★ 역추적 격자에서 **링크된 칸 9 / 30** · **gcc 와 clang 이 갈린 행 0 / 10** · **ld.bfd 와 gold 가 갈린 행 0 / 10** — 에러의 **종류**는 판을 안 탔다. 판을 탄 것은 **문구의 모양**과 **`-lm` 의 자리**(드라이버가 넘기는 `--as-needed`)였다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★ 이 편의 파일은 **경고 0 · `-c` 통과** — 그 침묵 자체가 증거다(컴파일러는 한 번역 단위만 본다) | 씀(침묵으로) |
| ② 실행 출력 | ★ 약한 심볼 판의 값(`hook` 이 널인가 · `level()` 이 몇인가) | 씀 |
| ③ sanitizer | — | 부적용(메모리 사고가 없는 주제다) |
| ★★★ ④ **링크 결과 + `nm`** | ★ **본체** — `undefined reference` / `multiple definition` / 성공 · 글자 `U`/`T`/`t`/`w`/`W` · 맹글링된 이름 | 씀 |
| ⑤ 드라이버가 넘긴 링크 명령(`-###`) | ★★ `-lm` 이 드라이버에 따라 갈린 **이유** — `--as-needed` 의 자리 | 씀 |
| 시간 측정 | — | 부적용(링크 속도는 이 편의 주제가 아니다) |
| ★ 제5의 상태 | 「링커가 무엇을 찾다 실패했나」를 **에러 문구로 물으면 이름 하나만** 온다(`area`). **어느 파일이 그 이름을 가졌고 어떤 글자로 가졌나**는 문구에 없다 — **`nm` 으로 바꿔 물어** 파일마다 글자로 받았다 | 창을 바꿔 답함 |

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== g++ --version | sed -n 1p (cc exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== ld --version | sed -n 1p (exit=0) =====
GNU ld (GNU Binutils for Ubuntu) 2.42
```

```text
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
```

★ **두 드라이버가 부르는 ld 는 같다** — `clang` 이 부르는 것도 `/usr/bin/ld`(→ ld.bfd)이고 판도 같다.

```text
===== readlink -f /usr/bin/ld; clang -### s45u.o -o x 2>&1 | tail -n 1 | awk '{print $1}' (exit=0) =====
/usr/bin/x86_64-linux-gnu-ld.bfd
"/usr/bin/ld"
```

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && gcc -Wl,--version s45n.o -o x 2>&1 | grep '^GNU ld'; clang -Wl,--version s45n.o -o x 2>&1 | grep '^GNU ld' (exit=0) =====
GNU ld (GNU Binutils for Ubuntu) 2.42
GNU ld (GNU Binutils for Ubuntu) 2.42
```

★★ **`lld` 는 이 머신에 없다** — 판별 블록 둘. 세 번째 판으로 **gold** 를 썼다.

```text
===== command -v ld.lld lld (exit=1) =====
```

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && clang -fuse-ld=lld s45n.o -o x (cc exit=1) =====
clang: error: invalid linker name in argument '-fuse-ld=lld'
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **역추적 격자 · `-lm` 격자 · `nm` 블록 · 약한 심볼 실행값** | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다 | 링크 에러 문구 | ★ **목적 파일 이름을 고정**했다 — `gcc a.c b.c` 로 한 번에 링크하면 임시 파일(`/tmp/cc….o`)의 이름이 문구에 박혀 **실행마다 흔들린다.** 문구를 싣는 블록은 전부 `-c` 로 `.o` 를 먼저 만들었다 |
| ★ 판에 매인다 | 문구의 **`(.text+0x13)` 오프셋** | 컴파일러·최적화가 바뀌면 움직인다(gcc 는 `+0x13`, clang 은 `+0x1a` — 같은 소스) |

## 한눈에 — 쉽게 말하면

**링커는 「이 이름의 가게가 동네에 몇 곳인가」를 세는 사람이다.** 0곳이면 「그런 가게 없다」, 2곳이면 「두 곳이다」라고 **이름 하나만** 말하고 끝낸다.

- **간판만 있고 가게가 없다** — 선언만 하고 정의를 안 만들었다. → **`undefined reference`**
- **가게는 있는데 문이 안쪽으로만 열린다** — `static` 정의는 **그 파일 사람만** 쓴다. → **`undefined reference` · `t`**
- **가게 이름이 한 글자 다르다** — 링커는 **글자가 같아야** 같은 가게로 본다. → **`undefined reference` · `T total_cuont`**
- **외국어 간판** — C++ 은 이름을 **바꿔 단다**(`_Z3addii`). → **`undefined reference` · 맹글링**
- **동네 명부를 먼저 읽고 나서 손님이 왔다** — 정적 라이브러리는 **그때까지 필요한 것만** 챙긴다. → **라이브러리 순서**
- **같은 간판의 가게가 두 곳** — 헤더에 정의를 두면 include 한 파일마다 가게가 선다. → **`multiple definition`**
- **「있으면 쓰고 없으면 말고」 간판** — 약한 심볼은 **없어도 링크가 되고, 있으면 강한 쪽이 이긴다.** → **`w` · `W`**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 간판만 | 선언 · 정의 없음 | ★★★ `undefined reference` · `nm` 의 **`U` 뿐** |
| 안쪽 문 | 다른 파일의 `static` 정의 | ★★ **`t helper` / `U helper`** — 정의가 **있는데** 못 쓴다 |
| 한 글자 다른 간판 | 이름 오타 | ★★ `T total_cuont` / `U total_count` |
| 외국어 간판 | C++ 로 컴파일한 정의 | ★★★ `T _Z3addii` / `U add` |
| 명부를 먼저 읽음 | `-ls45 s45lm.o` | ★★ 정적 라이브러리를 **앞에** 두면 실패 · 뒤에 두면 성공 |
| 같은 간판 두 곳 | 헤더의 정의 | ★★ `T scale` / `T scale` |
| 있으면 쓰고 | `__attribute__((weak))` | ★★ `w hook` → 링크 성공 · **주소가 널** |

```text
   링크 에러 두 종류가 가리키는 것

   undefined reference to 'X'          multiple definition of 'X'
     = 정의(T)가 0 개로 보였다             = 정의(T)가 2 개 이상이다
            |                                   |
     nm 으로 파일마다 X 를 찾는다           nm 으로 T X 를 가진 파일을 찾는다
            |                                   |
     +------+------+------+------+       헤더에 정의가 있나 (두 파일 모두 T)
     |      |      |      |      |       같은 이름을 두 .c 가 정의했나
    U 뿐   t X   T X'   T _Z..X  T X 가
   (정의   (static (이름   (C++   라이브러리 안에 있는데
    없음)   정의)  오타)   맹글링)  순서 밖
```

- ★★★ **이 주제의 본체는 「컴파일러·링커 구현」 칸** — 표준은 「정의는 정확히 하나」까지만 말하고, **그 규칙을 어떻게 검사하고 어떤 문구로 알리나**는 툴체인의 몫이다.
- ★★ **에러 문구는 이름 하나를 줄 뿐** — 원인은 **`nm` 의 글자**로 가른다. `U` 뿐이면 정의가 없고, `t` 면 숨었고, 이름이 비슷한 `T` 면 오타다.

> **번역 단위(translation unit)** — 전처리가 끝난 `.c` 하나. 컴파일러는 **한 번에 하나만** 본다.\
> 예: `s45s1.c` 와 `s45s2.c` 는 서로의 `static` 을 모른다.

> **`nm`** — 목적 파일의 심볼 표를 찍는 도구. 이름 앞의 한 글자가 **정의가 있나 · 밖에서 보이나**를 말한다.\
> 예: `T api`(정의 · 밖에서 보임) · `t helper`(정의 · 이 파일 전용) · `U helper`(정의 없음 · 밖에서 찾음).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`undefined reference` 와 `multiple definition` 은 각각 어떤 원인들을 가리키고, `nm` 의 어느 글자가 그것을 가르나.**
2. ★★ **소스가 같은데 링크가 갈리는 자리는 어디인가** — 라이브러리 순서 · 드라이버 · 링커 판.
3. ★★ **링크가 「된다」는 것은 무엇을 보장하지 않나** — 약한 심볼과 `static` 사본.

## 동작 방식

### (0) ★ 헤더 배치 — 44번 주제가 이미 잰 것

- ★★ [44번 형제](../44-headers-and-separate-compilation/)의 헤더 배치 격자(헤더 내용 14 × 빌드 5 · 두 번역 단위): **정의 없는 선언은 다섯 빌드 다 `undefined reference` · `nm` 은 `U / U`**, **헤더의 함수 정의는 다섯 빌드 다 `multiple definition` · `T / T`**, **`static` 정의는 성공 · `t / t`**, **`int hv;`(임시 정의)는 gcc 기본에서 `multiple definition` 이고 `-fcommon` 에서만 통과**, **`const int hv = 5;` 는 C 에서 `multiple definition` 이고 C++ 에서 통과**. 그 격자의 끝 줄 — **링크가 깨진 칸 18 / 42 · 세 컴파일러가 갈린 행 0 / 14**.
- ★ **이 편은 그 42칸을 다시 재지 않았다** — 헤더 줄은 (1) 격자의 **2번 줄 하나**로만 두고, **에러를 받아서 원인으로 거꾸로 가는 길**을 본다.

### (1) ★★★ 역추적 격자 — 원인 열 줄 × 링크 세 판

**언제 쓰나** — 링크 에러를 받았는데 **어느 파일의 무엇이 원인인지** 모를 때. ★★★ **이 편의 본체**다.

```c
/* s45u.c */
int area(int w, int h);                 /* 선언 */

int main(void) {
    return area(2, 3) == 6 ? 0 : 1;
}
```

```c
/* s45h.h */
#ifndef S45H_H
#define S45H_H

int scale(int x) { return 10 * x; }

#endif
```

```c
/* s45h1.c */
#include "s45h.h"

int use_one(void) { return scale(1); }
```

```c
/* s45h2.c */
#include "s45h.h"

int use_one(void);

int main(void) { return scale(2) + use_one() == 30 ? 0 : 1; }
```

```c
/* s45s1.c */
static int helper(int x) { return x + 1; }

int api(int x) { return helper(x); }
```

```c
/* s45s2.c */
int helper(int x);

int main(void) { return helper(1) == 2 ? 0 : 1; }
```

```c
/* s45t1.c */
int total_cuont(void) { return 3; }
```

```c
/* s45t2.c */
int total_count(void);

int main(void) { return total_count() == 3 ? 0 : 1; }
```

```cpp
// s45x.cpp
int add(int a, int b) { return a + b; }
```

```c
/* s45xc.c */
int add(int a, int b);

int main(void) { return add(1, 2) == 3 ? 0 : 1; }
```

```c
/* s45l.c */
int lib_value(void) { return 7; }
```

```c
/* s45lm.c */
int lib_value(void);

int main(void) { return lib_value() == 7 ? 0 : 1; }
```

```c
/* s45n.c */
int only_helper(void) { return 0; }
```

```c
/* s45w1.c */
#include <stdio.h>

int hook(void) __attribute__((weak));   /* 약한 선언 */

int main(void) {
    printf("hook 주소가 널인가 = %d\n", hook == NULL);
    printf("hook() = %d\n", hook ? hook() : -1);
    return 0;
}
```

```c
/* s45w3.c */
#include <stdio.h>

__attribute__((weak)) int level(void) { return 1; }   /* 약한 정의 */

int main(void) {
    printf("level() = %d\n", level());
    return 0;
}
```

```c
/* s45w4.c */
int level(void) { return 2; }
```

```text
===== 역추적 격자 — 원인 10 × 링크 3 (+ nm) (exit=0) =====
원인                              	gcc (ld.bfd)	clang (ld.bfd)	gcc -fuse-ld=gold	nm (gcc 로 만든 .o)
1 선언만 있고 정의 없음           	undefined reference	undefined reference	undefined reference	U area
2 헤더에 정의 · 두 파일이 include 	multiple definition	multiple definition	multiple definition	T scale / T scale
3 다른 파일의 static 정의         	undefined reference	undefined reference	undefined reference	t helper / U helper
4 정의 쪽 이름이 한 글자 다름     	undefined reference	undefined reference	undefined reference	T total_cuont / U total_count
5 정의를 C++ 로 컴파일            	undefined reference	undefined reference	undefined reference	T _Z3addii / U add
6 정적 라이브러리를 앞에          	undefined reference	undefined reference	undefined reference	T lib_value / U lib_value
7 정적 라이브러리를 뒤에          	링크 성공	링크 성공	링크 성공	T lib_value / U lib_value
8 main 이 없음                    	undefined reference	undefined reference	undefined reference	(없음)
9 약한 선언 · 정의 없음           	링크 성공	링크 성공	링크 성공	w hook
10 약한 정의 + 강한 정의          	링크 성공	링크 성공	링크 성공	W level / T level
(칸 = 각 파일을 $CC -std=c17 -c 로 따로 만든 뒤 링크한 결과 · C++ 파일은 g++/clang++ -std=c++17 -c · 정적 라이브러리 = ar rcs libs45.a s45l.o)
링크된 칸 9 / 30
gcc 와 clang 이 갈린 행 0 / 10
ld.bfd 와 gold 가 갈린 행 0 / 10
```

그림 해설 (한 단계씩):

- ★★★ **링크된 칸 9 / 30** — 성공한 것은 **7 · 9 · 10 줄**뿐이다. 나머지 일곱 줄은 **세 판 전부** 깨졌다.
- ★★★ **`undefined reference` 여섯 줄(1 · 3 · 4 · 5 · 6 · 8)은 문구의 모양이 같다** — 「이 이름을 못 찾았다」. **원인은 `nm` 칸이 가른다.**
  - **1 — `U area` 하나뿐.** 정의가 **어느 파일에도 없다.**
  - **3 — `t helper` / `U helper`.** 정의가 **있다.** 다만 소문자 `t` — **이 파일 전용**이라 링커가 다른 파일의 `U` 에 이어 주지 않는다.
  - **4 — `T total_cuont` / `U total_count`.** 정의가 **밖에서 보이게** 있는데 **이름이 다르다.** 링커는 비슷한 이름을 찾아 주지 않는다.
  - **5 — `T _Z3addii` / `U add`.** 정의가 **밖에서 보이게** 있는데 **C++ 이 이름을 바꿔 달았다**((3)).
  - **6 — `T lib_value` / `U lib_value`.** 정의도 이름도 맞는데 **라이브러리가 앞에** 있었다. **같은 `nm` 칸의 7 줄은 성공**한다 — **`nm` 으로는 6 과 7 이 안 갈린다.** 순서는 링크 명령에만 있다((4)).
  - **8 — `main` 이 (없음).** 찾는 쪽이 **내 파일이 아니라 C 런타임의 `_start`** 다((5)).
- ★★ **`multiple definition` 은 2 줄 하나** — `T scale / T scale`. **정의가 둘**이라는 뜻이고 원인 후보가 훨씬 좁다(헤더 정의 · 같은 이름을 두 `.c` 가 정의).
- ★★ **9 · 10 줄은 성공하지만 조용한 대가가 있다**((6)).
- ★★★ **gcc 와 clang 이 갈린 행 0 / 10 · ld.bfd 와 gold 가 갈린 행 0 / 10** — **에러의 종류**는 드라이버도 링커도 안 탔다. 다른 것은 **문구의 모양**이다((2)).

### (2) ★★ 같은 에러, 세 판의 문구

**언제 쓰나** — CI 로그와 내 터미널의 문구가 달라 **같은 에러인지** 헷갈릴 때.

```text
===== gcc -std=c17 -c s45u.c -o s45u.o && gcc s45u.o -o x (cc exit=1) =====
/usr/bin/ld: s45u.o: in function `main':
s45u.c:(.text+0x13): undefined reference to `area'
collect2: error: ld returned 1 exit status
```

```text
===== clang -std=c17 -c s45u.c -o s45u.o && clang s45u.o -o x (cc exit=1) =====
/usr/bin/ld: s45u.o: in function `main':
s45u.c:(.text+0x1a): undefined reference to `area'
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== gcc -std=c17 -c s45u.c -o s45u.o && gcc -fuse-ld=gold s45u.o -o x (cc exit=1) =====
s45u.o:s45u.c:function main:(.text+0x13): error: undefined reference to 'area'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45h1.c -o s45h1.o && gcc -std=c17 -c s45h2.c -o s45h2.o && gcc s45h1.o s45h2.o -o x (cc exit=1) =====
/usr/bin/ld: s45h2.o: in function `scale':
s45h2.c:(.text+0x0): multiple definition of `scale'; s45h1.o:s45h1.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45h1.c -o s45h1.o && gcc -std=c17 -c s45h2.c -o s45h2.o && gcc -fuse-ld=gold s45h1.o s45h2.o -o x (cc exit=1) =====
/usr/bin/ld.gold: error: s45h2.o: multiple definition of 'scale'
/usr/bin/ld.gold: s45h1.o: previous definition here
collect2: error: ld returned 1 exit status
```

- ★★★ **ld.bfd 의 두 줄 문법** — 첫 줄 `/usr/bin/ld: s45u.o: in function 'main':` 이 **부른 쪽 함수**를, 둘째 줄 `s45u.c:(.text+0x13): undefined reference to 'area'` 가 **부른 자리와 찾은 이름**을 말한다. ★ **부른 쪽이지 정의 쪽이 아니다** — 정의는 없으니 가리킬 수가 없다.
- ★★ **마지막 줄은 링커가 아니라 드라이버가 찍는다** — gcc 는 `collect2: error: ld returned 1 exit status`, clang 은 `clang: error: linker command failed with exit code 1 (use -v to see invocation)`. **위의 `/usr/bin/ld:` 줄은 두 판이 글자까지 같다**(오프셋만 `+0x13` 대 `+0x1a`).
- ★★ **gold 는 한 줄 문법** — `s45u.o:s45u.c:function main:(.text+0x13): error: undefined reference to 'area'`. `multiple definition` 은 **`previous definition here`** 로 앞선 정의를 가리킨다(ld.bfd 는 `first defined here`).
- ★★ **`multiple definition` 은 두 파일을 다 말한다** — `s45h2.o` 의 정의가 **`s45h1.o` 에서 먼저 정의됐다**고. 원인 파일이 문구에 **다 나오는** 유일한 경우다.

### (3) ★★ `nm` 으로 원인을 가르는 세 줄 — `static` · 오타 · C++

**언제 쓰나** — `undefined reference` 인데 「분명히 정의했다」고 느낄 때.

```text
===== gcc -std=c17 -c s45s1.c -o s45s1.o && gcc -std=c17 -c s45s2.c -o s45s2.o && gcc s45s1.o s45s2.o -o x (cc exit=1) =====
/usr/bin/ld: s45s2.o: in function `main':
s45s2.c:(.text+0xe): undefined reference to `helper'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45s1.c -o s45s1.o && gcc -std=c17 -c s45s2.c -o s45s2.o && nm s45s1.o s45s2.o (exit=0) =====

s45s1.o:
0000000000000013 T api
0000000000000000 t helper

s45s2.o:
                 U helper
0000000000000000 T main
```

```text
===== gcc -std=c17 -c s45t1.c -o s45t1.o && gcc -std=c17 -c s45t2.c -o s45t2.o && gcc s45t1.o s45t2.o -o x (cc exit=1) =====
/usr/bin/ld: s45t2.o: in function `main':
s45t2.c:(.text+0x9): undefined reference to `total_count'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45t1.c -o s45t1.o && gcc -std=c17 -c s45t2.c -o s45t2.o && nm s45t1.o s45t2.o (exit=0) =====

s45t1.o:
0000000000000000 T total_cuont

s45t2.o:
0000000000000000 T main
                 U total_count
```

```text
===== g++ -std=c++17 -c s45x.cpp -o s45x.o && gcc -std=c17 -c s45xc.c -o s45xc.o && gcc s45x.o s45xc.o -o x (cc exit=1) =====
/usr/bin/ld: s45xc.o: in function `main':
s45xc.c:(.text+0x13): undefined reference to `add'
collect2: error: ld returned 1 exit status
```

```text
===== g++ -std=c++17 -c s45x.cpp -o s45x.o && nm s45x.o && nm -C s45x.o (exit=0) =====
0000000000000000 T _Z3addii
0000000000000000 T add(int, int)
```

```cpp
// s45xe.cpp
extern "C" int add(int a, int b) { return a + b; }
```

```text
===== g++ -std=c++17 -c s45xe.cpp -o s45xe.o && gcc -std=c17 -c s45xc.c -o s45xc.o && gcc s45xe.o s45xc.o -o x && ./x && nm s45xe.o (exit=0) =====
0000000000000000 T add
```

- ★★★ **문구 셋은 모양이 같고 `nm` 이 셋 다 다르다** — `t helper`(숨은 정의) · `T total_cuont`(다른 이름) · `T _Z3addii`(바뀐 이름).
- ★★ **`static` 정의의 `t`** — [29번 형제](../29-scope-and-linkage-static-extern/)의 「파일 스코프 `static` 은 내부 링크」가 목적 파일에서 **소문자 한 글자**로 보인다.
- ★★★ **C++ 의 이름 바꾸기(맹글링)** — `add(int, int)` 가 `_Z3addii` 가 된다(`nm -C` 가 되돌려 읽어 준다). **인자 타입이 이름에 박히므로** 오버로드가 가능하고, 대가로 **C 쪽의 `add` 와 이어지지 않는다.** `extern "C"` 를 **정의 쪽(C++ 파일)** 에 붙이면 `T add` 가 되어 링크되고 실행이 `exit=0` 으로 끝난다.
- ★ 템플릿 인스턴스화가 만드는 C++ 쪽 링크 에러는 [C++ 35 — 인스턴스화 · 헤더 배치 · 에러 읽기](../../../cpp/syntax/35-instantiation-header-placement-and-reading-errors/)가 정본이다.

### (4) ★★★ 순서 — 정적 라이브러리와 `-lm`

**언제 쓰나** — 「같은 명령인데 인자 순서만 바꿨더니 깨졌다」.

```text
===== gcc -std=c17 -c s45l.c -o s45l.o && ar rcs libs45.a s45l.o && gcc -std=c17 -c s45lm.c -o s45lm.o && gcc -L. -ls45 s45lm.o -o x (cc exit=1) =====
/usr/bin/ld: s45lm.o: in function `main':
s45lm.c:(.text+0x9): undefined reference to `lib_value'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45l.c -o s45l.o && ar rcs libs45.a s45l.o && gcc -std=c17 -c s45lm.c -o s45lm.o && clang -L. -ls45 s45lm.o -o x (cc exit=1) =====
/usr/bin/ld: s45lm.o: in function `main':
s45lm.c:(.text+0x9): undefined reference to `lib_value'
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
   ld 는 명령줄을 왼쪽에서 오른쪽으로 한 번 훑는다 (정적 라이브러리 .a)

   -L. -ls45 s45lm.o            s45lm.o -L. -ls45
   ----------------             ----------------
   libs45.a 를 연다              s45lm.o 를 읽는다 -> lib_value 가 필요하다(U)
   지금 필요한 것? 없다          libs45.a 를 연다
   -> 아무것도 안 꺼낸다         -> s45l.o 를 꺼낸다 (T lib_value)
   s45lm.o 를 읽는다 -> U        끝 — 전부 풀렸다
   끝 — lib_value 가 안 풀렸다
```

- ★★★ **정적 라이브러리를 앞에 두면 두 드라이버 다 실패** — ld 는 `.a` 를 만났을 때 **그때까지 풀리지 않은 이름**만 꺼낸다. 뒤에 오는 파일의 필요는 **이미 지나간** 라이브러리가 못 채운다.

공유 라이브러리 쪽 — `libm` 의 `cos` 를 부르는 파일 하나로 `-lm` 의 자리를 바꾼다.

```c
/* s45m.c */
#include <math.h>
#include <stdio.h>

int main(int argc, char **argv) {
    (void)argv;
    printf("cos(%d) = %.3f\n", argc, cos((double)argc));
    return 0;
}
```

```text
===== -lm 의 자리 — 드라이버 2 × 순서 2 (공유 라이브러리 libm) (exit=0) =====
드라이버	s45m.c -lm	-lm s45m.c
gcc     	링크 성공	undefined reference
clang   	링크 성공	링크 성공
(칸 = $CC -std=c17 -c s45m.c 뒤 $CC s45m.o -lm / $CC -lm s45m.o 의 링크 결과)
링크된 칸 3 / 4
```

```text
===== gcc -std=c17 -c s45m.c -o s45m.o && gcc -lm s45m.o -o x (cc exit=1) =====
/usr/bin/ld: s45m.o: in function `main':
s45m.c:(.text+0x27): undefined reference to `cos'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -### -lm s45m.o -o x 2>&1 | grep collect2 | tr ' ' '\n' | grep -n -E '^-lm$|^s45m.o$|as-needed' (exit=0) =====
17:--as-needed
38:-lm
39:s45m.o
42:--as-needed
48:--as-needed
```

```text
===== clang -### -lm s45m.o -o x 2>&1 | tail -n 1 | tr ' ' '\n' | grep -n -E '"-lm"|"s45m.o"|as-needed' (exit=0) =====
26:"-lm"
27:"s45m.o"
29:"--as-needed"
31:"--no-as-needed"
34:"--as-needed"
36:"--no-as-needed"
```

- ★★★ **공유 라이브러리 `libm` 에서는 드라이버가 갈렸다** — gcc 는 `-lm s45m.o` 에서 **`undefined reference to 'cos'`**, clang 은 **두 순서 다 성공.**
- ★★★ **이유는 ld 가 아니라 드라이버가 넘긴 옵션**이다 — Ubuntu 의 gcc 는 **17 번째 인자로 `--as-needed` 를 `-lm`(38 번째)보다 앞에** 넘긴다. `--as-needed` 아래의 공유 라이브러리는 「**그때까지 필요한 게 있을 때만**」 남는다 — 정적 라이브러리와 **같은 모양의 순서 규칙**이 공유 라이브러리에 생긴다. clang 은 `--as-needed` 를 **`-lm`(26 번째) 뒤**(29 번째 · `libgcc` 둘레)에만 넘긴다 — `-lm` 은 **순서와 무관하게** 남는다.
- ★★ **그래서 「ld 는 순서를 본다」는 반쪽이다** — **정적 라이브러리에서는 항상**, **공유 라이브러리에서는 `--as-needed` 가 켜진 구간에서만** 순서가 결과를 바꾼다. 그 스위치를 누가 켜느냐는 **배포판의 드라이버 설정**이다.
- ★ **규칙은 하나로 충분하다** — **`-l` 은 그것을 쓰는 목적 파일보다 뒤에.** 이러면 두 드라이버 · 두 종류의 라이브러리에서 전부 통과한다(격자의 `s45m.c -lm` 열 · 7 번 줄).

### (5) ★★ `main` 이 없다 — 찾는 쪽이 내 파일이 아니다

**언제 쓰나** — 라이브러리용 파일을 실행 파일로 링크했을 때.

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && gcc s45n.o -o x (cc exit=1) =====
/usr/bin/ld: /usr/lib/gcc/x86_64-linux-gnu/13/../../../x86_64-linux-gnu/Scrt1.o: in function `_start':
(.text+0x1b): undefined reference to `main'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && nm s45n.o && nm /usr/lib/x86_64-linux-gnu/Scrt1.o (exit=0) =====
0000000000000000 T only_helper
                 U _GLOBAL_OFFSET_TABLE_
0000000000000000 R _IO_stdin_used
0000000000000000 r __abi_tag
0000000000000000 D __data_start
                 U __libc_start_main
0000000000000000 T _start
0000000000000000 W data_start
                 U main
```

- ★★ **에러가 가리키는 것은 `Scrt1.o` 의 `_start`** — 내 소스에는 `main` 을 부르는 줄이 없다. **C 런타임의 시작 코드가 `U main`** 을 들고 들어온다(`nm Scrt1.o` 의 마지막 줄).
- ★ **「내가 안 부른 이름」의 `undefined reference`** 는 **드라이버가 끼워 넣은 목적 파일**을 의심한다 — 링크 명령은 `gcc -###` 로 보인다((4)).

### (6) ★★ 약한 심볼 — 링크는 되는데

**언제 쓰나** — 「있으면 쓰고 없으면 말고」 훅, 또는 **라이브러리의 기본 구현을 덮어쓰는** 판.

```c
/* s45w2.c */
int hook(void) { return 5; }
```

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && gcc s45w1.o -o x ; ./x (cc exit=0 · run exit=0) =====
hook 주소가 널인가 = 1
hook() = -1
```

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && nm s45w1.o (exit=0) =====
                 U _GLOBAL_OFFSET_TABLE_
                 w hook
0000000000000000 T main
                 U printf
```

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && gcc -std=c17 -c s45w2.c -o s45w2.o && gcc s45w1.o s45w2.o -o x ; ./x (cc exit=0 · run exit=0) =====
hook 주소가 널인가 = 0
hook() = 5
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc s45w3.o -o x ; ./x (cc exit=0 · run exit=0) =====
level() = 1
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc -std=c17 -c s45w4.c -o s45w4.o && gcc s45w3.o s45w4.o -o x ; ./x (cc exit=0 · run exit=0) =====
level() = 2
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc -std=c17 -c s45w4.c -o s45w4.o && nm s45w3.o s45w4.o (exit=0) =====

s45w3.o:
0000000000000000 W level
000000000000000f T main
                 U printf

s45w4.o:
0000000000000000 T level
```

- ★★★ **약한 선언(`w hook`)은 정의가 없어도 링크된다** — 대신 **`hook` 의 주소가 널**이다(`hook 주소가 널인가 = 1`). 널 검사 없이 부르면 **널 함수 포인터 호출**이다 — 이 소스는 `hook ? hook() : -1` 로 막았다.
- ★★ **강한 정의가 들어오면 그쪽이 쓰인다** — `s45w2.o` 를 더하면 `hook() = 5`.
- ★★★ **약한 정의(`W level`) + 강한 정의(`T level`)는 `multiple definition` 이 아니다** — 강한 쪽이 이긴다(`level() = 2`). 혼자면 약한 정의가 쓰인다(`level() = 1`).
- ★★ **「링크가 됐다」가 「내 정의가 쓰였다」가 아니다** — 어느 정의가 이겼는지는 **실행값이나 `nm` 으로만** 보인다. 링커는 이 판에서 **아무 말도 안 했다**(경고 0 · `cc exit=0`).
- ★ **`__attribute__((weak))` 는 GNU 확장**이다 — ISO C 에 약한 심볼은 없다.

## 문법 — 형태와 규칙

### 형태 — 에러 문구에서 원인으로

★★★ **이 편의 산출물은 이 표다.** 문구를 받으면 **왼쪽에서 오른쪽으로** 읽는다.

| 문구(ld.bfd) | 먼저 볼 것 | `nm` 명령 | 그 글자가 말하는 원인 |
|---|---|---|---|
| `undefined reference to 'X'` | ★★★ **X 를 정의한 파일이 링크 명령에 있나** | `nm *.o \| grep X` | 아무 데도 `T X` 가 없고 `U X` 만 → **정의 없음**(1) |
| 같음 | ★★ 정의한 파일의 글자가 소문자인가 | `nm 정의파일.o \| grep X` | **`t X`** → 그 정의는 **`static`**(3) |
| 같음 | ★★ 비슷한 이름의 `T` 가 있나 | `nm 정의파일.o` | **`T X'`**(한 글자 다름) → **오타**(4) |
| 같음 | ★★ `_Z` 로 시작하는 이름이 있나 | `nm -C 정의파일.o` | **`T _Z…X…`** → **C++ 로 컴파일됨** · `extern "C"`(5) |
| 같음 | ★★ `T X` 가 **라이브러리 안에** 있나 | `nm libfoo.a \| grep X` | 있는데 실패 → **링크 명령의 순서**(6) · `-###` 로 `--as-needed` |
| `undefined reference to 'main'` · `_start` 에서 | ★ 실행 파일로 링크할 파일인가 | `nm 내파일.o \| grep main` | 없음 → **`main` 이 없는 파일**(8) |
| `multiple definition of 'X'` | ★★★ **두 파일 이름이 문구에 다 있다** | `nm 두파일.o \| grep X` | `T X / T X` → **헤더의 정의** 또는 **같은 이름 두 정의**(2) |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 선언만 하고 정의 안 함 | 컴파일 경고 0 · **링크 실패** | ★★ 표준(정의가 정확히 하나여야) — 링커가 잡음 | (1) |
| 헤더에 함수 정의 | 컴파일 경고 0 · **`multiple definition`** | ★★ 표준(정의가 둘) — 링커가 잡음 | (1) · [44번 형제](../44-headers-and-separate-compilation/) |
| 다른 파일의 `static` 함수를 선언해 부름 | 컴파일 경고 0 · **링크 실패** | ★★ 표준(내부 링크는 다른 번역 단위에서 안 보인다) | (3) |
| C 에서 C++ 정의를 부름(`extern "C"` 없음) | **링크 실패** | ★★ C++ 의 이름 규칙 · 툴체인 | (3) |
| `-l` 을 목적 파일 **앞에** | 정적 라이브러리는 **항상 실패** · `libm` 은 **gcc(Ubuntu)만 실패** | ★★ 링커 구현 · **드라이버 설정** | (4) |
| 약한 선언을 널 검사 없이 호출 | 경고 0 · 링크 성공 · **널 함수 포인터 호출** | ★ GNU 확장 | (6) |

### 규칙 불릿

- ★★★ **컴파일러는 한 번역 단위만 본다** — 「정의가 몇 개인가」는 **링커만** 안다. 그래서 이 편의 사고는 **전부 `-c` 를 통과**한다.
- ★★★ **`undefined reference` 는 「정의가 0 개로 보였다」** — 없음 · 숨음(`t`) · 다른 이름 · 바뀐 이름 · 순서 밖 · 런타임이 찾는 `main`.
- ★★ **`multiple definition` 은 「정의가 둘」** — 문구에 **두 파일이 다 나온다.**
- ★★ **`-l` 은 쓰는 쪽 뒤에** — 정적 라이브러리는 항상, 공유 라이브러리는 `--as-needed` 아래에서 순서를 탄다.
- ★ **링크 문구를 로그로 남길 때는 `-c` 로 목적 파일 이름을 고정**하라 — 한 번에 링크하면 `/tmp/cc….o` 가 박힌다.

## 어디서 틀리나

### 1. ★★★ 「정의했는데 `undefined reference` 라니 링커가 틀렸다」

**정의가 있는 줄이 셋**이었다 — `static`(`t`) · 오타(`T total_cuont`) · C++(`T _Z3addii`)((3)). 링커는 **글자가 같고 밖에서 보이는** 정의만 센다.

### 2. ★★★ 「에러가 가리키는 파일을 고치면 된다」

`undefined reference` 가 가리키는 것은 **부른 쪽**이다(`s45s2.o: in function 'main'`). **고칠 곳은 대개 정의 쪽**이다((2)).

### 3. ★★ 「clang 에서 되던 빌드가 gcc 에서 깨졌다 — 컴파일러 버그」

`-lm` 의 자리 하나가 **드라이버의 `--as-needed`** 때문에 갈렸다((4)). **링크 명령을 `-###` 로 펼쳐 보면** 보인다.

### 4. ★★ 「링크가 됐으니 내 함수가 불린다」

약한 정의 + 강한 정의는 **말없이 강한 쪽**을 썼다((6)). 약한 선언은 **정의가 없어도** 링크됐다.

### 5. ★ 「`main` 을 부르지도 않았는데 왜 `main` 을 찾나」

찾는 쪽은 **`Scrt1.o` 의 `_start`** 다((5)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「컴파일러·링커 구현」 칸이 본체**다 — 표준은 「정의는 하나」까지만 말하고, **문구 · 글자 · 순서 규칙 · 약한 심볼은 전부 툴체인**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★ **표준** | 어느 구현에서도 같다 | ★★ **외부 링크 식별자는 정의가 정확히 하나** · 내부 링크(`static`)는 다른 번역 단위에서 안 보인다 · 호스트 환경의 프로그램은 **`main` 을 가져야 한다** | 격자 1 · 2 · 3 · 8 줄 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **외부 이름의 유효 글자 수**(표준은 **앞 31 글자** 를 최소치로 둔다 — 이 판은 앞 7 글자가 같은 `total_count` 와 `total_cuont` 를 **다른 이름**으로 봤다) | 4 줄 |
| ★★★ **컴파일러·링커 구현** | 도구의 선택 | ★★★ **에러 문구 두 모양**(ld.bfd 두 줄 · gold 한 줄) · 드라이버의 끝 줄(`collect2` · `clang: error`) · **`nm` 의 글자** · 정적 라이브러리를 한 번 훑는 순서 규칙 · **Ubuntu gcc 의 `--as-needed`** · **약한 심볼**(GNU 확장) · C++ 맹글링(Itanium C++ ABI) | 격자 · `-###` · `nm` |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음(이 편이 던진 것 중에는)** | — |
| ★★ **UB** | 아무 일이나 | ★★ **정의가 없거나 둘인 프로그램은 표준상 규칙 위반**이다 — 이 판은 **링커가 전부 에러로 잡았다**(9 / 30 의 나머지). ★ 약한 선언을 널 검사 없이 부르면 **널 함수 포인터 호출** | 격자 · (6) |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★ **표준** | ★★★ **컴파일 단계는 전부 침묵** — 격자의 파일은 **전부 `-c` 가 통과**했다. 정의의 개수는 **링커만** 센다 |
| ★★★ **컴파일러·링커 구현** | ★★ **에러 문구는 부른 쪽만 말한다** — 정의가 `static` 인지 · 이름이 비슷한지 · 맹글링됐는지는 **`nm` 을 열어야** 보인다 · ★★ **`--as-needed` 는 아무 말 없이** `-lm` 을 버렸다 · ★★ **약한 정의가 졌다는 경고가 없다** |
| ★★ **UB** | ★ 약한 선언의 **널 주소**는 링크가 말하지 않는다 — 실행해야 안다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **링크 에러는 문구가 아니라 `nm` 으로 읽는다** — 문구는 이름 하나, `nm` 은 파일마다 글자.
  - ★★ **에러의 종류는 판을 안 탔다(0 / 10 · 0 / 10)** — 판을 탄 것은 **문구의 모양**과 **드라이버가 넘긴 옵션**이다.
  - ★★ **링크 성공은 「정의가 하나로 정해졌다」이지 「내가 원한 정의다」가 아니다** — 약한 심볼((6)).

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 링크 에러의 원인 찾기 | ★★★ **`nm` 으로 파일마다 그 이름의 글자** | 문구의 파일만 고치기 |
| 로그에 남길 링크 문구 | ★ **`-c` 로 목적 파일을 고정**한 뒤 링크 | 한 번에 `gcc a.c b.c`(임시 이름이 박힌다) |
| 라이브러리 링크 | ★★ **`-l` 을 쓰는 쪽 뒤에** | 드라이버마다 다른 `--as-needed` 에 기대기 |
| C 에서 C++ 함수 부르기 | ★★ **정의 쪽에 `extern "C"`** | C 쪽에서 맹글링된 이름을 흉내 내기 |
| 선택적 훅 | ★ 약한 선언 + **널 검사** | 널 검사 없는 호출 |
| 헤더에 둘 것 | ★★ **선언만**(정의는 한 `.c`) — [44번 형제](../44-headers-and-separate-compilation/) | 헤더의 함수 정의 |

판단 규칙 두 줄.

- ★★★ **`undefined reference` 를 받으면 「정의가 어디 있고 무슨 글자인가」를 먼저 묻는다** — `nm` 한 줄이 여섯 원인을 가른다.
- ★★ **`multiple definition` 을 받으면 문구의 두 파일이 같은 헤더를 include 했나를 본다.**

## 핵심 문장

- ★★★ **역추적 격자에서 링크된 칸 9 / 30 — 실패한 일곱 줄은 세 판 전부에서 같은 종류의 에러였다(gcc/clang 0 / 10 · bfd/gold 0 / 10).**
- ★★★ **`undefined reference` 여섯 줄은 문구가 같고 `nm` 이 다르다 — `U` 뿐 · `t` · 비슷한 `T` · `_Z` 로 시작하는 `T` · 라이브러리 안의 `T` · `_start` 의 `U main`.**
- ★★ **`multiple definition` 은 문구에 두 파일이 다 나온다 — `T scale / T scale`.**
- ★★★ **정적 라이브러리를 앞에 두면 두 드라이버 다 실패했고, `-lm` 을 앞에 두면 gcc 만 실패했다 — Ubuntu gcc 가 `--as-needed` 를 `-lm` 앞에 넘기기 때문이다.**
- ★★ **약한 선언은 정의 없이 링크되고 주소가 널이다 — 약한 정의는 강한 정의에게 말없이 진다.**
- ★ **두 드라이버가 부르는 ld 는 같은 판(2.42)이고, `lld` 는 이 머신에 없다.**

## 관련 자료

- [44번 형제](../44-headers-and-separate-compilation/)(헤더와 분할 컴파일) — ★★★ **선행.** 헤더 배치 격자(14 × 5)의 정본. 이 편은 그 에러를 **받는 쪽**이다.
- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★★ `static`/`extern` 링크 규칙과 `nm` 의 `U`/`T`/`t` 의 정본.
- [39번 형제 — `inline` 과 C 의 인라인 규칙](../39-inline-and-c-inline-rules/) — ★★ `inline` 이 만드는 `undefined reference` / `multiple definition` 은 거기.
- [34번 형제 — 함수 선언·정의·프로토타입](../34-function-declarations-definitions-and-prototypes/) — ★ 선언과 정의의 구분.
- [C++ 35 — 인스턴스화 · 헤더 배치 · 에러 읽기](../../../cpp/syntax/35-instantiation-header-placement-and-reading-errors/) — ★ C++ 쪽의 링크 에러(템플릿).
- [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/) — ★ 링커 일반(재배치 · 심볼 해석)은 거기, 여기는 **C 의 링크 에러를 거꾸로 읽는 법**.

## 용어 풀이

> **외부 링크 / 내부 링크** — 이름이 **다른 번역 단위에서도 같은 것을 가리키나**(외부) / **이 번역 단위 안에서만**인가(내부 — `static`).\
> 예: `int api(int)` 는 외부, `static int helper(int)` 는 내부.

> **`nm` 의 `U` · `T` · `t` · `w` · `W`** — 정의 없음(밖에서 찾음) · 텍스트 정의(밖에서 보임) · 텍스트 정의(이 파일 전용) · 약한 미정의 · 약한 정의.\
> 예: `w hook` 은 「없어도 된다」, `W level` 은 「강한 정의가 오면 진다」.

> **맹글링(name mangling)** — C++ 컴파일러가 함수 이름에 **인자 타입을 박아** 목적 파일의 이름을 만드는 것.\
> 예: `add(int, int)` → `_Z3addii`. `nm -C` 가 되돌려 읽는다.

> **`--as-needed`** — 뒤따르는 공유 라이브러리를 **그때까지 필요한 게 있을 때만** 남기라는 ld 옵션.\
> 예: Ubuntu gcc 는 이것을 `-lm` 앞에 넘겨 `gcc -lm s45m.o` 를 깨뜨렸다.

> **약한 심볼(weak symbol)** — 정의가 없어도 링크되고(주소가 널), 강한 정의가 있으면 **말없이 지는** 심볼. GNU 확장 `__attribute__((weak))`.\
> 예: `int hook(void) __attribute__((weak));`.

> **`Scrt1.o` 와 `_start`** — 드라이버가 실행 파일에 끼워 넣는 C 런타임 시작 코드. `_start` 가 `main` 을 부른다.\
> 예: `main` 이 없으면 에러가 `Scrt1.o: in function '_start'` 를 가리킨다.

## 더 들어가면

- ★★ **정적 라이브러리의 순환 의존** — `-Wl,--start-group … --end-group` 이 `.a` 를 여러 번 훑게 한다. ★ **던지지 않았다.**
- ★ **`-Wl,--trace-symbol=X`** — 링커가 X 를 어느 파일에서 정의·참조로 봤나를 직접 말해 준다. ★ **던지지 않았다.**
- ★ **`lld` 의 문구** — 이 머신에 없어 **못 쟀다**(판별 블록).
- ★ **공유 라이브러리를 만드는 판(`-shared`)** — 정의 없는 이름이 **링크 시점이 아니라 실행 시점**에 깨질 수 있다. ★ **던지지 않았다.**

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 외부 정의 절 — 「**외부 링크로 선언된 식별자가 식에 쓰이면 프로그램 전체 어딘가에 그 외부 정의가 정확히 하나 있어야 하고, 안 쓰이면 하나를 넘으면 안 된다**」, 번역 한계 절 — 「**외부 식별자는 앞 31 글자까지 구분**」(최소치)를 **본문에서 직접 찾아 읽었다**).
★★ **표준이 말하는 것은 「외부 링크 식별자가 식에 쓰이면 프로그램 전체에 그 정의가 정확히 하나 있어야 한다」는 규칙까지다.** 링커 · 목적 파일 · `nm` 의 글자 · 에러 문구 · 라이브러리 순서는 **전부 표준 밖**(툴체인)이다 — 이 편의 본문 대부분이 그 칸이다.
★ **표준 조항 번호는 인용하지 않는다.** 링크 결과 · `nm` 글자 · 문구는 **전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
★★★ **본체는 역추적 격자다** — 원인 10 줄 × 링크 3 판(gcc · clang · `gcc -fuse-ld=gold`) + 줄마다 `nm` 증거.\
★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
★★★ **경계** — **헤더에 무엇을 두면 깨지나**(헤더 내용 14 × 빌드 5 — 정의 없는 선언 · 헤더 정의 · `static` · 임시 정의와 `-fcommon` · `const`)는 [44번 형제](../44-headers-and-separate-compilation/)가 **이미 쟀다.** 이 편은 그 격자를 **다시 재지 않고**, 에러를 **받는 쪽**에서 원인으로 **거꾸로 걷는 법**만 다룬다(헤더 줄은 격자에 **한 줄**만 둔다).\
★ **`inline` 의 링크**는 [39번 형제](../39-inline-and-c-inline-rules/), **`static`/`extern` 링크 규칙 자체**는 [29번 형제](../29-scope-and-linkage-static-extern/), **선언과 정의의 구분**은 [34번 형제](../34-function-declarations-definitions-and-prototypes/)가 정본이다. **링커 일반**(재배치·심볼 해석 알고리즘)은 [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/) 이 정본이다.
선행 — [44번 형제](../44-headers-and-separate-compilation/) · [29번 형제](../29-scope-and-linkage-static-extern/) · [34번 형제](../34-function-declarations-definitions-and-prototypes/).
