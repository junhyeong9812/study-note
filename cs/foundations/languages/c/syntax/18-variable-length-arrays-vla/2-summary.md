# c/syntax/18 — 가변 길이 배열(VLA): 「**크기를 실행 시점에 정하고, 그 자리를 스택에서 꺼낸다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **이 문서는 표준 문서 URL 을 새로 열지 않았다.** 표준 쪽 사실은 [`../README.md`](../README.md) 가 선언한 기준 소스(C17 대응 초안 **N2310** · C23 대응 초안 **N3220** · cppreference)를 따르고, **숫자·진단·종료 코드는 전부 이 머신의 실행으로 접지했다.** ★ **표준 조항 번호는 쓰지 않는다.**
> **실행 검증** — 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본은 `-std=c17 -Wall -Wextra -pedantic`, 작업 디렉터리는 `/tmp/c17b/18`, 소스는 `ex.c`\~`ex7.c` 다.\
> ★★ **`-std=` 비교 블록은 「컴파일 + 실행」을 한 덩어리로 받은 꼴이라 실행 출력만 실린다** — **각 `-std=` 의 경고 건수는 이 문서의 근거가 아니다.**\
> 그 블록이 말하는 것은 **`cc exit=0 · run exit=0`** 과 **프로그램이 스스로 찍은 답** 둘이다. 경고 쪽 근거는 **`-Wvla` 블록 하나**뿐이다.\
> ★ 소스 블록의 첫 줄 `/* ex4.c */` 는 **캡처가 붙인 파일명 배너**다 — 진단의 줄 번호는 **그 줄을 뺀 실파일 기준**이다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 주소 · `pc`/`bp`/`sp` · PID · `BuildId` · 박힌 경로 | ★ **`sizeof` 값**(32 · 16 · 36 · 68 · 20 · 12 · 8 · 4) |
> | `n = 0` 판이 찍은 원소 값 — **UB 의 산물이다** | ★ **`f()` 호출 횟수**(모두 **2**) · `__STDC_VERSION__` 값 |
> | — | **종료 코드**(`0` · `1` · `139`) · 진단 본문 · 플래그 이름 |
> | — | ★ **8MB 경계의 부등호** — 8,000,000 통과, 9,000,000 죽음 |
>
> **버전** — **VLA 는 C99부터**다. ★★ **C99 필수 → C11 선택**(`__STDC_NO_VLA__`) **→ C23 에서 선택 범위 축소.** 그 셋은 **표준 문서 쪽 사실**이고, **이 구현이 실제로 어떤가는 따로 쟀다**((3)).
> ★★ **경계** — **`goto`·`switch` 가 VLA 스코프로 못 뛰는 것**은 [12번 형제](../12-control-flow-and-switch/)가 정본이다. 여기서는 **결론만 되짚고 두 컴파일러 문구 차이**만 짚는다(관용구는 [13번 형제](../13-goto-cleanup-idiom/)).\
> **`sizeof` 의 일반 규칙**은 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이고 여기는 「**VLA 면 어디까지 평가되나**」만 본다. **감쇠와 매개변수 재작성**은 [16번 형제](../16-array-pointer-decay-and-function-parameters/).\
> **다차원 배열의 안쪽 보폭**은 [목록의 **17번 주제**](../17-multidimensional-arrays-and-pointer-types/) — ★ 그쪽은 **컴파일 시점**, 여기는 **실행 시점**이다. 저장 기간 고르기는 [목록의 **28번 주제**](../28-choosing-among-four-storage-durations/), `malloc` 은 [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/).
> 선행 — [16번 형제](../16-array-pointer-decay-and-function-parameters/) · [08번 형제](../08-sizeof-alignment-and-offsetof/) · [12번 형제](../12-control-flow-and-switch/).

## 한눈에 — 쉽게 말하면

**보통 배열은 도면에 그려 둔 주차 구획이고, VLA 는 차가 들어올 때 길이를 재서 고깔을 세우는 것이다.**

보통 구획은 **도면에 이미 그려져 있다** — 몇 자리인지 도면만 보면 안다.\
VLA 는 **차가 들어오는 순간 길이를 재서** 그만큼 고깔을 세우고, 차가 나가면 걷는다.

여기서 두 가지가 따라온다.

- **「몇 자리냐」를 도면으로 답할 수 없다** — ★ 그래서 `sizeof` 가 **실행 시점**에 계산된다.
- **주차장이 얼마나 넓은지 아무도 말해 주지 않는다** — 벽에 부딪혀도 **경고등도 안내방송도 없다.** ★ **이것이 가장 위험한 자리**다.

| 비유 | 실체 | 층 |
|---|---|---|
| 도면에 그려 둔 구획 | `int fixed[8]` — `sizeof` 가 **32** | **표준** |
| 차 길이를 재서 세운 고깔 | `int vla[n]` — 타입이 실행 시점에 정해진다 | ★ **조건부 표준** |
| 「몇 자리냐」를 차가 온 뒤에야 안다 | `sizeof vla` 가 **16 · 36 · 68** 로 달라진다 | **표준** |
| 차가 나가면 고깔을 걷는다 | 저장 기간이 **자동**이다 | **표준** |
| 고깔을 영구 시설로 못 만든다 | `static`·파일 스코프·구조체 멤버·`extern` 이 **전부 에러** | **표준** |
| 「우리는 고깔 서비스 안 합니다」 안내문 | `__STDC_NO_VLA__` | ★ **조건부 표준** |
| ★ 이 머신엔 그 안내문이 **안 붙어 있다** | 여덟 벌 전부 **정의 안 됨** | ★ **재 본 것** |
| 주차장이 얼마나 넓은가 | `ulimit -s` = **8192 KB** | **환경 한계** |
| 고깔을 세우다 벽에 부딪힘 | 스택 소진 — ★ **진단 없이 `run exit=139`** | ★ **UB** |
| 길이를 0 이나 음수로 재는 것 | `char vla[0]` · `char vla[-1]` | ★ **UB** |
| 옆 건물 유료 주차장 | `malloc` — **없으면 「없다」고 말해 준다**(`NULL`) | [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/) |

```text
   고정 배열                              VLA
   int fixed[8];                         int vla[n];        (n 은 실행 시점 값)

   +--------------------------+          +--------------------------+
   | 크기 : 컴파일 시간에 확정   |          | 크기 : ★ 실행 시점에 확정  |
   | sizeof : ★ 상수 (32)      |          | sizeof : ★ 그때 계산 (16) |
   | 어디에 : 스택 프레임        |          | 어디에 : ★ 표준은 말 안 함 |
   | 실패 : 없음 (컴파일이 잡음) |          | 실패 : ★ 진단 없이 죽는다  |
   +--------------------------+          +--------------------------+

   ★ 같은 대괄호 표기인데 ─ 한쪽은 도면에 있고, 한쪽은 그때 가서 잰다.
```

> **VLA(variable length array · 가변 길이 배열)** — 크기를 **실행 시점의 값**으로 정하는 배열.\
> 예: `int vla[n]` 에서 `n` 이 4 면 `sizeof vla` 가 16, 9 면 36 이다.

> **조건부 기능(conditional feature)** — 표준에 있지만 **구현이 「안 준다」고 선언할 수 있는** 기능.\
> 예: VLA 는 C11 부터 그렇다 — 안 주는 구현은 `__STDC_NO_VLA__` 를 정의해 그 사실을 말한다.

## 이 주제가 답하려는 질문

1. ★★★ **「C99 필수 → C11 선택 → C23」이 내 컴파일러에서는 무엇으로 나타나나** — `__STDC_NO_VLA__` 를 여덟 벌로 직접 찍는다.
2. ★★ **`sizeof` 가 VLA 에서 어디까지 평가되나** — 여섯 식으로 **「VLA 를 썼으니 평가된다」가 틀렸다**는 것을 본다.
3. ★★ **크기를 잘못 잡으면 누가 말해 주나** — 스택 소진·0·음수 셋을 던져 **누가 침묵하는지**를 본다.

## 동작 방식

### (1) `sizeof` 가 실행 시점에 계산된다 — 같은 함수를 세 `n` 으로 부른다

**언제 쓰나** — 「`sizeof` 는 컴파일 시간 상수다」라고 배운 뒤 VLA 를 처음 만났을 때.

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

```text
   같은 함수 show(n) 을 세 번 부른다 — 한 번의 컴파일, 세 개의 크기

   show(4)                  show(9)                  show(17)
   +--------------------+   +--------------------+   +--------------------+
   | vla   : int[4]     |   | vla   : int[9]     |   | vla   : int[17]    |
   | sizeof vla  =  16  |   | sizeof vla  =  36  |   | sizeof vla  =  68  |
   | fixed : int[8] = 32|   | fixed : int[8] = 32|   | fixed : int[8] = 32|
   +--------------------+   +--------------------+   +--------------------+

   ★ 흔들린 칸은 vla 쪽뿐이다. fixed 는 세 번 다 32 — 도면에 그려져 있으니까.
```

그림 해설 (한 단계씩):

- **`sizeof vla` 가 16 · 36 · 68** 이다. **한 번 컴파일한 같은 코드**가 호출마다 다른 값을 낸다.\
  ★ **`sizeof` 가 상수가 아닌 자리는 C 에 이것 하나**다(일반 규칙은 [08번 형제](../08-sizeof-alignment-and-offsetof/)).
- **`sizeof vla / sizeof vla[0]` 이 여기서는 맞는 답**을 낸다(4 · 9 · 17). ★ **매개변수로 넘기는 순간 틀린다**((6)).
- **결과 타입은 `size_t`** 다 — `_Generic` 으로 물어 받았다. 바뀌는 것은 **언제 정해지느냐**뿐이다.
- ★ `&vla` 가 세 번 다 `&fixed` 보다 **낮은 주소**였다 — **관찰이지 보장이 아니다.** 표준은 **어디에 잡는지 말하지 않는다.**

비용 — **크기가 공짜가 아니다.** 함수에 들어갈 때마다 **그만큼 자리를 잡는 일**이 실행 시점에 일어난다.

### (2) ★★ `sizeof` 가 피연산자를 **평가하는 자리와 아닌 자리** — 여섯 식을 던진다

**언제 쓰나** — 「VLA 면 `sizeof` 의 피연산자가 평가된다」를 외운 뒤 **어디까지 그런지** 확인할 때.\
★ **[08번 형제](../08-sizeof-alignment-and-offsetof/)가 `sizeof` 일반 규칙의 정본**이고 여기서는 **VLA 쪽 경계만** 본다.

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

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex2.c -o x2c ; ./x2c (cc exit=0 · run exit=0) =====
sizeof fixed[f()]            =   4   f() 호출 안 됐다
sizeof vla[f()]              =   4   f() 호출 안 됐다
sizeof vla                   =  16   f() 호출 안 됐다
sizeof(int[3])               =  12   f() 호출 안 됐다
sizeof(int[f()])             =  20   f() 호출 ★ 됐다
sizeof(int[f()?3:3])         =  12   f() 호출 ★ 됐다

f() 는 모두 2 번 불렸다
```

| 식 | 값 | `f()` 가 불렸나 | 왜 |
|---|---|---|---|
| `sizeof fixed[f()]` | **4** | 안 불림 | 피연산자 타입이 `int` — 가변 길이 배열이 아니다 |
| ★ `sizeof vla[f()]` | **4** | ★ **안 불림** | **`vla` 가 VLA 여도 `vla[f()]` 의 타입은 `int`** 다 |
| `sizeof vla` | **16** | 안 불림 | 크기를 실행 시점에 잰다. ★ **이 줄은 「평가되나」를 증명하지 못한다** — 부작용이 없다 |
| `sizeof(int[3])` | **12** | 안 불림 | 크기가 상수식이라 **보통 배열 타입**이다 |
| `sizeof(int[f()])` | **20** | ★ **불림** | 타입 자체가 가변 길이 배열이다. `f()` 가 5 를 돌려줘 `5 × 4` |
| ★ `sizeof(int[f()?3:3])` | **12** | ★ **불림** | **값이 늘 3 인데도** 상수식이 아니라 **가변 길이 배열 타입**이다 |

```text
   sizeof <식 또는 (타입)>
        │
        └─ 갈림길은 하나 : ★ "피연산자의 타입" 이 가변 길이 배열인가?
             │
             ├─ 아니다 ──> 피연산자는 ★ 평가되지 않는다
             │                sizeof fixed[f()]      ->  4    f() ★ 안 불린다
             │                sizeof vla[f()]        ->  4    f() ★ 안 불린다
             │                sizeof(int[3])         -> 12
             │
             └─ 그렇다 ──> 피연산자는 ★ 평가된다
                              sizeof vla             -> 16
                              sizeof(int[f()])       -> 20    f() ★ 불린다
                              sizeof(int[f()?3:3])   -> 12    f() ★ 불린다

   f() 는 프로그램 전체에서 ★ 두 번 불렸다 — 위 두 자리뿐이다.
```

그림 해설 (한 단계씩):

- ★★★ **함정은 `sizeof vla[f()]` 다.** `vla` 는 분명히 VLA 인데 **`f()` 가 안 불린다.**\
  갈림길은 **「변수가 VLA 냐」가 아니라 「`sizeof` 가 받는 식의 타입이 가변 길이 배열이냐」다**.
- ★★ **`sizeof(int[f()?3:3])` 은 부른다.** 기준은 **「값이 상수냐」가 아니라 「상수식이냐」다** — 호출이 들어간 순간 상수식이 아니고, 그러면 그 타입이 **가변 길이 배열**이 된다. **크기가 12 로 고정인데도** 그렇다.
- ★ **gcc 와 clang 의 출력이 한 글자도 같다** — **표준이 정한 것**이라 그렇다.
- ★★ **진단은 0건**이다. **호출 횟수를 직접 세는 것** 말고 이 사실을 볼 방법이 없다.

비용 — VLA 가 섞인 코드에서는 **`sizeof` 안에 부작용을 절대 넣지 않는 것**이 유일한 방어다.

### (3) ★★★ 본체 — 조건부 표준: C99 필수 → C11 선택 → C23

**언제 쓰나** — 「VLA 를 써도 되나」를 결정할 때. ★ **이 주제의 무게중심이 여기다.**\
★★ **두 가지를 반드시 갈라 적어야 한다** — 「**표준 문서가 그렇게 정했다**」와 「**이 구현에서 재 보니 이렇더라**」.

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

먼저 도구에게 물어본다 — **`-Wvla` 를 직접 켜면** 이렇게 말한다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wvla ex3.c -o /dev/null (cc exit=0) =====
ex3.c: In function ‘main’:
ex3.c:15:5: warning: ISO C90 forbids variable length array ‘vla’ [-Wvla]
   15 |     int vla[n];
      |     ^~~
```

- ★★ **에러가 아니라 경고**다 — **`cc exit=0`**, 실행 파일이 나온다.
- ★ **`-std=c17` 로 컴파일했는데 문구는 「`ISO C90 forbids`」다**. gcc 의 `-Wvla` 는 **어느 `-std=` 에서든 같은 문장**을 쓴다 — **진단 문구를 「지금 고른 표준」으로 읽으면 안 된다.**
- ★★ **이 경고는 `-Wall -Wextra -pedantic` 에 안 들어 있다.** **`-Wvla` 를 손으로 켜야** 나온다.

그러면 `-std=` 를 바꾸면 어떻게 되나. **여덟 벌을 찍었다** — 아래는 그중 **네 판**이고, **나머지 판도 매크로 칸이 한 글자도 같았다**(표).

```text
===== gcc -std=c89 -Wall -Wextra -pedantic ex3.c -o x3_89 ; ./x3_89 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 정의 안 됨 (C89)
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
===== clang -std=c23 -Wall -Wextra -pedantic ex3.c -o x3c_23 ; ./x3c_23 (cc exit=0 · run exit=0) =====
__STDC_VERSION__   = 202311L
__STDC_NO_VLA__    = ★ 정의 안 됨 -> VLA 가 있다
실제로 int vla[n] 이 되나 : sizeof = 16 · vla[0] = 42
```

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

> ★ 표의 아홉 판 중 나머지 다섯(gcc `c99`·`c11`·`c17` · clang `c89`·`c17`)의 출력 블록은 **정답 파일**에 있다.

```text
   표준 문서 쪽 사실                          이 머신에서 잰 것
   ─────────────────────────────────         ─────────────────────────────────
   C99 : VLA ★ 필수                          __STDC_NO_VLA__ 가 여덟 벌 전부
   C11 : VLA ★ 선택                            ★ 정의 안 됨
         안 주는 구현은 __STDC_NO_VLA__ 정의
                                             -std=c89 -pedantic 에서도
   C23 : 선택의 ★ 범위가 좁아졌다                ★ 컴파일되고 ★ 실행된다
         가변 수정 타입은 다시 필수,               (cc exit=0 · run exit=0 · sizeof 16)
         자동 저장 기간의 VLA 객체만 선택
                                             경고는 ★ -Wvla 를 손으로 켜야 나온다

   ★ 왼쪽은 "무엇이 옳은가", 오른쪽은 "지금 무엇이 되는가" ─ 둘은 다른 이야기다.
```

그림 해설 (한 단계씩):

- ★★★ **`__STDC_NO_VLA__` 는 여덟 벌 어디에서도 정의되지 않았다.** **이 구현들은 VLA 를 뺀 적이 없다.**
- ★★ **그 출력이 말하는 것은 「이 두 컴파일러에는 있다」뿐**이다. **「내 코드가 이식 가능하다」는 한 글자도 말하지 않는다** — 안 주는 구현을 **이 머신에서는 만날 수 없다.**
- ★★ **`-std=c89 -pedantic` 이 VLA 를 막지 않는다**(`cc exit=0 · run exit=0` · `sizeof` 16). ★ **`-std=` 는 「강제」가 아니라 「기본값 선택」이다**.
- ★★ **gcc 13 에는 `-std=c23` 이 없다** — 「`did you mean -std=c2x`」와 함께 `cc exit=1` 이다. ★ **경고 0건인데 `exit=1`** 이라 **경고만 세면 「통과」로 기록된다.**
- ★★ **같은 「C23」인데 선 지점이 다르다** — gcc `c2x` 는 **`202000L`**, clang `c23` 은 **`202311L`**. ★ **그 매크로는 「어느 표준이냐」가 아니라 「어느 작업 판을 구현했나」를 말한다.**

비용 — **「쓸 수 있다」와 「써도 된다」가 다르다.** 이식성을 원하면 **`-Wvla` 로 스스로 막는 쪽**이 유일하게 확실하다.

### (4) ★★ 스택 소진 — 경계를 찾아 던지면, **진단이 한 줄도 없다**

**언제 쓰나** — 「`malloc` 을 안 썼으니 실패할 일이 없다」고 생각할 때. 자리가 얼마나 있는지부터 묻고 **경계 양쪽으로 던진다.**

```text
===== ulimit -s (exit=0) =====
8192
```

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
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 100000000 (cc exit=0 · run exit=139) =====
요청 100000000 바이트
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

> ★ **대조할 것은 숫자가 아니라 성질이다.** ASan 의 주소·`pc`/`bp`/`sp`·PID·`BuildId` 는 실행마다 바뀐다.\
> 근거는 **`stack-overflow` 가 `touch ex4.c:5` 에서 났다**는 것, **종료 코드가 `139` ↔ `1` 로 갈린다**는 것, 그리고 **부등호**다.

```text
   ulimit -s = 8192 KB = 8,388,608 바이트

   요청 8,000,000 바이트                요청 9,000,000 바이트
   +-------------------------+         +-------------------------+
   | 잡은 자리  8,000,000    |         | 잡은 자리  9,000,000 ★넘침|
   +-------------------------+         +-------------------------+
   출력 : "잡았다 (1 2)"                출력 : ★ 없다
          "정상 종료"                          (요청 줄에서 끊긴다)
   run exit = 0                         run exit = ★ 139
   진단   : 없다                         진단   : ★ 한 줄도 없다
```

그림 해설 (한 단계씩):

- ★★★ **경계가 부등호로 잡힌다** — **8,000,000 통과 / 9,000,000 죽음.** 8,000,000 판은 **양 끝을 실제로 써서** 「잡기만 한 것」이 아님을 보였다.
- ★★★ **죽는 판에 진단이 한 줄도 없다.** 컴파일 경고 0건, 실행 중 출력 0줄, 남는 것은 **`run exit=139`**(= 128 + 11) 하나다.
- ★★ **ASan 만 이름을 붙인다** — `stack-overflow` 이고 **`touch ex4.c:5`**, 즉 **VLA 를 잡는 그 줄**이다. ★ **종료 코드도 `1` 로 바뀐다.**
- ★ **100,000,000 판도 맨몸에서는 `139` 하나**다 — **12배를 넘겨도 출력이 더 나오지 않는다.**
- ★★ **`-Wvla` 는 이 사고를 못 막는다.** 「VLA 다」만 말하고 **「이 `n` 이 크다」는 안 본다** — `n` 은 **실행 시점 값**이다.

비용 — **실패를 받을 방법이 없다.** `malloc` 은 **`NULL` 로 「못 준다」고 말하는데** VLA 에는 **그런 반환값이 없다.**\
★ **그래서 크기를 못 믿으면 VLA 가 아니라 `malloc`** 이다([목록의 **37번 주제**](../37-malloc-calloc-realloc-free/)).

### (5) ★ 크기가 0 이거나 음수면 — UBSan 은 말하는데 **프로그램은 「정상 종료」한다**

**언제 쓰나** — 「`n` 을 검사했다」고 할 때. **같은 `ex4.c` 를 인자만 바꿔 던진다.**

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

```text
   n = 0 을 던진 판

   UBSan 이 말한 것                              프로그램이 한 것
   ───────────────────────────────────          ─────────────────────────
   "variable length array bound evaluates       "잡았다" 를 찍고
    to non-positive value 0"                    "정상 종료" 를 찍고
   + index 0 / index -1 out of bounds (네 줄)    ★ run exit = 0 으로 끝난다

   ★ 진단은 다섯 줄인데 ─ 종료 코드만 보는 자동화는 ★ 통과로 읽는다.
```

그림 해설 (한 단계씩):

- ★★ **`n` 이 0 도 UB** 다 — 「음수만 조심하면 된다」가 아니다.
- ★★★ **말하고도 `run exit=0` 으로 정상 종료한다.** UBSan 은 기본에서 **보고하고 계속 간다** — 죽이려면 `-fno-sanitize-recover=all` 을 따로 켜야 하고 ★ **이 문서는 그 판을 안 던졌다.**
- ★ **`0` 판은 다섯 줄, `-1` 판은 한 줄**이다. 0 쪽은 **뒤따르는 배열 접근까지** 걸렸다 — **같은 부류의 UB 인데 드러나는 양이 다르다.**
- ★★ **UBSan 은 스택 소진을 못 본다.** (4)를 잡은 것은 **ASan** 이다 — **두 도구가 서로 다른 것을 본다.**
- ★ 두 판이 찍은 원소 값은 **UB 의 산물이라 근거가 못 된다.** 근거는 **진단 본문**과 **`run exit=0`** 둘이다.

비용 — **`n > 0` 과 상한을 코드가 직접 확인하는 것** 말고 방법이 없다.

### (6) VLA 매개변수 — 1차원은 포인터, **2차원은 안쪽 보폭이 실행 시점 값**

**언제 쓰나** — 열 수가 실행 시간에 정해지는 2차원 배열을 함수에 넘길 때.\
★ **감쇠와 매개변수 재작성 자체는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본**이고 여기서는 **VLA 쪽만** 본다.

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

```text
   1차원 VLA 매개변수                     2차원 VLA 매개변수
   int a[n]                              int a[rows][cols]
   +-------------+                       +-------------+
   | 포인터      |                       | 포인터      |
   +-------------+                       +-------------+
   sizeof a    = 8                       sizeof a    = 8
   길이 n 은 ★ 타입에 안 남는다            sizeof a[0] = ★ 12  (실행 시점 cols=3)

   ★ 바깥 한 겹만 잃는 것은 16·17번과 같다.
     다른 것은 ─ 17번에서 남은 안쪽 보폭은 ★ 컴파일 시점 값이고,
                여기서 남은 안쪽 보폭은 ★ 실행 시점 값이다.
```

그림 해설 (한 단계씩):

- **1차원 `int a[n]` 은 포인터로 재작성**된다 — **`sizeof a` 가 8**. [16번 형제](../16-array-pointer-decay-and-function-parameters/)의 `int a[10]` 과 **똑같은 결말**이다.
- ★★★ **2차원은 다르다** — `sizeof a` 는 8 인데 **`sizeof a[0]` 이 12** 다. **`cols = 3` 이라는 실행 시점 값**이 타입에 들어 있다.\
  ★ **[목록의 17번 주제](../17-multidimensional-arrays-and-pointer-types/)와 같은 12 인데 정해진 시점이 다르다.**
- ★ **두 컴파일러가 같은 자리를 다른 이름으로 잡는다** — `sizeof` 쪽 둘은 **양쪽 다 `-Wsizeof-array-argument`** 인데,\
  **`int a[*]` 와 `int a[n]` 의 불일치**는 **gcc 가 `-Wvla-parameter`**, **clang 이 `-Warray-parameter`** 다. ★ **이름으로 검색하면 한쪽만 나온다.**
- ★ **`[*]` 는 프로토타입 전용 표기**다. 정의에서는 이름을 적어야 하고, 어긋나면 위 경고가 난다(**양쪽 다 `cc exit=0`**).

비용 — **차원마다 길이를 따로 넘겨야 한다.** 그 대가로 **`a[i][j]` 표기를 그대로 쓸 수 있다.**

### (7) 저장 기간이 **자동으로 고정된다** — 다섯 자리가 전부 에러

**언제 쓰나** — 「크기를 실행 시점에 정하는 배열을 전역에 하나 두자」고 생각했을 때.

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

```text
   VLA 를 놓아 보려 한 다섯 자리                          gcc 가 한 말

   (가) 파일 스코프    static int file_vla[n];            variably modified ... at file scope
   (나) 구조체 멤버    struct S { int a[n]; };            variably modified ... at file scope
   (다) 함수 안 static static int fn_vla[m];              storage size ... isn't constant
   (라) 초기자         int init_vla[m] = {1,2,3};         may not be initialized
                                                          (except with an empty initializer)
   (마) extern         extern int ext_vla[m];             must have no linkage + storage size

   ★ 다섯 다 error ─ cc exit=1.

   +------------------------------------------+
   | 블록 안에서 선언한 ★ 자동 저장 기간 객체    |   <- VLA 가 놓일 수 있는 유일한 자리
   +------------------------------------------+
```

그림 해설 (한 단계씩):

- ★★ **다섯 자리가 전부 에러**이고 **한 번의 컴파일에서 다 나온다**(`cc exit=1`). **경고가 아니다.**
- ★ **(가)와 (나)의 문구가 같다** — **구조체 멤버 선언도 그 위치에서 평가돼야** 하므로 **파일 스코프로 불린다.**
- ★★ **(다) 함수 안의 `static` 도 안 된다** — 자리는 함수 안인데 **저장 기간이 정적**이라 **프로그램 시작 전에 크기가 정해져 있어야** 한다.
- ★ **(라)** 의 문구가 「**빈 초기자는 예외**」를 덧붙인다 — ★ **그 판은 이 문서가 던지지 않았다.** **(마)** 는 이유가 **둘**로 나온다.
- ★★★ 한 줄로 — **VLA 의 저장 기간은 고를 수 있는 것이 아니라 자동으로 고정된다**(고르는 이야기는 [목록의 **28번 주제**](../28-choosing-among-four-storage-durations/)).

비용 — **수명이 블록에 묶인다.** 함수 밖으로 내보내려면 **`malloc`** 이다.

### (8) `goto` 가 VLA 스코프를 못 넘는다 — **[12번 형제](../12-control-flow-and-switch/)가 정본**

**언제 쓰나** — `goto cleanup` 관용구([13번 형제](../13-goto-cleanup-idiom/))를 VLA 가 있는 함수에 쓸 때. ★ 여기서는 **결론과 문구 차이만**.

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

```text
   int n = 4;
   goto skip;     ──┐   ★ 못 뛴다 ─ 컴파일 에러 · cc exit=1
   int vla[n];      │   뛰면 "자리를 잡는 일" 을 건너뛴 채
   vla[0] = 1;      │   그 자리를 쓰는 코드 안으로 들어가게 된다
 skip:            <─┘
```

그림 해설 (한 단계씩):

- ★★ **경고가 아니라 에러**이고 `cc exit=1` 이다. ★ [12번 형제](../12-control-flow-and-switch/)에서는 **`switch` 도 같은 규칙에 걸린다**는 것까지 본다.
- ★ **두 컴파일러가 다른 각도로 말한다** — **gcc 는 타입으로**(`variably modified type`), **clang 은 이유로**(`bypasses initialization of variable length array`). ★ **clang 쪽이 「무엇을 건너뛰는지」를 알려 준다.**
- ★ gcc 는 에러 뒤에 **경고까지** 낸다 — **에러가 난 컴파일에서도 경고는 나온다.**
- ★ **`goto cleanup` 과 충돌하는 자리**다 — 정리 라벨이 VLA 선언보다 뒤면 **그 앞에서 뛰어넘는 `goto` 가 전부 막힌다.**

비용 — **VLA 를 쓰면 함수 안의 제어 흐름이 제약을 받는다.** 대처는 **VLA 를 더 안쪽 블록으로 미는 것**이다.

## 문법 — 형태와 규칙

### 형태 — VLA 가 나오는 네 자리

```text
  ① 블록 안의 객체        int n = 그때의 값;
                          int vla[n];              /* ★ 자동 저장 기간만 */

  ② 함수 매개변수 (1차원)  int sum1(int n, int a[n]);        /* ≡ int *a */

  ③ 함수 매개변수 (2차원)  int sum2(int r, int c, int a[r][c]);
                                                   /* ≡ int (*a)[c] — 안쪽이 실행 시점 값 */

  ④ 프로토타입의 별표      int sum3(int n, int a[*]);
                          int sum3(int n, int a[n]) { … }   /* 정의에서는 이름으로 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
  static int g[n];                  /* ★ error — 정적 저장 기간 (표준) */
  struct S { int a[n]; };           /* ★ error — 구조체 멤버 (표준) */
  void f(void) { static int a[m]; } /* ★ error — 함수 안 static (표준) */
  int a[m] = {1, 2, 3};             /* ★ error — 초기자 (표준) */
  extern int a[m];                  /* ★ error — 링크가 있다 (표준) */
  goto skip; int vla[n]; skip: ;    /* ★ error — 스코프 진입 (표준 · 12번 형제) */

  char vla[n];  /* n <= 0 */        /* ★ UB — 컴파일은 된다. UBSan 만 말한다 */
  char vla[n];  /* n 이 아주 큼 */   /* ★ UB — 진단 0줄. ASan 만 말한다 */

  sizeof vla[f()]                   /* 함정 — f() 가 ★ 안 불린다 (표준) */
  sizeof(int[f() ? 3 : 3])          /* 함정 — f() 가 ★ 불린다 (표준) */
```

### 규칙 불릿

- ★★ **VLA 는 C99 부터**다. **C99 필수 → C11 선택**(`__STDC_NO_VLA__`) **→ C23 에서 선택 범위 축소.**
- ★★ **저장 기간은 자동으로 고정**된다. 정적·구조체 멤버·`extern`·초기자는 **전부 에러**다.
- ★★ **`sizeof` 가 실행 시점에 계산**된다. **값은 배열을 만든 시점의 크기**이고 결과 타입은 여전히 **`size_t`** 다.
- ★★★ **`sizeof` 의 피연산자가 평가되는 기준은 「그 식의 타입이 가변 길이 배열이냐」다**.
- ★ **크기가 0 이하면 UB** 다. 컴파일은 된다. **스택 소진도 UB** 이고 **진단이 없다.**
- ★ **매개변수의 `[n]` 은 1차원에서 버려진다.** **2차원은 안쪽 한 겹이 남고 그 값이 실행 시점**이다.
- ★ **`[*]` 는 프로토타입 전용 표기**이고, **`goto`·`switch` 는 VLA 스코프 안으로 못 뛴다**(에러).
- ★ **`-std=` 로는 막히지 않는다.** 막으려면 **`-Wvla`** 를 켠다.

## 어디서 틀리나

### 1. ★★★ 「`-std=c89` 로 컴파일했으니 VLA 는 안 쓰였겠지」

- **쓰였다.** `-std=c89 -pedantic` 에서 **컴파일도 실행도 됐고**(`cc exit=0 · run exit=0`) `sizeof` 가 **16** 으로 찍혔다.
- ★ **`-std=` 는 「기본값 선택」이지 「강제」가 아니다.** 막으려면 **`-Wvla`** 이고, 켜도 **경고**다(`cc exit=0`).

### 2. ★★★ 「`__STDC_NO_VLA__` 가 없으니 어디서나 쓸 수 있다」

- 그 출력이 말하는 것은 「**gcc 13 과 clang 18 에는 있다**」뿐이다. **없는 구현을 이 머신에서는 만날 수 없다.**
- ★ **부재는 이식성의 증거가 아니다.** 이식성을 걸어야 하면 **`#ifdef` 로 대체 경로**를 두거나 **아예 안 쓴다.**

### 3. ★★★ 「`malloc` 을 안 썼으니 할당 실패가 없다」

- **스택 소진이 그 자리를 대신한다.** 9,000,000 바이트에서 **`run exit=139`**, 진단 **0줄**.
- ★ **`malloc` 은 `NULL` 로 말하는데 VLA 에는 그런 반환값이 없다.** 이름을 붙이는 것은 **ASan 뿐**이다.

### 4. ★★ 「`n` 이 음수만 아니면 된다」

- **0 도 UB** 다. UBSan 이 **`non-positive value 0`** 이라고 말한다.
- ★★ **말하고도 `run exit=0`** 이다 — **종료 코드만 보면 통과다.** 검사는 **`n > 0` 과 상한 둘 다**여야 한다.

### 5. ★★★ 「VLA 를 썼으니 `sizeof` 안의 호출도 평가되겠지」

- **`sizeof vla[f()]` 는 `f()` 를 안 부른다** — 피연산자의 타입이 **`int`** 이기 때문이다.
- ★ 반대로 **`sizeof(int[f()?3:3])` 은 부른다** — **값이 늘 3 인데도** 상수식이 아니라서다. ★ **진단 0건**이다.

### 6. ★★ 「전역에 VLA 를 하나 두고 재사용하자」

- **에러**다 — 다섯 자리 전부. **저장 기간을 고를 수 없다.**
- 함수 밖으로 내보내야 하면 **`malloc`**([목록의 **37번 주제**](../37-malloc-calloc-realloc-free/)), 구조체에 붙이려면 **유연 배열 멤버**([목록의 **26번 주제**](../26-flexible-array-members/))다.

### 7. ★★ 「VLA 매개변수 `int a[n]` 이면 `sizeof a` 가 `n*4` 겠지」

- **8** 이다 — 포인터로 재작성된다. ★ **2차원만 다르다** — `sizeof a[0]` 이 **12** 이고 그것은 **실행 시점의 `cols`** 다.
- ★ **`-Wsizeof-array-argument` 가 잡아 준다**(양쪽 다).

### 8. ★ 「`goto cleanup` 으로 정리하면 되지」

- **VLA 스코프 안으로는 못 뛴다** — **에러**이고 `cc exit=1` 이다([12번 형제](../12-control-flow-and-switch/)가 정본).
- ★ VLA 선언을 **더 안쪽 블록으로** 밀거나, 정리 대상이 있는 함수에서는 **VLA 를 쓰지 않는다.**

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★ **이 주제는 「조건부 표준」이 본체**다 — [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 그 칸을 「해당 없음」으로 비운 자리에 **이 주제의 무게가 전부 들어 있다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **`sizeof` 의 실행 시점 계산**(16·36·68) · **피연산자 평가 규칙** · **저장 기간이 자동으로 고정**되는 것 · **`goto`·`switch` 의 스코프 진입 금지** · **매개변수 재작성** · `[*]` 는 프로토타입 전용 | gcc·clang 출력이 한 글자도 같음 · 에러 여섯 자리 `cc exit=1` · `f()` 호출 **2회** | ★★ **`sizeof vla[f()]` 가 평가 안 되는 것 — 진단 0건.** 어느 플래그도 말하지 않는다 |
| ★★★ **조건부 표준** | 구현이 「안 준다」고 선언할 수 있다 | ★★ **본체** — **VLA 자체.** **C99 필수 → C11 선택**(`__STDC_NO_VLA__`) **→ C23 에서 선택 범위 축소**(가변 수정 타입은 필수, 자동 저장 기간의 VLA 객체만 선택) | ★ **재 본 것** — 매크로가 **여덟 벌 전부 정의 안 됨** · `-std=c89 -pedantic` 에서도 `cc exit=0 · run exit=0` · gcc 13 에 **`-std=c23` 없음**(`cc exit=1`) · gcc `c2x` `202000L` ↔ clang `c23` `202311L` | ★★★ **`-std=` 가 막아 주지 않는다.** `-Wvla` 를 **손으로 켜야** 말하고 켜도 **경고**다. ★ **매크로의 부재는 이식성을 한 글자도 보장하지 않는다** |
| **구현 정의** | 문서화 의무가 있다 | `sizeof(int)`=4 라서 **16·36·68·12·20** 인 것 · VLA 의 정렬 · **큰 `n` 에서 실패하는 방식**(여기서는 SIGSEGV) | `sizeof` 출력 · `run exit=139` | ★ **정렬은 이 문서가 안 쟀다** |
| **미명시** | 몇 가지 중 하나 | ★ **VLA 를 어디에 잡는가** — 표준은 **저장 기간만** 정하고 「스택」이라는 말을 쓰지 않는다. **자리가 얼마나 있는가**(`ulimit -s` 8192 KB)도 **표준이 아니라 환경**이다 | `&vla` 가 `&fixed` 보다 **낮은 주소**였다 — ★ **관찰이지 보장이 아니다** · `ulimit -s` 출력 | ★★ **주소는 흔들리는 칸**이라 근거로 못 쓴다 |
| **UB** | 아무 일이나 | ★★ **크기가 0 이하** · ★★ **자리를 넘겨 잡는 것**(스택 소진) | UBSan `non-positive value 0` / `-1` · ASan `stack-overflow` at `touch ex4.c:5` · `run exit=139` ↔ `1` | ★★★ **맨몸에서는 진단이 한 줄도 없다.** ★★ **UBSan 은 말하고도 `run exit=0`** 으로 끝난다 |

### 「도구가 못 보는 것」을 층마다 — 한 줄씩

| 층 | 무엇이 안 보이나 | 무엇을 켜야 보이나 |
|---|---|---|
| **표준**(`sizeof` 평가) | ★ `sizeof vla[f()]` 가 **평가 안 되는 것** — 세 플래그 전부 **0건** | ★ **없다.** 호출 횟수를 **직접 세는 것**뿐 |
| **표준**(저장 기간·`goto`) | — **전부 에러로 잡힌다**(`cc exit=1`) | 기본 플래그로 충분하다 |
| ★★★ **조건부 표준** | ★ **`-std=c89 -pedantic` 조차 안 막는다** · ★ **매크로의 부재는 이식성을 안 말한다** | **`-Wvla`**(경고) · 더 세게는 `-Werror=vla` — ★ **뒤쪽은 안 던졌다** |
| **구현 정의**(자리 크기) | ★★★ **스택 소진에 진단이 한 줄도 없다** — 컴파일 0건, 실행 중 0줄, 남는 것은 `run exit=139` 하나 | **ASan**(`stack-overflow` · `run exit=1`) — ★ **이름을 붙이는 유일한 도구** |
| **미명시**(어디에 잡히나) | ★ 볼 수 있는 것이 **주소뿐**인데 그것은 **흔들리는 칸**이다 | ★ **없다.** 관찰로만 남긴다 |
| **UB**(0 이하) | ★★ **UBSan 이 말해도 `run exit=0`** — 종료 코드만 보면 **통과**다 | **UBSan** + ★ **죽이는 옵션을 따로** |
| **UB**(너무 큼) | ★★ **`-Wvla` 도 못 본다** — 「크다」는 **`n` 이 실행 시점 값이라** 볼 수 없다 | **ASan** · 실행 전 **`n` 상한 검사** |

- ★★★ **가장 위험한 칸은 「스택 소진」이다** — **컴파일러도 sanitizer 도 기본에서는 한마디도 안 한다.**
- ★★ **두 번째는 조건부 표준**이다 — **`-std=` 를 믿으면 안 되고**, `-Wvla` 를 켜지 않으면 **코드에 흔적이 안 남는다.**
- ★ **표준 칸의 사고는 대부분 컴파일이 막는다**(저장 기간 다섯 + `goto` 하나). **다만 `sizeof` 평가 규칙만은 진단이 0건**이다.

### 이 주제의 네 번째 창 — **종료 코드**와 **`f()` 호출 횟수**

- **컴파일 진단**은 스택 소진을 아예 못 보고, **실행 출력**은 0 을 던진 판에서 **「정상 종료」를 찍는다.**
- ★★★ **종료 코드** — `0`(정상·UBSan 이 말해도 0) · `1`(ASan) · `139`(맨몸 SIGSEGV) · `1`(컴파일 에러). **출력이 같아 보여도 갈린다.**
- ★★ **부작용 횟수** — **`f()` 가 두 번** 불렸다는 숫자 하나가 **여섯 식의 평가 여부를 전부 판정**한다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| **작고 상한이 확실한** 임시 버퍼 | `int buf[n]`(상한 검사 뒤) | 상한 없이 `int buf[n]` |
| 크기를 **못 믿는** 버퍼 | `malloc` — ★ **실패를 `NULL` 로 받는다** | VLA — ★ **실패를 받을 방법이 없다** |
| 함수 밖으로 **돌려줄** 배열 | `malloc` | VLA — 저장 기간이 자동으로 고정 |
| 전역·구조체 멤버 | 고정 크기 또는 **유연 배열 멤버**([목록의 **26번 주제**](../26-flexible-array-members/)) | VLA — ★ 컴파일 에러 |
| 실행 시간에 정해지는 **2차원** 접근 | `int a[rows][cols]` 매개변수 | `int **` — [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
| **이식성**을 걸어야 할 때 | `#ifdef __STDC_NO_VLA__` 대체 경로 | ★ 「매크로가 없더라」를 근거로 쓰기 |
| VLA 를 **금지**하고 싶을 때 | **`-Wvla`**(필요하면 `-Werror=vla`) | `-std=c89` — ★ **안 막힌다** |
| 경계를 넘겼는지 확인 | **ASan** | 경고만 보고 만족 — ★ **0건이다** |
| `n <= 0` 을 확인 | **코드에서 직접** + UBSan | 종료 코드만 보기 — ★ **0 이 나온다** |

판단 규칙 두 줄.

- ★★ **VLA 는 「상한이 확실한 작은 버퍼」에만 쓴다.** 상한을 말할 수 없으면 **그것은 `malloc` 자리**다.
- ★★ **쓰기로 했으면 `-Wvla` 를 켜 두고 예외만 허용한다** — 켜 놓지 않으면 **들어온 것조차 모른다.**

## 핵심 문장

- ★★★ **`sizeof` 가 상수가 아닌 자리는 VLA 하나**다 — 같은 함수를 세 `n` 으로 부르면 **16 · 36 · 68** 이다.\
  결과 타입은 여전히 **`size_t`** — 바뀌는 것은 **언제 정해지느냐**뿐이다.
- ★★★ **`sizeof` 의 피연산자가 평가되는 기준은 「그 식의 타입이 가변 길이 배열이냐」다**.\
  **`sizeof vla[f()]` 는 `f()` 를 안 부르고**(타입이 `int`), **`sizeof(int[f()?3:3])` 은 부른다**(값이 늘 3 인데도). ★ **`f()` 는 모두 두 번** 불렸다.
- ★★★ **「표준이 정한 것」과 「이 구현에서 잰 것」은 다른 이야기다.**\
  표준 쪽 — **C99 필수 → C11 선택 → C23 에서 선택 범위 축소.** 잰 것 쪽 — **매크로는 여덟 벌 어디에도 없었고** `-std=c89 -pedantic` 에서도 **컴파일·실행이 됐다.**
- ★★★ **`-std=` 는 강제가 아니라 기본값 선택**이다. 막는 것은 **`-Wvla`** 이고 켜도 **경고**(`cc exit=0`)다.\
  ★ 그 문구는 `-std=c17` 에서도 「**`ISO C90 forbids`**」다 — **문구를 현재 표준으로 읽으면 안 된다.**
- ★★ **gcc 13 에는 `-std=c23` 이 없다**(`cc exit=1`). gcc `c2x` 는 **`202000L`**, clang `c23` 은 **`202311L`** — **같은 이름으로 다른 지점에 서 있다.**
- ★★★ **스택 소진에 진단이 한 줄도 없다.** 8,000,000 은 통과하고 **9,000,000 은 `run exit=139`** 인데 **컴파일 경고 0건 · 실행 중 0줄**이다.\
  **이름을 붙여 주는 것은 ASan 뿐**(`stack-overflow` · `run exit=1`)이다.
- ★★ **크기가 0 이어도 UB** 이고, **UBSan 이 말하고도 `run exit=0`** 으로 끝난다 — ★ **종료 코드만 보는 자동화는 통과로 읽는다.**
- ★★ **저장 기간은 고를 수 없고 자동으로 고정된다** — 다섯 자리가 **전부 에러**이고 한 번의 컴파일에서 다 나온다.
- ★★ **VLA 매개변수는 1차원이면 포인터**(`sizeof a` = 8)**, 2차원이면 안쪽 한 겹이 남는다**(`sizeof a[0]` = **12**).\
  ★ **[목록의 17번 주제](../17-multidimensional-arrays-and-pointer-types/)와 같은 12 인데, 거기서는 컴파일 시점 값이고 여기서는 실행 시점 값**이다.
- ★ **`goto`·`switch` 는 VLA 스코프 안으로 못 뛴다**(에러) — **정본은 [12번 형제](../12-control-flow-and-switch/)다**.

## 관련 자료

- [`../README.md`](../README.md) — 주제 목록(이 주제는 18번) · ★ **이 문서의 표준 쪽 기준 소스 선언이 거기 있다**
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — ★★ **`sizeof` 일반 규칙의 정본.** 그쪽은 「평가하지 않는다」까지, 여기는 「**그 예외가 어디까지인가**」부터
- [`12-control-flow-and-switch/`](../12-control-flow-and-switch/) — ★★ **`goto`·`switch` 의 VLA 스코프 진입 금지의 정본.** 여기는 **결론과 문구 차이**까지
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — `goto cleanup` 관용구. VLA 와 충돌하는 자리를 거기서도 한 번 던졌다
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — ★★ **감쇠와 매개변수 재작성의 정본.** 그쪽의 「조건부 표준」 칸은 **비어 있다** — 층 분포가 정반대다
- [`15-pointer-arithmetic-and-indexing/`](../15-pointer-arithmetic-and-indexing/) · [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — 보폭과 선언 읽기의 정본
- [목록의 **17번 주제**](../17-multidimensional-arrays-and-pointer-types/) (다차원 배열) — ★ **안쪽 보폭이 컴파일 시점인 판.** 여기는 **실행 시점인 판**
- [목록의 **26번 주제**](../26-flexible-array-members/) (유연 배열 멤버) · [목록의 **28번 주제**](../28-choosing-among-four-storage-durations/) (저장 기간 4종) · [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/) (`malloc` 계열)
- 목록의 **56번 주제** (공간 위반) — 잡은 자리를 넘어 접근했을 때

## 용어 풀이

- **VLA(variable length array · 가변 길이 배열)** — 크기를 실행 시점 값으로 정하는 배열. 예: `n` 이 9 면 `sizeof vla` 가 36 이다.
- **가변 수정 타입(variably modified type)** — 크기에 **실행 시점 값이 들어간 타입**.\
  예: `int (*p)[n]`. ★ **`goto` 를 막는 gcc 진단이 이 말을 쓴다.**
- **조건부 기능(conditional feature)** — 표준에 있지만 구현이 「안 준다」고 선언할 수 있는 기능. 예: VLA 는 C11 부터 그렇다.
- **`__STDC_NO_VLA__`** — 「이 구현은 VLA 객체를 안 준다」는 선언용 매크로.\
  ★ 예: 여덟 벌에서 **전부 정의되지 않았다** — **「있다」는 뜻이지 「이식된다」는 뜻이 아니다.**
- **`__STDC_VERSION__`** — 구현이 「내가 구현한 표준 판」이라고 말하는 매크로.\
  예: gcc `-std=c2x` 는 `202000L`, clang `-std=c23` 은 `202311L` — **같은 이름인데 값이 다르다.**
- **자동 저장 기간(automatic storage duration)** — 블록에 들어갈 때 생기고 나갈 때 사라지는 수명.\
  ★ 예: VLA 는 **이것 말고 다른 저장 기간을 고를 수 없다.**
- **스택 소진(stack overflow)** — 자동 저장 기간 객체를 놓을 자리가 모자라 넘치는 것.\
  예: 8192 KB 한계에서 9,000,000 바이트를 잡자 **`run exit=139`** 로 죽었다 — **진단은 0줄이다.**
- **`-Wvla`** — VLA 선언을 경고하는 플래그. ★ **`-Wall -Wextra -pedantic` 에 안 들어 있다.**\
  예: `-std=c17` 에서 켜도 문구는 「`ISO C90 forbids variable length array`」다.
- **`-Wvla-parameter`(gcc) · `-Warray-parameter`(clang)** — 매개변수의 배열 크기 표기가 선언끼리 어긋난 것을 경고.\
  ★ 예: `int a[*]` 로 선언하고 `int a[n]` 으로 정의한 자리 — **같은 사실에 두 이름이 붙어 있다.**
- **`[*]`(별표 표기)** — 프로토타입에서 「여기 크기가 실행 시점 값이다」를 이름 없이 적는 표기. 예: `int sum3(int n, int a[*]);`
- **ASan(AddressSanitizer)** — 메모리 접근 위반을 실행 중에 잡는 도구.\
  ★ 예: **스택 소진에 이름을 붙여 주는 유일한 도구**다(`stack-overflow` · `run exit=1`).
- **UBSan(UndefinedBehaviorSanitizer)** — 정의되지 않은 동작을 실행 중에 보고하는 도구.\
  ★ 예: `n <= 0` 을 잡는다 — **잡고도 프로그램은 `run exit=0`** 으로 끝난다.
- **`ulimit -s`** — 셸이 새 프로세스에 주는 **스택 한계**(KB). 예: 이 머신은 **8192**, 즉 8,388,608 바이트다.

---

## 더 들어가면

- ★ **`-Werror=vla` 와 `-fno-sanitize-recover=all` 을 안 던졌다.** 실측한 것은 **`-Wvla` 가 경고이고 `cc exit=0`** 이라는 것,\
  **UBSan 이 말하고도 `run exit=0`** 이라는 것까지다. ★ 「전수 관찰」과 「빌드 깨기」는 **다른 실행**이다.
- ★ **`-Wstack-usage=` 같은 「자리 크기」 쪽 플래그를 안 던졌다.** 결론은 「**기본과 `-Wall -Wextra -pedantic` 에서 0건**」까지다.
- ★ **스택 경계를 정밀하게 좁히지 않았다.** 8,000,000 과 9,000,000 **두 점**만 던졌다 —\
  프레임의 나머지가 얼마를 쓰는지에 달려 있어 **「8,388,608 에서 끊긴다」로 적으면 지어내는 것**이 된다.
- ★ **최적화 수준을 바꿔 던지지 않았다.** 스택 소진과 `n <= 0` 은 **UB** 라 갈릴 수 있는 자리인데 **기본 한 벌**만 던졌다.
- ★ **VLA 의 정렬**(`_Alignof`)과 **`alloca` 와의 비교**, **빈 초기자**(`int a[m] = {}`)를 안 던졌다.
- ★ **`__STDC_NO_VLA__` 를 정의하는 구현을 만나지 못했다.** 그래서 **「그 구현에서 무엇이 막히는가」는 이 문서가 말할 수 없고**,\
  **C23 에서 선택의 범위가 좁아졌다는 것도 출력으로는 확인되지 않는다**(표준 문서 쪽 사실이다).
