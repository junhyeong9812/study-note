# cpp/syntax/35 — 인스턴스화와 헤더 배치 · 오류 읽기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「인스턴스는 정의와 쓰임이 만나는 번역 단위에서만 생긴다」** 와 **「내 줄은 사슬의 끝」** 두 가지를 칸마다 따라가는 것이다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · GNU ld·nm 2.42 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex`. 번역 단위가 둘인 문항은 **`-c` 로 따로 컴파일한 뒤 링크**한다.
> ★★★ **이 주제의 본체는 링커와 `nm -C`(1\~4번), 그리고 진단을 세는 격자(6번)다.**
> ★ **「부적용인 창」이 있다** — ASan(결론이 전부 링크·컴파일 단계에서 난다).
> ★★★ **25편이 잰 것은 다시 묻지 않는다** — `B` 는 다중 정의, `static inline` 변수는 `u`/`V`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 선언만 둔 헤더 (예측)

```cpp
/* box.h */
// 선언만 둔 헤더 — 멤버 함수의 정의는 box_def.cpp 에 있다
#pragma once
template <class T> struct Box {
    T v;
    T get() const;
};
```

```cpp
/* box_def.cpp */
// 멤버 함수 정의 — -DEXPLICIT 이면 끝에 명시적 인스턴스화 한 줄
#include "box.h"
template <class T> T Box<T>::get() const { return v; }
#ifdef EXPLICIT
template struct Box<int>;
#endif
```

```cpp
/* use_box.cpp */
// Box<int> 를 쓰는 쪽 — box.h 만 본다
#include <cstdio>
#include "box.h"
int main() {
    Box<int> b{42};
    std::printf("%d\n", b.get());
}
```

- ★★★ `-DEXPLICIT` 없이 두 파일을 `-c` 로 컴파일하고 링크하면? 컴파일 단계와 링크 단계 중 어디서 멈추나?
- ★★★ 그때 `nm -C box_def.o use_box.o` 는 각각 무엇을 보이나?
- ★★ `-DEXPLICIT` 를 켜면 링크되나 — `box_def.o` 의 기호 글자는?

### 2. ★★★ 클래스 전체 대 멤버 하나 (예측)

```cpp
/* install.cpp */
// 명시적 인스턴스화 — 클래스 전체(-DWHOLE) 대 멤버 하나. odd() 는 int 로는 컴파일될 수 없는 몸통이다
template <class T> struct Box {
    T v;
    T get() const { return v; }
    void odd() const { v.no_such_member(); }
};

#ifdef WHOLE
template struct Box<int>;
#else
template int Box<int>::get() const;
#endif
```

- ★★★ `-DWHOLE` 없이 · 있이 `-c` 로 컴파일하면 각각?

### 3. ★★★ 정의까지 둔 헤더 — 두 번역 단위 (예측)

```cpp
/* hbox.h */
// 정의까지 둔 헤더 — -DUSE_EXTERN 이면 Box<int> 의 암묵 인스턴스화를 막는다
#pragma once
template <class T> struct HBox {
    T v;
    T get() const { return v; }
};
#ifdef USE_EXTERN
extern template struct HBox<int>;
#endif
```

```cpp
/* hbox_a.cpp */
// 번역 단위 1 — HBox<int>::get 을 부르는 함수 하나
#include "hbox.h"
int from_a() { return HBox<int>{1}.get(); }
```

```cpp
/* hbox_b.cpp */
// 번역 단위 2 — main 에서 HBox<int>::get 을 부르고 from_a 도 부른다
#include <cstdio>
#include "hbox.h"
int from_a();
int main() { std::printf("%d %d\n", HBox<int>{2}.get(), from_a()); }
```

- ★★★ `-DUSE_EXTERN` 없이 링크하면 되나 — `nm -C hbox_a.o hbox_b.o` 에서 `HBox<int>::get` 의 글자는?

### 4. ★★ `extern template` (예측)

```cpp
/* hbox_inst.cpp */
// 명시적 인스턴스화 정의를 여기 한 곳에만 둔다
#include "hbox.h"
template struct HBox<int>;
```

```bash
# ext-opt.sh
# ext-opt.sh — extern template 을 켠 hbox_a.cpp 를 최적화 두 판으로. HBox<int>::get 을 밖에서 찾는(U) 기호가 남나
for c in g++ clang++; do for o in -O0 -O2; do
  $c -std=c++20 $o -DUSE_EXTERN -c hbox_a.cpp -o xa.o
  printf '%-8s %s  U HBox<int>::get 기호 %s개 · W 기호 %s개\n' "$c" "$o" \
    "$(nm -C xa.o | grep -c ' U HBox<int>::get')" "$(nm -C xa.o | grep -c ' W HBox<int>::get')"
done; done
rm -f xa.o
```

- ★★ `-DUSE_EXTERN` 으로 `hbox_a.o`·`hbox_b.o` 만 링크하면? `hbox_inst.o` 를 더하면?
- ★★★ `ext-opt.sh` 의 네 줄은?

### 5. ★★★ 네 겹의 사슬 (예측)

```cpp
/* deep01.cpp */
// 네 겹의 함수 템플릿 — 맨 안쪽 한 곳에서만 < 를 쓴다. Point 에는 < 가 없다
struct Point {
    int x, y;
};

template <class T> bool less_than(const T& a, const T& b) { return a < b; }
template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
template <class T> bool validate(const T (&arr)[2]) { return check_pair(arr); }

int main() {
    Point ps[2] = {{1, 2}, {3, 4}};
    return validate(ps);
}
```

- ★★★ 첫 `error:` 는 몇 행을 가리키나 — 13행은 진단의 어디에, 어떤 문구와 함께 나오나(두 컴파일러 각각)?

### 6. ★★★ 여덟 모양 × 컴파일러 둘 (예측)

```cpp
/* deep02.cpp */
// deep01 과 같은 네 겹 — 바깥 validate 에만 C++20 컨셉 제약을 붙였다.
// 기본은 직접 쓴 컨셉(a < b 한 줄), -DSTD_CONCEPT 이면 std::totally_ordered
#include <concepts>

struct Point {
    int x, y;
};

template <class T>
concept Less = requires(const T& a, const T& b) { a < b; };

template <class T> bool less_than(const T& a, const T& b) { return a < b; }
template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
#ifdef STD_CONCEPT
template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
#else
template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
#endif

int main() {
    Point ps[2] = {{1, 2}, {3, 4}};
    return validate(ps);
}
```

```cpp
/* deep03.cpp */
// 표준 라이브러리에서 — < 가 없는 타입의 vector 를 std::sort 로. -DRANGES 이면 std::ranges::sort
#include <algorithm>
#include <vector>

struct Point {
    int x, y;
};

int main() {
    std::vector<Point> v{{3, 4}, {1, 2}};
#ifdef RANGES
    std::ranges::sort(v);
#else
    std::sort(v.begin(), v.end());
#endif
}
```

```bash
# err-count.sh
# err-count.sh — 같은 실수(< 가 없는 타입)를 여덟 모양으로 × 컴파일러 둘. 진단을 세기만 한다
# 칸: 「경우;호출 줄을 찾을 글자」 — 호출 줄은 소스에서 grep 으로 찾는다
cases=('deep01.cpp;validate(ps)' 'deep02.cpp;validate(ps)' 'deep02.cpp -DSTD_CONCEPT;validate(ps)'
       'deep03.cpp;std::sort(' 'deep03.cpp -DRANGES;ranges::sort('
       'deep01.cpp -ftemplate-backtrace-limit=1;validate(ps)' 'deep03.cpp -ftemplate-backtrace-limit=1;std::sort('
       'deep02.cpp -DSTD_CONCEPT -fconcepts-diagnostics-depth=2;validate(ps)')
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "경우" "컴파일러" "cc exit" "총 줄" ": error: 줄" "첫 error 가 가리키는 곳" "그곳이 호출 줄인가" "호출 줄이 처음 나오는 줄" > t.tsv
for kc in "${cases[@]}"; do
  k="${kc%%;*}"; mark="${kc#*;}"
  set -- $k; f=$1
  call=$(grep -n -F "$mark" "$f" | head -n 1 | cut -d: -f1)
  for c in g++ clang++; do
    out=$($c -std=c++20 -Wall -Wextra -pedantic $k -o ex 2>&1); rc=$?
    total=$(printf '%s\n' "$out" | wc -l)
    errs=$(printf '%s\n' "$out" | grep -c ': error: ')
    first=$(printf '%s\n' "$out" | grep -m 1 ': error: ' | sed -E 's#^([a-z+]+): error: .*#(\1 자체)#; s#^([^:]*/)?([^/:]+):([0-9]+):.*#\2:\3#')
    at=$(printf '%s\n' "$out" | grep -n -m 1 "^$f:$call:" | cut -d: -f1)
    if [ "$first" = "$f:$call" ]; then same=O; else same=X; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$k" "$c" "$rc" "$total" "$errs" "$first" "$same" "${at:--}" >> t.tsv
  done
done
cat t.tsv
bad=$(awk -F'\t' 'NF != 8' t.tsv | wc -l)
[ "$bad" -eq 0 ] || { echo "칸 수가 어긋난 행 $bad"; exit 1; }
rows=$(( $(wc -l < t.tsv) - 1 ))
same=$(tail -n +2 t.tsv | awk -F'\t' '$7 == "O"' | wc -l)
nocall=$(tail -n +2 t.tsv | awk -F'\t' '$8 == "-"' | wc -l)
echo "첫 error 가 호출 줄을 가리킨 칸 $same / $rows · 호출 줄이 아예 안 나온 칸 $nocall / $rows"
rm -f ex t.tsv
```

- ★★★ 「그곳이 호출 줄인가」가 `O` 인 행은 어느 것들인가?
- ★★★ `deep01` 과 `deep02`(두 판)의 g++ 「총 줄」은 늘었나 줄었나?
- ★★ `-ftemplate-backtrace-limit=1` 행에서 「호출 줄이 처음 나오는 줄」은 두 컴파일러가 같은가?

### 7. ★★★ 헤더 정의와 두 번역 단위 (왜)

- ★★★ 3번의 링크 결과를 25편 (1)의 `int Cfg::count = 0;` 판과 견주어, 두 판이 갈리는 이유를 **`nm` 글자**로 말하라.

### 8. ★★ 표준 컨셉이 말한 이유 (왜)

- ★★ 6번의 `deep02.cpp -DSTD_CONCEPT` 에서 컴파일러가 `<` 가 아니라 `==` 를 탓한 이유는?

### 9. ★★★ 줄 수라는 칸 (경계)

- ★★★ 6번의 「총 줄」과 「첫 error 가 가리키는 곳」 중 어느 쪽을 결론의 근거로 삼아야 하나 — 왜?

### 10. ★★ `-O2` 판과 코드 크기 (경계)

- ★★ 4번의 `ext-opt.sh` 결과로 「`extern template` 이 코드 크기를 줄인다」고 말할 수 있나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 1번처럼 「선언은 헤더, 정의는 `.cpp`」로 나누는 것이 C 함수와 C++ 템플릿에서 각각 어떻게 되나(C 갈래 44번이 다룰 자리)?
- ★★ Rust 는 6번의 `deep01` 같은 코드를 어느 자리에서 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
