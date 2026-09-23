# c/syntax/20 — 널 종단 문자열과 문자열 리터럴: 「**문자열은 타입이 아니라 0 하나로 맺는 약속이다**」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · clang 18.1.3 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra -pedantic`.
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **바이트 격자**(`61 62 63 00` 이 몇 칸인가) ② **종료 코드**(`run exit=0` 인가 `139` 인가 `1` 인가)
> ③ **그 사실이 다섯 층 중 어느 칸인가**(표준인가 구현 정의인가 미명시인가 UB 인가).
> ★★★ **이 주제는 UB 가 본체**다 — **리터럴 수정**이 그것이고, 두 번째가 **미명시**(리터럴 공유)다.
> ★ **「죽었다」가 답이 아니다** — 어느 층이라서 죽어도 되는지를 답해라.
> ★ **대조할 것이 숫자가 아닌 칸이 있다** — ASan 리포트의 주소·`pc`/`bp`/`sp`·PID·`BuildId` 와
> 섹션 주소는 **실행·빌드마다 바뀐다.** 답으로 외울 것은 **바이트 격자·종료 코드·진단 문구와 플래그 이름**이다.
> ★ **한 벌만 돌리고 답하지 마라** — 4번은 **다섯 벌**을 돌려야 답이 하나로 모이지 않는다는 것이 답이다.
> 선행 — [16번 형제](../16-array-pointer-decay-and-function-parameters/) · [15번 형제](../15-pointer-arithmetic-and-indexing/) · [14번 형제](../14-pointers-address-dereference-and-pointer-types/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 배열·포인터·손으로 쓴 네 바이트를 나란히 재면 (예측) ★★★ 이 주제의 축

```c
/* ex.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char arr[] = "abc";          /* 배열 — 복사본이 만들어진다 */
    char *lit  = "abc";          /* 포인터 — 리터럴을 가리킨다 */
    char raw[4] = {'a', 'b', 'c', '\0'};   /* 손으로 쓴 같은 것 */

    printf("sizeof arr = %zu · strlen(arr) = %zu\n", sizeof arr, strlen(arr));
    printf("sizeof lit = %zu · strlen(lit) = %zu   (★ 포인터 크기다)\n", sizeof lit, strlen(lit));
    printf("sizeof raw = %zu · strlen(raw) = %zu\n", sizeof raw, strlen(raw));
    printf("arr 과 raw 의 바이트가 같은가 : memcmp = %d\n", memcmp(arr, raw, 4));

    printf("\n바이트를 직접 본다\n");
    for (size_t k = 0; k < sizeof arr; k++)
        printf("  arr[%zu] = 0x%02x %s\n", k, (unsigned char)arr[k],
               arr[k] ? "" : "<- 널 종단자");

    printf("\n널이 중간에 있으면 — 「길이」가 둘로 갈린다\n");
    char mid[] = "ab\0cd";
    printf("  sizeof mid = %zu · strlen(mid) = %zu\n", sizeof mid, strlen(mid));
    printf("  바이트 : ");
    for (size_t k = 0; k < sizeof mid; k++) printf("%02x ", (unsigned char)mid[k]);
    printf("\n");
    printf("  printf(\"%%s\") 로 찍으면 : [%s]   <- 첫 널에서 멈춘다\n", mid);
    printf("  여섯 바이트를 눈에 보이게 : [");
    for (size_t k = 0; k < sizeof mid; k++)
        printf("%s", mid[k] ? (char[2]){mid[k], 0} : "\\0");
    printf("]\n");
    return 0;
}
```

- `sizeof arr` · `sizeof lit` · `sizeof raw` 는 각각 얼마인가?
- `strlen` 셋은 각각 얼마인가?
- ★ `memcmp(arr, raw, 4)` 는 얼마인가 — 그 값이 뜻하는 것은?
- ★★ 그 결과로 「**문자열 타입**」이 있다고 말할 수 있는가, 없다고 말할 수 있는가?
- `char mid[] = "ab\0cd"` 의 `sizeof` 와 `strlen` 은 각각 얼마인가?
- ★ `printf("%s", mid)` 는 무엇을 찍는가?

### 2. 복사본을 고치고 이어서 리터럴을 고치면 (예측) ★★★ 이 주제의 본체

```c
/* ex2.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char arr[] = "abc";          /* 배열 = 복사본 */
    char *lit  = "abc";          /* 리터럴 그 자체 */

    arr[0] = 'A';                /* (가) 복사본은 고쳐도 된다 */
    printf("(가) arr 를 고쳤다 : %s\n", arr);

    printf("(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'\n");
    lit[0] = 'A';                /* (나) 리터럴 수정 = UB */
    printf("(나) 살아남았다 : %s\n", lit);
    return 0;
}
```

- **출력은 어디까지 찍히는가** — 마지막 `printf` 는 나오는가?
- 평범한 실행의 **종료 코드**는 얼마인가 — gcc 와 clang 이 같은가?
- `-Wall -Wextra -pedantic` 으로 컴파일하면 **경고는 몇 건**인가?
- ★ ASan 으로 다시 돌리면 **무엇이라고 말하고 종료 코드는 얼마**인가?
- ★★ 이 사실은 다섯 층 중 **어느 칸**인가 — 「죽는다」가 그 칸의 정의인가?
- ★ 앞의 `arr[0] = 'A'` 는 왜 아무 일도 안 나는가 — **두 줄의 차이**는 무엇인가?

### 3. 그 위험을 컴파일러에게 물어보려면 (경계) ★★

- 2번의 코드에서 **`-Wall -Wextra -pedantic` 이 침묵하는 이유**는 무엇인가?
- 그것을 말하게 하는 플래그 이름은 무엇인가 — **gcc 와 clang 의 진단 플래그 이름이 같은가?**
- ★ 그 진단이 가리키는 것은 **「수정」인가 「초기화」인가** — 무엇이 걸린 것인가?
- ★ 리터럴이 놓인 **섹션 이름**은 무엇이고, 그것은 보장인가 관찰인가?
- ★★ ASan 의 진단 한 줄이 **무엇을 한 것인지** 말해 준다 — 그 낱말은?
- 그 플래그를 켜면 **에러가 되는가** — `cc exit` 은 얼마인가?

### 4. 같은 글자의 리터럴 둘이 같은 주소인가 (예측) ★★★ 두 번째 무게중심

```c
/* ex3.c */
#include <stdio.h>
#include <string.h>

static const char *f(void) { return "hello"; }

int main(void) {
    const char *a = "hello";
    const char *b = "hello";          /* 같은 글자의 리터럴 둘 */
    const char *c = f();              /* 다른 함수 안의 같은 리터럴 */
    const char *d = "hello world";    /* 더 긴 리터럴 */
    const char *tail = d + 6;         /* 그 꼬리 "world" */
    const char *e = "world";          /* 꼬리와 같은 글자 */

    printf("a == b            : %s   (같은 파일 안의 같은 리터럴)\n", a == b ? "★ 공유" : "따로");
    printf("a == c            : %s   (다른 함수 안의 같은 리터럴)\n", a == c ? "★ 공유" : "따로");
    printf("e == d+6          : %s   (꼬리 겹침)\n", e == tail ? "★ 공유" : "따로");
    printf("strcmp(a,b) = %d · strcmp(e,tail) = %d  (글자는 어차피 같다)\n",
           strcmp(a, b), strcmp(e, tail));
    printf("a-b 의 바이트 차  : %td\n", a - b);
    printf("d 와 a 의 차가 0 인가 : %s\n", d == a ? "그렇다" : "아니다");
    return 0;
}
```

- `a == b` 는 **다섯 벌**(gcc `-O0`·gcc `-O2`·gcc `-O2 -fno-merge-constants`·clang `-O0`·clang `-O2`)에서 각각 어떻게 나오는가?
- ★★ `e == d+6`(꼬리 겹침)은 다섯 벌에서 **갈리는가** — 갈린다면 어디서 갈리는가?
- `strcmp(a, b)` 와 `strcmp(e, tail)` 은 얼마인가 — ★ 그것이 `==` 와 무슨 상관인가?
- ★ 이 결과를 코드가 **의지해도 되는가** — 다섯 층 중 어느 칸인가?
- ★★ 다섯 벌 중 **가장 보수적인 벌**은 무엇이고, 그 벌만 보고 결론을 세우면 어떻게 틀리는가?

### 5. 세 칸짜리 배열에 네 글자 리터럴을 넣으면 (예측) ★★

```c
/* ex4.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char exact[4] = "abc";     /* 딱 맞는다 — 널까지 들어간다 */
    char tight[3] = "abc";     /* ★ 널이 안 들어간다 (표준이 허용한다) */
    char big[6]   = "abc";     /* 남는 칸은 0 으로 채워진다 */

    printf("exact : sizeof %zu · 바이트 ", sizeof exact);
    for (size_t k = 0; k < sizeof exact; k++) printf("%02x ", (unsigned char)exact[k]);
    printf("· strlen %zu\n", strlen(exact));

    printf("tight : sizeof %zu · 바이트 ", sizeof tight);
    for (size_t k = 0; k < sizeof tight; k++) printf("%02x ", (unsigned char)tight[k]);
    printf("· ★ 널이 없다 -> strlen 은 배열 밖을 읽는다(UB)\n");

    printf("big   : sizeof %zu · 바이트 ", sizeof big);
    for (size_t k = 0; k < sizeof big; k++) printf("%02x ", (unsigned char)big[k]);
    printf("· strlen %zu\n", strlen(big));
    return 0;
}
```

- **컴파일이 되는가** — `cc exit` 은 얼마인가?
- 세 배열의 **바이트 격자**는 각각 어떻게 되는가?
- ★★ **경고는 몇 건**인가 — gcc 와 clang 이 같은가?
- ★ `big` 의 남는 칸에는 무엇이 들어가는가 — 쓰레기인가 0 인가?
- ★★★ `tight` 는 **적법한가 아닌가** — 적법하다면 무엇이 위험한가?

### 6. 한 칸을 더 줄이면 (경계) ★

```c
/* ex5.c */
#include <stdio.h>

int main(void) {
    char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
    printf("%c%c\n", over[0], over[1]);
    return 0;
}
```

- 5번과 무엇이 달라졌길래 **진단이 생기는가**?
- gcc 와 clang 의 진단 문구에서 **한쪽에만 있는 것**은 무엇인가?
- 그것은 **경고인가 에러인가** — `cc exit` 은?
- ★ 5번은 0건이고 6번은 경고인 **경계선**을 한 문장으로 말하면?
- ★ 경고가 난 뒤 `over` 에는 몇 바이트가 들어가는가?

### 7. 널이 없는 배열을 `strlen` 에 넘기면 (예측) ★★★

```c
/* ex6.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char tight[3] = "abc";     /* 널이 없다 */
    printf("strlen 직전\n");
    printf("strlen(tight) = %zu\n", strlen(tight));
    printf("%%s 로 찍으면 : [%s]\n", tight);
    return 0;
}
```

- **평범한 실행**의 출력 두 줄은 각각 무엇인가?
- 평범한 실행의 **종료 코드**는 얼마인가?
- ★★ ASan 으로 돌리면 무엇이 나오고 **어느 배열의 어느 칸**을 짚는가?
- ★ `READ of size 4` 라고 나오는데 배열은 세 칸이다 — 왜 **4** 인가?
- ★★★ 이것이 이 주제에서 **가장 나쁜 자리**인 이유는?
- ★ 5번의 「경고 0건」과 이 문항의 「`run exit=0`」을 **이어 붙이면** 무엇이 되는가?

### 8. `strncpy` 를 세 가지 길이로 부르면 (예측) ★★

```c
/* ex7.c */
#include <stdio.h>
#include <string.h>

static void dump(const char *tag, const char buf[5]) {
    printf("%s : ", tag);
    for (int k = 0; k < 5; k++) printf("%02x ", (unsigned char)buf[k]);
    printf("\n");
}

int main(void) {
    /* (가) 원본이 짧으면 — 남는 칸을 전부 0 으로 채운다 */
    char a[5];
    memset(a, 0x7e, sizeof a);
    strncpy(a, "ab", 5);
    dump("(가) strncpy(a,\"ab\",5)   ", a);

    /* (나) 원본이 딱 맞으면 — 널이 안 붙는다 */
    char b[5];
    memset(b, 0x7e, sizeof b);
    strncpy(b, "abcde", 5);
    dump("(나) strncpy(b,\"abcde\",5)", b);

    /* (다) 원본이 길면 — 잘리고 널도 없다 */
    char c[5];
    memset(c, 0x7e, sizeof c);
    strncpy(c, "abcdefgh", 5);
    dump("(다) strncpy(c,\"abcdefgh\",5)", c);

    /* (라) 안전하게 쓰는 꼴 — 마지막 칸을 직접 0 으로 */
    char d[5];
    strncpy(d, "abcdefgh", sizeof d - 1);
    d[sizeof d - 1] = '\0';
    dump("(라) 마지막 칸을 손으로 0", d);
    printf("     d = [%s] · strlen = %zu\n", d, strlen(d));
    return 0;
}
```

- (가)·(나)·(다) 세 배열의 **바이트 격자**는 각각 어떻게 되는가?
- ★ `0x7e` 로 미리 채워 둔 것은 **무엇을 보려고** 한 것인가?
- gcc 의 경고는 **몇 건이고 어느 호출**에 대한 것인가 — ★ `-O2` 에서 **문구가 달라지는가**?
- ★★ clang 은 `-O2` 에서 몇 건인가?
- (라)처럼 쓰면 무엇이 보장되고 무엇이 **여전히 보장되지 않는가**?

### 9. `sizeof` 와 `strlen` 이 답하는 것 (왜) ★★


- 두 값은 각각 **무엇을 세는가** — 어느 쪽이 컴파일 시간이고 어느 쪽이 실행 시간인가?
- ★ `char *p = "abc"` 에서 `sizeof p` 가 배열 크기가 아닌 이유는 어느 주제가 정본인가?
- 둘이 **갈라지는 입력** 두 가지를 대면?
- ★ 널이 아예 없으면 `strlen` 은 무엇을 답하는가 — 그것은 「답」인가?

### 10. 리터럴로 배열을 초기화하면 왜 복사본인가 (왜) ★★

- `char s[] = "abc"` 와 `char *p = "abc"` 는 각각 **무엇이 만들어지는가**?
- ★ 앞엣것에서 리터럴이 **감쇠하지 않는** 이유는 — 어느 주제가 정본인가?
- 「복사본이다」를 **출력으로 증명**하려면 무엇을 찍으면 되는가?
- ★ 복사본의 저장 기간과 리터럴의 저장 기간은 어떻게 다른가?
- ★★ `char *p = "abc"` 를 **고칠 수 있게 만드는** 가장 싼 고침은 무엇인가?

### 11. 다섯 층과 무게중심 (연결) ★★★

- 이 주제에서 **표준 / 조건부 표준 / 구현 정의 / 미명시 / UB** 칸에 각각 무엇이 들어가는가?
- **비어 있는 칸**은 무엇인가?
- ★★ 이 주제에서 **가장 두꺼운 칸**과 **두 번째로 두꺼운 칸**은 각각 무엇인가?
- ★ **도구가 침묵하는 자리**를 층마다 하나씩 대면?
- ★ [16번 형제](../16-array-pointer-decay-and-function-parameters/)의 층 분포와 **무엇이 같고 무엇이 다른가**?

### 12. 경계 — 어디까지가 이 주제인가 (연결) ★

- `strcpy`·`strcat`·`strlen` 같은 **`<string.h>` 함수들의 계약 전반**은 어느 주제가 정본인가?
- **배열이 포인터로 감쇠하는 규칙** 자체는 어느 주제가 정본인가?
- **배열 밖 접근이 무엇을 만드나**는 어느 주제가 정본인가?
- 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?
- ★ `char *q = "hi"` 와 `char s[] = "hi"` 의 `sizeof` 대비는 어느 주제가 먼저 다뤘는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
