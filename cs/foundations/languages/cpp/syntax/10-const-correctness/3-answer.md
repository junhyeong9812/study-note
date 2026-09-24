# cpp/syntax/10 — `const` 정확성 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **같은 UB 를 네 판으로 돌리는 것**이다(4번).
> **읽는 법** — `nm` 출력의 **주소는 흔들리는 칸**이다. 근거로 쓰는 것은 **심볼 종류 문자**(`r`·`R`·`U`)다.\
> UB 는 4번(`const_cast`)과 8번(리터럴 수정) 둘이고, **그 UB 가 만든 값은 「모순」으로만 읽는다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ 객체의 `const` 가 오버로드를 고른다 — `cb` 는 `const` 판으로 간다

**출력**

```text
===== 소스: cnst01.cpp =====
// const 멤버 함수와 const 오버로드 — 객체의 const 가 어느 함수를 고르나
#include <cstdio>

struct Buf {
    int a[3]{1, 2, 3};

    int&       at(int i)       { std::puts("    at()       비-const 판"); return a[i]; }
    const int& at(int i) const { std::puts("    at() const const 판");    return a[i]; }

    int sum() const { return a[0] + a[1] + a[2]; }
    void bump()     { ++a[0]; }
};

int main() {
    Buf b;
    const Buf& cb = b;

    std::puts("[1] b.at(0) = 9;        객체가 비-const");
    b.at(0) = 9;
    std::puts("[2] cb.at(0) 을 읽는다   객체가 const");
    std::printf("    값 %d\n", cb.at(0));
    std::puts("[3] const 객체로도 부를 수 있는 것");
    std::printf("    cb.sum() = %d\n", cb.sum());
    std::printf("    b.sum()  = %d   (비-const 객체도 const 멤버를 부른다)\n", b.sum());
    b.bump();
    std::printf("    b.bump() 뒤 sum = %d\n", b.sum());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] b.at(0) = 9;        객체가 비-const
    at()       비-const 판
[2] cb.at(0) 을 읽는다   객체가 const
    at() const const 판
    값 9
[3] const 객체로도 부를 수 있는 것
    cb.sum() = 14
    b.sum()  = 14   (비-const 객체도 const 멤버를 부른다)
    b.bump() 뒤 sum = 15
```

**왜 그런가**

- ★★★ **`at(int)` 와 `at(int) const` 는 다른 함수**다. 이름과 인자가 같아도 **`this` 의 타입이 다르다** —\
  앞은 `Buf*`, 뒤는 `const Buf*`. 그래서 **오버로드 후보로 같이 놓인다.**
- **`[1]` 은 `b` 가 비-const 이므로 두 후보 중 「더 잘 맞는」 비-const 판**을 고른다.\
  돌려준 것이 `int&` 라 `= 9` 가 된다.
- **`[2]` 는 `cb` 가 `const Buf&` 이므로 후보가 `const` 판 하나**다.\
  돌려준 것이 `const int&` 라 **읽기만 된다.**
- ★★ **값이 9 인 이유** — 앞줄에서 `b.at(0) = 9` 로 썼기 때문이다.\
  `b` 와 `cb` 는 **같은 객체를 보는 두 창**이다.
- ★ **`b.sum()` 이 되는 이유** — 비-const 객체는 **`const` 멤버도 부를 수 있다.**\
  `Buf&` 에서 `const Buf&` 로 가는 변환은 공짜다. 반대는 없다.
- ★★ 그래서 **고치지 않는 멤버 함수에 `const` 를 안 붙이면 전염된다** —\
  `const Buf&` 를 받는 함수가 **그 멤버를 통째로 못 쓴다.**
- **`cb.at(0) = 1;`** 은 컴파일 에러다 — `const int&` 를 왼쪽에 둘 수 없다.\
  (같은 종류의 에러가 7번의 (7)번 줄이다.)

```text
   b.at(0)      ->  at(int)         ->  int&        쓸 수 있다
   cb.at(0)     ->  at(int) const   ->  const int&  읽기만
        ↑
   this 의 타입이 후보를 고른다
```

### 2. ★★ `mutable` 이 둘 — `hits` 는 1·2·3, `cached` 는 -1 에서 42 로 한 번

**출력**

```text
===== 소스: cnst02.cpp =====
// mutable — const 멤버 함수 안에서 바뀌는 유일한 멤버
#include <cstdio>

struct Doc {
    int              text = 41;
    mutable int      cached = -1;      // 계산 결과 저장
    mutable unsigned hits = 0;         // 호출 횟수

    int score() const {
        ++hits;                         // const 인데 바뀐다
        if (cached < 0) cached = text + 1;
        return cached;
    }
};

int main() {
    const Doc d;
    std::printf("부르기 전: cached=%d hits=%u\n", d.cached, d.hits);
    for (int n = 1; n <= 3; ++n) {
        int v = d.score();              // ★ 한 줄에 하나만 — 평가 순서에 안 기댄다
        std::printf("%d회째    : score=%d cached=%d hits=%u\n", n, v, d.cached, d.hits);
    }
    std::printf("text      : %d  (이쪽은 const 객체라 못 바꾼다)\n", d.text);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
부르기 전: cached=-1 hits=0
1회째    : score=42 cached=42 hits=1
2회째    : score=42 cached=42 hits=2
3회째    : score=42 cached=42 hits=3
text      : 41  (이쪽은 const 객체라 못 바꾼다)
```

**왜 그런가**

- ★★★ **`d` 는 `const Doc` 인데 `hits` 가 늘어난다.** `mutable` 이 붙은 멤버는 **`const` 규칙에서 빠지기** 때문이다.
- **`cached` 는 -1 → 42 로 한 번만 바뀐다** — `if (cached < 0)` 이 두 번째부터 막는다.\
  ★ 「**결과는 항상 42 이고 내부만 바뀐다**」 — 이것이 논리적 `const` 의 정의다.
- **`text` 는 못 바꾼다** — `mutable` 이 아니므로 `const` 객체의 멤버로서 그대로 막힌다.\
  같은 종류의 에러가 7번의 (1)번 줄이다.
- ★★ **스레드 안전하지 않다.** `++hits` 는 동기화 없는 읽기-수정-쓰기다.\
  **`const` 를 보고 「읽기 전용이니 락이 필요 없다」고 읽으면 여기서 깨진다.**
- ★★★ **소스가 한 줄에 `d.score()` 와 `d.cached` 를 같이 안 넣은 이유** —\
  함수 인자의 **평가 순서가 미명시**라 어느 것이 먼저 읽힐지 모른다.\
  ★ 한 `printf` 에 섞으면 **어느 값이 찍힐지가 컴파일러에 달린다** — `cached`·`hits` 가 **호출 전 값**으로 나올 수 있다.\
  **출력이 평가 순서에 달린 블록은 근거가 못 된다** — 그래서 `int v = d.score();` 로 갈라 놨다.

### 3. ★★★ `outside` 가 1 → 99 → 7 로 바뀐다 — 경고는 0건

**출력**

```text
===== 소스: cnst03.cpp =====
// 비트단위 const 와 논리적 const — 포인터 멤버가 뚫는 구멍
#include <cstdio>

struct Holder {
    int  own = 1;        // 내 것
    int* p;              // 남의 것을 가리킨다

    explicit Holder(int* q) : p(q) {}

    void poke() const { *p = 99; }        // 된다 — p 가 const 지 *p 는 아니다
    int& leak() const { return *p; }      // const 멤버가 쓰기 가능한 참조를 내준다
    int  read() const { return own; }
};

int main() {
    int outside = 1;
    const Holder h(&outside);

    std::printf("전   : outside=%d h.own=%d\n", outside, h.own);
    h.poke();
    std::printf("poke : outside=%d   (h 는 const 인데 밖이 바뀌었다)\n", outside);
    h.leak() = 7;
    std::printf("leak : outside=%d   (const 멤버가 돌려준 참조로 썼다)\n", outside);
    std::printf("own  : %d           (이쪽은 정말 못 바꾼다)\n", h.read());
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
전   : outside=1 h.own=1
poke : outside=99   (h 는 const 인데 밖이 바뀌었다)
leak : outside=7   (const 멤버가 돌려준 참조로 썼다)
own  : 1           (이쪽은 정말 못 바꾼다)
```

**왜 그런가**

- ★★★ **`const Holder h` 가 지키는 것**은 「**`h` 의 비트**」다.\
  `h.p` 라는 **포인터 값**은 못 바꾸지만, **`*h.p`** 는 `h` 의 비트가 아니다.
- **`poke()` 안에서 `p` 의 타입은 `int* const`**(포인터가 const)이지 `const int*`(가리키는 것이 const)가 아니다.\
  그래서 `*p = 99` 가 **문법적으로 옳다.**
- ★★ **`leak()` 이 더 나쁘다** — `const` 멤버 함수가 **`int&`** 를 밖으로 내준다.\
  부르는 쪽은 `h` 가 `const` 라는 사실을 **알 수도 없다.**
- **`own` 은 안 바뀐다** — 값으로 든 멤버에는 `h` 의 `const` 가 그대로 간다.
- ★★★ **경고가 0건이다.** g++ 도 clang 도 이 자리에 아무 말을 하지 않는다 —\
  **막을 이유가 없기 때문**이다. 표준이 허용하는 코드다.
- **고치는 두 가지** —\
  ① `const` 멤버 함수가 **`const int&`** 를 돌려주게 한다(`leak()` 쪽).\
  ② 애초에 안 고칠 것이면 **멤버를 `const int*` 로** 든다(`poke()` 쪽까지 막힌다).

```text
   비트단위 const (컴파일러가 강제)        논리적 const (사람이 지킨다)
   +----------------------------+        +----------------------------+
   | h.own  = 1   못 바꾼다      |        | "h 가 뜻하는 상태"          |
   | h.p    = &outside 못 바꾼다 |        |   outside 도 그 일부라면     |
   +----------------------------+        |   const 가 깨진 것이다       |
             *h.p 는?  ★ 막지 않는다      +----------------------------+
```

### 4. ★★★ `k=10  *p=20  &k==p:1` — 네 판이 전부 같았다

**출력** — `-O0`

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**출력** — `-O2`

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**출력** — clang `-O2`

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**출력** — UBSan

```text
===== 소스: cnst04.cpp =====
// const_cast — 원래 const 인 것을 고치면 UB, 아니면 아니다
#include <cstdio>

int main() {
    const int k = 10;
    int* p = const_cast<int*>(&k);
    *p = 20;                                   // ★ 여기가 UB
    std::printf("[UB]    k=%d  *p=%d  &k==p:%d\n",
                k, *p, static_cast<int>(&k == p));

    int m = 30;                                // 원래 const 가 아니다
    const int& cr = m;
    const_cast<int&>(cr) = 40;                 // ★ UB 아님
    std::printf("[정상]  m=%d  cr=%d\n", m, cr);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined cnst04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[UB]    k=10  *p=20  &k==p:1
[정상]  m=40  cr=40
```

**왜 그런가**

- ★★★ **읽을 것은 값이 아니라 모순이다.** `&k == p` 가 **1**(같은 주소)인데\
  `k` 는 **10**, `*p` 는 **20** 이다. **둘 다 맞다고 우기는 상태**가 UB 의 모양이다.
- **컴파일러는 `k` 가 `const` 이므로 「10 이다」를 접어 둘 권리가 있다** — 그래서 `k` 를 읽는 자리에 **상수 10** 을 넣는다.\
  `*p` 는 포인터를 따라가므로 **실제로 써 놓은 20** 을 읽는다.
- ★★★ **`[정상]` 줄은 UB 가 아니다.** `m` 은 **원래 `const` 가 아니었고**, `cr` 이라는 **창만 `const`** 였다.\
  창을 걷어내고 쓰는 것은 **허용**이라 `m=40 cr=40` 으로 **한 값만** 답한다.
- ★★ **네 판이 전부 같았다** — 그렇다고 **「안전하다」는 결론은 못 낸다.**\
  UB 는 「**어떤 값이 나온다**」가 아니라 「**표준이 아무것도 약속하지 않는다**」이므로,\
  관찰이 몇 판 같아도 **다음 버전·다른 최적화·다른 주변 코드에서 갈린다.**\
  ★ 그래서 본문의 결론을 「**값이 갈린다**」가 아니라 「**같은 주소가 두 값을 답한다**」로 적었다.
- ★★★ **UBSan 이 한 줄도 안 낸다** — `run exit=0` 이다.\
  이 UB 는 **런타임 검사로 잡는 종류가 아니다**(쓰기 자체는 유효한 메모리로 간다).\
  **「sanitizer 가 조용하니 괜찮다」가 여기서 깨진다.**
- ★ `const_cast` 를 **언제 고르나**의 정본은 형제 [`03번`](../03-four-cast-operators/)이다.\
  여기서 얻을 규칙은 하나다 — **「원래 객체가 `const` 였나」를 먼저 답하고 나서 쓴다.**

### 5. ★★ `limit` 는 TU 마다 하나씩 — `nm` 에서 소문자 `r` 이다

**출력**

```text
===== 소스: cnst05a.cpp =====
// 번역 단위 A — 네임스페이스 스코프의 const 는 내부 링크다
const int limit = 10;              // 이 TU 만의 것
extern const int shared = 20;      // extern 을 붙이면 외부 링크

int from_a()        { return limit; }
int shared_from_a() { return shared; }
===== 소스: cnst05b.cpp =====
// 번역 단위 B — 같은 이름을 다시 정의해도 충돌하지 않는다
#include <cstdio>

const int limit = 99;              // A 의 limit 과 다른 물건
extern const int shared;           // A 의 것을 쓴다

int from_a();
int shared_from_a();

int main() {
    std::printf("limit  : B 에서 %d · A 에서 %d\n", limit, from_a());
    std::printf("shared : B 에서 %d · A 에서 %d\n", shared, shared_from_a());
    std::printf("&limit 를 비교할 수 있나 : 두 TU 의 limit 는 서로 다른 객체다\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -c cnst05a.cpp -o a.o && g++ -std=c++20 -Wall -Wextra -pedantic -c cnst05b.cpp -o b.o && g++ a.o b.o -o ex && ./ex (exit=0) =====
limit  : B 에서 99 · A 에서 10
shared : B 에서 20 · A 에서 20
&limit 를 비교할 수 있나 : 두 TU 의 limit 는 서로 다른 객체다
```

**심볼**

```text
===== 소스: cnst05a.cpp =====
// 번역 단위 A — 네임스페이스 스코프의 const 는 내부 링크다
const int limit = 10;              // 이 TU 만의 것
extern const int shared = 20;      // extern 을 붙이면 외부 링크

int from_a()        { return limit; }
int shared_from_a() { return shared; }
===== nm -C a.o; echo '--- b.o ---'; nm -C b.o (exit=0) =====
000000000000000f T shared_from_a()
0000000000000000 T from_a()
0000000000000000 r limit
0000000000000004 R shared
--- b.o ---
                 U shared_from_a()
                 U from_a()
0000000000000000 r limit
0000000000000000 T main
                 U printf
                 U puts
                 U shared
```

**왜 그런가**

- ★★★ **네임스페이스 스코프의 `const` 는 내부 링크**다. 그래서 두 파일에 같은 이름이 있어도 **충돌하지 않는다.**\
  `nm` 이 `r limit`(소문자 = local)로 답한 것이 그 증거다.
- **`shared` 는 `extern` 을 붙여 정의했으므로 외부 링크**다 — `a.o` 에서 `R shared`(대문자 = global),\
  `b.o` 에서 `U shared`(미정의)로 나오고 링커가 이어 준다.\
  그래서 양쪽이 **20** 을 본다.
- ★★ **`b.o` 에도 `r limit` 가 따로 있다** — 각자의 것이다. 출력이 「B 에서 99 · A 에서 10」인 이유다.
- ★ **헤더에 `const int N = 10;` 을 두고 열 파일에서 포함하면 객체가 열 개** 생긴다.\
  값이 같으니 대개 안 드러나지만 **주소를 비교하면 조용히 틀린다.**\
  ★ C++17 부터는 **`inline constexpr`** 로 하나로 만든다 — 정본은 목록의 **25번 주제**다.
- ★★ **C 는 반대다** — C 의 파일 스코프 `const` 는 **외부 링크**라 두 파일에 같은 이름을 두면 **링크 에러**가 난다.\
  링크 일반의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **29번**이다.

```text
   nm 의 심볼 문자 (이 문서가 근거로 쓰는 칸)

   r  읽기 전용 데이터 · ★ 소문자 = 내부 링크
   R  읽기 전용 데이터 · ★ 대문자 = 외부 링크
   T  코드(text)      · 대문자 = 외부 링크
   U  아직 없다 — 링커가 찾아야 한다
```

### 6. ★ `a=5 b=5 c=3  sizeof 둘 다 20` — `const` 도 배열 크기로 쓰인다

**출력**

```text
===== 소스: cnst06.cpp =====
// const 와 constexpr — 「못 바꾼다」와 「컴파일 때 안다」는 다르다
#include <cstdio>

int runtime() { return 3; }

int main() {
    const int     a = 5;          // 초기화식이 상수식이라 상수식으로도 쓰인다
    constexpr int b = 5;          // 상수식임을 강제한다
    const int     c = runtime();  // ★ const 는 런타임 값도 받는다

    int arr1[a]{};                // 된다
    int arr2[b]{};                // 된다
    static_assert(a == 5);
    static_assert(b == 5);

    std::printf("a=%d b=%d c=%d  sizeof(arr1)=%zu sizeof(arr2)=%zu\n",
                a, b, c, sizeof(arr1), sizeof(arr2));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst06.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a=5 b=5 c=3  sizeof(arr1)=20 sizeof(arr2)=20
```

**왜 그런가**

- ★★ **`const int a = 5;` 가 배열 크기로 쓰인 이유는 `const` 라서가 아니라 초기화식이 상수식이었기 때문**이다.\
  정수 타입 `const` 변수가 **상수식으로 초기화되면** 그 자체가 상수식이 된다.
- **`sizeof(arr1)` 과 `sizeof(arr2)` 가 둘 다 20** — `int` 5개다. `a` 와 `b` 가 같은 일을 했다.
- ★★★ **`const int c = runtime();` 은 컴파일된다.** `const` 는 「**못 고친다**」일 뿐이라 **런타임 값도 받는다.**\
  같은 자리에 `constexpr` 를 쓰면 에러다 — 7번의 (5)번 줄이 그것이다.
- ★ **한 문장으로** — 「**`const` 는 「못 고친다」, `constexpr` 는 「지금 안다」**」다.\
  `constexpr` 는 `const` 를 **포함**한다(변수에 쓸 때).
- ★ `constexpr`·`consteval`·`constinit` 자체의 정본은 목록의 **38번 주제**다.

### 7. ★★ 에러 일곱 — 일곱 가지가 전부 다른 이유다

**출력** — g++

```text
===== 소스: cnst08.cpp =====
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst08.cpp -o ex 2>&1 | grep 'error:' (cc exit=1) =====
cnst08.cpp:6:25: error: assignment of member ‘S::m’ in read-only object
cnst08.cpp:11:15: error: uninitialized ‘const x’ [-fpermissive]
cnst08.cpp:13:10: error: passing ‘const S’ as ‘this’ argument discards qualifiers [-fpermissive]
cnst08.cpp:14:14: error: invalid conversion from ‘const int*’ to ‘int*’ [-fpermissive]
cnst08.cpp:15:30: error: call to non-‘constexpr’ function ‘int runtime()’
cnst08.cpp:19:8: error: assignment of read-only variable ‘cp’
cnst08.cpp:21:9: error: assignment of read-only location ‘* pc’
```

**출력** — clang

```text
===== 소스: cnst08.cpp =====
// const 가 막는 일곱 — 전부 에러다
int runtime();

struct S {
    int m = 0;
    int bad() const { m = 1; return m; }   // (1) const 멤버가 멤버를 고친다
    void mut()      { ++m; }
};

int main() {
    const int x;                            // (2) 초기화 없는 const
    const S s;
    s.mut();                                // (3) const 객체로 비-const 멤버 호출
    int* p = &s.m;                          // (4) const 멤버의 주소를 int* 로
    constexpr int d = runtime();            // (5) constexpr 는 런타임 값을 못 받는다

    int i = 0, j = 0;
    int* const cp = &i;
    cp = &j;                                // (6) const 포인터를 다시 겨눈다
    const int* pc = &i;
    *pc = 1;                                // (7) 포인터-투-const 로 쓴다
    (void)x; (void)p; (void)d; (void)pc;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic cnst08.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
cnst08.cpp:6:25: error: cannot assign to non-static data member within const member function 'bad'
cnst08.cpp:11:15: error: default initialization of an object of const type 'const int'
cnst08.cpp:13:5: error: 'this' argument to member function 'mut' has type 'const S', but function is not marked const
cnst08.cpp:14:10: error: cannot initialize a variable of type 'int *' with an rvalue of type 'const int *'
cnst08.cpp:15:19: error: constexpr variable 'd' must be initialized by a constant expression
cnst08.cpp:19:8: error: cannot assign to variable 'cp' with const-qualified type 'int *const'
cnst08.cpp:21:9: error: read-only variable is not assignable
7 errors generated.
```

**왜 그런가**

| # | 줄 | 어긴 것 | g++ 문구의 핵심 |
|---|---|---|---|
| (1) | `m = 1;` in `bad() const` | **멤버 함수의 `const`** — `this` 가 `const S*` | `in read-only object` |
| (2) | `const int x;` | **나중에 못 고치므로** 지금 정해야 한다 | `uninitialized 'const x'` |
| (3) | `s.mut();` | **`const` 객체에 맞는 후보가 없다** | `discards qualifiers` |
| (4) | `int* p = &s.m;` | **`const` 를 버리는 암묵 변환은 없다** | `invalid conversion from 'const int*'` |
| (5) | `constexpr int d = runtime();` | ★ **`const` 가 아니라 `constexpr` 규칙** | `call to non-'constexpr' function` |
| (6) | `cp = &j;` | `int* const` — **포인터가** `const` | `read-only variable 'cp'` |
| (7) | `*pc = 1;` | `const int*` — **가리키는 것이** `const` | `read-only location '* pc'` |

- ★★ **(6)과 (7)이 가장 자주 헷갈리는 짝**이다. **`const` 가 `*` 의 왼쪽이면 가리키는 것, 오른쪽이면 포인터**다.\
  읽는 순서의 정본은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**이다.
- ★ **clang 도 일곱 개**다(`7 errors generated.`). **판정은 같고 문구만 다르다.**
- ★ **g++ 의 셋에 `[-fpermissive]` 가 붙어 있다**((2)·(3)·(4)) —\
  그 플래그로 **경고로 내려가는 진단**이라는 뜻이다.\
  ★★ 그 플래그가 실제로 무엇을 하는지의 실측은 목록의 **08번 주제**에 있다.

### 8. ★★★ `cc exit=0` · `run exit=139` — 빌드는 통과하고 실행이 죽는다

**출력** — `-pedantic`

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic cnst07.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
cnst07.cpp: In function ‘int main()’:
cnst07.cpp:6:15: warning: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    6 |     char* p = "abc";                            // ★ 여기
      |               ^~~~~
쓰기 전: p=abc
```

**출력** — `-pedantic-errors`

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic-errors cnst07.cpp -o ex (cc exit=1) =====
cnst07.cpp: In function ‘int main()’:
cnst07.cpp:6:15: error: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    6 |     char* p = "abc";                            // ★ 여기
      |               ^~~~~
```

**출력** — clang

```text
===== 소스: cnst07.cpp =====
// C++11 부터 ill-formed 인데 컴파일이 통과하는 줄
#include <cstdio>

int main() {
    std::setvbuf(stdout, nullptr, _IONBF, 0);   // 죽어도 출력이 안 사라지게
    char* p = "abc";                            // ★ 여기
    std::printf("쓰기 전: p=%s\n", p);
    p[0] = 'X';                                 // ★ 읽기 전용 구역에 쓴다 — UB
    std::printf("쓴 뒤  : p=%s\n", p);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic cnst07.cpp -o ex 2>&1 | grep -E 'warning:|generated' (cc exit=0) =====
cnst07.cpp:6:15: warning: ISO C++11 does not allow conversion from string literal to 'char *' [-Wwritable-strings]
1 warning generated.
```

**왜 그런가**

- ★★★ **`char* p = "abc";` 는 C++11부터 ill-formed** 다. 문자열 리터럴의 타입은 `const char[4]` 이고,\
  **`const` 를 버리는 암묵 변환이 없기 때문**이다(7번의 (4)와 같은 규칙).
- ★★★ **그런데 `cc exit=0`** 이다. g++ 는 `-Wwrite-strings` 경고 한 줄만 내고 **빌드를 성공시킨다.**\
  **`-pedantic-errors` 를 붙여야** 같은 진단이 `error:` 가 되고 **`cc exit=1`** 이 된다.
- ★★ **clang 도 같은 모양**이다 — 경고 이름만 `-Wwritable-strings` 로 다르고 **`cc exit=0`** 이다.\
  **컴파일러를 바꿔도 안 잡힌다.**
- **`p[0] = 'X';` 는 UB** 다 — 문자열 리터럴을 고치는 것이기 때문이다.\
  이 구현에서는 **읽기 금지 구역**에 놓여 `run exit=139` 로 죽었다.\
  ★ 「**죽는다**」는 **이 구현의 결과**이고, 표준이 정한 것은 「**수정이 UB**」까지다.
- ★★★ **`setvbuf(stdout, nullptr, _IONBF, 0)` 가 있는 이유** —\
  죽으면서 **버퍼에 남은 stdout 이 통째로 사라지기** 때문이다.\
  그 줄이 없으면 「쓰기 전: p=abc」가 **출력에서 없어진다** — 「돌려 봤다」를 지켜도 **재현이 안 되는** 블록이 된다.
- ★★ 그래서 **「`-std=c++20` 으로 돌렸다」는 「C++20 으로 검증했다」가 아니다.**\
  `-std=` 는 **기본값 선택**이고, 표준 준수를 주장하려면 **`-pedantic-errors`** 가 필요하다.
- ★ 이것이 이 갈래의 **고정 항목**이다 — 「**종료 코드가 0인데 ill-formed**」.

### 9. 어느 쪽을 쓸까

| 물음 | 답 | 근거 |
|---|---|---|
| 멤버 함수에 `const` 를 안 붙이면? | ★ **전염된다** — `const T&` 를 받는 함수 전체가 그 멤버를 못 쓴다 | 1번 |
| 캐시가 필요하다 | **그 멤버만 `mutable`** — `const_cast` 가 아니라 | 2번·4번 |
| 멤버에 포인터가 있다 | ★ **`const` 멤버는 `const T&` 를 돌려준다** · 안 고칠 것이면 멤버를 `const T*` 로 | 3번 |
| 헤더에 상수를 둔다 | **`inline constexpr`**(C++17\~) | 5번 |
| 옛 API 가 `const` 를 안 받는다 | ★ **「원래 객체가 `const` 인가」를 먼저 답한다** — `const` 였으면 `const_cast` 는 UB | 4번 |
| 컴파일 시간 값이 필요하다 | **`constexpr`** | 6번 |
| 값 매개변수 | ★ **선언에는 안 붙인다** — 복사본 이야기라 호출자와 무관하다 | — |

- ★★★ **한 문장** — 「**`const` 는 「이 경로로 안 고친다」는 계약이지 「아무도 안 고친다」는 보장이 아니다**」.\
  그 증거가 3번(포인터 멤버)과 4번(`const_cast`)이고, **둘 다 진단이 0건**이다.

### 10. 이 주제의 지도

- **`const_cast` 를 언제 고르나** — 형제 [`03번`](../03-four-cast-operators/)이 정본이다.\
  ★ 여기(4번)는 **그것이 UB 가 되는 경계**만 본다.
- **`const T&` 가 어떤 식들을 받나** — 목록의 **08번 주제**(값 범주)가 정본이다.\
  ★ `const T&` 는 **lvalue·const lvalue·prvalue·xvalue 넷을 다 받는 유일한 칸**이다.
- **`const` 객체를 `std::move` 하면** — 목록의 **09번 주제**가 정본이다.\
  ★ `const` 라서 `T&&` 오버로드로 못 가고 **조용히 복사**가 된다 — 08번의 오버로드 격자가 그 이유다.
- **매개변수를 무엇으로 받나** — 목록의 **11번 주제**가 정본이다.\
  ★ 여기서 얻은 것은 **계약 표기**까지이고, **크기·수명·소유권으로 고르는 것**은 거기다.
- **`const char*` / `char* const` 를 읽는 순서** — C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **31번**.\
  ★ 여기(7번)는 **에러 한 줄씩**으로 갈라 두는 데까지만 했다.
- **Rust 의 `&` 와 무엇이 다른가** — [`rust/syntax/10 — 빌림과 별칭 규칙`](../../../rust/syntax/10-borrowing-and-aliasing-rules/)이 정본이다.\
  ★ 한 문장으로 — 「**C++ 의 `const` 는 내가 안 고치겠다는 약속이고, Rust 의 `&` 는 아무도 안 고친다는 보장**」이다.\
  그 차이가 3번에서 그대로 나온다 — C++ 는 **아무 말도 안 한다.**

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `cnst01.cpp` const 오버로드 | `cb` 는 `const` 판 · `b` 는 비-const 판 · `sum` 14 → 15 | g++ |
| `cnst02.cpp` `mutable` | ★ `hits` **1·2·3** · `cached` -1 → 42 **한 번** | g++ (clang 으로도 같은 출력을 얻었으나 **블록으로 싣지 않았다**) |
| `cnst03.cpp` 논리적 const 구멍 | ★★★ `outside` **1 → 99 → 7** · `own` 그대로 · **경고 0건** | g++ |
| `cnst04.cpp` `const_cast` UB | ★★★ **`k=10 *p=20 &k==p:1`** — **네 판 전부 같음** | g++ `-O0` · g++ `-O2` · clang `-O2` · g++ `-fsanitize=undefined` |
| `cnst05a/b.cpp` 내부 링크 | ★ `limit` **99 대 10** · `shared` **양쪽 20** | g++ `-c` 둘 + 링크 |
| 〃 심볼 | ★★ **`r limit` · `R shared` · `U shared`** | `nm -C` |
| `cnst06.cpp` `const` 대 `constexpr` | `a=5 b=5 c=3` · `sizeof` **둘 다 20** | g++ |
| `cnst07.cpp` 리터럴 → `char*` | ★★★ **`cc exit=0` · `run exit=139`** · 경고 1 | g++ `-pedantic` |
| 〃 엄격 | ★★★ **`cc exit=1`** — 같은 진단이 `error:` 가 된다 | g++ `-pedantic-errors` |
| 〃 clang | ★ **`cc exit=0`** · `-Wwritable-strings` | clang `-pedantic` |
| `cnst08.cpp` 막히는 일곱 | ★ **g++ 에러 7 · clang 에러 7** | g++ · clang |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · binutils 2.42)에서만** 그렇다.

- ★ **`nm` 의 심볼 문자 표기**(`r`·`R`·`T`·`U`) — ELF 와 binutils 의 규약이다.\
  **「내부 링크다」가 언어 보장**이고, **「소문자 `r` 로 보인다」가 도구의 표기**다.
- ★★ **`cnst07.cpp` 가 `run exit=139` 로 죽는 것** — 문자열 리터럴을 **쓰기 금지 구역에 두는 것은 구현이 고른 것**이다.\
  표준이 정한 것은 「**수정이 UB**」까지다.
- ★ **`cnst04.cpp` 의 `k=10 *p=20`** — **UB 의 결과**라 보장이 아니다(아래 참조).
- 진단 문구 전부 · 경고 이름(`-Wwrite-strings` 대 `-Wwritable-strings`) · **에러를 몇 개로 세는가**.
- `cnst02.cpp` 의 `hits` 가 **정확히 1·2·3** 인 것은 보장이지만, **한 `printf` 안에 섞었을 때의 순서는 미명시**다(2번).

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **`const` 멤버 함수가 비-`mutable` 멤버를 못 고치는** 것.
- **`const` 객체로 비-const 멤버 함수를 못 부르는** 것 · **`const` 오버로드가 갈리는** 것.
- **`mutable` 멤버가 `const` 멤버 함수 안에서 바뀌는** 것.
- ★★ **`const` 가 포인터 멤버 너머를 안 막는** 것 — **막는 게 아니라 원래 범위 밖**이다.
- **`const T*` 에서 `T*` 로 가는 암묵 변환이 없는** 것.
- **네임스페이스 스코프 `const` 가 내부 링크인** 것 · **`extern` 이 그것을 외부 링크로 바꾸는** 것.
- **`const` 가 런타임 값을 받고 `constexpr` 는 못 받는** 것.
- ★ **원래 `const` 인 객체를 `const_cast` 로 고치면 UB** 인 것 · **문자열 리터럴 수정이 UB** 인 것.
- ★ **`char*` ← 문자열 리터럴이 C++11부터 ill-formed** 인 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★★★ 4번의 **`k=10  *p=20`** — **네 판이 같았다는 것은 관찰**이다.\
  근거로 쓰는 것은 「**`&k == p` 가 1 인데 두 값이 다르다**」는 **모순**이고,\
  「**어느 판에서도 10 과 20 이 나온다**」가 아니다.
- ★★ 8번의 **`run exit=139`** — SIGSEGV 로 죽은 것은 **이 구현의 결과**다.\
  근거로 쓰는 것은 「**컴파일은 통과했다**(`cc exit=0`)」쪽이다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **`volatile`**(C 갈래 목록의 **32번**이 정본) ·\
  **멤버 함수의 `&`·`&&` 한정자**(목록의 **08번 주제**에 `operator=` 쪽 실측이 있다) ·\
  **`std::as_const`·`const` 이터레이터**(목록의 **43번 주제**) ·\
  **`inline constexpr` 로 TU 당 하나로 만드는 것**(목록의 **25번 주제** — 5번은 `const` 쪽만 던졌다) ·\
  **`const` 멤버 함수 둘을 `const_cast` 로 합치는 관용구**(4번의 경계를 알았으니 쓸 수는 있다) ·\
  **`mutable` 을 여러 스레드에서 동시에 부르는 것**(2번은 단일 스레드다) ·\
  **`cnst03.cpp` 를 clang 으로**(g++ 만 던졌다 — 경고 0건이 컴파일러에 달린 값인지 확인하지 않았다).
- **못 잰 것** — ★ **「`const` 를 붙이면 최적화가 되나」를 수치로.**\
  `const` 는 **계약**이지 최적화 지시가 아니고, 4번이 보인 것은 「**`k` 를 상수로 접었다**」는 **한 사례**다.\
  **어떤 경우에 접히는지는 이 문서가 재지 않았다** — 벤치마크 하네스가 따로 필요하다.\
  ★ 이 문서는 그래서 **성능 수치를 하나도 적지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번의 네 판** — 최적화기가 바뀌면 **가장 먼저 움직이는 자리**다. UBSan 이 언젠가 이것을 잡을 수도 있다.
- ★★ **8번의 `cc exit`** — 컴파일러가 이 진단을 기본 에러로 올리면 **`cc exit=0` 이 1 로 바뀐다.**
- ★ **7번의 에러 개수**(g++ 7 · clang 7)와 **`[-fpermissive]` 가 붙는 줄들.**
- ★ **3번의 경고 0건** — 「`const` 멤버가 비-const 참조를 내준다」에 린트가 생길 수 있다.
