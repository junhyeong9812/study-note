# c/syntax/17 — 다차원 배열과 그 포인터 타입: 「**한 줄로 깔리고, 한 겹만 벗겨진다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c17b/17`, 소스는 `ex.c`\~`ex7.c` 다.\
> ★★ 출력이 섞이는 프로그램에는 **`setvbuf(stdout, NULL, _IONBF, 0)`** 를 넣어 순서를 고정했고,\
> ASan 블록은 **`| sed -n '1,/^SUMMARY/p'`** 로 잘랐다 — **그 명령의 전체 출력**이라 다시 던질 수 있다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 순회 실험의 **초**·**배율** · `a[3][0]` 의 **쓰레기 값** | ★ **행우선 < 열우선** 부등호 · 주소들 **사이의 차이**(44 · 16 · 4 · 48) |
> | UBSan 의 **주소·바이트 덤프** · ASan 의 `pc`/`bp`/`sp` · PID · `BuildId` | ★ **`sizeof` 값**(48 · 16 · 8 · 4) · `_Generic` 의 **타입 이름** |
> | — | **`파일:줄:칸`** · 진단 본문 · 플래그 이름 · **종료 코드** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `int a[3][4]` 의 크기와 주소 차 — **48 · 16 · 4, 그리고 44** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof a       = 48
sizeof a[0]    = 16
sizeof a[0][0] = 4
첫 원소 &a[0][0] - 끝 원소 &a[2][3] 의 차 = 44 바이트
행 시작 주소의 차 : a[1]-a[0] = 16 · a[2]-a[1] = 16 바이트

원소를 선언 순서로 찍는다 (오프셋 = &a[i][j] - &a[0][0])
  a[0][0] =  1   오프셋  0
  a[0][1] =  2   오프셋  4
  a[0][2] =  3   오프셋  8
  a[0][3] =  4   오프셋 12
  a[1][0] =  5   오프셋 16
  a[1][1] =  6   오프셋 20
  a[1][2] =  7   오프셋 24
  a[1][3] =  8   오프셋 28
  a[2][0] =  9   오프셋 32
  a[2][1] = 10   오프셋 36
  a[2][2] = 11   오프셋 40
  a[2][3] = 12   오프셋 44

한 줄로 이어 읽는다 (int * 하나로 12칸)
  1 2 3 4 5 6 7 8 9 10 11 12 
```

(소스 전문은 [2-summary.md](2-summary.md) (1)에 있다.)

**왜 그런가**

```text
   +----+----+----+----+----+----+----+----+----+----+----+----+
   |  1 |  2 |  3 |  4 |  5 |  6 |  7 |  8 |  9 | 10 | 11 | 12 |
   +----+----+----+----+----+----+----+----+----+----+----+----+
     0    4    8    12   16   20   24   28   32   36   40   44
     ^                   ^                   ^              ^
     a[0][0]             a[1][0]             a[2][0]        a[2][3]

   ★ 48 = 12칸 x 4바이트.  44 = 48 - 4 (마지막 "칸의 시작"까지만 잰 것)
```

- **세 `sizeof` 는 48 · 16 · 4** 다. `sizeof a` == `sizeof a[0]` × 3 이 **정확히** 성립한다.
- **`&a[2][3] - &a[0][0]` 은 44** 다 — 마지막 **원소의 시작**까지만 쟀기 때문이고,\
  ★ 「48 − 4 = 44」가 맞아떨어지는 것이 **끝까지 빈틈이 없다는 증거**다.
- **행 시작 주소의 차는 둘 다 16**, **오프셋은 0 · 4 · 8 · … · 44**(공차 4)다. 한 칸도 건너뛰지 않는다.
- ★★ **마지막 루프는 `1 2 3 4 5 6 7 8 9 10 11 12` 를 찍는다** — `int *` 하나로 12칸이 다 읽힌다.\
  ★★★ **그런데 그것이 표준이 보장하는 것은 아니다.** `flat` 은 **`a[0]`(`int[4]`) 안의 원소**를 가리키는 포인터라\
  `flat[4]` 부터는 그 배열의 끝을 넘는다 — **6번 답**이 그 이야기다.

### 2. 일곱 식의 타입과 보폭 — **`int **` 는 한 번도 안 나온다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=0) =====
a        -> int (*)[4]
a + 0    -> int (*)[4]
&a       -> int (*)[3][4]
a[0]     -> int *
&a[0][0] -> int *
*a       -> int *
a[0][0]  -> int

보폭 — 무엇에 1을 더하나
  (char *)(a+1)        - (char *)a        = 16
  (char *)(a[0]+1)     - (char *)a[0]     = 4
  (char *)(&a+1)       - (char *)&a       = 48

sizeof 로 본 같은 것
  sizeof a = 48 · sizeof *a = 16 · sizeof **a = 4
  sizeof &a = 8 · sizeof *&a = 48
  int (*p)[4] = a;  sizeof p = 8 · sizeof *p = 16 · p[1][2] = 7
```

(소스 전문은 [2-summary.md](2-summary.md) (2)에 있다.)

**왜 그런가**

```text
   a        -> int (*)[4]      감쇠했다 (바깥 한 겹만 벗겨진다)
   a + 0    -> int (*)[4]      a 와 같다
   &a       -> int (*)[3][4]   ★ 감쇠 안 한다
   a[0]     -> int *           a[0] 은 int[4] 이고 그것이 다시 감쇠한 것
   &a[0][0] -> int *           같은 번지, 같은 타입
   *a       -> int *           *a 는 a[0] 이다
   a[0][0]  -> int

   보폭 :  a+1 = +16(행)   a[0]+1 = +4(칸)   &a+1 = +48(배열 전체)
   sizeof:  a 48 · *a 16 · **a 4 · &a 8 · *&a 48
```

- **일곱 답은 `int (*)[4]` · `int (*)[4]` · `int (*)[3][4]` · `int *` · `int *` · `int *` · `int`** 다.
- ★★★ **`int **` 라고 답하는 것은 0개**다. **배열에서 저절로 만들어지는 타입이 아니다.**
- **보폭은 16 · 4 · 48** — **가리키는 것의 크기가 곧 보폭**이다.\
  `int[4]` 는 16바이트, `int` 는 4바이트, `int[3][4]` 는 48바이트다.
- **다섯 `sizeof` 는 48 · 16 · 4 · 8 · 48** 이다. ★ **`sizeof &a` 가 8**(포인터)인데 **`sizeof *&a` 가 다시 48** 인 것이\
  「`&a` 가 **배열 전체**를 가리킨다」는 증거다.
- **`sizeof p` 는 8**(포인터), **`sizeof *p` 는 16**(가리키는 `int[4]`), **`p[1][2]` 는 7** 이다.\
  ★ `p + 1` 이 **16바이트** 건너 둘째 행에 닿고 거기서 `[2]` 가 **8바이트 더** 간다 → 오프셋 24 → `7`.

### 3. 매개변수 세 꼴 — **한 글자도 다르지 않다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3 ; ./x3 (cc exit=0 · run exit=0) =====
main 안     : sizeof a = 48 · sizeof a[0] = 16
int a[3][4] : sizeof a = 8 · sizeof a[0] = 16 · 타입 int (*)[4] · a[1][2] = 7
int a[][4]  : sizeof a = 8 · sizeof a[0] = 16 · 타입 int (*)[4] · a[1][2] = 7
int (*a)[4] : sizeof a = 8 · sizeof a[0] = 16 · 타입 int (*)[4] · a[1][2] = 7
선언 int a[3][4] · 정의 int (*a)[4] : a[2][3] = 12
```

```c
/* ex3.c */
#include <stdio.h>

#define TYPE(e) _Generic((e), int (*)[4]: "int (*)[4]", int **: "int **", default: "그 밖")

static void f_full(int a[3][4]) {
    printf("int a[3][4] : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}
static void f_open(int a[][4]) {
    printf("int a[][4]  : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}
static void f_ptr(int (*a)[4]) {
    printf("int (*a)[4] : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}

/* 선언과 정의를 다른 꼴로 써도 같은 함수다 — 링크가 된다는 것이 증거다 */
void f_decl(int a[3][4]);
void f_decl(int (*a)[4]) { printf("선언 int a[3][4] · 정의 int (*a)[4] : a[2][3] = %d\n", a[2][3]); }

int main(void) {
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    printf("main 안     : sizeof a = %zu · sizeof a[0] = %zu\n", sizeof a, sizeof a[0]);
    f_full(a);
    f_open(a);
    f_ptr(a);
    f_decl(a);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex3.c -o x3 (cc exit=0) =====
ex3.c: In function ‘f_full’:
ex3.c:7:19: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int (*)[4]’ [-Wsizeof-array-argument]
    7 |            sizeof a, sizeof a[0], TYPE(a), a[1][2]);
      |                   ^
ex3.c:5:24: note: declared here
    5 | static void f_full(int a[3][4]) {
      |                    ~~~~^~~~~~~
ex3.c: In function ‘f_open’:
ex3.c:11:19: warning: ‘sizeof’ on array function parameter ‘a’ will return size of ‘int (*)[4]’ [-Wsizeof-array-argument]
   11 |            sizeof a, sizeof a[0], TYPE(a), a[1][2]);
      |                   ^
ex3.c:9:24: note: declared here
    9 | static void f_open(int a[][4]) {
      |                    ~~~~^~~~~~
ex3.c: At top level:
ex3.c:20:19: warning: argument 1 of type ‘int (*)[4]’ declared as a pointer [-Warray-parameter=]
   20 | void f_decl(int (*a)[4]) { printf("선언 int a[3][4] · 정의 int (*a)[4] : a[2][3] = %d\n", a[2][3]); }
      |             ~~~~~~^~~~~
ex3.c:19:17: note: previously declared as an array ‘int[3][4]’
   19 | void f_decl(int a[3][4]);
      |             ~~~~^~~~~~~
```

**왜 그런가**

```text
   void f(int a[3][4])  --재작성-->  void f(int (*a)[4])
   void f(int a[][4])   --재작성-->  void f(int (*a)[4])
   void f(int (*a)[4])                void f(int (*a)[4])

   세 함수 안 :  sizeof a 8 · sizeof a[0] 16 · int (*)[4] · a[1][2] = 7
   main 안     :  sizeof a 48 · sizeof a[0] 16
   ★ 달라진 것은 48 -> 8 하나뿐. 즉 "행 수 3" 만 잃었다.
```

- **세 함수의 네 값은 `8` · `16` · `int (*)[4]` · `7`** 로 **셋이 완전히 같다.**
- **`main` 안은 `48` 과 `16`** 이다. ★ **바뀐 것은 `sizeof a` 하나**(48 → 8) — **열 수는 타입에 남는다.**
- **gcc 경고는 3건**이다 — `f_full`·`f_open` 의 **`-Wsizeof-array-argument`** 둘과,\
  ★★★ **성격이 다른 한 건**인 **`-Warray-parameter=`** 하나다.
- ★ 그 한 건을 낸 것은 **`f_decl`** 이다 — **선언은 `int a[3][4]`, 정의는 `int (*a)[4]`** 로 **꼴을 바꿔 썼다.**\
  ★ gcc 문서에서 확인한 것 — **`-Warray-parameter=2` 가 `-Wall` 에 들어 있다.**
- ★★ **`f_decl` 은 링크된다.** 실행되어 **`a[2][3]` 이 12** 를 찍었다.\
  **경고가 말하는 것은 「틀렸다」가 아니라 「두 자리의 표기가 어긋났다」이고**, 끄는 방법은 **표기를 맞추는 것**이다.

### 4. `int **` 로 받으면 — **경고 한 줄, 그리고 `run exit=139`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 (cc exit=0 · run exit=139) =====
good : a[1][0] = 5
bad 가 a[1] 로 읽을 8바이트 = a[0][2], a[0][3] = 3, 4
```

```c
/* ex4.c */
#include <stdio.h>

static void good(int (*a)[4]) { printf("good : a[1][0] = %d\n", a[1][0]); }
static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    good(a);
    printf("bad 가 a[1] 로 읽을 8바이트 = a[0][2], a[0][3] = %d, %d\n", a[0][2], a[0][3]);
    bad(a);
    printf("여기까지 오면 죽지 않은 것이다\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 (cc exit=0) =====
ex4.c: In function ‘main’:
ex4.c:11:9: warning: passing argument 1 of ‘bad’ from incompatible pointer type [-Wincompatible-pointer-types]
   11 |     bad(a);
      |         ^
      |         |
      |         int (*)[4]
ex4.c:4:23: note: expected ‘int **’ but argument is of type ‘int (*)[4]’
    4 | static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }
      |                 ~~~~~~^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex4.c -o x4c (cc exit=0) =====
ex4.c:11:9: warning: incompatible pointer types passing 'int[3][4]' to parameter of type 'int **' [-Wincompatible-pointer-types]
   11 |     bad(a);
      |         ^
ex4.c:4:23: note: passing argument to parameter 'a' here
    4 | static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }
      |                       ^
1 warning generated.
```

**왜 그런가**

```text
   실제 메모리 (오프셋)
     0    4    8   12   16   20   24   28   32   36   40   44
   +----+----+----+----+----+----+----+----+----+----+----+----+
   |  1 |  2 |  3 |  4 |  5 |  6 |  7 |  8 |  9 | 10 | 11 | 12 |
   +----+----+----+----+----+----+----+----+----+----+----+----+
             \_________/
              int ** 는 이 8바이트를 ★ 주소로 읽는다 (그 비트는 3, 4)

   int (*a)[4] :  a[1] = 시작 + 1 x 16  -> 오프셋 16 -> 5 6 7 8 -> a[1][0] = 5
   int **a     :  a[1] = 시작 + 1 x  8  -> 그 자리의 값을 ★ 번지로 여기고 역참조 -> SIGSEGV
```

- **경고이고 에러가 아니다** — **`cc exit=0`** 이라 실행 파일이 그대로 나온다.
- **gcc 의 `note:`** 가 두 타입을 나란히 말한다 — 「**expected `int **` but argument is of type `int (*)[4]`**」.
- ★★ **clang 은 같은 자리를 다른 이름으로 부른다** — 「`passing 'int[3][4]' to parameter of type 'int **'`」.\
  ★ **gcc 는 감쇠 뒤 타입**(`int (*)[4]`)을, **clang 은 감쇠 전 타입**(`int[3][4]`)을 적는다.
- **찍힌 것은 두 줄**이다 — `good : a[1][0] = 5` 와 `bad 가 a[1] 로 읽을 8바이트 … = 3, 4`.\
  ★★ **`bad :` 줄도 「여기까지 오면 죽지 않은 것이다」도 안 찍혔다** — `printf` 의 인자를 계산하다 죽었다.\
  **`run exit=139`**(= 128 + 11, SIGSEGV)다. ★ **출력의 부재가 증거**다.
- ★★★ **`bad` 안의 `a[1]` 은 둘째 행이 아니다.** 「**오프셋 8부터 8바이트를 읽은 값**」을 **번지로** 쓴다.\
  그 8바이트는 `a[0][2]`·`a[0][3]` 의 비트이고 실행이 먼저 찍어 준 값이 **3, 4** 였다.\
  ★ **죽은 것은 운이 좋은 쪽**이다 — 그 비트가 유효한 번지였으면 **조용히 엉뚱한 값**을 읽는다\
  ([01번 형제](../01-declaration-syntax-and-reading/)의 결론을 되짚은 것이다).

### 5. `int a[3][]` — **컴파일 에러, `cc exit=1`** ★★

**출력** — ★ 실행 파일이 아예 나오지 않는다.

```c
/* ex5.c */
#include <stdio.h>

/* (가) 첫 차원은 생략할 수 있다 — 매개변수 자리에서 버려지는 것이 그것뿐이기 때문이다 */
static void ok_open(int a[][4]) { printf("ok_open  : a[1][0] = %d\n", a[1][0]); }

/* (나) 둘째 차원은 생략할 수 없다 — 한 행의 보폭이 정해지지 않는다 */
static void ng_open(int a[3][]) { printf("ng_open  : a[1][0] = %d\n", a[1][0]); }

int main(void) {
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    ok_open(a);
    ng_open(a);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=1) =====
ex5.c:7:25: error: array type has incomplete element type ‘int[]’
    7 | static void ng_open(int a[3][]) { printf("ng_open  : a[1][0] = %d\n", a[1][0]); }
      |                         ^
ex5.c:7:25: note: declaration of ‘a’ as multidimensional array must have bounds for all dimensions except the first
ex5.c: In function ‘ng_open’:
ex5.c:7:25: warning: unused parameter ‘a’ [-Wunused-parameter]
    7 | static void ng_open(int a[3][]) { printf("ng_open  : a[1][0] = %d\n", a[1][0]); }
      |                     ~~~~^~~~~~
ex5.c: In function ‘main’:
ex5.c:12:13: error: type of formal parameter 1 is incomplete
   12 |     ng_open(a);
      |             ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=1) =====
ex5.c:7:26: error: array has incomplete element type 'int[]'
    7 | static void ng_open(int a[3][]) { printf("ng_open  : a[1][0] = %d\n", a[1][0]); }
      |                          ^
1 error generated.
```

**왜 그런가**

```text
   int a[3][4]   ->  int (*a)[4]     [3] 은 어차피 버려진다
   int a[ ][4]   ->  int (*a)[4]     ★ 같은 결과
   int a[3][ ]   ->  int (*a)[ ]     ★ "크기를 모르는 배열"을 가리키는 포인터
                                        -> 보폭을 정할 수 없다 -> 에러
```

- **`cc exit=1`** 이다. ★★ **4번과 정반대**다 — 4번은 **경고에 `cc exit=0`** 이라 실행 파일이 나왔다.\
  ★ **`int **` 는 「타입이 안 맞는다」이고, `int a[3][]` 는 「타입이 성립하지 않는다」이다**.
- **gcc 는 네 줄**을 낸다 — **`error:` 두 줄**(불완전 원소 타입 · 호출부의 불완전 매개변수)과\
  **`note:` 한 줄**, 그리고 **`-Wunused-parameter` 경고 한 줄**이다.\
  ★ 마지막 것은 **곁가지**다(타입이 불완전해 본문에서 `a` 를 못 쓴 결과). **`error:` 줄이 본론**이다.
- ★★★ **gcc 의 `note:` 가 규칙을 그대로 말해 준다** —\
  「**declaration of `a` as multidimensional array must have bounds for all dimensions except the first**」.
- **clang 은 에러 한 건**으로 끝낸다(`array has incomplete element type 'int[]'`). ★ **gcc 가 「왜」를 더 말한다.**

### 6. `int *` 로 행을 넘으면 — **두 도구가 둘 다 침묵한다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g ex7.c -o x7 ; ./x7 (cc exit=0 · run exit=0) =====
flat[3]  = 4  (a[0] 안 — 문제 없다)
flat[4]  = 5  (★ a[0] 의 끝을 넘었다)
flat[11] = 12  (★ 그래도 값은 맞게 나온다)
a[0][4]  = 5  (★ 같은 자리를 다른 표기로)
a[3][0]  = -271391632  (★ 배열 전체의 밖)
```

```c
/* ex7.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    int *flat = &a[0][0];           /* a[0] 은 int[4] 다 */
    printf("flat[3]  = %d  (a[0] 안 — 문제 없다)\n", flat[3]);
    printf("flat[4]  = %d  (★ a[0] 의 끝을 넘었다)\n", flat[4]);
    printf("flat[11] = %d  (★ 그래도 값은 맞게 나온다)\n", flat[11]);
    printf("a[0][4]  = %d  (★ 같은 자리를 다른 표기로)\n", a[0][4]);
    printf("a[3][0]  = %d  (★ 배열 전체의 밖)\n", a[3][0]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=undefined ex7.c -o x7u ; ./x7u (cc exit=0 · run exit=0) =====
flat[3]  = 4  (a[0] 안 — 문제 없다)
flat[4]  = 5  (★ a[0] 의 끝을 넘었다)
flat[11] = 12  (★ 그래도 값은 맞게 나온다)
ex7.c:10:76: runtime error: index 4 out of bounds for type 'int [4]'
a[0][4]  = 5  (★ 같은 자리를 다른 표기로)
ex7.c:11:60: runtime error: index 3 out of bounds for type 'int [3][4]'
ex7.c:11:5: runtime error: load of address 0x7fff04b8a9a0 with insufficient space for an object of type 'int'
0x7fff04b8a9a0: note: pointer points here
 0c 00 00 00  40 aa b8 04 ff 7f 00 00  00 32 50 ea 69 86 be d4  50 aa a7 4c a8 70 00 00  e8 aa b8 04
              ^ 
a[3][0]  = 79211072  (★ 배열 전체의 밖)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex7.c -o x7a ; ./x7a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
flat[3]  = 4  (a[0] 안 — 문제 없다)
flat[4]  = 5  (★ a[0] 의 끝을 넘었다)
flat[11] = 12  (★ 그래도 값은 맞게 나온다)
a[0][4]  = 5  (★ 같은 자리를 다른 표기로)
=================================================================
==83830==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x752be6400060 at pc 0x5b86fc1dc7e4 bp 0x7ffef1ce13f0 sp 0x7ffef1ce13e0
READ of size 4 at 0x752be6400060 thread T0
    #0 0x5b86fc1dc7e3 in main /tmp/c17b/17/ex7.c:11
    #1 0x752be842a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x752be842a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5b86fc1dc1c4 in _start (/tmp/c17b/17/x7a+0x11c4) (BuildId: 6f17895b7576ae2f8c97e24a78853e2b017404e4)

Address 0x752be6400060 is located in stack of thread T0 at offset 96 in frame
    #0 0x5b86fc1dc298 in main /tmp/c17b/17/ex7.c:3

  This frame has 1 object(s):
    [48, 96) 'a' (line 5) <== Memory access at offset 96 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow /tmp/c17b/17/ex7.c:11 in main
```

**왜 그런가**

```text
   접근            오프셋   평범한 실행   UBSan          ASan
   flat[3]           12      4            조용           조용        <- 합법
   ★ flat[4]         16      5            ★ 조용         ★ 조용
   ★ flat[11]        44      12           ★ 조용         ★ 조용
   a[0][4]           16      5            ★ 잡는다       ★ 조용
   a[3][0]           48      쓰레기       ★ 잡는다       ★ 잡는다(죽는다)

   종료 코드                 run exit=0   run exit=0     run exit=1

   UBSan : "첨자가 ★ 이 타입의 범위 안인가" — flat 은 그냥 int * 라 볼 경계가 없다
   ASan  : "번지가 ★ 이 객체(48바이트) 안인가" — a[0][4] 는 객체 안이라 잡을 것이 없다
```

- **다섯 값은 `4` · `5` · `12` · `5` · 쓰레기**다.\
  ★ **흔들리는 것은 `a[3][0]` 하나**다 — 평범한 실행과 UBSan 판에서 **서로 다른 값**이 나왔다. **근거가 못 된다.**
- **평범한 실행은 `run exit=0`** 이다. ★★★ **「돌아갔다」가 아무것도 증명하지 못하는 자리**다.
- **UBSan 이 말하는 것은 뒤의 두 줄**(`a[0][4]` 와 `a[3][0]`)뿐이고 **진단은 세 줄**이다 —\
  `index 4 out of bounds for type 'int [4]'` · `index 3 out of bounds for type 'int [3][4]'` ·\
  그리고 `load of address … with insufficient space for an object of type 'int'`.\
  ★ **UBSan 은 죽지 않는다**(`run exit=0`) — 진단을 찍고 계속 간다.
- ★★★ **`flat[4]` 와 `a[0][4]` 는 같은 번지이고 값도 둘 다 5 인데 결과가 갈린다.**\
  **UBSan 이 보는 것은 「첨자가 그 타입의 범위 안인가」이고**, `a[0]` 은 **`int[4]`** 라 `4` 가 밖인데\
  **`flat` 은 그냥 `int *` 라 볼 경계가 없다.** ★★ **틀린 것은 번지가 아니라 「어떤 타입으로 지나갔나」다**.
- **ASan 이 잡는 것은 `a[3][0]` 한 줄**이고 **`run exit=1`** 로 죽는다. 프레임 정보가 **`[48, 96) 'a'`** 로 객체를 말해 준다.\
  ★ `a[0][4]` 는 **48바이트 객체 안**이라 ASan 의 문법으로는 위반이 아니다 — 값 `5` 를 찍고 지나갔다.

### 7. 행우선/열우선에서 근거가 되는 것 — **부등호와 「안 변한다」는 성질** ★★

**출력** (요약은 [2-summary.md](2-summary.md) (6)에 있고, 여기에는 **양 끝 두 벌**을 싣는다)

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 ex6.c -o x6_O0 ; ./x6_O0 (cc exit=0 · run exit=0) =====
배열 4096 x 4096 int = 67108864 바이트 · 한 행 = 16384 바이트 (CLOCKS_PER_SEC = 1000000)
판  행우선(초)  열우선(초)  배율   합(같아야 한다)
1      0.050       0.168    3.34  58720256 58720256
2      0.050       0.179    3.55  58720256 58720256
3      0.050       0.172    3.46  58720256 58720256
4      0.053       0.180    3.37  58720256 58720256
5      0.047       0.160    3.40  58720256 58720256
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 ex6.c -o x6c ; ./x6c (cc exit=0 · run exit=0) =====
배열 4096 x 4096 int = 67108864 바이트 · 한 행 = 16384 바이트 (CLOCKS_PER_SEC = 1000000)
판  행우선(초)  열우선(초)  배율   합(같아야 한다)
1      0.012       0.205   17.63  58720256 58720256
2      0.011       0.184   16.10  58720256 58720256
3      0.008       0.160   20.60  58720256 58720256
4      0.006       0.173   28.51  58720256 58720256
5      0.010       0.162   16.80  58720256 58720256
```

**왜 그런가**

```text
               행우선(초)        열우선(초)        배율
   gcc  -O0    0.043 ~ 0.045     0.171 ~ 0.188     3.82 ~ 4.23
   gcc  -O1    0.008 ~ 0.010     0.138 ~ 0.158    15.22 ~ 18.46
   gcc  -O2    0.006 ~ 0.009     0.149 ~ 0.177    20.00 ~ 24.37
   clang -O2   0.006 ~ 0.012     0.141 ~ 0.161    13.42 ~ 25.37

   ★ 열우선은 0.17대 -> 0.15대.  행우선은 0.044 -> 0.007.
```

- **합은 두 순서에서 같다**(`58720256`). ★★ **시간보다 먼저 확인해야 하는 이유** — 합이 다르면 **다른 계산**을 비교한 것이고,\
  안 나오면 **루프가 통째로 지워졌을** 수도 있다. ★ 「빨라졌다」의 가장 흔한 거짓 원인이 그것이다.
- **`-O0` → `-O2` 에서 행우선은 여섯 배 빨라지고**(0.044 → 0.007) **열우선은 거의 그대로**다(0.17대 → 0.15대).
- ★★★ **그래서 배율이 커진 것은 「열우선이 느려져서」가 아니라 「행우선만 빨라져서」다**.\
  ★ **열우선이 기다리는 것은 계산이 아니라 메모리**라서 컴파일러가 구해 주지 못한다.
- ★★ **근거로 쓸 수 있는 것** — ① **행우선 < 열우선** 이라는 **부등호**(스무 벌 전부 같았다)\
  ② **열우선 시간이 최적화에 거의 반응하지 않는다**는 성질 ③ **두 합이 같다**는 사실.
- ★ **근거로 쓸 수 없는 것** — **초의 절댓값**과 **배율 숫자**다. `-O1`\~`-O2` 에서만 **13.42\~25.37** 로 벌어진다.\
  ★ 배율은 이 머신의 캐시·프리페처에 달린 것이라 **표준도 구현 정의도 아니다.**

### 8. 왜 첫 차원만 생략할 수 있는가 — **버려지는 겹이 그것 하나이기 때문** ★★★

**답**

```text
   버려지는 겹      남는 겹
   [3]              [4]
   |                |
   안 써도 잃을 게   ★ 보폭을 만든다 (a + 1 = +16)
   없다              -> 모르면 a + 1 을 계산할 수 없다
```

- **버려지는 것은 바깥 한 겹**이다. `int[3][4]` → `int (*)[4]` 에서 **`[3]` 만 떨어진다.**
- **둘째 차원을 비우면 `int (*a)[]`** 가 된다 — **「크기를 모르는 배열」을 가리키는 포인터**다.\
  ★ 그 배열 타입이 **불완전**해서 **`a + 1` 의 보폭을 정할 수 없고**, C 는 **배열의 원소 타입이 불완전한 것**을 금지한다.
- ★★★ **`int **` 를 못 쓰는 이유와 같은 문장**이다 —\
  **「매개변수 자리에서 벗겨지는 것은 바깥 한 겹뿐이고, 남은 겹이 보폭을 만든다.」**\
  `int **` 는 **남은 겹을 「포인터 하나(8바이트)」로 바꿔 버린** 것이고,\
  `int a[3][]` 는 **남은 겹의 크기를 아예 안 준** 것이다. **둘 다 보폭이 안 나온다.**

### 9. `p[1][2]` 가 맞는 값을 내는 이유 — **바깥은 행, 안쪽은 칸** ★★

**답**

```text
   p[1][2]  ==  *( *(p + 1) + 2 )

   p + 1        p 는 int (*)[4]  -> +16바이트 (행 하나)      -> 오프셋 16
   *(p + 1)     결과는 int[4] 이고 식에서 다시 감쇠 -> int *
   ... + 2      int * 라 +8바이트 (칸 둘)                    -> 오프셋 24  -> 값 7

   int **p 라면
   p + 1        +8바이트 (포인터 하나)
   *(p + 1)     ★ 그 8바이트를 "번지"로 읽는다   <- 여기가 진짜 차이다
   ... + 2      그 번지에서 +8바이트
```

- **`p + 1` 은 16바이트, 그 다음 `+ 2` 는 8바이트** 움직인다. 합쳐 **오프셋 24** 이고 값이 **7** 이다.
- ★★★ **`int **` 로 쓰면 보폭만 달라지는 것이 아니다.** **`*(p + 1)` 이 한 겹 더 역참조**한다 —\
  **데이터를 주소로 읽는다.** ★ 보폭이 8이라는 것은 **부수적인 이야기**이고, **역참조가 한 번 더 있는 것**이 본질이다.
- ★★ **`sizeof` 로는 못 가른다** — **`int (*)[4]` 도 8, `int **` 도 8, `int *` 도 8** 이다.\
  ★ 가르는 것은 **`_Generic` 이 답한 타입 이름**과 **보폭**(16 ↔ 8 ↔ 4)이고,\
  ★ **`sizeof *p` 는 가른다** — 16 ↔ 8 ↔ 4.

### 10. 버전 축 — **C23 에서도 그대로 경고다** (경계) ★

**출력**

```c
/* ex4.c */
#include <stdio.h>

static void good(int (*a)[4]) { printf("good : a[1][0] = %d\n", a[1][0]); }
static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    good(a);
    printf("bad 가 a[1] 로 읽을 8바이트 = a[0][2], a[0][3] = %d, %d\n", a[0][2], a[0][3]);
    bad(a);
    printf("여기까지 오면 죽지 않은 것이다\n");
    return 0;
}
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic ex4.c -o /dev/null (cc exit=0) =====
ex4.c: In function ‘main’:
ex4.c:11:9: warning: passing argument 1 of ‘bad’ from incompatible pointer type [-Wincompatible-pointer-types]
   11 |     bad(a);
      |         ^
      |         |
      |         int (*)[4]
ex4.c:4:23: note: expected ‘int **’ but argument is of type ‘int (*)[4]’
    4 | static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }
      |                 ~~~~~~^
```

```text
===== clang -std=c23 -Wall -Wextra -pedantic ex4.c -o /dev/null (cc exit=0) =====
ex4.c:11:9: warning: incompatible pointer types passing 'int[3][4]' to parameter of type 'int **' [-Wincompatible-pointer-types]
   11 |     bad(a);
      |         ^
ex4.c:4:23: note: passing argument to parameter 'a' here
    4 | static void bad(int **a)      { printf("bad  : a[1][0] = %d\n", a[1][0]); }
      |                       ^
1 warning generated.
```

**왜 그런가**

- ★ **gcc 13 에는 `-std=c23` 이 없다** — 그래서 이 배치는 gcc 에 **`-std=c2x`** 를 쓴다.\
  (배치 공통 환경 사실이고 ★ **이 주제는 그 실패 출력을 블록으로 싣지 않았다.**) clang 18 은 `-std=c23` 이 있다.
- ★★ **승격되지 않았다.** `-std=c17` 판과 **진단 본문·플래그 이름·줄·칸·종료 코드가 한 글자도 같다.**\
  네 벌(gcc c17 · gcc c2x · clang c17 · clang c23) 전부 **경고 1건에 `cc exit=0`** 이다.
- **행 우선 연속 배치와 감쇠 결과 타입은 C89 이후 바뀐 적이 없다.** 이 주제의 본체는 **버전 축이 없다.**
- **`_Generic` 은 C11부터**다. ★ **주제의 일부가 아니라 도구**다 —\
  C99 이하에서는 같은 확인을 **보폭으로만** 해야 하고, 그쪽은 C89에서도 된다.

### 11. 어느 도구가 무엇을 보나 ★★

**출력** — gcc 가 3건을 낸 같은 파일을 clang 에 던진 것

```c
/* ex3.c */
#include <stdio.h>

#define TYPE(e) _Generic((e), int (*)[4]: "int (*)[4]", int **: "int **", default: "그 밖")

static void f_full(int a[3][4]) {
    printf("int a[3][4] : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}
static void f_open(int a[][4]) {
    printf("int a[][4]  : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}
static void f_ptr(int (*a)[4]) {
    printf("int (*a)[4] : sizeof a = %zu · sizeof a[0] = %zu · 타입 %s · a[1][2] = %d\n",
           sizeof a, sizeof a[0], TYPE(a), a[1][2]);
}

/* 선언과 정의를 다른 꼴로 써도 같은 함수다 — 링크가 된다는 것이 증거다 */
void f_decl(int a[3][4]);
void f_decl(int (*a)[4]) { printf("선언 int a[3][4] · 정의 int (*a)[4] : a[2][3] = %d\n", a[2][3]); }

int main(void) {
    int a[3][4] = {{1,2,3,4},{5,6,7,8},{9,10,11,12}};
    printf("main 안     : sizeof a = %zu · sizeof a[0] = %zu\n", sizeof a, sizeof a[0]);
    f_full(a);
    f_open(a);
    f_ptr(a);
    f_decl(a);
    return 0;
}
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex3.c -o x3c (cc exit=0) =====
ex3.c:7:19: warning: sizeof on array function parameter will return size of 'int (*)[4]' instead of 'int[3][4]' [-Wsizeof-array-argument]
    7 |            sizeof a, sizeof a[0], TYPE(a), a[1][2]);
      |                   ^
ex3.c:5:24: note: declared here
    5 | static void f_full(int a[3][4]) {
      |                        ^
ex3.c:11:19: warning: sizeof on array function parameter will return size of 'int (*)[4]' instead of 'int[][4]' [-Wsizeof-array-argument]
   11 |            sizeof a, sizeof a[0], TYPE(a), a[1][2]);
      |                   ^
ex3.c:9:24: note: declared here
    9 | static void f_open(int a[][4]) {
      |                        ^
2 warnings generated.
```

**왜 그런가**

```text
   프로그램        gcc                                   clang
   ex3.c (세 꼴)   3건  -Wsizeof-array-argument x2        2건  -Wsizeof-array-argument x2
                        + ★ -Warray-parameter= x1              + ★ 없음
   ex4.c (int **)  1건  "int (*)[4]" 라고 적는다           1건  ★ "int[3][4]" 라고 적는다
   ex5.c (a[3][])  4줄  error 2 + note 1 + warning 1       1건  error 1
   맞게 쓴 코드     ★ 0건                                  ★ 0건
```

- **갈리는 자리 둘** — ① **`-Warray-parameter=`** 는 **gcc 에만** 있다(3건 대 2건).\
  ② **`int a[3][]`** 에서 gcc 는 **네 줄**, clang 은 **한 건**이다.
- ★ **clang 이 더 말해 주는 것** — `-Wsizeof-array-argument` 문구에 **버려진 타입**을 적는다\
  (`instead of 'int[3][4]'` · `instead of 'int[][4]'`). gcc 는 적지 않는다.
- ★★★ **맞게 쓴 코드의 경고는 0건**이다 — **「경고가 없다」가 아무 정보가 아니라는 뜻**이다.
- ★★ **다섯 도구가 각각 보는 것**
  - **`sizeof`** — **크기만** 본다. `int (*)[4]`·`int **`·`int *` 를 **전부 8** 로 답해 못 가른다.
  - **`_Generic`** — **타입 이름**을 본다. ★ 이 주제의 **네 번째 창**이다.
  - **보폭**(포인터 차를 바이트로) — **가리키는 것의 크기**를 본다(16 · 4 · 48).
  - **UBSan** — **첨자가 그 타입의 범위 안인가**를 본다. **타입이 지워지면 침묵**한다.
  - **ASan** — **객체 경계**만 본다. **48바이트 안의 일은 전부 통과**시킨다.

### 12. 다섯 층과 경계 ★★

**답**

| 층 | 이 주제(17번) | [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
|---|---|---|
| **표준** | ★★ **본체** — 행 우선 연속 배치 · 감쇠 결과 `int (*)[4]` · `&a` 는 `int (*)[3][4]` · 세 꼴 동치 · 첫 차원만 생략 | 감쇠 규칙 · 매개변수 재작성 · 감쇠 안 하는 셋 |
| **조건부 표준** | ★ **없다** | ★ **해당 없음** |
| **구현 정의** | `sizeof(int)`==4 라서 **48·16·4·44**·보폭 16 · `sizeof(int *)`==8 | `sizeof(int)`·리터럴이 읽기 전용 영역에 놓이는 것 |
| **미명시** | ★ **배열 객체의 주소값 자체**(이 문서는 **차만** 썼다) | 같은 리터럴의 공유 여부 |
| **UB** | 행 경계를 넘는 `int *` 접근 · 배열 전체 밖 · `int **` 로 받은 뒤의 역참조 | ★★ **본체** — 길이를 잃은 뒤의 접근 |

- **비어 있는 칸은 「조건부 표준」이다**. ★ **그 칸은 [목록의 18번 주제](../18-variable-length-arrays-vla/)(VLA)에서 채워진다** —\
  VLA 는 **C99 필수 → C11 선택(`__STDC_NO_VLA__`)** 으로 바뀐 기능이라 **조건부 보장**이 생긴다.
- ★★ **무게중심이 16번과 정반대**다 — **16번은 UB 가 본체**이고 **17번은 표준이 본체**다.\
  ★ 다만 **17번의 UB 칸에 사각지대가 하나 있다**(`flat[4]`). **16번의 UB 는 「사람이 계약으로 막아야 하는 것」이었고**,\
  **17번의 UB 는 「표기를 바꿔야 도구에 보이는 것」이다**.
- **경계 네 줄**
  - **선언 읽기**(`int (*)[4]` 를 어떻게 읽나) — [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.
  - **감쇠 일반 규칙과 `sizeof` 함정** — [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.
  - **VLA 매개변수** — [목록의 **18번 주제**](../18-variable-length-arrays-vla/)가 정본이다. 이 문서는 던지지 않았다.
  - **배열 밖 접근 자체** — 목록의 **56번 주제**가 정본이다. 여기서는 **도구가 보는가**까지만 봤다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| `ex.c` (17-a) 연속 배치 | `sizeof` **48/16/4** · `&a[2][3]-&a[0][0]` **44** · 행 간격 **16·16** · 오프셋 **0\~44 공차 4** · `int *` 로 12칸 | gcc `-std=c17 -Wall -Wextra -pedantic` |
| `ex2.c` (17-b) 타입·보폭 | `_Generic` **일곱 답** · 보폭 **16/4/48** · `sizeof` **48·16·4·8·48** · `p[1][2]` **7** | gcc `-std=c17 -Wall -Wextra -pedantic` |
| `ex3.c` (17-c) 세 꼴 | 세 함수 **8/16/`int (*)[4]`/7** 동일 · main **48/16** · gcc **3건**(★ `-Warray-parameter=` 포함) · clang **2건** · `f_decl` 링크됨(`a[2][3]`=12) | gcc 1벌 · clang 1벌 |
| `ex4.c` (17-d) `int **` | **경고 1건 · `cc exit=0`** · gcc 는 `int (*)[4]`, clang 은 `int[3][4]` 라고 적음 · 실행 **`run exit=139`** · ★ **C23 에서도 한 글자도 같음** | gcc `-std=c17`·`-std=c2x` · clang `-std=c17`·`-std=c23` (네 벌) |
| `ex5.c` (17-e) `a[3][]` | **`cc exit=1`** · gcc **4줄**(error 2 · note 1 · warning 1) · clang **error 1건** | gcc 1벌 · clang 1벌 |
| `ex6.c` (17-f) 순회 순서 | 합 **58720256** 일치 · **행우선 < 열우선**(스무 벌 전부) · ★ **열우선 시간이 최적화에 거의 반응 안 함** | gcc `-O0`·`-O1`·`-O2` · clang `-O2` (각 5판, 스무 벌) |
| `ex7.c` (17-g) sanitizer | 평범한 실행 **`run exit=0`** · UBSan **뒤 두 줄만 잡음, `run exit=0`** · ASan **`a[3][0]` 만 잡고 `run exit=1`** · ★ `flat[4]` 는 **둘 다 침묵** | gcc 평범 · gcc `-fsanitize=undefined` · gcc `-fsanitize=address` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- **`sizeof(int)`==4 · `sizeof(int *)`==8** 이라 **48 · 16 · 4 · 44 · 8** 과 **보폭 16 · 4 · 48** 인 것.
- **순회 실험의 초와 배율** — 캐시·프리페처에 달렸다. ★ **부등호와 「안 변한다」는 성질만** 근거다.
- **`a[3][0]` 이 찍은 값** — ★ **UB 의 산물이라 아무 근거도 못 된다**(판마다 달랐다).
- **`-Warray-parameter=` 가 gcc 에만 있는 것**, **gcc 가 `int a[3][]` 에 네 줄을 내는 것** — 진단 구현의 분류다.

**연속 배치와 감쇠 결과 타입 자체는 구현 의존이 아니다.** 행 우선 · `int (*)[4]` · 세 꼴 동치 ·\
첫 차원만 생략 가능한 것은 **어느 C 구현에서도 같다.**

**안 돌려 본 것**

- **3차원 이상**(`int a[2][3][4]`) · **`int (*q)[3][4] = &a;` 로 받아 `(*q)[i][j]` 로 쓰는 꼴**.
- **`-Werror=incompatible-pointer-types`** 로 빌드를 깨는 것 · **`-fno-sanitize-recover=all`** 로 UBSan 을 죽이는 것.
- **`int flat[12]` 로 처음부터 선언하는 대안**과 **`memcpy` 로 옮기는 대안** — (7-b)의 결론은 「관용구가 UB 다」까지다.
- **VLA 매개변수**([목록의 **18번 주제**](../18-variable-length-arrays-vla/)) · **타일링으로 열우선을 구제하는 것**(알고리즘 갈래의 몫).

**버전이 올랐을 때 다시 돌려야 하는 것**

- **`-Wincompatible-pointer-types` 가 기본에서 에러로 승격됐는지** — 지금은 **경고에 `cc exit=0`** 이다.
- **clang 이 `-Warray-parameter=` 에 해당하는 진단을 갖게 됐는지** — 지금은 **gcc 만** 낸다.
- **UBSan 이 `int *` 로 행을 넘는 것을 보게 됐는지** — 지금은 **침묵**한다. ★ 이 주제에서 가장 값진 재확인 자리다.
- **`sizeof` 값과 보폭은 다른 ISA 로 갈 때** 다시 잰다.
- **연속 배치 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
