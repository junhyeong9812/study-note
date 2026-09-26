# c/syntax/38 — 소유권 관례를 코드로 표현하기: 「**C 의 타입은 「누가 놓나」를 말하지 않는다 — 이름·주석·문서가 말하고, 도구는 그 말을 들을 때만 돕는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** ·
> **clang 18.1.3** · **glibc 2.39** · **rustc 1.92.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s38sig.h` · `s38buf.h` · `s38buf.c` · `s38v.c` · `s38m.c` · `s38attr.c` · `s38an.c` · `s38s.c` · `s38x.cpp` · `s38x2.cpp` · `s38r.rs` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
> ★★★ **본체는 판정표(문서)** — 도구 격자는 **판정을 어겼을 때**를 본다.
> ★★ **흔들리는 칸** — 리포트의 PID · 주소. 정규화 규칙은 기본 넷뿐이다.

## 이 파일이 다시 싣는 소스

★ 3번의 격자는 `s38buf.c` 와 함께 빌드한다 — 질문 파일에 없던 그 소스를 싣는다. 6·9번의 진단은 소스 줄을 끼워 보여 주지 않으므로 그 소스를, 10번의 Rust 소스도 여기 싣는다.

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 판정표 — **놓는 것은 `strdup`(`free`) · `realloc`(성공 시) · `fopen`(`fclose`) · `buf_create`(`buf_destroy`) · `buf_get` 의 `*out`(`free`) · 타입만으로 서는 칸 0 / 10** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fsyntax-only -x c s38sig.h (cc exit=0) =====
```

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

| 선언 | 놓나 | 무엇으로 | 근거 |
|---|---|---|---|
| `strdup` | **놓는다** | `free` | N3220 · `man` |
| `getenv` | 놓지 않는다 | — | N3220(고치지 말 것 · 덮어쓸 수 있음) · `man` |
| `strerror` | 놓지 않는다 | — | `man`(고치지 말 것 · 다음 호출에 무효) |
| `strtok` | 놓지 않는다 | — | N3220(토큰의 첫 글자) — 인자 문자열 안 |
| `realloc` | **성공 시 새것을 놓는다** · `ptr` 은 넘어감 · 실패 시 `ptr` 그대로 | `free` | 37번 형제 |
| `fopen` | **놓는다** | `fclose` | 표준의 스트림 규칙 |
| `buf_create` | **놓는다** | `buf_destroy` | 헤더 주석 |
| `buf_peek` | 놓지 않는다 | — | 헤더 주석 |
| `buf_get` | **성공 시 `*out` 을 놓는다** | `free` | 헤더 주석 |
| `buf_sink` | 인자를 가져간다 | — | 헤더 주석 |

**왜 그런가**

- ★★★ **`strdup`·`getenv`·`strerror`·`strtok` 의 반환 타입은 모두 `char *`** 이고 **놓는 것은 하나**다 — 타입은 소유를 싣지 않는다. **근거 칸은 전부 문서**(N3220 · `man` · 내 헤더 주석)다.
- ★★ **`const` 는 보장이 아니다** — `getenv`·`strerror` 는 고치면 안 되는데 `char *` 이고, `buf_peek` 의 `const char *` 는 **관례로 붙인 힌트**다.
- ★ `man 3 strdup` 의 STANDARDS 가 `POSIX.1-2008` 만 적는 것은 **이 머신의 문서가 C23 편입 이전의 것**이기 때문이다(N3220 에는 `strdup` 절이 있다).

### 2. `strdup` 의 판 — **`-std=c17` 에서 gcc 두 판은 `exit=0` 경고 2 · clang 은 `exit=1` 에러 2 · `c2x`·`gnu17` 은 전부 0 · `-pedantic-errors` 면 gcc 도 `exit=1`** ★★

**출력**

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors -c s38s.c -o /dev/null (cc exit=1) =====
s38s.c: In function ‘main’:
s38s.c:5:15: error: implicit declaration of function ‘strdup’; did you mean ‘strcmp’? [-Wimplicit-function-declaration]
    5 |     char *s = strdup("hello");
      |               ^~~~~~
      |               strcmp
s38s.c:5:15: error: initialization of ‘char *’ from ‘int’ makes pointer from integer without a cast [-Wint-conversion]
```

**왜 그런가**

- ★★ **glibc 의 `string.h` 는 `-std=c17`(엄격 모드)에서 `strdup` 을 선언하지 않는다** — 선언은 POSIX/확장 모드나 **C2X 모드**에서 열린다(`gnu17` · `c2x` 칸이 0).
- ★★ **선언이 없으니 gcc 는 암시적 선언(`int strdup()`)을 가정**하고, 그 `int` 를 `char *` 에 넣는다는 경고를 더한다. **빌드는 된다**(`cc exit=0`).
- ★★★ **그 바이너리는 실행하지 않는다** — 64비트 포인터가 `int` 로 돌아오면 **잘릴 수 있는 UB** 다.
- ★ clang 은 같은 호출을 **에러**로, gcc 는 **`-pedantic-errors` 를 줘야** 에러로 막는다.

### 3. 여섯 경우 — **ASan 답한 칸 11 / 12 · 빠진 칸은 [1] clang · [2] 는 `heap-use-after-free` · [3] 은 스택 주소의 `bad-free` · [6] 은 ASan 자신이 `SEGV`** ★★★

**출력**

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

**왜 그런가**

- ★★★ **[1] `*out` 을 안 놓기** — 적법하지만 누수다. gcc ASan 은 **`Direct leak of 6 byte(s)`**(`buf_get` 의 `malloc`), **clang ASan 은 `exit=0` · 리포트 없음.** LSan 은 종료 시점에 **남은 값을 뿌리로 보므로** 침묵이 「누수 없음」을 뜻하지 않는다(clang 칸의 정확한 원인은 확정하지 않았다).
- ★★★ **[2] 이전 뒤 다시 놓기** — ASan 이 말한 종류는 **`heap-use-after-free`** 다. `buf_destroy` 가 **`free(b->data)` 를 위해 `b->data` 를 먼저 읽기** 때문에(`s38buf.c:19`) 첫 사고가 읽기다. 보통 빌드는 **SEGV(139)**.
- ★★★ **[3] `getenv` 결과 `free`** — glibc `free(): invalid pointer` 로 `abort`(134), ASan **`bad-free`** 와 「**`located in stack of thread T0`**」 — 이 판의 환경 문자열은 **스택 꼭대기**에 있다.
- ★★ **[4] `_create` 결과 `free`** — 실행은 조용하고, 두 ASan 이 **안쪽 `data` 의 누수**로 잡는다. 컴파일 때 gcc 가 이미 `-Wmismatched-dealloc` 을 냈다.
- ★★ **[5] 주인이 놓은 뒤 빌린 것 쓰기** — 두 ASan `heap-use-after-free`, 보통 빌드는 조용.
- ★★★ **[6] `strerror` 결과 `free`** — glibc `munmap_chunk(): invalid pointer` 로 `abort`. **두 ASan 은 `SEGV` — 자기 할당기(`Deallocate`) 안에서 죽었다.** 리포트는 나왔지만 **`bad-free` 라는 올바른 진단은 아니다.**
- ★★ **리포트가 없는 칸은 하나**([1] clang) — 그래서 11 / 12.

### 4. `-Wmismatched-dealloc` — **gcc 두 판은 `free(b)` 만 경고 · `buf_destroy((buf *)s)` 는 조용 · clang 0 · 분석기는 3** ★★

**출력**

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

**왜 그런가**

- ★★ **`free(b)` 는 헤더가 `buf_create` 의 짝을 `buf_destroy` 로 선언했기 때문에** 잡혔다(gcc-12·13 한 글자도 같다).
- ★★ **`buf_destroy((buf *)s)` 가 조용한 이유는 glibc 헤더** — `strdup` 의 선언에 **`__attribute_malloc__` 만** 있고 짝(`__attr_dealloc_free`)이 없다. **짝을 모르는 함수는 경고의 대상이 아니다.**
- ★ **clang 은 가드 때문에 속성을 못 받아 0** · `clang --analyze` 도 0 · gcc 분석기는 3(그중에는 (9)와 같은 재추론이 섞일 수 있다).

### 5. 가드 없는 속성 — **gcc 13 `cc exit=0` · clang 18 `'malloc' attribute takes no arguments` 로 `cc exit=1`** ★★

**출력**

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

**왜 그런가**

- ★★ **clang 18 은 인자 있는 `malloc` 속성을 모른다** — 무시가 아니라 **에러**다. 헤더를 두 컴파일러가 같이 읽으면 **빌드가 깨진다.**
- ★ 그래서 `s38buf.h` 는 **`__GNUC__ >= 11` 이고 `__clang__` 이 아닐 때만** 펼친다 — glibc 자신도 `__GNUC_PREREQ (11, 0)` 으로 같은 속성을 가둔다(4번의 `cdefs.h` 블록).

### 6. C++ — **`use of deleted function … unique_ptr(const unique_ptr&)` · 이동 뒤 `b == nullptr` 은 1** ★★

**출력**

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

**왜 그런가**

- ★★ **값으로 받는 `std::unique_ptr<Buf>` 매개변수가 「가져간다」를 타입으로** 말한다 — 복사 생성자가 삭제돼 있어 **몰래 넘길 수 없고**, `std::move` 로 **보이게** 넘겨야 한다.
- ★ 넘긴 뒤 `b` 는 **비어 있다** — C 의 「`_sink` 뒤에는 쓰지 마라」가 **값으로 드러난다**([C++ 26](../../../cpp/syntax/26-unique-ptr-and-ownership-transfer/)).

### 7. 접미사 다섯 — **만든 쪽의 짝 · 빌림 · 성공 시 이전 · 가져감을 이름으로 싣는다** ★★

**왜 그런가**

- ★★ `_create`/`_destroy` — **소유 + 놓는 창구**. `_peek` — **빌림 + 유효 기간**(주인이 살아 있고 안 바뀌는 동안). `char **out` — **성공 시 소유 이전 · 실패 시 `NULL`**. `_sink` — **인자 소유를 가져감**.
- ★★ **규칙을 한 곳에 두면 어긴 자리가 보인다** — 함수마다 흩으면 **이름과 주석이 어긋날 때** 어느 쪽이 맞는지 판정할 기준이 없다. 헤더 첫머리가 **판정표의 정본 칸**이 된다(1번의 「헤더 주석」 근거).

### 8. 출력 매개변수의 실패 — **`*out = NULL` 이면 호출자는 성공 여부와 무관하게 `free(*out)` 할 수 있다** ★★

**왜 그런가**

- ★★ **`free(NULL)` 은 아무 일도 없으므로**([37번 형제](../37-malloc-calloc-realloc-free/)) 실패 경로에서도 **한 줄로 정리**할 수 있다 — 쓰레기 값이 남으면 그 `free` 가 UB 다.
- ★ **`char *` 반환 + 실패 시 `NULL`** 은 실패 이유를 싣지 못하고, **반환 타입이 `getenv` 와 같아져** 소유 판정이 다시 문서로 밀린다. 출력 매개변수는 **반환값을 상태에, 포인터를 소유에** 나눠 쓴다.

### 9. 분석기의 재추론 — **옳은 코드에 `leak of ‘n’`(10행)과 「`free` 로 놓았어야」(18행) 두 경고** ★★

**출력**

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

**왜 그런가**

- ★★ **정의가 같은 번역 단위에 있으니 분석기가 `node_create` 안의 `malloc` 을 따라 들어가** 짝을 `free` 로 다시 정했고, 그래서 선언된 짝 `node_destroy` 를 **틀렸다**고 했다. `node_create` 가 포인터를 **돌려주는** 자리를 누수로 본 것도 같은 추론의 결과로 보인다(★ 분석기 소스로 확인하지 않았다).
- ★ **판정으로 쓰면 옳은 코드를 고치게 된다** — `-Wall` 0건 · 표준 위에서 적법. 분석기 경고는 **조사 목록**이다.

### 10. Rust — **`E0382` 한 번 · 「this parameter takes ownership of the value」** ★★

**출력**

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

**왜 그런가**

- ★★ **값으로 받는 매개변수가 곧 이전**이고, 두 번째 `buf_sink(b)` 를 **컴파일러가 막는다** — `error: aborting due to 1 previous error`.
- ★ **「this parameter takes ownership of the value」** 가 C 의 `_sink` 주석(「인자를 가져간다」)과 같은 말이다 — Rust 는 그 말을 **타입 검사기가 한다**([Rust 08](../../../rust/syntax/08-ownership-and-move/)).

### 11. 다섯 층 — **표준 칸은 함수별 문장뿐 · 관례가 본체 · 판정 도구는 없다** ★★★

**왜 그런가**

- **표준** — `strdup` 은 `free` 가능 · `getenv` 는 고치지 말 것 · `strtok` 은 토큰 첫 글자 · **메모리 관리 함수가 준 것이 아닌 포인터 `free` 는 UB** · C23 `strdup` 편입.
- **구현 정의** — 환경 문자열이 스택에 있음 · glibc 의 `invalid pointer` 검사 · 엄격 모드에서 POSIX 선언 숨김.
- **컴파일러 구현** — gcc 의 짝 속성과 `-Wmismatched-dealloc` · clang 의 속성 에러 · 분석기의 재추론.
- **UB** — 빌린 것 `free` · 이전한 것 다시 놓기 · 주인이 놓은 뒤 쓰기 · 잘린 포인터 쓰기.
- **층 밖(관례)** — `_create`/`_destroy` · `_peek` · `char **out` · `_sink` · 헤더 첫머리 규칙.
- ★★★ **판정 도구는 없었다** — 도구는 **어긴 결과**(누수 · 잘못된 `free` · 해제 후 읽기)만 보고, 그것도 **그 경로를 지났을 때만** 본다.
- ★★ **ASan 이 죽은 칸은 [6]** 이다 — 「리포트가 나왔다」는 뜻에서 셌지만 **진단의 종류(`SEGV`)는 틀렸다.** 셈과 함께 그 사실을 적어야 한다.

### 12. 경계 ★

**왜 그런가**

- **`free` 의 계약** — [37번 형제](../37-malloc-calloc-realloc-free/) · **불투명 타입** — [25번 형제](../25-incomplete-types-and-opaque-struct/)(`ctr_new`/`ctr_free`).
- **해제 후 사용의 패턴** — 목록의 **57번 주제**.
- ★ 이 주제가 책임지는 것 — ① **판정표**(문서가 근거) ② **어긴 결과를 도구가 보나**(위반 격자) ③ **관례를 컴파일러에게 알리는 법과 한계**(속성 · 분석기 · C++·Rust 대비).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s38sig.h` · `man` 넷 | ★★★ 판정표의 근거 · 선언 컴파일 | 진단 1 · 문서 4 |
| `s38s.c` | ★★ `strdup` 판 격자 9칸 · `-pedantic-errors` | 진단 12 |
| `s38v.c` + `s38buf.c` | ★★★ **위반 격자 21칸 · 11 / 12** · 리포트 넷 · 보통 빌드 셋 | 실행 28 |
| `s38m.c` · `s38attr.c` · 헤더 둘 | ★★ `-Wmismatched-dealloc` · clang 에러 · glibc 선언 | 진단 16 · 헤더 2 |
| `s38an.c` | ★★ 분석기 재추론 두 판 | 진단 3 |
| `s38x.cpp` · `s38x2.cpp` · `s38r.rs` | ★ C++ · Rust 대비 | 3 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 흔들린 칸은 **리포트의 PID · 주소**뿐이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3번 격자** — glibc 2.39 의 검사 문구 · 두 ASan 의 판정(특히 **clang [1] 의 침묵 · [6] 의 `SEGV`**).
- ★★ **2번** — glibc 의 선언 조건과 두 컴파일러의 암시적 선언 처리.
- ★★ **4·5·9번** — gcc 속성 · 분석기 · clang 18 의 속성 지원.

**`strdup`·`getenv`·`strerror`·`strtok` 의 소유 문장 · 메모리 관리 함수가 준 것이 아닌 포인터를 `free` 하면 UB 인 것 · C23 의 `strdup` 편입은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `fopen`/`fclose` 짝 · `__attribute__((cleanup))` · `setenv` 뒤의 `getenv` 포인터 · glibc 가 짝을 선언한 함수(`reallocarray`)의 틀린 짝.
- ★ **못 잰 것** — clang ASan [1] 침묵의 정확한 원인(스택에 남은 값인지 — 확정하지 않았다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번** — clang 이 인자 있는 `malloc` 속성을 받기 시작하면 가드의 조건이 바뀐다.
- ★★ **3번 [6]** — ASan 이 `bad-free` 를 제대로 말하게 될 수 있다.
- ★★ **4번** — glibc 가 `strdup` 에 짝을 선언하면 `buf_destroy((buf *)s)` 도 잡힌다.
- ★ **1번의 `man`** — 문서가 C23 을 반영할 수 있다.
