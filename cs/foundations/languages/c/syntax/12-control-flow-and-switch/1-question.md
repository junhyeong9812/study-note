# c/syntax/12 — 제어문과 `switch`: **점프이지 블록이 아니다** — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제에는 UB 가 거의 없다.** [11번 형제](../11-bitwise-operations-and-shifts/)는 **UB 가 본체**였고 [10번 형제](../10-evaluation-order-and-sequence-points/)는 **미명시가 본체**였는데
> 여기는 **「표준」과 「컴파일 에러」가 본체**다 — 그래서 **sanitizer 가 아니라 컴파일러 진단**이 답이 된다.
> ★ **그러니 「몇 건이 나고 어느 플래그의 것인가」와 「경고인가 에러인가」를 같이 답해라.**
> ★★ **컴파일이 실패한 것도 출력이다** — 이 주제에는 **에러가 나는 프로그램이 넷** 있다.
> 선행 — [07번 형제](../07-enum-and-enumeration-constants/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 중괄호를 뺀 중첩 `if` (예측)

```c
int a = 0, b = 0;
if (a == 1)
    if (b == 1)
        printf("둘 다 1\n");
else
    printf("else 가 어디에 붙었나?\n");
printf("끝\n");
```

- 이 프로그램은 무엇을 찍는가 — **몇 줄**인가?
- `else` 는 어느 `if` 에 붙었는가?
- 경고는 몇 건이고 **어느 플래그**의 것인가 — `-Wextra` 단독으로도 나는가?
- gcc 와 clang 이 **가리키는 줄**이 같은가?

### 2. 루프 안의 `switch` 와 `continue` (예측) ★★

```c
for (int i = 0; i < 4; i++) {
    switch (i) {
    case 1: break;
    default: printf("%d ", i);
    }
    printf("| ");
}
/* --- */
int n = 0;
do { n++; if (n == 2) continue; printf("n=%d ", n); } while (n < 4);
/* --- */
for (int i = 0; i < 3; i++) {
    switch (i) {
    case 0: printf("zero ");  break;
    default: printf("other "); break;
    case 2: printf("two ");   break;
    }
}
```

- 세 덩어리는 각각 무엇을 찍는가?
- 첫 덩어리에서 `case 1: break;` 는 **무엇을 끝내는가?**
- 둘째 덩어리는 무한 루프가 되는가?
- 셋째 덩어리에서 `default` 가 가운데 있는데 문제가 되는가?
- 이 프로그램의 경고 건수는?

### 3. `break` 를 빠뜨리면 (예측)

```c
static void run(int x) {
    printf("x=%d : ", x);
    switch (x) {
    case 1: printf("one ");
    case 2: printf("two "); break;
    case 3: printf("three ");
            /* fall through */
    case 4: printf("four "); break;
    default: printf("other ");
    }
    printf("\n");
}
/* x = 1..5 로 부른다 */
```

- 다섯 줄은 각각 무엇을 찍는가?
- `gcc -Wall` 과 `gcc -Wextra` 는 각각 몇 건인가?
- `gcc -Wimplicit-fallthrough=5` 는 몇 건인가 — 왜 달라지는가?
- `clang -Wall -Wextra` 는 몇 건인가?

### 4. `case` 가 `do` 루프 안에 있으면 (예측) ★★★ 이 주제의 축

```c
static void send(const char *from, char *to, int count) {
    int n = (count + 7) / 8;
    switch (count % 8) {
    case 0: do { *to++ = *from++;
    case 7:      *to++ = *from++;
    case 6:      *to++ = *from++;
    case 5:      *to++ = *from++;
    case 4:      *to++ = *from++;
    case 3:      *to++ = *from++;
    case 2:      *to++ = *from++;
    case 1:      *to++ = *from++;
            } while (--n > 0);
    }
}
/* "ABCDEFGHIJKLMNOPQRSTU"(21자)를 보낸다 */
```

- **컴파일이 되는가?** 된다면 무엇을 찍는가?
- `count = 21` 일 때 **어느 `case` 로 뛰고 몇 바퀴를 도는가?**
- 경고는 몇 건이고 어느 플래그인가?
- ★ 이 코드가 합법이라는 사실은 `switch` 에 대해 **무엇을 증명하는가?**

### 5. `switch` 안에서 선언하면 (예측) ★★

```c
int x = 2;
switch (x) {
    int v = 99;
case 1: printf("case 1: v=%d\n", v); break;
case 2: printf("case 2: v=%d\n", v); break;
}
```

- 이것은 **에러인가 경고인가** — 컴파일되는가?
- 컴파일된다면 무엇을 찍는가 — gcc 와 clang 이 같은 값을 찍는가?
- 경고는 몇 건이고 어느 플래그인가?
- ★ `int v = 99;` 를 `int vla[x];` 로 바꾸면 무엇이 달라지는가?

### 6. `char` 를 `switch` 하면 (예측)

```c
char c = (char)200;
printf("c = %d  (CHAR_MIN=%d)\n", c, CHAR_MIN);
switch (c) {
case 200: printf("case 200 에 걸렸다\n"); break;
case -56: printf("case -56 에 걸렸다\n"); break;
default:  printf("default\n"); break;
}
unsigned char u = 200;
switch (u) {
case 200: printf("unsigned char 200 은 case 200 에 걸린다\n"); break;
default:  printf("default\n"); break;
}
```

- 네 줄은 무엇을 찍는가?
- 같은 `200` 인데 두 `switch` 의 결과가 다른 이유는?
- 경고는 몇 건이고 gcc 와 clang 이 **같은 플래그 이름**으로 말하는가?
- `c` 가 `-56` 인 것은 무슨 층인가?

### 7. `switch` 는 블록인가 점프인가 (왜) ★★

- 4번의 코드가 합법인 **이유**를 한 문장으로 쓰면?
- `case 3:` 은 **문인가 라벨인가** — `goto` 의 `out:` 과 무엇이 같은가?
- 그래서 fall-through 는 **버그인가 설계인가?**

### 8. `goto` 가 못 넘는 선 (경계) ★

- `goto` 로 **할 수 있는 것** 셋과 **못 하는 것** 둘을 대면?
- VLA 스코프 안으로 뛰면 **경고인가 에러인가** — 종료 코드는?
- gcc 와 clang 의 진단 문구는 어떻게 다른가 — 어느 쪽이 **이유**를 말하는가?
- 같은 규칙이 `switch` 에도 걸리는가?

### 9. `case` 에 무엇을 쓸 수 있나 (경계) ★★

- 열거 상수·매크로·`1 + 1`·`sizeof(int)` 는 되는가?
- `const int K = 3;` 을 `case K:` 로 쓰면 어떻게 되는가 — **gcc 와 clang 이 같은가?**
- `switch (1.0)` 과 중복 `case` 는 각각 무엇이 되는가?
- 이 중 **「내 기계에서는 된다」가 나는 자리**는 어디인가?

### 10. `-std=` 는 무엇을 강제하나 (경계) ★★★

- `[[fallthrough]]`(C23)를 `gcc -std=c89 -Wall -Wextra` 로 컴파일하면 몇 건인가?
- 그것을 드러내려면 무엇이 필요한가?
- 「라벨 뒤 선언」은 `-pedantic` 과 `-pedantic-errors` 에서 각각 어떻게 되는가?
- gcc 13 에서 C23 을 쓰려면 어느 플래그를 쓰는가?

### 11. `for (;;)` 과 `while (1)` (경계)

- 둘 중 어느 쪽이 빠른가 — **무엇으로 확인했는가?**
- `-O2` 뿐 아니라 **`-O0`** 에서도 같은가 — 왜 그것이 더 강한 근거인가?
- `while (1)` 의 조건 비교는 어셈블리 어디에 있는가?

### 12. 다섯 층과 도구 (연결) ★★

- 이 주제에서 **표준 / 구현 정의 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇이고 왜 비었는가?
- [10번](../10-evaluation-order-and-sequence-points/)·[11번 형제](../11-bitwise-operations-and-shifts/)와 견주면 이 주제의 층 분포는 어떻게 다른가?
- ★ **어떤 도구도 안 잡는 함정** 하나를 대면 — 왜 안 잡히는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
