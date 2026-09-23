# c/syntax/08 — `sizeof`·정렬·`offsetof`: 구조체에 난 구멍을 눈으로 본다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> ★ **수치를 손으로 계산하지 말고 「무엇으로 재는가」까지 답하라.**
> 이 주제의 절반은 `offsetof`·`_Alignof`·`_Static_assert` 라는 **재는 도구**에 대한 것이다.
> **환경** — gcc 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra`.\
> 최적화 수준이나 `-pedantic`·`-fshort-enums` 가 답을 바꾸는 문항은 **문항 안에 적었다.**
> 선행 — [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `sizeof` 의 세 얼굴 (예측)

```c
int a[10]; int i = 5; char *s = "hello";
printf("%zu\n", sizeof(int));
printf("%zu\n", sizeof i);
printf("%zu\n", sizeof i + 1);
printf("%zu\n", sizeof a);
printf("%zu\n", sizeof s);
printf("%zu\n", sizeof "hello");
```

- 여섯 줄은 각각 무엇을 찍는가?
- 셋째 줄이 헷갈리는 이유는 무엇인가 — 어떻게 묶이는가?
- `sizeof s` 와 `sizeof "hello"` 가 다른 이유는?
- `sizeof` 의 결과 타입은 무엇이고 그것이 왜 사고가 되는가?

### 2. 피연산자가 평가되나 (예측)

```c
static int side = 0;
static int boom(void) { side = 1; printf("boom 이 불렸다\n"); return 7; }
int j = 0;
printf("%zu\n", sizeof(boom()));
printf("%d\n", side);
printf("%zu, %d\n", sizeof(j++), j);
```

- 무엇이 찍히는가 — `boom 이 불렸다` 가 나오는가?
- `side` 와 `j` 는 각각 무엇인가?
- 이 규칙에 **예외가 하나** 있다 — 무엇이고 어떻게 확인하는가?
- 그 예외에서 `sizeof` 는 무엇을 기억하는가?

### 3. 멤버 순서만 바꾸면 (예측) ★★★ 이 주제의 본체

```c
struct Bad  { char a; int b; char c; double d; };
struct Good { double d; int b; char a; char c; };
```

- 두 `sizeof` 는 각각 무엇인가 — 멤버 크기의 합은 얼마인가?
- 두 `_Alignof` 는?
- `offsetof` 로 잰 네 멤버의 자리는 각각 어디인가 — **구멍은 어디에 몇 바이트씩 있나?**
- 그 지도가 맞는지 **`offsetof` 말고 다른 방법으로** 확인하려면 어떻게 하는가?
- 구조체 크기를 정하는 규칙 셋을 쓰면?

### 4. `#pragma pack` 의 대가 (예측) ★★

```c
#pragma pack(push, 1)
struct Packed { char a; int b; char c; double d; };
#pragma pack(pop)
static struct Packed p;
int *q = &p.b;
*q = 0x41424344;
```

- `sizeof(struct Packed)` 와 `_Alignof(struct Packed)` 는?
- `&p.b` 가 4의 배수인가?
- `-fsanitize=undefined` 로 돌리면 몇 줄이 나오는가?
- `-Wall -Wextra` 는 몇 건을 말하는가?
- 같은 구조체를 `__attribute__((packed))` 로 선언하면 경고가 달라지는가 — **배치는 같은가?**

### 5. 유연 배열 멤버 (예측)

```c
struct Buf { int n; int a[]; };
printf("%zu %zu\n", sizeof(struct Buf), offsetof(struct Buf, a));
struct Buf *b = malloc(sizeof *b + 5 * sizeof b->a[0]);
```

- 두 값은 각각 무엇인가 — `a[]` 가 세어지는가?
- `malloc` 에 넘긴 크기는 얼마인가?
- ASan 으로 돌리면 통과하는가?
- 이 구조가 「포인터 멤버 + 별도 할당」보다 나은 점은?

### 6. 빈 구조체 (예측)

```c
struct Empty { };
printf("%zu\n", sizeof(struct Empty));
```

- gcc 기본 빌드에서 무엇이 찍히는가 — 컴파일은 되는가?
- `-pedantic` 과 `-pedantic-errors` 는 각각 무엇을 하는가?
- **같은 소스를 C++ 로 컴파일하면** 무엇이 찍히는가?
- 이 차이가 실무에서 문제가 되는 자리는?

### 7. 구조체 정렬은 어떻게 정해지나 (왜)

여섯 구조체(`{char}` · `{char,short}` · `{char,int}` · `{char,double}` · `{double,char}` · `{char,char,char}`)의
`sizeof` 와 `_Alignof` 를 잰다.

- `_Alignof(struct)` 를 정하는 규칙은 무엇인가?
- `sizeof % _Alignof` 는 여섯 개 모두 얼마인가 — 왜 그래야 하는가?
- `struct { double a; char b; }` 가 9가 아니라 16인 이유는?
- 구조체 배열의 크기가 `sizeof` 의 정확히 n배인 것과 이 규칙은 어떤 관계인가?

### 8. `_Alignof`·`_Alignas`·`alignof` (경계)

- `_Alignof` 로 `char`·`int`·`double`·`long double`·`void *` 를 재면 각각 얼마인가?
- `_Alignas(1) int x;` 는 되는가 — 진단 문구는?
- `malloc` 이 돌려주는 주소는 어떤 정렬을 보장하는가 — 무엇으로 확인하는가?
- `alignof`·`alignas` 철자를 **헤더 없이** 쓰려면 어느 표준이 필요한가 — `-std=c17` 에서는?

### 9. `_Static_assert` 로 못 박기 (경계)

- `sizeof`·`offsetof`·`_Alignof` 를 `_Static_assert` 에 쓸 수 있는가 — 왜인가?
- 단언이 거짓이면 무엇이 일어나는가?
- 런타임 `assert` 와 무엇이 다른가 — 세 가지를 들면?
- 단언 메시지를 쓸 때 실무적으로 주의할 것 하나는?

### 10. `memcmp` 로 구조체를 비교하면 (왜)

```c
struct T { char a; int b; };
struct T x, y;
memset(&x, 0x00, sizeof x); memset(&y, 0xFF, sizeof y);
x.a = 1; x.b = 2;  y.a = 1; y.b = 2;
printf("%d\n", memcmp(&x, &y, sizeof x));
```

- 멤버 값이 전부 같은데 `memcmp` 는 무엇을 돌려주는가?
- 왜 그런가 — 패딩 바이트의 값은 어느 층인가?
- 경고나 sanitizer 가 이것을 잡아 주는가?
- 그러면 `y = x;` 로 대입한 뒤에는 어떻게 되는가 — 그 결과를 보장으로 읽어도 되는가?

### 11. `offsetof` 의 경계 (경계)

- gcc 에서 `offsetof` 는 무엇으로 정의되어 있는가 — `gcc -E -dM` 으로 확인하면?
- 옛날 관용구 `((size_t)&(((T *)0)->M))` 는 같은 답을 주는가?
- 그 관용구를 sanitizer 로 돌리면 — gcc 와 clang 이 같은가?
- 비트필드 멤버에 `offsetof` 를 쓰면?

### 12. 그래서 무엇을 하나 (연결)

- 구조체 크기를 줄이는 **공짜 방법**과 **대가가 있는 방법**은 각각 무엇인가?
- 배치에 의존하는 코드를 쓸 때 반드시 같이 쓸 것은?
- 파일 형식·네트워크 패킷을 다루는 이식 가능한 형태는?
- 이 주제의 다섯 층 중 **도구가 원리상 못 잡는** 층은 어디이고, 거기 해당하는 것은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
