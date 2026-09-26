# cpp/syntax/27 — `shared_ptr` 와 참조 계수 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::shared_ptr`](https://en.cppreference.com/w/cpp/memory/shared_ptr) · [cppreference — `std::make_shared`](https://en.cppreference.com/w/cpp/memory/shared_ptr/make_shared) · [cppreference — `std::enable_shared_from_this`](https://en.cppreference.com/w/cpp/memory/enable_shared_from_this) · [cppreference — `std::weak_ptr`](https://en.cppreference.com/w/cpp/memory/weak_ptr)\
> ★ **이 배치에서는 위 cppreference 네 쪽을 열지 못했다**(웹 도구 한도). 규칙은 **전부 실행·ASan·`-O2` 어셈블리·libstdc++ 헤더 줄**로 적었다 —\
> 제어 블록의 모양은 **헤더(`shared_ptr_base.h`)의 선언 줄**을, 판 경계는 **두 판에 던진 결과**를 근거로 쓴다.
> **실행 검증** — 이 문서의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 대비 블록은 **rustc 1.92.0** · **Python 3.12.3** 이다(`(8)` 에 버전 블록).\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`sptr01.cpp` \~ `sptr07.cpp` · `spthread.cpp` · `sptr-asm.sh` · `rcsend.rs` · `refcnt.py`).\
> ★★★ **할당 횟수는 전역 `operator new` 를 가로채 셌다** — 표준이 허락하는 치환이다. **시간은 한 번도 재지 않았다.** 「느리다」·「빠르다」는 이 문서에 **없다** — 세는 것은 **할당 횟수 · 바이트 · `sizeof` · `lock` 접두 명령의 개수**뿐이다.\
> ★★★ **ASan 블록은 마커를 `stderr` 로 찍었다** · 자른 블록은 **자르는 명령을 배너에** 적었다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — `shared_ptr`·`weak_ptr`·`make_shared`·`enable_shared_from_this` 는 **C++11부터**, **`weak_from_this` 와 「안 맡긴 객체의 `shared_from_this` 는 `bad_weak_ptr`」는 C++17부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **[26번](../26-unique-ptr-and-ownership-transfer/)과 한 사슬이고, 이 편이 급소다.** 26번이 「소유자가 하나면 **타입**에 적힌다」를 보였다면, 이 편은 「소유자가 여럿이면 **제어 블록**이 생기고 그 값을 치른다」를 보인다.
> ★★★ **앞 편들이 잰 것 — 다시 재지 않고 인용한다.**\
> [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1) — **`shared_ptr<Base>(new Derived)` 는 가상 소멸자 없이도 `~Derived` 를 부른다**(삭제자가 `Derived*` 를 기억) · `Base* raw` 를 거치면 `~Base` 만 · ASan 스택의 **`std::_Sp_counted_ptr<Base*>`** · ★★ **`sizeof` `shared_ptr` 16 · `unique_ptr` 8**.\
> [15번](../15-raii-resources-as-types/) (5) — **`sizeof(shared_ptr<int>)` 16**(「제어 블록 포인터가 하나 더」) · 그리고 ★★ **ASan 은 메모리만 본다 — 파일 핸들·락은 못 본다.**
> **경계** — 「`weak_ptr` 로 순환을 끊는 설계(부모↔자식 그림)」는 [목록의 **28번 주제**](../28-weak-ptr-and-reference-cycles/)가 정본이다 — 여기서는 **순환이 새는 것과 `weak_ptr` 로 0 이 되는 것**까지만 잰다.\
> 「참조 계수 일반론」은 [`memory-management/`](../../../../memory-management/) 쪽, 「RAII 가 못 지우는 것 — `shared_ptr` 순환」의 **논증**은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md)가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소 | ★★★ **할당 횟수 · 바이트 · `use_count()` · 해제 횟수와 시점** — 이 주제의 답 자체다 |
> | ★★ **clang + ASan 이 순환 누수를 보고한 판의 수**((3) — 10판 중 몇 판인지는 **실행마다 바뀐다**) | ★★★ **`lock` 접두 명령 개수** · **g++ + ASan 의 누수 종류(`Indirect leak` 2)** · **소멸자 로그** |
> | 어셈블리의 **레지스터 이름·오프셋** | ★★ **예외 이름(`bad_weak_ptr`)** · **Rust 에러 코드 `E0277`** · **Python 의 `getrefcount`·회수 수** |

## 한눈에 — 쉽게 말하면

**`shared_ptr` 는 「공동 명의 통장 + 은행 장부」다.**

통장 하나를 **여럿이 공동 명의**로 갖는다. 누가 명의자인지는 **통장 안이 아니라 은행 장부(제어 블록)에** 적혀 있다.\
명의자가 늘 때마다 장부에 **한 줄 더하고**, 빠질 때마다 **한 줄 지운다.** **마지막 명의자가 빠지면** 통장을 해지한다.\
그리고 **「조회만 하는 사람」(`weak_ptr`)** 명단이 따로 있다 — 이 사람이 남아 있으면 **통장은 해지돼도 장부는 못 버린다.**

- **장부가 따로 있다** — `shared_ptr` 는 **통장 포인터 + 장부 포인터** 두 칸이다(16바이트 — 20편).
- **장부를 만드는 데 드는 일** — `make_shared` 는 통장과 장부를 **한 번에** 만들고, `shared_ptr(new T)` 는 **따로 두 번** 만든다((1)).
- **장부에 한 줄 적는 일** — 여러 창구(스레드)가 동시에 적어도 안 틀리게 **잠그고 적는다**(`lock` 명령)((7)).
- **서로를 명의자로 적은 두 통장** — 둘 다 **영원히 해지되지 않는다**((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 은행 장부 | ★★★ **제어 블록** — 강한 계수 · 약한 계수 · 삭제자 | (1)(6) |
| 통장+장부를 한 번에 | ★★★ **`make_shared` — 할당 1회 · 32바이트** | (1) |
| 따로 두 번 | ★★★ **`shared_ptr<T>(new T)` — 할당 2회 · 40바이트** | (1) |
| 명의자 수 | ★★ **`use_count()`** — 복사 +1 · 이동 0 · `weak_ptr` 0 | (2) |
| 서로를 명의자로 | ★★★ **순환 참조 — ASan `Indirect leak` 2** | (3) |
| 조회만 하는 사람 | ★★★ **`weak_ptr` — 순환이 끊겨 누수 0** · `lock()` 은 해지 뒤 `nullptr` | (2)(3) |
| 장부를 못 버리는 조회자 | ★★★ **`make_shared` + `weak_ptr` — 객체는 죽었는데 1016바이트가 남는다** | (6) |
| 잠그고 적기 | ★★★ **`lock xadd` — shared 판 4개 · unique 판 0개** | (7) |

```text
   shared_ptr<T> s  (16바이트)                         제어 블록 (libstdc++)
   ┌───────────┬────────────┐                          ┌────────┬──────────┬───────────┬──────────────┐
   │ T* 8      │ 블록* 8     │ ───────────────────────▶ │ vptr 8 │ use 4    │ weak 4    │ (삭제자·포인터 │
   └─────┬─────┴────────────┘                          │        │ #shared  │ #weak+1   │  또는 T 자체)  │
         │                                             └────────┴──────────┴───────────┴──────────────┘
         ▼
      [ T ]         make_shared : 블록 안에 T 가 같이 산다  — 할당 1회
                    shared_ptr(new T) : T 따로, 블록 따로   — 할당 2회
```

## 이 주제가 답하려는 질문

1. ★★★ **제어 블록은 정말 있나 — 무엇으로 보이나** · `make_shared` 와 `shared_ptr(new T)` 는 **할당을 몇 번** 하나((1)).
2. ★★ **`use_count()` 는 어느 동작에서 움직이나** · `weak_ptr` 는 계수를 올리나((2)).
3. ★★★ **순환 참조는 정말 새나 — 누가 그것을 보나** · `weak_ptr` 로 끊으면((3)).
4. ★★ **`make_shared` 에 약점이 있나** — `weak_ptr` 가 남으면 **메모리는 언제 풀리나**((6)).
5. ★★★ **`shared_ptr` 을 기본값으로 쓰면 안 되는 이유는 무엇으로 셀 수 있나** — 크기 · 할당 · 원자 명령((1)(7)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ① 할당·해제 계수기다

★★★ **이 주제의 본체는 ① 할당 계수기다** — 전역 `operator new`/`delete` 를 가로채 **제어 블록이 생기는 것을 횟수와 바이트로** 본다. **제어 블록은 눈에 안 보이는데, 할당 한 번은 셀 수 있다.**\
★★ **짝이 ③ ASan(순환)과 ④ `-O2` 어셈블리(원자 명령)다**.

```text
① ★ 할당·해제 계수기     make_shared 1회 대 new 2회 · weak_ptr 가 남을 때 해제 시점   (1)(6)
② 두 컴파일러 대조       —(에러가 주제가 아니다) · Rust 의 E0277 대비                  (8)
③ ASan                   순환 참조 Indirect leak · weak_ptr 로 0                         (3)
④ ★ 어셈블리(-O2)        shared_ptr 복사 대입의 lock 접두 명령 · 단일 스레드 검사       (7)
⑤ 경고 격자              —                                                              부적용
⑥ <type_traits>·sizeof   sizeof 16 대 8 — 20편 인용                                     인용
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ★★★ **① 할당·해제 계수기** | ★★★ **본체** — **1회 32바이트 대 2회 40바이트** · 해제 **0회 → 1회**(weak 가 죽을 때) | **쓴다** |
| ② 두 컴파일러 대조 | ★ 이 편의 실험은 **전부 통과하는 코드**다 — 두 컴파일러의 **실행 출력**이 같은지만 본다 · Rust 는 **컴파일 에러가 곧 대비** | **쓴다(대비)** |
| ③ ASan | ★★★ **g++ 는 `Indirect leak` 2건 10 / 10 판** · ★★ **clang 은 판마다 다르다** | **쓴다** |
| ★★ **④ 어셈블리(-O2)** | ★★★ **`lock` 접두 SHARED 4 · UNIQUE 0 · RAW 0**(두 컴파일러) | **쓴다** |
| ⑤ 경고 격자 | ★ **부적용** — 순환·원자 비용 어느 것도 **컴파일러가 경고할 일이 아니다**(규칙대로 된 코드다) | **안 쓴다** |
| ⑥ `sizeof` | ★ **인용** — 20편 (1)(6)이 **16 · 8** 을 찍었다 | **다시 안 찍는다** |

- ★★ **⑤ 를 부적용으로 둔 이유** — (3)의 순환도 (7)의 원자 명령도 **올바른 C++** 다. 순환은 「누수」이지 규칙 위반이 아니다 — 경고가 **나올 자리가 아니다**(18-B 의 「잴 것이 없다」).
- ★★ **ASan 이 못 보는 것을 먼저 적어 둔다** — [15번](../15-raii-resources-as-types/)이 말한 대로 **메모리만** 본다. `shared_ptr` 순환이 **파일 핸들**을 붙들고 있으면 **ASan 은 그 파일이 안 닫힌 것을 모른다.** 그리고 (3)이 보이듯 **메모리 누수조차 판에 따라 놓친다.**

### (1) ★★★ 제어 블록을 센다 — `make_shared` 1회 대 `shared_ptr(new T)` 2회

**언제 쓰나** — `shared_ptr` 를 만들 때마다. **이 절이 이 주제의 중심이다.**

```cpp
/* sptr01.cpp */
// 전역 operator new 를 가로채 할당 횟수를 센다 — make_shared 대 shared_ptr(new T) 대 unique_ptr
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

static int allocs = 0;
static std::size_t bytes = 0;

void* operator new(std::size_t n) {
    ++allocs; bytes += n;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc();
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

struct T { long a = 1, b = 2; };           // 16바이트

template <class F>
void count(const char* label, F make) {
    allocs = 0; bytes = 0;
    {
        auto p = make();
        std::printf("%-34s 할당 %d회 · %2zu바이트\n", label, allocs, bytes);
    }
}

int main() {
    std::printf("sizeof(T) = %zu\n", sizeof(T));
    count("(1) std::make_shared<T>()",        [] { return std::make_shared<T>(); });
    count("(2) std::shared_ptr<T>(new T)",    [] { return std::shared_ptr<T>(new T); });
    count("(3) std::make_unique<T>()",        [] { return std::make_unique<T>(); });
    count("(4) std::shared_ptr<T>(make_unique)", [] { return std::shared_ptr<T>(std::make_unique<T>()); });
    count("(5) 복사 한 번 더",                 [] { auto a = std::make_shared<T>(); auto b = a; return b; });
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
```

- ★★★ **`make_shared<T>()` 는 1회 32바이트, `shared_ptr<T>(new T)` 는 2회 40바이트** — `T` 는 16바이트다.\
  ★ **남는 바이트가 제어 블록**이다 — `make_shared` 는 **32 − 16 = 16바이트**를, `new` 판은 **40 − 16 = 24바이트**를 **따로 한 번 더** 잡았다.
- ★★★ **`make_unique<T>()` 는 1회 16바이트** — **제어 블록이 없다.** `T` 만 잡는다. 이것이 26번과 이 편의 **바이트 단위 차이**다.
- ★★ **(4) `unique_ptr` 를 `shared_ptr` 로 옮기면 2회 40바이트** — `T` 는 이미 있고, **옮기는 순간 제어 블록을 새로 잡는다.** 팩토리가 `unique_ptr` 를 돌려주면 받는 쪽이 이 값을 치르고 공유로 바꿀 수 있다.
- ★★ **(5) 복사 한 번 더 해도 1회** — 복사는 **할당하지 않는다.** 장부에 한 줄(계수 +1)만 적는다.

★★ **헤더가 제어 블록의 칸을 말한다.**

```text
===== grep -nE '_Atomic_word  _M_(use|weak)_count;' /usr/include/c++/13/bits/shared_ptr_base.h (exit=0) =====
237:      _Atomic_word  _M_use_count;     // #shared
238:      _Atomic_word  _M_weak_count;    // #weak + (#shared != 0)
===== grep -nE '^    class _Sp_counted_(ptr|deleter|ptr_inplace) final' /usr/include/c++/13/bits/shared_ptr_base.h (exit=0) =====
419:    class _Sp_counted_ptr final : public _Sp_counted_base<_Lp>
494:    class _Sp_counted_deleter final : public _Sp_counted_base<_Lp>
580:    class _Sp_counted_ptr_inplace final : public _Sp_counted_base<_Lp>
```

- ★★ **`_M_use_count`(강한 계수) · `_M_weak_count`(약한 계수 — 주석이 `#weak + (#shared != 0)`)** 가 둘 다 `_Atomic_word`(4바이트)다. 앞에 **vptr 8** 이 붙어 **16바이트**가 `make_shared` 의 오버헤드와 맞는다.
- ★★ **제어 블록의 종류가 셋이다** — `_Sp_counted_ptr`(`new T` 를 받은 판 — 포인터 8 을 더 들어 **24**) · `_Sp_counted_deleter`(삭제자를 받은 판) · **`_Sp_counted_ptr_inplace`**(`make_shared` — **`T` 를 블록 안에** 둔다).\
  ★ (3)의 ASan 스택에 **`_Sp_counted_ptr_inplace<Child, …>`** 가 찍힌다 — 그 블록이 **실제로 쓰였다**는 증거다. 20편의 `_Sp_counted_ptr<Base*>` 는 `new` 판이었다.

★★ **판 격자 — 컴파일러와 최적화 수준을 바꿔도 계수는 같나.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
===== g++ -std=c++20 -O2 sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
===== clang++ -std=c++20 -O2 sptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(T) = 16
(1) std::make_shared<T>()          할당 1회 · 32바이트
(2) std::shared_ptr<T>(new T)      할당 2회 · 40바이트
(3) std::make_unique<T>()          할당 1회 · 16바이트
(4) std::shared_ptr<T>(make_unique) 할당 2회 · 40바이트
(5) 복사 한 번 더             할당 1회 · 32바이트
```

- ★★★ **clang · g++ `-O2` · clang `-O2` 셋 다 한 글자도 같다** — 앞 배치의 규칙 24 「**계수는 판을 잘 안 탄다**」가 여기서도 맞았다. (`operator new` 를 **치환해서** 부작용이 생겼으므로 `-O2` 가 할당을 없애지 못한다 — 이 판의 관찰이다.)

```text
                            할당   바이트   블록 종류                   T 는 어디에
   make_shared<T>()          1      32     _Sp_counted_ptr_inplace     ★ 블록 안
   shared_ptr<T>(new T)      2      40     _Sp_counted_ptr   (24)      따로 (16)
   shared_ptr<T>(unique_ptr) 2      40     _Sp_counted_deleter (24)    따로 (16)
   make_unique<T>()          1      16     ★ 없다                      따로 (16)
   복사 한 번 더             0      0      (계수 +1)
```

### (2) ★★ `use_count()` 격자 — 복사 · 이동 · `weak_ptr` · `lock()`

**언제 쓰나** — 「지금 이 객체를 몇 곳이 살려 두나」를 따져야 할 때.

```cpp
/* sptr02.cpp */
// use_count() 가 어느 동작에서 움직이나 — 한 줄씩 찍는다
#include <cstdio>
#include <memory>
#include <utility>

struct T { ~T() { std::printf("      ~T\n"); } };

int main() {
    auto a = std::make_shared<T>();
    std::printf("(1) auto a = make_shared<T>()        a.use_count()=%ld\n", a.use_count());
    auto b = a;
    std::printf("(2) auto b = a                        a.use_count()=%ld\n", a.use_count());
    auto c = std::move(b);
    std::printf("(3) auto c = std::move(b)             a.use_count()=%ld · b 가 비었나 %d\n", a.use_count(), (int)(b == nullptr));
    std::weak_ptr<T> w = a;
    std::printf("(4) weak_ptr<T> w = a                 a.use_count()=%ld · w.use_count()=%ld\n", a.use_count(), w.use_count());
    {
        auto l = w.lock();
        std::printf("(5) auto l = w.lock()   (블록 안)     a.use_count()=%ld\n", a.use_count());
    }
    std::printf("(6) l 이 블록을 나간 뒤               a.use_count()=%ld\n", a.use_count());
    const auto& r = a;
    std::printf("(7) const auto& r = a                 a.use_count()=%ld\n", r.use_count());
    c.reset();
    std::printf("(8) c.reset()                         a.use_count()=%ld\n", a.use_count());
    a.reset();
    std::printf("(9) a.reset()                         w.use_count()=%ld · w.expired()=%d\n", w.use_count(), (int)w.expired());
    auto l2 = w.lock();
    std::printf("(10) auto l2 = w.lock()               l2 가 비었나 %d\n", (int)(l2 == nullptr));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) auto a = make_shared<T>()        a.use_count()=1
(2) auto b = a                        a.use_count()=2
(3) auto c = std::move(b)             a.use_count()=2 · b 가 비었나 1
(4) weak_ptr<T> w = a                 a.use_count()=2 · w.use_count()=2
(5) auto l = w.lock()   (블록 안)     a.use_count()=3
(6) l 이 블록을 나간 뒤               a.use_count()=2
(7) const auto& r = a                 a.use_count()=2
(8) c.reset()                         a.use_count()=1
      ~T
(9) a.reset()                         w.use_count()=0 · w.expired()=1
(10) auto l2 = w.lock()               l2 가 비었나 1
```

- ★★★ **복사는 +1, 이동은 0**((2)→(3)) — 이동은 **장부를 안 건드린다**(`b` 가 빠지고 `c` 가 들어와 **합이 같다**). 이동한 `b` 는 **비었다**.
- ★★★ **`weak_ptr` 는 강한 계수를 올리지 않는다**((4) — 2 그대로). `w.use_count()` 도 **강한 계수**를 돌려준다(2).
- ★★ **`lock()` 은 살아 있으면 `shared_ptr` 를 하나 더 만든다**((5) — 3) — 그 `shared_ptr` 가 죽으면 **돌아온다**((6) — 2).
- ★ **`const auto&` 는 계수를 안 올린다**((7)) — 참조일 뿐이다.
- ★★★ **마지막 강한 참조가 죽는 순간 `~T` 가 돈다**((8) 뒤) — **`weak_ptr` 가 남아 있어도.** 그 뒤 `w.expired()=1` · `w.lock()` 은 **`nullptr`**((9)(10)).
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) auto a = make_shared<T>()        a.use_count()=1
(2) auto b = a                        a.use_count()=2
(3) auto c = std::move(b)             a.use_count()=2 · b 가 비었나 1
(4) weak_ptr<T> w = a                 a.use_count()=2 · w.use_count()=2
(5) auto l = w.lock()   (블록 안)     a.use_count()=3
(6) l 이 블록을 나간 뒤               a.use_count()=2
(7) const auto& r = a                 a.use_count()=2
(8) c.reset()                         a.use_count()=1
      ~T
(9) a.reset()                         w.use_count()=0 · w.expired()=1
(10) auto l2 = w.lock()               l2 가 비었나 1
```

### (3) ★★★ 순환 참조 — 누가 보나, `weak_ptr` 로 끊으면

**언제 쓰나** — 부모가 자식을, 자식이 부모를 `shared_ptr` 로 들 때. **이 편의 두 번째 급소다.**

```cpp
/* sptr03.cpp */
// 부모와 자식이 서로를 가리킨다 — 기본은 둘 다 shared_ptr, -DASK_WEAK 이면 자식→부모를 weak_ptr 로
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <memory>

struct Parent;
struct Child {
#ifdef ASK_WEAK
    std::weak_ptr<Parent>   parent;
#else
    std::shared_ptr<Parent> parent;
#endif
    ~Child() { std::fprintf(stderr, "      ~Child\n"); }
};
struct Parent {
    std::shared_ptr<Child> child;
    ~Parent() { std::fprintf(stderr, "      ~Parent\n"); }
};

__attribute__((noinline)) void link_pair() {
    auto p = std::make_shared<Parent>();
    auto c = std::make_shared<Child>();
    p->child = c;
    c->parent = p;
    std::fprintf(stderr, "(1) 서로 이은 직후  p.use_count()=%ld · c.use_count()=%ld\n", p.use_count(), c.use_count());
}

int main() {
    link_pair();
    std::fprintf(stderr, "(2) link_pair() 에서 돌아왔다\n");
}
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(1) 서로 이은 직후  p.use_count()=2 · c.use_count()=2
(2) link_pair() 에서 돌아왔다

=================================================================
==415667==ERROR: LeakSanitizer: detected memory leaks

Indirect leak of 32 byte(s) in 1 object(s) allocated from:
    #0 0x7a028bcfe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5725035183ff in std::__new_allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x5725035178f8 in std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x5725035178f8 in std::allocator_traits<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >::allocate(std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x5725035178f8 in std::__allocated_ptr<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > > std::__allocate_guarded<std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >(std::allocator<std::_Sp_counted_ptr_inplace<Child, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&) /usr/include/c++/13/bits/allocated_ptr.h:98
    #5 0x57250351709e in std::__shared_count<(__gnu_cxx::_Lock_policy)2>::__shared_count<Child, std::allocator<void>>(Child*&, std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:969
    #6 0x572503516c0a in std::__shared_ptr<Child, (__gnu_cxx::_Lock_policy)2>::__shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:1712
    #7 0x5725035167bb in std::shared_ptr<Child>::shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr.h:464
    #8 0x5725035161e1 in std::shared_ptr<Child> std::make_shared<Child>() /usr/include/c++/13/bits/shared_ptr.h:1010
    #9 0x572503515503 in link_pair() sptr03.cpp:22
    #10 0x572503515684 in main sptr03.cpp:29

Indirect leak of 32 byte(s) in 1 object(s) allocated from:
    #0 0x7a028bcfe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5725035182af in std::__new_allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x5725035173b3 in std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x5725035173b3 in std::allocator_traits<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >::allocate(std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x5725035173b3 in std::__allocated_ptr<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > > std::__allocate_guarded<std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> > >(std::allocator<std::_Sp_counted_ptr_inplace<Parent, std::allocator<void>, (__gnu_cxx::_Lock_policy)2> >&) /usr/include/c++/13/bits/allocated_ptr.h:98
    #5 0x572503516e28 in std::__shared_count<(__gnu_cxx::_Lock_policy)2>::__shared_count<Parent, std::allocator<void>>(Parent*&, std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:969
    #6 0x572503516aaa in std::__shared_ptr<Parent, (__gnu_cxx::_Lock_policy)2>::__shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr_base.h:1712
    #7 0x5725035166b3 in std::shared_ptr<Parent>::shared_ptr<std::allocator<void>>(std::_Sp_alloc_shared_tag<std::allocator<void> >) /usr/include/c++/13/bits/shared_ptr.h:464
    #8 0x5725035160e3 in std::shared_ptr<Parent> std::make_shared<Parent>() /usr/include/c++/13/bits/shared_ptr.h:1010
    #9 0x5725035154d5 in link_pair() sptr03.cpp:21
    #10 0x572503515684 in main sptr03.cpp:29

SUMMARY: AddressSanitizer: 64 byte(s) leaked in 2 allocation(s).
```

```text
===== echo "g++ (순환) 누수 종류 : $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa 2>&1; ./exa 2>&1 | grep -oE '^(Direct|Indirect) leak' | sort | uniq -c | tr -s ' ' | tr '\n' ';')" (exit=0) =====
g++ (순환) 누수 종류 :  2 Indirect leak;
```

- ★★★ **`~Parent`·`~Child` 가 한 줄도 없고 ASan 이 64바이트 누수**를 보고한다 — 두 블록이 **서로의 계수를 1 로 붙들고** 있어 아무도 0 이 되지 않는다(`p.use_count()=2 · c.use_count()=2`).
- ★★★ **보고가 전부 `Indirect leak` 이다 — `Direct leak` 은 0건.** 「**Direct 하나 · Indirect 하나**」로 나올 것 같지만,\
  **순수한 순환에서는 둘 다 「다른 누수 블록에서만 닿는 블록」이라** LSan 이 둘 다 간접으로 분류한다. **뿌리가 없는 누수**다.
- ★★ **스택 프레임이 제어 블록의 종류를 말한다** — `std::_Sp_counted_ptr_inplace<Child, …>` · `<Parent, …>`. `make_shared` 한 번이 **블록째 32바이트**를 잡았고, 그 블록이 샜다.

★★★ **자식 → 부모를 `weak_ptr` 로 바꾸면**(`-DASK_WEAK`) —

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DASK_WEAK sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(1) 서로 이은 직후  p.use_count()=1 · c.use_count()=2
      ~Parent
      ~Child
(2) link_pair() 에서 돌아왔다
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DASK_WEAK sptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=0) =====
(1) 서로 이은 직후  p.use_count()=1 · c.use_count()=2
      ~Parent
      ~Child
(2) link_pair() 에서 돌아왔다
```

- ★★★ **두 컴파일러 다 누수 0 · `run exit=0`** · `~Parent` → `~Child` 가 돈다. `p.use_count()=1` — 자식의 `weak_ptr` 가 **부모의 강한 계수를 안 올렸다.**
- ★ 부모가 먼저 죽고(강한 계수 1 → 0), 부모가 든 `child` 가 죽으며 자식이 따라 죽는다. **그림과 설계 규칙은 [목록의 28번 주제](../28-weak-ptr-and-reference-cycles/)다**.

★★★ **그런데 같은 순환 판을 clang + ASan 으로 돌리면 — 판마다 다르다.**

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "clang + ASan 10판 중 리포트가 나온 판 $n" (exit=0) =====
clang + ASan 10판 중 리포트가 나온 판 6
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. sptr03.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "g++   + ASan 10판 중 리포트가 나온 판 $n" (exit=0) =====
g++   + ASan 10판 중 리포트가 나온 판 10
```

- ★★★ **g++ + ASan 은 10 / 10 판 모두 보고**하는데, **clang + ASan 은 10판 중 일부만 보고**한다 — 그 수는 **실행마다 바뀐다**(흔들리는 칸).\
  ★ 이 배치의 예행에서 같은 바이너리가 **30판 중 14판 · 10판 중 6판**을 보고했고, **제출 전 재대조의 두 캡처는 6 과 2** 였다. **자릿수만 주장한다** — 「**놓치는 판이 있다**」.
- ★★ **LeakSanitizer 는 스택·레지스터를 보수적으로 훑어 「아직 닿는 포인터」를 찾는다** — 죽은 스택 칸에 남은 주소가 **닿는 것처럼 보이면** 누수를 놓친다. 순환을 `link_pair()`(`noinline`)로 옮긴 것도 그 때문인데, **clang 판은 그래도 흔들렸다.**\
  ★ 흔들리는 이유가 **정확히 어느 칸인지는 재지 못했다** — 예행에서 `ASAN_OPTIONS=detect_stack_use_after_return=0`(가짜 스택 끔)이 **순환을 `main` 안에 둔 판에서는 0 / 20**, **함수로 옮긴 지금 판에서는 6 / 8** 이었다. 프로그램이 달라 원인을 하나로 좁히지 못했다(제3의 상태 — 본문에 블록을 싣지 않았다).
- ★★★ **결론 — 「ASan 이 조용하다」는 「순환이 없다」가 아니다.** [20번](../20-virtual-destructors-and-polymorphic-deletion/)의 「clang + ASan 은 type-mismatch 를 못 본다」와 **같은 부류의 새 항목**이다 — 이번에는 **컴파일러 기본값이 아니라 실행마다** 갈린다.

```text
   순환 (둘 다 shared_ptr)                         자식 -> 부모를 weak_ptr 로
   Parent ──shared──▶ Child                         Parent ──shared──▶ Child
      ▲                 │                              ▲                 │
      └─────shared──────┘   use 2 · 2                  └ ─ ─ weak ─ ─ ─ ─┘   use 1 · 2
   p, c 가 스코프를 나가도 서로 1 을 붙든다           p 가 나가면 Parent 0 → ~Parent → child 해제 → ~Child
   ★ Indirect leak 2 (뿌리 없는 누수)                 ★ 누수 0
```

### (4) ★★ `enable_shared_from_this` — 안 맡긴 객체에서 부르면

**언제 쓰나** — 멤버 함수 안에서 **자기 자신을 가리키는 `shared_ptr`** 가 필요할 때(콜백에 `this` 를 넘기면서 수명을 붙들고 싶을 때).

```cpp
/* sptr04.cpp */
// enable_shared_from_this — shared_ptr 가 맡은 객체와 안 맡은 객체에서 shared_from_this() 를 부른다
#include <cstdio>
#include <memory>

struct Job : std::enable_shared_from_this<Job> {
    std::shared_ptr<Job> self() { return shared_from_this(); }
};

int main() {
    auto owned = std::make_shared<Job>();
    auto again = owned->self();
    std::printf("(1) shared_ptr 가 맡은 객체   owned.use_count()=%ld · 같은 객체인가 %d\n",
                owned.use_count(), (int)(owned == again));

    Job local;
    std::printf("(2) 지역 변수에서 부른다\n");
    try {
        auto p = local.self();
        std::printf("    반환됨 p==nullptr %d\n", (int)(p == nullptr));
    } catch (const std::exception& e) {
        std::printf("    catch: %s\n", e.what());
    }

    Job* raw = new Job;
    std::printf("(3) new 로 만들고 아직 안 맡겼다\n");
    try {
        auto p = raw->self();
        std::printf("    반환됨 p==nullptr %d\n", (int)(p == nullptr));
    } catch (const std::exception& e) {
        std::printf("    catch: %s\n", e.what());
    }
    delete raw;

#if __cplusplus >= 201703L
    std::printf("(4) weak_from_this() — 안 맡긴 객체\n");
    std::printf("    expired=%d\n", (int)local.weak_from_this().expired());
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
(4) weak_from_this() — 안 맡긴 객체
    expired=1
```

- ★★ **(1) `shared_ptr` 가 맡은 객체에서는 `use_count()=2`** — `shared_from_this()` 가 **같은 제어 블록**에 한 줄을 더했다. **`shared_ptr<Job>(this)` 로 새로 만들었다면** 블록이 **둘**이 되어 이중 해제가 된다 — 그것을 피하는 장치다.
- ★★★ **(2) 지역 변수 · (3) 아직 안 맡긴 `new` 객체에서 부르면 `bad_weak_ptr` 예외.** 객체 안의 `weak_ptr` 가 **아무 블록도 가리키지 않기** 때문이다.
- ★ **(4) `weak_from_this()` 는 C++17** — 안 맡긴 객체에서는 **`expired=1`** 인 빈 `weak_ptr` 를 돌려준다(예외 없이 물어보는 길).

★★ **같은 파일을 `-std=c++14` 로** —

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
===== clang++ -std=c++14 -Wall -Wextra -pedantic sptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) shared_ptr 가 맡은 객체   owned.use_count()=2 · 같은 객체인가 1
(2) 지역 변수에서 부른다
    catch: bad_weak_ptr
(3) new 로 만들고 아직 안 맡겼다
    catch: bad_weak_ptr
```

- ★★ **C++14 판도 `bad_weak_ptr` 를 던졌다** — 그러나 **층이 다르다.** C++17 부터는 「**`bad_weak_ptr` 를 던진다**」가 규정이고, C++14 에서는 **안 맡긴 객체에서 부르는 것 자체가 미정의**였다(알려진 판 경계 — 기준 소스를 이 배치에서 열지 못했다).\
  ★★★ **「C++14 에서도 던졌다」는 libstdc++ 가 같은 코드를 두 판에 쓴 결과**이지 C++14 의 보장이 아니다 — **「두 판에서 같았다」가 보장이 아닌** 자리다.

### (5) ★ 별칭 생성자 — 멤버를 가리키며 전체를 살려 둔다

**언제 쓰나** — 객체의 **일부(멤버)만** 넘겨주면서 **객체 전체의 수명**을 붙들고 싶을 때.

```cpp
/* sptr05.cpp */
// 별칭 생성자 — 멤버를 가리키는 shared_ptr 가 객체 전체를 살려 두나
#include <cstdio>
#include <memory>

struct Pair {
    int first = 1, second = 2;
    ~Pair() { std::printf("      ~Pair\n"); }
};

int main() {
    auto whole = std::make_shared<Pair>();
    std::shared_ptr<int> part(whole, &whole->second);      // 별칭 생성자
    std::printf("(1) part.get()==&whole->second %d · *part=%d · use_count=%ld\n",
                (int)(part.get() == &whole->second), *part, whole.use_count());
    whole.reset();
    std::printf("(2) whole.reset() 뒤  *part=%d · part.use_count()=%ld\n", *part, part.use_count());
    part.reset();
    std::printf("(3) part.reset() 뒤\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) part.get()==&whole->second 1 · *part=2 · use_count=2
(2) whole.reset() 뒤  *part=2 · part.use_count()=1
      ~Pair
(3) part.reset() 뒤
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) part.get()==&whole->second 1 · *part=2 · use_count=2
(2) whole.reset() 뒤  *part=2 · part.use_count()=1
      ~Pair
(3) part.reset() 뒤
```

- ★★ **`part` 는 `&whole->second` 를 가리키면서 `whole` 의 제어 블록을 공유**한다 — `use_count=2`.
- ★★★ **`whole.reset()` 뒤에도 `*part=2` 이고 `~Pair` 가 안 돈다** — `part` 가 **블록의 강한 계수 1** 을 들고 있다. `part.reset()` 에서야 `~Pair`.
- ★ **`shared_ptr` 는 「무엇을 가리키나(`get()`)」와 「무엇을 살려 두나(블록)」가 다를 수 있다** — 두 칸(16바이트)이 **따로 있는 이유**다.

### (6) ★★★ `make_shared` 의 약점 — `weak_ptr` 가 남으면 메모리는 언제 풀리나

**언제 쓰나** — 큰 객체를 `make_shared` 로 만들고 **캐시·관찰자**가 `weak_ptr` 를 오래 들 때.

```cpp
/* sptr06.cpp */
// weak_ptr 하나가 남으면 메모리는 언제 풀리나 — make_shared 판과 shared_ptr(new T) 판
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <new>

// 할당한 블록의 크기를 기억해 두었다가 해제할 때 몇 바이트가 돌아갔는지 센다
static void*       live_p[16];
static std::size_t live_n[16];
static int frees = 0;
static std::size_t freed = 0;

void* operator new(std::size_t n) {
    void* p = std::malloc(n);
    if (!p) throw std::bad_alloc();
    for (int i = 0; i < 16; ++i) if (!live_p[i]) { live_p[i] = p; live_n[i] = n; break; }
    return p;
}
void operator delete(void* p) noexcept {
    for (int i = 0; i < 16; ++i) if (live_p[i] == p) { ++frees; freed += live_n[i]; live_p[i] = nullptr; }
    std::free(p);
}
void operator delete(void* p, std::size_t) noexcept { operator delete(p); }

struct Big {
    char buf[1000] = {};
    ~Big() { std::printf("      ~Big\n"); }
};

static void report(const char* what) { std::printf("    %-24s 해제 %d회 · %4zu바이트\n", what, frees, freed); }

int main() {
    std::printf("(M) make_shared<Big>()\n");
    frees = 0; freed = 0;
    {
        std::weak_ptr<Big> w;
        {
            auto s = std::make_shared<Big>();
            w = s;
        }
        report("마지막 shared_ptr 이 죽었다");
    }
    report("weak_ptr 도 죽었다");

    std::printf("(N) shared_ptr<Big>(new Big)\n");
    frees = 0; freed = 0;
    {
        std::weak_ptr<Big> w;
        {
            std::shared_ptr<Big> s(new Big);
            w = s;
        }
        report("마지막 shared_ptr 이 죽었다");
    }
    report("weak_ptr 도 죽었다");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(M) make_shared<Big>()
      ~Big
    마지막 shared_ptr 이 죽었다 해제 0회 ·    0바이트
    weak_ptr 도 죽었다   해제 1회 · 1016바이트
(N) shared_ptr<Big>(new Big)
      ~Big
    마지막 shared_ptr 이 죽었다 해제 1회 · 1000바이트
    weak_ptr 도 죽었다   해제 2회 · 1024바이트
```

- ★★★ **`make_shared` 판(M) — 마지막 `shared_ptr` 가 죽으면 `~Big` 은 돌지만 해제는 0회.** **`weak_ptr` 까지 죽어야 1016바이트가 한 번에** 돌아간다.\
  ★ **객체와 블록이 한 덩어리**라 블록을 못 버리면(약한 계수 > 0) **객체 자리도 못 버린다.** 소멸자는 돌았으니 **「죽었는데 자리는 남은」** 상태다.
- ★★★ **`new` 판(N) — 마지막 `shared_ptr` 가 죽는 순간 1000바이트(객체)가 풀리고**, `weak_ptr` 가 죽을 때 **24바이트(블록)가** 풀린다(합계 1024).
- ★★ **그래서 「`make_shared` 가 언제나 낫다」는 틀린다** — 할당은 1회로 줄지만 **`weak_ptr` 가 오래 사는 큰 객체**는 **메모리를 오래 붙든다.** 무엇을 고를지는 **`weak_ptr` 의 수명**이 정한다.
- ★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic sptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(M) make_shared<Big>()
      ~Big
    마지막 shared_ptr 이 죽었다 해제 0회 ·    0바이트
    weak_ptr 도 죽었다   해제 1회 · 1016바이트
(N) shared_ptr<Big>(new Big)
      ~Big
    마지막 shared_ptr 이 죽었다 해제 1회 · 1000바이트
    weak_ptr 도 죽었다   해제 2회 · 1024바이트
```

```text
                         마지막 shared_ptr 가 죽을 때      weak_ptr 가 죽을 때
   make_shared<Big>        ~Big · 해제 0회   ★              해제 1회 1016 (객체+블록 한 덩어리)
   shared_ptr(new Big)     ~Big · 해제 1회 1000             해제 1회 24   (블록)

   ★ 「소멸자가 돌았다」와 「메모리가 돌아갔다」가 make_shared 에서는 다른 시점이다
```

### (7) ★★★ 원자 명령을 센다 — `shared_ptr` 복사 대입 한 번이 무엇이 되나

**언제 쓰나** — 「`shared_ptr` 을 기본값으로 써도 되나」를 판단할 때. **시간은 재지 않는다 — 명령만 센다.**

```cpp
/* sptr07.cpp */
// 복사·이동 한 번이 무슨 명령이 되나 — -DASK_SHARED · -DASK_UNIQUE · -DASK_RAW 로 한 함수만 남긴다
#include <memory>

#if defined(ASK_SHARED)
std::shared_ptr<int> keep;
void store(const std::shared_ptr<int>& p) { keep = p; }       // shared_ptr 복사 대입
#elif defined(ASK_UNIQUE)
std::unique_ptr<int> keep;
void store(std::unique_ptr<int>& p)       { keep = std::move(p); }  // unique_ptr 이동 대입
#elif defined(ASK_RAW)
int* keep;
void store(int* p)                         { keep = p; }       // 원시 포인터 복사
#endif
```

```bash
# sptr-asm.sh
# sptr-asm.sh — 세 판을 -O2 로 어셈블해 lock 접두 명령과 단일 스레드 검사를 센다
for c in g++ clang++; do
  for k in SHARED UNIQUE RAW; do
    asm=$($c -std=c++20 -O2 -S -o - -DASK_$k sptr07.cpp)
    printf '%-8s %-7s lock 접두 %d개 · __libc_single_threaded 검사 %d곳\n' "$c" "$k" \
      "$(printf '%s\n' "$asm" | grep -cE '^[[:space:]]+lock[[:space:]]')" \
      "$(printf '%s\n' "$asm" | grep -c '__libc_single_threaded')"
  done
done
```

```text
===== bash sptr-asm.sh (exit=0) =====
g++      SHARED  lock 접두 4개 · __libc_single_threaded 검사 4곳
g++      UNIQUE  lock 접두 0개 · __libc_single_threaded 검사 0곳
g++      RAW     lock 접두 0개 · __libc_single_threaded 검사 0곳
clang++  SHARED  lock 접두 4개 · __libc_single_threaded 검사 4곳
clang++  UNIQUE  lock 접두 0개 · __libc_single_threaded 검사 0곳
clang++  RAW     lock 접두 0개 · __libc_single_threaded 검사 0곳
```

```text
===== g++ -std=c++20 -O2 -S -o - -DASK_SHARED sptr07.cpp | grep -E '^[[:space:]]+lock[[:space:]]|__libc_single_threaded' (exit=0) =====
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, 12(%rdi)
	cmpb	$0, __libc_single_threaded(%rip)
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, (%rcx)
	lock addl	$1, 8(%rbx)
	cmpb	$0, __libc_single_threaded(%rip)
	lock xaddl	%eax, (%rcx)
===== clang++ -std=c++20 -O2 -S -o - -DASK_SHARED sptr07.cpp | grep -E '^[[:space:]]+lock[[:space:]]|__libc_single_threaded' (exit=0) =====
	movq	__libc_single_threaded@GOTPCREL(%rip), %rcx
	lock		xaddl	%eax, 8(%rbx)
	movq	__libc_single_threaded@GOTPCREL(%rip), %rax
	movq	__libc_single_threaded@GOTPCREL(%rip), %rcx
	lock		incl	8(%r14)
	lock		xaddl	%eax, 8(%rbx)
	movq	__libc_single_threaded@GOTPCREL(%rip), %rax
	lock		xaddl	%eax, 12(%rbx)
```

- ★★★ **`shared_ptr` 복사 대입 판에 `lock` 접두 명령 4개 · `unique_ptr` 이동 대입과 원시 포인터 복사 판에 0개** — 두 컴파일러가 **같은 수**다.\
  ★ `lock xaddl`(더하고 옛값 받기 — 감소 후 0 이 됐나 보려고) · `lock addl`/`lock incl`(더하기만)이 **계수 증감**이다.
- ★★★ **그런데 `__libc_single_threaded` 검사가 같은 수(4곳)만큼 있다** — libstdc++ 는 **「프로세스가 아직 단일 스레드면 원자 명령을 건너뛰는」 분기**를 넣었다(g++ 판의 `cmpb $0, __libc_single_threaded(%rip)`).\
  ★★ **「명령이 있다」와 「매번 실행된다」는 다르다** — 스레드를 하나도 안 만든 프로그램은 **비원자 경로**를 탈 수 있다. 이것은 **구현의 선택**이다(표준은 「계수 갱신이 경쟁 없이 안전해야 한다」만 요구한다).
- ★ **`unique_ptr` 이동은 0** — 26번의 ④ 창을 **여기서 대신 연 것**이다(제5의 상태). 이동은 **포인터 복사 + 원본에 널 쓰기**라 장부가 없다.

```text
   keep = p;   (shared_ptr 복사 대입)                    keep = std::move(p);   (unique_ptr)
   ├ 새것의 use 계수 +1        lock addl / lock incl      ├ 포인터 옮기기
   ├ 옛것의 use 계수 -1        lock xaddl  → 0 이면 파괴  ├ 원본에 nullptr
   └ (블록의 weak 계수 -1)     lock xaddl  → 0 이면 해제  └ 옛것 delete
   ★ 각 lock 앞에 「단일 스레드인가」 분기 (libstdc++)     ★ lock 0 개
```

★ 왼쪽의 **줄마다 어느 `lock` 이 맡는지는 내 추론**이다 — 실측한 것은 **개수(4 · 0)와 명령 이름**뿐이다.

### (8) ★★ 다른 언어와 나란히 — Rust `Rc`/`Arc` · Python 참조 계수 + 순환 수집기

**언제 쓰나** — 「C++ 의 참조 계수는 무엇을 안 해 주나」를 말할 때.

```text
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
===== python3 --version (exit=0) =====
Python 3.12.3
```

★★★ **Rust — 스레드로 보내면 `Rc` 는 컴파일 에러, `Arc` 는 된다.** C++ 은 둘을 **한 타입(`shared_ptr`)** 으로 만들고 **계수를 늘 원자적으로** 갱신한다.

```rust
// rcsend.rs
// 참조 계수 포인터를 다른 스레드로 보낸다 — -D 대신 cfg 로 Rc 판과 Arc 판을 가른다
use std::thread;

#[cfg(not(arc))]
use std::rc::Rc as Shared;
#[cfg(arc)]
use std::sync::Arc as Shared;

fn main() {
    let a = Shared::new(5);
    let b = Shared::clone(&a);
    println!("strong_count = {}", Shared::strong_count(&a));
    let h = thread::spawn(move || {
        println!("thread 안에서 *b = {}", b);
    });
    h.join().unwrap();
}
```

```text
===== rustc --edition 2021 rcsend.rs -o rcx (cc exit=1) =====
error[E0277]: `Rc<i32>` cannot be sent between threads safely
  --> rcsend.rs:13:27
   |
13 |       let h = thread::spawn(move || {
   |               ------------- ^------
   |               |             |
   |  _____________|_____________within this `{closure@rcsend.rs:13:27: 13:34}`
   | |             |
   | |             required by a bound introduced by this call
14 | |         println!("thread 안에서 *b = {}", b);
15 | |     });
   | |_____^ `Rc<i32>` cannot be sent between threads safely
   |
   = help: within `{closure@rcsend.rs:13:27: 13:34}`, the trait `Send` is not implemented for `Rc<i32>`
note: required because it's used within this closure
  --> rcsend.rs:13:27
   |
13 |     let h = thread::spawn(move || {
   |                           ^^^^^^^
note: required by a bound in `spawn`
  --> /rustc/ded5c06cf21d2b93bffd5d884aa6e96934ee4234/library/std/src/thread/mod.rs:725:1

error: aborting due to 1 previous error

For more information about this error, try `rustc --explain E0277`.
```

```text
===== rustc --edition 2021 --cfg arc rcsend.rs -o rcx && ./rcx (cc exit=0 · run exit=0) =====
strong_count = 2
thread 안에서 *b = 5
```

```cpp
/* spthread.cpp */
// C++ 의 shared_ptr 는 다른 스레드로 넘어가나
#include <cstdio>
#include <memory>
#include <thread>

int main() {
    auto a = std::make_shared<int>(5);
    auto b = a;
    std::printf("use_count = %ld\n", a.use_count());
    std::thread t([b] { std::printf("thread 안에서 *b = %d\n", *b); });
    t.join();
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread spthread.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
use_count = 2
thread 안에서 *b = 5
```

- ★★★ **Rust 의 `Rc<i32>` 는 `Send` 가 아니라 `thread::spawn` 에서 `E0277`** — **비원자 계수**라 스레드를 넘기면 안 된다는 것을 **타입이 말한다.** `--cfg arc` 로 `Arc` 판을 켜면 된다.
- ★★★ **C++ 의 `shared_ptr` 는 그냥 넘어간다**(`cc exit=0`) — 대신 **계수는 늘 원자적**이다((7)의 `lock`). Rust 는 **「원자 비용을 낼지」를 타입으로 고르게** 하고, C++ 은 **늘 내고**(libstdc++ 는 단일 스레드 분기로 줄이고) **스레드 안전 여부를 묻지 않는다.**
- ★★ **C++ 에서 원자적인 것은 「계수」뿐이다** — 가리키는 `int` 에 두 스레드가 쓰면 **여전히 데이터 경쟁**이다. Rust 는 그것도 `Send`/`Sync` 로 막는다.
- ★ Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **41번**(`Rc`/`Arc`·`Weak`)과 **50번**(`Send`/`Sync`) — **둘 다 폴더가 없다.** 이 편이 **한 블록만** 던졌다.

★★ **Python — 참조 계수 + 순환 수집기.** `shared_ptr` 가 못 하는 「순환 회수」를 **추적 수집기가 따로** 한다.

```python
# refcnt.py
# refcnt.py — CPython 의 참조 계수와 순환 수집기. use_count() 와 나란히 본다
import gc
import sys
import weakref

class Node:
    pass

a = Node()
print("(1) 이름 하나        getrefcount =", sys.getrefcount(a))
b = a
print("(2) 이름 둘          getrefcount =", sys.getrefcount(a))
del b
print("(3) 하나를 지운 뒤   getrefcount =", sys.getrefcount(a))

gc.disable()
p, c = Node(), Node()
p.child, c.parent = c, p
wp = weakref.ref(p)
del p, c
print("(4) 순환을 만들고 이름을 지운 뒤  살아 있나 =", wp() is not None)
print("(5) gc.collect() 가 회수한 객체 수 =", gc.collect())
print("(6) 그 뒤                         살아 있나 =", wp() is not None)
```

```text
===== python3 refcnt.py (exit=0) =====
(1) 이름 하나        getrefcount = 2
(2) 이름 둘          getrefcount = 3
(3) 하나를 지운 뒤   getrefcount = 2
(4) 순환을 만들고 이름을 지운 뒤  살아 있나 = True
(5) gc.collect() 가 회수한 객체 수 = 2
(6) 그 뒤                         살아 있나 = False
```

- ★★ **`sys.getrefcount` 가 이름 하나일 때 2** — 인자로 넘기면서 **하나를 더 만들기** 때문이다(`use_count()` 는 그런 덧셈이 없다).
- ★★★ **순환을 만들고 이름을 지워도 살아 있다((4) `True`) — 참조 계수만으로는 C++ 과 같다.** 그런데 **`gc.collect()` 가 2개를 회수**하고 **그 뒤 죽었다((6) `False`).**
- ★★★ **C++ `shared_ptr` 에는 그 수집기가 없다** — (3)의 순환은 **프로그램이 끝날 때까지** 샌다. Java·C# 처럼 **추적 GC 만 있는 언어**는 순환을 **처음부터 문제 삼지 않는다** — 이 편은 그 두 언어를 **던지지 않았다**(Python 판이 「추적 수집이 순환을 회수하나」에 답했다 — 창을 바꿔 답한 것).
- ★ `gc.collect()` 의 반환값(2)은 **CPython 판의 세부**다 — 판이 바뀌면 수가 달라질 수 있다.

### (9) ★★★ `shared_ptr` 을 기본값으로 쓰면 안 되는 이유 — 센 것만으로

| 대가 | `unique_ptr` | `shared_ptr` | 근거 |
|---|---|---|---|
| ★★ **크기** | **8** | **16** | [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1)의 `sizeof` · [15번](../15-raii-resources-as-types/) (5) |
| ★★★ **할당** | **1회 16바이트** | **1회 32바이트**(`make_shared`) · **2회 40바이트**(`new`) | (1) |
| ★★★ **원자 명령**(복사 대입 한 번) | **0개** | **4개** + 단일 스레드 분기 4곳 | (7) |
| ★★★ **수명이 흐려진다** | 소유자가 **타입에 하나** | **순환이면 영원히** 산다 · ASan 이 **판마다 놓친다** | (3) |
| ★★ **해제 시점** | 스코프 끝 | **마지막 강한 참조** · `make_shared` 면 **마지막 약한 참조**까지 자리가 남는다 | (2)(6) |

- ★★★ **「느리다」는 이 표에 없다** — 시간은 재지 않았다. **센 것은 크기 · 할당 · 원자 명령 · 해제 시점**뿐이다.
- ★★★ **판단 규칙** — **소유자가 정말 여럿이고 누가 마지막일지 모를 때만** `shared_ptr`. 그 밖에는 `unique_ptr`(26번), 관찰은 `T*`/`T&`. **팩토리는 `unique_ptr` 를 돌려주면** 받는 쪽이 필요할 때 공유로 바꾼다((1)의 `(4)` — 그때 블록 한 번을 치른다).

## 문법 — 형태와 규칙

### 형태

```text
   auto s = std::make_shared<T>(args...);     기본형 — 할당 1회 (T 와 블록 한 덩어리)
   std::shared_ptr<T> s2(new T);              할당 2회 — 20편의 「Base* raw」 함정도 이 모양
   std::weak_ptr<T> w = s;                    강한 계수를 안 올린다
   if (auto l = w.lock()) { … }               살아 있으면 shared_ptr, 아니면 nullptr
   struct J : std::enable_shared_from_this<J> { … shared_from_this() … };
   std::shared_ptr<int> part(s, &s->member);  별칭 — 멤버를 가리키며 s 의 블록을 공유
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(6)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **만들 때는 `make_shared`** — 단, **큰 객체 + 오래 사는 `weak_ptr`** 면 `new` 판이 메모리를 먼저 돌려준다((1)(6)).
- ★★★ **순환이 생기는 방향 하나는 `weak_ptr`** 로 — 부모 → 자식은 `shared_ptr`, 자식 → 부모는 `weak_ptr`((3)).
- ★★ **`weak_ptr` 는 `lock()` 으로만 쓴다** — 만료되면 `nullptr`((2)).
- ★★ **자기 자신의 `shared_ptr` 는 `shared_from_this()`** — `shared_ptr<T>(this)` 는 블록을 둘 만든다 · 안 맡긴 객체면 `bad_weak_ptr`((4)).
- ★★★ **기본값은 `unique_ptr`** — `shared_ptr` 는 크기·할당·원자 명령·수명의 흐림을 치른다((9)).

## 어디서 틀리나

### 1. ★★★ 「`shared_ptr` 는 포인터 하나에 계수가 붙은 것」

(1)이 반증이다 — **계수는 포인터 옆이 아니라 따로 할당된 제어 블록**에 있다. `new` 판은 **할당이 2회**다.

### 2. ★★★ 「`make_shared` 가 언제나 낫다」

(6)이 반증이다 — **`weak_ptr` 가 남아 있으면 객체 자리(1016바이트)가 안 돌아간다.** `new` 판은 객체 1000바이트를 **먼저** 돌려줬다.

### 3. ★★★ 「순환이 있으면 ASan 이 알려 준다」

(3)이 반증이다 — **g++ 판은 10 / 10 이지만 clang 판은 판마다 놓친다.** 그리고 **메모리가 아닌 자원은 어느 판도 못 본다**(15편).

### 4. ★★ 「순환 누수는 Direct 하나 · Indirect 하나로 나온다」

(3)이 반증이다 — **순수한 순환은 `Indirect leak` 둘**이다. 뿌리가 없다.

### 5. ★★ 「`weak_ptr` 도 계수를 하나 올린다」

(2)가 반증이다 — **강한 계수는 그대로**(2). 올라가는 것은 **약한 계수**이고, 그것은 **블록의 수명**만 늘린다((6)).

### 6. ★★ 「`shared_ptr` 는 스레드 안전하다」

(8)이 반쯤 반증이다 — **계수만 원자적**이다. 가리키는 값은 보호하지 않는다. Rust 는 `Rc` 를 **스레드로 못 보내게** 막는다.

### 7. ★★ 「C++14 에서도 `bad_weak_ptr` 가 났으니 C++14 도 보장한다」

(4)가 반증이다 — **C++14 에서는 미정의**였다. 같은 라이브러리가 두 판에 **같은 코드**를 썼을 뿐이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 급소는 「구현」 칸이다** — 제어 블록이 **있다**는 것은 표준이지만, **어디에 몇 바이트로 무엇과 함께** 사는지는 구현이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **마지막 강한 참조가 죽으면 객체 파괴**((2)(6)) · **`weak_ptr` 는 강한 계수를 안 올린다** · **`lock()` 만료 시 `nullptr`** · **C++17 `bad_weak_ptr`**((4)) · **별칭 생성자의 수명 공유**((5)) · **계수 갱신은 스레드 간 안전** | `use_count` 로그 · 소멸자 로그 · 예외 이름 | ★★★ **순환 누수 — 규칙 위반이 아니다**(경고 0) |
| **조건부 표준** | 특정 판에서만 | ★★ **`weak_from_this` 는 C++17** · **안 맡긴 객체의 `shared_from_this` 는 C++14 에서 미정의 → C++17 에서 `bad_weak_ptr`** | `-std=c++14`/`c++20` | ★★ **C++14 판도 던졌다** — 보장처럼 보인다((4)) |
| **구현 정의** | 문서화 의무 | ★★★ **제어 블록의 배치·크기**(vptr + 4 + 4 · `make_shared` 한 덩어리 32 · `new` 판 24)((1)) · **`make_shared` 가 한 번에 할당하는 것** · ★★★ **원자 명령과 단일 스레드 분기**((7)) | 할당 계수기 · 헤더 줄 · `-O2 -S` | ★★ **「`lock` 이 있다」 ≠ 「매번 실행된다」** |
| **미명시** | 몇 가지 중 하나 | ★ **이 주제에는 해당하는 결론이 없다** | — | — |
| **UB** | 아무 일이나 | ★★ **한 객체에 제어 블록 둘**(`shared_ptr<T>(this)` 두 번) · **C++14 의 안 맡긴 `shared_from_this`** — 이 문서는 **앞의 것을 던지지 않았다** | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | ASan (g++ · clang) |
|---|---|---|---|---|
| ★★★ **순환 참조 누수** | 표준(허용된 코드) | ★★★ **0건** | ★★★ **0건** | ★★ **10 / 10 판 · 판마다 다름** |
| ★★★ **순환이 파일 핸들을 붙들면** | 표준 | **0건** | **0건** | ★★★ **못 본다**(메모리만 본다 — 15편) |
| ★★ **`make_shared` + `weak_ptr` 의 늦은 해제** | 구현 | **0건** | **0건** | ★ **누수가 아니다**(결국 풀린다) — 계수기로만 보인다 |
| ★★ **`shared_ptr` 를 스레드로 넘김** | 표준(허용) | **0건** · `cc exit=0` | — | — · Rust 는 **E0277** |

- ★★ **이 표의 결론** — ★★★ **`shared_ptr` 의 비용과 사고는 전부 「규칙대로 된 코드」에서 난다.** 컴파일러는 0건이고, ASan 은 **메모리 누수만 · 그것도 판에 따라** 본다. **할당 계수기와 로그가 이 주제의 도구**다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 이 편의 코드는 전부 **올바른 C++** 이다. 가까운 것은 (4)의 **C++14 판 `shared_from_this`**(미정의인데 던지고 `run exit=0`)지만, 그것은 **ill-formed 가 아니라 UB** 라 다른 칸이다.
- ★ 예행에서 **`shared_ptr<C[]>(new C[2])` 를 `-std=c++14` 로** 던졌더니 두 컴파일러 다 **경고 0 · `~C` 2회**였다 — C++14 의 `shared_ptr<T[]>` 는 **libstdc++ 의 확장**으로 보이지만, 그 판의 표준 조항을 **열어 보지 못해** 「ill-formed 인가 UB 인가」를 판정하지 않았다(본문에 블록을 싣지 않았다).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 소유자가 하나 | ★★★ **`unique_ptr`**(26번) | 8바이트 · 블록 없음 · `lock` 0 |
| 소유자가 여럿 · 마지막을 모른다 | ★★★ **`make_shared`** | 할당 1회((1)) |
| 큰 객체 + 오래 사는 `weak_ptr` | ★★ **`shared_ptr<T>(new T)`** 또는 `unique_ptr` 설계로 | 객체 자리를 먼저 돌려준다((6)) |
| 순환이 생기는 구조 | ★★★ **한 방향을 `weak_ptr`** | 누수 0((3)) — 28번 |
| 관찰만 한다 | ★★ **`weak_ptr` + `lock()`** 또는 `T*` | 계수를 안 올린다((2)) |
| 멤버 함수에서 자기 수명을 붙든다 | ★★ **`enable_shared_from_this`** | 블록 하나를 공유((4)) |
| 멤버만 넘기며 전체를 살려 둔다 | ★ **별칭 생성자** | (5) |

## 핵심 문장

- ★★★ **제어 블록은 할당 계수기로 보인다** — `make_shared` **1회 32바이트**, `shared_ptr(new T)` **2회 40바이트**, `make_unique` **1회 16바이트**(블록 없음).
- ★★★ **순수한 순환은 `Indirect leak` 둘로 새고, `weak_ptr` 로 한 방향을 바꾸면 0** — 그리고 **clang + ASan 은 그 누수를 판마다 놓친다.**
- ★★★ **`make_shared` 는 `weak_ptr` 가 남아 있는 동안 객체 자리까지 붙든다** — 소멸자는 돌고 **1016바이트는 weak 가 죽을 때** 돌아갔다.
- ★★★ **`shared_ptr` 복사 대입에는 `lock` 접두 명령이 4개, `unique_ptr` 이동에는 0개** — libstdc++ 는 그 앞에 **단일 스레드 분기**를 둔다.
- ★★ **`weak_ptr` 는 강한 계수를 안 올리고, `lock()` 은 만료 뒤 `nullptr`** · **안 맡긴 객체의 `shared_from_this` 는 C++17 부터 `bad_weak_ptr`**.
- ★★ **Rust 는 `Rc` 를 스레드로 보내면 `E0277`, C++ 은 늘 원자 계수로 통과** · **Python 은 순환을 `gc.collect()` 가 회수**하고 C++ 에는 그 수집기가 없다.

## 관련 자료

- [26번](../26-unique-ptr-and-ownership-transfer/) — ★★★ **이 편과 한 사슬.** 소유자가 하나면 **타입**에, 여럿이면 **제어 블록**에 적힌다. (1)의 `make_unique` 16바이트 · (7)의 `UNIQUE` 판 0개가 그 대비다.
- [20번](../20-virtual-destructors-and-polymorphic-deletion/) (1) — `shared_ptr<Base>(new Derived)` 의 삭제자 · `_Sp_counted_ptr<Base*>` · `sizeof` 16 대 8.
- [15번](../15-raii-resources-as-types/) (5) — `sizeof(shared_ptr<int>)` 16 · ASan 은 메모리만 본다.
- [목록의 **28번 주제**](../28-weak-ptr-and-reference-cycles/) — ★★ **`weak_ptr` 와 순환 참조.** 부모↔자식 그림과 끊는 설계의 정본.
- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — **「`shared_ptr` 순환 참조는 해제되지 않는다」** 가 RAII 가 **그대로 두는 것** 목록에 있다. 여기는 그것을 **ASan 으로 재고 `weak_ptr` 로 0 을 본** 쪽이다.
- [`memory-management/`](../../../../memory-management/) — 참조 계수·추적 GC 일반론.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **41번**(`Rc`/`Arc`·`Weak`)·**50번**(`Send`/`Sync`) — **폴더가 없다.** (8)이 한 블록을 던졌다.
- Python 갈래 목록([`python/syntax/README.md`](../../../python/syntax/README.md)) — 참조 계수·순환 수집기 주제는 **목록에 없다**(CPython 내부로 분류돼 있다). (8)이 한 블록을 던졌다.

## 용어 풀이

> **제어 블록(control block)** — `shared_ptr` 가 가리키는 **따로 할당된 장부**. 강한 계수 · 약한 계수 · 삭제자(또는 객체 자체)를 담는다.\
> 예: (1)의 `_Sp_counted_ptr_inplace` · 24바이트 · 16바이트.

> **강한 계수(use count)** — 객체를 살려 두는 `shared_ptr` 의 수. 0 이 되면 **객체를 파괴**한다.\
> 예: (2)의 `use_count()`.

> **약한 계수(weak count)** — 블록을 살려 두는 `weak_ptr` 의 수(+ 강한 참조가 있으면 1). 0 이 되면 **블록을 해제**한다.\
> 예: (6)에서 weak 가 죽을 때 해제된 것.

> **순환 참조(reference cycle)** — `shared_ptr` 끼리 서로를 가리켜 **강한 계수가 0 이 안 되는** 구조.\
> 예: (3)의 `Indirect leak` 2.

> **별칭 생성자(aliasing constructor)** — `shared_ptr<U>(r, p)` — **`r` 의 블록을 공유하면서 `p` 를 가리키는** `shared_ptr`.\
> 예: (5)의 `part`.

> **`enable_shared_from_this`** — 상속하면 객체 안에 `weak_ptr` 를 하나 두어, `shared_from_this()` 로 **기존 블록을 공유하는** `shared_ptr` 를 얻게 하는 기반 클래스.\
> 예: (4)의 `use_count()=2` 와 `bad_weak_ptr`.

> **`lock` 접두(x86)** — 뒤 명령을 **다른 코어와 경쟁 없이 원자적으로** 수행하게 하는 접두어.\
> 예: (7)의 `lock xaddl` 4개.

## 더 들어가면

- **`std::atomic<std::shared_ptr<T>>`(C++20)** — `shared_ptr` **객체 자체**를 여러 스레드가 바꿀 때. 계수의 원자성과는 **다른 문제**다. 이 문서는 던지지 않았다.
- **`allocate_shared`** — 제어 블록을 **사용자 할당자**로 잡는다. 할당 계수기를 할당자로 옮겨 잴 수 있다.
- **`std::make_shared<T[]>`(C++20)** — 배열판. 이 문서는 던지지 않았다.
- **삭제자를 받는 `shared_ptr<T>(p, d)` 와 크기** — 삭제자는 **블록**에 들어가므로 `sizeof(shared_ptr)` 는 **16 그대로**다(26번의 `unique_ptr` 와 대비) — 이 문서는 **숫자를 찍지 않았다.**
