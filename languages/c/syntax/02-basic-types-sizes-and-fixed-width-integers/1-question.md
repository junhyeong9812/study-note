# c/syntax/02 — 기본 타입·크기·고정폭 정수: 표준은 최소만 정한다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · x86-64 Linux(LP64) · 기본 `-std=c17 -Wall -Wextra`.\
> C23 확인은 `-std=c2x` 로 한다(gcc 13 에 `-std=c23` 이 없다).
> ★ **이 주제의 답은 두 겹이다.** 「값이 무엇인가」로 끝나면 절반이고,\
> 「**그 값을 누가 보장하나**」(표준 / 구현 정의 / 미명시 / UB)까지 답해야 맞는 것이다.
> 선행 — [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 환경의 실제 크기 (예측)

```c
printf("%zu %zu %zu %zu %zu\n",
       sizeof(char), sizeof(short), sizeof(int), sizeof(long), sizeof(long long));
printf("%zu %zu %zu %zu\n",
       sizeof(void *), sizeof(size_t), sizeof(ptrdiff_t), sizeof(long double));
printf("%d %d %d\n", CHAR_BIT, INT_MAX, CHAR_MIN);
```

- 열두 개 값은 각각 무엇인가?
- 이 중 **어느 환경에서도 같은 것**은 몇 개이고 무엇인가?
- `long` 과 `long long` 이 같은 크기여도 되는가?

### 2. 표준이 보장하는 최소는 어디까지인가 (경계)

- `int` 가 담을 수 있다고 표준이 보장하는 범위는 무엇인가 — 32767 인가 65535 인가 2147483647 인가?
- `sizeof(char)` 가 1 이라는 것은 무엇의 결과인가?
- `CHAR_BIT` 이 8 이 아닐 수 있는가?
- 「`int` 는 4바이트」라는 가정을 **주석이 아니라 빌드 실패**로 바꾸려면 무엇을 쓰는가?

### 3. `(char)200` 은 무엇인가 (예측)

```c
char c = (char)200;
printf("%d %d %d\n", CHAR_MIN, c, (unsigned char)200);
```

- 이 환경에서 세 값은 무엇인가?
- 이 답은 표준이 정한 것인가, 구현 정의인가, 미명시인가, UB 인가?
- 같은 gcc 로 **답을 뒤집으려면** 어떤 플래그를 주는가?
- 그때 세 값은 무엇이 되는가?

### 4. 리터럴의 타입 (예측)

```c
/* 각 리터럴의 타입은 무엇인가? */
1        1u        1L        'a'
0x7fffffff          0x80000000          0xffffffff
2147483648          4294967295
sizeof(int)
```

- 아홉 개의 타입을 각각 답하라.
- `0xffffffff` 와 `4294967295` 는 값이 같은데 타입이 같은가?
- 왜 갈리는가 — 10진과 16진의 규칙 차이를 한 문장으로.
- 이것이 다음 주제에서 어떤 사고로 이어지는가?

### 5. `sizeof(int) - 5` (예측)

```c
printf("%zu\n", sizeof(int) - 5);
```

- 무엇이 찍히는가?
- `sizeof` 의 결과 타입은 무엇인가?
- `sizeof(boom())` 이라고 쓰면 `boom()` 이 실행되는가?

### 6. `int_fast16_t` 는 몇 바이트인가 (예측)

```c
printf("%zu %zu %zu %zu\n",
       sizeof(int_fast8_t), sizeof(int_fast16_t),
       sizeof(int_least16_t), sizeof(int32_t));
```

- 네 값은 각각 무엇인가?
- `int_fast16_t` 가 그 크기인 이유를 한 줄로 설명할 수 있는가?
- `int_fast16_t buf[1000000]` 은 몇 바이트를 차지하는가?
- `int32_t`·`int_least32_t`·`int_fast32_t` 중 **없을 수도 있는 것**은 어느 것인가?

### 7. `_Bool b = 0.5;` (예측)

```c
_Bool b1 = 5, b2 = 0.5, b3 = (void *)0;
printf("%d %d %d %zu %zu\n", b1, b2, b3, sizeof(_Bool), sizeof(b1 + b1));
```

- 다섯 값은 각각 무엇인가?
- `int i = 0.5;` 는 `0` 인데 `_Bool b = 0.5;` 는 왜 다른가?
- `sizeof(b1 + b1)` 이 1 이 아닌 이유는?

### 8. `bool` 은 언제부터 키워드인가 (경계)

```c
/* #include <stdbool.h> 없이 */
bool b = true;
```

- `-std=c17` 로 컴파일하면 무엇이 나오는가?
- `-std=c2x` 로 컴파일하면?
- `<stdbool.h>` 는 C17 에서 무엇을 해 주는가?
- C23 에서 `<stdbool.h>` 는 사라졌는가?

### 9. 어느 타입을 고르나 (연결)

- 파일에 쓸 길이 필드 · 배열 인덱스 · 바이트 버퍼 · 핫 루프 누적 변수 — 각각 무엇을 고르는가?
- `char` 를 바이트 버퍼에 쓰면 무엇이 깨지는가?
- 100만 개짜리 배열의 원소 타입으로 `int_fast32_t` 를 고르면 무엇이 문제인가?

### 10. 어느 층에 속하나 (경계)

다음 다섯을 **표준이 정한 것 / 구현 정의 / 미명시 / UB** 로 가르라.

- `sizeof(char) == 1`
- `sizeof(int) == 4`
- `char` 가 부호 있는가
- `int` 가 `-32767\~32767` 을 담는다
- `int32_t` 라는 이름이 존재하는가

### 11. 서식 지정자를 틀리면 (연결)

```c
size_t n = 10;  int64_t v = 1;  ptrdiff_t d = 2;
printf("%d\n", n);
printf("%ld\n", v);
printf("%d\n", d);
```

- 세 줄 중 `-Wall -Wextra` 가 경고를 내는 것은 어느 것인가?
- 경고가 안 나는 줄은 이식성이 있는가?
- 경고가 난 줄들의 **출력**은 무엇인가 — 틀린 값이 나오는가?
- 올바른 지정자는 각각 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
