# c/syntax/35 — 함수 포인터와 콜백 테이블: 「**함수 이름은 주소가 되고, 테이블은 재배치를 기다린다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `qsort` 비교 결과가 「**서로 일관되어 전체 순서를 이루어야 한다**」는 문장, 「**한 타입의 함수 포인터를 다른 타입으로 바꿨다 되돌리면 같다 · 호환되지 않는 타입으로 부르면 UB**」, `sizeof` 를 **함수 타입에 쓰지 못한다**는 제약, 캐스트 연산자의 제약(함수 포인터 ↔ 객체 포인터를 **제약으로는 막지 않는다**), 부록 J 의 「**함수 포인터 캐스트**」가 **흔한 확장**에 적힌 것을 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **섹션 이름·재배치·종료 코드·sanitizer 리포트는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **테이블의 자리는 판 격자**(컴파일러 2 × PIE 기본 / `-fno-PIE` / `-fPIC`)로, **sanitizer 는 탐침 격자**로 돌렸다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 함수 포인터·`qsort` 는 **C89 부터**다. 이 편의 규칙은 판 사이에 **바뀌지 않았다.** ★ `typeof` 같은 C23 도구는 쓰지 않았다.
> ★★ **경계** — **선언을 안쪽 → 바깥으로 읽는 법**(나선 규칙이라고도 부른다)은 [01번 형제](../01-declaration-syntax-and-reading/)가, **`typedef` 로 자르는 법**은 [06번 형제](../06-typedef-and-type-aliases/)가, **함수 포인터 → `void *` 가 ISO 밖이라는 첫 실측**은 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이다. 여기는 「**테이블 · 콜백 · 서명이 어긋난 호출**」을 본다.\
> ★ **`const` 의 뜻**은 [31번 형제](../31-const-and-pointer-const-placement/)가, **sanitizer 사용법**은 목록의 **58번 주제**가 정본이다.
> 선행 — [06번 형제](../06-typedef-and-type-aliases/) · [14번 형제](../14-pointers-address-dereference-and-pointer-types/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — 오브젝트 파일의 섹션과 재배치다.** 디스패치 테이블(함수 포인터 배열)이 **어느 섹션에 놓이는지**를 `objdump -t` 로 판 격자에 올린다 — **「`const` 면 `.rodata`」가 아니었다.**
★★ 그리고 **콜백의 사고는 sanitizer 창**으로 본다 — `qsort` 비교자의 오버플로 · 서명이 어긋난 호출.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | `sizeof` 함수 · 서명이 다른 캐스트(gcc `-Wcast-function-type`) · `void *` 변환(gcc `-Wpedantic`) — ★ **clang 은 뒤의 둘에 0건** | 씀 |
| ② 실행 출력 | `f`·`&f`·`*f`·`**f` 가 같은 값 · `qsort` 가 **정렬됐나** · `const` 테이블에 쓰면 `run exit` | 씀 |
| ③ sanitizer | ★★ UBSan `signed integer overflow`(비교자) · ★★ clang **`-fsanitize=function`**(서명 불일치) · gcc 에는 **그 옵션이 없다** | 씀 |
| ★★★ ④ **오브젝트 섹션 · 재배치** | ★ **본체** — `table_ro` 가 **`.data.rel.ro`** 류 · `-fno-PIE` 에서만 **`.rodata`** · 재배치 **`R_X86_64_64`** | 씀 |
| ⑤ `-O2` 어셈블리 | 테이블 호출이 **`jmp [rdx+rax*8]`** 한 줄 | 씀 |
| 시간 측정 | 「간접 호출은 느리다」 | ★ **안 쟀다**(규칙 — 재지 않은 성능 주장 금지) |
| ★ 제5의 상태 | 「`const` 테이블이 정말 읽기 전용인가」를 **섹션 이름**으로 물으면 `.data.rel.ro` 라는 **쓰기 가능한 이름**이 나온다 — **실행해서 써 보는 창**으로 바꿔 물어 **`run exit=139`** 를 봤다 | 창을 바꿔 답함 |

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
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **섹션 격자 · 재배치 · 어셈블리** | 같은 컴파일러 · 같은 플래그면 같다 |
| 안 흔들린다 | ★★ **`sorted? no / yes`** · `qsort` 결과의 순서 | 같은 glibc `qsort` · 같은 입력 |
| 안 흔들린다 | ★★ UBSan 리포트의 **`파일:줄:칸`** · `run exit`(`0` · `1` · `139`) | 같은 자리를 밟는다 |
| 안 흔들린다 | ★ 서명이 어긋난 호출의 **`r = 42`** | UB 지만 이 판의 번역이 정해져 있다 — 「**이 판의 값**」이다 |

★★ **정규화 규칙은 기본 넷뿐**이다 — 재배치 블록의 오프셋(`.text+0x…`)이 주소 규칙에 걸리지만 **원문이 같아** 흔들리지 않는다.

## 한눈에 — 쉽게 말하면

**함수 포인터는 「내선 번호표」다. 디스패치 테이블은 그 번호표를 붙인 게시판이다.**

- **이름을 부르면 곧 번호** — 부서 이름(`twice`)을 적든, 「부서 이름의 번호」(`&twice`)를 적든, **같은 번호**가 적힌다. → **`f` · `&f` · `*f` · `**f` 가 전부 같은 포인터**
- **게시판의 번호는 건물을 옮기면 다시 적어야 한다** — 이사(프로그램 적재)할 때마다 주소가 바뀌니 **적재기가 번호를 고쳐 적고 나서** 잠근다. → **`const` 테이블이 `.rodata` 가 아니라 `.data.rel.ro` 에 놓인다**
- **번호를 잘못 이해하면** — 「3층 회계팀」 번호로 「3층 인사팀」에 전화하면 **누군가는 받지만 엉뚱한 사람**이다. → **서명이 다른 함수 포인터로 부르기** — UB, 이 판에서는 **값이 우연히 맞았다**
- **순서를 묻는 심판이 계산을 틀리면** — 「A 가 B 보다 큰가」를 **뺄셈으로** 답하다 넘치면 **줄 세우기가 틀린다.** → **`return a - b` 비교자**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 이름 = 번호 | 함수 지시자가 포인터로 바뀐다 | ★★ **네 벌 다 같다**(`p1 == p4 : 1`) |
| 이사 뒤 다시 적는 게시판 | `table_ro` → `.data.rel.ro` + `R_X86_64_64` | ★★★ **섹션 격자** |
| 다시 적은 뒤 잠근 게시판 | RELRO — 적재 뒤 읽기 전용 | ★★ **써 보면 `139`** |
| 엉뚱한 사람이 받는 전화 | 서명이 다른 함수 포인터 호출 | ★★ clang **`-fsanitize=function`** 만 |
| 넘치는 심판 | `a - b` 비교자 | ★★ **`sorted? no`** · UBSan |

```text
   int (*const table_ro[3])(int, int) = { op_add, op_sub, op_mul };

   컴파일할 때 (.o)                        적재할 때 (실행 파일)
   ------------------------------------    ------------------------------------
   table_ro : 빈 칸 셋 (0 으로 채움)        적재기가 op_* 의 실제 주소를 채운다
   재배치   : R_X86_64_64 .text+0x0 …       (PIE 는 주소가 적재마다 다르다)
   섹션     : .data.rel.ro(.local)          채운 뒤 그 페이지를 읽기 전용으로
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 함수 지시자의 변환 · 함수 포인터끼리의 변환 · `qsort` 의 계약.
- ★★★ **「UB」 칸이 셋**이다 — 서명이 다른 호출 · 비교자의 부호 있는 오버플로 · `const` 객체에 쓰기.
- ★★ **「조건부 표준」 칸이 드물게 찬다** — 함수 포인터 ↔ `void *` 는 ISO C 가 정의하지 않고, **다른 표준(POSIX)이 요구**한다.

> **함수 지시자(function designator)** — 함수 타입을 가진 식. `sizeof`·`&` 의 피연산자가 아니면 **「그 함수를 가리키는 포인터」로 바뀐다.**\
> 예: `twice` 는 대부분의 자리에서 `&twice` 와 같다.

> **디스패치 테이블(dispatch table)** — 함수 포인터 배열. **번호로 함수를 고른다.**\
> 예: `table_ro[i](a, b)`.

> **재배치(relocation)** — 링크·적재 때 **주소를 채워 넣으라는 표시**. 함수 주소가 적재 위치에 따라 바뀌면 필요하다.\
> 예: `R_X86_64_64 .text+0x10`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **디스패치 테이블은 어디에 놓이나** — `const` 가 있을 때와 없을 때, PIE 일 때와 아닐 때.
2. ★★★ **콜백이 틀리면 무엇이 나오나** — `qsort` 비교자와 서명이 다른 호출, **그리고 누가 잡나.**
3. ★★ **함수 포인터의 선언과 값** — 이름이 포인터가 되는 자리, `signal` 모양의 선언, `void *` 와의 경계.

## 동작 방식

### (1) ★★ 함수 이름은 포인터가 된다 — `f` · `&f` · `*f` · `**f`

**언제 쓰나** — 「`&` 를 붙여야 하나 · `(*fp)()` 로 불러야 하나」가 헷갈릴 때.

```c
/* s35a.c */
#include <stdio.h>

static int twice(int x) { return 2 * x; }

int main(void) {
    int (*p1)(int) = twice;
    int (*p2)(int) = &twice;
    int (*p3)(int) = *twice;
    int (*p4)(int) = **twice;
    printf("p1 == p2 : %d   p1 == p3 : %d   p1 == p4 : %d\n", p1 == p2, p1 == p3, p1 == p4);
    printf("p1(5) = %d   (*p1)(5) = %d   (**p1)(5) = %d   (***p1)(5) = %d\n",
           p1(5), (*p1)(5), (**p1)(5), (***p1)(5));
    printf("sizeof p1 = %zu\n", sizeof p1);
    return 0;
}
```

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

- ★★★ **네 초기자가 전부 같은 포인터**다 — `twice` 는 곧바로 포인터로 바뀌고, `*twice` 는 「포인터를 풀어 함수」가 됐다가 **다시 포인터로** 바뀐다. `**twice` 도 같다.
- ★★ **부를 때도 같다** — `p1(5)` · `(*p1)(5)` · `(***p1)(5)` 가 전부 `10`. 함수 호출 연산자는 **함수 포인터를 받는다**([01번 형제](../01-declaration-syntax-and-reading/)의 「형태가 둘인 것이지 뜻이 둘인 게 아니다」).
- ★ **포인터 하나는 8바이트**다(이 판).

**예외 둘 — `sizeof` 와 `&`**

```c
/* s35b.c */
#include <stdio.h>

static int twice(int x) { return 2 * x; }

int main(void) {
    printf("sizeof twice  = %zu\n", sizeof twice);
    printf("sizeof &twice = %zu\n", sizeof &twice);
    return 0;
}
```

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

- ★★★ **`sizeof twice` 는 제약 위반**이다 — 함수 지시자는 `sizeof` 의 피연산자일 때 **포인터로 안 바뀌고**, 표준은 함수 타입에 `sizeof` 를 쓰지 못하게 한다.
- ★★★ **그런데 두 컴파일러 다 `-pedantic` 에서 `exit=0`** 이고 값 **`1`** 을 낸다(GNU 확장). `-pedantic-errors` 라야 `exit=1`. → **「종료 코드 0인데 ill-formed」**
- ★ **`sizeof &twice` 는 합법 — `8`**.

### (2) ★★★ 디스패치 테이블은 어디에 놓이나 — 섹션 격자

**언제 쓰나** — 「테이블에 `const` 를 붙이면 읽기 전용 섹션에 들어가겠지」라고 생각할 때. ★★★ **이 편의 본체**다.

```c
/* s35c.c */
static int op_add(int a, int b) { return a + b; }
static int op_sub(int a, int b) { return a - b; }
static int op_mul(int a, int b) { return a * b; }

int (*table_rw[3])(int, int)       = { op_add, op_sub, op_mul };
int (*const table_ro[3])(int, int) = { op_add, op_sub, op_mul };

int call_rw(int i, int a, int b) { return table_rw[i](a, b); }
int call_ro(int i, int a, int b) { return table_ro[i](a, b); }
```

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

그림 해설 (한 단계씩):

- ★★★ **`const` 를 붙인 `table_ro` 는 기본 빌드에서 `.rodata` 가 아니다** — gcc `.data.rel.ro.local` · clang `.data.rel.ro`. **`-fno-PIE` 에서만 `.rodata`** 다.
- ★★★ **이유는 재배치**다 — `table_ro` 에는 **`R_X86_64_64 .text+…`** 가 셋 붙어 있다. 테이블의 값이 **함수 주소**라서, PIE(적재 위치가 매번 다른 실행 파일)에서는 **적재기가 채워 넣어야** 한다. 채울 곳은 적재 때 **쓸 수 있어야** 하므로 `.rodata` 에 못 둔다.
- ★★ **`const` 없는 `table_rw` 는 쓰기 섹션**이다 — gcc 는 PIE 에서 `.data.rel.local`, clang 은 늘 `.data`. **이름이 다를 뿐 둘 다 쓰기 가능**이다(섹션 이름 고르기는 구현의 것이다).
- ★★ **부르는 쪽은 둘 다 한 줄** — `jmp [QWORD PTR [rdx+rax*8]]`. `const` 는 **호출 번역을 안 바꿨다**(이 판 · `-O2`).
- ★ **`-fPIC` 는 기본(PIE)과 같은 칸**이다 — 이 판의 기본 빌드가 **이미 PIE** 이기 때문이다.

### (3) ★★ `const` 테이블에 써 보면 — 제5의 상태

**언제 쓰나** — 「`.data.rel.ro` 는 이름에 `data` 가 있으니 쓸 수 있나」를 물을 때.

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

```text
===== const 테이블에 캐스트로 쓰기 — 컴파일러 2 × PIE 유무 (마커는 표준 오류) (exit=0) =====
gcc    (기본)            run exit=139 | [1] after writing table_rw[0]|
gcc    -no-pie -fno-PIE  run exit=139 | [1] after writing table_rw[0]|
clang  (기본)            run exit=139 | [1] after writing table_rw[0]|
clang  -no-pie -fno-PIE  run exit=139 | [1] after writing table_rw[0]|
```

- ★★★ **네 벌 다 `run exit=139`** — `[1]` 은 찍히고 **`[2]` 는 안 찍혔다.** `table_rw` 쓰기는 되고 **`table_ro` 쓰기에서 죽었다.**
- ★★ **PIE 에서도 `-no-pie` 에서도 같다** — PIE 판은 `.data.rel.ro` 가 **적재 뒤 읽기 전용이 된 것**(RELRO), 비-PIE 판은 처음부터 `.rodata` 다. **가는 길이 다르고 결과가 같다.**
- ★★★ **이것은 UB 의 한 판 결과**다 — **원래 `const` 인 객체를 고치는 것은 UB**([31번 형제](../31-const-and-pointer-const-placement/)). `139` 는 **이 판의 적재기와 링커가 만든 결과**이고, 「`const` 테이블은 쓰면 죽는다」는 **규칙이 아니다.**
- ★ **섹션 이름만 보면 틀린 결론**이 나온다 — `.data.rel.ro` 는 이름에 `data` 가 있지만 **실행 중에는 읽기 전용**이었다. **창을 바꿔 물어야** 보인다.

### (4) ★★★ `qsort` 비교자 — `return a - b` 가 넘친다

**언제 쓰나** — 정수 배열을 `qsort` 로 정렬하는 비교자를 쓸 때.

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

```text
   cmp_sub(INT_MIN, 1)  =  -2147483648 - 1   ->  int 를 넘는다 (부호 있는 오버플로 — UB)
                                               이 판에서는 큰 양수로 감겨
                                               "INT_MIN 이 1 보다 크다" 로 읽혔다
   cmp_rel(INT_MIN, 1)  =  (a > b) - (a < b)  =  0 - 1  =  -1     넘칠 수 없다
```

- ★★★ **`cmp_sub` 는 네 벌 다 `sorted? no`** — `INT_MIN` 이 섞이자 **정렬이 틀렸다.** `cmp_rel` 은 네 벌 다 `yes`.
- ★★★ **UBSan 이 자리까지 짚는다** — `s35d.c:7:14: runtime error: signed integer overflow: -2147483648 - 1`. 두 컴파일러 같은 줄 · 같은 칸이다.
- ★★ **UBSan 은 기본으로 계속 달린다** — `exit=0` 에 정렬도 끝까지 한다. **첫 건에서 죽이려면** `-fno-sanitize-recover=all` — clang 판이 **`exit=1`** 이다.
- ★★ **비교자의 계약은 「음수 · 0 · 양수」다** — 뺄셈은 **그 부호를 넘침 없이** 못 낸다. `(a > b) - (a < b)` 는 **값이 −1 · 0 · 1 뿐**이라 넘칠 수 없다.
- ★★ **`qsort` 결과의 순서 자체**(`1 3 2147483647 …`)는 **이 glibc `qsort` 의 관찰**이다 — 표준은 비교 결과가 **서로 일관되어 전체 순서를 이루어야 한다**고 요구하고, 넘친 뺄셈은 그 요구를 깬다. **그러니 오버플로 말고도 UB 가 하나 더** 있는 셈이다. 근거로 쓰는 칸은 **`sorted?`** 뿐이다.

### (5) ★★★ 서명이 다른 함수 포인터로 부르기 — 두 컴파일러 대비

**언제 쓰나** — 콜백 타입이 조금 안 맞아서 **캐스트로 끼워 맞췄을 때.**

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

그림 해설 (한 단계씩):

- ★★★ **표준 문장 그대로** — 함수 포인터는 **다른 타입으로 바꿨다 되돌려도 같다**(캐스트 자체는 합법). 그런데 **호환되지 않는 타입으로 부르면 UB** 다. `int (*)(int)` 를 `int (*)(long)` 으로 부른 것이 그것이다.
- ★★★ **컴파일 단계** — gcc 는 **`-Wcast-function-type`**(`-Wall` 만으로는 **0건** — 아래 블록 — `-Wextra` 가 켠다)으로 캐스트를 짚고, **clang 은 0건**이다.
- ★★★ **실행 단계** — **clang `-fsanitize=function`**(그리고 그것을 포함한 `-fsanitize=undefined`)이 **`call to function take_int through pointer to incorrect function type`** 으로 잡는다. **gcc 는 `-fsanitize=function` 옵션이 없다** — `unrecognized argument`, `cc exit=1`. gcc UBSan 은 **침묵**한다.
- ★★ **탐침 셋 중 답한 칸 둘** — 둘 다 clang 이다. **두 컴파일러가 정반대 창에서 말했다** — gcc 는 **컴파일 경고로만**, clang 은 **실행 sanitizer 로만.**
```text
   FnLong g = (FnLong)take_int;   g(41L);

                     컴파일할 때 (캐스트)             실행할 때 (호출)
                     ------------------------------   ------------------------------
   gcc 13            -Wcast-function-type 경고        -fsanitize=function 없음
                     (-Wextra 가 켠다)                 UBSan 침묵
   clang 18          경고 0                           -fsanitize=function 이 잡는다
```

- ★★ **`r = 42` 는 이 판의 우연**이다 — x86-64 에서 `long` 의 아래 32비트가 `int` 자리에 그대로 앉았다. **UB 의 관찰**이다.

### (6) ★★ `signal` 모양의 선언 — 안쪽 → 바깥, 그리고 `typedef`

**언제 쓰나** — `void (*signal(int, void (*)(int)))(int);` 를 만났을 때.

```c
/* s35g.c */
#include <stdio.h>

typedef void (*Handler)(int);

void (*set_raw(int sig, void (*fn)(int)))(int);   /* signal 과 같은 모양 */
Handler set_td(int sig, Handler fn);              /* typedef 로 푼 것 */

static Handler current;

void (*set_raw(int sig, void (*fn)(int)))(int) {
    (void)sig;
    Handler old = current;
    current = fn;
    return old;
}

Handler set_td(int sig, Handler fn) { return set_raw(sig, fn); }

static void on(int s) { printf("on(%d)\n", s); }

int main(void) {
    Handler (*a)(int, Handler)              = set_raw;   /* 서로 바꿔 담는다 */
    void (*(*b)(int, void (*)(int)))(int)   = set_td;
    a(2, on);
    Handler old = b(2, NULL);
    old(2);
    return 0;
}
```

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

```text
   void (*set_raw(int sig, void (*fn)(int)))(int);

   ① set_raw                         "set_raw 는"
   ② set_raw(int, void (*)(int))     "int 와 (int 를 받는 함수의 포인터)를 받는 함수이고"
   ③ (*set_raw(…))                   "그 함수는 포인터를 돌려준다"
   ④ (*set_raw(…))(int)              "그 포인터는 int 를 받는 함수를 가리키고"
   ⑤ void (*set_raw(…))(int)         "그 함수는 void 를 돌려준다"

   typedef void (*Handler)(int);  ->  Handler set_td(int sig, Handler fn);   같은 타입
```

- ★★★ **두 선언이 같은 타입**이다 — `set_raw` 를 `Handler (*)(int, Handler)` 에, `set_td` 를 손으로 쓴 긴 타입에 **서로 바꿔 담았는데** 두 컴파일러 다 **경고 0건 · `cc exit=0`** 이다.
- ★★ **읽는 순서는 [01번 형제](../01-declaration-syntax-and-reading/)의 안쪽 → 바깥** — 이름에서 시작해 **오른쪽(괄호·대괄호)을 먼저**, 막히면 왼쪽(`*`)으로.
- ★ **`typedef` 하나가 괄호 두 겹을 없앤다** — [06번 형제](../06-typedef-and-type-aliases/)의 「함수 포인터는 `typedef` 가 가장 값을 내는 자리」.

### (7) ★★ 함수 포인터 ↔ `void *` — 조건부 표준 층

**언제 쓰나** — `dlsym` 처럼 `void *` 로 받은 주소를 함수로 부를 때.

```c
/* s35f.c */
static int twice(int x) { return 2 * x; }

void *as_object(void)            { return (void *)twice; }
int (*as_function(void *p))(int) { return (int (*)(int))p; }
```

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

- ★★★ **gcc 는 두 방향 다 `-Wpedantic` 경고**(`ISO C forbids conversion …`) · **clang 은 `-pedantic-errors` 로도 0건**이다 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 한 방향으로 잰 것을 **두 방향 · 두 강도**로 넓혔다.
- ★★★ **표준 문서에서 이것은 제약 위반이 아니다** — 캐스트의 제약은 **스칼라 타입이면 된다**까지이고, 함수 포인터와 객체 포인터 사이의 변환은 **뜻을 정하지 않았다.** 부록 J 가 「**흔한 확장**」으로 적어 둔 자리다. ★ gcc 의 「**forbids**」는 **문구가 표준보다 세다**(진단 문구는 틀릴 수도 있다 — 종료 코드는 `0`).
- ★★ **그래서 층은 「조건부 표준」이다** — ISO C 는 보장하지 않고, POSIX 의 `dlsym` 은 **이 변환이 되기를 요구한다**(14편의 서술 — ★ 이 편은 POSIX 문서를 **열어 확인하지 않았다**).

### (8) ★ Rust 의 `fn` 포인터와 클로저 — 대비

**언제 쓰나** — 「C 의 함수 포인터에 상태를 싣고 싶다」를 다른 언어는 어떻게 푸나 볼 때.

```rust
// s35r.rs
fn twice(x: i32) -> i32 { 2 * x }

fn main() {
    let k = 10;
    let f: fn(i32) -> i32 = twice;          // 함수 포인터
    let g: fn(i32) -> i32 = |x| x + 1;      // 아무것도 안 잡는 클로저
    let h = move |x: i32| x + k;            // k 를 잡는 클로저
    println!("f(5) = {}  g(5) = {}  h(5) = {}", f(5), g(5), h(5));
    println!("size_of fn ptr = {}", std::mem::size_of_val(&f));
    println!("size_of h      = {}", std::mem::size_of_val(&h));
}
```

```text
===== rustc s35r.rs -o r ; ./r (cc exit=0 · run exit=0) =====
f(5) = 10  g(5) = 6  h(5) = 15
size_of fn ptr = 8
size_of h      = 4
```

```rust
// s35r2.rs
fn main() {
    let k = 10;
    let f: fn(i32) -> i32 = move |x| x + k;  // 잡는 클로저를 fn 에 담으면?
    println!("{}", f(5));
}
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

- ★★ **아무것도 안 잡는 클로저는 `fn` 포인터가 된다**(`g`) — C 의 함수 포인터와 같은 8바이트다.
- ★★ **무언가 잡는 클로저는 `fn` 이 될 수 없다** — `E0308` · `closures can only be coerced to fn types if they do not capture any variables`. 잡은 `k` 는 **클로저 값 안에**(4바이트) 산다.
- ★ **C 에는 이 구분이 없다** — 상태를 싣고 싶으면 **`void *` 인자를 하나 더** 넘기는 관용구(`qsort_r` 류)를 쓴다(★ **던지지 않았다**). Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **35번**이 `fn` 과 클로저의 정본이 될 자리다(아직 폴더가 없다).

## 문법 — 형태와 규칙

### 형태

(1)의 `s35a.c` · (2)의 `s35c.c` · (6)의 `s35g.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 뜻 | 층 |
|---|---|---|
| `int (*fp)(int) = twice;` | 함수 포인터 선언 + 대입(`&` 없어도 같다) | ★★★ 표준 |
| `fp(5)` · `(*fp)(5)` | 호출 — 두 형태 같은 뜻 | 표준 |
| `int (*table[3])(int, int)` | 함수 포인터 배열(디스패치 테이블) | 표준 |
| `int (*const table[3])(int, int)` | 원소가 `const` 인 테이블 — ★ 섹션은 PIE 에서 `.data.rel.ro` | 표준 + 섹션은 구현 |
| `typedef void (*Handler)(int);` | 함수 포인터 별칭 | 표준 |
| `int (*cmp)(const void *, const void *)` | `qsort` 비교자 서명 | ★★★ 표준(음수 · 0 · 양수 계약) |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `sizeof twice` | 두 컴파일러 경고 · ★ **`exit=0`** · 값 `1` | ★★★ 제약 위반 | (1) |
| `return a - b;`(비교자) | 경고 0 · `sorted? no` · UBSan `signed integer overflow` | ★★★ UB | (4) |
| 서명이 다른 포인터로 부르기 | gcc `-Wcast-function-type` · clang 0 · clang `-fsanitize=function` | ★★★ UB | (5) |
| `const` 테이블에 캐스트로 쓰기 | 경고 0 · **`run exit=139`**(네 벌) | ★★★ UB | (3) |
| 함수 포인터 ↔ `void *` | gcc `-Wpedantic` · clang 0 · `exit=0` | ★★ 조건부 표준(ISO 미정의 · POSIX 요구) | (7) |

### 규칙 불릿

- ★★★ **함수 이름은 `sizeof`·`&` 밖에서 포인터가 된다** — `f`·`&f`·`*f`·`**f` 가 같다.
- ★★★ **함수 포인터끼리의 캐스트는 합법, 호환되지 않는 타입으로 부르기는 UB** 다.
- ★★★ **비교자는 부호만 맞히면 된다** — 뺄셈은 넘친다. `(a > b) - (a < b)`.
- ★★ **`const` 테이블도 PIE 에서는 재배치 때문에 `.data.rel.ro`** 다 — 적재 뒤 읽기 전용(이 판).
- ★★ **함수 포인터 ↔ `void *` 는 ISO C 밖**이다 — gcc 만 말한다.
- ★ **긴 선언은 안쪽 → 바깥으로 읽고, `typedef` 로 자른다.**

## 어디서 틀리나

### 1. ★★★ 「`const` 를 붙이면 테이블이 `.rodata` 에 들어간다」

**PIE 에서는 `.data.rel.ro`** 다((2)). 재배치가 필요한 값(함수 주소)은 **적재 때 써야** 한다. `.rodata` 는 **`-fno-PIE`** 에서만이었다.

### 2. ★★★ 「`return a - b;` 는 정석 비교자다」

**`INT_MIN` 하나에 정렬이 틀렸다**((4)). UBSan 이 **`signed integer overflow`** 로 짚는다. 경고는 **0건**이다.

### 3. ★★★ 「캐스트로 서명을 맞추면 부를 수 있다」

**캐스트는 합법, 호출은 UB** 다((5)). gcc 는 **캐스트를** 경고하고 clang 은 **호출을** 실행 중에 잡는다 — **한쪽 컴파일러만 쓰면 한쪽 창만 열린다.**

### 4. ★★ 「`sizeof` 로 함수 크기를 잴 수 있다」

**제약 위반**이다((1)) — 그런데 `exit=0` 에 `1` 이 나온다. `-pedantic-errors` 라야 막힌다.

### 5. ★★ 「clang 이 조용하니 `void *` 변환은 표준이다」

**ISO C 가 정하지 않은 변환**이다((7)). clang 은 **`-pedantic-errors` 로도** 말하지 않는다.

### 6. ★ 「간접 호출은 느리니 테이블을 피하자」

**재지 않았다.** 이 편은 호출이 **`jmp [rdx+rax*8]` 한 줄**이라는 것까지만 봤다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 함수 포인터의 변환 규칙이 짧고 단단하다.\
★★★ **「구현 정의」 칸이 본체 창(섹션)을 품는다** — 섹션 이름과 RELRO 는 표준 밖이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ 함수 지시자 → 포인터 · **함수 포인터끼리 캐스트 왕복은 같다** · `sizeof` 함수 타입 금지(제약) · `qsort` 비교자의 계약 · `const` 원소 테이블의 타입 | `p1 == p4 : 1` · `sizeof` 진단 · `cmp_rel` `yes` · 교차 대입 0건 |
| ★★ **조건부 표준** | 다른 표준·확장이 정할 때만 | ★★ **함수 포인터 ↔ `void *`**(ISO 미정의 · 부록 J 흔한 확장 · POSIX 요구) | gcc 경고 · clang 0 |
| ★★★ **구현 정의** | 문서화 의무가 있다(또는 도구의 선택) | ★★★ **테이블이 놓이는 섹션**(`.data.rel.ro` · `.rodata` · `.data.rel.local` · `.data`) · 재배치 종류 · RELRO · `sizeof twice = 1`(GNU 확장) · 호출 번역 | 섹션 격자 · 재배치 · `139` · 어셈블리 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음** — ★ 「모순된 비교자를 받은 `qsort` 의 순서」는 미명시처럼 보이지만, 표준은 비교 결과가 **서로 일관되어 전체 순서를 이루어야 한다(shall)** 고 적는다. 제약 밖의 「shall」을 어기면 **UB** 다 — 아래 칸 | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **서명이 다른 포인터로 부르기** · **비교자의 부호 있는 오버플로** · ★★ **일관되지 않은 비교자를 `qsort` 에 주기** · **`const` 테이블에 쓰기** | `r = 42` · `sorted? no`(순서 `1 3 2147483647 …` 는 이 glibc 의 결과) · `run exit=139` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`sizeof twice` 는 두 컴파일러 다 `-pedantic` 에서 `exit=0`** — 「**종료 코드 0인데 ill-formed**」 새 항목 |
| ★★ **조건부 표준** | ★★ **clang 은 `void *` 변환에 `-pedantic-errors` 로도 0건** |
| ★★★ **구현 정의** | ★★ **섹션 이름은 쓰기 가능 여부를 말하지 않는다** — `.data.rel.ro` 는 실행 중 읽기 전용이었다 |
| ★★★ **UB** | ★★★ **gcc 에는 서명 불일치 호출을 실행 중에 잡는 도구가 없다**(`-fsanitize=function` 없음 · UBSan 침묵) · ★★ **clang 은 그 캐스트에 컴파일 경고 0** · ★ **`const` 테이블 쓰기는 경고 0** — 죽는 것은 이 판의 적재기 덕이다 · ★ **비교자 오버플로는 컴파일 경고 0** |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **서명이 어긋난 호출은 두 컴파일러를 같이 써야 두 창이 다 열린다** — gcc 는 캐스트를, clang 은 호출을 봤다.
  - ★★★ **섹션 이름으로 보호를 판단하지 마라** — 실행해서 써 봐야 알았다.
  - ★★ **콜백의 계약(부호)은 UBSan 이 가장 잘 본다** — 자리를 `줄:칸` 까지 짚었다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 번호로 함수를 고르기 | ★★★ **`int (*const table[N])(…)`** — 원소를 `const` 로 | 원소가 `const` 가 아닌 테이블(쓰기 섹션에 남는다) |
| 정수 비교자 | ★★★ **`(a > b) - (a < b)`** | `return a - b;` |
| 콜백 타입이 조금 다를 때 | ★★★ **맞는 서명의 얇은 감싸개 함수** | 캐스트로 끼워 맞추기(UB) |
| 긴 함수 포인터 선언 | ★★ **`typedef`** | 괄호 세 겹을 손으로 |
| `dlsym` 결과를 함수로 | ★ POSIX 가 요구하는 캐스트 — **ISO 밖**이라는 것을 안다 | 「표준이니까」라고 믿기 |
| 콜백을 시험 | ★★ **clang `-fsanitize=undefined`** + gcc `-Wextra` 둘 다 | 한 컴파일러만 |

판단 규칙 두 줄.

- ★★★ **「이 포인터로 부르는 함수의 진짜 서명이 무엇인가」를 호출 자리에서 답할 수 없으면** 캐스트로 맞추지 말고 감싸개를 쓴다.
- ★★ **테이블은 원소를 `const` 로** — 섹션은 판에 따라 다르지만, 적어도 이 판에서는 **실행 중 쓰기가 막혔다.**

## 핵심 문장

- ★★★ **`const` 원소 디스패치 테이블은 PIE 기본 빌드에서 `.rodata` 가 아니라 `.data.rel.ro`(gcc `.data.rel.ro.local`)에 놓였다** — 함수 주소가 재배치(`R_X86_64_64`)를 기다리기 때문이다. `-fno-PIE` 에서만 `.rodata`.
- ★★★ **그 테이블에 캐스트로 쓰면 네 벌 다 `run exit=139`** 였다 — UB 의 관찰이다.
- ★★★ **`return a - b` 비교자는 `INT_MIN` 이 섞이자 정렬이 틀렸고(`sorted? no`), UBSan 이 `s35d.c:7:14` 의 `signed integer overflow` 로 짚었다.**
- ★★★ **서명이 다른 함수 포인터 호출은 gcc 가 캐스트를 `-Wcast-function-type` 으로, clang 이 호출을 `-fsanitize=function` 으로 잡았다** — gcc 에는 그 sanitizer 가 없다.
- ★★ **`f`·`&f`·`*f`·`**f` 는 같은 포인터다** — `sizeof f` 만 예외(제약 위반인데 두 컴파일러 `exit=0` · 값 `1`).
- ★★ **함수 포인터 ↔ `void *` 는 gcc 만 경고하고 clang 은 `-pedantic-errors` 로도 조용하다** — ISO 가 정하지 않은 조건부 표준 층이다.
- ★ **`signal` 모양의 선언과 `typedef` 로 푼 선언은 서로 대입해도 경고 0 — 같은 타입이다.**

## 관련 자료

- [01번 형제 — 선언 문법과 읽는 법](../01-declaration-syntax-and-reading/) — ★★ **선행.** 안쪽 → 바깥으로 읽기의 정본. (6)이 그 규칙을 `signal` 모양에 썼다.
- [06번 형제 — `typedef` 와 타입 별칭](../06-typedef-and-type-aliases/) — ★★ **선행.** 「함수 포인터는 `typedef` 가 가장 값을 내는 자리」의 정본 예고가 이 편이다.
- [14번 형제 — 포인터](../14-pointers-address-dereference-and-pointer-types/) — ★★ 함수 포인터 → `void *` 의 **첫 실측**. 이 편은 두 방향 · 두 강도로 넓혔다.
- [31번 형제 — `const`](../31-const-and-pointer-const-placement/) — ★ 원래 `const` 인 객체를 고치면 UB.
- 목록의 **58번 주제** — sanitizer 사용법의 정본.
- ★ C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **39번**(람다와 캡처) · **40번**(`std::function`·호출 가능 타입) — C 의 함수 포인터를 **상태를 실은 호출 가능 객체**로 넓힌 쪽. 아직 폴더가 없다.
- ★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **35번**(함수 포인터와 클로저 반환) — (8)의 정본이 될 자리. 아직 폴더가 없다.

## 용어 풀이

> **함수 포인터** — 함수를 가리키는 포인터. 호출할 수 있다.\
> 예: `int (*fp)(int) = twice; fp(5);`.

> **함수 지시자** — 함수 타입의 식. `sizeof`·`&` 밖에서는 포인터로 바뀐다.\
> 예: `twice`.

> **디스패치 테이블** — 함수 포인터 배열.\
> 예: `table_ro[i](a, b)`.

> **콜백(callback)** — 다른 함수에 넘겨져 **그쪽이 불러 주는** 함수.\
> 예: `qsort` 의 비교자.

> **PIE(Position Independent Executable)** — 적재 위치가 매번 달라도 도는 실행 파일. 이 판의 기본값이다.\
> 예: `-no-pie -fno-PIE` 로 끈다.

> **재배치 · RELRO** — 재배치는 적재 때 주소를 채우라는 표시, RELRO 는 **채운 뒤 그 페이지를 읽기 전용으로** 바꾸는 링커·적재기의 장치.\
> 예: `.data.rel.ro` 에 쓰면 `139`.

> **`-fsanitize=function`** — clang 의 UBSan 검사. **함수를 호환되지 않는 타입의 포인터로 부르는 것**을 실행 중에 잡는다. gcc 에는 없다.\
> 예: `call to function take_int through pointer to incorrect function type`.

> **`-Wcast-function-type`** — gcc 의 경고. **서명이 호환되지 않는 함수 포인터 캐스트**를 짚는다. 이 판에서는 `-Wextra` 가 켰다.\
> 예: `int (*)(int)` → `int (*)(long int)`.

## 더 들어가면

- ★★ **실행 파일에서 `.data.rel.ro` 가 RELRO 구간에 드는지** — 예비로 `readelf -l` 을 봤지만 **블록으로 캡처하지 않았으므로** 근거로 쓰지 않는다. (3)의 `139` 가 이 편의 근거다.
- ★★ **`qsort_r` · 상태를 싣는 콜백** — C 에는 표준 `qsort_r` 이 없다(판마다 다르다). ★ **던지지 않았다.**
- ★ **C23 `typeof` 로 함수 포인터 타입 쓰기** — ★ **던지지 않았다.**
- ★ **gcc 의 `-fcf-protection`(`endbr64`)과 간접 호출** — 어셈블리의 `endbr64` 가 그 흔적이다. ★ **다루지 않았다.**
- ★ **간접 호출의 비용** — ★ **안 쟀다**(규칙).
