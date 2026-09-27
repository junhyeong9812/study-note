# cpp/syntax/37 — SFINAE 와 `enable_if` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 진단의 줄 수(격자의 「N줄」)** 다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · 골라진 오버로드의 출력 · 첫 error 의 행 · O/X · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **판 1\~4 는 같다 — `std::string` 은 `0`, `int`·`Plain` 은 대안 없으면 37행(호출 줄) 에러 · 대안 있으면 `-1`** · ★★★ **판 0 은 `int`·`Plain` 이 대안이 있어도 17행(몸통) 에러**

**출력**

```bash
# sf-grid.sh
# sf-grid.sh — 판 다섯 × 인자 셋 × 대안 오버로드 유무 × 컴파일러 둘.
# 칸: 통과면 「출력」, 에러면 「에러 N줄 · 첫 error 행 · 호출 줄인가 O/X」
forms=('0 제약 없음' '1 enable_if_t 반환 타입' '2 enable_if_t 기본 인자' '3 void_t 기본 인자' '4 requires(C++20)')
args=(std::string int Plain)
call=$(grep -n -F 'count_of(x)' sf01.cpp | head -n 1 | cut -d: -f1)
cell() {
  local out rc total first line same
  out=$($1 -std=c++20 -Wall -Wextra -pedantic -DFORM="$2" -DARG="$3" $4 sf01.cpp -o ex 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then printf '출력 %s' "$(./ex)"; return; fi
  total=$(printf '%s\n' "$out" | wc -l)
  first=$(printf '%s\n' "$out" | grep -m 1 ': error: ' | sed -E 's#^([^:]*/)?([^/:]+):([0-9]+):.*#\2:\3#')
  line="${first##*:}"
  if [ "$first" = "sf01.cpp:$call" ]; then same=O; else same=X; fi
  printf '에러 %s줄 · %s행 · %s' "$total" "$line" "$same"
}
printf '%s\t%s\t%s\t%s\t%s\n' "판" "인자" "대안" "g++" "clang++" > t.tsv
for fl in "${forms[@]}"; do
  n="${fl%% *}"
  for a in "${args[@]}"; do
    for fb in 없음 있음; do
      if [ "$fb" = 있음 ]; then d=-DFALLBACK; else d=; fi
      printf '%s\t%s\t%s\t%s\t%s\n' "$fl" "$a" "$fb" "$(cell g++ "$n" "$a" "$d")" "$(cell clang++ "$n" "$a" "$d")" >> t.tsv
    done
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 5' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
cells=$(( ($(wc -l < t.tsv) - 1) * 2 ))
errs=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=4;i<=5;i++) if ($i ~ /^에러/) n++ } END { print n+0 }')
errO=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=4;i<=5;i++) if ($i ~ /^에러.* O$/) n++ } END { print n+0 }')
# 컴파일러 사이 — 통과/에러 여부와 출력만 견준다(줄 수·행은 뺀다)
ccs=$(tail -n +2 t.tsv | awk -F'\t' '{ a=$4; b=$5; sub(/ .*/, "", a); sub(/ .*/, "", b); if (a=="출력") a=$4; if (b=="출력") b=$5; if (a!=b) n++ } END { print n+0 }')
rows=$(( $(wc -l < t.tsv) - 1 ))
echo "에러 칸 $errs / $cells · 그중 첫 error 가 호출 줄 $errO / $errs · 컴파일러 사이 갈린 행 $ccs / $rows"
rm -f ex t.tsv
```

```text
===== bash sf-grid.sh (exit=0) =====
판	인자	대안	g++	clang++
0 제약 없음	std::string	없음	출력 0	출력 0
0 제약 없음	std::string	있음	출력 0	출력 0
0 제약 없음	int	없음	에러 5줄 · 17행 · X	에러 7줄 · 17행 · X
0 제약 없음	int	있음	에러 5줄 · 17행 · X	에러 7줄 · 17행 · X
0 제약 없음	Plain	없음	에러 5줄 · 17행 · X	에러 7줄 · 17행 · X
0 제약 없음	Plain	있음	에러 5줄 · 17행 · X	에러 7줄 · 17행 · X
1 enable_if_t 반환 타입	std::string	없음	출력 0	출력 0
1 enable_if_t 반환 타입	std::string	있음	출력 0	출력 0
1 enable_if_t 반환 타입	int	없음	에러 17줄 · 37행 · O	에러 7줄 · 37행 · O
1 enable_if_t 반환 타입	int	있음	출력 -1	출력 -1
1 enable_if_t 반환 타입	Plain	없음	에러 17줄 · 37행 · O	에러 7줄 · 37행 · O
1 enable_if_t 반환 타입	Plain	있음	출력 -1	출력 -1
2 enable_if_t 기본 인자	std::string	없음	출력 0	출력 0
2 enable_if_t 기본 인자	std::string	있음	출력 0	출력 0
2 enable_if_t 기본 인자	int	없음	에러 11줄 · 37행 · O	에러 7줄 · 37행 · O
2 enable_if_t 기본 인자	int	있음	출력 -1	출력 -1
2 enable_if_t 기본 인자	Plain	없음	에러 11줄 · 37행 · O	에러 7줄 · 37행 · O
2 enable_if_t 기본 인자	Plain	있음	출력 -1	출력 -1
3 void_t 기본 인자	std::string	없음	출력 0	출력 0
3 void_t 기본 인자	std::string	있음	출력 0	출력 0
3 void_t 기본 인자	int	없음	에러 11줄 · 37행 · O	에러 9줄 · 37행 · O
3 void_t 기본 인자	int	있음	출력 -1	출력 -1
3 void_t 기본 인자	Plain	없음	에러 11줄 · 37행 · O	에러 9줄 · 37행 · O
3 void_t 기본 인자	Plain	있음	출력 -1	출력 -1
4 requires(C++20)	std::string	없음	출력 0	출력 0
4 requires(C++20)	std::string	있음	출력 0	출력 0
4 requires(C++20)	int	없음	에러 17줄 · 37행 · O	에러 10줄 · 37행 · O
4 requires(C++20)	int	있음	출력 -1	출력 -1
4 requires(C++20)	Plain	없음	에러 17줄 · 37행 · O	에러 10줄 · 37행 · O
4 requires(C++20)	Plain	있음	출력 -1	출력 -1
에러 칸 24 / 60 · 그중 첫 error 가 호출 줄 16 / 24 · 컴파일러 사이 갈린 행 0 / 30
```

**왜 그런가**

- ★★★ **판 1\~4 는 제약이 선언(반환 타입 · 템플릿 매개변수 · `requires`)에 있다** — 치환이 실패하면 후보에서 빠져, 대안이 없으면 「맞는 함수가 없다」가 **호출 줄**에서, 대안이 있으면 `count_of(...)` 가 골라진다.
- ★★★ **판 0 은 제약이 없어** 템플릿이 후보로 남고 이긴 뒤 **몸통에서** 깨진다(7번).
- ★★ **에러 칸 24 중 호출 줄이 16, 나머지 8 이 전부 판 0** · **컴파일러 사이 0 / 30**. 줄 수는 판마다 다르다(10번).

### 2. ★★★ **기본은 `-1` · `-DDEDUCED` 는 하드 에러(6행 — 몸통의 `t.size()`)**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic imm01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
-1
===== clang++ -std=c++20 -Wall -Wextra -pedantic imm01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
-1
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DDEDUCED imm01.cpp -o ex (cc exit=1) =====
imm01.cpp: In instantiation of ‘auto count_of(const T&) [with T = int]’:
imm01.cpp:12:59:   required from here
imm01.cpp:6:57: error: request for member ‘size’ in ‘t’, which is of non-class type ‘const int’
    6 | template <class T> auto count_of(const T& t) { return t.size(); }
      |                                                       ~~^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DDEDUCED imm01.cpp -o ex (cc exit=1) =====
imm01.cpp:6:56: error: member reference base type 'const int' is not a structure or union
    6 | template <class T> auto count_of(const T& t) { return t.size(); }
      |                                                       ~^~~~~
imm01.cpp:12:51: note: in instantiation of function template specialization 'count_of<int>' requested here
   12 | int main() { std::printf("%d\n", static_cast<int>(count_of(42))); }
      |                                                   ^
1 error generated.
```

**왜 그런가**

- ★★★ **`-> decltype(t.size())` 는 반환 타입이 선언에 있어** 실패가 즉시 문맥 안 — 조용히 빠진다.
- ★★★ **`auto` 는 반환 타입을 알려고 몸통을 인스턴스화**해야 하고, 몸통 안의 실패는 하드 에러다.

### 3. ★★★ **기본은 `fallback` · `-DNESTED` 는 하드 에러(6행 — `Inner` 의 몸통)**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic imm02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
fallback
===== clang++ -std=c++20 -Wall -Wextra -pedantic imm02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
fallback
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DNESTED imm02.cpp -o ex (cc exit=1) =====
imm02.cpp: In instantiation of ‘struct Inner<int>’:
imm02.cpp:10:20:   required by substitution of ‘template<class T, class> const char* kind(T) [with T = int; <template-parameter-1-2> = <missing>]’
imm02.cpp:16:38:   required from here
imm02.cpp:6:11: error: ‘int’ is not a class, struct, or union type
    6 |     using type = typename T::value_type;
      |           ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DNESTED imm02.cpp -o ex (cc exit=1) =====
imm02.cpp:6:27: error: type 'int' cannot be used prior to '::' because it has no members
    6 |     using type = typename T::value_type;
      |                           ^
imm02.cpp:10:37: note: in instantiation of template class 'Inner<int>' requested here
   10 | template <class T, class = typename Inner<T>::type> const char* kind(T) { return "template"; }
      |                                     ^
imm02.cpp:10:65: note: in instantiation of default argument for 'kind<int>' required here
   10 | template <class T, class = typename Inner<T>::type> const char* kind(T) { return "template"; }
      |                                                                 ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
imm02.cpp:16:34: note: while substituting deduced template arguments into function template 'kind' [with T = int, $1 = (no value)]
   16 | int main() { std::printf("%s\n", kind(42)); }
      |                                  ^
1 error generated.
```

**왜 그런가**

- ★★★ **`typename T::value_type` 은 템플릿 매개변수 타입 그 자체** — 즉시 문맥이라 SFINAE.
- ★★★ **`typename Inner<T>::type` 은 `Inner<int>` 를 인스턴스화하는 부수 효과 안**에서 실패 — cppreference 의 「**errors in those side-effects are treated as hard errors**」.

### 4. ★★★ **기본은 에러 — 첫 에러는 재선언(g++ `redefinition of ‘template<class T, class> const char* kind(T)’` · clang `template parameter redefines default argument`)** · **`-DNTTP` 는 통과하고 `integral floating`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic redecl.cpp -o ex (cc exit=1) =====
redecl.cpp:10:87: error: redefinition of ‘template<class T, class> const char* kind(T)’
   10 | template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
      |                                                                                       ^~~~
redecl.cpp:9:81: note: ‘template<class T, class> const char* kind(T)’ previously declared here
    9 | template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
      |                                                                                 ^~~~
redecl.cpp: In function ‘int main()’:
redecl.cpp:13:50: error: no matching function for call to ‘kind(double)’
   13 | int main() { std::printf("%s %s\n", kind(1), kind(1.5)); }
      |                                              ~~~~^~~~~
redecl.cpp:9:81: note: candidate: ‘template<class T, class> const char* kind(T)’
    9 | template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
      |                                                                                 ^~~~
redecl.cpp:9:81: note:   template argument deduction/substitution failed:
In file included from redecl.cpp:3:
/usr/include/c++/13/type_traits: In substitution of ‘template<bool _Cond, class _Tp> using std::enable_if_t = typename std::enable_if::type [with bool _Cond = false; _Tp = void]’:
redecl.cpp:9:20:   required from here
/usr/include/c++/13/type_traits:2610:11: error: no type named ‘type’ in ‘struct std::enable_if<false, void>’
 2610 |     using enable_if_t = typename enable_if<_Cond, _Tp>::type;
      |           ^~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic redecl.cpp -o ex (cc exit=1) =====
redecl.cpp:10:28: error: template parameter redefines default argument
   10 | template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
      |                            ^
redecl.cpp:9:28: note: previous default template argument defined here
    9 | template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
      |                            ^
redecl.cpp:10:87: error: redefinition of 'kind'
   10 | template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
      |                                                                                       ^
redecl.cpp:9:81: note: previous definition is here
    9 | template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
      |                                                                                 ^
redecl.cpp:13:37: error: no matching function for call to 'kind'
   13 | int main() { std::printf("%s %s\n", kind(1), kind(1.5)); }
      |                                     ^~~~
redecl.cpp:10:87: note: candidate template ignored: requirement 'std::is_floating_point_v<int>' was not satisfied [with T = int]
   10 | template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
      |                                                                                       ^
redecl.cpp:13:46: error: no matching function for call to 'kind'
   13 | int main() { std::printf("%s %s\n", kind(1), kind(1.5)); }
      |                                              ^~~~
redecl.cpp:10:87: note: candidate template ignored: substitution failure [with T = double, $1 = std::enable_if_t<std::is_floating_point_v<double>>]
   10 | template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
      |                                                                                       ^
4 errors generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DNTTP redecl.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
integral floating
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DNTTP redecl.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
integral floating
```

**왜 그런가**

- ★★★ **기본 템플릿 인자는 서명에 안 든다** — 두 선언이 모두 `template<class T, class> const char* kind(T)` 로 같다(8번). 뒤따르는 `no matching function` 은 **두 번째 정의가 버려진 연쇄**다.

### 5. ★★ **`ifc01` 은 `3 8`** · **`ifc02` 는 두 컴파일러 다 에러(`no_such_function`)**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ifc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
3 8
===== clang++ -std=c++20 -Wall -Wextra -pedantic ifc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
3 8
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ifc02.cpp -o ex (cc exit=1) =====
ifc02.cpp: In function ‘int f()’:
ifc02.cpp:4:16: error: ‘no_such_function’ was not declared in this scope
    4 |         return no_such_function();
      |                ^~~~~~~~~~~~~~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic ifc02.cpp -o ex (cc exit=1) =====
ifc02.cpp:4:16: error: use of undeclared identifier 'no_such_function'
    4 |         return no_such_function();
      |                ^
1 error generated.
```

**왜 그런가**

- ★★★ **템플릿 안의 `if constexpr` 는 인스턴스화할 때 버린 가지를 인스턴스화하지 않는다** — `double` 에 `t.size()` 가 있어도 괜찮다.
- ★★★ **비템플릿 함수에는 인스턴스화가 없다** — 버린 가지도 **보통 코드처럼 검사**되고, 선언 없는 이름은 에러다.

### 6. ★ **기본은 통과하고 `1 0` · `-DSTD` 는 `-std=c++23` 에서도 에러 — `std::is_detected_v` 가 없다**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic detect01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic detect01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 0
```

```text
===== g++ -std=c++23 -Wall -Wextra -pedantic -DSTD detect01.cpp -o ex (cc exit=1) =====
detect01.cpp:10:12: error: ‘is_detected_v’ has not been declared in ‘std’
   10 | using std::is_detected_v;
      |            ^~~~~~~~~~~~~
detect01.cpp: In function ‘int main()’:
detect01.cpp:15:37: error: ‘is_detected_v’ was not declared in this scope; did you mean ‘std::experimental::fundamentals_v2::is_detected_v<_Op, _Args ...>’?
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                     ^~~~~~~~~~~~~
      |                                     std::experimental::fundamentals_v2::is_detected_v<_Op, _Args ...>
In file included from detect01.cpp:3:
/usr/include/c++/13/experimental/type_traits:284:18: note: ‘std::experimental::fundamentals_v2::is_detected_v<_Op, _Args ...>’ declared here
  284 |   constexpr bool is_detected_v = is_detected<_Op, _Args...>::value;
      |                  ^~~~~~~~~~~~~
detect01.cpp:15:60: error: missing template arguments before ‘,’ token
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                                            ^
detect01.cpp:15:73: error: expected primary-expression before ‘>’ token
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                                                         ^
detect01.cpp:15:74: error: expected primary-expression before ‘,’ token
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                                                          ^
detect01.cpp:15:99: error: missing template arguments before ‘,’ token
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                                                                                   ^
detect01.cpp:15:101: error: expected primary-expression before ‘int’
   15 | int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
      |                                                                                                     ^~~
```

```text
===== clang++ -std=c++23 -Wall -Wextra -pedantic -DSTD detect01.cpp -o ex (cc exit=1) =====
detect01.cpp:10:7: error: no member named 'is_detected_v' in namespace 'std'; did you mean 'std::experimental::is_detected_v'?
   10 | using std::is_detected_v;
      |       ^~~~~~~~~~~~~~~~~~
      |       std::experimental::is_detected_v
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/experimental/type_traits:284:18: note: 'std::experimental::is_detected_v' declared here
  284 |   constexpr bool is_detected_v = is_detected<_Op, _Args...>::value;
      |                  ^
1 error generated.
```

**왜 그런가**

- ★★ **`is_detected` 는 library fundamentals TS v2** — `<experimental/type_traits>` 의 `std::experimental` 에만 있다. 표준에 들어오지 않았다.
- ★ 두 컴파일러가 같은 결론인 것은 **같은 libstdc++ 13 헤더**라서다.

### 7. ★★★ **판 0 의 템플릿은 선언에 제약이 없어 치환이 성공하고, `count_of(const T&)` 가 `count_of(...)` 보다 나은 후보라 골라진다 — 몸통의 실패는 오버로드 해석이 끝난 뒤라 하드 에러**

- ★★★ 줄임표 `...` 매개변수는 **최하위 순위**다. 치환이 성공한 템플릿이 있으면 반드시 진다.
- ★★ 진단에 **대안이 한 번도 안 나온다**(1번 요약의 판 0 전문) — 해석은 이미 끝났다.

### 8. ★★★ **`class = X` 는 「타입 매개변수 + 기본 인자」라 기본 인자가 서명에서 빠지고, `enable_if_t<…, int> = 0` 은 「비타입 매개변수의 타입 자체」에 조건이 들어가 서명이 달라진다**

- ★★★ 앞 꼴의 두 선언은 **`template<class T, class>`** 로 같아 재선언이 되고, 뒤 꼴은 **`template<class T, enable_if_t<is_integral_v<T>, int>>`** 대 **`… is_floating_point_v<T> …`** 로 **다른 템플릿**이다.

### 9. ★★ **`candidate:` 줄 — `template<class T> std::enable_if_t<has_size<T>::value, long unsigned int> count_of(const T&)`** 에 조건이 적혀 있다

- ★★ `enable_if<false, …>` 는 「**첫 인자가 거짓**」 이라는 뜻일 뿐 무엇이 거짓인지는 말하지 않는다. clang 은 `requirement 'has_size<int, void>::value' was not satisfied` 로 **번역해** 준다.
- ★ 그 블록의 두 번째 `error:` 는 **표준 헤더 안**이다 — 실수는 하나다.

### 10. ★★ **말할 수 없다 — 줄 수는 이 판의 관찰이다**(흔들리는 칸 · 규칙 24)

- ★★ 근거로 쓸 수 있는 칸은 **첫 error 의 행과 O/X** — 판 1\~4 가 전부 **37행 · O** 로 같다. 35편의 결론(「바뀌는 것은 길이가 아니라 자리」)과 같다.

### 11. 다른 주제와 잇기

- ★★ **부분 특수화**(33편) — `has_size<T, void_t<…>>` 가 **식이 될 때만 맞는 부분 특수화**라 `true_type` 이 되고, 안 되면 치환 실패로 기본(`false_type`)이 남는다.
- ★★ **컨셉의 제약은 서명의 일부**라 `template <std::integral T>` 와 `template <std::floating_point T>` 는 **다른 템플릿**이다(36편) — 재선언이 아니다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `sf01.cpp` + `sf-grid.sh` | 판 5 × 인자 3 × 대안 2 × 컴파일러 2 | ★★★ **에러 칸 24 / 60 · 호출 줄 16 / 24 · 컴파일러 사이 0 / 30** |
| `imm01.cpp` · `imm02.cpp` | 두 컴파일러 × 두 판 | ★★★ **`-1`·`fallback` / 하드 에러** |
| `redecl.cpp` | 두 컴파일러 × `NTTP` 유무 | ★★★ **재선언 / `integral floating`** |
| `ifc01.cpp` · `ifc02.cpp` | 두 컴파일러 | ★★ **`3 8` / 에러** |
| `detect01.cpp` | 두 컴파일러 × `STD` 유무(`c++20`·`c++23`) | ★ **`1 0` / 에러** |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **진단의 줄 수** · **`enable_if` 실패를 말하는 방식**(g++ `type` 없음 · clang 요구 불만족) · **연쇄 에러의 개수**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **즉시 문맥 안의 치환 실패는 후보 탈락 · 부수 효과 안은 하드 에러 · 기본 템플릿 인자는 서명이 아니다 · `if constexpr` 는 템플릿 안에서만 가지를 버린다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ 람다를 담은 선언(C++20 에서 즉시 문맥 밖) · 여러 부분 특수화가 동시에 맞는 모호 · `-std=c++14` 이하.
- ★ 「**부적용인 창**」 — ASan · 어셈블리.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **1번 격자** — 줄 수는 바뀌어도 된다. **O/X 칸과 출력 칸이 그대로인지**가 볼 것이다.
