# cpp/syntax/20 — 가상 소멸자와 다형적 삭제 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소** · **진단 문구** · **UB 인 실행의 결과 그 자체**다.\
> 근거로 쓰는 것은 다음이다 — **어느 소멸자·해제 함수가 몇 번 불렸나** · **격자의 0/1** · **`sizeof`** ·\
> **`cc exit`/`run exit`** · **경고·에러 개수** · **어셈블리에서 무엇을 `call` 하나**.
> ★★★ **19편이 잰 것(`~DerNV` 0회 · 128바이트 · 경고 조건 · vtable 두 칸)은 다시 재지 않았다** — 인용만 한다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`shared_ptr` 둘은 `~Derived` 를 부르고 나머지 셋은 `~Base` 만** — 갈린 것은 **그 순간 손에 든 포인터의 타입**이다

**출력**

```cpp
/* vdtor01.cpp */
// 소멸자가 가상이 아닌 기반 — shared_ptr 와 unique_ptr 에 같은 파생 객체를 맡긴다
#include <cstdio>
#include <memory>

struct Base {                                       // ★ 소멸자가 가상이 아니다
    ~Base() { std::printf("      ~Base\n"); }
};
struct Derived : Base {
    ~Derived() { std::printf("      ~Derived\n"); }
};

int main() {
    std::printf("(1) shared_ptr<Base>(new Derived)\n");
    { std::shared_ptr<Base> p(new Derived); }

    std::printf("(2) shared_ptr<Base> = make_shared<Derived>()\n");
    { std::shared_ptr<Base> p = std::make_shared<Derived>(); }

    std::printf("(3) Base* 로 먼저 받은 뒤 shared_ptr<Base>(raw)\n");
    { Base* raw = new Derived; std::shared_ptr<Base> p(raw); }

    std::printf("(4) unique_ptr<Base>(new Derived)\n");
    { std::unique_ptr<Base> p(new Derived); }

    std::printf("(5) unique_ptr<Derived> 를 unique_ptr<Base> 로 옮긴다\n");
    { std::unique_ptr<Base> p = std::make_unique<Derived>(); }

    std::printf("(6) sizeof  shared_ptr<Base> %zu · unique_ptr<Base> %zu\n",
                sizeof(std::shared_ptr<Base>), sizeof(std::unique_ptr<Base>));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic vdtor01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr<Base>(new Derived)
      ~Derived
      ~Base
(2) shared_ptr<Base> = make_shared<Derived>()
      ~Derived
      ~Base
(3) Base* 로 먼저 받은 뒤 shared_ptr<Base>(raw)
      ~Base
(4) unique_ptr<Base>(new Derived)
      ~Base
(5) unique_ptr<Derived> 를 unique_ptr<Base> 로 옮긴다
      ~Base
(6) sizeof  shared_ptr<Base> 16 · unique_ptr<Base> 8
```

**왜 그런가**

- ★★★ **`(1)`·`(2)` 는 `~Derived` → `~Base`** — `shared_ptr` 의 `Y*` 생성자는 **`delete ptr` 를 삭제자로** 쓰고, `ptr` 가 **`Derived*`** 였다.
- ★★★ **`(3)` 은 `~Base` 만** — `raw` 가 **이미 `Base*`** 였으므로 삭제자가 **`delete (Base*)`** 를 기억했다.\
  ★ **같은 `shared_ptr<Base>` 인데 결과가 다르다** — 타입에 흔적이 없으니 **코드를 봐도 안 보인다.**
- ★★ **`(5)` 도 `(4)` 와 같다** — `unique_ptr<Derived>` 를 `unique_ptr<Base>` 로 옮기면 삭제자가 **`default_delete<Base>`** 가 된다.
- ★ **`sizeof` 는 16 과 8** — `shared_ptr` 는 **제어 블록을 가리키는 포인터**가 하나 더 있다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic vdtor01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr<Base>(new Derived)
      ~Derived
      ~Base
(2) shared_ptr<Base> = make_shared<Derived>()
      ~Derived
      ~Base
(3) Base* 로 먼저 받은 뒤 shared_ptr<Base>(raw)
      ~Base
(4) unique_ptr<Base>(new Derived)
      ~Base
(5) unique_ptr<Derived> 를 unique_ptr<Base> 로 옮긴다
      ~Base
(6) sizeof  shared_ptr<Base> 16 · unique_ptr<Base> 8
```

### 2. ★★★ **표준의 보장이다** — `r` 의 스택에 **`_Sp_counted_ptr<Base*>`** 가 찍힌다

**출력**

```cpp
/* vdtor02.cpp */
// 같은 대비를 ASan 에게 묻는다 — 인자 s 는 shared_ptr, r 은 raw 를 거친 shared_ptr, u 는 unique_ptr
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstring>
#include <memory>

struct Base    { long a = 1; ~Base()    { std::fprintf(stderr, "      ~Base\n"); } };
struct Derived : Base { long b = 2; ~Derived() { std::fprintf(stderr, "      ~Derived\n"); } };

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "s";
    if (std::strcmp(m, "s") == 0) {
        std::fprintf(stderr, "(s) shared_ptr<Base>(new Derived)\n");
        std::shared_ptr<Base> p(new Derived);
    } else if (std::strcmp(m, "r") == 0) {
        std::fprintf(stderr, "(r) Base* raw = new Derived; shared_ptr<Base>(raw)\n");
        Base* raw = new Derived;
        std::shared_ptr<Base> p(raw);
    } else {
        std::fprintf(stderr, "(u) unique_ptr<Base>(new Derived)\n");
        std::unique_ptr<Base> p(new Derived);
    }
    std::fprintf(stderr, "    블록을 나왔다\n");
}
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor02.cpp -o exa && ./exa s 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(s) shared_ptr<Base>(new Derived)
      ~Derived
      ~Base
    블록을 나왔다
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor02.cpp -o exa && ./exa r 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(r) Base* raw = new Derived; shared_ptr<Base>(raw)
      ~Base
=================================================================
==4050402==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x502000000010 in thread T0:
  object passed to delete has wrong type:
  size of the allocated type:   16 bytes;
  size of the deallocated type: 8 bytes.
    #0 0x7e96cd8ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x59f654b23ac9 in std::_Sp_counted_ptr<Base*, (__gnu_cxx::_Lock_policy)2>::_M_dispose() /usr/include/c++/13/bits/shared_ptr_base.h:428
    #2 0x59f654b22961 in std::_Sp_counted_base<(__gnu_cxx::_Lock_policy)2>::_M_release() /usr/include/c++/13/bits/shared_ptr_base.h:346
    #3 0x59f654b22d87 in std::__shared_count<(__gnu_cxx::_Lock_policy)2>::~__shared_count() /usr/include/c++/13/bits/shared_ptr_base.h:1071
    #4 0x59f654b22c5b in std::__shared_ptr<Base, (__gnu_cxx::_Lock_policy)2>::~__shared_ptr() /usr/include/c++/13/bits/shared_ptr_base.h:1524
    #5 0x59f654b22c7b in std::shared_ptr<Base>::~shared_ptr() /usr/include/c++/13/bits/shared_ptr.h:175
    #6 0x59f654b2262c in main vdtor02.cpp:19

0x502000000010 is located 0 bytes inside of 16-byte region [0x502000000010,0x502000000020)
allocated by thread T0 here:
    #0 0x7e96cd8fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x59f654b225f6 in main vdtor02.cpp:17

SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor02.cpp -o exa && ./exa u 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(u) unique_ptr<Base>(new Derived)
      ~Base
=================================================================
==4050482==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x502000000010 in thread T0:
  object passed to delete has wrong type:
  size of the allocated type:   16 bytes;
  size of the deallocated type: 8 bytes.
    #0 0x7429ce6ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x63ef0e4ef3be in std::default_delete<Base>::operator()(Base*) const /usr/include/c++/13/bits/unique_ptr.h:99
    #2 0x63ef0e4eef7e in std::unique_ptr<Base, std::default_delete<Base> >::~unique_ptr() /usr/include/c++/13/bits/unique_ptr.h:404
    #3 0x63ef0e4ee6be in main vdtor02.cpp:22

0x502000000010 is located 0 bytes inside of 16-byte region [0x502000000010,0x502000000020)
allocated by thread T0 here:
    #0 0x7429ce6fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x63ef0e4ee696 in main vdtor02.cpp:21

SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
```

**왜 그런가**

- ★★★ **보장이다** — 기준 소스(cppreference `shared_ptr` 생성자) — 「**`delete ptr` 를 삭제자로 쓴다**」 · 「그 `delete` 가 잘 정의돼야 한다」.\
  `ptr` 가 `Derived*` 이면 **애초에 다형적 삭제가 아니다** — UB 조항에 걸리지 않는다.
- ★★★ **`r` 의 스택 `#1` 이 `std::_Sp_counted_ptr<Base*, …>::_M_dispose()`** 다 — **제어 블록이 기억한 타입이 `Base*`** 라는 증거다.\
  ★ `u` 는 **`std::default_delete<Base>::operator()(Base*)`** 다. **둘 다 `new-delete-type-mismatch`(16 대 8)** — 19편과 같은 수다.
- ★★ **`s` 의 침묵은 경로를 안 밟아서가 아니다** — `~Derived` 로그가 찍혔으니 **지우는 경로를 밟았다.** 삭제가 **올바르기 때문에** 조용하다.\
  ★ 그래서 `s` 의 제어 블록 이름(`_Sp_counted_ptr<Derived*>` 일 것)은 **관찰하지 못했다** — 추론이다.
- ★ `_Sp_counted_ptr` 는 **libstdc++ 13 의 이름**이다(구현 정의). 근거는 「**그 자리에 `Base*` 가 찍혔다**」는 사실이다.
- ★★ **clang 18 + ASan 은 `u` 를 못 본다**(0건) — 기본 해제 함수가 **크기를 안 받는 `_ZdlPv`** 라 견줄 크기가 없다. `-fsized-deallocation` 이면 1건이다.

```text
===== echo "clang 기본 + ASan (u) : $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor02.cpp -o exa 2>&1; ./exa u 2>&1 | grep -cE 'ERROR: AddressSanitizer: new-delete-type-mismatch')건" (exit=0) =====
clang 기본 + ASan (u) : 0건
===== echo "clang -fsized-deallocation + ASan (u) : $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -fsized-deallocation vdtor02.cpp -o exa 2>&1; ./exa u 2>&1 | grep -cE 'ERROR: AddressSanitizer: new-delete-type-mismatch')건" (exit=0) =====
clang -fsized-deallocation + ASan (u) : 1건
===== echo "clang 기본이 부르는 해제 함수 : $(clang++ -std=c++20 -O0 -S -o - vdtor02.cpp | grep -oE 'call[q]?[[:space:]]+_ZdlPv[m]?' | sort -u | tr '\n' ' ')" (exit=0) =====
clang 기본이 부르는 해제 함수 : callq	_ZdlPv 
===== echo "g++ 기본이 부르는 해제 함수   : $(g++ -std=c++20 -O0 -S -o - vdtor02.cpp | grep -oE 'call[q]?[[:space:]]+_ZdlPv[m]?' | sort -u | tr '\n' ' ')" (exit=0) =====
g++ 기본이 부르는 해제 함수   : call	_ZdlPvm 
```

### 3. ★★★ **UB 는 ① ④ ⑤** — ②③은 보장이다

**출력** — 요약 (1)·(6)의 블록이 근거다(①④는 `new-delete-type-mismatch`, ⑤는 g++ `SEGV` · clang 종료 코드 0으로 `~Derived` 0회).

```text
   ① delete (Base*)new Derived;   비가상     ★ UB     — delete 식: 기반 소멸자가 가상이어야 한다
   ② delete (Base*)new Derived;   가상       보장
   ③ shared_ptr<Base>(new Derived) 비가상    보장     — 삭제자가 delete (Derived*)
   ④ unique_ptr<Base>(new Derived) 비가상    ★ UB     — default_delete<Base> 가 ① 과 같은 식
   ⑤ delete[] (Base*)new Derived[3] 가상     ★ UB     — 배열 요소 타입과 비슷해야 한다
```

**왜 그런가**

- ★★★ **③이 보장인 이유와 ④가 UB 인 이유가 같은 문장에서 나온다** — **누가 어떤 타입으로 `delete` 를 쓰나.**
- ★★ **⑤는 가상 소멸자와 무관하다** — 배열 삭제는 **가리키는 타입이 요소 타입과 비슷해야** 하고, `Base` 와 `Derived` 는 **크기부터 다르다**(16 대 24).\
  ★ 원소를 **16바이트씩** 건너가므로 **둘째 원소부터 엉뚱한 자리**를 소멸 대상으로 본다((7)).

### 4. ★★ `V` 의 `noexcept` 칸은 **0**(`V5` 는 1) · `PV` 는 **소멸가능 0 · 이동생 0**

**출력**

```cpp
/* vdtor03.cpp */
// has_virtual_destructor 격자 — 소멸자를 어떻게 선언했나에 따라 무엇이 갈리나
#include <cstdio>
#include <string>
#include <type_traits>

struct NV    { std::string s; ~NV() {} };                        // 비가상 소멸자
struct V     { std::string s; virtual ~V() = default; };         // 가상 소멸자 = default
struct V5    { std::string s; virtual ~V5() = default;           // 가상 소멸자 + 이동을 되살렸다
               V5() = default;
               V5(const V5&) = default;            V5& operator=(const V5&) = default;
               V5(V5&&) noexcept = default;        V5& operator=(V5&&) noexcept = default; };
struct PV    { std::string s; virtual void f() {} protected: ~PV() = default; };  // protected 비가상
struct Fin final { std::string s; virtual void f() {} ~Fin() = default; };        // final + 비가상
struct Zero  { std::string s; };                                 // 아무것도 안 썼다
struct DerV  : V { };                                            // 가상 소멸자를 물려받았다

template <class T> void row(const char* name) {
    std::printf("%-5s |  %d    %d   |  %d    %d   |  %d    %d   |  %2zu\n", name,
        (int)std::has_virtual_destructor_v<T>,
        (int)std::is_polymorphic_v<T>,
        (int)std::is_destructible_v<T>,
        (int)std::is_trivially_destructible_v<T>,
        (int)std::is_move_constructible_v<T>,
        (int)std::is_nothrow_move_constructible_v<T>,
        sizeof(T));
}

int main() {
    std::printf("타입  | 가상소멸 다형 | 소멸가능 trivial | 이동생 noexcept | sizeof\n");
    row<Zero>("Zero"); row<NV>("NV"); row<V>("V"); row<V5>("V5");
    row<PV>("PV"); row<Fin>("Fin"); row<DerV>("DerV");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic vdtor03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입  | 가상소멸 다형 | 소멸가능 trivial | 이동생 noexcept | sizeof
Zero  |  0    0   |  1    0   |  1    1   |  32
NV    |  0    0   |  1    0   |  1    0   |  32
V     |  1    1   |  1    0   |  1    0   |  40
V5    |  1    1   |  1    0   |  1    1   |  40
PV    |  0    1   |  0    0   |  0    0   |  40
Fin   |  0    1   |  1    0   |  1    0   |  40
DerV  |  1    1   |  1    0   |  1    0   |  40
```

**왜 그런가**

- ★★★ **`V` 는 0, `V5` 는 1** — `virtual ~V() = default;` 가 **이동의 암묵 선언을 막았고**, `V5` 는 이동을 **되살렸다**((5)).
- ★★★ **`PV` 의 소멸가능 0** — 소멸자가 `protected` 라 **바깥에서 안 보인다.**\
  ★★ **이동생도 0** — `is_move_constructible` 은 「**`T t(std::move(u));` 변수 정의가 되나**」를 묻고, 그 정의에는 **소멸자 접근이 필요**하다.
- ★ **`DerV` 가상소멸 1**(물려받는다) · **`Fin` 다형 1**(가상 함수 `f` 가 있다 — 소멸자는 비가상이지만 `final` 이라 문제가 없다).
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic vdtor03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
타입  | 가상소멸 다형 | 소멸가능 trivial | 이동생 noexcept | sizeof
Zero  |  0    0   |  1    0   |  1    1   |  32
NV    |  0    0   |  1    0   |  1    0   |  32
V     |  1    1   |  1    0   |  1    0   |  40
V5    |  1    1   |  1    0   |  1    1   |  40
PV    |  0    1   |  0    0   |  0    0   |  40
Fin   |  0    1   |  1    0   |  1    0   |  40
DerV  |  1    1   |  1    0   |  1    0   |  40
```

### 5. ★★★ **`VB` 만 복사로 바뀐다** — `= default` 도 사용자 선언이다

**출력**

```cpp
/* vdtor04.cpp */
// virtual ~B() = default; 한 줄이 이동을 지운다 — 18편의 「소멸자를 쓰면 이동이 사라진다」와 같은 규칙인가
#include <cstdio>
#include <utility>
#include <vector>

struct Tr {                                      // 멤버 — 무엇이 불렸는지 말한다
    Tr() {}
    Tr(const Tr&)          { std::printf("      멤버: 복사\n"); }
    Tr(Tr&&)      noexcept { std::printf("      멤버: 이동\n"); }
    Tr& operator=(const Tr&)          { std::printf("      멤버: 복사 대입\n"); return *this; }
    Tr& operator=(Tr&&)      noexcept { std::printf("      멤버: 이동 대입\n"); return *this; }
    ~Tr() {}
};

struct Zero { Tr t; };                                      // 아무것도 안 썼다
struct VB   { Tr t; virtual ~VB() = default; };             // ★ 가상 소멸자 = default 한 줄
struct VB5  { Tr t; virtual ~VB5() = default;               // 이동을 = default 로 되살렸다
              VB5() = default;
              VB5(const VB5&) = default;         VB5& operator=(const VB5&) = default;
              VB5(VB5&&) noexcept = default;     VB5& operator=(VB5&&) noexcept = default; };

template <class T> void probe(const char* name) {
    std::printf("(%s) std::move 로 만들고 std::move 로 대입한다\n", name);
    { T a; T b = std::move(a); T c; c = std::move(b); }
    std::printf("(%s) vector 재할당 — 자리 둘에 셋째를 넣는다\n", name);
    { std::vector<T> v; v.reserve(2); v.emplace_back(); v.emplace_back(); v.emplace_back(); }
}

int main() {
    probe<Zero>("Zero");
    probe<VB>("VB");
    probe<VB5>("VB5");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic vdtor04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(Zero) std::move 로 만들고 std::move 로 대입한다
      멤버: 이동
      멤버: 이동 대입
(Zero) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 이동
      멤버: 이동
(VB) std::move 로 만들고 std::move 로 대입한다
      멤버: 복사
      멤버: 복사 대입
(VB) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 복사
      멤버: 복사
(VB5) std::move 로 만들고 std::move 로 대입한다
      멤버: 이동
      멤버: 이동 대입
(VB5) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 이동
      멤버: 이동
```

**왜 그런가**

- ★★★ **`VB` 는 만들기·대입·재할당이 전부 복사**다 — [18번](../18-rule-of-zero-three-five-default-delete/) (2)의 `Dtor` 와 **같은 로그**다.
- ★★★ **걸린다** — 규칙이 보는 것은 「**사용자가 소멸자를 선언했나**」이고 **`= default` 도 선언**이다. `virtual` 은 **아무 상관이 없다.**
- ★★ **`VB5` 는 이동으로 돌아온다** — 이동 둘을 `= default` 로 되살렸고, 그러면 **복사가 지워지므로** 복사도 같이 적었다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic vdtor04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(Zero) std::move 로 만들고 std::move 로 대입한다
      멤버: 이동
      멤버: 이동 대입
(Zero) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 이동
      멤버: 이동
(VB) std::move 로 만들고 std::move 로 대입한다
      멤버: 복사
      멤버: 복사 대입
(VB) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 복사
      멤버: 복사
(VB5) std::move 로 만들고 std::move 로 대입한다
      멤버: 이동
      멤버: 이동 대입
(VB5) vector 재할당 — 자리 둘에 셋째를 넣는다
      멤버: 이동
      멤버: 이동
```

### 6. ★★ **2번 줄만 에러**다(경고 1건이 같이 난다) — `unique_ptr<Base>` 면 에러가 **`unique_ptr.h:99`** 로 옮겨 간다

**출력**

```cpp
/* vdtor05.cpp */
// protected 비가상 소멸자 — 「기반 포인터로 지우지 마라」를 타입으로 말한다
struct Base {
    virtual void f() {}
protected:
    ~Base() = default;                  // ★ 비가상이지만 바깥에서 부를 수 없다
};
struct Derived final : Base {
    void f() override {}
};

int main() {
    Derived* d = new Derived;
    Base* b = d;
    delete d;                           // 1. 파생 포인터로 지운다
    Base* b2 = new Derived;
    delete b2;                          // 2. 기반 포인터로 지운다
    Derived local;                      // 3. 지역 객체
    (void)b; (void)local;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 vdtor05.cpp -o ex (cc exit=1) =====
vdtor05.cpp: In function ‘int main()’:
vdtor05.cpp:16:5: warning: deleting object of polymorphic class type ‘Base’ which has non-virtual destructor might cause undefined behavior [-Wdelete-non-virtual-dtor]
   16 |     delete b2;                          // 2. 기반 포인터로 지운다
      |     ^~~~~~~~~
vdtor05.cpp:16:12: error: ‘constexpr Base::~Base()’ is protected within this context
   16 |     delete b2;                          // 2. 기반 포인터로 지운다
      |            ^~
vdtor05.cpp:5:5: note: declared protected here
    5 |     ~Base() = default;                  // ★ 비가상이지만 바깥에서 부를 수 없다
      |     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 vdtor05.cpp -o ex (cc exit=1) =====
vdtor05.cpp:16:5: warning: delete called on non-final 'Base' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
   16 |     delete b2;                          // 2. 기반 포인터로 지운다
      |     ^
vdtor05.cpp:16:12: error: calling a protected destructor of class 'Base'
   16 |     delete b2;                          // 2. 기반 포인터로 지운다
      |            ^
vdtor05.cpp:5:5: note: declared protected here
    5 |     ~Base() = default;                  // ★ 비가상이지만 바깥에서 부를 수 없다
      |     ^
1 warning and 1 error generated.
```

```cpp
/* vdtor06.cpp */
// protected 소멸자를 unique_ptr<Base> 에 맡기면 — 막힌 자리가 표준 라이브러리 안으로 옮겨 간다
#include <memory>
struct Base {
    virtual void f() {}
protected:
    ~Base() = default;
};
struct Derived final : Base { void f() override {} };

int main() {
    std::unique_ptr<Derived> ok = std::make_unique<Derived>();   // 1. 파생 타입으로 맡긴다
    std::unique_ptr<Base> no = std::make_unique<Derived>();      // 2. 기반 타입으로 맡긴다
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 vdtor06.cpp -o ex (cc exit=1) =====
In file included from /usr/include/c++/13/memory:78,
                 from vdtor06.cpp:2:
/usr/include/c++/13/bits/unique_ptr.h: In instantiation of ‘void std::default_delete<_Tp>::operator()(_Tp*) const [with _Tp = Base]’:
/usr/include/c++/13/bits/unique_ptr.h:404:17:   required from ‘std::unique_ptr<_Tp, _Dp>::~unique_ptr() [with _Tp = Base; _Dp = std::default_delete<Base>]’
vdtor06.cpp:12:58:   required from here
/usr/include/c++/13/bits/unique_ptr.h:99:9: error: ‘constexpr Base::~Base()’ is protected within this context
   99 |         delete __ptr;
      |         ^~~~~~~~~~~~
vdtor06.cpp:6:5: note: declared protected here
    6 |     ~Base() = default;
      |     ^
```

**왜 그런가**

- ★★★ **1번(`Derived*` 로 `delete`)과 3번(지역 객체)은 통과한다** — 파생의 소멸자는 기반의 `protected` 소멸자를 **부를 수 있다.**
- ★★ **에러와 함께 `-Wdelete-non-virtual-dtor` 경고가 난다** — 기반이 다형적이고 소멸자가 비가상이기 때문이다. 에러가 이미 막았으니 **중복**이다.
- ★★ **`unique_ptr<Base>` 판은 `default_delete<Base>` 의 `delete __ptr;` 자리**(`unique_ptr.h:99`)에서 막힌다 — 1번의 `unique_ptr<Derived>` 는 통과한다.
- ★ **`final`** — `Derived` 의 소멸자는 **public 비가상**이다. `final` 이 없으면 **`Derived` 의 파생을 `Derived*` 로 지우는** 같은 사고가 한 층 아래에서 난다.

### 7. ★ g++ **`run exit=139`**(`(4)` 없음) · clang **`run exit=0`** — `~Derived` **0회**, `id` 는 **7 · 쓰레기 · 0**

**출력**

```cpp
/* vdtor07.cpp */
// 파생 배열을 기반 포인터로 delete[] 한다 — 소멸자가 가상이어도 되나
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>

struct Base {
    long id = 0;
    virtual ~Base() {                         // id 가 0~99 밖이면 값 대신 그 사실만 찍는다(주소일 수 있다)
        if (id >= 0 && id < 100) std::fprintf(stderr, "      ~Base  id=%ld\n", id);
        else                     std::fprintf(stderr, "      ~Base  id=(0~99 밖의 값)\n");
    }
};
struct Derived : Base {
    long extra = 7;
    ~Derived() override { std::fprintf(stderr, "      ~Derived id=%ld\n", id); }
};

int main() {
    std::fprintf(stderr, "(1) sizeof Base %zu · Derived %zu\n", sizeof(Base), sizeof(Derived));
    std::fprintf(stderr, "(2) Derived[3] 을 Derived* 로 delete[] — 대조군\n");
    { Derived* d = new Derived[3]; for (long i = 0; i < 3; ++i) d[i].id = i; delete[] d; }
    std::fprintf(stderr, "(3) Derived[3] 을 Base* 로 delete[]\n");
    Base* b = new Derived[3];
    delete[] b;
    std::fprintf(stderr, "(4) 여기까지 왔다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic vdtor07.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
(1) sizeof Base 16 · Derived 24
(2) Derived[3] 을 Derived* 로 delete[] — 대조군
      ~Derived id=2
      ~Base  id=2
      ~Derived id=1
      ~Base  id=1
      ~Derived id=0
      ~Base  id=0
(3) Derived[3] 을 Base* 로 delete[]
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic vdtor07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) sizeof Base 16 · Derived 24
(2) Derived[3] 을 Derived* 로 delete[] — 대조군
      ~Derived id=2
      ~Base  id=2
      ~Derived id=1
      ~Base  id=1
      ~Derived id=0
      ~Base  id=0
(3) Derived[3] 을 Base* 로 delete[]
      ~Base  id=7
      ~Base  id=(0~99 밖의 값)
      ~Base  id=0
(4) 여기까지 왔다
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor07.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) sizeof Base 16 · Derived 24
(2) Derived[3] 을 Derived* 로 delete[] — 대조군
      ~Derived id=2
      ~Base  id=2
      ~Derived id=1
      ~Base  id=1
      ~Derived id=0
      ~Base  id=0
(3) Derived[3] 을 Base* 로 delete[]
AddressSanitizer:DEADLYSIGNAL
=================================================================
==4051291==ERROR: AddressSanitizer: SEGV on unknown address 0x000000000000 (pc 0x578734e73611 bp 0x7ffe60b6df50 sp 0x7ffe60b6df10 T0)
==4051291==The signal is caused by a READ memory access.
==4051291==Hint: address points to the zero page.
    #0 0x578734e73611 in main vdtor07.cpp:23

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV vdtor07.cpp:23 in main
```

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor07.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(1) sizeof Base 16 · Derived 24
(2) Derived[3] 을 Derived* 로 delete[] — 대조군
      ~Derived id=2
      ~Base  id=2
      ~Derived id=1
      ~Base  id=1
      ~Derived id=0
      ~Base  id=0
(3) Derived[3] 을 Base* 로 delete[]
      ~Base  id=7
      ~Base  id=(0~99 밖의 값)
      ~Base  id=0
(4) 여기까지 왔다
```

**왜 그런가**

- ★★★ **g++ 는 죽고 clang 은 끝까지 간다** — 어셈블리가 이유를 보인다(요약 (6)).\
  g++ 는 배열 원소의 소멸자를 **가상으로**(`call *%rax`) 부르다 **둘째 원소의 「vptr」 자리에서 0** 을 읽고 죽는다.\
  clang 은 **`~Base` 를 이름으로**(`call _ZN4BaseD2Ev`) 부르므로 안 죽고, **16바이트씩 걸어 `extra`(=7)를 `id` 로** 읽는다.
- ★★★ **ASan 도 갈렸다** — g++ 판 `SEGV`, **clang 판은 침묵**(`run exit=0`). 어긋난 읽기가 **할당 범위 안**이라 ASan 의 과녁 밖이다.
- ★★ **어느 쪽도 「올바른 결과」가 아니다** — UB 다. **「clang 에서는 괜찮았다」가 가장 위험한 근거**다.

```text
===== g++ -std=c++20 -O0 -S -o - vdtor07.cpp | awk '/^main:/,/cfi_endproc/' | grep -E 'call' (exit=0) =====
	call	fprintf@PLT
	call	fwrite@PLT
	call	_Znam@PLT
	call	_ZN7DerivedC1Ev
	call	*%rax
	call	_ZdaPvm@PLT
	call	fwrite@PLT
	call	_Znam@PLT
	call	_ZN7DerivedC1Ev
	call	*%rax
	call	_ZdaPvm@PLT
	call	fwrite@PLT
===== clang++ -std=c++20 -O0 -S -o - vdtor07.cpp | awk '/^main:/,/cfi_endproc/' | grep -E 'call' (exit=0) =====
	callq	fprintf@PLT
	callq	fprintf@PLT
	callq	_Znam@PLT
	callq	_ZN7DerivedC2Ev
	callq	_ZN7DerivedD2Ev
	callq	_ZdaPv@PLT
	callq	fprintf@PLT
	callq	_Znam@PLT
	callq	_ZN7DerivedC2Ev
	callq	_ZN4BaseD2Ev
	callq	_ZdaPv@PLT
	callq	fprintf@PLT
```

### 8. ★ **`Base` 16 · `Derived` 24 · `Base` 의 것인데 48** — 지역 객체는 **안 부른다**

**출력**

```cpp
/* vdtor08.cpp */
// delete p 가 부르는 operator delete 는 누구의 것인가 — 클래스마다 operator delete 를 두고 로그를 찍는다
#include <cstdio>
#include <cstdlib>
#include <new>

struct Base {
    long a = 0;
    virtual ~Base() {}
    static void* operator new(std::size_t n) { std::printf("      Base::operator new    %zu\n", n); return std::malloc(n); }
    static void  operator delete(void* p, std::size_t n) { std::printf("      Base::operator delete %zu\n", n); std::free(p); }
};
struct Derived : Base {                           // 자기 operator delete 를 둔다
    long b = 0;
    static void* operator new(std::size_t n) { std::printf("      Derived::operator new    %zu\n", n); return std::malloc(n); }
    static void  operator delete(void* p, std::size_t n) { std::printf("      Derived::operator delete %zu\n", n); std::free(p); }
};
struct Plain : Base {                             // 자기 것이 없다 — Base 의 것을 물려받는다
    long c[4] = {};
};

int main() {
    std::printf("(1) Base* p = new Base;    delete p;\n");
    { Base* p = new Base;    delete p; }
    std::printf("(2) Base* p = new Derived; delete p;\n");
    { Base* p = new Derived; delete p; }
    std::printf("(3) Base* p = new Plain;   delete p;\n");
    { Base* p = new Plain;   delete p; }
    std::printf("(4) 지역 객체 Derived d; — operator delete 가 불리나\n");
    { Derived d; }
    std::printf("(5) sizeof Base %zu · Derived %zu · Plain %zu\n", sizeof(Base), sizeof(Derived), sizeof(Plain));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic vdtor08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) Base* p = new Base;    delete p;
      Base::operator new    16
      Base::operator delete 16
(2) Base* p = new Derived; delete p;
      Derived::operator new    24
      Derived::operator delete 24
(3) Base* p = new Plain;   delete p;
      Base::operator new    48
      Base::operator delete 48
(4) 지역 객체 Derived d; — operator delete 가 불리나
(5) sizeof Base 16 · Derived 24 · Plain 48
```

**왜 그런가**

- ★★★ **`(2)` 는 `Derived::operator delete 24`** — 포인터는 `Base*` 인데 해제 함수는 **동적 타입의 범위에서 찾는다**(기준 소스).
- ★★★ **`(3)` 은 함수는 `Base` 의 것, 크기는 `Plain` 의 것(48)** 이다 — **같은 클래스의 것이 아니다.**\
  ★ 크기를 넘기는 쪽이 **`Plain` 의 삭제 소멸자(`D0`)** 이기 때문이다. 이름 찾기는 `Plain` 에서 시작해 **`Base` 까지 올라가 찾았다.**
- ★★ **`(4)` 는 아무것도 안 찍힌다** — 지역 객체는 **소멸만** 하고 **해제는 안 한다.** 그래서 소멸자가 **두 벌**(완전 · 삭제) 필요하다.

```text
===== g++ -std=c++20 -O0 -S -o - vdtor08.cpp | grep -E '^\s+\.set\s+_ZN7DerivedD1Ev' (exit=0) =====
	.set	_ZN7DerivedD1Ev,_ZN7DerivedD2Ev
===== g++ -std=c++20 -O0 -S -o - vdtor08.cpp | awk '/^_ZN7DerivedD[0-2]Ev:/,/cfi_endproc/' | grep -E '^_Z|call' (exit=0) =====
_ZN7DerivedD2Ev:
	call	_ZN4BaseD2Ev
_ZN7DerivedD0Ev:
	call	_ZN7DerivedD1Ev
	call	_ZN7DeriveddlEPvm
===== clang++ -std=c++20 -O0 -S -o - vdtor08.cpp | awk '/^_ZN7DerivedD[0-2]Ev:/,/cfi_endproc/' | grep -E '^_Z|call' (exit=0) =====
_ZN7DerivedD2Ev:                        # @_ZN7DerivedD2Ev
	callq	_ZN4BaseD2Ev
_ZN7DerivedD0Ev:                        # @_ZN7DerivedD0Ev
	callq	_ZN7DerivedD2Ev
	callq	_ZN7DeriveddlEPvm
```

- ★★★ **`D0`(삭제 소멸자)의 본체가 「소멸자 호출 + `Derived::operator delete`」 두 줄**이다 — 19편 vtable 의 `[deleting]` 칸이 이것이다.

### 9. ★ **링크 에러**다 — 소멸자는 **파생이 덮어도 기반 것이 불린다**

**출력**

```cpp
/* vdtor09.cpp */
// 순수 가상 소멸자 — 파생이 덮어도 기반의 정의가 따로 필요한가
#include <cstdio>

struct Base {
    virtual ~Base() = 0;                // 순수 가상 소멸자 — Base 를 추상으로 만든다
};
#ifdef DEF
Base::~Base() { std::printf("      ~Base (순수 가상인데 본체가 있다)\n"); }
#endif
struct Derived : Base {
    ~Derived() override { std::printf("      ~Derived\n"); }
};

int main() {
    Base* p = new Derived;
    delete p;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c vdtor09.cpp -o vdtor09.o && g++ vdtor09.o -o ex (cc exit=1) =====
/usr/bin/ld: vdtor09.o: in function `Derived::~Derived()':
vdtor09.cpp:(.text._ZN7DerivedD2Ev[_ZN7DerivedD5Ev]+0x35): undefined reference to `Base::~Base()'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c vdtor09.cpp -o vdtor09.o && clang++ vdtor09.o -o ex (cc exit=1) =====
/usr/bin/ld: vdtor09.o: in function `Derived::~Derived()':
vdtor09.cpp:(.text._ZN7DerivedD2Ev[_ZN7DerivedD2Ev]+0x36): undefined reference to `Base::~Base()'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DDEF vdtor09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      ~Derived
      ~Base (순수 가상인데 본체가 있다)
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DDEF vdtor09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
      ~Derived
      ~Base (순수 가상인데 본체가 있다)
```

**왜 그런가**

- ★★★ **컴파일은 되고 링크가 실패한다** — `undefined reference to 'Base::~Base()'` 가 **`Derived::~Derived()` 안에서** 났다.
- ★★ **소멸자는 특별하다** — 파생 소멸자는 **끝에서 반드시 기반 소멸자를 부른다.** `f() = 0` 은 파생이 덮으면 **기반 것이 안 불리니** 정의가 없어도 된다.\
  ★ 기준 소스 — 「순수 가상 함수의 정의는 줄 수 있고, **소멸자라면 반드시 줘야 한다**」(CWG 390).
- ★ **한 줄에 쓰면 문법 에러**다 — g++ `pure-specifier on function-definition` 1건 · clang 은 4건으로 번진다(요약 (8)).

### 10. ★★ **g++ 1 · clang 2** — 갈린 것은 **`unique_ptr<Poly>`**(탐침 6)

**출력**

```cpp
/* vdtor10.cpp */
// 다형적 삭제에서 틀리는 자리 일곱을 심었다 — 컴파일러가 몇 군데에서 말하는지 센다
#include <memory>
#include <utility>

struct Poly    { virtual void f() {} ~Poly() {} };               // 가상 함수가 있는데 소멸자는 비가상
struct PolyDer : Poly { long x = 0; };

struct Leaf final { virtual void f() {} ~Leaf() {} };            // final — 파생이 없다

struct Guard   { virtual void f() {} protected: ~Guard() {} };   // protected 비가상
struct GuardDer final : Guard { };

struct VB      { virtual ~VB() {} long id = 0; };                // 소멸자는 가상이다
struct VD      : VB { long extra = 0; };

struct Plain   { ~Plain() {} };                                  // 가상 함수가 하나도 없다
struct PlainDer : Plain { long x = 0; };

int main() {
    Poly* a = new PolyDer; delete a;                             // 1. 다형 기반으로 지운다(대조군)
    Leaf* b = new Leaf;    delete b;                             // 2. final 클래스를 자기 포인터로 지운다
    GuardDer* c = new GuardDer; delete c;                        // 3. protected 기반 — 파생으로 지운다
    VB* d = new VD[2];     delete[] d;                           // 4. 파생 배열을 기반 포인터로 delete[]
    Plain* raw = new PlainDer;
    std::shared_ptr<Plain> e(raw);                               // 5. raw 를 거쳐 shared_ptr 에 맡긴다
    std::unique_ptr<Poly> f(new PolyDer);                        // 6. 다형 기반을 unique_ptr 에 맡긴다
    VB v1; VB v2 = std::move(v1); (void)v2;                      // 7. 가상 소멸자가 이동을 지웠다
}
```

```text
===== echo "vdtor10 탐침 일곱  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c vdtor10.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
vdtor10 탐침 일곱  g++ 경고 1
===== echo "vdtor10 탐침 일곱  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c vdtor10.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
vdtor10 탐침 일곱  clang 경고 2
===== echo "vdtor10 탐침 일곱  g++ -Wnon-virtual-dtor 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -Wnon-virtual-dtor -c vdtor10.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
vdtor10 탐침 일곱  g++ -Wnon-virtual-dtor 경고 4
===== echo "vdtor10 탐침 일곱  clang -Wnon-virtual-dtor 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -Wnon-virtual-dtor -c vdtor10.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
vdtor10 탐침 일곱  clang -Wnon-virtual-dtor 경고 4
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c vdtor10.cpp -o /dev/null (cc exit=0) =====
vdtor10.cpp:20:28: warning: delete called on non-final 'Poly' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
   20 |     Poly* a = new PolyDer; delete a;                             // 1. 다형 기반으로 지운다(대조군)
      |                            ^
In file included from vdtor10.cpp:2:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/memory:78:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:99:2: warning: delete called on non-final 'Poly' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
   99 |         delete __ptr;
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:404:4: note: in instantiation of member function 'std::default_delete<Poly>::operator()' requested here
  404 |           get_deleter()(std::move(__ptr));
      |           ^
vdtor10.cpp:26:27: note: in instantiation of member function 'std::unique_ptr<Poly>::~unique_ptr' requested here
   26 |     std::unique_ptr<Poly> f(new PolyDer);                        // 6. 다형 기반을 unique_ptr 에 맡긴다
      |                           ^
2 warnings generated.
```

**왜 그런가**

- ★★ **두 컴파일러 다 탐침 1(다형 기반 `delete`)에 답한다** — 19편 (8)의 조건 그대로다.
- ★★★ **탐침 6에서 갈린다** — clang 은 **`unique_ptr.h:99` 의 `delete __ptr;`** 에 경고를 달고 **사슬을 거슬러 26번 줄**을 짚는다.\
  g++ 는 **0건**이다 — 그 경고가 **시스템 헤더 안에서** 나야 하는데 g++ 는 거기서 **보여 주지 않았다**(관찰 — 원인은 추론).\
  ★ **그래서 g++ 에서는 「`unique_ptr` 로 감쌌더니 경고가 사라졌다」가 실제로 일어난다.**
- ★★ **`-Wnon-virtual-dtor` 는 답한 탐침 수를 안 늘린다** — 경고 줄은 4 로 늘지만 **전부 1번 탐침(`Poly`)의 선언 자리**다.
- ★★★ **탐침 4(배열)·5(raw 를 거친 `shared_ptr`)·7(이동)은 어떤 플래그로도 0건**이다.

### 11. ★★★ **「물려받나 · 기반 포인터로 지우나 · 파생을 막나」** 셋이다

**출력** — 요약 (10)의 판단표.

```text
   물려받을 사람이 없다                ->  final                    (소멸자 비가상 그대로)
   기반 포인터로 지운다                ->  public virtual ~Base()   (+ 이동이 필요하면 다섯을 다 적는다)
   물려받지만 기반 포인터로는 안 지운다 ->  protected 비가상 ~Base()
```

**왜 그런가**

- ★★★ **어느 것도 안 고르면 `public` 비가상이 남는다** — 그 조합만이 **UB 를 조용히 허락**한다.
- ★★ **어림규칙이 빠뜨리는 자리** — **가상 함수가 0개인 기반**이다. 19편 (8)이 보였듯 그런 기반도 다형적으로 지울 수 있고 **경고는 0건**이다.\
  ★ 그래서 기준은 「가상 함수가 있나」가 아니라 「**기반 포인터로 지울 일이 있나**」다.
- ★ **`shared_ptr` 를 근거로 삼으면 안 되는 이유** — (1)의 `(3)` 처럼 **`Base*` 를 한 번만 거쳐도 UB** 이고, **경고도 0건**이다((10)의 탐침 5).\
  ★ 게다가 그 기반을 **누가 `unique_ptr<Base>` 로 쓸지** 막을 수 없다.

### 12. ★★ **미명시** · 19편은 **vtable 덤프**, 이 편은 **어셈블리 + 해제 함수 로그** · **18번** · **15번**

**왜 그런가**

- ★★ **`delete[]` 의 소멸자를 가상으로 부를지(g++) 직접 부를지(clang)는 미명시**다 — 정적/동적 타입이 같은 **올바른 프로그램에서는 결과가 같기** 때문이다.\
  ★ 둘이 다른 증상을 낸 것은 **UB 인 프로그램에서만**이다.
- ★★ **19편 (11)은 `-fdump-lang-class`·`-fdump-vtable-layouts` 로 두 칸을 찍었다.** 이 편 (7)은 **같은 질문을 `-O0` 어셈블리(`D0` 의 본체)와 클래스별 `operator delete` 로그**로 다시 물었다 — **제5의 상태**(창을 바꿔 답한 것)다.
- ★ **이동이 사라지는 규칙의 정본은 [18번](../18-rule-of-zero-three-five-default-delete/)** 이다.
- ★ **[15번](../15-raii-resources-as-types/) (5)** 가 `unique_ptr` 에 함수 포인터 삭제자를 달면 **16바이트**가 되는 것을 먼저 찍었다 — **삭제자를 기억할 자리**의 대가다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `vdtor01.cpp` 다섯 가지로 맡기기 | g++ · clang 각 1회 | ★★★ `shared_ptr` 둘만 `~Derived` · `(3)` 은 `~Base` 만 · `sizeof` **16 · 8** · 두 컴파일러 동일 |
| `vdtor02.cpp` ASan | g++ + ASan 3회(`s`·`r`·`u`) · clang + ASan 3회(`u` 기본 2 · `-fsized-deallocation` 1) | ★★★ `s` 침묵 · `r`·`u` **`new-delete-type-mismatch`** · `r` 스택에 **`_Sp_counted_ptr<Base*>`** · ★★ **clang 기본은 `u` 에 0건** |
| `vdtor03.cpp` 격자 | g++ · clang 각 1회 | ★★ `V` 의 `noexcept` 이동 **0** · `PV` **소멸가능 0 · 이동생 0** |
| `vdtor04.cpp` 이동이 사라짐 | g++ · clang 각 1회 | ★★★ `VB` 만 **복사** · `VB5` 는 이동으로 돌아옴 |
| `vdtor05.cpp`·`vdtor06.cpp` `protected` | g++ · clang 각 1회 | ★★ **2번 줄만 에러** · `unique_ptr` 판은 **`unique_ptr.h:99`** |
| `vdtor07.cpp` 배열 `delete[]` | g++ · clang 각 1회 + ASan 각 1회 | ★★★ g++ **139** · clang **0**(`id=7`) · ASan g++ `SEGV` · **clang 침묵** · 어셈블리 `call *%rax` 대 `call _ZN4BaseD2Ev` |
| `vdtor08.cpp` 해제 함수 | g++ · clang 각 1회 + 어셈블리 | ★★★ **16 · 24 · 48** · `D0` = 소멸 + `Derived::operator delete` |
| `vdtor09.cpp`·`vdtor12.cpp` 순수 가상 소멸자 | g++ · clang 각 2회 | ★★ **링크 에러** · `-DDEF` 로 돈다 · 한 줄 형태는 **문법 에러**(1건 대 4건) |
| `vdtor10.cpp` 탐침 일곱 | g++ · clang 각 2회(기본 · `-Wnon-virtual-dtor`) | ★★★ 답한 탐침 **g++ 1 · clang 2** · 탐침 4·5·7 **0건** |
| `vdtor11.cpp` 형태 | g++ 1회(`-Wnon-virtual-dtor`) | 경고 0건 · `has_virtual_destructor` **1 · 0 · 0** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · Itanium C++ ABI · ASan)에서만** 그렇다.

- ★★★ **ASan 스택의 `_Sp_counted_ptr<Base*>`·`default_delete<Base>` 이름과 헤더 줄 번호.**
- ★★ **`sizeof(shared_ptr<Base>)` 16 · `unique_ptr<Base>` 8** · vptr 8바이트.
- ★★ **`D0`/`D1`/`D2` 이름과 g++ 의 `.set` 별칭** · **`_ZdaPvm` 대 `_ZdaPv`.**
- ★★ **탐침 6에서 g++ 가 헤더 안 경고를 안 보이는 것** · 진단 문구 전부.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **`shared_ptr(Y*)` 가 `delete ptr`(Y*)로 지우는 것** — 그래서 `new Derived` 를 **바로** 넘기면 `~Derived` 가 도는 것.
- ★★★ **기반 소멸자가 비가상이면 다형적 `delete` 가 UB 인 것** · **배열 `delete[]` 는 요소 타입이 달라지면 UB 인 것.**
- ★★ **해제 함수를 동적 타입의 범위에서 찾는 것** · **`protected` 소멸자 접근 규칙** · **순수 가상 소멸자에 정의가 필요한 것.**
- ★★★ **사용자 선언 소멸자(`= default` 포함)가 이동의 암묵 선언을 막는 것.**

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ **1번의 `(3)`·`(4)`·`(5)`, 7번 전부.** 근거로 쓰는 것은 「**`~Derived` 가 안 불렸다**」·「ASan 이 무엇이라 불렀나」·「**g++ 139 · clang 0**」이라는 관찰뿐이다.\
  ★ 「clang 에서는 `id=7` 이 찍힌다」를 성질로 읽으면 안 된다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **clang + ASan 으로 `vdtor02` 의 `s`·`r`**(`u` 만 던졌다) · ★ **`std::destroying_delete_t`** · ★ **가상 상속 판**(`D1`·`D2` 가 갈리는 자리) · ★ **`-std=c++98` 판.**
- ★ **「부적용인 창」** — `-O2` 어셈블리 세기. 이 주제에는 잴 비용이 없다. **「안 쟀다」가 아니라 「여기서 잴 것이 아니다」다.**
- ★ **「인용한 창」** — vtable 덤프. [19번](../19-inheritance-virtual-functions-override-final/) (11)이 찍었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **10번의 탐침 6** — g++ 가 헤더 안 경고를 보이기 시작하면 「감싸면 사라진다」가 바뀐다.
- ★★ **7번의 두 컴파일러 선택**(`call *%rax` 대 `call _ZN4BaseD2Ev`) — 미명시라 **판이 바뀌면 뒤집힐 수 있다.**
- ★ **libstdc++ 판이 바뀌면 2번의 스택 이름·줄 번호.**
