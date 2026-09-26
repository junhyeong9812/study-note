# cpp/syntax/20 — 가상 소멸자와 다형적 삭제 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `delete` 식](https://en.cppreference.com/w/cpp/language/delete) · [cppreference — `shared_ptr` 생성자](https://en.cppreference.com/w/cpp/memory/shared_ptr/shared_ptr) · [cppreference — 추상 클래스](https://en.cppreference.com/w/cpp/language/abstract_class) · [cppreference — `<type_traits>`](https://en.cppreference.com/w/cpp/header/type_traits) · [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)\
> ★ cppreference 세 쪽은 2026-09-26 에 열어 **해당 문장을 확인했다**(`delete` 식의 「기반 소멸자가 가상이어야 한다」·「배열은 요소 타입이 비슷해야 한다」·「해제 함수는 동적 타입의 범위에서 찾는다」, `shared_ptr` 의 「`delete ptr` 를 삭제자로 쓴다」, 추상 클래스의 「순수 가상 소멸자는 정의가 반드시 있어야 한다」).
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`vdtor01.cpp` \~ `vdtor11.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **ASan 을 붙인 블록은 마커를 `stderr` 로 찍었다.** sanitizer 가 `abort()` 로 죽이면\
> **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다((1)·(6)의 소스에 그렇게 적혀 있다).\
> ★★ **리포트를 자른 블록은 자르는 명령을 배너에 적었다** — 실린 것이 「생략한 일부」가 아니라 「**그 명령의 전체 출력**」이다.
> **버전** — 가상 소멸자·`protected` 소멸자·순수 가상 소멸자는 **C++98부터**. `shared_ptr`·`unique_ptr`·`final`·`= default` 는 **C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **[19번](../19-inheritance-virtual-functions-override-final/)이 이 주제의 핵심을 이미 쟀다 — 다시 재지 않고 인용한다.**\
> 그 편 (8)(11)(12)가 실측한 것 — **`~DerNV` 0회 · 128바이트가 샌다** · ASan **`new-delete-type-mismatch`(16 대 8)** ·\
> `sizeof` **BaseNV 8 · DerNV 16 · BaseV 16 · DerV 24** · **경고의 스위치는 「기반이 다형적인가」** · vtable 의 **`[complete]`/`[deleting]` 두 칸**.\
> ★★ **여기서 새로 묻는 것은 둘이다** — 「**무엇이 미정의인가**」의 층 분류와 「**언제 가상으로 둘까**」의 판단 규칙.
> **경계** — 「소멸자가 언제 도나」는 [14번](../14-destructors-and-deterministic-destruction/)이, 「가상 디스패치 규칙」은 [19번](../19-inheritance-virtual-functions-override-final/)이,\
> 「이동이 왜 사라지나」는 [18번](../18-rule-of-zero-three-five-default-delete/)이 정본이다. 「`shared_ptr` 의 제어 블록」은 목록의 **27번 주제**, 「추상 클래스와 vtable 비용」은 [21번](../21-abstract-classes-pure-virtual-and-vtable-cost/)이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소 | ★★★ **어느 소멸자가 몇 번 불렸나**(호출 로그) — 이 주제의 답 자체다 |
> | 두 컴파일러의 **진단 문구** | ★★★ **`<type_traits>` 격자의 0/1** · **`sizeof`** |
> | UB 인 실행의 **결과 그 자체**(죽나 · 쓰레기 값이 무엇인가) | ★★ **`cc exit`/`run exit`** · **경고·에러 개수** · **진단의 `(행,열)`** |
> | — | ★★ **어셈블리에서 무엇을 `call` 하나**(이름 · 간접 호출 여부) |
>
> ★ **(6)의 clang 판은 쓰레기 값을 읽는다** — 주소일 수 있어 **값 대신 「0\~99 밖의 값」이라는 사실만** 찍게 했다(소스 주석).\
> **흔들리는 것을 지운 게 아니라 안 흔들리는 형식으로 바꾼 것**이다.

## 한눈에 — 쉽게 말하면

**가상 소멸자는 「반납 창구가 짐을 열어 보고 처리하는 것」이다.**

보관소에 이삿짐을 맡긴다. 겉 상자에는 「**일반 짐**」이라고 적혀 있지만 안에는 **냉장칸**이 하나 더 있다.

- **반납 창구가 겉 라벨만 보고 처리하면**(비가상 소멸자) — 일반 짐 절차만 밟고, **냉장칸은 아무도 비우지 않는다.**
- **창구가 상자를 열어 진짜 내용물을 확인하면**(가상 소멸자) — 냉장칸부터 비우고 겉 상자를 치운다.
- ★ **맡길 때 받은 보관증에 「냉장칸 있음」이 적혀 있으면**(`shared_ptr`) — 창구가 라벨을 안 봐도 **보관증대로** 처리한다.\
  ★★ 단 **보관증은 「맡긴 순간」에 쓴다.** 이미 「일반 짐」 라벨만 붙은 상태로 맡기면 **보관증에도 「일반 짐」이 적힌다.**

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 겉 라벨 | ★★★ **정적 타입**(`Base*`) | (1) |
| 안의 냉장칸 | ★★★ **파생이 따로 든 자원** — `~Derived` 만 놓을 수 있다 | (1) |
| 라벨만 보고 처리한다 | ★★★ **비가상 소멸자로 `delete`** — **UB** 다 | (1)(2) |
| 상자를 열어 본다 | ★★★ **가상 소멸자** | (3) |
| 맡길 때 쓴 보관증 | ★★★ **`shared_ptr` 의 타입 소거된 삭제자** | (1) |
| 「일반 짐」 라벨로 맡겼다 | ★★ **`Base*` 로 먼저 받은 뒤 `shared_ptr` 에 넘김** | (1) |
| 「이 창구에서는 반납 안 받습니다」 | ★★ **`protected` 비가상 소멸자** | (5) |
| 「이 상자는 더 안 쪼갭니다」 | ★ **`final`** | (5)(10) |

> **다형적 삭제(polymorphic deletion)** — **기반 포인터로 파생 객체를 `delete` 하는 것**.\
> 예: (1)의 `(4)` 에서 `unique_ptr<Base>` 가 `Derived` 를 들고 있다가 지웠다.

> **타입 소거(type erasure)** — **구체 타입을 기억하되 바깥 타입에는 드러내지 않는 기법**.\
> 예: `shared_ptr<Base>` 라는 **같은 타입**이 속으로는 「`Derived*` 를 지워라」를 들고 있다((1)의 ASan 스택이 그 이름을 보인다).

```text
   Base* 로 들고 있는 Derived 를 지운다

                 무엇이 ~Derived 를 부르나            결과
   delete p      p 의 정적 타입(Base)의 소멸자        ~Base 만   ★ UB
                 -> 가상이면 동적 타입으로 간다        ~Derived + ~Base
   shared_ptr    ★ 만들 때 받은 포인터의 타입         ~Derived + ~Base   (가상이 아니어도)
   unique_ptr    default_delete<Base> -> delete p     ~Base 만   ★ UB
```

- ★★★ **이 그림의 셋째 줄이 이 편의 새 재료다.** 「가상 소멸자가 없으면 무조건 샌다」가 아니다 —\
  **누가 `delete` 식을 쓰느냐, 그때 어떤 타입을 들고 있느냐**가 답을 정한다.

## 이 주제가 답하려는 질문

1. **기반 포인터로 지울 때 무엇이 미정의이고 무엇이 보장되나** — 그 선을 **표준 문장과 실행으로** 긋는다((1)(2)(6)).
2. **왜 `shared_ptr<Base>` 는 가상 소멸자 없이도 맞게 지우고 `unique_ptr<Base>` 는 못 하나**((1)).
3. **가상 소멸자 한 줄이 무엇을 바꾸나** — 격자·이동·`delete` 가 부르는 해제 함수까지((3)(4)(7)).
4. **언제 가상으로 두고, 언제 `protected` 로 막고, 언제 `final` 로 끊나**((5)(10)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 호출 로그다

★★★ **이 주제의 본체는 ① 호출 로그다** — **`shared_ptr` 대 `unique_ptr` 에 같은 객체를 맡기고 어느 소멸자가 도는지** 찍는다.\
★★ **짝이 ⑥ `<type_traits>` 격자**다 — [18번](../18-rule-of-zero-three-five-default-delete/)의 형식으로 `has_virtual_destructor` 를 찍는다.

```text
① 호출 로그             어느 소멸자·어느 operator delete 가 몇 번 불렸나      (1)(4)(6)(7)(8)
② 두 컴파일러 대조       protected 소멸자 · 순수 가상 소멸자의 진단 전문        (5)(8)
③ ASan 리포트            shared_ptr 대 unique_ptr · 파생 배열 delete[]          (1)(6)
④ 어셈블리(-O0)          delete[] 가 무엇을 call 하나 · 삭제 소멸자의 본체       (6)(7)
⑤ 경고 격자              탐침 일곱 중 몇이 답하나                               (9)
⑥ <type_traits> 격자     has_virtual_destructor · 이동 · 소멸 가능              (3)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 호출 로그** | ★★★ **본체** — (1)이 다섯 가지 맡기는 법을 **한 블록에 나란히** 찍는다 | **쓴다** |
| ② 두 컴파일러 대조 | `protected` 소멸자 · 순수 가상 소멸자의 링크 에러 | **쓴다** |
| ③ ASan 리포트 | ★★ **스택 프레임에 `_Sp_counted_ptr<Base*>` 가 찍힌다** — 삭제자가 기억한 타입이 보인다 | **쓴다** |
| ④ 어셈블리 | ★ **`-O0` 로만** 쓴다 — 「무엇을 `call` 하나」를 보는 것이지 비용이 아니다 | **쓴다(-O0)** |
| ⑤ 경고 격자 | 탐침 일곱 중 **g++ 1 · clang 2** | **쓴다** |
| ★★ **⑥ `<type_traits>` 격자** | ★★ **짝** — `has_virtual_destructor` · `is_destructible` · 이동 | **쓴다** |
| vtable 덤프 | ★ **인용** — [19번](../19-inheritance-virtual-functions-override-final/) (11)이 찍었다(`[complete]`/`[deleting]`) | **다시 안 찍는다** |
| `-O2` 어셈블리 세기 | ★ **부적용** — 이 주제에는 **잴 비용이 없다**. 비용의 정본은 [21번](../21-abstract-classes-pure-virtual-and-vtable-cost/) | **안 쓴다** |

- ★★★ **「vtable 덤프」를 다시 안 찍은 것은 「안 쟀다」가 아니다** — 19편이 이미 **두 도구로** 찍었다.\
  ★★ 대신 (7)은 「**`[deleting]` 칸이 왜 따로 있나**」라는 **같은 질문을 다른 창**(`-O0` 어셈블리 + 클래스별 `operator delete` 로그)으로 물었다.\
  ★ 이것이 **제5의 상태**다 — 「못 잰 것」도 「부적용」도 아니라 **창을 바꿔 답한 것**이다.\
  바꾼 창이 못 보는 것 — **vtable 의 몇 번째 칸인지**는 어셈블리만으로 안 보인다(그건 19편의 덤프가 말한다).
- ★★★ **`-O2` 세기는 부적용이다** — 이 주제의 질문은 「**무엇이 불리나**」이지 「얼마나 드나」가 아니다.

### (1) ★★★ `shared_ptr` 대 `unique_ptr` — 같은 파생 객체를 맡긴다

**언제 쓰나** — 「가상 소멸자가 없는 기반인데 스마트 포인터에 담았으니 괜찮겠지?」를 점검할 때마다. **이 절이 이 주제의 중심이다.**

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

```text
   맡긴 방법                                  삭제자가 기억한 타입     불린 소멸자
   (1) shared_ptr<Base>(new Derived)           Derived*                 ~Derived  ~Base
   (2) shared_ptr<Base> = make_shared<Derived>  Derived                  ~Derived  ~Base
   (3) Base* raw = new Derived; …(raw)          ★ Base*                  ~Base 만        ★ UB
   (4) unique_ptr<Base>(new Derived)            Base (default_delete)    ~Base 만        ★ UB
   (5) unique_ptr<Derived> -> unique_ptr<Base>  Base (default_delete)    ~Base 만        ★ UB

   ★ 갈리는 것은 스마트 포인터의 「종류」가 아니라 「그 순간 손에 든 포인터의 타입」이다
```

- ★★★ **`(1)` 은 가상 소멸자가 없는데도 `~Derived` 가 돈다.** `Base` 의 소멸자는 **비가상**이다.
- ★★★ **이유는 삭제자다** — `shared_ptr` 의 `Y*` 생성자는 **`delete ptr` 를 삭제자로 쓴다**(기준 소스).\
  이때 `ptr` 는 **`Y*` = `Derived*`** 다. 그래서 **`delete (Derived*)` 가 불린다** — 가상일 필요가 없다.\
  ★ 그 삭제자가 **제어 블록 안에 숨어 있다** — `shared_ptr<Base>` 라는 타입에는 흔적이 없다. **타입 소거**다.
- ★★ **`(2)` 도 같다** — `make_shared<Derived>` 가 **`Derived` 를 아는 제어 블록**을 만들고, 그 뒤에 `shared_ptr<Base>` 로 변환된다.
- ★★★ **`(3)` 이 함정이다.** 같은 `shared_ptr<Base>` 인데 **`~Derived` 가 안 돈다.**\
  ★ `raw` 가 **이미 `Base*`** 였으므로 `Y` = `Base` 가 되고, 삭제자는 **`delete (Base*)`** 를 기억한다.\
  ★★★ **「`shared_ptr` 는 안전하다」가 아니라 「`shared_ptr` 는 만들 때 받은 포인터의 타입을 기억한다」가 규칙이다.**
- ★★★ **`(4)`·`(5)` 는 `~Base` 만** — `unique_ptr<Base>` 의 삭제자는 **`default_delete<Base>`** 이고, 그것은 **`delete (Base*)`** 다.\
  ★ `(5)` 는 `make_unique<Derived>` 로 만들었는데도 그렇다 — **옮기는 순간 삭제자가 `default_delete<Base>` 로 바뀐다.**
- ★★ **`(6)` 이 대가다** — `shared_ptr<Base>` **16** · `unique_ptr<Base>` **8**. **제어 블록을 가리키는 포인터**가 하나 더 있다.\
  ★ [15번](../15-raii-resources-as-types/) (5)가 같은 모양을 찍었다 — **`unique_ptr` 에 함수 포인터 삭제자를 달면 16** 이 된다.\
  ★★ **삭제자를 「기억」하려면 어딘가에 자리가 필요하다** — `unique_ptr` 는 **타입에**(템플릿 인자), `shared_ptr` 는 **제어 블록에** 둔다.
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

★★★ **ASan 에게 셋을 따로 물었다** — `s`(= `(1)`) · `r`(= `(3)`) · `u`(= `(4)`).

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

- ★★★ **`s` 는 ASan 이 침묵하고 `run exit=0`** 이다. **이 경로를 밟았는데도 침묵했다** — 탐침을 심기만 한 것이 아니다(`~Derived` 로그가 그 증거).
- ★★★ **`r` 과 `u` 는 `new-delete-type-mismatch`** 다 — **16바이트로 잡은 것을 8바이트로 놓았다.**\
  ★ 19편 (8)과 **같은 이름·같은 수**다. 스마트 포인터가 사고를 **막지도, 바꾸지도 않았다.**
- ★★★ **스택 프레임이 삭제자의 정체를 보여 준다.**\
  `r` — **`std::_Sp_counted_ptr<Base*, …>::_M_dispose()`** · `u` — **`std::default_delete<Base>::operator()(Base*)`**.\
  ★★ **`_Sp_counted_ptr<Base*>` 의 `Base*` 가 곧 「보관증에 적힌 타입」이다**. `s` 였다면 그 자리가 `Derived*` 였을 것이다 —\
  ★ 다만 **`s` 는 오류가 없어 스택이 안 찍힌다.** 그 자리의 이름은 **관찰하지 못했다**(추론이다).
- ★ 프레임의 `shared_ptr_base.h:428` 같은 줄 번호는 **libstdc++ 13 의 것**이다 — **구현 관찰**이지 표준이 아니다.

★★★ **같은 `u` 를 clang + ASan 으로 던지면 — 침묵한다.**

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. vdtor02.cpp -o exa && ./exa u 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(u) unique_ptr<Base>(new Derived)
      ~Base
    블록을 나왔다
```

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

- ★★★ **clang 18 + ASan 은 `u` 에서 `run exit=0`** 이다 — **같은 UB 인데 리포트가 0건**이다.
- ★★★ **이유는 해제 함수에 크기가 안 넘어가서**다 — clang 18 은 기본으로 **`_ZdlPv`**(`operator delete(void*)`)를,\
  g++ 13 은 **`_ZdlPvm`**(`operator delete(void*, size_t)`)를 부른다. ASan 의 `new-delete-type-mismatch` 는 **넘어온 크기와 잡은 크기를 견주는 검사**라\
  **크기가 안 오면 견줄 것이 없다.** `-fsized-deallocation` 을 켜면 clang 도 **1건**을 낸다.
- ★★ **「탐침을 심었다」와 「그 경로를 밟았다」 사이에 한 칸이 더 있다** — 경로를 밟았고 UB 도 났는데, **그 검사가 쓰는 재료(크기)가 컴파일러 기본값에 달려 있었다.**\
  ★ 19편 (8)의 `new-delete-type-mismatch` 는 **g++ 판에서만** 잰 것이다 — 그 편의 결론은 그대로이고, **도구의 조건**이 하나 더 드러났다.

### (2) ★★★ 선을 긋는다 — 무엇이 UB 이고 무엇이 보장인가

**언제 쓰나** — 「돌려 봤더니 괜찮았다」를 근거로 쓰고 싶어질 때.

```text
   [표준 문장]                                   [그래서]

   delete 식 — 기반 부분 객체를 가리키는        delete (Base*)p;  Base 소멸자 비가상  -> ★ UB
   포인터로 지우면 기반 소멸자가 가상이어야      delete (Base*)p;  Base 소멸자 가상    -> 보장
   한다. 아니면 UB

   shared_ptr(Y* ptr) — 삭제자로 delete ptr      shared_ptr<Base>(new Derived)  Y=Derived -> 보장
   를 쓴다. 그 delete 가 잘 정의돼야 한다         shared_ptr<Base>((Base*)raw)   Y=Base    -> ★ UB

   delete[] — 가리키는 타입이 배열 요소          delete[] (Base*)new Derived[3]           -> ★ UB
   타입과 비슷해야 한다. 아니면 UB                (가상 소멸자가 있어도 — (6))
```

- ★★★ **`shared_ptr` 가 피하는 것은 「표준이 보장하는 동작」이다** — 구현의 호의가 아니다.\
  ★ `delete ptr` 의 `ptr` 가 `Derived*` 이므로 **애초에 다형적 삭제가 아니다.** UB 조항에 **걸리지 않는다.**
- ★★★ **`(3)` 의 UB 는 `shared_ptr` 의 결함이 아니다** — 조항이 요구하는 「**잘 정의된 `delete`**」를 사용자가 못 지킨 것이다.
- ★★★ **ASan 이 붙인 이름은 UB 의 「한 가지 결과」일 뿐이다.** `new-delete-type-mismatch` 는 **이 구현이 잡아낸 모습**이고,\
  표준은 **아무 결과도 약속하지 않는다**. 그래서 19편이 쓴 「128바이트가 샌다」도 **관찰**이다.
- ★ **층 전체는 「구현 세부사항 대 언어 보장」 절**에 표로 모았다.

### (3) ★★ `has_virtual_destructor` 격자 — 소멸자를 어떻게 선언했나

**언제 쓰나** — 「이 타입을 기반 포인터로 지워도 되나?」를 **컴파일 시간에** 물을 때.\
★ [18번](../18-rule-of-zero-three-five-default-delete/) (1)의 격자와 **같은 형식**이다.

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

```text
   격자를 읽는 순서

   ① 가상소멸 칸이 1 인가     -> 기반 포인터로 지워도 된다 (DerV 처럼 물려받아도 1)
   ② 다형 칸만 1 인가         -> ★ 가상 함수는 있는데 소멸자는 비가상 — 경고가 켜지는 자리 (PV · Fin)
   ③ 소멸가능 칸이 0 인가     -> 소멸자가 바깥에서 안 보인다 (protected — PV)
   ④ noexcept 칸이 0 인가     -> ★ 소멸자를 선언했다 — 이동이 사라졌다 ((4))
```

| 타입 | 적은 것 | 읽는 법 |
|---|---|---|
| `Zero` | 아무것도 | **기준선** — 가상소멸 0 · `noexcept` 이동 1 |
| `NV` | 비가상 소멸자 `~NV() {}` | 가상소멸 0 · ★ **`noexcept` 칸 0** — 18편 `S8` 과 같은 자리 |
| `V` | ★ **`virtual ~V() = default;`** | ★★★ **가상소멸 1 · `noexcept` 칸 0** — **`= default` 여도 이동이 사라진다** |
| `V5` | 가상 소멸자 + 이동 `= default` | ★★ **`noexcept` 칸이 1 로 돌아온다** — 되살린 것이 격자에 보인다 |
| `PV` | ★ **`protected` 비가상** | ★★★ **소멸가능 0 · 이동생 0** — 바깥에서 **만들지도** 못한다(아래) |
| `Fin` | `final` + 비가상 + 가상 함수 | 가상소멸 0 · 다형 1 — **파생이 없으니 문제가 없다**((5)) |
| `DerV` | `V` 를 물려받기만 | ★★ **가상소멸 1** — **가상성은 물려받는다** |

- ★★★ **`V` 와 `V5` 의 차이가 (4)의 예고다** — 둘 다 가상 소멸자인데 **`noexcept` 이동 칸이 0 대 1** 이다.
- ★★★ **`PV` 의 `is_move_constructible` 이 0 이다** — 이동 생성자는 **멀쩡히 있는데도** 그렇다.\
  ★ 이 트레이트는 「`T t(std::move(u));` 라는 **변수 정의가 되나**」를 묻고, 변수 정의에는 **소멸자 접근**이 필요하다.\
  ★★ **`protected` 소멸자는 「기반으로 지우지 마라」와 함께 「기반을 값으로 만들지 마라」까지 말한다.**
- ★ **`sizeof` 는 32 대 40** — 가상 함수가 하나라도 생기면 **vptr 8바이트**가 붙는다(19편 (8)의 `(4)` 와 같은 8).
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

### (4) ★★★ `virtual ~B() = default;` 한 줄이 이동을 지운다

**언제 쓰나** — 다형 기반에 「**습관처럼**」 `virtual ~Base() = default;` 를 적을 때. **실무에서 가장 흔히 밟는 자리다.**

★★★ **[18번](../18-rule-of-zero-three-five-default-delete/) (2)의 「소멸자를 쓰면 이동이 사라진다」와 같은 규칙인가** — 던져서 확인한다.

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

```text
   Zero { Tr t; }          VB { Tr t; virtual ~VB() = default; }     VB5 { …; 이동 = default }

   std::move 로 만들면     멤버: 이동        멤버: 복사   ★              멤버: 이동
   std::move 로 대입하면   멤버: 이동 대입   멤버: 복사 대입 ★           멤버: 이동 대입
   vector 재할당           이동              복사  ★                    이동

   ★ 「= default」 도 「사용자 선언」이다 — 소멸자를 선언했으니 이동이 안 만들어진다
```

- ★★★ **`VB` 는 `std::move` 를 썼는데 복사가 돈다.** 소멸자 본문을 쓰지도 않았다 — **`= default` 한 줄**이다.
- ★★★ **18편과 같은 규칙이다** — 특수 멤버를 「**사용자가 선언했나**」가 기준이고, **`= default` 도 선언이다.**\
  ★ `virtual` 이 붙은 것은 **아무 상관이 없다.** 가상이든 아니든 **소멸자를 선언한 순간** 이동 둘이 **암묵 선언되지 않는다.**
- ★★★ **`vector` 재할당까지 복사로 바뀐다** — 18편 (2)의 `(4)` 와 **같은 자리**다. **다형 기반이 들고 있는 멤버**가 전부 이 비용을 문다.
- ★★ **`VB5` 가 처방이다** — 이동 둘을 `= default` 로 **되살리면** 로그가 이동으로 돌아온다.\
  ★ 그런데 **이동을 선언하면 복사가 지워지므로**(18편 `S3`) **복사도 같이 선언**해야 한다. **다섯을 다 적게 된다.**
- ★★ **다형 기반에서는 복사를 아예 `= delete` 하는 쪽도 흔하다** — 「형태」 절의 `Shape` 가 그렇다.\
  ★ 기반을 값으로 복사하면 **잘림**(slicing)이 나기 때문이다. **이 선택은 설계**이지 규칙이 아니다.
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

### (5) ★★ `protected` 비가상 소멸자 — 「기반으로 지우지 마라」를 타입으로 말한다

**언제 쓰나** — 믹스인·정책 클래스처럼 **상속은 하되 기반 포인터로 들고 다닐 일은 없는** 기반을 만들 때.

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

- ★★★ **2번 줄 하나만 에러다** — `delete d;`(파생 포인터)와 `Derived local;`(지역 객체)은 **통과**한다.\
  ★ 파생의 소멸자는 기반의 `protected` 소멸자를 **부를 수 있고**, 바깥의 `delete (Base*)` 는 **못 부른다.**
- ★★★ **UB 가 컴파일 에러로 올라왔다** — 19편 (8)의 사고가 **빌드조차 안 된다.**
- ★★ **그런데 경고도 같이 난다** — `Base` 가 다형적이고 소멸자가 비가상이라 **`-Wdelete-non-virtual-dtor` 가 먼저 운다.**\
  ★ 에러가 이미 막았으니 **이 경고는 중복**이다. **두 컴파일러 다 에러 1 + 경고 1** 이다.
- ★★ **`Derived` 에 `final` 을 붙였다** — 파생의 파생이 `Derived*` 로 지워지는 길을 **끊기 위해서**다.\
  ★ `final` 이 없으면 `Derived` 의 소멸자(**public · 비가상**)를 통해 **같은 사고가 한 층 아래에서** 날 수 있다.

★★ **같은 기반을 `unique_ptr<Base>` 에 맡기면 막힌 자리가 표준 라이브러리 안으로 옮겨 간다.**

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

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 vdtor06.cpp -o ex (cc exit=1) =====
In file included from vdtor06.cpp:2:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/memory:78:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:99:2: warning: delete called on non-final 'Base' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
   99 |         delete __ptr;
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:404:4: note: in instantiation of member function 'std::default_delete<Base>::operator()' requested here
  404 |           get_deleter()(std::move(__ptr));
      |           ^
vdtor06.cpp:12:32: note: in instantiation of member function 'std::unique_ptr<Base>::~unique_ptr' requested here
   12 |     std::unique_ptr<Base> no = std::make_unique<Derived>();      // 2. 기반 타입으로 맡긴다
      |                                ^
In file included from vdtor06.cpp:2:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/memory:78:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:99:9: error: calling a protected destructor of class 'Base'
   99 |         delete __ptr;
      |                ^
vdtor06.cpp:6:5: note: declared protected here
    6 |     ~Base() = default;
      |     ^
1 warning and 1 error generated.
```

- ★★★ **에러 위치가 `unique_ptr.h:99`** 다 — **`default_delete<Base>` 가 `delete` 를 쓰는 자리**다.\
  ★ (1)에서 **UB 로 조용히 지나가던 바로 그 줄**이 여기서는 **컴파일 에러**가 됐다.
- ★★ **1번 줄(`unique_ptr<Derived>`)은 통과한다** — 파생 타입으로 들고 있으면 **파생의 public 소멸자**를 부른다.
- ★ **clang 은 `in instantiation of … requested here` 로 사슬을 거슬러 올라가** 결국 **12번 줄**(`unique_ptr<Base> no`)을 짚는다.

```text
   소멸자를 어디에 두나

   public  virtual   ~Base()   기반 포인터로 지워도 된다             ★ 다형 계층의 기본
   protected 비가상  ~Base()   기반 포인터로 지우면 컴파일 에러       ★ 믹스인 · 정책 클래스
   public  비가상    ~Base()   기반 포인터로 지우면 UB (경고는 가끔)  ★ 상속 계층에는 두지 않는다
   final 클래스      ~Leaf()   파생이 없다 — 가상일 이유가 없다       ★ 값 타입 · 잎 클래스
```

### (6) ★ 파생 배열을 기반 포인터로 `delete[]` 한다 — 가상 소멸자가 있어도

**언제 쓰나** — 「소멸자를 가상으로 만들었으니 `Base* p = new Derived[n]` 도 괜찮겠지?」를 점검할 때.

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

- ★★★ **g++ 판은 `run exit=139`(SIGSEGV)** 다 — `(3)` 마커를 찍고 **죽었다.** `(4)` 가 없다.
- ★★★ **clang 판은 `run exit=0`** 이다 — **`(4) 여기까지 왔다`** 가 찍혔다. 그런데 **`~Derived` 가 한 번도 안 돌았고** `id` 가 **`7` · 쓰레기 · `0`** 이다.\
  ★★ `id=7` 은 **`extra` 의 값**이다 — `Base` 크기(16)로 걸어가서 **`Derived`(24) 경계를 어긋나게 읽었다.**
- ★★★ **두 컴파일러가 정반대의 얼굴을 보였다** — 하나는 죽고, 하나는 **종료 코드 0으로 틀린 일을 한다.**\
  ★ 어느 쪽도 「올바른 결과」가 아니다 — **UB** 이기 때문이다(기준 소스 — 「가리키는 타입이 배열 요소 타입과 비슷해야 한다」).
- ★★★ **ASan 에게 물었다.**

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

- ★★★ **g++ + ASan 은 `SEGV` · clang + ASan 은 침묵(`run exit=0`)** 이다.\
  ★★ **clang 판은 ASan 이 지키는 경로를 밟았는데도 못 봤다** — 어긋난 읽기가 **전부 할당 범위 안**이기 때문이다(24 × 3 = 72바이트 안에서 16씩 걸었다).\
  ★ **「ASan 이 조용하다」는 「안전하다」가 아니다.** 여기서는 **메모리 오류가 아니라 「엉뚱한 객체를 소멸」한** 것이라 ASan 의 과녁 밖이다.
- ★★★ **왜 갈렸나 — 무엇을 `call` 하는지 어셈블리로 봤다.**

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

```text
   delete[] (Base*)b   가 부르는 소멸자

   g++      call *%rax                  ★ 가상으로 부른다 — 둘째 칸의 「vptr」 자리에 id(0)가 있다 -> 0 번지를 읽고 SEGV
   clang    call _ZN4BaseD2Ev           ★ ~Base 를 이름으로 부른다 — 죽지는 않지만 16바이트씩 걸어 엉뚱한 값을 읽는다

   delete[] (Derived*)d  (대조군)
   g++      call *%rax                  clang   call _ZN7DerivedD2Ev
```

- ★★★ **g++ 는 `delete[]` 의 소멸자도 가상으로 부르고(`call *%rax`), clang 은 `~Base` 를 직접 부른다**(`_ZN4BaseD2Ev`).\
  ★ clang 의 선택은 **표준과 모순되지 않는다** — 배열 삭제는 **정적 타입과 동적 타입이 같아야** 하므로, 같다고 가정하면 **가상으로 부를 이유가 없다.**\
  ★★ **그 가정이 깨진 자리에서 두 선택이 서로 다른 UB 증상**을 낸다. **어느 쪽이 맞느냐는 질문이 성립하지 않는다.**
- ★ **해제 함수도 다르다** — g++ 는 **크기를 넘기는 `_ZdaPvm`**(`operator delete[](void*, size_t)`), clang 은 **`_ZdaPv`** 다. **구현 선택**이다.
- ★★ **처방** — **다형 객체의 배열을 만들지 않는다.** `std::vector<std::unique_ptr<Base>>` 로 **포인터의 배열**을 만든다.

### (7) ★ `[deleting]` 소멸자는 왜 따로 있나 — `operator delete` 를 누구 것으로 부르나

**언제 쓰나** — 19편 (11)의 vtable 덤프에서 **소멸자가 두 칸**(`[complete]`·`[deleting]`)을 쓰는 이유가 궁금할 때.

★★ **19편이 찍은 것** — clang 덤프의 `B::~B() [complete]` · `B::~B() [deleting]` 두 칸, g++ 덤프의 `B::~B` **두 줄**.\
★ **여기서는 같은 질문을 다른 창으로 묻는다** — **클래스마다 `operator delete` 를 두고** 누구의 것이 불리는지 찍는다.

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

- ★★★ **`(2)` 에서 `Derived::operator delete 24` 가 불린다** — 포인터는 `Base*` 인데 **동적 타입의 해제 함수**다.\
  ★ 기준 소스 — 「해제 함수의 이름은 **동적 타입의 범위**에서 찾는다」.
- ★★★ **`(3)` 이 더 놀랍다** — `Plain` 은 자기 `operator delete` 가 없어 **`Base` 의 것**이 불리는데, **넘어온 크기가 48** 이다.\
  ★ **`Base` 의 함수가 `Plain` 의 크기를 안다** — 크기를 정한 쪽이 **`Plain` 의 소멸자**이기 때문이다.
- ★★ **`(4)` 는 `operator delete` 가 안 불린다** — 지역 객체는 **소멸만** 하고 **해제는 안 한다.**
- ★★★ **이 둘이 소멸자가 두 칸인 이유다** — 「**소멸만**」(지역 객체·멤버·기반 부분)과 「**소멸 + 해제**」(`delete p`)가 필요하다.\
  ★ **어느 해제 함수를 몇 바이트로 부를지**는 **동적 타입만 안다** — 그래서 **해제까지 가상 칸에 묶어** 둔 것이다.

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

```text
   Itanium C++ ABI 의 소멸자 세 벌 (이 편에서 찍힌 이름)

   D2  _ZN7DerivedD2Ev   기반 부분 소멸자  — 자기 멤버를 치우고 ~Base(D2) 를 부른다
   D1  _ZN7DerivedD1Ev   완전 소멸자       — g++ 는 D2 의 별칭(.set)이다   = [complete]
   D0  _ZN7DerivedD0Ev   삭제 소멸자       — D1(또는 D2) 을 부르고 Derived::operator delete 를 부른다   = [deleting]

   delete (Base*)p  ->  vtable 의 [deleting] 칸  ->  동적 타입의 D0  ->  동적 타입의 operator delete
```

- ★★★ **`D0` 의 본체가 정확히 두 줄이다** — **소멸자(`D1`/`D2`)를 부르고, `Derived::operator delete`(`_ZN7DeriveddlEPvm`)를 부른다.**
- ★★ **g++ 는 `D1` 을 `D2` 의 별칭**으로 두고(`.set _ZN7DerivedD1Ev,_ZN7DerivedD2Ev`), clang 은 `D0` 에서 **`D2` 를 바로** 부른다.\
  ★ 가상 상속이 없으면 둘이 같은 일을 하기 때문이다. **이름 붙이는 법은 ABI 의 것**이고 **구현 정의**다.
- ★ **clang 도 로그는 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic vdtor08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
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

### (8) ★ 순수 가상 소멸자 — 파생이 덮어도 정의가 따로 필요하다

**언제 쓰나** — 「순수 가상으로 만들 함수가 없는데 추상 클래스로 만들고 싶다」 — 소멸자를 순수 가상으로 둘 때.

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

- ★★★ **컴파일은 되고 링크가 실패한다** — `undefined reference to 'Base::~Base()'`. **두 컴파일러 다** 그렇다(같은 `ld`).\
  ★ 링크 에러가 **`Derived::~Derived()` 안에서** 났다 — **파생 소멸자가 끝에서 반드시 기반 소멸자를 부르기** 때문이다.
- ★★★ **다른 순수 가상 함수와 다른 점이 여기다** — `f() = 0` 은 파생이 덮으면 **기반 것이 안 불리지만**,\
  **소멸자는 파생이 덮어도 기반 것이 불린다.** 그래서 **정의가 반드시** 있어야 한다(기준 소스 — CWG 390).
- ★★ **`-DDEF` 로 정의를 주면** 돌고 **`~Derived` → `~Base`** 순서로 찍힌다.
- ★ **정의는 클래스 밖에** 둔다 — 한 줄에 쓰면 **문법 에러**다.

```cpp
/* vdtor12.cpp */
// 순수 지정과 본체를 한 줄에 — virtual ~Base() = 0 {} 는 되나
struct Base { virtual ~Base() = 0 {} };
struct Derived : Base { };
int main() { Derived d; (void)d; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 vdtor12.cpp -o ex (cc exit=1) =====
vdtor12.cpp:2:31: error: pure-specifier on function-definition
    2 | struct Base { virtual ~Base() = 0 {} };
      |                               ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 vdtor12.cpp -o ex (cc exit=1) =====
vdtor12.cpp:2:23: error: initializer on function does not look like a pure-specifier
    2 | struct Base { virtual ~Base() = 0 {} };
      |                       ^         ~
vdtor12.cpp:2:34: error: expected ';' at end of declaration list
    2 | struct Base { virtual ~Base() = 0 {} };
      |                                  ^
      |                                  ;
vdtor12.cpp:3:8: error: deleted function '~Derived' cannot override a non-deleted function
    3 | struct Derived : Base { };
      |        ^
vdtor12.cpp:2:23: note: overridden virtual function is here
    2 | struct Base { virtual ~Base() = 0 {} };
      |                       ^
vdtor12.cpp:3:18: note: destructor of 'Derived' is implicitly deleted because base class 'Base' has no destructor
    3 | struct Derived : Base { };
      |                  ^
vdtor12.cpp:4:22: error: call to implicitly-deleted default constructor of 'Derived'
    4 | int main() { Derived d; (void)d; }
      |                      ^
vdtor12.cpp:3:18: note: default constructor of 'Derived' is implicitly deleted because base class 'Base' has no destructor
    3 | struct Derived : Base { };
      |                  ^
4 errors generated.
```

- ★★ **g++ 는 1건**(`pure-specifier on function-definition`)으로 끝나고 **clang 은 4건**으로 번진다 —\
  clang 은 그 줄을 **소멸자가 없는 기반**으로 읽고 되살아나서 `Derived` 의 소멸자·생성자까지 **지워졌다**고 짚는다.\
  ★ **근거는 둘 다 `cc exit=1`** 이라는 것이다. 에러 개수의 차이는 **복구 방식**의 차이다.

### (9) 경고를 누가 보나 — 탐침 일곱

★★★ **탐침 일곱 중 몇이 답하나를 먼저 선언한다** — **답한 탐침은 g++ 1개(1번) · clang 2개(1번·6번)** 다.\
★ `-Wnon-virtual-dtor` 를 켜면 경고 줄이 **둘 다 4** 로 늘지만, **늘어난 것은 전부 1번 탐침의 선언 자리**다 — **답한 탐침 수는 그대로**다.

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
===== g++ -std=c++20 -Wall -Wextra -pedantic -c vdtor10.cpp -o /dev/null (cc exit=0) =====
vdtor10.cpp: In function ‘int main()’:
vdtor10.cpp:20:28: warning: deleting object of polymorphic class type ‘Poly’ which has non-virtual destructor might cause undefined behavior [-Wdelete-non-virtual-dtor]
   20 |     Poly* a = new PolyDer; delete a;                             // 1. 다형 기반으로 지운다(대조군)
      |                            ^~~~~~~~
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

| 심은 것 | g++ | clang | `-Wnon-virtual-dtor` | 실제로는 |
|---|---|---|---|---|
| 1. 다형 기반을 기반 포인터로 지움(대조군) | ★ **1** | ★ **1** | 선언 자리에서 **+3**(g++)·**+2**(clang) | ★★★ **UB** |
| 2. `final` 클래스를 자기 포인터로 지움 | 0 | 0 | 0 | ★ **정상** — 파생이 없다 |
| 3. `protected` 기반 — 파생으로 지움 | 0 | 0 | 0 | ★ **정상** — 「accessible」 조건에 안 걸린다 |
| 4. ★★★ **파생 배열을 기반 포인터로 `delete[]`** | ★★★ **0** | ★★★ **0** | ★★★ **0** | ★★★ **UB** — (6) |
| 5. ★★★ **raw 를 거쳐 `shared_ptr<Plain>`** | ★★★ **0** | ★★★ **0** | ★★★ **0** | ★★★ **UB** — (1)의 `(3)` |
| 6. ★★ **다형 기반을 `unique_ptr` 에** | ★★ **0** | ★★ **1**(`unique_ptr.h:99`) | — | ★★★ **UB** — (1)의 `(4)` |
| 7. ★★ **가상 소멸자가 이동을 지움** | 0 | 0 | 0 | ★★ **복사로 조용히 바뀐다** — (4) |

- ★★★ **탐침 6이 두 컴파일러가 갈린 자리다** — clang 은 **`unique_ptr.h` 안의 `delete __ptr;`** 에 경고를 붙이고 **사슬을 거슬러 26번 줄**까지 짚는다.\
  ★ g++ 는 **0건** — 경고가 **시스템 헤더 안에서** 나야 하는데 g++ 는 그 자리의 경고를 **보여 주지 않는다**(관찰 — 원인은 추론이다).\
  ★★ **「`unique_ptr` 로 감쌌더니 경고가 사라졌다」가 g++ 에서는 실제로 일어난다.**
- ★★★ **탐침 4·5 는 어떤 플래그로도 0건이다** — (6)의 배열과 (1)의 `(3)` 은 **호출 로그와 ASan 만** 본다.
- ★★ **탐침 2·3 이 조용한 것은 정답이다** — `final` 과 `protected` 가 **경고 조건 자체를 끈다.**\
  ★ clang 의 경고 이름이 그것을 말한다 — **`delete called on non-final …`**. **`final` 이면 조건에서 빠진다.**

### (10) ★★★ 언제 가상으로 둘까 — 판단표

(1)\~(9)를 판단 순서로 접었다.

```text
   이 클래스를 물려받을 사람이 있나?
     아니다  ──> ★ final 을 붙인다. 소멸자는 비가상 그대로.            (3)의 Fin · 형태의 Point
     그렇다
       │
       기반 포인터(Base* · unique_ptr<Base>)로 파생을 지울 일이 있나?
         있다   ──> ★★★ public virtual ~Base()                          (3)의 V
                     └ 이동이 필요하면 다섯을 다 적는다 — (4)
                     └ 잎 클래스에는 final — 경고 조건도 같이 꺼진다 — (9)
         없다   ──> ★★ protected 비가상 ~Base()                          (5)
                     └ 기반으로 delete 하면 컴파일 에러가 된다
                     └ 파생에는 final — 한 층 아래로 새지 않게

   ★ shared_ptr 로만 쓸 것이니 괜찮다  ──> (1)의 (3) 때문에 이것을 근거로 삼지 않는다
```

| 묻는 것 | 예 | 아니오 |
|---|---|---|
| **다형적 삭제를 허용하나** | ★★★ **`public virtual ~Base()`** | 다음 칸 |
| **다형적 삭제를 막나** | ★★ **`protected` 비가상 소멸자** | 다음 칸 |
| **파생을 막나** | ★ **`final`** — 가상 소멸자가 필요 없다 | ★★★ **어느 것도 안 고르면 `public` 비가상이 남는다** — 이 조합만은 피한다 |

- ★★★ 「**가상 함수가 하나라도 있으면 소멸자도 가상**」은 **경고 조건과 같은 모양**의 어림규칙이다 —\
  ★ 19편 (8)이 보였듯 **가상 함수가 0개인 기반도 다형적으로 지울 수 있고**, 그때 **도구는 한마디도 안 한다.**\
  ★★ 그래서 기준은 「**가상 함수가 있나**」가 아니라 「**기반 포인터로 지울 일이 있나**」다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* vdtor11.cpp */
// 소멸자를 두는 세 가지 형태. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <memory>
#include <type_traits>
#include <vector>

class Shape {                                    // ① 기반 포인터로 지울 계층 — public 가상
public:
    virtual ~Shape() = default;
    Shape() = default;                           // ★ 소멸자를 선언했으니 나머지를 정한다
    Shape(const Shape&) = delete;                //   다형 계층은 복사를 막는 쪽이 흔하다(잘림 방지)
    Shape& operator=(const Shape&) = delete;
    virtual double area() const = 0;
};
class Square final : public Shape {              // 잎 클래스는 final
public:
    explicit Square(double s) : s_(s) {}
    double area() const override { return s_ * s_; }
private:
    double s_;
};

class Counted {                                  // ② 기반으로는 안 지울 믹스인 — protected 비가상
public:
    int uses() const { return n_; }
    void touch() { ++n_; }
protected:
    ~Counted() = default;                        // 바깥에서 기반 포인터로 delete 하면 컴파일 에러
private:
    int n_ = 0;
};
class Session final : public Counted { };

struct Point final { double x, y; };             // ③ 값 타입 — 상속할 일이 없다. 가상이 필요 없다

int main() {
    std::vector<std::unique_ptr<Shape>> v;
    v.push_back(std::make_unique<Square>(3));
    std::printf("area=%.1f\n", v[0]->area());

    Session s; s.touch();
    std::printf("uses=%d\n", s.uses());

    std::printf("has_virtual_destructor  Shape %d · Counted %d · Point %d\n",
                (int)std::has_virtual_destructor_v<Shape>, (int)std::has_virtual_destructor_v<Counted>,
                (int)std::has_virtual_destructor_v<Point>);
    std::printf("sizeof  Point %zu (double 둘)\n", sizeof(Point));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -Wnon-virtual-dtor vdtor11.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
area=9.0
uses=1
has_virtual_destructor  Shape 1 · Counted 0 · Point 0
sizeof  Point 16 (double 둘)
```

- ★ **`-Wnon-virtual-dtor` 를 켜고도 경고 0건**이다 — ① `Shape` 는 가상, ② `Counted` 는 `protected`(accessible 조건 밖), ③ `Point` 는 가상 함수가 없다.

### 규칙

- ★★★ **기반 포인터로 지울 계층이면 소멸자를 `public virtual`** 로 둔다 — 없으면 **UB** 다((2)).
- ★★★ **`virtual ~B() = default;` 도 사용자 선언이다** — 이동이 사라진다. 필요하면 **이동을 `= default` 로 되살린다**((4)).
- ★★ **기반으로 지울 일이 없는 기반은 `protected` 비가상 소멸자** — 사고가 **컴파일 에러**로 올라온다((5)).
- ★★ **잎 클래스는 `final`** — 한 층 아래로 새는 길을 끊는다((5)(9)).
- ★★★ **`shared_ptr` 는 「만들 때 받은 포인터의 타입」을 기억한다** — `new Derived` 를 **바로** 넘기거나 `make_shared<Derived>` 를 쓴다((1)).
- ★ **순수 가상 소멸자에는 클래스 밖 정의가 반드시 필요하다**((8)).
- ★ **다형 객체의 배열을 만들지 않는다** — 가상 소멸자가 있어도 **`delete[]` 는 UB** 다((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| `protected: ~Base();` + `delete (Base*)p;` | ★★ **컴파일 에러**(g++ `is protected within this context` · clang `calling a protected destructor`) | (5) |
| 같은 기반 + `unique_ptr<Base>` | ★★ **컴파일 에러** — 위치가 `unique_ptr.h:99` | (5) |
| `virtual ~Base() = 0;` 정의 없음 | ★★ **링크 에러** `undefined reference to 'Base::~Base()'` | (8) |
| `virtual ~Base() = 0 {}` (한 줄에) | ★ **문법 에러**(g++ 1건 · clang 4건) | (8) |

## 어디서 틀리나

### 1. ★★★ 「스마트 포인터에 담으면 가상 소멸자가 없어도 된다」

**절반만 맞다.** (1)에서 **`shared_ptr` 만** 됐고, 그것도 **`(3)` 처럼 `Base*` 를 거치면 안 된다.**\
★ `unique_ptr<Base>` 는 **raw `delete` 와 똑같이 UB** 이고, g++ 에서는 **경고마저 사라진다**((9)의 탐침 6).

### 2. ★★★ 「`= default` 로 적었으니 아무것도 안 바뀐다」

(4)가 반증이다 — **이동이 복사로 바뀐다.** **`= default` 는 「본문을 컴파일러에 맡긴다」이지 「선언하지 않았다」가 아니다.**

### 3. ★★ 「소멸자를 가상으로 했으니 `Base* p = new Derived[n]` 도 된다」

(6)이 반증이다 — g++ 는 **죽고** clang 은 **종료 코드 0으로 틀린 소멸자를 부른다.** **가상 소멸자는 배열을 구하지 못한다.**

### 4. ★★ 「가상 함수가 없는 클래스는 상속해도 소멸자 걱정이 없다」

19편 (8)이 반증했다 — **가상 함수 0개인 기반의 다형적 삭제도 UB** 이고 **경고는 0건**이다.\
★ 여기 (10)의 기준은 「가상 함수가 있나」가 아니라 「**기반 포인터로 지울 일이 있나**」다.

### 5. ★★ 「순수 가상 소멸자는 본체가 없다」

(8)이 반증이다 — **본체가 없으면 링크가 안 된다.** 순수 가상이 뜻하는 것은 「**추상 클래스로 만든다**」이지 「본체가 없다」가 아니다.

### 6. ★ 「`protected` 소멸자는 파생에서도 못 지운다」

(5)가 반증이다 — **`Derived*` 로는 지워진다**(1번 줄 통과). 막히는 것은 **바깥에서 `Base*` 로 지우는 것 하나**다.

### 7. ★ 「`Base::operator delete` 는 `Base` 크기로 불린다」

(7)의 `(3)` 이 반증이다 — **`Base` 의 해제 함수에 `Plain` 의 크기 48** 이 넘어왔다. 크기는 **동적 타입의 소멸자**가 정한다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 선은 이렇다** — **가상 소멸자 없는 다형적 삭제는 UB 이고, `shared_ptr` 가 그것을 피하는 것은 표준이 보장하는 동작이다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **`shared_ptr(Y*)` 의 삭제자는 `delete ptr`(Y*)** — 그래서 `(1)`·`(2)` 는 **보장** · **`default_delete<Base>` 는 `delete (Base*)`** · **해제 함수는 동적 타입의 범위에서 찾는다**((7)) · **`protected` 소멸자 접근 규칙**((5)) · **사용자 선언 소멸자는 이동의 암묵 선언을 막는다**((4)) · **순수 가상 소멸자에도 정의가 필요하다**((8)) | 호출 로그 · 진단 전문 + `cc exit` · 격자 | ★★★ 「**이 `shared_ptr` 가 어떤 포인터로 만들어졌나**」 — 타입에 안 남는다((1)의 `(3)`) |
| **조건부 표준** | 특정 조건에서만 | ★ **`make_shared`·`final`·`= default` 는 C++11부터** · `-Wdelete-non-virtual-dtor` 류는 **컴파일러의 호의**((9)) | `-std=c++20` 으로만 돌렸다 | ★ C++98 판으로는 안 돌려 봤다 |
| **구현 정의** | 문서화 의무 | ★★ **`sizeof(shared_ptr<Base>)` = 16 · `unique_ptr<Base>` = 8** · vptr 8바이트((3)) · ★★ **크기 있는 해제 함수를 기본으로 쓰나**(g++ `_ZdlPvm` · clang 18 `_ZdlPv` — (1)) · **D0/D1/D2 이름과 g++ 의 `.set` 별칭**((7)) · ASan 스택의 **`_Sp_counted_ptr<Base*>`**((1)) · 진단 문구 | `sizeof` · 어셈블리 · ASan | ★★ **다른 표준 라이브러리는 제어 블록 이름이 다르다** — 근거는 「`Base*` 가 찍혔다」는 사실이다 |
| **미명시** | 몇 가지 중 하나 | ★★ **`delete[]` 의 소멸자를 가상으로 부를지 직접 부를지**((6) — g++ `call *%rax` · clang `call _ZN4BaseD2Ev`) · **크기 있는 해제 함수를 쓸지**(`_ZdaPvm` 대 `_ZdaPv`) | `-O0` 어셈블리 | ★ **어느 쪽을 골라도 표준 위반이 아니다** — 정적/동적 타입이 같을 때는 결과가 같다 |
| **UB** | 아무 일이나 | ★★★ **가상 소멸자 없이 기반 포인터로 `delete`**((1)의 `(3)`·`(4)`·`(5)`) · ★★★ **파생 배열을 기반 포인터로 `delete[]`**((6)) — **가상 소멸자가 있어도** | ASan `new-delete-type-mismatch` · SEGV · 호출 로그 | ★★★ **clang + ASan 은 (6)을 못 본다**(`run exit=0`) · 탐침 4·5 는 **어떤 플래그로도 0건** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 호출 로그 |
|---|---|---|---|---|---|
| `shared_ptr<Base>(new Derived)` 가 `~Derived` 를 부른다 | 표준 | — | — | ★ **침묵**(정상) | ★★★ **`~Derived` · `~Base`** |
| ★★★ **raw `Base*` 를 거친 `shared_ptr`** | UB | ★★★ **0건** | ★★★ **0건** | ★★ `new-delete-type-mismatch` + `_Sp_counted_ptr<Base*>` | ★★ `~Base` 만 |
| ★★ **다형 기반을 `unique_ptr<Base>`** | UB | ★★ **0건** | ★ **warning 1**(헤더 안) | ★★ g++ `new-delete-type-mismatch` · ★★★ **clang 기본은 침묵**(크기 없는 해제) | ★ `~Base` 만 |
| ★★★ **파생 배열 `delete[]`** | UB | ★★★ **0건** | ★★★ **0건** | ★ g++ `SEGV` · ★★★ **clang 침묵** | ★★ `~Derived` 0회 · `id=7` |
| `protected` 소멸자로 기반 `delete` | 표준 | ★★ **error 1** + warning 1 | ★★ **error 1** + warning 1 | — | — |
| 순수 가상 소멸자 정의 없음 | 표준 | ★★ **링크 에러** | ★★ **링크 에러** | — | — |
| ★★ **`virtual ~B() = default` 가 이동을 지움** | 표준 | ★★★ **0건** | ★★★ **0건** | — | ★★★ **「멤버: 복사」** |

- ★★ **이 표의 결론 세 줄**
  - **`protected` 와 순수 가상 소멸자 누락은 빌드가 막아 준다** — 적기만 하면 된다.
  - ★★★ **`shared_ptr`·`unique_ptr`·배열의 UB 는 컴파일러가 거의 안 본다** — 호출 로그와 ASan 이 전부다.
  - ★★★ **이동이 사라지는 것은 UB 가 아니라 표준이다** — 그래서 **어떤 도구도 안 운다.** 로그만 본다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

★★ **이 배치의 고정 항목**([14번](../14-destructors-and-deterministic-destruction/) (8) · [18번](../18-rule-of-zero-three-five-default-delete/) (7))을 이 주제에서도 찾았다.\
★ 던진 후보 — (8)의 **`virtual ~Base() = 0 {}`**(한 줄에 순수 지정 + 본체) · [21번](../21-abstract-classes-pure-virtual-and-vtable-cost/)의 **`virtual void f() = 0 { }`**.\
★★ **둘 다 두 컴파일러가 `cc exit=1` 로 막았다** — 이 주제의 문법은 **컴파일러가 관대하지 않은 자리**였다.\
★ **「이 편에서는 못 찾았다」까지가 주장**이다 — 「없다」가 아니다. 같은 배치에서 찾은 새 항목은\
[22번](../22-operator-overloading/)(`static operator()`)과 [23번](../23-three-way-comparison-spaceship/)(`bool` 이 아닌 `==`)에 있다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 인터페이스·다형 계층의 뿌리 | ★★★ **`public virtual ~Base()`** | 기반 포인터로 지운다((2)) |
| 그 기반이 이동 가능한 멤버를 든다 | ★★ **이동·복사도 결정한다**(다섯) | `= default` 소멸자가 이동을 지운다((4)) |
| 믹스인·정책 클래스 | ★★ **`protected` 비가상** | 기반으로 지우면 **컴파일 에러**((5)) |
| 잎 클래스 · 값 타입 | ★ **`final`** | 파생이 없다 — 경고 조건도 꺼진다((9)) |
| 가상 소멸자 없는 남의 기반을 다뤄야 한다 | ★★ **`make_shared<Derived>` 또는 `shared_ptr<Base>(new Derived)`** | 삭제자가 `Derived*` 를 기억한다((1)) — **raw `Base*` 를 거치지 않는다** |
| 다형 객체 여럿을 모은다 | ★★★ **`vector<unique_ptr<Base>>`** | 파생 배열 `delete[]` 는 UB((6)) |

- ★ **「가상 소멸자는 느리니 피하라」는 이 문서의 조언이 아니다** — **비용은 재지 않았다**((0)의 부적용).\
  ★ 고르는 기준은 「**기반 포인터로 지울 일이 있나**」다. 비용의 정본은 [21번](../21-abstract-classes-pure-virtual-and-vtable-cost/)이다.

## 핵심 문장

- ★★★ **가상 소멸자 없이 기반 포인터로 `delete` 하면 UB** 다 — **스마트 포인터에 담아도** `unique_ptr<Base>` 는 똑같다.
- ★★★ **`shared_ptr<Base>(new Derived)` 는 표준이 보장하는 대로 `~Derived` 를 부른다** — 삭제자가 **만들 때의 포인터 타입**을 기억하기 때문이다.
- ★★ **그래서 `Base*` 를 먼저 거치면 `shared_ptr` 도 UB** 다 — ASan 스택에 **`_Sp_counted_ptr<Base*>`** 가 찍혔다.
- ★★★ **`virtual ~B() = default;` 도 사용자 선언이라 이동이 사라진다** — 18편과 같은 규칙이다.
- ★★ **`protected` 비가상 소멸자는 다형적 삭제를 컴파일 에러로 바꾸고**, **`final` 은 파생 자체를 끊는다.**
- ★ **파생 배열의 `delete[]` 는 가상 소멸자가 있어도 UB** 다 — g++ 는 죽고 clang 은 **종료 코드 0으로** 틀렸다.
- ★ **소멸자가 vtable 에 두 칸인 이유**는 「소멸만」과 「소멸 + 동적 타입의 해제 함수」가 따로 필요하기 때문이다.

## 관련 자료

- [19번](../19-inheritance-virtual-functions-override-final/) — ★★★ **이 편의 직접 선행.** (8)의 계수·ASan·경고 조건, (11)의 vtable 덤프를 **다시 재지 않고 인용했다.**\
  그쪽은 「**가상 소멸자가 없으면 무엇이 안 도나**」까지, 여기는 「**무엇이 미정의이고 언제 가상으로 두나**」부터다.
- [14번](../14-destructors-and-deterministic-destruction/) — **소멸자가 언제 도나.** (5)의 「경고 0건」 자리가 19편을 거쳐 여기까지 왔다. (6)의 `delete` 대 `delete[]` 가 이 편 (6)의 앞 단계다.
- [18번](../18-rule-of-zero-three-five-default-delete/) — ★★ **(4)의 규칙의 정본.** 격자 형식을 (3)이 그대로 썼다.
- [15번](../15-raii-resources-as-types/) — (1)의 `sizeof` 대비. **함수 포인터 삭제자를 단 `unique_ptr` 가 16바이트**였다.
- [21번](../21-abstract-classes-pure-virtual-and-vtable-cost/) — **추상 클래스와 가상 호출 비용.** 순수 가상 함수의 일반 규칙은 거기, 여기는 **순수 가상 소멸자** 하나다.
- 목록의 **26번 주제**(`unique_ptr`)·**27번 주제**(`shared_ptr`) — **API 사용의 정본.** 여기는 **삭제자가 무엇을 기억하나**까지다.
- [`oop-basics/`](../../../../oop-basics/) — 상속·다형성의 개념. 여기는 **C++ 의 소멸 규칙**만 본다.

## 용어 풀이

> **가상 소멸자(virtual destructor)** — `virtual ~Base()`. **기반 포인터로 지워도 동적 타입의 소멸자가 돈다.**\
> 예: 19편 (8)의 `(3)` 에서 `~DerV` 가 1회 돌았다.

> **다형적 삭제(polymorphic deletion)** — 기반 포인터로 파생 객체를 `delete` 하는 것. **기반 소멸자가 비가상이면 UB.**\
> 예: (1)의 `(4)` 가 `~Base` 만 불렀다.

> **삭제자(deleter)** — 스마트 포인터가 자원을 놓을 때 부르는 것. `unique_ptr` 는 **타입에**, `shared_ptr` 는 **제어 블록에** 둔다.\
> 예: (1)의 ASan 스택 — `default_delete<Base>` 와 `_Sp_counted_ptr<Base*>`.

> **타입 소거(type erasure)** — 구체 타입을 속에 기억하고 바깥 타입에는 드러내지 않는 것.\
> 예: `shared_ptr<Base>` 가 속으로 `delete (Derived*)` 를 들고 있었다((1)의 `(1)`).

> **`protected` 비가상 소멸자** — 바깥에서 기반 포인터로 지우는 것을 **컴파일 에러**로 만드는 관용구.\
> 예: (5)에서 `delete b2;` 만 막혔다.

> **삭제 소멸자(deleting destructor)** — 소멸 후 **동적 타입의 `operator delete`** 까지 부르는 소멸자 판. Itanium ABI 의 `D0`.\
> 예: (7)에서 `_ZN7DerivedD0Ev` 가 `Derived::operator delete` 를 불렀다.

> **순수 가상 소멸자(pure virtual destructor)** — `virtual ~Base() = 0;`. 클래스를 추상으로 만들지만 **정의가 반드시 필요하다.**\
> 예: (8)에서 정의가 없자 `undefined reference to 'Base::~Base()'`.

> **`has_virtual_destructor`** — 「**소멸자가 가상인가**」를 묻는 트레이트. **물려받은 가상성도 1** 이다.\
> 예: (3)의 `DerV` 가 1 이었다.

## 더 들어가면

- **`std::destroying_delete_t`(C++20)** — 클래스별 `operator delete` 가 **소멸자 호출까지 직접 맡는** 형태. (7)의 두 칸 이야기를 **사용자 쪽으로** 끌어온 것이다. 이 문서는 던지지 않았다.
- **가상 상속에서 `D1` 과 `D2` 가 갈린다** — (7)에서 g++ 가 둘을 별칭으로 둔 것은 **가상 기반이 없어서**다. 가상 상속 판은 안 찍었다.
- **`shared_ptr` 의 별칭 생성자(aliasing constructor)** — 제어 블록과 가리키는 포인터를 **따로 준다.** (1)의 「무엇을 기억하나」가 더 벌어지는 자리다. 목록의 **27번 주제**다.
- **삭제 소멸자와 `delete this`** — 객체가 스스로 지우는 관용구에서 `D0` 이 불린다. 이 문서는 다루지 않았다.
