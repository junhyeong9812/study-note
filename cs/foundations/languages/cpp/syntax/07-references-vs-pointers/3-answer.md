# cpp/syntax/07 — 참조와 포인터의 차이 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump/nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이라 질문 쪽 발췌와 어긋날 수 있다 —\
> 그래서 **진단을 싣는 블록마다 그 진단을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★★ 이 주제의 네 번째 창은 **생성된 기계어**(`objdump -d`)다(3번).
> **읽는 법** — 기계어 덤프의 **주소·오프셋은 흔들리는 칸**이다. 근거로 쓰는 것은 **명령어 열**이다.\
> UB 는 6번(널 참조)과 7번(댕글링) 둘이고, **그 UB 가 만든 값은 싣지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ `r = b;` 는 재결합이 아니다 — `a` 가 2 가 된다

**출력**

```text
===== 소스: ptr01.cpp =====
// 참조는 재결합되지 않는다 — 같은 모양의 대입이 다른 일을 한다
#include <cstdio>

int main() {
    int a = 1, b = 2;
    int& r = a;
    int* p = &a;

    r = b;      // 참조: a 에 b 의 값을 쓴다
    p = &b;     // 포인터: p 가 가리키는 곳을 바꾼다

    std::printf("a=%d b=%d r=%d *p=%d\n", a, b, r, *p);
    std::printf("&a == &r : %d    &a == p : %d\n",
                static_cast<int>(&a == &r), static_cast<int>(&a == p));
    std::printf("sizeof(a)=%zu sizeof(r)=%zu sizeof(p)=%zu\n",
                sizeof(a), sizeof(r), sizeof(p));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
a=2 b=2 r=2 *p=2
&a == &r : 1    &a == p : 0
sizeof(a)=4 sizeof(r)=4 sizeof(p)=8
```

**왜 그런가**

| 쓴 것 | 한 일 | 그 뒤 |
|---|---|---|
| `r = b;` | ★ **`a` 에 `b` 의 값을 쓴다** | `a=2` · `r=2` · **`&a == &r` 은 계속 참** |
| `p = &b;` | **`p` 가 `b` 를 가리키게 된다** | `*p=2`(이제 `b` 를 본다) · `&a == p` 는 **거짓** |

- ★★★ **참조에는 「가리키는 대상을 바꾼다」는 연산 자체가 없다.**\
  `r` 에 무엇을 쓰든 **`a` 에 쓰는 것**이다. 그래서 `&a == &r` 이 **끝까지 참**이고,\
  그것이 「**`r` 은 `a` 의 또 하나의 이름**」이라는 말의 뜻이다.
- ★★ **`sizeof(r) == 4`**(`sizeof(int)`) — 표준이 「**참조의 `sizeof` 는 가리키는 대상의 크기**」로 정했다.\
  ★★★ **그렇다고 참조가 저장 공간을 안 쓴다는 뜻이 아니다.**\
  표준은 **참조가 공간을 차지하는지 정하지 않는다**(미명시). 이 구현에서는 **실제로 차지한다** —\
  3번의 기계어와 4번의 `sizeof(HasRef) == 8` 이 그 증거다.
- `sizeof(p) == 8` — 포인터는 **자기 크기**를 답한다.

### 2. ★ 에러 **다섯**(g++) / **넷**(clang) — 넷 다 포인터로는 된다

**출력**

```text
===== 소스: ptr02.cpp =====
// 참조가 못 하는 넷 — 포인터는 전부 된다
int g = 0;

int main() {
    int a = 1;
    int& r;                 // ① 초기화 없이
    int& ar[2] = {a, g};    // ② 참조의 배열
    int&* pr = &a;          // ③ 참조로의 포인터
    int& & rr = a;          // ④ 참조로의 참조
    (void)r; (void)ar; (void)pr; (void)rr;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr02.cpp -o ex (cc exit=1) =====
ptr02.cpp: In function ‘int main()’:
ptr02.cpp:6:10: error: ‘r’ declared as reference but not initialized
    6 |     int& r;                 // ① 초기화 없이
      |          ^
ptr02.cpp:7:10: error: declaration of ‘ar’ as array of references
    7 |     int& ar[2] = {a, g};    // ② 참조의 배열
      |          ^~
ptr02.cpp:8:11: error: cannot declare pointer to ‘int&’
    8 |     int&* pr = &a;          // ③ 참조로의 포인터
      |           ^~
ptr02.cpp:9:12: error: cannot declare reference to ‘int&’, which is not a typedef or a template type argument
    9 |     int& & rr = a;          // ④ 참조로의 참조
      |            ^~
ptr02.cpp:10:20: error: ‘ar’ was not declared in this scope; did you mean ‘rr’?
   10 |     (void)r; (void)ar; (void)pr; (void)rr;
      |                    ^~
      |                    rr
```

```text
===== 소스: ptr02.cpp =====
// 참조가 못 하는 넷 — 포인터는 전부 된다
int g = 0;

int main() {
    int a = 1;
    int& r;                 // ① 초기화 없이
    int& ar[2] = {a, g};    // ② 참조의 배열
    int&* pr = &a;          // ③ 참조로의 포인터
    int& & rr = a;          // ④ 참조로의 참조
    (void)r; (void)ar; (void)pr; (void)rr;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ptr02.cpp -o ex 2>&1 | grep -E 'error:|generated' (cc exit=1) =====
ptr02.cpp:6:10: error: declaration of reference variable 'r' requires an initializer
ptr02.cpp:7:12: error: 'ar' declared as array of references of type 'int &'
ptr02.cpp:8:9: error: 'pr' declared as a pointer to a reference of type 'int &'
ptr02.cpp:9:10: error: 'rr' declared as a reference to a reference
4 errors generated.
```

**왜 그런가**

| 쓴 것 | g++ | 포인터로는? |
|---|---|---|
| `int& r;` | ``declared as reference but not initialized`` | ★ **된다**(`int* p;`) |
| `int& ar[2];` | ``declaration of `ar` as array of references`` | ★ **된다**(`int* ar[2];`) |
| `int&* pr;` | ``cannot declare pointer to `int&` `` | ★ **된다**(`int** pr;`) |
| `int& & rr;` | ``cannot declare reference to `int&`, which is not a typedef or a template type argument`` | ★ **된다**(`int** rr;`) |

- **g++ 는 에러 5개**다 — 위 넷에 **`ar` 이 선언되지 못해 생긴 후속 에러** 하나가 붙는다.\
  **clang 은 4개**다(`4 errors generated.`). ★ **에러를 몇 개로 세는가는 구현이다.**
- ★★ **넷이 전부 포인터로는 된다.**
- ★★★ **넷이 하나의 성질로 설명된다** — **참조는 객체가 아니라 이름이다.**\
  배열의 원소도 포인터가 가리키는 대상도 **객체여야 하므로** 참조는 그 자리에 못 들어간다.
- ★★ **④의 단서** — ``which is not a typedef or a template type argument`` 는\
  「**직접 적을 수만 없고 템플릿 안에서는 생긴다**」는 뜻이다.\
  그때 **참조 축약**(`T& &` → `T&`)이 일어나고, 그것이 **전달 참조의 밑바탕**이다(목록의 **09번 주제**).

### 3. ★★★ **같다** — 한 명령도 다르지 않다

**출력**

```text
===== 소스: ptr03.cpp =====
int by_ref(int& x) { return x + 1; }
int by_ptr(int* x) { return *x + 1; }
===== g++ -std=c++20 -O2 -c ptr03.cpp -o ptr03.o && objdump -d --no-show-raw-insn ptr03.o | sed -n '/^0000/,$p' (exit=0) =====
0000000000000000 <_Z6by_refRi>:
   0:	endbr64
   4:	mov    (%rdi),%eax
   6:	add    $0x1,%eax
   9:	ret
   a:	nopw   0x0(%rax,%rax,1)

0000000000000010 <_Z6by_ptrPi>:
  10:	endbr64
  14:	mov    (%rdi),%eax
  16:	add    $0x1,%eax
  19:	ret
```

```text
===== 소스: ptr03.cpp =====
int by_ref(int& x) { return x + 1; }
int by_ptr(int* x) { return *x + 1; }
===== g++ -std=c++20 -O0 -c ptr03.cpp -o ptr03-O0.o && objdump -d --no-show-raw-insn ptr03-O0.o | sed -n '/^0000/,$p' (exit=0) =====
0000000000000000 <_Z6by_refRi>:
   0:	endbr64
   4:	push   %rbp
   5:	mov    %rsp,%rbp
   8:	mov    %rdi,-0x8(%rbp)
   c:	mov    -0x8(%rbp),%rax
  10:	mov    (%rax),%eax
  12:	add    $0x1,%eax
  15:	pop    %rbp
  16:	ret

0000000000000017 <_Z6by_ptrPi>:
  17:	endbr64
  1b:	push   %rbp
  1c:	mov    %rsp,%rbp
  1f:	mov    %rdi,-0x8(%rbp)
  23:	mov    -0x8(%rbp),%rax
  27:	mov    (%rax),%eax
  29:	add    $0x1,%eax
  2c:	pop    %rbp
  2d:	ret
```

```text
===== 소스: ptr03.cpp =====
int by_ref(int& x) { return x + 1; }
int by_ptr(int* x) { return *x + 1; }
===== nm -C ptr03.o; echo '--- 맹글링 원본 ---'; nm ptr03.o (exit=0) =====
0000000000000010 T by_ptr(int*)
0000000000000000 T by_ref(int&)
--- 맹글링 원본 ---
0000000000000010 T _Z6by_ptrPi
0000000000000000 T _Z6by_refRi
```

**왜 그런가**

| 물음 | 답 |
|---|---|
| `-O2` 의 명령어 열 | ★ **같다** — `endbr64` / `mov (%rdi),%eax` / `add $0x1,%eax` / `ret` |
| `-O0` 은? | ★ **거기서도 같다** — 프롤로그·에필로그까지 같은 순서다 |
| `nm -C` 는? | ★ **이름만 다르다** — `by_ref(int&)` 대 `by_ptr(int*)`, 맹글링은 `_Z6by_refRi` 대 `_Z6by_ptrPi` |

- ★★★ **참조도 포인터도 `%rdi` 에 주소를 받아 `mov (%rdi),%eax` 로 읽는다.**\
  **참조는 이 구현에서 포인터로 구현된다** — 1번의 `sizeof(r) == 4` 는 **그 사실을 숨긴다.**
- ★★★ **「참조가 더 빠르다」가 틀리는 근거가 이것**이다. 근거로 **코드 생성**을 들면 틀린다 —\
  **같은 명령어**가 나온다. 참조가 사는 것은 속도가 아니라 **컴파일러가 막아 주는 것**(2번·8번)이다.
- ★★ 뒤집으면 **「참조는 공짜다」도 틀린다** — **주소를 넘기는 비용은 그대로 있다.**\
  작은 값(`int`)을 `const int&` 로 받으면 **값 전달보다 느릴 수 있다**(간접 접근이 는다).\
  정본은 목록의 **11번 주제**다.
- ★ **주소·오프셋은 흔들리는 칸**이라 근거로 안 쓴다. ★ 그리고 이 결론은 **관찰**이다 —\
  「**타입 체계의 차이지 코드의 차이가 아니다**」가 결론이고, **명령어 하나하나가 결론이 아니다.**

### 4. ★★ 둘 다 **8** — 그런데 참조 멤버는 대입을 지운다

**출력**

```text
===== 소스: ptr04.cpp =====
// 참조 멤버는 대입을 지운다
#include <cstdio>

struct HasRef { int& r; };
struct HasPtr { int* p; };

int main() {
    int a = 1, b = 2;
    HasRef x{a}, y{b};
    HasPtr u{&a}, v{&b};
    std::printf("sizeof(HasRef)=%zu sizeof(HasPtr)=%zu\n", sizeof(HasRef), sizeof(HasPtr));
    u = v;                 // 포인터 멤버는 대입된다
    std::printf("*u.p = %d\n", *u.p);
    x = y;                 // 참조 멤버는?
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr04.cpp -o ex (cc exit=1) =====
ptr04.cpp: In function ‘int main()’:
ptr04.cpp:14:9: error: use of deleted function ‘HasRef& HasRef::operator=(const HasRef&)’
   14 |     x = y;                 // 참조 멤버는?
      |         ^
ptr04.cpp:4:8: note: ‘HasRef& HasRef::operator=(const HasRef&)’ is implicitly deleted because the default definition would be ill-formed:
    4 | struct HasRef { int& r; };
      |        ^~~~~~
ptr04.cpp:4:8: error: non-static reference member ‘int& HasRef::r’, cannot use default assignment operator
```

```text
===== 소스: ptr04.cpp =====
// 참조 멤버는 대입을 지운다
#include <cstdio>

struct HasRef { int& r; };
struct HasPtr { int* p; };

int main() {
    int a = 1, b = 2;
    HasRef x{a}, y{b};
    HasPtr u{&a}, v{&b};
    std::printf("sizeof(HasRef)=%zu sizeof(HasPtr)=%zu\n", sizeof(HasRef), sizeof(HasPtr));
    u = v;                 // 포인터 멤버는 대입된다
    std::printf("*u.p = %d\n", *u.p);
    x = y;                 // 참조 멤버는?
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ptr04.cpp -o ex 2>&1 | grep -E 'error:|note:|generated' (cc exit=1) =====
ptr04.cpp:14:7: error: object of type 'HasRef' cannot be assigned because its copy assignment operator is implicitly deleted
ptr04.cpp:4:22: note: copy assignment operator of 'HasRef' is implicitly deleted because field 'r' is of reference type 'int &'
1 error generated.
```

**왜 그런가**

| 물음 | 답 |
|---|---|
| `sizeof(HasRef)` / `sizeof(HasPtr)` | ★ **둘 다 8** — 참조가 **실제로는 포인터**다(3번) |
| `u = v;`(포인터 멤버) | **된다** — `*u.p` 가 `2` 가 된다 |
| `x = y;`(참조 멤버) | ★ **에러** — ``use of deleted function `HasRef& HasRef::operator=(const HasRef&)` `` |

- ★★★ **진단이 이유까지 말해 준다** — ``non-static reference member `int& HasRef::r`, cannot use default assignment operator``.\
  **참조는 재결합이 없으니**(1번) **대입 연산자를 만들 방법이 없다.**\
  「`x.r` 이 `y.r` 이 보는 객체를 보게 한다」는 것이 **참조로는 표현 불가능한 문장**이다.\
  clang 은 같은 말을 `note:` 로 한 줄 붙인다.
- ★★★ **컨테이너에 못 담는다.** `std::vector<HasRef>` 는 `push_back`·`erase`·`sort` 가 전부 **대입을 쓴다.**\
  참조 멤버를 두는 순간 그 타입은 「**담을 수 없는 타입**」이 된다.
- ★ 고치는 법은 **포인터 멤버**나 **`std::reference_wrapper<int>`** 다(후자는 대입이 된다).\
  ★ **이 문서는 `reference_wrapper` 를 안 던졌다.**

### 5. ★★ A 에서는 블록 끝까지 산다 — 포인터는 아예 못 받는다

**출력**

```text
===== 소스: ptr05.cpp =====
// const 참조가 임시의 수명을 늘린다
#include <cstdio>

struct Noisy {
    int v;
    explicit Noisy(int x) : v(x) { std::printf("  Noisy(%d) 생성\n", v); }
    ~Noisy()                     { std::printf("  ~Noisy(%d) 파괴\n", v); }
};

Noisy make(int x) { return Noisy(x); }

int main() {
    std::printf("A: const 참조에 묶는다\n");
    {
        const Noisy& r = make(1);
        std::printf("  블록 안 — r.v = %d\n", r.v);
    }
    std::printf("B: 안 묶고 그냥 만든다\n");
    {
        make(2);
        std::printf("  이 줄은 파괴 뒤다\n");
    }
    std::printf("끝\n");
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
A: const 참조에 묶는다
  Noisy(1) 생성
  블록 안 — r.v = 1
  ~Noisy(1) 파괴
B: 안 묶고 그냥 만든다
  Noisy(2) 생성
  ~Noisy(2) 파괴
  이 줄은 파괴 뒤다
끝
```

**왜 그런가**

| 경우 | 임시가 언제 죽나 |
|---|---|
| A: `const Noisy& r = make(1);` | ★ **`r` 의 블록이 끝날 때** — `~Noisy(1)` 이 「블록 안」 출력 **뒤**에 찍혔다 |
| B: `make(2);`(안 묶음) | **그 문장이 끝날 때** — `~Noisy(2)` 가 다음 출력 **앞**에 찍혔다 |

- ★★★ **두 출력의 순서가 그 자체로 증거다.**\
  A 는 `Noisy(1) 생성` → `블록 안 — r.v = 1` → `~Noisy(1) 파괴`,\
  B 는 `Noisy(2) 생성` → `~Noisy(2) 파괴` → `이 줄은 파괴 뒤다`.\
  규칙의 이름은 **수명 연장(lifetime extension)** 이고, **`const T&`(와 `T&&`)에 묶었을 때만** 일어난다.

**포인터로는 흉내조차 못 낸다.**

```text
===== 소스: ptr06.cpp =====
// 포인터는 같은 일을 못 한다 — 임시의 주소를 못 받는다
struct Noisy { int v; };
Noisy make(int x) { return Noisy{x}; }

int main() {
    const Noisy* p = &make(3);
    return p->v;
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr06.cpp -o ex (cc exit=1) =====
ptr06.cpp: In function ‘int main()’:
ptr06.cpp:6:27: error: taking address of rvalue [-fpermissive]
    6 |     const Noisy* p = &make(3);
      |                       ~~~~^~~
```

```text
===== 소스: ptr06.cpp =====
// 포인터는 같은 일을 못 한다 — 임시의 주소를 못 받는다
struct Noisy { int v; };
Noisy make(int x) { return Noisy{x}; }

int main() {
    const Noisy* p = &make(3);
    return p->v;
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ptr06.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=1) =====
ptr06.cpp:6:22: error: taking the address of a temporary object of type 'Noisy' [-Waddress-of-temporary]
1 error generated.
```

- ★★★ ``error: taking address of rvalue [-fpermissive]``(g++) ·\
  ``error: taking the address of a temporary object of type 'Noisy' [-Waddress-of-temporary]``(clang).\
  **임시의 주소를 못 얻는다** — 그러니 「포인터로 임시를 받는다」는 문장이 **언어에 없다.**
- ★★★ **이것이 매개변수 설계의 근거다.**\
  `f(const T& x)` 는 **`f(std::string("hi"))` 를 받을 수 있고**,\
  `f(const T* x)` 는 **호출자가 변수를 따로 만들어야 한다.**
- ★ **수명 연장에는 구멍이 많다** — 참조를 **반환**하거나 **멤버로 저장**하면 **안 늘어난다.**\
  이 문서는 **블록 안 판만** 던졌다. 정본은 목록의 **30번 주제**다.

### 6. ★★ 경고 **둘** — 「없다」가 아니라 「없다고 가정한다」

**출력**

```text
===== 소스: ptr08.cpp =====
// 참조는 널이 아니라고 「가정된다」 — 검사하려 들면 컴파일러가 말해 준다
#include <cstdio>

bool check_ref(int& r) { return &r == nullptr; }
bool check_ptr(int* p) { return p == nullptr; }

int main() {
    int a = 1;
    std::printf("check_ref(a)=%d  check_ptr(&a)=%d  check_ptr(nullptr)=%d\n",
                static_cast<int>(check_ref(a)),
                static_cast<int>(check_ptr(&a)),
                static_cast<int>(check_ptr(nullptr)));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr08.cpp -o ex (cc exit=0) =====
ptr08.cpp: In function ‘bool check_ref(int&)’:
ptr08.cpp:4:36: warning: the compiler can assume that the address of ‘r’ will never be NULL [-Waddress]
    4 | bool check_ref(int& r) { return &r == nullptr; }
      |                                 ~~~^~~~~~~~~~
ptr08.cpp:4:21: note: ‘r’ declared here
    4 | bool check_ref(int& r) { return &r == nullptr; }
      |                ~~~~~^
ptr08.cpp:4:39: warning: ‘nonnull’ argument ‘r’ compared to NULL [-Wnonnull-compare]
    4 | bool check_ref(int& r) { return &r == nullptr; }
      |                                       ^~~~~~~
```

```text
===== 소스: ptr08.cpp =====
// 참조는 널이 아니라고 「가정된다」 — 검사하려 들면 컴파일러가 말해 준다
#include <cstdio>

bool check_ref(int& r) { return &r == nullptr; }
bool check_ptr(int* p) { return p == nullptr; }

int main() {
    int a = 1;
    std::printf("check_ref(a)=%d  check_ptr(&a)=%d  check_ptr(nullptr)=%d\n",
                static_cast<int>(check_ref(a)),
                static_cast<int>(check_ptr(&a)),
                static_cast<int>(check_ptr(nullptr)));
}
===== g++ -std=c++20 -w ptr08.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
check_ref(a)=0  check_ptr(&a)=0  check_ptr(nullptr)=1
```

```text
===== 소스: ptr08.cpp =====
// 참조는 널이 아니라고 「가정된다」 — 검사하려 들면 컴파일러가 말해 준다
#include <cstdio>

bool check_ref(int& r) { return &r == nullptr; }
bool check_ptr(int* p) { return p == nullptr; }

int main() {
    int a = 1;
    std::printf("check_ref(a)=%d  check_ptr(&a)=%d  check_ptr(nullptr)=%d\n",
                static_cast<int>(check_ref(a)),
                static_cast<int>(check_ptr(&a)),
                static_cast<int>(check_ptr(nullptr)));
}
===== clang++ -std=c++20 -Wall -Wextra -pedantic ptr08.cpp -o ex 2>&1 | grep -E 'error:|warning:|generated' (cc exit=0) =====
ptr08.cpp:4:34: warning: reference cannot be bound to dereferenced null pointer in well-defined C++ code; comparison may be assumed to always evaluate to false [-Wtautological-undefined-compare]
1 warning generated.
```

**왜 그런가**

| 물음 | 답 |
|---|---|
| 컴파일되는가 | ★ **된다. `cc exit=0`** |
| g++ 경고 | ★ **2건** — `-Waddress` 와 `-Wnonnull-compare` |
| clang 경고 | **1건** — `-Wtautological-undefined-compare` |
| `check_ref(a)` | **0**(거짓) |

- ★★★ **g++ 문구가 정확히 말해 준다** — ``the compiler can assume that the address of `r` will never be NULL``.\
  「**없다**」가 아니라 「**없다고 가정하고 최적화한다**」다.\
  clang 은 더 세게 말한다 — ``reference cannot be bound to dereferenced null pointer in well-defined C++ code; comparison may be assumed to always evaluate to false``.
- ★★ **그러니 「참조는 널이 아니다」는 보장이 아니라 「그런 코드를 쓰지 않겠다는 약속」이다.**\
  약속을 깨면 **컴파일러가 이미 그 가정 위에서 코드를 만들어 놓은 뒤**다.

**깨면 UB 이고, 이 UB 는 도구가 본다.**

```text
===== 소스: ptr09.cpp =====
// 그 가정을 깨면 — 묶는 순간이 UB 다
#include <cstdio>

int peek(int& r) { return r; }

int main() {
    int* p = nullptr;
    std::fprintf(stderr, "마커: 묶기 직전\n");
    int& r = *p;
    std::fprintf(stderr, "마커: 묶었다\n");
    std::fprintf(stderr, "peek = %d\n", peek(r));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O0 -fsanitize=undefined ptr09.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
마커: 묶기 직전
ptr09.cpp:9:10: runtime error: reference binding to null pointer of type 'int'
마커: 묶었다
ptr09.cpp:4:27: runtime error: load of null pointer of type 'int'
```

- ★★ **`runtime error: reference binding to null pointer of type 'int'`** — **묶는 그 줄**(`int& r = *p;`)을 짚는다.\
  「읽을 때」가 아니라 **「묶을 때」가 이미 UB** 라는 것이 문구에 적혀 있다.\
  마커(`묶기 직전` / `묶었다`)가 그 사이에 찍힌 것이 순서를 보여 준다.
- ★ sanitizer 없이 돌리면 **아무 말 없이 죽는다**.

```text
===== 소스: ptr09.cpp =====
// 그 가정을 깨면 — 묶는 순간이 UB 다
#include <cstdio>

int peek(int& r) { return r; }

int main() {
    int* p = nullptr;
    std::fprintf(stderr, "마커: 묶기 직전\n");
    int& r = *p;
    std::fprintf(stderr, "마커: 묶었다\n");
    std::fprintf(stderr, "peek = %d\n", peek(r));
}
===== g++ -std=c++20 -Wall -Wextra -pedantic -O2 ptr09.cpp -o ex && ./ex (cc exit=0 · run exit=139) =====
마커: 묶기 직전
마커: 묶었다
```

- **`run exit=139`**(SIGSEGV)다. ★ **컴파일 시간에는 경고 0건**이다.
- ★ **마커를 `std::cerr` 로 찍었다** — stdout 과 섞으면 **죽을 때 버퍼가 날아가** 마커가 통째로 사라진다.
- ★ **UB 가 만든 값은 싣지 않았다.** 근거로 쓰는 것은 「UBSan 이 묶는 줄을 짚었다」와 「`run exit=139`」다.

### 7. **같은 경고 이름** — 참조가 더 안전하지 않다

**출력**

```text
===== 소스: ptr07.cpp =====
// 지역을 돌려주면 — 참조와 포인터가 같은 경고를 받는다
#include <cstdio>

int& dangling_ref() { int local = 42; return local; }
int* dangling_ptr() { int local = 43; return &local; }

int main() {
    int& r = dangling_ref();
    int* p = dangling_ptr();
    std::printf("r=%d *p=%d\n", r, *p);
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr07.cpp -o ex (cc exit=0) =====
ptr07.cpp: In function ‘int& dangling_ref()’:
ptr07.cpp:4:46: warning: reference to local variable ‘local’ returned [-Wreturn-local-addr]
    4 | int& dangling_ref() { int local = 42; return local; }
      |                                              ^~~~~
ptr07.cpp:4:27: note: declared here
    4 | int& dangling_ref() { int local = 42; return local; }
      |                           ^~~~~
ptr07.cpp: In function ‘int* dangling_ptr()’:
ptr07.cpp:5:46: warning: address of local variable ‘local’ returned [-Wreturn-local-addr]
    5 | int* dangling_ptr() { int local = 43; return &local; }
      |                                              ^~~~~~
ptr07.cpp:5:27: note: declared here
    5 | int* dangling_ptr() { int local = 43; return &local; }
      |                           ^~~~~
```

**왜 그런가**

| 함수 | 경고 | 이름 |
|---|---|---|
| `int& dangling_ref()` | ``reference to local variable `local` returned`` | ★ `-Wreturn-local-addr` |
| `int* dangling_ptr()` | ``address of local variable `local` returned`` | ★ **같은** `-Wreturn-local-addr` |

- ★★★ **경고 이름이 같다.** 문구만 `reference to` 대 `address of` 로 다르다 —\
  **컴파일러는 둘을 같은 사고로 본다.**
- ★★ **`cc exit=0`** 이다. **경고일 뿐 빌드는 된다.**
- ★★★ **그러므로 「참조가 안전하다」는 틀린 요약**이다.\
  참조가 막는 것은 「**널**」과 「**재결합**」뿐이고, **댕글링은 그대로 난다.**\
  정본은 목록의 **30번 주제**다.
- ★ 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의 `decltype(auto)` 댕글링이 **같은 경고**를 받았다 —\
  거기서는 **`return (x);` 의 괄호 하나**가 이 경고를 불러냈다.

### 8. `take_ref(nullptr)` 만 막힌다 — 그래서 시그니처가 문서가 된다

**출력**

```text
===== 소스: ptr10.cpp =====
// 인터페이스 — 참조 매개변수는 「없음」을 못 받는다
void take_ref(int& x) { (void)x; }
void take_ptr(int* x) { (void)x; }

int main() {
    take_ptr(nullptr);     // ① 포인터는 「없음」이 값이다
    take_ref(nullptr);     // ② 참조는?
}
===== g++ -std=c++20 -Wall -Wextra -pedantic ptr10.cpp -o ex (cc exit=1) =====
ptr10.cpp: In function ‘int main()’:
ptr10.cpp:7:14: error: invalid initialization of non-const reference of type ‘int&’ from an rvalue of type ‘std::nullptr_t’
    7 |     take_ref(nullptr);     // ② 참조는?
      |              ^~~~~~~
ptr10.cpp:2:20: note: in passing argument 1 of ‘void take_ref(int&)’
    2 | void take_ref(int& x) { (void)x; }
      |               ~~~~~^
```

**왜 그런가**

- **`take_ptr(nullptr)`** 는 **통과**한다 — 포인터에게 **널은 값**이다.
- **`take_ref(nullptr)`** 는 막힌다 —\
  ``error: invalid initialization of non-const reference of type `int&` from an rvalue of type `std::nullptr_t` `` +\
  ``note: in passing argument 1 of `void take_ref(int&)` ``.
- ★★★ **그래서 시그니처가 문서가 된다** —\
  `void f(int& x)` 는 「**반드시 있다**」를, `void f(int* x)` 는 「**없을 수도 있다**」를 말한다.\
  호출자는 `f(*p)` 를 쓰기 전에 **`p` 를 검사해야 한다**는 것을 시그니처만 보고 안다.
- ★★ **`T*` 보다 나은 도구** —\
  ① **`std::optional<T>`** — 「값이 없을 수 있음」을 **소유와 함께** 말한다(목록의 **47번 주제**) ·\
  ② **`T*`** 는 「비소유 관찰자 + 없을 수 있음」의 정당한 자리다(목록의 **29번 주제**) ·\
  ③ **`std::reference_wrapper<T>`** 는 「참조인데 재결합·저장이 된다」.\
  ★ **이 문서는 ①②③을 던져 보지 않았다** — 정본이 다른 주제다.

### 9. 어느 쪽을 쓸까

**왜 그런가**

**참조를 먼저 고르는 이유 셋**

- ① ★ **「반드시 있다」를 타입으로 말한다**(8번) — 호출자도 구현자도 **널 검사를 안 쓴다.**
- ② **재결합이 없어 읽기 쉽다**(1번) — 한 번 정해지면 그 이름은 그 객체다.
- ③ ★ **임시를 받을 수 있다**(5번) — `f(std::string("hi"))` 가 된다. **포인터로는 불가능하다.**

**포인터를 반드시 써야 하는 자리 셋**

- ① **없을 수 있을 때**(널) · ② **가리키는 대상을 바꿔야 할 때**(재결합) ·\
  ③ **멤버·배열·컨테이너에 담을 때**(2번·4번).\
  ★ **C API 경계**도 여기에 든다 — C 에는 참조가 없다.

**「참조는 널이 아니다」는 보장인가 약속인가**

- ★★★ **약속이다**(6번). 컴파일러는 「**없다고 가정**」할 뿐이고, 깨면 **UB** 다.\
  **컴파일 시간에는 0건**이고 UBSan 만 본다.

**재결합하고 싶어지면**

- **`std::reference_wrapper<T>`** — 참조를 **객체로 감싼 것**이라 대입이 되고 컨테이너에 담긴다.\
  ★ **이 문서는 안 던졌다.**

### 10. 이 주제의 지도

**왜 그런가**

- **`auto&`·`auto&&` 가 무엇인지**의 정본은 형제 [**05번**](../05-auto-and-decltype-type-deduction/)이다.\
  ★ 거기 (6)의 `decltype(auto)` 댕글링이 **이 주제의 7번과 같은 경고**를 받는다.
- **참조가 어떤 식에 묶이는지**(lvalue·xvalue·prvalue)의 정본은 목록의 **08번 주제**(값 범주)다.\
  ★ `T&` 는 lvalue 에만 묶이고, `const T&` 와 `T&&` 가 임시를 받는다(5번).
- **`const T&` 매개변수 설계**의 정본은 목록의 **10번 주제**(`const` 정확성)와\
  목록의 **11번 주제**(매개변수 전달 방식 고르기)다. ★ 3번의 「참조가 공짜는 아니다」가 거기서 결론난다.
- **댕글링과 수명 연장**의 정본은 목록의 **30번 주제**다 —\
  ★ **수명 연장이 안 되는 자리**(반환·멤버 저장·범위 for)가 거기 있고, 이 문서는 **블록 안 판만** 던졌다.
- **포인터 산술·배열 감쇠**는 C 갈래\
  [`15-pointer-arithmetic-and-indexing/`](../../../c/syntax/15-pointer-arithmetic-and-indexing/)·[`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)다.\
  ★ **참조에는 그 이야기가 없다** — 참조는 「이름」이라 **더하거나 뺄 대상이 아니고**,\
  **참조의 배열이 없으니**(2번) 감쇠할 배열도 없다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 명령으로 돌렸나 |
|---|---|---|
| `ptr01.cpp` 재결합 | `a=2 b=2 r=2 *p=2` · ★ `&a == &r` **참** · `sizeof` 4/4/8 | g++ |
| `ptr02.cpp` 못 하는 넷 | ★ **g++ 에러 5 · clang 에러 4** | g++ · clang |
| `ptr03.cpp` 기계어 | ★★★ **`-O2`·`-O0` 둘 다 명령어 열이 같다** · 심볼만 `Ri` 대 `Pi` | g++ `-O2 -c` · `-O0 -c` + `objdump` · `nm` |
| `ptr04.cpp` 참조 멤버 | ★ `sizeof` **둘 다 8** · `x = y;` **에러**(삭제된 대입) | g++ · clang |
| `ptr05.cpp` 수명 연장 | ★ A 는 **블록 끝**에 파괴 · B 는 **문장 끝**에 파괴 | g++ |
| `ptr06.cpp` 임시의 주소 | ★ **에러** — `taking address of rvalue` / `taking the address of a temporary object` | g++ · clang |
| `ptr07.cpp` 댕글링 반환 | ★★ **같은 경고 이름** `-Wreturn-local-addr` · **`cc exit=0`** | g++ |
| `ptr08.cpp` 널 검사 | ★ g++ **경고 2**(`-Waddress`·`-Wnonnull-compare`) · clang **1**(`-Wtautological-undefined-compare`) | g++ · clang |
| 〃 실행 | `check_ref(a)=0 check_ptr(&a)=0 check_ptr(nullptr)=1` | g++ `-w` |
| `ptr09.cpp` 널 참조 UB | ★ UBSan **1줄**(묶는 줄을 짚는다) · **`run exit=139`** | g++ `-O0 -fsanitize=undefined` |
| 〃 sanitizer 없이 | ★ **진단 0줄** · **`run exit=139`** | g++ `-O2` |
| `ptr10.cpp` 인터페이스 | ★ `take_ptr(nullptr)` 통과 · `take_ref(nullptr)` **에러** | g++ |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · binutils 2.42)에서만** 그렇다.

- ★ **참조가 포인터로 구현되는 것**(`sizeof(HasRef) == 8` · 3번의 기계어) —\
  **표준은 참조가 저장 공간을 쓰는지 정하지 않는다**(미명시).
- ★ **기계어가 같다는 것** — **관찰**이다. 결론은 「**타입 체계의 차이지 코드의 차이가 아니다**」이고,\
  **명령어 하나하나가 결론이 아니다.**
- ★ **맹글링**(`_Z6by_refRi` · `_Z6by_ptrPi`) — 플랫폼 ABI(Itanium C++ ABI).
- 진단 문구 전부 · 경고 이름(`-Waddress`·`-Wnonnull-compare` 대 `-Wtautological-undefined-compare`) ·
  **에러를 몇 개로 세는가**(2번에서 g++ 5, clang 4).
- 기계어 덤프의 **주소·오프셋** — 흔들리는 칸이다.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **참조는 반드시 초기화**되고 **재결합이 없는** 것.
- **참조의 배열·참조로의 포인터·참조로의 참조가 없는** 것.
- **`sizeof(참조)` 가 대상의 크기**인 것.
- **참조 멤버가 복사 대입 연산자를 삭제하는** 것.
- **`const T&` 가 임시의 수명을 늘리는** 것 · **임시의 주소를 못 얻는** 것.
- **`nullptr` 를 `T&` 에 못 묶는** 것.
- ★ **널 포인터를 역참조해 참조에 묶는 것이 UB** 인 것.

**UB 의 결과라 보장이 아닌 것**(관찰로만 읽는다)

- ★ 6번의 **`run exit=139`** — SIGSEGV 로 죽은 것은 **이 판의 결과**다.\
  근거로 쓰는 것은 「**UBSan 이 묶는 줄을 짚었다**」와 「**sanitizer 없이는 0줄이다**」다.
- ★ 7번의 **댕글링 참조·포인터가 읽은 값** — 이 문서는 **싣지 않았다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **rvalue 참조 `T&&`**(정본이 목록의 **09번 주제**다) ·
  **`std::reference_wrapper` 로 재결합 흉내 내기** ·
  **`std::optional`·`std::span` 으로 「없음」을 말하는 것**(정본이 목록의 **47번**·**46번 주제**다) ·
  **수명 연장이 안 되는 자리**(참조 반환·멤버 저장·범위 for 의 임시 — 목록의 **30번 주제**) ·
  **참조 멤버가 있는 타입의 이동 연산**(복사 대입만 던졌다) ·
  **비트필드로의 참조**(프록시가 필요하다 — 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의 `vector<bool>` 과 같은 집안) ·
  **`-O1`·`-O3`·`-Os` 의 기계어**(3번은 `-O0`·`-O2` 두 수준만 던졌다).
- **못 잰 것** — ★ **「참조가 더 빠른가」를 수치로.**\
  3번이 보인 것은 「**이 두 함수의 명령어 열이 같다**」까지다.\
  **호출 비용 전체를 재려면 벤치마크 하네스가 따로** 필요하고, 그때도 **함수 모양에 달린 답**이 나온다.\
  ★ 이 문서는 그래서 **수치를 적지 않았다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★ **`by_ref`/`by_ptr` 의 기계어가 계속 같은지**(3번) — 최적화기가 바뀌면 가장 먼저 움직인다.
- ★ **널 참조에 대한 경고 개수**(g++ 2 · clang 1)와 이름.
- ★ **UBSan 이 내는 줄 수**(지금은 1줄).
- 진단 문구와 **에러 개수**(2번의 5 대 4).
