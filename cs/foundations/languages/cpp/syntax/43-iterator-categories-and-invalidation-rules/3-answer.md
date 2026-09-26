# cpp/syntax/43 — 이터레이터 범주와 무효화 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·리포트는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **ASan 의 PID·주소·`pc`/`bp`/`sp` · 디버그 모드 리포트의 `@ 0x…` · 진단 문구와 총 줄 수** 다.\
> 근거로 쓰는 것은 다음이다 — **격자의 칸 · `Error:` 줄 · 리포트 이름 · `SUMMARY` 의 `파일:줄` · `run exit` · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **적용 27 칸 — 명세상 이터레이터 무효 13 · 참조 무효 10**(차이 셋 = `deque` 끝 추가 · 해시 쪽 두 rehash) · ★★★ **디버그 모드는 1 칸(`rehash()` 직접)에서 침묵 · ASan 은 5 칸에서 침묵** · ★★ `SANITIZE_VECTOR` 는 **`vector` × `clear`** 를 더 잡는다

**출력**

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

**왜 그런가**

- ★★★ **이터레이터는 「어디에 있나」 까지 들고 있고, 참조는 「그 원소」만 가리킨다** — `deque` 는 끝에 칸을 덧붙이면 **칸 목록(이터레이터가 쓰는 것)** 이 바뀌어도 원소는 그대로다. 해시 쪽 rehash 도 **칸을 다시 나눌 뿐 노드는 안 옮긴다.**
- ★★★ **디버그 모드는 연산마다 「무효로 표시할 이터레이터」를 정한다** — 이 판의 `rehash()` 직접 호출에는 그 표시가 없었다(6번).
- ★★★ **ASan 은 해제·경계 밖만 본다** — 메모리가 살아 있는 무효화는 못 본다(7번).

### 2. ★★★ **`FORM=1` — `Error: attempt to increment a singular iterator.` · `run exit=134` / ASan `heap-buffer-overflow` · `erase01.cpp:20`** · ★★ **`FORM=2..5` 는 전부 `1 3 5 | size 3`**(`FORM=4` 는 앞에 `erase_if 가 돌려준 수 3`)

**출력**

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
===== g++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DFORM=1 erase01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: heap-buffer-overflow erase01.cpp:20 in main
===== clang++ -std=c++20 -O0 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DFORM=1 erase01.cpp -o exa && ./exa 2>&1 | grep -E '^SUMMARY' (cc exit=0 · run exit=1) =====
SUMMARY: AddressSanitizer: heap-buffer-overflow erase01.cpp:20:13 in main
```

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

**왜 그런가**

- ★★★ **`erase(it)` 뒤의 `it` 는 무효** — 디버그 모드는 그것을 **올리는 순간**(원인)을, ASan 은 건너뛰며 **끝을 지나쳐 읽은 순간**(결과)을 잡는다.
- ★★ **옳은 꼴은 전부 「`erase` 가 돌려준 다음 이터레이터」를 쓰거나 알고리즘에 맡긴다.**

### 3. ★★★ **`capacity 3` · `x = 1` 두 줄 뒤 `heap-use-after-free` · `rfor01.cpp:8`** — `freed by` 에 **`_M_realloc_insert` → `push_back`(`rfor01.cpp:9`)** · ★★ 디버그 모드는 **`Error: attempt to increment a singular iterator.`**

**출력**

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

**왜 그런가**

- ★★★ **범위 `for` 는 `begin()`·`end()` 를 처음에 한 번 잡는다** — 첫 몸통의 `push_back(4)` 가 capacity 3 을 넘겨 **재할당**하자 그 둘이 **해제된 옛 버퍼**를 가리키게 됐다. 다음 반복의 `*__begin` 이 `heap-use-after-free`, 디버그 모드에서는 그 앞의 `++__begin` 이 먼저 걸린다.

### 4. ★★ **`array`·`vector` 1 1 1 1 · `deque` 1 1 1 0 · `list`·`map` 1 1 0 0 · `forward_list`·`unordered_map` 1 0 0 0**

**출력**

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

**왜 그런가**

- ★★ **`deque` 는 번호로 바로 가지만(임의 접근) 연속이 아니다** — 41편 (1)의 200 개 행과 같은 사실을 **컨셉**이 말한다.

### 5. ★★★ **`FORM=1`(`std::sort`)과 `FORM=2`(`std::ranges::sort`)가 에러 — 앞은 `stl_algo.h:1948`(X), 뒤는 `sort01.cpp:16`(호출 줄 · O)** · `list.sort()` 와 `std::sort(deque)` 는 `1 2 3`

**출력**

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

**왜 그런가**

- ★★★ **`std::sort` 는 이터레이터 범주를 제약으로 걸지 않는다** — 몸통의 `__last - __first` 에서 **연산자가 없다**로 터진다. **`std::ranges::sort` 는 `random_access_range` 컨셉**을 호출 자리에서 검사한다.

### 6. ★★★ **「안전」이 아니라 「그 자리를 검사하지 않았다」로 읽는다** — 명세가 무효라고 하면 무효다

- ★★★ 두 칸 다 `bucket_count` 가 바뀌었다(`103 -> 1031` · `13 -> 29`). **같은 사건인데 검사기가 한쪽 경로에만 표시를 달았다** — 검사기의 침묵은 **몇 군데를 물었나**를 따로 확인해야 뜻이 있다(규칙 18-A). 그래서 격자에 **명세 열**을 따로 뒀다.

### 7. ★★★ **ASan 은 「해제된 메모리」와 「할당 경계 밖」을 본다 — 가운데 삽입은 아무것도 해제하지 않는다.** 원소가 한 칸씩 밀렸을 뿐이라 참조가 가리키는 자리는 **살아 있는 `int`** 다

- ★★ `_GLIBCXX_SANITIZE_VECTOR` 는 **`size()` 밖**까지 ASan 에 알리지만, 밀려 온 원소는 **`size()` 안**이라 그래도 못 본다. **어떤 도구도 「다른 원소를 가리키게 됐다」는 보지 않는다** — 명세 표가 유일한 근거다.

### 8. ★★ **`erase` 는 「지운 다음 원소」의 유효한 이터레이터를 돌려준다** — 무효가 된 `it` 를 버리고 새 것으로 갈아탄다. ★★ `std::remove_if` 는 **이터레이터만 받는 알고리즘**이라 컨테이너의 크기를 바꿀 수 없다 — 남길 것을 앞으로 모으고 **새 끝**을 돌려줄 뿐이다

### 9. ★★ **제약(컨셉)이 있느냐** — `std::ranges::sort` 는 `random_access_range` 를 **선언에** 걸어 호출 자리에서 거절하고, `std::sort` 는 **몸통에서 쓰다가** 터진다

- ★★ 35편 (7)의 「컨셉을 걸면 첫 에러가 호출 줄로」 · clang 이 사슬 끝까지 **`__is_base_of(std::random_access_iterator_tag, std::bidirectional_iterator_tag)` evaluated to false** 를 보였다(요약 (4)).

### 10. ★★ **말할 수 없다 — 무효가 된 것을 쓰는 것은 UB 다.** 도구가 침묵하는 칸이 있다는 것은 1번이 보였고, **값이 맞은 것은 「이 판의 우연」** 일 뿐이다

- ★★ 1번의 `vector` × 「뒤 삭제」 칸(명세상 **유효**)과 「가운데 삽입」 칸(명세상 **무효** · ASan 침묵)은 **실행만으로는 구분되지 않는다.** 가르는 것은 명세 표다.

### 11. 다른 주제와 잇기

- ★★★ **Rust** — **컴파일 단계 · E0502**([Rust 38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/) (4) — `for` 안의 `remove`).
- ★★ **Java** — **실행 단계 · `ConcurrentModificationException`** — 단 `hasNext()` 는 대조하지 않아 **끝에서 두 번째를 지우면 예외 없이 건너뛴다**([Java 43번](../../../java/syntax/43-iterator-and-fail-fast/)).
- ★★ **C#** — **실행 단계 · `List<T>._version` 대조** — 끝에서 두 번째에서도 던진다([C# 31번](../../../csharp/syntax/31-ienumerable-and-foreach/)).
- ★ **C++ 보통 빌드는 아무 단계에서도 막지 않는다** — `_GLIBCXX_DEBUG` 를 켜야 C# 과 같은 일을 한다.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `inv01.cpp` + `inv-grid.sh` | 5 × 7 × 컴파일러 2 × 창 3(빌드 6 · 실행 210) | ★★★ **적용 27 · 명세상 무효 13 / 10 · 명세와 갈린 칸 1 · 5(`SV` 4) · 갈린 행 0 / 35** |
| `inv01.cpp` rehash 두 판 | g++ 디버그 | ★★★ **직접 `rehash` 침묵 · 넣다가 rehash 잡음** |
| `erase01.cpp` | 두 컴파일러 × (디버그 · ASan · 보통 넷) | ★★★ **`singular` · `heap-buffer-overflow` · `1 3 5` 넷** |
| `rfor01.cpp` | 두 컴파일러 × (ASan · 디버그) | ★★★ **`heap-use-after-free rfor01.cpp:8`** |
| `cat01.cpp` · `sort01.cpp` + `sort-grid.sh` | 두 컴파일러 | ★★ **컨셉 표 · 실패 4 / 8 중 호출 줄 2** |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **디버그 모드가 검사하는 자리 · `SANITIZE_VECTOR` 의 범위 · 진단 문구.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **무효화 표 · `erase` 의 반환값 · 범위 `for` 의 풀이 · 이터레이터 범주 · `std::sort` 의 임의 접근 요구.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `-O2` 의 격자 · 여러 개 `insert` · `std::string`.
- **못 잰 것** — libc++ 의 디버그 모드(libc++ 없음).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 격자** — 특히 **디버그 모드의 `rehash()` 칸.**
