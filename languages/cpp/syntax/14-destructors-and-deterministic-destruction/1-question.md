# cpp/syntax/14 — 소멸자와 결정적 파괴 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **줄 순서를 맞히는 것**이 절반이다 — 「역순이다」로 뭉개지 말고
> **어느 줄 다음에 어느 줄이 오는지**를 적어라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★ **네 번째 창은 「종료 코드」다**(4·5번). `cc exit` 과 `run exit` 을 갈라서 답해야 한다.
> ★ **「부적용인 창」이 있다** — 진단의 `(행,열)`. 파괴 순서는 **소스의 열이 아니라 실행 시점**이 정해
> 열로 가를 것이 없다. **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> 선행 — [12번](../12-class-basics-members-access-and-this/)·[13번](../13-constructors-member-init-list-and-delegating/)이 이 주제의 바로 앞이고,
> 형제 [`09번`](../09-rvalue-references-move-and-forward/)·[`11번`](../11-choosing-parameter-passing/)이 로그·계수 방식의 뿌리다.
> 이어지는 것 — [15번](../15-raii-resources-as-types/)이 **이 시점을 자원 관리에 쓰는 법**을 답한다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 여섯 자리에서 무엇이 언제 사라지나 (예측)

```cpp
/* dtor01.cpp */
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
```

- `(1)` 의 **파괴 세 줄 순서**를 맞힐 수 있는가?
- ★★ `(2)` 의 **파괴 다섯 줄 순서**는? — `~Derived()` 본문·파생 멤버 둘·`~Base()` 본문·기반의 멤버.
- ★★ `(3)` 의 **vector 원소 세 줄**은 어느 순서인가 — 그리고 **그 순서는 표준이 정한 것인가**?
- `(4)` 의 `[파괴] 임시` 는 `이 줄은 임시가 사라진 뒤다` 의 **앞인가 뒤인가**?
- ★ `(5)` 에서 `참조에 묶인 임시` 는 어디서 죽는가?
- ★★ `전역 static` 의 **생성 줄**과 **파괴 줄**은 각각 출력의 어디에 있는가?

### 2. ★★ 세 층을 지나 던지면 (예측)

```cpp
/* dtor02.cpp */
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
```

- **`[파괴]` 줄이 몇 개** 찍히고, **어느 순서**인가?
- ★ `[catch]` 줄은 그 소멸자들의 **앞인가 뒤인가**?
- ★ `이 줄은 안 돈다` 는 찍히는가?
- ★★ 이 소스가 **마커를 전부 `stderr` 로 찍은** 이유는 무엇인가?

### 3. ★★★ 기반 포인터로 지우면 (예측)

```cpp
/* dtor05.cpp */
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
```

- `(1)` 에서 **`[파괴]` 줄이 몇 개** 찍히는가 — 그리고 **어느 것**인가?
- ★★★ `run exit` 은 얼마인가? 경고는 **g++·clang 각각 몇 건**인가?
- ★★★ `-fsanitize=address` 를 붙이면 **무엇이라는 이름의 오류**가 나오는가 — 누수인가 아닌가?
- ★★ 기반 클래스에 **가상 함수가 하나라도 있으면** 경고가 달라지는가?

### 4. ★★ `new D[3]` 을 `delete` 로 놓으면 (예측)

```cpp
/* dtor07.cpp */
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
```

- **`[파괴]` 줄이 몇 개** 찍히는가?
- ★★ `(2) 여기까지 오나` 는 찍히는가 — **`run exit`** 은 얼마인가?
- ★ g++ 는 경고하는가? 경고 이름은?
- ★ ASan 은 이것을 **무엇이라고 부르는가** — 3번의 이름과 같은가?

### 5. ★ 소멸자에서 던지면 (예측)

```cpp
/* dtor03.cpp */
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
```

- `[catch] 여기로 오나?` 와 `(2) 여기까지 오나?` 중 **찍히는 것**이 있는가?
- ★★ **`cc exit`** 과 **`run exit`** 은 각각 얼마인가?
- ★ 컴파일러가 미리 말해 주는가 — 경고 이름과 `note:` 줄은?
- ★ 소멸자에 `noexcept` 를 **안 적어도** `noexcept` 인가 — **언제부터**인가?

### 6. ★★ 한 식 안에 임시 셋 (예측)

```cpp
/* dtor08.cpp */
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
```

- `(1)` 에서 **생성 세 줄**과 **파괴 세 줄**의 순서를 맞힐 수 있는가?
- ★★★ 그중 **g++ 와 clang 이 갈리는 칸**은 어디인가 — 그리고 **갈리지 않는 성질**은 무엇인가?
- ★ `(3)` 에서 **g++ 와 clang 중 경고하는 쪽**은 어디이고 경고 이름은 무엇인가?
- ★ 이 문서가 `p` 가 **가리키는 값을 읽지 않은** 이유는?

### 7. ★ 프로그램이 끝나면 정리가 되는가 (경계)

- `static` 객체는 **`main` 의 마지막 줄보다 먼저 죽는가 나중에 죽는가**?
- ★ 함수 지역 `static` 을 **두 번 부르면 생성 로그가 몇 줄**인가 — 한 번도 안 부르면?
- ★★★ `std::_Exit(0)` 으로 나가면 `[파괴]` 줄이 **몇 개**인가 — 그때 `run exit` 은?
- ★ 그래서 「프로그램이 끝나면 소멸자가 다 돈다」는 **어디까지 참인가**?

### 8. ★★ 경고를 누가 보나 (경계)

- **파괴 순서 자체**를 말해 주는 컴파일러 플래그가 있는가?
- ★★★ 탐침 아홉 중 **침묵한 둘**은 무엇인가?
- ★★ 같은 사건인데 **경고 개수가 컴파일러마다 다른** 예를 들 수 있는가?
- ★ `c_str()` 댕글링을 **어느 컴파일러가** 보는가?

### 9. ★★ `cc exit=0` 이 뜻하지 않는 것 (경계)

- `void*` 에 `delete` 를 하면 **표준은 뭐라 하고**, g++ 는 **어떤 진단과 종료 코드**를 내는가?
- ★★★ **`-pedantic-errors` 를 줘도 살아나는가** — clang 은?
- ★★ 불완전 타입 포인터를 `delete` 하는 것은 **ill-formed 인가 UB 인가** — 무엇이 안 불리는가?
- ★ 그래서 `cc exit=0` 은 **몇 가지**를 뜻할 수 있는가?

### 10. 다른 주제와 잇기 (연결)

- **「선언 순서로 초기화된다」의 정본**은 몇 번 주제이고, 여기서 그것이 어떻게 뒤집히는가?
- **「가상 소멸자를 언제 붙이나」의 설계 판**은 몇 번 주제인가?
- 「**소멸자를 적으면 이동이 사라진다**」의 정본은 몇 번인가?
- ★ **소멸자가 없는 언어**가 같은 문제를 어떻게 푸는가 — 어느 갈래 몇 번인가?
- ★★ **러스트의 `Drop`** 과 C++ 소멸자가 **갈리는 한 가지**는 무엇인가 — 어느 갈래 몇 번인가?
- ★★ **C# 이 `IDisposable`/`using` 을 따로 둔 이유**를 이 주제의 말로 설명할 수 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
