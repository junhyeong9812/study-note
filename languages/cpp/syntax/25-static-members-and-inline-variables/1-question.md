# cpp/syntax/25 — 정적 멤버·`inline` 변수(C++17) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「링크까지 가나」를 맞히는 것**이 절반이다 — 「컴파일됐으니 된다」로 뭉개지 말고
> **정의가 몇 개 생기고, 누가 그 주소를 요구하나**를 따라가야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · GNU ld 2.42 · x86-64 Linux. 번역 단위는 **`-c` 로 따로 컴파일한 뒤 링크**한다.
> ★★★ **이 주제의 본체는 「링커 진단과 `nm` 글자」다**(1·2·4번).
> ★ **「부적용인 창」이 둘 있다** — ASan(읽힌 값이 0 으로 채워진 정적 저장소다)과 `<type_traits>`(정의 위치는 타입의 성질이 아니다).
> ★★ **C 갈래 29번이 잰 것은 다시 묻지 않는다** — 잠정 정의·`-fcommon`·전역 `inline int` 의 `u`/`V`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 헤더 안에서 정의한 정적 데이터 멤버 (예측)

```cpp
/* cfg.h */
// 정적 데이터 멤버를 헤더 안에서 정의한다. -DASK_INLINE 이면 C++17 inline 판
#pragma once
struct Cfg {
#ifdef ASK_INLINE
    static inline int count = 0;
#else
    static int count;
#endif
    static int bump();
};
#ifndef ASK_INLINE
int Cfg::count = 0;
#endif
```

```cpp
/* cfg_a.cpp */
// 번역 단위 1 — cfg.h 를 포함하고 bump() 를 정의한다
#include "cfg.h"
int Cfg::bump() { return ++count; }
```

```cpp
/* cfg_b.cpp */
// 번역 단위 2 — cfg.h 를 포함하고 main 에서 쓴다
#include <cstdio>
#include "cfg.h"
int main() {
    Cfg::bump();
    Cfg::bump();
    Cfg::count += 10;
    std::printf("count = %d\n", Cfg::count);
}
```

- ★★ `-std=c++17` 로 두 파일을 따로 컴파일하면 **컴파일은 통과**하나 — 링크는?
- ★★ 링크가 안 된다면 링커는 **무엇의 이름**을 대나?
- ★ `nm -C cfg_a.o` 에서 `Cfg::count` 옆의 글자는?

### 2. ★★★ `-DASK_INLINE` 판 (예측)

- ★★ 링크가 되나 — 된다면 `count = ?`
- ★★★ `nm` 에서 `Cfg::count` 의 글자는 g++ 와 clang++ 에서 **같은가**?

### 3. ★★ 같은 `inline` 판을 `-std=c++14` 로 (예측)

- ★★ 두 컴파일러의 `cc exit` 와 `run exit` 는 — 경고는 몇 건인가?
- ★ 그것을 에러로 만들려면 무엇을 켜야 하나?

### 4. ★★★ 클래스 안에서 값을 준 상수를 참조로 넘기면 (예측)

```cpp
/* odr01.cpp */
// 클래스 안에서 값을 준 정적 상수 둘 — 값으로 읽기와 const int& 로 넘기기
// -DASK_REF_A · -DASK_REF_B 로 참조로 넘기는 줄을 하나씩 켠다 · -DASK_DEF_A · -DASK_DEF_B 는 클래스 밖 정의를 더한다
#include <algorithm>
#include <cstdio>

struct K {
    static const int     A = 7;
    static constexpr int B = 9;
};

#ifdef ASK_DEF_A
const int K::A;           // 클래스 밖 정의 — 초기자 없이
#endif
#ifdef ASK_DEF_B
constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
#endif

int main() {
    int x = 8;
    std::printf("값으로 읽기  A+0=%d B+0=%d\n", K::A + 0, K::B + 0);
#ifdef ASK_REF_A
    std::printf("std::max(K::A, x) = %d\n", std::max(K::A, x));
#endif
#ifdef ASK_REF_B
    std::printf("std::max(K::B, x) = %d\n", std::max(K::B, x));
#endif
    (void)x;
}
```

- ★★★ `-DASK_REF_A` · `-DASK_REF_B` 를 각각 **C++14/C++17 × `-O0`/`-O2`** 로 링크하면 **어느 칸이 깨지나**?
- ★★ `static const` 와 `static constexpr` 는 C++17 에서 같은 답인가?
- ★ C++17 에서 `-DASK_REF_A -DASK_REF_B` 로 만든 `odr01.o` 의 `nm` 에서 `K::A` 와 `K::B` 의 글자는?

### 5. ★★★ 두 번역 단위의 정적 멤버가 서로에 기대면 (예측)

```cpp
/* siof.h */
// siof.h — 두 번역 단위가 나눠 쓰는 선언
#pragma once
struct Config { static int base; };
struct Report { static int doubled; };
int& lazy_base();
```

```cpp
/* siof_cfg.cpp */
// siof_cfg.cpp — 동적 초기화가 필요한 정적 멤버 하나와, 같은 값을 함수 지역 static 으로 주는 함수
#include <cstdio>
#include "siof.h"

static int read_base() { std::fprintf(stderr, "    [siof_cfg] read_base() 가 돈다\n"); return 21; }

#ifdef ASK_CONSTINIT
constinit int Config::base = read_base();
#else
int Config::base = read_base();
#endif

int& lazy_base() {
    static int b = read_base();       // 처음 부를 때 초기화된다
    return b;
}
```

```cpp
/* siof_use.cpp */
// siof_use.cpp — 다른 번역 단위의 값으로 자기를 초기화한다. -DASK_LAZY 이면 함수를 거친다
#include <cstdio>
#include "siof.h"

static int make_doubled() {
#ifdef ASK_LAZY
    int b = lazy_base();
#else
    int b = Config::base;
#endif
    std::fprintf(stderr, "    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 %d\n", b);
    return b * 2;
}
int Report::doubled = make_doubled();

int main() {
    std::fprintf(stderr, "    [main] Report::doubled = %d\n", Report::doubled);
}
```

- ★★★ `g++ siof_cfg.o siof_use.o` 와 `g++ siof_use.o siof_cfg.o` 로 링크하면 `Report::doubled` 는 각각 얼마인가?
- ★★ 값이 다르다면 **읽은 쪽이 본 값**은 무엇이고 — 그것은 쓰레기인가?
- ★ clang++ 로 컴파일하면 답이 바뀌나?

### 6. ★★ `-DASK_LAZY` 로 함수 지역 `static` 을 거치면 (예측)

- ★★ 두 링크 순서에서 `Report::doubled` 는 각각 얼마인가?
- ★★ `-O2` 어셈블리에서 `lazy_base()` 는 `__cxa_guard_*` 를 **몇 번 부르는 코드**인가 — `-fno-threadsafe-statics` 면?
- ★ 이미 초기화된 뒤 부르면 어느 길로 나가나?

### 7. ★★ `-O2` 가 통과시킨 ODR 누락 (경계)

- ★★★ 4번에서 `-O0` 은 깨지고 `-O2` 는 링크되는 칸이 있다 — `-O2` 판은 **올바른 프로그램**인가?
- ★★ 그 판을 `-pedantic-errors` 로 던지면 잡히나 — 앞 편의 「`-pedantic-errors` 라야 잡힌다」 항목들과 무엇이 다른가?

### 8. ★ C 에서는 되던 전역 `int t;` (경계)

- ★★ 두 파일에 `int t;` 를 두고 **`g++ -fcommon`** 으로 링크하면? · 같은 파일을 **`gcc -x c -fcommon`** 으로 하면?
- ★ `nm` 글자는 두 경우에 각각 무엇인가?

### 9. ★★ C++17 의 암묵 `inline` 이 붙는 범위 (왜)

- ★★ 왜 `static constexpr` 는 C++17 에서 클래스 밖 정의가 필요 없어지고 `static const` 는 아닌가?
- ★ C++17 에서 `constexpr int K::B;` 를 굳이 쓰면 경고가 나나 — 어느 플래그로?

### 10. ★ 이 주제에서 ASan 을 안 쓰는 이유 (왜)

- ★ 5번에서 먼저 읽힌 `Config::base` 의 값은 왜 **UB 가 아닌가**?
- ★ 같은 실험을 `std::string` 정적 멤버로 하면 무엇이 달라질까?

### 11. 다른 주제와 잇기 (연결)

- ★★★ 1·2번은 C 갈래 몇 번의 무엇과 같은 문제를 푸나 — C 는 무엇으로, C++17 은 무엇으로 푸나?
- ★ 함수 지역 `static` 이 「처음 부를 때 생긴다」는 몇 번 주제가 로그로 쟀나?
- ★ ODR 일반과 모듈은 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
