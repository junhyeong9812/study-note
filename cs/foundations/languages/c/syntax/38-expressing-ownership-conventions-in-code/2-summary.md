# c/syntax/38 — 소유권 관례를 코드로 표현하기: 「**C 의 타입은 「누가 놓나」를 말하지 않는다 — 이름·주석·문서가 말하고, 도구는 그 말을 들을 때만 돕는다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `strdup` 의 「**`malloc` 으로 잡은 것처럼 잡은 공간에 복사하고 · 돌려준 포인터는 `free` 에 넘길 수 있다**」, `getenv` 의 「**가리키는 문자열을 프로그램이 고치면 안 되고 · 다음 `getenv` 호출이 덮어쓸 수 있다**」, `strtok` 의 「**토큰의 첫 글자를 가리키는 포인터**」, `free` 의 「**메모리 관리 함수가 돌려준 포인터가 아니면 UB**」, 부록의 바뀐 점 목록 「**integration of functions: … strdup, strndup**」를 **본문에서 직접 찾아 읽었다**) · 이 머신의 **`man 3 strdup` · `getenv` · `strerror` · `strtok`**(글자째 캡처)
> ★ **표준 조항 번호는 인용하지 않는다.** 판정의 근거는 **문서**이고, **도구가 무엇을 잡나는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★★ **본체는 시그니처 판정표다** — 선언 10 개 × 「호출자가 놓나 · 무엇으로 · 근거」. ★★ **판정은 문서가 정본**이고, 도구 격자는 **판정을 어겼을 때 무엇이 잡나**를 본다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — **`strdup` 은 C23 에서 표준에 들어왔다**(그 전에는 POSIX). ★ **gcc 의 `__attribute__((malloc(해제함수)))`** 는 컴파일러 확장이다 — 이 문서는 **gcc-12 · gcc 13 · clang 18** 에서 던졌다.
> ★★ **경계** — **`malloc` 계열의 계약과 실패 처리**는 [37번 형제](../37-malloc-calloc-realloc-free/), **불완전 타입으로 내부를 숨기는 법**은 [25번 형제](../25-incomplete-types-and-opaque-struct/)(그쪽 `ctr_new`/`ctr_free` 가 이 편의 「만든 쪽이 놓는 짝」의 첫 사례다)가 정본이다. **해제 후 사용 · 댕글링의 코드 패턴**은 목록의 **57번 주제**다.
> 선행 — [37번 형제](../37-malloc-calloc-realloc-free/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창이 아니라 「문서」다.** C 의 선언은 `char *` 를 돌려준다고만 말한다 — **그것을 놓아야 하는지**는 선언 밖에 있다. 이 편은 선언 10 개를 놓고 **문서를 근거로 판정한 뒤**, 그 판정을 **어기는 코드**를 세 도구 창에 던진다.
★★★ 결과 — **타입만으로 판정이 서는 칸은 0 / 10** 이었고, **어긴 코드 여섯 가지 중 ASan 이 답한 칸은 11 / 12** 였다. 그 한 칸의 빈자리와 **ASan 자신이 죽은 두 칸**이 이 편의 가장 중요한 칸이다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ★★★ ⓪ **문서** | ★ **본체** — N3220 · `man` 이 「놓나」를 말한다 | 씀 |
| ① 컴파일 진단 | ★★ `strdup` 의 판 경계(암시적 선언) · **`-Wmismatched-dealloc`**(짝을 선언했을 때) · `-fanalyzer` · clang 의 속성 에러 | 씀 |
| ② 실행 출력 | ★ 보통 빌드의 `exit`(glibc 의 `abort` · SEGV) | 씀 |
| ★★★ ③ sanitizer | ★★★ **관례를 어긴 여섯 경우 × gcc/clang ASan** — 리포트 전문 | 씀 |
| ④ 어셈블리 | — | 부적용(소유권은 **기계어에 흔적이 없다** — 같은 `call free` 다) |
| ★ 제5의 상태 | 「이 포인터를 놓아야 하나」를 **타입에게 물으면 답이 없다** — `strdup` 과 `getenv` 는 **같은 모양 `char *`** 에 **반대 답**이다. **이름 · 주석 · 속성으로 바꿔 물었다** — 그리고 속성으로 물었을 때만 **컴파일러가 대답했다** | 창을 바꿔 답함 |

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
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ASan·LSan 리포트의 **PID** · **주소** | 기본 규칙 둘이 지운다 |
| 안 흔들린다 | ★★★ **판정표**(문서) · 위반 격자 · 도구 격자 · 판 격자 | 같은 판이면 같다 |
| 안 흔들린다 | 리포트의 **`파일:줄`** · 종류(`bad-free` · `heap-use-after-free` · `SEGV`) · `Direct leak of 6 byte(s)` | 경로를 죽였다 |

## 한눈에 — 쉽게 말하면

**C 의 포인터는 「주소만 적힌 쪽지」다 — 그 쪽지가 「열쇠」인지 「구경표」인지는 쪽지에 안 적혀 있다.**

- **열쇠를 받으면 반납할 의무가 생긴다** — `strdup` 이 주는 것. 반납 창구도 정해져 있다(`free`). → **소유**
- **구경표는 반납하면 안 된다** — `getenv` 가 주는 것. 반납 창구에 내밀면 **창구가 고장 난다**(`bad-free` · `abort`). → **빌림**
- **맡기고 나면 내 것이 아니다** — `buf_sink(b)` 뒤의 `b`. 다시 반납하면 **이미 없는 것을 반납**한다. → **이전**
- **쪽지 모양이 같으니 겉봉에 글씨를 쓴다** — `_create`/`_destroy` · `_peek` · `char **out` · 주석. → **관례**
- **글씨를 컴파일러가 읽을 수 있게 쓰는 방법이 하나 있다** — `__attribute__((malloc(buf_destroy, 1)))`. 그러면 **틀린 창구에 내밀 때 경고**가 난다(gcc). → **속성**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 같은 쪽지 모양 | `char *strdup(…)` · `char *getenv(…)` | ★★★ **판정표 — 타입만으로 서는 칸 0 / 10** |
| 구경표 반납 | `free(getenv(…))` | ★★★ glibc `abort` · ASan `bad-free`(**스택 주소**) |
| 맡긴 뒤 반납 | `buf_sink(b); buf_destroy(b);` | ★★ 보통 빌드 SEGV · ASan `heap-use-after-free` |
| 열쇠 안 반납 | `buf_get` 의 `*out` 을 안 놓기 | ★★ gcc ASan 은 누수 · **clang ASan 은 리포트 없음** |
| 겉봉 글씨 | `_create`/`_destroy` 짝 | ★★ gcc `-Wmismatched-dealloc` · clang 은 **속성 자체가 에러** |

```text
   선언이 말하는 것                문서가 말하는 것                놓는 법
   ----------------------------   ----------------------------   ----------------
   char *strdup(const char *)     malloc 한 것처럼 · free 가능      free
   char *getenv(const char *)     고치지 마라 · 덮어쓸 수 있다        놓지 않는다
   char *strerror(int)            고치지 마라 · 다음 호출이 무효화    놓지 않는다
   char *strtok(char *, …)        토큰의 첫 글자(인자 문자열 안)      놓지 않는다
             ▲ 네 줄의 반환 타입이 한 글자도 같다
```

- ★★★ **이 주제의 본체는 「표준」 칸이 거의 비어 있다는 사실**이다 — 표준은 **라이브러리 함수마다 문장으로** 소유를 적을 뿐, **언어 차원의 소유 개념이 없다.** 내가 만든 API 의 소유는 **표준 밖(관례)** 이다.
- ★★ **「UB」 칸이 그 관례를 어긴 대가**다 — 빌린 것을 `free` · 이전한 것을 다시 놓기 · 놓은 뒤 쓰기.
- ★★ **「컴파일러 구현」 칸에 유일한 기계적 도움**이 있다 — gcc 의 짝 속성.

> **소유(ownership)** — 「이 블록을 **놓을 책임**이 누구에게 있나」. C 언어에는 이 개념이 없고 **문서와 관례**에만 있다.\
> 예: `strdup` 이 돌려준 포인터의 주인은 호출자다.

> **빌림(borrow)** — 놓을 책임 없이 **잠시 가리키는 것**. 원래 주인이 살아 있고 바꾸지 않는 동안만 유효하다.\
> 예: `getenv` 의 반환 · `buf_peek` 의 반환.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **함수 선언만 보고 「누가 놓나」를 판정할 수 있나** — 없다면 무엇을 보고 판정하나.
2. ★★★ **관례를 어기면 무엇이 잡나** — 보통 빌드 · gcc/clang ASan · 컴파일 경고 · 분석기.
3. ★★ **관례를 컴파일러가 읽게 만들 수 있나** — `__attribute__((malloc(…)))` 와 그 한계 · C++ 과 Rust 는 무엇을 하나.

## 동작 방식

### (1) ★★★ 시그니처 판정표 — 선언 열 개

**언제 쓰나** — 처음 보는 함수가 포인터를 돌려주거나 받을 때. ★★★ **이 편의 본체**다.

```c
/* s38sig.h */
#include <stddef.h>
#include <stdio.h>

typedef struct buf buf;

char       *strdup(const char *s);
char       *getenv(const char *name);
char       *strerror(int errnum);
char       *strtok(char *s, const char *delim);
void       *realloc(void *ptr, size_t size);
FILE       *fopen(const char *path, const char *mode);
buf        *buf_create(size_t cap);
const char *buf_peek(const buf *b);
int         buf_get(const buf *b, char **out);
void        buf_sink(buf *b);
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fsyntax-only -x c s38sig.h (cc exit=0) =====
```

★ 이 목록은 **실제로 컴파일되는 선언**이다(`-fsyntax-only` · 경고 0). 판정은 아래 문서가 근거다.

| 선언 | 반환(또는 출력)을 호출자가 놓나 | 무엇으로 | 근거 |
|---|---|---|---|
| `char *strdup(const char *s)` | ★★★ **놓는다** | `free` | N3220 「돌려준 포인터는 `free` 에 넘길 수 있다」 · `man`「`malloc(3)` 으로 얻고 `free(3)` 으로 놓을 수 있다」 |
| `char *getenv(const char *name)` | ★★★ **놓지 않는다** | — | N3220 「프로그램이 고치면 안 된다 · 다음 `getenv` 가 덮어쓸 수 있다」 · `man`「환경 안의 값을 가리키는 포인터」 |
| `char *strerror(int errnum)` | ★★ **놓지 않는다** | — | `man`「고치면 안 된다 · 다음 `strerror` 호출에 무효가 된다」 |
| `char *strtok(char *s, const char *delim)` | ★★ **놓지 않는다**(인자 문자열 안을 가리킨다) | — | N3220 「토큰의 첫 글자를 가리키는 포인터」 · `man` 은 구분자 자리를 널로 덮는다고 적는다 |
| `void *realloc(void *ptr, size_t size)` | ★★ **성공하면 `ptr` 을 가져가고 새것을 준다 · 실패하면 `ptr` 은 그대로 호출자의 것** | `free` | [37번 형제](../37-malloc-calloc-realloc-free/) |
| `FILE *fopen(const char *path, const char *mode)` | ★★ **놓는다 — `free` 가 아니다** | `fclose` | 표준의 스트림 규칙(★ 이 편은 `fopen` 을 던지지 않았다) |
| `buf *buf_create(size_t cap)` | ★★ **놓는다** | `buf_destroy` | 내 헤더의 주석 |
| `const char *buf_peek(const buf *b)` | ★★ **놓지 않는다**(빌림) | — | 내 헤더의 주석 |
| `int buf_get(const buf *b, char **out)` | ★★ **성공(0)이면 `*out` 을 놓는다** · 실패면 `*out` 은 `NULL` | `free` | 내 헤더의 주석 |
| `void buf_sink(buf *b)` | ★★ **`b` 를 가져간다** — 부른 뒤 쓰지도 놓지도 않는다 | — | 내 헤더의 주석 |

그림 해설 (한 단계씩):

- ★★★ **`char *` 를 돌려주는 넷 중 놓아야 하는 것은 하나(`strdup`)** 다 — 네 선언의 반환 타입이 **한 글자도 같다.** **타입만으로 판정이 서는 칸 0 / 10.**
- ★★ **`const` 는 힌트일 뿐이다** — `buf_peek` 의 `const char *` 는 「고치지 마라 → 아마 빌림」을 암시하지만, **`getenv`·`strerror` 는 고치면 안 되는데도 `char *`** 다(역사적 선언). 반대로 `const` 를 돌려주면서 소유를 넘기는 API 도 만들 수 있다.
- ★★ **매개변수 쪽도 같다** — `buf_sink(buf *)` 와 `buf_peek(const buf *)` 는 **포인터 하나를 받는다**는 점에서 같고, 하나는 가져가고 하나는 빌린다.
- ★★ **그래서 판정의 근거는 전부 「문서」 칸**에 있다 — 표준 함수는 N3220·`man`, 내 함수는 **내 헤더의 주석**.

```text
===== MANWIDTH=80 man 3 strdup | sed -n '/^RETURN VALUE/,/^ERRORS/p;/^STANDARDS/,/^HISTORY/p' | grep -v -E '^(ERRORS|HISTORY)' (exit=0) =====
RETURN VALUE
       On success, the strdup() function returns a pointer to  the  duplicated
       string.  It returns NULL if insufficient memory was available, with er‐
       rno set to indicate the error.

STANDARDS
       strdup()
       strndup()
              POSIX.1-2008.

       strdupa()
       strndupa()
              GNU.

```

```text
===== MANWIDTH=80 man 3 getenv | sed -n '/^RETURN VALUE/,/^ATTRIBUTES/p' | grep -v '^ATTRIBUTES' (exit=0) =====
RETURN VALUE
       The getenv() function returns a pointer to the value  in  the  environ‐
       ment, or NULL if there is no match.

```

```text
===== MANWIDTH=80 man 3 strerror | sed -n '/^DESCRIPTION/,/^$/p' (exit=0) =====
DESCRIPTION
       The strerror() function returns a pointer to a  string  that  describes
       the  error  code  passed  in  the  argument  errnum, possibly using the
       LC_MESSAGES part of the current locale to select the  appropriate  lan‐
       guage.   (For  example,  if  errnum is EINVAL, the returned description
       will be "Invalid argument".)  This string must not be modified  by  the
       application,  and  the returned pointer will be invalidated on a subse‐
       quent call to strerror() or strerror_l(), or if  the  thread  that  ob‐
       tained  the  string  exits.   No other library function, including per‐
       ror(3), will modify this string.

```

```text
===== MANWIDTH=80 man 3 strtok | sed -n '/^RETURN VALUE/,/^ATTRIBUTES/p' | grep -v '^ATTRIBUTES' (exit=0) =====
RETURN VALUE
       The  strtok() and strtok_r() functions return a pointer to the next to‐
       ken, or NULL if there are no more tokens.

```

- ★★ **`man 3 strdup` 의 STANDARDS 는 `POSIX.1-2008` 만** 적는다 — 이 머신의 문서는 **C23 편입을 아직 모른다.** N3220 에는 `strdup` 절이 있고 부록의 바뀐 점 목록이 「integration of functions: … strdup, strndup」이라고 적는다. **문서도 판이 있다.**

### (2) ★★ 내 API 의 관례 — 이름 · 주석 · 속성

**언제 쓰나** — 불투명 타입을 만들어 내놓을 때([25번 형제](../25-incomplete-types-and-opaque-struct/)의 `ctr_new`/`ctr_free` 가 같은 모양이다).

```c
/* s38buf.h */
#ifndef S38BUF_H
#define S38BUF_H
#include <stddef.h>

/* 소유권 표기 규칙 (이 헤더의 약속)
 *   _create        : 새 객체를 만든다 — 호출자가 소유하고 짝인 _destroy 로 놓는다
 *   _destroy       : 소유한 것을 놓는다 — NULL 이면 아무것도 안 한다
 *   _peek          : 빌려준다 — 객체가 살아 있고 바뀌지 않는 동안만 유효, 놓지 않는다
 *   char **out     : 성공(0)이면 *out 은 호출자 소유 — free 로 놓는다 · 실패면 *out 은 NULL
 *   _sink          : 인자를 가져간다 — 부른 뒤 호출자는 그 포인터를 쓰지도 놓지도 않는다
 */
typedef struct buf buf;

void buf_destroy(buf *b);

#if defined(__GNUC__) && !defined(__clang__) && __GNUC__ >= 11
#define BUF_OWNED __attribute__((malloc, malloc(buf_destroy, 1)))
#else
#define BUF_OWNED
#endif

BUF_OWNED buf *buf_create(size_t cap);
const char    *buf_peek(const buf *b);
int            buf_get(const buf *b, char **out);
void           buf_sink(buf *b);

#endif
```

```c
/* s38buf.c */
#include <stdlib.h>
#include <string.h>
#include "s38buf.h"

struct buf { size_t cap; char *data; };

buf *buf_create(size_t cap) {
    buf *b = malloc(sizeof *b);
    if (!b) return NULL;
    b->data = calloc(cap + 1, 1);
    if (!b->data) { free(b); return NULL; }
    b->cap = cap;
    memcpy(b->data, "hello", cap < 5 ? cap : 5);
    return b;
}

void buf_destroy(buf *b) {
    if (!b) return;
    free(b->data);
    free(b);
}

const char *buf_peek(const buf *b) { return b->data; }

int buf_get(const buf *b, char **out) {
    *out = NULL;
    char *s = malloc(strlen(b->data) + 1);
    if (!s) return -1;
    strcpy(s, b->data);
    *out = s;
    return 0;
}

void buf_sink(buf *b) { buf_destroy(b); }
```

- ★★★ **다섯 접미사가 다섯 규칙이다** — `_create`(소유 · 짝으로 놓는다) · `_destroy`(놓는다 · 널이면 아무것도 안 한다) · `_peek`(빌림) · `char **out`(성공 시 소유 이전) · `_sink`(인자를 가져간다).
- ★★ **규칙을 헤더 첫머리에 한 번 적었다** — 함수마다 주석을 흩으면 **어긴 곳을 찾기 어렵다.**
- ★★ **`BUF_OWNED` 매크로가 gcc 11 이상에서만** `__attribute__((malloc, malloc(buf_destroy, 1)))` 로 펼쳐진다 — 이유는 (5).
- ★ **`buf_destroy(NULL)` 을 안전하게 만든 것**은 `free(NULL)` 의 약속([37번 형제](../37-malloc-calloc-realloc-free/))을 **내 짝에도 옮긴** 것이다.
- ★ **`buf_get` 은 실패하면 `*out = NULL`** 로 둔다 — 호출자가 **성공 여부와 무관하게 `free(*out)`** 할 수 있게.

### (3) ★★★ 관례를 어기면 — 여섯 경우 × 세 실행

**언제 쓰나** — 「어기면 도구가 잡겠지」를 확인할 때.

```c
/* s38v.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "s38buf.h"

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int k = argc > 1 ? atoi(argv[1]) : 0;
    buf *b = buf_create(8);
    if (!b) return 1;
    char *s = NULL;
    switch (k) {
    case 0:                                   /* 헤더의 약속대로 */
        if (buf_get(b, &s) == 0) { printf("[0] %s\n", s); free(s); }
        printf("[0] %s\n", buf_peek(b));
        buf_destroy(b);
        break;
    case 1:                                   /* _get 의 *out 을 놓지 않는다 */
        if (buf_get(b, &s) == 0) printf("[1] %s\n", s);
        buf_destroy(b);
        break;
    case 2:                                   /* _sink 뒤에 _destroy */
        buf_sink(b);
        buf_destroy(b);
        break;
    case 3: {                                 /* getenv 결과를 free */
        char *home = getenv("PATH");
        printf("[3] getenv 가 NULL 인가 %d\n", home == NULL);
        free(home);
        buf_destroy(b);
        break;
    }
    case 4:                                   /* _create 의 결과를 free */
        free(b);
        break;
    case 5: {                                 /* _peek 결과를 _destroy 뒤에 */
        const char *v = buf_peek(b);
        buf_destroy(b);
        printf("[5] %d\n", v[0] == 'h');
        break;
    }
    case 6: {                                 /* strerror 결과를 free */
        char *m = strerror(2);
        printf("[6] strerror 가 NULL 인가 %d\n", m == NULL);
        free(m);
        buf_destroy(b);
        break;
    }
    }
    return 0;
}
```

```text
===== 관례를 어기면 — 경우 7 × 실행 3 (s38v.c + s38buf.c · -std=c17 -O0) (exit=0) =====
경우	보통 실행	gcc ASan	clang ASan
[0]	exit=0 	exit=0 리포트 없음	exit=0 리포트 없음
[1]	exit=0 	exit=1 LeakSanitizer: detected memory leaks	exit=0 리포트 없음
[2]	exit=139 	exit=1 AddressSanitizer: heap-use-after-free	exit=1 AddressSanitizer: heap-use-after-free
[3]	exit=134 free(): invalid pointer	exit=1 AddressSanitizer: bad-free	exit=1 AddressSanitizer: bad-free
[4]	exit=0 	exit=1 LeakSanitizer: detected memory leaks	exit=1 LeakSanitizer: detected memory leaks
[5]	exit=0 	exit=1 AddressSanitizer: heap-use-after-free	exit=1 AddressSanitizer: heap-use-after-free
[6]	exit=134 munmap_chunk(): invalid pointer	exit=1 AddressSanitizer: SEGV	exit=1 AddressSanitizer: SEGV
관례를 어긴 경우(1~6)에 ASan 이 답한 칸 11 / 12
```

그림 해설 (한 단계씩):

- ★★★ **ASan 이 답한 칸 11 / 12** — 빠진 한 칸은 **[1] 의 clang** 이다. `buf_get` 의 `*out` 을 놓지 않았는데 **clang ASan 은 `exit=0` · 리포트 없음**, gcc ASan 은 `Direct leak`. ★ 이유는 **확정하지 않았다** — LSan 은 종료 시점에 **스택·레지스터에 남은 값**도 뿌리로 보므로, clang `-O0` 판에서 `s` 의 값이 어딘가 남았을 가능성이 크다(**내 추론**).
- ★★★ **[2] 이전한 것을 다시 놓기** — 보통 빌드는 **SEGV(139)**, ASan 은 **double free 가 아니라 `heap-use-after-free`** 를 말했다. `buf_destroy` 가 **놓기 전에 `b->data` 를 읽기** 때문이다 — 첫 사고 지점이 **읽기**다.
- ★★★ **[3] `getenv` 결과를 `free`** — 보통 빌드는 glibc 가 **`free(): invalid pointer`** 로 `abort`(134), ASan 은 **`bad-free`** 와 함께 「**스레드 T0 의 스택에 있는 주소**」라고 말한다 — 이 판에서 환경 문자열은 **프로세스 스택 꼭대기**에 있다.
- ★★ **[4] `_create` 결과를 `free`** — 보통 빌드는 조용하다(`exit=0`). 두 ASan 은 **`b->data` 의 누수**로 잡는다 — **짝을 틀린 것 자체가 아니라 그 결과(안쪽 블록의 누수)** 를 본다.
- ★★ **[5] 빌린 것을 주인이 놓은 뒤 쓰기** — 두 ASan `heap-use-after-free`. 보통 빌드는 조용하다.
- ★★★ **[6] `strerror` 결과를 `free`** — 보통 빌드는 **`munmap_chunk(): invalid pointer`** 로 `abort`, **두 ASan 은 `SEGV`** — ASan 이 **자기 할당기 안에서 죽었다**(아래 리포트). 「답했다」로 셌지만 **`bad-free` 라는 진단은 나오지 않았다.**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s38v.c s38buf.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 1 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
s38v.c: In function ‘main’:
s38v.c:34:9: warning: ‘free’ called on pointer returned from a mismatched allocation function [-Wmismatched-dealloc]
   34 |         free(b);
      |         ^~~~~~~
s38v.c:9:14: note: returned from ‘buf_create’
    9 |     buf *b = buf_create(8);
      |              ^~~~~~~~~~~~~

=================================================================
==1225333==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 6 byte(s) in 1 object(s) allocated from:
    #0 0x7fe31f0fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x5a42962d2ac2 in buf_get s38buf.c:27
    #2 0x5a42962d2628 in main s38v.c:19
    #3 0x7fe31ec2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #4 0x7fe31ec2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #5 0x5a42962d22e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

SUMMARY: AddressSanitizer: 6 byte(s) leaked in 1 allocation(s).
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s38v.c s38buf.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 2 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
s38v.c: In function ‘main’:
s38v.c:34:9: warning: ‘free’ called on pointer returned from a mismatched allocation function [-Wmismatched-dealloc]
   34 |         free(b);
      |         ^~~~~~~
s38v.c:9:14: note: returned from ‘buf_create’
    9 |     buf *b = buf_create(8);
      |              ^~~~~~~~~~~~~
=================================================================
==1225350==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000018 at pc 0x5fb58d8ae9e2 bp 0x7ffc567dc280 sp 0x7ffc567dc270
READ of size 8 at 0x502000000018 thread T0
    #0 0x5fb58d8ae9e1 in buf_destroy s38buf.c:19
    #1 0x5fb58d8ae69c in main s38v.c:24
    #2 0x7af5f2c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7af5f2c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x5fb58d8ae2e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

0x502000000018 is located 8 bytes inside of 16-byte region [0x502000000010,0x502000000020)
freed by thread T0 here:
    #0 0x7af5f30fc4d8 in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52
    #1 0x5fb58d8ae9fd in buf_destroy s38buf.c:20
    #2 0x5fb58d8aeb5f in buf_sink s38buf.c:34
    #3 0x5fb58d8ae68d in main s38v.c:23
    #4 0x7af5f2c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #5 0x7af5f2c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #6 0x5fb58d8ae2e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

previously allocated by thread T0 here:
    #0 0x7af5f30fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x5fb58d8ae8aa in buf_create s38buf.c:8
    #2 0x5fb58d8ae4d5 in main s38v.c:9
    #3 0x7af5f2c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #4 0x7af5f2c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #5 0x5fb58d8ae2e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

SUMMARY: AddressSanitizer: heap-use-after-free s38buf.c:19 in buf_destroy
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s38v.c s38buf.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 3 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
s38v.c: In function ‘main’:
s38v.c:34:9: warning: ‘free’ called on pointer returned from a mismatched allocation function [-Wmismatched-dealloc]
   34 |         free(b);
      |         ^~~~~~~
s38v.c:9:14: note: returned from ‘buf_create’
    9 |     buf *b = buf_create(8);
      |              ^~~~~~~~~~~~~
=================================================================
==1225359==ERROR: AddressSanitizer: attempting free on address which was not malloc()-ed: 0x7ffd9ec16d82 in thread T0
    #0 0x7b96822fc4d8 in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52
    #1 0x5a06c9e5c6ea in main s38v.c:29
    #2 0x7b9681e2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7b9681e2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x5a06c9e5c2e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

Address 0x7ffd9ec16d82 is located in stack of thread T0
SUMMARY: AddressSanitizer: bad-free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52 in free
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s38v.c s38buf.c -o x ; ./x 3 (cc exit=0 · run exit=134) =====
[3] getenv 가 NULL 인가 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s38v.c s38buf.c -o x ; ./x 3 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
free(): invalid pointer
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s38v.c s38buf.c -o x ; ./x 6 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
munmap_chunk(): invalid pointer
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s38v.c s38buf.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 6 2>&1 >/dev/null | sed -n '/^==/,/^SUMMARY/p' (exit=1) =====
=================================================================
==1225708==ERROR: AddressSanitizer: SEGV on unknown address 0x700427dcc76a (pc 0x700428044688 bp 0x7fffd75fa340 sp 0x7fffd75fa300 T0)
==1225708==The signal is caused by a WRITE memory access.
    #0 0x700428044688 in bool __sanitizer::atomic_compare_exchange_strong<__sanitizer::atomic_uint8_t>(__sanitizer::atomic_uint8_t volatile*, __sanitizer::atomic_uint8_t::Type*, __sanitizer::atomic_uint8_t::Type, __sanitizer::memory_order) ../../../../src/libsanitizer/sanitizer_common/sanitizer_atomic_clang.h:81
    #1 0x700428044688 in __asan::Allocator::AtomicallySetQuarantineFlagIfAllocated(__asan::AsanChunk*, void*, __sanitizer::BufferedStackTrace*) ../../../../src/libsanitizer/asan/asan_allocator.cpp:668
    #2 0x700428044688 in __asan::Allocator::Deallocate(void*, unsigned long, unsigned long, __sanitizer::BufferedStackTrace*, __asan::AllocType) ../../../../src/libsanitizer/asan/asan_allocator.cpp:724
    #3 0x7004280fc49b in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:53
    #4 0x5ef77d9ee7dc in main s38v.c:45
    #5 0x700427c2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #6 0x700427c2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #7 0x5ef77d9ee2e4 in _start (x+0x12e4) (BuildId: 5803a71493a1ce02bc2faa94e59ccf77d3108b96)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV ../../../../src/libsanitizer/sanitizer_common/sanitizer_atomic_clang.h:81 in bool __sanitizer::atomic_compare_exchange_strong<__sanitizer::atomic_uint8_t>(__sanitizer::atomic_uint8_t volatile*, __sanitizer::atomic_uint8_t::Type*, __sanitizer::atomic_uint8_t::Type, __sanitizer::memory_order)
==1225708==ABORTING
```

- ★★ **컴파일 단계에서 이미 한 줄이 경고됐다** — 위 블록들 첫머리의 `-Wmismatched-dealloc`(`s38v.c:34` 의 `free(b)`). 헤더가 **짝을 선언했기 때문**이다((4)). 나머지 다섯 경우에는 **컴파일 경고가 없다.**

### (4) ★★ 짝을 선언하면 — `-Wmismatched-dealloc` 과 분석기

**언제 쓰나** — 「`_create` 의 짝을 컴파일러가 알게 할 수 없나」.

```c
/* s38m.c */
#define _POSIX_C_SOURCE 200809L
#include <stdlib.h>
#include <string.h>
#include "s38buf.h"

void wrong_pairs(void) {
    buf *b = buf_create(4);
    free(b);                                  /* _create 의 짝이 아닌 것 */
    char *s = strdup("x");
    buf_destroy((buf *)s);                    /* strdup 의 짝이 아닌 것 */
}
```

```text
===== 짝을 선언한 헤더(s38buf.h)를 쓰는 두 파일 — 도구 6 (-std=c17 -Wall -Wextra -pedantic -c) (exit=0) =====
도구                  	s38m.c	s38v.c
gcc-12                	경고 1 · mismatched 1	경고 1 · mismatched 1
gcc                   	경고 1 · mismatched 1	경고 1 · mismatched 1
clang                 	경고 0 · mismatched 0	경고 0 · mismatched 0
gcc-12 -fanalyzer     	경고 3 · mismatched 3	경고 2 · mismatched 2
gcc -fanalyzer        	경고 3 · mismatched 3	경고 2 · mismatched 2
clang --analyze       	경고 0 · mismatched 0	경고 0 · mismatched 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s38m.c -o /dev/null (cc exit=0) =====
s38m.c: In function ‘wrong_pairs’:
s38m.c:8:5: warning: ‘free’ called on pointer returned from a mismatched allocation function [-Wmismatched-dealloc]
    8 |     free(b);                                  /* _create 의 짝이 아닌 것 */
      |     ^~~~~~~
s38m.c:7:14: note: returned from ‘buf_create’
    7 |     buf *b = buf_create(4);
      |              ^~~~~~~~~~~~~
```

```text
===== gcc-12 -std=c17 -Wall -Wextra -pedantic -c s38m.c -o /dev/null (cc exit=0) =====
s38m.c: In function ‘wrong_pairs’:
s38m.c:8:5: warning: ‘free’ called on pointer returned from a mismatched allocation function [-Wmismatched-dealloc]
    8 |     free(b);                                  /* _create 의 짝이 아닌 것 */
      |     ^~~~~~~
s38m.c:7:14: note: returned from ‘buf_create’
    7 |     buf *b = buf_create(4);
      |              ^~~~~~~~~~~~~
```

그림 해설 (한 단계씩):

- ★★★ **gcc-12 와 gcc 13 은 `free(b)` 를 `-Wall` 만으로 잡는다** — `‘free’ called on pointer returned from a mismatched allocation function`. **두 판이 한 글자도 같다.**
- ★★ **그런데 `buf_destroy((buf *)s)` 는 둘 다 안 잡았다** — `mismatched 1` 이다. `strdup` 의 짝(`free`)과 다른 것에 넘겼는데 조용하다. ★★ **이유는 헤더에 있다** — glibc 2.39 의 `strdup` 선언에는 **`__attribute_malloc__` 만** 붙고 짝(`__attr_dealloc_free`)이 없다(아래 두 블록). **짝을 선언하지 않은 함수는 이 경고의 대상이 아니다.**

```text
===== grep -n -A2 'Duplicate S, returning' /usr/include/string.h (exit=0) =====
186:/* Duplicate S, returning an identical malloc'd string.  */
187-extern char *strdup (const char *__s)
188-     __THROW __attribute_malloc__ __nonnull ((1));
--
200:/* Duplicate S, returning an identical alloca'd string.  */
201-# define strdupa(s)							      \
202-  (__extension__							      \
```

```text
===== grep -n -B1 -A3 'define __attr_dealloc(dealloc' /usr/include/x86_64-linux-gnu/sys/cdefs.h (exit=0) =====
706-   allocated by the declared function.  */
707:# define __attr_dealloc(dealloc, argno) \
708-    __attribute__ ((__malloc__ (dealloc, argno)))
709-# define __attr_dealloc_free __attr_dealloc (__builtin_free, 1)
710-#else
711:# define __attr_dealloc(dealloc, argno)
712-# define __attr_dealloc_free
713-#endif
714-
```
- ★★ **clang 은 0** — 헤더의 `BUF_OWNED` 가 clang 에서는 **빈 매크로**다. 가드를 뺐을 때 무슨 일이 나는지가 (5)다.
- ★ **분석기(`-fanalyzer`)는 3 · 2** — 경고가 더 많지만 (6)에서 보듯 **틀린 말도 섞인다.** `clang --analyze` 는 0.

### (5) ★★ clang 에서는 그 속성이 **에러**다

**언제 쓰나** — 헤더를 gcc 와 clang 이 같이 읽을 때.

```c
/* s38attr.c */
typedef struct buf buf;
void buf_destroy(buf *b);
__attribute__((malloc, malloc(buf_destroy, 1))) buf *buf_create(unsigned long cap);
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s38attr.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s38attr.c -o /dev/null (cc exit=1) =====
s38attr.c:3:24: error: 'malloc' attribute takes no arguments
    3 | __attribute__((malloc, malloc(buf_destroy, 1))) buf *buf_create(unsigned long cap);
      |                        ^
1 error generated.
```

- ★★★ **clang 18 은 `'malloc' attribute takes no arguments` 로 `cc exit=1`** — 무시하는 게 아니라 **빌드가 깨진다.** 그래서 (2)의 헤더는 **`__GNUC__ >= 11` 이고 clang 이 아닐 때만** 속성을 펼친다.
- ★ **gcc 13 은 0건**이다. ★ **glibc 자신도 이 속성을 `__GNUC_PREREQ (11, 0)` 으로 가둔다**((4)의 `cdefs.h` 블록) — (2)의 가드가 11 인 근거가 그것이다. **이 문서가 던진 판은 gcc-12·13 뿐**이다.

### (6) ★★ 정의가 같은 번역 단위에 있으면 — 분석기가 짝을 뒤집는다

**언제 쓰나** — 「`-fanalyzer` 를 켜면 소유 규칙을 다 봐 준다」.

```c
/* s38an.c */
#include <stdlib.h>

typedef struct node { int v; } node;
void node_destroy(node *n);
__attribute__((malloc, malloc(node_destroy, 1))) node *node_create(int v);

node *node_create(int v) {                    /* 정의가 같은 번역 단위에 있다 */
    node *n = malloc(sizeof *n);
    if (n) n->v = v;
    return n;
}
void node_destroy(node *n) { free(n); }

int use(void) {
    node *n = node_create(7);
    if (!n) return -1;
    int v = n->v;
    node_destroy(n);                          /* 헤더가 말한 짝으로 놓는다 */
    return v;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s38an.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fanalyzer -c s38an.c -o /dev/null | grep -E 'warning:' (cc exit=0) =====
s38an.c:10:12: warning: leak of ‘n’ [CWE-401] [-Wanalyzer-malloc-leak]
s38an.c:18:5: warning: ‘n’ should have been deallocated with ‘free’ but was deallocated with ‘node_destroy’ [CWE-762] [-Wanalyzer-mismatching-deallocation]
```

```text
===== gcc-12 -std=c17 -Wall -Wextra -pedantic -fanalyzer -c s38an.c -o /dev/null | grep -E 'warning:' (cc exit=0) =====
s38an.c:10:12: warning: leak of ‘n’ [CWE-401] [-Wanalyzer-malloc-leak]
s38an.c:18:5: warning: ‘n’ should have been deallocated with ‘free’ but was deallocated with ‘node_destroy’ [CWE-762] [-Wanalyzer-mismatching-deallocation]
```

그림 해설 (한 단계씩):

- ★★★ **이 소스는 옳다** — `node_create` 로 만들고 **선언한 짝 `node_destroy`** 로 놓는다. `-Wall` 은 0건이다.
- ★★★ **분석기는 두 판 다 경고 둘을 낸다** — `node_create` 안(10행)을 **`n` 의 누수**라 하고, 18행을 「**`free` 로 놓아야 하는데 `node_destroy` 로 놓았다**」고 한다. **정의 안의 `malloc` 을 보고 짝을 `free` 로 다시 추론**한 것이다.
- ★★ **이것은 도구가 틀린 말을 한 자리**다 — 근거는 종료 코드 `0` 과 **표준 위에서 적법한 코드**라는 사실이다. 분석기의 경고를 **판정으로 쓰지 말고 조사 목록으로** 읽는다.

### (7) ★★ `strdup` 의 판 경계 — 선언이 없으면 반환 타입이 `int` 가 된다

**언제 쓰나** — `-std=c17` 로 빌드하는 코드에서 `strdup` 을 부를 때.

```c
/* s38s.c */
#include <stdlib.h>
#include <string.h>

int main(void) {
    char *s = strdup("hello");
    int ok = s != NULL;
    free(s);
    return !ok;
}
```

```text
===== strdup 을 부르는 파일 — 컴파일러 3 × 판 3 (-Wall -Wextra -pedantic -c s38s.c) (exit=0) =====
컴파일러	-std=c17	-std=c2x	-std=gnu17
gcc-12  	exit=0 경고 2 에러 0	exit=0 경고 0 에러 0	exit=0 경고 0 에러 0
gcc     	exit=0 경고 2 에러 0	exit=0 경고 0 에러 0	exit=0 경고 0 에러 0
clang   	exit=1 경고 0 에러 2	exit=0 경고 0 에러 0	exit=0 경고 0 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s38s.c -o /dev/null (cc exit=0) =====
s38s.c: In function ‘main’:
s38s.c:5:15: warning: implicit declaration of function ‘strdup’; did you mean ‘strcmp’? [-Wimplicit-function-declaration]
    5 |     char *s = strdup("hello");
      |               ^~~~~~
      |               strcmp
s38s.c:5:15: warning: initialization of ‘char *’ from ‘int’ makes pointer from integer without a cast [-Wint-conversion]
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s38s.c -o /dev/null (cc exit=1) =====
s38s.c:5:15: error: call to undeclared function 'strdup'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]
    5 |     char *s = strdup("hello");
      |               ^
s38s.c:5:15: note: did you mean 'strcmp'?
/usr/include/string.h:156:12: note: 'strcmp' declared here
  156 | extern int strcmp (const char *__s1, const char *__s2)
      |            ^
s38s.c:5:11: error: incompatible integer to pointer conversion initializing 'char *' with an expression of type 'int' [-Wint-conversion]
    5 |     char *s = strdup("hello");
      |           ^   ~~~~~~~~~~~~~~~
2 errors generated.
```

그림 해설 (한 단계씩):

- ★★★ **`-std=c17` 에서 glibc 의 `string.h` 는 `strdup` 을 선언하지 않는다** — 엄격한 표준 모드에서 **POSIX 확장을 숨기기** 때문이다. `-std=c2x` 와 `-std=gnu17` 에서는 선언된다(경고 0).
- ★★★ **gcc 는 경고 2 · `cc exit=0`** — 암시적 선언(반환 `int`) + **`int` 를 `char *` 로** 바꾼다는 경고. **빌드가 된다.** clang 은 **에러 2 · `exit=1`**.
```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors -c s38s.c -o /dev/null (cc exit=1) =====
s38s.c: In function ‘main’:
s38s.c:5:15: error: implicit declaration of function ‘strdup’; did you mean ‘strcmp’? [-Wimplicit-function-declaration]
    5 |     char *s = strdup("hello");
      |               ^~~~~~
      |               strcmp
s38s.c:5:15: error: initialization of ‘char *’ from ‘int’ makes pointer from integer without a cast [-Wint-conversion]
```

- ★★ **`-pedantic-errors` 를 주면 gcc 도 `cc exit=1`** 이다 — 경고 둘이 에러 둘이 된다. 「**`-pedantic` 은 경고, `-pedantic-errors` 라야 막힌다**」는 34·25번 형제가 본 모양과 같다.
- ★★ **gcc 판을 실행하면 UB** 다 — 64비트 포인터가 `int` 로 **잘려 돌아올 수 있다.** 그래서 실행 결과는 싣지 않았다. 「소유를 판정하기 전에 **선언이 보이는지부터**」가 이 칸의 교훈이다.

### (8) ★ C++ 과 Rust — 타입이 소유를 말한다

**언제 쓰나** — 「다른 언어는 이 판정을 어디에 두나」.

```cpp
// s38x.cpp
#include <memory>

struct Buf { int n = 0; };

std::unique_ptr<Buf> buf_create() { return std::make_unique<Buf>(); }
void buf_sink(std::unique_ptr<Buf> b) { (void)b; }

int main() {
    auto b = buf_create();
    buf_sink(b);                             // std::move 없이 넘긴다
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s38x.cpp -o /dev/null | grep -E 'error:|note: declared here' (cc exit=1) =====
s38x.cpp:10:13: error: use of deleted function ‘std::unique_ptr<_Tp, _Dp>::unique_ptr(const std::unique_ptr<_Tp, _Dp>&) [with _Tp = Buf; _Dp = std::default_delete<Buf>]’
/usr/include/c++/13/bits/unique_ptr.h:522:7: note: declared here
```

```cpp
// s38x2.cpp
#include <cstdio>
#include <memory>

struct Buf { int n = 0; };

std::unique_ptr<Buf> buf_create() { return std::make_unique<Buf>(); }
void buf_sink(std::unique_ptr<Buf> b) { (void)b; }

int main() {
    auto b = buf_create();
    buf_sink(std::move(b));
    std::printf("buf_sink 뒤 b 가 비었나 = %d\n", b == nullptr);
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s38x2.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
buf_sink 뒤 b 가 비었나 = 1
```

```rust
// s38r.rs
struct Buf {
    n: usize,
}

fn buf_create() -> Buf {
    Buf { n: 8 }
}

fn buf_sink(b: Buf) {
    let _ = b.n;
}

fn main() {
    let b = buf_create();
    buf_sink(b);
    buf_sink(b);
}
```

```text
===== rustc --edition 2021 s38r.rs -o r (rustc exit=1) =====
error[E0382]: use of moved value: `b`
  --> s38r.rs:16:14
   |
14 |     let b = buf_create();
   |         - move occurs because `b` has type `Buf`, which does not implement the `Copy` trait
15 |     buf_sink(b);
   |              - value moved here
16 |     buf_sink(b);
   |              ^ value used here after move
   |
note: consider changing this parameter type in function `buf_sink` to borrow instead if owning the value isn't necessary
  --> s38r.rs:9:16
   |
 9 | fn buf_sink(b: Buf) {
   |    --------    ^^^ this parameter takes ownership of the value
   |    |
   |    in this function
note: if `Buf` implemented `Clone`, you could clone the value
  --> s38r.rs:1:1
   |
 1 | struct Buf {
   | ^^^^^^^^^^ consider implementing `Clone` for this type
...
15 |     buf_sink(b);
   |              - you could clone this value

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0382`.
```

- ★★★ **C++ 은 `std::unique_ptr<Buf>` 라는 반환 타입이 「소유를 넘긴다」를 말한다** — `buf_sink(b)` 가 **복사 생성자가 삭제됐다**는 에러로 막히고, `std::move(b)` 로 **명시해야** 넘어간다. 넘긴 뒤 `b` 는 **비어 있다**(`= 1`). [C++ 26 — `unique_ptr` 과 소유권 이전](../../../cpp/syntax/26-unique-ptr-and-ownership-transfer/)이 정본이다.
- ★★★ **Rust 는 값으로 받는 매개변수(`b: Buf`)가 곧 이전**이고, 두 번째 사용을 **`E0382` 로 컴파일러가 막는다.** 진단이 「**이 매개변수가 값의 소유권을 가져간다**」고 **C 의 헤더 주석이 하던 말**을 한다. [Rust 08 — 소유권과 이동](../../../rust/syntax/08-ownership-and-move/)이 정본이다.
- ★★ **C 에서 같은 말을 하는 것은 주석뿐**이다 — `void buf_sink(buf *b)` 는 **`buf_peek(const buf *b)` 와 기계어가 구별되지 않는다.**

## 문법 — 형태와 규칙

### 형태

(2)의 `s38buf.h` 가 이 절의 **실제로 컴파일되는 형태**다. 관례를 한 줄씩:

| 쓴 꼴 | 뜻 | 층 |
|---|---|---|
| `T *t_create(…); void t_destroy(T *);` | ★★★ **만든 쪽의 짝으로 놓는다** | 관례 |
| `void t_destroy(T *t) { if (!t) return; … }` | 널을 받으면 아무것도 안 한다 | 관례(`free` 를 본뜸) |
| `const char *t_peek(const T *);` | 빌림 — 주인이 살아 있는 동안만 | 관례 |
| `int t_get(const T *, char **out);` | 성공(0)이면 `*out` 소유 이전 · 실패면 `*out = NULL` | 관례 |
| `void t_sink(T *);` | 인자를 가져간다 | 관례 |
| `__attribute__((malloc, malloc(t_destroy, 1)))` | 짝을 컴파일러에게 알린다 | ★ gcc 확장 — clang 18 은 에러 |
| 헤더 첫머리의 규칙 주석 | 규칙을 한 곳에 | 관례 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `free(getenv("PATH"))` | 경고 0 · glibc `abort`(134) · ASan `bad-free`(스택 주소) | ★★★ UB | (3) |
| `free(strerror(2))` | 경고 0 · glibc `abort`(134) · ★ **ASan 자신이 `SEGV`** | ★★★ UB | (3) |
| `t_sink(b); t_destroy(b);` | 경고 0 · SEGV(139) · ASan `heap-use-after-free` | ★★★ UB | (3) |
| `free(t_create(…))` | ★ **짝 속성이 있으면 gcc `-Wmismatched-dealloc`** · 실행은 조용 · ASan 은 안쪽 누수 | ★★ 적법하지만 누수(관례 위반) | (3)·(4) |
| `t_get` 의 `*out` 을 안 놓기 | 경고 0 · gcc ASan 누수 · **clang ASan 침묵** | ★★ 적법하지만 누수 | (3) |
| `-std=c17` 에서 `strdup` | gcc 경고 2 · **`cc exit=0`** · clang 에러 | ★★ C17 의 제약 위반(암시적 선언) | (7) |
| clang 에서 `malloc(해제함수, N)` 속성 | **에러** · `exit=1` | ★ 컴파일러 구현 | (5) |

### 규칙 불릿

- ★★★ **포인터를 돌려받으면 문서부터 본다** — 타입은 소유를 말하지 않는다(0 / 10).
- ★★★ **만든 쪽의 짝으로 놓는다** — `strdup`→`free` · `fopen`→`fclose` · `t_create`→`t_destroy`.
- ★★ **빌린 것은 놓지 않고, 주인보다 오래 쥐지 않는다** — `getenv` · `strerror` · `_peek`.
- ★★ **가져가는 함수 뒤에는 그 포인터를 쓰지 않는다** — 필요하면 호출자 쪽 변수를 `NULL` 로.
- ★★ **규칙은 헤더 첫머리에 한 번** · 함수 이름의 접미사로 반복.
- ★ **gcc 라면 짝 속성**을 붙인다 — 단 clang 에서는 가드가 필요하다.

## 어디서 틀리나

### 1. ★★★ 「`char *` 를 돌려주니 `free` 하면 된다」

`getenv`·`strerror`·`strtok` 도 `char *` 다((1)). `free` 하면 **glibc 가 `abort`** 하고 ASan 은 `bad-free` — 또는 **ASan 자신이 죽는다**((3)의 [6]).

### 2. ★★★ 「ASan 을 돌렸으니 누수는 없다」

**clang ASan 이 [1] 의 누수를 놓쳤다**((3)). LSan 은 **남은 값을 뿌리로 본다** — 침묵은 증거가 아니다.

### 3. ★★ 「double free 면 ASan 이 `double-free` 라고 말하겠지」

`buf_destroy` 처럼 **놓기 전에 안을 읽는 해제 함수**는 첫 사고가 **읽기**다 — ASan 은 `heap-use-after-free` 라고 말했다((3)의 [2]).

### 4. ★★ 「`-fanalyzer` 가 짝을 틀렸다고 하니 고쳐야 한다」

**정의가 보이면 분석기가 짝을 `free` 로 다시 추론**했다((6)). 옳은 코드에 경고 둘이다.

### 5. ★★ 「속성은 모르는 컴파일러가 무시한다」

**clang 18 은 에러**로 막는다((5)).

### 6. ★ 「`strdup` 은 어디서나 선언돼 있다」

`-std=c17` 의 glibc 는 **숨긴다**((7)). gcc 는 **경고만 내고 빌드한다** — 반환이 `int` 로 잘릴 수 있다.

### 7. ★ 「`man` 이 POSIX 라고 하니 표준 C 에는 없다」

**C23 에 들어왔다** — 이 머신의 `man` 이 그것을 아직 모를 뿐이다((1)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 얇다** — 언어에는 소유 개념이 없고, **라이브러리 함수마다 문장으로** 적혀 있을 뿐이다.\
★★ **관례(층 밖)가 본체**이고, **UB 가 그 관례를 어긴 대가**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★ **표준** | 어느 구현에서도 같다 | ★★ **함수별 문장** — `strdup` 은 `free` 가능 · `getenv` 는 고치지 말 것 · `strtok` 은 토큰 첫 글자 · ★★★ **`free` 에 메모리 관리 함수가 준 것이 아닌 포인터를 넘기면 UB** · C23 의 `strdup` 편입 | N3220 본문 · 부록 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** — ★ 단 `strdup` 이 보이느냐는 **기능 검사 매크로(glibc)** 에 달렸다((7) — 구현 쪽) | 판 격자 |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★ **환경 문자열이 스택에 있다**(이 판) · `strerror` 문자열의 자리 · glibc 의 `free(): invalid pointer` 검사 · `-std=c17` 에서 POSIX 선언을 숨김 | ASan `located in stack` · `abort` |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★★ **`malloc(해제함수, N)` 속성** — gcc 는 받고 `-Wmismatched-dealloc` 을 낸다 · clang 18 은 **에러** · 분석기의 짝 재추론 | 도구 격자 · (5)·(6) |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **빌린 포인터 `free`** · **이전한 포인터 다시 놓기** · **주인이 놓은 뒤 빌린 것 쓰기** · 암시적 선언으로 잘린 포인터 쓰기 | 위반 격자 · 리포트 전문 |

★ **층 밖 — 관례** 칸: `_create`/`_destroy` · `_peek` · `char **out` · `_sink` · 헤더 첫머리의 규칙. **표준도 컴파일러도 이것을 모른다** — 속성을 붙이지 않는 한.

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★ **표준** | ★★★ **「이 포인터를 놓아야 하나」를 판정하는 도구는 없다** — 문서만 판정한다(0 / 10) |
| ★★ **구현 정의** | ★ `man` 이 `strdup` 의 C23 편입을 모른다 — **문서도 낡는다** |
| ★★ **컴파일러 구현** | ★★ **짝 속성은 gcc 에만** 있고, 있어도 `buf_destroy((buf *)strdup(…))` 는 **안 잡았다** · ★★ 분석기는 **옳은 코드에 경고**했다 |
| ★★★ **UB** | ★★ **clang ASan 의 누수 침묵**([1]) · ★★ **ASan 이 `strerror` 결과 `free` 에서 스스로 `SEGV`**([6]) · 보통 빌드는 [1]·[4]·[5] 에 **`exit=0`** |
| ★★ **(층을 가로지름)** | ★★ **「종료 코드 0인데 ill-formed」 항목 하나** — gcc 의 `-std=c17` `strdup`(clang 이 「ISO C99 and later do not support implicit function declarations」라고 적는 호출인데 gcc 는 경고 둘에 `cc exit=0` · **`-pedantic-errors` 라야 `exit=1`**) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **판정은 문서가 하고 도구는 위반의 결과만 본다** — 그것도 **결과가 메모리 사고일 때만.**
  - ★★ **짝을 컴파일러에게 알리는 유일한 길(gcc 속성)이 가장 이른 경고**였다 — 실행 전에, 누수가 나기 전에.
  - ★★ **ASan 은 「잡는다」보다 「그 판에서 그 경로를 지났을 때 잡을 수 있다」** — 침묵(clang [1])도, 자기 사고([6])도 있었다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 새 객체를 내놓기 | ★★★ **`t_create`/`t_destroy` 짝** + 헤더 첫머리 규칙 + (gcc) 짝 속성 | 「`free` 로 놓으세요」 |
| 내부 문자열 보여 주기 | ★★ **`const char *t_peek(const T *)`** + 수명 주석 | 내부 버퍼를 `char *` 로 |
| 호출자에게 새 문자열 주기 | ★★ **`int t_get(…, char **out)`** · 실패 시 `*out = NULL` | 반환값 하나에 실패와 소유를 섞기 |
| 인자를 가져가기 | ★★ **`_sink`·`_take` 같은 이름** + 「부른 뒤 쓰지 마라」 | 이름 없이 조용히 `free` |
| 표준 함수의 반환 | ★★ **`man` 과 표준 문장을 본다** | 반환 타입으로 추측 |
| 여러 컴파일러 | ★ **속성은 가드 매크로로** | 가드 없는 `malloc(해제함수, N)` |

판단 규칙 두 줄.

- ★★★ **포인터를 받는 모든 자리에서 「놓는가 · 무엇으로 · 언제까지 유효한가」 셋을 답할 수 있어야 한다** — 답이 문서에 없으면 그 API 가 틀렸다.
- ★★ **컴파일러가 읽을 수 있는 형태(속성)로 한 번 더 적을 수 있으면 적는다** — 가장 이른 경고가 거기서 나온다.

## 핵심 문장

- ★★★ **`strdup`·`getenv`·`strerror`·`strtok` 은 반환 타입이 같고 놓는 규칙은 반대다 — 선언 열 개 중 타입만으로 판정이 서는 칸은 0 이었다.**
- ★★★ **관례를 어긴 여섯 경우에 ASan 은 11 / 12 칸에서 답했다 — 빠진 한 칸은 clang ASan 의 누수 침묵이다.**
- ★★★ **`free(getenv(…))` 는 glibc `abort` · ASan `bad-free`(스택 주소), `free(strerror(…))` 는 ASan 자신이 `SEGV` 로 죽었다.**
- ★★ **이전한 포인터를 다시 놓으면 ASan 은 `double-free` 가 아니라 `heap-use-after-free` 를 말했다 — 해제 함수가 안을 먼저 읽었기 때문이다.**
- ★★ **gcc-12·13 은 `malloc(buf_destroy, 1)` 속성이 있으면 `free(b)` 를 `-Wmismatched-dealloc` 으로 잡았고, clang 18 은 그 속성을 에러로 막았다.**
- ★★ **정의가 같은 번역 단위에 있으면 `-fanalyzer` 가 짝을 `free` 로 다시 추론해 옳은 코드에 경고 둘을 냈다.**
- ★ **`-std=c17` 에서 `strdup` 은 선언되지 않는다 — gcc 는 경고 둘에 빌드하고 clang 은 에러다.**

## 관련 자료

- [37번 형제 — `malloc`/`calloc`/`realloc`/`free`](../37-malloc-calloc-realloc-free/) — ★★★ **선행.** 놓는 함수의 계약(`free(NULL)` · 실패한 `realloc`).
- [25번 형제 — 불완전 타입과 opaque struct](../25-incomplete-types-and-opaque-struct/) — ★★ **`ctr_new`/`ctr_free` 짝**이 먼저 나온 자리. 크기를 숨기면 **짝이 강제**된다.
- [28번 형제 — 저장 기간](../28-choosing-among-four-storage-durations/) — ★ 「함수 밖으로 돌려줄 값」을 `malloc` 해서 넘기는 선택.
- [21번 형제 — 구조체](../21-struct-declaration-initialization-and-designated-initializers/) — ★ 포인터 멤버를 둘 때 누가 놓나.
- [C++ 26 — `unique_ptr` 과 소유권 이전](../../../cpp/syntax/26-unique-ptr-and-ownership-transfer/) — ★★ **타입이 소유를 말하는** 언어.
- [Rust 08 — 소유권과 이동](../../../rust/syntax/08-ownership-and-move/) — ★★ **컴파일러가 소유를 강제하는** 언어.
- 목록의 **57번 주제**(해제 후 사용 · 이중 해제) · 목록의 **58번 주제**(sanitizer).

## 용어 풀이

> **소유 이전(ownership transfer)** — 놓을 책임이 **다른 쪽으로 넘어가는 것**. C 에서는 **이름·주석**으로만 표시한다.\
> 예: `buf_sink(b)` 뒤에는 호출자가 `b` 를 놓지 않는다.

> **출력 매개변수(out parameter)** — 결과를 **포인터가 가리키는 곳에 써 주는** 매개변수. 반환값은 성공 여부에 쓴다.\
> 예: `int buf_get(const buf *b, char **out);`.

> **`-Wmismatched-dealloc`** — gcc 경고. **짝으로 선언된 해제 함수가 아닌 것**으로 놓으면 알린다. `-Wall` 에 들어 있다.\
> 예: `‘free’ called on pointer returned from a mismatched allocation function`.

> **`bad-free`** — ASan 의 리포트 종류. **메모리 관리 함수가 준 적 없는 주소**를 `free` 에 넘겼다.\
> 예: `attempting free on address which was not malloc()-ed`.

> **암시적 함수 선언** — 선언 없이 부른 함수를 `int f()` 로 가정하던 C89 의 규칙. **C99 부터 없다**(clang 진단 문구 — ★ 표준 조항은 이 문서가 열지 않았다).\
> 예: `-std=c17` 에서 `strdup` 을 부르면 gcc 가 `implicit declaration` 경고.

## 더 들어가면

- ★★ **`__attribute__((cleanup(f)))`** — 스코프를 벗어날 때 `f` 를 부르는 gcc·clang 확장. C 에서 C++ 의 소멸자를 흉내 내는 자리다. ★ **던지지 않았다.**
- ★★ **glibc 가 짝을 선언한 함수**(`reallocarray` 가 자기 자신을 짝으로 둔다 — `stdlib.h`) — 그런 함수를 틀린 짝으로 놓으면 `-Wmismatched-dealloc` 이 나는지. ★ **던지지 않았다.**
- ★ **`getenv` 뒤의 `setenv`** — 빌린 포인터가 **다른 호출로 무효가 되는** 자리. ★ **던지지 않았다.**
