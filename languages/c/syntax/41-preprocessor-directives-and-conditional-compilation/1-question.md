# c/syntax/41 — 전처리기 지시자와 조건부 컴파일: 「**전처리기는 컴파일러보다 먼저 도는 텍스트 치환기다 — 컴파일러는 그 결과만 받는다**」 — 질문

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **3번은 칸마다 「그 정의에서 `X` 가 치환되면 무엇이 남나」를 먼저 적고** 그다음 분기를 골라라.
- ★★ **「에러」·「조용히 다른 분기」·「경고 후 처리」를 갈라** 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 글자는 컴파일러에 도착하나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 전처리 결과와 목적 파일에 남는 것 (예측) ★★★

```c
/* s41a.c */
#define LIMIT 10
#define TWICE(x) ((x) * 2)

#ifdef VERBOSE
int verbose_mode = 1;
#endif

int limit_twice(void) { return TWICE(LIMIT); }
```

- ★★★ `gcc -std=c17 -E -P s41a.c` 는 무엇을 찍는가? `-DVERBOSE` 를 더하면?
- ★★ `-P` 를 빼면 무엇이 더 찍히는가? 사라진 지시자 자리는 어떻게 되는가?
- ★★ `gcc -std=c17 -DVERBOSE -c s41a.c -o s41a.o && nm s41a.o` 에는 어떤 이름이 나오는가? `LIMIT`·`TWICE` 는?

### 2. 매크로 안의 오류 — 두 컴파일러가 짚는 줄 (예측) ★★★

```c
/* s41b.c */
#define FIELD(p) ((p)->val)

struct box { int val; };

int get(int n) {
    return FIELD(n);
}
```

- ★★★ gcc 와 clang 은 에러의 **본문 위치**를 각각 몇 행 몇 열로 대는가? 덧붙는 `note:` 는 어디를 가리키는가?
- ★★★ `gcc -std=c17 -E -P s41b.c -o s41b.i` 로 만든 `.i` 를 `gcc -std=c17 -c s41b.i` 로 컴파일하면 진단은 어느 파일 · 몇 행을 가리키는가? 매크로 언급은 남는가?
- ★★ `-P` 없이 만든 `.i` 를 컴파일하면? 보여 주는 소스 줄과 캐럿의 열은 맞는가?

### 3. `#if` 격자 — 식 다섯 × 정의 넷 × 컴파일러 둘 (예측) ★★★ 이 주제의 축

```c
/* s41c.c */
#if FORM == 1
#  if X
branch_1
#  else
branch_2
#  endif
#elif FORM == 2
#  if defined(X)
branch_1
#  else
branch_2
#  endif
#elif FORM == 3
#  ifdef X
branch_1
#  else
branch_2
#  endif
#elif FORM == 4
#  if X == 1
branch_1
#  else
branch_2
#  endif
#endif
```

```c
/* s41c5.c */
#if 0
#elifdef X
branch_1
#else
branch_2
#endif
```

칸 = `$CC -std=<판> -Wall -Wextra -pedantic [-DFORM=<행>] <정의> -E -P <소스>` 가 남긴 `branch_N` 의 N(`-E -P` 가 실패하면 「에러」).
행은 `FORM` 1\~4(`s41c.c`, `-std=c17`) · `s41c5.c` 를 `-std=c17` 과 `-std=c2x` 로. 정의 넷은 **(없음) · `-DX` · `-DX=0` · `-DX="s"`**.

- ★★★ `#if X` · `#if defined(X)` · `#ifdef X` · `#if X == 1` 네 행의 여덟 칸(gcc · clang)은?
- ★★★ `s41c5.c` 의 c17 행과 c2x 행은? **gcc 와 clang 이 갈리는 칸**이 있는가?
- ★★ 어느 칸에 **경고**가 붙는가?

### 4. 미리 정의된 매크로 (예측) ★★

`$CC -std=<판> -dM -E - </dev/null` 로 찍는다.

- ★★★ `__STDC_VERSION__` 은 gcc · clang 각각 `-std=c11` · `c17` · `c2x` 에서 얼마인가?
- ★★ clang 에서 `__GNUC__` 는 정의되는가? 된다면 값은?
- ★★ `linux`·`unix`(밑줄 없음)와 `__linux__` 는 `-std=c17` 과 `-std=gnu17` 에서 각각 있는가?

### 5. `#include "…"` 대 `<…>` (예측) ★★

```c
/* s41i1.c */
#include "s41q.h"
```

```c
/* s41i2.c */
#include <s41q.h>
```

```text
===== head qd/s41q.h id/s41q.h s41q.h (exit=0) =====
==> qd/s41q.h <==
int from_qd;

==> id/s41q.h <==
int from_id;

==> s41q.h <==
int from_here;
```

- ★★★ 옆에 `s41q.h` 가 **있을 때** 플래그 넷(없음 · `-iquote qd` · `-I id` · 둘 다)에서 `s41i1.c` 와 `s41i2.c` 는 각각 어느 파일을 가져오는가?
- ★★★ 옆 파일을 **치운 뒤**에는?
- ★★ 「못 찾음」 칸에서 gcc 와 clang 은 **같이 구는가**? 종료 코드는?

### 6. `#warning` 과 `#error` 의 판과 종료 코드 (예측) ★★

```c
/* s41w.c */
#warning "check the limit"

#ifndef LIMIT
#error "LIMIT is not defined"
#endif

int limit = LIMIT;
```

- ★★ `-std=c17 -pedantic -DLIMIT=3` 으로 gcc · clang 을 돌리면 경고는 몇 줄이고 무엇이라 하는가? `-std=c2x` 로 바꾸면?
- ★★ `-std=c2x` 에서 `-DLIMIT` 를 빼면 **에러가 몇 개** 나오는가? 종료 코드는?

### 7. 정의 안 된 이름은 `#if` 에서 무엇이 되나 (왜) ★★★

- `#if X` 에서 `X` 가 정의 안 됐으면 **에러가 아닌** 이유를 표준의 문장으로 말하라.
- ★★ 그 결과를 보이게 하는 경고는 무엇이고, `-Wall -Wextra` 에 들어 있는가?
- ★ `-DX=abc` 일 때 `#if X == 1` 은 어떻게 평가되는가?

### 8. gcc `-std=c17` 의 `#elifdef` — 침묵과 에러 (경계) ★★★

- 3번의 c17 행에서 gcc 가 **진단 0줄로** 다른 분기를 고른 이유는?
- ★★ 같은 gcc `-std=c17` 이 `#if 1` 뒤의 `#elifdef` 에서는 **에러**를 낸다. 두 자리의 차이를 「건너뛰는 그룹」으로 설명하라.
- ★ `-std=gnu17` 은?

### 9. 전처리 식도 식이다 (왜) ★

- `#if 1 / 0` 은 왜 에러인가? `#if X` 에 `-DX="s"` 는?
- ★ gcc 가 `-DX="s"` 의 에러 위치를 `<command-line>` 으로 대는 이유는?

### 10. Go 에는 전처리기가 없다 (연결) ★

- Go 는 조건부 빌드를 **어느 단위로** 고르는가? Go 갈래 몇 번 주제인가?
- ★ C 의 「한 파일 안 몇 줄을 고른다」가 주는 편리함과 대가는?

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 컴파일러 구현** 칸에 각각 무엇이 들어가는가?
- ★★★ `-Wall -Wextra -pedantic` 으로도 **0줄인 사고** 둘은?
- ★★ `__STDC_VERSION__ >= 202311L` 로 C23 을 판별하면 이 판에서 무엇이 틀리는가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **「전처리 → 컴파일 → 링크」 흐름 일반**은 어느 문서가 정본이고, 그 문서에 **전처리 단계만 다룬 절**이 있는가?
- **함수형 매크로의 함정 · `#`/`##` · include guard** 는 각각 몇 번 형제인가?

## 실행 환경

**환경** — gcc 13.3.0 · gcc-12 12.4.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.

★★★ **본체 창은 전처리 결과** — 3번은 **칸마다 「남은 분기(1 / 2 / 에러)」** 를 적어야 답이다.
선행 — 없음.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
