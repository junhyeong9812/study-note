# cpp/syntax/14 — 소멸자와 결정적 파괴 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 소멸자](https://en.cppreference.com/w/cpp/language/destructor) · [cppreference — 객체 수명](https://en.cppreference.com/w/cpp/language/lifetime) · [cppreference — `delete` 식](https://en.cppreference.com/w/cpp/language/delete) · [cppreference — 저장 기간](https://en.cppreference.com/w/cpp/language/storage_duration) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html) · [AddressSanitizer](https://github.com/google/sanitizers/wiki/AddressSanitizer)
> **실행 검증** — 이 문서의 모든 출력·진단·sanitizer 리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`dtor01.cpp` \~ `dtor13.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **표준 출력과 표준 오류를 한 블록에 섞지 않았다.** sanitizer 가 `abort()` 로 죽이면\
> **버퍼에 남은 표준 출력이 통째로 사라지므로**, ASan 을 붙이는 판의 마커는 전부 `std::fprintf(stderr, …)` 로 찍었다\
> ((5)(6)(7)의 소스에 그렇게 적혀 있다). ★ ASan 리포트를 자른 블록은 **자르는 명령을 배너에 적었다.**
> **버전** — 소멸자 자체는 **C++98부터**. **소멸자가 기본으로 `noexcept` 인 것은 C++11부터**((7)) ·\
> `= default`/`= delete` 도 **C++11부터** · `std::_Exit` 는 **C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **12 → 13 → 14 → 15 는 한 사슬이다** — [12번](../12-class-basics-members-access-and-this/)이 **그릇**을,\
> [13번](../13-constructors-member-init-list-and-delegating/)이 **채우는 법**을 답했다. **여기 14 가 「언제 비워지나」에 답하고**,\
> [15번](../15-raii-resources-as-types/)이 **그 시점을 자원 관리에 쓰는 법**을 답한다.\
> ★★ **[13번](../13-constructors-member-init-list-and-delegating/) (2)의 「선언 순서로 초기화된다」가 여기서 뒤집힌다** — 파괴는 그 **역순**이다((1)).
> **경계** — 「**가상 소멸자를 언제 붙이나**」의 설계 판은 목록의 **20번 주제**가 정본이고,\
> 여기서는 **안 붙였을 때 실제로 무엇이 일어나는가**만 던져 본다((5)).\
> 「0/3/5의 법칙」은 **18번**, 「이동 후 상태」는 **17번**, 「`unique_ptr`」은 **26번**,\
> 「예외와 스택 되감기」 자체는 **51번**, 「수명 연장 규칙의 전모」는 **30번 주제**가 정본이다.\
> **대비** — C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/))은 **소멸자가 없는 언어**가 같은 문제를 라벨로 푸는 법이고,\
> Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/))의 `Drop` 은 **여기와 같은 결정적 파괴**다.\
> C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **1번**([`01-value-types-and-reference-types/`](../../../csharp/syntax/01-value-types-and-reference-types/))은 **정반대** — GC 가 언제 치울지 프로그램이 모른다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**(`==1138999==`)·주소·`BuildId` | ★★★ **로그가 찍힌 순서** — 이 주제의 답 자체다 |
> | 두 컴파일러의 **진단 문구**와 경고 이름 | ★★★ **소멸자가 몇 번 돌았나**(`[파괴]` 줄 수) |
> | 객체의 주소값 · 실행 시간 | ★★ **`cc exit` 와 `run exit`**(갈라 적었다) · **경고 개수** |
> | ★ **임시 객체가 만들어진 순서** — **g++ 와 clang 이 달랐다**((4)) | ★★ **ASan 이 뭐라고 부르는가**(`new-delete-type-mismatch`·`bad-free`·`double-free`) |
> | — | ★ **임시 객체가 파괴된 순서** — 만든 순서의 역순이라는 **성질**은 두 컴파일러에서 같았다 |

## 한눈에 — 쉽게 말하면

**C++ 의 파괴는 「스코프를 나가는 순간」이다.** 청소부를 기다리지 않는다.

식탁에 접시를 쌓는다고 하자.\
접시를 올린 순서가 `지역 1 → 지역 2 → 지역 3` 이면, 치우는 순서는 **반드시 `3 → 2 → 1`** 이다.\
맨 위부터 집어야 하기 때문이고, 그것은 **예의가 아니라 물리**다.

C++ 의 소멸자가 정확히 그렇다. **쌓인 역순으로, 그 자리에서, 빠짐없이** 돈다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 접시는 맨 위부터 치운다 | ★★★ **스코프 역순 파괴** | (1) |
| 큰 접시 안에 담긴 작은 접시가 먼저 | ★★ **멤버가 먼저, 기반 클래스가 마지막** | (1) |
| 식사가 엎어져도 접시는 치운다 | ★★★ **예외 되감기에서도 전부 돈다** | (2) |
| 식당 문을 닫을 때 치우는 접시 | ★ **`static` 은 `main` 이 끝난 뒤** | (3) |
| 잠깐 든 접시는 손을 놓는 순간 | ★ **임시 객체는 전체 식의 끝** | (4) |
| ★★★ **뚜껑만 보고 치우면 속을 못 치운다** | ★★★ **가상 소멸자가 없으면 파생 쪽이 안 돈다** | (5) |
| 셋을 담았는데 하나만 치우면 | ★★ **`new[]` 를 `delete` 로 놓으면** | (6) |
| 치우다 그릇을 던지면 식당이 닫힌다 | ★ **소멸자에서 던지면 `std::terminate`** | (7) |

> **결정적 파괴(deterministic destruction)** — **언제 파괴되는지가 코드만 보고 정해지는 것**.\
> 예: `{ D x; }` 의 `x` 는 닫는 중괄호에서 **반드시** 파괴된다. 「언젠가」가 아니다.

> **스택 되감기(stack unwinding)** — 예외가 지나가는 길의 지역 객체를 **역순으로 파괴하며 프레임을 걷어내는 것**.\
> 예: (2)에서 `inner` 의 `b`·`a` → `middle` 의 `m` → `main` 의 `o` 순으로 파괴됐다.

```text
   결정적 파괴 (C++)                        GC (C# · Java)

   {                                        {
       D x;   <- 여기서 생긴다                  var x = new D();
       ...                                      ...
   }          <- ★ 여기서 반드시 죽는다      }   <- ★ 아무 일도 안 일어난다
                                                    (GC 가 언제 올지 모른다)
   +-----------------+                      +-----------------+
   | 시점을 코드가 정한다 |                      | 시점을 런타임이 정한다 |
   +-----------------+                      +-----------------+
         |                                          |
   자원 해제를 여기에 얹을 수 있다             자원 해제를 여기에 못 얹는다
         |                                          |
       RAII (15번)                            IDisposable / using
```

- ★★★ **C# 이 `IDisposable`/`using` 을 따로 두는 이유가 저 오른쪽 그림이다** — 메모리는 GC 가 맡지만\
  **파일·락·소켓은 「언젠가」로는 안 되기 때문**에 결정적 해제 문법을 하나 더 얹은 것이다\
  (C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **37번**이 정본).

## 이 주제가 답하려는 질문

1. **무엇이 언제 파괴되나** — 스코프·멤버·기반·컨테이너·임시·`static` 을 **한 줄로 세울 수 있나**((1)(3)(4)).
2. **예외가 지나가도 도나** — 그리고 **안 도는 길은 있나**((2)(3)).
3. **가상 소멸자를 빠뜨리면 「무엇이」 일어나나** — 「UB 다」 말고 **실제 출력으로**((5)).
4. **소멸자에서 던지면 무엇이 되나** — 그리고 **왜 기본이 `noexcept` 인가**((7)).

## 동작 방식

### (0) 이 주제가 쓰는 네 창

「언제 파괴되나」는 눈에 안 보인다. 창 넷을 갈라 쓴다.

```text
① 생성·파괴 로그          무엇이 몇 번, 어떤 순서로 돌았나     (1)(2)(3)(4)
② ASan 리포트             UB 가 「무엇으로」 드러나나          (5)(6)
③ 컴파일 진단과 경고 개수   같은 UB 를 누가 보고 누가 침묵하나   (5)(8)(9)
④ 종료 코드               terminate 인가 정상 종료인가        (6)(7)
```

- ★★★ **주력 창은 ①이다.** 파괴 순서는 **논쟁거리가 아니라 로그**다 — 이 주제는 **전수로 찍어** 답한다((1)).\
  ★ 이 로그 방식은 형제 [`13번`](../13-constructors-member-init-list-and-delegating/) (2)를 그대로 이어받은 것이고,\
  계수 방식의 뿌리는 형제 [`11번`](../11-choosing-parameter-passing/)의 `Probe` 다.
- ★★ **네 번째 창은 ④다.** (7)의 `run exit=134` 가 「`terminate` 가 불렸다」를 **말이 아니라 수로** 말해 준다.\
  **경고 0건이어도 종료 코드가 134면 그 프로그램은 죽은 것**이다.
- ★★★ **②가 없으면 (5)(6)은 「아무 일도 안 일어났다」로 보인다.** (5)는 **정상 종료(`run exit=0`)** 했다 —\
  ASan 을 붙여야 `new-delete-type-mismatch` 가 나온다. **「안 터졌다」는 「안전하다」가 아니다.**
- ★ 「**부적용인 창**」 — **진단의 `(행,열)`.** 05\~09 의 C# 형제들과 [12번](../12-class-basics-members-access-and-this/)이 쓴 그 창은\
  **결합 방향·파싱 우선순위**를 가르는 데 쓰는 것인데, 파괴 순서는 **소스의 열이 아니라 실행 시점**이 정한다.\
  **「안 쟀다」가 아니라 「잴 것이 없다」다.**

### (1) ★★★ 파괴 순서 전수 — 이 주제의 본체

**언제 쓰나** — 언제나. 아래 여섯 판이 C++ 프로그램에서 객체가 사라지는 **모든 자리**다.

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

```text
   ① 같은 스코프에 셋                       ② 멤버와 기반 클래스

   생성  지역 1 -> 지역 2 -> 지역 3          생성  기반의 멤버
   파괴  지역 3 -> 지역 2 -> 지역 1                -> Base()  본문
         ^^^^^^^^^^^^^^^^^^^^^^^                  -> 파생 멤버 1 -> 파생 멤버 2
         ★ 쌓인 역순                              -> Derived() 본문
                                            파괴  ~Derived() 본문
                                                  -> 파생 멤버 2 -> 파생 멤버 1
                                                  -> ~Base() 본문 -> 기반의 멤버
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                  ★ 정확히 생성의 역순
```

```text
   ③ vector 원소 셋                         ④⑤ 임시 객체

   생성  벡터 0 -> 벡터 1 -> 벡터 2           pass(D{"임시"});
   파괴  벡터 0 -> 벡터 1 -> 벡터 2              생성 -> 파괴 -> 다음 줄
         ^^^^^^^^^^^^^^^^^^^^^^^               ^^^^^^^^^^^^ 전체 식의 끝
         ★ 앞에서부터다 (역순이 아니다)
                                             const D& r = D{"임시"};
   ⑥ static                                     -> 블록 끝까지 산다
   전역 static 은 main 보다 먼저 생기고            ^^^^^^^^^^^^^^^ 수명 연장
   main 이 끝난 뒤에 죽는다
```

그림 해설 (한 단계씩):

- ★★★ **지역 객체는 선언 역순으로 파괴된다** — `지역 3 → 지역 2 → 지역 1`. **예외가 없다.**
- ★★★ **멤버는 선언 역순, 기반 클래스는 맨 마지막**이다.\
  `~Derived()` **본문이 먼저** 돌고, 그다음 파생 멤버가 역순으로, 그다음 `~Base()` 본문, 마지막이 기반의 멤버다.\
  ★ [13번](../13-constructors-member-init-list-and-delegating/) (2)의 「선언 순서로 초기화된다」가 **여기서 한 글자도 어긋나지 않고 뒤집힌다.**
- ★★ **`std::vector` 는 앞에서부터 파괴한다**(`벡터 0 → 1 → 2`). **역순이 아니다** —\
  이것은 **표준이 순서를 정해 두지 않은 자리**이고, 지금 본 것은 **libstdc++ 의 선택**이다(아래 다섯 층 표).
- ★★ **`static` 객체는 `main` 이 끝난 뒤에 죽는다.** `(7) main 의 마지막 줄` 이 찍힌 **다음에**\
  `함수 지역 static` 과 `전역 static` 이 파괴됐다 — 자세한 순서는 (3).
- ★ **임시 객체는 전체 식의 끝에서 죽고**, `const` 참조에 묶으면 **그 참조의 수명까지 늘어난다** — 자세히는 (4).

**비용** — 0. 소멸자를 적지 않은 타입(`int` 같은)은 **아무 코드도 안 나온다.**

### (2) ★★ 예외가 지나가도 전부 돈다 — 되감기

**언제 쓰나** — 「이 경로에서도 해제가 되나?」가 걱정될 때마다. **[15번](../15-raii-resources-as-types/) 전체가 이 절 위에 서 있다.**

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

```text
   main ── try {  D o;
                  middle() ── D m;
                              inner() ── D a;  D b;
                                         throw!
                                            |
   되감기 ◄───────────────────────────────────┘
        b -> a  (inner 의 지역, 역순)
        m       (middle 의 지역)
        o       (main 의 try 블록 지역)
        -> catch 로 들어간다
```

- ★★★ **세 프레임을 지나오면서 소멸자 넷이 전부 돌았다.** 한 프레임 안에서는 **역순**이고,\
  프레임 사이에서도 **안쪽부터 바깥쪽으로** — 결국 **전체가 하나의 역순**이다.
- ★★★ **`[catch]` 줄이 소멸자들 뒤에 찍혔다** — 되감기가 **먼저** 끝나고 그다음에 처리기가 돈다.
- ★ **이 블록은 마커를 전부 표준 오류로 찍었다.** 표준 출력과 표준 오류를 섞으면\
  **파이프로 받을 때 순서가 뒤집히는 런타임이 있기 때문**이고, 그러면 이 절의 결론이 통째로 흔들린다.
- ★★ **되감기를 안 하는 길이 둘 있다** — **소멸자에서 다시 던져 `terminate` 로 가는 것**((7))과\
  **`std::_Exit` 로 나가는 것**((3)). 둘 다 이 문서에서 던져 봤다.

**비용** — 되감기 자체는 **예외가 났을 때만** 든다. 다만 **되감기를 할 수 있게 만드는 표**는 예외가 안 나도\
바이너리에 들어간다 — [15번](../15-raii-resources-as-types/) (7)에서 그 표를 세어 본다.

### (3) ★★ `static` 은 언제 죽나 — 그리고 안 죽는 길

**언제 쓰나** — 전역 로거·싱글턴·캐시를 둘 때. **「프로그램 끝에 정리되겠지」가 참인지** 확인하는 자리다.

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

- ★★★ **`static` 은 `main` 이 끝난 뒤에 파괴된다.** `main 의 마지막 줄` 다음에 `main 의 지역` 이 죽고,\
  **그다음** 함수 지역 `static` 과 전역이 죽었다.
- ★★★ **파괴 순서는 「구성이 끝난 역순」이다** — 전역 1 → 전역 2 → 함수 지역 `static` 순으로 구성됐고,\
  파괴는 **함수 지역 `static` → 전역 2 → 전역 1** 이었다.
- ★★ **함수 지역 `static` 은 「처음 부를 때」 생긴다** — `lazy()` 를 두 번 불렀는데 **생성 로그는 한 줄**이다.\
  그래서 **한 번도 안 부르면 생기지도 않고, 생기지 않았으면 파괴되지도 않는다.**
- ★ **한 번역 단위 안에서는 전역의 구성 순서가 적은 순서**다. **번역 단위가 둘 이상이면 그 순서가 미명시**이고,\
  그것이 「static 초기화 순서 문제」다 — 이 문서는 **한 파일만 돌렸으므로 그 판은 안 던져 봤다.**

그리고 **파괴가 아예 안 도는 길**이 있다.

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

- ★★★ **`std::_Exit` 로 나가면 소멸자가 하나도 안 돈다** — `[파괴]` 줄이 **0개**다.\
  `run exit=0` 이므로 **「정상 종료했다」와 「정리가 됐다」는 다른 말**이다.
- ★★ **`std::abort()`·`std::quick_exit()`·`std::terminate()` 도 같은 집안**이다.\
  (7)에서 `terminate` 를 실제로 밟아 보면 **그 뒤 줄이 안 찍히는 것**으로 같은 사실이 보인다.
- ★ **그래서 「소멸자에 중요한 일을 넣지 마라」가 나온다.** 파일 플러시·락 해제는 괜찮지만,\
  **「프로그램이 끝날 때 반드시 한 번」이 필요한 일**은 소멸자만으로 보장되지 않는다.

**비용** — 0. 다만 **`static` 파괴는 「다른 `static` 이 이미 죽었을 수 있는 시점」에 돈다**는 것이 위험이다.

### (4) ★★ 임시 객체는 언제 죽나 — 그리고 g++ 와 clang 이 갈리는 자리

**언제 쓰나** — `f(g(x))` 처럼 이름 없는 값이 끼는 식을 쓸 때. `c_str()` 사고가 여기서 난다.

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

★★ **같은 소스를 clang 으로 던지면 「만든 순서」가 다르다.**

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

```text
   int r = use(D{왼쪽}, D{오른쪽}) + D{셋째}.value();
                                                  ^ 전체 식의 끝(세미콜론)

   g++    : 만들기  오른쪽 -> 왼쪽 -> 셋째      파괴  셋째 -> 왼쪽 -> 오른쪽
   clang  : 만들기  왼쪽 -> 오른쪽 -> 셋째      파괴  셋째 -> 오른쪽 -> 왼쪽
            ^^^^^^^^^^^^^^^^^^^^^^^^           ^^^^^^^^^^^^^^^^^^^^^^^^^
            ★ 갈린다 (미명시)                  ★ 「만든 역순」이라는 성질은 같다
```

- ★★★ **인자를 만드는 순서는 미명시다.** 두 컴파일러가 실제로 갈렸다 — **여기에 결론을 세우면 안 된다.**
- ★★★ **그런데 「만든 역순으로 파괴된다」는 성질은 두 판에서 같았다.** 이것이 **근거로 쓸 수 있는 칸**이다.
- ★★ **임시는 세미콜론에서 죽는다**(`식이 끝났다` 가 파괴 뒤에 찍혔다). 「한 줄 안에서만 산다」가 아니라\
  「**전체 식(full-expression)이 끝날 때까지**」 산다.
- ★★★ **`const` 참조에 묶으면 수명이 늘어난다**(`참조가 붙잡은 임시` 가 블록 끝까지 살았다) —\
  **그런데 그 규칙은 「멤버를 가리키는 포인터」에는 안 붙는다.**\
  `std::string("…").c_str()` 의 결과는 **세미콜론에서 이미 죽은 메모리**를 가리킨다.
- ★★ **clang 만 그것을 경고한다** — `object backing the pointer will be destroyed at the end of the full-expression [-Wdangling-gsl]`.\
  **g++ 는 같은 줄에 대해 침묵했다**((9)의 개수표).
- ★ **그래서 이 문서는 `p` 를 읽지 않았다.** 읽는 것 자체가 UB 라 **값이 아니라 「널이 아니다」만** 싣는다.

**비용** — 0. 임시를 붙잡는 `const&` 는 **복사를 안 만들므로** 공짜다. 대신 **무엇을 붙잡았는지 헷갈리면 댕글링**이다.

### (5) ★★★ 가상 소멸자가 없는데 기반 포인터로 지우면 — 실제로 무엇이 일어나나

**언제 쓰나** — 상속을 쓰는 코드를 읽을 때마다. **이 주제에서 가장 조용한 사고**다.

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

```text
   BaseNV* p = new DerNV;   delete p;

   DerNV 가 잡은 32바이트 --+
                            |
   delete p 가 부르는 것   ~BaseNV 하나뿐  ★ ~DerNV 는 아예 안 불린다
                            |
                          32바이트가 그대로 남는다 (그리고 크기도 틀리게 놓는다)

   BaseV* q = new DerV;     delete q;      <- virtual 이 붙어 있으면
                          ~DerV -> ~BaseV  ★ 파생부터 제대로 돈다
```

- ★★★ **`~DerNV` 가 한 번도 안 불렸다.** 로그에 `[파괴] ~BaseNV` 만 있다 —\
  **`~DerNV` 가 놓기로 되어 있던 32바이트는 그대로 남는다.**
- ★★★ **그런데 프로그램은 `run exit=0` 으로 정상 종료했다.** 아무 경고도, 아무 에러도 없다.\
  ★★ **이것이 이 주제에서 가장 나쁜 자리다** — 「돌아갔다」가 아무것도 증명하지 못한다.
- ★★ **가상 소멸자가 있으면 `~DerV → ~BaseV`** 로 **파생부터** 돈다 — (1)의 역순 규칙 그대로다.

★★ **ASan 을 붙이면 비로소 보인다.**

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

- ★★★ **ASan 이 「누수」가 아니라 「타입 불일치」로 잡았다** — `new-delete-type-mismatch`.\
  `size of the allocated type: 8 bytes` 대 `size of the deallocated type: 1 bytes` —\
  **`DerNV` 로 8바이트를 잡아 놓고 `BaseNV` 로 1바이트를 놓으려 한 것**이다.
- ★★ **누수보다 먼저 이것이 터진다.** UB 의 실제 모습은 「32바이트가 샌다」 하나가 아니라\
  「**할당기가 다른 크기로 반환을 받는다**」이기도 하다.
- ★ **`run exit=1`** 이다(`ABORTING`). ASan 없이 돌린 판의 `run exit=0` 과 갈라 봐야 한다.

★★★ **경고가 나는 판과 안 나는 판이 갈린다.**

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

| 지우는 대상 | 가상 함수가 있나 | 소멸자가 가상인가 | g++ 경고 | clang 경고 | 실제로는 |
|---|---|---|---|---|---|
| `Poly*` → `DerPoly` | ★ **있다** | 아니다 | ★★ **1건** | ★★ **1건** | UB |
| `Plain*` → `DerPlain` | **없다** | 아니다 | ★★★ **0건** | ★★★ **0건** | ★★★ **똑같이 UB** |

- ★★★ **두 컴파일러 다 「가상 함수가 하나라도 있는 클래스」만 경고한다.**\
  가상 함수가 없는 기반 클래스로 파생 객체를 지우는 것은 **똑같이 UB 인데 아무도 말하지 않는다.**
- ★★ **(5) 맨 위의 `dtor05.cpp` 가 바로 그 판이다** — `BaseNV` 에는 가상 함수가 없으므로 **경고 0건**이다((9)).
- ★ 경고 이름은 g++ `-Wdelete-non-virtual-dtor` · clang `-Wdelete-non-abstract-non-virtual-dtor` 로 **다르다.**

**비용** — `virtual ~Base() = default;` 한 줄이 **vtable 포인터 8바이트**(이미 가상 함수가 있으면 0)와\
**가상 호출 한 번**을 더한다. **설계 판단의 정본은 목록의 20번 주제**다.

### (6) ★★ `delete` 대 `delete[]` — 소멸자가 몇 번 도나

**언제 쓰나** — `new[]` 가 있는 옛 코드를 읽을 때. **[15번](../15-raii-resources-as-types/)을 읽고 나면 둘 다 안 쓰게 된다.**

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

- ★★★ **소멸자가 셋 중 하나만 돌았다**(`[파괴] D 0`). `delete[]` 가 아니면 **개수를 모른다.**
- ★★★ **그리고 프로그램이 죽었다** — `munmap_chunk(): invalid pointer`, **`run exit=134`**.\
  배열 할당은 앞에 개수를 적어 두는 구현이 흔해 **포인터 자체가 어긋난다.**
- ★★ **g++ 가 이것은 경고한다** — `-Wmismatched-new-delete` **1건**(clang 도 1건 — (9)).\
  (5)와 달리 **여기는 도구가 본다.**

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

- ★★ **ASan 은 `bad-free` 라고 부른다** — `attempting free on address which was not malloc()-ed`.\
  (5)의 `new-delete-type-mismatch` 와 **다른 이름**이다. **이름이 곧 무엇이 어긋났는지다.**
- ★ **여기서도 `[파괴] D 0` 한 줄만 찍혔다** — sanitizer 를 붙여도 **소멸자는 여전히 한 번만** 돈다.

**비용** — `delete[]` 를 제대로 쓰면 0. 그러나 **`std::vector` 를 쓰면 이 선택 자체가 사라진다.**

### (7) ★ 소멸자에서 던지면 — 그리고 왜 기본이 `noexcept` 인가

**언제 쓰나** — 소멸자에서 `fclose`·`commit`·`flush` 처럼 **실패할 수 있는 일**을 할 때.

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

- ★★★ **`catch` 로 안 간다.** `[catch] 여기로 오나?` 도 `(2) 여기까지 오나?` 도 **한 줄도 안 찍혔다.**\
  `terminate called after throwing an instance of 'std::runtime_error'` 로 **프로그램이 죽었다**(`run exit=134`).
- ★★★ **컴파일러가 미리 말해 준다** — `warning: 'throw' will always call 'terminate' [-Wterminate]` 와\
  `note: in C++11 destructors default to 'noexcept'`. **경고 문구가 곧 규칙 설명**이다.
- ★★ **`cc exit=0` 인데 `run exit=134`** 다 — **컴파일이 통과한 것과 프로그램이 사는 것은 다른 이야기**다.

★ **소멸자가 정말로 `noexcept` 인지 물어봤다.**

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

| 적은 것 | `noexcept(소멸자 호출)` | 읽는 법 |
|---|---|---|
| `~Plain() {}` | ★ **1** | **안 적어도 `noexcept` 다** |
| `~Marked() noexcept {}` | 1 | 적어도 같다 |
| `~Loud() noexcept(false) {}` | ★★ **0** | ★★ **직접 꺼야 꺼진다** |
| `std::string`·`std::vector<int>` | 1 | 표준 타입도 그렇다 |

- ★★★ **C++11 부터 소멸자는 적지 않아도 `noexcept` 다.** 그래서 소멸자 안의 `throw` 는\
  **예외를 밖으로 내보내는 것이 아니라 `std::terminate` 를 부르는 것**이 된다.
- ★★ **`noexcept(false)` 로 열 수는 있다**(`Loud` 가 0이다). 그러나 **그 타입을 `vector` 에 넣는 순간**\
  되감기 중 파괴에서 같은 문제가 되살아난다 — 정본은 목록의 **53번 주제**다.
- ★ **그래서 규칙은 하나다** — **소멸자에서 던지지 않는다.** 실패를 알려야 하면\
  **`close()` 같은 명시 메서드를 따로 두고**, 소멸자는 **조용히 최선을 다하는 자리**로 남긴다.

**비용** — 0. 대신 **소멸자에서 실패를 보고할 방법이 없다**는 설계 제약이 생긴다.

### (8) ★★ 종료 코드가 0인데 ill-formed — `delete` 가 받을 수 없는 것

**언제 쓰나** — 「빌드가 통과하니 맞는 코드다」라고 말하고 싶을 때.

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

★★ **`-pedantic-errors` 를 줘 봤다 — 그리고 두 컴파일러가 갈렸다.**

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

| 코드 | 표준이 뭐라 하나 | g++ `-pedantic` | g++ `-pedantic-errors` | clang `-pedantic` | clang `-pedantic-errors` |
|---|---|---|---|---|---|
| `delete v;`(`void*`) | ★★★ **ill-formed** — `delete` 의 피연산자는 **객체 포인터**라야 한다 | 경고 · **exit 0** | ★★★ **경고 · exit 0** | 경고 · exit 0 | ★★ **error · exit 1** |
| `delete p;`(불완전 타입) | **UB** — 소멸자도 전용 `operator delete` 도 안 불린다 | 경고 | 경고 | 경고 | 경고 |

- ★★★ **`void*` 에 `delete` 는 표준이 금지한 것인데 g++ 는 `-pedantic-errors` 로도 통과시킨다**(`cc exit=0`).\
  [13번](../13-constructors-member-init-list-and-delegating/) (8)의 `-fpermissive` 와 **같은 집안의 두 번째 사례**다 —\
  다만 저쪽은 **플래그를 켜야** 통과했고, **여기는 아무것도 안 켜도 통과한다.**
- ★★★ **clang 은 `-pedantic-errors` 에서 에러로 바꾼다**(`cc exit=1`). 「**한 컴파일러에서 본 것을 플래그의 성질로 일반화하지 마라**」가\
  여기서도 그대로 성립한다.
- ★★ **불완전 타입 쪽은 ill-formed 가 아니라 UB 다** — 그래서 **둘 다 경고에서 멈춘다.**\
  g++ 의 `note` 가 무엇이 빠지는지 정확히 적어 준다 — `neither the destructor nor the class-specific 'operator delete' will be called`.
- ★ **그래서 「우리 빌드는 경고만 난다」는 「표준에 맞다」가 아니다.** 경고 하나가 **표준 위반**일 수 있다.

**비용** — `void*` 를 지우지 않으면 0. **`void*` 로 자원을 들고 다니지 않는 것**이 애초의 처방이고, 그것이 [15번](../15-raii-resources-as-types/)이다.

### (9) 경고를 누가 보나 — 탐침 아홉

「경고가 안 났다」를 산문으로 적으면 **안 물어본 것과 물었는데 조용한 것이 구분되지 않는다.**\
그래서 **탐침 아홉 개**(g++ 5 · clang 4)에 플래그를 똑같이 걸어 개수를 찍었다.

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

| 사건 | g++ 경고 | clang 경고 | 실제로는 |
|---|---|---|---|
| 소멸자에서 던짐 | **1** | — | `terminate` · `run exit=134` |
| ★★★ **가상 아닌 소멸자**(가상 함수 없는 기반) | ★★★ **0** | ★★★ **0** | ★★★ **UB — 파생 소멸자가 안 돈다** |
| 가상 아닌 소멸자(가상 함수 있는 기반) | **1** | **1** | UB |
| `new[]` 를 `delete` 로 | **1** | **1** | `run exit=134` |
| ★★ **`void*` 에 `delete`**(+ 불완전 타입) | **3** | **2** | ★★ **ill-formed 인데 `cc exit=0`** |
| ★★ **`c_str()` 이 가리키는 임시**((4)) | ★★★ **0** | ★ **1**(`-Wdangling-gsl`) | UB |

- ★★★ **탐침 아홉 중 답한 것 일곱, 침묵한 것 둘**이다. 침묵한 둘이 **이 주제에서 가장 위험한 둘**이다 —\
  **가상 함수가 없는 기반 클래스로 지우는 것**과 **g++ 에서 `c_str()` 댕글링**.
- ★★ **같은 사건인데 개수가 다르다**(`void*` 판: g++ 3 · clang 2). **「경고 N건」은 컴파일러를 밝혀야 뜻이 있다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* dtor12.cpp */
// 소멸자 한 벌의 형태 — 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <memory>
#include <string>

class Handle {                                   // ① 자원을 든 잎사귀 타입
public:
    explicit Handle(const char* tag) : tag_(tag) {}
    ~Handle() { std::printf("  ~Handle(%s)\n", tag_.c_str()); }   // 적지 않아도 noexcept 다
    Handle(const Handle&)            = delete;   // 복사를 막으면
    Handle& operator=(const Handle&) = delete;
    Handle(Handle&&) noexcept            = default;   // 이동은 직접 열어 줘야 한다
    Handle& operator=(Handle&&) noexcept = default;
private:
    std::string tag_;
};

class Shape {                                    // ② 기반 클래스
public:
    virtual ~Shape() = default;                  // ★ 다형적으로 지울 거면 virtual
    virtual double area() const = 0;
};

class Square final : public Shape {              // ③ final 이면 더 파생되지 않는다
public:
    explicit Square(double s) : s_(s) {}
    ~Square() override { std::printf("  ~Square(%.0f)\n", s_); }
    double area() const override { return s_ * s_; }
private:
    double s_;
    Handle h_{"Square 의 멤버"};                 // 멤버는 선언 역순으로 파괴된다
};

int main() {
    std::unique_ptr<Shape> p = std::make_unique<Square>(3);
    std::printf("area = %.0f\n", p->area());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor12.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
area = 9
  ~Square(3)
  ~Handle(Square 의 멤버)
```

### 규칙

- **소멸자는 인자도 반환 타입도 없고, 클래스마다 하나뿐**이며 **오버로드되지 않는다.**
- **지역 객체는 선언 역순**, **멤버는 선언 역순**, **기반 클래스는 맨 마지막**에 파괴된다 — 전부 **생성의 정확한 역순**이다.
- **소멸자 본문이 먼저 돌고, 그다음 멤버가 파괴된다.** 본문에서는 멤버가 **아직 살아 있다.**
- **C++11부터 소멸자는 적지 않아도 `noexcept`** 다. 던지면 **`std::terminate`** 로 간다.
- **기반 포인터로 파생 객체를 지울 거면 기반의 소멸자를 `virtual` 로** 만든다. 아니면 **UB** 다.
- **`new[]` 는 `delete[]` 로** 놓는다. 짝이 어긋나면 **UB** 다.
- **임시 객체는 전체 식의 끝에서** 파괴된다. **`const` 참조에 묶으면 그 참조만큼 산다.**
- **`static` 은 `main` 이 끝난 뒤 구성 역순**으로 파괴되고, **`std::_Exit` 로 나가면 하나도 안 돈다.**

### 금지 사례 — 여섯 줄이 각각 막힌다

```text
===== 소스: dtor13.cpp =====
// 소멸자에서 막히는 것을 한 파일에 모았다
struct A { ~A(int); };                      // 매개변수를 받으려 한다
struct B { int ~B(); };                     // 반환 타입을 적으려 한다
struct C { ~C(); ~C(); };                   // 두 벌을 적으려 한다
struct D { static ~D(); };                  // static 으로 만들려 한다
struct E { ~E() = delete; };
void f(int x) { delete x; }                 // 포인터가 아닌 것을 지우려 한다
int main() {
    E e;                                    // 소멸자가 지워져 있다
    (void)e; f(1);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic dtor13.cpp -o ex (cc exit=1) =====
dtor13.cpp:2:12: error: destructors may not have parameters
    2 | struct A { ~A(int); };                      // 매개변수를 받으려 한다
      |            ^
dtor13.cpp:3:12: error: return type specification for destructor invalid
    3 | struct B { int ~B(); };                     // 반환 타입을 적으려 한다
      |            ^~~
dtor13.cpp:4:18: error: ‘C::~C()’ cannot be overloaded with ‘C::~C()’
    4 | struct C { ~C(); ~C(); };                   // 두 벌을 적으려 한다
      |                  ^
dtor13.cpp:4:12: note: previous declaration ‘C::~C()’
    4 | struct C { ~C(); ~C(); };                   // 두 벌을 적으려 한다
      |            ^
dtor13.cpp:5:12: error: destructor cannot be static member function
    5 | struct D { static ~D(); };                  // static 으로 만들려 한다
      |            ^~~~~~
dtor13.cpp: In function ‘void f(int)’:
dtor13.cpp:7:24: error: type ‘int’ argument given to ‘delete’, expected pointer
    7 | void f(int x) { delete x; }                 // 포인터가 아닌 것을 지우려 한다
      |                        ^
dtor13.cpp: In function ‘int main()’:
dtor13.cpp:9:7: error: use of deleted function ‘E::~E()’
    9 |     E e;                                    // 소멸자가 지워져 있다
      |       ^
dtor13.cpp:6:12: note: declared here
    6 | struct E { ~E() = delete; };
      |            ^
```

- ★ **여섯 에러가 이 주제의 규칙 셋에 대응한다** — 소멸자의 **형태**(인자·반환 타입·중복·`static`) ·\
  **`delete` 의 피연산자**(포인터라야 한다) · **`= delete` 된 소멸자**.
- ★★ **`~E() = delete;` 를 적으면 그 타입은 「스택에 둘 수 없는 타입」이 된다** — `E e;` 가 **컴파일에서 막힌다.**\
  [13번](../13-constructors-member-init-list-and-delegating/)의 `= delete` 가 **복사를 막았다면**, 여기서는 **파괴 자체를 막은 것**이다.

## 어디서 틀리나

### 1. ★★★ 「가상 소멸자를 빠뜨리면 메모리가 샌다」

- ★ **틀린 말은 아니지만 절반이다.** 실측에서 먼저 터진 것은 **누수가 아니라 `new-delete-type-mismatch`** 였다((5)).
- ★★★ **그리고 경고가 0건일 수 있다.** 기반 클래스에 **가상 함수가 하나도 없으면** 두 컴파일러 다 침묵한다.

### 2. ★★★ 「돌아갔으니 괜찮다」

- ★ **(5)는 `run exit=0` 으로 정상 종료했다.** 소멸자가 안 돌았는데도 그렇다.
- ★★ **「안 터졌다」는 「안전하다」가 아니다** — ASan 을 붙이는 것까지가 한 실험이다.

### 3. ★★ 「`vector` 도 역순으로 파괴하겠지」

- ★ **앞에서부터였다**((1)의 ③). 그리고 **표준이 그 순서를 정하지 않았다** — 근거로 쓰면 안 되는 칸이다.

### 4. ★★ 「임시는 그 줄에서 죽는다」

- ★ **전체 식의 끝**이다. 세미콜론까지는 산다((4)).
- ★★ **`const&` 에 묶으면 늘어나지만, 그 객체의 멤버를 가리키는 포인터에는 안 붙는다** — `c_str()` 사고.

### 5. ★★ 「소멸자에서 던지면 잡으면 된다」

- ★ **못 잡는다.** 소멸자는 기본이 `noexcept` 라 **`std::terminate`** 로 간다((7)).

### 6. ★ 「프로그램이 끝나면 소멸자가 다 돌겠지」

- ★ **`std::_Exit` 는 하나도 안 돌린다**((3)). `abort`·`terminate` 도 마찬가지다.

### 7. ★★ 「빌드에 경고만 나니 표준에 맞다」

- ★ **`void*` 에 `delete` 는 ill-formed 인데 g++ 는 `-pedantic-errors` 로도 `cc exit=0`** 이다((8)).

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「표준」과 「UB」 두 칸이 함께 두껍다** — 초기화([13번](../13-constructors-member-init-list-and-delegating/))는 UB 가 하나뿐이었는데,\
**파괴 쪽은 UB 가 셋**이고 그중 둘은 **아무 도구도 안 보는 판**이 있다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **본체** — 지역·멤버는 **선언 역순**, 기반은 마지막((1)) · **되감기에서 전부 돈다**((2)) · **임시는 전체 식의 끝**, `const&` 수명 연장((4)) · **`static` 은 `main` 뒤 구성 역순**((3)) · **소멸자 기본 `noexcept`**((7)) · 소멸자의 형태 제약(금지 사례) | 로그 순서 · `noexcept(…)` 값 · 진단 전문 + `cc exit` | ★★ 「**이 소멸자가 실제로 불렸나**」 — 로그를 심지 않으면 안 보인다 |
| **조건부 표준** | 특정 조건에서만 보장 | ★ **소멸자가 기본 `noexcept` 인 것은 C++11부터** · `= default`/`= delete` 도 C++11부터 · `std::_Exit` 도 C++11부터 | `-std=c++20` 으로만 돌렸다 | ★ **이 문서는 C++98·C++03 판으로 안 돌려 봤다** |
| **구현 정의** | 문서화 의무가 있다 | ★ **진단 문구와 경고 이름**(g++ `-Wdelete-non-virtual-dtor` · clang `-Wdelete-non-abstract-non-virtual-dtor`) · **경고 개수**((9)) · **`-pedantic-errors` 가 `void*` `delete` 를 에러로 올리는지**((8) — clang 만) · `run exit=134`(SIGABRT) | 개수 블록 · `cc exit`/`run exit` | ★★ **「경고 N건」은 컴파일러를 안 밝히면 뜻이 없다** |
| **미명시** | 몇 가지 중 하나 | ★★ **`std::vector` 가 원소를 파괴하는 순서**((1)의 ③ — 여기서는 **앞에서부터**) · ★★★ **함수 인자로 쓰인 임시를 만드는 순서**((4) — **g++ 와 clang 이 달랐다**) · 번역 단위가 여럿일 때의 **전역 구성 순서** | 로그 순서를 두 컴파일러에서 | ★★★ **한 컴파일러만 보면 「정해져 있다」로 읽힌다** — 실제로 갈렸다 |
| **UB** | 아무 일이나 | ★★★ **셋이다** — ① 가상 아닌 소멸자로 다형적 삭제((5)) ② `new[]`/`delete` 짝 어긋남((6)) ③ 불완전 타입 `delete`((8)) | ASan 리포트 이름 · `run exit` · 경고 | ★★★ **①은 기반에 가상 함수가 없으면 두 컴파일러 다 경고 0건** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | ASan | 무엇이 잡나 |
|---|---|---|---|---|---|
| 파괴 순서 자체 | 표준 | 0건 | 0건 | — | ★ **로그만** |
| 가상 아닌 소멸자(가상 함수 **있음**) | **UB** | 경고 1 | 경고 1 | `new-delete-type-mismatch` | ★ 셋 다 |
| ★★★ **가상 아닌 소멸자(가상 함수 없음)** | **UB** | ★★★ **0건** | ★★★ **0건** | ★★ **잡는다** | ★★★ **ASan 만** |
| `new[]` 를 `delete` 로 | **UB** | 경고 1 | 경고 1 | `bad-free` | ★ 셋 다 |
| ★★ **`c_str()` 이 가리키는 임시** | **UB** | ★★★ **0건** | ★ **경고 1** | (읽지 않아 안 터진다) | ★★ **clang 만** |
| `void*` 에 `delete` | **ill-formed** | 경고 · **exit 0** | 경고 · exit 0 | — | ★★ **clang `-pedantic-errors` 만 에러로** |
| 소멸자에서 던짐 | 표준(→ `terminate`) | 경고 1 | — | — | ★ 경고 + `run exit=134` |
| `std::_Exit` 로 정리를 건너뜀 | 표준 | **0건** | **0건** | — | ★★★ **아무 도구도 못 본다** |

- ★★ **이 표의 결론 세 줄**
  - **파괴 순서는 어떤 도구도 말해 주지 않는다** — **로그를 심는 것**이 유일한 창이다.
  - **가장 위험한 UB 두 개가 경고 0건이다** — 가상 함수 없는 기반의 다형적 삭제, g++ 에서의 `c_str()` 댕글링.
  - **`cc exit=0` 은 세 가지를 뜻할 수 있다** — 맞는 코드 · UB · **ill-formed**((8)).

### ★ 진단이 0줄인 것도 블록으로 받았다

(9)의 개수 블록이 그 자리다. **탐침 아홉 중 일곱이 답했고 둘이 침묵했다.**\
침묵한 둘은 위 표의 ★★★ 줄로 남겨 두었고, **그 둘이 곧 이 주제의 답**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 자원을 하나 든다 | **소멸자에 해제를 적는다** | (1)의 규칙이 **모든 경로**를 덮는다 — 정본은 [15번](../15-raii-resources-as-types/) |
| 그 타입이 상속될 수 있다 | **`virtual ~Base() = default;`** | 아니면 파생 소멸자가 **안 돈다**((5)) |
| 상속을 아예 막고 싶다 | **`final`** | 가상 소멸자 비용을 안 내고 (5)의 UB 도 없앤다 |
| 소멸자에서 실패할 수 있는 일을 한다 | **명시 `close()` 를 따로 둔다** | 소멸자에서 던지면 **`terminate`**((7)) |
| 프로그램 끝에 반드시 한 번 | ★★ **소멸자에 의존하지 않는다** | `_Exit`·`abort` 가 건너뛴다((3)) |
| 배열이 필요하다 | **`std::vector`/`std::array`** | `new[]`/`delete[]` 짝 맞추기를 **없앤다**((6)) |
| 임시를 오래 들고 싶다 | **값으로 받는다** | `const&` 수명 연장은 **한 단계만** 붙는다((4)) |

- ★ **「소멸자를 안 적는 것」이 기본값이다.** 멤버가 전부 RAII 타입이면 **소멸자를 적을 필요가 없고**,\
  적는 순간 **이동 연산이 사라진다**([13번](../13-constructors-member-init-list-and-delegating/) (7)).

## 핵심 문장

- **파괴는 생성의 정확한 역순**이다 — 지역은 선언 역순, 멤버는 선언 역순, 기반은 마지막.
- **되감기에서도 전부 돈다** — 그래서 RAII 가 성립한다.
- **가상 소멸자를 빠뜨리면 파생 소멸자가 아예 안 돌고, 경고가 0건일 수 있다.**
- **소멸자는 적지 않아도 `noexcept` 이고, 던지면 `std::terminate`** 다.
- **`std::_Exit` 는 소멸자를 하나도 안 돌린다** — 「프로그램이 끝나면 정리된다」는 보장이 아니다.
- **`void*` 에 `delete` 는 ill-formed 인데 g++ 는 `cc exit=0`** 이다.

## 관련 자료

- [13번](../13-constructors-member-init-list-and-delegating/) — **초기화 순서의 정본**. (1)의 파괴 순서가 그 역순이다.
- [15번](../15-raii-resources-as-types/) — **이 시점을 자원 관리에 쓰는 법**. (2)의 되감기가 거기서 결론이 된다.
- [12번](../12-class-basics-members-access-and-this/) — 클래스라는 그릇. `this` 와 멤버 배치는 거기.
- 형제 [`09번`](../09-rvalue-references-move-and-forward/) — **이동 후 원본도 파괴된다.** (1)의 계수가 거기서 의미를 갖는다.
- 형제 [`11번`](../11-choosing-parameter-passing/) — **로그·계수 방식의 뿌리**(`Probe`).
- 목록의 **20번 주제** — 「가상 소멸자를 **언제 붙이나**」의 설계 판. 여기는 **안 붙였을 때 무엇이 일어나나**까지.
- 목록의 **18번 주제** — 0/3/5의 법칙. 「소멸자를 적으면 이동이 사라진다」의 정본.
- 목록의 **30번 주제** — 수명 연장 규칙의 전모. (4)는 그중 **임시 하나**만 본 것이다.
- 목록의 **51번 주제** — 예외와 스택 되감기 자체. (2)는 그 결과만 본 것이다.
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **13번**([`13-goto-cleanup-idiom/`](../../../c/syntax/13-goto-cleanup-idiom/)) — **소멸자가 없으면** 같은 일을 라벨로 한다.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **9번**([`09-copy-clone-and-drop/`](../../../rust/syntax/09-copy-clone-and-drop/)) — `Drop` 도 **결정적**이다.\
  ★ 다만 러스트는 **이동한 값은 원본에서 `drop` 되지 않는다**는 규칙을 컴파일러가 강제한다 — C++ 는 **빈 껍데기가 여전히 파괴된다**([15번](../15-raii-resources-as-types/) (4)).
- C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **1번**([`01-value-types-and-reference-types/`](../../../csharp/syntax/01-value-types-and-reference-types/))과 **37번** — **GC 와 `IDisposable`**.

## 용어 풀이

> **소멸자(destructor)** — 객체가 파괴될 때 도는 특수 멤버 함수. **인자도 반환 타입도 없다.**\
> 예: `~Handle() { std::fclose(f_); }`

> **결정적 파괴(deterministic destruction)** — 파괴 시점이 **코드만 보고 정해지는 것**.\
> 예: `{ D x; }` 의 `x` 는 닫는 중괄호에서 파괴된다.

> **스택 되감기(stack unwinding)** — 예외가 지나가는 길의 지역 객체를 **역순으로 파괴하는 것**.\
> 예: (2)에서 세 프레임의 지역 객체 넷이 전부 파괴됐다.

> **가상 소멸자(virtual destructor)** — `virtual` 이 붙은 소멸자. **정적 타입이 아니라 동적 타입**의 소멸자를 부른다.\
> 예: `virtual ~Shape() = default;` — `Shape*` 로 `Square` 를 지워도 `~Square` 가 돈다.

> **다형적 삭제(polymorphic deletion)** — 기반 클래스 포인터로 파생 객체를 `delete` 하는 것.\
> 예: `Shape* p = new Square(3); delete p;` — **가상 소멸자가 없으면 UB** 다((5)).

> **임시 객체(temporary)** — 이름 없이 식 안에서 만들어지는 객체.\
> 예: `use(D{"임시"})` 의 `D{"임시"}` — **전체 식의 끝**에서 파괴된다.

> **전체 식(full-expression)** — 다른 식의 부분이 아닌 가장 바깥 식. 대개 **세미콜론까지**다.\
> 예: `int r = f(D{}) + g(D{});` 전부가 하나의 전체 식이라, 임시 둘이 **세미콜론에서 함께** 죽는다.

> **수명 연장(lifetime extension)** — 임시를 `const` 참조(또는 rvalue 참조)에 묶으면 **그 참조만큼 사는 것**.\
> 예: `const D& r = D{"…"};` — 블록 끝까지 산다. ★ **멤버를 가리키는 포인터에는 안 붙는다.**

> **`noexcept`** — 「이 함수는 예외를 밖으로 내보내지 않는다」는 계약. 어기면 **`std::terminate`** 다.\
> 예: 소멸자는 **C++11부터 적지 않아도** `noexcept` 다((7)).

> **`std::terminate`** — 예외 처리를 계속할 수 없을 때 런타임이 부르는 것. 기본 동작은 `abort()` 다.\
> 예: (7)에서 `run exit=134`(= 128 + SIGABRT 6)가 그 흔적이다.

> **AddressSanitizer(ASan)** — 메모리 오류를 실행 중에 잡는 계측기. `-fsanitize=address` 로 켠다.\
> 예: (5)의 `new-delete-type-mismatch`, (6)의 `bad-free`.

> **`std::_Exit`** — **정리를 하나도 하지 않고** 프로세스를 끝내는 함수.\
> 예: (3)에서 `[파괴]` 줄이 **0개**였다.

## 더 들어가면

- **`std::exit` 대 `std::_Exit`** — `exit` 는 `static` 소멸자와 `atexit` 처리기를 돌리고 `_Exit` 는 안 돌린다.\
  이 문서는 **`_Exit` 만** 던졌다.
- **소멸자와 `std::vector` 의 강한 보장** — 이동 생성자가 `noexcept` 가 아니면 `vector` 재할당이 **복사로 간다.**\
  정본은 목록의 **53번 주제**.
- **`std::destroy_at`·`std::construct_at`(C++20)** — 수명을 손으로 여닫는 도구. 할당기·`optional` 구현이 쓴다.
- **소멸 순서와 `static` 초기화 순서 문제** — 번역 단위가 둘 이상일 때의 미명시 구간. 정본은 목록의 **25번 주제**.
