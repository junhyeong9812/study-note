# c/syntax/51 — `<stdlib.h>` 변환 · `qsort` · `bsearch`: 「**`atoi` 에는 실패를 말할 자리가 없다 — `strtol` 의 `endptr` 와 `errno` 가 그 자리다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s51a.c` · `s51c.c`\~`s51f.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **본체 창은 변환 격자** — 입력 10 × 두 함수.
> ★★ **흔들리는 칸** — 없다. `ulimit` 칸은 **한도 값에 매인다**(선언).

## 이 파일이 다시 싣는 소스

★ 3번의 UBSan 리포트가 가리키는 줄을 여기서 대조한다(질문 파일의 소스와 같다).

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 변환 격자 — **`strtol` 이 성공이 아니라고 알린 입력 6 / 10 · `atoi` 는 그 여섯을 못 가른다 · 넘치는 입력의 `atoi` 는 UB** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`atoi` 는 값 하나만 돌려준다** — `"0"` 과 `"abc"`·`""`·`"-0x1A"` 가 같은 `0`, `"42"` 와 `"42abc"`·`"42 "` 가 같은 `42` 다. **정상과 실패가 한 값에 겹친다.**
- ★★★ **`"99999999999999999999"` 의 `atoi` 는 UB** — 표준 문장 「If the value of the result cannot be represented, the behavior is undefined.」 그래서 **값을 싣지 않았다.** 같은 입력의 `strtol` 은 `LONG_MAX` + `ERANGE` 로 **정해져 있다.**
- ★★ **`strtol` 의 세 신호** — 소비 0(숫자 없음: `"abc"` · `""`) · 남음 > 0(찌꺼기: `"42abc"` · `"42 "` · `"-0x1A"`) · `ERANGE`. `"  42"` 는 앞 공백을 먹어 **성공**, `"08"` 은 base 10 이라 **8 로 성공**이다.

### 2. 진법 접두와 `-std` — **갈린 칸 4 / 20 — 전부 `0b`/`0B` × base 0·2 · `"0b101"` base 16 은 `45313` · `"08"` base 0 은 소비 1** ★★

**출력**

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

**왜 그런가**

- ★★ **C23 이 base 2(와 base 0)에 `0b` 접두를 더했다** — `-std=c2x` 판은 `0b101` 을 5, `0B11` 을 3 으로 읽고, `-std=c17` 판은 `0` 까지만 읽는다(소비 1).
- ★★★ **소스가 같은데 링크 심볼이 다르다** — glibc 헤더가 `-std=c2x` 에서 `strtol` 을 **`__isoc23_strtol`** 로 바꿨다. 같은 소스 · 같은 컴파일러 · 옵션 하나.
- ★★ **`"0b101"` 의 base 16 은 `0xb101 = 45313`** — `b` 가 16진 숫자다(두 판 같음). **`"08"` 의 base 0 은 8진으로 읽다가 `8` 에서 멈춘다** — 값 0 · 소비 1 · `errno` 0.

### 3. 비교자 넷 — **`by_wide` 틀린 순서 · `by_diff` 제자리 · 옳은 둘은 정렬 · UBSan 은 `implicit-conversion` 판에서 `by_wide` 한 줄만** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`by_wide` 는 `long long` 차이를 `int` 로 좁힌다** — `INT_MAX - (-1) = 2147483648` 이 `int` 에 안 들어가 이 판에서 `-2147483648` 이 된다. 「`INT_MAX` 가 `-1` 보다 작다」가 되어 순서가 **순환**한다 — 표준의 「전체 순서여야 한다(shall)」 위반이라 **UB** 다.
- ★★ **`by_diff` 는 `double` 차이를 `int` 로 버린다** — 이 네 값은 차이가 전부 1 보다 작아 **모든 쌍이 0(「같다」)** 이다. 순서가 모순되지는 않아서 결과는 **미명시**(같은 원소의 순서)이고, 이 판은 **원래 순서 그대로** 두었다.
- ★★★ **UBSan 기본 묶음은 둘 다 0 줄** — 좁히기는 **구현 정의 변환**, 범위 안의 `double` → `int` 는 **적법**이라 「UB 검사기」가 볼 것이 없다. `implicit-conversion` 을 켜야 `s51c.c:8:12` 한 줄이 나오고, 그 리포트의 `SUMMARY` 가 `undefined-behavior` 라고 적는 것은 **이름표일 뿐**이다.
- ★ **경고 0** — 세 벌 다.

### 4. 서명이 다른 비교자 — **gcc 는 `by_two` 만 · clang 은 `-Wcast-function-type` 을 줘야 둘 다 · `-fsanitize=function` 은 침묵(`1 2 3`)** ★★★

**출력**

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

**왜 그런가**

- ★★★ **gcc 의 `-Wcast-function-type` 은 포인터 매개변수끼리를 맞는 것으로 친다** — `const int *` ↔ `const void *` 인 `by_int` 는 통과, `int` ↔ `const void *` 인 `by_two` 만 경고.
- ★★ **clang 은 `-Wall -Wextra` 에 이 경고가 없다** — `-Wcast-function-type` 을 **따로** 켜면 `-Wcast-function-type-strict` 로 둘 다 짚는다.
- ★★★ **`-fsanitize=function` 은 부르는 쪽을 계측한다** — 부르는 곳이 **glibc 의 `qsort`** 라 계측이 없다. 그래서 UB 인 호출이 **조용히 `1 2 3`** 을 냈다.

### 5. 안정성 — **보통 실행은 셋 다 0 · `ulimit -v 15000` 아래 백만 개만 `580403` · 「안정 정렬이다」는 말할 수 없다** ★★

**출력**

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

**왜 그런가**

- ★★★ **같은 바이너리 · 같은 입력에서 결과가 갈렸다** — 메모리가 넉넉하면 이 glibc 는 같은 키의 순서를 지켰고, 임시 버퍼를 못 잡는 한도에서는 **다른 경로**로 정렬해 뒤집었다. 정렬 자체(`key order breaks`)는 둘 다 맞다.
- ★★ **표준은 「같다고 비교되는 원소의 순서는 미명시」** 라고 적는다 — 안정성은 **약속이 아니라 이 판 · 이 메모리 상황의 관찰**이다.
- ★ 한도 다섯 값 — 너무 낮으면 배열부터 못 잡고, 넉넉하면 0 이다.

### 6. 정렬 안 된 배열에 `bsearch` — **`as-is` 는 1·4 만 `hit` · `sorted` 는 다섯 다 `hit`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s51f.c -o x ; ./x (cc exit=0 · run exit=0) =====
as-is     1:hit  2:NULL  3:NULL  4:hit  5:NULL
sorted    1:hit  2:hit  3:hit  4:hit  5:hit
```

**왜 그런가**

- ★★ **이분 탐색은 가운데를 보고 반을 버린다** — 정렬이 안 되어 있으면 **있는 원소가 버린 반에** 있을 수 있다. 2 · 3 · 5 가 그랬다.
- ★ 이 걸음은 **이 glibc 의 것**이다(9번 — 표준에서는 UB).

### 7. `atoi` 의 오류 동작 — **`errno` 를 건드리지 않아도 되고, 표현할 수 없으면 UB · 「오류 때를 빼면 `(int)strtol(nptr, nullptr, 10)`」** ★★

**왜 그런가**

- ★★ 수 변환 함수 머리 — 「atof, atoi, atol, and atoll are **not required to affect the value of … errno** on an error. If the value of the result cannot be represented, **the behavior is undefined**.」 1번 격자의 넘치는 입력은 **이 둘째 문장**에 걸려 값을 싣지 않았다.
- ★ `atoi` 절 — 「**Except for the behavior on error**, they are equivalent to … `(int)strtol(nptr, nullptr, 10)`」. 빠진 것은 **`endptr`(널) · 오류 때의 동작** — 곧 **실패를 알리는 두 통로가 둘 다 없다.**

### 8. `errno = 0` 과 `long` → `int` — **`strtol` 은 성공 때 `errno` 를 안 건드린다 · `strtol` 은 `long` 범위만 본다** ★★

**왜 그런가**

- ★★ **`errno` 는 성공 때 지워지지 않는다** — 앞선 다른 호출이 남긴 `ERANGE` 가 있으면 성공한 변환을 실패로 읽는다. 그래서 **부르기 직전에 0.**
- ★★ **`strtol` 의 `ERANGE` 는 `long` 의 범위**다 — 이 판의 `long` 은 64 비트라 `"3000000000"` 은 `ERANGE` 없이 성공한다(아래 블록 — 값 · 소비 10 · `errno` 0 · 남음 0). `int` 에 넣으려면 **`INT_MIN <= v && v <= INT_MAX`** 를 한 번 더 본다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s51a.c -o x && ./x 3000000000 10 | tr '\037' ' ' (exit=0) =====
3000000000 10 0 0
```

### 9. `bsearch` 의 전제 — **UB · 「shall consist of … in that order」 + 「shall 위반은 UB」** ★★

**왜 그런가**

- ★★ `bsearch` 절 — 「The array **shall** consist of: all the elements that compare less than, all the elements that compare equal to, and all the elements that compare greater than the key object, **in that order**.」
- ★★ 규범 절 — 「If a "shall" or "shall not" requirement that appears outside of a constraint … is violated, **the behavior is undefined**.」 그래서 6번의 `NULL` 은 「못 찾음」이라는 **정해진 답이 아니라** 이 판에서 나온 모습이다.

### 10. 35번 형제와 이어서 — **`a - b` 의 UBSan 전문 · 서명 캐스트(`int` → `long`)의 두 컴파일러 대비는 그쪽이 쟀다** ★★

**왜 그런가**

- [35번 형제](../35-function-pointers-and-callback-tables/) (4)절 — `cmp_sub` 가 `INT_MIN` 에서 **`signed integer overflow`** · 네 빌드 `sorted? no`. (5)절 — `int (*)(int)` 를 `int (*)(long)` 로 부르면 gcc 는 **경고**, clang 은 **`-fsanitize=function`** 이 잡는다.
- ★★ **이 편이 더한 칸** — ① **UBSan 이 못 보는 틀린 비교자 둘**(좁히기 · `double` 버림) ② **`qsort` 비교자의 전형적 캐스트**(포인터 매개변수)를 **gcc 경고도, `-fsanitize=function` 도 못 본다**는 것 — 35편의 두 창이 **둘 다 닫히는 자리**다.

### 11. 다섯 층과 네 번째 창 ★★★

**왜 그런가**

- **표준** — `strtol` 의 분해 · `endptr` · `ERANGE` · C23 `0b` · 인자 규칙.
- **구현 정의** — 범위 밖 정수 변환의 값 · `atoi` 가 오류 때 `errno` 를 세우는지.
- **glibc·컴파일러 구현** — `__isoc23_strtol` 링크 · `qsort` 의 경로 · `bsearch` 의 걸음 · 경고의 관용.
- **미명시** — 같은 원소의 순서.
- **UB** — `atoi` 넘침 · 순서 불일치 비교자 · 서명이 다른 비교자 호출 · 정렬 안 된 `bsearch`.
- ★★★ **네 번째 창 = 링크 심볼(`nm -u`)과 주소 공간 한도(`ulimit -v`).** 앞은 「**같은 이름의 함수가 정말 같은 함수인가**」, 뒤는 「**평소에 안 타는 경로에서도 같은가**」를 묻는다. 못 보는 것 — `nm` 은 **그 함수가 무엇을 다르게 하는지**를, `ulimit` 는 **어떤 알고리즘으로 갈아탔는지**를 말하지 않는다.

### 12. 경계와 다른 갈래 ★

**왜 그런가**

- **알고리즘** — [`algorithm/03-quick-sort/`](../../../../cs/algorithm/03-quick-sort/) · [`algorithm/06-binary-search/`](../../../../cs/algorithm/06-binary-search/).
- ★ **Go `strconv.Atoi`** — `" 42"` · `"42 "` 를 **둘 다 `invalid syntax` 에러**로 돌려준다([Go 갈래 11번](../../../go/syntax/11-strings-strconv-bytes-and-unicode-utf8/)의 실측). C 의 `strtol` 은 앞 공백을 먹고 뒤 공백은 「남음 1」로 알린다 — **엄격함이 기본값이냐, 호출자가 `endptr` 로 세우느냐**의 차이다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s51a.c` | ★★★ **변환 격자 6 / 10** · ★★ **진법 격자 4 / 20** · 링크 심볼 · `"3000000000"` | 빌드 6 · 실행 51 · `nm` 1 |
| `s51c.c` | ★★★ 비교자 격자 · UBSan 리포트 | 빌드 4 · 실행 4 |
| `s51d.c` | ★★★ 캐스트 경고 셋 · `-fsanitize=function` | 진단 3 · 실행 1 |
| `s51e.c` | ★★ 안정성 격자 · 한도 다섯 값 | 실행 11 |
| `s51f.c` | ★★ 정렬 안 된 `bsearch` | 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 이 편은 흔들린 칸이 없어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **2번의 링크 심볼** — glibc 2.38 이후의 헤더.
- ★★★ **5번 전부** — glibc `qsort` 의 구현과 한도 값.
- ★★ **3번의 `-2147483648` · 6번의 `hit`/`NULL` 패턴** — 이 판의 변환 · 이 glibc 의 걸음.
- ★★ **4번의 경고** — gcc 13 · clang 18 의 경고 설계.

**`strtol` 의 값·`endptr`·`ERANGE` · C23 의 `0b` · `atoi` 넘침이 UB 인 것 · 비교자가 전체 순서를 이뤄야 한다는 것 · `bsearch` 의 정렬 전제는 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `strtoul("-1")` · C 로케일 밖의 주어 형식 · 차이가 1 이상 섞인 `by_diff` 데이터.
- ★ **부적용** — 시간 측정.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번** — glibc 가 `qsort` 구현을 바꾸면 결과가 달라진다(★ 이 문서는 glibc 의 **판 이력을 확인하지 않았다**).
- ★★ **2번** — `-std=c23` 이 기본이 되는 판.
- ★★ **4번** — gcc 가 `-strict` 에 해당하는 경고를 얻는지.
