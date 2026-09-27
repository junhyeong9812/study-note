# cpp/syntax/29 — `new`/`delete` 와 raw 포인터가 남는 자리 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「이 포인터는 지우는 포인터인가 보기만 하는 포인터인가 — 보기만 한다면 수명은 누가 보장하나」** 를 가르는 것이다 — 「raw 포인터는 나쁘다」로 뭉개지 마라.
> **환경** — g++ 13.3.0 · clang 18.1.3 · libstdc++ 13 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「사고 × 도구」 격자다**(1번) — 경고 · 정적 분석기 · ASan 을 한 격자에 넣었다. ★★ 짝은 **`-O2` 어셈블리(2번).**
> ★ **시간은 한 번도 재지 않았다.**
> ★★★ **26편·14편이 잰 것은 다시 묻지 않는다** — 삭제자 크기 7 / 10 · 배열 `bad-free`/`alloc-dealloc-mismatch` · `release()` 누수 · `new[]` + `delete` 의 소멸자 1회와 `run exit=134`.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★★ 손으로 쓴 `new`/`delete` 여섯 판을 도구 일곱에 던진다 (예측)

```cpp
/* raw01.cpp */
// new/delete 를 손으로 쓸 때 나는 사고 여섯 — -DACC=1..6 으로 하나만 켠다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>

struct W {
    int v = 0;
    ~W() { std::fprintf(stderr, "      ~W\n"); }
};

void work(bool fail) { if (fail) throw std::runtime_error("work 실패"); }

__attribute__((noinline)) void accident() {
#if ACC == 1
    std::fprintf(stderr, "(1) 같은 포인터를 두 번 delete\n");
    W* p = new W;
    delete p;
    delete p;
#elif ACC == 2
    std::fprintf(stderr, "(2) delete 를 빠뜨린다\n");
    W* p = new W;
    p->v = 1;
#elif ACC == 3
    std::fprintf(stderr, "(3) new[] 로 잡고 delete 로 놓는다\n");
    W* p = new W[3];
    delete p;
#elif ACC == 4
    std::fprintf(stderr, "(4) new 와 delete 사이에서 예외가 난다\n");
    W* p = new W;
    try {
        work(true);
        delete p;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "    catch: %s\n", e.what());
    }
#elif ACC == 5
    std::fprintf(stderr, "(5) C 함수가 malloc 한 버퍼를 delete 로 놓는다\n");
    char* s = strdup("hello");
    delete s;
#elif ACC == 6
    std::fprintf(stderr, "(6) delete 한 뒤 읽는다\n");
    W* p = new W;
    delete p;
    std::fprintf(stderr, "    p->v = %d\n", p->v);
#endif
}

int main() {
    accident();
    std::fprintf(stderr, "    accident() 에서 돌아왔다\n");
}
```

```bash
# raw-grid.sh
# raw-grid.sh — 사고 여섯 × 도구 일곱. 도구가 댄 이름을 찍고, 사고를 제 이름으로 댔는지 센다
W='-std=c++20 -Wall -Wextra -pedantic'
A='-std=c++20 -fsanitize=address -g'
names_w() { $1 2>&1 | grep -oE '\[-W[a-z-]+\]|\[[a-z]+\.[A-Za-z]+\]' | tr -d '[]' | sort -u | paste -sd, -; }
names_a() { $1 $A -DACC=$2 raw01.cpp -o gx 2>/dev/null; ./gx 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [A-Za-z-]+|^(Direct|Indirect) leak' | sed 's/SUMMARY: AddressSanitizer: //; s/ leak/-leak/' | sort -u | paste -sd, -; }
want=('' 'double-free|use-after-free|NewDelete$' 'leak|Leaks' 'mismatch|Mismatch|bad-free' 'leak|Leaks' 'mismatch|Mismatch' 'use-after-free|NewDelete$')
hit=0; cells=0; wrong=0
for n in 1 2 3 4 5 6; do
  for t in 'g++ -Wall -O0' 'g++ -Wall -O2' 'clang++ -Wall' 'g++ -fanalyzer' 'clang++ --analyze' 'g++ ASan' 'clang++ ASan'; do
    case $t in
      'g++ -Wall -O0')     r=$(names_w "g++ $W -DACC=$n -c raw01.cpp -o /dev/null") ;;
      'g++ -Wall -O2')     r=$(names_w "g++ $W -O2 -DACC=$n -c raw01.cpp -o /dev/null") ;;
      'clang++ -Wall')     r=$(names_w "clang++ $W -DACC=$n -c raw01.cpp -o /dev/null") ;;
      'g++ -fanalyzer')    r=$(names_w "g++ -std=c++20 -fanalyzer -DACC=$n -c raw01.cpp -o /dev/null") ;;
      'clang++ --analyze') r=$(names_w "clang++ -std=c++20 --analyze -DACC=$n raw01.cpp -o /dev/null") ;;
      'g++ ASan')          r=$(names_a g++ $n) ;;
      'clang++ ASan')      r=$(names_a clang++ $n) ;;
    esac
    cells=$((cells+1)); mark=' '
    if printf '%s\n' "$r" | tr ',' '\n' | grep -qE "${want[$n]}"; then hit=$((hit+1)); mark='O'; fi
    case $r in *possible-null*) wrong=$((wrong+1));; esac
    printf '(%d) %-18s %s %s\n' "$n" "$t" "$mark" "${r:--}"
  done
done
rm -f gx raw01.plist
echo "사고를 제 이름으로 댄 칸 $hit / $cells · 없는 널을 짚은 칸 $wrong"
```

- ★★★ 사고마다 **`-Wall -Wextra` 가 경고하는 것**은 어느 것인가 — `-O2` 로 올리면 늘어나나?
- ★★★ **ASan 이 두 컴파일러 모두 잡는 것 · 한쪽만 잡는 것**은?
- ★★ 두 정적 분석기가 **놓치는 사고**는 — 그리고 **없는 문제를 짚는 칸**이 있나?

### 2. ★★★ `new` 와 `delete` 사이에 던질 수 있는 호출 (예측)

```cpp
/* raw03.cpp */
// 같은 일을 raw new/delete 와 unique_ptr 로 — 사이에 던질 수 있는 호출이 있다. -DASK_RAW · -DASK_UNIQUE
#include <memory>

struct W { int v; };
void use(W*);                       // 다른 번역 단위에 있다 — 던질 수 있다

#if defined(ASK_RAW)
void job() {
    W* p = new W{1};
    use(p);
    delete p;
}
#elif defined(ASK_UNIQUE)
void job() {
    auto p = std::make_unique<W>(W{1});
    use(p.get());
}
#endif
```

```bash
# raw-asm.sh
# raw-asm.sh — 두 판을 -O2 로 어셈블해 operator new · operator delete · _Unwind_Resume 호출을 센다
for c in g++ clang++; do
  for k in RAW UNIQUE; do
    asm=$($c -std=c++20 -O2 -S -o - -DASK_$k raw03.cpp)
    printf '%-8s %-7s operator new %d · operator delete %d · _Unwind_Resume %d\n' "$c" "$k" \
      "$(printf '%s\n' "$asm" | grep -cE '(call|jmp)[a-z]*[[:space:]]+_Znwm')" \
      "$(printf '%s\n' "$asm" | grep -cE '(call|jmp)[a-z]*[[:space:]]+_ZdlPv')" \
      "$(printf '%s\n' "$asm" | grep -cE '(call|jmp)[a-z]*[[:space:]]+_Unwind_Resume')"
  done
done
```

- ★★★ 두 판의 **`operator delete` 호출 수와 `_Unwind_Resume` 호출 수**는 — 두 컴파일러에서 같은가?
- ★★ 그 차이가 1번의 **어느 사고**를 설명하나?

### 3. ★★ 할당이 실패하는 크기를 실행 중에 준다 (예측)

```cpp
/* raw02.cpp */
// 할당이 실패하면 — new 는 던지고 new (std::nothrow) 는 nullptr 을 돌려주나. 크기는 실행 중에 정한다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstdlib>
#include <new>

int main(int argc, char** argv) {
    long long n = argc > 1 ? std::atoll(argv[1]) : 1;     // 원소 수 — 컴파일러가 미리 못 보게
    std::fprintf(stderr, "n = %lld\n", n);

    try {
        char* p = new char[n];
        std::fprintf(stderr, "(1) new char[n]                  성공 · p==nullptr %d\n", (int)(p == nullptr));
        delete[] p;
    } catch (const std::bad_array_new_length& e) {
        std::fprintf(stderr, "(1) new char[n]                  catch bad_array_new_length: %s\n", e.what());
    } catch (const std::bad_alloc& e) {
        std::fprintf(stderr, "(1) new char[n]                  catch bad_alloc: %s\n", e.what());
    }

    char* q = new (std::nothrow) char[n];
    std::fprintf(stderr, "(2) new (std::nothrow) char[n]   q==nullptr %d\n", (int)(q == nullptr));
    delete[] q;
}
```

- ★★★ `16` · `4611686018427387904` · `-1` 에서 `(1)`·`(2)` 는 각각 무엇을 찍나?
- ★★ `-1` 에서 **어느 `catch`** 가 잡나?
- ★★★ 같은 `4611686018427387904` 를 **ASan 빌드**로 돌리면 `(1)` 줄이 찍히나?

### 4. ★★★ raw 포인터가 남는 다섯 모양 (예측)

```cpp
/* raw04.cpp */
// raw 포인터가 남는 다섯 모양 — 인자 o · c · p · i · t 로 하나씩 돌린다
// 마커는 표준 오류로 찍는다 — sanitizer 가 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <vector>

struct W { int v; };

// (o) 비소유 관찰자 — 받기만 하고 지우지 않는다. 없을 수도 있다(nullptr)
void show(const W* w) { std::fprintf(stderr, "    show: %d\n", w ? w->v : -1); }

// (c) C API 경계 — 해제 함수를 삭제자로 단다
struct FileCloser { void operator()(std::FILE* f) const { std::fprintf(stderr, "    fclose\n"); std::fclose(f); } };
struct FreeDeleter { void operator()(void* p) const { std::fprintf(stderr, "    free\n"); std::free(p); } };

// (t) 트리 — 부모가 자식을 unique_ptr 로 소유하고, 자식은 부모를 raw 포인터로 가리킨다
struct Node {
    char name;
    Node* parent = nullptr;
    std::vector<std::unique_ptr<Node>> kids;
    explicit Node(char n) : name(n) {}
    Node* add(char n) {
        kids.push_back(std::make_unique<Node>(n));
        kids.back()->parent = this;
        return kids.back().get();
    }
    ~Node() { std::fprintf(stderr, "      ~Node %c\n", name); }
};

int main(int argc, char** argv) {
    const char* m = argc > 1 ? argv[1] : "o";
    if (std::strcmp(m, "o") == 0) {
        std::fprintf(stderr, "(o) unique_ptr 가 소유하고 show() 는 .get() 을 받는다\n");
        auto w = std::make_unique<W>(W{7});
        show(w.get());
        show(nullptr);
    } else if (std::strcmp(m, "c") == 0) {
        std::fprintf(stderr, "(c) fopen · strdup 의 결과를 삭제자 달린 unique_ptr 로 받는다\n");
        std::unique_ptr<std::FILE, FileCloser> f(std::fopen("/dev/null", "w"));
        std::unique_ptr<char, FreeDeleter> s(strdup("hello"));
        std::fputs(s.get(), f.get());
        std::fprintf(stderr, "    sizeof 두 unique_ptr = %zu · %zu\n", sizeof f, sizeof s);
    } else if (std::strcmp(m, "p") == 0) {
        std::fprintf(stderr, "(p) vector 원소를 raw 포인터로 들고 push_back 한다\n");
        std::vector<W> v{{1}, {2}};
        W* first = &v[0];
        for (int i = 0; i < 8; ++i) v.push_back({i});
        std::fprintf(stderr, "    first->v = %d\n", first->v);
    } else if (std::strcmp(m, "i") == 0) {
        std::fprintf(stderr, "(i) vector 원소를 인덱스로 들고 push_back 한다\n");
        std::vector<W> v{{1}, {2}};
        std::size_t first = 0;
        for (int i = 0; i < 8; ++i) v.push_back({i});
        std::fprintf(stderr, "    v[first].v = %d\n", v[first].v);
    } else {
        std::fprintf(stderr, "(t) 부모 r · 자식 x · 손자 y — 손자에서 뿌리까지 raw 포인터로 올라간다\n");
        Node r('r');
        Node* y = r.add('x')->add('y');
        std::fprintf(stderr, "    y -> %c -> %c\n", y->parent->name, y->parent->parent->name);
    }
    std::fprintf(stderr, "    main 끝\n");
}
```

- ★★ `c` 판에서 **`free` 와 `fclose` 의 순서**와 **두 `unique_ptr` 의 크기**는?
- ★★★ `i` 판과 `p` 판을 ASan 으로 돌리면 — 어느 쪽이 리포트를 내나, 무슨 이름으로?
- ★★ `t` 판의 **소멸자 순서**는 — 자식의 `parent` 는 부모보다 오래 사나?

### 5. ★★ `FILE` 을 닫지 않고 돌아온다 (예측)

```cpp
/* raw05.cpp */
// fopen 한 FILE 을 fclose 하지 않고 함수에서 돌아온다 — LeakSanitizer 는 무엇을 보고하나
#include <cstdio>

__attribute__((noinline)) void write_once() {
    std::FILE* f = std::fopen("/dev/null", "w");
    std::fputs("x", f);
}

int main() {
    write_once();
    std::fprintf(stderr, "write_once() 에서 돌아왔다\n");
}
```

- ★★★ 두 컴파일러의 ASan 은 무엇을 보고하나 — `run exit` 은?

### 6. ★★★ 예외를 잡은 뒤의 자원 (왜)

- ★★★ 1번의 (4)는 `catch` 가 **돌았는데도** 왜 새나 — 2번의 어느 숫자가 그것을 보이나?

### 7. ★★ raw 포인터가 정당한 자리 (경계)

- ★★★ 「소유하나 · 수명을 누가 보장하나」 두 칸으로 **정당한 네 자리**를 말하라.
- ★★ 4번의 `p` 판이 정당하지 **않은** 이유를 같은 두 칸으로 말하라.

### 8. ★★ 도구 셋이 비워 두는 칸 (경계)

- ★★★ 경고 · 정적 분석기 · ASan 은 각각 **무엇을 못 보나** — 1번과 5번에서 한 칸씩 대라.
- ★ 「ASan 빌드에서 할당 실패 처리를 시험한다」는 왜 성립하지 않나?

### 9. ★★ 음수 크기의 `new[]` (경계)

- ★★ 3번의 `-1` 결과는 cppreference 가 적은 것과 **무엇이 다른가** — 이 문서가 그것을 「구현이 틀렸다」로 적지 **않은** 이유는?

### 10. 다른 주제와 잇기 (연결)

- ★★ 20편 (6)의 「g++ SEGV · clang 쓰레기」는 **어떤 사고**였나 — `new[]` + `delete` 의 정본은 몇 편인가?
- ★★ 26편의 「C++11 식 `f(unique_ptr<W>(new W), g())` 누수」는 이 머신에서 **재현됐나** — 2번과 무엇이 같은 문제인가?
- ★ 「C API 경계에서는 전부 raw 포인터로 돌아간다」를 **논증한 문서**와 그 절은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
