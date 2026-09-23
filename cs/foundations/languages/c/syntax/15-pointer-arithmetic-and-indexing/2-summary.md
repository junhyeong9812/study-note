# c/syntax/15 — 포인터 산술과 인덱싱: 「**`a[i]` 는 문법이 아니라 축약이다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Array subscript / Pointer arithmetic](https://en.cppreference.com/w/c/language/operator_member_access) · [GCC 13 Instrumentation Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Instrumentation-Options.html) · [Clang UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
> **실행 검증** — 이 문서의 모든 출력·경고·sanitizer 진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c13`, 소스 파일명은 언제나 `ex.c` 다 — sanitizer 출력에 경로가 박히기 때문이다.\
> ★★ **실행 블록은 `./x 2>&1 | cat` (또는 `| sed -n '1,/^SUMMARY/p'`) 으로 받았다** —\
> sanitizer 는 stderr, `printf` 는 stdout 이라 **터미널과 파이프에서 순서가 달라진다.**\
> 섞이는 프로그램에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣어 **순서를 고정**했고 소스에 그렇게 적혀 있다.\
> ★ 그 한 줄이 없으면 **ASan 이 죽는 판에서 stdout 이 통째로 사라진다**(이 문서를 쓰며 실제로 그랬다).
> ★★ **흔들리는 칸 / 안 흔들리는 칸** — 이 주제는 **UB 의 값이 본문에 실리므로** 이 선언이 특히 중요하다.
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | `%p` 주소값 · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | 주소들 **사이의 차이** · `sizeof` 값 |
> | ★ **UB 가 만든 값**(`*end` · `a[10]` · `NULL+1`) | ★ **그 값이 「갈린다」는 사실** |
> | ASan 리포트의 **Shadow bytes** 와 메모리 덤프 | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 |
> | — | **종료 코드**(`cc exit` 과 `run exit` 을 갈라 적었다) |
>
> **버전** — 포인터 산술과 인덱싱의 규칙은 **C89 이후 바뀐 적이 없다.**\
> ★ **C23 이 하나 바꿨다** — `NULL + 0` 이 정의된 동작이 됐다. 아래 (5)에서 던져 본다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계** — 포인터의 **타입과 역참조**는 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이고 이 주제는 **그 위에 선다.**\
> **배열이 포인터가 되는 자리**는 [16번 형제](../16-array-pointer-decay-and-function-parameters/), **`*p++` 의 우선순위**는 [09번 형제](../09-operator-precedence-and-associativity/)가 정본이다.\
> **경계를 넘는 접근이 왜** 「**죽지 않을 수 있는가**」는 목록의 **56번 주제**가 정본이다.
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [09번 형제](../09-operator-precedence-and-associativity/).

## 한눈에 — 쉽게 말하면

**포인터 산술은 「몇 번째 칸」이지 「몇 바이트」가 아니다.**

아파트 복도를 걷는다고 하자.\
`p + 1` 은 「**한 걸음**」이 아니라 「**한 집**」이다.\
집이 넓으면 한 집 가는 데 더 많이 걷는다 — **집 크기가 걸음 수를 정한다.**

그래서 같은 `+ 1` 인데 `char *` 는 1바이트, `int *` 는 4바이트, `double *` 는 8바이트를 간다.

그리고 **`a[i]` 는 문법이 아니라 축약**이다 — 표준이 `a[i]` 를 **`*(a + i)` 로 정의**한다.\
덧셈은 **순서를 바꿔도 같으므로** `*(i + a)` 도 같고, 그래서 `i[a]` 도 **컴파일된다.**

| 비유 | 실체 | 층 |
|---|---|---|
| 한 걸음이 아니라 한 집 | `p + 1` 이 `sizeof *p` 만큼 | **표준** |
| 집 번호 차이 | `q - p` 가 **원소 개수** | **표준** |
| 그 차이를 담는 자 | `ptrdiff_t` — **부호 있는 정수** | **표준**(폭은 구현 정의) |
| 「3번 집」 == 「집의 3번」 | `a[3]` == `3[a]` | **표준** |
| 복도 끝에서 한 발 더 | `a + n` — **만들 수 있다** | **표준** |
| 그 자리의 문을 여는 것 | `*(a + n)` | ★ **UB** |
| 두 걸음 더 | `a + n + 1` | ★ **UB** — 만들기만 해도 |
| 다른 동 복도와 거리 재기 | 서로 다른 배열끼리 뺄셈 | ★ **UB** |
| 없는 건물에서 한 집 가기 | `NULL + 1` | ★ **UB**(C23 도 `+0` 만 풀었다) |

```text
   int a[5] = {10, 20, 30, 40, 50};   ★ int 는 4바이트

   인덱스     0     1     2     3     4    (끝 한 칸 뒤)
            +-----+-----+-----+-----+-----+ - - -+
            |  10 |  20 |  30 |  40 |  50 |  ??  |
            +-----+-----+-----+-----+-----+ - - -+
   주소 +0     +4    +8   +12   +16   +20
   포인터   a           a+2                 ★ a+5
                                             만들어도 되고 비교해도 된다
                                             ★ 역참조하면 UB

   a[2]  ==  *(a + 2)  ==  *(2 + a)  ==  2[a]     <- 전부 30
```

- ★★ **이 주제는 UB 가 본체**다. [13번 형제](../13-goto-cleanup-idiom/)가 **표준이 본체**였던 것과 정반대이고,\
  [11번 형제](../11-bitwise-operations-and-shifts/)와 같은 모양이다.
- ★★★ **그리고 그 UB 를 도구가 거의 못 본다.** 아래 (5)에서 **세 자리 전부 컴파일러 경고 0건**이고,\
  ★ **한 자리는 gcc·clang·sanitizer 조합에 따라 답이 셋으로 갈렸다**(`4` · `-4` · `8`).

> **스케일링(scaling)** — 포인터에 정수를 더할 때 **가리키는 타입의 크기를 곱하는 것**.\
> 예: `int *p` 에서 `p + 1` 은 주소가 **4 늘어난다**(이 환경에서).

> **`ptrdiff_t`** — 두 포인터를 뺀 결과의 타입(`<stddef.h>`). **부호 있는 정수**다.\
> 예: `&a[1] - &a[4]` 는 `-3` 이다. `size_t` 로 받으면 거대한 양수가 된다.

> **끝 한 칸 뒤(one past the end)** — 배열의 마지막 원소 **바로 다음 자리**를 가리키는 포인터.\
> 예: `int a[5]` 에서 `a + 5`. **만들고 비교하는 것은 합법**, **역참조는 UB**.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **`p + 1` 이 몇 바이트 가는지를 무엇으로 보이나** — 주소 차이로 찍는다.
2. ★★★ **`a[i]` 가 `*(a+i)` 라는 것의 관찰 가능한 결과는 무엇인가** — `i[a]` 를 던져 본다.
3. ★★★ **포인터 산술의 UB 세 자리를 도구가 어디까지 보나** — **세 자리 전부 컴파일러는 침묵**이다.

## 동작 방식

### (1) `p + 1` 은 **타입 크기만큼** 움직인다 — 주소 차이로 본다

**언제 쓰나** — 「포인터에 1 을 더하면 1바이트 가겠지」라고 생각했을 때.

```text
===== 소스: ex.c (15-a) =====
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

int main(void) {
    int    ai[5] = {10, 20, 30, 40, 50};
    char   ac[5] = {1, 2, 3, 4, 5};
    double ad[5] = {1, 2, 3, 4, 5};

    int    *pi = ai;
    char   *pc = ac;
    double *pd = ad;

    printf("타입      sizeof  p        p+1      주소 차이(바이트)\n");
    printf("int    %8zu  %p  %p  %ld\n", sizeof *pi, (void *)pi, (void *)(pi + 1),
           (long)((uintptr_t)(pi + 1) - (uintptr_t)pi));
    printf("char   %8zu  %p  %p  %ld\n", sizeof *pc, (void *)pc, (void *)(pc + 1),
           (long)((uintptr_t)(pc + 1) - (uintptr_t)pc));
    printf("double %8zu  %p  %p  %ld\n", sizeof *pd, (void *)pd, (void *)(pd + 1),
           (long)((uintptr_t)(pd + 1) - (uintptr_t)pd));

    /* ★ 포인터 뺄셈은 바이트가 아니라 "원소 개수" 를 돌려준다 */
    ptrdiff_t d = &ai[4] - &ai[1];
    printf("\n&ai[4] - &ai[1] = %td   (원소 개수)\n", d);
    printf("바이트로는       = %ld\n", (long)((uintptr_t)&ai[4] - (uintptr_t)&ai[1]));
    printf("sizeof(ptrdiff_t) = %zu   sizeof(size_t) = %zu\n",
           sizeof(ptrdiff_t), sizeof(size_t));

    /* 뺀 순서를 뒤집으면 음수 — ptrdiff_t 는 부호 있는 타입이다 */
    printf("&ai[1] - &ai[4] = %td   (음수가 나온다)\n", &ai[1] - &ai[4]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
타입      sizeof  p        p+1      주소 차이(바이트)
int           4  0x7ffff6bd1360  0x7ffff6bd1364  4
char          1  0x7ffff6bd13b3  0x7ffff6bd13b4  1
double        8  0x7ffff6bd1380  0x7ffff6bd1388  8

&ai[4] - &ai[1] = 3   (원소 개수)
바이트로는       = 12
sizeof(ptrdiff_t) = 8   sizeof(size_t) = 8
&ai[1] - &ai[4] = -3   (음수가 나온다)
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** `0x7ffff6bd1360` 은 실행마다 바뀐다.\
> 근거는 **「주소 차이 == `sizeof *p`」** 라는 세 줄의 대응과 **뺄셈이 원소 개수 3 을 낸다**는 것이다.

```text
   같은 "+1" 인데 보폭이 다르다

   char *pc      [0][1][2][3][4]        pc+1 은 +1 바이트
                  ^  ^

   int *pi       [ 0 ][ 1 ][ 2 ]        pi+1 은 +4 바이트
                  ^    ^

   double *pd    [   0   ][   1   ]     pd+1 은 +8 바이트
                  ^       ^

   ★ 규칙 한 줄 :  (p + n) 의 주소 =  p 의 주소 + n * sizeof(*p)
```

```text
   뺄셈은 그 역이다

   &ai[4] - &ai[1]  =  (16 - 4) / 4  =  3      <- 원소 개수
                        바이트 차이 12
```

그림 해설 (한 단계씩):

- ★★ **주소 차이가 `sizeof *p` 와 정확히 같다** — 세 줄이 `4`·`1`·`8` 로 대응한다.\
  **포인터 산술의 단위는 바이트가 아니라** 「**가리키는 타입 한 개**」다.
- ★ **뺄셈은 그 역연산**이다 — 바이트 차이 **12** 를 `sizeof(int)` 로 나눈 **3** 이 나온다.
- ★★ **`ptrdiff_t` 는 부호 있는 타입**이다. 순서를 뒤집으면 **`-3`** 이 나온다.\
  ★ **`size_t` 로 받으면 안 된다** — 같은 8바이트지만 부호가 없어 **거대한 양수**가 된다.
- **서식 지정자는 `%td`** 다(`ptrdiff_t` 용). `%d` 로 찍으면 `-Wformat` 이 잡는다.
- ★ `sizeof(ptrdiff_t)` 와 `sizeof(size_t)` 가 **둘 다 8** 인 것은 **구현 정의**다.

비용 — 없다. **컴파일러가 곱셈을 대신 해 준다.**

### (2) `a[i]` 는 `*(a + i)` 로 **정의된다** — 그래서 `i[a]` 도 된다

**언제 쓰나** — 「인덱싱은 배열만의 문법 아닌가?」라고 생각했을 때.

```text
===== 소스: ex.c (15-b) =====
#include <stdio.h>

int main(void) {
    int a[5] = {10, 20, 30, 40, 50};
    int i = 2;
    int *p = a;

    printf("a[i]      = %d\n", a[i]);
    printf("*(a + i)  = %d\n", *(a + i));
    printf("*(i + a)  = %d\n", *(i + a));
    printf("i[a]      = %d   <- ★ 되는가?\n", i[a]);
    printf("p[i]      = %d\n", p[i]);
    printf("i[p]      = %d\n", i[p]);
    printf("2[a]      = %d\n", 2[a]);

    printf("\n같은가 : a[i]==*(a+i) %d   a[i]==i[a] %d   &a[i]==&i[a] %d\n",
           a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);

    i[a] = 99;                 /* 좌변으로도 쓸 수 있나 */
    printf("i[a] = 99 후 : a[2] = %d\n", a[2]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:17:35: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                   ^~
ex.c:17:50: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                                  ^~
a[i]      = 30
*(a + i)  = 30
*(i + a)  = 30
i[a]      = 30   <- ★ 되는가?
p[i]      = 30
i[p]      = 30
2[a]      = 30

같은가 : a[i]==*(a+i) 1   a[i]==i[a] 1   &a[i]==&i[a] 1
i[a] = 99 후 : a[2] = 99
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:17:35: warning: self-comparison always evaluates to true [-Wtautological-compare]
   17 |            a[i] == *(a + i), a[i] == i[a], &a[i] == &i[a]);
      |                                   ^
1 warning generated.
(출력은 gcc 와 바이트 단위로 같다)
```

```text
   표준이 정의하는 것

       a[i]   ==   *(a + i)          <- 인덱싱은 "축약" 이다

   덧셈은 교환 가능하므로

       *(a + i)  ==  *(i + a)  ==  i[a]

   ★ 그래서 2[a] 도 컴파일되고 좌변으로도 쓸 수 있다.
     "배열의 2번" 이 아니라 "주소 + 2 칸의 값" 이기 때문이다.
```

그림 해설 (한 단계씩):

- **일곱 줄이 전부 30** 이다. `i[a]`·`i[p]`·`2[a]` 까지 **컴파일되고 같은 값**을 낸다.
- ★★★ **컴파일러가 스스로 증명해 준다** — gcc 가 `a[i] == i[a]` 를 **`self-comparison`**(자기 자신과의 비교)이라고 경고했다.\
  **같은 식이라는 것을 컴파일러가 안다**는 뜻이다. `&a[i] == &i[a]` 도 같다.
- ★ **gcc 는 2건, clang 은 1건**이다 — clang 은 `&a[i] == &i[a]` 쪽을 잡지 않았다. **잡는 범위가 다르다.**
- **`i[a] = 99` 가 좌변으로 동작한다** — `a[2]` 가 99 가 됐다. **완전히 같은 식**이라 당연하다.
- ★ **이 사실이 실무에서 쓸모 있는 것은 아니다.** `i[a]` 를 쓰면 안 된다.\
  ★ **쓸모 있는 것은 「인덱싱에 경계 검사가 없다」는 함의**다 — `a[i]` 는 **주소 계산일 뿐**이고,\
  `i` 가 범위 안인지는 **아무도 확인하지 않는다.** 그것이 (4)·(5)의 UB 를 만든다.

비용 — 없다. **`a[i]` 와 `*(a+i)` 는 같은 기계어**다.

### (3) 끝 한 칸 뒤 포인터는 **합법**이고 역참조는 **UB** 다

**언제 쓰나** — `for (p = a; p != a + n; p++)` 관용구가 왜 안전한지 물을 때.

```text
===== 소스: ex.c (15-c) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {10, 20, 30, 40, 50};
    int *end = a + 5;              /* ★ 한 칸 뒤 포인터 — 합법이다 */

    printf("a      = %p\n", (void *)a);
    printf("a + 5  = %p   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)\n", (void *)end);
    printf("end - a = %td\n", end - a);
    printf("end > a ? %d\n", end > a);

    int sum = 0;
    for (int *p = a; p != end; p++) sum += *p;   /* 관용구 — end 를 역참조하지 않는다 */
    printf("합 = %d\n", sum);

    printf("\n이제 역참조한다 -> ★ UB\n");
    printf("*end = %d\n", *end);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
a      = 0x7ffd07decd70
a + 5  = 0x7ffd07decd84   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)
end - a = 5
end > a ? 1
합 = 150

이제 역참조한다 -> ★ UB
*end = 32765
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | sed -n '1,/^SUMMARY/p'  (run exit=1) =====
a      = 0x7d17eea00020
a + 5  = 0x7d17eea00034   (끝 한 칸 뒤 — 만들어도 되고 비교해도 된다)
end - a = 5
end > a ? 1
합 = 150

이제 역참조한다 -> ★ UB
ex.c:18:5: runtime error: load of address 0x7d17eea00034 with insufficient space for an object of type 'int'
0x7d17eea00034: note: pointer points here
  32 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
              ^ 
=================================================================
==3681571==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7d17eea00034 at pc 0x562b23d957e0 bp 0x7fffc09e9770 sp 0x7fffc09e9760
READ of size 4 at 0x7d17eea00034 thread T0
    #0 0x562b23d957df in main /tmp/c13/ex.c:18
    #1 0x7d17f0e2a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x7d17f0e2a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x562b23d95264 in _start (/tmp/c13/xs+0x2264) (BuildId: 9133f346a3176b3e9d14295232229cb6b620f63b)

Address 0x7d17eea00034 is located in stack of thread T0 at offset 52 in frame
    #0 0x562b23d95338 in main /tmp/c13/ex.c:3

  This frame has 1 object(s):
    [32, 52) 'a' (line 5) <== Memory access at offset 52 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c13/ex.c:18 in main
```

> ★ **대조할 것은 숫자가 아니라 성질이다.** 주소·PID·`BuildId` 와 **`*end` 의 값은 실행마다 바뀐다**\
> (위 두 블록에서 `32765` 와 `[32, 52)` 라는 프레임 범위는 같은 판이 아니다 — 판마다 값이 다르다).\
> 근거는 **① `a + 5` 를 만들고 비교하는 동안 진단이 0줄** ② **역참조한 18행에서만 두 도구가 동시에 말한다** ③ **run exit 이 0 에서 1 로 갈린다**는 것이다.\
> ★ **ASan 리포트는 `SUMMARY` 줄까지만 받았다**(`sed -n '1,/^SUMMARY/p'`) — 그 아래 Shadow bytes 범례는 주소뿐이다.

```text
   합법 구역                                 UB 구역
   +-----+-----+-----+-----+-----+  - - - +
   |  0  |  1  |  2  |  3  |  4  |  a+5   |
   +-----+-----+-----+-----+-----+  - - - +
    ^                             ^  ^
    a                             |  ★ 이 자리를 "가리키는 것" 은 합법
                                  |     비교·뺄셈도 합법
                                  |  ★ 이 자리를 "읽는 것" 은 UB
                                  a+5

   ★ 그래서 for (p = a; p != a+5; p++) 가 안전하다 —
     p 가 a+5 가 되는 순간 루프가 끝나 ★ 역참조하지 않는다.
```

그림 해설 (한 단계씩):

- **`a + 5` 를 만들고, `end - a` 를 계산하고, `end > a` 를 비교하는 것까지 전부 합법**이다.\
  진단이 **0줄**이고 값도 맞는다(`5` · `1`).
- **루프가 정확히 `150` 을 냈다** — `10+20+30+40+50`. **끝 한 칸 뒤를 종료 조건으로 쓰는 것이 관용구**인 이유다.
- ★★ **`*end` 에서만** 두 도구가 동시에 말한다 —\
  UBSan 이 **`insufficient space for an object of type 'int'`**,\
  ASan 이 **`stack-buffer-overflow`** 와 **`[32, 52) 'a' (line 4)`**(배열이 32\~52 에 있고 52 를 읽었다).
- ★ **그런데 평범한 실행에서는 안 죽었다** — `*end = 32767` 을 찍고 `exit=0` 으로 끝났다.\
  **「안 터졌다」는 「안전하다」가 아니다.** 경계 밖 접근이 **성공할 수 있다**는 것은 목록의 **56번 주제**가 정본이다.
- ★ **`a + 6` 은 만들기만 해도 UB** 다 — 합법인 것은 **끝 한 칸 뒤까지**다. (5)에서 그것을 던진다.

비용 — 없다. **종료 조건을 `!=` 로 쓰면 자연히 지켜진다.**

### (4) `*p++` 대 `(*p)++` — 포인터가 움직이나 값이 움직이나

**언제 쓰나** — 배열을 훑는 관용구를 읽을 때. **우선순위 규칙의 정본은 [09번 형제](../09-operator-precedence-and-associativity/)** 이고 여기서는 결론만 되짚는다.

```text
===== 소스: ex.c (15-i) =====
#include <stdio.h>
#include <stddef.h>

int main(void) {
    int arr[4] = {10, 20, 30, 40};
    int *p = arr;
    int v;

    v = *p++;                    /* 문을 나눠 잰다 — 한 printf 안에서 재지 않는다 */
    printf("*p++   = %d,  p - arr = %td\n", v, p - arr);

    p = arr;
    v = (*p)++;
    printf("(*p)++ = %d,  arr[0] = %d,  p - arr = %td\n", v, arr[0], p - arr);

    p = arr;
    v = *++p;
    printf("*++p   = %d,  p - arr = %td\n", v, p - arr);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, exit=0) =====
*p++   = 10,  p - arr = 1
(*p)++ = 10,  arr[0] = 11,  p - arr = 0
*++p   = 20,  p - arr = 1
```

```text
   *p++     ==  *(p++)     후위 ++ 가 단항 * 보다 세다 (09번 형제)
            ->  값 10 을 내고 ★ 포인터가 한 칸 간다     p - arr = 1

   (*p)++   ->  ★ 값이 11 이 되고 포인터는 그대로       p - arr = 0

   *++p     ->  먼저 한 칸 가고 그 자리 값 20           p - arr = 1
```

그림 해설 (한 단계씩):

- **`*p++` 는 `*(p++)`** 다 — **포인터가 움직이고** 값은 **움직이기 전 자리**의 것이다.
- **`(*p)++` 는 값이 움직이고** 포인터는 그대로다 — `arr[0]` 이 11 이 됐고 `p - arr` 가 0 이다.
- **`*++p` 는 먼저 가고 읽는다** — 20 이 나온다.
- ★ **문을 나눠서 쟀다.** 한 `printf` 안에서 `*p++` 와 `p - arr` 를 같이 재면\
  **인자 평가 순서가 미명시**라 값이 달라진다([10번 형제](../10-evaluation-order-and-sequence-points/)).\
  ★ [09번 형제](../09-operator-precedence-and-associativity/)에서 **실제로 그렇게 갈린 실측**이 있다.
- **포인터가 움직이는 폭은 (1)의 규칙 그대로**다 — `int *` 면 4바이트.

비용 — 없다. **괄호 하나가 뜻을 완전히 바꾼다.**

### (5) ★★★ 포인터 산술 UB 세 자리 — **도구가 어디까지 보나**

**언제 쓰나** — 「sanitizer 를 켰으니 UB 는 잡히겠지」라고 생각했을 때.

> ★★ **「전수 관찰」과 「빌드 깨기」는 다른 실행이다.** UBSan 은 **같은 소스 위치를 한 번만** 보고하고\
> `-fno-sanitize-recover=all` 은 **첫 건에서 죽어** 나머지를 감춘다.\
> 그래서 세 자리를 **각각 다른 프로그램으로** 던졌다.

#### 자리 ① — 배열 밖 포인터를 만들고 읽기

```text
===== 소스: ex.c (15-d) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {1, 2, 3, 4, 5};
    volatile int i = 10;
    int *p = a + i;                 /* ★ UB 1 — 배열 + 한 칸 뒤 를 넘는 포인터를 "만드는" 것 */
    printf("a + 10 = %p  (역참조는 하지 않았다)\n", (void *)p);
    printf("a[10] = %d   <- 여기서 읽는다\n", a[i]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
a + 10 = 0x7ffc923c9b38  (역참조는 하지 않았다)
a[10] = 325231050   <- 여기서 읽는다
```

```text
===== clang -std=c17 -g -fsanitize=undefined · ./x 2>&1 | cat  (run exit=0) =====
ex.c:7:16: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:7:16 
a + 10 = 0x7ffee0029338  (역참조는 하지 않았다)
ex.c:9:53: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:9:53 
a[10] = 1317183946   <- 여기서 읽는다
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | sed -n '1,/^SUMMARY/p'  (run exit=1) =====
a + 10 = 0x7c6008200068  (역참조는 하지 않았다)
ex.c:9:54: runtime error: index 10 out of bounds for type 'int [5]'
ex.c:9:5: runtime error: load of address 0x7c6008200068 with insufficient space for an object of type 'int'
0x7c6008200068: note: pointer points here
 00 00 00 00  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  00 c0 0f 08 60 7c 00 00  00 00 00 00
              ^ 
=================================================================
==3681600==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7c6008200068 at pc 0x6156008d869c bp 0x7fff1ec817d0 sp 0x7fff1ec817c0
READ of size 4 at 0x7c6008200068 thread T0
    #0 0x6156008d869b in main /tmp/c13/ex.c:9
    #1 0x7c600a62a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x7c600a62a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x6156008d8244 in _start (/tmp/c13/xs+0x1244) (BuildId: 6320b50f35ce20e097017f67142a880b9d12d33a)

Address 0x7c6008200068 is located in stack of thread T0 at offset 104 in frame
    #0 0x6156008d8318 in main /tmp/c13/ex.c:3

  This frame has 2 object(s):
    [48, 52) 'i' (line 6)
    [64, 84) 'a' (line 5) <== Memory access at offset 104 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c13/ex.c:9 in main
```

```text
===== 소스: ex.c (15-g) =====
#include <stdio.h>
int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int a[5] = {1, 2, 3, 4, 5};
    volatile int i = 10;
    int *p = a + i;                 /* 만들기만 한다 — 역참조하지 않는다 */
    printf("만들어진 포인터 = %p\n", (void *)p);
    return 0;
}
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | cat  (run exit=0) =====
만들어진 포인터 = 0x77b92d000068
```

```text
===== clang -std=c17 -g -fsanitize=undefined,address · ./x 2>&1 | cat  (run exit=0) =====
ex.c:6:16: runtime error: index 10 out of bounds for type 'int[5]'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:6:16 
만들어진 포인터 = 0x7633aba00048
```

- ★★★ **gcc 는 「포인터를 만드는 것」을 못 본다.** 7행(`a + i`)에서 아무 말도 없고,\
  **9행에서 실제로 읽을 때만** 말한다. clang 은 **7행에서 이미** 말한다.
- ★★ **그래서 「만들기만 하고 안 읽는」 코드(15-g)는 gcc 조합에서 진단 0줄에 run exit=0** 이다 — **UB 인데도.**\
  **clang 은 같은 코드에서 1줄**을 낸다.
- ★ **상수 첨자면 이야기가 다르다.** `volatile` 을 떼고 `int i = 10;` 으로 두면 —

```text
===== 같은 프로그램에서 volatile 만 뗀 판 =====
gcc   -std=c17 -Wall -Wextra -pedantic -O0 :  0 건
gcc   -std=c17 -Wall -Wextra -pedantic -O2 :  2 건   [-Warray-bounds=]
clang -std=c17 -Wall -Wextra -pedantic -O0 :  0 건
clang -std=c17 -Wall -Wextra -pedantic -O2 :  0 건
```

- ★★ **gcc 는 `-O2` 에서만 컴파일 타임에 잡는다.** `-O0` 은 0건이고 **clang 은 어느 수준에서도 0건**이다.\
  **한 최적화 수준만 돌리고 「도구가 잡는다/못 잡는다」를 단정하면 안 된다.**

#### 자리 ② — 서로 다른 배열의 포인터끼리 뺄셈

```text
===== 소스: ex.c (15-e) =====
#include <stdio.h>
#include <stddef.h>

int main(void) {
    int a[4] = {1, 2, 3, 4};
    int b[4] = {5, 6, 7, 8};
    ptrdiff_t d = b - a;            /* ★ UB 2 — 서로 다른 배열의 포인터끼리 뺄셈 */
    printf("b - a = %td\n", d);
    printf("b < a ? %d   (서로 다른 배열끼리의 비교도 미명시다)\n", b < a);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (cc exit=0 · run exit=0) =====
ex.c: In function ‘main’:
ex.c:9:71: warning: comparison between two arrays [-Warray-compare]
    9 |     printf("b < a ? %d   (서로 다른 배열끼리의 비교도 미명시다)\n", b < a);
      |                                                                       ^
ex.c:9:71: note: use ‘&b[0] < &a[0]’ to compare the addresses
b - a = 4
b < a ? 0   (서로 다른 배열끼리의 비교도 미명시다)
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (cc exit=0 · run exit=0) =====
ex.c:9:87: warning: array comparison always evaluates to a constant [-Wtautological-compare]
    9 |     printf("b < a ? %d   (서로 다른 배열끼리의 비교도 미명시다)\n", b < a);
      |                                                                       ^
1 warning generated.
b - a = -4
b < a ? 1   (서로 다른 배열끼리의 비교도 미명시다)
```

```text
===== 같은 소스를 40벌로 던진 결과 — b - a 의 값 =====
gcc   -O0/-O1/-O2/-O3/-Os                     b - a = 4
gcc   + -fsanitize=undefined                  b - a = 4
gcc   + -fsanitize=address (또는 address,undefined)   b - a = 8
clang -O0/-O1/-O2/-O3/-Os                     b - a = -4
clang + -fsanitize=undefined                  b - a = -4
clang + -fsanitize=address (또는 address,undefined)   b - a = 8

★ sanitizer 진단은 ★ 한 줄도 나오지 않았다 (뺄셈에 대해서는).
★ 경고는 "b < a" 쪽에만 나온다 — gcc 는 -Warray-compare, clang 은 -Wtautological-compare.
★ 그 "b < a" 의 ★ 값도 갈린다 — gcc 는 0, clang 은 1.
```

- ★★★ **같은 소스가 세 가지 답을 냈다** — **4**(gcc) · **-4**(clang) · **8**(ASan 을 켠 두 컴파일러 전부).
- ★★ **갈린 축이 최적화 수준이 아니었다.** `-O0`\~`-Os` 다섯 벌이 **전부 같았고**,\
  갈린 것은 **컴파일러**와 **ASan 을 켰는지**였다. ASan 이 **스택 객체 사이에 레드존을 넣어** 배치를 바꾼 것이다.\
  ★ **「어디에 넣어야 갈린다」는 처방은 없다** — 값·조건·누산을 다 던져 보고 **갈린 자리를 적는 수밖에 없다.**
- ★★★ **어떤 도구도 뺄셈 자체를 진단하지 않았다.** 경고는 **비교(`b < a`)** 쪽에만 났고,\
  gcc 는 `-Warray-compare`(「comparison between two arrays」), clang 은 `-Wtautological-compare`(「array comparison always evaluates to a constant」)로\
  **이름도 문구도 다르다.**
- ★★ **그리고 `b < a` 의 값도 갈린다** — **gcc 는 0, clang 은 1** 이다.\
  **뺄셈은 UB, 비교는 미명시**인데 **둘 다 컴파일러에 따라 답이 달라졌다.**
- ★ **gcc 의 `note:` 가 함정이다** — 「`&b[0] < &a[0]` 로 주소를 비교하라」고 권하는데,\
  **그렇게 고쳐도 서로 다른 객체의 포인터 비교라 미명시**다. **경고를 끄는 조언이지 UB 를 없애는 조언이 아니다.**

#### 자리 ③ — 널 포인터 산술

```text
===== 소스: ex.c (15-f) =====
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* ★ 출력 순서를 고정한다 — 파이프로 받아도 같게 */
    int *n = NULL;
    volatile int k = 1;
    int *p = n + k;                 /* ★ UB 3 — 널 포인터에 0 아닌 값을 더한다 */
    printf("NULL + 1 = %p\n", (void *)p);
    int *q = n + 0;                 /* C17 에서는 이것도 UB, C23 에서 정의됨 */
    printf("NULL + 0 = %p\n", (void *)q);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (경고 0 건, cc exit=0 · run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== gcc -std=c17 -g -fsanitize=address,undefined · ./x 2>&1 | cat  (run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== gcc -std=c17 -g -fsanitize=pointer-overflow · ./x 2>&1 | cat  (run exit=0) =====
NULL + 1 = 0x4
NULL + 0 = (nil)
```

```text
===== clang -std=c17 -g -fsanitize=undefined · ./x 2>&1 | cat  (run exit=0) =====
ex.c:7:16: runtime error: applying non-zero offset 4 to null pointer
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:7:16 
NULL + 1 = 0x4
ex.c:9:16: runtime error: applying zero offset to null pointer
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ex.c:9:16 
NULL + 0 = (nil)
```

★ **`-std=c2x` 로 바꿔 던진 판도 한 글자도 같았다** — C23 이 `NULL + 0` 을 정의했는데도 clang 18 은 여전히 두 줄을 낸다.

★ **위 두 gcc 블록에는 진단이 한 줄도 없다.** 「생략한 것」이 아니라 **나오지 않은 것**이다 —\
`2>&1 | cat` 로 받았으므로 stderr 까지 포함한 전부가 저 두 줄이다.\
★ **clang 은 `-std=c17` 과 `-std=c2x` 에서 한 글자도 다르지 않은 출력을 냈다.**

- ★★★ **gcc 의 `-fsanitize=undefined` 는 널 포인터 산술을 보지 않는다.**\
  `-fsanitize=pointer-overflow` 를 **직접 켜도** 진단이 0줄이었다 — **플래그는 받아 주는데 동작하지 않는다.**
- ★★ **clang 만 잡는다.** 그것도 **두 자리를 따로** — `applying non-zero offset 4 to null pointer` 와\
  `applying zero offset to null pointer`.
- ★ **`-std=c2x` 로 바꿔도 clang 18 은 `NULL + 0` 을 여전히 보고한다.** C23 이 그것을 정의했는데도 그렇다 —\
  두 판의 출력이 **한 글자도 다르지 않았다.** ★ **명세가 바뀐 것과 도구가 따라온 것은 다른 문제**다.
- **`NULL + 1` 이 `0x4` 를 찍었다** — `0 + 1 * sizeof(int)` 를 그냥 계산한 것이다.\
  ★ **이 값은 근거가 아니다.** UB 라 아무 의미가 없다.

### (6) `void *` 산술은 표준에 없다 — **GNU 확장**

**언제 쓰나** — 바이트 단위로 걷고 싶을 때. **`char *` 를 써야 한다.**

```text
===== 소스: ex.c (15-h) =====
#include <stdio.h>
#include <stdint.h>

int main(void) {
    char buf[8] = {0, 1, 2, 3, 4, 5, 6, 7};
    void *vp = buf;

    printf("sizeof(void) = %zu\n", sizeof(void));   /* 표준에 없다 */
    void *v1 = vp + 1;                              /* 표준에 없다 */
    printf("vp        = %p\n", vp);
    printf("vp + 1    = %p   (차이 %ld 바이트)\n", v1,
           (long)((uintptr_t)v1 - (uintptr_t)vp));
    printf("*(char*)(vp+1) = %d\n", *(char *)v1);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra (경고 0 건, exit=0) =====
(아무것도 나오지 않는다)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c: In function ‘main’:
ex.c:8:43: warning: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu\n", sizeof(void));   /* 표준에 없다 */
      |                                           ^~~~
ex.c:9:19: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
    9 |     void *v1 = vp + 1;                              /* 표준에 없다 */
      |                   ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic (exit=0) =====
ex.c:8:36: warning: invalid application of 'sizeof' to a void type [-Wpointer-arith]
    8 |     printf("sizeof(void) = %zu\n", sizeof(void));   /* 표준에 없다 */
      |                                    ^     ~~~~~~
ex.c:9:19: warning: arithmetic on a pointer to void is a GNU extension [-Wgnu-pointer-arith]
    9 |     void *v1 = vp + 1;                              /* 표준에 없다 */
      |                ~~ ^
2 warnings generated.
```

```text
===== 실행 (gcc) =====
sizeof(void) = 1
vp        = 0x7ffe0d1a6bd0
vp + 1    = 0x7ffe0d1a6bd1   (차이 1 바이트)
*(char*)(vp+1) = 1
```

그림 해설 (한 단계씩):

- ★★★ **`-Wall -Wextra` 로는 0건**이다. **`-pedantic` 을 붙여야** 양쪽 컴파일러가 말한다.
- **GNU 확장에서 `sizeof(void)` 는 1** 이고, 그래서 **`void *` 산술이 바이트 단위**로 돈다.\
  **ISO C 에는 둘 다 없다** — `void` 는 크기가 없는 타입이라 스케일링할 값이 없다.
- ★ **clang 의 진단이 더 정확하다** — 「**GNU extension**」이라고 이름을 말한다.\
  gcc 는 「`void *` 가 산술에 쓰였다」까지만 말한다.
- **바이트 단위로 걸으려면 `char *`** 를 쓴다. `unsigned char *` 가 더 안전하다(부호가 구현 정의가 아니다).

비용 — 캐스트 하나. **이식성을 잃지 않는다.**

### (7) 이 주제의 진단을 한 표로

```text
===== 각 프로그램을 일곱 조합으로 던져 warning: 줄을 센 것 =====
(세는 법 — grep -c 'warning:' 이다. grep -c warning 은 clang 의
 "2 warnings generated." 요약 줄까지 세어 한 건이 더 나온다)
```

| 프로그램 | gcc 무플래그 | gcc `-Wall` | gcc `+Wextra` | gcc `+pedantic` | clang `-Wall -Wextra` | clang `+pedantic` | 런타임 도구 |
|---|---|---|---|---|---|---|---|
| 15-a 스케일링 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 15-b `i[a]` | 0 | **2** | 2 | 2 | **1** | 1 | — |
| 15-c 끝 한 칸 뒤 + 역참조 | **0** | **0** | **0** | **0** | **0** | **0** | ★ UBSan + ASan |
| 15-d 배열 밖(`volatile`) | **0** | **0** | **0** | **0** | **0** | **0** | ★ gcc 는 **읽을 때만**, clang 은 **만들 때부터** |
| 15-e 다른 배열 뺄셈 | 0 | **1**(비교 쪽) | 1 | 1 | **1**(비교 쪽) | 1 | ★★ **없다 — 값만 갈린다** |
| 15-f 널 산술 | **0** | **0** | **0** | **0** | **0** | **0** | ★★ **clang UBSan 만** |
| 15-g 포인터 형성만 | **0** | **0** | **0** | **0** | **0** | **0** | ★★ **clang UBSan 만** |
| 15-h `void *` 산술 | 0 | 0 | **0** | **2** | **0** | **2** | — |

- ★★★ **UB 세 자리(15-d·15-e·15-f)가 전부 컴파일러 경고 0건**이다.\
  15-e 의 1건은 **비교** 쪽이지 **뺄셈** 쪽이 아니다.
- ★★ **런타임 도구도 셋을 다르게 본다** — 15-c 는 둘 다, 15-d 는 시점이 다르고, 15-f 는 **clang 만**이다.
- ★ **`-pedantic` 이 있어야만 보이는 것은 15-h**(`void *` 산술)다.

## 문법 — 형태와 규칙

### 형태 — 여섯 가지 연산

```c
int a[5];  int *p = a;  int *q = a + 3;
ptrdiff_t d;

p + 2;          /* ① 포인터 + 정수  -> 포인터.  주소 + 2 * sizeof(*p) */
2 + p;          /* ② 정수 + 포인터  -> 같다 (교환 가능) */
q - 1;          /* ③ 포인터 - 정수  -> 포인터 */
d = q - p;      /* ④ 포인터 - 포인터 -> ptrdiff_t (원소 개수) */
p++;  ++p;      /* ⑤ 증감 — 한 칸 */
p < q;  p == q; /* ⑥ 비교 — 같은 배열 안이면 정의된다 */

a[3];           /* == *(a + 3) — 인덱싱은 ①과 역참조의 축약 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
int a[5], b[5];

a + 6;              /* ★ UB — 끝 한 칸 뒤(a+5)를 넘는 포인터는 "만들기만 해도" */
*(a + 5);           /* ★ UB — 끝 한 칸 뒤를 역참조 */
b - a;              /* ★ UB — 서로 다른 배열의 포인터끼리 뺄셈 */
b < a;              /* ★ 미명시 — 서로 다른 객체의 포인터 비교 */
(int *)0 + 1;       /* ★ UB — 널 포인터 산술 (C23 도 +0 만 풀었다) */

void *v = a;
v + 1;              /* ★ 표준에 없다 — GNU 확장. -pedantic 이 말한다 */
sizeof(void);       /* ★ 같음 */

size_t n = q - p;   /* ★ 틀린 타입 — 음수가 거대한 양수가 된다. ptrdiff_t 를 쓴다 */
printf("%d", q-p);  /* ★ 틀린 서식 — %td 를 쓴다 */
```

### 규칙 불릿

- **`p + n` 의 주소는 `p` 의 주소 + `n * sizeof(*p)`** 다. **단위는 바이트가 아니라 원소**다.
- **`q - p` 는 원소 개수**이고 타입은 **`ptrdiff_t`**(부호 있음). 서식은 **`%td`**.
- ★ **`a[i]` 는 `*(a + i)` 로 정의된다.** 그래서 `i[a]` 도 컴파일되고 **경계 검사가 없다.**
- ★ **만들어도 되는 범위는** 「**배열의 첫 원소 \~ 끝 한 칸 뒤**」다. 그 밖은 **만들기만 해도 UB**.
- ★ **끝 한 칸 뒤는 비교·뺄셈까지 합법이고 역참조만 UB** 다.
- ★ **서로 다른 배열의 포인터끼리 빼면 UB**, **비교하면 미명시**다.
- ★ **널 포인터 산술은 UB** 다. C23 이 **`NULL + 0` 만** 정의했다.
- **`void *` 산술과 `sizeof(void)` 는 ISO C 에 없다** — GNU 확장이고 `-pedantic` 이 말한다.
- **`*p++` 는 포인터가, `(*p)++` 는 값이 움직인다**([09번 형제](../09-operator-precedence-and-associativity/)).

## 어디서 틀리나

### 1. ★★ 「`p + 1` 은 1바이트 가겠지」

- **가리키는 타입 한 개만큼** 간다. `int *` 는 4, `double *` 는 8.
- 바이트 단위로 걸으려면 **`char *` 나 `unsigned char *`** 로 캐스트한다.
- ★ **`void *` 로 하면 GNU 확장**이고 `-pedantic` 이 말한다.

### 2. ★★ 「포인터 차를 `size_t` 나 `int` 로 받는다」

- 차는 **`ptrdiff_t`**(부호 있음)다. `size_t` 로 받으면 **음수가 거대한 양수**가 된다.
- 서식은 **`%td`** 다. `%d` 로 찍으면 `-Wformat` 이 잡는다.
- ★ `sizeof(ptrdiff_t)` 는 **구현 정의**다(여기서 8).

### 3. ★★★ 「배열 밖을 가리키기만 하고 안 읽으면 괜찮겠지」

- **아니다.** 끝 한 칸 뒤를 **넘는 포인터는 만들기만 해도 UB** 다.
- ★ **gcc 의 sanitizer 는 그것을 못 본다** — 읽을 때만 말한다. **clang 은 만들 때부터** 말한다.
- ★ 그래서 gcc 조합으로 「진단 0줄」을 받아도 **UB 가 없다는 뜻이 아니다.**

### 4. ★★★ 「두 배열의 거리를 포인터 뺄셈으로 잰다」

- **UB** 다. 실측에서 **같은 소스가 `4`·`-4`·`8` 세 답**을 냈다.
- ★ **어떤 도구도 뺄셈을 진단하지 않는다.** 경고는 **비교 쪽에만** 난다.
- 거리를 재야 하면 **`uintptr_t` 로 캐스트해 정수 뺄셈**을 한다(그것은 구현 정의이지 UB 가 아니다).

### 5. ★ 「gcc 의 `note:` 대로 고치면 된다」

- gcc 가 `b < a` 에 「`&b[0] < &a[0]` 을 쓰라」고 권하는데,\
  ★ **그렇게 고쳐도 서로 다른 객체의 포인터 비교라 미명시**다.
- **경고를 끄는 조언이지 UB 를 없애는 조언이 아니다.**

### 6. ★★ 「`-fsanitize=undefined` 를 켰으니 포인터 UB 는 다 잡힌다」

- **gcc 의 UBSan 은 널 포인터 산술을 보지 않는다.** `-fsanitize=pointer-overflow` 를 직접 켜도 **0줄**이었다.
- **clang 만** `applying non-zero offset 4 to null pointer` 를 낸다.
- ★ **두 컴파일러의 sanitizer 를 둘 다 돌려야 한다.**

### 7. ★ 「`-O2` 에서 `-Warray-bounds` 가 잡아 주더라」

- **상수 첨자일 때만**이고 **gcc `-O2` 에서만**이다. `-O0` 은 0건, **clang 은 어느 수준에서도 0건**이었다.
- 첨자가 `volatile` 이거나 실행 시간에 정해지면 **컴파일 타임 검사는 아무것도 못 한다.**

### 8. 「`i[a]` 를 쓰면 멋있다」

- **쓰면 안 된다.** 쓸모 있는 것은 그 사실 자체가 아니라 **「인덱싱이 주소 계산일 뿐」이라는 함의**다.
- gcc 가 `a[i] == i[a]` 를 **`self-comparison`** 으로 경고한 것이 그 증거다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★ **이 주제는 UB 칸이 본체**다 — [13번 형제](../13-goto-cleanup-idiom/)가 **표준이 본체**였던 것과 정반대이고,\
★★★ **그 UB 들을 도구가 거의 못 본다**는 것이 이 주제의 값이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | `p + n` 의 **스케일링** · `q - p` 가 **원소 개수** · **`a[i]` == `*(a+i)`** · **끝 한 칸 뒤 포인터의 합법성**(비교·뺄셈 포함) · `*p++` 와 `(*p)++` 의 차이 | 주소 차이가 `sizeof *p` 와 일치 · 일곱 식이 전부 30 · 루프가 150 · gcc 의 `self-comparison` 경고 | ★ **`a[i]` 에 경계 검사가 없다는 것** — 문법으로는 안 보인다 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ `uintptr_t` — 거리를 잴 때 쓰는데 **선택 타입**이다 | `sizeof` 8 · 컴파일 통과 | ★ 없는 구현을 이 머신에서 볼 수 없다 |
| **구현 정의** | 문서화 의무가 있다 | `sizeof(ptrdiff_t)`·`sizeof(size_t)`(여기서 **8**) · **포인터의 표현** · GNU 확장에서 `sizeof(void) == 1` | `sizeof` 출력 · `-pedantic` 진단 | ★ **`void *` 산술이 그냥 돌아간다** — `-pedantic` 없이는 표준 밖인 줄 모른다 |
| **미명시** | 몇 가지 중 하나 | ★ **서로 다른 객체의 포인터 비교**(`b < a`) — 결과가 정해져 있지 않다 · **두 배열의 상대 배치** | `b < a` 가 0 · gcc `-Warray-compare` · ASan 을 켜면 배치가 바뀜 | ★ **`0` 이라는 답이 그럴듯하다** — 미명시인 줄 모른다 |
| **UB** | 아무 일이나 | ★★ **본체 넷** — ① 끝 한 칸 뒤 **역참조** ② 그 범위를 **넘는 포인터 형성** ③ **다른 배열끼리 뺄셈** ④ **널 포인터 산술** | ①·② ASan+UBSan · ③ **값이 4/-4/8 로 갈림** · ④ clang UBSan | ★★★ **넷 다 컴파일러 경고 0건** · ②는 gcc 가 못 봄 · ③은 **아무도 못 봄** · ④는 clang 만 |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | gcc 컴파일 | clang 컴파일 | gcc sanitizer | clang sanitizer | 무엇이 잡나 |
|---|---|---|---|---|---|---|
| 스케일링·뺄셈 | 표준 | 0건 | 0건 | 0줄 | 0줄 | ★ 잡을 것이 없다 |
| `i[a]` | 표준 | **2건**(`self-comparison`) | **1건** | — | — | ★ 컴파일러가 **같은 식임을 증명**한다 |
| 끝 한 칸 뒤 **형성** | 표준 | **0건** | 0건 | **0줄** | **0줄** | ★ 합법이라 잡을 것이 없다 |
| 끝 한 칸 뒤 **역참조** | **UB** | **0건** | 0건 | ★ **UBSan + ASan** | ★ 같음 | 런타임 도구 |
| 범위 밖 포인터 **형성** | **UB** | **0건** | **0건** | ★ **0줄** | ★ **1줄** | ★★ **clang sanitizer 만** |
| 범위 밖 **읽기**(변수 첨자) | **UB** | 0건 | 0건 | UBSan + ASan | UBSan + ASan | 런타임 도구 |
| 범위 밖 **읽기**(상수 첨자) | **UB** | ★ **`-O2` 2건** | ★ **0건** | — | — | ★ gcc `-O2` 의 `-Warray-bounds=` |
| 다른 배열 **뺄셈** | **UB** | **0건** | **0건** | ★ **0줄** | ★ **0줄** | ★★★ **아무도 안 잡는다** |
| 다른 배열 **비교** | 미명시 | **1건** | **1건** | 0줄 | 0줄 | ★ 이름이 다르다(`-Warray-compare` ↔ `-Wtautological-compare`) |
| 널 포인터 산술 | **UB** | **0건** | **0건** | ★ **0줄** | ★ **2줄** | ★★ **clang sanitizer 만** |
| `void *` 산술 | 표준 밖 | **0건 / `+pedantic` 2건** | 같음 | — | — | ★ `-pedantic` 뿐 |

- ★★ **이 표의 결론 네 줄**
  - **UB 넷 중 어느 것도 컴파일러 경고로는 안 잡힌다.** 이 주제에서 경고는 **표준 안쪽 것**만 말한다.
  - ★★★ **「다른 배열끼리 뺄셈」은 어떤 도구도 안 잡는다.** 잡히는 대신 **값이 갈린다**(4 · -4 · 8).
  - **gcc 와 clang 의 sanitizer 가 서로 다른 것을 본다** — 포인터 **형성**과 **널 산술**은 clang 만이다.
  - ★ **`-pedantic` 이 없으면 `void *` 산술이 표준 밖인 줄 모른다.**

### 이 주제의 네 번째 창 — **`ptrdiff_t` 와 스케일링**, 그리고 **답이 갈리는지 보는 것**

- **컴파일 진단**은 UB 넷 중 **하나도** 못 본다.
- **실행 출력**은 그럴듯한 값을 준다 — `b - a = 4` 는 **틀렸다고 생각할 이유가 없는 숫자**다.
- **sanitizer** 는 넷 중 **둘 반**만 본다(형성은 clang 만, 뺄셈은 아무도 안 본다).
- ★★ **그래서 창을 둘 더 썼다.**
  - **`ptrdiff_t` 와 주소 차이** — 「+1 이 몇 바이트인가」를 **숫자로** 만든다.\
    ★ **주소값이 아니라 차이를 쓰므로** ASLR 을 견딘다.
  - ★★★ **같은 소스를 40벌로 던져 「답이 갈리는지」 보는 것** —\
    `b - a` 가 **4 · -4 · 8** 로 갈렸다. **진단이 없는 UB 를 드러내는 유일한 방법**이었고,\
    ★ **갈린 축이 최적화 수준이 아니라** 「**컴파일러 + ASan 여부**」였다는 것도 그때 알았다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 배열을 훑는다 | `for (p = a; p != a + n; p++)` | `p <= a + n` (끝 한 칸 뒤를 역참조) |
| 두 원소의 거리 | 같은 배열이면 `q - p` | 다른 배열끼리 `b - a` |
| 다른 객체의 거리 | `(uintptr_t)b - (uintptr_t)a` | 포인터 뺄셈 |
| 차를 담는다 | `ptrdiff_t d = q - p;` | `size_t`·`int` |
| 차를 찍는다 | `printf("%td", d)` | `%d`·`%zu` |
| 바이트 단위로 걷기 | `(unsigned char *)p + 1` | `(void *)p + 1` |
| 인덱싱 | `a[i]` | `i[a]`(된다고 쓰지 마라) |
| 널일 수 있는 포인터에 더하기 | 먼저 널을 검사 | `p + n` 을 먼저 |
| 경계 밖을 확인 | ASan + **clang** UBSan 둘 다 | gcc UBSan 하나로 만족 |
| 표준 준수 확인 | `-pedantic` | `-std=c17` 만 믿기 |

판단 규칙 두 줄.

- **포인터가 살 수 있는 범위는** 「**첫 원소 \~ 끝 한 칸 뒤**」다. 그 밖은 **가리키기만 해도** 없는 것으로 친다.
- **도구가 조용한 것은 UB 가 없다는 뜻이 아니다.** 이 주제의 UB 넷 중 **셋이 컴파일러에게 안 보인다.**

## 핵심 문장

- ★★ **`p + n` 의 주소는 `p` + `n * sizeof(*p)`** 다. 실측에서 `char`·`int`·`double` 이 **1 · 4 · 8** 바이트였다.
- ★★ **`q - p` 는 원소 개수**이고 타입은 **`ptrdiff_t`**(부호 있음). 실측 `&ai[4] - &ai[1]` 이 **3**, 뒤집으면 **-3** 이다.\
  **바이트로는 12** 였다. 서식은 **`%td`**.
- ★★★ **`a[i]` 는 `*(a + i)` 로 정의된다.** 그래서 **`i[a]`·`2[a]` 가 컴파일되고 좌변으로도 쓰인다**(실측 전부 30).\
  ★ **gcc 가 `a[i] == i[a]` 를 `self-comparison` 으로 경고**한 것이 「같은 식」이라는 증거다.
- ★★★ **그 정의의 진짜 함의는** 「**인덱싱에 경계 검사가 없다**」는 것이다 — `a[i]` 는 **주소 계산일 뿐**이다.
- ★★ **끝 한 칸 뒤 포인터(`a + 5`)는 만들고 비교하고 빼는 것까지 합법**이고 **역참조만 UB** 다.\
  실측에서 `end - a = 5`·`end > a = 1` 에 **진단 0줄**, `*end` 에서만 **UBSan + ASan** 이 동시에 말했다.
- ★★★ **포인터 산술 UB 네 자리가 전부 컴파일러 경고 0건**이다.
- ★★★ **「다른 배열끼리 뺄셈」은 어떤 도구도 잡지 않는다.** 대신 **같은 소스가 세 답**을 냈다 —\
  **4**(gcc) · **-4**(clang) · **8**(ASan 을 켠 양쪽). ★ **갈린 축은 최적화 수준이 아니라** 「**컴파일러 + ASan 여부**」였다.
- ★★ **범위 밖 포인터를 「만들기만」 하는 것을 gcc sanitizer 는 못 본다.** clang 만 `index 10 out of bounds` 를 낸다.
- ★★ **널 포인터 산술을 gcc 의 `-fsanitize=undefined` 는 보지 않는다.**\
  `-fsanitize=pointer-overflow` 를 **직접 켜도 0줄**이었다. **clang 만** 잡는다.
- ★ **C23 이 `NULL + 0` 을 정의했지만 clang 18 은 `-std=c2x` 에서도 여전히 보고한다** —\
  **명세가 바뀐 것과 도구가 따라온 것은 다른 문제**다.
- ★ **`void *` 산술과 `sizeof(void)` 는 ISO C 에 없다**(GNU 확장, `sizeof(void) == 1`).\
  **`-Wall -Wextra` 로는 0건**이고 **`-pedantic` 에서만** 나온다.
- ★ **`-Warray-bounds` 는 상수 첨자 + gcc `-O2` 에서만** 잡았다. `-O0` 은 0건, **clang 은 어느 수준에서도 0건**.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 15번)
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — ★★ **포인터 타입과 역참조의 정본.** 이 주제는 **그 타입 위에 선다** — 「한 칸이 몇 바이트인가」를 정하는 것이 거기의 타입이다
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — ★★ **배열이 포인터가 되는 자리의 정본.** 이 주제의 산술이 **함수 안에서 길이를 잃은 뒤** 무엇이 되는지가 거기 있다
- [`09-operator-precedence-and-associativity/`](../09-operator-precedence-and-associativity/) — ★ **`*p++` 대 `(*p)++` 의 정본.** 여기는 **결론만** 되짚었다
- [`10-evaluation-order-and-sequence-points/`](../10-evaluation-order-and-sequence-points/) — 한 `printf` 안에서 `*p++` 와 `p - arr` 를 같이 재면 안 되는 이유
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — `sizeof *p` 가 스케일링의 계수인 것
- [`11-bitwise-operations-and-shifts/`](../11-bitwise-operations-and-shifts/) — ★ **UB 가 본체인 형제 주제.** 다섯 층의 두께가 이 주제와 같다
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — **표준이 본체인 형제.** 층 분포가 정반대다
- 목록의 **19번 주제** (`void *`·널 포인터) — `void *` 산술이 없는 이유 · `NULL` 의 성질
- 목록의 **56번 주제** (공간 위반 — 배열 밖 접근) — ★ **경계를 넘는 접근이 「죽지 않을 수 있다」는 것의 정본.** 여기는 **어떤 산술이 그것을 만드나**까지
- 목록의 **58번 주제** (UB 를 잡는 도구) — gcc 와 clang 의 sanitizer 가 **서로 다른 것을 보는** 이유

## 용어 풀이

- **포인터 산술(pointer arithmetic)** — 포인터에 정수를 더하거나 빼는 것. **단위는 바이트가 아니라 원소**다.
- **스케일링(scaling)** — 더할 정수에 `sizeof(*p)` 를 곱하는 것. 예: `int *p` 에서 `p+1` 은 주소가 4 늘어난다.
- **`ptrdiff_t`** — 포인터 뺄셈의 결과 타입(`<stddef.h>`). **부호 있는 정수**이고 서식은 `%td`.
- **끝 한 칸 뒤(one past the end)** — 마지막 원소 바로 다음 자리. **만들고 비교하는 것은 합법**, **역참조는 UB**.
- **인덱싱(subscripting)** — `a[i]`. 표준이 **`*(a + i)` 로 정의**하므로 `i[a]` 와 같다.
- **미명시 동작(unspecified behavior)** — 몇 가지 중 하나이되 어느 것인지 정해지지 않은 것. 예: 서로 다른 객체의 포인터 비교.
- **미정의 동작(UB)** — 표준이 아무 요구도 하지 않는 것. 예: 다른 배열끼리의 포인터 뺄셈.
- **레드존(redzone)** — ASan 이 객체 사이에 끼우는 검사용 여백. ★ **그래서 ASan 을 켜면 객체 배치가 바뀐다.**
- **`-Warray-bounds`** — 컴파일 타임에 첨자 범위를 검사. ★ **gcc `-O2` 이상 + 상수 첨자**일 때만 쓸모가 있었다.
- **`-Warray-compare`** — 배열 이름끼리 비교한 것을 경고(gcc). clang 은 같은 자리를 `-Wtautological-compare` 로 말한다.
- **`-Wpointer-arith` / `-Wgnu-pointer-arith`** — `void *` 산술·`sizeof(void)` 를 경고. **`-pedantic` 이 켠다.**
- **`-fsanitize=pointer-overflow`** — 널 포인터 산술 등을 검사하는 UBSan 검사기.\
  ★ **gcc 13.3.0 은 플래그를 받지만 이 실험에서 진단을 내지 않았다.**

---

## 더 들어가면

- ★ **`restrict` 와 앨리어싱**은 포인터 산술의 최적화를 바꾼다. `memcpy` 와 `memmove` 의 시그니처 차이가 거기서 온다.\
  ★ **이 문서에서 던져 보지 않았다.** 목록의 **33번 주제**의 몫이다.

- **다차원 배열의 산술**(`int a[3][4]` 에서 `a + 1` 이 16바이트)은 [16번 형제](../16-array-pointer-decay-and-function-parameters/)에서 실측했다.\
  ★ **이 문서는 1차원만** 다뤘다.

- ★ **부호 있는 정수 오버플로와 포인터 산술이 겹치는 자리**(`p + huge`)는 던져 보지 않았다.\
  목록의 **54번 주제**의 몫이다.

- **`p - p` 가 0 인 것**과 **널 포인터끼리의 뺄셈**은 던져 보지 않았다.\
  ★ C23 이 널 관련 규칙을 손댔는데 **`NULL + 0` 하나만 확인**했다.

- ★ **「다른 배열끼리 뺄셈」이 `4`·`-4`·`8` 로 갈린 이유 중 clang 쪽(`-4`)의 배치 근거는 확인하지 않았다.**\
  ASan 쪽(`8`)은 **레드존 때문**이라고 설명할 수 있지만, **clang 이 왜 `b` 를 `a` 앞에 두는지는 안 찍어 봤다.**\
  **재현되는 것**(「세 답이 갈린다」)과 **한 판의 결과**(「clang 이 -4 다」)를 갈라 읽어야 한다.

- ★ **`-fsanitize=pointer-overflow` 가 gcc 에서 정말 아무것도 안 잡는지**는 이 한 프로그램으로만 확인했다.\
  **다른 형태의 포인터 오버플로는 던져 보지 않았다.**
