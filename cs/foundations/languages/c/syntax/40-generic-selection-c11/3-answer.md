# c/syntax/40 — `_Generic` 타입 제네릭 선택 (C11): 「**`_Generic` 은 식을 평가하지 않고 타입만 본다 — 그 타입은 한정자를 벗고 배열을 포인터로 바꾼 뒤의 것이다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** · **clang 18.1.3** · **g++ 13.3.0** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s40a.c`\~`s40e.c` · `s40d2.c` · `s40x.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다.\
> ★★★ **본체 창은 선택 격자** — 인자 14 × 컴파일러 3 × 판 2.
> ★★ **흔들리는 칸** — 없다. 정규화 규칙은 기본 넷뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 선택 격자 — **`ci` 는 `int` · `a` 는 `int *` · `ca` 는 `const int *` · `'a'` 는 `int` · `c` 는 `char` · `1.0f` 는 `default` · 갈린 칸 0 / 70 · 경고는 gcc 0 · clang 14** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40a.c -o x ; ./x (cc exit=0 · run exit=0) =====
c         	char
'a'       	int
s         	short
ci        	int
a         	int *
&a        	int (*)[3]
ca        	const int *
pc        	char *
pcc       	const char *
"abc"     	char *
+c        	int
c + c     	int
(char)1   	char
1.0f      	default
```

```text
===== 선택 격자 — 인자 14 × 컴파일러 3 × 판 2 (-Wall -Wextra -pedantic) (exit=0) =====
인자      	gcc c11	gcc c17	gcc-12 c11	gcc-12 c17	clang c11	clang c17
c         	char	char	char	char	char	char
'a'       	int	int	int	int	int	int
s         	short	short	short	short	short	short
ci        	int	int	int	int	int	int
a         	int *	int *	int *	int *	int *	int *
&a        	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]	int (*)[3]
ca        	const int *	const int *	const int *	const int *	const int *	const int *
pc        	char *	char *	char *	char *	char *	char *
pcc       	const char *	const char *	const char *	const char *	const char *	const char *
"abc"     	char *	char *	char *	char *	char *	char *
+c        	int	int	int	int	int	int
c + c     	int	int	int	int	int	int
(char)1   	char	char	char	char	char	char
1.0f      	default	default	default	default	default	default
경고	0	0	0	0	14	14
gcc c11 칸과 갈린 칸 0 / 70
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40a.c -o /dev/null | sed -n '1,4p;$p' (cc exit=0) =====
s40a.c:22:5: warning: due to lvalue conversion of the controlling expression, association of type 'const int' will never be selected because it is qualified [-Wunreachable-code-generic-assoc]
   22 |     P(c);  P('a');  P(s);  P(ci);  P(a);  P(&a);  P(ca);
      |     ^
s40a.c:12:40: note: expanded from macro 'P'
14 warnings generated.
```

**왜 그런가**

- ★★★ **제어식의 타입은 lvalue 변환 · 배열→포인터 · 함수→포인터 뒤의 것** — `ci` 는 한정자가 떨어져 `int`, `a` 는 `int *`, `ca` 는 `const int *`(한정자가 **가리키는 쪽**으로 옮겨가 남는다), `&a` 는 원래 포인터 `int (*)[3]`.
- ★★★ **문자 상수는 C 에서 `int`** · **`char` 변수는 그대로 `char`** — 제어식은 평가되지 않으니 **정수 승격도 없다.** `+c`·`c + c` 는 **연산이 승격을 일으켜** `int`. `(char)1` 은 캐스트의 결과 타입 `char`.
- ★★ **`"abc"` 는 `char[4]` → `char *`** · `pcc` 는 `const char *` · `pc` 는 `char *`.
- ★★ **`1.0f` 는 `default`** — `float:` 칸이 없고, `double:` 칸으로 **변환되어 가지 않는다.**
- ★★★ **여섯 빌드가 70 칸 전부 같다** — 규칙이 전부 표준 문장이라서다. **경고만** clang 14(`P` 한 번마다 `-Wunreachable-code-generic-assoc`) · gcc 두 판 0.

### 2. 맞는 분기 없음 — **두 컴파일러 에러 · `cc exit=1` · `float` 은 `double` 로 안 간다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40b.c -o /dev/null (cc exit=1) =====
s40b.c: In function ‘pick’:
s40b.c:2:21: error: ‘_Generic’ selector of type ‘float’ is not compatible with any association
    2 |     return _Generic(f, int: 1, double: 2);
      |                     ^
s40b.c:3:1: warning: control reaches end of non-void function [-Wreturn-type]
    3 | }
      | ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40b.c -o /dev/null (cc exit=1) =====
s40b.c:2:21: error: controlling expression type 'float' not compatible with any generic association type
    2 |     return _Generic(f, int: 1, double: 2);
      |                     ^
1 error generated.
```

**왜 그런가**

- ★★ **`default` 가 없으면 제어식의 타입이 목록의 정확히 하나와 호환되어야 한다**(제약). `float` 은 `int` 와도 `double` 과도 **호환 타입이 아니다** — 변환 가능성은 따지지 않는다.
- ★ gcc 의 `control reaches end of non-void function` 은 **선택이 실패한 여파**다.

### 3. 부작용 — **`r1 = 10 · i = 0 · calls = 0` / `r2 = 20 · calls = 0` · clang 만 `-Wunevaluated-expression`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40c.c -o x ; ./x (cc exit=0 · run exit=0) =====
r1 = 10 · i = 0 · calls = 0
r2 = 20 · calls = 0
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40c.c -o /dev/null (cc exit=0) =====
s40c.c:8:24: warning: expression with side effects has no effect in an unevaluated context [-Wunevaluated-expression]
    8 |     int r1 = _Generic(i++, int: 10, default: bump());
      |                        ^
1 warning generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40c.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★ **제어식은 평가되지 않는다** — `i++` 는 **타입(`int`)만** 주고 증가하지 않았다.
- ★★ **고르지 않은 연관의 식도 평가되지 않는다** — `bump()` 는 두 선택 어디서도 안 불렸다(`calls = 0`).
- ★ **gcc 는 0건** · clang 은 「부작용이 있는 식이 평가되지 않는 문맥에 있다」.

### 4. `ABS` — **그냥 빌드는 `3 4 2.5` · `short` 와 `struct money` 는 둘 다 「어느 연관과도 호환 안 됨」 에러 · gcc 는 매크로 본문(5행)을, clang 은 부른 자리(13·17행)를 먼저 짚는다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40d.c -o x ; ./x (cc exit=0 · run exit=0) =====
3 4 2.5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DUSE_SHORT -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c: In function ‘main’:
s40d.c:5:25: error: ‘_Generic’ selector of type ‘short int’ is not compatible with any association
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^
s40d.c:13:20: note: in expansion of macro ‘ABS’
   13 |     printf("%d\n", ABS(sh));
      |                    ^~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -DUSE_SHORT -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c:13:20: error: controlling expression type 'short' not compatible with any generic association type
   13 |     printf("%d\n", ABS(sh));
      |                    ^~~~~~~
s40d.c:5:25: note: expanded from macro 'ABS'
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^~~
1 error generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -DUSE_MONEY -c s40d.c -o /dev/null (cc exit=1) =====
s40d.c: In function ‘main’:
s40d.c:5:25: error: ‘_Generic’ selector of type ‘struct money’ is not compatible with any association
    5 | #define ABS(x) _Generic((x), int: abs, long: labs, double: fabs)(x)
      |                         ^
s40d.c:17:21: note: in expansion of macro ‘ABS’
   17 |     printf("%ld\n", ABS(m).cents);
      |                     ^~~
```

**왜 그런가**

- ★★ **목록은 `int`·`long`·`double` 로 닫혀 있다** — `short` 도, 사용자 타입도 **매크로 본문을 고치지 않으면** 받을 수 없다.
- ★★ **`short` 는 승격되지 않는다** — 1번의 `s` 칸이 `short` 였던 것과 같은 규칙.
- ★ **짚는 자리의 차이는 진단 구현**이다 — 둘 다 다른 쪽을 `note:` 로 보인다.

### 5. 인자 둘 — **컴파일 안 된다 · `ABS(q)` 에서 `too few arguments`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s40d2.c -o /dev/null (cc exit=1) =====
s40d2.c: In function ‘main’:
s40d2.c:7:16: error: too few arguments to function ‘scaled_abs’
    7 | #define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)
      |                ^~~~~~~~
s40d2.c:12:21: note: in expansion of macro ‘ABS’
   12 |     printf("%ld\n", ABS(q));
      |                     ^~~
s40d2.c:5:6: note: declared here
    5 | long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }
      |      ^~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s40d2.c -o /dev/null (cc exit=1) =====
s40d2.c:12:21: error: too few arguments to function call, expected 2, have 1
   12 |     printf("%ld\n", ABS(q));
      |                     ^~~~~~
s40d2.c:7:80: note: expanded from macro 'ABS'
    7 | #define ABS(x) _Generic((x), int: abs, long: labs, struct scaled: scaled_abs)(x)
      |                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  ^
s40d2.c:5:6: note: 'scaled_abs' declared here
    5 | long scaled_abs(struct scaled s, int unit) { return labs(s.v) / unit; }
      |      ^          ~~~~~~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

**왜 그런가**

- ★★ **매크로는 고른 함수를 `(x)` 하나로 부른다** — 호출의 모양이 **매크로 한 곳에 고정**이다. 인자가 둘인 `scaled_abs` 는 `struct scaled` 를 넣은 호출에서만 골라지고, 거기서 인자가 모자란다.
- ★ **`ABS(-3)` 은 `abs` 를 골랐고 `scaled_abs` 는 고르지 않았다** — 고르지 않은 연관은 평가되지 않으니 에러가 없다(3번의 규칙).

### 6. `<tgmath.h>` — **`float` · `double` · `long double`(두 컴파일러 같다) · `_Generic` 은 3 번(전부 내 `NAME`) · gcc 는 `__builtin_tgmath`, clang 은 `__tg_sqrt`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s40e.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
sqrt(f)    -> float
sqrt(n)    -> double
sqrt(2.0L) -> long double
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s40e.c -o x -lm ; ./x (cc exit=0 · run exit=0) =====
sqrt(f)    -> float
sqrt(n)    -> double
sqrt(2.0L) -> long double
```

```text
===== gcc -std=c17 -E s40e.c | grep -oE '__builtin_tgmath|__tg_sqrt|_Generic' | sort | uniq -c (cc exit=0) =====
      3 _Generic
      3 __builtin_tgmath
```

```text
===== clang -std=c17 -E s40e.c | grep -oE '__builtin_tgmath|__tg_sqrt|_Generic' | sort | uniq -c (cc exit=0) =====
      3 _Generic
      9 __tg_sqrt
```

```text
===== for f in /usr/include/tgmath.h /usr/lib/llvm-18/lib/clang/18/include/tgmath.h; do printf '%s : _Generic %s · __builtin_tgmath %s · overloadable %s\n' $f $(grep -c _Generic $f) $(grep -c __builtin_tgmath $f) $(grep -c overloadable $f); done (exit=0) =====
/usr/include/tgmath.h : _Generic 4 · __builtin_tgmath 24 · overloadable 0
/usr/lib/llvm-18/lib/clang/18/include/tgmath.h : _Generic 0 · __builtin_tgmath 0 · overloadable 3
```

**왜 그런가**

- ★★ **`<tgmath.h>` 의 규칙은 「정수 인자는 `double` 로」** — `sqrt(n)` 이 `double`.
- ★★★ **이 판의 두 구현은 `_Generic` 을 쓰지 않았다** — glibc 판은 **컴파일러 내장 `__builtin_tgmath`**, clang 판은 **`overloadable` 속성을 단 함수 묶음 `__tg_sqrt`**. `_Generic` 3 번은 전부 `s40e.c` 의 `NAME` 매크로다.
- ★ glibc 의 `tgmath.h` 에도 `_Generic` 이 4 줄 있지만 **이 판의 gcc 가 그 갈래를 쓰지 않았다**(`-E` 에 없다) — 어느 조건의 갈래인지는 읽지 않았다.

### 7. `const int:` 칸 — **고르게 만드는 식은 없다 · 「lvalue 변환은 타입 한정자를 떨어뜨린다」 · 가를 수 있는 것은 포인터가 가리키는 쪽의 `const`** ★★

**왜 그런가**

- ★★ **제어식의 타입은 lvalue 변환을 거친 것처럼 본다**고 표준이 적고, 각주가 **「lvalue 변환은 타입 한정자를 떨어뜨린다」**. 그래서 제어식의 최상위 타입은 **`const int` 로 보일 수가 없다.** clang 이 그것을 「will never be selected」로 적었다.
- ★ **포인터가 가리키는 쪽의 `const` 는 남는다** — `ca` → `const int *` · `pcc` → `const char *`. 그쪽으로는 가를 수 있다.

### 8. 승격 — **승격은 연산이 만든다 · `_Generic` 은 식을 평가하지 않으니 승격하지 않는다** ★★

**왜 그런가**

- ★★ **`c` 는 `char` 변수 그대로**(lvalue 변환은 한정자만 떼고 **승격하지 않는다**), **`+c` 는 단항 `+` 가 정수 승격**을 일으켜 `int`, **`(char)1` 은 캐스트 결과 `char`**. 정수 승격 규칙 자체는 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/)가 정본이다.
- ★ **`abs(sh)` 는 함수 호출이라 인자가 `int` 로 변환**된다(프로토타입의 매개변수 타입으로). `ABS(sh)` 는 먼저 **`_Generic` 이 `short` 를 보고** 목록에서 못 찾아 에러다 — 변환은 **선택 뒤의 호출**에서나 일어날 일이다.

### 9. 36편과 대비 — **`...` 는 런타임에 믿고 · `_Generic` 은 컴파일 때 본다 · 승격이 반대 · 틀리면 UB 대 에러** ★★★

**왜 그런가**

- ★★★ **타입을 아는 때** — `...` 는 **받는 쪽이 `va_arg(ap, T)` 로 믿을 뿐**(형식 문자열·개수로 따로 알린다), `_Generic` 은 **컴파일러가 제어식의 타입을** 본다.
- ★★ **작은 타입** — `...` 는 `char`→`int` · `float`→`double` 로 **올려 보낸다**([36번 형제](../36-variadic-functions-stdarg/)의 승격 격자). `_Generic` 은 **그대로 본다**(1번의 `c` · `1.0f`).
- ★★ **틀렸을 때** — 36편은 `va_arg(ap, char)` 가 **UB 로 조용히**(clang 에서 값이 맞아 보였다) 지나갔고, 이 편은 **컴파일 에러**로 멈췄다(2·4·5번).

### 10. C++ — **`3 4 2.5 7 500` · `my_abs(sh)` 는 `my_abs(int)`(승격) · 새 타입은 오버로드 한 벌 추가** ★★

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s40x.cpp -o x ; ./x (cc exit=0 · run exit=0) =====
3 4 2.5 7 500
```

**왜 그런가**

- ★★ **오버로드 해석에는 승격·변환의 순위가 있다** — `short` 는 `int` 로 **승격**되는 후보가 가장 좋아 `my_abs(int)`. `_Generic` 에는 그 사다리가 없다(4번의 에러).
- ★ **새 타입 비용** — C++ 은 **`my_abs(Money)` 한 벌을 더 선언**하면 끝(기존 선언을 안 건드린다 — **열린 목록**). `_Generic` 매크로는 **본문의 목록을 고쳐야** 한다(닫힌 목록). [C++ 01](../../../cpp/syntax/01-function-overloading-and-overload-resolution/).

### 11. 다섯 층 — **표준이 거의 전부 · 조건부 표준은 C11 부터 · 컴파일러 구현은 경고와 `<tgmath.h>` · UB 없음** ★★★

**왜 그런가**

- **표준** — 변환 셋 · 한정자 떨어짐 · 평가하지 않음 · `default` 규칙 · 호환 타입 금지 · 문자 상수 `int`.
- **조건부 표준** — `_Generic` 은 **C11 부터**(이 편은 C11·C17 만).
- **컴파일러 구현** — clang 의 두 경고 · 에러를 짚는 자리 · `<tgmath.h>` 의 구현 수단.
- **UB** — 없음. 틀리면 **에러**로 멈추거나, **적법하게 조용**하다(죽은 칸 · 평가되지 않는 부작용).
- ★★★ **안 갈린 이유** — 선택 규칙이 **전부 표준 문장**이고, 컴파일 때 끝나는 일이라 최적화·런타임이 끼어들 자리가 없다.
- ★★ **gcc 로만 빌드하면 안 보이는 것** — **절대 안 골라지는 `const int:` 칸**(1번) · **평가되지 않는 `i++`**(3번).

### 12. 경계 ★

**왜 그런가**

- **`typedef` 의 `two compatible types`** — [06번 형제](../06-typedef-and-type-aliases/) · **`NULL` 의 타입** — [19번 형제](../19-void-pointer-null-pointer-and-null/).
- **매크로의 규칙** — 목록의 **41번 주제**(전처리기) · 목록의 **42번 주제**(함수형 매크로의 함정).
- ★ 이 주제가 책임지는 것 — ① **제어식이 무슨 타입으로 보이나**(격자) ② **평가하지 않음 · 맞는 분기 없음** ③ **매크로와 묶었을 때의 한계**(닫힌 목록 · 고정된 호출 모양 · `<tgmath.h>` 의 실제 구현).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s40a.c` | ★★★ **선택 격자 84칸 · 갈린 칸 0 / 70** · 경고 행 | 빌드 6 · 실행 7 · 진단 1 |
| `s40b.c` | ★★ 맞는 분기 없음 에러 | 진단 2 |
| `s40c.c` | ★★ 평가하지 않음 · clang 경고 | 실행 1 · 진단 2 |
| `s40d.c` · `s40d2.c` | ★★ 닫힌 목록 · 고정된 호출 모양 | 실행 1 · 진단 5 |
| `s40e.c` | ★★ `<tgmath.h>` 결과 · `-E` · 헤더 세기 | 실행 2 · 전처리 2 · 헤더 1 |
| `s40x.cpp` | ★ C++ 오버로드 | 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★ **1·3번의 경고** — clang 만 낸다.
- ★★ **6번의 구현 수단** — glibc 2.39 의 `tgmath.h` · clang 18 의 `tgmath.h`.

**선택 격자의 모든 칸 · 평가하지 않음 · `default` 규칙 · 호환 타입 금지는 구현 의존이 아니다.**\
어느 C11 이후 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — C23 `typeof`·`typeof_unqual` 과의 조합 · 함수 지명자를 제어식에(함수→포인터 변환) · `-std=c2x`.
- ★ **읽지 않은 것** — glibc `tgmath.h` 의 `_Generic` 갈래의 조건 · DR 481 의 원문.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **6번** — 헤더의 구현 수단은 판마다 바뀔 수 있다.
- ★ **1번의 경고 행** — gcc 가 죽은 연관을 경고하기 시작할 수 있다.
