# cpp/syntax/21 — 추상 클래스·순수 가상·vtable 비용 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 추상 클래스](https://en.cppreference.com/w/cpp/language/abstract_class) · [cppreference — 가상 함수](https://en.cppreference.com/w/cpp/language/virtual) · [Itanium C++ ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html) · [GCC 13 Optimize Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html)\
> ★ cppreference 「추상 클래스」는 2026-09-26 에 열어 **세 문장을 확인했다** — 「순수 가상 함수에도 정의를 줄 수 있고 **클래스 밖에서** 준다」·\
> 「**생성자·소멸자에서 순수 가상을 가상 호출하면 UB**(정의가 있든 없든)」·「순수 가상 소멸자는 정의가 반드시 필요하다」.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **javac 21.0.5** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`abs01.cpp` \~ `abs07.cpp` · `devirt.cpp` · `devirt-grid.sh` · `Abs.java`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 소스 펜스의 배너도 **캡처가 찍은 것**이다. 원고에 손으로 쓴 배너는 없다.
> ★★★ **`terminate` 로 끝나는 블록((3))은 마커를 `stderr` 로 찍었다.** `abort()` 로 죽으면 **버퍼에 남은 표준 출력이 통째로 사라지기 때문**이다.
> **버전** — 순수 가상·추상 클래스는 **C++98부터**. `override`·`final` 은 **C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 수치는 실행으로 접지했다.
> ★★★ **이 편은 「비용」을 시간이 아니라 명령으로 센다.** 벤치마크는 **하나도 없다.**\
> 센 것은 **간접 `call`/`jmp` 가 있나 · 함수를 이름으로 부르나 · `call` 자체가 사라졌나** 셋이다.\
> ★★★ **그래서 이 문서는 「가상 호출이 느리다」고 쓰지 않는다** — 잰 것은 「**간접 호출이 되고, 인라인이 막힌다**」까지다.\
> 그것이 몇 나노초인지·분기 예측이 어떤지·캐시가 어떤지는 **이 문서가 재지 않았다.**
> **경계** — 「가상 디스패치 규칙·vtable 의 배치」는 [19번](../19-inheritance-virtual-functions-override-final/)이 정본이다 — 19편 (11)이 vtable 을 두 도구로 찍었고,\
> 「**가상 호출 비용은 21번이 정본**」으로 넘긴 창을 **여기서 이어받는다.** 「추상 클래스의 개념」은 [`oop-basics/`](../../../../oop-basics/) §17 이 정본이다.\
> 「순수 가상 **소멸자**」는 [20번](../20-virtual-destructors-and-polymorphic-deletion/) (8)이 정본이다.
> **대비** — ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **16번**([`16-inheritance-virtual-override-abstract-sealed-new/`](../../../csharp/syntax/16-inheritance-virtual-override-abstract-sealed-new/)) —\
> **`callvirt` 가 비가상에도 나오고(널 검사) `sealed` 여도 IL 은 `callvirt` 이며 디버추얼라이제이션은 JIT 몫**이라는 실측을 (7)에서 인용한다.\
> Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) — (7)에서 `javap -c` 로 한 번 던진다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | **g++ 클래스 덤프의 주소**(`(0x0x…)`) | ★★★ **어셈블리의 `call *…`/`jmp *…` 유무 · 부르는 심볼 이름 · `call` 이 사라졌나** — 이 주제의 답 자체다 |
> | 두 컴파일러의 **진단 문구** | ★★★ **디버추얼라이제이션 격자의 칸**(간접 · 직접 · 인라인) |
> | 지역 레이블 이름(`.L8` · `.LBB0_3`) | ★★ **`sizeof`** · **vtable 항목 수와 그 자리의 이름** · **레이아웃의 오프셋** |
> | ★★★ **실행 시간 — 아예 재지 않았다** | ★★ **`cc exit`/`run exit`** · **경고·에러 개수** · **javap 의 명령 이름** |

## 한눈에 — 쉽게 말하면

**가상 호출은 「대표번호로 거는 전화」다.**

회사에 전화할 때 **대표번호**로 걸면 교환대가 「지금 이 부서를 누가 맡고 있나」를 **보고 나서** 연결해 준다.\
**내선번호**를 알면 **바로** 그 자리로 간다. 그리고 **답을 이미 알면 전화를 안 건다.**

- **대표번호** — `b.f()` 를 **기반 참조로** 부른다 → 객체 안의 표(vtable)를 **읽고 나서** 건다 = **간접 호출**(`call *…`).
- **내선번호** — 누가 받을지 **컴파일러가 이미 안다** → **직접 호출**(`call _ZNK2Df1fEv`).
- **안 건다** — 받을 사람의 답까지 안다 → **인라인**. `call` 이 **사라지고** `movl $1, %eax` 만 남는다.
- ★★★ **「교환대가 느리다」는 이 비유가 말하는 것이 아니다** — 말하는 것은 「**교환대를 거치면 내가 답을 미리 알 수 없다**」다.\
  그것이 **인라인이 막힌다**는 뜻이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 대표번호 | ★★★ **간접 호출** — vtable 을 읽고 `call *` | (4) |
| 내선번호 | ★★ **직접 호출** — 심볼 이름으로 `call` | (4) |
| 안 건다 | ★★★ **인라인** — `call` 이 사라진다 | (4) |
| 교환대의 부서표 | ★★ **vtable**(표준에는 없는 말) | (6) |
| 「이 부서는 더 안 쪼갭니다」 | ★★ **`final`** — 컴파일러가 내선번호를 알게 된다 | (4) |
| 「아마 그 사람이겠지」 하고 먼저 확인 | ★★ **추측 디버추얼라이제이션**(g++) | (4) |
| 빈 자리가 남은 부서표 | ★★★ **추상 클래스** — 객체를 못 만든다 | (1) |

> **간접 호출(indirect call)** — 부를 주소를 **메모리에서 읽어 와서** 부르는 것. x86-64 어셈블리에서 `call *…`·`jmp *…`.\
> 예: (4)의 `t1_base_ref` 가 g++ `-O2` 에서도 `jmp *(%rax)` 였다.

> **디버추얼라이제이션(devirtualization)** — 가상 호출을 **컴파일러가 직접 호출로 바꾸는 것**. 받을 함수를 **증명할 수 있을 때만** 한다.\
> 예: (4)의 `t3_final_class` 가 `-O0` 에서도 `call _ZNK2Df1fEv` 였다.

```text
   b.f()   (b 는 const B&)

   간접     movq (%rdi),%rax   ->  jmp *(%rax)            vtable 을 읽고 건다     ★ 무엇이 불릴지 컴파일 시간에 모른다
   직접     call _ZNK2Df1fEv                              이름으로 건다            ★ 누가 받는지는 안다
   인라인   movl $1, %eax  ; ret                          안 건다                  ★ 답까지 안다
```

- ★★★ **이 셋이 이 편의 「비용」의 전부다.** 시간은 안 쟀다 — **명령이 어떻게 바뀌나**를 센다.

## 이 주제가 답하려는 질문

1. **추상 클래스는 무엇을 막고, 순수 가상은 정확히 무엇을 뜻하나** — 본체가 있어도 되나((1)(2)).
2. **생성자에서 순수 가상을 부르면 무엇이 일어나나** — 19편의 「생성자 속 가상 호출은 기반 것」의 극단((3)).
3. ★★★ **가상 호출은 무엇으로 바뀌고, 언제 컴파일러가 그것을 직접 호출로 되돌리나** — 명령으로 센다((4)).
4. **인터페이스 둘을 물려받으면 객체에 무엇이 붙나**((6)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ④ `-O2` 어셈블리다

★★★ **이 주제의 본체는 ④ 어셈블리다** — **디버추얼라이제이션 격자**(탐침 여덟 × g++·clang × `-O0`·`-O2`)가 중심이다.\
★ [19번](../19-inheritance-virtual-functions-override-final/)이 「**부적용인 창**」으로 남긴 자리를 **여기서 연다**(부적용인 창 릴레이).

```text
① 호출 로그             순수 가상의 본체 · 생성자 속 순수 가상            (2)(3)
② 두 컴파일러 대조       추상 클래스 인스턴스화 · 한 줄 본체의 진단 전문   (1)(2)
③ ASan                   —                                                  부적용
④ ★ 어셈블리(-O0/-O2)    간접 · 직접 · 인라인을 함수마다 센다              (4)
⑤ 경고 격자              생성자 속 순수 가상 — 직접 대 한 다리             (3)
⑥ 레이아웃·vtable 덤프   인터페이스 둘 = vptr 둘 · thunk                    (6)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 호출 로그 | 순수 가상의 본체를 이름으로 부르기 · `pure virtual method called` | **쓴다** |
| ② 두 컴파일러 대조 | 추상 클래스 진단이 **남은 순수 가상의 이름을 나열하나** | **쓴다** |
| ③ ASan | ★ **부적용** — 이 주제의 실패는 **메모리 오류가 아니라 `terminate`** 다. 잴 것이 없다 | **안 쓴다** |
| ★★★ **④ 어셈블리** | ★★★ **본체** — `devirt-grid.sh` 가 **32칸**을 센다 | **쓴다** |
| ⑤ 경고 격자 | 직접 부르면 **양쪽 1건**, 한 다리 거치면 **양쪽 0건** | **쓴다** |
| ⑥ 레이아웃·덤프 | clang `-fdump-record-layouts` · g++ `-fdump-lang-class` | **쓴다** |
| ★★ **실행 시간** | ★★★ **안 쟀다** — 「부적용」이 아니라 「**이 문서가 하지 않은 측정**」이다 | **안 쓴다** |

- ★★★ **실행 시간을 「부적용」으로 두지 않은 이유** — 가상 호출에는 **분명히 잴 수 있는 시간 비용이 있을 수 있다.**\
  잴 것이 없는 게 아니라 **재려면 벤치마크 하네스·반복·잡음 측정이 필요하고, 이 문서는 그것을 안 만들었다.**\
  ★ 그래서 **「못 잰 것」도 「부적용」도 아니고 「안 잰 것」이며**, 그 자리에서 **아무 결론도 내지 않는다.**
- ★★ **③ ASan 은 부적용이다** — 생성자 속 순수 가상은 **런타임이 `__cxa_pure_virtual` 로 잡아 `terminate`** 한다. 메모리를 틀리게 쓰지 않는다.
- ★ 「없다고 적기 전에 버전 호출을 블록으로 남긴다」(규칙 26) — (4)의 첫 블록 · (7)의 `javac` 블록이 그것이다.

### (1) ★★ 추상 클래스를 만들면 — 남은 순수 가상의 이름을 나열하나

**언제 쓰나** — 인터페이스를 구현하다가 「**왜 객체를 못 만들지?**」가 떴을 때. 19편 (6)은 **순수 가상 하나**였고, 여기는 **셋 중 하나만 덮은** 경우다.

```cpp
/* abs01.cpp */
// 순수 가상이 셋인 인터페이스 — 하나만 덮은 파생을 만들면 컴파일러가 남은 이름을 나열하나
struct Codec {
    virtual int  encode(int) const = 0;
    virtual int  decode(int) const = 0;
    virtual const char* name() const = 0;
    virtual ~Codec() = default;
};
struct Half : Codec {
    int encode(int x) const override { return x + 1; }        // 셋 중 하나만 덮었다
};

int main() {
    Codec c;                             // 1. 인터페이스 자체를 만든다
    Half h;                              // 2. 하나만 덮은 파생을 만든다
    Codec* p = new Half;                 // 3. new 로 만든다
    (void)c; (void)h; (void)p;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 abs01.cpp -o ex (cc exit=1) =====
abs01.cpp: In function ‘int main()’:
abs01.cpp:13:11: error: cannot declare variable ‘c’ to be of abstract type ‘Codec’
   13 |     Codec c;                             // 1. 인터페이스 자체를 만든다
      |           ^
abs01.cpp:2:8: note:   because the following virtual functions are pure within ‘Codec’:
    2 | struct Codec {
      |        ^~~~~
abs01.cpp:3:18: note:     ‘virtual int Codec::encode(int) const’
    3 |     virtual int  encode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:4:18: note:     ‘virtual int Codec::decode(int) const’
    4 |     virtual int  decode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:5:25: note:     ‘virtual const char* Codec::name() const’
    5 |     virtual const char* name() const = 0;
      |                         ^~~~
abs01.cpp:14:10: error: cannot declare variable ‘h’ to be of abstract type ‘Half’
   14 |     Half h;                              // 2. 하나만 덮은 파생을 만든다
      |          ^
abs01.cpp:8:8: note:   because the following virtual functions are pure within ‘Half’:
    8 | struct Half : Codec {
      |        ^~~~
abs01.cpp:4:18: note:     ‘virtual int Codec::decode(int) const’
    4 |     virtual int  decode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:5:25: note:     ‘virtual const char* Codec::name() const’
    5 |     virtual const char* name() const = 0;
      |                         ^~~~
abs01.cpp:15:20: error: invalid new-expression of abstract class type ‘Half’
   15 |     Codec* p = new Half;                 // 3. new 로 만든다
      |                    ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 abs01.cpp -o ex (cc exit=1) =====
abs01.cpp:13:11: error: variable type 'Codec' is an abstract class
   13 |     Codec c;                             // 1. 인터페이스 자체를 만든다
      |           ^
abs01.cpp:3:18: note: unimplemented pure virtual method 'encode' in 'Codec'
    3 |     virtual int  encode(int) const = 0;
      |                  ^
abs01.cpp:4:18: note: unimplemented pure virtual method 'decode' in 'Codec'
    4 |     virtual int  decode(int) const = 0;
      |                  ^
abs01.cpp:5:25: note: unimplemented pure virtual method 'name' in 'Codec'
    5 |     virtual const char* name() const = 0;
      |                         ^
abs01.cpp:14:10: error: variable type 'Half' is an abstract class
   14 |     Half h;                              // 2. 하나만 덮은 파생을 만든다
      |          ^
abs01.cpp:4:18: note: unimplemented pure virtual method 'decode' in 'Half'
    4 |     virtual int  decode(int) const = 0;
      |                  ^
abs01.cpp:5:25: note: unimplemented pure virtual method 'name' in 'Half'
    5 |     virtual const char* name() const = 0;
      |                         ^
abs01.cpp:15:20: error: allocating an object of abstract class type 'Half'
   15 |     Codec* p = new Half;                 // 3. new 로 만든다
      |                    ^
3 errors generated.
```

- ★★★ **두 컴파일러 다 남은 이름을 나열한다** — `Codec` 에는 **셋**, `Half` 에는 **덮지 않은 둘**(`decode`·`name`).\
  ★ `encode` 는 `Half` 의 목록에서 **빠진다** — 덮었기 때문이다. **목록이 곧 「고칠 것」의 목록**이다.
- ★★ **나열 방식이 다르다** — g++ 는 `because the following virtual functions are pure within 'Half':` 아래에 **시그니처 전체**를,\
  clang 은 **이름마다 `unimplemented pure virtual method 'decode' in 'Half'`** 한 줄씩 낸다.
- ★★ **3번(`new Half`)에는 목록이 다시 안 나온다** — 두 컴파일러 다 **같은 타입의 목록은 한 번만** 보였다(관찰).
- ★★ **에러 3건 · `cc exit=1`** — 두 컴파일러 같다.

```text
   Codec  { encode = 0 · decode = 0 · name = 0 }        남은 순수 가상 3  -> 추상
     └ Half { encode 를 덮었다 }                        남은 순수 가상 2  -> ★ 여전히 추상
          └ (decode · name 까지 덮은 파생)               남은 순수 가상 0  -> 객체를 만들 수 있다

   ★ 「추상인가」는 상속 사슬에서 「남은 칸이 0 인가」로 판정한다 — 진단이 그 남은 칸을 나열한다
```

### (2) ★★ 순수 가상에도 본체를 줄 수 있다 — 누가 부르나

**언제 쓰나** — 「파생은 반드시 덮되, **공통 기본 동작**은 기반에 두고 싶다」 때.

```cpp
/* abs02.cpp */
// 순수 가상에 본체를 준다 — 그래도 추상인가, 그 본체는 누가 부르나
#include <cstdio>
#include <type_traits>

struct Logger {
    virtual void log(const char* m) const = 0;       // 순수 가상 — 파생이 반드시 덮는다
    virtual ~Logger() = default;
};
void Logger::log(const char* m) const {              // ★ 그런데 본체가 있다(클래스 밖에서 정의)
    std::printf("      Logger::log  [기본 형식] %s\n", m);
}

struct Stamp : Logger {
    void log(const char* m) const override {
        std::printf("      Stamp::log   앞에 도장을 찍고 ->\n");
        Logger::log(m);                              // ★ 기반의 본체를 이름으로 부른다
    }
};

int main() {
    std::printf("(1) is_abstract<Logger> = %d · is_abstract<Stamp> = %d\n",
                (int)std::is_abstract_v<Logger>, (int)std::is_abstract_v<Stamp>);
    Stamp s;
    const Logger& r = s;
    std::printf("(2) r.log(\"hi\") — 가상 호출\n");
    r.log("hi");
    std::printf("(3) r.Logger::log(\"hi\") — 이름으로 부르면 가상 디스패치가 꺼진다\n");
    r.Logger::log("hi");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) is_abstract<Logger> = 1 · is_abstract<Stamp> = 0
(2) r.log("hi") — 가상 호출
      Stamp::log   앞에 도장을 찍고 ->
      Logger::log  [기본 형식] hi
(3) r.Logger::log("hi") — 이름으로 부르면 가상 디스패치가 꺼진다
      Logger::log  [기본 형식] hi
```

- ★★★ **`is_abstract<Logger>` 가 1** 이다 — **본체가 있어도 추상**이다. 순수 가상이 뜻하는 것은 「본체가 없다」가 아니라 「**파생이 반드시 덮어야 한다**」다.
- ★★★ **본체는 이름으로만 불린다** — `Stamp::log` 안의 `Logger::log(m)`, 그리고 바깥의 `r.Logger::log("hi")`.\
  ★ **이름으로 부르면 가상 디스패치가 꺼진다** — `(3)` 에서 `Stamp::log` 가 **안 불렸다.**

```text
   Logger::log  = 0   + 클래스 밖 본체         ★ 「덮어라」 약속 + 기본 동작

   r.log("hi")           가상 호출   ->  Stamp::log  ->  (안에서) Logger::log   두 줄
   r.Logger::log("hi")   이름 호출   ->  Logger::log                             한 줄  ★ 디스패치가 꺼진다
```
- ★★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic abs02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) is_abstract<Logger> = 1 · is_abstract<Stamp> = 0
(2) r.log("hi") — 가상 호출
      Stamp::log   앞에 도장을 찍고 ->
      Logger::log  [기본 형식] hi
(3) r.Logger::log("hi") — 이름으로 부르면 가상 디스패치가 꺼진다
      Logger::log  [기본 형식] hi
```

★★ **본체를 클래스 안에 한 줄로 쓰면 안 된다** — 기준 소스가 「**클래스 밖에서** 준다」고 적은 이유다.

```cpp
/* abs06.cpp */
// 순수 가상 함수의 본체를 클래스 안에 한 줄로 — virtual void f() = 0 {} 는 되나
struct Base {
    virtual void f() = 0 { }             // 순수 지정 + 본체
    virtual ~Base() = default;
};
int main() { }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 abs06.cpp -o ex (cc exit=1) =====
abs06.cpp:3:22: error: pure-specifier on function-definition
    3 |     virtual void f() = 0 { }             // 순수 지정 + 본체
      |                      ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 abs06.cpp -o ex (cc exit=1) =====
abs06.cpp:3:18: error: initializer on function does not look like a pure-specifier
    3 |     virtual void f() = 0 { }             // 순수 지정 + 본체
      |                  ^     ~
abs06.cpp:3:25: error: expected ';' at end of declaration list
    3 |     virtual void f() = 0 { }             // 순수 지정 + 본체
      |                         ^
      |                         ;
2 errors generated.
```

- ★★ **양쪽 `cc exit=1`** — g++ `pure-specifier on function-definition` · clang `initializer on function does not look like a pure-specifier`.
- ★ 문법이 「`= 0`」과 「본체」를 **한 선언에 같이 못 두게** 되어 있다. 그래서 (2)의 `abs02.cpp` 는 **클래스 밖**에서 정의했다.

### (3) ★★★ 생성자 안에서 순수 가상을 부르면 — 19편의 극단

**언제 쓰나** — 기반 생성자에서 「초기화 훅」을 부르고 싶어질 때.

★★★ **[19번](../19-inheritance-virtual-functions-override-final/) (9)가 실측한 것** — 생성자 안의 가상 호출은 **기반 것**이 불리고, **`D::speak` 는 한 번도 안 불렸다.**\
**그 「기반 것」이 순수 가상이면 무엇이 불리나** — 이것이 여기서 묻는 것이다. 두 가지로 부른다 — **직접** · **비가상 함수를 한 번 거쳐서**.

```cpp
/* abs03.cpp */
// 생성자 안에서 순수 가상을 「직접」 부른다 — 19편의 「생성자 속 가상 호출은 기반 것」의 극단
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
    virtual void init() = 0;                          // 순수 가상 — 본체가 없다
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() { Derived d; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o && g++ abs03.o -o ex (cc exit=1) =====
abs03.cpp: In constructor ‘Base::Base()’:
abs03.cpp:5:83: warning: pure virtual ‘virtual void Base::init()’ called from constructor
    5 |     Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
      |                                                                               ~~~~^~
/usr/bin/ld: abs03.o: in function `Base::Base()':
abs03.cpp:(.text._ZN4BaseC2Ev[_ZN4BaseC5Ev]+0x49): undefined reference to `Base::init()'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o && clang++ abs03.o -o ex && ./ex (cc exit=0 · run exit=134) =====
abs03.cpp:5:86: warning: call to pure virtual member function 'init' has undefined behavior; overrides of 'init' in subclasses are not available in the constructor of 'Base' [-Wcall-to-pure-virtual-from-ctor-dtor]
    5 |     Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
      |                                                                               ^
abs03.cpp:6:5: note: 'init' declared here
    6 |     virtual void init() = 0;                          // 순수 가상 — 본체가 없다
      |     ^
1 warning generated.
      Base() 가 init() 을 직접 부른다
pure virtual method called
terminate called without an active exception
```

- ★★★ **같은 소스에서 두 컴파일러가 갈렸다.**\
  **g++ 는 경고 1건 + 링크 에러**(`undefined reference to 'Base::init()'`)다 — 생성자 안의 `init()` 을 **`Base::init` 으로 직접 부르는 코드**로 만들었고, 그 본체가 **없다.**\
  **clang 은 경고 1건 + 링크 성공 + `run exit=134`** 다 — **vtable 을 거쳐 부르는 코드**로 만들었고, 그 칸의 `__cxa_pure_virtual` 이 **`pure virtual method called`** 를 찍고 죽였다.
- ★★ **두 선택 다 표준과 모순되지 않는다** — 생성자에서 순수 가상을 가상 호출하는 것은 **UB** 다(기준 소스). **결과가 무엇이든 표준 위반이 아니다.**
- ★★ **경고 문구가 이유를 말해 준다** — clang `overrides of 'init' in subclasses are not available in the constructor of 'Base'`.

```cpp
/* abs04.cpp */
// 생성자 안에서 순수 가상을 「비가상 함수를 한 번 거쳐」 부른다
// 마커는 표준 오류로 찍는다 — terminate 로 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 setup() 을 부른다\n"); setup(); }
    void setup() { std::fprintf(stderr, "      setup() 이 init() 을 부른다\n"); init(); }  // 비가상 중간 다리
    virtual void init() = 0;
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() {
    std::fprintf(stderr, "(1) Derived 를 만든다\n");
    Derived d;
    std::fprintf(stderr, "(2) 여기까지 왔다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs04.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
(1) Derived 를 만든다
      Base() 가 setup() 을 부른다
      setup() 이 init() 을 부른다
pure virtual method called
terminate called without an active exception
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic abs04.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
(1) Derived 를 만든다
      Base() 가 setup() 을 부른다
      setup() 이 init() 을 부른다
pure virtual method called
terminate called without an active exception
```

```text
===== echo "abs03(직접)   g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o 2>&1 | grep -c 'warning:') · clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o 2>&1 | grep -c 'warning:')" (exit=0) =====
abs03(직접)   g++ 경고 1 · clang 경고 1
===== echo "abs04(한 다리) g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c abs04.cpp -o abs04.o 2>&1 | grep -c 'warning:') · clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c abs04.cpp -o abs04.o 2>&1 | grep -c 'warning:')" (exit=0) =====
abs04(한 다리) g++ 경고 0 · clang 경고 0
```

```text
   Derived d;  를 만들 때 — 객체는 아직 Base 다 (19편 (9))

   직접      Base() { init(); }                      g++   : Base::init 으로 직접  -> 본체 없음 -> 링크 에러
                                                     clang : vtable 칸으로           -> __cxa_pure_virtual -> 134
   한 다리   Base() { setup(); }  setup() { init(); }  둘 다 : vtable 칸으로           -> __cxa_pure_virtual -> 134

   경고      직접 1 · 1        한 다리 0 · 0      ★ 한 다리만 거쳐도 두 컴파일러가 다 조용하다
```

- ★★★ **한 다리를 거치면 경고가 0건**이고 **두 컴파일러 다 `run exit=134`** 다.\
  ★ `setup()` 은 **비가상**이라 컴파일러가 「생성자 안이다」를 모르고, `init()` 을 **평범한 가상 호출**로 만든다.\
  ★★ 그 순간 vtable 은 **`Base` 의 것**이고(19편 (9)) 그 칸에는 **`__cxa_pure_virtual`** 이 들어 있다.
- ★★★ **`Derived::init` 은 두 판 다 한 번도 안 불렸다** — 19편의 「동작이 조용히 사라진다」가 여기서는 「**프로그램이 죽는다**」가 됐다.
- ★★ **메시지를 찍는 것은 컴파일러가 아니라 런타임 라이브러리**다 — 두 컴파일러 다 **libstdc++(libsupc++)** 를 쓰므로 문구가 같다.\
  ★ `terminate called without an active exception` 은 **예외가 없는데 `std::terminate` 가 불렸다**는 뜻이다.
- ★★ **마커를 `stderr` 로 찍은 이유가 여기서 보인다** — `abort` 로 죽으면 stdout 버퍼가 사라진다(19-A).

### (4) ★★★ 디버추얼라이제이션 격자 — 같은 `f()` 를 여덟 자리에서 부른다

**언제 쓰나** — 「가상 호출이 비싸다던데 `final` 을 붙이면 뭐가 달라지나?」를 **명령으로** 확인할 때. **이 절이 이 주제의 본체다.**

★ **「도구가 없다」고 적기 전에 버전 호출을 블록으로 남긴다**(규칙 26).

```text
===== g++ --version | head -1 (exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
===== clang++ --version | head -1 (exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
===== which g++ clang++ (exit=0) =====
/usr/bin/g++
/usr/bin/clang++
```

```cpp
/* devirt.cpp */
// 디버추얼라이제이션 탐침 — 같은 f() 를 여덟 가지 자리에서 부른다. 함수마다 어셈블리를 센다
struct B            { virtual int f() const; virtual ~B() = default; };
struct Dn : B       { int f() const override { return 3; } };        // 아무것도 안 붙였다
struct Df final : B { int f() const override { return 1; } };        // 클래스에 final
struct Dm : B       { int f() const final    { return 2; } };        // 함수에 final
struct N            { int g() const { return 4; } };                 // 가상이 아니다

extern "C" {
int t1_base_ref(const B& b)        { return b.f(); }   // 1. 기반 참조로 부른다
int t2_derived_ref(const Dn& d)    { return d.f(); }   // 2. 파생 참조 — 그 밑에 또 파생이 있을 수 있다
int t3_final_class(const Df& d)    { return d.f(); }   // 3. 정적 타입이 final 클래스
int t4_final_func(const Dm& d)     { return d.f(); }   // 4. 정적 타입의 f 가 final
int t5_local_object()              { Dn d; return d.f(); }          // 5. 지역 객체 — 동적 타입이 보인다
int t6_new_then_call()             { B* p = new Dn; int r = p->f(); delete p; return r; }  // 6. 방금 new 한 것
int t7_qualified(const Dn& d)      { return d.Dn::f(); }            // 7. 이름으로 부른다
int t8_nonvirtual(const N& n)      { return n.g(); }                // 8. 비가상 — 대조군
}
```

★★ **세는 법을 스크립트로 고정했다** — 사람이 어셈블리를 눈으로 세지 않는다.

```bash
# devirt-grid.sh
# 디버추얼라이제이션 격자 — devirt.cpp 의 탐침 여덟을 두 컴파일러 × -O0/-O2 로 어셈블리까지 내리고
# 함수마다 「간접 call/jmp」(call *…)·「f 나 g 를 이름으로 부르는 call/jmp」·「f 의 주소를 싣는 leaq」 개수를 센다
set -u -o pipefail
for cc in g++ clang++; do
  for opt in -O0 -O2; do
    echo "[$cc $opt]"
    $cc -std=c++20 $opt -S -fno-asynchronous-unwind-tables -fcf-protection=none -o devirt.s devirt.cpp || exit 1
    awk '
      /^t[0-9]_[a-z_]*:/        { name = $1; sub(":", "", name); ind = 0; dir = 0; adr = 0; next }
      name == ""                { next }
      /^\t(call|jmp)q?\t\*/     { ind++ }
      /^\t(call|jmp)q?\t_ZNK(2D[nfm]1fEv|1N1gEv)/ { dir++ }
      /^\tleaq\t_ZNK2D[nfm]1fEv/ { adr++ }
      /^\.LFE|^\.Lfunc_end/     {
        verdict = (ind > 0 && adr > 0) ? "추측 후 간접" : (ind > 0) ? "간접" : (dir > 0) ? "직접" : "인라인(call 없음)"
        printf "  %-18s 간접 %d · 직접 %d · f 주소 %d  -> %s\n", name, ind, dir, adr, verdict
        name = ""
      }' devirt.s
  done
done
rm -f devirt.s
```

```text
===== bash devirt-grid.sh (exit=0) =====
[g++ -O0]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 1 · f 주소 0  -> 직접
  t4_final_func      간접 0 · 직접 1 · f 주소 0  -> 직접
  t5_local_object    간접 0 · 직접 1 · f 주소 0  -> 직접
  t6_new_then_call   간접 2 · 직접 0 · f 주소 0  -> 간접
  t7_qualified       간접 0 · 직접 1 · f 주소 0  -> 직접
  t8_nonvirtual      간접 0 · 직접 1 · f 주소 0  -> 직접
[g++ -O2]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 1  -> 추측 후 간접
  t3_final_class     간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t4_final_func      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t5_local_object    간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t6_new_then_call   간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t7_qualified       간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t8_nonvirtual      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
[clang++ -O0]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 1 · f 주소 0  -> 직접
  t4_final_func      간접 0 · 직접 1 · f 주소 0  -> 직접
  t5_local_object    간접 0 · 직접 1 · f 주소 0  -> 직접
  t6_new_then_call   간접 2 · 직접 0 · f 주소 0  -> 간접
  t7_qualified       간접 0 · 직접 1 · f 주소 0  -> 직접
  t8_nonvirtual      간접 0 · 직접 1 · f 주소 0  -> 직접
[clang++ -O2]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t4_final_func      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t5_local_object    간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t6_new_then_call   간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t7_qualified       간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t8_nonvirtual      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
```

| 탐침 | g++ `-O0` | g++ `-O2` | clang `-O0` | clang `-O2` |
|---|---|---|---|---|
| 1. 기반 참조 `const B&` | 간접 | ★★★ **간접** | 간접 | ★★★ **간접** |
| 2. 파생 참조 `const Dn&`(밑에 또 파생 가능) | 간접 | ★★★ **추측 후 간접** | 간접 | ★★★ **간접** |
| 3. 정적 타입이 **`final` 클래스** | ★★★ **직접** | 인라인 | ★★★ **직접** | 인라인 |
| 4. 정적 타입의 **`f` 가 `final`** | ★★★ **직접** | 인라인 | ★★★ **직접** | 인라인 |
| 5. **지역 객체** | ★★ **직접** | 인라인 | ★★ **직접** | 인라인 |
| 6. 방금 `new` 한 것 `B* p = new Dn` | 간접(+ 삭제 1) | ★★ **인라인** | 간접(+ 삭제 1) | ★★ **인라인** |
| 7. 이름으로 부름 `d.Dn::f()` | 직접 | 인라인 | 직접 | 인라인 |
| 8. 비가상 `n.g()`(대조군) | 직접 | 인라인 | 직접 | 인라인 |

- ★★★ **1번은 `-O2` 에서도 간접이다** — 두 컴파일러 다 **`jmp *(%rax)`** 다. **무엇이 불릴지 이 번역 단위 안에서 증명할 수 없기** 때문이다.
- ★★★ **8번(비가상)은 `-O2` 에서 `call` 이 사라진다** — `movl $4, %eax` 한 줄이다. **1번과 8번의 차이가 「인라인이 막힌다」의 실체**다.
- ★★★ **3·4·5번은 `-O0` 에서 이미 직접 호출이다** — 최적화를 **하나도 안 켰는데** 간접이 아니다.\
  ★ 이것은 최적화 패스가 아니라 **컴파일러 앞단**의 판단이다 — 정적 타입이 `final` 이거나 **객체 자체**(참조가 아니라)이면 **받을 함수가 하나뿐**임을 **문법만 보고** 안다.
- ★★★ **2번에서 두 컴파일러가 갈렸다** — g++ `-O2` 만 「**추측 후 간접**」이다.

```text
===== g++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[0-9]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:
	movq	(%rdi), %rax
	jmp	*(%rax)
t2_derived_ref:
	movq	(%rdi), %rax
	leaq	_ZNK2Dn1fEv(%rip), %rdx
	movq	(%rax), %rax
	cmpq	%rdx, %rax
	jne	.L8
	movl	$3, %eax
	ret
.L8:
	jmp	*%rax
t3_final_class:
	movl	$1, %eax
	ret
t4_final_func:
	movl	$2, %eax
	ret
t5_local_object:
	movl	$3, %eax
	ret
t6_new_then_call:
	movl	$3, %eax
	ret
t7_qualified:
	movl	$3, %eax
	ret
t8_nonvirtual:
	movl	$4, %eax
	ret
```

```text
===== clang++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[0-9]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:                            # @t1_base_ref
	movq	(%rdi), %rax
	jmpq	*(%rax)                         # TAILCALL
t2_derived_ref:                         # @t2_derived_ref
	movq	(%rdi), %rax
	jmpq	*(%rax)                         # TAILCALL
t3_final_class:                         # @t3_final_class
	movl	$1, %eax
	retq
t4_final_func:                          # @t4_final_func
	movl	$2, %eax
	retq
t5_local_object:                        # @t5_local_object
	movl	$3, %eax
	retq
t6_new_then_call:                       # @t6_new_then_call
	movl	$3, %eax
	retq
t7_qualified:                           # @t7_qualified
	movl	$3, %eax
	retq
t8_nonvirtual:                          # @t8_nonvirtual
	movl	$4, %eax
	retq
```

```text
   t2_derived_ref (const Dn& d) { return d.f(); }         g++ -O2

   movq  (%rdi), %rax              vptr 을 읽는다
   leaq  _ZNK2Dn1fEv(%rip), %rdx   ★ Dn::f 의 주소를 싣는다
   movq  (%rax), %rax              vtable 첫 칸을 읽는다
   cmpq  %rdx, %rax                ★ 「그 칸이 Dn::f 인가?」
   jne   .L8                       아니면 ─┐
   movl  $3, %eax ; ret            맞으면 ★ 인라인한 본체(3)를 돌려준다
.L8: jmp *%rax                      ←──────┘ 간접 호출로 떨어진다
```

- ★★★ **g++ 는 「아마 `Dn::f` 일 것」이라 추측하고 비교 한 번으로 확인한 뒤 인라인한다** — 틀리면 **간접 호출로 떨어진다.**\
  ★ `Dn` 이 `final` 이 아니므로 **밑에 또 파생이 있을 수 있어** 확정은 못 한다. 그래서 **양쪽 경로를 다** 만든다.
- ★★ **clang `-O2` 는 추측하지 않는다** — **`jmpq *(%rax)`** 두 줄이다.
- ★★ **그 추측은 g++ 의 한 패스가 한다** — `-fno-devirtualize-speculatively` 로 끄면 **g++ 도 clang 과 같은 두 줄**이 된다.

```text
===== g++ -std=c++20 -O2 -fno-devirtualize-speculatively -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t2_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t2_derived_ref:
	movq	(%rdi), %rax
	jmp	*(%rax)
```

- ★★ **6번(`new` 직후)은 두 컴파일러 다 `-O2` 에서 인라인**이다 — `new Dn` 을 **같은 함수 안에서 봤으므로** 동적 타입을 안다.\
  ★ `-O0` 의 「간접 2」는 **`f` 호출 하나 + `delete p` 의 삭제 소멸자 호출 하나**다([20번](../20-virtual-destructors-and-polymorphic-deletion/) (7)의 `D0`).

★★ **`-O0` 에서 1번과 3번을 나란히 본다** — 최적화 없이도 갈리는 자리다.

```text
===== g++ -std=c++20 -O0 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[13]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rax
	movq	(%rax), %rax
	movq	(%rax), %rdx
	movq	-8(%rbp), %rax
	movq	%rax, %rdi
	call	*%rdx
	leave
	ret
t3_final_class:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rax
	movq	%rax, %rdi
	call	_ZNK2Df1fEv
	leave
	ret
```

```text
===== clang++ -std=c++20 -O0 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[13]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:                            # @t1_base_ref
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rdi
	movq	(%rdi), %rax
	callq	*(%rax)
	addq	$16, %rsp
	popq	%rbp
	retq
t3_final_class:                         # @t3_final_class
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rdi
	callq	_ZNK2Df1fEv
	addq	$16, %rsp
	popq	%rbp
	retq
```

- ★★★ **두 함수의 차이는 한 줄이다** — `call *%rdx`(vtable 에서 읽은 주소) 대 **`call _ZNK2Df1fEv`**(이름).\
  ★ 앞의 `movq (%rax), %rax` · `movq (%rax), %rdx` 두 줄이 **vptr → vtable 칸**을 읽는 것이다. **3번에는 그 두 줄이 없다.**

```text
   「비용」으로 센 것 — 이 셋뿐이다

   ① 간접 호출이 되나         call */jmp * 가 있나              1·2(clang)번 -O2 에서도 있다
   ② 누가 받는지 컴파일러가 아나  call <이름> 인가                3·4·5·7번은 -O0 에서도 이름이다
   ③ 인라인되나                call 이 사라지나                  1번은 -O2 에서도 안 사라진다 · 8번은 사라진다

   ★ 안 잰 것: 시간 · 분기 예측 · 캐시 · 코드 크기가 성능에 미치는 영향
```

- ★★★ **이 격자가 「가상 호출의 비용」에 대해 말하는 전부**다 — **간접 호출이 되고, 인라인이 막힌다.**\
  ★★★ **「그래서 느리다」는 이 격자가 말하지 않는다.** 인라인이 막혀서 **무엇을 못 하게 됐는지**(상수 접기 · 루프 최적화)는 호출하는 쪽 코드에 달려 있고, 여기서 **재지 않았다.**
- ★★ **`final` 이 주는 것을 정확히 말하면** — 「**빠르게 한다**」가 아니라 「**컴파일러가 받을 함수를 증명할 수 있게 한다**」다. 그 뒤에 직접 호출·인라인이 **따라올 수 있다.**

### (5) ★★ 객체 크기에 vptr 가 붙는다 — 19편 인용

★ **다시 재지 않는다** — [19번](../19-inheritance-virtual-functions-override-final/) (8)의 `(4)` 가 **`BaseNV 8 · BaseV 16`** 을 찍었다. **가상 함수가 하나라도 생기면 vptr 8바이트**가 붙는다.\
★ [20번](../20-virtual-destructors-and-polymorphic-deletion/) (3)의 격자도 같은 8 을 보였다(`sizeof` **32 대 40**).\
★★ **이 편이 새로 보이는 것은 「인터페이스를 둘 물려받으면 vptr 가 둘」이다** — (6).

### (6) ★★ 인터페이스 관용구 — 둘을 물려받으면 vptr 가 둘이다

**언제 쓰나** — 데이터 없는 순수 가상만의 클래스를 **여럿** 구현할 때.

```cpp
/* abs05.cpp */
// 인터페이스 관용구 — 데이터 없는 순수 가상만의 클래스, 그리고 둘을 함께 물려받으면
#include <cstdio>
#include <type_traits>

struct Reader { virtual int  read() = 0;     virtual ~Reader() = default; };   // 데이터가 없다
struct Writer { virtual void write(int) = 0; virtual ~Writer() = default; };

struct Pipe : Reader, Writer {                   // 인터페이스 둘을 구현한다
    int buf = 0;
    int  read() override       { return buf; }
    void write(int v) override { buf = v; }
};

int main() {
    std::printf("(1) sizeof  Reader %zu · Writer %zu · Pipe %zu (int 는 %zu)\n",
                sizeof(Reader), sizeof(Writer), sizeof(Pipe), sizeof(int));
    std::printf("(2) is_abstract  Reader %d · Pipe %d  |  is_polymorphic Reader %d\n",
                (int)std::is_abstract_v<Reader>, (int)std::is_abstract_v<Pipe>,
                (int)std::is_polymorphic_v<Reader>);
    Pipe p;
    Reader* r = &p;
    Writer* w = &p;
    w->write(42);
    std::printf("(3) w->write(42) 뒤 r->read() = %d\n", r->read());
    std::printf("(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = %td\n",
                (char*)w - (char*)r);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) sizeof  Reader 8 · Writer 8 · Pipe 24 (int 는 4)
(2) is_abstract  Reader 1 · Pipe 0  |  is_polymorphic Reader 1
(3) w->write(42) 뒤 r->read() = 42
(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = 8
```

★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic abs05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) sizeof  Reader 8 · Writer 8 · Pipe 24 (int 는 4)
(2) is_abstract  Reader 1 · Pipe 0  |  is_polymorphic Reader 1
(3) w->write(42) 뒤 r->read() = 42
(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = 8
```

- ★★ **`Reader`·`Writer` 는 각각 8** — 데이터가 **하나도 없는데** 8바이트다. **vptr 하나**다.
- ★★★ **`Pipe` 는 24** — `int` 하나(4)에 **vptr 둘(16)** 과 정렬 패딩(4)이다.
- ★★★ **같은 객체인데 `Writer*` 와 `Reader*` 의 값이 8 차이난다** — `Writer` 부분 객체가 **8바이트 뒤**에 있기 때문이다.

```text
===== clang++ -std=c++20 -Xclang -fdump-record-layouts -fsyntax-only abs05.cpp | sed -n '/^ *0 | struct Pipe$/,/nvalign/p' (exit=0) =====
         0 | struct Pipe
         0 |   struct Reader (primary base)
         0 |     (Reader vtable pointer)
         8 |   struct Writer (base)
         8 |     (Writer vtable pointer)
        16 |   int buf
           | [sizeof=24, dsize=20, align=8,
           |  nvsize=20, nvalign=8]
```

```text
===== g++ -std=c++20 -fdump-lang-class=stdout -c abs05.cpp -o /dev/null | sed -n '/^Vtable for Pipe/,/^$/p;/^Class Pipe/,/^$/p' (exit=0) =====
Vtable for Pipe
Pipe::_ZTV4Pipe: 11 entries
0     (int (*)(...))0
8     (int (*)(...))(& _ZTI4Pipe)
16    (int (*)(...))Pipe::read
24    (int (*)(...))Pipe::~Pipe
32    (int (*)(...))Pipe::~Pipe
40    (int (*)(...))Pipe::write
48    (int (*)(...))-8
56    (int (*)(...))(& _ZTI4Pipe)
64    (int (*)(...))Pipe::_ZThn8_N4Pipe5writeEi
72    (int (*)(...))Pipe::_ZThn8_N4PipeD1Ev
80    (int (*)(...))Pipe::_ZThn8_N4PipeD0Ev

Class Pipe
   size=24 align=8
   base size=20 base align=8
Pipe (0x0x78c923769cb0) 0
    vptr=((& Pipe::_ZTV4Pipe) + 16)
Reader (0x0x78c92323fb40) 0 nearly-empty
      primary-for Pipe (0x0x78c923769cb0)
Writer (0x0x78c92323fba0) 8 nearly-empty
      vptr=((& Pipe::_ZTV4Pipe) + 64)
```

```text
   Pipe 객체 (24바이트)                     Pipe 의 vtable (11칸)

   0  [ Reader vptr ] ───────────────▶  16  Pipe::read     ┐
   8  [ Writer vptr ] ──────────┐       24  Pipe::~Pipe     │ 주 vtable (Reader 겸 Pipe)
  16  [ int buf     ]           │       32  Pipe::~Pipe     │
  20  [ 패딩        ]           │       40  Pipe::write     ┘
                                │       48  -8               ★ offset_to_top — 「나는 전체의 8바이트 뒤다」
                                │       56  RTTI
                                └────▶  64  _ZThn8_…write   ★ thunk — this 를 8 빼고 Pipe::write 로
                                        72  _ZThn8_…D1Ev
                                        80  _ZThn8_…D0Ev
```

- ★★★ **vtable 이 두 덩어리**다 — 앞 덩어리는 `Reader`(와 `Pipe` 자신)의 것, **뒤 덩어리(48\~80)는 `Writer` 부분 객체의 것**이다.
- ★★★ **`offset_to_top` 이 `-8`** — 19편 (11)에서는 **항상 0** 이던 칸이다. 19편이 「다중 상속에서 쓰인다」고 **안 잰 채** 남겨 둔 자리가 여기서 **값을 가졌다.**
- ★★ **`_ZThn8_` 은 thunk 다** — `Writer*` 로 `write` 를 부르면 `this` 가 **`Writer` 부분**을 가리키므로, **8 을 빼서 `Pipe` 의 시작으로 되돌린 뒤** `Pipe::write` 로 간다.\
  ★ **이 조정은 간접 호출 한 번에 명령이 더 붙는 자리**다 — 다만 **몇 명령인지는 이 문서가 세지 않았다.**
- ★ 레이아웃은 clang `-fdump-record-layouts`, vtable 은 g++ `-fdump-lang-class` 로 찍었다 — **g++ 덤프의 주소는 흔들리는 칸**이다.

### (7) ★★ 다른 언어는 이 자리를 어디서 푸나 — C# 인용 · Java 실측

★★ C# 은 C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **16번**([`16-inheritance-virtual-override-abstract-sealed-new/`](../../../csharp/syntax/16-inheritance-virtual-override-abstract-sealed-new/)) (4)가 실측했다 — **그 편의 결론을 인용한다.**

| | C# (그 편 실측) | C++ (이 편 (4)) |
|---|---|---|
| 비가상 메서드 호출 | ★★★ **`callvirt`** — 널 검사 때문 | ★★ **직접 `call` 또는 인라인** |
| `sealed`(C++ 의 `final`) 타입의 가상 메서드 | ★★★ **여전히 `callvirt`** | ★★★ **`-O0` 에서도 직접 `call`** |
| 디버추얼라이제이션을 누가 하나 | ★★★ **JIT**(IL 층에서는 안 바꾼다) | ★★★ **컴파일러**(앞단 + 최적화 패스) |

★ **「없다고 적기 전에 버전 호출을 블록으로 남긴다」**(규칙 26).

```text
===== set +u; source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1; set -u; which javac && javac -version (exit=0) =====
/home/jun/.sdkman/candidates/java/current/bin/javac
javac 21.0.5
```

```java
// Abs.java
// 자바의 추상 클래스·인터페이스·final 클래스 — 호출 자리의 바이트코드 명령을 찍는다
public class Abs {
    interface Shape { int area(); }                        // 인터페이스
    static abstract class Base { abstract int area(); }    // 추상 클래스
    static final class Sq extends Base { int area() { return 9; } }   // final 클래스

    static int viaInterface(Shape s) { return s.area(); }
    static int viaAbstract(Base b)   { return b.area(); }
    static int viaFinal(Sq q)        { return q.area(); }

    public static void main(String[] a) {
        System.out.println(viaInterface(() -> 4) + " " + viaAbstract(new Sq()) + " " + viaFinal(new Sq()));
    }
}
```

```text
===== set +u; source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1; set -u; javac Abs.java && java Abs && javap -c Abs | sed -n '/static int via/,/ireturn/p' (exit=0) =====
4 9 9
  static int viaInterface(Abs$Shape);
    Code:
       0: aload_0
       1: invokeinterface #7,  1            // InterfaceMethod Abs$Shape.area:()I
       6: ireturn
  static int viaAbstract(Abs$Base);
    Code:
       0: aload_0
       1: invokevirtual #13                 // Method Abs$Base.area:()I
       4: ireturn
  static int viaFinal(Abs$Sq);
    Code:
       0: aload_0
       1: invokevirtual #16                 // Method Abs$Sq.area:()I
       4: ireturn
```

- ★★★ **자바의 `final` 클래스도 바이트코드는 `invokevirtual`** 이다 — **C# 의 `sealed` → `callvirt` 와 같은 모양**이다.\
  ★ 인터페이스는 **`invokeinterface`**, 추상 클래스는 **`invokevirtual`** — **명령 이름만** 다르고 둘 다 **디스패치 명령**이다.
- ★★ **세 언어가 같은 일을 다른 층에서 한다** — C++ 은 **컴파일러가 기계어로**, C#·Java 는 **바이트코드는 그대로 두고 JIT 이** 바꾼다(JIT 의 결과는 이 문서가 **안 찍었다**).
- ★ 정본 — Java 는 Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) · C# 은 위 C# 갈래 16번이다.

## 문법 — 형태와 규칙

### 형태

```cpp
/* abs07.cpp */
// 인터페이스 한 벌의 형태. 이 파일은 그대로 컴파일된다
#include <cstdio>
#include <memory>
#include <vector>

class Storage {                                  // ① 인터페이스 — 데이터 없음, 순수 가상 + 가상 소멸자
public:
    virtual ~Storage() = default;
    virtual bool put(int key, int value) = 0;
    virtual bool get(int key, int& out) const = 0;
protected:
    Storage() = default;                         // 인터페이스를 값으로 복사하지 않는다
    Storage(const Storage&) = default;
    Storage& operator=(const Storage&) = default;
};

class Logged : public Storage {                  // ② 비가상 인터페이스(NVI) — 공개 함수는 비가상, 구현은 protected 가상
public:
    bool put(int k, int v) final { std::printf("  put(%d)\n", k); return do_put(k, v); }
protected:
    virtual bool do_put(int k, int v) = 0;
};

class ArrayStore final : public Logged {         // ③ 잎은 final — 이 타입으로 부르면 컴파일러가 직접 부를 수 있다
public:
    bool get(int k, int& out) const override {
        if (k < 0 || k >= 4) return false;
        out = a_[k]; return true;
    }
protected:
    bool do_put(int k, int v) override { if (k < 0 || k >= 4) return false; a_[k] = v; return true; }
private:
    int a_[4] = {};
};

int main() {
    std::vector<std::unique_ptr<Storage>> v;
    v.push_back(std::make_unique<ArrayStore>());
    v[0]->put(2, 42);
    int x = 0;
    bool ok = v[0]->get(2, x);                   // 인자 평가 순서에 기대지 않게 먼저 부른다
    std::printf("get(2) -> %d, x=%d\n", (int)ok, x);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  put(2)
get(2) -> 1, x=42
```

★ **clang 도 한 글자도 같았다.**

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic abs07.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  put(2)
get(2) -> 1, x=42
```

### 규칙

- **순수 가상은 `= 0`** 이고, 하나라도 남으면 **추상 클래스**다 — 객체를 못 만든다((1)).
- ★★ **순수 가상에도 본체를 줄 수 있다** — **클래스 밖에서** 주고, **이름으로만** 불린다((2)).
- ★★★ **생성자·소멸자에서 순수 가상을 부르지 않는다** — 직접이든 한 다리를 거치든 **UB** 이고, 한 다리를 거치면 **경고도 0건**이다((3)).
- ★★ **잎 클래스에는 `final`** — 컴파일러가 **받을 함수를 증명**할 수 있게 된다((4)의 3·4번).
- ★★ **인터페이스는 데이터 없이 순수 가상 + 가상 소멸자** — 소멸자 규칙은 [20번](../20-virtual-destructors-and-polymorphic-deletion/)이다.
- ★ **인터페이스를 여럿 물려받으면 vptr 가 여럿**이다 — 부분 객체마다 하나((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | 무엇이 되나 | 어디서 |
|---|---|---|
| `Codec c;`(순수 가상이 남은 클래스) | ★★ **컴파일 에러** — 남은 이름을 나열한다 | (1) |
| `virtual void f() = 0 { }` | ★★ **문법 에러** — 본체는 클래스 밖에 | (2) |
| 생성자에서 순수 가상을 **직접** 부름 | ★★ **경고 1** + g++ **링크 에러** · clang **`run exit=134`** | (3) |
| 생성자에서 순수 가상을 **한 다리 거쳐** 부름 | ★★★ **경고 0** + 두 컴파일러 **`run exit=134`** | (3) |

## 어디서 틀리나

### 1. ★★★ 「가상 호출은 느리다」

**이 문서가 잰 것이 아니다.** 잰 것은 (4)의 세 가지 — **간접 호출이 되나 · 이름으로 부르나 · 인라인되나**다.\
★ 「느리다」는 **시간 측정**이 있어야 하는 주장이고, 이 문서에는 **그 측정이 없다.**

### 2. ★★★ 「`final` 을 붙여야 디버추얼라이제이션이 된다」

(4)의 5·6·7번이 반증이다 — **지역 객체 · 방금 `new` 한 것 · 이름으로 부른 것**은 `final` 없이도 **직접·인라인**이 됐다.\
★ `final` 은 **참조·포인터로 받은 자리**에서 증명의 재료가 된다(3·4번).

### 3. ★★ 「`final` 이 없으면 기반 참조 호출은 무조건 간접이다」

(4)의 2번이 반증이다 — g++ `-O2` 는 **추측하고 비교한 뒤 인라인**한다. 다만 **틀린 경우를 위한 간접 호출도 남긴다.**

### 4. ★★ 「순수 가상 = 본체가 없는 함수」

(2)가 반증이다 — **본체가 있어도 추상**이다. 순수 가상은 「**파생이 반드시 덮는다**」는 약속이다.

### 5. ★★★ 「생성자에서 부르면 기반 것이 불리니 순수 가상이면 컴파일 에러가 나겠지」

(3)이 반증이다 — **컴파일은 된다.** 직접 부르면 **경고 1건**, 한 다리 거치면 **경고 0건**이고, 실행하면 **`pure virtual method called` 로 죽는다.**

### 6. ★ 「인터페이스는 데이터가 없으니 크기가 0이다」

(6)이 반증이다 — **`Reader` 8바이트**(vptr). 둘을 물려받으면 **16바이트**가 붙는다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제에서는 「vtable」이라는 말 자체가 표준 밖이다** — 표준은 **가상 함수가 동적 타입으로 골라진다**는 **결과**만 말하고, **무엇으로 고르나는 말하지 않는다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **순수 가상이 남으면 추상 — 객체를 못 만든다**((1)) · **순수 가상의 본체는 이름으로 부를 수 있다**((2)) · **본체는 클래스 밖에서**((2)) · **가상 함수는 동적 타입으로 골라진다**(결과만) | 진단 전문 + `cc exit` · 호출 로그 | ★★ 「**이 호출이 간접인가**」는 표준이 **묻지도 않는다** |
| **조건부 표준** | 특정 조건에서만 | ★ **`final` 은 C++11부터** | `-std=c++20` 으로만 돌렸다 | — |
| **구현 정의** | 문서화 의무 | ★★ **Itanium C++ ABI 의 배치** — vptr 가 앞에 · `offset_to_top` · thunk `_ZThn8_` · 삭제/완전 소멸자 두 칸((6)) · **`sizeof` 8·24** · 진단 문구 | 레이아웃·vtable 덤프 · `sizeof` | ★ **다른 ABI(MSVC)는 배치가 다르다** |
| **미명시** | 몇 가지 중 하나 — 표준이 말하지 않는 것 | ★★★ **디스패치를 vtable 로 하는가 자체**(표준에 그 낱말이 없다) · ★★★ **디버추얼라이제이션을 언제 하나**((4) — g++ 만 추측) · **생성자 속 직접 호출을 직접 부를지 vtable 로 부를지**((3)) | 어셈블리 격자 · 두 컴파일러 대조 | ★★★ **판이 바뀌면 격자가 바뀔 수 있다** — 성질이 아니라 관찰이다 |
| **UB** | 아무 일이나 | ★★★ **생성자·소멸자에서 순수 가상을 가상 호출**((3)) — 정의가 있든 없든 | `run exit=134` · 링크 에러 · 경고 개수 | ★★★ **한 다리 거치면 경고 0건** · ASan 은 부적용(메모리 오류가 아니다) |

- ★★ **19편과의 조정** — 19편은 **vtable 의 배치**를 「구현 정의」에 뒀다. 그 배치는 **Itanium C++ ABI 가 문서화**하므로 그 칸이 맞다.\
  ★ 이 편이 「미명시」에 둔 것은 **「vtable 로 디스패치한다」는 사실 자체**다 — 표준은 그것을 **요구하지도 금하지도 않는다.** **두 층이 다른 질문에 답한다.**

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | 어셈블리 | 호출 로그 |
|---|---|---|---|---|---|
| 추상 클래스 인스턴스화 | 표준 | **error 3** | **error 3** | — | — |
| 순수 가상 한 줄 본체 | 표준 | **error 1** | **error 2** | — | — |
| ★★ **생성자에서 순수 가상 직접** | UB | ★ **warning 1** · 링크 에러 | ★ **warning 1** · 134 | ★ 직접 대 간접(갈림) | ★ `Derived::init` **0회** |
| ★★★ **생성자에서 순수 가상 한 다리** | UB | ★★★ **0건** · 134 | ★★★ **0건** · 134 | — | ★ `Derived::init` **0회** |
| ★★★ **기반 참조 호출이 간접인가** | 미명시 | ★★★ **0건**(물을 방법이 없다) | ★★★ **0건** | ★★★ **`jmp *`** | — |
| ★★ **g++ 의 추측 디버추얼라이제이션** | 미명시 | 0건 | — | ★★ **`leaq`+`cmpq`** | — |

- ★★ **이 표의 결론 두 줄**
  - ★★★ **「비용」에 관한 사실은 컴파일러 진단 어디에도 안 나온다** — 어셈블리로만 보인다.
  - ★★★ **생성자 속 순수 가상은 한 다리만 거쳐도 도구가 전부 조용하다** — 실행해야 안다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

★ 던진 후보 — (2)의 **`virtual void f() = 0 { }`**. **두 컴파일러가 `cc exit=1` 로 막았다.**\
★ **「못 찾았다」까지가 주장**이다. 같은 배치의 새 항목은 [22번](../22-operator-overloading/)·[23번](../23-three-way-comparison-spaceship/)에 있다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 구현을 갈아 끼울 경계(저장소 · 코덱) | ★★★ **순수 가상 인터페이스 + 가상 소멸자** | 호출하는 쪽이 구현을 몰라도 된다 |
| 파생이 반드시 덮되 기본 동작도 준다 | ★★ **순수 가상 + 클래스 밖 본체** | 파생이 `Base::f()` 로 부른다((2)) |
| 초기화 훅 | ★★★ **생성자 밖 `init()`** | 생성자 속 순수 가상은 UB((3)) |
| 잎 클래스 | ★★ **`final`** | 받을 함수를 증명할 재료가 된다((4)) |
| 호출하는 쪽에서 구현을 이미 안다 | ★ **가상을 안 쓰는 선택지도 있다**(템플릿 등) | 인라인이 막히지 않는다((4)의 8번) — 다만 **그 이득의 크기는 재지 않았다** |

- ★★★ **「성능 때문에 가상을 피하라」는 이 문서의 조언이 아니다** — 이 문서가 보인 것은 **명령이 어떻게 바뀌나**까지다.

## 핵심 문장

- **순수 가상이 하나라도 남으면 추상 클래스**이고, 두 컴파일러는 **남은 이름을 나열한다.**
- ★★ **순수 가상에도 본체가 있을 수 있다** — 클래스 밖에서 주고, **이름으로만** 불린다.
- ★★★ **생성자에서 순수 가상을 부르면 UB** — 한 다리만 거쳐도 **경고 0건**에 **`pure virtual method called` 로 죽는다.** 직접 부르면 **g++ 는 링크 에러, clang 은 134** 로 갈렸다.
- ★★★ **가상 호출의 「비용」으로 잰 것은 「간접 호출이 되고, 인라인이 막힌다」까지다** — 1번 탐침은 `-O2` 에서도 **`jmp *(%rax)`** 였다.
- ★★ **`final` 클래스·`final` 함수·지역 객체는 `-O0` 에서도 직접 호출**이고, g++ 는 `final` 이 없는 자리를 **추측**으로 푼다(clang 은 안 한다).
- ★★ **인터페이스 둘을 물려받으면 vptr 가 둘**이고, 두 번째 vtable 에 **`offset_to_top = -8`** 과 **thunk** 가 생긴다.

## 관련 자료

- [19번](../19-inheritance-virtual-functions-override-final/) — ★★★ **이 편의 직접 선행.** 그 편이 「**가상 호출 비용은 21번이 정본**」으로 넘긴 창을 (4)가 이어받았다.\
  그쪽은 **vtable 의 구조**까지, 여기는 **그 구조가 명령을 어떻게 바꾸나**부터다.
- [20번](../20-virtual-destructors-and-polymorphic-deletion/) — **순수 가상 소멸자**는 거기 (8)이 정본이다. (4)의 6번 탐침의 「삭제 1」이 그 편 (7)의 `D0` 이다.
- [`oop-basics/`](../../../../oop-basics/) §17 — **추상 클래스의 개념.** 여기는 **C++ 구현 모델**까지.
- ★★ C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **16번**([`16-inheritance-virtual-override-abstract-sealed-new/`](../../../csharp/syntax/16-inheritance-virtual-override-abstract-sealed-new/)) — **`callvirt`·`sealed`·JIT** 의 실측을 (7)이 인용했다.
- Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **11번**([`11-interfaces-default-methods/`](../../../java/syntax/11-interfaces-default-methods/)) — 인터페이스의 정본. (7)에서 `javap -c` 로 한 번 던졌다.

## 용어 풀이

> **순수 가상 함수(pure virtual function)** — `= 0` 으로 선언한 가상 함수. **파생이 반드시 덮어야** 한다. 본체는 있어도 된다.\
> 예: (2)의 `Logger::log` 는 본체가 있는데도 `is_abstract<Logger>` 가 1 이었다.

> **추상 클래스(abstract class)** — 순수 가상이 하나라도 남은 클래스. **객체를 만들 수 없다.**\
> 예: (1)에서 `Half` 는 `decode`·`name` 이 남아 추상이었다.

> **간접 호출(indirect call)** — 메모리에서 읽은 주소로 부르는 것. `call *…`·`jmp *…`.\
> 예: (4)의 1번 탐침 — `-O2` 에서도 `jmp *(%rax)`.

> **디버추얼라이제이션(devirtualization)** — 가상 호출을 **직접 호출로 바꾸는 것**. 받을 함수를 증명할 수 있을 때만.\
> 예: (4)의 3번 탐침 — `-O0` 에서 `call _ZNK2Df1fEv`.

> **추측 디버추얼라이제이션(speculative devirtualization)** — 「아마 이 함수」라 보고 **주소를 비교해 맞으면 인라인, 아니면 간접 호출**.\
> 예: (4)의 2번 탐침 — g++ `-O2` 의 `leaq`·`cmpq`·`jne`.

> **인라인(inlining)** — 호출을 **본체로 바꿔 끼우는 것**. `call` 이 사라진다.\
> 예: (4)의 8번 탐침 — `movl $4, %eax` 한 줄.

> **`__cxa_pure_virtual`** — Itanium ABI 에서 **순수 가상 칸에 들어가는 함수**. 불리면 `pure virtual method called` 를 찍고 `terminate` 한다.\
> 예: (3)에서 `run exit=134`.

> **thunk** — `this` 를 **조정한 뒤 진짜 함수로 넘기는** 작은 함수.\
> 예: (6)의 `_ZThn8_N4Pipe5writeEi` — 8 을 빼고 `Pipe::write` 로 간다.

> **`offset_to_top`** — vtable 의 한 칸. **이 부분 객체가 전체 객체의 시작에서 얼마나 떨어져 있나.**\
> 예: (6)에서 `Writer` 부분의 vtable 에 `-8`.

## 더 들어가면

- **실행 시간을 재려면** — 벤치마크 하네스(반복·워밍업·잡음 측정)가 따로 필요하다. **간접 호출의 시간은 분기 예측기가 그 자리를 얼마나 맞히나**에 크게 달린다고 알려져 있다 — **이 문서는 그것을 확인하지 않았다.**
- **`-fstrict-vtable-pointers`(clang)·`-fdevirtualize-at-ltrans`(g++)·LTO** — 번역 단위를 넘어 디버추얼라이제이션 재료를 늘리는 장치들. 이 문서는 **던지지 않았다.**
- **가상 상속과 VTT** — (6)의 `offset_to_top` 에 **가상 기반 오프셋**이 더해지는 자리. 단일·다중 상속만 봤다.
- **정적 다형성(CRTP)·`std::variant`+`std::visit`** — 가상 없이 다형성을 얻는 길. 목록의 템플릿 주제들에서 다룬다.
