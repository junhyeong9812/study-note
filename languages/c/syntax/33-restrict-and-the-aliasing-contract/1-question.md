# c/syntax/33 — `restrict` 와 앨리어싱 계약: 「**겹치지 않는다는 약속 — 지키는 것은 호출자다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · glibc · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **`restrict` 가 번역을 무엇으로 바꾸나**(어셈블리의 로드 수) ② **약속을 어기면 무엇이 나오나**(값 — 그리고 그것이 왜 결론이 아닌가)
> ③ **누가 그 약속을 지켜 주나**(경고 · sanitizer · 서명).
> ★★★ **본체 창은 `-O2` 어셈블리** — 1·2번은 **읽는 명령 수**까지 적어야 답이다.
> ★★★ **3·4번의 값은 UB 의 한 판 결과**다 — 「**어느 판에서 무엇이 나왔나**」를 적되 그것을 **규칙으로 적지 마라.**
> ★ **시간은 묻지 않는다** — 이 편은 재지 않았다.
> 선행 — [31번 형제](../31-const-and-pointer-const-placement/)(`twice_read` 가 여기서 온다) · 목록의 **55번 주제**.

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1\~6)은 소스만 보고 적어 본 뒤** 답을 연다.
- ★★★ **1·3·4번은 판 격자**다 — 컴파일러 2 × 최적화 수준. 한 칸으로 답하지 마라.
- ★★ **5번은 칸마다 「답했나」를 먼저** 적고, 답했다면 **무엇을 보고 답했나**를 적어라.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이 약속을 지켜야 하는 것은 함수를 쓴 쪽인가, 부르는 쪽인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 31편의 `twice_read` 에 `restrict` 를 붙인 판 — `*p` 를 읽는 명령 (예측) ★★★ 이 주제의 축

```c
/* s33a.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int restrict_p_only(const int *restrict p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int restrict_q_only(const int *p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}
```

- ★★★ `twice_read` 와 `twice_read_r` 은 **gcc `-O2`** 에서 `*p` 를 각각 **몇 번** 읽는가? **clang `-O2`** 는?
- ★★ 읽기가 줄었다면 **두 번째 `*p` 는 무엇으로** 바뀌었는가?
- ★★ **`-O0`** 에서는?
- ★ 이 차이를 「**빨라졌다**」로 적어도 되는가?

### 2. 한쪽에만 붙이면 (예측) ★★

같은 `s33a.c` 의 `restrict_p_only` · `restrict_q_only` 다.

- ★★ 두 함수의 `-O2` 는 `*p` 를 각각 몇 번 읽는가?
- ★★ 표준의 형식 정의(「그 포인터로 접근하는 객체가 **고쳐진다면** …」)로 그 결과를 설명할 수 있는가?
- ★ `-std=c89 -pedantic` 으로 이 파일을 컴파일하면?

### 3. 같은 `x` 를 두 포인터로 넘기면 (예측) ★★★

```c
/* s33b1.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

void copy_plain(int *d, const int *s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}

void copy_restrict(int *restrict d, const int *restrict s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}
```

```c
/* s33b2.c */
#include <stdio.h>

int  twice_read(const int *p, int *q);
int  twice_read_r(const int *restrict p, int *restrict q);
void copy_plain(int *d, const int *s, int n);
void copy_restrict(int *restrict d, const int *restrict s, int n);

static void show(const char *tag, const int *a) {
    printf("%-14s", tag);
    for (int i = 0; i < 8; i++) printf(" %d", a[i]);
    printf("\n");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int x = 7, *p = &x, *q = &x;           /* 두 포인터가 같은 x */
    printf("twice_read   (p, q) = %d\n", twice_read(p, q));
    x = 7;
    printf("twice_read_r (p, q) = %d\n", twice_read_r(p, q));

    int a[8], b[8];
    for (int i = 0; i < 8; i++) a[i] = b[i] = i;
    copy_plain(a + 1, a, 7);               /* 목적지가 원본보다 한 칸 뒤 */
    copy_restrict(b + 1, b, 7);
    show("copy_plain", a);
    show("copy_restrict", b);
    return 0;
}
```

- ★★★ `twice_read(p, q)` 와 `twice_read_r(p, q)` 의 출력은 **gcc/clang × `-O0`/`-O1`/`-O2`** 에서 각각?
- ★★ 어느 쪽이 **UB** 인가? 그 판단은 **값을 보고** 하는가, **규칙을 보고** 하는가?
- ★★ 값이 갈리는 판을 보고 「**`-O0` 이면 안전하다**」고 적어도 되는가?

### 4. 겹치는 배열을 복사 루프 둘에 (예측) ★★★

같은 `s33b1.c`·`s33b2.c` 의 `copy_plain(a + 1, a, 7)` · `copy_restrict(b + 1, b, 7)` 다.

- ★★★ 두 줄의 출력은 **판마다** 어떻게 되는가? **어느 쪽이 C 의 뜻**인가?
- ★★★ `-O2` 에서 `copy_restrict` 의 어셈블리에는 **루프가 있는가**? 없다면 **무엇이** 있는가?
- ★★ `copy_restrict` 가 어떤 판에서 낸 값은 **어떤 표준 함수**의 결과와 같은가? 그 같음은 **누구의 성질**인가?

### 5. 3·4번을 ASan·UBSan 격자로 돌리면 (예측) ★★

**탐침** — 컴파일러 2 × sanitizer 2(`-fsanitize=address` · `-fsanitize=undefined`) × `-O0`/`-O2` = 8칸. 칸마다 3·4번의 두 위반을 한 번에 돌린다.

- ★★★ 몇 칸이 **리포트를 냈는가**? 낸 칸은 **무슨 이름**의 리포트인가?
- ★★★ 그 리포트는 **`restrict` 를 본 것**인가? 아니면 무엇을 본 것인가?
- ★★ 같은 소스 · 같은 `-O2` 인데 **gcc ASan 이 침묵한** 이유를 어셈블리로 확인하려면 무엇을 세는가?
- ★★ sanitizer 판에서 `twice_read_r` 이 **`7`** 이 나온 칸이 있다면, 그것은 무엇을 뜻하는가?

### 6. 컴파일러 경고 — 글자로 같은 인자와 변수로 같은 인자 (예측) ★★

```c
/* s33d.c */
int twice_read_r(const int *restrict p, int *restrict q);

int by_address(void) {
    int x = 7;
    return twice_read_r(&x, &x);
}

int by_variables(void) {
    int x = 7, *p = &x, *q = &x;
    return twice_read_r(p, q);
}
```

- ★★ gcc `-Wall` 은 `by_address` · `by_variables` 중 **어느 것**에 경고하는가? **`-O0`** 에서도 같은가?
- ★★ clang 은?
- ★ 경고가 나도 **`cc exit`** 는?

### 7. `memcpy` 와 `memmove` 의 서명 (왜) ★★

- ★★★ glibc `string.h` 의 두 서명은 **어디가** 다른가? 그 차이가 **무슨 뜻**인가?
- ★★ 겹치는 영역에 `memcpy` 를 부르면 표준은 무엇이라고 하는가? **이 glibc 판**에서는 무엇이 나왔나?
- ★★ ASan 은 그것을 **잡는가**? 두 컴파일러가 같은가?

### 8. C++ 에는 `restrict` 가 없다 (경계) ★

- ★★ C++17 에서 `restrict` 를 쓰면 g++·clang++ 는 무엇을 하는가?
- ★ `__restrict__` 는? `-pedantic` 은 그것을 문제 삼는가?

### 9. `const` · `volatile` · `restrict` — 한정자 세 개 (연결) ★★

- ★★★ 셋이 각각 **누구에게 무엇을** 약속하는가?
- ★★ 31편의 `twice_read` 는 `const` 인데 **왜** 두 번 읽었나? `restrict` 는 무엇을 바꿨나?
- ★ 32편의 `volatile` 과 이 편의 `restrict` 는 **로드 수를 어느 방향으로** 움직이는가?

### 10. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- ★★★ 「**적격한 프로그램에서 `restrict` 를 전부 지워도 뜻이 같다**」는 문장이 왜 이 주제의 무게중심을 UB 칸으로 옮기는가?
- ★★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★★ 이 편에 「**종료 코드 0인데 ill-formed**」 새 항목이 있는가? 없다면 **대신 무엇이** 있는가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- **타입이 다른 포인터**로 같은 메모리를 읽는 규칙은 목록의 몇 번 주제인가?
- **`const`** 와 **`volatile`** 은 각각 어느 형제가 정본인가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
