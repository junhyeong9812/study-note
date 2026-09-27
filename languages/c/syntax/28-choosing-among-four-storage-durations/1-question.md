# c/syntax/28 — 저장 기간 4종을 고르는 법: 「**이 값은 언제 태어나 언제 죽나**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic` · `ulimit -s` = 8192 KiB.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **언제 태어나 언제 죽나**(네 저장 기간) ② 주소가 아니라 「**어느 구역·같은 객체인가**」
> ③ **죽은 뒤에 읽으면 여섯 벌이 어떻게 갈리나**.
> ★★★ **5번은 한 벌로 답하지 마라** — **컴파일러 2 × 최적화 3 = 여섯 벌**을 다 적어야 한다.
> ★★★ 그리고 **여기서 갈린 축은 [27번 형제](../27-compound-literals/)와 다르다** — 무엇이었는지가 문항의 절반이다.
> ★★ **주소 자체는 흔들린다**(ASLR). 근거로 쓸 수 있는 것은 **구역 이름 · 권한 · 주소들 사이의 차 · 같은 객체인가**뿐이다.
> ★ **「진단이 0건」인 자리가 하나 있다** — 그것이 무엇인지도 답해야 한다(4번).
> 선행 — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · [목록의 **37번 주제**](../37-malloc-calloc-realloc-free/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·2·3·4·5·7)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **5번은 「UB 다」로 끝내면 답이 아니다** — **여섯 칸과 `run exit` 를 채워야** 답이다.
- ★★ **1번과 7번은 「주소가 얼마인가」가 아니라 「어느 구역인가 · 같은가 다른가」를 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 객체는 몇 개 있고 언제 죽나**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 객체의 주소를 `/proc/self/maps` 에 대조하면 (예측) ★★★ 이 주제의 축

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

- 여섯 줄의 **구역**은 각각 무엇으로 나오는가?
- ★★★ 여섯 줄 중 **권한이 다른 것**이 하나 있다 — 무엇이고 무엇이 없는가?
- ★★ 그 사실이 **어느 형제 주제의 결론**을 설명하는가?
- ★★ `_Thread_local` 은 어느 구역에 있는가? **왜 실행 파일 이미지가 아닌가**?
- ★★★ 이 출력에서 **실행마다 바뀌는 칸**은 어느 것이고 **안 바뀌는 칸**은 어느 것인가?
- ★ `(char *)&s_data - (char *)&s_bss` 는 얼마인가? 그 값을 **근거로 써도 되는가**?

### 2. 같은 함수를 세 번 부르면 (예측) ★★★

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

- `a` 와 `s` 는 세 호출에서 각각 무엇으로 찍히는가?
- ★★★ `&a` 가 **첫 호출과 같은 자리인가**? 세 번 다?
- ★★★ 「주소가 같다」가 「**살아 있다**」는 뜻인가? 왜 그렇게 판단하는가?
- ★★ 이 오해가 **5번의 UB 를 어떻게 보이게** 만드는가?
- ★★ **함수 안 `static`** 과 **파일 스코프 `static`** 은 무엇을 바꾸는가 — 같은가 다른가?
- ★ `static` 의 초기화는 **언제** 일어나는가?

### 3. 초기화를 안 하면 (예측) ★★★

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

- 정적 쪽 두 줄은 무엇으로 찍히는가? ★ 그것은 **보장인가 관찰인가**?
- 자동 쪽 두 줄은 무엇으로 찍히는가?
- ★★★ **여섯 벌**(gcc·clang × `-O0`/`-O1`/`-O2`)에서 `a_indet` 은 어떻게 갈리는가?
- ★★ **gcc 에서 `a_indet` 이 `0` 으로 나오는 것**을 근거로 「자동 변수도 0 이다」라고 쓰면 무엇이 틀리는가?
- ★ 경고는 **몇 건** 나오고 플래그는 무엇인가? ★ `cc exit` 는?
- ★★ 이 격자에서 **대조할 것**은 숫자인가 다른 것인가?

### 4. 자동 저장 기간에 1 · 4 · 64 MiB 를 잡으면 (예측) ★★

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

- `ulimit -s` 는 얼마인가?
- 세 크기에서 각각 무슨 일이 나는가? ★ `run exit` 는?
- ★★★ **컴파일러가 경고를 몇 건** 내는가? 왜 그런가?
- ★★ 같은 크기를 `malloc` 으로 잡으면 어떻게 되는가? **실패를 알 수 있는가**?
- ★★ 스택 한도는 **어느 층**에 속하는가? 같은 바이너리가 환경에 따라 달라지는가?
- ★ 64 MiB 벌에서 **첫 줄이 남은 이유**는?

### 5. 지역 변수의 주소를 돌려주면 (예측) ★★★ 본체

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

- ★★★ **여섯 벌**(gcc·clang × `-O0`/`-O1`/`-O2`)의 `run exit` 와 출력을 각각 적으면?
- ★★★ 그중 **「정답처럼 보이는」 칸**은 몇 개이고 어느 것인가?
- ★★★ **갈린 축**이 무엇인가? ★ [27번 형제](../27-compound-literals/)와 **같은 축인가 다른 축인가**?
- ★★ gcc 와 clang 의 **경고 건수**와 **플래그 이름**은 각각 무엇인가? `cc exit` 는?
- ★ 정적 쪽(`ok_static`)은 여섯 벌에서 어떻게 나오는가?
- ★★ 이 UB 를 **`-pedantic-errors` 로 막을 수 있는가**?

### 6. 왜 gcc 만 죽나 (왜) ★★★

```c
/* s28d2.c */
int *leak_auto(void) {
    int local = 1234;
    return &local;              /* ★ 블록이 끝나면 죽는 자리를 돌려준다 */
}
```

- ★★★ `gcc -O1 -S -masm=intel` 로 찍으면 `leak_auto` 가 무엇으로 번역되는가?
- ★★★ clang 은 무엇으로 번역하는가?
- ★★★ 그 두 줄이 5번의 결과를 **어떻게 설명하는가**?
- ★★ ASan 리포트가 **무슨 주소**를 가리키고 **무슨 Hint** 를 적는가? 그것이 역어셈블과 **어떻게 맞물리는가**?
- ★★ 세 창(경고·실행 출력·sanitizer) 중 **이 질문에 답하는 창**이 있는가? 그러면 **네 번째 창**은 무엇인가?
- ★ 「값이 나오는 컴파일러」와 「죽는 컴파일러」 중 **어느 쪽이 안전한가**?

### 7. 세 스레드가 같은 이름의 변수를 고치면 (예측) ★★

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

- 세 스레드의 `tls` 는 각각 얼마인가? **메인**은?
- ★★★ `&tls` 가 셋 다 **같은가 다른가**? `&shared` 는?
- ★★ **값만 보고** 「객체가 넷인지 하나인지」를 가를 수 있는가?
- ★ 메인의 `&tls` 도 스레드들과 다른가? 그러면 객체가 **몇 개**인가?
- ★★ 이 실험에서 **일부러 안 한 것**은 무엇인가? 왜인가?
- ★ 컴파일에 무엇이 더 필요한가?

### 8. `thread_local` 이라는 철자 (경계) ★★

```c
/* s28g.c */
#include <stdio.h>
thread_local int a = 1;             /* C23 키워드 */
int main(void) { printf("thread_local a = %d\n", a); return 0; }
```

```c
/* s28g2.c */
#include <stdio.h>
#include <threads.h>
thread_local int a = 1;             /* <threads.h> 가 매크로로 준다 */
int main(void) { printf("thread_local a = %d\n", a); return 0; }
```

- `gcc -std=c17` 으로 앞 파일을 던지면 무슨 일이 나는가? `cc exit` 는?
- `gcc -std=c2x` 으로 던지면?
- ★★ 뒤 파일(`<threads.h>` 를 넣은 것)을 `-std=c17` 으로 던지면?
- ★★★ 그래서 `thread_local` 은 **어느 층**에 속하는가? **C11 과 C23 에서 무엇이 다른가**?
- ★★ 에러 메시지만 보고 「이 컴파일러는 지원 안 한다」로 읽으면 **무엇이 틀리는가**?
- ★ 이식성을 생각하면 **어느 철자**를 쓰는 것이 나은가?

### 9. 다른 문법들은 어느 저장 기간인가 (연결) ★★

- **문자열 리터럴** · **복합 리터럴**(함수 안 / 파일 스코프) · **VLA** 는 각각 어느 저장 기간인가?
- ★★ 그중 **새 저장 기간을 만드는 것**이 있는가?
- ★★ **opaque struct 의 객체**와 **유연 배열 멤버 구조체**는 사실상 어느 저장 기간에 놓이는가? **왜인가**?
- ★ 그 둘은 「고른 것」인가 「떠밀린 것」인가?
- ★★ `(static struct P){1,2}` 는 어느 저장 기간이고 **어느 버전부터**인가?

### 10. 이 값을 어디에 둘까 (왜) ★★★

- ★★★ 네 가지를 고를 때 **먼저 묻는 질문**은 무엇인가?
- ★★ 그다음에 묻는 질문은?
- ★ 함수 밖으로 돌려줄 값은 어디에 두는가? 두 가지 형태를 대면?
- ★★ 큰 버퍼를 자동이 아니라 할당에 두는 이유를 **두 가지** 대면?
- ★★ 함수 안 `static` 의 대가는 무엇이고, 그 대가를 피하는 방법은?
- ★ 「이름은 하나인데 객체는 여럿」이 필요한 자리는?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **비어 있는 칸이 있는가**? ★ 이 주제가 **다른 편들과 다른 점**이 하나 있다 — 무엇인가?
- ★★ **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★★ **진단이 0건인 자리**는 어디인가? 그것이 왜 특히 나쁜가?
- ★★ 이 주제의 **네 번째 창**은 무엇이고, 세 창이 못 하는 것이 무엇인가?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **스택 프레임·가상 메모리·힙의 구조**는 어느 주제가 정본인가?
- **`static` 이 링크를 바꾸는 것**과 **무엇이 0 이 되는가**는 각각 어느 주제인가?
- **`malloc`/`free` 의 계약**과 **댕글링이 왜 최악인가**는 각각 어느 주제인가?
- ★ **문자열 리터럴** · **VLA** · **복합 리터럴**은 각각 어느 형제가 정본인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★★ **C++ 에서 갈라지는 자리** 두 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
