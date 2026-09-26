# cpp/syntax/25 — 정적 멤버·`inline` 변수(C++17) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **GNU ld 2.42** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다(소스는 질문 파일과 같다).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · `.text+0x…` 오프셋 · `nm` 의 주소 칸**이다.\
> 근거로 쓰는 것은 다음이다 — **링크가 되나(`cc exit`) · 무엇의 이름이 불렸나 · `nm` 글자 · 초기화 로그의 순서 · 격자의 O/X · `__cxa_guard` 호출 수**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **컴파일은 통과 · 링크에서 `multiple definition of 'Cfg::count'`** · 글자는 **`B`**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex (cc exit=1) =====
/usr/bin/ld: cfg_b.o:(.bss+0x0): multiple definition of `Cfg::count'; cfg_a.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && clang++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && clang++ cfg_a.o cfg_b.o -o ex (cc exit=1) =====
/usr/bin/ld: cfg_b.o:(.bss+0x0): multiple definition of `Cfg::count'; cfg_a.o:(.bss+0x0): first defined here
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -c cfg_b.cpp -o cfg_b.o && nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 B Cfg::count

cfg_b.o:
                 U Cfg::bump()
0000000000000000 B Cfg::count
0000000000000000 T main
                 U printf
```

**왜 그런가**

- ★★★ **`int Cfg::count = 0;` 이 헤더에 있어** 포함한 두 번역 단위가 **각자 정의를 하나씩** 가졌다. `B`(이 파일이 자리를 가진 정의)가 **둘**이라 링커가 거부한다.
- ★ 컴파일러는 **한 번역 단위씩만** 보므로 이 사고를 볼 수 없다 — **링커가 처음 보는 자리**다.

### 2. ★★★ **링크 O · `count = 12`** · 글자는 **g++ `u` · clang++ `V`**(다르다)

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && g++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
count = 12
===== nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 u Cfg::count

cfg_b.o:
                 U Cfg::bump()
0000000000000000 u Cfg::count
0000000000000000 T main
                 U printf
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && clang++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
count = 12
===== nm -C cfg_a.o cfg_b.o (exit=0) =====

cfg_a.o:
0000000000000000 T Cfg::bump()
0000000000000000 V Cfg::count

cfg_b.o:
0000000000000000 r .L.str
                 U Cfg::bump()
0000000000000000 V Cfg::count
0000000000000000 T main
                 U printf
```

**왜 그런가**

- ★★★ **`inline` 변수는 여러 번역 단위의 같은 정의를 하나로 합친다** — 두 파일이 같은 `count` 를 봐서 `2 + 10 = 12`.
- ★★ **`u`(GNU 유일 전역)와 `V`(약한 객체)는 표시 방식이 다를 뿐 뜻이 같다** — 「여럿이어도 하나로」. **글자는 구현 정의 칸**이다.

### 3. ★★ **두 컴파일러 다 `cc exit=0 · run exit=0`** · 경고 **2**(번역 단위마다 1) · **`-pedantic-errors`** 로 에러 1 · 1

**출력**

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_a.cpp -o cfg_a.o && g++ -std=c++14 -Wall -Wextra -pedantic -DASK_INLINE -c cfg_b.cpp -o cfg_b.o && g++ cfg_a.o cfg_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
In file included from cfg_a.cpp:2:
cfg.h:5:12: warning: inline variables are only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^~~~~~
In file included from cfg_b.cpp:3:
cfg.h:5:12: warning: inline variables are only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
    5 |     static inline int count = 0;
      |            ^~~~~~
count = 12
```

```text
===== echo "g++   -std=c++14 -pedantic-errors cfg_a.cpp 에러 $(g++ -std=c++14 -Wall -Wextra -pedantic-errors -DASK_INLINE -c cfg_a.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
g++   -std=c++14 -pedantic-errors cfg_a.cpp 에러 1
===== echo "clang -std=c++14 -pedantic-errors cfg_a.cpp 에러 $(clang++ -std=c++14 -Wall -Wextra -pedantic-errors -DASK_INLINE -c cfg_a.cpp -o /dev/null 2>&1 | grep -c 'error:')" (exit=0) =====
clang -std=c++14 -pedantic-errors cfg_a.cpp 에러 1
```

```text
===== bash cfg-grid.sh (exit=0) =====
컴파일러 표준  cfg.h            링크     경고 nm(cfg_a.o 의 count)
g++      c++14   (클래스 밖 정의) X          0      B
g++      c++14   -DASK_INLINE     O count = 12 2      u
g++      c++17   (클래스 밖 정의) X          0      B
g++      c++17   -DASK_INLINE     O count = 12 0      u
clang++  c++14   (클래스 밖 정의) X          0      B
clang++  c++14   -DASK_INLINE     O count = 12 2      V
clang++  c++17   (클래스 밖 정의) X          0      B
clang++  c++17   -DASK_INLINE     O count = 12 0      V
링크까지 간 칸 4 / 8 · 그중 경고가 난 칸 2
```

**왜 그런가**

- ★★ **C++14 에서 `inline` 변수는 ill-formed** 인데 두 컴파일러가 **확장으로 받는다.** 격자의 `링크까지 간 칸 4 / 8 · 그중 경고가 난 칸 2` 가 그것이다.
- ★ **「`-std=` 는 강제가 아니라 기본값 선택」** — [24번](../24-explicit-and-converting-constructors/) (7)의 `explicit(bool)` 과 같은 집안이다.

### 4. ★★★ **`-O0` 에서만 깨진다** — C++14 는 A·B 둘 다, **C++17 은 A(`static const`)만** · `-O2` 는 **0칸** · `nm` 은 **`U K::A` · `u`/`V K::B`**

**출력**

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -DASK_REF_B -c odr01.cpp -o odr01.o && g++ odr01.o -o ex (cc exit=1) =====
/usr/bin/ld: odr01.o: warning: relocation against `_ZN1K1BE' in read-only section `.text'
/usr/bin/ld: odr01.o: in function `main':
odr01.cpp:(.text+0x4a): undefined reference to `K::B'
/usr/bin/ld: warning: creating DT_TEXTREL in a PIE
collect2: error: ld returned 1 exit status
```

```text
===== bash odr-grid.sh (exit=0) =====
컴파일러 표준  -O   탐침       링크
g++      c++14   -O0  (값만)     O
g++      c++14   -O2  (값만)     O
g++      c++14   -O0  -DASK_REF_A  X undefined
g++      c++14   -O2  -DASK_REF_A  O
g++      c++14   -O0  -DASK_REF_B  X undefined
g++      c++14   -O2  -DASK_REF_B  O
g++      c++17   -O0  (값만)     O
g++      c++17   -O2  (값만)     O
g++      c++17   -O0  -DASK_REF_A  X undefined
g++      c++17   -O2  -DASK_REF_A  O
g++      c++17   -O0  -DASK_REF_B  O
g++      c++17   -O2  -DASK_REF_B  O
clang++  c++14   -O0  (값만)     O
clang++  c++14   -O2  (값만)     O
clang++  c++14   -O0  -DASK_REF_A  X undefined
clang++  c++14   -O2  -DASK_REF_A  O
clang++  c++14   -O0  -DASK_REF_B  X undefined
clang++  c++14   -O2  -DASK_REF_B  O
clang++  c++17   -O0  (값만)     O
clang++  c++17   -O2  (값만)     O
clang++  c++17   -O0  -DASK_REF_A  X undefined
clang++  c++17   -O2  -DASK_REF_A  O
clang++  c++17   -O0  -DASK_REF_B  O
clang++  c++17   -O2  -DASK_REF_B  O
링크가 깨진 칸  -O0 6 / 12 · -O2 0 / 12
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && nm -C odr01.o | grep 'K::' (exit=0) =====
                 U K::A
0000000000000000 u K::B
===== clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && nm -C odr01.o | grep 'K::' (exit=0) =====
                 U K::A
0000000000000000 V K::B
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 -DASK_REF_A -DASK_REF_B -c odr01.cpp -o odr01.o && echo "-O2 에서 K:: 심볼 $(nm -C odr01.o | grep -c 'K::')개" (exit=0) =====
-O2 에서 K:: 심볼 0개
```

**왜 그런가**

- ★★★ **`std::max` 는 `const int&` 를 받는다** — 주소가 필요한 쓰임(**ODR 사용**)이라 **정의가 있어야** 한다. 클래스 안의 `= 7`·`= 9` 는 C++14 에서 **값만 알려 주는 선언**이다.
- ★★★ **C++17 은 `constexpr` 정적 멤버만 암묵 `inline`**(= 정의)으로 만든다 — 그래서 B 는 C++17 에서 되고 **A 는 여전히 깨진다.** `nm` 이 **`U`(어딘가에 있어야 함)** 와 **`u`/`V`(여기 있음)** 로 가른다.
- ★★ **`-O2` 는 `std::max` 를 펼쳐 참조를 지운다** — `K::` 심볼이 **0개**가 되어 아무것도 요구하지 않는다.

### 5. ★★★ **`42` 와 `0`** — 읽은 쪽이 본 값은 **0**(쓰레기가 아니다) · clang++ 도 **같다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && g++ -std=c++20 -Wall -Wextra -pedantic -c siof_use.cpp -o siof_use.o && g++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== g++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 0
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 0
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c siof_use.cpp -o siof_use.o && clang++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== clang++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 0
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 0
```

**왜 그런가**

- ★★★ **번역 단위 사이의 동적 초기화 순서는 미명시**다 — 이 판(GNU ld)은 **링크 명령 순서**를 따랐고, 그 순서만 바꿨더니 값이 갈렸다.
- ★★ **정적 저장소는 동적 초기화 전에 0 으로 채워진다** — 그래서 먼저 읽힌 `Config::base` 는 **0** 이다(로그 `읽은 값 0`).
- ★ **두 컴파일러가 같은 링커를 부른다** — 「clang 에서도 같았다」는 **보장이 아니다.**

### 6. ★★ **두 순서 다 `42`** · 가드 호출 **2 · 2**(`-fno-threadsafe-statics` 면 **0 · 0**) · 이미 초기화됐으면 **가드 바이트 검사 뒤 바로 `ret`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c siof_cfg.cpp -o siof_cfg.o && g++ -std=c++20 -Wall -Wextra -pedantic -DASK_LAZY -c siof_use.cpp -o siof_use.o && g++ siof_cfg.o siof_use.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [main] Report::doubled = 42
===== g++ siof_use.o siof_cfg.o -o ex && ./ex (cc exit=0 · run exit=0) =====
    [siof_cfg] read_base() 가 돈다
    [siof_use] Report::doubled 를 초기화한다 — 읽은 값 21
    [siof_cfg] read_base() 가 돈다
    [main] Report::doubled = 42
```

```text
===== echo "g++   -O2                        __cxa_guard 호출 $(g++ -std=c++20 -O2 -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
g++   -O2                        __cxa_guard 호출 2
===== echo "g++   -O2 -fno-threadsafe-statics __cxa_guard 호출 $(g++ -std=c++20 -O2 -fno-threadsafe-statics -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
g++   -O2 -fno-threadsafe-statics __cxa_guard 호출 0
===== echo "clang -O2                        __cxa_guard 호출 $(clang++ -std=c++20 -O2 -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
clang -O2                        __cxa_guard 호출 2
===== echo "clang -O2 -fno-threadsafe-statics __cxa_guard 호출 $(clang++ -std=c++20 -O2 -fno-threadsafe-statics -S -o - siof_cfg.cpp | grep -cE 'call[q]?[[:space:]]+__cxa_guard_(acquire|release)')" (exit=0) =====
clang -O2 -fno-threadsafe-statics __cxa_guard 호출 0
```

```text
===== g++ -std=c++20 -O2 -S -o - siof_cfg.cpp | awk '/^_Z9lazy_basev:/,/cfi_endproc/' | grep -E '_ZGV|__cxa_guard|^\.L[0-9]+:|testb|je[[:space:]]|jne[[:space:]]|ret$|movl[[:space:]]+\$21' (exit=0) =====
	movzbl	_ZGVZ9lazy_basevE1b(%rip), %eax
	testb	%al, %al
	je	.L16
	ret
.L16:
	leaq	_ZGVZ9lazy_basevE1b(%rip), %rbx
	call	__cxa_guard_acquire@PLT
	jne	.L17
	ret
.L17:
	movl	$21, _ZZ9lazy_basevE1b(%rip)
	call	__cxa_guard_release@PLT
	ret
.L6:
```

**왜 그런가**

- ★★★ **함수 지역 `static` 은 처음 부를 때 초기화된다** — `Report::doubled` 가 먼저 초기화되든 나중이든 **그 순간 `b` 를 짓는다.**
- ★★ **C++11 부터 그 초기화는 스레드 안전**해야 하고, 이 구현은 **`__cxa_guard_acquire`/`release`** 로 산다. 빠른 길은 `movzbl _ZGV… ; testb ; je` — **가드 바이트 한 번 읽기**다.
- ★ **시간은 재지 않았다** — 명령의 **모양**만이 근거다.

### 7. ★★★ **아니다 — 진단이 필요 없는 ill-formed** 이다 · `-pedantic-errors` 로도 **안 잡힌다**

**출력**

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic-errors -O2 -DASK_REF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::B, x) = 9
===== clang++ -std=c++14 -Wall -Wextra -pedantic-errors -O2 -DASK_REF_B odr01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
값으로 읽기  A+0=7 B+0=9
std::max(K::B, x) = 9
```

**왜 그런가**

- ★★★ **ODR 사용한 변수에 정의가 없으면 프로그램은 ill-formed 이고, 표준은 그 진단을 요구하지 않는다.** `-O2` 는 참조를 지워 **링커가 모르게** 만들었을 뿐이다.
- ★★ **앞 편들의 항목(`static operator()`·`explicit(bool)`·C++14 `inline`)은 「컴파일러가 알면서 확장으로 받는 것」이라** `-pedantic-errors` 가 잡았다. **이것은 컴파일러가 볼 의무가 없는 것**이라 **어느 플래그도** 안 잡는다 — `-O0` 링크만이 잡았다.

### 8. ★ **`g++ -fcommon` 은 `multiple definition`(`B t`)** · **`gcc -x c -fcommon` 은 링크 O(`C t`)**

**출력**

```cpp
/* tent1.cpp */
int t;
int get1() { return t; }
```

```cpp
/* tent2.cpp */
int t;
int get1();
int main() { t = 5; return get1() - 5; }
```

```text
===== g++ -std=c++17 -fcommon -c tent1.cpp -o tent1.o && g++ -std=c++17 -fcommon -c tent2.cpp -o tent2.o && g++ tent1.o tent2.o -o ex (cc exit=1) =====
/usr/bin/ld: tent2.o:(.bss+0x0): multiple definition of `t'; tent1.o:(.bss+0x0): first defined here
collect2: error: ld returned 1 exit status
===== nm tent1.o (exit=0) =====
0000000000000000 T _Z4get1v
0000000000000000 B t
===== gcc -x c -std=c17 -fcommon -c tent1.cpp -o tent1c.o && gcc -x c -std=c17 -fcommon -c tent2.cpp -o tent2c.o && gcc tent1c.o tent2c.o -o ex && ./ex; echo "run=$?"; nm tent1c.o (exit=0) =====
run=0
0000000000000000 T get1
0000000000000004 C t
```

**왜 그런가**

- ★★ **C++ 에는 잠정 정의가 없다** — `int t;` 는 그냥 정의(`B`)라 `-fcommon` 이 공용(`C`)으로 만들 자리가 없다.
- ★ C 에서는 **초기자 없는 파일 스코프 선언이 잠정 정의**라 `-fcommon` 이 합친다 — C 갈래 29번 (5).

### 9. ★★ **암묵 `inline` 은 `constexpr` 에만 붙도록 C++17 이 정했다** · 중복 정의는 **`-Wdeprecated` 라야** 경고 1 · 1

**출력**

```text
===== echo "g++   -std=c++17 기본 플래그 경고 $(g++ -std=c++17 -Wall -Wextra -pedantic -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:') · -Wdeprecated 경고 $(g++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
g++   -std=c++17 기본 플래그 경고 0 · -Wdeprecated 경고 1
===== echo "clang -std=c++17 기본 플래그 경고 $(clang++ -std=c++17 -Wall -Wextra -pedantic -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:') · -Wdeprecated 경고 $(clang++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null 2>&1 | grep -c 'warning:')" (exit=0) =====
clang -std=c++17 기본 플래그 경고 0 · -Wdeprecated 경고 1
===== g++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null (cc exit=0) =====
odr01.cpp:15:15: warning: redundant redeclaration of ‘constexpr’ static data member ‘K::B’ [-Wdeprecated]
   15 | constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
      |               ^
odr01.cpp:8:26: note: previous declaration of ‘K::B’
    8 |     static constexpr int B = 9;
      |                          ^
===== clang++ -std=c++17 -Wall -Wextra -pedantic -Wdeprecated -DASK_DEF_B -c odr01.cpp -o /dev/null (cc exit=0) =====
odr01.cpp:15:18: warning: out-of-line definition of constexpr static data member is redundant in C++17 and is deprecated [-Wdeprecated-redundant-constexpr-static-def]
   15 | constexpr int K::B;       // 클래스 밖 정의 — 초기자 없이
      |                  ^
1 warning generated.
```

**왜 그런가**

- ★★ **`constexpr` 정적 멤버는 반드시 클래스 안에서 초기자를 갖는다** — 그래서 그 자리를 정의로 삼아도 모자람이 없다. **`static const` 는 클래스 밖에서 초기화할 수도 있는 선언**이라 같은 규칙을 붙이지 않았다(내 추론 — 판 격자는 실측).
- ★ **C++17 의 `constexpr int K::B;` 는 쓸모없는 중복이고 폐기 예정**이다. **`-Wall -Wextra -pedantic` 으로는 0 · 0** — 옛 코드를 올려도 **말이 없다.**

### 10. ★ **정적 저장소가 먼저 0 으로 채워지기 때문**이다 · `std::string` 이면 **생성 전 객체를 쓰는 UB** 가 된다(이 문서는 던지지 않았다)

- ★ 5번의 `0` 은 **정의된 값**(0 초기화)이다 — 메모리 오류가 없으니 **ASan 이 볼 것이 없다**(부적용인 창).
- ★ **비자명 생성자 타입**은 0 으로 채워진 바이트가 **유효한 객체가 아니다** — 그때는 UB 이고 ASan 창이 열릴 수 있다. **안 돌려 본 것**이다.

### 11. 다른 주제와 잇기

- ★★★ **C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 29번**([`29-scope-and-linkage-static-extern/`](../../../c/syntax/29-scope-and-linkage-static-extern/)) — **같은 이름의 정의가 여러 파일에 있는 문제.** C 는 **컴파일러 확장 `-fcommon`**(잠정 정의 · `C`)으로, C++17 은 **언어 문법 `inline`**(`u`/`V`)으로 푼다.
- ★ **[14번](../14-destructors-and-deterministic-destruction/) (3)** — `lazy()` 를 두 번 불렀는데 생성 로그가 한 줄.
- ★ 목록의 **55번 주제** — 모듈·ODR·헤더 배치.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `cfg.h` + `cfg_a/b.cpp` 클래스 밖 정의 | g++ · clang C++17 링크 각 1회 + `nm` | ★★★ **`multiple definition`** · `B` 둘 |
| 같은 것 `-DASK_INLINE` | g++ · clang C++17 링크·실행 각 1회 + `nm` | ★★★ **`count = 12`** · **`u` · `V`** |
| `cfg-grid.sh` | 두 컴파일러 × 두 판 × 두 헤더 = 8칸 | ★★ **링크 4 / 8 · 경고 2칸** |
| C++14 `inline` + `-pedantic-errors` | g++ · clang 각 2회 | ★★ `cc exit=0` → **에러 1 · 1** |
| `odr01.cpp` + `odr-grid.sh` | 두 컴파일러 × 두 판 × 두 `-O` × 세 탐침 = 24칸 | ★★★ **`-O0` 6 / 12 · `-O2` 0 / 12** |
| `odr01.cpp` `nm` · 클래스 밖 정의 · `-Wdeprecated` · `-pedantic-errors -O2` | 각 1\~2회 | ★★ **`U` · `u`/`V`** · 정의 더하면 O · 경고 **0 → 1** · pedantic 도 **`cc exit=0`** |
| `siof_*.cpp` 링크 순서 | g++ · clang 각 두 순서 + `-DASK_LAZY` 두 순서 | ★★★ **`42` · `0`** → lazy **`42` · `42`** |
| `constinit` · 가드 세기 | g++ · clang 각 1회 · `-O2 -S` 4판 | ★★ **에러** · 가드 **2 · 0 · 2 · 0** |
| `tent1/2.cpp` | g++ `-fcommon` · gcc `-x c -fcommon` | ★ **`B` 깨짐 · `C` 링크** |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · GNU ld 2.42)에서만** 그렇다.

- ★★★ **링크 순서가 초기화 순서를 정한 것** — 링커의 관찰이다.
- ★★ **`nm` 글자 `u`·`V`** · **가드를 `__cxa_guard_*` 로 구현한 것**(Itanium C++ ABI) · **`-O2` 가 `std::max` 를 펼친 것.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **정의가 둘이면 ill-formed** · **ODR 사용에는 정의가 필요** · **C++17 `inline` 변수는 하나로 합쳐진다** · **`constexpr` 정적 멤버는 C++17 부터 암묵 `inline`** · **번역 단위 사이의 동적 초기화 순서는 미명시** · **함수 지역 `static` 초기화는 스레드 안전.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **비자명 생성자 타입(`std::string`)의 초기화 순서 UB** · ★ **정적 파괴 순서 문제** · ★ **LTO 판에서의 초기화 순서** · ★ **`constinit` 이 받아 주는 판.**
- ★ **「부적용인 창」** — ASan(0 은 정의된 값) · `<type_traits>`(정의 위치는 타입 성질이 아니다).
- ★ **cppreference 의 해당 쪽들을 이 배치에서 열지 못했다**(도구 한도) — 규칙은 전부 **던져서** 확인했고, 판 경계는 **컴파일러 경고의 문구**가 말한 것만 적었다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번** — 링커를 바꾸거나(lld·gold) LTO 를 켜면 순서가 바뀌는지.
- ★★ **4번의 `-O2` 칸** — 인라인 판단이 바뀌면 `-O2` 에서도 깨질 수 있다.
