# c/syntax/05 — 명시 캐스트와 포인터 변환: 내가 대놓고 바꾸는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Cast operator (C)](https://en.cppreference.com/w/c/language/cast) · [cppreference — Pointer conversions](https://en.cppreference.com/w/c/language/conversion) · [GCC 13 Optimize Options — `-fstrict-aliasing`](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html)
> **실행 검증** — 이 문서의 모든 출력·경고·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 블록은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준 + sanitizer 로 돌렸다.** 한 수준만 돌린 결과는 싣지 않는다.\
> 대조용으로 `clang 18.1.3` 을 쓴 자리는 그 자리에 밝혔다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> **버전** — 캐스트·포인터 변환 규칙은 C89 부터 같다. `intptr_t`/`uintptr_t` 는 **C99부터**이고 **선택 사항**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> **경계** — 「엄격한 앨리어싱 규칙 자체」는 목록의 **55번 주제**가 정본이다. 여기서는 **캐스트가 그 규칙을 어기는 자리**까지만 쓴다.\
> 「`void *`·`NULL`」의 정본은 목록의 **19번 주제**, 「`const` 의 계약」은 목록의 **31번 주제**다.

## 한눈에 — 쉽게 말하면

**캐스트에는 두 종류가 있다. 값을 바꾸는 것과, 값은 그대로 두고 「이렇게 읽어라」고 말하는 것.**

[03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 「컴파일러가 몰래 바꾸는 것」이었다면 이 주제는 「**내가 대놓고 바꾸는 것**」이다.\
대놓고 하기 때문에 **컴파일러가 더 이상 말려 주지 않는다** — 그게 이 주제의 위험 전부다.

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **환전** — 원화를 달러로 바꾼다 | **값 변환 캐스트** — `(int)3.9`·`(long)i`. 숫자가 실제로 바뀐다 |
| **라벨 갈아 붙이기** — 상자 내용은 그대로, 겉에 쓴 이름만 바꾼다 | **포인터 캐스트** — `(char *)pi`. 비트는 하나도 안 바뀐다 |
| 라벨을 갈아 붙여도 **상자를 안 열면 아무 일도 안 난다** | 포인터 캐스트 자체는 대개 조용하다 |
| **상자를 열었을 때** 내용이 라벨과 다르면 사고 | **역참조**가 UB 가 되는 자리 |
| 「알고 하는 겁니다」라고 서명하면 **경고가 꺼진다** | 캐스트가 `-Wconversion`·`-Wdiscarded-qualifiers` 를 끈다 |

- 값 변환 캐스트는 **기계어 명령을 만든다.** 포인터 캐스트는 **명령을 하나도 안 만든다.**
- 그래서 「캐스트했으니 안전하다」는 거꾸로다 — **캐스트는 안전장치가 아니라 안전장치를 끄는 스위치**다.

```text
   두 종류의 캐스트

   (int)3.9         값이 3.9 -> 3 으로 바뀐다          [환전]
                    cvttsd2si 라는 명령이 생긴다

   (char *)pi       비트가 하나도 안 바뀐다             [라벨]
                    명령이 안 생긴다 (mov 한 줄은 ABI 때문)

   -> 전자는 "무엇을 하나"가 분명하고
      후자는 "무슨 일이 일어나나"가 ★ 그 뒤 역참조에서 결정된다
```

> **캐스트(cast)** — `(타입)식` 형태로 식의 타입을 바꾸라고 명시하는 연산자.\
> 예: `(int)3.9` 는 `3` 이라는 **새 값**을 만든다. 원래 `3.9` 는 그대로 있다.

> **역참조(dereference)** — 포인터가 가리키는 곳의 값을 실제로 읽거나 쓰는 것(`*p`·`p->x`·`p[0]`).\
> 예: `int *p = (int *)(buf+1);` 까지는 아무 일도 안 나고, `*p = 1;` 에서 사고가 난다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. 캐스트는 **무엇을 바꾸고 무엇을 안 바꾸는가** — 기계어로 확인할 수 있는가.
2. 포인터 캐스트에서 **UB 가 되는 자리는 캐스트인가 역참조인가** — 도구는 어디서 잡는가.
3. 캐스트가 **끄는 경고**는 무엇이고, 그중 **끄면 안 되는 것**은 무엇인가.

## 동작 방식

### (1) 캐스트가 실제로 명령을 만드나 — 어셈블리로 본다

**언제 쓰나** — 「이 캐스트가 무슨 일을 하나」가 헷갈릴 때. 이 주제의 **네 번째 창**이다.

```c
char *   c_ptr (int *p)   { return (char *)p; }     /* 포인터 캐스트 — 해석만 바꾼다 */
unsigned c_u   (int i)    { return (unsigned)i; }   /* 부호 해석만 바꾼다 */
long     c_long(int i)    { return (long)i; }       /* 값 보존 + 폭 확장 */
int      c_int (double d) { return (int)d; }        /* ★ 값을 바꾼다 */
```

`gcc -std=c17 -O1 -S -masm=intel asm2.c -o -` 에서 지시자(`.` 로 시작하는 줄)를 걷어낸 것이다.

```text
c_ptr:
	endbr64
	mov	rax, rdi
	ret
c_u:
	endbr64
	mov	eax, edi
	ret
c_long:
	endbr64
	movsx	rax, edi
	ret
c_int:
	endbr64
	cvttsd2si	eax, xmm0
	ret
```

```text
   캐스트 네 개가 만든 명령

   (char *)p     mov rax, rdi          <- 인자를 반환 레지스터로 옮긴 것뿐.
                                          ★ 캐스트 때문에 생긴 명령이 0개다

   (unsigned)i   mov eax, edi          <- 같다. 비트가 안 바뀐다

   (long)i       movsx rax, edi        <- ★ 부호 확장 명령이 하나 생겼다
                                          32비트 -1 을 64비트 -1 로 만든다

   (double->int) cvttsd2si eax, xmm0   <- ★ 진짜 변환 명령
                                          "truncate toward zero" 가 이름에 있다
```

그림 해설 (한 단계씩):

- **포인터 캐스트는 명령을 안 만든다.** `mov rax, rdi` 는 「1번 인자 레지스터 → 반환 레지스터」라는 호출 규약의 몫이지 캐스트의 몫이 아니다.
- **`(unsigned)i` 도 명령을 안 만든다.** 비트가 그대로이고 **읽는 규칙만** 바뀐다.
- **`(long)i` 는 `movsx` 하나를 만든다.** 폭이 넓어지므로 부호 비트를 채워야 한다 — **비트가 바뀐다.**
- **`(int)d` 는 `cvttsd2si` 를 만든다.** 이름의 `tt` 가 **truncate toward zero**(0 쪽으로 자름)다 —\
  [04번 형제](../04-floating-point-types-and-conversions/)가 `(int)-3.9 == -3` 으로 관찰한 것이 명령 이름에 박혀 있다.

비용 — 없다. 컴파일만 해 보면 된다.

### (2) 값을 바꾸는 캐스트 대 해석을 바꾸는 캐스트

**언제 쓰나** — 「비트를 그대로 두고 다른 타입으로 읽고 싶다」는 생각이 들 때. **거기가 함정이다.**

```text
(int)3.9           = 3
(unsigned)-1       = 4294967295
세 포인터가 같은 주소인가: 1
비트를 float 로 읽으면 3.14159274
그런데 (float)x 는   1078530048.00000000   <- 값 변환이다
(intptr_t) 왕복 == 원본? 1
sizeof: void*=8 int=4 intptr_t=8
void* 왕복 == 원본? 1  (캐스트를 안 썼다)
```

```text
   int x = 1078530011;   (= 0x40490FDB)

   ① (float)x                    "값" 을 float 로
       1078530011 -> 1078530048.0        <- 유효 비트 24개라 반올림됐다

   ② memcpy 로 비트를 옮김        "비트" 를 float 로
       0x40490FDB -> 3.14159274          <- ★ 완전히 다른 답

   -> 같은 x 에서 두 값이 나온다. 무엇을 원하는지 먼저 정해야 한다.
```

그림 해설 (한 단계씩):

- **`(float)x` 는 값을 옮긴다.** `1078530011` 을 `float` 로 담느라 반올림돼 `1078530048.0` 이 됐다([04번 형제](../04-floating-point-types-and-conversions/)의 `2^24` 경계).
- **비트를 그대로 읽으면 `3.14159274`** 다. 이걸 **타입 펀닝**이라고 부른다.
- 비트를 옮기는 **이식 가능한 방법은 `memcpy`** 다. `*(float *)&x` 는 (4)에서 보듯 UB 다.
- `void *` 는 **캐스트 없이** 오간다 — 그것이 `void *` 가 특별한 이유다.

> **타입 펀닝(type punning)** — 같은 메모리를 다른 타입으로 읽어 비트를 재해석하는 것.\
> 예: `int` 로 쓴 `0x40490FDB` 를 `float` 로 읽어 `3.14159274` 를 얻는 것.

비용 — `memcpy` 는 **공짜다.** (5)에서 어셈블리로 확인한다.

### (3) 정수 ↔ 포인터 — `intptr_t` 가 있는 이유

**언제 쓰나** — 주소를 정수로 찍거나, 포인터에 태그 비트를 심을 때.

```text
(intptr_t) 로 왕복 == 원본? 1
(int)      로 왕복 == 원본? 0
sizeof: void*=8 int=4 intptr_t=8 uintptr_t=8
```

```text
   void *p  (64비트)
   +--------------------------------+
   | 0x00007ffd....                 |
   +--------------------------------+
        |                    |
        | (intptr_t)         | (int)
        v                    v
   +--------------------------------+   +----------------+
   | 64비트 정수 — 전부 담긴다       |   | 32비트 — ★ 잘렸다 |
   +--------------------------------+   +----------------+
        |                                    |
        | 되돌리면                            | 되돌리면
        v                                    v
     원본과 같다 (1)                      원본이 아니다 (0)
```

그림 해설 (한 단계씩):

- `sizeof(void *)` 는 8, `sizeof(int)` 는 4다. **`int` 에 포인터를 담으면 절반이 사라진다.**
- `intptr_t`/`uintptr_t` 는 「**`void *` 를 담았다 되돌릴 수 있는 정수 타입**」이다. 그래서 왕복이 된다.
- 표준이 보장하는 것은 **`void *` → `intptr_t` → `void *`** 왕복이다. 반대 방향(임의의 정수 → 포인터)은 보장이 아니다.
- ★ **`intptr_t` 는 선택 사항이다.** 「포인터를 담을 수 있는 정수 타입이 있는 구현」에만 있다. 이 환경에는 있다.

비용 — 없다. 다만 **`uintptr_t` 를 쓰는 편**이 낫다(비트 연산에 음수가 안 끼어든다).

### (4) 포인터 캐스트는 조용하고, 역참조가 시끄럽다 — 정렬 위반

**언제 쓰나** — `char` 버퍼를 다른 타입으로 읽을 때. 네트워크·파일 파서의 단골 자리다.

```c
char buf[16] = {0};
int *p = (int *)(buf + 1);              /* 캐스트만 하고 */
printf("A: 캐스트 통과 (p=buf+1, 정렬 안 맞음)\n");
printf("B: 포인터 비교도 된다: %d\n", (char *)p == buf + 1);
(void)p;                                 /* ★ 역참조는 안 한다 */
printf("C: 끝까지 아무 말도 없었다\n");
```

```text
=== 캐스트만, 역참조 없음 : ubsan ===
A: 캐스트 통과 (p=buf+1, 정렬 안 맞음)
B: 포인터 비교도 된다: 1
C: 끝까지 아무 말도 없었다
exit=0
```

역참조를 더하면 **같은 sanitizer 가 말을 한다.**

```text
=== 역참조까지 : ubsan (recover 허용) ===
A: 캐스트 통과
align3.c:7:8: runtime error: store to misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
B: 썼다
align3.c:9:5: runtime error: load of misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
C: 읽으면 0x41424344
exit=0
```

```text
   char buf[16];      주소가 4의 배수라고 하자

   buf+0  buf+1  buf+2  buf+3  buf+4 ...
   +-----+-----+-----+-----+-----+
   |     |  ★  |     |     |     |
   +-----+-----+-----+-----+-----+
            ^
            (int *) 로 캐스트한 자리 — 4의 배수가 아니다

   캐스트     : 조용하다            <- 도구가 아무 말도 안 한다
   *p = ...   : ★ misaligned store  <- 여기서 잡힌다
   *p 읽기    : ★ misaligned load
```

그림 해설 (한 단계씩):

- **`-fsanitize=undefined` 의 기본 집합에 `alignment` 검사가 들어 있다.** [04번 형제](../04-floating-point-types-and-conversions/)의 `float-cast-overflow` 와 달리 따로 켤 필요가 없다.
- **잡는 자리는 역참조**다. 캐스트만 하고 끝내면 exit 0 이고 한 줄도 안 나온다.
- ★ 그런데 **표준의 문장은 「변환 자체가 정의되지 않는다」고 말한다**(정렬이 더 엄한 타입으로 바꿀 때).\
  **도구가 잡는 자리와 표준이 금지하는 자리가 어긋난다** — 「도구가 조용하다」를 「표준이 허용한다」로 읽으면 안 된다.
- x86-64 는 정렬이 안 맞아도 **그냥 돈다.** 그래서 sanitizer 없이는 증상이 아예 없다.
- **이식 가능한 답은 `memcpy`** 다. `-O0`·`-O2` 어느 쪽에서도 같은 값을 준다.

비용 — `memcpy` 로 바꾸는 비용은 0이다((5) 참조).

### (5) 엄격한 앨리어싱 — 최적화 수준이 답을 바꾼다 ★★

**언제 쓰나** — `*(다른타입 *)&x` 를 쓰고 싶어질 때마다. **이 주제에서 가장 위험한 자리다.**

```c
int alias_test(int *pi, float *pf) {
    *pi = 1;
    *pf = 2.0f;        /* 타입이 달라 못 겹친다고 가정한다 */
    return *pi;        /* 그 가정 위에서는 1 로 접을 수 있다 */
}
int r = alias_test(&x, (float *)&x);   /* ★ 같은 객체를 두 타입으로 넘긴다 */
```

**다섯 최적화 수준 × 두 플래그로 돌렸다.**

```text
-O0  strict : alias_test = 1073741824 x          = 1073741824 
-O0  no-str : alias_test = 1073741824 x          = 1073741824 
-O1  strict : alias_test = 1073741824 x          = 1073741824 
-O1  no-str : alias_test = 1073741824 x          = 1073741824 
-O2  strict : alias_test = 1 x          = 1073741824 
-O2  no-str : alias_test = 1073741824 x          = 1073741824 
-O3  strict : alias_test = 1 x          = 1073741824 
-O3  no-str : alias_test = 1073741824 x          = 1073741824 
-Os  strict : alias_test = 1 x          = 1073741824 
-Os  no-str : alias_test = 1073741824 x          = 1073741824 
```

**어셈블리로 보면 무슨 일이 있었는지가 한 줄로 드러난다.**

```text
=== -O2 strict ===
alias_test:
	endbr64
	mov	DWORD PTR [rdi], 1
	mov	eax, 1
	mov	DWORD PTR [rsi], 0x40000000
	ret
=== -O2 -fno-strict-aliasing ===
alias_test:
	endbr64
	mov	DWORD PTR [rdi], 1
	mov	DWORD PTR [rsi], 0x40000000
	mov	eax, DWORD PTR [rdi]
	ret
```

```text
   strict (기본)                       -fno-strict-aliasing
   +-----------------------------+    +-----------------------------+
   | mov [rdi], 1                |    | mov [rdi], 1                |
   | mov eax, 1        ★ 상수     |    | mov [rsi], 0x40000000       |
   | mov [rsi], 0x40000000       |    | mov eax, [rdi]    ★ 다시 읽음 |
   | ret                         |    | ret                         |
   +-----------------------------+    +-----------------------------+
     "float 로 쓴 것이 int 를 건드릴      "혹시 모르니 메모리에서 다시
      리 없다" -> 읽지도 않는다            읽는다"
```

그림 해설 (한 단계씩):

- **`mov eax, 1` 과 `mov eax, DWORD PTR [rdi]`** — 한 명령 차이다. 앞엣것은 **메모리를 안 읽는다.**
- 순서까지 바뀌었다 — strict 쪽은 `mov eax, 1` 이 **`[rsi]` 에 쓰기 전에** 놓였다.
- **`-O0`·`-O1` 에서는 안 갈린다.** 「테스트는 디버그 빌드로 돌리고 운영은 `-O2`」인 팀에서 그대로 사고가 된다.
- ★ **`-Wall -Wextra` 는 이것을 한 줄도 말하지 않는다.** 플래그별로 세어서 확인했다.

```text
[] -O2 경고 0 건
[-Wall] -O2 경고 0 건
[-Wextra] -O2 경고 0 건
[-Wall -Wextra] -O2 경고 0 건
[-Wall -Wextra -Wstrict-aliasing=2] -O2 경고 1 건
```

```text
-Wstrict-aliasing=1 : 1 건
-Wstrict-aliasing=2 : 1 건
-Wstrict-aliasing=3 : 0 건
```

- ★★ **`-Wall` 이 켜는 기본 수준은 3이고, 그 수준은 이 위반을 놓친다.** `=2` 로 낮춰야 잡힌다.\
  「`-Wstrict-aliasing` 이 `-Wall` 에 있다」는 맞지만 **「그래서 잡힌다」는 틀렸다.**
- **sanitizer 는 둘 다 조용하다.**

```text
=== ubsan ===
alias_test = 1
x          = 1073741824
exit=0
=== asan ===
alias_test = 1
x          = 1073741824
exit=0
```

- **UBSan 도 ASan 도 한 줄도 안 낸다.** 이 갈래에서 **도구가 가장 못 보는 UB** 다.
- clang 18.1.3 도 `-O2` 에서 **`1`** 을 냈고 `-Wall -Wextra` 로 경고 **0건**이었다.

비용 — **`memcpy` 로 바꾸면 명령이 똑같다.** 공짜다.

```c
float pun_cast(int x)   { return *(float *)&x; }          /* ★ UB */
float pun_memcpy(int x) { float f; memcpy(&f, &x, sizeof f); return f; }
```

```text
pun_cast:
	endbr64
	movd	xmm0, edi
	ret
pun_memcpy:
	endbr64
	movd	xmm0, edi
	ret
```

- **두 함수의 기계어가 한 글자도 다르지 않다.** 「성능 때문에 캐스트를 쓴다」는 근거가 여기서 사라진다.

> **엄격한 앨리어싱(strict aliasing)** — 서로 호환되지 않는 타입의 두 포인터는 같은 객체를 가리키지 않는다고 컴파일러가 가정해도 좋다는 규칙.\
> 예: `int *` 와 `float *` 가 같은 곳을 가리키면 그 가정이 깨져 **읽기 자체가 생략된다.**\
> 정본은 목록의 **55번 주제**. 여기서는 **캐스트가 그 규칙을 어기는 자리**만 본다.

### (6) `const` 를 캐스트로 떼면

**언제 쓰나** — 낡은 API 가 `char *` 를 받는데 내 값이 `const char *` 일 때.

```c
const int frozen = 7;
int *bad = (int *)&frozen;     /* 캐스트로 const 를 뗀다 */
*bad = 99;                     /* ★ 원래 객체가 const 다 -> UB */
printf("*bad = %d, frozen = %d\n", *bad, frozen);
```

```text
-O0  : *bad = 99, frozen = 99
-O1  : *bad = 99, frozen = 7
-O2  : *bad = 99, frozen = 7
-O3  : *bad = 99, frozen = 7
-Os  : *bad = 99, frozen = 7
```

```text
   같은 메모리, 같은 소스, 두 개의 답

   -O0                          -O1 이상
   +----------------------+     +----------------------+
   | frozen 을 메모리에서  |     | frozen 은 7 이라고   |
   | 다시 읽는다          |     | ★ 컴파일 시간에 박았다|
   |   -> 99              |     |   -> 7               |
   +----------------------+     +----------------------+
        *bad 는 둘 다 99 다 — 한 변수가 두 값을 갖는다
```

그림 해설 (한 단계씩):

- **`-O0` 은 99, `-O1` 이상은 7.** 같은 객체를 두 이름으로 읽었는데 답이 다르다.
- 「경계선이 `-O2` 가 아니라 `-O1`」이다 — **최적화 수준을 둘만 돌리면 못 잡는다.**
- **UBSan 이 조용하다.**

```text
--- ubsan ---
*bad = 99, frozen = 7
exit=0
```

- 캐스트가 경고를 껐다는 것도 세어서 확인했다.

```text
[-Wall] 0 건
[-Wextra] 0 건
[-Wall -Wextra] 0 건
[-Wall -Wextra -Wcast-qual] 1 건
```

  캐스트를 빼면 `-Wall` 없이도 나온다.

```text
const3.c:1:44: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
```

- ★ **원래 객체가 `const` 가 아니면 떼고 써도 정의된다.** `const int *` 를 받았지만 그 대상이 보통 변수면 괜찮다.\
  **UB 인지 아닌지가 「포인터의 타입」이 아니라 「원래 객체가 무엇으로 선언됐나」에 달렸다.**
- 문자열 리터럴은 더 확실하다 — `(char *)"hello"` 에 쓰면 **세그멘테이션 오류**다(`exit=139`).\
  ASan 은 이것을 `SEGV ... caused by a WRITE memory access` 로 잡았다.

비용 — `-Wcast-qual` 을 켜면 이 캐스트가 전부 드러난다. 켜는 것이 옳다.

### (7) 함수 포인터 캐스트는 따로다

**언제 쓰나** — 콜백 테이블에 시그니처가 다른 함수를 우겨 넣고 싶을 때.

```text
##### -O0 #####
정상 호출        : 5
왕복 후 호출     : 5 (포인터 같음? 1)
틀린 시그니처로  : 2109177954   <- ★ UB
exit=0
##### -O2 #####
정상 호출        : 5
왕복 후 호출     : 5 (포인터 같음? 1)
틀린 시그니처로  : 2   <- ★ UB
exit=0
```

`-O0` 을 세 판 돌리면 **값이 매번 다르다.**

```text
틀린 시그니처로  : -10496158   <- ★ UB
틀린 시그니처로  : -916449438   <- ★ UB
틀린 시그니처로  : -623433806   <- ★ UB
```

```text
   함수 포인터 캐스트 두 가지

   ① 다른 함수 포인터 타입으로 바꿨다 되돌린다
        Fn2 -> FnV -> Fn2 -> 호출
        -> ★ 정의된다. 값이 보존된다 (실측: 왕복 후 5)

   ② 다른 시그니처로 바꿔서 ★ 호출한다
        Fn2 -> Fn1 -> f1(2)
        -> ★ UB. -O0 은 매 실행 다른 값, -O2 는 2
```

그림 해설 (한 단계씩):

- **왕복은 보장된다.** 함수 포인터를 다른 함수 포인터 타입으로 바꿨다 되돌리면 원래 값이다.
- **그 타입으로 호출하면 UB** 다. `-O2` 에서 `add` 가 인라인되면서 gcc 가 이렇게 말했다.

```text
fnp.c:3:34: warning: ‘b’ is used uninitialized [-Wuninitialized]
```

  **소스에 초기화 안 한 변수가 한 개도 없는데** 이런 경고가 나온다 — 인자가 하나 모자란 결과다.
- ★ **함수 포인터와 객체 포인터(`void *` 포함) 사이의 변환은 표준이 보장하지 않는다.** POSIX 의 `dlsym` 이 그래서 골치인 자리다.
- 경고는 **`-Wextra` 에 있다.** `-Wall` 이 아니다.

```text
[] 0 건
[-Wall] 0 건
[-Wextra] 1 건
[-Wall -Wextra] 1 건
```

- **gcc 의 UBSan 에는 이 검사가 아예 없다.**

```text
gcc: error: unrecognized argument to ‘-fsanitize=’ option: ‘function’
```

  clang 은 있고, 켜면 잡는다.

```text
fnp.c:20:58: runtime error: call to function add through pointer to incorrect function type 'int (*)(int)'
```

비용 — 없다. **하지 말아야 할 일**을 안 하면 된다.

### (8) 캐스트가 끄는 경고와 못 끄는 경고

**언제 쓰나** — 경고를 없애려고 캐스트를 넣기 직전에.

같은 코드를 **암시 변환**과 **명시 캐스트** 두 벌로 만들어 세었다.

```text
[-Wall -Wextra]  암시 0 건  /  캐스트 0 건
[-Wall -Wextra -Wconversion]  암시 2 건  /  캐스트 0 건
```

```text
warn.c:8:15: warning: conversion from ‘long unsigned int’ to ‘char’ may change value [-Wconversion]
warn.c:9:15: warning: conversion from ‘long unsigned int’ to ‘int’ may change value [-Wconversion]
```

- **2건 → 0건.** 캐스트가 한 일은 **값을 안전하게 만든 것이 아니라 경고를 없앤 것**이다.

그런데 **안 꺼지는 것도 있다.**

```text
ptrint3.c:1:51: warning: cast from pointer to integer of different size [-Wpointer-to-int-cast]
```

```text
[플래그 없음] ptrint3:
1
```

```text
   캐스트가 끄는 것                     캐스트가 못 끄는 것
   +----------------------------+      +----------------------------+
   | -Wconversion               |      | -Wpointer-to-int-cast      |
   | -Wdiscarded-qualifiers     |      |   (플래그 없이도 나온다)    |
   | -Wsign-compare             |      | -Wcast-function-type       |
   | -Wint-conversion           |      |   (-Wextra)                |
   +----------------------------+      +----------------------------+
     "알고 한다" 로 받아들인다            "알고 해도 위험하다" 고 본다
```

그림 해설 (한 단계씩):

- **폭이 줄어드는 포인터→정수 캐스트**는 캐스트를 씌워도 경고가 남는다. 플래그를 하나도 안 줘도 나온다.
- **함수 포인터 캐스트**도 `-Wextra` 에서 남는다.
- 나머지는 대부분 **캐스트가 「서명」으로 받아들여져** 조용해진다.
- `-Wsign-compare` 는 **캐스트로 고칠 수도 있고 망칠 수도 있다.**

```text
그냥        : 0
(unsigned)i : 0
(int)u      : 1
```

  `(unsigned)i < u` 는 **경고만 사라지고 답은 그대로 틀렸다.** `i < (int)u` 는 둘 다 고쳤다.\
  같은 「캐스트로 경고를 껐다」인데 결과가 반대다.

비용 — `-Wcast-qual`·`-Wstrict-aliasing=2` 를 켜는 것.

## 문법 — 형태와 규칙

### 형태

```c
(타입이름)식            /* 캐스트 연산자 — 단항, 오른쪽 결합 */

(int)3.9                /* 값 변환 */
(char *)pi              /* 포인터 재해석 */
(intptr_t)pv            /* 포인터 -> 정수 */
(void (*)(void))fp      /* 함수 포인터 -> 함수 포인터 */
(void)expr              /* 결과를 버린다는 표시 (경고 끄기용) */
```

- **캐스트의 결과는 값이지 객체가 아니다.** 그래서 왼쪽에 못 쓴다.

```text
lval.c:1:37: error: lvalue required as left operand of assignment
    1 | int main(void) { int i = 0; (char)i = 1; return i; }
```

- `malloc` 의 반환에 캐스트를 **안 붙이는 것**이 C 의 관례다. `void *` 가 캐스트 없이 오가기 때문이다.

```text
7
(캐스트 없이 경고 0)
```

  헤더를 빼먹으면 이 경고가 나온다.

```text
mal2.c:2:27: warning: implicit declaration of function ‘malloc’ [-Wimplicit-function-declaration]
```

  ★ **「캐스트를 붙이면 이 경고가 가려진다」는 C89 시절 이야기**이고, 이 컴파일러에서는 재현되지 않는다 —\
  캐스트를 붙여도 같은 경고가 나온다(정답 10번의 출력). 지금 캐스트를 안 붙이는 근거는 **필요가 없다는 것**뿐이다.

### 금지 사례 — 조용히 틀리는 다섯 형태

```c
/* (1) 타입 펀닝을 포인터 캐스트로 */
float f = *(float *)&i;                 /* UB — -O2 에서 답이 달라진다 */

/* (2) 정렬을 무시한 캐스트 후 역참조 */
int *p = (int *)(buf + 1); *p = 0;      /* UB — ubsan 이 잡는다 */

/* (3) const 객체에 캐스트로 쓴다 */
const int c = 7; *(int *)&c = 9;        /* UB — -O0 과 -O1 이 다르다 */

/* (4) 함수 포인터를 다른 시그니처로 호출 */
((int (*)(int))add)(2);                 /* UB — 값이 매 실행 다르다 */

/* (5) 포인터를 int 에 담는다 */
int n = (int)p;                          /* 64비트에서 절반이 잘린다 */
```

### 규칙 불릿

- 캐스트는 **새 값을 만든다.** 원래 객체는 안 바뀌고, 결과는 **lvalue 가 아니다.**
- **산술 타입끼리의 캐스트는 값 변환**이다 — 비트가 바뀔 수 있다.
- **포인터끼리의 캐스트는 비트를 안 바꾼다.** 바뀌는 것은 「어떻게 읽을 것인가」뿐이다.
- **`void *` 는 어떤 객체 포인터와도 캐스트 없이 오가고, 왕복이 보장**된다.
- 정렬이 더 엄한 타입으로 바꾸는 것은 **정렬이 안 맞으면 표준이 정의하지 않는다.** 도구는 **역참조**에서 잡는다.
- **호환되지 않는 타입으로 읽는 것**(엄격한 앨리어싱 위반)은 UB 이고, **`-O2` 이상에서 답이 갈린다.**
- **원래 객체가 `const`** 일 때 캐스트로 떼고 쓰면 UB 다. 원래 객체가 `const` 가 아니면 정의된다.
- 함수 포인터 ↔ 함수 포인터 **왕복은 보장**되고, **다른 시그니처로 호출하면 UB** 다.
- **정수 ↔ 포인터 왕복은 `intptr_t`/`uintptr_t` 로만** 보장된다(선택 사항인 타입).
- 캐스트는 **경고를 끈다.** 그것이 캐스트의 부작용 중 가장 위험한 것이다.

## 어디서 틀리나

### 1. 「캐스트했으니 컴파일러가 확인해 준 것」이라고 읽는다

- 정반대다. 캐스트는 **확인을 끄는 선언**이다.
- `-Wconversion` 2건이 캐스트 두 개로 0건이 됐다.
- [04번 형제](../04-floating-point-types-and-conversions/)가 같은 것을 부동소수 쪽에서 관찰했다 — `(float)16777217` 은 값이 틀리는데 `-Wconversion` 도 조용하다.

### 2. 「포인터 캐스트는 UB 다」 또는 「포인터 캐스트는 안전하다」

- 둘 다 반쪽이다. **캐스트 자체는 대개 조용하고, 사고는 역참조에서 난다.**
- 단 **정렬** 쪽은 표준 문장이 「변환 자체」를 금지한다 — 도구가 잡는 자리와 다르다.
- 실측: 캐스트만 하고 끝내면 UBSan 이 **한 줄도 안 냈다.**

### 3. 한 최적화 수준만 돌리고 결론을 낸다

- 엄격한 앨리어싱은 **`-O2` 부터** 갈렸다(`-O0`·`-O1` 은 같다).
- `const` 떼고 쓰기는 **`-O1` 부터** 갈렸다.
- **경계선이 주제마다 다르다.** 「`-O0` 과 `-O2` 만 보면 된다」도 틀린 규칙이다.

### 4. sanitizer 를 켰으니 봤다고 생각한다

| 위반 | gcc UBSan 기본 | ASan | 경고 |
|---|---|---|---|
| 정렬 위반 역참조 | **잡는다** | 못 잡는다 | 없음 |
| 엄격한 앨리어싱 | **못 잡는다** | 못 잡는다 | `-Wstrict-aliasing=2` 만 |
| `const` 객체에 쓰기 | **못 잡는다** | 못 잡는다 | `-Wcast-qual`(캐스트가 있다는 사실만) |
| 리터럴에 쓰기 | 못 잡는다 | **SEGV 로 잡는다** | 없음 |
| 틀린 시그니처 호출 | **검사가 없다** | 못 잡는다 | `-Wextra` |

- ★ **세 칸이 「못 잡는다」다.** 「sanitizer 를 켰다」가 「전수를 봤다」가 아니다.

### 5. `(char)` 로 좁히면 구현 정의라는 것을 잊는다

```text
CHAR_MIN=-128 CHAR_MAX=127  (char 에 부호가 있나: 1)
(char)200          = -56
(unsigned char)200 = 200
(char)-1 을 unsigned char 로 = 255
(char)300          = 44
(signed char)-129  = 127
```

```text
CHAR_MIN=0 CHAR_MAX=255  (char 에 부호가 있나: 0)
(char)200          = 200
```

- **`-funsigned-char` 하나로 `(char)200` 이 `-56` ↔ `200` 으로 뒤집힌다.**
- 바이트를 다룰 때 `char` 대신 **`unsigned char`** 를 쓰는 이유가 이것이다.
- `-Wconversion` 도 조용하다(명시 캐스트라서).

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
[04번 형제](../04-floating-point-types-and-conversions/)가 세운 「**조건부 표준**」 층은 이 주제에 **해당하는 것이 없다** — 그래서 그 줄을 비워 둔다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | 캐스트 결과가 lvalue 가 아닌 것 · 산술 캐스트가 값 변환인 것 · 포인터→포인터 캐스트가 **값을 보존**하고 되돌아오는 것 · `void *` 왕복 · 함수 포인터 왕복 · `(int)d` 가 **절단**인 것 | 컴파일 에러 · 왕복 비교 실행 · `cvttsd2si` 명령 이름 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음**(이 주제에 조건부 보장은 없다) | — | — |
| **구현 정의** | 문서화 의무가 있다 | **`char` 의 부호**(`(char)200` 이 `-56`) · `sizeof(void *)`=8 · `intptr_t`/`uintptr_t` 가 **존재하는지** · 포인터→정수 변환 결과의 표현 · 범위 밖 값을 부호 있는 정수로 **변환**한 결과 | `<limits.h>` · `-funsigned-char` 로 **뒤집어 봄** · `sizeof` | 경고가 한 건도 안 난다 |
| **미명시** | 몇 가지 중 하나 | 함수 인자 평가 순서(이 주제의 실험 하나가 여기 걸렸다 — 아래 참조) | gcc 가 오른쪽부터 평가 | **sanitizer 가 원리상 못 잡는다** |
| **UB** | 아무 일이나 | **정렬이 안 맞는 역참조** · **엄격한 앨리어싱 위반** · **`const` 객체에 캐스트로 쓰기** · **틀린 시그니처로 함수 호출** · 문자열 리터럴 수정 | `-O0`\~`-Os` 다섯 수준 · UBSan · ASan | **앨리어싱·`const` 는 UBSan 도 ASan 도 못 잡는다** · 최적화로 **사라진 UB** 는 아무도 못 본다 |

### UB 를 「이론」이 아니라 출력으로

이 문서의 프로그램에서 나온 실제 줄 전수다.

```text
align3.c:7:8: runtime error: store to misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
align3.c:9:5: runtime error: load of misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
pack.c:20:8: runtime error: store to misaligned address 0x5d0f2cfc6199 for type 'int', which requires 4 byte alignment
==1779422==ERROR: AddressSanitizer: SEGV on unknown address 0x55bdadf91140 ... The signal is caused by a WRITE memory access.
fnp.c:20:58: runtime error: call to function add through pointer to incorrect function type 'int (*)(int)'
```

★ 마지막 줄만 **clang** 의 것이다 — gcc 에는 그 검사가 아예 없다(정답 9번).

- **다섯 줄뿐이다.** 이 문서가 만든 UB 는 그보다 많다 — 나머지는 **아무도 안 잡았다.**
- ★ **「한 건도 안 나왔다」가 「UB 가 없다」가 아니다.**

### 미명시가 실험 하나를 망친 기록

`sizeof` 실험([08번 형제](../08-sizeof-alignment-and-offsetof/))에서 같은 `printf` 안에 부작용 있는 식과 그 부작용을 읽는 식을 같이 넣었더니,\
gcc 가 **오른쪽부터 평가**해서 「호출 수가 안 늘었다」는 **틀린 관찰**이 나왔다.\
문을 나눠 다시 재니 답이 뒤집혔다. **측정 코드 자체가 미명시에 걸릴 수 있다** — 이 주제를 공부한 값이 거기서 나왔다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 소수부를 버리고 정수로 | 범위 검사 후 `(int)d` | 검사 없는 `(int)d` |
| 비트를 다른 타입으로 읽기 | **`memcpy`** (명령이 같다) | `*(float *)&i` |
| `char` 버퍼에서 정수 꺼내기 | **`memcpy`** | `*(int *)(buf+k)` |
| 주소를 정수로 | `uintptr_t` | `int`·`long`(폭 보장 없음) |
| `void *` 와 객체 포인터 사이 | **캐스트 없이** | 습관적 캐스트 |
| `malloc` 반환 받기 | 캐스트 없이 | `(int *)malloc(...)` |
| 부호 비교 경고 없애기 | 한쪽을 **넓은 타입**으로 올리기 | `(unsigned)i`(답이 그대로 틀린다) |
| 낡은 API 에 `const` 벗겨 넘기기 | **원본이 `const` 가 아닐 때만** | `const` 객체에 쓰기 |
| 콜백 테이블 | **시그니처를 맞춘다** | 캐스트로 우겨 넣기 |
| 바이트 다루기 | `unsigned char` | `char`(부호가 구현 정의) |

판단 규칙 두 줄.

- **캐스트를 쓰고 싶어지면 먼저 「무엇을 끄려는 건가」를 묻는다.** 경고를 끄는 것이면 대개 틀린 수선이다.
- **비트를 옮기고 싶으면 `memcpy`** 다. 공짜이고, UB 가 아니고, 최적화 수준에 안 흔들린다.

## 핵심 문장

- 캐스트는 **값을 바꾸는 것**과 **해석을 바꾸는 것** 둘이다 — `cvttsd2si` 가 생기느냐 안 생기느냐로 어셈블리에서 갈린다.
- **포인터 캐스트는 조용하고 역참조가 시끄럽다.** 캐스트만 하고 끝내면 UBSan 이 한 줄도 안 낸다.\
  단 **표준 문장은 정렬이 안 맞는 「변환 자체」를 금지**한다 — 도구와 표준의 자리가 어긋난다.
- **엄격한 앨리어싱 위반은 `-O2` 부터 답이 갈린다**(`1` ↔ `1073741824`). `-O0`·`-O1` 만 돌리면 못 본다.\
  **UBSan 도 ASan 도 못 잡고**, `-Wall -Wextra` 도 0건이며, **`-Wstrict-aliasing=2`** 로 낮춰야 1건이 나온다.
- **`memcpy` 는 공짜다.** `*(float *)&x` 와 **기계어가 한 글자도 다르지 않다.**
- `const` 를 캐스트로 떼고 쓰면 **원래 객체가 `const` 일 때만** UB 이고, **`-O1` 부터** 답이 갈린다.
- 함수 포인터는 **왕복은 보장, 다른 시그니처 호출은 UB** 다. gcc 의 UBSan 에는 **그 검사가 아예 없다.**
- **캐스트는 경고를 끈다** — `-Wconversion` 2건이 0건이 됐다. 다만 **폭이 줄어드는 포인터→정수 캐스트**는 못 끈다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 05번)
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — **그쪽은 「컴파일러가 몰래 바꾸는 것」까지, 여기는 「내가 대놓고 바꾸는 것」부터.** `-1 < 1u` 를 캐스트로 고치는 자리가 이 문서의 (8)
- [`04-floating-point-types-and-conversions/`](../04-floating-point-types-and-conversions/) — `(int)d` 의 범위 밖 UB 와 `float-cast-overflow` 가 기본 집합에 없다는 것. **그쪽이 부동소수 쪽 정본**
- [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/) — `char` 의 부호가 구현 정의인 것 · `intptr_t` 의 폭
- [`../../../../data-representation/`](../../../../data-representation/) — **그쪽은 비트 표현·엔디언까지, 여기는 그 위에서 C 가 그 비트를 어떻게 다시 읽나부터**
- [`../../../c-cpp-csharp.md`](../../../c-cpp-csharp.md) — **그쪽은 「이 실패 계급이 왜 정합성 도메인에서 최악인가」라는 논증까지, 여기는 「어떤 캐스트가 그것을 만드나」부터**
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — **왜 정렬이 필요한가**의 정본. 이 문서 (4)의 반대편이고, 거기는 `#pragma pack` 이 같은 UB 를 만든다
- [목록의 **14번 주제**](../14-pointers-address-dereference-and-pointer-types/) (포인터) · 목록의 **19번 주제** (`void *`·`NULL`) — 포인터 자체의 정본
- 목록의 **23번 주제** (`union` 과 타입 펀닝) — C 에서 `union` 을 통한 펀닝이 허용되는 범위
- 목록의 **31번 주제** (`const` 와 포인터 const 위치) — `const` 가 계약이라는 것의 정본
- 목록의 **55번 주제** (엄격한 앨리어싱 규칙) — 이 문서 (5)가 정본으로 다뤄지는 곳
- 목록의 **58번 주제** (UB 를 잡는 도구) — 이 문서의 경고·sanitizer 표가 정본으로 다뤄지는 곳

## 용어 풀이

- **캐스트(cast)** — `(타입)식`. 식의 타입을 바꾸라고 명시하는 단항 연산자. **결과는 값이고 lvalue 가 아니다.**
- **값 변환(value conversion)** — 숫자로서의 값을 목표 타입에 맞게 옮기는 것. `(int)3.9` → `3`.
- **재해석(reinterpretation)** — 비트는 그대로 두고 읽는 규칙만 바꾸는 것. 포인터 캐스트가 이쪽.
- **타입 펀닝(type punning)** — 같은 메모리를 다른 타입으로 읽는 것. 이식 가능한 방법은 `memcpy`.
- **엄격한 앨리어싱(strict aliasing)** — 호환되지 않는 타입의 포인터는 같은 객체를 안 가리킨다는 컴파일러의 가정. `-O2` 에서 기본으로 켜진다.
- **정렬(alignment)** — 객체의 주소가 어떤 수의 배수여야 하는가. `_Alignof` 로 물어본다([08번 형제](../08-sizeof-alignment-and-offsetof/)).
- **`intptr_t` / `uintptr_t`** — `void *` 를 담았다 되돌릴 수 있는 정수 타입. **선택 사항**이다.
- **`-fstrict-aliasing`** — 앨리어싱 가정을 켜는 gcc 플래그. `-O2` 이상에서 기본이다. 끄려면 `-fno-strict-aliasing`.
- **`-Wcast-qual`** — 캐스트로 `const`·`volatile` 을 떼는 자리를 경고하는 플래그. `-Wall -Wextra` 에 없다.
- **`cvttsd2si`** — x86 의 「double 을 0 쪽으로 잘라 정수로」 명령. `(int)d` 가 만드는 명령.
- **`movsx`** — 부호를 채우며 폭을 넓히는 x86 명령. `(long)i` 가 만드는 명령.

---

## 더 들어가면

- **`union` 을 통한 타입 펀닝은 C 에서 허용된다**(C++ 과 다르다). 마지막에 쓴 멤버가 아닌 멤버를 읽는 것이\
  C 에서는 「값이 재해석된다」로 정의돼 있다. 이 문서에서는 **던져 보지 않았다** — 정본은 목록의 **23번 주제**다.

- **`-fno-strict-aliasing` 으로 빌드하는 프로젝트가 실제로 있다.** 리눅스 커널이 대표적이다.\
  「UB 를 고치는 대신 컴파일러에게 그 최적화를 포기시키는」 선택이고, **대가는 성능**이다.\
  이 문서에서 그 성능 차이는 **재 보지 않았다.**

- **`restrict` 는 앨리어싱의 반대 방향**이다 — 「겹치지 않는다」를 프로그래머가 약속하는 것.\
  `memcpy` 의 시그니처에 `restrict` 가 붙어 있고 `memmove` 에는 없다. 정본은 목록의 **33번 주제**.

- **`(void)expr` 는 캐스트 중 유일하게 「값을 버린다」는 뜻**이다. `-Wunused-result` 를 끄는 관용구인데,\
  gcc 는 `__attribute__((warn_unused_result))` 가 붙은 함수(`scanf`·`write` 등)에서는 **`(void)` 로도 안 꺼진다.**\
  이 문서에서는 **확인하지 않았다.**

- **32비트에서는 `(int)p` 가 안 잘린다.** 그래서 「32비트에서 돌던 코드가 64비트에서 깨진다」는 고전이 나온다.\
  이 머신에는 32비트 헤더가 없어 **확인하지 못했다**(04번 형제가 같은 자리에서 막혔다 —\
  `bits/libc-header-start.h` 가 없다). `gcc-multilib` 를 설치하면 잴 수 있다.
