# cpp/syntax/34 — 가변 인자 템플릿과 팩 확장 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 폴드 식](https://en.cppreference.com/w/cpp/language/fold) · [cppreference — 파라미터 팩](https://en.cppreference.com/w/cpp/language/parameter_pack)\
> ★ 이 배치에서 **폴드 식 쪽만 열어 확인했다** — 「네 꼴의 전개(단항 우 `(E op ...)` → `(E1 op (... op (EN-1 op EN)))` 등)」 · 「**빈 팩의 단항 폴드는 `&&`(→ `true`) · `||`(→ `false`) · `,`(→ `void()`) 만 된다**」 두 문장이다. 파라미터 팩 쪽은 **열지 않았다** — 팩 확장 규칙은 **두 컴파일러의 실행 출력**으로만 적었다.
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++17 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`pack01.cpp` \~ `pack05.cpp` · `fold-grid.sh`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.
> **버전** — 가변 인자 템플릿·파라미터 팩·`sizeof...`·`std::forward` 는 **C++11부터**, **폴드 식은 C++17부터**다. 기준은 **C++17**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[09번](../09-rvalue-references-move-and-forward/)·[31번](../31-function-templates-and-argument-deduction/)에서 온다 — 앞 편들이 잰 것은 다시 재지 않고 인용한다.**\
> [09번](../09-rvalue-references-move-and-forward/) (3) — **복사와 이동을 로그로 센다**(`Noisy`) · (6) — **`T&&` 에 lvalue 면 `T = int&`, prvalue·xvalue 면 `T = int`** · **이름이 있는 `x` 는 언제나 lvalue — 그래서 `forward` 를 한 번 더 써야 한다.**\
> [31번](../31-function-templates-and-argument-deduction/) (2) — **`T&&` 열은 인자마다 `T` 가 참조가 된다** · (5) — **`T` 가 같으면 인스턴스는 하나.**\
> ★★ **여기서 새로 묻는 것은 넷이다** — **폴드 식 격자(연산자 5 × 꼴 4 × 팩 2 × 컴파일러 2)** · **완벽 전달 팩토리를 `forward` 있고/없고로** · **`...` 을 붙이는 자리** · **팩이 타입을 보존한다는 것(C `stdarg` 대비).**
> **경계** — 「`std::forward` 가 무엇을 하는 캐스트인가」는 [09번](../09-rvalue-references-move-and-forward/)이, 「C 의 `...`」은 C 갈래 [36번](../../../c/syntax/36-variadic-functions-stdarg/)이, 「팩을 컨셉으로 제약하기」는 목록의 **36번 주제**가 정본이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단의 **문구** · g++ 가 진단 위치를 **`<command-line>`** 으로 적는 것((2) 빈 팩 — 식을 `-D` 로 넣었기 때문) | ★★★ **격자 칸의 값·`error`·`void`** · **「갈린 칸 N / M」** · **`cc exit`** |
> | ★★★ **(4)의 `g(1)` · `g(2)` · `g(3)` 이 찍히는 순서** — g++ 는 3·2·1, clang 은 1·2·3 — **미명시**다 | ★★★ **복사·이동 로그의 종류와 개수**((3)) · **`f got N args`** · **타입 이름**(`char` · `short` · `float` · `bool`) |

## 한눈에 — 쉽게 말하면

**파라미터 팩은 「이름표가 붙은 채로 한 줄로 선 손님들」이다.**

C 의 `...`(C 갈래 36편)은 손님들을 **이름표 없이 한 방에** 몰아넣는다 — 꺼내는 쪽이 「이건 `int` 겠지」 하고 **짐작**해야 하고, `char`·`float` 는 들어가면서 **옷이 바뀐다**(승격).\
C++ 의 팩은 손님마다 **타입 이름표**가 붙어 있다 — `char` 는 `char` 로, `float` 는 `float` 로 **끝까지** 간다((5)).

- **`sizeof...(Ts)`** — 줄에 **몇 명** 섰나((1)).
- **`f(args...)`** — 줄을 **그대로** 다음 방에 넘긴다 · **`f(g(args)...)`** — **한 명씩** `g` 를 거쳐 넘긴다((4)).
- **폴드 식** — 줄 선 손님들을 **연산자 하나로 이어 붙인다**. **어느 쪽 끝부터 붙이나**가 `-` 에서 답을 바꾼다((2)).
- **`std::forward<Args>(args)...`** — 손님이 **데려온 짐(lvalue/rvalue)** 까지 그대로 넘긴다. 빼먹으면 **전부 복사**가 된다((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 이름표 붙은 줄 | ★★★ **파라미터 팩 `Ts... xs`** — 원소마다 타입이 남는다 | (5) |
| 몇 명 섰나 | ★★ **`sizeof...(Ts)`** | (1) |
| 한 명씩 벗겨 내기 | ★★ **재귀 풀기**(`first, rest...`) | (1) |
| 연산자로 이어 붙이기 | ★★★ **폴드 식 네 꼴** | (2) |
| 아무도 없는 줄 | ★★★ **빈 팩 — 단항 폴드는 `&&`·`\|\|`·`,` 만** | (2) |
| 짐까지 그대로 | ★★★ **`std::forward<Args>(args)...`** | (3) |
| 한 명씩 거치나, 통째로 거치나 | ★★ **`f(g(args)...)` 대 `f(g(args...))`** | (4) |

```text
   (... - xs)   단항 좌    ((10 - 3) - 2)       =  5
   (xs - ...)   단항 우    (10 - (3 - 2))       =  9
   (I - ... - xs) 이항 좌  (((0 - 10) - 3) - 2) = -15
   (xs - ... - I) 이항 우  (10 - (3 - (2 - 0))) =  9
   ★ 점 셋이 왼쪽에 있으면 왼쪽부터 묶는다
```

## 이 주제가 답하려는 질문

1. ★★★ **폴드 식의 네 꼴은 어떻게 묶이나 — 빈 팩이면 무엇이 되나**((2)).
2. ★★★ **팩을 받아 그대로 넘기는 팩토리에서 `forward` 를 빼면 무엇이 달라지나**((3)).
3. ★★ **`...` 을 어디에 붙이느냐로 무엇이 달라지나**((4)).
4. ★★ **팩과 C 의 `...` 은 무엇이 다른가**((5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러 격자와 복사·이동 로그다

★★★ **이 주제의 본체는 ② 두 컴파일러 대조다** — 폴드 식은 **칸마다 따로 컴파일**해 값 또는 `error` 를 받는다(빈 팩의 `+` 는 컴파일이 안 되므로 한 파일에 못 담는다).\
★★ **짝이 실행 로그다** — 복사·이동이 일어났는지는 **생성자에 심은 `printf`** 로 센다(09편 (3)의 방법).\
★★★ **그리고 이 편에서 처음 나온 칸 — 두 컴파일러가 「다르게」 낸 칸**이 (4)에 있다. 규칙이 **정하지 않은** 자리다(미명시).

```text
① 다섯 층 표            폴드 규칙은 표준 · 함수 인자 평가 순서는 미명시               (구현 세부사항 절)
② ★ 두 컴파일러 대조     연산자 5 × 꼴 4 × 팩 2 = 40칸 × 컴파일러 2                   (2)
③ ASan                   —                                                          부적용
④ 어셈블리              —                                                          부적용 — 로그로 바꿨다
⑤ 경고 격자             —                                                          부적용
⑥ ★ 실행 로그            copy/move 로그 · g(1)(2)(3) 순서 · 원소마다 타입 이름         (3)(4)(5)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★★ **폴드·전달 규칙은 표준, `f(g(args)...)` 의 평가 순서는 미명시** | **쓴다** |
| ★★★ **② 두 컴파일러 대조** | ★★★ **본체** — 40칸 × 2 에서 **갈린 칸 0 / 40** · **좌 대 우가 갈린 짝 3 / 10** · **error 4 / 40** | **쓴다** |
| ③ ASan | ★ **부적용** — 팩 확장은 **컴파일 때 끝난다**(18-B). 로그의 대상 객체도 스택의 `int` 하나짜리다 | **안 쓴다** |
| ④ 어셈블리 | ★ **부적용** — 「복사가 났나」는 기계어보다 **생성자 로그**가 직접 답한다(제5의 상태 — 09편 (3)과 같은 바꾼 창) | **안 쓴다(바꿔서)** |
| ⑤ 경고 격자 | ★ **부적용** — 격자 스크립트는 진단을 **보지 않는다**(`2>/dev/null` — 칸에는 값·`void`·`error` 만). `-std=c++17` 로 통과한 단독 블록은 **경고 0** 이었다(C++14 판은 종료 코드 0 절) | **안 쓴다** |
| ★★★ **⑥ 실행 로그** | ★★★ **copy 대 move** · **`g` 가 불린 순서** · **`__cxa_demangle` 로 푼 원소 타입** | **쓴다** |

### (1) ★★ 팩을 푸는 두 방법 — 재귀 대 폴드, 그리고 `sizeof...`

**언제 쓰나** — 가변 인자 템플릿을 처음 쓸 때. **C++11 코드는 재귀, C++17 코드는 폴드**로 읽힌다.

```cpp
/* pack02.cpp */
// 같은 합을 두 방법으로 — 재귀로 한 겹씩 벗기기(C++11) 대 폴드 식(C++17). 그리고 sizeof...
#include <cstdio>

long sum_rec() { return 0; }
template <class T, class... Rest> long sum_rec(T first, Rest... rest) {
    std::printf("  sum_rec: first=%ld, sizeof...(rest)=%zu\n", (long)first, sizeof...(rest));
    return first + sum_rec(rest...);
}

template <class... Ts> long sum_fold(Ts... xs) {
    std::printf("  sum_fold: sizeof...(Ts)=%zu\n", sizeof...(Ts));
    return (0 + ... + xs);
}

int main() {
    std::printf("sum_rec(1, 2, 3) = %ld\n", sum_rec(1, 2, 3));
    std::printf("sum_fold(1, 2, 3) = %ld\n", sum_fold(1, 2, 3));
    std::printf("sum_fold() = %ld\n", sum_fold());
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
```

- ★★ **재귀는 한 겹씩 벗긴다** — `sizeof...(rest)` 가 **2 → 1 → 0** 으로 줄고, 0 이 되면 **비템플릿 `sum_rec()`** 가 끝을 받는다. **끝을 받을 함수를 따로 써야** 하는 것이 재귀 풀기의 비용이다.
- ★★ **폴드는 한 번에 접는다** — `sizeof...(Ts)=3` 을 한 번 찍고 끝. **빈 팩도** `sum_fold()` = 0 — 이항 폴드 `(0 + ... + xs)` 의 **`0` 이 빈 팩의 답**이 된다((2)).
- ★ **`sizeof...` 은 팩의 원소 수**다 — 값을 보지 않고 **개수만** 센다(컴파일 때 정해진다).

### (2) ★★★ 폴드 식 격자 — 연산자 5 × 꼴 4 × 팩 2 × 컴파일러 2

**언제 쓰나** — 폴드 식을 쓸 때마다 「점 셋을 어느 쪽에 둘까」 · 「빈 팩이 올 수 있나」.

```cpp
/* pack01.cpp */
// 폴드 식 한 칸 — 식은 -DFOLD=… , 넘기는 팩은 -DPACK=… 로 고른다. init 자리는 I
#include <cstdio>
#include <type_traits>

template <class... Ts> auto cell(Ts... xs) {
    constexpr auto I = INIT;
    (void)I;
    return FOLD;
}

template <class F> void run(F f) {
    if constexpr (std::is_void_v<decltype(f())>) {
        f();
        std::puts("void");
    } else {
        std::printf("%lld\n", (long long)f());
    }
}

int main() {
    run([] { return cell(PACK); });
}
```

```bash
# fold-grid.sh
# fold-grid.sh — 연산자 다섯 × 폴드 꼴 넷 × 팩 둘(빈 팩 · 10,3,2) × 컴파일러 둘. 칸마다 값 또는 error
ops=('+' '-' ',' '&&' '||')
inits=('0' '0' '0' 'true' 'false')
forms=('(... OP xs)' '(xs OP ...)' '(I OP ... OP xs)' '(xs OP ... OP I)')
names=('단항 좌' '단항 우' '이항 좌' '이항 우')
cell() {  # $1 컴파일러 $2 식 $3 init $4 팩
  if $1 -std=c++17 -Wall -Wextra -pedantic "-DFOLD=$2" "-DINIT=$3" "-DPACK=$4" pack01.cpp -o gx 2>/dev/null; then ./gx; else echo error; fi
}
printf '%s\t%s\t%s\t%s\t%s\t%s\n' "연산자" "꼴" "g++ 빈 팩" "g++ 10,3,2" "clang++ 빈 팩" "clang++ 10,3,2" > grid.tsv
for k in 0 1 2 3 4; do for j in 0 1 2 3; do
  op="${ops[$k]}"; e="${forms[$j]//OP/"$op"}"
  row="$op"$'\t'"${names[$j]} $e"
  for c in g++ clang++; do for p in '' '10, 3, 2'; do row="$row"$'\t'"$(cell $c "$e" "${inits[$k]}" "$p")"; done; done
  printf '%s\n' "$row" >> grid.tsv
done; done
cat grid.tsv
bad=$(awk -F'\t' 'NF != 6' grid.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < grid.tsv) - 1 ))
cc_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($3 != $5) + ($4 != $6) } END { print n }')
lr_split=$(tail -n +2 grid.tsv | awk -F'\t' '{ v[NR] = $4 } END { for (i = 1; i <= NR; i += 2) n += (v[i] != v[i+1]); print n }')
errs=$(tail -n +2 grid.tsv | awk -F'\t' '{ n += ($3 == "error") + ($4 == "error") } END { print n }')
echo "g++ 대 clang++ 가 갈린 칸 $cc_split / $((rows * 2)) · 좌 대 우가 갈린 짝(10,3,2) $lr_split / $((rows / 2)) · error 칸(g++) $errs / $((rows * 2))"
rm -f gx grid.tsv
```

```text
===== bash fold-grid.sh (exit=0) =====
연산자	꼴	g++ 빈 팩	g++ 10,3,2	clang++ 빈 팩	clang++ 10,3,2
+	단항 좌 (... + xs)	error	15	error	15
+	단항 우 (xs + ...)	error	15	error	15
+	이항 좌 (I + ... + xs)	0	15	0	15
+	이항 우 (xs + ... + I)	0	15	0	15
-	단항 좌 (... - xs)	error	5	error	5
-	단항 우 (xs - ...)	error	9	error	9
-	이항 좌 (I - ... - xs)	0	-15	0	-15
-	이항 우 (xs - ... - I)	0	9	0	9
,	단항 좌 (... , xs)	void	2	void	2
,	단항 우 (xs , ...)	void	2	void	2
,	이항 좌 (I , ... , xs)	0	2	0	2
,	이항 우 (xs , ... , I)	0	0	0	0
&&	단항 좌 (... && xs)	1	1	1	1
&&	단항 우 (xs && ...)	1	1	1	1
&&	이항 좌 (I && ... && xs)	1	1	1	1
&&	이항 우 (xs && ... && I)	1	1	1	1
||	단항 좌 (... || xs)	0	1	0	1
||	단항 우 (xs || ...)	0	1	0	1
||	이항 좌 (I || ... || xs)	0	1	0	1
||	이항 우 (xs || ... || I)	0	1	0	1
g++ 대 clang++ 가 갈린 칸 0 / 40 · 좌 대 우가 갈린 짝(10,3,2) 3 / 10 · error 칸(g++) 4 / 40
```

- ★★★ **g++ 대 clang++ 가 갈린 칸 0 / 40** — 폴드는 **표준이 전개를 정한다.**
- ★★★ **좌 대 우가 갈린 짝 3 / 10** — **`-` 의 단항(5 대 9) · `-` 의 이항(-15 대 9) · `,` 의 이항(2 대 0)** 셋. `+`·`&&`·`||` 는 **결합 방향이 답을 안 바꾼다**(결합 법칙이 성립한다).\
  ★ **`,` 이항이 갈린 이유** — `(I , ... , xs)` 는 `((I, 10), 3), 2` 라 **마지막이 `2`**, `(xs , ... , I)` 는 `10, (3, (2, I))` 라 **마지막이 `I` = 0**. 쉼표 연산자는 **오른쪽 끝 값**을 돌려준다.
- ★★★ **빈 팩의 단항 폴드 — `+`·`-` 는 `error`, `,` 는 `void`, `&&` 는 `1`(true), `||` 는 `0`(false)** — error 4칸이 전부 **빈 팩 × 단항 × `+`/`-`** 다. cppreference 의 세 연산자·세 값과 **정확히 같다.**
- ★★ **이항 폴드는 빈 팩에서 `I` 를 돌려준다** — `+`·`-`·`,` 는 `0`, `&&` 는 `true`, `||` 는 `false` — **`I` 가 곧 빈 팩의 답**이다.

**빈 팩에 `(... + xs)` 를 던지면** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic '-DFOLD=(... + xs)' -DINIT=0 -DPACK= pack01.cpp -o ex (cc exit=1) =====
pack01.cpp: In instantiation of ‘auto cell(Ts ...) [with Ts = {}]’:
pack01.cpp:21:25:   required from here
<command-line>: error: fold of empty expansion over operator+
pack01.cpp:8:12: note: in expansion of macro ‘FOLD’
    8 |     return FOLD;
      |            ^~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic '-DFOLD=(... + xs)' -DINIT=0 -DPACK= pack01.cpp -o ex (cc exit=1) =====
pack01.cpp:8:12: error: unary fold expression has empty expansion for operator '+' with no fallback value
    8 |     return FOLD;
      |            ^
<command line>:1:15: note: expanded from macro 'FOLD'
    1 | #define FOLD (... + xs)
      |               ^
pack01.cpp:21:21: note: in instantiation of function template specialization 'cell<>' requested here
   21 |     run([] { return cell(PACK); });
      |                     ^
1 error generated.
```

- ★★★ **g++ `fold of empty expansion over operator+` · clang `unary fold expression has empty expansion for operator '+' with no fallback value`** — clang 문구가 처방을 말한다: **「fallback value」 = 이항 폴드의 `I`.**
- ★ g++ 가 진단 위치를 **`<command-line>`** 으로 적은 것은 **식을 `-DFOLD=` 로 넣었기 때문**이다(흔들리는 칸). **`Ts = {}`**(빈 팩)과 **`required from here`**(21행)가 근거다.

```text
   빈 팩 × 단항 폴드            빈 팩 × 이항 폴드
   (... + xs)   error          (I + ... + xs)   I
   (... - xs)   error          (I - ... - xs)   I
   (... , xs)   void()         (I , ... , xs)   I
   (... && xs)  true           (I && ... && xs) I
   (... || xs)  false          (I || ... || xs) I
   ★ 항등원이 뻔한 셋만 표준이 값을 정했다 — + 의 0 은 정해 주지 않는다
```

### (3) ★★★ 완벽 전달 팩토리 — `forward` 있고 / 없고

**언제 쓰나** — `make_unique`·`emplace_back` 처럼 **받은 인자로 다른 객체를 만드는** 함수를 쓸 때.

```cpp
/* pack03.cpp */
// 팩을 받아 T 를 만드는 팩토리 — forward 를 쓴 판과 안 쓴 판. 복사·이동을 로그로 센다
#include <cstdio>
#include <utility>

struct Noisy {
    int id;
    explicit Noisy(int i) : id(i) {}
    Noisy(const Noisy& o) : id(o.id) { std::printf("    copy(%d)\n", id); }
    Noisy(Noisy&& o) noexcept : id(o.id) { std::printf("    move(%d)\n", id); }
};

struct Duo {
    Noisy a;
    Noisy b;
    Duo(const Noisy& x, const Noisy& y) : a(x), b(y) { std::puts("    Duo(const&, const&)"); }
    Duo(Noisy&& x, Noisy&& y) : a(std::move(x)), b(std::move(y)) { std::puts("    Duo(&&, &&)"); }
    Duo(const Noisy& x, Noisy&& y) : a(x), b(std::move(y)) { std::puts("    Duo(const&, &&)"); }
};

template <class T, class... Args> T make_fwd(Args&&... args) {
    return T(std::forward<Args>(args)...);
}

template <class T, class... Args> T make_plain(Args&&... args) {
    return T(args...);
}

int main() {
    Noisy n1(1), n2(2);
    std::puts("[1] make_fwd<Duo>(n1, n2)");
    { Duo d = make_fwd<Duo>(n1, n2); (void)d; }
    std::puts("[2] make_fwd<Duo>(Noisy(3), Noisy(4))");
    { Duo d = make_fwd<Duo>(Noisy(3), Noisy(4)); (void)d; }
    std::puts("[3] make_fwd<Duo>(n1, Noisy(5))");
    { Duo d = make_fwd<Duo>(n1, Noisy(5)); (void)d; }
    std::puts("[4] make_plain<Duo>(n1, n2)");
    { Duo d = make_plain<Duo>(n1, n2); (void)d; }
    std::puts("[5] make_plain<Duo>(Noisy(3), Noisy(4))");
    { Duo d = make_plain<Duo>(Noisy(3), Noisy(4)); (void)d; }
    std::puts("[6] make_plain<Duo>(n1, Noisy(5))");
    { Duo d = make_plain<Duo>(n1, Noisy(5)); (void)d; }
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] make_fwd<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[2] make_fwd<Duo>(Noisy(3), Noisy(4))
    move(3)
    move(4)
    Duo(&&, &&)
[3] make_fwd<Duo>(n1, Noisy(5))
    copy(1)
    move(5)
    Duo(const&, &&)
[4] make_plain<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[5] make_plain<Duo>(Noisy(3), Noisy(4))
    copy(3)
    copy(4)
    Duo(const&, const&)
[6] make_plain<Duo>(n1, Noisy(5))
    copy(1)
    copy(5)
    Duo(const&, const&)
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] make_fwd<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[2] make_fwd<Duo>(Noisy(3), Noisy(4))
    move(3)
    move(4)
    Duo(&&, &&)
[3] make_fwd<Duo>(n1, Noisy(5))
    copy(1)
    move(5)
    Duo(const&, &&)
[4] make_plain<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[5] make_plain<Duo>(Noisy(3), Noisy(4))
    copy(3)
    copy(4)
    Duo(const&, const&)
[6] make_plain<Duo>(n1, Noisy(5))
    copy(1)
    copy(5)
    Duo(const&, const&)
```

- ★★★ **`forward` 가 있으면 인자마다 따로 간다** — `[1]` lvalue 둘 → **copy · copy** · `[2]` 임시 둘 → **move · move** · `[3]` lvalue 하나 + 임시 하나 → **copy · move**(생성자도 `Duo(const&, &&)`).
- ★★★ **`forward` 를 빼면 전부 copy** — `[5]` 에서 임시 `Noisy(3)`·`Noisy(4)` 를 넘겼는데 **copy · copy** 에 `Duo(const&, const&)`. **`args` 는 이름이 있어 lvalue** 이기 때문이다(09편 (6)의 「`x` 는 언제나 lvalue」 — 팩이어도 같다).
- ★★ **두 컴파일러 로그가 한 글자도 같다** — 호출 수와 종류는 **표준이 정하는 것**이다(★ `Duo` 가 반환하면서 복사·이동됐다면 멤버 `Noisy` 의 copy/move 가 **두 줄 더** 찍혔을 텐데 **한 줄도 없다** — C++17 의 반환값 복사 생략).
- ★ **`std::forward<Args>(args)...` 는 원소마다 자기 `Args` 로 캐스트**한다 — `[3]` 에서 첫째는 `Args = Noisy&`(→ lvalue), 둘째는 `Args = Noisy`(→ rvalue). 31편 (2)의 `T&&` 열과 **같은 추론을 원소마다** 한 것이다.

```text
                          [1] n1, n2      [2] Noisy(3), Noisy(4)   [3] n1, Noisy(5)
   make_fwd  (forward)    copy copy       ★ move move              copy move
   make_plain(그냥 args)   copy copy       ★ copy copy              copy copy
   ★ 차이는 rvalue 로 넘긴 칸에서만 난다 — lvalue 칸은 둘이 같다
```

### (4) ★★ `...` 을 붙이는 자리 — 그리고 두 컴파일러가 갈린 칸

**언제 쓰나** — 팩을 함수에 넘기면서 **원소마다** 무엇을 하고 싶을 때.

```cpp
/* pack04.cpp */
// ... 을 어디에 붙이나 — 같은 팩, 두 자리
#include <cstdio>

int g(int x) {
    std::printf("  g(%d)\n", x);
    return x * 10;
}
template <class... Ts> int g(Ts... xs) {
    std::printf("  g(pack of %zu)\n", sizeof...(xs));
    return (0 + ... + xs);
}
template <class... Ts> void f(Ts... xs) {
    std::printf("  f got %zu args:", sizeof...(xs));
    ((std::printf(" %d", xs)), ...);
    std::printf("\n");
}

template <class... Ts> void outside(Ts... args) { f(g(args)...); }
template <class... Ts> void inside(Ts... args) { f(g(args...)); }

int main() {
    std::puts("[1] f(g(args)...) with 1, 2, 3");
    outside(1, 2, 3);
    std::puts("[2] f(g(args...)) with 1, 2, 3");
    inside(1, 2, 3);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(3)
  g(2)
  g(1)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(1)
  g(2)
  g(3)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

- ★★★ **`f(g(args)...)` 는 `f(g(1), g(2), g(3))`** — `g` 가 **원소마다** 불리고 `f` 는 **3개**를 받는다(`10 20 30`). **`f(g(args...))` 는 `f(g(1, 2, 3))`** — `g` 가 **한 번**, `f` 는 **1개**(`6`). **`...` 은 그 앞의 패턴 전체를 원소마다 복제한다.**
- ★★ `g(args)` 의 원소 하나짜리 호출은 **비템플릿 `int g(int)`** 로 갔다 — 템플릿과 비템플릿이 똑같이 맞으면 **비템플릿**(01편).
- ★★★ **g++ 는 `g(3) g(2) g(1)`, clang 은 `g(1) g(2) g(3)`** — **이 편에서 두 컴파일러가 갈린 유일한 자리**다. 함수 인자의 **평가 순서는 미명시**라 둘 다 맞다. **`f got 3 args: 10 20 30` 은 둘이 같다** — 인자의 **자리**는 정해져 있고, **계산 순서**만 정해져 있지 않다.
★★ **최적화를 켜도 같은 갈림인가** —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(3)
  g(2)
  g(1)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
===== clang++ -std=c++17 -Wall -Wextra -pedantic -O2 pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(1)
  g(2)
  g(3)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

- ★★ **`-O2` 에서도 g++ 3·2·1 · clang 1·2·3** — 이 판에서는 **최적화 수준이 아니라 컴파일러가** 순서를 정했다. ★ 그래도 **「g++ 는 늘 오른쪽부터」가 아니다** — 미명시라 판이 바뀌면 바뀔 수 있다(관찰이지 보장이 아니다).

- ★★ **순서가 필요하면 쉼표 폴드를 쓴다** — `f` 안의 `((std::printf(" %d", xs)), ...)` 는 두 컴파일러 다 `10 20 30` 순서다. **쉼표 연산자는 왼쪽부터 끝낸다** — 함수 인자 목록의 쉼표는 **연산자가 아니다.**

```text
   f(g(args)...)          →  f( g(1), g(2), g(3) )    ← 원소마다 g — 계산 순서는 미명시
   f(g(args...))          →  f( g(1, 2, 3) )          ← g 한 번
   ((printf(xs)), ...)    →  printf(1), (printf(2), printf(3))   ← 쉼표 연산자 — 왼쪽부터
```

### (5) ★★ 팩은 타입을 들고 간다 — C `stdarg` 대비

**언제 쓰나** — 「가변 인자면 C 의 `...` 으로도 되지 않나」를 따질 때.

```cpp
/* pack05.cpp */
// 팩의 원소마다 타입을 찍는다 — char · short · float · bool 을 넘긴다
#include <cstdio>
#include <cstdlib>
#include <cxxabi.h>
#include <typeinfo>

template <class T> void one(const T&) {
    int st = 0;
    char* s = abi::__cxa_demangle(typeid(T).name(), nullptr, nullptr, &st);
    std::printf("  %-6s sizeof=%zu\n", s, sizeof(T));
    std::free(s);
}

template <class... Ts> void each(const Ts&... xs) { (one(xs), ...); }

int main() {
    char c = 'a';
    short s = 2;
    float f = 1.5f;
    bool b = true;
    each(c, s, f, b);
}
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  char   sizeof=1
  short  sizeof=2
  float  sizeof=4
  bool   sizeof=1
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  char   sizeof=1
  short  sizeof=2
  float  sizeof=4
  bool   sizeof=1
```

- ★★★ **`char` · `short` · `float` · `bool` 이 넘긴 그대로** — `sizeof` 도 1 · 2 · 4 · 1. **승격이 없다.** 팩의 원소는 **자기 타입으로** 추론되기 때문이다(`Ts = {char, short, float, bool}`).
- ★★★ **C 의 `...` 은 정반대다** — C 갈래 [36번](../../../c/syntax/36-variadic-functions-stdarg/) (1)(2)가 쟀다: **`...` 뒤에서는 `char`·`short`·`_Bool` 이 `int` 로, `float` 가 `double` 로 승격**되고, `va_arg(ap, float)` 로 꺼내면 **gcc 는 프로그램을 죽이고(`exit=132`) clang 은 맞아 보이는 값을 낸다**(UB). **타입 정보가 호출 자리에서 사라진다.**
- ★ Go 의 `...T` 는 **한 타입의 슬라이스**다 — Go 갈래 [12번](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/) (4). **원소마다 다른 타입을 보존하는 것**은 셋 중 C++ 팩뿐이다.

```text
                 넘긴 것                      받는 쪽이 보는 것
   C  f(n, ...)  char short float _Bool       int int double int   ★ 승격 · 타입은 짐작  (C 36편)
   Go f(xs ...T) T T T                        []T                  한 타입의 슬라이스   (Go 12편)
   C++ f(Ts...)  char short float bool        char short float bool ★ 원소마다 자기 타입
```

## 문법 — 형태와 규칙

### 형태

```text
   template <class... Ts> void f(Ts... xs);          팩 선언 — 타입 팩 Ts · 함수 매개변수 팩 xs
   template <class... Args> T make(Args&&... args);  전달 참조 팩
   sizeof...(Ts)                                     원소 수
   g(xs...)          g(h(xs)...)                     팩 확장 — ... 앞의 패턴을 원소마다
   (... op xs)  (xs op ...)                          단항 좌 · 단항 우 (C++17)
   (I op ... op xs)  (xs op ... op I)                이항 좌 · 이항 우 (C++17)
   T(std::forward<Args>(args)...)                    완벽 전달
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **점 셋이 왼쪽이면 왼쪽부터 묶는다** — `-` 에서만 값이 갈리고 `+`·`&&`·`||` 는 안 갈린다((2)).
- ★★★ **빈 팩의 단항 폴드는 `&&`(true) · `||`(false) · `,`(void) 만 — 나머지는 이항 폴드의 `I` 로**((2)).
- ★★★ **팩을 넘길 때 `std::forward<Args>(args)...`** — 빼면 rvalue 로 넘긴 칸이 **copy** 가 된다((3)).
- ★★ **`...` 은 앞의 패턴 전체를 복제한다** — `g(args)...` 와 `g(args...)` 는 다른 호출이다((4)).
- ★★★ **확장된 함수 인자의 계산 순서는 미명시** — 순서가 필요하면 쉼표 폴드((4)).
- ★★ **팩은 원소마다 타입을 보존한다** — 승격이 없다((5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| 빈 팩에 `(... + xs)` | `fold of empty expansion over operator+` | `unary fold expression has empty expansion for operator '+' with no fallback value` | (2) |
| 빈 팩에 `(... - xs)` · `(xs + ...)` · `(xs - ...)` | 〃(격자 칸 `error`) | 〃 | (2) 격자 |

## 어디서 틀리나

### 1. ★★★ 「폴드는 어느 쪽으로 접어도 같다」

(2)가 반증이다 — **`-` 는 5 대 9, 이항은 -15 대 9.** 결합 법칙이 서는 연산자에서만 같다.

### 2. ★★★ 「빈 팩의 합은 0 이다」

(2)가 반증이다 — **`(... + xs)` 는 두 컴파일러 다 에러.** 0 을 원하면 **`(0 + ... + xs)`** 로 적는다.

### 3. ★★★ 「`Args&&...` 로 받았으니 그대로 넘기면 이동된다」

(3)이 반증이다 — **`forward` 가 없으면 임시를 넘겨도 copy.** 받는 쪽 이름 `args` 는 lvalue 다.

### 4. ★★ 「`f(g(args)...)` 는 `g` 를 왼쪽부터 부른다」

(4)가 반증이다 — **g++ 는 3·2·1**. 순서는 **미명시**이고 두 컴파일러가 **실제로 갈렸다.**

### 5. ★★ 「가변 인자는 C 의 `...` 과 같은 것이다」

(5)가 반증이다 — **팩은 `char`·`float` 를 그대로 들고 간다.** C 는 승격하고 타입을 잃는다(C 36편).

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 편은 「미명시」 칸이 처음으로 찼다** — (4)의 `g` 호출 순서. 나머지는 거의 전부 「표준」이라 **40칸 × 2 에서 갈린 칸 0** 이었다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **폴드 40칸**((2)) · **빈 팩 세 연산자**((2)) · **copy/move 의 종류와 수**((3)) · **확장 결과 `f got 3` / `f got 1`**((4)) · **원소 타입 보존**((5)) | 두 컴파일러 · cppreference(폴드) | ★ **로그는 「심은 곳」만 센다** — `Noisy` 밖의 복사는 안 보인다 |
| **조건부 표준** | 특정 판에서만 | ★★ **폴드 식은 C++17 부터** · **반환값 복사 생략(`Duo` 의 복사 0)은 C++17 부터 보장** | ★ **`pack02.cpp` 를 `-std=c++14` 로** — 경고만 내고 통과(종료 코드 0 절) | ★★★ **`-pedantic` 은 경고만** — `-pedantic-errors` 라야 막힌다 |
| **구현 정의** | 문서화 의무 | ★ `__cxa_demangle` 이 푸는 **이름의 철자**((5)) | 두 컴파일러 출력 | — |
| **미명시** | 몇 가지 중 하나 | ★★★ **`f(g(args)...)` 에서 `g` 를 부르는 순서**((4)) — g++ 3·2·1, clang 1·2·3 | 두 컴파일러 실행 | ★★★ **경고 0** — 순서에 기댄 코드를 아무도 알려 주지 않는다 |
| **UB** | 아무 일이나 | ★ **이 주제의 코드는 UB 가 없다** — 대비한 C 36편 쪽이 UB 다 | — | — |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | g++ 컴파일러 | clang 컴파일러 | 실행 도구 |
|---|---|---|---|---|
| ★★★ **`forward` 를 빠뜨려 이동이 복사가 된다** | 표준(허용된 코드) | ★★★ **경고 0** | ★★★ **경고 0** | 로그를 심어야 보인다 |
| ★★★ **인자 계산 순서에 기댄 코드** | 미명시 | ★★★ **경고 0** | ★★★ **경고 0** | ★ **두 컴파일러를 돌려야** 보인다 |
| ★★ **빈 팩 단항 `+`** | ill-formed | ★★★ **에러** | ★★★ **에러** | — |

- ★★ **이 표의 결론** — **성능 사고(`forward` 누락)와 순서 사고(미명시)는 조용하다.** 둘 다 이 편은 **로그와 두 컴파일러**로만 잡았다.

### ★★ 종료 코드 0인데 ill-formed — `-std=c++14` 의 폴드 식

★★ **(1)의 `pack02.cpp` 를 `-std=c++14` 로 던지면** —

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
pack02.cpp: In function ‘long int sum_fold(Ts ...)’:
pack02.cpp:12:23: warning: fold-expressions only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
   12 |     return (0 + ... + xs);
      |                       ^~
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
===== clang++ -std=c++14 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
pack02.cpp:12:17: warning: pack fold expression is a C++17 extension [-Wc++17-extensions]
   12 |     return (0 + ... + xs);
      |                 ^
1 warning generated.
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
```

- ★★★ **두 컴파일러 다 `cc exit=0` · 실행도 C++17 과 같은 값** — 폴드 식은 **C++17 문법인데** 경고 한 줄(g++ `fold-expressions only available with ‘-std=c++17’` · clang `pack fold expression is a C++17 extension`)만 내고 **확장으로 받아 준다.**

```text
===== g++ -std=c++14 -Wall -Wextra -pedantic -pedantic-errors pack02.cpp -o ex (cc exit=1) =====
pack02.cpp: In function ‘long int sum_fold(Ts ...)’:
pack02.cpp:12:23: error: fold-expressions only available with ‘-std=c++17’ or ‘-std=gnu++17’ [-Wc++17-extensions]
   12 |     return (0 + ... + xs);
      |                       ^~
===== clang++ -std=c++14 -Wall -Wextra -pedantic -pedantic-errors pack02.cpp -o ex (cc exit=1) =====
pack02.cpp:12:17: error: pack fold expression is a C++17 extension [-Werror,-Wc++17-extensions]
   12 |     return (0 + ... + xs);
      |                 ^
1 error generated.
```

- ★★★ **`-pedantic-errors` 를 붙여야 `cc exit=1`** — 「`-std=` 는 강제가 아니라 기본값 선택」과 같은 집안이다. **`-pedantic` 은 경고, `-pedantic-errors` 라야 에러**다.
- ★ 빈 팩 단항 `+`·`-` 는 **두 컴파일러 다 `cc exit=1`** 이었다(격자 4칸 · 단독 블록 둘) — 그쪽은 확장이 없다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 팩을 연산자 하나로 접는다 · C++17 | ★★★ **폴드 식** | (1)(2) — 끝 판 함수가 필요 없다 |
| 빈 팩이 올 수 있다 | ★★★ **이항 폴드 `(I op ... op xs)`** | (2) — `&&`·`\|\|`·`,` 가 아니면 단항은 에러 |
| `-`·`/` 처럼 방향이 답을 바꾼다 | ★★ **꼴을 의도대로 고르고 주석** | (2) |
| 받은 인자로 객체를 만든다 | ★★★ **`Args&&... args` + `std::forward<Args>(args)...`** | (3) |
| 원소마다 부수 효과를 순서대로 | ★★★ **쉼표 폴드** | (4) — 함수 인자 목록은 순서가 미명시 |
| 타입이 다른 가변 인자 | ★★★ **팩** — C 의 `...` 은 쓰지 않는다 | (5) · C 36편 |
| C++11/14 코드베이스 | ★★ **재귀 풀기 + 끝 판 오버로드** | (1) |

## 핵심 문장

- ★★★ **폴드 식 40칸 × 2 — 컴파일러가 갈린 칸 0 / 40, 좌 대 우가 갈린 짝 3 / 10(`-` 둘 · `,` 이항 하나).**
- ★★★ **빈 팩의 단항 폴드는 `&&`→true · `||`→false · `,`→void 만 — `+`·`-` 는 에러, 이항 폴드는 `I`.**
- ★★★ **`forward` 가 있으면 임시는 move, 빼면 copy** — 받는 이름 `args` 가 lvalue 라서다(09편).
- ★★ **`f(g(args)...)` 는 `g` 를 원소마다, `f(g(args...))` 는 한 번** — `...` 은 앞의 패턴 전체를 복제한다.
- ★★★ **`g` 를 부르는 순서가 g++ 3·2·1, clang 1·2·3** — 미명시다. 순서가 필요하면 쉼표 폴드.
- ★★ **팩은 `char`·`float` 를 그대로 들고 간다** — C 의 `...` 은 승격하고 타입을 잃는다.

## 관련 자료

- [09번](../09-rvalue-references-move-and-forward/) (3)(6) — ★★★ **로그로 세는 법과 `forward` 가 필요한 이유** — (3)은 그것을 **팩 전체**에 한 것이다.
- [31번](../31-function-templates-and-argument-deduction/) (2)(5) — `T&&` 의 추론 — `Args` 가 원소마다 `Noisy&` / `Noisy` 가 되는 근거.
- [01번](../01-function-overloading-and-overload-resolution/) — 비템플릿이 이기는 규칙 — (4)의 `g(int)`.
- [33번](../33-template-specialization-and-partial-specialization/) — 재귀 풀기의 끝 판을 **오버로드**로 둔 것이 33편 (2)의 방식이다.
- [35번](../35-instantiation-header-placement-and-reading-errors/) — 팩을 받는 템플릿도 **헤더에** 둔다.
- C 갈래 [36번](../../../c/syntax/36-variadic-functions-stdarg/) — ★★★ **C 의 `...` — 승격 격자와 `va_arg(ap, float)` 의 UB.** 여기는 **타입이 남는 쪽**이다.
- Go 갈래 [12번](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/) (4) — 가변 인자는 **한 타입의 슬라이스**.
- 목록의 **36번 주제**(컨셉) — 팩의 원소마다 제약 걸기(`std::integral auto... xs`).

## 용어 풀이

> **파라미터 팩(parameter pack)** — 0개 이상의 템플릿 인자(`class... Ts`) 또는 함수 인자(`Ts... xs`)를 한 이름으로 묶은 것.\
> 예: (1)의 `Rest... rest`.

> **팩 확장(pack expansion)** — `패턴...` 을 원소마다 패턴을 복제한 목록으로 펼치는 것.\
> 예: (4)의 `g(args)...` → `g(1), g(2), g(3)`.

> **폴드 식(fold expression)** — C++17. 팩을 이항 연산자 하나로 접는 식. 단항 좌/우 · 이항 좌/우 네 꼴.\
> 예: (2)의 격자.

> **완벽 전달(perfect forwarding)** — 받은 인자의 값 범주(lvalue/rvalue)까지 그대로 다음 함수에 넘기는 것. `T&&` + `std::forward<T>`.\
> 예: (3)의 `make_fwd`.

> **미명시 동작(unspecified behavior)** — 표준이 몇 가지 중 하나를 허락하고 **어느 것인지 문서화도 요구하지 않는** 것.\
> 예: (4)의 `g` 호출 순서.

> **기본 인자 승격(default argument promotion)** — C 의 `...` 뒤에서 작은 정수가 `int` 로, `float` 가 `double` 로 바뀌는 것. 팩에는 없다.\
> 예: (5)의 대비 · C 36편 (2).

## 더 들어가면

- **팩의 N 번째 원소 꺼내기** — 이 문서는 `std::tuple` 이나 재귀 없이 꺼내는 법을 던지지 않았다.
- **람다의 팩 캡처(C++20)** — `[...xs = std::move(xs)]`. 이 문서는 던지지 않았다.
- **`std::tuple` 로 팩 보관하기 · `std::apply`** — 팩을 값으로 들고 다니는 법. 목록의 **48번 주제** 쪽이다.
