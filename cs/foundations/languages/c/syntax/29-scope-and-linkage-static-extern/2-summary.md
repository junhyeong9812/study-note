# c/syntax/29 — 스코프와 링크(`static`·`extern`): 「**이 이름은 어디까지 보이고, 다른 파일의 같은 이름과 같은 것인가**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 잠정 정의·링크 규칙·`inline` 정의·부록 J 의 「여러 외부 정의」 공통 확장을 **본문에서 직접 찾아 읽었다**) · [GCC 10 Porting — `-fno-common` 기본값](https://gcc.gnu.org/gcc-10/porting_to.html) · [Clang 11 Release Notes](https://releases.llvm.org/11.0.0/tools/clang/docs/ReleaseNotes.html)(「`-fno-common` has been enabled as the default」)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **심볼·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다. 소스 펜스도 같은 파일에서 떠 왔다.
> **버전** — 스코프 넷·링크 셋·`static`/`extern` 은 **C89 부터**다. **`inline` 은 C99 부터**다((8)).\
> ★★ **잠정 정의를 두 파일에 두면 링크가 깨지는 것**은 언어 규칙이 아니라 **컴파일러 기본값**이 바꾼 것이다 — **GCC 10 · Clang 11** 부터 `-fno-common` 이 기본이다((5)).
> ★★ **경계** — **링커가 무엇을 하는가**(심볼 해석·재배치) 일반은 [`foundations/compiler-pipeline/`](../../../../compiler-pipeline/)가 정본이다.\
> 여기는 「**C 의 어떤 선언이 어떤 심볼을 만드나**」만 본다.\
> ★ **저장 기간**은 [28번 형제](../28-choosing-among-four-storage-durations/)가 정본이다 — 여기서는 **링크와 갈라 세우는 데**만 쓴다.\
> ★ **`inline` 의 규칙 전체**는 목록의 **39번 주제**, **헤더에 무엇을 두나**는 목록의 **44번 주제**, **링크 오류를 거꾸로 읽는 법**은 목록의 **45번 주제**가 정본이다.\
> ★ **파일 스코프 `const` 의 링크**는 [31번 형제](../31-const-and-pointer-const-placement/)가 정본이다.
> 선행 — [28번 형제](../28-choosing-among-four-storage-durations/) · [25번 형제](../25-incomplete-types-and-opaque-struct/)(두 번역 단위 실험).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — `nm` 이다.** 링크는 **심볼의 글자 한 개**(`T`/`t`/`D`/`d`/`B`/`b`/`U`/`C`)로 오브젝트 파일에 박힌다.
실행 출력은 링크가 **깨졌는지**만 말하고, `nm` 은 **왜 깨졌는지**를 말한다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | 프로토타입 스코프 경고 · `conflicting types` · `-Wshadow` · `-Wlto-type-mismatch` | 씀 |
| ② 실행 출력 | 가려진 `x` 의 값 · `-fcommon` 이 두 `t` 를 **하나로 합친 것** | 씀 |
| ③ sanitizer | `extern` 타입 불일치에 ASan+UBSan 을 던졌다 — **침묵**((7)) | 씀(침묵) |
| ★★★ ④ **`nm`·`readelf -s`** | ★ **본체** — 링크 셋과 저장 기간을 **심볼의 글자와 `Bind` 칸**으로 | 씀 |
| ⑤ 단계별 종료 코드 | 컴파일 `exit=0` · 링크 `exit=1` 을 **갈라서** 찍는다((6)) | 씀 |
| 역어셈블 | 링크는 **어느 심볼이 어디 있나**의 문제라 명령을 볼 일이 없다 | ★ **부적용**(잴 것이 없다) |
| ★ 제5의 상태 | 「`inline` 함수에 외부 정의가 있나」를 **링크 에러 대신 `nm` 으로** 물었다 — `U twice` 대 `T twice` 대 `t twice`((8)) | 창을 바꿔 답함 |

★ **바꾼 창(`nm`)이 못 보는 것** — `nm` 의 소문자는 **ELF 의 `LOCAL`** 이지 C 의 「내부 링크」가 아니다. **링크 없는 함수 안 `static`** 도 소문자로 나온다((3)).

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

★ `gcc-12`(12.4.0)와 `g++`·`clang++` 도 같은 머신에 있다 — (5)의 판 격자와 (9)의 대비에 썼다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **`nm` 의 글자와 이름** · `readelf -s` 의 `Bind`·`Type`·`Ndx` | 오브젝트 파일 안의 **상대 주소**라 ASLR 과 무관하다 |
| 안 흔들린다 | ★★ **`nm` 의 주소 칸**(`0000000000000018` 같은 것) | 섹션 안의 오프셋이다 — 재실행에 같았다. 다만 **컴파일러가 바뀌면 바뀐다** |
| 안 흔들린다 | 링커 진단 전문 · 단계별 종료 코드 | 오브젝트를 **먼저 `-c` 로 만들고** 링크했다 — 한 줄로 돌리면 `/tmp/ccXXXX.o` 가 박혀 흔들린다 |
| 안 흔들린다 | 실행 출력 | 이 편의 프로그램은 전부 결정적이다 |
| 해당 없음 | 주소·PID | 실행 중 주소를 찍지 않았다 |

★ **정규화 규칙은 하나도 안 썼다** — 이 편의 블록은 재실행에서 한 글자도 같아야 한다.

## 한눈에 — 쉽게 말하면

**스코프는 「이 이름이 어디서 보이나」이고, 링크는 「다른 곳의 같은 이름이 같은 물건인가」다.**

회사 건물로 생각한다.

- **회의실 칠판에 쓴 이름** — 그 회의실 안에서만 보인다. 옆 회의실에 같은 이름이 있어도 **남남**이다. → **블록 스코프 · 링크 없음**
- **우리 부서 게시판** — 부서 안에서는 다 보이지만 **다른 부서에는 안 보인다.** 다른 부서에 같은 이름이 있어도 남남이다. → **파일 스코프 `static` · 내부 링크**
- **사내 전화번호부** — 회사 전체가 보고, **같은 이름은 같은 사람**이다. 두 부서가 같은 이름으로 **각자 등록하면 충돌**한다. → **외부 링크**
- **「번호부에 있을 거예요」라는 메모** — 사람을 만들지 않는다. **가리키기만** 한다. 번호부에 없으면 전화가 안 걸린다. → **`extern` 선언 · `U`**

| 비유 | 실체 | `nm` 의 글자 |
|---|---|---|
| 회의실 칠판 | 함수 안 `int local;` | ★ **없다** — 심볼이 안 생긴다 |
| 회의실 칠판인데 **밤새 남는 것** | 함수 안 `static int calls;` | ★★ `b` — **링크 없음인데 소문자가 붙는다** |
| 부서 게시판 | 파일 스코프 `static int s;` · `static` 함수 | `b`·`d`·`t` (소문자) |
| 사내 번호부 | 파일 스코프 `int g = 1;` · 보통 함수 | `B`·`D`·`T` (대문자) |
| 「번호부에 있을 거예요」 | `extern int e;` 를 **쓰면** | `U` (정의 없음) |
| 쓰지도 않은 메모 | `extern int e;` 를 **안 쓰면** | ★ **없다** |
| ★ 두 부서가 같은 이름으로 등록 | 두 파일의 `int shared = 1;` · `int shared = 2;` | ★★ `multiple definition` — **링크 `exit=1`** |
| ★ 이름만 적고 **등록은 알아서** | 두 파일의 `int t;`(잠정 정의) | ★★★ **판에 달렸다** — `-fcommon` 이면 합쳐지고 기본값이면 깨진다 |

```text
   같은 낱말 static 이 자리에 따라 바꾸는 것

   파일 스코프        static int s;         -> ★ 링크를 바꾼다 (외부 -> 내부)   nm: b
                                               저장 기간은 원래 정적이다
   함수 안            static int calls;     -> ★ 저장 기간을 바꾼다 (자동 -> 정적) nm: b
                                               링크는 원래 없다

   ★ 두 줄이 nm 에서 ★ 같은 글자 b 로 나온다 — 그래서 nm 만 보고는 둘을 못 가른다
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 스코프 넷·링크 셋·`static`/`extern` 의 뜻이 전부 표준이다.
- ★★ 두 번째 무게중심은 「**UB**」다 — **같은 이름의 외부 정의가 둘**인 것(잠정 정의 포함)과 **`extern` 으로 타입을 다르게 선언**하는 것. 둘 다 **표준이 진단을 요구하지 않는다.**
- ★★ 그리고 「**조건부 표준 — 공통 확장**」 칸이 드물게 차 있다 — `-fcommon` 이 **부록 J 의 「여러 외부 정의」 확장**이다((5)).
- ★ 「**미명시**」 칸도 하나 있다 — `inline` 정의와 외부 정의가 둘 다 있을 때 **어느 쪽을 부를지**((8)).

> **스코프(scope)** — 이름이 **어디서부터 어디까지 보이는가.** 소스 코드의 범위다.\
> 예: 함수 안 `int x;` 는 그 블록이 끝나면 안 보인다.

> **링크(linkage)** — 다른 선언의 **같은 이름이 같은 물건을 가리키는가.** 외부·내부·없음 셋이다.\
> 예: 두 파일의 `int g;` 는 외부 링크라 **같은 객체**를 가리키려 한다.

> **번역 단위(translation unit)** — `.c` 파일 하나를 **전처리까지 끝낸 것.** 컴파일러는 한 번에 하나만 본다.\
> 예: `gcc -c a.c` 가 만드는 `a.o` 하나가 번역 단위 하나에서 나온다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`static` 은 왜 자리마다 다른 일을 하나** — 파일 스코프에서는 무엇을, 함수 안에서는 무엇을 바꾸나.
2. ★★★ **같은 이름이 두 파일에 있으면 무슨 일이 나나** — 정의·선언·잠정 정의·`inline` 각각.
3. ★★ **그것을 어떻게 확인하나** — 실행이 아니라 **오브젝트 파일에 무엇이 박혔는지**로.

## 동작 방식

### (1) ★★ 스코프 넷 — 가려짐과 「다시 부르기」

**언제 쓰나** — 같은 이름이 안팎에 있을 때 **지금 어느 것을 쓰고 있는지** 판단할 때.

```c
/* s29g.c */
#include <stdio.h>

int x = 1;                               /* 파일 스코프 */

int main(void) {
    printf("파일 스코프         x = %d\n", x);
    int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
    printf("main 블록           x = %d\n", x);
    {
        int x = 3;                       /* 더 안쪽 블록 — 또 가린다 */
        printf("안쪽 블록           x = %d\n", x);
        {
            extern int x;                /* ★ 가려진 파일 스코프 x 를 다시 부른다 */
            printf("extern 으로 부른    x = %d\n", x);
        }
    }
    for (int x = 4; x < 5; x++)          /* for 의 첫 칸도 블록 스코프다 */
        printf("for 머리            x = %d\n", x);
    printf("다시 main 블록      x = %d\n", x);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s29g.c -o x ; ./x (cc exit=0 · run exit=0) =====
파일 스코프         x = 1
main 블록           x = 2
안쪽 블록           x = 3
extern 으로 부른    x = 1
for 머리            x = 4
다시 main 블록      x = 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29g.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wshadow -c s29g.c -o /dev/null (cc exit=0) =====
s29g.c: In function ‘main’:
s29g.c:7:9: warning: declaration of ‘x’ shadows a global declaration [-Wshadow]
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
s29g.c:3:5: note: shadowed declaration is here
    3 | int x = 1;                               /* 파일 스코프 */
      |     ^
s29g.c:10:13: warning: declaration of ‘x’ shadows a previous local [-Wshadow]
   10 |         int x = 3;                       /* 더 안쪽 블록 — 또 가린다 */
      |             ^
s29g.c:7:9: note: shadowed declaration is here
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
s29g.c:17:14: warning: declaration of ‘x’ shadows a previous local [-Wshadow]
   17 |     for (int x = 4; x < 5; x++)          /* for 의 첫 칸도 블록 스코프다 */
      |              ^
s29g.c:7:9: note: shadowed declaration is here
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
```

```text
   int x = 1;                  파일 스코프  <-----------------------+
   main {                                                           |
       int x = 2;              main 블록 — 파일의 x 를 가린다         |
       {                                                            |
           int x = 3;          안쪽 블록 — 또 가린다                  |
           { extern int x; }   ★ 링크 있는 x 를 찾아 ★ 파일의 x 로 --+
       }
       for (int x = 4; ...)    for 머리 — 블록 스코프
   }                           다시 main 블록의 x = 2
```

그림 해설 (한 단계씩):

- ★★ **가려진 것은 사라진 것이 아니다.** 안쪽 블록이 끝나면 바깥 `x` 가 다시 보인다 — 마지막 줄이 `2` 다.
- ★★★ **`extern int x;` 가 `1` 을 찍는다.** 바로 바깥의 `x = 3` 은 **링크가 없는** 자동 변수라 짝이 될 수 없고,\
  그러면 이 선언은 **외부 링크**를 갖게 되어 **파일 스코프의 `x`** 와 같은 것이 된다 — 표준이 그렇게 정한다.
- ★ **`-Wshadow` 는 기본 `-Wall -Wextra` 에 없다** — 둘째 블록이 **진단 0줄 · `cc exit=0`** 이다. 따로 켜야 세 건이 나온다. ★ **`extern` 줄에는 경고가 없다** — 가림이 아니라 **다시 부르기**이기 때문이다.
- ★ **`for` 의 첫 칸도 블록 스코프**다(C99 부터). 루프가 끝나면 `x = 4` 는 없다.

**(1-나) ★★ 함수 프로토타입 스코프 — 괄호 안에서 처음 나온 태그는 괄호와 함께 죽는다**

```c
/* s29h.c */
void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */

struct Point { int x, y; };              /* 파일 스코프의 struct Point — 다른 타입이다 */

void take(struct Point *p) { (void)p; }

int main(void) { return 0; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29h.c -o /dev/null (cc exit=1) =====
s29h.c:1:18: warning: ‘struct Point’ declared inside parameter list will not be visible outside of this definition or declaration
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^~~~~
s29h.c:5:6: error: conflicting types for ‘take’; have ‘void(struct Point *)’
    5 | void take(struct Point *p) { (void)p; }
      |      ^~~~
s29h.c:1:6: note: previous declaration of ‘take’ with type ‘void(struct Point *)’
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29h.c -o /dev/null (cc exit=1) =====
s29h.c:1:18: warning: declaration of 'struct Point' will not be visible outside of this function [-Wvisibility]
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^
s29h.c:5:6: error: conflicting types for 'take'
    5 | void take(struct Point *p) { (void)p; }
      |      ^
s29h.c:1:6: note: previous declaration is here
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^
1 warning and 1 error generated.
```

- ★★★ **첫 줄의 `struct Point` 는 괄호 안에서만 사는 새 타입**이다 — 두 컴파일러가 **그 자리에 경고**를 단다.
- ★★ 그래서 5행의 `struct Point`(파일 스코프)는 **다른 타입**이고 `conflicting types` 가 난다 — **`cc exit=1`**.
- ★★ **gcc 의 진단 문구가 이상하다** — 두 선언의 타입을 **둘 다 `void(struct Point *)`** 로 찍는다. **글자는 같은데 다른 타입**이다.\
  ★ 진단 문구를 근거로 쓰면 「같은데 왜 충돌?」에서 막힌다 — **근거는 앞 줄의 경고와 `cc exit`** 다.
- ★ 처방은 **태그를 먼저 파일 스코프에 선언**하는 것이다(`struct Point;` 한 줄). [25번 형제](../25-incomplete-types-and-opaque-struct/)의 불완전 타입 선언이 바로 그것이다.

비용 — **가림은 경고 없이 지나간다.** `-Wshadow` 를 켜지 않으면 **어느 `x` 인지는 읽는 사람의 몫**이다.

### (2) ★★★ 링크 셋을 `nm` 이 글자로 말한다

**언제 쓰나** — 「이 이름이 다른 파일에서 보이나」를 **추측하지 않고 확인**할 때.

```c
/* s29a.c */
int        g_def = 1;          /* 외부 링크 · 정의 · 값 있음 */
int        g_zero = 0;         /* 외부 링크 · 정의 · 0 */
static int s_def = 2;          /* 내부 링크 · 정의 · 값 있음 */
static int s_zero;             /* 내부 링크 · 정의 · 0 */
extern int e_used;             /* 외부 링크 · 선언만 — 쓴다 */
extern int e_unused;           /* 외부 링크 · 선언만 — 안 쓴다 */

static int helper(void) { return s_def + s_zero; }   /* 내부 링크 함수 */

int api(void) {                                      /* 외부 링크 함수 */
    static int calls;          /* ★ 링크 없음 · 정적 저장 기간 */
    int        local = 0;      /* ★ 링크 없음 · 자동 저장 기간 */
    calls++;
    local++;
    return helper() + g_def + g_zero + e_used + calls + local;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && nm s29a.o (cc exit=0) =====
0000000000000018 T api
0000000000000008 b calls.0
                 U e_used
0000000000000000 D g_def
0000000000000000 B g_zero
0000000000000000 t helper
0000000000000004 d s_def
0000000000000004 b s_zero
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && nm s29a.o (cc exit=0) =====
0000000000000000 T api
0000000000000004 b api.calls
                 U e_used
0000000000000000 D g_def
0000000000000000 B g_zero
0000000000000050 t helper
0000000000000004 d s_def
0000000000000008 b s_zero
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && readelf -s -W s29a.o | sed -n '/FILE/,$p' (cc exit=0) =====
     1: 0000000000000000     0 FILE    LOCAL  DEFAULT  ABS s29a.c
     2: 0000000000000000     0 SECTION LOCAL  DEFAULT    1 .text
     3: 0000000000000000     0 SECTION LOCAL  DEFAULT    3 .data
     4: 0000000000000000     0 SECTION LOCAL  DEFAULT    4 .bss
     5: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    3 s_def
     6: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    4 s_zero
     7: 0000000000000000    24 FUNC    LOCAL  DEFAULT    1 helper
     8: 0000000000000008     4 OBJECT  LOCAL  DEFAULT    4 calls.0
     9: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    3 g_def
    10: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    4 g_zero
    11: 0000000000000018    82 FUNC    GLOBAL DEFAULT    1 api
    12: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND e_used
```

```text
   선언                          링크      저장 기간    nm       readelf Bind
   ----------------------------  --------  ----------  -------  ------------
   int g_def = 1;                외부      정적        D        GLOBAL
   int g_zero = 0;               외부      정적        B        GLOBAL
   static int s_def = 2;         ★ 내부    정적        d        LOCAL
   static int s_zero;            ★ 내부    정적        b        LOCAL
   extern int e_used;   (쓴다)    외부      —           U        GLOBAL · UND
   extern int e_unused; (안 쓴다) 외부      —           ★ 없다    ★ 없다
   static int helper(void)       ★ 내부    —           t        LOCAL
   int api(void)                 외부      —           T        GLOBAL
   static int calls;  (함수 안)   ★ 없음    ★ 정적      ★ b      ★ LOCAL
   int local;         (함수 안)   없음      자동         ★ 없다    ★ 없다

   ★ 대문자 = GLOBAL · 소문자 = LOCAL · U = 이 파일에 정의가 없다
   ★ D/d = .data(값 있음) · B/b = .bss(0) · T/t = .text(함수)
```

그림 해설 (한 단계씩):

- ★★★ **대문자와 소문자가 곧 `readelf` 의 `GLOBAL` 과 `LOCAL`** 이다 — 두 창이 같은 말을 한다.
- ★★★ **`e_unused` 는 심볼이 아예 없다.** `extern` 선언은 **아무것도 만들지 않는다** — 쓰는 순간 `U` 가 된다.
- ★★ **`g_zero = 0` 은 `B` 다.** 값을 `0` 으로 적어도 **`.bss`** 로 간다 — 「0 은 파일에 안 싣는다」는 [30번 형제](../30-initialization-rules-and-indeterminate-values/)의 결론과 같다.
- ★★ **`local` 은 심볼이 없다** — 자동 저장 기간이라 **스택에만** 있다. 링크도 없고 이름도 안 남는다.
- ★★ **두 컴파일러가 갈린 자리** — 함수 안 `static int calls` 의 **심볼 이름**이 **gcc 는 `calls.0`, clang 은 `api.calls`** 다.\
  ★ 둘 다 **다른 파일에서 부를 수 없게** 이름을 뭉갠 것이고, 그 방식은 **표준이 정하지 않는다**(구현 정의보다도 느슨하다 — 이름 자체가 표준 밖이다).
- ★ **주소 칸도 컴파일러마다 다르다**(`api` 가 gcc `0x18` · clang `0x0`). **글자와 이름만** 근거로 쓴다.

비용 — **소문자라고 다 「내부 링크」가 아니다.** 그것은 (3)이 다룬다.

### (3) ★★★ 같은 키워드 `static` 이 두 가지를 바꾼다 — 그리고 `nm` 은 그 둘을 못 가른다

**언제 쓰나** — 「`static` 을 붙이면 무엇이 달라지나」를 한 문장으로 답해야 할 때.

(2)의 `s_zero`(파일 스코프 `static`)와 `calls`(함수 안 `static`)를 나란히 본다.

```text
                    static 이 없으면            static 을 붙이면           바뀐 것
   ---------------  ------------------------  ------------------------  -----------
   파일 스코프       int s;  외부 링크 · 정적    static int s; 내부 · 정적   ★ 링크
                    nm: B                      nm: b
   함수 안          int c;  링크 없음 · 자동    static int c; 없음 · 정적   ★ 저장 기간
                    nm: (없다)                 nm: b  (이름: calls.0)

   ★ 오른쪽 두 칸이 ★ 같은 b 다. nm 의 소문자는 「이 파일 밖에서 안 보인다」일 뿐이다.
```

- ★★★ **파일 스코프의 `static` 은 링크를 바꾼다**(외부 → 내부). 저장 기간은 **원래도 정적**이었다.
- ★★★ **함수 안의 `static` 은 저장 기간을 바꾼다**(자동 → 정적). 링크는 **원래도 없었다** — 여전히 그 함수 안에서만 보인다.
- ★★★ **`nm` 은 둘 다 `b` 로 찍는다.** ELF 에는 「내부 링크」와 「링크 없음」을 가르는 칸이 **없다** — 둘 다 **`LOCAL`** 이다.\
  ★★ **가르는 것은 이름**이다 — 함수 안 `static` 은 `calls.0`·`api.calls` 처럼 **뭉개진 이름**으로 나온다. 표준이 보장하는 표시가 아니라 **컴파일러의 관례**다.
- ★ [28번 형제](../28-choosing-among-four-storage-durations/)가 「**같은 낱말이 자리에 따라 다른 일을 한다**」고 적고 이 편으로 넘긴 자리다.

비용 — **`nm` 이 링크를 말한다는 것은 반만 맞다.** 대문자는 외부 링크를 말하지만, **소문자는 「내부」와 「없음」을 뭉뚱그린다.**

### (4) ★★ 두 파일에 같은 이름을 정의하면 — 그리고 `static` 을 붙이면

**언제 쓰나** — 헤더에 변수 **정의**를 넣었다가 링크가 깨졌을 때.

```c
/* s29b1.c */
int shared = 1;                /* ★ 외부 링크 정의 */
int from_b1(void) { return shared; }
```

```c
/* s29b2.c */
#include <stdio.h>

int shared = 2;                /* ★ 같은 이름의 외부 링크 정의 — 두 번째 */
int from_b1(void);

int main(void) {
    printf("b1 쪽 shared = %d · b2 쪽 shared = %d\n", from_b1(), shared);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29b1.c s29b2.c && gcc s29b1.o s29b2.o -o x (cc exit=1) =====
/usr/bin/ld: s29b2.o:(.data+0x0): multiple definition of `shared'; s29b1.o:(.data+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29b1.c s29b2.c && clang s29b1.o s29b2.o -o x (cc exit=1) =====
/usr/bin/ld: s29b2.o:(.data+0x0): multiple definition of `shared'; s29b1.o:(.data+0x0): first defined here
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★★ **컴파일은 두 파일 다 통과하고 링크에서 죽는다.** 컴파일러는 **한 번에 한 파일만** 보므로 충돌을 볼 수 없다.
- ★★ **메시지를 내는 것은 둘 다 `/usr/bin/ld`** 다 — 컴파일러가 달라도 **첫 줄이 한 글자도 같다.** 끝 줄만 `collect2` 대 `clang: error` 로 갈린다.
- ★ `(.data+0x0)` — 두 `shared` 가 **각자의 `.data`** 에 있다. 값이 있는 정의라 `D` 다.

`static` 을 붙이면:

```c
/* s29c1.c */
static int shared = 1;         /* ★ 내부 링크 — 이 파일 것 */
int from_c1(void) { return shared; }
```

```c
/* s29c2.c */
#include <stdio.h>

static int shared = 2;         /* ★ 내부 링크 — 이 파일 것 */
int from_c1(void);

int main(void) {
    printf("c1 쪽 shared = %d · c2 쪽 shared = %d\n", from_c1(), shared);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29c1.c s29c2.c && gcc s29c1.o s29c2.o -o x ; ./x (cc exit=0 · run exit=0) =====
c1 쪽 shared = 1 · c2 쪽 shared = 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29c1.c s29c2.c && nm s29c1.o s29c2.o (cc exit=0) =====

s29c1.o:
0000000000000000 T from_c1
0000000000000000 d shared

s29c2.o:
                 U from_c1
0000000000000000 T main
                 U printf
0000000000000000 d shared
```

- ★★★ **두 `shared` 가 둘 다 산다** — `1` 과 `2` 가 따로 찍힌다. **이름은 같고 물건은 둘**이다.
- ★★ `nm` 에서 **둘 다 소문자 `d`** 다. 링커가 **서로 짝지으려 하지 않는다.**
- ★ `s29c2.o` 의 `U from_c1` — 함수는 `static` 이 아니라 **외부 링크로 짝지어졌다.** 한 파일 안에서도 이름마다 링크가 다르다.

비용 — **`static` 은 충돌을 없애는 것이 아니라 「같은 것이 아니다」라고 선언하는 것**이다. 한 값을 공유하려던 것이면 **틀린 처방**이다 — 헤더에는 `extern int shared;` 를, 정의는 **한 파일에만** 둔다(목록의 **44번 주제**).

### (5) ★★★ 잠정 정의 — `int t;` 를 두 파일에 두면 **판에 달렸다**

**언제 쓰나** — 옛 코드가 새 컴파일러에서 링크가 깨질 때. ★ **이 편의 판 격자**다.

```c
/* s29t1.c */
int t;                         /* ★ 잠정 정의(tentative definition) — 초기자 없음 */
int get_t1(void) { return t; }
```

```c
/* s29t2.c */
#include <stdio.h>

int t;                         /* ★ 같은 이름의 잠정 정의 — 두 번째 파일 */
int get_t1(void);

int main(void) {
    t = 5;
    printf("t2 쪽 t = %d · t1 쪽 t = %d\n", t, get_t1());
    return 0;
}
```

```c
/* s29u1.c */
int t = 0;                     /* ★ 초기자가 있다 — 잠정 정의가 아니라 정의 */
int get_t1(void) { return t; }
```

```text
===== 잠정 정의 두 개 — 컴파일러 3 × 플래그 3 · 초기자 하나 × 2 (exit=0) =====
컴파일러   플래그       cc     link     실행
gcc-12     (기본)       exit=0 exit=1   -
gcc-12     -fno-common  exit=0 exit=1   -
gcc-12     -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
gcc        (기본)       exit=0 exit=1   -
gcc        -fno-common  exit=0 exit=1   -
gcc        -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
clang      (기본)       exit=0 exit=1   -
clang      -fno-common  exit=0 exit=1   -
clang      -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
--- 한쪽에 초기자(int t = 0;)를 두면 (s29u1.c + s29t2.c)
gcc        (기본)       exit=0 exit=1   -
gcc        -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
clang      (기본)       exit=0 exit=1   -
clang      -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29t1.c s29t2.c && gcc s29t1.o s29t2.o -o x (cc exit=1) =====
/usr/bin/ld: s29t2.o:(.bss+0x0): multiple definition of `t'; s29t1.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fcommon -c s29t1.c s29t2.c && gcc -fcommon s29t1.o s29t2.o -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fcommon -c s29t1.c -o s29t1.o && nm s29t1.o && gcc -std=c17 -Wall -Wextra -pedantic -c s29t1.c -o s29t1.o && nm s29t1.o (cc exit=0) =====
0000000000000000 T get_t1
0000000000000004 C t
0000000000000000 T get_t1
0000000000000000 B t
```

```text
   int t;  ← 초기자가 없는 파일 스코프 선언 = ★ 잠정 정의(tentative definition)

   -fno-common (지금의 기본값)            -fcommon
   ---------------------------          ---------------------------
   s29t1.o : B t   (.bss 에 자리)        s29t1.o : C t   (★ 자리 없음 — 「공용」)
   s29t2.o : B t                         s29t2.o : C t
   링커 : 정의 둘 -> ★ multiple definition  링커 : 공용 둘 -> ★ 하나로 합친다
          link exit=1                           link exit=0 · t2 쪽 5 = t1 쪽 5
```

그림 해설 (한 단계씩):

- ★★★ **세 컴파일러 전부 기본값에서 링크가 깨진다**(`exit=1`). **`-fcommon` 을 주면 통과**하고 두 `t` 가 **하나로 합쳐진다** — t2 가 쓴 `5` 를 t1 이 읽는다.
- ★★★ **갈린 것은 `nm` 의 글자 하나다** — `-fcommon` 이면 **`C`**(common), 기본값이면 **`B`**. `C` 는 「**자리를 링커가 정해 달라**」는 뜻이라 여러 개가 있어도 된다.
- ★★ **한쪽에 초기자가 있어도 결과가 같다**(`int t = 0;` + `int t;`) — `-fcommon` 이면 공용 하나와 정의 하나가 **합쳐지고**, 기본값이면 깨진다.
- ★★ **컴파일은 모든 칸에서 `exit=0`** 이다. **죽는 곳은 늘 링크**다. ★ `-fcommon` 의 병합은 **진단 0줄**로 일어난다(`gcc -fcommon` 블록).

**판 경계 — 이 머신에서 잰 것과 못 잰 것**

| 판 | `int t;` 두 파일의 기본 결과 | 근거 |
|---|---|---|
| GCC 9 이하 | 통과(`-fcommon` 이 기본) | ★ **못 잰 것** — 이 머신에 GCC 9 이하가 없다. [GCC 10 Porting](https://gcc.gnu.org/gcc-10/porting_to.html)의 문장으로만 |
| ★ **GCC 10** | ★ **여기서 기본값이 `-fno-common` 으로 바뀌었다** | 같은 문서 |
| GCC 12.4 · 13.3 | **링크 `exit=1`** | ★ 위 격자 — **실측** |
| Clang 10 이하 | 통과 | ★ **못 잰 것** — 문서로만 |
| ★ **Clang 11** | ★ **`-fno-common` 이 기본** | [Clang 11 Release Notes](https://releases.llvm.org/11.0.0/tools/clang/docs/ReleaseNotes.html) |
| Clang 18.1 | **링크 `exit=1`** | ★ 위 격자 — **실측** |

- ★★★ **경계 자체는 이 머신에서 잴 수 없다** — 가진 판이 전부 경계 **뒤쪽**이다. 「GCC 10 에서 바뀌었다」는 **문서의 주장**이고 이 문서가 **실행으로 확인한 것은 「12·13·18 은 깨진다」까지**다.
- ★★ **표준은 무엇이라 하나** — 한 번역 단위 안의 잠정 정의는 **그 파일 끝에서 정의 하나**가 된다. 두 파일이면 **외부 정의가 둘**이고, 외부 링크 이름에 정의가 둘이면 **UB** 다(진단 의무가 없다).\
  ★★ `-fcommon` 의 병합은 **부록 J 의 「여러 외부 정의」 공통 확장**이다 — 표준이 **「이런 확장이 흔하다」고 적어 둔 것**이지 보장이 아니다.

비용 — **옛 코드의 헤더에 `int t;` 가 있으면 새 컴파일러에서 깨진다.** 처방은 `-fcommon` 이 아니라 **헤더에는 `extern int t;`, 정의는 한 파일에**다(목록의 **44번 주제**).

### (6) ★★ `static` 함수를 다른 파일에서 부르면 — **컴파일은 통과하고 링크에서 죽는다**

**언제 쓰나** — `undefined reference` 가 났는데 정의는 분명히 있을 때.

```c
/* s29d1.c */
static int helper(void) { return 7; }   /* ★ 내부 링크 */
int use_helper(void) { return helper(); }
```

```c
/* s29d2.c */
#include <stdio.h>

int helper(void);              /* ★ 외부 링크로 선언 — 다른 파일의 static 을 부르려 한다 */

int main(void) {
    printf("helper() = %d\n", helper());
    return 0;
}
```

```text
===== static 함수를 다른 번역 단위에서 — 단계별 종료 코드 (컴파일은 -std=c17 -Wall -Wextra -pedantic -c) (exit=0) =====
gcc    ① s29d1.c 컴파일            exit=0
gcc    ② s29d2.c 컴파일            exit=0
gcc    ③ s29d1.o + s29d2.o 링크   exit=1
clang  ① s29d1.c 컴파일            exit=0
clang  ② s29d2.c 컴파일            exit=0
clang  ③ s29d1.o + s29d2.o 링크   exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29d1.c s29d2.c && gcc s29d1.o s29d2.o -o x (cc exit=1) =====
/usr/bin/ld: s29d2.o: in function `main':
s29d2.c:(.text+0x9): undefined reference to `helper'
collect2: error: ld returned 1 exit status
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29d1.c s29d2.c && clang s29d1.o s29d2.o -o x (cc exit=1) =====
/usr/bin/ld: s29d2.o: in function `main':
s29d2.c:(.text+0x10): undefined reference to `helper'
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29d1.c s29d2.c && nm s29d1.o s29d2.o (cc exit=0) =====

s29d1.o:
0000000000000000 t helper
000000000000000f T use_helper

s29d2.o:
                 U helper
0000000000000000 T main
                 U printf
```

- ★★★ **단계가 셋이고 죽는 것은 셋째뿐**이다 — 두 파일 컴파일은 `exit=0`, 링크만 `exit=1`.
- ★★★ **`nm` 이 이유를 글자로 보여 준다** — `s29d1.o` 에는 `t helper`(**소문자**), `s29d2.o` 에는 `U helper`. **소문자는 링커의 짝짓기 대상이 아니다.**
- ★★ 링커는 「`helper` 가 없다」고 말한다. **있는데 안 보이는 것**과 **없는 것**을 링커 진단은 **가르지 않는다** — `nm` 이 가른다.
- ★ `(.text+0x9)` 대 `(.text+0x10)` — **호출 명령의 오프셋**이 컴파일러마다 다르다. 근거로 쓰지 않는다.

비용 — **컴파일 단계만 도는 빌드(`-c`·린트·IDE)는 이것을 절대 못 잡는다.** 링크까지 가야 드러난다.

### (7) ★★ `extern` 으로 타입을 다르게 선언하면 — **여섯 벌 중 다섯이 침묵한다**

**언제 쓰나** — 헤더 없이 `extern` 을 손으로 적었을 때. [25번 형제](../25-incomplete-types-and-opaque-struct/)의 「`-flto` 는 서명은 잡고 구조체 레이아웃은 못 잡았다」에 잇는다.

```c
/* s29e1.c */
double val = 3.5;              /* ★ 정의는 double */
```

```c
/* s29e2.c */
#include <stdio.h>

extern int val;                /* ★ 선언은 int — 타입이 다르다 */

int main(void) {
    printf("val 을 int 로 읽으면 = %d\n", val);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s29e1.c s29e2.c -o x ; ./x (cc exit=0 · run exit=0) =====
val 을 int 로 읽으면 = 0
```

```text
===== extern 타입 불일치 — 여섯 벌 (exit=0) =====
gcc                                    cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
gcc -flto                              cc exit=0 경고 1건 | run exit=0 | val 을 int 로 읽으면 = 0
clang                                  cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
clang -flto                            cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
gcc -fsanitize=address,undefined -g    cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
clang -fsanitize=address,undefined -g  cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s29e1.c s29e2.c -o x (cc exit=0) =====
s29e2.c:3:12: warning: type of ‘val’ does not match original declaration [-Wlto-type-mismatch]
    3 | extern int val;                /* ★ 선언은 int — 타입이 다르다 */
      |            ^
s29e1.c:1:8: note: type ‘double’ should match type ‘int’
    1 | double val = 3.5;              /* ★ 정의는 double */
      |        ^
s29e1.c:1:8: note: ‘val’ was previously declared here
s29e1.c:1:8: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -flto s29e1.c s29e2.c -o x (cc exit=0) =====
```

- ★★★ **gcc `-flto` 만 잡는다** — `type of 'val' does not match original declaration`. **그리고 `cc exit=0`** 이다 — 경고일 뿐이다.
- ★★★ **clang `-flto` 는 한 마디도 없다** — 같은 이름의 옵션인데 **대조하는 것이 다르다.** 「`-flto` 가 잡는다」는 **gcc 의 성질**이지 플래그의 성질이 아니다.
- ★★ **ASan+UBSan 두 벌도 침묵**한다 — `int` 4바이트를 읽는 것은 `double` 8바이트 **범위 안**이라 메모리 오류가 아니다. **원리상 못 보는 자리**다.
- ★★ **값 `0`** 은 `3.5` 의 `double` 비트 패턴 **아래 32비트**가 우연히 0 이라서다 — 이 값은 **UB 의 한 결과**이지 계산해 낼 대상이 아니다.
- ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)에서 **`-flto` 가 함수 서명은 잡았다**. 여기서는 **변수 타입도 잡았다**(gcc). 못 잡은 것은 **구조체 레이아웃**이었다 — **gcc `-flto` 가 보는 것은 「선언의 타입」까지**다.

비용 — **「헤더를 거쳐 선언을 한 곳에만 둔다」 말고는 막을 길이 없다.** 도구 여섯 벌 중 하나만, 그것도 경고로만 말한다.

### (8) ★ C99 `inline` — `inline` 만 쓰면 **외부 정의가 없다**

**언제 쓰나** — 헤더에 `inline` 함수를 두었는데 **`-O0` 에서만** 링크가 깨질 때.

```c
/* s29f.c */
#include <stdio.h>

inline int twice(int x) { return 2 * x; }   /* ★ inline 만 — 외부 정의가 아니다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

```c
/* s29f2.c */
#include <stdio.h>

inline int twice(int x) { return 2 * x; }
extern inline int twice(int x);             /* ★ 이 한 줄이 이 파일에 외부 정의를 만든다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

```c
/* s29f3.c */
#include <stdio.h>

static inline int twice(int x) { return 2 * x; }   /* ★ 내부 링크 — 필요하면 이 파일에 사본을 만든다 */

int main(void) {
    printf("twice(21) = %d\n", twice(21));
    return 0;
}
```

```text
===== C99 inline — 파일 3 × 컴파일러 2 × 최적화 2 (링크 종료 코드) (exit=0) =====
s29f   gcc    -O0  link exit=1 | -
s29f   gcc    -O2  link exit=0 | twice(21) = 42
s29f   clang  -O0  link exit=1 | -
s29f   clang  -O2  link exit=0 | twice(21) = 42
s29f2  gcc    -O0  link exit=0 | twice(21) = 42
s29f2  gcc    -O2  link exit=0 | twice(21) = 42
s29f2  clang  -O0  link exit=0 | twice(21) = 42
s29f2  clang  -O2  link exit=0 | twice(21) = 42
s29f3  gcc    -O0  link exit=0 | twice(21) = 42
s29f3  gcc    -O2  link exit=0 | twice(21) = 42
s29f3  clang  -O0  link exit=0 | twice(21) = 42
s29f3  clang  -O2  link exit=0 | twice(21) = 42
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f.c && gcc s29f.o -o x (cc exit=1) =====
/usr/bin/ld: s29f.o: in function `main':
s29f.c:(.text+0xe): undefined reference to `twice'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f.c -o f1.o && nm f1.o && gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f2.c -o f2.o && nm f2.o && gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f3.c -o f3.o && nm f3.o (cc exit=0) =====
0000000000000000 T main
                 U printf
                 U twice
0000000000000012 T main
                 U printf
0000000000000000 T twice
000000000000000e T main
                 U printf
0000000000000000 t twice
```

- ★★★ **`inline` 만 있으면 `-O0` 에서 링크가 깨지고 `-O2` 에서는 통과한다.** 같은 소스가 **최적화 수준에 따라 링크가 되고 안 되는** 드문 자리다.
- ★★★ **`nm` 이 이유를 말한다 — 제5의 상태**다. 「외부 정의가 있나」를 링크 에러로 묻는 대신 **`nm` 으로 물었다**:\
  `s29f` 는 **`U twice`**(정의 없음) · `s29f2` 는 **`T twice`**(외부 정의) · `s29f3` 은 **`t twice`**(이 파일 전용 사본).
- ★★ **C99 의 규칙** — 외부 링크 함수의 정의에 **`extern` 없이 `inline` 만** 붙으면 그것은 「**인라인 정의**」이고 **외부 정의를 만들지 않는다.** 호출이 인라인되지 않으면 **다른 곳의 외부 정의**를 찾으러 간다.
- ★★ **`-O2` 가 통과한 것은 호출을 펼쳐서 심볼이 필요 없어졌기 때문**이다 — **보장이 아니다.** 인라인할지는 컴파일러가 고른다.
- ★ **미명시 칸** — 인라인 정의와 외부 정의가 **둘 다 있으면 어느 쪽을 쓸지 표준이 정하지 않는다.**
- ★ **C++ 의 `inline` 은 뜻이 다르다** — 여러 번역 단위에 같은 정의가 있어도 된다는 약속이다((9)). 이 규칙 전체는 목록의 **39번 주제**가 정본이다.

비용 — **디버그 빌드에서만 깨지는 링크 오류**가 된다. 처방은 **`static inline`** 이거나, **한 `.c` 파일에 `extern inline` 선언 한 줄**이다.

### (9) ★ C++ 은 같은 문제를 다른 문법으로 푼다

**언제 쓰나** — C++ 코드에서 `static` 대신 `namespace { }` 를 볼 때.

```cpp
// s29x.cpp
namespace {                          // ★ 이름 없는 네임스페이스 — C 의 파일 스코프 static 자리
int hidden_counter = 1;
int hidden_fn() { return hidden_counter; }
}
static int old_style = 2;            // C 와 같은 static 도 된다
inline int shared_inline = 3;        // ★ C++17 inline 변수 — 여러 번역 단위에 있어도 하나다
int exported() { return hidden_fn() + old_style + shared_inline; }
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s29x.cpp -o s29x.o && nm s29x.o (cc exit=0) =====
0000000000000010 T _Z8exportedv
0000000000000004 d _ZL9old_style
0000000000000000 d _ZN12_GLOBAL__N_114hidden_counterE
0000000000000000 t _ZN12_GLOBAL__N_19hidden_fnEv
0000000000000000 u shared_inline
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s29x.cpp -o s29x.o && nm s29x.o (cc exit=0) =====
0000000000000000 T _Z8exportedv
0000000000000000 d _ZL9old_style
0000000000000004 d _ZN12_GLOBAL__N_114hidden_counterE
0000000000000020 t _ZN12_GLOBAL__N_19hidden_fnEv
0000000000000000 V shared_inline
```

```cpp
// s29y1.cpp
inline int shared_inline = 3;        // ★ 번역 단위 1 에도 정의
int from_y1() { return shared_inline; }
```

```cpp
// s29y2.cpp
#include <cstdio>

inline int shared_inline = 3;        // ★ 번역 단위 2 에도 같은 정의
int from_y1();

int main() {
    shared_inline = 10;
    std::printf("y2 쪽 = %d · y1 쪽 = %d\n", shared_inline, from_y1());
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s29y1.cpp s29y2.cpp && g++ s29y1.o s29y2.o -o x ; ./x (cc exit=0 · run exit=0) =====
y2 쪽 = 10 · y1 쪽 = 10
```

- ★★ **이름 없는 네임스페이스가 C 의 파일 스코프 `static` 자리**다 — `hidden_counter` 가 **`d`**, `hidden_fn` 이 **`t`**(소문자)로 나온다.\
  ★ 이름에 `_GLOBAL__N_1` 이 붙는다 — **뭉갠 이름**이라 다른 파일에서 **철자를 맞출 방법이 없다.**
- ★★★ **C++17 `inline` 변수는 두 파일에 정의가 있어도 링크된다** — y2 가 쓴 `10` 을 y1 이 읽는다. **C 의 (4)가 깨졌던 모양 그대로인데 통과**한다.
- ★★ **두 컴파일러가 다른 글자를 쓴다** — g++ 는 **`u`**(GNU 고유 전역), clang++ 는 **`V`**(약한 객체). **「여럿이어도 된다」를 표시하는 방식**이 구현마다 다르다.
- ★ C 의 `-fcommon` 이 **컴파일러 확장**으로 하던 일을 C++17 은 **언어 문법**으로 약속한다. 그 정본은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **25번**(정적 멤버·`inline` 변수)이고, 이름 없는 네임스페이스는 [C++ 06 — 네임스페이스와 ADL](../../../cpp/syntax/06-namespaces-and-adl/)이 정본이다.

비용 — **C 에는 이 둘이 없다.** 공유 변수는 **`extern` 선언 + 정의 하나**, 파일 전용은 **`static`** 뿐이다.

## 문법 — 형태와 규칙

### 형태

(2)의 `s29a.c` 가 이 절의 **실제로 컴파일되는 형태**다. 선언 하나당 한 줄로 다시 적으면 이렇다.

| 쓴 꼴 | 자리 | 링크 | 저장 기간 | `nm` |
|---|---|---|---|---|
| `int g = 1;` | 파일 | 외부 | 정적 | `D` |
| `int g;` | 파일 | 외부 | 정적 | ★ `B`(기본값) · `C`(`-fcommon`) |
| `static int s;` | 파일 | ★ 내부 | 정적 | `b` |
| `extern int e;` | 파일 | 외부 | — (선언만) | 쓰면 `U` · 안 쓰면 없음 |
| `int f(void) { … }` | 파일 | 외부 | — | `T` |
| `static int f(void) { … }` | 파일 | ★ 내부 | — | `t` |
| `inline int f(int) { … }` | 파일 | 외부 | — | ★ `U`(외부 정의 없음) |
| `int a;` | 블록 | 없음 | 자동 | 없음 |
| `static int c;` | 블록 | 없음 | ★ 정적 | `b` (`c.0` · `f.c`) |
| `extern int x;` | 블록 | 외부(바깥에 링크 있는 선언이 없으면) | — | `U` 또는 같은 파일의 정의 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 두 파일의 `int shared = 1;` / `= 2;` | 컴파일 `exit=0` · 링크 `multiple definition` **`exit=1`** | ★★ UB(진단 의무 없음 — 링커가 잡은 것) | (4) |
| 두 파일의 `int t;` | ★★★ 기본값 링크 `exit=1` · `-fcommon` 통과 | UB · `-fcommon` 은 **공통 확장** | (5) |
| 다른 파일의 `static` 함수를 부름 | 컴파일 `exit=0` · 링크 `undefined reference` **`exit=1`** | 표준(내부 링크의 정의대로) | (6) |
| `extern int val;` 인데 정의는 `double` | ★★ **여섯 벌 중 gcc `-flto` 만 경고** · 전부 `exit=0` | ★★ UB | (7) |
| `inline` 만 붙은 외부 함수를 부름 | ★ `-O0` 링크 `exit=1` · `-O2` 통과 | 표준(외부 정의가 없음) · 어느 정의를 부를지는 미명시 | (8) |
| 괄호 안에서 처음 나온 `struct Point` | 경고 + `conflicting types` **`cc exit=1`** | 표준(제약 위반) | (1-나) |

### 규칙 불릿

- ★★★ **스코프는 넷**이다 — 블록 · 파일 · 함수 프로토타입 · 함수(레이블만). **링크는 셋**이다 — 외부 · 내부 · 없음.
- ★★★ **파일 스코프 `static` 은 링크를 바꾸고, 함수 안 `static` 은 저장 기간을 바꾼다.**
- ★★★ **`nm` 의 대문자는 외부 링크, 소문자는 `LOCAL`** 이다 — 소문자는 **내부 링크와 링크 없음을 둘 다** 덮는다.
- ★★★ **`extern` 선언은 아무것도 만들지 않는다** — 쓰면 `U`, 안 쓰면 심볼조차 없다.
- ★★ **외부 링크 이름에 정의가 둘이면 UB** 다. 지금의 두 컴파일러는 링크에서 **`multiple definition`** 으로 막는다.
- ★★ **잠정 정의(`int t;`)를 두 파일에 두는 것**이 통과하느냐는 **`-fcommon` 에 달렸고**, 기본값은 **GCC 10 · Clang 11 부터** `-fno-common` 이다.
- ★★ **다른 파일의 `static` 함수는 컴파일은 통과하고 링크에서 죽는다.**
- ★★ **`extern` 의 타입 불일치는 gcc `-flto` 만 경고로 잡는다** — clang `-flto`·ASan·UBSan 은 침묵한다.
- ★ **C99 `inline` 만으로는 외부 정의가 없다** — `-O0` 에서 링크가 깨질 수 있다.
- ★ **블록 안 `extern int x;` 는 가려진 파일 스코프 `x` 를 다시 부를 수 있다.**
- ★ **괄호 안에서 처음 나온 태그는 그 괄호와 함께 죽는다**(함수 프로토타입 스코프).

## 어디서 틀리나

### 1. ★★★ 「`static` 이면 다 같은 얘기 아닌가」

**자리에 따라 바꾸는 것이 다르다**((3)). 파일 스코프에서는 **링크**를, 함수 안에서는 **저장 기간**을 바꾼다.\
★ 그리고 `nm` 은 **둘 다 `b`** 로 찍어 이 차이를 **안 보여 준다.** 가르는 것은 **뭉갠 이름**(`calls.0`)뿐이다.

### 2. ★★★ 「옛날엔 됐는데 컴파일러를 올리니 링크가 깨진다」

**잠정 정의가 헤더에 있을 가능성이 크다**((5)). GCC 10 · Clang 11 부터 **`-fno-common` 이 기본**이다.\
★★ `-fcommon` 을 켜면 「고쳐지지만」 **UB 를 확장으로 덮은 것**이다. 처방은 **헤더에 `extern`, 정의는 한 곳**이다.

### 3. ★★ 「정의가 분명히 있는데 `undefined reference` 가 난다」

**있는데 안 보이는 것일 수 있다**((6)). `static` 함수는 `nm` 에서 **소문자 `t`** 라 링커가 짝짓지 않는다.\
★ 링커 진단은 「없다」와 「안 보인다」를 **가르지 않는다** — **`nm` 을 봐라.**

### 4. ★★ 「`extern` 으로 선언했으니 타입은 컴파일러가 맞춰 보겠지」

**컴파일러는 한 파일만 본다**((7)). **여섯 벌 중 gcc `-flto` 한 벌만** 경고했고, 그것도 `cc exit=0` 이다.\
★ 「`-flto` 가 잡는다」는 **gcc 의 성질**이다 — clang `-flto` 는 침묵했다.

### 5. ★★ 「`-O2` 에서는 되니까 괜찮다」

**`inline` 만 붙은 함수는 `-O0` 에서 링크가 깨진다**((8)). `-O2` 의 통과는 **인라인이 심볼을 지웠기 때문**이지 보장이 아니다.

### 6. ★ 「`nm` 에 소문자면 내부 링크다」

**반만 맞다**((3)). **링크 없는 함수 안 `static`** 도 소문자다. `nm` 의 소문자는 **ELF 의 `LOCAL`** 이다.

### 7. ★ 「`extern int x;` 는 바로 바깥의 `x` 를 가리킨다」

**링크 있는 선언을 찾는다**((1)). 바로 바깥의 `x` 가 **링크 없는 자동 변수**면 건너뛰고 **파일 스코프의 `x`** 가 된다 — `1` 이 찍혔다.

### 8. ★ 「진단이 같은 타입이라고 하는데 왜 충돌이냐」

**gcc 의 문구가 두 타입을 같은 글자로 찍었다**((1-나)). 하나는 **괄호 안의 새 태그**다. **문구가 아니라 앞 줄의 경고**가 원인을 말한다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 스코프와 링크의 규칙이 전부 거기 있다.\
★★ 두 번째는 「**UB**」다 — **정의가 둘**이거나 **타입이 어긋난** 외부 링크 이름. **표준은 진단을 요구하지 않고**, 막는 것은 **링커**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | **스코프 넷 · 링크 셋** · 파일 스코프 `static` = 내부 링크 · 함수 안 `static` = 링크 없음 + 정적 · `extern` 이 선언일 뿐인 것 · **블록 안 `extern` 이 링크 있는 선언을 찾는 것** · 잠정 정의가 파일 끝에서 정의가 되는 것 · **C99 `inline` 만으로는 외부 정의가 없는 것** · 프로토타입 스코프의 태그 | `nm` 의 글자 · `extern` 으로 부른 `x = 1` · 링크 `exit=1`(6) · `U twice`(8) · `conflicting types` |
| ★★ **조건부 표준 — 공통 확장** | 표준이 「흔한 확장」으로 적어 둔 것 | ★★ **`-fcommon` 의 여러 외부 정의 병합** — 부록 J 의 확장 | `C t` · 두 `t` 가 하나로(`t1 쪽 t = 5`) |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **컴파일러 기본값**(`-fno-common` 이 GCC 10 · Clang 11 부터) · 심볼 이름을 뭉개는 방식(`calls.0` 대 `api.calls`) · C++ `inline` 변수의 글자(`u` 대 `V`) · 진단 문구 | 판 격자 · `nm` 두 벌 |
| ★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★ **인라인 정의와 외부 정의가 둘 다 있을 때 어느 쪽을 부르나** · 인라인할지 말지 | `-O0` 링크 실패 · `-O2` 통과 |
| ★★ **UB** | 아무 일이나 | ★★ **외부 링크 이름의 외부 정의가 둘**(잠정 정의 둘 포함) · ★★ **같은 객체를 호환되지 않는 타입으로 선언**(`double` 을 `extern int`) | 링크 `multiple definition` · ★ **여섯 벌 중 다섯 벌 침묵** · `val = 0` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`nm` 이 내부 링크와 링크 없음을 못 가른다** — 둘 다 소문자(`LOCAL`)다. ★ **`-Wshadow` 는 `-Wall -Wextra` 에 없다** — 가림은 기본 경고 0건이다 |
| ★★ **공통 확장** | ★★ **`-fcommon` 이 두 정의를 합칠 때 경고가 없다** — 격자의 `-fcommon` 칸이 전부 `exit=0` · 진단 0줄이다 |
| ★ **구현 정의** | ★ **기본값이 바뀐 판 경계를 도구가 알려 주지 않는다** — 옛 코드가 **이유 없이** 깨진 것처럼 보인다 |
| ★ **미명시** | ★★ **어느 정의가 불렸는지 말해 주는 도구가 없다** — `-O2` 에서 인라인되면 심볼이 **아예 안 남는다** |
| ★★ **UB** | ★★★ **`extern` 타입 불일치는 여섯 벌 중 다섯이 침묵** — ASan·UBSan 은 **원리상 못 본다**(범위 안 읽기). ★ gcc `-flto` 의 경고도 **`cc exit=0`** 이다 |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드가 0인데 ill-formed」는 이 편에서 새 항목이 없다** — 이 편의 위반은 **컴파일이 아니라 링크에서** 죽거나(`exit=1`), **UB 라 진단 의무가 없다.** ★ 대신 「**종료 코드 0인데 UB**」가 (7)에 있다 |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **링크 문제의 창은 컴파일러가 아니라 `nm` 과 링커**다 — 컴파일 단계는 **모든 칸에서 `exit=0`** 이었다.
  - ★★★ **가장 위험한 칸은 (7)** 이다 — 값이 나오고(`0`), 종료 코드가 0 이고, **도구 다섯이 침묵**한다.
  - ★★ **판 격자가 필요한 자리는 (5)와 (8)** 이다 — 하나는 **컴파일러 판**, 하나는 **최적화 수준**이 링크 결과를 바꿨다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 이 파일 안에서만 쓰는 함수·변수 | ★★ **파일 스코프 `static`** | 그냥 전역(이름이 새어 나간다) |
| 여러 파일이 한 변수를 공유 | ★★★ **헤더에 `extern int g;` · 한 `.c` 에 `int g = 0;`** | ★★ 헤더에 `int g;`(잠정 정의 — 판에 달렸다) |
| 함수 호출을 가로질러 값을 남기기 | 함수 안 `static` | 파일 스코프 전역 |
| 헤더에 작은 함수 두기 | ★ **`static inline`** | ★ `inline` 만(외부 정의가 없다) |
| 다른 파일의 이름을 쓰기 | **그 파일의 헤더를 `#include`** | ★★ `extern` 을 손으로 적기(타입이 어긋나도 모른다) |
| 링크가 깨졌을 때 원인 찾기 | ★★ **`nm` 으로 글자를 본다** | 링커 문구만 읽기 |
| 옛 코드의 `multiple definition` | ★ **정의를 한 곳으로 모은다** | `-fcommon` 으로 덮기 |

판단 규칙 두 줄.

- ★★★ **「이 이름을 다른 파일이 알아야 하나」를 먼저 묻는다** — 아니면 **`static`**.
- ★★ **알아야 하면 「정의는 어디 한 곳인가」를 묻는다** — 헤더는 **선언만**, 정의는 **한 `.c`** 에.

## 핵심 문장

- ★★★ **스코프는 「어디서 보이나」, 링크는 「다른 곳의 같은 이름이 같은 물건인가」다.**
- ★★★ **파일 스코프 `static` 은 링크를, 함수 안 `static` 은 저장 기간을 바꾼다** — 그리고 **`nm` 은 둘 다 `b` 로 찍는다.**
- ★★★ **`nm` 의 대문자는 외부 링크, 소문자는 `LOCAL`, `U` 는 이 파일에 정의 없음**이다.
- ★★★ **잠정 정의 두 개는 판에 달렸다** — 기본값(GCC 10 · Clang 11 부터 `-fno-common`)이면 링크 `exit=1`, `-fcommon` 이면 **`C` 둘이 하나로 합쳐진다.**
- ★★ **다른 파일의 `static` 함수는 컴파일 `exit=0` · 링크 `exit=1`** 이다 — `t helper` 대 `U helper`.
- ★★ **`extern` 타입 불일치는 여섯 벌 중 gcc `-flto` 만 경고한다** — 그것도 `cc exit=0` 이다.
- ★★ **C99 `inline` 만으로는 외부 정의가 없다** — `-O0` 에서 링크가 깨지고 `-O2` 에서 통과했다.
- ★ **C++ 는 이름 없는 네임스페이스와 `inline` 변수로 같은 문제를 푼다** — g++ `u` · clang++ `V`.

## 관련 자료

- [`foundations/compiler-pipeline/`](../../../../compiler-pipeline/) — ★★ **경계.** 링커가 **심볼을 어떻게 해석하나** 일반은 그쪽이 정본이다. 여기는 **C 선언이 무슨 심볼을 만드나**만.
- [28번 형제 — 저장 기간 4종을 고르는 법](../28-choosing-among-four-storage-durations/) — ★★★ **직접 선행.** 「`static` 이 자리에 따라 다른 일을 한다」를 거기서 넘겨받았다.
- [25번 형제 — 불완전 타입과 opaque struct](../25-incomplete-types-and-opaque-struct/) — ★★ **두 번역 단위 실험의 앞 편.** `-flto` 가 **서명은 잡고 구조체 레이아웃은 못 잡은** 것을 (7)이 **변수 타입**으로 이었다.
- [30번 형제 — 초기화 규칙과 불확정 값](../30-initialization-rules-and-indeterminate-values/) — ★ `B`/`b` 가 **`.bss`** 인 이유의 정본.
- [31번 형제 — `const` 와 포인터 const 위치](../31-const-and-pointer-const-placement/) — ★ **파일 스코프 `const` 의 링크**(C 는 외부, C++ 은 내부)의 정본.
- [01번 형제 — 선언 문법과 읽는 법](../01-declaration-syntax-and-reading/) — ★ `nm` 의 `T`/`t` 를 **처음 보인** 자리. 여기서는 그것을 **링크 셋 전체**로 넓혔다.
- 목록의 **39번 주제** — `inline` 과 C 의 인라인 규칙. (8)은 **링크 쪽 증상**만 봤다.
- 목록의 **44번 주제** — 헤더와 분할 컴파일. **`extern` 은 헤더, 정의는 한 곳**의 정본.
- 목록의 **45번 주제** — 번역 단위와 링크 오류 읽기. `multiple definition`·`undefined reference` 를 **거꾸로 읽는 법**의 정본.
- ★ **C++ 갈래와 갈리는 자리** — [C++ 06 — 네임스페이스와 ADL](../../../cpp/syntax/06-namespaces-and-adl/)(이름 없는 네임스페이스가 `t` 로 나오는 실측) · C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **25번**(`inline` 변수).

## 용어 풀이

> **스코프(scope)** — 이름이 보이는 **소스 코드의 범위.** 블록 · 파일 · 함수 프로토타입 · 함수 넷이다.\
> 예: `for (int x = 4; …)` 의 `x` 는 루프가 끝나면 안 보인다.

> **링크(linkage)** — 다른 선언의 같은 이름이 **같은 물건을 가리키는가.** 외부 · 내부 · 없음 셋이다.\
> 예: `static int s;` 는 내부 링크라 다른 파일의 `s` 와 남남이다.

> **외부 정의(external definition)** — 파일 스코프에서 **실제로 자리를 만드는** 선언.\
> 예: `int g = 1;` 은 외부 정의고 `extern int g;` 는 아니다.

> **잠정 정의(tentative definition)** — 초기자도 `extern` 도 없는 파일 스코프 객체 선언. **파일 끝까지 다른 정의가 없으면 0 으로 정의**가 된다.\
> 예: `int t;`. 두 파일에 있으면 기본값에서 링크가 깨진다.

> **공용 심볼(common symbol, `nm` 의 `C`)** — 「**자리는 링커가 정해 달라**」는 심볼. 여러 개가 하나로 합쳐진다.\
> 예: `-fcommon` 으로 컴파일한 `int t;` 가 `C t` 로 나온다.

> **인라인 정의(inline definition)** — C99 에서 `extern` 없이 `inline` 만 붙은 외부 함수 정의. **외부 정의를 만들지 않는다.**\
> 예: `inline int twice(int x) {…}` 만 있으면 `nm` 에 `U twice` 가 남는다.

> **`nm`** — 오브젝트 파일의 **심볼 표**를 찍는 도구. 대문자는 전역, 소문자는 지역, `U` 는 미정의다.\
> 예: `0000000000000000 t helper` — 이 파일 안의 `.text` 에 있는 지역 함수.

> **`LOCAL` / `GLOBAL`(ELF 바인딩)** — 심볼이 **이 오브젝트 밖에서 보이나.** `readelf -s` 의 `Bind` 칸이다.\
> 예: 내부 링크도, 함수 안 `static` 도 **`LOCAL`** 이다.

## 더 들어가면

- ★★ **`__attribute__((weak))` 와 약한 심볼(`W`/`V`)** — 정의가 둘이어도 되는 **또 하나의 확장**이다. ★ **던지지 않았다**(C++ `inline` 변수의 `V` 로만 봤다).
- ★★ **정적 라이브러리(`.a`)에서의 `undefined reference`** — 링크 순서가 결과를 바꾸는 자리다. ★ **던지지 않았다**(목록의 **45번 주제**).
- ★ **`-fvisibility=hidden` 과 공유 라이브러리의 심볼 노출** — 외부 링크인데 **`.so` 밖에서는 안 보이는** 제4의 층이다. ★ **던지지 않았다.**
- ★ **GCC 9 이하에서의 (5)** — ★ **못 잰 것**. 이 머신에 없다. 문서로만 적었다.
- ★ **`-flto` 에 구조체 레이아웃 불일치를 주면** — [25번 형제](../25-incomplete-types-and-opaque-struct/)가 이미 **못 잡는다**를 보였다. 여기서는 **다시 던지지 않았다.**
- ★ **`extern inline` 의 gnu89 의미**(`-fgnu89-inline`) — C99 와 **정반대**다. ★ **던지지 않았다**(목록의 **39번 주제**).
