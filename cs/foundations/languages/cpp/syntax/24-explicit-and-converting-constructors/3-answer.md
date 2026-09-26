# cpp/syntax/24 — `explicit` 과 변환 생성자 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구**다.\
> 근거로 쓰는 것은 다음이다 — **`calls` 수 · 불린 함수 이름 · 어느 줄이 에러인가 · 에러 개수 · `cc exit` · 격자의 O/X · 타입 특성의 0/1 · 경고 개수**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`(1)`\~`(4)` 와 `(6)` 이 1, `(5)` 만 0** — 변환은 식에 있어도 **밟은 가지에서만** 돈다

**출력**

```cpp
/* conv01.cpp */
// 인자 하나짜리 생성자에 로그를 심었다 — 어느 자리에서 몇 번 불리나
// -DASK_EXPLICIT 이면 같은 생성자에 explicit 을 붙인다
#include <cstdio>

#ifdef ASK_EXPLICIT
#define MAYBE_EXPLICIT explicit
#else
#define MAYBE_EXPLICIT
#endif

static int calls = 0;

struct Meter {
    int v;
    MAYBE_EXPLICIT Meter(int x) : v(x) { ++calls; std::printf("      Meter(int %d)\n", x); }
};
bool operator==(Meter a, Meter b) { return a.v == b.v; }
void take(Meter m) { std::printf("      take(Meter %d)\n", m.v); }
Meter give() { return 7; }

static void done() { std::printf("    calls %d\n", calls); calls = 0; }

int main(int argc, char**) {
    bool yes = argc > 0, no = argc < 0;      // 실행 시점에 정해지는 참·거짓
    Meter m(1);
    calls = 0;

    std::printf("(1) Meter a = 5;\n");
    { Meter a = 5; (void)a; }
    done();

    std::printf("(2) take(6);\n");
    take(6);
    done();

    std::printf("(3) Meter c = give();\n");
    { Meter c = give(); (void)c; }
    done();

    std::printf("(4) m == 1\n");
    { bool e = (m == 1); std::printf("      -> %d\n", (int)e); }
    done();

    std::printf("(5) yes ? m : 9\n");
    { Meter t = yes ? m : 9; (void)t; }
    done();

    std::printf("(6) no ? m : 9\n");
    { Meter t = no ? m : 9; (void)t; }
    done();
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      Meter(int 1)
(1) Meter a = 5;
      Meter(int 5)
    calls 1
(2) take(6);
      Meter(int 6)
      take(Meter 6)
    calls 1
(3) Meter c = give();
      Meter(int 7)
    calls 1
(4) m == 1
      Meter(int 1)
      -> 1
    calls 1
(5) yes ? m : 9
    calls 0
(6) no ? m : 9
      Meter(int 9)
    calls 1
```

**왜 그런가**

- ★★★ **복사 초기화 · 인자 · 반환 · 연산자 인자 · 삼항의 가지** — 다섯 자리 다 **`Meter` 라는 글자 없이** 생성자가 돌았다.
- ★★★ **`(5)` 는 `yes` 가 참이라 `m` 가지를 밟았다** — `9` 를 `Meter` 로 바꾸는 변환은 식의 타입을 정하려고 **들어 있지만 실행되지 않았다.** `(6)` 은 `9` 가지를 밟아 1.
- ★ 첫 줄은 **`Meter m(1);`**(직접 초기화)이다. 세기 전에 `calls = 0` 으로 지웠다.

### 2. ★★★ **여섯 줄이 에러**(`give()` 포함) — `calls 0` 이던 `(5)` 도 **에러**다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_EXPLICIT -fmax-errors=0 conv01.cpp -o ex (cc exit=1) =====
conv01.cpp: In function ‘Meter give()’:
conv01.cpp:19:23: error: could not convert ‘7’ from ‘int’ to ‘Meter’
   19 | Meter give() { return 7; }
      |                       ^
      |                       |
      |                       int
conv01.cpp: In function ‘int main(int, char**)’:
conv01.cpp:29:17: error: conversion from ‘int’ to non-scalar type ‘Meter’ requested
   29 |     { Meter a = 5; (void)a; }
      |                 ^
conv01.cpp:33:10: error: could not convert ‘6’ from ‘int’ to ‘Meter’
   33 |     take(6);
      |          ^
      |          |
      |          int
conv01.cpp:41:19: error: no match for ‘operator==’ (operand types are ‘Meter’ and ‘int’)
   41 |     { bool e = (m == 1); std::printf("      -> %d\n", (int)e); }
      |                 ~ ^~ ~
      |                 |    |
      |                 |    int
      |                 Meter
conv01.cpp:17:6: note: candidate: ‘bool operator==(Meter, Meter)’
   17 | bool operator==(Meter a, Meter b) { return a.v == b.v; }
      |      ^~~~~~~~
conv01.cpp:17:32: note:   no known conversion for argument 2 from ‘int’ to ‘Meter’
   17 | bool operator==(Meter a, Meter b) { return a.v == b.v; }
      |                          ~~~~~~^
conv01.cpp:45:21: error: operands to ‘?:’ have different types ‘Meter’ and ‘int’
   45 |     { Meter t = yes ? m : 9; (void)t; }
      |                 ~~~~^~~~~~~
conv01.cpp:49:20: error: operands to ‘?:’ have different types ‘Meter’ and ‘int’
   49 |     { Meter t = no ? m : 9; (void)t; }
      |                 ~~~^~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_EXPLICIT -ferror-limit=0 conv01.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
conv01.cpp:19:23: error: no viable conversion from returned value of type 'int' to function return type 'Meter'
conv01.cpp:29:13: error: no viable conversion from 'int' to 'Meter'
conv01.cpp:33:5: error: no matching function for call to 'take'
conv01.cpp:41:19: error: invalid operands to binary expression ('Meter' and 'int')
conv01.cpp:45:21: error: incompatible operand types ('Meter' and 'int')
conv01.cpp:49:20: error: incompatible operand types ('Meter' and 'int')
6 errors generated.
```

**왜 그런가**

- ★★★ **1번에서 로그가 찍힌 다섯 자리 + `return 7;`** — `explicit` 은 **복사 초기화에서 그 생성자를 후보에서 뺀다.** 여섯 자리 다 복사 초기화다.
- ★★ **`(5)` 는 실행에서 안 밟았어도 컴파일은 두 가지를 다 본다** — 삼항의 타입이 정해지려면 `9` → `Meter` 변환이 **있어야** 하는데 그것이 막혔다.

### 3. ★★★ **복사 초기화 열 칸이 X** · **`push_back` X · `emplace_back` O** · 두 컴파일러 **갈린 칸 0**

**출력**

```bash
# conv-grid.sh
# conv-grid.sh — conv07.cpp 의 탐침 15개를 하나씩 켜고, explicit 유무 × 두 컴파일러로 컴파일되나를 찍는다
names=("" "Meter a = 5;" "take(5);" "return 5;" "return {5};" "take({5});" "m == 5" "c ? m : 5"
       "Meter a = {5};" "Meter arr[] = {5, 6};" "vec.push_back(5);" "Meter a(5);" "Meter a{5};"
       "Meter a = Meter(5);" "static_cast<Meter>(5)" "vec.emplace_back(5);")
ok() { "$@" >/dev/null 2>&1 && echo O || echo X; }
printf '%-3s %-24s %-8s %-8s %-8s %-8s\n' "#" "탐침" "g++" "g++ ex" "clang" "clang ex"
split=0; cc=0
for p in $(seq 1 15); do
  g0=$(ok g++ -std=c++20 -DPROBE=$p -c conv07.cpp -o /dev/null)
  g1=$(ok g++ -std=c++20 -DPROBE=$p -DASK_EXPLICIT -c conv07.cpp -o /dev/null)
  c0=$(ok clang++ -std=c++20 -DPROBE=$p -c conv07.cpp -o /dev/null)
  c1=$(ok clang++ -std=c++20 -DPROBE=$p -DASK_EXPLICIT -c conv07.cpp -o /dev/null)
  printf '%-3s %-24s %-8s %-8s %-8s %-8s\n' "$p" "${names[$p]}" "$g0" "$g1" "$c0" "$c1"
  [ "$g0" != "$g1" ] && split=$((split+1))
  [ "$g0$g1" != "$c0$c1" ] && cc=$((cc+1))
done
echo "explicit 로 갈린 칸 $split / 15 · 두 컴파일러가 갈린 칸 $cc / 15"
```

```text
===== bash conv-grid.sh (exit=0) =====
#   탐침                   g++      g++ ex   clang    clang ex
1   Meter a = 5;             O        X        O        X       
2   take(5);                 O        X        O        X       
3   return 5;                O        X        O        X       
4   return {5};              O        X        O        X       
5   take({5});               O        X        O        X       
6   m == 5                   O        X        O        X       
7   c ? m : 5                O        X        O        X       
8   Meter a = {5};           O        X        O        X       
9   Meter arr[] = {5, 6};    O        X        O        X       
10  vec.push_back(5);        O        X        O        X       
11  Meter a(5);              O        O        O        O       
12  Meter a{5};              O        O        O        O       
13  Meter a = Meter(5);      O        O        O        O       
14  static_cast<Meter>(5)    O        O        O        O       
15  vec.emplace_back(5);     O        O        O        O       
explicit 로 갈린 칸 10 / 15 · 두 컴파일러가 갈린 칸 0 / 15
```

**왜 그런가**

- ★★★ **`explicit 로 갈린 칸 10 / 15`** — 1\~10번(`=` · 인자 · `return` · `return {5}` · `take({5})` · `==` · 삼항 · `= {5}` · 배열 · `push_back`)은 **복사 초기화**, 11\~15번은 **직접 초기화**다.
- ★★★ **`push_back(5)` 는 인자 `const Meter&` 를 `5` 로 초기화**해야 해서 복사 초기화, **`emplace_back(5)` 는 안에서 `Meter(5)` 로 짓는** 직접 초기화다.
- ★ **`return {5};` 는 복사 리스트 초기화**, `Meter a{5};` 는 **직접 리스트 초기화** — 중괄호라는 모양이 아니라 **`=`·인자·반환 자리냐**가 가른다.
- ★ **`두 컴파일러가 갈린 칸 0 / 15`** — 표준 규칙이다.

### 4. ★★ **2번·3번이 에러** — 사용자 정의 변환이 **두 번** 필요하다. 4번은 **직접 초기화**라 한 번이면 된다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 conv02.cpp -o ex (cc exit=1) =====
conv02.cpp: In function ‘int main()’:
conv02.cpp:14:11: error: could not convert ‘(const char*)"lee"’ from ‘const char*’ to ‘Name’
   14 |     greet("lee");                // 2. 리터럴을 넘긴다
      |           ^~~~~
      |           |
      |           const char*
conv02.cpp:15:14: error: conversion from ‘const char [5]’ to non-scalar type ‘Name’ requested
   15 |     Name n = "park";             // 3. 리터럴로 복사 초기화
      |              ^~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 conv02.cpp -o ex (cc exit=1) =====
conv02.cpp:14:5: error: no matching function for call to 'greet'
   14 |     greet("lee");                // 2. 리터럴을 넘긴다
      |     ^~~~~
conv02.cpp:10:6: note: candidate function not viable: no known conversion from 'const char[4]' to 'Name' for 1st argument
   10 | void greet(Name n) { std::printf("greet(%s)\n", n.s.c_str()); }
      |      ^     ~~~~~~
conv02.cpp:15:10: error: no viable conversion from 'const char[5]' to 'Name'
   15 |     Name n = "park";             // 3. 리터럴로 복사 초기화
      |          ^   ~~~~~~
conv02.cpp:6:8: note: candidate constructor (the implicit copy constructor) not viable: no known conversion from 'const char[5]' to 'const Name &' for 1st argument
    6 | struct Name {
      |        ^~~~
conv02.cpp:6:8: note: candidate constructor (the implicit move constructor) not viable: no known conversion from 'const char[5]' to 'Name &&' for 1st argument
    6 | struct Name {
      |        ^~~~
conv02.cpp:8:5: note: candidate constructor not viable: no known conversion from 'const char[5]' to 'std::string' (aka 'basic_string<char>') for 1st argument
    8 |     Name(std::string x) : s(std::move(x)) {}
      |     ^    ~~~~~~~~~~~~~
2 errors generated.
```

**왜 그런가**

- ★★★ **리터럴 → `std::string` → `Name` 은 사용자 정의 변환 둘**이다. 암묵 변환 순서에는 **사용자 정의 변환이 0\~1 번**뿐이다.
- ★★ **`Name m("choi")` 는 `Name(std::string)` 의 인자 `x` 를 `"choi"` 로 초기화**하는 것이라 **`const char*` → `string` 한 번**이다.

### 5. ★★★ **`show(bool)` · `show(const std::string&)` · `put(double)` · `len(Meter)` · `len(Meter)`** — 경고는 **g++ 0 · clang 은 `-Wconversion` 일 때 1**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) show("hello")
    show(bool) 1
(2) show(std::string("hello"))
    show(const std::string&) "hello"
(3) put(3)
    put(double) 3
(4) len('A')
    len(Meter) 65
(5) len(true)
    len(Meter) 1
```

```text
===== echo "g++   -Wall -Wextra -pedantic               경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic               경고 0
===== echo "g++   -Wall -Wextra -pedantic -Wconversion  경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -Wconversion -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -Wall -Wextra -pedantic -Wconversion  경고 0
===== echo "clang -Wall -Wextra -pedantic               경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic               경고 0
===== echo "clang -Wall -Wextra -pedantic -Wconversion  경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -Wconversion -c conv05.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -Wall -Wextra -pedantic -Wconversion  경고 1
===== echo "clang -Weverything 중 -Wstring-conversion   경고 $(clang++ -std=c++20 -Weverything -c conv05.cpp -o /dev/null 2>&1 | grep -c 'Wstring-conversion')" (exit=0) =====
clang -Weverything 중 -Wstring-conversion   경고 1
```

**왜 그런가**

- ★★★ **`"hello"` → `bool` 은 표준 변환**, `"hello"` → `std::string` 은 **사용자 정의 변환**이다. **표준 변환 순서가 이긴다** — 문자열을 찍으려던 줄이 `1` 을 찍었다.
- ★★ **`put(3)` 도 같다** — `int` → `double`(표준) 이 `int` → `Meter`(사용자 정의) 를 이긴다.
- ★★ **`(4)` 는 안 걸린다** — `char` → `int`(표준, 승격) + `int` → `Meter`(사용자 정의 한 번)이다. 「한 번뿐」은 **사용자 정의 변환의 횟수**다.
- ★★★ **g++ 는 `-Wconversion` 으로도 0**, clang 은 `-Wconversion` 아래의 `-Wstring-conversion` 이 `(1)` **하나만** 본다. **`(3)`\~`(5)` 는 아무도 말하지 않는다.**

### 6. ★★★ **7\~10번이 에러** · 떼면 **`h + k` 가 2 · `h == k` 가 1** — 4번은 **문맥적 변환**, 7번은 **복사 초기화**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 conv03.cpp -o ex (cc exit=1) =====
conv03.cpp: In function ‘int main()’:
conv03.cpp:24:15: error: cannot convert ‘Handle’ to ‘bool’ in initialization
   24 |     bool b3 = h;                         std::printf("7. bool b3 = h  %d\n", (int)b3);
      |               ^
      |               |
      |               Handle
conv03.cpp:25:15: error: cannot convert ‘Handle’ to ‘int’ in initialization
   25 |     int  n  = h;                         std::printf("8. int n = h    %d\n", n);
      |               ^
      |               |
      |               Handle
conv03.cpp:26:17: error: no match for ‘operator+’ (operand types are ‘Handle’ and ‘Handle’)
   26 |     int  s  = h + k;                     std::printf("9. h + k        %d\n", s);
      |               ~ ^ ~
      |               |   |
      |               |   Handle
      |               Handle
conv03.cpp:26:17: note: candidate: ‘operator+(int, int)’ (built-in)
   26 |     int  s  = h + k;                     std::printf("9. h + k        %d\n", s);
      |               ~~^~~
conv03.cpp:26:17: note:   no known conversion for argument 2 from ‘Handle’ to ‘int’
conv03.cpp:27:50: error: no match for ‘operator==’ (operand types are ‘Handle’ and ‘Handle’)
   27 |     std::printf("10. h == k       %d\n", (int)(h == k));
      |                                                ~ ^~ ~
      |                                                |    |
      |                                                |    Handle
      |                                                Handle
conv03.cpp:27:50: note: candidate: ‘operator==(int, int)’ (built-in)
   27 |     std::printf("10. h == k       %d\n", (int)(h == k));
      |                                                ~~^~~~
conv03.cpp:27:50: note:   no known conversion for argument 2 from ‘Handle’ to ‘int’
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_IMPLICIT conv03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1. if (h)
2. !h
3. h && k
4. h ? 1 : 0    1
5. bool b1(h)   1
6. static_cast  1
7. bool b3 = h  1
8. int n = h    1
9. h + k        2
10. h == k       1
```

**왜 그런가**

- ★★★ **1\~6번은 `bool t(h);` 꼴**(문맥적 변환 · 직접 초기화 · `static_cast`)이라 `explicit` 변환 함수가 **후보가 된다.**
- ★★★ **7번 `bool b3 = h;` 는 복사 초기화**라 막히고, 8\~10번은 **`bool` 을 거쳐 `int` 로 가야** 하는 암묵 변환이라 막힌다.
- ★★★ **`explicit` 을 떼면 `fd` 3·4 인 핸들이 더해서 2, 비교해서 「같다」(1)** 가 된다 — **`cc exit=0` · 경고 0건**이다.

### 7. ★★ **g++ — 괄호·복사 초기화 통과(경고 0) · `{d}` 경고** · **clang — 괄호·복사 초기화 경고 · `{d}` 에러** · 상수 `{3.5}` 는 **g++ 도 에러**

**출력**

```cpp
/* conv06.cpp */
// int 를 받는 생성자에 double 을 넘긴다 — 괄호·복사 초기화·중괄호
// -DASK_CONST 이면 중괄호에 상수를 넣은 줄을 켠다
#include <cstdio>

struct Meter { int v; Meter(int x) : v(x) {} };

int main() {
    double d = 3.5;
    Meter a(3.5);         // 1. 괄호 · 상수
    Meter b = 3.5;        // 2. 복사 초기화 · 상수
    Meter c{d};           // 3. 중괄호 · 변수
#ifdef ASK_CONST
    Meter e{3.5};         // 4. 중괄호 · 상수
    (void)e;
#endif
    std::printf("a.v=%d b.v=%d c.v=%d\n", a.v, b.v, c.v);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv06.cpp: In function ‘int main()’:
conv06.cpp:11:13: warning: narrowing conversion of ‘d’ from ‘double’ to ‘int’ [-Wnarrowing]
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
a.v=3 b.v=3 c.v=3
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 conv06.cpp -o ex (cc exit=1) =====
conv06.cpp:9:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
    9 |     Meter a(3.5);         // 1. 괄호 · 상수
      |           ~ ^~~
conv06.cpp:10:15: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
   10 |     Meter b = 3.5;        // 2. 복사 초기화 · 상수
      |               ^~~
conv06.cpp:11:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
conv06.cpp:11:13: note: insert an explicit cast to silence this issue
   11 |     Meter c{d};           // 3. 중괄호 · 변수
      |             ^
      |             static_cast<int>( )
2 warnings and 1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONST -fmax-errors=0 conv06.cpp -o ex 2>&1 | grep -E 'error:|warning:' (cc exit=1) =====
conv06.cpp:11:13: warning: narrowing conversion of ‘d’ from ‘double’ to ‘int’ [-Wnarrowing]
conv06.cpp:13:16: error: narrowing conversion of ‘3.5e+0’ from ‘double’ to ‘int’ [-Wnarrowing]
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DASK_CONST -ferror-limit=0 conv06.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=1) =====
conv06.cpp:9:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
conv06.cpp:10:15: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
conv06.cpp:11:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
conv06.cpp:13:13: error: type 'double' cannot be narrowed to 'int' in initializer list [-Wc++11-narrowing]
conv06.cpp:13:13: warning: implicit conversion from 'double' to 'int' changes value from 3.5 to 3 [-Wliteral-conversion]
3 warnings and 2 errors generated.
```

**왜 그런가**

- ★★ **좁히기 금지는 중괄호의 규칙**이다 — 괄호·`=` 로 넘기면 `3.5` 가 **조용히 `3`** 이 된다(g++ 는 경고도 없다).
- ★★ **g++ 는 비상수 좁히기를 경고로 통과**시킨다 — [4번](../04-brace-initialization-narrowing-and-initializer-list/) (4)가 정본이다. 상수 `3.5` 는 **에러**다.

### 8. ★ **`cc exit=0`**(두 컴파일러 · 경고 1) — `-pedantic-errors` 로 **에러 1 · 1**

**출력**

```cpp
/* conv04.cpp */
// C++20 explicit(bool) — 인자 타입에 따라 explicit 을 켜고 끈다
#include <cstdio>
#include <type_traits>

struct Num {
    long v;
    template <class U>
    explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
};

int main() {
    Num a = 5;                    // 1. int 로 복사 초기화
    Num b{2.5};                   // 2. double 로 직접 초기화
#ifdef ASK_COPY
    Num c = 2.5;                  // 3. double 로 복사 초기화
    (void)c;
#endif
    std::printf("a.v=%ld b.v=%ld\n", a.v, b.v);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv04.cpp:8:5: warning: ‘explicit(bool)’ only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
    8 |     explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
      |     ^~~~~~~~
a.v=5 b.v=2
===== clang++ -std=c++17 -Wall -Wextra -pedantic conv04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
conv04.cpp:8:13: warning: explicit(bool) is a C++20 extension [-Wc++20-extensions]
    8 |     explicit(!std::is_integral_v<U>) Num(U u) : v(static_cast<long>(u)) {}
      |             ^
1 warning generated.
a.v=5 b.v=2
```

```text
===== echo "g++   -std=c++17 -pedantic-errors 에러 $(g++ -std=c++17 -Wall -Wextra -pedantic-errors -c conv04.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
g++   -std=c++17 -pedantic-errors 에러 1
===== echo "clang -std=c++17 -pedantic-errors 에러 $(clang++ -std=c++17 -Wall -Wextra -pedantic-errors -c conv04.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
clang -std=c++17 -pedantic-errors 에러 1
```

**왜 그런가**

- ★★ **`explicit(bool)` 은 C++20 문법**이다 — C++17 모드에서는 ill-formed 인데 두 컴파일러가 **확장으로 받아 경고만** 낸다.
- ★ [22번](../22-operator-overloading/) (8)의 **`static operator()` 를 C++20 으로** 던진 항목과 같은 집안이다 — 「**`-std=` 는 강제가 아니라 기본값 선택**」.

### 9. ★★ **`is_convertible` 은 복사 초기화, `is_constructible` 은 직접 초기화**를 묻는다 — **0 · 1**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic conv08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int -> Imp       is_convertible 1   is_constructible 1
int -> Exp       is_convertible 0   is_constructible 1
BImp -> bool     is_convertible 1   is_constructible 1
BExp -> bool     is_convertible 0   is_constructible 1
BExp -> int      is_convertible 0   is_constructible 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic conv08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int -> Imp       is_convertible 1   is_constructible 1
int -> Exp       is_convertible 0   is_constructible 1
BImp -> bool     is_convertible 1   is_constructible 1
BExp -> bool     is_convertible 0   is_constructible 1
BExp -> int      is_convertible 0   is_constructible 0
```

**왜 그런가**

- ★★ `is_convertible<From, To>` 는 「`To t = from;` 꼴이 되나」, `is_constructible<To, From>` 은 「`To t(from);` 이 되나」다. **`explicit` 은 앞쪽만 닫는다.**
- ★ **3번 격자의 「복사 초기화 열 칸 / 직접 초기화 다섯 칸」 선과 같은 선**이다. `explicit operator bool` 도 **0 · 1** 이다.

### 10. ★★ **값의 뜻이 바뀌는 것(`Meter`·`Buffer(size_t)`)에 붙이고, 같은 값의 다른 표현(`BigInt`·`String`)에는 안 붙인다**

- ★★★ **`Buffer b = 64;` 가 「64바이트 버퍼」로 말없이 되면 안 된다** — `int` 가 **크기**라는 다른 뜻으로 바뀐다. `Meter m = 5;` 도 단위가 생긴다.
- ★★ **`BigInt x = 5L;` · `String s = "a";` 는 같은 값을 다른 모양으로 담는 것**이라 암묵이 편하고, [22번](../22-operator-overloading/)의 **대칭 연산**(`1 + x`)도 그것에 기댄다.
- ★ **`emplace_back`·직접 초기화는 `explicit` 을 통과한다** — `explicit` 은 「**말없이 바뀌는 것**」만 막는 도구이지 **그 타입을 못 만들게 하는 도구가 아니다**(3번).

### 11. 다른 주제와 잇기

- ★★★ **[22번](../22-operator-overloading/) (1)** — 대칭(`1 + a`)은 **암묵 변환을 허락해야** 얻는다. `explicit` 을 붙이면 **대칭을 잃고 사고를 막는다** — 이 편의 (1)(4)(5)가 그 사고다.
- ★ **[1번](../01-function-overloading-and-overload-resolution/)의 오버로드 해결 순위** — 표준 변환 순서 > 사용자 정의 변환 순서.
- ★ **[16번](../16-copy-constructor-and-copy-assignment/) (2)의 의무 생략** — `return 7;` 이 반환 객체를 **바로 짓는다**(prvalue).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `conv01.cpp` 호출 로그 | g++ · clang 각 1회 + `-DASK_EXPLICIT` 각 1회 | ★★★ `calls` **1·1·1·1·0·1** · explicit **에러 6 · 6** |
| `conv07.cpp` + `conv-grid.sh` | 15탐침 × explicit 유무 × 두 컴파일러 = 60회 | ★★★ **갈린 칸 10 / 15 · 컴파일러 간 0 / 15** |
| `conv08.cpp` 타입 특성 | g++ · clang 각 1회 | ★★ `int -> Exp` **0 · 1** |
| `conv02.cpp` 두 단계 | g++ · clang 각 1회 | ★★ **에러 2 · 2**(2·3번) |
| `conv05.cpp` 오버로드 | g++ · clang 실행 각 1회 + 경고 5판 | ★★★ **`show(bool)`** · 경고 **0·0·0·1·1** |
| `conv03.cpp` `operator bool` | g++ · clang 각 3판(기본 · `-DASK_CONTEXT_ONLY` · `-DASK_IMPLICIT`) | ★★★ **에러 4 · 4** · 떼면 **`h + k` 2 · `h == k` 1** |
| `conv06.cpp` 좁히기 | g++ · clang 각 2판 + `-pedantic-errors` 1회 | ★★ g++ `cc exit=0`(`3 3 3`) · clang `cc exit=1` |
| `conv04.cpp` `explicit(bool)` | C++20 실행 · 복사 초기화 에러 · C++17 실행 · `-pedantic-errors` | ★ C++17 **`cc exit=0`** → **에러 1 · 1** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ 13)에서만** 그렇다.

- ★★ **진단 문구 · 좁히기를 에러로 하나 경고로 하나 · 어느 경고 플래그가 무엇을 보나.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **`explicit` 생성자는 복사 초기화에서 후보가 아니다** · **사용자 정의 변환은 한 번** · **표준 변환 순서 > 사용자 정의 변환 순서** · **문맥적 bool 변환은 `bool t(e);`**.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **변환 생성자와 변환 함수가 동시에 있을 때의 모호성** · ★ **CTAD 의 `explicit` 추론 가이드** · ★ **`std::pair`·`std::optional` 의 조건부 `explicit` 소스.**
- ★ **「부적용인 창」** — ASan · 어셈블리. 변환은 **평범한 생성자 호출**이고 메모리를 건드리지 않는다.
- ★ 기준 소스 중 **cppreference 「변환 생성자」 쪽은 이 배치에서 열지 못했다**(도구 한도) — 해당 규칙은 전부 **던져서** 확인했다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **5번의 경고 격자** — g++ 가 문자열 → `bool` 경고를 내기 시작하는지.
- ★ **8번** — C++17 모드의 `explicit(bool)` 이 에러로 바뀌는지.
