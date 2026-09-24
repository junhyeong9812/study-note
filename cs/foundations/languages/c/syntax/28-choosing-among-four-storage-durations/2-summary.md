# c/syntax/28 — 저장 기간 4종을 고르는 법: 「**이 값은 언제 태어나 언제 죽나**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf)) · [cppreference — Storage duration (C)](https://en.cppreference.com/w/c/language/storage_duration) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html) · [`proc(5)` — `/proc/[pid]/maps`](https://man7.org/linux/man-pages/man5/proc.5.html)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **주소·값·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **UB 가 걸린 실험은 「컴파일러 2 × 최적화 3」 여섯 벌**을 돌렸다 — 한 벌만 돌리면 **정반대 결론**이 난다(아래 (5)).\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 자동·정적·할당은 **C89 부터**다. **스레드 저장 기간은 C11 부터**(`_Thread_local`).\
> ★ **`thread_local` 이라는 철자**는 **C11 에서는 `<threads.h>` 의 매크로**이고 **C23 부터 키워드**다 — 아래 (7).\
> ★★ **`-std=` 는 강제가 아니라 기본값 선택**이다 — 표준 준수를 주장하는 자리에는 전부 `-pedantic` 을 붙였다.\
> ★★★ 그런데 이 주제의 **UB 는 `-pedantic` 으로도 `-pedantic-errors` 로도 안 막힌다** — 경고를 안 내는 컴파일러가 있기 때문이다(아래 (5)).
> ★★ **경계** — **스택 프레임·가상 메모리·힙의 구조**는 [`foundations/memory-management/`](../../../../memory-management/)와 [`foundations/variables-and-memory/`](../../../../variables-and-memory/)가 정본이다.\
> 여기는 「**C 에서 이 값을 어느 저장 기간에 둘까**」라는 **선택**만 본다 — ★ 구조가 아니라 **고르는 법**이다.\
> ★ **`static` 이 링크를 바꾸는 것**은 목록의 **29번 주제**, **초기화 규칙과 불확정 값**은 목록의 **30번 주제**가 정본이다.\
> ★ **`malloc`/`free` 의 계약**은 목록의 **37번 주제**, **해제 후 사용·댕글링**은 목록의 **57번 주제**, **sanitizer** 는 목록의 **58번 주제**다.\
> ★ **문자열 리터럴**은 [20번 형제](../20-null-terminated-strings-and-string-literals/), **VLA** 는 [18번 형제](../18-variable-length-arrays-vla/), **복합 리터럴**은 [27번 형제](../27-compound-literals/)가 정본이다.
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · 목록의 **37번 주제**.
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**저장 기간은 「물건을 어디에 두느냐」다.**

일을 하다 보면 물건을 둘 자리를 고른다.

- **책상 위** — 지금 하는 일에만 쓴다. **일이 끝나면 치운다.** → **자동**
- **책장** — 사무실이 문을 열 때부터 닫을 때까지 그대로 있다. → **정적**
- **내 사물함** — **사람마다 하나씩** 있고 남의 것은 안 보인다. → **스레드**
- **창고에서 빌린 선반** — **내가 빌리고 내가 돌려줘야** 한다. 안 돌려주면 계속 물고 있다. → **할당**

| 비유 | 실체 | 언제 태어나 언제 죽나 |
|---|---|---|
| 책상 위 | `int a;`(함수 안) | 블록에 들어갈 때 \| **블록이 끝날 때** |
| 책장 | `static int s;` · 전역 변수 · 문자열 리터럴 | 프로그램 시작 전 \| **프로그램이 끝날 때** |
| 사물함 | `_Thread_local int t;` | 스레드가 생길 때 \| **그 스레드가 끝날 때** |
| 빌린 선반 | `malloc(n)` | `malloc` 이 돌려준 순간 \| **`free` 를 부를 때** |
| ★ 책상 위 물건을 **치운 뒤 찾기** | 죽은 자동 객체를 읽기 | ★★★ **UB — 여섯 벌이 세 갈래로 갈렸다** |
| ★ 책장에 둔 것은 **처음부터 0** | 정적 객체의 초기화 | **표준 — 0 이 보장된다** |
| ★ 책상 위 물건은 **주워 온 상태** | 자동 객체의 초기값 | ★★ **불확정** |
| ★ 책상이 **넘치면** | 자동 저장 기간을 너무 크게 잡기 | ★ **이 환경에서 `run exit=139`** |

```text
   한 프로그램 안의 네 구역 — /proc/self/maps 로 확인한 것

   주소 높음
     +------------------------+
     | [stack]      rw-p      |  ★ 자동   — 함수가 들어오고 나갈 때마다 오르내린다
     +------------------------+
     |        ...             |
     +------------------------+
     | (익명 매핑)   rw-p      |  ★ 스레드 — 스레드마다 한 벌씩 따로 잡힌다
     +------------------------+
     | [heap]       rw-p      |  ★ 할당   — malloc 이 여기서 떼어 준다
     +------------------------+
     | 실행 파일     rw-p      |  ★ 정적   — s_bss · s_data
     | 실행 파일     r--p      |  ★ 정적   — "hello" ← ★ w 가 없다
     +------------------------+
   주소 낮음

   ★ 주소는 실행마다 흔들린다(ASLR). ★ 「어느 구역인가」와 ★ 「주소들 사이의 차」는 안 흔들린다.
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 네 저장 기간의 수명 규칙이 전부 표준이다.
- ★★ 두 번째 무게중심은 「**UB**」다 — **죽은 객체를 읽는 것.** 여섯 벌이 **세 갈래**로 갈렸다.
- ★★ 그리고 「**미명시**」 칸이 얇게 있다 — **불확정 값으로 무엇이 읽히나**.
- ★ **구현 정의 칸은 얇다** — 스택 한도·각 구역의 배치·진단 문구.

> **저장 기간(storage duration)** — 그 객체가 **언제 태어나 언제 죽는가.**\
> 예: 함수 안의 `int a;` 는 블록이 끝날 때 죽는다. `static int s;` 는 프로그램이 끝날 때까지 산다.

> **불확정 값(indeterminate value)** — **무엇이 들어 있는지 정해지지 않은** 상태.\
> 예: 초기화를 안 한 자동 변수. 읽는 것이 위험하고, 이 환경에서는 **실행마다 다른 수**가 나왔다.

> **ASLR(주소 공간 배치 난수화)** — 실행할 때마다 구역의 시작 주소를 바꾸는 보안 기능.\
> 예: `%p` 로 찍은 주소는 실행마다 바뀌지만 **두 주소의 차**는 안 바뀐다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **이 값을 어디에 두어야 하나** — 네 가지를 고르는 기준이 무엇인가.
2. ★★★ **각각 언제 태어나 언제 죽나** — 그리고 **죽은 뒤에 읽으면 무슨 일이 나나.**
3. ★★ **그것을 어떻게 확인하나** — 주소가 흔들리는데 **무엇을 근거로 쓸 수 있나.**

## 동작 방식

### (1) ★★★ 네 저장 기간을 한 프로그램에서 나란히 본다

**언제 쓰나** — 「이 포인터가 가리키는 것이 어디 있나」를 판단할 때.

```c
/* s28a.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int  s_bss;                    /* 정적 — 0 으로 초기화된다 */
static int  s_data = 42;              /* 정적 — 값이 있다 */
static _Thread_local int t_tls = 7;   /* 스레드 */
static const char *lit = "hello";     /* 문자열 리터럴 — 정적 */

/* 주소가 /proc/self/maps 의 어느 줄에 드는지 찾아 ★ 권한과 이름만 ★ 돌려준다.
   주소 자체는 ASLR 로 흔들리지만 「어느 구역인가」는 안 흔들린다. */
static const char *region(const void *p) {
    static char out[512], line[512];
    unsigned long a = (unsigned long)p, lo, hi;
    char perm[8], path[400];
    FILE *f = fopen("/proc/self/maps", "r");
    out[0] = 0;
    while (fgets(line, sizeof line, f)) {
        path[0] = 0;
        if (sscanf(line, "%lx-%lx %7s %*s %*s %*s %399s", &lo, &hi, perm, path) >= 3
            && a >= lo && a < hi) {
            const char *tag = path[0] == '[' ? path
                            : path[0] == 0   ? "(익명 매핑)" : "(실행 파일 이미지)";
            snprintf(out, sizeof out, "%-4s %s", perm, tag);
            break;
        }
    }
    fclose(f);
    return out[0] ? out : "(못 찾음)";
}

int main(void) {
    int  a_auto = 1;
    int *h = malloc(sizeof *h);

    printf("저장 기간·무엇   권한 · 구역\n");
    printf("자동   a_auto    %s\n", region(&a_auto));
    printf("정적   s_bss     %s\n", region(&s_bss));
    printf("정적   s_data    %s\n", region(&s_data));
    printf("정적   \"hello\"   %s\n", region(lit));
    printf("스레드 t_tls     %s\n", region(&t_tls));
    printf("할당   malloc    %s\n", region(h));

    printf("\n★ 주소는 흔들려도 차이는 안 흔들린다\n");
    printf("(char *)&s_data - (char *)&s_bss = %td 바이트\n", (char *)&s_data - (char *)&s_bss);
    printf("문자열 리터럴 구역에 w 가 없다 — 그래서 쓰면 죽는다\n");
    free(h);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28a.c -o x ; ./x (cc exit=0 · run exit=0) =====
저장 기간·무엇   권한 · 구역
자동   a_auto    rw-p [stack]
정적   s_bss     rw-p (실행 파일 이미지)
정적   s_data    rw-p (실행 파일 이미지)
정적   "hello"   r--p (실행 파일 이미지)
스레드 t_tls     rw-p (익명 매핑)
할당   malloc    rw-p [heap]

★ 주소는 흔들려도 차이는 안 흔들린다
(char *)&s_data - (char *)&s_bss = -48 바이트
문자열 리터럴 구역에 w 가 없다 — 그래서 쓰면 죽는다
```

```text
   같은 프로그램에서 여섯 가지 객체의 주소를 /proc/self/maps 에 대조했다

   객체                권한    구역               저장 기간
   -----------------  ------  ----------------  --------------
   a_auto (지역 변수)  rw-p    [stack]           ★ 자동
   s_bss  (static)    rw-p    실행 파일 이미지    ★ 정적
   s_data (static=42) rw-p    실행 파일 이미지    ★ 정적
   "hello"            ★ r--p  실행 파일 이미지    ★ 정적  <- ★ w 가 없다
   t_tls (_Thread_local) rw-p (익명 매핑)         ★ 스레드
   malloc 한 것        rw-p    [heap]            ★ 할당

   ★ 주소 자체는 ASLR 로 흔들린다. ★ 이 표의 「권한 · 구역」 칸은 안 흔들린다.
```

그림 해설 (한 단계씩):

- ★★★ **네 저장 기간이 서로 다른 구역에 있다** — `[stack]` · 실행 파일 이미지 · 익명 매핑 · `[heap]`.\
  ★★ **이것이 이 주제의 네 번째 창**이다 — 주소를 눈으로 보지 말고 **어느 구역에 드는지**를 묻는다.
- ★★★ **문자열 리터럴만 권한이 `r--p`** 다. **`w` 가 없다** — 그래서 `"abc"[0] = 'X'` 가 죽는다([20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본).\
  ★ 다른 정적 객체(`s_bss`·`s_data`)는 같은 실행 파일 이미지인데 **`rw-p`** 다. 「**정적이면 못 고친다」가 아니라 「그 구역의 권한에 달렸다**」는 뜻이다.
- ★★ **`_Thread_local` 은 익명 매핑**에 있다 — 실행 파일 이미지가 아니다. **스레드마다 한 벌씩 따로 잡히기** 때문이다((6)에서 확인한다).
- ★★ **주소 차이는 안 흔들린다** — `(char *)&s_data - (char *)&s_bss` 가 **`-48`** 로 실행마다 같다.\
  ★ 근거로 쓸 수 있는 것은 「**어느 구역인가」와 「차이**」이고, **주소 자체는 아니다.**
- ★ **`[stack]` 과 `[heap]` 은 커널이 이름을 붙여 준다** — 리눅스의 `/proc/self/maps` 가 그 줄에 그렇게 적는다.

비용 — **이 창은 리눅스에서만 열린다.** 다른 OS 에서는 다른 도구가 필요하다.

### (2) ★★★ 수명 — 「같은 자리에 다시 태어나는 것」과 「살아 있는 것」은 다르다

**언제 쓰나** — 함수 안 `static` 을 쓸까 말까 결정할 때.

```c
/* s28b.c */
#include <stdio.h>

static const void *first_a;

static void counter(int call) {
    int        a = 0;      /* 자동 — 호출마다 새로 태어난다 */
    static int s = 0;      /* 정적 — 프로그램이 끝날 때까지 한 객체다 */
    a++; s++;
    if (call == 1) first_a = &a;
    printf("  %d번째 호출 : a=%d  s=%d   &a 가 첫 호출과 같은 자리인가 : %s\n",
           call, a, s, (&a == first_a) ? "예" : "아니오");
}

int main(void) {
    printf("같은 함수를 세 번 부른다\n");
    counter(1); counter(2); counter(3);
    printf("\n★ 자동 a 는 매번 1 · 정적 s 는 1 2 3 으로 쌓인다\n");
    printf("★ 「같은 자리에 다시 태어나는 것」과 「살아 있는 것」은 다르다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28b.c -o x ; ./x (cc exit=0 · run exit=0) =====
같은 함수를 세 번 부른다
  1번째 호출 : a=1  s=1   &a 가 첫 호출과 같은 자리인가 : 예
  2번째 호출 : a=1  s=2   &a 가 첫 호출과 같은 자리인가 : 예
  3번째 호출 : a=1  s=3   &a 가 첫 호출과 같은 자리인가 : 예

★ 자동 a 는 매번 1 · 정적 s 는 1 2 3 으로 쌓인다
★ 「같은 자리에 다시 태어나는 것」과 「살아 있는 것」은 다르다
```

```text
   static int s = 0;   <- ★ 한 번만 초기화된다 (프로그램 시작 전)
   int        a = 0;   <- ★ 호출마다 새로 초기화된다

   호출 1   a: [0]->1    s: [0]->1     &a = 0x...A0
   호출 2   a: [0]->1    s: [1]->2     &a = 0x...A0   ★ 같은 자리
   호출 3   a: [0]->1    s: [2]->3     &a = 0x...A0   ★ 같은 자리

   ★ 주소가 같다고 ★ 살아 있는 것이 아니다.
   ★ 함수가 끝나면 그 자리는 ★ 다음 호출이 다시 쓴다.
```

그림 해설 (한 단계씩):

- ★★★ **`a` 는 매번 `1`, `s` 는 `1 2 3` 으로 쌓인다.** 같은 함수 안의 두 줄인데 수명이 다르다.
- ★★★ **세 호출의 `&a` 가 모두 같은 자리**다. 그런데 **그 객체가 계속 살아 있는 것이 아니다** — 매번 **죽고 다시 태어난다.**\
  ★★ **「주소가 같다」를 「살아 있다」로 읽는 것**이 (5)의 UB 를 「괜찮아 보이게」 만드는 원인이다.
- ★★ **함수 안 `static` 은 저장 기간만 바꾸고 이름의 가시성은 안 바꾼다** — 그 이름은 여전히 **그 함수 안에서만** 보인다.\
  ★ **파일 스코프의 `static`** 은 반대로 **링크를 바꾼다**(목록의 **29번 주제**가 정본). **같은 낱말이 자리에 따라 다른 일을 한다.**
- ★ **`static` 의 초기화는 프로그램 시작 전에 한 번**이다. 「첫 호출 때 초기화된다」가 아니다.

비용 — **함수 안 `static` 은 그 함수를 재진입 불가·스레드 안전하지 않게** 만든다. 그 대가가 (6)의 `_Thread_local` 이다.

### (3) ★★★ 초기화 — 정적은 **0 이 보장**되고 자동은 **불확정**이다

**언제 쓰나** — 「초기값을 안 줘도 되나」를 물을 때.

```c
/* s28c.c */
#include <stdio.h>

static int s_zero;              /* 정적 — ★ 0 이 보장된다 */
static int s_arr[4];

int main(void) {
    int a_indet;                /* 자동 — ★ 불확정이다 */
    int a_arr[4];
    printf("정적 : s_zero=%d  s_arr = %d %d %d %d\n",
           s_zero, s_arr[0], s_arr[1], s_arr[2], s_arr[3]);
    printf("자동 : a_indet=%d  a_arr = %d %d %d %d\n",
           a_indet, a_arr[0], a_arr[1], a_arr[2], a_arr[3]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28c.c -o x ; ./x (cc exit=0 · run exit=0) =====
정적 : s_zero=0  s_arr = 0 0 0 0
자동 : a_indet=0  a_arr = 0 0 -1528595728 30953
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28c.c -o x (cc exit=0) =====
s28c.c: In function ‘main’:
s28c.c:11:5: warning: ‘a_arr’ is used uninitialized [-Wuninitialized]
   11 |     printf("자동 : a_indet=%d  a_arr = %d %d %d %d\n",
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   12 |            a_indet, a_arr[0], a_arr[1], a_arr[2], a_arr[3]);
      |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s28c.c:8:9: note: ‘a_arr’ declared here
    8 |     int a_arr[4];
      |         ^~~~~
s28c.c:11:5: warning: ‘a_indet’ is used uninitialized [-Wuninitialized]
   11 |     printf("자동 : a_indet=%d  a_arr = %d %d %d %d\n",
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   12 |            a_indet, a_arr[0], a_arr[1], a_arr[2], a_arr[3]);
      |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s28c.c:7:9: note: ‘a_indet’ was declared here
    7 |     int a_indet;                /* 자동 — ★ 불확정이다 */
      |         ^~~~~~~
```

```text
===== 정적은 0 · 자동은 불확정 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : a_indet=0  a_arr = 0 0 -1767908624 30893
gcc   -O1 : a_indet=0  a_arr = 0 0 0 0
gcc   -O2 : a_indet=0  a_arr = 0 0 0 0
clang -O0 : a_indet=1625603304  a_arr = 0 0 1616349936 31681
clang -O1 : a_indet=1766708224  a_arr = 0 0 -113226976 0
clang -O2 : a_indet=-1280685264  a_arr = 0 0 314592032 0
```

```text
   정적 저장 기간                        자동 저장 기간
   --------------------------------    --------------------------------
   static int s_zero;      -> ★ 0      int a_indet;      -> ★ 불확정
   static int s_arr[4];    -> ★ 0 0 0 0 int a_arr[4];    -> ★ 불확정

   여섯 벌로 던져 본 자동 쪽
     gcc   -O0 : a_indet=0            a_arr = 0 0 (쓰레기) (쓰레기)
     gcc   -O1 : a_indet=0            a_arr = 0 0 0 0
     gcc   -O2 : a_indet=0            a_arr = 0 0 0 0
     clang -O0 : a_indet=(쓰레기)      a_arr = 0 0 (쓰레기) (쓰레기)
     clang -O1 : a_indet=(쓰레기)      a_arr = 0 0 (쓰레기) 0
     clang -O2 : a_indet=(쓰레기)      a_arr = 0 0 (쓰레기) 0

   ★ 「0 이 나왔다」를 ★ 「0 으로 초기화된다」로 읽으면 안 된다.
```

그림 해설 (한 단계씩):

- ★★★ **정적 쪽은 여섯 벌 전부 `0`** 이다 — 이것은 **표준의 보장**이다. 초기자를 안 써도 0 이다.
- ★★★ **자동 쪽은 벌마다 다르다.** gcc 는 `a_indet` 이 여섯 벌 중 셋에서 `0` 으로 나오고, clang 은 세 벌 다 쓰레기다.\
  ★★ **gcc `-O0` 의 `a_indet=0` 이 가장 위험하다** — 「자동 변수도 0 이구나」로 읽히기 딱 좋은데 **보장이 아니다.**
- ★★★ **쓰레기 값은 실행마다 바뀐다.** 대조할 것은 숫자가 아니라 「**정적은 여섯 벌 전부 0 이고 자동은 안 그렇다**」는 성질이다.
- ★★ **gcc 는 `-O0` 에서도 `[-Wuninitialized]` 로 2건을 잡는다** — `a_arr` 과 `a_indet` 각각.\
  ★ **이 주제에서는 gcc 가 `-O0` 에서도 말해 준다** — [27번 형제](../27-compound-literals/)의 UB 가 `-O0` 에서 1건뿐이었던 것과 다르다.
- ★ **`cc exit=0`** 이다. 경고가 나도 빌드는 통과한다.

비용 — **자동 변수는 반드시 초기화한다.** 「어차피 0 이던데」는 **여섯 벌 중 몇 벌의 관찰**일 뿐이다.

### (4) ★★ 스택은 한도가 있다 — 힙은 그보다 훨씬 크다

**언제 쓰나** — 큰 버퍼를 지역 배열로 잡을까 `malloc` 할까 고를 때.

```c
/* s28f.c */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    size_t mb = (argc > 1) ? (size_t)atoi(argv[1]) : 1;
    printf("자동 저장 기간에 %zu MiB 를 잡아 본다\n", mb);
    {
        char big[mb * 1024 * 1024];     /* 가변 길이 배열 — 자동 저장 기간 */
        big[0] = 1; big[mb*1024*1024 - 1] = 2;
        printf("  자동 : 성공 (첫 바이트 %d · 끝 바이트 %d)\n", big[0], big[mb*1024*1024-1]);
    }
    char *h = malloc(mb * 1024 * 1024);
    if (h) { h[0] = 1; h[mb*1024*1024-1] = 2; printf("  할당 : 성공\n"); free(h); }
    else printf("  할당 : malloc 이 NULL 을 돌려줬다\n");
    return 0;
}
```

```text
===== ulimit -s 를 보고 1 · 4 · 64 MiB 를 자동 저장 기간에 잡아 본다 (exit=0) =====
ulimit -s = 8192 KiB
자동 저장 기간에 1 MiB 를 잡아 본다
  자동 : 성공 (첫 바이트 1 · 끝 바이트 2)
  할당 : 성공
  run exit=0
자동 저장 기간에 4 MiB 를 잡아 본다
  자동 : 성공 (첫 바이트 1 · 끝 바이트 2)
  할당 : 성공
  run exit=0
자동 저장 기간에 64 MiB 를 잡아 본다
  run exit=139
```

```text
   ulimit -s = 8192 KiB = 8 MiB

    1 MiB  자동 : 성공     할당 : 성공     run exit=0
    4 MiB  자동 : 성공     할당 : 성공     run exit=0
   64 MiB  ★ 자동에서 죽는다 — 출력이 한 줄도 더 안 나온다   run exit=139

   ★ malloc 은 64 MiB 도 문제가 없다 — 죽은 것은 ★ 자동 쪽이다.
   ★ 그리고 ★ 진단이 한 줄도 없다. 컴파일도 통과하고 경고도 0건이다.
```

그림 해설 (한 단계씩):

- ★★★ **1 MiB·4 MiB 는 성공하고 64 MiB 에서 죽는다**(`run exit=139` = SIGSEGV). `ulimit -s` 가 **8192 KiB** 이기 때문이다.
- ★★★ **컴파일러는 한 마디도 안 한다.** 크기가 실행 시간에 정해지는 **VLA** 라 컴파일 시간에 알 수 없다([18번 형제](../18-variable-length-arrays-vla/)가 정본).
- ★★ **`malloc` 쪽은 64 MiB 도 성공한다.** 힙은 스택보다 훨씬 크고, **모자라면 `NULL` 을 돌려주므로 검사할 수 있다.**\
  ★ 스택은 **넘치면 그냥 죽는다** — 검사할 방법이 없다.
- ★★ **스택 한도는 구현 정의이자 실행 환경의 설정**이다. `ulimit -s` 로 바뀌므로 **같은 바이너리가 환경에 따라 죽고 산다.**
- ★ **`setvbuf(stdout, NULL, _IONBF, 0)` 덕에 죽기 전 줄이 남았다** — 없었으면 64 MiB 벌의 출력이 **통째로 사라진다.**

비용 — **큰 것은 힙에 둔다.** 경계가 어디인지는 **환경 설정에 달렸고 컴파일러가 안 알려 준다.**

### (5) ★★★ 죽은 자동 객체를 읽으면 — **여섯 벌이 세 갈래로 갈렸다**

**언제 쓰나** — 「지역 변수 주소를 돌려줘도 되나」를 물을 때. **이 편의 본체다.**

```c
/* s28d.c */
#include <stdio.h>

static int *leak_auto(void) {
    int local = 1234;
    return &local;              /* ★ 블록이 끝나면 죽는 자리를 돌려준다 */
}
static int *ok_static(void) {
    static int s = 1234;
    return &s;                  /* 정적이라 살아 있다 */
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int *p = ok_static();
    printf("정적 : *p = %d\n", *p);
    int *q = leak_auto();
    printf("자동 : *q = %d   <- 이 값을 믿을 수 있나?\n", *q);
    return 0;
}
```

```text
===== 자동 저장 기간의 주소를 돌려주면 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : run exit=139 (출력 없음 — 죽었다)
gcc   -O1 : run exit=139 (출력 없음 — 죽었다)
gcc   -O2 : run exit=139 (출력 없음 — 죽었다)
clang -O0 : run exit=0   자동 : *q = 1234   <- 이 값을 믿을 수 있나?
clang -O1 : run exit=0   자동 : *q = 1234   <- 이 값을 믿을 수 있나?
clang -O2 : run exit=0   자동 : *q = -289897232   <- 이 값을 믿을 수 있나?
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 s28d.c -o x (cc exit=0) =====
s28d.c: In function ‘leak_auto’:
s28d.c:5:12: warning: function returns address of local variable [-Wreturn-local-addr]
    5 |     return &local;              /* ★ 블록이 끝나면 죽는 자리를 돌려준다 */
      |            ^~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O1 s28d.c -o x (cc exit=0) =====
s28d.c:5:13: warning: address of stack memory associated with local variable 'local' returned [-Wreturn-stack-address]
    5 |     return &local;              /* ★ 블록이 끝나면 죽는 자리를 돌려준다 */
      |             ^~~~~
1 warning generated.
```

```text
   같은 소스 · 같은 UB · 세 갈래

   gcc   -O0/-O1/-O2 : ★ run exit=139 — 출력이 아예 없다 (죽는다)
   clang -O0/-O1     : ★ run exit=0   — *q = 1234 ★ 정답처럼 보인다
   clang -O2         : ★ run exit=0   — *q = (쓰레기)

   경고는 둘 다 1건씩 나온다 — 그런데 ★ 플래그 이름이 다르다
     gcc   : [-Wreturn-local-addr]      "function returns address of local variable"
     clang : [-Wreturn-stack-address]   "address of stack memory ... returned"
   ★ 둘 다 cc exit=0 이다.
```

그림 해설 (한 단계씩):

- ★★★ **gcc 는 세 벌 전부 죽고**(`run exit=139`) **clang 은 세 벌 전부 산다**(`run exit=0`).\
  ★★★ **그리고 clang `-O0`/`-O1` 은 `1234` 라는 「정답」을 준다** — 이 주제에서 가장 위험한 칸이다.
- ★★★ **갈린 축이 「컴파일러」다.** [27번 형제](../27-compound-literals/)에서는 최적화 수준으로 갈렸는데 여기서는 컴파일러로 갈린다 —\
  ★★ **「무엇으로 갈리는가」를 한 축으로 단정하면 안 된다.** 둘 다 흔들어야 한다.
- ★★ **경고는 둘 다 1건**이고 **`cc exit=0`** 이다. 플래그 이름이 다르다 — `[-Wreturn-local-addr]` 대 `[-Wreturn-stack-address]`.\
  ★ **여기서는 clang 도 말해 준다** — [27번 형제](../27-compound-literals/)의 복합 리터럴 UB 에는 **0건**이었던 것과 갈린다.
- ★ **정적 쪽(`ok_static`)은 여섯 벌 전부 `1234`** 다. 비교군으로 쓴다.
- ★ **`setvbuf` 덕에 gcc 쪽에서도 첫 줄(`정적 : *p = 1234`)은 남는다** — 격자는 둘째 줄만 뽑았다.

비용 — **테스트가 한쪽 컴파일러에서 통과한다.** 그것도 **값이 맞아 보이는 쪽**으로.

**(5-나) 왜 gcc 만 죽나 — 역어셈블이 답한다**

```c
/* s28d2.c */
int *leak_auto(void) {
    int local = 1234;
    return &local;              /* ★ 블록이 끝나면 죽는 자리를 돌려준다 */
}
```

```text
===== gcc -std=c17 -O1 -S -masm=intel s28d2.c -o - | grep -v '^[[:space:]]*\.' (exit=0) =====
leak_auto:
	endbr64
	mov	eax, 0
	ret
```

```text
===== clang -std=c17 -O1 -S -masm=intel s28d2.c -o - | grep -v '^[[:space:]]*\.' (exit=0) =====
leak_auto:                              # @leak_auto
# %bb.0:
	lea	rax, [rsp - 4]
	ret
                                        # -- End function
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -fsanitize=address s28d.c -o x ; ASAN_OPTIONS=strip_path_prefix=/src/ ./x 2>&1 | sed -n '1,8p' (cc exit=0 · run exit=1) =====
정적 : *p = 1234
AddressSanitizer:DEADLYSIGNAL
=================================================================
==1123512==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000 (pc 0x621d6fd9f28f bp 0x7ffc5b579e20 sp 0x7ffc5b579d80 T0)
==1123512==The signal is caused by a READ memory access.
==1123512==Hint: address points to the zero page.
    #0 0x621d6fd9f28f in main (x+0x128f) (BuildId: 23905cc8a4b4952b2d88100226f09eb8c69d0917)
    #1 0x798b7b22a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
```

```text
   gcc   : mov eax, 0          <- ★ 널 포인터를 돌려준다
   clang : lea rax, [rsp - 4]  <- ★ 죽은 프레임의 주소를 그대로 돌려준다

   그래서
     gcc   -> *q 가 널 역참조 -> ★ SIGSEGV (run exit=139)
     clang -> *q 가 죽은 스택을 읽음 -> ★ 값이 남아 있으면 1234 가 나온다

   ASan 도 같은 말을 한다 — SEGV on unknown address 0x000000000000
                            "Hint: address points to the zero page"
```

- ★★★ **gcc 는 이 UB 를 「널 포인터 반환」으로 바꿔 버린다**(`mov eax, 0`). 그래서 **반드시 죽는다** — 조용히 지나가지 않는다.
- ★★★ **clang 은 `lea rax, [rsp - 4]`** 로 **스택 포인터보다 아래 주소**를 돌려준다. 그 자리가 아직 안 덮였으면 `1234` 가 읽힌다.
- ★★★ **이것이 이 주제의 네 번째 창의 두 번째 층이다** — **세 창(경고·실행 출력·sanitizer)이 「무슨 일이 났나」는 말해 줘도 「컴파일러가 이 UB 를 어떻게 처리했나」는 안 말해 준다.**\
  ★ `-S -masm=intel` **네 줄**이 그것을 답한다.
- ★★ **ASan 은 gcc 쪽에서 `SEGV on unknown address 0x000000000000` 을 내고 `Hint: address points to the zero page` 라고 적는다** — **널 포인터였음을 리포트가 직접 확인해 준다.**
- ★ ASan 리포트의 PID·`pc`/`bp`/`sp`·모듈 오프셋은 **흔들린다.** 안 흔들리는 것은 **`0x000000000000` 과 그 Hint 줄**이다.

### (6) ★★ 스레드 저장 기간 — 이름은 하나, 객체는 스레드마다

**언제 쓰나** — 전역 상태가 필요한데 스레드마다 달라야 할 때.

```c
/* s28e.c */
#include <stdio.h>
#include <pthread.h>
#include <stdint.h>

static _Thread_local int tls = 100;   /* ★ 스레드마다 한 벌 */
static           int shared = 100;    /* 정적 — 프로그램에 한 벌 */

struct Slot { int tls_val; uintptr_t tls_addr; uintptr_t shared_addr; };
static struct Slot slot[3];

static void *work(void *arg) {
    long id = (long)arg;
    tls += (int)id;                   /* 제 것만 고친다 */
    slot[id-1].tls_val     = tls;
    slot[id-1].tls_addr    = (uintptr_t)&tls;
    slot[id-1].shared_addr = (uintptr_t)&shared;
    return NULL;
}

int main(void) {
    pthread_t t[3];
    for (long i = 1; i <= 3; i++) pthread_create(&t[i-1], NULL, work, (void *)i);
    for (int i = 0; i < 3; i++) pthread_join(t[i], NULL);

    for (int i = 0; i < 3; i++)
        printf("스레드 %d : tls = %d\n", i + 1, slot[i].tls_val);
    printf("메인     : tls = %d   <- 스레드들이 고친 것이 안 보인다\n", tls);

    printf("\n&tls 가 셋 다 다른가     : %s\n",
           (slot[0].tls_addr != slot[1].tls_addr &&
            slot[1].tls_addr != slot[2].tls_addr &&
            slot[0].tls_addr != slot[2].tls_addr) ? "예 — 스레드마다 제 객체다" : "아니오");
    printf("&shared 가 셋 다 같은가  : %s\n",
           (slot[0].shared_addr == slot[1].shared_addr &&
            slot[1].shared_addr == slot[2].shared_addr) ? "예 — 프로그램에 한 객체다" : "아니오");
    printf("메인의 &tls 도 스레드들과 다른가 : %s\n",
           ((uintptr_t)&tls != slot[0].tls_addr) ? "예" : "아니오");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -pthread s28e.c -o x ; ./x (cc exit=0 · run exit=0) =====
스레드 1 : tls = 101
스레드 2 : tls = 102
스레드 3 : tls = 103
메인     : tls = 100   <- 스레드들이 고친 것이 안 보인다

&tls 가 셋 다 다른가     : 예 — 스레드마다 제 객체다
&shared 가 셋 다 같은가  : 예 — 프로그램에 한 객체다
메인의 &tls 도 스레드들과 다른가 : 예
```

```text
   static           int shared = 100;   ★ 프로그램에 ★ 한 객체
   static _Thread_local int tls = 100;  ★ 스레드마다 ★ 한 객체씩

   스레드 1 : tls += 1  -> 101      &tls  ┐
   스레드 2 : tls += 2  -> 102      &tls  ├─ ★ 셋 다 다르다
   스레드 3 : tls += 3  -> 103      &tls  ┘
   메인     : tls        -> ★ 100   &tls  ← 메인의 것도 또 다르다

   &shared : 셋 다 ★ 같다

   ★ 이름은 하나인데 객체가 넷이다 (메인 + 스레드 3).
```

그림 해설 (한 단계씩):

- ★★★ **세 스레드가 `101`·`102`·`103` 을 보고 메인은 `100` 을 본다.** 각자 제 것을 고쳤다.
- ★★★ **`&tls` 가 셋 다 다르고 `&shared` 는 셋 다 같다.** **주소로 「객체가 몇 개인가」를 직접 확인한 것**이다.\
  ★★ **값만 봐서는 갈리지 않는다** — 값은 「덮어쓰기가 운 좋게 안 났나」로도 읽힌다. (1)·(5)와 같은 형태의 창이다.
- ★★ **메인의 `&tls` 도 스레드들과 다르다.** 메인 스레드도 **제 사물함**을 갖는다.
- ★★ **출력이 결정적이다** — 스레드마다 **제 것만** 고치고 결과는 **배열에 담았다가 메인이 순서대로** 찍었다.\
  ★ **공유 변수를 여러 스레드가 고치는 실험은 일부러 안 했다** — 그것은 동시성 주제이지 저장 기간 주제가 아니다([`foundations/process-thread/`](../../../../process-thread/)).
- ★ **`-pthread` 가 필요하다.** `_Thread_local` 자체는 C11 문법이지만 스레드를 만드는 것은 POSIX 다.

비용 — **스레드마다 한 벌씩 메모리를 더 쓴다.** 그리고 **스레드가 끝나면 그 벌은 죽는다.**

### (7) ★ `thread_local` 이라는 철자 — 버전마다 다르다

**언제 쓰나** — 헤더에 스레드 지역 변수를 선언할 때.

```c
/* s28g.c */
#include <stdio.h>
thread_local int a = 1;             /* C23 키워드 */
int main(void) { printf("thread_local a = %d\n", a); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28g.c -o x (cc exit=1) =====
s28g.c:2:13: error: expected ‘;’ before ‘int’
    2 | thread_local int a = 1;             /* C23 키워드 */
      |             ^~~~
      |             ;
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic s28g.c -o x ; ./x (cc exit=0 · run exit=0) =====
thread_local a = 1
```

```c
/* s28g2.c */
#include <stdio.h>
#include <threads.h>
thread_local int a = 1;             /* <threads.h> 가 매크로로 준다 */
int main(void) { printf("thread_local a = %d\n", a); return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s28g2.c -o x ; ./x (cc exit=0 · run exit=0) =====
thread_local a = 1
```

```text
   철자              C11                     C23
   ---------------  ----------------------  ----------------------
   _Thread_local    ★ 키워드                 ★ 키워드 (계속 된다)
   thread_local     ★ <threads.h> 의 매크로   ★ 키워드

   실측
     gcc -std=c17  + thread_local (헤더 없음) -> ★ error · cc exit=1
     gcc -std=c2x  + thread_local (헤더 없음) -> ★ 통과 · 1 을 찍는다
     gcc -std=c17  + <threads.h> + thread_local -> ★ 통과 · 1 을 찍는다
```

- ★★ **`-std=c17` 에서 `thread_local` 을 그냥 쓰면 `error: expected ';' before 'int'`** 다 — 파서가 그 낱말을 모른다. **`cc exit=1`** 이다.
- ★★ **`-std=c2x` 에서는 키워드**라 그대로 통과한다.
- ★★ **C11·C17 에서도 `<threads.h>` 를 넣으면 된다** — 그 헤더가 `thread_local` 을 **매크로로** 준다.\
  ★ 그래서 **에러 메시지만 보고 「이 컴파일러는 지원 안 한다」로 읽으면 틀린다** — 헤더가 빠진 것일 수 있다.
- ★ **이식성을 생각하면 `_Thread_local` 이 가장 안전하다** — C11 부터 어디서나 키워드다.
- ★★ **철자 이야기가 하나 더 있다 — `-std=c23` 이라는 플래그 자체가 gcc 13 에 없다**(`cc exit=1` · 경고 0건).\
  clang 18 은 받아 준다. ★ 그래서 이 배치는 **둘 다 받는 `-std=c2x`** 로 고정했다([27번 형제](../27-compound-literals/)의 (6-나)가 실측이다).

### (8) ★★ 다른 문법들이 어느 저장 기간에 들어가나

**언제 쓰나** — 형제 주제의 문법을 이 표에 얹을 때.

```text
   문법                              저장 기간          정본
   -------------------------------  ---------------   -------------------------
   함수 안 int a;                    ★ 자동             이 주제
   함수 안 static int s;             ★ 정적             이 주제 · 29번 주제(링크)
   파일 스코프 int g;                 ★ 정적             29번 주제(링크)
   _Thread_local int t;              ★ 스레드           이 주제
   malloc / calloc / realloc         ★ 할당             37번 주제(계약)
   "hello" (문자열 리터럴)            ★ 정적 · r--p      20번 형제
   함수 안 (struct P){1,2}           ★ 자동             27번 형제
   파일 스코프 (struct P){1,2}        ★ 정적             27번 형제
   (static struct P){1,2}            ★ 정적 (C23부터)   27번 형제
   함수 안 int vla[n];               ★ 자동 (스택)      18번 형제
   opaque struct 의 객체              ★ 사실상 할당뿐     25번 형제
   FAM 구조체                         ★ 사실상 할당뿐     26번 형제

   ★ 25·26번 형제는 ★ 「고를 수 없어서」 할당으로 떠밀린 경우다 — 이유는 달라도 결과는 같다.
```

- ★★ **복합 리터럴도 VLA 도 새 저장 기간을 만들지 않는다** — 전부 **자동이거나 정적**이다.
- ★★ opaque struct 와 FAM 구조체는 「**선택」이 아니라 「강제**」다. 크기를 모르거나 꼬리를 못 주므로 **`malloc` 밖에 길이 없다.**
- ★ **문자열 리터럴만 정적인데 권한이 `r--p`** 다((1)). 같은 「정적」이라도 **쓸 수 있느냐는 또 다른 축**이다.

## 문법 — 형태와 규칙

### 형태

```text
void f(void) {
    int a;                  /* ★ 자동 — 블록이 끝나면 죽는다. 초기값 불확정 */
    int b = 0;              /* 자동 + 초기화 */
    static int s;           /* ★ 정적 — 프로그램이 끝날 때까지. ★ 0 이 보장된다 */
    static int t = 42;      /* 정적 + 초기자 (프로그램 시작 전에 한 번) */
    int vla[n];             /* 자동 — 스택에 잡힌다 (18번 형제) */
    int *h = malloc(n);     /* ★ 할당 — free 를 부를 때까지 */
    free(h);
}

static int g_file;          /* 정적 + 내부 링크 (29번 주제) */
int        g_extern;        /* 정적 + 외부 링크 */

static _Thread_local int tls;           /* ★ 스레드 — C11부터 */
#include <threads.h>
static thread_local int tls2;           /* 같은 것 — C11 은 매크로, C23 은 키워드 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
int *f(void) { int local = 1234; return &local; }
/* ★★★ UB — 죽은 자동 객체의 주소를 돌려준다.
   gcc 는 널을 돌려줘 ★ run exit=139 · clang 은 죽은 스택 주소를 돌려줘 ★ 1234 가 나온다 */

char *g(void) { char buf[16]; sprintf(buf, "x"); return buf; }
/* ★★★ 같은 UB — 배열이라 감쇠했을 뿐이다 */

void h(void) { int a; printf("%d", a); }
/* ★★ 불확정 값을 읽는다. gcc 는 [-Wuninitialized] 로 잡고 ★ cc exit=0 */

void big(void) { char buf[64*1024*1024]; buf[0]=1; }
/* ★ 스택 한도를 넘는다 — 이 환경에서 ★ run exit=139. ★ 진단 0건 */

void reent(void) { static int s; s++; }
/* ★ UB 아님 — 다만 ★ 재진입 불가 · 스레드 안전하지 않다 */

"hello"[0] = 'X';
/* ★★ UB — 그 구역의 권한이 ★ r--p 다 (20번 형제) */

thread_local int t;   /* ★ -std=c17 에서 헤더 없이 쓰면 컴파일 에러 · cc exit=1 */
```

### 규칙 불릿

- ★★★ **저장 기간은 넷뿐이다** — 자동 · 정적 · 스레드 · 할당. **새 문법이 새 저장 기간을 만들지 않는다.**
- ★★★ **자동은 블록이 끝날 때 죽는다.** 그 주소를 블록 밖으로 내보내면 **UB** 이고, **여섯 벌이 세 갈래로 갈렸다.**
- ★★★ **정적 객체는 0 으로 초기화되고 자동 객체는 불확정**이다. 「0 이 나왔다」는 **관찰**이지 보장이 아니다.
- ★★ **함수 안 `static` 은 저장 기간을 바꾸고, 파일 스코프 `static` 은 링크를 바꾼다.** **같은 낱말이 자리에 따라 다른 일**을 한다(목록의 **29번 주제**).
- ★★ **「주소가 같다」와 「살아 있다」는 다르다** — 세 호출의 `&a` 가 같은 자리였지만 매번 **죽고 다시 태어났다.**
- ★★ **스레드 저장 기간은 C11 부터**(`_Thread_local`). **이름은 하나인데 객체는 스레드마다 하나씩**이다.
- ★★ **`thread_local` 이라는 철자는 C11 에서 `<threads.h>` 의 매크로, C23 부터 키워드**다. 이식성은 `_Thread_local` 이 낫다.
- ★★ **스택은 한도가 있고 컴파일러가 안 알려 준다** — 이 환경에서 `ulimit -s` 가 8 MiB 이고 **64 MiB 자동 배열이 `run exit=139`** 였다.
- ★★ **할당은 실패를 알려 준다**(`NULL`). 스택은 **넘치면 그냥 죽는다** — 검사할 방법이 없다.
- ★ **문자열 리터럴은 정적인데 `r--p`** 다 — **「정적」과 「쓸 수 있다」는 다른 축**이다.
- ★ **이 UB 는 `-pedantic-errors` 로도 못 막는다** — 경고를 에러로 올리는 것과 무관하게 `cc exit=0` 이고, 애초에 경고가 안 나는 자리도 있다.
- ★ **역어셈블이 「컴파일러가 이 UB 를 어떻게 처리했나」를 답한다** — gcc 는 `mov eax, 0`, clang 은 `lea rax, [rsp - 4]`.

## 어디서 틀리나

### 1. ★★★ 「clang 에서는 `1234` 가 잘 나오던데」

**여섯 벌 중 두 벌만 그렇다**((5)). gcc 는 세 벌 전부 **`run exit=139`** 로 죽고 clang `-O2` 는 쓰레기를 준다.\
★★ 그리고 **`1234` 를 주는 쪽이 「더 나은 컴파일러」가 아니다** — gcc 는 널을 돌려줘 **반드시 죽게** 만들었고, clang 은 **조용히 지나가게** 뒀다.\
★ **죽는 쪽이 오히려 안전하다.**

### 2. ★★★ 「초기화 안 해도 0 이던데」

**정적만 그렇다**((3)). 자동 변수는 **불확정**이고, gcc `-O0` 의 `a_indet=0` 은 **여섯 벌 중 한 벌의 관찰**이다.\
★★ clang 은 세 벌 다 쓰레기를 줬다. **「0 이 나왔다」를 「0 으로 초기화된다」로 읽으면 안 된다.**

### 3. ★★★ 「주소가 같으니 살아 있는 거 아닌가」

**아니다**((2)). 세 호출의 `&a` 가 같은 자리였지만 **매번 죽고 다시 태어났다.**\
★ 이 오해가 (5)의 UB 를 「괜찮아 보이게」 만든다 — **스택은 자리를 재사용할 뿐**이다.

### 4. ★★ 「큰 배열이면 컴파일러가 경고해 주겠지」

**진단 0건**이다((4)). 64 MiB 자동 배열이 **경고 한 줄 없이 `run exit=139`** 로 죽었다.\
★ 크기가 실행 시간에 정해지면 **볼 정보 자체가 없다.** 큰 것은 **힙에 둔다.**

### 5. ★★ 「함수 안 `static` 이 편하네」

**재진입 불가·스레드 안전하지 않다**((2)). 두 스레드가 같이 부르면 **한 객체를 같이 고친다.**\
★ 스레드마다 달라야 하면 **`_Thread_local`**((6)), 호출마다 달라야 하면 **호출자가 준 자리**다.

### 6. ★★ 「`static` 이면 다 같은 얘기 아닌가」

**자리에 따라 다른 일을 한다**((2)). **함수 안**이면 저장 기간을, **파일 스코프**면 링크를 바꾼다.\
★ 링크 쪽은 목록의 **29번 주제**가 정본이다.

### 7. ★ 「`thread_local` 이 에러 나니 이 컴파일러는 지원 안 하나 보다」

**헤더가 빠진 것일 수 있다**((7)). `-std=c17` 에서는 **`<threads.h>` 를 넣으면 통과**한다.\
★ C23 부터는 헤더 없이도 키워드다.

### 8. ★ 「정적이면 못 고치는 거 아닌가」

**구역의 권한에 달렸다**((1)). `s_bss`·`s_data` 는 `rw-p` 라 고칠 수 있고,\
★ **문자열 리터럴만 `r--p`** 라 고치면 죽는다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 네 저장 기간의 수명과 초기화 규칙이 전부 거기 있다.\
★★ 두 번째는 「**UB**」다 — **죽은 자동 객체를 읽는 것.** 여섯 벌이 **세 갈래**로 갈렸다.\
★ **구현 정의 칸은 얇고**(스택 한도·구역 배치), **미명시 칸도 얇다**(불확정 값으로 무엇이 읽히나).

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | **네 저장 기간과 각각의 수명** · **정적 객체가 0 으로 초기화되는 것** · **자동 객체가 불확정인 것** · **함수 안 `static` 이 호출을 가로질러 사는 것** · **스레드마다 `_Thread_local` 객체가 하나씩인 것**(C11부터) · `thread_local` 철자의 버전 규칙 | `s_zero=0`·`s_arr = 0 0 0 0`(여섯 벌 동일) · `a=1 s=1/2/3` · `&tls` 셋이 다르고 `&shared` 셋이 같음 · `-std=c17` 에서 `thread_local` **`cc exit=1`**, `<threads.h>` 로 통과 |
| **조건부 표준** | 매크로가 정의될 때만 | ★★ **`thread_local` 이라는 철자**가 여기 걸린다 — **C11·C17 에서는 `<threads.h>` 가 정의할 때만** 쓸 수 있다(C23 부터는 키워드) | `-std=c17` + 헤더 없음 → **에러** · `-std=c17` + `<threads.h>` → **통과** |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **스택 한도**(`ulimit -s` = 8192 KiB) · **각 저장 기간이 어느 구역에 놓이는가** · **문자열 리터럴 구역의 권한**(`r--p`) · 진단 문구와 플래그 이름 · **컴파일러가 UB 를 어떻게 번역하는가** | `/proc/self/maps` 대조 6행 · 1/4 MiB 성공, 64 MiB **`run exit=139`** · `[-Wreturn-local-addr]` 대 `[-Wreturn-stack-address]` · `mov eax, 0` 대 `lea rax, [rsp - 4]` |
| ★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★ **불확정 값으로 무엇이 읽히는가** · ★ 죽은 자동 객체의 자리가 **언제 덮이는가** | 여섯 벌 격자 — gcc 는 `a_indet=0`, clang 은 쓰레기. **실행마다도 바뀐다** |
| ★★ **UB** | 아무 일이나 | ★★★ **죽은 자동 객체를 읽는 것**(주소를 반환하거나 전역에 저장) · ★ **문자열 리터럴을 고치는 것**([20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본) · ★ **스택을 넘기는 것** | ★★ **여섯 벌** — gcc 셋은 `run exit=139`, clang `-O0`/`-O1` 은 **`1234`**, clang `-O2` 는 쓰레기. **경고는 둘 다 1건 · `cc exit=0`** · ASan `SEGV on unknown address 0x000000000000` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **「이 객체가 지금 살아 있나」를 말해 주는 도구가 없다.** 컴파일러는 **선언 자리**만 보고, 실행 중에 그것을 묻는 창은 sanitizer 뿐이다. ★ **`&a` 가 세 호출에서 같았다**는 것도 **직접 찍어야** 안다 |
| ★★ **조건부 표준** | ★★ **`thread_local` 이 에러 날 때 「헤더가 없어서인지 버전이 낮아서인지」를 진단이 안 가른다** — 둘 다 `error: expected ';' before 'int'` 다. ★ **헤더를 넣어 다시 던져 봐야** 갈린다 |
| ★ **구현 정의** | ★★★ **스택 한도를 넘는 것에 진단이 0건**이다 — 64 MiB 자동 배열이 **경고 한 줄 없이** 죽었다. ★ **`ulimit -s` 는 환경 설정이라 같은 바이너리가 환경에 따라 죽고 산다** |
| ★ **미명시** | ★ **불확정 값이 무엇인지 아무도 안 알려 준다.** gcc 가 `[-Wuninitialized]` 로 **읽었다는 사실**은 잡지만 **무엇이 읽혔는지**는 말하지 않는다 |
| ★★ **UB** | ★★★ **`cc exit=0`** 이다 — 두 컴파일러가 각각 1건씩 경고를 내는데 **빌드는 통과**한다. ★★★ **그리고 clang `-O0`/`-O1` 은 `1234` 라는 「정답」을 준다** — 실행 출력이 **함정**이다. ★★ **세 창 중 어느 것도 「컴파일러가 이 UB 를 어떻게 번역했나」는 말해 주지 않는다** — 역어셈블만 답한다 |

- ★★ **이 표의 결론 네 줄**
  - ★★★ **가장 위험한 칸은 clang `-O0`/`-O1` 의 `1234`** 다 — **경고도 났는데 값이 맞아 보인다.** 「경고는 봤지만 돌려 보니 되던데」가 정확히 여기서 난다.
  - ★★★ **갈린 축이 [27번 형제](../27-compound-literals/)와 다르다** — 거기서는 최적화 수준, 여기서는 **컴파일러**였다. **처방이 없으므로 둘 다 흔든다.**
  - ★★ **스택 한도는 진단이 0건**이고 **환경 설정에 달렸다** — 「내 머신에서 되던데」가 가장 약한 근거가 되는 자리다.
  - ★ **조건부 표준 칸이 비어 있지 않은 드문 주제**다 — `thread_local` 이 **헤더가 정의할 때만** 쓸 수 있는 철자였다.

### 이 주제의 네 번째 창 — **역어셈블(`gcc -S -masm=intel`)**

- **컴파일 진단**은 (5)를 잡는다(둘 다 1건) — 그런데 **`cc exit=0`** 이고 빌드가 나간다.
- **실행 출력**은 clang 에서 **`1234` 라는 정답**을 준다 — 창이 아니라 **함정**이다.
- **sanitizer** 는 gcc 쪽에서 **`SEGV on … 0x000000000000`** 을 내지만, **왜 널인지**는 말하지 않는다.
- ★★★ 그래서 네 번째 창은 「**역어셈블 네 줄**」이다.\
  `mov eax, 0`(gcc)과 `lea rax, [rsp - 4]`(clang) — **컴파일러가 이 UB 를 무엇으로 번역했는지**가 거기 있다.\
  ★★ 그 한 줄이 「**gcc 는 왜 늘 죽고 clang 은 왜 값이 나오나**」를 통째로 설명한다.
- ★ **(1)의 `/proc/self/maps` 대조는 그 앞 단계의 창**이다 — 「이 주소가 어느 구역인가」를 묻는다.\
  ★ 주소는 ASLR 로 흔들려도 **구역 이름과 권한은 안 흔들린다.**

## 언제 쓰고 언제 안 쓰나

| 이 값을 어디에 둘까 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 함수 안에서만 쓰는 작은 값 | ★★ **자동** `int a = 0;` | ★ 초기화 없이 쓰기 |
| 함수 안에서만 쓰는 **큰 버퍼** | ★★ **할당**(`malloc`) — 실패를 검사할 수 있다 | ★★ 자동 배열(스택 한도를 넘으면 그냥 죽는다) |
| 함수 호출을 가로질러 남기기 | **함수 안 `static`** | 전역 변수(이름이 새어 나간다) |
| 파일 안에서만 공유하기 | **파일 스코프 `static`**(목록의 **29번 주제**) | 그냥 전역 |
| 스레드마다 달라야 하는 것 | ★★ **`_Thread_local`** | ★★ 함수 안 `static`(공유된다) |
| 크기가 실행 시간에 정해지는 것 | ★ **할당** | ★ VLA(스택 한도가 걸린다 — [18번 형제](../18-variable-length-arrays-vla/)) |
| 함수 밖으로 돌려줄 것 | ★★★ **할당** 또는 **호출자가 준 자리에 채우기** | ★★★ 지역 변수의 주소 |
| 읽기 전용 문자열 | `const char *s = "hello";` | ★ `char *s = "hello";` 뒤에 수정(`r--p` 다) |
| 이름은 하나인데 객체는 여럿 | `_Thread_local` | 배열 + 스레드 인덱스(직접 관리해야 한다) |
| 이식되는 철자 | ★ **`_Thread_local`** | ★ 헤더 없는 `thread_local`(C17 에서 에러) |
| 이 UB 를 잡기 | ★★ **두 컴파일러 + ASan** | ★★ 한 컴파일러의 실행 결과 |

판단 규칙 두 줄.

- ★★★ **「이 값이 이 블록보다 오래 살아야 하나」를 먼저 묻는다** — 답이 「예」면 자동은 탈락이다.
- ★★ **「몇 개 있어야 하나」를 그다음에 묻는다** — 프로그램에 하나면 정적, 스레드마다면 스레드, 호출마다면 자동이나 할당이다.

## 핵심 문장

- ★★★ **저장 기간은 넷뿐이고**(자동·정적·스레드·할당) **어떤 문법도 다섯째를 만들지 않는다.**
- ★★★ **죽은 자동 객체를 읽는 것은 UB** 이고 **여섯 벌이 세 갈래**로 갈렸다 — gcc 셋은 `run exit=139`, clang `-O0`/`-O1` 은 **`1234`**, clang `-O2` 는 쓰레기다.
- ★★★ **갈린 축이 「컴파일러」였다** — [27번 형제](../27-compound-literals/)에서는 최적화 수준이었다. **한 축으로 단정하면 안 된다.**
- ★★★ **역어셈블 네 줄이 그 이유를 답한다** — gcc `mov eax, 0`(널) 대 clang `lea rax, [rsp - 4]`(죽은 프레임).
- ★★ **정적은 0 이 보장되고 자동은 불확정**이다. gcc `-O0` 의 `a_indet=0` 은 **관찰이지 보장이 아니다.**
- ★★ **「주소가 같다」와 「살아 있다」는 다르다** — 세 호출의 `&a` 가 같은 자리였지만 매번 죽고 다시 태어났다.
- ★★ **함수 안 `static` 은 저장 기간을, 파일 스코프 `static` 은 링크를 바꾼다.**
- ★★ **스택 한도를 넘는 것에 진단이 0건**이다 — 64 MiB 자동 배열이 경고 없이 `run exit=139` 였다.
- ★★ **`_Thread_local` 은 이름 하나에 객체 여럿**이다 — `&tls` 셋이 다르고 `&shared` 셋이 같았다.
- ★ **`thread_local` 은 C11 에서 `<threads.h>` 의 매크로, C23 부터 키워드**다.

## 관련 자료

- [`foundations/memory-management/`](../../../../memory-management/) · [`foundations/variables-and-memory/`](../../../../variables-and-memory/) — ★★ **경계.**\
  **스택 프레임·가상 메모리·힙의 구조**는 그쪽이 정본이고, 여기는 「**C 에서 무엇을 고르나**」만 다룬다.\
  ★ 이 편의 (1)은 그 구조를 **다시 설명하지 않고** `/proc/self/maps` 에 **대조만** 한다.
- 목록의 **29번 주제** — 스코프와 링크(`static`·`extern`). **파일 스코프 `static` 이 링크를 바꾸는 것**은 그쪽이 정본이다.
- 목록의 **30번 주제** — 초기화 규칙과 불확정 값. **무엇이 0 이 되고 무엇이 불확정인가**의 정본이다. 여기는 **저장 기간과 묶어서만** 본다.
- 목록의 **37번 주제** — `malloc`/`calloc`/`realloc`/`free`. **할당 저장 기간의 API 계약**은 그쪽이다.
- 목록의 **57번 주제** — 시간 위반(해제 후 사용·이중 해제·댕글링). **(5)의 UB 가 왜 최악인가**는 그쪽이다.
- 목록의 **58번 주제** — UB 를 잡는 도구. (5)의 ASan 과 경고 플래그는 그쪽이 정본이다.
- [20번 형제 — 널 종단 문자열과 문자열 리터럴](../20-null-terminated-strings-and-string-literals/) — ★★ **문자열 리터럴의 저장 기간·수정 금지**의 정본.\
  ★ 여기서는 **`r--p` 라는 실측**만 더한다.
- [18번 형제 — 가변 길이 배열(VLA)](../18-variable-length-arrays-vla/) — ★★ (4)의 큰 배열이 VLA 다. **VLA 자체**는 그쪽이 정본이고, 여기는 「**스택에 놓인다**」는 사실만.
- [27번 형제 — 복합 리터럴](../27-compound-literals/) — ★★ **같은 UB 의 다른 얼굴.**\
  거기서는 **최적화 수준**으로 갈렸고 여기서는 **컴파일러**로 갈렸다. 두 편을 나란히 읽으면 「**축을 단정하지 마라**」가 실측으로 보인다.
- [25번 형제](../25-incomplete-types-and-opaque-struct/) · [26번 형제](../26-flexible-array-members/) — ★ 둘 다 **할당 저장 기간으로 떠밀리는** 주제다. 이유는 달라도 결과가 같다((8)).
- [14번 형제 — 포인터](../14-pointers-address-dereference-and-pointer-types/) — ★ **직접 선행.** 「포인터의 값」과 「가리키는 값」을 가르는 것이 (5)의 전제다.
- [`foundations/process-thread/`](../../../../process-thread/) — ★ **동시성 개념 자체**는 그쪽이다. (6)은 **경쟁을 일부러 안 만들었다.**
- ★ **C++ 갈래와 갈리는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)).\
  ★★ **`thread_local` 은 C++11 부터 키워드**라 헤더가 필요 없다 — C 에서 (7)처럼 갈리는 자리가 **C++ 에는 없다.**\
  ★ 그리고 C++ 에는 **생성자·소멸자가 붙는 정적 객체**가 있어 「정적 초기화 순서」라는 **C 에 없는 문제**가 생긴다(이 문서는 그쪽을 **던지지 않았다**).

## 용어 풀이

> **저장 기간(storage duration)** — 그 객체가 **언제 태어나 언제 죽는가.** 네 가지뿐이다.\
> 예: 함수 안 `int a;` 는 자동, `static int s;` 는 정적이다.

> **자동 저장 기간(automatic)** — 블록에 들어갈 때 태어나 **블록이 끝날 때 죽는** 것.\
> 예: 지역 변수. 초기값은 **불확정**이다.

> **정적 저장 기간(static)** — 프로그램이 시작하기 전에 태어나 **끝날 때까지 사는** 것.\
> 예: `static int s;` · 전역 변수 · 문자열 리터럴. 초기값은 **0 이 보장**된다.

> **스레드 저장 기간(thread)** — 스레드가 생길 때 태어나 **그 스레드가 끝날 때 죽는** 것. **C11 부터.**\
> 예: `_Thread_local int t;`. 이름은 하나인데 **객체는 스레드마다 하나씩**이다.

> **할당 저장 기간(allocated)** — `malloc` 이 돌려준 순간 태어나 **`free` 를 부를 때 죽는** 것.\
> 예: `int *h = malloc(4);`. 수명을 **내가 정한다.**

> **불확정 값(indeterminate value)** — 무엇이 들어 있는지 정해지지 않은 상태.\
> 예: 초기화 안 한 자동 변수. 여섯 벌 중 gcc 는 `0`, clang 은 쓰레기를 줬다.

> **ASLR(주소 공간 배치 난수화)** — 실행할 때마다 구역의 시작 주소를 바꾸는 것.\
> 예: `%p` 는 실행마다 바뀌고 **두 주소의 차**는 안 바뀐다.

> **`/proc/self/maps`** — 리눅스가 그 프로세스의 **메모리 구역 목록**을 보여 주는 파일.\
> 예: 각 줄에 주소 범위 · 권한(`rw-p`) · 이름(`[stack]`·`[heap]`)이 있다.

## 더 들어가면

- ★★ **`calloc` 과 정적 초기화의 「0」이 같은 것인가** — 둘 다 바이트를 0 으로 만들지만,\
  **포인터의 널 표현이 모든 비트 0 이라는 보장은 없다.** ★ 이 문서는 **그쪽을 던지지 않았다**(목록의 **30번 주제**·**37번 주제**).
- ★★ **스레드 저장 기간 객체의 소멸** — C11 의 `tss_t`·`tss_create` 로 **소멸자**를 달 수 있다.\
  ★ 이 문서는 **`<threads.h>` 의 스레드 API 를 던지지 않았다**(`thread_local` 매크로만 썼다).
- ★ **`ulimit -s unlimited` 로 한도를 올리면 (4)가 어떻게 되나** — ★ **던지지 않았다.**
- ★ **`-fstack-clash-protection`·`-fstack-protector` 가 (4)를 어떻게 바꾸나** — ★ **던지지 않았다.**
- ★ **`ASAN_OPTIONS=detect_stack_use_after_return=1`** 로 (5)를 잡는 것 — ★ 이 문서는 **널 역참조로 죽는 쪽만** 봤고 그 옵션은 **던지지 않았다.**
- ★ **정적 객체가 실제로 `.bss` 와 `.data` 중 어디에 가는지 `objdump` 로 확인하는 것** — ★ **던지지 않았다.**\
  ★ (1)은 `/proc/self/maps` 까지만 봤고, 그 안에서 `.bss` 와 `.data` 를 **가르지 않았다**(둘 다 `rw-p` 실행 파일 이미지로 나온다).
- ★ **`-O3`·`-Os` 에서의 (5) 격자** — ★ **던지지 않았다**(`-O0`\~`-O2` 까지만 흔들었다).
