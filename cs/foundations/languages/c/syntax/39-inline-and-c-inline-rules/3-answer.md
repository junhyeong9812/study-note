# c/syntax/39 — `inline` 과 C 의 인라인 규칙: 「**C 의 `inline` 은 「펼쳐라」가 아니라 「이 정의는 외부 정의가 아니다」다 — 그래서 헤더에 두면 링크가 판을 탄다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **g++ 13.3.0** · **clang++ 18.1.3** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 `s39.h` · `s39a.c`\~`s39f.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **본체 창은 링크 격자** — 지정자 4 × 판 3 × 컴파일러 2 × 최적화 2.
> ★★ **흔들리는 칸** — 없다(블록에 싣는 링크 문구는 오브젝트 이름을 고정해 임시 파일 이름을 뺐다). 정규화 규칙은 기본 넷뿐이다.

## 이 파일이 다시 싣는 소스

★ 9번은 질문 파일에 없는 `s39f.c` 를 쓴다.

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

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 링크 격자(C99) — **`inline` 만은 `-O0` 실패 · `-O2` 성공 · 헤더의 `extern inline` 은 전부 `multiple definition` · `static inline` 과 DECL 은 전부 성공 · gcc/clang 0 / 24** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`inline` 만** — 두 파일의 정의가 **둘 다 인라인 정의**라 **외부 정의가 없다.** `-O0` 은 호출을 펼치지 않아 링커가 외부 정의를 찾다 **두 파일 모두에서** `undefined reference`. `-O2` 는 호출을 펼쳐 **심볼이 필요 없어졌을 뿐**이다(3번의 「(없음)」).
- ★★★ **헤더의 `extern inline`** — `extern` 이 붙은 선언은 그 번역 단위의 정의를 **외부 정의로** 만든다. 헤더를 include 한 **두 파일 모두** → 외부 정의 둘 → `multiple definition`(최적화와 무관).
- ★★ **`static inline`** — 내부 링크 사본 둘. 링커에 이름이 안 간다.
- ★★★ **DECL** — `s39a.c` 만 외부 정의 → **정확히 하나** → 성공, 값 `twice(1) = 2 · from_a(20) = 40`.
- ★★ **gcc 와 clang 은 한 칸도 안 갈렸다**(0 / 24) — 격자의 끝 줄은 48 번의 빌드에서 나온 **`warning:` 합계**도 센다.

### 2. gnu89 — **`inline` 만은 전부 `multiple definition` · `extern inline` 은 `-O0` 실패 · `-O2` 성공 · 갈린 칸 12 / 16(안 갈린 넷은 `static inline`) · `-std=gnu89` 는 같다** ★★★

**출력**

```text
===== gcc -std=c17 -fgnu89-inline -Wall -Wextra -O0 -c s39a.c && gcc -std=c17 -fgnu89-inline -Wall -Wextra -O0 -c s39b.c && gcc s39a.o s39b.o -o x (cc exit=1) =====
/usr/bin/ld: s39b.o: in function `twice':
s39b.c:(.text+0x0): multiple definition of `twice'; s39a.o:s39a.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

(격자는 1번의 블록 — 둘째·셋째 덩어리)

**왜 그런가**

- ★★★ **gnu89 의 `inline` 은 외부 정의를 만든다** — 두 파일이 둘 다 만들어 `multiple definition`. DECL 줄도 같은 이유로 깨진다.
- ★★★ **gnu89 의 `extern inline` 은 「펼칠 때만 쓰고 정의를 만들지 마라」** — C99 의 `inline` 만과 **같은 증상**(`-O0` 실패 · `-O2` 성공).
- ★★ **`static inline` 네 칸만 안 갈렸다** — 그래서 12 / 16.
- ★ **`-std=gnu89` 는 인라인 의미까지 gnu89** — 둘째·셋째 덩어리가 한 글자도 같다.

### 3. `nm` — **C99: `inline` 은 `U U`/(없음) · `static` 은 `t t`/(없음) · `extern` 은 `T T T T` · DECL 은 `T U`/`T (없음)` · gnu89 는 `inline` 과 `extern inline` 이 맞바뀐다** ★★

**출력**

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

**왜 그런가**

- ★★ **`U` 는 「정의가 없어 밖에서 찾는다」** — C99 `inline` 만의 `-O0` 두 칸이 1번의 `undefined reference` 두 줄이다.
- ★★ **`T` 가 두 파일에 있으면 충돌** — 헤더 `extern inline`(C99) · `inline`(gnu89).
- ★★ **`-O2` 의 「(없음)」은 1번 `KW=inline` 줄의 `-O2` 성공을 설명한다** — 정의가 생긴 것이 아니라 **필요가 사라졌다.** 주소를 쓰거나 펼치지 못하는 호출이 하나만 있어도 다시 깨진다.

### 4. C++ — **16칸 전부 링크 성공 · `nm -C` 는 두 파일 다 `W twice(int)`** ★★

**출력**

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

**왜 그런가**

- ★★ **C++ 의 `inline` 함수는 「번역 단위마다 같은 정의가 있어도 된다」** 는 약속이고, 구현은 **약한 심볼(`W`)** 로 내보내 링커가 하나로 합친다. 1번에서 깨졌던 두 줄(`inline` 만 `-O0` · 헤더 `extern inline`)이 여기서는 다 된다.
- ★ C++ 에서 `extern inline` 은 `inline` 과 같은 뜻이 된다(외부 링크 `inline`). **C 와 달리 `extern` 이 「외부 정의를 만든다」는 뜻을 싣지 않는다.**

### 5. `&twice` — **C `static inline` 0 · C DECL 1 · C++ `static inline` 0 · C++ `inline` 1 · 최적화 무관** ★★

**출력**

```text
===== 두 번역 단위에서 &twice — 언어 2 × KW 2 × 최적화 2 (s39c.c + s39d.c · gcc / g++) (exit=0) =====
언어 · KW                 	-O0	-O2
C static inline           	두 번역 단위의 &twice 가 같은가 = 0	두 번역 단위의 &twice 가 같은가 = 0
C inline + DECL           	두 번역 단위의 &twice 가 같은가 = 1	두 번역 단위의 &twice 가 같은가 = 1
C++ static inline         	두 번역 단위의 &twice 가 같은가 = 0	두 번역 단위의 &twice 가 같은가 = 0
C++ inline                	두 번역 단위의 &twice 가 같은가 = 1	두 번역 단위의 &twice 가 같은가 = 1
```

**왜 그런가**

- ★★ **`static inline` 은 번역 단위마다 다른 함수**다 — 주소가 다르다(두 언어 다).
- ★★ **외부 링크 인라인 함수는 주소가 하나** — N3220 각주 「인라인 정의가 몇 개이든 함수의 주소는 하나」. C 에서는 그것이 **외부 정의의 주소**, C++ 에서는 링커가 합친 하나다.
- ★ **주소를 쓰면 `-O2` 에서도 정의가 남는다** — 그래서 줄이 안 바뀐다.

### 6. 제약 위반 — **gcc 경고 둘 · clang 경고 둘 · 둘 다 `cc exit=0` · `-pedantic-errors` 에서 gcc 는 두 줄 다 에러, clang 은 `hidden` 줄만 에러** ★★

**출력**

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

**왜 그런가**

- ★★ **외부 링크 인라인 정의에는 제약이 둘** — 수정 가능한 정적·스레드 저장 기간 객체를 **정의하면 안 되고**, 내부 링크 식별자를 **참조하면 안 된다.** `calls` 가 앞의 것, `hidden` 이 뒤의 것이다.
- ★★★ **제약 위반인데 기본은 둘 다 `cc exit=0`** — 「종료 코드 0인데 ill-formed」.
- ★★ **`-pedantic-errors` 에서 clang 은 `-Wstatic-in-inline` 만 에러로 올리고 `-Wstatic-local-in-inline` 은 경고로 남긴다** — 두 컴파일러가 **어느 진단을 표준 위반 묶음으로 보나**가 다르다(clang 의 `calls` 줄이 경고로 남은 것은 **표준이 그것을 허락한다는 뜻이 아니다**).

### 7. `-O0` 의 `call` — **표준 위반이 아니다 · 효과의 정도는 구현 정의 · 속도는 적을 수 없다** ★★

**출력**

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

**왜 그런가**

- ★★ **표준은 `inline` 을 「호출을 가능한 한 빠르게 하라는 제안」으로 적고, 「그 제안이 얼마나 먹히는지는 구현 정의」라고 한다** — 각주는 「**한 번도 펼치지 않는 구현**」도 예로 든다. `-O0` 의 `call twice 1 번`(세 지정자 · 두 컴파일러)은 적법하다.
- ★★ **`-O1`·`-O2` 에서 `call` 이 사라진 것은 최적화기의 일**이다 — 격자의 넷째 열(**지정자 없음** · `-DKW=`)이 **다른 세 열과 한 글자도 같다.** 이 판에서 펼침은 `inline` 이 아니라 **최적화 수준**이 정했다.
- ★★★ **「빠르다」는 적을 수 없다** — 이 편은 **명령 수**를 셌지 **시간**을 재지 않았다.

### 8. `extern inline` 선언의 자리 — **한 `.c` 에만 — 외부 정의는 하나여야 한다** ★★

**왜 그런가**

- ★★ **그 한 줄이 「이 번역 단위의 정의를 외부 정의로」** 만든다. 헤더에 두면 include 한 **모든 파일이** 외부 정의를 가져 1번 셋째 줄(`multiple definition`)과 같아진다.
- ★ **표준 예제 1** — `fahr` 는 `extern double fahr(double);` 가 있어 **외부 정의**, `cels` 는 없어서 **인라인 정의**(다른 번역 단위에 외부 정의가 있어야 한다). 이 편의 `s39a.c`(DECL)가 `fahr`, `s39b.c` 가 `cels` 모양이다.

### 9. `static inline` 의 대가 — **주소가 파일마다 다름 · 정적 변수가 파일마다 따로 · 쓰는 파일마다 사본** ★★

**출력**

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

**왜 그런가**

- ★★ **주소** — 5번의 `= 0`. **정적 변수** — 파일마다 따로라 **「전체 호출 횟수」 같은 것을 셀 수 없다.** **코드 크기** — 펼치지 않은 판에서 사본이 파일 수만큼(3번의 `-O0` `t t`). ★ 크기 자체는 재지 않았다.
- ★★ **`s39f.c`** — `count_calls` 에 `extern inline` 선언을 더해 **외부 정의**로 만들었고(외부 정의에는 제약이 없다), `read_hidden` 은 **`static inline`** 으로 바꿨다. gcc 는 0건.
- ★ **clang 의 남은 경고는 판정이 아니다** — 「파일마다 다를 수 있다」는 조심의 말이고, 이 판에는 외부 정의가 **하나**다. 종료 코드 `0`.

### 10. C 와 C++ 의 `inline` — **C: 인라인 정의는 외부 정의가 아니다(외부 정의는 따로 하나) · C++: 같은 정의가 여럿 있어도 된다(링커가 합친다)** ★★

**왜 그런가**

- ★★ **C** — 여러 번역 단위의 인라인 정의는 **각자 그 파일 전용**이고, 파일을 넘는 호출은 **단 하나의 외부 정의**로 간다. 그래서 1번의 `inline` 만이 깨졌다.
- ★★ **C++** — `inline` 이 붙은 정의는 **모든 번역 단위에 같은 것이 있어도 되고** 하나로 취급된다(ODR 의 `inline` 예외). 4번의 `W`.
- ★ **C++17 `inline` 변수** — 29편 (9)에서 g++ 는 **`u`**, clang++ 는 **`V`** 로 보였다.

### 11. 다섯 층 — **표준이 본체 · 펼침은 구현 정의 · gnu89 는 컴파일러 구현 · 어느 정의를 쓰나는 미명시** ★★★

**왜 그런가**

- **표준** — 인라인 정의 ≠ 외부 정의 · `extern` 선언이 외부 정의를 만든다 · 외부 정의는 하나 · 주소는 하나 · 제약 둘 · `static inline` 은 내부 링크.
- **구현 정의** — 제안이 얼마나 먹히나(`-O0` 의 `call`).
- **컴파일러 구현** — gnu89 의미 · 제약 위반을 경고로 두는 기본값 · clang 의 `-pedantic-errors` 범위 · C++ 의 `W`.
- **미명시** — 호출이 인라인 정의를 쓰나 외부 정의를 쓰나(★ 던지지 않았다).
- ★★★ **컴파일러는 한 번역 단위만 본다** — 「외부 정의가 없다 / 둘이다」는 **여러 번역 단위를 모은 뒤에야** 드러나므로 링커만 안다. 격자의 끝 줄이 **컴파일·링크 48 번의 `warning:` 합계**다.
- ★★ **「종료 코드 0인데 ill-formed」** — 6번의 두 줄(gcc·clang 기본값).

### 12. 경계 ★

**왜 그런가**

- **한 번역 단위의 세 형태 · 링크 규칙** — [29번 형제](../29-scope-and-linkage-static-extern/)((8)·(9)).
- **헤더 배치** — 목록의 **44번 주제** · **링크 오류 거꾸로 읽기** — 목록의 **45번 주제**.
- ★ 이 주제가 책임지는 것 — ① **지정자별 정의 수와 링크**(격자 · `nm`) ② **판·언어의 뒤집힘**(gnu89 · C++) ③ **`inline` 이 보장하지 않는 것**(펼침 · 주소 · 제약).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s39.h` + `s39a.c` + `s39b.c` | ★★★ **링크 격자 48칸 · 12 / 16 · 0 / 24** · 링크 문구 셋 · 실행 1 | 48 · 4 |
| 같은 셋 | ★★ `nm` 격자 32칸 · C++ 격자 16칸 · `nm -C` | 32 · 16 · 1 |
| `s39a.c` | ★★ 어셈블리 격자 24칸 · `-O0` 몸통 | 24 · 1 |
| `s39c.c` + `s39d.c` | ★★ 주소 격자 8칸 | 8 |
| `s39e.c` · `s39f.c` | ★★ 제약 위반 · `-pedantic-errors` | 진단 6 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★ **7번** — 두 컴파일러가 어느 최적화 수준에서 펼치나.
- ★★ **2번** — gnu89 의미는 GNU 확장이다(clang 도 흉내 낸다).
- ★ **6번의 진단 묶음** · **4번의 `W`**.

**인라인 정의가 외부 정의가 아니라는 것 · `extern` 선언이 외부 정의를 만든다는 것 · 외부 링크 함수의 주소가 하나라는 것 · 두 제약은 구현 의존이 아니다.**\
어느 C 구현에서도 같다(판 안에서).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 미명시 칸(어느 정의를 탔나) · `always_inline`/`noinline` · LTO.
- ★ **재지 않은 것** — **`inline` 의 속도 · 코드 크기**(이 편의 주제가 아니다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **6번** — `-pedantic-errors` 의 범위가 바뀔 수 있다.
- ★ **7번** — `-O1` 의 펼침 여부.
