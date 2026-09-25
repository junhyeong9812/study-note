# cpp/syntax/14 — 소멸자와 결정적 파괴 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·sanitizer 리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **ASan 의 PID·주소**와 **진단 문구**는 흔들리는 칸이다.\
> 근거로 쓰는 것은 **로그 순서 · 소멸자가 돈 횟수 · ASan 오류의 이름 · `cc exit`/`run exit` · 경고 개수**다.\
> ★★ **한 칸이 더 흔들린다** — **임시 객체를 만드는 순서**가 g++ 와 clang 에서 갈렸다(6번).\
> 갈리지 않은 것은 **「만든 역순으로 파괴된다」는 성질**이고, 근거는 그쪽만 쓴다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「몇 배 빠르다」는 문장이 **한 줄도 없다**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 전부 **생성의 역순** — 다만 `vector` 만 앞에서부터다

**출력**

```text
===== 소스: dtor01.cpp =====
// 파괴 순서를 전수로 찍는다 — 스코프·멤버·기반·컨테이너·임시·static
#include <cstdio>
#include <vector>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) { std::printf("    [생성] %s\n", tag); }
    ~D() { std::printf("    [파괴] %s\n", tag); }
};

struct Base {
    D b{"기반의 멤버"};
    Base() { std::printf("  [본문] Base()\n"); }
    ~Base() { std::printf("  [본문] ~Base()\n"); }
};

struct Derived : Base {
    D m1{"파생 멤버 1 — 먼저 선언"};
    D m2{"파생 멤버 2 — 나중 선언"};
    Derived() { std::printf("  [본문] Derived()\n"); }
    ~Derived() { std::printf("  [본문] ~Derived()\n"); }
};

static D g_static{"전역 static"};

void pass(const D&) {}

int main() {
    std::printf("(1) 같은 스코프에 셋\n");
    { D x{"지역 1"}; D y{"지역 2"}; D z{"지역 3"}; std::printf("    블록 끝 직전\n"); }

    std::printf("(2) 멤버와 기반 클래스\n");
    { Derived d; std::printf("    블록 끝 직전\n"); }

    std::printf("(3) vector 원소 셋\n");
    { std::vector<D> v; v.reserve(3);
      v.emplace_back("벡터 0"); v.emplace_back("벡터 1"); v.emplace_back("벡터 2");
      std::printf("    블록 끝 직전\n"); }

    std::printf("(4) 임시 객체\n");
    pass(D{"임시"});
    std::printf("    이 줄은 임시가 사라진 뒤다\n");

    std::printf("(5) const 참조에 묶은 임시\n");
    { const D& r = D{"참조에 묶인 임시"}; (void)r; std::printf("    블록 끝 직전\n"); }

    std::printf("(6) 함수 안의 static\n");
    { static D local_static{"함수 지역 static"}; }

    std::printf("(7) main 의 마지막 줄\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
    [생성] 전역 static
(1) 같은 스코프에 셋
    [생성] 지역 1
    [생성] 지역 2
    [생성] 지역 3
    블록 끝 직전
    [파괴] 지역 3
    [파괴] 지역 2
    [파괴] 지역 1
(2) 멤버와 기반 클래스
    [생성] 기반의 멤버
  [본문] Base()
    [생성] 파생 멤버 1 — 먼저 선언
    [생성] 파생 멤버 2 — 나중 선언
  [본문] Derived()
    블록 끝 직전
  [본문] ~Derived()
    [파괴] 파생 멤버 2 — 나중 선언
    [파괴] 파생 멤버 1 — 먼저 선언
  [본문] ~Base()
    [파괴] 기반의 멤버
(3) vector 원소 셋
    [생성] 벡터 0
    [생성] 벡터 1
    [생성] 벡터 2
    블록 끝 직전
    [파괴] 벡터 0
    [파괴] 벡터 1
    [파괴] 벡터 2
(4) 임시 객체
    [생성] 임시
    [파괴] 임시
    이 줄은 임시가 사라진 뒤다
(5) const 참조에 묶은 임시
    [생성] 참조에 묶인 임시
    블록 끝 직전
    [파괴] 참조에 묶인 임시
(6) 함수 안의 static
    [생성] 함수 지역 static
(7) main 의 마지막 줄
    [파괴] 함수 지역 static
    [파괴] 전역 static
```

**왜 그런가**

```text
   ① 지역 셋                ② 멤버와 기반              ③ vector

   지역 3                   ~Derived() 본문            벡터 0   <- ★ 앞에서부터
   지역 2                   파생 멤버 2                벡터 1
   지역 1                   파생 멤버 1                벡터 2
   ^^^^^^ 선언 역순          ~Base() 본문
                            기반의 멤버
                            ^^^^^^^^^^ 기반이 맨 마지막
```

- ★★★ **지역 객체는 선언 역순**이다 — `지역 3 → 지역 2 → 지역 1`. **스택에 쌓인 것을 위에서부터 걷는다.**
- ★★★ **파생 객체의 파괴는 네 단계**다 — **① 파생 소멸자 본문 → ② 파생 멤버(선언 역순) → ③ 기반 소멸자 본문 → ④ 기반의 멤버.**\
  생성이 `기반 멤버 → Base() 본문 → 파생 멤버 → Derived() 본문` 이었으니 **정확한 역순**이다.
- ★★ **`std::vector` 만 앞에서부터**였다(`벡터 0 → 1 → 2`). ★★★ **표준은 이 순서를 정해 두지 않았다** —\
  **libstdc++ 의 선택**이고, 근거로 쓰면 안 되는 칸이다.
- ★ **`(4)` 의 임시는 `pass(...)` 가 끝나는 세미콜론에서** 죽는다 — `이 줄은 임시가 사라진 뒤다` **앞**이다.
- ★ **`(5)` 의 `const D&` 에 묶인 임시는 블록 끝까지** 산다 — `블록 끝 직전` **뒤**에 파괴된다.
- ★★ **`전역 static` 의 생성 줄은 출력 맨 위**(`(1)` 보다도 위)이고, **파괴 줄은 맨 아래**(`(7) main 의 마지막 줄` 아래)다.

### 2. ★★ 소멸자 넷이 전부 돌고, 그다음에 `catch` 다

**출력**

```text
===== 소스: dtor02.cpp =====
// 예외 되감기에서 소멸자가 도나 — 마커도 진단도 전부 표준 오류로 찍는다
#include <cstdio>
#include <stdexcept>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) { std::fprintf(stderr, "    [생성] %s\n", tag); }
    ~D() { std::fprintf(stderr, "    [파괴] %s\n", tag); }
};

void inner()  { D a{"inner 의 a"}; D b{"inner 의 b"}; throw std::runtime_error("inner 가 던진다"); }
void middle() { D m{"middle 의 m"}; inner(); }

int main() {
    std::fprintf(stderr, "(1) 세 층을 지나 던지면\n");
    try {
        D o{"main 의 o"};
        middle();
        std::fprintf(stderr, "    이 줄은 안 돈다\n");
    } catch (const std::exception& e) {
        std::fprintf(stderr, "    [catch] %s\n", e.what());
    }
    std::fprintf(stderr, "(2) 잡은 뒤에는 계속 돈다\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 세 층을 지나 던지면
    [생성] main 의 o
    [생성] middle 의 m
    [생성] inner 의 a
    [생성] inner 의 b
    [파괴] inner 의 b
    [파괴] inner 의 a
    [파괴] middle 의 m
    [파괴] main 의 o
    [catch] inner 가 던진다
(2) 잡은 뒤에는 계속 돈다
```

**왜 그런가**

- ★★★ **`[파괴]` 가 넷**이다 — `inner 의 b → inner 의 a → middle 의 m → main 의 o`.\
  **한 프레임 안에서는 선언 역순**, **프레임끼리는 안쪽부터** — 합치면 **전체가 하나의 역순**이다.
- ★★★ **`[catch]` 는 소멸자들 뒤**다. 되감기가 **다 끝난 뒤에** 처리기가 돈다.
- ★ **`이 줄은 안 돈다` 는 찍히지 않았다** — `middle()` 에서 던졌으므로 그 뒤 문장은 실행되지 않는다.
- ★★ **마커를 전부 `stderr` 로 찍은 이유** — 표준 출력과 표준 오류를 섞으면\
  **파이프로 받을 때 순서가 뒤집히는 런타임이 있기 때문**이다. 이 절의 결론이 **순서 그 자체**라\
  섞는 순간 근거가 무너진다. 표준 오류는 버퍼링을 안 해 순서가 고정된다.

### 3. ★★★ `~DerNV` 는 **한 번도 안 불린다** — 그런데 `run exit=0` 이고 경고도 0건이다

**출력**

```text
===== 소스: dtor05.cpp =====
// 가상 소멸자가 없는 기반 포인터로 지우면 — 마커를 표준 오류로 찍는다
#include <cstdio>
#include <cstdlib>

struct BaseNV {
    ~BaseNV() { std::fprintf(stderr, "  [파괴] ~BaseNV\n"); }
};
struct DerNV : BaseNV {
    char* buf;
    DerNV() : buf(static_cast<char*>(std::malloc(32))) {
        std::fprintf(stderr, "  [생성] ~DerNV 가 놓아야 할 32바이트를 잡았다\n");
    }
    ~DerNV() { std::fprintf(stderr, "  [파괴] ~DerNV — 32바이트를 놓는다\n"); std::free(buf); }
};

struct BaseV {
    virtual ~BaseV() { std::fprintf(stderr, "  [파괴] ~BaseV\n"); }
};
struct DerV : BaseV {
    ~DerV() override { std::fprintf(stderr, "  [파괴] ~DerV\n"); }
};

int main() {
    std::fprintf(stderr, "(1) 가상 소멸자가 없는데 기반 포인터로 delete\n");
    BaseNV* p = new DerNV;
    delete p;
    std::fprintf(stderr, "(2) 가상 소멸자가 있으면\n");
    BaseV* q = new DerV;
    delete q;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 가상 소멸자가 없는데 기반 포인터로 delete
  [생성] ~DerNV 가 놓아야 할 32바이트를 잡았다
  [파괴] ~BaseNV
(2) 가상 소멸자가 있으면
  [파괴] ~DerV
  [파괴] ~BaseV
```

**ASan 을 붙이면**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. dtor05.cpp -o exa && ./exa | grep -E '^(==|  object|  size|SUMMARY)' (cc exit=0 · run exit=1) =====
=================================================================
==1330059==ERROR: AddressSanitizer: new-delete-type-mismatch on 0x502000000010 in thread T0:
  object passed to delete has wrong type:
  size of the allocated type:   8 bytes;
  size of the deallocated type: 1 bytes.
SUMMARY: AddressSanitizer: new-delete-type-mismatch ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
==1330059==HINT: if you don't care about these errors you may set ASAN_OPTIONS=new_delete_type_mismatch=0
==1330059==ABORTING
```

**경고가 나는 판과 안 나는 판**

```text
===== 소스: dtor06.cpp =====
// 경고가 나는 판과 안 나는 판 — 같은 UB 인데 하나만 보인다
struct Poly { virtual void f() {} ~Poly() {} };       // 가상 함수는 있고 소멸자는 가상이 아니다
struct DerPoly : Poly { int big[8]; };
struct Plain { ~Plain() {} };                          // 가상 함수가 하나도 없다
struct DerPlain : Plain { int big[8]; };
int main() {
    Poly* a = new DerPoly;   delete a;
    Plain* b = new DerPlain; delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor06.cpp -o ex (cc exit=0) =====
dtor06.cpp: In function ‘int main()’:
dtor06.cpp:7:30: warning: deleting object of polymorphic class type ‘Poly’ which has non-virtual destructor might cause undefined behavior [-Wdelete-non-virtual-dtor]
    7 |     Poly* a = new DerPoly;   delete a;
      |                              ^~~~~~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic dtor06.cpp -o ex (cc exit=0) =====
dtor06.cpp:7:30: warning: delete called on non-final 'Poly' that has virtual functions but non-virtual destructor [-Wdelete-non-abstract-non-virtual-dtor]
    7 |     Poly* a = new DerPoly;   delete a;
      |                              ^
1 warning generated.
```

**왜 그런가**

- ★★★ **`(1)` 에서 `[파괴]` 는 한 줄뿐이다 — `~BaseNV`.**\
  `delete p` 는 **`p` 의 정적 타입**(`BaseNV*`)만 보고 소멸자를 고르므로 **`~DerNV` 로 갈 길이 없다.**\
  `~DerNV` 가 놓기로 되어 있던 32바이트는 **그대로 남는다.**
- ★★★ **`run exit=0` 이고 g++·clang **둘 다 경고 0건**이다**(9번의 개수 블록).\
  기반 클래스에 **가상 함수가 하나도 없으면** 두 컴파일러 다 `-Wdelete-non-virtual-dtor` 계열을 안 켠다.
- ★★★ **ASan 은 누수가 아니라 `new-delete-type-mismatch` 로 잡는다** —\
  `size of the allocated type: 8 bytes` 대 `size of the deallocated type: 1 bytes`.\
  ★ **`DerNV` 로 잡고 `BaseNV` 로 놓으니 할당기가 받는 크기가 어긋난 것**이다. `run exit=1`(`ABORTING`).
- ★★ **가상 함수가 있는 기반(`Poly`)은 경고가 난다** — g++ 1건 · clang 1건, 이름은 각각\
  `-Wdelete-non-virtual-dtor` 와 `-Wdelete-non-abstract-non-virtual-dtor` 다.\
  **가상 함수가 없는 `Plain` 쪽은 똑같이 UB 인데 0건**이다 — **같은 파일 안에서 하나만 보인다.**
- ★ **`BaseV` 쪽**은 `~DerV → ~BaseV` 로 **파생부터** 돈다 — 1번의 역순 규칙 그대로다.

### 4. ★★ 소멸자가 **셋 중 하나만** 돌고, 프로그램이 죽는다(`run exit=134`)

**출력**

```text
===== 소스: dtor07.cpp =====
// new[] 로 잡고 delete 로 놓으면 — 소멸자가 몇 번 도나
#include <cstdio>
struct D {
    int id = -1;
    ~D() { std::fprintf(stderr, "  [파괴] D %d\n", id); }
};
int main() {
    std::fprintf(stderr, "(1) new D[3] 을 delete 로 놓는다\n");
    D* a = new D[3];
    a[0].id = 0; a[1].id = 1; a[2].id = 2;
    delete a;
    std::fprintf(stderr, "(2) 여기까지 오나\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor07.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
dtor07.cpp: In function ‘int main()’:
dtor07.cpp:11:12: warning: ‘void operator delete(void*, long unsigned int)’ called on pointer returned from a mismatched allocation function [-Wmismatched-new-delete]
   11 |     delete a;
      |            ^
dtor07.cpp:9:19: note: returned from ‘void* operator new [](long unsigned int)’
    9 |     D* a = new D[3];
      |                   ^
(1) new D[3] 을 delete 로 놓는다
  [파괴] D 0
munmap_chunk(): invalid pointer
```

**ASan 을 붙이면**

```text
===== g++ -std=c++20 -Wall -Wextra -fsanitize=address -g -ffile-prefix-map="$PWD"=. dtor07.cpp -o exa && ./exa | grep -E '^(==|  \[|SUMMARY|D [0-9])' (cc exit=0 · run exit=1) =====
dtor07.cpp: In function ‘int main()’:
dtor07.cpp:11:12: warning: ‘void operator delete(void*, long unsigned int)’ called on pointer returned from a mismatched allocation function [-Wmismatched-new-delete]
   11 |     delete a;
      |            ^
dtor07.cpp:9:19: note: returned from ‘void* operator new [](long unsigned int)’
    9 |     D* a = new D[3];
      |                   ^
  [파괴] D 0
=================================================================
==1330155==ERROR: AddressSanitizer: attempting free on address which was not malloc()-ed: 0x503000000048 in thread T0
SUMMARY: AddressSanitizer: bad-free ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164 in operator delete(void*, unsigned long)
==1330155==ABORTING
```

**왜 그런가**

- ★★★ **`[파괴] D 0` 한 줄뿐**이다. `delete` 는 **객체 하나**를 지우는 문법이라 **개수를 모른다.**
- ★★★ **`(2) 여기까지 오나` 는 안 찍혔다** — `munmap_chunk(): invalid pointer` 로 죽었다.\
  **`cc exit=0` · `run exit=134`** 다(128 + SIGABRT).\
  ★ 배열 할당은 **앞에 개수를 적어 두는 구현이 흔해** 반환 포인터 자체가 어긋난다.
- ★★ **여기는 도구가 본다** — g++ `-Wmismatched-new-delete` **1건**, clang 도 **1건**.\
  `note: returned from 'void* operator new [](long unsigned int)'` 가 어디서 왔는지까지 적어 준다.
- ★★ **ASan 은 이것을 `bad-free` 라고 부른다**(`attempting free on address which was not malloc()-ed`).\
  ★★★ **3번의 `new-delete-type-mismatch` 와 이름이 다르다** — **이름이 곧 무엇이 어긋났는지**다.

### 5. ★ 둘 다 안 찍힌다 — `std::terminate` 다

**출력**

```text
===== 소스: dtor03.cpp =====
// 소멸자에서 던지면 — 마커를 표준 오류로 찍어 순서를 고정한다
#include <cstdio>
#include <stdexcept>

struct Bomb {
    ~Bomb() {
        std::fprintf(stderr, "    [소멸자] 여기서 던진다\n");
        throw std::runtime_error("소멸자에서 던졌다");
    }
};

int main() {
    std::fprintf(stderr, "(1) 소멸자에서 던지면\n");
    try {
        Bomb b; (void)b;
    } catch (const std::exception&) {
        std::fprintf(stderr, "    [catch] 여기로 오나?\n");
    }
    std::fprintf(stderr, "(2) 여기까지 오나?\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor03.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
dtor03.cpp: In destructor ‘Bomb::~Bomb()’:
dtor03.cpp:8:9: warning: ‘throw’ will always call ‘terminate’ [-Wterminate]
    8 |         throw std::runtime_error("소멸자에서 던졌다");
      |         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
dtor03.cpp:8:9: note: in C++11 destructors default to ‘noexcept’
(1) 소멸자에서 던지면
    [소멸자] 여기서 던진다
terminate called after throwing an instance of 'std::runtime_error'
  what():  소멸자에서 던졌다
```

**소멸자가 정말 `noexcept` 인가**

```text
===== 소스: dtor04.cpp =====
// 소멸자는 적지 않아도 noexcept 다
#include <cstdio>
#include <type_traits>
#include <string>
#include <vector>

struct Plain { ~Plain() {} };
struct Marked { ~Marked() noexcept {} };
struct Loud { ~Loud() noexcept(false) {} };

int main() {
    Plain p; Marked m; Loud l;
    std::printf("  noexcept(p.~Plain())         = %d\n", (int)noexcept(p.~Plain()));
    std::printf("  noexcept(m.~Marked())        = %d\n", (int)noexcept(m.~Marked()));
    std::printf("  noexcept(l.~Loud())          = %d   (직접 꺼야 꺼진다)\n", (int)noexcept(l.~Loud()));
    std::printf("  is_nothrow_destructible<std::string> = %d\n",
                (int)std::is_nothrow_destructible_v<std::string>);
    std::printf("  is_nothrow_destructible<std::vector<int>> = %d\n",
                (int)std::is_nothrow_destructible_v<std::vector<int>>);
    std::printf("  is_nothrow_destructible<Loud> = %d\n", (int)std::is_nothrow_destructible_v<Loud>);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  noexcept(p.~Plain())         = 1
  noexcept(m.~Marked())        = 1
  noexcept(l.~Loud())          = 0   (직접 꺼야 꺼진다)
  is_nothrow_destructible<std::string> = 1
  is_nothrow_destructible<std::vector<int>> = 1
  is_nothrow_destructible<Loud> = 0
```

**왜 그런가**

- ★★★ **`[catch] 여기로 오나?` 도 `(2) 여기까지 오나?` 도 안 찍혔다.**\
  `terminate called after throwing an instance of 'std::runtime_error'` 뒤에 프로그램이 죽었다.
- ★★★ **`cc exit=0` · `run exit=134`** 다. **컴파일이 통과한 것과 프로그램이 사는 것은 다른 이야기**다.
- ★★ **컴파일러가 미리 말한다** — `warning: 'throw' will always call 'terminate' [-Wterminate]` 와\
  `note: in C++11 destructors default to 'noexcept'`. **경고 문구가 곧 규칙 설명**이다.
- ★★★ **소멸자는 C++11부터 적지 않아도 `noexcept`** 다 — `noexcept(p.~Plain())` 이 **1**이다.\
  **`noexcept(false)` 로 직접 꺼야** 0이 된다(`Loud`). `std::string`·`std::vector<int>` 도 **1**이다.
- ★ **그래서 규칙은 하나다** — 소멸자에서 던지지 않는다. 실패를 알려야 하면 **명시 `close()`** 를 따로 둔다.

### 6. ★★ 파괴는 **만든 역순** — 그런데 **만드는 순서가 두 컴파일러에서 갈렸다**

**출력 — g++**

```text
===== 소스: dtor08.cpp =====
// 임시 객체는 언제 사라지나 — 전체 식의 끝
#include <cstdio>
#include <string>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) { std::printf("    [생성] %s\n", tag); }
    ~D() { std::printf("    [파괴] %s\n", tag); }
    int value() const { return 1; }
};

int use(const D&, const D&) { return 0; }

int main() {
    std::printf("(1) 한 식 안에 임시 둘\n");
    int r = use(D{"임시 왼쪽"}, D{"임시 오른쪽"}) + D{"임시 셋째"}.value();
    std::printf("    식이 끝났다 (r=%d)\n", r);

    std::printf("(2) const 참조에 묶으면 수명이 늘어난다\n");
    { const D& kept = D{"참조가 붙잡은 임시"};
      std::printf("    아직 살아 있다: %s\n", kept.tag);
      std::printf("    블록 끝 직전\n"); }

    std::printf("(3) 멤버를 가리키는 참조는 임시를 못 붙잡는다\n");
    { const char* p = std::string("사라질 문자열").c_str();
      std::printf("    p 를 읽지 않는다 — 가리키는 곳이 이미 사라졌다 (p != nullptr: %d)\n",
                  (int)(p != nullptr)); }
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) 한 식 안에 임시 둘
    [생성] 임시 오른쪽
    [생성] 임시 왼쪽
    [생성] 임시 셋째
    [파괴] 임시 셋째
    [파괴] 임시 왼쪽
    [파괴] 임시 오른쪽
    식이 끝났다 (r=1)
(2) const 참조에 묶으면 수명이 늘어난다
    [생성] 참조가 붙잡은 임시
    아직 살아 있다: 참조가 붙잡은 임시
    블록 끝 직전
    [파괴] 참조가 붙잡은 임시
(3) 멤버를 가리키는 참조는 임시를 못 붙잡는다
    p 를 읽지 않는다 — 가리키는 곳이 이미 사라졌다 (p != nullptr: 1)
```

**출력 — clang**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic dtor08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
dtor08.cpp:25:23: warning: object backing the pointer will be destroyed at the end of the full-expression [-Wdangling-gsl]
   25 |     { const char* p = std::string("사라질 문자열").c_str();
      |                       ^~~~~~~~~~~~~~~~~~~~~~~~~~~~
1 warning generated.
(1) 한 식 안에 임시 둘
    [생성] 임시 왼쪽
    [생성] 임시 오른쪽
    [생성] 임시 셋째
    [파괴] 임시 셋째
    [파괴] 임시 오른쪽
    [파괴] 임시 왼쪽
    식이 끝났다 (r=1)
(2) const 참조에 묶으면 수명이 늘어난다
    [생성] 참조가 붙잡은 임시
    아직 살아 있다: 참조가 붙잡은 임시
    블록 끝 직전
    [파괴] 참조가 붙잡은 임시
(3) 멤버를 가리키는 참조는 임시를 못 붙잡는다
    p 를 읽지 않는다 — 가리키는 곳이 이미 사라졌다 (p != nullptr: 1)
```

**왜 그런가**

```text
   int r = use(D{왼쪽}, D{오른쪽}) + D{셋째}.value();

   g++    만들기  오른쪽 · 왼쪽 · 셋째      파괴  셋째 · 왼쪽 · 오른쪽
   clang  만들기  왼쪽 · 오른쪽 · 셋째      파괴  셋째 · 오른쪽 · 왼쪽
          ^^^^^^^^^^^^^^^^^^^^^^^          ^^^^^^^^^^^^^^^^^^^^^^^^
          ★ 갈린다 — 미명시                ★ 「만든 역순」이라는 성질은 같다
```

- ★★★ **함수 인자를 만드는 순서는 미명시다.** 두 컴파일러가 실제로 갈렸으므로 **여기에 결론을 세우면 안 된다.**
- ★★★ **갈리지 않는 것은 「만든 역순으로 파괴된다」는 성질**이다 — 두 판 모두 그랬고, 이것이 **근거로 쓸 칸**이다.
- ★★ **세 임시가 전부 세미콜론에서 죽었다**(`식이 끝났다` 가 파괴 뒤). **전체 식의 끝**이 기준이다.
- ★ **`(3)` 을 경고하는 쪽은 clang 뿐**이다 —\
  `object backing the pointer will be destroyed at the end of the full-expression [-Wdangling-gsl]`.\
  **g++ 는 같은 줄에 대해 0건**이다.
- ★ **`p` 가 가리키는 값을 안 읽은 이유** — 이미 파괴된 메모리를 읽는 것 자체가 **UB** 라\
  값을 실으면 「돌려 봤다」가 아니라 「우연히 나온 쓰레기를 실었다」가 된다.\
  **실을 수 있는 것은 「널이 아니다」뿐**이고, 그것으로도 「포인터는 멀쩡해 보인다」가 증명된다.

### 7. ★ `main` 이 끝난 **뒤**에 죽는다 — 그리고 `_Exit` 는 하나도 안 돌린다

**출력 — `static` 의 생성과 파괴**

```text
===== 소스: dtor09.cpp =====
// static 객체는 언제, 어떤 순서로 파괴되나
#include <cstdio>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) { std::printf("  [생성] %s\n", tag); }
    ~D() { std::printf("  [파괴] %s\n", tag); }
};

D g1{"전역 1 — 먼저 적음"};
D g2{"전역 2 — 나중 적음"};

D& lazy() { static D s{"함수 지역 static — 처음 부를 때"}; return s; }

int main() {
    std::printf("  main 시작\n");
    lazy();
    lazy();
    D local{"main 의 지역"};
    std::printf("  main 의 마지막 줄\n");
    return 0;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor09.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  [생성] 전역 1 — 먼저 적음
  [생성] 전역 2 — 나중 적음
  main 시작
  [생성] 함수 지역 static — 처음 부를 때
  [생성] main 의 지역
  main 의 마지막 줄
  [파괴] main 의 지역
  [파괴] 함수 지역 static — 처음 부를 때
  [파괴] 전역 2 — 나중 적음
  [파괴] 전역 1 — 먼저 적음
```

**출력 — `std::_Exit` 로 나가면**

```text
===== 소스: dtor10.cpp =====
// _Exit 로 나가면 소멸자가 하나도 안 돈다
#include <cstdio>
#include <cstdlib>

struct D {
    const char* tag;
    explicit D(const char* t) : tag(t) { std::printf("  [생성] %s\n", tag); }
    ~D() { std::printf("  [파괴] %s\n", tag); }
};

D g1{"전역 1"};

int main() {
    D local{"main 의 지역"};
    std::printf("  이제 std::_Exit(0) 을 부른다\n");
    std::fflush(stdout);
    std::_Exit(0);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor10.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  [생성] 전역 1
  [생성] main 의 지역
  이제 std::_Exit(0) 을 부른다
```

**왜 그런가**

- ★★★ **`static` 은 `main` 의 마지막 줄 뒤에 죽는다.** `main 의 마지막 줄` → `main 의 지역` 파괴 →\
  **함수 지역 `static` → 전역 2 → 전역 1** 순이다. **구성이 끝난 역순**이다.
- ★★ **함수 지역 `static` 은 처음 부를 때 한 번만** 생긴다 — `lazy()` 를 두 번 불렀는데 **생성 로그는 한 줄**이다.\
  **한 번도 안 부르면 생기지도 않고, 생기지 않았으면 파괴되지도 않는다.**
- ★★★ **`std::_Exit(0)` 으로 나가면 `[파괴]` 줄이 0개**다. 그런데 **`run exit=0`** 이다 —\
  **「정상 종료했다」와 「정리가 됐다」는 다른 말**이다.
- ★ **그래서 「프로그램이 끝나면 소멸자가 다 돈다」는 `return`/`std::exit` 경로에서만 참**이다.\
  `_Exit`·`abort`·`terminate` 는 전부 건너뛴다(5번의 `terminate` 가 그 실측이다).

### 8. ★★ 탐침 아홉 중 **일곱이 답하고 둘이 침묵**했다

**출력**

```text
===== echo "dtor03 소멸자에서 던짐   g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic dtor03.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor03 소멸자에서 던짐   g++ 경고 1
===== echo "dtor05 가상 아닌 소멸자  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic dtor05.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor05 가상 아닌 소멸자  g++ 경고 0
===== echo "dtor06 다형 클래스       g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic dtor06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor06 다형 클래스       g++ 경고 1
===== echo "dtor07 delete vs delete[] g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic dtor07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor07 delete vs delete[] g++ 경고 1
===== echo "dtor05 가상 아닌 소멸자  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic dtor05.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor05 가상 아닌 소멸자  clang 경고 0
===== echo "dtor06 다형 클래스       clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic dtor06.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor06 다형 클래스       clang 경고 1
===== echo "dtor07 delete vs delete[] clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic dtor07.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor07 delete vs delete[] clang 경고 1
===== echo "dtor11 ill-formed delete  g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic dtor11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor11 ill-formed delete  g++ 경고 3
===== echo "dtor11 ill-formed delete  clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic dtor11.cpp -o ex 2>&1 | grep -c 'warning:')" (exit=0) =====
dtor11 ill-formed delete  clang 경고 2
```

**왜 그런가**

| 사건 | g++ | clang | 도구가 보나 |
|---|---|---|---|
| 소멸자에서 던짐 | 1 | — | ★ 본다 |
| 가상 아닌 소멸자 — 기반에 **가상 함수 있음** | 1 | 1 | ★ 본다 |
| ★★★ 가상 아닌 소멸자 — 기반에 **가상 함수 없음** | ★★★ **0** | ★★★ **0** | ★★★ **못 본다** |
| `new[]` 를 `delete` 로 | 1 | 1 | ★ 본다 |
| `void*` 에 `delete`(+ 불완전 타입) | 3 | 2 | ★ 본다(경고까지만) |
| ★★ `c_str()` 이 가리키는 임시 | ★★★ **0** | ★ **1** | ★★ **clang 만** |
| 파괴 순서 자체 | 0 | 0 | ★★★ **아무도 못 본다 — 로그만** |

- ★★★ **침묵한 둘**은 **가상 함수가 없는 기반으로 다형적 삭제**(3번)와 **g++ 에서의 `c_str()` 댕글링**(6번)이다.\
  **이 주제에서 가장 위험한 둘이 정확히 그 둘**이다.
- ★★ **같은 사건인데 개수가 다르다** — `void*` 판이 g++ 3 · clang 2다.\
  **「경고 N건」은 컴파일러를 밝히지 않으면 뜻이 없다.**
- ★ **파괴 순서를 말해 주는 플래그는 없다.** 이 주제의 유일한 창은 **소멸자에 로그를 심는 것**이다.

### 9. ★★ `void*` 에 `delete` 는 **ill-formed 인데 g++ 는 `cc exit=0`** 이다

**출력**

```text
===== 소스: dtor11.cpp =====
// 종료 코드가 0인데 ill-formed — delete 가 받을 수 없는 것 둘
#include <cstdio>

struct Incomplete;                       // 정의가 어디에도 없다

void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다

int main() {
    void* v = new int(5);
    delete v;                            // ★ void* 에 delete — 표준이 금지한다
    std::printf("여기까지 왔다\n");
    (void)kill;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor11.cpp -o ex (cc exit=0) =====
dtor11.cpp: In function ‘void kill(Incomplete*)’:
dtor11.cpp:6:28: warning: possible problem detected in invocation of ‘operator delete’ [-Wdelete-incomplete]
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |                            ^~~~~~~~
dtor11.cpp:6:23: warning: ‘p’ has incomplete type
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |           ~~~~~~~~~~~~^
dtor11.cpp:4:8: note: forward declaration of ‘struct Incomplete’
    4 | struct Incomplete;                       // 정의가 어디에도 없다
      |        ^~~~~~~~~~
dtor11.cpp:6:28: note: neither the destructor nor the class-specific ‘operator delete’ will be called, even if they are declared when the class is defined
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |                            ^~~~~~~~
dtor11.cpp: In function ‘int main()’:
dtor11.cpp:10:12: warning: deleting ‘void*’ is undefined [-Wdelete-incomplete]
   10 |     delete v;                            // ★ void* 에 delete — 표준이 금지한다
      |            ^
```

**`-pedantic-errors` 를 주면**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors dtor11.cpp -o ex (cc exit=0) =====
dtor11.cpp: In function ‘void kill(Incomplete*)’:
dtor11.cpp:6:28: warning: possible problem detected in invocation of ‘operator delete’ [-Wdelete-incomplete]
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |                            ^~~~~~~~
dtor11.cpp:6:23: warning: ‘p’ has incomplete type
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |           ~~~~~~~~~~~~^
dtor11.cpp:4:8: note: forward declaration of ‘struct Incomplete’
    4 | struct Incomplete;                       // 정의가 어디에도 없다
      |        ^~~~~~~~~~
dtor11.cpp:6:28: note: neither the destructor nor the class-specific ‘operator delete’ will be called, even if they are declared when the class is defined
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |                            ^~~~~~~~
dtor11.cpp: In function ‘int main()’:
dtor11.cpp:10:12: warning: deleting ‘void*’ is undefined [-Wdelete-incomplete]
   10 |     delete v;                            // ★ void* 에 delete — 표준이 금지한다
      |            ^
===== clang++ -std=c++20 -Wall -Wextra -pedantic-errors dtor11.cpp -o ex (cc exit=1) =====
dtor11.cpp:6:28: warning: deleting pointer to incomplete type 'Incomplete' may cause undefined behavior [-Wdelete-incomplete]
    6 | void kill(Incomplete* p) { delete p; }   // 불완전 타입 — 소멸자를 못 부른다
      |                            ^      ~
dtor11.cpp:4:8: note: forward declaration of 'Incomplete'
    4 | struct Incomplete;                       // 정의가 어디에도 없다
      |        ^
dtor11.cpp:10:5: error: cannot delete expression with pointer-to-'void' type 'void *' [-Werror,-Wdelete-incomplete]
   10 |     delete v;                            // ★ void* 에 delete — 표준이 금지한다
      |     ^      ~
1 warning and 1 error generated.
```

**왜 그런가**

| 코드 | 표준 | g++ `-pedantic` | g++ `-pedantic-errors` | clang `-pedantic-errors` |
|---|---|---|---|---|
| `delete v;`(`void*`) | ★★★ **ill-formed** | 경고 · exit 0 | ★★★ **경고 · exit 0** | ★★ **error · exit 1** |
| `delete p;`(불완전 타입) | **UB** | 경고 | 경고 | 경고 |

- ★★★ **`delete` 의 피연산자는 「객체 타입에 대한 포인터」라야 한다.** `void` 는 객체 타입이 아니므로\
  `delete v;` 는 **표준이 금지한 코드**다. 그런데 **g++ 는 `-pedantic-errors` 를 줘도 경고에서 멈추고 `cc exit=0`** 이다.
- ★★★ **clang 은 같은 플래그에서 에러로 올린다**(`cc exit=1`). **한 컴파일러에서 본 것을 플래그의 성질로 일반화하면 안 된다** —\
  [13번](../13-constructors-member-init-list-and-delegating/) (8)의 `-fpermissive` 가 같은 집안이고,\
  **거기는 플래그를 켜야 통과했는데 여기는 아무것도 안 켜도 통과한다.**
- ★★ **불완전 타입 쪽은 ill-formed 가 아니라 UB** 다 — 그래서 **둘 다 경고에서 멈춘다.**\
  g++ 의 `note` 가 무엇이 안 불리는지 적는다 — **소멸자도, 그 클래스 전용 `operator delete` 도 안 불린다.**
- ★ **그래서 `cc exit=0` 은 세 가지를 뜻할 수 있다** — **맞는 코드 · UB · ill-formed.**

### 10. 다른 주제와 잇기

- **「선언 순서로 초기화된다」의 정본**은 [13번](../13-constructors-member-init-list-and-delegating/) (2)다.\
  ★ 여기서는 그것이 **한 글자도 어긋나지 않고 뒤집힌다** — 파괴는 **선언 역순**이고, 기반은 **맨 마지막**이다.
- **「가상 소멸자를 언제 붙이나」의 설계 판**은 목록의 **20번 주제**다.\
  여기(14번)는 **안 붙였을 때 실제로 무엇이 일어나는가**까지만 본다.
- 「**소멸자를 적으면 이동이 사라진다**」의 정본은 목록의 **18번 주제**(0/3/5의 법칙)이고,\
  그 실측은 [13번](../13-constructors-member-init-list-and-delegating/) (7)에 있다.
- ★ **소멸자가 없는 언어**는 **라벨과 `goto`** 로 같은 일을 한다 —\
  C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/)).\
  ★★ 그쪽의 결론은 「**분기가 아니라 중복을 줄인다**」였고, C++ 판의 대조는 [15번](../15-raii-resources-as-types/) (7)에 있다.
- ★★ **러스트의 `Drop` 과 갈리는 한 가지** — 러스트는 **이동한 값이 원본 자리에서 `drop` 되지 않는다**는 것을\
  컴파일러가 강제한다. C++ 는 **이동해도 원본이 여전히 파괴되고**, 그래서 「**빈 껍데기도 안전하게 파괴되는 소멸자**」를\
  사람이 직접 써야 한다([15번](../15-raii-resources-as-types/) (4)).\
  Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))이 정본이다.
- ★★ **C# 이 `IDisposable`/`using` 을 따로 둔 이유** — C# 의 파괴 시점은 **GC 가 정한다.**\
  메모리는 그것으로 충분하지만 **파일·락·소켓은 「언젠가」로는 안 되므로**,\
  **결정적 해제를 문법으로 하나 더 얹은 것**이 `using` 이다.\
  C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **1번**([`01-value-types-and-reference-types/`](../../../csharp/syntax/01-value-types-and-reference-types/))과 **37번 주제**가 그 자리다.

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `dtor01.cpp` 파괴 순서 전수 | g++ 1회(6판) | ★★★ 지역·멤버 **선언 역순** · 기반 **마지막** · ★★ `vector` 는 **앞에서부터** |
| `dtor02.cpp` 되감기 | g++ 1회 | ★★ `[파괴]` **4줄** 전부 돌고 그다음 `[catch]` |
| `dtor03.cpp` 소멸자에서 던짐 | g++ 1회 | ★★★ `terminate` · **`cc exit=0` · `run exit=134`** · 경고 1건 |
| `dtor04.cpp` `noexcept` | g++ 1회(6줄) | `Plain` **1** · `Marked` 1 · `Loud` **0** · `string`/`vector` 1 |
| `dtor05.cpp` 가상 아닌 소멸자 | g++ 1회 + ASan 1회 | ★★★ `~DerNV` **0회** · `run exit=0` · 경고 **g++ 0 · clang 0** · ASan **`new-delete-type-mismatch`** |
| `dtor06.cpp` 경고 갈림 | g++ · clang 각 1회 | ★★ 가상 함수 **있는** 쪽만 경고 1건 · 없는 쪽 **0건** |
| `dtor07.cpp` `delete` 대 `delete[]` | g++ 1회 + ASan 1회 | ★★ 소멸자 **1회만** · `run exit=134` · 경고 g++ 1 · clang 1 · ASan **`bad-free`** |
| `dtor08.cpp` 임시 수명 | g++ · clang 각 1회 | ★★★ **만드는 순서가 갈렸다** · 파괴는 **양쪽 다 만든 역순** · `-Wdangling-gsl` **clang 만 1건** |
| `dtor09.cpp` `static` | g++ 1회 | ★★ `main` **뒤** 파괴 · 구성 역순 · 함수 지역 `static` 생성 **1줄** |
| `dtor10.cpp` `std::_Exit` | g++ 1회 | ★★★ `[파괴]` **0줄** · `run exit=0` |
| `dtor11.cpp` ill-formed `delete` | g++ 3회 · clang 1회 | ★★★ `void*` `delete` — g++ **`-pedantic-errors` 로도 `cc exit=0`** · clang **`cc exit=1`** |
| `dtor12.cpp` 형태 | g++ 1회 | `area = 9` · `~Square` → `~Handle` |
| `dtor13.cpp` 금지 사례 | g++ 1회 | **에러 6건** |
| 경고 개수 탐침 | g++ 5회 · clang 4회 | ★★★ **답한 것 7 · 침묵한 것 2** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · libstdc++ · ASan)에서만** 그렇다.

- ★★ **경고 개수와 경고 이름 전부**(`-Wdelete-non-virtual-dtor` 대 `-Wdelete-non-abstract-non-virtual-dtor`).
- ★★ **`std::vector` 가 원소를 앞에서부터 파괴하는 것** — 표준은 순서를 정하지 않는다.
- ★★ **함수 인자로 쓰인 임시를 만드는 순서** — 미명시이고 **두 컴파일러가 실제로 갈렸다.**
- ★★ **`-pedantic-errors` 가 `void*` `delete` 를 에러로 올리는지** — clang 만 그렇다.
- ★ **ASan 리포트의 PID·주소·`SUMMARY` 의 소스 경로** · **진단 문구 전부** · `run exit=134` 가 SIGABRT 라는 것.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **지역 객체가 선언 역순으로, 멤버가 선언 역순으로, 기반 클래스가 마지막으로** 파괴되는 것.
- **소멸자 본문이 멤버 파괴보다 먼저** 도는 것.
- **되감기에서 지나온 프레임의 지역 객체가 전부** 파괴되는 것.
- **임시가 전체 식의 끝에서** 파괴되고, **`const` 참조에 묶이면 그 참조만큼 사는** 것.
- **`static` 이 구성 역순으로, `main` 이 끝난 뒤** 파괴되는 것.
- **소멸자가 기본으로 `noexcept` 이고, 던지면 `std::terminate`** 인 것(C++11부터).
- **`std::_Exit` 가 소멸자를 하나도 돌리지 않는** 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ **3번** — 가상 아닌 소멸자로 다형적 삭제. 근거로 쓰는 것은 「**`~DerNV` 로그가 없다**」와\
  「**ASan 이 `new-delete-type-mismatch` 라고 불렀다**」뿐이다. **어떤 바이트가 어떻게 남는지는 싣지 않았다.**
- ★★ **4번** — `new[]`/`delete` 짝 어긋남. `munmap_chunk(): invalid pointer` 는 **이 할당기의 메시지**다.
- ★ **6번 `(3)`** — `c_str()` 댕글링. **`p` 가 가리키는 값은 읽지 않았다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-std=c++98`·`c++11`·`c++17` 판**(전부 `-std=c++20`) ·\
  ★ **`-O1`\~`-O3`·`-Os` 판**(이 문서의 로그는 **기본 최적화 판**의 것이다) ·\
  ★ **번역 단위가 둘 이상일 때의 `static` 구성 순서** · ★ **`std::exit` 와 `atexit`**(`_Exit` 만 던졌다) ·\
  ★ **`std::deque`·`std::list`·`std::map` 의 원소 파괴 순서**(`vector` 만 봤다) ·\
  ★ **UBSan**(`-fsanitize=undefined`) — 이 주제의 UB 셋은 **ASan 이 보는 종류**라 ASan 만 붙였다 ·\
  ★ **소멸자를 명시적으로 두 번 부르는 판**(`p->~D(); delete p;`).
- **못 잰 것** — ★★★ **「가상 소멸자가 얼마나 비싼가」.**\
  이 문서가 센 것은 **소멸자가 몇 번 돌았나까지**다. vtable 포인터가 더해지는 것은 `sizeof` 로 볼 수 있지만\
  **가상 호출 한 번의 값**은 **벤치마크 하네스가 따로 필요하다.**
- ★ 「**부적용인 창**」 — **진단의 `(행,열)`.** 파괴 순서는 **소스의 열이 아니라 실행 시점**이 정하므로\
  열로 가를 것이 없다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **g++·clang 이 「가상 함수 없는 기반의 다형적 삭제」를 경고하기 시작했는지**(3번·8번 — 지금은 **둘 다 0건**).
- ★★ **g++ 가 `-Wdangling-gsl` 류를 붙였는지**(6번 — 지금은 **0건**, clang 만 1건).
- ★★ **g++ 가 `void*` `delete` 를 `-pedantic-errors` 에서 에러로 올렸는지**(9번 — 지금은 **`cc exit=0`**).
- ★ **`std::vector` 의 원소 파괴 순서**(1번 — 지금은 **앞에서부터**) — libstdc++ 가 바꾸면 움직인다.
- ★ **경고 개수**(8번의 3건·2건 등) — 진단을 합치거나 쪼개면 움직인다.
