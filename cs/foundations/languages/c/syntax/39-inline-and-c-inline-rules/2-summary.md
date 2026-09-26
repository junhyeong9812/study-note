# c/syntax/39 — `inline` 과 C 의 인라인 규칙: 「**C 의 `inline` 은 「펼쳐라」가 아니라 「이 정의는 외부 정의가 아니다」다 — 그래서 헤더에 두면 링크가 판을 탄다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) 함수 지정자 절 — 「**`inline` 은 호출을 가능한 한 빠르게 하라는 제안이고, 그 제안이 얼마나 먹히는지는 구현 정의**」·「**외부 링크 함수의 파일 스코프 선언이 전부 `extern` 없는 `inline` 이면 그 정의는 인라인 정의이고, 외부 정의를 만들지 않는다**」·「**호출이 인라인 정의를 쓸지 외부 정의를 쓸지는 미명시**」·「**외부 링크 인라인 정의는 수정 가능한 정적·스레드 저장 기간 객체를 정의하거나 내부 링크 식별자를 참조하면 안 된다(제약)**」·각주 「**함수는 인라인 정의가 몇 개이든 주소가 하나다**」, 예제 1 의 `extern double fahr(double); // creates an external definition` 를 **본문에서 직접 찾아 읽었다**)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **링크 결과 · `nm` 글자 · 어셈블리 · 진단은 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다.\
> ★★★ **본체는 링크 격자다** — 헤더의 지정자 4 × 판 3(C99 의미 · `-fgnu89-inline` · `-std=gnu89`) × 컴파일러 2 × `-O0`/`-O2`, **두 번역 단위가 같은 헤더를 include** 한다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `inline` 은 **C99 부터**다. 그 전의 **GNU C(gnu89) 확장 `inline`** 은 **뜻이 반대**다((2)).
> ★★★ **경계** — **한 번역 단위 안의 C99 `inline` 세 형태**(`inline` 만 · `+ extern` 선언 · `static inline`)는 [29번 형제](../29-scope-and-linkage-static-extern/)의 (8)이 **이미 쟀다**(그쪽의 12칸 격자와 `nm` 의 `U`/`T`/`t`). 이 편은 그 결과를 **다시 재지 않고**, **두 번역 단위 · 헤더 · 판 뒤집힘 · C++ 대비 · 주소 · 제약**으로 넓힌다.\
> ★ **정의가 몇 개 남나의 앞**(선언과 정의의 구분)은 [34번 형제](../34-function-declarations-definitions-and-prototypes/), **`static`/`extern` 의 링크 규칙 자체**는 [29번 형제](../29-scope-and-linkage-static-extern/)가 정본이다. **헤더에 무엇을 두나**는 목록의 **44번 주제**, **링크 오류를 거꾸로 읽기**는 목록의 **45번 주제**다.
> 선행 — [29번 형제](../29-scope-and-linkage-static-extern/) · 목록의 **44번 주제**.
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — 링크 결과다.** 컴파일은 전부 통과한다(경고 0). **링크에서만** 「정의가 없다」·「정의가 둘이다」가 갈린다.
★★★ 그 격자에서 **C99 판과 gnu89 판이 갈린 칸 12 / 16**, **gcc 와 clang 이 갈린 칸 0 / 24** — 갈리는 축은 **컴파일러가 아니라 판**이다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | ★ 제약 위반(`static` 을 쓰는 `inline`) · 그 밖은 **경고 0** | 씀 |
| ② 실행 출력 | ★ 링크가 된 판의 값 · **두 번역 단위의 `&twice` 가 같나** | 씀 |
| ③ sanitizer | — | 부적용(메모리 사고가 없는 주제다) |
| ★★★ ④ **링크 결과 + `nm`** | ★ **본체** — `링크 성공` / `undefined reference` / `multiple definition` · 심볼 글자 `T`/`t`/`U`/`W`/(없음) | 씀 |
| ⑤ 어셈블리 | ★★ **`call twice` 가 남는 칸** — 「`inline` 은 명령이 아니다」 | 씀 |
| 시간 측정 | — | ★★★ **부적용 — 「`inline` 이 빠르다」는 재지 않았다.** 이 편은 **정의가 몇 개 남나**의 주제다 |
| ★ 제5의 상태 | 「외부 정의가 있나」를 **링크 에러로** 물으면 `-O2` 에서는 **대답이 사라진다**(호출이 펼쳐져 심볼이 필요 없어진다). **`nm` 으로 바꿔 물어** 번역 단위마다 글자로 받았다 — 29편 (8)의 방식을 두 번역 단위로 넓혔다 | 창을 바꿔 답함 |

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
===== g++ --version | sed -n 1p (cc exit=0) =====
g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★ **어셈블리의 명령 배치 · 레지스터** | 판마다 달라질 수 있다 — 이 편은 **`call twice` 가 몇 번인가**만 센다(그 수는 안 흔들렸다) |
| 안 흔들린다 | ★★★ **링크 격자 · `nm` 격자 · C++ 격자 · 주소 격자** | 같은 판 · 같은 플래그면 같다 |
| 안 흔들린다 | 링크 에러 문구 | ★ **오브젝트 이름을 고정**했다 — `gcc a.c b.c` 로 한 번에 링크하면 임시 파일(`/tmp/cc….o`)의 이름이 문구에 박혀 **실행마다 흔들린다.** 문구를 싣는 블록은 `-c` 로 `s39a.o`·`s39b.o` 를 먼저 만들었다 |

## 한눈에 — 쉽게 말하면

**C 의 `inline` 함수는 「각 지점에 둔 견본」이고, 「본점」은 따로 한 곳에만 있어야 한다.**

- **견본(인라인 정의)은 그 지점 안에서만 쓴다** — 컴파일러가 견본으로 **그 자리에서 처리**할 수도 있다. → **인라인 정의**
- **견본으로 처리하지 않은 주문은 본점(외부 정의)으로 간다** — 본점이 **아무 데도 없으면** 링커가 「그런 가게 없다」고 한다. → **`undefined reference`**
- **지점 하나를 본점으로 지정하는 한 줄**이 `extern inline int twice(int);` 다. → **외부 정의를 만든다**
- **모든 지점이 스스로 본점이라고 하면** 본점이 둘이 된다. → **헤더의 `extern inline` · `multiple definition`**
- **`static inline` 은 지점마다 자기 가게를 차린다** — 본점이 필요 없고, 가게가 **지점 수만큼** 생긴다. → **내부 링크 사본 · 주소가 다르다**
- ★ **옛 GNU 규칙은 견본과 본점의 표시가 반대**였다. → **gnu89 뒤집힘**

| 비유 | 실체 | 보이나 |
|---|---|---|
| 견본만 | 헤더의 `inline int twice(…) {…}` | ★★★ `-O0` 에서 `undefined reference` · `nm` 의 `U` |
| 본점 지정 한 줄 | 한 `.c` 의 `extern inline int twice(int);` | ★★ `T` 가 한 곳 · 링크 성공 |
| 모두가 본점 | 헤더의 `extern inline int twice(…) {…}` | ★★★ `multiple definition` |
| 지점마다 자기 가게 | `static inline` | ★★ `t` 둘 · **`&twice` 가 다르다** |
| 반대 표시 | `-fgnu89-inline` | ★★★ **갈린 칸 12 / 16** |

```text
   헤더 s39.h:  KW int twice(int x) { return 2 * x; }      s39a.c, s39b.c 가 둘 다 include

                        s39a.o          s39b.o          링크 (-O0)
   KW=inline            U twice         U twice         undefined reference   (본점이 없다)
   KW=static inline     t twice         t twice         성공                  (지점마다 사본)
   KW=extern inline     T twice         T twice         multiple definition   (본점이 둘)
   inline + DECL(a 만)  T twice         U twice         성공                  (본점은 a 하나)
```

- ★★★ **이 주제의 본체는 「표준」 칸** — 인라인 정의가 외부 정의가 아니라는 것 · `extern` 선언 한 줄이 외부 정의를 만든다는 것 · 제약 둘 · 주소가 하나라는 것이 **전부 표준 문장**이다.
- ★★ **「구현 정의」 칸에 「실제로 펼치느냐」** 가 든다 — 표준이 직접 「효과의 정도는 구현 정의」라고 적는다. `-O0` 의 `call twice` 가 그것이다.
- ★ **「미명시」 칸** — 인라인 정의와 외부 정의가 둘 다 보일 때 **어느 쪽을 쓰나**.

> **인라인 정의(inline definition)** — 외부 링크 함수의 정의인데, 그 번역 단위의 파일 스코프 선언이 **전부 `extern` 없는 `inline`** 인 것. **외부 정의가 아니다.**\
> 예: 헤더의 `inline int twice(int x) { return 2 * x; }`.

> **외부 정의(external definition)** — 링커가 다른 번역 단위의 호출을 이어 줄 **단 하나의** 정의.\
> 예: 한 `.c` 에 `extern inline int twice(int);` 를 더하면 그 번역 단위의 정의가 외부 정의가 된다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`inline` · `static inline` · `extern inline` 은 각각 몇 개의 정의를, 어떤 링크로 남기나** — 헤더를 두 번역 단위가 include 할 때.
2. ★★ **그 규칙은 판(C99 대 gnu89)과 언어(C 대 C++)에 따라 어떻게 뒤집히나.**
3. ★★ **`inline` 은 무엇을 보장하지 않나** — 펼침 · 성능 · 그리고 표준이 걸어 둔 제약.

## 동작 방식

### (0) ★ 한 번역 단위 — 29편이 이미 잰 것

- ★★ [29번 형제 (8)](../29-scope-and-linkage-static-extern/)의 격자: **`inline` 만 있는 파일은 gcc·clang 둘 다 `-O0` 에서 `link exit=1`, `-O2` 에서 통과** · **`extern inline` 선언을 더한 파일과 `static inline` 파일은 네 칸 다 통과** · `nm` 이 `U twice` / `T twice` / `t twice`.
- ★ **이 편은 그 12칸을 다시 재지 않았다** — 같은 규칙을 **헤더 + 두 번역 단위**로 옮기면 무엇이 더 생기나를 본다((1)의 `extern inline` 헤더 줄 · (2)의 뒤집힘 · (5)의 주소).

### (1) ★★★ 링크 격자 — 헤더를 두 번역 단위가 include 하면

**언제 쓰나** — 작은 함수를 헤더에 두고 여러 `.c` 에서 부를 때. ★★★ **이 편의 본체**다.

```c
/* s39.h */
#ifndef S39_H
#define S39_H

#ifndef KW
#define KW inline                    /* 격자가 -DKW=... 로 바꿔 끼운다 */
#endif

KW int twice(int x) { return 2 * x; }

#endif
```

```c
/* s39a.c */
#include "s39.h"

#ifdef DECL
extern inline int twice(int x);      /* -DDECL 판에서만 들어가는 한 줄 */
#endif

int from_a(int v) { return twice(v); }
```

```c
/* s39b.c */
#include <stdio.h>
#include "s39.h"

int from_a(int v);

int main(void) {
    printf("twice(1) = %d · from_a(20) = %d\n", twice(1), from_a(20));
    return 0;
}
```

```text
===== 링크 격자 — KW 4 × 판 3 × 컴파일러 2 × 최적화 2 (두 번역 단위 s39a.c + s39b.c) (exit=0) =====
헤더의 KW (+ s39a.c)          	gcc -O0	gcc -O2	clang -O0	clang -O2
--- -std=c17
inline                        	undefined reference	링크 성공	undefined reference	링크 성공
static inline                 	링크 성공	링크 성공	링크 성공	링크 성공
extern inline                 	multiple definition	multiple definition	multiple definition	multiple definition
inline + DECL                 	링크 성공	링크 성공	링크 성공	링크 성공
--- -std=c17 -fgnu89-inline
inline                        	multiple definition	multiple definition	multiple definition	multiple definition
static inline                 	링크 성공	링크 성공	링크 성공	링크 성공
extern inline                 	undefined reference	링크 성공	undefined reference	링크 성공
inline + DECL                 	multiple definition	multiple definition	multiple definition	multiple definition
--- -std=gnu89
inline                        	multiple definition	multiple definition	multiple definition	multiple definition
static inline                 	링크 성공	링크 성공	링크 성공	링크 성공
extern inline                 	undefined reference	링크 성공	undefined reference	링크 성공
inline + DECL                 	multiple definition	multiple definition	multiple definition	multiple definition
(각 칸 = $CC <판> -Wall -Wextra <최적화> -DKW=<KW> s39a.c s39b.c -o x 의 링크 결과)
C99 판과 -fgnu89-inline 판이 갈린 칸 12 / 16
gcc 와 clang 이 갈린 칸 0 / 24
48 번의 컴파일·링크에서 나온 warning: 줄 합계 0
```

```text
===== gcc -std=c17 -Wall -Wextra -O0 -c s39a.c && gcc -std=c17 -Wall -Wextra -O0 -c s39b.c && gcc s39a.o s39b.o -o x (cc exit=1) =====
/usr/bin/ld: s39a.o: in function `from_a':
s39a.c:(.text+0x15): undefined reference to `twice'
/usr/bin/ld: s39b.o: in function `main':
s39b.c:(.text+0x1f): undefined reference to `twice'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -Wall -Wextra -O0 '-DKW=extern inline' -c s39a.c && gcc -std=c17 -Wall -Wextra -O0 '-DKW=extern inline' -c s39b.c && gcc s39a.o s39b.o -o x (cc exit=1) =====
/usr/bin/ld: s39b.o: in function `twice':
s39b.c:(.text+0x0): multiple definition of `twice'; s39a.o:s39a.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -Wall -Wextra -O0 -DDECL s39a.c s39b.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice(1) = 2 · from_a(20) = 40
```

그림 해설 (한 단계씩 — 첫 덩어리 `-std=c17`):

- ★★★ **`inline` 만 — `-O0` 은 `undefined reference`, `-O2` 는 성공.** 두 번역 단위 다 **인라인 정의만** 가졌고 **외부 정의는 어디에도 없다.** `-O0` 은 호출을 펼치지 않으니 링커가 외부 정의를 찾다 실패한다. **에러가 두 번역 단위 모두에서** 난다(`from_a` 와 `main`).
- ★★★ **`extern inline` 을 헤더에 두면 네 칸 다 `multiple definition`** — C99 의미에서 `extern` 이 붙은 선언은 **그 번역 단위의 정의를 외부 정의로** 만든다. 헤더를 include 한 **두 파일이 둘 다** 외부 정의를 가진다.
- ★★ **`static inline` 은 네 칸 다 성공** — 내부 링크라 **파일마다 제 사본**이다. 충돌할 이름이 링커에 안 간다.
- ★★★ **`inline` + `s39a.c` 에만 `extern inline` 선언(DECL) — 네 칸 다 성공.** 외부 정의가 **정확히 하나**다. 표준 예제 1 이 `extern double fahr(double); // creates an external definition` 으로 보이는 바로 그 모양이다.
- ★★ **gcc 와 clang 이 갈린 칸 0 / 24** — 이 규칙은 **두 컴파일러가 같은 답**을 낸다.

### (2) ★★★ gnu89 — 같은 소스, 뜻이 뒤집힌다

**언제 쓰나** — 옛 코드(또는 옛 기본값을 쓰는 빌드)가 컴파일러를 올린 뒤 링크가 깨질 때([29번 형제](../29-scope-and-linkage-static-extern/)의 「어디서 틀리나」 2번과 같은 자리).

```text
===== gcc -std=c17 -fgnu89-inline -Wall -Wextra -O0 -c s39a.c && gcc -std=c17 -fgnu89-inline -Wall -Wextra -O0 -c s39b.c && gcc s39a.o s39b.o -o x (cc exit=1) =====
/usr/bin/ld: s39b.o: in function `twice':
s39b.c:(.text+0x0): multiple definition of `twice'; s39a.o:s39a.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

그림 해설 (한 단계씩 — 격자의 둘째·셋째 덩어리):

- ★★★ **`-fgnu89-inline` 에서 `inline` 만은 네 칸 다 `multiple definition`** — gnu89 의 `inline` 은 **외부 정의를 만든다.** C99 에서 `undefined reference` 였던 자리가 **정반대 에러**가 된다.
- ★★★ **`extern inline` 은 `-O0` 에서 `undefined reference`, `-O2` 에서 성공** — gnu89 의 `extern inline` 은 **「펼칠 때만 쓰고 정의는 만들지 마라」** 다. C99 의 `inline` 만과 **같은 모양**이다.
- ★★ **`inline` + DECL 도 `multiple definition`** — 이미 모든 파일이 외부 정의를 가지니 선언 한 줄은 소용이 없다.
- ★★ **`static inline` 만 판을 가리지 않는다** — 네 칸 × 세 판 다 성공.
- ★★ **`-std=gnu89` 덩어리는 `-fgnu89-inline` 덩어리와 한 글자도 같다** — 판을 gnu89 로 고르면 인라인 의미도 따라온다.
- ★★★ **C99 판과 `-fgnu89-inline` 판이 갈린 칸 12 / 16** — 안 갈린 네 칸은 전부 `static inline` 줄이다.

```text
                     C99 (-std=c17)                 gnu89 (-fgnu89-inline)
                     ----------------------------   ----------------------------
   inline            인라인 정의 — 외부 정의 없음     외부 정의를 만든다
   extern inline     외부 정의를 만든다               펼칠 때만 — 정의 없음
   static inline     파일마다 사본                   파일마다 사본
```

### (3) ★★ `nm` 으로 번역 단위마다 — 글자가 이유를 말한다

**언제 쓰나** — 링크 에러가 **어느 파일의 무엇 때문**인지 가를 때.

```text
===== nm 으로 본 twice — 판 2 × KW 4 × 최적화 2 × 번역 단위 2 (gcc) (exit=0) =====
판 · KW                             	s39a.o -O0	s39b.o -O0	s39a.o -O2	s39b.o -O2
 inline                             	U	U	(없음)	(없음)
 static inline                      	t	t	(없음)	(없음)
 extern inline                      	T	T	T	T
 inline + DECL                      	T	U	T	(없음)
 -fgnu89-inline inline              	T	T	T	T
 -fgnu89-inline static inline       	t	t	(없음)	(없음)
 -fgnu89-inline extern inline       	U	U	(없음)	(없음)
 -fgnu89-inline inline + DECL       	T	T	T	T
(칸 = nm 이 twice 에 붙인 글자 · T 외부 정의 · t 이 파일 전용 · U 정의 없음·밖에서 찾는다 · (없음) 심볼 자체가 없다)
```

- ★★★ **C99 `inline` 만** — `-O0` 은 두 파일 다 **`U`**(정의 없음 · 밖에서 찾는다), `-O2` 는 **심볼 자체가 없다**(호출이 펼쳐져 필요 없어졌다). `-O2` 의 성공이 **보장이 아니라 부재**인 이유가 이 칸이다.
- ★★ **`extern inline`(헤더)** — 네 칸 다 **`T`**. 두 파일이 둘 다 외부 정의 → `multiple definition`.
- ★★ **DECL** — `s39a.o` 는 `T`, `s39b.o` 는 `U`(`-O0`) 또는 없음(`-O2`) — **본점 하나 + 손님 하나**.
- ★★ **gnu89 는 `inline` 과 `extern inline` 의 글자가 C99 와 맞바뀐다** — `T T T T` ↔ `U U (없음) (없음)`.
- ★ **`static inline` 은 `-O0` 에서 `t` 둘 · `-O2` 에서 없음** — 쓸모가 없어지면 **사본도 안 남는다.**

### (4) ★★ C++ — 같은 파일이 전부 링크된다

**언제 쓰나** — 「C++ 에서는 헤더에 `inline` 을 두면 되던데」.

```text
===== 같은 파일을 C++ 로 — KW 4 × 컴파일러 2 × 최적화 2 (-x c++ -std=c++17) (exit=0) =====
KW (+ s39a.c)         	g++ -O0	g++ -O2	clang++ -O0	clang++ -O2
inline                	링크 성공	링크 성공	링크 성공	링크 성공
static inline         	링크 성공	링크 성공	링크 성공	링크 성공
extern inline         	링크 성공	링크 성공	링크 성공	링크 성공
inline + DECL         	링크 성공	링크 성공	링크 성공	링크 성공
```

```text
===== g++ -x c++ -std=c++17 -O0 -c s39a.c -o a.o && g++ -x c++ -std=c++17 -O0 -c s39b.c -o b.o && nm -C a.o b.o | grep -E 'twice|:$' (exit=0) =====
a.o:
0000000000000000 W twice(int)
b.o:
0000000000000000 W twice(int)
```

- ★★★ **C++ 로 컴파일하면 16칸 전부 `링크 성공`** — C 에서 `undefined reference` 였던 `inline` 만도, `multiple definition` 이었던 `extern inline` 도 통과한다.
- ★★ **`nm` 이 `W`(약한 심볼)** — C++ 의 `inline` 함수는 **각 번역 단위에 정의를 두고 링커가 하나로 합친다.** 「정의가 여럿이어도 된다(단 같아야 한다)」가 C++ 의 `inline` 이다 — C 의 「이 정의는 외부 정의가 아니다」와 **뜻이 다르다.**
- ★ C++ 의 `inline` 변수(C++17)는 [29번 형제](../29-scope-and-linkage-static-extern/)의 (9)가 `u`/`V` 로 보였다. 정적 멤버·`inline` 변수의 정본은 [C++ 25 — 정적 멤버와 `inline` 변수](../../../cpp/syntax/25-static-members-and-inline-variables/)다.

### (5) ★★ 주소가 하나인가 — `static inline` 은 아니다

**언제 쓰나** — 헤더의 함수 주소를 **비교하거나 테이블 키로** 쓸 때.

```c
/* s39c.c */
#include "s39.h"

#ifdef DECL
extern inline int twice(int x);
#endif

int (*addr_c(void))(int) { return twice; }
```

```c
/* s39d.c */
#include <stdio.h>
#include "s39.h"

int (*addr_c(void))(int);

int main(void) {
    int (*mine)(int) = twice;
    printf("두 번역 단위의 &twice 가 같은가 = %d\n", mine == addr_c());
    return 0;
}
```

```text
===== 두 번역 단위에서 &twice — 언어 2 × KW 2 × 최적화 2 (s39c.c + s39d.c · gcc / g++) (exit=0) =====
언어 · KW                 	-O0	-O2
C static inline           	두 번역 단위의 &twice 가 같은가 = 0	두 번역 단위의 &twice 가 같은가 = 0
C inline + DECL           	두 번역 단위의 &twice 가 같은가 = 1	두 번역 단위의 &twice 가 같은가 = 1
C++ static inline         	두 번역 단위의 &twice 가 같은가 = 0	두 번역 단위의 &twice 가 같은가 = 0
C++ inline                	두 번역 단위의 &twice 가 같은가 = 1	두 번역 단위의 &twice 가 같은가 = 1
```

- ★★★ **`static inline` 은 두 번역 단위의 `&twice` 가 다르다(`= 0`)** — 파일마다 **다른 함수**다. C 도 C++ 도 같다.
- ★★ **C 의 DECL 판과 C++ 의 `inline` 은 같다(`= 1`)** — 표준 각주가 「**인라인 정의가 몇 개이든 함수의 주소는 하나**」라고 적는다. C 에서 그 「하나」는 **외부 정의의 주소**다.
- ★ **`-O0`/`-O2` 가 바꾸지 않는다** — 주소를 쓰면 **펼쳐도 정의가 남는다.**

### (6) ★★ 「`inline` 은 펼치라는 명령이 아니다」 — `call` 이 남는 칸

**언제 쓰나** — 「`inline` 을 붙였으니 호출 비용이 없다」.

```text
===== from_a 몸통의 call twice — 컴파일러 2 × 최적화 3 × KW 4 (s39a.c 만 · -std=c17) (exit=0) =====
컴파일러 · 최적화 	inline + DECL	static inline	extern inline	(지정자 없음)
gcc -O0           	call twice 1 번	call twice 1 번	call twice 1 번	call twice 1 번
gcc -O1           	call twice 0 번	call twice 0 번	call twice 0 번	call twice 0 번
gcc -O2           	call twice 0 번	call twice 0 번	call twice 0 번	call twice 0 번
clang -O0         	call twice 1 번	call twice 1 번	call twice 1 번	call twice 1 번
clang -O1         	call twice 0 번	call twice 0 번	call twice 0 번	call twice 0 번
clang -O2         	call twice 0 번	call twice 0 번	call twice 0 번	call twice 0 번
```

```text
===== gcc -std=c17 -O0 -S -masm=intel -fno-asynchronous-unwind-tables -DDECL s39a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^from_a:/,/ret/p' (cc exit=0) =====
from_a:
        endbr64
        push    rbp
        mov     rbp, rsp
        sub     rsp, 8
        mov     DWORD PTR -4[rbp], edi
        mov     eax, DWORD PTR -4[rbp]
        mov     edi, eax
        call    twice
        leave
        ret
```

- ★★★ **`-O0` 에서는 세 형태 · 두 컴파일러 전부 `call twice 1 번`** — `inline` 이 붙어 있어도 **펼치지 않았다.** 표준이 「제안의 효과는 구현 정의」라고 적은 자리가 이 칸이다.
- ★★★ **지정자가 없는 판(`-DKW=` — 그냥 `int twice(int)`)도 한 글자도 같다** — `-O0` 1 번 · `-O1`·`-O2` 0 번. **이 판에서 펼침을 정한 것은 `inline` 이 아니라 최적화 수준**이다. 펼친 것은 **최적화기**다.
- ★★★ **「그래서 빠르다」는 이 문서가 재지 않았다** — `call` 이 없어진 것은 **명령 수의 관찰**이지 시간이 아니다.

### (7) ★★ 제약 — 외부 링크 인라인 정의는 `static` 을 쓸 수 없다

**언제 쓰나** — 헤더의 `inline` 함수 안에 호출 횟수를 세는 `static` 변수를 두려 할 때.

```c
/* s39e.c */
static int hidden = 1;

inline int count_calls(void) {       /* 외부 링크 · inline 만 */
    static int calls;
    return ++calls;
}

inline int read_hidden(void) {       /* 외부 링크 · inline 만 */
    return hidden;
}

int use(void) { return count_calls() + read_hidden(); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s39e.c -o /dev/null (cc exit=0) =====
s39e.c:9:12: warning: ‘hidden’ is static but used in inline function ‘read_hidden’ which is not static
    9 |     return hidden;
      |            ^~~~~~
s39e.c:4:16: warning: ‘calls’ is static but declared in inline function ‘count_calls’ which is not static
    4 |     static int calls;
      |                ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s39e.c -o /dev/null (cc exit=0) =====
s39e.c:4:5: warning: non-constant static local variable in inline function may be different in different files [-Wstatic-local-in-inline]
    4 |     static int calls;
      |     ^
s39e.c:3:1: note: use 'static' to give inline function 'count_calls' internal linkage
    3 | inline int count_calls(void) {       /* 외부 링크 · inline 만 */
      | ^
      | static 
s39e.c:9:12: warning: static variable 'hidden' is used in an inline function with external linkage [-Wstatic-in-inline]
    9 |     return hidden;
      |            ^
s39e.c:8:1: note: use 'static' to give inline function 'read_hidden' internal linkage
    8 | inline int read_hidden(void) {       /* 외부 링크 · inline 만 */
      | ^
      | static 
s39e.c:1:12: note: 'hidden' declared here
    1 | static int hidden = 1;
      |            ^
2 warnings generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors -c s39e.c -o /dev/null (cc exit=1) =====
s39e.c:9:12: error: ‘hidden’ is static but used in inline function ‘read_hidden’ which is not static
    9 |     return hidden;
      |            ^~~~~~
s39e.c:4:16: error: ‘calls’ is static but declared in inline function ‘count_calls’ which is not static
    4 |     static int calls;
      |                ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic-errors -c s39e.c -o /dev/null (cc exit=1) =====
s39e.c:4:5: warning: non-constant static local variable in inline function may be different in different files [-Wstatic-local-in-inline]
    4 |     static int calls;
      |     ^
s39e.c:3:1: note: use 'static' to give inline function 'count_calls' internal linkage
    3 | inline int count_calls(void) {       /* 외부 링크 · inline 만 */
      | ^
      | static 
s39e.c:9:12: error: static variable 'hidden' is used in an inline function with external linkage [-Werror,-Wstatic-in-inline]
    9 |     return hidden;
      |            ^
s39e.c:8:1: note: use 'static' to give inline function 'read_hidden' internal linkage
    8 | inline int read_hidden(void) {       /* 외부 링크 · inline 만 */
      | ^
      | static 
s39e.c:1:12: note: 'hidden' declared here
    1 | static int hidden = 1;
      |            ^
1 warning and 1 error generated.
```

```c
/* s39f.c */
static int hidden = 1;

inline int count_calls(void) {
    static int calls;
    return ++calls;
}
extern inline int count_calls(void);  /* 이 번역 단위에 외부 정의를 만든다 */

static inline int read_hidden(void) { /* 내부 링크 */
    return hidden;
}

int use(void) { return count_calls() + read_hidden(); }
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s39f.c -o /dev/null (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s39f.c -o /dev/null (cc exit=0) =====
s39f.c:4:5: warning: non-constant static local variable in inline function may be different in different files [-Wstatic-local-in-inline]
    4 |     static int calls;
      |     ^
s39f.c:3:1: note: use 'static' to give inline function 'count_calls' internal linkage
    3 | inline int count_calls(void) {
      | ^
      | static 
1 warning generated.
```

그림 해설 (한 단계씩):

- ★★★ **두 줄 다 표준의 제약 위반**이다 — 외부 링크 인라인 정의가 **수정 가능한 정적 객체(`calls`)를 정의**하고, **내부 링크 식별자(`hidden`)를 참조**했다.
- ★★★ **그런데 gcc 는 경고 둘에 `cc exit=0`** 이다 — **「종료 코드 0인데 ill-formed」** 의 고정 항목이다. **`-pedantic-errors` 라야** 두 줄 다 에러(`exit=1`)가 된다.
- ★★ **clang 도 기본은 경고 둘 · `exit=0`** 이고, `-pedantic-errors` 에서는 **`hidden` 줄만 에러**로 올린다(`-Werror,-Wstatic-in-inline`). **`calls` 줄은 경고로 남는다** — 두 컴파일러가 **어느 제약을 `-pedantic` 묶음에 넣었나**가 다르다.
- ★★ **`s39f.c`(외부 정의로 만들고 `static inline` 으로 바꾼 판)는 gcc 0건** — 외부 정의에는 이 제약이 없다. ★ **clang 은 `calls` 에 여전히 경고**한다(「파일마다 다를 수 있다」) — 이 판에서는 **외부 정의가 하나뿐이라 그 걱정이 해당하지 않는다.** 경고는 조심하라는 말이고 **위반의 판정이 아니다**(종료 코드 `0`).
- ★ 표준 각주가 이유를 준다 — 인라인 정의는 **외부 정의와 서로 다른 것**이라, 안의 정적 객체도 **정의마다 따로** 생긴다. 호출 횟수가 **어느 정의를 탔느냐에 따라 갈리게** 된다.

## 문법 — 형태와 규칙

### 형태

(1)의 `s39.h` + `s39a.c`(DECL 판) + `s39b.c` 가 이 절의 **실제로 링크되는 형태**다. 헤더에 둘 때의 권장형 둘:

| 쓴 꼴 | 뜻 | 판 |
|---|---|---|
| 헤더: `static inline int f(int x) { … }` | ★★ 파일마다 사본 · 판 무관 · **주소가 파일마다 다르다** | C99 부터 |
| 헤더: `inline int f(int x) { … }` + **한** `.c`: `extern inline int f(int);` | ★★★ 외부 정의 하나 · 주소 하나 · **C99 의미에서만** | C99 부터 |
| 헤더: `extern inline int f(int x) { … }` | ★ C99 에서 **`multiple definition`** · gnu89 에서는 「펼칠 때만」 | 판에 따라 반대 |
| 헤더: `inline int f(int x) { … }` 만 | ★ C99 `-O0` 에서 **`undefined reference`** | — |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 헤더의 `inline` 만(외부 정의 없음) | 경고 0 · ★ **`-O0` 링크 실패 · `-O2` 통과** | ★★ 표준(외부 정의가 필요한데 없다) | (1) |
| 헤더의 `extern inline` 정의 | 경고 0 · **링크 `multiple definition`** | ★★ 표준(외부 정의가 둘 — 링커가 잡음) | (1) |
| 외부 링크 `inline` 안의 수정 가능한 `static` 변수 | gcc 경고 · **`cc exit=0`** · `-pedantic-errors` 에러 | ★★★ 제약 위반 | (7) |
| 외부 링크 `inline` 이 `static` 식별자 참조 | 같음 | ★★★ 제약 위반 | (7) |
| gnu89 판 코드를 C99 판으로 빌드 | **링크 에러가 반대 종류로** | 판 경계 | (2) |
| `static inline` 함수의 주소를 파일 사이에서 비교 | 경고 0 · **`= 0`** | ★ 표준(다른 함수다) | (5) |

### 규칙 불릿

- ★★★ **외부 링크 함수에 `extern` 없는 `inline` 만 있으면 그 정의는 외부 정의가 아니다** — 어딘가 한 곳에 외부 정의가 있어야 한다.
- ★★★ **`extern inline` 선언(또는 `inline` 없는 선언) 한 줄이 그 번역 단위의 정의를 외부 정의로 만든다** — 그 줄은 **한 `.c` 에만**.
- ★★ **`static inline` 은 판 무관하게 안전하다** — 대가는 **파일마다 사본 · 주소가 다름 · 정적 변수가 파일마다 따로**.
- ★★ **펼치느냐는 구현이 정한다** — `-O0` 은 안 펼쳤다.
- ★★ **외부 링크 인라인 정의 안에는 수정 가능한 `static` 변수 · 내부 링크 참조 금지**(제약).
- ★ **gnu89 는 `inline` 과 `extern inline` 의 뜻이 C99 와 반대** — `-fgnu89-inline` · `-std=gnu89`.
- ★ **C++ 의 `inline` 은 「여러 정의 허용」** — C 와 다르다.

## 어디서 틀리나

### 1. ★★★ 「헤더에 `inline` 을 두면 끝」

C 에서는 **외부 정의가 없어** `-O0` 에서 링크가 깨진다((1)). `-O2` 에서 되는 것은 **심볼이 사라져서**다((3)).

### 2. ★★★ 「C++ 에서 되던 헤더를 C 로 옮겼다」

C++ 은 16칸 전부 성공, C 는 `inline` 만 줄과 `extern inline` 줄이 깨진다((1)·(4)). **같은 낱말, 다른 규칙**이다.

### 3. ★★ 「`extern inline` 이 제일 확실해 보인다」

C99 에서 헤더에 두면 **`multiple definition`** 이다((1)). gnu89 에서는 **정반대로 정의가 없다**((2)).

### 4. ★★ 「`static inline` 이면 같은 함수다」

**번역 단위마다 다른 함수** — 주소 비교가 `0` 이다((5)). 안의 `static` 변수도 파일마다 따로다.

### 5. ★★ 「`inline` 을 붙였으니 호출이 없다」

`-O0` 에서는 **`call twice` 가 남았다**((6)). 그리고 **빠른지는 재지 않았다.**

### 6. ★★ 「경고만 났으니 괜찮다」

`static` 을 쓰는 외부 링크 `inline` 은 **제약 위반**인데 **`cc exit=0`** 이다((7)). `-pedantic-errors` 로만 막힌다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸이 본체**다 — 인라인 정의와 외부 정의의 구분, 제약, 주소 하나가 전부 표준 문장이다.\
★★ **「구현 정의」 칸에 「펼치느냐」**, **「미명시」 칸에 「어느 정의를 쓰나」** 가 든다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **인라인 정의는 외부 정의가 아니다** · `extern` 선언이 외부 정의를 만든다 · **외부 정의는 하나**(둘이면 링커가 잡았다) · **주소는 하나** · 제약 둘 · `static inline` 은 내부 링크 | 링크 격자 · `nm` · 주소 격자 · (7) |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **해당 없음** | — |
| ★★ **구현 정의** | 문서화 의무가 있다 | ★★★ **「제안이 얼마나 먹히나」**(표준이 직접 구현 정의라고 적는다) — `-O0` 의 `call twice` | 어셈블리 격자 |
| ★★ **컴파일러 구현** | 도구의 선택 | ★★ **gnu89 의미**(`-fgnu89-inline` · `-std=gnu89`) · 제약 위반을 **경고로만** 내는 기본값 · clang 이 `-pedantic-errors` 에 **한 줄만** 올린 것 · **C++ 의 `W` 심볼** | 판 격자 · (7) |
| ★ **미명시** | 몇 가지 중 하나 | ★ **호출이 인라인 정의를 쓰나 외부 정의를 쓰나** | ★ 던지지 않았다(두 정의가 **같은 몸통**이라 값으로는 가를 수 없다) |
| **UB** | 아무 일이나 | ★ **해당 없음(이 편이 던진 것 중에는)** — 외부 정의가 둘인 것은 표준상 규칙 위반이지만 이 판에서는 **링커가 에러로 잡았다** | 링크 격자 |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★★ **컴파일 단계는 링크 격자 48 번 전부에서 `warning:` 0 줄**(격자의 끝 줄) — 「외부 정의가 없다 / 둘이다」는 **링커만** 안다 · ★★ `-O2` 는 **없는 외부 정의를 감춘다**((3)의 「(없음)」) |
| ★★ **구현 정의** | ★ 펼쳤는지 안 펼쳤는지 알려 주는 진단이 없다 — 어셈블리로만 보인다 |
| ★★ **컴파일러 구현** | ★★ **gnu89 판으로 빌드되는지 알려 주는 경고가 없다** — 링크 에러의 **종류**가 바뀔 뿐이다 |
| ★ **미명시** | ★ 어느 정의를 탔는지 **아무 창도 말하지 않는다** |
| ★★ **(층을 가로지름)** | ★★★ **「종료 코드 0인데 ill-formed」 두 줄**((7) — gcc·clang 기본값) · ★ clang 은 `-pedantic-errors` 에서도 **한 줄을 경고로 남겼다** |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **인라인 규칙의 사고는 전부 링크에서 난다** — 컴파일러는 한 번역 단위만 보니 「정의가 몇 개인가」를 모른다.
  - ★★ **`-O2` 의 성공은 증거가 아니다** — 판을 `-O0` 으로 바꾸거나 주소를 쓰면 드러난다.
  - ★★ **판(gnu89)이 바뀌면 에러의 종류가 뒤집힌다** — 에러 문구만 보고 원인을 적으면 틀린다(목록의 **45번 주제**).

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 헤더에 작은 함수 · 간단히 | ★★ **`static inline`** | `inline` 만 |
| 헤더에 작은 함수 · 주소·정적 상태가 하나여야 | ★★★ **헤더 `inline` + 한 `.c` 의 `extern inline` 선언** | 헤더의 `extern inline` 정의 |
| 옛 gnu89 코드 | ★ `-fgnu89-inline` 을 **명시**하거나 C99 의미로 옮기기 | 판을 모른 채 컴파일러만 올리기 |
| 호출 횟수 세기 | ★ **외부 정의 쪽(`.c`)에 정적 변수** | 외부 링크 `inline` 안의 `static` |
| 성능 | ★★★ **재 보고 판단** — 이 문서는 재지 않았다 | 「`inline` 이니까 빠르다」 |
| C++ 과 공유하는 헤더 | ★ **`static inline`** 이 두 언어에서 같은 뜻 | C++ 의 `inline` 규칙을 C 에 기대기 |

판단 규칙 두 줄.

- ★★★ **C 의 `inline` 을 보면 「외부 정의는 어디 있나」를 먼저 묻는다** — 답이 없으면 `-O0` 에서 깨진다.
- ★★ **헤더에는 `static inline` 이 기본값**, 주소·상태가 하나여야 할 때만 외부 정의 한 줄을 더한다.

## 핵심 문장

- ★★★ **헤더의 `inline` 만은 두 번역 단위 모두에서 `-O0` 에 `undefined reference`, `-O2` 에 성공했다 — `nm` 은 `U` 와 「심볼 없음」으로 이유를 말했다.**
- ★★★ **헤더의 `extern inline` 정의는 C99 에서 네 칸 다 `multiple definition` 이다 — `extern inline` 선언은 한 `.c` 에만 둔다.**
- ★★★ **C99 판과 gnu89 판이 갈린 칸 12 / 16, gcc 와 clang 이 갈린 칸 0 / 24 — `inline` 과 `extern inline` 의 뜻이 판에 따라 맞바뀐다.**
- ★★ **같은 파일을 C++ 로 컴파일하면 16칸 전부 링크된다 — `nm` 의 `W` 가 「여러 정의 허용」을 말한다.**
- ★★ **`static inline` 은 두 번역 단위의 `&twice` 가 달랐고(0), 외부 정의 판과 C++ `inline` 은 같았다(1).**
- ★★ **`-O0` 은 세 형태 모두 `call twice` 를 남겼다 — `inline` 은 명령이 아니다. 속도는 재지 않았다.**
- ★★ **외부 링크 `inline` 안의 `static` 은 제약 위반인데 gcc 는 `cc exit=0` — `-pedantic-errors` 라야 막힌다.**

## 관련 자료

- [29번 형제 — 스코프와 링크](../29-scope-and-linkage-static-extern/) — ★★★ **선행.** (8)이 **한 번역 단위의 C99 `inline`** 12칸을 쟀고 (9)가 C++ 의 `inline` 변수를 보였다. `static`/`extern` 링크 규칙의 정본.
- [34번 형제 — 함수 선언·정의·프로토타입](../34-function-declarations-definitions-and-prototypes/) — ★★ 「선언과 정의」의 앞.
- [C++ 25 — 정적 멤버와 `inline` 변수](../../../cpp/syntax/25-static-members-and-inline-variables/) — ★ C++ 의 `inline` 이 「여러 정의 허용」인 자리.
- 목록의 **44번 주제**(헤더와 분할 컴파일) — ★★ 헤더에 무엇을 두나의 정본.
- 목록의 **45번 주제**(링크 오류 읽기) — ★★ `undefined reference` / `multiple definition` 을 거꾸로 읽는 법.

## 용어 풀이

> **`static inline`** — 내부 링크 인라인 함수. 번역 단위마다 **자기 사본**이고 외부 정의가 필요 없다.\
> 예: `static inline int twice(int x) { return 2 * x; }`.

> **gnu89 인라인 의미** — C99 이전 GNU C 의 규칙. **`inline` 은 외부 정의를 만들고, `extern inline` 은 정의를 만들지 않는다** — C99 와 반대.\
> 예: `gcc -fgnu89-inline` · `gcc -std=gnu89`.

> **`nm` 의 `T` / `t` / `U` / `W`** — 외부 정의(텍스트) / 이 파일 전용 / 정의 없음(밖에서 찾음) / 약한 심볼(링커가 하나로 합침).\
> 예: C++ 의 `inline` 함수는 `W twice(int)`.

> **ODR(One Definition Rule)** — C++ 의 「정의는 하나 — 단 `inline` 은 번역 단위마다 같은 정의가 있어도 된다」 규칙. C 에는 **이 이름의 규칙이 없고**, 대신 「외부 정의는 하나」와 인라인 정의 규칙이 있다.\
> 예: (4)의 C++ 격자 16칸 성공.

## 더 들어가면

- ★★ **미명시 칸을 값으로 가르기** — 인라인 정의와 외부 정의의 **몸통을 다르게** 두면(표준상 허용되는지부터 따져야 한다) 어느 쪽을 탔는지 보인다. ★ **던지지 않았다.**
- ★ **`__attribute__((always_inline))` · `noinline`** — 펼침을 **강제**하는 컴파일러 확장. ★ **던지지 않았다.**
- ★ **LTO 에서의 인라인** — 번역 단위를 넘는 펼침. ★ **던지지 않았다.**
