# cpp/syntax/03 — 캐스트 4종 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·에러·심볼은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **gcc 13.3.0**(C 대비) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 블록은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준 × 두 컴파일러로 돌렸다.**\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex` 이고 파일 이름은 **`ex.cpp`·`ex.c`** 뿐이다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다.\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 `capture.sh` 가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **오브젝트 파일의 미정의 심볼과 크기**(8번)다.
> **읽는 법** — UB 가 만든 값(`punned=1` · `k=7`)은 **근거로 쓰지 않는다.**\
> 근거로 쓰는 것은 「**갈렸다는 사실**」과 「**어느 플래그에서 갈렸나**」다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★ 여섯 줄 전부 통과 — `3.9` 는 **3** 으로 잘린다

**출력**

```text
===== 소스: ex.cpp =====
// static_cast 가 하는 일 — 「원래 되는 변환을 명시적으로 쓴다」
#include <cstdio>

enum class Color : unsigned char { Red, Green };
struct Base { int a = 1; };
struct Derived : Base { int b = 2; };

int main() {
    double d = 3.9;
    int    i = static_cast<int>(d);              // ① 산술 변환(절단)
    void*  v = &i;
    int*   p = static_cast<int*>(v);             // ② void* -> T*
    Derived der;
    Base*  up = static_cast<Base*>(&der);        // ③ 업캐스트
    Derived* down = static_cast<Derived*>(up);   // ④ 다운캐스트 — 검사는 없다
    int    n = static_cast<int>(Color::Green);   // ⑤ 범위 있는 열거형 -> 정수
    Color  c = static_cast<Color>(1);            // ⑥ 정수 -> 범위 있는 열거형
    std::printf("i=%d *p=%d up->a=%d down->b=%d n=%d c==Green:%d\n",
                i, *p, up->a, down->b, n,
                static_cast<int>(c == Color::Green));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
i=3 *p=3 up->a=1 down->b=2 n=1 c==Green:1
```

**왜 그런가**

| 쓰임 | 결과 | 이름 |
|---|---|---|
| `static_cast<int>(3.9)` | **3** | **절단**(truncation). 반올림이 아니다 |
| `static_cast<int*>(v)` | `*p=3` | `void*` → `T*`. C 에서는 캐스트조차 필요 없던 자리 |
| `static_cast<Base*>(&der)` | `up->a=1` | 업캐스트. 암묵으로도 된다 |
| `static_cast<Derived*>(up)` | `down->b=2` | 다운캐스트 |
| `static_cast<int>(Color::Green)` | `n=1` | 열거형 → 정수 |
| `static_cast<Color>(1)` | `c==Green:1` | 정수 → 열거형 |

- **절단**이다 — 어셈블리 수준 근거(`cvttsd2si` 의 `tt` 가 truncate toward zero)는\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)에 있다.
- ★★ **④에서 컴파일러가 확인하는 것은 「계통이 맞는가」뿐**이다.\
  `Derived` 가 `Base` 에서 파생됐는지만 보고, **그 포인터가 실제로 `Derived` 를 가리키는지는 안 본다.**\
  여기서는 진짜 `Derived` 였으니 맞았을 뿐이다 — 9번에서 **틀린 경우**를 본다.
- **⑤⑥이 없으면 컴파일이 안 된다.** `enum class` 가 정수와의 **암묵 변환을 끊어** 두었기 때문이고,\
  정본은 [**02번 형제**](../02-enum-class-and-scoped-enumerations/)의 「담장 ②」다.

### 2. ★★ 에러 **셋** — 그리고 그 셋이 나머지 도구의 일자리다

**출력 — g++**

```text
===== 소스: ex.cpp =====
// static_cast 가 거부하는 셋 — 그 셋이 나머지 세 캐스트의 일자리다
struct Base { int a = 1; };
struct Hidden : private Base { int b = 2; };   // private 상속

int main() {
    const int k = 7;
    int* p = static_cast<int*>(&k);            // ① const 를 떼는 일

    Hidden h;
    Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로

    double d = 1.0;
    int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로

    (void)p; (void)q; (void)r;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:7:14: error: invalid ‘static_cast’ from type ‘const int*’ to type ‘int*’
    7 |     int* p = static_cast<int*>(&k);            // ① const 를 떼는 일
      |              ^~~~~~~~~~~~~~~~~~~~~
ex.cpp:10:36: error: ‘Base’ is an inaccessible base of ‘Hidden’
   10 |     Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로
      |                                    ^
ex.cpp:13:14: error: invalid ‘static_cast’ from type ‘double*’ to type ‘int*’
   13 |     int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로
      |              ^~~~~~~~~~~~~~~~~~~~~
```

**출력 — clang**

```text
===== 소스: ex.cpp =====
// static_cast 가 거부하는 셋 — 그 셋이 나머지 세 캐스트의 일자리다
struct Base { int a = 1; };
struct Hidden : private Base { int b = 2; };   // private 상속

int main() {
    const int k = 7;
    int* p = static_cast<int*>(&k);            // ① const 를 떼는 일

    Hidden h;
    Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로

    double d = 1.0;
    int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로

    (void)p; (void)q; (void)r;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:7:14: error: static_cast from 'const int *' to 'int *' is not allowed
    7 |     int* p = static_cast<int*>(&k);            // ① const 를 떼는 일
      |              ^~~~~~~~~~~~~~~~~~~~~
ex.cpp:10:34: error: cannot cast 'Hidden' to its private base class 'Base'
   10 |     Base* q = static_cast<Base*>(&h);          // ② 접근할 수 없는 기반으로
      |                                  ^
ex.cpp:3:17: note: declared private here
    3 | struct Hidden : private Base { int b = 2; };   // private 상속
      |                 ^~~~~~~~~~~~
ex.cpp:13:14: error: static_cast from 'double *' to 'int *' is not allowed
   13 |     int* r = static_cast<int*>(&d);            // ③ 무관한 포인터 타입으로
      |              ^~~~~~~~~~~~~~~~~~~~~
3 errors generated.
```

**왜 그런가**

| 거부된 것 | 누구의 일자리 | g++ 문구 |
|---|---|---|
| `const int*` → `int*` | **`const_cast`** | `invalid 'static_cast' from type 'const int*' to type 'int*'` |
| `Hidden*` → `Base*`(private) | **`reinterpret_cast`** 또는 설계 수정 | `'Base' is an inaccessible base of 'Hidden'` |
| `double*` → `int*` | **`reinterpret_cast`** | `invalid 'static_cast' from type 'double*' to type 'int*'` |

- **clang 이 한 줄 더 말해 주는 곳은 ②**다 — `note: declared private here` 가\
  **상속 선언 줄을 직접 짚는다.** g++ 는 그 줄을 안 짚는다.\
  ★ clang 은 `3 errors generated.` 꼬리도 붙인다.
- **이 셋에 `dynamic_cast` 가 답인 자리는 없다.** `dynamic_cast` 는\
  「`static_cast` 가 거부해서」 쓰는 것이 아니라 **「`static_cast` 로도 되지만 검사가 필요해서」** 쓰는 것이다.

### 3. ★★★ 같은 객체가 **두 값**으로 읽힌다 — 그리고 열 벌이 전부 같았다

**출력 — g++ `-O0`**

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

**출력 — clang++ `-O2`**

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

**출력 — sanitizer(대표 한 벌)**

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -fsanitize=undefined,address ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

**왜 그런가**

- ★★★ **한 `fprintf` 안에서 `k=7` 인데 `*p=99` 이고 `read_through(&k)=99`** 다.\
  같은 객체를 이름으로 읽으면 7, 포인터로 읽으면 99 다 — **UB 의 모양이 이렇게 생겼다.**
- **다섯 수준 × 두 컴파일러 = 열 벌이 전부 같았다.**

| 명령 | 출력 |
|---|---|
| g++ `-O0` / `-O1` / `-O2` / `-O3` / `-Os` | `k=7  *p=99  read_through(&k)=99` |
| clang++ `-O0` / `-O1` / `-O2` / `-O3` / `-Os` | 〃 |

  ★★ **「최적화 수준을 올려야 드러난다」가 C++ 에서는 틀리다.** `-O0` 에서부터 드러난다.\
  이유는 4번에 있다.
- **UBSan·ASan 은 0줄**이다. `-O0 -fsanitize=undefined` · `-O0 -fsanitize=address` ·\
  `-O2 -fsanitize=undefined,address` · clang UBSan 네 벌 전부 **진단 없이 같은 값**을 냈다.
- **`-Wcast-qual` 도 0건**이다.

```text
===== 소스: ex.cpp =====
// const_cast 로 「진짜 const 객체」를 고치면 — 한 printf 안에서 값이 둘로 갈린다
#include <cstdio>

int read_through(const int* q) { return *q; }   // 밖에서 다시 읽어 본다

int main() {
    const int k = 7;
    int* p = const_cast<int*>(&k);
    *p = 99;
    std::fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
                 k, *p, read_through(&k));
}
===== for F in "-Wall -Wextra" "-Wall -Wextra -pedantic" "-Wcast-qual" "-Wall -Wextra -Wcast-qual"; do printf "[%-26s] warning: %s 건  cc exit=" "$F" "$(g++ -std=c++20 -O2 $F ex.cpp -o ex 2>&1 | grep -c "warning:")"; g++ -std=c++20 -O2 $F ex.cpp -o ex >/dev/null 2>&1; echo $?; done (exit=0) =====
[-Wall -Wextra             ] warning: 0 건  cc exit=0
[-Wall -Wextra -pedantic   ] warning: 0 건  cc exit=0
[-Wcast-qual               ] warning: 0 건  cc exit=0
[-Wall -Wextra -Wcast-qual ] warning: 0 건  cc exit=0
```

  ★ **`const_cast` 는 「일부러 벗긴다」는 선언**이라 `-Wcast-qual` 이 말하지 않는다.\
  그 플래그는 **C 스타일로 몰래 벗길 때** 쓰는 것이다.
- **원래 객체가 `const` 가 아니면 결과가 달라진다** — 그때는 **정의된 동작**이고 `k=99` 다.

```text
===== 소스: ex.cpp =====
// const 를 떼고 써도 「정의된」 자리 — 원래 객체가 const 가 아니면 된다
#include <cstdio>

void write_through(const int* cp) { *const_cast<int*>(cp) = 99; }

int main() {
    int k = 7;                     // 원래 객체가 const 가 아니다
    write_through(&k);
    std::fprintf(stderr, "k=%d\n", k);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99
```

```text
===== 소스: ex.cpp =====
// const 를 떼고 써도 「정의된」 자리 — 원래 객체가 const 가 아니면 된다
#include <cstdio>

void write_through(const int* cp) { *const_cast<int*>(cp) = 99; }

int main() {
    int k = 7;                     // 원래 객체가 const 가 아니다
    write_through(&k);
    std::fprintf(stderr, "k=%d\n", k);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99
```

  ★★ **가르는 것**은 포인터의 타입이 아니라 「**원래 객체가 무엇으로 선언됐나**」다.\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이 C 에서 같은 결론을 냈다.

### 4. ★★★ **`gcc -O0` 만 다르다** — 경계선이 C 쪽에 있다

**출력 — `gcc -O0`**

```text
===== 소스: ex.c =====
/* 같은 코드를 C 로 — 원래 객체가 const 일 때 C 와 C++ 이 갈리는 자리 */
#include <stdio.h>

int read_through(const int *q) { return *q; }

int main(void) {
    const int k = 7;
    int *p = (int *)&k;
    *p = 99;
    fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
            k, *p, read_through(&k));
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 ex.c -o ex && ./ex (cc exit=0 · run exit=0) =====
k=99  *p=99  read_through(&k)=99
```

**출력 — `gcc -O1`**

```text
===== 소스: ex.c =====
/* 같은 코드를 C 로 — 원래 객체가 const 일 때 C 와 C++ 이 갈리는 자리 */
#include <stdio.h>

int read_through(const int *q) { return *q; }

int main(void) {
    const int k = 7;
    int *p = (int *)&k;
    *p = 99;
    fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
            k, *p, read_through(&k));
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 ex.c -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

**출력 — `gcc -O2`**

```text
===== 소스: ex.c =====
/* 같은 코드를 C 로 — 원래 객체가 const 일 때 C 와 C++ 이 갈리는 자리 */
#include <stdio.h>

int read_through(const int *q) { return *q; }

int main(void) {
    const int k = 7;
    int *p = (int *)&k;
    *p = 99;
    fprintf(stderr, "k=%d  *p=%d  read_through(&k)=%d\n",
            k, *p, read_through(&k));
    return 0;
}
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 ex.c -o ex && ./ex (cc exit=0 · run exit=0) =====
k=7  *p=99  read_through(&k)=99
```

**왜 그런가**

- **`gcc -O0` 은 `k=99`** 다. 3번의 `g++ -O0`(`k=7`)과 **다르다.**
- **`gcc -O1` 부터 `k=7`** 이 된다. ★ 경계선이 **C 쪽에만** 있다 —\
  C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)이\
  「**경계선이 `-O2` 가 아니라 `-O1`**」이라고 실측해 둔 그 자리다.
- **C++ 에는 경계선이 없다.** 다섯 수준 전부 `k=7` 이다.
- ★★★ **갈리는 이유는 최적화가 아니라 「상수식」이라는 낱말**이다.\
  C++ 에서 `const int k = 7;` 은 **상수식**이고, 이름 `k` 가 쓰인 자리는\
  **어느 최적화 수준에서도 값 7 로 접힌다.** C 의 `const int` 는 그런 것이 아니라\
  「쓰면 안 되는 변수」일 뿐이므로 `-O0` 에서는 메모리를 다시 읽는다.
- ★★ **이 자리를 잡아 준 것**은 「다섯 최적화 수준」이 아니라 「**같은 코드를 두 언어로 던진 것**」이다.\
  다섯 수준만 돌렸으면 C++ 쪽에서 「아무 데서도 안 갈린다」만 얻고 **왜인지는 못 얻었다.**

### 5. ★★★ 경계선은 **`-O1`** — 그리고 도구가 아무것도 안 말한다

**출력 — g++ `-O0 -fstrict-aliasing`**

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fstrict-aliasing ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1073741824
```

**출력 — g++ `-O1 -fstrict-aliasing`**

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O1 -fstrict-aliasing ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1
```

**출력 — clang++ `-O2`**

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1
```

**출력 — sanitizer 둘 다**

```text
===== 소스: ex.cpp =====
// reinterpret_cast 와 엄격한 앨리어싱 — 최적화가 답을 바꾸는 자리
#include <cstdio>

int punned(int* pi, float* pf) {   // 컴파일러는 이 둘이 겹칠 수 없다고 가정한다
    *pi = 1;
    *pf = 2.0f;
    return *pi;
}

int main() {
    int x = 0;
    int r = punned(&x, reinterpret_cast<float*>(&x));
    std::fprintf(stderr, "punned=%d\n", r);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -fsanitize=undefined,address ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
punned=1
```

**왜 그런가**

| 최적화 | g++ `-fstrict-aliasing` | g++ `-fno-strict-aliasing` |
|---|---|---|
| `-O0` | `1073741824` | `1073741824` |
| **`-O1`** | ★ **`1`** | `1073741824` |
| `-O2` | `1` | `1073741824` |
| `-O3` | `1` | `1073741824` |
| `-Os` | `1` | `1073741824` |

- **`-O0` 과 `-O2` 의 출력이 다르다.** 경계선은 **`-O1`** 이다.
- **`-fno-strict-aliasing` 을 주면 다섯 수준 전부 `1073741824`** 다 — 그 플래그가 **가정을 끈다.**
- **clang 의 경계선은 `-O2`** 였다(`-O0` 은 `1073741824`, `-O2` 는 `1`).\
  ★ **경계선이 컴파일러마다 다르다.** 그리고 C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)은\
  **다른 소스 모양에서 gcc 의 경계를 `-O2`** 로 실측했다 —\
  ★★ **「경계는 `-O2` 다」를 규칙으로 외우면 틀린다. 소스 모양이 바꾼다.**
- **`-Wall -Wextra -pedantic` 은 0건**이고 **UBSan·ASan 도 0줄**이다.\
  ★★ **이 문서에서 도구가 가장 못 보는 UB 다.** C 편의 결론과 같다.\
  ★ 여기서 경고가 0건인 이유는 **캐스트를 함수 인자로 넘겼기** 때문이다 —\
  같은 위반을 **그 자리에서 역참조**하면 g++ 가 말한다(10번).

### 6. ★★ `4Left` · `非null` · `nullptr` · `std::bad_cast`

**출력**

```text
===== 소스: ex.cpp =====
// dynamic_cast 넷 — 포인터는 nullptr, 참조는 bad_cast
#include <cstdio>
#include <typeinfo>

struct Base  { virtual ~Base() = default; };
struct Left  : Base { int l = 10; };
struct Right : Base { int r = 20; };

int main() {
    Base* b = new Left;                            // 실제로는 Left 다
    std::printf("typeid(*b).name() = %s\n", typeid(*b).name());
    std::printf("typeid(*b) == typeid(Left) : %d\n",
                static_cast<int>(typeid(*b) == typeid(Left)));
    std::printf("dynamic_cast<Left*>  : %s\n",
                dynamic_cast<Left*>(b)  ? "非null" : "nullptr");
    std::printf("dynamic_cast<Right*> : %s\n",
                dynamic_cast<Right*>(b) ? "非null" : "nullptr");
    try {
        Right& r = dynamic_cast<Right&>(*b);
        (void)r;
    } catch (const std::bad_cast& e) {
        std::printf("참조 판은 예외 — what() = %s\n", e.what());
    }
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
typeid(*b).name() = 4Left
typeid(*b) == typeid(Left) : 1
dynamic_cast<Left*>  : 非null
dynamic_cast<Right*> : nullptr
참조 판은 예외 — what() = std::bad_cast
```

**왜 그런가**

- **`typeid(*b).name()` 은 `4Left`** 다. **맹글링된 이름**이고 `4` 는 `Left` 의 글자 수다.\
  ★ **이 철자는 플랫폼의 C++ ABI 가 정한다** — 표준은 「사람이 읽을 이름」을 보장하지 않는다.\
  사람이 읽을 이름이 필요하면 `abi::__cxa_demangle`(gcc·clang 확장)을 따로 쓴다.
- **맞는 파생으로는 `非null`**, **틀린 파생으로는 `nullptr`** 이다.\
  ★ 포인터 판의 계약이 「실패하면 `nullptr`」이고, 그래서 **`if (auto* p = dynamic_cast<T*>(b))`** 관용구가 성립한다.
- **참조 판은 `std::bad_cast` 를 던진다.** 참조에는 「null 참조」가 없으므로 **예외 말고 방법이 없다.**\
  `what()` 은 `std::bad_cast` 다.
- ★★ **`typeid` 비교와 `dynamic_cast` 는 다른 질문이다.**\
  `typeid(*b) == typeid(Left)` 는 「**정확히 `Left` 인가**」,\
  `dynamic_cast<Left*>(b)` 는 「**`Left` 이거나 그 파생인가**」를 묻는다.\
  `Left` 를 상속한 `SubLeft` 객체라면 **앞은 거짓, 뒤는 참**이다.

### 7. 가상 함수 하나와 RTTI — 둘 다 없으면 **컴파일이 안 된다**

**출력 — 비다형 타입 (g++)**

```text
===== 소스: ex.cpp =====
// dynamic_cast 는 다형 타입에만 쓴다 — 가상 함수가 하나도 없으면
struct Plain  { int y = 1; };
struct PlainD : Plain { int z = 2; };

int main() {
    Plain p;
    PlainD* d = dynamic_cast<PlainD*>(&p);
    return d ? 1 : 0;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:7:17: error: cannot ‘dynamic_cast’ ‘& p’ (of type ‘struct Plain*’) to type ‘struct PlainD*’ (source type is not polymorphic)
    7 |     PlainD* d = dynamic_cast<PlainD*>(&p);
      |                 ^~~~~~~~~~~~~~~~~~~~~~~~~
```

**출력 — 비다형 타입 (clang)**

```text
===== 소스: ex.cpp =====
// dynamic_cast 는 다형 타입에만 쓴다 — 가상 함수가 하나도 없으면
struct Plain  { int y = 1; };
struct PlainD : Plain { int z = 2; };

int main() {
    Plain p;
    PlainD* d = dynamic_cast<PlainD*>(&p);
    return d ? 1 : 0;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex (cc exit=1) =====
ex.cpp:7:17: error: 'Plain' is not polymorphic
    7 |     PlainD* d = dynamic_cast<PlainD*>(&p);
      |                 ^                     ~~
1 error generated.
```

**출력 — `-fno-rtti` (g++)**

```text
===== 소스: ex.cpp =====
// dynamic_cast 와 typeid 는 RTTI 위에 서 있다 — -fno-rtti 로 던져 본다
#include <cstdio>
#include <typeinfo>

struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

int main() {
    Base* b = new Derived;
    std::printf("%s\n", typeid(*b).name());
    Derived* d = dynamic_cast<Derived*>(b);
    std::printf("%s\n", d ? "非null" : "nullptr");
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -fno-rtti ex.cpp -o ex (cc exit=1) =====
ex.cpp: In function ‘int main()’:
ex.cpp:10:33: error: cannot use ‘typeid’ with ‘-fno-rtti’
   10 |     std::printf("%s\n", typeid(*b).name());
      |                                 ^
ex.cpp:11:18: error: ‘dynamic_cast’ not permitted with ‘-fno-rtti’
   11 |     Derived* d = dynamic_cast<Derived*>(b);
      |                  ^~~~~~~~~~~~~~~~~~~~~~~~~
```

**출력 — `-fno-rtti` (clang)**

```text
===== 소스: ex.cpp =====
// dynamic_cast 와 typeid 는 RTTI 위에 서 있다 — -fno-rtti 로 던져 본다
#include <cstdio>
#include <typeinfo>

struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

int main() {
    Base* b = new Derived;
    std::printf("%s\n", typeid(*b).name());
    Derived* d = dynamic_cast<Derived*>(b);
    std::printf("%s\n", d ? "非null" : "nullptr");
    delete b;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fno-rtti ex.cpp -o ex (cc exit=1) =====
ex.cpp:10:25: error: use of typeid requires -frtti
   10 |     std::printf("%s\n", typeid(*b).name());
      |                         ^
ex.cpp:11:18: error: use of dynamic_cast requires -frtti
   11 |     Derived* d = dynamic_cast<Derived*>(b);
      |                  ^
2 errors generated.
```

**왜 그런가**

- **가상 함수가 없으면** — g++ 는 `(source type is not polymorphic)`,\
  clang 은 `'Plain' is not polymorphic`. ★ **둘 다 「다형적이지 않다」는 낱말을 쓴다.**\
  `dynamic_cast` 는 **vtable 을 타고** 타입 정보에 닿는데, vtable 이 없으면 물어볼 곳이 없다.
- **`-fno-rtti` 에서는 `dynamic_cast` 와 `typeid` 가 함께** 막힌다 —\
  ★★ **둘이 같은 장치 위에 서 있다**는 증거다.
- **에러 개수가 다르다** — g++ 는 **4줄**(`typeid` 1 + `dynamic_cast` 3),\
  clang 은 **2줄**(종류당 1개로 묶는다) + `2 errors generated.`.\
  ★ **「에러가 몇 개냐」는 컴파일러의 세는 방식이지 문제의 개수가 아니다.**
- **`-fno-rtti` 가 흔한 곳** — 임베디드·게임 엔진처럼 바이너리 크기와 결정성이 중요한 현장이다.\
  거기서는 **가상 함수로 풀거나**([목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)), **태그 필드**·**`std::variant`**(목록의 **47번 주제**)로 대신한다.

### 8. `static_cast` 판은 **미정의 심볼이 0개**, `dynamic_cast` 판은 **셋**

**출력 — `static_cast` 판**

```text
===== 소스: ex.cpp =====
// 같은 함수를 두 캐스트로 — 오브젝트 파일이 값을 말한다
struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

#ifdef USE_DYNAMIC
Derived* down(Base* b) { return dynamic_cast<Derived*>(b); }
#else
Derived* down(Base* b) { return static_cast<Derived*>(b); }
#endif
===== g++ -std=c++20 -Wall -Wextra -pedantic -c ex.cpp -o ex.o && nm -uC ex.o; echo '오브젝트 크기:' $(wc -c < ex.o) '바이트' (cc exit=0 · run exit=0) =====
오브젝트 크기: 1232 바이트
```

**출력 — `dynamic_cast` 판**

```text
===== 소스: ex.cpp =====
// 같은 함수를 두 캐스트로 — 오브젝트 파일이 값을 말한다
struct Base    { virtual ~Base() = default; };
struct Derived : Base {};

#ifdef USE_DYNAMIC
Derived* down(Base* b) { return dynamic_cast<Derived*>(b); }
#else
Derived* down(Base* b) { return static_cast<Derived*>(b); }
#endif
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_DYNAMIC -c ex.cpp -o ex.o && nm -uC ex.o; echo '오브젝트 크기:' $(wc -c < ex.o) '바이트' (cc exit=0 · run exit=0) =====
                 U vtable for __cxxabiv1::__class_type_info
                 U vtable for __cxxabiv1::__si_class_type_info
                 U __dynamic_cast
오브젝트 크기: 2704 바이트
```

**왜 그런가**

- **`static_cast` 판의 미정의 심볼은 0개**다. `nm -uC` 가 아무것도 안 찍는다 —\
  **컴파일 시간에 끝났다**는 뜻이다.
- **`dynamic_cast` 판에는 셋**이 생긴다 —\
  `__dynamic_cast`(런타임 함수) · `vtable for __cxxabiv1::__class_type_info` ·\
  `vtable for __cxxabiv1::__si_class_type_info`(타입 정보 객체).
- **오브젝트 크기가 1232 → 2704 바이트**다. 함수 몸통 한 줄 차이인데 **2배 이상**이다.
- ★★ **이 창과 7번의 `-fno-rtti` 에러는 같은 사실의 양면**이다 —\
  여기서는 **있는 것을 보여 주고**, 거기서는 **없앴더니 비명을 듣는다.**\
  둘 다 「`dynamic_cast` 는 런타임 장치를 쓴다」를 말한다.
- ★ 크기 숫자는 **같은 컴파일러·플래그에서 결정적**이라 근거로 쓸 수 있다.\
  다만 **컴파일러가 바뀌면 달라지는 구현 값**이다.

### 9. 다섯 단계 — 그리고 그 줄에 `dynamic_cast` 는 없다

**출력 — (2)의 셋을 `(T)x` 로 던지면**

```text
===== 소스: ex.cpp =====
// C 스타일 캐스트는 무엇으로 풀리나 — static_cast 가 거부한 셋을 그대로 던진다
#include <cstdio>

struct Base   { int a = 1; };
struct Hidden : private Base { int b = 2; };

int main() {
    const int k = 7;
    int* p = (int*)&k;          // -> const_cast
    Hidden h;
    Base* q = (Base*)&h;        // -> reinterpret_cast (static_cast 는 접근 불가)
    double d = 1.0;
    int* r = (int*)&d;          // -> reinterpret_cast
    std::printf("*p=%d q->a=%d r!=nullptr:%d\n", *p, q->a, static_cast<int>(r != nullptr));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
*p=7 q->a=1 r!=nullptr:1
```

**출력 — 다운캐스트 세 벌**

```text
===== 소스: ex.cpp =====
// C 스타일 캐스트가 절대 되지 못하는 하나 — dynamic_cast
#include <cstdio>

struct Base  { virtual ~Base() = default; int a = 1; };
struct Left  : Base { int l = 10; };
struct Right : Base { int r = 20; };

int main() {
    Base* b = new Left;                              // 실제로는 Left 다
    Right* by_c       = (Right*)b;                   // 검사 없음
    Right* by_static  = static_cast<Right*>(b);      // 검사 없음
    Right* by_dynamic = dynamic_cast<Right*>(b);     // 검사한다
    std::printf("(Right*)b=%s  static_cast=%s  dynamic_cast=%s\n",
        by_c       ? "非null" : "nullptr",
        by_static  ? "非null" : "nullptr",
        by_dynamic ? "非null" : "nullptr");
    std::printf("by_c->r 을 읽으면: %d\n", by_c->r);
    delete b;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(Right*)b=非null  static_cast=非null  dynamic_cast=nullptr
by_c->r 을 읽으면: 10
```

**왜 그런가**

```text
   (T)x 를 만나면 컴파일러가 차례로 시도한다

   1. const_cast<T>(x)
   2. static_cast<T>(x)
   3. static_cast<T>(...) 한 뒤 const_cast<T>(...)
   4. reinterpret_cast<T>(x)
   5. reinterpret_cast<T>(...) 한 뒤 const_cast<T>(...)

   ★ 이 줄에 dynamic_cast 는 없다.
```

- **그 줄에 없는 캐스트는 `dynamic_cast`** 다. **괄호로는 검사를 살 수 없다.**
- **(2)의 셋은 전부 통과한다** — `(int*)&k` 는 **1번**, `(Base*)&h` 와 `(int*)&d` 는 **4번**으로 풀린다.\
  ★ `(Base*)&h` 가 **`reinterpret_cast` 로 풀린다**는 것이 위험한 대목이다 —\
  다중 상속의 업캐스트는 **주소 보정**이 필요한데 `reinterpret_cast` 는 비트를 그대로 둔다.
- **`(Right*)b` 로 다운캐스트하면 `非null`** 이고 `static_cast` 도 마찬가지다.\
  **`dynamic_cast` 만 `nullptr`** 을 준다 — 객체는 실제로 `Left` 이므로 그쪽이 맞다.
- ★★★ **`by_c->r` 을 읽으면 `10` 이 나온다.** 그 자리에 있는 것은 `Left::l` 이다.\
  **UB 이고, 컴파일러도 sanitizer 도 아무 말을 안 한다.**\
  ★ 「**값이 나왔으니 맞다**」가 이 주제에서 가장 위험한 추론이다.

### 10. 값은 같고, **UB 인 것은 하나**다

**출력 — 세 방법**

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 -w ex.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
reinterpret=1078523331 memcpy=1078523331 bit_cast=1078523331
```

**출력 — g++ `-O2` 의 경고**

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex (cc exit=0) =====
ex.cpp: In function ‘int main()’:
ex.cpp:8:14: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
    8 |     int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
      |              ^~~~~~~~~~~~~~~~~~~~~~~~~~
ex.cpp:8:9: warning: ‘f’ is used uninitialized [-Wuninitialized]
    8 |     int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
      |         ^
ex.cpp:7:11: note: ‘f’ declared here
    7 |     float f = 3.14f;
      |           ^
```

**출력 — g++ `-O0`**

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 ex.cpp -o ex (cc exit=0) =====
```

**출력 — clang++ `-O2`**

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic -O2 ex.cpp -o ex (cc exit=0) =====
```

**출력 — 플래그별로 세기**

```text
===== 소스: ex.cpp =====
// 비트를 그대로 읽는 세 방법 — 값은 같고 「합법인가」가 다르다
#include <cstdio>
#include <cstring>
#include <bit>

int main() {
    float f = 3.14f;
    int a = *reinterpret_cast<int*>(&f);                 // UB (엄격한 앨리어싱 위반)
    int b; std::memcpy(&b, &f, sizeof b);                // 정의됨
    int c = std::bit_cast<int>(f);                       // 정의됨 (C++20)
    std::fprintf(stderr, "reinterpret=%d memcpy=%d bit_cast=%d\n", a, b, c);
}
===== for F in "-Wall -Wextra" "-Wstrict-aliasing=1" "-Wstrict-aliasing=2" "-Wstrict-aliasing=3"; do printf "[%-22s] warning: %s 건  cc exit=" "$F" "$(g++ -std=c++20 -O2 $F ex.cpp -o ex 2>&1 | grep -c "warning:")"; g++ -std=c++20 -O2 $F ex.cpp -o ex >/dev/null 2>&1; echo $?; done (exit=0) =====
[-Wall -Wextra         ] warning: 2 건  cc exit=0
[-Wstrict-aliasing=1   ] warning: 1 건  cc exit=0
[-Wstrict-aliasing=2   ] warning: 1 건  cc exit=0
[-Wstrict-aliasing=3   ] warning: 1 건  cc exit=0
```

**왜 그런가**

- **셋이 같은 값**(`1078523331`)이다. ★ **값이 같은 것이 합법성을 말해 주지 않는다.**
- **UB 인 것은 `*reinterpret_cast<int*>(&f)` 하나**다.\
  `memcpy` 와 **`std::bit_cast`(C++20)** 는 정의된다.
- ★★★ **두 번째 경고가 교재다** — `'f' is used uninitialized`.\
  `f` 는 **바로 윗줄에서 `3.14f` 로 초기화**됐다. 그런데 컴파일러가\
  「그 대입은 이 `int` 읽기에 닿을 수 없다」고 판단했고, **그 판단의 근거가 엄격한 앨리어싱 가정**이다.\
  ★ **경고가 가정을 자백한다** — 「나는 이 둘이 같은 메모리일 리 없다고 가정했다」.
- **`-O0` 은 0건**이다. 최적화기가 봐야 보이는 경고다.
- **clang `-O2` 는 같은 플래그로 0건**이다. ★ **「경고가 없으니 괜찮다」가 컴파일러에 달렸다.**
- **`-Wstrict-aliasing=3` 은 1건**이다. C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)은\
  같은 플래그로 **0건**인 소스를 실측했다 —\
  ★★ **같은 플래그가 소스 모양에 따라 다르게 답한다.** 「`-Wall` 의 기본 수준 3은 못 잡는다」를 **규칙으로 외우면 틀린다.**
- ★ 여기서 `-Wall -Wextra` 가 **2건**인 것은 `-Wstrict-aliasing` 1 + `-Wuninitialized` 1 이다.

### 11. 이 주제의 지도

**왜 그런가**

- **실행 시간 비용이 있는 것은 `dynamic_cast`** 하나다. 밑에 깔린 장치는 **vtable 과 RTTI** 이고,\
  vtable 의 정본은 [목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)(상속·가상 함수)다.
- **`const_cast` 를 안 쓰게 만드는 설계**는 [목록의 **10번 주제**](../10-const-correctness/)(`const` 정확성)다 —\
  인터페이스를 처음부터 `const` 정확하게 쓰면 벗길 일이 안 생긴다.
- **`dynamic_cast` 를 안 쓰게 만드는 설계 둘** — ① **가상 함수**로 「물어보기」를 「시키기」로 바꾼다([목록의 **19번 주제**](../19-inheritance-virtual-functions-override-final/)) ·\
  ② **`std::variant` + `visit`** 으로 닫힌 집합을 타입으로 만든다(목록의 **47번 주제**).
- **열거형↔정수 캐스트가 필요한 이유**는 [**02번 형제**](../02-enum-class-and-scoped-enumerations/)의 담장 ②다.
- **C 스타일 캐스트와 엄격한 앨리어싱의 정본**은 C 갈래\
  [`05-explicit-casts-and-pointer-conversions/`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)다.\
  이 문서는 거기 결론을 **되짚기만** 하고, **C++ 가 새로 하는 것**(넷으로 쪼갠 것·`dynamic_cast`·상수식)만 팠다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `static_cast` 여섯 쓰임 | **통과** — `i=3 *p=3 up->a=1 down->b=2 n=1 c==Green:1` | g++ |
| `static_cast` 거부 셋 | **에러 3** · clang 만 `note: declared private here` | g++ · clang |
| ★ `const_cast` UB | **열 벌 전부 `k=7  *p=99  read_through(&k)=99`** | g++ ×5 · clang ×5 (`-O0`\~`-Os`) |
| 〃 sanitizer | **0줄** ×4 | g++ ubsan · g++ asan · g++ ubsan+asan · clang ubsan |
| 〃 경고 세기 | **네 벌 전부 0건** · `cc exit` 전부 0 | `-Wall -Wextra` / `+-pedantic` / `-Wcast-qual` / 합침 |
| `const_cast` 정의된 쓰임 | `k=99` — `-O0`·`-O2` 동일 | g++ ×2 |
| ★ 같은 코드를 C 로 | **`gcc -O0` 만 `k=99`** · `-O1`·`-O2` 는 `k=7` | gcc ×3 |
| ★ 엄격한 앨리어싱 | **다섯 수준 × 두 플래그 = 10벌** · 경계는 **`-O1`** · `-fno-` 는 전부 `1073741824` | g++ ×10 |
| 〃 clang | `-O0` `1073741824` · `-O2` `1` — **경계가 `-O2`** | clang ×2 |
| 〃 sanitizer | `punned=1` · **진단 0줄** | g++ `-O2 -fsanitize=undefined,address` |
| 타입 펀닝 3방법 | 셋 다 `1078523331` | g++ `-O2 -w` |
| 〃 경고 | g++ `-O2` **2건**(앨리어싱 + `used uninitialized`) · `-O0` **0건** · clang `-O2` **0건** | g++ ×2 · clang ×1 |
| 〃 `-Wstrict-aliasing` 수준별 | `=1`·`=2`·`=3` 전부 **1건** | g++ `-O2` ×4 |
| `dynamic_cast` 넷 | `4Left` · `1` · `非null` · `nullptr` · `std::bad_cast` | g++ |
| 비다형 타입 | **에러 1** — 두 컴파일러 다 「polymorphic」 | g++ · clang |
| `-fno-rtti` | g++ **에러 4** · clang **에러 2** | g++ · clang |
| ★ `nm -uC` 대조 | `static_cast` 판 **0개 / 1232 바이트** · `dynamic_cast` 판 **3개 / 2704 바이트** | g++ `-c` + `nm` ×2 |
| C 스타일 캐스트 셋 | **전부 통과** — `*p=7 q->a=1 r!=nullptr:1` | g++ |
| C 스타일 다운캐스트 | `非null` / `非null` / **`nullptr`** · `by_c->r` 이 **10** | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++/gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- `typeid(...).name()` 이 **`4Left`** 인 것 — **플랫폼 ABI.** 사람이 읽을 이름은 보장되지 않는다.
- **`__dynamic_cast`·`__cxxabiv1::__class_type_info` 라는 심볼 이름**과 **오브젝트 크기 1232/2704**.
- 진단 문구 전부 · **에러를 몇 개로 세는가**(`-fno-rtti` 에서 4 대 2).
- **`-Wstrict-aliasing=3` 이 1건**인 것 — 소스 모양에 달렸다.
- **`std::bad_cast::what()` 이 `"std::bad_cast"`** 인 것(표준은 구현 정의 문자열이라고만 한다).

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ `const_cast` UB 가 **열 벌에서 같았던 것**. 「안 갈렸다」가 「정의됐다」가 아니다.
- ★ 앨리어싱 경계가 **g++ 는 `-O1`, clang 은 `-O2`** 인 것.
- ★ 틀린 다운캐스트로 읽은 값이 **`10`** 인 것.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- 네 캐스트가 각각 무엇을 거부하는가 · C 스타일 캐스트의 **풀리는 순서**와 거기 `dynamic_cast` 가 **없는 것** ·
  포인터 실패 = `nullptr`, 참조 실패 = `std::bad_cast` · `dynamic_cast` 가 **다형 타입만** 받는 것 ·
  부동→정수가 **절단**인 것 · `memcpy`·`std::bit_cast` 가 **정의된** 것.
- ★ **`dynamic_cast`·`typeid` 를 쓸 수 있는지는 조건부**다 — `-fno-rtti` 면 문법이 아니다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **다중 상속**에서 `reinterpret_cast` 업캐스트가 주소를 어긋나게 하는 것\
  (이 문서는 단일 상속만 던졌다 — 주소를 싣게 되면 「흔들리는 칸」이 늘어난다) ·\
  `dynamic_cast<void*>(p)` · 가상 상속에서의 다운캐스트 ·\
  **`union` 을 통한 타입 펀닝**(C 갈래 [`05번`](../../../c/syntax/05-explicit-casts-and-pointer-conversions/)도 안 던졌다 — C++20 의 답이 `std::bit_cast` 라 그쪽을 실측했다) ·\
  `reinterpret_cast` 로 포인터↔정수 왕복(그 정본은 C 편이다).
- **못 잰 것** — **`dynamic_cast` 가 얼마나 느린가.**\
  계층 깊이·다중 상속·컴파일러에 달려 있고, 수치를 적으려면 **벤치마크 하네스가 따로** 필요하다.\
  이 문서가 보인 것은 「**호출이 생긴다**」와 「**오브젝트가 2배가 된다**」까지다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- **앨리어싱 경계선**(g++ `-O1` · clang `-O2`) — 최적화기가 바뀌면 가장 먼저 움직인다.
- **`const_cast` UB 가 여전히 열 벌에서 같은지.**
- `-fno-rtti` 진단 문구와 **에러 개수**.
- `nm -uC` 의 심볼 이름과 **오브젝트 크기**.
- `-Wstrict-aliasing` 수준별 건수.
