# c/syntax/03 — 정수 승격과 통상 산술 변환: 말없이 일어나는 변환 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력·경고를 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra`.\
> 최적화 수준이 답에 영향을 주는 문항은 **문항 안에 어느 수준으로 돌리는지 적었다.**
> ★ **이 주제의 답은 세 겹이다.**\
> ① 무엇이 출력되나 ② **어느 최적화 수준에서도 같은가** ③ 어느 층인가(표준 / 구현 정의 / 미명시 / UB).\
> ①만 답하면 이 주제를 배운 게 아니다. **「`-O0` 에서 이랬다」는 아무것도 증명하지 않는다.**
> 선행 — [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `-1 < 1u` (예측) ★ 이 주제의 정점

```c
int i = -1;
unsigned u = 1u;
printf("%d %d %u\n", -1 < 1u, -1 < 1, (unsigned)i);
```

- 세 값은 각각 무엇인가?
- `-1 < 1u` 가 그 값인 이유를 비트 그림으로 설명할 수 있는가?
- 이 코드에 경고가 나는가 — 난다면 어느 플래그가 잡는가?
- 그 플래그는 `-Wall` 에 들어 있는가?

### 2. `sizeof` 가 낀 비교 (예측)

```c
int a[10];
int k = -1;
printf("%d %d\n", k < sizeof(a)/sizeof(a[0]),
                  k < (int)(sizeof(a)/sizeof(a[0])));

/* 그리고 이 루프 */
int b[5] = {10,20,30,40,50};
int sum = 0;
for (size_t i = sizeof(b)/sizeof(b[0]) - 1; i >= 0; i--) sum += b[i];
printf("sum = %d\n", sum);
```

- 첫 `printf` 의 두 값은 각각 무엇인가?
- 아래 루프는 언제 끝나는가 — 끝나기는 하는가?
- 이 루프에 `-Wall -Wextra` 가 무슨 경고를 주는가?
- ASan 으로 돌리면 무엇이 나오는가?
- 어떻게 고치는가?

### 3. 좁은 타입끼리의 곱셈 (예측)

```c
unsigned char c = 200;
signed char sc = -100;
unsigned short us = 65535;
printf("%d %d %d %d\n", c * c, (unsigned char)(c * c), sc * 2, us * us);
```

- 네 값은 각각 무엇인가?
- `c * c` 가 그 값인 이유는? (`unsigned char` 의 최댓값은 255 인데)
- `us * us` 만 이상한 값인 이유는?
- 넷 중 **UB 인 것**은 어느 것이고, 무엇으로 확인하는가?

### 4. 통상 산술 변환 — 결과 타입 (예측)

다음 식들의 **결과 타입**을 답하라(이 환경: `int` 4바이트, `long` 8바이트).

```c
int i; unsigned u; long l; unsigned long ul; long long ll;
char c; short s; unsigned short us; float f; double d;

i + u        i + l        u + l        u + ul       l + ul
l + u        ll + ul      i + f        f + d        ul + d
c + c        s + us       +c           +us
```

- 열네 개의 타입을 각각 답하라.
- `u + l` 이 `long` 인데 `l + ul` 은 `unsigned long` 이다 — 규칙 차이를 한 문장으로.
- `ll + ul` 이 **어느 쪽도 아닌 타입**이 되는 이유는?
- `+c` 와 `+us` 가 같은 타입인 것은 이 환경에서만 그런가?

### 5. `INT_MAX + 1` — 세 도구로 (예측) ★★

```c
/* (A) 단순 덧셈 */
int add_one(int x) { return x + 1; }
int x = INT_MAX;
printf("%d\n", add_one(x));

/* (B) 루프 조건 */
int n = 0;
for (int i = INT_MAX - 2; i > 0; i++) n++;
printf("n = %d\n", n);
```

- (A)를 `-O0`·`-O2`·`-fsanitize=undefined` 로 돌리면 각각 무엇이 나오는가 — **셋이 다른가?**
- (B)를 같은 셋으로 돌리면 각각 무엇이 나오는가 — **셋이 다른가?**
- (B)에서 `-O1` 이상은 컴파일 시간에 무엇을 말해 주는가?
- (A)와 (B)의 답이 갈린 것에서 무엇을 배우는가?

### 6. 시프트 (예측)

```c
int over31(int v, int s) { return v << s; }   /* over31(1, 31) */
int cnt32 (int v, int s) { return v << s; }   /* cnt32 (1, 32) */
int cntneg(int v, int s) { return v << s; }   /* cntneg(1, -1) */
printf("%d %d %d\n", over31(1,31), cnt32(1,32), cntneg(1,-1));
```

- `-O0` 에서 세 값은? `-O2` 에서는?
- UBSan 은 몇 건을 잡고, 각각 뭐라고 말하는가?
- 세 함수를 하나로 합치면 UBSan 의 보고가 달라지는가 — 왜?
- `1 << 32` 를 **상수로** 쓰면 컴파일 시간에 무엇이 나오는가?

### 7. 부호 없는 정수는 UB 인가 (경계)

```c
unsigned n = 0;
for (unsigned i = UINT_MAX - 2; i > 0; i++) n++;
printf("%u %u %u\n", n, UINT_MAX + 1u, 0u - 1u);
```

- `-O0`·`-O2`·UBSan 세 결과가 다른가?
- 세 값은 각각 무엇인가?
- 이것은 어느 층인가 — 그리고 5번의 (B)와 무엇이 다른가?
- 「부호 없는 쪽이 안전하다」는 결론이 맞는가?

### 8. `-fwrapv` 는 무엇을 바꾸나 (경계)

- `-O2 -fwrapv` 로 5번의 (B)를 돌리면 무엇이 나오는가?
- 이 플래그는 **하드웨어 동작**을 바꾸는가, **언어 규칙**을 바꾸는가?
- 그 차이가 왜 결정적인가 — 최적화기가 무엇을 못 하게 되는가?
- 대가는 무엇인가?

### 9. 경고로 잡히는 것 / 안 잡히는 것 (연결)

여섯 함정을 놓고 도구를 하나씩 켠다.

```c
int f1(int a, int b)             { return a + b; }   /* INT_MAX + 1 */
int f2(int v, int s)             { return v << s; }  /* 1 << 40 */
unsigned char f3(unsigned char c){ return c * c; }   /* c = 200 */
int f4(int i, unsigned u)        { return i < u; }   /* -1 < 1u */
int f5(double d)                 { return (int)d; }  /* 1e10 */
int f6(int *p)                   { return p[5]; }    /* int[3] */
```

- `-Wall -Wextra` 는 몇 건을 잡는가?
- `-Wconversion -Wsign-conversion` 을 더하면 몇 건이 되는가?
- `-O2` 로 올리면 **새로 나오는 경고**가 있는가 — 왜?
- `f3` 이 `-Wconversion` 으로도 안 잡히는 이유는 무엇인가?
- UBSan 기본 집합이 `f5` 를 안 잡는 이유는?
- 아무 도구도 안 켜고 `-O0` 과 `-O2` 로 돌리면 여섯 값 중 몇 개가 달라지는가 — 그리고 종료 코드는?

### 10. 왜 부호 있는 것만 UB 인가 (왜)

- 부호 없는 오버플로는 정의되어 있는데 부호 있는 것은 왜 UB 인가?
- C23 에서 부호 표현이 2의 보수로 못박혔는데도 여전히 UB 인 이유는?
- UB 로 두면 컴파일러가 무엇을 할 수 있게 되는가 — 구체적인 최적화 하나를 들 수 있는가?
- 부호 있는 오버플로를 「일으킨 뒤에 검사」할 수 없는 이유는?

### 11. 그래서 어떻게 쓰나 (연결)

- 인덱스와 길이를 비교하는 올바른 형태 두 가지는?
- 역방향 루프의 안전한 형태는?
- `if (i < len - 1)` 을 고치는 형태는?
- 이 주제의 결론을 **빌드 플래그 한 줄**로 쓰면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
