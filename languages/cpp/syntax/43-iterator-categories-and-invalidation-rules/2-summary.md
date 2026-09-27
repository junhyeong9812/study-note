# cpp/syntax/43 — 이터레이터 범주와 무효화 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Containers library 의 「Iterator invalidation」 표](https://en.cppreference.com/w/cpp/container) · [`std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back) · [`std::deque::push_front`](https://en.cppreference.com/w/cpp/container/deque/push_front) · [`std::unordered_map::rehash`](https://en.cppreference.com/w/cpp/container/unordered_map/rehash) · [`std::erase_if`(vector)](https://en.cppreference.com/w/cpp/container/vector/erase2)\
> ★ 이 배치에서 **위 cppreference 쪽들을 열어 확인했다** — 무효화 표는 **(삽입 · 삭제) × (이터레이터 · 참조) × 조건**으로 적혀 있다: `vector` 삽입은 「**Insertion changed capacity**」면 전부 무효, 아니면 「**Before modified element(s)**」만 유효 · `deque` 삽입은 이터레이터 무효 · 참조는 「**Modified first or last element**」면 유효 · `list`·`forward_list`·정렬 연관 컨테이너는 삽입에 전부 유효 · 해시 쪽은 「**Insertion caused rehash**」면 이터레이터 무효 · 참조 유효. 그리고 「**clear invalidates all iterators and references.**」
> **실행 검증** — 이 문서의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★★ clang 도 같은 라이브러리 — **`_GLIBCXX_DEBUG`·`_GLIBCXX_SANITIZE_VECTOR` 는 libstdc++ 의 장치**라 두 컴파일러가 **같은 검사기**를 쓴다) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`inv01.cpp`·`erase01.cpp`·`rfor01.cpp`·`cat01.cpp`·`sort01.cpp`·`inv-grid.sh`·`sort-grid.sh`).\
> ★★ **ASan 블록은 `-O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=.`** 로 빌드했고 **마커는 표준 오류로** 찍었다(규칙 19-A). **격자는 판마다 한 번 빌드하고 칸마다 돌렸다**(빌드 여섯 · 칸마다 바이너리 여섯을 한 번씩 — 실행 210). 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — 이터레이터 범주 태그는 **C++98**, 이터레이터 컨셉(`std::random_access_iterator` 등)·`std::ranges::sort`·`std::erase_if` 는 **C++20** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[41번](../41-choosing-sequence-containers/)에서 온다** — 41 (1)이 **「처음 원소 주소가 그대로인가」** 를 넣는 동안만 봤다. 여기서는 **연산 일곱 전부 · 이터레이터와 참조를 갈라서 · 쓰면 무엇이 나오나**까지 간다. [42번](../42-associative-containers-ordered-vs-hashed/) (5)의 **`bucket_count` 가 바뀌는 순간(rehash)** 이 격자의 `unordered_map` 행이다.\
> [30번](../30-dangling-references-and-lifetime-extension/) — 댕글링 일반과 ASan 사용법. [36번](../36-concepts-and-requires/) · [35번](../35-instantiation-header-placement-and-reading-errors/) — **컨셉을 걸면 첫 에러가 호출 줄로** — (4)의 `std::ranges::sort(list)` 가 그 사례다.
> ★★★ **무효가 된 이터레이터·참조를 쓰는 것은 UB 다 — 그 값은 싣지 않는다.** 결과는 **`_GLIBCXX_DEBUG` 가 잡았나 · ASan 리포트 이름**뿐이다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 **PID · 주소 · `pc`/`bp`/`sp`** · 디버그 모드 리포트의 **`@ 0x…`** · 진단 **문구와 총 줄 수** | ★★★ **격자의 칸(잡음 / 침묵 / 리포트 이름) · `Error:` 줄 · `SUMMARY` 의 `파일:줄` · `run exit` · 격자의 마지막 줄** |
> | ★ **디버그 모드가 검사하는 자리** — libstdc++ 의 선택(표준 밖) | ★★★ **명세 칸** — cppreference 표를 옮긴 것 |

## 한눈에 — 쉽게 말하면

**이터레이터는 「좌석 번호표」, 참조는 「그 사람의 손」이다.**

- 좌석을 **다시 배치**하면(`vector` 재할당) 번호표도 손도 **엉뚱한 곳**을 잡는다 — 옛 극장은 **철거됐다**(ASan `heap-use-after-free`).
- 좌석 **가운데에 한 줄 끼워 넣으면**(`vector` 가운데 삽입) 극장은 그대로인데 **뒤쪽 사람이 한 칸씩 밀린다.** 번호표는 무효다 — 그런데 **극장이 철거되지 않았으니 ASan 은 모른다**((1)의 「명세와 갈린 칸」).
- **`deque`** 는 끝에 줄을 붙이면 **사람은 안 움직이는데 좌석표 체계(이터레이터)가 바뀐다** — 번호표는 무효, 손은 유효.
- **`list`·`map`** 은 한 사람씩 따로 앉아 있어 **남이 들어오고 나가도 그 사람은 그대로**다 — **지워진 사람만** 무효.
- **해시 쪽**은 칸 수를 바꾸면(rehash) **번호표만 무효**, 사람은 그대로.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 좌석 재배치 · 옛 극장 철거 | ★★★ **`vector` 재할당 — 전부 무효 · `heap-use-after-free`** | (1) |
| 뒤쪽이 한 칸씩 밀림 | ★★★ **`vector` 가운데 삽입·앞 삭제 — 무효인데 ASan 침묵** | (1) |
| 좌석표 체계만 바뀜 | ★★ **`deque` 끝 삽입 · 해시 rehash — 이터레이터만 무효** | (1) |
| 따로 앉은 사람 | ★★ **`list`·`map` — 지워진 것만** | (1) |
| 지우고 나서 번호표로 다음 칸 | ★★★ **순회 중 `erase` 뒤 `++it`** | (2) |
| 훑는 도중 극장 확장 | ★★★ **범위 `for` 안의 `push_back`** | (3) |

```text
   vector: 0 1 [2] 3        it ─▶ [2]  r ─▶ [2]
           insert(begin()+1, 9)
           0 9 1 [2] 3      it 는 무효(명세) · 같은 주소에는 이제 「1」 이 있다  → ASan 은 침묵
           push_back 으로 capacity 초과
           새 버퍼 …        옛 버퍼 해제 → it · r 로 읽으면 heap-use-after-free
```

## 이 주제가 답하려는 질문

1. ★★★ **컨테이너 다섯 × 연산 일곱 — 어느 칸의 이터레이터·참조가 무효인가, 도구는 어느 칸을 잡나**((1)).
2. ★★★ **순회 중 지우기는 어떻게 써야 하나**((2)).
3. ★★ **범위 기반 `for` 안에서 같은 `vector` 를 키우면**((3)).
4. ★★ **이터레이터 범주는 무엇을 막나 — `std::sort(list)` 와 `std::ranges::sort(list)` 의 에러가 다른 까닭**((4)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ④ `_GLIBCXX_DEBUG` 와 ③ ASan 이다

★★★ **무효화는 「값이 틀렸다」로 안 보인다** — 무효가 된 참조가 **우연히 맞는 값**을 읽기도 하고, 밀려 온 **다른 원소**를 읽기도 한다. 그래서 두 도구로 묻는다 — **이터레이터는 `_GLIBCXX_DEBUG`**(쓰기 전에 「이 이터레이터는 무효로 표시됐나」를 본다) · **참조는 ASan**(해제된 메모리를 읽나). 그리고 **명세 칸과 대조**한다.

```text
① 다섯 층 표              무효화 규칙은 표준 · 검사 자리는 libstdc++                           (구현 세부사항 절)
② 두 컴파일러              격자 전체 · sort 에러 전문                                           (1)(4)
③ ★★★ ASan                 참조 창 — heap-use-after-free · container-overflow                     (1)(3)
④ ★★★ _GLIBCXX_DEBUG       이터레이터 창 — attempt to dereference / increment a singular iterator   (1)(2)(3)
⑤ ★★★ 명세 대조 격자        컨테이너 5 × 연산 7 — 명세 · 도구 · 갈린 칸을 스크립트가 센다             (1)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **명세 대 검사기의 자리** | **쓴다** |
| ② 두 컴파일러 | ★★ **격자 컴파일러 사이 갈린 행 0 / 35** · 정렬 에러 | **쓴다** |
| ★★★ **③ ASan** | ★★★ 참조 창 — **명세상 무효 10 칸 중 잡은 칸 5**(+ `SANITIZE_VECTOR` 로 6) | **쓴다** |
| ★★★ **④ `_GLIBCXX_DEBUG`** | ★★★ **본체** — 이터레이터 창 — **명세상 무효 13 칸 중 12 칸을 잡았다 · 놓친 칸 1(`rehash()`)** | **쓴다** |
| ★★★ **⑤ 명세 대조 격자** | ★★★ **명세와 갈린 칸 — 이터레이터 1 / 27 · 참조 5 / 27(`SANITIZE_VECTOR` 까지 4 / 27)** | **쓴다** |
| ★ 제5의 상태 | 참조의 무효화를 **ASan 이 못 보는 칸**(메모리가 살아 있다) — `vector` 는 **`_GLIBCXX_SANITIZE_VECTOR`** 로 창을 바꿔 한 칸을 더 물었다 | **창을 바꿔 답함** — ★ 그 창도 **「밀려 온 다른 원소」는 못 본다** |

### (1) ★★★ 무효화 격자 — 컨테이너 다섯 × 연산 일곱

**언제 쓰나** — 이터레이터·참조·포인터를 **들고 있는 채로** 컨테이너를 고칠 때마다.

```cpp
/* inv01.cpp */
// 무효화 탐침 — ./a.out <컨테이너 1..5> <연산 1..7>. 원소 0 1 2 3 을 넣고 「2」를 가리키는 이터레이터와 참조를 잡은 뒤
// 연산을 하나 하고, -DUSE_ITER 이면 이터레이터를, 아니면 참조를 쓴다. 찍는 것은 표준 오류로
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <iterator>
#include <list>
#include <map>
#include <unordered_map>
#include <vector>

[[noreturn]] void not_applicable() { std::fprintf(stderr, "부적용\n"); std::exit(3); }

template <class Seq> int probe_seq(int op, bool is_vector) {
    Seq c;
    if constexpr (requires { c.reserve(1); }) c.reserve(op == 2 ? 4 : 8);
    for (int i = 0; i < 4; ++i) c.push_back(i);
    auto it = std::next(c.begin(), 2);
    int& r = *it;
    (void)r;
    switch (op) {
    case 1: c.push_back(9); break;                                   // 끝에 추가 — 용량 안
    case 2: if (!is_vector) not_applicable(); c.push_back(9); break;  // 끝에 추가 — 용량 초과
    case 3: c.insert(std::next(c.begin()), 9); break;                // 가운데 삽입 — 잡은 원소 앞
    case 4: c.erase(c.begin()); break;                               // 첫 원소 지우기 — 잡은 원소 앞
    case 5: c.erase(std::prev(c.end())); break;                      // 마지막 원소 지우기 — 잡은 원소 뒤
    case 6: if constexpr (requires { c.reserve(1); }) c.reserve(100); else not_applicable(); break;
    case 7: c.clear(); break;
    }
#ifdef USE_ITER
    return *it;
#else
    return r;
#endif
}

template <class Map> int probe_map(int op, bool is_unordered) {
    Map c;
    if constexpr (requires { c.rehash(1); }) { if (op != 2) c.reserve(100); }
    for (int i = 0; i < 4; ++i) c.emplace(i, i);
    auto it = c.find(2);
    int& r = it->second;
    (void)r;
    switch (op) {
    case 1: c.emplace(10, 10); break;
    case 2:
        if (!is_unordered) not_applicable();
        if constexpr (requires { c.bucket_count(); }) {
            auto b = c.bucket_count();
            for (int k = 10; c.bucket_count() == b; ++k) c.emplace(k, k);   // rehash 가 일어날 때까지 넣는다
            std::fprintf(stderr, "bucket_count %zu -> %zu\n", b, c.bucket_count());
        }
        break;
    case 3: not_applicable();
    case 4: c.erase(0); break;
    case 5: c.erase(3); break;
    case 6:
        if constexpr (requires { c.rehash(1); }) {
            auto b = c.bucket_count();
            c.rehash(1000);
            std::fprintf(stderr, "bucket_count %zu -> %zu\n", b, c.bucket_count());
        } else not_applicable();
        break;
    case 7: c.clear(); break;
    }
#ifdef USE_ITER
    return it->second;
#else
    return r;
#endif
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    int cont = std::atoi(argv[1]), op = std::atoi(argv[2]);
    int v = 0;
    switch (cont) {
    case 1: v = probe_seq<std::vector<int>>(op, true); break;
    case 2: v = probe_seq<std::deque<int>>(op, false); break;
    case 3: v = probe_seq<std::list<int>>(op, false); break;
    case 4: v = probe_map<std::map<int, int>>(op, false); break;
    case 5: v = probe_map<std::unordered_map<int, int>>(op, true); break;
    }
    std::fprintf(stderr, "썼다\n");
    return v == 2 ? 0 : 1;
}
```

- ★★ **탐침** — 원소 `0 1 2 3` 을 넣고 **「2」를 가리키는 이터레이터 `it` 와 참조 `r`** 를 잡은 뒤 연산을 **하나** 한다. 「앞」·「뒤」는 **잡은 원소보다 앞 · 뒤**라는 뜻이다(해시 쪽에서는 키 0 과 3 을 지울 뿐 **위치의 앞뒤는 뜻이 없다**).
- ★★ **「끝에 추가(용량 안)」** 은 `vector` 를 `reserve(8)` · 해시 쪽을 `reserve(100)` 해 두고 넣는다 — **재할당·rehash 가 없는 판**이다. **「(재할당·rehash)」** 는 `vector` 를 `reserve(4)` 로 꽉 채우고 · 해시 쪽은 **`bucket_count` 가 바뀔 때까지** 넣는다.

```bash
# inv-grid.sh
# inv-grid.sh — 컨테이너 다섯 × 연산 일곱. 판마다 한 번 빌드해 칸마다 돌린다(컴파일러 둘 × 창 셋 = 빌드 여섯)
# 창: 이터레이터 = -D_GLIBCXX_DEBUG 가 쓰기를 잡나 · 참조 = ASan · 참조 = ASan + -D_GLIBCXX_SANITIZE_VECTOR
# 명세 칸은 cppreference 「Iterator invalidation」 표를 옮긴 것이다(무효 / 유효). 부적용 칸은 탐침이 스스로 알린다
conts=('1 vector' '2 deque' '3 list' '4 map' '5 unordered_map')
ops=('1 끝에 추가(용량 안)' '2 끝에 추가(재할당·rehash)' '3 가운데 삽입(앞)' '4 첫 원소 지우기(앞)' '5 마지막 원소 지우기(뒤)' '6 reserve·rehash' '7 clear')
# 명세 — "컨테이너 연산" → "이터레이터 참조"
spec() {
  case "$1 $2" in
    "1 1") echo "유효 유효" ;; "1 2") echo "무효 무효" ;; "1 3") echo "무효 무효" ;; "1 4") echo "무효 무효" ;;
    "1 5") echo "유효 유효" ;; "1 6") echo "무효 무효" ;;
    "2 1") echo "무효 유효" ;; "2 3") echo "무효 무효" ;; "2 4") echo "유효 유효" ;; "2 5") echo "유효 유효" ;;
    "5 2") echo "무효 유효" ;; "5 6") echo "무효 유효" ;;
    *" 7") echo "무효 무효" ;;
    *) echo "유효 유효" ;;
  esac
}
for c in g++ clang++; do
  $c -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG -DUSE_ITER inv01.cpp -o "d-$c" || { echo "cc 에러"; exit 1; }
  $c -std=c++20 -O0 -fsanitize=address -g inv01.cpp -o "a-$c" || { echo "cc 에러"; exit 1; }
  $c -std=c++20 -O0 -fsanitize=address -g -D_GLIBCXX_SANITIZE_VECTOR inv01.cpp -o "s-$c" || { echo "cc 에러"; exit 1; }
done
verdict() {   # $1 = 바이너리 · $2 $3 = 칸
  local out rc k
  out=$("./$1" "$2" "$3" 2>&1); rc=$?
  [ "$rc" -eq 3 ] && { printf '부적용'; return; }
  case "$1" in
    d-*) printf '%s\n' "$out" | grep -q '^Error: ' && printf '잡음' || printf '침묵' ;;
    *) k=$(printf '%s\n' "$out" | grep -m 1 -oE '^SUMMARY: AddressSanitizer: [a-z-]+' | sed 's/^SUMMARY: AddressSanitizer: //'); printf '%s' "${k:-침묵}" ;;
  esac
}
merge() { [ "$1" = "$2" ] && printf '%s' "$1" || printf 'g++ %s / clang %s' "$1" "$2"; }
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "컨테이너" "연산" "명세 이터레이터" "debug 모드" "명세 참조" "ASan" "ASan+SANITIZE_VECTOR" > t.tsv
split=0
for ct in "${conts[@]}"; do
  for op in "${ops[@]}"; do
    a=${ct%% *}; b=${op%% *}
    dg=$(verdict d-g++ $a $b); dc=$(verdict d-clang++ $a $b)
    ag=$(verdict a-g++ $a $b); ac=$(verdict a-clang++ $a $b)
    sg=$(verdict s-g++ $a $b); sc=$(verdict s-clang++ $a $b)
    [ "$dg$ag$sg" = "$dc$ac$sc" ] || split=$(( split + 1 ))
    if [ "$dg" = "부적용" ]; then si="부적용"; sr="부적용"; else set -- $(spec $a $b); si=$1; sr=$2; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$ct" "$op" "$si" "$(merge "$dg" "$dc")" "$sr" "$(merge "$ag" "$ac")" "$(merge "$sg" "$sc")" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 7' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
tail -n +2 t.tsv | awk -F'\t' -v nsplit="$split" '
  $3 == "부적용" { na++; next }
  { app++
    if ($3 == "무효") ii++; if ($5 == "무효") ri++
    if (($3 == "무효") != ($4 == "잡음")) im++
    if (($5 == "무효") != ($6 != "침묵")) ra++
    if (($5 == "무효") != ($6 != "침묵" || $7 != "침묵")) rs++ }
  END {
    printf "적용 칸 %d / %d(부적용 %d) · 명세상 무효 — 이터레이터 %d / %d · 참조 %d / %d\n", app, app + na, na, ii, app, ri, app
    printf "명세와 갈린 칸 — 이터레이터(debug 모드) %d / %d · 참조(ASan) %d / %d · 참조(ASan+SANITIZE_VECTOR 까지) %d / %d · 컴파일러 사이 갈린 행 %d / %d\n", im, app, ra, app, rs, app, nsplit, app + na
  }' || exit 1
rm -f d-g++ d-clang++ a-g++ a-clang++ s-g++ s-clang++ t.tsv
```

```text
===== bash inv-grid.sh (exit=0) =====
컨테이너	연산	명세 이터레이터	debug 모드	명세 참조	ASan	ASan+SANITIZE_VECTOR
1 vector	1 끝에 추가(용량 안)	유효	침묵	유효	침묵	침묵
1 vector	2 끝에 추가(재할당·rehash)	무효	잡음	무효	heap-use-after-free	heap-use-after-free
1 vector	3 가운데 삽입(앞)	무효	잡음	무효	침묵	침묵
1 vector	4 첫 원소 지우기(앞)	무효	잡음	무효	침묵	침묵
1 vector	5 마지막 원소 지우기(뒤)	유효	침묵	유효	침묵	침묵
1 vector	6 reserve·rehash	무효	잡음	무효	heap-use-after-free	heap-use-after-free
1 vector	7 clear	무효	잡음	무효	침묵	container-overflow
2 deque	1 끝에 추가(용량 안)	무효	잡음	유효	침묵	침묵
2 deque	2 끝에 추가(재할당·rehash)	부적용	부적용	부적용	부적용	부적용
2 deque	3 가운데 삽입(앞)	무효	잡음	무효	침묵	침묵
2 deque	4 첫 원소 지우기(앞)	유효	침묵	유효	침묵	침묵
2 deque	5 마지막 원소 지우기(뒤)	유효	침묵	유효	침묵	침묵
2 deque	6 reserve·rehash	부적용	부적용	부적용	부적용	부적용
2 deque	7 clear	무효	잡음	무효	침묵	침묵
3 list	1 끝에 추가(용량 안)	유효	침묵	유효	침묵	침묵
3 list	2 끝에 추가(재할당·rehash)	부적용	부적용	부적용	부적용	부적용
3 list	3 가운데 삽입(앞)	유효	침묵	유효	침묵	침묵
3 list	4 첫 원소 지우기(앞)	유효	침묵	유효	침묵	침묵
3 list	5 마지막 원소 지우기(뒤)	유효	침묵	유효	침묵	침묵
3 list	6 reserve·rehash	부적용	부적용	부적용	부적용	부적용
3 list	7 clear	무효	잡음	무효	heap-use-after-free	heap-use-after-free
4 map	1 끝에 추가(용량 안)	유효	침묵	유효	침묵	침묵
4 map	2 끝에 추가(재할당·rehash)	부적용	부적용	부적용	부적용	부적용
4 map	3 가운데 삽입(앞)	부적용	부적용	부적용	부적용	부적용
4 map	4 첫 원소 지우기(앞)	유효	침묵	유효	침묵	침묵
4 map	5 마지막 원소 지우기(뒤)	유효	침묵	유효	침묵	침묵
4 map	6 reserve·rehash	부적용	부적용	부적용	부적용	부적용
4 map	7 clear	무효	잡음	무효	heap-use-after-free	heap-use-after-free
5 unordered_map	1 끝에 추가(용량 안)	유효	침묵	유효	침묵	침묵
5 unordered_map	2 끝에 추가(재할당·rehash)	무효	잡음	유효	침묵	침묵
5 unordered_map	3 가운데 삽입(앞)	부적용	부적용	부적용	부적용	부적용
5 unordered_map	4 첫 원소 지우기(앞)	유효	침묵	유효	침묵	침묵
5 unordered_map	5 마지막 원소 지우기(뒤)	유효	침묵	유효	침묵	침묵
5 unordered_map	6 reserve·rehash	무효	침묵	유효	침묵	침묵
5 unordered_map	7 clear	무효	잡음	무효	heap-use-after-free	heap-use-after-free
적용 칸 27 / 35(부적용 8) · 명세상 무효 — 이터레이터 13 / 27 · 참조 10 / 27
명세와 갈린 칸 — 이터레이터(debug 모드) 1 / 27 · 참조(ASan) 5 / 27 · 참조(ASan+SANITIZE_VECTOR 까지) 4 / 27 · 컴파일러 사이 갈린 행 0 / 35
```

- ★★★ **명세상 무효 — 이터레이터 13 / 27 · 참조 10 / 27.** 이터레이터가 더 자주 무효다 — **`deque` 끝 추가 · 해시 rehash 두 곳은 이터레이터만** 무효다.
- ★★★ **`_GLIBCXX_DEBUG` 는 명세와 1 / 27 칸만 갈렸다 — `unordered_map` × `rehash()`.** 넣다가 일어난 rehash(「끝에 추가(재할당·rehash)」 행)는 **잡았는데**, **`rehash(1000)` 을 직접 부른 칸은 침묵**했다(아래 블록 — `bucket_count 103 -> 1031` 인데 `썼다`). **디버그 모드도 명세를 전부 검사하지는 않는다.**
- ★★★ **ASan 은 참조 창에서 5 / 27 칸을 놓쳤다** — **`vector` 가운데 삽입 · 앞 삭제 · `clear` · `deque` 가운데 삽입 · `clear`.** 다섯 칸 다 **메모리가 해제되지 않았다** — 원소가 **밀렸거나**(`vector`) **칸이 남았다**(`deque`·`vector` 의 `clear`). ASan 은 **해제된 메모리**만 본다.
- ★★ **`_GLIBCXX_SANITIZE_VECTOR` 를 켜면 `vector` × `clear` 한 칸을 `container-overflow` 로 더 잡는다**(4 / 27). **`size()` 밖을 읽은 것**이라 잡힌다. **밀려 온 원소를 읽는 두 칸은 그래도 침묵** — 그 자리는 **`size()` 안**이다.
- ★★ **컴파일러 사이 갈린 행 0 / 35** — 검사기가 **libstdc++ 의 것**이라 두 컴파일러가 같다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG -DUSE_ITER inv01.cpp -o ex && ./ex 5 6 (cc exit=0 · run exit=0) =====
bucket_count 103 -> 1031
썼다
===== g++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG -DUSE_ITER inv01.cpp -o ex && ./ex 5 2 (cc exit=0 · run exit=134) =====
bucket_count 13 -> 29
/usr/include/c++/13/debug/safe_iterator.h:312:
In function:
    gnu_debug::_Safe_iterator<_Iterator, _Sequence, _Category>::pointer 
    gnu_debug::_Safe_iterator<_Iterator, _Sequence, _Category>::operator->() 
    const [with _Iterator = std::detail::_Node_iterator<std::pair<const int, 
    int>, false, false>; _Sequence = std::debug::unordered_map<int, int>; 
    _Category = std::forward_iterator_tag; pointer = std::pair<const int, 
    int>*]

Error: attempt to dereference a singular iterator.

Objects involved in the operation:
    iterator "this" @ 0x7ffde2b42860 {
      type = std::detail::_Node_iterator<std::pair<int const, int>, false, false> (mutable iterator);
      state = singular;
      references sequence with type 'std::debug::unordered_map<int, int, std::hash<int>, std::equal_to<int>, std::allocator<std::pair<int const, int> > >' @ 0x7ffde2b428c0
    }
```

- ★★★ **같은 디버그 빌드 · 같은 `unordered_map` — `./ex 5 6`(직접 `rehash`)은 `썼다` · `run exit=0`, `./ex 5 2`(넣다가 rehash)는 `Error: attempt to dereference a singular iterator.` · `run exit=134`.** 둘 다 **`bucket_count` 가 바뀌었다**(103 → 1031 · 13 → 29). 명세는 둘 다 이터레이터 무효다. **침묵은 「안전」이 아니라 「안 물었다」** 다(규칙 18-A).

```text
                    끝 추가   끝 추가      가운데   앞 삭제   뒤 삭제   reserve·   clear
                    (용량 안) (재할당)     삽입                         rehash
   vector   이터     O         ✘ 잡음       ✘ 잡음   ✘ 잡음    O         ✘ 잡음     ✘ 잡음
            참조     O         ✘ UAF        ✘ ★침묵  ✘ ★침묵   O         ✘ UAF      ✘ ★침묵(SV 는 잡음)
   deque    이터     ✘ 잡음    —            ✘ 잡음   O         O         —          ✘ 잡음
            참조     O         —            ✘ ★침묵  O         O         —          ✘ ★침묵
   list·map 이터·참조 O(지워진 것만 무효)                                              ✘ 잡음 · UAF
   unordered_map 이터 O        ✘ 잡음       —        O         O         ✘ ★침묵    ✘ 잡음
            참조     O         O            —        O         O         O          ✘ UAF
   ★ O = 명세상 유효 · ✘ = 명세상 무효 · ★ = 도구가 명세와 갈린 칸. 위 격자에서 옮긴 요약이다 — 원본은 캡처
```

### (2) ★★★ 순회 중 삭제 — 틀린 꼴 하나 · 옳은 꼴 넷

**언제 쓰나** — 조건에 맞는 원소를 **돌면서** 지울 때.

```cpp
/* erase01.cpp */
// 순회 중 짝수 지우기 — 네 꼴(-DFORM=1..4)과 map 한 꼴(-DFORM=5). 결과와 크기를 표준 오류로 찍는다
#include <algorithm>
#include <cstdio>
#include <map>
#include <vector>

int main() {
#if FORM == 5
    std::map<int, int> m{{1, 1}, {2, 2}, {3, 3}, {4, 4}, {5, 5}, {6, 6}};
    for (auto it = m.begin(); it != m.end();) {
        if (it->first % 2 == 0) it = m.erase(it);
        else ++it;
    }
    for (const auto& kv : m) std::fprintf(stderr, "%d ", kv.first);
    std::fprintf(stderr, "| size %zu\n", m.size());
#else
    std::vector<int> v{1, 2, 3, 4, 5, 6};
#if FORM == 1
    for (auto it = v.begin(); it != v.end(); ++it)          // 지운 뒤에도 ++it
        if (*it % 2 == 0) v.erase(it);
#elif FORM == 2
    for (auto it = v.begin(); it != v.end();) {             // erase 가 돌려준 것을 받는다
        if (*it % 2 == 0) it = v.erase(it);
        else ++it;
    }
#elif FORM == 3
    v.erase(std::remove_if(v.begin(), v.end(), [](int x) { return x % 2 == 0; }), v.end());
#elif FORM == 4
    auto n = std::erase_if(v, [](int x) { return x % 2 == 0; });
    std::fprintf(stderr, "erase_if 가 돌려준 수 %zu\n", n);
#endif
    for (int x : v) std::fprintf(stderr, "%d ", x);
    std::fprintf(stderr, "| size %zu\n", v.size());
#endif
}
```

**틀린 꼴(`FORM=1`) — 지운 이터레이터를 `++`**:

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG -DFORM=1 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
/usr/include/c++/13/debug/safe_iterator.h:326:
In function:
    gnu_debug::_Safe_iterator<_Iterator, _Sequence, _Category>& 
    gnu_debug::_Safe_iterator<_Iterator, _Sequence, _Category>::operator++() 
    [with _Iterator = gnu_cxx::normal_iterator<int*, std::vector<int, 
    std::allocator<int> > >; _Sequence = std::debug::vector<int>; _Category 
    = std::forward_iterator_tag]

Error: attempt to increment a singular iterator.

Objects involved in the operation:
    iterator "this" @ 0x7ffc11f7cc70 {
      type = gnu_cxx::normal_iterator<int*, std::vector<int, std::allocator<int> > > (mutable iterator);
      state = singular;
      references sequence with type 'std::debug::vector<int, std::allocator<int> >' @ 0x7ffc11f7cd00
    }
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG -DFORM=1 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/debug/safe_iterator.h:328:
In function:
    _Safe_iterator<_Iterator, _Sequence, _Category> &
    gnu_debug::_Safe_iterator<gnu_cxx::normal_iterator<int *, std::
    vector<int>>, std::vector<int>, std::forward_iterator_tag>::operator++() 
    [_Iterator = gnu_cxx::normal_iterator<int *, std::vector<int>>, 
    _Sequence = std::vector<int>, _Category = std::forward_iterator_tag]

Error: attempt to increment a singular iterator.

Objects involved in the operation:
    iterator "this" @ 0x7ffea75673a0 {
      type = gnu_cxx::normal_iterator<int*, std::vector<int, std::allocator<int> > > (mutable iterator);
      state = singular;
      references sequence with type 'std::debug::vector<int, std::allocator<int> >' @ 0x7ffea7567410
    }
```

- ★★★ **`Error: attempt to increment a singular iterator.`** — `erase(it)` 가 `it` 를 **무효로 표시**했고, 루프의 `++it` 가 그것을 **올리려다** 멈췄다(`run exit=134` · 두 컴파일러 같은 검사기). `state = singular` 가 그 표시다.

```text
===== g++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DFORM=1 erase01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: heap-buffer-overflow erase01.cpp:20 in main
===== clang++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DFORM=1 erase01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: heap-buffer-overflow erase01.cpp:20:13 in main
```

- ★★ **ASan 은 `heap-buffer-overflow` 로 잡았다**(`erase01.cpp:20` — `if (*it % 2 == 0)` 줄) — 지운 뒤 `++it` 로 **원소를 하나 건너뛰다 끝을 지나쳐** 버퍼 밖을 읽었다. **같은 실수가 두 창에서 이름이 다르다** — 디버그 모드는 **「무효를 올렸다」(원인)** · ASan 은 **「버퍼 밖을 읽었다」(결과)**.

**옳은 꼴 넷**:

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=2 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=2 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=3 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=3 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
erase_if 가 돌려준 수 3
1 3 5 | size 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=4 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
erase_if 가 돌려준 수 3
1 3 5 | size 3
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=5 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=5 erase01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
1 3 5 | size 3
```

- ★★★ **넷 다 `1 3 5 | size 3`** — `it = v.erase(it)`(`erase` 가 **다음 원소의 이터레이터**를 돌려준다) · **erase-remove 관용구** · **C++20 `std::erase_if` — 한 줄, 지운 수 3 을 돌려준다** · **`map` 도 `it = m.erase(it)`**(지운 것만 무효라 **다음 이터레이터는 살아 있다**).
- ★★ **erase-remove 가 왜 둘인가** — `std::remove_if` 는 **남길 것을 앞으로 모을 뿐 크기를 안 줄인다**(알고리즘은 컨테이너를 모른다). 뒤쪽 찌꺼기를 `v.erase(…, v.end())` 가 지운다. **`std::erase_if` 가 그 두 줄을 한 줄로** 묶었다.

**다른 언어는 이 자리를 어떻게 막나** — 한 줄씩.

- ★★★ **Rust** — [38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/) (1)(4): **`for` 안의 `v.remove` · 빌림을 든 채 `v.push` 는 컴파일 에러 E0502.** 무효화가 **타입 시스템에서** 막힌다 — 같은 코드가 C++ 에서는 **경고 0 · ASan `heap-use-after-free`** 라고 그 편이 보였다.
- ★★ **Java** — [43번](../../../java/syntax/43-iterator-and-fail-fast/): **`modCount` 대조로 `ConcurrentModificationException`** — 단 **`hasNext()` 에서는 대조하지 않아 끝에서 두 번째를 지우면 예외 없이 건너뛴다**(best-effort).
- ★★ **C#** — [31번](../../../csharp/syntax/31-ienumerable-and-foreach/): **`List<T>._version` 을 `MoveNext` 마다 대조** — 끝에서 두 번째에서도 던진다.
- ★ **C++ 은 셋 중 누구와도 다르다 — 보통 빌드는 아무것도 대조하지 않는다.** `_GLIBCXX_DEBUG` 가 **C# 의 `_version` 과 같은 일을 선택으로** 해 준다.

### (3) ★★★ 범위 기반 `for` 안에서 `push_back`

```cpp
/* rfor01.cpp */
// 범위 기반 for 안에서 같은 vector 에 push_back — 처음 원소 셋, capacity 3
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v{1, 2, 3};
    std::fprintf(stderr, "capacity %zu\n", v.capacity());
    for (int x : v) {
        if (x == 1) v.push_back(4);
        std::fprintf(stderr, "x = %d\n", x);
    }
    std::fprintf(stderr, "size %zu\n", v.size());
}
```

```text
===== g++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. rfor01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
capacity 3
x = 1
=================================================================
==2271021==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000014 at pc 0x56a03422a724 bp 0x7ffccdf10950 sp 0x7ffccdf10940
READ of size 4 at 0x502000000014 thread T0
    #0 0x56a03422a723 in main rfor01.cpp:8

0x502000000014 is located 4 bytes inside of 12-byte region [0x502000000010,0x50200000001c)
freed by thread T0 here:
    #0 0x73600fcff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x56a03422cfae in std::__new_allocator<int>::deallocate(int*, unsigned long) /usr/include/c++/13/bits/new_allocator.h:172
    #2 0x56a03422bdca in std::allocator<int>::deallocate(int*, unsigned long) /usr/include/c++/13/bits/allocator.h:210
    #3 0x56a03422bdca in std::allocator_traits<std::allocator<int> >::deallocate(std::allocator<int>&, int*, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:517
    #4 0x56a03422bdca in std::_Vector_base<int, std::allocator<int> >::_M_deallocate(int*, unsigned long) /usr/include/c++/13/bits/stl_vector.h:390
    #5 0x56a03422c893 in void std::vector<int, std::allocator<int> >::_M_realloc_insert<int>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int&&) /usr/include/c++/13/bits/vector.tcc:519
    #6 0x56a03422c026 in int& std::vector<int, std::allocator<int> >::emplace_back<int>(int&&) /usr/include/c++/13/bits/vector.tcc:123
    #7 0x56a03422bd49 in std::vector<int, std::allocator<int> >::push_back(int&&) /usr/include/c++/13/bits/stl_vector.h:1299
    #8 0x56a03422a79a in main rfor01.cpp:9

previously allocated by thread T0 here:
    #0 0x73600fcfe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x56a03422b9db in std::__new_allocator<int>::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x56a03422b65f in std::allocator<int>::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x56a03422b65f in std::allocator_traits<std::allocator<int> >::allocate(std::allocator<int>&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x56a03422b65f in std::_Vector_base<int, std::allocator<int> >::_M_allocate(unsigned long) /usr/include/c++/13/bits/stl_vector.h:381
    #5 0x56a03422af4d in void std::vector<int, std::allocator<int> >::_M_range_initialize<int const*>(int const*, int const*, std::forward_iterator_tag) /usr/include/c++/13/bits/stl_vector.h:1692
    #6 0x56a03422ab60 in std::vector<int, std::allocator<int> >::vector(std::initializer_list<int>, std::allocator<int> const&) /usr/include/c++/13/bits/stl_vector.h:682
    #7 0x56a03422a5b2 in main rfor01.cpp:6

SUMMARY: AddressSanitizer: heap-use-after-free rfor01.cpp:8 in main
```

- ★★★ **`x = 1` 한 줄 뒤 `heap-use-after-free` · `rfor01.cpp:8`** — 첫 원소에서 `push_back(4)` 가 **capacity 3 을 넘겨 재할당**했고(`_M_realloc_insert` 가 옛 버퍼를 `deallocate` — `freed by` 의 `#5`), 루프가 **옛 버퍼의 다음 원소**를 읽으려다 걸렸다.
- ★★ **범위 `for` 는 `begin()`·`end()` 를 처음 한 번 잡아 두는 문법**이라, 몸통에서 컨테이너를 키우면 그 둘이 **옛 버퍼를 가리킨 채** 남는다.

```text
===== clang++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. rfor01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: heap-use-after-free rfor01.cpp:8:16 in main
===== g++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG rfor01.cpp -o ex && ./ex 2>&1 | grep -E '^(capacity|x =|Error)' (cc exit=0 · run exit=134) =====
capacity 3
x = 1
Error: attempt to increment a singular iterator.
===== clang++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG rfor01.cpp -o ex && ./ex 2>&1 | grep -E '^(capacity|x =|Error)' (cc exit=0 · run exit=134) =====
capacity 3
x = 1
Error: attempt to increment a singular iterator.
```

- ★★ **clang 도 같은 `heap-use-after-free rfor01.cpp:8:16`** · **디버그 모드는 두 컴파일러 다 `attempt to increment a singular iterator`** — 범위 `for` 안에 숨은 `++__begin` 을 잡았다.

### (4) ★★ 이터레이터 범주 — 무엇을 할 수 있나

```cpp
/* cat01.cpp */
// 컨테이너마다 이터레이터가 어느 컨셉(C++20)을 만족하나 — 1 은 만족, 0 은 아님
#include <array>
#include <cstdio>
#include <deque>
#include <forward_list>
#include <iterator>
#include <list>
#include <map>
#include <unordered_map>
#include <vector>

template <class C> void row(const char* name) {
    using It = typename C::iterator;
    std::printf("%s\t%d\t%d\t%d\t%d\n", name, (int)std::forward_iterator<It>, (int)std::bidirectional_iterator<It>,
                (int)std::random_access_iterator<It>, (int)std::contiguous_iterator<It>);
}

int main() {
    std::printf("컨테이너\tforward\tbidirectional\trandom_access\tcontiguous\n");
    row<std::array<int, 4>>("array");
    row<std::vector<int>>("vector");
    row<std::deque<int>>("deque");
    row<std::list<int>>("list");
    row<std::forward_list<int>>("forward_list");
    row<std::map<int, int>>("map");
    row<std::unordered_map<int, int>>("unordered_map");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic cat01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
컨테이너	forward	bidirectional	random_access	contiguous
array	1	1	1	1
vector	1	1	1	1
deque	1	1	1	0
list	1	1	0	0
forward_list	1	0	0	0
map	1	1	0	0
unordered_map	1	0	0	0
===== clang++ -std=c++20 -Wall -Wextra -pedantic cat01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
컨테이너	forward	bidirectional	random_access	contiguous
array	1	1	1	1
vector	1	1	1	1
deque	1	1	1	0
list	1	1	0	0
forward_list	1	0	0	0
map	1	1	0	0
unordered_map	1	0	0	0
```

- ★★★ **`random_access` 는 `array`·`vector`·`deque` 셋 · `contiguous` 는 `array`·`vector` 둘** — **`deque` 는 번호로 바로 가지만 연속은 아니다**(41편 (1)의 200 개 행).
- ★★ **`list`·`map` 은 양방향 · `forward_list`·`unordered_map` 은 앞으로만.**

```cpp
/* sort01.cpp */
// list 를 정렬하는 세 꼴(-DFORM=1..3)과 deque 를 std::sort 로(-DFORM=4). 결과를 찍는다
#include <algorithm>
#include <cstdio>
#include <deque>
#include <list>

int main() {
#if FORM == 4
    std::deque<int> c{3, 1, 2};
#else
    std::list<int> c{3, 1, 2};
#endif
#if FORM == 1
    std::sort(c.begin(), c.end());
#elif FORM == 2
    std::ranges::sort(c);
#elif FORM == 3
    c.sort();
#elif FORM == 4
    std::sort(c.begin(), c.end());
#endif
    for (int x : c) std::printf("%d ", x);
    std::printf("\n");
}
```

```bash
# sort-grid.sh
# sort-grid.sh — 정렬 네 꼴 × 컴파일러 둘. 진단을 세기만 한다. 호출 줄은 꼴 1..4 가 sort01.cpp 의 14·16·18·20 행이다
forms=('1 std::sort(list)' '2 std::ranges::sort(list)' '3 list.sort()' '4 std::sort(deque)')
calls=(14 16 18 20)
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "꼴" "컴파일러" "cc exit" "총 줄" ": error: 줄" "첫 error 가 가리키는 곳" "그곳이 호출 줄인가" > t.tsv
for f in "${forms[@]}"; do
  n=${f%% *}; call=${calls[$(( n - 1 ))]}
  for c in g++ clang++; do
    out=$($c -std=c++20 -Wall -Wextra -pedantic -DFORM=$n sort01.cpp -o sx 2>&1); rc=$?
    total=$(printf '%s' "$out" | grep -c '')
    errs=$(printf '%s\n' "$out" | grep -c ': error: ')
    first=$(printf '%s\n' "$out" | grep -m 1 ': error: ' | sed -E 's#^([^:]*/)?([^/:]+):([0-9]+):.*#\2:\3#')
    [ "$rc" -eq 0 ] && first="$(./sx)"
    if [ "$first" = "sort01.cpp:$call" ]; then same=O; elif [ "$rc" -eq 0 ]; then same=-; else same=X; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$f" "$c" "$rc" "$total" "$errs" "$first" "$same" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 7' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
fail=$(tail -n +2 t.tsv | awk -F'\t' '$3 != 0' | wc -l)
same=$(tail -n +2 t.tsv | awk -F'\t' '$7 == "O"' | wc -l)
echo "컴파일 실패 칸 $fail / $(( $(wc -l < t.tsv) - 1 )) · 그중 첫 error 가 호출 줄을 가리킨 칸 $same / $fail"
rm -f sx t.tsv
```

```text
===== bash sort-grid.sh (exit=0) =====
꼴	컴파일러	cc exit	총 줄	: error: 줄	첫 error 가 가리키는 곳	그곳이 호출 줄인가
1 std::sort(list)	g++	1	24	1	stl_algo.h:1948	X
1 std::sort(list)	clang++	1	38	2	stl_algo.h:1948	X
2 std::ranges::sort(list)	g++	1	30	1	sort01.cpp:16	O
2 std::ranges::sort(list)	clang++	1	24	1	sort01.cpp:16	O
3 list.sort()	g++	0	0	0	1 2 3 	-
3 list.sort()	clang++	0	0	0	1 2 3 	-
4 std::sort(deque)	g++	0	0	0	1 2 3 	-
4 std::sort(deque)	clang++	0	0	0	1 2 3 	-
컴파일 실패 칸 4 / 8 · 그중 첫 error 가 호출 줄을 가리킨 칸 2 / 4
```

- ★★★ **`std::sort(list)` 는 첫 error 가 `stl_algo.h:1948`(X) · `std::ranges::sort(list)` 는 `sort01.cpp:16`(호출 줄 · O)** — 두 컴파일러 같다. **`list.sort()` 와 `std::sort(deque)` 는 `1 2 3`.**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=1 sort01.cpp -o ex (cc exit=1) =====
In file included from /usr/include/c++/13/algorithm:61,
                 from sort01.cpp:2:
/usr/include/c++/13/bits/stl_algo.h: In instantiation of ‘constexpr void std::__sort(_RandomAccessIterator, _RandomAccessIterator, _Compare) [with _RandomAccessIterator = _List_iterator<int>; _Compare = __gnu_cxx::__ops::_Iter_less_iter]’:
/usr/include/c++/13/bits/stl_algo.h:4861:18:   required from ‘constexpr void std::sort(_RAIter, _RAIter) [with _RAIter = _List_iterator<int>]’
sort01.cpp:14:14:   required from here
/usr/include/c++/13/bits/stl_algo.h:1948:50: error: no match for ‘operator-’ (operand types are ‘std::_List_iterator<int>’ and ‘std::_List_iterator<int>’)
 1948 |                                 std::__lg(__last - __first) * 2,
      |                                           ~~~~~~~^~~~~~~~~
In file included from /usr/include/c++/13/bits/stl_algobase.h:67,
                 from /usr/include/c++/13/algorithm:60:
/usr/include/c++/13/bits/stl_iterator.h:625:5: note: candidate: ‘template<class _IteratorL, class _IteratorR> constexpr decltype ((__y.base() - __x.base())) std::operator-(const reverse_iterator<_IteratorL>&, const reverse_iterator<_IteratorR>&)’
  625 |     operator-(const reverse_iterator<_IteratorL>& __x,
      |     ^~~~~~~~
/usr/include/c++/13/bits/stl_iterator.h:625:5: note:   template argument deduction/substitution failed:
/usr/include/c++/13/bits/stl_algo.h:1948:50: note:   ‘std::_List_iterator<int>’ is not derived from ‘const std::reverse_iterator<_IteratorL>’
 1948 |                                 std::__lg(__last - __first) * 2,
      |                                           ~~~~~~~^~~~~~~~~
/usr/include/c++/13/bits/stl_iterator.h:1800:5: note: candidate: ‘template<class _IteratorL, class _IteratorR> constexpr decltype ((__x.base() - __y.base())) std::operator-(const move_iterator<_IteratorL>&, const move_iterator<_IteratorR>&)’
 1800 |     operator-(const move_iterator<_IteratorL>& __x,
      |     ^~~~~~~~
/usr/include/c++/13/bits/stl_iterator.h:1800:5: note:   template argument deduction/substitution failed:
/usr/include/c++/13/bits/stl_algo.h:1948:50: note:   ‘std::_List_iterator<int>’ is not derived from ‘const std::move_iterator<_IteratorL>’
 1948 |                                 std::__lg(__last - __first) * 2,
      |                                           ~~~~~~~^~~~~~~~~
```

- ★★★ **`std::sort` 는 범주를 제약으로 걸지 않는다** — 몸통 깊은 곳 **`__last - __first`**(임의 접근 이터레이터의 뺄셈)에서 **`no match for ‘operator-’`** 로 터진다. 원인(「`list` 는 임의 접근이 아니다」)은 **그 연산자가 없다**는 증상으로만 보인다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DFORM=2 sort01.cpp -o ex 2>&1 | head -n 8 (cc exit=1) =====
sort01.cpp: In function ‘int main()’:
sort01.cpp:16:22: error: no match for call to ‘(const std::ranges::__sort_fn) (std::__cxx11::list<int>&)’
   16 |     std::ranges::sort(c);
      |     ~~~~~~~~~~~~~~~~~^~~
In file included from /usr/include/c++/13/algorithm:63,
                 from sort01.cpp:2:
/usr/include/c++/13/bits/ranges_algo.h:1781:7: note: candidate: ‘template<class _Iter, class _Sent, class _Comp, class _Proj>  requires (random_access_iterator<_Iter>) && (sentinel_for<_Sent, _Iter>) && (sortable<_Iter, _Comp, _Proj>) constexpr _Iter std::ranges::__sort_fn::operator()(_Iter, _Sent, _Comp, _Proj) const’
 1781 |       operator()(_Iter __first, _Sent __last,
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DFORM=2 sort01.cpp -o ex (cc exit=1) =====
sort01.cpp:16:5: error: no matching function for call to object of type 'const __sort_fn'
   16 |     std::ranges::sort(c);
      |     ^~~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ranges_algo.h:1794:7: note: candidate template ignored: constraints not satisfied [with _Range = std::list<int> &, _Comp = ranges::less, _Proj = identity]
 1794 |       operator()(_Range&& __r, _Comp __comp = {}, _Proj __proj = {}) const
      |       ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ranges_algo.h:1790:14: note: because 'std::list<int> &' does not satisfy 'random_access_range'
 1790 |     template<random_access_range _Range,
      |              ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ranges_base.h:605:37: note: because 'iterator_t<list<int, allocator<int>> &>' (aka '_List_iterator<int>') does not satisfy 'random_access_iterator'
  605 |       = bidirectional_range<_Tp> && random_access_iterator<iterator_t<_Tp>>;
      |                                     ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/iterator_concepts.h:683:10: note: because 'derived_from<__detail::__iter_concept<_List_iterator<int> >, random_access_iterator_tag>' evaluated to false
  683 |       && derived_from<__detail::__iter_concept<_Iter>,
      |          ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:67:28: note: because '__is_base_of(std::random_access_iterator_tag, std::bidirectional_iterator_tag)' evaluated to false
   67 |     concept derived_from = __is_base_of(_Base, _Derived)
      |                            ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/ranges_algo.h:1781:7: note: candidate function template not viable: requires at least 2 arguments, but 1 was provided
 1781 |       operator()(_Iter __first, _Sent __last,
      |       ^          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
 1782 |                  _Comp __comp = {}, _Proj __proj = {}) const
      |                  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1 error generated.
```

- ★★★ **`std::ranges::sort` 는 컨셉으로 막는다** — clang 이 사슬 끝까지 말한다: **`'std::list<int> &' does not satisfy 'random_access_range'`** → **`_List_iterator<int>` does not satisfy `random_access_iterator`** → **`__is_base_of(std::random_access_iterator_tag, std::bidirectional_iterator_tag)` evaluated to false.** **범주가 곧 태그의 상속 관계**라는 것이 진단에 그대로 나온다. 35편 (7)의 「컨셉을 걸면 첫 에러가 호출 줄로」가 여기서도 성립했다.
- ★★ **`list` 에는 멤버 `sort()` 가 따로 있다** — 노드를 **다시 잇는** 정렬이라 임의 접근이 필요 없다.

## 문법 — 형태와 규칙

### 형태

```text
   it = c.erase(it);                           지운 다음 원소의 이터레이터를 받는다 — 모든 컨테이너
   v.erase(std::remove_if(v.begin(), v.end(), pred), v.end());   erase-remove 관용구
   std::erase_if(v, pred);                     C++20 — 지운 수를 돌려준다
   for (auto& x : v) { … }                     몸통에서 v 를 키우지 마라 — begin/end 를 한 번 잡는다
   std::random_access_iterator<It>             C++20 컨셉 — forward · bidirectional · random_access · contiguous
   l.sort();                                   list 는 멤버 sort — std::sort 는 임의 접근이 필요
   -D_GLIBCXX_DEBUG  ·  -D_GLIBCXX_SANITIZE_VECTOR   libstdc++ 의 검사 장치 (표준 밖)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(4)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **`vector` — 재할당이면 전부, 아니면 바뀐 자리부터 뒤가 무효**((1)).
- ★★★ **`deque` — 끝 삽입은 이터레이터만, 가운데는 둘 다 · 끝 삭제는 지운 것만**((1)).
- ★★★ **`list`·`map` — 지워진 것만 · 해시 쪽 rehash 는 이터레이터만**((1)).
- ★★★ **`clear` 는 전부 무효**((1)).
- ★★★ **순회 중 지우기는 `it = c.erase(it)` 또는 `std::erase_if`**((2)).
- ★★ **범위 `for` 몸통에서 같은 컨테이너의 크기를 바꾸지 마라**((3)).
- ★★ **`std::sort` 는 임의 접근 이터레이터 — `list` 는 멤버 `sort()`**((4)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `std::sort(l.begin(), l.end())` — `list` | `no match for ‘operator-’` (`stl_algo.h:1948`) | `invalid operands to binary expression` (`stl_algo.h:1948`) | (4) |
| `std::ranges::sort(l)` — `list` | `no match for call to ‘(const std::ranges::__sort_fn) (…)’` (호출 줄) | `no matching function for call to object of type 'const __sort_fn'` + `does not satisfy 'random_access_range'` | (4) |

## 어디서 틀리나

### 1. ★★★ 「ASan 을 켜면 무효화된 참조를 잡는다」

(1) — **참조 창에서 5 칸을 놓쳤다.** 메모리가 살아 있으면(밀려 온 원소 · 남은 칸) ASan 은 모른다.

### 2. ★★★ 「디버그 모드면 무효화된 이터레이터를 다 잡는다」

(1) — **`unordered_map::rehash()` 를 직접 부른 칸에서 침묵**했다. 넣다가 난 rehash 는 잡았다.

### 3. ★★★ 「`deque` 끝에 넣으면 아무것도 무효가 안 된다」

(1) — **이터레이터는 무효**(디버그 모드가 잡음). 유효한 것은 **참조**다(41편의 「주소 그대로」).

### 4. ★★★ 「`erase` 뒤에 `++it` 해도 다음 칸으로 간다」

(2) — **`attempt to increment a singular iterator`** · ASan 은 `heap-buffer-overflow`. 받아야 할 것은 **`erase` 의 반환값**이다.

### 5. ★★ 「범위 `for` 는 안전하다」

(3) — **몸통에서 `push_back` 하면 `heap-use-after-free`.**

### 6. ★★ 「`std::sort` 는 어떤 컨테이너든 정렬한다」

(4) — **임의 접근만.** `list` 는 멤버 `sort()`, `deque` 는 된다.

### 7. ★ 「실행해 보니 값이 맞았으니 괜찮다」

(1)의 `vector` × 「뒤 삭제」·「끝 추가(용량 안)」은 **명세상 유효**라 맞는 것이고, **「가운데 삽입」 칸의 참조는 명세상 무효인데 ASan 도 침묵**한다. **값이 맞는지로는 두 칸이 구분되지 않는다** — 명세 표가 가른다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 사고는 UB 층에 산다** — 무효화 규칙은 표준이 정하지만 **무효가 된 것을 쓰면 UB** 라 **도구 없이는 아무것도 말할 수 없다.** 그리고 **도구마다 보는 자리가 다르다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **무효화 표 전체 · `erase` 의 반환값 · 범위 `for` 의 풀이 · 이터레이터 범주 · `std::sort` 의 임의 접근 요구** | cppreference 표 · (1)의 명세 열 | — |
| **조건부 표준** | 특정 판에서만 | ★★ **이터레이터 컨셉·`ranges::sort`·`std::erase_if` C++20** | (2)(4) | — |
| **구현 정의 · 라이브러리** | 문서화 의무 없음 | ★★★ **`_GLIBCXX_DEBUG`·`_GLIBCXX_SANITIZE_VECTOR` — 어느 연산을 검사하나** | (1)의 두 창 | ★★★ **`rehash()` 직접 호출은 디버그 모드도 침묵** |
| **컴파일러의 것** | 표준 밖 | ★ **ASan 계측**(두 컴파일러) | (1)(3) | ★★ **ASan 은 해제·경계 밖만 본다 — 밀려 온 원소 · 남은 칸은 못 본다** |
| **UB** | 아무 일이나 | ★★★ **무효가 된 이터레이터·참조를 쓰는 모든 칸** — 값을 싣지 않았다 | 두 도구 | ★★★ **두 도구를 다 켜도 참조 창 4 칸은 침묵** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 조건으로 여러 개 지우기 | ★★★ **`std::erase_if`(C++20)** · 그 전에는 erase-remove | (2) |
| 돌면서 하나씩 판단해 지우기 | ★★★ **`it = c.erase(it)`** | (2) |
| 들고 있는 참조가 삽입을 견뎌야 한다 | ★★ **`deque`(끝 삽입) · `list`·`map`(전부)** | (1) |
| 해시 쪽 이터레이터를 오래 든다 | ★★ **`reserve` 로 rehash 를 막는다** — 참조는 rehash 에도 유효 | (1) |
| 무효화를 의심할 때 | ★★★ **`_GLIBCXX_DEBUG` + ASan 둘 다** — `vector` 는 `_GLIBCXX_SANITIZE_VECTOR` 도 | (1) |
| `list` 정렬 | ★★ **`l.sort()`** | (4) |

## 핵심 문장

- ★★★ **컨테이너 다섯 × 연산 일곱 = 적용 27 칸 · 명세상 무효는 이터레이터 13 · 참조 10.**
- ★★★ **`_GLIBCXX_DEBUG` 는 명세와 1 / 27 칸만 갈렸다 — `unordered_map::rehash()` 직접 호출에서 침묵.**
- ★★★ **ASan 은 참조 창에서 5 / 27 칸을 놓쳤다 — 메모리가 살아 있는 무효화(밀림 · 남은 칸).** `_GLIBCXX_SANITIZE_VECTOR` 가 `vector` × `clear` 하나를 더 잡는다.
- ★★★ **순회 중 `erase` 뒤 `++it` 는 디버그 모드 `attempt to increment a singular iterator` · ASan `heap-buffer-overflow` — 옳은 꼴 넷은 전부 `1 3 5`.**
- ★★★ **범위 `for` 안의 `push_back` 은 `heap-use-after-free` — 옛 버퍼의 다음 원소를 읽는다.**
- ★★ **`std::sort(list)` 는 몸통의 `operator-` 에서(X), `std::ranges::sort(list)` 는 호출 줄에서(O) 터진다 — 범주는 태그의 상속이다.**

## 관련 자료

- [41번](../41-choosing-sequence-containers/) (1) — ★★ **넣는 동안 처음 원소 주소가 바뀌나** — 여기의 격자는 그것을 **연산 일곱 · 이터레이터와 참조**로 넓혔다.
- [42번](../42-associative-containers-ordered-vs-hashed/) (5) — `bucket_count` 가 바뀌는 순간 = rehash.
- [30번](../30-dangling-references-and-lifetime-extension/) — 댕글링 일반 · ASan 의 옵션.
- [35번](../35-instantiation-header-placement-and-reading-errors/) (6) · [36번](../36-concepts-and-requires/) — ★ **컨셉을 걸면 첫 에러가 호출 줄로** — (4)의 `ranges::sort(list)`.
- Rust 갈래 [38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/) — ★★★ **E0502 — 무효화를 컴파일에서 막는다.**
- Java 갈래 [43번](../../../java/syntax/43-iterator-and-fail-fast/) — ★★ **`modCount` · `ConcurrentModificationException` · best-effort.**
- C# 갈래 [31번](../../../csharp/syntax/31-ienumerable-and-foreach/) — ★★ **`_version` 을 `MoveNext` 마다 대조.**

## 용어 풀이

> **이터레이터 무효화(iterator invalidation)** — 컨테이너를 고친 뒤 이터레이터·참조·포인터가 **더 이상 그 원소를 가리킨다고 보장되지 않는 것.** 무효가 된 것을 쓰면 UB.\
> 예: (1)의 명세 열.

> **singular iterator** — libstdc++ 디버그 모드의 말로 「**어느 원소에도 붙어 있지 않다고 표시된 이터레이터**」. 올리거나 역참조하면 멈춘다.\
> 예: (2)의 `state = singular`.

> **이터레이터 범주(iterator category)** — 이터레이터가 할 수 있는 일의 등급. forward → bidirectional → random access → contiguous. 태그 타입의 **상속**으로 표현된다.\
> 예: (4)의 `__is_base_of(…)`.

> **erase-remove 관용구** — `remove_if` 로 남길 것을 앞으로 모으고 `erase` 로 꼬리를 자르는 두 단계.\
> 예: (2)의 `FORM=3`.

> **`_GLIBCXX_DEBUG` · `_GLIBCXX_SANITIZE_VECTOR`** — libstdc++ 의 매크로. 앞은 **이터레이터 상태 추적 컨테이너**로 바꾸고, 뒤는 **`vector` 의 `size()` 밖을 ASan 에 알린다**.\
> 예: (1)의 두 창.

## 더 들어가면

- **`-O2` 의 무효화 격자** — 이 편은 `-O0` 만 던졌다. 30편이 **clang `-O2` + ASan 이 스택 탐침을 놓친** 사례를 보였다 — 힙 쪽은 **던지지 않았다.**
- **`insert` 가 여러 개를 넣을 때 · `emplace` 의 인자가 같은 컨테이너의 원소일 때** — 이 편은 던지지 않았다.
- **`std::string` 의 무효화(SSO)** — 목록 밖. 던지지 않았다.
