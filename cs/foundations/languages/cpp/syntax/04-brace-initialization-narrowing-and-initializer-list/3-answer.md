# cpp/syntax/04 — `{}` 균일 초기화·좁히기·`initializer_list` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **의도적 타입 에러**(`TypeOf<T>`)다(6번).
> **읽는 법** — 이 주제에는 **미정의 동작이 없다.** 그래서 출력은 전부 근거로 쓸 수 있다.\
> 대신 조심할 것은 **「빌드됐다」가 근거가 아니라는 것**이다 — 3번이 그 자리다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `{3, 0}` 은 크기 2 다 — 그러나 `string` 으로 바꾸면 같아진다

**출력**

```text
===== 소스: brace01.cpp =====
// () 와 {} 가 갈리는 자리 — vector 네 가지
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> a(3, 0);
    std::vector<int> b{3, 0};
    std::vector<int> c(3);
    std::vector<int> d{3};
    std::printf("a(3,0) size=%zu  a[0]=%d\n", a.size(), a[0]);
    std::printf("b{3,0} size=%zu  b[0]=%d b[1]=%d\n", b.size(), b[0], b[1]);
    std::printf("c(3)   size=%zu  c[0]=%d\n", c.size(), c[0]);
    std::printf("d{3}   size=%zu  d[0]=%d\n", d.size(), d[0]);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a(3,0) size=3  a[0]=0
b{3,0} size=2  b[0]=3 b[1]=0
c(3)   size=3  c[0]=0
d{3}   size=1  d[0]=3
```

**왜 그런가**

| 쓴 것 | 뽑힌 생성자 | `size()` |
|---|---|---|
| `a(3, 0)` | `vector(size_type n, const T& v)` | **3** |
| `b{3, 0}` | ★ `vector(initializer_list<int>)` | ★ **2** — 원소가 `3` 과 `0` |
| `c(3)` | `vector(size_type n)` | 3 |
| `d{3}` | ★ `vector(initializer_list<int>)` | ★ **1** — 원소가 `3` |

- ★★★ **갈리는 이유를 한 문장으로** — 「**중괄호 초기화에서는 `initializer_list` 생성자가 다른 모든 생성자보다 먼저 고려된다.**」\
  `initializer_list<int>` 는 `{3, 0}` 을 **그대로** 받을 수 있으므로 거기서 끝난다.
- ★★ **원소 타입을 `std::string` 으로 바꾸면 갈리지 않는다.**

```text
===== 소스: brace02.cpp =====
// 같은 두 인자를 string 으로 바꾸면 — initializer_list 가 후보가 아니게 된다
#include <cstdio>
#include <string>
#include <vector>

int main() {
    std::vector<std::string> a(3, "ha");
    std::vector<std::string> b{3, "ha"};
    std::printf("a(3,\"ha\") size=%zu a[0]=%s\n", a.size(), a[0].c_str());
    std::printf("b{3,\"ha\"} size=%zu b[0]=%s\n", b.size(), b[0].c_str());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a(3,"ha") size=3 a[0]=ha
b{3,"ha"} size=3 b[0]=ha
```

- **`3` 을 `std::string` 으로 만들 수 없어** `initializer_list<std::string>` 이 **애초에 후보가 아니다.**\
  그래서 `{3, "ha"}` 도 `(size, value)` 생성자로 가서 **`a` 와 완전히 같아진다.**
- ★ 그러므로 외울 것은 「중괄호는 다르다」가 아니라 「**`initializer_list` 가 후보일 때만 다르다**」다.

### 2. ★★★ 에러 **넷** · 경고 **셋** · 진단 없음 **둘** — 그리고 `int b{3.0}` 도 에러다

**출력**

```text
===== 소스: brace03.cpp =====
// 좁히기 아홉 줄 — 무엇이 에러이고 무엇이 통과하나
int main() {
    int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
    int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
    char     c{65};       // (3) int -> char, 상수식이고 들어간다
    char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
    int n = 65;
    char     e{n};        // (5) int -> char, 비상수
    double   f{1};        // (6) int -> double, 상수식
    int m = 1;
    double   g{m};        // (7) int -> double, 비상수
    unsigned u{-1};       // (8) 음수 상수 -> unsigned
    long long big = 1;
    double   h{big};      // (9) long long -> double, 비상수
    (void)a; (void)b; (void)c; (void)d; (void)e;
    (void)f; (void)g; (void)u; (void)h;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace03.cpp -o ex (cc exit=1) =====
brace03.cpp: In function ‘int main()’:
brace03.cpp:3:16: error: narrowing conversion of ‘3.8999999999999999e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    3 |     int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
      |                ^~~
brace03.cpp:4:16: error: narrowing conversion of ‘3.0e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    4 |     int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
      |                ^~~
brace03.cpp:6:16: error: narrowing conversion of ‘300’ from ‘int’ to ‘char’ [-Wnarrowing]
    6 |     char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
      |                ^~~
brace03.cpp:8:16: warning: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    8 |     char     e{n};        // (5) int -> char, 비상수
      |                ^
brace03.cpp:11:16: warning: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
   11 |     double   g{m};        // (7) int -> double, 비상수
      |                ^
brace03.cpp:12:16: error: narrowing conversion of ‘-1’ from ‘int’ to ‘unsigned int’ [-Wnarrowing]
   12 |     unsigned u{-1};       // (8) 음수 상수 -> unsigned
      |                ^~
brace03.cpp:14:16: warning: narrowing conversion of ‘big’ from ‘long long int’ to ‘double’ [-Wnarrowing]
   14 |     double   h{big};      // (9) long long -> double, 비상수
      |                ^~~
```

**왜 그런가**

표준이 좁히기로 정한 것은 **네 갈래**이고, **예외 조건이 갈래마다 다르다.**

```text
  ① 부동소수점 → 정수                   ★ 예외 없음
  ② 더 넓은 부동 → 더 좁은 부동          상수식 + 표현 범위 안 → 예외
  ③ 정수/무범위 열거형 → 부동소수점       상수식 + 왕복이 정확 → 예외
  ④ 정수 → 값 전부를 못 담는 정수         상수식 + 승격 뒤 값이 들어감 → 예외
```

| 줄 | 변환 | 갈래 | g++ | 왜 |
|---|---|---|---|---|
| (1) `int a{3.9}` | `double`→`int` | ① | **에러** | 예외가 없다 |
| (2) `int b{3.0}` | `double`→`int` | ① | ★ **에러** | ★ **값이 정확해도** 막힌다 |
| (3) `char c{65}` | `int`→`char` | ④ | **진단 0** | 상수식이고 들어간다 |
| (4) `char d{300}` | `int`→`char` | ④ | **에러** | 상수식인데 **안 들어간다** |
| (5) `char e{n}` | `int`→`char` | ④ | ★ **경고** | **비상수** — 예외에 못 든다 |
| (6) `double f{1}` | `int`→`double` | ③ | **진단 0** | 상수식이고 왕복이 정확 |
| (7) `double g{m}` | `int`→`double` | ③ | ★ **경고** | **비상수** |
| (8) `unsigned u{-1}` | `int`→`unsigned` | ④ | **에러** | 음수 상수 |
| (9) `double h{big}` | `long long`→`double` | ③ | ★ **경고** | **비상수** |

- ★★★ **(2)가 함정이다.** 「상수식이면 통과」를 **규칙으로** 외우면 여기서 틀린다.\
  **부동→정수(①)에는 상수식 예외가 아예 없다.**
- ★★ **(3)과 (5)를 가르는 것은 「상수식인가」뿐**이다 — 같은 `int`→`char` 인데 하나는 진단 0건, 하나는 걸린다.
- ★ **(6)/(7)도 같은 짝**이다. `int`→`double` 은 이 머신에서 값을 잃지 않는데도\
  표준이 **타입으로** 규칙을 써 놓아서 **비상수면 좁히기**다.

**clang 의 답 — 판정은 같고 심각도가 다르다.**

```text
===== 소스: brace03.cpp =====
// 좁히기 아홉 줄 — 무엇이 에러이고 무엇이 통과하나
int main() {
    int      a{3.9};      // (1) double -> int, 비상수가 아니라 리터럴
    int      b{3.0};      // (2) double -> int, 상수식이고 값도 정확하다
    char     c{65};       // (3) int -> char, 상수식이고 들어간다
    char     d{300};      // (4) int -> char, 상수식인데 안 들어간다
    int n = 65;
    char     e{n};        // (5) int -> char, 비상수
    double   f{1};        // (6) int -> double, 상수식
    int m = 1;
    double   g{m};        // (7) int -> double, 비상수
    unsigned u{-1};       // (8) 음수 상수 -> unsigned
    long long big = 1;
    double   h{big};      // (9) long long -> double, 비상수
    (void)a; (void)b; (void)c; (void)d; (void)e;
    (void)f; (void)g; (void)u; (void)h;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace03.cpp -o ex 2>&1 | grep -v '^ ' (cc exit=1) =====
brace03.cpp:3:16: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
brace03.cpp:3:16: note: insert an explicit cast to silence this issue
brace03.cpp:3:16: warning: implicit conversion from 'double' to 'int' changes value from 3.9 to 3 [-Wliteral-conversion]
brace03.cpp:4:16: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
brace03.cpp:4:16: note: insert an explicit cast to silence this issue
brace03.cpp:6:16: error: constant expression evaluates to 300 which cannot be narrowed to type 'char' [-Wc++11-narrowing]
brace03.cpp:6:16: note: insert an explicit cast to silence this issue
brace03.cpp:8:16: error: non-constant-expression cannot be narrowed from type 'int' to 'char' in initializer list [-Wc++11-narrowing]
brace03.cpp:8:16: note: insert an explicit cast to silence this issue
brace03.cpp:11:16: error: non-constant-expression cannot be narrowed from type 'int' to 'double' in initializer list [-Wc++11-narrowing]
brace03.cpp:11:16: note: insert an explicit cast to silence this issue
brace03.cpp:12:16: error: constant expression evaluates to -1 which cannot be narrowed to type 'unsigned int' [-Wc++11-narrowing]
brace03.cpp:12:16: note: insert an explicit cast to silence this issue
brace03.cpp:14:16: error: non-constant-expression cannot be narrowed from type 'long long' to 'double' in initializer list [-Wc++11-narrowing]
brace03.cpp:14:16: note: insert an explicit cast to silence this issue
brace03.cpp:6:16: warning: implicit conversion from 'int' to 'char' changes value from 300 to 44 [-Wconstant-conversion]
2 warnings and 7 errors generated.
```

- ★★ **(5)·(7)·(9)를 clang 은 `error` 로 낸다.** g++ 는 `warning` 이다 — 3번에서 그 결과를 종료 코드로 본다.
- ★ clang 은 `note: insert an explicit cast to silence this issue` 로 **고칠 코드까지** 보여 준다.

### 3. ★★★ **g++ 는 `cc exit=0`, clang 은 `cc exit=1`** — 표준은 clang 쪽이다

**출력**

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace04.cpp -o ex (cc exit=0) =====
brace04.cpp: In function ‘int main()’:
brace04.cpp:4:14: warning: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:6:14: warning: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
    6 |     double g{m};
      |              ^
```

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace04.cpp -o ex (cc exit=1) =====
brace04.cpp:4:14: error: non-constant-expression cannot be narrowed from type 'int' to 'char' in initializer list [-Wc++11-narrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:4:14: note: insert an explicit cast to silence this issue
    4 |     char   e{n};
      |              ^
      |              static_cast<char>( )
brace04.cpp:6:14: error: non-constant-expression cannot be narrowed from type 'int' to 'double' in initializer list [-Wc++11-narrowing]
    6 |     double g{m};
      |              ^
brace04.cpp:6:14: note: insert an explicit cast to silence this issue
    6 |     double g{m};
      |              ^
      |              static_cast<double>( )
2 errors generated.
```

**왜 그런가**

- ★★★ **같은 소스가 g++ 에서 빌드되고 clang 에서 막힌다.**\
  표준은 목록 초기화 안의 좁히기를 **ill-formed**(문법 위반)로 정했다. 그런데 **ill-formed 코드에 대해 구현은\
  「진단을 낼 의무」만 지고 「거부할 의무」는 지지 않는다.** g++ 는 그 재량을 **경고**로 쓴다.
- ★★ **그래서 표준이 정한 답은 clang 쪽**이고, 「g++ 에서 빌드됐다」는 **근거가 못 된다.**

**`-pedantic` 으로는 안 바뀐다.** `-pedantic-errors` 라야 한다.

```text
===== 소스: brace04.cpp =====
// 좁히기 중 「비상수」인 둘만 남긴 판 — g++ 는 이것을 통과시킨다
int main() {
    int n = 65;
    char   e{n};
    int m = 1;
    double g{m};
    (void)e; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors brace04.cpp -o ex (cc exit=1) =====
brace04.cpp: In function ‘int main()’:
brace04.cpp:4:14: error: narrowing conversion of ‘n’ from ‘int’ to ‘char’ [-Wnarrowing]
    4 |     char   e{n};
      |              ^
brace04.cpp:6:14: error: narrowing conversion of ‘m’ from ‘int’ to ‘double’ [-Wnarrowing]
    6 |     double g{m};
      |              ^
```

**플래그별로 세면**

```text
===== 소스: count04.sh =====
# 경고를 플래그별로 센다 — 종료 코드와 함께 봐야 뜻이 있다
for f in '-Wall -Wextra' '-Wall -Wextra -pedantic' \
         '-Wall -Wextra -pedantic-errors' '-Wall -Wextra -Werror=narrowing'; do
  o=$(g++ -std=c++20 $f brace04.cpp -o ex 2>&1)
  echo "g++     [$f] cc exit=$? · warning:=$(printf '%s' "$o" | grep -c 'warning:') · error:=$(printf '%s' "$o" | grep -c 'error:')"
done
for f in '-Wall -Wextra' '-Wall -Wextra -pedantic'; do
  o=$(clang++ -std=c++20 $f brace04.cpp -o ex 2>&1)
  echo "clang++ [$f] cc exit=$? · warning:=$(printf '%s' "$o" | grep -c 'warning:') · error:=$(printf '%s' "$o" | grep -c 'error:')"
done
===== bash count04.sh (exit=0) =====
g++     [-Wall -Wextra] cc exit=0 · warning:=2 · error:=0
g++     [-Wall -Wextra -pedantic] cc exit=0 · warning:=2 · error:=0
g++     [-Wall -Wextra -pedantic-errors] cc exit=1 · warning:=0 · error:=2
g++     [-Wall -Wextra -Werror=narrowing] cc exit=1 · warning:=0 · error:=2
clang++ [-Wall -Wextra] cc exit=1 · warning:=0 · error:=2
clang++ [-Wall -Wextra -pedantic] cc exit=1 · warning:=0 · error:=2
```

| 컴파일러·플래그 | `cc exit` | `warning:` | `error:` |
|---|---|---|---|
| g++ `-Wall -Wextra` | **0** | 2 | 0 |
| g++ `-Wall -Wextra -pedantic` | **0** | 2 | 0 |
| g++ `-Wall -Wextra -pedantic-errors` | **1** | 0 | **2** |
| g++ `-Wall -Wextra -Werror=narrowing` | **1** | 0 | **2** |
| clang++ `-Wall -Wextra` | **1** | 0 | **2** |
| clang++ `-Wall -Wextra -pedantic` | **1** | 0 | **2** |

- ★★ **「경고 0건」은 종료 코드를 같이 봐야 뜻이 있다**는 규칙의 반대편 사례다 —\
  여기서는 「**경고 2건인데 종료 코드가 0**」이 문제다. 경고만 세고 넘어가면 **ill-formed 코드가 그대로 나간다.**
- ★ 세는 법 — `grep -c 'warning:'`. `grep -c warning` 은 clang 의 `2 warnings generated.` 요약 줄까지 센다.

### 4. ★★ 다섯 줄이 다섯 가지 — 그리고 빈 `{}` 는 기본 생성자다

**출력**

```text
===== 소스: brace05.cpp =====
// initializer_list 가 다른 생성자를 이기는 것 — 그리고 빈 {} 는 안 이긴다
#include <cstdio>
#include <initializer_list>

struct W {
    W()                             { std::printf("W()\n"); }
    W(int, int)                     { std::printf("W(int,int)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W a(1, 2);      // ① 괄호 — 생성자 오버로드 해석
    W b{1, 2};      // ② 중괄호 — initializer_list 가 먼저다
    W c{};          // ③ 빈 중괄호 — 기본 생성자다
    W d({});        // ④ 빈 중괄호를 「인자로」 넘기면
    W e{1, 2, 3};   // ⑤ 셋이면 (int,int) 는 후보도 아니다
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
W(int,int)
W(init_list) size=2
W()
W(init_list) size=0
W(init_list) size=3
```

**왜 그런가**

| 쓴 것 | 불린 것 | 왜 |
|---|---|---|
| `W a(1, 2)` | `W(int,int)` | 괄호 — **평범한 오버로드 해석** |
| `W b{1, 2}` | ★ `W(init_list)` size=2 | 중괄호 — `initializer_list` 를 **먼저** 본다 |
| `W c{}` | ★ `W()` | ★ **빈 중괄호는 기본 생성자**다 |
| `W d({})` | `W(init_list)` size=0 | 빈 중괄호를 **인자로** 넘기면 목록이다 |
| `W e{1, 2, 3}` | `W(init_list)` size=3 | `W(int,int)` 는 인자 수가 안 맞는다 |

- ★★★ **③과 ④의 차이가 규칙의 전부다.** `W c{}` 의 중괄호는 **초기화 문법**이고,\
  `W d({})` 의 안쪽 중괄호는 **넘기는 인자**다.
- 규칙 한 문장 — **「중괄호 초기화에서 `initializer_list` 생성자는 다른 모든 생성자보다 먼저 고려된다.\
  단 목록이 비어 있으면 기본 생성자가 먼저다.」**

**생성자를 `W(double,double)` 과 `initializer_list<int>` 로 바꾸면 — 이겨서 에러가 난다.**

```text
===== 소스: brace06.cpp =====
// initializer_list 가 「이겨서 에러가 되는」 자리
#include <cstdio>
#include <initializer_list>

struct W {
    W(double, double)               { std::printf("W(double,double)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W f(1.0, 2.0);   // 괄호 — 정확히 맞는 생성자가 있다
    W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
    (void)f; (void)g;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace06.cpp -o ex (cc exit=1) =====
brace06.cpp: In function ‘int main()’:
brace06.cpp:12:17: error: narrowing conversion of ‘1.0e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |                 ^
```

```text
===== 소스: brace06.cpp =====
// initializer_list 가 「이겨서 에러가 되는」 자리
#include <cstdio>
#include <initializer_list>

struct W {
    W(double, double)               { std::printf("W(double,double)\n"); }
    W(std::initializer_list<int> l) { std::printf("W(init_list) size=%zu\n", l.size()); }
};

int main() {
    W f(1.0, 2.0);   // 괄호 — 정확히 맞는 생성자가 있다
    W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
    (void)f; (void)g;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace06.cpp -o ex (cc exit=1) =====
brace06.cpp:12:9: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |         ^~~
brace06.cpp:12:9: note: insert an explicit cast to silence this issue
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |         ^~~
      |         static_cast<int>( )
brace06.cpp:12:14: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |              ^~~
brace06.cpp:12:14: note: insert an explicit cast to silence this issue
   12 |     W g{1.0, 2.0};   // 중괄호 — initializer_list<int> 가 먼저 뽑힌다
      |              ^~~
      |              static_cast<int>( )
2 errors generated.
```

- ★★★ **`W(double,double)` 이 정확히 맞는데도 안 뽑혔다.** `initializer_list<int>` 가 먼저 뽑히고,\
  `1.0` → `int` 가 **좁히기라서** 그제야 실패한 것이다.\
  **이것이 「이겼다」의 증거다** — 졌다면 `W(double,double)` 로 가서 아무 문제가 없었을 테니까.
- ★ **괄호 쪽(`W f(1.0, 2.0)`)은 통과한다** — 진단이 `g` 줄에만 붙었다.
- ★ clang 은 인자 **둘 다** 에러로 세고(`2 errors generated.`) g++ 는 **한 줄**만 낸다 —\
  **에러를 몇 개로 세는가는 구현이다.**

### 5. ★★ `T t();` 는 **함수 선언**이다

**출력**

```text
===== 소스: brace07.cpp =====
// 가장 성가신 파싱 — T t(); 는 변수가 아니다
#include <cstdio>

struct T {
    int v = 7;
    T() { std::printf("T()\n"); }
};

int main() {
    T t();
    std::printf("t.v = %d\n", t.v);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace07.cpp -o ex (cc exit=1) =====
brace07.cpp: In function ‘int main()’:
brace07.cpp:10:8: warning: empty parentheses were disambiguated as a function declaration [-Wvexing-parse]
   10 |     T t();
      |        ^~
brace07.cpp:10:8: note: remove parentheses to default-initialize a variable
   10 |     T t();
      |        ^~
      |        --
brace07.cpp:10:8: note: or replace parentheses with braces to value-initialize a variable
brace07.cpp:11:33: error: request for member ‘v’ in ‘t’, which is of non-class type ‘T()’
   11 |     std::printf("t.v = %d\n", t.v);
      |                                 ^
```

```text
===== 소스: brace07.cpp =====
// 가장 성가신 파싱 — T t(); 는 변수가 아니다
#include <cstdio>

struct T {
    int v = 7;
    T() { std::printf("T()\n"); }
};

int main() {
    T t();
    std::printf("t.v = %d\n", t.v);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace07.cpp -o ex (cc exit=1) =====
brace07.cpp:10:8: warning: empty parentheses interpreted as a function declaration [-Wvexing-parse]
   10 |     T t();
      |        ^~
brace07.cpp:10:8: note: remove parentheses to declare a variable
   10 |     T t();
      |        ^~
brace07.cpp:11:31: error: base of member reference is a function; perhaps you meant to call it with no arguments?
   11 |     std::printf("t.v = %d\n", t.v);
      |                               ^
      |                                ()
1 warning and 1 error generated.
```

**왜 그런가**

- ★★ **`T t();` 는 「`T` 를 돌려주고 인자가 없는 함수 `t`」의 선언**이다. 그래서 `t.v` 가\
  ``non-class type `T()` `` 라는 에러를 낸다. **경고만 보고 넘어가면 그 줄까지 가서야 막힌다.**
- **경고 이름은 두 컴파일러가 같다** — `-Wvexing-parse`.
- ★ **g++ 가 제안하는 고침은 둘**이다 —\
  ① `note: remove parentheses to default-initialize a variable`(→ `T t;`) ·\
  ② `note: or replace parentheses with braces to value-initialize a variable`(→ `T t{};`).\
  clang 은 ①만 제안한다.
- ★★ **`{}` 를 쓰면 이 함정이 없다.** `T t{};` 는 **선언 문법으로 읽힐 수 없기 때문**이다 —\
  「어디에나 중괄호」를 권하는 가장 실용적인 근거가 이것이다.
- ★ 이 함정은 인자가 있어도 난다(`T t(U());`). **이 문서는 빈 괄호 판만 던졌다.**

### 6. ★ `int` 와 `std::initializer_list<int>`

**출력**

```text
===== 소스: brace08.cpp =====
// auto x{1} 대 auto x = {1} — 타입을 의도적 타입 에러로 찍는다
#include <initializer_list>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    auto a{1};
    auto b = {1};
    auto c = {1, 2};
    TypeOf<decltype(a)> ta;
    TypeOf<decltype(b)> tb;
    TypeOf<decltype(c)> tc;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace08.cpp -o ex (cc exit=1) =====
brace08.cpp: In function ‘int main()’:
brace08.cpp:10:25: error: aggregate ‘TypeOf<int> ta’ has incomplete type and cannot be defined
   10 |     TypeOf<decltype(a)> ta;
      |                         ^~
brace08.cpp:11:25: error: aggregate ‘TypeOf<std::initializer_list<int> > tb’ has incomplete type and cannot be defined
   11 |     TypeOf<decltype(b)> tb;
      |                         ^~
brace08.cpp:12:25: error: aggregate ‘TypeOf<std::initializer_list<int> > tc’ has incomplete type and cannot be defined
   12 |     TypeOf<decltype(c)> tc;
      |                         ^~
```

```text
===== 소스: brace08.cpp =====
// auto x{1} 대 auto x = {1} — 타입을 의도적 타입 에러로 찍는다
#include <initializer_list>

template <class T> struct TypeOf;   // 선언만 — 정의가 없다

int main() {
    auto a{1};
    auto b = {1};
    auto c = {1, 2};
    TypeOf<decltype(a)> ta;
    TypeOf<decltype(b)> tb;
    TypeOf<decltype(c)> tc;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace08.cpp -o ex (cc exit=1) =====
brace08.cpp:10:25: error: implicit instantiation of undefined template 'TypeOf<int>'
   10 |     TypeOf<decltype(a)> ta;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
brace08.cpp:11:25: error: implicit instantiation of undefined template 'TypeOf<std::initializer_list<int>>'
   11 |     TypeOf<decltype(b)> tb;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
brace08.cpp:12:25: error: implicit instantiation of undefined template 'TypeOf<std::initializer_list<int>>'
   12 |     TypeOf<decltype(c)> tc;
      |                         ^
brace08.cpp:4:27: note: template is declared here
    4 | template <class T> struct TypeOf;   // 선언만 — 정의가 없다
      |                           ^
3 errors generated.
```

**왜 그런가**

| 쓴 것 | 타입 | 언제부터 |
|---|---|---|
| `auto a{1}` | ★ **`int`** | **C++17부터.** C++11/14 에서는 `initializer_list<int>` 였다 |
| `auto b = {1}` | `std::initializer_list<int>` | C++11부터 그대로 |
| `auto c = {1, 2}` | `std::initializer_list<int>` | 〃 |

- ★★ **`=` 하나가 타입을 바꾼다.** `auto a{1}` 은 **값**이고 `auto b = {1}` 은 **목록**이다.
- ★★ **`TypeOf<T>` 가 왜 필요한가** — 두 줄 다 컴파일되고 **아무것도 안 찍는다.**\
  정의가 없는 템플릿에 그 타입을 넣으면 **컴파일러가 자기 입으로 타입을 말한다**(`TypeOf<int>` · `TypeOf<std::initializer_list<int> >`).\
  이 창의 정본은 형제 [**05번**](../05-auto-and-decltype-type-deduction/)이다.

**원소가 둘인 「직접」 목록 초기화는 아예 막힌다.**

```text
===== 소스: brace09.cpp =====
// auto 의 직접 목록 초기화는 원소가 하나여야 한다
int main() {
    auto c{1, 2};
    (void)c;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace09.cpp -o ex (cc exit=1) =====
brace09.cpp: In function ‘int main()’:
brace09.cpp:3:16: error: direct-list-initialization of ‘auto’ requires exactly one element [-fpermissive]
    3 |     auto c{1, 2};
      |                ^
brace09.cpp:3:16: note: for deduction to ‘std::initializer_list’, use copy-list-initialization (i.e. add ‘=’ before the ‘{’)
brace09.cpp:3:16: error: deducing from brace-enclosed initializer list requires ‘#include <initializer_list>’
  +++ |+#include <initializer_list>
    1 | // auto 의 직접 목록 초기화는 원소가 하나여야 한다
    2 | int main() {
    3 |     auto c{1, 2};
      |                ^
```

- g++ 의 `note:` 가 고침을 직접 말한다 — **`=` 를 붙이라**고. `auto c = {1, 2};` 는 된다(위 블록의 `c`).

### 7. 셋 다 C 에서는 되고 C++ 에서는 g++ 가 막는다 — clang 은 통과시킨다

**출력**

```text
===== 소스: brace11.cpp =====
// C 에서 되고 C++ 에서 안 되는 지정 초기자 셋
struct P { int x; int y; int z; };

int main() {
    P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
    P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
    int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
    (void)a; (void)b; (void)arr;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace11.cpp -o ex (cc exit=1) =====
brace11.cpp: In function ‘int main()’:
brace11.cpp:5:23: warning: missing initializer for member ‘P::x’ [-Wmissing-field-initializers]
    5 |     P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
      |                       ^
brace11.cpp:5:23: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
brace11.cpp:5:23: error: designator order for field ‘P::x’ does not match declaration order in ‘P’
brace11.cpp:6:17: error: either all initializer clauses should be designated or none of them should be
    6 |     P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
      |                 ^
brace11.cpp:6:18: warning: missing initializer for member ‘P::z’ [-Wmissing-field-initializers]
    6 |     P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
      |                  ^
brace11.cpp:7:19: warning: ISO C++ does not allow C99 designated initializers [-Wpedantic]
    7 |     int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
      |                   ^
brace11.cpp:7:26: sorry, unimplemented: non-trivial designated initializers not supported
    7 |     int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
      |                          ^
```

```text
===== 소스: desig01.c =====
/* 같은 셋을 C 로 던지면 */
struct P { int x; int y; int z; };

int main(void) {
    struct P a = {.z = 3, .x = 1};
    struct P b = {.x = 1, 2};
    int arr[3] = {[1] = 5};
    (void)a; (void)b; (void)arr;
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic desig01.c -o ex (cc exit=0) =====
```

```text
===== 소스: brace11.cpp =====
// C 에서 되고 C++ 에서 안 되는 지정 초기자 셋
struct P { int x; int y; int z; };

int main() {
    P a{.z = 3, .x = 1};       // ① 선언 순서를 어긴다
    P b{.x = 1, 2};            // ② 지정과 위치를 섞는다
    int arr[3] = {[1] = 5};    // ③ 배열 지정 초기자
    (void)a; (void)b; (void)arr;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace11.cpp -o ex 2>&1 | grep -E 'warning:|error:|note:|generated' (cc exit=0) =====
brace11.cpp:5:22: warning: ISO C++ requires field designators to be specified in declaration order; field 'z' will be initialized after field 'x' [-Wreorder-init-list]
brace11.cpp:5:14: note: previous initialization for field 'z' is here
brace11.cpp:5:23: warning: missing field 'y' initializer [-Wmissing-field-initializers]
brace11.cpp:6:9: warning: mixture of designated and non-designated initializers in the same initializer list is a C99 extension [-Wc99-designator]
brace11.cpp:6:17: note: first non-designated initializer is here
brace11.cpp:6:18: warning: missing field 'z' initializer [-Wmissing-field-initializers]
brace11.cpp:7:19: warning: array designators are a C99 extension [-Wc99-designator]
5 warnings generated.
```

**왜 그런가**

| 쓴 것 | C(gcc 13 `-std=c17 -pedantic`) | g++ 13(C++20) | clang++ 18(C++20) |
|---|---|---|---|
| `.z = 3, .x = 1`(순서 어김) | **통과 · 진단 0** | ★ **에러** | ★ **경고** `-Wreorder-init-list` |
| `.x = 1, 2`(지정·위치 혼합) | **통과 · 진단 0** | ★ **에러** | ★ **경고** `-Wc99-designator` |
| `[1] = 5`(배열 지정 초기자) | **통과 · 진단 0** | ★ **`sorry, unimplemented`** | ★ **경고** `-Wc99-designator` |
| **종료 코드** | **0** | **1** | ★ **0**(경고 5건) |

- ★★★ **여기서도 두 컴파일러가 갈린다.** 이번에는 **g++ 가 엄격하고 clang 이 느슨하다** — 3번과 **방향이 반대**다.\
  「어느 컴파일러가 더 엄격한가」를 **컴파일러 단위로 외우면 틀린다.**
- ★★ **C++ 가 일부러 뺀 것은 「순서 어김」과 「혼합」이다.** C++ 는 멤버 **파괴가 선언 역순**임을 보장하는데,\
  초기화가 지정 순서를 따라가면 **생성과 파괴의 짝이 어긋난다.** 그래서 **선언 순서만** 허용한다.
- ★ **배열 지정 초기자는 C++ 에 없다.** g++ 의 `sorry, unimplemented` 는 에러가 아니라\
  「**GCC 확장인데 이 자리에서는 구현이 없다**」는 뜻이라 문구가 다르다.
- ★ C 쪽 규칙 전부(빠진 멤버가 0 이 되는 것 포함)의 정본은\
  C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **21번**이다. 여기서는 **갈리는 셋만** 던졌다.

### 8. ★★ C++20 에서는 되고 — **좁히기 검사가 없다**

**출력**

```text
===== 소스: brace13.cpp =====
// C++20 괄호 집합체 초기화 — 좁히기 검사가 없다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a(1, 2, 3);
    P b(1, 2.9, 3);
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace13.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a = 1,2,3
b = 1,2,3
```

```text
===== 소스: brace14.cpp =====
// 같은 값을 중괄호로 — 이쪽은 좁히기가 걸린다
struct P { int x; int y; int z; };

int main() {
    P b{1, 2.9, 3};
    (void)b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace14.cpp -o ex (cc exit=1) =====
brace14.cpp: In function ‘int main()’:
brace14.cpp:5:12: error: narrowing conversion of ‘2.8999999999999999e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
    5 |     P b{1, 2.9, 3};
      |            ^~~
```

```text
===== 소스: brace13.cpp =====
// C++20 괄호 집합체 초기화 — 좁히기 검사가 없다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a(1, 2, 3);
    P b(1, 2.9, 3);
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
}
===== g++ -std=c++17 -Wall -Wextra -pedantic brace13.cpp -o ex 2>&1 | head -12 (cc exit=1) =====
brace13.cpp: In function ‘int main()’:
brace13.cpp:7:16: error: no matching function for call to ‘P::P(int, int, int)’
    7 |     P a(1, 2, 3);
      |                ^
brace13.cpp:4:8: note: candidate: ‘P::P()’
    4 | struct P { int x; int y; int z; };
      |        ^
brace13.cpp:4:8: note:   candidate expects 0 arguments, 3 provided
brace13.cpp:4:8: note: candidate: ‘constexpr P::P(const P&)’
brace13.cpp:4:8: note:   candidate expects 1 argument, 3 provided
brace13.cpp:4:8: note: candidate: ‘constexpr P::P(P&&)’
brace13.cpp:4:8: note:   candidate expects 1 argument, 3 provided
```

**왜 그런가**

| 쓴 것 | 표준판 | 결과 | 진단 |
|---|---|---|---|
| `P b(1, 2.9, 3)` | C++20 | ★ **`b.y == 2`** — 조용히 잘렸다 | ★★ **0건** |
| `P b{1, 2.9, 3}` | C++20 | **컴파일 에러** | `-Wnarrowing` 1건 |
| `P a(1, 2, 3)` | C++17 | **컴파일 에러** | `no matching function for call to 'P::P(int, int, int)'` |

- ★★★ **같은 집합체·같은 값인데 중괄호는 에러, 괄호는 조용한 절단**이다.\
  그리고 **괄호 쪽은 C++20 에서 새로 생긴 자리**다 — 표준판을 올리면서 **함정이 하나 늘었다.**
- ★★ **왜 검사가 없나** — 괄호 집합체 초기화는 **함수 호출 인자 변환과 같은 규칙**을 쓴다.\
  거기에는 좁히기 금지가 없다. 좁히기 금지는 **목록 초기화의 규칙**이다.
- ★ **clang 도 같은 답**이다(진단 0건 · `b.y = 2`).

```text
===== 소스: brace13.cpp =====
// C++20 괄호 집합체 초기화 — 좁히기 검사가 없다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a(1, 2, 3);
    P b(1, 2.9, 3);
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic brace13.cpp -o ex (cc exit=0) =====
brace13.cpp:8:12: warning: implicit conversion from 'double' to 'int' changes value from 2.9 to 2 [-Wliteral-conversion]
    8 |     P b(1, 2.9, 3);
      |        ~   ^~~
1 warning generated.
```

- ★★ **「`{}` 를 기본으로 쓰라」는 조언이 C++20 에서 더 강해졌다.** 전에는 집합체를 괄호로 **못 채웠으므로**\
  실수할 자리가 없었는데, 이제는 **되면서 검사만 없다.**

### 9. `0` · `nullptr` · `0` · `{0,0}` — 이름은 「값 초기화」다

**출력**

```text
===== 소스: brace12.cpp =====
// 값 초기화 — {} 가 「0 으로 채워라」가 되는 자리
#include <cstdio>

struct A { int a; int b; };

int main() {
    int    i{};
    int*   p{};
    double d{};
    A      s{};
    std::printf("i=%d  p=%s  d=%g  s={%d,%d}\n",
                i, p ? "非null" : "nullptr", d, s.a, s.b);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
i=0  p=nullptr  d=0  s={0,0}
```

**왜 그런가**

- **`T t{}` 는 값 초기화**다 — 기본 타입은 **0**, 포인터는 **`nullptr`**, 집합체는 **멤버마다 값 초기화**.
- **집합체에서 빠뜨린 멤버도 값 초기화**된다(7번의 `P c{1}` → `1,0,0`).\
  ★ 그런데 `-Wextra` 의 **`-Wmissing-field-initializers`** 가 그것을 **경고로** 말해 준다 —\
  컴파일러는 「0 을 바란 것」과 「빠뜨린 것」을 구별할 수 없기 때문이다.

```text
===== 소스: brace10.cpp =====
// 집합체 초기화와 지정 초기자(C++20) — 빠진 멤버는 값 초기화된다
#include <cstdio>

struct P { int x; int y; int z; };

int main() {
    P a{1, 2, 3};
    P b{.x = 1, .z = 3};
    P c{1};
    P d{};
    std::printf("a = %d,%d,%d\n", a.x, a.y, a.z);
    std::printf("b = %d,%d,%d\n", b.x, b.y, b.z);
    std::printf("c = %d,%d,%d\n", c.x, c.y, c.z);
    std::printf("d = %d,%d,%d\n", d.x, d.y, d.z);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic brace10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
brace10.cpp: In function ‘int main()’:
brace10.cpp:8:23: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
    8 |     P b{.x = 1, .z = 3};
      |                       ^
brace10.cpp:9:10: warning: missing initializer for member ‘P::y’ [-Wmissing-field-initializers]
    9 |     P c{1};
      |          ^
brace10.cpp:9:10: warning: missing initializer for member ‘P::z’ [-Wmissing-field-initializers]
a = 1,2,3
b = 1,0,3
c = 1,0,0
d = 0,0,0
```

- ★ **`A t;`(중괄호 없이, 지역)는 기본 초기화**라 멤버가 **불확정 값**이다.\
  ★★ **이 문서는 그 값을 싣지 않았다** — 불확정 값은 「흔들리는 칸」이라 근거로 못 쓴다.\
  대신 g++ 의 **`-Wuninitialized`** 가 그것을 경고로 말해 준다(이 문서에서 확인했다).
- ★ 그래서 이 언어의 기본 습관은 「**선언하면 `{}` 를 붙인다**」가 된다.

### 10. 이 주제의 지도

**왜 그런가**

- **`{}` 가 오버로드 해석을 바꾸는 규칙**의 밑바탕(후보 집합·순위·모호)은 형제\
  [**01번**](../01-function-overloading-and-overload-resolution/)이 정본이다.\
  여기는 그 위에 **`initializer_list` 가 먼저 걸러지는 한 겹**만 얹었다(4번).
- **좁히기 ④의 「정수 승격 뒤의 값」은** C 갈래\
  [`03-integer-promotion-and-usual-arithmetic-conversions/`](../../../c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/)가 정본이다.
- **구조체 집합체 초기화·C99 지정 초기자**는 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **21번**이다 —\
  **아직 폴더가 없어 링크가 없다.** 여기서는 **C++ 가 갈리는 셋만** 실측했다(7번).
- **`auto x = {1}` 이 `initializer_list` 가 되는 규칙**과 `TypeOf<T>` 창은 형제\
  [**05번**](../05-auto-and-decltype-type-deduction/)이 더 판다.
- **`std::vector<int> v{3, 0}` 의 함정을 타입으로 막는 도구**는 목록의 **47번 주제**(`optional`·`variant`)와\
  목록의 **32번 주제**(CTAD·추론 가이드) 쪽이다 — 「개수」와 「값」을 **다른 타입**으로 만들면 이 사고가 안 난다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `brace01.cpp` `vector` 네 줄 | `(3,0)`→3 · `{3,0}`→**2** · `(3)`→3 · `{3}`→**1** | g++ |
| `brace02.cpp` `vector<string>` | ★ **둘 다 크기 3** — 갈리지 않는다 | g++ |
| `brace03.cpp` 좁히기 아홉 줄 | g++ **에러 4 · 경고 3 · 진단 없음 2** | g++ |
| 〃 clang | ★ **에러 7 · 경고 2** — 판정은 같고 **심각도가 다르다** | clang |
| `brace04.cpp` 비상수 둘 | ★★ **g++ `cc exit=0`** · **clang `cc exit=1`** | g++ · clang |
| 〃 플래그별 | `-pedantic` **안 바뀜** · `-pedantic-errors`·`-Werror=narrowing` 에서 **exit=1** | g++ ×4 · clang ×2 |
| `brace05.cpp` `initializer_list` 다섯 줄 | `W(int,int)` / `init_list 2` / **`W()`** / `init_list 0` / `init_list 3` | g++ |
| `brace06.cpp` 이겨서 에러 | ★ `W(double,double)` 이 있는데도 **좁히기 에러** | g++ · clang |
| `brace07.cpp` 가장 성가신 파싱 | 두 컴파일러 다 `-Wvexing-parse` · g++ 는 **note 2**, clang 은 **note 1** | g++ · clang |
| `brace08.cpp` `auto` 와 중괄호 | `int` / `initializer_list<int>` / `initializer_list<int>` | g++ · clang |
| `brace09.cpp` `auto c{1,2}` | **에러** — 직접 목록 초기화는 원소 하나 | g++ |
| `brace10.cpp` 집합체·지정 초기자 | `1,2,3` / `1,0,3` / `1,0,0` / `0,0,0` + `-Wmissing-field-initializers` 3건 | g++ |
| `brace11.cpp` 금지 셋 | ★ **g++ 에러(exit=1)** · **clang 경고 5건(exit=0)** | g++ · clang |
| `desig01.c` 같은 셋을 C 로 | ★ **진단 0건 · exit=0** | gcc `-std=c17 -pedantic` |
| `brace12.cpp` 값 초기화 | `0` · `nullptr` · `0` · `{0,0}` | g++ |
| `brace13.cpp` 괄호 집합체 초기화 | ★★ **`b.y == 2` · 진단 0건**(C++20) | g++ · clang |
| 〃 `-std=c++17` | **에러** — 이 기능은 C++20부터다 | g++ |
| `brace14.cpp` 같은 값을 중괄호로 | **좁히기 에러** | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++/gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- ★★ **비상수 좁히기가 g++ 에서 「경고」인 것** — 표준은 ill-formed 라고만 하고 **거부를 요구하지 않는다.**
- ★★ **지정 초기자 순서 위반이 clang 에서 「경고」인 것** — 같은 성질이다.
- 진단 문구 전부 · **에러를 몇 개로 세는가**(`W g{1.0, 2.0}` 이 g++ 1건, clang 2건).
- `sorry, unimplemented: non-trivial designated initializers not supported` 라는 **GCC 내부 표현**.
- g++ 가 `-Wvexing-parse` 에 붙이는 **note 두 줄**(clang 은 한 줄).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- 좁히기 **네 갈래와 예외 조건** · **부동→정수에 예외가 없는 것** ·
  `initializer_list` 가 **먼저 고려되는** 것 · **빈 `{}` 가 기본 생성자**인 것 ·
  집합체가 **선언 순서**로 채워지고 **남은 것은 값 초기화**인 것 ·
  `T t();` 가 **함수 선언**인 것 · 지정 초기자가 **선언 순서만** 허용하는 것.
- ★ **언제부터인가**도 언어가 보장한다 — `auto x{1}` 이 `int` 인 것은 **C++17부터**,
  지정 초기자와 괄호 집합체 초기화는 **C++20부터**.
- ★★ **괄호 집합체 초기화에 좁히기 검사가 없는 것도 「언어」다** — 구현이 봐주는 게 아니라\
  **함수 인자 변환 규칙을 쓰기 때문**이다. 그래서 **어느 컴파일러에서도 안 잡힌다.**

**미정의 동작**

- ★ **이 주제에는 없다.** 이 문서의 프로그램은 전부 정의된 동작만 한다.\
  유일한 접점은 **`{}` 를 안 쓴 기본 초기화의 불확정 값**인데 **읽지 않았다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `initializer_list` 의 **수명**(멤버로 저장하면 댕글링) ·
  **원소가 `const` 라 옮길 수 없는 것**(`vector<unique_ptr<T>>` 를 중괄호로 못 채우는 이유) ·
  인자가 있는 **가장 성가신 파싱**(`T t(U());`) ·
  **CTAD 와 중괄호**(`std::vector v{1,2,3}`) ·
  C++11/14/17 로 각각 던져 **집합체 조건이 좁아진 자취**를 보는 것\
  (이 문서는 `auto x{1}` 과 괄호 집합체 초기화 **두 자리만** 표준판을 바꿔 던졌다).
- **못 잰 것** — 없다. 이 주제의 결론은 전부 **진단과 출력**으로 잡힌다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **g++ 가 비상수 좁히기를 계속 경고로 두는지** — 이 문서의 중심 결론이다.
- ★ **clang 이 지정 초기자 순서 위반을 계속 경고로 두는지.**
- ★ **괄호 집합체 초기화에 좁히기 진단이 생겼는지**(지금은 두 컴파일러 다 0건).
- 진단 문구와 **note 개수** · `-Wvexing-parse` 의 제안 목록.
