# c/syntax/34 — 함수 선언·정의·프로토타입: 「**빈 괄호는 C17 에서 「모른다」, C23 에서 「없다」**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 「**매개변수 형 목록이 없는 함수 선언자는 `void` 하나짜리 목록으로 선언한 것과 같다**」, 변경 이력의 「**식별자 목록으로 쓴 함수 정의 지원을 뺐다**」·「**빈 괄호를 `void` 와 같게 다루도록 했다**」, C99 변경 이력의 「**암시적 함수 선언을 뺐다**」, 함수 호출의 「**기본 인자 승격**」 문장, `_Noreturn` 이 **구식 기능**이 된 문장, `main` 의 두 서명 밖을 「**다른 구현 정의 방식**」에 맡긴 문장, 제약 위반에 「**적어도 하나의 진단**」을 요구하는 문장을 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **종료 코드·진단·어셈블리는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 판 격자다** — `-std=c17` 대 `-std=c2x` × **gcc-12 · gcc 13 · clang 18**, 암시적 선언은 × `c89`/`c99`/`c17`/`c2x` × `-pedantic`/`-pedantic-errors`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — **프로토타입은 C89 부터**, **암시적 함수 선언은 C99 가 뺐고**, **빈 괄호의 뜻과 옛(K&R) 정의는 C23 이 바꿨다.** `[[noreturn]]` 은 **C23**, `_Noreturn` 은 **C11**(C23 에서 구식 기능). ★ 이 판의 gcc 13 은 `-std=c23` 이 없어 **`-std=c2x`** 로 C23 을 부른다.
> ★★ **경계** — **선언을 읽는 법**(`int (*f)(int)`)은 [01번 형제](../01-declaration-syntax-and-reading/)가, **링크**(`static`·`extern`)는 [29번 형제](../29-scope-and-linkage-static-extern/)가 정본이다. **가변 인자**는 [36번 형제](../36-variadic-functions-stdarg/)가 정본이다 — 이 편과 **한 사슬**이다(기본 인자 승격).\
> ★ **헤더에 무엇을 두나**는 목록의 **44번 주제**, **`inline`** 은 목록의 **39번 주제**다.
> 선행 — [01번 형제](../01-declaration-syntax-and-reading/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 첫째 창 — 컴파일 진단의 판 격자다.** 같은 소스를 **`-std=c17` 과 `-std=c2x`** 로 던져 **`cc exit` 가 갈리는 칸**을 스크립트가 센다.
★★★ 그리고 **판 격자에 컴파일러 판(gcc-12)을 한 축 더** 넣는다 — **「C23 모드」가 컴파일러마다 다른 C23** 이었다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ★★★ ① **컴파일 진단(판 격자)** | ★ **본체** — 빈 괄호 · 옛 정의 · 암시적 선언이 **판마다 에러 / 경고 / 침묵**으로 갈린다 | 씀 |
| ② 실행 출력 | 빈 괄호 선언으로 `float` 을 넘기면 **값이 틀린다**((5)) · 판이 받아 준 소스의 실행 결과 | 씀 |
| ③ sanitizer | ★★ **탐침 4칸 중 답한 칸 0**((5)) | 씀(침묵) |
| ④ `-O2` 어셈블리 | ★★ **호출하는 쪽이 `cvtss2sd` 로 `float` 을 `double` 로 올리고 `al` 을 채운다**((6)) — 승격이 **보인다** | 씀 |
| ⑤ `-flto` | 두 번역 단위를 견주나 — **프로토타입이 있으면 잡고 없으면 못 잡는다**((5)) | 씀 |
| 시간 측정 | — | 부적용(성능 주제가 아니다) |
| ★ 제5의 상태 | 「프로토타입 없는 호출에서 인자가 무엇으로 넘어가나」를 **실행 값**으로 물으면 「틀렸다」까지만 보인다 — **어셈블리로 바꿔 물어** 「`double` 로 올려 넘긴다」를 봤다 | 창을 바꿔 답함 |

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== gcc-12 --version | sed -n 1p (cc exit=0) =====
gcc-12 (Ubuntu 12.4.0-2ubuntu1~24.04.1) 12.4.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== command -v gcc-12 gcc-13 gcc-14 gcc-15 (exit=0) =====
/usr/bin/gcc-12
/usr/bin/gcc-13
```

★ **gcc 14 는 이 머신에 없다** — 「gcc 14 가 암시적 선언을 에러로 올렸다」는 이 문서가 **확인하지 못한 것**이다(제3의 상태 — 못 잰 것).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **판 격자 전부**(`exit` · 경고 수 · 에러 수 · 「갈린 칸 N / M」) | 같은 컴파일러 · 같은 플래그면 같다 |
| 안 흔들린다 | ★★ **`half_f(v) == 1.5 ? no`** | UB 지만 **참/거짓으로 찍어** 쓰레기 값 자체를 싣지 않았다 |
| 안 흔들린다 | 어셈블리 · `-flto` 격자 · sanitizer 격자 | 같다 |

★★ **정규화 규칙은 기본 넷뿐이고, 이 편에서는 걸리는 칸이 없다** — 흔들리는 칸을 **만들지 않게** 찍었다.

## 한눈에 — 쉽게 말하면

**프로토타입은 「이 창구는 서류 두 장, 첫 장은 신청서」라고 붙인 안내문이다.**

- **안내문이 있으면** — 직원이 **서류 수와 종류를 문 앞에서** 확인한다. 틀리면 **돌려보낸다.** → **`int f(int, int);`** — 인자 수가 틀리면 **에러**
- **C17 의 빈 괄호 `int f();`** — 「**안내문이 아직 없다**」. 뭘 가져와도 받는다. 대신 **모든 서류를 표준 규격으로 접어서**(승격) 넘긴다. → **`f(1, 2)` 가 통과** · `float` 은 `double` 로
- **C23 의 빈 괄호** — 「**서류 없음**」이라는 안내문이다. 뭘 가져오면 **돌려보낸다.** → **`f(1, 2)` 는 에러**
- **안내문 없이 창구 이름만 부르기** — C89 는 「아마 `int` 를 돌려주는 창구겠지」 하고 받아 줬다. → **암시적 함수 선언** — **C99 가 뺐다**

| 비유 | 실체 | 판마다 |
|---|---|---|
| 서류 두 장 안내문 | `int f(int, int);` | 모든 판 같다 |
| 「안내문 없음」 | C17 의 `int f();` | ★★★ **`f(1, 2)` 통과** — gcc 는 경고도 0 |
| 「서류 없음」 | C23 의 `int f();` = `int f(void);` | ★★★ **`f(1, 2)` 에러**(gcc 13 · clang) · ★ **gcc-12 는 아직 옛 뜻** |
| 표준 규격으로 접기 | **기본 인자 승격** — `float` → `double`, `char`·`short` → `int` | ★★ C17 은 **두 자리**(빈 괄호 · `...`), C23 은 **한 자리**(`...`) |
| 창구 이름만 부르기 | 암시적 함수 선언 | ★★★ C89 합법 · C99 부터 없다 — **gcc 는 경고, clang 은 에러** |

```text
   int f();   f(1, 2);                          (s34a.c)

   -std=c17                                      -std=c2x
   ----------------------------------------      ----------------------------------------
   int f();  = "매개변수 정보 없음"               int f();  = int f(void)  "매개변수 없음"
   f(1, 2)   = 인자를 승격해서 그냥 넘긴다        f(1, 2)   = 인자 수가 틀렸다
   gcc 13 · gcc-12 : exit 0, 경고 0               gcc 13 · clang : exit 1  (에러 2건)
   clang           : exit 0, 경고 3               gcc-12         : exit 0  ← 아직 옛 뜻
```

- ★★★ **이 주제는 「표준 판이 바뀌어 뜻이 바뀐」 자리가 본체**다 — 다섯 층 표와 **따로** 판 경계 표를 둔다.
- ★★★ **「종료 코드 0인데 ill-formed」 후보가 가장 많은 주제**다 — 셋을 캡처했다(도구가 못 보는 것 표).
- ★★ **「UB」 칸은 하나가 두껍다** — 프로토타입 없는 선언으로 **정의와 다른 타입의 인자**를 넘기는 것.

> **프로토타입(prototype)** — 매개변수의 **수와 타입**까지 적은 함수 선언. 호출을 컴파일러가 검사하고, 인자를 **매개변수 타입으로 변환**한다.\
> 예: `double half(float x);`.

> **기본 인자 승격(default argument promotions)** — 매개변수 타입을 모르는 자리의 인자에 거는 변환. **정수 승격**을 하고 **`float` 을 `double`** 로 올린다.\
> 예: C17 에서 `double h(); h(1.5f)` 는 `double` 을 넘긴다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **빈 괄호 `f()` 는 판마다 무슨 뜻인가** — `-std=c17` 대 `-std=c2x`, 그리고 **컴파일러 판**.
2. ★★★ **프로토타입이 없으면 무엇이 일어나나** — 검사가 사라지고 **승격**이 일어난다. 그것이 **두 번역 단위를 건너면** 무엇이 되나.
3. ★★ **선언 없이 부르면** — 판마다 에러인가 경고인가 침묵인가.

## 동작 방식

### (1) ★★★ 빈 괄호와 옛 정의 — 판 격자

**언제 쓰나** — 옛 코드의 `int f();` 나 `int g(a, b) int a; int b; {…}` 를 **C23 으로 올릴 때.** ★★★ **이 편의 본체**다.

```c
/* s34v.c */
#include <stdio.h>

int f(void);                      /* void 를 적었다 */

int main(void) {
    printf("f() = %d\n", f());
    return 0;
}

int f(void) { return 42; }
```

```c
/* s34a.c */
#include <stdio.h>

int f();                          /* 괄호 안이 비었다 */

int main(void) {
    printf("f(1, 2) = %d\n", f(1, 2));
    return 0;
}

int f(int a, int b) { return a + b; }
```

```c
/* s34b.c */
#include <stdio.h>

int g(a, b)                       /* 매개변수 이름만 적고 */
    int a;                        /* 타입은 괄호 밖에서 */
    int b;
{
    return a * b;
}

int main(void) {
    printf("g(3, 4) = %d\n", g(3, 4));
    return 0;
}
```

```c
/* s34c.c */
double half();                    /* 괄호 안이 비었다 */

double half(float x) { return x / 2; }
```

```text
===== 빈 괄호와 옛 정의 — 파일 4 × 컴파일러 3 × 판 2 (exit=0) =====
파일     컴파일러 -std=c17 -pedantic         | -std=c2x -pedantic
s34v.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34v.c   gcc      exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34v.c   clang    exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34a.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 0 에러 0
s34a.c   gcc      exit=0 경고 0 에러 0       | exit=1 경고 0 에러 2
s34a.c   clang    exit=0 경고 3 에러 0       | exit=1 경고 0 에러 2
s34b.c   gcc-12   exit=0 경고 0 에러 0       | exit=0 경고 1 에러 0
s34b.c   gcc      exit=0 경고 0 에러 0       | exit=0 경고 1 에러 0
s34b.c   clang    exit=0 경고 1 에러 0       | exit=1 경고 0 에러 4
s34c.c   gcc-12   exit=1 경고 0 에러 1       | exit=1 경고 0 에러 1
s34c.c   gcc      exit=1 경고 0 에러 1       | exit=1 경고 0 에러 1
s34c.c   clang    exit=1 경고 2 에러 1       | exit=1 경고 0 에러 1
(격자 플래그 = -Wall -Wextra -pedantic -fmax-errors=0 / clang 은 -ferror-limit=0)
두 판의 종료 코드가 갈린 칸 3 / 12
```

```text
===== 같은 두 파일을 -pedantic-errors 로 — 판 c2x (exit=0) =====
s34a.c   gcc-12   -std=c2x -pedantic-errors  exit=0 경고 0 에러 0
s34a.c   gcc      -std=c2x -pedantic-errors  exit=1 경고 0 에러 2
s34a.c   clang    -std=c2x -pedantic-errors  exit=1 경고 0 에러 2
s34b.c   gcc-12   -std=c2x -pedantic-errors  exit=1 경고 0 에러 1
s34b.c   gcc      -std=c2x -pedantic-errors  exit=1 경고 0 에러 1
s34b.c   clang    -std=c2x -pedantic-errors  exit=1 경고 0 에러 4
```

그림 해설 (한 단계씩):

- ★★★ **갈린 칸 3 / 12** — `s34a` 의 gcc 13 · clang, `s34b` 의 clang. **셋 다 C17 에서 통과하고 C23 에서 막혔다.**
- ★★★ **gcc-12 의 `-std=c2x` 는 `s34a` 를 통과시킨다** — `-pedantic-errors` 로도 **`exit=0`**. **gcc 12 는 「빈 괄호 = `void`」를 아직 구현하지 않았다.** 같은 `-std=c2x` 가 **컴파일러 판마다 다른 C23** 이다.
- ★★★ **gcc 13 의 `-std=c2x` 는 옛 정의(`s34b`)를 경고 하나로 통과**시킨다 — `exit=0`. **C23 에는 그 문법이 없는데** 받아 준다. `-pedantic-errors` 라야 `exit=1`. → **「종료 코드 0인데 ill-formed」**
- ★★ **C17 의 gcc 는 `s34a`·`s34b` 에 경고 0건**이다 — `-Wall -Wextra -pedantic` 인데도. clang 은 C17 에서도 **「모든 판에서 구식이다」** 경고를 낸다.
- ★ **`s34c` 는 두 판 다 에러**다 — 그런데 **이유가 다르다**((3)).
- ★ **`s34v`(`void` 를 적은 것)는 모든 칸이 같다** — **괄호에 `void` 를 적으면 판이 상관없다.**

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=0) =====
s34a.c:3:6: warning: a function declaration without a prototype is deprecated in all versions of C [-Wstrict-prototypes]
    3 | int f();                          /* 괄호 안이 비었다 */
      |      ^
      |       void
s34a.c:6:31: warning: passing arguments to 'f' without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype]
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                               ^
s34a.c:3:5: warning: a function declaration without a prototype is deprecated in all versions of C and is treated as a zero-parameter prototype in C23, conflicting with a subsequent definition [-Wdeprecated-non-prototype]
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c:10:5: note: conflicting prototype is here
   10 | int f(int a, int b) { return a + b; }
      |     ^
3 warnings generated.
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=1) =====
s34a.c: In function ‘main’:
s34a.c:6:30: error: too many arguments to function ‘f’
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                              ^
s34a.c:3:5: note: declared here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c: At top level:
s34a.c:10:5: error: conflicting types for ‘f’; have ‘int(int,  int)’
   10 | int f(int a, int b) { return a + b; }
      |     ^
s34a.c:3:5: note: previous declaration of ‘f’ with type ‘int(void)’
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34a.c -o /dev/null (cc exit=1) =====
s34a.c:6:32: error: too many arguments to function call, expected 0, have 2
    6 |     printf("f(1, 2) = %d\n", f(1, 2));
      |                              ~ ^~~~
s34a.c:3:5: note: 'f' declared here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
s34a.c:10:5: error: conflicting types for 'f'
   10 | int f(int a, int b) { return a + b; }
      |     ^
s34a.c:3:5: note: previous declaration is here
    3 | int f();                          /* 괄호 안이 비었다 */
      |     ^
2 errors generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s34a.c -o x ; ./x (cc exit=0 · run exit=0) =====
f(1, 2) = 3
```

- ★★★ **gcc 13 `-std=c2x` 가 말하는 타입** — `previous declaration of 'f' with type 'int(void)'`. **컴파일러가 직접 「빈 괄호는 `int(void)`」라고 적었다.**
- ★★ **clang C23 의 문구** — `expected 0, have 2`. 역시 **매개변수 0개**로 읽었다.
- ★★ **clang C17 의 경고가 판 경계를 예고한다** — `is treated as a zero-parameter prototype in C23, conflicting with a subsequent definition`.
- ★ **C17 에서 돌리면 `f(1, 2) = 3`** — 옛 뜻 그대로 돈다.

비용 — **옛 코드를 C23 으로 올리면 이 자리가 전부 깨진다.** 그리고 **gcc-12 로 시험하면 안 깨진다** — 컴파일러 판까지 맞춰야 판 경계가 보인다.

### (2) ★★ 옛(K&R) 정의 — 판과 컴파일러가 따로 논다

**언제 쓰나** — 1980년대식 `int g(a, b) int a; int b; {…}` 를 만났을 때.

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=0) =====
s34b.c: In function ‘g’:
s34b.c:3:5: warning: old-style function definition [-Wold-style-definition]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic-errors -c s34b.c -o /dev/null (cc exit=1) =====
s34b.c: In function ‘g’:
s34b.c:3:5: error: old-style function definition [-Wold-style-definition]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
```

```text
===== gcc -std=c2x s34b.c -o x ; ./x (cc exit=0 · run exit=0) =====
g(3, 4) = 12
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=1) =====
s34b.c:3:7: error: unknown type name 'a'
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |       ^
s34b.c:3:10: error: unknown type name 'b'
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |          ^
s34b.c:3:12: error: expected ';' after top level declarator
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |            ^
      |            ;
s34b.c:6:1: error: expected identifier or '('
    6 | {
      | ^
4 errors generated.
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34b.c -o /dev/null (cc exit=0) =====
s34b.c:3:5: warning: a function definition without a prototype is deprecated in all versions of C and is not supported in C23 [-Wdeprecated-non-prototype]
    3 | int g(a, b)                       /* 매개변수 이름만 적고 */
      |     ^
1 warning generated.
```

- ★★★ **gcc 13 은 `-std=c2x` 에서 경고 · `-pedantic-errors` 에서 에러**다 — 같은 진단(`-Wold-style-definition`)이 **강도에 따라** 오르내린다. **경고 판은 실행까지 된다**(`g(3, 4) = 12`).
- ★★★ **clang 은 C23 에서 그 문법을 아예 모른다** — `unknown type name 'a'` 로 **선언으로 읽다 깨진다**(에러 4건). C17 에서는 **`is not supported in C23`** 경고.
- ★★ **두 컴파일러가 갈린 자리**다 — gcc 는 「있지만 C23 이 싫어하는 문법」, clang 은 「없는 문법」으로 다룬다.

### (3) ★★ 빈 괄호 선언 뒤의 `float` 정의 — 한 번역 단위 안

**언제 쓰나** — 「선언과 정의의 서명이 다르면 어떻게 되나」를 **한 파일 안에서** 물을 때.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:3:8: error: conflicting types for ‘half’; have ‘double(float)’
    3 | double half(float x) { return x / 2; }
      |        ^~~~
s34c.c:3:1: note: an argument type that has a default promotion cannot match an empty parameter name list declaration
    3 | double half(float x) { return x / 2; }
      | ^~~~~~
s34c.c:1:8: note: previous declaration of ‘half’ with type ‘double()’
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^~~~
```

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:3:8: error: conflicting types for ‘half’; have ‘double(float)’
    3 | double half(float x) { return x / 2; }
      |        ^~~~
s34c.c:1:8: note: previous declaration of ‘half’ with type ‘double(void)’
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34c.c -o /dev/null (cc exit=1) =====
s34c.c:1:12: warning: a function declaration without a prototype is deprecated in all versions of C [-Wstrict-prototypes]
    1 | double half();                    /* 괄호 안이 비었다 */
      |            ^
      |             void
s34c.c:1:8: warning: a function declaration without a prototype is deprecated in all versions of C and is treated as a zero-parameter prototype in C23, conflicting with a subsequent definition [-Wdeprecated-non-prototype]
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^
s34c.c:3:8: note: conflicting prototype is here
    3 | double half(float x) { return x / 2; }
      |        ^
s34c.c:3:8: error: conflicting types for 'half'
    3 | double half(float x) { return x / 2; }
      |        ^
s34c.c:1:8: note: previous declaration is here
    1 | double half();                    /* 괄호 안이 비었다 */
      |        ^
2 warnings and 1 error generated.
```

- ★★★ **C17 의 gcc 가 이유를 적는다** — `an argument type that has a default promotion cannot match an empty parameter name list declaration`. **빈 괄호 선언으로 부르면 `float` 이 `double` 로 올라가서 넘어오는데, 정의는 `float` 을 기다린다** — 둘이 안 맞으니 **호환되지 않는 타입**이다.
- ★★ **C23 의 gcc 는 이유가 바뀐다** — `previous declaration ... with type 'double(void)'`. 이제는 **매개변수 0개 대 1개**의 충돌이다.
- ★ **같은 에러 · 같은 `cc exit=1` · 다른 이유** — 판 격자에서 「안 갈린 칸」도 **문구를 읽어야** 판 경계가 보인다.

### (4) ★★★ 선언 없이 부르기 — 암시적 함수 선언의 판 격자

**언제 쓰나** — 헤더를 빠뜨린 채 함수를 불렀을 때.

```c
/* s34d.c */
#include <stdio.h>

int main(void) {
    printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
    return 0;
}

int sq(int x) { return x * x; }
```

```text
===== 선언 없이 부르기 — 컴파일러 3 × 판 4 × 두 강도 (-Wall -Wextra) (exit=0) =====
컴파일러 판     -pedantic              | -pedantic-errors
gcc-12   c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
gcc-12   c99    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc-12   c17    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc-12   c2x    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
gcc      c99    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c17    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
gcc      c2x    exit=0 경고 1 에러 0   | exit=1 경고 0 에러 1
clang    c89    exit=0 경고 1 에러 0   | exit=0 경고 1 에러 0
clang    c99    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
clang    c17    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
clang    c2x    exit=1 경고 0 에러 1   | exit=1 경고 0 에러 1
```

```text
   sq(3);   (위에 sq 의 선언이 없다)

   C89                                      C99 · C11 · C17 · C23
   --------------------------------------   --------------------------------------
   "int sq() 가 있다고 치자" — 합법           그런 규칙이 없다 — 진단이 필요하다
   인자는 승격해서 넘긴다                     gcc 12·13 : 경고 한 줄 · exit 0
                                             clang 18  : 에러 · exit 1
                                             (C23 의 clang 은 "모르는 이름"이라고만 한다)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=0) =====
s34d.c: In function ‘main’:
s34d.c:4:28: warning: implicit declaration of function ‘sq’ [-Wimplicit-function-declaration]
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=1) =====
s34d.c:4:28: error: call to undeclared function 'sq'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^
1 error generated.
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic -c s34d.c -o /dev/null (cc exit=1) =====
s34d.c:4:28: error: use of undeclared identifier 'sq'
    4 |     printf("sq(3) = %d\n", sq(3));  /* 이 줄 위에 sq 의 선언이 없다 */
      |                            ^
1 error generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s34d.c -o x ; ./x (cc exit=0 · run exit=0) =====
sq(3) = 9
```

그림 해설 (한 단계씩):

- ★★★ **gcc-12 와 gcc 13 은 모든 판에서 경고**다 — **C99 이후 판에서도 `-pedantic` 이면 `exit=0`**. `-pedantic-errors` 라야 에러. → **「종료 코드 0인데 ill-formed」**
- ★★★ **clang 18 은 C99 이후 판에서 에러**다 — `-pedantic` 만으로 `exit=1`. 문구가 **「C99 부터 지원하지 않는다」** 고 판을 **직접 말한다.**
- ★★ **C89 는 셋 다 `exit=0` · 경고 1** — 이 경고는 **`-Wall` 이 켠 것**이다. `-pedantic` 만 주면 gcc 는 **0건**이다(아래 블록). **C89 에서는 합법**이기 때문이다.
- ★★ **clang C23 은 문구가 바뀐다** — `use of undeclared identifier 'sq'`. C23 에서는 **암시적 선언이라는 개념 자체**가 없어 그냥 **모르는 이름**이다.
- ★ **gcc 로 통과시키면 돌기도 한다** — `sq(3) = 9`. 암시적 선언이 만든 `int sq()` 가 **우연히 맞았다.** 반환형이 `int` 가 아니었다면 틀렸을 것이다(★ **던지지 않았다**).

```text
===== gcc -std=c89 -pedantic -c s34d.c -o /dev/null (cc exit=0) =====
```

★ **gcc 14 가 이것을 에러로 올렸다는 말**이 있다 — 이 머신에 **gcc 14 가 없어**(「이 판」 절의 `command -v`) **확인하지 못했다.** gcc-12 · gcc 13 은 **둘 다 경고**였다.

비용 — **gcc 로만 빌드하는 코드는 헤더 누락이 경고 한 줄로 지나간다.** `-Werror=implicit-function-declaration` 이나 `-pedantic-errors` 가 없으면 **빌드가 통과한다.**

### (5) ★★★ 두 번역 단위 — 빈 괄호 선언으로 `float` 을 넘기면

**언제 쓰나** — 「다른 파일의 함수를 프로토타입 없이 부르면」을 물을 때. ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)의 「**`-flto` 는 두 번역 단위의 서명 불일치는 잡는다**」가 여기서 **조건이 붙는다.**

```c
/* s34e1.c */
#include <stdio.h>

double half_f();                  /* 괄호 안이 비었다 */
double half_d();

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

```c
/* s34e2.c */
double half_f(float x)  { return x / 2; }
double half_d(double x) { return x / 2; }
```

```c
/* s34e3.c */
#include <stdio.h>

double half_f(double);            /* 프로토타입을 적었다 — 정의와 다르게 */
double half_d(double);

int main(void) {
    float v = 3.0f;
    printf("half_f(v) == 1.5 ? %s\n", half_f(v) == 1.5 ? "yes" : "no");
    printf("half_d(v) == 1.5 ? %s\n", half_d(v) == 1.5 ? "yes" : "no");
    return 0;
}
```

```text
===== 두 번역 단위 — 빈 괄호 선언으로 float 을 넘긴다 (s34e1.c + s34e2.c) (exit=0) =====
--- gcc -O0 (cc exit=0 · 경고 0)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- gcc -O2 (cc exit=0 · 경고 0)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- clang -O0 (cc exit=0 · 경고 4)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
--- clang -O2 (cc exit=0 · 경고 4)
half_f(v) == 1.5 ? no
half_d(v) == 1.5 ? yes
```

```text
===== -flto 가 두 번역 단위를 견주나 — 호출 쪽 파일 2 × 컴파일러 2 × -flto 유무 (exit=0) =====
s34e1.c + s34e2.c  gcc    (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e1.c + s34e2.c  gcc    -flto   cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e1.c + s34e2.c  clang  (없음)  cc exit=0 · 경고 4 · lto-type-mismatch 0
s34e1.c + s34e2.c  clang  -flto   cc exit=0 · 경고 4 · lto-type-mismatch 0
s34e3.c + s34e2.c  gcc    (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e3.c + s34e2.c  gcc    -flto   cc exit=0 · 경고 1 · lto-type-mismatch 1
s34e3.c + s34e2.c  clang  (없음)  cc exit=0 · 경고 0 · lto-type-mismatch 0
s34e3.c + s34e2.c  clang  -flto   cc exit=0 · 경고 0 · lto-type-mismatch 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s34e3.c s34e2.c -o x (cc exit=0) =====
s34e3.c:3:8: warning: type of ‘half_f’ does not match original declaration [-Wlto-type-mismatch]
    3 | double half_f(double);            /* 프로토타입을 적었다 — 정의와 다르게 */
      |        ^
s34e2.c:1:8: note: type mismatch in parameter 1
    1 | double half_f(float x)  { return x / 2; }
      |        ^
s34e2.c:1:8: note: type ‘float’ should match type ‘double’
s34e2.c:1:8: note: ‘half_f’ was previously declared here
s34e2.c:1:8: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

```text
===== 같은 두 파일을 sanitizer 로 — 컴파일러 2 × sanitizer 2 (-O0 -g) (exit=0) =====
gcc    address    run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
gcc    undefined  run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
clang  address    run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
clang  undefined  run exit=0 리포트 0줄 | half_f(v) == 1.5 ? no|half_d(v) == 1.5 ? yes|
답한 칸 0 / 4
```

```text
   호출하는 쪽 (s34e1.c)            넘어가는 것          받는 쪽 (s34e2.c)
   ------------------------------   ----------------   ------------------------------
   double half_f();  half_f(v)  ->  v 를 double 로     double half_f(float x)
                                    올려서 넘긴다   ->  float 을 기다린다   ★ 안 맞는다
   double half_d();  half_d(v)  ->  v 를 double 로  ->  double half_d(double x)  맞는다
```

그림 해설 (한 단계씩):

- ★★★ **`half_f` 는 네 벌 다 틀린 값**이다(`== 1.5 ? no`) — 호출 쪽은 **승격된 `double`** 을 넘기고, 정의는 **`float`** 을 읽는다. **UB** 다(호환되지 않는 타입으로 부른 것).
- ★★★ **`half_d` 는 맞는다** — 승격된 타입(`double`)과 정의의 타입이 **같기** 때문이다. **빈 괄호 선언으로 부를 수 있는 정의는 「승격된 타입만 받는」 정의뿐**이다.
- ★★★ **gcc 는 경고 0건**이다 — `-Wall -Wextra -pedantic` 에서도. clang 은 **「구식이다」** 경고 4건(서명 불일치를 말한 것은 아니다).
- ★★★ **`-flto` 는 빈 괄호 쪽을 못 본다** — `s34e1` + `-flto` 는 두 컴파일러 다 **`lto-type-mismatch 0`**. **프로토타입을 적은 `s34e3`** 이라야 gcc `-flto` 가 **`type mismatch in parameter 1`** 을 낸다. clang `-flto` 는 **그것도 0**.
- ★★ **sanitizer 탐침 4칸 중 답한 칸 0** — ASan·UBSan 둘 다 조용히 **틀린 값**을 낸다.

★★★ **25편의 「`-flto` 는 서명을 본다」에 붙는 조건** — **호출 쪽에 서명이 있어야** 견줄 것이 있다. 빈 괄호 선언은 **견줄 서명이 없으므로** 「불일치」가 성립하지 않는다.

### (6) ★★ 어셈블리로 보는 승격 — 제5의 상태

**언제 쓰나** — (5)의 「올려서 넘긴다」를 **값이 아니라 명령으로** 보고 싶을 때.

```c
/* s34f.c */
double take_np();                 /* 괄호 안이 비었다 */
double take_p(float);             /* 프로토타입 */

double via_np(float v) { return take_np(v); }
double via_p(float v)  { return take_p(v); }
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s34f.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
via_np:
        endbr64
        mov     eax, 1
        cvtss2sd        xmm0, xmm0
        jmp     take_np@PLT
via_p:
        endbr64
        jmp     take_p@PLT
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s34f.c -o - 2>/dev/null | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
via_np:                                 # @via_np
# %bb.0:
        cvtss2sd        xmm0, xmm0
        mov     al, 1
        jmp     take_np@PLT                     # TAILCALL
.Lfunc_end0:
                                        # -- End function
via_p:                                  # @via_p
# %bb.0:
        jmp     take_p@PLT                      # TAILCALL
.Lfunc_end1:
                                        # -- End function
```

- ★★★ **빈 괄호 쪽(`via_np`)만 `cvtss2sd xmm0, xmm0`** 이 있다 — `float` 을 **`double` 로 바꾸는 명령**이다. 프로토타입 쪽(`via_p`)은 **바로 `jmp`** — `float` 그대로 넘긴다.
- ★★★ **빈 괄호 쪽은 `al` 도 채운다**(gcc `mov eax, 1` · clang `mov al, 1`) — x86-64 호출 규약에서 **가변 인자 함수에게 「벡터 레지스터를 몇 개 썼나」를 알려 주는 값**이다. **프로토타입 없는 호출을 가변 인자 호출처럼 번역**했다 — [36번 형제](../36-variadic-functions-stdarg/)와 **같은 번역**이다.
- ★ 이 두 줄이 「승격이 일어난다」의 **명령 수준 증거**다 — 실행 값은 「틀렸다」까지만 말했다((5)). **창을 바꿔 물은 것**이다.

### (7) ★ `static` 함수의 순서 · `main` 의 서명 · noreturn 두 꼴

**언제 쓰나** — 「정의가 아래 있는 `static` 함수를 위에서 부르면」 · 「`void main` 은 되나」 · 「`[[noreturn]]` 은 C17 에서 되나」를 물을 때.

```c
/* s34h.c */
int main(void) { return helper(); }

static int helper(void) { return 0; }
```

```c
/* s34m.c */
void main(void) { }
```

```c
/* s34m2.c */
int main(int argc, char *argv[]) {
    (void)argv;
    return argc - 1;
}
```

```c
/* s34g1.c */
#include <stdlib.h>

_Noreturn void die1(void) { exit(1); }
```

```c
/* s34g2.c */
#include <stdlib.h>

[[noreturn]] void die2(void) { exit(1); }
```

```text
===== noreturn 두 꼴 · static 함수의 순서 · main 의 서명 — 파일 5 × 컴파일러 2 × 판 2 (-Wall -Wextra -pedantic) (exit=0) =====
s34g1.c  gcc    c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34g1.c  clang  c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34g2.c  gcc    c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 0 에러 0
s34g2.c  clang  c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 0 에러 0
s34h.c   gcc    c17 exit=1 경고 2 에러 1   | c2x exit=1 경고 2 에러 1
s34h.c   clang  c17 exit=1 경고 0 에러 2   | c2x exit=1 경고 0 에러 1
s34m.c   gcc    c17 exit=0 경고 1 에러 0   | c2x exit=0 경고 1 에러 0
s34m.c   clang  c17 exit=1 경고 0 에러 1   | c2x exit=1 경고 0 에러 1
s34m2.c  gcc    c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
s34m2.c  clang  c17 exit=0 경고 0 에러 0   | c2x exit=0 경고 0 에러 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s34h.c -o /dev/null (cc exit=1) =====
s34h.c: In function ‘main’:
s34h.c:1:25: warning: implicit declaration of function ‘helper’ [-Wimplicit-function-declaration]
    1 | int main(void) { return helper(); }
      |                         ^~~~~~
s34h.c: At top level:
s34h.c:3:12: error: static declaration of ‘helper’ follows non-static declaration
    3 | static int helper(void) { return 0; }
      |            ^~~~~~
s34h.c:1:25: note: previous implicit declaration of ‘helper’ with type ‘int()’
    1 | int main(void) { return helper(); }
      |                         ^~~~~~
s34h.c:3:12: warning: ‘helper’ defined but not used [-Wunused-function]
    3 | static int helper(void) { return 0; }
      |            ^~~~~~
```

- ★★★ **`static` 함수를 선언 전에 부르면 두 컴파일러 다 에러**다 — gcc 는 **암시적 선언이 먼저 `int helper()`(외부 링크)를 만들고**, 뒤의 `static` 정의와 **링크가 충돌**한다(`static declaration ... follows non-static declaration`). [29번 형제](../29-scope-and-linkage-static-extern/)의 링크 규칙이 **여기서 에러로** 나온다. **처방은 위에 `static int helper(void);` 한 줄**이다.
- ★★ **`void main(void)` — gcc 는 경고(`exit=0`), clang 은 에러**다. 표준이 `main` 의 두 서명(`int main(void)` · `int main(int, char *[])`) 밖을 **「구현 정의 방식」에 맡겼기** 때문에 **두 구현의 선택이 갈렸다.** `int main(int argc, char *argv[])` 은 **모든 칸이 0건**이다.
- ★★ **`[[noreturn]]` 은 C17 에서 `-pedantic` 경고 · C23 에서 0건**이다 — 두 컴파일러 같다. **`_Noreturn` 은 두 판 다 0건**이다 — C23 이 **구식 기능**으로 돌렸는데도 이 판의 두 컴파일러는 **아무 말도 안 한다.**


### (8) ★ C++ 에서 빈 괄호는 처음부터 `void` 였다

**언제 쓰나** — C 와 C++ 을 오갈 때. **C23 이 C 를 C++ 쪽으로 옮겼다.**

```cpp
// s34x.cpp
int f();

int main() { return f(1, 2); }

int f(int a, int b) { return a + b; }
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s34x.cpp -o /dev/null (cc exit=1) =====
s34x.cpp: In function ‘int main()’:
s34x.cpp:3:22: error: too many arguments to function ‘int f()’
    3 | int main() { return f(1, 2); }
      |                     ~^~~~~~
s34x.cpp:1:5: note: declared here
    1 | int f();
      |     ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s34x.cpp -o /dev/null (cc exit=1) =====
s34x.cpp:3:21: error: no matching function for call to 'f'
    3 | int main() { return f(1, 2); }
      |                     ^
s34x.cpp:1:5: note: candidate function not viable: requires 0 arguments, but 2 were provided
    1 | int f();
      |     ^
1 error generated.
```

- ★★★ **C++17 에서 `int f();` 뒤의 `f(1, 2)` 는 에러**다 — g++ 가 **`int f()`** 를 **`too many arguments`** 로 막는다. **C 의 C23 과 같은 판정**이다.
- ★★ **clang++ 는 오버로드 해석의 말투**를 쓴다 — `candidate function not viable: requires 0 arguments`. C++ 에서는 **같은 이름의 다른 서명**이 따로 있을 수 있어서 「후보가 안 맞는다」로 말한다([C++ 01번 형제](../../../cpp/syntax/01-function-overloading-and-overload-resolution/)).
- ★ **C++ 은 오버로딩이 있어 서명이 곧 이름의 일부**다 — 「매개변수를 모른다」는 선언이 설 자리가 없다(★ 이 문장은 **해석**이다 — 연혁 근거를 찾아 읽지 않았다).

## 문법 — 형태와 규칙

### 형태

(1)의 `s34v.c` · (7)의 `s34m2.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 뜻 | 판 |
|---|---|---|
| `int f(void);` | ★★★ **매개변수 없음** — 모든 판에서 같다 | C89 부터 |
| `int f(int a, int b);` | 프로토타입 — 수·타입 검사, 인자를 매개변수 타입으로 변환 | C89 부터 |
| `int f();` | ★★★ C17: **매개변수 정보 없음**(승격해서 넘김) · C23: **`int f(void)`** | ★ 판에 따라 뜻이 다르다 |
| `int g(a, b) int a; int b; {…}` | 옛 정의(식별자 목록) | ★ **C23 이 뺐다** |
| `int f(int, ...);` | 가변 인자 — 뒤쪽 인자는 **기본 인자 승격**([36번 형제](../36-variadic-functions-stdarg/)) | C89 부터 |
| `static int helper(void);` | 내부 링크 함수의 **앞선 선언** | C89 부터 |
| `[[noreturn]] void die(void);` | 돌아오지 않는 함수 | C23 |
| `_Noreturn void die(void);` | 같은 뜻 | C11 · ★ C23 에서 구식 기능 |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| C23 에서 `int f();` 뒤 `f(1, 2)` | gcc 13·clang **에러** · ★ gcc-12 **`exit=0`** | ★★★ 제약 위반(C23) | (1) |
| C23 에서 옛 정의 | ★ gcc 13 **경고 · `exit=0`** · clang **에러** | ★★★ 문법 없음(C23) | (1)·(2) |
| 빈 괄호 선언 + `float` 매개변수 정의(한 파일) | **에러** · 두 판 다(이유가 다름) | ★★ 호환되지 않는 선언 | (3) |
| C99 이후 선언 없이 부르기 | ★ gcc **경고 · `exit=0`** · clang **에러** | ★★★ 제약 위반 | (4) |
| 빈 괄호 선언으로 `float` 을 넘겨 `float` 정의를 부르기(두 파일) | 경고 0(gcc) · 값이 틀림 · `-flto` 0 · sanitizer 0 | ★★★ UB | (5) |
| `static` 함수를 선언 전에 부르기 | **에러** · 두 컴파일러 | ★★ 링크 충돌 | (7) |
| `void main(void)` | gcc 경고 · clang **에러** | 구현 정의 | (7) |

### 규칙 불릿

- ★★★ **괄호가 비면 C17 은 「모른다」, C23 은 「없다」** — `int f(void)` 라고 적으면 **판이 상관없다.**
- ★★★ **프로토타입이 없으면 인자는 기본 인자 승격을 거쳐 넘어간다** — `float` → `double`, 좁은 정수 → `int`. **받는 쪽이 승격된 타입이 아니면 UB**.
- ★★★ **암시적 함수 선언은 C99 가 뺐다** — 그런데 **gcc 12·13 은 경고로만** 말한다.
- ★★ **옛 정의는 C23 이 뺐다** — gcc 13 은 **경고로만**, clang 은 **문법째 모른다.**
- ★★ **`-std=c2x` 가 무엇을 구현했는지는 컴파일러 판마다 다르다** — gcc-12 는 빈 괄호의 새 뜻이 없다.
- ★★ **`-flto` 는 두 쪽에 서명이 있어야 견준다** — 빈 괄호 쪽은 못 본다.
- ★ **`static` 함수는 쓰기 전에 선언한다** · **`main` 은 `int` 를 돌려준다** · **`[[noreturn]]` 은 C23**.

## 어디서 틀리나

### 1. ★★★ 「`int f();` 는 인자가 없는 함수다」

**C17 까지는 틀리다**((1)) — 「매개변수 정보 없음」이라 `f(1, 2)` 가 **경고 0건으로** 통과했다(gcc). **C23 부터 맞다.** 판을 적지 않고 말하면 반은 틀린다.

### 2. ★★★ 「`-std=c2x` 로 컴파일했으니 C23 으로 검증했다」

**gcc-12 는 빈 괄호의 새 뜻이 없었다**((1)). 그리고 **gcc 13 은 C23 에 없는 옛 정의를 경고로 받았다**((2)). **판 플래그는 「기본값 선택」이다** — `-pedantic-errors` 와 **컴파일러 판**까지 적어야 한다.

### 3. ★★★ 「헤더를 빠뜨리면 컴파일러가 막아 준다」

**gcc 는 경고 한 줄**이다((4)) — `exit=0`. clang 은 막는다. **빌드 로그의 경고를 안 읽으면 지나간다.**

### 4. ★★★ 「두 파일의 서명이 달라도 `-flto` 가 잡는다」

**호출 쪽이 빈 괄호면 못 잡는다**((5)). 25편의 결론은 「**양쪽에 서명이 있을 때**」의 것이다.

### 5. ★★ 「`float` 을 넘겼으니 `float` 으로 받으면 된다」

**프로토타입이 없으면 `double` 로 넘어간다**((5)·(6)) — `cvtss2sd` 가 그 명령이다.

### 6. ★ 「`static` 함수는 파일 어디서나 부를 수 있다」

**쓰기 전에 선언해야 한다**((7)). 안 하면 암시적 선언이 **외부 링크**를 만들어 충돌한다.

### 7. ★ 「`_Noreturn` 은 C23 에서 경고가 난다」

**이 판의 두 컴파일러는 0건**이다((7)). 구식 기능이 됐다는 것은 **표준 문서의 말**이고, 이 판의 도구는 아직 말하지 않는다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 판마다 다르다** — 그래서 판 경계를 **따로 표로** 세운다.

### ★★★ 판 경계 — 표준 판이 바뀌어 뜻이 바뀐 자리

| 형태 | C89 | C99·C11·C17 | C23 | 이 판의 컴파일러가 한 일 |
|---|---|---|---|---|
| `int f();` | 매개변수 정보 없음 | 매개변수 정보 없음 | ★★★ **`int f(void)`** | ★ **gcc-12 는 C23 모드에서도 옛 뜻** · gcc 13·clang 은 새 뜻 |
| 옛(K&R) 정의 | 있다 | 있다 | ★★★ **없다** | ★ **gcc 13 은 C23 에서 경고로 받음** · clang 은 문법째 모름 |
| 선언 없이 부르기 | ★ **합법**(`int` 를 돌려준다고 가정) | ★★★ **없다** | 없다 | ★ **gcc 12·13 은 경고** · clang 은 에러 |
| 기본 인자 승격이 걸리는 자리 | 빈 괄호 · `...` | ★★ **빈 괄호 · `...` 두 자리** | ★★★ **`...` 한 자리** | 빈 괄호 호출에 `cvtss2sd`((6)) |
| `[[noreturn]]` | — | — | ★ 있다 | C17 에서 `-pedantic` 경고 |
| `_Noreturn` | — | C11 부터 | ★ 구식 기능 | 두 컴파일러 0건 |

```text
   기본 인자 승격이 걸리는 자리

   C89 ~ C17                                C23
   --------------------------------------   --------------------------------------
   ① 빈 괄호로 선언된 함수의 모든 인자        ① (없다 — 빈 괄호가 void 가 됐다)
   ② ... 뒤의 인자                            ② ... 뒤의 인자
```

### 다섯 층

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다(그 판 안에서) | ★★★ 프로토타입의 검사와 변환 · **기본 인자 승격** · 판 경계 표의 세 변경 · **빈 괄호 선언과 승격 타입이 아닌 매개변수 정의는 호환되지 않는다** · `main` 의 두 서명 | 판 격자 · `cc exit` · gcc 의 `default promotion` 문구 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★ **`main` 의 다른 서명**(gcc 경고 · clang 에러) · 호출 규약의 `al`(가변 인자 번역) · ★ **어떤 제약 위반을 경고로, 어떤 것을 에러로 낼지**(표준은 「진단」만 요구한다) | `s34m.c` 두 판 · 어셈블리 · 격자 |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음**(이 편이 던진 것 중에는) | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **호환되지 않는 타입으로 함수를 부르기** — 빈 괄호 선언으로 `float` 정의를 부른 것 · 두 번역 단위의 서명 불일치 | `== 1.5 ? no` 네 벌 · sanitizer 0 / 4 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **「종료 코드 0인데 ill-formed」 셋** — ① **gcc 12·13 의 C99 이후 암시적 선언**(경고 · `exit=0`) ② **gcc 13 `-std=c2x` 의 옛 정의**(경고 · `exit=0`) ③ ★ **gcc-12 `-std=c2x` 의 `f(1, 2)`** — `-pedantic-errors` 로도 **`exit=0`**. ①②는 `-pedantic-errors` 가 잡고 **③은 아무것도 못 잡는다**(그 판이 C23 의 그 규칙을 모른다) |
| ★★ **구현 정의** | ★ **`_Noreturn` 이 구식 기능이 된 것**을 두 컴파일러 다 말하지 않는다 |
| ★★★ **UB** | ★★★ **빈 괄호 선언을 건너는 서명 불일치** — gcc 경고 0 · `-flto` 0(두 컴파일러) · **sanitizer 0 / 4** · ★★ **프로토타입이 있어도 clang `-flto` 는 0** |
| ★★ **(층을 가로지름)** | ★★ **C17 의 gcc 는 빈 괄호 호출에 `-Wall -Wextra -pedantic` 로 경고 0건** — 옛 뜻에서는 합법이라 할 말이 없다. gcc 는 같은 플래그에서 **빈 괄호를 문제 삼지 않았고**, clang 은 같은 플래그에서 **말한다** |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **「종료 코드 0」은 판 경계를 넘지 못한다** — ①②는 강도(`-pedantic-errors`)로, ③은 **컴파일러 판**으로만 드러났다.
  - ★★★ **빈 괄호는 도구의 눈을 가린다** — 검사할 서명이 없으니 컴파일러도 `-flto` 도 sanitizer 도 **견줄 것이 없다.**
  - ★★ **두 컴파일러가 가장 크게 갈린 곳은 「제약 위반을 에러로 낼까 경고로 낼까」다** — 표준은 「진단하라」까지만 정한다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 인자 없는 함수 | ★★★ **`int f(void)`** — 모든 판에서 같다 | `int f()`(C17 에서 「모른다」) |
| 다른 파일의 함수 부르기 | ★★★ **헤더의 프로토타입** | 빈 괄호 선언 · 선언 없이 부르기 |
| 헤더 누락을 빌드에서 막기 | ★★ **`-Werror=implicit-function-declaration`** 또는 `-pedantic-errors` | gcc 기본값(경고) |
| 옛 코드를 C23 으로 | ★★ **옛 정의를 프로토타입 정의로** 고치고 **빈 괄호에 `void`** | `-std=c2x` 만 바꾸기 |
| C23 검증 | ★★ **gcc 13 이상 · clang** + `-pedantic-errors` | gcc-12 `-std=c2x` |
| 돌아오지 않는 함수 | ★ C23 이면 `[[noreturn]]`, C11·C17 이면 `_Noreturn` | — |
| 파일 안 도우미 | ★ **위에 `static` 선언** | 정의를 아래 두고 위에서 부르기 |

판단 규칙 두 줄.

- ★★★ **괄호가 비었으면 `void` 를 적는다** — 그 한 낱말로 판 경계가 사라진다.
- ★★ **「몇 판에서 몇 컴파일러로 확인했나」를 같이 적는다** — 이 주제의 결론은 **판 · 컴파일러 판 · 강도** 셋에 매여 있다.

## 핵심 문장

- ★★★ **C17 의 `int f();` 는 「매개변수 정보 없음」이라 `f(1, 2)` 가 통과했고(gcc 경고 0), C23 에서는 `int f(void)` 라 gcc 13·clang 이 에러를 냈다** — 갈린 칸 3 / 12.
- ★★★ **gcc-12 의 `-std=c2x` 는 빈 괄호의 새 뜻이 없어 `-pedantic-errors` 로도 `exit=0` 이었다.**
- ★★★ **gcc 13 은 C23 에 없는 옛 정의를 경고 하나로 받았고(`exit=0`), clang 은 문법째 몰랐다.**
- ★★★ **암시적 함수 선언은 C99 가 뺐는데, gcc 12·13 은 모든 판에서 경고(`exit=0`), clang 은 C99 이후 에러였다.** gcc 14 는 이 머신에 없어 못 잰 것이다.
- ★★★ **프로토타입 없이 `float` 을 넘기면 `double` 로 올라간다** — 어셈블리의 `cvtss2sd` 와 `al` 이 그 증거이고, `float` 정의는 **틀린 값**을 받았다.
- ★★ **`-flto` 는 호출 쪽이 빈 괄호면 불일치를 못 본다** — 프로토타입을 적은 쪽만 gcc 가 잡았다. sanitizer 는 0 / 4.
- ★★ **`static` 함수를 선언 전에 부르면 암시적 선언이 외부 링크를 만들어 충돌한다.**
- ★ **C++ 은 처음부터 `f()` 가 `f(void)` 였다** — C23 이 C 를 그쪽으로 옮겼다.

## 관련 자료

- [01번 형제 — 선언 문법과 읽는 법](../01-declaration-syntax-and-reading/) — ★★ **선행.** 선언자를 읽는 법의 정본. 이 편은 **괄호 안이 무슨 뜻이냐**만 본다.
- [36번 형제](../36-variadic-functions-stdarg/) — ★★★ **같은 사슬.** 기본 인자 승격이 **가변 인자**에서 무엇을 하는지의 정본. (6)의 `al` 이 그쪽과 같은 번역이다.
- [03번 형제 — 정수 승격과 통상 산술 변환](../03-integer-promotion-and-usual-arithmetic-conversions/) · [04번 형제 — 부동소수점 타입과 변환](../04-floating-point-types-and-conversions/) — ★ 승격 규칙 자체의 정본.
- [25번 형제 — 불완전 타입과 opaque struct](../25-incomplete-types-and-opaque-struct/) — ★★ **`-flto` 가 서명은 본다**는 실측. 이 편이 「**호출 쪽에 서명이 있을 때**」라는 조건을 붙였다.
- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★ (7)의 `static` 충돌이 그 링크 규칙이다.
- 목록의 **44번 주제** — 헤더에 무엇을 두나.
- ★ **C++ 갈래** — [C++ 01번 형제 — 함수 오버로딩](../../../cpp/syntax/01-function-overloading-and-overload-resolution/). **서명이 곧 이름의 일부**인 언어.

## 용어 풀이

> **함수 선언** — 함수의 이름과 타입을 알리는 것. 몸통이 없다.\
> 예: `int f(int);`.

> **함수 정의** — 몸통까지 있는 선언. 정의는 **그 파일의 뒤쪽 호출에 대해 프로토타입 구실**도 한다.\
> 예: `int f(int a) { return a; }`.

> **프로토타입** — 매개변수의 수와 타입까지 적은 선언.\
> 예: `double half(float x);`.

> **빈 괄호 선언** — `int f();`. **C17 까지는 매개변수 정보가 없는 선언**, **C23 부터는 `int f(void)`**.\
> 예: C17 에서 `f(1, 2)` 가 통과한다.

> **옛(K&R) 정의 · 식별자 목록 정의** — 괄호에 이름만 적고 타입은 괄호 밖에 적는 정의. C23 이 뺐다.\
> 예: `int g(a, b) int a; int b; { … }`.

> **암시적 함수 선언** — 선언 없이 부르면 `int 이름()` 으로 선언된 것으로 치던 C89 규칙. C99 가 뺐다.\
> 예: `sq(3)` 위에 `sq` 선언이 없다.

> **기본 인자 승격** — 매개변수 타입을 모르는 인자에 거는 정수 승격 + `float` → `double`.\
> 예: `cvtss2sd xmm0, xmm0`.

> **`-pedantic-errors`** — 표준이 요구하는 진단을 **에러로** 내게 하는 플래그. `-pedantic` 은 경고로 낸다.\
> 예: gcc 13 `-std=c2x` 의 옛 정의가 경고 → 에러.

> **`[[noreturn]]` / `_Noreturn`** — 「이 함수는 호출자에게 돌아오지 않는다」. 앞은 C23 속성, 뒤는 C11 함수 지정자(C23 에서 구식 기능).\
> 예: `[[noreturn]] void die(void);`.

## 더 들어가면

- ★★ **gcc 14 의 암시적 선언** — 에러로 올렸다는 말이 있다. ★ **못 잰 것** — 이 머신에 없다.
- ★★ **암시적 선언이 `int` 가 아닌 반환형을 가진 함수를 부를 때** — 예: `double` 을 돌려주는 함수를 선언 없이 부르면 **반환값이 틀린다**. ★ **던지지 않았다.**
- ★ **`-Wstrict-prototypes` · `-Wold-style-definition` · `-Wmissing-prototypes`** 를 gcc C17 에 켜면 무엇이 잡히나. ★ **격자로 던지지 않았다**(gcc 13 C2x 의 `-Wold-style-definition` 만 봤다).
- ★ **`-std=c23` 을 받는 clang** — 규칙 12 에 적힌 대로 clang 18 은 `-std=c23` 도 받는다. 이 편은 두 컴파일러를 같은 플래그로 맞추려고 **`-std=c2x` 만** 썼다.
- ★ **C23 의 `f(...)` 와 `va_start(ap)`** — [36번 형제](../36-variadic-functions-stdarg/)가 판 격자로 던진다.
