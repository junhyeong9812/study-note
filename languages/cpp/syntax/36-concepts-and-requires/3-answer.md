# cpp/syntax/36 — 컨셉과 `requires`(C++20) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구 · 진단의 줄 수** 다.\
> 근거로 쓰는 것은 다음이다 — **`cc exit` · 통과/에러 · 골라진 오버로드의 출력 · 표의 1/0 · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **`int`·`long`·`bool`·`char` 는 통과, `double`·`Meters` 는 에러 — 네 표기 · 두 컴파일러 전부 같다(표기 사이 0 / 12 · 컴파일러 사이 0 / 24)**

**출력**

```bash
# form-grid.sh
# form-grid.sh — 표기 넷 × 인자 여섯 × 컴파일러 둘. 칸에는 컴파일이 통과했나만 찍는다
forms=('1 template<std::integral T>' '2 requires 절(앞)' '3 requires 절(뒤)' '4 std::integral auto')
args=(int long bool char double Meters)
printf '%s\t%s\t%s\t%s\n' "인자" "표기" "g++" "clang++" > t.tsv
for a in "${args[@]}"; do
  for fl in "${forms[@]}"; do
    n="${fl%% *}"; label="${fl#* }"
    row="$a	$n $label"
    for c in g++ clang++; do
      if $c -std=c++20 -Wall -Wextra -pedantic -DFORM="$n" -DARG="$a" form01.cpp -o ex 2>/dev/null; then r="통과"; else r="에러"; fi
      row="$row	$r"
    done
    printf '%s\n' "$row" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
# 표기 사이 — (인자, 컴파일러) 묶음마다 네 표기의 결과가 한 가지인가
forms_split=$(tail -n +2 t.tsv | awk -F'\t' '{ g[$1]=g[$1] " " $3; c[$1]=c[$1] " " $4 } END { n=0; for (k in g) { split(g[k], x, " "); split(c[k], y, " "); for (i=2;i<=4;i++) { if (x[i]!=x[1]) { n++; break } } for (i=2;i<=4;i++) { if (y[i]!=y[1]) { n++; break } } } print n }')
groups=$(( ${#args[@]} * 2 ))
cc_split=$(tail -n +2 t.tsv | awk -F'\t' '$3 != $4' | wc -l)
cells=$(( $(wc -l < t.tsv) - 1 ))
echo "표기 사이 갈린 묶음 $forms_split / $groups · 컴파일러 사이 갈린 칸 $cc_split / $cells"
rm -f ex t.tsv
```

```text
===== bash form-grid.sh (exit=0) =====
인자	표기	g++	clang++
int	1 template<std::integral T>	통과	통과
int	2 requires 절(앞)	통과	통과
int	3 requires 절(뒤)	통과	통과
int	4 std::integral auto	통과	통과
long	1 template<std::integral T>	통과	통과
long	2 requires 절(앞)	통과	통과
long	3 requires 절(뒤)	통과	통과
long	4 std::integral auto	통과	통과
bool	1 template<std::integral T>	통과	통과
bool	2 requires 절(앞)	통과	통과
bool	3 requires 절(뒤)	통과	통과
bool	4 std::integral auto	통과	통과
char	1 template<std::integral T>	통과	통과
char	2 requires 절(앞)	통과	통과
char	3 requires 절(뒤)	통과	통과
char	4 std::integral auto	통과	통과
double	1 template<std::integral T>	에러	에러
double	2 requires 절(앞)	에러	에러
double	3 requires 절(뒤)	에러	에러
double	4 std::integral auto	에러	에러
Meters	1 template<std::integral T>	에러	에러
Meters	2 requires 절(앞)	에러	에러
Meters	3 requires 절(뒤)	에러	에러
Meters	4 std::integral auto	에러	에러
표기 사이 갈린 묶음 0 / 12 · 컴파일러 사이 갈린 칸 0 / 24
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 -DARG=double form01.cpp -o ex (cc exit=1) =====
form01.cpp: In function ‘int main()’:
form01.cpp:20:25: error: no matching function for call to ‘take(double)’
   20 | int main() { return take(ARG{}) - 1; }
      |                     ~~~~^~~~~~~
form01.cpp:17:5: note: candidate: ‘template<class auto:1>  requires  integral<auto:1> int take(auto:1)’
   17 | int take(std::integral auto) { return 1; }
      |     ^~~~
form01.cpp:17:5: note:   template argument deduction/substitution failed:
form01.cpp:17:5: note: constraints not satisfied
In file included from form01.cpp:2:
/usr/include/c++/13/concepts: In substitution of ‘template<class auto:1>  requires  integral<auto:1> int take(auto:1) [with auto:1 = double]’:
form01.cpp:20:25:   required from here
/usr/include/c++/13/concepts:100:13:   required for the satisfaction of ‘integral<auto:1>’ [with auto:1 = double]
/usr/include/c++/13/concepts:100:24: note: the expression ‘is_integral_v<_Tp> [with _Tp = double]’ evaluated to ‘false’
  100 |     concept integral = is_integral_v<_Tp>;
      |                        ^~~~~~~~~~~~~~~~~~
```

**왜 그런가**

- ★★★ **네 표기는 전부 「템플릿 매개변수 `T` 하나에 `std::integral<T>` 제약」** 으로 같은 뜻이다. 제약이 거짓이면 그 템플릿은 **후보에서 빠지고** 남은 후보가 없어 에러가 난다.
- ★★ **`bool`·`char` 가 통과한 것이 이 격자의 함정**이다 — `std::integral` 은 이 둘을 담는다(6번).
- ★ 에러 칸 하나를 열어 본 위 블록이 **제약 때문에 막힌 것**(`is_integral_v<_Tp>` 가 `false`)을 보인다 — 격자의 「에러」가 다른 이유가 아니라는 확인이다(8번).

### 2. ★★★ **`FORM=1` 은 에러(`deduced conflicting types`) · `FORM=4` 는 통과하고 `4`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 form02.cpp -o ex (cc exit=1) =====
form02.cpp: In function ‘int main()’:
form02.cpp:11:39: error: no matching function for call to ‘take2(int, long int)’
   11 | int main() { std::printf("%d\n", take2(1, 2L)); }
      |                                  ~~~~~^~~~~~~
form02.cpp:6:32: note: candidate: ‘template<class T>  requires  integral<T> int take2(T, T)’
    6 | template <std::integral T> int take2(T, T) { return 1; }
      |                                ^~~~~
form02.cpp:6:32: note:   template argument deduction/substitution failed:
form02.cpp:11:39: note:   deduced conflicting types for parameter ‘T’ (‘int’ and ‘long int’)
   11 | int main() { std::printf("%d\n", take2(1, 2L)); }
      |                                  ~~~~~^~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 form02.cpp -o ex (cc exit=1) =====
form02.cpp:11:34: error: no matching function for call to 'take2'
   11 | int main() { std::printf("%d\n", take2(1, 2L)); }
      |                                  ^~~~~
form02.cpp:6:32: note: candidate template ignored: deduced conflicting types for parameter 'T' ('int' vs. 'long')
    6 | template <std::integral T> int take2(T, T) { return 1; }
      |                                ^
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 form02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
4
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 form02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
4
```

**왜 그런가**

- ★★★ **`template<std::integral T> int take2(T, T)` 는 두 인자에서 `T` 를 하나로** 추론해야 하는데 `int` 와 `long` 이 충돌한다 — **제약을 보기도 전에 추론에서** 막혔다.
- ★★★ **`std::integral auto` 는 `auto` 마다 템플릿 매개변수가 하나씩** 생긴다 — `take2<int, long>` 이 되어 둘 다 `integral` 이라 통과한다.
- ★ 그래서 1번의 「네 표기는 같다」는 **매개변수 하나일 때만**의 결론이다.

### 3. ★★★ **`int -> std::signed_integral` · `unsigned -> std::integral` · `bool -> std::integral` · `char -> std::signed_integral`** · `-funsigned-char` 면 **`char` 줄만 `std::integral` 로**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int      -> std::signed_integral
unsigned -> std::integral
bool     -> std::integral
char     -> std::signed_integral
===== clang++ -std=c++20 -Wall -Wextra -pedantic sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int      -> std::signed_integral
unsigned -> std::integral
bool     -> std::integral
char     -> std::signed_integral
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -funsigned-char sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int      -> std::signed_integral
unsigned -> std::integral
bool     -> std::integral
char     -> std::integral
===== clang++ -std=c++20 -Wall -Wextra -pedantic -funsigned-char sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
int      -> std::signed_integral
unsigned -> std::integral
bool     -> std::integral
char     -> std::integral
```

**왜 그런가**

- ★★★ **`int` 는 두 오버로드가 다 맞는데, `signed_integral` 이 `integral` 을 포함(subsume)해 더 제약된 쪽이 골라진다** — 표준의 `signed_integral` 정의가 **`integral<T>` 를 이름으로** 쓰고 거기에 `is_signed_v<T>` 를 `&&` 로 더했기 때문이다.
- ★★ **`bool` 은 부호 없는 타입**(`is_signed_v<bool>` 거짓)이라 `signed_integral` 후보가 빠진다.
- ★★★ **`char` 의 부호는 ABI 가 정한다** — x86-64 Linux 는 부호 있음, `-funsigned-char` 로 뒤집으면 **같은 소스가 다른 오버로드를 부른다.**

### 4. ★★★ **`MODE=1` 은 `pick(1)` 에서 모호 에러 · `MODE=2` 는 통과하고 `unsigned -> A` · `int -> B`**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DMODE=1 sub02.cpp -o ex (cc exit=1) =====
sub02.cpp: In function ‘int main()’:
sub02.cpp:25:41: error: call of overloaded ‘pick(int)’ is ambiguous
   25 |     std::printf("int      -> %s\n", pick(1));
      |                                     ~~~~^~~
sub02.cpp:9:13: note: candidate: ‘const char* pick(T) [with T = int]’
    9 | const char* pick(T) { return "A"; }
      |             ^~~~
sub02.cpp:12:13: note: candidate: ‘const char* pick(T) [with T = int]’
   12 | const char* pick(T) { return "B"; }
      |             ^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DMODE=1 sub02.cpp -o ex (cc exit=1) =====
sub02.cpp:25:37: error: call to 'pick' is ambiguous
   25 |     std::printf("int      -> %s\n", pick(1));
      |                                     ^~~~
sub02.cpp:9:13: note: candidate function [with T = int]
    9 | const char* pick(T) { return "A"; }
      |             ^
sub02.cpp:12:13: note: candidate function [with T = int]
   12 | const char* pick(T) { return "B"; }
      |             ^
sub02.cpp:8:14: note: similar constraint expressions not considered equivalent; constraint expressions cannot be considered equivalent unless they originate from the same concept
    8 |     requires std::is_integral_v<T>
      |              ^~~~~~~~~~~~~~~~~~~~~
sub02.cpp:11:14: note: similar constraint expression here
   11 |     requires std::is_integral_v<T> && std::is_signed_v<T>
      |              ^~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DMODE=2 sub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
unsigned -> A
int      -> B
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DMODE=2 sub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
unsigned -> A
int      -> B
```

**왜 그런가**

- ★★★ **`MODE=1` 의 두 `std::is_integral_v<T>` 는 「다른 원자 제약」** 이다(7번) — 컴파일러가 `B` 가 `A` 를 포함한다고 증명하지 못해 **둘 다 맞는 `int` 에서 모호**가 난다. `unsigned` 는 `B` 가 거짓이라 문제없다.
- ★★ **clang 은 이유를 적는다**(`similar constraint expressions not considered equivalent … unless they originate from the same concept`) · g++ 는 후보 둘만 적는다.
- ★★★ **`MODE=2` 는 공통 부분을 컨셉 `Int` 로 이름 붙여** 두 오버로드가 **같은 식(컨셉 정의 안의 한 식)** 을 가리키게 했다 → `B` 가 `A` 를 포함 → `int -> B`.

### 5. ★★ **`HasSize` — 문자열·벡터·`Bag` 1 · `HasValueType` — 문자열·벡터 1 · `SizeIsInt` — `Bag` 만 1 · ★ `BigA` 는 전부 1 · `BigB` 는 `double`·문자열·벡터만 1**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic req01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
T                  HasSize HasValueType SizeIsInt BigA BigB
char                     0            0         0    1    0
double                   0            0         0    1    1
std::string              1            1         0    1    1
std::vector<int>         1            1         0    1    1
Bag                      1            0         1    1    0
===== clang++ -std=c++20 -Wall -Wextra -pedantic req01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
T                  HasSize HasValueType SizeIsInt BigA BigB
char                     0            0         0    1    0
double                   0            0         0    1    1
std::string              1            1         0    1    1
std::vector<int>         1            1         0    1    1
Bag                      1            0         1    1    0
```

**왜 그런가**

- ★★★ **`BigA` 의 `sizeof(T) > 4;` 는 단순 요구** — 식이 **유효한가**만 보고 값은 안 본다(cppreference 「**unevaluated operand**」). `char` 에서도 그 식은 **유효**하다.
- ★★★ **`BigB` 의 `requires sizeof(T) > 4;` 는 중첩 요구** — **값이 참**이어야 한다. `char`·`Bag`(데이터 멤버가 없는 구조체)이 0.
- ★★ **`SizeIsInt` 는 반환 타입까지** 본다 — 표준 컨테이너의 `size()` 는 `size_t` 라 0, `Bag` 은 `int` 라 1.

### 6. ★★ **`bool` — `integral` 1 · `signed` 0 · `unsigned` 1 · `floating` 0 · `convertible` 1** · **`char` — 1 · 1 · 0 · 0 · 1** · **`int&` — `convertible` 만 1** · **`double` — `floating` 과 `convertible` 1** · **`enum class` — 전부 0**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic stdc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
T              integral signed_integral unsigned_integral floating_point convertible_to<T,int>
bool                  1               0                 1              0                    1
char                  1               1                 0              0                    1
signed char           1               1                 0              0                    1
unsigned char         1               0                 1              0                    1
char8_t               1               0                 1              0                    1
wchar_t               1               1                 0              0                    1
int                   1               1                 0              0                    1
const int             1               1                 0              0                    1
int&                  0               0                 0              0                    1
unsigned              1               0                 1              0                    1
double                0               0                 0              1                    1
enum class            0               0                 0              0                    0
===== clang++ -std=c++20 -Wall -Wextra -pedantic stdc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
T              integral signed_integral unsigned_integral floating_point convertible_to<T,int>
bool                  1               0                 1              0                    1
char                  1               1                 0              0                    1
signed char           1               1                 0              0                    1
unsigned char         1               0                 1              0                    1
char8_t               1               0                 1              0                    1
wchar_t               1               1                 0              0                    1
int                   1               1                 0              0                    1
const int             1               1                 0              0                    1
int&                  0               0                 0              0                    1
unsigned              1               0                 1              0                    1
double                0               0                 0              1                    1
enum class            0               0                 0              0                    0
```

**왜 그런가**

- ★★★ **`std::integral` 은 `bool`·모든 문자 타입을 담는다** — 「정수만」 제약에 `true`·`'a'` 가 들어온다.
- ★★★ **`bool` 은 `unsigned_integral` 도 1** — `is_unsigned_v<bool>` 이 참이다.
- ★★ **`int&` 는 정수 타입이 아니다** — 전달 참조에 `std::integral<T>` 를 걸면 lvalue 인자에서 막힌다. `remove_cvref_t` 로 벗긴다.
- ★★ **`double` 은 `int` 로 암묵 변환되니 `convertible_to<T,int>` 가 1** · **`enum class` 는 암묵 변환이 없어 0**.

### 7. ★★★ **원자 제약은 「소스의 같은 식」에서 나왔을 때만 같다 — 글자가 같아도 따로 적은 두 식은 다르다** · `MODE=2` 는 두 오버로드가 **같은 컨셉 정의 안의 한 식**을 가리킨다

- ★★★ cppreference — 「**Two atomic constraints are considered identical if they are formed from the same expression at the source level and their parameter mappings are equivalent.**」 · 「**Types and expressions are not analyzed for equivalence**」.
- ★★ 컴파일러가 **식의 뜻을 비교하지 않는다** — `N > 0` 이 `N >= 0` 을 포함하지 않는 것과 같은 이유다(같은 쪽의 예).
- ★ 그래서 표준의 `signed_integral` 은 `integral` 을 **이름으로** 재사용한다 — 3번이 모호하지 않은 이유다.

### 8. ★★ **말할 수 없다 — 0 은 「매개변수 하나 · 이 여섯 인자」의 결과다(2번이 반례)** · 0 이 진짜인지는 **에러 칸 하나를 열어 이유가 제약인지** 본다

- ★★ 2번이 **매개변수 둘에서 표기가 갈리는** 반례다. 격자는 **물은 칸만** 답한다.
- ★★ 「0 건」이 결론인 격자는 **그 0 이 다른 이유(매크로 실수·헤더 누락)로 생긴 것이 아닌지** 따로 물어야 한다(규칙 22) — 1번의 `double` 전문이 **`is_integral_v<_Tp>` 가 `false`** 라고 말한다.

### 9. ★★ **할 수 없다 — clang 도 libstdc++ 13 의 `<concepts>` 를 읽었다**

- ★★ 두 컴파일러가 같은 **헤더**를 읽었으니 같은 표가 나오는 것은 당연하다. **서로 다른 라이브러리 구현(libc++)** 은 이 머신에 없어 **못 쟀다.**
- ★ 표준 쪽 근거는 **형질의 정의**(`is_integral`·`is_unsigned`)다 — 실행이 아니라 명세다.

### 10. ★ **플랫폼(ABI)에 따라 다른 오버로드가 불린다** — x86-64 Linux 는 부호 있는 `char`, `-funsigned-char`(또는 그것이 기본인 플랫폼)에서는 `std::integral` 쪽

- ★ **소스는 한 글자도 안 바뀌는데** 3번의 `char` 줄이 바뀌었다. `char` 를 **정수로 다루려면** `signed char`/`unsigned char` 를 명시한다.

### 11. 다른 주제와 잇기

- ★★ **35편 (7)(8)** — 컨셉을 걸면 **첫 에러가 호출 줄**로 온다(컨셉이 걸린 칸 전부). 그런데 **줄 수는 g++ 8 → 17 → 29 로 늘었다.** 바뀌는 것은 **길이가 아니라 자리**다.
- ★★ **Rust 는 안 넘는다** — [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (9): **경계는 이름(`impl`)으로 걸린다.** C++ 컨셉은 **모양**으로 맞아 `Bag` 이 통과했다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `form01.cpp` + `form-grid.sh` | 표기 4 × 인자 6 × 컴파일러 2 | ★★★ **표기 사이 0 / 12 · 컴파일러 사이 0 / 24** |
| `form02.cpp` | `FORM=1`·`4` × 두 컴파일러 | ★★★ **에러 / `4`** |
| `sub01.cpp` | 두 컴파일러 × `-funsigned-char` 유무 | ★★★ **`char` 줄만 갈린다** |
| `sub02.cpp` | `MODE=1`·`2` × 두 컴파일러 | ★★★ **모호 / `A B`** |
| `req01.cpp` · `stdc01.cpp` | 두 컴파일러 | ★★ **표가 한 글자도 같다**(같은 라이브러리) |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **`char` 가 부호 있는 타입**(ABI) · **진단 문구**(clang 만 모호의 이유를 적는다) · **표준 컨셉의 정의는 libstdc++ 13 한 판**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **제약 불만족은 후보 탈락** · **subsumption 은 원자 제약의 동일성으로** · **단순 요구는 식의 유효성만, 중첩 요구는 값** · **`auto` 매개변수마다 템플릿 매개변수 하나.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — ★ **libc++ 의 표준 컨셉**(이 머신에 없다) · **다른 ABI 의 `char`**(플래그로만).
- **안 돌려 본 것** — `||` 제약의 subsumption · 클래스 템플릿 멤버의 뒤 `requires` 절.
- ★ 「**부적용인 창**」 — ASan · 어셈블리.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번의 두 전문** — 모호의 이유를 g++ 도 적게 되는지.
