# cpp/syntax/39 — 람다와 캡처 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소·`pc`/`bp`/`sp` · 진단 문구** 다.\
> 근거로 쓰는 것은 다음이다 — **리포트 이름 · `SUMMARY` 의 `파일:줄` · `cc exit`/`run exit` · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **리포트 12 칸 — `[&x]`·`[&]`·`[this]` 의 「돌려준 뒤」는 `stack-use-after-return`, 「스코프 밖」은 `stack-use-after-scope`(두 컴파일러 같다)** · 값 칸 — 즉시는 참조 캡처 **7** · 값 캡처 **42**, 나머지 **42** · **`[p = std::move(p)]` × `std::function` 은 컴파일 에러** · ★★ `uar=0` 이면 **`use-after-return` 여섯 칸이 사라진다** · ★★ 경고는 **12 칸 중 2 칸**(clang 의 `[&x]`·`[&]` 반환)

**출력**

```bash
# cap-grid.sh
# cap-grid.sh — 캡처 일곱 × 부르는 때 셋. 열: 경고 두 판 · ASan 두 판(ASAN_OPTIONS 없이) · detect_stack_use_after_return=0 인 ASan 두 판.
# ASan 칸에는 리포트 이름, 리포트가 없으면 찍힌 값을 적는다. =0 칸은 값을 적지 않는다(댕글링이면 UB 의 한 결과라서)
caps=('1 [x]' '2 [&x]' '3 [=]' '4 [&]' '5 [this]' '6 [*this]' '7 [p = std::move(p)]')
whens=('1 즉시' '2 돌려준 뒤' '3 std::function 스코프 밖')
W='-std=c++20 -Wall -Wextra -pedantic'
A='-std=c++20 -O0 -fsanitize=address -g'
echo "ASAN_OPTIONS 환경 변수 = ${ASAN_OPTIONS-(설정 안 됨)}"
warn() {
  local out
  if ! out=$($1 $W -DCAP=$2 -DWHEN=$3 -c cap01.cpp -o /dev/null 2>&1); then printf 'cc 에러'; return; fi
  out=$(printf '%s\n' "$out" | grep -oE 'warning: .*\[-W[a-z-]+\]' | grep -oE '\-W[a-z-]+' | sort -u | tr '\n' ' ')
  printf '%s' "${out:--}"
}
# 한 번 빌드해 세 번 돌린다 — ASAN_OPTIONS 없이 · detect_stack_use_after_return=1 · =0
kind() { printf '%s\n' "$1" | grep -m 1 '^SUMMARY: AddressSanitizer:' | sed -E 's/^SUMMARY: AddressSanitizer: ([A-Za-z-]+).*/\1/'; }
asan() {
  local rd r1 r0 k
  if ! $1 $A -DCAP=$2 -DWHEN=$3 cap01.cpp -o gx 2>/dev/null; then printf 'cc 에러\tcc 에러'; return; fi
  rd=$(env -u ASAN_OPTIONS ./gx 2>&1)
  r1=$(ASAN_OPTIONS=detect_stack_use_after_return=1 ./gx 2>&1)
  r0=$(ASAN_OPTIONS=detect_stack_use_after_return=0 ./gx 2>&1)
  [ "$(kind "$rd")" = "$(kind "$r1")" ] || echo "$1 CAP=$2 WHEN=$3" >> diff1.txt
  k=$(kind "$rd")
  if [ -n "$k" ]; then printf '%s' "$k"; else printf '값 %s' "$(printf '%s\n' "$rd" | head -n 1)"; fi
  k=$(kind "$r0")
  printf '\t%s' "${k:-리포트 없음}"
}
: > diff1.txt
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "캡처" "부르는 때" "g++ 경고" "clang 경고" "g++ ASan 기본" "clang ASan 기본" "g++ ASan uar=0" "clang ASan uar=0" > t.tsv
for k in "${caps[@]}"; do
  for w in "${whens[@]}"; do
    n="${k%% *}"; m="${w%% *}"
    ga=$(asan g++ $n $m); ca=$(asan clang++ $n $m)
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$k" "$w" "$(warn g++ $n $m)" "$(warn clang++ $n $m)" \
      "${ga%%$'\t'*}" "${ca%%$'\t'*}" "${ga#*$'\t'}" "${ca#*$'\t'}" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 8' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
cc=$(tail -n +2 t.tsv | awk -F'\t' '$5 == "cc 에러"' | wc -l)
runnable=$(( (rows - cc) * 2 ))
dang=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=5;i<=6;i++) if ($i ~ /use-after|overflow/) n++ } END { print n+0 }')
lost=$(tail -n +2 t.tsv | awk -F'\t' '{ if ($5 ~ /use-after/ && $7 == "리포트 없음") n++; if ($6 ~ /use-after/ && $8 == "리포트 없음") n++ } END { print n+0 }')
warned=$(tail -n +2 t.tsv | awk -F'\t' '{ if ($5 ~ /use-after/ && $3 != "-") n++; if ($6 ~ /use-after/ && $4 != "-") n++ } END { print n+0 }')
echo "ASAN_OPTIONS 없이 돌린 칸과 detect_stack_use_after_return=1 칸의 리포트가 다른 칸 $(wc -l < diff1.txt)"
echo "댕글링 칸 $dang / $runnable · 그중 uar=0 이면 리포트가 사라지는 칸 $lost / $dang · 같은 판 경고가 난 칸 $warned / $dang · 컴파일이 안 된 행 $cc / $rows"
rm -f gx t.tsv diff1.txt
```

```text
===== bash cap-grid.sh (exit=0) =====
ASAN_OPTIONS 환경 변수 = (설정 안 됨)
캡처	부르는 때	g++ 경고	clang 경고	g++ ASan 기본	clang ASan 기본	g++ ASan uar=0	clang ASan uar=0
1 [x]	1 즉시	-	-	값 42	값 42	리포트 없음	리포트 없음
1 [x]	2 돌려준 뒤	-	-	값 42	값 42	리포트 없음	리포트 없음
1 [x]	3 std::function 스코프 밖	-	-	값 42	값 42	리포트 없음	리포트 없음
2 [&x]	1 즉시	-	-	값 7	값 7	리포트 없음	리포트 없음
2 [&x]	2 돌려준 뒤	-	-Wreturn-stack-address 	stack-use-after-return	stack-use-after-return	리포트 없음	리포트 없음
2 [&x]	3 std::function 스코프 밖	-	-	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope
3 [=]	1 즉시	-	-	값 42	값 42	리포트 없음	리포트 없음
3 [=]	2 돌려준 뒤	-	-	값 42	값 42	리포트 없음	리포트 없음
3 [=]	3 std::function 스코프 밖	-	-	값 42	값 42	리포트 없음	리포트 없음
4 [&]	1 즉시	-	-	값 7	값 7	리포트 없음	리포트 없음
4 [&]	2 돌려준 뒤	-	-Wreturn-stack-address 	stack-use-after-return	stack-use-after-return	리포트 없음	리포트 없음
4 [&]	3 std::function 스코프 밖	-	-	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope
5 [this]	1 즉시	-	-	값 7	값 7	리포트 없음	리포트 없음
5 [this]	2 돌려준 뒤	-	-	stack-use-after-return	stack-use-after-return	리포트 없음	리포트 없음
5 [this]	3 std::function 스코프 밖	-	-	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope	stack-use-after-scope
6 [*this]	1 즉시	-	-	값 42	값 42	리포트 없음	리포트 없음
6 [*this]	2 돌려준 뒤	-	-	값 42	값 42	리포트 없음	리포트 없음
6 [*this]	3 std::function 스코프 밖	-	-	값 42	값 42	리포트 없음	리포트 없음
7 [p = std::move(p)]	1 즉시	-	-	값 42	값 42	리포트 없음	리포트 없음
7 [p = std::move(p)]	2 돌려준 뒤	-	-	값 42	값 42	리포트 없음	리포트 없음
7 [p = std::move(p)]	3 std::function 스코프 밖	cc 에러	cc 에러	cc 에러	cc 에러	cc 에러	cc 에러
ASAN_OPTIONS 없이 돌린 칸과 detect_stack_use_after_return=1 칸의 리포트가 다른 칸 0
댕글링 칸 12 / 40 · 그중 uar=0 이면 리포트가 사라지는 칸 6 / 12 · 같은 판 경고가 난 칸 2 / 12 · 컴파일이 안 된 행 1 / 21
```

```text
===== g++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DCAP=2 -DWHEN=2 cap01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
=================================================================
==1739903==ERROR: AddressSanitizer: stack-use-after-return on address 0x78c2a3b00060 at pc 0x6495dfaa42f5 bp 0x7fff26ef2a90 sp 0x7fff26ef2a80
READ of size 4 at 0x78c2a3b00060 thread T0
    #0 0x6495dfaa42f4 in operator() cap01.cpp:54
    #1 0x6495dfaa44c2 in main cap01.cpp:63

Address 0x78c2a3b00060 is located in stack of thread T0 at offset 32 in frame
    #0 0x6495dfaa4308 in make() cap01.cpp:52

    [32, 36) 'x' (line 53) <== Memory access at offset 32 is inside this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-return cap01.cpp:54 in operator()
```

**왜 그런가**

- ★★★ **참조로 잡는 셋은 대상의 주소를 든다** — `make()` 가 돌아가면 그 프레임이, 블록이 끝나면 그 지역이 **죽는다.** 읽는 순간이 UB 이고 ASan 이 이름을 댄다.
- ★★★ **「돌려준 뒤」는 돌아간 프레임이라 `use-after-return`** — 이것을 보려면 ASan 이 돌아간 프레임을 **가짜 스택으로 옮겨 두는** 기능(`detect_stack_use_after_return`)이 켜져 있어야 한다. 이 판은 **기본값이 켜짐**(기본과 `=1` 이 다른 칸 0)이고, **`=0` 이면 여섯 칸이 전부 침묵**한다.
- ★★ **「스코프 밖」은 같은 함수 안의 끝난 블록**이라 `use-after-scope` — 그 옵션과 무관하다.
- ★★ **즉시 칸의 7 대 42** — 참조 캡처는 **부른 때**의 원본을, 값 캡처는 **만든 때**의 복사본을 읽는다.

### 2. ★★★ **`[=]` 는 C++20 에서만 경고(g++ `-Wdeprecated` · clang `-Wdeprecated-this-capture`) · `[=, this]` 는 C++14·17 에서 경고(`-Wc++20-extensions`) · `[=, *this]` 는 C++14 에서만 경고(`-Wc++17-extensions`)** — **에러 칸 0 · 침묵 10 / 18**

**출력**

```bash
# this-grid.sh
# this-grid.sh — [=] · [=, this] · [=, *this] × 판 셋 × 컴파일러 둘. 칸에는 경고 옵션 이름 · 에러 · - 를 찍는다
forms=('1 [=]' '2 [=, this]' '3 [=, *this]')
cell() {
  local out rc w
  out=$($1 -std="$2" -Wall -Wextra -pedantic -DFORM="$3" thiscap.cpp -o ex 2>&1); rc=$?
  [ "$rc" -ne 0 ] && { printf '에러'; return; }
  w=$(printf '%s\n' "$out" | grep -oE 'warning: .*\[-W[a-z0-9+-]+\]' | grep -oE '\[-W[a-z0-9+-]+\]' | tr -d '[]' | sort -u | tr '\n' ' ')
  printf '%s' "${w:--}"
}
printf '%s\t%s\t%s\t%s\n' "캡처 목록" "판" "g++" "clang++" > t.tsv
for f in "${forms[@]}"; do
  for s in c++14 c++17 c++20; do
    printf '%s\t%s\t%s\t%s\n' "$f" "$s" "$(cell g++ $s "${f%% *}")" "$(cell clang++ $s "${f%% *}")" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
split=$(tail -n +2 t.tsv | awk -F'\t' '$3 != $4' | wc -l)
quiet=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i == "-") n++ } END { print n+0 }')
echo "컴파일러 사이 갈린 행 $split / $rows · 경고도 에러도 없는 칸 $quiet / $(( rows * 2 ))"
rm -f ex t.tsv
```

```text
===== bash this-grid.sh (exit=0) =====
캡처 목록	판	g++	clang++
1 [=]	c++14	-	-
1 [=]	c++17	-	-
1 [=]	c++20	-Wdeprecated 	-Wdeprecated-this-capture 
2 [=, this]	c++14	-Wc++20-extensions 	-Wc++20-extensions 
2 [=, this]	c++17	-Wc++20-extensions 	-Wc++20-extensions 
2 [=, this]	c++20	-	-
3 [=, *this]	c++14	-Wc++17-extensions 	-Wc++17-extensions 
3 [=, *this]	c++17	-	-
3 [=, *this]	c++20	-	-
컴파일러 사이 갈린 행 1 / 9 · 경고도 에러도 없는 칸 10 / 18
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 thiscap.cpp -o ex (cc exit=0) =====
thiscap.cpp: In lambda function:
thiscap.cpp:8:18: warning: implicit capture of ‘this’ via ‘[=]’ is deprecated in C++20 [-Wdeprecated]
    8 |         auto f = [=] { return v; };
      |                  ^
thiscap.cpp:8:18: note: add explicit ‘this’ or ‘*this’ capture
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 thiscap.cpp -o ex (cc exit=0) =====
thiscap.cpp:8:31: warning: implicit capture of 'this' with a capture default of '=' is deprecated [-Wdeprecated-this-capture]
    8 |         auto f = [=] { return v; };
      |                               ^
thiscap.cpp:8:19: note: add an explicit capture of 'this' to capture '*this' by reference
    8 |         auto f = [=] { return v; };
      |                   ^
      |                    , this
1 warning generated.
===== clang++ -std=c++20 -Wall -Wextra -pedantic -Wdeprecated -DFORM=1 thiscap.cpp -o ex (cc exit=0) =====
thiscap.cpp:8:31: warning: implicit capture of 'this' with a capture default of '=' is deprecated [-Wdeprecated-this-capture]
    8 |         auto f = [=] { return v; };
      |                               ^
thiscap.cpp:8:19: note: add an explicit capture of 'this' to capture '*this' by reference
    8 |         auto f = [=] { return v; };
      |                   ^
      |                    , this
1 warning generated.
```

**왜 그런가**

- ★★★ **`[=]` 로 멤버를 쓰면 `this` 가 암묵적으로 캡처**되고, C++20 이 그것을 **폐기**했다(7번).
- ★★ **`[=, this]` 는 C++20 에서 들어온 문법 · `[*this]` 는 C++17** — 그 전 판에서는 **확장으로 받아 경고 한 줄 · `exit 0`**. 종료 코드 0 인데 그 판으로는 ill-formed 다.
- ★ 갈린 한 행은 **경고 옵션의 이름**만 다르다.

### 3. ★★ **`-DMUT` 없이는 에러**(g++ `increment of read-only variable ‘n’` · clang `cannot assign to a variable captured by copy in a non-mutable lambda`) · **`-DMUT` 는 `1` · `2` · `copy 3` · `inc 3` · `outer n = 0`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic mut01.cpp -o ex (cc exit=1) =====
mut01.cpp: In lambda function:
mut01.cpp:9:33: error: increment of read-only variable ‘n’
    9 |     auto inc = [n]() { return ++n; };
      |                                 ^
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic mut01.cpp -o ex (cc exit=1) =====
mut01.cpp:9:31: error: cannot assign to a variable captured by copy in a non-mutable lambda
    9 |     auto inc = [n]() { return ++n; };
      |                               ^ ~
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DMUT mut01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
call 1 -> 1
call 2 -> 2
copy   -> 3
inc    -> 3
outer n = 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DMUT mut01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
call 1 -> 1
call 2 -> 2
copy   -> 3
inc    -> 3
outer n = 0
```

**왜 그런가**

- ★★★ **람다의 `operator()` 는 기본이 `const`** — 값 캡처 멤버를 못 고친다. `mutable` 이 그 `const` 를 뗀다.
- ★★ **바뀌는 것은 람다 안의 복사본** — 원본은 0. **`auto copy = inc;` 는 상태(2)까지 복사**해 둘이 따로 3 이 된다.

### 4. ★★★ **`std::function` 은 두 컴파일러 다 에러(`std::function target must be copy-constructible`)** · **`std::move_only_function` 은 `42 1`** · **`-std=c++20` 의 `-DMOF` 는 에러(`move_only_function` 없음)**

**출력**

```text
===== g++ -std=c++23 -Wall -Wextra -pedantic mo01.cpp -o ex (cc exit=1) =====
In file included from /usr/include/c++/13/functional:59,
                 from mo01.cpp:3:
/usr/include/c++/13/bits/std_function.h: In instantiation of ‘std::function<_Res(_ArgTypes ...)>::function(_Functor&&) [with _Functor = main()::<lambda()>; _Constraints = void; _Res = int; _ArgTypes = {}]’:
mo01.cpp:13:41:   required from here
/usr/include/c++/13/bits/std_function.h:439:69: error: static assertion failed: std::function target must be copy-constructible
  439 |           static_assert(is_copy_constructible<__decay_t<_Functor>>::value,
      |                                                                     ^~~~~
/usr/include/c++/13/bits/std_function.h:439:69: note: ‘std::integral_constant<bool, false>::value’ evaluates to false
```

```text
===== clang++ -std=c++23 -Wall -Wextra -pedantic mo01.cpp -o ex (cc exit=1) =====
In file included from mo01.cpp:3:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/functional:59:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:439:18: error: static assertion failed due to requirement 'is_copy_constructible<(lambda at mo01.cpp:9:14)>::value': std::function target must be copy-constructible
  439 |           static_assert(is_copy_constructible<__decay_t<_Functor>>::value,
      |                         ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
mo01.cpp:13:30: note: in instantiation of function template specialization 'std::function<int ()>::function<(lambda at mo01.cpp:9:14), void>' requested here
   13 |     std::function<int()> g = std::move(f);
      |                              ^
In file included from mo01.cpp:3:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/functional:59:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:161:14: error: call to implicitly-deleted copy constructor of '(lambda at mo01.cpp:9:14)'
  161 |               = new _Functor(std::forward<_Fn>(__f));
      |                     ^        ~~~~~~~~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:215:6: note: in instantiation of function template specialization 'std::_Function_base::_Base_manager<(lambda at mo01.cpp:9:14)>::_M_create<const (lambda at mo01.cpp:9:14) &>' requested here
  215 |             _M_create(__functor, std::forward<_Fn>(__f), _Local_storage());
      |             ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:198:8: note: in instantiation of function template specialization 'std::_Function_base::_Base_manager<(lambda at mo01.cpp:9:14)>::_M_init_functor<const (lambda at mo01.cpp:9:14) &>' requested here
  198 |               _M_init_functor(__dest,
      |               ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:282:13: note: in instantiation of member function 'std::_Function_base::_Base_manager<(lambda at mo01.cpp:9:14)>::_M_manager' requested here
  282 |             _Base::_M_manager(__dest, __source, __op);
      |                    ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/std_function.h:452:35: note: in instantiation of member function 'std::_Function_handler<int (), (lambda at mo01.cpp:9:14)>::_M_manager' requested here
  452 |               _M_manager = &_My_handler::_M_manager;
      |                                          ^
mo01.cpp:13:30: note: in instantiation of function template specialization 'std::function<int ()>::function<(lambda at mo01.cpp:9:14), void>' requested here
   13 |     std::function<int()> g = std::move(f);
      |                              ^
mo01.cpp:9:15: note: copy constructor of '(lambda at mo01.cpp:9:14)' is implicitly deleted because field '' has a deleted copy constructor
    9 |     auto f = [p = std::move(p)] { return *p; };
      |               ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unique_ptr.h:522:7: note: 'unique_ptr' has been explicitly marked deleted here
  522 |       unique_ptr(const unique_ptr&) = delete;
      |       ^
2 errors generated.
```

```text
===== g++ -std=c++23 -Wall -Wextra -pedantic -DMOF mo01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
42 1
===== clang++ -std=c++23 -Wall -Wextra -pedantic -DMOF mo01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
42 1
===== g++ -std=c++20 -Wall -Wextra -pedantic -DMOF mo01.cpp -o ex (cc exit=1) =====
mo01.cpp: In function ‘int main()’:
mo01.cpp:11:10: error: ‘move_only_function’ is not a member of ‘std’
   11 |     std::move_only_function<int()> g = std::move(f);
      |          ^~~~~~~~~~~~~~~~~~
mo01.cpp:11:36: error: ‘g’ was not declared in this scope
   11 |     std::move_only_function<int()> g = std::move(f);
      |                                    ^
```

**왜 그런가**

- ★★★ 8번의 사슬 — **`unique_ptr` 복사 금지 → 클로저 복사 금지 → `std::function` 은 복사 가능한 것만** 담는다.
- ★★ **`1` 은 `p == nullptr`** — 원래 `p` 는 초기화 캡처로 **옮겨져** 비었다.

### 5. ★ **`42 2.5` · `7 2.5`** · **`-DBAD` 는 에러(`vector<T>` 와 `int` 가 안 맞는다)** · **`twice` 의 `operator()` 는 `<int>`·`<double>` 두 벌**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic gen01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
42 2.5
7 2.5
===== clang++ -std=c++20 -Wall -Wextra -pedantic gen01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
42 2.5
7 2.5
===== g++ -std=c++20 -O0 -c gen01.cpp -o gen.o && nm -C gen.o | grep -F 'lambda' (exit=0) =====
0000000000000012 t auto main::{lambda(auto:1)#1}::operator()<double>(double) const
0000000000000000 t auto main::{lambda(auto:1)#1}::operator()<int>(int) const
000000000000004a t auto main::{lambda<typename $T0>(std::vector<$T0, std::allocator<$T0> > const&)#1}::operator()<double>(std::vector<double, std::allocator<double> > const&) const
000000000000002a t auto main::{lambda<typename $T0>(std::vector<$T0, std::allocator<$T0> > const&)#1}::operator()<int>(std::vector<int, std::allocator<int> > const&) const
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DBAD gen01.cpp -o ex (cc exit=1) =====
gen01.cpp: In function ‘int main()’:
gen01.cpp:12:30: error: no match for call to ‘(main()::<lambda(const std::vector<T>&)>) (int)’
   12 |     std::printf("%d\n", first(42));
      |                         ~~~~~^~~~
gen01.cpp:8:18: note: candidate: ‘template<class T> main()::<lambda(const std::vector<T>&)>’
    8 |     auto first = []<typename T>(const std::vector<T>& v) { return v.front(); };
      |                  ^
gen01.cpp:8:18: note:   template argument deduction/substitution failed:
gen01.cpp:12:30: note:   mismatched types ‘const std::vector<T>’ and ‘int’
   12 |     std::printf("%d\n", first(42));
      |                         ~~~~~^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DBAD gen01.cpp -o ex (cc exit=1) =====
gen01.cpp:12:25: error: no matching function for call to object of type '(lambda at gen01.cpp:8:18)'
   12 |     std::printf("%d\n", first(42));
      |                         ^~~~~
gen01.cpp:8:18: note: candidate template ignored: could not match 'std::vector<T>' against 'int'
    8 |     auto first = []<typename T>(const std::vector<T>& v) { return v.front(); };
      |                  ^
1 error generated.
```

**왜 그런가**

- ★★ **제네릭 람다는 호출 연산자가 템플릿**이다 — 부른 타입마다 한 벌(31편의 「인스턴스는 `T` 가 다를 때만」).
- ★★ **템플릿 람다는 매개변수의 모양으로 받는 것을 제한**한다 — `int` 에서는 `vector<T>` 추론이 실패한다.

### 6. ★ **`same type 0` · `1` · `4` · `8` · `16` · `16` · `fp() 1`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic type01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
same type a b     = 0
sizeof []         = 1
sizeof [x]        = 4
sizeof [&x]       = 8
sizeof [x, d]     = 16
sizeof [&x, &d]   = 16
fp()              = 1
===== clang++ -std=c++20 -Wall -Wextra -pedantic type01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
same type a b     = 0
sizeof []         = 1
sizeof [x]        = 4
sizeof [&x]       = 8
sizeof [x, d]     = 16
sizeof [&x, &d]   = 16
fp()              = 1
```

**왜 그런가**

- ★★ **람다 식마다 고유한 클래스** — 글자가 같아도 다른 타입.
- ★★ **캡처가 멤버**라 크기가 캡처를 따라간다 — 크기 값 자체는 이 ABI 의 관찰이다(10번).
- ★ **캡처 없는 람다만 함수 포인터로 바뀐다.**

### 7. ★★★ **`[=]` 는 「다 복사」로 읽히는데 `this` 만은 포인터로 잡혀 객체를 복사하지 않는다 — 1번의 `[this]` 행(「돌려준 뒤」 `use-after-return` · 「스코프 밖」 `use-after-scope`)과 같은 사고가 겉보기 값 캡처 안에 숨는다**

- ★★ 고치는 법은 두 컴파일러가 적어 준다 — **`[=, this]`**(참조임을 드러낸다) 또는 **`[=, *this]`**(객체를 복사한다).

### 8. ★★★ **`unique_ptr` 은 복사 생성자가 삭제됐다 → 그것을 멤버로 든 클로저도 복사 생성자가 암묵적으로 삭제된다 → `std::function` 은 담은 것을 복사할 수 있어야 한다(자기 자신이 복사 가능하므로) → 정적 단언 실패**

- ★★ clang 이 이 사슬을 전부 적었다 — `copy constructor … is implicitly deleted because field '' has a deleted copy constructor` · `'unique_ptr' has been explicitly marked deleted here`.
- ★ `std::move_only_function` 은 **복사를 요구하지 않는** 함수 래퍼다(C++23).

### 9. ★★ **말할 수 없다 — 그 칸이 바로 「돌려준 뒤」 참조 캡처 칸이다**(경고 0 · `uar=0` 침묵인데 UB)

- ★★ 1번 격자에서 **g++ 의 `[&x]`·`[&]`·`[this]` 반환 칸**이 그렇다 — 경고 0 이고, `uar=0` 이면 리포트도 없다. **침묵은 안전의 증거가 아니다**(30편 (1)의 탐침 7 과 같은 결론).

### 10. ★★ **말할 수 없다 — 표준은 참조 캡처를 어떻게 저장하는지 정하지 않는다.** 8 은 이 판(x86-64 · 두 컴파일러)의 관찰이다

- ★ 언어가 보장하는 것은 「**참조로 캡처된 대상을 가리킨다**」 는 뜻뿐이다.

### 11. 다른 주제와 잇기

- ★★ **C++ 의 `[&i]` 는 죽은 루프 변수를 읽는다 — 두 컴파일러 다 `stack-use-after-scope`**(`[i]` 판은 `0 1 2`). C# 은 변수를 **힙의 클래스로 옮겨** 살려 두므로 `3 3 3` 이다([C# 28번](../../../csharp/syntax/28-lambdas-and-closure-capture/)).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic loop01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
0 1 2 
===== clang++ -std=c++20 -Wall -Wextra -pedantic loop01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
0 1 2 
===== g++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DBYREF loop01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: stack-use-after-scope loop01.cpp:10 in operator()
===== clang++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DBYREF loop01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: stack-use-after-scope loop01.cpp:10:37 in main::$_0::operator()() const
```

- ★★ **컴파일 단계** — [Rust 34번](../../../rust/syntax/34-closures-fn-fnmut-fnonce-and-move/) (4): 반환·스레드에서 참조를 잡은 클로저는 **E0373** 로 거절되고 `move` 를 요구받는다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `cap01.cpp` + `cap-grid.sh` | 캡처 7 × 때 3 × 컴파일러 2 × (경고 · ASan 기본 · uar=1 · uar=0) | ★★★ **댕글링 12 / 40 · uar=0 이면 사라짐 6 / 12 · 경고 2 / 12 · 기본과 uar=1 차이 0** |
| `cap01.cpp` 리포트 | g++ `CAP=2 WHEN=2` | ★★ **`stack-use-after-return` · `'x' (line 53)`** |
| `thiscap.cpp` + `this-grid.sh` | 3 × 판 3 × 컴파일러 2 | ★★★ **컴파일러 사이 1 / 9(이름만) · 침묵 10 / 18** |
| `mut01.cpp` · `mo01.cpp` · `gen01.cpp` · `type01.cpp` · `loop01.cpp` | 두 컴파일러 | ★★ 위 정답 |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **`detect_stack_use_after_return` 의 기본값** · **경고가 잡는 칸** · **`sizeof` 의 값** · **기호 이름**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **값 캡처는 복사 · 참조 캡처는 참조 · `operator()` 는 기본 `const` · 클로저 타입은 고유 · move-only 멤버면 클로저도 move-only.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **`-O2` 의 캡처 격자** · **람다의 인라인**(역어셈블로 확인하지 않아 주장하지 않는다) · 구조적 바인딩 캡처.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 격자** — 특히 **ASan 옵션의 기본값**과 **경고 칸**.
