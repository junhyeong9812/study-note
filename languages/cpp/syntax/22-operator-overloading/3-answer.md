# cpp/syntax/22 — 연산자 오버로딩 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구** · **진단의 전체 줄 수**다.\
> 근거로 쓰는 것은 다음이다 — **어느 줄이 에러인가 · 에러 개수 · `cc exit`** · **호출·평가 로그** · **`sizeof`** · **매크로가 있나**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **3번만 에러** — 멤버의 **왼쪽(`*this`)은 변환되지 않는다**. 비멤버면 되고 첫 인자는 **`1`**

**출력**

```cpp
/* opov01.cpp */
// operator+ 를 멤버로 둔다 — a + 1 은 되는데 1 + a 는 되나
struct Money {
    long won;
    Money(long w) : won(w) {}                        // 암묵 변환 생성자 — long 에서 Money 로
    Money operator+(const Money& o) const { return Money(won + o.won); }   // ★ 멤버
};

int main() {
    Money a(1000);
    Money b = a + a;                                 // 1. Money + Money
    Money c = a + 1;                                 // 2. Money + 정수 — 오른쪽이 변환된다
    Money d = 1 + a;                                 // 3. 정수 + Money — 왼쪽도 변환되나
    (void)b; (void)c; (void)d;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 opov01.cpp -o ex (cc exit=1) =====
opov01.cpp: In function ‘int main()’:
opov01.cpp:12:17: error: no match for ‘operator+’ (operand types are ‘int’ and ‘Money’)
   12 |     Money d = 1 + a;                                 // 3. 정수 + Money — 왼쪽도 변환되나
      |               ~ ^ ~
      |               |   |
      |               int Money
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov01.cpp -o ex (cc exit=1) =====
opov01.cpp:12:17: error: invalid operands to binary expression ('int' and 'Money')
   12 |     Money d = 1 + a;                                 // 3. 정수 + Money — 왼쪽도 변환되나
      |               ~ ^ ~
1 error generated.
```

```cpp
/* opov02.cpp */
// 같은 operator+ 를 비멤버로 옮긴다 — 이번에는 1 + a 가 되나
#include <cstdio>

struct Money {
    long won;
    Money(long w) : won(w) {}
    friend Money operator+(const Money& l, const Money& r) {   // ★ 비멤버(숨은 friend)
        std::printf("      operator+(%ld, %ld)\n", l.won, r.won);
        return Money(l.won + r.won);
    }
};

int main() {
    Money a(1000);
    std::printf("(1) a + a\n");  Money b = a + a;
    std::printf("(2) a + 1\n");  Money c = a + 1;
    std::printf("(3) 1 + a\n");  Money d = 1 + a;
    std::printf("    b=%ld c=%ld d=%ld\n", b.won, c.won, d.won);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a + a
      operator+(1000, 1000)
(2) a + 1
      operator+(1000, 1)
(3) 1 + a
      operator+(1, 1000)
    b=2000 c=1001 d=1001
```

**왜 그런가**

- ★★★ **`a + 1` 은 `a.operator+(1)`** — 인자 `1` 이 `Money(long)` 으로 **변환된다.**\
  **`1 + a` 는 `int` 에게서 멤버를 찾는다** — 없고, **`1` 을 `Money` 로 바꿔 멤버를 찾아 주지는 않는다.**
- ★★★ **비멤버면 두 자리가 평등하다** — 로그 `operator+(1, 1000)`. **왼쪽 `1` 이 `Money(1)` 로 변환되어** 첫 인자가 됐다.

### 2. ★★ **2번·3번 둘 다 에러** — 대칭을 만든 것은 **암묵 변환**이었다

**출력**

```cpp
/* opov12.cpp */
// 비멤버로 옮겼는데 생성자에 explicit 을 붙이면 — 대칭은 무엇 덕분이었나
struct Money {
    long won;
    explicit Money(long w) : won(w) {}                         // ★ 암묵 변환을 막았다
    friend Money operator+(const Money& l, const Money& r) { return Money(l.won + r.won); }
};

int main() {
    Money a(1000);
    Money b = a + a;                                 // 1. Money + Money
    Money c = a + 1;                                 // 2. Money + 정수
    Money d = 1 + a;                                 // 3. 정수 + Money
    (void)b; (void)c; (void)d;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 opov12.cpp -o ex 2>&1 | grep -E 'error:' (cc exit=1) =====
opov12.cpp:11:17: error: no match for ‘operator+’ (operand types are ‘Money’ and ‘int’)
opov12.cpp:12:17: error: no match for ‘operator+’ (operand types are ‘int’ and ‘Money’)
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov12.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
opov12.cpp:11:17: error: invalid operands to binary expression ('Money' and 'int')
opov12.cpp:12:17: error: invalid operands to binary expression ('int' and 'Money')
2 errors generated.
```

**왜 그런가**

- ★★★ **비멤버인데도 섞인 식 둘이 막힌다** — `explicit` 이 **정수 → `Money` 변환**을 막았다.
- ★★ **대칭 = 비멤버 × 암묵 변환**이다. 비멤버는 **두 자리를 평등하게** 만들 뿐이고, **평등하게 변환해 줄 재료**는 변환 생성자다.

### 3. ★★ **1번은 되고 `(1, 2)`** · 2번은 **에러**(g++ **338줄**) · **비멤버 + `std::ostream&` 반환**

**출력**

```cpp
/* opov03.cpp */
// operator<< 를 멤버로 두면 — 왼쪽 피연산자가 무엇이어야 하나
#include <iostream>

struct Pt {
    int x, y;
    std::ostream& operator<<(std::ostream& os) const {        // ★ 멤버 — 왼쪽이 Pt 다
        return os << '(' << x << ", " << y << ')';
    }
};

int main() {
    Pt p{1, 2};
    p << std::cout << '\n';                    // 1. 거꾸로 쓰면 된다
#ifdef CONVENTIONAL
    std::cout << p << '\n';                    // 2. 관례대로 쓰면
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1, 2)
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -fmax-errors=0 opov03.cpp -o ex 2>&1 | sed -n '1,8p' (cc exit=1) =====
opov03.cpp: In function ‘int main()’:
opov03.cpp:15:15: error: no match for ‘operator<<’ (operand types are ‘std::ostream’ {aka ‘std::basic_ostream<char>’} and ‘Pt’)
   15 |     std::cout << p << '\n';                    // 2. 관례대로 쓰면
      |     ~~~~~~~~~ ^~ ~
      |          |       |
      |          |       Pt
      |          std::ostream {aka std::basic_ostream<char>}
In file included from /usr/include/c++/13/iostream:41,
```

```text
===== echo "g++   진단 $(g++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -fmax-errors=0 opov03.cpp -o ex 2>&1 | wc -l)줄 · 후보 note $(g++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -fmax-errors=0 opov03.cpp -o ex 2>&1 | grep -c 'note: candidate')개" (exit=0) =====
g++   진단 338줄 · 후보 note 47개
===== echo "clang 진단 $(clang++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -ferror-limit=0 opov03.cpp -o ex 2>&1 | wc -l)줄 · 후보 note $(clang++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -ferror-limit=0 opov03.cpp -o ex 2>&1 | grep -c 'note: candidate')개" (exit=0) =====
clang 진단 147줄 · 후보 note 47개
```

**왜 그런가**

- ★★★ **멤버 `operator<<` 의 왼쪽은 `Pt`** 다 — 그래서 **`p << std::cout`** 가 된다. (1)과 같은 규칙이다.
- ★★ **`std::cout << p` 는 `ostream` 쪽에서 찾는다** — `ostream` 에 멤버를 **우리가 더할 수 없으니** 비멤버밖에 없다.\
  ★ g++ 가 **후보 47개**를 전부 나열해 338줄이 됐다(clang 147줄). **줄 수는 흔들리는 칸**이다.
- ★ **반환을 `std::ostream&` 로** 해야 `cout << a << b` 로 **이어 쓸 수** 있다.

### 4. ★★★ **g++ 13 은 안 된다 · clang 18 은 C++23 에서만** — `Self` 는 **0 · 1** · 매크로는 **없다**

**출력**

```cpp
/* opov05.cpp */
// C++23 「deducing this」 — operator[] 두 벌을 하나로 합친다. 이 판의 컴파일러가 받나
#include <cstdio>
#include <type_traits>

struct Row {
    int a[3]{10, 20, 30};
    template <class Self>
    auto&& operator[](this Self&& self, int i) {           // ★ 명시적 객체 매개변수
        std::printf("      Self 가 const 인가: %d\n",
                    (int)std::is_const_v<std::remove_reference_t<Self>>);
        return self.a[i];
    }
};

int main() {
    Row r;
    const Row& cr = r;
    r[0] = 99;
    int x = cr[0];
    std::printf("    x=%d\n", x);
    std::printf("    decltype(cr[0]) 가 const int& 인가: %d\n",
                (int)std::is_same_v<decltype(cr[0]), const int&>);
}
```

```text
===== g++ -std=c++23 -Wall -Wextra -pedantic -fmax-errors=0 opov05.cpp -o ex 2>&1 | sed -n '1,4p' (cc exit=1) =====
opov05.cpp:8:23: error: expected identifier before ‘this’
    8 |     auto&& operator[](this Self&& self, int i) {           // ★ 명시적 객체 매개변수
      |                       ^~~~
opov05.cpp:8:23: error: expected ‘,’ or ‘...’ before ‘this’
===== echo "g++ -std=c++23 에러 $(g++ -std=c++23 -Wall -Wextra -pedantic -fmax-errors=0 opov05.cpp -o ex 2>&1 | grep -c 'error:')건" (exit=0) =====
g++ -std=c++23 에러 9건
```

```text
===== clang++ -std=c++23 -Wall -Wextra -pedantic opov05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      Self 가 const 인가: 0
      Self 가 const 인가: 1
    x=99
    decltype(cr[0]) 가 const int& 인가: 1
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov05.cpp -o ex (cc exit=1) =====
opov05.cpp:8:23: error: explicit object parameters are incompatible with C++ standards before C++2b
    8 |     auto&& operator[](this Self&& self, int i) {           // ★ 명시적 객체 매개변수
      |                       ^~~~~~~~~~~~~~~~
1 error generated.
```

```text
===== echo "g++   -std=c++23 : $(g++ -std=c++23 -dM -E -x c++ /dev/null | grep -cE '__cpp_explicit_this_parameter')" (exit=0) =====
g++   -std=c++23 : 0
===== echo "clang -std=c++23 : $(clang++ -std=c++23 -dM -E -x c++ /dev/null | grep -cE '__cpp_explicit_this_parameter')" (exit=0) =====
clang -std=c++23 : 0
```

**왜 그런가**

- ★★★ **g++ 13.3.0 은 `-std=c++23` 으로도 에러 9건** — `expected identifier before 'this'`. **파서가 그 문법을 모른다.**
- ★★★ **clang 18 은 `-std=c++23` 에서 된다** — `Self` 를 **`Row&`(0) · `const Row&`(1)** 로 추론했고 `decltype(cr[0])` 는 **`const int&`** 다.\
  ★ `-std=c++20` 에서는 `incompatible with C++ standards before C++2b` 로 막는다.
- ★★★ **clang 18 은 기능을 받으면서 `__cpp_explicit_this_parameter` 를 정의하지 않는다**(0) — **매크로로 판정하면 틀린다.** 이유는 확인하지 않았다.
- ★ 두 벌 판(`opov04.cpp`)은 **양쪽 다 된다** — 요약 (3).

### 5. ★★ **4 · 1 · 4 · 8 · 16 · 32** — `[k,big]` 은 **16**(패딩) · `operator()` 호출 **된다** · 두 람다는 **다른 타입**

**출력**

```cpp
/* opov06.cpp */
// operator() 와 함수 객체 — 람다는 operator() 를 가진 이름 없는 클래스인가
#include <cstdio>
#include <string>
#include <type_traits>

struct Adder {                                   // 손으로 쓴 함수 객체
    int k;
    int operator()(int x) const { return x + k; }
};

int main() {
    int k = 5; long big = 7; std::string s = "abc";
    Adder add{k};
    auto lam0 = [](int x) { return x + 1; };             // 캡처 없음
    auto lam1 = [k](int x) { return x + k; };            // int 하나를 값으로
    auto lam2 = [&k](int x) { return x + k; };           // int 하나를 참조로
    auto lam3 = [k, big](int x) { return x + k + big; }; // int + long
    auto lam4 = [s](int x) { return x + (int)s.size(); };// string 하나를 값으로

    std::printf("(1) add(1)=%d · lam1(1)=%d · lam1.operator()(1)=%d\n", add(1), lam1(1), lam1.operator()(1));
    std::printf("(2) sizeof  Adder %zu · 캡처없음 %zu · [k] %zu · [&k] %zu · [k,big] %zu · [s] %zu\n",
                sizeof(Adder), sizeof(lam0), sizeof(lam1), sizeof(lam2), sizeof(lam3), sizeof(lam4));
    std::printf("(3) is_class<람다> %d · 캡처 없는 람다를 함수 포인터로: %d\n",
                (int)std::is_class_v<decltype(lam1)>, ((int (*)(int))lam0)(41));
    std::printf("(4) 같은 모양의 람다 둘은 같은 타입인가: %d\n",
                (int)std::is_same_v<decltype(lam1), decltype([k](int x) { return x + k; })>);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) add(1)=6 · lam1(1)=6 · lam1.operator()(1)=6
(2) sizeof  Adder 4 · 캡처없음 1 · [k] 4 · [&k] 8 · [k,big] 16 · [s] 32
(3) is_class<람다> 1 · 캡처 없는 람다를 함수 포인터로: 42
(4) 같은 모양의 람다 둘은 같은 타입인가: 0
```

**왜 그런가**

- ★★★ **람다는 `operator()` 를 가진 클래스**이고 **캡처가 멤버**다 — 그래서 `sizeof` 가 캡처만큼이고 `lam1.operator()(1)` 이 된다.
- ★★ **`[k,big]` 은 `int` 4 + `long` 8 인데 16** — **`long` 의 정렬(8)** 때문에 패딩이 들어갔다(멤버 순서는 **미명시**라 배치 자체는 구현의 선택이다).
- ★ **캡처 없음 1** — 빈 클래스도 1바이트다([12번](../12-class-basics-members-access-and-this/) (2)).
- ★ **같은 모양이어도 다른 타입** — 람다 식마다 **새 클로저 타입**이 생긴다.

### 6. ★★★ `(1)` 은 **안 찍히고** `(2)`·`(3)` 은 **찍힌다** — 순서는 **왼쪽 → 오른쪽**(C++17 부터 보장) · 경고 **0건**

**출력**

```cpp
/* opov07.cpp */
// && 를 오버로드하면 단락 평가가 사라지나 — 양쪽 피연산자에 로그를 심는다
#include <cstdio>

struct Flag {
    bool v;
    explicit operator bool() const { return v; }
};
Flag operator&&(Flag a, Flag b) { std::printf("      operator&& 본체\n"); return Flag{a.v && b.v}; }
Flag operator||(Flag a, Flag b) { std::printf("      operator|| 본체\n"); return Flag{a.v || b.v}; }

bool  left_b()  { std::printf("      왼쪽을 평가했다\n");  return false; }
bool  right_b() { std::printf("      오른쪽을 평가했다\n"); return true;  }
Flag  left_f()  { std::printf("      왼쪽을 평가했다\n");  return Flag{false}; }
Flag  right_f() { std::printf("      오른쪽을 평가했다\n"); return Flag{true};  }
Flag  yes_f()   { std::printf("      왼쪽을 평가했다\n");  return Flag{true};  }

int main() {
    std::printf("(1) 내장 &&   false && …\n");
    bool r1 = left_b() && right_b();
    std::printf("    결과 %d\n", (int)r1);
    std::printf("(2) 오버로드한 &&   Flag{false} && …\n");
    Flag r2 = left_f() && right_f();
    std::printf("    결과 %d\n", (int)r2.v);
    std::printf("(3) 오버로드한 ||   Flag{true} || …\n");
    Flag r3 = yes_f() || right_f();
    std::printf("    결과 %d\n", (int)r3.v);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 내장 &&   false && …
      왼쪽을 평가했다
    결과 0
(2) 오버로드한 &&   Flag{false} && …
      왼쪽을 평가했다
      오른쪽을 평가했다
      operator&& 본체
    결과 0
(3) 오버로드한 ||   Flag{true} || …
      왼쪽을 평가했다
      오른쪽을 평가했다
      operator|| 본체
    결과 1
```

**왜 그런가**

- ★★★ **오버로드한 `&&` 는 함수**다 — 부르기 전에 **인자 둘을 다 만든다.** 그래서 왼쪽이 `false` 여도 오른쪽을 평가한다.
- ★★ **순서 왼쪽 → 오른쪽은 C++17 부터 보장**이다 — 연산자 표기로 부른 오버로드는 **내장 연산자의 순서 규칙**을 따른다.\
  ★ **순서가 정해진 것과 건너뛰는 것은 다른 성질**이다 — 앞엣것은 지켜졌고 **뒤엣것(단락)은 사라졌다.**
- ★★★ **경고는 없다** — 두 컴파일러 다 이 파일에 **진단 0줄**(`cc exit=0`)이다. 호출 자리만 보면 **내장 `&&` 와 똑같이 생겼다.**

### 7. ★ **에러 5 · 5** — `->*` 는 **통과** · g++ 는 **`?:` 에만** 「ISO C++ prohibits overloading」

**출력**

```cpp
/* opov08.cpp */
// 오버로드할 수 없는 연산자 다섯 — 선언만 해 본다
struct X {
    int v;
    int operator.(int);                  // 1. 멤버 접근 .
    int operator.*(int);                 // 2. 멤버 포인터 접근 .*
    int operator::(int);                 // 3. 범위 해석 ::
    int operator?:(int, int);            // 4. 조건 ?:
    int operator sizeof();               // 5. sizeof
    int operator->*(int);                // 6. 대조군 — ->* 는 오버로드된다
};
int main() {}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 opov08.cpp -o ex (cc exit=1) =====
opov08.cpp:4:17: error: expected type-specifier before ‘.’ token
    4 |     int operator.(int);                  // 1. 멤버 접근 .
      |                 ^
opov08.cpp:5:17: error: expected type-specifier before ‘.*’ token
    5 |     int operator.*(int);                 // 2. 멤버 포인터 접근 .*
      |                 ^~
opov08.cpp:6:17: error: expected type-specifier before ‘::’ token
    6 |     int operator::(int);                 // 3. 범위 해석 ::
      |                 ^~
opov08.cpp:7:9: error: ISO C++ prohibits overloading ‘operator ?:’
    7 |     int operator?:(int, int);            // 4. 조건 ?:
      |         ^~~~~~~~
opov08.cpp:8:18: error: expected type-specifier before ‘sizeof’
    8 |     int operator sizeof();               // 5. sizeof
      |                  ^~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov08.cpp -o ex (cc exit=1) =====
opov08.cpp:4:17: error: expected a type
    4 |     int operator.(int);                  // 1. 멤버 접근 .
      |                 ^
opov08.cpp:5:17: error: expected a type
    5 |     int operator.*(int);                 // 2. 멤버 포인터 접근 .*
      |                 ^
opov08.cpp:6:17: error: expected a type
    6 |     int operator::(int);                 // 3. 범위 해석 ::
      |                 ^
opov08.cpp:7:17: error: expected a type
    7 |     int operator?:(int, int);            // 4. 조건 ?:
      |                 ^
opov08.cpp:8:18: error: expected a type
    8 |     int operator sizeof();               // 5. sizeof
      |                  ^
5 errors generated.
```

**왜 그런가**

- ★★ **`.`·`.*`·`::`·`sizeof` 는 `operator` 뒤에 올 수 있는 낱말이 아니다** — 파서가 **`expected type-specifier`** 로 막는다.
- ★★ **`?:` 는 파서가 읽은 뒤 규칙으로** 막는다 — 그래서 문구가 다르다(내 추론 — 근거는 **문구가 갈린 것**뿐이다).
- ★ clang 은 다섯 다 **`expected a type`** 이다.

### 8. ★★ **넷 다 에러 · `operator+` 는 통과** — g++ 의 문구 차이는 **C++23 의 `static` 허용**을 반영한 것으로 보인다

**출력**

```cpp
/* opov09.cpp */
// 멤버여야만 하는 연산자 넷을 비멤버로 선언해 본다
struct X { int v; int* p; };
X&   operator=(X& l, const X& r);        // 1. 대입
int& operator[](X& x, int i);            // 2. 첨자
int  operator()(X& x, int i);            // 3. 호출
int* operator->(X& x);                   // 4. 멤버 접근 ->
X    operator+(const X& l, const X& r);  // 5. 대조군 — 이것은 비멤버가 된다
int main() {}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 opov09.cpp -o ex (cc exit=1) =====
opov09.cpp:3:6: error: ‘X& operator=(X&, const X&)’ must be a non-static member function
    3 | X&   operator=(X& l, const X& r);        // 1. 대입
      |      ^~~~~~~~
opov09.cpp:4:6: error: ‘int& operator[](X&, int)’ must be a member function
    4 | int& operator[](X& x, int i);            // 2. 첨자
      |      ^~~~~~~~
opov09.cpp:5:6: error: ‘int operator()(X&, int)’ must be a member function
    5 | int  operator()(X& x, int i);            // 3. 호출
      |      ^~~~~~~~
opov09.cpp:6:6: error: ‘int* operator->(X&)’ must be a non-static member function
    6 | int* operator->(X& x);                   // 4. 멤버 접근 ->
      |      ^~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov09.cpp -o ex (cc exit=1) =====
opov09.cpp:3:6: error: overloaded 'operator=' must be a non-static member function
    3 | X&   operator=(X& l, const X& r);        // 1. 대입
      |      ^
opov09.cpp:4:6: error: overloaded 'operator[]' must be a non-static member function
    4 | int& operator[](X& x, int i);            // 2. 첨자
      |      ^
opov09.cpp:5:6: error: overloaded 'operator()' must be a non-static member function
    5 | int  operator()(X& x, int i);            // 3. 호출
      |      ^
opov09.cpp:6:6: error: overloaded 'operator->' must be a non-static member function
    6 | int* operator->(X& x);                   // 4. 멤버 접근 ->
      |      ^
4 errors generated.
```

**왜 그런가**

- ★★ **`=`·`[]`·`()`·`->` 는 비멤버가 될 수 없다**(기준 소스). 에러 **4 · 4**.
- ★ g++ 는 `[]`·`()` 에 **「member function」**, `=`·`->` 에 **「non-static member function」** 이라 쓴다 — C++23 이 앞의 둘에 **`static` 을 허락**했기 때문으로 보인다(추론). clang 은 넷 다 `non-static` 이다.

### 9. ★★ **`cc exit=0`**(양쪽 경고 1건) — **`-pedantic-errors`** 라야 막힌다

**출력**

```cpp
/* opov10.cpp */
// C++23 의 static operator() 를 -std=c++20 으로 던진다 — 빌드가 되나
#include <cstdio>

struct Inc {
    static int operator()(int x) { return x + 1; }     // ★ C++23 부터 허용되는 형태
};

int main() { std::printf("Inc{}(41) = %d\n", Inc{}(41)); }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
opov10.cpp:5:16: warning: ‘static int Inc::operator()(int)’ may be a static member function only with ‘-std=c++23’ or ‘-std=gnu++23’ [-Wc++23-extensions]
    5 |     static int operator()(int x) { return x + 1; }     // ★ C++23 부터 허용되는 형태
      |                ^~~~~~~~
Inc{}(41) = 42
===== clang++ -std=c++20 -Wall -Wextra -pedantic opov10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
opov10.cpp:5:16: warning: declaring overloaded 'operator()' as 'static' is a C++23 extension [-Wc++23-extensions]
    5 |     static int operator()(int x) { return x + 1; }     // ★ C++23 부터 허용되는 형태
      |                ^
1 warning generated.
Inc{}(41) = 42
```

```text
===== echo "g++ -pedantic-errors 에러 $(g++ -std=c++20 -Wall -Wextra -pedantic-errors -fmax-errors=0 opov10.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
g++ -pedantic-errors 에러 1
===== echo "clang -pedantic-errors 에러 $(clang++ -std=c++20 -Wall -Wextra -pedantic-errors -ferror-limit=0 opov10.cpp -o ex 2>&1 | grep -c 'error:')" (exit=0) =====
clang -pedantic-errors 에러 1
```

**왜 그런가**

- ★★★ **C++20 에서 `operator()` 는 비`static` 멤버여야 한다** — 이 코드는 **ill-formed** 인데 **두 컴파일러가 경고만 내고 통과시켰고 값도 맞다**(`42`).
- ★★ **`-pedantic-errors` 로 양쪽 에러 1** — 앞 배치의 **세 건**(g++ 좁히기 · clang 지정 초기자 · g++ 매개변수 `auto`)과 [18번](../18-rule-of-zero-three-five-default-delete/) (7)의 익명 구조체에 이어 **같은 집안**이다.

### 10. ★★ `+` **비멤버** · `<<` **비멤버** · `+=` **멤버** · `[]` **멤버 두 벌** · `&&` **오버로드하지 않는다**

**출력** — 요약의 「형태」 절.

```cpp
/* opov11.cpp */
// 연산자 오버로딩 한 벌의 형태. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <iostream>

class Vec2 {
public:
    Vec2(double x = 0, double y = 0) : x_(x), y_(y) {}

    Vec2& operator+=(const Vec2& o) { x_ += o.x_; y_ += o.y_; return *this; }   // ① 복합 대입은 멤버
    Vec2  operator-() const { return Vec2(-x_, -y_); }                          // ② 단항은 멤버
    double&       operator[](int i)       { return i == 0 ? x_ : y_; }          // ③ [] 는 두 벌
    const double& operator[](int i) const { return i == 0 ? x_ : y_; }

    friend Vec2 operator+(Vec2 l, const Vec2& r) { l += r; return l; }          // ④ 이항은 비멤버 — += 로 만든다
    friend bool operator==(const Vec2&, const Vec2&) = default;                 // ⑤ C++20 — != 는 따로 안 쓴다
    friend std::ostream& operator<<(std::ostream& os, const Vec2& v) {          // ⑥ << 는 비멤버
        return os << '(' << v.x_ << ", " << v.y_ << ')';
    }
private:
    double x_, y_;
};

int main() {
    Vec2 a(1, 2), b(3, 4);
    Vec2 c = a + b;
    Vec2 d = 1 + a;                        // 대칭 — 1 이 Vec2(1, 0) 으로 변환된다
    std::cout << c << ' ' << d << ' ' << -a << '\n';
    std::cout << (c == Vec2(4, 6)) << ' ' << (c != d) << ' ' << c[1] << '\n';
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(4, 6) (2, 2) (-1, -2)
1 1 6
```

**왜 그런가**

- ★★★ **이항 `+` 는 두 자리가 평등해야** 하므로 비멤버, **`<<` 는 왼쪽이 `ostream`** 이라 비멤버.
- ★★ **`+=` 는 자기 자신을 바꾸므로** 멤버, **`[]` 는 멤버여야만 하고** 읽기·쓰기 두 벌.
- ★★★ **`&&` 는 단락 평가를 잃으므로** 오버로드하지 않는다 — `explicit operator bool` 로 **내장 `&&`** 를 쓰게 한다.
- ★ **`+` 를 `+=` 로 만들면** 산술 규칙이 **한 곳**에만 있다. 형태의 ④ 가 `Vec2 l` 을 **값으로 받아** `l += r` 하고 돌려준다.

### 11. 다른 주제와 잇기

- ★★★ **비교 연산자에서는 재작성 후보가 대칭을 푼다** — 멤버 `operator<=>(long)` 하나로 **`5000 < a`** 가 된다. [23번](../23-three-way-comparison-spaceship/) (6)이다.
- ★ **[6번](../06-namespaces-and-adl/)의 ADL** — 인자에 `Money` 가 있으면 `Money` 의 숨은 friend 가 후보가 된다.
- ★ Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **30번** — `impl Add<Money> for i64` 처럼 **방향마다 구현**을 쓴다(그 편이 아직 없어 **이 편은 던지지 않았다**).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `opov01.cpp` 멤버 `+` | g++ · clang 각 1회 | ★★★ **3번 줄만 에러** · `cc exit=1` |
| `opov02.cpp` 비멤버 `+` | g++ · clang 각 1회 | ★★★ 셋 다 됨 · 로그 `operator+(1, 1000)` |
| `opov12.cpp` `explicit` | g++ · clang 각 1회 | ★★ **에러 2 · 2** |
| `opov03.cpp` 멤버 `<<` | g++ 1회 실행 + g++ · clang 에러 각 1회 + 줄 수 셈 | ★★ `(1, 2)` · **338줄 · 147줄** · 후보 **47 · 47** |
| `opov04.cpp` `[]` 두 벌 | g++ · clang 각 2회(실행 · `-DWRITE_CONST`) | ★★ 비`const`/`const` 판 · const 판 쓰기는 에러 |
| `opov05.cpp` deducing `this` | g++ `c++23` · clang `c++20`/`c++23` + 매크로 2회 | ★★★ **g++ 에러 9** · clang 23 **됨** · 매크로 **0 · 0** |
| `opov06.cpp` 람다 | g++ · clang 각 1회 | ★★ **4 · 1 · 4 · 8 · 16 · 32** |
| `opov07.cpp` `&&`·`\|\|` | g++ · clang 각 1회 | ★★★ 오버로드 판만 **오른쪽 평가** · 경고 0 |
| `opov08.cpp`·`opov09.cpp` | g++ · clang 각 1회 | ★ **에러 5 · 5** · **4 · 4** |
| `opov10.cpp` `static operator()` | g++ · clang 각 2회(`-pedantic` · `-pedantic-errors`) | ★★ **`cc exit=0`** → **에러 1 · 1** |
| `opov11.cpp` 형태 | g++ · clang 각 1회 | `(4, 6) (2, 2) (-1, -2)` · `1 1 6` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ 13)에서만** 그렇다.

- ★★ **클로저 타입의 `sizeof`**(패딩 포함) · **진단 문구와 줄 수** · **기능 매크로를 정의하나.**
- ★★★ **deducing `this` 를 받나** — 판에 매인다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **멤버 연산자의 `*this` 자리는 변환되지 않는** 것 · **비멤버는 두 자리가 똑같이 변환을 받는** 것.
- ★★★ **오버로드한 `&&`·`||` 는 단락 평가가 없는** 것 · **C++17 부터 피연산자가 왼쪽 → 오른쪽**인 것.
- ★★ **오버로드 불가 넷**(`::`·`.`·`.*`·`?:`)과 **멤버 필수 넷**(`=`·`()`·`[]`·`->`).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **Rust 30번의 대칭**(그 편이 없다) · ★ **g++ 14 이상의 deducing `this`** · ★ **다차원 `operator[]`(C++23)** — 이 편 본문에는 싣지 않았다(주장에도 쓰지 않았다) · ★ **캡처 멤버의 순서.**
- ★ **「부적용인 창」** — ASan · 어셈블리. 연산자 호출은 **평범한 함수 호출**이다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번 전부** — g++ 가 deducing `this` 를 받기 시작하는지, clang 이 매크로를 정의하기 시작하는지.
- ★★ **9번** — `static operator()` 의 경고가 에러로 바뀌는지.
- ★ **3번의 진단 줄 수**(표준 라이브러리 판).
