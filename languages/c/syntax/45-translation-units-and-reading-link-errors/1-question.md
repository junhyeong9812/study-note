# c/syntax/45 — 번역 단위와 링크 오류 읽기: 「**링크 에러는 「이 이름의 정의가 몇 개인가」에 대한 링커의 대답이다 — 문구에서 원인으로 거꾸로 걸어가는 길은 `nm` 이 깐다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 다섯 문항(1\~5)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **컴파일(`-c`)과 링크를 갈라** 생각하라 — 이 편의 파일은 **전부 `-c` 가 통과한다.** 갈리는 것은 링크다.
- ★★ 각 문항 끝에서 스스로 물어라 — 「**링커가 찾는 이름의 정의가 몇 개 있나 — 0 · 1 · 2?**」
- ★ 링크 명령은 전부 **목적 파일을 먼저 `-c` 로 따로** 만든 뒤 잇는다(`gcc a.o b.o -o x`).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 원인 열 줄 × 링크 세 판 (예측) ★★★ 이 주제의 축

아래 파일 묶음을 줄마다 **`-std=c17 -c` 로 따로** 만든 뒤 링크한다(C++ 파일은 `-std=c++17 -c`).
링크 판은 셋 — `gcc`(ld.bfd) · `clang`(같은 기본 링커) · `gcc -fuse-ld=gold`.

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

| 줄 | 링크하는 것 |
|---|---|
| 1 | `s45u.o` |
| 2 | `s45h1.o s45h2.o` |
| 3 | `s45s1.o s45s2.o` |
| 4 | `s45t1.o s45t2.o` |
| 5 | `s45x.o`(C++ 로 만든 것) `s45xc.o` |
| 6 | `-L. -ls45 s45lm.o`(`libs45.a` = `ar rcs libs45.a s45l.o`) |
| 7 | `s45lm.o -L. -ls45` |
| 8 | `s45n.o` |
| 9 | `s45w1.o` |
| 10 | `s45w3.o s45w4.o` |

- ★★★ 열 줄 × 세 판, 각 칸의 링크 결과는?
- ★★ **링크가 된 칸은 몇 칸**인가? gcc 와 clang 이 갈리는 줄이 있는가? ld.bfd 와 gold 는?

### 2. `nm` 이 붙이는 글자 (예측) ★★★

1번의 파일을 gcc(C++ 파일은 g++)로 만들고 `nm` 으로 **문제의 이름** 하나만 본다.

- ★★★ 1\~5 줄의 두 파일에서 그 이름의 글자는 각각 무엇인가(`U` · `T` · `t` · 없음)? 5번 줄은 **이름 자체**도 적어라.
- ★★ 9·10 줄의 `hook`·`level` 은 무슨 글자인가?
- ★ 8번 줄에서 `main` 을 찾는 파일은 **어느 파일**인가?

### 3. `-lm` 의 자리 (예측) ★★

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

`s45m.c` 를 `-c` 로 만든 뒤 `$CC s45m.o -lm` 과 `$CC -lm s45m.o` 로 링크한다(`$CC` = `gcc` · `clang`).

- ★★ 네 칸의 결과는?
- ★★★ 두 드라이버가 **같은 ld** 를 부르는데도 갈린다면, **무엇이 다른가**?

### 4. 약한 심볼 (예측) ★★

```c
/* s45w2.c */
int hook(void) { return 5; }
```

- ★★ `s45w1.o` 만 링크한 판과 `s45w1.o s45w2.o` 를 링크한 판은 각각 무엇을 찍는가?
- ★★ `s45w3.o` 만 링크한 판과 `s45w3.o s45w4.o` 를 링크한 판은 각각 무엇을 찍는가?

### 5. 같은 에러, 세 링커의 문구 (예측) ★★

1번의 1줄(`undefined reference`)과 2줄(`multiple definition`)을 gcc · clang · gold 로 링크한다.

- ★★ 세 판의 **마지막 줄**은 각각 누가 찍은 무슨 줄인가?
- ★★ gold 의 문구는 ld.bfd 와 **무엇이 같고 무엇이 다른가**?

### 6. 에러 문구에서 원인으로 (왜) ★★★

- ★★★ `undefined reference to 'X'` 를 받았을 때 **원인 후보를 전부** 대고, 각각 **`nm` 으로 무엇을 보면 가려지나**?
- ★★ `multiple definition of 'X'` 는 원인 후보가 왜 훨씬 좁은가?

### 7. C++ 로 컴파일한 정의 (왜) ★★

- ★★ 5번 줄에서 정의는 **있는데** 왜 `undefined reference` 인가?
- ★ `extern "C"` 는 어느 쪽 파일에 붙이는가? 붙이면 `nm` 은 무엇을 보이는가?

### 8. 라이브러리 순서 (경계) ★★

- ★★ 6·7 줄(정적 라이브러리)과 3번 문항(공유 라이브러리 `libm`)에서 순서가 결과를 바꾸는 **이유가 같은가**?
- ★ 「`-l` 은 뒤에」를 **규칙으로 외워도 되는 이유**와 **그 규칙이 가리는 것**은?

### 9. 약한 심볼은 해결책인가 (경계) ★★

- ★★ 9번 줄이 링크된다는 것은 **무엇을 약속하고 무엇을 약속하지 않는가**?
- ★ 약한 심볼은 표준 C 인가?

### 10. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러·링커 구현** 칸에 각각 무엇이 들어가는가?
- ★★★ 이 편의 모든 파일이 **`-c` 를 경고 없이 통과**한다면, 그 사실은 무엇을 뜻하는가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **헤더에 무엇을 두나**(배치 격자) · **`inline` 의 링크** · **`static`/`extern` 링크 규칙** 은 각각 어디가 정본인가?
- ★ C++ 의 **템플릿 인스턴스화 링크 에러**는 어느 갈래에서 다루나?

## 실행 환경

**환경** — gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0 · GNU ld 2.42(ld.bfd) · ld.gold · x86-64 Linux · glibc 2.39.

★★★ **본체 창은 넷째 창 — 링크 결과 + `nm`** 이다. 1번은 **칸마다 「링크 성공 / `undefined reference` / `multiple definition`」**, 2번은 **파일마다 글자**를 적어야 답이다.
★★ **헤더에 무엇을 두면 깨지나**(헤더 내용 14 × 빌드 5 격자)는 [44번 형제](../44-headers-and-separate-compilation/)가 이미 쟀다 — 여기는 그 에러를 **받아서 거꾸로 읽는** 쪽이다.
선행 — [44번 형제](../44-headers-and-separate-compilation/) · [29번 형제](../29-scope-and-linkage-static-extern/) · [34번 형제](../34-function-declarations-definitions-and-prototypes/).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
