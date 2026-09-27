# cpp/syntax/37 — SFINAE 와 `enable_if` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — SFINAE](https://en.cppreference.com/w/cpp/language/sfinae) · [cppreference — `std::experimental::is_detected`](https://en.cppreference.com/w/cpp/experimental/is_detected)\
> ★ 이 배치에서 **위 두 cppreference 쪽을 열어 확인했다** — 「**Only the failures in the types and expressions in the immediate context of the function type or its template parameter types … are SFINAE errors. If the evaluation of a substituted type/expression causes a side-effect such as instantiation of some template specialization … errors in those side-effects are treated as hard errors.**」 · `is_detected` 는 **`<experimental/type_traits>` · library fundamentals TS v2** 에 정의된다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★★ **clang 도 libstdc++ 13 을 쓴다** — `std::enable_if`·`std::void_t`·`<experimental/type_traits>` 는 **두 컴파일러가 같은 헤더**를 읽었다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`sf01.cpp`·`imm01.cpp`·`imm02.cpp`·`redecl.cpp`·`ifc01.cpp`·`ifc02.cpp`·`detect01.cpp`·`sf-grid.sh`).\
> ★ **진단에 소스 경로가 박히지 않게 상대 경로로 컴파일**했다. 표준 헤더 경로(`/usr/include/c++/13/…`)는 그대로 남는다. 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — SFINAE 규칙은 **C++98부터**(표현식 SFINAE 는 **C++11부터**), `std::enable_if` 는 **C++11**, `enable_if_t` 는 **C++14**, `std::void_t` 는 **C++17**, `if constexpr` 는 **C++17**, 컨셉은 **C++20** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[36번](../36-concepts-and-requires/)에서 온다** — 거기서 **컨셉으로** 적은 「이 타입만 받는다」를 여기서는 **C++20 이전의 방법으로** 적고, **읽어 낸 뒤 컨셉으로 되돌려 쓴다.**\
> [35번](../35-instantiation-header-placement-and-reading-errors/) (5)(7) — **제약 없는 템플릿은 첫 에러가 몸통, 컨셉이 걸리면 호출 줄.** 이 편의 격자 (1)은 **SFINAE 판도 그 「호출 줄」 쪽에 선다**는 것을 센다.
> **경계** — 「컨셉 문법과 subsumption」은 [36번](../36-concepts-and-requires/)이, 「부분 특수화」(void_t 탐지가 기대는 장치)는 [33번](../33-template-specialization-and-partial-specialization/)이, 「오버로드 해석」은 [01번](../01-function-overloading-and-overload-resolution/)이 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · ★★ **진단의 줄 수**((1) 격자의 「N줄」 — 이 판의 관찰, 규칙 24) | ★★★ **통과 / 에러(`cc exit`)** · **골라진 오버로드의 출력**(`0` · `-1`) · ★★★ **첫 error 의 행 · 호출 줄인가(O/X)** |
> | — | ★★★ **격자의 마지막 줄** — 「에러 칸 N / M · 호출 줄 N / M · 컴파일러 사이 N / M」 |

## 한눈에 — 쉽게 말하면

**SFINAE 는 「지원서 서류 심사」다.** 지원서(함수 템플릿의 **선언** — 반환 타입·매개변수·템플릿 매개변수)에 **빈칸을 채울 수 없으면** 그 지원자는 **조용히 탈락**한다. 에러가 아니다.

- 그런데 **면접(함수 몸통)** 에서 사고가 나면 그건 **탈락이 아니라 사고**다 — 하드 에러.
- **서류에 붙은 추천서(다른 템플릿)를 펼쳐 봐야 알 수 있는 결함**도 사고다 — 추천서를 펼치는 순간(인스턴스화) 거기서 난 에러는 서류 심사 밖이다((2)).
- 컨셉은 **지원 자격을 공고문에 적는 것**이고, SFINAE 는 **서류 양식에 빈칸이 생기게 만들어** 같은 효과를 내는 **요령**이다.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 서류 빈칸 → 조용히 탈락 | ★★★ **치환 실패는 에러가 아니다(SFINAE)** | (1) |
| 면접에서 사고 | ★★★ **몸통 안 오류는 하드 에러** | (1) 판 0 · (2) |
| 추천서를 펼쳐야 알 수 있는 결함 | ★★★ **즉시 문맥 밖 — `Inner<T>` 의 몸통** | (2) |
| 같은 양식을 두 번 제출 | ★★★ **기본 템플릿 인자만 다른 두 오버로드 = 재선언** | (3) |
| 공고문의 자격 요건 | ★★ **컨셉 · `requires`** | (1) 판 4 |

```text
   count_of(42)                       후보: template <class T> enable_if_t<has_size<T>::value, size_t> count_of(const T&)
        │                                     int count_of(...)
        ▼
   T = int 추론 → 선언에 치환: enable_if_t<false, size_t> → 「type 이 없다」
        │
        ├── 즉시 문맥(선언의 타입) 안의 실패 → ★ 후보에서 조용히 빠진다   → count_of(...) 가 골라져 -1
        │
        └── 몸통 · 다른 템플릿의 몸통 안의 실패 → ★ 하드 에러             (1) 판 0 · (2)
```

## 이 주제가 답하려는 질문

1. ★★★ **같은 의도(「`.size()` 가 있는 타입만」)를 네 가지 옛 방법·새 방법으로 적으면 무엇이 같고 무엇이 다른가**((1)).
2. ★★★ **어떤 실패가 「조용한 탈락」이고 어떤 실패가 하드 에러인가**((2)).
3. ★★ **`enable_if` 를 기본 템플릿 인자에 걸 때 무엇이 깨지나**((3)).
4. ★★ **SFINAE 를 안 써도 되는 자리 — `if constexpr` · 컨셉 · 그리고 `is_detected` 는 표준인가**((4)(5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러와 ⑤ 진단 세기 격자다

★★★ **SFINAE 의 결론은 「어느 오버로드가 골라졌나」와 「에러가 어디에 났나」 두 가지**다 — 앞은 **출력**이, 뒤는 **격자의 O/X** 가 답한다.\
★★ **35편의 `err-count.sh` 칸(첫 error 의 행 · 호출 줄인가)을 그대로 가져와** 판 다섯에 적용했다.

```text
① 다섯 층 표            SFINAE·즉시 문맥은 표준 · is_detected 는 TS · 진단은 컴파일러       (구현 세부사항 절)
② ★ 두 컴파일러          골라진 오버로드 · 하드 에러 전문 · 재선언 전문                     (1)~(5)
③ ASan                   —                                                                부적용
④ 어셈블리·기호표        —                                                                부적용
⑤ ★ 진단 세기 격자       판 5 × 인자 3 × 대안 2 × 컴파일러 2 — 행 · O/X                   (1)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **즉시 문맥의 경계는 표준, `is_detected` 는 표준이 아니라 TS** | **쓴다** |
| ★★★ **② 두 컴파일러** | ★★★ **본체** — 격자 **컴파일러 사이 0 / 30** · 하드 에러 두 쌍 · 재선언 두 전문 | **쓴다** |
| ③ ASan | ★ **부적용** — 결론이 전부 컴파일 단계에서 난다(18-B) | **안 쓴다** |
| ④ 어셈블리 → 기호표 | ★ **부적용** — 탈락한 후보는 **코드를 만들지 않는다.** 골라진 쪽은 출력이 말한다 | **안 쓴다** |
| ★★★ **⑤ 진단 세기** | ★★★ **에러 칸 24 / 60 · 그중 첫 error 가 호출 줄 16 / 24** — 호출 줄이 아닌 8칸은 **전부 판 0(제약 없음)** | **쓴다** |

### (1) ★★★ 같은 의도 다섯 판 — 격자

**언제 쓰나** — 컨셉 이전 코드(C++11\~17)를 **읽을 때**. `enable_if_t<…>` 가 반환 타입에 있거나 `template <class T, …= 0>` 꼴이 보이면 이 절이다.

```cpp
/* sf01.cpp */
// 같은 의도 — 「.size() 가 있는 타입만 받는 count_of」 — 를 다섯 판으로. -DFORM=0..4 로 하나만 켠다.
// -DFALLBACK 이면 무엇이든 받는 count_of(...) 를 하나 더 둔다. -DARG=<타입> 으로 인자를 고른다
#include <cstddef>
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

struct Plain {
    int v;
};

template <class T, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<const T&>().size())>> : std::true_type {};

#if FORM == 0
template <class T> std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 1
template <class T> std::enable_if_t<has_size<T>::value, std::size_t> count_of(const T& t) { return t.size(); }
#elif FORM == 2
template <class T, std::enable_if_t<has_size<T>::value, int> = 0> std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 3
template <class T, class = std::void_t<decltype(std::declval<const T&>().size())>>
std::size_t count_of(const T& t) { return t.size(); }
#elif FORM == 4
template <class T>
    requires requires(const T& t) { t.size(); }
std::size_t count_of(const T& t) { return t.size(); }
#endif

#ifdef FALLBACK
int count_of(...) { return -1; }
#endif

int main() {
    ARG x{};
    std::printf("%d\n", static_cast<int>(count_of(x)));
}
```

- ★★ **판 0** — 제약 없음(35편의 `deep01` 자리) · **판 1** — `enable_if_t` 를 **반환 타입**에 · **판 2** — `enable_if_t<…, int> = 0` 을 **기본 템플릿 인자**에 · **판 3** — `void_t<decltype(…)>` 를 **기본 템플릿 인자**에(탐지를 직접) · **판 4** — C++20 `requires`.
- ★ 판 1·2 가 쓰는 **`has_size`** 가 **탐지 관용구(detection idiom)** 다 — 기본 `false_type` + **`void_t<decltype(식)>` 이 되면 고르는 부분 특수화** `true_type`(33편의 부분 특수화). 식이 안 되면 부분 특수화의 치환이 실패해 **조용히** 기본이 남는다 — 그것도 SFINAE 다.

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

- ★★★ **판 1\~4 는 한 칸도 다르지 않다** — `std::string` 은 `0`(빈 문자열의 `size()`), `int`·`Plain` 은 **대안이 없으면 호출 줄(37행) 에러 · 대안이 있으면 `-1`**. **옛 세 판과 컨셉이 같은 의도를 같은 결과로** 냈다.
- ★★★ **판 0 은 대안이 있어도 에러** — 제약이 없으니 템플릿이 **후보에 남고**, `count_of(const T&)` 가 `count_of(...)` 보다 **나은 후보**라 골라진다. **그 뒤 몸통(17행)에서 깨진다** — 하드 에러. 「대안을 두면 된다」는 **선언에서 떨어뜨릴 때만** 통한다.
- ★★★ **첫 error 가 호출 줄인 칸 16 / 24 — 나머지 8 칸이 전부 판 0.** SFINAE 판도 **컨셉과 같이 에러를 호출 줄로 당긴다**(후보가 탈락해 「맞는 함수가 없다」가 되기 때문이다).
- ★★ **줄 수는 판마다 다르다** — g++ 판 1 **17줄** · 판 2·3 **11줄** · 판 4 **17줄**(이 판의 관찰 — 흔들리는 칸). 35편과 같다 — **바뀌는 것은 길이가 아니라 자리**다.

**★★ 판 1 의 에러를 열면** — 컨셉과 달리 **이유가 「조건이 거짓」이 아니라 「`type` 이 없다」로** 나온다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 -DARG=int sf01.cpp -o ex (cc exit=1) =====
sf01.cpp: In function ‘int main()’:
sf01.cpp:37:50: error: no matching function for call to ‘count_of(int&)’
   37 |     std::printf("%d\n", static_cast<int>(count_of(x)));
      |                                          ~~~~~~~~^~~
sf01.cpp:19:70: note: candidate: ‘template<class T> std::enable_if_t<has_size<T>::value, long unsigned int> count_of(const T&)’
   19 | template <class T> std::enable_if_t<has_size<T>::value, std::size_t> count_of(const T& t) { return t.size(); }
      |                                                                      ^~~~~~~~
sf01.cpp:19:70: note:   template argument deduction/substitution failed:
In file included from /usr/include/c++/13/bits/char_traits.h:50,
                 from /usr/include/c++/13/string:42,
                 from sf01.cpp:5:
/usr/include/c++/13/type_traits: In substitution of ‘template<bool _Cond, class _Tp> using std::enable_if_t = typename std::enable_if::type [with bool _Cond = false; _Tp = long unsigned int]’:
sf01.cpp:19:70:   required by substitution of ‘template<class T> std::enable_if_t<has_size<T>::value, long unsigned int> count_of(const T&) [with T = int]’
sf01.cpp:37:50:   required from here
/usr/include/c++/13/type_traits:2610:11: error: no type named ‘type’ in ‘struct std::enable_if<false, long unsigned int>’
 2610 |     using enable_if_t = typename enable_if<_Cond, _Tp>::type;
      |           ^~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 -DARG=int sf01.cpp -o ex (cc exit=1) =====
sf01.cpp:37:42: error: no matching function for call to 'count_of'
   37 |     std::printf("%d\n", static_cast<int>(count_of(x)));
      |                                          ^~~~~~~~
sf01.cpp:19:70: note: candidate template ignored: requirement 'has_size<int, void>::value' was not satisfied [with T = int]
   19 | template <class T> std::enable_if_t<has_size<T>::value, std::size_t> count_of(const T& t) { return t.size(); }
      |                                                                      ^
1 error generated.
```

- ★★★ **g++ 는 이유를 `enable_if` 의 몸통으로 말한다** — `no type named ‘type’ in ‘struct std::enable_if<false, long unsigned int>’`(표준 헤더 `type_traits:2610`). **읽는 법** — 「`enable_if<false, …>`」가 보이면 **첫 인자(조건)가 거짓**이라는 뜻이다. 조건이 무엇이었는지는 **위의 `candidate:` 줄**(`has_size<T>::value`)에서 읽는다.
- ★★★ **clang 은 번역해 준다** — `requirement 'has_size<int, void>::value' was not satisfied`. clang 이 `enable_if` 를 **알아보고 컨셉처럼 말한다.**
- ★ **g++ 의 이 블록에는 `error:` 가 두 줄**이다 — 두 번째는 표준 헤더 안이다. **`error:` 줄 수는 실수의 수가 아니다**(35편 (6)).

**★★ 판 0 의 에러를 열면** — 대안 `count_of(...)` 가 있는데도 —

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=0 -DARG=int -DFALLBACK sf01.cpp -o ex (cc exit=1) =====
sf01.cpp: In instantiation of ‘std::size_t count_of(const T&) [with T = int; std::size_t = long unsigned int]’:
sf01.cpp:37:50:   required from here
sf01.cpp:17:64: error: request for member ‘size’ in ‘t’, which is of non-class type ‘const int’
   17 | template <class T> std::size_t count_of(const T& t) { return t.size(); }
      |                                                              ~~^~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=0 -DARG=int -DFALLBACK sf01.cpp -o ex (cc exit=1) =====
sf01.cpp:17:63: error: member reference base type 'const int' is not a structure or union
   17 | template <class T> std::size_t count_of(const T& t) { return t.size(); }
      |                                                              ~^~~~~
sf01.cpp:37:42: note: in instantiation of function template specialization 'count_of<int>' requested here
   37 |     std::printf("%d\n", static_cast<int>(count_of(x)));
      |                                          ^
1 error generated.
```

- ★★★ **17행(몸통 `t.size()`)이 첫 에러** · g++ `In instantiation of …` 사슬 · clang `in instantiation of function template specialization 'count_of<int>' requested here`. **대안이 있다는 사실은 진단에 한 번도 안 나온다** — 오버로드 해석은 이미 끝났다.

### (2) ★★★ 즉시 문맥 — 조용한 탈락과 하드 에러의 경계

**언제 쓰나** — 「SFINAE 를 걸었는데 왜 대안으로 안 가고 에러가 나지?」 할 때.

**쌍 1 — 반환 타입을 적었나, 추론하게 뒀나**

```cpp
/* imm01.cpp */
// 즉시 문맥 — 반환 타입을 decltype 으로 적은 판(기본) 대 auto 로 추론하게 둔 판(-DDEDUCED).
// 둘 다 무엇이든 받는 대안 count_of(...) 가 있다
#include <cstdio>

#ifdef DEDUCED
template <class T> auto count_of(const T& t) { return t.size(); }
#else
template <class T> auto count_of(const T& t) -> decltype(t.size()) { return t.size(); }
#endif
int count_of(...) { return -1; }

int main() { std::printf("%d\n", static_cast<int>(count_of(42))); }
```

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

- ★★★ **`-> decltype(t.size())` 는 `-1`** — 반환 타입이 **선언의 일부**라 `int` 에서 `t.size()` 가 안 되는 것이 **치환 실패**가 되고, 템플릿이 탈락해 `count_of(...)` 가 골라졌다.
- ★★★ **`auto` 로 두면 하드 에러(6행)** — 반환 타입을 알려면 **몸통을 인스턴스화해야** 하고, 몸통 안의 실패는 즉시 문맥이 아니다. **같은 몸통, 한 줄 차이**다.

**쌍 2 — 기본 템플릿 인자가 직접 읽나, 다른 템플릿이 읽나**

```cpp
/* imm02.cpp */
// 즉시 문맥 — 기본 템플릿 인자에서 T::value_type 을 직접 읽는 판(기본) 대
// 보조 클래스 Inner<T> 의 몸통이 읽게 한 판(-DNESTED). 둘 다 대안 kind(...) 가 있다
#include <cstdio>

template <class T> struct Inner {
    using type = typename T::value_type;
};

#ifdef NESTED
template <class T, class = typename Inner<T>::type> const char* kind(T) { return "template"; }
#else
template <class T, class = typename T::value_type> const char* kind(T) { return "template"; }
#endif
const char* kind(...) { return "fallback"; }

int main() { std::printf("%s\n", kind(42)); }
```

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

- ★★★ **`class = typename T::value_type` 는 `fallback`** — `int::value_type` 이 없다는 실패가 **템플릿 매개변수 타입 자체**에서 나서 즉시 문맥이다.
- ★★★ **`class = typename Inner<T>::type` 은 하드 에러(6행)** — `Inner<int>` 를 **인스턴스화하는 부수 효과** 안에서 실패했다. cppreference 의 「**instantiation of some template specialization … treated as hard errors**」 그대로다.
- ★★ **두 컴파일러 다 에러 줄을 `Inner` 의 몸통(6행)** 으로 잡고 호출 줄(16행)은 사슬 끝에 적는다 — **35편의 「사슬」 모양으로 돌아갔다.**

```text
   즉시 문맥 안(조용히 탈락)                      즉시 문맥 밖(하드 에러)
   ─────────────────────────                      ──────────────────────────
   -> decltype(t.size())      반환 타입            auto + 몸통의 t.size()          몸통을 봐야 반환 타입을 안다
   class = typename T::value_type                  class = typename Inner<T>::type  Inner<T> 를 인스턴스화한다
   enable_if_t<false, …>      반환 타입·기본 인자   (1) 판 0 의 몸통                 오버로드가 끝난 뒤
```

### (3) ★★★ 기본 템플릿 인자 방식의 함정 — 조건만 다른 두 오버로드

**언제 쓰나** — `enable_if` 로 **정수면 A, 실수면 B** 처럼 오버로드를 가를 때.

```cpp
/* redecl.cpp */
// 조건만 다른 두 오버로드 — 기본 템플릿 인자로 enable_if 를 거는 두 모양. -DNTTP 이면 「enable_if_t<…, int> = 0」
#include <cstdio>
#include <type_traits>

#ifdef NTTP
template <class T, std::enable_if_t<std::is_integral_v<T>, int> = 0> const char* kind(T) { return "integral"; }
template <class T, std::enable_if_t<std::is_floating_point_v<T>, int> = 0> const char* kind(T) { return "floating"; }
#else
template <class T, class = std::enable_if_t<std::is_integral_v<T>>> const char* kind(T) { return "integral"; }
template <class T, class = std::enable_if_t<std::is_floating_point_v<T>>> const char* kind(T) { return "floating"; }
#endif

int main() { std::printf("%s %s\n", kind(1), kind(1.5)); }
```

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

- ★★★ **`template <class T, class = enable_if_t<…>>` 두 개는 「같은 템플릿의 재선언」** — g++ `redefinition of ‘template<class T, class> const char* kind(T)’` · clang `template parameter redefines default argument` + `redefinition of 'kind'`. **기본 인자는 서명의 일부가 아니다** — 두 선언의 서명이 둘 다 `template<class T, class> const char* kind(T)` 로 **똑같다.**
- ★★ **그 뒤의 에러는 연쇄다** — 두 번째 정의가 버려져 `kind(1.5)`(g++)·`kind(1)`·`kind(1.5)`(clang)에서 후보가 모자란다. **첫 에러만 원인**이다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DNTTP redecl.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
integral floating
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DNTTP redecl.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
integral floating
```

- ★★★ **`enable_if_t<…, int> = 0`(판 2 의 꼴)이면 통과하고 `integral floating`** — 조건이 **템플릿 매개변수의 타입** 안에 들어가 두 선언의 서명이 **달라진다.** 판 2 가 이 꼴인 이유다.
- ★★ **컨셉으로 되돌려 쓰면 이 함정이 없다** — `template <std::integral T>` 와 `template <std::floating_point T>` 는 **제약이 서명의 일부**라 서로 다른 템플릿이다(36편).

### (4) ★★ `if constexpr` — 오버로드 두 벌 대신 함수 하나

**언제 쓰나** — 「타입에 따라 **몸통만** 다르다」일 때. 오버로드를 가를 필요가 없으면 SFINAE 를 안 쓴다.

```cpp
/* ifc01.cpp */
// 오버로드 두 벌 대신 함수 하나 — if constexpr 로 가지를 고른다(has_size 는 void_t 탐지)
#include <cstddef>
#include <cstdio>
#include <string>
#include <type_traits>
#include <utility>

template <class T, class = void> struct has_size : std::false_type {};
template <class T> struct has_size<T, std::void_t<decltype(std::declval<const T&>().size())>> : std::true_type {};

template <class T> std::size_t measure(const T& t) {
    if constexpr (has_size<T>::value) {
        return t.size();
    } else {
        return sizeof(t);
    }
}

int main() { std::printf("%zu %zu\n", measure(std::string("abc")), measure(1.0)); }
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic ifc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
3 8
===== clang++ -std=c++20 -Wall -Wextra -pedantic ifc01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
3 8
```

- ★★★ **`3 8`** — `std::string` 은 `size()` 가지, `double` 은 `sizeof` 가지. **버린 가지(`t.size()` on `double`)는 인스턴스화되지 않아 에러가 없다.**
- ★★ **단 템플릿 안에서만이다** —

```cpp
/* ifc02.cpp */
// 템플릿이 아닌 함수의 if constexpr — 버린 가지에 선언 없는 이름을 둔다
int f() {
    if constexpr (false) {
        return no_such_function();
    }
    return 0;
}

int main() { return f(); }
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

- ★★★ **템플릿이 아닌 함수에서는 `if constexpr (false)` 의 가지도 검사된다** — 두 컴파일러 다 `no_such_function` 을 에러로 적는다. 버린 가지가 검사를 피하는 것은 「**템플릿의 인스턴스화에서 버려질 때**」 뿐이다.

### (5) ★ `is_detected` 는 표준인가

**언제 쓰나** — 인터넷의 탐지 관용구 예제가 `std::is_detected` 를 쓸 때.

```cpp
/* detect01.cpp */
// 탐지 관용구의 표준 이름 — -DSTD 이면 std::is_detected_v, 아니면 std::experimental::is_detected_v
#include <cstdio>
#include <experimental/type_traits>
#include <string>
#include <utility>

template <class T> using size_expr = decltype(std::declval<const T&>().size());

#ifdef STD
using std::is_detected_v;
#else
using std::experimental::is_detected_v;
#endif

int main() { std::printf("%d %d\n", is_detected_v<size_expr, std::string>, is_detected_v<size_expr, int>); }
```

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

- ★★★ **`std::experimental::is_detected_v` 는 된다(`1 0`) · `std::is_detected_v` 는 `-std=c++23` 에서도 없다** — g++ `‘is_detected_v’ has not been declared in ‘std’` · clang `no member named 'is_detected_v' in namespace 'std'; did you mean 'std::experimental::is_detected_v'?`.
- ★★ **`is_detected` 는 library fundamentals TS v2** 의 것이다 — 표준 C++ 에 들어오지 않았다. ★ **두 컴파일러가 같은 결론을 낸 것은 같은 libstdc++ 13 헤더를 읽어서**다.
- ★★ **C++20 에서는 탐지 자체가 필요 없다** — `requires { t.size(); }`((1) 판 4)가 같은 질문을 **언어로** 묻는다.

## 문법 — 형태와 규칙

### 형태

```text
   template <class T> std::enable_if_t<cond<T>, R> f(T);                 ① 반환 타입 SFINAE
   template <class T, std::enable_if_t<cond<T>, int> = 0> R f(T);          ② 기본 템플릿 인자 — 비타입 매개변수 꼴
   template <class T, class = std::enable_if_t<cond<T>>> R f(T);           ②' ★ 오버로드끼리 재선언이 된다
   template <class T> auto f(const T& t) -> decltype(t.size());            ③ 표현식 SFINAE(C++11)
   template <class T, class = void> struct has_x : std::false_type {};      ④ 탐지 관용구 — void_t(C++17)
   template <class T> struct has_x<T, std::void_t<decltype(식)>> : std::true_type {};
   template <class T> requires requires(const T& t) { t.size(); } R f(T);  ⑤ C++20 — 같은 의도
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(3)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **선언(반환 타입·매개변수 타입·템플릿 매개변수)에 치환하다 실패하면 후보에서 빠진다 — 에러가 아니다**((1)).
- ★★★ **몸통 · 추론된 반환 타입 · 다른 템플릿의 인스턴스화 안의 실패는 하드 에러다**((1) 판 0 · (2)).
- ★★★ **기본 템플릿 인자는 서명이 아니다 — 조건만 다른 두 오버로드는 재선언**((3)). **`enable_if_t<…, int> = 0`** 으로 쓴다.
- ★★ **탈락한 후보만 남으면 「맞는 함수가 없다」가 호출 줄에서 난다**((1) 16 / 24).
- ★★ **몸통만 다르면 `if constexpr` — 템플릿 안에서만** 버린 가지가 검사를 피한다((4)).
- ★ **`std::is_detected` 는 표준에 없다** — `std::experimental`(TS)((5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| 제약 없는 템플릿 + 대안 `(...)` | `request for member ‘size’ in ‘t’ …` (몸통) | `member reference base type 'const int' …` (몸통) | (1) |
| `auto` 반환 타입 + 대안 | `request for member ‘size’ …` | `member reference base type …` | (2) |
| 기본 인자 안에서 `Inner<T>::type` | `‘int’ is not a class, struct, or union type` | `type 'int' cannot be used prior to '::'` | (2) |
| `class = enable_if_t<…>` 두 오버로드 | `redefinition of ‘template<class T, class> …’` | `template parameter redefines default argument` | (3) |
| 비템플릿 함수의 `if constexpr (false)` 가지에 없는 이름 | `‘no_such_function’ was not declared` | `use of undeclared identifier` | (4) |
| `std::is_detected_v` | `has not been declared in ‘std’` | `no member named 'is_detected_v' in namespace 'std'` | (5) |

## 어디서 틀리나

### 1. ★★★ 「대안 오버로드를 두면 SFINAE 가 알아서 그쪽으로 보낸다」

(1) 판 0 · (2)가 반증이다 — **제약이 선언에 없으면(판 0) · 몸통을 봐야 하면(`auto`) · 다른 템플릿을 펼쳐야 하면(`Inner`) 하드 에러.**

### 2. ★★★ 「`class = enable_if_t<…>` 로 정수판·실수판 두 오버로드를 만들 수 있다」

(3)이 반증이다 — **재선언 에러.** `enable_if_t<…, int> = 0` 이어야 한다.

### 3. ★★ 「SFINAE 는 에러를 템플릿 깊숙이 밀어 넣는다 — 컨셉만 호출 줄로 당긴다」

(1)이 반증이다 — **판 1\~3 도 첫 에러가 호출 줄**(37행)이다. 다른 것은 **이유를 말하는 방식**(g++ 의 `enable_if<false, …>`)이다.

### 4. ★★ 「`if constexpr (false)` 의 가지는 컴파일되지 않는다」

(4)가 반증이다 — **비템플릿 함수에서는 검사된다.**

### 5. ★ 「`std::is_detected` 는 C++17 표준이다」

(5)가 반증이다 — **`-std=c++23` 에서도 없다.** TS 의 `std::experimental` 이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 규칙은 전부 표준이다** — 무엇이 즉시 문맥인가, 기본 인자가 서명인가는 **표준이 정하고**, **진단이 그것을 어떻게 말하나**(g++ 의 `enable_if<false>` 대 clang 의 `requirement … was not satisfied`)는 **컴파일러의 것**이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **즉시 문맥 안 치환 실패 = 후보 탈락** · **부수 효과(인스턴스화) 안 = 하드 에러** · **기본 템플릿 인자는 서명이 아니다** · **`if constexpr` 는 템플릿 안에서만 가지를 버린다** | cppreference · 두 컴파일러 | ★★ **「즉시 문맥」의 경계는 이 편이 두 쌍으로만 확인했다** — 다른 모양(별칭 템플릿·람다)은 던지지 않았다 |
| **조건부 표준** | 특정 판에서만 | ★★ **`void_t` C++17 · `if constexpr` C++17 · 컨셉 C++20** | ★ 판을 내려 던지지 않았다 | — |
| **TS** | 표준 밖 기술 명세 | ★★★ **`std::experimental::is_detected`** — library fundamentals TS v2 | `-std=c++23` 에서도 `std::` 에 없음 | ★ **libstdc++ 한 판만** 봤다 |
| **컴파일러의 것** | 표준 밖 | ★★★ **`enable_if` 실패를 g++ 는 `type` 없음으로, clang 은 요구 불만족으로 말한다** · 줄 수 · 연쇄 에러의 개수 | 두 컴파일러 전문 · 격자 | ★ **줄 수는 이 판 값** |
| **UB** | 아무 일이나 | ★ **이 편의 코드는 UB 가 없다** | — | — |

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 막혀야 할 칸은 전부 `cc exit=1` 이었다. 거꾸로 「**에러여야 할 것 같은데 통과한**」 칸 — 판 1\~4 의 `-1` — 은 **ill-formed 가 아니라 설계된 동작**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| C++20 을 쓸 수 있다 | ★★★ **컨셉 · `requires`** | (1) 판 4 — 같은 결과, 재선언 함정 없음((3)) |
| C++17 이하 · 오버로드를 가른다 | ★★ **`enable_if_t<…, int> = 0`** | (3) — `class = …` 는 재선언 |
| C++17 이하 · 멤버가 있나 | ★★ **`void_t` 탐지 관용구** | (1)의 `has_size` |
| 몸통만 다르다 | ★★★ **`if constexpr`** | (4) — 오버로드 불필요 |
| 옛 코드의 에러를 읽는다 | ★★ **`enable_if<false, …>` = 조건 거짓 · 조건은 `candidate:` 줄** | (1) |
| `std::is_detected` 를 쓰고 싶다 | ★ **`std::experimental` 이거나 직접 정의** — 표준이 아니다 | (5) |

## 핵심 문장

- ★★★ **옛 세 판(`enable_if_t` 반환 · `enable_if_t` 기본 인자 · `void_t`)과 컨셉은 같은 의도에 같은 결과 — 격자 컴파일러 사이 0 / 30, 호출 줄 16 / 24(나머지 8 칸이 전부 제약 없는 판).**
- ★★★ **SFINAE 는 선언에서만** — 몸통 · `auto` 반환 타입 · 다른 템플릿의 인스턴스화 안의 실패는 대안이 있어도 하드 에러.
- ★★★ **`class = enable_if_t<…>` 두 오버로드는 재선언** — 기본 인자는 서명이 아니다. `enable_if_t<…, int> = 0`.
- ★★ **`if constexpr` 의 버린 가지는 템플릿 안에서만 검사를 피한다.**
- ★ **`std::is_detected` 는 표준이 아니다 — `-std=c++23` 에서도.**

## 관련 자료

- [36번](../36-concepts-and-requires/) — ★★★ **같은 의도의 C++20 판.** 여기서 옛 코드를 읽어 내고 저기로 되돌려 쓴다. 재선언 함정이 없는 이유(제약은 서명의 일부)도 저기다.
- [35번](../35-instantiation-header-placement-and-reading-errors/) (5)(8) — ★★ **제약 없는 템플릿의 사슬**과 **세기 격자의 원형**. (1)의 O/X 칸이 거기서 왔다.
- [33번](../33-template-specialization-and-partial-specialization/) — ★★ **부분 특수화** — `has_size<T, void_t<…>>` 가 기대는 장치.
- [31번](../31-function-templates-and-argument-deduction/) — 추론이 끝난 뒤에 치환이 온다 — SFINAE 는 **그 치환 단계**의 규칙이다.

## 용어 풀이

> **SFINAE(Substitution Failure Is Not An Error)** — 템플릿 인자를 **선언에 치환하다 실패하면** 그 템플릿을 후보에서 빼고 **에러로 치지 않는** 규칙.\
> 예: (1) 판 1\~3 의 `-1`.

> **즉시 문맥(immediate context)** — 함수 타입과 템플릿 매개변수 타입 **그 자체**. 여기서의 실패만 SFINAE 다. 다른 템플릿을 인스턴스화하는 부수 효과 안은 밖이다.\
> 예: (2)의 `T::value_type`(안) 대 `Inner<T>::type`(밖).

> **하드 에러(hard error)** — 대안 후보가 있어도 컴파일을 멈추는 에러.\
> 예: (1) 판 0, (2)의 `auto`·`Inner`.

> **`std::enable_if<B, T>`** — `B` 가 참이면 `type` 이 `T`, 거짓이면 **`type` 이 없다.** 그 「없음」을 치환 실패로 쓴다.\
> 예: (1) 판 1·2.

> **탐지 관용구(detection idiom)** — `void_t<decltype(식)>` 을 부분 특수화에 넣어 **식이 되는지를 `bool` 형질로** 바꾸는 방법.\
> 예: (1)의 `has_size`.

> **표현식 SFINAE(expression SFINAE)** — C++11. `decltype(식)` 처럼 **식**을 선언에 넣어 그 식이 안 되면 탈락시키는 것.\
> 예: (2) 쌍 1 의 `-> decltype(t.size())`.

## 더 들어가면

- **클래스 템플릿의 부분 특수화 SFINAE** — `has_size` 가 이미 그것이다. 여러 부분 특수화가 동시에 맞는 모호는 이 편이 던지지 않았다.
- **C++20 에서 람다는 즉시 문맥이 아니다** — cppreference 가 「**A lambda expression is not considered part of the immediate context.(since C++20)**」라고 적는다. 이 편은 **던지지 않았다.**
