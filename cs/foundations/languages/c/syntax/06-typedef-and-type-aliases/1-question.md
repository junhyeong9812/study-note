# c/syntax/06 — `typedef` 와 타입 별칭: 새 타입이 아니라 별명이다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **단 이 주제의 「출력」은 대개 컴파일 에러다.** `typedef` 는 기계어에 흔적을 안 남긴다.
> 「에러가 났나」가 아니라 「**어느 줄에서 났나**」를 맞히는 것이 답이다.
> **환경** — gcc 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra`.\
> 표준 버전이 답을 바꾸는 문항은 **문항 안에 적었다.**
> 선행 — [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `_Generic` 에 둘을 같이 올리면 (예측) ★

```c
typedef int MyInt;
MyInt a = 1;
printf("%s\n", _Generic(a, int: "int 로 잡혔다", MyInt: "MyInt 로 잡혔다"));
```

- 무엇이 찍히는가?
- 이것이 이 주제의 결론을 어떻게 증명하는가?
- 같은 함수를 `int f(int);` · `MyInt f(MyInt);` 두 줄로 선언하면 어떻게 되는가?
- **실행 출력이 아니라 무엇이 근거인가?**

### 2. `typedef char *String;` 뒤의 `const` (예측) ★★★ 이 주제 최고의 함정

```c
typedef char *String;
char buf[] = "hello";
const String s = buf;
s[0] = 'H';                /* (a) */
s = buf;                   /* (b) */
```

- (a)와 (b) 중 **어느 줄에서 에러가 나는가?**
- 그렇다면 `const String` 은 무슨 타입인가 — `const char *` 인가?
- `_Generic(&s, ...)` 으로 물어보면 무엇이라고 답하는가?
- 진짜 `const char *s` 로 썼다면 에러가 어느 줄로 옮겨 가는가?

### 3. 같은 것을 `#define` 으로 하면 (예측) ★★

```c
#define String char *
const String s = buf;
s[0] = 'H';                /* (a) */
s = buf;                   /* (b) */
```

- 이번에는 **어느 줄에서 에러가 나는가?**
- 2번과 결과가 같은가 다른가 — 다르다면 왜인가?
- `String a, b;` 와 `char *c, d;` 는 각각 `sizeof` 가 어떻게 되는가?
- 두 실험에서 `typedef` 가 이긴 자리와 진 자리는 각각 어디인가?

### 4. 태그와 별칭이 다른 것을 가리키면 (예측)

```c
struct A { int x; };
typedef struct { double y; } A;      /* ★ 같은 글자 A */
struct A sa = {7};
A        ta = {2.5};
printf("%zu %zu\n", sizeof sa, sizeof ta);
sa = ta;                              /* (c) */
```

- 이 선언들이 **컴파일은 되는가?**
- 두 `sizeof` 는 무엇인가?
- (c)는 어떻게 되는가 — 진단 문구는?
- 이 함정을 없애는 관례는 무엇인가?

### 5. 배열 별칭을 파라미터에 (예측)

```c
typedef int Row[4];
static void take(Row r) { printf("%zu\n", sizeof r); }
Row x = {1,2,3,4};
printf("%zu\n", sizeof x);
take(x);
```

- 두 `sizeof` 는 각각 무엇인가?
- 함수 안에서 `r[0] = 99;` 를 하면 호출자의 `x` 가 바뀌는가?
- gcc 가 무엇이라고 경고하는가 — 어느 플래그인가?
- 별칭이 **감쇠를 막아 주는가?**

### 6. 불투명 타입 (예측)

```c
typedef struct S S;        /* struct S 의 정의는 아직 없다 */
S *make(void);
int get(S *);
```

- 이 세 줄만으로 **헤더가 성립하는가?**
- 같은 자리에서 `sizeof(S)` 를 쓰면 어떻게 되는가 — 진단 문구는?
- 그래서 이 타입은 **어떻게만 다룰 수 있는가?**
- 이 구조가 주는 이득 하나를 컴파일 관점에서 말하면?

### 7. 같은 함수를 세 이름으로 선언해도 되는 이유 (왜)

- `int f(int);` · `MyInt f(MyInt);` · `AlsoInt f(AlsoInt);` 가 왜 충돌하지 않는가?
- 만약 `typedef` 가 새 타입을 만든다면 무엇이 달라졌겠는가?
- `sizeof(MyInt)` 가 4인 것은 `MyInt` 의 성질인가 `int` 의 성질인가?
- 이 차이가 「어느 층인가」에 어떻게 반영되는가?

### 8. `typedef static int Bad;` (경계)

- 이 줄은 컴파일되는가 — 진단 문구는 무엇인가?
- 그 문구에서 `typedef` 의 **문법상 위치**에 대해 무엇을 알 수 있는가?
- `typedef` 가 저장 기간을 바꾸는가?
- 블록 안에서 `typedef` 이름과 같은 이름의 변수를 선언하면 어떻게 되는가 — 그 뒤 그 이름을 타입으로 쓰면?

### 9. 단위를 `typedef` 로 가르면 (왜)

- `typedef double Meters;` 와 `typedef double Feet;` 를 섞어 쓰면 경고가 몇 건인가?
- `-Wconversion` 을 켜면 달라지는가?
- 강제력을 얻으려면 무엇으로 바꿔야 하는가 — 그때 진단은?
- 그 대가는 무엇인가?

### 10. 함수 포인터 별칭이 값을 내는 자리 (왜)

- `typedef char *CharFn(int);` 와 `typedef CharFn *CharFnPtr;` 로 만든 `CharFnPtr ft[3]` 은
  손으로 쓴 어떤 선언과 같은가?
- 두 배열이 같은 타입이라는 것을 무엇으로 확인하는가?
- `typedef` 로 자를지 말지의 판단 기준을 한 줄로 쓰면?
- `qsort` 의 비교자를 별칭으로 두면 무엇이 좋아지는가?

### 11. 같은 `typedef` 를 두 번 (경계)

- `typedef int T;` 를 두 번 쓰면 어떻게 되는가?
- 표준 버전에 따라 갈리는가 — `-std=c89` 와 `-std=c17` 에서 각각?
- `-pedantic` 없이도 갈리는가?
- 이 규칙이 실무에서 쓸모 있는 자리는?

### 12. 그래서 언제 쓰고 언제 안 쓰나 (연결)

- `typedef` 로 **감추면 안 되는 것 셋**은 무엇인가?
- 표준 라이브러리가 `FILE *` 을 쓰고 `FILEP` 를 안 만드는 이유는?
- 「`typedef` 는 검사가 아니라 무엇인가」를 한 낱말로 쓰면?
- 이 주제의 결론을 한 문장으로 쓰면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
