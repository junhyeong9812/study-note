# c/syntax/31 — `const` 와 포인터 const 위치: 「**`const` 는 약속이지 보장이 아니다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · g++/clang++ 같은 판 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`*` 의 어느 쪽에 `const` 가 있나**(오른쪽에서 왼쪽으로 읽기) ② **`const` 가 약속하지 않는 것**(에일리어싱 · 캐스트 · 리터럴)
> ③ **C 와 C++ 이 갈리는 자리**(`char **` · 리터럴 타입 · 파일 스코프 링크).
> ★★★ **본체 창은 `-O2` 어셈블리** — 4번은 **명령 수**까지 적어야 답이다. ★ **시간은 묻지 않는다** — 이 편은 재지 않았다.
> ★★★ **5번은 판 격자**다 — 네 벌을 다 적어라.
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [29번 형제](../29-scope-and-linkage-static-extern/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **3번은 「경고다」로 끝내면 답이 아니다** — **`cc exit` · `run exit` · 왜 막아야 하나**까지.
- ★★ **2번은 에러 문구를 두 컴파일러로** — 그리고 **어느 문구가 원인을 틀리게 가리키나**도.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 `const` 는 포인터의 약속인가, 객체의 성질인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 가지 선언 — 되는 대입 (예측) ★★

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

- 출력 한 줄은?
- ★★ `p1`·`p2`·`p3` 를 **오른쪽에서 왼쪽으로** 소리 내어 읽으면?
- ★★ `p3` 는 `const char *const` 인데 **왜 `Abc` 를 보는가**?
- ★ `char const *p` 는 셋 중 **어느 것과 같은가**?

### 2. 막히는 대입 넷 — 진단 전문 (예측) ★★

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

- ★★ 네 줄 각각에 **gcc 는 무엇이라** 말하는가? 두 가지 문구가 **무엇을 가르는가**?
- ★★★ **clang 의 ③(`p3[0] = 'X'`) 문구**는 원인을 **맞게** 가리키는가?
- ★ `cc exit` 는? gcc 가 **덤으로** 다는 경고는 무엇이고 왜 나오나?

### 3. `char **` 를 `const char **` 자리에 (예측) ★★★ 유명한 함정

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

- ★★★ 두 컴파일러에서 **경고인가 에러인가**? `cc exit` 는?
- ★★★ 실행하면 **`run exit`** 는? 출력은 몇 줄 나오는가?
- ★★★ **왜 이 변환을 막아야 하나** — 반례의 두 줄이 **각자 정당한데** 합치면 무엇이 새는가?
- ★★ 두 컴파일러의 **플래그 이름** 중 **원인을 더 정확히 말하는 쪽**은?
- ★★ `char **` 를 **`const char *const *`** 자리에 넣으면(`s31c2.c`) C 는 받는가? **C++ 은**?
- ★ `-std=c2x` 와 `-pedantic-errors` 는 결과를 바꾸는가?

### 4. `const int *p` 를 받은 함수의 어셈블리 (예측) ★★★ 본체

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

- ★★★ `-O2` 에서 `twice_read` 는 `[rdi]` 를 **몇 번** 읽는가? **gcc 와 clang 이 같은가**?
- ★★★ `across_call` 은 `call opaque` 뒤에 `*p` 를 **다시 읽는가**?
- ★★★ `const_object` 는 `K` 를 **몇 번** 읽는가? 무엇이 남는가?
- ★★ 갈림은 **「포인터가 `const` 냐」인가 「객체가 `const` 냐」인가**?
- ★★ `-O0` 에서 `K` 는 **메모리로 읽히는가**?
- ★ 이 결과로 「**`const` 가 빠르다**」를 말할 수 있는가?

### 5. `const` 를 캐스트로 떼고 쓰기 — 세 객체 × 네 벌 (예측) ★★★

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

- ★★★ `plain` · `local_c`(그리고 같은 자리를 `volatile` 로 다시 읽은 값) · `static_c` 를 **네 벌**(gcc·clang × `-O0`/`-O2`)에서 각각 적으면?
- ★★★ 「**한 객체가 두 값**」처럼 보이는 칸은 어디인가? 왜 그렇게 보이는가?
- ★★★ `static_c` 에서 **최적화 수준이 「죽는다 / 산다」를 뒤집는가**?
- ★★ 세 객체 중 **합법인 것**은? 나머지 둘은 **어느 층**인가?
- ★ **호출된 함수(`sneaky`) 쪽에서** 떼도 되는지 알 수 있는가?

### 6. 문자열 리터럴 — C 와 C++ (예측) ★★

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

- ★★ C 에서 `"abc"` 가 감쇠한 타입은? `char *s = "abc";` 에 **경고가 나는가**?
- ★★★ 실행하면 `run exit` 는?
- ★★ `-Wwrite-strings` 를 켜면? ★ clang 의 문구가 **리터럴의 타입을 무엇이라** 부르는가?
- ★★ C++ 에서 `"abc"` 는 `const char[4]` 인가? `char *s = "abc";` 는 **경고인가 에러인가**? `-pedantic-errors` 면?

### 7. 파일 스코프 `const` 의 링크 — C 대 C++ (연결) ★★★

- ★★★ `const int K = 5;` 한 줄을 C 와 C++ 로 컴파일하면 `nm` 에서 **각각 무슨 글자와 이름**인가?
- ★★ C++ 에서 **`extern const int K2 = 6;`** 은?
- ★★★ 두 파일에 같은 줄을 두면 **C 와 C++ 의 링크 결과**는?
- ★★ 그래서 **C 헤더에 상수를 두는 옳은 방법**은?
- ★ C++ 이름의 **`_ZL`** 은 무엇을 뜻하는가?

### 8. `const` 는 무엇을 약속하고 무엇을 약속하지 않나 (왜) ★★★

- ★★★ `const int *p` 가 약속하는 것은 **한 문장으로** 무엇인가?
- ★★★ 그 약속이 **「`*p` 가 안 바뀐다」가 아닌 이유**를 `s31d2.c` 의 출력으로 설명하면?

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

- ★★ 「두 포인터가 겹치지 않는다」를 약속하는 한정자는?
- ★ 4번의 두 번 읽기를 「**느리다**」로 적으면 무엇이 틀리는가?

### 9. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★ **비어 있는 칸**은? **정말 빈 것과 안 던진 것**을 갈라 답하면?
- ★★★ 이 편의 「**종료 코드 0인데 ill-formed**」 항목은 **몇 개**이고 각각 무엇인가?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★ **sanitizer 창이 부적용**인 이유는?

### 10. `const` 와 `volatile` 은 어떻게 짝을 이루나 (연결) ★

- ★ 둘 다 **한정자**다 — `const` 가 「안 고친다」라면 `volatile` 은 **무엇**을 약속하는가?
- ★ `const volatile` 을 함께 붙이는 자리를 **하나** 떠올리면?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **선언 읽는 법 일반** · **포인터 자체** · **리터럴의 저장 기간**은 각각 어느 형제가 정본인가?
- **`restrict`** 와 **엄격한 앨리어싱**은 각각 목록의 몇 번 주제인가?
- ★ C++ 쪽 대비의 정본은?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
