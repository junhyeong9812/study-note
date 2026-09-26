# c/syntax/29 — 스코프와 링크(`static`·`extern`): 「**이 이름은 어디까지 보이고, 다른 파일의 같은 이름과 같은 것인가**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **gcc-12 12.4.0** ·
> **clang 18.1.3** · g++/clang++ 같은 판 · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s29a.c`\~`s29y2.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **링크 실험은 전부 `-c` 로 오브젝트를 먼저 만들고 링크했다** — 한 줄로 돌리면 진단에 `/tmp/ccXXXX.o` 가 박혀 흔들린다.
> ★★★ **본체 창은 `nm`** 이다. **역어셈블은 부적용**(링크는 심볼의 문제라 명령을 볼 일이 없다).
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **이 편에는 없다** — 정규화 규칙을 하나도 안 썼다 | ★★★ **`nm` 의 글자와 이름** · `readelf -s` 의 `Bind` |
> | (한 줄 컴파일+링크의 `/tmp/ccXXXX.o` — 그래서 **쓰지 않았다**) | ★★★ **단계별 종료 코드** — 컴파일 `exit` · 링크 `exit` |
> | — | ★★ 링커 진단 전문 · 컴파일러 진단 전문 |
> | — | ★ `nm` 의 주소 칸(오브젝트 안 오프셋) — 다만 **컴파일러가 바뀌면 다르다** |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 겹으로 가린 `x` — **`extern` 은 링크 있는 선언을 찾아 파일의 `x = 1` 이 된다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s29g.c -o x ; ./x (cc exit=0 · run exit=0) =====
파일 스코프         x = 1
main 블록           x = 2
안쪽 블록           x = 3
extern 으로 부른    x = 1
for 머리            x = 4
다시 main 블록      x = 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29g.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wshadow -c s29g.c -o /dev/null (cc exit=0) =====
s29g.c: In function ‘main’:
s29g.c:7:9: warning: declaration of ‘x’ shadows a global declaration [-Wshadow]
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
s29g.c:3:5: note: shadowed declaration is here
    3 | int x = 1;                               /* 파일 스코프 */
      |     ^
s29g.c:10:13: warning: declaration of ‘x’ shadows a previous local [-Wshadow]
   10 |         int x = 3;                       /* 더 안쪽 블록 — 또 가린다 */
      |             ^
s29g.c:7:9: note: shadowed declaration is here
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
s29g.c:17:14: warning: declaration of ‘x’ shadows a previous local [-Wshadow]
   17 |     for (int x = 4; x < 5; x++)          /* for 의 첫 칸도 블록 스코프다 */
      |              ^
s29g.c:7:9: note: shadowed declaration is here
    7 |     int x = 2;                           /* 블록 스코프 — 파일의 x 를 가린다 */
      |         ^
```

**왜 그런가**

- ★★ 여섯 줄은 `1 · 2 · 3 · 1 · 4 · 2` 다. 가려진 것은 **사라진 것이 아니라** 안쪽 블록이 끝나면 다시 보인다.
- ★★★ **`extern int x;` 는 바로 바깥의 `x = 3` 이 아니다.** 그 `x` 는 **링크가 없는** 자동 변수라 짝이 될 수 없다.\
  표준 규칙 — 앞에 보이는 선언이 **링크 없음**이면, 이 `extern` 선언은 **외부 링크**를 갖는다. 그래서 **파일 스코프의 `x`** 와 같은 것이 된다.
- ★★ **기본 경고는 0건**이다 — 둘째 블록이 **`cc exit=0` 에 진단 0줄**이다.\
  ★ **`-Wshadow` 를 더하면 3건** — 7·10·17행. **`extern` 줄은 없다** — 가림이 아니라 **다시 부르기**다.
- ★ **`for` 머리의 `x` 는 루프가 끝나면 안 보인다** — 마지막 줄이 다시 `2` 다.

### 2. 선언 열 개의 `nm` — **대문자 셋 · 소문자 넷 · `U` 하나 · 심볼 없음 둘** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && nm s29a.o (cc exit=0) =====
0000000000000018 T api
0000000000000008 b calls.0
                 U e_used
0000000000000000 D g_def
0000000000000000 B g_zero
0000000000000000 t helper
0000000000000004 d s_def
0000000000000004 b s_zero
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && nm s29a.o (cc exit=0) =====
0000000000000000 T api
0000000000000004 b api.calls
                 U e_used
0000000000000000 D g_def
0000000000000000 B g_zero
0000000000000050 t helper
0000000000000004 d s_def
0000000000000008 b s_zero
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29a.c -o s29a.o && readelf -s -W s29a.o | sed -n '/FILE/,$p' (cc exit=0) =====
     1: 0000000000000000     0 FILE    LOCAL  DEFAULT  ABS s29a.c
     2: 0000000000000000     0 SECTION LOCAL  DEFAULT    1 .text
     3: 0000000000000000     0 SECTION LOCAL  DEFAULT    3 .data
     4: 0000000000000000     0 SECTION LOCAL  DEFAULT    4 .bss
     5: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    3 s_def
     6: 0000000000000004     4 OBJECT  LOCAL  DEFAULT    4 s_zero
     7: 0000000000000000    24 FUNC    LOCAL  DEFAULT    1 helper
     8: 0000000000000008     4 OBJECT  LOCAL  DEFAULT    4 calls.0
     9: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    3 g_def
    10: 0000000000000000     4 OBJECT  GLOBAL DEFAULT    4 g_zero
    11: 0000000000000018    82 FUNC    GLOBAL DEFAULT    1 api
    12: 0000000000000000     0 NOTYPE  GLOBAL DEFAULT  UND e_used
```

**왜 그런가**

- ★★★ **글자** — `g_def` **`D`** · `g_zero` **`B`** · `s_def` **`d`** · `s_zero` **`b`** · `e_used` **`U`** · `helper` **`t`** · `api` **`T`** · `calls` **`b`**.
- ★★★ **심볼이 없는 둘** — **`e_unused`**(`extern` 선언을 **안 썼다** — 선언은 아무것도 만들지 않는다) · **`local`**(자동 저장 기간 — 스택에만 있다).
- ★★ **`g_zero = 0` 은 `B`** 다. `0` 을 적어도 **`.bss`** 로 간다.
- ★★ **함수 안 `static` 의 이름이 갈린다** — gcc **`calls.0`** · clang **`api.calls`**. 둘 다 **다른 파일에서 철자를 맞출 수 없게** 뭉갠 것이고, 방식은 **표준 밖**이다.
- ★★ **`readelf -s` 의 `Bind`** — 대문자는 **`GLOBAL`**, 소문자는 **`LOCAL`** 이다. `e_used` 는 `GLOBAL` 인데 `Ndx` 가 **`UND`** 다.
- ★ **주소 칸은 근거로 쓰지 않는다** — `api` 가 gcc `0x18`, clang `0x0` 이다. 오브젝트 안 오프셋이라 재실행에는 안 흔들리지만 **컴파일러가 바뀌면 다르다.**

### 3. 같은 이름 두 정의 — **컴파일 통과 · 링크 `exit=1`** · `static` 이면 **둘이 따로 산다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29b1.c s29b2.c && gcc s29b1.o s29b2.o -o x (cc exit=1) =====
/usr/bin/ld: s29b2.o:(.data+0x0): multiple definition of `shared'; s29b1.o:(.data+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29b1.c s29b2.c && clang s29b1.o s29b2.o -o x (cc exit=1) =====
/usr/bin/ld: s29b2.o:(.data+0x0): multiple definition of `shared'; s29b1.o:(.data+0x0): first defined here
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29c1.c s29c2.c && gcc s29c1.o s29c2.o -o x ; ./x (cc exit=0 · run exit=0) =====
c1 쪽 shared = 1 · c2 쪽 shared = 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29c1.c s29c2.c && nm s29c1.o s29c2.o (cc exit=0) =====

s29c1.o:
0000000000000000 T from_c1
0000000000000000 d shared

s29c2.o:
                 U from_c1
0000000000000000 T main
                 U printf
0000000000000000 d shared
```

**왜 그런가**

- ★★★ **컴파일은 두 파일 다 `exit=0`** 이다(배너의 `&&` 앞이 통과했기에 링크까지 갔다). **컴파일러는 한 파일만 본다.**
- ★★★ **링크가 `multiple definition of 'shared'` 로 죽는다.** 첫 줄은 **`/usr/bin/ld` 가 낸 것이라 두 컴파일러에서 한 글자도 같다** — 끝 줄만 `collect2: error` 대 `clang: error: linker command failed` 로 갈린다.
- ★★ **`static` 을 붙이면 링크가 통과하고 `1` 과 `2` 가 따로 찍힌다.** `nm` 에서 **둘 다 소문자 `d`** — 링커가 짝지으려 하지 않는다.
- ★ **틀린 처방이 되는 경우** — 원래 **한 값을 공유하려던** 것이면, `static` 은 오류를 없앤 대신 **공유를 깨뜨렸다.** 공유가 목적이면 **헤더에 `extern`, 정의는 한 곳**이다.

### 4. `int t;` 두 파일 — **기본값은 전부 링크 `exit=1`, `-fcommon` 은 합쳐서 통과** ★★★

**출력**

```text
===== 잠정 정의 두 개 — 컴파일러 3 × 플래그 3 · 초기자 하나 × 2 (exit=0) =====
컴파일러   플래그       cc     link     실행
gcc-12     (기본)       exit=0 exit=1   -
gcc-12     -fno-common  exit=0 exit=1   -
gcc-12     -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
gcc        (기본)       exit=0 exit=1   -
gcc        -fno-common  exit=0 exit=1   -
gcc        -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
clang      (기본)       exit=0 exit=1   -
clang      -fno-common  exit=0 exit=1   -
clang      -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
--- 한쪽에 초기자(int t = 0;)를 두면 (s29u1.c + s29t2.c)
gcc        (기본)       exit=0 exit=1   -
gcc        -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
clang      (기본)       exit=0 exit=1   -
clang      -fcommon     exit=0 exit=0   t2 쪽 t = 5 · t1 쪽 t = 5
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fcommon -c s29t1.c s29t2.c && gcc -fcommon s29t1.o s29t2.o -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fcommon -c s29t1.c -o s29t1.o && nm s29t1.o && gcc -std=c17 -Wall -Wextra -pedantic -c s29t1.c -o s29t1.o && nm s29t1.o (cc exit=0) =====
0000000000000000 T get_t1
0000000000000004 C t
0000000000000000 T get_t1
0000000000000000 B t
```

**왜 그런가**

- ★★★ **아홉 칸 중 `-fcommon` 세 칸만 통과**한다. 기본값과 `-fno-common` 은 **같은 결과**다 — 셋 다 **기본값이 이미 `-fno-common`** 이기 때문이다. **컴파일은 전 칸 `exit=0`**.
- ★★★ **`-fcommon` 칸의 `t1 쪽 t = 5`** — t2 가 쓴 값을 t1 이 읽었다. **두 `t` 가 한 객체로 합쳐졌다.**\
  ★ 그리고 **진단이 0줄**이다(둘째 블록) — 병합은 **조용히** 일어난다.
- ★★ **한쪽에 초기자를 둬도 결과가 같다** — `-fcommon` 이면 공용 하나와 정의 하나가 합쳐지고, 기본값이면 깨진다.
- ★★ **`nm` 의 글자** — `-fcommon` 판은 **`C t`**(공용 — 자리를 링커가 정한다), 기본 판은 **`B t`**(이 파일의 `.bss` 에 자리가 있는 정의).
- ★★★ **판 경계는 이 머신에서 잰 것이 아니다.** 가진 판(gcc 12.4 · 13.3 · clang 18.1)이 **전부 경계 뒤쪽**이라 「10 부터」·「11 부터」는 **GCC 10 Porting 문서와 Clang 11 Release Notes 의 문장**이다.\
  ★ 실행으로 확인한 것은 「**이 세 판은 깨진다**」까지다 — 「못 잰 것」으로 따로 적는다.
- ★★ **표준** — 잠정 정의는 **그 파일 끝에서 정의 하나**가 된다. 두 파일이면 외부 링크 이름에 **외부 정의가 둘**이고, 그것은 **UB**(진단 의무 없음)다.\
  ★★ `-fcommon` 의 병합은 **부록 J 의 「여러 외부 정의」 공통 확장** — **조건부 표준(확장)** 칸이다.

### 5. `static` 함수를 다른 파일에서 — **① 0 · ② 0 · ③ 1** ★★

**출력**

```text
===== static 함수를 다른 번역 단위에서 — 단계별 종료 코드 (컴파일은 -std=c17 -Wall -Wextra -pedantic -c) (exit=0) =====
gcc    ① s29d1.c 컴파일            exit=0
gcc    ② s29d2.c 컴파일            exit=0
gcc    ③ s29d1.o + s29d2.o 링크   exit=1
clang  ① s29d1.c 컴파일            exit=0
clang  ② s29d2.c 컴파일            exit=0
clang  ③ s29d1.o + s29d2.o 링크   exit=1
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29d1.c s29d2.c && gcc s29d1.o s29d2.o -o x (cc exit=1) =====
/usr/bin/ld: s29d2.o: in function `main':
s29d2.c:(.text+0x9): undefined reference to `helper'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29d1.c s29d2.c && nm s29d1.o s29d2.o (cc exit=0) =====

s29d1.o:
0000000000000000 t helper
000000000000000f T use_helper

s29d2.o:
                 U helper
0000000000000000 T main
                 U printf
```

**왜 그런가**

- ★★★ **컴파일 둘은 `exit=0`, 링크만 `exit=1`** 이다. `s29d2.c` 는 `int helper(void);` 라는 **선언만 보고** 만족한다.
- ★★ 핵심 줄은 **`undefined reference to 'helper'`** 다.
- ★★★ **`nm`** — `s29d1.o` 에는 **`t helper`**(소문자 = `LOCAL`), `s29d2.o` 에는 **`U helper`**. 링커는 **`GLOBAL` 끼리만 짝짓는다** — 소문자 `t` 는 후보가 아니다.
- ★ **링커 진단은 「없다」와 「안 보인다」를 가르지 않는다** — 둘 다 `undefined reference` 다. **`nm` 이 가른다.**
- ★ **컴파일 단계만 도는 검사로는 원리상 못 잡는다** — 두 파일을 동시에 보는 단계가 링크뿐이다.

### 6. C99 `inline` — **`inline` 만이면 `-O0` 링크 `exit=1`, `-O2` 통과** ★★

**출력**

```text
===== C99 inline — 파일 3 × 컴파일러 2 × 최적화 2 (링크 종료 코드) (exit=0) =====
s29f   gcc    -O0  link exit=1 | -
s29f   gcc    -O2  link exit=0 | twice(21) = 42
s29f   clang  -O0  link exit=1 | -
s29f   clang  -O2  link exit=0 | twice(21) = 42
s29f2  gcc    -O0  link exit=0 | twice(21) = 42
s29f2  gcc    -O2  link exit=0 | twice(21) = 42
s29f2  clang  -O0  link exit=0 | twice(21) = 42
s29f2  clang  -O2  link exit=0 | twice(21) = 42
s29f3  gcc    -O0  link exit=0 | twice(21) = 42
s29f3  gcc    -O2  link exit=0 | twice(21) = 42
s29f3  clang  -O0  link exit=0 | twice(21) = 42
s29f3  clang  -O2  link exit=0 | twice(21) = 42
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f.c -o f1.o && nm f1.o && gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f2.c -o f2.o && nm f2.o && gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s29f3.c -o f3.o && nm f3.o (cc exit=0) =====
0000000000000000 T main
                 U printf
                 U twice
0000000000000012 T main
                 U printf
0000000000000000 T twice
000000000000000e T main
                 U printf
0000000000000000 t twice
```

**왜 그런가**

- ★★★ **열두 칸 중 `s29f` 의 `-O0` 두 칸만 실패**한다. **최적화 수준이 링크 결과를 바꾸는 칸**이 바로 거기다.
- ★★★ **`nm`** — `s29f` **`U twice`**(외부 정의가 없다) · `s29f2` **`T twice`**(`extern inline` 선언 한 줄이 외부 정의를 만들었다) · `s29f3` **`t twice`**(`static inline` — 이 파일 전용 사본).\
  ★★ 이것이 **제5의 상태**다 — 「외부 정의가 있나」를 링크 에러가 아니라 **`nm` 으로 물어** 답을 얻었다.
- ★★ **`-O2` 의 통과는 보장이 아니다** — 호출을 펼쳐서 `twice` 라는 심볼이 **필요 없어졌을 뿐**이다. 인라인할지는 컴파일러가 고른다.
- ★ **둘 다 있으면 어느 쪽을 부를지 표준이 정하지 않는다** — **미명시**다.
- ★ **C++ 의 `inline` 은 뜻이 다르다** — 「여러 번역 단위에 같은 정의가 있어도 된다」는 약속이고, C++ 에서는 이 링크 실패가 안 난다.

### 7. `static` 의 두 뜻 — **파일은 링크, 함수 안은 저장 기간 · `nm` 은 둘 다 `b`** ★★★

**왜 그런가**

- ★★★ **파일 스코프 `static`** 은 **링크**를 바꾼다(외부 → 내부). 저장 기간은 **원래도 정적**이었다.
- ★★★ **함수 안 `static`** 은 **저장 기간**을 바꾼다(자동 → 정적). 링크는 **원래도 없었다** — 여전히 그 함수 안에서만 보인다.
- ★★★ **`nm` 에서 둘 다 `b`** 다(2번의 `s_zero` 와 `calls.0`). ELF 에는 **「내부 링크」와 「링크 없음」을 가르는 칸이 없다** — 둘 다 **`LOCAL`** 이다.
- ★★ **가르는 것은 뭉갠 이름**(`calls.0` · `api.calls`)뿐이다 — **컴파일러의 관례**지 표준의 보장이 아니다.
- ★ 「소문자면 내부 링크」는 **반만** 맞다 — 소문자는 **「이 파일 밖에서 안 보인다」** 까지만 말한다.

### 8. `extern` 타입 불일치 — **여섯 벌 중 gcc `-flto` 한 벌만, 그것도 경고로** ★★

**출력**

```text
===== extern 타입 불일치 — 여섯 벌 (exit=0) =====
gcc                                    cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
gcc -flto                              cc exit=0 경고 1건 | run exit=0 | val 을 int 로 읽으면 = 0
clang                                  cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
clang -flto                            cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
gcc -fsanitize=address,undefined -g    cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
clang -fsanitize=address,undefined -g  cc exit=0 경고 0건 | run exit=0 | val 을 int 로 읽으면 = 0
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s29e1.c s29e2.c -o x (cc exit=0) =====
s29e2.c:3:12: warning: type of ‘val’ does not match original declaration [-Wlto-type-mismatch]
    3 | extern int val;                /* ★ 선언은 int — 타입이 다르다 */
      |            ^
s29e1.c:1:8: note: type ‘double’ should match type ‘int’
    1 | double val = 3.5;              /* ★ 정의는 double */
      |        ^
s29e1.c:1:8: note: ‘val’ was previously declared here
s29e1.c:1:8: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -flto s29e1.c s29e2.c -o x (cc exit=0) =====
```

**왜 그런가**

- ★★★ **말하는 것은 한 벌**(gcc `-flto`)뿐이다 — `[-Wlto-type-mismatch]` · **`cc exit=0`**. 나머지 다섯은 **경고 0건 · 전부 `exit=0`**.
- ★★ **clang `-flto` 의 빈 블록**이 곧 답이다 — **같은 이름의 옵션인데 대조하는 것이 다르다.**
- ★★ **ASan·UBSan 이 못 보는 이유** — `int` 4바이트 읽기가 `double` 8바이트 **범위 안**이라 메모리 오류가 아니고, 산술 문제도 아니다. **원리상 창 밖**이다.
- ★★ **출력 `0` 은 UB 의 한 결과**다 — `3.5` 의 아래 32비트가 이 판에서 0 이었을 뿐, **계산해 낼 대상이 아니다.**
- ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)와 이어 보면 — gcc `-flto` 는 **함수 서명과 변수 타입**(선언의 타입)은 보고, **구조체 레이아웃**은 못 봤다.
- ★ **「`-flto` 가 잡는다」는 gcc 의 성질**이다 — 플래그의 성질로 적으면 clang 에서 **틀린 문장**이 된다.

### 9. 괄호 안의 `struct Point` — **프로토타입 스코프라 괄호와 함께 죽는다** ★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -c s29h.c -o /dev/null (cc exit=1) =====
s29h.c:1:18: warning: ‘struct Point’ declared inside parameter list will not be visible outside of this definition or declaration
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^~~~~
s29h.c:5:6: error: conflicting types for ‘take’; have ‘void(struct Point *)’
    5 | void take(struct Point *p) { (void)p; }
      |      ^~~~
s29h.c:1:6: note: previous declaration of ‘take’ with type ‘void(struct Point *)’
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -c s29h.c -o /dev/null (cc exit=1) =====
s29h.c:1:18: warning: declaration of 'struct Point' will not be visible outside of this function [-Wvisibility]
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^
s29h.c:5:6: error: conflicting types for 'take'
    5 | void take(struct Point *p) { (void)p; }
      |      ^
s29h.c:1:6: note: previous declaration is here
    1 | void take(struct Point *p);              /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^
1 warning and 1 error generated.
```

**왜 그런가**

- ★★ 1행의 `struct Point` 는 **함수 프로토타입 스코프**에 선언된다 — 그 괄호가 끝나면 사라진다. 두 컴파일러가 **그 자리에 경고**를 단다.
- ★★ 5행의 `struct Point`(파일 스코프)는 **다른 타입**이라 `conflicting types` — **`cc exit=1`**.
- ★★ **gcc 는 두 타입을 둘 다 `void(struct Point *)`** 로 찍는다 — **글자는 같은데 다른 타입**이다. 문구를 근거로 쓰면 「같은데 왜?」에서 막힌다. **근거는 앞 줄의 경고와 `cc exit`** 다.
- ★ 처방 — 파일 스코프에 **`struct Point;` 한 줄**을 먼저 둔다.

### 10. C++ 의 풀이 — **이름 없는 네임스페이스는 `t`/`d`, `inline` 변수는 두 파일에서 링크된다** ★★

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s29x.cpp -o s29x.o && nm s29x.o (cc exit=0) =====
0000000000000010 T _Z8exportedv
0000000000000004 d _ZL9old_style
0000000000000000 d _ZN12_GLOBAL__N_114hidden_counterE
0000000000000000 t _ZN12_GLOBAL__N_19hidden_fnEv
0000000000000000 u shared_inline
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s29x.cpp -o s29x.o && nm s29x.o (cc exit=0) =====
0000000000000000 T _Z8exportedv
0000000000000000 d _ZL9old_style
0000000000000004 d _ZN12_GLOBAL__N_114hidden_counterE
0000000000000020 t _ZN12_GLOBAL__N_19hidden_fnEv
0000000000000000 V shared_inline
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s29y1.cpp s29y2.cpp && g++ s29y1.o s29y2.o -o x ; ./x (cc exit=0 · run exit=0) =====
y2 쪽 = 10 · y1 쪽 = 10
```

**왜 그런가**

- ★★ **이름 없는 네임스페이스**가 C 의 파일 스코프 `static` 자리다 — `hidden_counter` **`d`** · `hidden_fn` **`t`**(소문자). 이름에 `_GLOBAL__N_1` 이 박혀 **다른 파일이 철자를 맞출 수 없다.**
- ★★★ **C++17 `inline` 변수는 두 파일에 정의가 있어도 링크된다** — y2 가 쓴 `10` 을 y1 이 읽는다. **C 의 3번이 깨졌던 모양 그대로**인데 통과한다.
- ★★ **글자가 갈린다** — g++ **`u`**(GNU 고유 전역) · clang++ **`V`**(약한 객체). 「여럿이어도 하나로 친다」의 **표시 방식이 구현마다 다르다.**
- ★ C 의 `-fcommon` 은 **컴파일러 확장**으로, C++17 `inline` 변수는 **언어 문법**으로 같은 일을 한다.

### 11. 다섯 층 — **표준이 본체 · UB 가 둘째 · 조건부 표준(공통 확장)이 드물게 찬다** ★★★

**왜 그런가**

- **표준** — 스코프 넷 · 링크 셋 · `static` 의 두 뜻 · `extern` 이 선언뿐인 것 · 블록 안 `extern` 의 규칙 · 잠정 정의 · C99 `inline` 정의.
- ★★★ **조건부 표준** — **`-fcommon` 의 여러 외부 정의 병합**(부록 J 공통 확장). **다른 편들은 이 칸이 매크로·헤더**였는데, 여기서는 **표준이 「흔한 확장」으로 적어 둔 동작**이다.
- **구현 정의** — 컴파일러 기본값(`-fno-common`) · 이름 뭉개기(`calls.0` 대 `api.calls`) · `u` 대 `V` · 진단 문구.
- **미명시** — 인라인 정의와 외부 정의 중 **어느 쪽을 부르나**.
- **UB** — 외부 정의 둘 · `extern` 타입 불일치.
- ★★ **가장 두꺼운 칸은 표준**, 두 번째는 **UB** 다.
- ★★ **침묵하는 자리** — 표준: `nm` 이 내부/없음을 못 가름 · 확장: `-fcommon` 병합에 진단 0 · 구현 정의: 판 경계를 안 알려 줌 · 미명시: 어느 정의인지 모름 · UB: 여섯 벌 중 다섯 침묵.
- ★★ **「종료 코드 0인데 ill-formed」 새 항목은 없다** — 이 편의 위반은 **링크에서 `exit=1`** 이거나 **UB 라 진단 의무가 없다.** 대신 **「종료 코드 0인데 UB」**(8번)가 있다.
- ★ **부적용 창은 역어셈블** — 링크는 **어느 심볼이 어디 있나**의 문제라, 명령이 무엇인지는 **질문과 무관**하다. 「안 쟀다」가 아니라 **「잴 것이 없다」** 다.

### 12. 경계 ★

**왜 그런가**

- **링커 일반** — [`foundations/compiler-pipeline/`](../../../../compiler-pipeline/).
- **저장 기간** — [28번 형제](../28-choosing-among-four-storage-durations/) · **파일 스코프 `const` 의 링크** — [31번 형제](../31-const-and-pointer-const-placement/).
- **`inline` 규칙 전체** — 목록의 **39번 주제** · **헤더 배치** — 목록의 **44번 주제** · **링크 오류 거꾸로 읽기** — 목록의 **45번 주제**.
- ★ 이 주제가 책임지는 것 — ① **`static` 두 뜻의 구분** ② **선언이 만드는 심볼(`nm` 의 글자)** ③ **같은 이름 두 파일의 단계별 결과**(잠정 정의 판 격자 포함).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s29g.c` | 가림 `1 2 3 1 4 2` · `extern` 이 파일의 `x` · `-Wshadow` **3건**(`extern` 줄 없음) | gcc 실행 1 · 진단 1 |
| `s29h.c` | 프로토타입 스코프 경고 + `conflicting types` · **`cc exit=1`** · gcc 문구가 두 타입을 **같은 글자**로 | gcc 1 · clang 1 |
| `s29a.c` | `nm` 글자 여덟 · **심볼 없음 둘** · `calls.0` 대 `api.calls` · `readelf -s` `Bind` | gcc `nm` 1 · clang `nm` 1 · `readelf` 1 |
| `s29b1.c`·`s29b2.c` | 링크 `multiple definition` · **`exit=1`** | gcc 1 · clang 1 |
| `s29c1.c`·`s29c2.c` | `static` 이면 `1`·`2` 따로 · `nm` 둘 다 `d` | gcc 실행 1 · `nm` 1 |
| `s29t1.c`·`s29t2.c`·`s29u1.c` | ★★★ **판 격자** — 컴파일러 3 × 플래그 3 + 초기자 변형 2 × 2 · `C t` 대 `B t` | ★ **13칸** · gcc 진단 1 · `nm` 2 |
| `s29d1.c`·`s29d2.c` | 단계별 **0 · 0 · 1** · `t helper` 대 `U helper` | 컴파일러 2 × 3단계 · 진단 2 · `nm` 1 |
| `s29e1.c`·`s29e2.c` | ★★ **여섯 벌 중 gcc `-flto` 만 경고** · 전부 `exit=0` · `val = 0` | 6벌 + `-flto` 진단 2 · 실행 1 |
| `s29f.c`·`s29f2.c`·`s29f3.c` | ★★ `inline` 만이면 **`-O0` 링크 `exit=1`** · `U`/`T`/`t` | 12칸 · 진단 1 · `nm` 3 |
| `s29x.cpp`·`s29y1.cpp`·`s29y2.cpp` | 이름 없는 네임스페이스 `t`/`d` · `inline` 변수 두 파일 링크 · **`u` 대 `V`** | g++ `nm` 1 · clang++ `nm` 1 · g++ 실행 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py` 로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **4번 격자의 기본값 칸 전부** — **컴파일러 판**에 달렸다. GCC 9 이하 · Clang 10 이하에서는 통과한다는 것이 **문서의 주장**이다.
- ★★ **8번의 「gcc `-flto` 만 잡는다」** — 두 컴파일러의 **이 판**이 대조하는 범위다.
- ★★ **6번의 `-O2` 통과** — 인라인 결정은 컴파일러의 선택이다.
- ★ **함수 안 `static` 의 뭉갠 이름**(`calls.0`·`api.calls`) · **C++ `inline` 변수의 글자**(`u`·`V`) · **`nm` 주소 칸** · 진단 문구.

**스코프 넷 · 링크 셋 · `static` 의 두 뜻 · `extern` 이 선언뿐인 것 · 잠정 정의가 파일 끝에서 정의가 되는 것 · C99 인라인 정의가 외부 정의가 아닌 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 약한 심볼(`__attribute__((weak))`) · 정적 라이브러리의 링크 순서 · `-fvisibility=hidden` · gnu89 `inline`(`-fgnu89-inline`) ·\
  `-flto` 에 구조체 레이아웃 불일치를 다시 주는 것([25번 형제](../25-incomplete-types-and-opaque-struct/)가 이미 보였다).
- ★ **못 잰 것** — **GCC 10 · Clang 11 이라는 판 경계 자체.** 이 머신의 판이 전부 경계 뒤쪽이라 **경계 앞의 칸을 만들 수 없다.**\
  「안 돌려 본 것」이 아니라 「**측정에 필요한 판이 없는 것**」이라 따로 적는다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **8번의 여섯 벌** — clang `-flto` 가 타입 불일치를 보기 시작할 수 있다.
- ★★ **6번 격자** — 인라인 결정이 바뀌면 `-O2` 칸이 움직인다.
- ★ **이름 뭉개기와 `nm` 글자**(`u`/`V`) · 진단 문구.
- **스코프·링크 규칙은 다시 돌릴 필요가 없다** — C89(`inline` 은 C99) 이후 바뀐 적이 없다.
