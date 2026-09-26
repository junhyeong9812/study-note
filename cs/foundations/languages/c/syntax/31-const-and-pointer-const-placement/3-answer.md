# c/syntax/31 — `const` 와 포인터 const 위치: 「**`const` 는 약속이지 보장이 아니다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · g++/clang++ 같은 판 · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s31a.c`\~`s31i2.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **UB 문항(5)은 컴파일러 2 × `-O0`/`-O2` 네 벌**을 돌렸다.
> ★★★ **본체 창은 `-O2` 어셈블리**(4번). ★★ **둘째 본체는 `nm`**(7번). ★ **sanitizer 는 부적용**(`const` 위반은 할당 범위 안의 쓰기다).
> ★★★ **시간은 재지 않았다** — 4번은 **명령 수**다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **이 편에는 없다** — 정규화 규칙을 하나도 안 썼다 | ★★★ **어셈블리 · 종료 코드**(`cc exit` · `run exit=0` \| `139`) |
> | — | ★★ 진단 전문 · `nm` 의 글자와 이름 · 실행 출력 |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 세 가지 선언 — **`p1 -> xyz · p2 -> Abc · p3 -> Abc`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31a.c -o x ; ./x (cc exit=0 · run exit=0) =====
p1 -> xyz · p2 -> Abc · p3 -> Abc
```

**왜 그런가**

- ★★ **읽기** — `p1` 은 「포인터 · char 를 가리키는 · 그 char 가 const」, `p2` 는 「const 인 포인터 · char 를 가리키는」, `p3` 는 「const 인 포인터 · const char 를 가리키는」.
- ★★ **`p1 = buf2` 는 된다**(포인터가 움직임) · **`p2[0] = 'A'` 는 된다**(가리키는 것을 고침).
- ★★ **`p3` 가 `Abc` 를 보는 이유** — `p3` 의 `const` 는 **p3 라는 경로로는 안 고친다**는 것이다. **`p2` 가 같은 메모리를 고쳤고**, `p3` 는 그것을 본다.
- ★ **`char const *p` 는 `p1` 과 같다** — `*` 의 왼쪽에 `const` 가 있다.

### 2. 막히는 대입 넷 — **전부 에러 · `cc exit=1` · clang ③ 문구가 원인을 틀리게 가리킨다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fmax-errors=0 -c s31b.c -o /dev/null (cc exit=1) =====
s31b.c: In function ‘f’:
s31b.c:7:11: error: assignment of read-only location ‘*p1’
    7 |     p1[0] = 'X';                         /* ① 가리키는 것을 바꾼다 */
      |           ^
s31b.c:8:8: error: assignment of read-only variable ‘p2’
    8 |     p2 = buf2;                           /* ② 포인터를 바꾼다 */
      |        ^
s31b.c:9:11: error: assignment of read-only location ‘*p3’
    9 |     p3[0] = 'X';                         /* ③ 가리키는 것을 바꾼다 */
      |           ^
s31b.c:10:8: error: assignment of read-only variable ‘p3’
   10 |     p3 = buf2;                           /* ④ 포인터를 바꾼다 */
      |        ^
s31b.c:4:17: warning: variable ‘p2’ set but not used [-Wunused-but-set-variable]
    4 |     char *const p2 = buf1;
      |                 ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -ferror-limit=0 -c s31b.c -o /dev/null (cc exit=1) =====
s31b.c:7:11: error: read-only variable is not assignable
    7 |     p1[0] = 'X';                         /* ① 가리키는 것을 바꾼다 */
      |     ~~~~~ ^
s31b.c:8:8: error: cannot assign to variable 'p2' with const-qualified type 'char *const'
    8 |     p2 = buf2;                           /* ② 포인터를 바꾼다 */
      |     ~~ ^
s31b.c:4:17: note: variable 'p2' declared const here
    4 |     char *const p2 = buf1;
      |     ~~~~~~~~~~~~^~~~~~~~~
s31b.c:9:11: error: cannot assign to variable 'p3' with const-qualified type 'const char *const'
    9 |     p3[0] = 'X';                         /* ③ 가리키는 것을 바꾼다 */
      |     ~~~~~ ^
s31b.c:5:23: note: variable 'p3' declared const here
    5 |     const char *const p3 = buf1;
      |     ~~~~~~~~~~~~~~~~~~^~~~~~~~~
s31b.c:10:8: error: cannot assign to variable 'p3' with const-qualified type 'const char *const'
   10 |     p3 = buf2;                           /* ④ 포인터를 바꾼다 */
      |     ~~ ^
s31b.c:5:23: note: variable 'p3' declared const here
    5 |     const char *const p3 = buf1;
      |     ~~~~~~~~~~~~~~~~~~^~~~~~~~~
4 errors generated.
```

**왜 그런가**

- ★★ **gcc 는 두 문구로 가른다** — 가리키는 것은 **`read-only location '*p1'`**·**`'*p3'`**, 포인터 자신은 **`read-only variable 'p2'`**·**`'p3'`**. 문구만으로 **어느 `const` 에 걸렸나**가 보인다.
- ★★★ **clang ③은 원인을 틀리게 가리킨다** — `p3[0] = 'X'` 는 **가리키는 `const char`** 에 걸린 것인데, clang 은 **`cannot assign to variable 'p3' with const-qualified type 'const char *const'`** 로 **포인터 변수**를 탓한다. ④와 **한 글자도 같은 문구**다.\
  ★ **근거는 캐럿 자리**(9행 11열 — `=` 앞의 `p3[0]`)와 **`cc exit`** 다.
- ★ **`cc exit=1`**. gcc 의 덤 경고 **`variable 'p2' set but not used`** — `p2 = buf2` 가 에러로 버려져 **쓰인 적이 없는 것**으로 보였다.

### 3. `char **` → `const char **` — **경고 · `cc exit=0` · 실행은 `139`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31c.c -o x (cc exit=0) =====
s31c.c: In function ‘main’:
s31c.c:10:23: warning: passing argument 1 of ‘point_at_readonly’ from incompatible pointer type [-Wincompatible-pointer-types]
   10 |     point_at_readonly(&p);               /* ★ char ** 를 const char ** 자리에 넘긴다 */
      |                       ^~
      |                       |
      |                       char **
s31c.c:3:44: note: expected ‘const char **’ but argument is of type ‘char **’
    3 | static void point_at_readonly(const char **out) {
      |                               ~~~~~~~~~~~~~^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s31c.c -o x (cc exit=0) =====
s31c.c:10:23: warning: passing 'char **' to parameter of type 'const char **' discards qualifiers in nested pointer types [-Wincompatible-pointer-types-discards-qualifiers]
   10 |     point_at_readonly(&p);               /* ★ char ** 를 const char ** 자리에 넘긴다 */
      |                       ^~
s31c.c:3:44: note: passing argument to parameter 'out' here
    3 | static void point_at_readonly(const char **out) {
      |                                            ^
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31c.c -o x ; ./x (cc exit=0 · run exit=139) =====
p -> READ-ONLY
p 는 char * 라 p[0] 에 쓰는 것을 컴파일러가 막지 않는다
```

```text
===== char ** 를 const 가 붙은 두 자리에 — 파일 2 × 컴파일러 2 × 판 3 (exit=0) =====
s31c   gcc    -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   gcc    -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c   gcc    -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   clang  -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c   clang  -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c   clang  -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  gcc    -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  gcc    -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c2  gcc    -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  clang  -std=c17 -pedantic         cc exit=0 · 경고 1 · 에러 0
s31c2  clang  -std=c17 -pedantic-errors  cc exit=1 · 경고 0 · 에러 1
s31c2  clang  -std=c2x -pedantic         cc exit=0 · 경고 1 · 에러 0
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s31cx.cpp -o /dev/null (cc exit=1) =====
s31cx.cpp: In function ‘int main()’:
s31cx.cpp:7:23: error: invalid conversion from ‘char**’ to ‘const char**’ [-fpermissive]
    7 |     point_at_readonly(&p);               // ★ char ** → const char ** — 위험한 쪽
      |                       ^~
      |                       |
      |                       char**
s31cx.cpp:1:44: note:   initializing argument 1 of ‘void point_at_readonly(const char**)’
    1 | static void point_at_readonly(const char **out) { *out = "READ-ONLY"; }
      |                               ~~~~~~~~~~~~~^~~
```

**왜 그런가**

- ★★★ **두 컴파일러 다 경고 · `cc exit=0`** 이다 — 그리고 **`run exit=139`**, 출력은 **두 줄**뿐이다(「안 죽었다」가 안 나온다). 「**종료 코드 0인데 ill-formed**」다.
- ★★★ **왜 막아야 하나** — `point_at_readonly` 는 `*out` 에 **`const char` 의 주소를 넣는다**(정당하다). 그런데 `out` 이 `&p` 라서 그 주소가 **`char *p` 에 들어간다.** 다음 줄 `p[0] = 'X'` 도 `char *` 로 쓰는 것이라 **정당해 보인다.** **두 줄이 각자 정당한데 합치면 `const` 가 새어 나간다** — 그래서 첫 변환을 막는다.
- ★★ **clang 의 `[-Wincompatible-pointer-types-discards-qualifiers]`** — 「중첩된 포인터에서 한정자를 버린다」가 **원인을 정확히 말한다.** gcc 는 `[-Wincompatible-pointer-types]` 로 뭉뚱그린다.
- ★★ **`const char *const *` 도 C 는 경고한다**(`s31c2` 행 — 경고 1 · `exit=0`). **C++ 은 이것을 받는다** — `s31cx.cpp` 의 에러는 **7행(위험한 쪽) 하나**뿐이다.
- ★ **`-std=c2x` 는 결과를 안 바꾸고**(C23 까지 같은 규칙), **`-pedantic-errors` 만 `exit=1`** 로 바꾼다.

### 4. `const int *p` 의 어셈블리 — **`*p` 를 두 번 읽고, `const` 객체 `K` 는 한 번도 안 읽는다** ★★★

**출력**

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s31d.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
twice_read:
	endbr64
	mov	eax, DWORD PTR [rdi]
	mov	DWORD PTR [rsi], 0
	add	eax, DWORD PTR [rdi]
	ret
across_call:
	endbr64
	push	rbp
	push	rbx
	mov	rbx, rdi
	sub	rsp, 8
	mov	ebp, DWORD PTR [rdi]
	call	opaque@PLT
	mov	eax, DWORD PTR [rbx]
	add	rsp, 8
	pop	rbx
	add	eax, ebp
	pop	rbp
	ret
const_object:
	endbr64
	sub	rsp, 8
	call	opaque@PLT
	mov	eax, 10
	add	rsp, 8
	ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s31d.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
twice_read:                             # @twice_read
# %bb.0:
	mov	eax, dword ptr [rdi]
	mov	dword ptr [rsi], 0
	add	eax, dword ptr [rdi]
	ret
.Lfunc_end0:
                                        # -- End function
across_call:                            # @across_call
# %bb.0:
	push	rbp
	push	rbx
	push	rax
	mov	rbx, rdi
	mov	ebp, dword ptr [rdi]
	call	opaque@PLT
	add	ebp, dword ptr [rbx]
	mov	eax, ebp
	add	rsp, 8
	pop	rbx
	pop	rbp
	ret
.Lfunc_end1:
                                        # -- End function
const_object:                           # @const_object
# %bb.0:
	push	rax
	call	opaque@PLT
	mov	eax, 10
	pop	rcx
	ret
.Lfunc_end2:
                                        # -- End function
```

```text
===== const 객체 K — 어셈블리에서 센 줄 수 (컴파일러 2 × 최적화 2) (exit=0) =====
            | const_object 안에서 K 를 메모리로 읽는 명령  | 즉치값 5 또는 10 을 쓰는 명령
gcc -O0     | 0 줄                                         | 2 줄
gcc -O2     | 0 줄                                         | 1 줄
clang -O0   | 0 줄                                         | 2 줄
clang -O2   | 0 줄                                         | 1 줄
```

**왜 그런가**

- ★★★ **`twice_read` 는 `[rdi]` 를 두 번** 읽는다 — `mov eax, [rdi]` · `add eax, [rdi]`. **두 컴파일러가 같은 모양**이다. `*q = 0` 이 **`*p` 를 바꿀 수 있기** 때문이다.
- ★★★ **`across_call` 은 `call opaque` 뒤에 다시 읽는다** — gcc `mov eax, [rbx]` · clang `add ebp, [rbx]`.
- ★★★ **`const_object` 는 `K` 를 0 번** 읽는다 — `mov eax, 10`. 객체 자체가 `const` 라 **바뀌면 UB** 이므로 값을 믿는다.
- ★★ **갈림은 「객체가 `const` 냐」** 다. 포인터의 `const` 는 **읽기 횟수를 하나도 안 줄였다.**
- ★★ **`-O0` 에서도 `K` 는 메모리로 안 읽힌다** — 네 벌 다 0 줄, `-O0` 은 즉치값 `5` 를 두 줄로 쓴다.
- ★ **「`const` 가 빠르다」는 이 결과로 말할 수 없다** — **시간을 재지 않았다.** 말할 수 있는 것은 **명령 수**뿐이다.

### 5. `const` 떼고 쓰기 — **비-`const` 는 합법 `99` · 원래 `const` 는 네 벌이 갈린다** ★★★

**출력**

```text
===== const 를 캐스트로 떼고 쓰기 — 원래 const 가 아닌 것 / 원래 const 인 자동 객체 (exit=0) =====
--- gcc -O0
plain   = 99
local_c = 99 · 같은 자리를 포인터로 다시 읽으면 = 99
--- gcc -O2
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
--- clang -O0
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
--- clang -O2
plain   = 99
local_c = 1 · 같은 자리를 포인터로 다시 읽으면 = 99
```

```text
===== 원래 const 인 정적 객체에 쓰기 — 컴파일러 2 × 최적화 2 (exit=0) =====
gcc    -O0  run exit=139 | static_c 에 쓴다|
gcc    -O2  run exit=0   | static_c 에 쓴다|static_c = 1|
clang  -O0  run exit=139 | static_c 에 쓴다|
clang  -O2  run exit=0   | static_c 에 쓴다|static_c = 1|
```

**왜 그런가**

- ★★★ **`plain`** — 네 벌 다 **`99`**. **`local_c`** — gcc `-O0` 만 `99`, 나머지 셋은 **`1`**(그런데 `volatile` 로 다시 읽으면 **`99`**). **`static_c`** — `-O0` 두 벌은 **`run exit=139`**, `-O2` 두 벌은 **`exit=0` · `1`**.
- ★★★ **「한 객체가 두 값」은 `local_c` 의 세 칸**이다 — 메모리에는 `99` 가 쓰였는데, 컴파일러는 이름 `local_c` 를 **`1` 로 접어** 두었다. **원래 `const` 인 객체는 안 바뀐다고 믿어도 되기** 때문이다.
- ★★★ **`static_c` 는 최적화 수준이 「죽는다 / 산다」를 뒤집는다** — `-O0` 은 **읽기 전용 구역**에 실제로 써서 죽고, `-O2` 는 **쓰기가 없어진 것처럼** 산다. 둘 다 **이 판의 한 결과**다.
- ★★ **합법은 `plain` 뿐**이다. `local_c`·`static_c` 는 **원래 `const` 인 객체를 고친 UB** 다.
- ★ **`sneaky` 는 알 수 없다** — 받은 것은 `const int *` 하나뿐이고, **원래 객체가 `const` 인지는 타입에 안 남는다.**

### 6. 문자열 리터럴 — **C 는 `char *` 로 감쇠하고 경고 0 · 쓰면 `139` · C++ 은 `const char[4]`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s31g.c -o x ; ./x (cc exit=0 · run exit=139) =====
"abc" 가 감쇠한 타입 = char *
s[0] 에 쓴다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wwrite-strings -c s31g.c -o /dev/null (cc exit=0) =====
s31g.c: In function ‘main’:
s31g.c:8:15: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
    8 |     char *s = "abc";                     /* C 에서는 경고 없이 통과한다 */
      |               ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wwrite-strings -c s31g.c -o /dev/null (cc exit=0) =====
s31g.c:8:11: warning: initializing 'char *' with an expression of type 'const char[4]' discards qualifiers [-Wincompatible-pointer-types-discards-qualifiers]
    8 |     char *s = "abc";                     /* C 에서는 경고 없이 통과한다 */
      |           ^   ~~~~~
1 warning generated.
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
"abc" 의 타입이 const char[4] 인가 = 1
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x (cc exit=0) =====
s31g.cpp: In function ‘int main()’:
s31g.cpp:7:15: warning: ISO C++ forbids converting a string constant to ‘char*’ [-Wwrite-strings]
    7 |     char *s = "abc";                     // ★ C++ 에서는 이 줄이 걸린다
      |               ^~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic s31g.cpp -o x (cc exit=0) =====
s31g.cpp:7:15: warning: ISO C++11 does not allow conversion from string literal to 'char *' [-Wwritable-strings]
    7 |     char *s = "abc";                     // ★ C++ 에서는 이 줄이 걸린다
      |               ^
1 warning generated.
```

```text
===== C++ 에서 -pedantic-errors 로 올리면 (exit=0) =====
g++      -pedantic-errors  cc exit=1
clang++  -pedantic-errors  cc exit=1
```

**왜 그런가**

- ★★ **C 의 `"abc"` 는 `char[4]`** — `_Generic` 이 **`char *`** 라고 답한다. `char *s = "abc";` 에 **경고가 없다.**
- ★★★ **`run exit=139`** — 타입은 `char[]` 인데 **자리는 읽기 전용**이다. 고치는 것은 **UB** 다.
- ★★ **`-Wwrite-strings`** — 두 컴파일러가 경고한다. **clang 은 리터럴을 `'const char[4]'` 라고 부른다** — 이 옵션이 리터럴을 **`const` 로 취급하게** 바꾼 것이 문구에 드러난다.
- ★★ **C++ 은 `const char[4]`**(`is_same_v` = `1`). `char *s = "abc";` 는 **기본 경고**(g++ `[-Wwrite-strings]` · clang++ `[-Wwritable-strings]`) · `cc exit=0` — **`-pedantic-errors` 면 둘 다 `exit=1`**. C++ 판의 「종료 코드 0인데 ill-formed」다.

### 7. 파일 스코프 `const` — **C `R K`(외부) · C++ `r _ZL1K`(내부)** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s31h.c -o h.o && nm h.o (cc exit=0) =====
0000000000000000 R K
0000000000000000 T addr_of_k
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s31h.cpp -o h.o && nm h.o (cc exit=0) =====
0000000000000004 R K2
0000000000000011 T _Z10addr_of_k2v
0000000000000000 T _Z9addr_of_kv
0000000000000000 r _ZL1K
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s31h.cpp -o h.o && nm h.o (cc exit=0) =====
0000000000000000 R K2
0000000000000010 T _Z10addr_of_k2v
0000000000000000 T _Z9addr_of_kv
0000000000000004 r _ZL1K
```

```text
===== 두 번역 단위에 같은 const int K = 5; — C 둘 · C++ 둘 (exit=0) =====
C   gcc      link exit=1 | -
C   clang    link exit=1 | -
C++ g++      link exit=0 | K = 5 · 1 쪽 K = 5
C++ clang++  link exit=0 | K = 5 · 1 쪽 K = 5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s31i1.c s31i2.c && gcc s31i1.o s31i2.o -o x (cc exit=1) =====
/usr/bin/ld: s31i2.o:(.rodata+0x0): multiple definition of `K'; s31i1.o:(.rodata+0x0): first defined here
collect2: error: ld returned 1 exit status
```

**왜 그런가**

- ★★★ **C 는 `R K`** — 대문자, 외부 링크, `.rodata`. **C++ 은 `r _ZL1K`** — 소문자, 내부 링크. **소스가 같은데 링크가 반대**다.
- ★★ **C++ 의 `extern const int K2 = 6;` 은 `R K2`** — 외부 링크로 돌아오고 이름도 안 뭉개진다.
- ★★★ **두 파일이면 C 는 두 컴파일러 다 링크 `exit=1`**(`multiple definition of 'K'`), **C++ 은 둘 다 통과** — 각 파일의 `K` 가 남남이다.
- ★★ **C 헤더의 상수** — `static const int K = 5;` · `enum { K = 5 };` · `#define K 5`.
- ★ **`_ZL`** 의 `L` 이 C++ 이름 뭉개기에서 **내부 링크(local)** 표시다.

### 8. `const` 의 약속 — **「이 경로로 안 고친다」뿐** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s31d2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read(&x, &y) = 14   (p 와 q 가 다른 곳)
twice_read(&x, &x) = 7   (p 와 q 가 같은 곳 — const 인데 값이 바뀌었다)
```

**왜 그런가**

- ★★★ **`const int *p` 가 약속하는 것** — 「**나는 `p` 를 통해 그 `int` 를 고치지 않겠다**」.
- ★★★ **「안 바뀐다」가 아닌 증거** — `twice_read(&x, &x) = 7`. `a = 7` 을 읽고, `*q = 0` 이 **같은 `x`** 를 0 으로 만들고, `b = *p` 는 **0** 이다. `p` 는 `const` 인데 `*p` 가 **바뀌었다** — 그리고 이것은 **UB 가 아니다**(비-`const` 객체를 다른 경로로 고친 것).
- ★★ **겹치지 않는다는 약속은 `restrict`** 다([목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/)).
- ★ **「느리다」는 재지 않은 주장**이다 — 이 편은 명령 수만 셌고, 두 번 읽기는 **옳은 번역**이다.

### 9. 다섯 층 — **표준이 본체 · UB 가 둘째 · 조건부 표준·미명시는 비었다(안 던진 것 포함)** ★★★

**왜 그런가**

- **표준** — `const` 의 위치 · 막히는 대입 넷 · `char **` 변환 규칙(두 가지) · **비-`const` 객체에서 떼고 쓰기 합법** · 리터럴 타입 `char[N]` · 파일 스코프 `const` 의 외부 링크 · 에일리어싱 때문의 재읽기.
- **조건부 표준** — ★ **정말 빈 칸**이다. 이 편의 규칙에 조건이 붙는 것이 없다.
- **구현 정의** — 읽기 전용 구역에 두는 것(그래서 `139`) · 진단 문구 · 제약 위반을 **경고로 낼지 에러로 낼지**.
- **미명시** — ★ **안 던진 칸**이다. 같은 리터럴 둘이 한 배열을 쓰는지는 미명시지만 **던지지 않았다.**
- **UB** — 원래 `const` 객체를 고치기 · 리터럴을 고치기.
- ★★★ **「종료 코드 0인데 ill-formed」 셋** — ① C `char **` → `const char **` ② C `char **` → `const char *const *` ③ C++ `char *s = "abc";`. 셋 다 **`-pedantic-errors` 라야 `exit=1`**.
- ★★ **침묵** — 표준: 제약 위반이 `exit=0` · 구현 정의: clang ③ 문구가 원인을 틀림 · UB: 캐스트로 뗀 쓰기에 경고 0건 · 리터럴 쓰기에 경고 0건.
- ★ **sanitizer 부적용** — 이 편의 위반은 전부 **할당된 범위 안의 쓰기**라 ASan 이 볼 것이 없고, UBSan 에 `const` 검사가 없다. 「안 쟀다」가 아니라 **「잴 것이 없다」**.

### 10. `const` 와 `volatile` ★

**왜 그런가**

- ★ `volatile` 은 「**접근할 때마다 실제로 메모리에 간다**」를 약속한다 — 읽기를 접거나 합치지 말라는 것. [32번 형제](../32-what-volatile-actually-guarantees/)가 정본이다.
- ★ **`const volatile`** — 「**내가 안 고치지만 바깥이 바꾸는 것**」. 예: **읽기 전용 장치 레지스터**(실시간 시계).\
  ★ 5번에서 `*(const volatile int *)&local_c` 로 **메모리를 다시 읽은 것**이 바로 이 짝을 쓴 것이다.

### 11. 경계 ★

**왜 그런가**

- **선언 읽기** — [01번 형제](../01-declaration-syntax-and-reading/) · **포인터** — [14번 형제](../14-pointers-address-dereference-and-pointer-types/) · **리터럴의 저장 기간** — [20번 형제](../20-null-terminated-strings-and-string-literals/).
- **`restrict`** — [목록의 **33번 주제**](../33-restrict-and-the-aliasing-contract/) · **엄격한 앨리어싱** — 목록의 **55번 주제**.
- ★ C++ 대비 — [C++ 10 — `const` 정확성](../../../cpp/syntax/10-const-correctness/).
- ★ 이 주제가 책임지는 것 — ① **`const` 위치 읽기** ② **`const` 가 약속하지 않는 것**(재읽기 · 캐스트 · 리터럴) ③ **C 와 C++ 이 갈리는 셋**.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s31a.c` | 되는 대입 두 가지 · `p3` 가 `Abc` | gcc 1 |
| `s31b.c` | 에러 4건 · `cc exit=1` · ★ clang ③ 문구 | gcc 1 · clang 1 |
| `s31c.c`·`s31c2.c`·`s31cx.cpp` | ★★★ **경고 · `cc exit=0` · `run exit=139`** · 안전한 쪽도 C 는 경고 · C++ 은 위험한 쪽만 에러 | 격자 12칸 · 진단 3 · 실행 1 · g++ 1 · clang++ 1 |
| `s31d.c`·`s31d2.c` | ★★★ **`[rdi]` 두 번** · `call` 뒤 재읽기 · **`K` 0 번**(네 벌) · `twice_read(&x,&x) = 7` | 어셈블리 `-O2` 2 · `-O0` 1 · 격자 4 · 실행 1 |
| `s31e.c`·`s31f.c` | ★★★ `plain 99` · `local_c` **1 / 메모리 99** · `static_c` **`-O0` 139 · `-O2` 1** | 4벌 × 2 |
| `s31g.c`·`s31g.cpp` | C `char *` · `139` · `-Wwrite-strings` · C++ `const char[4]` · `-pedantic-errors` `exit=1` | 실행 2 · 진단 4 · 격자 2 |
| `s31h.c`·`s31h.cpp`·`s31i*.c`·`s31i*.cpp` | ★★ C `R K` · C++ `r _ZL1K` · `R K2` · 두 파일 링크 C 실패 · C++ 통과 | `nm` 4 · 링크 격자 4 · 진단 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py` 로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **5번 격자 전부** — UB 다. 결론은 「**네 벌이 갈린다」와 「최적화가 죽고 사는 것을 뒤집는다**」이지 어느 숫자가 아니다.
- ★★ **4번 어셈블리** — 컴파일러의 선택이다. **재읽기 자체는 표준이 요구하는 결과**(에일리어싱)이고, **명령의 모양**이 구현이다.
- ★★ **제약 위반을 경고로 내는 것**(3번) — 컴파일러의 선택이다.
- ★ **읽기 전용 구역**(`139`) · 진단 문구 · clang ③ 문구.

**`const` 의 위치와 뜻 · 막히는 대입 · `char **` 변환 규칙 · 비-`const` 객체에서 떼고 쓰기가 합법인 것 · 원래 `const` 객체와 리터럴을 고치는 것이 UB 인 것 · C 의 파일 스코프 `const` 가 외부 링크인 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `restrict` 로 `twice_read` 가 바뀌는지 · C23 `constexpr` · `const` 멤버와 구조체 대입 · 같은 리터럴 둘의 주소 · `-O1`·`-O3`.
- ★ **못 잰 것** — **gcc 의 더 새 판에서 3번 경고의 기본값이 바뀌었나.** 이 머신에 gcc 12·13 만 있다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3번 격자** — 제약 위반을 **에러로 올리는 판**이 나오면 `cc exit` 가 바뀐다.
- ★★ **5번 격자** · **4번 어셈블리**.
- ★ **2번 clang ③ 문구** — 고쳐질 수 있다.
- **`const` 의 규칙은 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
