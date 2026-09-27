# c/syntax/16 — 배열-포인터 감쇠와 함수 매개변수: 「**함수 문턱에서 길이를 잃는다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 답은 대부분 `sizeof` 의 숫자**다. **40 인가 8 인가 16 인가**를 맞히는 것이 인출이다.
> ★ **경고는 몇 건이고 어느 플래그의 것인가**를 같이 답해라 —
> ★★ **이 주제의 경고는 `-pedantic` 이 필요 없다.** [13번](../13-goto-cleanup-idiom/)·[14번](../14-pointers-address-dereference-and-pointer-types/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 정반대다.
> 선행 — [15번 형제](../15-pointer-arithmetic-and-indexing/) · [01번 형제](../01-declaration-syntax-and-reading/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 배열을 세 꼴로 받아 `sizeof` 를 찍으면 (예측) ★★★ 이 주제의 축

```c
static void f_sized(int a[10])  { printf("%zu\n", sizeof a); }
static void f_open (int a[])    { printf("%zu\n", sizeof a); }
static void f_ptr  (int *a)     { printf("%zu\n", sizeof a); }

int main(void) {
    int arr[10] = {0};
    printf("%zu\n", sizeof arr);
    f_sized(arr);  f_open(arr);  f_ptr(arr);
}
```

- **네 숫자**는 각각 얼마인가?
- 경고는 몇 건인가 — **세 함수 중 몇 개**에 대한 것인가?
- ★ 경고가 **안 붙는 함수**는 어느 것이고 왜인가?
- 이 경고를 보려면 어느 플래그가 필요한가?

### 2. `sizeof` 로 감쇠 여부를 들여다보면 (예측) ★★

```c
int arr[10] = {0};

sizeof arr;              sizeof *&arr;
sizeof (arr + 0);        sizeof (1 ? arr : arr);
sizeof (arr, arr);       sizeof &arr[0];
sizeof &arr;             sizeof (int *){arr};
```

- **여덟 값**은 각각 얼마인가?
- 그중 **감쇠가 일어나지 않은** 것은 몇 개인가?
- gcc 와 clang 의 경고 건수가 다른가 — **왜인가?**
- ★ `sizeof (+arr)` 를 넣으면 무슨 일이 나는가?

### 3. 감쇠가 안 일어나는 세 자리를 증명하면 (예측) ★★★

```c
int arr[10] = {0};
printf("%zu\n", sizeof arr);

int  *p1 = arr;
int (*p2)[10] = &arr;
/* arr, arr+1, &arr, &arr+1 의 주소와 바이트 차이를 찍는다 */
/* arr==&arr[0] 과 (void*)arr==(void*)&arr 도 찍는다 */
/* sizeof p1, sizeof p2, sizeof *p2 도 찍는다 */

char s[] = "hi";
char *q  = "hi";
/* sizeof s, sizeof q, s 의 수정 가능 여부, 두 주소를 찍는다 */
```

- `arr + 1` 과 `&arr + 1` 은 각각 **몇 바이트** 움직이는가?
- `sizeof p2` 와 `sizeof *p2` 는 각각 얼마인가?
- `sizeof s` 와 `sizeof q` 는 각각 얼마인가 — **왜 다른가?**
- ★ 경고는 몇 건인가 — 그것이 뜻하는 것은?

### 4. 매개변수에 `static` 을 넣고 계약을 어기면 (예측) ★★

```c
static int sum10(int a[static 10]) {
    int s = 0;
    for (int i = 0; i < 10; i++) s += a[i];
    return s;
}
int main(void) {
    int big[10] = {1,2,3,4,5,6,7,8,9,10};
    int small[3] = {1,2,3};
    sum10(big);  sum10(small);  sum10(NULL);
}
```

- `sizeof` 는 달라지는가?
- 경고는 몇 건이고 **어느 호출**에 대한 것인가 — gcc 와 clang 의 **플래그 이름이 같은가?**
- `static` 을 빼면 각 컴파일러는 몇 건인가 — ★ **둘이 같은가?**
- 최적화 수준을 바꾸면 건수가 달라지는가?
- 평범한 실행과 ASan 실행의 **종료 코드**는?

### 5. 2차원 배열을 함수에 넘기면 (예측) ★★

```c
static void row_form(int a[][4], int rows) {
    printf("%zu %zu %zu\n", sizeof a, sizeof a[0], sizeof a[0][0]);
    printf("%d\n", a[1][0]);
}
int main(void) {
    int m[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    printf("%zu %zu %zu\n", sizeof m, sizeof m[0], sizeof m[0][0]);
    int (*p)[4] = m;
    printf("%zu %zu\n", sizeof p, sizeof *p);
    row_form(m, 3);
}
```

- **여덟 숫자**는 각각 얼마인가?
- 매개변수 안에서 **무엇을 잃고 무엇이 남았나?**
- `a[1][0]` 이 맞는 값을 내는 이유는?
- ★ `int **p` 로 받으면 무슨 진단이 나오는가 — 경고인가 에러인가?

### 6. 감쇠가 일어나는 자리를 전부 대면 (경계) ★★

- 배열 이름이 감쇠하는 자리를 **아홉 개** 대면?
- 감쇠 **안 하는** 자리 셋은?
- `sizeof arr / sizeof arr[0]` 이 함수 안에서 내는 값은 얼마인가 — ★ 왜 그 값이 더 나쁜가?

### 7. `&arr` 와 `arr` (왜) ★★

- 두 식의 **타입**은 각각 무엇인가?
- **주소값**은 같은가?
- `sizeof` 로 둘을 구분할 수 있는가 — 없다면 **무엇으로** 구분하는가?

### 8. 문자열 리터럴의 두 얼굴 (경계) ★

- `char s[] = "hi"` 와 `char *q = "hi"` 는 각각 무엇을 만드는가?
- 둘 중 **고칠 수 있는** 것은?
- 주소가 어느 대역에 놓였는가 — 그것이 보장인가 관찰인가?

### 9. 어느 도구가 무엇을 보나 (연결) ★★

- 다섯 프로그램 중 **경고 0건**인 것은 무엇인가?
- 이 주제의 경고 중 **`-pedantic` 이 필요한 것**은 몇 개인가?
- gcc 와 clang 이 **서로 다른 것을 보는** 자리 둘은?
- ★ **`int *a` 로 써 놓으면 왜 `sizeof` 함정이 안 잡히는가?**

### 10. 다섯 층과 무게중심 (연결) ★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- [15번 형제](../15-pointer-arithmetic-and-indexing/)와 UB 의 **모양**이 어떻게 다른가?
- ★ 이 주제의 **네 번째 창** 둘은 무엇인가?

### 11. 경계 — 어디까지가 이 주제인가 (연결) ★

- 동적 배열의 **용량·증가 전략**은 어느 갈래가 정본인가?
- `int (*)[4]` 를 `int **` 로 받았을 때 **무엇을 읽게 되는가**는 어느 주제가 정본인가?
- `char *q = "hi"; q[0] = 'H';` 는 어느 주제가 정본인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
