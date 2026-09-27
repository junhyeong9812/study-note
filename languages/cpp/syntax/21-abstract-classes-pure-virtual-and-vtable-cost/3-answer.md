# cpp/syntax/21 — 추상 클래스·순수 가상·vtable 비용 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **javac 21.0.5** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 다.\
> **진단의 줄 번호는 그 파일 기준**이므로 **출력을 싣는 블록마다 그 출력을 낸 소스를 같은 자리에** 뒀다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **g++ 클래스 덤프의 주소** · **진단 문구** · **지역 레이블 이름**이다.\
> 근거로 쓰는 것은 다음이다 — **`call *`/`jmp *` 유무 · 부르는 심볼 이름 · `call` 이 사라졌나** · **격자의 칸** · **`sizeof`** · **`cc exit`/`run exit`** · **경고·에러 개수**.
> ★★★ **이 파일에는 「가상 호출이 느리다」는 문장이 한 줄도 없다** — 시간을 재지 않았다. 답은 **명령**으로 적는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **셋 다 에러**다 — 남은 이름을 나열하고, `Half` 목록에는 **`encode` 가 없다**

**출력**

```cpp
/* abs01.cpp */
// 순수 가상이 셋인 인터페이스 — 하나만 덮은 파생을 만들면 컴파일러가 남은 이름을 나열하나
struct Codec {
    virtual int  encode(int) const = 0;
    virtual int  decode(int) const = 0;
    virtual const char* name() const = 0;
    virtual ~Codec() = default;
};
struct Half : Codec {
    int encode(int x) const override { return x + 1; }        // 셋 중 하나만 덮었다
};

int main() {
    Codec c;                             // 1. 인터페이스 자체를 만든다
    Half h;                              // 2. 하나만 덮은 파생을 만든다
    Codec* p = new Half;                 // 3. new 로 만든다
    (void)c; (void)h; (void)p;
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 abs01.cpp -o ex (cc exit=1) =====
abs01.cpp: In function ‘int main()’:
abs01.cpp:13:11: error: cannot declare variable ‘c’ to be of abstract type ‘Codec’
   13 |     Codec c;                             // 1. 인터페이스 자체를 만든다
      |           ^
abs01.cpp:2:8: note:   because the following virtual functions are pure within ‘Codec’:
    2 | struct Codec {
      |        ^~~~~
abs01.cpp:3:18: note:     ‘virtual int Codec::encode(int) const’
    3 |     virtual int  encode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:4:18: note:     ‘virtual int Codec::decode(int) const’
    4 |     virtual int  decode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:5:25: note:     ‘virtual const char* Codec::name() const’
    5 |     virtual const char* name() const = 0;
      |                         ^~~~
abs01.cpp:14:10: error: cannot declare variable ‘h’ to be of abstract type ‘Half’
   14 |     Half h;                              // 2. 하나만 덮은 파생을 만든다
      |          ^
abs01.cpp:8:8: note:   because the following virtual functions are pure within ‘Half’:
    8 | struct Half : Codec {
      |        ^~~~
abs01.cpp:4:18: note:     ‘virtual int Codec::decode(int) const’
    4 |     virtual int  decode(int) const = 0;
      |                  ^~~~~~
abs01.cpp:5:25: note:     ‘virtual const char* Codec::name() const’
    5 |     virtual const char* name() const = 0;
      |                         ^~~~
abs01.cpp:15:20: error: invalid new-expression of abstract class type ‘Half’
   15 |     Codec* p = new Half;                 // 3. new 로 만든다
      |                    ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ferror-limit=0 abs01.cpp -o ex (cc exit=1) =====
abs01.cpp:13:11: error: variable type 'Codec' is an abstract class
   13 |     Codec c;                             // 1. 인터페이스 자체를 만든다
      |           ^
abs01.cpp:3:18: note: unimplemented pure virtual method 'encode' in 'Codec'
    3 |     virtual int  encode(int) const = 0;
      |                  ^
abs01.cpp:4:18: note: unimplemented pure virtual method 'decode' in 'Codec'
    4 |     virtual int  decode(int) const = 0;
      |                  ^
abs01.cpp:5:25: note: unimplemented pure virtual method 'name' in 'Codec'
    5 |     virtual const char* name() const = 0;
      |                         ^
abs01.cpp:14:10: error: variable type 'Half' is an abstract class
   14 |     Half h;                              // 2. 하나만 덮은 파생을 만든다
      |          ^
abs01.cpp:4:18: note: unimplemented pure virtual method 'decode' in 'Half'
    4 |     virtual int  decode(int) const = 0;
      |                  ^
abs01.cpp:5:25: note: unimplemented pure virtual method 'name' in 'Half'
    5 |     virtual const char* name() const = 0;
      |                         ^
abs01.cpp:15:20: error: allocating an object of abstract class type 'Half'
   15 |     Codec* p = new Half;                 // 3. new 로 만든다
      |                    ^
3 errors generated.
```

**왜 그런가**

- ★★ **에러 3건 · `cc exit=1`** — 두 컴파일러 같다.
- ★★ **나열한다** — `Codec` 에 셋, `Half` 에 **`decode`·`name` 둘**. `encode` 는 덮었으니 **빠진다.**
- ★ **3번에는 목록이 다시 안 나온다** — 같은 타입의 목록은 한 번만 보였다(관찰).

### 2. ★★ **1**(본체가 있어도 추상) — `(2)` 는 **`Stamp::log` → `Logger::log`**, `(3)` 은 **`Logger::log` 만**

**출력**

```cpp
/* abs02.cpp */
// 순수 가상에 본체를 준다 — 그래도 추상인가, 그 본체는 누가 부르나
#include <cstdio>
#include <type_traits>

struct Logger {
    virtual void log(const char* m) const = 0;       // 순수 가상 — 파생이 반드시 덮는다
    virtual ~Logger() = default;
};
void Logger::log(const char* m) const {              // ★ 그런데 본체가 있다(클래스 밖에서 정의)
    std::printf("      Logger::log  [기본 형식] %s\n", m);
}

struct Stamp : Logger {
    void log(const char* m) const override {
        std::printf("      Stamp::log   앞에 도장을 찍고 ->\n");
        Logger::log(m);                              // ★ 기반의 본체를 이름으로 부른다
    }
};

int main() {
    std::printf("(1) is_abstract<Logger> = %d · is_abstract<Stamp> = %d\n",
                (int)std::is_abstract_v<Logger>, (int)std::is_abstract_v<Stamp>);
    Stamp s;
    const Logger& r = s;
    std::printf("(2) r.log(\"hi\") — 가상 호출\n");
    r.log("hi");
    std::printf("(3) r.Logger::log(\"hi\") — 이름으로 부르면 가상 디스패치가 꺼진다\n");
    r.Logger::log("hi");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) is_abstract<Logger> = 1 · is_abstract<Stamp> = 0
(2) r.log("hi") — 가상 호출
      Stamp::log   앞에 도장을 찍고 ->
      Logger::log  [기본 형식] hi
(3) r.Logger::log("hi") — 이름으로 부르면 가상 디스패치가 꺼진다
      Logger::log  [기본 형식] hi
```

**왜 그런가**

- ★★★ **본체가 있어도 추상**이다 — 순수 가상은 「파생이 반드시 덮는다」는 약속이다.
- ★★ **본체는 이름으로만 불린다** — `(3)` 의 `r.Logger::log` 는 **가상 디스패치를 끄므로** `Stamp::log` 가 안 불린다.
- ★ **한 줄로 쓰면 문법 에러**다 — 본체는 **클래스 밖에서** 준다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -fmax-errors=0 abs06.cpp -o ex (cc exit=1) =====
abs06.cpp:3:22: error: pure-specifier on function-definition
    3 |     virtual void f() = 0 { }             // 순수 지정 + 본체
      |                      ^
```

### 3. ★★★ **g++ 는 링크에서, clang 은 실행에서** 멈춘다 — 경고는 **양쪽 1건**, `Derived::init` 은 **0회**

**출력**

```cpp
/* abs03.cpp */
// 생성자 안에서 순수 가상을 「직접」 부른다 — 19편의 「생성자 속 가상 호출은 기반 것」의 극단
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
    virtual void init() = 0;                          // 순수 가상 — 본체가 없다
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() { Derived d; }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o && g++ abs03.o -o ex (cc exit=1) =====
abs03.cpp: In constructor ‘Base::Base()’:
abs03.cpp:5:83: warning: pure virtual ‘virtual void Base::init()’ called from constructor
    5 |     Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
      |                                                                               ~~~~^~
/usr/bin/ld: abs03.o: in function `Base::Base()':
abs03.cpp:(.text._ZN4BaseC2Ev[_ZN4BaseC5Ev]+0x49): undefined reference to `Base::init()'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o && clang++ abs03.o -o ex && ./ex (cc exit=0 · run exit=134) =====
abs03.cpp:5:86: warning: call to pure virtual member function 'init' has undefined behavior; overrides of 'init' in subclasses are not available in the constructor of 'Base' [-Wcall-to-pure-virtual-from-ctor-dtor]
    5 |     Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
      |                                                                               ^
abs03.cpp:6:5: note: 'init' declared here
    6 |     virtual void init() = 0;                          // 순수 가상 — 본체가 없다
      |     ^
1 warning generated.
      Base() 가 init() 을 직접 부른다
pure virtual method called
terminate called without an active exception
```

**왜 그런가**

- ★★★ **g++ 는 생성자 안의 `init()` 을 `Base::init` 직접 호출로 만든다** — 그 본체가 없으니 **`undefined reference to 'Base::init()'`**.
- ★★★ **clang 은 vtable 칸을 거쳐 부른다** — 생성 중인 객체의 vtable 은 **`Base` 의 것**이고, 그 칸에 **`__cxa_pure_virtual`** 이 있다 → **`pure virtual method called` · `run exit=134`**.
- ★★ **둘 다 표준과 모순되지 않는다** — 생성자에서 순수 가상을 가상 호출하는 것은 **UB** 다(기준 소스).
- ★★ **경고는 양쪽 1건** — g++ `pure virtual … called from constructor` · clang `-Wcall-to-pure-virtual-from-ctor-dtor`.

### 4. ★★★ **경고 0건 · `run exit=134`** — 두 컴파일러 같다

**출력**

```cpp
/* abs04.cpp */
// 생성자 안에서 순수 가상을 「비가상 함수를 한 번 거쳐」 부른다
// 마커는 표준 오류로 찍는다 — terminate 로 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 setup() 을 부른다\n"); setup(); }
    void setup() { std::fprintf(stderr, "      setup() 이 init() 을 부른다\n"); init(); }  // 비가상 중간 다리
    virtual void init() = 0;
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() {
    std::fprintf(stderr, "(1) Derived 를 만든다\n");
    Derived d;
    std::fprintf(stderr, "(2) 여기까지 왔다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs04.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
(1) Derived 를 만든다
      Base() 가 setup() 을 부른다
      setup() 이 init() 을 부른다
pure virtual method called
terminate called without an active exception
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic abs04.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
(1) Derived 를 만든다
      Base() 가 setup() 을 부른다
      setup() 이 init() 을 부른다
pure virtual method called
terminate called without an active exception
```

```text
===== echo "abs03(직접)   g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o 2>&1 | grep -c 'warning:') · clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c abs03.cpp -o abs03.o 2>&1 | grep -c 'warning:')" (exit=0) =====
abs03(직접)   g++ 경고 1 · clang 경고 1
===== echo "abs04(한 다리) g++ 경고 $(g++ -std=c++20 -Wall -Wextra -pedantic -c abs04.cpp -o abs04.o 2>&1 | grep -c 'warning:') · clang 경고 $(clang++ -std=c++20 -Wall -Wextra -pedantic -c abs04.cpp -o abs04.o 2>&1 | grep -c 'warning:')" (exit=0) =====
abs04(한 다리) g++ 경고 0 · clang 경고 0
```

**왜 그런가**

- ★★★ **`setup()` 은 비가상**이라 컴파일러가 「생성자 안에서 부른다」를 **그 호출 자리에서 모른다** — `init()` 을 평범한 가상 호출로 만들고 **경고도 안 낸다.**
- ★★ **표준 출력으로 찍었다면 마커가 통째로 사라졌을 것**이다 — `abort()` 로 죽으면 stdout 버퍼가 flush 되지 않는다(19-A).\
  ★ 이 판에서는 **stdout 판을 따로 던지지 않았다** — 「사라졌을 것」은 규칙 19-A 에 기댄 추론이다.
- ★ **`pure virtual method called` 는 런타임 라이브러리(libsupc++)의 문구**다 — 컴파일러가 아니다. 두 컴파일러 다 libstdc++ 를 쓰므로 같다.

### 5. ★★★ 1번은 **`-O2` 에서도 간접** · 3·4·5번은 **`-O0` 에서 이미 직접** · 2번은 **g++ 만 추측 후 간접** · 8번은 **`call` 이 사라진다**

**출력**

```bash
# devirt-grid.sh
# 디버추얼라이제이션 격자 — devirt.cpp 의 탐침 여덟을 두 컴파일러 × -O0/-O2 로 어셈블리까지 내리고
# 함수마다 「간접 call/jmp」(call *…)·「f 나 g 를 이름으로 부르는 call/jmp」·「f 의 주소를 싣는 leaq」 개수를 센다
set -u -o pipefail
for cc in g++ clang++; do
  for opt in -O0 -O2; do
    echo "[$cc $opt]"
    $cc -std=c++20 $opt -S -fno-asynchronous-unwind-tables -fcf-protection=none -o devirt.s devirt.cpp || exit 1
    awk '
      /^t[0-9]_[a-z_]*:/        { name = $1; sub(":", "", name); ind = 0; dir = 0; adr = 0; next }
      name == ""                { next }
      /^\t(call|jmp)q?\t\*/     { ind++ }
      /^\t(call|jmp)q?\t_ZNK(2D[nfm]1fEv|1N1gEv)/ { dir++ }
      /^\tleaq\t_ZNK2D[nfm]1fEv/ { adr++ }
      /^\.LFE|^\.Lfunc_end/     {
        verdict = (ind > 0 && adr > 0) ? "추측 후 간접" : (ind > 0) ? "간접" : (dir > 0) ? "직접" : "인라인(call 없음)"
        printf "  %-18s 간접 %d · 직접 %d · f 주소 %d  -> %s\n", name, ind, dir, adr, verdict
        name = ""
      }' devirt.s
  done
done
rm -f devirt.s
```

```text
===== bash devirt-grid.sh (exit=0) =====
[g++ -O0]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 1 · f 주소 0  -> 직접
  t4_final_func      간접 0 · 직접 1 · f 주소 0  -> 직접
  t5_local_object    간접 0 · 직접 1 · f 주소 0  -> 직접
  t6_new_then_call   간접 2 · 직접 0 · f 주소 0  -> 간접
  t7_qualified       간접 0 · 직접 1 · f 주소 0  -> 직접
  t8_nonvirtual      간접 0 · 직접 1 · f 주소 0  -> 직접
[g++ -O2]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 1  -> 추측 후 간접
  t3_final_class     간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t4_final_func      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t5_local_object    간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t6_new_then_call   간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t7_qualified       간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t8_nonvirtual      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
[clang++ -O0]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 1 · f 주소 0  -> 직접
  t4_final_func      간접 0 · 직접 1 · f 주소 0  -> 직접
  t5_local_object    간접 0 · 직접 1 · f 주소 0  -> 직접
  t6_new_then_call   간접 2 · 직접 0 · f 주소 0  -> 간접
  t7_qualified       간접 0 · 직접 1 · f 주소 0  -> 직접
  t8_nonvirtual      간접 0 · 직접 1 · f 주소 0  -> 직접
[clang++ -O2]
  t1_base_ref        간접 1 · 직접 0 · f 주소 0  -> 간접
  t2_derived_ref     간접 1 · 직접 0 · f 주소 0  -> 간접
  t3_final_class     간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t4_final_func      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t5_local_object    간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t6_new_then_call   간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t7_qualified       간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
  t8_nonvirtual      간접 0 · 직접 0 · f 주소 0  -> 인라인(call 없음)
```

```text
===== g++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[0-9]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:
	movq	(%rdi), %rax
	jmp	*(%rax)
t2_derived_ref:
	movq	(%rdi), %rax
	leaq	_ZNK2Dn1fEv(%rip), %rdx
	movq	(%rax), %rax
	cmpq	%rdx, %rax
	jne	.L8
	movl	$3, %eax
	ret
.L8:
	jmp	*%rax
t3_final_class:
	movl	$1, %eax
	ret
t4_final_func:
	movl	$2, %eax
	ret
t5_local_object:
	movl	$3, %eax
	ret
t6_new_then_call:
	movl	$3, %eax
	ret
t7_qualified:
	movl	$3, %eax
	ret
t8_nonvirtual:
	movl	$4, %eax
	ret
```

```text
===== clang++ -std=c++20 -O2 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[0-9]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:                            # @t1_base_ref
	movq	(%rdi), %rax
	jmpq	*(%rax)                         # TAILCALL
t2_derived_ref:                         # @t2_derived_ref
	movq	(%rdi), %rax
	jmpq	*(%rax)                         # TAILCALL
t3_final_class:                         # @t3_final_class
	movl	$1, %eax
	retq
t4_final_func:                          # @t4_final_func
	movl	$2, %eax
	retq
t5_local_object:                        # @t5_local_object
	movl	$3, %eax
	retq
t6_new_then_call:                       # @t6_new_then_call
	movl	$3, %eax
	retq
t7_qualified:                           # @t7_qualified
	movl	$3, %eax
	retq
t8_nonvirtual:                          # @t8_nonvirtual
	movl	$4, %eax
	retq
```

**왜 그런가**

- ★★★ **1번은 남는다** — 두 컴파일러 다 **`jmp *(%rax)`** 다. 이 번역 단위 안에서 **받을 함수를 증명할 수 없다.**
- ★★★ **3·4·5번은 `-O0` 에서 이미 `call _ZNK2Df1fEv` 류의 직접 호출**이다 — 정적 타입이 `final` 이거나 **객체 자체**이면 받을 함수가 **문법만 보고** 하나로 정해진다.
- ★★★ **2번은 갈린다** — g++ `-O2` 는 **`leaq`+`cmpq`+`jne`** 로 추측하고, clang `-O2` 는 **`jmpq *(%rax)`** 로 남긴다.
- ★★ **8번(비가상)은 `-O2` 에서 `movl $4, %eax` 한 줄** — **1번과 8번의 차이가 「인라인이 막힌다」의 실체**다.

```text
===== g++ -std=c++20 -O0 -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t[13]_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t1_base_ref:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rax
	movq	(%rax), %rax
	movq	(%rax), %rdx
	movq	-8(%rbp), %rax
	movq	%rax, %rdi
	call	*%rdx
	leave
	ret
t3_final_class:
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$16, %rsp
	movq	%rdi, -8(%rbp)
	movq	-8(%rbp), %rax
	movq	%rax, %rdi
	call	_ZNK2Df1fEv
	leave
	ret
```

### 6. ★★ 「**vtable 첫 칸이 `Dn::f` 인가**」를 확인한다 — 아닐 수도 있어서 **간접 호출을 남긴다**

**출력**

```text
   movq  (%rdi), %rax              vptr
   leaq  _ZNK2Dn1fEv(%rip), %rdx   Dn::f 의 주소
   movq  (%rax), %rax              vtable 첫 칸
   cmpq  %rdx, %rax                같은가?
   jne   .L8                       다르면 간접 호출로
   movl  $3, %eax ; ret            같으면 인라인한 본체
.L8: jmp *%rax
```

```text
===== g++ -std=c++20 -O2 -fno-devirtualize-speculatively -S -fno-asynchronous-unwind-tables -fcf-protection=none -o - devirt.cpp | awk '/^t2_[a-z_]*:/{f=1} f{print} /^\.LFE|^\.Lfunc_end/{f=0}' | grep -vE '^\s*\.(size|p2align|type|globl|cfi)|^\.LF[BE]|^\.Lfunc_end|^# %bb|^\s*#' (exit=0) =====
t2_derived_ref:
	movq	(%rdi), %rax
	jmp	*(%rax)
```

**왜 그런가**

- ★★ **`Dn` 은 `final` 이 아니다** — `const Dn&` 뒤에 **`Dn` 의 파생**이 있을 수 있어 `Dn::f` 로 **확정**할 수 없다. 그래서 **맞으면 인라인, 틀리면 간접**의 두 길을 만든다.
- ★★ **`-fno-devirtualize-speculatively` 로 끄면 두 줄**(`movq`·`jmp *(%rax)`)이 된다 — **clang `-O2` 와 같은 모양**이다.
- ★ 「그 비교 한 번이 이득인가」는 **재지 않았다** — 추측이 맞는 비율과 시간에 달린 문제다.

### 7. ★★ **8 · 8 · 24** — 포인터 차이는 **8**, `offset_to_top` 은 **-8**

**출력**

```cpp
/* abs05.cpp */
// 인터페이스 관용구 — 데이터 없는 순수 가상만의 클래스, 그리고 둘을 함께 물려받으면
#include <cstdio>
#include <type_traits>

struct Reader { virtual int  read() = 0;     virtual ~Reader() = default; };   // 데이터가 없다
struct Writer { virtual void write(int) = 0; virtual ~Writer() = default; };

struct Pipe : Reader, Writer {                   // 인터페이스 둘을 구현한다
    int buf = 0;
    int  read() override       { return buf; }
    void write(int v) override { buf = v; }
};

int main() {
    std::printf("(1) sizeof  Reader %zu · Writer %zu · Pipe %zu (int 는 %zu)\n",
                sizeof(Reader), sizeof(Writer), sizeof(Pipe), sizeof(int));
    std::printf("(2) is_abstract  Reader %d · Pipe %d  |  is_polymorphic Reader %d\n",
                (int)std::is_abstract_v<Reader>, (int)std::is_abstract_v<Pipe>,
                (int)std::is_polymorphic_v<Reader>);
    Pipe p;
    Reader* r = &p;
    Writer* w = &p;
    w->write(42);
    std::printf("(3) w->write(42) 뒤 r->read() = %d\n", r->read());
    std::printf("(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = %td\n",
                (char*)w - (char*)r);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic abs05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
(1) sizeof  Reader 8 · Writer 8 · Pipe 24 (int 는 4)
(2) is_abstract  Reader 1 · Pipe 0  |  is_polymorphic Reader 1
(3) w->write(42) 뒤 r->read() = 42
(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = 8
```

```text
===== clang++ -std=c++20 -Xclang -fdump-record-layouts -fsyntax-only abs05.cpp | sed -n '/^ *0 | struct Pipe$/,/nvalign/p' (exit=0) =====
         0 | struct Pipe
         0 |   struct Reader (primary base)
         0 |     (Reader vtable pointer)
         8 |   struct Writer (base)
         8 |     (Writer vtable pointer)
        16 |   int buf
           | [sizeof=24, dsize=20, align=8,
           |  nvsize=20, nvalign=8]
```

```text
===== g++ -std=c++20 -fdump-lang-class=stdout -c abs05.cpp -o /dev/null | sed -n '/^Vtable for Pipe/,/^$/p;/^Class Pipe/,/^$/p' (exit=0) =====
Vtable for Pipe
Pipe::_ZTV4Pipe: 11 entries
0     (int (*)(...))0
8     (int (*)(...))(& _ZTI4Pipe)
16    (int (*)(...))Pipe::read
24    (int (*)(...))Pipe::~Pipe
32    (int (*)(...))Pipe::~Pipe
40    (int (*)(...))Pipe::write
48    (int (*)(...))-8
56    (int (*)(...))(& _ZTI4Pipe)
64    (int (*)(...))Pipe::_ZThn8_N4Pipe5writeEi
72    (int (*)(...))Pipe::_ZThn8_N4PipeD1Ev
80    (int (*)(...))Pipe::_ZThn8_N4PipeD0Ev

Class Pipe
   size=24 align=8
   base size=20 base align=8
Pipe (0x0x78c923769cb0) 0
    vptr=((& Pipe::_ZTV4Pipe) + 16)
Reader (0x0x78c92323fb40) 0 nearly-empty
      primary-for Pipe (0x0x78c923769cb0)
Writer (0x0x78c92323fba0) 8 nearly-empty
      vptr=((& Pipe::_ZTV4Pipe) + 64)
```

**왜 그런가**

- ★★ **데이터가 없는 인터페이스도 8바이트**다 — vptr 하나.
- ★★★ **`Pipe` 에는 vptr 가 둘**이다 — 오프셋 0(`Reader`)과 8(`Writer`). 그래서 `Writer*` 로 바꾸면 **주소가 8 늘어난다.**
- ★★ **`Writer` 부분의 vtable 에 `offset_to_top = -8`** 과 **thunk `_ZThn8_…`** 가 생긴다 — 19편 (11)의 단일 상속에서는 **0** 이었다.

### 8. ★★★ **간접 호출이 되나 · 이름으로 부르나 · 인라인되나** — 「느리다」는 **시간 측정이 있어야** 하고, 이 편은 **안 했다**

**왜 그런가**

- ★★★ **센 것 셋** — ① `call *`/`jmp *` 유무 ② `call <이름>` 인가 ③ `call` 이 사라졌나. 전부 (5)의 격자에 있다.
- ★★★ **「느리다」로 가려면** — 같은 일을 **두 판으로 여러 번 돌려 시간을 재고**, 잡음보다 큰 차이가 나는지 보여야 한다. **분기 예측·캐시**가 그 시간에 끼어든다.\
  ★ **이 편은 그것을 하지 않았다** — 그래서 **아무 결론도 적지 않았다.**
- ★ **「부적용」이 아닌 이유** — 부적용은 「**잴 것이 없다**」다. 가상 호출에는 **잴 수 있는 시간이 있을 수 있고**, 이 문서가 **안 만든 측정**일 뿐이다.

### 9. ★★ C# 은 **`callvirt`**(C# 갈래 **16번**) · 자바는 **`invokevirtual`** · C++ 은 **`-O0` 에서도 직접 `call`**

**출력**

```java
// Abs.java
// 자바의 추상 클래스·인터페이스·final 클래스 — 호출 자리의 바이트코드 명령을 찍는다
public class Abs {
    interface Shape { int area(); }                        // 인터페이스
    static abstract class Base { abstract int area(); }    // 추상 클래스
    static final class Sq extends Base { int area() { return 9; } }   // final 클래스

    static int viaInterface(Shape s) { return s.area(); }
    static int viaAbstract(Base b)   { return b.area(); }
    static int viaFinal(Sq q)        { return q.area(); }

    public static void main(String[] a) {
        System.out.println(viaInterface(() -> 4) + " " + viaAbstract(new Sq()) + " " + viaFinal(new Sq()));
    }
}
```

```text
===== set +u; source ~/.sdkman/bin/sdkman-init.sh >/dev/null 2>&1; set -u; javac Abs.java && java Abs && javap -c Abs | sed -n '/static int via/,/ireturn/p' (exit=0) =====
4 9 9
  static int viaInterface(Abs$Shape);
    Code:
       0: aload_0
       1: invokeinterface #7,  1            // InterfaceMethod Abs$Shape.area:()I
       6: ireturn
  static int viaAbstract(Abs$Base);
    Code:
       0: aload_0
       1: invokevirtual #13                 // Method Abs$Base.area:()I
       4: ireturn
  static int viaFinal(Abs$Sq);
    Code:
       0: aload_0
       1: invokevirtual #16                 // Method Abs$Sq.area:()I
       4: ireturn
```

**왜 그런가**

- ★★ **C# — `sealed` 여도 IL 은 `callvirt`**, 디버추얼라이제이션은 **JIT 몫**이다 — C# 갈래 목록([`csharp/syntax/README.md`](../../../csharp/syntax/README.md))의 **16번**([`16-inheritance-virtual-override-abstract-sealed-new/`](../../../csharp/syntax/16-inheritance-virtual-override-abstract-sealed-new/)) (4)의 실측이다.
- ★★ **자바 — `final` 클래스 `Sq` 의 호출도 `invokevirtual`** 이다. 인터페이스는 `invokeinterface`.
- ★★ **C++ — (5)의 3번 탐침이 `-O0` 에서 `call _ZNK2Df1fEv`** 였다. **바꾸는 층이 컴파일러**다.

### 10. ★★ **미명시** · **구현 정의**(19편과 같은 층) · **미명시** · **UB**

**왜 그런가**

- ★★ **vtable 은 표준에 없는 말**이다 — 표준은 「가상 함수는 동적 타입으로 골라진다」는 **결과**만 말한다. **무엇으로 고르나는 미명시**다.
- ★★ **`offset_to_top = -8` 은 Itanium C++ ABI 가 문서화한 배치**다 — 19편이 vtable 배치를 둔 **구현 정의** 칸과 같다.\
  ★ **두 층이 다른 질문에 답한다** — 「vtable 로 하나」는 미명시, 「vtable 을 어떻게 놓나」는 구현 정의.
- ★★ **추측 디버추얼라이제이션은 미명시** — 결과가 같으면 **어떤 코드를 내도 된다.** 판이 바뀌면 격자가 바뀔 수 있다.
- ★ **생성자에서 순수 가상을 가상 호출하는 것은 UB** — 그래서 (3)의 두 컴파일러 결과가 달라도 **둘 다 맞다.**

### 11. 다른 주제와 잇기

- ★★ **19편의 「부적용인 창」은 `-O2` 어셈블리 세기**였다 — 「가상 호출 비용은 21번이 정본」. **이 편 (4)의 디버추얼라이제이션 격자**가 이어받았다.
- ★ **삭제 소멸자(`D0`)** 다 — `delete p` 가 vtable 의 `[deleting]` 칸을 부른다. [20번](../20-virtual-destructors-and-polymorphic-deletion/) (7)이 그 본체를 찍었다.
- ★ **순수 가상 소멸자의 정본은 [20번](../20-virtual-destructors-and-polymorphic-deletion/) (8)** 이다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `abs01.cpp` 추상 클래스 | g++ · clang 각 1회 | ★★ **에러 3 · 3** · 남은 이름 나열 |
| `abs02.cpp`·`abs06.cpp` 순수 가상의 본체 | g++ · clang 각 1회 | ★★ `is_abstract` **1** · 이름으로만 불림 · 한 줄 본체 **에러 1 · 2** |
| `abs03.cpp` 생성자 속 직접 | g++ · clang 각 1회 | ★★★ **g++ 링크 에러 · clang `run exit=134`** · 경고 **1 · 1** |
| `abs04.cpp` 생성자 속 한 다리 | g++ · clang 각 1회 | ★★★ **경고 0 · 0** · **`run exit=134`** 양쪽 |
| `devirt.cpp` 격자 | g++ · clang × `-O0`·`-O2` = 4판 + 덤프 6회 | ★★★ 1번 **`-O2` 에서도 간접** · 3·4·5번 **`-O0` 직접** · 2번 **g++ 만 추측** |
| `abs05.cpp` 인터페이스 둘 | g++ · clang 각 1회 + 덤프 2회 | ★★ **8 · 8 · 24** · 차이 **8** · `offset_to_top` **-8** |
| `Abs.java` | javac + java + javap 각 1회 | ★★ `final` 클래스도 **`invokevirtual`** |
| `abs07.cpp` 형태 | g++ 1회 | `put(2)` · `get(2) -> 1, x=42` |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · g++ 13.3.0 · clang 18.1.3 · Itanium C++ ABI)에서만** 그렇다.

- ★★★ **디버추얼라이제이션 격자 전부** — 어느 판이 무엇을 직접 호출로 바꾸나는 **미명시**다.
- ★★ **`offset_to_top`·thunk·vptr 위치** · `sizeof` 8·24 · **`__cxa_pure_virtual` 과 그 문구.**
- ★★ **(3)의 직접 호출을 g++ 는 직접으로, clang 은 vtable 로** 만든 것.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **순수 가상이 남으면 추상 — 객체를 못 만드는** 것 · **순수 가상에 클래스 밖 본체를 주고 이름으로 부를 수 있는** 것.
- ★★★ **생성자·소멸자에서 순수 가상을 가상 호출하면 UB 인** 것.
- ★★ **가상 함수가 동적 타입으로 골라지는** 것(결과만 — 수단은 아니다).

**안 돌려 본 것 / 못 잰 것**

- ★★★ **안 잰 것 — 실행 시간.** 벤치마크 하네스를 만들지 않았다. 「느리다/빠르다」는 **어느 쪽도 적지 않았다.**
- **안 돌려 본 것** — ★ **LTO·`-fstrict-vtable-pointers`** · ★ **JIT 의 결과**(C#·Java 는 바이트코드까지만) · ★ **가상 상속** · ★ **`-O1`·`-O3`**(두 판만 봤다).
- ★ **「부적용인 창」** — ASan. 이 주제의 실패는 메모리 오류가 아니다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **5번 격자 전부** — 특히 **2번 탐침**(g++ 만 추측)과 **6번 탐침**(`new` 직후).
- ★★ **3번의 두 컴파일러 선택** — 미명시·UB 자리라 판이 바뀌면 뒤집힐 수 있다.
- ★ **javac 판이 바뀌면 9번의 상수 풀 번호**(`#7` 등).
