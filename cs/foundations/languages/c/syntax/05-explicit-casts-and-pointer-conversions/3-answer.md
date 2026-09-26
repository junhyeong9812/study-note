# c/syntax/05 — 명시 캐스트와 포인터 변환: 내가 대놓고 바꾸는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고·어셈블리는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **UB 가 걸린 답(4·5·6·9번)은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 수준 + sanitizer 로 돌렸다.**\
> `clang 18.1.3` 을 쓴 자리는 그 자리에 밝혔다. 기본 플래그는 `-std=c17 -Wall -Wextra`.
> ★ **주소가 찍히는 줄은 실행마다 다르다**(ASLR). 그래서 본문의 실험은 대부분 **주소 대신 비교 결과**를 찍는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 캐스트 네 개가 만드는 기계어 ★

**출력**

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

**캐스트가 만든 명령 수**

| 함수 | 캐스트 | 캐스트가 만든 명령 |
|---|---|---|
| `c_ptr` | `(char *)p` | **0개** (`mov rax, rdi` 는 호출 규약) |
| `c_u` | `(unsigned)i` | **0개** (`mov eax, edi` 는 호출 규약) |
| `c_long` | `(long)i` | **1개** — `movsx` (부호 확장) |
| `c_int` | `(int)d` | **1개** — `cvttsd2si` |

**명령이 안 생기는 둘**

- **`(char *)p` 와 `(unsigned)i`** 다.
- 둘의 공통점: **비트가 안 바뀐다.** 바뀌는 것은 「이 비트를 무엇으로 읽을 것인가」뿐이다.
- `endbr64` 는 CET(간접 분기 보호)용이고 캐스트와 무관하다.

**`cvttsd2si` 의 이름**

```text
   cvt  t   t   sd   2   si
    |   |   |   |    |   |
    |   |   |   |    |   +-- signed integer (부호 있는 정수로)
    |   |   |   |    +------ to
    |   |   |   +----------- scalar double (double 한 개)
    |   |   +--------------- ★ truncate (0 쪽으로 자른다)
    |   +------------------- with
    +----------------------- convert
```

- `t` 가 「**자른다**」를 말한다. [04번 형제](../04-floating-point-types-and-conversions/)가 `(int)-3.9 == -3` 으로 관찰한 규칙이 **명령 이름에 박혀 있다.**
- 반올림이 아니라 절단이라는 것을, 실행 결과 말고 **기계어 이름**으로 한 번 더 확인할 수 있다.

**「캐스트는 두 종류다」를 어떻게 보여 주나**

```text
   값을 바꾸는 캐스트          해석을 바꾸는 캐스트
   +--------------------+     +--------------------+
   | 변환 명령이 생긴다   |     | 명령이 안 생긴다    |
   | movsx / cvttsd2si  |     | (mov 는 ABI 몫)    |
   | 비트가 바뀐다        |     | 비트가 그대로다     |
   +--------------------+     +--------------------+
      틀리면 "값이 이상하다"      틀리면 ★ "아무 일도 안 난다"
                                  그리고 나중에 터진다
```

- **어셈블리가 이 주제의 네 번째 창**이다. 지어낼 수 없고 독자가 자기 머신에서 재현한다.

### 2. 같은 `int` 를 `float` 로

**출력**

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

**두 줄**

- `memcpy` 로 읽으면 **`3.14159274`**
- `(float)x` 는 **`1078530048.00000000`**

**얼마나 다른가**

```text
   int x = 1078530011   (= 0x40490FDB)

   비트로 읽으면      0 10000000 10010010000111111011011
                      ^ 부호  ^ 지수      ^ 가수          -> 3.14159274

   값으로 옮기면      1078530011 을 float 에 담는다
                      float 의 유효 비트는 24개 -> 반올림
                                                  -> 1078530048.0
```

- **10억 배쯤 다르다.** 「같은 데이터를 다른 타입으로 본다」와 「숫자를 옮긴다」는 전혀 다른 일이다.
- `1078530048` 은 `1078530011` 을 `float` 에 담느라 **반올림된 값**이다([04번 형제](../04-floating-point-types-and-conversions/)의 `2^24` 경계 — `2^30` 근처에서는 눈금 간격이 64다).

**어느 쪽이 어느 쪽인가**

- `memcpy` = **비트를 그대로 옮긴다**(타입 펀닝).
- `(float)x` = **값을 옮긴다**(값 변환).

**`*(float *)&x` 로 써도 되나**

- 이 프로그램에서는 **같은 답이 나온다.** 하지만 **쓰면 안 된다.**
- 5번에서 보듯 **엄격한 앨리어싱 위반**이고, `-O2` 이상에서 읽기 자체가 사라질 수 있다.
- 그리고 **`memcpy` 로 바꿔도 기계어가 똑같다**(5번의 마지막 블록). 바꾸지 않을 이유가 없다.

### 3. 포인터를 정수에 담았다 되돌리기

**출력**

```text
(intptr_t) 로 왕복 == 원본? 1
(int)      로 왕복 == 원본? 0
sizeof: void*=8 int=4 intptr_t=8 uintptr_t=8
```

**두 비교**

- `intptr_t` 로 왕복 → **`1`(같다)**
- `int` 로 왕복 → **`0`(다르다)**

**왜 갈리나**

```text
   void *p   0x00007ffd_xxxxxxxx    (64비트)
                |
                | (intptr_t)  폭 8            | (int)  폭 4
                v                             v
        +----------------+          +--------+
        | 64비트 전부     |          | 하위 32비트만 |
        +----------------+          +--------+
                |                             |
          되돌리면 원본                되돌리면 ★ 다른 주소
```

- `sizeof(void *)` 는 8, `sizeof(int)` 는 4다. **상위 4바이트가 통째로 사라진다.**
- `intptr_t` 는 「`void *` 를 담았다 되돌릴 수 있는 정수」라고 정의된 타입이라 왕복이 성립한다.

**경고가 남나**

```text
ptrint3.c:1:51: warning: cast from pointer to integer of different size [-Wpointer-to-int-cast]
```

```text
[플래그 없음] ptrint3:
1
```

- ★ **플래그를 하나도 안 줘도 나온다.** 캐스트가 못 끄는 드문 경고다.
- 「캐스트 = 알고 하는 겁니다」라는 서명이 **여기서는 안 받아들여진다.**

**`intptr_t` 는 어느 층인가**

- **구현 정의이자 선택 사항**이다. 「포인터를 담을 수 있는 정수 타입이 있는 구현」에만 존재한다.
- 이 환경에는 있고 폭은 8이다.
- 비트 연산을 할 거면 **`uintptr_t`** 쪽이 낫다 — 음수가 안 끼어든다.

### 4. 정렬이 안 맞는 포인터 ★★

**출력**

```text
=== 캐스트만, 역참조 없음 : ubsan ===
A: 캐스트 통과 (p=buf+1, 정렬 안 맞음)
B: 포인터 비교도 된다: 1
C: 끝까지 아무 말도 없었다
exit=0
```

```text
=== 역참조까지 : ubsan (recover 허용) ===
A: 캐스트 통과
align3.c:7:8: runtime error: store to misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
B: 썼다
align3.c:9:5: runtime error: load of misaligned address 0x7ffcee707c51 for type 'int', which requires 4 byte alignment
C: 읽으면 0x41424344
exit=0
```

**(a)만 돌리면**

- **한 줄도 안 나온다.** `exit=0` 이고 포인터 비교까지 정상으로 된다.

**(b)까지 돌리면**

- **두 줄** — `store to misaligned address` 와 `load of misaligned address`.
- `-fno-sanitize-recover=all` 을 붙이면 **첫 줄에서 죽어서**(`exit=1`) 두 번째 줄을 못 본다.\
  ★ 「**중단시키면 전수를 못 본다**」는 것이 이 옵션의 대가다.

**기본 집합인가**

- ★ **기본 집합이다.** `-fsanitize=undefined` 만으로 나온다.
- [04번 형제](../04-floating-point-types-and-conversions/)의 `float-cast-overflow` 와 **정반대**다 — 그쪽은 따로 켜야 했다.
- **「UBSan 의 기본 집합」을 한 낱말로 외우면 안 된다.** 검사마다 다르다.

**표준과 도구의 자리가 같은가**

```text
   표준이 금지하는 자리            도구가 잡는 자리
   +--------------------------+  +--------------------------+
   | (int *)(buf+1)           |  | *p = ...                 |
   | ★ 변환 자체              |  | ★ 역참조                 |
   +--------------------------+  +--------------------------+
        여기서는 아무 말이 없다        여기서 두 줄이 나온다
```

- **다르다.** 표준의 문장은 정렬이 더 엄한 타입으로의 **변환 자체**를 정의하지 않는다고 말하는데,\
  gcc 의 UBSan 은 **변환에 침묵하고 역참조에서** 잡는다.
- 그래서 **「도구가 조용하다」를 「표준이 허용한다」로 읽으면 안 된다.**
- 반대로 실무적으로는 「역참조만 안 하면 대개 무사하다」가 맞는 관찰이기도 하다 —\
  **두 문장을 갈라서 기억한다.**

**이식 가능한 대안**

```c
int v;
memcpy(&v, buf + 1, sizeof v);
```

- `memcpy` 는 정렬을 요구하지 않는다. 실측에서 `0x41424344` 를 정확히 읽었다.
- x86-64 는 정렬이 안 맞아도 그냥 돌기 때문에 **sanitizer 없이는 증상이 아예 없다.**\
  「우리 서버에서 잘 되는데요」가 이식성 근거가 못 되는 자리다.

### 5. 같은 객체를 두 타입으로 ★★★

**출력**

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

**몇 종류의 값 · 경계선**

- **두 종류** — `1` 과 `1073741824`.
- **경계선은 `-O2`** 다. `-O0`·`-O1` 은 두 플래그 모두 `1073741824`, `-O2`·`-O3`·`-Os` 는 기본 빌드에서만 `1`.
- ★ **`-Os` 도 갈린다.** 「최적화 수준을 높이면」이 아니라 「**이 최적화가 켜지면**」이다.

**`x` 도 갈리나**

- **아니다.** 열 번 모두 `1073741824` 다.
- **반환값만 틀리고 메모리는 맞다** — 그래서 디버거로 변수를 찍어 보면 **정상으로 보인다.**\
  이 주제에서 가장 고약한 성질이다.

**어셈블리**

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

- **한 명령 차이**다. `mov eax, DWORD PTR [rdi]`(메모리에서 다시 읽기) 가 `mov eax, 1`(상수) 로 바뀌었다.
- 순서도 바뀌었다 — strict 쪽은 `mov eax, 1` 이 **`[rsi]` 에 쓰기 전**으로 올라갔다.\
  「읽기가 사라졌다」와 「순서가 바뀌었다」가 **같은 한 줄**에 들어 있다.

**경고**

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

- ★★ **`-Wall` 은 0건이다.** `-Wstrict-aliasing` 자체는 `-Wall` 에 들어 있지만 **기본 수준이 3이고, 3은 이것을 놓친다.**
- **`=2` 로 낮춰야** 1건이 나온다. 「플래그가 켜져 있다」와 「그래서 잡힌다」가 다른 사례다.
- 잡았을 때의 문구:

```text
alias2.c:11:37: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
```

**sanitizer**

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

- **둘 다 한 줄도 안 낸다.** 이 갈래에서 **도구가 가장 못 보는 UB** 다.
- clang 18.1.3 도 `-O2` 에서 `1` 을 냈고 `-Wall -Wextra` 로 **0건**이었다 — 컴파일러를 바꿔도 안 보인다.

**`memcpy` 의 비용**

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

- **한 글자도 안 다르다.** `memcpy` 는 공짜다.
- 「성능 때문에 캐스트를 쓴다」는 말은 **이 출력 앞에서 끝난다.**

### 6. `const` 를 캐스트로 떼고 쓰면 ★

**출력**

```text
-O0  : *bad = 99, frozen = 99
-O1  : *bad = 99, frozen = 7
-O2  : *bad = 99, frozen = 7
-O3  : *bad = 99, frozen = 7
-Os  : *bad = 99, frozen = 7
```

**경계선**

- **`-O1`** 이다. `-O0` 만 `99 99` 이고 나머지 넷은 `99 7`.
- ★ 5번은 `-O2` 가 경계였는데 여기는 `-O1` 이다 — **경계선은 UB 마다 다르다.**\
  「`-O0` 과 `-O2` 만 돌리면 된다」는 규칙도 우연히 맞는 것뿐이다.

```text
   -O0                          -O1 이상
   +----------------------+     +----------------------+
   | frozen 을 메모리에서  |     | frozen 은 7 이라고   |
   | 다시 읽는다          |     | ★ 컴파일 시간에 박았다|
   |   -> 99              |     |   -> 7               |
   +----------------------+     +----------------------+
        *bad 는 둘 다 99 — 한 객체가 두 값을 갖는다
```

**sanitizer**

```text
--- ubsan ---
*bad = 99, frozen = 7
exit=0
```

- **아무 말도 안 한다.** 같은 화면에 `99` 와 `7` 이 나란히 찍혀 있는데도.

**경고**

```text
[-Wall] 0 건
[-Wextra] 0 건
[-Wall -Wextra] 0 건
[-Wall -Wextra -Wcast-qual] 1 건
```

- **`-Wcast-qual`** 을 켜야 1건이다. `-Wall -Wextra` 에 없다.

**캐스트를 빼면**

```text
const3.c:1:44: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
```

- **플래그 없이도 나온다.** 캐스트가 이 경고를 껐던 것이다.

**원래 객체가 `const` 가 아니면**

- **결론이 달라진다.** 그때는 **정의된 동작**이다.

```text
(1) const 아닌 객체: counter = 42
```

- `const int *` 를 받았지만 그 대상이 보통 변수라면, 캐스트로 떼고 써도 된다.
- ★ **UB 인지 아닌지가 「포인터의 타입」이 아니라 「원래 객체가 무엇으로 선언됐나」에 달렸다.**\
  포인터만 보고는 판정할 수 없다는 뜻이다.
- 문자열 리터럴은 가장 확실한 `const` 객체다 — `(char *)"hello"` 에 쓰면 **세그멘테이션 오류**(`exit=139`)이고,\
  ASan 이 `SEGV ... The signal is caused by a WRITE memory access` 로 잡았다.

### 7. 캐스트가 끄는 경고와 못 끄는 경고

**출력**

```text
[-Wall -Wextra]  암시 0 건  /  캐스트 0 건
[-Wall -Wextra -Wconversion]  암시 2 건  /  캐스트 0 건
```

```text
warn.c:8:15: warning: conversion from ‘long unsigned int’ to ‘char’ may change value [-Wconversion]
warn.c:9:15: warning: conversion from ‘long unsigned int’ to ‘int’ may change value [-Wconversion]
```

**왜 조용해지나**

- 캐스트는 **「이 변환은 의도한 것이다」라는 선언**으로 취급된다.
- `-Wconversion` 은 「말없이 값이 바뀔 수 있다」를 잡는 경고이므로, **말을 했으면** 잡지 않는다.
- 그런데 **값이 바뀌는 사실 자체는 하나도 안 바뀌었다.** 2건 → 0건은 **코드가 아니라 진단이 바뀐 것**이다.

**남는 경고**

| 경고 | 캐스트를 씌워도 남나 | 어느 플래그 |
|---|---|---|
| `-Wconversion` | 꺼진다 | `-Wconversion` |
| `-Wdiscarded-qualifiers` | 꺼진다 | 기본 |
| `-Wint-conversion` | 꺼진다 | 기본 |
| `-Wsign-compare` | 꺼진다 | **`-Wextra`** |
| **`-Wpointer-to-int-cast`** | **남는다** | **기본**(플래그 없이도) |
| **`-Wcast-function-type`** | **남는다** | **`-Wextra`** |

- 남는 둘의 공통점: **캐스트를 썼다는 사실 자체가 위험 신호**인 변환이다.\
  폭이 줄어드는 포인터→정수, 시그니처가 다른 함수 포인터. 「알고 해도 위험하다」는 판정이다.

**`-Wsign-compare` 를 고치는 두 방법**

```text
그냥        : 0
(unsigned)i : 0
(int)u      : 1
```

```text
sign.c:4:36: warning: comparison of integer expressions of different signedness: ‘int’ and ‘unsigned int’ [-Wsign-compare]
```

- `(unsigned)i < u` → **경고만 껐다.** 답은 `0` 으로 **그대로 틀렸다.**
- `i < (int)u` → **경고도 끄고 답도 `1` 로 고쳤다.**
- 같은 「캐스트로 경고를 껐다」인데 **결과가 반대**다. 경고 개수로는 둘을 구별할 수 없다.

**한 줄로**

- **캐스트는 코드를 고치는 도구가 아니라 진단을 끄는 도구다.** 고친 것은 따로 증명해야 한다.

### 8. `(char)` 로 좁히면

**출력**

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
(unsigned char)200 = 200
(char)-1 을 unsigned char 로 = 255
(char)300          = 44
(signed char)-129  = 127
```

**`(char)200`**

- 이 환경에서 **`-56`** 이다. `200` 이 `signed char` 범위(`-128`\~`127`)를 넘어 감싼 결과다.

**`-funsigned-char` 를 붙이면**

- **`200`** 이 된다. **플래그 하나로 값이 뒤집힌다.**

**어느 층인가**

- **구현 정의**다. **UB 가 아니다.**
- 범위 밖 값을 부호 있는 정수 타입으로 변환하는 것은 「구현 정의 결과이거나 구현 정의 신호를 낸다」로 정해져 있다.\
  gcc 는 2의 보수로 감싸는 쪽을 문서화하고 있다.
- `char` 자체에 부호가 있는지도 **구현 정의**다(ARM 리눅스는 대개 부호 없음). [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)가 정본.

**`-Wconversion` 이 말해 주나**

```text
[-Wall -Wextra] 0 건
[-Wall -Wextra -Wconversion] 0 건
```

- **한 건도 안 나온다.** 명시 캐스트라서 `-Wconversion` 도 조용하다(7번과 같은 이유).

**그래서 무엇을 쓰나**

- 바이트를 다룰 때는 **`unsigned char`** 다. `(unsigned char)200` 은 어느 플래그에서도 `200` 이다.
- `<ctype.h>` 함수에 `char` 를 그냥 넘기면 안 되는 이유도 같다(목록의 **52번 주제**).

### 9. 함수 포인터 캐스트

**출력**

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

```text
틀린 시그니처로  : -10496158   <- ★ UB
틀린 시그니처로  : -916449438   <- ★ UB
틀린 시그니처로  : -623433806   <- ★ UB
```

**왕복**

- **원래 값이다.** `포인터 같음? 1` 이고 호출도 정상으로 `5` 를 냈다.
- 함수 포인터를 다른 함수 포인터 타입으로 바꿨다 되돌리는 것은 **표준이 보장**한다.

**그 타입으로 호출하면**

- **UB** 다.

**`-O0` 세 판**

- **매번 다르다** — `-10496158`·`-916449438`·`-623433806`.
- 두 번째 인자 자리에 들어 있던 **레지스터의 쓰레기 값**을 더한 결과다.
- ★ 「세 판 돌려 같은 값이 나왔다」가 보장이 아니듯, **매번 다른 것은 UB 의 가장 알아보기 쉬운 증상**이다.

**`-O2` 의 경고**

```text
In function ‘add’,
    inlined from ‘main’ at fnp.c:20:5:
fnp.c:3:34: warning: ‘b’ is used uninitialized [-Wuninitialized]
    3 | int add(int a, int b) { return a + b; }
```

- **소스에 초기화 안 한 변수가 한 개도 없는데** 이런 말이 나온다.
- `add` 를 인라인한 뒤에 보니 **두 번째 인자가 아예 전달되지 않았다** — 그것이 「초기화되지 않은 `b`」로 보인 것이다.
- `-O0` 에서는 인라인을 안 해서 **이 경고가 없다.** 최적화가 진단을 만들어 낸 사례다.

**어느 플래그인가**

```text
[] 0 건
[-Wall] 0 건
[-Wextra] 1 건
[-Wall -Wextra] 1 건
```

```text
fnp.c:19:14: warning: cast between incompatible function types from ‘Fn2’ {aka ‘int (*)(int,  int)’} to ‘int (*)(int)’ [-Wcast-function-type]
```

- **`-Wextra`** 다. `-Wall` 이 아니다.
- [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 `-Wsign-compare` 에서 찾은 것과 **같은 패턴**이다 —\
  **타입을 넘나드는 경고는 `-Wextra` 쪽에 몰려 있다.**

**gcc 의 UBSan 으로 잡히나**

```text
gcc: error: unrecognized argument to ‘-fsanitize=’ option: ‘function’
```

- **검사가 아예 없다.** 「기본 집합에 없다」가 아니라 **존재하지 않는다.**
- clang 에는 있고, 켜면 잡는다.

```text
fnp.c:20:58: runtime error: call to function add through pointer to incorrect function type 'int (*)(int)'
(/tmp/xr+0x2f7e8): note: add defined here
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior fnp.c:20:58 
```

- ★ **「sanitizer 로 돌렸다」가 컴파일러마다 다른 의미**라는 것을 보여 주는 자리다.

### 10. `void *` 는 무엇이 다른가

**출력**

```text
void* 왕복 == 원본? 1  (캐스트를 안 썼다)
```

```text
7
(캐스트 없이 경고 0)
```

```text
mal2.c:2:27: warning: implicit declaration of function ‘malloc’ [-Wimplicit-function-declaration]
    2 | int main(void) { int *p = malloc(4); printf("%p\n", (void*)p); return 0; }
      |                           ^~~~~~
mal2.c:2:1: note: include ‘<stdlib.h>’ or provide a declaration of ‘malloc’
```

**캐스트가 필요한가**

- **필요 없다.** `void *` 와 어떤 객체 포인터 사이는 **양방향 모두 암시 변환**이 된다.
- `-Wall -Wextra` 로 경고 0건이다.

**왕복이 보장되나**

- **객체 포인터 → `void *` → 원래 타입** 의 왕복이 보장된다. 실측도 `1` 이다.
- 보장되지 않는 것: **다른 객체 타입으로** 갔다 오는 것(정렬·앨리어싱이 걸린다), **함수 포인터**와의 변환.

**`malloc` 에 캐스트를 안 붙이는 근거**

- `void *` 가 캐스트 없이 대입되기 때문이다. 붙일 이유가 없다.

**붙이면 무엇이 가려지나**

```text
   #include <stdlib.h> 를 빠뜨렸다

   C89 시절:  선언이 없으면 반환 타입이 int 로 가정된다
              캐스트 없이  -> "int 를 포인터에 넣는다" 고 걸린다
              캐스트 있으면 -> "int 를 포인터로 캐스트한다" 가 되어 ★ 조용해진다

   gcc 13 (C99 이후): 암시 선언 자체가 제거되어
              ★ 캐스트가 있어도 없어도 같은 경고가 나온다
```

★ **이것이 고전으로 알려진 근거인데, 이 컴파일러에서는 재현되지 않는다.** 던져서 확인했다.

```text
--- 캐스트 있음, stdlib.h 없음 ---
mal3.c:2:34: warning: implicit declaration of function ‘malloc’ [-Wimplicit-function-declaration]
mal3.c:2:1: note: include ‘<stdlib.h>’ or provide a declaration of ‘malloc’
```

- **캐스트를 붙여도 같은 경고가 나온다.** C99 가 암시 선언을 없앴기 때문이다.
- 그러니 「캐스트를 붙이면 헤더 누락이 가려진다」는 **C89 시절 이야기**로 적어야 맞다.\
  지금 남는 근거는 「**필요 없는 것을 쓰지 않는다**」와 「**캐스트가 진단을 끄는 도구라는 일반 원리**」뿐이다.
- **C 에서 `malloc` 캐스트는 C++ 습관**이다. C++ 은 `void *` 의 암시 변환을 허용하지 않는다.

**함수 포인터는 같은 이야기인가**

- **아니다.** `void *` 와 **함수 포인터** 사이의 변환은 표준이 보장하지 않는다.
- POSIX 의 `dlsym` 이 `void *` 를 돌려주면서 그것을 함수 포인터로 쓰라고 하는 자리가 **표준 밖**인 이유다.

### 11. 그래서 언제 캐스트를 쓰나

**비트를 옮기는 이식 가능한 답과 그 비용**

```c
float f;
memcpy(&f, &i, sizeof f);
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

- **`memcpy`** 이고, **비용은 0이다.** 기계어가 한 글자도 안 다르다.

**먼저 물어야 할 한 문장**

- **「이 캐스트가 끄고 있는 것은 무엇인가?」**
- 끄고 있는 것이 **경고**면 대개 틀린 수선이다. 끄고 있는 것이 **없으면**(`void *` 왕복 등) 대개 불필요한 캐스트다.

**빌드 플래그 한 줄**

```text
개발·운영 빌드
  gcc -std=c17 -O2 -Wall -Wextra -Wconversion -Wcast-qual \
      -Wstrict-aliasing=2 -Wcast-align -Werror

테스트 빌드
  gcc -std=c17 -O1 -g -fsanitize=undefined,address \
      -fno-sanitize-recover=all
  + ★ 같은 소스를 -O0 과 -O2 양쪽으로 돌려 답이 같은지 본다

교차 확인
  clang -fsanitize=undefined,function   (gcc 에 function 검사가 없다)
```

- **`-Wstrict-aliasing=2`** 를 명시한다 — `-Wall` 의 기본 수준 3은 놓친다.
- **`-Wcast-qual`** 을 명시한다 — `-Wall -Wextra` 에 없다.
- **최적화 수준을 두 개 이상** 돌리는 것이 이 주제에서는 sanitizer 보다 강한 검사다.

**도구가 못 잡는 UB 는 몇 개인가**

| UB | gcc UBSan | ASan | 경고 |
|---|---|---|---|
| 정렬 위반 역참조 | **잡는다**(기본 집합) | 못 잡는다 | 없음 |
| 엄격한 앨리어싱 위반 | 못 잡는다 | 못 잡는다 | `-Wstrict-aliasing=2` |
| `const` 객체에 쓰기 | 못 잡는다 | 못 잡는다 | `-Wcast-qual`(캐스트가 있다는 사실만) |
| 틀린 시그니처로 호출 | **검사가 없다** | 못 잡는다 | `-Wextra` |
| 문자열 리터럴 수정 | 못 잡는다 | **SEGV 로 잡는다** | 없음 |

- **다섯 중 gcc UBSan 이 잡는 것은 하나**다.
- **「sanitizer 를 켰다」가 「전수를 봤다」가 아니다.** 나머지 넷은 **최적화 수준을 바꿔 답이 갈리는지**로 잡아야 한다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 플래그로 돌렸나 |
|---|---|---|
| 캐스트 어셈블리 | `(char*)`·`(unsigned)` 는 명령 0개 · `(long)` 은 `movsx` · `(int)double` 은 `cvttsd2si` | `-O1 -S -masm=intel` |
| 캐스트 기본 | `(int)3.9`=3 · `(unsigned)-1` · 세 포인터 동일 · `memcpy` 3.14159274 ↔ `(float)x` 1078530048 · `void*` 왕복 | `-std=c17 -Wall -Wextra` |
| 정수↔포인터 | `intptr_t` 왕복 1 / `int` 왕복 0 · `sizeof` 4종 · `-Wpointer-to-int-cast` 가 **플래그 없이** 1건 | `-Wall -Wextra` / 플래그 없음 |
| 정렬 (캐스트만) | UBSan **무반응** · exit 0 | `-O0 -fsanitize=undefined` |
| 정렬 (역참조) | `store`·`load` **2건** · `-fno-sanitize-recover` 면 1건에서 중단 · ASan 무반응 | `-O0`·`-O2`·ubsan·asan |
| 엄격한 앨리어싱 | **다섯 수준 × 2플래그 = 10회** · `-O2` 부터 `1` ↔ `1073741824` · `x` 는 안 갈림 | `-O0`\~`-Os` × `-fstrict-aliasing`/`-fno-` |
| 〃 어셈블리 | `mov eax, 1` ↔ `mov eax, [rdi]` · 순서도 바뀜 | `-O2 -S -masm=intel` × 2 |
| 〃 경고·도구 | `-Wall -Wextra` **0건** · `=1`·`=2` 는 1건, **`=3` 은 0건** · ubsan·asan **무반응** · clang 도 0건·`1` | 플래그 6벌 · ubsan · asan · clang |
| `memcpy` 대 캐스트 | **기계어 동일**(`movd xmm0, edi`) | `-O2 -S -masm=intel` |
| `const` 떼기 | **다섯 수준** · `-O1` 부터 `99 7` · ubsan 무반응 · `-Wcast-qual` 만 1건 · 캐스트 빼면 기본 경고 | `-O0`\~`-Os`·ubsan·플래그 4벌 |
| 리터럴 쓰기 | exit 139(SEGV) · ASan `SEGV ... WRITE memory access` | `-O0`·`-O2`·asan |
| 경고 끄기 | `-Wconversion` 암시 2건 → 캐스트 0건 · `-Wsign-compare` 세 형태의 답 `0/0/1` | `-Wall -Wextra` ± `-Wconversion` |
| `(char)` 캐스트 | `(char)200` = **-56 ↔ 200** (`-funsigned-char` 로 뒤집음) · `-Wconversion` 0건 | 기본 / `-funsigned-char` |
| 함수 포인터 | 왕복 OK · 틀린 호출은 `-O0` **매 판 다른 값**, `-O2` 는 2 · `-Wextra` 1건 · gcc 에 `function` 검사 **없음** · clang 은 잡음 | `-O0`(3판)·`-O2`·ubsan·clang |
| lvalue·`malloc` | `(char)i = 1` 은 **error** · `malloc` 캐스트 없이 경고 0 · 헤더 빠뜨리면 `implicit declaration` | `-std=c17 -Wall -Wextra` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0)에서만** 그렇다.

- `(char)200` 이 `-56` 인 것 — `char` 의 부호는 **구현 정의**다.
- `sizeof(void *)`=8, `intptr_t` 가 **존재하는 것** — 둘 다 구현 정의(후자는 선택 사항).
- 정렬이 안 맞는 역참조가 **그냥 도는 것** — x86-64 의 성질이다. 트랩을 내는 아키텍처가 있다(**확인 못 했다**).
- 엄격한 앨리어싱이 갈리는 **경계선 `-O2`** 와 `const` 의 **경계선 `-O1`** — UB 라 **보장이 아니다.**
- `-Wstrict-aliasing` 의 기본 수준이 3이고 3이 이 위반을 놓치는 것 — gcc 의 선택이다.
- UBSan/ASan 기본 집합의 구성과 `-fsanitize=function` 의 **부재** — gcc 의 선택이고 clang 과 다르다.
- `-O2` 에서 `‘b’ is used uninitialized` 경고가 나오는 것 — 인라인 여부에 달렸다.

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — 32비트(`-m32`)에서 `(int)p` 가 안 잘리는 것. `bits/libc-header-start.h` 가 없어 컴파일이 안 된다.\
  `gcc-multilib` 를 설치하면 잴 수 있다. **설치 제안만 하고 안 했다.**
- **못 잰 것** — 정렬 위반이 **트랩을 내는** 아키텍처의 동작. 이 머신은 x86-64 하나뿐이다.
- **안 돌려 본 것** — `union` 을 통한 타입 펀닝([목록의 **23번 주제**](../23-union-and-the-boundary-of-type-punning/)) · `-fno-strict-aliasing` 의 **성능 대가** ·\
  `(void)expr` 가 `warn_unused_result` 를 못 끄는지 · `-Wcast-align` 이 x86-64 에서 무엇을 잡는지.

**버전이 올랐을 때 다시 돌려야 하는 것**

- 5·6·9번의 최적화 수준별 값(UB — 보장이 아니다).
- `-Wstrict-aliasing` 의 기본 수준과 각 수준이 잡는 범위.
- gcc 의 UBSan 에 `-fsanitize=function` 이 생겼는지.
- `-Wall`·`-Wextra` 의 구성(`-Wcast-function-type` 이 `-Wall` 로 옮겨갔는지).
