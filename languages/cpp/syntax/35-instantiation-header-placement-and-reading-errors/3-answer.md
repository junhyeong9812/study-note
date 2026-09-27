# cpp/syntax/35 — 인스턴스화와 헤더 배치 · 오류 읽기 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU ld·nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 링커의 `.text+0x…` 오프셋 · `nm` 의 주소 · ★ 진단의 줄 수(이 판의 관찰)** 다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · `undefined reference` 의 이름 · `nm` 의 글자와 기호의 유무 · 첫 에러의 파일:줄 · O/X**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **컴파일은 두 번 다 통과, 링크에서 `undefined reference to 'Box<int>::get() const'`** · **`box_def.o` 는 기호 0개 · `use_box.o` 는 `U`** · `-DEXPLICIT` 면 **링크되고 `W`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && g++ box_def.o use_box.o -o ex (cc exit=1) =====
/usr/bin/ld: use_box.o: in function `main':
use_box.cpp:(.text+0x2a): undefined reference to `Box<int>::get() const'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && clang++ box_def.o use_box.o -o ex (cc exit=1) =====
/usr/bin/ld: use_box.o: in function `main':
use_box.cpp:(.text+0x16): undefined reference to `Box<int>::get() const'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && nm -C box_def.o use_box.o (exit=0) =====

box_def.o:

use_box.o:
                 U Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DEXPLICIT -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && g++ box_def.o use_box.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C box_def.o use_box.o (exit=0) =====

box_def.o:
0000000000000000 W Box<int>::get() const

use_box.o:
                 U Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DEXPLICIT -c box_def.cpp -o box_def.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && clang++ box_def.o use_box.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C box_def.o use_box.o (exit=0) =====

box_def.o:
0000000000000000 W Box<int>::get() const

use_box.o:
0000000000000000 r .L.str
0000000000000000 r .L__const.main.b
                 U Box<int>::get() const
0000000000000000 T main
                 U printf
```

**왜 그런가**

- ★★★ **인스턴스는 정의와 쓰임이 만나는 번역 단위에서만 생긴다** — `box_def.cpp` 에는 쓰임이, `use_box.cpp` 에는 정의가 없다.
- ★★ **명시적 인스턴스화는 「쓰임이 없어도 여기서 만들라」** 다 — 그래서 `box_def.o` 에 `W` 가 생겼다.

### 2. ★★★ **없이 — 통과, `W Box<int>::get() const` 하나** · **있이 — `odd()` 에서 에러**(두 컴파일러 다 9행을 원인으로)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c install.cpp -o inst.o && nm -C inst.o (exit=0) =====
0000000000000000 W Box<int>::get() const
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c install.cpp -o inst.o && nm -C inst.o (exit=0) =====
0000000000000000 W Box<int>::get() const
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DWHOLE -c install.cpp -o inst.o (cc exit=1) =====
install.cpp: In instantiation of ‘void Box<T>::odd() const [with T = int]’:
install.cpp:9:17:   required from here
install.cpp:5:26: error: request for member ‘no_such_member’ in ‘((const Box<int>*)this)->Box<int>::v’, which is of non-class type ‘const int’
    5 |     void odd() const { v.no_such_member(); }
      |                        ~~^~~~~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DWHOLE -c install.cpp -o inst.o (cc exit=1) =====
install.cpp:5:25: error: member reference base type 'const int' is not a structure or union
    5 |     void odd() const { v.no_such_member(); }
      |                        ~^~~~~~~~~~~~~~~
install.cpp:9:17: note: in instantiation of member function 'Box<int>::odd' requested here
    9 | template struct Box<int>;
      |                 ^
1 error generated.
```

**왜 그런가**

- ★★★ **클래스의 명시적 인스턴스화는 멤버를 전부 만든다** — 암묵 인스턴스화(32편 (6))와 반대다. 안 되는 멤버가 있으면 **멤버 단위**로 한다.

### 3. ★★★ **링크되고 `2 1`** · **두 `.o` 다 `W HBox<int>::get() const`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -c hbox_b.cpp -o hbox_b.o && g++ hbox_a.o hbox_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
0000000000000000 W HBox<int>::get() const
                 U __stack_chk_fail

hbox_b.o:
                 U from_a()
0000000000000000 W HBox<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c hbox_b.cpp -o hbox_b.o && clang++ hbox_a.o hbox_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
0000000000000000 W HBox<int>::get() const

hbox_b.o:
0000000000000000 r .L.str
                 U from_a()
0000000000000000 W HBox<int>::get() const
0000000000000000 T main
                 U printf
```

**왜 그런가**

- ★★★ **두 번역 단위가 정의와 쓰임을 다 가져 각자 인스턴스를 만들었고, `W` 라 링커가 하나만 남겼다** — 7번.

### 4. ★★ **둘만이면 `undefined reference` · `hbox_inst.o` 를 더하면 링크(`2 1`) — a·b 는 `U`, inst 만 `W`** · ★★★ **`-O0` 은 `U` 1개, `-O2` 는 `U` 0개**(두 컴파일러 같다 · `W` 는 넷 다 0개)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && g++ hbox_a.o hbox_b.o -o ex (cc exit=1) =====
/usr/bin/ld: hbox_a.o: in function `from_a()':
hbox_a.cpp:(.text+0x2a): undefined reference to `HBox<int>::get() const'
/usr/bin/ld: hbox_b.o: in function `main':
hbox_b.cpp:(.text+0x32): undefined reference to `HBox<int>::get() const'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && clang++ hbox_a.o hbox_b.o -o ex (cc exit=1) =====
/usr/bin/ld: hbox_a.o: in function `from_a()':
hbox_a.cpp:(.text+0x14): undefined reference to `HBox<int>::get() const'
/usr/bin/ld: hbox_b.o: in function `main':
hbox_b.cpp:(.text+0x14): undefined reference to `HBox<int>::get() const'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_inst.cpp -o hbox_inst.o && g++ hbox_a.o hbox_b.o hbox_inst.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o hbox_inst.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
                 U HBox<int>::get() const
                 U __stack_chk_fail

hbox_b.o:
                 U from_a()
                 U HBox<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf

hbox_inst.o:
0000000000000000 W HBox<int>::get() const
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_inst.cpp -o hbox_inst.o && clang++ hbox_a.o hbox_b.o hbox_inst.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o hbox_inst.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
                 U HBox<int>::get() const

hbox_b.o:
0000000000000000 r .L.str
                 U from_a()
                 U HBox<int>::get() const
0000000000000000 T main
                 U printf

hbox_inst.o:
0000000000000000 W HBox<int>::get() const
```

```text
===== bash ext-opt.sh (exit=0) =====
g++      -O0  U HBox<int>::get 기호 1개 · W 기호 0개
g++      -O2  U HBox<int>::get 기호 0개 · W 기호 0개
clang++  -O0  U HBox<int>::get 기호 1개 · W 기호 0개
clang++  -O2  U HBox<int>::get 기호 0개 · W 기호 0개
```

**왜 그런가**

- ★★ **`extern template` 은 「여기서는 인스턴스를 만들지 말고 다른 곳의 것을 쓰라」** — 다른 곳이 없으면 링크 에러다.
- ★★★ **인라인은 막지 않는다** — `-O2` 에서 `get()` 이 펼쳐져 **부를 일 자체가 없어졌다.**

### 5. ★★★ **첫 에러는 두 컴파일러 다 6행(`a < b`)** · 13행은 **g++ 에서 에러 위 사슬의 끝 `required from here`**, **clang 에서 에러 아래 마지막 `validate<Point>' requested here`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic deep01.cpp -o ex (cc exit=1) =====
deep01.cpp: In instantiation of ‘bool less_than(const T&, const T&) [with T = Point]’:
deep01.cpp:7:75:   required from ‘bool ordered(const T&, const T&) [with T = Point]’
deep01.cpp:8:71:   required from ‘bool check_pair(const T (&)[2]) [with T = Point]’
deep01.cpp:9:72:   required from ‘bool validate(const T (&)[2]) [with T = Point]’
deep01.cpp:13:20:   required from here
deep01.cpp:6:70: error: no match for ‘operator<’ (operand types are ‘const Point’ and ‘const Point’)
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~~^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic deep01.cpp -o ex (cc exit=1) =====
deep01.cpp:6:70: error: invalid operands to binary expression ('const Point' and 'const Point')
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~ ^ ~
deep01.cpp:7:66: note: in instantiation of function template specialization 'less_than<Point>' requested here
    7 | template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
      |                                                                  ^
deep01.cpp:8:64: note: in instantiation of function template specialization 'ordered<Point>' requested here
    8 | template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
      |                                                                ^
deep01.cpp:9:62: note: in instantiation of function template specialization 'check_pair<Point>' requested here
    9 | template <class T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                                              ^
deep01.cpp:13:12: note: in instantiation of function template specialization 'validate<Point>' requested here
   13 |     return validate(ps);
      |            ^
1 error generated.
```

**왜 그런가**

- ★★★ **에러는 「실패한 식」이 있는 자리를 가리킨다** — 제약 없는 템플릿은 **맨 안쪽까지 인스턴스화한 뒤에야** 실패를 안다. 요구한 쪽은 사슬로 거슬러 올라가 적는다.

### 6. ★★★ **`O` 는 `deep02` 네 행 · `deep03 -DRANGES` 두 행 · g++ 의 `-fconcepts-diagnostics-depth=2` 한 행 — 7 / 16** · **g++ 8 → 17 → 29 로 늘었다** · **다르다 — g++ 4번째 줄, clang 은 `-`(안 나온다)**

**출력**

```text
===== bash err-count.sh (exit=0) =====
경우	컴파일러	cc exit	총 줄	: error: 줄	첫 error 가 가리키는 곳	그곳이 호출 줄인가	호출 줄이 처음 나오는 줄
deep01.cpp	g++	1	8	1	deep01.cpp:6	X	5
deep01.cpp	clang++	1	16	1	deep01.cpp:6	X	13
deep02.cpp	g++	1	17	1	deep02.cpp:23	O	2
deep02.cpp	clang++	1	13	1	deep02.cpp:23	O	1
deep02.cpp -DSTD_CONCEPT	g++	1	29	1	deep02.cpp:23	O	2
deep02.cpp -DSTD_CONCEPT	clang++	1	19	1	deep02.cpp:23	O	1
deep03.cpp	g++	1	78	3	predefined_ops.h:45	X	9
deep03.cpp	clang++	1	220	9	predefined_ops.h:45	X	28
deep03.cpp -DRANGES	g++	1	34	1	deep03.cpp:12	O	2
deep03.cpp -DRANGES	clang++	1	36	1	deep03.cpp:12	O	1
deep01.cpp -ftemplate-backtrace-limit=1	g++	1	7	1	deep01.cpp:6	X	4
deep01.cpp -ftemplate-backtrace-limit=1	clang++	1	10	1	deep01.cpp:6	X	-
deep03.cpp -ftemplate-backtrace-limit=1	g++	1	67	3	predefined_ops.h:45	X	7
deep03.cpp -ftemplate-backtrace-limit=1	clang++	1	133	9	predefined_ops.h:45	X	-
deep02.cpp -DSTD_CONCEPT -fconcepts-diagnostics-depth=2	g++	1	32	5	deep02.cpp:23	O	2
deep02.cpp -DSTD_CONCEPT -fconcepts-diagnostics-depth=2	clang++	1	1	1	(clang++ 자체)	X	-
첫 error 가 호출 줄을 가리킨 칸 7 / 16 · 호출 줄이 아예 안 나온 칸 3 / 16
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic deep02.cpp -o ex (cc exit=1) =====
deep02.cpp: In function ‘int main()’:
deep02.cpp:23:20: error: no matching function for call to ‘validate(Point [2])’
   23 |     return validate(ps);
      |            ~~~~~~~~^~~~
deep02.cpp:18:24: note: candidate: ‘template<class T>  requires  Less<T> bool validate(const T (&)[2])’
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                        ^~~~~~~~
deep02.cpp:18:24: note:   template argument deduction/substitution failed:
deep02.cpp:18:24: note: constraints not satisfied
deep02.cpp: In substitution of ‘template<class T>  requires  Less<T> bool validate(const T (&)[2]) [with T = Point]’:
deep02.cpp:23:20:   required from here
deep02.cpp:10:9:   required for the satisfaction of ‘Less<T>’ [with T = Point]
deep02.cpp:10:16:   in requirements with ‘const T& a’, ‘const T& b’ [with T = Point]
deep02.cpp:10:53: note: the required expression ‘(a < b)’ is invalid
   10 | concept Less = requires(const T& a, const T& b) { a < b; };
      |                                                   ~~^~~
cc1plus: note: set ‘-fconcepts-diagnostics-depth=’ to at least 2 for more detail
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic deep02.cpp -o ex (cc exit=1) =====
deep02.cpp:23:12: error: no matching function for call to 'validate'
   23 |     return validate(ps);
      |            ^~~~~~~~
deep02.cpp:18:24: note: candidate template ignored: constraints not satisfied [with T = Point]
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                        ^
deep02.cpp:18:11: note: because 'Point' does not satisfy 'Less'
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |           ^
deep02.cpp:10:53: note: because 'a < b' would be invalid: invalid operands to binary expression ('const Point' and 'const Point')
   10 | concept Less = requires(const T& a, const T& b) { a < b; };
      |                                                     ^
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -ftemplate-backtrace-limit=1 deep01.cpp -o ex (cc exit=1) =====
deep01.cpp: In instantiation of ‘bool less_than(const T&, const T&) [with T = Point]’:
deep01.cpp:7:75:   [ skipping 2 instantiation contexts, use -ftemplate-backtrace-limit=0 to disable ]
deep01.cpp:9:72:   required from ‘bool validate(const T (&)[2]) [with T = Point]’
deep01.cpp:13:20:   required from here
deep01.cpp:6:70: error: no match for ‘operator<’ (operand types are ‘const Point’ and ‘const Point’)
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~~^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ftemplate-backtrace-limit=1 deep01.cpp -o ex (cc exit=1) =====
deep01.cpp:6:70: error: invalid operands to binary expression ('const Point' and 'const Point')
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~ ^ ~
deep01.cpp:7:66: note: in instantiation of function template specialization 'less_than<Point>' requested here
    7 | template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
      |                                                                  ^
deep01.cpp:8:64: note: (skipping 3 contexts in backtrace; use -ftemplate-backtrace-limit=0 to see all)
    8 | template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
      |                                                                ^
1 error generated.
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fconcepts-diagnostics-depth=2 deep02.cpp -o ex (cc exit=1) =====
clang++: error: unknown argument: '-fconcepts-diagnostics-depth=2'
```

**왜 그런가**

- ★★★ **컨셉이 걸린 템플릿은 호출 자리에서 후보에서 빠진다** — 안쪽을 인스턴스화하지 않으니 첫 에러가 **호출 줄**이다. 대신 **컨셉이 왜 불만족인지**를 적느라 줄이 늘 수 있다.
- ★★ **백트레이스 제한은 컴파일러마다 자르는 법이 다르다** — g++ 는 처음·끝을 남기고, clang 은 앞쪽만 남긴다.

### 7. ★★★ **템플릿 인스턴스는 `W`(약한 기호) — 여럿이면 하나만 남긴다** · 25편의 `int Cfg::count = 0;` 은 **`B`(자리를 가진 정의)** 라 둘이면 `multiple definition` 이다

- ★★ 언어 쪽 이유 — **클래스 안에서 정의한 멤버 함수는 암묵 `inline`** 이고 템플릿 인스턴스는 **여러 번역 단위에 같은 정의로** 있어도 된다. `W` 는 그 약속을 이 ABI 가 링커에게 전하는 방식이다.

### 8. ★★ **`std::totally_ordered` 는 `<` 만이 아니라 `==` 도 요구하고, 컴파일러는 처음 막힌 요구를 적었다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DSTD_CONCEPT deep02.cpp -o ex (cc exit=1) =====
deep02.cpp: In function ‘int main()’:
deep02.cpp:23:20: error: no matching function for call to ‘validate(Point [2])’
   23 |     return validate(ps);
      |            ~~~~~~~~^~~~
deep02.cpp:16:40: note: candidate: ‘template<class T>  requires  totally_ordered<T> bool validate(const T (&)[2])’
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                        ^~~~~~~~
deep02.cpp:16:40: note:   template argument deduction/substitution failed:
deep02.cpp:16:40: note: constraints not satisfied
In file included from deep02.cpp:3:
/usr/include/c++/13/concepts: In substitution of ‘template<class T>  requires  totally_ordered<T> bool validate(const T (&)[2]) [with T = Point]’:
deep02.cpp:23:20:   required from here
/usr/include/c++/13/concepts:294:15:   required for the satisfaction of ‘__weakly_eq_cmp_with<_Tp, _Tp>’ [with _Tp = Point]
/usr/include/c++/13/concepts:304:13:   required for the satisfaction of ‘equality_comparable<_Tp>’ [with _Tp = Point]
/usr/include/c++/13/concepts:333:13:   required for the satisfaction of ‘totally_ordered<T>’ [with T = Point]
/usr/include/c++/13/concepts:295:4:   in requirements with ‘std::remove_reference_t<_Tp>& __t’, ‘std::remove_reference_t<_Up>& __u’ [with _Tp = Point; _Up = Point]
/usr/include/c++/13/concepts:296:17: note: the required expression ‘(__t == __u)’ is invalid
  296 |           { __t == __u } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:297:17: note: the required expression ‘(__t != __u)’ is invalid
  297 |           { __t != __u } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:298:17: note: the required expression ‘(__u == __t)’ is invalid
  298 |           { __u == __t } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:299:17: note: the required expression ‘(__u != __t)’ is invalid
  299 |           { __u != __t } -> __boolean_testable;
      |             ~~~~^~~~~~
cc1plus: note: set ‘-fconcepts-diagnostics-depth=’ to at least 2 for more detail
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DSTD_CONCEPT deep02.cpp -o ex (cc exit=1) =====
deep02.cpp:23:12: error: no matching function for call to 'validate'
   23 |     return validate(ps);
      |            ^~~~~~~~
deep02.cpp:16:40: note: candidate template ignored: constraints not satisfied [with T = Point]
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                        ^
deep02.cpp:16:11: note: because 'Point' does not satisfy 'totally_ordered'
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |           ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:334:9: note: because 'Point' does not satisfy 'equality_comparable'
  334 |       = equality_comparable<_Tp>
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:304:35: note: because '__detail::__weakly_eq_cmp_with<Point, Point>' evaluated to false
  304 |     concept equality_comparable = __detail::__weakly_eq_cmp_with<_Tp, _Tp>;
      |                                   ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:296:10: note: because '__t == __u' would be invalid: invalid operands to binary expression ('const remove_reference_t<Point>' (aka 'const Point') and 'const remove_reference_t<Point>' (aka 'const Point'))
  296 |           { __t == __u } -> __boolean_testable;
      |                 ^
1 error generated.
```

- ★ 그래서 `<` 만 정의해 줘도 이 에러는 **안 사라진다** — 컨셉이 **원인을 다르게 말하는** 자리다.

### 9. ★★★ **「첫 error 가 가리키는 곳」** — 줄 수는 **이 판의 관찰**이라 컴파일러 판이 바뀌면 바뀌고, 「어느 파일:줄을 가리키나 · 그것이 호출 줄인가」는 **컨셉 제약 유무라는 코드의 성질**이 정한다

- ★ 줄 수로 「컨셉이면 짧다」를 세우면 **`deep01` → `deep02` 에서 거꾸로** 나온다.

### 10. ★★ **말할 수 없다** — 보인 것은 **`U` 기호가 사라졌다**는 것뿐이다. 크기는 `size`·`nm -S` 로 **재야** 하고, 이 문서는 재지 않았다

- ★ `-O2` 의 결과는 **인라인** 때문이지 `extern template` 때문이 아니다 — `-O0` 에서는 `U` 가 남았다.

### 11. 다른 주제와 잇기

- ★★ **C 함수는 정의 한 벌을 `.c` 에서 만들어 두면 끝**이다 — 쓰는 쪽은 선언만 있으면 된다. **템플릿은 쓰는 쪽이 정의를 봐야 실물을 만든다** — 그래서 「선언은 헤더, 정의는 `.c`」가 템플릿에서 깨진다.
- ★★ **Rust 는 경계가 없으면 정의 자리에서, 빠진 경계는 호출 자리에서 막는다** — Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (1)(3). C++ 은 컨셉을 걸어야 호출 자리로 온다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `box.h`·`box_def.cpp`·`use_box.cpp` | 두 컴파일러 × `EXPLICIT` 유무 + `nm -C` | ★★★ **`undefined reference` · 기호 0개 / 링크 · `W`** |
| `use_box_d.cpp` + `EXPLICIT` | g++ | ★★ **`undefined reference to Box<double>`** |
| `install.cpp` | 두 컴파일러 × `WHOLE` 유무 | ★★★ **멤버 하나 통과 · 전체는 에러** |
| `hbox*.cpp` | 두 컴파일러 × `USE_EXTERN` 유무 × inst 유무 + `nm -C` | ★★★ **`W` 두 벌 / `U` + 한 곳의 `W`** |
| `ext-opt.sh` | 두 컴파일러 × `-O0`/`-O2` | ★★ **`U` 1 → 0** |
| `deep01~03.cpp` + `err-count.sh` | 경우 8 × 컴파일러 2 | ★★★ **호출 줄 7 / 16 · 호출 줄 없음 3 / 16** |

**구현 의존 항목** — 다음은 **이 환경(g++ 13 · clang 18 · GNU ld 2.42)에서만** 그렇다.

- ★★★ **진단 줄 수 전부** · **`required from` 대 `requested here`** · **백트레이스 제한의 자르는 법** · **`-fconcepts-diagnostics-depth`(g++ 전용)** · **`W` 라는 글자** · **`-O2` 의 인라인**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **정의가 안 보이면 인스턴스화 불가** · **같은 인스턴스는 여러 번역 단위에 있어도 된다** · **명시적 인스턴스화는 멤버 전부** · **`extern template` 은 다른 곳의 정의를 쓴다** · **컨셉 불만족은 후보 탈락.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **서로 다른 정의의 ODR 위반** · **모듈** · **코드 크기·컴파일 시간**(재지 않았다 — 주장하지 않는다).
- ★ **「부적용인 창」** — ASan.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **6번 격자 전체** — 줄 수는 판마다 바뀐다. **O/X 칸이 그대로인지**가 볼 것이다.
