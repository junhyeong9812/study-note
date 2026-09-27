# cpp/syntax/38 — `constexpr` · `consteval` · `constinit` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU objdump·nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 역어셈블의 오프셋·레지스터 · ASan 의 PID·주소** 다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · `sq(int)` 재배치의 유무 · `$0x31` 의 유무 · `nm` 의 글자 · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **에러 8칸 — `consteval`×런타임 인자 · 보통 함수×(`constexpr` 변수 · `static_assert` · 템플릿 인자)** · ★★★ **호출이 남은 칸 — `constexpr`×`sq(n)` · 보통×`sq(n)` · 보통×`int v = sq(7)` 은 두 컴파일러, `constexpr`×`int v = sq(7)` 은 clang 만**(갈린 행 1 / 15)

**출력**

```bash
# cx-grid.sh
# cx-grid.sh — 함수 셋 × 부르는 자리 다섯 × 컴파일러 둘. 최적화 수준은 첫 인자(없으면 -O0)
# 통과한 칸은 probe(int) 의 역어셈블(재배치 포함)에서 sq 호출이 몇 번 남았나 · 상수 49($0x31)가 있나를 센다
O="${1:--O0}"
fns=('1 constexpr' '2 consteval' '3 보통')
sites=('1 constexpr 변수 초기화' '2 static_assert' '3 런타임 인자 sq(n)' '4 템플릿 인자 Tag<sq(7)>' '5 보통 변수 int v = sq(7)')
cell() {
  local calls imm
  if ! $1 -std=c++20 $O -DFN="$2" -DSITE="$3" -c cx01.cpp -o cx.o 2>/dev/null; then printf '에러'; return; fi
  objdump -dr --no-show-raw-insn -C cx.o | awk '/<probe\(int\)>:/ { on=1; next } /^$/ { on=0 } on' > probe.s
  calls=$(grep -c 'R_X86_64_PLT32[[:space:]]*sq(int)' probe.s)
  if grep -q '\$0x31' probe.s; then imm='49 있음'; else imm='49 없음'; fi
  printf '통과 · 호출 %s · %s' "$calls" "$imm"
}
printf '%s\t%s\t%s\t%s\n' "함수" "자리" "g++ $O" "clang++ $O" > t.tsv
for f in "${fns[@]}"; do
  for s in "${sites[@]}"; do
    printf '%s\t%s\t%s\t%s\n' "$f" "$s" "$(cell g++ "${f%% *}" "${s%% *}")" "$(cell clang++ "${f%% *}" "${s%% *}")" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
errs=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i == "에러") n++ } END { print n+0 }')
left=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i ~ /호출 [1-9]/) n++ } END { print n+0 }')
ccs=$(tail -n +2 t.tsv | awk -F'\t' '$3 != $4' | wc -l)
echo "에러 칸 $errs / $(( rows * 2 )) · 통과했는데 호출이 남은 칸 $left / $(( rows * 2 - errs )) · 컴파일러 사이 갈린 행 $ccs / $rows"
rm -f cx.o probe.s t.tsv
```

```text
===== bash cx-grid.sh -O0 (exit=0) =====
함수	자리	g++ -O0	clang++ -O0
1 constexpr	1 constexpr 변수 초기화	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
1 constexpr	2 static_assert	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
1 constexpr	3 런타임 인자 sq(n)	통과 · 호출 1 · 49 없음	통과 · 호출 1 · 49 없음
1 constexpr	4 템플릿 인자 Tag<sq(7)>	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
1 constexpr	5 보통 변수 int v = sq(7)	통과 · 호출 0 · 49 있음	통과 · 호출 1 · 49 없음
2 consteval	1 constexpr 변수 초기화	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
2 consteval	2 static_assert	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
2 consteval	3 런타임 인자 sq(n)	에러	에러
2 consteval	4 템플릿 인자 Tag<sq(7)>	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
2 consteval	5 보통 변수 int v = sq(7)	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
3 보통	1 constexpr 변수 초기화	에러	에러
3 보통	2 static_assert	에러	에러
3 보통	3 런타임 인자 sq(n)	통과 · 호출 1 · 49 없음	통과 · 호출 1 · 49 없음
3 보통	4 템플릿 인자 Tag<sq(7)>	에러	에러
3 보통	5 보통 변수 int v = sq(7)	통과 · 호출 1 · 49 없음	통과 · 호출 1 · 49 없음
에러 칸 8 / 30 · 통과했는데 호출이 남은 칸 7 / 22 · 컴파일러 사이 갈린 행 1 / 15
```

```text
===== g++ -std=c++20 -O0 -DFN=1 -DSITE=5 -c cx01.cpp -o cx.o && objdump -dr --no-show-raw-insn -C cx.o | sed -n '/<probe(int)>:/,/^$/p' (exit=0) =====
0000000000000000 <probe(int)>:
   0:	endbr64
   4:	push   %rbp
   5:	mov    %rsp,%rbp
   8:	mov    %edi,-0x14(%rbp)
   b:	movl   $0x31,-0x4(%rbp)
  12:	mov    -0x4(%rbp),%eax
  15:	pop    %rbp
  16:	ret
===== clang++ -std=c++20 -O0 -DFN=1 -DSITE=5 -c cx01.cpp -o cx.o && objdump -dr --no-show-raw-insn -C cx.o | sed -n '/<probe(int)>:/,/^$/p' (exit=0) =====
0000000000000000 <probe(int)>:
   0:	push   %rbp
   1:	mov    %rsp,%rbp
   4:	sub    $0x10,%rsp
   8:	mov    %edi,-0x4(%rbp)
   b:	mov    $0x7,%edi
  10:	call   15 <probe(int)+0x15>
			11: R_X86_64_PLT32	sq(int)-0x4
  15:	mov    %eax,-0x8(%rbp)
  18:	mov    -0x8(%rbp),%eax
  1b:	add    $0x10,%rsp
  1f:	pop    %rbp
  20:	ret
  21:	data16 data16 data16 data16 data16 cs nopw 0x0(%rax,%rax,1)
```

**왜 그런가**

- ★★★ **상수 식 문맥(자리 1·2·4)은 컴파일 시간 평가가 강제된다** — 보통 함수는 거기 못 들어가 에러, `constexpr`·`consteval` 은 상수 49 가 박힌다.
- ★★★ **런타임 인자(자리 3)는 상수 식이 될 수 없다** — `constexpr` 은 보통 호출, `consteval` 은 에러(7번).
- ★★★ **자리 5(보통 변수)는 상수 식 문맥이 아니다** — 표준이 평가 시점을 정하지 않으니 **g++ 는 접고 clang 은 불렀다**(덤프의 `movl $0x31` 대 `call … sq(int)`).

### 2. ★★ **네 경우 모두 C++17 은 막히고 C++20 은 통과 — 단 `try` 블록의 C++17 칸은 에러가 아니라 경고**(판 사이 12 / 12 · 컴파일러 사이 0 / 8)

**출력**

```bash
# cx20-grid.sh
# cx20-grid.sh — 넓어진 것 넷 × 판 둘(c++17 · c++20) × 컴파일러 셋. 칸에는 통과 · 경고 · 에러만 찍는다
cases=('1 constexpr 가상 함수' '2 constexpr 안 new/delete' '3 constexpr 안 std::vector' '4 constexpr 안 try 블록')
cell() {
  local out rc
  out=$($1 -std="$2" -Wall -Wextra -pedantic -DCASE="$3" cx20.cpp -o ex 2>&1); rc=$?
  if [ "$rc" -ne 0 ]; then printf '에러'; elif printf '%s' "$out" | grep -q 'warning:'; then printf '경고'; else printf '통과'; fi
}
printf '%s\t%s\t%s\t%s\t%s\n' "경우" "판" "g++ 13" "g++-12" "clang++ 18" > t.tsv
for k in "${cases[@]}"; do
  for s in c++17 c++20; do
    n="${k%% *}"
    printf '%s\t%s\t%s\t%s\t%s\n' "$k" "$s" "$(cell g++ $s $n)" "$(cell g++-12 $s $n)" "$(cell clang++ $s $n)" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 5' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
# 판 사이 — (경우, 컴파일러) 묶음에서 c++17 칸과 c++20 칸이 다른가
std_split=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=5;i++) v[$1,i]=v[$1,i] "|" $i } END { for (k in v) { split(v[k], x, "|"); if (x[2]!=x[3]) n++ } print n+0 }')
groups=$(( ${#cases[@]} * 3 ))
cc_split=$(tail -n +2 t.tsv | awk -F'\t' '!($3 == $4 && $4 == $5)' | wc -l)
rows=$(( $(wc -l < t.tsv) - 1 ))
echo "판 사이 갈린 묶음 $std_split / $groups · 컴파일러 사이 갈린 행 $cc_split / $rows"
rm -f ex t.tsv
```

```text
===== bash cx20-grid.sh (exit=0) =====
경우	판	g++ 13	g++-12	clang++ 18
1 constexpr 가상 함수	c++17	에러	에러	에러
1 constexpr 가상 함수	c++20	통과	통과	통과
2 constexpr 안 new/delete	c++17	에러	에러	에러
2 constexpr 안 new/delete	c++20	통과	통과	통과
3 constexpr 안 std::vector	c++17	에러	에러	에러
3 constexpr 안 std::vector	c++20	통과	통과	통과
4 constexpr 안 try 블록	c++17	경고	경고	경고
4 constexpr 안 try 블록	c++20	통과	통과	통과
판 사이 갈린 묶음 12 / 12 · 컴파일러 사이 갈린 행 0 / 8
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -DCASE=4 cx20.cpp -o ex (cc exit=0) =====
cx20.cpp: In function ‘constexpr int count()’:
cx20.cpp:30:5: warning: ‘try’ in ‘constexpr’ function only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
   30 |     try {
      |     ^~~
===== g++ -std=c++17 -Wall -Wextra -pedantic -pedantic-errors -DCASE=4 cx20.cpp -o ex (cc exit=1) =====
cx20.cpp: In function ‘constexpr int count()’:
cx20.cpp:30:5: error: ‘try’ in ‘constexpr’ function only available with ‘-std=c++20’ or ‘-std=gnu++20’ [-Wc++20-extensions]
   30 |     try {
      |     ^~~
```

**왜 그런가**

- ★★★ **가상 함수 · `new`/`delete` · `std::vector` · `try` 는 C++20 에서 `constexpr` 함수 안에 허락됐다**(cppreference 의 **until C++20** 표시).
- ★★ **`try` 는 C++17 에서 확장으로 받아 준다** — `-pedantic` 이면 경고, `-pedantic-errors` 면 에러(10번).
- ★ **`vector` 칸의 세 컴파일러 일치 중 독립된 라이브러리 판은 둘**(libstdc++ 12 · 13) — clang 은 13 을 읽었다.

### 3. ★★★ **컴파일 안 된다 — 두 컴파일러 다 3행의 `new` 를 가리킨다**(g++ `allocated storage has not been deallocated` · clang `allocation performed here was not deallocated`)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic leak01.cpp -o ex (cc exit=1) =====
leak01.cpp:7:23: error: non-constant condition for static assertion
    7 | static_assert(count() == 3);
      |               ~~~~~~~~^~~~
leak01.cpp:3:23: error: ‘(count() == 3)’ is not a constant expression because allocated storage has not been deallocated
    3 |     int* p = new int(3);
      |                       ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic leak01.cpp -o ex (cc exit=1) =====
leak01.cpp:7:15: error: static assertion expression is not an integral constant expression
    7 | static_assert(count() == 3);
      |               ^~~~~~~~~~~~
leak01.cpp:3:14: note: allocation performed here was not deallocated
    3 |     int* p = new int(3);
      |              ^
1 error generated.
```

**왜 그런가**

- ★★★ **상수 평가 안의 할당은 그 평가가 끝나기 전에 풀려야** 한다. 풀리지 않은 할당을 남긴 식은 **상수 식이 아니다** — 그래서 `static_assert` 가 실패한다.

### 4. ★★★ **`-DCONST` 는 에러(g++ `overflow in constant expression` · clang `value 2147483648 is outside the range …`)** · ★★ **런타임은 `done` · `exit 0` — 아무 말 없다** · UBSan 이면 **`runtime error: signed integer overflow`** 가 한 줄 더(여전히 `exit 0`)

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCONST ub01.cpp -o ex (cc exit=1) =====
ub01.cpp: In function ‘int main(int, char**)’:
ub01.cpp:9:26:   in ‘constexpr’ expansion of ‘add(2147483647, 1)’
ub01.cpp:9:37: error: overflow in constant expression [-fpermissive]
    9 |     constexpr int v = add(INT_MAX, 1);
      |                                     ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCONST ub01.cpp -o ex (cc exit=1) =====
ub01.cpp:9:19: error: constexpr variable 'v' must be initialized by a constant expression
    9 |     constexpr int v = add(INT_MAX, 1);
      |                   ^   ~~~~~~~~~~~~~~~
ub01.cpp:5:44: note: value 2147483648 is outside the range of representable values of type 'int'
    5 | constexpr int add(int a, int b) { return a + b; }
      |                                            ^
ub01.cpp:9:23: note: in call to 'add(2147483647, 1)'
    9 |     constexpr int v = add(INT_MAX, 1);
      |                       ^~~~~~~~~~~~~~~
1 error generated.
```

★ 아래 런타임 진단을 낸 소스(질문 4번과 같다) —

```cpp
/* ub01.cpp */
// 부호 있는 덧셈 — 상수 평가(-DCONST) 대 런타임. 런타임 판은 값을 찍지 않고 다 돌았다는 표시만 찍는다
#include <climits>
#include <cstdio>

constexpr int add(int a, int b) { return a + b; }

int main([[maybe_unused]] int argc, char**) {
#ifdef CONST
    constexpr int v = add(INT_MAX, 1);
    return v;
#else
    volatile int v = add(INT_MAX, argc);
    (void)v;
    std::fprintf(stderr, "done\n");
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
done
===== clang++ -std=c++20 -Wall -Wextra -pedantic ub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
done
===== g++ -std=c++20 -Wall -Wextra -pedantic -fsanitize=undefined ub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ub01.cpp:5:46: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
done
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fsanitize=undefined ub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ub01.cpp:5:44: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: undefined-behavior ub01.cpp:5:44 
done
```

**왜 그런가**

- ★★★ **상수 평가는 UB 를 만나면 상수 식이 아니게 된다** — 그래서 컴파일 에러다.
- ★★★ **런타임의 같은 넘침은 UB** 이고, 도구 없이는 **아무 표시도 없다.** 값은 UB 의 한 결과라 **싣지 않았다** — 소스가 값을 찍지 않게 만든 이유다.
- ★★ **UBSan 은 기본으로 계속 진행**한다 — `exit 0` 인 채 `runtime error:` 줄만 남긴다.

### 5. ★★ **기본 · `-DPLAIN` 은 통과(둘 다 `42`) · `-DDYNAMIC` 는 에러** · **기본은 `D counter` · 초기화 함수 없음 / `-DPLAIN` 은 `B counter` + `_GLOBAL__sub_I_…`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DDYNAMIC cinit01.cpp -o ex (cc exit=1) =====
cinit01.cpp:8:15: error: ‘constinit’ variable ‘counter’ does not have a constant initializer
    8 | constinit int counter = runtime_base();
      |               ^~~~~~~
cinit01.cpp:8:37: error: call to non-‘constexpr’ function ‘int runtime_base()’
    8 | constinit int counter = runtime_base();
      |                         ~~~~~~~~~~~~^~
cinit01.cpp:5:5: note: ‘int runtime_base()’ declared here
    5 | int runtime_base() { return 40; }
      |     ^~~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DDYNAMIC cinit01.cpp -o ex (cc exit=1) =====
cinit01.cpp:8:15: error: variable does not have a constant initializer
    8 | constinit int counter = runtime_base();
      |               ^         ~~~~~~~~~~~~~~
cinit01.cpp:8:1: note: required by 'constinit' specifier here
    8 | constinit int counter = runtime_base();
      | ^~~~~~~~~
cinit01.cpp:8:25: note: non-constexpr function 'runtime_base' cannot be used in a constant expression
    8 | constinit int counter = runtime_base();
      |                         ^
cinit01.cpp:5:5: note: declared here
    5 | int runtime_base() { return 40; }
      |     ^
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c cinit01.cpp -o ci.o && g++ ci.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C ci.o (exit=0) =====
0000000000000000 T runtime_base()
0000000000000000 D counter
000000000000000f T main
                 U printf
===== g++ -std=c++20 -Wall -Wextra -pedantic -DPLAIN -c cinit01.cpp -o ci.o && g++ ci.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C ci.o (exit=0) =====
000000000000005f t _GLOBAL__sub_I__Z12runtime_basev
0000000000000000 T runtime_base()
0000000000000049 t __static_initialization_and_destruction_0()
0000000000000000 B counter
000000000000000f T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c cinit01.cpp -o ci.o && clang++ ci.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C ci.o (exit=0) =====
0000000000000000 r .L.str
0000000000000000 T runtime_base()
0000000000000000 D counter
0000000000000010 T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DPLAIN -c cinit01.cpp -o ci.o && clang++ ci.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C ci.o (exit=0) =====
0000000000000000 r .L.str
0000000000000020 t _GLOBAL__sub_I_cinit01.cpp
0000000000000000 T runtime_base()
0000000000000000 t __cxx_global_var_init
0000000000000000 B counter
0000000000000010 T main
                 U printf
```

**왜 그런가**

- ★★★ **`constinit` 은 정적 초기화를 요구**한다 — 비-`constexpr` 함수를 부르는 초기화는 동적 초기화라 에러.
- ★★★ **`-DPLAIN` 은 같은 초기화를 `constinit` 없이 허락**하고, 컴파일러가 **시작 때 도는 초기화 함수**를 만든다. `counter` 는 그때까지 **0(`B`)** 이다.
- ★★ **`counter += 2` 가 통과** — `constinit` 은 `const` 가 아니다.

### 6. ★ **`-std=c++23` 은 `1 2`** · **`-std=c++20` 도 경고 한 줄(`-Wc++23-extensions`)과 함께 `1 2`**

**출력**

```text
===== g++ -std=c++23 -Wall -Wextra -pedantic ifcv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 2
===== clang++ -std=c++23 -Wall -Wextra -pedantic ifcv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 2
===== g++ -std=c++20 -Wall -Wextra -pedantic ifcv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ifcv01.cpp: In function ‘constexpr int where()’:
ifcv01.cpp:5:8: warning: ‘if consteval’ only available with ‘-std=c++2b’ or ‘-std=gnu++2b’ [-Wc++23-extensions]
    5 |     if consteval {
      |        ^~~~~~~~~
1 2
===== clang++ -std=c++20 -Wall -Wextra -pedantic ifcv01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
ifcv01.cpp:5:8: warning: consteval if is a C++23 extension [-Wc++23-extensions]
    5 |     if consteval {
      |        ^
1 warning generated.
1 2
```

**왜 그런가**

- ★ **`constexpr int a = where();` 는 상수 평가 → 1 · `int b = where();` 는 런타임 평가 → 2.**
- ★ C++20 칸은 **종료 코드 0 인데 그 판으로는 ill-formed**(확장으로 받아 줌)다.

### 7. ★★★ **`sq(n)` 은 상수 식이 될 수 없는 자리라 `constexpr` 함수는 보통 함수로 불린다** · **`consteval` 은 「모든 호출이 상수 식이어야」 하는 즉시 함수라 그 자리에서 에러**

- ★★★ `constexpr` 은 **「상수 평가에 쓸 수 있다」는 허가**이지 **강제**가 아니다(cppreference 「**can appear in a constant expression**」).
- ★★ `consteval` 에러 전문 — g++ `‘n’ is not a constant expression` · clang `call to consteval function 'sq' is not a constant expression`.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFN=2 -DSITE=3 cx01.cpp -o ex (cc exit=1) =====
cx01.cpp: In function ‘int probe(int)’:
cx01.cpp:22:14: error: ‘n’ is not a constant expression
   22 |     return sq(n);
      |            ~~^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFN=2 -DSITE=3 cx01.cpp -o ex (cc exit=1) =====
cx01.cpp:22:12: error: call to consteval function 'sq' is not a constant expression
   22 |     return sq(n);
      |            ^
cx01.cpp:22:15: note: function parameter 'n' with unknown value cannot be used in a constant expression
   22 |     return sq(n);
      |               ^
cx01.cpp:14:32: note: declared here
   14 | int probe([[maybe_unused]] int n) {
      |                                ^
1 error generated.
```

### 8. ★★★ **말할 수 없다 — `-O2` 는 보통 함수도 49 로 접었다**(최적화기의 일)

**출력**

```text
===== bash cx-grid.sh -O2 (exit=0) =====
함수	자리	g++ -O2	clang++ -O2
1 constexpr	1 constexpr 변수 초기화	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
1 constexpr	2 static_assert	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
1 constexpr	3 런타임 인자 sq(n)	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
1 constexpr	4 템플릿 인자 Tag<sq(7)>	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
1 constexpr	5 보통 변수 int v = sq(7)	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
2 consteval	1 constexpr 변수 초기화	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
2 consteval	2 static_assert	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
2 consteval	3 런타임 인자 sq(n)	에러	에러
2 consteval	4 템플릿 인자 Tag<sq(7)>	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
2 consteval	5 보통 변수 int v = sq(7)	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
3 보통	1 constexpr 변수 초기화	에러	에러
3 보통	2 static_assert	에러	에러
3 보통	3 런타임 인자 sq(n)	통과 · 호출 0 · 49 없음	통과 · 호출 0 · 49 없음
3 보통	4 템플릿 인자 Tag<sq(7)>	에러	에러
3 보통	5 보통 변수 int v = sq(7)	통과 · 호출 0 · 49 있음	통과 · 호출 0 · 49 있음
에러 칸 8 / 30 · 통과했는데 호출이 남은 칸 0 / 22 · 컴파일러 사이 갈린 행 0 / 15
```

- ★★★ **호출이 남은 칸이 7 → 0** 으로 줄었다 — 보통 함수까지. **역어셈블의 상수는 「누가 계산했나」를 말하지 않는다.** 언어의 강제는 **에러 칸(8 / 30 — 두 판 같음)** 과 **`-O0` 격자**로 본다.

### 9. ★★ **어느 쪽도 어기지 않았다 — 그 자리는 상수 식 문맥이 아니라 평가 시점이 컴파일러의 선택이다**

- ★★ 표준은 **결과(49)** 만 정한다. 컴파일 시간에 미리 계산해 넣든 런타임에 부르든 **관찰 가능한 동작이 같다.**

### 10. ★★ **C++17 코드가 아니다 — `-pedantic-errors` 로 던지면 같은 진단이 `error:` 가 되고 `cc exit=1`**

- ★★ **`-std=` 는 「강제」가 아니라 「기본값 선택」** 이다. 확장을 경고로 받아 주는 판에서 **`exit 0` 은 준수의 증거가 아니다.**

### 11. 다른 주제와 잇기

- ★★ [Rust 07번](../../../rust/syntax/07-const-static-and-const-fn/) — **`const fn` 은 상수 자리면 컴파일 타임 평가가 의무(E0080), 런타임 자리면 보통 호출(패닉)** — 1번의 `constexpr` 과 같은 모양이다.
- ★★ [30번](../30-dangling-references-and-lifetime-extension/) — **ASan 으로 물으면 침묵이 리포트로 바뀐다.** 4번 쌍 2 의 범위 밖 읽기가 `global-buffer-overflow` 로 멈췄다 — 넘침은 ASan 이 아니라 **UBSan** 의 몫이라 쌍 1 은 UBSan 으로 물었다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `cx01.cpp` + `cx-grid.sh` | 함수 3 × 자리 5 × 컴파일러 2 × `-O0`·`-O2` | ★★★ **에러 8 / 30 · 호출 남음 7 / 22 → 0 / 22 · 갈린 행 1 / 15 → 0 / 15** |
| `cx01.cpp` 덤프 | `FN=1 SITE=5` × 두 컴파일러 `-O0` | ★★★ **g++ `movl $0x31` · clang `call sq(int)`** |
| `cx20.cpp` + `cx20-grid.sh` | 경우 4 × 판 2 × 컴파일러 3 | ★★★ **판 사이 12 / 12 · 컴파일러 사이 0 / 8** |
| `leak01.cpp` · `ub01.cpp` · `ub02.cpp` | 두 컴파일러 · 런타임 + UBSan/ASan | ★★★ **컴파일 에러 / `done` · 도구가 잡는다** |
| `cinit01.cpp` | 세 판 × 두 컴파일러 + `nm -C` | ★★ **`D` / `B` + `_GLOBAL__sub_I`** |
| `ifcv01.cpp` | `c++20`·`c++23` × 두 컴파일러 | ★ **`1 2`** |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **상수 식 문맥 밖의 접힘**(g++ 접음 · clang 호출) · **`-O2` 의 접힘** · **`-pedantic` 의 확장 경고** · **`nm` 의 글자와 초기화 함수 이름**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **상수 식 문맥의 평가 · `consteval` 의 런타임 호출 금지 · 상수 평가 안 UB·누수는 ill-formed · `constinit` 은 정적 초기화 아니면 ill-formed.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **시간**(「빠르다」는 주장하지 않는다) · 두 번역 단위의 정적 초기화 순서 실험 · `std::is_constant_evaluated()`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **1번 `-O0` 격자의 자리 5** — 컴파일러의 선택이라 판마다 바뀔 수 있다.
