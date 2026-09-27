# cpp/syntax/16 — 복사 생성자와 복사 대입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **ASan 의 PID·주소·스택 프레임 줄**과 **진단 문구**는 흔들리는 칸이다.\
> 근거로 쓰는 것은 다음이다 — **어느 특수 멤버가 몇 번 불렸나** · **만들어진 객체 수** · **`malloc`/`free` 횟수** ·\
> **`cc exit`/`run exit`** · **경고 개수** · **진단의 `(행,열)`**.
> ★★★ **이 문서는 시간을 재지 않았다.** 「복사가 느리다」·「생략이 빠르다」는 문장이 **한 줄도 없다** —\
> 이 문서가 센 것은 **호출 횟수와 할당 횟수까지**다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ `(1)`\~`(3)` 은 전부 **복사 생성자**, `(4)` 만 **복사 대입** — 객체는 **8개**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
    기본 생성자  #2
(1) Loud c = b;        — 선언과 함께 = 을 썼다
    복사 생성자  #3 <- #2
(2) Loud c(b);         — 괄호로 썼다
    복사 생성자  #4 <- #2
(3) Loud c{b};         — 중괄호로 썼다
    복사 생성자  #5 <- #2
(4) a = b;             — 이미 있는 것에 = 을 썼다
    복사 대입    #1 <- #2
(5) Loud c = std::move(b);
    이동 생성자  #6 <- #2
(6) a = std::move(b);
    이동 대입    #1 <- #2
(7) by_value(b);       — 값으로 받는 함수에 넘긴다
    복사 생성자  #7 <- #2
(8) by_const_ref(b);   — const 참조로 받는 함수에
(9) by_value(std::move(b));
    이동 생성자  #8 <- #2
(10) 지금까지 만들어진 객체 수 8개
```

**왜 그런가**

- ★★★ **경계는 「객체가 그 자리에서 새로 생기는가」 하나다.**
  - `Loud c = b;` · `Loud c(b);` · `Loud c{b};` — **`c` 가 그 줄에서 태어난다.** 초기화이므로 **복사 생성자**다.
  - `a = b;` — `a` 는 **이미 두 줄 위에서 태어났다.** 내용을 갈아 끼우는 것이므로 **복사 대입**이다.
- ★★ 출력에서 그것이 **번호로 보인다.** `(1)`\~`(3)` 은 `#3`·`#4`·`#5` 라는 **새 번호**가 찍히고,\
  `(4)` 는 `복사 대입    #1 <- #2` 로 **`#1` 이 그대로** 남아 있다.
- ★★★ **아무 로그도 안 찍히는 쪽은 `(8)` 의 `const Loud&`** 다. **아무것도 안 만들어진다.**\
  ★ 반대로 `(7)` 의 `by_value(b)` 는 **복사 생성자가 돈다** — 소스에 복사라는 글자가 없는데도.
- ★ `(5)`·`(6)`·`(9)` 는 **`std::move` 를 씌운 같은 세 자리**이고 **이동 쪽이 뽑혔다.** 정본은 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)다.
- ★ **만들어진 객체 수는 8개**다 — `a`·`b` 둘 + `(1)`\~`(3)` 셋 + `(5)` 하나 + `(7)` 하나 + `(9)` 하나.\
  `(4)`·`(6)`·`(8)` 은 **새 객체를 안 만든다.**
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic copy01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    기본 생성자  #1
    기본 생성자  #2
(1) Loud c = b;        — 선언과 함께 = 을 썼다
    복사 생성자  #3 <- #2
(2) Loud c(b);         — 괄호로 썼다
    복사 생성자  #4 <- #2
(3) Loud c{b};         — 중괄호로 썼다
    복사 생성자  #5 <- #2
(4) a = b;             — 이미 있는 것에 = 을 썼다
    복사 대입    #1 <- #2
(5) Loud c = std::move(b);
    이동 생성자  #6 <- #2
(6) a = std::move(b);
    이동 대입    #1 <- #2
(7) by_value(b);       — 값으로 받는 함수에 넘긴다
    복사 생성자  #7 <- #2
(8) by_const_ref(b);   — const 참조로 받는 함수에
(9) by_value(std::move(b));
    이동 생성자  #8 <- #2
(10) 지금까지 만들어진 객체 수 8개
```

### 2. ★★ **5개 대 6개** — 늘어나는 것은 `named()` 한 자리뿐이고, 늘어난 것은 **이동 생성자**다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #3
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #4
    복사 생성자  #5 <- #4
(5) 만들어진 객체 수 5개
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors copy02.cpp -o ex2 && ./ex2 (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
    이동 생성자  #3 <- #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #4
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #5
    복사 생성자  #6 <- #5
(5) 만들어진 객체 수 6개
```

**왜 그런가**

- ★★★ **C++17 이 두 자리의 생략을 의무로 못 박았다.**
  - `L a = prvalue();` — 돌려주는 것이 **이름 없는 임시**(prvalue)다.
  - `by_value(L());` — 값 인자에 넘기는 것이 **이름 없는 임시**다.
  - ★ 이 둘은 「복사를 생략한다」가 아니라 「**애초에 임시가 안 생긴다**」로 읽어야 한다.\
    그래서 `-fno-elide-constructors` 를 켜도 **끌 것이 없다.**
- ★★ **`L b = named();` 만 늘어난다.** 이름 있는 지역을 돌려주는 생략(NRVO)은 **여전히 재량**이다.
- ★★★ **늘어난 것은 복사 생성자가 아니라 이동 생성자다**(`이동 생성자  #3 <- #2`).\
  `return t;` 의 `t` 는 **먼저 rvalue 로 취급**되기 때문이다 — 정본은 [9번](../09-rvalue-references-move-and-forward/).
- ★ `by_value(c)` 의 복사는 **생략과 무관한 진짜 복사**다. 양쪽에서 똑같이 한 줄이다.
- ★ **clang 도 같은 5 대 6 이었다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fno-elide-constructors copy02.cpp -o ex2 && ./ex2 (cc exit=0 · run exit=0) =====
(1) prvalue 를 받는다      L a = prvalue();
    기본 생성자  #1
(2) 이름 있는 지역을 받는다 L b = named();
    기본 생성자  #2
    이동 생성자  #3 <- #2
(3) 임시를 값 인자로        by_value(L());
    기본 생성자  #4
(4) 변수를 값 인자로        by_value(c);
    기본 생성자  #5
    복사 생성자  #6 <- #5
(5) 만들어진 객체 수 6개
```

- ★★ **이것이 다섯 층 중 「미명시」의 실측이다** — 표준은 NRVO 를 **허용할 뿐 강제하지 않는다.**

### 3. ★★ `(1)` 은 **0 과 1** · `(3)` 은 **0** · `malloc` **4회** `free` **1회**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 복사 생성 뒤
    두 객체가 같은 주소를 드나: 0
    두 객체의 내용이 같나      : 1
(2) b 만 고친 뒤
    a = "가나다"  b = "라마바"
(3) 복사 대입 뒤  c = "가나다"  (a 와 같은 주소인가: 0)
(4) 지금까지 malloc 4회 · free 1회 (블록을 나가면 free 가 3회 더)
```

**왜 그런가**

- ★★★ **깊은 복사의 증거는 두 줄을 같이 봐야 선다.**
  - `두 객체가 같은 주소를 드나: 0` — **주소가 다르다**(얕은 복사가 아니다).
  - `두 객체의 내용이 같나 : 1` — **내용은 같다**(복사가 됐다).
  - ★ 둘 중 하나만 보면 판정이 안 된다.
- ★★ `(2)` 가 그 독립을 **행동으로** 다시 보인다 — `b` 만 고쳤는데 `a` 가 그대로다.
- ★★ `(3)` 의 `c.p == a.p` 가 **0** 이다. 복사 **대입**도 새로 잡았다는 뜻이다.
- ★ **`malloc` 4회** — `a` 1 + `c` 1 + 복사 생성 1 + 복사 대입 1.\
  **`free` 1회** — 복사 대입이 **옛것을 놓은** 한 번뿐이다. 나머지 셋은 **블록을 나가면서** 돈다.
- ★★ **대입의 순서가 규칙이다** — 소스에서 `malloc` 이 `free` 보다 **위에** 있다.\
  뒤집으면 4번이 된다.

### 4. ★★★ **0** 이다 — 그런데 **안 터지고 경고도 0건**이다

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 서로 다른 둘을 대입한다  a = b;
    a 가 "라마바" 인가: 1
(2) 자기 자신을 대입한다  a = a;
    a 가 아직 "라마바" 인가: 0
```

**왜 그런가**

- ★★★ **`cc exit=0` · `run exit=0` 이고 경고는 0건**이다. **값만 조용히 상한다.**
- ★★★ **순서가 사고의 전부다.**
  - ① `free(p)` — 내 버퍼를 놓는다.
  - ② `strlen(o.p)` — **`o` 는 나 자신이다.** 방금 놓은 것을 읽는다.
  - ③ 그래서 `n` 은 **쓰레기에서 나온 길이**이고, ④ `memcpy` 도 **놓은 것에서** 복사한다.
- ★★ **소스가 값을 안 찍는다.** 상한 내용은 **판마다 달라 재현이 안 되기 때문**이다.\
  대신 「**아직 원래 값인가**」만 묻고, 그 답 `0` 은 **15판을 돌려 전부 같았다.**
- ★★★ **ASan 에게 물으면 이름이 붙는다.**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. copy04.cpp -o exa && ./exa | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) 서로 다른 둘을 대입한다  a = b;
    a 가 "라마바" 인가: 1
(2) 자기 자신을 대입한다  a = a;
=================================================================
==2613344==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000050 at pc 0x77c20907d96f bp 0x7ffc7a5d5080 sp 0x7ffc7a5d4828
READ of size 2 at 0x502000000050 thread T0
    #0 0x77c20907d96e in strlen ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391
    #1 0x618e397d184b in Naive::operator=(Naive const&) copy04.cpp:18
    #2 0x618e397d1543 in main copy04.cpp:31

0x502000000050 is located 0 bytes inside of 10-byte region [0x502000000050,0x50200000005a)
freed by thread T0 here:
    #0 0x77c2090fc4d8 in free ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:52
    #1 0x618e397d181b in Naive::operator=(Naive const&) copy04.cpp:17
    #2 0x618e397d1543 in main copy04.cpp:31

previously allocated by thread T0 here:
    #0 0x77c2090fd9c7 in malloc ../../../../src/libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x618e397d188c in Naive::operator=(Naive const&) copy04.cpp:19
    #2 0x618e397d1468 in main copy04.cpp:28

SUMMARY: AddressSanitizer: heap-use-after-free ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391 in strlen
```

- ★★★ **세 지점이 한 함수 안에 있다** — `READ` 가 **18번 줄**, `freed by` 가 **17번 줄**, `previously allocated` 가 **19번 줄**.\
  ★ **놓은 줄과 읽은 줄이 한 줄 간격**이다. 눈으로 못 보는 것이 아니라 **눈으로 보고도 안 보이는** 자리다.
- ★★ **`run exit=1`** 이다 — ASan 이 `abort()` 했다.
- ★★★ **마커를 `stderr` 로 찍은 이유가 이 블록에 있다.** `(1)`·`(2)` 두 줄이 리포트 **앞에 남아 있다**.\
  표준 출력으로 찍었으면 `abort()` 가 버퍼째 지워 **한 줄도 안 남는다**(규칙 19-A).

### 5. ★★★ 온전하다 · `s1` 은 **원본 그대로** · `(3)` 은 **1**(그래서 사고다)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) copy-and-swap 에 자기 대입
    a = "가나다"   (자기 대입 검사 한 줄도 없다)
(2) 대입 도중 할당이 실패하면 — copy-and-swap
    [catch] bad_alloc
    s1 = "원본은 살아남나"  ★ 원본 그대로다
(3) 같은 일을 naive 구현에 — 포인터가 어떻게 되나
    [catch] bad_alloc
    n1.p 가 대입 전과 같은 주소인가: 1  ★ 그 주소는 이미 free 된 것이다
```

**왜 그런가**

- ★★★ **자기 대입 검사가 한 줄도 없는데 안전하다.**\
  `Safe& operator=(Safe o)` 는 **값으로 받는다** — 들어온 순간 `o` 는 **`a` 의 복사본**이고, 맞바꿔도 `a` 는 제 값을 갖는다.
- ★★★ **`(2)` 에서 `s1` 이 `"원본은 살아남나"` 로 남았다.** 이것이 **강한 보장**이다.\
  던질 수 있는 자리는 **값으로 받는 순간**뿐인데, 그때는 **`*this` 를 아직 안 건드렸다.**
- ★★★ **`(3)` 의 `1` 이 사고다.** naive 구현은 **먼저 놓고** 나서 잡으므로,\
  잡다가 던지면 `n1.p` 가 **이미 해제된 주소를 그대로 들고** 남는다.\
  ★ 그 뒤 소멸자가 돌면 **이중 해제**다. 그래서 예제가 `n1.p = nullptr;` 로 치웠다.
- ★★ **공짜가 아니다** — `(1)` 에서 `Safe` 가 하나 더 만들어졌다. **자기 대입에서도 복사가 한 번 난다.**\
  ★ 「같은 것을 대입하는 일이 잦다」면 3번의 `if (this == &o)` 한 줄이 싸다. **둘 다 맞고 상황이 고른다.**
- ★ **강한 보장의 전모는 목록의 52번 주제**다. 여기서 본 것은 **한 사례**다.

### 6. ★ **컴파일이 안 된다** — 무한 재귀를 볼 기회가 없다

**출력**

```cpp
/* copy06.cpp */
// 복사 생성자를 const T& 가 아니라 T 로 받으면 — 컴파일러가 먼저 막는다
struct C {
    int x;
    C() : x(0) {}
    C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
};
struct A {
    int x;
    A() : x(0) {}
    A(const A&) = default;
    A& operator=(A o) { x = o.x; return *this; }   // 값으로 받는 복사 대입은 합법이다
};
int main() { A a, b; a = b; (void)a; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 copy06.cpp -o ex (cc exit=1) =====
copy06.cpp:5:5: error: invalid constructor; you probably meant ‘C (const C&)’
    5 |     C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
      |     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 copy06.cpp -o ex (cc exit=1) =====
copy06.cpp:5:9: error: copy constructor must pass its first argument by reference
    5 |     C(C o) { x = o.x; }                 // 값으로 받는 복사 생성자
      |         ^
      |         const &
1 error generated.
```

**왜 그런가**

- ★★★ **표준이 `T(T)` 라는 선언 자체를 금지한다.** 실행까지 못 간다.\
  ★ 「값으로 받으려면 먼저 복사해야 하고, 그 복사가 또 자기를 부른다」는 **추론이 맞지만**,\
  **그 추론을 실행으로 확인할 수는 없다.** 두 컴파일러 다 `cc exit=1` 이다.
- ★★ **두 문구가 다르다.** g++ 는 `invalid constructor; you probably meant ‘C (const C&)’`,\
  clang 은 `copy constructor must pass its first argument by reference` 에 **고칠 문자열(`const &`)까지** 붙인다.\
  ★ **진단 문구는 구현 정의**다 — 근거로 쓰는 것은 `cc exit=1` 과 진단의 `(행,열)` 둘이다.
- ★★★ **복사 대입은 막히지 않는다**(`A& operator=(A o)` 가 같은 파일에 있는데 에러가 그 줄을 안 가리킨다).\
  **대입은 이미 있는 객체에 하는 것**이라 「자기를 만들려고 자기를 부르는」 고리가 안 생긴다.\
  ★ 그것이 5번의 copy-and-swap 이 성립하는 이유다.

### 7. ★★ 탐침 여섯 중 **하나**만 답했다 — 2번이다

**출력**

```cpp
/* copy07.cpp */
// 복사에서 틀리는 자리 여섯을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <cstdio>
#include <cstdlib>
#include <cstring>

struct P1 {                                   // 1. 소멸자만 쓰고 복사를 안 막았다 (얕은 복사)
    char* p;
    P1() : p(static_cast<char*>(std::malloc(8))) {}
    ~P1() { std::free(p); }
};
struct P2 {                                   // 2. 복사 생성자만 쓰고 복사 대입은 안 썼다
    char* p;
    P2() : p(static_cast<char*>(std::malloc(8))) {}
    P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
};
struct P3 {                                   // 3. 복사 생성자가 멤버 하나를 빠뜨렸다
    int a, b;
    P3() : a(0), b(0) {}
    P3(const P3& o) : a(o.a) {}
};
struct P4 {                                   // 4. 복사 대입이 *this 를 안 돌려준다
    int a;
    P4() : a(0) {}
    void operator=(const P4& o) { a = o.a; }
};
struct P5 {                                   // 5. 자기 대입을 안 막은 대입 연산자
    char* p; std::size_t n;
    P5() : p(static_cast<char*>(std::malloc(8))), n(8) {}
    ~P5() { std::free(p); }
    P5(const P5& o) : p(static_cast<char*>(std::malloc(o.n))), n(o.n) { std::memcpy(p, o.p, n); }
    P5& operator=(const P5& o) {
        std::free(p);
        n = o.n;
        p = static_cast<char*>(std::malloc(n));
        std::memcpy(p, o.p, n);
        return *this;
    }
};
struct P6 {                                   // 6. 복사 대입이 멤버를 하나도 안 옮긴다
    int a;
    P6() : a(0) {}
    P6& operator=(const P6&) { return *this; }
};

int main() {
    P1 a; P1 b(a); (void)b;                   // 얕은 복사 — 소멸자 둘이 같은 포인터를 놓는다
    P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
    P3 e; P3 f(e); (void)f;
    P4 g, h; g = h;
    P5 i, j; i = j;
    P6 k, l; k = l;
    std::printf("여섯 자리 전부 컴파일됐다\n");
    a.p = nullptr; b.p = nullptr;             // 이중 해제를 피해 치운다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex (cc exit=0) =====
copy07.cpp: In function ‘int main()’:
copy07.cpp:47:24: warning: implicitly-declared ‘constexpr P2& P2::operator=(const P2&)’ is deprecated [-Wdeprecated-copy]
   47 |     P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                        ^
copy07.cpp:14:5: note: because ‘P2’ has user-provided ‘P2::P2(const P2&)’
   14 |     P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
      |     ^~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex (cc exit=0) =====
copy07.cpp:14:5: warning: definition of implicit copy assignment operator for 'P2' is deprecated because it has a user-provided copy constructor [-Wdeprecated-copy-with-user-provided-copy]
   14 |     P2(const P2& o) : p(static_cast<char*>(std::malloc(8))) { (void)o; }
      |     ^
copy07.cpp:47:22: note: in implicit copy assignment operator for 'P2' first required here
   47 |     P2 c; P2 d(c); c = d;                     // 암묵 복사 대입을 쓴다
      |                      ^
1 warning generated.
```

```text
===== echo "copy07 탐침 여섯  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
copy07 탐침 여섯  g++ 경고 1
===== echo "copy07 탐침 여섯  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic copy07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
copy07 탐침 여섯  clang 경고 1
===== echo "copy07 을 ASan 으로 돌리면: $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. copy07.cpp -o exa 2>/dev/null; ./exa >/dev/null 2>asan16.txt; grep -cE 'ERROR: (Address|Leak)Sanitizer' asan16.txt) 건" (exit=0) =====
copy07 을 ASan 으로 돌리면: 1 건
===== echo "그 리포트의 요약: $(grep -hE '^SUMMARY' asan16.txt | head -1 | grep . || echo 리포트 없음)" (exit=0) =====
그 리포트의 요약: SUMMARY: AddressSanitizer: 24 byte(s) leaked in 3 allocation(s).
```

**왜 그런가**

| 심은 것 | g++ | clang | 실제로는 |
|---|---|---|---|
| 1. 소멸자만 쓰고 복사를 안 막았다 | 0 | 0 | ★★★ 얕은 복사 → 이중 해제 |
| 2. 복사 생성자만 쓰고 복사 대입은 안 썼다 | ★ **1** | ★ **1** | ★★ 암묵 복사 대입이 deprecated |
| 3. 복사 생성자가 멤버 하나를 빠뜨렸다 | 0 | 0 | ★★ `b` 가 초기화되지 않은 채 복사된다 |
| 4. 복사 대입이 `*this` 를 안 돌려준다 | 0 | 0 | ★ 연쇄 대입이 컴파일 안 된다 |
| 5. 자기 대입을 안 막은 대입 연산자 | 0 | 0 | ★★★ 4번의 use-after-free |
| 6. 복사 대입이 멤버를 하나도 안 옮긴다 | 0 | 0 | ★★ 대입이 아무 일도 안 한다 |

- ★★★ **답한 것 1, 침묵한 것 5**이고 **`cc exit=0`** 이다.
- ★★★ **답한 그 하나가 [목록의 18번 주제](../18-rule-of-zero-three-five-default-delete/)의 예고다** — 「복사 생성자를 썼으면 **복사 대입도 결정하라**」.\
  ★ 경고 이름은 컴파일러마다 다르다(`-Wdeprecated-copy` 대 `-Wdeprecated-copy-with-user-provided-copy`)지만 **가리키는 자리가 같다.**
- ★★ **ASan 은 `24 byte(s) leaked in 3 allocation(s)` 를 잡는다.**\
  ★ 그런데 그 셋은 **「복사가 틀렸다」가 아니라 「소멸자가 없다」는 사고**(`P2`·`P3` 류의 `malloc`)다.\
  **ASan 도 복사의 논리는 못 본다.**
- ★★★ **탐침 5번에 ASan 이 침묵하는 이유** — 이 파일의 `i = j` 는 **서로 다른 객체**다.\
  자기 대입 경로를 **밟지 않았으므로** 사고가 안 난다. **「탐침을 심었다」와 「그 경로를 밟았다」는 다른 것**이다.

### 8. ★ 경계는 「**그 줄에서 객체가 태어나는가**」 하나다

- **선언과 함께 쓴 `=` 는 초기화**다 — 왼쪽이 **그 줄에서 처음 생기므로** 복사 **생성자**가 돈다.
- **이미 선언된 것에 쓴 `=` 는 대입**이다 — 왼쪽이 **이미 있으므로** 옛 내용을 버리는 **복사 대입**이 돈다.
- ★★ **그래서 「기본 생성자 + 대입」으로 읽으면 계수가 안 맞는다.** 1번의 `(1)` 은 로그가 **한 줄**이다.
- ★★★ **복사 생성자에 계수기를 심어 「복사 횟수」를 세는 코드는 두 군데서 틀린다.**
  - **대입은 안 세진다** — 다른 함수다.
  - **생략된 것도 안 세진다** — 2번의 `prvalue()` 판은 **0회**다(C++17 의무 생략).

### 9. ★★ 하나는 **표준**(C++17부터), 하나는 **미명시**, 하나는 **관찰**

- 「**`prvalue` 를 돌려받는 자리에 복사 생성자가 안 불린다**」 — ★★★ **표준**이다. **C++17부터 의무**다.\
  ★ 그 전에는 **허용**일 뿐이었다. 「어느 버전부터인가」가 답의 절반이다.
- 「**`named()` 를 돌려받는 자리에 아무것도 안 불린다**」 — ★★★ **미명시**다.\
  표준은 NRVO 를 **허용할 뿐 강제하지 않는다.** `-fno-elide-constructors` 로 **실제로 갈렸다**(2번).
- 「**자기 대입 뒤에 값이 상한다**」 — ★★★ **관찰**이다. UB 이므로 **아무 일이나 일어날 수 있다.**\
  ★ 근거로 쓸 수 있는 것은 「**ASan 이 `heap-use-after-free` 라고 불렀다**」와 「**15판이 전부 `0` 이었다**」뿐이다.\
  「**항상 `0` 이 나온다**」로 적으면 구현 관찰을 표준 보장으로 올린 것이 된다.

### 10. 다른 주제와 잇기

- **얕은 복사가 이중 해제를 만드는 것**은 [15번](../15-raii-resources-as-types/)의 **(4)가 실측했다** —\
  `[놓음]` **두 줄**과 ASan 의 **`double-free`**. 여기 3번은 **그것을 고치는 쪽**이다.
- 「**복사 생성자를 썼으면 복사 대입도 결정하라**」의 정본은 [목록의 **18번 주제**](../18-rule-of-zero-three-five-default-delete/)(0/3/5의 법칙)다.\
  ★ 7번의 탐침 2번이 그 주제의 **유일한 컴파일러 신호**다.
- 「**`return t;` 의 `t` 가 먼저 rvalue 로 취급된다**」는 [9번](../09-rvalue-references-move-and-forward/)이 정본이고,\
  값 범주 자체는 [8번](../08-value-categories-lvalue-prvalue-xvalue/)이다.
- ★★ **러스트는 복사가 기본이 아니다** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)).\
  **`Clone` 을 손으로 불러야** 깊은 복사가 되고, `Copy` 는 **비트 복사가 안전한 타입에만** 붙는다.\
  ★ C++ 은 **아무 말이 없으면 멤버별 복사를 만들어 준다** — **기본값이 정반대**다.\
  ★ 그래서 러스트에는 **이 주제의 4번(자기 대입)·7번(탐침) 같은 자리가 없다** — 대신 [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)에서 볼 대가를 치른다.
- ★ **값 타입이냐 참조 타입이냐가 복사의 뜻을 정하는 언어**는 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **2번**([`02-struct-vs-class-choosing/`](../../../csharp/syntax/02-struct-vs-class-choosing/))이다.\
  ★ C++ 은 **타입마다 복사의 뜻을 저자가 정한다** — 그 권한이 이 주제의 값이자 비용이다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `copy01.cpp` 전수 격자 | g++ · clang 각 1회 | ★★★ `(1)`\~`(3)` **복사 생성** · `(4)` **복사 대입** · `(8)` **로그 0줄** · 객체 **8개** · 두 컴파일러 동일 |
| `copy02.cpp` 생략 | g++ · clang 각 2회(기본 · `-fno-elide-constructors`) | ★★★ **5개 대 6개** · 늘어난 자리는 `named()` 하나 · 늘어난 것은 **이동 생성자** |
| `copy03.cpp` 깊은 복사 | g++ 1회 | ★★ 주소 **0** · 내용 **1** · `malloc` **4** · `free` **1** |
| `copy04.cpp` 자기 대입 | g++ 1회 + **15판 반복** + ASan 1회 | ★★★ `0`(15/15 동일) · **경고 0건 · `run exit=0`** · ASan **`heap-use-after-free`** (`run exit=1`) |
| `copy05.cpp` copy-and-swap | g++ 1회 | ★★★ 자기 대입 안전 · `s1` **원본 그대로** · naive 는 **해제된 주소 유지**(`1`) |
| `copy06.cpp` 값으로 받는 복사 생성자 | g++ · clang 각 1회 | ★★ **양쪽 `cc exit=1`** · 복사 대입 쪽은 **통과** |
| `copy07.cpp` 탐침 여섯 | g++ · clang 각 1회 + ASan 1회 | ★★★ **경고 1 · 1**(탐침 2번) · ASan **24바이트 · 3할당** |
| `copy08.cpp` 형태 | g++ 1회 | `a="가나다" b="가나다" c="가나다"` (자기 대입 포함) |
| `copy09.cpp` 금지 사례 | g++ 1회 | **에러 3건**(const 멤버 · 참조 멤버 · const 를 안 받는 복사 생성자) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · ASan)에서만** 그렇다.

- ★★★ **4번의 `0`** — UB 의 결과다. 15판이 같았다는 것은 **관찰이지 보장이 아니다.**
- ★★★ **2번의 NRVO** — **미명시**다. 다른 컴파일러·다른 최적화 수준에서 갈릴 수 있다.
- ★★ **진단 문구와 경고 이름 전부** · **ASan 이 사고에 붙이는 이름** · `run exit=1`(ASan `ABORTING`).
- ★ **ASan 리포트의 PID·주소·스택 프레임 줄.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **선언과 함께 쓴 `=` 는 복사 생성자, 이미 있는 것에 쓴 `=` 는 복사 대입**인 것.
- **값 인자는 복사**이고 **`const&` 인자는 아무것도 안 만드는** 것.
- **`T(T)` 는 ill-formed** 인 것 — 그리고 **`T& operator=(T)` 는 합법**인 것.
- **`const` 멤버·참조 멤버가 있으면 복사 대입이 암묵적으로 지워지는** 것.
- ★★★ **prvalue 를 초기화·값 인자에 쓰는 자리의 생략은 C++17부터 의무**인 것.
- **컴파일러가 만드는 복사는 멤버별 복사**인 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ **4번의 자기 대입.** 근거로 쓰는 것은 「**ASan 이 `heap-use-after-free` 라고 불렀다**」와 「**값이 원래대로가 아니다**」뿐이다.
- ★★ **5번 `(3)` 의 「해제된 주소를 그대로 든다」** — 관찰이다. 그 뒤의 이중 해제도 UB 다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++14` 이하 판**(거기서는 2번의 `(1)`·`(3)` 도 갈릴 수 있다) ·\
  ★ **`-O1`\~`-O2` 에서 2번을 다시 찍는 판**(기본값만 봤다) ·\
  ★ **`v[i] = v[j]` 형태로 자기 대입을 일으키는 판**(4번은 `a = a` 로만 던졌다) ·\
  ★ **clang 으로 copy09 의 금지 사례**(g++ 로만 던졌다).
- **못 잰 것** — ★★★ **「복사가 시간을 얼마나 쓰나」.** 이 문서가 센 것은 **호출 횟수와 할당 횟수까지**다.\
  ★★ **런타임 할당 계수기**가 C++ 표준에 없어, 3번은 **소스에 계수기를 손으로 심었고** 7번은 **ASan 누수 리포트로 바꿔** 물었다.\
  ★ 바꾼 창이 못 보는 것도 있다 — **ASan 은 힙만 본다.**
- ★ 「**부적용인 창**」 — **`-O2` 어셈블리 세기.** 복사만 따로 재면 **비교 대상이 없어** 수가 뜻을 못 만든다.\
  **「안 쟀다」가 아니라 「여기서는 잴 것이 없다」다** — [목록의 **17번 주제**](../17-move-constructor-assignment-and-moved-from-state/)가 복사판과 이동판을 나란히 놓고 쓴다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **2번의 NRVO** — 미명시라 컴파일러 판이 바뀌면 움직인다.
- ★★ **7번의 탐침 중 하나라도 더 답하기 시작했는지**(지금은 **여섯 중 하나**).
- ★★ **6번의 진단 문구** — clang 이 붙여 주는 고침 문자열은 판마다 달라질 수 있다.
- ★ **ASan 이 누수를 보고하는 기본값**(`detect_leaks`) — 꺼지면 7번의 `24 byte(s)` 가 사라진다.
