# c/syntax/35 — 함수 포인터와 콜백 테이블: 「**함수 이름은 주소가 되고, 테이블은 재배치를 기다린다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux · glibc 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s35a.c`\~`s35g.c` · `s35r.rs`·`s35r2.rs` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **판 격자** — 3번은 컴파일러 2 × PIE 기본 / `-fno-PIE` / `-fPIC`, 4번은 × PIE 유무, 5번은 × sanitizer 플래그 3, 6번은 × `-O0`/`-O2`.
> ★★★ **본체 창은 오브젝트 섹션** · 콜백의 사고는 **sanitizer 창**.
> ★★ **흔들리는 칸은 없다** — 정규화 규칙은 기본 넷뿐이다(재배치의 `.text+0x…` 는 주소 규칙에 걸리지만 원문이 같다).

## 이 파일이 다시 싣는 소스

★ 4·5·6번의 격자와 sanitizer 리포트는 **소스 줄을 끼워 보여 주지 않는다** — 그 소스를 여기 한 번 더 싣는다(질문 파일의 것과 같다).

```c
/* s35c2.c */
#include <stdio.h>

static int op_add(int a, int b) { return a + b; }
static int op_sub(int a, int b) { return a - b; }

int (*table_rw[2])(int, int)       = { op_add, op_sub };
int (*const table_ro[2])(int, int) = { op_add, op_sub };

int main(void) {
    table_rw[0] = op_sub;
    fprintf(stderr, "[1] after writing table_rw[0]\n");
    *(int (**)(int, int))&table_ro[0] = op_sub;   /* const 를 캐스트로 떼고 쓴다 */
    fprintf(stderr, "[2] after writing table_ro[0]\n");
    return table_ro[0](1, 2);
}
```

```c
/* s35d.c */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static int cmp_sub(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return a - b;
}

static int cmp_rel(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static void run(const char *tag, int (*cmp)(const void *, const void *)) {
    int v[] = { 3, INT_MIN, 1, INT_MAX, -2, 0 };
    size_t n = sizeof v / sizeof v[0];
    qsort(v, n, sizeof v[0], cmp);
    int sorted = 1;
    for (size_t i = 1; i < n; i++) if (v[i - 1] > v[i]) sorted = 0;
    printf("%-8s", tag);
    for (size_t i = 0; i < n; i++) printf(" %d", v[i]);
    printf("   | sorted? %s\n", sorted ? "yes" : "no");
}

int main(void) {
    run("cmp_sub", cmp_sub);
    run("cmp_rel", cmp_rel);
    return 0;
}
```

```c
/* s35e.c */
#include <stdio.h>

static int take_int(int x) { return x + 1; }

typedef int (*FnLong)(long);

int main(void) {
    FnLong g = (FnLong)take_int;          /* 서명이 다른 타입으로 캐스트 */
    fprintf(stderr, "[1] before the call\n");
    int r = g(41L);
    fprintf(stderr, "[2] after the call, r = %d\n", r);
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 넷 다 같은 포인터 — **비교 셋 다 `1` · 호출 넷 다 `10`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s35a.c -o x ; ./x (cc exit=0 · run exit=0) =====
p1 == p2 : 1   p1 == p3 : 1   p1 == p4 : 1
p1(5) = 10   (*p1)(5) = 10   (**p1)(5) = 10   (***p1)(5) = 10
sizeof p1 = 8
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s35a.c -o x ; ./x (cc exit=0 · run exit=0) =====
p1 == p2 : 1   p1 == p3 : 1   p1 == p4 : 1
p1(5) = 10   (*p1)(5) = 10   (**p1)(5) = 10   (***p1)(5) = 10
sizeof p1 = 8
```

**왜 그런가**

- ★★ **함수 지시자는 `sizeof`·`&` 밖에서 포인터로 바뀐다** — `twice` 는 곧 포인터, `*twice` 는 「풀어서 함수」가 됐다가 **다시 포인터**, `**twice` 도 같다.
- ★ **호출 연산자는 함수 포인터를 받는다** — `(***p1)(5)` 도 `p1(5)` 와 같다.

### 2. `sizeof` 함수 — **두 컴파일러 경고 · `exit=0` · 값 `1` · `-pedantic-errors` 면 에러** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s35b.c -o x (cc exit=0) =====
s35b.c: In function ‘main’:
s35b.c:6:44: warning: invalid application of ‘sizeof’ to a function type [-Wpointer-arith]
    6 |     printf("sizeof twice  = %zu\n", sizeof twice);
      |                                            ^~~~~
```

```text
===== sizeof 를 함수에 — 컴파일러 2 × 두 강도 (-std=c17 -Wall -Wextra) (exit=0) =====
gcc    -pedantic         exit=0 경고 1 에러 0
gcc    -pedantic-errors  exit=1 경고 0 에러 1
clang  -pedantic         exit=0 경고 2 에러 0
clang  -pedantic-errors  exit=1 경고 0 에러 1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s35b.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof twice  = 1
sizeof &twice = 8
```

**왜 그런가**

- ★★★ **함수 타입에 `sizeof` 를 쓰는 것은 제약 위반**이다 — 그런데 `-pedantic` 에서 두 컴파일러 다 **`exit=0`** 이고 값 `1`(GNU 확장)을 낸다. → **「종료 코드 0인데 ill-formed」**
- ★ **`sizeof &twice` 는 합법 — `8`**. clang 의 경고 2건 중 하나는 `twice` 가 **실제로 쓰이지 않아 내보내지 않는다**는 것이다.

### 3. 섹션 — **`table_ro` 는 PIE 기본에서 `.data.rel.ro`(gcc `.data.rel.ro.local`) · `-fno-PIE` 에서만 `.rodata`** ★★★

**출력**

```text
===== 테이블이 놓이는 섹션 — 컴파일러 2 × 플래그 3 (objdump -t 의 섹션 칸) (exit=0) =====
컴파일러 플래그     table_rw (const 없음)  | table_ro (* const)
gcc      (기본)     .data.rel.local        | .data.rel.ro.local
gcc      -fno-PIE   .data                  | .rodata
gcc      -fPIC      .data.rel.local        | .data.rel.ro.local
clang    (기본)     .data                  | .data.rel.ro
clang    -fno-PIE   .data                  | .rodata
clang    -fPIC      .data                  | .data.rel.ro
```

```text
===== gcc -std=c17 -O2 -c s35c.c -o c.o && objdump -t c.o | grep -E 'table_|op_' | expand (exit=0) =====
0000000000000000 l     F .text  0000000000000008 op_add
0000000000000010 l     F .text  0000000000000009 op_sub
0000000000000020 l     F .text  000000000000000a op_mul
0000000000000000 g     O .data.rel.local        0000000000000018 table_rw
0000000000000000 g     O .data.rel.ro.local     0000000000000018 table_ro
```

```text
===== gcc -std=c17 -O2 -c s35c.c -o c.o && objdump -r -j .data.rel.ro.local c.o | sed -n '/RELOCATION/,$p' (exit=0) =====
RELOCATION RECORDS FOR [.data.rel.ro.local]:
OFFSET           TYPE              VALUE
0000000000000000 R_X86_64_64       .text
0000000000000008 R_X86_64_64       .text+0x0000000000000010
0000000000000010 R_X86_64_64       .text+0x0000000000000020


```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s35c.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^call_rw:/,$p' | grep -v '^table_' (cc exit=0) =====
call_rw:
        endbr64
        movsx   rax, edi
        mov     edi, esi
        mov     esi, edx
        lea     rdx, table_rw[rip]
        jmp     [QWORD PTR [rdx+rax*8]]
call_ro:
        endbr64
        movsx   rax, edi
        mov     edi, esi
        mov     esi, edx
        lea     rdx, table_ro[rip]
        jmp     [QWORD PTR [rdx+rax*8]]
```

**왜 그런가**

- ★★★ **테이블의 값이 함수 주소**라서 **적재 위치에 따라 바뀐다** — `objdump -r` 이 `table_ro` 의 세 칸에 **`R_X86_64_64 .text+…`** 재배치를 붙였다. 적재 때 **써서 채워야** 하므로 `.rodata` 가 아니라 **`.data.rel.ro`** 에 둔다.
- ★★ **`-fno-PIE` 는 주소가 링크 때 정해지므로** `.rodata` 에 둘 수 있다.
- ★★ **`table_rw` 는 쓰기 섹션**(gcc `.data.rel.local`/`.data`, clang `.data`).
- ★ **호출 번역은 같다** — 둘 다 `jmp [QWORD PTR [rdx+rax*8]]`.

### 4. `const` 테이블에 쓰기 — **네 벌 다 `run exit=139` · `[1]` 만 찍힌다** ★★

**출력**

```text
===== const 테이블에 캐스트로 쓰기 — 컴파일러 2 × PIE 유무 (마커는 표준 오류) (exit=0) =====
gcc    (기본)            run exit=139 | [1] after writing table_rw[0]|
gcc    -no-pie -fno-PIE  run exit=139 | [1] after writing table_rw[0]|
clang  (기본)            run exit=139 | [1] after writing table_rw[0]|
clang  -no-pie -fno-PIE  run exit=139 | [1] after writing table_rw[0]|
```

**왜 그런가**

- ★★ **`table_rw` 쓰기는 되고 `table_ro` 쓰기에서 죽었다**(`[2]` 가 없다).
- ★★ **길이 다르다** — PIE 판은 `.data.rel.ro` 가 **적재 뒤 읽기 전용이 된** 것, 비-PIE 판은 처음부터 `.rodata`.
- ★★★ **규칙으로 적지 않는다** — 원래 `const` 인 객체를 고치는 것은 **UB** 다. `139` 는 이 판의 링커·적재기의 결과다.

### 5. 서명이 다른 호출 — **gcc 는 캐스트를 `-Wextra` 경고로 · clang 은 호출을 `-fsanitize=function` 으로 · gcc 에는 그 옵션이 없다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s35e.c -o /dev/null (cc exit=0) =====
s35e.c: In function ‘main’:
s35e.c:8:16: warning: cast between incompatible function types from ‘int (*)(int)’ to ‘int (*)(long int)’ [-Wcast-function-type]
    8 |     FnLong g = (FnLong)take_int;          /* 서명이 다른 타입으로 캐스트 */
      |                ^
```

```text
===== gcc -std=c17 -Wall -c s35e.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s35e.c -o /dev/null (cc exit=0) =====
```

```text
===== 서명이 다른 함수 포인터로 부르기 — 컴파일러 2 × 플래그 3 (-std=c17 -O0 -g) (exit=0) =====
gcc    (없음)                cc exit=0 · run exit=0 · runtime error 0줄
gcc    -fsanitize=undefined  cc exit=0 · run exit=0 · runtime error 0줄
gcc    -fsanitize=function   cc exit=1 | error: unrecognized argument to ‘-fsanitize=’ option: ‘function’
clang  (없음)                cc exit=0 · run exit=0 · runtime error 0줄
clang  -fsanitize=undefined  cc exit=0 · run exit=0 · runtime error 1줄
clang  -fsanitize=function   cc exit=0 · run exit=0 · runtime error 1줄
(sanitizer 를 켠 칸 중) 답한 칸 2 / 3
```

```text
===== clang -std=c17 -O0 -g -fsanitize=function -ffile-prefix-map="$PWD"=. s35e.c -o x && ./x (exit=0) =====
[1] before the call
s35e.c:10:13: runtime error: call to function take_int through pointer to incorrect function type 'int (*)(long)'
s35e.c:3: note: take_int defined here
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s35e.c:10:13 
[2] after the call, r = 42
```

```text
===== gcc -std=c17 -O0 -g -fsanitize=function s35e.c -o x (cc exit=1) =====
gcc: error: unrecognized argument to ‘-fsanitize=’ option: ‘function’
```

**왜 그런가**

- ★★★ **캐스트 자체는 합법, 호출은 UB** — 표준 문장 그대로다(바꿨다 되돌리면 같다 · 호환되지 않는 타입으로 부르면 UB).
- ★★★ **컴파일 단계** — gcc 만 **`-Wcast-function-type`** 을 낸다(`-Wall` 만으로는 0건 · `-Wextra` 가 켠다). clang 은 0건.
- ★★★ **실행 단계** — clang **`-fsanitize=function`**(그것을 포함한 `-fsanitize=undefined` 도)이 `call to function take_int through pointer to incorrect function type` 으로 잡는다. gcc 는 **옵션이 없어** `cc exit=1`, gcc UBSan 은 침묵. **답한 칸 2 / 3**.
- ★★ **`r = 42` 는 근거가 아니다** — `long` 의 아래 32비트가 이 호출 규약에서 우연히 `int` 자리에 앉은 **UB 의 관찰**이다.

### 6. 비교자 — **`cmp_sub` 네 벌 `no` · `cmp_rel` 네 벌 `yes` · UBSan `s35d.c:7:14` · 기본은 멈추지 않는다** ★★★

**출력**

```text
===== qsort 비교자 둘 — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
cmp_sub  1 3 2147483647 -2147483648 -2 0   | sorted? no
cmp_rel  -2147483648 -2 0 1 3 2147483647   | sorted? yes
--- gcc -O2
cmp_sub  1 3 2147483647 -2147483648 -2 0   | sorted? no
cmp_rel  -2147483648 -2 0 1 3 2147483647   | sorted? yes
--- clang -O0
cmp_sub  1 3 2147483647 -2147483648 -2 0   | sorted? no
cmp_rel  -2147483648 -2 0 1 3 2147483647   | sorted? yes
--- clang -O2
cmp_sub  1 3 2147483647 -2147483648 -2 0   | sorted? no
cmp_rel  -2147483648 -2 0 1 3 2147483647   | sorted? yes
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s35d.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s35d.c:7:14: runtime error: signed integer overflow: -2147483648 - 1 cannot be represented in type 'int'
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=undefined -ffile-prefix-map="$PWD"=. s35d.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s35d.c:7:14: runtime error: signed integer overflow: -2147483648 - 1 cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s35d.c:7:14 
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=signed-integer-overflow -fno-sanitize-recover=all -ffile-prefix-map="$PWD"=. s35d.c -o x && ./x (exit=1) =====
s35d.c:7:14: runtime error: signed integer overflow: -2147483648 - 1 cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s35d.c:7:14 
```

**왜 그런가**

- ★★★ **`INT_MIN - 1` 이 넘친다** — 부호 있는 오버플로는 **UB** 이고, 이 판에서는 큰 양수로 감겨 「`INT_MIN` 이 `1` 보다 크다」는 답이 됐다.
- ★★★ **UBSan 은 기본으로 계속 달린다**(`exit=0`) — 첫 건에서 멈추려면 **`-fno-sanitize-recover=all`**(clang 판 `exit=1`).
- ★★ **순서 자체는 근거가 아니다** — 표준은 비교 결과가 **서로 일관되어 전체 순서를 이루어야 한다**고 요구한다. 넘친 뺄셈은 그것을 깨므로 이것도 **UB** 이고, 숫자의 순서는 **이 glibc `qsort` 의 결과**다. 근거는 **`sorted?`** 칸뿐이다.
- ★ **처방** — `(a > b) - (a < b)`. 값이 −1 · 0 · 1 뿐이라 넘칠 수 없다(여기는 UB 가 판마다 갈리는 자리가 아니라 **UB 를 안 만드는 식**이라 처방을 적는다).

### 7. `signal` 모양 — **「int 와 핸들러를 받아, int 를 받고 void 를 돌려주는 함수의 포인터를 돌려주는 함수」 · 교차 대입 경고 0** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s35g.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s35g.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s35g.c -o x ; ./x (cc exit=0 · run exit=0) =====
on(2)
```

**왜 그런가**

- ★★ **안쪽 → 바깥** — `set_raw` → `(int, void (*)(int))` 를 받는 함수 → `*` 포인터를 돌려주고 → `(int)` 를 받는 함수를 가리키고 → `void` 를 돌려준다([01번 형제](../01-declaration-syntax-and-reading/)).
- ★★ **같은 타입의 증거** — 두 함수를 **서로의 타입으로 적은 포인터에 바꿔 담았는데** 두 컴파일러 다 **경고 0 · `cc exit=0`**. 타입이 다르면 `-Wall` 이 호환되지 않는 포인터 대입을 말했을 것이다.

### 8. `void *` 경계 — **gcc 두 방향 경고 · clang `-pedantic-errors` 로도 0 · 제약 위반이 아니다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s35f.c -o /dev/null (cc exit=0) =====
s35f.c: In function ‘as_object’:
s35f.c:3:43: warning: ISO C forbids conversion of function pointer to object pointer type [-Wpedantic]
    3 | void *as_object(void)            { return (void *)twice; }
      |                                           ^
s35f.c: In function ‘as_function’:
s35f.c:4:43: warning: ISO C forbids conversion of object pointer to function pointer type [-Wpedantic]
    4 | int (*as_function(void *p))(int) { return (int (*)(int))p; }
      |                                           ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s35f.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -pedantic-errors -c s35f.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★ **표준 문서의 캐스트 제약은 「스칼라 타입이면 된다」까지**다 — 함수 포인터 ↔ 객체 포인터는 **제약으로 막지 않고, 뜻을 정하지 않았다.** 부록 J 의 **흔한 확장** 목록에 있다. → **조건부 표준 층**(POSIX `dlsym` 이 요구한다는 것은 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)의 서술 — 이 편은 POSIX 문서를 열지 않았다).
- ★ **gcc 의 「forbids」는 문구가 표준보다 세다** — 종료 코드는 `0` 이다. 진단 문구보다 **종료 코드와 표준 문장**을 근거로 쓴다.

### 9. 다섯 층 — **표준이 본체 · 섹션은 구현 정의 · UB 넷 · 조건부 표준 하나** ★★★

**왜 그런가**

- **표준** — 함수 지시자 → 포인터 · 함수 포인터끼리 캐스트 왕복 · `sizeof` 함수 금지 · 비교자 계약.
- **조건부 표준** — 함수 포인터 ↔ `void *`.
- **구현 정의** — ★★★ **섹션 이름 · 재배치 · RELRO** · `sizeof twice = 1` · 호출 번역.
- **미명시** — 해당 없음(`qsort` 순서는 UB 쪽이다).
- **UB** — 서명이 다른 호출 · 비교자 오버플로 · 일관되지 않은 비교자 · `const` 테이블 쓰기.
- ★★★ **본체 창이 구현 정의 칸에 있다** — 「`const` 가 어디에 놓이나」는 **표준이 말하지 않는다.** 표준은 「고치면 UB」까지이고, **어디에 놓여 어떻게 막히나는 툴체인의 일**이다.
- ★★ **「종료 코드 0인데 ill-formed」** — `sizeof twice`(두 컴파일러).
- ★★ **다른 창에서 말한 자리** — 서명이 다른 호출(gcc 컴파일 경고 / clang 실행 sanitizer).

### 10. 다른 언어 ★

**출력**

```text
===== rustc s35r.rs -o r ; ./r (cc exit=0 · run exit=0) =====
f(5) = 10  g(5) = 6  h(5) = 15
size_of fn ptr = 8
size_of h      = 4
```

```text
===== rustc s35r2.rs -o r2 (rustc exit=1) =====
error[E0308]: mismatched types
 --> s35r2.rs:3:29
  |
3 |     let f: fn(i32) -> i32 = move |x| x + k;  // 잡는 클로저를 fn 에 담으면?
  |            --------------   ^^^^^^^^^^^^^^ expected fn pointer, found closure
  |            |
  |            expected due to this
  |
  = note: expected fn pointer `fn(i32) -> i32`
                found closure `{closure@s35r2.rs:3:29: 3:37}`
note: closures can only be coerced to `fn` types if they do not capture any variables
 --> s35r2.rs:3:42
  |
3 |     let f: fn(i32) -> i32 = move |x| x + k;  // 잡는 클로저를 fn 에 담으면?
  |                                          ^ `k` captured here

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0308`.
```

**왜 그런가**

- ★ **Rust — 잡은 클로저는 `fn` 포인터가 될 수 없다**(`E0308`) · 안 잡은 클로저는 된다(8바이트 — C 의 함수 포인터와 같은 크기). **상태를 실은 호출 가능 값**은 **클로저 타입**이 따로 있다.
- ★ **C++ `std::function`** — 함수 포인터 · 람다 · 함수 객체를 **하나의 호출 가능 타입**으로 묶는다. C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **40번**(람다는 **39번**) — 아직 폴더가 없다.

### 11. 경계 ★

**왜 그런가**

- **선언 읽기** — [01번 형제](../01-declaration-syntax-and-reading/) · **`typedef`** — [06번 형제](../06-typedef-and-type-aliases/).
- **`void *` 의 첫 실측** — [14번 형제](../14-pointers-address-dereference-and-pointer-types/).
- ★ 이 주제가 책임지는 것 — ① **테이블의 자리**(섹션 · 재배치) ② **콜백의 사고와 그것을 잡는 창** ③ **함수 포인터의 선언과 값**.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s35a.c`·`s35b.c` | ★★ 네 벌 같은 포인터 · `sizeof` 제약 위반인데 `exit=0` | 실행 3 · 진단 1 · 격자 4 |
| `s35c.c`·`s35c2.c` | ★★★ **섹션 격자** · `R_X86_64_64` · `jmp [rdx+rax*8]` · 쓰면 `139` | 격자 6 · objdump 2 · 어셈블리 1 · 실행 4 |
| `s35d.c` | ★★★ `sorted? no` · UBSan `7:14` · 기본은 계속 | 격자 4 · UBSan 3 |
| `s35e.c` | ★★★ gcc `-Wextra` 경고 · clang `-fsanitize=function` · gcc 옵션 없음 · 2 / 3 | 진단 3 · 격자 6 · 실행 2 |
| `s35f.c`·`s35g.c` | ★★ `void *` gcc만 · 교차 대입 0 | 진단 5 · 실행 1 |
| `s35r.rs`·`s35r2.rs` | ★ Rust `fn` 대 클로저 | 실행 1 · 컴파일 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3번 섹션 격자** — 섹션 이름과 PIE 기본값은 툴체인(gcc·clang·binutils·배포판)의 선택이다.
- ★★ **4번의 `139`** — 이 판의 RELRO · 적재기의 결과(UB).
- ★★ **5번의 `r = 42` · 6번의 순서** — UB 의 이 판 결과.
- ★ **5번의 도구 격자** — gcc 13 에 `-fsanitize=function` 이 없는 것, clang 18 에 `-Wcast-function-type` 이 이 캐스트에 안 나는 것.

**함수 지시자의 변환 · 함수 포인터 캐스트 왕복 · 호환되지 않는 타입의 호출이 UB 인 것 · `sizeof` 함수 금지 · 비교자 계약은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `readelf -l` 의 RELRO 구간 캡처 · 상태를 싣는 콜백(`void *` 인자) · C23 `typeof` · `-fcf-protection` 끄기.
- ★ **못 잰 것** — **간접 호출의 시간**(규칙으로 안 쟀다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번 섹션 격자** — 기본 PIE 여부나 섹션 명명이 바뀔 수 있다.
- ★★ **5번 도구 격자** — gcc 가 `-fsanitize=function` 을 들여올 수 있다.
- ★ **6번** — glibc `qsort` 가 바뀌면 순서(근거 아님)가 바뀐다. `sorted?` 는 그대로일 것이다.
