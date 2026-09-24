# c/syntax/26 — 유연 배열 멤버: 「**머리와 꼬리를 한 번에 잡는다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`sizeof` 와 `offsetof` 의 수치**(그리고 그 차) ② **바이트 덤프**(무엇이 옮겨졌나)
> ③ **에러인가 경고인가 침묵인가**, 그리고 **그때 `cc exit` 는 얼마인가**.
> ★★★ **이 주제의 가장 위험한 자리는 UB 가 아니다** — **표준 동작인데 기대가 틀린 곳**이라
> 다섯 층 표로는 안 잡힌다(4번). ★ 그 자리에서는 「**어느 도구가 잡나」가 아니라 「왜 아무도 안 잡나**」를 답해야 한다.
> ★★ **「경고 몇 건」만 세지 마라** — 이 주제에는 **경고가 났는데 `cc exit=0`** 인 자리가 다섯 군데다.
> 선행 — [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) · [22번 형제](../22-struct-padding-and-alignment/) · 목록의 **37번 주제**.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·2·4·5·6·9)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 네 구조체의 `sizeof` 와 `offsetof` 를 각각 적어야** 답이다 — 「`sizeof` 에 꼬리가 안 들어간다」까지만 적으면 절반이다.
- ★★★ **4번은 「무엇이 복사되나」가 아니라 「왜 아무도 안 말리나」까지 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 자리는 `sizeof` 를 쓰나 안 쓰나**」. 이 주제의 사고는 전부 거기서 갈린다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 네 가지 구조체의 `sizeof` 와 `offsetof` 를 나란히 재면 (예측) ★★★ 이 주제의 축

```c
/* s26a.c */
#include <stdio.h>
#include <stddef.h>

struct Msg  { int len; char data[]; };          /* 유연 배열 멤버 */
struct Gap  { int n; char c; char data[]; };    /* ★ 꼬리 패딩이 끼는 모양 */
struct Wide { char c; double d; char data[]; };
struct Old  { int len; char data[1]; };         /* C99 이전 관용구 */

int main(void) {
    printf("%-6s %-8s %-10s %s\n", "struct", "sizeof", "offsetof", "sizeof - offsetof");
    printf("%-6s %-8zu %-10zu %zu\n", "Msg",  sizeof(struct Msg),  offsetof(struct Msg,  data),
           sizeof(struct Msg)  - offsetof(struct Msg,  data));
    printf("%-6s %-8zu %-10zu %zu\n", "Gap",  sizeof(struct Gap),  offsetof(struct Gap,  data),
           sizeof(struct Gap)  - offsetof(struct Gap,  data));
    printf("%-6s %-8zu %-10zu %zu\n", "Wide", sizeof(struct Wide), offsetof(struct Wide, data),
           sizeof(struct Wide) - offsetof(struct Wide, data));
    printf("%-6s %-8zu %-10zu %zu\n", "Old",  sizeof(struct Old),  offsetof(struct Old,  data),
           sizeof(struct Old)  - offsetof(struct Old,  data));
    printf("\n★ sizeof 에 data 는 안 들어간다. Gap 은 sizeof 가 offsetof 보다 3 크다 (꼬리 패딩)\n");
    return 0;
}
```

- `Msg`·`Gap`·`Wide`·`Old` 의 `sizeof` 는 각각 얼마인가?
- `offsetof(…, data)` 는 각각 얼마인가?
- ★★ **둘이 갈리는 구조체**는 어느 것이고 **차이는 얼마**인가? 왜 갈리는가?
- ★★★ `malloc` 에 `sizeof + n` 을 주는 것과 `offsetof + n` 을 주는 것 중 **어느 쪽이 모자랄 수 있는가**?
- ★ `Old` 의 차이가 **4** 인 이유를 두 조각으로 나눠 설명하면?
- ★ 이 사실들은 **표준인가 구현 정의인가** — 하나씩 가르면?

### 2. 한 번의 할당으로 머리와 꼬리를 묶으면 (예측) ★★

```c
/* s26b.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

struct Msg { int len; char data[]; };

static struct Msg *msg_new(const char *s) {
    size_t n = strlen(s);
    struct Msg *m = malloc(sizeof *m + n);      /* ★ 헤더 + 꼬리를 한 번에 */
    if (!m) return NULL;
    m->len = (int)n;
    memcpy(m->data, s, n);
    return m;
}

int main(void) {
    struct Msg *m = msg_new("hello");
    printf("len=%d  data=%.*s\n", m->len, m->len, m->data);
    printf("malloc 한 바이트 = sizeof(struct Msg)(%zu) + 5 = %zu\n",
           sizeof(struct Msg), sizeof(struct Msg) + 5);
    printf("꼭 필요한 바이트  = offsetof(data)(%zu) + 5 = %zu\n",
           offsetof(struct Msg, data), offsetof(struct Msg, data) + 5);

    const unsigned char *b = (const unsigned char *)m;
    printf("바이트 :");
    for (size_t k = 0; k < sizeof *m + 5; k++) printf(" %02x", b[k]);
    printf("\n         ^^^^^^^^^^^ len(4바이트)  ^^^^^^^^^^^^^^ data 5바이트\n");
    free(m);
    return 0;
}
```

- 출력의 네 줄은 각각 무엇인가?
- ★★ 바이트 덤프는 무엇으로 나오는가? 어느 바이트가 `len` 이고 어느 바이트가 `data` 인가?
- ★ `sizeof *m + 5` 와 `offsetof(…, data) + 5` 가 **여기서는 같은 값**이다 — 왜인가?
- ★★ `char *data;` 로 두 번 할당하는 방식과 견주면 **무엇을 얻고 무엇을 잃는가**?
- ★ `sizeof(struct Msg)` 대신 `sizeof *m` 을 쓴 이유는?

### 3. 다섯 가지 배치를 던져 보면 — 어느 것이 에러이고 어느 것이 경고인가 (경계) ★★★

```c
/* s26c.c */
struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */

int main(void) { return 0; }
```

```c
/* s26c2.c */
struct Ok   { int n; char d[]; };
struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */

int main(void) { (void)arr; return 0; }
```

- 앞 파일의 두 줄은 **에러인가 경고인가**? `cc exit` 는?
- 뒤 파일의 세 줄은 **에러인가 경고인가**? `cc exit` 는?
- ★★★ 뒤 파일에서 **`-pedantic` 을 빼면** 무슨 일이 나는가?
- ★★ gcc 와 clang 의 **플래그 이름**이 어떻게 다른가? 그 차이가 실무에서 무엇을 뜻하는가?
- ★ 「이름 있는 멤버가 하나는 있어야 한다」는 규칙이 **왜 필요한가**?
- ★ clang 이 두 번째 에러에 **덧붙이는 줄**은 무엇인가?

### 4. 이 구조체를 대입하면 (예측) ★★★ 본체

```c
/* s26d.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

static struct Msg *msg_new(const char *s) {
    size_t n = strlen(s);
    struct Msg *m = malloc(sizeof *m + n);
    m->len = (int)n;
    memcpy(m->data, s, n);
    return m;
}

int main(void) {
    struct Msg *a = msg_new("hello");
    struct Msg *b = malloc(sizeof *b + 5);      /* 넉넉히 잡아 둔다 */
    memset(b, 0, sizeof *b + 5);

    *b = *a;                                    /* ★ 구조체 대입 */

    printf("원본   : len=%d data=%.5s\n", a->len, a->data);
    printf("복사본 : len=%d data=%.5s\n", b->len, b->data);
    printf("data 5바이트 :");
    for (int k = 0; k < 5; k++) printf(" %02x", (unsigned char)b->data[k]);
    printf("   <- 원본은 68 65 6c 6c 6f 였다\n");
    printf("memcpy(sizeof *a) 도 같다 — 옮기는 것은 %zu 바이트뿐이다\n", sizeof *a);
    free(a); free(b);
    return 0;
}
```

- 복사본의 `len` 은 얼마인가? `data` 는 무엇으로 찍히는가?
- ★★ **여섯 벌**(gcc·clang × `-O0`/`-O2` + ASan·UBSan + FORTIFY)에서 **경고가 몇 건**씩 나오는가?
- ★★★ 아무도 안 말리는 이유는 무엇인가 — **이것이 UB 인가**?
- ★★ `memcpy(b, a, sizeof *a)` 는 다른가?
- ★ **옳은 복사법**을 한 줄로 쓰면?
- ★★ 이 사고가 「제5의 상태」인 이유는? **틀린 것이 값인가 아니면 다른 것인가**?

### 5. 꼬리를 한 칸 넘겨 쓰면 (예측) ★★

```c
/* s26e.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);       /* ★ ASan 이 abort 해도 stdout 이 안 사라지게 */
    size_t n = 5;
    struct Msg *m = malloc(sizeof *m + n);  /* data 는 5바이트뿐이다 */
    m->len = (int)n;
    memcpy(m->data, "hello", n);
    printf("여기까지는 정상이다 : %.5s\n", m->data);
    m->data[n] = '!';                       /* ★ 한 칸 넘는다 */
    printf("★ 한 칸 넘겨 썼다 — 이 줄이 보이나? 빌드에 달렸다\n");
    free(m);
    return 0;
}
```

- 그냥 빌드해서 돌리면 무슨 일이 나는가? `run exit` 는?
- ★★ ASan 빌드로 돌리면 무엇이 나오는가? **에러 이름**과 **접근 크기**는?
- ★★★ ASan 리포트가 **할당 크기**를 얼마라고 적는가? 그 숫자가 어디서 왔는가?
- ★★ 소스 첫 줄의 `setvbuf(stdout, NULL, _IONBF, 0)` 가 **없으면** 무슨 일이 나는가?
- ★ 컴파일러가 이것을 못 보는 이유는?
- ★ ASan 리포트에서 **실행마다 바뀌는 칸**과 **안 바뀌는 칸**을 가르면?

### 6. C99 이전의 「길이 1 배열」과 나란히 놓으면 (예측) ★★

```c
/* s26f.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>

struct New { int len; char data[]; };   /* C99 부터 — 유연 배열 멤버 */
struct Old { int len; char data[1]; };  /* C99 이전 관용구 — 「길이 1」 */

int main(void) {
    const char *s = "hello";
    size_t n = strlen(s);

    size_t need_new = sizeof(struct New) + n;
    size_t need_old = sizeof(struct Old) - 1 + n;
    size_t exact    = offsetof(struct New, data) + n;

    struct New *a = malloc(need_new);
    struct Old *b = malloc(need_old);
    a->len = (int)n; memcpy(a->data, s, n);
    b->len = (int)n; memcpy(b->data, s, n);

    printf("New sizeof=%zu  Old sizeof=%zu   (Old 는 data[1] 한 바이트를 포함한다)\n",
           sizeof(struct New), sizeof(struct Old));
    printf("New 할당식 sizeof+n       = %zu\n", need_new);
    printf("Old 할당식 sizeof-1+n     = %zu   <- ★ %zu 바이트 더 잡았다\n",
           need_old, need_old - need_new);
    printf("꼭 필요한 바이트 offsetof+n = %zu\n", exact);
    printf("\n둘 다 읽힌다 : new=%.5s old=%.5s\n", a->data, b->data);
    printf("★ 출력도 같고 진단도 없다 — 갈리는 것은 할당 산술과 ★ 표준이 보장하느냐 ★ 뿐이다\n");
    free(a); free(b);
    return 0;
}
```

- 두 방식의 `sizeof` 는 각각 얼마인가?
- 두 할당식은 각각 몇 바이트를 잡는가? **꼭 필요한 바이트**는 얼마인가?
- ★★★ **출력이 갈리는가**? **진단이 갈리는가**?
- ★★ 그러면 **무엇이 갈리는가** — 두 가지를 대면?
- ★ `sizeof - 1 + n` 의 `- 1` 은 무엇을 빼는 것인가? **무엇을 못 빼는가**?
- ★ 낡은 코드에서 `- 1` 을 지우면 어떻게 되는가?

### 7. `-D_FORTIFY_SOURCE=2 -O2` 는 무엇을 보나 (경계) ★★

```c
/* s26g.c */
#include <stdio.h>
#include <string.h>

struct New { int len; char data[]; };
struct Old { int len; char data[1]; };

static struct New g_new;        /* 크기를 아는 객체 — data 는 0바이트다 */
static struct Old g_old;        /* 크기를 아는 객체 — data 는 1바이트다 */

int main(void) {
    strcpy(g_new.data, "hello");   /* 둘 다 넘친다 */
    strcpy(g_old.data, "hello");
    printf("%s %s\n", g_new.data, g_old.data);
    return 0;
}
```

- 이 파일을 `-O2 -D_FORTIFY_SOURCE=2` 로 던지면 무슨 진단이 나오는가? **`cc exit` 는**?
- ★ 같은 플래그로 6번의 `s26f.c`(`malloc` 을 쓰는 쪽)를 던지면 **몇 건**이 나오는가?
- ★★★ 그래서 **갈리는 축**은 「FAM 이냐 길이 1 배열이냐」인가, 아니면 다른 것인가?
- ★★ 그 사실이 **실전에서 무엇을 뜻하는가** — FAM 은 어떤 객체로 쓰이는가?
- ★ 그러면 경계는 **무엇이 지키는가**?

### 8. 초기자로 만들려 하면 (왜) ★★

```c
/* s26h.c */
#include <stdio.h>

struct Msg { int len; char data[]; };

static struct Msg g = { 3, { 'a', 'b', 'c' } };   /* (1) 정적 저장 기간 */

int main(void) {
    struct Msg m = { 3, { 'a', 'b', 'c' } };      /* (2) 자동 저장 기간 */
    struct Msg z = { 3 };                          /* (3) 꼬리를 안 적는다 */
    printf("%d %c\n", g.len, g.data[0]);
    printf("%d %d\n", m.len, z.len);
    return 0;
}
```

- 세 줄은 각각 통과하는가? `cc exit` 는?
- ★★ **정적 저장 기간**과 **자동 저장 기간**이 갈리는 이유는?
- ★ `{ 3 }` 처럼 꼬리를 안 적으면 아무 말이 없다 — 그 객체는 **쓸모가 있는가**?
- ★★ 그래서 FAM 구조체는 **거의 언제나 어느 저장 기간**에 놓이는가?
- ★ 정적 쪽만 남기면 `cc exit` 가 얼마가 되는가? 그것이 무슨 뜻인가?

### 9. 한 덩어리에 셋을 담고 인덱싱하면 (예측) ★★★

```c
/* s26i.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Msg { int len; char data[]; };

int main(void) {
    const size_t payload = 8;
    const size_t stride  = sizeof(struct Msg) + payload;   /* 한 칸의 진짜 크기 */
    char *buf = malloc(stride * 3);
    memset(buf, 0, stride * 3);

    for (int i = 0; i < 3; i++) {                           /* ★ 손으로 stride 를 곱한다 */
        struct Msg *m = (struct Msg *)(buf + (size_t)i * stride);
        m->len = i;
        memcpy(m->data, "abcdefgh", payload);
        m->data[0] = (char)('A' + i);
    }

    struct Msg *m0 = (struct Msg *)buf;
    printf("sizeof(struct Msg) = %zu · 내가 쓴 stride = %zu\n", sizeof(struct Msg), stride);
    printf("m0 + 1 은 %td 바이트 뒤다   <- ★ stride 가 아니다\n",
           (char *)(m0 + 1) - (char *)m0);
    printf("m0[1].len = %d   <- 두 번째 칸의 len 이 아니다\n", m0[1].len);
    printf("\n손으로 stride 를 곱해 읽으면\n");
    for (int i = 0; i < 3; i++) {
        struct Msg *m = (struct Msg *)(buf + (size_t)i * stride);
        printf("  칸 %d : len=%d data=%.8s\n", i, m->len, m->data);
    }
    free(buf);
    return 0;
}
```

- `sizeof(struct Msg)` 와 내가 쓴 `stride` 는 각각 얼마인가?
- ★★★ `m0 + 1` 은 **몇 바이트** 뒤인가? 왜 그 값인가?
- ★★ `m0[1].len` 은 얼마로 찍히는가? ★ 그 수를 **16진으로 바꾸면** 무엇이 보이는가?
- ★ 그 수가 **알아보기 쉬운 편이었다** — 어떤 경우에 못 알아챘을까?
- ★★ 제대로 읽으려면 어떻게 해야 하는가?
- ★ 그래서 FAM 구조체를 여러 개 다루는 **옳은 형태**는 무엇인가?

### 10. 왜 마지막이어야 하고 왜 혼자 있으면 안 되나 (왜) ★★

- ★★ FAM 이 **마지막 멤버여야 하는** 이유는?
- ★★ **이름 있는 멤버가 최소 하나** 있어야 하는 이유는?
- ★ 다른 구조체가 FAM 구조체를 **값으로 품으면** 실제로 무엇이 무너지는가?
- ★ `struct Ok arr[4];` 가 무너지는 이유는 9번과 **같은 이유인가 다른 이유인가**?
- ★★ 이 넷 중 **표준이 에러로 막는 것**과 **구현이 확장으로 받아 주는 것**을 가르면?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은?
- ★★★ 4번의 사고는 **어느 칸에 들어가는가**? 그 답이 무엇을 말해 주는가?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★ 「**종료 코드가 0인데 ill-formed**」인 자리가 **몇 군데**인가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **왜 패딩이 생기나**와 **패딩 바이트의 값**은 어느 주제가 정본인가?
- **`a[i]` 가 `*(a+i)` 이고 걸음이 `sizeof` 라는 것**은 어느 주제인가?
- **`realloc` 의 계약**과 **배열 밖 접근**은 각각 어느 주제인가?
- ★ **크기를 모르는 배열**(`extern char msg[];`)과 이 주제는 **무엇이 다른가**?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★★ **C++ 에서 갈라지는 자리**는 어디인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
