# cpp/syntax/29 — `new`/`delete` 와 raw 포인터가 남는 자리 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — `new` 식](https://en.cppreference.com/w/cpp/language/new) · [cppreference — `std::bad_array_new_length`](https://en.cppreference.com/w/cpp/memory/new/bad_array_new_length)\
> ★ **cppreference 의 `new` 식 쪽은 이 배치에서 열었다** — 「배열 크기가 음수면 `bad_array_new_length` 와 맞는 예외」 조항만 읽었고, (3)이 그것과 **다른 관찰**을 싣는다. 나머지 규칙은 **실행·ASan·정적 분석기·`-O2` 어셈블리**로 적었다.
> **실행 검증** — 이 문서의 모든 출력·리포트·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`raw01.cpp` \~ `raw05.cpp` · `raw-grid.sh` · `raw-asm.sh`).\
> ★★★ **ASan 블록은 마커를 `stderr` 로 찍었다** · 자른 블록은 **자르는 명령을 배너에** 적었다 · clang + ASan 블록은 런타임 프레임의 절대 경로와 BuildId 를 `sed` 로 지웠다(그 `sed` 도 배너에 있다).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다. **시간은 한 번도 재지 않았다.**
> **버전** — `new`/`delete`·`new (std::nothrow)`·`std::bad_alloc` 은 **C++98부터**, **`std::bad_array_new_length` 는 C++11부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 실행으로 접지했다.
> ★★★ **[26번](../26-unique-ptr-and-ownership-transfer/)의 결론이다 — 앞 편들이 잰 것은 다시 재지 않고 인용한다.**\
> [26번](../26-unique-ptr-and-ownership-transfer/) (3) — **삭제자 크기 격자 「커진 칸 7 / 10」**(상태 없는 삭제자는 8 그대로) · (4) **배열을 `unique_ptr<T>` 에 맡기면 `Cell` 은 `bad-free` · `int` 는 `alloc-dealloc-mismatch`**(두 컴파일러) · (5) **`release()` 한 줄에 `Direct leak`, 경고 0 · 0** · ★★ (7) **C++11 식 `f(unique_ptr<W>(new W), g())` 의 누수는 두 컴파일러에서 재현되지 않았다**(g++ 는 `g()` 먼저, clang 은 `unique_ptr` 완성 뒤 — 「못 잰 것」).\
> [14번](../14-destructors-and-deterministic-destruction/) (6) — **`new D[3]` 을 `delete` 로 놓으면 소멸자 1회 · g++ `run exit=134`(`munmap_chunk(): invalid pointer`) · `-Wmismatched-new-delete` · ASan `bad-free`.**\
> [20번](../20-virtual-destructors-and-polymorphic-deletion/) (6) — **파생 배열을 기반 포인터로 `delete[]` 하면 g++ 는 SEGV, clang 은 `run exit=0` 인데 `~Derived` 0회·쓰레기 값** — ★ 이것은 **`delete` 대 `delete[]` 불일치가 아니라 「기반 포인터로 배열 지우기」** 다(두 사고를 섞지 마라).\
> [15번](../15-raii-resources-as-types/) — ★★ **ASan 은 메모리만 본다 — 파일 핸들·락은 못 본다.**\
> ★★ **여기서 새로 묻는 것은 셋이다** — **손으로 쓴 `new`/`delete` 사고 여섯을 도구 일곱이 각각 잡나** · **할당 실패는 무엇으로 오나** · **raw 포인터가 정당한 자리는 어디인가**.
> **경계** — 「RAII 가 못 지우는 것 — C API 경계에서는 전부 raw 포인터로 돌아간다」의 **논증은 [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) 의 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절**이 정본이다.\
> 「`malloc`/`free` 의 API 계약」은 C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **37번**(폴더 없음), 「C 의 다중 자원 해제」는 [C 13번 `goto cleanup`](../../../c/syntax/13-goto-cleanup-idiom/)이다.\
> 「예외와 되감기」는 목록의 **51번 주제**, 「이터레이터·포인터 무효화 규칙」은 목록의 **43번 주제**가 정본이다 — 여기서는 **raw 포인터 판단에 필요한 한 조각**만 던진다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 **PID**·주소 | ★★★ **사고 격자의 칸마다 도구가 댄 이름 · 「제 이름으로 댄 칸 N / 42」** — 이 주제의 답 자체다 |
> | ★ **clang + ASan 의 (2) 누수 판정** — 이 판에서는 **10 / 10 판 침묵**이었지만, 27편에서 같은 도구가 **판마다** 갈렸으므로 수를 성질로 적지 않는다 | ★★★ **`operator delete` · `_Unwind_Resume` 호출 수** · **잡은 예외 이름 · `q==nullptr`** · **ASan 오류 종류** · **`run exit`** |

## 한눈에 — 쉽게 말하면

**`new`/`delete` 는 「열쇠를 손으로 반납하는 코인 로커」이고, raw 포인터는 「로커 번호가 적힌 쪽지」다.**

`new` 로 로커를 빌리면 **반납은 전적으로 내 기억**에 달려 있다. 두 번 반납하거나(이중 해제), 잊거나(누수),\
다른 창구에 반납하거나(`delete` 대 `delete[]`·`free`), 중간에 쫓겨나면(예외) 반납할 기회가 없다.\
**번호 쪽지(raw 포인터)는 잘못이 아니다** — 쪽지로 **로커를 지우려 할 때**가 잘못이다.

- **쪽지만 보고 물건을 확인** — 비소유 관찰자. 로커 주인(소유자)이 **더 오래 산다는 것이 구조로 보장**되면 정당하다((4)).
- **다른 건물의 로커**(C 라이브러리) — 그 건물 창구(`fclose`·`free`)에 반납해야 한다. **반납 창구를 삭제자로 달아 두면** 잊을 일이 없다((4)(5)).
- **로커 번호 대신 줄 번호**(인덱스) — 로커 줄이 통째로 이사(`vector` 재할당)해도 **줄 번호는 유효**하다((4)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 손으로 반납 | ★★★ **`new` / `delete`** — 사고 여섯 | (1) |
| 두 번 반납 · 잊음 · 창구 착각 · 쫓겨남 | ★★★ **이중 해제 · 누수 · 짝 불일치 · 예외 경로** | (1)(2) |
| 쫓겨날 때 대신 반납해 주는 직원 | ★★★ **`unique_ptr` 의 되감기 경로 — `operator delete` 가 한 번 더** | (2) |
| 로커가 없다고 말하는 두 방식 | ★★ **`bad_alloc` 예외 대 `nothrow` 의 `nullptr`** | (3) |
| 번호 쪽지 | ★★★ **비소유 raw 포인터** — 네 자리 | (4) |
| 다른 건물 창구 | ★★ **`fopen`/`fclose` · `strdup`/`free` + 삭제자** | (4)(5) |
| 줄 번호 | ★★ **인덱스** — 재할당 뒤에도 유효 | (4) |

```text
   raw 포인터가 「무엇을 하느냐」로 가른다

   T* p 로  ─┬─ 가리키기만 한다 (관찰)      ── 정당 · 단, 수명을 누가 보장하나를 말할 수 있어야 한다
             ├─ C API 에 넘기고 받는다       ── 경계에서만 · 받는 즉시 삭제자 달린 unique_ptr 로
             └─ delete p 한다 (소유)         ── ★ 이것이 사고 여섯의 출발점
```

## 이 주제가 답하려는 질문

1. ★★★ **`new`/`delete` 를 직접 쓰면 나는 사고 여섯을 도구가 잡나** — 경고 · 정적 분석기 · ASan 을 칸마다((1)).
2. ★★★ **예외 경로 누수는 기계어에서 무엇이 없는 것인가**((2)).
3. ★★ **할당이 실패하면 무엇이 오나** — `bad_alloc` · `nullptr` · 그리고 ASan 아래에서는((3)).
4. ★★★ **raw 포인터가 정당한 자리는 어디인가** — 소유하나 · 수명을 누가 보장하나((4)(5)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ③ ASan 과 정적 분석기를 합친 「사고 × 도구」 격자다

★★★ **이 주제의 본체는 사고 격자다** — **사고 여섯 × 도구 일곱 = 42칸**을 스크립트가 채우고 센다.\
★★ **짝이 ④ `-O2` 어셈블리(예외 경로)** 다. **⑥ 크기는 26편 인용.**

```text
① 다섯 층 표            이중 해제 · 짝 불일치 · 해제 후 사용은 UB · 누수는 UB 가 아니다       (구현 세부사항 절)
② 두 컴파일러 대조       경고 · 분석기 · ASan 을 두 컴파일러로                              (1)(3)(4)
③ ★ ASan + 정적 분석기   사고 격자 42칸 · FILE 누수 침묵                                    (1)(5)
④ ★ 어셈블리(-O2)       raw 판 delete 1 · unique_ptr 판 delete 2 + _Unwind_Resume          (2)
⑤ 경고 격자             사고 격자의 경고 세 열(-Wall -O0 · -O2 · clang)                    (1)
⑥ <type_traits>·sizeof  삭제자 달린 unique_ptr 8 · 8 — 26편 격자 인용                      (4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **UB 셋 · UB 아닌 누수 · 구현이 표준과 다르게 보인 자리 하나((3))** | **쓴다** |
| ② 두 컴파일러 대조 | ★★ 경고·ASan 열이 **컴파일러마다 다르다** — (2) 누수를 clang + ASan 이 놓친다 | **쓴다** |
| ★★★ **③ ASan + 정적 분석기** | ★★★ **본체** — `g++ -fanalyzer` · `clang++ --analyze` 를 **ASan 과 같은 격자**에 넣었다 | **쓴다** |
| ★★ **④ 어셈블리(-O2)** | ★★★ **예외 경로에 `operator delete` 가 있나** | **쓴다** |
| ⑤ 경고 격자 | ★★ 사고 격자의 **세 열**로 들어갔다 — 따로 세우지 않았다 | **쓴다(격자 안)** |
| ⑥ `sizeof` | ★ **인용** — 26편 (3)의 7 / 10 · (4)의 판에서 `sizeof` 두 줄만 찍혔다 | **인용** |

- ★★ **ASan 이 못 보는 것을 먼저 적어 둔다** — 15편 말대로 **메모리만** 본다. (5)가 보이듯 **`fopen` 한 `FILE` 을 안 닫아도 침묵**한다 — 그리고 (1)이 보이듯 **메모리 누수조차 컴파일러에 따라** 놓친다.

### (1) ★★★ 사고 여섯 × 도구 일곱 — 누가 무엇을 잡나

**언제 쓰나** — 「`new`/`delete` 를 직접 써도 도구가 잡아 주지 않나」를 따질 때.

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

```text
===== bash raw-grid.sh (exit=0) =====
(1) g++ -Wall -O0        -
(1) g++ -Wall -O2        -
(1) clang++ -Wall        -
(1) g++ -fanalyzer     O -Wanalyzer-possible-null-argument,-Wanalyzer-use-after-free
(1) clang++ --analyze  O cplusplus.NewDelete
(1) g++ ASan           O double-free
(1) clang++ ASan       O double-free
(2) g++ -Wall -O0        -
(2) g++ -Wall -O2        -
(2) clang++ -Wall        -
(2) g++ -fanalyzer     O -Wanalyzer-malloc-leak,-Wanalyzer-possible-null-argument
(2) clang++ --analyze  O cplusplus.NewDeleteLeaks
(2) g++ ASan           O Direct-leak
(2) clang++ ASan         -
(3) g++ -Wall -O0      O -Wmismatched-new-delete
(3) g++ -Wall -O2      O -Wmismatched-new-delete
(3) clang++ -Wall      O -Wmismatched-new-delete
(3) g++ -fanalyzer       -Wanalyzer-malloc-leak,-Wanalyzer-possible-null-dereference
(3) clang++ --analyze  O unix.MismatchedDeallocator
(3) g++ ASan           O bad-free
(3) clang++ ASan       O bad-free
(4) g++ -Wall -O0        -
(4) g++ -Wall -O2        -
(4) clang++ -Wall        -
(4) g++ -fanalyzer       -Wanalyzer-possible-null-argument
(4) clang++ --analyze    -
(4) g++ ASan           O Direct-leak
(4) clang++ ASan       O Direct-leak
(5) g++ -Wall -O0        -
(5) g++ -Wall -O2        -
(5) clang++ -Wall        -
(5) g++ -fanalyzer     O -Wanalyzer-mismatching-deallocation
(5) clang++ --analyze  O unix.MismatchedDeallocator
(5) g++ ASan           O alloc-dealloc-mismatch
(5) clang++ ASan       O alloc-dealloc-mismatch
(6) g++ -Wall -O0        -
(6) g++ -Wall -O2      O -Wuse-after-free
(6) clang++ -Wall        -
(6) g++ -fanalyzer     O -Wanalyzer-possible-null-argument,-Wanalyzer-use-after-free
(6) clang++ --analyze  O cplusplus.NewDelete
(6) g++ ASan           O heap-use-after-free
(6) clang++ ASan       O heap-use-after-free
사고를 제 이름으로 댄 칸 24 / 42 · 없는 널을 짚은 칸 5
```

★ 격자를 손으로 한 장에 접으면(칸의 `O` 만 옮겼다 — **원본은 위 캡처**) —

```text
                       g++ -Wall  g++ -Wall  clang   g++          clang      g++    clang
   사고                  -O0        -O2      -Wall   -fanalyzer   --analyze  ASan   ASan
   (1) 이중 delete        .          .         .        O            O         O      O
   (2) delete 누락        .          .         .        O            O         O      .
   (3) new[] + delete     O          O         O        .            O         O      O
   (4) 예외 경로 누수      .          .         .        .            .         O      O
   (5) strdup + delete    .          .         .        O            O         O      O
   (6) delete 뒤 읽기      .          O         .        O            O         O      O
   ★ 제 이름으로 댄 칸 24 / 42 · 없는 널을 짚은 칸 5 (g++ -fanalyzer)
```

- ★★★ **경고 세 열은 거의 비었다** — `-Wall -Wextra` 로 잡힌 것은 **(3) 짝 불일치(세 열 다)와 (6)을 `-O2` 에서만(`-Wuse-after-free`)**. **이중 해제·누수·예외 경로·C 버퍼 불일치는 경고 0.**
- ★★★ **정적 분석기는 많이 잡는다 — 그런데 둘이 서로 다른 곳을 놓친다.**\
  **`clang++ --analyze` 는 (4) 예외 경로 누수를 놓쳤고**, **`g++ -fanalyzer` 는 (3)을 「짝 불일치」가 아니라 「누수」로 불렀고 (4)도 놓쳤다.**\
  ★★ **`g++ -fanalyzer` 는 5칸에서 「`operator new` 가 널일 수 있다」(`-Wanalyzer-possible-null-*`)를 짚었다** — 던지는 `new` 는 널을 돌려주지 않는다((3)). **없는 문제를 짚은 것**이다.
- ★★★ **ASan 은 (4)까지 잡는다** — 실행이 그 경로를 **실제로 지나갔기** 때문이다. 그런데 **clang + ASan 은 (2) 누수를 놓쳤다.**
- ★★★ **(4) 예외 경로 누수는 두 ASan 만 잡는다** — 경고 **0**, 두 분석기 **0**. **실행으로만 보인다.**

★★ **(2)를 clang + ASan 으로 열 번 — 그리고 (4) 한 판의 전문.**

```text
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=2 raw01.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "clang + ASan (2) 10판 중 리포트가 나온 판 $n" (exit=0) =====
clang + ASan (2) 10판 중 리포트가 나온 판 0
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=2 raw01.cpp -o exa && n=0; for i in 1 2 3 4 5 6 7 8 9 10; do r=$(./exa 2>&1); case $r in *'SUMMARY: AddressSanitizer'*) n=$((n+1));; esac; done; echo "g++   + ASan (2) 10판 중 리포트가 나온 판 $n" (exit=0) =====
g++   + ASan (2) 10판 중 리포트가 나온 판 10
```

- ★★ **clang + ASan 은 (2)를 10판 모두 침묵**, g++ 는 **10 / 10**. 27편에서 같은 도구가 순환 누수를 **판마다** 놓쳤다 — 이 판에서는 **매번** 놓쳤다. **수는 성질로 적지 않는다**(흔들리는 칸) — 주장은 「**놓친다**」뿐이다.
- ★ 누수 판정은 LSan 이 **스택·레지스터를 보수적으로 훑어** 「아직 닿는 포인터」를 찾는 방식이다 — 죽은 칸에 주소가 남아 있으면 **닿는 것으로 본다**(27편 (3)의 설명과 같다). **이 판의 원인이 정확히 어느 칸인지는 재지 않았다.**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. -DACC=4 raw01.cpp -o exa && ./exa 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
(4) new 와 delete 사이에서 예외가 난다
    catch: work 실패
    accident() 에서 돌아왔다

=================================================================
==3371661==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 4 byte(s) in 1 object(s) allocated from:
    #0 0x73668e2fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x5afba50cd449 in accident() raw01.cpp:31
    #2 0x5afba50cd583 in main raw01.cpp:51

SUMMARY: AddressSanitizer: 4 byte(s) leaked in 1 allocation(s).
```

- ★★★ **`catch` 가 돌고, 호출자에게 돌아온 뒤, 종료 시점에 `Direct leak of 4 byte(s)`** — `delete p;` 는 `throw` **다음 줄**이라 한 번도 실행되지 않았다. **예외를 잡았다고 자원이 돌아오는 것이 아니다.**

### (2) ★★★ 예외 경로 — 기계어에서 무엇이 없나

**언제 쓰나** — 「`new` 와 `delete` 사이에 던질 수 있는 호출이 있다」는 것을 **코드 모양만으로** 알아볼 때.

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

```text
===== bash raw-asm.sh (exit=0) =====
g++      RAW     operator new 1 · operator delete 1 · _Unwind_Resume 0
g++      UNIQUE  operator new 1 · operator delete 2 · _Unwind_Resume 1
clang++  RAW     operator new 1 · operator delete 1 · _Unwind_Resume 0
clang++  UNIQUE  operator new 1 · operator delete 2 · _Unwind_Resume 1
```

- ★★★ **raw 판 — `operator delete` 1 · `_Unwind_Resume` 0.** `use(p)` 가 던지면 **그대로 호출자에게 튕겨 나간다** — 지울 코드가 **아예 없다.**
- ★★★ **`unique_ptr` 판 — `operator delete` 2 · `_Unwind_Resume` 1.** 하나는 정상 경로, 하나는 **던졌을 때 지우고 되감기를 이어 가는 경로**다. 두 컴파일러가 **같은 수**다.
- ★★ **「`unique_ptr` 는 비용이 0」이 아니다** — 정상 경로의 명령은 같지만 **되감기 경로가 따로 생긴다**(g++ 는 `.cold` 조각). **그 몫이 곧 (1)의 (4)를 막는 것**이다. 시간은 재지 않았다.

```text
   raw                                    unique_ptr
   new ─ use(p) ─ delete                  new ─ use(p) ─ delete          (정상)
            │                                     │
            └─ 던지면 ─▶ 호출자로 ★ 누수            └─ 던지면 ─▶ delete ─▶ _Unwind_Resume
```

### (3) ★★ 할당이 실패하면 — `bad_alloc` · `nullptr` · 그리고 ASan 아래에서는

**언제 쓰나** — 「`new` 의 결과를 `nullptr` 과 비교해야 하나」를 판단할 때.

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex 16 2>&1 (cc exit=0 · run exit=0) =====
n = 16
(1) new char[n]                  성공 · p==nullptr 0
(2) new (std::nothrow) char[n]   q==nullptr 0
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex 4611686018427387904 2>&1 (cc exit=0 · run exit=0) =====
n = 4611686018427387904
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
===== g++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex -1 2>&1 (cc exit=0 · run exit=0) =====
n = -1
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
```

- ★★★ **던지는 `new` 는 `bad_alloc` 을 던지고, `new (std::nothrow)` 는 `nullptr` 을 돌려준다** — 2^62 바이트(주소 공간 밖)에서 두 모양이 갈렸다. **던지는 `new` 의 결과를 `nullptr` 과 비교하는 코드는 죽은 코드**다((1)의 `-fanalyzer` 헛짚음이 그 반대편이다).
- ★★★ **음수(`-1`)도 `bad_alloc`** 이었다 — 그런데 cppreference 의 `new` 식 쪽은 C++11부터 **「크기 식이 음수면 할당 함수를 부르지 않고 `bad_array_new_length` 와 맞는 예외를 던진다」** 고 적는다.\
  이 판(g++ 13 · clang 18 · libstdc++ 13)의 관찰은 **`bad_array_new_length` 핸들러가 잡지 않았다**(더 앞에 있는데도) — **두 컴파일러 다.**\
  ★★ **표준 조항 원문은 열지 못했다** — 그래서 「구현이 어긋났다」고 **판정하지 않고** 「**문서와 다른 관찰**」로만 적는다(제3의 상태).
- ★ **clang 도 같은 줄**이다 —

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex 4611686018427387904 2>&1 (cc exit=0 · run exit=0) =====
n = 4611686018427387904
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
===== clang++ -std=c++20 -Wall -Wextra -pedantic raw02.cpp -o ex && ./ex -1 2>&1 (cc exit=0 · run exit=0) =====
n = -1
(1) new char[n]                  catch bad_alloc: std::bad_alloc
(2) new (std::nothrow) char[n]   q==nullptr 1
```

★★★ **같은 2^62 를 ASan 아래에서 — `catch` 가 돌지 않는다.**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa && ./exa 4611686018427387904 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' (cc exit=0 · run exit=1) =====
n = 4611686018427387904
=================================================================
==3371847==ERROR: AddressSanitizer: requested allocation size 0x4000000000000000 (0x4000000000001000 after adjustments for alignment, red zones etc.) exceeds maximum supported size of 0x10000000000 (thread T0)
    #0 0x7a762d2fe6c8 in operator new[](unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98
    #1 0x647dd4138392 in main raw02.cpp:12

==3371847==HINT: if you don't care about these errors you may set allocator_may_return_null=1
SUMMARY: AddressSanitizer: allocation-size-too-big ../../../../src/libsanitizer/asan/asan_new_delete.cpp:98 in operator new[](unsigned long)
```

```text
===== echo "g++   $(g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa 2>&1; ./exa 4611686018427387904 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+')" (exit=0) =====
g++   SUMMARY: AddressSanitizer: allocation-size-too-big
===== echo "clang $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw02.cpp -o exa 2>&1; ./exa 4611686018427387904 2>&1 | grep -oE '^SUMMARY: AddressSanitizer: [a-z-]+')" (exit=0) =====
clang SUMMARY: AddressSanitizer: allocation-size-too-big
```

```text
   할당을 못 한다                   보통 빌드                     ASan 빌드
   new char[n]                      throw std::bad_alloc          ★ allocation-size-too-big 로 종료
   new (std::nothrow) char[n]       nullptr                       (도달하지 못한다)
   new char[-1]                     bad_alloc (이 판)             —
   ★ 「실패를 처리하는 코드」는 ASan 빌드에서 돌 기회가 없다
```

- ★★★ **ASan 은 `bad_alloc` 을 던지는 대신 `allocation-size-too-big` 로 프로그램을 죽인다**(`run exit=1`) — `n = …` 다음 줄이 **(1) `catch` 가 아니라 ASan 리포트**다. 두 컴파일러 다.\
  ★★ **도구가 프로그램의 동작을 바꾸는 자리**다 — 「할당 실패를 잡는 코드」는 **ASan 빌드에서 시험할 수 없다**(리포트의 `HINT` 가 `allocator_may_return_null=1` 을 권하지만, 예행에서 그 옵션을 줘도 **`out-of-memory` 로 다시 죽었다** — 본문에 블록을 싣지 않았다).

### (4) ★★★ raw 포인터가 정당한 네 자리 — 그리고 정당하지 않은 한 자리

**언제 쓰나** — 코드 리뷰에서 `T*` 를 보고 「소유인가 관찰인가」를 가를 때.

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

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa o 2>&1 (cc exit=0 · run exit=0) =====
(o) unique_ptr 가 소유하고 show() 는 .get() 을 받는다
    show: 7
    show: -1
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa c 2>&1 (cc exit=0 · run exit=0) =====
(c) fopen · strdup 의 결과를 삭제자 달린 unique_ptr 로 받는다
    sizeof 두 unique_ptr = 8 · 8
    free
    fclose
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa i 2>&1 (cc exit=0 · run exit=0) =====
(i) vector 원소를 인덱스로 들고 push_back 한다
    v[first].v = 1
    main 끝
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa t 2>&1 (cc exit=0 · run exit=0) =====
(t) 부모 r · 자식 x · 손자 y — 손자에서 뿌리까지 raw 포인터로 올라간다
    y -> x -> r
      ~Node r
      ~Node x
      ~Node y
    main 끝
```

- ★★★ **(o) 비소유 관찰자** — `show(const W*)` 는 **지우지 않는다** · `nullptr` 도 받는다(참조와 다른 점 — 07편). **`unique_ptr` 가 소유하고 `.get()` 을 넘긴다.**
- ★★★ **(c) C API 경계** — `fopen`·`strdup` 의 결과를 **받는 즉시 삭제자 달린 `unique_ptr`** 에 넣었다. **`free` → `fclose` 순**(선언 역순)으로 돌고, 크기는 **8 · 8**(빈 삭제자 — 26편 (3)의 「8 로 남은 셋」과 같은 부류).
- ★★ **(i) 인덱스** — `push_back` 여덟 번 뒤에도 `v[first].v = 1`. **줄 번호는 이사를 견딘다.**
- ★★★ **(t) 트리의 부모 포인터** — 부모가 자식을 **`unique_ptr` 로 소유**하고, 자식은 부모를 **`Node*`** 로 가리킨다. 손자에서 뿌리까지 `y -> x -> r`, ASan **침묵**.\
  ★★ **정당한 이유는 수명이 구조로 보장되기 때문**이다 — 자식은 **부모의 멤버(`kids`)로서 부모보다 먼저 죽는다**(`~Node r` 본체가 돈 **뒤에** `kids` 가 파괴되어 `~Node x`·`~Node y`). [목록의 **28번 주제**](../28-weak-ptr-and-reference-cycles/)의 설계 A 를 **`weak_ptr` 없이** 만든 판이다.

★★★ **정당하지 않은 자리 — `vector` 원소를 raw 포인터로 들고 `push_back`.**

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa && ./exa p 2>&1 | sed -n '1,/^SUMMARY/p' | grep -vE '^    #[0-9]+ 0x[0-9a-f]+ in (_start|__libc_start)' | grep -vE '^(Shadow|  [A-Z]|  0x|=>0x)' (cc exit=0 · run exit=1) =====
(p) vector 원소를 raw 포인터로 들고 push_back 한다
=================================================================
==3371987==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010 at pc 0x612861505c45 bp 0x7ffc44d68ec0 sp 0x7ffc44d68eb0
READ of size 4 at 0x502000000010 thread T0
    #0 0x612861505c44 in main raw04.cpp:50

0x502000000010 is located 0 bytes inside of 8-byte region [0x502000000010,0x502000000018)
freed by thread T0 here:
    #0 0x723b566ff5e8 in operator delete(void*, unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:164
    #1 0x61286150bb80 in std::__new_allocator<W>::deallocate(W*, unsigned long) /usr/include/c++/13/bits/new_allocator.h:172
    #2 0x612861508e7a in std::allocator<W>::deallocate(W*, unsigned long) /usr/include/c++/13/bits/allocator.h:210
    #3 0x612861508e7a in std::allocator_traits<std::allocator<W> >::deallocate(std::allocator<W>&, W*, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:517
    #4 0x612861508e7a in std::_Vector_base<W, std::allocator<W> >::_M_deallocate(W*, unsigned long) /usr/include/c++/13/bits/stl_vector.h:390
    #5 0x61286150a7db in void std::vector<W, std::allocator<W> >::_M_realloc_insert<W>(__gnu_cxx::__normal_iterator<W*, std::vector<W, std::allocator<W> > >, W&&) /usr/include/c++/13/bits/vector.tcc:519
    #6 0x61286150906e in W& std::vector<W, std::allocator<W> >::emplace_back<W>(W&&) /usr/include/c++/13/bits/vector.tcc:123
    #7 0x61286150824d in std::vector<W, std::allocator<W> >::push_back(W&&) /usr/include/c++/13/bits/stl_vector.h:1299
    #8 0x612861505be2 in main raw04.cpp:49

previously allocated by thread T0 here:
    #0 0x723b566fe548 in operator new(unsigned long) ../../../../src/libsanitizer/asan/asan_new_delete.cpp:95
    #1 0x612861508175 in std::__new_allocator<W>::allocate(unsigned long, void const*) /usr/include/c++/13/bits/new_allocator.h:151
    #2 0x6128615074c5 in std::allocator<W>::allocate(unsigned long) /usr/include/c++/13/bits/allocator.h:198
    #3 0x6128615074c5 in std::allocator_traits<std::allocator<W> >::allocate(std::allocator<W>&, unsigned long) /usr/include/c++/13/bits/alloc_traits.h:482
    #4 0x6128615074c5 in std::_Vector_base<W, std::allocator<W> >::_M_allocate(unsigned long) /usr/include/c++/13/bits/stl_vector.h:381
    #5 0x612861506db3 in void std::vector<W, std::allocator<W> >::_M_range_initialize<W const*>(W const*, W const*, std::forward_iterator_tag) /usr/include/c++/13/bits/stl_vector.h:1692
    #6 0x6128615069c6 in std::vector<W, std::allocator<W> >::vector(std::initializer_list<W>, std::allocator<W> const&) /usr/include/c++/13/bits/stl_vector.h:682
    #7 0x612861505b27 in main raw04.cpp:47

SUMMARY: AddressSanitizer: heap-use-after-free raw04.cpp:50 in main
```

```text
===== echo "clang o · c · i · t · p : $(clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw04.cpp -o exa 2>&1; for m in o c i t p; do ./exa $m >/dev/null 2>&1; printf '%s ' $?; done)" (exit=0) =====
clang o · c · i · t · p : 0 0 0 0 1 
```

- ★★★ **`heap-use-after-free`** — `push_back` 이 재할당하며 **옛 버퍼를 `operator delete` 했고**(리포트의 `freed by` — `_M_realloc_insert`), `first` 는 **그 옛 버퍼**를 가리켰다.
- ★★ **clang + ASan 도 같다**(`o · c · i · t` 는 0, `p` 만 **1**).
- ★★ **(i) 와 (p) 는 같은 일을 하는데 하나는 줄 번호, 하나는 로커 번호**다 — **무엇이 수명을 보장하나**에서 갈린다. 무효화 규칙의 전모는 목록의 **43번 주제**다.

| 자리 | raw 포인터가 소유하나 | 수명을 누가 보장하나 | 이 문서의 실측 |
|---|---|---|---|
| ★★★ 비소유 관찰자(매개변수) | **아니다** | **호출자** — 호출이 끝날 때까지 소유자가 산다 | (o) 침묵 |
| ★★★ C API 경계 | **받는 순간만** — 즉시 삭제자로 넘긴다 | **삭제자 달린 `unique_ptr`** | (c) 침묵 · 8바이트 |
| ★★ 배열 인덱스 대용 | **아니다**(인덱스) | **컨테이너** — 재할당해도 줄 번호는 유효 | (i) 침묵 |
| ★★★ 트리의 부모 포인터 | **아니다** | **구조** — 자식은 부모의 멤버라 먼저 죽는다 | (t) 침묵 |
| ★★★ `vector` 원소를 가리키는 포인터 | 아니다 | ★ **아무도** — 재할당이 옛 버퍼를 지운다 | (p) **`heap-use-after-free`** |
| ★★★ `delete p` 하는 raw 포인터 | **그렇다** | ★ **사람의 기억** | (1) 사고 여섯 |

### (5) ★★ C API 경계를 안 감싸면 — `FILE` 을 안 닫아도 ASan 은 침묵한다

**언제 쓰나** — 「ASan 이 조용하니 자원이 새지 않았다」고 말하고 싶을 때.

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

```text
===== g++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw05.cpp -o exa && ./exa 2>&1 (cc exit=0 · run exit=0) =====
write_once() 에서 돌아왔다
===== clang++ -std=c++20 -fsanitize=address -g -ffile-prefix-map="$PWD"=. raw05.cpp -o exa && ./exa 2>&1 (cc exit=0 · run exit=0) =====
write_once() 에서 돌아왔다
```

- ★★★ **두 컴파일러의 ASan 이 모두 `run exit=0` · 리포트 0줄** — `fclose` 를 안 했는데.
- ★★ **`FILE` 구조체도 `malloc` 으로 잡히는데 왜 안 보이나** — glibc 가 **열린 스트림을 전부 자기 목록에 걸어 두기** 때문에 LSan 이 보기에 **「아직 닿는」** 메모리다(표준 스트림 목록 — 이 설명은 **구현에 대한 내 읽기**이고, 실측은 「침묵」 한 줄이다).\
  ★★★ **15편의 「ASan 은 파일 핸들을 못 본다」가 여기서 한 번 더** — **메모리로 만든 핸들조차** 못 본다.
- ★★ **처방은 (4)의 (c)** — 받는 즉시 `unique_ptr<FILE, FileCloser>` 에 넣으면 **닫는 것을 잊을 자리가 없다.**

## 문법 — 형태와 규칙

### 형태

```text
   T* p = new T(args);   delete p;            단일 — 짝이 맞아야 한다
   T* a = new T[n];      delete[] a;          배열 — delete 로 놓으면 UB (14편 · 26편)
   T* q = new (std::nothrow) T;               실패하면 nullptr (던지지 않는다)
   auto u = std::make_unique<T>(args);        소유는 이쪽으로 — 되감기 경로가 따라온다
   std::unique_ptr<FILE, FileCloser> f(std::fopen(...));    C API 경계
   void show(const T* p);                     비소유 관찰 — 지우지 않는다 · 널 가능
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (1)\~(5)가 **실행한 소스**로 보였다.

### 규칙

- ★★★ **소유하는 raw 포인터(`delete` 하는 포인터)를 두지 않는다** — 사고 여섯의 출발점이다((1)).
- ★★★ **`new` 와 해제 사이에 던질 수 있는 호출이 있으면 raw 판은 샌다** — `unique_ptr` 가 되감기 경로를 만든다((2)).
- ★★ **던지는 `new` 의 결과를 `nullptr` 과 비교하지 않는다** — 실패는 예외로 온다. 널로 받고 싶으면 **`new (std::nothrow)`**((3)).
- ★★★ **raw 포인터는 「누가 수명을 보장하나」를 한 문장으로 말할 수 있을 때만** — 호출자 · 구조 · 삭제자((4)).
- ★★ **C API 의 결과는 받는 즉시 삭제자 달린 `unique_ptr` 로** — ASan 은 안 닫힌 `FILE` 을 못 본다((5)).

## 어디서 틀리나

### 1. ★★★ 「`-Wall -Wextra` 면 `new`/`delete` 실수를 잡는다」

(1)이 반증이다 — **42칸 중 경고 열에서 잡힌 것은 (3) 세 칸과 (6)의 `-O2` 한 칸뿐**이다. 이중 해제·누수·예외 경로는 **경고 0**.

### 2. ★★★ 「정적 분석기가 있으면 ASan 은 필요 없다」

(1)이 반증이다 — **(4) 예외 경로 누수를 두 분석기 모두 놓쳤고**, `g++ -fanalyzer` 는 **없는 널을 5칸**에서 짚었다.

### 3. ★★★ 「ASan 이 누수를 알려 준다」

(1)이 반쯤 반증이다 — **clang + ASan 은 (2)를 10판 모두 침묵**했다. 그리고 (5)의 **`FILE` 은 두 ASan 모두** 못 봤다.

### 4. ★★ 「예외를 잡았으니 자원도 돌아왔다」

(1)의 `c29-exleak` 가 반증이다 — **`catch` 가 돌고 나서** `Direct leak`. (2)의 raw 판에는 **되감기 경로에 `delete` 가 없다.**

### 5. ★★ 「`new` 가 실패하면 `nullptr` 을 돌려준다」

(3)이 반증이다 — **`bad_alloc` 을 던진다.** `nullptr` 은 **`nothrow` 판**의 것이다. 그리고 **ASan 아래에서는 둘 다 아니고 죽는다.**

### 6. ★★ 「raw 포인터는 전부 나쁘다」

(4)가 반증이다 — **관찰 · C API 경계 · 트리의 부모 포인터**는 수명을 **누군가 보장**하는 한 정당하다. 나쁜 것은 **`delete` 하는 raw 포인터**와 **수명을 아무도 보장하지 않는 raw 포인터**(p)다.

### 7. ★★ 「20편의 g++ SEGV · clang 쓰레기는 `delete` 대 `delete[]` 불일치다」

20편 (6)을 다시 읽어라 — 그것은 **파생 배열을 기반 포인터로 `delete[]`** 한 사고다. **`new[]` + `delete`** 는 14편 (6)(g++ `run exit=134`)과 이 편 (1)의 (3)(ASan `bad-free`)이다.

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제의 급소는 「UB」 칸과 「UB 아닌 사고」 칸의 경계다** — 이중 해제는 UB 지만 **누수는 UB 가 아니다.** 그래서 **도구의 태도가 다르다.**

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **던지는 `new` 의 실패는 `bad_alloc`, `nothrow` 는 `nullptr`**((3)) · **예외가 나면 되감기 중 지역 객체의 소멸자가 돈다 — raw 포인터에는 소멸자가 없다**((2)) · **누수는 규칙 위반이 아니다** | 예외 이름 · `q==nullptr` · 호출 수 | ★★★ **(4) 예외 경로 누수 — 경고·분석기 0** |
| **조건부 표준** | 특정 판에서만 | ★★ **음수 크기의 `new[]` 는 C++11부터 `bad_array_new_length`**(cppreference) — ★ **이 판은 `bad_alloc` 이었다**((3)) | 두 컴파일러 `-1` | ★★ **표준 원문을 열지 못해 판정 보류** |
| **구현 정의** | 문서화 의무 | ★★ **할당 한도(2^62 가 실패)** · **`unique_ptr` 의 되감기 경로 모양**(`.cold` · `_Unwind_Resume`)((2)) · **glibc 의 스트림 목록**((5)) | `-O2 -S` · 실행 | ★ 명령 모양은 **x86-64 · 이 두 컴파일러**의 것 |
| **미명시** | 몇 가지 중 하나 | ★ 이 주제에는 **결론을 세운 칸이 없다** | — | — |
| **UB** | 아무 일이나 | ★★★ **이중 `delete`(1) · `new[]` + `delete`(3) · `malloc` 버퍼를 `delete`(5) · 해제 뒤 읽기(6) · 재할당 뒤 옛 포인터(p)** | ASan 오류 종류 | ★★ **ASan 없이는 이 판에서 무엇이 나올지 말할 수 없다** — 이 문서는 ASan 없는 실행 값을 **싣지 않았다** |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | 경고(두 컴파일러) | 분석기(두 컴파일러) | ASan (g++ · clang) |
|---|---|---|---|---|
| ★★★ **(4) 예외 경로 누수** | 표준(허용된 코드) | ★★★ **0 · 0** | ★★★ **0 · 0** | **잡음 · 잡음** |
| ★★★ **(2) `delete` 누락** | 표준(허용된 코드) | **0 · 0** | 잡음 · 잡음 | 잡음 · ★★ **침묵(10 / 10)** |
| ★★ **(1) 이중 `delete`** | UB | **0 · 0** | 잡음 · 잡음 | 잡음 · 잡음 |
| ★★ **(5) `strdup` + `delete`** | UB | **0 · 0** | 잡음 · 잡음 | 잡음 · 잡음 |
| ★★★ **안 닫은 `FILE`** | 표준(허용된 코드) | — | — | ★★★ **침묵 · 침묵** |
| ★★ **ASan 이 `bad_alloc` 대신 죽인다** | 도구의 동작 | — | — | ★★ **`allocation-size-too-big`** |
| ★★ **`-fanalyzer` 가 던지는 `new` 를 널 가능으로 봄** | 도구의 헛짚음 | — | ★ **5칸** | — |

- ★★★ **이 표의 결론** — **경고는 거의 아무것도 못 보고, 분석기는 경로를 못 보고, ASan 은 컴파일러와 자원 종류에 따라 못 본다.** 세 창이 **서로 다른 칸**을 비워 둔다 — **하나만 믿으면 그 칸이 샌다.**

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 이 편의 사고는 전부 **컴파일은 되는 코드**이고, ill-formed 가 아니라 **UB 또는 허용된 누수**다. `cc exit=0` 으로 조용히 통과한 **ill-formed** 는 없었다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 새 객체를 소유한다 | ★★★ **`make_unique`**(26번) · 공유면 `make_shared`(27번) | 되감기 경로가 따라온다((2)) |
| 함수가 객체를 **보기만** 한다 | ★★★ **`T&`**(널 불가) 또는 **`T*`**(널 가능) | (4)(o) · 07편 |
| C 라이브러리가 준 자원 | ★★★ **삭제자 달린 `unique_ptr`** | (4)(c) · (5) |
| 부모 포인터(부모가 자식을 소유) | ★★ **`T*`** — 구조가 수명을 보장 | (4)(t) · 공유 소유면 28번 |
| 컨테이너 원소를 오래 가리킨다 | ★★ **인덱스**(또는 무효화 규칙을 아는 반복자) | (4)(i)(p) · 43번 |
| 할당 실패를 값으로 받고 싶다 | ★ **`new (std::nothrow)`** | (3) — 단 ASan 빌드에서는 시험 못 한다 |
| `new`/`delete` 를 손으로 | ★ **할당자·자료구조를 직접 만들 때만** | (1) — 사고 여섯 |

## 핵심 문장

- ★★★ **손으로 쓴 `new`/`delete` 의 사고 여섯 × 도구 일곱에서 「제 이름으로 댄 칸」은 24 / 42** — 경고 열은 거의 비고, **예외 경로 누수는 두 ASan 만** 잡았다.
- ★★★ **raw 판의 예외 경로에는 `operator delete` 가 없다** — `unique_ptr` 판은 **`delete` 2 · `_Unwind_Resume` 1**(두 컴파일러).
- ★★★ **던지는 `new` 는 `bad_alloc`, `nothrow` 는 `nullptr`, ASan 아래에서는 `allocation-size-too-big` 으로 죽는다** — 음수 크기도 이 판은 **`bad_alloc`** 이었다.
- ★★★ **raw 포인터가 정당한 자리는 「수명을 누가 보장하나」를 말할 수 있는 자리** — 호출자 · 구조 · 삭제자. **`vector` 원소 포인터는 아무도 보장하지 않아 `heap-use-after-free`.**
- ★★ **clang + ASan 은 `delete` 누락을, 두 ASan 은 안 닫은 `FILE` 을 놓쳤다** — 「ASan 이 조용하다」는 「새지 않았다」가 아니다.

## 관련 자료

- [26번](../26-unique-ptr-and-ownership-transfer/) — ★★★ **이 편의 앞 절반.** 삭제자 크기 격자 7 / 10 · 배열 `bad-free`/`alloc-dealloc-mismatch` · `release()` 누수 · C++11 식 예외 안전 문제는 **재현되지 않았다**.
- [14번](../14-destructors-and-deterministic-destruction/) (6) — `new[]` + `delete` 의 소멸자 1회 · `run exit=134` · `-Wmismatched-new-delete`.
- [20번](../20-virtual-destructors-and-polymorphic-deletion/) (6) — 파생 배열을 기반 포인터로 `delete[]` — g++ SEGV · clang 조용한 쓰레기(**다른 사고**).
- [15번](../15-raii-resources-as-types/) — ASan 은 메모리만 본다 · RAII 로 세 경로를 덮기.
- [07번](../07-references-vs-pointers/) — 관찰자를 `T&` 로 받을지 `T*` 로 받을지(널 가능성).
- [목록의 **28번 주제**](../28-weak-ptr-and-reference-cycles/) — 공유 소유 트리의 부모 포인터는 `weak_ptr`. 이 편의 (t)는 **단독 소유 트리**다.
- [`c-cpp-csharp.md`](../../../c-cpp-csharp.md) — 「C++ — RAII는 해제를 잊는 실패를 지우고, 죽은 것을 가리키는 실패는 못 지운다」 절 — **「C API 경계에서는 전부 raw 포인터로 돌아간다」** 의 논증 정본.
- C 갈래 목록([`c/syntax/README.md`](../../../c/syntax/README.md))의 **37번**(`malloc`/`calloc`/`realloc`/`free`) — **폴더가 없다.** · [C 13번 `goto cleanup`](../../../c/syntax/13-goto-cleanup-idiom/) — C 에서 여러 자원을 되감는 법.
- 목록의 **43번 주제**(이터레이터 범주와 무효화 규칙) · **51번 주제**(예외와 스택 되감기).

## 용어 풀이

> **raw 포인터(원시 포인터)** — 스마트 포인터가 아닌 `T*`. **소유 여부를 타입이 말하지 않는다.**\
> 예: (4)의 `show(const W*)` · `Node* parent`.

> **비소유 관찰자(non-owning observer)** — 가리키기만 하고 **지우지 않는** 포인터·참조. 수명은 **다른 누군가**가 보장해야 한다.\
> 예: (4)의 (o) · (t).

> **이중 해제(double free)** — 이미 해제한 메모리를 **또 해제**하는 것. UB.\
> 예: (1)의 (1) — ASan `double-free`.

> **`std::bad_alloc`** — 던지는 `new` 가 메모리를 못 얻을 때 던지는 예외.\
> 예: (3)의 2^62.

> **`new (std::nothrow)`** — 실패하면 던지지 않고 **`nullptr` 을 돌려주는** `new`.\
> 예: (3)의 `q==nullptr 1`.

> **`_Unwind_Resume`** — 되감기 도중 **정리 코드(landing pad)** 를 돈 뒤 되감기를 이어 가는 런타임 함수. 이것이 보이면 **예외 경로에 할 일이 있다**는 뜻이다.\
> 예: (2)의 `unique_ptr` 판 1 · raw 판 0.

> **정적 분석기** — 실행하지 않고 **경로를 따라가며** 결함을 찾는 도구. 이 문서는 `g++ -fanalyzer` 와 `clang++ --analyze` 를 썼다.\
> 예: (1)의 두 열.

## 더 들어가면

- **`operator new` 교체 · `std::set_new_handler`** — 실패 시 부를 함수를 바꾼다. 이 문서는 던지지 않았다.
- **placement new 와 `std::destroy_at`** — 이미 있는 메모리에 객체를 만들고 지운다. `delete` 가 아닌 짝이 있다. 이 문서는 던지지 않았다.
- **`gsl::owner<T*>` 와 `not_null`** — raw 포인터에 **소유 여부를 이름으로** 붙이는 관례(가이드라인 지원 라이브러리). 이 문서는 던지지 않았다.
- **`allocator_may_return_null`** — ASan 이 할당 실패를 죽이지 않고 돌려주게 하는 옵션. 예행에서 **던지는 `new` 에는 효과가 없었다** — 원인은 재지 않았다.
