# c/syntax/39 — `inline` 과 C 의 인라인 규칙: 「**C 의 `inline` 은 「펼쳐라」가 아니라 「이 정의는 외부 정의가 아니다」다 — 그래서 헤더에 두면 링크가 판을 탄다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0 · clang++ 18.1.3 · x86-64 Linux.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **지정자별로 정의가 몇 개, 어떤 링크로 남나**(두 번역 단위 · 헤더) ② **판(C99 대 gnu89)과 언어(C 대 C++)가 무엇을 뒤집나**
> ③ **`inline` 이 보장하지 않는 것**(펼침 · 주소 · 제약).
> ★★★ **본체 창은 링크 격자** — 1번은 **칸마다 「링크 성공 / `undefined reference` / `multiple definition`」** 을 적어야 답이다.
> ★★ **한 번역 단위 안의 세 형태**는 [29번 형제](../29-scope-and-linkage-static-extern/) (8)에서 이미 풀었다 — 여기는 **헤더를 두 파일이 include** 한다.
> 선행 — [29번 형제](../29-scope-and-linkage-static-extern/) · 목록의 **44번 주제**.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·2번은 `-O0` 과 `-O2` 를 따로** 적어라 — 같은 소스의 링크가 **최적화 수준에 따라** 갈리는 칸이 있다.
- ★★ **「컴파일이 통과했다」와 「링크가 통과했다」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 프로그램에서 `twice` 의 외부 정의는 몇 개인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 헤더의 지정자 넷 × 두 번역 단위 (예측) ★★★ 이 주제의 축

```c
/* s39.h */
#ifndef S39_H
#define S39_H

#ifndef KW
#define KW inline                    /* 격자가 -DKW=... 로 바꿔 끼운다 */
#endif

KW int twice(int x) { return 2 * x; }

#endif
```

```c
/* s39a.c */
#include "s39.h"

#ifdef DECL
extern inline int twice(int x);      /* -DDECL 판에서만 들어가는 한 줄 */
#endif

int from_a(int v) { return twice(v); }
```

```c
/* s39b.c */
#include <stdio.h>
#include "s39.h"

int from_a(int v);

int main(void) {
    printf("twice(1) = %d · from_a(20) = %d\n", twice(1), from_a(20));
    return 0;
}
```

`KW` 를 `inline` · `static inline` · `extern inline` 으로 바꾸고, 넷째 줄은 `KW=inline` 에 **`s39a.c` 만 `-DDECL`** 을 준다. `gcc`/`clang` × `-O0`/`-O2` 로 `s39a.c s39b.c` 를 링크한다(`-std=c17`).

- ★★★ 네 줄 × 네 칸, 각 칸의 링크 결과는?
- ★★★ `KW=inline` 줄에서 `-O0` 과 `-O2` 가 갈린다면 **왜 `-O2` 쪽**인가?
- ★★ gcc 와 clang 이 갈리는 칸이 있는가?

### 2. `-fgnu89-inline` 과 `-std=gnu89` (예측) ★★★

같은 네 줄을 `-std=c17 -fgnu89-inline` 과 `-std=gnu89` 로 링크한다.

- ★★★ `KW=inline` 줄과 `KW=extern inline` 줄은 각각 어떻게 되는가?
- ★★ C99 판과 `-fgnu89-inline` 판을 칸끼리 견주면 **몇 칸이 갈리는가**? 안 갈리는 칸은 어느 줄인가?
- ★ `-std=gnu89` 덩어리는 `-fgnu89-inline` 덩어리와 다른가?

### 3. `nm` 이 붙이는 글자 (예측) ★★

gcc 로 `s39a.o` 와 `s39b.o` 를 **따로** 만들고 `nm` 으로 `twice` 의 글자를 본다(`-O0`/`-O2` · C99 판과 gnu89 판).

- ★★ C99 판 네 줄에서 두 파일의 글자는 각각 `T` · `t` · `U` · (없음) 중 무엇인가?
- ★★ gnu89 판에서 **맞바뀌는** 두 줄은?
- ★ `-O2` 의 「(없음)」은 1번의 어느 칸을 설명하는가?

### 4. 같은 파일을 C++ 로 (예측) ★★

같은 `s39a.c`·`s39b.c` 를 `g++ -x c++` · `clang++ -x c++`(`-std=c++17`)로 네 줄 × `-O0`/`-O2` 링크한다.

- ★★ 16 칸의 결과는? 1번과 다른 칸은?
- ★★ `nm -C` 는 두 파일의 `twice(int)` 에 **무슨 글자**를 붙이는가?

### 5. 두 번역 단위의 `&twice` (예측) ★★

```c
/* s39c.c */
#include "s39.h"

#ifdef DECL
extern inline int twice(int x);
#endif

int (*addr_c(void))(int) { return twice; }
```

```c
/* s39d.c */
#include <stdio.h>
#include "s39.h"

int (*addr_c(void))(int);

int main(void) {
    int (*mine)(int) = twice;
    printf("두 번역 단위의 &twice 가 같은가 = %d\n", mine == addr_c());
    return 0;
}
```

- ★★ C 의 `static inline` · C 의 `inline + DECL` · C++ 의 `static inline` · C++ 의 `inline` 에서 **같은가** 줄은 각각 `0` 인가 `1` 인가?
- ★ `-O2` 에서 달라지는 줄이 있는가?

### 6. `static` 을 쓰는 외부 링크 `inline` (예측) ★★

```c
/* s39e.c */
static int hidden = 1;

inline int count_calls(void) {       /* 외부 링크 · inline 만 */
    static int calls;
    return ++calls;
}

inline int read_hidden(void) {       /* 외부 링크 · inline 만 */
    return hidden;
}

int use(void) { return count_calls() + read_hidden(); }
```

- ★★ gcc 와 clang 은 무엇이라고 말하고 `cc exit` 는?
- ★★ `-pedantic-errors` 를 주면 두 컴파일러에서 **에러가 되는 줄**은?

### 7. `-O0` 의 `call twice` (왜) ★★

- ★★ `-O0` 에서 `inline` 함수의 호출이 **남는다면**, 그것은 표준 위반인가? 표준은 `inline` 의 효과를 무엇이라고 적는가?
- ★★★ `-O2` 에서 `call` 이 사라진 것으로 「`inline` 이 빠르다」를 적을 수 있는가?

### 8. `extern inline` 선언 한 줄의 자리 (왜) ★★

- ★★ `extern inline int twice(int);` 한 줄을 넣을 자리로 **헤더와 한 `.c`** 중 어느 쪽이 맞는가? 왜?
- ★ 표준 예제 1 의 `fahr` 와 `cels` 는 이 편의 어느 줄과 같은 모양인가?

### 9. `static inline` 의 대가 (경계) ★★

- ★★ 헤더에 `static inline` 을 두는 선택은 무엇을 잃는가(주소 · 정적 변수 · 코드 크기)?
- ★ `s39e.c` 를 고친 `s39f.c` 는 무엇을 바꿨고, clang 의 남은 경고는 **위반의 판정**인가?

### 10. C++ 의 `inline` 은 왜 다른가 (연결) ★★

- ★★ C 의 인라인 정의와 C++ 의 `inline` 함수가 **여러 번역 단위에 정의가 있을 때** 각각 무엇을 약속하는가?
- ★ C++ 의 `inline` **변수**는 29편 (9)에서 `nm` 이 무슨 글자로 보였는가?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 구현 정의 / 컴파일러 구현 / 미명시** 칸에 각각 무엇이 들어가는가?
- ★★★ 인라인 규칙의 사고가 **컴파일이 아니라 링크에서** 나는 이유는?
- ★★ 이 편의 「**종료 코드 0인데 ill-formed**」 항목은?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **한 번역 단위의 C99 `inline` 세 형태**와 **`static`/`extern` 링크 규칙**은 어느 형제가 정본인가?
- **헤더에 무엇을 두나** · **링크 오류 거꾸로 읽기**는 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
