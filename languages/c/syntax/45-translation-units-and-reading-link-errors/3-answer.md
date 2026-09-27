# c/syntax/45 — 번역 단위와 링크 오류 읽기: 「**링크 에러는 「이 이름의 정의가 몇 개인가」에 대한 링커의 대답이다 — 문구에서 원인으로 거꾸로 걸어가는 길은 `nm` 이 깐다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **clang 18.1.3** · **g++ 13.3.0** · **GNU ld 2.42** · **ld.gold** ·
> x86-64 Linux · glibc 2.39 에서 실제로 돌려 얻은 것이다.\
> 소스는 `s45*.c` · `s45h.h` · `s45x.cpp` · `s45xe.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★★ **본체 창은 링크 결과 + `nm`** — 원인 10 × 링크 3.
> ★★ **흔들리는 칸** — 없다(링크 문구는 목적 파일 이름을 고정해 임시 파일 이름을 뺐다). 정규화 규칙은 기본 넷뿐이다.

## 이 파일이 다시 싣는 소스

★ 7번은 질문 파일에 없는 `s45xe.cpp` 를 쓴다. 1번의 1 줄 소스를 문구 블록 앞에 다시 둔다.

```c
/* s45u.c */
int area(int w, int h);                 /* 선언 */

int main(void) {
    return area(2, 3) == 6 ? 0 : 1;
}
```

```cpp
// s45xe.cpp
extern "C" int add(int a, int b) { return a + b; }
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 역추적 격자 — **링크된 칸 9 / 30 · 실패한 일곱 줄은 세 판 전부 같은 종류 · gcc/clang 0 / 10 · bfd/gold 0 / 10** ★★★

**출력**

```text
===== 역추적 격자 — 원인 10 × 링크 3 (+ nm) (exit=0) =====
원인                              	gcc (ld.bfd)	clang (ld.bfd)	gcc -fuse-ld=gold	nm (gcc 로 만든 .o)
1 선언만 있고 정의 없음           	undefined reference	undefined reference	undefined reference	U area
2 헤더에 정의 · 두 파일이 include 	multiple definition	multiple definition	multiple definition	T scale / T scale
3 다른 파일의 static 정의         	undefined reference	undefined reference	undefined reference	t helper / U helper
4 정의 쪽 이름이 한 글자 다름     	undefined reference	undefined reference	undefined reference	T total_cuont / U total_count
5 정의를 C++ 로 컴파일            	undefined reference	undefined reference	undefined reference	T _Z3addii / U add
6 정적 라이브러리를 앞에          	undefined reference	undefined reference	undefined reference	T lib_value / U lib_value
7 정적 라이브러리를 뒤에          	링크 성공	링크 성공	링크 성공	T lib_value / U lib_value
8 main 이 없음                    	undefined reference	undefined reference	undefined reference	(없음)
9 약한 선언 · 정의 없음           	링크 성공	링크 성공	링크 성공	w hook
10 약한 정의 + 강한 정의          	링크 성공	링크 성공	링크 성공	W level / T level
(칸 = 각 파일을 $CC -std=c17 -c 로 따로 만든 뒤 링크한 결과 · C++ 파일은 g++/clang++ -std=c++17 -c · 정적 라이브러리 = ar rcs libs45.a s45l.o)
링크된 칸 9 / 30
gcc 와 clang 이 갈린 행 0 / 10
ld.bfd 와 gold 가 갈린 행 0 / 10
```

**왜 그런가**

- ★★★ **성공은 7 · 9 · 10 줄뿐**이다 — 라이브러리를 뒤에 둔 판, 약한 선언, 약한 정의 + 강한 정의.
- ★★★ **`undefined reference` 여섯 줄**(1 · 3 · 4 · 5 · 6 · 8)은 전부 「**링커가 본 정의가 0 개**」다 — 정의가 없거나(1), 숨었거나(3 — `static`), 이름이 다르거나(4 · 5), 순서 밖이거나(6), 찾는 쪽이 런타임이다(8).
- ★★ **`multiple definition` 은 2 줄** — 헤더의 정의를 두 파일이 include 해 **정의가 둘**이다.
- ★★ **판은 에러의 종류를 안 바꿨다** — 세 판이 **같은 규칙**(정의는 하나)을 검사한다. 판이 바꾼 것은 **문구의 모양**(5번)이다.

### 2. `nm` 의 글자 — **1 `U` 뿐 · 2 `T / T` · 3 `t / U` · 4 `T total_cuont / U total_count` · 5 `T _Z3addii / U add` · 9 `w` · 10 `W / T` · 8 은 `Scrt1.o`** ★★★

**출력** — 1번 격자의 오른쪽 칸, 그리고 파일 전체의 `nm`:

```text
===== gcc -std=c17 -c s45s1.c -o s45s1.o && gcc -std=c17 -c s45s2.c -o s45s2.o && nm s45s1.o s45s2.o (exit=0) =====

s45s1.o:
0000000000000013 T api
0000000000000000 t helper

s45s2.o:
                 U helper
0000000000000000 T main
```

```text
===== gcc -std=c17 -c s45t1.c -o s45t1.o && gcc -std=c17 -c s45t2.c -o s45t2.o && nm s45t1.o s45t2.o (exit=0) =====

s45t1.o:
0000000000000000 T total_cuont

s45t2.o:
0000000000000000 T main
                 U total_count
```

```text
===== g++ -std=c++17 -c s45x.cpp -o s45x.o && nm s45x.o && nm -C s45x.o (exit=0) =====
0000000000000000 T _Z3addii
0000000000000000 T add(int, int)
```

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && nm s45w1.o (exit=0) =====
                 U _GLOBAL_OFFSET_TABLE_
                 w hook
0000000000000000 T main
                 U printf
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc -std=c17 -c s45w4.c -o s45w4.o && nm s45w3.o s45w4.o (exit=0) =====

s45w3.o:
0000000000000000 W level
000000000000000f T main
                 U printf

s45w4.o:
0000000000000000 T level
```

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && nm s45n.o && nm /usr/lib/x86_64-linux-gnu/Scrt1.o (exit=0) =====
0000000000000000 T only_helper
                 U _GLOBAL_OFFSET_TABLE_
0000000000000000 R _IO_stdin_used
0000000000000000 r __abi_tag
0000000000000000 D __data_start
                 U __libc_start_main
0000000000000000 T _start
0000000000000000 W data_start
                 U main
```

**왜 그런가**

- ★★★ **`U` 는 「정의가 없다 · 밖에서 찾는다」** — 1 줄은 **어느 파일에도 `T area` 가 없다.**
- ★★★ **`t` 는 「정의가 있다 · 이 파일 전용」** — 3 줄의 `helper` 는 **정의가 있는데** 링커가 다른 파일의 `U helper` 에 이어 주지 않는다.
- ★★ **4 · 5 줄은 `T` 가 있는데 이름이 다르다** — 오타(`total_cuont`)와 맹글링(`_Z3addii`).
- ★★ **9 줄 `w hook`** — 약한 **미정의**. **10 줄 `W level` / `T level`** — 약한 정의와 강한 정의.
- ★ **8 줄은 내 파일에 `main` 이 (없음)** — `U main` 을 가진 것은 **`Scrt1.o`**(C 런타임 시작 코드)다.

### 3. `-lm` 의 자리 — **gcc 는 `-lm s45m.o` 만 실패 · clang 은 두 순서 다 성공** ★★

**출력**

```text
===== -lm 의 자리 — 드라이버 2 × 순서 2 (공유 라이브러리 libm) (exit=0) =====
드라이버	s45m.c -lm	-lm s45m.c
gcc     	링크 성공	undefined reference
clang   	링크 성공	링크 성공
(칸 = $CC -std=c17 -c s45m.c 뒤 $CC s45m.o -lm / $CC -lm s45m.o 의 링크 결과)
링크된 칸 3 / 4
```

```text
===== gcc -std=c17 -c s45m.c -o s45m.o && gcc -lm s45m.o -o x (cc exit=1) =====
/usr/bin/ld: s45m.o: in function `main':
s45m.c:(.text+0x27): undefined reference to `cos'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -### -lm s45m.o -o x 2>&1 | grep collect2 | tr ' ' '\n' | grep -n -E '^-lm$|^s45m.o$|as-needed' (exit=0) =====
17:--as-needed
38:-lm
39:s45m.o
42:--as-needed
48:--as-needed
```

```text
===== clang -### -lm s45m.o -o x 2>&1 | tail -n 1 | tr ' ' '\n' | grep -n -E '"-lm"|"s45m.o"|as-needed' (exit=0) =====
26:"-lm"
27:"s45m.o"
29:"--as-needed"
31:"--no-as-needed"
34:"--as-needed"
36:"--no-as-needed"
```

**왜 그런가**

- ★★★ **다른 것은 ld 가 아니라 드라이버가 넘긴 옵션**이다 — gcc 는 **`--as-needed` 를 17 번째 인자로 `-lm`(38 번째)보다 앞에** 넘긴다. 그 아래의 `-lm` 은 「그때까지 필요한 게 있을 때만」 남는데, 아직 `s45m.o` 를 안 읽었으니 **버려진다.**
- ★★ **clang 은 `--as-needed` 를 `-lm`(26 번째) 뒤**에만 넘긴다(`libgcc` 둘레) — `-lm` 은 순서와 무관하게 남는다.
- ★★ 두 드라이버가 부르는 ld 는 **같은 판**이다:

```text
===== gcc -std=c17 -c s45n.c -o s45n.o && gcc -Wl,--version s45n.o -o x 2>&1 | grep '^GNU ld'; clang -Wl,--version s45n.o -o x 2>&1 | grep '^GNU ld' (exit=0) =====
GNU ld (GNU Binutils for Ubuntu) 2.42
GNU ld (GNU Binutils for Ubuntu) 2.42
```

### 4. 약한 심볼 — **`hook` 만: 주소 널 · `-1` · `s45w2` 를 더하면 `5` · `level` 혼자 `1` · 강한 정의를 더하면 `2`** ★★

**출력**

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && gcc s45w1.o -o x ; ./x (cc exit=0 · run exit=0) =====
hook 주소가 널인가 = 1
hook() = -1
```

```text
===== gcc -std=c17 -c s45w1.c -o s45w1.o && gcc -std=c17 -c s45w2.c -o s45w2.o && gcc s45w1.o s45w2.o -o x ; ./x (cc exit=0 · run exit=0) =====
hook 주소가 널인가 = 0
hook() = 5
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc s45w3.o -o x ; ./x (cc exit=0 · run exit=0) =====
level() = 1
```

```text
===== gcc -std=c17 -c s45w3.c -o s45w3.o && gcc -std=c17 -c s45w4.c -o s45w4.o && gcc s45w3.o s45w4.o -o x ; ./x (cc exit=0 · run exit=0) =====
level() = 2
```

**왜 그런가**

- ★★★ **약한 선언은 정의가 없어도 링크된다 — 주소가 널이다.** 널 검사(`hook ? hook() : -1`)가 없었으면 **널 함수 포인터 호출**이다.
- ★★ **강한 정의가 오면 그쪽이 쓰인다** — `hook() = 5` · `level() = 2`.
- ★★★ **약한 정의 + 강한 정의는 `multiple definition` 이 아니다** — 약한 쪽이 **말없이 진다.** 경고도 없다(`cc exit=0`).

### 5. 세 판의 문구 — **끝 줄은 드라이버의 것(`collect2` · `clang: error`) · gold 는 한 줄 문법에 `error:` · `previous definition here`** ★★

**출력**

```text
===== gcc -std=c17 -c s45u.c -o s45u.o && gcc s45u.o -o x (cc exit=1) =====
/usr/bin/ld: s45u.o: in function `main':
s45u.c:(.text+0x13): undefined reference to `area'
collect2: error: ld returned 1 exit status
```

```text
===== clang -std=c17 -c s45u.c -o s45u.o && clang s45u.o -o x (cc exit=1) =====
/usr/bin/ld: s45u.o: in function `main':
s45u.c:(.text+0x1a): undefined reference to `area'
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== gcc -std=c17 -c s45u.c -o s45u.o && gcc -fuse-ld=gold s45u.o -o x (cc exit=1) =====
s45u.o:s45u.c:function main:(.text+0x13): error: undefined reference to 'area'
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45h1.c -o s45h1.o && gcc -std=c17 -c s45h2.c -o s45h2.o && gcc s45h1.o s45h2.o -o x (cc exit=1) =====
/usr/bin/ld: s45h2.o: in function `scale':
s45h2.c:(.text+0x0): multiple definition of `scale'; s45h1.o:s45h1.c:(.text+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== gcc -std=c17 -c s45h1.c -o s45h1.o && gcc -std=c17 -c s45h2.c -o s45h2.o && gcc -fuse-ld=gold s45h1.o s45h2.o -o x (cc exit=1) =====
/usr/bin/ld.gold: error: s45h2.o: multiple definition of 'scale'
/usr/bin/ld.gold: s45h1.o: previous definition here
collect2: error: ld returned 1 exit status
```

**왜 그런가**

- ★★ **`/usr/bin/ld:` 로 시작하는 줄은 gcc 판과 clang 판이 같다**(오프셋 `+0x13` 대 `+0x1a` 만 다르다 — 목적 파일이 다르다). **끝 줄만** 드라이버가 찍는다 — gcc 는 **`collect2`**(gcc 가 ld 를 부르는 중간 단계), clang 은 **`clang: error: linker command failed`**.
- ★★ **gold 는 「파일:소스:함수:(오프셋): error:」 한 줄**이고, `multiple definition` 은 **`previous definition here`** 로 앞선 정의를 가리킨다. **같은 것은 이름 · 종류 · 파일**, 다른 것은 **문법**이다.
- ★ 그래서 **문구를 grep 하는 스크립트는 링커를 바꾸면 깨진다** — `undefined reference` 라는 낱말은 둘 다 있지만 줄의 모양이 다르다.

### 6. 문구에서 원인으로 — **`undefined reference` 여섯 후보는 `nm` 의 글자로 · `multiple definition` 은 문구가 두 파일을 다 준다** ★★★

- ★★★ **`undefined reference to 'X'` 의 후보와 `nm` 창**
  - **정의 없음** — `nm *.o | grep X` 에 **`U X` 만**.
  - **`static` 정의** — 정의 파일에 **`t X`**.
  - **이름 오타** — 정의 파일에 **비슷한 이름의 `T`**.
  - **C++ 로 컴파일** — `nm -C` 로 보면 **`T X(인자…)`** · 원래 이름은 `_Z…`.
  - **라이브러리 순서** — `nm libfoo.a` 에 `T X` 가 **있는데** 실패 → **링크 명령**(`-###`)을 본다.
  - **`main` 이 없음** — 문구가 **`_start`** 를 가리키고 내 파일에 `main` 이 없다.
- ★★ **`multiple definition` 은 「정의가 둘」 하나뿐** — 문구가 **두 파일을 다** 준다(`s45h2.o` · `first defined here … s45h1.o`). 남는 질문은 「**두 파일이 같은 헤더를 include 했나, 같은 이름을 각자 정의했나**」 둘이다.

### 7. C++ 로 컴파일한 정의 — **정의는 `_Z3addii` 라는 다른 이름으로 있다 · `extern "C"` 는 정의 쪽에** ★★

**출력**

```text
===== g++ -std=c++17 -c s45x.cpp -o s45x.o && gcc -std=c17 -c s45xc.c -o s45xc.o && gcc s45x.o s45xc.o -o x (cc exit=1) =====
/usr/bin/ld: s45xc.o: in function `main':
s45xc.c:(.text+0x13): undefined reference to `add'
collect2: error: ld returned 1 exit status
```

```text
===== g++ -std=c++17 -c s45xe.cpp -o s45xe.o && gcc -std=c17 -c s45xc.c -o s45xc.o && gcc s45xe.o s45xc.o -o x && ./x && nm s45xe.o (exit=0) =====
0000000000000000 T add
```

**왜 그런가**

- ★★★ **C++ 은 함수 이름에 인자 타입을 박는다**(`add(int, int)` → `_Z3addii`). C 쪽 `s45xc.o` 는 **`U add`** 를 찾는데 **`T add` 가 아무 데도 없다.**
- ★★ **`extern "C"` 를 C++ 쪽 정의에 붙이면** 맹글링을 끄고 `T add` 가 된다 — 링크 성공 · `./x` `exit=0` · `nm` 이 `T add`.
- ★ 실무에서는 **헤더의 선언을 `#ifdef __cplusplus` / `extern "C" {` 로 감싸** C 와 C++ 이 같은 헤더를 쓴다 — 이 편은 **던지지 않았다.**

### 8. 라이브러리 순서의 두 이유 — **정적은 「한 번 훑기」, `libm` 은 「`--as-needed` 아래에서만」 — 같은 모양, 다른 원인** ★★

- ★★ **정적 라이브러리(6 · 7 줄)** — ld 는 `.a` 를 만났을 때 **그때까지 풀리지 않은 이름**만 꺼낸다. 앞에 두면 꺼낼 것이 없다. **두 드라이버 다 실패**했다(격자 · `45-e6-clang`).

```text
===== gcc -std=c17 -c s45l.c -o s45l.o && ar rcs libs45.a s45l.o && gcc -std=c17 -c s45lm.c -o s45lm.o && clang -L. -ls45 s45lm.o -o x (cc exit=1) =====
/usr/bin/ld: s45lm.o: in function `main':
s45lm.c:(.text+0x9): undefined reference to `lib_value'
clang: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★ **공유 라이브러리(3번)** — 공유 라이브러리는 **통째로 링크에 남는 것이 기본**이라 원래는 순서를 안 탄다. **`--as-needed` 가 켜진 구간에서만** 「그때 필요 없으면 버린다」가 되어 **정적과 같은 모양**이 된다.
- ★★ **「`-l` 은 뒤에」 한 규칙이면 두 경우가 다 풀린다** — 대가는 **이유가 가려진다**는 것이다. 드라이버를 바꿨더니 **되던 틀린 순서가 깨지는** 일(clang → gcc)을 규칙만 외운 쪽은 설명하지 못한다.

### 9. 약한 심볼의 약속 — **「링크가 된다」까지 · 정의가 있다는 약속은 없다 · GNU 확장** ★★

- ★★ **약속하는 것** — 정의가 없어도 **링크가 끝난다** · 강한 정의가 있으면 **그것이 쓰인다.**
- ★★★ **약속하지 않는 것** — **정의가 있다는 것**(주소가 널일 수 있다) · **어느 정의가 이겼는지 알려 주는 것**(경고 0).
- ★ **표준 C 가 아니다** — `__attribute__((weak))` 는 GNU 확장이고 ELF 의 약한 바인딩에 기댄다.

### 10. 다섯 층 — **표준은 「정의는 하나」까지 · 문구·글자·순서·약한 심볼은 전부 툴체인 · `-c` 의 침묵은 「컴파일러는 모른다」의 증거** ★★★

| 층 | 이 주제에서 |
|---|---|
| ★★ **표준** | ★★ 외부 링크 식별자의 정의는 **정확히 하나** · 내부 링크는 다른 번역 단위에서 안 보인다 · `main` |
| ★ **구현 정의** | ★ 외부 이름의 유효 글자 수 |
| ★★★ **컴파일러·링커 구현** | ★★★ **에러 문구 · `nm` 글자 · 정적 라이브러리 순서 규칙 · `--as-needed`(Ubuntu gcc) · 약한 심볼 · 맹글링** |
| ★★ **UB** | ★ 정의가 없거나 둘인 프로그램(이 판은 링커가 전부 잡았다) · 약한 선언의 널 호출 |

- ★★★ **`-c` 가 전부 경고 없이 통과한다는 것은 「컴파일러는 한 번역 단위만 본다」는 뜻이다** — 정의의 개수는 **링커만** 센다. 이 주제의 사고는 **컴파일 창에서 원리상 안 보인다.**

### 11. 경계 — **헤더 배치는 44 · `inline` 은 39 · 링크 규칙은 29 · 템플릿은 C++ 35** ★

- **헤더에 무엇을 두나**(배치 격자 14 × 5)는 [44번 형제](../44-headers-and-separate-compilation/), **`inline` 의 링크**는 [39번 형제](../39-inline-and-c-inline-rules/), **`static`/`extern` 링크 규칙**은 [29번 형제](../29-scope-and-linkage-static-extern/)가 정본이다.
- ★ **C++ 템플릿 인스턴스화 링크 에러**는 [C++ 35 — 인스턴스화 · 헤더 배치 · 에러 읽기](../../../cpp/syntax/35-instantiation-header-placement-and-reading-errors/)가 다룬다.
- ★ 이 편이 **끝까지 책임지는 것** — **문구 → `nm` → 원인** 표 · **순서가 결과를 바꾸는 두 이유** · **링크 성공이 보장하지 않는 것**(약한 심볼).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s45u.c` · `s45h*.c` · `s45s*.c` · `s45t*.c` · `s45x.cpp` + `s45xc.c` · `s45l.c` + `s45lm.c` · `s45n.c` · `s45w*.c` | ★★★ **역추적 격자 30칸 · 9 / 30 · 0 / 10 · 0 / 10** · `nm` 열 | 30 |
| 같은 파일 | ★★ 문구 블록(ld.bfd 7 · clang 2 · gold 2) · `nm` 블록 5 · 실행 4 | 11 · 5 · 4 |
| `s45xe.cpp` | ★ `extern "C"` 로 고친 판 | 1 |
| `s45m.c` | ★★ `-lm` 격자 4칸 · `-###` 둘 | 4 · 2 |
| — | ★ ld 판 · `lld` 판별 | 4 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **이 편의 블록은 정규화 없이 전부 동일**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **3번** — Ubuntu gcc 의 `--as-needed` 기본값. 다른 배포판·다른 드라이버에서는 네 칸이 다를 수 있다.
- ★★ **5번의 문구 모양** · **2번의 `nm` 글자** · **4번의 약한 심볼**(GNU 확장 · ELF).

**정의가 정확히 하나여야 한다는 것 · 내부 링크가 다른 번역 단위에서 안 보인다는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — **`lld`**(이 머신에 없다 — 판별 블록).
- **안 돌려 본 것** — `--start-group` · `--trace-symbol` · `-shared` 의 실행 시점 해석.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **3번** — 배포판이 드라이버 기본값을 바꾸면 갈린다.
- ★ **5번** — 링커 판이 오르면 문구가 바뀔 수 있다.
