# c/syntax/49 — `<string.h>` 문자열 함수와 함정: 「**`n` 이 붙은 함수도 「널까지 n」을 약속하지 않는다 — 함수마다 `n` 의 뜻이 다르고, 널 종단은 함수가 아니라 호출자가 확인한다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — `strncpy` 의 「**n 글자를 넘지 않게 복사한다(널 뒤의 글자는 복사하지 않는다) · 원본이 n 보다 짧은 문자열이면 모두 n 글자가 될 때까지 널을 덧붙인다**」(원본이 길 때 널을 붙인다는 문장은 **없다**), `strncat` 의 「**n 글자를 넘지 않게 붙이고 · 끝에는 늘 널을 붙인다**」·각주 「**그래서 결과 배열에 들어갈 수 있는 최대 글자 수는 `strlen(s1)+n+1`**」, `snprintf` 의 「**n 이 충분했다면 썼을 글자 수(널 제외) — 널 종단 출력이 완전히 쓰인 것은 반환값이 음수가 아니고 n 보다 작을 때, 그리고 그때만**」, `strcat` 의 「**널까지 포함해 붙인다**」를 **본문에서 직접 찾아 읽었다**) · 이 머신의 `libc.so.6` 심볼 목록
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **널 종단 · 바꾼 바이트 · 반환값 · ASan · fortify 는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 경계 조건 격자다** — 함수 7 × 원본 길이 3(짧음 · 같음 · 김) × 빌드 3(gcc ASan · gcc `-O2` · clang `-O2`), `d` 는 `char[8]`.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> ★★★ **경계** — **`strncpy` 의 세 경우를 바이트로**(`61 62 00 00 00` · `61 62 63 64 65` · 잘림)와 **널 없는 배열에 `strlen` → ASan `stack-buffer-overflow`**, **`sizeof` 대 `strlen`(배열 대 포인터)** 은 [20번 형제](../20-null-terminated-strings-and-string-literals/)가 **이미 쟀다.** 이 편은 그 바이트를 다시 찍지 않고 **여섯 함수를 한 격자**에 세운다.\
> ★ **문자열 탐색 알고리즘**(KMP 등)은 [`algorithm/25-string-matching/`](../../../../cs/algorithm/25-string-matching/)이 정본이다 — 여기는 **표준 함수의 계약과 경계 조건**만 본다. **`memcpy`/`memmove` 의 겹침 · `memset`** 은 [목록의 **50번 주제**](../50-string-h-memory-functions-memcpy-memmove-memset-memcmp/)다.
> 선행 — [20번 형제](../20-null-terminated-strings-and-string-literals/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 둘째 창 — 실행 결과의 경계 조건 격자다.** 널 종단은 **`memchr(d, 0, 8)`** 로 판정했다 — **문자열로 찍지 않는다**(널이 없으면 `%s` 가 곧 미정의다).
★★★ 그 격자에서 **널 종단 안 된 칸 5 / 21**(`strncpy` 둘 · `memcpy` 셋) · **넘친 칸 4 / 21**(`strcpy` 둘 · `strncat(…, sizeof d)` 둘). **넘친 넷 가운데 gcc `-O2` 는 4 / 4 를 멈췄고 clang `-O2` 는 0 / 4** 였다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★ `strncat(…, sizeof d)` 한 줄만 두 컴파일러가 잡았다 · `sizeof` 포인터 | 씀 |
| ★★★ ② **실행 출력(경계 격자)** | ★ **본체** — `memchr` 널 판정 · 바꾼 바이트 · 반환값 | 씀 |
| ③ sanitizer | ★★ **넘친 칸 4** · `WRITE of size 13` · `[32, 40) 'd'` | 씀 |
| ④ fortify(보통 빌드의 실행 검사) | ★★★ gcc `-O2` 의 `*** buffer overflow detected ***` · `exit 134` | 씀 |
| ⑤ 읽은 바이트 계수기 | ★★ `strcat` 되풀이의 **읽은 바이트** — 시간이 아니다 | 씀 |
| 시간 측정 | — | ★★★ **부적용 — 「`strcat` 반복은 느리다」는 재지 않았다.** 센 것은 읽은 바이트다 |
| ★ 제5의 상태 | 「넘쳤나」를 **보통 빌드에게 물으면 컴파일러마다 대답이 다르다**(gcc `exit 134` · clang `exit 0`). **ASan 으로 바꿔 물어** 넘침을 확정했고, clang 칸의 `exit 0` 은 **「안전」이 아니라 「안 물었다」** 임을 갈랐다 | 창을 바꿔 답함 |

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

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| 안 흔들린다 | ★★★ **경계 격자 · 계수기 출력 · 진단** | 같은 판이면 같다 |
| ★ 흔들린다 | **ASan 리포트의 PID · 주소** | 정규화 기본 규칙 — 대조할 것은 **종류 · `WRITE of size 13` · `[32, 40) 'd'`** 다 |
| ★ 싣지 않은 칸 | **clang `-O2` 넘친 칸의 결과 바이트** | 미정의 동작의 한 판이라 **「안 멈춤 (exit 0) — UB」** 로만 적었다 |

## 한눈에 — 쉽게 말하면

**문자열 함수의 `n` 은 「봉투 크기」처럼 보이지만 함수마다 다른 것을 센다.**

- **`strcpy`** — 봉투 크기를 **아예 안 받는다.** 편지가 길면 봉투 밖으로 쏟아진다. → **넘침**
- **`strncpy(d, s, n)`** — **딱 n 칸을 채운다.** 편지가 짧으면 나머지를 0 으로 메우고, 길면 **끝 표시 없이** 자른다. → **널 없음**
- **`strncat(d, s, n)`** — n 은 **덧붙일 글자 수**다. 봉투에 이미 든 것과 끝 표시 자리는 **내가 빼야** 한다. → **`sizeof d` 를 주면 넘침**
- **`snprintf` · `strlcpy`** — n 은 **봉투 전체**다. 늘 끝 표시를 넣고, **원래 쓰려던 길이**를 알려 준다. → **잘림을 안다**
- **`memcpy`** — 문자열을 모른다. 끝 표시는 **내가** 넣는다.

| 비유 | 실체 | 보이나 |
|---|---|---|
| 봉투 크기 안 받음 | `strcpy(d, s)` | ★★★ 같음·김에서 **ASan 넘침** · gcc `-O2` 멈춤 · clang `-O2` **조용** |
| 딱 n 칸 | `strncpy(d, s, sizeof d)` | ★★★ 같음·김에서 **널 없음** · 짧아도 **8 바이트** 씀 |
| 덧붙일 수 | `strncat(d, s, sizeof d)` | ★★ 같음·김에서 **넘침** — `sizeof d - 1` 이면 멀쩡 |
| 봉투 전체 + 원래 길이 | `snprintf` · `strlcpy` | ★★★ 세 길이 다 **널 있음** · 반환 **3 · 8 · 12** |
| 문자열 모름 | `memcpy` | ★★ 세 길이 다 **널 없음** |

```text
   d = char[8] , 원본 길이별로 널은 어디에 ?          (· = 0x7e 가 남은 칸, 0 = 널)

                        짧음 "abc"          같음 "abcdefgh"        김 "abcdefghijkl"
   strcpy              a b c 0 · · · ·     a b c d e f g h | 0 ★   a b c … h | i j k l 0 ★  (밖으로)
   strncpy(.., 8)      a b c 0 0 0 0 0     a b c d e f g h  (널 없음)  a b c d e f g h  (널 없음)
   strncat(.., 8)      a b c 0 · · · ·     a b c d e f g h | 0 ★   a b c … h | 0 ★
   strncat(.., 7)      a b c 0 · · · ·     a b c d e f g 0         a b c d e f g 0
   snprintf / strlcpy  a b c 0 · · · ·     a b c d e f g 0 (반환 8) a b c d e f g 0 (반환 12)
   memcpy(.., n)       a b c · · · · ·     a b c d e f g h         a b c d e f g h

   | 뒤 ★ = 배열 밖 쓰기 (ASan 이 잡았다)
```

- ★★★ **이 주제의 본체는 「표준」 칸** — 각 함수가 **짧을 때 · 길 때** 무엇을 하는지가 전부 표준 문장이다. 사고는 **문장을 「n 이면 안전」으로 뭉뚱그릴 때** 난다.
- ★★ **보통 빌드가 넘침을 멈추는가는 컴파일러·배포판 칸**이다 — Ubuntu gcc 는 `-O2` 에서 `_FORTIFY_SOURCE` 를 켠다((3)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **함수마다 `n` 은 무엇을 세고, 원본이 짧음 · 같음 · 김일 때 널 종단 · 넘침 · 반환값은 어떻게 되나.**
2. ★★ **잘림을 알 수 있는 함수는 어느 것이고, 넘침은 누가 잡나** — ASan · fortify · 컴파일 경고.
3. ★★ **`strlen`·`strcat` 은 왜 매번 처음부터 걷나** — 읽은 바이트로.

## 동작 방식

### (1) ★★★ 경계 조건 격자 — 함수 일곱 × 원본 길이 셋 × 빌드 셋

**언제 쓰나** — 고정 크기 버퍼에 문자열을 넣을 때 **어느 함수를 어떤 `n` 으로** 부를지 정할 때. ★★★ **이 편의 본체**다.

```c
/* s49a.c */
#define _DEFAULT_SOURCE                  /* 기능 매크로 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *const SRC[] = { "abc", "abcdefgh", "abcdefghijkl" };

int main(int argc, char **argv) {
    if (argc < 3) return 2;
    int fn = atoi(argv[1]);
    const char *s = SRC[atoi(argv[2])];
    char d[8];
    char before[8];
    long ret = 0;

    memset(d, 0x7e, sizeof d);
    if (fn == 3 || fn == 4) d[0] = '\0';          /* 이어 붙일 빈 문자열 */
    memcpy(before, d, sizeof d);

    switch (fn) {
    case 1: strcpy(d, s); break;
    case 2: strncpy(d, s, sizeof d); break;
    case 3: strncat(d, s, sizeof d); break;
    case 4: strncat(d, s, sizeof d - 1); break;
    case 5: ret = snprintf(d, sizeof d, "%s", s); break;
    case 6: ret = (long)strlcpy(d, s, sizeof d); break;
    case 7: { size_t n = strlen(s) < sizeof d ? strlen(s) : sizeof d;
              memcpy(d, s, n); break; }
    }

    int changed = 0;
    for (size_t i = 0; i < sizeof d; i++) changed += d[i] != before[i];
    printf("%s\t%d\t%ld\n", memchr(d, '\0', sizeof d) != NULL ? "있음" : "없음", changed, ret);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s49a.c -o /dev/null (cc exit=0) =====
s49a.c: In function ‘main’:
s49a.c:23:13: warning: ‘strncat’ specified bound 8 equals destination size [-Wstringop-overflow=]
   23 |     case 3: strncat(d, s, sizeof d); break;
      |             ^~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -c s49a.c -o /dev/null (cc exit=0) =====
s49a.c:23:27: warning: the value of the size argument in 'strncat' is too large, might lead to a buffer overflow [-Wstrncat-size]
   23 |     case 3: strncat(d, s, sizeof d); break;
      |                           ^~~~~~~~
s49a.c:23:27: note: change the argument to be the free space in the destination buffer minus the terminating null byte
   23 |     case 3: strncat(d, s, sizeof d); break;
      |                           ^~~~~~~~
      |                           sizeof(d) - strlen(d) - 1
1 warning generated.
```

```text
===== 경계 조건 격자 — 함수 7 × 원본 길이 3 × 빌드 3 (d 는 char[8]) (exit=0) =====
함수                          	원본 길이	gcc ASan -O0	gcc -O2 (보통 빌드)	clang -O2 (보통 빌드)
strcpy(d, s)                  	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strcpy(d, s)                  	같음 8   	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strcpy(d, s)                  	김 12    	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncpy(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
strncpy(d, s, sizeof d)       	같음 8   	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
strncpy(d, s, sizeof d)       	김 12    	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
strncat(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strncat(d, s, sizeof d)       	같음 8   	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncat(d, s, sizeof d)       	김 12    	넘침 stack-buffer-overflow (exit 1)	fortify 멈춤 (exit 134)	안 멈춤 (exit 0) — UB
strncat(d, s, sizeof d - 1)   	짧음 3   	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0	널 있음 · 쓴 4 · 반환 0
strncat(d, s, sizeof d - 1)   	같음 8   	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
strncat(d, s, sizeof d - 1)   	김 12    	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0	널 있음 · 쓴 8 · 반환 0
snprintf(d, sizeof d, "%s", s)	짧음 3   	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3
snprintf(d, sizeof d, "%s", s)	같음 8   	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8
snprintf(d, sizeof d, "%s", s)	김 12    	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12
strlcpy(d, s, sizeof d)       	짧음 3   	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3	널 있음 · 쓴 4 · 반환 3
strlcpy(d, s, sizeof d)       	같음 8   	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8	널 있음 · 쓴 8 · 반환 8
strlcpy(d, s, sizeof d)       	김 12    	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12	널 있음 · 쓴 8 · 반환 12
memcpy(d, s, n)               	짧음 3   	널 없음 · 쓴 3 · 반환 0	널 없음 · 쓴 3 · 반환 0	널 없음 · 쓴 3 · 반환 0
memcpy(d, s, n)               	같음 8   	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
memcpy(d, s, n)               	김 12    	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0	널 없음 · 쓴 8 · 반환 0
(각 줄 = ./x <함수> <길이> · d 는 char[8] 을 0x7e 로 채운 것(strncat 두 줄은 d[0] 만 0) · 널 = memchr(d, 0, 8) · 쓴 = 호출 전과 달라진 바이트 수 · 반환 = snprintf/strlcpy 의 값(나머지는 0) · memcpy 의 n = min(strlen(s), sizeof d))
널 종단 안 된 칸 5 / 21
넘친 칸(ASan) 4 / 21
넘친 칸 가운데 gcc -O2 가 멈춘 칸 4 / 4 · clang -O2 가 멈춘 칸 0 / 4
```

그림 해설 (한 단계씩):

- ★★★ **`strcpy` — 짧으면 멀쩡(4 바이트 = 글자 3 + 널), 같음·김은 넘침.** 「같음 8」 도 넘친다 — 글자 8 개에 **널 하나가 더** 들어갈 자리가 없다.
- ★★★ **`strncpy(d, s, sizeof d)` — 같음·김에서 널이 없다.** 넘치지는 않는다(딱 8 칸). **짧아도 8 바이트를 썼다** — 남은 다섯 칸을 0 으로 채웠다. [20번 형제](../20-null-terminated-strings-and-string-literals/) (7)의 바이트와 같은 모양이다.
- ★★★ **`strncat(d, s, sizeof d)` — 같음·김에서 넘침.** `n` 은 **붙일 글자 수**이고 **널은 따로 붙인다** — 빈 `d` 에 8 글자 + 널 = 9 바이트. 각주의 `strlen(s1)+n+1` 이 그 셈이다.
- ★★ **`strncat(d, s, sizeof d - 1)` — 세 길이 다 널이 있다.** 단 **`d` 가 비어 있을 때만** 맞다 — 일반형은 `sizeof d - strlen(d) - 1`(clang 의 제안 줄이 그것이다).
- ★★★ **`snprintf` · `strlcpy` — 세 길이 다 널이 있고 반환이 원본 길이(3 · 8 · 12).** 「같음」에서 반환 8 은 **8 글자를 쓰고 싶었는데 7 글자만 들어갔다**는 뜻이다. **반환 `>= sizeof d` 면 잘렸다.**
- ★★ **`memcpy(d, s, min(strlen, 8))` — 세 길이 다 널이 없다.** 널을 복사하지 않았으니 당연하다 — **결함이 아니라 계약**이다.
- ★★★ **널 종단 안 된 칸 5 / 21 · 넘친 칸 4 / 21** — 「안전한 줄 알았던 `n` 함수」 둘(`strncpy` · `strncat`)이 **각각 다른 방식**으로 사고를 냈다.

### (2) ★★ 넘친 칸의 ASan 리포트

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s49a.c -o x 2>/dev/null && ASAN_OPTIONS=strip_path_prefix="$PWD/" ./x 1 2 | sed -n '1,/^SUMMARY/p' (exit=1) =====
=================================================================
==1212269==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x780f4c800028 at pc 0x780f4eca7923 bp 0x7ffe5bd199d0 sp 0x7ffe5bd19178
WRITE of size 13 at 0x780f4c800028 thread T0
    #0 0x780f4eca7922 in strcpy ../../../../src/libsanitizer/asan/asan_interceptors.cpp:563
    #1 0x604a9b5bf63f in main s49a.c:21
    #2 0x780f4e82a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x780f4e82a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x604a9b5bf304 in _start (x+0x1304) (BuildId: 288822a83d8901ad63526cf6eb4aa8fea8a04a2d)

Address 0x780f4c800028 is located in stack of thread T0 at offset 40 in frame
    #0 0x604a9b5bf3d8 in main s49a.c:8

  This frame has 2 object(s):
    [32, 40) 'd' (line 12) <== Memory access at offset 40 overflows this variable
    [64, 72) 'before' (line 13)
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow ../../../../src/libsanitizer/asan/asan_interceptors.cpp:563 in strcpy
```

- ★★ **`WRITE of size 13`** — `"abcdefghijkl"` 12 글자 + 널. `d` 는 **`[32, 40)`**(8 바이트), 바로 뒤의 `before` 는 `[64, 72)` — 사이의 빨간 구역에 걸렸다.
- ★ 리포트의 첫 프레임은 **ASan 의 `strcpy` 가로채기**, 내 소스 줄은 **그 다음 프레임**(`s49a.c:21`)이다 — [20번 형제](../20-null-terminated-strings-and-string-literals/) (6)과 같은 읽기 순서.

### (3) ★★★ 보통 빌드 — gcc `-O2` 는 멈추고 clang `-O2` 는 조용하다

**언제 쓰나** — 「릴리스 빌드에서는 넘침이 죽는다더라 / 안 죽더라」.

```text
===== gcc -O2 -dM -E - < /dev/null | grep FORTIFY; clang -O2 -dM -E - < /dev/null | grep FORTIFY; echo "clang grep exit=$?" (exit=0) =====
#define _FORTIFY_SOURCE 3
clang grep exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s49a.c -o x ; ./x 1 1 2>&1 >/dev/null (cc exit=0 · run exit=134) =====
*** buffer overflow detected ***: terminated
```

- ★★★ **Ubuntu gcc 는 `-O2` 에서 `_FORTIFY_SOURCE=3` 을 미리 정의한다** — glibc 헤더가 그것을 보고 `strcpy` 를 **크기를 아는 `__strcpy_chk`** 로 바꾼다. 넘치면 **`*** buffer overflow detected ***: terminated` · `exit 134`(`abort`)**.
- ★★★ **clang `-O2` 는 그 매크로를 정의하지 않았다**(`grep` 이 아무것도 못 찾음 · `exit=1`) — 같은 넘침이 **`exit 0` 으로 끝났다.** 그 칸의 결과 바이트는 **미정의 동작의 한 판**이라 싣지 않았다.
- ★★ **이것은 표준의 차이가 아니라 배포판이 드라이버에 심은 기본값**이다 — 47편의 `-Wformat` specs 와 같은 집안이다. **「넘치면 죽는다」에 기대는 코드는 빌드가 바뀌면 조용해진다.**
- ★ **fortify 는 크기를 컴파일러가 알 때만** 검사한다 — 여기서는 `d` 가 지역 배열이라 알았다. 포인터로 받은 버퍼는 **모를 수 있다**(던지지 않았다).

### (4) ★★ `strlcpy` — 이 판에는 있다, 단 표준이 아니다

```text
===== gcc -std=c17 -c s49l.c -o /dev/null (cc exit=0) =====
s49l.c: In function ‘main’:
s49l.c:6:16: warning: implicit declaration of function ‘strlcpy’; did you mean ‘strncpy’? [-Wimplicit-function-declaration]
    6 |     size_t r = strlcpy(d, "abcdef", sizeof d);
      |                ^~~~~~~
      |                strncpy
```

```c
/* s49l.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char d[4];
    size_t r = strlcpy(d, "abcdef", sizeof d);
    printf("반환 %zu · d = %s · 잘렸나 = %d\n", r, d, r >= sizeof d);
    return 0;
}
```

```text
===== gcc -std=c17 -D_DEFAULT_SOURCE -Wall s49l.c -o x ; ./x (cc exit=0 · run exit=0) =====
반환 6 · d = abc · 잘렸나 = 1
```

```text
===== nm -D /lib/x86_64-linux-gnu/libc.so.6 | grep -E ' strlcpy| strlcat' (exit=0) =====
00000000000b4cd0 W strlcat@@GLIBC_2.38
00000000000b4d50 W strlcpy@@GLIBC_2.38
```

- ★★ **`-std=c17` 만으로는 선언이 안 보인다** — 암시적 선언 경고(gcc 13 은 경고 · `exit=0` — [48번 형제](../48-stdio-input-and-files/)의 `gets` 와 같은 모양). **`_DEFAULT_SOURCE`**(또는 `_GNU_SOURCE`)를 줘야 헤더가 연다.
- ★★★ **`libc.so.6` 의 `strlcpy`·`strlcat` 은 `GLIBC_2.38`** — **glibc 2.38 부터**다. 그보다 옛 glibc 에서는 링크가 안 된다. **ISO C 에는 없다**(BSD 에서 온 함수).
- ★★ **반환은 원본 길이** — `반환 6 · d = abc · 잘렸나 = 1`. `snprintf` 와 같은 판정(`>= 크기`)이 된다.

### (5) ★★ `strcat` 을 되풀이하면 — 읽은 바이트

**언제 쓰나** — 반복문 안에서 `strcat(buf, piece)` 를 부를 때.

```c
/* s49c.c */
#include <stdio.h>
#include <string.h>

static unsigned long long reads;                 /* 읽은 바이트를 센다 */

static size_t counting_strlen(const char *s) {
    size_t n = 0;
    while (reads++, s[n] != '\0') n++;
    return n;
}

static char *counting_strcat(char *d, const char *s) {  /* strcat 과 같은 일 */
    char *end = d + counting_strlen(d);
    size_t k = 0;
    do { reads++; end[k] = s[k]; } while (s[k++] != '\0');
    return d;
}

static char buf[2 * 4000 + 1];

int main(void) {
    const int ns[] = { 10, 100, 1000, 4000 };
    for (int t = 0; t < 4; t++) {
        int n = ns[t];

        reads = 0; buf[0] = '\0';
        for (int i = 0; i < n; i++) counting_strcat(buf, "ab");
        unsigned long long a = reads;

        reads = 0; buf[0] = '\0';
        char *end = buf;                          /* 끝을 기억해 두는 꼴 */
        for (int i = 0; i < n; i++) end = counting_strcat(end, "ab") + 2;
        unsigned long long b = reads;

        printf("n = %4d · 길이 %5zu · strcat 반복 %9llu 바이트 읽음 · 끝을 기억 %6llu 바이트 읽음\n",
               n, strlen(buf), a, b);
    }
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s49c.c -o x ; ./x (cc exit=0 · run exit=0) =====
n =   10 · 길이    20 · strcat 반복       130 바이트 읽음 · 끝을 기억     40 바이트 읽음
n =  100 · 길이   200 · strcat 반복     10300 바이트 읽음 · 끝을 기억    400 바이트 읽음
n = 1000 · 길이  2000 · strcat 반복   1003000 바이트 읽음 · 끝을 기억   4000 바이트 읽음
n = 4000 · 길이  8000 · strcat 반복  16012000 바이트 읽음 · 끝을 기억  16000 바이트 읽음
```

- ★★★ **`strcat` 은 매번 `d` 의 끝을 찾으러 처음부터 걷는다** — 되풀이하면 읽은 바이트가 **130 → 10300 → 1003000**. `n` 이 10 배가 되면 **약 100 배**다(길이의 제곱).
- ★★ **끝을 기억해 두면 40 → 400 → 4000** — `n` 과 **같이** 10 배다.
- ★★★ **이 문서는 시간을 재지 않았다** — 센 것은 **계수기가 센 바이트**다. 「느리다」는 이 수에서 **추론**할 수 있을 뿐 측정이 아니다. ★ 계수기는 **표준 `strcat` 과 같은 일을 하는 내 함수**다 — glibc 의 실제 `strcat` 이 몇 바이트씩 읽는지는 안 쟀다.
- ★ **`strlen` 도 같다** — 길이를 저장하지 않는 문자열에서 길이는 **매번 걸어서** 얻는다.

### (6) ★★ `sizeof` 로 크기를 넘기면 — 포인터가 된 배열

```c
/* s49z.c */
#include <stdio.h>
#include <string.h>

static void fill(char *d, const char *s) {
    strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
    d[sizeof d - 1] = '\0';
}

int main(void) {
    char name[32];
    fill(name, "abcdefghijklmnop");
    printf("sizeof name = %zu · strlen(name) = %zu\n", sizeof name, strlen(name));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s49z.c -o /dev/null (cc exit=0) =====
s49z.c: In function ‘fill’:
s49z.c:5:26: warning: argument to ‘sizeof’ in ‘strncpy’ call is the same expression as the destination; did you mean to provide an explicit length? [-Wsizeof-pointer-memaccess]
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |                          ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s49z.c -o /dev/null (cc exit=0) =====
s49z.c:5:26: warning: 'strncpy' call operates on objects of type 'char' while the size is based on a different type 'char *' [-Wsizeof-pointer-memaccess]
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |             ~            ^
s49z.c:5:26: note: did you mean to provide an explicit length?
    5 |     strncpy(d, s, sizeof d);            /* 배열 크기를 쓰려던 자리 */
      |                          ^
1 warning generated.
```

```text
===== gcc -std=c17 s49z.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof name = 32 · strlen(name) = 7
```

- ★★★ **`fill` 안의 `d` 는 포인터다** — `sizeof d` 는 **8**(포인터 크기)이지 32 가 아니다. 그래서 `d[7] = '\0'` 이 되고 **`strlen(name) = 7`** — 원본 16 글자가 **조용히 7 글자**가 됐다.
- ★★ **두 컴파일러 다 `-Wsizeof-pointer-memaccess` 로 잡았다** — 이 실수는 **경고가 있는 드문 자리**다. 배열이 매개변수에서 포인터가 되는 규칙은 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.
- ★ 처방 — **크기를 매개변수로** 받는다(`fill(char *d, size_t n, …)`).

## 문법 — 형태와 규칙

### 형태 — 함수마다 `n` 의 뜻

| 함수 | `n` 이 세는 것 | 널 종단 | 잘림을 아나 |
|---|---|---|---|
| `strcpy(d, s)` | — (크기를 안 받는다) | ★ 넘치지 않으면 | ★ 모른다 · **넘친다** |
| `strncpy(d, s, n)` | ★★★ **쓸 바이트 수 — 딱 n**(짧으면 0 으로 채움) | ★★★ **원본이 n 이상이면 없다** | 모른다 |
| `strncat(d, s, n)` | ★★★ **붙일 글자 최대 n**(널은 따로) | ★ 늘 붙인다 | 모른다 · **`n` 을 잘못 주면 넘친다** |
| `snprintf(d, n, …)` | ★★ **버퍼 전체** | ★★ n > 0 이면 늘 | ★★★ **반환 `>= n`** |
| `strlcpy(d, s, n)`(glibc 2.38 · 비표준) | ★★ **버퍼 전체** | ★★ n > 0 이면 늘 | ★★★ **반환 `>= n`** |
| `memcpy(d, s, n)` | ★ 바이트 수 | ★ 모른다(문자열 함수가 아니다) | — |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 결과 | 층 | 어느 절 |
|---|---|---|---|
| `strcpy(d, s)` · `strlen(s) >= sizeof d` | 경고 0 · ASan 넘침 · gcc `-O2` `exit 134` · clang `-O2` **조용** | ★★★ UB | (1) · (3) |
| `strncpy(d, s, sizeof d)` 뒤 `d` 를 문자열로 | 경고 0 · **널 없음** | ★★★ 표준 계약 → 뒤의 사용이 UB | (1) |
| `strncat(d, s, sizeof d)` | ★ 두 컴파일러 경고 · 넘침 | ★★★ UB | (1) · (2) |
| 매개변수 배열에 `sizeof` | ★★ 두 컴파일러 경고 · **조용한 잘림** | ★★ 표준(배열이 포인터로) | (6) |
| `-std=c17` 에서 `strlcpy` | 경고(암시적 선언) · `exit=0` | ★★ glibc 기능 매크로 · 비표준 | (4) |
| 반복문 안의 `strcat` | 경고 0 · 읽은 바이트가 길이의 제곱 | ★ 표준(길이를 저장하지 않는 문자열) | (5) |

### 규칙 불릿

- ★★★ **`strncpy` 는 「안전한 `strcpy`」가 아니다 — 원본이 n 이상이면 널이 없다.**
- ★★★ **`strncat` 의 n 은 버퍼 크기가 아니다 — `sizeof d - strlen(d) - 1`.**
- ★★★ **잘림을 알아야 하면 `snprintf`(또는 glibc 2.38 의 `strlcpy`)의 반환을 크기와 견준다.**
- ★★ **널 종단은 호출자가 `memchr` 등으로 확인한다 — 찍어 보지 않는다.**
- ★★ **넘침은 표준이 잡아 주지 않는다 — ASan 과 fortify 는 도구의 몫이고 빌드마다 다르다.**

## 어디서 틀리나

### 1. ★★★ 「`strncpy` 에 `sizeof d` 를 줬으니 안전하다」

넘치지는 않지만 **같음·김에서 널이 없다**((1)). 그 뒤의 `strlen`·`%s` 가 [20번 형제](../20-null-terminated-strings-and-string-literals/)의 사고가 된다.

### 2. ★★★ 「`strncat` 에도 `sizeof d` 를 주면 된다」

**넘쳤다**((1)) — `n` 은 붙일 글자 수이고 널이 한 칸 더 필요하다.

### 3. ★★ 「릴리스 빌드에서는 넘치면 죽는다」

gcc `-O2`(Ubuntu)는 죽었고 **clang `-O2` 는 `exit 0`** 이었다((3)).

### 4. ★★ 「`snprintf` 는 넘치지 않으니 끝」

넘치지는 않지만 **잘렸는지는 반환을 봐야** 안다(반환 12 · 버퍼 8).

### 5. ★ 「`strlcpy` 는 어디에나 있다」

**glibc 2.38 부터 · 비표준 · 기능 매크로가 있어야** 선언이 보인다((4)).

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 각 함수의 짧을 때 · 길 때 동작이 전부 표준 문장이다.\
★★ **넘침을 멈추느냐는 「컴파일러·배포판」 칸**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **`strncpy` 는 짧으면 널로 채우고 길면 널을 안 붙인다** · **`strncat` 은 n 글자 + 늘 널** · **`snprintf` 는 썼을 길이를 돌려준다** · `strcpy`·`strcat` 은 크기를 모른다 | 격자 |
| ★★ **glibc · POSIX** | 표준 밖의 선택 | ★★ **`strlcpy`·`strlcat`(`GLIBC_2.38`)** · `_DEFAULT_SOURCE` 로 선언 · `_FORTIFY_SOURCE` 의 `__*_chk` | (4) · (3) |
| ★★ **컴파일러 구현(배포판)** | 도구의 선택 | ★★★ **Ubuntu gcc `-O2` 의 `_FORTIFY_SOURCE=3` · clang 은 안 정의** · 두 컴파일러의 `strncat` 경고 · `-Wsizeof-pointer-memaccess` | (3) · (1) · (6) |
| **미명시** | 몇 가지 중 하나 | ★ **해당 없음(이 편이 던진 것 중에는)** | — |
| ★★★ **UB** | 아무 일이나 | ★★★ **배열 밖 쓰기**(`strcpy` · `strncat` 넘친 칸) · **널 없는 배열을 문자열로 쓰기** | ASan · 격자 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **`strncpy` 의 널 없음 · `strcpy` 넘침에 컴파일 경고 0**(격자 소스 — `strncat(…, sizeof d)` 한 줄만 잡혔다) |
| ★★ **컴파일러 구현** | ★★★ **clang `-O2` 보통 빌드는 넘친 네 칸을 전부 `exit 0` 으로** 끝냈다 |
| ★★★ **UB** | ★★ ASan 은 **실행한 경로만** 본다 — 짧은 입력으로 시험하면 `strcpy` 도 통과한다(격자 첫 줄) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **함수의 `n` 을 읽을 때 「무엇의 개수인가」를 먼저 묻는다** — 셋이 서로 다르다.
  - ★★ **널 종단은 결과를 `memchr` 로 확인하는 창이 가장 싸다.**
  - ★★ **넘침을 막는 것은 호출 형태이지 빌드 옵션이 아니다** — 빌드 옵션은 판마다 바뀐다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 고정 버퍼에 문자열 복사 · 잘림 알기 | ★★★ **`snprintf(d, sizeof d, "%s", s)` · 반환 `>= sizeof d` 검사** | `strcpy` · `strncpy` |
| glibc 2.38+ 만 대상 | ★★ `strlcpy`(+ `_DEFAULT_SOURCE`) | 이식성이 필요한 코드에서 `strlcpy` |
| 고정 폭 레코드(널 없어도 되는 필드) | ★ `strncpy` — 그 본래 용도 | 문자열로 쓸 버퍼에 `strncpy` |
| 이어 붙이기 | ★★ **끝 포인터를 들고 다니기** · 또는 `snprintf` 로 한 번에 | 반복문의 `strcat` · `strncat(…, sizeof d)` |
| 함수에 버퍼 넘기기 | ★★ **크기를 같이** 넘기기 | 매개변수에 `sizeof` |

판단 규칙 두 줄.

- ★★★ **「이 호출 뒤에 `d` 에 널이 있나 · 잘렸는지 아나」를 두 질문으로 따로 묻는다.**
- ★★ **문자열 함수의 결과는 찍어서 확인하지 않는다 — 바이트로 확인한다.**

## 핵심 문장

- ★★★ **경계 격자에서 널 종단 안 된 칸 5 / 21(`strncpy` 둘 · `memcpy` 셋), 넘친 칸 4 / 21(`strcpy` 둘 · `strncat(…, sizeof d)` 둘).**
- ★★★ **`strncpy(d, s, sizeof d)` 는 원본이 같거나 길면 널이 없었고, 짧으면 8 바이트를 다 썼다.**
- ★★★ **넘친 넷을 gcc `-O2` 는 fortify 로 전부 멈췄고(`exit 134`) clang `-O2` 는 하나도 안 멈췄다 — Ubuntu gcc 만 `_FORTIFY_SOURCE=3` 을 정의한다.**
- ★★ **`snprintf` · `strlcpy` 는 세 길이 다 널이 있고 원본 길이(3 · 8 · 12)를 돌려줬다 — 반환 `>= 크기` 가 잘림이다.**
- ★★ **`strlcpy` 는 `GLIBC_2.38` 이고 `-std=c17` 만으로는 선언이 안 보였다.**
- ★★ **`strcat` 되풀이는 읽은 바이트가 130 → 10300 → 1003000, 끝을 기억하면 40 → 400 → 4000 — 시간은 재지 않았다.**

## 관련 자료

- [20번 형제 — 널 종단 문자열과 문자열 리터럴](../20-null-terminated-strings-and-string-literals/) — ★★★ **선행.** `strncpy` 세 경우의 바이트 · 널 없는 배열에 `strlen` · `sizeof` 대 `strlen`.
- [16번 형제 — 배열 감쇠와 함수 매개변수](../16-array-pointer-decay-and-function-parameters/) — ★★ 매개변수의 `sizeof` 가 8 인 이유.
- [48번 형제 — `<stdio.h>` 입력과 파일](../48-stdio-input-and-files/) — ★ 읽은 줄(`fgets`)의 널과 개행.
- [목록의 **50번 주제**](../50-string-h-memory-functions-memcpy-memmove-memset-memcmp/)(`<string.h>` 메모리 함수) — ★★ `memcpy`/`memmove` 의 겹침 · `memset`.
- [`algorithm/25-string-matching/`](../../../../cs/algorithm/25-string-matching/) — ★ 문자열 탐색 알고리즘은 거기, 여기는 **표준 함수의 계약**.
- [Rust 15 — 슬라이스 · 범위 · UTF-8 경계](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/) — ★★ **길이를 가진** 문자열·슬라이스.

## 용어 풀이

> **널 종단(null termination)** — 문자열의 끝을 **값 0 인 바이트**로 표시하는 C 의 관례. 길이는 저장하지 않는다.\
> 예: `"abc"` 는 `61 62 63 00`.

> **`_FORTIFY_SOURCE`** — glibc 가 크기를 아는 호출을 **검사하는 판(`__strcpy_chk` 등)** 으로 바꾸게 하는 매크로. 넘치면 `abort`.\
> 예: Ubuntu gcc `-O2` 는 `_FORTIFY_SOURCE=3` 을 미리 정의한다.

> **`strlcpy`** — 버퍼 전체 크기를 받아 늘 널을 붙이고 **원본 길이**를 돌려주는 BSD 함수. glibc 2.38 부터 있다 · ISO C 가 아니다.\
> 예: `strlcpy(d, "abcdef", 4)` → `6` · `d = "abc"`.

> **`memchr(d, 0, n)`** — 첫 n 바이트 안에서 0 을 찾는다. **문자열을 읽지 않고** 널 종단을 판정하는 창.\
> 예: 격자의 「널 있음 / 없음」.

## 더 들어가면

- ★★ **`strndup` · `strdup`(C23 편입)** — 소유권은 [38번 형제](../38-expressing-ownership-conventions-in-code/). ★ 경계 격자에 **넣지 않았다.**
- ★ **`memccpy`(C23)** — 널을 만나면 멈추는 복사로 `strcat` 되풀이를 풀 수 있다. ★ **던지지 않았다.**
- ★ **포인터로 받은 버퍼에서 fortify 가 크기를 아는가** — `__builtin_object_size`. ★ **던지지 않았다.**
