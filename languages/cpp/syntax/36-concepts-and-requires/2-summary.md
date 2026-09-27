# cpp/syntax/36 — 컨셉과 `requires`(C++20) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Constraints and concepts](https://en.cppreference.com/w/cpp/language/constraints) · [cppreference — Requires expression](https://en.cppreference.com/w/cpp/language/requires)\
> ★ 이 배치에서 **위 두 cppreference 쪽을 열어 확인했다** — 「**Two atomic constraints are considered identical if they are formed from the same expression at the source level and their parameter mappings are equivalent.**」 · 「`P` 가 `Q` 를 subsume 한다 = 원자 제약의 동일성까지만 따져 `P` 가 `Q` 를 함의한다 — **Types and expressions are not analyzed for equivalence**」 · 「**A simple requirement asserts that expression is valid. expression is an unevaluated operand.**」 세 문장이다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★★ **clang 도 libstdc++ 13 을 쓴다** — 그래서 **`std::integral` 같은 표준 컨셉의 표에서 두 컴파일러가 같은 줄을 낸 것은 「두 라이브러리 구현이 일치한다」의 근거가 아니다** — 같은 헤더를 읽었을 뿐이다((4)).\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`form01.cpp`·`form02.cpp`·`sub01.cpp`·`sub02.cpp`·`req01.cpp`·`stdc01.cpp`·`form-grid.sh`).\
> ★ **진단에 소스 경로가 박히지 않게 상대 경로로 컴파일**했다. 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — 컨셉·`requires` 절·`requires` 식·축약 함수 템플릿(`std::integral auto` 매개변수)은 전부 **C++20부터**, 표준 컨셉은 **`<concepts>`(C++20)** 다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[35번](../35-instantiation-header-placement-and-reading-errors/)에서 온다 — 35편이 잰 것은 다시 재지 않는다.**\
> [35번](../35-instantiation-header-placement-and-reading-errors/) (7)(8) — **컨셉을 걸면 첫 에러가 호출 줄로 온다**(16칸 중 컨셉이 걸린 칸 전부) · **그런데 줄 수는 g++ `deep01` 8 → 직접 쓴 `Less` 17 → `std::totally_ordered` 29 로 오히려 늘었다** · **`totally_ordered` 는 `<` 가 아니라 `==` 를 탓했다** · 짧아진 것은 **`ranges::sort`** 쪽(78 → 34)뿐이다.\
> ★★ **그래서 이 편은 오류의 길이·자리를 다시 세지 않는다.** 여기서 새로 묻는 것은 셋이다 — **제약을 적는 네 가지 표기가 같은 것을 뜻하나** · **두 제약 중 어느 쪽이 「더 제약된」 것인가(subsumption)** · **`requires` 식과 표준 컨셉을 고를 때 무엇이 걸리나.**
> **경계** — 「인스턴스화 오류의 자리와 길이」는 [35번](../35-instantiation-header-placement-and-reading-errors/)이, 「컨셉 이전의 같은 의도(SFINAE)」는 [37번](../37-sfinae-and-enable-if/)이, 「오버로드 해석의 기본 순서」는 [01번](../01-function-overloading-and-overload-resolution/)이 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 진단의 **줄 수** | ★★★ **통과 / 에러(`cc exit`)** · **골라진 오버로드의 출력** · **표의 1/0** |
> | ★ `char` 가 부호 있는 타입인가 — **이 ABI(x86-64 Linux)의 선택**이다((3)) | ★★★ **격자의 「갈린 묶음 N / M」** 줄 · **모호 에러가 나는가** |

## 한눈에 — 쉽게 말하면

**컨셉은 「입장 조건」이 적힌 팻말이다.** 템플릿이 가게라면, 컨셉은 **문 앞에서 손님(타입)을 확인**한다.

- 팻말이 없으면 손님은 **일단 들어와 주방(템플릿 몸통)에서 사고를 친다** — 에러가 몸통을 가리킨다(35편 (5)).
- 팻말이 있으면 **문 앞에서 돌려보낸다** — 에러가 호출 줄에 난다(35편 (7)).
- **팻말을 붙이는 자리는 네 곳이다** — 간판(`template<std::integral T>`) · 문 위(`requires` 절 앞) · 문 옆(`requires` 절 뒤) · 손님 이름표(`std::integral auto`). **네 곳 다 같은 조건이다**((1)) — 단 이름표는 **손님마다 따로** 달린다((1)의 두 번째 블록).
- **팻말이 두 개면 더 까다로운 쪽이 이긴다**(subsumption) — **단 「같은 문장」을 가리킬 때만** 비교할 수 있다. 같은 말을 **두 번 따로 적으면** 컴파일러는 둘이 같은 말인지 모른다((2)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 입장 조건 팻말 | ★★ **컨셉 · 제약(constraint)** | (1) |
| 팻말 붙이는 네 자리 | ★★★ **네 표기 — 격자 `0 / 12`** | (1) |
| 더 까다로운 팻말이 이긴다 | ★★★ **subsumption — `signed_integral` 이 `integral` 을 이긴다** | (2) |
| 같은 말을 따로 두 번 적음 | ★★★ **`&&` 로 직접 쓴 형질 식 — 모호 에러** | (2) |
| 「이 손님이 이걸 할 수 있나」 | ★★ **`requires` 식** — 식이 **되나**만 본다 | (3) |
| 기성 팻말 | ★★ **표준 컨셉** — `bool`·`char` 도 `integral` | (4) |

```text
   template <std::integral T> int take(T);        호출 take(1.5)
                                                    │
                          ┌─────────────────────────┘
                          ▼
             T = double 추론 → 제약 검사 std::integral<double> = false
                          │
                          ▼
             후보에서 빠진다 → 남은 후보 0 → 에러는 「호출 줄」에서      (35편 (7))
             ★ 몸통은 인스턴스화되지 않는다
```

## 이 주제가 답하려는 질문

1. ★★★ **제약을 적는 네 표기는 같은 것을 뜻하나 — 어디서 갈리나**((1)).
2. ★★★ **두 오버로드가 다 맞을 때 어느 것이 골라지나 — 「같은 뜻」을 직접 쓰면 왜 모호해지나**((2)).
3. ★★ **`requires` 식은 무엇을 검사하나 — 식이 참인가, 식이 되는가**((3)).
4. ★★ **표준 컨셉을 고를 때 무엇이 걸리나 — `std::integral` 은 무엇을 포함하나**((4)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러의 통과·에러와 골라진 오버로드다

★★★ **이 편의 결론은 전부 「컴파일이 되나 · 무엇이 골라졌나」** 두 가지로 난다 — 격자는 **스크립트가 세고**((1)), 오버로드는 **출력이 말한다**((2)).\
★★ **오류의 길이와 자리는 35편이 이미 쟀다** — 그 창(진단 세기 격자)은 **이 편에서 다시 열지 않는다**(제5의 상태가 아니라 「앞 편 인용」이다).

```text
① 다섯 층 표            제약 규칙은 표준 · char 의 부호는 ABI · 진단은 컴파일러             (구현 세부사항 절)
② ★ 두 컴파일러          표기 격자 · 모호 에러 전문 · 골라진 오버로드                      (1)~(4)
③ ASan                   —                                                                부적용
④ 어셈블리·기호표        —                                                                부적용
⑤ 진단 세기 격자         —                                                                35편 인용
⑥ ★ 컴파일 시간 표       requires 식 · 표준 컨셉을 1/0 으로 찍는다                         (3)(4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **subsumption 규칙은 표준, `char` 의 부호는 ABI, 진단 문구는 컴파일러** | **쓴다** |
| ★★★ **② 두 컴파일러** | ★★★ **본체** — 네 표기 격자 **표기 사이 0 / 12 · 컴파일러 사이 0 / 24** · 모호 에러 두 전문 | **쓴다** |
| ③ ASan | ★ **부적용** — 결론이 전부 컴파일 단계에서 난다(18-B) | **안 쓴다** |
| ④ 어셈블리 → 기호표 | ★ **부적용** — 컨셉은 **후보를 거르는 장치**라 만들어진 코드에 흔적을 남길 자리가 없다. 잴 것이 없다(18-B) | **안 쓴다** |
| ⑤ 진단 세기 | ★★ **35편 (8)이 쟀다** — 다시 재지 않는다 | **인용** |
| ⑥ 컴파일 시간 표 | ★★ **컨셉은 `bool` 로 평가되는 식이다** — `printf("%d", std::integral<T>)` 로 **표를 찍었다**((3)(4)) | **쓴다** |

### (1) ★★★ 네 표기 — 같은 제약을 네 자리에

**언제 쓰나** — 템플릿에 제약을 걸 때마다. **어느 표기를 고를지**는 취향이 아니라 (1)의 두 번째 블록이 가르는 자리가 있다.

```cpp
/* form01.cpp */
// 같은 제약(std::integral)을 네 가지 표기로 — -DFORM=1..4 로 하나만 켜고, -DARG=<타입> 으로 인자를 고른다
#include <concepts>

struct Meters {
    int v;
};

#if FORM == 1
template <std::integral T> int take(T) { return 1; }
#elif FORM == 2
template <class T>
    requires std::integral<T>
int take(T) { return 1; }
#elif FORM == 3
template <class T> int take(T) requires std::integral<T> { return 1; }
#elif FORM == 4
int take(std::integral auto) { return 1; }
#endif

int main() { return take(ARG{}) - 1; }
```

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

- ★★★ **표기 사이 갈린 묶음 0 / 12 · 컴파일러 사이 갈린 칸 0 / 24** — 인자 하나에 대해 **네 표기가 같은 답**을 냈다. `int`·`long`·**`bool`**·**`char`** 가 통과하고 `double`·`Meters` 가 막힌다.
- ★★ **이 0 이 진짜인가**(규칙 22) — 격자의 「에러」 칸이 **제약 때문에 막힌 것**인지 한 칸을 열어 본다. 축약 표기(`FORM=4`)에 `double` —

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

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 -DARG=double form01.cpp -o ex (cc exit=1) =====
form01.cpp:20:21: error: no matching function for call to 'take'
   20 | int main() { return take(ARG{}) - 1; }
      |                     ^~~~
form01.cpp:17:5: note: candidate template ignored: constraints not satisfied [with auto:1 = double]
   17 | int take(std::integral auto) { return 1; }
      |     ^
form01.cpp:17:10: note: because 'double' does not satisfy 'integral'
   17 | int take(std::integral auto) { return 1; }
      |          ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:100:24: note: because 'is_integral_v<double>' evaluated to false
  100 |     concept integral = is_integral_v<_Tp>;
      |                        ^
1 error generated.
```

- ★★★ **두 컴파일러 다 20행 — 호출 줄**이고 이유는 **`is_integral_v<_Tp>` 가 거짓**(g++ `evaluated to ‘false’` · clang `does not satisfy 'integral'`)이다. 격자의 「에러」는 **다른 이유로 난 에러가 아니다.**
- ★ **축약 표기에서도 컴파일러는 템플릿을 적는다** — g++ `template<class auto:1>  requires  integral<auto:1> int take(auto:1)`. **`std::integral auto` 는 이름 없는 템플릿 매개변수 하나**다.

**★★★ 그런데 매개변수가 둘이면 갈린다** — 이름 붙인 `T` 하나는 **두 인자가 같은 타입**이어야 하고, `auto` 둘은 **각자 따로** 추론된다.

```cpp
/* form02.cpp */
// 매개변수가 둘일 때 — 이름 붙인 T 하나(-DFORM=1) 대 auto 둘(-DFORM=4)
#include <concepts>
#include <cstdio>

#if FORM == 1
template <std::integral T> int take2(T, T) { return 1; }
#elif FORM == 4
int take2(std::integral auto, std::integral auto) { return 4; }
#endif

int main() { std::printf("%d\n", take2(1, 2L)); }
```

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

- ★★★ **`template<std::integral T> int take2(T, T)` 에 `(1, 2L)` 은 에러** — g++ `deduced conflicting types for parameter ‘T’ (‘int’ and ‘long int’)` · clang `deduced conflicting types for parameter 'T' ('int' vs. 'long')`. **제약 이전에 추론에서** 막혔다(31편의 「추론 충돌」).
- ★★★ **`int take2(std::integral auto, std::integral auto)` 는 통과하고 `4`** — `auto` 하나마다 **템플릿 매개변수가 하나씩** 생긴다.
- ★ 그래서 **「네 표기는 같다」는 「매개변수 하나일 때」의 결론**이다. 둘 이상이면 **축약 표기는 서로 다른 타입을 허락하는 표기**다.

### (2) ★★★ subsumption — 더 제약된 쪽이 골라진다

**언제 쓰나** — 「정수면 A, **부호 있는** 정수면 더 특수한 B」처럼 **겹치는 제약**으로 오버로드를 나눌 때.

```cpp
/* sub01.cpp */
// 두 오버로드 — std::integral 대 std::signed_integral. 인자 넷을 넘겨 어느 쪽이 골라지나 찍는다
#include <concepts>
#include <cstdio>

template <std::integral T> const char* pick(T) { return "std::integral"; }
template <std::signed_integral T> const char* pick(T) { return "std::signed_integral"; }

int main() {
    std::printf("int      -> %s\n", pick(1));
    std::printf("unsigned -> %s\n", pick(1u));
    std::printf("bool     -> %s\n", pick(true));
    std::printf("char     -> %s\n", pick('a'));
}
```

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

- ★★★ **`int` 는 두 오버로드가 다 맞는데 모호하지 않고 `std::signed_integral` 이 골라진다** — `signed_integral` 이 **`integral<T> && is_signed_v<T>` 로 정의**되어 있어 `integral` 을 **포함(subsume)** 하기 때문이다. 두 컴파일러 같다.
- ★★ **`unsigned`·`bool` 은 `integral` 쪽** — `signed_integral` 이 거짓이라 후보가 하나뿐이다.
- ★★★ **`char` 는 `signed_integral`** — 이 판에서 `char` 가 **부호 있는 타입**이라서다. **이것은 ABI 의 선택**이다 — 같은 소스를 **`-funsigned-char`** 로 던지면 —

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

- ★★★ **`char -> std::integral` 로 바뀐다** — **소스는 한 글자도 안 바뀌었다.** `char` 를 `signed_integral` 로 오버로드 가르는 코드는 **플랫폼마다 다른 함수를 부른다**(ARM Linux 의 기본은 부호 없는 `char` 다 — 이 머신에서는 **플래그로만** 확인했다).

**★★★ 같은 뜻을 형질 식 `&&` 로 직접 쓰면** — 컨셉 이름 없이 `std::is_integral_v<T>` 를 두 오버로드에 **각각** 적는다.

```cpp
/* sub02.cpp */
// 같은 뜻을 컨셉 없이 형질(trait) 식으로 — -DMODE=1 은 두 오버로드 다 식을 직접 쓴다,
// -DMODE=2 는 앞쪽 식을 컨셉 Int 로 한 번 이름 붙이고 두 오버로드가 그 이름을 쓴다
#include <cstdio>
#include <type_traits>

#if MODE == 1
template <class T>
    requires std::is_integral_v<T>
const char* pick(T) { return "A"; }
template <class T>
    requires std::is_integral_v<T> && std::is_signed_v<T>
const char* pick(T) { return "B"; }
#elif MODE == 2
template <class T> concept Int = std::is_integral_v<T>;
template <class T>
    requires Int<T>
const char* pick(T) { return "A"; }
template <class T>
    requires Int<T> && std::is_signed_v<T>
const char* pick(T) { return "B"; }
#endif

int main() {
    std::printf("unsigned -> %s\n", pick(1u));
    std::printf("int      -> %s\n", pick(1));
}
```

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

- ★★★ **`pick(1)` 이 모호(ambiguous)** — `B` 의 제약 `is_integral_v<T> && is_signed_v<T>` 는 **뜻으로는** `A` 의 `is_integral_v<T>` 를 포함하는데 **컴파일러는 그렇게 보지 않았다.**
- ★★★ **이유 — 두 `std::is_integral_v<T>` 는 「다른 원자 제약」이다.** cppreference 의 규칙 그대로 — 원자 제약은 「**소스에서 같은 식**」(같은 자리에 적힌 같은 식)일 때만 동일하다. 8행과 11행에 **따로 적은** 두 식은 글자가 같아도 **다른 식**이다.
- ★★ **clang 은 그 이유를 말한다** — `similar constraint expressions not considered equivalent; constraint expressions cannot be considered equivalent unless they originate from the same concept`. **g++ 는 후보 둘만 적고 이유는 적지 않는다.**
- ★ **`pick(1u)` 줄은 에러가 아니다** — `B` 가 거짓이라 후보가 `A` 하나다. **모호는 「둘 다 맞을 때」만** 난다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DMODE=2 sub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
unsigned -> A
int      -> B
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DMODE=2 sub02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
unsigned -> A
int      -> B
```

- ★★★ **`MODE=2` — 식을 컨셉 `Int` 로 한 번 이름 붙이면 `int -> B`** 로 풀린다. 두 오버로드의 `Int<T>` 는 **같은 컨셉 정의 안의 같은 식**(`std::is_integral_v<T>`, 14행)으로 펼쳐져 **동일한 원자 제약**이 된다.
- ★★ **교훈 — 겹치는 제약으로 오버로드를 가르려면 공통 부분을 컨셉으로 이름 붙여라.** 표준의 `signed_integral` 이 `integral` 을 **이름으로** 쓰는 것이 이 때문이다.

```text
   A: requires std::is_integral_v<T>                    원자 {is_integral_v<T> @ 8행}
   B: requires std::is_integral_v<T> && is_signed_v<T>  원자 {is_integral_v<T> @ 11행} ∧ {is_signed_v<T> @ 11행}
      → 8행의 원자와 11행의 원자는 「다른 식」 → B 가 A 를 포함한다고 증명 못 한다 → 모호

   A: requires Int<T>                                   Int 를 펼침 → 원자 {is_integral_v<T> @ 14행}
   B: requires Int<T> && is_signed_v<T>                 원자 {is_integral_v<T> @ 14행} ∧ {is_signed_v<T> @ 19행}
      → 같은 14행의 원자 → B 가 A 를 포함 → B 가 골라진다
```

### (3) ★★ `requires` 식 — 식이 「되나」를 본다

**언제 쓰나** — 표준 컨셉에 없는 요구(「`.size()` 가 있다」)를 직접 적을 때.

```cpp
/* req01.cpp */
// requires 식 — 단순 요구 · 타입 요구 · 복합 요구 · 중첩 요구를 타입 넷에 물어 1/0 으로 찍는다
#include <concepts>
#include <cstdio>
#include <string>
#include <vector>

template <class T> concept HasSize = requires(const T& t) { t.size(); };
template <class T> concept HasValueType = requires { typename T::value_type; };
template <class T> concept SizeIsInt = requires(const T& t) {
    { t.size() } -> std::same_as<int>;
};
template <class T> concept BigA = requires { sizeof(T) > 4; };
template <class T> concept BigB = requires { requires sizeof(T) > 4; };

struct Bag {
    int size() const { return 3; }
};

template <class T> void row(const char* name) {
    std::printf("%-18s %7d %12d %9d %4d %4d\n", name, HasSize<T>, HasValueType<T>, SizeIsInt<T>, BigA<T>, BigB<T>);
}

int main() {
    std::printf("%-18s %7s %12s %9s %4s %4s\n", "T", "HasSize", "HasValueType", "SizeIsInt", "BigA", "BigB");
    row<char>("char");
    row<double>("double");
    row<std::string>("std::string");
    row<std::vector<int>>("std::vector<int>");
    row<Bag>("Bag");
}
```

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

- ★★★ **`BigA` 는 다섯 타입 전부 1** — `requires { sizeof(T) > 4; }` 는 **단순 요구(simple requirement)** 라 **식 `sizeof(T) > 4` 가 「되나」만** 본다. `char` 에서 그 식은 **거짓이지만 문법적으로 된다** — 그래서 참이다. cppreference — 「**expression is an unevaluated operand**」.
- ★★★ **`BigB` 는 `requires { requires sizeof(T) > 4; }`** — 안쪽 `requires` 가 **중첩 요구(nested requirement)** 이고, **값이 참이어야** 한다. `char`·`Bag`(멤버 함수만 있는 빈 구조체)이 0 이다.
- ★★ **`HasSize` 는 모양만 본다** — 직접 만든 `Bag` 도 `.size()` 가 있으니 1 이다. ★ **Rust 는 반대다** — [Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (9)이 「**경계는 이름으로 걸린다 — 모양이 맞아도 `impl` 이 없으면 못 넘는다**」를 보였다. C++ 컨셉은 **모양(구조)으로** 맞는다.
- ★★ **`SizeIsInt` 는 복합 요구 `{ t.size() } -> std::same_as<int>`** — `std::string::size()` 는 `size_t` 라 **0**, `Bag::size()` 는 `int` 라 **1**. **반환 타입까지 물을 때만** 이 꼴을 쓴다.
- ★ **`HasValueType` 은 타입 요구** `typename T::value_type;` — `Bag` 은 0.

### (4) ★★ 표준 컨셉 고르기 — `std::integral` 이 무엇을 담나

**언제 쓰나** — 「정수만」·「실수만」을 받을 때. **흔한 사고는 `bool` 과 `char` 가 정수라는 것**이다.

```cpp
/* stdc01.cpp */
// 표준 컨셉 다섯을 타입 열둘에 물어 1/0 으로 찍는다
#include <concepts>
#include <cstdio>

enum class Color { red };

template <class T> void row(const char* name) {
    std::printf("%-14s %8d %15d %17d %14d %20d\n", name, std::integral<T>, std::signed_integral<T>,
                std::unsigned_integral<T>, std::floating_point<T>, std::convertible_to<T, int>);
}

int main() {
    std::printf("%-14s %8s %15s %17s %14s %20s\n", "T", "integral", "signed_integral", "unsigned_integral",
                "floating_point", "convertible_to<T,int>");
    row<bool>("bool");
    row<char>("char");
    row<signed char>("signed char");
    row<unsigned char>("unsigned char");
    row<char8_t>("char8_t");
    row<wchar_t>("wchar_t");
    row<int>("int");
    row<const int>("const int");
    row<int&>("int&");
    row<unsigned>("unsigned");
    row<double>("double");
    row<Color>("enum class");
}
```

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

- ★★★ **`bool`·`char`·`char8_t`·`wchar_t` 가 전부 `integral` 이 1** — 「정수만 받는다」고 `std::integral` 을 걸면 **`true` 도 `'a'` 도 들어온다.** (1)의 격자에서 `bool`·`char` 가 통과한 것과 같다.
- ★★★ **`bool` 은 `unsigned_integral` 도 1** — `std::is_unsigned_v<bool>` 이 참이라서다. **「부호 없는 정수만」이라는 제약도 `bool` 을 막지 못한다.**
- ★★ **`int&` 는 `integral` 이 0 · `const int` 는 1** — 참조 타입은 정수 타입이 아니다. 전달 참조 `T&&` 에 `std::integral<T>` 를 걸면 **lvalue 인자에서 `T = int&` 가 되어 막힌다**(31편의 전달 참조 추론) — `std::integral<std::remove_cvref_t<T>>` 로 벗겨야 한다.
- ★★ **`enum class` 는 전부 0 — `convertible_to<T,int>` 도 0** · `double` 은 `convertible_to<T,int>` 가 **1**(암묵 변환이 되니까). **`convertible_to<int>` 는 「정수」가 아니다.**
- ★ **두 컴파일러의 표가 한 글자도 같다** — 그러나 **clang 도 libstdc++ 13 의 `<concepts>` 를 읽었다.** 이 일치는 **표준 규칙의 확인**이 아니라 **같은 헤더를 두 번 읽은 것**이다. 표준의 근거는 cppreference 와 형질 정의다.

```text
   원하는 것                         고를 것                                          (4)의 표에서
   정수 — bool·char 는 빼고          std::integral<T> && !std::same_as<T, bool> …      ★ 표준에 이런 컨셉은 없다 — 직접 쓴다
   부호 있는 정수                    std::signed_integral                               char 는 ABI 따라 들고 난다
   부호 없는 정수                    std::unsigned_integral                             ★ bool 이 들어온다
   실수                              std::floating_point                                double 1
   「int 로 바뀌면 된다」             std::convertible_to<T, int>                         double 도 1 · enum class 0
```

## 문법 — 형태와 규칙

### 형태

```text
   template <std::integral T> int take(T);                        ① 타입 제약 — 템플릿 매개변수 자리
   template <class T> requires std::integral<T> int take(T);      ② requires 절 — 템플릿 머리 뒤
   template <class T> int take(T) requires std::integral<T>;      ③ requires 절 — 선언 끝(뒤)
   int take(std::integral auto);                                  ④ 축약 함수 템플릿 — auto 마다 매개변수 하나
   template <class T> concept HasSize = requires(const T& t) { t.size(); };        requires 식
   requires { requires sizeof(T) > 4; }                          중첩 요구 — 값이 참이어야
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(3)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **네 표기는 매개변수가 하나일 때 같은 결과를 냈다**(격자 0 / 12) — **축약 표기는 `auto` 마다 따로 추론**된다((1)).
- ★★★ **더 제약된 오버로드가 골라진다 — 「더 제약됨」은 원자 제약의 동일성으로만 판단**한다((2)).
- ★★★ **같은 식을 두 번 따로 적으면 다른 원자 제약이다** — 공통 부분은 **컨셉으로 이름 붙여라**((2)).
- ★★ **단순 요구는 식이 되나만, 중첩 요구는 값이 참인가를** 본다((3)).
- ★★ **`std::integral` 은 `bool`·문자 타입을 포함하고, `bool` 은 `unsigned_integral` 이기도 하다**((4)).
- ★ ③(뒤 `requires` 절)만 **클래스 템플릿의 비템플릿 멤버 함수**에 쓸 수 있다(`void f() requires std::integral<T>;`) — 이 편은 **던지지 않았다.**

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `template<std::integral T> int take2(T, T)` 에 `(1, 2L)` | `deduced conflicting types for parameter ‘T’` | `deduced conflicting types for parameter 'T'` | (1) |
| 형질 식을 두 오버로드에 따로 적고 둘 다 맞는 인자 | `call of overloaded ‘pick(int)’ is ambiguous` | `call to 'pick' is ambiguous` + `similar constraint expressions not considered equivalent` | (2) |
| `std::integral auto` 에 `double` | `the expression ‘is_integral_v<_Tp>’ … evaluated to ‘false’` | `because 'double' does not satisfy 'integral'` | (1) |

## 어디서 틀리나

### 1. ★★★ 「`std::integral auto` 는 `template<std::integral T>` 의 줄임말이다」

(1)의 두 번째 블록이 반증이다 — **매개변수가 둘이면 `(1, 2L)` 을 한쪽은 받고 한쪽은 거절**한다.

### 2. ★★★ 「뜻이 포함 관계면 컴파일러가 더 구체적인 쪽을 고른다」

(2)가 반증이다 — **형질 식을 따로 적으면 모호.** 컴파일러는 **뜻을 보지 않고 식의 출처를 본다.**

### 3. ★★★ 「`requires { sizeof(T) > 4; }` 는 크기가 4 보다 큰 타입만 받는다」

(3)이 반증이다 — **`char` 도 1.** 식이 **되나**만 보고 **값은 안 본다.** 값을 보려면 `requires sizeof(T) > 4` 를 **안에 한 번 더** 쓴다.

### 4. ★★★ 「`std::integral` 을 걸면 정수만 들어온다」

(4)가 반증이다 — **`bool`·`char`·`char8_t`·`wchar_t` 도 들어온다.** `std::unsigned_integral` 은 **`bool` 까지** 받는다.

### 5. ★★ 「`char` 는 `signed_integral` 이다」

(2)가 반증이다 — **이 판(x86-64 Linux)의 선택**일 뿐, `-funsigned-char` 한 줄로 `std::integral` 쪽으로 넘어간다.

### 6. ★★ 「두 컴파일러가 같은 표를 냈으니 표준 컨셉은 구현 간 일치가 확인됐다」

(4)가 반증이다 — **clang 도 libstdc++ 13 을 읽었다.** 확인된 것은 **한 라이브러리 구현**이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 거의 전부가 표준이다** — 어느 오버로드가 골라지나 · 원자 제약의 동일성 · 요구의 뜻은 **표준이 정하고**, **`char` 의 부호**만 ABI 가, **진단**만 컴파일러가 정한다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **제약 불만족 = 후보 탈락** · **subsumption 은 원자 제약의 동일성으로** · **단순 요구는 식의 유효성만** · **`is_unsigned_v<bool>` 은 참** | cppreference 두 쪽 · 두 컴파일러 | ★★ **표준 컨셉의 표는 libstdc++ 한 구현만 봤다** — libc++ 가 이 머신에 없다(`-stdlib=libc++` 는 링크에서 막혔다) |
| **조건부 표준** | 특정 판에서만 | ★★ **컨셉 전부 C++20부터** | ★ `-std=c++17` 로 던지지 않았다 | — |
| **구현 정의 · ABI** | 문서화 의무 | ★★★ **`char` 의 부호**((2)) — x86-64 Linux 는 부호 있음 | `-funsigned-char` 대조 | ★ **다른 ABI 는 플래그로 흉내만 냈다** — ARM 머신에서 돌리지 않았다 |
| **컴파일러의 것** | 표준 밖 | ★★★ **모호 에러에 이유를 적나**(clang 은 적고 g++ 는 안 적는다)((2)) · 진단 문구 · `auto:1` 이라는 이름 | 두 컴파일러 전문 | ★ **진단 줄 수는 35편이 쟀다** |
| **UB** | 아무 일이나 | ★ **이 편의 코드는 UB 가 없다** | — | — |

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 막혀야 할 칸은 전부 **`cc exit=1`** 이었다. 「통과했는데 뜻이 다른」 자리는 있다 — **`BigA` 가 `char` 에 참**((3))인 것 — 그러나 그것은 **ill-formed 가 아니라 뜻을 잘못 적은 것**이다. **컴파일러가 잡을 수 없는** 종류다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 매개변수 하나에 제약 하나 | ★★ **`template<std::integral T>` 또는 `std::integral auto`** | (1) — 같은 결과 |
| 두 매개변수가 **같은 타입**이어야 | ★★★ **이름 붙인 `T` 하나** | (1) — `auto` 둘은 따로 추론 |
| 제약이 여러 줄 · `&&` 로 엮임 | ★★ **`requires` 절** | 읽기 쉽다 |
| 겹치는 제약으로 오버로드를 가른다 | ★★★ **공통 부분을 컨셉으로 이름 붙인다** | (2) — 형질 식을 따로 적으면 모호 |
| 「이 멤버가 있나」 | ★★ **`requires` 식의 단순 요구** | (3) |
| 「값이 참이어야」(크기 등) | ★★★ **중첩 요구 `requires 식;`** | (3) — 단순 요구는 값을 안 본다 |
| 정수 — `bool` 은 빼고 | ★★ **`std::integral<T> && !std::same_as<T, bool>`** 을 컨셉으로 | (4) |
| 전달 참조 `T&&` 에 제약 | ★★ **`std::remove_cvref_t<T>` 에 건다** | (4) — `int&` 는 `integral` 이 아니다 |

## 핵심 문장

- ★★★ **제약의 네 표기는 매개변수 하나에서 같은 답(격자 0 / 12)** — 단 **`auto` 는 매개변수마다 따로** 추론돼 `(1, 2L)` 을 받는다.
- ★★★ **더 제약된 오버로드가 골라진다** — `int` 는 `signed_integral` 쪽, **`char` 는 이 ABI 에서만** 그쪽.
- ★★★ **같은 형질 식을 두 번 따로 적으면 subsumption 이 안 된다 — 모호 에러.** 컨셉으로 이름 붙이면 풀린다.
- ★★ **`requires { 식; }` 은 식이 되나만 본다** — 값은 `requires { requires 식; }`.
- ★★ **`std::integral` 은 `bool`·`char` 를 담고, `bool` 은 `unsigned_integral` 이기도 하다.**

## 관련 자료

- [35번](../35-instantiation-header-placement-and-reading-errors/) (7)(8) — ★★★ **컨셉이 오류를 호출 줄로 옮긴다 · 줄 수는 오히려 늘었다.** 여기는 그 뒤 — **어떻게 적고 어떻게 고르나.**
- [31번](../31-function-templates-and-argument-deduction/) — ★★ **추론 충돌**((1)의 `take2`) · **전달 참조의 `T = int&`**((4)).
- [37번](../37-sfinae-and-enable-if/) — ★★ **같은 의도를 C++20 이전에 적던 법.** 여기는 컨셉, 저기는 `enable_if`·`void_t`.
- [01번](../01-function-overloading-and-overload-resolution/) — 오버로드 해석의 기본 순서. subsumption 은 **그 순서가 비겼을 때의** 마지막 판정이다.
- Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (9) — ★★ **Rust 의 경계는 이름(`impl`)으로 걸린다** — C++ 컨셉은 **모양**으로 맞는다((3)의 `Bag`).

## 용어 풀이

> **컨셉(concept)** — 템플릿 인자에 대한 요구를 이름 붙인 것. `bool` 로 평가되는 상수 식이다.\
> 예: (3)의 `HasSize`.

> **제약(constraint)** — 템플릿에 걸린 조건. 만족하지 않으면 그 템플릿은 **후보에서 빠진다.**\
> 예: (1)의 네 표기.

> **원자 제약(atomic constraint)** — `&&`·`||` 로 더 쪼갤 수 없는 제약 조각. **소스의 같은 식에서 나왔을 때만** 서로 같다.\
> 예: (2)의 8행과 11행의 `std::is_integral_v<T>` — 글자는 같고 원자는 다르다.

> **subsumption(포함)** — 제약 P 가 Q 를 함의한다고 **원자 동일성만으로** 증명되면 P 가 더 제약된 것이다. 둘 다 맞으면 P 쪽 오버로드가 골라진다.\
> 예: (2)의 `signed_integral` 대 `integral`.

> **`requires` 식(requires expression)** — `requires (매개변수) { 요구… }`. 요구가 전부 성립하면 `true`.\
> 예: (3).

> **단순 요구 / 중첩 요구** — `식;` 은 식이 **유효한가**, `requires 식;` 은 식의 **값이 참인가**.\
> 예: (3)의 `BigA` / `BigB`.

> **축약 함수 템플릿(abbreviated function template)** — 매개변수 타입에 `auto`(또는 `컨셉 auto`)를 쓴 함수. **`auto` 마다 템플릿 매개변수가 하나** 생긴다.\
> 예: (1)의 `FORM=4`.

## 더 들어가면

- **`||` 제약과 subsumption** — 이 편은 `&&` 만 던졌다. `||` 가 섞이면 정규형(DNF·CNF) 변환이 끼어든다(cppreference 의 정의).
- **클래스 템플릿 멤버의 뒤 `requires` 절** — 이 편은 **던지지 않았다.** 32편의 클래스 템플릿 위에서 다음에 볼 자리다.
- **libc++ 에서의 표준 컨셉 표** — 이 머신에 libc++ 가 없어 **못 쟀다**(제3의 상태 — `-stdlib=libc++` 가 링크에서 막혔다).
