# c/syntax/18 — 가변 길이 배열(VLA): 「**크기를 실행 시점에 정하고, 그 자리를 스택에서 꺼낸다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본은 `-std=c17 -Wall -Wextra -pedantic`, 작업 디렉터리는 `/tmp/c17b/18`, 소스는 `ex.c`\~`ex7.c` 다.\
> ★★ **`-std=` 비교 블록은 「컴파일 + 실행」을 한 덩어리로 받은 꼴이라 실행 출력만 실린다** — **각 `-std=` 의 경고 건수는 이 파일의 근거가 아니다.**\
> ★ 소스 블록의 첫 줄 `/* ex4.c */` 는 **캡처가 붙인 파일명 배너**다 — 진단의 줄 번호는 **그 줄을 뺀 실파일 기준**이다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 주소 · `pc`/`bp`/`sp` · PID · `BuildId` · 박힌 경로 | ★ **`sizeof` 값**(32 · 16 · 36 · 68 · 20 · 12 · 8 · 4) |
> | `n = 0` 판이 찍은 원소 값 — **UB 의 산물이다** | ★ **`f()` 호출 횟수**(모두 **2**) · `__STDC_VERSION__` 값 |
> | — | **종료 코드**(`0` · `1` · `139`) · 진단 본문 · 플래그 이름 · **8MB 경계의 부등호** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 함수를 세 `n` 으로 부르면 — **16 · 36 · 68** 로 매번 달라진다 ★★

**출력**

```c
/* ex.c */
#include <stdio.h>
#include <stdlib.h>

static void show(int n) {
    int vla[n];                     /* 크기가 실행 시점에 정해진다 */
    int fixed[8];
    for (int i = 0; i < n; i++) vla[i] = i * i;
    printf("n = %2d : sizeof vla = %3zu · 원소 %2zu 개 · vla[n-1] = %3d · &vla = %s\n",
           n, sizeof vla, sizeof vla / sizeof vla[0], vla[n - 1],
           (char *)&vla < (char *)&fixed ? "fixed 보다 낮은 주소" : "fixed 보다 높은 주소");
}

int main(int argc, char **argv) {
    (void)argv;
    printf("sizeof 가 상수인가 — _Generic 으로 타입을 본다\n");
    int n = 3 + argc;               /* 컴파일 시점에 모르는 값 */
    int vla[n];
    int fixed[8];
    printf("  고정 배열 int[8]  : sizeof = %zu (컴파일 시점 상수)\n", sizeof fixed);
    printf("  가변 배열 int[n]  : sizeof = %zu (n = %d 은 실행 시점 값)\n", sizeof vla, n);
    printf("  sizeof 의 타입    : %s\n",
           _Generic(sizeof vla, size_t: "size_t", default: "그 밖"));
    printf("\n같은 함수를 세 n 으로 부르면 sizeof 가 매번 달라진다\n");
    show(4); show(9); show(17);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof 가 상수인가 — _Generic 으로 타입을 본다
  고정 배열 int[8]  : sizeof = 32 (컴파일 시점 상수)
  가변 배열 int[n]  : sizeof = 16 (n = 4 은 실행 시점 값)
  sizeof 의 타입    : size_t

같은 함수를 세 n 으로 부르면 sizeof 가 매번 달라진다
n =  4 : sizeof vla =  16 · 원소  4 개 · vla[n-1] =   9 · &vla = fixed 보다 낮은 주소
n =  9 : sizeof vla =  36 · 원소  9 개 · vla[n-1] =  64 · &vla = fixed 보다 낮은 주소
n = 17 : sizeof vla =  68 · 원소 17 개 · vla[n-1] = 256 · &vla = fixed 보다 낮은 주소
```

**왜 그런가**

- **`main` 의 두 값은 32 와 16** 이다. `fixed` 는 `int[8]`, `vla` 는 `n = 3 + argc = 4` 라서 `int[4]` 다.
- **세 값은 16 · 36 · 68**(`4·4` · `9·4` · `17·4`). ★ **한 번 컴파일한 같은 코드**가 호출마다 다른 값을 낸다.\
  ★★ **`sizeof` 가 상수가 아닌 자리는 C 에 VLA 하나**다(일반 규칙은 [08번 형제](../08-sizeof-alignment-and-offsetof/)).
- **결과 타입은 안 바뀐다** — `_Generic` 으로 물어 **`size_t`** 를 받았다. 바뀌는 것은 **언제 정해지느냐**뿐이다.
- ★ **`sizeof vla / sizeof vla[0]` 은 여기서 맞는 답**(4 · 9 · 17)을 낸다. **배열 그 자체**를 재고 있어서다 —\
  ★ **매개변수로 넘기는 순간 틀린다**(6번 답). **같은 관용구인데 자리에 따라 갈린다.**
- ★ `&vla` 가 세 번 다 `&fixed` 보다 **낮은 주소**였다 — **관찰이지 보장이 아니다**(10번 답의 「미명시」 칸).

### 2. `sizeof` 안에 함수 호출을 넣은 여섯 식 — **`f()` 는 두 번만 불린다** ★★★

**출력**

```c
/* ex2.c */
#include <stdio.h>

static int calls = 0;
static int f(void) { calls++; return 5; }

#define TRY(label, expr)                                                     \
    do {                                                                     \
        int before = calls;                                                  \
        size_t v = (expr);                                                   \
        printf("%-28s = %3zu   f() 호출 %s\n", label, v,                     \
               calls > before ? "★ 됐다" : "안 됐다");                       \
    } while (0)

int main(void) {
    int n = 4;
    int fixed[8];
    int vla[n];
    (void)fixed; (void)vla;

    TRY("sizeof fixed[f()]",   sizeof fixed[f()]);
    TRY("sizeof vla[f()]",     sizeof vla[f()]);
    TRY("sizeof vla",          sizeof vla);
    TRY("sizeof(int[3])",      sizeof(int[3]));
    TRY("sizeof(int[f()])",    sizeof(int[f()]));
    TRY("sizeof(int[f()?3:3])", sizeof(int[f() ? 3 : 3]));
    printf("\nf() 는 모두 %d 번 불렸다\n", calls);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=0) =====
sizeof fixed[f()]            =   4   f() 호출 안 됐다
sizeof vla[f()]              =   4   f() 호출 안 됐다
sizeof vla                   =  16   f() 호출 안 됐다
sizeof(int[3])               =  12   f() 호출 안 됐다
sizeof(int[f()])             =  20   f() 호출 ★ 됐다
sizeof(int[f()?3:3])         =  12   f() 호출 ★ 됐다

f() 는 모두 2 번 불렸다
```

> ★ **clang 판도 한 글자도 같았다** — 그 블록은 [2-summary.md](2-summary.md) (2)에 있다.

**왜 그런가**

```text
   갈림길은 하나 : ★ "피연산자의 타입" 이 가변 길이 배열인가?

   아니다 ──> 피연산자는 ★ 평가되지 않는다
                sizeof fixed[f()]      ->  4    f() ★ 안 불린다
                sizeof vla[f()]        ->  4    f() ★ 안 불린다   <- 함정
                sizeof(int[3])         -> 12

   그렇다 ──> 피연산자는 ★ 평가된다
                sizeof vla             -> 16
                sizeof(int[f()])       -> 20    f() ★ 불린다
                sizeof(int[f()?3:3])   -> 12    f() ★ 불린다      <- 함정
```

- **여섯 값은 4 · 4 · 16 · 12 · 20 · 12** 이고 **`f()` 는 모두 두 번** — 뒤의 두 식에서만 불렸다.
- ★★★ **기준 한 줄** — 「**변수가 VLA 냐**」가 아니라 「**`sizeof` 가 받는 식의 타입이 가변 길이 배열이냐**」다.\
  `vla[f()]` 의 타입은 **`int`** 라서 보통 `sizeof` 와 똑같이 **평가하지 않는다.**
- ★★ **`sizeof(int[f()?3:3])` 이 부르는 이유** — 기준은 **「값이 상수냐」가 아니라 「상수식이냐」다**.\
  호출이 들어간 순간 상수식이 아니고, 그러면 그 타입이 **가변 길이 배열**이 된다. **크기가 12 로 늘 같은데도** 그렇다.
- ★ **`sizeof vla` 줄은 평가 여부를 증명하지 못한다**(부작용이 없다). ★★ **진단은 0건**이고 **gcc·clang 이 같다.**

### 3. `__STDC_NO_VLA__` 를 여덟 벌로 찍으면 — **어디에서도 정의되지 않았다** ★★★

**출력**

```c
/* ex3.c */
#include <stdio.h>

int main(void) {
#ifdef __STDC_VERSION__
    printf("__STDC_VERSION__   = %ldL\n", (long)__STDC_VERSION__);
#else
    printf("__STDC_VERSION__   = 정의 안 됨 (C89)\n");
#endif
#ifdef __STDC_NO_VLA__
    printf("__STDC_NO_VLA__    = %d  -> VLA 를 안 준다고 선언한 구현\n", __STDC_NO_VLA__);
#else
    printf("__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다\n");
#endif
    int n = 4;
    int vla[n];
    vla[0] = 42;
    printf("실제로 int vla[n] 이 되나 : sizeof = %zu · vla[0] = %d\n", sizeof vla, vla[0]);
    return 0;
}
```

```text
===== gcc -std=c89 -Wall -Wextra -pedantic ex3.c -o x3_89 ; ./x3_89 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 정의 안 됨 (C89)
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== gcc -std=c99 -Wall -Wextra -pedantic ex3.c -o x3_99 ; ./x3_99 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 199901L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== gcc -std=c11 -Wall -Wextra -pedantic ex3.c -o x3_11 ; ./x3_11 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 201112L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3_17 ; ./x3_17 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 201710L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic ex3.c -o x3_2x ; ./x3_2x (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 202000L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== gcc -std=c23 -Wall -Wextra -pedantic ex3.c -o /dev/null (cc exit=1) =====
gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
```

```text
===== clang -std=c89 -Wall -Wextra -pedantic ex3.c -o x3c_89 ; ./x3c_89 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 정의 안 됨 (C89)
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex3.c -o x3c_17 ; ./x3c_17 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 201710L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

```text
===== clang -std=c23 -Wall -Wextra -pedantic ex3.c -o x3c_23 ; ./x3c_23 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 202311L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

**왜 그런가**

| 판 | `__STDC_VERSION__` | `__STDC_NO_VLA__` | `int vla[n]` 이 되나 |
|---|---|---|---|
| gcc `-std=c89` | 정의 안 됨 | ★ **정의 안 됨** | **된다** — `sizeof` 16 · `cc exit=0 · run exit=0` |
| gcc `-std=c99` | `199901L` | ★ **정의 안 됨** | 된다 |
| gcc `-std=c11` | `201112L` | ★ **정의 안 됨** | 된다 |
| gcc `-std=c17` | `201710L` | ★ **정의 안 됨** | 된다 |
| gcc `-std=c2x` | `202000L` | ★ **정의 안 됨** | 된다 |
| gcc `-std=c23` | — | — | ★ **그런 옵션이 없다** — `cc exit=1` |
| clang `-std=c89` | 정의 안 됨 | ★ **정의 안 됨** | 된다 |
| clang `-std=c17` | `201710L` | ★ **정의 안 됨** | 된다 |
| clang `-std=c23` | `202311L` | ★ **정의 안 됨** | 된다 |

- ★★★ **여덟 벌 어디에도 그 매크로가 없다.** **이 구현들은 VLA 를 뺀 적이 없다.**
- ★★ **`-std=c89 -pedantic` 에서도 컴파일되고 실행된다**(`cc exit=0 · run exit=0` · `sizeof` 16).\
  ★ **`-std=` 는 「강제」가 아니라 「기본값 선택」이다**.
- ★★ **gcc 13 에는 `-std=c23` 이 없다** — 「`did you mean -std=c2x`」와 함께 **`cc exit=1`** 이다.\
  ★ **경고 0건인데 `exit=1`** 이라 **경고만 세면 「통과」로 기록된다.**
- ★★ **같은 「C23」인데 선 지점이 다르다** — gcc `c2x` **`202000L`** ↔ clang `c23` **`202311L`**.
- ★★★ **갈라 말하면** — **표준이 정한 것**: C99 필수 → C11 선택 → C23 에서 선택 범위 축소.\
  **이 구현이 그런 것**: 매크로가 여덟 벌 전부 없고 `-std=c89` 에서도 된다. ★ **뒤엣것은 앞엣것의 증거가 아니다**(9번 답).

### 4. 8MB 스택에 두 크기를 던지면 — **8,000,000 통과 / 9,000,000 `139`** ★★★

**출력**

```c
/* ex4.c */
#include <stdio.h>
#include <stdlib.h>

static void touch(long n) {
    char vla[n];                    /* n 바이트를 스택에서 잡는다 */
    vla[0] = 1;
    vla[n - 1] = 2;                 /* 양 끝을 건드려 실제로 쓴다 */
    fprintf(stderr, "  n = %10ld 바이트 : 잡았다 (%d %d)\n", n, vla[0], vla[n - 1]);
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "쓰는 법: ./x <바이트수>\n"); return 2; }
    long n = strtol(argv[1], NULL, 10);
    fprintf(stderr, "요청 %ld 바이트\n", n);
    touch(n);
    fprintf(stderr, "정상 종료\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 8000000 (cc exit=0 · run exit=0) =====
요청 8000000 바이트
  n =    8000000 바이트 : 잡았다 (1 2)
정상 종료
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 9000000 (cc exit=0 · run exit=139) =====
요청 9000000 바이트
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex4.c -o x4a ; ./x4a 100000000 | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
요청 100000000 바이트
AddressSanitizer:DEADLYSIGNAL
=================================================================
==84376==ERROR: AddressSanitizer: stack-overflow on address 0x7ffcb3a9c908 (pc 0x580f12bf8354 bp 0x7ffcb429a960 sp 0x7ffcb3a9b910 T0)
    #0 0x580f12bf8354 in touch /tmp/c17b/18/ex4.c:5
    #1 0x580f12bf860c in main /tmp/c17b/18/ex4.c:15
    #2 0x71449882a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x71449882a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x580f12bf8204 in _start (/tmp/c17b/18/x4a+0x1204) (BuildId: b202344f7d086ce635a6856bca5419ac7e8cdfe4)

SUMMARY: AddressSanitizer: stack-overflow /tmp/c17b/18/ex4.c:5 in touch
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소·`pc`/`bp`/`sp`·PID·`BuildId` 는 실행마다 바뀐다.\
> 근거는 **`stack-overflow` 가 `touch ex4.c:5` 에서 났다**는 것, **종료 코드가 `139` ↔ `1`** 이라는 것, 그리고 **부등호**다.

**왜 그런가**

- **8,000,000 은 `run exit=0`** 이고 「잡았다 (1 2)」와 「정상 종료」를 찍는다 — **양 끝을 실제로 써서** 확인했다.\
  **9,000,000 은 `run exit=139`**(= 128 + 11)이고 **「요청 …」 줄에서 출력이 끊긴다.** `ulimit -s` 는 **8192 KB**(= 8,388,608)다.
- ★★★ **컴파일 경고 0건 · 실행 중 진단 0줄.** **남는 것은 종료 코드 하나**다 — **어디서·왜 죽었는지 아무도 말해 주지 않는다.**
- ★ **100,000,000 판도 맨몸에서는 똑같이 `139` 하나**다(블록은 [2-summary.md](2-summary.md) (4)) — **12배를 넘겨도 출력이 더 나오지 않는다.**
- ★★ **ASan 을 켜면 이름이 붙는다** — `stack-overflow` at **`touch ex4.c:5`**, 즉 **VLA 를 잡는 그 줄**이고 **종료 코드가 `1`** 이 된다.\
  ★ **같은 프로그램이 도구에 따라 다른 코드로 죽는다.**
- ★★ **`-Wvla` 는 못 막는다.** 「VLA 를 썼다」만 말하고 **「이 `n` 이 크다」는 안 본다** — `n` 은 **실행 시점 값**이다.

### 5. 크기가 0 이거나 음수면 — **UBSan 은 말하는데 `run exit=0`** ★★

**출력**

```c
/* ex4.c */
#include <stdio.h>
#include <stdlib.h>

static void touch(long n) {
    char vla[n];                    /* n 바이트를 스택에서 잡는다 */
    vla[0] = 1;
    vla[n - 1] = 2;                 /* 양 끝을 건드려 실제로 쓴다 */
    fprintf(stderr, "  n = %10ld 바이트 : 잡았다 (%d %d)\n", n, vla[0], vla[n - 1]);
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "쓰는 법: ./x <바이트수>\n"); return 2; }
    long n = strtol(argv[1], NULL, 10);
    fprintf(stderr, "요청 %ld 바이트\n", n);
    touch(n);
    fprintf(stderr, "정상 종료\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=undefined ex4.c -o x4u ; ./x4u 0 (cc exit=0 · run exit=0) =====
요청 0 바이트
ex4.c:5:10: runtime error: variable length array bound evaluates to non-positive value 0
ex4.c:6:8: runtime error: index 0 out of bounds for type 'char [*]'
ex4.c:7:8: runtime error: index -1 out of bounds for type 'char [*]'
ex4.c:8:82: runtime error: index -1 out of bounds for type 'char [*]'
ex4.c:8:74: runtime error: index 0 out of bounds for type 'char [*]'
  n =          0 바이트 : 잡았다 (1 0)
정상 종료
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=undefined ex4.c -o x4u ; ./x4u -1 (cc exit=0 · run exit=0) =====
요청 -1 바이트
ex4.c:5:10: runtime error: variable length array bound evaluates to non-positive value -1
  n =         -1 바이트 : 잡았다 (1 2)
정상 종료
```

**왜 그런가**

- **`0` 판은 다섯 줄, `-1` 판은 한 줄**이고 문구는 「**`variable length array bound evaluates to non-positive value`**」다.
- ★★ **`0` 도 UB** 다. `0` 판은 **뒤따르는 배열 접근까지**(`index 0`·`index -1`) 걸렸고 `-1` 판은 **크기 자체만** 걸렸다 —\
  **같은 부류의 UB 인데 드러나는 양이 다르다.**
- ★★★ **두 판 다 `run exit=0`** 이다. UBSan 은 기본에서 **보고하고 계속 간다** — **종료 코드만 보는 자동화는 통과로 읽는다.**\
  ★ 죽이려면 `-fno-sanitize-recover=all` 을 따로 켜야 하고 **이 문서는 그 판을 안 던졌다.**
- ★★ **ASan 은 이 둘을 잡지 않았다** — ASan 이 잡은 것은 **4번의 스택 소진**이다. **두 도구가 서로 다른 것을 본다.**
- ★ 두 판이 찍은 원소 값은 **UB 의 산물이라 근거가 못 된다.** 근거는 **진단 본문**과 **`run exit=0`** 둘이다.

### 6. VLA 매개변수 두 꼴의 `sizeof` — **8 과 12** ★★

**출력**

```c
/* ex5.c */
#include <stdio.h>

/* (가) 1차원 VLA 매개변수 — [n] 은 포인터로 재작성된다 (17번 주제와 같다) */
static int sum1(int n, int a[n]) {
    int s = 0;
    for (int i = 0; i < n; i++) s += a[i];
    printf("  sum1 : sizeof a = %zu (포인터)\n", sizeof a);
    return s;
}

/* (나) 2차원 VLA 매개변수 — 바깥 한 겹만 잃고 안쪽 보폭이 실행 시점에 정해진다 */
static int sum2(int rows, int cols, int a[rows][cols]) {
    int s = 0;
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++) s += a[i][j];
    printf("  sum2 : sizeof a = %zu (포인터) · sizeof a[0] = %zu (★ 실행 시점 cols=%d)\n",
           sizeof a, sizeof a[0], cols);
    return s;
}

/* (다) 매개변수에서 크기를 * 로 적을 수 있다 — 선언에서만 */
int sum3(int n, int a[*]);
int sum3(int n, int a[n]) { int s = 0; for (int i = 0; i < n; i++) s += a[i]; return s; }

int main(void) {
    int flat[6] = {1,2,3,4,5,6};
    int grid[2][3] = {{1,2,3},{4,5,6}};
    printf("sum1(6, flat)      = %d\n", sum1(6, flat));
    printf("sum2(2, 3, grid)   = %d\n", sum2(2, 3, grid));
    printf("sum3(6, flat)      = %d\n", sum3(6, flat));
    int n = 4;
    int vla[n];
    for (int i = 0; i < n; i++) vla[i] = 10 * (i + 1);
    printf("sum1(4, vla)       = %d\n", sum1(n, vla));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o x5 (cc exit=0) =====
ex5.c: In function ‘sum1’:
ex5.c:7:57: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int *’ [-Wsizeof-array-argument]
    7 |     printf("  sum1 : sizeof a = %zu (포인터)\n", sizeof a);
      |                                                         ^
ex5.c:4:28: note: declared here
    4 | static int sum1(int n, int a[n]) {
      |                        ~~~~^~~~
ex5.c: In function ‘sum2’:
ex5.c:17:19: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int (*)[cols]’ [-Wsizeof-array-argument]
   17 |            sizeof a, sizeof a[0], cols);
      |                   ^
ex5.c:12:41: note: declared here
   12 | static int sum2(int rows, int cols, int a[rows][cols]) {
      |                                     ~~~~^~~~~~~~~~~~~
ex5.c: At top level:
ex5.c:22:21: warning: argument 2 of type ‘int[*]’ declared with 1 unspecified variable bound [-Wvla-parameter]
   22 | int sum3(int n, int a[*]);
      |                 ~~~~^~~~
ex5.c:23:21: note: subsequently declared as ‘int[n]’ with 0 unspecified variable bounds
   23 | int sum3(int n, int a[n]) { int s = 0; for (int i = 0; i < n; i++) s += a[i]; return s; }
      |                 ~~~~^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex5.c -o x5c (cc exit=0) =====
ex5.c:7:60: warning: sizeof on array function parameter will return size of 'int *' instead of 'int[n]' [-Wsizeof-array-argument]
    7 |     printf("  sum1 : sizeof a = %zu (포인터)\n", sizeof a);
      |                                                         ^
ex5.c:4:28: note: declared here
    4 | static int sum1(int n, int a[n]) {
      |                            ^
ex5.c:17:19: warning: sizeof on array function parameter will return size of 'int (*)[cols]' instead of 'int[rows][cols]' [-Wsizeof-array-argument]
   17 |            sizeof a, sizeof a[0], cols);
      |                   ^
ex5.c:12:41: note: declared here
   12 | static int sum2(int rows, int cols, int a[rows][cols]) {
      |                                         ^
ex5.c:23:21: warning: argument 'a' of type 'int[n]' with mismatched bound [-Warray-parameter]
   23 | int sum3(int n, int a[n]) { int s = 0; for (int i = 0; i < n; i++) s += a[i]; return s; }
      |                     ^
ex5.c:22:21: note: previously declared as 'int[*]' here
   22 | int sum3(int n, int a[*]);
      |                     ^
3 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o x5 ; ./x5 (cc exit=0 · run exit=0) =====
  sum1 : sizeof a = 8 (포인터)
sum1(6, flat)      = 21
  sum2 : sizeof a = 8 (포인터) · sizeof a[0] = 12 (★ 실행 시점 cols=3)
sum2(2, 3, grid)   = 21
sum3(6, flat)      = 21
  sum1 : sizeof a = 8 (포인터)
sum1(4, vla)       = 100
```

**왜 그런가**

- **`sum1` 안의 `sizeof a` 는 8** — **포인터로 재작성**된다. [16번 형제](../16-array-pointer-decay-and-function-parameters/)의 `int a[10]` 과 **똑같은 결말**이다.
- ★★★ **`sum2` 는 `sizeof a` 가 8, `sizeof a[0]` 이 12** 다. **`cols = 3` 이라는 실행 시점 값**이 타입에 들어 있다.\
  ★ **[목록의 17번 주제](../17-multidimensional-arrays-and-pointer-types/)와 같은 12 인데 정해진 시점이 다르다** — 거기서는 **컴파일 시간**, 여기서는 **호출할 때**다.
- **세 합은 21 · 21 · 21** 이고 VLA 를 넘긴 `sum1(4, vla)` 는 **100** 이다.
- ★ **경고는 양쪽 다 3건**이고 **이름이 갈린다** — `sizeof` 쪽 둘은 **양쪽 다 `-Wsizeof-array-argument`** 인데,\
  **`int a[*]` 와 `int a[n]` 의 불일치**는 **gcc 가 `-Wvla-parameter`**, **clang 이 `-Warray-parameter`** 다.
- ★ **clang 은 버려진 타입**(`instead of 'int[rows][cols]'`)을, **gcc 는 남은 타입**(`int (*)[cols]`)을 적는다. **둘 다 `cc exit=0`** 이다.

### 7. VLA 를 놓을 수 없는 다섯 자리 — **전부 에러, 한 번에 나온다** ★★

**출력**

```c
/* ex7.c */
#include <stdio.h>

int n = 4;
static int file_vla[n];             /* (가) 파일 스코프 — 정적 저장 기간 */

struct S { int a[n]; };             /* (나) 구조체 멤버 */

int main(void) {
    int m = 3;
    static int fn_vla[m];           /* (다) 함수 안의 static */
    int init_vla[m] = {1, 2, 3};    /* (라) 초기자를 붙인 VLA */
    extern int ext_vla[m];          /* (마) extern 으로 선언한 VLA */
    printf("%p %p %p\n", (void *)file_vla, (void *)fn_vla, (void *)init_vla);
    (void)ext_vla;
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o /dev/null (cc exit=1) =====
ex7.c:4:12: error: variably modified ‘file_vla’ at file scope
    4 | static int file_vla[n];             /* (가) 파일 스코프 — 정적 저장 기간 */
      |            ^~~~~~~~
ex7.c:6:16: error: variably modified ‘a’ at file scope
    6 | struct S { int a[n]; };             /* (나) 구조체 멤버 */
      |                ^
ex7.c: In function ‘main’:
ex7.c:10:16: error: storage size of ‘fn_vla’ isn’t constant
   10 |     static int fn_vla[m];           /* (다) 함수 안의 static */
      |                ^~~~~~
ex7.c:11:23: error: variable-sized object may not be initialized except with an empty initializer
   11 |     int init_vla[m] = {1, 2, 3};    /* (라) 초기자를 붙인 VLA */
      |                       ^
ex7.c:12:16: error: object with variably modified type must have no linkage
   12 |     extern int ext_vla[m];          /* (마) extern 으로 선언한 VLA */
      |                ^~~~~~~
ex7.c:12:16: error: storage size of ‘ext_vla’ isn’t constant
ex7.c:12:16: warning: unused variable ‘ext_vla’ [-Wunused-variable]
ex7.c:10:16: warning: unused variable ‘fn_vla’ [-Wunused-variable]
   10 |     static int fn_vla[m];           /* (다) 함수 안의 static */
      |                ^~~~~~
```

**왜 그런가**

- **컴파일되는 것은 하나도 없다.** 다섯 자리 **전부 에러**이고 **`cc exit=1`** 이다 — **경고가 아니다.**
- ★ **(가)와 (나)의 문구가 같은 이유** — **구조체 멤버 선언도 그 위치에서 평가돼야** 하므로 **파일 스코프로 불린다.**
- ★★ **(다) 함수 안의 `static` 도 안 된다** — 자리는 함수 안인데 **저장 기간이 정적**이라 **프로그램 시작 전에 크기가 정해져 있어야** 한다.
- ★ **(라)** 는 「**빈 초기자는 예외**」를 덧붙이고(그 판은 **안 던졌다**), **(마)** 는 이유가 **둘**(링크·크기)로 나온다.
- ★★★ **VLA 가 놓일 수 있는 유일한 자리는 블록 안의 자동 저장 기간**이다(고르는 이야기는 [목록의 **28번 주제**](../28-choosing-among-four-storage-durations/)).

### 8. `goto` 와 VLA 스코프 — **에러**이고 `cc exit=1` ★

**출력**

```c
/* ex6.c */
#include <stdio.h>

int main(void) {
    int n = 4;
    goto skip;                  /* VLA 가 사는 스코프 안으로 뛴다 */
    int vla[n];
    vla[0] = 1;
skip:
    printf("여기 왔다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex6.c -o /dev/null (cc exit=1) =====
ex6.c: In function ‘main’:
ex6.c:5:5: error: jump into scope of identifier with variably modified type
    5 |     goto skip;                  /* VLA 가 사는 스코프 안으로 뛴다 */
      |     ^~~~
ex6.c:8:1: note: label ‘skip’ defined here
    8 | skip:
      | ^~~~
ex6.c:6:9: note: ‘vla’ declared here
    6 |     int vla[n];
      |         ^~~
ex6.c:6:9: warning: variable ‘vla’ set but not used [-Wunused-but-set-variable]
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex6.c -o /dev/null (cc exit=1) =====
ex6.c:5:5: error: cannot jump from this goto statement to its label
    5 |     goto skip;                  /* VLA 가 사는 스코프 안으로 뛴다 */
      |     ^
ex6.c:6:9: note: jump bypasses initialization of variable length array
    6 |     int vla[n];
      |         ^
1 error generated.
```

**왜 그런가**

- ★★ **경고가 아니라 에러**이고 **`cc exit=1`** 이다. ★ **정본은 [12번 형제](../12-control-flow-and-switch/)이고**, 거기서는 **`switch` 도 같은 규칙**이라는 것까지 본다.
- ★★ **두 컴파일러가 다른 각도로 말한다** — **gcc 는 타입으로**(`variably modified type`), **clang 은 이유로**(`bypasses initialization of variable length array`).\
  ★ **「무엇을 건너뛰는지」를 알려 주는 쪽은 clang** 이다.
- ★ gcc 는 에러 뒤에 **경고까지** 낸다 — **에러가 난 컴파일에서도 경고는 나온다.**
- ★★ **`goto cleanup` 과의 충돌** — 정리 라벨이 VLA 선언보다 뒤면 **그 앞에서 뛰어넘는 `goto` 가 전부 막힌다.**\
  대처는 **VLA 를 더 안쪽 블록으로 미는 것**이다(관용구는 [13번 형제](../13-goto-cleanup-idiom/)).

### 9. 「표준이 정했다」와 「재 보니 그렇더라」 ★★★

**답**

```text
   표준 문서 쪽 사실                          이 머신에서 잰 것
   ─────────────────────────────────         ─────────────────────────────────
   C99 : VLA ★ 필수                          __STDC_NO_VLA__ 가 여덟 벌 전부
   C11 : VLA ★ 선택 (__STDC_NO_VLA__)          ★ 정의 안 됨
   C23 : 선택의 ★ 범위가 좁아졌다              -std=c89 -pedantic 에서도
         가변 수정 타입은 다시 필수,             ★ 컴파일되고 ★ 실행된다
         자동 저장 기간의 VLA 객체만 선택        gcc 13 에 -std=c23 이 ★ 없다

   ★ 왼쪽은 "무엇이 옳은가", 오른쪽은 "지금 무엇이 되는가".
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wvla ex3.c -o /dev/null (cc exit=0) =====
ex3.c: In function ‘main’:
ex3.c:15:5: warning: ISO C90 forbids variable length array ‘vla’ [-Wvla]
   15 |     int vla[n];
      |     ^~~
```

- **연혁 셋은 표준 문서 쪽 사실**이다 — 이 문서는 **그 문서를 새로 열지 않았고** 근거는 [`../README.md`](../README.md) 의 기준 소스 선언이다.\
  **매크로가 없다는 것은 잰 것**이고 **gcc 13 과 clang 18 두 구현에 대한 사실**이다.
- ★★★ **「없으니 어디서나 쓸 수 있다」가 틀린 이유** — 그 출력이 증명한 것은 「**이 두 구현에는 있다**」뿐이다.\
  ★ **매크로는 「없는 쪽」이 자기를 신고하는 장치**라, **안 붙은 것은 정보가 아니라 침묵**이다.
- ★★ **`-std=c17` 인데 문구가 「`ISO C90 forbids`」인 것** — gcc 의 `-Wvla` 는 **어느 `-std=` 에서든 같은 문장**을 쓴다.\
  ★ **진단 문구를 「지금 고른 표준」으로 읽으면 안 된다.** 그리고 **경고**라 **`cc exit=0`** 이고, **`-Wall -Wextra -pedantic` 에 안 들어 있다.**

### 10. 다섯 층과 무게중심 ★★

**답**

| 층 | 이 주제(18번) | [16번](../16-array-pointer-decay-and-function-parameters/) | [12번](../12-control-flow-and-switch/) |
|---|---|---|---|
| **표준** | `sizeof` 의 실행 시점 계산·평가 규칙 · 저장 기간 고정 · 스코프 진입 금지 · 매개변수 재작성 | 감쇠 규칙 · 매개변수 재작성 | ★★ **본체** |
| ★★★ **조건부 표준** | ★★ **본체** — **VLA 자체**(C99 필수 → C11 선택 → C23 축소) · `__STDC_NO_VLA__` | ★ **해당 없음** | ★ **해당 없음** |
| **구현 정의** | `sizeof(int)`=4 라서 16·36·68 · 정렬 · 큰 `n` 의 실패 방식 | `sizeof(int *)`=8 · 리터럴이 놓이는 영역 | ★ 거의 없다 |
| **미명시** | ★ **VLA 를 어디에 잡는가**(「스택」은 표준의 말이 아니다) | 같은 리터럴의 공유 여부 | ★ 해당 없음 |
| **UB** | **크기가 0 이하** · **자리를 넘겨 잡는 것** | ★★ **본체** — 길이를 잃은 뒤의 접근 | ★ 둘뿐 |

- ★★★ **가장 두꺼운 칸은 「조건부 표준」이고** **[16번 형제](../16-array-pointer-decay-and-function-parameters/)는 그 칸이 「해당 없음」이었다** — **층 분포가 정반대**다.
- ★ **빈 칸은 없다.** 다섯 칸이 전부 채워지는 주제라 **층을 안 가르면 문장이 섞인다** —\
  「VLA 는 표준이다」와 「VLA 는 선택이다」가 **둘 다 맞는 말**이 되는 자리다.
- ★★ **「어디에 잡히는가」는 미명시**다. 근거가 **`&vla` 가 더 낮은 주소였다는 관찰 한 줄**뿐이고 **주소는 흔들리는 칸**이라 **약하다** —\
  「스택에서 꺼낸다」는 **표어이지 표준의 문장이 아니다.**

### 11. 누가 침묵하나 ★★★

**답**

```text
   같은 프로그램·같은 입력 — 도구만 바꾼다

   맨몸           진단 0줄 · run exit=139   <- "죽었다" 말고 아무 정보도 없다
   -Wall -Wextra  0건 · -pedantic 0건       <- 크기 이야기를 아예 안 한다
   -Wvla          "VLA 다" 만 말한다         <- ★ "크다" 는 안 본다
   UBSan          n <= 0 만 말한다           <- ★ 스택 소진은 못 본다 · run exit=0
   ASan           stack-overflow             <- ★ 이름을 붙여 주는 유일한 도구
                  touch ex4.c:5 · run exit=1
```

- **스택 소진** — **컴파일 경고 0건 · 실행 중 0줄**, **남는 것은 `run exit=139` 하나**다. ★ **이름을 붙이는 것은 ASan 뿐**이다.
- ★★★ **UBSan 이 말하고도 종료 코드가 0 인 것이 위험한 이유** — **사람은 진단을 보지만 자동화는 코드를 본다.**\
  로그를 안 읽는 CI 는 **UB 가 다섯 줄 나온 실행을 「통과」로 기록**한다. ★ **「에러 없이 돌았다」가 「됐다」가 아닌 자리**다.
- ★ **`sizeof` 평가 규칙은 어느 플래그도 말해 주지 않는다** — **진단 0건**이다.
- ★★ **네 번째 창 둘** — ① **종료 코드**(`0` · `1` · `139` · 컴파일 `1`) — **출력이 같아 보여도 갈린다.**\
  ② **부작용 횟수** — **`f()` 가 두 번** 불렸다는 숫자 하나가 **여섯 식의 평가 여부를 전부 판정**한다.

### 12. 경계 — 어디까지가 이 주제인가 ★

**답**

- **`sizeof` 의 일반 규칙** — [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이고 이 주제는 「**그 예외가 어디까지인가**」만 본다.
- **`goto`·`switch` 의 VLA 스코프 진입 금지** — [12번 형제](../12-control-flow-and-switch/)가 정본이고 여기는 **결론과 문구 차이**까지다(관용구는 [13번 형제](../13-goto-cleanup-idiom/)).
- **감쇠와 매개변수 재작성** — [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이고 여기는 「**안쪽 한 겹이 실행 시점 값이 되는 자리**」만 더한다.\
  **다차원 배치 자체**는 [목록의 **17번 주제**](../17-multidimensional-arrays-and-pointer-types/)다.
- ★★ **크기를 못 믿을 때는 `malloc`**(목록의 **37번 주제**)이다. ★ **다른 점은 하나** — **`malloc` 은 실패를 `NULL` 로 말해 주고 VLA 에는 그런 반환값이 없다.**\
  구조체에 가변 길이를 붙이려면 **유연 배열 멤버**([목록의 **26번 주제**](../26-flexible-array-members/))다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `ex.c` (18-a) | `sizeof` **32 ↔ 16** · 세 호출에서 **16·36·68** · 결과 타입 **`size_t`** · `&vla` 가 더 낮은 주소(관찰) | gcc 1벌(컴파일+실행) |
| `ex2.c` (18-b) | 여섯 값 **4·4·16·12·20·12** · **`f()` 총 2회** · ★ `sizeof vla[f()]` 는 **안 불림** · gcc·clang 출력 동일 | gcc 1벌 · clang 1벌 |
| `ex3.c` (18-c) | **매크로가 여덟 벌 전부 정의 안 됨** · `__STDC_VERSION__` 값 · **gcc 13 에 `-std=c23` 없음**(`cc exit=1`) · gcc `c2x` **202000L** ↔ clang `c23` **202311L** · `-Wvla` 는 **경고**(`cc exit=0`), 문구는 `ISO C90` | gcc 6벌(`c89`\~`c23`) · clang 3벌(`c89`·`c17`·`c23`) · gcc `-Wvla` 1벌 |
| `ex4.c` (18-d) | `ulimit -s` **8192** · **8,000,000 통과**(`run exit=0`) / **9,000,000·100,000,000 죽음**(`run exit=139`) · **진단 0줄** · ASan **`stack-overflow` at `touch ex4.c:5`**(`run exit=1`) · UBSan **`non-positive value` 0·-1**(둘 다 `run exit=0`) | gcc 맨몸 3판 · `-fsanitize=address` 1판 · `-fsanitize=undefined` 2판 |
| `ex5.c` (18-e) | `sizeof a` **8** · ★ `sizeof a[0]` **12**(실행 시점 `cols`) · 합 **21·21·21·100** · 경고 **각 3건** · **`-Wvla-parameter`(gcc) ↔ `-Warray-parameter`(clang)** | gcc 2벌 · clang 1벌 |
| `ex6.c` (18-f) | `goto` 의 VLA 스코프 진입 = **error `cc exit=1`** · gcc 는 **타입**으로, clang 은 **이유**로 말함 | gcc 1벌 · clang 1벌 |
| `ex7.c` (18-g) | 다섯 자리 **전부 error**(`cc exit=1`) · (가)(나) 문구 동일 · (라)의 「빈 초기자는 예외」 문구 | gcc 1벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · `ulimit -s` 8192)에서만** 그렇다.

- **`sizeof(int)`=4** 라서 **16·36·68·12·20** 인 것 — ★ **구현 정의**다.
- **8MB 경계** — `ulimit -s` 에 달렸다. ★ **경계를 옮기면 8,000,000 도 죽는다.** **`run exit=139`** 도 **이 환경의 실패 방식**이다.
- **매크로가 없는 것** — ★ **두 구현에 대한 사실이지 C 언어에 대한 사실이 아니다.**
- **gcc 13 에 `-std=c23` 이 없는 것**, **`c2x` 가 `202000L` 인 것** — 그 판의 구현 상태다.
- **`-Wvla-parameter` ↔ `-Warray-parameter`** — 진단 분류의 이름 차이다.

**`sizeof` 평가 규칙과 저장 기간 제약은 구현 의존이 아니다.** 여섯 식의 값과 `f()` 호출 2회, 다섯 자리의 에러,\
`goto` 진입 금지는 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `-Werror=vla` · `-fno-sanitize-recover=all` · `-Wstack-usage=` · **VLA 의 정렬**(`_Alignof`) ·\
  **`alloca` 와의 비교** · **빈 초기자**(`int a[m] = {}`) · **최적화 수준을 바꾼 판**(UB 가 걸린 자리인데 기본 한 벌만 던졌다).
- ★ **각 `-std=` 의 경고 건수** — 그 블록들은 **실행 출력만** 담는 꼴이라 **이 문서로는 답할 수 없다.**\
  경고 쪽 근거는 **`-Wvla` 블록 하나**뿐이다.
- ★ **못 잰 것 — 스택 경계의 정확한 값.** 두 점만 던졌고 **프레임의 나머지가 얼마를 쓰는지**에 달려 있어\
  **「8,388,608 에서 끊긴다」로 적으면 지어내는 것**이 된다. 말할 수 있는 것은 **부등호**뿐이다.
- ★ **못 잰 것 — `__STDC_NO_VLA__` 를 정의하는 구현에서 무엇이 막히나.** **그런 구현이 이 머신에 없다.**\
  ★ **C23 에서 선택의 범위가 좁아졌다는 것도 출력으로는 확인되지 않는다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- **gcc 가 `-std=c23` 을 갖게 됐는지**, 그때 **`__STDC_VERSION__` 이 `202311L` 이 되는지**.
- **`__STDC_NO_VLA__` 를 정의하는 판이 나오는지** — 지금은 **여덟 벌 전부 없다.**
- **`-Wvla` 의 문구가 바뀌는지**(지금은 `-std=c17` 에서도 `ISO C90`), **그것이 `-Wall` 류에 들어가는지**.
- **`sizeof` 값과 8MB 경계** — 다른 ISA·다른 `ulimit` 로 갈 때 다시 잰다.
- **평가 규칙·저장 기간 제약·`goto` 진입 금지는 다시 돌릴 필요가 없다** — 구현이 아니라 **표준이 정한 것**이다.
