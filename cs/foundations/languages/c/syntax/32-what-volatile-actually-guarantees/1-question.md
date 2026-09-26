# c/syntax/32 — `volatile` 이 실제로 보장하는 것: 「**매번 가서 본다 — 그것뿐이다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux(논리 CPU 여럿) · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`volatile` 이 막는 것**(접근 제거·합치기 — 어셈블리) ② **못 막는 것**(원자성 · 컴파일러 순서 · CPU 순서 — 실행해서 센 수)
> ③ **정당한 자리 셋**(장치 레지스터 · `setjmp` · 시그널).
> ★★★ **본체 창은 `-O2` 어셈블리** — 1번은 **로드·스토어 수**까지 적어야 답이다.
> ★★★ **3·5번의 수는 흔들린다** — **「잃었나」·「있나」만** 답으로 적어라. 숫자를 맞히는 문항이 아니다.
> ★ **시간은 묻지 않는다** — 이 편은 재지 않았다.
> 선행 — [31번 형제](../31-const-and-pointer-const-placement/).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **2·6번은 판 격자**다 — 한 칸으로 답하지 마라.
- ★★ **4·5번은 「어셈블리로 보이나 안 보이나」부터** 답해라 — 안 보이면 **무슨 창으로** 바꿔 물었나.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 값을 바꾸는 것은 누구인가 — 장치 · 핸들러 · `longjmp` · 다른 스레드**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 함수를 `volatile` 있이/없이 — `-O2` 어셈블리 (예측) ★★★ 이 주제의 축

```c
/* s32a.c */
int          plain_flag;
volatile int vol_flag;

void wait_plain(void)   { while (!plain_flag) { } }
void wait_vol(void)     { while (!vol_flag) { } }

int  read3_plain(void)  { return plain_flag + plain_flag + plain_flag; }
int  read3_vol(void)    { return vol_flag + vol_flag + vol_flag; }

void write2_plain(void) { plain_flag = 1; plain_flag = 2; }
void write2_vol(void)   { vol_flag = 1; vol_flag = 2; }
```

- ★★★ `wait_plain` 을 **gcc `-O2`** 와 **clang `-O2`** 는 각각 **무엇으로** 번역하는가?
- ★★★ `wait_vol` 은? 로드가 **루프 안에** 있는가?
- ★★ `read3_*` 의 **로드 수**와 `write2_*` 의 **스토어 수**는 각각?
- ★★ `-O0` 에서 `volatile` 없는 쪽은 어떻게 되는가? ★ **두 컴파일러가 갈리는 칸**이 있는가?
- ★ clang 이 `wait_plain` 을 통째로 지운 것은 **무슨 규칙** 덕인가? `volatile` 이 그것을 왜 막는가?

### 2. 시그널 핸들러의 깃발 — 파일 셋 × 네 벌 (예측) ★★★

```c
/* s32b.c */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static int got;                          /* ★ volatile 이 없다 */

static void on_alarm(int sig) { (void)sig; got = 1; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGALRM, on_alarm);
    alarm(1);                            /* 1초 뒤 핸들러가 got = 1 */
    printf("기다린다\n");
    while (!got) { }
    printf("깼다 · got = %d\n", (int)got);
    return 0;
}
```

`s32b2.c` 는 **마지막 `printf` 가 `"깼다\n"` 뿐**(루프 뒤에 `got` 을 다시 안 읽는다)이라는 것만 다르고, `s32c.c` 는 **`static volatile sig_atomic_t got;`** 이라는 것만 다르다.

- ★★★ **열두 칸**(파일 3 × gcc·clang × `-O0`/`-O2`)의 **`run exit`** 와 출력은? (`timeout 3` 으로 돌렸다)
- ★★★ **「기다리지 않고 깨는」 칸**이 있는가? 왜 그렇게 되는가?
- ★★ `s32b` 와 `s32b2` 의 **한 줄 차이**가 결과를 어떻게 바꾸는가?
- ★★ 표준이 핸들러에게 **허락한 형태**는 무엇이고, 나머지는 **어느 층**인가?

### 3. 두 스레드가 `volatile int` 에 `++` 를 천만 번씩 (예측) ★★★

```c
/* s32d.c */
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>

#define N 10000000

static volatile int v_counter;           /* ★ volatile */
static _Atomic int  a_counter;           /* ★ _Atomic */
static atomic_int   go;                  /* 두 스레드를 같이 출발시키는 깃발 */

static void *work_v(void *arg) { (void)arg; while (!go) { } for (int i = 0; i < N; i++) v_counter++; return NULL; }
static void *work_a(void *arg) { (void)arg; while (!go) { } for (int i = 0; i < N; i++) a_counter++; return NULL; }

static int run(void *(*fn)(void *)) {
    pthread_t t1, t2;
    go = 0;
    pthread_create(&t1, NULL, fn, NULL);
    pthread_create(&t2, NULL, fn, NULL);
    go = 1;
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}

int main(void) {
    run(work_v);
    int lost_v = 2 * N - v_counter;
    printf("volatile int : 잃었나 = %s · 잃은 수 : %d\n", lost_v > 0 ? "예" : "아니오", lost_v);
    run(work_a);
    int lost_a = 2 * N - a_counter;
    printf("_Atomic int  : 잃었나 = %s · 잃은 수 : %d\n", lost_a > 0 ? "예" : "아니오", lost_a);
    return 0;
}
```

- ★★★ 두 컴파일러에서 **「잃었나」** 는? `_Atomic` 은?
- ★★★ **같은 바이너리를 10 번** 돌리면 「잃었나」는 몇 대 몇인가?
- ★★ **잃은 수**를 답으로 적어도 되는가?
- ★★★ `inc_vol` 을 **clang `-O2`** 는 명령 몇 개로 번역하는가? 그런데도 잃는 이유는?
- ★★ `inc_atomic` 은 무엇이 **한 글자** 다른가?

### 4. `volatile` 깃발로 데이터를 넘기면 — 어셈블리 (예측) ★★

```c
/* s32f.c */
int          data;
volatile int ready;

void publish(void) {
    data = 1;                            /* ① */
    ready = 1;                           /* ★ volatile 쓰기 */
    data = 2;                            /* ② */
}

int consume(void) {
    int a = data;                        /* ① */
    int r = ready;                       /* ★ volatile 읽기 */
    int b = data;                        /* ② */
    return a + r + b;
}
```

- ★★★ `publish` 의 **`data = 1`** 은 `-O2` 어셈블리에 **남는가**?
- ★★★ `consume` 의 **두 `data` 읽기**는 몇 개가 되는가? `ready` 읽기의 **앞인가 뒤인가** — 두 컴파일러가 같은가?
- ★★ 이것이 `volatile` 에 대해 **무엇을 증명**하는가?

### 5. 쓰고 나서 남의 것을 읽기 — 20만 판 (예측) ★★★

```c
/* s32g2.c */
volatile int vx, vy;
_Atomic int  ax, ay;

int body_vol(void)    { vx = 1; return vy; }   /* 쓰고 나서 남의 것을 읽는다 */
int body_atomic(void) { ax = 1; return ay; }
```

```c
/* s32g.c */
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>

#define TRIALS 200000

static volatile int vx, vy, vr1, vr2;    /* ★ volatile 판 */
static atomic_int   ax, ay;              /* ★ _Atomic 판 (기본 순서 = seq_cst) */
static int          ar1, ar2;
static atomic_int   turn1, turn2, done1, done2;
static int          use_atomic;

static void *t1(void *arg) {
    (void)arg;
    for (int t = 1; t <= TRIALS; t++) {
        while (atomic_load(&turn1) != t) { }
        if (use_atomic) { atomic_store(&ax, 1); ar1 = atomic_load(&ay); }
        else            { vx = 1; vr1 = vy; }            /* 쓰고 나서 남의 것을 읽는다 */
        atomic_store(&done1, t);
    }
    return NULL;
}

static void *t2(void *arg) {
    (void)arg;
    for (int t = 1; t <= TRIALS; t++) {
        while (atomic_load(&turn2) != t) { }
        if (use_atomic) { atomic_store(&ay, 1); ar2 = atomic_load(&ax); }
        else            { vy = 1; vr2 = vx; }
        atomic_store(&done2, t);
    }
    return NULL;
}

static int both_zero(int atomic_mode) {
    pthread_t a, b;
    int count = 0;
    use_atomic = atomic_mode;
    atomic_store(&turn1, 0); atomic_store(&turn2, 0);
    atomic_store(&done1, 0); atomic_store(&done2, 0);
    pthread_create(&a, NULL, t1, NULL);
    pthread_create(&b, NULL, t2, NULL);
    for (int t = 1; t <= TRIALS; t++) {
        vx = vy = 0; atomic_store(&ax, 0); atomic_store(&ay, 0);
        atomic_store(&turn1, t); atomic_store(&turn2, t);
        while (atomic_load(&done1) != t || atomic_load(&done2) != t) { }
        if (atomic_mode ? (ar1 == 0 && ar2 == 0) : (vr1 == 0 && vr2 == 0)) count++;
    }
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    return count;
}

int main(void) {
    int v = both_zero(0);
    printf("volatile : 두 스레드가 둘 다 0 을 읽은 판이 있나 = %s · 판 수 : %d / %d\n",
           v > 0 ? "있다" : "없다", v, TRIALS);
    int a = both_zero(1);
    printf("_Atomic  : 두 스레드가 둘 다 0 을 읽은 판이 있나 = %s · 판 수 : %d / %d\n",
           a > 0 ? "있다" : "없다", a, TRIALS);
    return 0;
}
```

- ★★ `body_vol` 의 어셈블리는 **소스 순서대로**인가? `body_atomic` 에는 무엇이 붙는가?
- ★★★ `volatile` 판에서 **「둘 다 0 을 읽은 판」이 있는가**? `_Atomic` 판은?
- ★★★ 어셈블리가 순서대로인데 둘 다 0 이 나온다면 **무엇이** 순서를 바꿨는가?
- ★★ `_Atomic` 의 `0 / 200000` 은 「**불가능**」의 증명인가? 무엇이 그것을 보장하는가?
- ★ 이 문항이 **제5의 상태**인 이유는?

### 6. `setjmp`/`longjmp` 뒤의 지역 변수 — 두 컴파일러 × 세 판 (예측) ★★

```c
/* s32h.c */
#include <setjmp.h>
#include <stdio.h>

static jmp_buf jb;

static void jump(void) { longjmp(jb, 1); }

int main(void) {
    int          plain = 1;
    volatile int vol   = 1;
    if (setjmp(jb) == 0) {
        plain = 2;                       /* ★ setjmp 뒤에 바꾼 지역 변수 */
        vol   = 2;
        jump();
    }
    printf("longjmp 뒤 : plain = %d · vol = %d\n", plain, vol);
    return 0;
}
```

- ★★★ 여섯 칸의 **`plain` 과 `vol`** 은?
- ★★ 경고는 몇 건인가? **`-Wclobbered` 를 따로 켜면**?
- ★★ 표준은 `plain` 의 값을 **무엇이라** 하는가?

### 7. 장치 레지스터 — 실행 못 하는 자리 (왜) ★★

```c
/* s32i.c */
#include <stdint.h>

#define REG_PLAIN (*(uint32_t *)0x40001000u)            /* 장치 레지스터라고 치자 */
#define REG_VOL   (*(volatile uint32_t *)0x40001000u)

void kick_plain(void) { REG_PLAIN = 1; REG_PLAIN = 1; }  /* 같은 값을 두 번 쓴다 */
void kick_vol(void)   { REG_VOL = 1; REG_VOL = 1; }
```

- ★★ `kick_plain` 과 `kick_vol` 의 **스토어 수**는?
- ★★ 장치 입장에서 그 차이는 **무엇**인가?
- ★ 이 소스를 **실행하지 않은 이유**는? 그것은 「안 쟀다」인가 「못 쟀다」인가?
- ★ `(uint32_t *)0x40001000u` 는 **어느 층**인가?

### 8. TSan 은 `volatile` 을 무엇으로 보나 (경계) ★★★

```c
/* s32j.c */
#include <pthread.h>
#include <stdio.h>

static volatile int counter;             /* ★ volatile 만 붙였다 */

static void *work(void *arg) {
    (void)arg;
    for (int i = 0; i < 1000; i++) counter++;
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, work, NULL);
    pthread_create(&t2, NULL, work, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    fprintf(stderr, "끝 — counter 를 찍지 않는다(값은 흔들린다)\n");
    return 0;
}
```

- ★★★ TSan 은 `volatile int` 의 `++` 를 **무엇으로** 보고하는가? `exit` 는?
- ★★ `_Atomic`(`s32k.c`)은?
- ★★★ **gcc 의 TSan 을 그대로 돌리면** 무슨 일이 나는가? 어떻게 풀었나?
- ★★ 그 경험이 「**도구가 없다**」고 적기 전에 무엇을 하라고 말하는가?
- ★ TSan 의 판정은 **표준의 어느 규칙**과 같은 말인가?

### 9. `volatile` 의 정당한 자리 셋 (연결) ★★

- ★★★ 셋을 대면? 각각 「**누가 값을 바꾸나**」는?
- ★★ **다른 스레드**는 왜 그 목록에 없는가?
- ★ 스레드 사이의 값은 **무엇**으로 두는가? 그것이 **선택 기능**이라는 것은 무슨 뜻인가?

### 10. Java 의 `volatile` 과 이름만 같다 (연결) ★★

- ★★★ Java 의 `volatile` 이 보장하고 C 의 `volatile` 이 보장하지 **않는** 것은?
- ★★ 둘 다 **보장하지 않는** 것은?
- ★ C 에서 Java `volatile` 에 가장 가까운 것은?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ **「`volatile` 접근이 무엇인가」** 는 어느 층인가? 표준은 그 자리를 **어떻게** 처리했나?
- ★★ **조건부 표준 칸**에 드는 것은?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★ 이 편에 「**종료 코드 0인데 ill-formed**」 새 항목이 있는가? 없다면 **대신 무엇이** 있는가?
- ★ **시간 측정 창**을 쓰지 않은 이유는?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- **동시성 개념 자체**(경쟁·가시성·락)는 어느 주제가 정본인가?
- **불확정 표현**과 **`const`** 는 각각 어느 형제가 정본인가?
- **TSan 사용법**은 목록의 몇 번 주제인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
