# c/syntax/06 — `typedef` 와 타입 별칭: 새 타입이 아니라 별명이다 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 플래그는 `-std=c17 -Wall -Wextra`. 표준 버전이 갈리는 답은 그 자리에 어느 `-std` 인지 밝혔다.
> ★ **이 주제의 관측값은 대개 「에러가 난 줄 번호」다.** `typedef` 는 기계어에 흔적을 안 남긴다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `_Generic` 에 둘을 같이 올리면 ★

**출력**

```text
gen.c: In function ‘main’:
gen.c:5:54: error: ‘_Generic’ specifies two compatible types
    5 |     printf("%s\n", _Generic(a, int: "int 로 잡혔다", MyInt: "MyInt 로 잡혔다"));
      |                                                      ^~~~~
gen.c:5:32: note: compatible type is here
    5 |     printf("%s\n", _Generic(a, int: "int 로 잡혔다", MyInt: "MyInt 로 잡혔다"));
```

**무엇이 찍히나**

- **아무것도 안 찍힌다. 컴파일이 안 된다.**
- 「어느 쪽으로 잡히나」를 물었는데, 컴파일러가 「**그 질문 자체가 성립하지 않는다**」고 답했다.

**어떻게 증명이 되나**

```text
   _Generic 은 "타입마다 하나씩" 을 요구한다

   _Generic(a, int: ..., long: ...)      OK  — 서로 다른 타입
   _Generic(a, int: ..., MyInt: ...)     ★ error: two compatible types
                            ^^^^^
                        "이 둘은 같은 타입이다" 라는 컴파일러의 선언
```

- ★ **이것이 이 주제에서 가장 강한 근거다.** 실행 결과를 관찰한 것이 아니라 **컴파일러가 판정을 말로 했다.**
- 「돌려 보니 값이 같더라」는 우연일 수 있지만, `two compatible types` 는 **타입 시스템의 판정**이다.

**두 줄로 선언하면**

```text
_Generic(MyInt 값) -> int
_Generic(int  값)  -> int
sizeof(MyInt)=4 sizeof(int)=4
f(41) = 42  (세 번 선언했는데 컴파일됐다)
```

- **통과한다.** 세 번 선언해도 된다 — **같은 함수의 같은 프로토타입**으로 읽힌다.
- `_Generic` 은 `MyInt` 값을 넣어도 **`int`** 라고 답한다. 목록에 `MyInt` 를 안 넣으면 `int` 가지를 탄다.

**무엇이 근거인가**

- **컴파일 에러(1번)와 컴파일 성공(3중 선언)** 이다.
- `typedef` 는 런타임에 아무 흔적도 안 남기므로 **실행 출력으로는 이 주제를 증명할 수 없다.**

### 2. `typedef char *String;` 뒤의 `const` ★★★

**출력**

```text
cs.c: In function ‘main’:
cs.c:9:7: error: assignment of read-only variable ‘s’
    9 |     s = buf;                   /* 포인터 자체를 바꿀 수 있나? */
      |       ^
```

**어느 줄에서 에러가 나나**

- **(b) `s = buf;` 에서 난다.** (a) `s[0] = 'H';` 는 **통과한다.**
- 줄 번호 9가 (b)이고, 문구가 **`read-only variable ‘s’`** — 읽기 전용인 것은 **`s` 자체**다.

**무슨 타입인가**

```text
   const String s;

   String   = char *              (이미 "char 를 가리키는 포인터" 라는 한 타입)
   const    = 그 타입 전체를 수식

   -> char * const s
      "바꿀 수 없는 포인터, 가리키는 곳은 쓸 수 있음"

   ★ const char * 가 아니다 (정반대에 가깝다)
```

- **`char * const`** 다. `const char *` 가 **아니다.**
- `const` 가 별칭의 **안쪽으로 파고들지 않는다.** 별칭은 이미 완성된 하나의 타입이고, `const` 는 그것을 밖에서 수식한다.

**`_Generic` 으로 물어보면**

```text
&s 는 char * const * -> s 는 char * const 다 ★
char * const t 도 같은 타입
```

- `&s` 의 타입이 **`char * const *`** 다. 그러므로 `s` 는 `char * const` 다.
- 손으로 쓴 `char * const t` 와 **같은 가지**로 잡혔다 — 완전히 같은 타입이라는 확인이다.

**진짜 `const char *` 였다면**

```text
cs2.c: In function ‘main’:
cs2.c:4:10: error: assignment of read-only location ‘*s’
    4 |     s[0] = 'H';                /* 여기서 에러가 나야 "const char*" 다 */
      |          ^
```

- **에러가 (a)로 옮겨 간다.** 그리고 문구가 `read-only variable ‘s’` 가 아니라 **`read-only location ‘*s’`** 다.
- ★ **진단 문구 하나가 두 타입을 가른다** — `variable ‘s’` 냐 `location ‘*s’` 냐.

### 3. 같은 것을 `#define` 으로 하면 ★★

**출력**

```text
cs4.c: In function ‘main’:
cs4.c:5:10: error: assignment of read-only location ‘*s’
    5 |     s[0] = 'H';                /* 여기서 에러가 나면 const char* 가 된 것이다 */
      |          ^
```

**어느 줄에서 나나**

- **(a) `s[0] = 'H';`** 다. 2번과 **정반대**다.

**왜 다른가**

```text
   #define String char *                typedef char *String;
   const String s;                      const String s;
       |                                    |
       | 전처리기가 글자를 바꾼다             | 컴파일러가 타입에 수식어를 붙인다
       v                                    v
   const char * s                       char * const s
   +--------------------------+         +--------------------------+
   | s 는 바꿀 수 있다          |         | s 를 못 바꾼다            |
   | s[0] 은 ★ 못 쓴다         |         | s[0] 은 ★ 쓸 수 있다      |
   +--------------------------+         +--------------------------+
```

- `#define` 은 **텍스트 치환**이라 `const` 가 `char` 앞으로 들어간다.
- `typedef` 는 **타입에 붙은 이름**이라 `const` 가 타입 전체를 수식한다.
- ★ **이 하나가 「`typedef` 는 텍스트 치환이 아니다」의 결정적 증거**다.

**여러 개 선언하면**

```text
#define : sizeof a=8 b=1
typedef : sizeof c=8 d=8
```

- `#define String char *` 뒤의 `String a, b;` 는 `char *a, b;` 가 되어 **`b` 가 `char`**(1바이트)다.
- `typedef` 쪽은 **둘 다 포인터**(8, 8)다.
- 경고는 **0건**이다. 어느 쪽도 컴파일러가 말려 주지 않는다.

**이긴 자리와 진 자리**

| 자리 | `typedef` | `#define` | 어느 쪽이 덜 놀라운가 |
|---|---|---|---|
| `const X s` | `char * const` | `const char *` | **`#define`** (기대대로) |
| `X a, b;` | 둘 다 포인터 | `b` 가 `char` | **`typedef`** (기대대로) |

- ★ **둘 다 한 번씩 놀라게 한다.** 그래서 「`typedef` 가 항상 낫다」도 「`#define` 이 직관적이다」도 틀렸다.
- 실무 결론은 **「포인터를 별칭으로 감추지 않는다」** 하나다. 그러면 두 함정이 다 사라진다.

### 4. 태그와 별칭이 다른 것을 가리키면

**출력**

```text
struct Node 와 Node: 1 2  같은 타입? 1
대입 후 n1.v = 2
sizeof(struct A)=4 sizeof(A)=8  <- ★ 서로 다른 타입
sa.x=7 ta.y=2.5
```

**컴파일은 되나**

- **된다.** 경고도 없다.

**두 `sizeof`**

- `sizeof(struct A)` = **4**(`int` 하나) · `sizeof(A)` = **8**(`double` 하나).
- 같은 글자 `A` 가 **완전히 다른 두 타입**을 가리키고 있다.

```text
   +------------------------+     +------------------------+
   | 태그 이름 공간          |     | 보통 이름 공간          |
   |   struct A { int x; }  |     |   A = struct{double y;}|
   |   sizeof = 4           |     |   sizeof = 8           |
   +------------------------+     +------------------------+
        ★ 같은 글자, 다른 칸, 다른 타입
```

**(c)는**

```text
tag2.c:3:56: error: incompatible types when assigning to type ‘struct A’ from type ‘A’
```

- **에러다.** 문구가 `type ‘struct A’ from type ‘A’` 인데, **눈으로는 같은 이름으로 보인다.**\
  진단 메시지조차 구별하기 어렵게 생겼다.

**없애는 관례**

- **태그와 `typedef` 이름을 같게 쓴다.**

```c
struct Node { int v; };
typedef struct Node Node;      /* 또는 typedef struct Node { int v; } Node; */
```

- 같게 쓰면 `struct Node` 와 `Node` 가 **같은 타입을 가리키고**, 실측에서 서로 대입됐다(`대입 후 n1.v = 2`).
- 이름 공간이 다르므로 **충돌하지 않는다.** 그것이 이 관용구가 가능한 이유다.

### 5. 배열 별칭을 파라미터에

**출력**

```text
arr.c: In function ‘take’:
arr.c:4:62: warning: ‘sizeof’ on array function parameter ‘r’ will return size of ‘int *’ [-Wsizeof-array-argument]
    4 |     printf("함수 안 sizeof(r) = %zu  (Row 는 %zu)\n", sizeof r, sizeof(Row));
      |                                                              ^
arr.c:3:22: note: declared here
    3 | static void take(Row r) {           /* ★ 파라미터에 쓰면? */
      |                  ~~~~^
밖에서 sizeof(x) = 16
함수 안 sizeof(r) = 8  (Row 는 16)
호출 뒤 x[0] = 99
```

**두 `sizeof`**

- 밖에서 **16**(`int[4]`) · 함수 안에서 **8**(`int *`).
- **같은 줄에서 `sizeof(Row)` 는 여전히 16**이다 — 타입에 물으면 배열이고, **파라미터 변수에 물으면 포인터**다.\
  이 대비가 한 줄에 들어 있는 것이 이 실험의 값이다.

**원본이 바뀌나**

- **바뀐다.** `호출 뒤 x[0] = 99`.
- 배열이 복사된 것이 아니라 **주소가 넘어갔다.**

**경고**

- **`-Wsizeof-array-argument`** 이고 **`-Wall`** 에 들어 있다.
- gcc 가 `declared here` 로 파라미터 선언까지 짚어 준다.

**별칭이 감쇠를 막나**

```text
   Row x;                     take(Row r)
   +------------------+       +------------------+
   | int[4] — 16바이트 |  --->  | int *  — 8바이트  |
   +------------------+       +------------------+
      "Row 를 넘긴다" 고 썼는데   ★ 별칭은 감쇠를 막지 못한다
                                 이름이 사실을 가렸을 뿐이다
```

- **못 막는다.** 감쇠는 **파라미터 선언의 규칙**이지 타입 이름의 문제가 아니다.
- 2번의 `const` 와 **성질이 같다** — 별칭이 「무슨 일이 일어나는지」를 가렸다.
- 정본은 목록의 **16번 주제**.

### 6. 불투명 타입

**출력**

```text
42
```

```text
opq2.c:2:37: error: invalid application of ‘sizeof’ to incomplete type ‘S’
    2 | int main(void) { return (int)sizeof(S); }
      |                                     ^
```

**헤더가 성립하나**

- **성립한다.** `typedef struct S S;` 한 줄이면 `S *` 와 `S` 를 쓰는 선언을 다 쓸 수 있다.
- 실측에서 `struct S` 의 정의를 **뒤에** 두고도 컴파일·실행이 됐다(`42`).

**`sizeof(S)` 를 쓰면**

- **`invalid application of ‘sizeof’ to incomplete type ‘S’`** 에러다.
- `s->v` 도 같은 이유로 막힌다. **크기도 멤버도 모른다.**

**어떻게만 다루나**

```text
   헤더 쪽에서 할 수 있는 것        할 수 없는 것
   +----------------------+        +----------------------+
   | S *p;      (포인터)   |        | S v;      (값)        |
   | f(S *);              |        | sizeof(S)            |
   | S *make(void);       |        | p->member            |
   +----------------------+        +----------------------+
       ★ 포인터로만 다룬다            -> 생성/해제 함수가 따라온다
```

- **포인터로만** 다룬다. 값으로 못 넘기고 스택에 못 놓는다.
- 그래서 `make`/`destroy` 짝이 API 에 따라온다(목록의 **38번 주제**).

**컴파일 관점의 이득**

- **구현의 `struct S` 를 바꿔도 헤더 사용자가 다시 컴파일하지 않아도 된다.**\
  크기를 모르니 애초에 크기에 의존하는 코드를 못 만들었기 때문이다.
- 헤더에 `#include` 를 덜 써도 되는 것도 따라온다(멤버 타입의 헤더가 필요 없다).
- 정본은 목록의 **25번 주제**.

### 7. 같은 함수를 세 이름으로 선언해도 되는 이유

**왜 충돌하지 않나**

- 세 선언이 **완전히 같은 프로토타입**이기 때문이다. `MyInt` 와 `AlsoInt` 는 `int` 와 **같은 타입**이라,\
  컴파일러 눈에는 `int f(int);` 를 세 번 쓴 것과 다르지 않다.
- C 에는 같은 함수의 **재선언**이 허용된다(같은 타입이면).

**새 타입이었다면**

- `MyInt f(MyInt);` 가 **다른 시그니처**가 되어 재선언 충돌(`conflicting types`)이 났을 것이다.
- C 에는 오버로드가 없으므로 「이름은 같고 타입이 다른 함수 둘」은 **성립 자체가 안 된다.**

**`sizeof(MyInt)` 가 4인 것**

- **`int` 의 성질**이다. `MyInt` 는 아무 성질도 갖고 있지 않다.
- `int` 가 2바이트인 구현이라면 `sizeof(MyInt)` 도 2다.

**「어느 층인가」에의 반영**

```text
   typedef 자체              -> ★ 전부 "표준" 층
                                (구현이 고를 여지가 없다)

   sizeof(MyInt) = 4        -> "구현 정의" 층
                                단 그것은 ★ int 의 칸이지 MyInt 의 칸이 아니다
```

- 이 주제의 층 표가 **거의 전부 「표준」 한 줄**인 이유가 이것이다.
- 별칭은 **아무것도 안 만들므로** 구현이 다르게 할 여지가 없다.

### 8. `typedef static int Bad;`

**출력**

```text
sc.c:1:1: error: multiple storage classes in declaration specifiers
    1 | typedef static int Bad;
      | ^~~~~~~
```

**컴파일되나**

- **안 된다.** `multiple storage classes in declaration specifiers`.

**문법상 위치**

- ★ **`typedef` 는 `static`·`extern`·`auto`·`register` 와 같은 칸**(저장 클래스 지정자)에 온다.\
  선언에 그 칸의 낱말은 **하나만** 올 수 있어서 둘을 같이 못 쓴다.
- [01번 형제](../01-declaration-syntax-and-reading/)가 「저장 클래스 지정자는 타입이 아니다」로 적어 둔 그 칸이다.
- **문법 칸만 같고 하는 일은 전혀 다르다** — 나머지 넷은 저장 기간·연결을 정하고 `typedef` 는 이름을 만든다.

**저장 기간을 바꾸나**

- **안 바꾼다.** 애초에 `typedef` 로 만든 이름은 **객체가 아니라 타입**이라 저장 기간이라는 말이 안 붙는다.

**가린 뒤 타입으로 쓰면**

```text
바깥 T 로 선언: 4
T = 5
```

```text
shadow2.c: In function ‘main’:
shadow2.c:2:30: error: expected ‘;’ before ‘x’
    2 | int main(void) { int T = 5; T x = 1; return x + T; }
      |                              ^~
```

- 같은 이름의 변수를 선언하면 **그 블록 안에서 `typedef` 이름이 가려진다.** 변수로는 잘 쓰인다(`T = 5`).
- 그 뒤 `T x = 1;` 은 **`expected ‘;’ before ‘x’`** 다 — 파서가 `T` 를 **타입으로 안 보고 식으로 읽었다.**
- ★ 에러 문구가 「타입이 아니다」가 아니라 「**세미콜론이 빠졌다**」인 것이 중요하다.\
  C 의 파서는 **이름이 타입인지 아닌지를 알아야만** 문장을 나눌 수 있다.

### 9. 단위를 `typedef` 로 가르면

**출력**

```text
[-Wall -Wextra] 0 건
[-Wall -Wextra -Wconversion] 0 건
미터에 피트를 더했다: 13.0  <- 경고 한 줄 없다
```

**경고 몇 건**

- **0건**이다.

**`-Wconversion` 을 켜면**

- **그래도 0건**이다. 변환이 **일어나지 않았기** 때문이다 — 애초에 같은 타입이라 변환할 것이 없다.

**강제력을 얻으려면**

```c
typedef struct { double v; } Meters;
typedef struct { double v; } Feet;
```

```text
unit2.c: In function ‘main’:
unit2.c:4:74: error: incompatible type for argument 2 of ‘add_m’
```

- **`struct` 로 감싼다.** 익명 `struct` 두 개는 멤버가 같아도 **서로 다른 타입**이라 컴파일 에러가 난다.
- 경고가 아니라 **에러**다 — 강제력의 등급이 다르다.

**대가**

- 멤버 이름(`.v`)을 계속 써야 한다.
- **산술 연산자를 못 쓴다** — `a + b` 대신 `add_m(a, b)` 같은 함수가 필요하다.
- 인라인되면 런타임 비용은 대개 사라지지만 **이 문서에서 재 보지는 않았다.**

```text
   typedef double Meters;          typedef struct{double v;} Meters;
   +--------------------------+    +--------------------------+
   | 문서 효과만 있다           |    | ★ 컴파일러가 강제한다      |
   | 경고 0건                  |    | error: incompatible type |
   | 연산자 그대로 쓴다         |    | .v 와 함수가 필요하다      |
   +--------------------------+    +--------------------------+
```

- **`typedef` 는 검사가 아니라 문서**다. 둘을 갈라서 기대해야 한다.

### 10. 함수 포인터 별칭이 값을 내는 자리

**출력**

```text
typedef 로 만든 배열 == 손으로 쓴 것? 1 (크기 24 vs 24)
호출: A
qsort: 1 2 5 9
```

**손으로 쓴 어떤 선언과 같은가**

```text
   typedef char *CharFn(int);        CharFn  = "int 받아 char* 돌려주는 함수" 타입
   typedef CharFn *CharFnPtr;        CharFnPtr = 그 함수를 가리키는 포인터

   CharFnPtr ft[3];     ==     char *(*ft[3])(int);
   ^^^^^^^^^                   ^^^^^^^^^^^^^^^^^^
   한 번에 읽힌다                안쪽->바깥으로 풀어야 한다 (01번 주제)
```

- **`char *(*ft[3])(int)`** 와 같다.

**무엇으로 확인하나**

- **크기가 같고**(24 = 8 × 3) **서로 대입된다**(`ft[0] = raw[1];` 가 통과했고 호출도 됐다).
- 대입이 되는 것이 크기보다 강한 근거다 — 타입이 호환된다는 뜻이다.

**판단 기준 한 줄**

- **괄호가 두 겹 이상이면 `typedef` 로 자른다.** [01번 형제](../01-declaration-syntax-and-reading/)의 결론 그대로다.
- 뒤집으면 — 괄호 한 겹까지는 자르지 않는다. 이름이 하나 늘어나는 비용이 더 크다.

**`qsort` 비교자를 별칭으로 두면**

```c
typedef int (*Cmp)(const void *, const void *);
Cmp c = by_int;
qsort(a, 4, sizeof a[0], c);
```

- 선언·대입·전달이 **전부 한 낱말**로 읽힌다. 실측 결과 `1 2 5 9`.
- 콜백 테이블(디스패치 테이블)을 만들 때 **배열 원소 타입으로 쓸 수 있는 것**이 더 큰 이득이다.
- 정본은 목록의 **35번 주제**.

### 11. 같은 `typedef` 를 두 번

**출력**

```text
(비면 0건)
```

```text
re.c:2:13: warning: redefinition of typedef ‘T’ [-Wpedantic]
    2 | typedef int T;          /* 같은 타입이면 OK (C11) */
      |             ^
re.c:1:13: note: previous declaration of ‘T’ with type ‘T’ {aka ‘int’}
```

**두 번 쓰면**

- **같은 타입이면 적법**하다(C11 부터). 다른 타입이면 당연히 에러다.

**표준 버전별**

| `-std` | `-pedantic` 과 함께 | 진단 |
|---|---|---|
| `c17` | 0건 | — |
| `c89` | 1건 | `warning: redefinition of typedef ‘T’ [-Wpedantic]` |

- **C11 부터 허용**되고 그 이전에는 제약 위반이다.

**`-pedantic` 없이도 갈리나**

- **아니다. 어느 표준에서도 조용하다.**
- ★ **`-std=c89` 로 컴파일했다고 C89 코드가 되는 것이 아니다.** gcc 는 확장을 기본으로 켜 둔다.\
  표준 준수를 확인하려면 **`-pedantic`(또는 `-pedantic-errors`)까지** 붙여야 한다.\
  (같은 성질을 [07번 형제](../07-enum-and-enumeration-constants/)가 C23 기능 쪽에서 더 크게 확인한다.)

**쓸모 있는 자리**

- **헤더 두 개가 같은 `typedef` 를 각자 선언하는 경우.** `size_t`·`FILE` 처럼 여러 헤더에 나오는 것들이 그렇다.
- C11 이전에는 `#ifndef _SIZE_T_DEFINED` 같은 가드를 손으로 써야 했다.

### 12. 그래서 언제 쓰고 언제 안 쓰나

**감추면 안 되는 것 셋**

```text
   1. *  (포인터)      -> const 가 안 읽힌다 (2번) · 역참조 깊이가 안 보인다
   2. [] (배열)        -> 감쇠를 감춘다 (5번)
   3. const            -> 별칭 안에 넣으면 밖에서 뺄 수가 없다
```

- 셋의 공통점: **별칭이 「무슨 일이 일어나는지」를 가린다.**
- 반대로 **함수 포인터·불투명 핸들**은 감추는 것이 목적이라 값을 낸다.

**`FILE *` 를 쓰고 `FILEP` 를 안 만드는 이유**

- **`*` 를 감추지 않기 위해서**다. `FILE *fp` 를 보면 **포인터**라는 것이 바로 보이고,\
  `const FILE *` 을 쓰면 뜻이 기대대로 된다.
- `FILE` 자체는 불투명 타입이다 — 내부를 안 보여 주는 것과 포인터를 감추는 것은 **다른 일**이다.
- POSIX 의 `pthread_t` 처럼 **핸들 전체를 감추는** 설계도 있다. 그때는 `*` 를 쓸 일이 아예 없다.

**한 낱말로**

- **문서**다. 검사가 아니다. 강제력이 필요하면 `struct` 로 감싼다(9번).

**한 문장으로**

- **`typedef` 는 타입을 만드는 도구가 아니라 「읽기 어려운 선언」을 고치는 도구이고,\
  별칭이 타입에 붙기 때문에 `const` 와 배열을 감추면 뜻이 뒤집힌다.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| `_Generic` 충돌 | `error: ‘_Generic’ specifies two compatible types` | `-std=c17 -Wall -Wextra` |
| 3중 선언 | `int f(int)`·`MyInt f(MyInt)`·`AlsoInt f(AlsoInt)` 가 **통과** · `f(41)=42` · `_Generic` 이 `int` 라고 답함 | `-std=c17 -Wall -Wextra` |
| `const String` | 에러가 **`s = buf;`** 줄(`read-only variable ‘s’`) · `s[0]` 은 통과 | `-std=c17 -Wall -Wextra` |
| `const char *` 대조 | 에러가 **`s[0]`** 줄(`read-only location ‘*s’`) | 〃 |
| `#define` 대조 | 에러가 **`s[0]`** 줄 — `typedef` 와 **정반대** | 〃 |
| `_Generic(&s)` | `char * const *` 가지로 잡힘 · 손으로 쓴 `char * const t` 와 같은 가지 | 〃 |
| 여러 개 선언 | `#define` : 8, **1** / `typedef` : 8, 8 · 경고 **0건** | 〃 |
| 태그 이름 공간 | `struct Node`↔`Node` 대입 OK · `struct A`(4)↔`A`(8) 은 `incompatible types` 에러 | 〃 |
| 불투명 타입 | `typedef struct S S;` 만으로 헤더 성립(실행 `42`) · `sizeof(S)` 는 `incomplete type` 에러 | 〃 |
| 배열 별칭 | 밖 16 / 안 8 · 원본이 바뀜(`x[0]=99`) · `-Wsizeof-array-argument`(`-Wall`) | 〃 |
| 단위 혼동 | `-Wall -Wextra` **0건** · `+-Wconversion` 도 **0건** · `struct` 래퍼는 **에러** | `-Wall -Wextra` ± `-Wconversion` |
| 함수 포인터 별칭 | `CharFnPtr ft[3]` == `char *(*raw[3])(int)` (크기 24, 서로 대입) · `qsort` 동작 | `-std=c17 -Wall -Wextra` |
| 저장 클래스 | `typedef static` 은 `multiple storage classes` 에러 | `-std=c17` |
| 가리기 | 변수로 쓰이고(`T = 5`), 그 뒤 타입으로 쓰면 `expected ‘;’ before ‘x’` | `-std=c17 -Wall -Wextra` |
| 재정의 | `-std=c17 -pedantic` **0건** / `-std=c89 -pedantic` **1건** · `-pedantic` 없으면 둘 다 조용 | `-std=c89`/`c17` × `-pedantic` |
| 익명 struct 자기참조 | 선언은 **경고 0건** 통과 · 대입에서 `‘struct Node *’ from ... ‘Node *’` 경고 · 태그를 붙이면 **0건** | `-std=c17 -Wall -Wextra` |
| `typeof` | `-std=c2x -pedantic` 통과(`6`) / `-std=c17` 은 `implicit declaration of function ‘typeof’` | `-std=c17`/`c2x` `-pedantic` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0)에서만** 그렇다.

- `sizeof(MyInt)`=4 · `sizeof(char *)`=8 — **바탕 타입의 성질**이지 `typedef` 의 성질이 아니다.
- 진단 문구의 정확한 낱말(`read-only variable` ↔ `read-only location`) — gcc 의 선택이다.\
  ★ 그런데 이 주제의 답은 문구가 아니라 「**어느 줄인가**」이므로, 컴파일러가 바뀌어도 결론은 같다.
- `-Wsizeof-array-argument` 가 `-Wall` 에 있는 것 · `-Wincompatible-pointer-types` 가 기본인 것.
- `-std=c17` 에서 `typeof` 가 안 되는 것(gcc 의 확장 노출 범위에 달렸다).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `struct` 래퍼의 **런타임 비용**(인라인되어 사라지는지) · `typedef` 와 `_Generic` 을 결합한\
  타입 제네릭 인터페이스(목록의 **40번 주제**) · C23 의 `typeof_unqual` · `typedef` 가 붙은 VLA(목록의 **18번 주제**).
- **못 잰 것** — 없다. 이 주제는 컴파일만으로 전부 확인된다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- 11번의 `-std=c89 -pedantic` 경고(gcc 가 진단을 옮길 수 있다).
- `typeof` 가 `-std=c17` 에서도 되게 바뀌었는지.
- `-Wall`·`-Wextra` 의 구성(`-Wsizeof-array-argument` 의 소속).
