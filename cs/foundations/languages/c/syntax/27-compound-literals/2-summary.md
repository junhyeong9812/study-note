# c/syntax/27 — 복합 리터럴: 「**이름 없는 변수를 식 한가운데 세운다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf)) · [cppreference — Compound literals (C)](https://en.cppreference.com/w/c/language/compound_literal) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·주소·진단·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · **g++ 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **UB 가 걸린 실험은 「컴파일러 2 × 최적화 3」 여섯 벌**을 돌렸다 — 한 벌만 돌리면 **정반대 결론**이 난다(아래 (3)).\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — 복합 리터럴은 **C99 부터**다.\
> ★★ **C23 부터** 복합 리터럴에 **저장 클래스 지정자**를 붙일 수 있다(`(static struct P){1,2}`) — 아래 (6).\
> ★ **gcc 13 은 `-std=c2x` 로 지원하고 clang 18 은 지원하지 않는다**(실측 — `error: expected expression`).\
> ★★ **`-std=` 는 강제가 아니라 기본값 선택**이다 — `-std=c17 -pedantic` 에서 그 문법이 **경고 1건에 `cc exit=0`** 으로 통과했다.
> ★★ **경계** — **구조체 선언·초기화·지정 초기자**는 [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)가 정본이다.\
> 여기는 「**그 초기자 문법을 식 한가운데 놓으면 무엇이 생기나**」만 본다 — ★ **수명과 좌변값성**이 이 편의 값이다.\
> ★ **문자열 리터럴의 저장 기간·수정 금지**는 [20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본이다 — 여기서는 **복합 리터럴과의 대비**로만 쓴다.\
> ★ **자동·정적 저장 기간의 수명 규칙 자체**는 [28번 형제](../28-choosing-among-four-storage-durations/), **포인터 문법**은 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이다.\
> ★ **`sizeof`** 는 [8번 형제](../08-sizeof-alignment-and-offsetof/), **해제 후 사용·댕글링**은 목록의 **57번 주제**, **sanitizer** 는 목록의 **58번 주제**다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · [28번 형제](../28-choosing-among-four-storage-durations/).
> 이 본문은 Claude 작성이다(원고 없음).

## 한눈에 — 쉽게 말하면

**복합 리터럴은 「이름표를 안 붙인 변수」다.**

`3` 이나 `"abc"` 같은 리터럴은 **값**이다. 값에는 주소가 없다.\
그런데 `(struct P){1, 2}` 는 다르다 — **진짜 객체가 하나 생긴다.** 주소도 있고 고칠 수도 있다.\
다른 점은 **이름표가 없다는 것**뿐이다.

- 이름표가 없으니 **그 자리에서 한 번 쓰고 잊는다** — 함수 인자로 넘기기에 알맞다.
- ★★ 그런데 **이름표가 없을 뿐 변수이므로 수명이 있다.** 블록 안이면 **블록이 끝날 때 죽는다.**
- ★★★ 그리고 **루프를 세 바퀴 돌아도 변수는 하나**다 — 이름표만 없지 **선언이 한 번**이기 때문이다.

| 비유 | 실체 | 층 |
|---|---|---|
| 이름표 없는 변수 | `(struct P){1, 2}` — **좌변값**이다 | **표준 (C99부터)** |
| 주소를 잡을 수 있다 | `&(struct P){1, 2}` | **표준** |
| 값을 고칠 수 있다 | `p->x = 99` | **표준** |
| 함수 안에 있으면 블록이 끝날 때 죽는다 | 자동 저장 기간 | **표준** |
| 함수 밖에 있으면 프로그램이 끝날 때까지 산다 | 정적 저장 기간 | **표준** |
| 죽은 뒤에 읽으면 | 댕글링 포인터 | ★★★ **UB — 여섯 벌이 전부 달랐다** |
| ★★ **루프를 돌아도 객체는 하나** | `for(...) a[i] = &(struct P){i, i*i};` | ★★ **관찰 — 이 구현의 선택** |
| `"abc"` 는 못 고치고 `(char[]){"abc"}` 는 고칠 수 있다 | 문자열 리터럴 대 복합 리터럴 | **표준** |
| 저장 클래스를 붙이기 | `(static struct P){1, 2}` | ★★ **C23부터 — gcc 만 됨** |

```text
   struct P { int x, y; };

   ── 함수 밖 ────────────────────────────────────────────
   static struct P *g = &(struct P){10, 20};
                         ^^^^^^^^^^^^^^^^^^ ★ 정적 저장 기간
                         프로그램이 끝날 때까지 산다  -> 10 20 을 읽는다

   ── 함수 안 ────────────────────────────────────────────
   void set(void) {
       keep = &(struct P){1, 2};
              ^^^^^^^^^^^^^^^^^ ★ 자동 저장 기간
   }   <---------------------- ★ 여기서 죽는다

   printf("%d %d", keep->x, keep->y);   -> ★ UB
       gcc  -O0 : 1 2          <- ★ 맞아 보인다. 가장 위험하다
       gcc  -O1 : 289313584 32767
       gcc  -O2 : 0 0
       clang-O0 : 1 2
       clang-O1 : 0 0
       clang-O2 : 518988784 32765
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 좌변값성·수명·저장 기간이 전부 표준에 적혀 있다.
- ★★ 두 번째 무게중심은 「**UB**」다 — **블록이 끝난 뒤에 읽는 것**. 여섯 벌이 **전부 달랐다.**
- ★★ 그리고 이 편에는 **「미명시」 칸에 걸리는 자리**가 하나 있다 — **루프에서 같은 객체가 재사용되는가.**

> **복합 리터럴(compound literal)** — `(타입){초기자}` 꼴로 **식 한가운데에서 이름 없는 객체를 만드는** 문법.\
> 예: `(struct P){.x = 1}`. **C99 부터**다.

> **좌변값(lvalue)** — **객체를 가리키는 식.** 주소를 잡을 수 있고 대입의 왼쪽에 놓일 수 있다.\
> 예: `(struct P){1,2}` 는 좌변값이라 `&` 가 된다. `3` 이나 `f()` 는 아니다.

> **저장 기간(storage duration)** — 그 객체가 **언제 태어나 언제 죽는가.**\
> 예: 복합 리터럴은 **블록 안이면 자동, 파일 스코프면 정적**이다([28번 형제](../28-choosing-among-four-storage-durations/)가 정본).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **이것은 값인가 객체인가** — 주소를 잡을 수 있나, 고칠 수 있나, `sizeof` 는 얼마인가.
2. ★★★ **언제 태어나 언제 죽나** — 그리고 **죽은 뒤에 읽으면 무슨 일이 나나.**
3. ★★ **같은 자리를 여러 번 지나면 객체가 여러 개 생기나** — 그리고 **그것을 어떻게 확인하나.**

## 동작 방식

### (1) ★★★ 복합 리터럴은 값이 아니라 **객체**다

**언제 쓰나** — 「이걸 `&` 로 잡아도 되나」를 물을 때.

```c
/* s27b.c */
#include <stdio.h>

struct P { int x, y; };

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);   /* 죽기 전 출력이 사라지지 않게 */
    printf("1) 좌변값이다 — 멤버를 고칠 수 있다\n");
    struct P *p = &(struct P){1, 2};
    p->x = 99;
    printf("   (%d,%d)\n", p->x, p->y);

    printf("2) 배열 복합 리터럴 — sizeof 가 배열 크기다\n");
    printf("   sizeof (int[]){1,2,3} = %zu · 원소 %zu 개\n",
           sizeof (int[]){1, 2, 3}, sizeof (int[]){1, 2, 3} / sizeof(int));

    printf("3) 지정 초기자를 쓰면 나머지는 0 이다\n");
    struct P q = (struct P){.y = 5};
    printf("   (%d,%d)\n", q.x, q.y);

    printf("4) (char[]){\"abc\"} 는 고칠 수 있다\n");
    char *s = (char[]){"abc"};
    s[0] = 'X';
    printf("   %s\n", s);

    printf("5) \"abc\" 는 문자열 리터럴이라 고치면 죽는다 — 다음 줄에서 끝난다\n");
    char *t = (char *)"abc";
    t[0] = 'X';
    printf("   %s   <- 이 줄은 보이지 않는다\n", t);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27b.c -o x ; ./x (cc exit=0 · run exit=139) =====
1) 좌변값이다 — 멤버를 고칠 수 있다
   (99,2)
2) 배열 복합 리터럴 — sizeof 가 배열 크기다
   sizeof (int[]){1,2,3} = 12 · 원소 3 개
3) 지정 초기자를 쓰면 나머지는 0 이다
   (0,5)
4) (char[]){"abc"} 는 고칠 수 있다
   Xbc
5) "abc" 는 문자열 리터럴이라 고치면 죽는다 — 다음 줄에서 끝난다
```

```text
   리터럴                        복합 리터럴
   ---------------------------  -------------------------------------
   3                            (struct P){1, 2}
   "abc"                        (char[]){"abc"}

   &3            ★ 에러          &(struct P){1,2}     ★ 된다
   3 = 4         ★ 에러          p->x = 99            ★ 된다
   "abc"[0]='X'  ★ 죽는다        (char[]){"abc"}[0]='X'  ★ 된다

   ★ 이름표만 없을 뿐 ★ 변수다.
```

그림 해설 (한 단계씩):

- ★★★ **주소를 잡을 수 있고 멤버를 고칠 수 있다** — `(1,2)` 를 만들어 `p->x = 99` 를 하니 `(99,2)` 가 됐다.
- ★★ **배열 복합 리터럴의 `sizeof` 는 배열 크기**다 — `sizeof (int[]){1,2,3}` 가 **12** 이고 원소가 **3개**다.\
  ★ 포인터로 감쇠하지 않는다. **객체 그 자체**이기 때문이다.
- ★★ **지정 초기자를 쓰면 나머지는 0 이다** — `(struct P){.y = 5}` 가 `(0,5)` 가 됐다([21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)의 규칙 그대로다).
- ★★★ **`(char[]){"abc"}` 는 고칠 수 있고 `"abc"` 는 고치면 죽는다.**\
  앞엣것은 **내 배열 객체**이고 뒤엣것은 **문자열 리터럴**이다([20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본).\
  ★ 실행이 **`run exit=139`(SIGSEGV)** 로 끝났다 — 마지막 줄이 안 찍힌다.
- ★ **소스 첫 줄의 `setvbuf(stdout, NULL, _IONBF, 0)` 가 없으면** 죽기 전 네 항목이 **통째로 사라진다.** 버퍼에 남은 채 프로세스가 끝나기 때문이다.

비용 — **객체가 하나 생긴다.** 값처럼 공짜가 아니다.

### (2) ★★ 저장 기간은 **어디에 썼느냐**로 정해진다

**언제 쓰나** — 복합 리터럴의 주소를 어딘가에 저장하려 할 때.

```c
/* s27a.c */
#include <stdio.h>

struct P { int x, y; };

static struct P *g = &(struct P){10, 20};   /* 파일 스코프 → 정적 저장 기간 */
static struct P *keep;

static void set(void) {
    keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
}                                           /* ★ 여기서 그 객체가 죽는다 */

int main(void) {
    printf("파일 스코프 : %d %d   <- 프로그램이 끝날 때까지 산다\n", g->x, g->y);
    set();
    printf("블록 스코프 : %d %d   <- 블록이 끝난 뒤에 읽었다\n", keep->x, keep->y);

    struct P *a[3];
    for (int i = 0; i < 3; i++) a[i] = &(struct P){i, i * i};
    printf("루프 세 번  : (%d,%d) (%d,%d) (%d,%d)\n",
           a[0]->x, a[0]->y, a[1]->x, a[1]->y, a[2]->x, a[2]->y);
    printf("주소가 같나 : a0==a1 %d · a1==a2 %d\n", a[0] == a[1], a[1] == a[2]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27a.c -o x ; ./x (cc exit=0 · run exit=0) =====
파일 스코프 : 10 20   <- 프로그램이 끝날 때까지 산다
블록 스코프 : 1 2   <- 블록이 끝난 뒤에 읽었다
루프 세 번  : (2,4) (2,4) (2,4)
주소가 같나 : a0==a1 1 · a1==a2 1
```

```text
   파일 스코프                      블록 스코프
   ------------------------------  ------------------------------
   static struct P *g =            void set(void) {
       &(struct P){10, 20};            keep = &(struct P){1, 2};
                                   }
   ★ 정적 저장 기간                 ★ 자동 저장 기간
   프로그램이 끝날 때까지 산다        ★ 닫는 중괄호에서 죽는다

   main 에서 g->x 를 읽는다   OK    main 에서 keep->x 를 읽는다   ★ UB
```

그림 해설 (한 단계씩):

- ★★★ **파일 스코프면 정적**이다 — `10 20` 을 언제 읽어도 살아 있다.
- ★★★ **블록 스코프면 자동**이다 — `set()` 의 닫는 중괄호에서 **그 객체가 죽는다.**\
  ★ 기본 빌드(`-O0`)에서는 **`1 2` 가 찍힌다** — **맞아 보인다.** 그것이 함정이다((3)에서 흔든다).
- ★★ **루프 세 번이 전부 `(2,4)`** 다. 주소 비교도 `a0==a1 1 · a1==a2 1` — **세 포인터가 같은 객체**를 가리킨다.\
  ★ 값만 보면 「마지막 값이 덮어쓴 것」처럼 보이는데, **주소를 찍어야** 「애초에 하나였다」가 보인다((4)).
- ★ **이 문단의 규칙은 [28번 형제](../28-choosing-among-four-storage-durations/)의 자동·정적 규칙 그대로**다. 복합 리터럴만의 새 규칙이 아니다.

비용 — **어디에 썼느냐가 수명을 정한다.** 같은 문법인데 자리에 따라 결과가 갈린다.

### (3) ★★★ 죽은 뒤에 읽으면 — **여섯 벌이 전부 달랐다**

**언제 쓰나** — 「`-O0` 에서 잘 되던데」를 근거로 쓰려 할 때. **이 편의 본체다.**

```text
===== 블록이 끝난 복합 리터럴을 읽으면 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : 1 2 | (2,4) (2,4) (2,4)
gcc   -O1 : -1225351904 32766 | (0,0) (0,0) (0,0)
gcc   -O2 : 0 0 | (0,0) (0,0) (0,0)
clang -O0 : 1 2 | (2,4) (2,4) (2,4)
clang -O1 : 0 0 | (2,4) (2,4) (2,4)
clang -O2 : 672393392 32766 | (2,4) (2,4) (2,4)
```

```text
===== 같은 소스에 경고가 몇 건 나오나 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : cc exit=0 · 경고 1건 : [-Wdangling-pointer=] 
gcc   -O1 : cc exit=0 · 경고 5건 : [-Wdangling-pointer=] [-Wuninitialized] 
gcc   -O2 : cc exit=0 · 경고 7건 : [-Wdangling-pointer=] [-Wuninitialized] 
clang -O0 : cc exit=0 · 경고 0건 : 
clang -O1 : cc exit=0 · 경고 0건 : 
clang -O2 : cc exit=0 · 경고 0건 : 
```

```text
   같은 소스 · 같은 UB · 여섯 가지 결과

                블록 스코프를 읽은 값      루프 세 번
   gcc   -O0  : 1 2                      (2,4) (2,4) (2,4)   ★ 맞아 보인다
   gcc   -O1  : 289313584 32767          (0,0) (0,0) (0,0)   ★ 스택 잔해
   gcc   -O2  : 0 0                      (0,0) (0,0) (0,0)
   clang -O0  : 1 2                      (2,4) (2,4) (2,4)   ★ 맞아 보인다
   clang -O1  : 0 0                      (2,4) (2,4) (2,4)
   clang -O2  : 518988784 32765          (2,4) (2,4) (2,4)   ★ 스택 잔해

   ★ 「값」만 보면 ★ 두 벌이 정답처럼 보인다.
   ★ 그리고 clang 은 여섯 벌 전부 ★ 경고 0건이다.
```

그림 해설 (한 단계씩):

- ★★★ **여섯 벌이 전부 다르다.** `1 2`(맞아 보임) · 스택 잔해 · `0 0` 이 뒤섞였다.\
  ★★ **한 벌만 돌리고 「되던데」로 결론을 세우면 정반대가 된다** — `-O0` 두 벌이 하필 **맞아 보이는 쪽**이다.
- ★★★ **gcc 와 clang 의 경고가 정반대다.**

  | | gcc | clang |
  |---|---|---|
  | `-O0` | **1건** `[-Wdangling-pointer=]` | **0건** |
  | `-O1` | **5건** `[-Wdangling-pointer=]` `[-Wuninitialized]` | **0건** |
  | `-O2` | **7건** `[-Wdangling-pointer=]` `[-Wuninitialized]` | **0건** |

  ★★★ **clang 18 은 여섯 벌 전부 침묵**이다. 「경고 0건이니 괜찮다」가 **여기서 깨진다.**
- ★★★ **gcc 의 경고 건수가 최적화 수준에 따라 늘어난다**(1 → 5 → 7). **최적화를 올려야 더 보인다** — 「빠른 빌드로 검사하고 느린 빌드로 배포」가 거꾸로다.
- ★★ **여섯 벌 전부 `cc exit=0`** 이다. UB 인데 빌드는 다 통과한다.
- ★ **gcc `-O1`·clang `-O2` 의 숫자는 실행마다 바뀐다**(스택 잔해).\
  대조할 것은 숫자가 아니라 「**여섯 벌이 서로 다르다**」는 성질이다.

비용 — **테스트가 통과할 수 있다.** 그것도 **가장 흔한 빌드(`-O0`)에서** 통과한다.

### (4) ★★★ 루프를 세 바퀴 돌아도 **객체는 하나** — 네 번째 창은 **주소**다

**언제 쓰나** — 복합 리터럴의 주소를 여러 개 모으려 할 때.

```text
   for (int i = 0; i < 3; i++) a[i] = &(struct P){i, i * i};

   기대 — 객체 세 개                       실제 — 객체 하나
   ------------------------------------   ------------------------------------
   a[0] -> (0,0)                          a[0] ─┐
   a[1] -> (1,1)                          a[1] ─┼─> ★ 같은 객체
   a[2] -> (2,4)                          a[2] ─┘

   값만 보면            (2,4) (2,4) (2,4)   <- 「덮어쓴 건가?」로 읽힌다
   주소를 비교하면       a0==a1 1 · a1==a2 1 <- ★ 「애초에 하나였다」
```

그림 해설 (한 단계씩):

- ★★★ **값만 보면 진단이 안 된다.** `(2,4)` 셋이 나오면 「루프 마지막 값이 덮어썼나」·「포인터가 잘못 들어갔나」로 읽히는데, 원인은 「**객체가 하나였다**」다.
- ★★★ **주소를 비교해야 갈린다** — `a[0] == a[1]` 이 `1` 이고 `a[1] == a[2]` 도 `1` 이다.\
  ★★ **이것이 이 주제의 네 번째 창**이다: **값이 아니라 「같은 객체인가」를 묻는 것.**
- ★★ 복합 리터럴은 「**그 블록에 딸린 객체**」다. 루프 몸통이 블록이지만, gcc·clang 은 **여섯 벌 전부 한 객체**로 잡았다.\
  ★ **이것은 관찰이지 보장이 아니다** — 「매 반복마다 새 객체」로 잡는 구현이 있어도 이 문서는 그것을 반증하지 못한다.
- ★★ **(3)의 격자에서 이 열을 보면** — gcc `-O1`/`-O2` 는 `(0,0)` 을 주고 clang 은 세 벌 다 `(2,4)` 를 준다.\
  ★ 값이 갈리는 것은 **블록이 끝난 뒤에 읽는 UB** 때문이고, **「객체가 하나」라는 사실 자체는 여섯 벌 전부 같았다.**
- ★ **고치는 법** — 세 객체가 필요하면 **이름 있는 배열**을 만든다: `struct P buf[3]; … a[i] = &buf[i];`

비용 — **가장 자연스러운 오해**다. 그리고 **값을 아무리 들여다봐도 안 풀린다.**

### (5) ★★ sanitizer 는 잡는다 — 세 창 중 유일하게

**언제 쓰나** — 「(3)의 UB 를 실제로 잡으려면」을 물을 때.

```c
/* s27d.c */
#include <stdio.h>

struct P { int x, y; };
static struct P *keep;

static void set(void) { keep = &(struct P){1, 2}; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    set();
    printf("블록이 끝난 복합 리터럴을 읽는다\n");
    printf("%d %d\n", keep->x, keep->y);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -fsanitize=address s27d.c -o x ; ASAN_OPTIONS=strip_path_prefix=/src/ ./x 2>&1 | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
블록이 끝난 복합 리터럴을 읽는다
=================================================================
==1123143==ERROR: AddressSanitizer: stack-use-after-scope on address 0x79dfbe300024 at pc 0x5edb2d4f9476 bp 0x7fff9ea21bb0 sp 0x7fff9ea21ba0
READ of size 4 at 0x79dfbe300024 thread T0
    #0 0x5edb2d4f9475 in main (x+0x1475) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)
    #1 0x79dfc042a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x79dfc042a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5edb2d4f91c4 in _start (x+0x11c4) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)

Address 0x79dfbe300024 is located in stack of thread T0 at offset 36 in frame
    #0 0x5edb2d4f9298 in main (x+0x1298) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)

  This frame has 1 object(s):
    [32, 40) '<unknown>' <== Memory access at offset 36 is inside this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-scope (x+0x1475) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec) in main
```

```text
   세 창                         이 UB 에 대해
   ---------------------------  -----------------------------------------
   컴파일 진단                    gcc 는 본다 (1~7건) · ★ clang 은 0건
   실행 출력                      ★ -O0 에서는 ★ 정답처럼 보인다
   sanitizer                     ★ 정확히 잡는다 — stack-use-after-scope

   ASAN_OPTIONS=strip_path_prefix=/src/ 로 절대 경로를 지웠다.
```

그림 해설 (한 단계씩):

- ★★★ **ASan 이 `stack-use-after-scope` 로 정확히 잡는다** — `READ of size 4` · `Address … is located in stack of thread T0 at offset 36 in frame` · `run exit=1`.
- ★★ 「**이 프레임에 객체가 1개**」라고까지 적어 준다(`This frame has 1 object(s)`) — **(4)의 「객체가 하나」를 ASan 이 독립적으로 확인해 준 셈**이다.
- ★★ **`-O1` 로 돌렸다.** `-O0` 에서도 잡히지만, **(3)에서 `-O0` 이 「맞아 보이는」 벌**이라 굳이 최적화를 켠 쪽을 실었다.
- ★ **흔들리는 칸** — PID(`==NNNN==`) · `pc`/`bp`/`sp` · 스택 주소 · 모듈 오프셋 · BuildId.\
  **안 흔들리는 칸** — `stack-use-after-scope` · `READ of size 4` · `offset 36 in frame` · `This frame has 1 object(s)` · `run exit=1`.
- ★ **sanitizer 가 유일한 자동 방어선**이다 — clang 의 정적 진단이 0건이므로, **clang 만 쓰는 빌드에서는 ASan 이 없으면 아무것도 안 잡힌다.**

비용 — **실행해야 한다.** 그 경로를 실제로 지나가는 테스트가 있어야 잡힌다.

### (6) ★★ C23 — 저장 클래스를 붙일 수 있다 (그런데 한쪽만)

**언제 쓰나** — 블록 안에서 만든 복합 리터럴을 **오래 살리고** 싶을 때.

```c
/* s27e.c */
#include <stdio.h>

struct P { int x, y; };
static struct P *keep;

/* ★ C23 부터 복합 리터럴에 저장 클래스 지정자를 붙일 수 있다 */
static void set(void) { keep = &(static struct P){1, 2}; }

int main(void) {
    set();
    printf("static 복합 리터럴 : %d %d\n", keep->x, keep->y);
    return 0;
}
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -O2 s27e.c -o x ; ./x (cc exit=0 · run exit=0) =====
static 복합 리터럴 : 1 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27e.c -o x (cc exit=0) =====
s27e.c: In function ‘set’:
s27e.c:7:50: warning: ISO C forbids storage class specifiers in compound literals before C2X [-Wpedantic]
    7 | static void set(void) { keep = &(static struct P){1, 2}; }
      |                                                  ^
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic s27e.c -o x (cc exit=1) =====
s27e.c:7:34: error: expected expression
    7 | static void set(void) { keep = &(static struct P){1, 2}; }
      |                                  ^
1 error generated.
```

```text
   같은 소스 · 세 가지 결과

   gcc   -std=c2x -pedantic -O2 : ★ cc exit=0 · 실행되어 1 2  <- 죽지 않는다
   gcc   -std=c17 -pedantic     : ★ cc exit=0 · warning 1건
                                  "ISO C forbids storage class specifiers
                                   in compound literals before C2X"
   clang -std=c2x -pedantic     : ★ cc exit=1 · error: expected expression

   ★ gcc 는 C17 모드에서도 ★ 받아 준다 (경고만).
   ★ clang 18 은 C23 모드에서도 ★ 못 알아듣는다.
```

그림 해설 (한 단계씩):

- ★★★ **`(static struct P){1, 2}` 는 정적 저장 기간이 된다** — `-O2` 로 돌려도 **`1 2`** 가 나온다. (2)·(3)의 UB 가 **문법 한 낱말로 사라진다.**
- ★★★ **`-std=c17 -pedantic` 에서도 gcc 는 통과시킨다** — 경고 1건에 **`cc exit=0`** 이다.\
  ★ 「`-std=c17` 로 돌렸으니 C17 로 검증했다」가 **여기서 깨진다.** 빌드를 막으려면 **`-pedantic-errors`** 다.
- ★★★ **clang 18 은 C23 모드에서도 못 알아듣는다** — `error: expected expression` 이고 **`cc exit=1`** 이다.\
  ★ **「C23 기능이니 쓰면 된다」가 아니다** — 기능마다 구현 지원이 다르다.
- ★ **이식성을 생각하면 아직 쓰지 않는 쪽**이 맞다. 같은 효과는 **이름 있는 `static` 변수**로 얻을 수 있다.

비용 — **한쪽 컴파일러에서만 빌드된다.** 지금은 그 대가가 크다.

**(6-나) ★★★ `-std=` 라는 철자 자체도 컴파일러마다 다르다**

```text
===== 같은 철자의 -std= 를 두 컴파일러에 던져 본다 — s27e.c 대신 최소 프로그램으로 (exit=0) =====
gcc   -std=c17  : cc exit=0 · 경고 0건  
clang -std=c17  : cc exit=0 · 경고 0건  
gcc   -std=c2x  : cc exit=0 · 경고 0건  
clang -std=c2x  : cc exit=0 · 경고 0건  
gcc   -std=c23  : cc exit=1 · 경고 0건  gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
clang -std=c23  : cc exit=0 · 경고 0건  
```

- ★★★ **`-std=c23` 은 gcc 13 에 없다** — `unrecognized command-line option` 이고 **`cc exit=1`** 인데 **경고는 0건**이다.\
  ★★ 「경고 0건」만 세는 스크립트는 이것을 **「깨끗한 빌드」로 기록한다.** **종료 코드를 같이 봐야** 뜻이 산다.
- ★★★ **같은 철자를 clang 18 은 받아 준다**(`cc exit=0`). **`-std=c2x` 는 둘 다** 받는다.\
  ★ 즉 **「이 철자가 되나」는 표준 버전의 문제가 아니라 그 컴파일러의 문제**다.
- ★★ **그래서 「`-std=c23` 으로 돌려 봤는데 아무 경고도 없더라」는 두 가지 뜻**이 될 수 있다 —\
  **정말 깨끗하거나, 컴파일 자체가 안 된 것**이거나. **`cc exit` 를 안 보면 못 가른다.**
- ★ 이 문서는 **`-std=c2x` 로 고정**했다 — 두 컴파일러가 다 받는 철자이기 때문이다.

### (7) ★★ 함수 인자 자리에서 — 이 문법이 값을 내는 곳

**언제 쓰나** — 선택 인자가 많은 함수를 부를 때. **이 문법의 본래 용도다.**

```c
/* s27c.c */
#include <stdio.h>

struct Opt { int retries; int timeout_ms; const char *tag; };

static void connect_to(const char *host, struct Opt o) {
    printf("%-8s retries=%d timeout=%dms tag=%s\n",
           host, o.retries, o.timeout_ms, o.tag ? o.tag : "(없음)");
}

static int sum(const int *a, int n) { int s = 0; for (int i = 0; i < n; i++) s += a[i]; return s; }

int main(void) {
    /* ★ 임시 구조체를 그 자리에서 만들어 넘긴다 — 이름 붙은 인자처럼 읽힌다 */
    connect_to("db",    (struct Opt){.retries = 3, .timeout_ms = 500, .tag = "primary"});
    connect_to("cache", (struct Opt){.timeout_ms = 50});
    connect_to("log",   (struct Opt){0});

    /* 배열도 그 자리에서 만들어 넘긴다 */
    printf("sum = %d\n", sum((int[]){1, 2, 3, 4, 5}, 5));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27c.c -o x ; ./x (cc exit=0 · run exit=0) =====
db       retries=3 timeout=500ms tag=primary
cache    retries=0 timeout=50ms tag=(없음)
log      retries=0 timeout=0ms tag=(없음)
sum = 15
```

```text
   옵션 구조체를 넘기는 세 가지 형태

   ① 변수를 만든다                 ② 복합 리터럴                    ③ 인자를 늘린다
   struct Opt o = {0};             connect_to("db",                connect_to("db",3,500,"p");
   o.retries = 3;                      (struct Opt){                ★ 순서를 외워야 한다
   o.timeout_ms = 500;                   .retries = 3,              ★ 기본값을 못 준다
   connect_to("db", o);                  .timeout_ms = 500});
   ★ 이름을 하나 더 만든다          ★ 그 자리에서 끝난다

   ★ (struct Opt){0} 하나로 ★ 전부 기본값이 된다.
```

그림 해설 (한 단계씩):

- ★★ **지정 초기자와 짝을 이루면 「이름 붙은 인자」처럼 읽힌다** — `.retries = 3, .timeout_ms = 500`.
- ★★ **안 적은 멤버는 0 이 된다** — `cache` 는 `retries=0`, `log` 는 `(struct Opt){0}` 하나로 **전부 기본값**이다.
- ★ **배열도 그 자리에서 만들어 넘긴다** — `sum((int[]){1,2,3,4,5}, 5)` 가 **15** 를 준다.\
  ★ 여기서는 **인자 자리의 복합 리터럴이 호출이 끝날 때까지는 살아 있다** — 그 블록이 아직 안 끝났으니까.
- ★★ **이 용법은 안전하다** — **주소를 함수 밖으로 저장하지 않기** 때문이다. (3)의 UB 는 **주소를 오래 들고 있을 때**만 난다.
- ★ **경고 0건**이다 — gcc 도 clang 도 할 말이 없다.

비용 — **없다.** 이 자리가 복합 리터럴의 **옳은 쓰임**이다.

### (8) ★ C++ 에서는 문법 자체가 다르다

**언제 쓰나** — C 코드를 C++ 로 옮기거나 공용 헤더를 쓸 때.

```c
/* s27f.cpp */
#include <cstdio>

struct P { int x, y; };
static P *keep;

static void set(void) { keep = &(P){1, 2}; }   /* C 에서는 되던 줄 */

int main(void) { set(); std::printf("%d %d\n", keep->x, keep->y); return 0; }
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s27f.cpp -o x (cc exit=1) =====
s27f.cpp: In function ‘void set()’:
s27f.cpp:6:41: warning: ISO C++ forbids compound-literals [-Wpedantic]
    6 | static void set(void) { keep = &(P){1, 2}; }   /* C 에서는 되던 줄 */
      |                                         ^
s27f.cpp:6:36: error: taking address of rvalue [-fpermissive]
    6 | static void set(void) { keep = &(P){1, 2}; }   /* C 에서는 되던 줄 */
      |                                    ^~~~~~
```

```text
   같은 줄 — keep = &(P){1, 2};

   C   : ★ 좌변값이다        -> & 가 된다 (그리고 블록 끝까지 산다)
   C++ : ★ 우변값이다        -> ★ error: taking address of rvalue
         그리고 애초에 ★ ISO C++ 에 복합 리터럴이 없다 (g++ 확장)

   ★ C 에서 「수명이 블록 끝까지」라 조심하던 문법이
   ★ C++ 에서는 ★ 주소를 못 잡아서 그 사고가 아예 안 난다.
```

- ★★★ **C 에서는 좌변값, C++ 에서는 우변값**이다. 그래서 `&(P){1,2}` 가 **C 에서는 되고 C++ 에서는 에러**(`taking address of rvalue`)다.
- ★★ **복합 리터럴 자체가 ISO C++ 에 없다** — g++ 는 확장으로 받고 `ISO C++ forbids compound-literals [-Wpedantic]` 로 알린다.
- ★ **그래서 이 편의 UB 가 C++ 에서는 문법 단계에서 막힌다** — 같은 이름의 문법인데 **위험의 모양이 다르다.**\
  ★ 자세한 것은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) 쪽이다.

## 문법 — 형태와 규칙

### 형태

```text
/* 구조체 */
(struct P){1, 2}                  /* 순서대로 */
(struct P){.y = 5}                /* 지정 초기자 — 나머지는 0 */
(struct P){0}                     /* 전부 0 */

/* 배열 — 길이를 적어도 되고 안 적어도 된다 */
(int[]){1, 2, 3}                  /* sizeof 는 12 */
(int[5]){1, 2}                    /* 나머지는 0 */
(char[]){"abc"}                   /* ★ 고칠 수 있는 char 배열 */

/* 좌변값이므로 */
&(struct P){1, 2}                 /* 주소를 잡는다 */
(struct P){1, 2}.x                /* 멤버를 읽는다 */
p = &(struct P){1, 2}; p->x = 9;  /* 고친다 */

/* 저장 기간 */
static struct P *g = &(struct P){1,2};   /* 파일 스코프 -> ★ 정적 */
void f(void) { p = &(struct P){1,2}; }   /* 블록 스코프 -> ★ 자동 */

/* C23부터 — 저장 클래스 지정자 */
(static struct P){1, 2}           /* gcc 13 -std=c2x 에서 확인 · clang 18 은 에러 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```text
struct P { int x, y; };
static struct P *keep;

void f(void) { keep = &(struct P){1, 2}; }
/* ★★★ 블록이 끝나면 죽는다. keep 을 읽는 것은 ★ UB
   gcc -O0 은 1 2 를 주고 clang -O2 는 쓰레기를 준다 — 여섯 벌이 다 달랐다 */

struct P *g(void) { return &(struct P){1, 2}; }
/* ★★★ 같은 UB — 지역 변수 주소를 돌려주는 것과 같다 */

for (int i=0;i<3;i++) a[i] = &(struct P){i, i*i};
/* ★★ 세 포인터가 ★ 같은 객체를 가리킨다. 값만 보면 「덮어썼나」로 읽힌다 */

(struct P){1,2} = q;              /* 좌변값이지만 ★ 배열·구조체 대입 규칙을 따른다 */

"abc"[0] = 'X';                   /* ★ 문자열 리터럴 — SIGSEGV (run exit=139) */
(char[]){"abc"}[0] = 'X';         /* ★ 복합 리터럴 — 된다 */

(static struct P){1,2}            /* ★★ C23부터. -std=c17 에서 gcc 는 경고 + cc exit=0
                                     clang 18 은 -std=c2x 에서도 ★ cc exit=1 */

&(P){1, 2}                        /* ★★ C++ 에서는 error: taking address of rvalue */
```

### 규칙 불릿

- ★★★ **복합 리터럴은 좌변값**이다 — **주소를 잡을 수 있고 고칠 수 있다.** 이 한 줄이 이 주제의 발판이다.
- ★★★ **저장 기간은 「어디에 썼느냐」로 정해진다** — 블록 안이면 **자동**, 파일 스코프면 **정적**이다.
- ★★★ **블록이 끝난 뒤에 읽는 것은 UB** 이고, **여섯 벌이 전부 달랐다.** `-O0` 두 벌은 **맞아 보인다.**
- ★★★ **clang 18 은 이 UB 에 경고 0건**이다. gcc 는 `-O0` 1건 → `-O1` 5건 → `-O2` 7건으로 **최적화를 올려야 는다.**
- ★★ **루프를 돌아도 객체는 하나**였다(여섯 벌 전부). ★ **관찰이지 보장이 아니다** — 값이 아니라 **주소를 비교해야** 보인다.
- ★★ **배열 복합 리터럴의 `sizeof` 는 배열 크기**다(`sizeof (int[]){1,2,3}` = 12). 포인터로 감쇠하지 않는다.
- ★★ **`(char[]){"abc"}` 는 고칠 수 있고 `"abc"` 는 못 고친다** — 뒤엣것은 `run exit=139` 로 죽는다.
- ★★ **함수 인자 자리에서 쓰는 것은 안전하다** — 주소를 밖으로 저장하지 않기 때문이다. **이것이 본래 용도**다.
- ★★ **C23 부터 저장 클래스 지정자**를 붙일 수 있다. **gcc 13 은 `-std=c2x` 에서 되고 clang 18 은 안 된다.**
- ★ **`-std=c17 -pedantic` 에서 그 C23 문법이 경고 1건에 `cc exit=0`** 으로 통과한다. 막으려면 `-pedantic-errors`.
- ★ **ASan 이 `stack-use-after-scope` 로 잡는다** — clang 빌드에서는 **유일한 방어선**이다.
- ★ **C++ 에서는 우변값**이라 `&` 가 **에러**다. 그리고 문법 자체가 **ISO C++ 에 없다.**

## 어디서 틀리나

### 1. ★★★ 「`-O0` 에서 `1 2` 가 나오던데」

**여섯 벌 중 두 벌만 그렇다**((3)). `-O1` 로 한 칸만 올리면 gcc 는 스택 잔해를, clang 은 `0 0` 을 준다.\
★★ **그리고 하필 맞아 보이는 두 벌이 가장 흔한 빌드**다. **한 벌짜리 실험은 여기서 정반대 결론을 준다.**

### 2. ★★★ 「경고가 0건이니 괜찮겠지」

**clang 18 은 여섯 벌 전부 0건**이다((3)). 같은 소스에 gcc 는 최대 7건을 낸다.\
★★ **「경고 0건」은 「그 컴파일러가 아무 말도 안 했다」는 뜻일 뿐**이다. 두 컴파일러를 던지거나 **ASan 을 켠다.**

### 3. ★★★ 「루프에서 값이 다 같길래 덮어쓴 줄 알았다」

**애초에 객체가 하나**다((4)). **값으로는 두 가설을 못 가른다** — `a[0] == a[1]` 을 찍어야 갈린다.\
★ 세 객체가 필요하면 **이름 있는 배열**을 만든다.

### 4. ★★ 「`&(struct P){…}` 를 반환하면 편하던데」

**지역 변수 주소를 반환하는 것과 같은 UB** 다. gcc 는 `[-Wdangling-pointer=]` 로 잡고 clang 은 **아무 말이 없다.**\
★ 돌려주려면 **`malloc` 하거나 호출자가 준 자리에 채운다.**

### 5. ★★ 「`(static struct P){…}` 를 쓰면 되겠네」

**gcc 에서만 빌드된다**((6)). clang 18 은 **`-std=c2x` 에서도 `cc exit=1`** 이다.\
★ 같은 효과를 **이름 있는 `static` 변수**로 얻을 수 있고 그쪽은 어디서나 빌드된다.

### 6. ★★ 「`-std=c17` 로 돌렸으니 C17 코드다」

**아니다**((6)). C23 전용 문법이 **경고 1건에 `cc exit=0`** 으로 통과했다.\
★ **`-pedantic-errors`** 라야 빌드가 멈춘다.

### 7. ★ 「`(char[]){"abc"}` 나 `"abc"` 나 같은 거 아닌가」

**정반대다**((1)). 앞엣것은 **내 배열이라 고칠 수 있고**, 뒤엣것은 고치면 **`run exit=139`** 다.\
★ 문자열 리터럴 쪽은 [20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본이다.

### 8. ★ 「함수 인자에 쓰는 것도 위험한 거 아닌가」

**안전하다**((7)). 그 블록이 아직 안 끝났고 **주소를 밖으로 저장하지 않기** 때문이다.\
★ 위험해지는 것은 **주소를 오래 들고 있을 때**뿐이다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 좌변값성·저장 기간·`sizeof` 가 전부 거기 있다.\
★★ 두 번째는 「**UB**」인데 자리는 하나다 — **블록이 끝난 뒤에 읽는 것.** 다만 그 하나가 **여섯 벌로 갈린다.**\
★★ 그리고 「**미명시**」 칸에 한 자리가 있다 — **루프에서 같은 객체가 재사용되는가.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | **좌변값인 것**(주소·수정) · **블록 안이면 자동, 파일 스코프면 정적**인 것 · **배열 복합 리터럴의 `sizeof` 가 배열 크기**인 것 · 지정 초기자의 **나머지 0** 규칙 · **`(char[]){"abc"}` 는 수정 가능**한 것 · C99 부터인 것 | `p->x = 99` → `(99,2)` · 파일 스코프 `10 20` 이 살아 있음 · `sizeof (int[]){1,2,3}` = **12** · `(struct P){.y=5}` → `(0,5)` · `(char[]){"abc"}[0]='X'` → `Xbc` |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ **얇다.** 진단 문구·플래그 이름 · **C23 저장 클래스 지정자의 지원 여부** · `-pedantic` 의 심각도 | gcc `[-Wdangling-pointer=]`·`[-Wuninitialized]` 대 clang **0건** · gcc `-std=c2x` **통과** 대 clang 18 **`cc exit=1`** |
| ★★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★★ **루프를 돌 때 같은 객체가 재사용되는가** — 이 구현에서는 **여섯 벌 전부 하나**였다 | `a[0]==a[1]` = 1 · `a[1]==a[2]` = 1 · ASan 이 `This frame has 1 object(s)` 라고 적음 |
| ★★ **UB (자리는 하나)** | 아무 일이나 | ★★★ **블록이 끝난 뒤에 그 객체를 읽는 것** | ★★ **여섯 벌** — `1 2` · `289313584 32767` · `0 0` · `1 2` · `0 0` · `518988784 32765`. **전부 `cc exit=0` · `run exit=0`** · ASan `stack-use-after-scope`(`run exit=1`) |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★ 여기는 도구가 잘 본다 — 문법 오류는 컴파일 에러다. ★★ 다만 **「이것이 객체다」라고 말해 주는 도구가 없다** — `&` 가 통과한다는 사실 말고는 표시가 없어서, **값처럼 읽고 지나가기 쉽다** |
| **조건부 표준** | ★ **해당 없음** |
| ★ **구현 정의** | ★★ **C23 저장 클래스 지정자를 지원하는지 말해 주는 것은 에러 메시지뿐**이다. gcc 는 `-std=c17` 에서도 받아 주고 clang 은 `-std=c2x` 에서도 안 받는다 — **`-std=` 만 보고는 알 수 없다** |
| ★★ **미명시** | ★★★ **「객체가 하나인가 셋인가」를 말해 주는 경고가 없다.** 값은 `(2,4)` 셋으로 **그럴듯하게** 나오고, **주소를 비교해야만** 보인다. ★ 이것이 이 주제의 **네 번째 창**이다 |
| ★★ **UB** | ★★★ **clang 18 은 여섯 벌 전부 경고 0건**이다 — **정적 진단만 믿는 빌드에서는 아무것도 안 걸린다.** ★★ gcc 도 **`-O0` 에서는 1건뿐**이고 최적화를 올려야 는다(1 → 5 → 7). ★ **ASan 이 유일하게 확실하다**(`stack-use-after-scope`) |
| ★★ **(층을 가로지름)** | ★★ **「종료 코드가 0인데 ill-formed」가 두 군데**다 — ① `-std=c17 -pedantic` 에서 C23 저장 클래스 지정자가 **경고 1건에 `cc exit=0`** ② **UB 여섯 벌 전부 `cc exit=0`**. ★ 앞엣것은 `-pedantic-errors` 로 막히고 **뒤엣것은 막을 플래그가 없다** |

- ★★ **이 표의 결론 네 줄**
  - ★★★ 가장 위험한 것은 「**맞아 보이는 출력**」이다 — `-O0` 두 벌이 `1 2` 를 준다. **가장 흔한 빌드가 가장 조용하다.**
  - ★★★ **두 번째는 컴파일러 간 비대칭**이다 — 같은 소스에 gcc 는 최대 7건, clang 은 0건이다. **한쪽만 쓰면 이 주제 전체가 무방비**다.
  - ★★ 세 번째는 「**객체가 하나**」다 — 값으로는 원인 진단이 안 되고 **주소 비교**라는 창을 따로 열어야 한다.
  - ★ **`-std=` 로는 C23 지원 여부를 알 수 없다.** 실제로 던져 보는 수밖에 없다.

### 이 주제의 네 번째 창 — **주소 동일성 검사**

- **컴파일 진단**은 gcc 에서만 말한다 — clang 은 **0건**이다.
- **실행 출력**은 `-O0` 에서 **정답처럼 보인다** — 창이 아니라 **함정**이다.
- **ASan** 은 (3)의 UB 는 잡지만 **(4)의 「객체가 하나」에는 할 말이 없다** — 그것은 UB 가 아니기 때문이다.
- ★★ 그래서 네 번째 창은 「**포인터끼리 `==` 로 비교하는 것**」이다.\
  `a[0] == a[1]` 이 `1` 이면 **애초에 한 객체**이고, `0` 이면 **덮어쓴 것**이다. **값으로는 이 둘이 구분되지 않는다.**
- ★ 그 창을 여는 비용은 `printf("%d", a[0]==a[1])` **한 줄**이다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 옵션 구조체를 한 번만 넘기기 | ★★ **`f(x, (struct Opt){.a=1, .b=2})`** | 인자를 늘려 순서 외우기 |
| 전부 기본값으로 넘기기 | `(struct Opt){0}` | 필드마다 0 을 쓰기 |
| 임시 배열을 넘기기 | `sum((int[]){1,2,3}, 3)` | 지역 배열 변수를 따로 만들기 |
| 고칠 수 있는 짧은 문자열 | ★ **`(char[]){"abc"}`** | ★★ `char *s = "abc";` 뒤에 수정(죽는다) |
| 그 주소를 **오래** 들고 있기 | ★★★ **`malloc` 또는 이름 있는 `static` 변수** | ★★★ 블록 안 복합 리터럴의 `&` |
| 함수에서 돌려주기 | `malloc` 또는 **호출자가 준 자리에 채우기** | `return &(struct P){…};` |
| 객체를 여러 개 만들기 | ★★ **이름 있는 배열** `struct P buf[3]` | ★★ 루프 안 복합 리터럴의 `&` (하나다) |
| 오래 살리는 문법을 쓰기 | ★ 이름 있는 `static` 변수 | ★ `(static struct P){…}`(gcc 만 된다) |
| 이 UB 를 잡기 | ★★ **ASan** + **gcc 로도 한 번 컴파일** | ★★ clang 의 경고만 믿기 |
| C++ 와 공유하는 헤더 | ★ 복합 리터럴을 피한다 | 그냥 두기(우변값이라 `&` 가 에러다) |

판단 규칙 두 줄.

- ★★★ **그 자리에서 쓰고 버리면 안전하고, 주소를 블록 밖으로 내보내는 순간 위험하다.**
- ★★ **「값이 맞아 보이는 것」을 근거로 쓰지 마라** — 이 주제에서는 **가장 흔한 빌드가 가장 그럴듯한 거짓말**을 한다.

## 핵심 문장

- ★★★ **복합 리터럴은 값이 아니라 이름 없는 객체**다 — **주소를 잡을 수 있고 고칠 수 있다.**
- ★★★ **저장 기간은 어디에 썼느냐로 정해진다** — 블록 안이면 자동, 파일 스코프면 정적.
- ★★★ **블록이 끝난 뒤에 읽으면 UB** 이고 **여섯 벌이 전부 달랐다** — 그중 **`-O0` 두 벌은 맞아 보인다.**
- ★★★ **clang 18 은 그 UB 에 경고 0건**이고 gcc 는 **`-O0` 1건 → `-O2` 7건**이다. **최적화를 올려야 더 보인다.**
- ★★ **루프를 세 바퀴 돌아도 객체는 하나**였다 — `a[0]==a[1]` 이 `1` 이다. **값이 아니라 주소로만 보인다.**
- ★★ **배열 복합 리터럴의 `sizeof` 는 배열 크기**다(`(int[]){1,2,3}` → **12**).
- ★★ **`(char[]){"abc"}` 는 고칠 수 있고 `"abc"` 는 고치면 `run exit=139`** 로 죽는다.
- ★★ **함수 인자 자리는 안전하다** — 주소를 밖으로 저장하지 않으니까. **이것이 본래 용도**다.
- ★ **C23 의 `(static struct P){…}` 는 gcc 13 만 된다** — clang 18 은 `-std=c2x` 에서도 `cc exit=1`.
- ★ **C++ 에서는 우변값**이라 `&` 가 에러이고, 복합 리터럴 자체가 **ISO C++ 에 없다.**

## 관련 자료

- [21번 형제 — 구조체 선언·초기화·지정 초기자](../21-struct-declaration-initialization-and-designated-initializers/) — ★★ **직접 선행.**\
  `{.x = 1}` 이라는 **초기자 문법**은 그쪽이 정본이고, 여기는 「**그것을 식 한가운데 놓으면 객체가 생긴다**」부터다.
- [28번 형제 — 저장 기간 4종을 고르는 법](../28-choosing-among-four-storage-durations/) — ★★ **수명 규칙의 정본.**\
  복합 리터럴은 **새 저장 기간을 만들지 않는다** — 자동이거나 정적이다.
- [20번 형제 — 널 종단 문자열과 문자열 리터럴](../20-null-terminated-strings-and-string-literals/) — ★★ **`"abc"` 쪽의 정본.**\
  (1)에서 `(char[]){"abc"}` 와 나란히 놓아 **수정 가능성**을 갈랐다.
- [8번 형제 — `sizeof`·정렬·`offsetof`](../08-sizeof-alignment-and-offsetof/) — ★ `sizeof (int[]){1,2,3}` 이 **12** 인 이유.
- [14번 형제 — 포인터](../14-pointers-address-dereference-and-pointer-types/) — ★ 「포인터의 값」과 「가리키는 값」을 가르는 것이 (4)의 전제다.
- [25번 형제 — 불완전 타입과 opaque struct](../25-incomplete-types-and-opaque-struct/) — ★ opaque 타입에는 복합 리터럴을 쓸 수 없다(크기를 모른다).
- [26번 형제 — 유연 배열 멤버](../26-flexible-array-members/) — ★ FAM 구조체도 복합 리터럴로 못 만든다(꼬리를 못 준다).
- 목록의 **57번 주제** — 시간 위반(해제 후 사용·댕글링). (3)의 UB 가 그 계열이다. **왜 이 실패가 최악인가**는 그쪽이 정본이다.
- 목록의 **58번 주제** — UB 를 잡는 도구. (5)의 ASan 과 (3)의 경고 플래그는 그쪽이 정본이다.
- [목록의 **30번 주제**](../30-initialization-rules-and-indeterminate-values/) — 초기화 규칙과 불확정 값. (3)의 `-O1` 에서 `[-Wuninitialized]` 가 같이 뜨는 이유가 거기 있다.
- ★ **C++ 갈래와 갈리는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)).\
  ★★ **C 에서는 좌변값, C++ 에서는 우변값**이라 `&(P){1,2}` 가 **C++ 에서는 컴파일 에러**다((8)).

## 용어 풀이

> **복합 리터럴(compound literal)** — `(타입){초기자}` 꼴로 **이름 없는 객체**를 만드는 문법.\
> 예: `(struct P){.x = 1}`. **C99 부터**다.

> **좌변값(lvalue)** — 객체를 가리키는 식. 주소를 잡을 수 있고 고칠 수 있다.\
> 예: `(struct P){1,2}` 는 좌변값이라 `&` 가 된다. `3` 은 아니다.

> **우변값(rvalue)** — 값일 뿐 객체가 아닌 것. 주소를 못 잡는다.\
> 예: C++ 의 `(P){1,2}` 가 그렇다 — `error: taking address of rvalue`.

> **자동 저장 기간(automatic storage duration)** — 블록에 들어갈 때 태어나 **블록이 끝날 때 죽는** 것.\
> 예: 함수 안의 복합 리터럴이 그렇다.

> **정적 저장 기간(static storage duration)** — 프로그램이 시작할 때 태어나 **끝날 때까지 사는** 것.\
> 예: 파일 스코프의 복합 리터럴이 그렇다.

> **댕글링 포인터(dangling pointer)** — 이미 죽은 객체를 가리키는 포인터.\
> 예: `set()` 이 끝난 뒤의 `keep`. 읽으면 **UB** 다.

> **`stack-use-after-scope`** — ASan 이 「스코프가 끝난 스택 객체를 읽었다」고 알리는 에러 이름.\
> 예: (5)에서 `READ of size 4` 와 함께 나왔다.

## 더 들어가면

- ★★ **`const` 로 한정한 복합 리터럴**(`(const int){1}`) — 두 개가 **같은 객체로 합쳐질 수 있다.**\
  ★ 이 문서는 **그쪽을 던지지 않았다** — 합쳐지는지 아닌지를 확인하지 않았다.
- ★★ **매크로 안에서 쓰는 관용구** — `#define OPT(...) ((struct Opt){__VA_ARGS__})` 꼴로 「이름 붙은 인자」를 흉내 낸다.\
  ★ 이 문서는 **매크로와의 결합을 던지지 않았다**(목록의 **42번 주제**가 매크로의 정본).
- ★ **`switch` 나 `if` 의 본문 없는 블록에서 만든 복합 리터럴의 수명** — ★ **던지지 않았다.**
- ★ **VLA 타입의 복합 리터럴**(`(int[n]){…}`) — ★ **던지지 않았다**([18번 형제](../18-variable-length-arrays-vla/)가 VLA 의 정본).
- ★ **`-Os`·`-O3` 에서의 (3) 격자** — ★ **던지지 않았다**(`-O0`\~`-O2` 까지만 흔들었다).
- ★ **clang 이 왜 이 UB 에 침묵하는가** — `-Wdangling` 계열 플래그를 따로 켜면 달라지는지 **확인하지 않았다.**
