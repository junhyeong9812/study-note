# c/syntax/44 — 헤더와 분할 컴파일: 「**헤더는 include 한 모든 번역 단위에 그대로 복사된다 — 그래서 헤더에는 복사돼도 정의가 하나로 남는 것만 둔다**」 — 정리 (힌트)

★★★ **본체는 넷째 창 — 링크 결과 + `nm` 이다.** 컴파일은 모든 칸이 통과한다. **링크에서만** 「정의가 둘」·「정의가 없다」가 갈린다.
★★★ 그 격자에서 **링크가 깨진 칸 18 / 42**(gcc · gcc-12 · clang) — **세 컴파일러가 갈린 행은 0 / 14**. 갈린 것은 **플래그**(`-fcommon` 이 1행을 살린다)와 **언어**(C++ 가 `const` 1행을 살린다)다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★★ 재정의 에러(guard 없음 · `#pragma once` 사본) · 순환 include 의 불완전 타입 · 쓰지 않은 `static` 함수 경고 | 씀 |
| ② 실행 출력 | ★★ 헤더의 `static` 이 **번역 단위마다 사본**이라는 것 — 계수기와 주소 비교 | 씀 |
| ③ sanitizer | — | 부적용(메모리 사고가 없는 주제다) |
| ★★★ ④ **링크 결과 + `nm`** | ★ **본체** — `링크 성공` / `multiple definition` / `undefined reference` · 글자 `T`/`t`/`B`/`b`/`R`/`U`/(없음) | 씀 |
| ⑤ 전처리 결과 · include 트리 | ★★ `-E -P` 로 **순환 include 가 만든 순서** · `-H` 트리 · `-MMD` 의존성 | 씀 |
| 시간 측정 | — | ★★★ **부적용 — 「`#pragma once` 가 guard 보다 빠르다」는 재지 않았다.** `-H` 로 **파일을 몇 번 여나**만 봤다 |
| ★ 제5의 상태 | 「`#pragma once` 는 같은 파일을 어떻게 알아보나」를 **명세로 물으면 답이 없다**(표준에 없다). **include 트리(`-H`)와 재정의 에러로 바꿔 물으니** gcc 는 **내용과 수정 시각이 같은 사본**을 같은 파일로 봤다 | 창을 바꿔 답함 |

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== gcc-12 --version | sed -n 1p (cc exit=0) =====
gcc-12 (Ubuntu 12.4.0-2ubuntu1~24.04.1) 12.4.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== g++ --version | sed -n 1p (cc exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **헤더 배치 격자 · guard/pragma 격자 · `nm` 글자 · include 트리** · 링크 에러 문구 | ★ 링크 문구를 싣는 블록은 **`-c` 로 `s44a.o`·`s44b.o` 를 먼저** 만들었다 — 한 번에 링크하면 `/tmp/cc….o` 가 박혀 흔들린다 |
| 안 흔들린다 | ★ guard/pragma 격자의 「같은 mtime」 칸 | 캡처가 `cp -p` 로 **수정 시각을 그대로 복사**하고, 다른 쪽은 `touch -d 2020-01-01` 로 **고정**한다 |
| **흔들린다** | — | 이 편에는 없다 — 정규화 규칙은 기본 넷뿐이다 |

## 한눈에 — 쉽게 말하면

**헤더는 「회의 자료 원본」이고, `#include` 는 「참석자마다 복사본을 한 부씩 나눠 주는 것」이다.**

- **복사본에 「우리 회사 전화번호는 이것」이라고 적혀 있으면 괜찮다** — 전화번호가 **하나**라는 사실은 변하지 않는다. → **선언(`extern int g;` · `int f(int);`)은 헤더에 둔다**
- **복사본에 「이 자리에 금고를 하나 설치한다」가 적혀 있으면** 참석자 수만큼 금고가 생긴다 — 회사에 「금고는 하나」 규칙이 있으면 어긋난다. → **정의(`int g = 0;` · 함수 몸통)는 `.c` 한 곳에**
- **「각자 책상에 자기 메모지를 둔다」는 괜찮다** — 원래 사람마다 하나다. 대신 **내 메모지에 쓴 것을 남이 못 본다.** → **`static` 정의는 통과하지만 사본이다**
- **같은 자료를 두 번 받으면 표가 두 번 붙는다** — 「이미 받았으면 버려라」 표시가 필요하다. → **include guard · `#pragma once`**
- **자료 A 가 「B 를 먼저 읽어라」, B 가 「A 를 먼저 읽어라」면** 누가 먼저 읽느냐에 따라 **한쪽은 모르는 말**을 만난다. → **순환 include**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 전화번호(선언) | `int hf(int);` · `extern int hv;` + `.c` 한 곳에 정의 → 링크 성공 | ★★★ (1) |
| 금고(정의) | `int hf(int x) { … }` · `int hv = 0;` → `multiple definition` | ★★★ (1) |
| 자기 메모지 | `static` 함수·변수 → 성공이지만 `nm` 에 `t`/`b` 두 개 · 값이 따로 논다 | ★★ (2) |
| 두 번 받기 | guard 없는 헤더 두 번 → `redefinition` | ★★ (3) |
| 서로 먼저 읽어라 | `s44ea.h` ↔ `s44eb.h` — include 순서에 따라 성공 / 불완전 타입 | ★★ (4) |

```text
   s44h.h (K=3: int hf(int x) { … })
         │ #include = 텍스트 복사
     ┌───┴────────────┐
     ▼                ▼
   s44a.c           s44b.c
   gcc -c           gcc -c            ← 컴파일은 둘 다 성공(각자 hf 를 하나씩 가진다)
     ▼                ▼
   s44a.o: T hf     s44b.o: T hf
     └──────┬─────────┘
            ▼
          링커 : 외부 정의가 둘 → multiple definition     (정의가 없으면 → undefined reference)
```

- ★★★ **이 주제는 「표준」 칸이 무겁다** — 「외부 정의는 정확히 하나」 한 문장이 격자의 거의 모든 칸을 정한다. 세 컴파일러가 **한 행도** 안 갈렸다.
- ★★ **「컴파일러 구현」 칸은 `-fcommon` · `#pragma once` 의 파일 동일성 판단**에 몰린다.

> **번역 단위(translation unit)** — `.c` 파일 하나에 그것이 include 한 헤더를 **전부 붙인** 것. 컴파일은 이 단위로 따로 된다.\
> 예: `gcc -c s44a.c` 한 번 = 번역 단위 하나.

> **외부 정의(external definition)** — 함수 몸통이나 저장 공간을 **만드는** 파일 스코프 선언. 외부 링크 이름은 프로그램 전체에 **하나**만.\
> 예: `int hv = 0;` · `int hf(int x) { … }`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **헤더에 무엇을 두면 링크가 깨지나** — 선언 · 정의 · `static` · `const` · 타입.
2. ★★ **같은 헤더가 두 번 들어오는 것을 무엇이 막나** — include guard 대 `#pragma once` · 경로가 다른 같은 파일.
3. ★★ **헤더끼리 서로 필요하면 어떻게 푸나 · 헤더를 바꾸면 무엇을 다시 컴파일하나** — 순환 include · 전방 선언 · `-H` · `-MMD`.

## 동작 방식

### (1) ★★★ 헤더 배치 격자 — 헤더 내용 열넷 × 빌드 다섯

**언제 쓰나** — 「이것을 헤더에 둬도 되나」를 판단할 때. ★★★ **이 편의 본체**다.

```c
/* s44h.h */
#if K == 1 || K == 2
int hf(int x);
#elif K == 3
int hf(int x) { return x + 1; }
#elif K == 4
static int hf(int x) { return x + 1; }
#elif K == 5
static inline int hf(int x) { return x + 1; }
#elif K == 6 || K == 7
extern int hv;
#elif K == 8
int hv = 0;
#elif K == 9
int hv;
#elif K == 10
static int hv = 0;
#elif K == 11
const int hv = 5;
#elif K == 12
struct hs { int v; };
#elif K == 13
enum he { HE_ONE = 1 };
#elif K == 14
typedef int ht;
#endif
```

```c
/* s44a.c */
#include "s44h.h"

#if K == 2
int hf(int x) { return x + 1; }
#elif K == 7
int hv = 0;
#endif

int use_a(void) {
#if K <= 5
    return hf(1);
#elif K <= 11
    return hv;
#elif K == 12
    struct hs s = { 1 };
    return s.v;
#elif K == 13
    return HE_ONE;
#else
    ht t = 1;
    return t;
#endif
}
```

```c
/* s44b.c */
#include "s44h.h"

int use_a(void);

int use_b(void) {
#if K <= 5
    return hf(2);
#elif K <= 11
    return hv;
#elif K == 12
    struct hs s = { 2 };
    return s.v;
#elif K == 13
    return HE_ONE;
#else
    ht t = 2;
    return t;
#endif
}

int main(void) { return use_a() + use_b() == 0; }
```

```text
===== 헤더 배치 격자 — 헤더 내용 14 × 빌드 5 (두 번역 단위 s44a.c + s44b.c) (exit=0) =====
K · 헤더 s44h.h 에 둔 것                	gcc	gcc-12	clang	gcc -fcommon	g++ (C++17)	nm s44a.o / s44b.o (gcc)
1 int hf(int);  (정의 없음)             	undefined reference	undefined reference	undefined reference	undefined reference	undefined reference	U / U
2 int hf(int);  + s44a.c 에 정의        	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	T / U
3 int hf(int x) { … }                   	multiple definition	multiple definition	multiple definition	multiple definition	multiple definition	T / T
4 static int hf(int x) { … }            	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	t / t
5 static inline int hf(int x) { … }     	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	t / t
6 extern int hv;  (정의 없음)           	undefined reference	undefined reference	undefined reference	undefined reference	undefined reference	U / U
7 extern int hv;  + s44a.c 에 int hv = 0;	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	B / U
8 int hv = 0;                           	multiple definition	multiple definition	multiple definition	multiple definition	multiple definition	B / B
9 int hv;                               	multiple definition	multiple definition	multiple definition	링크 성공	multiple definition	B / B
10 static int hv = 0;                   	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	b / b
11 const int hv = 5;                    	multiple definition	multiple definition	multiple definition	multiple definition	링크 성공	R / R
12 struct hs { int v; };                	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
13 enum he { HE_ONE = 1 };              	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
14 typedef int ht;                      	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
(칸 = $CC -O0 -Wall -Wextra -DK=<행> 으로 s44a.c · s44b.c 를 따로 -c 한 뒤 두 .o 를 링크한 결과 · nm 은 이름 hf/hv 의 글자)
링크가 깨진 칸(gcc · gcc-12 · clang) 18 / 42
gcc · gcc-12 · clang 이 서로 갈린 행 0 / 14
gcc 기본과 -fcommon 이 갈린 행 1 / 14
C(gcc) 와 C++(g++) 가 갈린 행 1 / 14
```

그림 해설 (한 단계씩):

- ★★★ **깨지는 것은 여섯 행 · 두 종류다.**
  - **`multiple definition`** — **정의가 헤더에 있다**: 함수 몸통(3) · `int hv = 0;`(8) · `int hv;`(9) · `const int hv = 5;`(11). 두 `.o` 가 **각자 외부 정의**를 가져 `nm` 이 `T`/`B`/`R` 을 **양쪽에** 찍는다.
  - **`undefined reference`** — **선언만 있고 정의가 아무 데도 없다**: `int hf(int);`(1) · `extern int hv;`(6). `nm` 이 **양쪽 다 `U`**.
- ★★★ **옳은 짝은 2·7행** — 헤더에 **선언**, **`.c` 하나에 정의**. `nm` 이 `T / U`(`B / U`) — **정의 하나 + 쓰는 쪽 참조**.
- ★★ **`static` 정의(4 · 10)와 `static inline`(5)은 통과한다** — 내부 링크라 링커가 **서로 모른다.** 대신 `t / t` · `b / b` — **번역 단위마다 한 벌씩**((2)).
- ★★ **`struct`·`enum`·`typedef`(12\~14)는 `nm` 에 아무것도 없다** — 타입은 **심볼을 만들지 않는다.** 그래서 헤더에 둔다.
- ★★★ **9행 `int hv;` 는 `-fcommon` 에서만 통과한다** — 잠정 정의가 공용(`C`) 심볼로 합쳐진다. **그 판 격자 전체(컴파일러 3 × 플래그 3)는 [29번 형제](../29-scope-and-linkage-static-extern/)의 (5)가 쟀다** — 이 편은 **헤더에 두면 이 한 행이 판을 탄다**만 인용한다. ★ `-fcommon` 도 **8행(초기자 있음)은 못 살린다.**
- ★★★ **11행 `const int hv = 5;` 는 C 에서 깨지고 C++ 에서 통과한다** — C 에서 파일 스코프 `const` 는 **외부 링크**(`nm` 이 `R` — 읽기 전용 데이터의 **외부** 심볼)이고, C++ 에서는 **내부 링크**다(아래 블록의 `r`).
- ★★ **세 컴파일러가 갈린 행 0 / 14** — gcc 13 · gcc-12 · clang 18 이 **같다.** 링크 규칙은 표준이고 링커(`ld`)도 같다.

```text
===== gcc -std=c17 -DK=3 -c s44a.c -o s44a.o && gcc -std=c17 -DK=3 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44b.o: in function `hf':
s44b.c:(.text+0x0): multiple definition of `hf'; s44a.o:s44a.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=1 -c s44a.c -o s44a.o && gcc -std=c17 -DK=1 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44a.o: in function `use_a':
s44a.c:(.text+0xe): undefined reference to `hf'
/usr/bin/ld: s44b.o: in function `use_b':
s44b.c:(.text+0xe): undefined reference to `hf'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=11 -c s44a.c -o s44a.o && gcc -std=c17 -DK=11 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44b.o:(.rodata+0x0): multiple definition of `hv'; s44a.o:(.rodata+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=11 -c s44a.c -o s44a.o && nm s44a.o && g++ -x c++ -std=c++17 -DK=11 -c s44a.c -o s44a.o && nm -C s44a.o (cc exit=0) =====
0000000000000000 R hv
0000000000000000 T use_a
0000000000000000 T use_a()
0000000000000000 r hv
```

- ★★ **링크 에러는 「누가 먼저 정의했나」를 댄다** — ``s44b.o … multiple definition of `hf'; s44a.o … first defined here``. **정의가 헤더에서 왔다는 말은 없다** — 두 `.o` 의 **공통 헤더**를 의심하는 것은 사람 몫이다([목록의 **45번 주제**](../45-translation-units-and-reading-link-errors/)).
- ★★ **`const` 행** — C 의 `nm` 은 `R hv`(외부), C++ 의 `nm -C` 는 `r hv`(내부). 같은 소스가 **언어에 따라 링크가 바뀐다.** C 에서 상수를 헤더에 두려면 **`static const`** 나 `enum` · `#define` 이다(★ `static const` 행은 던지지 않았다 — 10행 `static int` 와 같은 규칙이다).

```text
===== gcc -std=c17 -O0 -DK=5 -c s44a.c -o s44a.o && nm s44a.o && gcc -std=c17 -O2 -DK=5 -c s44a.c -o s44a.o && nm s44a.o (cc exit=0) =====
0000000000000000 t hf
000000000000000f T use_a
0000000000000000 T use_a
```

- ★ **`static inline`(5행)의 `nm` 글자는 최적화를 탄다** — `-O0` 은 `t hf`, `-O2` 는 **심볼 자체가 없다**(호출이 펼쳐졌다). 격자는 `-O0` 으로 쟀다. 헤더의 `inline`·`extern inline` 이 판과 최적화에 따라 어떻게 깨지는지는 [39번 형제](../39-inline-and-c-inline-rules/)의 격자가 정본이다(`extern inline` 은 헤더에 두면 **전부 `multiple definition`**).

### (2) ★★ 헤더의 `static` — 통과하지만 사본이다

```c
/* s44s.h */
static int hcount;
static int hbump(void) { return ++hcount; }
```

```c
/* s44sa.c */
#include "s44s.h"

typedef int (*bump_fn)(void);

int a_bump(void) { return hbump(); }
bump_fn a_fn(void) { return hbump; }
```

```c
/* s44sb.c */
#include <stdio.h>
#include "s44s.h"

typedef int (*bump_fn)(void);

int a_bump(void);
bump_fn a_fn(void);

int main(void) {
    int a1 = a_bump();
    int a2 = a_bump();
    int b1 = hbump();
    printf("a_bump() -> %d, %d · hbump() -> %d · a_fn() == hbump : %d\n",
           a1, a2, b1, a_fn() == hbump);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44sa.c s44sb.c -o x ; ./x (cc exit=0 · run exit=0) =====
a_bump() -> 1, 2 · hbump() -> 1 · a_fn() == hbump : 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44sa.c -o s44sa.o && gcc -std=c17 -Wall -Wextra -pedantic -c s44sb.c -o s44sb.o && nm s44sa.o s44sb.o | grep -E 'hbump|hcount|:$' (exit=0) =====
s44sa.o:
0000000000000000 t hbump
0000000000000000 b hcount
s44sb.o:
0000000000000000 t hbump
0000000000000000 b hcount
```

- ★★★ **`a_bump()` 두 번은 1, 2 · `hbump()` 한 번은 1** — `hcount` 가 **번역 단위마다 따로** 있다. 한쪽에서 올린 값을 다른 쪽이 **못 본다.**
- ★★★ **`a_fn() == hbump` 는 0** — 두 `.c` 의 `hbump` 는 **주소가 다른 두 함수**다. `nm` 도 `t hbump` · `b hcount` 를 **파일마다 하나씩** 찍는다.
- ★★ **그래서 헤더의 `static` 변수는 거의 항상 실수**다 — 「전역 하나」를 원했다면 **`extern` 선언 + `.c` 정의**(격자 7행)다.

```c
/* s44i.h */
static inline int hinc(int x) { return x + 1; }
```

```c
/* s44u.c */
#include "s44s.h"
#include "s44i.h"

int nothing(void) { return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44u.c -o /dev/null (cc exit=0) =====
In file included from s44u.c:1:
s44s.h:2:12: warning: ‘hbump’ defined but not used [-Wunused-function]
    2 | static int hbump(void) { return ++hcount; }
      |            ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44u.c -o /dev/null (cc exit=0) =====
In file included from s44u.c:1:
./s44s.h:2:12: warning: unused function 'hbump' [-Wunused-function]
    2 | static int hbump(void) { return ++hcount; }
      |            ^~~~~
1 warning generated.
```

- ★★ **쓰지 않은 `static` 함수는 경고, `static inline` 은 조용하다** — `s44u.c` 는 두 헤더를 include 하고 아무것도 안 쓴다. gcc 「‘hbump’ defined but not used [-Wunused-function]」, clang 「unused function 'hbump'」. **`hinc`(static inline)에는 두 컴파일러 다 0줄.** 헤더에 함수 정의를 둔다면 **`static inline`** 인 이유가 이것이다.

### (3) ★★ include guard 대 `#pragma once` — 경로가 다른 같은 파일

**언제 쓰나** — 같은 헤더가 **여러 경로**로 들어오는 빌드(심볼릭 링크 · 설치본과 소스본 · 복사된 벤더 코드).

```c
/* s44n.h */
struct gq { int v; };
```

```c
/* s44g.h */
#ifndef S44G_H
#define S44G_H

struct gq { int v; };

#endif
```

```c
/* s44p.h */
#pragma once

struct gq { int v; };
```

```c
/* s44m.c */
#include FIRST
#include SECOND

int main(void) {
    struct gq q = { 0 };
    return q.v;
}
```

```text
===== include guard 대 #pragma once — 헤더 3 × 두 번째 경로 6 × 컴파일러 3 (exit=0) =====
두 번째 include               	같은 inode	같은 내용	같은 mtime
d1/ · 같은 경로 두 번         	예	예	예
d3/ · 디렉토리 심볼릭 링크    	예	예	예
d5/ · 파일 심볼릭 링크        	예	예	예
d6/ · 하드 링크               	예	예	예
d2/ · 사본 · 같은 mtime       	아니오	예	예
d4/ · 사본 · 다른 mtime       	아니오	예	아니오
---
헤더 · 두 번째 include              	gcc	gcc-12	clang
s44n.h · d1/ 같은 경로 두 번        	재정의 에러	재정의 에러	재정의 에러
s44n.h · d3/ 디렉토리 심볼릭 링크   	재정의 에러	재정의 에러	재정의 에러
s44n.h · d5/ 파일 심볼릭 링크       	재정의 에러	재정의 에러	재정의 에러
s44n.h · d6/ 하드 링크              	재정의 에러	재정의 에러	재정의 에러
s44n.h · d2/ 사본 · 같은 mtime      	재정의 에러	재정의 에러	재정의 에러
s44n.h · d4/ 사본 · 다른 mtime      	재정의 에러	재정의 에러	재정의 에러
s44g.h · d1/ 같은 경로 두 번        	통과	통과	통과
s44g.h · d3/ 디렉토리 심볼릭 링크   	통과	통과	통과
s44g.h · d5/ 파일 심볼릭 링크       	통과	통과	통과
s44g.h · d6/ 하드 링크              	통과	통과	통과
s44g.h · d2/ 사본 · 같은 mtime      	통과	통과	통과
s44g.h · d4/ 사본 · 다른 mtime      	통과	통과	통과
s44p.h · d1/ 같은 경로 두 번        	통과	통과	통과
s44p.h · d3/ 디렉토리 심볼릭 링크   	통과	통과	통과
s44p.h · d5/ 파일 심볼릭 링크       	통과	통과	통과
s44p.h · d6/ 하드 링크              	통과	통과	통과
s44p.h · d2/ 사본 · 같은 mtime      	통과	통과	재정의 에러
s44p.h · d4/ 사본 · 다른 mtime      	재정의 에러	재정의 에러	재정의 에러
(칸 = $CC -std=c17 -DFIRST="d1/<헤더>" -DSECOND="<디렉토리>/<헤더>" -c s44m.c 의 결과)
재정의 에러가 난 칸 22 / 54
gcc 와 clang 이 갈린 행 1 / 18
```

그림 해설 (한 단계씩):

- ★★★ **guard 없는 헤더(`s44n.h`)는 여섯 경우 전부 재정의 에러** — 같은 경로 두 번부터 막힌다.
- ★★★ **include guard(`s44g.h`)는 여섯 경우 전부 통과** — guard 는 **매크로 이름**으로 판단하므로 **파일이 무엇이든**(사본이라도) 두 번째를 비운다.
- ★★★ **`#pragma once`(`s44p.h`)는 「같은 파일」 판단에 달렸다** — 같은 경로 · 디렉토리 심볼릭 링크 · 파일 심볼릭 링크 · 하드 링크(**같은 inode**)는 세 컴파일러 다 통과. **사본에서 갈렸다.**
  - ★★★ **사본 · 같은 mtime** — **gcc · gcc-12 는 통과, clang 은 재정의 에러**. gcc 는 **내용과 수정 시각이 같은 다른 파일**을 같은 파일로 봤다(아래 `-H` 가 **한 줄**만 찍는다). ★ 「내용은 다르고 mtime 만 같은」 칸은 던지지 않았다 — gcc 가 무엇을 비교하는지까지는 이 격자가 말하지 않는다.
  - ★★ **사본 · 다른 mtime** — 세 컴파일러 다 **재정의 에러**.
- ★★ **gcc 와 clang 이 갈린 행 1 / 18** — 그 한 행이 「사본 · 같은 mtime」이다. ★ 「심볼릭 링크에서 갈린다」는 **이 판에서 아니었다** — 두 컴파일러 다 심볼릭 링크를 따라가 같은 파일로 봤다.

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44p.h"' '-DSECOND="d2/s44p.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44p.h
```

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44g.h"' '-DSECOND="d2/s44g.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44g.h
. d2/s44g.h
```

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44g.h"' '-DSECOND="d1/s44g.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44g.h
```

```text
===== clang -std=c17 '-DFIRST="d1/s44p.h"' '-DSECOND="d2/s44p.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
./d2/s44p.h:3:8: error: redefinition of 'gq'
    3 | struct gq { int v; };
      |        ^
./d1/s44p.h:3:8: note: previous definition is here
    3 | struct gq { int v; };
      |        ^
1 error generated.
```

```text
===== gcc -std=c17 '-DFIRST="d1/s44p.h"' '-DSECOND="d4/s44p.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d4/s44p.h:3:8: error: redefinition of ‘struct gq’
    3 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44p.h:3:8: note: originally defined here
    3 | struct gq { int v; };
      |        ^~
```

```text
===== gcc -std=c17 '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d1/s44n.h:1:8: error: redefinition of ‘struct gq’
    1 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44n.h:1:8: note: originally defined here
    1 | struct gq { int v; };
      |        ^~
```

- ★★ **`-H` 가 여는 파일을 보여 준다** — `#pragma once` 사본(같은 mtime)은 gcc 가 **`d1/s44p.h` 한 번만** 열었다. guard 사본은 **`d2/s44g.h` 도 연다**(guard 가 비우는 것은 **열고 난 뒤**다). 같은 경로의 guard 는 **한 번만** 연다 — gcc 가 guard 모양을 기억해 두 번째 열기를 건너뛰는 것으로 보인다(★ gcc 문서는 읽지 않았다 — 본 것은 `-H` 의 줄 수다).
- ★★★ **`#pragma once` 는 표준이 아니다**(N3220 에 0건) — 「같은 파일」의 정의가 **컴파일러마다 다르고**, 이 격자가 그 차이를 한 칸으로 보였다. **guard 는 표준 전처리만으로 된다.**
- ★★★ **「`#pragma once` 가 guard 보다 빠르다」는 재지 않았다** — 본 것은 **파일을 여는 횟수**(`-H`)뿐이다.

```text
===== gcc -std=c2x '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d1/s44n.h:1:8: error: redefinition of ‘struct gq’
    1 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44n.h:1:8: note: originally defined here
    1 | struct gq { int v; };
      |        ^~
```

```text
===== clang -std=c2x '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
./d1/s44n.h:1:8: error: redefinition of 'gq'
    1 | struct gq { int v; };
      |        ^
s44m.c:1:10: note: './d1/s44n.h' included multiple times, additional include site here
    1 | #include FIRST
      |          ^
s44m.c:2:10: note: './d1/s44n.h' included multiple times, additional include site here
    2 | #include SECOND
      |          ^
./d1/s44n.h:1:8: note: unguarded header; consider using #ifdef guards or #pragma once
    1 | struct gq { int v; };
      |        ^
1 error generated.
```

- ★★ **C23 은 같은 내용의 `struct` 재정의를 허용한다**(N3220 태그 절 — 「같은 태그의 두 선언이 멤버 목록을 가지면 호환 타입의 요건을 채워야 한다」 — 금지가 아니라 **조건**이 됐다). ★★ **그러나 이 판의 gcc 13 · clang 18 은 `-std=c2x` 에서도 재정의 에러**다 — **명세가 허용하는데 구현이 아직 막는 자리**. guard 를 빼도 되는 날은 이 판에서는 오지 않았다.

### (4) ★★ 순환 include — 누가 먼저 읽히느냐

**언제 쓰나** — 두 헤더가 서로의 타입을 쓸 때.

```c
/* s44ea.h */
#ifndef S44EA_H
#define S44EA_H

#include "s44eb.h"

struct ea { int id; struct eb inner; };

#endif
```

```c
/* s44eb.h */
#ifndef S44EB_H
#define S44EB_H

#include "s44ea.h"

struct eb { int id; struct ea *owner; };

#endif
```

```c
/* s44e1.c */
#include "s44ea.h"
#include "s44eb.h"

int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```c
/* s44e2.c */
#include "s44eb.h"
#include "s44ea.h"

int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44e1.c -o x && clang -std=c17 -Wall -Wextra -pedantic s44e1.c -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44e2.c -o /dev/null (cc exit=1) =====
In file included from s44eb.h:4,
                 from s44e2.c:1:
s44ea.h:6:31: error: field ‘inner’ has incomplete type
    6 | struct ea { int id; struct eb inner; };
      |                               ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44e2.c -o /dev/null (cc exit=1) =====
In file included from s44e2.c:1:
In file included from ./s44eb.h:4:
./s44ea.h:6:31: error: field has incomplete type 'struct eb'
    6 | struct ea { int id; struct eb inner; };
      |                               ^
./s44ea.h:6:28: note: forward declaration of 'struct eb'
    6 | struct ea { int id; struct eb inner; };
      |                            ^
1 error generated.
```

```text
===== gcc -std=c17 -E -P s44e1.c (cc exit=0) =====
struct eb { int id; struct ea *owner; };
struct ea { int id; struct eb inner; };
int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```text
===== gcc -std=c17 -E -P s44e2.c (cc exit=0) =====
struct ea { int id; struct eb inner; };
struct eb { int id; struct ea *owner; };
int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

그림 해설 (한 단계씩):

- ★★★ **같은 두 헤더인데 include 순서만 바꾸면 한쪽은 성공, 한쪽은 에러**다. `s44ea.h` 의 `struct ea` 는 `struct eb` 를 **값으로** 담아 `eb` 가 **완전해야** 하고, `s44eb.h` 의 `struct eb` 는 `struct ea *` **포인터**만 담는다.
- ★★★ **`s44e2.c`(eb 먼저)의 `-E -P`** — `s44eb.h` 가 guard 를 세우고 `s44ea.h` 를 include → `s44ea.h` 가 `s44eb.h` 를 include 하지만 **guard 에 막혀 빈손** → `struct ea { … struct eb inner; }` 가 **`struct eb` 정의보다 먼저** 나온다. gcc 「field ‘inner’ has incomplete type」, clang 「field has incomplete type 'struct eb'」.
- ★★ **`s44e1.c`(ea 먼저)는 반대 순서**라 `struct eb` 가 먼저 완성된다. **guard 가 순환을 끊어 주지만, 끊긴 자리에서 한쪽이 불완전해진다.**

```text
   #include "s44eb.h"   (s44e2.c 의 첫 줄)
     S44EB_H 정의
     #include "s44ea.h"
       S44EA_H 정의
       #include "s44eb.h"  → S44EB_H 가 이미 있다 → 빈손
       struct ea { … struct eb inner; };   ← struct eb 가 아직 없다 → 불완전 타입 에러
     struct eb { … struct ea *owner; };
```

**전방 선언 + 포인터로 푼다.**

```c
/* s44fa.h */
#ifndef S44FA_H
#define S44FA_H

#include "s44fb.h"

struct fa { int id; struct fb inner; };

#endif
```

```c
/* s44fb.h */
#ifndef S44FB_H
#define S44FB_H

struct fa;

struct fb { int id; struct fa *owner; };

#endif
```

```c
/* s44f2.c */
#include "s44fb.h"
#include "s44fa.h"

int main(void) {
    struct fa a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44f2.c -o x ; ./x (cc exit=0 · run exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44f2.c -o /dev/null (cc exit=0) =====
```

- ★★★ **`s44fb.h` 는 `s44fa.h` 를 include 하지 않고 `struct fa;` 한 줄**(전방 선언)만 둔다 — 포인터 멤버는 **불완전 타입으로 충분**하다. 순환이 사라져 **어느 순서로 include 해도** 된다(`fb` 먼저인 `s44f2.c` 가 두 컴파일러에서 통과 · `run exit=0`).
- ★★ **값으로 담는 쪽만 상대 헤더를 include** 한다 — 한 방향이다. 이 「크기를 몰라도 되는 자리엔 포인터 + 전방 선언」이 [25번 형제](../25-incomplete-types-and-opaque-struct/)의 불투명 구조체와 같은 도구다.
- ★ **두 구조체가 서로를 값으로** 담는 것은 헤더와 무관하게 불가능하다(크기가 무한) — 순환 include 는 그 **한 단계 앞**, 「한쪽만 값인데 순서가 틀린」 경우에 난다.

### (5) ★★ include 트리와 의존성 — 헤더를 바꾸면 무엇을 다시 컴파일하나

```c
/* s44t.c */
#include <stddef.h>
#include "s44fa.h"

size_t fa_size(void) { return sizeof(struct fa); }
```

```text
===== gcc -std=c17 -H -c s44t.c -o s44t.o (cc exit=0) =====
. /usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h
. s44fa.h
.. s44fb.h
Multiple include guards may be useful for:
/usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h
```

```text
===== gcc -std=c17 -MMD -c s44t.c -o s44t.o && cat s44t.d (cc exit=0) =====
s44t.o: s44t.c s44fa.h s44fb.h
```

```text
===== gcc -std=c17 -MD -c s44t.c -o s44t.o && cat s44t.d (cc exit=0) =====
s44t.o: s44t.c /usr/include/stdc-predef.h \
 /usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h s44fa.h s44fb.h
```

- ★★ **`-H`** — 연 헤더를 **깊이만큼 점**을 붙여 찍는다(`s44fa.h` 안에서 `s44fb.h` 를 열어 `..`). ★ 끝의 「Multiple include guards may be useful for:」 는 **guard 가 없는 헤더**(여기선 gcc 의 `stddef.h`)를 알려 준다.
- ★★★ **`-MMD`** — `s44t.o: s44t.c s44fa.h s44fb.h` — **이 `.o` 는 이 파일들에 의존한다**는 Makefile 규칙을 만든다. **`s44fb.h` 를 고치면 `s44t.o` 를 다시 만들어야 한다**가 기계적으로 나온다. **`-MD` 는 시스템 헤더까지** 적는다.
- ★ **헤더를 바꿨는데 다시 컴파일 안 된 `.o` 가 남으면** 두 번역 단위가 **다른 판의 `struct`** 를 믿게 된다 — 이 편은 그 사고를 던지지 않았다(링크는 통과하고 **조용히 틀린다** — 규칙상의 결과다).

## 문법 — 형태와 규칙

### 형태

```text
   /* s.h — 헤더에 두는 것 */
   #ifndef S_H                         include guard (표준 전처리만)
   #define S_H
   struct s;                           전방 선언 — 포인터만 쓸 때
   struct p { int x; };                타입 정의 — 심볼 없음
   enum e { E1 = 1 };  typedef int t;  심볼 없음
   extern int counter;                 ★ 변수는 선언만
   int api(int);                       ★ 함수는 선언만
   static inline int fast(int x) { … } 함수 정의를 굳이 헤더에 둔다면 static inline
   #endif

   /* s.c — 정의는 한 곳에 */
   #include "s.h"
   int counter = 0;
   int api(int x) { … }
```

### 금지 사례 — 어느 것이 무슨 층인가

| 헤더에 둔 것 | 결과 | 층 |
|---|---|---|
| `int f(int x) { … }` · `int g = 0;` | `multiple definition` | ★★★ 표준(외부 정의 둘 — UB · 진단 의무 없음, 링커가 막는다) |
| `int g;` | 기본값에서 `multiple definition` · `-fcommon` 에서 통과 | ★★ 표준(UB) + 컴파일러 구현(공용 심볼) — [29번 형제](../29-scope-and-linkage-static-extern/) |
| `const int g = 5;` | C `multiple definition` · C++ 통과 | ★★ 표준(언어마다 링크가 다르다) |
| `static int g;` | 통과 · **사본** | 표준(내부 링크) |
| guard 없는 헤더 두 번 | 재정의 에러(C23 은 허용하나 이 판은 막는다) | 표준 + 구현의 C23 지원 |
| `#pragma once` + 같은 내용 · 같은 mtime 사본 | gcc 통과 · clang 에러 | ★★★ 컴파일러 구현 |

### 규칙 불릿

- ★★★ **헤더에는 「몇 번 복사돼도 정의가 하나로 남는 것」만** — 선언 · 타입 · 매크로 · `static inline`.
- ★★★ **변수는 `extern` 선언을 헤더에, 정의(`int g = 0;`)는 `.c` 하나에.**
- ★★ **모든 헤더에 include guard** — `#pragma once` 를 쓰더라도 **사본이 생기는 빌드**에서는 guard 가 안전하다.
- ★★ **서로 필요한 헤더는 전방 선언 + 포인터로 한 방향만 include.**
- ★ **`-MMD` 로 의존성을 빌드에 넣는다.**

## 어디서 틀리나

### 1. ★★★ 「헤더에 전역 변수를 두면 모두가 같은 변수를 쓴다」

`int hv = 0;` 이면 **`multiple definition`**, `static int hv = 0;` 이면 **통과하지만 파일마다 다른 변수**다((1)·(2)). 같은 하나를 원하면 **`extern` + `.c` 정의**.

### 2. ★★★ 「`int hv;` 는 선언이라 헤더에 둬도 된다」

**잠정 정의**다 — 기본값에서 `multiple definition`, `-fcommon` 에서만 통과((1) 9행). 옛 코드가 새 컴파일러에서 깨지는 전형이다([29번 형제](../29-scope-and-linkage-static-extern/)).

### 3. ★★ 「`const` 는 C++ 처럼 파일마다 따로다」

C 의 파일 스코프 `const` 는 **외부 링크**라 `multiple definition` 이다((1) 11행). C++ 로 컴파일하면 통과해서 **C++ 에서 옮겨 온 코드**가 여기서 깬다.

### 4. ★★★ 「`#pragma once` 는 guard 와 같다」

**사본에서 갈렸다**((3)) — gcc 는 같은 내용 · 같은 mtime 사본을 **같은 파일로** 보고 두 번째를 버렸고, clang 은 **다른 파일로** 봐 재정의 에러를 냈다. 표준에 없는 기능이라 **「같은 파일」이 구현마다 다르다.** guard 는 여섯 경우 전부 같았다.

### 5. ★★ 「include guard 가 있으니 순환 include 는 안전하다」

guard 는 **무한 반복만** 막는다 — 끊긴 자리에서 **한쪽 타입이 불완전**해져 include 순서에 따라 에러가 난다((4)).

### 6. ★★ 「`static inline` 이 `static` 보다 빠르니까 헤더에 쓴다」

이 편이 본 이유는 **속도가 아니라 경고**다 — 안 쓰는 `static` 함수는 `-Wunused-function` 경고, `static inline` 은 0줄((2)). 속도는 재지 않았다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 무겁다** — 헤더 배치 격자는 **세 컴파일러가 0 / 14 행 갈렸다.**\
★★ **「컴파일러 구현」 칸은 `-fcommon` 과 `#pragma once`** 에 몰린다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **외부 정의는 하나 · `static` 은 내부 링크(사본) · 타입은 심볼 없음 · C 의 파일 스코프 `const` 는 외부 링크 · include 는 텍스트 복사 · 불완전 타입 멤버 금지 · 포인터는 불완전 타입으로 충분** | 격자 · `nm` · 계수 · 에러 |
| ★★★ **UB** | 아무 일이나 | ★★ **외부 정의가 둘**(3·8·9·11행) — 진단 의무가 없다. **이 판은 링커가 전부 막았다** | 링크 에러 |
| ★★ **조건부 표준** | 판이 조건 | ★★ **C23 의 같은 내용 태그 재정의 허용** — 이 판은 미구현 | `-std=c2x` 에러 |
| **구현 정의** | 문서화 의무 | ★ **`#include` 검색**([41번 형제](../41-preprocessor-directives-and-conditional-compilation/)) · `#pragma` | — |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★★ **`#pragma once` 의 파일 동일성**(gcc 는 같은 내용 · 같은 mtime 사본을 같은 파일로 봤다 · 다른 mtime 이면 아니다 — 판정 규칙 자체는 확인하지 않았다) · ★★ **`-fcommon`**(공용 심볼) · `-H` 의 guard 기억 · `-MMD` · 쓰지 않은 `static` 의 경고 | 격자 · `-H` · 진단 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **헤더의 `static` 변수가 사본인 것** — 컴파일 · 링크 · 경고 전부 0. 값이 따로 논다는 것은 **실행해야** 보인다 |
| ★★ **컴파일러 구현** | ★★ **gcc 가 `#pragma once` 사본을 버린 것** — 진단 0줄. `-H` 로만 보인다 · **`-fcommon` 의 병합** — 진단 0줄 |
| ★★ **(층을 가로지름)** | ★ **헤더를 고친 뒤 안 다시 만든 `.o`** — 링크는 통과한다(던지지 않았다) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **링크 에러는 친절한 쪽이다** — 조용한 것은 **`static` 사본**과 **`#pragma once` 의 판단**이다.
  - ★★ **표준만으로 되는 도구(guard · `extern`)를 고른다** — 판과 컴파일러에 안 흔들린다.
  - ★★ **`nm` 이 「정의가 몇 개인가」를 글자로 말한다** — 링크 전에 확인할 수 있다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 전역 변수 하나 공유 | ★★★ 헤더 `extern int g;` + `.c` 하나 `int g = 0;` | 헤더 `int g;` · `int g = 0;` · `static int g;` |
| 함수 공유 | ★★★ 헤더 선언 + `.c` 정의 | 헤더에 몸통 |
| 작은 함수를 헤더에 | ★★ `static inline`([39번 형제](../39-inline-and-c-inline-rules/)) | `static`(안 쓰면 경고) · `extern inline`(전부 깨짐) |
| 상수 공유 | ★★ `enum` · `#define` · `static const` | `const int g = 5;`(C 에서 깨짐) |
| 두 번 include 막기 | ★★★ include guard(원하면 `#pragma once` 를 **같이**) | `#pragma once` 만 — 사본이 생기는 빌드에서 |
| 서로 필요한 타입 | ★★ 전방 선언 + 포인터 · 한 방향 include | 서로 include |
| 재컴파일 판단 | ★★ `-MMD` 의존성 | 손으로 관리 |

판단 규칙 두 줄.

- ★★★ **「이 줄이 두 `.c` 에 복사되면 정의가 둘이 되나」를 묻는다** — 되면 `.c` 로 옮긴다.
- ★★ **`nm *.o` 로 같은 이름에 `T`/`D`/`B`/`R` 이 둘 이상인지 본다.**

## 핵심 문장

- ★★★ **헤더 배치 격자 14행 × 5빌드에서 gcc · gcc-12 · clang 의 링크가 깨진 칸은 18 / 42 — 세 컴파일러가 갈린 행은 0 이다.**
- ★★★ **정의(함수 몸통 · `int g = 0;` · `int g;` · `const int g = 5;`)를 헤더에 두면 `multiple definition`, 선언만 두고 정의가 없으면 `undefined reference` — 옳은 짝은 헤더 선언 + `.c` 하나 정의(`nm` `T / U`).**
- ★★ **`static` 정의는 통과하지만 번역 단위마다 사본이다 — 계수기가 따로 오르고(1, 2 대 1) 함수 주소가 다르다(`a_fn() == hbump` 는 0).**
- ★★ **C 의 `const int g = 5;` 는 `R`(외부)로 깨지고 C++ 는 `r`(내부)로 통과했다. `int g;` 는 `-fcommon` 에서만 통과했다(판 격자는 29편).**
- ★★★ **include guard 는 여섯 경로 전부 통과, `#pragma once` 는 같은 내용 · 같은 mtime 사본에서 gcc 통과 · clang 에러로 갈렸다(1 / 18 행) — 심볼릭 링크는 두 컴파일러 다 같은 파일로 봤다.**
- ★★ **순환 include 는 guard 가 끊은 자리에서 한쪽 타입이 불완전해져 include 순서에 따라 에러가 난다 — 전방 선언 + 포인터로 한 방향만 include 하면 풀린다.**

## 관련 자료

- [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/) — ★★★ **경계.** 「4. 컴파일 전체 흐름과 링커」가 **`.o` 여럿을 링커가 합친다**까지를 쓴다. **그쪽은 링커가 하는 일 일반까지, 여기는 같은 헤더를 가진 `.o` 들이 왜 충돌하나부터.**
- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★★★ **선행.** `static`/`extern` 규칙 · **잠정 정의의 판 격자**.
- [39번 형제 — `inline`](../39-inline-and-c-inline-rules/) — ★★ 헤더의 `inline`·`extern inline` 링크 격자.
- [41번 형제 — 전처리기](../41-preprocessor-directives-and-conditional-compilation/) — ★★ **선행.** include 가 텍스트 복사라는 것 · 검색 경로.
- [25번 형제 — 불투명 구조체](../25-incomplete-types-and-opaque-struct/) — ★★ 전방 선언 + 포인터의 다른 쓸모.
- [34번 형제 — 선언·정의·프로토타입](../34-function-declarations-definitions-and-prototypes/) — ★ 선언과 정의의 구분.
- [목록의 **45번 주제**](../45-translation-units-and-reading-link-errors/)(번역 단위와 링크 오류 읽기) — ★ 이 편의 링크 에러를 **거꾸로** 읽는 자리.
- [C++ 35 — 인스턴스화와 헤더 배치](../../../cpp/syntax/35-instantiation-header-placement-and-reading-errors/) · [C++ 25 — `inline` 변수](../../../cpp/syntax/25-static-members-and-inline-variables/) — ★ C++ 가 **정의를 헤더에 두게** 만든 장치들. C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **55번**(ODR · 모듈)이 번역 단위 규칙의 정본 자리다.

## 용어 풀이

> **include guard** — `#ifndef X_H / #define X_H / … / #endif` 로 헤더 내용을 **두 번째부터 비우는** 관용구. 표준 전처리만 쓴다.\
> 예: `s44g.h`.

> **`#pragma once`** — 「이 파일은 한 번만 넣어라」는 **비표준** 지시. 무엇이 「같은 파일」인지는 컴파일러가 정한다.\
> 예: `s44p.h` 의 첫 줄.

> **전방 선언(forward declaration)** — 정의 없이 `struct 이름;` 만 두어 **불완전 타입**을 알리는 것. 포인터 멤버·매개변수에는 충분하다.\
> 예: `struct fa;`.

> **`nm` 글자** — `T`/`t` 코드(대문자 = 외부) · `D`/`d` 초기화된 데이터 · `B`/`b` 0 데이터 · `R`/`r` 읽기 전용 · `C` 공용 · `U` 정의 없음(밖에서 찾는다).\
> 예: `B hv` · `U hf`.

> **`-MMD`** — 컴파일하면서 `.d` 파일에 **이 목적 파일이 의존하는 헤더 목록**(시스템 헤더 제외)을 Makefile 규칙으로 적는 gcc/clang 옵션.\
> 예: `s44t.o: s44t.c s44fa.h s44fb.h`.

## 더 들어가면

- ★★ **헤더를 고친 뒤 한쪽 `.o` 만 다시 만든 빌드** — 두 번역 단위가 다른 `struct` 를 믿는 사고. ★ 던지지 않았다.
- ★ **`static const int` 를 헤더에** — 10행과 같은 규칙일 것 — ★ 던지지 않았다.
- ★ **clang 의 `#pragma once` 판단 기준** — inode 인가 경로 해석인가. 이 격자는 「사본을 다른 파일로 본다」까지만 보였다.

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 외부 정의 절 — 「**외부 링크 식별자가 식에 쓰이면 프로그램 전체에 외부 정의가 정확히 하나 있어야 한다**」 · 「**초기자 없는 파일 스코프 객체 선언은 잠정 정의**」 · 태그 절 — 「**같은 태그의 두 선언이 멤버 목록을 가지면 호환 타입의 요건을 채워야 한다**」(C23 의 태그 호환) 를 **본문에서 직접 찾아 읽었다** · ★ **`#pragma once` 는 N3220 에 한 번도 나오지 않는다**(`grep` 0건))
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **링크 결과 · `nm` 글자 · include 트리 · 진단은 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
★★★ **본체는 헤더 배치 격자다** — 헤더에 둔 것 14 × 빌드 5(gcc · gcc-12 · clang · gcc `-fcommon` · g++), **두 번역 단위가 같은 헤더를 include** 하고 따로 `-c` 한 뒤 링크한다. 칸마다 **링크 결과**, 끝 칸에 **`nm` 글자**.\
★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
**버전** — include 와 링크 규칙은 C89 부터다. ★ **gcc 10 · clang 11 부터 `-fno-common` 이 기본**([29번 형제](../29-scope-and-linkage-static-extern/)가 문서로 확인). ★ **C23 은 같은 내용의 `struct` 재정의를 허용**하지만 이 판의 두 컴파일러는 아직 막는다((3)).
★★★ **경계** — **링크 단계 일반(심볼 해결 · 재배치 · 라이브러리)** 은 [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/)의 「4. 컴파일 전체 흐름과 링커」가 정본이다 — 그쪽은 **`.o` 여럿이 링커로 합쳐진다**까지, 이 편은 **그 `.o` 들이 같은 헤더를 가졌을 때 무엇을 두면 깨지나**부터.\
★★★ **`static`/`extern` 의 링크 규칙 자체와 잠정 정의의 판 격자**(`-fno-common`/`-fcommon` × 컴파일러 3)는 [29번 형제](../29-scope-and-linkage-static-extern/)의 (5)가, **헤더의 `inline`·`extern inline` 링크 격자**는 [39번 형제](../39-inline-and-c-inline-rules/)가 **이미 쟀다** — 이 편은 그 격자를 **다시 재지 않고** 「헤더에 둘 수 있나」의 한 행씩으로만 인용한다.\
★ **`#include` 가 텍스트를 붙여 넣는다는 것 · 검색 경로**는 [41번 형제](../41-preprocessor-directives-and-conditional-compilation/), **불투명 구조체**는 [25번 형제](../25-incomplete-types-and-opaque-struct/), **링크 오류를 거꾸로 읽기**는 [목록의 **45번 주제**](../45-translation-units-and-reading-link-errors/)다.
선행 — [29번 형제](../29-scope-and-linkage-static-extern/) · [41번 형제](../41-preprocessor-directives-and-conditional-compilation/).
