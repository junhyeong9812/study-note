# c/syntax/13 — `goto cleanup` 관용구: 「**분기가 아니라 중복을 줄인다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제에는 UB 가 거의 없다.** [12번 형제](../12-control-flow-and-switch/)와 같은 모양이고
> [15번 형제](../15-pointer-arithmetic-and-indexing)·[16번 형제](../16-array-pointer-decay-and-function-parameters)가 **UB 가 본체**인 것과 정반대다 — 여기는 **「표준」이 본체**다.
> ★ **그러니 「몇 건이 나고 어느 플래그의 것인가」와 「경고인가 에러인가」를 같이 답해라.**
> ★★ **「경고 0건」은 종료 코드를 같이 봐야 뜻이 있다** — 이 주제에는 **경고 0건에 `exit=1`** 인 프로그램이 둘 있다.
> 선행 — [12번 형제](../12-control-flow-and-switch/) · 목록의 **37번 주제**.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 자원 셋을 잡는 함수를 단계마다 실패시키면 (예측) ★★

```c
static int run(void) {
    char *buf = NULL;  FILE *f = NULL;  int *tbl = NULL;
    int rc = -1;
    buf = get_buf(1, 64);            if (!buf) goto out;
    f   = get_file(2, "/tmp/x");     if (!f)   goto out_buf;
    tbl = get_tbl(3, 8);             if (!tbl) goto out_file;
    if (fail_at == 4) goto out_tbl;
    rc = 0;
out_tbl:  free(tbl);   printf("  <-- table 해제\n");
out_file: fclose(f);   printf("  <-- file  해제\n");
out_buf:  free(buf);   printf("  <-- buf   해제\n");
out:      printf("  rc=%d\n", rc);   return rc;
}
/* fail_at 을 0,1,2,3,4 로 두고 다섯 번 부른다 */
```

- 다섯 번의 호출은 각각 **해제를 몇 줄** 찍는가?
- `fail_at=2` 일 때 `fclose` 가 불리는가 — 왜인가?
- 해제 순서는 획득 순서와 어떤 관계인가?
- 경고는 몇 건이고, ASan+UBSan 은 무엇이라 하는가?

### 2. 같은 일을 세 가지 모양으로 짜서 `-O2` 로 컴파일하면 (예측) ★★★ 이 주제의 축

```c
int with_goto(void) { /* 실패마다 goto out_x; 라벨에 해제를 층층이 */ }
int with_nest(void) { /* if (a) { if (b) { if (c) { ... } rel2(b); } rel1(a); } */ }
int with_dup (void) { /* 실패마다 { rel1(a); return -1; } 처럼 해제를 복사 */ }
```

- 세 함수의 **명령 수·분기 수·`call` 수**는 어떤 관계인가?
- `-O0` 에서도 같은 순서인가?
- **소스에 해제 호출이 몇 번 적혔나**를 세면 무엇이 보이는가?
- 그래서 이 관용구가 파는 것은 무엇인가?

### 3. `free` 와 `fclose` 에 널을 넘기면 (예측) ★★

```c
char *p = NULL;
free(p);
printf("free(NULL) 통과\n");
fflush(stdout);

FILE *f = NULL;
fclose(f);
printf("fclose(NULL) 통과\n");
```

- 이 프로그램은 몇 줄을 찍고 **종료 코드는 얼마**인가?
- 컴파일 경고는 몇 건인가?
- ASan+UBSan 을 붙이면 **무엇이 추가로 나오는가** — 그 근거는 표준인가 구현인가?
- ★ 이 사실이 **라벨 설계**에 무엇을 강제하는가?

### 4. 라벨 바로 뒤에 선언을 두면 (예측) ★★

```c
static int run(int fail) {
    char *buf = malloc(8);
    if (!buf) return -1;
    if (fail) goto out;
    buf[0] = 'x';
out:
    int n = 1;
    free(buf);
    return n;
}
```

- `gcc -std=c17 -Wall -Wextra` 는 몇 건인가?
- `-pedantic` 을 붙이면 몇 건이고 **어느 플래그**인가 — `-pedantic-errors` 면?
- `clang -std=c17 -Wall -Wextra` 는 몇 건인가 — gcc 와 **왜 다른가?**
- `-std=c2x` 로 바꾸면 어떻게 되는가?

### 5. 라벨을 블록의 마지막에 두면 (예측)

```c
static void run(int fail) {
    char *buf = malloc(8);
    if (!buf) return;
    if (fail) goto out;
    buf[0] = 'x';
out:
    free(buf);
cleanup_end:
}
```

- 이것은 컴파일되는가 — 되면 경고는 몇 건인가?
- `-pedantic` 이 말하는 것과 `-Wall` 이 말하는 것은 **서로 다른 이야기인가?**
- 고치는 데 필요한 글자는 몇 개인가?

### 6. `goto` 가 선언을 건너뛰면 (예측) ★★

```c
int fail = 1;
if (fail) goto skip;
{
    int v = 99;
skip:
    printf("v=%d\n", v);
}
```

- 이것은 **에러인가 경고인가** — 컴파일되는가?
- 컴파일된다면 무엇을 찍는가 — **여러 번 돌리면 같은가?**
- `gcc -O0`·`-O1`·`-O2` 는 각각 몇 건인가 — 가리키는 줄이 어디인가?
- `clang -O0` 은 몇 건인가 — ★ 이 차이가 뜻하는 것은?

### 7. `goto` 가 못 넘는 선 (경계) ★

- `goto` 로 **할 수 있는 것** 셋과 **못 하는 것** 둘을 대면?
- VLA 스코프 안으로 뛰면 경고인가 에러인가 — **종료 코드**는?
- 다른 함수의 라벨로 뛰면 진단 문구가 무엇인가 — 「금지」인가 「없다」인가?
- **보통 변수의 초기화를 건너뛰는 것**은 왜 막히지 않는가?

### 8. 이 패턴이 C 에만 남는 이유 (왜) ★★

- C++ · Rust · Go · Java 는 같은 일을 무엇으로 하는가 — 각각 한 줄로?
- C 에 없는 것 **둘**을 대면?
- 그래서 `goto` 가 이 자리를 맡게 된 이유를 한 문장으로 쓰면?
- ★ 이것은 「`goto` 를 쓰자」는 주장인가?

### 9. 라벨 이름과 역순 해제 (경계) ★

- 라벨 이름을 `out_buf` 로 지을 때와 `free_buf` 로 지을 때 **읽는 방향**이 어떻게 달라지는가?
- 라벨을 **어느 순서로 쌓아야** 역순 해제가 저절로 되는가 — 그것을 가능하게 하는 문법 성질은?
- 자원 포인터를 `= NULL` 로 초기화하는 것이 막는 사고는 무엇인가?
- 라벨을 **하나로 합쳐도 되는** 조건은?

### 10. 다섯 층과 도구 (연결) ★★

- 이 주제에서 **표준 / 구현 정의 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇이고 왜 비었는가?
- [12번](../12-control-flow-and-switch/)·[15번](../15-pointer-arithmetic-and-indexing)·[16번 형제](../16-array-pointer-decay-and-function-parameters)와 견주면 이 주제의 층 분포는 어떻게 다른가?
- ★ **어떤 컴파일러도 안 잡는 함정** 하나를 대면 — 무엇이 잡는가?

### 11. 플래그별 경고 수와 종료 코드 (연결) ★★

- 여덟 프로그램 중 **경고 0건인데 `exit=1`** 인 것은 몇 개인가?
- `-pedantic` 이 있어야만 보이는 것 둘은?
- gcc 와 clang 이 **서로 다른 것을 보는** 자리 둘은?
- ★ `grep -c warning` 과 `grep -c 'warning:'` 은 왜 다른 수를 내는가?

### 12. 이 주제의 네 번째 창 (연결) ★

- 컴파일 진단 · 실행 출력 · sanitizer 세 창으로 **안 잡히는 것**은 무엇인가?
- 그래서 이 주제가 더 쓴 창 **둘**은 무엇인가?
- 그 둘이 각각 **반증한 것**과 **검산한 것**은 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
