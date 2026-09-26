# cpp/syntax/28 — `weak_ptr` 와 순환 참조 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::weak_ptr`](https://en.cppreference.com/w/cpp/memory/weak_ptr) · [cppreference — `weak_ptr::lock`](https://en.cppreference.com/w/cpp/memory/weak_ptr/lock)\
> ★ **이 배치에서는 위 cppreference 두 쪽을 열지 않았다** — 규칙은 **실행·ASan·TSan·`-O2` 어셈블리·`is_constructible` 격자**로 적었다.
> **실행 검증** — 이 문서의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 대비 블록은 **rustc 1.92.0** 이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`wptr01.cpp` \~ `wptr06.cpp` · `wptr-asm.sh` · `rcweak.rs`).\
> ★★★ **ASan 블록은 마커를 `stderr` 로 찍었다** · 자른 블록은 **자르는 명령을 배너에** 적었다.\
> ★★ **TSan 블록은 `setarch -R` 로 주소 무작위화를 끄고 돌렸다** — 이 머신에서 g++ 13 의 TSan 은 무작위화가 켜져 있으면 **`FATAL: ThreadSanitizer: unexpected memory mapping` 으로 시작도 못 하는 판**이 있었다(예행 5판 중 4판). 그 명령도 배너에 있다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다. **시간은 한 번도 재지 않았다.**
> **버전** — `weak_ptr`·`lock()`·`expired()` 는 **C++11부터**다. 기준은 **C++20**이다(`std::erase_if` 가 C++20).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **[27번](../27-shared-ptr-and-reference-counting/)의 직접 결론이다 — 27번이 잰 것은 다시 재지 않고 인용한다.**\
> [27번](../27-shared-ptr-and-reference-counting/) (3) — **부모↔자식을 둘 다 `shared_ptr` 로 들면 g++ + ASan `Indirect leak` 2건(64바이트) 10 / 10 판 · `Direct leak` 0건** · **자식 → 부모를 `weak_ptr` 로 바꾸면 두 컴파일러 다 누수 0 · `~Parent → ~Child`** · ★★ **clang + ASan 은 그 순환 누수를 판마다 놓친다**(30판 중 14 · 10판 중 6).\
> [27번](../27-shared-ptr-and-reference-counting/) (2)(6) — **`weak_ptr` 는 강한 계수를 안 올린다 · 만료된 `lock()` 은 `nullptr`** · **`make_shared` + `weak_ptr` 면 마지막 `shared_ptr` 가 죽을 때 `~Big` 은 돌지만 해제는 0회, `weak_ptr` 가 죽을 때 1016바이트가 한꺼번에** · (4) **안 맡긴 객체의 `shared_from_this` 는 `bad_weak_ptr`** · (7) **`shared_ptr` 복사 대입에 `lock` 접두 4개**.\
> ★★ **여기서 새로 묻는 것은 다섯이다** — **`expired()` 와 `lock()` 사이의 틈(TOCTOU)** · **트리에서 어느 방향을 약하게 하나** · **캐시·관찰자가 만료를 알아채는 법** · **`weak_ptr` 의 크기와 무엇에서 만들 수 있나** · **`unique_ptr` 에는 `weak_ptr` 가 없다**.
> **경계** — 「RAII 가 못 지우는 것 — `shared_ptr` 순환」의 **논증은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절**이 정본이다. 「참조 계수 일반론」은 [`memory-management/`](../../../../memory-management/) 쪽이다.\
> 「제어 블록의 모양과 비용」은 [27번](../27-shared-ptr-and-reference-counting/), 「raw 포인터가 관찰자로 남는 자리」는 목록의 **29번 주제**다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **TOCTOU 의 횟수** — 2만 판 중 「빈 `shared_ptr` 를 쥔 판」의 수((1) — 실행마다 바뀐다) | ★★★ **두 단계 판에서 그런 판이 「있었나」(참/거짓)** · **한 단계(`lock()`) 판에서 「값이 틀린 판」이 있었나** |
> | ★★ 「10번 돌려 몇 번」의 비율((1)) — **자릿수만** 주장한다 | ★★★ **`lock` 접두 · `cmpxchg` 개수**((2)) · **소멸자 로그 순서**((3)(4)) · **`is_constructible` 0/1 · `sizeof`**((5)) |
> | ASan 리포트의 **PID**·주소 · 어셈블리의 **레지스터·레이블 이름** | ★★ **에러가 나는 줄 · `cc exit`/`run exit`** · **예외 이름(`bad_weak_ptr`)** · **Rust 의 `strong`/`weak` 계수** |

## 한눈에 — 쉽게 말하면

**`weak_ptr` 는 「도서관 대출 현황판을 볼 수 있는 출입증」이다.**

책(객체)을 **빌린 사람**(`shared_ptr`)이 한 명이라도 있으면 책은 서가에 없어지지 않는다.\
출입증을 가진 사람(`weak_ptr`)은 **현황판(제어 블록)을 볼 수 있지만 책을 붙잡아 두지는 못한다.**\
책을 읽고 싶으면 **창구에서 「지금 빌릴 수 있나」를 묻고 그 자리에서 빌려야**(`lock()`) 한다.

- **「현황판을 보고 → 창구로 걸어간다」는 두 번의 행동이다** — 그 사이에 마지막 대출자가 책을 반납하고 서가가 치워질 수 있다((1)).
- **창구의 「확인하고 빌리기」는 한 번의 행동이다** — 빌려 주거나 「없다」고 말하거나 둘 중 하나다((2)).
- **부모 책이 부록을 빌려 두고, 부록은 부모를 출입증으로만 본다** — 그래야 둘 다 반납된다((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 출입증 | ★★ **`weak_ptr`** — 강한 계수를 안 올린다 · **16바이트** | (5) · 27편 (2) |
| 현황판만 본다 | ★★★ **`expired()`** — 원자 명령 **0개**(평범한 읽기 한 번) | (2) |
| 창구에서 확인하고 빌리기 | ★★★ **`lock()`** — **`lock cmpxchg` 1개**, 0 이면 포기하는 **재시도 루프** | (2) |
| 보고 → 걸어가는 사이에 반납 | ★★★ **TOCTOU** — 「살아 있다」를 들은 뒤 **빈 `shared_ptr`** | (1) |
| 부모가 부록을 빌린다 | ★★★ **부모 → 자식 `shared_ptr` · 자식 → 부모 `weak_ptr`** | (3) |
| 도서관 목록(캐시) | ★★ **`map<id, weak_ptr>`** — 반납된 칸이 **목록에 남는다** | (4) |
| 대출증 없는 개인 책 | ★★ **`unique_ptr`** — 출입증을 **만들 길이 없다**(에러) | (5) |

```text
   shared_ptr s ──┐                       weak_ptr w ──┐
                  ▼                                    ▼
             ┌─────────────── 제어 블록 ───────────────────┐
             │  use  (강한 계수)   weak (약한 계수 + 1)      │──▶ [ 객체 ]
             └──────────────────────────────────────────────┘
   w.expired()   use 를 한 번 읽는다                 ── 읽은 뒤에 use 가 0 이 될 수 있다
   w.lock()      use 가 0 이 아니면 use+1 을 「원자적으로」 ── 성공하면 shared_ptr, 아니면 비어 있다
```

## 이 주제가 답하려는 질문

1. ★★★ **`expired()` 로 확인한 뒤 `lock()` 하면 무엇이 틀리나** — 정말 그 틈이 열리나, `lock()` 한 번이면 왜 안 열리나((1)(2)).
2. ★★★ **트리에서 어느 방향을 `weak_ptr` 로 두나** — 반대로 두면 무엇이 사라지나((3)).
3. ★★ **캐시·관찰자는 대상이 죽은 것을 어떻게 아나** — 만료된 칸은 누가 치우나((4)).
4. ★★ **`weak_ptr` 는 무엇에서 만들 수 있나** — `unique_ptr` 에서는 왜 안 되나((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ④ 어셈블리와 실행 판정 격자다

★★★ **이 주제의 본체는 ④ `-O2` 어셈블리다** — `expired()` 와 `lock()` 이 **무슨 명령이 되는지**가 곧 TOCTOU 의 원인이다.\
★★ **그 짝이 「N판 실행 판정」이다** — 두 스레드가 다투는 결과는 **횟수가 아니라 참/거짓**으로 읽는다. ★ **ASan 은 트리 설계의 누수 판정**에만 쓴다.

```text
① 다섯 층 표            lock 의 원자성은 표준 · 명령 모양은 구현                        (구현 세부사항 절)
② 두 컴파일러 대조       TOCTOU · 트리 · 캐시 · 에러 · 격자 — 전부 두 컴파일러로       (1)(3)(4)(5)
③ ASan / TSan           트리 두 설계 누수 0 · ★ TSan 은 TOCTOU 에 침묵                 (1)(3)
④ ★ 어셈블리(-O2)       expired 는 lock 0 · lock 은 lock cmpxchg 1 + 재시도 루프       (2)
⑤ 경고 격자             —                                                              부적용
⑥ <type_traits>·sizeof  is_constructible 10칸 · sizeof 16                              (5)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **`lock()` 이 원자적이라는 것은 표준, `cmpxchg` 루프는 구현** | **쓴다** |
| ② 두 컴파일러 대조 | ★★ 실행 출력이 **한 글자도 같은지** — 트리·캐시·격자 전부 같았다 · 에러는 문구가 다르다 | **쓴다** |
| ③ ASan · TSan | ★★ ASan 은 트리 설계 **누수 0** · ★★★ **TSan 은 TOCTOU 를 보고하지 않는다**(경쟁이 아니라 **논리의 틈**이다) | **쓴다** |
| ★★★ **④ 어셈블리(-O2)** | ★★★ **본체** — `expired` **lock 0 · cmpxchg 0**, `lock` **lock 1 · cmpxchg 1** | **쓴다** |
| ⑤ 경고 격자 | ★ **부적용** — TOCTOU 도 트리 설계도 **규칙대로 된 코드**다. 경고가 나올 자리가 아니다(18-B 「잴 것이 없다」) | **안 쓴다** |
| ⑥ `<type_traits>`·`sizeof` | ★★ **`weak_ptr<int>` 를 만들 수 있는 칸 6 / 10** · `sizeof` **16** | **쓴다** |

- ★★ **창을 바꿔 답한 자리(제5의 상태)** — 「두 스레드가 다툰다」를 **TSan 에게도 물었는데 침묵**했다. 그래서 같은 질문을 **N판 실행 판정**으로 다시 물었다. TSan 이 못 보는 이유는 (1)의 끝에 있다.

### (1) ★★★ `expired()` 다음 `lock()` — 그 틈이 정말 열리나

**언제 쓰나** — `weak_ptr` 를 든 쪽이 **다른 스레드가 놓을 수 있는 객체**를 쓸 때.

```cpp
/* wptr01.cpp */
// expired() 로 살아 있음을 확인한 뒤 lock() 한다 — 그 사이에 다른 스레드가 마지막 shared_ptr 를 놓는다
// 기본은 「확인 → lock」 두 단계, -DASK_ONESTEP 이면 lock() 한 번으로 묻는다
// 판마다 새 shared_ptr 와 새 스레드를 만든다 — 한 판 안에서 두 스레드가 같은 제어 블록을 다툰다
#include <atomic>
#include <cstdio>
#include <memory>
#include <thread>

int main(int argc, char**) {
    const int trials = 20000;
    int said_alive = 0;      // 첫 질문에 「살아 있다」고 답한 판
    int got_null = 0;        // 그런데 손에 쥔 shared_ptr 가 비어 있던 판
    int wrong_value = 0;     // 손에 쥔 shared_ptr 가 가리키는 값이 기대와 다른 판
    for (int i = 0; i < trials; ++i) {
        auto s = std::make_shared<int>(i);
        std::weak_ptr<int> w = s;
        std::atomic<bool> go{false};
        std::thread owner([&] {
            while (!go.load(std::memory_order_acquire)) {}
            s.reset();                                   // 마지막 강한 참조를 놓는다
        });
        go.store(true, std::memory_order_release);
#ifdef ASK_ONESTEP
        if (auto p = w.lock()) {
            ++said_alive;
            if (*p != i) ++wrong_value;
        }
#else
        if (!w.expired()) {
            ++said_alive;
            auto p = w.lock();
            if (!p) ++got_null;
            else if (*p != i) ++wrong_value;
        }
#endif
        owner.join();
    }
    if (argc > 1)                                        // 인자를 주면 수를 그대로 찍는다(판마다 바뀐다)
        std::printf("판 %d · 살아 있다고 답한 판 %d · 그 뒤 빈 shared_ptr %d · 값이 틀린 판 %d\n",
                    trials, said_alive, got_null, wrong_value);
    else
        std::printf("빈 shared_ptr 를 쥔 판이 있었나 %d · 값이 틀린 판이 있었나 %d\n",
                    (int)(got_null > 0), (int)(wrong_value > 0));
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 0 · 값이 틀린 판이 있었나 0
```

- ★★★ **두 단계 판(기본) — 「빈 `shared_ptr` 를 쥔 판이 있었나 1」.** `expired()` 가 **「살아 있다」고 답한 뒤** `lock()` 이 **빈 것**을 돌려준 판이 있었다.\
  **확인과 사용 사이에 마지막 소유자가 놓았다** — 이것이 **TOCTOU**(검사 시점 대 사용 시점)다.
- ★★★ **한 단계 판(`-DASK_ONESTEP`) — 「값이 틀린 판이 있었나 0」.** `lock()` 이 준 것이 비어 있지 않으면 **언제나 살아 있는 객체**였다. 이 판에는 **두 번째 질문 자체가 없어서** 「빈 것을 쥔 판」이 원리상 0 이다.
- ★ **clang 도 같은 두 줄**이었다 —

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 0 · 값이 틀린 판이 있었나 0
```

★★ **흔들리는 칸을 따로 센다** — 한 판(2만 번) 안에서 틈이 **몇 번** 열렸는지는 실행마다 다르다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && ./ex n (cc exit=0 · run exit=0) =====
판 20000 · 살아 있다고 답한 판 19996 · 그 뒤 빈 shared_ptr 17 · 값이 틀린 판 0
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread wptr01.cpp -o ex && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do case $(./ex) in *'쥔 판이 있었나 1'*) n=$((n+1));; esac; done; echo "두 단계 판 — 10번 돌려 빈 shared_ptr 를 쥔 적이 있던 번 $n" (exit=0) =====
두 단계 판 — 10번 돌려 빈 shared_ptr 를 쥔 적이 있던 번 10
===== g++ -std=c++20 -Wall -Wextra -pedantic -pthread -DASK_ONESTEP wptr01.cpp -o ex && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do case $(./ex) in *'값이 틀린 판이 있었나 1'*) n=$((n+1));; esac; done; echo "한 단계 판 — 10번 돌려 값이 틀린 적이 있던 번 $n" (exit=0) =====
한 단계 판 — 10번 돌려 값이 틀린 적이 있던 번 0
```

- ★★ **2만 번 중 몇 번**(위 캡처의 수)은 **흔들리는 칸**이다 — 예행에서 g++ 판이 **4\~31번**, clang 판이 **9\~24번** 사이였다. **주장하는 것은 「열린다」 뿐**이다.
- ★★ **「10번 돌려 몇 번」도 흔들리는 칸**이다 — 이 캡처와 예행에서는 **10 / 10** 이었지만, 비율을 성질로 적지 않는다.

★★★ **TSan 에게 물으면 — 침묵한다.**

```text
===== g++ -std=c++20 -fsanitize=thread -g -pthread wptr01.cpp -o ext && setarch -R ./ext 2>&1 (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
===== clang++ -std=c++20 -fsanitize=thread -g -pthread wptr01.cpp -o ext && setarch -R ./ext 2>&1 (cc exit=0 · run exit=0) =====
빈 shared_ptr 를 쥔 판이 있었나 1 · 값이 틀린 판이 있었나 0
```

- ★★★ **두 컴파일러의 TSan 이 경고 한 줄 없이 `run exit=0`** 이고, **틈은 그대로 열렸다**(`있었나 1`).
- ★★ **이유 — 이것은 데이터 경쟁이 아니다.** `expired()` 와 `lock()` 은 **각각 원자적으로** 제어 블록을 읽고 쓴다. TSan 이 찾는 것은 「**동기화 없이 같은 메모리를 동시에 쓰는 것**」이지 「**두 원자 연산 사이에 세상이 바뀌는 것**」이 아니다.\
  ★★★ **「TSan 이 조용하다」는 「스레드 안전하다」가 아니다** — 27편의 「ASan 이 조용하다 ≠ 순환이 없다」와 **같은 부류의 새 항목**이다.

```text
   두 단계 (틈이 있다)                              한 단계
   스레드 A              스레드 B                    스레드 A              스레드 B
   w.expired() → false                               w.lock()  ── use>0 이면 use+1 을 원자적으로
        │                s.reset()  use 1→0 · ~int        │                 s.reset()
        ▼                                                  ▼
   w.lock()   → 빈 shared_ptr  ★ 「살아 있다」를 믿었다   p 가 비었거나, 비지 않았으면 끝까지 산다
```

### (2) ★★★ 왜 한 번이면 되나 — `expired()` 와 `lock()` 의 명령을 센다

**언제 쓰나** — 「`lock()` 도 결국 확인하고 올리는 두 단계 아닌가」를 의심할 때.

```cpp
/* wptr02.cpp */
// expired() 와 lock() 이 각각 무슨 명령이 되나 — -DASK_EXPIRED · -DASK_LOCK 로 한 함수만 남긴다
#include <memory>

#if defined(ASK_EXPIRED)
bool ask(const std::weak_ptr<int>& w) { return !w.expired(); }
#elif defined(ASK_LOCK)
std::shared_ptr<int> ask(const std::weak_ptr<int>& w) { return w.lock(); }
#endif
```

```bash
# wptr-asm.sh
# wptr-asm.sh — expired() 판과 lock() 판을 -O2 로 어셈블해 lock 접두 명령과 cmpxchg 를 센다
for c in g++ clang++; do
  for k in EXPIRED LOCK; do
    asm=$($c -std=c++20 -O2 -S -o - -DASK_$k wptr02.cpp)
    printf '%-8s %-8s lock 접두 %d개 · cmpxchg %d개\n' "$c" "$k" \
      "$(printf '%s\n' "$asm" | grep -cE '^[[:space:]]+lock[[:space:]]')" \
      "$(printf '%s\n' "$asm" | grep -cE 'cmpxchg')"
  done
done
```

```text
===== bash wptr-asm.sh (exit=0) =====
g++      EXPIRED  lock 접두 0개 · cmpxchg 0개
g++      LOCK     lock 접두 1개 · cmpxchg 1개
clang++  EXPIRED  lock 접두 0개 · cmpxchg 0개
clang++  LOCK     lock 접두 1개 · cmpxchg 1개
```

- ★★★ **`expired()` 판은 `lock` 접두 0 · `cmpxchg` 0, `lock()` 판은 `lock` 접두 1 · `cmpxchg` 1** — 두 컴파일러가 **같은 수**다.
- ★★ **몸통을 보면 이유가 보인다** —

```text
===== g++ -std=c++20 -O2 -S -o - -DASK_EXPIRED wptr02.cpp | sed -n '/^_Z3ask/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.(cfi|p2align)' (exit=0) =====
_Z3askRKSt8weak_ptrIiE:
.LFB3348:
	endbr64
	movq	8(%rdi), %rdx
	xorl	%eax, %eax
	testq	%rdx, %rdx
	je	.L1
	movl	8(%rdx), %eax
	testl	%eax, %eax
	setne	%al
.L1:
	ret
===== g++ -std=c++20 -O2 -S -o - -DASK_LOCK wptr02.cpp | sed -n '/^_Z3ask/,/\.cfi_endproc/p' | grep -vE '^[[:space:]]+\.(cfi|p2align)' (exit=0) =====
_Z3askRKSt8weak_ptrIiE:
.LFB3348:
	endbr64
	movq	8(%rsi), %rax
	movq	%rax, 8(%rdi)
	testq	%rax, %rax
	je	.L2
	leaq	8(%rax), %rdx
	movl	8(%rax), %eax
.L5:
	testl	%eax, %eax
	je	.L3
	leal	1(%rax), %ecx
	lock cmpxchgl	%ecx, (%rdx)
	jne	.L5
	movq	8(%rdi), %rax
	testq	%rax, %rax
	je	.L2
	movl	8(%rax), %eax
	testl	%eax, %eax
	je	.L2
	movq	(%rsi), %rax
	movq	%rax, (%rdi)
	movq	%rdi, %rax
	ret
.L3:
	movq	$0, 8(%rdi)
.L2:
	xorl	%eax, %eax
	movq	%rax, (%rdi)
	movq	%rdi, %rax
	ret
```

- ★★★ **`expired()` 는 `movl 8(%rdx), %eax` → `testl` → `setne` — 강한 계수를 한 번 읽을 뿐**이다. 읽은 값은 **그 순간의 사진**이다.
- ★★★ **`lock()` 은 `.L5` 로 돌아가는 루프다** — 계수가 0 이면(`je .L3`) **포기**하고, 아니면 **`lock cmpxchgl` 로 「아직 그 값이면 +1」** 을 시도하고, 그 사이 누가 바꿨으면(`jne .L5`) **다시 읽고 다시 시도**한다.\
  ★ **「0 이 아님을 확인」과 「+1」 이 한 명령 안에서 묶인다** — 그래서 **확인과 사용 사이에 틈이 없다.**
- ★ **줄마다의 뜻(무엇이 강한 계수인지)은 내 읽기**다 — 실측한 것은 **개수와 명령 이름, 루프 모양**뿐이다. 27편 (7)의 `shared_ptr` 복사와 달리 **`__libc_single_threaded` 분기가 이 몸통에는 없었다**(g++ 판).

### (3) ★★★ 트리 — 어느 방향을 `weak_ptr` 로 두나

**언제 쓰나** — 부모가 자식을, 자식이 부모를 알아야 하는 구조(트리·DOM·장면 그래프)를 설계할 때.\
★ **둘 다 `shared_ptr` 인 판은 27편 (3)이 쟀다**(`Indirect leak` 2). 여기서는 **한쪽을 약하게 하는 두 판**을 견준다.

```cpp
/* wptr03.cpp */
// 부모 하나 · 자식 둘 — 어느 방향을 weak_ptr 로 두나. 두 설계 × 무엇을 쥐고 있나
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <memory>
#include <vector>

struct A {                                   // 설계 A — 부모 → 자식 shared, 자식 → 부모 weak
    char name;
    std::vector<std::shared_ptr<A>> kids;
    std::weak_ptr<A> parent;
    explicit A(char n) : name(n) {}
    ~A() { std::fprintf(stderr, "      ~A %c\n", name); }
};
struct B {                                   // 설계 B — 부모 → 자식 weak, 자식 → 부모 shared
    char name;
    std::vector<std::weak_ptr<B>> kids;
    std::shared_ptr<B> parent;
    explicit B(char n) : name(n) {}
    ~B() { std::fprintf(stderr, "      ~B %c\n", name); }
};

template <class N>
std::shared_ptr<N> build(bool keep_child) {  // 뿌리 r 과 자식 x · y 를 잇고, 뿌리나 자식 x 하나만 돌려준다
    auto r = std::make_shared<N>('r');
    auto x = std::make_shared<N>('x');
    auto y = std::make_shared<N>('y');
    r->kids = {x, y};
    x->parent = r;
    y->parent = r;
    return keep_child ? x : r;
}

template <class N>
int live_kids(const N& n) {
    int k = 0;
    for (const auto& c : n.kids) {
        if constexpr (std::is_same_v<N, A>) k += c != nullptr;
        else k += !c.expired();
    }
    return k;
}

template <class N>
bool parent_alive(const N& n) {
    if constexpr (std::is_same_v<N, A>) return !n.parent.expired();
    else return n.parent != nullptr;
}

template <class N>
void run(const char* label, bool keep_child) {
    std::fprintf(stderr, "%s\n", label);
    auto held = build<N>(keep_child);
    if (keep_child)
        std::fprintf(stderr, "    쥔 것 = 자식 %c · 그 부모가 살아 있나 %d\n", held->name, (int)parent_alive(*held));
    else
        std::fprintf(stderr, "    쥔 것 = 뿌리 %c · 살아 있는 자식 수 %d\n", held->name, live_kids(*held));
    std::fprintf(stderr, "    쥔 것을 놓는다\n");
}

int main() {
    run<A>("(A1) 설계 A · 뿌리를 쥔다", false);
    run<A>("(A2) 설계 A · 자식 x 를 쥔다", true);
    run<B>("(B1) 설계 B · 뿌리를 쥔다", false);
    run<B>("(B2) 설계 B · 자식 x 를 쥔다", true);
    std::fprintf(stderr, "(끝) main 을 나간다\n");
}
```

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. wptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=0) =====
(A1) 설계 A · 뿌리를 쥔다
    쥔 것 = 뿌리 r · 살아 있는 자식 수 2
    쥔 것을 놓는다
      ~A r
      ~A x
      ~A y
(A2) 설계 A · 자식 x 를 쥔다
      ~A r
      ~A y
    쥔 것 = 자식 x · 그 부모가 살아 있나 0
    쥔 것을 놓는다
      ~A x
(B1) 설계 B · 뿌리를 쥔다
      ~B y
      ~B x
    쥔 것 = 뿌리 r · 살아 있는 자식 수 0
    쥔 것을 놓는다
      ~B r
(B2) 설계 B · 자식 x 를 쥔다
      ~B y
    쥔 것 = 자식 x · 그 부모가 살아 있나 1
    쥔 것을 놓는다
      ~B x
      ~B r
(끝) main 을 나간다
```

- ★★★ **두 설계 다 누수 0**(`run exit=0`, 리포트 없음) — **순환은 둘 다 끊겼다.** 그런데 **살아남는 것이 다르다.**
- ★★★ **설계 A(부모 → 자식 `shared_ptr`)** — 뿌리를 쥐면 **자식 둘이 산다**(A1). 자식만 쥐면 **부모와 형제가 먼저 죽고**(`~A r · ~A y`) 자식은 **부모가 죽었다는 것을 안다**(A2 `0`).
- ★★★ **설계 B(자식 → 부모 `shared_ptr`)** — 뿌리를 쥐어도 **자식이 `build()` 를 나오자마자 죽는다**(B1 — `~B y · ~B x` 가 「쥔 것」 줄보다 **먼저**, 살아 있는 자식 **0**).\
  자식 하나를 쥐면 그 자식이 **부모를 살려 두고**(B2 `1`) **형제는 죽는다**(`~B y`).
- ★★ **규칙** — **소유는 「누가 누구를 만들고 지우나」의 방향**으로, **약한 참조는 그 반대 방향**으로 둔다. 트리에서는 **부모가 자식을 소유**한다 — 그래서 **자식 → 부모가 `weak_ptr`** 다.\
  B 는 **「순환만 끊으면 된다」의 반례**다 — 누수는 없지만 **자식을 아무도 소유하지 않는다.**
- ★ **clang + ASan 도 한 글자도 같다** —

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. wptr03.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | sed -E 's# \(/[^ ]*/(exa\+0x[0-9a-f]+)\) \(BuildId: [0-9a-f]+\)# (\1)#' (cc exit=0 · run exit=0) =====
(A1) 설계 A · 뿌리를 쥔다
    쥔 것 = 뿌리 r · 살아 있는 자식 수 2
    쥔 것을 놓는다
      ~A r
      ~A x
      ~A y
(A2) 설계 A · 자식 x 를 쥔다
      ~A r
      ~A y
    쥔 것 = 자식 x · 그 부모가 살아 있나 0
    쥔 것을 놓는다
      ~A x
(B1) 설계 B · 뿌리를 쥔다
      ~B y
      ~B x
    쥔 것 = 뿌리 r · 살아 있는 자식 수 0
    쥔 것을 놓는다
      ~B r
(B2) 설계 B · 자식 x 를 쥔다
      ~B y
    쥔 것 = 자식 x · 그 부모가 살아 있나 1
    쥔 것을 놓는다
      ~B x
      ~B r
(끝) main 을 나간다
```

```text
   설계 A  (부모 소유)                          설계 B  (자식이 부모를 소유)
        r ──shared──▶ x , y                          r ◀──shared── x , y
        ▲ ─ ─ weak ─ ─ ┘                             └ ─ ─ weak ─ ─ ▶
   뿌리를 쥐면 : r · x · y 산다                  뿌리를 쥐면 : r 만 산다   ★ 자식 0
   x 를 쥐면   : r · y 죽음, x.parent 만료        x 를 쥐면   : x · r 산다, y 죽음
   누수 0                                        누수 0
   ★ 약한 참조는 「소유의 반대 방향」에 둔다
```

### (4) ★★ 캐시와 관찰자 — 만료를 알아채는 법, 그리고 치우는 법

**언제 쓰나** — 「쓰는 사람이 있는 동안만 들고 있고 싶은」 목록 — 텍스처 캐시 · 이벤트 구독자.

```cpp
/* wptr04.cpp */
// weak_ptr 캐시와 관찰자 목록 — 쓰는 쪽이 다 놓으면 캐시·목록은 그것을 어떻게 알아채나
#include <cstdio>
#include <functional>
#include <map>
#include <memory>
#include <vector>

struct Texture {
    int id;
    explicit Texture(int i) : id(i) { std::printf("      [load] %d\n", id); }
    ~Texture() { std::printf("      [drop] %d\n", id); }
};

std::map<int, std::weak_ptr<Texture>> cache;

std::shared_ptr<Texture> get(int id) {
    auto& slot = cache[id];
    if (auto sp = slot.lock()) return sp;            // 아직 누가 쓰고 있다
    auto sp = std::make_shared<Texture>(id);         // 아무도 안 쓴다 — 새로 만든다
    slot = sp;
    return sp;
}

int expired_entries() {
    int n = 0;
    for (const auto& [id, w] : cache) n += w.expired();
    return n;
}

struct Listener {
    char name;
    void on_event() const { std::printf("      %c 가 받았다\n", name); }
};

struct Subject {
    std::vector<std::weak_ptr<Listener>> subs;
    void notify() {
        int dead = 0;
        for (const auto& w : subs) {
            if (auto l = w.lock()) l->on_event();
            else ++dead;
        }
        std::erase_if(subs, [](const std::weak_ptr<Listener>& w) { return w.expired(); });
        std::printf("      죽은 구독자 %d · 남은 구독 %zu\n", dead, subs.size());
    }
};

int main() {
    std::printf("(1) a = get(1); b = get(1);\n");
    auto a = get(1);
    auto b = get(1);
    std::printf("    a 와 b 가 같은 객체인가 %d · use_count %ld\n", (int)(a == b), a.use_count());
    std::printf("(2) a.reset(); b.reset();\n");
    a.reset();
    b.reset();
    std::printf("    캐시 크기 %zu · 만료된 항목 %d\n", cache.size(), expired_entries());
    std::printf("(3) c = get(1);\n");
    auto c = get(1);
    std::printf("(4) get(2) · get(3) 을 받자마자 버린다\n");
    get(2);
    get(3);
    std::printf("    캐시 크기 %zu · 만료된 항목 %d\n", cache.size(), expired_entries());
    std::erase_if(cache, [](const auto& kv) { return kv.second.expired(); });
    std::printf("    만료 항목을 쓸어낸 뒤 캐시 크기 %zu\n", cache.size());

    std::printf("(5) 관찰자 p · q · r 을 구독시키고 q 를 놓는다\n");
    Subject s;
    auto p = std::make_shared<Listener>(Listener{'p'});
    auto q = std::make_shared<Listener>(Listener{'q'});
    auto r = std::make_shared<Listener>(Listener{'r'});
    s.subs = {p, q, r};
    q.reset();
    s.notify();
    std::printf("(6) 한 번 더 알린다\n");
    s.notify();
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic wptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a = get(1); b = get(1);
      [load] 1
    a 와 b 가 같은 객체인가 1 · use_count 2
(2) a.reset(); b.reset();
      [drop] 1
    캐시 크기 1 · 만료된 항목 1
(3) c = get(1);
      [load] 1
(4) get(2) · get(3) 을 받자마자 버린다
      [load] 2
      [drop] 2
      [load] 3
      [drop] 3
    캐시 크기 3 · 만료된 항목 2
    만료 항목을 쓸어낸 뒤 캐시 크기 1
(5) 관찰자 p · q · r 을 구독시키고 q 를 놓는다
      p 가 받았다
      r 가 받았다
      죽은 구독자 1 · 남은 구독 2
(6) 한 번 더 알린다
      p 가 받았다
      r 가 받았다
      죽은 구독자 0 · 남은 구독 2
      [drop] 1
```

- ★★★ **캐시는 객체를 살려 두지 않는다** — (1)에서 `a`·`b` 가 같은 객체를 받고(`use_count 2`), 둘이 놓자 **`[drop] 1`** · (3)에서 다시 부르면 **`[load] 1` 이 또 찍힌다**(새로 만든다).
- ★★★ **만료된 칸은 스스로 사라지지 않는다** — (2)에서 **캐시 크기 1 · 만료 1**, (4)에서 **크기 3 · 만료 2**. `std::erase_if` 로 **직접 쓸어내야** 크기가 1 로 준다.\
  ★★ **그 칸이 `make_shared` 로 만든 객체의 `weak_ptr` 라면, 쓸기 전까지 객체 자리 전체를 붙든다** — 27편 (6)의 「1016바이트는 weak 가 죽을 때」가 **여기서 일어난다.**
- ★★ **관찰자 목록** — `notify()` 가 `lock()` 에 실패한 구독자를 **건너뛰고**(`q` 는 안 받았다) **세고 치운다**(죽은 구독자 1 · 남은 구독 2 → 다음 알림에서 0).
- ★ **clang 도 한 글자도 같다** —

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic wptr04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) a = get(1); b = get(1);
      [load] 1
    a 와 b 가 같은 객체인가 1 · use_count 2
(2) a.reset(); b.reset();
      [drop] 1
    캐시 크기 1 · 만료된 항목 1
(3) c = get(1);
      [load] 1
(4) get(2) · get(3) 을 받자마자 버린다
      [load] 2
      [drop] 2
      [load] 3
      [drop] 3
    캐시 크기 3 · 만료된 항목 2
    만료 항목을 쓸어낸 뒤 캐시 크기 1
(5) 관찰자 p · q · r 을 구독시키고 q 를 놓는다
      p 가 받았다
      r 가 받았다
      죽은 구독자 1 · 남은 구독 2
(6) 한 번 더 알린다
      p 가 받았다
      r 가 받았다
      죽은 구독자 0 · 남은 구독 2
      [drop] 1
```

```text
   cache[1] : weak ─┐          a, b 가 쥔 동안 : lock() 성공 → 같은 객체 (use 2)
                    ▼          a, b 가 놓으면  : [drop] 1 · 칸은 남는다 (만료)
             [ 제어 블록 ]      다시 get(1)     : lock() 실패 → 새로 만들어 칸을 덮는다
   ★ 칸을 지우는 것은 erase_if 뿐 — 캐시 크기 3 · 만료 2 → 1
```

### (5) ★★ `weak_ptr` 는 무엇에서 만들 수 있나 — 그리고 `unique_ptr` 에는 왜 없나

**언제 쓰나** — 「`unique_ptr` 가 가진 것을 약하게 가리키고 싶다」는 설계가 떠오를 때.

```cpp
/* wptr05.cpp */
// weak_ptr 를 unique_ptr 에서 만들 수 있나 · 곧바로 역참조할 수 있나
#include <memory>

int main() {
    auto u = std::make_unique<int>(1);
    auto s = std::make_shared<int>(2);
    std::weak_ptr<int> w1 = s;          // 1. shared_ptr 에서
    std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
    int a = *w1;                        // 3. 역참조
    int b = *w1.lock();                 // 4. lock() 을 거쳐 역참조
    (void)w2; (void)a; (void)b;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 wptr05.cpp -o ex (cc exit=1) =====
wptr05.cpp: In function ‘int main()’:
wptr05.cpp:8:29: error: conversion from ‘std::unique_ptr<int, std::default_delete<int> >’ to non-scalar type ‘std::weak_ptr<int>’ requested
    8 |     std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
      |                             ^
wptr05.cpp:9:13: error: no match for ‘operator*’ (operand type is ‘std::weak_ptr<int>’)
    9 |     int a = *w1;                        // 3. 역참조
      |             ^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 wptr05.cpp -o ex (cc exit=1) =====
wptr05.cpp:8:24: error: no viable conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'std::weak_ptr<int>'
    8 |     std::weak_ptr<int> w2 = u;          // 2. unique_ptr 에서
      |                        ^    ~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:831:7: note: candidate constructor not viable: no known conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'const weak_ptr<int> &' for 1st argument
  831 |       weak_ptr(const weak_ptr&) noexcept = default;
      |       ^        ~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:837:7: note: candidate constructor not viable: no known conversion from '__detail::__unique_ptr_t<int>' (aka 'unique_ptr<int>') to 'weak_ptr<int> &&' for 1st argument
  837 |       weak_ptr(weak_ptr&&) noexcept = default;
      |       ^        ~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:828:2: note: candidate template ignored: could not match 'shared_ptr' against 'unique_ptr'
  828 |         weak_ptr(const shared_ptr<_Yp>& __r) noexcept
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:834:2: note: candidate template ignored: could not match 'weak_ptr' against 'unique_ptr'
  834 |         weak_ptr(const weak_ptr<_Yp>& __r) noexcept
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/shared_ptr.h:840:2: note: candidate template ignored: could not match 'weak_ptr' against 'unique_ptr'
  840 |         weak_ptr(weak_ptr<_Yp>&& __r) noexcept
      |         ^
wptr05.cpp:9:13: error: indirection requires pointer operand ('std::weak_ptr<int>' invalid)
    9 |     int a = *w1;                        // 3. 역참조
      |             ^~~
2 errors generated.
```

- ★★★ **`unique_ptr` 에서 `weak_ptr` 를 만드는 줄(8행)이 두 컴파일러 다 에러**다 — clang 의 후보 목록이 이유를 말한다. **`weak_ptr` 의 생성자는 `shared_ptr` 또는 `weak_ptr` 만 받는다**(`could not match 'shared_ptr' against 'unique_ptr'`).
- ★★★ **이유 — `unique_ptr` 에는 제어 블록이 없다.** `weak_ptr` 가 보는 「현황판」 자체가 없으니 **만료를 물을 곳이 없다**(27편 (1) — `make_unique` 는 **1회 16바이트**, 블록 없음).
- ★★ **`*w1` 도 에러(9행)** — `weak_ptr` 에는 **`operator*` 가 없다.** 반드시 **`lock()` 을 거쳐야**(10행은 에러가 없다) 쓸 수 있다 — **「확인 없이 쓰는 길」을 타입이 막았다.**
- ★ 에러 수 — g++ **2** · clang **2**(`2 errors generated.`). 문구는 다르고 **줄은 같다**.

★★ **같은 질문을 `is_constructible` 격자로 — 그리고 만료된 것을 승격하는 두 길.**

```cpp
/* wptr06.cpp */
// weak_ptr<int> 를 무엇에서 만들 수 있나 — is_constructible 격자와 크기
#include <cstdio>
#include <memory>
#include <type_traits>

struct Base { virtual ~Base() = default; };
struct Derived : Base {};

int ones = 0, cells = 0;

template <class To, class From>
void row(const char* label) {
    bool v = std::is_constructible_v<To, From>;
    ones += v; ++cells;
    std::printf("  %-52s %d\n", label, (int)v);
}

int main() {
    std::printf("sizeof(weak_ptr<int>) = %zu · sizeof(shared_ptr<int>) = %zu · sizeof(unique_ptr<int>) = %zu\n",
                sizeof(std::weak_ptr<int>), sizeof(std::shared_ptr<int>), sizeof(std::unique_ptr<int>));
    std::printf("is_constructible_v<To, From>\n");
    row<std::weak_ptr<int>, const std::shared_ptr<int>&>("weak_ptr<int>    <- const shared_ptr<int>&");
    row<std::weak_ptr<int>, std::shared_ptr<int>&&>("weak_ptr<int>    <- shared_ptr<int>&&");
    row<std::weak_ptr<int>, const std::weak_ptr<int>&>("weak_ptr<int>    <- const weak_ptr<int>&");
    row<std::weak_ptr<Base>, const std::shared_ptr<Derived>&>("weak_ptr<Base>   <- const shared_ptr<Derived>&");
    row<std::weak_ptr<int>, const std::unique_ptr<int>&>("weak_ptr<int>    <- const unique_ptr<int>&");
    row<std::weak_ptr<int>, std::unique_ptr<int>&&>("weak_ptr<int>    <- unique_ptr<int>&&");
    row<std::weak_ptr<int>, int*>("weak_ptr<int>    <- int*");
    row<std::shared_ptr<int>, std::unique_ptr<int>&&>("shared_ptr<int>  <- unique_ptr<int>&&");
    row<std::shared_ptr<int>, const std::weak_ptr<int>&>("shared_ptr<int>  <- const weak_ptr<int>&");
    row<std::unique_ptr<int>, const std::shared_ptr<int>&>("unique_ptr<int>  <- const shared_ptr<int>&");
    std::printf("만들 수 있는 칸 %d / %d\n", ones, cells);

    std::weak_ptr<int> w;
    { auto s = std::make_shared<int>(7); w = s; }
    std::printf("만료된 w 에서 — w.lock() 이 비었나 %d\n", (int)(w.lock() == nullptr));
    try {
        std::shared_ptr<int> s(w);
        std::printf("만료된 w 에서 — shared_ptr<int>(w) 가 비었나 %d\n", (int)(s == nullptr));
    } catch (const std::exception& e) {
        std::printf("만료된 w 에서 — shared_ptr<int>(w) catch: %s\n", e.what());
    }
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic wptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(weak_ptr<int>) = 16 · sizeof(shared_ptr<int>) = 16 · sizeof(unique_ptr<int>) = 8
is_constructible_v<To, From>
  weak_ptr<int>    <- const shared_ptr<int>&           1
  weak_ptr<int>    <- shared_ptr<int>&&                1
  weak_ptr<int>    <- const weak_ptr<int>&             1
  weak_ptr<Base>   <- const shared_ptr<Derived>&       1
  weak_ptr<int>    <- const unique_ptr<int>&           0
  weak_ptr<int>    <- unique_ptr<int>&&                0
  weak_ptr<int>    <- int*                             0
  shared_ptr<int>  <- unique_ptr<int>&&                1
  shared_ptr<int>  <- const weak_ptr<int>&             1
  unique_ptr<int>  <- const shared_ptr<int>&           0
만들 수 있는 칸 6 / 10
만료된 w 에서 — w.lock() 이 비었나 1
만료된 w 에서 — shared_ptr<int>(w) catch: bad_weak_ptr
```

- ★★★ **`sizeof(weak_ptr<int>)` = 16** — `shared_ptr` 와 같이 **객체 포인터 + 블록 포인터** 두 칸이다(20편·27편의 16 과 같은 모양).
- ★★★ **`weak_ptr<int>` 로 만들 수 있는 칸 6 / 10** — **`shared_ptr` · `weak_ptr`(파생 → 기반 포함)에서만 1**, **`unique_ptr` · `int*` 에서는 0**.\
  ★★ **`unique_ptr` 를 약하게 보려면 `shared_ptr` 로 옮기는 길(`shared_ptr<int> <- unique_ptr<int>&&` 가 1)** 뿐이다 — 그때 **블록 할당 한 번**을 치른다(27편 (1)의 `(4)`).
- ★★★ **만료된 `w` 에서 — `lock()` 은 비어 있고, `shared_ptr<int>(w)` 는 `bad_weak_ptr` 를 던진다.** 같은 「승격」이 **조용히 비는 길과 던지는 길** 둘이다.
- ★ **clang 도 한 글자도 같다** —

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic wptr06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
sizeof(weak_ptr<int>) = 16 · sizeof(shared_ptr<int>) = 16 · sizeof(unique_ptr<int>) = 8
is_constructible_v<To, From>
  weak_ptr<int>    <- const shared_ptr<int>&           1
  weak_ptr<int>    <- shared_ptr<int>&&                1
  weak_ptr<int>    <- const weak_ptr<int>&             1
  weak_ptr<Base>   <- const shared_ptr<Derived>&       1
  weak_ptr<int>    <- const unique_ptr<int>&           0
  weak_ptr<int>    <- unique_ptr<int>&&                0
  weak_ptr<int>    <- int*                             0
  shared_ptr<int>  <- unique_ptr<int>&&                1
  shared_ptr<int>  <- const weak_ptr<int>&             1
  unique_ptr<int>  <- const shared_ptr<int>&           0
만들 수 있는 칸 6 / 10
만료된 w 에서 — w.lock() 이 비었나 1
만료된 w 에서 — shared_ptr<int>(w) catch: bad_weak_ptr
```

### (6) ★★ Rust 와 나란히 — `Rc`/`Weak` 도 같은 두 판을 낸다

**언제 쓰나** — 「Rust 는 순환을 막아 주나」를 물을 때.

```rust
// rcweak.rs
// 부모 → 자식은 Rc, 자식 → 부모는 Weak — 기본판. --cfg cycle 이면 자식 → 부모도 Rc 로 든다
use std::cell::RefCell;
use std::rc::Rc;
#[cfg(not(cycle))]
use std::rc::Weak;

struct Node {
    name: char,
    kids: RefCell<Vec<Rc<Node>>>,
    #[cfg(not(cycle))]
    parent: RefCell<Weak<Node>>,
    #[cfg(cycle)]
    parent: RefCell<Option<Rc<Node>>>,
}

impl Drop for Node {
    fn drop(&mut self) {
        println!("      drop {}", self.name);
    }
}

fn node(name: char) -> Rc<Node> {
    Rc::new(Node {
        name,
        kids: RefCell::new(vec![]),
        #[cfg(not(cycle))]
        parent: RefCell::new(Weak::new()),
        #[cfg(cycle)]
        parent: RefCell::new(None),
    })
}

fn main() {
    let x;
    {
        let r = node('r');
        x = node('x');
        r.kids.borrow_mut().push(Rc::clone(&x));
        #[cfg(not(cycle))]
        {
            *x.parent.borrow_mut() = Rc::downgrade(&r);
        }
        #[cfg(cycle)]
        {
            *x.parent.borrow_mut() = Some(Rc::clone(&r));
        }
        println!("(1) r: strong {} weak {} · x: strong {} weak {}",
                 Rc::strong_count(&r), Rc::weak_count(&r), Rc::strong_count(&x), Rc::weak_count(&x));
        println!("(2) r 이 스코프를 나간다");
    }
    #[cfg(not(cycle))]
    println!("(3) x 의 부모를 upgrade — {:?}", x.parent.borrow().upgrade().map(|p| p.name));
    #[cfg(cycle)]
    println!("(3) x 의 부모 — {:?}", x.parent.borrow().as_ref().map(|p| p.name));
    println!("(4) main 끝");
}
```

```text
===== rustc --version (exit=0) =====
rustc 1.92.0 (ded5c06cf 2025-12-08)
===== rustc --edition 2021 rcweak.rs -o rwx && ./rwx (cc exit=0 · run exit=0) =====
(1) r: strong 1 weak 1 · x: strong 2 weak 0
(2) r 이 스코프를 나간다
      drop r
(3) x 의 부모를 upgrade — None
(4) main 끝
      drop x
===== rustc --edition 2021 --cfg cycle rcweak.rs -o rwx && ./rwx (cc exit=0 · run exit=0) =====
(1) r: strong 2 weak 0 · x: strong 2 weak 0
(2) r 이 스코프를 나간다
(3) x 의 부모 — Some('r')
(4) main 끝
```

- ★★★ **기본판(자식 → 부모 `Weak`)** — `r` 의 **strong 1 · weak 1**, `r` 이 스코프를 나가자 **`drop r`**, 그 뒤 `upgrade()` 는 **`None`** — C++ 의 설계 A2 와 **같은 모양**이다(`lock()` 이 비는 것).
- ★★★ **`--cfg cycle` 판(둘 다 `Rc`)** — **strong 2 · 2** 이고 **`drop` 이 한 줄도 없다** — `main` 이 끝나도. **Rust 도 순환 누수를 컴파일에서 막지 않는다**(`cc exit=0`).\
  ★ 27편 (8)의 「스레드로 넘기면 `Rc` 는 E0277」과 대비된다 — **Rust 가 타입으로 막는 것은 스레드 안전성이지 순환이 아니다.**
- ★ Rust 쪽 정본은 Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **41번**(`Rc`/`Arc`·`Weak`와 순환) — **폴더가 없다.** 이 편이 **한 블록만** 던졌다.

## 문법 — 형태와 규칙

### 형태

```text
   std::weak_ptr<T> w = s;                  shared_ptr 에서만 (또는 다른 weak_ptr)
   if (auto p = w.lock()) { use(*p); }      ★ 확인과 사용을 한 번에
   w.expired()                              사진 한 장 — 결과를 믿고 lock 없이 쓰지 않는다
   std::shared_ptr<T> p(w);                 만료면 bad_weak_ptr 를 던진다
   std::erase_if(cache, [](auto& kv){ return kv.second.expired(); });   만료 칸 청소
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **`weak_ptr` 는 `lock()` 한 번으로 쓴다** — `expired()` 로 확인한 뒤 `lock()` 하는 두 단계에는 **틈이 열린다**((1)).
- ★★★ **약한 참조는 소유의 반대 방향** — 트리는 **부모 → 자식 소유**, **자식 → 부모 `weak_ptr`**((3)).
- ★★ **캐시·구독 목록의 만료 칸은 직접 치운다** — `make_shared` 객체면 **치우기 전까지 자리가 남는다**((4) · 27편 (6)).
- ★★ **`unique_ptr` 를 약하게 보는 길은 없다** — 필요하면 **`shared_ptr` 로 옮기거나 raw 관찰자**(목록의 **29번 주제**)((5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ | clang | 어디서 |
|---|---|---|---|
| `std::weak_ptr<int> w = unique;` | `conversion from … to non-scalar type` | `no viable conversion` | (5) 8행 |
| `*w` | `no match for 'operator*'` | `indirection requires pointer operand` | (5) 9행 |

## 어디서 틀리나

### 1. ★★★ 「`expired()` 가 거짓이면 `lock()` 은 성공한다」

(1)이 반증이다 — **2만 판 중 여러 판에서 빈 `shared_ptr` 를 쥐었다**(두 컴파일러). `expired()` 는 **그 순간의 사진**이다((2) — 원자 명령 0).

### 2. ★★★ 「TSan 이 조용하면 스레드 문제가 없다」

(1)이 반증이다 — **두 컴파일러의 TSan 이 침묵했는데 틈은 열렸다.** 원자 연산 둘 사이의 틈은 **데이터 경쟁이 아니다.**

### 3. ★★★ 「순환만 끊으면 어느 쪽을 약하게 해도 같다」

(3)이 반증이다 — **설계 B 는 누수 0 인데 자식이 전부 죽는다.** 약하게 할 방향은 **소유의 반대**다.

### 4. ★★ 「`weak_ptr` 캐시는 알아서 비워진다」

(4)가 반증이다 — **만료된 칸이 캐시에 그대로 남는다**(크기 3 · 만료 2). 그리고 `make_shared` 객체면 **자리까지 붙든다**(27편 (6)).

### 5. ★★ 「`unique_ptr` 도 `weak_ptr` 로 관찰할 수 있다」

(5)가 반증이다 — **에러**다. `is_constructible` 도 **0**. 제어 블록이 없기 때문이다.

### 6. ★★ 「Rust 는 순환 누수를 막는다」

(6)이 반증이다 — **`Rc` 둘이 서로를 들면 `drop` 이 한 줄도 없다**(`cc exit=0`).

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 급소는 「표준」 칸과 「구현」 칸의 경계다** — **`lock()` 이 원자적**이라는 것은 약속이고, **그것이 `cmpxchg` 루프**라는 것은 이 구현의 모양이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **`lock()` 은 원자적으로 「살아 있으면 공유, 아니면 빈 것」**((1)(2)) · **`weak_ptr` 는 `shared_ptr`/`weak_ptr` 에서만 만든다**((5)) · **만료된 `weak_ptr` 로 만든 `shared_ptr` 는 `bad_weak_ptr`**((5)) · **마지막 강한 참조에서 파괴**((3)(4)) | 두 단계/한 단계 판정 · 에러 전문 · `is_constructible` · 소멸자 로그 | ★★★ **TOCTOU — TSan 도 경고도 침묵**((1)) |
| **조건부 표준** | 특정 판에서만 | ★ **`std::erase_if` 는 C++20**((4)) — 이 문서는 판을 바꿔 던지지 않았다 | — | — |
| **구현 정의** | 문서화 의무 | ★★★ **`lock()` 이 `lock cmpxchg` 루프가 되는 것 · `expired()` 가 평범한 읽기 한 번인 것**((2)) · **`sizeof(weak_ptr)` 16**((5)) | `-O2 -S` · `sizeof` | ★ 명령 모양은 **x86-64 · libstdc++ 13** 의 것 |
| **미명시** | 몇 가지 중 하나 | ★★ **두 스레드 중 누가 먼저 가나** — 틈이 **몇 번** 열리나((1)) | N판 판정 | ★★ **「몇 번」 위에 결론을 세우지 않는다** |
| **UB** | 아무 일이나 | ★ **이 주제의 코드는 UB 가 없다** — 빈 `shared_ptr` 를 **역참조하면** UB 지만 이 문서는 **확인하고 세기만** 했다 | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | TSan · ASan |
|---|---|---|---|---|
| ★★★ **`expired()` → `lock()` 의 틈** | 표준(허용된 코드) | ★★★ **0건** | ★★★ **0건** | ★★★ **TSan 두 컴파일러 침묵 · `run exit=0`** |
| ★★★ **설계 B — 자식이 아무에게도 소유되지 않음** | 표준(허용된 코드) | **0건** | **0건** | ★★ **ASan 누수 0** — 「샜나」만 묻는 도구라 **「사라졌나」는 못 본다** |
| ★★ **캐시의 만료 칸이 쌓임** | 표준(허용된 코드) | **0건** | **0건** | ★ **누수가 아니다**(결국 풀린다) — 크기를 세야 보인다 |
| ★★ **`unique_ptr` → `weak_ptr`** | ill-formed | ★★★ **에러** | ★★★ **에러** | — |

- ★★★ **이 표의 결론** — **`weak_ptr` 의 사고는 전부 「규칙대로 된 코드」에서 난다.** 컴파일러는 0건이고, **TSan 은 논리의 틈을, ASan 은 설계의 방향을 못 본다.** **판정 격자와 로그가 이 주제의 도구**다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 이 편의 에러 줄((5))은 **두 컴파일러 다 `cc exit=1`** 이었다. 나머지는 전부 **올바른 C++** 이다 — 조용히 통과한 ill-formed 는 **없었다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 다른 스레드가 놓을 수 있는 객체를 쓴다 | ★★★ **`if (auto p = w.lock())`** | 확인과 사용이 한 번((1)(2)) |
| 트리 · 부모 포인터 | ★★★ **부모 → 자식 `shared_ptr`(또는 `unique_ptr`), 자식 → 부모 `weak_ptr`** | (3) — `unique_ptr` 판은 목록의 **29번 주제** |
| 쓰는 사람이 있을 때만 들고 싶은 캐시 | ★★ **`map<key, weak_ptr>` + 주기적 `erase_if`** | (4) |
| 이벤트 구독자 | ★★ **`vector<weak_ptr>` + 알릴 때 치우기** | (4) |
| 소유자가 하나(`unique_ptr`) · 관찰만 | ★★ **raw 포인터·참조**(수명을 구조가 보장할 때) | (5) — 목록의 **29번 주제** |
| 만료를 예외로 알리고 싶다 | ★ **`shared_ptr<T>(w)`** | `bad_weak_ptr`((5)) |

## 핵심 문장

- ★★★ **`expired()` 로 확인한 뒤 `lock()` 하면 틈이 열린다** — 두 컴파일러 다 2만 판 중 **빈 `shared_ptr` 를 쥔 판이 있었다.** `lock()` 한 번이면 **값이 틀린 판이 없다.**
- ★★★ **`expired()` 는 `lock` 접두 0, `lock()` 은 `lock cmpxchg` 1 + 재시도 루프** — 원자성은 **한 명령 안에서 「0 이 아닌가」와 「+1」을 묶는 것**이다.
- ★★★ **TSan 은 그 틈에 침묵한다** — 데이터 경쟁이 아니라 **논리의 틈**이기 때문이다.
- ★★★ **약한 참조는 소유의 반대 방향** — 자식 → 부모를 `shared_ptr` 로 두면 **누수는 0 인데 자식이 전부 죽는다.**
- ★★ **`weak_ptr` 는 `shared_ptr`/`weak_ptr` 에서만 만든다(6 / 10)** — `unique_ptr` 에는 **제어 블록이 없어서** 에러다. 크기는 **16**.
- ★★ **Rust 의 `Rc` 둘도 순환이면 `drop` 이 한 줄도 없다** — 타입이 막는 것은 **스레드**지 **순환**이 아니다.

## 관련 자료

- [27번](../27-shared-ptr-and-reference-counting/) — ★★★ **이 편의 앞 절반.** 순환 누수(`Indirect leak` 2) · `weak_ptr` 로 0 · clang + ASan 의 판별 흔들림 · `make_shared` 의 늦은 해제 · `lock` 접두 4.
- [26번](../26-unique-ptr-and-ownership-transfer/) — `unique_ptr` 에 블록이 없다는 것(크기 8)이 (5)의 에러의 뿌리다.
- 목록의 **29번 주제** — **raw 포인터가 관찰자로 남는 자리.** `unique_ptr` 가 소유한 트리의 부모 포인터가 거기 있다.
- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절의 **「`shared_ptr` 순환 참조는 해제되지 않는다」** 가 **논증의 정본**이다. 여기는 **그것을 끊는 방향과 `lock()` 의 원자성**을 잰 쪽이다.
- [`memory-management/`](../../../../memory-management/) — 참조 계수·추적 GC 일반론.
- Rust 갈래 목록([`rust/syntax/README.md`](../../../rust/syntax/README.md))의 **41번**(`Rc`/`Arc`·`Weak`와 순환) — **폴더가 없다.** (6)이 한 블록을 던졌다.

## 용어 풀이

> **`weak_ptr`** — 제어 블록을 가리키지만 **강한 계수를 안 올리는** 스마트 포인터. 객체를 살려 두지 못하고 **`lock()` 으로만** 쓴다.\
> 예: (5)의 `sizeof` 16 · `is_constructible` 6 / 10.

> **`lock()`** — 강한 계수가 0 이 아니면 **원자적으로 +1 해** `shared_ptr` 를 돌려주고, 0 이면 **빈 `shared_ptr`** 를 돌려준다.\
> 예: (2)의 `lock cmpxchgl` 루프.

> **`expired()`** — 강한 계수가 0 인지 **한 번 읽어** 답한다. 읽은 뒤의 변화는 모른다.\
> 예: (2)의 `movl 8(%rdx), %eax` · (1)의 두 단계 판.

> **TOCTOU(time of check to time of use)** — **검사한 시점과 사용하는 시점 사이**에 상태가 바뀌어 검사 결과가 거짓이 되는 것.\
> 예: (1)의 「살아 있다고 답했는데 빈 `shared_ptr`」.

> **`cmpxchg`(compare-and-exchange, x86)** — 「메모리가 기대값과 같으면 새 값을 쓰고, 아니면 현재 값을 돌려준다」를 한 명령으로 하는 것. `lock` 접두와 함께 **원자적**이다.\
> 예: (2)의 재시도 루프.

> **TSan(ThreadSanitizer)** — 동기화 없는 동시 접근(**데이터 경쟁**)을 실행 중에 찾는 도구.\
> 예: (1)에서 틈에 **침묵**한 것.

> **`bad_weak_ptr`** — 만료된 `weak_ptr` 로 `shared_ptr` 를 **생성자로** 만들 때 던지는 예외.\
> 예: (5)의 `shared_ptr<int>(w)`.

## 더 들어가면

- **`std::atomic<std::weak_ptr<T>>`(C++20)** — `weak_ptr` **객체 자체**를 여러 스레드가 바꿀 때. (1)의 틈과는 **다른 문제**다. 이 문서는 던지지 않았다.
- **`owner_before`·`owner_less`** — `weak_ptr` 를 **`map` 의 키**로 쓸 때의 비교. 만료돼도 순서가 안 바뀐다. 이 문서는 던지지 않았다.
- **`enable_shared_from_this` 와 `weak_from_this`** — 27편 (4)가 `bad_weak_ptr` 와 `expired=1` 을 쟀다.
- **캐시 청소의 시점** — 매 조회마다 · 주기적으로 · 크기가 넘칠 때. 이 문서는 **청소하지 않으면 쌓인다**까지만 보였다.
