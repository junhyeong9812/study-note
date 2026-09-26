# c/syntax/06 — `typedef` 와 타입 별칭: 새 타입이 아니라 별명이다 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — typedef declaration (C)](https://en.cppreference.com/w/c/language/typedef) · [cppreference — Scope](https://en.cppreference.com/w/c/language/scope) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·경고·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **이 주제의 가장 강한 근거는 「컴파일 에러」다** — `typedef` 는 런타임에 흔적이 없어서 실행 출력으로는 증명이 안 되는 것이 많다.\
> 버전이 갈리는 자리는 `-std=c89`·`-std=c17`·`-std=c2x` 로 나눠 돌렸다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> **버전** — `typedef` 는 C89 부터 같다. **같은 `typedef` 를 두 번 쓰는 것**은 C11 부터 적법하다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 결과는 컴파일·실행으로 접지했다.
> **경계** — 「선언을 안쪽→바깥으로 읽는 법」은 [01번 형제](../01-declaration-syntax-and-reading/)가 정본이다.\
> 여기는 **그 선언을 `typedef` 로 자르는 쪽**만 쓴다. 「불완전 타입과 opaque struct」의 정본은 [목록의 **25번 주제**](../25-incomplete-types-and-opaque-struct/)다.

## 한눈에 — 쉽게 말하면

**`typedef` 는 새 타입을 만들지 않는다. 이미 있는 타입에 별명을 붙일 뿐이다.**

그래서 「`MyInt` 에 `int` 를 넣으면 안 되게 하고 싶다」는 기대가 **처음부터 성립하지 않는다.**\
그리고 **텍스트 치환도 아니어서** `#define` 을 생각하고 쓰면 정확히 반대 결과가 나온다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 사람 하나에 **별명 하나 더** 붙이기 | `typedef int MyInt;` — 같은 타입, 이름 둘 |
| 별명으로 불러도 **같은 사람**이다 | `MyInt` 와 `int` 는 **완전히 같은 타입** |
| 별명을 붙였다고 **다른 사람 취급을 못 한다** | 단위 혼동(`Meters`↔`Feet`)을 **못 막는다** |
| 별명은 **이름표**이지 **문장 바꾸기**가 아니다 | `#define` 은 텍스트 치환, `typedef` 는 **타입에 붙는 이름** |
| 그래서 **수식어가 붙는 위치가 다르다** | `const String` ≠ `const char *` ★ 이 주제 최고의 함정 |
| 긴 직함을 **짧은 호칭으로** 부르기 | `char *(*f[3])(int)` 를 `CharFnPtr f[3]` 으로 |

```text
   typedef int MyInt;

   #define 이었다면              typedef 는
   +----------------------+     +----------------------+
   | "MyInt" 라는 글자를   |     | int 라는 ★ 타입에    |
   | "int" 로 바꿔 치기    |     | 이름표를 하나 더 건다  |
   | (전처리기 단계)       |     | (컴파일러가 안다)     |
   +----------------------+     +----------------------+
          텍스트가 움직인다            타입은 하나, 이름이 둘
```

- 이 그림의 차이가 실제로 드러나는 자리가 **딱 하나**인데, 그것이 `const` 다((5) 참조).
- 그 하나 때문에 **`typedef` 와 `#define` 을 같은 것으로 배우면 반드시 틀린다.**

> **타입 별칭(type alias)** — 기존 타입을 가리키는 또 하나의 이름. 새 타입이 아니다.\
> 예: `typedef int MyInt;` 뒤에 `MyInt` 와 `int` 는 컴파일러에게 **구별 불가능한 같은 타입**이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 「새 타입이 아니라 별칭」을 **무엇으로 증명**할 수 있는가 — 실행이 아니라 무엇으로?
2. `typedef` 와 `#define` 은 **어디서 갈라지는가** — 갈라지는 자리는 몇 개인가?
3. `typedef` 가 **값을 내는 자리**와 **해를 끼치는 자리**는 각각 어디인가?

## 동작 방식

### (1) 별칭이라는 것을 컴파일러가 직접 말해 준다

**언제 쓰나** — 「`MyInt` 는 `int` 와 다른 타입이겠지」라는 생각이 들 때.

`_Generic` 의 목록에 `int` 와 `MyInt` 를 **둘 다** 올려 보면 된다.

```c
typedef int MyInt;
printf("%s\n", _Generic(a, int: "int 로 잡혔다", MyInt: "MyInt 로 잡혔다"));
```

```text
gen.c: In function ‘main’:
gen.c:5:54: error: ‘_Generic’ specifies two compatible types
    5 |     printf("%s\n", _Generic(a, int: "int 로 잡혔다", MyInt: "MyInt 로 잡혔다"));
      |                                                      ^~~~~
gen.c:5:32: note: compatible type is here
```

```text
   _Generic 은 "타입마다 하나씩" 을 요구한다

   _Generic(a, int: ..., long: ...)      OK — 서로 다른 타입
   _Generic(a, int: ..., MyInt: ...)     ★ error: two compatible types
                            ^^^^^
                        컴파일러가 "같은 타입" 이라고 말한다
```

그림 해설 (한 단계씩):

- ★ **이것이 이 주제에서 가장 강한 근거**다. 「실행해 보니 같더라」가 아니라 **컴파일러가 에러로 선언**한다.
- 같은 함수를 **세 이름으로 세 번 선언**해도 통과한다.

```c
int  f(int);
MyInt f(MyInt);
AlsoInt f(AlsoInt);
int f(int x) { return x + 1; }
```

```text
_Generic(MyInt 값) -> int
_Generic(int  값)  -> int
sizeof(MyInt)=4 sizeof(int)=4
f(41) = 42  (세 번 선언했는데 컴파일됐다)
```

- 세 선언이 **같은 함수의 같은 프로토타입**으로 읽혔다. 별칭이 아니면 재선언 충돌이 났어야 한다.
- `_Generic` 은 `MyInt` 값을 넣어도 **`int`** 라고 답한다.

비용 — 없다. 컴파일만 해 보면 된다.

### (2) 별칭이라서 타입 안전을 못 준다

**언제 쓰나** — 「단위를 `typedef` 로 갈라 두면 섞이는 걸 막겠지」라고 생각할 때.

```c
typedef double Meters;
typedef double Feet;
static Meters add_m(Meters a, Meters b) { return a + b; }
Feet f = 10.0; Meters m = 3.0;
add_m(m, f);                      /* ★ 피트를 미터 자리에 */
```

```text
[-Wall -Wextra] 0 건
[-Wall -Wextra -Wconversion] 0 건
미터에 피트를 더했다: 13.0  <- 경고 한 줄 없다
```

`struct` 로 감싸면 **그때는 막힌다.**

```c
typedef struct { double v; } Meters;
typedef struct { double v; } Feet;
```

```text
unit2.c: In function ‘main’:
unit2.c:4:74: error: incompatible type for argument 2 of ‘add_m’
```

```text
   typedef double Meters;            typedef struct { double v; } Meters;
   typedef double Feet;              typedef struct { double v; } Feet;
   +--------------------------+      +--------------------------+
   | 둘 다 double 이다         |      | 둘은 ★ 서로 다른 타입이다 |
   | 섞어도 경고 0건           |      | 섞으면 컴파일 에러        |
   +--------------------------+      +--------------------------+
     별명은 구별을 못 만든다            익명 struct 는 매번 새 타입이다
```

그림 해설 (한 단계씩):

- **`typedef` 로는 단위를 못 가른다.** `-Wconversion` 까지 켜도 0건이다.
- **`struct` 로 감싸면 갈린다.** 익명 `struct` 두 개는 멤버가 같아도 **서로 다른 타입**이기 때문이다.
- 그 대가는 `.v` 를 계속 쓰는 것과, 산술 연산자를 못 쓰는 것이다.
- 「`typedef` 로 도메인 타입을 만든다」는 **문서 효과**는 있고 **강제력은 없다.** 둘을 갈라서 기대해야 한다.

비용 — `struct` 래퍼는 이 컴파일러에서 대개 최적화로 사라지지만 **이 문서에서 재 보지는 않았다.**

### (3) 태그 이름 공간과 보통 이름 공간이 다르다

**언제 쓰나** — `typedef struct Node Node;` 라는 관용구를 읽을 때.

```text
struct Node 와 Node: 1 2  같은 타입? 1
대입 후 n1.v = 2
sizeof(struct A)=4 sizeof(A)=8  <- ★ 서로 다른 타입
sa.x=7 ta.y=2.5
```

```text
   C 의 이름 공간은 여러 개다

   +------------------------+     +------------------------+
   | 태그 이름 공간          |     | 보통 이름 공간          |
   | struct/union/enum 뒤    |     | 변수·함수·typedef 이름  |
   |   struct Node          |     |   Node (typedef)       |
   |   struct A             |     |   A    (typedef)       |
   +------------------------+     +------------------------+
        ★ 서로 안 부딪힌다 — 같은 글자를 써도 다른 칸이다
```

그림 해설 (한 단계씩):

- `struct Node { ... }; typedef struct Node Node;` 에서 **두 `Node` 는 다른 칸에 산다.** 그래서 충돌이 없다.
- 극단적으로, 태그 `A` 와 typedef 이름 `A` 가 **전혀 다른 타입**을 가리켜도 컴파일된다 — `sizeof` 가 4와 8이다.
- 그러면 서로 대입은 안 된다.

```text
tag2.c:3:56: error: incompatible types when assigning to type ‘struct A’ from type ‘A’
```

- 실무 규칙: **태그와 typedef 이름을 같게 쓴다.** 같게 쓰면 이 함정이 안 생긴다.

> **태그(tag)** — `struct`·`union`·`enum` 뒤에 오는 이름. `struct Node` 의 `Node`.\
> 예: 태그는 **`struct` 를 앞에 붙여야만** 쓸 수 있고, `typedef` 이름은 그냥 쓴다.

비용 — 없다.

### (4) 불투명 타입 — 헤더에 내부를 안 보여 준다

**언제 쓰나** — 라이브러리 헤더를 설계할 때.

```c
typedef struct S S;        /* 불완전 타입의 별칭 — 이것만으로 헤더가 성립한다 */
S *make(void);
int get(S *);
```

```text
42
```

크기를 물으면 거기서 막힌다.

```text
opq2.c:2:37: error: invalid application of ‘sizeof’ to incomplete type ‘S’
```

```text
   헤더 (.h)                      구현 (.c)
   +--------------------------+   +--------------------------+
   | typedef struct S S;      |   | struct S { int v; ... }; |
   | S *make(void);           |   |                          |
   | int get(S *);            |   | 여기서만 내부가 보인다     |
   +--------------------------+   +--------------------------+
     ★ 크기를 모른다               -> 값으로 못 다루고
     -> sizeof 도 s->v 도 에러        ★ 포인터로만 다룬다
```

그림 해설 (한 단계씩):

- **`typedef struct S S;` 한 줄이면 헤더가 완성**된다. `struct S` 의 정의는 `.c` 에만 둔다.
- 대가는 **포인터로만 다뤄야 하는 것**이다 — 크기를 모르니 값으로 못 넘기고 스택에 못 놓는다.
- 그래서 `make`/`free` 짝이 따라온다(목록의 **38번 주제**).
- 정본은 [목록의 **25번 주제**](../25-incomplete-types-and-opaque-struct/). 여기서는 **`typedef` 가 그 관용구를 어떻게 가능하게 하나**까지만 본다.

비용 — 할당이 강제된다. 그 대신 **내부를 바꿔도 헤더 사용자가 다시 컴파일하지 않아도 된다.**

### (5) ★★ `const String s` 는 `const char *` 가 아니다 — 이 주제 최고의 함정

**언제 쓰나** — 포인터를 `typedef` 로 감싼 코드를 읽거나 쓸 때.

```c
typedef char *String;
const String s = buf;      /* ★ 이것이 무엇이 되나 */
s[0] = 'H';                /* 가리키는 곳은 쓸 수 있나? */
s = buf;                   /* 포인터 자체를 바꿀 수 있나? */
```

```text
cs.c: In function ‘main’:
cs.c:9:7: error: assignment of read-only variable ‘s’
    9 |     s = buf;                   /* 포인터 자체를 바꿀 수 있나? */
      |       ^
```

- **에러가 난 줄이 `s = buf;` 다.** `s[0] = 'H';` 는 **통과했다.**
- 즉 `const String s` 는 **`char * const s`** 다 — 「바꿀 수 없는 포인터, 가리키는 곳은 쓸 수 있음」.

대조로 진짜 `const char *` 를 써 보면 **에러 나는 줄이 반대로 바뀐다.**

```text
cs2.c: In function ‘main’:
cs2.c:4:10: error: assignment of read-only location ‘*s’
    4 |     s[0] = 'H';                /* 여기서 에러가 나야 "const char*" 다 */
      |          ^
```

`#define` 으로 바꾸면 **`typedef` 와 정반대**가 된다.

```text
cs4.c: In function ‘main’:
cs4.c:5:10: error: assignment of read-only location ‘*s’
    5 |     s[0] = 'H';                /* 여기서 에러가 나면 const char* 가 된 것이다 */
```

타입을 **직접 물어봐도** 같은 답이다.

```text
&s 는 char * const * -> s 는 char * const 다 ★
char * const t 도 같은 타입
```

```text
   typedef char *String;

   const String s;                 #define String char *
   = char * const s                const String s;
                                   = const char * s   (텍스트 치환)
   +--------------------------+    +--------------------------+
   | s 를 다른 데로 못 돌린다  |    | s 를 다른 데로 돌릴 수 있다|
   | s[0] 은 ★ 쓸 수 있다      |    | s[0] 은 ★ 못 쓴다         |
   +--------------------------+    +--------------------------+
          정반대다
```

그림 해설 (한 단계씩):

- **`const` 가 별칭의 「안쪽」이 아니라 「바깥」에 붙는다.** `String` 이 이미 「`char` 를 가리키는 포인터」라는\
  **하나의 타입**이고, `const` 는 그 타입 전체를 수식한다.
- 텍스트 치환이었다면 `const` 가 `char` 앞으로 들어가서 `const char *` 가 됐을 것이다 — `#define` 이 그렇게 된다.
- **이 하나가 「`typedef` 는 텍스트 치환이 아니다」의 유일하면서 결정적인 증거**다.
- 그래서 **포인터를 `typedef` 로 감추지 않는 것**이 관례다. 감추면 `const` 를 읽을 수가 없다.
- 한 줄에 여럿을 선언할 때도 갈린다.

```text
8 8 8 1
```

  `String a, b;` 는 **둘 다 포인터**(8, 8)인데 `char *c, d;` 는 **`d` 가 `char`**(1)다.\
  `*` 는 선언자마다 붙고 **별칭은 타입에 붙기** 때문이다. 이쪽은 `typedef` 가 **헷갈림을 줄이는** 드문 자리다.

비용 — 없다. 규칙을 아느냐의 문제다.

### (6) 복잡한 선언을 자르는 도구

**언제 쓰나** — 괄호가 두 겹 이상 되는 선언을 만났을 때([01번 형제](../01-declaration-syntax-and-reading/)의 결론).

```c
typedef char *CharFn(int);        /* 함수 타입 */
typedef CharFn *CharFnPtr;        /* 그 함수를 가리키는 포인터 */

CharFnPtr ft[3];                  /* == char *(*ft[3])(int) */
```

```text
typedef 로 만든 배열 == 손으로 쓴 것? 1 (크기 24 vs 24)
호출: A
qsort: 1 2 5 9
```

```text
   char *(*ft[3])(int)            CharFnPtr ft[3]
   +--------------------------+   +--------------------------+
   | 안쪽 -> 바깥으로 읽어야   |   | 두 typedef 로 잘라 놓으면 |
   | 한다 (01번 주제)         |   | 한 번에 읽힌다            |
   +--------------------------+   +--------------------------+
        같은 타입이다 — 크기 24, 서로 대입된다
```

그림 해설 (한 단계씩):

- **두 배열이 서로 대입된다.** 같은 타입이라는 뜻이다.
- `qsort` 의 비교자도 `typedef int (*Cmp)(const void *, const void *);` 로 잘라 두면\
  **`qsort(a, 4, sizeof a[0], c)`** 가 그냥 읽힌다.
- **함수 포인터는 `typedef` 가 가장 값을 내는 자리**다. 정본은 [목록의 **35번 주제**](../35-function-pointers-and-callback-tables/).

비용 — 이름이 하나 늘어난다. **괄호 두 겹 이상이면 그 값이 비용보다 크다.**

### (7) 배열 별칭을 파라미터에 쓰면 감쇠한다

**언제 쓰나** — `typedef int Row[4];` 같은 것을 함수에 넘길 때.

```c
typedef int Row[4];
static void take(Row r) {
    printf("함수 안 sizeof(r) = %zu  (Row 는 %zu)\n", sizeof r, sizeof(Row));
}
```

```text
arr.c: In function ‘take’:
arr.c:4:62: warning: ‘sizeof’ on array function parameter ‘r’ will return size of ‘int *’ [-Wsizeof-array-argument]
밖에서 sizeof(x) = 16
함수 안 sizeof(r) = 8  (Row 는 16)
호출 뒤 x[0] = 99
```

```text
   Row x;                    take(Row r)
   +----------------+        +----------------+
   | int[4] — 16바이트|  --->  | int *  — 8바이트 |
   +----------------+        +----------------+
        원본은 배열              ★ 파라미터에서는 포인터로 감쇠한다
                                 별칭으로 감춰도 감쇠는 막을 수 없다
                                 그래서 r[0]=99 가 ★ 원본을 바꾼다
```

그림 해설 (한 단계씩):

- **`Row` 라는 이름이 「배열을 통째로 넘긴다」는 인상을 주는데 실제로는 포인터가 넘어간다.**
- `sizeof r` 이 16이 아니라 8이고, `r[0] = 99` 가 **호출자의 배열을 바꾼다.**
- gcc 가 `-Wsizeof-array-argument` 로 잡아 준다(**플래그 없이도 켜져 있다**).
- **별칭이 사실을 가린 사례**다 — (5)와 성질이 같다.
- 감쇠 규칙 자체의 정본은 [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/).

비용 — 없다. **배열 별칭을 파라미터에 안 쓰면 된다.**

## 문법 — 형태와 규칙

### 형태 — 선언에서 이름을 읽는다

```c
typedef int MyInt;                      /* MyInt 가 int 의 별칭 */
typedef char *String;                   /* String 이 char* 의 별칭 */
typedef struct Node Node;               /* 태그와 같은 이름을 써도 된다 */
typedef struct { double v; } Meters;    /* 익명 struct 에 이름 주기 */
typedef int (*Cmp)(const void *, const void *);   /* 함수 포인터 */
typedef int Row[4];                     /* 배열 */
typedef void (*Handler)(int);           /* 시그널 핸들러 */
```

★ **읽는 법은 하나다 — 앞의 `typedef` 를 지우고 보통 선언으로 읽은 뒤,\
그 선언이 만들었을 「변수 이름」 자리에 있는 것이 별칭 이름이다.**

```text
   typedef int (*Cmp)(const void *, const void *);
   |------|
   지운다

   int (*Cmp)(const void *, const void *);
          ^^^
          보통 선언이었다면 Cmp 라는 "변수" 를 만들었을 것이다
          -> 그 변수의 타입이 Cmp 라는 별칭의 뜻이다
             (01번 주제의 안쪽->바깥 읽기 그대로)
```

### 금지 사례 — 걸리는 것과 안 걸리는 것

```c
/* (1) 저장 클래스를 두 개 쓴다 -> 에러 */
typedef static int Bad;

/* (2) 가린 뒤 타입으로 쓴다 -> 에러 */
typedef int T;
int main(void) { int T = 5; T x = 1; }

/* (3) 단위를 typedef 로 가른다 -> ★ 안 걸린다 */
typedef double Meters; typedef double Feet;

/* (4) 포인터를 typedef 로 감춘 뒤 const -> ★ 안 걸린다. 뜻만 바뀐다 */
typedef char *String; const String s;

/* (5) 배열 별칭을 파라미터에 -> 경고만, 감쇠는 그대로 */
typedef int Row[4]; void f(Row r);
```

(1)과 (2)의 출력이다.

```text
sc.c:1:1: error: multiple storage classes in declaration specifiers
    1 | typedef static int Bad;
      | ^~~~~~~
```

```text
shadow2.c: In function ‘main’:
shadow2.c:2:30: error: expected ‘;’ before ‘x’
    2 | int main(void) { int T = 5; T x = 1; return x + T; }
      |                              ^~
```

- ★ **`typedef` 는 문법상 `static`·`extern` 과 같은 칸**(저장 클래스 지정자)에 온다. 그래서 둘을 같이 못 쓴다.\
  [01번 형제](../01-declaration-syntax-and-reading/)가 「저장 클래스 지정자는 타입이 아니다」로 적어 둔 그 칸이다.
- (2)의 에러 문구가 **`expected ‘;’ before ‘x’`** 인 것이 핵심이다 — 컴파일러가 `T` 를 **더 이상 타입으로 안 보고** 있다.\
  **파서 단계에서 이름의 뜻이 바뀐다**는 증거다.

### 규칙 불릿

- `typedef` 는 **새 타입을 만들지 않는다.** `_Generic` 이 `two compatible types` 에러로 그것을 말해 준다.
- **문법상 저장 클래스 지정자**다 — `static` 과 같이 못 쓴다. 하지만 저장 기간은 안 바꾼다.
- **별칭은 타입에 붙는다.** 그래서 `const String` 은 `char * const` 이고 `const char *` 가 **아니다.**
- `#define` 은 텍스트 치환이라 **`const` 의 위치가 정반대**가 된다.
- **태그 이름 공간과 보통 이름 공간이 다르다.** `typedef struct S S;` 가 그래서 가능하다.
- `typedef struct S S;` 만으로 **불완전 타입의 별칭**이 되고, 그것이 불투명 타입의 기반이다.
- **배열 별칭도 파라미터에서 감쇠한다.** 별칭이 감쇠를 막지 못한다.
- 같은 타입으로 **같은 `typedef` 를 두 번** 쓰는 것은 **C11 부터** 적법하다.
- **`typedef` 이름은 스코프를 따른다.** 안쪽 블록에서 같은 이름의 변수를 선언하면 가려진다.

## 어디서 틀리나

### 1. `#define` 처럼 읽는다

- **`const String s` 가 최고의 함정**이다. `typedef` 와 `#define` 이 **정반대**의 결과를 낸다.
- 실측: `typedef` 쪽은 `s = buf;` 에서 에러, `#define` 쪽은 `s[0] = 'H';` 에서 에러.
- 반대로 `String a, b;` 는 `typedef` 쪽이 옳다 — `#define` 이면 `b` 가 `char` 가 된다.

### 2. 「별칭으로 타입 안전을 얻었다」고 생각한다

- `Meters` 에 `Feet` 를 넣어도 **`-Wconversion` 까지 켜서 0건**이다.
- 강제력이 필요하면 **`struct` 로 감싼다.** 그러면 컴파일 에러가 난다.
- `typedef` 는 **문서**이지 **검사**가 아니다.

### 3. 포인터를 `typedef` 로 감춘다

- `const` 가 안 읽히고((5)), 함수 시그니처에서 **역참조 깊이**가 안 보인다.
- 관례: **포인터를 감추지 않는다.** 예외는 **불투명 핸들**처럼 내부를 일부러 감출 때뿐이다.
- 표준 라이브러리도 그렇다 — `FILE *` 은 `FILE` 을 `typedef` 하고 **`*` 는 노출**한다.

### 4. 배열 별칭을 파라미터에 쓴다

- `Row r` 은 `int *r` 이다. `sizeof r` 이 16이 아니라 **8**이다.
- 이름만 보면 배열이 통째로 복사될 것 같은데 **원본이 바뀐다**(`x[0]` 이 99가 됐다).

### 5. 태그와 별칭 이름을 다르게 쓴다

- `struct A` 와 typedef `A` 가 **서로 다른 타입**일 수 있다 — `sizeof` 가 4와 8이었다.
- 대입하면 `incompatible types when assigning to type ‘struct A’ from type ‘A’` 다.
- **같은 이름을 쓰는 것이 관례**인 이유가 이것이다.

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★ **이 주제는 특이하게 거의 전부가 「표준」 층이다.** `typedef` 는 **런타임에 흔적이 없어서**\
구현이 고를 여지가 없기 때문이다. 대신 **「도구가 못 보는 것」이 다른 뜻으로 많다** —\
도구가 **막지 않는 것**(단위 혼동·감쇠)이 이 주제의 값이 나오는 자리다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | `typedef` 가 **새 타입을 안 만드는 것** · 저장 클래스 지정자 칸에 오는 것 · **별칭이 타입에 붙어** `const String` 이 `char * const` 가 되는 것 · 태그와 보통 이름 공간이 다른 것 · 불완전 타입의 별칭이 되는 것 · **배열 별칭도 파라미터에서 감쇠**하는 것 · 스코프·가리기 규칙 | `_Generic` 에러 · 함수 3중 선언 · `const` 두 벌의 에러 위치 · `sizeof` 16↔8 | **단위 혼동을 아무 플래그도 안 잡는다**(0건) |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** | — | — |
| **구현 정의** | 문서화 의무가 있다 | 별칭이 가리키는 **바탕 타입 자체**의 성질(`sizeof(MyInt)`=4 는 `int` 가 4라서다 — 별칭의 성질이 아니다) | `sizeof` | — |
| **미명시** | 몇 가지 중 하나 | **해당 없음** | — | — |
| **UB** | 아무 일이나 | **해당 없음** — `typedef` 자체로는 UB 를 만들 수 없다 | — | — |

### 「버전」이 갈리는 자리 — 같은 `typedef` 를 두 번

```text
(비면 0건)
re.c:2:13: warning: redefinition of typedef ‘T’ [-Wpedantic]
    2 | typedef int T;          /* 같은 타입이면 OK (C11) */
      |             ^
re.c:1:13: note: previous declaration of ‘T’ with type ‘T’ {aka ‘int’}
```

- 위쪽이 **`-std=c17 -pedantic`**(0건), 아래쪽이 **`-std=c89 -pedantic`**(1건)이다.
- **C11 부터** 같은 타입이면 재정의가 적법하다. 헤더가 서로를 include 할 때 실제로 도움이 된다.
- ★ **`-pedantic` 없이는 어느 표준에서도 조용하다.** 「`-std=c89` 로 컴파일했으니 C89 코드」가 아니다.

### 이 주제에서 「출력」이란 무엇인가

- `typedef` 는 **기계어에 흔적을 안 남긴다.** 그래서 실행 출력으로는 「같은 타입이다」를 증명할 수 없다.
- 이 문서의 근거는 **세 가지**다.
  - **컴파일 에러** — `_Generic ... two compatible types` · `assignment of read-only variable` 의 **줄 위치**.
  - **컴파일 성공** — 세 이름으로 한 함수를 선언한 것이 통과한 것.
  - **경고 개수** — 단위 혼동에서 **0건**이 나온 것.
- ★ **「에러가 난 줄 번호」가 이 주제의 주된 관측값**이다. 「에러가 났다」가 아니라 「**어느 줄에서 났나**」가 답을 가른다((5)).

## 언제 쓰고 언제 안 쓰나

| 상황 | `typedef` 를 쓴다 | 안 쓴다 |
|---|---|---|
| 함수 포인터 | **쓴다** — 괄호가 두 겹이다 | — |
| 괄호 두 겹 이상인 선언 | **쓴다** | — |
| 불투명 핸들(`typedef struct S S;`) | **쓴다** | — |
| `struct` 에 짧은 이름 주기 | **쓴다**(태그와 같은 이름으로) | — |
| 고정폭 정수(`int32_t` 류) | 표준 것을 **쓴다** | 직접 만들기 |
| 포인터 감추기(`typedef char *String`) | — | **안 쓴다** — `const` 가 안 읽힌다 |
| 단위·도메인 구분 | — | **안 쓴다** — 강제력이 없다. `struct` 래퍼를 쓴다 |
| 배열(파라미터로 넘길 것) | — | **안 쓴다** — 감쇠를 감춘다 |
| 기본 타입에 짧은 별명(`typedef unsigned u;`) | — | **안 쓴다** — 읽는 사람이 한 번 더 찾아야 한다 |

판단 규칙 두 줄.

- **`typedef` 는 「읽기 어려운 선언」을 고치는 도구**다. 읽기 쉬운 것을 더 짧게 만들려고 쓰면 손해다.
- **감추면 안 되는 것 셋 — `*`·배열·`const`.** 감추면 읽는 사람이 사실을 못 본다.

## 핵심 문장

- `typedef` 는 **새 타입을 만들지 않는다.** `_Generic` 에 `int` 와 `MyInt` 를 같이 올리면\
  **`error: ‘_Generic’ specifies two compatible types`** 로 **컴파일러가 직접 말해 준다.**
- **텍스트 치환이 아니다.** `typedef char *String;` 뒤의 `const String s` 는 **`char * const`** 이고,\
  같은 것을 `#define` 으로 하면 **`const char *`** 가 된다 — **에러가 나는 줄이 서로 반대**다.
- **별칭은 타입 안전을 못 준다.** `Meters` 자리에 `Feet` 를 넣어도 `-Wconversion` 까지 **0건**이다.\
  강제하려면 **`struct` 로 감싼다**(그러면 컴파일 에러).
- **태그 이름 공간과 보통 이름 공간이 다르다.** 그래서 `typedef struct S S;` 가 되고, 불투명 타입이 거기서 나온다.
- **배열 별칭도 파라미터에서 감쇠한다** — `sizeof` 가 16이 아니라 8이고 원본이 바뀐다.
- **`typedef` 는 문법상 저장 클래스 지정자**다 — `typedef static int Bad;` 는 `multiple storage classes` 에러다.
- 이 주제의 관측값은 「**에러가 난 줄 번호**」다. `typedef` 는 기계어에 흔적을 안 남긴다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 06번)
- [`01-declaration-syntax-and-reading/`](../01-declaration-syntax-and-reading/) — **그쪽은 「`char *(*f[3])(int)` 를 안쪽→바깥으로 읽는 법」까지, 여기는 「그것을 `typedef` 로 자르는 법」부터.** 「괄호 두 겹이면 자른다」는 판단 기준이 거기 있다
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — `int32_t`·`size_t` 가 전부 `typedef` 다. **그쪽은 「어느 타입을 고르나」까지, 여기는 「그 별칭이 무엇인가」부터**
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — 별칭이 `const` 를 감추면, 그것을 캐스트로 떼는 코드가 따라온다
- [목록의 **16번 주제**](../16-array-pointer-decay-and-function-parameters/) (배열-포인터 감쇠) — (7)의 감쇠 규칙 정본
- [목록의 **21번 주제**](../21-struct-declaration-initialization-and-designated-initializers/) (구조체 선언·초기화) — `typedef struct { ... } T;` 의 정본
- [목록의 **25번 주제**](../25-incomplete-types-and-opaque-struct/) (불완전 타입과 opaque struct) — (4)가 정본으로 다뤄지는 곳
- [목록의 **31번 주제**](../31-const-and-pointer-const-placement/) (`const` 와 포인터 const 위치) — (5)의 `char * const` ↔ `const char *` 정본
- [목록의 **35번 주제**](../35-function-pointers-and-callback-tables/) (함수 포인터와 콜백 테이블) — (6)이 정본으로 다뤄지는 곳
- 목록의 **40번 주제** (`_Generic`) — 이 문서의 주된 증명 도구
- 목록의 **42번 주제** (함수형 매크로의 함정) — `#define` 쪽의 정본

## 용어 풀이

- **`typedef`** — 기존 타입에 별명을 붙이는 선언. **새 타입을 만들지 않는다.** 문법상 저장 클래스 지정자 칸에 온다.
- **타입 별칭(type alias)** — `typedef` 가 만든 이름. 바탕 타입과 **완전히 같은 타입**이다.
- **호환 타입(compatible type)** — 컴파일러가 같은 것으로 취급하는 타입. `_Generic` 은 호환 타입 두 개를 목록에 못 올린다.
- **태그(tag)** — `struct`·`union`·`enum` 뒤의 이름. **보통 이름 공간과 다른 칸**에 산다.
- **이름 공간(name space)** — 같은 글자가 충돌하지 않고 공존할 수 있는 칸. C 에는 태그·레이블·구조체 멤버·그 밖 넷이 있다.
- **불완전 타입(incomplete type)** — 크기를 모르는 타입. `struct S;` 만 선언한 상태. `sizeof` 를 못 쓴다.
- **불투명 타입(opaque type)** — 내부를 감춘 타입. 헤더에 `typedef struct S S;` 만 두는 관용구.
- **감쇠(decay)** — 배열이 첫 원소를 가리키는 포인터로 바뀌는 것. 함수 파라미터에서 **언제나** 일어난다.
- **`_Generic`** — C11 의 타입별 분기 식. 이 문서에서 **「같은 타입인가」를 묻는 도구**로 썼다.
- **저장 클래스 지정자(storage-class specifier)** — `static`·`extern`·`auto`·`register`·`typedef`. 선언에 **하나만** 올 수 있다.

---

## 더 들어가면

- **`typedef` 는 저장 기간을 안 바꾼다.** 문법 칸만 같이 쓸 뿐이다.\
  `typedef` 로 선언한 이름은 **객체가 아니라 타입**이라 저장 기간이라는 말 자체가 안 붙는다.

- ★ **`typedef` 이름 때문에 C 의 파싱이 문맥 의존이 된다.** `T * x;` 라는 줄은\
  `T` 가 타입이면 **선언**이고, 변수면 **곱셈 식**이다. 같은 글자가 두 가지로 읽힌다.\
  (2)의 실측 에러 `expected ‘;’ before ‘x’` 가 그 증거다 — `T` 가 변수가 되자 파서가 선언으로 못 읽었다.\
  이것을 **lexer hack** 이라고 부른다. 이 문서에서는 **에러 하나로만 관찰했고** 파서 내부는 안 봤다.

- **표준 라이브러리는 포인터를 감추지 않는다.** `FILE`·`DIR` 은 `typedef` 인데 **`*` 는 노출**한다\
  (`FILE *fp`). 감추는 쪽은 POSIX 의 `pthread_t` 처럼 **내부를 아예 안 보여 주는** 것들이다.

- **C23 에 `typeof` 가 들어왔다.** `typeof(expr)` 로 식의 타입을 그대로 쓰는 것인데,\
  `typedef` 와 달리 **이름을 안 만든다.** 던져서 확인했다 — `-std=c2x -pedantic` 은 **경고 없이 통과**하고,\
  `-std=c17` 은 **`warning: implicit declaration of function ‘typeof’`** 를 낸다(함수 호출로 읽힌다).

- ★ **태그 없는 익명 `struct` 는 자기 자신을 가리키는 멤버를 못 만든다.** 연결 리스트 노드가 태그를 갖는 이유다.\
  그런데 **에러가 안 나서** 더 고약하다 — 던져서 확인했다.

```c
typedef struct { int v; struct Node *next; } Node;   /* 태그 없는 익명 struct */
Node a, b;
a.next = &b;
```

```text
selfref3.c:2:54: warning: assignment to ‘struct Node *’ from incompatible pointer type ‘Node *’ [-Wincompatible-pointer-types]
```

  선언 자체는 **경고 하나 없이 통과**한다. `struct Node` 가 그 자리에서 **새 불완전 타입으로 생겨** 버리기 때문이다.\
  그래서 `next` 는 **영원히 정의되지 않을 다른 타입**을 가리킨다. 태그를 붙이면(`typedef struct Node {...} Node;`)\
  같은 코드가 **0건**으로 통과한다. **(3)의 「태그와 이름을 같게 쓴다」가 여기서도 답이다.**
