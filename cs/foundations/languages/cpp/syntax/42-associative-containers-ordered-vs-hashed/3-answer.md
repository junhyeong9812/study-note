# cpp/syntax/42 — 연관 컨테이너 — 정렬 vs 해시 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구와 총 줄 수 · 디버그 모드 리포트의 `@ 0x…` 주소** 다.\
> 근거로 쓰는 것은 다음이다 — **통과 칸 · 첫 error 의 O/X · `cc exit`/`run exit` · `Error:` 줄 · 격자의 마지막 줄**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **통과 12 / 48 — 정렬 쪽은 `<` 또는 `<=>`, 해시 쪽은 `hash` + `==`** · ★★ 해시 쪽의 `hash` 누락은 **내 파일의 선언 줄**, 정렬 쪽과 `==` 누락은 **표준 헤더(`stl_function.h`)** 를 가리킨다

**출력**

```bash
# key-grid.sh
# key-grid.sh — P 에 준 것 여섯 × 컨테이너 넷 × 컴파일러 둘. 칸: 통과면 찍힌 값, 에러면 「첫 error 의 파일:줄 · 내 파일인가(O/X)」
gives=('1 아무것도' '2 operator<' '3 operator==' '4 std::hash<P>' '5 std::hash<P> + ==' '6 <=> = default')
conts=('1 set' '2 map' '3 unordered_set' '4 unordered_map')
cell() {
  local out rc first
  out=$($1 -std=c++20 -Wall -Wextra -pedantic -DGIVE=$2 -DCONT=$3 key01.cpp -o kx 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then printf '%s' "$(./kx)"; return; fi
  first=$(printf '%s\n' "$out" | grep -m 1 ': error: ' | sed -E 's#^([^:]*/)?([^/:]+):([0-9]+):.*#\2:\3#')
  case "$first" in key01.cpp:*) printf '에러 %s O' "$first" ;; *) printf '에러 %s X' "$first" ;; esac
}
printf '%s\t%s\t%s\t%s\n' "준 것" "컨테이너" "g++" "clang++" > t.tsv
for g in "${gives[@]}"; do
  for c in "${conts[@]}"; do
    printf '%s\t%s\t%s\t%s\n' "$g" "$c" "$(cell g++ ${g%% *} ${c%% *})" "$(cell clang++ ${g%% *} ${c%% *})" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 4' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
pass=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i !~ /^에러/) n++ } END { print n+0 }')
err=$(( rows * 2 - pass ))
mine=$(tail -n +2 t.tsv | awk -F'\t' '{ for (i=3;i<=4;i++) if ($i ~ /^에러.* O$/) n++ } END { print n+0 }')
split=$(tail -n +2 t.tsv | awk -F'\t' '($3 ~ /^에러/) != ($4 ~ /^에러/)' | wc -l)
echo "통과 칸 $pass / $(( rows * 2 )) · 에러 칸 중 첫 error 가 내 파일 $mine / $err · 통과 여부가 컴파일러 사이 갈린 행 $split / $rows"
rm -f kx t.tsv
```

```text
===== bash key-grid.sh (exit=0) =====
준 것	컨테이너	g++	clang++
1 아무것도	1 set	에러 stl_function.h:408 X	에러 stl_function.h:408 X
1 아무것도	2 map	에러 stl_function.h:408 X	에러 stl_function.h:408 X
1 아무것도	3 unordered_set	에러 key01.cpp:36 O	에러 key01.cpp:36 O
1 아무것도	4 unordered_map	에러 key01.cpp:39 O	에러 key01.cpp:39 O
2 operator<	1 set	size 1 · find 1	size 1 · find 1
2 operator<	2 map	size 1 · find 1	size 1 · find 1
2 operator<	3 unordered_set	에러 key01.cpp:36 O	에러 key01.cpp:36 O
2 operator<	4 unordered_map	에러 key01.cpp:39 O	에러 key01.cpp:39 O
3 operator==	1 set	에러 stl_function.h:408 X	에러 stl_function.h:408 X
3 operator==	2 map	에러 stl_function.h:408 X	에러 stl_function.h:408 X
3 operator==	3 unordered_set	에러 key01.cpp:36 O	에러 key01.cpp:36 O
3 operator==	4 unordered_map	에러 key01.cpp:39 O	에러 key01.cpp:39 O
4 std::hash<P>	1 set	에러 stl_function.h:408 X	에러 stl_function.h:408 X
4 std::hash<P>	2 map	에러 stl_function.h:408 X	에러 stl_function.h:408 X
4 std::hash<P>	3 unordered_set	에러 stl_function.h:378 X	에러 stl_function.h:378 X
4 std::hash<P>	4 unordered_map	에러 stl_function.h:378 X	에러 stl_function.h:378 X
5 std::hash<P> + ==	1 set	에러 stl_function.h:408 X	에러 stl_function.h:408 X
5 std::hash<P> + ==	2 map	에러 stl_function.h:408 X	에러 stl_function.h:408 X
5 std::hash<P> + ==	3 unordered_set	size 1 · find 1	size 1 · find 1
5 std::hash<P> + ==	4 unordered_map	size 1 · find 1	size 1 · find 1
6 <=> = default	1 set	size 1 · find 1	size 1 · find 1
6 <=> = default	2 map	size 1 · find 1	size 1 · find 1
6 <=> = default	3 unordered_set	에러 key01.cpp:36 O	에러 key01.cpp:36 O
6 <=> = default	4 unordered_map	에러 key01.cpp:39 O	에러 key01.cpp:39 O
통과 칸 12 / 48 · 에러 칸 중 첫 error 가 내 파일 16 / 36 · 통과 여부가 컴파일러 사이 갈린 행 0 / 24
```

**왜 그런가**

- ★★★ **`std::less<P>` 는 `<` 를, `std::hash<P>`·`std::equal_to<P>` 는 특수화와 `==` 를 부른다** — 없는 것을 부르는 순간이 **라이브러리 안**이라 첫 에러가 헤더를 가리킨다(35편의 「제약 없는 템플릿은 몸통에서 터진다」).
- ★★★ **해시 쪽의 `hash` 누락만 선언 줄(O)** — 6번.
- ★★ **`<=>` 는 `<` 와 `==` 를 주지만 `hash` 는 주지 않는다** — 여섯째 행이 정렬 쪽만 통과한다.

### 2. ★★ **`map : 1 3 17 29 42 50 88` · `unordered_map: 1 88 17 29 42 3 50` · 18 판 모두 1 가지**

**출력**

```bash
# order-grid.sh
# order-grid.sh — order01.cpp 를 컴파일러 셋(g++ 13 · clang++ 18 · g++-12) × 최적화 둘 로 빌드해 판마다 세 번 돌린다. 줄마다 서로 다른 가짓수를 센다
: > all.txt
runs=0
for c in g++ clang++ g++-12; do
  for o in -O0 -O2; do
    $c -std=c++20 -Wall -Wextra -pedantic $o order01.cpp -o ox || { echo "cc 에러"; exit 1; }
    for i in 1 2 3; do ./ox >> all.txt || exit 1; runs=$(( runs + 1 )); done
  done
done
./ox
for tag in 'map          :' 'unordered_map:' 'unordered_map bucket_count'; do
  n=$(grep -F "$tag" all.txt | sort -u | wc -l)
  printf '「%s」 줄 — %d 판 중 서로 다른 가짓수 %d\n' "$tag" "$runs" "$n"
done
rm -f ox all.txt
```

```text
===== bash order-grid.sh (exit=0) =====
map          : 1 3 17 29 42 50 88
unordered_map: 1 88 17 29 42 3 50
unordered_map bucket_count = 13
「map          :」 줄 — 18 판 중 서로 다른 가짓수 1
「unordered_map:」 줄 — 18 판 중 서로 다른 가짓수 1
「unordered_map bucket_count」 줄 — 18 판 중 서로 다른 가짓수 1
```

**왜 그런가**

- ★★ **`map` 은 비교자 순서로 저장한다** — 넣은 순서와 무관하다.
- ★★ **`unordered_map` 의 순서는 칸 번호와 칸끼리 잇는 방식이 정하는 구현의 순서**다 — **libstdc++ 는 실행마다 섞지 않아** 18 판이 같았다. 보장이 아니다(8번).

### 3. ★★★ **size 1 → 2 → 2 → 2 → 2 — `m["b"]` 에서만 늘었다 · `at("c")` 는 `out_of_range what() = map::at`** · ★★ `-DCONSTMAP` 판은 **컴파일 에러**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
시작          size 1
m["b"] 읽기   size 2 · 값 0
m.at("c")     size 2 · out_of_range what() = map::at
m.find("d")   size 2 · 찾았나 0
contains("e") size 2 · 있나 0
===== clang++ -std=c++20 -Wall -Wextra -pedantic sub01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
시작          size 1
m["b"] 읽기   size 2 · 값 0
m.at("c")     size 2 · out_of_range what() = map::at
m.find("d")   size 2 · 찾았나 0
contains("e") size 2 · 있나 0
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DCONSTMAP sub01.cpp -o ex (cc exit=1) =====
sub01.cpp: In function ‘int main()’:
sub01.cpp:11:32: error: passing ‘const std::map<std::__cxx11::basic_string<char>, int>’ as ‘this’ argument discards qualifiers [-fpermissive]
   11 |     std::printf("%d\n", cm["zz"]);
      |                                ^
In file included from /usr/include/c++/13/map:63,
                 from sub01.cpp:3:
/usr/include/c++/13/bits/stl_map.h:524:7: note:   in call to ‘std::map<_Key, _Tp, _Compare, _Alloc>::mapped_type& std::map<_Key, _Tp, _Compare, _Alloc>::operator[](key_type&&) [with _Key = std::__cxx11::basic_string<char>; _Tp = int; _Compare = std::less<std::__cxx11::basic_string<char> >; _Alloc = std::allocator<std::pair<const std::__cxx11::basic_string<char>, int> >; mapped_type = int; key_type = std::__cxx11::basic_string<char>]’
  524 |       operator[](key_type&& __k)
      |       ^~~~~~~~
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DCONSTMAP sub01.cpp -o ex (cc exit=1) =====
sub01.cpp:11:27: error: no viable overloaded operator[] for type 'const std::map<std::string, int>' (aka 'const map<basic_string<char>, int>')
   11 |     std::printf("%d\n", cm["zz"]);
      |                         ~~^~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_map.h:504:7: note: candidate function not viable: 'this' argument has type 'const std::map<std::string, int>' (aka 'const map<basic_string<char>, int>'), but method is not marked const
  504 |       operator[](const key_type& __k)
      |       ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_map.h:524:7: note: candidate function not viable: 'this' argument has type 'const std::map<std::string, int>' (aka 'const map<basic_string<char>, int>'), but method is not marked const
  524 |       operator[](key_type&& __k)
      |       ^
1 error generated.
```

**왜 그런가**

- ★★★ **`operator[]` 는 「없으면 `T()` 를 넣고 그 참조를 돌려준다」** — 읽기만 해도 넣는다. 그래서 **`const map` 에는 그 멤버가 없다**(넣을 수 있는 함수는 `const` 일 수 없다).
- ★★ **`at`·`find`·`contains` 는 넣지 않는다.** `what()` 의 `map::at` 은 libstdc++ 의 문자열이다.

### 4. ★★ **보통 빌드는 세 줄 다 찍고 `run exit=0` · 디버그 빌드는 두 줄 뒤 `sort` 에서 `Error: comparison doesn't meet irreflexive requirements` · `run exit=134`** — 멈춘 자리는 **`sort`**

**출력**

```cpp
/* swo01.cpp */
// 엄격 약순서를 어기는 비교자(<=) — 비교자 자체의 값을 찍고, set 에 같은 키를 두 번 넣고, 같은 비교자로 정렬한다
#include <algorithm>
#include <cstdio>
#include <set>
#include <vector>

struct LessEq {
    bool operator()(int a, int b) const { return a <= b; }
};

int main() {
    LessEq c;
    std::fprintf(stderr, "c(1, 1) = %d · 동치 판정 !c(1,1) && !c(1,1) = %d\n", c(1, 1), !c(1, 1) && !c(1, 1));
    std::set<int, LessEq> s;
    s.insert(1);
    s.insert(1);
    std::fprintf(stderr, "set 에 1 을 두 번 넣었다\n");
    std::vector<int> v{3, 1, 2, 1};
    std::sort(v.begin(), v.end(), LessEq{});
    std::fprintf(stderr, "sort 가 끝났다\n");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic swo01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
c(1, 1) = 1 · 동치 판정 !c(1,1) && !c(1,1) = 0
set 에 1 을 두 번 넣었다
sort 가 끝났다
===== clang++ -std=c++20 -Wall -Wextra -pedantic swo01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
c(1, 1) = 1 · 동치 판정 !c(1,1) && !c(1,1) = 0
set 에 1 을 두 번 넣었다
sort 가 끝났다
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG swo01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
c(1, 1) = 1 · 동치 판정 !c(1,1) && !c(1,1) = 0
set 에 1 을 두 번 넣었다
/usr/include/c++/13/bits/stl_algo.h:4892:
In function:
    constexpr void std::sort(_RAIter, _RAIter, _Compare) [with _RAIter = 
    gnu_debug::_Safe_iterator<gnu_cxx::normal_iterator<int*, vector<int, 
    allocator<int> > >, debug::vector<int>, random_access_iterator_tag>; 
    _Compare = LessEq]

Error: comparison doesn't meet irreflexive requirements, assert(!(a < a)).

Objects involved in the operation:
    instance "functor" @ 0x7ffc2fd15d1f {
      type = LessEq;
    }
    iterator::value_type "ordered type"  {
      type = int;
    }
===== clang++ -std=c++20 -Wall -Wextra -pedantic -D_GLIBCXX_DEBUG swo01.cpp -o ex && ./ex (cc exit=0 · run exit=134) =====
c(1, 1) = 1 · 동치 판정 !c(1,1) && !c(1,1) = 0
set 에 1 을 두 번 넣었다
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:4892:
In function:
    void std::sort(_RandomAccessIterator, _RandomAccessIterator, _Compare) 
    [_RandomAccessIterator = gnu_debug::_Safe_iterator<gnu_cxx::
    normal_iterator<int *, std::vector<int>>, std::vector<int>>, _Compare = 
    LessEq]

Error: comparison doesn't meet irreflexive requirements, assert(!(a < a)).

Objects involved in the operation:
    instance "functor" @ 0x7ffd5b4753df {
      type = LessEq;
    }
    iterator::value_type "ordered type"  {
      type = int;
    }
```

**왜 그런가**

- ★★ **`c(1, 1) = 1`** 이 비반사성을 깬다. 컴파일러는 비교자의 **값**을 모른다 — 보통 빌드는 침묵한다.
- ★★ **libstdc++ 디버그 모드는 이 판에서 `sort` 에 `!(a < a)` 단언을 둔다** — `set::insert` 에는 그 검사가 없었다(두 줄째 「set 에 1 을 두 번 넣었다」가 먼저 찍혔다).

### 5. ★★ **둘 다 `bucket_count 1109` · `load_factor 0.902` — `std::hash<int>` 는 빈 아닌 버킷 1000 · 가장 큰 1, `Zero` 는 빈 아닌 버킷 1 · 가장 큰 1000**

**출력**

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic hash01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::hash<int>  size 1000 · bucket_count 1109 · 빈 아닌 버킷 1000 · 가장 큰 버킷 1 · load_factor 0.902
Zero            size 1000 · bucket_count 1109 · 빈 아닌 버킷 1 · 가장 큰 버킷 1000 · load_factor 0.902
===== clang++ -std=c++20 -Wall -Wextra -pedantic hash01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::hash<int>  size 1000 · bucket_count 1109 · 빈 아닌 버킷 1000 · 가장 큰 버킷 1 · load_factor 0.902
Zero            size 1000 · bucket_count 1109 · 빈 아닌 버킷 1 · 가장 큰 버킷 1000 · load_factor 0.902
```

**왜 그런가**

- ★★ **칸 수는 원소 수만 보고 늘린다** — 해시가 나빠도 똑같이 1109 로 늘었다. 그래서 **적재율도 같다.**
- ★★ **`Zero` 는 계약(같은 키 → 같은 해시)을 지킨다** — 틀린 것이 아니라 **분포가 나쁜 것**이라 어떤 도구도 에러를 내지 않는다.

### 6. ★★★ **`std::hash<P>` 를 안 주면 그 특수화는 disabled 이고, disabled 특수화는 기본 생성이 안 된다** — 해시 컨테이너의 기본 생성자가 그것을 기본 생성하려다 **지워진다**

- ★★★ cppreference 「**If std::hash<Key> is not provided by the program or the user, it is disabled.**」 · 「**Disabled specializations … `std::is_default_constructible<std::hash<Key>>::value` … false**」.
- ★★ 그래서 에러 문구가 **「해시가 없다」가 아니라 「기본 생성자가 지워졌다」** 다 — g++ `use of deleted function ‘…unordered_set()’` · clang `call to implicitly-deleted default constructor`.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=3 key01.cpp -o ex 2>&1 | head -n 2 (cc exit=1) =====
key01.cpp: In function ‘int main()’:
key01.cpp:36:27: error: use of deleted function ‘std::unordered_set<_Value, _Hash, _Pred, _Alloc>::unordered_set() [with _Value = P; _Hash = std::hash<P>; _Pred = std::equal_to<P>; _Alloc = std::allocator<P>]’
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=3 key01.cpp -o ex 2>&1 | head -n 3 (cc exit=1) =====
key01.cpp:36:27: error: call to implicitly-deleted default constructor of 'std::unordered_set<P>'
   36 |     std::unordered_set<P> c;
      |                           ^
===== echo "g++ 총 줄 $(g++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=3 key01.cpp -o ex 2>&1 | wc -l) · clang++ 총 줄 $(clang++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=3 key01.cpp -o ex 2>&1 | wc -l)" (exit=0) =====
g++ 총 줄 126 · clang++ 총 줄 114
```

### 7. ★★ **해시는 칸 번호일 뿐 — 같은 칸의 원소 중 「같은 키」를 가리려면 `==` 가 필요하다.** 정렬 쪽은 **동치 `!comp(a,b) && !comp(b,a)`** 로 판정해 `==` 를 안 쓴다

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=4 -DCONT=3 key01.cpp -o ex (cc exit=1) =====
In file included from /usr/include/c++/13/functional:49,
                 from key01.cpp:5:
/usr/include/c++/13/bits/stl_function.h: In instantiation of ‘constexpr bool std::equal_to<_Tp>::operator()(const _Tp&, const _Tp&) const [with _Tp = P]’:
/usr/include/c++/13/bits/hashtable_policy.h:1715:16:   required from ‘bool std::__detail::_Hashtable_base<_Key, _Value, _ExtractKey, _Equal, _Hash, _RangeHash, _Unused, _Traits>::_M_key_equals(const _Key&, const std::__detail::_Hash_node_value<_Value, typename _Traits::__hash_cached::value>&) const [with _Key = P; _Value = P; _ExtractKey = std::__detail::_Identity; _Equal = std::equal_to<P>; _Hash = std::hash<P>; _RangeHash = std::__detail::_Mod_range_hashing; _Unused = std::__detail::_Default_ranged_hash; _Traits = std::__detail::_Hashtable_traits<false, true, true>; typename _Traits::__hash_cached = std::__detail::_Hashtable_traits<false, true, true>::__hash_cached]’
/usr/include/c++/13/bits/hashtable.h:1672:29:   required from ‘std::_Hashtable<_Key, _Value, _Alloc, _ExtractKey, _Equal, _Hash, _RangeHash, _Unused, _RehashPolicy, _Traits>::iterator std::_Hashtable<_Key, _Value, _Alloc, _ExtractKey, _Equal, _Hash, _RangeHash, _Unused, _RehashPolicy, _Traits>::find(const key_type&) [with _Key = P; _Value = P; _Alloc = std::allocator<P>; _ExtractKey = std::__detail::_Identity; _Equal = std::equal_to<P>; _Hash = std::hash<P>; _RangeHash = std::__detail::_Mod_range_hashing; _Unused = std::__detail::_Default_ranged_hash; _RehashPolicy = std::__detail::_Prime_rehash_policy; _Traits = std::__detail::_Hashtable_traits<false, true, true>; iterator = std::__detail::_Insert_base<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true> >::iterator; key_type = P]’
/usr/include/c++/13/bits/unordered_set.h:658:25:   required from ‘std::unordered_set<_Value, _Hash, _Pred, _Alloc>::iterator std::unordered_set<_Value, _Hash, _Pred, _Alloc>::find(const key_type&) [with _Value = P; _Hash = std::hash<P>; _Pred = std::equal_to<P>; _Alloc = std::allocator<P>; iterator = std::__detail::_Insert_base<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true> >::iterator; key_type = P]’
key01.cpp:42:58:   required from here
/usr/include/c++/13/bits/stl_function.h:378:20: error: no match for ‘operator==’ (operand types are ‘const P’ and ‘const P’)
  378 |       { return __x == __y; }
      |                ~~~~^~~~~~
```

- ★★ 첫 에러가 **`std::equal_to<P>` 안의 `__x == __y`** 다(`stl_function.h:378`).

### 8. ★★★ **말할 수 없다 — 이 머신의 세 판은 libstdc++ 한 계열이다.** 명세는 「**not sorted in any particular order**」라고만 적는다

- ★★★ [Go 09번](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/) — **명세가 순서를 정하지 않고 gc 가 일부러 섞는다**(3 개 키 600 판에서 3 가지). [Rust 39번](../../../rust/syntax/39-hashmap-vs-btreemap-and-entry-api/) — **`HashMap` 은 프로세스 300 개에서 6 가지.** libstdc++ 는 섞지 않았을 뿐이다 — **그래서 가장 잘 속는다.**

### 9. ★★ **가를 수 없다 — 두 줄의 `load_factor` 가 0.902 로 같다.** 봐야 할 것은 **`bucket_size` 분포**(빈 아닌 버킷 수 · 가장 큰 버킷)다

### 10. ★★ **말할 수 없다 — 디버그 모드가 그 자리를 검사하지 않았을 뿐이다.** 요구사항 위반은 UB 이고, **같은 비교자가 `sort` 에서는 잡혔다**

- ★★ **「침묵」은 「검사했는데 통과」가 아니라 「검사 안 함」일 수 있다** — 18-A 의 「몇 군데 물었나」.

### 11. 다른 주제와 잇기

- ★★ **칸 수가 바뀌는 순간이 rehash** 다 — 43편 격자의 **`unordered_map` × 「끝에 추가(재할당·rehash)」** 행이 그 순간을 일부러 만들어 이터레이터 무효화를 본다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic bucket01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 bucket_count 1 · max_load_factor 1.0
size   1 에서 bucket_count  13
size  14 에서 bucket_count  29
size  30 에서 bucket_count  59
size  60 에서 bucket_count 127
size 128 에서 bucket_count 257
===== clang++ -std=c++20 -Wall -Wextra -pedantic bucket01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 bucket_count 1 · max_load_factor 1.0
size   1 에서 bucket_count  13
size  14 에서 bucket_count  29
size  30 에서 bucket_count  59
size  60 에서 bucket_count 127
size 128 에서 bucket_count 257
```

- ★ **트리는 [`data-structure/06-binary-search-tree/`](../../../../../data-structure/06-binary-search-tree/)·[`16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/), 해시는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)** 가 정본이다 — 여기는 **표준 컨테이너가 키에게 요구하는 것**만.

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `key01.cpp` + `key-grid.sh` | 6 × 4 × 컴파일러 2 | ★★★ **통과 12 / 48 · 내 파일 16 / 36 · 갈린 행 0 / 24** |
| `order01.cpp` + `order-grid.sh` | 컴파일러 3 × 최적화 2 × 3 번 | ★★ **18 판 모두 1 가지** |
| `sub01.cpp` | 두 컴파일러 + `-DCONSTMAP` | ★★★ **size 2 · `out_of_range` · const 에러** |
| `swo01.cpp` | 두 컴파일러 × 보통 / `_GLIBCXX_DEBUG` | ★★ **`sort` 에서만 잡힘** |
| `hash01.cpp` · `bucket01.cpp` | 두 컴파일러 | ★★ **버킷 1 개에 1000 · 적재율 같음 · 1 → 13 → 29 → …** |

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **해시 순회 순서 · `bucket_count` 수열 · `what()` 문자열 · 디버그 모드가 검사하는 자리.**

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **키 요구사항 · disabled `hash` · `map` 키 순 · `operator[]` 는 넣는다 · `at` 은 `out_of_range`.**

**안 돌려 본 것 / 못 잰 것**

- **못 잰 것** — 다른 표준 라이브러리의 순서·버킷(libc++ 없음).
- **안 돌려 본 것** — **시간** · 비교 횟수 · 이질 탐색 · `try_emplace`.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **2번 가짓수 · 4번 디버그 모드 · 5번 버킷 수열.**
