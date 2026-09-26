# cpp/syntax/32 — 클래스 템플릿과 CTAD(C++17) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 타입 이름의 철자 · `sizeof(std::string)`** 이다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · 격자 칸의 타입 · 「갈린 칸 N / M」 · `nm` 의 글자와 기호의 유무**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **적은 선언은 C++14 에서도 통과** · **안 적은 선언은 C++14 에서 에러(g++ 2건 · clang 1건), C++17 에서 통과**

**출력**

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
===== clang++ -std=c++14 -Wall -Wextra -pedantic ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
```

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex (cc exit=1) =====
ctad01.cpp: In function ‘int main()’:
ctad01.cpp:14:9: error: missing template arguments before ‘b’
   14 |     Box b(2);
      |         ^
ctad01.cpp:15:35: error: ‘b’ was not declared in this scope
   15 |     std::printf("b.get() = %d\n", b.get());
      |                                   ^
```

```text
===== clang++ -std=c++14 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex (cc exit=1) =====
ctad01.cpp:14:5: error: use of class template 'Box' requires template arguments
   14 |     Box b(2);
      |     ^
ctad01.cpp:4:27: note: template is declared here
    4 | template <class T> struct Box {
      | ~~~~~~~~~~~~~~~~~~        ^
1 error generated.
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
b.get() = 2
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DOMIT ctad01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a.get() = 1
b.get() = 2
```

**왜 그런가**

- ★★★ **C++14 에는 클래스 템플릿의 인자를 추론하는 규칙이 없다** — 함수 템플릿만 추론했다. C++17 의 CTAD 가 그 규칙이다.
- ★ g++ 의 둘째 에러(`‘b’ was not declared`)는 **첫째의 여파**다 — 선언이 실패해 이름이 없어졌다.

### 2. ★★★ **`Box<int>` 셋 · `Box<char const*>` · 에러 · `Duo<int, double>` · `vector<int>` · `vector<int>` · `vector<vector<int>>` · `pair<int, char const*>` · `array<int, 3>`** — **판이 가른 칸 20 / 22 · 컴파일러가 가른 칸 0 / 22**

**출력**

```text
===== bash ctad-grid.sh (exit=0) =====
선언	g++ c++14	g++ c++17	clang++ c++14	clang++ c++17
Box x{1};	error	Box<int>	error	Box<int>
Box x(1);	error	Box<int>	error	Box<int>
Box x = 1;	error	Box<int>	error	Box<int>
Box x{"hi"};	error	Box<char const*>	error	Box<char const*>
Box x{1, 2.0};	error	error	error	error
Duo x{1, 2.0};	error	Duo<int, double>	error	Duo<int, double>
std::vector x{1, 2};	error	std::vector<int, std::allocator<int> >	error	std::vector<int, std::allocator<int> >
std::vector x{v2};	error	std::vector<int, std::allocator<int> >	error	std::vector<int, std::allocator<int> >
std::vector x{v2, v2};	error	std::vector<std::vector<int, std::allocator<int> >, std::allocator<std::vector<int, std::allocator<int> > > >	error	std::vector<std::vector<int, std::allocator<int> >, std::allocator<std::vector<int, std::allocator<int> > > >
std::pair x{1, "a"};	error	std::pair<int, char const*>	error	std::pair<int, char const*>
std::array x{1, 2, 3};	error	std::array<int, 3ul>	error	std::array<int, 3ul>
c++14 대 c++17 이 갈린 칸 20 / 22 · g++ 대 clang++ 가 갈린 칸 0 / 22
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DCASE=5 ctad02.cpp -o ex (cc exit=1) =====
ctad02.cpp: In function ‘int main()’:
ctad02.cpp:32:17: error: class template argument deduction failed:
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:32:17: error: no matching function for call to ‘Box(int, double)’
ctad02.cpp:11:5: note: candidate: ‘template<class T> Box(T, T)-> Box<T>’
   11 |     Box(T x, T) : v(x) {}
      |     ^~~
ctad02.cpp:11:5: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   deduced conflicting types for parameter ‘T’ (‘int’ and ‘double’)
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:10:5: note: candidate: ‘template<class T> Box(T)-> Box<T>’
   10 |     Box(T x) : v(x) {}
      |     ^~~
ctad02.cpp:10:5: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   candidate expects 1 argument, 2 provided
   32 |     Box x{1, 2.0};
      |                 ^
ctad02.cpp:8:27: note: candidate: ‘template<class T> Box(Box<T>)-> Box<T>’
    8 | template <class T> struct Box {
      |                           ^~~
ctad02.cpp:8:27: note:   template argument deduction/substitution failed:
ctad02.cpp:32:17: note:   mismatched types ‘Box<T>’ and ‘int’
   32 |     Box x{1, 2.0};
      |                 ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DCASE=5 ctad02.cpp -o ex (cc exit=1) =====
ctad02.cpp:32:9: error: no viable constructor or deduction guide for deduction of template arguments of 'Box'
   32 |     Box x{1, 2.0};
      |         ^
ctad02.cpp:11:5: note: candidate template ignored: deduced conflicting types for parameter 'T' ('int' vs. 'double')
   11 |     Box(T x, T) : v(x) {}
      |     ^
ctad02.cpp:10:5: note: candidate function template not viable: requires single argument 'x', but 2 arguments were provided
   10 |     Box(T x) : v(x) {}
      |     ^   ~~~
ctad02.cpp:8:27: note: candidate function template not viable: requires 1 argument, but 2 were provided
    8 | template <class T> struct Box {
      |                           ^~~
1 error generated.
```

**왜 그런가**

- ★★★ **c++14 열은 전부 `error`**(CTAD 가 없다), **c++17 열은 `Box x{1, 2.0}` 만 `error`** — 두 판이 같은 두 칸이 그 행이다.
- ★★★ **`std::vector x{v2}` 는 감싸지 않고 복사한다** — 복사 추론 후보가 이긴다(7번). **`{v2, v2}` 만** `initializer_list` 생성자로 감싼다.
- ★★ **`Box x{"hi"}` 는 값 매개변수라 감쇠**, **`Box x{1, 2.0}` 은 `Box(T, T)` 에서 충돌** — 8번.

### 3. ★★ **`Box<char const*>` → `Box<std::string>`**(두 컴파일러 같다) · `sizeof` 는 **8 → 32** — 둘 다 **구현이 정한 값**이다

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<char const*>
sizeof(x)   = 8
===== g++ -std=c++17 -Wall -Wextra -pedantic -DWITH_GUIDE ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >
sizeof(x)   = 32
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<char const*>
sizeof(x)   = 8
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DWITH_GUIDE ctad03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Box<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > >
sizeof(x)   = 32
```

**왜 그런가**

- ★★ **가이드는 「이 인자면 이 타입」만 정한다** — 생성자는 그대로이고, `Box<std::string>` 의 `Box(std::string)` 이 `"hi"` 를 변환해 받는다.
- ★ 8 은 이 판의 포인터 크기, **32 는 libstdc++ 의 `std::string` 크기**다 — 표준은 둘 다 정하지 않는다.

### 4. ★★ **`8 8`** · ★★★ **g++ `wrong number of template arguments (1, should be 2)` · clang `too few template arguments for class template 'Duo'`**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
8 8
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
8 8
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DPARTIAL ctad04.cpp -o ex (cc exit=1) =====
ctad04.cpp: In function ‘int main()’:
ctad04.cpp:16:13: error: wrong number of template arguments (1, should be 2)
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |             ^
ctad04.cpp:4:36: note: provided for ‘template<class T, class U> struct Duo’
    4 | template <class T, class U> struct Duo {
      |                                    ^~~
ctad04.cpp:16:15: error: scalar object ‘d’ requires one element in initializer
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |               ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DPARTIAL ctad04.cpp -o ex (cc exit=1) =====
ctad04.cpp:16:5: error: too few template arguments for class template 'Duo'
   16 |     Duo<long> d{1, 2.0};               // 클래스 템플릿 — T 만 적는다
      |     ^
ctad04.cpp:4:36: note: template is declared here
    4 | template <class T, class U> struct Duo {
      | ~~~~~~~~~~~~~~~~~~~~~~~~~~~        ^
1 error generated.
```

**왜 그런가**

- ★★ `make_duo<long>(1, 2.0)` — 함수 템플릿은 **앞의 인자만 적고 나머지를 추론**한다(`long` · `double` → `8 8`).
- ★★★ **클래스 템플릿은 인자 목록이 있으면 CTAD 를 하지 않는다** — `Duo<long>` 은 「전부 적은 목록」으로 읽혀 **하나가 모자란다.**

### 5. ★★ **C++17 은 두 컴파일러 다 에러 · C++20 은 두 컴파일러 다 `Agg<int> · a + b = 3`**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic ctad05.cpp -o ex (cc exit=1) =====
ctad05.cpp: In function ‘int main()’:
ctad05.cpp:13:15: error: class template argument deduction failed:
   13 |     Agg x{1, 2};
      |               ^
ctad05.cpp:13:15: error: no matching function for call to ‘Agg(int, int)’
ctad05.cpp:7:27: note: candidate: ‘template<class T> Agg()-> Agg<T>’
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note:   template argument deduction/substitution failed:
ctad05.cpp:13:15: note:   candidate expects 0 arguments, 2 provided
   13 |     Agg x{1, 2};
      |               ^
ctad05.cpp:7:27: note: candidate: ‘template<class T> Agg(Agg<T>)-> Agg<T>’
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note:   template argument deduction/substitution failed:
ctad05.cpp:13:15: note:   mismatched types ‘Agg<T>’ and ‘int’
   13 |     Agg x{1, 2};
      |               ^
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic ctad05.cpp -o ex (cc exit=1) =====
ctad05.cpp:13:9: error: no viable constructor or deduction guide for deduction of template arguments of 'Agg'
   13 |     Agg x{1, 2};
      |         ^
ctad05.cpp:7:27: note: candidate function template not viable: requires 1 argument, but 2 were provided
    7 | template <class T> struct Agg {
      |                           ^~~
ctad05.cpp:7:27: note: candidate function template not viable: requires 0 arguments, but 2 were provided
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ctad05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Agg<int> · a + b = 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic ctad05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
decltype(x) = Agg<int> · a + b = 3
```

**왜 그런가**

- ★★ **C++17 의 규칙표는 생성자에서만 만들어진다** — g++ 후보가 `Agg()` 와 복사 후보 둘뿐이다. **C++20 이 집합체 추론 후보를 더했다.**

### 6. ★★★ **`exit=0` · `W Box<int>::get() const` 만 있고 `odd` 는 없다** · 켜면 **7행(몸통)을 가리키고 14행은 「required from here」·「requested here」로 붙는다**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c ctad06.cpp -o c6.o && nm -C c6.o (exit=0) =====
0000000000000000 W Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c ctad06.cpp -o c6.o && nm -C c6.o (exit=0) =====
0000000000000000 r .L.str
0000000000000000 r .L__const.main.b
0000000000000000 W Box<int>::get() const
0000000000000000 T main
                 U printf
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DCALL_ODD ctad06.cpp -o ex (cc exit=1) =====
ctad06.cpp: In instantiation of ‘void Box<T>::odd() const [with T = int]’:
ctad06.cpp:14:10:   required from here
ctad06.cpp:7:26: error: request for member ‘no_such_member’ in ‘((const Box<int>*)this)->Box<int>::v’, which is of non-class type ‘const int’
    7 |     void odd() const { v.no_such_member(); }
      |                        ~~^~~~~~~~~~~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DCALL_ODD ctad06.cpp -o ex (cc exit=1) =====
ctad06.cpp:7:25: error: member reference base type 'const int' is not a structure or union
    7 |     void odd() const { v.no_such_member(); }
      |                        ~^~~~~~~~~~~~~~~
ctad06.cpp:14:7: note: in instantiation of member function 'Box<int>::odd' requested here
   14 |     b.odd();
      |       ^
1 error generated.
```

**왜 그런가**

- ★★★ **클래스 템플릿의 멤버 함수는 쓰일 때만 인스턴스화된다** — 안 쓴 `odd()` 는 `int` 로 검사받지도, 기호로 남지도 않는다.
- ★★ 부르면 그 순간 인스턴스화되고, 에러는 **실패한 식이 있는 몸통**을 먼저 가리킨다. **원인이 된 호출은 사슬 끝**이다(35편 (5)).

### 7. ★★★ **복사 추론 후보** — 가상의 생성자 `Box(Box)` 에서 온 가이드다. `std::vector x{v2}` 에서 **이 후보가 이겨** `vector<int>` 가 됐다

- ★★ `Box` 에는 `Box(Box<T>)` 를 쓴 적이 없다 — 컴파일러가 **늘 하나 더** 세운다(cppreference 의 copy deduction candidate).
- ★★ `vector` 에서는 `{v2}` 한 원소를 **`vector<int>` 로 읽는 이 후보**와 **`initializer_list<vector<int>>` 로 읽는 생성자**가 맞붙고, 복사 후보가 이긴다.

### 8. ★★ **`"hi"` 칸 = 31편 (2)의 `T` 열 `"hi"` → `const char*`(감쇠)** · **`{1, 2.0}` 칸 = 31편 (3)의 `max_of(1, 2.0)`**(`deduced conflicting types` — 문구까지 같다)

- ★★ 생성자 `Box(T x)` 가 **값 매개변수**이고, `Box(T x, T)` 가 **두 인자에 같은 `T`** 를 요구한다 — 31편의 두 칸과 매개변수 꼴이 같다.

### 9. ★★ **클래스 템플릿은 「인자 목록이 없을 때만」 추론한다 — 함수 템플릿은 적힌 앞자리를 고정하고 나머지를 추론한다**

- ★ 그래서 일부만 정하고 싶으면 **팩토리 함수 템플릿**을 거친다(`make_duo<long>`).

### 10. ★★ **같은 표준 라이브러리 위에서 두 컴파일러의 CTAD 가 같은 타입을 냈다**까지다 — **clang 이 libstdc++ 13 을 썼으므로** 「두 라이브러리 구현이 같다」는 증명하지 못한다

- ★ `std::vector` 의 가이드·생성자는 **라이브러리의 코드**다 — libc++ 로 던지지 않았다.

### 11. 다른 주제와 잇기

- ★★ **Java 다이아몬드는 좌변(기대 타입)에서**, **CTAD 는 오른쪽의 생성자 인자에서** 가져온다 — Java 갈래 [17번](../../../java/syntax/17-generic-declarations/) (8).
- ★★ **Rust 는 정의 자리에서 경계만 보고 몸통을 검사한다** — 안 부른 함수도 E0599. C++ 은 **인스턴스화할 때** 검사한다 — Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (1)(7).
- ★ **`template struct Box<int>;` 는 멤버를 전부 만들어 `odd()` 에서 에러가 난다** — [35번](../35-instantiation-header-placement-and-reading-errors/) (2).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `ctad01.cpp` | 두 컴파일러 × c++14/17 × `OMIT` 유무 | ★★★ **c++14 + `OMIT` 만 에러** |
| `ctad02.cpp` + `ctad-grid.sh` | 선언 11 × 판 2 × 컴파일러 2 | ★★★ **판 20 / 22 · 컴파일러 0 / 22** |
| `ctad02.cpp -DCASE=5` | 두 컴파일러 | ★★ **후보 셋(g++) — 복사 추론 후보** |
| `ctad03.cpp` 가이드 | 두 컴파일러 × 유무 | ★★ **`char const*` → `std::string`** |
| `ctad04.cpp` 일부 지정 | 두 컴파일러 | ★★★ **함수 통과 · 클래스 에러** |
| `ctad05.cpp` 집합체 | 두 컴파일러 × c++17/20 | ★★ **17 에러 · 20 통과** |
| `ctad06.cpp` + `nm -C` | 두 컴파일러 × 호출 유무 | ★★★ **`odd` 기호 없음 · 부르면 에러** |

**구현 의존 항목** — 다음은 **이 환경(g++ 13 · clang 18 · libstdc++ 13)에서만** 그렇다.

- ★★ **타입 이름의 철자**(`char const*` · `3ul` · `std::__cxx11::basic_string`) · **`sizeof(std::string)` = 32** · **진단 문구**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **c++17 열의 11칸** · **복사 추론 후보** · **일부 지정이면 추론 안 함** · **집합체 CTAD 는 C++20** · **쓰인 멤버만 인스턴스화.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **템플릿인 추론 가이드 · `explicit` 가이드 · 별칭 템플릿 CTAD(C++20)** · ★ **libc++ 로 표준 컨테이너 행**.
- ★ **「부적용인 창」** — ASan · 경고 격자.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **2번** — 표준 컨테이너 행(라이브러리의 가이드가 바뀌면 칸이 바뀐다).
- ★ **1번·4번** — 진단 문구.
