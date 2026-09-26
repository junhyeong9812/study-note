# cpp/syntax/39 — 람다와 캡처 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Lambda expressions](https://en.cppreference.com/w/cpp/language/lambda)\
> ★ 이 배치에서 **위 cppreference 쪽을 열어 확인했다** — 「**The implicit capture of `*this` when the capture default is `=` is deprecated.**」(C++20) · `mutable` 은 「**Allows body to modify the objects captured by copy**」 · 람다는 「**a prvalue expression of unique unnamed non-union non-aggregate class type, known as closure type**」 · 템플릿 매개변수 목록이 있는 람다는 **C++20** 이다.
> **실행 검증** — 이 문서의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★ clang 도 같은 라이브러리 — `std::function`·`std::move_only_function` 칸은 한 구현) · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`cap01.cpp`·`thiscap.cpp`·`mut01.cpp`·`mo01.cpp`·`gen01.cpp`·`type01.cpp`·`loop01.cpp`·`cap-grid.sh`·`this-grid.sh`).\
> ★★ **ASan 블록은 `-O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=.`** 로 빌드했고 **값·마커는 표준 오류로** 찍었다(sanitizer 가 `abort` 하면 표준 출력 버퍼가 사라진다 — 규칙 19-A). 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — 람다는 **C++11**, 제네릭 람다(`auto` 매개변수)·초기화 캡처는 **C++14**, `[*this]` 는 **C++17**, `[=]` 의 `this` 암묵 캡처 폐기·`[=, this]`·템플릿 람다는 **C++20**, `std::move_only_function` 은 **C++23** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[09번](../09-rvalue-references-move-and-forward/)과 [30번](../30-dangling-references-and-lifetime-extension/)에서 온다 — 앞 편이 잰 것은 다시 재지 않는다.**\
> [30번](../30-dangling-references-and-lifetime-extension/) (1)(2) — **탐침 5(람다가 지역을 `[&]` 로 잡아 반환)는 `-O0` ASan 두 컴파일러 다 `stack-use-after-return`** · **`detect_stack_use_after_return` 은 이 판에서 기본으로 켜져 있었고 끄면 놓친다** · **clang 은 `-Wreturn-stack-address` 로 경고했다.**\
> ★★ **여기서 새로 묻는 것은 「캡처 모양 일곱 × 부르는 때 셋」 전체**다 — 30편의 한 칸을 격자로 넓히고, **`[this]`·초기화 캡처·`std::function`** 을 더한다. [09번](../09-rvalue-references-move-and-forward/) — **`std::move` 는 캐스트이고 옮기는 것은 이동 생성자** — (4)의 `[p = std::move(p)]` 가 그 이동이다.
> **경계** — 「`std::function` 의 타입 소거 비용」은 목록의 **40번 주제**, 「댕글링 일반과 수명 연장」은 [30번](../30-dangling-references-and-lifetime-extension/), 「`unique_ptr`」은 [26번](../26-unique-ptr-and-ownership-transfer/)이 정본이다.
> ★★★ **「람다가 인라인된다」는 이 문서가 보이지 않았다** — 역어셈블로 확인하지 않은 인라인 주장은 싣지 않는다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID · 주소 · `pc`/`bp`/`sp` · 프레임 오프셋** · 진단 **문구** | ★★★ **리포트 이름**(`stack-use-after-return`·`stack-use-after-scope`) · **`SUMMARY` 의 `파일:줄`** · **`run exit`** · **격자의 마지막 줄** |
> | ★ `sizeof` 의 값 — **이 ABI 의 관찰**(표준은 클로저의 크기를 정하지 않는다) | ★★★ **`mutable` 없는 변경 · move-only 람다를 `std::function` 에 담기 · 템플릿 람다에 `int` 가 에러인가** |

## 한눈에 — 쉽게 말하면

**람다는 「도시락」이다.** 만드는 자리에서 **반찬(캡처)** 을 싸서 들고 나간다.

- **값 캡처 `[x]`** — 반찬을 **덜어서 담는다.** 부엌이 치워져도 도시락은 멀쩡하다.
- **참조 캡처 `[&x]`** — 반찬 대신 **「부엌 3번 선반에 있음」이라는 쪽지**를 담는다. **부엌이 치워지면(함수가 돌아가면 · 블록이 끝나면)** 쪽지가 가리키는 곳은 비었다 — ASan 이 그 자리를 잡는다((1)).
- **`[this]`** 도 쪽지다 — **「이 객체는 저기 있음」.** 객체가 죽으면 같은 사고다. **`[*this]`** 는 객체를 **통째로 덜어 담는다.**
- **초기화 캡처 `[p = std::move(p)]`** — 반찬 통을 **넘겨받는다**(이동). 도시락이 **하나뿐인 통**을 들었으니 **복사할 수 없는 도시락**이 되고, **복사를 요구하는 가방(`std::function`)** 에는 안 들어간다((4)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 덜어 담은 반찬 | ★★ **값 캡처 `[x]`·`[=]`·`[*this]`** | (1) |
| 선반 쪽지 | ★★★ **참조 캡처 `[&x]`·`[&]`·`[this]`** — 댕글링 칸 **12 / 40** | (1) |
| 부엌이 치워짐 | ★★★ **`stack-use-after-return` · `stack-use-after-scope`** | (1) |
| 쪽지인데 겉은 반찬처럼 보임 | ★★★ **`[=]` 의 `this` 암묵 캡처 — C++20 폐기 경고** | (2) |
| 도시락 안에서 반찬을 먹어 치움 | ★★ **`mutable`** — 복사본만 바뀐다 | (3) |
| 하나뿐인 통 → 복사 불가 도시락 | ★★★ **move-only 람다 — `std::function` 에 못 담는다** | (4) |
| 어떤 반찬이든 받는 도시락 | ★ **제네릭 람다 · 템플릿 람다** | (5) |

```text
   auto make() {                           main:
       int x = 42;                             auto f = make();       ← make 의 프레임은 이미 치워졌다
       return [&x] { return x; };              f();                   ← x 의 자리를 읽는다
   }                                                 │
                                                     ▼
                                     ASan 「stack-use-after-return」 — x (line 53)
```

## 이 주제가 답하려는 질문

1. ★★★ **캡처 모양마다, 부르는 때마다 — 어느 칸이 댕글링이고 도구는 그것을 어떻게 잡나**((1)).
2. ★★★ **`[=]` 는 `this` 를 값으로 잡나 — C++20 은 무엇을 폐기했나**((2)).
3. ★★ **값 캡처를 람다 안에서 바꾸면 — `mutable` 은 무엇을 바꾸나**((3)).
4. ★★★ **`unique_ptr` 을 옮겨 잡은 람다는 어디에 담을 수 있나**((4)).
5. ★ **제네릭 람다 · 템플릿 람다 · 람다 타입의 고유성**((5)(6)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ③ ASan 이다

★★★ **댕글링 캡처는 UB 라 「값」을 결과로 실을 수 없다** — 그래서 **ASan 리포트의 이름**이 결과다(30편의 방식).\
★★ **ASan 이 조용한 칸은 두 종류**다 — **값이 멀쩡한 칸**(값을 싣는다)과 **`detect_stack_use_after_return=0` 으로 끈 칸**(값을 싣지 않는다 — 「리포트 없음」만).

```text
① 다섯 층 표            캡처 규칙은 표준 · 클로저 크기는 ABI · 경고는 컴파일러            (구현 세부사항 절)
② ★ 두 컴파일러          this 폐기 경고 격자 · mutable · move-only 전문                   (2)~(5)
③ ★ ASan                 캡처 7 × 때 3 — 기본 · uar=1 · uar=0 세 번 돌린다                (1)
④ 기호표                 제네릭 람다의 operator()<int> · <double> 두 벌                   (5)
⑤ ★ 격자                 캡처 격자 · this 격자 — 마지막 줄을 스크립트가 센다               (1)(2)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **캡처의 뜻은 표준, `sizeof` 는 ABI, 경고 이름은 컴파일러** | **쓴다** |
| ★★ **② 두 컴파일러** | ★★★ `this` 격자 **컴파일러 사이 1 / 9(경고 이름만)** · `mutable` · move-only 전문 | **쓴다** |
| ★★★ **③ ASan** | ★★★ **본체** — **댕글링 칸 12 / 40 · uar=0 이면 사라지는 칸 6 / 12 · 기본과 uar=1 이 다른 칸 0** | **쓴다** |
| ④ 기호표 | ★ **제네릭 람다는 `operator()` 템플릿** — `nm -C` 에 `<int>`·`<double>` 두 벌((5)) | **쓴다** |
| ⑤ 격자 | ★★ **경고가 댕글링을 잡은 칸 2 / 12** — 나머지는 **실행만** 잡았다 | **쓴다** |

### (1) ★★★ 캡처 수명 격자 — 캡처 일곱 × 부르는 때 셋

**언제 쓰나** — 람다를 **만든 자리 밖으로 내보낼 때마다**(반환 · 멤버에 저장 · 콜백 등록).

```cpp
/* cap01.cpp */
// 캡처 일곱(-DCAP=1..7) × 부르는 때 셋(-DWHEN=1..3). 캡처 대상은 42 로 만들고,
// WHEN=1 은 만든 뒤 대상을 7 로 바꾸고 부른다. 값은 표준 오류로 찍는다
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

struct Counter {
    int v = 42;
    auto by_this() { return [this] { return v; }; }
    auto by_copy() { return [*this] { return v; }; }
};

#if CAP == 1
#define SETUP int x = 42;
#define LAMBDA [x] { return x; }
#define CHANGE x = 7;
#elif CAP == 2
#define SETUP int x = 42;
#define LAMBDA [&x] { return x; }
#define CHANGE x = 7;
#elif CAP == 3
#define SETUP int x = 42;
#define LAMBDA [=] { return x; }
#define CHANGE x = 7;
#elif CAP == 4
#define SETUP int x = 42;
#define LAMBDA [&] { return x; }
#define CHANGE x = 7;
#elif CAP == 5
#define SETUP Counter c;
#define LAMBDA c.by_this()
#define CHANGE c.v = 7;
#elif CAP == 6
#define SETUP Counter c;
#define LAMBDA c.by_copy()
#define CHANGE c.v = 7;
#elif CAP == 7
#define SETUP auto p = std::make_unique<int>(42);
#define LAMBDA [p = std::move(p)] { return *p; }
#define CHANGE
#endif

#if WHEN == 1
int call_now() {
    SETUP
    auto f = LAMBDA;
    CHANGE
    return f();
}
#elif WHEN == 2
auto make() {
    SETUP
    return LAMBDA;
}
#endif

int main() {
#if WHEN == 1
    std::fprintf(stderr, "%d\n", call_now());
#elif WHEN == 2
    auto f = make();
    std::fprintf(stderr, "%d\n", f());
#elif WHEN == 3
    std::function<int()> keep;
    {
        SETUP
        keep = LAMBDA;
    }
    std::fprintf(stderr, "%d\n", keep());
#endif
}
```

- ★★ **부르는 때 셋** — `WHEN=1` **즉시**(만든 함수 안에서, 대상을 7 로 바꾼 뒤) · `WHEN=2` **돌려준 뒤**(`make()` 가 끝난 다음) · `WHEN=3` **`std::function` 에 담아 블록 밖**(같은 함수 안, 블록이 끝난 다음).

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

- ★★★ **댕글링 칸 12 / 40** — **참조로 잡는 셋(`[&x]` · `[&]` · `[this]`)의 「돌려준 뒤」·「스코프 밖」** 여섯 행 × 두 컴파일러. 두 컴파일러가 **같은 칸에서 같은 이름**을 냈다.
- ★★★ **「돌려준 뒤」는 `stack-use-after-return` · 「스코프 밖」은 `stack-use-after-scope`** — 앞은 **돌아간 함수의 프레임**, 뒤는 **같은 함수 안에서 끝난 블록**이다. 같은 캡처 · 다른 부르는 때 · **다른 이름**.
- ★★★ **`detect_stack_use_after_return` 판별** — **ASAN_OPTIONS 없이 돌린 칸과 `=1` 칸이 다른 칸 0** — 이 판에서는 **기본으로 켜져 있다**(30편 (2)와 같다). **`=0` 이면 사라지는 칸 6 / 12** — 정확히 **`stack-use-after-return` 여섯 칸**이다. **`use-after-scope` 여섯 칸은 그 옵션과 무관**하게 잡혔다.
- ★★★ **경고는 12 칸 중 2 칸만** — clang 의 `-Wreturn-stack-address` 가 **`[&x]`·`[&]` 의 「돌려준 뒤」** 를 잡았다. **`[this]` 반환 · 「스코프 밖」 여섯 칸 · g++ 전부는 경고 0** — **실행만** 잡았다.
- ★★ **즉시 부르면 참조 캡처는 바뀐 값을 본다** — `[&x]`·`[&]`·`[this]` 가 **7**, 값 캡처(`[x]`·`[=]`·`[*this]`)는 **만든 때의 42**. **값 캡처는 「만든 때」, 참조 캡처는 「부른 때」의 값**이다.
- ★★★ **`[p = std::move(p)]` 는 즉시·돌려준 뒤 모두 42 — 그리고 「`std::function` 에 담기」는 컴파일이 안 된다(`cc 에러`)** — (4)에서 연다.

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

- ★★★ **`[&x]` 를 돌려받아 부른 칸의 g++ 리포트** — `READ of size 4` · 읽은 곳 **`operator()` 54행**(람다 몸통) · 그 주소는 **`make()` 프레임의 `'x' (line 53)`**. ASan 이 「**무엇을 읽었나 · 그것이 누구의 지역이었나**」 를 둘 다 적는다.

```text
   캡처         즉시(7 로 바꾼 뒤)   돌려준 뒤                  std::function · 블록 밖
   [x] [=]      42                   42                         42
   [&x] [&]     7                    ★ use-after-return        ★ use-after-scope
   [this]       7                    ★ use-after-return        ★ use-after-scope
   [*this]      42                   42                         42
   [p=move(p)]  42                   42                         ★ 컴파일 에러(move-only)
   ★ 칸의 값은 위 격자에서 옮긴 요약이다 — 원본은 캡처. uar=0 이면 「돌려준 뒤」의 ★ 가 사라진다
```

**★★ C# 과 견주면** — [C# 28번](../../../csharp/syntax/28-lambdas-and-closure-capture/)은 「**람다는 값이 아니라 변수를 캡처한다 — Roslyn 은 그 변수를 `<>c__DisplayClass` 의 필드로 옮긴다**」를 보였다. 변수가 **힙의 클래스로 옮겨가니** 함수가 끝나도 살아 있고, 그래서 C# 의 `for` 루프는 **`3 3 3`** 이다. C++ 의 `[&i]` 는 **변수를 옮기지 않는다** — 루프가 끝나면 그 변수는 **없다.**

```cpp
/* loop01.cpp */
// 루프 변수를 캡처한 람다 셋을 모아 두고 루프가 끝난 뒤 부른다 — 기본 [i], -DBYREF 이면 [&i]
#include <cstdio>
#include <functional>
#include <vector>

int main() {
    std::vector<std::function<int()>> fns;
    for (int i = 0; i < 3; ++i) {
#ifdef BYREF
        fns.push_back([&i] { return i; });
#else
        fns.push_back([i] { return i; });
#endif
    }
    for (auto& f : fns) std::fprintf(stderr, "%d ", f());
    std::fprintf(stderr, "\n");
}
```

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

- ★★★ **`[i]` 는 `0 1 2`** — 반복마다 **값을 덜어** 담았다. **`[&i]` 는 두 컴파일러 다 `stack-use-after-scope`** — C# 이 `3 3 3` 을 찍은 자리에서 C++ 은 **죽은 변수를 읽는다.**
- ★★ **Rust 는 이 자리를 컴파일에서 막는다** — [Rust 34번](../../../rust/syntax/34-closures-fn-fnmut-fnonce-and-move/) (4) 「**`move` 가 꼭 필요한 것은 수명 때문이다 — 스레드·반환에서 E0373**」. 빌림 검사가 **참조가 캡처 대상보다 오래 사는 것**을 거절한다. C++ 은 **실행 도구(ASan)가 있어야** 본다.

### (2) ★★★ `[=]` 와 `this` — C++20 의 폐기

**언제 쓰나** — 멤버 함수 안에서 `[=]` 를 쓸 때. **`[=]` 는 멤버를 복사하지 않는다 — `this` 포인터를 복사한다.** (1)의 `[this]` 행과 같은 댕글링이 `[=]` 안에 숨는다.

```cpp
/* thiscap.cpp */
// 멤버 함수 안의 람다 — 캡처 목록 세 모양(-DFORM=1..3). 멤버 v 를 읽는다
#include <cstdio>

struct Widget {
    int v = 42;
    int read() {
#if FORM == 1
        auto f = [=] { return v; };
#elif FORM == 2
        auto f = [=, this] { return v; };
#elif FORM == 3
        auto f = [=, *this] { return v; };
#endif
        return f();
    }
};

int main() { std::printf("%d\n", Widget{}.read()); }
```

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

- ★★★ **`[=]` 가 `v` 를 쓰면 C++20 에서만 경고** — g++ `-Wdeprecated` · clang `-Wdeprecated-this-capture`. **C++14·17 에서는 두 컴파일러 다 침묵**한다. 「컴파일러 사이 갈린 행 1 / 9」는 **이 한 행 — 경고 옵션의 이름만** 다르다.
- ★★★ **`[=, this]` 는 C++20 문법** — C++14·17 에서는 **경고(`-Wc++20-extensions`) 한 줄에 `exit 0`**. `[=, *this]` 는 **C++17 문법**이라 C++14 에서만 경고. **두 자리 다 종료 코드 0 인데 그 판으로는 ill-formed**(규칙 19-A).
- ★ **경고도 에러도 없는 칸 10 / 18.**

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

- ★★★ **g++ `implicit capture of ‘this’ via ‘[=]’ is deprecated in C++20` · clang `implicit capture of 'this' with a capture default of '=' is deprecated`** — 둘 다 **고치는 법**을 적는다(g++ `add explicit ‘this’ or ‘*this’ capture` · clang `, this` 를 끼워 넣는 고침 제안).
- ★★ **clang 은 `-Wdeprecated` 를 따로 안 줘도 켜져 있다** — 두 번째 판(`-Wdeprecated` 추가)과 **같은 출력**이다.
- ★★ **폐기 이유를 한 줄로** — `[=]` 는 **「다 복사한다」로 읽히는데 `this` 만은 참조처럼 군다**. (1)의 `[this]` 「돌려준 뒤」 칸이 **그 결과**다.

### (3) ★★ `mutable` — 복사본만 바뀐다

**언제 쓰나** — 람다가 **자기 안의 상태**(호출 횟수 등)를 들고 다녀야 할 때.

```cpp
/* mut01.cpp */
// 값 캡처한 n 을 람다 안에서 올린다 — -DMUT 이면 mutable. 원본 n 과 람다의 복사본을 함께 찍는다
#include <cstdio>

int main() {
    int n = 0;
#ifdef MUT
    auto inc = [n]() mutable { return ++n; };
#else
    auto inc = [n]() { return ++n; };
#endif
    std::printf("call 1 -> %d\n", inc());
    std::printf("call 2 -> %d\n", inc());
    auto copy = inc;
    std::printf("copy   -> %d\n", copy());
    std::printf("inc    -> %d\n", inc());
    std::printf("outer n = %d\n", n);
}
```

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

- ★★★ **`mutable` 없이 값 캡처를 바꾸면 에러** — g++ `increment of read-only variable ‘n’` · clang `cannot assign to a variable captured by copy in a non-mutable lambda`. 람다의 `operator()` 는 기본이 **`const` 멤버 함수**라서다.

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

- ★★★ **`call 1 -> 1` · `call 2 -> 2` · `outer n = 0`** — 바뀌는 것은 **람다 안의 복사본**이다. 원본 `n` 은 끝까지 0.
- ★★★ **`copy -> 3` · `inc -> 3`** — `auto copy = inc;` 가 **그 시점의 상태(2)를 복사**했고, 두 람다는 **따로** 3 이 됐다. **람다를 복사하면 상태도 갈라진다.**

### (4) ★★★ 초기화 캡처로 `unique_ptr` 을 옮기면 — move-only 람다

**언제 쓰나** — 소유권을 **람다에 넘겨** 비동기 작업·콜백에 실을 때(26편의 `unique_ptr`).

```cpp
/* mo01.cpp */
// 초기화 캡처로 unique_ptr 을 옮겨 받은 람다를 담는다 — 기본 std::function, -DMOF 이면 std::move_only_function
#include <cstdio>
#include <functional>
#include <memory>
#include <utility>

int main() {
    auto p = std::make_unique<int>(42);
    auto f = [p = std::move(p)] { return *p; };
#ifdef MOF
    std::move_only_function<int()> g = std::move(f);
#else
    std::function<int()> g = std::move(f);
#endif
    std::printf("%d %d\n", g(), p == nullptr);
}
```

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

- ★★★ **`std::function` 에 담으면 에러** — g++ `static assertion failed: std::function target must be copy-constructible` · clang 은 같은 단언 + **`copy constructor of '(lambda …)' is implicitly deleted because field '' has a deleted copy constructor`** + `'unique_ptr' has been explicitly marked deleted here`.
- ★★★ **이유의 사슬** — `unique_ptr` 복사 금지 → **그것을 멤버로 가진 클로저도 복사 불가** → `std::function` 은 **담은 것을 복사할 수 있어야** 한다(자기 자신이 복사 가능하니까).
- ★★ **clang 이 사슬을 끝까지 말한다** — 필드 이름이 `''`(빈 이름)으로 나오는 것이 **클로저의 멤버에는 이름이 없다**는 흔적이다.

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

- ★★★ **`std::move_only_function`(C++23)이면 통과하고 `42 1`** — `1` 은 **`p == nullptr`** — 원래 `p` 는 **옮겨져 비었다**(09편 — 옮기는 것은 이동 생성자, `std::move` 는 캐스트).
- ★★ **`-std=c++20` 에서는 `move_only_function` 이 없다**(`is not a member of ‘std’`). ★ **두 컴파일러의 C++23 칸은 같은 libstdc++ 13** 이다.

### (5) ★ 제네릭 람다 · 템플릿 람다

**언제 쓰나** — 람다 하나로 **여러 타입**을 받을 때. 템플릿 람다는 **받는 모양을 제한**할 때(`vector<T>` 만).

```cpp
/* gen01.cpp */
// 제네릭 람다(auto) 대 템플릿 람다(C++20 []<typename T>). 템플릿 람다는 vector 만 받는다.
// -DBAD 이면 템플릿 람다에 int 를 넘긴다
#include <cstdio>
#include <vector>

int main() {
    auto twice = [](auto x) { return x + x; };
    auto first = []<typename T>(const std::vector<T>& v) { return v.front(); };
    std::printf("%d %.1f\n", twice(21), twice(1.25));
    std::printf("%d %.1f\n", first(std::vector<int>{7, 8}), first(std::vector<double>{2.5}));
#ifdef BAD
    std::printf("%d\n", first(42));
#endif
}
```

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

- ★★ **`42 2.5` · `7 2.5`** — `twice` 는 `int`·`double` 을, `first` 는 `vector<int>`·`vector<double>` 을 받았다.
- ★★★ **기호표에 `operator()<int>` 와 `operator()<double>` 이 두 벌씩** — **제네릭 람다는 「호출 연산자가 템플릿인 클래스」** 다. `auto` 매개변수는 g++ 이름으로 `auto:1`, 템플릿 람다는 `$T0` 로 보인다(31편의 「인스턴스는 `T` 가 다를 때만」).

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

- ★★ **템플릿 람다에 `int` 는 에러** — g++ `mismatched types ‘const std::vector<T>’ and ‘int’` · clang `could not match 'std::vector<T>' against 'int'`. **`[]<typename T>(const std::vector<T>&)` 는 `vector` 가 아니면 추론이 실패**한다 — `auto` 로는 이 제한을 적을 수 없다.

### (6) ★ 람다 타입은 고유하다 — 크기가 캡처를 말한다

```cpp
/* type01.cpp */
// 람다 타입은 고유한가 — 글자가 같은 두 람다 · 캡처에 따른 크기 · 캡처 없는 람다의 함수 포인터 변환
#include <cstdio>
#include <type_traits>

int main() {
    int x = 1;
    double d = 2.0;
    auto a = [] { return 1; };
    auto b = [] { return 1; };
    auto c = [x] { return x; };
    auto e = [&x] { return x; };
    auto g = [x, d] { return x + d; };
    auto h = [&x, &d] { return x + d; };
    std::printf("same type a b     = %d\n", std::is_same_v<decltype(a), decltype(b)>);
    std::printf("sizeof []         = %zu\n", sizeof(a));
    std::printf("sizeof [x]        = %zu\n", sizeof(c));
    std::printf("sizeof [&x]       = %zu\n", sizeof(e));
    std::printf("sizeof [x, d]     = %zu\n", sizeof(g));
    std::printf("sizeof [&x, &d]   = %zu\n", sizeof(h));
    int (*fp)() = a;
    std::printf("fp()              = %d\n", fp());
}
```

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

- ★★★ **글자가 같은 두 람다 `a`·`b` 도 `same type = 0`** — 람다 식 하나마다 **이름 없는 새 클래스**가 생긴다(cppreference 「**unique unnamed … class type**」).
- ★★ **`sizeof` — `[]` 1 · `[x]` 4 · `[&x]` 8 · `[x, d]` 16 · `[&x, &d]` 16** — 캡처가 **멤버**가 된다. 참조 캡처가 8 인 것은 **이 판이 주소 하나로 구현한 관찰**이다(표준은 참조 캡처의 저장 방식을 정하지 않는다).
- ★★ **캡처 없는 람다는 함수 포인터로 바뀐다**(`fp() = 1`) — 캡처가 있으면 안 된다(상태를 둘 곳이 없다).

## 문법 — 형태와 규칙

### 형태

```text
   [x]              값 캡처 — 만든 때의 복사본                 [&x]        참조 캡처 — 부른 때의 원본
   [=]              쓰는 것을 전부 값으로 · ★ this 는 암묵 참조(C++20 폐기)
   [&]              쓰는 것을 전부 참조로
   [this]           객체를 가리키는 포인터                     [*this]     객체를 통째로 복사 (C++17)
   [=, this]        C++20 — this 를 명시                       [p = std::move(p)]  초기화 캡처 (C++14)
   [n]() mutable { ++n; }     복사본을 고친다
   [](auto x) { … }           제네릭 람다 (C++14)              []<typename T>(std::vector<T> v) { … }  템플릿 람다 (C++20)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(6)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **참조로 잡는 것(`[&x]`·`[&]`·`[this]`·`[=]` 안의 `this`)은 대상보다 오래 살면 댕글링** — 경고는 12 칸 중 2 칸만 잡았다((1)).
- ★★★ **값 캡처는 만든 때, 참조 캡처는 부른 때의 값**((1)의 즉시 행).
- ★★★ **C++20 에서 `[=]` 의 `this` 암묵 캡처는 폐기** — `[=, this]` 또는 `[*this]` 로 적는다((2)).
- ★★ **값 캡처를 고치려면 `mutable` — 고쳐지는 것은 복사본**((3)).
- ★★★ **move-only 멤버를 잡은 람다는 move-only — `std::function` 불가, `std::move_only_function`(C++23) 가능**((4)).
- ★ **람다 식마다 타입이 새로 생긴다 · 캡처 없는 람다만 함수 포인터로**((6)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `[n]() { ++n; }` | `increment of read-only variable ‘n’` | `cannot assign to a variable captured by copy in a non-mutable lambda` | (3) |
| move-only 람다를 `std::function` 에 | `std::function target must be copy-constructible` | 같은 단언 + `implicitly deleted` | (4) |
| `-std=c++20` 에서 `std::move_only_function` | `‘move_only_function’ is not a member of ‘std’` | `no member named 'move_only_function'` | (4) |
| 템플릿 람다 `vector<T>` 에 `int` | `mismatched types ‘const std::vector<T>’ and ‘int’` | `could not match 'std::vector<T>' against 'int'` | (5) |
| C++20 에서 `[=]` 가 멤버를 씀 | 경고 `-Wdeprecated` | 경고 `-Wdeprecated-this-capture` | (2) |

## 어디서 틀리나

### 1. ★★★ 「`[=]` 는 전부 복사하니 안전하다」

(2)가 반증이다 — **`this` 는 포인터로** 잡힌다. (1)의 `[this]` 행과 같은 댕글링이 숨는다. C++20 이 폐기 경고를 내는 이유다.

### 2. ★★★ 「참조 캡처 댕글링은 경고가 잡아 준다」

(1)이 반증이다 — **12 칸 중 경고 2 칸**(clang 의 `[&x]`·`[&]` 반환). `[this]` 반환 · 블록 밖 · g++ 전부는 **경고 0 · 실행만** 잡았다.

### 3. ★★★ 「ASan 이면 댕글링 캡처를 다 잡는다」

(1)이 반증이다 — **`detect_stack_use_after_return=0` 이면 「돌려준 뒤」 여섯 칸이 사라진다.** 이 판에서는 기본으로 켜져 있었을 뿐이다.

### 4. ★★ 「`mutable` 이면 바깥 변수가 바뀐다」

(3)이 반증이다 — **`outer n = 0`.** 복사본만 바뀌고, 람다를 복사하면 상태도 갈라진다.

### 5. ★★★ 「초기화 캡처 람다도 `std::function` 에 담으면 된다」

(4)가 반증이다 — **move-only 라 에러.** C++23 `std::move_only_function`.

### 6. ★ 「글자가 같은 람다는 같은 타입이다」

(6)이 반증이다 — **`same type = 0`.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 사고는 UB 층에 산다** — 캡처 규칙은 표준이 정하지만, **대상이 죽은 뒤의 읽기는 UB** 라 **도구 없이는 아무것도 말할 수 없다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **값 캡처는 복사 · 참조 캡처는 참조** · **`operator()` 는 기본 `const`** · **클로저 타입은 고유** · **move-only 멤버면 복사 불가** | 두 컴파일러 · cppreference | — |
| **조건부 표준** | 특정 판에서만 | ★★★ **`[*this]` C++17 · `[=, this]`·템플릿 람다 C++20 · `[=]` 의 `this` 폐기 C++20 · `move_only_function` C++23** | `this` 격자 · `-std=c++20` 대 `c++23` | — |
| **구현 정의 · ABI** | 문서화 의무 | ★★ **클로저의 `sizeof`**((6)) · **기호 이름 `auto:1`·`$T0`**((5)) | `sizeof` · `nm -C` | ★ 참조 캡처가 **포인터 하나**라는 것은 이 판의 관찰 |
| **컴파일러의 것** | 표준 밖 | ★★★ **경고가 잡는 칸**(clang 만 `[&x]` 반환) · 경고 옵션 이름 · **`-Wc++20-extensions` 로 받아 주는 확장** | 두 격자 | ★★ **경고 0 은 안전이 아니다**((1) 10 / 12 칸) |
| **UB** | 아무 일이나 | ★★★ **댕글링 캡처 12 칸** — **값을 싣지 않았다** | ASan 세 번(기본 · uar=1 · uar=0) | ★★★ **ASan 은 스택·힙 메모리만 본다** — `uar=0` 이면 돌아간 프레임을 못 본다 · **`-O2` 판은 던지지 않았다**(30편 (1)이 clang `-O2` 에서 스택 탐침 다섯을 놓쳤다) |

### ★★ 종료 코드 0인데 ill-formed — 이 편에서 두 자리

- ★★★ **`-std=c++14`·`c++17` 의 `[=, this]`** · **`-std=c++14` 의 `[=, *this]`** — 경고 한 줄 · `cc exit=0`((2)의 격자).

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 람다가 만든 자리 안에서만 불린다 | ★★ **`[&]` 도 된다** | (1) 즉시 행 — 댕글링 없음 |
| 람다를 돌려주거나 저장한다 | ★★★ **값 캡처 · 필요한 것만 이름으로 `[x]`** | (1) — 참조 캡처는 댕글링 |
| 멤버 함수에서 객체가 먼저 죽을 수 있다 | ★★★ **`[*this]`**(복사) — 아니면 `shared_ptr` 을 초기화 캡처로 | (1)(2) |
| 멤버 함수에서 `[=]` | ★★ **`[=, this]` 로 명시**(C++20) | (2) — 폐기 경고 |
| 람다에 상태 | ★★ **`mutable` + 값 캡처** — 복사하면 갈라진다 | (3) |
| 소유권을 람다에 넘긴다 | ★★★ **`[p = std::move(p)]` + `std::move_only_function`(C++23)** 또는 템플릿 매개변수로 받기 | (4) |
| 여러 타입 | ★ **`auto` 매개변수** · 모양 제한은 **템플릿 람다** 또는 컨셉 `std::integral auto` | (5) · 36편 |

## 핵심 문장

- ★★★ **캡처 일곱 × 때 셋에서 댕글링 12 / 40 — 전부 참조로 잡는 셋(`[&x]`·`[&]`·`[this]`)의 「돌려준 뒤」·「스코프 밖」** · 이름은 `use-after-return` 대 `use-after-scope`.
- ★★★ **`detect_stack_use_after_return` 은 이 판의 기본값이 켜짐(기본과 `=1` 이 다른 칸 0) — 끄면 `use-after-return` 여섯 칸이 전부 사라진다.**
- ★★★ **경고가 잡은 댕글링은 12 칸 중 2 칸(clang)** — 나머지는 실행만 잡았다.
- ★★★ **`[=]` 의 `this` 는 포인터 — C++20 이 폐기 경고를 낸다**(C++14·17 은 침묵).
- ★★★ **`unique_ptr` 을 옮겨 잡은 람다는 move-only — `std::function` 은 에러, C++23 `std::move_only_function` 은 `42 1`.**
- ★★ **`mutable` 은 복사본을 고친다 — 원본은 0, 람다를 복사하면 상태도 갈라진다.**

## 관련 자료

- [30번](../30-dangling-references-and-lifetime-extension/) (1)(2) — ★★★ **댕글링 일곱 모양 × 도구 여섯 · `detect_stack_use_after_return`** — 여기의 격자는 그 탐침 5 를 **캡처 일곱 × 때 셋**으로 넓힌 것이다.
- [09번](../09-rvalue-references-move-and-forward/) — ★★ **`std::move` 는 캐스트** — (4)의 `p == nullptr` 이 옮긴 흔적이다.
- [26번](../26-unique-ptr-and-ownership-transfer/) — `unique_ptr` 의 복사 금지 — (4)의 사슬 첫 고리.
- [36번](../36-concepts-and-requires/) — ★ `std::integral auto` 매개변수 — (5)의 제네릭 람다에 **제약**을 거는 법.
- 목록의 **40번 주제** — `std::function` 의 타입 소거와 비용(여기는 **담을 수 있나**만 봤다).
- C# 갈래 [28번](../../../csharp/syntax/28-lambdas-and-closure-capture/) — ★★★ **변수 자체를 캡처해 힙 클래스로 옮긴다 · `for` 는 `3 3 3`** — C++ 의 `[&i]` 는 옮기지 않아 **죽은 변수**를 읽는다((1)의 `loop01`).
- Rust 갈래 [34번](../../../rust/syntax/34-closures-fn-fnmut-fnonce-and-move/) — ★★ **`move` 가 필요한 것은 수명 때문 — E0373** · 클로저 크기가 캡처를 말한다((6)과 같은 관찰).

## 용어 풀이

> **클로저(closure) · 클로저 타입** — 람다 식이 만드는 객체와 그 타입. 캡처가 **멤버**가 되고, 몸통이 **`operator()`** 가 된다. 람다 식마다 타입이 새로 생긴다.\
> 예: (6)의 `same type = 0`.

> **값 캡처 / 참조 캡처** — 만든 때 복사해 담는 것 / 원본을 가리키는 것.\
> 예: (1)의 즉시 행 42 대 7.

> **초기화 캡처(init-capture)** — `[이름 = 식]`. 캡처 멤버를 **임의의 식으로 초기화**한다. 이동으로 소유권을 넘길 때 쓴다.\
> 예: (4)의 `[p = std::move(p)]`.

> **`stack-use-after-return` / `stack-use-after-scope`** — ASan 리포트. 앞은 **돌아간 함수의 스택**을, 뒤는 **끝난 블록의 지역**을 읽은 것. 앞은 `detect_stack_use_after_return` 이 켜져 있어야 보인다.\
> 예: (1)의 격자.

> **move-only** — 이동은 되고 복사는 안 되는 타입. `unique_ptr` 과 그것을 멤버로 가진 클로저.\
> 예: (4).

> **제네릭 람다 · 템플릿 람다** — `auto` 매개변수 람다(C++14) · `[]<typename T>` 로 템플릿 매개변수를 이름 붙인 람다(C++20). 둘 다 **`operator()` 가 템플릿**이다.\
> 예: (5)의 `nm -C`.

## 더 들어가면

- **`-O2` 의 캡처 격자** — 30편 (1)이 **clang `-O2` + ASan 이 스택 탐침 다섯을 놓쳤다**고 보였다. 이 편은 `-O0` 만 던졌다 — 같은 모양이 나올지는 **던지지 않았다.**
- **람다의 인라인** — 「람다는 인라인된다」는 **역어셈블로 확인하지 않았다.** 확인하려면 `-O2` 의 `objdump -d` 에서 `operator()` 호출이 사라졌는지 봐야 한다.
- **`std::function` 의 할당과 크기** — 목록의 **40번 주제**.
- **구조적 바인딩을 캡처하기(C++20)** — 이 편은 던지지 않았다.
