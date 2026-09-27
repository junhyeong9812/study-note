# cpp/syntax/38 — `constexpr` · `consteval` · `constinit` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — constexpr](https://en.cppreference.com/w/cpp/language/constexpr) · [cppreference — consteval](https://en.cppreference.com/w/cpp/language/consteval) · [cppreference — constinit](https://en.cppreference.com/w/cpp/language/constinit)\
> ★ 이 배치에서 **위 세 cppreference 쪽을 열어 확인했다** — `constexpr` 함수는 「**An invocation of a constexpr function can appear in a constant expression**」(나타날 **수 있다** — 의무가 아니다) · 가상 함수 금지와 `try` 블록 금지가 **(until C++20)** · `consteval` 은 「**every potentially-evaluated call to the function must (directly or indirectly) produce a compile time constant expression**」 · `constinit` 은 「**asserts that a variable has static initialization … otherwise the program is ill-formed**」 · 「`constinit` 은 `const` 를 붙이지 않는다」.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(g++-12 는 libstdc++ 12) · GNU objdump·nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★★ **clang 도 libstdc++ 13 을 쓴다** — `constexpr std::vector` 칸((3))에서 **g++ 13 과 clang 이 같은 것은 같은 헤더를 읽어서**다. **g++-12 칸만 다른 라이브러리 판(12)** 이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`cx01.cpp`·`cx20.cpp`·`leak01.cpp`·`ub01.cpp`·`ub02.cpp`·`cinit01.cpp`·`ifcv01.cpp`·`cx-grid.sh`·`cx20-grid.sh`).\
> ★ **진단에 소스 경로가 박히지 않게 상대 경로로 컴파일**했고, ASan 블록은 `-ffile-prefix-map="$PWD"=.` 을 붙였다. 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — `constexpr` 는 **C++11**(C++14 에서 몸통 제한 완화), **`consteval`·`constinit`·`constexpr` 가상 함수·`constexpr` 안 `new`/`delete`·`try` 블록은 C++20**, **`if consteval` 은 C++23** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[31번](../31-function-templates-and-argument-deduction/)에서 온다** — 템플릿 인자는 **컴파일 시간에 알아야 하는 값**이다. 이 편은 「**어떤 계산이 그 자리에 들어갈 수 있나**」를 묻는다.
> ★★★ **「`constexpr` 이 빠르다」는 이 문서가 재지 않았다** — 보인 것은 **역어셈블에 호출이 남았나 · 상수가 박혔나**뿐이다(시간 0회 측정).
> **경계** — 「정적 멤버·`inline` 변수」는 [25번](../25-static-members-and-inline-variables/)이, 「`if constexpr`」는 [37번](../37-sfinae-and-enable-if/) (4)가, 「런타임 UB 를 도구로 잡는 법」은 [30번](../30-dangling-references-and-lifetime-extension/)이 정본이다. Rust 의 같은 자리는 [Rust 07번](../../../rust/syntax/07-const-static-and-const-fn/)(`const fn`).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 역어셈블의 **오프셋·레지스터·명령 순서** · ASan 리포트의 **PID·주소** | ★★★ **컴파일되나(`cc exit`)** · ★★★ **`probe(int)` 안에 `sq(int)` 재배치(호출)가 있나 · 상수 `$0x31` 이 있나** |
> | ★★ **`-O0` 에서 상수로 접히나 — 컴파일러의 선택**((1) 5행 — 두 컴파일러가 갈린 칸) | ★★★ **`consteval` 의 런타임 인자 에러 · 상수 평가 안 UB 에러** · `nm` 의 **`D`/`B` 글자와 `_GLOBAL__sub_I` 기호의 유무** |

## 한눈에 — 쉽게 말하면

**컴파일 시간 계산은 「미리 계산해서 인쇄해 둔 표」다.** 계산기를 들고 다니는 대신 **답을 인쇄해 붙여 둔다.**

- **`constexpr` 함수는 「인쇄해도 되는 계산」이라는 허가증**이다. 인쇄할 **자리**(`constexpr` 변수 · `static_assert` · 템플릿 인자)에 쓰면 인쇄되고, 그 밖에서는 **그냥 계산기**로 쓰인다((1)).
- **`consteval` 은 「반드시 인쇄해야 하는 계산」** — 계산기로 쓰려 하면 **에러**다.
- **`constinit` 은 「이 표는 프로그램이 시작하기 전에 이미 붙어 있어야 한다」** — 시작하면서 계산해야 하면 에러다. **표 자체는 나중에 고쳐 써도 된다**(`const` 가 아니다).
- **인쇄소는 실수를 안 넘긴다** — 계산 중 **넘침·범위 밖**이 나오면 인쇄를 거절한다(컴파일 에러). **계산기(런타임)는 조용히** 틀린 답을 낸다((4)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 인쇄해도 되는 계산 | ★★★ **`constexpr` 함수 — 런타임 인자면 보통 호출** | (1) |
| 반드시 인쇄 | ★★★ **`consteval` — 런타임 인자면 에러** | (1)(2) |
| 인쇄할 자리 | ★★ **상수 식 문맥**(`constexpr` 변수·`static_assert`·템플릿 인자) | (1) |
| 인쇄소가 거절하는 실수 | ★★★ **상수 평가 안 UB = 컴파일 에러** | (4) |
| 시작 전에 붙어 있는 표 | ★★ **`constinit` — 정적 초기화** | (5) |
| C++20 에 늘어난 인쇄 가능 품목 | ★★ **가상 함수 · `new`/`delete` · `std::vector` · `try`** | (3) |

```text
   constexpr int sq(int);           부르는 자리                         결과(-O0, 두 컴파일러)
                                    constexpr int v = sq(7);            ★ 상수 49 가 박힌다 — 호출 없음
                                    static_assert(sq(7) == 49);         컴파일러가 계산하고 코드는 없다
                                    Tag<sq(7)>                          상수 49
                                    sq(n)   (n 은 런타임 값)             ★ call sq(int) — 보통 호출
                                    int v = sq(7);                      ★★ g++ 상수 · clang 호출 — 갈린다
```

## 이 주제가 답하려는 질문

1. ★★★ **`constexpr` · `consteval` · 보통 함수를 어느 자리에서 부르면 컴파일되나 — 결과가 상수로 접히나**((1)).
2. ★★★ **`constexpr` 은 컴파일 시간을 보장하나 — `consteval` 은 무엇이 다른가**((1)(2)).
3. ★★ **C++20 에서 상수 평가 안으로 들어온 것은 무엇인가 — `new` 를 쓰고 안 지우면**((3)).
4. ★★★ **런타임에서 조용한 UB 가 상수 평가에서는 어떻게 되나**((4)).
5. ★★ **`constinit` 은 무엇을 막나 — `const` 인가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러와 ④ 역어셈블이다

★★★ **「컴파일 시간 계산인가」는 역어셈블이 답한다** — 상수 평가였으면 **`probe(int)` 안에 상수 `$0x31`(49)만 남고 `sq` 호출이 없다.** `.o` 는 재배치가 안 풀려 있으므로 **`objdump -dr` 의 `R_X86_64_PLT32 sq(int)` 줄**로 호출을 센다.\
★★ **그런데 최적화도 같은 모양을 만든다** — `-O2` 에서는 보통 함수도 상수로 접힌다((1)의 두 번째 격자). 그래서 **언어가 강제한 것을 보려면 `-O0`** 을 본다.

```text
① 다섯 층 표            상수 식 규칙은 표준 · -O0 에서 접나는 컴파일러                     (구현 세부사항 절)
② ★ 두 컴파일러 (+g++-12) consteval 에러 · 상수 평가 UB 에러 · C++17/20 격자             (1)~(6)
③ ASan / UBSan           상수 평가 UB 의 「런타임 짝」 — 조용한가, 도구가 잡나             (4)
④ ★ 역어셈블 → 기호표    probe(int) 의 sq 호출 · $0x31 · constinit 의 D 대 B              (1)(5)
⑤ ★ 격자                 함수 3 × 자리 5 × 컴파일러 2 × -O0/-O2 · 경우 4 × 판 2 × 컴파일러 3  (1)(3)
⑥ 최적화 두 판          -O0 대 -O2 — 접힘이 언어의 것인가 최적화의 것인가                  (1)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★★ **상수 식 문맥에서의 평가는 표준, 그 밖에서 접나는 컴파일러** | **쓴다** |
| ★★★ **② 두 컴파일러** | ★★★ `consteval` 런타임 인자 에러 · 누수 에러 · 넘침·범위 밖 에러 · `constinit` 에러 전문 | **쓴다** |
| ③ ASan / UBSan | ★★ **상수 평가 UB 의 짝** — 런타임은 `done` 만 찍고 조용하다 · UBSan·ASan 이 잡는다((4)) | **쓴다** |
| ★★★ **④ 역어셈블 → 기호표** | ★★★ **`-O0` 의 `probe(int)` 에 `sq` 호출이 남은 칸 7 / 22** · `constinit` 은 **`D`**, 동적 초기화는 **`B` + `_GLOBAL__sub_I`**((5)) | **쓴다** |
| ★★★ **⑤ 격자** | ★★★ **컴파일러 사이 갈린 행 1 / 15(`-O0`) · 0 / 15(`-O2`)** · **판 사이 갈린 묶음 12 / 12 · 컴파일러 사이 0 / 8** | **쓴다** |
| ⑥ 최적화 두 판 | ★★ **`-O2` 는 보통 함수도 접는다** — 호출이 남은 칸 7 → 0 | **쓴다** |

### (1) ★★★ 컴파일 시간 격자 — 함수 셋 × 부르는 자리 다섯

**언제 쓰나** — 「이 함수가 컴파일 시간에 도나?」를 물을 때마다. **답은 함수의 표시가 아니라 부르는 자리가 정한다.**

```cpp
/* cx01.cpp */
// 함수 셋(-DFN=1 constexpr · 2 consteval · 3 보통) × 부르는 자리 다섯(-DSITE=1..5)
template <int N> struct Tag {
    static constexpr int value = N;
};

#if FN == 1
constexpr int sq(int x) { return x * x; }
#elif FN == 2
consteval int sq(int x) { return x * x; }
#elif FN == 3
int sq(int x) { return x * x; }
#endif

int probe([[maybe_unused]] int n) {
#if SITE == 1
    constexpr int v = sq(7);
    return v;
#elif SITE == 2
    static_assert(sq(7) == 49);
    return 0;
#elif SITE == 3
    return sq(n);
#elif SITE == 4
    return Tag<sq(7)>::value;
#elif SITE == 5
    int v = sq(7);
    return v;
#endif
}

int main(int argc, char**) { return probe(argc) == 49; }
```

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

- ★★★ **`constexpr` 함수는 런타임 인자 `sq(n)` 에서 보통 호출이다(호출 1)** — 두 컴파일러 같다. **`constexpr` 은 「상수 평가에 쓸 수 있다」이지 「컴파일 시간에 돈다」가 아니다.**
- ★★★ **`consteval` 은 런타임 인자에서 에러** · 나머지 네 자리는 **호출 0 · 상수** — 「**모든 호출이 상수 식을 만들어야 한다**」((2)에 전문).
- ★★★ **보통 함수는 상수 식 문맥 셋(`constexpr` 변수 · `static_assert` · 템플릿 인자)에서 에러** · 런타임 두 자리에서는 호출이 남는다.
- ★★★ **갈린 한 칸 — `constexpr` 함수를 보통 변수 `int v = sq(7);` 로 받으면 g++ `-O0` 은 상수 49, clang `-O0` 은 호출.** 그 자리는 **상수 식 문맥이 아니다** — 컴파일러가 **할 수도 안 할 수도** 있는 자리이고, 두 컴파일러가 **다르게 골랐다.**

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

- ★★★ **g++ — `movl $0x31,-0x4(%rbp)`** 한 줄(49 를 지역 변수에 넣는다) · **clang — `mov $0x7,%edi` + `call … sq(int)`**(7 을 넘겨 부른다). **같은 소스 · 같은 `-O0`** 이다.
- ★ 이 블록은 **「g++ 가 빠르다」의 근거가 아니다** — 시간은 재지 않았다. 보인 것은 **명령의 모양**뿐이다.

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

- ★★★ **`-O2` 에서는 호출이 남은 칸이 0 / 22** — **보통 함수의 `int v = sq(7)` 도 49 로 접혔다**(`49 있음`). 런타임 인자 `sq(n)` 은 **`sq(int)` 재배치가 사라졌지만 상수도 없다** — 그 자리에 무엇이 들어갔는지는 이 문서가 싣지 않았다.
- ★★ **그래서 「상수만 남았다」는 `-O2` 에서는 언어의 증거가 못 된다** — 최적화기도 같은 일을 한다. **언어가 강제하는 것은 에러 칸(8 / 30)이 `-O0`·`-O2` 에서 같다는 것**뿐이다.

### (2) ★★★ `consteval` 에 런타임 인자 — 에러 전문

**언제 쓰나** — 「이 함수는 **절대** 런타임에 돌면 안 된다」(해시 상수 · 형식 문자열 검사)일 때.

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

- ★★★ **g++ `‘n’ is not a constant expression` · clang `call to consteval function 'sq' is not a constant expression` + `function parameter 'n' with unknown value`** — 두 컴파일러 다 22행 `return sq(n);`.
- ★★ **`constexpr` 판의 같은 줄은 통과하고 보통 호출이 됐다**((1)) — **한 낱말 차이가 「런타임에 돌 수 있나」를 가른다.**

### (3) ★★ C++20 에서 넓어진 것 — 판 격자

**언제 쓰나** — 옛 코드(C++17)에 `constexpr` 을 붙이려다 막힐 때.

```cpp
/* cx20.cpp */
// C++20 에서 넓어진 것 넷 — -DCASE=1..4 로 하나만 켠다. 전부 상수 평가(static_assert) 안에서 쓴다
#include <vector>

#if CASE == 1
struct Shape {
    virtual constexpr int sides() const { return 0; }
};
struct Tri : Shape {
    constexpr int sides() const override { return 3; }
};
constexpr int count() {
    Tri t;
    const Shape& s = t;
    return s.sides();
}
#elif CASE == 2
constexpr int count() {
    int* p = new int(3);
    int v = *p;
    delete p;
    return v;
}
#elif CASE == 3
constexpr int count() {
    std::vector<int> v{1, 2, 3};
    return static_cast<int>(v.size());
}
#elif CASE == 4
constexpr int count() {
    try {
        return 3;
    } catch (...) {
        return 0;
    }
}
#endif

static_assert(count() == 3);
int main() {}
```

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

- ★★★ **판 사이 갈린 묶음 12 / 12 · 컴파일러 사이 갈린 행 0 / 8** — 네 경우 모두 **C++17 에서 막히고 C++20 에서 통과**한다. 세 컴파일러가 같다.
- ★★★ **`constexpr` 가상 함수** — `const Shape&` 로 **가상 호출**을 했는데 상수 평가에서 `Tri::sides` 가 골라졌다(`static_assert(count() == 3)` 통과).
- ★★★ **`constexpr` 안 `std::vector`** — C++20 에서 통과. ★ **g++-12 칸은 libstdc++ 12** 라 **두 번째 라이브러리 판**의 확인이다 — g++ 13 과 clang 18 은 **같은 libstdc++ 13** 이다.
- ★★★ **`try` 블록의 C++17 칸은 「에러」가 아니라 「경고」** — `exit 0` 이다. **종료 코드 0 인데 C++17 로는 ill-formed**(규칙 19-A 고정 항목) —

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

- ★★★ **`-pedantic` 은 경고, `-pedantic-errors` 는 에러** — 같은 진단 문구가 `warning:` 에서 `error:` 로 바뀐다. **「`-std=c++17` 로 통과했다」는 「C++17 코드다」가 아니다.**

**★★★ 상수 평가 안에서 `new` 를 하고 안 지우면**

```cpp
/* leak01.cpp */
// 상수 평가 안의 new — delete 를 빼먹은 판
constexpr int count() {
    int* p = new int(3);
    return *p;
}

static_assert(count() == 3);
int main() {}
```

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

- ★★★ **에러** — g++ `is not a constant expression because allocated storage has not been deallocated` · clang `allocation performed here was not deallocated`. **상수 평가 안의 할당은 그 평가가 끝나기 전에 풀어야** 한다(「일시적 할당」). 두 컴파일러 다 **3행의 `new`** 를 가리킨다.
- ★★ **그래서 `constexpr std::vector` 를 `constexpr` 변수로 남길 수는 없다** — (3)의 `CASE=3` 이 통과한 것은 **벡터가 함수 안에서 죽기** 때문이다.

### (4) ★★★ 상수 평가 안의 UB 는 컴파일 에러 — 런타임 짝과 나란히

**언제 쓰나** — 「이 계산에 넘침이 있나」를 **컴파일러에게 검사시키고** 싶을 때.

**쌍 1 — 부호 있는 정수 넘침**

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

- ★★★ **상수 평가(`-DCONST`)는 에러** — g++ `overflow in constant expression` · clang `value 2147483648 is outside the range of representable values of type 'int'`.
- ★★★ **런타임 판은 도구 없이 `done` · `exit 0`** — **아무 말도 없다.** 값은 **찍지 않았다**(UB 의 한 결과라 결과로 실을 수 없다).
- ★★ **UBSan 을 붙여야 `runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'`** 가 나온다 — 두 컴파일러. **실행 종료 코드는 여전히 0** 이다(UBSan 기본은 계속 진행).

**쌍 2 — 배열 범위 밖 읽기**

```cpp
/* ub02.cpp */
// 배열 범위 밖 읽기 — 상수 평가(-DCONST) 대 런타임. 런타임 판은 값을 찍지 않고 다 돌았다는 표시만 찍는다
#include <cstdio>

constexpr int table[3] = {10, 20, 30};
constexpr int at(int i) { return table[i]; }

int main([[maybe_unused]] int argc, char**) {
#ifdef CONST
    constexpr int v = at(3);
    return v;
#else
    volatile int v = at(argc + 2);
    (void)v;
    std::fprintf(stderr, "done\n");
#endif
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCONST ub02.cpp -o ex (cc exit=1) =====
ub02.cpp: In function ‘int main(int, char**)’:
ub02.cpp:9:25:   in ‘constexpr’ expansion of ‘at(3)’
ub02.cpp:5:41: error: array subscript value ‘3’ is outside the bounds of array ‘table’ of type ‘const int [3]’
    5 | constexpr int at(int i) { return table[i]; }
      |                                  ~~~~~~~^
ub02.cpp:4:15: note: declared here
    4 | constexpr int table[3] = {10, 20, 30};
      |               ^~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCONST ub02.cpp -o ex (cc exit=1) =====
ub02.cpp:9:19: error: constexpr variable 'v' must be initialized by a constant expression
    9 |     constexpr int v = at(3);
      |                   ^   ~~~~~
ub02.cpp:5:34: note: read of dereferenced one-past-the-end pointer is not allowed in a constant expression
    5 | constexpr int at(int i) { return table[i]; }
      |                                  ^
ub02.cpp:9:23: note: in call to 'at(3)'
    9 |     constexpr int v = at(3);
      |                       ^~~~~
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
done
===== clang++ -std=c++20 -Wall -Wextra -pedantic ub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
done
===== g++ -std=c++20 -Wall -Wextra -pedantic -fsanitize=address -g -ffile-prefix-map="$PWD"=. ub02.cpp -o ex && ./ex 2>&1 | grep -E '^(SUMMARY|==[0-9]+==ERROR)' (cc exit=0 · run exit=1) =====
==1713181==ERROR: AddressSanitizer: global-buffer-overflow on address 0x614c5d5fd02c at pc 0x614c5d5fc3ec bp 0x7ffe443b6a50 sp 0x7ffe443b6a40
SUMMARY: AddressSanitizer: global-buffer-overflow ub02.cpp:5 in at(int)
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fsanitize=address -g -ffile-prefix-map="$PWD"=. ub02.cpp -o ex && ./ex 2>&1 | grep -E '^(SUMMARY|==[0-9]+==ERROR)' (cc exit=0 · run exit=1) =====
==1713261==ERROR: AddressSanitizer: global-buffer-overflow on address 0x55a4652fae0c at pc 0x55a4652e7bf6 bp 0x7ffc98f9d9b0 sp 0x7ffc98f9d9a8
SUMMARY: AddressSanitizer: global-buffer-overflow ub02.cpp:5:34 in at(int)
```

- ★★★ **상수 평가는 에러** — g++ `array subscript value ‘3’ is outside the bounds of array ‘table’` · clang `read of dereferenced one-past-the-end pointer is not allowed in a constant expression`.
- ★★★ **런타임은 도구 없이 `done` · `exit 0`** · **ASan 을 붙이면 `global-buffer-overflow`** 로 멈춘다(`run exit=1`).
- ★★ **같은 함수(`at`)** 다 — **상수 평가는 UB 를 허락하지 않는 모드**이고, 그래서 **`static_assert` 에 넣은 테스트는 UB 검사기 노릇을 한다.** 단 **상수 평가에 넣을 수 있는 입력만** 검사한다.

```text
   같은 식 add(INT_MAX, 1)            상수 평가                    런타임(-O0, 도구 없음)       런타임 + UBSan
                                       ★ 컴파일 에러                 done · exit 0 — 침묵          runtime error … (exit 0)
   같은 식 at(3)                       ★ 컴파일 에러                 done · exit 0 — 침묵          ASan global-buffer-overflow (exit 1)
```

### (5) ★★ `constinit` — 시작 전에 끝난 초기화

**언제 쓰나** — 전역·정적 변수가 **다른 번역 단위의 전역보다 먼저 초기화된다는 보장**이 필요할 때(정적 초기화 순서 문제).

```cpp
/* cinit01.cpp */
// 전역 변수 초기화 세 모양 — constinit + 상수 식(기본) · constinit + 보통 함수(-DDYNAMIC) · constinit 없이 보통 함수(-DPLAIN)
#include <cstdio>

constexpr int base() { return 40; }
int runtime_base() { return 40; }

#if defined(DYNAMIC)
constinit int counter = runtime_base();
#elif defined(PLAIN)
int counter = runtime_base();
#else
constinit int counter = base();
#endif

int main() {
    counter += 2;
    std::printf("%d\n", counter);
}
```

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

- ★★★ **`constinit int counter = runtime_base();` 는 에러** — g++ `‘constinit’ variable ‘counter’ does not have a constant initializer` · clang `variable does not have a constant initializer` + `required by 'constinit' specifier here`.

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

- ★★★ **`constinit` 판(기본)은 `D counter` — 초기값 40 이 데이터 영역에 이미 들어 있다** · 초기화 함수 기호가 **없다.**
- ★★★ **`constinit` 없는 `-DPLAIN` 판은 `B counter`(0 으로 시작) + `_GLOBAL__sub_I_…` 초기화 함수** — **프로그램 시작 때 `runtime_base()` 를 불러** 40 을 넣는다(동적 초기화). 두 컴파일러 같다(기호 이름만 다르다 — g++ `__static_initialization_and_destruction_0` · clang `__cxx_global_var_init`).
- ★★ **다른 번역 단위의 동적 초기화가 이 `counter` 를 읽으면** `-DPLAIN` 판은 **아직 0 일 수 있다**(순서가 번역 단위 사이에서 정해져 있지 않다) — 이 편은 **그 두 번역 단위 실험을 던지지 않았다.** `constinit` 은 **그 가능성을 컴파일 에러로 없앤다.**
- ★★ **`constinit` 은 `const` 가 아니다** — `counter += 2` 가 통과하고 `42` 를 찍는다.

### (6) ★ `if consteval`(C++23) — 상수 평가인지 묻기

**언제 쓰나** — 한 함수가 **상수 평가에서는 A, 런타임에서는 B**(예: 런타임에서만 SIMD)로 가야 할 때.

```cpp
/* ifcv01.cpp */
// if consteval(C++23) — 같은 함수를 상수 평가와 런타임에서 부른다
#include <cstdio>

constexpr int where() {
    if consteval {
        return 1;
    } else {
        return 2;
    }
}

int main() {
    constexpr int a = where();
    int b = where();
    std::printf("%d %d\n", a, b);
}
```

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

- ★★★ **`1 2`** — `constexpr int a = where();` 는 상수 평가라 **1**, `int b = where();` 는 **2**. 두 컴파일러 같다.
- ★★ **`-std=c++20` 에서도 경고 한 줄과 함께 통과**(`-Wc++23-extensions`) — 여기도 **종료 코드 0 인데 그 판으로는 ill-formed** 인 자리다.
- ★ **`int b = where();` 가 2 라는 것은 (1)의 g++ 「보통 변수 칸이 상수로 접혔다」와 모순이 아니다** — 컴파일러가 결과를 미리 계산해 넣더라도 **그 평가는 「상수 평가」가 아니라** `if consteval` 은 거짓이다(`-O0` 의 두 컴파일러에서 `2`).

## 문법 — 형태와 규칙

### 형태

```text
   constexpr int f(int);          상수 평가에 「쓸 수 있다」 — 런타임 인자면 보통 호출
   consteval int g(int);          즉시 함수 — 모든 호출이 상수 식이어야
   constexpr int v = f(7);        constexpr 변수 — 초기화가 상수 식이어야 · const 가 붙는다
   constinit int c = f(7);        정적 초기화를 요구 — const 가 아니다 (C++20)
   static_assert(f(7) == 49);     상수 식 문맥
   Tag<f(7)>                      템플릿 인자 — 상수 식 문맥
   if consteval { … } else { … }  상수 평가 중인가 (C++23)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(6)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **상수 식 문맥(`constexpr` 변수 · `static_assert` · 템플릿 인자)에서만 컴파일 시간 평가가 강제된다**((1)).
- ★★★ **`constexpr` 함수는 런타임 인자로 보통 호출된다 · `consteval` 은 에러다**((1)(2)).
- ★★★ **상수 평가 안의 UB(넘침·범위 밖)는 컴파일 에러다 — 런타임에서는 조용하다**((4)).
- ★★★ **상수 평가 안의 `new` 는 평가가 끝나기 전에 `delete` 해야 한다**((3)).
- ★★ **C++20 — 가상 함수 · `new`/`delete` · `std::vector` · `try` 블록이 상수 평가 안으로**((3)).
- ★★ **`constinit` 은 동적 초기화를 막는다 — `const` 는 아니다**((5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `consteval` 함수에 런타임 인자 | `‘n’ is not a constant expression` | `call to consteval function 'sq' is not a constant expression` | (2) |
| 보통 함수를 `constexpr` 변수·`static_assert`·템플릿 인자에 | (에러 — 격자 칸) | (에러 — 격자 칸) | (1) |
| 상수 평가 안 `new` 후 `delete` 없음 | `allocated storage has not been deallocated` | `allocation performed here was not deallocated` | (3) |
| `constexpr int v = add(INT_MAX, 1);` | `overflow in constant expression` | `value 2147483648 is outside the range …` | (4) |
| `constexpr int v = at(3);`(길이 3) | `array subscript value ‘3’ is outside the bounds …` | `read of dereferenced one-past-the-end pointer …` | (4) |
| `constinit` 에 비-`constexpr` 함수 | `does not have a constant initializer` | `variable does not have a constant initializer` | (5) |

## 어디서 틀리나

### 1. ★★★ 「`constexpr` 함수는 컴파일 시간에 계산된다」

(1)이 반증이다 — **런타임 인자면 `-O0` 두 컴파일러 다 `call sq(int)`.** 상수 식 문맥이 아닌 자리는 **컴파일러의 선택**이다(보통 변수 칸이 g++·clang 에서 갈렸다).

### 2. ★★★ 「역어셈블에 상수만 남았으니 컴파일 시간 계산이다」

(1)의 `-O2` 격자가 반증이다 — **보통 함수도 `49` 로 접혔다.** 언어의 강제를 보려면 **`-O0` 과 에러 칸**을 본다.

### 3. ★★★ 「`constexpr` 함수 안의 넘침은 런타임과 똑같이 조용하다」

(4)가 반증이다 — **상수 평가에서는 컴파일 에러.** 런타임에서만 조용하다.

### 4. ★★ 「`-std=c++17` 로 컴파일이 통과했으니 C++17 코드다」

(3)(6)이 반증이다 — **`try` 블록 · `if consteval` 이 경고 한 줄과 `exit 0`.** `-pedantic-errors` 라야 에러다.

### 5. ★★ 「`constinit` 은 `constexpr` 처럼 값을 못 바꾸게 한다」

(5)가 반증이다 — **`counter += 2` 가 통과하고 42.**

### 6. ★★ 「`constexpr` 이면 `std::vector` 를 상수로 들고 있을 수 있다」

(3)이 반증이다 — **할당은 평가가 끝나기 전에 풀어야 한다**(안 풀면 누수 에러). 함수 **안에서** 쓰고 버리는 것만 된다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 경계는 「상수 식 문맥인가」 하나다** — 그 안에서는 **표준이** 평가와 에러를 강제하고, 그 밖에서는 **컴파일러와 최적화기가** 무엇이든 한다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **상수 식 문맥의 평가** · **`consteval` 의 런타임 호출 금지** · **상수 평가 안 UB·누수 = ill-formed** · **`constinit` = 정적 초기화 아니면 ill-formed** | 두 컴파일러 에러 · cppreference | ★★ **「컴파일 시간에 돌았다」 자체는 역어셈블의 모양으로만** 봤다 — 표준은 결과만 정한다 |
| **조건부 표준** | 특정 판에서만 | ★★★ **C++20 의 넷**((3)) · **`if consteval` C++23** | 판 격자 · 세 컴파일러 | ★ **`constexpr std::vector` 는 라이브러리 두 판(12·13)만** |
| **구현 정의 · ABI** | 문서화 의무 | ★★ **`D`/`B` · `_GLOBAL__sub_I` 라는 기호**((5)) | `nm -C` | ★ 다른 ABI 는 던지지 않았다 |
| **컴파일러의 것** | 표준 밖 | ★★★ **상수 식 문맥 밖에서 접나**(g++ 접음 · clang 호출 — `-O0`) · **`-O2` 의 접힘** · 진단 문구 · **`-pedantic` 이 경고냐 에러냐** | 역어셈블 격자 | ★★★ **시간은 재지 않았다** — 「빠르다」는 이 문서에 없다 |
| **UB** | 아무 일이나 | ★★★ **런타임의 넘침·범위 밖**((4)) — **값을 싣지 않았다** | UBSan · ASan | ★★ **도구 없는 런타임 판은 `done` 만** — 무엇을 읽었는지는 결과로 싣지 않는다 |

### ★★ 종료 코드 0인데 ill-formed — 이 편에서 두 자리

- ★★★ **`-std=c++17` 의 `constexpr` 안 `try`** · **`-std=c++20` 의 `if consteval`** — 둘 다 **경고 한 줄 · `cc exit=0`**. `-pedantic-errors` 로 에러가 된다((3)에 전문).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 상수로도 런타임으로도 쓰는 계산 | ★★★ **`constexpr` 함수** | (1) — 자리가 정한다 |
| 반드시 컴파일 시간 | ★★★ **`consteval`** 또는 **결과를 `constexpr` 변수로 받기** | (1)(2) |
| 결과가 상수로 박히는지 확인 | ★★ **`constexpr` 변수 · `static_assert` 에 넣는다** — 역어셈블(`-O2`)을 믿지 않는다 | (1) |
| 계산식의 UB 를 컴파일러로 검사 | ★★★ **`static_assert` 로 상수 평가시킨다** | (4) — 넣은 입력만 검사된다 |
| 전역의 초기화 순서가 걱정 | ★★★ **`constinit`** | (5) — 동적 초기화면 에러 |
| 전역이지만 고쳐 쓴다 | ★★ **`constinit`**(`constexpr` 은 `const`) | (5) |
| 상수 평가와 런타임에서 다른 구현 | ★ **`if consteval`(C++23)** · C++20 은 `std::is_constant_evaluated()` | (6) |

## 핵심 문장

- ★★★ **컴파일 시간 평가를 강제하는 것은 함수 표시가 아니라 부르는 자리다** — `constexpr` 함수는 `sq(n)` 에서 `-O0` 두 컴파일러 다 호출을 남겼다(호출이 남은 칸 7 / 22).
- ★★★ **`consteval` 은 런타임 인자면 에러** — 「모든 호출이 상수 식」.
- ★★★ **상수 식 문맥 밖은 컴파일러의 것** — `int v = sq(7)` 을 g++ 는 접고 clang 은 불렀다(`-O0`) · `-O2` 는 보통 함수도 접는다.
- ★★★ **상수 평가 안 UB 는 컴파일 에러, 런타임은 `done` · `exit 0`** — 넘침·범위 밖 두 쌍.
- ★★ **C++20 의 넷(가상 · `new`/`delete` · `vector` · `try`)은 판 사이 12 / 12 로 갈린다** — `new` 는 평가 안에서 풀어야 한다.
- ★★ **`constinit` 은 `D`(정적) 대 `B`+`_GLOBAL__sub_I`(동적)를 가르는 단언이고 `const` 가 아니다.**

## 관련 자료

- [31번](../31-function-templates-and-argument-deduction/) — 템플릿 인자는 상수 식이다 — (1)의 `Tag<sq(7)>` 칸.
- [37번](../37-sfinae-and-enable-if/) (4) — ★★ **`if constexpr`** — 여기의 `if consteval` 과 이름만 닮았다. 앞은 **가지를 버리고**, 뒤는 **평가 모드를 묻는다.**
- [30번](../30-dangling-references-and-lifetime-extension/) — ★★ **런타임 UB 를 ASan 으로 묻는 법** — (4)의 런타임 짝이 그 방식이다.
- [25번](../25-static-members-and-inline-variables/) — 정적 변수의 정의 자리 — (5)의 `constinit` 은 **초기화 시점** 쪽이다.
- Rust 갈래 [07번](../../../rust/syntax/07-const-static-and-const-fn/) — ★★ **`const fn` 도 「상수 자리면 컴파일 타임 평가가 의무(E0080), 런타임 자리면 보통 호출(패닉)」** — (1)의 `constexpr` 과 같은 모양이다.

## 용어 풀이

> **상수 식 문맥(constant-evaluated context)** — 값이 컴파일 시간에 필요한 자리. `constexpr` 변수 초기화 · `static_assert` · 템플릿 인자 · 배열 크기 등.\
> 예: (1)의 자리 1·2·4.

> **상수 평가(constant evaluation)** — 컴파일러가 식을 **실행해 보는** 것. UB 를 만나면 **에러로 멈춘다.**\
> 예: (4).

> **즉시 함수(immediate function)** — `consteval` 함수. 모든 호출이 상수 식이어야 한다.\
> 예: (2).

> **일시적 할당(transient allocation)** — 상수 평가 안의 `new` 는 **그 평가가 끝나기 전에 풀려야** 한다.\
> 예: (3)의 `leak01.cpp`.

> **정적 초기화 / 동적 초기화** — 앞은 **프로그램이 시작하기 전에** 값이 들어가 있는 것(0 초기화·상수 초기화), 뒤는 **시작할 때 코드가 돌아** 값을 넣는 것.\
> 예: (5)의 `D counter` 대 `B counter` + `_GLOBAL__sub_I_…`.

> **`R_X86_64_PLT32`** — `.o` 안의 **아직 안 풀린 함수 호출 자리**를 적은 재배치. `objdump -dr` 가 그 줄로 **무엇을 부르려는지** 보여 준다.\
> 예: (1)의 clang `-O0` 판.

## 더 들어가면

- **`std::is_constant_evaluated()`(C++20)** — `if consteval` 의 앞 판. `if constexpr (std::is_constant_evaluated())` 로 쓰면 **항상 참**이 되는 함정이 알려져 있다 — 이 편은 **던지지 않았다.**
- **정적 초기화 순서 문제의 두 번역 단위 실험** — (5)는 기호표로 「동적 초기화가 생긴다」까지만 보였다. 실제로 **0 을 읽는 판**은 던지지 않았다.
- **`constexpr` 소멸자 · `constexpr std::string`** — C++20. 이 편은 `vector` 만 봤다.
