# c/syntax/50 — `<string.h>` 메모리 함수: 「**`memcpy` 는 겹치지 않는다는 약속 위에 서고, `memset`·`memcmp` 는 값이 아니라 바이트를 다룬다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `memcpy` 의 「**If copying takes place between objects that overlap, the behavior is undefined.**」, `memmove` 의 「**as if the n characters … are first copied into a temporary array**」, `memset` 의 「**the value of c (converted to an unsigned char)**」, `memcmp` 각주의 「**padding … take on unspecified values**」, 정수 표현 절의 「**all the bits are zero shall be a representation of the value zero**」, `calloc` 각주의 「**need not be the same as the representation of floating-point zero or a null pointer constant**」를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **결과 바이트 · ASan 리포트 · 경고 · 재배치 심볼은 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`, 캡처 셸은 `LC_ALL=C`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다. 이 편의 **그림 6 · 덤프(캡처 블록) 20**.
> **버전** — 네 함수는 **C89 부터** 있다. ★ `memcpy` 매개변수의 `restrict` 는 **C99** 부터다(C89 에는 `restrict` 가 없다). 이 편의 규칙은 C11 · C17 · C23 사이에 **바뀌지 않았다**.
> ★★★ **경계** — **`restrict` 의 뜻 · 앨리어싱 · 루프가 `memcpy` 로 바뀌는 것**은 [33번 형제](../33-restrict-and-the-aliasing-contract/)가 정본이다(그쪽 (2)·(4)·(6)절 — 이 편은 **다시 재지 않고** 인용한다). **패딩 바이트의 덤프 · 20 판 가짓수**는 [22번 형제](../22-struct-padding-and-alignment/)의 (3)절, **널 포인터의 바이트**는 [19번 형제](../19-void-pointer-null-pointer-and-null/)의 (8)절, **`calloc` 의 0** 은 [37번 형제](../37-malloc-calloc-realloc-free/)·[30번 형제](../30-initialization-rules-and-indeterminate-values/)가 정본이다. **문자열 함수**(`strcpy`·`strncpy`)는 목록의 **49번 주제**다.
> 선행 — [33번 형제](../33-restrict-and-the-aliasing-contract/) · 목록의 **49번 주제**.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 셋째 창 — sanitizer 의 겹침 격자다.** 함수 둘(`memcpy`·`memmove`) × 겹침 셋 × 크기 둘(실행 시 값 · 상수 8)을 **ASan 빌드 다섯 벌**에 돌려 칸마다 「**ASan 이 무엇을 말했나**」를 찍는다.
★★★ 그 격자에서 **ASan 이 잡은 칸 10 / 60** — `memcpy` 겹침 **스물 칸 중 열 칸이 침묵**했고, 침묵은 **두 갈래 이유**(상수 크기의 인라인 · 배포판 기본 `_FORTIFY_SOURCE`)로 갈렸다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | gcc `-Wrestrict` 가 **글자로 보이는 겹침**만 잡는다 · clang **0건**((3)) | 씀 |
| ② 실행 출력 | `memmove` 결과 · 멤버 `==` 대 `memcmp` · `memset` 의 `16843009` · 「모든 비트 0」 | 씀 |
| ★★★ ③ **sanitizer(겹침 격자)** | ★ **본체** — ASan `memcpy-param-overlap` 이 **어느 빌드 · 어느 크기에서** 나오나 | 씀 |
| ④ 오브젝트 재배치 | ★★ **`memcpy` 가 호출로 남나 · `__memcpy_chk` 로 바뀌나** — `objdump -dr` 의 심볼((2)·(4)) | 씀 |
| 시간 측정 | 「`memcpy` 가 `memmove` 보다 빠르다」 | ★ **부적용** — 재지 않았다(재지 않은 성능 주장 금지). 인라인 여부는 **명령의 모양**이지 속도가 아니다 |
| ★ 제5의 상태 | 「겹친 `memcpy` 의 결과는 무엇인가」는 **값으로 물을 수 없다**(UB — 싣지 않는다) — **ASan 의 가로채기**로 바꿔 물었다. ★ 그런데 그 창은 **`memcpy` 호출이 남아 있을 때만** 열린다 — 호출이 사라졌는지를 **재배치 심볼**로 한 번 더 물었다 | 창을 바꿔 답함 |

★ **바꾼 창(ASan 가로채기)이 못 보는 것** — **인라인된 복사**(상수 8 바이트가 `mov` 두 개가 되면 가로챌 호출이 없다) · **`__memcpy_chk` 로 바뀐 호출**(이 판의 gcc `-O2` 기본). 두 경우 다 **리포트 0 줄, 종료 코드 0** 이다.

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== ldd --version | sed -n 1p (exit=0) =====
ldd (Ubuntu GLIBC 2.39-0ubuntu8.9) 2.39
```

```text
===== gcc -O2 -dM -E - < /dev/null | grep -E '_FORTIFY_SOURCE' (cc exit=0) =====
#define _FORTIFY_SOURCE 3
```

★★ **이 gcc 는 `-O2` 에서 `_FORTIFY_SOURCE` 를 스스로 3 으로 정의한다**(Ubuntu 의 기본값 — 소스도 명령도 이 매크로를 적지 않았다). 1번 격자의 한 열이 이 한 줄 때문에 바뀐다((4)).

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ASan 리포트의 **PID**(`==N==`) · **주소**(`0x…`) · `BuildId` | 실행·빌드마다 다르다 — `normalize-shaky.py` 의 기본 규칙이 지운다 |
| 안 흔들린다 | ★★★ **겹침 격자 60 칸 전부** · 재배치 격자 · 경고 | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다(선언) | ★★ **패딩 격자의 「20 판 중 N 판」** | 이 판에서는 빌드마다 **20/20 또는 0/20** 으로 갈렸다 — 판 사이가 아니라 **빌드 사이**에서 흔들린다. ★ **보장이 아니다**(패딩은 미명시) |
| 안 흔들린다 | 리포트의 **`파일:줄:칸`** · `SUMMARY` 줄 · `located 2 bytes inside of global variable 'buf'` | `-ffile-prefix-map` 과 `strip_path_prefix` 로 경로를 죽였다 |

★★ **정규화 규칙은 기본 넷뿐**이다 — 위 표의 첫 줄과 같은 목록이다.

## 한눈에 — 쉽게 말하면

**메모리 함수 넷은 「이삿짐 센터」의 네 가지 일이다.**

- **`memmove` 는 「짐을 전부 트럭에 실었다가 내린다」** — 옮길 자리가 원래 자리와 겹쳐도 짐이 안 섞인다. → **임시 배열을 거친 것처럼**
- **`memcpy` 는 「두 집이 안 겹친다고 계약서에 서명하고」 바로 나른다** — 겹치는 이사를 맡기면 **계약 위반**이다. 무엇이 벌어질지 계약서에 없다. → **겹치면 UB**
- **`memset` 은 「방마다 같은 벽지 한 장」을 바른다** — 방(바이트)이 넷인 큰 방(`int`)에 `1` 을 바르면 **네 방 모두 1** 이 되어 큰 방은 `0x01010101` 이다. → **바이트 단위**
- **`memcmp` 는 「두 집의 사진을 픽셀째 비교」한다** — 가구(멤버)가 같아도 **벽 틈의 먼지(패딩)** 가 다르면 「다르다」고 한다. 가구가 같은지를 묻는 게 아니다. → **바이트 비교**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 트럭에 실었다 내리기 | `memmove` 의 「임시 배열처럼」 | ★ 격자의 `ABABCDEFGHKLMNOP` |
| 안 겹친다는 서명 | `memcpy` 의 `restrict` 매개변수 · 「겹치면 UB」 | ★★★ ASan `memcpy-param-overlap` — **10 / 60 칸만** |
| 서명을 보는 검사관 | ASan 의 `memcpy` 가로채기 | ★★ **호출이 남아 있을 때만** — 인라인 · `__memcpy_chk` 는 못 본다 |
| 방마다 같은 벽지 | `memset(a, 1, sizeof a)` | ★★ `16843009` |
| 픽셀 비교 | `memcmp` | ★★★ `-0.0` 은 「다르다」 · NaN 복사본은 「같다」 |

```text
   memmove(buf + 2, buf, 8)                 memcpy(buf + 2, buf, 8)
   ------------------------------------     ------------------------------------
   "먼저 임시 배열에 8 글자를 떠 둔다"         "두 영역이 안 겹친다"를 호출자가 약속했다
   A B C D E F G H  -> tmp                  겹친다  ->  UB
   tmp -> buf+2                             결과를 적지 않는다
   ABABCDEFGHKLMNOP  (보장)                  ASan 이 호출을 가로챘을 때만
                                            memcpy-param-overlap 으로 말한다
```

- ★★★ **이 주제의 본체는 「표준」 칸과 「UB」 칸의 경계**다 — `memmove` 의 겹침 처리 · `memset` 의 `unsigned char` 변환 · 정수의 「모든 비트 0 = 0」이 **표준**이고, **겹친 `memcpy`** 가 **UB** 다.
- ★★ **「미명시」 칸** — 패딩 바이트의 값. 그래서 패딩이 있는 구조체의 `memcmp` 는 **답이 정해져 있지 않다.**

> **`memcpy(d, s, n)`** — `s` 의 `n` 바이트를 `d` 로 복사한다. 두 매개변수가 `restrict` — **겹치면 UB.**\
> 예: `memcpy(dst, src, sizeof *src);`.

> **`memmove(d, s, n)`** — 같은 복사를 **겹쳐도 되게** 한다 — 「임시 배열을 거친 것처럼」.\
> 예: `memmove(buf + 1, buf, len);`(한 칸 밀기).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`memcpy` 와 `memmove` 는 무엇으로 고르고, 겹친 `memcpy` 를 누가 보나** — 결과 · ASan · 경고.
2. ★★★ **`memcmp` 는 언제 멤버 비교와 다른 답을 내나** — 패딩 · `-0.0` · NaN.
3. ★★ **`memset` 은 무엇을 채우나** — 바이트 단위 · 「모든 비트 0」이 `int`·포인터·`double` 에게 각각 무엇인가.

## 동작 방식

### (1) ★★★ 겹침 격자 — 함수 둘 × 겹침 셋 × 크기 둘 × ASan 다섯 벌

**언제 쓰나** — 버퍼 안에서 데이터를 밀거나 당길 때 **어느 함수를 부를지** · 「ASan 이 조용하니 괜찮다」를 믿어도 되는지 판단할 때. ★★★ **이 편의 본체**다.

```c
/* s50a.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char buf[32];

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 4) return 2;
    int fn = argv[1][0] == 'c';            /* c = memcpy, m = memmove */
    int mode = atoi(argv[2]);              /* 0 = none, 1 = dst after src, 2 = dst before src */
    int fixed = argv[3][0] == 'k';         /* k = constant 8, r = size read at run time */
    volatile size_t n = 8;
    strcpy(buf, "ABCDEFGHIJKLMNOP");
    char *d = mode == 0 ? buf + 8 : mode == 1 ? buf + 2 : buf;
    char *s = mode == 2 ? buf + 2 : buf;
    if (fn && fixed)       memcpy(d, s, 8);
    else if (fn)           memcpy(d, s, n);
    else if (fixed)        memmove(d, s, 8);
    else                   memmove(d, s, n);
    printf("%s\n", buf);
    return 0;
}
```

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
   겹침 셋 (buf = "ABCDEFGHIJKLMNOP", 8 바이트)

   없음        buf+8 <- buf      [ABCDEFGH][IJKLMNOP]      겹치지 않는다(맞닿기만)
   dst > src   buf+2 <- buf      [AB[CDEFGH]IJ]KLMNOP      뒤로 밀기 — 앞에서부터 베끼면 덮어 쓴다
   dst < src   buf   <- buf+2    [[AB]CDEFGHIJ]KLMNOP      앞으로 당기기
```

그림 해설 (한 단계씩):

- ★★★ **`memmove` 는 두 겹침 모두 뜻이 있다** — `dst > src` 는 `ABABCDEFGHKLMNOP`(원래의 `ABCDEFGH` 가 두 칸 밀려 앉았다) · `dst < src` 는 `CDEFGHIJIJKLMNOP`. **크기가 실행 시 값이든 상수든 같다** — 표준이 「임시 배열을 거친 것처럼」을 약속했기 때문이다.
- ★★★ **`memcpy` 의 겹침 네 줄은 결과를 싣지 않았다** — 표준 문장이 **UB** 다. 돌려서 나온 글자는 「이 판에서 나온 것」일 뿐 C 의 결과가 아니다([33번 형제](../33-restrict-and-the-aliasing-contract/) (6)절이 이 glibc 에서 `memmove` 와 같은 글자가 나온 것을 **관찰로** 적어 두었다).
- ★★★ **ASan 이 잡은 칸 10 / 60** — 잡은 열 칸은 **전부 `memcpy` 겹침**이고, `memmove` 스물네 칸과 겹침 없는 `memcpy` 여덟 칸에서는 **한 칸도 말하지 않았다**(오탐 0).
- ★★★ **`memcpy` 겹침 스무 칸 중 열 칸이 침묵했다** — ① **상수 8 줄**은 clang `-O0` 한 벌만 잡았다 ② **gcc `-O2` 열**은 실행 시 크기조차 **한 칸도 못 잡았다.** 같은 열에서 **`-U_FORTIFY_SOURCE` 만 더한 판**은 잡는다.

비용 — **`memmove` 는 겹침을 처리하는 대신 약속을 요구하지 않는다.** 속도 차이는 **재지 않았다.**

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

- ★★ **리포트가 두 영역을 반열림 구간으로 적는다** — `[…a2,…aa)` 와 `[…a0, …a8)` · 그리고 **둘 다 `buf` 안**이라고 짚는다(`2 bytes inside` · `0 bytes inside`). **스택의 `#1` 이 `s50a.c:18:28`** — `else if (fn) memcpy(d, s, n);` 줄이다.
- ★ `#0` 이 **`__asan_memcpy`** 다 — clang ASan 판의 `memcpy` 호출은 **ASan 의 함수로 바뀌어** 있다((2)의 격자).

### (2) ★★ `memcpy` 는 호출로 남는가 — 재배치 격자

**언제 쓰나** — 「ASan 이 겹침을 잡는다」를 **내 코드의 이 줄**에 대해 믿어도 되는지 확인할 때. 1번의 상수 8 줄이 왜 조용했는지의 답이다.

```c
/* s50f.c */
#include <string.h>

void copy8(void *d, const void *s) { memcpy(d, s, 8); }
void copy32(void *d, const void *s) { memcpy(d, s, 32); }
void copyn(void *d, const void *s, size_t n) { memcpy(d, s, n); }
void move8(void *d, const void *s) { memmove(d, s, 8); }
```

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

```text
===== gcc -std=c17 -O2 -c s50f.c -o f.o && objdump -dr --no-show-raw-insn -M intel f.o | awk '/<copy8>:/,/ret/' | expand (exit=0) =====
0000000000000000 <copy8>:
   0:   endbr64
   4:   mov    rax,QWORD PTR [rsi]
   7:   mov    QWORD PTR [rdi],rax
   a:   ret
```

- ★★★ **크기가 상수인 `copy8` 은 여덟 빌드 중 일곱에서 호출이 사라졌다** — `-O2` 는 `mov` 두 개(8 바이트 읽고 쓰기), `-O0` 도 인라인이다. **ASan 을 켜도 gcc 두 벌 · clang `-O2` 는 인라인 + 경계 검사**(`__asan_report_load_n/store_n`)뿐이다 — **경계는 보지만 겹침은 안 본다.**
- ★★★ **clang `-O0 -fsanitize=address` 만 `copy8` 을 `__asan_memcpy` 호출로 남겼다** — 그래서 1번에서 **clang `-O0` 열만 상수 8 줄을 잡았다.** 두 격자가 **같은 사실을 두 창에서** 말한다.
- ★★ **크기를 모르는 `copyn` 은 여덟 벌 다 호출**이다 — gcc 는 `memcpy`(ASan 런타임이 그 심볼을 가로챈다), clang ASan 은 `__asan_memcpy`.
- ★ **`memmove` 도 같은 운명**이다 — `move8` 은 `memmove` 호출조차 없이 인라인된다(8 바이트를 **다 읽고 나서 쓰면** 겹쳐도 뜻이 맞는다).
- ★★ **이 격자는 속도가 아니라 「검사가 설 자리가 있느냐」를 말한다** — 인라인이 빠른지는 **재지 않았다.**

### (3) ★★ 컴파일러 경고 — 글자로 보이는 겹침만

**언제 쓰나** — 「겹치면 컴파일러가 말해 주겠지」라고 생각할 때.

```c
/* s50g.c */
#include <string.h>

static char buf[32] = "ABCDEFGHIJKLMNOP";

void shift_right(void) { memcpy(buf + 2, buf, 8); }
void shift_left(void) { memcpy(buf, buf + 2, 8); }
void shift_var(char *d, const char *s) { memcpy(d, s, 8); }
```

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

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s50a.c -o /dev/null (cc exit=0) =====
```

- ★★★ **gcc 는 `buf + 2, buf, 8` 처럼 주소와 크기가 전부 보이는 두 줄만** `-Wrestrict` 로 잡는다 — `accessing 8 bytes at offsets 2 and 0 overlaps 6 bytes at offset 2`. **겹친 바이트 수까지** 계산했다.
- ★★ **`shift_var` 는 0 건**이다 — 포인터가 매개변수로 오면 **값을 모른다.** 1번의 `s50a.c` 도 `-O2` 에서 **경고 0 줄**이다(주소를 실행 시 고른다).
- ★★ **clang 은 세 함수 다 0 건**이다 — [33번 형제](../33-restrict-and-the-aliasing-contract/) (5)절의 `restrict` 매개변수 실측과 같은 모양이다.

### (4) ★★ gcc `-O2` 열이 비는 이유 — `__memcpy_chk`

**언제 쓰나** — 같은 ASan 인데 **최적화 수준을 올리자 리포트가 사라졌을 때.**

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

```text
   gcc -O2 (이 판의 기본)                     gcc -O2 -U_FORTIFY_SOURCE
   ---------------------------------------    ---------------------------------------
   _FORTIFY_SOURCE=3 이 스스로 정의된다          매크로가 없다
   memcpy(d, s, n)  -> __memcpy_chk(...)        memcpy(d, s, n)  -> memcpy
   memmove(d, s, n) -> __memmove_chk(...)       memmove(d, s, n) -> memmove
   ASan 이 겹침을 재지 않는 경로                  ASan 이 가로채는 경로
   1번 격자: 0 칸                                1번 격자: 2 칸 (실행 시 크기 두 줄)
```

- ★★★ **호출의 이름이 바뀌었다** — 기본 판은 `__memcpy_chk`·`__memmove_chk`(glibc 의 **목적지 크기 검사 판**), 매크로를 지운 판은 `memcpy`·`memmove`. ★ 두 판 모두에 남은 `memcpy` 하나는 이 표로는 **어느 줄의 것인지 가리지 않았다**(겹침 줄의 호출은 위의 두 이름이다).
- ★★ **`__memcpy_chk` 는 「목적지가 넘치나」를 보는 함수**다 — **「겹치나」는 안 본다.** 그리고 이 판의 ASan 은 그 호출에서 **겹침 리포트를 내지 않았다**(1번 격자의 gcc `-O2` 열 — 실측).
- ★★ **층** — `_FORTIFY_SOURCE` 는 **C 표준에 없다.** glibc 의 기능이고, **그것을 `-O2` 에 켜 둔 것은 배포판(Ubuntu) 의 컴파일러 설정**이다. 같은 gcc 13 이라도 다른 배포판에서는 이 열이 달라질 수 있다(★ 다른 배포판은 **돌려 보지 않았다**).

### (5) ★★★ 멤버 `==` 와 `memcmp` — 양쪽으로 갈린다

**언제 쓰나** — 구조체 두 개가 「같은가」를 **`memcmp` 한 줄로** 끝내고 싶을 때.

```c
/* s50b.c */
#include <math.h>
#include <stdio.h>
#include <string.h>

struct D { double v; };

static const char *eq(struct D a, struct D b) { return a.v == b.v ? "same" : "diff"; }
static const char *mc(struct D a, struct D b) { return memcmp(&a, &b, sizeof a) == 0 ? "same" : "diff"; }

int main(void) {
    struct D p = { 0.0 }, q = { -0.0 };
    struct D x = { NAN }, y = x;
    printf("{0.0} vs {-0.0}   member == : %s   memcmp : %s\n", eq(p, q), mc(p, q));
    printf("{NAN} vs copy     member == : %s   memcmp : %s\n", eq(x, y), mc(x, y));
    return 0;
}
```

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

```text
                    멤버 ==         memcmp        왜
   {0.0} vs {-0.0}   same           diff          -0.0 == 0.0 은 참(값) · 부호 비트가 다르다(바이트)
   {NAN} vs 복사본    diff           same          NaN == NaN 은 거짓(값) · 비트는 한 글자도 같다(바이트)
```

- ★★★ **두 방향으로 다 갈렸다** — 값이 같은데 바이트가 다른 쌍(`0.0`/`-0.0`)과 **바이트가 같은데 값이 다른 쌍**(NaN 과 그 복사본). 「`memcmp` 가 0 이면 같은 값이다」도 「같은 값이면 `memcmp` 가 0 이다」도 **둘 다 틀렸다.**
- ★★ **네 빌드가 같은 답**이다 — 이 두 줄은 **패딩이 없어서** 판을 안 탄다. 판을 타는 것은 (6)이다.
- ★ `-0.0 == 0.0` 이 참이고 NaN 이 자기와 다르다는 **값의 규칙**은 [04번 형제](../04-floating-point-types-and-conversions/) (5)절이 정본이다.

### (6) ★★★ 패딩이 있는 구조체 — 빌드마다 답이 다르다

**언제 쓰나** — 패딩이 있는 구조체를 `memcmp`·해시·전송에 쓸 때.

```c
/* s50c.c */
#include <stdio.h>
#include <string.h>

struct S { char c; int i; };               /* 1 byte, 3 bytes of padding, 4 bytes */

static void dirty(void) {
    volatile unsigned char junk[64];
    for (int k = 0; k < 64; k++) junk[k] = (unsigned char)(0xA0 + k);
}

static struct S by_member(void) {
    struct S v;
    v.c = 'x'; v.i = 7;
    return v;
}

static struct S by_memset(void) {
    struct S v;
    memset(&v, 0, sizeof v);
    v.c = 'x'; v.i = 7;
    return v;
}

int main(void) {
    dirty(); struct S a = by_member();
    dirty(); struct S b = by_memset();
    struct S m;
    memset(&m, 0, sizeof m);
    m.c = 'x'; m.i = 7;
    printf("members a,b equal : %d\n", a.c == b.c && a.i == b.i);
    printf("memcmp(a, b)      : %s\n", memcmp(&a, &b, sizeof a) ? "nonzero" : "zero");
    printf("memcmp(b, m)      : %s\n", memcmp(&b, &m, sizeof b) ? "nonzero" : "zero");
    return 0;
}
```

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

- ★★★ **멤버는 여섯 빌드 · 120 판 전부 같다** — 그런데 `memcmp(a, b)` 는 **빌드에 따라 20/20 이 「다르다」 또는 0/20 이 「다르다」** 이다. 같은 소스가 **빌드를 바꾸면 반대 답**을 낸다. 패딩 값이 **미명시**이기 때문이다(표준 각주 — 패딩은 값이 저장될 때 **unspecified values** 를 가진다).
- ★★★ **`memset` 으로 지우고 만든 `b` 와 `m` 조차 gcc `-O1` 에서 20/20 「다르다」** — `b` 는 **함수가 값으로 돌려준 구조체**다. 돌려주는 길에 패딩이 **다시 채워졌다.** 「`memset` 했으니 패딩은 0 이다」는 **`memset` 한 그 객체에서만** 참이다([22번 형제](../22-struct-padding-and-alignment/)의 「어디서 틀리나」 2번 — clang `-O1` 의 꼬리 구멍 — 과 같은 모양을 **다른 빌드에서** 다시 만났다).
- ★★ **한 빌드 안에서는 20 판이 전부 같았다** — 흔들림은 **판 사이가 아니라 빌드 사이**다. ★ **그래도 보장이 아니다** — 이 격자는 「이 판에서 이랬다」까지만 말한다. 바이트 덤프와 판마다 달라지는 사례는 [22번 형제](../22-struct-padding-and-alignment/) (3)절이 정본이다.

비용 — **구조체 비교는 멤버를 하나씩 비교하는 함수를 쓴다.** `memcmp` 를 쓰려면 **패딩 없는 배치 + 부동소수 멤버 없음**이 둘 다 필요하다.

### (7) ★★ `memset` 은 바이트 단위다

**언제 쓰나** — `int`·`double` 배열을 **0 이 아닌 값으로** 채우고 싶을 때.

```c
/* s50e.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    int a[4];
    memset(a, 1, sizeof a);
    printf("memset(a, 1)   : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    memset(a, -1, sizeof a);
    printf("memset(a, -1)  : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    memset(a, 0x101, sizeof a);
    printf("memset(a, 257) : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    for (int k = 0; k < 4; k++) a[k] = 1;
    printf("loop a[k] = 1  : %d %d %d %d\n", a[0], a[1], a[2], a[3]);
    return 0;
}
```

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

```text
   memset(a, 1, 16)   바이트마다 0x01

   a[0] = 01 01 01 01  -> 0x01010101 = 16843009
   a[1] = 01 01 01 01
   ...

   memset(a, 257, 16)  257 을 unsigned char 로 -> 1  (위와 같다)
   memset(a, -1, 16)   -1  을 unsigned char 로 -> 0xFF -> 모든 바이트 0xFF = int -1
```

- ★★★ **`memset(a, 1, …)` 은 `int` 를 1 로 만들지 않는다** — `16843009`(`0x01010101`). 둘째 인자는 **`unsigned char` 로 바뀐 한 바이트**다(표준 문장 그대로).
- ★★ **`-1` 이 「맞게」 나온 것은 우연이 아니라 산술**이다 — 모든 바이트 `0xFF` 가 이 판의 `int` 에서 `-1` 이다(2의 보수 — C23 부터는 표준이 2의 보수를 요구한다). **`0` 과 `-1` 말고는** 바이트 반복이 원하는 `int` 를 만들지 않는다.
- ★★ **경고 0 줄**이다 — `-Wall -Wextra -pedantic` 은 이 실수를 **말하지 않는다.**
- ★ 채우고 싶으면 **루프**다 — 넷째 줄.

### (8) ★★★ 「모든 비트 0」은 무엇의 0 인가 — 층이 셋이다

**언제 쓰나** — 구조체를 `memset(&s, 0, sizeof s)` 로 밀고 「포인터는 널, `double` 은 `0.0`」이라고 넘어갈 때.

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

```text
   memset(&x, 0, sizeof x) 뒤에         이 판에서       누가 보장하나
   ---------------------------------    ------------    ----------------------------------------
   int     i == 0                        1              ★ 표준 — 정수는 모든 비트 0 이 값 0
   double  d == 0.0 · signbit 0          1 · 0          ★ 조건부 표준 — __STDC_IEC_559__ 이면
                                                          IEC 60559 형식이고 +0 은 모든 비트 0
   void *  p == NULL                     1              ★ 없음 — 구현이 그랬을 뿐
   함수 포인터 f == NULL                  1              ★ 없음
```

- ★★★ **네 줄 다 「참」이지만 근거가 셋으로 갈린다** — 정수는 **표준 문장**(「모든 비트가 0 인 표현은 그 타입의 값 0」), `double` 은 **부록 F 를 따를 때만**(이 판은 `__STDC_IEC_559__ = 1`), 포인터는 **아무도** — `calloc` 의 각주가 「**부동소수 0 이나 널 포인터의 표현과 같을 필요가 없다**」고 적는다.
- ★★ **`-0.0` 의 바이트는 `00 … 80`** 이다 — `memset` 0 이 만드는 것은 **`+0.0`** 이다. 둘은 `==` 로는 같고 바이트로는 다르다((5)).
- ★★ **네 빌드 · 서로 다른 출력 1 가지** — 그래서 더 위험하다. 어느 판에서도 참이 나오니 **가정이 굳는다.** 포인터 쪽의 상세는 [19번 형제](../19-void-pointer-null-pointer-and-null/) (8)절이 정본이고, 이 편은 **`double` 과 함수 포인터 칸**을 더했다.

## 문법 — 형태와 규칙

### 형태

```c
/* s50a.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char buf[32];

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    if (argc < 4) return 2;
    int fn = argv[1][0] == 'c';            /* c = memcpy, m = memmove */
    int mode = atoi(argv[2]);              /* 0 = none, 1 = dst after src, 2 = dst before src */
    int fixed = argv[3][0] == 'k';         /* k = constant 8, r = size read at run time */
    volatile size_t n = 8;
    strcpy(buf, "ABCDEFGHIJKLMNOP");
    char *d = mode == 0 ? buf + 8 : mode == 1 ? buf + 2 : buf;
    char *s = mode == 2 ? buf + 2 : buf;
    if (fn && fixed)       memcpy(d, s, 8);
    else if (fn)           memcpy(d, s, n);
    else if (fixed)        memmove(d, s, 8);
    else                   memmove(d, s, n);
    printf("%s\n", buf);
    return 0;
}
```

- 네 함수 모두 **`void *` 를 받아** 바이트 수 `n` 만큼 일한다 — 타입을 모른다.
- **반환값은 첫 인자**(`memcpy`·`memmove`·`memset`) · `memcmp` 는 **부호만** 뜻이 있다(크기는 미명시 — [22번 형제](../22-struct-padding-and-alignment/) (3)절이 이 판의 크기를 찍어 두었다).

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 도구 | 층 | 절 |
|---|---|---|---|
| `memcpy(buf + 2, buf, 8)` (글자로 보임) | gcc `-Wrestrict` · clang 0 | ★★★ UB | (3) |
| `memcpy(d, s, n)` (실행 시 겹침) | 경고 0 · ASan **빌드에 따라** | ★★★ UB | (1)·(4) |
| `memcmp(&a, &b, sizeof a)` (패딩 있는 구조체) | 경고 0 · 도구 0 | ★★ 미명시(답이 정해지지 않음) | (6) |
| `memcmp` 로 `double` 멤버 비교 | 경고 0 | ★★ 적법 — 값이 아니라 바이트를 물었을 뿐 | (5) |
| `memset(a, 1, sizeof a)` (`int` 배열) | 경고 0 | 적법 — 뜻이 다를 뿐 | (7) |
| `memset(&p, 0, sizeof p)` 로 널 만들기 | 경고 0 | ★ 구현 의존 | (8) |

### 규칙 불릿

- ★★★ **겹칠 수 있으면 `memmove`.** 「겹치지 않는다」를 **증명할 수 있을 때만** `memcpy`.
- ★★★ **구조체 비교는 멤버 비교.** `memcmp` 는 **바이트가 곧 뜻인 데이터**(바이트 배열 · 패딩 없는 정수 구조체)에만.
- ★★ **`memset` 은 0 과 `0xFF` 말고는 「값 채우기」가 아니다.**
- ★★ **널 포인터가 필요하면 `= NULL` 을 쓴다.** 「모든 비트 0」에 기대는 코드는 **이 판의 성질**에 기대는 것이다.

## 어디서 틀리나

### 1. ★★★ 「ASan 을 켰고 조용했으니 겹침은 없다」

**ASan 은 호출을 가로챌 때만 본다**((1)·(2)). 크기가 상수라 인라인되면, 또는 이 판의 gcc `-O2` 처럼 `__memcpy_chk` 로 바뀌면 **리포트 0 줄**이다. **1번 격자의 `memcpy` 겹침 스무 칸 중 열 칸이 그랬다.**

### 2. ★★★ 「겹쳐도 `memcpy` 결과가 맞더라」

그 글자는 **UB 의 관찰**이다([33번 형제](../33-restrict-and-the-aliasing-contract/) 「어디서 틀리나」 5번). 이 문서는 그 칸에 **결과를 싣지 않았다.**

### 3. ★★★ 「`memset` 으로 지우고 만들었으니 `memcmp` 가 맞다」

**값으로 돌려받는 순간** 패딩이 다시 채워질 수 있다 — gcc `-O1` 에서 20/20((6)).

### 4. ★★ 「`memcmp` 가 0 이면 같은 값」

NaN 과 그 복사본은 **`memcmp` 0 인데 `==` 가 거짓**이다((5)). 반대 방향은 `-0.0`.

### 5. ★★ 「`memset(a, 1, n)` 으로 1 을 채운다」

`16843009` 다((7)). **경고도 없다.**

### 6. ★ 「`memcpy` 가 `memmove` 보다 빠르니 바꾸자」

**재지 않았다.** 이 편이 잰 것은 **인라인되느냐**이고, 그것은 속도의 증거가 아니다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.

| 층 | 뜻 | 이 주제에서 | 근거 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | `memmove` 의 「임시 배열처럼」 · `memset` 의 `unsigned char` 변환 · `memcmp` 의 부호 · **정수의 모든 비트 0 = 0** | `ABABCDEFGHKLMNOP` · `16843009` · `i == 0 : 1` |
| ★★ **조건부 표준** | `__STDC_IEC_559__` 일 때 | `double` 의 모든 비트 0 = `+0.0` · `-0.0 == 0.0` · NaN 은 자기와 다르다 | `__STDC_IEC_559__ = 1` · (5)의 두 줄 |
| ★★ **구현(과 배포판)** | 구현이 정한다 | 널 포인터의 표현 · **`_FORTIFY_SOURCE=3` 기본값**(Ubuntu gcc) · 인라인 여부 · ASan 이 무엇을 가로채나 | `NULL 00 … 00` · `ver-fortify` · 재배치 격자 |
| **미명시** | 몇 가지 중 하나 | ★★★ **패딩 바이트의 값** · `memcmp` 반환의 크기 | 패딩 격자의 20/20 대 0/20 |
| ★★★ **UB** | 아무 일이나 | **겹친 `memcpy`** | 싣지 않음 · ASan 10 / 60 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 이 편의 사례 | 무엇이 봤나 | 무엇이 못 봤나 |
|---|---|---|---|
| UB | 겹친 `memcpy` | ASan — **호출이 남은 판만** · gcc `-Wrestrict` — **글자로 보일 때만** | ASan: 인라인 · `__memcpy_chk` · clang 경고 전부 |
| 미명시 | 패딩 `memcmp` | **아무 도구도** — 적법한 코드다 | 전부 |
| 구현 의존 | `memset` 널 · `memset(a, 1)` | **아무 도구도** | 전부 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓴다 | 안 쓴다 |
|---|---|---|
| 서로 다른 객체 사이 복사 | `memcpy` · 구조체 대입 | — |
| 한 버퍼 안에서 밀기·당기기 | ★★★ **`memmove`** | `memcpy` |
| 구조체 같음 판정 | ★★★ **멤버 비교 함수** | `memcmp` |
| 바이트 배열 · 해시 키(패딩 없음이 증명됨) | `memcmp` | — |
| 0 으로 밀기 | `memset(p, 0, n)` · `= {0}` | — |
| 0 이 아닌 값 채우기 | **루프** | `memset(a, 1, n)` |
| 포인터를 널로 | `p = NULL` | `memset` 에 기대기 |

## 핵심 문장

1. ★★★ **`memcpy` 는 겹치지 않는다는 약속이고, 겹치면 UB 다 — 겹칠 수 있으면 `memmove`.**
2. ★★★ **ASan 은 호출을 가로챌 때만 겹침을 본다 — 이 판에서 `memcpy` 겹침 스무 칸 중 열 칸이 침묵했다.**
3. ★★★ **`memcmp` 는 바이트를 비교한다 — `-0.0` 은 다르고, NaN 복사본은 같고, 패딩은 빌드마다 다르다.**
4. ★★ **`memset` 은 바이트 하나를 반복한다 — `int` 에 1 을 채우면 `16843009`.**
5. ★★ **「모든 비트 0」은 정수에게만 표준이 0 을 약속한다 — `double` 은 부록 F 일 때, 포인터는 아무도.**

## 관련 자료

- [33번 형제 — `restrict` 와 앨리어싱 계약](../33-restrict-and-the-aliasing-contract/) — ★★★ `memcpy` 서명의 `__restrict` · 루프가 `memcpy` 가 되는 것 · 겹친 `memcpy` 가 이 glibc 에서 낸 글자(관찰). 그쪽은 **약속의 뜻**까지, 여기는 **두 함수를 고르고 도구가 어디까지 보나**부터.
- [22번 형제 — 구조체 패딩·정렬](../22-struct-padding-and-alignment/) — ★★ 패딩 바이트 덤프 · 20 판 가짓수 · `memcmp` 반환값 크기. 그쪽은 **구멍 안의 바이트**까지, 여기는 **`memcmp` 가 무엇을 답하나**부터.
- [19번 형제 — `void *`·널 포인터·`NULL`](../19-void-pointer-null-pointer-and-null/) — (8)절 「`memset` 0 은 널이라는 보장이 없다」. 여기는 `double`·함수 포인터 칸을 더했다.
- [37번 형제 — `malloc`/`calloc`](../37-malloc-calloc-realloc-free/) · [30번 형제 — 초기화와 불확정 값](../30-initialization-rules-and-indeterminate-values/) — `calloc` 의 0 과 `malloc` 의 불확정.
- [04번 형제 — 부동소수점](../04-floating-point-types-and-conversions/) — `-0.0`·NaN 의 **값 규칙**.
- 목록의 **49번 주제** — `strcpy`·`strncpy` 같은 **문자열** 함수의 경계.
- 목록의 **58번 주제** — sanitizer 사용법 자체.

## 용어 풀이

> **겹침(overlap)** — 복사의 원본과 목적지 영역이 **한 바이트라도 같은 메모리**를 쓰는 것.

> **`memcpy-param-overlap`** — ASan 이 `memcpy` 의 두 영역이 겹칠 때 내는 리포트 이름. **호출을 가로챈 곳에서만** 나온다.

> **인라인(inline)** — 함수 호출을 **그 자리의 명령**으로 바꿔 넣는 것. 크기가 상수인 작은 `memcpy` 는 `mov` 몇 개가 된다.

> **`_FORTIFY_SOURCE`** — glibc 의 기능 매크로. 정의되면 `memcpy` 같은 호출을 **목적지 크기를 검사하는 판**(`__memcpy_chk`)으로 바꾼다. C 표준에 없다.

> **재배치(relocation)** — 오브젝트 파일에서 「여기에 이 심볼의 주소를 채워라」는 표시. `objdump -dr` 의 `R_X86_64_PLT32 memcpy` 가 **호출이 남아 있다**는 증거다.

> **패딩(padding)** — 정렬을 맞추려고 멤버 사이·끝에 끼운 바이트. 값이 **미명시**다.

> **`-0.0`** — 부호 비트만 1 인 0. `0.0` 과 `==` 로는 같다.

> **`__STDC_IEC_559__`** — 구현이 부록 F(IEC 60559 = IEEE 754)를 따른다는 표시 매크로.

## 더 들어가면

- ★★ **`memset_explicit`(C23)** — 컴파일러가 「곧 버릴 메모리에 쓰기」로 보고 **지우지 못하게** 하는 판. 비밀번호 지우기용이다. ★ 이 편은 **던지지 않았다**([30번 형제](../30-initialization-rules-and-indeterminate-values/)가 `-O2` 에서 `memset` 이 사라지는 것을 쟀다).
- ★ **`memccpy`(C23 표준 편입)** — 특정 바이트에서 멈추는 복사. 역시 `restrict` · 겹치면 UB. **던지지 않았다.**
- ★ **다른 배포판의 gcc** — `_FORTIFY_SOURCE` 기본값이 없는 판에서 1번 격자의 gcc `-O2` 열이 어떻게 되는지는 **돌려 보지 않았다**(여기서는 `-U_FORTIFY_SOURCE` 로 그 판을 흉내 냈다).
