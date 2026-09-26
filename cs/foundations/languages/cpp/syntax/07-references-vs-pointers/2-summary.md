# cpp/syntax/07 — 참조와 포인터의 차이 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 참조 선언](https://en.cppreference.com/w/cpp/language/reference) · [참조 초기화와 수명 연장](https://en.cppreference.com/w/cpp/language/reference_initialization) · [포인터 선언](https://en.cppreference.com/w/cpp/language/pointer) · [`std::reference_wrapper`](https://en.cppreference.com/w/cpp/utility/functional/reference_wrapper) · [`std::optional`](https://en.cppreference.com/w/cpp/utility/optional) · [GCC 13 Warning Options — `-Waddress`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·진단·기계어는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU objdump/nm 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고,\
> 블록마다 **소스 파일 이름이 다르다**(`ptr01.cpp` \~ `ptr10.cpp`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다.\
> ★ 긴 진단은 **거르는 명령을 배너에 적어 두었다**(`| grep -E 'error:|generated'`).\
> 그러니 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이다.
> **버전** — lvalue 참조는 **C++98부터**. rvalue 참조(`T&&`)는 **C++11부터**이고,\
> **이 주제는 lvalue 참조만** 다룬다(그쪽 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「포인터가 무엇인가」(주소·역참조·포인터 타입)의 정본은 C 갈래\
> [`14-pointers-address-dereference-and-pointer-types/`](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/)다.\
> 「포인터 산술·배열 감쇠」는 C 갈래 [`15번`](../../../c/syntax/15-pointer-arithmetic-and-indexing/)·[`16번`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/),\
> 「`void*`·널 포인터」는 C 갈래 [`19번`](../../../c/syntax/19-void-pointer-null-pointer-and-null/)이다.\
> 여기는 **C 에 없는 쪽**만 쓴다 — **참조가 무엇을 못 하고, 그 「못 함」이 설계에서 무엇을 사는가.**\
> 「값 범주(어떤 식에 참조가 묶이나)」는 [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/), 「rvalue 참조·`move`」는 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/),\
> 「`const` 정확성 설계」는 [목록의 **10번 주제**](../10-const-correctness/), 「매개변수 전달 방식 고르기」는 [목록의 **11번 주제**](../11-choosing-parameter-passing/),\
> 「댕글링과 수명」은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)가 정본이다. 여기서는 **그 앞의 한 겹**까지만 판다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 기계어 덤프의 **주소·오프셋**(`0:` · `17:`) | ★ **명령어 열 자체**(`endbr64` · `mov (%rdi),%eax` · `add $0x1,%eax` · `ret`) |
> | 댕글링 참조가 **읽은 값**(이 문서는 **싣지 않았다**) | **진단 본문** · `파일:줄:칸` · **경고 이름** |
> | UB 로 죽을 때 셸이 찍는 신호 메시지 | **`cc exit` 와 `run exit`**(갈라 적었다 — 널 참조 판은 `run exit=139`) |
> | — | `sizeof` 값 · 소멸자가 **언제** 불렸나 · **맹글링된 심볼**(`_Z6by_refRi` 대 `_Z6by_ptrPi`) |

## 한눈에 — 쉽게 말하면

**포인터는 「주소가 적힌 쪽지」이고, 참조는 「그 사람에게 붙인 또 하나의 이름」이다.**

쪽지는 **비워 둘 수도, 다른 주소로 고쳐 쓸 수도** 있다.\
이름은 **붙이는 순간 정해지고, 빈 이름이 없고, 다른 사람에게 옮겨 붙일 수 없다.**

| 비유 | 실체 |
|---|---|
| **주소가 적힌 쪽지** — 비어 있을 수 있다 | `int* p = nullptr;` |
| **쪽지를 고쳐 쓴다** | `p = &b;` — **재결합** |
| ★ **사람에게 붙인 또 하나의 이름** | `int& r = a;` — **`r` 은 `a` 다** |
| ★ **「이름을 다른 사람에게 옮긴다」는 문장이 없다** | `r = b;` 는 **`a` 에 `b` 의 값을 쓰는 것**((1)) |
| ★ **빈 이름이라는 게 없다** | `int& r;` 는 **컴파일 에러**((2)) |
| **쪽지 다발은 만들 수 있다** | `int* arr[2];` — 되지만 `int& ar[2];` 는 **안 된다**((2)) |
| ★★ **그런데 일을 시키면 둘이 똑같이 일한다** | **기계어가 한 명령도 안 다르다**((3)) |

- ★★★ **차이는 「타입 체계」에 있지 「기계어」에 있지 않다**((3)).\
  `by_ref(int&)` 와 `by_ptr(int*)` 가 `-O0` 에서도 `-O2` 에서도 **명령어 열이 같다.**\
  다른 것은 **맹글링된 이름**(`Ri` 대 `Pi`)뿐이다 — **차이는 컴파일러가 무엇을 막아 주느냐**다.
- ★★ **참조가 「못 하는 것」이 곧 참조의 값**이다 — 널이 없고, 재결합이 없으니\
  **「이 인자는 반드시 있다」를 타입으로 말할 수 있다**((8)).
- ★★ **딱 한 가지는 참조만 할 수 있다** — **임시의 수명을 늘리는 것**((5)).\
  포인터는 `&make(3)` 이 **컴파일 에러**라 흉내조차 못 낸다.

```text
   int a = 1, b = 2;

   int* p = &a;        p ──> a          "쪽지"
   p = &b;             p ──> b          재결합된다

   int& r = a;         r ≡ a            "또 하나의 이름"
   r = b;              a 의 값이 2 가 된다   ← 재결합이 아니다!
                       &a == &r 은 계속 참

   ┌── 참조가 못 하는 것 ──────────────┬── 포인터는? ──┐
   │ 초기화 없이 선언      int& r;     │ 된다          │
   │ 참조의 배열           int& ar[2]; │ 된다          │
   │ 참조로의 포인터       int&* pr;   │ 된다(int**)   │
   │ 참조로의 참조         int& & rr;  │ 된다(int**)   │
   │ 널                    —           │ 된다(nullptr) │
   │ 재결합                —           │ 된다          │
   └───────────────────────────────────┴───────────────┘

   ┌── 참조만 할 수 있는 것 ───────────────────────────┐
   │ const T& r = 임시;   임시의 수명이 r 까지 늘어난다 │
   │ const T* p = &임시;  ← 컴파일 에러                 │
   └───────────────────────────────────────────────────┘
```

> **참조(reference)** — 이미 있는 객체에 붙이는 **또 하나의 이름**.\
> **반드시 초기화해야 하고, 다른 객체로 옮겨 붙일 수 없다.**

> **재결합(rebinding)** — 「가리키는 대상을 바꾸는 것」. 포인터에는 있고 **참조에는 없다.**

> **수명 연장(lifetime extension)** — `const T&`(또는 `T&&`)에 임시를 묶으면\
> **그 참조가 사는 동안 임시도 산다**는 규칙((5)).

> **댕글링(dangling)** — 이미 죽은 객체를 가리키는 참조·포인터. **UB 다.**

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **참조는 포인터와 무엇이 다른가** — **문법**(못 하는 것)과 **기계어**를 **갈라서** 말할 수 있나((2)·(3)).
2. **그 「못 함」이 무엇을 사는가** — 「널일 수 있다」를 **타입으로** 말하는 쪽과 못 말하는 쪽을 가를 수 있나((8)).
3. **참조가 안전한가** — **아니다**((7)). 댕글링은 **둘 다 난다.** 그것을 **같은 경고로** 보일 수 있나.

## 동작 방식

### (0) 이 주제가 쓰는 네 창

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| **실행 출력** | 재결합이 없다는 것 · 임시의 수명 · `sizeof` | (1)·(4)·(5) |
| **컴파일 진단** | ★ **참조가 못 하는 것 전부** — 이 주제의 값이 여기 몰린다 | (2)·(4)·(6)·(8) |
| ★★ **생성된 기계어**(`objdump -d`) | ★★★ **타입 체계의 차이지 코드의 차이가 아니라는 것** | (3) |
| **sanitizer + 종료 코드** | 널 참조가 **UB 라는 것**과 **도구가 본다는 것** | (6) |

★★★ **세 번째 창이 이 주제의 중심이다.** 「참조가 빠르다」·「포인터가 빠르다」 같은 말이
**무엇을 근거로 하면 틀리는지**를 한 번에 끝낸다 — **같은 명령어 열**이 나온다((3)).

★ **그래서 이 주제의 질문은 「무엇이 더 좋은가」가 아니라 「무엇을 말할 수 있는가」가 된다.**
`f(int&)` 는 「**반드시 있다**」를 말하고, `f(int*)` 는 「**없을 수도 있다**」를 말한다((8)).

### (1) 재결합이 없다 — 같은 모양의 대입이 다른 일을 한다

**언제 쓰나** — 참조를 처음 쓸 때. **가장 자주 무는 자리**다.

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

| 쓴 것 | 한 일 |
|---|---|
| `r = b;` | ★ **`a` 에 `b` 의 값을 쓴다.** `r` 이 `b` 를 가리키게 되는 것이 **아니다** |
| `p = &b;` | **`p` 가 `b` 를 가리키게 된다** — 재결합 |

- ★★★ **`&a == &r` 이 계속 참**이다. `r = b;` 뒤에도 `r` 은 여전히 `a` 다.\
  **참조에는 「가리키는 대상을 바꾼다」는 연산 자체가 없다** — `r` 에 무엇을 쓰든 **`a` 에 쓰는 것**이다.
- ★★ **`sizeof(r) == 4`** 다(`sizeof(int)`). ★ **그렇다고 참조가 저장 공간을 안 쓴다는 뜻은 아니다** —\
  `sizeof` 는 **참조가 가리키는 대상의 크기**를 답하도록 표준이 정했을 뿐이고,\
  구현이 **내부적으로 포인터를 쓸지 말지는 규정하지 않는다**((3)에서 실제로 포인터처럼 쓰이는 것을 본다).
- ★ `sizeof(p) == 8` — 포인터는 **자기 크기**를 답한다.

### (2) 참조가 못 하는 넷

**언제 쓰나** — 「참조로 이걸 할 수 있나?」 할 때. **진단이 답을 말해 준다.**

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

| 쓴 것 | g++ 의 답 | 포인터로는? |
|---|---|---|
| `int& r;` | ``declared as reference but not initialized`` | ★ **된다**(`int* p;`) |
| `int& ar[2];` | ``declaration of `ar` as array of references`` | ★ **된다**(`int* ar[2];`) |
| `int&* pr;` | ``cannot declare pointer to `int&` `` | ★ **된다**(`int** pr;`) |
| `int& & rr;` | ``cannot declare reference to `int&`, which is not a typedef or a template type argument`` | ★ **된다**(`int** rr;`) |

- ★★★ **넷이 전부 「참조는 객체가 아니다」로 설명된다.** 배열의 원소도, 포인터가 가리키는 대상도\
  **객체여야 한다.** 참조는 **이름일 뿐**이라 그 자리에 못 들어간다.
- ★★ **④의 단서가 중요하다** — ``which is not a typedef or a template type argument``.\
  **직접 적을 수는 없지만 템플릿 안에서는 생길 수 있다**는 뜻이고,\
  그때 **참조 축약**(`T& &` → `T&`)이 일어난다. 그 규칙이 **전달 참조의 밑바탕**이다([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).
- ★ clang 은 **네 에러를 네 줄로** 낸다(g++ 는 후속 에러가 하나 더 붙는다).

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

### (3) ★★★ 기계어 — 한 명령도 다르지 않다

**언제 쓰나** — 「참조가 빠른가?」라는 말이 나올 때. **이 절이 그 질문을 끝낸다.**

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

`-O0` 에서도 같다.

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

- ★★★ **두 함수의 명령어 열이 한 글자도 다르지 않다** — `-O0` 에서도, `-O2` 에서도.\
  **참조도 포인터도 `%rdi` 에 주소를 받아 `mov (%rdi),%eax` 로 읽는다.**\
  ★ 주소·오프셋은 **흔들리는 칸**이라 근거로 쓰지 않는다(머리말 표). 근거는 **명령어 열**이다.
- ★★ 그러면 **무엇이 다른가** — 이름이다.

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

- **`_Z6by_refRi`** 대 **`_Z6by_ptrPi`** — `R` 은 reference, `P` 는 pointer다.\
  ★★ **타입 체계에서만 갈리고 코드 생성에서는 안 갈린다.** 링커는 이 둘을 **다른 함수**로 본다.
- ★★★ **「참조가 더 빠르다」가 틀리는 근거가 이것**이다 — **같은 코드**가 나온다.\
  참조가 사는 것은 속도가 아니라 **컴파일러가 막아 주는 것**(널·재결합·초기화 누락)이다.
- ★ 뒤집으면 **「참조는 공짜다」도 조심할 말**이다 — 주소를 넘기는 비용은 **그대로 있다.**\
  작은 값(`int`)을 `const int&` 로 받으면 **값 전달보다 느릴 수 있다**(간접 접근이 는다).\
  그 판단의 정본은 [목록의 **11번 주제**](../11-choosing-parameter-passing/)다.

### (4) 참조를 멤버로 두면 — 대입이 사라진다

**언제 쓰나** — 구조체에 참조를 넣고 싶을 때. **거의 항상 포인터가 답이다.**

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

- **`sizeof(HasRef) == 8`** — 포인터와 **같다**. 구현이 내부적으로 포인터를 쓴 것이다((3)과 같은 이야기).\
  ★ 표준이 그 크기를 **보장하지는 않는다.**
- ★★★ **`x = y;` 가 막힌다** — ``use of deleted function `HasRef& HasRef::operator=(const HasRef&)` `` +\
  ``non-static reference member `int& HasRef::r`, cannot use default assignment operator``.\
  **참조는 재결합이 없으니**((1)) **대입 연산자를 만들 방법이 없다.** 그래서 컴파일러가 **삭제**한다.
- ★★ **컨테이너에 못 넣는다.** `std::vector<HasRef>` 는 `push_back`·정렬·`erase` 가 전부 **대입을 쓴다.**\
  ★ 그래서 참조 멤버를 두는 순간 그 타입은 「**담을 수 없는 타입**」이 된다.
- ★ 고치는 법은 **포인터 멤버**나 **`std::reference_wrapper<int>`** 다(후자는 대입이 된다 — 재결합을 흉내 낸다).

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

### (5) ★★ 참조만 할 수 있는 것 — 임시의 수명 연장

**언제 쓰나** — 함수 매개변수를 `const T&` 로 받을 때. **왜 그게 되는지**가 여기 있다.

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

| 경우 | 임시가 언제 죽나 |
|---|---|
| A: `const Noisy& r = make(1);` | ★ **`r` 의 블록이 끝날 때** — 수명이 늘어났다 |
| B: `make(2);`(안 묶음) | **그 문장이 끝날 때**(세미콜론) |

- ★★★ **A 에서 `~Noisy(1)` 이 「블록 안」 출력 뒤에 찍혔다** — 임시가 **`r` 만큼 살았다**는 증거다.\
  이 규칙의 이름이 **수명 연장**이고, **`const T&`(와 `T&&`)에 묶었을 때만** 일어난다.
- ★★★ **포인터는 흉내조차 못 낸다.**

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

- ``error: taking address of rvalue [-fpermissive]`` — **임시의 주소를 못 얻는다.**\
  clang 은 ``error: taking the address of a temporary object of type 'Noisy' [-Waddress-of-temporary]`` 다.

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

- ★★★ **이것이 매개변수 설계의 근거다.** `f(const T& x)` 는 **임시도 받을 수 있고**,\
  `f(const T* x)` 는 **호출자가 변수를 따로 만들어야 한다.**\
  `f(std::string("hi"))` 가 되는 것이 그래서다.
- ★ **수명 연장에는 구멍이 많다** — 참조를 **반환**하거나 **멤버로 저장**하면 안 늘어난다.\
  정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다.

### (6) 널 참조 — 「가정」이지 「보장」이 아니다

**언제 쓰나** — 「참조는 널일 수 없다」를 얼마나 믿을지 정할 때.

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

- ★★★ **경고 문구가 정확히 말해 준다** — ``the compiler can assume that the address of `r` will never be NULL``.\
  「**없다**」가 아니라 「**없다고 가정하고 최적화한다**」다.
- ★ 경고 **둘**이다 — `-Waddress` 와 `-Wnonnull-compare`. `cc exit=0` 이고, 실행하면 이렇게 나온다.

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

clang 은 한 줄로 더 세게 말한다.

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

- ★★ ``reference cannot be bound to dereferenced null pointer in well-defined C++ code; comparison may be assumed to always evaluate to false`` —\
  「**제대로 된 코드라면 그럴 수 없다**」는 뜻이다.

그 가정을 깨면 UB 이고, **이 UB 는 도구가 본다.**

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

- ★★ **`runtime error: reference binding to null pointer of type 'int'`** — **묶는 그 줄**을 짚어 준다.\
  「읽을 때」가 아니라 **「묶을 때」가 이미 UB** 라는 것이 문구에 적혀 있다.
- ★ sanitizer 없이 돌리면 **아무 말 없이 죽는다**(`run exit=139`).

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

- ★ **마커를 `std::cerr` 로 찍었다.** stdout 과 섞으면 **죽을 때 버퍼가 날아가** 마커가 사라진다.
- ★ **UB 가 만든 값은 이 문서에 싣지 않았다.** 근거로 쓰는 것은 「**UBSan 이 묶는 줄을 짚었다**」와 「**`run exit=139`**」다.

### (7) 지역을 돌려주면 — 참조도 포인터도 **똑같이** 위험하다

**언제 쓰나** — 「참조가 더 안전하지 않나」를 의심할 때.

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

| 함수 | 경고 |
|---|---|
| `int& dangling_ref()` | ``warning: reference to local variable `local` returned  [-Wreturn-local-addr]`` |
| `int* dangling_ptr()` | ``warning: address of local variable `local` returned  [-Wreturn-local-addr]`` |

- ★★★ **경고 이름이 같다**(`-Wreturn-local-addr`). 문구만 `reference to` 대 `address of` 로 다르다.\
  **컴파일러는 둘을 같은 사고로 본다.**
- ★★ **`cc exit=0`** 이다 — **경고일 뿐 빌드는 된다.**
- ★★★ **그러므로 「참조가 안전하다」는 틀린 요약**이다. 참조가 막는 것은 「**널**」과 「**재결합**」뿐이고,\
  **댕글링은 그대로 난다.** 정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다.
- ★ 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의 `decltype(auto)` 댕글링이 **같은 경고**를 받는다 —\
  거기서는 **괄호 하나**가 이 경고를 불러냈다.

### (8) 인터페이스 — 「없음」을 타입으로 말할 수 있나

**언제 쓰나** — 함수 시그니처를 정할 때. **이 주제의 실무적 결론**이다.

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

- **`take_ptr(nullptr)`** 는 **통과**한다 — 포인터에게 **널은 값**이다.
- **`take_ref(nullptr)`** 는 **막힌다** — ``invalid initialization of non-const reference of type `int&` from an rvalue of type `std::nullptr_t` ``.
- ★★★ **그래서 시그니처가 문서가 된다** —\
  `void f(int& x)` 는 「**반드시 있다**」를, `void f(int* x)` 는 「**없을 수도 있다**」를 말한다.\
  ★ 호출자는 **`f(*p)` 를 쓰기 전에 `p` 를 검사해야 한다**는 것을 시그니처만 보고 안다.
- ★★ **`T*` 보다 나은 도구가 있다** —\
  ① **`std::optional<T>`**(값이 없을 수 있음 · 소유) — 목록의 **47번 주제** ·\
  ② **`std::optional<std::reference_wrapper<T>>`** 또는 **`T*`**(비소유 관찰자) ·\
  ③ 「참조를 재결합하고 싶다」면 **`std::reference_wrapper<T>`**.\
  ★ **이 문서는 ①②③을 던져 보지 않았다** — 정본이 다른 주제다.

### (9) 다섯 층 — 무엇이 표준이고 무엇이 도구인가

★★ **이 주제도 「표준」 칸이 두껍다** — 참조의 규칙은 전부 표준이 정한다.
구현이 갈리는 곳은 **참조를 어떻게 구현하느냐**(대개 포인터)와 **진단 문구**뿐이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **참조는 반드시 초기화**된다 · **재결합이 없다** · **참조의 배열·참조로의 포인터·참조로의 참조가 없다** · **`sizeof(참조)` 는 대상의 크기** · **참조 멤버가 대입 연산자를 삭제하는 것** · **`const T&` 가 임시의 수명을 늘리는 것** · **임시의 주소를 못 얻는 것** · **`nullptr` 를 `T&` 에 못 묶는 것** | 두 컴파일러의 진단·실행 출력이 같은 자리 | ★ **「참조가 널이 아니다」는 가정이지 검사가 아니다**((6)) |
| **조건부 표준** | 표준판이 있을 때만 | **rvalue 참조 `T&&` 는 C++11부터** — ★ **이 주제는 lvalue 참조만** 다룬다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | ★ **참조가 내부적으로 포인터로 구현되는 것** · `sizeof(HasRef) == 8` · 진단 문구 · 경고 이름(`-Waddress` 대 `-Wtautological-undefined-compare`) | `objdump` · `sizeof` | — |
| **미명시** | 몇 가지 중 하나 | ★ **참조가 저장 공간을 차지하는지** — 표준이 **정하지 않는다**(구현이 고른다) | (3)에서 **실제로는 차지한다**는 것만 관찰 | ★ `sizeof` 로는 **안 보인다**(대상 크기를 답하므로) |
| **UB** | 아무 일이나 | ★ **널 포인터를 역참조해 참조에 묶기**((6)) · **댕글링 참조 읽기**((7)) | UBSan 1줄 + `run exit=139` · `-Wreturn-local-addr` | ★ 댕글링 쪽은 **경고만 나고 `cc exit=0`** |

**「도구가 못 보는 것」을 층마다 — 전용 표**

| 사실 | g++ `-Wall -Wextra -pedantic` | clang 같은 플래그 | UBSan | 비고 |
|---|---|---|---|---|
| 참조가 못 하는 넷((2)) | **에러 5**(후속 1 포함) | **에러 4** | — | ★ 에러를 **몇 개로 세는가**가 다르다 |
| 참조 멤버의 대입((4)) | **에러 2** | **에러 1 + note 1** | — | 판정은 같다 |
| 임시의 주소((5)) | **에러 1**(`-fpermissive`) | **에러 1**(`-Waddress-of-temporary`) | — | 〃 |
| `&r == nullptr` 검사((6)) | ★ **경고 2** · `cc exit=0` | ★ **경고 1** · `cc exit=0` | — | ★ 경고 이름이 다르다 |
| ★ **널 참조 묶기**((6)) | ★★ **0건** | ★★ **0건** | ★ **1줄** · `run exit=139` | ★ **컴파일 시간에는 안 보인다** |
| 댕글링 반환((7)) | **경고 2** · `cc exit=0` | — | — | ★ 참조 판과 포인터 판이 **같은 경고 이름** |
| ★ **참조와 포인터의 기계어가 같다는 것**((3)) | — | — | — | ★ **`objdump` 로만 보인다** |

- ★★★ **이 주제에서 가장 자주 틀리는 것은 「참조가 안전하다」이고, 그 반례가 (7)이다.**\
  **참조가 막는 것은 「널」과 「재결합」뿐**이고 **댕글링은 그대로 난다.**

## 문법 — 형태와 규칙

### 형태

```cpp
/* ptr01.cpp */
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
```

규칙 불릿.

- **`T& r = obj;`** — 참조는 **반드시 초기화**된다. **선언과 결합이 한 문장**이다.
- **`r = x;`** 는 **재결합이 아니라 대입**이다 — `obj` 에 쓴다((1)).
- **`&r` 은 `&obj` 와 같다.** `sizeof(r)` 은 **`sizeof(T)`** 다.
- **참조의 배열 · 참조로의 포인터 · 참조로의 참조는 없다**((2)).\
  ★ 참조로의 참조는 **템플릿 안에서만** 생기고 **참조 축약**으로 접힌다.
- **참조 멤버는 복사 대입 연산자를 삭제한다**((4)) — 그 타입은 **컨테이너에 못 담는다.**
- **`const T& r = 임시;`** 는 **임시의 수명을 `r` 까지 늘린다**((5)). 포인터는 **임시의 주소를 못 얻는다.**
- **`T&` 에 `nullptr` 를 못 묶는다**((8)). **널은 포인터만의 값**이다.
- **참조도 댕글링한다**((7)) — 지역을 돌려주면 포인터와 **같은 경고**를 받는다.

### 금지 사례 — 던져서 받은 여섯

| 쓴 것 | 컴파일러 | 무엇이 나오나 |
|---|---|---|
| `int& r;` | g++ | ``error: `r` declared as reference but not initialized`` |
| `int& ar[2];` | g++ | ``error: declaration of `ar` as array of references`` |
| `int&* pr;` | g++ | ``error: cannot declare pointer to `int&` `` |
| `int& & rr;` | g++ | ``error: cannot declare reference to `int&`, which is not a typedef or a template type argument`` |
| 참조 멤버가 있는 구조체에 `x = y;` | g++ | ``error: use of deleted function `HasRef& HasRef::operator=(const HasRef&)` `` |
| `const Noisy* p = &make(3);` | g++ | ``error: taking address of rvalue  [-fpermissive]`` |
| 〃 | clang | ``error: taking the address of a temporary object of type 'Noisy'  [-Waddress-of-temporary]`` |
| `take_ref(nullptr)` | g++ | ``error: invalid initialization of non-const reference of type `int&` from an rvalue of type `std::nullptr_t` `` |

### 고를 것을 손으로 돌리는 순서

1. **「없을 수도 있나?」** — 있으면 **포인터**(또는 `std::optional`). 없으면 **참조**.
2. **「가리키는 대상을 바꿔야 하나?」** — 그러면 **포인터**(또는 `std::reference_wrapper`).
3. **「멤버로 저장하나?」** — 그러면 **포인터**. 참조 멤버는 **대입을 지운다**((4)).
4. **「배열·컨테이너에 담나?」** — **포인터**(참조의 배열은 없다).
5. **「임시를 받아야 하나?」** — **`const T&`**((5)). 포인터로는 **아예 안 된다.**
6. **「C API 와 주고받나?」** — **포인터**(C 에 참조가 없다).
7. 그 밖에는 **참조**가 기본값이다 — **널 검사를 안 써도 되고**, 호출부가 `&` 없이 깔끔하다.\
   ★ 단 **작은 값**(`int`·`double`)은 **값으로 받는 편이 낫다** — 정본은 [목록의 **11번 주제**](../11-choosing-parameter-passing/).

## 어디서 틀리나

### 1. ★★★ 「참조가 포인터보다 빠르다(느리다)」

**기계어가 한 명령도 다르지 않다**((3)) — `-O0` 에서도 `-O2` 에서도.\
다른 것은 **맹글링된 이름**(`Ri` 대 `Pi`)뿐이다. 차이는 **타입 체계**에 있다.

### 2. ★★★ 「참조는 안전하다」

**댕글링은 그대로 난다**((7)). 지역을 돌려주면 포인터와 **같은 경고**(`-Wreturn-local-addr`)를 받고,\
**`cc exit=0`** 이다. 참조가 막는 것은 「**널**」과 「**재결합**」뿐이다.

### 3. ★★★ 「`r = b;` 는 `r` 이 `b` 를 가리키게 한다」

아니다((1)). **`a` 에 `b` 의 값을 쓴다.** `&a == &r` 은 **계속 참**이다.\
★ 참조에는 **재결합이라는 연산 자체가 없다.**

### 4. ★★ 「참조는 널일 수 없다」

**컴파일러가 「없다고 가정」할 뿐**이다((6)). 경고 문구가 그렇게 적혀 있다 —\
``the compiler can assume that the address of `r` will never be NULL``.\
★ `*(int*)nullptr` 를 묶으면 **UB** 이고 **컴파일 시간에는 0건**이다. UBSan 만 본다.

### 5. ★★ 「`sizeof(참조)` 가 4니까 공간을 안 쓴다」

**아니다**((1)·(3)). `sizeof` 는 **대상의 크기를 답하도록** 표준이 정했을 뿐이고,\
**실제로는 포인터로 구현된다**(`sizeof(HasRef) == 8`).\
★ **표준은 참조가 저장 공간을 쓰는지 정하지 않는다** — 미명시 칸이다((9)).

### 6. ★★ 「구조체 멤버로 참조를 두면 깔끔하다」

**대입 연산자가 사라진다**((4)). `std::vector` 에 못 담고, 정렬·`erase` 도 못 한다.\
★ 포인터나 **`std::reference_wrapper`** 를 쓴다.

### 7. ★★ 「`const T&` 로 받으면 항상 이득이다」

**작은 값은 손해일 수 있다**((3)) — 간접 접근이 는다.\
★ 판단의 정본은 [목록의 **11번 주제**](../11-choosing-parameter-passing/)(매개변수 전달 방식 고르기)다.

### 8. ★ 「참조를 못 만들면 포인터로 우회하면 된다」

**임시는 그것도 안 된다**((5)). `&make(3)` 은 **컴파일 에러**다 —\
**임시를 받는 것은 `const T&` 만의 능력**이다.

### 9. ★ 「참조로의 참조는 아예 없다」

**직접 적을 수만 없다**((2)의 ④). 에러 문구에 ``not a typedef or a template type argument`` 가 붙어 있다 —\
템플릿 안에서는 생기고 **참조 축약**으로 접힌다. 그것이 **전달 참조의 밑바탕**이다([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).

### 10. 「참조는 C 의 포인터를 대체한다」

**세 자리에서는 못 한다** — 널 · 재결합 · **C API 경계**.\
★ 포인터 산술·배열 감쇠도 참조에는 없다 — 그쪽 정본은 C 갈래\
[`15번`](../../../c/syntax/15-pointer-arithmetic-and-indexing/)·[`16번`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/)이다.

## 구현 세부사항 대 언어 보장

| 사실 | 누가 보장하나 |
|---|---|
| **참조는 반드시 초기화**되고 **재결합이 없는** 것 | **언어** |
| **참조의 배열·참조로의 포인터·참조로의 참조가 없는** 것 | **언어** |
| **`sizeof(참조)` 가 대상의 크기**인 것 | **언어** |
| **참조 멤버가 복사 대입을 삭제하는** 것 | **언어** |
| **`const T&` 가 임시의 수명을 늘리는** 것 | **언어** |
| **임시의 주소를 못 얻는** 것 · **`nullptr` 를 `T&` 에 못 묶는** 것 | **언어** |
| **널 포인터를 역참조해 참조에 묶는 것이 UB** 인 것 | **언어** |
| ★ **참조가 저장 공간을 차지하는지** | ★ **미명시** — 표준이 정하지 않는다. 이 구현에서는 **차지한다**((3)·(4)) |
| ★ **`by_ref` 와 `by_ptr` 의 기계어가 같은 것** | ★ **관찰이다.** 최적화기가 바뀌면 달라질 수 있다 — 「**타입 체계의 차이지 코드의 차이가 아니다**」가 결론이고 **명령어 하나하나가 결론이 아니다** |
| ★ **맹글링 `_Z6by_refRi` / `_Z6by_ptrPi`** | ★ **플랫폼 ABI**(Itanium C++ ABI) |
| 진단 문구 · 경고 이름 · **에러를 몇 개로 세는가**((2)에서 g++ 5, clang 4) | **컴파일러 구현** |

## 언제 쓰고 언제 안 쓰나

**참조를 먼저 고르는 이유 셋**\
① **「반드시 있다」를 타입으로 말한다**((8)) — 호출자도 구현자도 널 검사를 안 쓴다.\
② **재결합이 없어 읽기 쉽다** — 한 번 정해지면 그 이름은 그 객체다.\
③ **임시를 받을 수 있다**((5)) — `f(std::string("hi"))` 가 된다.

**포인터를 반드시 써야 하는 자리 셋**\
① **없을 수 있을 때**(널) · ② **가리키는 대상을 바꿔야 할 때**(재결합) ·\
③ **멤버·배열·컨테이너에 담을 때**((2)·(4)). ★ **C API 경계**도 여기에 든다.

**참조를 재결합하고 싶어지면** — **`std::reference_wrapper<T>`**.\
대입이 되고 컨테이너에 담긴다. ★ **이 문서는 안 던졌다.**

**값으로 받는 편이 나을 때** — 작은 타입(`int`·`double`·포인터 하나).\
★ 정본은 [목록의 **11번 주제**](../11-choosing-parameter-passing/)다.

## 핵심 문장

1. **참조는 또 하나의 이름이다** — `r = b;` 는 재결합이 아니라 **`a` 에 쓰는 것**이다.
2. **기계어는 같다** — 차이는 타입 체계에 있고, `nm` 이 `Ri` 와 `Pi` 로 그것을 보여 준다.
3. **참조가 막는 것은 「널」과 「재결합」뿐이다** — **댕글링은 그대로 난다.**
4. **「참조는 널이 아니다」는 가정이지 검사가 아니다** — 깨면 UB 이고 컴파일 시간에는 0건이다.
5. **임시를 받는 것은 `const T&` 만의 능력이다** — 포인터는 `&임시` 가 컴파일 에러다.
6. **참조 멤버는 대입을 지운다** — 그 타입은 컨테이너에 못 담는다.

## 관련 자료

- C 갈래 [`14-pointers-address-dereference-and-pointer-types/`](../../../c/syntax/14-pointers-address-dereference-and-pointer-types/) —\
  ★ **포인터가 무엇인가**의 정본. 주소·역참조·포인터 타입은 전부 거기다.\
  여기는 **C 에 없는 쪽**(참조)만.
- C 갈래 [`15-pointer-arithmetic-and-indexing/`](../../../c/syntax/15-pointer-arithmetic-and-indexing/)·[`16-array-pointer-decay-and-function-parameters/`](../../../c/syntax/16-array-pointer-decay-and-function-parameters/) —\
  **참조에는 없는 이야기**(산술·감쇠). 참조는 「이름」이라 더할 것이 없다.
- C 갈래 [`19-void-pointer-null-pointer-and-null/`](../../../c/syntax/19-void-pointer-null-pointer-and-null/) — 널 포인터의 정본.
- [**05번 형제**](../05-auto-and-decltype-type-deduction/) — `auto&`·`auto&&` 가 **무엇을 붙이는지**.\
  거기 (6)의 댕글링이 **이 주제의 (7)과 같은 경고**를 받는다.
- [목록의 **08번 주제**](../08-value-categories-lvalue-prvalue-xvalue/)(값 범주) — **어떤 식에 참조가 묶이나**. `T&` 는 lvalue 에만 묶인다.
- [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)(rvalue 참조·`move`·`forward`) — **`T&&` 와 참조 축약**.\
  ★ (2)의 ④에 붙은 단서가 거기로 이어진다.
- [목록의 **10번 주제**](../10-const-correctness/)(`const` 정확성) — `const T&` 를 **설계 도구**로 쓰는 법.
- [목록의 **11번 주제**](../11-choosing-parameter-passing/)(매개변수 전달 방식) — ★ **값·`const&`·`&&` 중 무엇으로 받나**의 정본.\
  (3)의 「참조가 공짜는 아니다」가 거기서 결론난다.
- [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)(댕글링 참조와 수명 연장) — ★ (5)·(7)의 정본.\
  **수명 연장이 안 되는 자리**(반환·멤버 저장·범위 for)가 거기 있다.
- 목록의 **47번 주제**(`optional`·`variant`) — 「없을 수 있음」을 **소유와 함께** 말하는 도구.

## 용어 풀이

> **참조(reference)** — 이미 있는 객체에 붙이는 또 하나의 이름. **초기화 필수 · 재결합 불가.**

> **재결합(rebinding)** — 가리키는 대상을 바꾸는 것. **포인터에만 있다.**

> **참조 축약(reference collapsing)** — 템플릿 안에서 `T& &` 같은 것이 생기면 `T&` 로 접히는 규칙.\
> 전달 참조의 밑바탕이다([목록의 **09번 주제**](../09-rvalue-references-move-and-forward/)).

> **수명 연장(lifetime extension)** — `const T&`/`T&&` 에 임시를 묶으면 임시가 그 참조만큼 사는 것.

> **댕글링(dangling)** — 죽은 객체를 가리키는 참조·포인터. **읽으면 UB.**

> **`std::reference_wrapper<T>`** — 참조를 **객체로 감싼 것**. 대입이 되고 컨테이너에 담긴다.

> **맹글링(name mangling)** — 타입 정보를 섞어 링커용 이름을 만드는 것.\
> `_Z6by_refRi` 의 `R` 이 reference, `_Z6by_ptrPi` 의 `P` 가 pointer다.

## 더 들어가면

- **rvalue 참조 `T&&`** — C++11. 이 문서는 **lvalue 참조만** 던졌다. 정본은 [목록의 **09번 주제**](../09-rvalue-references-move-and-forward/).
- **`std::reference_wrapper` 로 재결합 흉내 내기** — ★ **이 문서는 안 던졌다.**
- **수명 연장이 안 되는 자리** — 참조를 **반환**할 때 · **멤버로 저장**할 때 ·\
  **범위 for 의 임시**(C++23 에서 일부 고쳐졌다). ★ 이 문서는 **블록 안 판만** 던졌다.\
  정본은 [목록의 **30번 주제**](../30-dangling-references-and-lifetime-extension/)다.
- **참조를 멤버로 둔 타입의 이동 연산** — 복사 대입만 던졌다. 이동도 같은 이유로 삭제된다. ★ 안 던졌다.
- **비트필드로의 참조** — 못 만든다(프록시가 필요하다). 형제 [`05번`](../05-auto-and-decltype-type-deduction/)의\
  `vector<bool>` 프록시와 **같은 집안**이다. ★ 이 문서는 안 던졌다.
- **`-O1`·`-O3`·`-Os` 에서의 기계어** — (3)은 **`-O0` 과 `-O2` 두 수준만** 던졌다.\
  결론이 「같다」이므로 갈릴 자리를 일부러 찾자면 **더 큰 함수**로 가야 한다.
