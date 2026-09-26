# c/syntax/31 — `const` 와 포인터 const 위치: 「**`const` 는 약속이지 보장이 아니다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 포인터 대입의 한정자 규칙, `const` 객체를 고치는 UB, 문자열 리터럴을 고치는 UB 를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **진단·어셈블리·심볼·종료 코드는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **UB 가 걸린 실험은 컴파일러 2 × `-O0`/`-O2` 네 벌**을 돌렸다 — 한 벌로는 **정반대 결론**이 난다((5)).\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `const` 는 **C89 부터**다. 이 편의 규칙은 C89 이후 바뀌지 않았다(`char **` → `const char *const *` 를 C 가 막는 것도 **C23 까지 그대로**다 — `-std=c2x` 로 확인((3))).
> ★★★ **재지 않은 성능 주장은 하지 않는다.** 「`const` 가 최적화를 돕는다」는 **시간으로 재지 않았다** — 이 편은 **어셈블리의 명령 수**만 센다.
> ★★ **경계** — **선언을 오른쪽에서 왼쪽으로 읽는 법** 일반은 [01번 형제](../01-declaration-syntax-and-reading/), **포인터 자체**는 [14번 형제](../14-pointers-address-dereference-and-pointer-types/)가 정본이다.\
> ★ **문자열 리터럴의 저장 기간**은 [20번 형제](../20-null-terminated-strings-and-string-literals/), **`restrict`** 는 [목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/), **엄격한 앨리어싱**은 목록의 **55번 주제**가 정본이다.\
> ★ **`volatile`**(같은 한정자의 다른 짝)은 [32번 형제](../32-what-volatile-actually-guarantees/)로 이어진다.
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [29번 형제](../29-scope-and-linkage-static-extern/)(링크와 `nm`).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — `-O2` 어셈블리다.** `const int *p` 를 받은 함수가 **`*p` 를 두 번 읽는 것**을 명령으로 본다.
★★ **둘째 본체는 `nm`** — 파일 스코프 `const` 의 링크를 **C 와 C++ 로 던져** 글자로 가른다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | 막히는 대입 네 가지 · `char **` → `const char **` · `-Wwrite-strings` | 씀 |
| ② 실행 출력 | `const` 를 떼고 쓴 뒤의 값 · 문자열 리터럴에 쓰기 · 반례 코드 | 씀 |
| ③ sanitizer | ★ **부적용** — `const` 위반은 **메모리 범위 안의 쓰기**라 ASan 이 볼 것이 없고, UBSan 에 이 검사가 없다 | ★ 잴 것이 없다 |
| ★★★ ④ **`-O2` 어셈블리** | ★ **본체** — `*p` 를 **두 번 읽는 것** · `const` 객체 `K` 는 **즉치값으로 접힌 것** | 씀 |
| ★★ ⑤ **`nm`** | 파일 스코프 `const` — C 는 **`R K`**, C++ 은 **`r _ZL1K`** | 씀 |
| ★ 제5의 상태 | 「`const` 객체가 정말 안 바뀌었나」를 **값으로 묻자 두 값이 나왔다** — 그래서 **`volatile` 포인터로 메모리를 다시 읽어** 물었다((5)) | 창을 바꿔 답함 |

★ **바꾼 창이 못 보는 것** — `volatile` 로 다시 읽는 것은 **그 순간 메모리에 무엇이 있나**만 말한다. **컴파일러가 이름 `local_c` 를 어디서 무엇으로 접었나**는 어셈블리만 답한다.

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

★ `g++`·`clang++` 도 같은 판이다 — (3)·(6)·(7)의 C++ 대비에 썼다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **어셈블리**(`-S -masm=intel`, 지시어를 걸러 낸 것) | 같은 컴파일러 · 같은 플래그면 같다 |
| 안 흔들린다 | ★★★ **종료 코드** — `cc exit` · `run exit=0` \| `139` | 결정적이다 |
| 안 흔들린다 | ★★ `nm` 의 글자와 이름 · 진단 전문 · 실행 출력 | 이 편의 프로그램은 전부 결정적이다 |
| 해당 없음 | 주소·PID | 주소를 찍지 않았고 sanitizer 를 안 썼다 |

★ **정규화 규칙은 하나도 안 썼다.** 이 편의 블록은 재실행에서 한 글자도 같아야 한다.

## 한눈에 — 쉽게 말하면

**`const` 는 「나는 이것을 안 고치겠다」는 서명이다. 「아무도 못 고친다」는 자물쇠가 아니다.**

- **도서관 열람증** — 「**이 책을 읽기만 하겠습니다**」에 서명했다. 그런데 **옆 사람이 같은 책에 밑줄을 긋는 것**은 막지 못한다. → **`const int *p`**
- **책장에 붙박은 전시품** — 유리장 안에 있다. **깨고 꺼내면** 무슨 일이 날지 모른다. → **`const int K = 5;`(객체 자체가 `const`)**
- **대출 카드를 코팅해 둔 것** — 카드 **자체**를 바꿀 수 없다. 카드에 적힌 **책**은 읽고 고칠 수 있다. → **`char *const p`**
- **서명을 몰래 지우고 고치기** — 원래 **내 책**이면 괜찮다. **전시품**이면 사고다. → **`const` 를 캐스트로 떼기**

| 비유 | 실체 | 무엇이 막히나 |
|---|---|---|
| 열람증 | `const char *p` | ★ `p[0] = 'X'` 가 **컴파일 에러** — 그러나 **다른 경로로는 바뀐다** |
| 코팅한 카드 | `char *const p` | ★ `p = other` 가 **컴파일 에러** |
| 둘 다 | `const char *const p` | 둘 다 |
| ★ 옆 사람의 밑줄 | `*q = 0` 이 `*p` 를 바꿈 | ★★★ **아무것도 안 막힌다** — 그래서 컴파일러가 **다시 읽는다** |
| 전시품 | `static const int K = 5;` | ★★ 고치면 **UB** — 컴파일러가 **`5` 로 접어도 된다** |
| 서명 지우기 | `*(int *)p = 99;` | 원래 비-`const` 면 ★ **합법** · 원래 `const` 면 ★★ **UB** |

```text
   ★ 선언은 이름에서 출발해 오른쪽에서 왼쪽으로 읽는다  ( * 는 "포인터" )

   const char * p              p  ->  *  ->  char  ->  const
                               "p 는 / 포인터다 / char 를 가리키는 / 그 char 가 const 인"
                               ★ 가리키는 것이 얼었다  : p[0] = 'X'  막힘   p = q  된다

   char * const p              p  ->  const  ->  *  ->  char
                               "p 는 / const 인 / 포인터다 / char 를 가리키는"
                               ★ 포인터가 얼었다        : p = q  막힘        p[0] = 'X'  된다

   const char * const p        p  ->  const  ->  *  ->  char  ->  const
                               ★ 둘 다 얼었다

   ★ 요령 : * 의 왼쪽에 const 가 있으면 「가리키는 것」, 오른쪽에 있으면 「포인터 자신」
            char const * p 는 const char * p 와 ★ 같은 것이다
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — 막히는 대입, `char **` 규칙, `const` 객체를 고치는 UB 가 전부 표준 문장이다.
- ★★ 두 번째 무게중심은 「**UB**」다 — **원래 `const` 인 객체를 고치는 것**과 **문자열 리터럴을 고치는 것.** 네 벌이 **다른 답**을 낸다.
- ★★ 「**종료 코드 0인데 ill-formed**」가 이 편의 가장 중요한 도구 사실이다 — **`char **` → `const char **` 가 경고 · `cc exit=0`** ((3)).

> **한정자(qualifier)** — 타입에 붙어 **그 객체에 무엇을 할 수 있나**를 바꾸는 낱말. C 에는 `const`·`volatile`·`restrict`·`_Atomic` 이 있다.\
> 예: `const int` 는 「이 이름으로는 안 고친다」.

> **에일리어싱(aliasing)** — **서로 다른 두 이름이 같은 메모리를 가리키는 것.**\
> 예: `twice_read(&x, &x)` 에서 `p` 와 `q` 가 둘 다 `x` 다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`const` 가 어디 붙었나를 어떻게 읽고, 각각 무엇을 막나.**
2. ★★★ **`const` 는 무엇을 약속하지 않나** — 에일리어싱 · 캐스트 · 문자열 리터럴.
3. ★★ **파일 스코프 `const` 는 링크를 바꾸나** — C 와 C++ 에서.

## 동작 방식

### (1) ★★★ 세 가지 선언 — 되는 대입

**언제 쓰나** — 함수 매개변수에 `const` 를 어디 붙일지 고를 때.

```c
/* s31a.c */
#include <stdio.h>

int main(void) {
    char buf1[] = "abc", buf2[] = "xyz";
    const char *p1 = buf1;               /* 가리키는 char 가 const */
    char *const p2 = buf1;               /* 포인터 자신이 const */
    const char *const p3 = buf1;         /* 둘 다 const */

    p1 = buf2;                           /* 된다 — p1 이 가리키는 곳을 바꾼다 */
    p2[0] = 'A';                         /* 된다 — p2 를 통해 가리키는 것을 바꾼다 */

    printf("p1 -> %s · p2 -> %s · p3 -> %s\n", p1, p2, p3);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31a.c -o x ; ./x (cc exit=0 · run exit=0) =====
p1 -> xyz · p2 -> Abc · p3 -> Abc
```

- ★★ **`p1 = buf2` 는 된다** — `const char *` 는 **가리키는 것**만 얼렸다. 포인터는 움직인다.
- ★★ **`p2[0] = 'A'` 는 된다** — `char *const` 는 **포인터**만 얼렸다. 가리키는 것은 고친다.
- ★ **`p3` 는 `p2` 가 고친 `Abc` 를 본다** — `const` 는 **p3 라는 경로**로 고치지 않겠다는 것이지 **그 메모리가 안 바뀐다**는 것이 아니다. (4)의 씨앗이다.

### (2) ★★ 막히는 대입 넷 — 진단 전문

**언제 쓰나** — 「`const` 가 무엇을 막나」를 컴파일러에게 직접 물을 때.

```c
/* s31b.c */
void f(void) {
    char buf1[] = "abc", buf2[] = "xyz";
    const char *p1 = buf1;
    char *const p2 = buf1;
    const char *const p3 = buf1;

    p1[0] = 'X';                         /* ① 가리키는 것을 바꾼다 */
    p2 = buf2;                           /* ② 포인터를 바꾼다 */
    p3[0] = 'X';                         /* ③ 가리키는 것을 바꾼다 */
    p3 = buf2;                           /* ④ 포인터를 바꾼다 */
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fmax-errors=0 -c s31b.c -o /dev/null (cc exit=1) =====
s31b.c: In function ‘f’:
s31b.c:7:11: error: assignment of read-only location ‘*p1’
    7 |     p1[0] = 'X';                         /* ① 가리키는 것을 바꾼다 */
      |           ^
s31b.c:8:8: error: assignment of read-only variable ‘p2’
    8 |     p2 = buf2;                           /* ② 포인터를 바꾼다 */
      |        ^
s31b.c:9:11: error: assignment of read-only location ‘*p3’
    9 |     p3[0] = 'X';                         /* ③ 가리키는 것을 바꾼다 */
      |           ^
s31b.c:10:8: error: assignment of read-only variable ‘p3’
   10 |     p3 = buf2;                           /* ④ 포인터를 바꾼다 */
      |        ^
s31b.c:4:17: warning: variable ‘p2’ set but not used [-Wunused-but-set-variable]
    4 |     char *const p2 = buf1;
      |                 ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -ferror-limit=0 -c s31b.c -o /dev/null (cc exit=1) =====
s31b.c:7:11: error: read-only variable is not assignable
    7 |     p1[0] = 'X';                         /* ① 가리키는 것을 바꾼다 */
      |     ~~~~~ ^
s31b.c:8:8: error: cannot assign to variable 'p2' with const-qualified type 'char *const'
    8 |     p2 = buf2;                           /* ② 포인터를 바꾼다 */
      |     ~~ ^
s31b.c:4:17: note: variable 'p2' declared const here
    4 |     char *const p2 = buf1;
      |     ~~~~~~~~~~~~^~~~~~~~~
s31b.c:9:11: error: cannot assign to variable 'p3' with const-qualified type 'const char *const'
    9 |     p3[0] = 'X';                         /* ③ 가리키는 것을 바꾼다 */
      |     ~~~~~ ^
s31b.c:5:23: note: variable 'p3' declared const here
    5 |     const char *const p3 = buf1;
      |     ~~~~~~~~~~~~~~~~~~^~~~~~~~~
s31b.c:10:8: error: cannot assign to variable 'p3' with const-qualified type 'const char *const'
   10 |     p3 = buf2;                           /* ④ 포인터를 바꾼다 */
      |     ~~ ^
s31b.c:5:23: note: variable 'p3' declared const here
    5 |     const char *const p3 = buf1;
      |     ~~~~~~~~~~~~~~~~~~^~~~~~~~~
4 errors generated.
```

- ★★★ **네 줄 전부 에러 · `cc exit=1`** — `const` 가 얼린 쪽을 고치려 했다.
- ★★ **gcc 의 문구가 두 가지를 가른다** — 「가리키는 것」은 **`read-only location '*p1'`**, 「포인터 자신」은 **`read-only variable 'p2'`**. 문구만 봐도 **어느 `const` 에 걸렸나**가 보인다.
- ★★★ **clang 의 ③ 문구는 원인을 잘못 가리킨다** — `p3[0] = 'X'` 는 **가리키는 `const char`** 에 걸린 것인데, clang 은 **`cannot assign to variable 'p3' with const-qualified type 'const char *const'`** 라고 **포인터 변수**를 탓한다.\
  ★ 문구를 근거로 쓰면 「포인터 쪽 `const` 를 떼면 되겠다」로 **틀린 처방**을 하게 된다. **근거는 캐럿의 자리(7행 11열 · 9행 11열)와 `cc exit`** 다.
- ★ gcc 는 덤으로 `p2` 에 **`set but not used`** 경고를 단다 — `p2 = buf2` 가 에러로 버려져 **쓰인 적이 없는 것**으로 보인 것이다.

### (3) ★★★ `char **` 를 `const char **` 에 못 넣는 이유 — 반례로

**언제 쓰나** — `main(int argc, char **argv)` 의 `argv` 를 `const char **` 를 받는 함수에 넘기다 경고가 났을 때.

```c
/* s31c.c */
#include <stdio.h>

static void point_at_readonly(const char **out) {
    *out = "READ-ONLY";                  /* const char 를 가리키게 한다 — 이 함수 자체는 정당하다 */
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char *p = NULL;
    point_at_readonly(&p);               /* ★ char ** 를 const char ** 자리에 넘긴다 */
    printf("p -> %s\n", p);
    printf("p 는 char * 라 p[0] 에 쓰는 것을 컴파일러가 막지 않는다\n");
    p[0] = 'X';
    printf("안 죽었다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31c.c -o x (cc exit=0) =====
s31c.c: In function ‘main’:
s31c.c:10:23: warning: passing argument 1 of ‘point_at_readonly’ from incompatible pointer type [-Wincompatible-pointer-types]
   10 |     point_at_readonly(&p);               /* ★ char ** 를 const char ** 자리에 넘긴다 */
      |                       ^~
      |                       |
      |                       char **
s31c.c:3:44: note: expected ‘const char **’ but argument is of type ‘char **’
    3 | static void point_at_readonly(const char **out) {
      |                               ~~~~~~~~~~~~~^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s31c.c -o x (cc exit=0) =====
s31c.c:10:23: warning: passing 'char **' to parameter of type 'const char **' discards qualifiers in nested pointer types [-Wincompatible-pointer-types-discards-qualifiers]
   10 |     point_at_readonly(&p);               /* ★ char ** 를 const char ** 자리에 넘긴다 */
      |                       ^~
s31c.c:3:44: note: passing argument to parameter 'out' here
    3 | static void point_at_readonly(const char **out) {
      |                                            ^
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31c.c -o x ; ./x (cc exit=0 · run exit=139) =====
p -> READ-ONLY
p 는 char * 라 p[0] 에 쓰는 것을 컴파일러가 막지 않는다
```

```text
   const char **out = &p;    ← 이것이 허용된다고 치자

   *out = "READ-ONLY";       out 의 눈으로는 정당하다 — const char 를 가리키게 했을 뿐
     |
     v
   p  ───────────►  "READ-ONLY"   (r--p 구역 — 28번 형제)
   (char *)                       ★ p 는 const 가 없는 포인터다

   p[0] = 'X';               p 의 눈으로도 정당하다 — char * 로 쓰는 것
     -> ★★★ run exit=139

   ★ 두 줄이 각자 정당한데 합치면 const 가 새어 나간다. 그래서 첫 줄을 막는다.
```

그림 해설 (한 단계씩):

- ★★★ **두 컴파일러 다 경고 · `cc exit=0`** — 그리고 실행하면 **`run exit=139`**. 「**종료 코드 0인데 ill-formed**」이다 — 포인터 대입의 한정자 규칙을 어긴 **제약 위반**인데, 진단을 경고로 냈으니 표준은 만족했고 **빌드는 초록불**이다.
- ★★★ **왜 막아야 하나** — `const char **` 로 **`const char` 의 주소를 `char *` 에 몰래 넣을 수 있기** 때문이다. 그다음 `p[0] = 'X'` 는 **아무 규칙도 안 어긴 것처럼** 보인다.
- ★★ **문구와 플래그가 갈린다** — gcc `[-Wincompatible-pointer-types]` · clang `[-Wincompatible-pointer-types-discards-qualifiers]`(「**중첩된 포인터에서 한정자를 버린다**」 — 이쪽이 원인을 정확히 말한다).

**판 격자 — 위험한 쪽과 안전한 쪽**

```c
/* s31c2.c */
static void read_only_view(const char *const *v) { (void)v; }   /* 두 단계 다 const */

int main(void) {
    char *p = 0;
    read_only_view(&p);                  /* ★ char ** 를 const char *const * 자리에 — 이것은 안전하다 */
    return 0;
}
```

```text
===== char ** 를 const 가 붙은 두 자리에 — 파일 2 × 컴파일러 2 × 판 3 (exit=0) =====
s31c   gcc    -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   gcc    -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c   gcc    -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   clang  -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   clang  -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c   clang  -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  gcc    -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  gcc    -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c2  gcc    -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  clang  -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  clang  -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c2  clang  -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s31c2.c -o /dev/null (cc exit=0) =====
s31c2.c: In function ‘main’:
s31c2.c:5:20: warning: passing argument 1 of ‘read_only_view’ from incompatible pointer type [-Wincompatible-pointer-types]
    5 |     read_only_view(&p);                  /* ★ char ** 를 const char *const * 자리에 — 이것은 안전하다 */
      |                    ^~
      |                    |
      |                    char **
s31c2.c:1:47: note: expected ‘const char * const*’ but argument is of type ‘char **’
    1 | static void read_only_view(const char *const *v) { (void)v; }   /* 두 단계 다 const */
      |                            ~~~~~~~~~~~~~~~~~~~^
```

- ★★★ **안전한 쪽(`const char *const *`)도 C 는 막는다** — 경고 1 · `exit=0`. **두 단계가 다 `const` 면** 1번 반례의 `*out = …` 가 불가능해 새어 나갈 길이 없는데도 그렇다.
- ★★ **`-std=c2x` 에서도 같다** — C23 까지 **이 규칙은 그대로**다.
- ★★ **`-pedantic-errors` 에서만 `exit=1`** 이다.

**C++ 은 둘을 가른다**

```cpp
// s31cx.cpp
static void point_at_readonly(const char **out) { *out = "READ-ONLY"; }
static void read_only_view(const char *const *v) { (void)v; }

int main() {
    char *p = nullptr;
    read_only_view(&p);                  // ★ char ** → const char *const * — 안전한 쪽
    point_at_readonly(&p);               // ★ char ** → const char ** — 위험한 쪽
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s31cx.cpp -o /dev/null (cc exit=1) =====
s31cx.cpp: In function ‘int main()’:
s31cx.cpp:7:23: error: invalid conversion from ‘char**’ to ‘const char**’ [-fpermissive]
    7 |     point_at_readonly(&p);               // ★ char ** → const char ** — 위험한 쪽
      |                       ^~
      |                       |
      |                       char**
s31cx.cpp:1:44: note:   initializing argument 1 of ‘void point_at_readonly(const char**)’
    1 | static void point_at_readonly(const char **out) { *out = "READ-ONLY"; }
      |                               ~~~~~~~~~~~~~^~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s31cx.cpp -o /dev/null (cc exit=1) =====
s31cx.cpp:7:5: error: no matching function for call to 'point_at_readonly'
    7 |     point_at_readonly(&p);               // ★ char ** → const char ** — 위험한 쪽
      |     ^~~~~~~~~~~~~~~~~
s31cx.cpp:1:13: note: candidate function not viable: no known conversion from 'char **' to 'const char **' for 1st argument
    1 | static void point_at_readonly(const char **out) { *out = "READ-ONLY"; }
      |             ^                 ~~~~~~~~~~~~~~~~
1 error generated.
```

- ★★★ **C++ 은 위험한 쪽만 에러로 막고 안전한 쪽은 받는다** — 에러는 **7행 하나**뿐이다(6행 `read_only_view(&p)` 는 통과).
- ★★ **C 는 둘 다 경고, C++ 은 하나만 에러** — 같은 문제를 **반대 방향으로** 틀렸다고 할 수 있다: C 는 **덜 세게**(경고) 막고 **더 넓게**(안전한 쪽까지) 막는다.

비용 — **C 에서 `argv` 를 `const char *const *` 로 받는 함수에 넘기려면 캐스트가 필요하다.** 그 캐스트가 **안전한 쪽**이라는 판단은 사람이 한다.

### (4) ★★★ `const` 는 최적화 보장이 아니다 — 에일리어싱 때문에 두 번 읽는다

**언제 쓰나** — 「`const int *` 를 받았으니 컴파일러가 `*p` 를 한 번만 읽겠지」라고 생각할 때. ★★★ **이 편의 본체**다.

```c
/* s31d.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;                              /* q 가 p 와 같은 곳일 수 있다 */
    int b = *p;                          /* ★ 그래서 다시 읽는다 */
    return a + b;
}

void opaque(void);                       /* 무엇을 하는지 이 파일은 모른다 */

int across_call(const int *p) {
    int a = *p;
    opaque();                            /* ★ 다른 경로로 *p 를 바꿀 수 있다 */
    return a + *p;
}

static const int K = 5;                  /* ★ 객체 자체가 const */

int const_object(void) {
    int a = K;
    opaque();
    return a + K;                        /* ★ K 는 바뀌면 UB 이므로 다시 안 읽어도 된다 */
}
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s31d.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
twice_read:
	endbr64
	mov	eax, DWORD PTR [rdi]
	mov	DWORD PTR [rsi], 0
	add	eax, DWORD PTR [rdi]
	ret
across_call:
	endbr64
	push	rbp
	push	rbx
	mov	rbx, rdi
	sub	rsp, 8
	mov	ebp, DWORD PTR [rdi]
	call	opaque@PLT
	mov	eax, DWORD PTR [rbx]
	add	rsp, 8
	pop	rbx
	add	eax, ebp
	pop	rbp
	ret
const_object:
	endbr64
	sub	rsp, 8
	call	opaque@PLT
	mov	eax, 10
	add	rsp, 8
	ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s31d.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
twice_read:                             # @twice_read
# %bb.0:
	mov	eax, dword ptr [rdi]
	mov	dword ptr [rsi], 0
	add	eax, dword ptr [rdi]
	ret
.Lfunc_end0:
                                        # -- End function
across_call:                            # @across_call
# %bb.0:
	push	rbp
	push	rbx
	push	rax
	mov	rbx, rdi
	mov	ebp, dword ptr [rdi]
	call	opaque@PLT
	add	ebp, dword ptr [rbx]
	mov	eax, ebp
	add	rsp, 8
	pop	rbx
	pop	rbp
	ret
.Lfunc_end1:
                                        # -- End function
const_object:                           # @const_object
# %bb.0:
	push	rax
	call	opaque@PLT
	mov	eax, 10
	pop	rcx
	ret
.Lfunc_end2:
                                        # -- End function
```

```text
   twice_read(const int *p, int *q)        gcc -O2 / clang -O2 (같은 모양)

     mov  eax, [rdi]        ① *p 를 읽는다
     mov  [rsi], 0          *q = 0          ← q 가 p 와 같은 곳일 수 있다
     add  eax, [rdi]        ② ★ *p 를 다시 읽는다

   const_object()          static const int K = 5;
     call opaque
     mov  eax, 10           ★ K 를 한 번도 안 읽는다 — 5 + 5 를 접어 10
```

그림 해설 (한 단계씩):

- ★★★ **`twice_read` 는 두 컴파일러 다 `[rdi]` 를 두 번 읽는다.** `p` 가 `const int *` 인데도 그렇다 — **`*q = 0` 이 `*p` 를 바꿀 수 있기** 때문이다.
- ★★★ **`across_call` 도 `call opaque` 뒤에 `*p` 를 다시 읽는다**(gcc `mov eax, [rbx]` · clang `add ebp, [rbx]`) — `opaque` 가 **다른 포인터로** `*p` 를 고칠 수 있다.
- ★★★ **`const_object` 는 `K` 를 한 번도 안 읽는다** — `mov eax, 10`. **객체 자체가 `const`** 라 바뀌면 UB 이므로, 컴파일러가 **값을 믿어도 된다.**
- ★★ **갈림은 「포인터가 `const` 냐」가 아니라 「객체가 `const` 냐」** 다. `const int *p` 는 **내 쪽의 약속**이고, `static const int K` 는 **그 객체의 성질**이다.
- ★ 이것은 **명령 수**다 — 이 편은 **시간을 재지 않았다.** 「두 번 읽으니 느리다」도 「`const` 객체가 빠르다」도 **이 문서의 주장이 아니다.**

**판 격자 — `K` 는 `-O0` 에서도 접힌다**

```text
===== const 객체 K — 어셈블리에서 센 줄 수 (컴파일러 2 × 최적화 2) (exit=0) =====
            | const_object 안에서 K 를 메모리로 읽는 명령  | 즉치값 5 또는 10 을 쓰는 명령
gcc -O0     | 0 줄                                         | 2 줄
gcc -O2     | 0 줄                                         | 1 줄
clang -O0   | 0 줄                                         | 2 줄
clang -O2   | 0 줄                                         | 1 줄
```

```text
===== gcc -std=c17 -O0 -S -masm=intel -fno-asynchronous-unwind-tables s31d.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | sed -n '/^const_object:/,$p' (cc exit=0) =====
const_object:
	endbr64
	push	rbp
	mov	rbp, rsp
	sub	rsp, 16
	mov	DWORD PTR -4[rbp], 5
	call	opaque@PLT
	mov	edx, 5
	mov	eax, DWORD PTR -4[rbp]
	add	eax, edx
	leave
	ret
```

- ★★ **네 벌 다 `K` 를 메모리로 읽는 명령이 0 줄**이다. `-O0` 에서도 **`mov edx, 5`** 로 즉치값을 쓴다 — `-O0` 은 「아무것도 안 접는다」가 아니다.
- ★ `-O0` 은 즉치값이 **두 줄**(`5` 를 두 번), `-O2` 는 **한 줄**(`10`)이다.

**실행으로 확인 — 같은 곳을 넘기면 `const` 인데 값이 바뀐다**

```c
/* s31d2.c */
#include <stdio.h>

int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int main(void) {
    int x = 7, y = 7;
    printf("twice_read(&x, &y) = %d   (p 와 q 가 다른 곳)\n", twice_read(&x, &y));
    x = 7;
    printf("twice_read(&x, &x) = %d   (p 와 q 가 같은 곳 — const 인데 값이 바뀌었다)\n", twice_read(&x, &x));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s31d2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read(&x, &y) = 14   (p 와 q 가 다른 곳)
twice_read(&x, &x) = 7   (p 와 q 가 같은 곳 — const 인데 값이 바뀌었다)
```

- ★★★ **`twice_read(&x, &x) = 7`** — `a = 7`, `*q = 0` 이 `x` 를 0 으로 만들고, **`b = 0`**. `p` 는 `const int *` 인데 **`*p` 가 두 번 읽는 사이에 바뀌었다.** 두 번 읽은 것이 **옳았다.**
- ★ 이것은 **UB 가 아니다** — `const int *` 로 **비-`const` 객체**를 가리키는 것은 합법이고, 다른 경로로 고치는 것도 합법이다. `*p` 를 한 번만 읽는 번역이 있다면 **그것이 틀린 번역**이다.
- ★ 「두 포인터가 겹치지 않는다」를 약속하는 것은 `const` 가 아니라 **`restrict`** 다([목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/)).

비용 — **`const` 를 붙여서 얻는 것은 「내가 실수로 안 고친다」의 컴파일러 검사**다. 겹침에 대한 약속은 아니다.

### (5) ★★★ `const` 를 캐스트로 떼고 쓰면 — **원래 `const` 냐가 층을 가른다**

**언제 쓰나** — 라이브러리가 `const` 를 안 붙인 API 라서 캐스트로 떼고 싶을 때.

```c
/* s31e.c */
#include <stdio.h>

static void sneaky(const int *p) {
    *(int *)p = 99;                      /* ★ const 를 캐스트로 떼고 쓴다 */
}

int main(void) {
    int plain = 1;                       /* 원래 const 가 아닌 객체 */
    sneaky(&plain);
    printf("plain   = %d\n", plain);

    const int local_c = 1;               /* ★ 원래 const 인 객체 — 자동 저장 기간 */
    sneaky(&local_c);
    printf("local_c = %d · 같은 자리를 포인터로 다시 읽으면 = %d\n",
           local_c, *(const volatile int *)&local_c);
    return 0;
}
```

```text
===== const 를 캐스트로 떼고 쓰기 — 원래 const 가 아닌 것 / 원래 const 인 자동 객체 (exit=0) =====
--- gcc -O0
plain   = 99
local_c = 99 · 같은 자리를 포인터로 다시 읽으면 = 99
--- gcc -O2
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
--- clang -O0
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
--- clang -O2
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
```

```c
/* s31f.c */
#include <stdio.h>

static const int static_c = 1;           /* ★ 원래 const · 정적 저장 기간 */

static void sneaky(const int *p) {
    *(int *)p = 99;
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("static_c 에 쓴다\n");
    sneaky(&static_c);
    printf("static_c = %d\n", static_c);
    return 0;
}
```

```text
===== 원래 const 인 정적 객체에 쓰기 — 컴파일러 2 × 최적화 2 (exit=0) =====
gcc    -O0  run exit=139 | static_c 에 쓴다|
gcc    -O2  run exit=0   | static_c 에 쓴다|static_c = 1|
clang  -O0  run exit=139 | static_c 에 쓴다|
clang  -O2  run exit=0   | static_c 에 쓴다|static_c = 1|
```

```text
                      원래 const 가 아님     원래 const · 자동       원래 const · 정적
                      int plain = 1;         const int local_c = 1;  static const int static_c = 1;
   ------------------  --------------------  ----------------------  ------------------------------
   gcc   -O0           99                    99                      ★ run exit=139
   gcc   -O2           99                    ★ 1 (메모리는 99)        ★ 1 · run exit=0
   clang -O0           99                    ★ 1 (메모리는 99)        ★ run exit=139
   clang -O2           99                    ★ 1 (메모리는 99)        ★ 1 · run exit=0
   ------------------  --------------------  ----------------------  ------------------------------
   층                  ★★ 표준 — 합법         ★★★ UB                  ★★★ UB
```

그림 해설 (한 단계씩):

- ★★★ **원래 `const` 가 아니면 합법**이다 — 네 벌 다 `99`. `const int *` 는 **보는 쪽의 약속**일 뿐, 떼고 쓰면 **원래 객체**를 고친 것이다.
- ★★★ **원래 `const` 인 자동 객체는 UB** 이고 **네 벌 중 셋이 `1`** 을 찍는데 **같은 자리를 `volatile` 포인터로 다시 읽으면 `99`** 다. **한 객체가 두 값**을 가진 것처럼 보인다 — 컴파일러가 이름 `local_c` 를 **`1` 로 접어** 두었기 때문이다. ★ 이것이 **제5의 상태**다.
- ★★★ **원래 `const` 인 정적 객체는 `-O0` 에서 `run exit=139`, `-O2` 에서 `exit=0` · `1`** 이다. `-O0` 은 **읽기 전용 구역**(`r--p` — [28번 형제](../28-choosing-among-four-storage-durations/))에 실제로 써서 죽고, `-O2` 는 **쓰기 자체가 없어진 것처럼** 산다.
- ★★ **최적화 수준이 「죽는다 / 산다」를 뒤집는다** — 한 판만 돌렸으면 「`const` 정적 객체에 쓰면 죽는다」 또는 「안 죽는다」 중 **하나를 규칙으로** 적었을 것이다. 둘 다 **이 판의 한 결과**다.

비용 — **캐스트로 떼는 것이 합법인지는 포인터가 아니라 원래 객체가 정한다.** 그것은 **호출된 쪽에서 알 수 없다** — 처방이 아니라 **떼지 않는 것**이 답이다.

### (6) ★ 문자열 리터럴은 C 에서 `char[]` 다 — 그런데 쓰면 UB

**언제 쓰나** — `char *s = "abc";` 가 경고 없이 통과해서 안심할 때.

```c
/* s31g.c */
#include <stdio.h>

#define TYPE(x) _Generic((x), char *: "char *", const char *: "const char *", default: "그 밖")

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("\"abc\" 가 감쇠한 타입 = %s\n", TYPE("abc"));
    char *s = "abc";                     /* C 에서는 경고 없이 통과한다 */
    printf("s[0] 에 쓴다\n");
    s[0] = 'X';
    printf("안 죽었다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31g.c -o x ; ./x (cc exit=0 · run exit=139) =====
"abc" 가 감쇠한 타입 = char *
s[0] 에 쓴다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wwrite-strings -c s31g.c -o /dev/null (cc exit=0) =====
s31g.c: In function ‘main’:
s31g.c:8:15: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
    8 |     char *s = "abc";                     /* C 에서는 경고 없이 통과한다 */
      |               ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wwrite-strings -c s31g.c -o /dev/null (cc exit=0) =====
s31g.c:8:11: warning: initializing 'char *' with an expression of type 'const char[4]' discards qualifiers [-Wincompatible-pointer-types-discards-qualifiers]
    8 |     char *s = "abc";                     /* C 에서는 경고 없이 통과한다 */
      |           ^   ~~~~~
1 warning generated.
```

- ★★★ **C 에서 `"abc"` 의 타입은 `char[4]`** 다 — `_Generic` 이 감쇠한 타입을 **`char *`** 라고 답한다. 그래서 `char *s = "abc";` 에 **경고가 없다**(`-Wall -Wextra -pedantic` 에서 0건).
- ★★★ **그런데 고치면 UB** 다 — 이 판에서 **`run exit=139`**. 타입은 `char[]` 인데 **자리는 읽기 전용**이다([20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본).
- ★★ **`-Wwrite-strings` 를 켜면 두 컴파일러가 경고**한다 — 이 옵션은 **리터럴을 `const char[]` 로 취급하게** 바꾼다. clang 의 문구가 그것을 드러낸다: **`with an expression of type 'const char[4]'`**.

**C++ 과 대비**

```cpp
// s31g.cpp
#include <cstdio>
#include <type_traits>

int main() {
    std::printf("\"abc\" 의 타입이 const char[4] 인가 = %d\n",
                (int)std::is_same_v<decltype("abc"), const char (&)[4]>);
    char *s = "abc";                     // ★ C++ 에서는 이 줄이 걸린다
    (void)s;
    return 0;
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
"abc" 의 타입이 const char[4] 인가 = 1
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x (cc exit=0) =====
s31g.cpp: In function ‘int main()’:
s31g.cpp:7:15: warning: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    7 |     char *s = "abc";                     // ★ C++ 에서는 이 줄이 걸린다
      |               ^~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x (cc exit=0) =====
s31g.cpp:7:15: warning: ISO C++11 does not allow conversion from string literal to 'char *' [-Wwritable-strings]
    7 |     char *s = "abc";                     // ★ C++ 에서는 이 줄이 걸린다
      |               ^
1 warning generated.
```

```text
===== C++ 에서 -pedantic-errors 로 올리면 (exit=0) =====
g++      -pedantic-errors  cc exit=1
clang++  -pedantic-errors  cc exit=1
```

- ★★★ **C++ 에서 `"abc"` 는 `const char[4]`** 다 — `is_same_v` 가 **`1`**. 그래서 `char *s = "abc";` 에 **기본 경고**가 나고, **`-pedantic-errors` 면 `cc exit=1`** 이다.
- ★ **g++ 는 경고(`[-Wwrite-strings]`), clang++ 도 경고(`[-Wwritable-strings]`)** 로 받는다 — 둘 다 **C++11 부터 금지된 변환**을 기본값에서는 경고로 남겨 둔다. **「종료 코드 0인데 ill-formed」의 C++ 판**이다.

비용 — **C 는 타입이 거짓말을 한다.** `-Wwrite-strings` 를 켜거나, 리터럴은 **늘 `const char *` 로** 받는다.

### (7) ★★ 파일 스코프 `const` 의 링크 — **C 는 외부, C++ 은 내부**

**언제 쓰나** — 헤더에 `const int K = 5;` 를 두었는데 **C 에서는 링크가 깨지고 C++ 에서는 안 깨질** 때.

```c
/* s31h.c */
const int K = 5;                         /* ★ 파일 스코프 const */
const int *addr_of_k(void) { return &K; }
```

```cpp
// s31h.cpp
const int K = 5;                         // ★ 파일(네임스페이스) 스코프 const — 소스는 C 와 같다
extern const int K2 = 6;                 // ★ extern 을 붙인 const
const int *addr_of_k() { return &K; }
const int *addr_of_k2() { return &K2; }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s31h.c -o h.o && nm h.o (cc exit=0) =====
0000000000000000 R K
0000000000000000 T addr_of_k
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s31h.c -o h.o && nm h.o (cc exit=0) =====
0000000000000000 R K
0000000000000000 T addr_of_k
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s31h.cpp -o h.o && nm h.o (cc exit=0) =====
0000000000000004 R K2
0000000000000011 T _Z10addr_of_k2v
0000000000000000 T _Z9addr_of_kv
0000000000000000 r _ZL1K
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s31h.cpp -o h.o && nm h.o (cc exit=0) =====
0000000000000000 R K2
0000000000000010 T _Z10addr_of_k2v
0000000000000000 T _Z9addr_of_kv
0000000000000004 r _ZL1K
```

- ★★★ **C 는 `R K`**(대문자 — 외부 링크 · `.rodata`), **C++ 은 `r _ZL1K`**(소문자 — 내부 링크). **소스가 한 글자도 같은데** 링크가 반대다.
- ★★ **C++ 에서 `extern` 을 붙이면 `R K2`** — 외부 링크로 돌아온다. 이름도 뭉개지지 않는다.
- ★ 이름의 **`L`**(`_ZL1K`)이 C++ 의 「**내부 링크**」 표시다([29번 형제](../29-scope-and-linkage-static-extern/)의 `_ZL9old_style` 과 같다).

**두 파일에 같은 줄을 두면**

```c
/* s31i1.c */
const int K = 5;                         /* ★ 번역 단위 1 */
int k_from_1(void) { return K; }
```

```c
/* s31i2.c */
#include <stdio.h>

const int K = 5;                         /* ★ 번역 단위 2 — 같은 줄 */
int k_from_1(void);

int main(void) {
    printf("K = %d · 1 쪽 K = %d\n", K, k_from_1());
    return 0;
}
```

```cpp
// s31i1.cpp
const int K = 5;                         // ★ 번역 단위 1
int k_from_1() { return K; }
```

```cpp
// s31i2.cpp
#include <cstdio>

const int K = 5;                         // ★ 번역 단위 2 — 같은 줄
int k_from_1();

int main() {
    std::printf("K = %d · 1 쪽 K = %d\n", K, k_from_1());
    return 0;
}
```

```text
===== 두 번역 단위에 같은 const int K = 5; — C 둘 · C++ 둘 (exit=0) =====
C   gcc      link exit=1 | -
C   clang    link exit=1 | -
C++ g++      link exit=0 | K = 5 · 1 쪽 K = 5
C++ clang++  link exit=0 | K = 5 · 1 쪽 K = 5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s31i1.c s31i2.c && gcc s31i1.o s31i2.o -o x (cc exit=1) =====
/usr/bin/ld: s31i2.o:(.rodata+0x0): multiple definition of `K'; s31i1.o:(.rodata+0x0): first defined here
collect2: error: ld returned 1 exit status
```

- ★★★ **C 는 두 컴파일러 다 링크 `exit=1`** — `multiple definition of 'K'`(`.rodata` 둘). **C++ 은 둘 다 통과** — 각 파일의 `K` 는 **남남**이다.
- ★★ 그래서 **C++ 헤더의 `const int K = 5;` 는 관용구**이고, **C 헤더에서는 링크 오류의 원인**이다. C 에서 헤더에 상수를 두려면 **`static const`** 이거나 **`enum`** · `#define` 이다.
- ★ 이 대비의 C++ 쪽 정본은 [C++ 10 — `const` 정확성](../../../cpp/syntax/10-const-correctness/)의 (7)이다.

비용 — **C 와 C++ 이 같이 읽는 헤더**에서 이 한 줄의 뜻이 **언어마다 반대**다.

## 문법 — 형태와 규칙

### 형태

(1)의 `s31a.c` 가 이 절의 **실제로 컴파일되는 형태**다. 읽는 법을 한 줄씩:

| 쓴 꼴 | 읽기(오른쪽에서 왼쪽) | 얼린 것 | 막히는 것 |
|---|---|---|---|
| `const char *p` | p 는 · 포인터 · char 의 · const | 가리키는 것 | `p[0] = …` |
| `char const *p` | p 는 · 포인터 · const · char 의 | ★ 위와 같다 | `p[0] = …` |
| `char *const p` | p 는 · const · 포인터 · char 의 | 포인터 | `p = …` |
| `const char *const p` | p 는 · const · 포인터 · char 의 · const | 둘 다 | 둘 다 |
| `const char **pp` | pp 는 · 포인터 · 포인터 · char 의 · const | 맨 끝 char | `**pp = …` |
| `const char *const *pp` | pp 는 · 포인터 · const 포인터 · const char 의 | 가운데 포인터와 char | `*pp = …` · `**pp = …` |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| `const char *p1; p1[0] = 'X';` | gcc `read-only location` · clang `read-only variable is not assignable` · **`cc exit=1`** | 표준(제약 위반) | (2) |
| `char **` 를 `const char **` 에 | ★★★ **경고 · `cc exit=0`** · `-pedantic-errors` 라야 `exit=1` · 실행 `139` | ★★ 표준 제약 위반 — **「종료 코드 0인데 ill-formed」** | (3) |
| `char **` 를 `const char *const *` 에 | C: **경고 · `exit=0`** · C++: **통과** | 표준(C 는 여기까지 막는다) | (3) |
| 원래 `const` 인 객체를 캐스트로 떼고 쓰기 | 경고 0 · 네 벌이 **99 / 1 / 139** 로 갈림 | ★★★ UB | (5) |
| `char *s = "abc"; s[0] = 'X';` | 경고 0 · **`run exit=139`** | ★★★ UB | (6) |
| C 헤더의 `const int K = 5;` 를 두 파일이 include | 링크 `multiple definition` **`exit=1`** | 표준(외부 링크) → 정의 둘 = UB | (7) |

### 규칙 불릿

- ★★★ **`const` 는 `*` 의 어느 쪽에 있나로 읽는다** — 왼쪽이면 가리키는 것, 오른쪽이면 포인터 자신.
- ★★★ **`const int *p` 는 「이 경로로는 안 고친다」는 약속**이다. **다른 경로로 바뀌는 것은 못 막는다** — 그래서 컴파일러는 `*p` 를 **다시 읽는다.**
- ★★★ **객체 자체가 `const` 면 고치는 것이 UB** 다 — 그래서 컴파일러가 **값을 접어도 된다**(`mov eax, 10`).
- ★★★ **캐스트로 `const` 를 떼고 쓰는 것은 원래 객체가 비-`const` 면 합법, `const` 면 UB** 다.
- ★★★ **`char **` → `const char **` 는 표준이 막는 변환**인데 **두 컴파일러 다 경고 · `cc exit=0`** 이다.
- ★★ **C 는 `char **` → `const char *const *` 도 막는다**(C23 까지). **C++ 은 이것을 받는다.**
- ★★ **C 의 문자열 리터럴은 `char[N]` 이지만 고치면 UB** 다. **C++ 에서는 `const char[N]`** 이다.
- ★★ **C 의 파일 스코프 `const` 는 외부 링크, C++ 은 내부 링크**다 — `R K` 대 `r _ZL1K`.
- ★ **clang 의 `const` 에러 문구는 원인을 틀리게 가리킬 수 있다** — 캐럿 자리를 봐라.

## 어디서 틀리나

### 1. ★★★ 「`const int *` 를 받았으니 `*p` 는 안 바뀐다」

**이 경로로 안 고칠 뿐**이다((4)). `twice_read(&x, &x)` 가 **`7`** 을 돌려줬다 — 두 번 읽는 사이에 바뀌었다.\
★ 컴파일러도 그것을 알아서 **`[rdi]` 를 두 번 읽는다.**

### 2. ★★★ 「`const` 를 붙이면 최적화가 된다」

**객체 자체가 `const` 일 때만 값을 접었다**((4)). 포인터의 `const` 는 **읽기 횟수를 한 번도 줄이지 않았다.**\
★ 그리고 이 편은 **시간을 재지 않았다** — 명령 수만 셌다.

### 3. ★★★ 「`char **` → `const char **` 는 경고일 뿐이니 괜찮다」

**반례가 `run exit=139`** 로 죽었다((3)). 경고의 정체는 **표준의 제약 위반**이고, `cc exit=0` 은 **컴파일러가 경고로 봐준 것**이다.

### 4. ★★ 「`const` 를 떼고 쓰니 되더라」

**원래 객체에 달렸다**((5)). 비-`const` 객체면 합법이고, 원래 `const` 면 **네 벌이 `99` · `1` · `139` 로 갈렸다.**\
★ **gcc `-O0` 의 `99`** 가 가장 위험하다 — 「되더라」로 읽히기 딱 좋다.

### 5. ★★ 「`char *s = "abc";` 에 경고가 없으니 써도 된다」

**C 의 타입이 `char[]` 일 뿐**이다((6)). 고치면 **`run exit=139`**. `-Wwrite-strings` 를 켜라.

### 6. ★★ 「헤더에 `const int K = 5;` 를 두면 된다 — C++ 에서 늘 그렇게 한다」

**C 에서는 외부 링크라 두 파일이 include 하면 `multiple definition`** 이다((7)).

### 7. ★ 「clang 이 포인터 변수 `p3` 가 `const` 라서 막혔다고 한다」

**`p3[0]` 은 가리키는 `const char` 에 걸린 것**이다((2)). clang ③의 문구가 원인을 잘못 가리킨다 — **캐럿 자리와 gcc 의 `read-only location '*p3'`** 가 맞다.

### 8. ★ 「`const char *const *` 로 받으면 C 에서도 안전하니 경고가 없겠지」

**C 는 그것도 경고**한다((3)). **C++ 만** 받는다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 막히는 대입, 포인터 변환 규칙, UB 의 경계가 전부 표준 문장이다.\
★★ 두 번째는 「**UB**」다 — **원래 `const` 인 객체**와 **문자열 리터럴**을 고치는 것.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준 (본체)** | 어느 구현에서도 같다 | `const` 의 위치와 뜻 · **막히는 대입 넷**(제약 위반) · **`char **` → `const char **` 와 `const char *const *` 가 막히는 것** · **비-`const` 객체를 캐스트로 떼고 고치는 것이 합법** · C 의 리터럴 타입 `char[N]` · **C 의 파일 스코프 `const` 가 외부 링크** · 에일리어싱 때문에 다시 읽어야 하는 것 | 에러 4건 `cc exit=1` · 경고 격자 · `plain = 99` 네 벌 · `_Generic` `char *` · `R K` · `twice_read(&x,&x) = 7` |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **없다** — 이 편의 규칙에는 조건이 붙지 않는다 | — |
| ★ **구현 정의** | 문서화 의무가 있다 | ★ `const` 객체와 리터럴을 **읽기 전용 구역에 두는 것**(그래서 `139`) · 진단 문구와 플래그 이름 · **제약 위반을 경고로 낼지 에러로 낼지** | `run exit=139` · 두 컴파일러의 문구 차 |
| ★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★ **이 편이 던진 것 중에는 없다.** (같은 문자열 리터럴 둘이 **한 배열을 쓰는지**는 미명시다 — **던지지 않았다**) | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **원래 `const` 인 객체를 고치는 것**(자동·정적) · ★★ **문자열 리터럴을 고치는 것** · ★ `char **` 반례의 `p[0] = 'X'`(결국 리터럴을 고친다) | ★★ **네 벌이 `99` / `1`(메모리 99) / `139` / `1`** · `run exit=139` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`char **` → `const char **` 가 경고 · `cc exit=0`** — 표준이 막으라는 것을 **빌드는 통과**시킨다. ★ `const char *const *` 도 같다 |
| **조건부 표준** | — |
| ★ **구현 정의** | ★★ **clang 의 에러 문구가 원인을 잘못 가리킨다**(③) — 도구가 말은 하는데 **틀린 말**을 한다 |
| ★ **미명시** | — (던진 것 없음) |
| ★★★ **UB** | ★★★ **`const` 를 캐스트로 떼고 쓰는 것에 경고 0건** — 캐스트는 **컴파일러에게 「알고 한다」고 말하는 것**이라 경고를 끈다. ★★ **ASan 은 원리상 못 본다**(할당된 범위 안의 쓰기) — 부적용 ★ **리터럴 쓰기에도 경고 0건**(`-Wwrite-strings` 없이는) |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드가 0인데 ill-formed」 새 항목 셋** — ① C 의 `char **` → `const char **` ② C 의 `char **` → `const char *const *` ③ **C++ 의 `char *s = "abc";`**(g++·clang++ 둘 다 경고 · `exit=0`). 셋 다 **`-pedantic-errors` 라야 `exit=1`** |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`const` 의 가장 큰 구멍은 「경고로 봐준 제약 위반」이다** — 반례가 `139` 로 죽는 변환이 `cc exit=0` 이다.
  - ★★★ **UB 쪽은 최적화 수준이 결과를 뒤집는다** — 정적 `const` 객체가 `-O0` 에서 죽고 `-O2` 에서 산다.
  - ★★ **`const` 가 약속하는 것은 「이 이름으로 안 고친다」뿐**이다 — 어셈블리가 그것을 **읽기 횟수로** 보여 줬다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 함수가 인자를 안 고친다고 알리기 | ★★★ **`const T *p`** | `T *const p`(호출자에게 의미 없다 — 지역 변수만 얼린다) |
| 문자열 리터럴을 가리키기 | ★★ **`const char *s = "abc";`** | ★ `char *s = "abc";` |
| 헤더에 상수 | ★ **C: `static const` · `enum` · `#define`** / C++: `const` · `constexpr` | ★ **C 헤더의 `const int K = 5;`**(외부 링크) |
| `const` 를 안 받는 옛 API 에 넘기기 | 그 API 가 **정말 안 고친다는 문서**를 확인하고 캐스트 | ★★ 원래 `const` 객체의 주소를 떼어 넘기기 |
| 두 포인터가 겹치지 않는다고 알리기 | ★ **`restrict`**([목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/)) | `const` 로 대신하기 |
| 한정자 위반을 빌드에서 막기 | ★★ **`-pedantic-errors`**(또는 `-Werror=incompatible-pointer-types`) | 경고 수만 세기 |

판단 규칙 두 줄.

- ★★★ **「`const` 가 무엇을 얼리나」는 `*` 의 왼쪽·오른쪽으로 읽는다.**
- ★★ **「`const` 를 떼도 되나」는 포인터가 아니라 원래 객체에 묻는다** — 그리고 호출된 쪽은 **그것을 알 수 없다.**

## 핵심 문장

- ★★★ **`const` 는 「이 경로로 안 고친다」는 약속이지 「안 바뀐다」는 보장이 아니다.**
- ★★★ **`const int *p` 를 받은 함수도 `-O2` 에서 `*p` 를 두 번 읽는다** — 두 컴파일러 다. 객체 자체가 `const` 인 `K` 만 `mov eax, 10` 으로 접혔다.
- ★★★ **`char **` → `const char **` 는 경고 · `cc exit=0` 인데 반례가 `run exit=139`** 로 죽는다 — 「종료 코드 0인데 ill-formed」.
- ★★★ **캐스트로 `const` 를 떼고 쓰면 원래 객체가 가른다** — 비-`const` 는 합법(`99`), 원래 `const` 는 UB(`99`·`1`·`139` 로 갈림).
- ★★ **C 는 `const char *const *` 도 막고 C++ 은 받는다.**
- ★★ **C 의 리터럴은 `char[4]`, C++ 은 `const char[4]`** — 둘 다 고치면 안 된다.
- ★★ **파일 스코프 `const` 는 C 에서 `R K`(외부), C++ 에서 `r _ZL1K`(내부)** — 두 파일 링크가 C 는 깨지고 C++ 은 통과했다.

## 관련 자료

- [01번 형제 — 선언 문법과 읽는 법](../01-declaration-syntax-and-reading/) — ★★ **읽는 법 일반**의 정본. 거기서 「`const` 는 계약이고 최적화 보장이 아니다(정본은 31번)」라고 넘긴 것을 여기서 **어셈블리로** 받았다.
- [14번 형제 — 포인터](../14-pointers-address-dereference-and-pointer-types/) — ★★ **직접 선행.**
- [20번 형제 — 널 종단 문자열과 문자열 리터럴](../20-null-terminated-strings-and-string-literals/) — ★★ **리터럴을 고치면 죽는 것**의 정본.
- [28번 형제 — 저장 기간](../28-choosing-among-four-storage-durations/) — ★ 리터럴 구역이 **`r--p`** 라는 실측.
- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★ `nm` 의 글자와 `_ZL` 의 뜻.
- [32번 형제 — `volatile`](../32-what-volatile-actually-guarantees/) — ★★ **같은 한정자 집안의 다른 짝.** `const` 가 「안 고친다」라면 `volatile` 은 「**매번 가서 본다**」다.
- [목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/) — `restrict` 와 앨리어싱 계약. **겹치지 않는다는 약속**의 정본.
- 목록의 **55번 주제** — 엄격한 앨리어싱 규칙. (4)의 「다시 읽는다」는 **같은 타입(`int`)끼리**라서다 — 타입이 다르면 그쪽 규칙이 나온다.
- ★ **C++ 갈래** — [C++ 10 — `const` 정확성](../../../cpp/syntax/10-const-correctness/)(네임스페이스 스코프 `const` 의 내부 링크 · `const_cast`) · [C++ 03 — 캐스트 4종](../../../cpp/syntax/03-four-cast-operators/).

## 용어 풀이

> **한정자(qualifier)** — 타입에 붙어 그 객체로 **무엇을 할 수 있나**를 바꾸는 낱말. `const`·`volatile`·`restrict`·`_Atomic`.\
> 예: `const int` 는 이 이름으로 대입할 수 없다.

> **const 객체** — **정의할 때부터** `const` 가 붙은 객체. 고치면 UB 다.\
> 예: `static const int K = 5;`. 반대로 `const int *p = &x;` 는 **x 가 const 객체가 아니다.**

> **제약 위반(constraint violation)** — 표준이 **진단을 요구하는** 규칙 위반. 진단이 경고여도 표준은 만족한다.\
> 예: `char **` 를 `const char **` 에 넣는 것 — 두 컴파일러가 경고로 냈다.

> **에일리어싱(aliasing)** — 두 이름이 같은 메모리를 가리키는 것.\
> 예: `twice_read(&x, &x)`.

> **즉치값(immediate)** — 명령 안에 **숫자로 박힌** 값. 메모리를 읽지 않는다.\
> 예: `mov eax, 10`.

> **`-Wwrite-strings`** — C 에서 문자열 리터럴을 **`const char[]` 처럼** 다루게 하는 경고 옵션.\
> 예: `char *s = "abc";` 에 경고가 난다.

## 더 들어가면

- ★★ **`restrict` 를 붙이면 `twice_read` 가 한 번만 읽나** — ★ **던지지 않았다**([목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/)).
- ★★ **C23 의 `constexpr` 객체** — 「컴파일 시간 상수」를 C 에도 들였다. ★ **던지지 않았다.**
- ★ **`const` 가 붙은 구조체 멤버**와 구조체 대입 — ★ **던지지 않았다.**
- ★ **같은 문자열 리터럴 둘이 같은 주소인가**(미명시) — ★ **던지지 않았다.**
- ★ **gcc 의 더 새 판에서 이 경고의 기본값이 바뀌었는가** — 이 머신에는 gcc 12·13 만 있어 **확인하지 못했다.** ★ **못 잰 것**.
