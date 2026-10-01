# c/syntax/50 — `<string.h>` 메모리 함수: 「**`memcpy` 는 겹치지 않는다는 약속 위에 서고, `memset`·`memcmp` 는 값이 아니라 바이트를 다룬다**」 — 정답

## 이 파일이 다시 싣는 소스

★ 7번은 질문 파일에 소스가 없다 — 여기 싣는다.

```c
/* s50d.c */
#include <math.h>
#include <stdio.h>
#include <string.h>

static void bytes(const char *tag, const void *p, size_t n) {
    const unsigned char *b = p;
    printf("%-10s", tag);
    for (size_t k = 0; k < n; k++) printf(" %02x", b[k]);
    printf("\n");
}

int main(void) {
    int i; void *p; double d; void (*f)(void);
    memset(&i, 0, sizeof i);
    memset(&p, 0, sizeof p);
    memset(&d, 0, sizeof d);
    memset(&f, 0, sizeof f);
    printf("i == 0      : %d\n", i == 0);
    printf("p == NULL   : %d\n", p == NULL);
    printf("f == NULL   : %d\n", f == NULL);
    printf("d == 0.0    : %d   signbit(d) : %d\n", d == 0.0, signbit(d) != 0);
    void *null_p = NULL; double pz = 0.0, nz = -0.0;
    bytes("NULL", &null_p, sizeof null_p);
    bytes("0.0", &pz, sizeof pz);
    bytes("-0.0", &nz, sizeof nz);
#ifdef __STDC_IEC_559__
    printf("__STDC_IEC_559__ = %d\n", __STDC_IEC_559__);
#else
    printf("__STDC_IEC_559__ undefined\n");
#endif
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 겹침 격자 — **`memmove` 는 `ABABCDEFGHKLMNOP` · `CDEFGHIJIJKLMNOP` · `memcpy` 겹침은 결과를 적지 않는다 · ASan 이 잡은 칸 10 / 60** ★★★

**출력**

```text
===== 겹침 격자 — 함수 2 × 겹침 3 × 크기 2 × ASan 빌드 5 (-std=c17) (exit=0) =====
함수    겹침      크기   결과(ASan 없는 gcc -O0) | gcc -O0 | gcc -O2 | gcc -O2 -U_FORTIFY_SOURCE | clang -O0 | clang -O2
memcpy  없음      실행시 ABCDEFGHABCDEFGH   | -       | -       | -                         | -         | -        
memcpy  없음      상수 8 ABCDEFGHABCDEFGH   | -       | -       | -                         | -         | -        
memcpy  dst > src 실행시 (UB — 싣지 않음)   | overlap | -       | overlap                   | overlap   | overlap  
memcpy  dst > src 상수 8 (UB — 싣지 않음)   | -       | -       | -                         | overlap   | -        
memcpy  dst < src 실행시 (UB — 싣지 않음)   | overlap | -       | overlap                   | overlap   | overlap  
memcpy  dst < src 상수 8 (UB — 싣지 않음)   | -       | -       | -                         | overlap   | -        
memmove 없음      실행시 ABCDEFGHABCDEFGH   | -       | -       | -                         | -         | -        
memmove 없음      상수 8 ABCDEFGHABCDEFGH   | -       | -       | -                         | -         | -        
memmove dst > src 실행시 ABABCDEFGHKLMNOP   | -       | -       | -                         | -         | -        
memmove dst > src 상수 8 ABABCDEFGHKLMNOP   | -       | -       | -                         | -         | -        
memmove dst < src 실행시 CDEFGHIJIJKLMNOP   | -       | -       | -                         | -         | -        
memmove dst < src 상수 8 CDEFGHIJIJKLMNOP   | -       | -       | -                         | -         | -        
(dst > src = buf+2 <- buf · dst < src = buf <- buf+2 · 없음 = buf+8 <- buf · 8 바이트 · overlap = memcpy-param-overlap · 오른쪽 다섯 칸은 전부 -fsanitize=address -g)
ASan 이 잡은 칸 10 / 60
```

```text
===== clang -std=c17 -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s50a.c -o x && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x c 1 r 2>&1 >/dev/null | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1144201==ERROR: AddressSanitizer: memcpy-param-overlap: memory ranges [0x653430b76aa2,0x653430b76aaa) and [0x653430b76aa0, 0x653430b76aa8) overlap
    #0 0x6534301a6ec4 in __asan_memcpy (x+0xc3ec4) (BuildId: 491990e6ebd5d26a7ccdaa682c6e12f4ce2d3a69)
    #1 0x6534301e797f in main s50a.c:18:28
    #2 0x734d8662a1c9 in __libc_start_call_main csu/../sysdeps/nptl/libc_start_call_main.h:58:16
    #3 0x734d8662a28a in __libc_start_main csu/../csu/libc-start.c:360:3
    #4 0x65343010e344 in _start (x+0x2b344) (BuildId: 491990e6ebd5d26a7ccdaa682c6e12f4ce2d3a69)

0x653430b76aa2 is located 2 bytes inside of global variable 'buf' defined in './s50a.c:5' (0x653430b76aa0) of size 32
0x653430b76aa0 is located 0 bytes inside of global variable 'buf' defined in './s50a.c:5' (0x653430b76aa0) of size 32
SUMMARY: AddressSanitizer: memcpy-param-overlap (x+0xc3ec4) (BuildId: 491990e6ebd5d26a7ccdaa682c6e12f4ce2d3a69) in __asan_memcpy
```

**왜 그런가**

- ★★★ **`memmove` 는 「임시 배열을 거친 것처럼」** — 표준이 겹침의 결과를 정해 두었다. 두 줄의 글자는 **어느 C 구현에서도 같아야 하는 결과**다.
- ★★★ **`memcpy` 겹침 네 줄은 UB** — 「If copying takes place between objects that overlap, the behavior is undefined.」 결과 칸에 적을 것은 **「적지 않는다」** 다. 이 판에서 무엇이 나왔든 그것은 C 의 답이 아니다.
- ★★★ **ASan 은 전부를 잡지 않는다 — 스무 칸 중 열 칸.** 실행 시 크기 줄은 **gcc `-O2` 열만 빼고** 잡았고, 상수 8 줄은 **clang `-O0` 열만** 잡았다. 크기가 상수인지가 답을 바꾼다(2번) · 빌드 기본 매크로가 답을 바꾼다(8번).
- ★ **겹침 없는 `memcpy` · 모든 `memmove` 는 한 칸도 말하지 않았다** — 오탐이 없다.

### 2. `memcpy` 는 호출로 남는가 — **크기를 모르는 `copyn` 만 늘 호출 · `copy8` 은 clang `-O0` ASan 판에서만 호출** ★★

**출력**

```text
===== memcpy 는 호출로 남나 — 함수 4 × 빌드 8 (objdump -dr 의 재배치 심볼) (exit=0) =====
빌드                       | copy8                | copy32               | copyn                | move8               
gcc -O0                    | 인라인 mov 7개       | call memcpy          | call memcpy          | 인라인 mov 7개      
gcc -O2                    | 인라인 mov 2개       | 인라인 mov 4개       | call memcpy          | 인라인 mov 2개      
gcc -O0 -fsanitize=address | 인라인 + asan 검사   | call memcpy          | call memcpy          | 인라인 + asan 검사  
gcc -O2 -fsanitize=address | 인라인 + asan 검사   | call memcpy          | call memcpy          | 인라인 + asan 검사  
clang -O0                  | 인라인 mov 7개       | 인라인 mov 13개      | call memcpy          | 인라인 mov 7개      
clang -O2                  | 인라인 mov 2개       | 인라인 mov 4개       | call memcpy          | 인라인 mov 2개      
clang -O0 -fsanitize=address | call __asan_memcpy   | call __asan_memcpy   | call __asan_memcpy   | call __asan_memmove 
clang -O2 -fsanitize=address | 인라인 + asan 검사   | call __asan_memcpy   | call __asan_memcpy   | 인라인 + asan 검사  
(칸 = 그 함수 몸통의 재배치 심볼 — 없으면 인라인이고 mov 명령 수를 센다 · asan 검사 = __asan_report_load_n/store_n 만 있음)
```

**왜 그런가**

- ★★ **크기가 상수면 컴파일러가 복사를 `mov` 로 편다** — `-O0` 에서도 그렇다(gcc·clang 둘 다 `copy8` 이 `mov` 7 개). `copy32` 는 ASan 없는 네 벌 중 gcc `-O0` 만 호출로 남겼다.
- ★★★ **ASan 판의 `copy8` 은 대부분 「인라인 + 경계 검사」** — `__asan_report_load_n/store_n` 은 **영역이 유효한가**를 보고, **두 영역이 겹치나**는 안 본다. **clang `-O0 -fsanitize=address` 만 `__asan_memcpy` 를 부른다** — 1번에서 상수 8 줄을 잡은 **유일한 열**과 정확히 겹친다.
- ★ **속도는 말할 수 없다** — 이 격자는 명령의 모양이다. 「`memcpy` 가 `memmove` 보다 빠르다」는 **재지 않았고**, 이 격자에서는 `move8` 도 `copy8` 과 **같은 모양**이다.

### 3. 글자로 보이는 겹침 — **gcc 는 `shift_right`·`shift_left` 에 `-Wrestrict` · `shift_var` 는 0 · clang 은 셋 다 0** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s50g.c -o /dev/null (cc exit=0) =====
s50g.c: In function 'shift_right':
s50g.c:5:26: warning: 'memcpy' accessing 8 bytes at offsets 2 and 0 overlaps 6 bytes at offset 2 [-Wrestrict]
    5 | void shift_right(void) { memcpy(buf + 2, buf, 8); }
      |                          ^~~~~~~~~~~~~~~~~~~~~~~
s50g.c: In function 'shift_left':
s50g.c:6:25: warning: 'memcpy' accessing 8 bytes at offsets 0 and 2 overlaps 6 bytes at offset 2 [-Wrestrict]
    6 | void shift_left(void) { memcpy(buf, buf + 2, 8); }
      |                         ^~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -c s50g.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★ **gcc 는 주소와 크기를 컴파일 때 다 아는 호출만** 본다 — `overlaps 6 bytes at offset 2` 까지 계산한다.
- ★ **`shift_var(buf + 2, buf)` 는 함수 밖의 인자**라 `shift_var` 안에서는 모른다 — 경고가 없다(그 호출을 인라인한 호출처에서 경고가 나는지는 **던지지 않았다**).
- ★ clang 은 [33번 형제](../33-restrict-and-the-aliasing-contract/) (5)절과 같은 판단 — **이 판의 clang 에는 대응 경고가 없다.**

### 4. 멤버 `==` 와 `memcmp` — **`{0.0}`/`{-0.0}` 은 `same`/`diff` · NaN 은 `diff`/`same` · 네 빌드 같음** ★★★

**출력**

```text
===== memcmp 대 멤버 == — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0
{0.0} vs {-0.0}   member == : same   memcmp : diff
{NAN} vs copy     member == : diff   memcmp : same
--- gcc -O2
{0.0} vs {-0.0}   member == : same   memcmp : diff
{NAN} vs copy     member == : diff   memcmp : same
--- clang -O0
{0.0} vs {-0.0}   member == : same   memcmp : diff
{NAN} vs copy     member == : diff   memcmp : same
--- clang -O2
{0.0} vs {-0.0}   member == : same   memcmp : diff
{NAN} vs copy     member == : diff   memcmp : same
```

**왜 그런가**

- ★★★ **값의 같음과 바이트의 같음은 두 방향으로 다 갈린다** — `-0.0` 은 부호 비트 하나가 다르고(`== 0.0` 은 참), NaN 은 비트가 같아도 `==` 가 거짓이다.
- ★★ **패딩이 없는 구조체라 판을 안 탄다** — 네 빌드가 같은 것은 그 때문이다(5번과 대조).

### 5. 패딩이 있는 구조체 — **`memcmp(a, b)` 는 빌드에 따라 20/20 또는 0/20 · `memcmp(b, m)` 도 gcc `-O1` 에서 20/20 「다르다」 · 멤버는 전부 같음** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s50c.c -o x ; ./x (cc exit=0 · run exit=0) =====
members a,b equal : 1
memcmp(a, b)      : nonzero
memcmp(b, m)      : zero
```

```text
===== 패딩이 있는 구조체 — 컴파일러 2 × 최적화 3 × 20 판 (exit=0) =====
gcc    -O0  | members equal 20/20 | memcmp(a,b) nonzero 20/20 | memcmp(b,m) nonzero  0/20
gcc    -O1  | members equal 20/20 | memcmp(a,b) nonzero 20/20 | memcmp(b,m) nonzero 20/20
gcc    -O2  | members equal 20/20 | memcmp(a,b) nonzero  0/20 | memcmp(b,m) nonzero  0/20
clang  -O0  | members equal 20/20 | memcmp(a,b) nonzero 20/20 | memcmp(b,m) nonzero  0/20
clang  -O1  | members equal 20/20 | memcmp(a,b) nonzero  0/20 | memcmp(b,m) nonzero  0/20
clang  -O2  | members equal 20/20 | memcmp(a,b) nonzero  0/20 | memcmp(b,m) nonzero  0/20
```

**왜 그런가**

- ★★★ **패딩은 미명시** — `dirty()` 가 깐 쓰레기가 남느냐, 컴파일러가 구조체를 레지스터로 옮기며 다른 값을 채우느냐가 **빌드마다 다르다.** 여섯 빌드 중 셋이 「다르다」(gcc `-O0`·`-O1` · clang `-O0`), 셋이 「같다」였다.
- ★★★ **`memset` 은 그 객체에서만 유효하다** — `b` 는 `by_memset()` 이 **값으로 돌려준** 복사본이다. gcc `-O1` 은 돌려주는 길에 패딩을 다시 채웠다 — 그래서 `memset` 으로 지운 `m` 과도 다르다.
- ★ **한 빌드 안의 20 판은 전부 같았다** — 흔들림은 빌드 사이다. 바이트 덤프는 [22번 형제](../22-struct-padding-and-alignment/) (3)절.

### 6. `memset` 의 둘째 인자 — **`16843009` · `-1` · `16843009` · `1`, 경고 0** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s50e.c -o x ; ./x (cc exit=0 · run exit=0) =====
memset(a, 1)   : 16843009 16843009 16843009 16843009
memset(a, -1)  : -1 -1 -1 -1
memset(a, 257) : 16843009 16843009 16843009 16843009
loop a[k] = 1  : 1 1 1 1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s50e.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★ **둘째 인자는 `unsigned char` 로 바뀐 한 바이트**다 — `1` 은 `0x01` 을 네 번(`0x01010101` = `16843009`), `257` 도 `0x01` 로 깎여 같은 결과, `-1` 은 `0xFF` 네 번이라 이 판의 `int` 에서 `-1`.
- ★ **컴파일러는 말하지 않는다** — 적법한 호출이기 때문이다.

### 7. 「모든 비트 0」 — **`int` 는 표준 · `double` 은 `__STDC_IEC_559__` 일 때 · 포인터는 보장 없음 · `-0.0` 은 `… 80`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 s50d.c -o x ; ./x (cc exit=0 · run exit=0) =====
i == 0      : 1
p == NULL   : 1
f == NULL   : 1
d == 0.0    : 1   signbit(d) : 0
NULL       00 00 00 00 00 00 00 00
0.0        00 00 00 00 00 00 00 00
-0.0       00 00 00 00 00 00 00 80
__STDC_IEC_559__ = 1
```

```text
===== 모든 비트 0 — 빌드 4 벌이 같은가 (exit=0) =====
빌드 4 벌 (gcc/clang × -O0/-O2) · 서로 다른 출력 1 가지
```

**왜 그런가**

- ★★★ **정수** — 「모든 비트가 0 인 표현은 그 타입의 값 0」이 표준 문장이다.
- ★★ **`double`** — 부록 F(IEC 60559)를 따르면 형식이 정해지고 그 형식의 `+0` 이 모든 비트 0 이다. 이 판은 `__STDC_IEC_559__ = 1`. 매크로가 없는 구현에서는 **보장이 없다.**
- ★★★ **포인터·함수 포인터** — `calloc` 각주가 「**널 포인터 상수의 표현과 같을 필요가 없다**」고 적는다. 이 판에서 네 줄이 다 참인 것은 **구현이 그랬을 뿐**이다([19번 형제](../19-void-pointer-null-pointer-and-null/) (8)절).
- ★★ **`-0.0` 의 바이트는 `00 00 00 00 00 00 00 80`** — `memset` 0 이 만드는 것은 `+0.0` 이다.

### 8. `gcc -O2 -dM -E` 의 한 줄 — **`_FORTIFY_SOURCE 3` · gcc `-O2` 열을 0 칸으로 만들었다 · 배포판의 일** ★★

**출력**

```text
===== gcc -O2 -dM -E - < /dev/null | grep -E '_FORTIFY_SOURCE' (cc exit=0) =====
#define _FORTIFY_SOURCE 3
```

```text
===== gcc -std=c17 -O2 -fsanitize=address -c s50a.c -o a.o && objdump -dr a.o | grep -oE 'R_X86_64_PLT32[[:space:]]+(__)?mem[a-z_]+' | sort | uniq -c | expand (exit=0) =====
      1 R_X86_64_PLT32  __memcpy_chk
      1 R_X86_64_PLT32  __memmove_chk
      1 R_X86_64_PLT32  memcpy
```

```text
===== gcc -std=c17 -O2 -U_FORTIFY_SOURCE -fsanitize=address -c s50a.c -o a.o && objdump -dr a.o | grep -oE 'R_X86_64_PLT32[[:space:]]+(__)?mem[a-z_]+' | sort | uniq -c | expand (exit=0) =====
      2 R_X86_64_PLT32  memcpy
      1 R_X86_64_PLT32  memmove
```

**왜 그런가**

- ★★ **`-O2` 에서 `_FORTIFY_SOURCE` 가 3 으로 정의된다** — 명령에도 소스에도 없다. 그러면 glibc 헤더가 `memcpy`·`memmove` 를 **`__memcpy_chk`·`__memmove_chk`** 로 돌린다(재배치 심볼이 바뀐다).
- ★★ **그 호출에서 ASan 은 겹침을 말하지 않았다** — 1번 격자의 gcc `-O2` 열 0 칸, 같은 열에 `-U_FORTIFY_SOURCE` 를 더하면 2 칸.
- ★ **층** — C 표준에 `_FORTIFY_SOURCE` 는 없다. **glibc 의 기능 + Ubuntu gcc 의 기본값**이다.

### 9. 33번 형제와 이어서 — **서명의 `__restrict` · 겹친 `memcpy` 가 이 glibc 에서 낸 글자 · 루프 → `memcpy` 변환은 그쪽이 쟀다** ★★

**왜 그런가**

- [33번 형제](../33-restrict-and-the-aliasing-contract/) (6)절 — `string.h` 의 `memcpy` 두 포인터에 `__restrict`, `memmove` 에는 없다 · 겹친 `memcpy` 가 네 빌드에서 `memmove` 와 **같은 글자**(관찰) · ASan 두 컴파일러 `memcpy-param-overlap`. (2)·(4)절 — 루프가 `jmp memcpy` 가 되고 **그 판에서만** ASan 이 답했다.
- ★★ **이 편이 더한 칸** — ① **크기 축**(상수 8 은 인라인되어 ASan 이 거의 못 본다) ② **`_FORTIFY_SOURCE` 축**(gcc `-O2` 기본 판은 실행 시 크기도 못 본다). 33편이 「ASan 이 겹침을 보는 유일한 경로」라고 적은 그 경로가 **언제 끊기는지**다.

### 10. 다섯 층과 네 번째 창 ★★★

**왜 그런가**

- **표준** — `memmove` 의 겹침 처리 · `memset` 의 `unsigned char` 변환 · `memcmp` 의 부호 · 정수의 모든 비트 0.
- **조건부 표준** — `__STDC_IEC_559__` 아래의 `+0.0` 표현 · `-0.0 == 0.0` · NaN 의 자기 불일치.
- **구현(과 배포판)** — 널 포인터 표현 · 인라인 여부 · `_FORTIFY_SOURCE=3` 기본값 · ASan 이 가로채는 심볼.
- **미명시** — 패딩 바이트 · `memcmp` 반환의 크기.
- **UB** — 겹친 `memcpy`.
- ★★★ **네 번째 창 = 오브젝트의 재배치 심볼.** ASan 이 조용할 때 **「호출이 남아 있었나」** 를 묻는다. 못 보는 것 — **호출이 남아 있어도 그 함수가 겹침을 재는지**는 모른다(`__memcpy_chk` 가 그랬다 — 그것은 1번 격자의 실행으로만 알았다).

### 11. 경계 ★

**왜 그런가**

- **패딩 덤프** — [22번 형제](../22-struct-padding-and-alignment/) (3)절. **`calloc` 의 0** — [37번 형제](../37-malloc-calloc-realloc-free/) · [30번 형제](../30-initialization-rules-and-indeterminate-values/).
- **`strcpy`·`strncpy`** — [목록의 **49번 주제**](../49-string-functions-and-pitfalls/).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s50a.c` | ★★★ **겹침 격자 · ASan 10 / 60** · 리포트 전문 · 재배치 두 판 · 경고 0 | 빌드 6 · 실행 68 · 리포트 1 · 재배치 2 · 진단 1 |
| `s50f.c` | ★★ 인라인 격자 32 칸 · `copy8` 덤프 | 빌드 8 · 덤프 9 |
| `s50g.c` | ★★ `-Wrestrict` 두 줄 · clang 0 | 진단 2 |
| `s50b.c` | ★★★ `-0.0` · NaN 두 방향 | 빌드 4 |
| `s50c.c` | ★★★ 패딩 격자 · 20 판 × 빌드 6 | 실행 121 |
| `s50d.c` | ★★ 모든 비트 0 · 네 빌드 한 가지 | 실행 5 |
| `s50e.c` | ★★ `16843009` · 경고 0 | 2 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. 흔들린 칸은 **리포트의 PID · 주소 · `BuildId`** 뿐이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1번의 ASan 열 다섯** — 인라인 판단(컴파일러) · `_FORTIFY_SOURCE` 기본값(배포판) · 가로채는 심볼(ASan 판).
- ★★★ **5번 패딩 격자 전부.**
- ★★ **7번의 포인터 두 줄** — 이 구현의 널 표현.

**`memmove` 의 결과 · `memset` 의 바이트 반복 · 정수의 모든 비트 0 · `memcmp` 가 바이트를 비교한다는 것 · 겹친 `memcpy` 가 UB 인 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `memset_explicit`·`memccpy`(C23) · 다른 배포판 gcc · 인라인된 호출처에서 `shift_var` 경고가 나는지.
- ★ **부적용** — 시간 측정(성능 주제가 아니다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 · 2번 격자** — 인라인 판단 · ASan 이 `__memcpy_chk` 를 가로채기 시작하는지.
- ★★ **3번** — clang 이 겹침 경고를 얻는지.
- ★★ **5번** — 최적화기의 구조체 반환 방식.

## 실행 환경

이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **glibc 2.39** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
소스는 `s50a.c`\~`s50g.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
★★★ **본체 창은 겹침 격자** — 12 줄 × ASan 5 벌.
★★ **흔들리는 칸** — 리포트의 PID · 주소 · `BuildId`(정규화 기본 규칙). 패딩 격자는 **빌드 사이**에서 갈린다(선언).
