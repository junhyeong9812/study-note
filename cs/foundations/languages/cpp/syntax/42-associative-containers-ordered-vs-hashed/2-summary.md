# cpp/syntax/42 — 연관 컨테이너 — 정렬 vs 해시 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `std::map`](https://en.cppreference.com/w/cpp/container/map) · [`std::unordered_map`](https://en.cppreference.com/w/cpp/container/unordered_map) · [`std::hash`](https://en.cppreference.com/w/cpp/utility/hash) · [Compare 요구사항](https://en.cppreference.com/w/cpp/named_req/Compare) · [`map::operator[]`](https://en.cppreference.com/w/cpp/container/map/operator_at) · [`map::at`](https://en.cppreference.com/w/cpp/container/map/at)\
> ★ 이 배치에서 **위 cppreference 쪽들을 열어 확인했다** — `map` 은 「**Keys are sorted by using the comparison function Compare. Search, removal, and insertion operations have logarithmic complexity.**」 · `unordered_map` 은 「**average constant-time complexity**」 · 「**Internally, the elements are not sorted in any particular order, but organized into buckets.**」 · `std::hash` 는 「**If std::hash<Key> is not provided by the program or the user, it is disabled.**」 · 「**Disabled specializations … `std::is_default_constructible<std::hash<Key>>::value` … false**」 · 「**If k1 == k2 is true, h(k1) == h(k2) is also true.**」 · Compare 는 「**Establishes strict weak ordering relation**」 · `operator[]` 는 「**Inserts value_type(key, T()) if the key does not exist.**」 · `at` 은 「**If no such element exists, an exception of type std::out_of_range is thrown.**」
> **실행 검증** — 이 문서의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★★ clang 도 같은 라이브러리 — 해시 순회 순서·버킷 수는 **한 구현 계열**이다. `g++-12` 만 libstdc++ 12 헤더) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`key01.cpp`·`order01.cpp`·`sub01.cpp`·`swo01.cpp`·`hash01.cpp`·`bucket01.cpp`·`key-grid.sh`·`order-grid.sh`). 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — `map`·`set` 은 **C++98**, `unordered_*`·`std::hash` 는 **C++11**, `contains` 와 `operator<=>` 는 **C++20** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **정본 경계** — **해시 테이블과 이진 탐색 트리의 원리**(버킷 · 체이닝 · 적재율 · 리사이즈 · 트리 탐색 · 균형)는 [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/)·[`06-binary-search-tree/`](../../../../../data-structure/06-binary-search-tree/)·[`16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/)가 정본이다(★ 그쪽은 **Java 로 직접 구현** — `hashCode`/`equals` 의 약속까지). **여기는 표준 컨테이너가 키에게 요구하는 것** — 비교자 대 `hash`+`==` · 어기면 무엇이 나오나.
> 선행 — [41번](../41-choosing-sequence-containers/)(컨테이너를 고르는 기준 — 할당·연속·주소). [23번](../23-three-way-comparison-spaceship/)(`<=>` `= default`)이 (1)의 여섯째 행으로 돌아온다. [35번](../35-instantiation-header-placement-and-reading-errors/)의 **「첫 에러가 내 파일을 가리키나(O/X)」** 를 (1)의 격자가 쓴다.
> ★★★ **「`unordered_map` 이 `map` 보다 빠르다」는 이 문서가 싣지 않는다 — 시간을 재지 않았다.** 나쁜 해시도 **버킷 분포**로만 보인다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구와 총 줄 수** · `_GLIBCXX_DEBUG` 리포트의 **`@ 0x…` 주소** | ★★★ **통과 칸 · 첫 error 가 내 파일인가(O/X) · `cc exit`/`run exit` · 격자의 마지막 줄** · 리포트의 **`Error:` 줄** |
> | ★ `unordered_map` 의 **순회 순서·`bucket_count` 수열** — **libstdc++ 의 관찰**(18 판 1 가지였지만 보장이 아니다) | ★★★ **`map` 은 키 순 · `operator[]` 는 넣는다 · `at` 은 `out_of_range`** — 명세 |

## 한눈에 — 쉽게 말하면

**연관 컨테이너는 「사물함」이다 — 정렬 사물함과 해시 사물함 두 종류.**

- **`map`·`set`(정렬)** — 사물함이 **이름 가나다순으로 늘어서 있다.** 찾을 때 **「앞이냐 뒤냐」만 물으면**(비교자 `<`) 된다. 순서대로 훑으면 **늘 가나다순**이다.
- **`unordered_map`·`unordered_set`(해시)** — **이름을 공식에 넣어 몇 번 칸인지 계산**하고(`hash`), 그 칸에서 **「같은 이름인가」를 물어**(`==`) 꺼낸다. 칸 번호가 공식 따라 흩어지니 **훑으면 순서가 제멋대로**다.
- **공식이 엉터리면**(항상 0) — 모두 **0 번 칸 하나에 몰린다.** 사물함 수도 적재율도 멀쩡해 보이는데 **한 칸만 1000 명**이다((5)).
- **`m[k]` 는 「보여 줘」가 아니라 「없으면 만들어」다** — 물어보기만 했는데 사물함이 하나 늘어난다((3)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 가나다순 사물함 · 「앞이냐 뒤냐」 | ★★★ **`map`·`set` — 비교자(엄격 약순서) 하나** | (1)(2) |
| 칸 번호 공식 + 「같은 이름인가」 | ★★★ **`unordered_*` — `hash` + `==` 둘 다** | (1) |
| 훑으면 제멋대로 | ★★ **해시 순회 순서 — 구현** | (2) |
| 「보여 줘」가 「만들어」로 | ★★★ **`operator[]` 는 없는 키를 넣는다** | (3) |
| 「앞이냐 뒤냐」에 「같다」도 「앞」이라 답함 | ★★★ **`<=` 비교자 — 엄격 약순서 위반** | (4) |
| 공식이 늘 0 | ★★ **나쁜 해시 — 버킷 하나에 1000** | (5) |

```text
   map<P,int>            비교자 하나로 충분           less<P>  →  a < b
                         (같다 = 둘 다 「앞」이 아니다)
   unordered_map<P,int>  두 가지가 필요                hash<P>  →  칸 번호
                                                       equal_to<P> →  a == b
   ★ 한쪽에 필요한 것을 다른 쪽에 줘도 안 된다 — (1)의 격자가 칸마다 보인다
```

## 이 주제가 답하려는 질문

1. ★★★ **커스텀 키에 무엇을 줘야 각 컨테이너가 받나 — 빠지면 에러는 어디를 가리키나**((1)).
2. ★★★ **순서는 누가 보장하나 — 해시 순서가 여러 판에서 같다면 그것은 무엇인가**((2)).
3. ★★★ **없는 키를 찾는 네 가지가 컨테이너를 어떻게 바꾸나**((3)).
4. ★★ **비교자·해시가 계약을 어기면 무엇이 잡아 주나**((4)(5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러 격자와 ⑤ 버킷 분포다

★★★ **요구사항을 빠뜨린 칸은 컴파일 에러**라 **「통과 칸 N / M」과 「첫 error 가 내 파일인가」** 가 결정적인 근거다. **어긴 계약**(약순서 · 해시 품질)은 컴파일러가 못 본다 — **`_GLIBCXX_DEBUG`** 와 **버킷 분포** 두 창으로 바꿔 묻는다.

```text
① 다섯 층 표            요구사항은 표준 · 순회 순서·버킷 수는 libstdc++                     (구현 세부사항 절)
② ★★★ 두 컴파일러 격자   준 것 6 × 컨테이너 4 × 컴파일러 2                                     (1)
③ 실행 출력            operator[] · at · find · contains 뒤의 size                           (3)
④ ★ libstdc++ 디버그 모드 -D_GLIBCXX_DEBUG — 약순서 위반을 잡나                                 (4)
⑤ ★★★ 버킷 분포         bucket_count · bucket_size — 시간 대신                                 (5)
⑥ ★ 순서 가짓수         18 판을 sort -u 로 세기                                                (2)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **요구사항 대 구현 관찰** | **쓴다** |
| ★★★ **② 두 컴파일러 격자** | ★★★ **본체** — **통과 12 / 48 · 에러 칸 중 첫 error 가 내 파일 16 / 36 · 갈린 행 0 / 24** | **쓴다** |
| ③ 실행 출력 | ★★★ `m["b"]` 뒤 **size 2** | **쓴다** |
| ④ 디버그 모드 | ★★ **`set` 은 침묵 · `sort` 는 `irreflexive` 로 잡음** | **쓴다** |
| ★★★ **⑤ 버킷 분포** | ★★★ **본체** — 나쁜 해시는 **빈 아닌 버킷 1 · 가장 큰 버킷 1000 · 그런데 `load_factor` 는 같다** | **쓴다** |
| ⑥ 순서 가짓수 | ★★ **18 판 모두 1 가지** — 한 구현 계열의 관찰 | **쓴다** |
| 시간 측정 | 「해시가 빠르다」·「나쁜 해시는 느리다」 | ★ **안 쟀다**(규칙 24) |
| ★ 제5의 상태 | 「해시가 나쁜가」를 **시간 대신 버킷 분포**로 물었다 | **창을 바꿔 답함** — ★ 이 창은 **비교 횟수를 직접 세지 않는다** |

### (1) ★★★ 커스텀 키 격자 — 준 것 여섯 × 컨테이너 넷

**언제 쓰나** — 직접 만든 타입을 **키로** 쓸 때마다.

```cpp
/* key01.cpp */
// 커스텀 키 P 를 연관 컨테이너 넷(-DCONT=1..4)에 넣는다 — P 에 준 것은 여섯 가지(-DGIVE=1..6)
#include <compare>
#include <cstddef>
#include <cstdio>
#include <functional>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>

struct P {
    int x, y;
#if GIVE == 2
    bool operator<(const P& o) const { return x != o.x ? x < o.x : y < o.y; }
#elif GIVE == 3 || GIVE == 5
    bool operator==(const P& o) const { return x == o.x && y == o.y; }
#elif GIVE == 6
    auto operator<=>(const P&) const = default;
#endif
};

#if GIVE == 4 || GIVE == 5
template <> struct std::hash<P> {
    std::size_t operator()(const P& p) const noexcept { return std::hash<int>{}(p.x) * 31 + std::hash<int>{}(p.y); }
};
#endif

int main() {
#if CONT == 1
    std::set<P> c;
    c.insert(P{1, 2});
#elif CONT == 2
    std::map<P, int> c;
    c.emplace(P{1, 2}, 7);
#elif CONT == 3
    std::unordered_set<P> c;
    c.insert(P{1, 2});
#elif CONT == 4
    std::unordered_map<P, int> c;
    c.emplace(P{1, 2}, 7);
#endif
    std::printf("size %zu · find %d\n", c.size(), c.find(P{1, 2}) != c.end());
}
```

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

- ★★★ **통과 12 / 48 · 컴파일러 사이 갈린 행 0 / 24.** 통과한 여섯 행 = **`set`·`map` 에 `<` 또는 `<=>`** · **`unordered_*` 에 `hash` + `==`**.
- ★★★ **`<=>` `= default` 는 정렬 쪽만 풀었다** — `==` 도 함께 생기지만(23편) **`hash` 가 없어 해시 쪽은 여전히 에러**다.
- ★★★ **`hash` 만 주면 해시 쪽이 `==` 에서 막힌다**(`stl_function.h:378` — `equal_to`) · **`==` 만 주면 `hash` 에서 막힌다.** **둘 다** 줘야 한다.
- ★★★ **에러가 가리키는 곳이 두 종류다** — **정렬 쪽은 `stl_function.h:408`(`std::less` 안의 `__x < __y`) — 라이브러리 안(X)** · **해시 쪽의 `hash` 누락은 `key01.cpp:36`/`39`(선언 줄) — 내 파일(O).** 에러 칸 중 **내 파일 16 / 36**.
- ★★★ **해시 쪽이 선언 줄에서 멈추는 이유** — `std::hash<P>` 를 안 주면 그 특수화는 **「disabled」** 이고, disabled 특수화는 **기본 생성이 안 된다**(cppreference). 그래서 **`std::unordered_set<P> c;` 한 줄이 이미 에러**다 — 넣기도 전에.

```text
                        set     map     unordered_set   unordered_map
   아무것도              ✘ X     ✘ X     ✘ O(선언)        ✘ O(선언)
   operator<            O       O       ✘ O(선언)        ✘ O(선언)
   operator==           ✘ X     ✘ X     ✘ O(선언)        ✘ O(선언)
   std::hash<P>         ✘ X     ✘ X     ✘ X(==)          ✘ X(==)
   std::hash<P> + ==    ✘ X     ✘ X     O                O
   <=> = default        O       O       ✘ O(선언)        ✘ O(선언)
   ★ 위 격자에서 옮긴 요약이다 — 원본은 캡처. O/X 는 「첫 error 가 내 파일인가」
```

**정렬 쪽의 에러**(`set` · 아무것도 안 줌):

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=1 key01.cpp -o ex (cc exit=1) =====
In file included from /usr/include/c++/13/functional:49,
                 from key01.cpp:5:
/usr/include/c++/13/bits/stl_function.h: In instantiation of ‘constexpr bool std::less<_Tp>::operator()(const _Tp&, const _Tp&) const [with _Tp = P]’:
/usr/include/c++/13/bits/stl_tree.h:2534:33:   required from ‘std::_Rb_tree<_Key, _Val, _KeyOfValue, _Compare, _Alloc>::iterator std::_Rb_tree<_Key, _Val, _KeyOfValue, _Compare, _Alloc>::find(const _Key&) [with _Key = P; _Val = P; _KeyOfValue = std::_Identity<P>; _Compare = std::less<P>; _Alloc = std::allocator<P>; iterator = std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>, std::allocator<P> >::iterator]’
/usr/include/c++/13/bits/stl_set.h:797:25:   required from ‘std::set<_Key, _Compare, _Alloc>::iterator std::set<_Key, _Compare, _Alloc>::find(const key_type&) [with _Key = P; _Compare = std::less<P>; _Alloc = std::allocator<P>; iterator = std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>, std::allocator<P> >::const_iterator; key_type = P]’
key01.cpp:42:58:   required from here
/usr/include/c++/13/bits/stl_function.h:408:20: error: no match for ‘operator<’ (operand types are ‘const P’ and ‘const P’)
  408 |       { return __x < __y; }
      |                ~~~~^~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=1 -DCONT=1 key01.cpp -o ex (cc exit=1) =====
In file included from key01.cpp:5:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/functional:49:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_function.h:408:20: error: invalid operands to binary expression ('const P' and 'const P')
  408 |       { return __x < __y; }
      |                ~~~ ^ ~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h:2118:13: note: in instantiation of member function 'std::less<P>::operator()' requested here
 2118 |           __comp = _M_impl._M_key_compare(__k, _S_key(__x));
      |                    ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h:2171:4: note: in instantiation of member function 'std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>>::_M_get_insert_unique_pos' requested here
 2171 |         = _M_get_insert_unique_pos(_KeyOfValue()(__v));
      |           ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_set.h:523:9: note: in instantiation of function template specialization 'std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>>::_M_insert_unique<P>' requested here
  523 |           _M_t._M_insert_unique(std::move(__x));
      |                ^
key01.cpp:31:7: note: in instantiation of member function 'std::set<P>::insert' requested here
   31 |     c.insert(P{1, 2});
      |       ^
In file included from key01.cpp:6:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/map:62:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h:764:16: error: static assertion failed due to requirement 'std::__is_invocable<std::less<P> &, const P &, const P &>{}': comparison object must be invocable with two arguments of key type
  764 |         static_assert(__is_invocable<_Compare&, const _Key&, const _Key&>{},
      |                       ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h:2118:41: note: in instantiation of member function 'std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>>::_S_key' requested here
 2118 |           __comp = _M_impl._M_key_compare(__k, _S_key(__x));
      |                                                ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_tree.h:2171:4: note: in instantiation of member function 'std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>>::_M_get_insert_unique_pos' requested here
 2171 |         = _M_get_insert_unique_pos(_KeyOfValue()(__v));
      |           ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_set.h:523:9: note: in instantiation of function template specialization 'std::_Rb_tree<P, P, std::_Identity<P>, std::less<P>>::_M_insert_unique<P>' requested here
  523 |           _M_t._M_insert_unique(std::move(__x));
      |                ^
key01.cpp:31:7: note: in instantiation of member function 'std::set<P>::insert' requested here
   31 |     c.insert(P{1, 2});
      |       ^
2 errors generated.
```

- ★★ **g++ `no match for ‘operator<’ (operand types are ‘const P’ and ‘const P’)` · clang `invalid operands to binary expression` + `comparison object must be invocable with two arguments of key type`**(두 번째 단언).
- ★★ **두 컴파일러가 가리킨 「내 줄」이 다르다** — g++ 는 **`required from here` 가 42행(`find`)**, clang 은 **`requested here` 가 31행(`insert`)** 이다. 둘 다 `<` 가 필요한 자리지만 **먼저 인스턴스화한 멤버**가 다르다(35편의 사슬 읽기 — 이 판의 관찰).

**해시 쪽의 에러**(`unordered_set` · 아무것도 안 줌 — 발췌라고 밝힌 발췌):

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

- ★★★ **g++ `use of deleted function ‘std::unordered_set<…>::unordered_set()’` · clang `call to implicitly-deleted default constructor of 'std::unordered_set<P>'`** — **「해시가 없다」가 아니라 「기본 생성자가 지워졌다」** 로 읽힌다. 원인(disabled `hash<P>`)은 **g++ 126 줄 · clang 114 줄**의 사슬 끝에 있다.

**`hash` 는 줬는데 `==` 가 없으면**:

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

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DGIVE=4 -DCONT=3 key01.cpp -o ex (cc exit=1) =====
In file included from key01.cpp:5:
In file included from /usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/functional:49:
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_function.h:378:20: error: invalid operands to binary expression ('const P' and 'const P')
  378 |       { return __x == __y; }
      |                ~~~ ^  ~~~
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/hashtable_policy.h:1728:11: note: in instantiation of member function 'std::equal_to<P>::operator()' requested here
 1728 |           return _M_eq()(__k, _ExtractKey{}(__n._M_v()));
      |                  ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/hashtable.h:2261:16: note: in instantiation of function template specialization 'std::__detail::_Hashtable_base<P, P, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Hashtable_traits<false, true, true>>::_M_key_equals_tr<P>' requested here
 2261 |             if (this->_M_key_equals_tr(__k, *__it._M_cur))
      |                       ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/hashtable.h:904:11: note: in instantiation of function template specialization 'std::_Hashtable<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true>>::_M_insert_unique<P, P, std::__detail::_AllocNode<std::allocator<std::__detail::_Hash_node<P, false>>>>' requested here
  904 |           return _M_insert_unique(
      |                  ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/hashtable.h:916:11: note: in instantiation of function template specialization 'std::_Hashtable<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true>>::_M_insert_unique_aux<P, std::__detail::_AllocNode<std::allocator<std::__detail::_Hash_node<P, false>>>>' requested here
  916 |           return _M_insert_unique_aux(
      |                  ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/hashtable_policy.h:1075:13: note: in instantiation of function template specialization 'std::_Hashtable<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true>>::_M_insert<P, std::__detail::_AllocNode<std::allocator<std::__detail::_Hash_node<P, false>>>>' requested here
 1075 |         return __h._M_insert(std::move(__v), __node_gen, __unique_keys{});
      |                    ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/unordered_set.h:433:21: note: in instantiation of member function 'std::__detail::_Insert<P, P, std::allocator<P>, std::__detail::_Identity, std::equal_to<P>, std::hash<P>, std::__detail::_Mod_range_hashing, std::__detail::_Default_ranged_hash, std::__detail::_Prime_rehash_policy, std::__detail::_Hashtable_traits<false, true, true>>::insert' requested here
  433 |       { return _M_h.insert(std::move(__x)); }
      |                     ^
key01.cpp:37:7: note: in instantiation of member function 'std::unordered_set<P>::insert' requested here
   37 |     c.insert(P{1, 2});
      |       ^
1 error generated.
```

- ★★ **`no match for ‘operator==’` / `invalid operands`** — `std::equal_to<P>` 안에서. **해시가 같은 두 키를 가려내려면 `==` 가 필요하다** — 해시는 **칸 번호**일 뿐 「같은 키인가」를 답하지 않는다.

### (2) ★★ 순서 — `map` 은 키 순, 해시는 「구현」

```cpp
/* order01.cpp */
// 같은 키 일곱을 같은 순서로 넣고 순회 순서를 찍는다 — map 과 unordered_map. bucket_count 도 찍는다
#include <cstdio>
#include <map>
#include <unordered_map>

int main() {
    const int keys[] = {50, 3, 17, 88, 1, 42, 29};
    std::map<int, int> m;
    std::unordered_map<int, int> u;
    for (int k : keys) { m[k] = 0; u[k] = 0; }
    std::printf("map          :");
    for (const auto& kv : m) std::printf(" %d", kv.first);
    std::printf("\nunordered_map:");
    for (const auto& kv : u) std::printf(" %d", kv.first);
    std::printf("\nunordered_map bucket_count = %zu\n", u.bucket_count());
}
```

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

- ★★★ **`map` 은 `1 3 17 29 42 50 88`** — 넣은 순서(`50 3 17 88 1 42 29`)와 무관하게 **키 순**이다. **명세가 보장한다**(「Keys are sorted」).
- ★★★ **`unordered_map` 은 `1 88 17 29 42 3 50`** — **18 판(컴파일러 셋 × 최적화 둘 × 세 번) 모두 1 가지.** ★★ 그런데 이것은 **「libstdc++ 한 계열이라 같다」** 이지 보장이 아니다 — 명세는 「**not sorted in any particular order**」라고만 적는다.
- ★★ **Go 와 견주면** — [Go 09번](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/)은 **명세가 순서를 정하지 않고 gc 가 일부러 섞는다**(3 개 키 600 판에서 3 가지). **Rust** [39번](../../../rust/syntax/39-hashmap-vs-btreemap-and-entry-api/)은 **`HashMap` 이 프로세스 300 개에서 6 가지 · `BTreeMap` 은 1 가지**. **libstdc++ 는 섞지 않았다(1 가지)** — 세 언어 중 **가장 잘 속는 판**이다. 여러 판에서 같다는 것이 **보장처럼 보이기** 때문이다.

### (3) ★★★ 없는 키를 찾는 네 가지

```cpp
/* sub01.cpp */
// map 에서 없는 키를 네 가지로 찾는다 — operator[] · at · find · contains. 매번 size 를 찍는다. -DCONSTMAP 이면 const map 에 []
#include <cstdio>
#include <map>
#include <stdexcept>
#include <string>

int main() {
    std::map<std::string, int> m{{"a", 1}};
#ifdef CONSTMAP
    const auto& cm = m;
    std::printf("%d\n", cm["zz"]);
#else
    std::printf("시작          size %zu\n", m.size());
    int v = m["b"];
    std::printf("m[\"b\"] 읽기   size %zu · 값 %d\n", m.size(), v);
    try {
        std::printf("%d\n", m.at("c"));
    } catch (const std::out_of_range& e) {
        std::printf("m.at(\"c\")     size %zu · out_of_range what() = %s\n", m.size(), e.what());
    }
    std::printf("m.find(\"d\")   size %zu · 찾았나 %d\n", m.size(), m.find("d") != m.end());
    std::printf("contains(\"e\") size %zu · 있나 %d\n", m.size(), m.contains("e"));
#endif
}
```

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

- ★★★ **`m["b"]` 를 「읽기」만 했는데 size 1 → 2** — `operator[]` 는 **없으면 `T()`(여기서 0)를 넣고** 그 참조를 돌려준다(cppreference 「**Inserts value_type(key, T()) if the key does not exist**」).
- ★★★ **`at("c")` 는 `std::out_of_range` · `what() = map::at`** — 넣지 않는다(size 2 그대로). ★ `what()` 문자열 **`map::at`** 은 libstdc++ 의 것이다(표준은 문자열을 정하지 않는다).
- ★★ **`find` 는 `end()` · `contains`(C++20)는 `0`** — 둘 다 size 를 안 바꾼다.

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

- ★★★ **`const map` 에는 `operator[]` 가 없다** — g++ `passing ‘const std::map<…>’ as ‘this’ argument discards qualifiers` · clang `no viable overloaded operator[] for type 'const std::map<…>'` + `but method is not marked const`. **넣을 수 있는 함수라서 `const` 일 수 없다** — 에러가 곧 (3)의 규칙의 증거다.

### (4) ★★ 비교자가 엄격 약순서를 어기면 — `<=`

**언제 쓰나** — 비교자를 직접 쓸 때. **`<=` 는 가장 흔한 실수**다.

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

- ★★★ **`c(1, 1) = 1`** — 「1 이 1 보다 앞인가」에 **예**라고 답한다. **엄격 약순서의 첫 조건(비반사성 — `comp(a, a)` 는 거짓)** 위반이다. 그래서 **동치 판정 `!c(a,b) && !c(b,a)` 가 0** — `set` 은 **1 과 1 을 같은 키로 못 본다.**
- ★★★ **보통 빌드는 두 컴파일러 다 침묵 · `run exit=0`** — 경고도 에러도 없다. 비교자 계약은 **컴파일러가 못 본다.** ★ 이 판에서 `set` 이 **무엇을 담게 됐는지는 싣지 않는다** — 요구사항 위반은 **UB** 다.

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

- ★★★ **`_GLIBCXX_DEBUG` 는 `sort` 에서 `Error: comparison doesn't meet irreflexive requirements, assert(!(a < a)).` 로 잡았다**(`run exit=134`).
- ★★★ **그런데 `set` 의 두 `insert` 는 디버그 모드도 침묵**했다 — 「set 에 1 을 두 번 넣었다」가 찍힌 **다음에** `sort` 에서 멈췄다. **디버그 모드가 비교자를 검사하는 자리는 이 판에서 알고리즘(`sort`) 쪽**이었다. **「디버그 모드면 비교자 실수를 다 잡는다」는 틀리다.**

### (5) ★★ 나쁜 해시 — 버킷 분포로

```cpp
/* hash01.cpp */
// 1..1000 을 unordered_set 에 넣고 버킷 분포를 센다 — std::hash<int> 대 항상 0 을 돌려주는 해시
#include <cstddef>
#include <cstdio>
#include <unordered_set>

struct Zero {
    std::size_t operator()(int) const noexcept { return 0; }
};

template <class Set> void report(const char* name) {
    Set s;
    for (int i = 1; i <= 1000; ++i) s.insert(i);
    std::size_t used = 0, biggest = 0;
    for (std::size_t b = 0; b < s.bucket_count(); ++b) {
        std::size_t n = s.bucket_size(b);
        if (n > 0) ++used;
        if (n > biggest) biggest = n;
    }
    std::printf("%-15s size %zu · bucket_count %zu · 빈 아닌 버킷 %zu · 가장 큰 버킷 %zu · load_factor %.3f\n",
                name, s.size(), s.bucket_count(), used, biggest, s.load_factor());
}

int main() {
    report<std::unordered_set<int>>("std::hash<int>");
    report<std::unordered_set<int, Zero>>("Zero");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic hash01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::hash<int>  size 1000 · bucket_count 1109 · 빈 아닌 버킷 1000 · 가장 큰 버킷 1 · load_factor 0.902
Zero            size 1000 · bucket_count 1109 · 빈 아닌 버킷 1 · 가장 큰 버킷 1000 · load_factor 0.902
===== clang++ -std=c++20 -Wall -Wextra -pedantic hash01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
std::hash<int>  size 1000 · bucket_count 1109 · 빈 아닌 버킷 1000 · 가장 큰 버킷 1 · load_factor 0.902
Zero            size 1000 · bucket_count 1109 · 빈 아닌 버킷 1 · 가장 큰 버킷 1000 · load_factor 0.902
```

- ★★★ **`Zero` 는 빈 아닌 버킷 1 · 가장 큰 버킷 1000** — **1000 개가 한 칸에 몰렸다.** `std::hash<int>` 는 **1000 칸에 하나씩**.
- ★★★ **그런데 `bucket_count 1109` · `load_factor 0.902` 는 둘이 똑같다** — **적재율은 「원소 수 / 칸 수」라 분포를 못 본다.** 나쁜 해시는 `load_factor` 로 안 드러나고 **`bucket_size` 를 훑어야** 보인다.
- ★★ **여전히 정답은 맞다** — `Zero` 도 **계약(같은 키면 같은 해시)은 지킨다.** 그래서 **틀린 게 아니라 나쁜 것**이고, 어떤 도구도 에러를 내지 않는다. 이 한 칸에 몰린 원소를 찾으려면 **칸 안에서 `==` 로 하나씩 대조**하게 된다(원리는 data-structure 05 — **이 편은 비교 횟수·시간을 재지 않았다**).

```cpp
/* bucket01.cpp */
// unordered_set<int> 에 하나씩 200 개를 넣으며 bucket_count 가 바뀌는 순간만 찍는다(max_load_factor 도)
#include <cstdio>
#include <unordered_set>

int main() {
    std::unordered_set<int> s;
    std::printf("처음 bucket_count %zu · max_load_factor %.1f\n", s.bucket_count(), s.max_load_factor());
    std::size_t last = s.bucket_count();
    for (int i = 0; i < 200; ++i) {
        s.insert(i);
        if (s.bucket_count() != last) {
            std::printf("size %3zu 에서 bucket_count %3zu\n", s.size(), s.bucket_count());
            last = s.bucket_count();
        }
    }
}
```

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

- ★★ **`bucket_count` 1 → 13 → 29 → 59 → 127 → 257** · `max_load_factor 1.0` — **원소 수가 칸 수를 넘으려는 순간 늘린다**(이 판 — 소수 근처로 대략 두 배). **이 순간이 rehash** 이고, **그때 이터레이터가 무효**가 된다(목록의 **43번 주제** — 격자의 `unordered_map` 행).

## 문법 — 형태와 규칙

### 형태

```text
   std::map<K, V, Cmp = std::less<K>>            Cmp(a, b) — 엄격 약순서. 없으면 K 의 operator< 를 쓴다
   std::unordered_map<K, V, H = std::hash<K>, Eq = std::equal_to<K>>   H(k) 와 Eq(a, b) 둘 다
   template <> struct std::hash<P> { std::size_t operator()(const P&) const noexcept; };
   auto operator<=>(const P&) const = default;   < 와 == 가 생긴다 · hash 는 안 생긴다 (C++20)
   m[k]          없으면 V() 를 넣는다 · const map 에는 없다
   m.at(k)       없으면 std::out_of_range
   m.find(k) / m.contains(k)   안 넣는다 (contains 는 C++20)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **정렬 쪽은 엄격 약순서 비교자 하나 · 해시 쪽은 `hash` + `==` 둘**((1) 12 / 48).
- ★★★ **`std::hash<P>` 를 안 주면 disabled — 선언 줄에서 이미 에러**((1)).
- ★★★ **`map` 은 키 순(보장) · 해시 쪽 순서는 구현**((2)).
- ★★★ **`operator[]` 는 넣는다 — 읽기만 하려면 `find`·`contains`·`at`**((3)).
- ★★ **비교자 계약 위반은 컴파일러가 못 본다 — 디버그 모드도 자리를 가린다**((4)).
- ★★ **해시 품질은 `load_factor` 로 안 보인다**((5)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ 진단 | clang 진단 | 어디서 |
|---|---|---|---|
| `<` 없는 키로 `set` | `no match for ‘operator<’` | `invalid operands to binary expression` + `comparison object must be invocable` | (1) |
| `hash` 없는 키로 `unordered_set` 선언 | `use of deleted function ‘…unordered_set()’` | `call to implicitly-deleted default constructor` | (1) |
| `hash` 만 있고 `==` 없음 | `no match for ‘operator==’` | `invalid operands to binary expression` | (1) |
| `const map` 에 `[]` | `discards qualifiers` | `no viable overloaded operator[]` | (3) |

## 어디서 틀리나

### 1. ★★★ 「`<=>` 를 `default` 로 두면 어디든 키가 된다」

(1)의 여섯째 행 — **정렬 쪽만 풀린다.** `hash` 는 안 생긴다.

### 2. ★★★ 「`hash` 만 주면 해시 컨테이너가 된다」

(1)의 넷째 행 — **`==` 에서 막힌다.** 해시는 칸 번호일 뿐이다.

### 3. ★★★ 「`unordered_map` 순서가 매번 같으니 믿어도 된다」

(2) — **18 판 1 가지는 이 구현의 관찰**이다. 명세는 순서를 정하지 않는다. Go 는 일부러 섞고, Rust 는 프로세스마다 다르다.

### 4. ★★★ 「`m[k]` 로 있는지 확인한다」

(3) — **size 가 늘어난다.** 확인은 `contains`·`find`.

### 5. ★★ 「`<=` 도 비교자다」

(4) — **`c(1,1) = 1` 이 비반사성을 깬다.** 보통 빌드는 침묵, 디버그 모드도 `set` 에서는 침묵했다.

### 6. ★★ 「`load_factor` 가 낮으면 해시가 괜찮다」

(5) — **`Zero` 도 0.902.** 분포는 `bucket_size` 로만 보인다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 사고는 「표준」과 「UB」 사이에 산다** — 요구사항 **누락**은 컴파일 에러(표준)지만, 요구사항 **위반**(약순서 · 해시 계약)은 **UB 라 도구 없이는 말할 수 없다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **비교자는 엄격 약순서 · `hash`+`==` · disabled `hash` 는 기본 생성 불가 · `map` 키 순 · `operator[]` 는 넣는다 · `at` 은 `out_of_range` · 로그 · 평균 상수 복잡도** | 두 컴파일러 격자 · cppreference | — |
| **조건부 표준** | 특정 판에서만 | ★★ **`contains`·`<=>` C++20** | (1)(3) | — |
| **구현 정의 · 라이브러리** | 문서화 의무 없음 | ★★★ **해시 순회 순서 · `bucket_count` 수열(13 · 29 · 59 …) · `what() = map::at`** | (2)(3)(5) | ★★ **18 판 1 가지는 한 구현 계열** — 다른 구현은 못 잰 것 |
| **컴파일러의 것** | 표준 밖 | ★ **「내 줄」로 먼저 가리킨 멤버**(g++ `find` 42행 · clang `insert` 31행) | (1)의 에러 | — |
| **UB** | 아무 일이나 | ★★★ **`<=` 비교자로 채운 `set`** — 값을 싣지 않았다 | `_GLIBCXX_DEBUG`((4)) | ★★★ **디버그 모드는 `sort` 에서만 잡았다 — `set` 은 침묵** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| **순서대로 훑어야 한다 · 범위 검색(`lower_bound`)** | ★★★ **`map`·`set`** | (2) 키 순 보장 |
| 순서가 필요 없고 키에 좋은 해시가 있다 | ★★ **`unordered_map`** — 시간 이득은 이 편이 **재지 않았다** | (1)(5) |
| 커스텀 키 · 정렬 쪽 | ★★ **`<=> = default`** 한 줄 | (1) |
| 커스텀 키 · 해시 쪽 | ★★★ **`std::hash<P>` 특수화 + `==`** | (1) |
| 있는지만 본다 | ★★★ **`contains`(C++20) · `find`** — `[]` 금지 | (3) |
| 없으면 에러로 | ★★ **`at`** | (3) |
| 비교자를 직접 쓴다 | ★★ **`<` 로 · 디버그 모드로 `sort` 한 번 돌려 보기** | (4) |

## 핵심 문장

- ★★★ **준 것 여섯 × 컨테이너 넷에서 통과 12 / 48 · 갈린 행 0** — 정렬 쪽은 `<` 또는 `<=>`, 해시 쪽은 **`hash` + `==` 둘 다.**
- ★★★ **`hash` 를 안 주면 선언 줄이 에러(disabled `hash` 는 기본 생성 불가) — 에러 칸 중 내 파일을 가리킨 16 / 36 이 전부 이 선언 줄이다.**
- ★★★ **`map` 은 키 순 보장 · `unordered_map` 순서는 18 판 1 가지였지만 구현의 관찰이다.**
- ★★★ **`m["b"]` 는 읽기만 해도 size 1 → 2 · `at` 은 `out_of_range` · `find`/`contains` 는 그대로.**
- ★★ **`<=` 비교자는 `c(1,1) = 1` — 보통 빌드 침묵 · 디버그 모드는 `sort` 에서만 `irreflexive` 로 잡았다.**
- ★★ **늘 0 인 해시는 버킷 하나에 1000 — `load_factor` 는 0.902 로 똑같다.**

## 관련 자료

- [`data-structure/05-hashmap/`](../../../../../data-structure/05-hashmap/) — ★★★ **해시 테이블의 원리**(버킷 · 체이닝 · 적재율 0.75 · 리사이즈 · `hashCode`/`equals` 의 약속). **여기는 표준 컨테이너가 키에게 요구하는 것.**
- [`data-structure/06-binary-search-tree/`](../../../../../data-structure/06-binary-search-tree/) · [`16-red-black-tree/`](../../../../../data-structure/16-red-black-tree/) — 정렬 쪽의 원리. ★ `std::map` 이 레드-블랙 트리라는 것은 **이 판의 기호(`_Rb_tree`)로 보일 뿐 표준이 정하지 않는다** — 표준은 **로그 복잡도**를 정한다.
- [41번](../41-choosing-sequence-containers/) — 컨테이너를 고르는 결정적 칸.
- [23번](../23-three-way-comparison-spaceship/) — `<=>` `= default` 가 `==` 까지 만든다((1)의 여섯째 행).
- [35번](../35-instantiation-header-placement-and-reading-errors/) — **첫 에러가 어디를 가리키나** — (1)의 O/X.
- 목록의 **43번 주제** — rehash 와 이터레이터 무효화.
- Go 갈래 [09번](../../../go/syntax/09-maps-declaration-comma-ok-delete-and-iteration-order/) — ★★ **명세가 무작위를 정하고 gc 가 일부러 섞는다.**
- Rust 갈래 [39번](../../../rust/syntax/39-hashmap-vs-btreemap-and-entry-api/) — ★★ **`HashMap` 6 가지 · `BTreeMap` 1 가지 · 「없으면 넣고」는 `entry` 로 해시 1 회.**

## 용어 풀이

> **연관 컨테이너(associative container)** — 원소를 **키로** 찾는 컨테이너. 정렬 쪽(`set`·`map`)과 해시 쪽(`unordered_set`·`unordered_map`).\
> 예: (1).

> **엄격 약순서(strict weak ordering)** — 비교자가 지켜야 할 규칙. **`comp(a, a)` 는 거짓(비반사)** · 추이 · 「둘 다 앞이 아니면 같다」가 추이.\
> 예: (4)의 `<=` 가 첫 조건을 깬다.

> **동치(equivalence)** — 정렬 컨테이너가 「같은 키」를 판정하는 법: `!comp(a,b) && !comp(b,a)`. `==` 를 쓰지 않는다.\
> 예: (4)의 `0`.

> **disabled `std::hash`** — 프로그램이 특수화를 안 준 `std::hash<Key>`. 기본 생성·복사가 안 된다.\
> 예: (1)의 선언 줄 에러.

> **버킷(bucket) · 적재율(load factor)** — 해시 쪽의 칸 · `size() / bucket_count()`.\
> 예: (5)의 0.902.

> **rehash** — 칸 수를 바꾸고 원소를 새 칸에 다시 나누는 것. 이터레이터가 무효가 된다.\
> 예: (5)의 `bucket_count` 수열 · 43편.

## 더 들어가면

- **이질 탐색(`std::less<>`·`is_transparent`)** — `map<std::string, …>` 에 `const char*` 로 찾을 때 임시 문자열을 안 만드는 법. **던지지 않았다.**
- **`try_emplace`·`insert_or_assign`(C++17)** — `operator[]` 의 대안. **던지지 않았다.**
- **나쁜 해시의 비교 횟수** — `==` 를 세는 계수기로 물을 수 있다. 이 편은 **버킷 분포까지만** 봤다.
