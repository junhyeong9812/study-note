# cpp/syntax/41 — 순차 컨테이너 선택 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — Containers library](https://en.cppreference.com/w/cpp/container) · [`std::vector`](https://en.cppreference.com/w/cpp/container/vector) · [`std::vector::push_back`](https://en.cppreference.com/w/cpp/container/vector/push_back) · [`std::deque`](https://en.cppreference.com/w/cpp/container/deque) · [`std::deque::push_front`](https://en.cppreference.com/w/cpp/container/deque/push_front)\
> ★ 이 배치에서 **위 cppreference 쪽들을 열어 확인했다** — `vector` 는 「**The elements are stored contiguously**」 · `push_back` 의 복잡도는 「**Amortized constant**」(★ **배수는 적혀 있지 않다**) · 「**If after the operation the new size() is greater than old capacity() a reallocation takes place, in which case all iterators … and all references to the elements are invalidated.**」 · `deque` 는 「**insertion and deletion at either end of a deque never invalidates pointers or references to the rest of the elements**」 · 「**the elements of a deque are not stored contiguously**」 · `push_front` 는 「**All iterators … are invalidated. No references are invalidated.**」
> **실행 검증** — 이 문서의 모든 출력은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** · **g++-12 (Ubuntu 12.4.0-2ubuntu1\~24.04.1) 12.4.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13**(★★ clang 도 같은 라이브러리 — 컨테이너의 `sizeof`·할당·증가 배수 칸은 **한 구현**이다. `g++-12` 만 **libstdc++ 12 헤더**다) · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`seq01.cpp`·`capseq01.cpp`·`mif01.cpp`·`seq-grid.sh`). 블록은 캡처 스크립트가 받은 것이다 — 사람이 옮겨 적은 줄은 없다.
> **버전** — `vector`·`deque`·`list` 는 **C++98**, `array`·`forward_list`·`emplace_back`·`std::move_if_noexcept` 는 **C++11** 이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **정본 경계** — **동적 배열과 연결 리스트의 원리**(2배 확장 · 분할 상환 O(1) · 캐시 지역성 · 노드 연결)는 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)·[`02-linked-list/`](../../../../../data-structure/02-linked-list/)·[`04-queue-deque/`](../../../../../data-structure/04-queue-deque/)가 정본이다(★ 그쪽은 **Java 로 직접 구현**한다). **여기는 표준 컨테이너의 선택과 계약** — 「무엇을 보장하고 무엇은 구현인가」만 본다.
> ★★★ **[17번](../17-move-constructor-assignment-and-moved-from-state/)에서 온다 — 앞 편이 잰 것은 다시 재지 않는다.**\
> [17번](../17-move-constructor-assignment-and-moved-from-state/) (3) — **이동 생성자에 `noexcept` 가 있으면 `vector` 재할당이 이동, 없으면 복사**(`is_nothrow_move_constructible` 1 대 0 · `capacity` 2 → 4 · 두 컴파일러 같음). 선행 [18번](../18-rule-of-zero-three-five-default-delete/) — 특수 멤버를 어떻게 적느냐가 여기서 **컨테이너의 행동**으로 돌아온다.\
> ★★ **여기서 새로 묻는 것은 셋이다** — ① **다섯 컨테이너 × 결정적 칸 넷**(sizeof · 할당 횟수 · 연속인가 · 원소 주소가 그대로인가) · ② **`std::move_if_noexcept` 를 직접 불러 보기 + 셋째 타입(복사 없음 · 던지는 이동)** · ③ **`capacity` 수열**.
> ★★★ **「`list` 는 캐시에 나쁘다」「`vector` 가 빠르다」는 이 문서가 싣지 않는다 — 시간을 재지 않았다.** 지역성은 **「연속인가」 참/거짓**으로만 적는다(규칙 24).
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ **주소 자체**(격자에 찍지 않았다 — 「같은가 · 이웃인가」만 찍는다) | ★★★ **할당 횟수 · 연속인가 · 주소가 그대로인가 · `capacity` 수열 · 이동/복사 로그** — 네 판(컴파일러 2 × `-O0`/`-O2`) 동일 |
> | ★ `sizeof`·**2 배**·`deque` 의 칸 크기 — **libstdc++ 의 관찰**(표준은 정하지 않는다) | ★★★ **`vector` 는 연속 · `deque` 는 끝 삽입에 참조 유지 · `list` 는 전부 유지** — 명세 |

## 한눈에 — 쉽게 말하면

**컨테이너 고르기는 「원소를 어디에 세워 두나」 고르기다.**

- **`vector`** — **한 줄 좌석.** 옆자리가 붙어 있어 **번호로 바로 찾고 훑기가 쉽다.** 자리가 모자라면 **더 큰 줄로 전원 이사**한다 — 이사하면 **좌석 번호표(주소·참조)가 다 무효**다.
- **`deque`** — **여러 개의 짧은 줄(칸)**. 앞뒤 끝에 새 칸을 붙이면 되니 **앞뒤로 들어와도 기존 사람은 안 움직인다**(참조 유지). 대신 **줄과 줄 사이는 떨어져 있다**(연속 아님).
- **`list`** — **한 사람씩 따로 앉고 옆 사람 위치를 쪽지로 든다.** 아무도 안 움직이지만 **사람마다 자리를 따로 잡는다**(할당 N 회).
- **`array`** — **정해진 N 석짜리 좌석.** 늘지 않는다 — 할당 0.

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 한 줄 좌석 · 전원 이사 | ★★★ **`vector` — 연속 · 재할당 5 회 · 주소 바뀜** | (1) |
| 미리 넉넉한 줄 | ★★ **`reserve(16)` — 할당 1 회 · 주소 그대로** | (1) |
| 짧은 줄 여러 개 | ★★★ **`deque` — 앞 삽입에도 참조 유지 · 연속 아님** | (1) |
| 쪽지로 이은 자리 | ★★ **`list`·`forward_list` — 원소마다 할당 · 주소 불변** | (1) |
| 이사할 때 안전하게 옮길 수 있나 | ★★★ **`noexcept` 이동 — 아니면 복사** | (3) · 17편 (3) |

```text
   vector   [0][1][2][3]                    ← 한 덩어리 · 모자라면 새 덩어리로 전원 이사
   deque    [0 1 2 …]  [… …]  [… …]         ← 칸 여러 개 + 칸 목록 · 끝에 칸을 붙인다
   list     (0)⇄(1)⇄(2)⇄(3)                  ← 원소마다 따로 · 서로 가리킨다
   array    [0][1]…[15]                     ← 크기가 타입의 일부 · 힙 없음
```

## 이 주제가 답하려는 질문

1. ★★★ **원소를 넣을 때 무엇이 결정적으로 다른가 — 할당 · 연속성 · 주소 안정성**((1)).
2. ★★★ **`vector` 는 얼마씩 늘리나 — 그것은 누가 보장하나**((2)).
3. ★★★ **재할당 때 원소를 옮기나 복사하나 — `std::move_if_noexcept` 가 가르는 셋째 경우**((3)).
4. ★★ **그래서 왜 기본값이 `vector` 인가**(언제 쓰나 절).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ④ 할당 계수기와 ⑤ 주소 비교다

★★★ **「지역성이 좋다」를 시간으로 말하지 않는다** — 대신 「**이웃한 두 원소의 주소 차이가 원소 하나 크기인가**」를 전 구간에서 참/거짓으로 찍는다. 주소 자체는 흔들리지만 **「이웃인가 · 같은가」는 안 흔들린다.**

```text
① 다섯 층 표          연속·참조 유지는 표준 · 배수·sizeof 는 libstdc++                   (구현 세부사항 절)
② 두 컴파일러 + g++-12  capacity 수열 · 이동/복사 로그                                    (2)(3)
③ 실행 출력           move_if_noexcept 가 돌려준 것                                     (3)
④ ★★★ 할당 계수기      operator new 가로채기 — 16 개 넣을 때 몇 번                         (1)
⑤ ★★★ 주소 비교        이웃인가 · 처음 원소 주소가 그대로인가 — 주소를 찍지 않고 비교만     (1)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **명세 대 libstdc++ 관찰** | **쓴다** |
| ② 두 컴파일러 · `g++-12` | ★★ **`capacity` 수열 세 판 동일** · 이동/복사 로그 두 판 동일 | **쓴다** |
| ③ 실행 출력 | ★★★ `move_if_noexcept` 가 **`T&&` 인가 `const T&` 인가** | **쓴다** |
| ★★★ **④ 할당 계수기** | ★★★ **본체** — 여덟 행 × 칸 넷 · **네 판 사이 갈린 칸 0 / 96** | **쓴다** |
| ★★★ **⑤ 주소 비교** | ★★★ **본체** — 연속 **3 / 8 행 · `deque` 는 16 개면 「예」, 200 개면 「아니오」** | **쓴다** |
| 시간 측정 | 「`list` 는 캐시에 나쁘다」 | ★ **안 쟀다**(규칙 24) — 연속성 참/거짓으로 대신했다 |
| ★ 제5의 상태 | 「지역성」을 **시간 대신 주소 관계**로 물었다 | **창을 바꿔 답함** — ★ 이 창은 **캐시 미스를 못 본다**(연속이어도 원소가 크면 한 줄에 몇 개 안 든다) |

### (1) ★★★ 결정적 칸 격자 — 원소 16 개를 넣으며

**언제 쓰나** — 컨테이너를 고를 때마다. **「몇 번 할당하나 · 붙어 있나 · 넣는 동안 원소가 움직이나」** 세 질문이 선택의 대부분을 정한다.

```cpp
/* seq01.cpp */
// 순차 컨테이너에 원소 N 개(기본 16)를 넣으며 센다(-DC=1..7) — operator new 횟수 · sizeof · 연속인가 · 처음 넣은 원소의 주소가 그대로인가
#include <array>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <forward_list>
#include <list>
#include <memory>
#include <new>
#include <vector>

static int g_news = 0;
void* operator new(std::size_t n) {
    ++g_news;
    if (void* p = std::malloc(n)) return p;
    throw std::bad_alloc{};
}
void operator delete(void* p) noexcept { std::free(p); }
void operator delete(void* p, std::size_t) noexcept { std::free(p); }

#ifndef N
#define N 16
#endif

// 이웃한 두 원소의 주소 차이가 원소 하나 크기인가 — 전 구간에서
template <class Cont> bool contiguous(Cont& c) {
    auto it = c.begin();
    const int* prev = std::addressof(*it);
    for (++it; it != c.end(); ++it) {
        const int* cur = std::addressof(*it);
        if (cur != prev + 1) return false;
        prev = cur;
    }
    return true;
}

int main() {
    int before = g_news;
#if C == 1 || C == 2
    std::vector<int> c;
#if C == 2
    c.reserve(N);
#endif
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_back(i);
    bool kept = (first == &c.front());
#elif C == 3
    std::array<int, N> c{};
    const int* first = &c.front();
    for (int i = 0; i < N; ++i) c[i] = i;
    bool kept = (first == &c.front());
#elif C == 4 || C == 5
    std::deque<int> c;
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) {
#if C == 4
        c.push_back(i);
#else
        c.push_front(i);
#endif
    }
#if C == 4
    bool kept = (first == &c.front());
#else
    bool kept = (first == &c.back());
#endif
#elif C == 6
    std::list<int> c;
    c.push_back(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_back(i);
    bool kept = (first == &c.front());
#elif C == 7
    std::forward_list<int> c;
    c.push_front(0);
    const int* first = &c.front();
    for (int i = 1; i < N; ++i) c.push_front(i);
    int last = 0;
    const int* lastp = nullptr;
    for (int& v : c) { last = v; lastp = &v; }
    (void)last;
    bool kept = (first == lastp);
#endif
    int news = g_news - before;
    std::printf("%zu\t%d\t%s\t%s\n", sizeof(c), news, contiguous(c) ? "예" : "아니오", kept ? "예" : "아니오");
}
```

- ★★ **할당은 컨테이너를 만든 순간부터** 센다 — `deque` 는 **빈 채로도** 칸 목록과 첫 칸을 잡는다(이 판).
- ★★ **「처음 원소」** — 맨 처음 넣은 `0` 이다. `deque push_front`·`forward_list` 는 뒤에 넣은 것이 앞에 오므로 **그 `0` 이 있는 끝**과 견준다.

```bash
# seq-grid.sh
# seq-grid.sh — 컨테이너 여덟 행 × 판 넷(컴파일러 둘 × -O0/-O2). 칸 넷은 seq01.cpp 가 찍는다
rows=('1 16 vector push_back' '2 16 vector reserve(16) 뒤 push_back' '3 16 array 칸에 쓰기' '4 16 deque push_back'
      '5 16 deque push_front' '4 200 deque push_back ×200' '6 16 list push_back' '7 16 forward_list push_front')
printf '%s\t%s\t%s\t%s\t%s\n' "컨테이너 · 넣는 법" "sizeof" "operator new 횟수" "연속인가" "처음 원소 주소 그대로인가" > t.tsv
diffs=0; cells=0
for r in "${rows[@]}"; do
  set -- $r; k=$1; n=$2; shift 2; name="$*"
  ref=""
  for c in g++ clang++; do
    for o in -O0 -O2; do
      $c -std=c++20 -Wall -Wextra -pedantic $o -DC=$k -DN=$n seq01.cpp -o sx || { echo "cc 에러 $r"; exit 1; }
      got=$(./sx) || exit 1
      if [ -z "$ref" ]; then ref="$got"; printf '%s\t%s\n' "$name" "$got" >> t.tsv
      else
        d=$(paste <(printf '%s\n' "$ref" | tr '\t' '\n') <(printf '%s\n' "$got" | tr '\t' '\n') | awk -F'\t' '$1 != $2' | wc -l)
        diffs=$(( diffs + d )); cells=$(( cells + 4 ))
      fi
    done
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 5' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
echo "판 넷 중 g++ -O0 과 갈린 칸 $diffs / $cells"
rm -f sx t.tsv
```

```text
===== bash seq-grid.sh (exit=0) =====
컨테이너 · 넣는 법	sizeof	operator new 횟수	연속인가	처음 원소 주소 그대로인가
vector push_back	24	5	예	아니오
vector reserve(16) 뒤 push_back	24	1	예	예
array 칸에 쓰기	64	0	예	예
deque push_back	80	2	예	예
deque push_front	80	3	아니오	예
deque push_back ×200	80	3	아니오	예
list push_back	24	16	아니오	예
forward_list push_front	8	16	아니오	예
판 넷 중 g++ -O0 과 갈린 칸 0 / 96
```

- ★★★ **`vector` 는 16 개에 할당 5 회 · 처음 원소 주소가 바뀌었다** — 1 · 2 · 4 · 8 · 16 으로 **다섯 번 이사**했다((2)). **`reserve(16)` 하면 1 회 · 주소 그대로**.
- ★★★ **`deque` 는 앞으로 넣어도 뒤로 넣어도 처음 원소 주소가 그대로** — cppreference 의 「**never invalidates pointers or references to the rest of the elements**」 그대로다. **`vector` 와 가장 크게 갈리는 칸**이다.
- ★★★ **`deque` 의 「연속인가」는 16 개 `push_back` 에서 「예」, 200 개에서 「아니오」** — 16 개는 **한 칸 안에 다 들어가서** 우연히 이웃했을 뿐이다. **명세는 연속을 약속하지 않는다**(「not stored contiguously」). ★★ **작은 입력의 「예」는 근거가 못 된다** — 이 한 행이 그 증거다.
- ★★ **`list`·`forward_list` 는 원소마다 할당 16 회 · 주소 불변 · 연속 아님.**
- ★★ **`array` 는 할당 0 · `sizeof = 64`**(`int` 16 개 — 원소가 객체 안에 있다). 나머지는 **원소 수와 무관한 머리 크기**다 — `vector` 24 · `deque` 80 · `list` 24 · `forward_list` 8(이 판).
- ★★★ **네 판 사이 갈린 칸 0 / 96** — 할당·연속·주소 안정성은 **최적화를 타지 않았다.** ★ 다만 **두 컴파일러가 같은 libstdc++** 다.

```text
                          할당(16 개)   연속인가       처음 원소가 그대로인가
   vector                 5            예             ✘  ← 이사
   vector + reserve(16)   1            예             O
   array                  0            예             O  (넣지 않고 칸에 쓴다)
   deque (앞 · 뒤)         2~3          ★ 16 개면 예   O  ← 앞에 넣어도
                                        200 개면 아니오
   list · forward_list    16           아니오         O
   ★ 위 격자에서 옮긴 요약이다 — 원본은 캡처
```

### (2) ★★ `capacity` 수열 — 얼마씩 늘리나

```cpp
/* capseq01.cpp */
// vector 에 하나씩 1000 개를 넣으며 capacity 가 바뀌는 순간만 찍는다
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v;
    std::printf("처음 capacity %zu\n", v.capacity());
    std::size_t last = v.capacity();
    int changes = 0;
    for (int i = 0; i < 1000; ++i) {
        v.push_back(i);
        if (v.capacity() != last) {
            std::printf("size %4zu 에서 capacity %4zu\n", v.size(), v.capacity());
            last = v.capacity();
            ++changes;
        }
    }
    std::printf("바뀐 횟수 %d\n", changes);
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
===== clang++ -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
===== g++-12 -std=c++20 -Wall -Wextra -pedantic capseq01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
처음 capacity 0
size    1 에서 capacity    1
size    2 에서 capacity    2
size    3 에서 capacity    4
size    5 에서 capacity    8
size    9 에서 capacity   16
size   17 에서 capacity   32
size   33 에서 capacity   64
size   65 에서 capacity  128
size  129 에서 capacity  256
size  257 에서 capacity  512
size  513 에서 capacity 1024
바뀐 횟수 11
```

- ★★★ **1 → 2 → 4 → 8 → … → 1024, 바뀐 횟수 11** — **이 판(libstdc++ 13 · 12)은 두 배**다. 세 판(g++ 13 · clang 18 · g++-12)이 한 글자도 같다.
- ★★★ **표준이 보장하는 것은 「Amortized constant」뿐**이다 — 배수를 적지 않는다. 두 배는 **구현의 선택**이다(다른 표준 라이브러리의 배수는 **이 머신에서는 못 잰 것**이다 — libc++ 없음).
- ★★ **「분할 상환 O(1)」 이 왜 성립하나**는 [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/)가 정본이다 — 그쪽이 **직접 구현한 2 배 확장**으로 보인다. 여기서는 **「표준 `vector` 도 이 판에서는 2 배였다」** 까지만 말한다.
- ★ **처음 capacity 0** — 빈 `vector` 는 **할당하지 않는다**((1)의 `vector` 가 5 회인 까닭 — 1 부터 시작).

### (3) ★★★ 재할당 때 옮기나 복사하나 — `std::move_if_noexcept`

**언제 쓰나** — 원소 타입의 이동 생성자를 적을 때(17편 (3)) · **복사가 없는 타입**을 `vector` 에 담을 때.

```cpp
/* mif01.cpp */
// std::move_if_noexcept 가 무엇을 돌려주나 · vector 재할당이 무엇으로 옮기나 — 타입 셋
#include <cstdio>
#include <type_traits>
#include <utility>
#include <vector>

struct NoexceptMove {
    NoexceptMove() = default;
    NoexceptMove(const NoexceptMove&) { std::printf("copy "); }
    NoexceptMove(NoexceptMove&&) noexcept { std::printf("move "); }
};
struct ThrowingMove {
    ThrowingMove() = default;
    ThrowingMove(const ThrowingMove&) { std::printf("copy "); }
    ThrowingMove(ThrowingMove&&) { std::printf("move "); }
};
struct MoveOnlyThrowing {                     // 복사가 없고 이동은 noexcept 가 아니다
    MoveOnlyThrowing() = default;
    MoveOnlyThrowing(const MoveOnlyThrowing&) = delete;
    MoveOnlyThrowing(MoveOnlyThrowing&&) { std::printf("move "); }
};

template <class T> void probe(const char* name) {
    T x;
    constexpr bool rv = std::is_rvalue_reference_v<decltype(std::move_if_noexcept(x))>;
    std::printf("%-17s nothrow_move=%d copyable=%d move_if_noexcept->%s | 재할당: ", name,
                (int)std::is_nothrow_move_constructible_v<T>, (int)std::is_copy_constructible_v<T>,
                rv ? "T&&" : "const T&");
    std::vector<T> v;
    v.reserve(2);
    v.emplace_back();
    v.emplace_back();
    v.emplace_back();                         // capacity 2 를 넘긴다 — 있던 둘을 옮긴다
    std::printf("\n");
}

int main() {
    probe<NoexceptMove>("NoexceptMove");
    probe<ThrowingMove>("ThrowingMove");
    probe<MoveOnlyThrowing>("MoveOnlyThrowing");
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic mif01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
NoexceptMove      nothrow_move=1 copyable=1 move_if_noexcept->T&& | 재할당: move move 
ThrowingMove      nothrow_move=0 copyable=1 move_if_noexcept->const T& | 재할당: copy copy 
MoveOnlyThrowing  nothrow_move=0 copyable=0 move_if_noexcept->T&& | 재할당: move move 
===== clang++ -std=c++20 -Wall -Wextra -pedantic mif01.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
NoexceptMove      nothrow_move=1 copyable=1 move_if_noexcept->T&& | 재할당: move move 
ThrowingMove      nothrow_move=0 copyable=1 move_if_noexcept->const T& | 재할당: copy copy 
MoveOnlyThrowing  nothrow_move=0 copyable=0 move_if_noexcept->T&& | 재할당: move move 
```

- ★★★ **`NoexceptMove` 는 `move move` · `ThrowingMove` 는 `copy copy`** — 17편 (3)의 결론 그대로다. **새로 보인 것**은 그 판정이 **`std::move_if_noexcept(x)` 의 반환 타입**으로 **그대로 보인다는 것**이다 — `T&&` 대 `const T&`.
- ★★★ **셋째 — `MoveOnlyThrowing`(복사 없음 · 던지는 이동)은 `move move`** — `move_if_noexcept` 가 **`T&&` 를 돌려준다.** **복사할 수 없으면 던질 수 있어도 옮긴다.** 대가는 **강한 예외 보장을 잃는 것**이다 — 옮기다 던지면 **옛 버퍼도 새 버퍼도 온전하지 않을 수 있다**(이 편은 던지는 판을 **돌리지 않았다**).
- ★★ **규칙 한 줄** — `move_if_noexcept` 는 「**`noexcept` 이동이 있거나 복사가 없으면 `T&&`, 아니면 `const T&`**」 다. 표의 `nothrow_move`·`copyable` 두 열이 그 조건이다.

```text
                      nothrow_move   copyable    move_if_noexcept   재할당
   NoexceptMove            1            1           T&&            move    ← 17편 (3)
   ThrowingMove            0            1           const T&       copy    ← 17편 (3)
   MoveOnlyThrowing        0            0           T&&            move    ★ 강한 보장 포기
```

## 문법 — 형태와 규칙

### 형태

```text
   std::vector<T> v;  v.reserve(n);          연속 · 끝 추가 분할 상환 O(1) · reserve 로 재할당 없애기
   std::array<T, N> a{};                      연속 · 크기 고정 · 힙 없음
   std::deque<T> d;  d.push_front(x);         양끝 O(1) · 끝 삽입에 참조 유지 · 연속 아님
   std::list<T> l;   l.splice(pos, other);    어디든 O(1) 삽입·삭제 · 참조 전부 유지
   std::forward_list<T> f;  f.push_front(x);  단일 연결 · size() 없음
   std::move_if_noexcept(x)                   noexcept 이동이거나 복사 불가면 T&&, 아니면 const T&
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(3)이 **실행한 소스**로 보였다(`splice` 는 던지지 않았다).

### 규칙

- ★★★ **`vector` 는 연속 · 끝 추가는 분할 상환 상수 · 용량을 넘기면 참조 전부 무효**((1) · cppreference).
- ★★★ **`deque` 는 양끝 삽입에 참조가 유지된다 · 연속은 아니다**((1)의 200 개 행).
- ★★ **`list`·`forward_list` 는 원소마다 할당하고 원소가 움직이지 않는다**((1)).
- ★★★ **재할당은 `move_if_noexcept` 로 옮긴다 — `noexcept` 이동이 없고 복사가 되면 복사**((3) · 17편 (3)).
- ★★ **배수는 구현이다** — 이 판 2 배((2)).

## 어디서 틀리나

### 1. ★★★ 「`deque` 도 연속이다」

(1)의 **16 개 행이 「예」라서 그렇게 보인다.** 200 개 행이 **「아니오」** 다. 한 칸에 다 들어간 것뿐이다 — **작은 입력으로 성질을 말하지 마라.**

### 2. ★★★ 「`vector` 에 넣은 원소의 주소는 그대로다」

(1) — **`reserve` 없이 16 개 넣으면 주소가 바뀐다.** 43편의 무효화 격자가 그 뒤를 잇는다.

### 3. ★★★ 「`vector` 는 두 배로 늘린다(표준)」

(2) — **표준은 「분할 상환 상수」만** 말한다. 두 배는 이 판의 libstdc++ 다.

### 4. ★★ 「`noexcept` 가 없으면 항상 복사한다」

(3)의 **`MoveOnlyThrowing` 은 옮긴다** — 복사가 없으면 고를 것이 없다. 대가는 **강한 보장**이다.

### 5. ★★ 「`list` 는 느리다 / `vector` 는 빠르다」

이 문서는 **시간을 재지 않았다.** 말할 수 있는 것은 **할당 16 회 대 5 회(또는 1 회) · 연속 아님 대 연속**뿐이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」 칸과 「라이브러리 구현」 칸이 거의 반씩이다** — 선택의 근거는 **표준 칸으로만** 세운다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **`vector`·`array` 연속 · `push_back` 분할 상환 상수 · 재할당 시 참조 무효 · `deque` 양끝 삽입 참조 유지 · `list` 참조 유지 · `move_if_noexcept` 규칙** | cppreference · (1)(3) | — |
| **조건부 표준** | 특정 판에서만 | ★ **`array`·`forward_list`·`move_if_noexcept` C++11** | — | — |
| **구현 정의 · 라이브러리** | 문서화 의무 없음 | ★★★ **2 배 · 첫 capacity 1 · `sizeof`(24 · 80 · 24 · 8) · `deque` 의 칸 크기와 빈 채 할당 2 회** | (1)(2) | ★★ **두 컴파일러가 같은 libstdc++** — 다른 구현은 못 잰 것 |
| **컴파일러의 것** | 표준 밖 | ★ 이 편에서는 **해당 없음** — 네 판 사이 갈린 칸 0 | (1) | — |
| **UB** | 아무 일이나 | ★ 이 편에서는 **던진 칸이 없다** — 무효가 된 참조를 **쓰는 것**은 43편 | — | — |

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 특별한 이유가 없다 | ★★★ **`vector`** | 연속((1)) · 끝 추가 분할 상환 상수 · 할당이 가장 적다(`reserve` 면 1 회) |
| 크기가 컴파일 때 정해진다 | ★★ **`array`** | 할당 0((1)) |
| 앞뒤로 넣고 빼며 **기존 원소를 가리켜 둔다** | ★★★ **`deque`** | 양끝 삽입에 참조 유지((1)) |
| 가운데 삽입·삭제가 잦고 **원소를 가리켜 둔다** · `splice` | ★★ **`list`** | 참조 전부 유지 — 대가는 원소마다 할당((1)) |
| 원소 타입의 이동이 던진다 | ★★ **이동 생성자에 `noexcept`** 를 붙일 수 있는지부터 | (3) · 17편 (3) |
| 개수를 미리 안다 | ★★ **`reserve(n)`** | 할당 5 → 1((1)) |

★★★ **기본값이 `vector` 인 이유** — 이 문서가 결정적으로 보인 것만으로 말하면: **연속이라 번호로 바로 찾고(C 배열·`data()` 로 넘길 수 있고)** · **할당 횟수가 가장 적고** · **머리가 작다.** 대가 하나는 **넣는 동안 원소가 움직인다**는 것이고, 그것이 필요 없을 때만 다른 것을 고른다.

## 핵심 문장

- ★★★ **16 개를 넣으면 `vector` 5 회 · `reserve` 1 회 · `deque` 2\~3 회 · `list` 16 회 할당 — 네 판 갈린 칸 0 / 96.**
- ★★★ **처음 원소의 주소가 바뀐 것은 `reserve` 없는 `vector` 하나** — `deque` 는 앞에 넣어도 그대로다.
- ★★★ **`deque` 의 「연속인가」는 16 개 「예」 · 200 개 「아니오」 — 작은 입력의 참은 근거가 아니다.**
- ★★★ **`capacity` 는 이 판에서 두 배(세 판 동일) — 표준은 분할 상환 상수만 약속한다.**
- ★★★ **`move_if_noexcept` 는 `noexcept` 이동이면 `T&&`, 아니면 `const T&` — 단 복사가 없으면 던지는 이동이어도 `T&&`(강한 보장 포기).**

## 관련 자료

- [`data-structure/01-dynamic-array/`](../../../../../data-structure/01-dynamic-array/) — ★★★ **동적 배열의 원리**(2 배 확장 · 분할 상환 · 캐시 지역성)는 거기. **여기는 표준 `vector` 가 무엇을 약속하나.**
- [`data-structure/02-linked-list/`](../../../../../data-structure/02-linked-list/) — 연결 리스트의 원리. 여기는 **`list`·`forward_list` 의 할당·주소 안정성**만.
- [`data-structure/04-queue-deque/`](../../../../../data-structure/04-queue-deque/) — 덱의 원리 — 그쪽은 **원형 배열**로 구현하고 **꽉 차면 2 배 배열로 원소를 옮긴다**(「동작 — 확장」). ★ **표준 `deque` 는 양끝 삽입에 참조를 유지해야 하므로** 그렇게 옮기는 구현은 계약을 못 지킨다 — (1)의 「앞에 넣어도 주소 그대로」가 그 차이다.
- [17번](../17-move-constructor-assignment-and-moved-from-state/) (3) — ★★★ **`noexcept` 한 낱말이 재할당을 가른다** — (3)은 그 위에 **`move_if_noexcept` 직접 호출 + 셋째 타입**을 얹었다.
- [18번](../18-rule-of-zero-three-five-default-delete/) — 특수 멤버를 쓰는 법이 컨테이너의 행동을 바꾼다(`= delete` 복사 → (3)의 셋째 타입).
- 목록의 **43번 주제** — 무효화 규칙 전체와 **무효가 된 참조를 쓰면** 무엇이 나오나.
- Rust 갈래 [38번](../../../rust/syntax/38-vec-api-capacity-retain-and-drain/) — ★★ **`push` 는 꽉 찼을 때만 재할당(보장) · 몇 배인지는 보장 아님(이 판 두 배)** — 같은 결론을 Rust 쪽에서 냈다.

## 용어 풀이

> **순차 컨테이너(sequence container)** — 원소를 **넣은 순서(위치)** 로 두는 컨테이너. `vector`·`array`·`deque`·`list`·`forward_list`.\
> 예: (1).

> **용량(capacity)** — `vector` 가 **재할당 없이** 담을 수 있는 원소 수. `size()` 와 다르다.\
> 예: (2)의 수열.

> **재할당(reallocation)** — 용량이 모자라 **더 큰 버퍼를 새로 잡고 원소를 옮기는 것.** 참조·이터레이터가 전부 무효가 된다.\
> 예: (1)의 「처음 원소 주소가 바뀜」.

> **분할 상환 상수(amortized constant)** — 가끔 드는 큰 비용을 여러 번에 나눠 평균하면 상수라는 뜻.\
> 예: `push_back` 의 복잡도 — 원리는 data-structure 01.

> **`std::move_if_noexcept`** — 이동이 `noexcept` 이거나 복사가 불가능하면 `T&&`, 아니면 `const T&` 를 돌려주는 캐스트.\
> 예: (3).

> **강한 예외 보장(strong guarantee)** — 연산이 던지면 **하기 전 상태 그대로**. `vector` 재할당이 복사를 고르는 이유.\
> 예: (3)의 셋째 타입이 이것을 잃는다.

## 더 들어가면

- **시간 격자** — 「연속이면 순회가 빠르다」는 **N 판 판 격자**로만 말할 수 있다. 이 편은 **돌리지 않았다.**
- **던지는 이동으로 재할당하면** — `MoveOnlyThrowing` 의 이동이 **실제로 던지는 판**은 돌리지 않았다(목록의 **52번 주제** — 예외 안전 보장).
- **`shrink_to_fit`·`insert` 가운데** — 이 편은 끝 추가만 봤다. 가운데 삽입의 무효화는 목록의 **43번 주제**.
