# cpp/syntax/30 — 댕글링 참조와 수명 연장 규칙 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「그 임시(또는 지역)는 정확히 어느 세미콜론에서 죽나」와 「어느 도구가 그것을 보나」** 두 가지다 — 「참조는 안전하다」·「ASan 이 잡는다」로 뭉개지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux · 대비 rustc 1.92.0 · go1.27.1.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「댕글링 × 도구」 격자다**(1번) — 경고 두 열 + ASan 네 열. ★★ 짝은 **소멸자 로그(4번)** 다.
> ★ **「부적용인 창」이 있다** — `<type_traits>`. 수명은 타입에 적히지 않는다.
> ★★★ **UB 를 읽은 값은 답이 아니다** — 이 편의 탐침은 값 대신 **「42 였나」 한 비트**만 찍는다. 그 비트도 **이 판의 한 결과**다.
> ★★★ **07편·14편·08편이 잰 것은 다시 묻지 않는다** — `const T& r = make();` 의 기본형 · 지역 반환의 `-Wreturn-local-addr` · `c_str()` 은 clang 만 경고 · `T&&` 도 늘린다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 일곱 모양을 여섯 도구에 던진다 (예측)

```cpp
/* dang01.cpp */
// 이미 죽은 것을 가리키는 일곱 모양 — -DPROBE=1..7 으로 하나만 켠다. 읽은 값이 42 인지만 찍는다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <algorithm>
#include <cstdio>
#include <string>
#include <string_view>
#include <vector>

struct S { int v; };

#if PROBE == 1
int& local_ref() { int x = 42; return x; }
#elif PROBE == 2
const S& pass(const S& s) { return s; }
#elif PROBE == 3
struct Box {
    std::vector<int> items_{42, 42, 42};
    const std::vector<int>& items() const { return items_; }
};
Box make_box() { return Box{}; }
#elif PROBE == 4
std::string make_text() { return std::string(40, '*') + "42"; }
#elif PROBE == 5
auto make_reader() {
    int x = 42;
    return [&] { return x; };
}
#elif PROBE == 7
struct View {
    const S& s;
    explicit View(const S& x) : s(x) {}
};
#endif

__attribute__((noinline)) int probe() {
#if PROBE == 1
    int& r = local_ref();
    return r;
#elif PROBE == 2
    const S& r = pass(S{42});
    return r.v;
#elif PROBE == 3
    int last = 0;
    for (int x : make_box().items()) last = x;
    return last;
#elif PROBE == 4
    std::string_view sv = make_text();
    return std::stoi(std::string(sv.substr(40)));
#elif PROBE == 5
    auto read = make_reader();
    return read();
#elif PROBE == 6
    int a = 41;
    const int& r = std::max(a + 1, a);
    return r;
#elif PROBE == 7
    View w(S{42});
    return w.s.v;
#endif
}

int main() {
    std::fprintf(stderr, "(%d) 읽은 값이 42 인가 %d\n", PROBE, (int)(probe() == 42));
}
```

```bash
# dang-grid.sh
# dang-grid.sh — 탐침 일곱 × 도구 여섯. 칸에는 도구가 댄 이름을, 침묵이면 - 를 찍는다
W='-std=c++20 -Wall -Wextra -pedantic'
A='-std=c++20 -fsanitize=address -g'
warn() { local w; w=$($1 $W -DPROBE=$2 -c dang01.cpp -o /dev/null 2>&1 | grep -oE 'warning: .*\[-W[a-z-]+\]' | grep -oE '\-W[a-z-]+' | sort -u | tr '\n' ' '); echo "${w:--}"; }
asan() { local r; $1 $A $3 -DPROBE=$2 dang01.cpp -o gx 2>/dev/null; r=$(./gx 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [A-Za-z-]+' | sed 's/SUMMARY: AddressSanitizer: //'); echo "${r:--}"; }
caught=0; cells=0; segv=0
printf '%-3s %-22s %-22s %-22s %-22s %-22s %-22s\n' '#' 'g++ -Wall' 'clang -Wall' 'g++ ASan -O0' 'clang ASan -O0' 'g++ ASan -O2' 'clang ASan -O2'
for n in 1 2 3 4 5 6 7; do
  row=("$(warn g++ $n)" "$(warn clang++ $n)" "$(asan g++ $n -O0)" "$(asan clang++ $n -O0)" "$(asan g++ $n -O2)" "$(asan clang++ $n -O2)")
  for c in "${row[@]}"; do cells=$((cells+1)); [ "$c" != "-" ] && caught=$((caught+1)); [ "$c" = "SEGV" ] && segv=$((segv+1)); done
  printf '%-3s %-22s %-22s %-22s %-22s %-22s %-22s\n' "$n" "${row[@]}"
done
rm -f gx
echo "잡은 칸 $caught / $cells (그중 SEGV 로 멈춘 칸 $segv)"
```

- ★★★ **g++ 경고와 clang 경고가 각각 잡는 탐침**은 — 둘 다 못 잡는 탐침이 있나?
- ★★★ `-O0` ASan 두 열과 **clang `-O2` ASan 열**은 각각 몇 칸을 잡나?
- ★★ 마지막 줄의 **「잡은 칸 N / 42」** 는?

### 2. ★★ ASan 옵션 하나만 바꿔 탐침 1 · 5 를 다시 (예측)

```bash
# dang-uar.sh
# dang-uar.sh — 함수가 돌아간 뒤의 스택을 읽는 두 탐침(1 · 5)을 ASan 옵션 하나만 바꿔 다시 돌린다
echo "ASAN_OPTIONS 환경 변수 = ${ASAN_OPTIONS-(설정 안 됨)}"
for n in 1 5; do
  for c in g++ clang++; do
    $c -std=c++20 -fsanitize=address -g -DPROBE=$n dang01.cpp -o gx 2>/dev/null
    for v in 1 0; do
      r=$(ASAN_OPTIONS=detect_stack_use_after_return=$v ./gx 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [A-Za-z-]+|^\([0-9]\) .*' | head -1)
      printf '탐침 %d  %-8s detect_stack_use_after_return=%d  ->  %s\n' "$n" "$c" "$v" "$r"
    done
  done
done
rm -f gx
```

- ★★★ 환경 변수를 안 준 판에서 탐침 5 는 이미 잡혔나 — `detect_stack_use_after_return=0` 이면?
- ★★ g++ 의 탐침 1 은 옵션에 따라 이름이 바뀌나?

### 3. ★★★ 임시를 참조에 묶는 일곱 모양 — 소멸자 로그 (예측)

```cpp
/* dang02.cpp */
// 임시를 참조에 묶는 일곱 모양 — 임시의 소멸자가 「다음 문장」 표시보다 먼저 찍히나 뒤에 찍히나
// 참조는 한 번도 읽지 않는다 — 소멸자가 찍히는 자리만 본다
#include <cstdio>
#include <utility>

struct T {
    int id;
    int m = 0;
    explicit T(int i) : id(i) {}
    ~T() { std::printf("      ~T(%d)\n", id); }
};

const T& pass(const T& x) { return x; }

struct H { const T& ref; };              // 참조 멤버를 가진 집합체

int main(int argc, char**) {
    bool flag = argc > 0;
    std::printf("(a) const T& r = T{1};\n");
    { const T& r = T{1};                       std::printf("    다음 문장\n"); (void)r; }
    std::printf("(b) const T& r = pass(T{2});\n");
    { const T& r = pass(T{2});                 std::printf("    다음 문장\n"); (void)r; }
    std::printf("(c) const int& r = T{3}.m;\n");
    { const int& r = T{3}.m;                   std::printf("    다음 문장\n"); (void)r; }
    std::printf("(d) T&& r = std::move(T{4});\n");
    { T&& r = std::move(T{4});                 std::printf("    다음 문장\n"); (void)r; }
    std::printf("(e) const T& r = flag ? T{5} : T{6};\n");
    { const T& r = flag ? T{5} : T{6};         std::printf("    다음 문장\n"); (void)r; }
    std::printf("(f) H h{T{7}};\n");
    { H h{T{7}};                               std::printf("    다음 문장\n"); (void)h; }
    std::printf("(g) H h(T{8});\n");
    { H h(T{8});                               std::printf("    다음 문장\n"); (void)h; }
    std::printf("(끝)\n");
}
```

- ★★★ `(a)`\~`(g)` 각각에서 `~T(n)` 은 **「다음 문장」 앞에 찍히나 뒤에 찍히나**?
- ★★ 두 컴파일러는 **어느 모양에** 경고하나 — 아무도 경고하지 않는 모양이 있나?

### 4. ★★ 범위 `for` 의 임시를 두 판으로 (예측)

```cpp
/* dang03.cpp */
// 범위 for 의 범위 식 안에서 만든 임시는 언제 죽나 — -std=c++20 과 -std=c++23 에 같은 파일을 던진다
// 본문은 x 를 읽지 않고 한 번 들어오면 나간다 — ~Holder 가 찍히는 자리만 본다
#include <cstdio>
#include <vector>

struct Holder {
    std::vector<int> items_{1, 2};
    const std::vector<int>& items() const { return items_; }
    ~Holder() { std::printf("    ~Holder\n"); }
};
Holder make() { return Holder{}; }

int main() {
    std::printf("__cplusplus = %ld · __cpp_range_based_for = %ld\n", __cplusplus, (long)__cpp_range_based_for);
    std::printf("(1) for (int x : make().items())\n");
    for (int x : make().items()) {
        (void)x;
        std::printf("    본문에 들어왔다\n");
        break;
    }
    std::printf("(2) 루프를 나왔다\n");
}
```

- ★★★ `-std=c++20` 과 `-std=c++23` 에서 `~Holder` 는 **「본문에 들어왔다」 앞인가 뒤인가** — 두 컴파일러에서?
- ★★ 네 판의 **`__cpp_range_based_for`** 값은 — 그 값으로 무엇을 판별하나?
- ★ g++ 의 `-std=c++23` 판 **`__cplusplus`** 는?

### 5. ★★★ 같은 세 모양을 Rust 로 (예측)

```rust
// dangle.rs
// C++ 의 댕글링 세 모양을 Rust 로 — --cfg 로 하나씩 켠다(local_ref · closure · view)
#[cfg(local_ref)]
fn local_ref<'a>() -> &'a i32 {
    let x = 42;
    &x
}

#[cfg(closure)]
fn make_reader() -> impl Fn() -> i32 {
    let x = 42;
    || x
}

fn main() {
    #[cfg(local_ref)]
    println!("{}", local_ref());
    #[cfg(closure)]
    println!("{}", make_reader()());
    #[cfg(view)]
    {
        let sv: &str = String::from("*42").as_str();
        println!("{}", sv);
    }
}
```

- ★★★ `--cfg local_ref` · `--cfg closure` · `--cfg view` 는 각각 **어떤 에러 코드**를 내나 — C++ 의 몇 번 탐침과 짝인가?

### 6. ★★ 지역의 주소를 Go 로 돌려준다 (예측)

```go
// esc.go
// C++ 에서 댕글링이 되는 두 모양을 Go 로 — 지역 변수의 주소와 그것을 잡은 클로저를 돌려준다
package main

import "fmt"

func localPtr() *int {
	x := 42
	return &x
}

func makeReader() func() int {
	y := 42
	return func() int { return y }
}

func main() {
	p := localPtr()
	r := makeReader()
	fmt.Println(*p == 42, r() == 42)
}
```

- ★★ `-gcflags='-m -l'` 은 `x` 에 대해 무엇이라 말하나 — 실행 결과는?
- ★ `y` 에는 왜 같은 말이 없나?

### 7. ★★★ 도구 없이 돌린 탐침이 기대값을 읽었다 (왜)

- ★★★ 이미 죽은 객체를 읽었는데 42 가 나오는 것은 **무엇을 증명하고 무엇을 증명하지 않나**?
- ★★ 그 값이 컴파일러·최적화 수준마다 갈리는 것을 보고 **「어디서 갈리는지」를 규칙으로 적지 않는 이유**는?

### 8. ★★★ 연장이 되는 모양과 안 되는 모양의 선 (경계)

- ★★★ 3번의 결과를 **한 문장 규칙**으로 — 무엇이 끼면 연장되지 않나?
- ★★ 이 규칙은 다섯 층 중 **어느 층**인가 — 그래서 3번의 로그를 근거로 써도 되는 이유는?

### 9. ★★ g++ 가 지역 참조 반환에 한 일 (왜)

- ★★ g++ 판 탐침 1 이 `stack-use-after-return` 이 아니라 `SEGV` 인 이유를 **기계어 한 줄**로?

### 10. ★★ 「`-std=c++23` 으로 빌드했다」 (경계)

- ★★★ 4번의 결과가 **C++23 표준이 틀렸다는 뜻이 아닌** 이유는 — 무엇으로 판별해야 하나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 「누가 해제하는가에는 답하지만 누가 아직 보고 있는가에는 답하지 않는다」는 문장과 **1번의 빈 칸**은 어떻게 이어지나 — 그 문장의 문서와 절은?
- ★ 29편의 `vector` 원소 포인터 사고는 이 편의 **어느 말**로 부를 수 있나?
- ★ 07편은 이 주제를 「그 앞의 한 겹」까지만 판다고 했다 — 그 한 겹은 무엇이었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
