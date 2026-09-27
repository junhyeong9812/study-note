# c/syntax/07 — `enum` 과 열거 상수: 이름이 붙은 정수일 뿐이다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra`.\
> 표준 버전이나 `-pedantic`·`-fshort-enums` 가 답을 바꾸는 문항은 **문항 안에 적었다.**
> ★ **이 주제에는 UB 가 없다.** 그래서 sanitizer 가 할 일이 없고,
> **「어느 플래그가 몇 건을 말하나」를 세는 것**이 유일한 검사다. 문항마다 그것을 묻는다.
> 선행 — [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 가지 타입을 물어본다 (예측) ★

```c
enum Small { S_A, S_B, S_C };
enum Neg   { N_A = -1, N_B = 0 };
enum Huge  { H_A = 2147483648u };
enum Tiny  { T_A = 0, T_B = 255 };
/* _Generic 으로 다음을 각각 물어본다 */
S_A · H_A · N_A                      /* 열거 상수 */
enum Small 변수 · enum Neg 변수 · enum Tiny 변수   /* 열거 타입 */
```

- 열거 상수 셋은 각각 무슨 타입인가?
- 열거 타입 변수 셋은 각각 무슨 타입인가?
- 상수와 변수의 답이 **다른 이유**는?
- 넷 중 하나만 답이 다르다 — 무엇이 그것을 가르는가?

### 2. `enum` 값에서 1을 빼면 (예측) ★★★ 이 주제의 위험지대

```c
enum Color { RED, GREEN, BLUE };
enum Color r = RED;
printf("%d\n", r - 1);
printf("%u\n", r - 1);
printf("%d\n", r - 1 < 0);
printf("%d\n", RED - 1 < 0);
```

- 네 줄은 각각 무엇을 찍는가?
- 셋째 줄과 넷째 줄이 **같은가 다른가** — 다르다면 무엇이 갈랐는가?
- `%d` 와 `%u` 중 **사실을 보여 주는 것**은 어느 쪽인가?
- 이것을 잡는 경고는 무엇이고 `-Wall` 인가 `-Wextra` 인가? clang 은 몇 건인가?
- 고치는 형태를 한 줄로 쓰면?

### 3. `sizeof(enum E)` 를 값 범위를 바꿔 가며 (예측)

위 1번의 네 `enum` 과 `enum Big { B_A = 2147483647 }` 의 `sizeof` 를 잰다.

- 다섯 값은 각각 무엇인가 — **값 범위에 따라 달라지는가?**
- `-fshort-enums` 를 붙이면 다섯 값이 어떻게 되는가?
- 이것은 어느 층인가?
- 그래서 `enum` 을 **어디에 쓰면 안 되는가?**

### 4. 범위 밖 값을 넣으면 (예측)

```c
enum Color { RED, GREEN, BLUE };
enum Color c = 999;
enum Color d = (enum Color)-5;
printf("%d %d\n", (int)c, (int)d);
```

- 컴파일되는가? 무엇이 찍히는가?
- `-Wall`·`-Wextra`·`-Wconversion`·`-pedantic` 을 각각 켜면 몇 건인가?
- `-O0`·`-O2`·`-fsanitize=undefined` 에서 답이 달라지는가 — 이것은 UB 인가?
- 이것을 잡아 주는 도구가 하나 있다 — 무엇이고 gcc 에 있는가?

### 5. `switch` 에서 열거자를 빠뜨리면 (예측)

```c
switch (c) {
case RED:   return "red";
case GREEN: return "green";
}
```

- 어떤 진단이 나오는가 — `-Wall` 인가 `-Wextra` 인가?
- `default:` 를 넣으면 그 진단이 어떻게 되는가?
- `default:` 가 있어도 말하게 하려면 무엇을 켜는가?
- 이 사실이 「`enum` 을 왜 쓰나」에 어떻게 답하는가?

### 6. C23 의 고정 기반 타입 (예측) ★★

```c
enum Byte : unsigned char { B_ZERO = 0, B_MAX = 255 };
printf("%ldL\n", (long)__STDC_VERSION__);
printf("%zu\n", sizeof(enum Byte));
/* 변수와 상수 B_MAX 의 타입을 _Generic 으로 물어본다 */
```

- `-std=c2x` 에서 세 줄은 각각 무엇을 찍는가?
- `B_MAX` 의 타입은 무엇인가 — **`int` 인가?**
- `-std=c17` 로 컴파일하면 **에러가 나는가?**
- `-std=c17 -pedantic` 은 무엇이라고 말하는가?
- `-std=c23` 이라는 옵션이 있는가?

### 7. 값 지정·이어붙기·중복 (왜)

```c
enum E { A, B = 10, C, D = 10, E_ = -1, F };
```

- 여섯 값은 각각 무엇인가?
- `C` 와 `F` 의 값이 정해지는 규칙을 한 줄로 쓰면?
- `B == D` 는 무엇인가 — 중복이 허용되는가?
- 이 선언에 경고가 몇 건 나오는가(`-pedantic` 까지 켜서)?

### 8. 비트 플래그로 쓰면 (경계)

```c
enum Perm { P_READ = 1, P_WRITE = 2, P_EXEC = 4 };
enum Perm both = P_READ | P_WRITE;
```

- `P_READ | P_WRITE` 의 타입은 무엇인가?
- `enum Perm` 변수에 넣을 때 경고가 나오는가?
- `both` 를 `switch` 의 `case` 로 받을 수 있는가 — 왜인가?
- 그래서 비트 플래그를 다루는 두 관례는 무엇인가?

### 9. 익명 `enum` 과 `#define` (경계)

```c
enum { BUFSZ = 256 };
#define DBUFSZ 256
```

- 둘 다 배열 크기·`case` 라벨·비트필드 폭으로 쓸 수 있는가?
- `gdb` 에서 `print` 해 보면 무엇이 다른가?
- 스코프가 어떻게 다른가?
- `#define` 만 되는 자리가 하나 있다 — 어디인가?

### 10. C17 과 C23 이 무엇이 다른가 (연결)

- 이 주제에서 C23 이 바꾼 것 **두 가지**는 무엇인가?
- gcc 가 그 변화를 **문구로 직접 말해 주는** 자리는 어디인가?
- `-std=c17` 이 C23 문법을 막아 주는가?
- 그렇다면 이식성을 확인하려면 무엇을 붙여야 하는가?

### 11. 그래서 언제 쓰나 (연결)

- `enum` 을 쓰는 값어치 **둘**을 말하면?
- 그 둘을 안 쓸 거면 `#define` 과 무엇이 다른가?
- 크기·부호가 중요한 자리(파일 형식·구조체 멤버)에서는 무엇을 쓰는가?
- 이 주제의 결론을 빌드 플래그 한 줄로 쓰면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
