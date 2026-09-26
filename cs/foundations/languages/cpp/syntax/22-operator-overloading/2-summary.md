# cpp/syntax/22 — 연산자 오버로딩 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 연산자 오버로딩](https://en.cppreference.com/w/cpp/language/operators) · [cppreference — 람다 식](https://en.cppreference.com/w/cpp/language/lambda)\
> ★ cppreference 「연산자 오버로딩」은 2026-09-26 에 열어 **네 문장을 확인했다** — 오버로드할 수 없는 것(`::`·`.`·`.*`·`?:`) ·\
> **비멤버가 될 수 없는 것**(`=`·`()`·`[]`·`->`, C++23 부터 `()`·`[]` 는 `static` 가능) · **`&&`·`||` 를 오버로드하면 단락 평가를 잃는다** · C++20 비교 연산자의 **재작성 후보**.
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`opov01.cpp` \~ `opov12.cpp`). ★ (3)만 **`-std=c++23`** 을 쓰고, 그 판은 **배너에 적었다.**\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.\
> ★★ **진단이 수백 줄인 블록((2))은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다. 전체 줄 수는 따로 셌다.
> **버전** — 연산자 오버로딩은 **C++98부터**. 숨은 friend 관용구는 C++98 에서도 되고, **`static operator()`·다차원 `operator[]`·deducing `this` 는 C++23** 이다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **이 편의 사슬** — (1)의 「**`1 + a` 가 막힌다**」가 [23번](../23-three-way-comparison-spaceship/)의 「**재작성 후보가 대칭을 푼다**」로 이어진다. **비교 연산자는 거기서 본다.**
> **경계** — 「클래스·멤버·`this`」는 [12번](../12-class-basics-members-access-and-this/)이, 「오버로드 해결」은 [1번](../01-function-overloading-and-overload-resolution/)이, 「인자 의존 탐색(ADL)」은 [6번](../06-namespaces-and-adl/)이 정본이다.\
> 「파이썬 dunder 로 본 연산자 오버로딩」은 [`oop-basics/`](../../../../oop-basics/) §19\~20 이 정본이고, 여기는 **C++ 규칙**만 본다.\
> 「변환 생성자와 `explicit`」은 [목록의 **24번 주제**](../24-explicit-and-converting-constructors/)다 — (1)이 그 자리를 **대칭의 재료**로만 건드린다.
> **대비** — Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **30번**(연산자 오버로딩 `std::ops`) — 아직 폴더가 없다.\
> ★ Rust 는 **트레이트 구현이 곧 연산자**이고 **`impl Add<Money> for i64` 를 따로 써야** `1 + a` 가 된다 — 이 편은 그것을 **던지지 않았다**(그 편이 생기면 거기서 잰다).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 두 컴파일러의 **진단 문구** · **후보 note 의 순서** | ★★★ **어느 줄이 에러인가 · 에러 개수 · `cc exit`** — 이 주제의 답 자체다 |
> | 진단의 **전체 줄 수**(표준 라이브러리 판에 따라 후보가 는다) | ★★★ **어느 연산자 함수가 몇 번 불렸나 · 피연산자 평가 로그** |
> | — | ★★ **`sizeof`(람다 · 함수 객체)** · **진단의 `(행,열)`** · **기능 매크로가 있나** |

## 한눈에 — 쉽게 말하면

**멤버 연산자는 「내가 먼저 말을 거는 사람」만 받는 창구다.**

은행 창구에 「**원화 계좌 전용**」이라고 붙어 있다. 원화 통장을 들고 온 손님이 「이 달러도 같이 넣어 주세요」라고 하면 **창구가 달러를 원화로 바꿔 받아 준다.**\
그런데 **달러를 든 손님이 먼저 와서** 「제 달러에 이 원화 통장을 더해 주세요」라고 하면 — **이 창구는 원화 통장 주인만 상대**하므로 받지 않는다.

- **멤버 `a.operator+(1)`** — 왼쪽(`a`)이 **창구 주인**이다. 오른쪽 `1` 은 **바꿔서 받아 준다.**
- **`1 + a`** — 왼쪽이 `int` 다. **`int` 에게는 그 창구가 없다** — 왼쪽은 **바꿔 주지 않는다.**
- **비멤버 `operator+(Money, Money)`** — 창구가 **은행 로비**에 있다. **양쪽을 다 바꿔서** 받는다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 원화 계좌 전용 창구 | ★★★ **멤버 연산자** — 왼쪽이 `*this` | (1) |
| 오른쪽 달러는 바꿔 준다 | ★★★ **인자는 암묵 변환된다** | (1) |
| 왼쪽 달러는 안 바꿔 준다 | ★★★ **`*this` 자리는 변환되지 않는다** | (1) |
| 로비의 공용 창구 | ★★★ **비멤버(숨은 friend)** | (1) |
| 환전을 아예 안 해 주는 은행 | ★★ **`explicit` 생성자** — 대칭이 통째로 사라진다 | (1) |
| 「손님이 먼저 말을 건다」가 정해진 창구 | ★★ **`operator<<`** — 왼쪽이 `ostream` 이다 | (2) |
| 두 사람 말을 다 듣고 나서 판단 | ★★★ **오버로드한 `&&`** — 단락 평가가 없다 | (5) |

```text
   Money a(1000);   Money(long) 은 암묵 변환 생성자

   멤버      a + 1   ->  a.operator+(Money(1))      ★ 오른쪽만 변환된다 — 된다
             1 + a   ->  1.operator+(a) ?           ★ int 에는 멤버가 없다 — 에러
   비멤버    a + 1   ->  operator+(a, Money(1))
             1 + a   ->  operator+(Money(1), a)     ★ 두 자리가 평등하다 — 된다
```

## 이 주제가 답하려는 질문

1. ★★★ **연산자를 멤버로 둘까 비멤버로 둘까** — 그 선택이 **대칭 변환**을 어떻게 가르나((1)).
2. **`<<`·`[]`·`()` 는 왜 그 자리에 그 모양으로 두나**((2)(3)(4)).
3. **오버로드하면 무엇이 사라지나** — `&&`·`||` 의 단락 평가((5)).
4. **무엇은 오버로드할 수 없고, 무엇은 멤버여야만 하나**((6)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러 대조다

★★★ **이 주제의 본체는 ② 컴파일 에러 전문이다** — 「이 줄이 되나 안 되나」가 규칙의 전부이고, **에러가 곧 교재**다.

```text
① 호출 로그             어느 연산자 함수가 불렸나 · 피연산자를 평가했나        (1)(3)(5)
② ★ 두 컴파일러 대조     1 + a · cout << p · 비멤버 = · operator. 의 진단 전문  (1)(2)(3)(6)(7)
③ ASan                   —                                                        부적용
④ 어셈블리               —                                                        부적용
⑤ 경고 격자              static operator() 를 C++20 으로 — 경고만 나고 통과    (8)
⑥ <type_traits>·sizeof   람다가 클래스인가 · 캡처 크기 · deducing this 의 Self   (3)(4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 호출 로그 | `operator+(1, 1000)` · **「오른쪽을 평가했다」** | **쓴다** |
| ★★★ **② 두 컴파일러 대조** | ★★★ **본체** — 에러 줄·개수·`cc exit` | **쓴다** |
| ③ ASan | ★ **부적용** — 이 주제에 메모리 오류가 없다 | **안 쓴다** |
| ④ 어셈블리 | ★ **부적용** — 연산자 오버로딩은 **이름만 다른 함수 호출**이다. 비용을 주장하지 않는다 | **안 쓴다** |
| ⑤ 경고 격자 | `-Wc++23-extensions` **양쪽 1건**, `-pedantic-errors` 로 **양쪽 에러 1** | **쓴다** |
| ⑥ `<type_traits>`·`sizeof` | `is_class<람다>` **1** · 캡처 `[k]` **4** · `[s]` **32** | **쓴다** |

- ★★ **④ 를 부적용으로 둔 이유** — `a + b` 는 **`operator+(a, b)` 라는 평범한 호출**로 바뀐다. 그 호출의 비용은 **평범한 함수 호출의 비용**이고, 이 편이 따로 말할 것이 없다.\
  ★ **「잴 것이 없다」가 결론**이다 — 「안 쟀다」가 아니다.

### (1) ★★★ 멤버 대 비멤버 — `1 + a` 는 왜 멤버일 때만 막히나

**언제 쓰나** — 산술·비교처럼 **양쪽이 평등한 이항 연산자**를 만들 때마다. **이 절이 이 주제의 중심이다.**

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

- ★★★ **3번 줄 하나만 에러다** — `a + 1` 은 되고 `1 + a` 는 안 된다.
- ★★★ **이유는 「`*this` 자리는 변환되지 않는다」다**. `a + 1` 은 `a.operator+(1)` 이고, 인자 `1` 은 `Money(long)` 으로 **암묵 변환된다.**\
  `1 + a` 는 **`1` 에게 `operator+` 멤버를 찾는다** — `int` 에는 멤버가 없고, **`1` 을 `Money` 로 바꿔서 멤버를 찾아 주지는 않는다.**
- ★★ **진단이 말해 준다** — g++ `(operand types are 'int' and 'Money')` · clang `('int' and 'Money')`. **왼쪽이 `int` 로 남아 있다.**

★★★ **같은 연산자를 비멤버로 옮긴다.**

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

- ★★★ **셋 다 된다** — 그리고 로그가 **`operator+(1, 1000)`** 이다. **왼쪽 `1` 이 `Money(1)` 로 변환되어** 첫 인자로 들어갔다.
- ★★ **`friend` 로 클래스 안에 정의했다** — 이것을 **숨은 friend** 라 한다. 클래스 밖 이름 조회에서는 안 보이고 **인자에 `Money` 가 있을 때만**([6번](../06-namespaces-and-adl/)의 ADL) 찾아진다.\
  ★ 비멤버이면서 **`private` 에 닿을 수 있고**, **아무 곳에서나 후보가 되지 않는다.**
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic opov02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a + a
      operator+(1000, 1000)
(2) a + 1
      operator+(1000, 1)
(3) 1 + a
      operator+(1, 1000)
    b=2000 c=1001 d=1001
```

★★ **그러면 대칭은 무엇 덕분이었나** — 생성자에 `explicit` 을 붙여 **변환을 막는다.**

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

- ★★★ **비멤버인데도 `a + 1` 과 `1 + a` 가 둘 다 막힌다** — **에러 2건**. 대칭을 만든 것은 비멤버가 아니라 「**두 자리 모두에서 변환이 허락된 것**」이었다.
- ★★ **그래서 규칙은 둘이 한 쌍이다** — **비멤버에 두면 두 자리가 평등해지고**, **변환 생성자가 있으면 그 평등이 섞인 타입까지 넓어진다.**\
  ★ 변환을 허락할지는 [목록의 **24번 주제**](../24-explicit-and-converting-constructors/)(`explicit`)의 판단이다.

```text
                      Money(long) 암묵        explicit Money(long)
   멤버 operator+     a+1 O   1+a ✗           a+1 ✗   1+a ✗
   비멤버 operator+   a+1 O   1+a O   ★        a+1 ✗   1+a ✗

   ★ 대칭 = 「비멤버」 × 「암묵 변환」 — 둘 중 하나라도 없으면 섞인 식이 막힌다
   ★ 비교 연산자는 C++20 에서 이 표가 바뀐다 — 23번의 재작성 후보
```

### (2) ★★ `operator<<` 는 비멤버여야 한다 — 멤버로 두면 거꾸로 써야 한다

**언제 쓰나** — `std::cout << obj` 로 찍고 싶을 때.

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

- ★★★ **멤버로 두면 `p << std::cout` 가 된다** — 멤버 연산자의 **왼쪽은 `*this`(= `Pt`)** 이기 때문이다. **(1)과 같은 규칙**이다.

```text
   std::cout << p     컴파일러가 찾는 두 길

   ① 멤버     std::cout.operator<<(p)       ostream 의 멤버 — ★ 남의 클래스라 더할 수 없다
   ② 비멤버   operator<<(std::cout, p)      ★ 우리가 쓸 수 있는 유일한 자리

   멤버로 둔 Pt::operator<<(ostream&)  은  p.operator<<(std::cout)  — 식으로 쓰면  p << std::cout
```

★★ **관례대로 `std::cout << p` 로 쓰면** — `-DCONVENTIONAL` 로 그 줄을 켠다.

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
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -ferror-limit=0 opov03.cpp -o ex 2>&1 | sed -n '1,4p' (cc exit=1) =====
opov03.cpp:15:15: error: invalid operands to binary expression ('ostream' (aka 'basic_ostream<char>') and 'Pt')
   15 |     std::cout << p << '\n';                    // 2. 관례대로 쓰면
      |     ~~~~~~~~~ ^  ~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/system_error:339:5: note: candidate function template not viable: no known conversion from 'Pt' to 'const error_code' for 2nd argument
```

```text
===== echo "g++   진단 $(g++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -fmax-errors=0 opov03.cpp -o ex 2>&1 | wc -l)줄 · 후보 note $(g++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -fmax-errors=0 opov03.cpp -o ex 2>&1 | grep -c 'note: candidate')개" (exit=0) =====
g++   진단 338줄 · 후보 note 47개
===== echo "clang 진단 $(clang++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -ferror-limit=0 opov03.cpp -o ex 2>&1 | wc -l)줄 · 후보 note $(clang++ -std=c++20 -Wall -Wextra -pedantic -DCONVENTIONAL -ferror-limit=0 opov03.cpp -o ex 2>&1 | grep -c 'note: candidate')개" (exit=0) =====
clang 진단 147줄 · 후보 note 47개
```

- ★★★ **g++ 진단이 338줄, clang 이 147줄** 이다 — **후보 note 가 양쪽 47개**다. 표준 라이브러리의 `operator<<` 오버로드를 **전부 후보로 나열**했기 때문이다.
- ★★★ **`std::cout << p` 는 `std::cout.operator<<(p)` 나 `operator<<(std::cout, p)` 를 찾는다** — **`ostream` 에 `Pt` 를 받는 멤버를 우리가 추가할 수 없으니** 비멤버밖에 없다.
- ★★ **그래서 `operator<<` 는 비멤버(대개 숨은 friend)** 이고, 반환은 **`std::ostream&`** 이다 — 그래야 `cout << a << b` 처럼 **이어 쓸 수 있다.** 형태 절의 ⑥이 그 모양이다.
- ★ **진단 줄 수는 흔들리는 칸**이다 — 표준 라이브러리 판이 바뀌면 후보가 는다. **근거는 「첫 에러 줄과 `cc exit=1`」이다**.

### (3) ★★ `operator[]` 두 벌 — 그리고 C++23 deducing `this` 로 하나로

**언제 쓰나** — 컨테이너 모양의 타입에서 **읽기와 쓰기를 둘 다** 열 때.

```cpp
/* opov04.cpp */
// operator[] 두 벌 — const 객체와 비const 객체가 각각 어느 쪽을 부르나
#include <cstdio>

struct Row {
    int a[3]{10, 20, 30};
    int&       operator[](int i)       { std::printf("      비const 판\n"); return a[i]; }
    const int& operator[](int i) const { std::printf("      const 판\n");   return a[i]; }
};

int main() {
    Row r;
    const Row& cr = r;
    std::printf("(1) r[0] = 99;\n");         r[0] = 99;
    std::printf("(2) int x = cr[0];\n");     int x = cr[0];
    std::printf("    x=%d\n", x);
#ifdef WRITE_CONST
    cr[1] = 5;                                 // 3. const 판으로 쓰려 하면
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic opov04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) r[0] = 99;
      비const 판
(2) int x = cr[0];
      const 판
    x=99
```

- ★★★ **같은 `[0]` 인데 불리는 판이 다르다** — 비`const` 객체는 **비`const` 판**, `const` 참조는 **`const` 판**이다. [10번](../10-const-correctness/)의 `const` 오버로드다.

```text
   r[0]    r 은 Row           ->  int&       operator[](int)            쓸 수 있다
   cr[0]   cr 은 const Row&   ->  const int& operator[](int) const      읽기만

   C++23   template <class Self> auto&& operator[](this Self&& self, int)
           r[0]   ->  Self = Row&         ->  int&
           cr[0]  ->  Self = const Row&   ->  const int&       ★ 한 벌이 두 벌 노릇을 한다
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DWRITE_CONST -fmax-errors=0 opov04.cpp -o ex (cc exit=1) =====
opov04.cpp: In function ‘int main()’:
opov04.cpp:17:11: error: assignment of read-only location ‘(& cr)->Row::operator[](1)’
   17 |     cr[1] = 5;                                 // 3. const 판으로 쓰려 하면
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DWRITE_CONST -ferror-limit=0 opov04.cpp -o ex (cc exit=1) =====
opov04.cpp:17:11: error: cannot assign to return value because function 'operator[]' returns a const value
   17 |     cr[1] = 5;                                 // 3. const 판으로 쓰려 하면
      |     ~~~~~ ^
opov04.cpp:7:11: note: function 'operator[]' which returns const-qualified type 'const int &' declared here
    7 |     const int& operator[](int i) const { std::printf("      const 판\n");   return a[i]; }
      |           ^~~~
1 error generated.
```

- ★★ **`const` 판으로는 쓸 수 없다** — 반환이 **`const int&`** 이기 때문이다. clang 이 그 반환 타입을 **짚어 준다.**
- ★★ **두 벌은 본문이 거의 같다** — 그 중복을 C++23 의 **deducing `this`**(명시적 객체 매개변수)가 하나로 합친다. **이 판이 받는지 던진다.**

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
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 opov05.cpp -o ex (cc exit=1) =====
opov05.cpp:8:23: error: explicit object parameters are incompatible with C++ standards before C++2b
    8 |     auto&& operator[](this Self&& self, int i) {           // ★ 명시적 객체 매개변수
      |                       ^~~~~~~~~~~~~~~~
1 error generated.
```

```text
===== clang++ -std=c++23 -Wall -Wextra -pedantic opov05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      Self 가 const 인가: 0
      Self 가 const 인가: 1
    x=99
    decltype(cr[0]) 가 const int& 인가: 1
```

```text
===== echo "g++   -std=c++23 : $(g++ -std=c++23 -dM -E -x c++ /dev/null | grep -cE '__cpp_explicit_this_parameter')" (exit=0) =====
g++   -std=c++23 : 0
===== echo "clang -std=c++23 : $(clang++ -std=c++23 -dM -E -x c++ /dev/null | grep -cE '__cpp_explicit_this_parameter')" (exit=0) =====
clang -std=c++23 : 0
```

| 판 | `-std=c++20` | `-std=c++23` | `__cpp_explicit_this_parameter` |
|---|---|---|---|
| **g++ 13.3.0** | 에러 | ★★★ **에러 9건** — `this` 를 매개변수 자리에서 **못 읽는다** | ★ **없다**(0) |
| **clang 18.1.3** | ★ 에러 — `incompatible with C++ standards before C++2b` | ★★★ **된다** — `Self` 가 `const` 인가 **0 · 1** | ★★ **없다**(0) |

- ★★★ **g++ 13 은 `-std=c++23` 으로도 못 받는다** — `expected identifier before 'this'`. **파서가 그 문법을 모른다.**\
  ★ 규칙 26 의 「없다고 적기 전에」와 같은 자리다 — **「안 된다」를 에러로 증명했다.**
- ★★★ **clang 18 은 `-std=c++23` 에서 된다** — 한 템플릿이 **`Self` 를 `Row&`(0)와 `const Row&`(1)** 로 추론해 두 벌 노릇을 했다.\
  ★ **`decltype(cr[0])` 가 `const int&`** 다 — `auto&&` 반환이 **`self` 의 `const` 를 그대로 전달**했다.
- ★★★ **그런데 clang 18 은 기능 매크로를 정의하지 않는다** — **코드는 되는데 `__cpp_explicit_this_parameter` 가 0** 이다.\
  ★★ **「매크로가 없으면 기능이 없다」도, 「있으면 된다」도 성립하지 않는 자리**다 — **던져서 확인하는 수밖에 없다.** 매크로가 없는 이유는 이 문서가 **확인하지 않았다.**

### (4) ★ `operator()` 와 함수 객체 — 람다는 그것이다

**언제 쓰나** — 「호출할 수 있는 값」을 만들 때. 표준 알고리즘에 넘기는 비교자·술어가 전부 이것이다.

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

- ★★★ **`lam1.operator()(1)` 이 된다** — 람다는 **`operator()` 를 가진 이름 없는 클래스**다. `is_class<람다>` 가 **1** 이다.

```text
   auto lam1 = [k](int x) { return x + k; };

   컴파일러가 만든 것(이름은 없다)
   class __람다 {
       int k;                                   ★ 캡처가 멤버가 된다  -> sizeof 4
   public:
       int operator()(int x) const { return x + k; }
   };
   __람다 lam1{k};                               ★ 그래서 lam1.operator()(1) 이 된다
```
- ★★★ **캡처가 곧 멤버다** — `sizeof` 가 **캡처 없음 1 · `[k]` 4 · `[&k]` 8 · `[k,big]` 16 · `[s]` 32** 다.\
  ★ 캡처 없는 람다의 **1** 은 「빈 클래스도 1바이트」([12번](../12-class-basics-members-access-and-this/) (2)) 규칙이다. `[k,big]` 이 12 가 아니라 **16** 인 것은 **`long` 정렬 패딩**이다.
- ★★ **손으로 쓴 `Adder` 와 `[k]` 람다가 둘 다 4** — **같은 물건**이다.
- ★★ **같은 모양으로 두 번 쓴 람다는 다른 타입**이다(`0`) — 람다 식마다 **새 클래스**가 생긴다.
- ★ **캡처 없는 람다만 함수 포인터로 바뀐다**(`42`) — 들고 다닐 상태가 없기 때문이다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic opov06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) add(1)=6 · lam1(1)=6 · lam1.operator()(1)=6
(2) sizeof  Adder 4 · 캡처없음 1 · [k] 4 · [&k] 8 · [k,big] 16 · [s] 32
(3) is_class<람다> 1 · 캡처 없는 람다를 함수 포인터로: 42
(4) 같은 모양의 람다 둘은 같은 타입인가: 0
```

### (5) ★★★ `&&`·`||` 를 오버로드하면 단락 평가가 사라진다

**언제 쓰나** — 「조건 타입」을 만들고 `&&` 로 엮고 싶어질 때. **유명한 함정**이다.

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

```text
   내장      false && right()            왼쪽이 false  ->  오른쪽을 안 본다        ★ 단락 평가
   오버로드  Flag{false} && right_f()    ->  operator&&(left_f(), right_f())
                                         함수를 부르려면 인자 둘을 다 만들어야 한다
                                         ->  왼쪽 · 오른쪽 · 본체                  ★ 단락이 없다
```

- ★★★ **`(2)` 는 왼쪽이 `false` 인데 오른쪽을 평가했다** — `operator&&` 는 **함수**이고, 함수를 부르기 전에 **인자를 전부 만든다.**
- ★★★ **`(3)` 의 `||` 도 같다** — 왼쪽이 `true` 인데 **오른쪽을 평가**했다.
- ★★ **순서는 왼쪽 → 오른쪽**이었다 — C++17 부터 **연산자 표기로 부른 오버로드는 내장 연산자의 순서 규칙**을 따른다(기준 소스 — 「C++17 전에는 그 순서 성질도 잃었다」).\
  ★ **단락은 여전히 잃는다** — 순서가 정해진 것과 **건너뛰는 것**은 다른 성질이다.
- ★★★ **처방은 하나다** — **`&&`·`||`·`,` 는 오버로드하지 않는다.** `explicit operator bool` 을 두면 **내장 `&&` 가 그대로** 쓰인다(`(1)` 과 같은 경로).
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic opov07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
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

### (6) ★ 오버로드할 수 없는 연산자 — 선언만 해 본다

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

- ★★ **다섯 다 에러 · 대조군 `->*` 는 통과**한다 — 에러 **5건 · 5건**.
- ★★★ **g++ 가 `?:` 에만 「ISO C++ 가 금지한다」고** 말하고, 나머지 넷(`.`·`.*`·`::`·`sizeof`)은 **`expected type-specifier`** 다.\
  ★ **앞의 넷은 `operator` 뒤에 올 수 있는 낱말이 아니라서 파서가 막고**, `?:` 는 **읽고 나서 규칙으로** 막는다. clang 은 다섯 다 **`expected a type`** 이다.
- ★ **`sizeof` 는 기준 소스의 목록(`::`·`.`·`.*`·`?:`)에 없다** — 연산자 함수 이름으로 쓸 수 있는 낱말 목록에 **애초에 없기** 때문이다.

```text
   연산자 오버로딩의 세 칸

   오버로드할 수 없다        ::   .   .*   ?:   (그리고 sizeof 등 연산자 함수 이름이 아닌 것)   (6)
   멤버로만 된다            =   ()   []   ->                                                  (7)
   어디든 되지만 비멤버 권장  + - * / == < <<  …  양쪽이 평등한 이항                            (1)(2)
   오버로드하면 성질을 잃는다 &&   ||   ,         단락 평가(,는 순서 성질 — 이 문서는 안 던졌다)   (5)
```

### (7) ★★ 멤버여야만 하는 연산자 넷 — 비멤버로 선언하면

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

- ★★★ **넷 다 에러 · 대조군 `operator+` 는 통과** — `=`·`[]`·`()`·`->`.
- ★★ **왜 `=` 는 멤버여야 하나** — 컴파일러가 **복사 대입을 암묵 선언**하는데([16번](../16-copy-constructor-and-copy-assignment/)), 비멤버를 허락하면 **클래스 밖에서 그 규칙을 뒤집을 수** 있게 된다.\
  ★ 이것은 **흔히 드는 설계 이유**다 — 이 문서가 확인한 것은 **에러가 난다는 것**뿐이다(내 추론).
- ★★ **진단이 판마다 다르다** — g++ 는 `[]`·`()` 에 **「member function」**, `=`·`->` 에 「**non-static member function**」이라고 쓴다.\
  ★ C++23 이 `operator[]`·`operator()` 에 **`static` 을 허락한 것**을 반영한 문구로 보인다(추론). clang 은 넷 다 **`non-static member function`** 이다.

### (8) ★★ 종료 코드 0인데 ill-formed — C++23 의 `static operator()` 를 C++20 으로

★★ **이 배치의 고정 항목**([14번](../14-destructors-and-deterministic-destruction/) (8) · [18번](../18-rule-of-zero-three-five-default-delete/) (7))의 새 항목이다.

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

- ★★★ **두 컴파일러 다 `cc exit=0 · run exit=0`** 이고 **값도 맞게 나온다**(`42`).\
  그런데 **C++20 에서 `operator()` 는 비`static` 멤버여야 한다** — **ill-formed** 이다. 경고가 스스로 그렇게 말한다(`only with '-std=c++23'` · `is a C++23 extension`).
- ★★★ **`-pedantic` 으로는 경고에 머물고 `-pedantic-errors` 라야 에러 1 · 1** 이다 — 앞 배치들의 세 건과 **같은 집안**이다.
- ★★ **다음 판의 문법을 앞 판에서 받아 주는 것**이 이 모양이다 — **「`-std=c++20` 으로 빌드했다」가 「C++20 코드다」가 아니다.**

## 문법 — 형태와 규칙

### 형태

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

- ★★ **`1 + a` 의 결과가 `(2, 2)`** — `1` 이 `Vec2(1, 0)` 으로 바뀌어 **왼쪽 자리**에 들어갔다((1)의 비멤버 대칭).
- ★★ **`!=` 를 안 썼는데 `c != d` 가 된다** — C++20 의 **재작성 후보**다. [23번](../23-three-way-comparison-spaceship/)이 정본이다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic opov11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(4, 6) (2, 2) (-1, -2)
1 1 6
```

### 규칙

- ★★★ **양쪽이 평등한 이항 연산자(`+`·`-`·`==`…)는 비멤버** — 멤버면 **왼쪽이 변환되지 않아** `1 + a` 가 막힌다((1)).
- ★★ **복합 대입(`+=`)·단항(`-a`)은 멤버** — 왼쪽이 **바뀌는 자기 자신**이다. 이항 `+` 는 **`+=` 로 만든다**(형태의 ④).
- ★★★ **`operator<<` 는 비멤버, `std::ostream&` 를 돌려준다**((2)).
- ★★ **`operator[]` 는 `const`/비`const` 두 벌** — C++23 deducing `this` 로 하나로 합칠 수 있으나 **g++ 13 은 못 받는다**((3)).
- ★★★ **`&&`·`||`·`,` 는 오버로드하지 않는다** — 단락 평가를 잃는다((5)).
- ★ **`=`·`[]`·`()`·`->` 는 멤버여야 한다**((7)) · **`::`·`.`·`.*`·`?:` 는 오버로드할 수 없다**((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| 멤버 `operator+` 로 `1 + a` | ★★★ **에러 1 · 1** — 왼쪽이 `int` 로 남는다 | (1) |
| `explicit` 생성자 + 비멤버로 `a + 1`·`1 + a` | ★★ **에러 2 · 2** | (1) |
| 멤버 `operator<<` 로 `cout << p` | ★★ **에러**(g++ 338줄 · clang 147줄) | (2) |
| g++ 13 에서 deducing `this` | ★★ **에러 9건**(`-std=c++23` 으로도) | (3) |
| `operator.` · `operator.*` · `operator::` · `operator?:` · `operator sizeof` | ★ **에러 5 · 5** | (6) |
| 비멤버 `operator=` · `[]` · `()` · `->` | ★ **에러 4 · 4** | (7) |

## 어디서 틀리나

### 1. ★★★ 「멤버든 비멤버든 결과는 같다」

(1)이 반증이다 — **`1 + a` 가 멤버일 때만 막힌다.** 차이는 **`*this` 자리가 변환되지 않는다**는 한 가지다.

### 2. ★★ 「비멤버로 옮기면 대칭이 된다」

**절반만 맞다.** (1)의 `explicit` 판이 반증이다 — **변환이 없으면 비멤버여도 섞인 식은 막힌다.** 대칭은 **비멤버 × 암묵 변환**이다.

### 3. ★★★ 「`&&` 를 오버로드해도 내장처럼 동작한다」

(5)가 반증이다 — **왼쪽이 `false` 여도 오른쪽을 평가한다.** 오른쪽에 **부작용·비싼 계산·널 역참조**가 있으면 그대로 일어난다.

### 4. ★★ 「`-std=c++23` 을 주면 C++23 기능이 된다」

(3)이 반증이다 — **g++ 13 은 deducing `this` 를 모른다.** `-std=` 는 **기본값 선택**이지 기능 목록이 아니다.

### 5. ★★ 「기능 매크로를 보면 되는지 안다」

(3)이 반증이다 — **clang 18 은 기능을 받으면서 매크로를 안 정의한다.** 매크로가 0 이라고 **없는 것이 아니다.**

### 6. ★ 「`-std=c++20` 으로 빌드되면 C++20 코드다」

(8)이 반증이다 — **`static operator()` 가 경고만 내고 통과한다.** `-pedantic-errors` 라야 막힌다.

### 7. ★ 「람다는 함수다」

(4)가 반증이다 — **`operator()` 를 가진 클래스**이고, **캡처가 멤버**라 `sizeof` 가 캡처만큼 커진다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 거의 전부다** — 연산자 오버로딩은 **이름 조회와 오버로드 해결의 규칙**이고, 구현이 끼어들 자리가 적다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **멤버 연산자의 `*this` 자리는 변환되지 않는다**((1)) · **`&&`·`\|\|` 오버로드는 단락 평가가 없다**((5)) · **C++17 부터 연산자 표기의 피연산자 순서는 내장 규칙을 따른다**((5)) · **오버로드 불가 넷·멤버 필수 넷**((6)(7)) · **람다는 클로저 타입(클래스)**((4)) | 진단 전문 + `cc exit` · 호출 로그 | ★★★ 「**이 `&&` 가 오버로드된 것인가**」 — 호출 자리만 보면 **내장과 똑같이 생겼다**((5)) |
| **조건부 표준** | 특정 판에서만 | ★★ **`static operator()`·다차원 `[]`·deducing `this` 는 C++23** | `-std=c++20`/`c++23` 두 판 | ★★ **g++ 13 은 C++23 판에서도 deducing `this` 를 모른다** |
| **구현 정의** | 문서화 의무 | ★ **클로저 타입의 크기와 배치**(`[k,big]` 16 — 패딩 포함) · 진단 문구 · **기능 매크로를 언제 정의하나** | `sizeof` · `-dM -E` | ★ **clang 18 은 기능이 되는데 매크로가 0** |
| **미명시** | 몇 가지 중 하나 | ★ **캡처 멤버의 순서**(표준은 클로저 멤버의 선언 순서를 정하지 않는다) — **이 문서는 찍지 않았다** | — | — |
| **UB** | 아무 일이나 | ★ **이 주제에는 없다** — 연산자 오버로딩 자체는 UB 를 만들지 않는다 | — | ★ 부적용(③ ASan 과 같은 이유) |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 호출 로그 |
|---|---|---|---|---|
| 멤버 `operator+` 로 `1 + a` | 표준 | **error 1** | **error 1** | — |
| ★★★ **오버로드한 `&&` 가 오른쪽을 평가** | 표준 | ★★★ **0건** | ★★★ **0건** | ★★★ **「오른쪽을 평가했다」** |
| ★★ **`static operator()` 를 C++20 으로** | 조건부 | ★ **warning 1** · `cc exit=0` | ★ **warning 1** · `cc exit=0` | 값 `42` |
| 비멤버 `operator=` | 표준 | **error** | **error** | — |
| ★★ **deducing `this`** | 조건부 | ★★ **C++23 에서도 error 9** | ★ C++23 **통과** · 매크로 **0** | `Self` const **0 · 1** |

- ★★ **이 표의 결론** — ★★★ **`&&` 오버로드의 함정은 컴파일러가 한마디도 안 한다.** 로그로만 보인다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 양쪽이 평등한 이항 연산 | ★★★ **비멤버 숨은 friend** | 두 자리가 평등해진다((1)) |
| 자기 자신을 바꾸는 연산(`+=`·`++`) | ★★ **멤버** | 왼쪽이 `*this` 다 |
| 출력 `<<` | ★★★ **비멤버 · `ostream&` 반환** | 왼쪽이 `ostream` 이다((2)) |
| 첨자 `[]` | ★★ **멤버 두 벌**(C++23 이면 deducing `this`) | 읽기·쓰기((3)) — **g++ 13 은 두 벌로** |
| 호출 가능한 값 | ★★ **람다**(상태가 많으면 클래스) | 같은 물건이다((4)) |
| 조건을 엮는 `&&`·`\|\|` | ★★★ **오버로드하지 않는다** · `explicit operator bool` | 단락 평가((5)) |
| 비교 연산자 | ★★★ **C++20 `<=>`·`==`** — 여섯을 손으로 쓰지 않는다 | [23번](../23-three-way-comparison-spaceship/) |

## 핵심 문장

- ★★★ **멤버 연산자는 왼쪽(`*this`)을 변환하지 않는다** — 그래서 `a + 1` 은 되고 `1 + a` 는 막힌다.
- ★★ **비멤버로 옮기면 두 자리가 평등해진다** — 단 **암묵 변환이 있어야** 섞인 식이 된다(`explicit` 이면 둘 다 막힌다).
- ★★ **`operator<<` 는 비멤버** — 멤버로 두면 `p << cout` 로 거꾸로 써야 한다.
- ★★★ **`&&`·`||` 를 오버로드하면 단락 평가가 사라진다** — 왼쪽이 `false` 여도 오른쪽을 평가했고 **경고는 0건**이었다.
- ★★ **람다는 `operator()` 를 가진 클래스이고 캡처가 멤버다** — `[s]` 가 32바이트였다.
- ★★ **deducing `this` 는 clang 18 에서 되고 g++ 13 에서 안 된다** — 그리고 **clang 18 도 매크로는 0** 이다.
- ★ **`static operator()` 는 C++20 모드에서 경고만 내고 통과한다** — `-pedantic-errors` 라야 막힌다.

## 관련 자료

- [23번](../23-three-way-comparison-spaceship/) — ★★★ **이 편의 사슬.** (1)의 「`1 + a` 가 막힌다」를 **비교 연산자에서는 재작성 후보가 푼다.**
- [12번](../12-class-basics-members-access-and-this/) — **멤버 함수와 `this`.** (1)의 「`*this` 자리」가 거기서 온다. (4)의 「빈 클래스 1바이트」도 거기 (2)다.
- [1번](../01-function-overloading-and-overload-resolution/) — **오버로드 해결.** 연산자 식은 **후보를 모은 뒤 그 절차**를 탄다.
- [6번](../06-namespaces-and-adl/) — **ADL.** 숨은 friend 가 찾아지는 길이다.
- [10번](../10-const-correctness/) — **`const` 오버로드.** (3)의 두 벌이 그것이다.
- [16번](../16-copy-constructor-and-copy-assignment/) — **복사 대입.** (7)의 `operator=` 가 멤버여야 하는 이유와 이어진다.
- [목록의 **24번 주제**](../24-explicit-and-converting-constructors/) — **`explicit` 과 변환 생성자.** (1)의 대칭이 그 판단에 달려 있다.
- [`oop-basics/`](../../../../oop-basics/) §19\~20 — **파이썬 dunder 로 본 연산자 오버로딩.** 여기는 **C++ 규칙**까지.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **30번**(`std::ops`) — **폴더가 아직 없다.** Rust 는 `impl Add<Rhs> for Lhs` 를 **방향마다** 쓴다 — 이 편은 **던지지 않았다.**

## 용어 풀이

> **연산자 오버로딩(operator overloading)** — `a + b` 를 **`operator+` 라는 이름의 함수 호출**로 푸는 것.\
> 예: (1)의 로그 `operator+(1, 1000)`.

> **멤버 연산자** — 클래스의 멤버로 둔 연산자. **왼쪽 피연산자가 `*this`** 이고 **변환되지 않는다.**\
> 예: (1)에서 `1 + a` 가 막혔다.

> **숨은 friend(hidden friend)** — 클래스 안에 `friend` 로 **정의**한 비멤버 함수. **ADL 로만** 찾아진다.\
> 예: (1)의 `opov02.cpp` 와 형태의 `operator+`·`operator<<`.

> **대칭 변환** — 이항 연산자의 **두 자리가 똑같이 암묵 변환을 받는 것**. 비멤버 + 암묵 변환 생성자에서 성립한다.\
> 예: (1)에서 `1 + a` 가 `operator+(Money(1), a)` 가 됐다.

> **단락 평가(short-circuit evaluation)** — 내장 `&&`·`||` 가 **왼쪽만으로 답이 정해지면 오른쪽을 안 보는 것**. 오버로드하면 사라진다.\
> 예: (5)의 `(1)` 과 `(2)`.

> **클로저 타입(closure type)** — 람다 식마다 컴파일러가 만드는 **이름 없는 클래스**. `operator()` 를 가진다.\
> 예: (4)에서 `is_class<람다>` 가 1, 같은 모양 둘이 **다른 타입**이었다.

> **deducing `this`(명시적 객체 매개변수)** — C++23. 멤버 함수의 첫 매개변수를 **`this Self&& self`** 로 받아 **`const`·값 범주를 템플릿으로 추론**하는 것.\
> 예: (3)에서 clang 18 이 `Self` 를 `const` 0 · 1 로 추론했다.

## 더 들어가면

- **`operator<=>`·`operator==` 와 재작성 후보** — 비교 연산자는 C++20 에서 규칙이 바뀌었다. [23번](../23-three-way-comparison-spaceship/)이 정본이다.
- **`operator->` 의 사슬** — `->` 를 오버로드하면 반환값에 대해 **다시 `->` 를 적용**한다(스마트 포인터의 원리). 이 문서는 선언 규칙만 봤다.
- **`operator new`/`operator delete`** — 할당 함수도 이 이름을 쓰지만 **식이 아니라 할당 자리**에 붙는다. [20번](../20-virtual-destructors-and-polymorphic-deletion/) (7)이 클래스별 판을 찍었다.
- **사용자 정의 리터럴 `operator""_km`** — 연산자라는 이름을 쓰지만 성격이 다르다. 목록의 다른 주제다.
