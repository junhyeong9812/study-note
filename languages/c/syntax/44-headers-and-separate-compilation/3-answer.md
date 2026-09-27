# c/syntax/44 — 헤더와 분할 컴파일: 「**헤더는 include 한 모든 번역 단위에 그대로 복사된다 — 그래서 헤더에는 복사돼도 정의가 하나로 남는 것만 둔다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** · **clang 18.1.3** · **g++ 13.3.0** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s44*.c` · `s44*.h` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
> ★★★ **본체 창은 링크 결과 + `nm`** — 헤더 내용 14 × 빌드 5.
> ★★ **흔들리는 칸** — 없다. 링크 문구는 `-c` 로 이름을 고정한 목적 파일로 찍었다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 헤더 배치 격자 — **깨진 칸 18 / 42(여섯 행) · 세 컴파일러가 갈린 행 0 · `-fcommon` 은 9행만 · g++ 는 11행만 다르다** ★★★

**출력**

```text
===== 헤더 배치 격자 — 헤더 내용 14 × 빌드 5 (두 번역 단위 s44a.c + s44b.c) (exit=0) =====
K · 헤더 s44h.h 에 둔 것                	gcc	gcc-12	clang	gcc -fcommon	g++ (C++17)	nm s44a.o / s44b.o (gcc)
1 int hf(int);  (정의 없음)             	undefined reference	undefined reference	undefined reference	undefined reference	undefined reference	U / U
2 int hf(int);  + s44a.c 에 정의        	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	T / U
3 int hf(int x) { … }                   	multiple definition	multiple definition	multiple definition	multiple definition	multiple definition	T / T
4 static int hf(int x) { … }            	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	t / t
5 static inline int hf(int x) { … }     	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	t / t
6 extern int hv;  (정의 없음)           	undefined reference	undefined reference	undefined reference	undefined reference	undefined reference	U / U
7 extern int hv;  + s44a.c 에 int hv = 0;	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	B / U
8 int hv = 0;                           	multiple definition	multiple definition	multiple definition	multiple definition	multiple definition	B / B
9 int hv;                               	multiple definition	multiple definition	multiple definition	링크 성공	multiple definition	B / B
10 static int hv = 0;                   	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	b / b
11 const int hv = 5;                    	multiple definition	multiple definition	multiple definition	multiple definition	링크 성공	R / R
12 struct hs { int v; };                	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
13 enum he { HE_ONE = 1 };              	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
14 typedef int ht;                      	링크 성공	링크 성공	링크 성공	링크 성공	링크 성공	(없음) / (없음)
(칸 = $CC -O0 -Wall -Wextra -DK=<행> 으로 s44a.c · s44b.c 를 따로 -c 한 뒤 두 .o 를 링크한 결과 · nm 은 이름 hf/hv 의 글자)
링크가 깨진 칸(gcc · gcc-12 · clang) 18 / 42
gcc · gcc-12 · clang 이 서로 갈린 행 0 / 14
gcc 기본과 -fcommon 이 갈린 행 1 / 14
C(gcc) 와 C++(g++) 가 갈린 행 1 / 14
```

```text
===== gcc -std=c17 -DK=3 -c s44a.c -o s44a.o && gcc -std=c17 -DK=3 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44b.o: in function `hf':
s44b.c:(.text+0x0): multiple definition of `hf'; s44a.o:s44a.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=1 -c s44a.c -o s44a.o && gcc -std=c17 -DK=1 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44a.o: in function `use_a':
s44a.c:(.text+0xe): undefined reference to `hf'
/usr/bin/ld: s44b.o: in function `use_b':
s44b.c:(.text+0xe): undefined reference to `hf'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=11 -c s44a.c -o s44a.o && gcc -std=c17 -DK=11 -c s44b.c -o s44b.o && gcc s44a.o s44b.o -o x (cc exit=1) =====
/usr/bin/ld: s44b.o:(.rodata+0x0): multiple definition of `hv'; s44a.o:(.rodata+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -DK=11 -c s44a.c -o s44a.o && nm s44a.o && g++ -x c++ -std=c++17 -DK=11 -c s44a.c -o s44a.o && nm -C s44a.o (cc exit=0) =====
0000000000000000 R hv
0000000000000000 T use_a
0000000000000000 T use_a()
0000000000000000 r hv
```

```text
===== gcc -std=c17 -O0 -DK=5 -c s44a.c -o s44a.o && nm s44a.o && gcc -std=c17 -O2 -DK=5 -c s44a.c -o s44a.o && nm s44a.o (cc exit=0) =====
0000000000000000 t hf
000000000000000f T use_a
0000000000000000 T use_a
```

**왜 그런가**

- ★★★ **`multiple definition` 넷(3 · 8 · 9 · 11)** — 헤더의 **정의**가 두 `.o` 에 복사돼 외부 정의가 둘이다(`nm` 이 양쪽에 `T`/`B`/`R`).
- ★★★ **`undefined reference` 둘(1 · 6)** — 선언만 있고 정의가 **아무 데도** 없다(`U / U`). **2 · 7행**처럼 `.c` 하나에 정의를 더하면 `T / U` · `B / U` 로 성공.
- ★★ **`static`(4 · 10)·`static inline`(5)** 은 내부 링크라 `t / t` · `b / b` — 링커가 서로 모른다. **타입(12\~14)** 은 심볼이 없다.
- ★★ **`-fcommon` 은 9행 `int hv;`(잠정 정의)만** 살린다 — 공용 심볼로 합쳐진다. 8행(초기자 있음)은 못 살린다.
- ★★ **g++ 는 11행만** 다르다 — C++ 의 파일 스코프 `const` 는 내부 링크(`r hv`), C 는 외부(`R hv`).
- ★ `static inline` 의 글자는 `-O0` 에서 `t`, `-O2` 에서 **없음**(호출이 펼쳐졌다).

### 2. 헤더의 `static` — **`a_bump() -> 1, 2 · hbump() -> 1 · a_fn() == hbump : 0` · `nm` 에 `t hbump`·`b hcount` 가 파일마다 하나씩** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44sa.c s44sb.c -o x ; ./x (cc exit=0 · run exit=0) =====
a_bump() -> 1, 2 · hbump() -> 1 · a_fn() == hbump : 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44sa.c -o s44sa.o && gcc -std=c17 -Wall -Wextra -pedantic -c s44sb.c -o s44sb.o && nm s44sa.o s44sb.o | grep -E 'hbump|hcount|:$' (exit=0) =====
s44sa.o:
0000000000000000 t hbump
0000000000000000 b hcount
s44sb.o:
0000000000000000 t hbump
0000000000000000 b hcount
```

**왜 그런가**

- ★★★ `static` 은 **내부 링크** — 두 번역 단위가 **각자의** `hcount` 와 `hbump` 를 가진다. a 쪽이 두 번 올려도 b 쪽은 1 부터, 함수 주소도 다르다.

### 3. 쓰지 않는 헤더 함수 — **`hbump` 만 `-Wunused-function` · `hinc` 는 0줄** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44u.c -o /dev/null (cc exit=0) =====
In file included from s44u.c:1:
s44s.h:2:12: warning: ‘hbump’ defined but not used [-Wunused-function]
    2 | static int hbump(void) { return ++hcount; }
      |            ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44u.c -o /dev/null (cc exit=0) =====
In file included from s44u.c:1:
./s44s.h:2:12: warning: unused function 'hbump' [-Wunused-function]
    2 | static int hbump(void) { return ++hcount; }
      |            ^~~~~
1 warning generated.
```

**왜 그런가**

- ★★ 쓰지 않은 `static` 함수는 **죽은 정의**라 경고 대상이다. `static inline` 은 헤더용 관용으로 보고 **두 컴파일러 다 경고하지 않는다.**

### 4. guard 대 `#pragma once` — **guard 전부 통과 · guard 없음 전부 에러 · `#pragma once` 는 사본(같은 mtime)에서 gcc 통과 · clang 에러 · 다른 mtime 사본은 셋 다 에러** ★★★

**출력**

```text
===== include guard 대 #pragma once — 헤더 3 × 두 번째 경로 6 × 컴파일러 3 (exit=0) =====
두 번째 include               	같은 inode	같은 내용	같은 mtime
d1/ · 같은 경로 두 번         	예	예	예
d3/ · 디렉토리 심볼릭 링크    	예	예	예
d5/ · 파일 심볼릭 링크        	예	예	예
d6/ · 하드 링크               	예	예	예
d2/ · 사본 · 같은 mtime       	아니오	예	예
d4/ · 사본 · 다른 mtime       	아니오	예	아니오
---
헤더 · 두 번째 include              	gcc	gcc-12	clang
s44n.h · d1/ 같은 경로 두 번        	재정의 에러	재정의 에러	재정의 에러
s44n.h · d3/ 디렉토리 심볼릭 링크   	재정의 에러	재정의 에러	재정의 에러
s44n.h · d5/ 파일 심볼릭 링크       	재정의 에러	재정의 에러	재정의 에러
s44n.h · d6/ 하드 링크              	재정의 에러	재정의 에러	재정의 에러
s44n.h · d2/ 사본 · 같은 mtime      	재정의 에러	재정의 에러	재정의 에러
s44n.h · d4/ 사본 · 다른 mtime      	재정의 에러	재정의 에러	재정의 에러
s44g.h · d1/ 같은 경로 두 번        	통과	통과	통과
s44g.h · d3/ 디렉토리 심볼릭 링크   	통과	통과	통과
s44g.h · d5/ 파일 심볼릭 링크       	통과	통과	통과
s44g.h · d6/ 하드 링크              	통과	통과	통과
s44g.h · d2/ 사본 · 같은 mtime      	통과	통과	통과
s44g.h · d4/ 사본 · 다른 mtime      	통과	통과	통과
s44p.h · d1/ 같은 경로 두 번        	통과	통과	통과
s44p.h · d3/ 디렉토리 심볼릭 링크   	통과	통과	통과
s44p.h · d5/ 파일 심볼릭 링크       	통과	통과	통과
s44p.h · d6/ 하드 링크              	통과	통과	통과
s44p.h · d2/ 사본 · 같은 mtime      	통과	통과	재정의 에러
s44p.h · d4/ 사본 · 다른 mtime      	재정의 에러	재정의 에러	재정의 에러
(칸 = $CC -std=c17 -DFIRST="d1/<헤더>" -DSECOND="<디렉토리>/<헤더>" -c s44m.c 의 결과)
재정의 에러가 난 칸 22 / 54
gcc 와 clang 이 갈린 행 1 / 18
```

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44p.h"' '-DSECOND="d2/s44p.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44p.h
```

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44g.h"' '-DSECOND="d2/s44g.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44g.h
. d2/s44g.h
```

```text
===== gcc -std=c17 -H '-DFIRST="d1/s44g.h"' '-DSECOND="d1/s44g.h"' -c s44m.c -o /dev/null (cc exit=0) =====
. d1/s44g.h
```

```text
===== clang -std=c17 '-DFIRST="d1/s44p.h"' '-DSECOND="d2/s44p.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
./d2/s44p.h:3:8: error: redefinition of 'gq'
    3 | struct gq { int v; };
      |        ^
./d1/s44p.h:3:8: note: previous definition is here
    3 | struct gq { int v; };
      |        ^
1 error generated.
```

```text
===== gcc -std=c17 '-DFIRST="d1/s44p.h"' '-DSECOND="d4/s44p.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d4/s44p.h:3:8: error: redefinition of ‘struct gq’
    3 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44p.h:3:8: note: originally defined here
    3 | struct gq { int v; };
      |        ^~
```

```text
===== gcc -std=c17 '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d1/s44n.h:1:8: error: redefinition of ‘struct gq’
    1 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44n.h:1:8: note: originally defined here
    1 | struct gq { int v; };
      |        ^~
```

**왜 그런가**

- ★★★ **guard 는 매크로 이름으로 판단**해 파일이 무엇이든 두 번째를 비운다 — 여섯 경로 18칸 전부 통과.
- ★★★ **`#pragma once` 는 「같은 파일인가」를 컴파일러가 판단**한다 — 같은 inode(같은 경로 · 두 심볼릭 링크 · 하드 링크)는 세 컴파일러 다 같은 파일로 봤다. **같은 내용 · 같은 mtime 사본**은 gcc·gcc-12 가 같은 파일로(`-H` 한 줄), clang 은 다른 파일로 봤다. mtime 이 다르면 셋 다 다른 파일.
- ★★ **갈린 행 1 / 18** — 심볼릭 링크 행은 **안 갈렸다.**
- ★★ `-H` — guard 사본은 **두 파일을 다 연다**(비우는 것은 연 뒤). 같은 경로 guard 는 한 번만 연다.

### 5. 순환 include — **`s44e1.c`(ea 먼저) 성공 · `s44e2.c`(eb 먼저) 불완전 타입 에러** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44e1.c -o x && clang -std=c17 -Wall -Wextra -pedantic s44e1.c -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s44e2.c -o /dev/null (cc exit=1) =====
In file included from s44eb.h:4,
                 from s44e2.c:1:
s44ea.h:6:31: error: field ‘inner’ has incomplete type
    6 | struct ea { int id; struct eb inner; };
      |                               ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44e2.c -o /dev/null (cc exit=1) =====
In file included from s44e2.c:1:
In file included from ./s44eb.h:4:
./s44ea.h:6:31: error: field has incomplete type 'struct eb'
    6 | struct ea { int id; struct eb inner; };
      |                               ^
./s44ea.h:6:28: note: forward declaration of 'struct eb'
    6 | struct ea { int id; struct eb inner; };
      |                            ^
1 error generated.
```

```text
===== gcc -std=c17 -E -P s44e1.c (cc exit=0) =====
struct eb { int id; struct ea *owner; };
struct ea { int id; struct eb inner; };
int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

```text
===== gcc -std=c17 -E -P s44e2.c (cc exit=0) =====
struct ea { int id; struct eb inner; };
struct eb { int id; struct ea *owner; };
int main(void) {
    struct ea a = { 1, { 2, 0 } };
    a.inner.owner = &a;
    return a.inner.owner->id - 1;
}
```

**왜 그런가**

- ★★★ **guard 가 순환을 끊은 자리에서 한쪽이 불완전해진다** — `s44e2.c` 는 `s44eb.h` → `s44ea.h` → (`s44eb.h` 는 guard 로 빈손) 순이라 `struct ea { … struct eb inner; }` 가 `struct eb` 보다 **먼저** 나온다. `s44e1.c` 는 그 반대라 통과한다.
- ★★ **푸는 법** — 포인터만 쓰는 쪽(`s44fb.h`)이 상대를 include 하지 말고 `struct fa;` **전방 선언**만 둔다. 그러면 순서와 무관하다.

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s44f2.c -o x ; ./x (cc exit=0 · run exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s44f2.c -o /dev/null (cc exit=0) =====
```

### 6. include 트리와 의존성 — **`-H` 는 `.` · `..` 로 깊이를 · `-MMD` 는 `s44t.o: s44t.c s44fa.h s44fb.h`** ★★

**출력**

```text
===== gcc -std=c17 -H -c s44t.c -o s44t.o (cc exit=0) =====
. /usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h
. s44fa.h
.. s44fb.h
Multiple include guards may be useful for:
/usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h
```

```text
===== gcc -std=c17 -MMD -c s44t.c -o s44t.o && cat s44t.d (cc exit=0) =====
s44t.o: s44t.c s44fa.h s44fb.h
```

```text
===== gcc -std=c17 -MD -c s44t.c -o s44t.o && cat s44t.d (cc exit=0) =====
s44t.o: s44t.c /usr/include/stdc-predef.h \
 /usr/lib/gcc/x86_64-linux-gnu/13/include/stddef.h s44fa.h s44fb.h
```

**왜 그런가**

- ★★ `-H` 는 여는 헤더를 깊이만큼 점을 붙여 찍고, guard 가 없는 헤더를 「Multiple include guards may be useful for」로 알려 준다(여기선 gcc 의 `stddef.h`).
- ★★★ `-MMD` 는 **사용자 헤더만**(`-MD` 는 `stdc-predef.h`·`stddef.h` 까지) Makefile 규칙으로 적는다 — **`s44fb.h` 를 고치면 `s44t.o` 를 다시 만든다.**

### 7. 헤더에 둬도 되는 것의 공통점 (왜) ★★★

- ★★★ 통과한 행은 전부 **「두 번 복사돼도 외부 정의가 0 개(타입 · 내부 링크) 또는 `.c` 한 곳의 1 개」** 다. N3220 — 외부 링크 식별자는 **프로그램 전체에 외부 정의가 정확히 하나**.
- ★★ **`static` 은 규칙을 지키지만 뜻이 바뀐다** — 번역 단위마다 사본이라 값이 따로 논다(2번), 안 쓰면 경고가 난다(3번). 공유가 목적이면 `extern` + 정의 하나, 함수라면 `static inline`.

### 8. `const` 행의 두 언어 (경계) ★★

- ★★ **C 의 파일 스코프 `const` 는 외부 링크** — `R hv`(대문자 = 외부)가 양쪽 `.o` 에 있어 `multiple definition`. **C++ 는 내부 링크** — `r hv`(소문자)라 통과(1번의 `44-h-k11-nm` 블록).
- ★ C 에서는 **`enum` 상수 · `#define` · `static const`**(★ `static const` 는 이 편이 던지지 않았다 — 10행과 같은 내부 링크 규칙이다).

### 9. 이미 잰 격자 (연결) ★★

- ★★ [29번 형제](../29-scope-and-linkage-static-extern/)의 (5) — 잠정 정의 두 개를 **컴파일러 3 × 플래그 3** 으로 쟀다. **GCC 10 · Clang 11 에서 `-fno-common` 이 기본**이 됐다(그 편이 문서로 확인 · 이 머신의 판은 전부 경계 뒤).
- ★ [39번 형제](../39-inline-and-c-inline-rules/) — 헤더의 `extern inline` 은 두 컴파일러 · 두 최적화 **전부 `multiple definition`**.

### 10. 명세에 없는 것 · 허용하는데 안 되는 것 (경계) ★★

- ★★ **`#pragma once` 는 N3220 에 없다**(0건) — 4번의 `s44p.h` 결과는 **컴파일러 구현**이다.
- ★★ **C23 은 같은 내용의 태그 재정의를 호환 타입 조건으로 허용**한다. **이 판의 gcc 13 · clang 18 은 `-std=c2x` 에서도 재정의 에러**다.

```text
===== gcc -std=c2x '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
d1/s44n.h:1:8: error: redefinition of ‘struct gq’
    1 | struct gq { int v; };
      |        ^~
In file included from s44m.c:1:
d1/s44n.h:1:8: note: originally defined here
    1 | struct gq { int v; };
      |        ^~
```

```text
===== clang -std=c2x '-DFIRST="d1/s44n.h"' '-DSECOND="d1/s44n.h"' -c s44m.c -o /dev/null (cc exit=1) =====
In file included from s44m.c:2:
./d1/s44n.h:1:8: error: redefinition of 'gq'
    1 | struct gq { int v; };
      |        ^
s44m.c:1:10: note: './d1/s44n.h' included multiple times, additional include site here
    1 | #include FIRST
      |          ^
s44m.c:2:10: note: './d1/s44n.h' included multiple times, additional include site here
    2 | #include SECOND
      |          ^
./d1/s44n.h:1:8: note: unguarded header; consider using #ifdef guards or #pragma once
    1 | struct gq { int v; };
      |        ^
1 error generated.
```

### 11. 다섯 층과 도구가 못 보는 것 (연결) ★★★

- ★★★ **표준** — 외부 정의는 하나 · `static` 은 사본 · 타입은 심볼 없음 · C 의 `const` 는 외부 링크 · 불완전 타입 멤버 금지. **UB** — 외부 정의가 둘(이 판은 링커가 막았다). **조건부 표준** — C23 태그 재정의(미구현). **컴파일러 구현** — `#pragma once` 의 동일성 · `-fcommon` · `-H` · `-MMD` · 경고.
- ★★★ **0줄인데 틀린 자리** — ① 헤더의 `static` 변수가 사본인 것(2번) ② gcc 가 `#pragma once` 사본을 **버린 것**(4번 — `-H` 로만 보인다).

### 12. 경계 (연결) ★

- ★ [`compiler-pipeline/`](../../../../cs/foundations/compiler-pipeline/) 「4. 컴파일 전체 흐름과 링커」 — **`.o` 를 링커가 합친다**까지. 이 편은 **같은 헤더를 가진 `.o` 가 왜 충돌하나**부터.
- ★ 링크 에러 거꾸로 읽기 = [목록의 **45번 주제**](../45-translation-units-and-reading-link-errors/) · 전방 선언 + 포인터 = [25번 형제](../25-incomplete-types-and-opaque-struct/)(불투명 구조체).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s44h.h` · `s44a.c` · `s44b.c` | ★★★ **헤더 배치 격자 70칸 + `nm` 28** · 링크 문구 3 · `nm` 2 | 컴파일 140 + 링크 70 |
| `s44s.h` · `s44sa.c` · `s44sb.c` | ★★ `static` 사본 | 실행 1 · `nm` 1 |
| `s44i.h` · `s44u.c` | ★★ 쓰지 않은 헤더 함수 | 진단 2 |
| `s44n.h` · `s44g.h` · `s44p.h` · `s44m.c` | ★★★ **guard/pragma 격자 54칸** · `-H` 3 · 진단 5 | 컴파일 54 + 8 |
| `s44ea.h` · `s44eb.h` · `s44e1.c` · `s44e2.c` · `s44fa.h` · `s44fb.h` · `s44f2.c` | ★★ 순환 include · 전방 선언 | 진단 3 · 전처리 2 · 실행 1 |
| `s44t.c` | ★★ `-H` · `-MMD` · `-MD` | 3 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **4번의 `#pragma once` 사본 칸** — gcc 13 · 12 · clang 18.
- ★★ **1번의 `-fcommon` 열** · **10번의 C23 미구현** · **6번의 `-H` 출력 모양.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `static const` 행 · 헤더를 고치고 한쪽 `.o` 만 다시 만든 빌드 · 내용은 다르고 mtime 만 같은 사본 · gcc 문서의 `#pragma once` 설명.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번 격자**와 **10번의 C23 태그 재정의** — 컴파일러가 C23 을 따라가면 guard 없는 헤더 행이 바뀔 수 있다.
