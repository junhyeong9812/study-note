# c/syntax/51 — `<stdlib.h>` 변환 · `qsort` · `bsearch`: 「**`atoi` 에는 실패를 말할 자리가 없다 — `strtol` 의 `endptr` 와 `errno` 가 그 자리다**」 — 정리 (힌트)

★★★ **본체는 둘째 창 — 실행 출력의 변환 격자다.** 입력 열 개를 `atoi` 와 `strtol`(+`endptr`+`errno`)에 넣고, 칸마다 **값 · 소비한 글자 수 · `errno` · 남은 글자 수**를 찍어 **스크립트가 「`strtol` 이 알린 것」을 분류**한다.
★★★ 그 격자에서 **`strtol` 이 성공이 아니라고 알린 입력 6 / 10** — `atoi` 는 그 여섯을 **성공과 가를 수단이 없다**(다섯은 평범한 값을 돌려주고, 하나는 UB 다).

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | gcc `-Wcast-function-type` 은 **포인터 매개변수끼리는 봐준다** · clang 은 **`-Wcast-function-type` 을 따로 줘야** 둘 다 잡는다((4)) | 씀 |
| ★★★ ② **실행 출력(변환 격자)** | ★ **본체** — `atoi` 값 · `strtol` 의 값/`endptr`/`errno` | 씀 |
| ③ sanitizer | ★★ **틀린 비교자 둘 중 UBSan 이 말한 것은 한 줄**, 그것도 `implicit-conversion` 을 켰을 때만 · `-fsanitize=function` 은 **`qsort` 안의 호출을 못 본다** | 씀 |
| ④ 링크 심볼 | ★★ `-std=c17` 은 `strtol` · `-std=c2x` 는 **`__isoc23_strtol`** 로 링크된다((2)) | 씀 |
| 시간 측정 | — | 부적용(성능 주제가 아니다 — `qsort` 속도는 재지 않았다) |
| ★ 제5의 상태 | 「`qsort` 는 안정 정렬인가」는 **보통 실행으로는 늘 「그렇다」로 보인다** — **주소 공간 한도(`ulimit -v`)** 로 glibc 의 임시 버퍼 할당을 실패시켜 **다른 경로**를 태워 물었다((5)) | 창을 바꿔 답함 |

★ **바꾼 창(`ulimit -v`)이 못 보는 것** — glibc `qsort` 의 **어느 경로가 무슨 알고리즘인지**는 말하지 않는다. 보이는 것은 **「같은 키 사이 순서가 뒤집혔나」** 라는 결과뿐이다.

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | 없음 | 이 편은 리포트에 PID·주소가 찍히는 블록이 없다(UBSan 리포트는 `파일:줄:칸` 뿐) |
| 안 흔들린다 | ★★★ **변환 격자 · 진법 격자** · 비교자 격자 · 경고 | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다(선언) | ★★ **`ulimit -v 15000` 칸의 `580403`** | 이 판 · 이 한도에서 재현됐다. ★ **한도 값은 판을 탄다** — 다섯 값을 따로 찍었다((5)의 둘째 블록) |

★★ **정규화 규칙은 기본 넷뿐**이다(이 편에서는 지울 것이 없다).

## 한눈에 — 쉽게 말하면

**문자열을 숫자로 읽는 것은 「주문서 받기」다.**

- **`atoi` 는 주문서를 읽고 숫자만 불러 준다** — 읽다가 막혀도 **「어디서 막혔는지」를 말하지 않는다.** 빈 주문서도, 「사과」라고 적힌 주문서도 **「0 개」** 로 들린다. 너무 큰 숫자는 **무엇이 불릴지 정해져 있지 않다.** → **실패를 말할 자리가 없다**
- **`strtol` 은 숫자와 함께 「여기까지 읽었다」는 책갈피(`endptr`)를 꽂아 준다** — 책갈피가 첫 글자에 있으면 **숫자가 없었다**, 끝에 있지 않으면 **뒤에 뭔가 남았다.** 너무 크면 **최댓값을 부르고 메모(`errno = ERANGE`)를 남긴다.** → **실패를 가르는 두 표시**
- **`qsort` 비교자는 「누가 앞이냐」만 대답하면 된다** — 음수 · 0 · 양수. **거리를 재서(`a - b`) 대답하면** 거리가 자(`int`)를 넘을 때 **부호가 뒤집힌다.** → **부호만 돌려라**
- **`bsearch` 는 「줄이 서 있다」고 믿고 반씩 건너뛴다** — 줄이 엉망이면 **있는 사람도 못 찾는다.** → **전제를 어기면 UB**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 막혀도 말 안 함 | `atoi` — 오류 때 `errno` 도 안 건드려도 된다 | ★★★ `"abc"` · `""` · `"0"` 이 전부 `0` |
| 책갈피 | `endptr` — 「소비」·「남음」 | ★★★ `"42abc"` 는 소비 2 · 남음 3 |
| 최댓값 + 메모 | `LONG_MAX` + `ERANGE` | ★★ `9223372036854775807` · `ERANGE` |
| 거리를 재서 대답 | `return a - b;`(35번 형제) · `return d;`(`long long` → `int`) | ★★ `0 2 3 2147483647 -2147483647 -1` |
| 줄이 서 있다고 믿기 | `bsearch` 의 전제 | ★★ 다섯 중 **셋을 못 찾음** |

```text
   strtol(s, &end, 10) 이 끝난 뒤 호출자가 보는 것

   end == s                  -> 숫자가 하나도 없었다        ("abc", "", "  ")
   *end != '\0'              -> 뒤에 글자가 남았다           ("42abc", "42 ")
   errno == ERANGE           -> 범위 밖 (값은 LONG_MAX/MIN) ("999…")
   셋 다 아니면               -> 성공

   atoi(s) 가 끝난 뒤 호출자가 보는 것

   int 하나.                  -> 위 넷을 가를 방법이 없다
```

- ★★★ **이 주제의 본체는 「표준」 칸과 「UB」 칸의 경계**다 — `strtol` 의 `endptr`·`ERANGE` · `qsort`/`bsearch` 의 인자 규칙이 **표준**이고, **`atoi` 의 넘침 · 일관되지 않은 비교자 · 정렬 안 된 `bsearch`** 가 **UB** 다.
- ★★ **「구현」 칸** — glibc `qsort` 의 안정성 · 이 판의 `strtol` 이 `-std` 에 따라 **다른 함수로 링크되는 것**.

> **`strtol(s, &end, base)`** — `s` 의 앞 공백을 건너뛰고 **주어(숫자 모양)** 를 `long` 으로 읽는다. 읽고 난 자리를 `*end` 에 남긴다. 넘치면 `LONG_MAX`/`LONG_MIN` + `errno = ERANGE`.\
> 예: `errno = 0; long v = strtol(s, &end, 10);`.

> **`qsort(base, n, size, cmp)`** — `cmp(a, b)` 가 **음수 · 0 · 양수**로 순서를 말하면 정렬한다. 비교 결과가 **전체 순서를 이뤄야** 한다.\
> 예: `qsort(v, n, sizeof v[0], by_int);`.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`atoi` 와 `strtol` 은 실패를 어떻게 다르게 다루나** — 숫자 없음 · 뒤에 남은 글자 · 범위 밖 · 진법.
2. ★★★ **`qsort` 비교자는 무엇을 지켜야 하고, 어겼을 때 누가 보나** — 넘침 · 좁히기 · 서명.
3. ★★ **`qsort`·`bsearch` 가 약속하지 않는 것은 무엇인가** — 안정성 · 정렬 안 된 입력.

## 동작 방식

### (1) ★★★ 변환 격자 — 입력 열 × `atoi` · `strtol`

**언제 쓰나** — 설정 파일 · 명령행 인자 · 네트워크 입력의 숫자를 읽을 때. ★★★ **이 편의 본체**다.

```c
/* s51a.c */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *ename(int e) { return e == 0 ? "0" : e == ERANGE ? "ERANGE" : e == EINVAL ? "EINVAL" : "other"; }

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    const char *s = argv[1];
    int base = atoi(argv[2]);
    char *end;
    errno = 0;
    long v = strtol(s, &end, base);
    int e = errno;
    /* 필드: strtol 값 · 소비한 글자 수 · errno · 남은 글자 수 */
    printf("%ld\x1f%d\x1f%s\x1f%zu", v, (int)(end - s), ename(e), strlen(end));
    if (argc > 3) printf("\x1f%d", atoi(s));
    printf("\n");
    return 0;
}
```

```text
===== 문자열 → 정수 — 입력 10 × (atoi · strtol+endptr+errno) (exit=0) =====
입력                     | atoi         | strtol 값              | 소비 | errno  | 남음 | strtol 이 알린 것
"42"                     | 42           | 42                     | 2    | 0      | 0    | 성공
"0"                      | 0            | 0                      | 1    | 0      | 0    | 성공
"42abc"                  | 42           | 42                     | 2    | 0      | 3    | 뒤에 남은 글자
"abc"                    | 0            | 0                      | 0    | 0      | 3    | 숫자 없음
""                       | 0            | 0                      | 0    | 0      | 0    | 숫자 없음
"  42"                   | 42           | 42                     | 4    | 0      | 0    | 성공
"42 "                    | 42           | 42                     | 2    | 0      | 1    | 뒤에 남은 글자
"99999999999999999999"   | UB — 싣지 않음 | 9223372036854775807    | 20   | ERANGE | 0    | 범위 밖
"-0x1A"                  | 0            | 0                      | 2    | 0      | 3    | 뒤에 남은 글자
"08"                     | 8            | 8                      | 2    | 0      | 0    | 성공
(base 10 · 소비 = endptr - s · 남음 = strlen(endptr))
strtol 이 성공이 아니라고 알린 입력 6 / 10 — atoi 는 그 6 개를 성공과 가를 수단이 없다
```

```text
   "42abc" 를 strtol 로 읽으면 (base 10)

   4  2  a  b  c  \0
   ^     ^
   s     end          값 42 · 소비 2 · 남음 3  -> "뒤에 남은 글자"

   "abc"
   a  b  c  \0
   ^
   s = end            값 0  · 소비 0           -> "숫자 없음" (표준: end 에 nptr 을 남긴다)
```

그림 해설 (한 단계씩):

- ★★★ **`atoi` 칸을 보면 `"0"` · `"abc"` · `""` · `"-0x1A"` 이 전부 `0`** 이고 `"42"` · `"42abc"` · `"  42"` · `"42 "` 가 전부 `42` 다. **정상 입력과 틀린 입력이 같은 값을 낸다** — 호출자는 가를 수가 없다.
- ★★★ **`"99999999999999999999"` 의 `atoi` 칸은 싣지 않았다** — 표준이 「결과를 표현할 수 없으면 **UB**」라고 적는다. 같은 입력에서 `strtol` 은 **`LONG_MAX` + `ERANGE`** 로 **정해진** 답을 낸다.
- ★★ **`strtol` 이 가르는 신호는 셋** — `소비 0`(숫자 없음) · `남음 > 0`(찌꺼기) · `ERANGE`(범위 밖). 격자의 분류 열은 **스크립트가 이 셋으로 계산**했다.
- ★★ **`"  42"` 는 성공**이다 — 앞 공백은 **주어 앞의 공백**으로 먹는다(소비 4). **`"42 "` 는 뒤에 1 글자가 남는다** — 뒤 공백은 안 먹는다. 앞뒤가 비대칭이다.
- ★★ **`"-0x1A"` 를 base 10 으로 읽으면 `0`**(소비 2 — `-0` 까지) · **`"08"` 은 base 10 에서 `8`** 이다 — 진법이 결과를 바꾼다((2)).

비용 — **`strtol` 은 세 줄이 더 든다**(`errno = 0` · `endptr` 비교 · `ERANGE` 확인). 그 세 줄이 곧 「실패를 안다」의 값이다.

### (2) ★★ 진법 접두 — `-std=c17` 과 `-std=c2x` 가 다른 함수를 부른다

**언제 쓰나** — base 0(자동 판별)이나 base 2 로 읽을 때.

```text
===== 진법 접두 — 입력 5 × base 4 × -std 2 (gcc · glibc) (exit=0) =====
입력     | base | -std=c17 값/소비   | -std=c2x 값/소비
"0b101"  | 0    | 0/1                | 5/5  <-
"0b101"  | 2    | 0/1                | 5/5  <-
"0b101"  | 8    | 0/1                | 0/1
"0b101"  | 16   | 45313/5            | 45313/5
"0B11"   | 0    | 0/1                | 3/4  <-
"0B11"   | 2    | 0/1                | 3/4  <-
"0B11"   | 8    | 0/1                | 0/1
"0B11"   | 16   | 2833/4             | 2833/4
"0x1A"   | 0    | 26/4               | 26/4
"0x1A"   | 2    | 0/1                | 0/1
"0x1A"   | 8    | 0/1                | 0/1
"0x1A"   | 16   | 26/4               | 26/4
"08"     | 0    | 0/1                | 0/1
"08"     | 2    | 0/1                | 0/1
"08"     | 8    | 0/1                | 0/1
"08"     | 16   | 8/2                | 8/2
"010"    | 0    | 8/3                | 8/3
"010"    | 2    | 2/3                | 2/3
"010"    | 8    | 8/3                | 8/3
"010"    | 16   | 16/3               | 16/3
c17 과 c2x 가 갈린 칸 4 / 20
```

```text
===== gcc -std=c17 -O0 s51a.c -o x17 && gcc -std=c2x -O0 s51a.c -o x2x && nm -u x17 x2x | grep -E '^x|strtol' (exit=0) =====
x17:
                 U strtol@GLIBC_2.2.5
x2x:
                 U __isoc23_strtol@GLIBC_2.38
```

- ★★★ **스무 칸 중 넷이 갈렸다** — 전부 **`0b`/`0B` 접두 × base 0·2** 다. `-std=c17` 은 `0` 을 읽고 `b` 에서 멈추고(`0/1`), `-std=c2x` 는 `0b101` 을 **5** 로 읽는다. C23 이 base 2 에 `0b` 접두를 허용했기 때문이다(표준 문장).
- ★★★ **소스는 한 글자도 같은데 링크된 심볼이 다르다** — `x17` 은 `strtol@GLIBC_2.2.5`, `x2x` 는 **`__isoc23_strtol@GLIBC_2.38`**. glibc 헤더가 `-std` 를 보고 `strtol` 을 **다른 함수로 바꿔 끼웠다.** 같은 머신에서도 **컴파일 옵션이 런타임 동작을 고른다.**
- ★★ **`"0b101"` 을 base 16 으로 읽으면 `45313`**(`0xb101`) — 두 판 다 같다. `b` 가 16진 숫자이기 때문이다. **`0x` 는 base 16 의 접두지만 `0b` 는 base 16 의 접두가 아니다.**
- ★★ **`"08"` 을 base 0 으로 읽으면 `0`, 소비 1** — `0` 으로 시작하면 8진이고 `8` 은 8진 숫자가 아니라 거기서 멈춘다. **`errno` 는 0** 이다 — `endptr` 을 안 보면 **「08 → 0」이 성공으로 지나간다.**
- ★ **`"010"` 은 base 0 에서 8** — 8진이다. 사람이 쓴 설정값을 base 0 으로 읽으면 **앞의 0 하나가 값을 바꾼다.**

### (3) ★★★ 비교자 넷 — 틀린 둘은 대부분의 창에서 조용하다

**언제 쓰나** — `qsort` 비교자를 **짧게** 쓰고 싶을 때.

```c
/* s51c.c */
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

static int by_wide(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    long long d = (long long)a - b;
    return d;
}

static int by_diff(const void *pa, const void *pb) {
    double a = *(const double *)pa, b = *(const double *)pb;
    return a - b;
}

static int by_rel_i(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static int by_rel_d(const void *pa, const void *pb) {
    double a = *(const double *)pa, b = *(const double *)pb;
    return (a > b) - (a < b);
}

int main(void) {
    int v[] = { 3, INT_MAX, -1, 0, INT_MIN + 1, 2 }, w[6];
    double x[] = { 0.5, 0.25, 0.75, 0.125 }, y[4];
    size_t n = sizeof v / sizeof v[0];
    for (size_t k = 0; k < n; k++) w[k] = v[k];
    for (size_t k = 0; k < 4; k++) y[k] = x[k];
    qsort(v, n, sizeof v[0], by_wide);
    qsort(w, n, sizeof w[0], by_rel_i);
    qsort(x, 4, sizeof x[0], by_diff);
    qsort(y, 4, sizeof y[0], by_rel_d);
    printf("by_wide  :"); for (size_t k = 0; k < n; k++) printf(" %d", v[k]); printf("\n");
    printf("by_rel_i :"); for (size_t k = 0; k < n; k++) printf(" %d", w[k]); printf("\n");
    printf("by_diff  :"); for (size_t k = 0; k < 4; k++) printf(" %g", x[k]); printf("\n");
    printf("by_rel_d :"); for (size_t k = 0; k < 4; k++) printf(" %g", y[k]); printf("\n");
    return 0;
}
```

```text
===== 틀린 비교자 둘 · 옳은 비교자 둘 — sanitizer 3 벌 (-std=c17 -Wall -Wextra -pedantic -O0 -g) (exit=0) =====
--- gcc -fsanitize=undefined (경고 0 · runtime error 0줄)
by_wide  : 0 2 3 2147483647 -2147483647 -1
by_rel_i : -2147483647 -1 0 2 3 2147483647
by_diff  : 0.5 0.25 0.75 0.125
by_rel_d : 0.125 0.25 0.5 0.75
--- clang -fsanitize=undefined (경고 0 · runtime error 0줄)
by_wide  : 0 2 3 2147483647 -2147483647 -1
by_rel_i : -2147483647 -1 0 2 3 2147483647
by_diff  : 0.5 0.25 0.75 0.125
by_rel_d : 0.125 0.25 0.5 0.75
--- clang -fsanitize=undefined,implicit-conversion (경고 0 · runtime error 1줄)
by_wide  : 0 2 3 2147483647 -2147483647 -1
by_rel_i : -2147483647 -1 0 2 3 2147483647
by_diff  : 0.5 0.25 0.75 0.125
by_rel_d : 0.125 0.25 0.5 0.75
```

```text
===== clang -std=c17 -O0 -g -fsanitize=undefined,implicit-conversion -ffile-prefix-map="$PWD"=. s51c.c -o x && ./x 2>&1 >/dev/null (exit=0) =====
s51c.c:8:12: runtime error: implicit conversion from type 'long long' of value 2147483648 (64-bit, signed) to type 'int' changed the value to -2147483648 (32-bit, signed)
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior s51c.c:8:12 
```

```text
   by_wide(INT_MAX, -1)   d = 2147483647 - (-1) = 2147483648   (long long — 넘치지 않는다)
                          return d;  -> int 로 바뀐다          값이 안 들어간다 -> 이 판: -2147483648
                          "INT_MAX 가 -1 보다 작다"로 읽힌다

   by_diff(0.5, 0.25)     a - b = 0.25   -> int 로 바뀐다 -> 0     "같다"로 읽힌다
                          차이가 1 보다 작은 쌍은 전부 "같다"
```

- ★★★ **`by_wide` 는 세 벌 다 틀린 순서**(`0 2 3 2147483647 -2147483647 -1`)이고 **`by_diff` 는 아예 안 움직였다**(원래 순서 `0.5 0.25 0.75 0.125` 그대로 — 모든 쌍이 「같다」).
- ★★★ **UBSan 기본 묶음은 두 벌 다 0 줄**이다 — `by_wide` 의 `long long` → `int` 는 **넘침이 아니라 변환**이고, 범위 밖 정수 변환은 **UB 가 아니라 구현 정의**(C17 까지 — 결과가 구현 정의이거나 신호)다. `by_diff` 의 `double` → `int` 는 **범위 안이라 적법**하다(소수부를 버릴 뿐).
- ★★ **`implicit-conversion` 을 켜야 `by_wide` 한 줄이 나온다** — `s51c.c:8:12` · `changed the value to -2147483648`. ★ **그 리포트의 `SUMMARY` 가 `undefined-behavior` 라고 적지만 이 변환은 UB 가 아니다** — 검사기 이름표를 근거로 쓰지 마라.
- ★★★ **`by_diff` 는 어떤 창도 말하지 않았다** — 경고 0 · 세 sanitizer 0 줄.
- ★★ **그러면 틀린 비교자는 UB 가 아닌가** — 표준은 비교 결과가 **전체 순서를 이뤄야 한다(shall)** 고 적고, 제약 밖의 「shall」을 어기면 UB 다. **`by_wide` 는 어겼다** — `-1 < 0`, `0 < INT_MAX` 인데 `INT_MAX < -1` 이라 **순환**이다. ★ **`by_diff` 는 이 데이터에서는 어기지 않았다** — 네 값의 차이가 전부 1 보다 작아 **모든 쌍이 「같다」**(모순 없는 순서)이고, 그래서 결과 순서는 **미명시**(같은 원소의 순서)일 뿐이다. 차이가 1 이상인 쌍이 섞이면 「a≈b, b≈c 인데 a<c」가 되어 **그때부터 UB** 다(★ 그 데이터는 **던지지 않았다** — 표준 문장에서 읽은 것이다).
- ★ **`return a - b` 의 부호 있는 넘침**(UBSan 이 잡는 쪽)은 [35번 형제](../35-function-pointers-and-callback-tables/) (4)절이 `INT_MIN` 입력으로 쟀다 — `signed integer overflow: -2147483648 - 1`.

비용 — **`(a > b) - (a < b)` 는 넘칠 수도 좁혀질 수도 없다.** 두 옳은 비교자(`by_rel_i`·`by_rel_d`)가 세 벌 다 맞게 정렬했다.

### (4) ★★★ 서명이 다른 비교자 — 포인터 매개변수는 봐준다

**언제 쓰나** — `int cmp(const int *, const int *)` 로 쓰고 **캐스트로 `qsort` 에 넘기고** 싶을 때.

```c
/* s51d.c */
#include <stdio.h>
#include <stdlib.h>

typedef int (*Cmp)(const void *, const void *);

static int by_int(const int *a, const int *b) { return (*a > *b) - (*a < *b); }
static int by_two(int a, int b) { return (a > b) - (a < b); }

int main(void) {
    int v[] = { 3, 1, 2 };
    qsort(v, 3, sizeof v[0], (Cmp)by_int);
    printf("%d %d %d\n", v[0], v[1], v[2]);
    Cmp other = (Cmp)by_two;
    (void)other;
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s51d.c -o /dev/null (cc exit=0) =====
s51d.c: In function 'main':
s51d.c:13:17: warning: cast between incompatible function types from 'int (*)(int,  int)' to 'int (*)(const void *, const void *)' [-Wcast-function-type]
   13 |     Cmp other = (Cmp)by_two;
      |                 ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s51d.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wcast-function-type -c s51d.c -o /dev/null (cc exit=0) =====
s51d.c:11:30: warning: cast from 'int (*)(const int *, const int *)' to 'Cmp' (aka 'int (*)(const void *, const void *)') converts to incompatible function type [-Wcast-function-type-strict]
   11 |     qsort(v, 3, sizeof v[0], (Cmp)by_int);
      |                              ^~~~~~~~~~~
s51d.c:13:17: warning: cast from 'int (*)(int, int)' to 'Cmp' (aka 'int (*)(const void *, const void *)') converts to incompatible function type [-Wcast-function-type-strict]
   13 |     Cmp other = (Cmp)by_two;
      |                 ^~~~~~~~~~~
2 warnings generated.
```

```text
===== clang -std=c17 -O0 -g -fsanitize=function -ffile-prefix-map="$PWD"=. s51d.c -o x && ./x (exit=0) =====
1 2 3
```

```text
                         (Cmp)by_int                      (Cmp)by_two
                         const int* 둘 -> const void* 둘   int 둘 -> const void* 둘
   gcc -Wall -Wextra     0                                -Wcast-function-type
   clang -Wall -Wextra   0                                0
   clang + -Wcast-function-type
                         -Wcast-function-type-strict      -Wcast-function-type-strict
   clang -fsanitize=function (qsort 안의 호출)
                         0 — "1 2 3"
```

- ★★★ **gcc 는 `by_int` 캐스트에 경고하지 않는다** — `-Wcast-function-type` 은 **포인터 매개변수끼리는 서로 맞는 것으로 친다**(`int` ↔ `const void *` 인 `by_two` 만 짚었다). `qsort` 에 가장 흔한 실수가 **정확히 그 봐주는 자리**다.
- ★★ **clang 은 `-Wall -Wextra` 에서 0 건**, `-Wcast-function-type` 을 **따로** 주면 **`-Wcast-function-type-strict`** 이름으로 둘 다 짚는다.
- ★★★ **`clang -fsanitize=function` 은 침묵하고 `1 2 3`** — 캐스트된 포인터로 부르는 곳은 **glibc 의 `qsort` 안**이고, 그 코드는 sanitizer 로 컴파일되지 않았다. [35번 형제](../35-function-pointers-and-callback-tables/) (5)절에서 같은 sanitizer 가 잡은 것은 **호출이 내 소스에 있었기 때문**이다.
- ★★ **여전히 UB 다** — 호환되지 않는 타입으로 함수를 부르는 것. x86-64 에서 `const int *` 와 `const void *` 가 같은 레지스터로 전달돼 **이 판에서는 맞게 정렬됐을 뿐**이다.

비용 — **비교자는 처음부터 `const void *` 둘을 받게 쓰고 안에서 바꾼다.** 캐스트가 필요 없어야 정상이다.

### (5) ★★ `qsort` 는 안정 정렬인가 — 제5의 상태

**언제 쓰나** — 「같은 키끼리는 원래 순서가 유지되겠지」를 믿고 싶을 때.

```c
/* s51e.c */
#include <stdio.h>
#include <stdlib.h>

struct R { int key; int seq; };

static int by_key(const void *pa, const void *pb) {
    const struct R *a = pa, *b = pb;
    return (a->key > b->key) - (a->key < b->key);
}

int main(int argc, char **argv) {
    size_t n = argc > 1 ? strtoul(argv[1], NULL, 10) : 10;
    struct R *v = malloc(n * sizeof *v);
    if (!v) { printf("n=%zu malloc NULL\n", n); return 1; }
    unsigned s = 12345;
    for (size_t i = 0; i < n; i++) {
        s = s * 1103515245u + 12345u;
        v[i].key = (int)((s >> 16) % 4);
        v[i].seq = (int)i;
    }
    qsort(v, n, sizeof v[0], by_key);
    size_t order = 0, inv = 0;
    for (size_t i = 1; i < n; i++) {
        if (v[i - 1].key > v[i].key) order++;
        if (v[i - 1].key == v[i].key && v[i - 1].seq > v[i].seq) inv++;
    }
    printf("n=%zu  key order breaks=%zu  seq inversions among equal keys=%zu\n", n, order, inv);
    free(v);
    return 0;
}
```

```text
===== 같은 비교자 · 같은 입력 — 크기 3 × 주소 공간 한도 2 (gcc -O2 · glibc qsort) (exit=0) =====
ulimit 없음         | n=10  key order breaks=0  seq inversions among equal keys=0
ulimit 없음         | n=1000  key order breaks=0  seq inversions among equal keys=0
ulimit 없음         | n=1000000  key order breaks=0  seq inversions among equal keys=0
ulimit -v 15000     | n=10  key order breaks=0  seq inversions among equal keys=0
ulimit -v 15000     | n=1000  key order breaks=0  seq inversions among equal keys=0
ulimit -v 15000     | n=1000000  key order breaks=0  seq inversions among equal keys=580403
```

```text
===== 주소 공간 한도 다섯 값 — n=1000000 (gcc -O2) (exit=0) =====
ulimit -v 10000  | n=1000000 malloc NULL
ulimit -v 12000  | n=1000000  key order breaks=0  seq inversions among equal keys=580403
ulimit -v 15000  | n=1000000  key order breaks=0  seq inversions among equal keys=580403
ulimit -v 18000  | n=1000000  key order breaks=0  seq inversions among equal keys=580403
ulimit -v 20000  | n=1000000  key order breaks=0  seq inversions among equal keys=0
```

- ★★★ **보통 실행 세 줄은 뒤집힘 0** — 이 판의 glibc `qsort` 는 **이 크기들에서 안정적으로 보였다.** 백만 개까지 그랬다.
- ★★★ **`ulimit -v 15000` 에서 백만 개만 `580403`** — 같은 바이너리 · 같은 입력 · 같은 비교자다. **정렬은 맞고(`key order breaks=0`) 같은 키 사이 순서만 뒤집혔다.** glibc 가 **임시 버퍼를 못 잡자 다른 경로**로 정렬한 것이다(버퍼가 작은 10 · 1000 은 한도 아래에서도 0). 한도를 다섯 값으로 바꿔 보면 **너무 낮으면 배열 자체를 못 잡고(`malloc NULL`) · 중간은 뒤집히고 · 넉넉하면 0** 이다(둘째 블록).
- ★★ **표준은 안정성을 약속하지 않는다** — 오히려 「**같다고 비교되는 두 원소의 순서는 미명시**」다. 「보통 실행에서 안정적」은 **이 glibc 의, 메모리가 넉넉할 때의 관찰**이다.
- ★ 안정 정렬이 필요하면 **키에 원래 위치를 더해 비교**한다(`seq` 를 두 번째 키로).

### (6) ★★ 정렬 안 된 배열에 `bsearch`

**언제 쓰나** — 「`bsearch` 는 못 찾으면 `NULL` 을 줄 테니 정렬은 선택이다」라고 생각할 때.

```c
/* s51f.c */
#include <stdio.h>
#include <stdlib.h>

static int by_int(const void *pa, const void *pb) {
    int a = *(const int *)pa, b = *(const int *)pb;
    return (a > b) - (a < b);
}

static void probe(const char *tag, const int *v, size_t n) {
    printf("%-8s", tag);
    for (int key = 1; key <= 5; key++) {
        const int *hit = bsearch(&key, v, n, sizeof v[0], by_int);
        printf("  %d:%s", key, hit ? "hit" : "NULL");
    }
    printf("\n");
}

int main(void) {
    int a[] = { 5, 1, 4, 2, 3 };
    probe("as-is", a, 5);
    qsort(a, 5, sizeof a[0], by_int);
    probe("sorted", a, 5);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s51f.c -o x ; ./x (cc exit=0 · run exit=0) =====
as-is     1:hit  2:NULL  3:NULL  4:hit  5:NULL
sorted    1:hit  2:hit  3:hit  4:hit  5:hit
```

- ★★ **`as-is` 는 다섯 중 셋을 못 찾았다** — 1 · 4 는 `hit`, 2 · 3 · 5 는 `NULL`. 배열 안에 **분명히 있는데** `NULL` 이다. `sorted` 는 다섯 다 `hit`.
- ★★★ **이것은 「못 찾음」이 아니라 UB 의 한 모습이다** — 표준은 배열이 「키보다 작은 것 · 같은 것 · 큰 것 **순서로 이뤄져야 한다(shall)**」고 적고, 그 「shall」은 제약 밖이라 **어기면 UB** 다. 이 판에서 `NULL` 이 나온 것은 **glibc 의 이분 탐색이 그렇게 걸었을 뿐**이다.

## 문법 — 형태와 규칙

### 형태

```c
/* s51a.c */
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *ename(int e) { return e == 0 ? "0" : e == ERANGE ? "ERANGE" : e == EINVAL ? "EINVAL" : "other"; }

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    const char *s = argv[1];
    int base = atoi(argv[2]);
    char *end;
    errno = 0;
    long v = strtol(s, &end, base);
    int e = errno;
    /* 필드: strtol 값 · 소비한 글자 수 · errno · 남은 글자 수 */
    printf("%ld\x1f%d\x1f%s\x1f%zu", v, (int)(end - s), ename(e), strlen(end));
    if (argc > 3) printf("\x1f%d", atoi(s));
    printf("\n");
    return 0;
}
```

- `errno = 0` → `strtol(s, &end, base)` → **`end == s`?** → **`*end != '\0'`?** → **`errno == ERANGE`?** 순서로 본다.
- `int` 가 필요하면 **`INT_MIN <= v && v <= INT_MAX`** 를 한 번 더 본다 — `strtol` 은 `long` 의 범위만 안다.
- 비교자는 `int f(const void *, const void *)` — 안에서 원래 타입으로 바꾸고 **`(a > b) - (a < b)`**.

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 도구 | 층 | 절 |
|---|---|---|---|
| `atoi("99999999999999999999")` | 경고 0 · 도구 0 | ★★★ UB | (1) |
| `atoi(s)` 로 입력 검증 | 경고 0 | 적법 — 실패를 모를 뿐 | (1) |
| `return a - b;`(`int`) | UBSan `signed-integer-overflow` | ★★★ UB | 35번 형제 (4) |
| `return d;`(`long long` → `int`) | UBSan 은 `implicit-conversion` 에서만 | ★★ 구현 정의 변환 + 순서 불일치(UB) | (3) |
| `return a - b;`(`double` → `int`) | 전부 0 | ★★ 이 데이터는 「전부 같다」(미명시 순서) · 차이 1 이상이 섞이면 순서 불일치(UB) | (3) |
| `(Cmp)by_int`(`const int *` 매개변수) | gcc 0 · clang `-Wcast-function-type-strict` · sanitizer 0 | ★★★ UB | (4) |
| 정렬 안 된 배열에 `bsearch` | 전부 0 | ★★ UB(「shall」 위반) | (6) |

### 규칙 불릿

- ★★★ **숫자 입력은 `strtol` 로 읽고 세 신호를 전부 본다.** `atoi` 는 **이미 검증된 문자열**에만.
- ★★ **`errno` 는 부르기 전에 0.** `strtol` 은 성공할 때 `errno` 를 **안 건드린다** — 앞의 값이 남아 있으면 오판한다([목록의 **46번 주제**](../46-errno-and-error-return-conventions/)).
- ★★ **base 는 명시한다.** base 0 은 `08` · `010` · (C23 에서) `0b` 를 **알아서** 해석한다.
- ★★★ **비교자는 부호만 — 뺄셈도 좁히기도 쓰지 않는다.**
- ★★ **안정성이 필요하면 스스로 만든다.** `bsearch` 는 **정렬된 배열에만**.

## 어디서 틀리나

### 1. ★★★ 「`atoi` 가 0 을 돌려주면 입력이 `"0"` 이었다」

`"abc"` · `""` · `"-0x1A"` 도 0 이다((1)).

### 2. ★★★ 「`strtol` 이 `errno` 를 안 세웠으니 성공이다」

`"42abc"` · `"08"`(base 0) 은 **`errno` 0 인데 끝까지 못 읽었다**((1)·(2)). **`endptr` 을 봐야 한다.**

### 3. ★★ 「같은 소스면 같은 `strtol` 이다」

**`-std` 가 링크 심볼을 바꾼다** — `0b101` 이 0 과 5 로 갈렸다((2)).

### 4. ★★★ 「UBSan 이 조용하니 비교자는 맞다」

`by_diff` 는 **모든 창이 조용한데 정렬이 안 된다**((3)).

### 5. ★★★ 「gcc 가 경고를 안 냈으니 캐스트는 괜찮다」

gcc 는 **포인터 매개변수끼리는 봐준다** · `-fsanitize=function` 은 **`qsort` 안을 못 본다**((4)).

### 6. ★★ 「glibc `qsort` 는 병합 정렬이라 안정적이다」

**메모리가 모자라면 아니다** — 같은 입력에서 `580403` 쌍이 뒤집혔다((5)). 표준은 약속하지 않는다.

### 7. ★ 「`bsearch` 가 `NULL` 이면 없는 것이다」

**정렬이 전제**다 — 있는 원소 셋을 못 찾았다((6)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.

| 층 | 뜻 | 이 주제에서 | 근거 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | `strtol` 의 공백·주어·나머지 분해 · `endptr` · `LONG_MAX`+`ERANGE` · 「변환 없음 → 0, `end = s`」 · C23 `0b` · `qsort`/`bsearch` 의 인자 규칙 | 변환 격자 · 진법 격자 |
| ★★ **구현 정의** | 문서화 의무 | 범위 밖 정수 변환의 값(C17) · `atoi` 가 오류 때 `errno` 를 세우나 | `by_wide` 의 `-2147483648` |
| ★★ **glibc·컴파일러 구현** | 이 판이 한 것 | ★★ **`-std=c2x` → `__isoc23_strtol`** · `qsort` 의 경로(메모리가 넉넉하면 안정) · `bsearch` 의 걸음 · gcc `-Wcast-function-type` 의 포인터 관용 · clang `-strict` | `nm -u` · `ulimit` 격자 · 경고 블록 |
| **미명시** | 몇 가지 중 하나 | ★★ **같다고 비교되는 원소의 순서**(표준 — 「their order in the resulting sorted array is unspecified」) · `bsearch` 가 같은 원소 여럿 중 무엇을 주나 | `580403` · `by_diff` 의 제자리 |
| ★★★ **UB** | 아무 일이나 | ★★★ **`atoi` 넘침** · 일관되지 않은 비교자 · 서명이 다른 비교자 호출 · 정렬 안 된 `bsearch` · `a - b` 넘침 | 싣지 않음 · `by_wide` · `(Cmp)by_int` · `as-is` 줄 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 이 편의 사례 | 무엇이 봤나 | 무엇이 못 봤나 |
|---|---|---|---|
| UB | `atoi` 넘침 | **아무 도구도** | 전부 |
| UB | `(Cmp)by_int` | clang `-Wcast-function-type`(따로 줘야) | gcc 경고 · `-fsanitize=function`(호출이 glibc 안) |
| 틀린 결과(이 데이터는 미명시) | `by_diff` | **아무 도구도** | 전부 |
| 구현 정의 | `by_wide` 좁히기 | UBSan `implicit-conversion` | UBSan 기본 묶음 · 경고 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓴다 | 안 쓴다 |
|---|---|---|
| 외부 입력 숫자 | ★★★ **`strtol` + 세 신호** | `atoi` · `sscanf("%d")`(넘침이 UB) |
| 이미 검증된 숫자 문자열 | `atoi`(짧다) | — |
| `int` 결과 | `strtol` 뒤 **범위 확인** | `(int)strtol(…)` 한 줄 |
| 정수 비교자 | `(a > b) - (a < b)` | `a - b` · `long long` 뺄셈을 `int` 로 |
| 부동소수 비교자 | `(a > b) - (a < b)`(NaN 이 없을 때) | `(int)(a - b)` |
| 같은 키의 원래 순서 | 두 번째 키 | `qsort` 의 관찰에 기대기 |
| 탐색 | 정렬된 배열의 `bsearch` | 정렬 안 된 배열 |

## 핵심 문장

1. ★★★ **`atoi` 는 실패를 말할 자리가 없다 — 이 판에서 `strtol` 이 알린 실패 여섯 중 `atoi` 가 가를 수 있는 것은 0 이다.**
2. ★★★ **`strtol` 의 실패 신호는 셋이다 — `end == s`, `*end != '\0'`, `errno == ERANGE`. `errno` 만 보면 둘을 놓친다.**
3. ★★ **`-std=c2x` 는 `strtol` 을 다른 함수로 링크한다 — 소스가 같아도 `0b101` 이 0 과 5 로 갈린다.**
4. ★★★ **비교자는 부호만 — 뺄셈 · 좁히기는 어떤 창도 못 보는 틀린 순서를 만든다.**
5. ★★ **`qsort` 의 안정성과 정렬 안 된 `bsearch` 는 표준이 약속하지 않는다 — 메모리 한도 하나로 안정성이 사라졌다.**

## 관련 자료

- [35번 형제 — 함수 포인터와 콜백 테이블](../35-function-pointers-and-callback-tables/) — ★★ `return a - b` 의 UBSan 전문 · 서명이 다른 함수 포인터(`int` → `long`)를 gcc 경고 · clang `-fsanitize=function` 이 나눠 잡는 것. 그쪽은 **콜백 일반**까지, 여기는 **`qsort` 가 부르는 비교자**부터.
- [`algorithm/03-quick-sort/`](../../../../cs/algorithm/03-quick-sort/) · [`algorithm/06-binary-search/`](../../../../cs/algorithm/06-binary-search/) — 알고리즘의 원리. 여기는 **API 계약**만.
- [목록의 **46번 주제**](../46-errno-and-error-return-conventions/) — `errno` 관례와 「언제 0 으로 두나」.
- [Go 갈래 11번 — `strconv`](../../../go/syntax/11-strings-strconv-bytes-and-unicode-utf8/) — ★ `strconv.Atoi` 는 `" 42"` · `"42 "` · `"0x2a"` · `""` 를 **전부 `invalid syntax` 에러**로 돌려준다(그쪽 실측). C 의 `strtol` 은 앞 공백을 먹고, `atoi` 는 에러 자체가 없다 — **실패를 값의 일부로 돌려주는 언어**와의 대비다.

## 용어 풀이

> **`endptr`** — `strtol` 이 「여기까지 읽었다」를 남기는 `char **` 인자. 첫 글자면 변환 없음, 끝(`'\0'`)이 아니면 찌꺼기.

> **주어(subject sequence)** — 표준의 용어. 앞 공백 뒤에서 **그 진법의 숫자 모양으로 읽을 수 있는 가장 긴 부분**.

> **`ERANGE`** — 결과가 범위 밖일 때 `strtol` 이 `errno` 에 넣는 값.

> **전체 순서(total ordering)** — 모든 쌍에 대해 「작다 · 같다 · 크다」가 **서로 모순 없이** 정해진 것. 「a≈b, b≈c 인데 a<c」는 전체 순서가 아니다.

> **안정 정렬(stable sort)** — 같다고 비교되는 원소들의 **원래 순서를 유지**하는 정렬.

> **`-Wcast-function-type-strict`** — clang 의 경고. **포인터 매개변수까지 엄격히** 비교해 함수 포인터 캐스트를 짚는다.

> **`__isoc23_strtol`** — glibc 가 `-std=c2x` 에서 `strtol` 대신 링크하는 C23 판 함수.

## 더 들어가면

- ★★ **`strtoul` 의 음수** — `"-1"` 을 `strtoul` 로 읽으면 **`ULONG_MAX`** 가 **에러 없이** 나온다(부호가 반환 타입에서 적용된다 — 표준 문장). ★ 이 편은 **던지지 않았다.**
- ★ **로케일** — 「C 로케일이 아니면 로케일 고유의 주어 형식을 더 받아도 된다」(표준). 이 편은 `LC_ALL=C` 로만 돌렸다.
- ★ **`qsort_s`/`bsearch_s`(부록 K)** — glibc 에 없다(★ 확인하지 않았다).

## 실행 환경

**기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 수 변환 함수 머리의 「**atof, atoi, atol, and atoll are not required to affect the value of … errno on an error. If the value of the result cannot be represented, the behavior is undefined.**」, `atoi` 의 「**Except for the behavior on error, they are equivalent to … (int)strtol(nptr, nullptr, 10)**」, `strtol` 의 세 부분 분해(공백 · 주어 · 나머지) · 「**no conversion … the value of nptr is stored in the object pointed to by endptr**」 · 「**LONG_MAX … and the value of the macro ERANGE is stored in errno**」 · 「**If the value of base is 2, the characters 0b or 0B may optionally precede**」, 검색·정렬 공통 절의 「**for qsort they shall define a total ordering**」, `qsort` 의 「**If two elements compare as equal, their order in the resulting sorted array is unspecified.**」, `bsearch` 의 「**The array shall consist of: all the elements that compare less than, … equal to, and … greater than the key object, in that order**」, 규범 절의 「**If a "shall" … requirement that appears outside of a constraint … is violated, the behavior is undefined**」를 **본문에서 직접 찾아 읽었다**)
★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값 · `errno` · 소비한 글자 수 · 경고 · sanitizer 리포트 · 링크 심볼은 전부 실행으로** 접지했다.
**실행 검증** — 이 문서의 모든 출력·진단은 「이 판」 절의 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`, 캡처 셸은 `LC_ALL=C`.\
★★ **블록은 전부 캡처 파일에서 조립했다.** 이 편의 **그림 4 · 덤프(캡처 블록) 15**.
**버전** — `atoi`·`strtol`·`qsort`·`bsearch` 는 **C89 부터**, `strtoll` 은 **C99 부터**. ★★ **C23** 이 `strtol` 에 **`0b` 접두**(base 0 · 2)를 더했다 — 이 판의 glibc 는 `-std=c2x` 에서만 그 판으로 링크한다((2)).
★★★ **경계** — **퀵 정렬 · 이분 탐색의 원리와 복잡도**는 [`algorithm/03-quick-sort/`](../../../../cs/algorithm/03-quick-sort/) · [`algorithm/06-binary-search/`](../../../../cs/algorithm/06-binary-search/)가 정본이다. 여기는 **표준 API 의 계약**만 본다.\
★★ **`return a - b` 비교자의 넘침 · 서명이 다른 함수 포인터 호출의 일반형**은 [35번 형제](../35-function-pointers-and-callback-tables/) (4)·(5)절이 정본이다(이 편은 **다시 재지 않고** 인용한다). **`errno` 관례**는 [목록의 **46번 주제**](../46-errno-and-error-return-conventions/)다.
선행 — [35번 형제](../35-function-pointers-and-callback-tables/) · [목록의 **46번 주제**](../46-errno-and-error-return-conventions/).
