# c/syntax/19 — `void *`·널 포인터·`NULL`: 「**타입을 잠시 벗는 포인터와, 어디도 안 가리키는 값**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 「누가 보장하나」다.** 같은 출력이라도 **표준이 정한 것**인지
> **이 구현이 그랬을 뿐**인지를 갈라서 답해라. 두 번째 줄을 못 붙이면 그 문항은 틀린 것으로 친다.
> ★★ **「경고 몇 건」과 「종료 코드」를 같이 적어라.** 이 주제의 표준 위반 둘은 **`-pedantic` 이 있어야** 보이고,
> 널 역참조는 **출력이 아니라 종료 코드로** 갈린다.
> ★★★ **컴파일러와 최적화 수준을 안 밝힌 답은 이 주제에서 오답이다** — 「널을 역참조하면 죽는다」는
> 한 줄짜리 답이 **여기서 실제로 깨진다.**
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [05번 형제](../05-explicit-casts-and-pointer-conversions/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `void *` 로 갔다 되돌아오면 (예측) ★★

```text
(발췌 — 전문은 정답 파일에)

int i = 7;  double d = 2.5;  struct P p = {1, 2};

void *v1 = &i;          void *v2 = &d;          void *v3 = &p;
int *pi = v1;           double *pd = v2;        struct P *pp = v3;

(void *)&i == v1 ?
int *arr = malloc(3 * sizeof *arr);   memset(arr, 0, 3 * sizeof *arr);   arr[1] = 42;
sizeof(void *)   sizeof(int *)   sizeof(char *)
```

- 이 소스에 **캐스트가 몇 번** 필요한가?
- `(void *)&i == v1` 은 무엇을 내는가 — **주소값이 보존되는가?**
- `arr[0] arr[1] arr[2]` 는 각각 얼마인가?
- 세 `sizeof` 는 각각 얼마이고, ★ 그중 **표준이 정한 것**은 무엇인가?
- 경고는 몇 건인가?

### 2. 함수 포인터를 `void *` 에 넣으면 (예측) ★★★ 이 주제의 축 하나

```c
/* ex2.c */
#include <stdio.h>

static int twice(int n) { return 2 * n; }

int main(void) {
    int i = 7;
    void *ok = &i;              /* 객체 포인터는 조용하다 */
    printf("객체 포인터 -> void* : %s\n", ok == &i ? "간다" : "?");

    void *fp1 = twice;          /* (가) 함수 -> void * : 캐스트 없이 */
    void *fp2 = (void *)twice;  /* (나) 명시 캐스트를 붙여도 */
    int (*back)(int) = fp2;     /* (다) void * -> 함수 포인터 */
    printf("함수 포인터 -> void* -> 함수 포인터 : back(21) = %d\n", back(21));
    printf("fp1 == fp2 : %s\n", fp1 == fp2 ? "같다" : "다르다");
    return 0;
}
```

- **컴파일되는가?** 된다면 `back(21)` 은 얼마이고 `fp1 == fp2` 는 무엇인가?
- 경고는 gcc 몇 건, clang 몇 건인가 — ★ **둘이 같은가?**
- ★ **명시 캐스트를 붙인 (나) 줄에 대해** 두 컴파일러가 같은 답을 하는가?
- ★★ **`-pedantic` 을 빼면** 몇 건인가?
- 이것은 몇 번째 층의 일인가 — **에러인가 경고인가?**

### 3. `void *` 에 `+1` 을 하면 (예측) ★★

```c
/* ex3.c */
#include <stdio.h>

int main(void) {
    int a[4] = {10, 20, 30, 40};
    void *v = a;
    char *c = (char *)a;

    printf("sizeof(void) = %zu   (표준에는 없다 — gcc 확장이 1 로 친다)\n", sizeof(void));
    printf("v      = %s\n", "a 의 첫 바이트");
    printf("v+1 - v      = %td 바이트\n", (char *)(v + 1) - (char *)v);
    printf("c+1 - c      = %td 바이트\n", (c + 1) - c);
    void *w = v;
    w++;                                   /* void * 증가 */
    printf("w++ 뒤 w - v = %td 바이트\n", (char *)w - (char *)v);
    printf("v 로 4바이트 뒤를 읽으면 : %d\n", *(int *)((char *)v + 4));
    return 0;
}
```

- `sizeof(void)` 는 **컴파일이 되는가?** 된다면 얼마인가?
- `v + 1` 은 **몇 바이트** 움직이는가 — `c + 1` 과 같은가?
- 경고는 gcc 몇 건, clang 몇 건이고 ★ **플래그 이름이 같은가?**
- ★★ `-pedantic` 을 빼면 몇 건인가?
- `-Werror=pointer-arith` 를 붙이면 **종료 코드**가 얼마인가?

### 4. 네 가지 널 표기를 `_Generic` 에 넣으면 (예측) ★★★

```text
(발췌 — 전문은 정답 파일에)

#define TYPE(e) _Generic((e), void *: "void *", int: "int", long: "long",
                              char *: "char *", default: "그 밖")

TYPE(NULL)   TYPE(0)   TYPE((void *)0)   TYPE(0L)

char *cp = NULL;   char *c0 = 0;   char *cv = (void *)0;
/* 셋이 널인지 · 셋이 서로 같은지 · cp 의 바이트 8개를 찍는다 */
```

- **네 타입 이름**은 각각 무엇인가?
- `cp`·`c0`·`cv` 는 **셋 다 널인가**, 그리고 **서로 같은가?**
- 널 포인터의 **여덟 바이트**는 무엇으로 찍히는가?
- ★★ 그 바이트는 **보장인가 관찰인가?**

### 5. 가변 인자 끝을 세 가지로 적으면 (예측) ★★★

```text
(발췌 — 전문은 정답 파일에)

static int count_until_null(int first, ...) {
    /* va_arg(ap, char *) 로 꺼내다가 NULL 을 만나면 센 개수를 돌려준다 */
}

count_until_null(0, "a", "b", 0);
count_until_null(0, "a", "b", NULL);
count_until_null(0, "a", "b", (char *)0);
```

그리고 인자를 늘려 **끝이 스택으로 밀려나는** 판을 따로 컴파일했다.

```c
/* ex8.c */
#include <stddef.h>

extern int f(int first, ...);

/* 인자가 많아 레지스터를 다 쓰고 스택으로 넘어가는 자리 */
int with_zero(void) { return f(0, "a", "b", "c", "d", "e", "f", "g", 0); }
int with_null(void) { return f(0, "a", "b", "c", "d", "e", "f", "g", (char *)NULL); }
```

- **세 줄의 출력**은 각각 무엇인가 — ★ **하나가 깨지는가?**
- ★★ `with_zero` 와 `with_null` 의 **기계어**는 얼마나 다른가?
- 그 결과가 「`0` 을 넘겨도 된다」는 뜻인가 — **아니라면 왜인가?**
- ★ 그렇다면 왜 관례는 `(char *)NULL` 인가?

### 6. 널을 역참조하면 (예측) ★★★ 이 주제의 축 둘

```c
/* ex10.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int *p = NULL;
    printf("역참조 직전\n");
    int v = *p;
    printf("읽은 값 = %d\n", v);
    return 0;
}
```

- gcc **기본**(`-O` 없음)·`-O1`·`-O2` 의 **출력과 종료 코드**는?
- clang `-O0`·`-O1`·`-O2` 는? — ★ **여섯 벌이 같은가?**
- 갈리는 것이 있다면 **경계선이 어디에 그어지는가** — **최적화 수준인가 컴파일러인가?**
- 갈린 벌의 **어셈블리에는 무엇이 달라져 있는가?**
- UBSan 은 무엇을 찍고 **몇 번으로 끝나는가** — ASan 은?
- ★★ 같은 바이너리를 세 번 돌리면 출력이 같은가?

### 7. `NULL` 은 어디서 오나 (경계) ★★

```c
/* nulldef.c */
#include <stddef.h>
NULL
```

- `gcc -E` 와 `clang -E` 가 각각 **무엇으로** 펼치는가 — ★ **두 문자열이 같은가?**
- `g++ -E` 는 무엇으로 펼치는가?
- 헤더 하나에 `#define NULL` 이 **몇 개** 들어 있는가?
- ★ `-std=c2x` 로 바꾸면 gcc 의 `NULL` 이 달라지는가?
- 이것은 다섯 층 중 어느 칸인가?

### 8. C23 `nullptr` (연결) ★★

```text
(발췌 — 전문은 정답 파일에)

printf("%ldL\n", (long)__STDC_VERSION__);
_Generic(NULL,    void *: …, nullptr_t: …, int: …)
_Generic(nullptr, void *: …, nullptr_t: …, int: …)
char *p = nullptr;
nullptr == NULL
```

- gcc `-std=c2x` 와 clang `-std=c23` 에서 `__STDC_VERSION__` 은 각각 얼마인가?
- `NULL` 과 `nullptr` 의 **타입 이름**은 각각 무엇인가 — ★ **같은가?**
- `-std=c17` 로 돌리면 gcc 는 **에러 몇 개**, clang 은 몇 개인가?
- ★★ gcc 13 은 `-std=c17 -pedantic` 에서 **`nullptr_t` 라는 이름**을 아는가?
- `nullptr == NULL` 은 무엇을 내는가?

### 9. 널 포인터 「상수」와 널 포인터 「값」 (왜) ★★★

- 널 포인터 **상수**의 정의는 무엇인가 — **어느 낱말들이 그 범주에 드는가?**
- 널 포인터 **값**은 그것과 어떻게 다른가?
- `char *p = NULL; char *q = p;` 에서 **`p` 는 널 포인터 상수인가?**
- ★★ 이 구분이 **살아나는 자리**는 어디인가 — 그리고 왜 하필 거기인가?
- `(void *)0` 은 상수인데 `(char *)0` 도 상수인가?

### 10. `memset` 으로 0 을 채운 포인터 (경계) ★★

```text
(발췌 — 전문은 정답 파일에)

struct Node { struct Node *next; int v; };

struct Node n;            memset(&n, 0, sizeof n);       n.next == NULL ?
struct Node *arr = calloc(4, sizeof *arr);                arr[2].next == NULL ?
struct Node *null_p = NULL;   /* NULL 의 바이트와 0 채움을 memcmp 로 대조한다 */
```

- 세 줄의 출력은 각각 무엇인가?
- ★★ 그것이 **표준의 보장**인가 — 아니라면 **무엇이 보장인가?**
- `calloc` 이 주는 것은 「0 으로 채운 바이트」인가 「널 포인터 배열」인가?
- 널로 채우고 싶으면 **무엇을 쓰는 것이 맞는가?**

### 11. 어느 도구가 무엇을 보나 (연결) ★★

- 이 주제에서 **`-pedantic` 이 있어야만** 보이는 것 둘은 무엇인가?
- ★★ 그 둘을 `-Wall -Wextra` 로만 컴파일하면 경고가 **몇 건**인가?
- `NULL` 의 실제 정의는 **어느 도구**로 봐야 보이는가?
- 널 역참조에 대해 **컴파일 진단**은 몇 건인가 — UBSan 과 ASan 의 **종료 코드**는?
- ★★★ **이 주제의 네 번째·다섯 번째 창**은 무엇인가?

### 12. 다섯 층·무게중심과 경계 (연결) ★★

- **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- 이 주제의 **무게중심**은 어느 칸인가 — [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 같은가?
- 캐스트 일반 · 포인터 기본 · `memset` 계약 · 널 역참조의 실패 계급은 **각각 어느 주제가 정본**인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
