# cpp/syntax/35 — 인스턴스화와 헤더 배치 · 오류 읽기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 14882 공개 작업 초안 — WG21 표준 문서 목록](https://www.open-std.org/jtc1/sc22/wg21/docs/standards) · [cppreference — 클래스 템플릿(암묵·명시적 인스턴스화)](https://en.cppreference.com/w/cpp/language/class_template)\
> ★ 이 배치에서 **위 cppreference 쪽을 열어 확인했다** — 「쓰이지 않는 멤버는 인스턴스화되지 않는다」 · 「클래스를 명시적 인스턴스화하면 **(이미 특수화되지 않은) 멤버마다** 같은 종류의 명시적 인스턴스화가 된다」 · 「`extern template` 은 암묵 인스턴스화를 건너뛰고 **다른 곳의 명시적 인스턴스화 정의를 쓴다 — 없으면 링크 에러**」 세 문장이다.\
> ★ 같은 쪽이 「**This can be used to reduce compilation times.**」라고 적지만 **이 문서는 컴파일 시간을 재지 않았다** — 그 주장은 옮기지 않는다.
> **실행 검증** — 이 문서의 모든 출력·진단·덤프는 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · **libstdc++ 13** · **GNU ld(binutils 2.42)** · GNU nm 2.42 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★ **이 주제는 번역 단위가 둘이어야 선다** — 블록마다 **`-c` 로 따로 컴파일한 뒤 `.o` 를 링크**했다(25편과 같은 이유 — 한 줄로 `g++ a.cpp b.cpp` 를 하면 링커 진단에 임시 파일 이름이 박힌다).\
> ★ **진단에 소스 경로가 박히지 않게 상대 경로로 컴파일**했다. 표준 헤더 경로(`/usr/include/c++/13/…`)는 그대로 남는다.\
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex` 이고, 블록마다 **소스 파일 이름이 다르다**(`box.h`·`box_def.cpp`·`use_box.cpp` · `hbox.h`·`hbox_a.cpp`·`hbox_b.cpp`·`hbox_inst.cpp` · `install.cpp` · `deep01.cpp` \~ `deep03.cpp` · `ext-opt.sh` · `err-count.sh`).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 사람이 옮겨 적은 줄은 하나도 없다. 소스 펜스의 배너도 **캡처가 찍은 것**이다.\
> ★★ **긴 표준 라이브러리 진단((6))은 거르는 명령을 배너에 적었다** — 실린 것은 「생략한 일부」가 아니라 **그 명령의 전체 출력**이고, 전문의 줄 수는 (8)의 스크립트가 센다.
> **버전** — 템플릿 인스턴스화 모델은 **C++98부터**, **`extern template` 은 C++11부터**, **컨셉·`requires` 는 C++20부터**다. 기준은 **C++20**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★★ **[31번](../31-function-templates-and-argument-deduction/)과 C 갈래 44번(헤더와 분할 컴파일 — 아직 폴더가 없다)에서 온다.** 앞 편들이 잰 것은 다시 재지 않고 인용한다.\
> [31번](../31-function-templates-and-argument-deduction/) (5) — **함수 템플릿의 인스턴스는 기호표에 `W`(약한 기호)로 남는다**(`W void by_ref<int>(int&)`) · [32번](../32-class-templates-and-ctad/) (6) — **멤버 함수는 쓰일 때만 만들어진다**(`odd` 는 기호가 없다).\
> [25번](../25-static-members-and-inline-variables/) (1) — **헤더에 정의한 정적 데이터 멤버는 두 번역 단위에서 `multiple definition`, `static inline` 이면 g++ `u` · clang `V` 로 합쳐진다.**\
> ★★ **여기서 새로 묻는 것은 둘이다** — **템플릿 정의를 어디에 두나**(`.cpp` 에만 두면 · 명시적 인스턴스화 · 헤더 정의 · `extern template`) · **긴 인스턴스화 오류에서 원인 줄을 찾는 법**(깊이 4의 사슬 · 표준 라이브러리 · 컨셉 전후 · 줄 수 격자).
> **경계** — 「ODR 일반과 모듈」은 목록의 **55번 주제**, 「컨셉 문법과 표준 컨셉」은 [목록의 **36번 주제**](../36-concepts-and-requires/), 「C 의 헤더 배치 규칙」은 C 갈래 44번이, 「링커 일반」은 [`compiler-pipeline/`](../../../../compiler-pipeline/)이 정본이다. 여기서 컨셉은 **오류가 어디로 옮겨 가나**만 본다.
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | 진단 **문구** · 링커 진단의 **`.text+0x…` 오프셋** · `nm` 의 **주소 칸** | ★★★ **링크가 되나(`cc exit`)** · **`undefined reference` 가 무엇의 이름인가** · ★★★ **`nm` 의 글자**(`W`·`U`·`T`)와 **기호의 유무** |
> | ★★★ **진단의 줄 수 · `: error:` 줄 수**((8)) — **이 판의 관찰**이다(규칙 24 — 한 판 값). 컴파일러 판이 바뀌면 바뀐다 | ★★★ **첫 에러가 가리키는 파일:줄 · 그것이 호출 줄인가(O/X)** · **호출 줄이 진단에 나오나** |
> | ★ `__stack_chk_fail` 같은 **배포판 기본 플래그가 만든 기호** | ★★ **`extern template` 판에서 `-O0` 은 `U`, `-O2` 는 `U` 가 사라진 것**((4)) — 두 컴파일러 같다 |

## 한눈에 — 쉽게 말하면

**템플릿은 「조립 설명서」이고, 인스턴스화는 「설명서대로 실물을 조립하는 것」이다.**

보통 함수는 **실물(기계어)을 한 공장(`.cpp`)에서 만들어 두고**, 다른 공장은 **이름(선언)만** 알고 링커가 이어 준다.\
템플릿은 다르다 — **실물을 만들려면 설명서 전체(정의)를 봐야 한다.** 설명서를 한 공장에만 두면 **다른 공장은 조립을 못 하고**, 설명서가 있는 공장은 **아무도 주문하지 않아 아무것도 안 만든다**((1)).

- **해법 셋** — 설명서를 **모든 공장에 복사**(헤더에 정의 — 공장마다 만들고 링커가 하나만 남긴다)((3)) · 설명서가 있는 공장이 **미리 몇 개 만들어 둔다**(명시적 인스턴스화)((2)) · 「**이건 저 공장에서 만들었으니 너는 만들지 마**」(`extern template`)((4)).
- **조립이 실패하면** 에러는 **설명서의 몇 쪽**(템플릿 몸통)을 먼저 가리키고, **누가 주문했나**(사용자 코드)는 **주문 경로 맨 끝**에 붙는다((5)).
- **주문을 받을 때 조건을 먼저 확인하면**(컨셉) — 에러가 **주문서 자리**(호출 줄)로 온다((7)).

| 비유 | 실체 | 이 문서에서 |
|---|---|---|
| 설명서 | ★★ **템플릿 정의** | (1) |
| 한 공장에만 둔 설명서 | ★★★ **정의가 `.cpp` 에만 — `undefined reference`** | (1) |
| 미리 만들어 둔다 | ★★★ **명시적 인스턴스화 `template struct Box<int>;`** | (2) |
| 모든 공장에 복사 | ★★★ **헤더 정의 — 양쪽 `.o` 에 `W`, 링커가 하나로** | (3) |
| 「너는 만들지 마」 | ★★ **`extern template struct HBox<int>;`** | (4) |
| 설명서의 몇 쪽 · 주문 경로 | ★★★ **첫 `error:` 줄 · `required from` 사슬** | (5)(6) |
| 주문서에서 조건 확인 | ★★★ **컨셉 제약 — 에러가 호출 줄로** | (7) |

```text
   box.h  (선언만)          box_def.cpp (정의)             use_box.cpp (Box<int> 를 쓴다)
   T get() const;           template<class T>             b.get()
                            T Box<T>::get() const {…}       │
                                  │                          ▼
                            아무도 Box<int> 를 안 씀      정의가 안 보인다 → 만들 수 없다
                                  ▼                          ▼
                            box_def.o : 기호 0개          use_box.o : U Box<int>::get() const
                                         └──── 링커 ────┘
                                     undefined reference to `Box<int>::get() const'
```

## 이 주제가 답하려는 질문

1. ★★★ **템플릿 정의를 `.cpp` 에 두면 왜 링크가 깨지나 — 무엇으로 고치나**((1)(2)).
2. ★★★ **헤더에 정의하면 두 번역 단위가 같은 함수를 가지는데 왜 다중 정의가 안 나나**((3)).
3. ★★ **`extern template` 은 무엇을 막고 무엇을 못 막나**((4)).
4. ★★★ **긴 인스턴스화 오류에서 내 코드의 줄은 어디에 있나 — 컨셉을 걸면 무엇이 바뀌나**((5)\~(8)).

## 동작 방식

### (0) 이 주제가 쓰는 창 — 본체는 ② 두 컴파일러·링커와 `nm`, 그리고 진단 세기다

★★★ **절반은 링커 이야기다** — 「어느 `.o` 에 무엇이 있나」는 **`nm -C` 의 글자**가 답한다(25편과 같은 창).\
★★★ **나머지 절반은 진단 자체가 데이터다** — 「오류가 몇 줄이고 첫 에러가 어디를 가리키나」를 **스크립트가 센다**((8)). 사람이 세면 틀린다.

```text
① 다섯 층 표            인스턴스화 규칙은 표준 · 진단 모양·줄 수는 컴파일러의 것          (구현 세부사항 절)
② ★ 두 컴파일러·링커     undefined reference · 링크 통과 · 진단 전문                      (1)~(7)
③ ASan                   —                                                              부적용
④ ★ 어셈블리 → 기호표    nm -C 의 W · U · 기호 0개                                       (1)~(4)
⑤ ★ 진단 세기 격자       경우 8 × 컴파일러 2 — 줄 수 · 첫 에러 자리 · 호출 줄             (8)
⑥ 최적화 두 판          extern template 판의 -O0 대 -O2                                 (4)
```

| 창 | 이 주제에서 | 쓰나 |
|---|---|---|
| ① 다섯 층 표 | ★★ **링크 결과와 `W`/`U` 의 뜻은 표준(ODR)·ABI, 진단의 모양과 줄 수는 컴파일러** | **쓴다** |
| ★★★ **② 두 컴파일러·링커** | ★★★ **두 컴파일러가 같은 GNU ld 를 불러 링커 줄이 같다**(25편) | **쓴다** |
| ③ ASan | ★ **부적용** — 이 편의 결론은 전부 **링크·컴파일 단계**에서 난다(18-B) | **안 쓴다** |
| ★★★ **④ → 기호표** | ★★★ **`box_def.o` 는 기호 0개** · **헤더 정의는 두 `.o` 에 `W`** · **`extern` 이면 `U`** — 어셈블리 대신 기호표(제5의 상태) | **쓴다(바꿔서)** |
| ★★★ **⑤ 진단 세기** | ★★★ **본체의 절반** — 16칸 중 **첫 에러가 호출 줄을 가리킨 칸 7 / 16 · 호출 줄이 아예 안 나온 칸 3 / 16** | **쓴다** |
| ⑥ 최적화 두 판 | ★★ **`extern template` 판에서 `-O2` 는 `U` 가 사라진다**((4)) | **쓴다** |

### (1) ★★★ 정의를 `.cpp` 에만 두면 — `undefined reference`

**언제 쓰나** — 「보통 함수처럼 선언은 헤더, 정의는 `.cpp`」로 템플릿을 나눴을 때.

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && g++ box_def.o use_box.o -o ex (cc exit=1) =====
/usr/bin/ld: use_box.o: in function `main':
use_box.cpp:(.text+0x2a): undefined reference to `Box<int>::get() const'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && clang++ box_def.o use_box.o -o ex (cc exit=1) =====
/usr/bin/ld: use_box.o: in function `main':
use_box.cpp:(.text+0x16): undefined reference to `Box<int>::get() const'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★★ **컴파일은 두 번 다 통과하고 링크에서 깨진다** — `undefined reference to 'Box<int>::get() const'`. 두 컴파일러가 **같은 GNU ld** 를 불러 **첫 줄이 같다**(오프셋만 다르다).

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && nm -C box_def.o use_box.o (exit=0) =====

box_def.o:

use_box.o:
                 U Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
```

- ★★★ **`box_def.o` 는 기호가 하나도 없다** — 정의가 **있는데** 아무도 `Box<int>` 를 쓰지 않았으니 **만들지 않았다**(32편 (6)의 「쓰일 때만」).
- ★★★ **`use_box.o` 는 `U Box<int>::get() const`** — 「**밖에서 찾아 달라**」. 쓰는 쪽은 **정의가 안 보여** 만들 수 없었다.
- ★ **두 파일 다 자기 할 일을 했다** — 틀린 것은 **정의와 쓰임이 한 번역 단위에서 만나지 않은 것**이다. C 갈래 44번이 다루는 「선언은 헤더, 정의는 `.c`」가 **템플릿에서는 통하지 않는** 이유다.

### (2) ★★★ 명시적 인스턴스화 — 정의가 있는 곳에서 미리 만든다

**언제 쓰나** — **쓰일 `T` 가 몇 개로 정해져 있고** 정의를 헤더에 드러내고 싶지 않을 때.

`box_def.cpp` 끝의 `#ifdef EXPLICIT` 한 줄 — `template struct Box<int>;` — 을 켠다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DEXPLICIT -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && g++ box_def.o use_box.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C box_def.o use_box.o (exit=0) =====

box_def.o:
0000000000000000 W Box<int>::get() const

use_box.o:
                 U Box<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DEXPLICIT -c box_def.cpp -o box_def.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c use_box.cpp -o use_box.o && clang++ box_def.o use_box.o -o ex && ./ex (cc exit=0 · run exit=0) =====
42
===== nm -C box_def.o use_box.o (exit=0) =====

box_def.o:
0000000000000000 W Box<int>::get() const

use_box.o:
0000000000000000 r .L.str
0000000000000000 r .L__const.main.b
                 U Box<int>::get() const
0000000000000000 T main
                 U printf
```

- ★★★ **링크가 되고 `42`** — 두 컴파일러 같다.
- ★★★ **`box_def.o` 에 `W Box<int>::get() const` 가 생겼다** · **`use_box.o` 는 여전히 `U`** — 링커가 `U` 를 `W` 로 잇는다. **명시적 인스턴스화 정의도 이 판에서는 `W`(약한 기호)** 로 나왔다(두 컴파일러 같다).
- ★★ **대가** — 쓰일 `T` 를 **정의 쪽이 미리 알아야** 한다. `EXPLICIT` 판 그대로 **`Box<double>` 을 쓰면** —

```cpp
/* use_box_d.cpp */
// Box<double> 을 쓰는 쪽 — box.h 만 본다
#include <cstdio>
#include "box.h"
int main() {
    Box<double> b{1.5};
    std::printf("%.1f\n", b.get());
}
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DEXPLICIT -c box_def.cpp -o box_def.o && g++ -std=c++20 -Wall -Wextra -pedantic -c use_box_d.cpp -o use_box_d.o && g++ box_def.o use_box_d.o -o ex (cc exit=1) =====
/usr/bin/ld: use_box_d.o: in function `main':
use_box_d.cpp:(.text+0x30): undefined reference to `Box<double>::get() const'
collect2: error: ld returned 1 exit status
```

- ★★★ **다시 `undefined reference`** — 이번에는 **`Box<double>::get() const`**. 명시 목록(`Box<int>`) 밖의 `T` 는 (1)과 같은 모양으로 깨진다.

**★★★ 클래스 전체를 명시적 인스턴스화하면 멤버를 전부 만든다** — 32편 (6)의 `odd()` 를 다시 쓴다.

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c install.cpp -o inst.o && nm -C inst.o (exit=0) =====
0000000000000000 W Box<int>::get() const
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c install.cpp -o inst.o && nm -C inst.o (exit=0) =====
0000000000000000 W Box<int>::get() const
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DWHOLE -c install.cpp -o inst.o (cc exit=1) =====
install.cpp: In instantiation of ‘void Box<T>::odd() const [with T = int]’:
install.cpp:9:17:   required from here
install.cpp:5:26: error: request for member ‘no_such_member’ in ‘((const Box<int>*)this)->Box<int>::v’, which is of non-class type ‘const int’
    5 |     void odd() const { v.no_such_member(); }
      |                        ~~^~~~~~~~~~~~~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DWHOLE -c install.cpp -o inst.o (cc exit=1) =====
install.cpp:5:25: error: member reference base type 'const int' is not a structure or union
    5 |     void odd() const { v.no_such_member(); }
      |                        ~^~~~~~~~~~~~~~~
install.cpp:9:17: note: in instantiation of member function 'Box<int>::odd' requested here
    9 | template struct Box<int>;
      |                 ^
1 error generated.
```

- ★★★ **멤버 하나(`template int Box<int>::get() const;`)만 만들면 통과 · `W Box<int>::get() const` 하나** — `odd()` 는 여전히 안 만든다.
- ★★★ **`-DWHOLE` 로 `template struct Box<int>;` 를 쓰면 `odd()` 에서 에러** — 두 컴파일러 다 **9행(`template struct Box<int>;`)을 원인으로** 적는다. cppreference — 클래스의 명시적 인스턴스화는 「**each of its non-inherited non-template members**」의 명시적 인스턴스화가 된다.
- ★ 그래서 **「`T` 에 따라 안 되는 멤버」가 있는 클래스는 통째로 명시적 인스턴스화할 수 없다** — 멤버 단위로 한다.

### (3) ★★★ 헤더에 정의하면 — 두 번역 단위가 같은 인스턴스를 만든다

**언제 쓰나** — 대부분의 템플릿. **표준 라이브러리가 이 방식**이다(`<vector>` 가 헤더에 정의를 싣는다).

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -c hbox_b.cpp -o hbox_b.o && g++ hbox_a.o hbox_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
0000000000000000 W HBox<int>::get() const
                 U __stack_chk_fail

hbox_b.o:
                 U from_a()
0000000000000000 W HBox<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf
===== clang++ -std=c++20 -Wall -Wextra -pedantic -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -c hbox_b.cpp -o hbox_b.o && clang++ hbox_a.o hbox_b.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
0000000000000000 W HBox<int>::get() const

hbox_b.o:
0000000000000000 r .L.str
                 U from_a()
0000000000000000 W HBox<int>::get() const
0000000000000000 T main
                 U printf
```

- ★★★ **두 `.o` 가 다 `W HBox<int>::get() const` 를 가졌는데 링크가 된다**(`2 1`) — **같은 함수의 정의가 두 벌**인데 `multiple definition` 이 안 난다.
- ★★★ **`W` 가 이유다** — 「약한 기호 — 여럿이어도 **하나만 남기고** 합쳐라」. 25편 (1)의 **`B`(자리를 가진 정의 — 둘이면 `multiple definition`)** 와 대비된다. 25편의 `static inline` 변수가 g++ `u` · clang `V` 로 합쳐진 것과 **같은 성질의 다른 글자**다.
- ★★ **언어 쪽 이유** — 클래스 안에서 정의한 멤버 함수는 **암묵적으로 `inline`** 이고, 템플릿의 인스턴스는 **여러 번역 단위에 있어도 된다**(같은 정의라면). `W` 는 **그 약속을 이 ABI 가 링커에게 전하는 방식**이다.

```text
                    nm 글자     두 .o 에 있으면
   int Cfg::count = 0;   B      ★ multiple definition          (25편 (1))
   static inline int     u / V  하나로 합친다                    (25편 (1))
   템플릿 인스턴스       W      ★ 하나로 합친다                   (3) · 31편 (5)
   extern template 쪽   U      밖에서 찾는다 — 없으면 undefined  (4)
```

### (4) ★★ `extern template` — 「여기서는 만들지 마」

**언제 쓰나** — **헤더 정의는 유지하되** 인스턴스를 **한 번역 단위에서만** 만들게 하고 싶을 때.

`hbox.h` 의 `-DUSE_EXTERN` 판(`extern template struct HBox<int>;`)으로 두 번역 단위를 컴파일한다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && g++ hbox_a.o hbox_b.o -o ex (cc exit=1) =====
/usr/bin/ld: hbox_a.o: in function `from_a()':
hbox_a.cpp:(.text+0x2a): undefined reference to `HBox<int>::get() const'
/usr/bin/ld: hbox_b.o: in function `main':
hbox_b.cpp:(.text+0x32): undefined reference to `HBox<int>::get() const'
collect2: error: ld returned 1 exit status
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && clang++ hbox_a.o hbox_b.o -o ex (cc exit=1) =====
/usr/bin/ld: hbox_a.o: in function `from_a()':
hbox_a.cpp:(.text+0x14): undefined reference to `HBox<int>::get() const'
/usr/bin/ld: hbox_b.o: in function `main':
hbox_b.cpp:(.text+0x14): undefined reference to `HBox<int>::get() const'
clang++: error: linker command failed with exit code 1 (use -v to see invocation)
```

- ★★★ **정의가 헤더에 다 보이는데도 `undefined reference`** — 두 번역 단위가 **만들지 말라는 말을 따랐고**, 만들어 둔 곳이 **없다.** cppreference 의 「없으면 링크 에러」 그대로다.

```cpp
/* hbox_inst.cpp */
// 명시적 인스턴스화 정의를 여기 한 곳에만 둔다
#include "hbox.h"
template struct HBox<int>;
```

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && g++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_inst.cpp -o hbox_inst.o && g++ hbox_a.o hbox_b.o hbox_inst.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o hbox_inst.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
                 U HBox<int>::get() const
                 U __stack_chk_fail

hbox_b.o:
                 U from_a()
                 U HBox<int>::get() const
                 U __stack_chk_fail
0000000000000000 T main
                 U printf

hbox_inst.o:
0000000000000000 W HBox<int>::get() const
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_a.cpp -o hbox_a.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_b.cpp -o hbox_b.o && clang++ -std=c++20 -Wall -Wextra -pedantic -DUSE_EXTERN -c hbox_inst.cpp -o hbox_inst.o && clang++ hbox_a.o hbox_b.o hbox_inst.o -o ex && ./ex (cc exit=0 · run exit=0) =====
2 1
===== nm -C hbox_a.o hbox_b.o hbox_inst.o (exit=0) =====

hbox_a.o:
0000000000000000 T from_a()
                 U HBox<int>::get() const

hbox_b.o:
0000000000000000 r .L.str
                 U from_a()
                 U HBox<int>::get() const
0000000000000000 T main
                 U printf

hbox_inst.o:
0000000000000000 W HBox<int>::get() const
```

- ★★★ **`hbox_inst.cpp` 한 곳에 명시적 인스턴스화를 두면 링크된다** — `hbox_a.o`·`hbox_b.o` 는 **`U`**, `hbox_inst.o` 만 **`W`**. (3)에서 **두 `.o` 에 있던 `W` 가 한 `.o` 로 모였다.**

**★★ 그런데 최적화를 켜면** —

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

```text
===== bash ext-opt.sh (exit=0) =====
g++      -O0  U HBox<int>::get 기호 1개 · W 기호 0개
g++      -O2  U HBox<int>::get 기호 0개 · W 기호 0개
clang++  -O0  U HBox<int>::get 기호 1개 · W 기호 0개
clang++  -O2  U HBox<int>::get 기호 0개 · W 기호 0개
```

- ★★★ **`-O2` 에서는 `U` 도 `W` 도 없다** — 두 컴파일러 같다. **`get()` 이 인라인되어 호출 자체가 사라졌다.** `extern template` 은 「**인스턴스를 만들지 마**」이지 「**정의를 쓰지 마**」가 아니다 — 인라인 함수는 여전히 펼쳐질 수 있다.
- ★ **이 블록은 「`extern template` 이 코드를 줄인다」·「컴파일이 빨라진다」의 근거가 아니다** — 이 문서는 **크기도 시간도 재지 않았다.** 보인 것은 **기호의 유무**뿐이다.

### (5) ★★★ 오류 읽기 — 깊이 4의 인스턴스화 사슬

**언제 쓰나** — 템플릿 안에서 에러가 났을 때마다. **내 코드의 어느 줄이 원인인가**를 찾는 법.

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic deep01.cpp -o ex (cc exit=1) =====
deep01.cpp: In instantiation of ‘bool less_than(const T&, const T&) [with T = Point]’:
deep01.cpp:7:75:   required from ‘bool ordered(const T&, const T&) [with T = Point]’
deep01.cpp:8:71:   required from ‘bool check_pair(const T (&)[2]) [with T = Point]’
deep01.cpp:9:72:   required from ‘bool validate(const T (&)[2]) [with T = Point]’
deep01.cpp:13:20:   required from here
deep01.cpp:6:70: error: no match for ‘operator<’ (operand types are ‘const Point’ and ‘const Point’)
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~~^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic deep01.cpp -o ex (cc exit=1) =====
deep01.cpp:6:70: error: invalid operands to binary expression ('const Point' and 'const Point')
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~ ^ ~
deep01.cpp:7:66: note: in instantiation of function template specialization 'less_than<Point>' requested here
    7 | template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
      |                                                                  ^
deep01.cpp:8:64: note: in instantiation of function template specialization 'ordered<Point>' requested here
    8 | template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
      |                                                                ^
deep01.cpp:9:62: note: in instantiation of function template specialization 'check_pair<Point>' requested here
    9 | template <class T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                                              ^
deep01.cpp:13:12: note: in instantiation of function template specialization 'validate<Point>' requested here
   13 |     return validate(ps);
      |            ^
1 error generated.
```

- ★★★ **첫 `error:` 는 두 컴파일러 다 6행** — `less_than` 의 몸통 `a < b` 다. **내 코드의 실수(`<` 가 없는 `Point` 를 넘긴 것)는 13행**인데 그 줄은 **에러 줄이 아니다.**
- ★★★ **g++ 는 사슬을 에러 앞에** 적는다 — `In instantiation of … less_than …` → `required from … ordered` → `check_pair` → `validate` → **`deep01.cpp:13:20:   required from here`**. ★ **「required from here」가 붙은 줄이 사용자 코드**다 — 사슬의 **맨 끝**(에러 바로 위)이다.
- ★★★ **clang 은 사슬을 에러 뒤에** 적는다 — `in instantiation of function template specialization 'less_than<Point>' requested here`(7행) → `ordered` → `check_pair` → **`validate<Point>' requested here` + 13행 소스**. **사슬의 마지막 `requested here`** 가 사용자 코드다.

```text
   g++                                         clang
   In instantiation of less_than [T = Point]   error 「invalid operands …」 (6행)
     required from ordered      (7행)          note 「less_than<Point> requested here」  (7행)
     required from check_pair   (8행)          note 「ordered<Point>   requested here」  (8행)
     required from validate     (9행)          note 「check_pair<Point> requested here」 (9행)
     required from here        ★(13행)         note 「validate<Point>  requested here」 ★(13행)
   error 「no match for operator<」 (6행)
   ★ 사용자 줄 = g++ 는 에러 「위」 맨 끝, clang 은 에러 「아래」 맨 끝
```

### (6) ★★ 표준 라이브러리 안에서 — `std::sort` 대 `std::ranges::sort`

**언제 쓰나** — 실무에서 가장 흔한 모양. **에러가 내 파일이 아니라 `/usr/include/…` 를 가리킨다.**

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

★★ **전문이 g++ 78줄 · clang 220줄이라**((8)이 센다) **거르는 명령을 배너에 적어 실었다** — 사용자 파일 줄(`^deep03`)과 `: error:` 줄만. **이것은 발췌다** — 전문은 `deep03.cpp` 를 배너의 명령에서 `| grep …` 를 빼고 던지면 나온다.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic deep03.cpp -o ex 2>&1 | grep -E '^deep03|: error: ' (cc exit=1) =====
deep03.cpp:14:14:   required from here
/usr/include/c++/13/bits/predefined_ops.h:45:23: error: no match for ‘operator<’ (operand types are ‘Point’ and ‘Point’)
deep03.cpp:14:14:   required from here
/usr/include/c++/13/bits/predefined_ops.h:98:22: error: no match for ‘operator<’ (operand types are ‘Point’ and ‘Point’)
deep03.cpp:14:14:   required from here
/usr/include/c++/13/bits/predefined_ops.h:69:22: error: no match for ‘operator<’ (operand types are ‘Point’ and ‘Point’)
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic deep03.cpp -o ex 2>&1 | grep -E '^deep03|: error: ' (cc exit=1) =====
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/predefined_ops.h:45:23: error: invalid operands to binary expression ('Point' and 'Point')
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/predefined_ops.h:69:22: error: invalid operands to binary expression ('Point' and 'Point')
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:1637:6: error: no matching function for call to object of type '__gnu_cxx::__ops::_Iter_less_iter'
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:88:11: error: no matching function for call to object of type '__gnu_cxx::__ops::_Iter_less_iter'
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:1877:11: error: no matching function for call to object of type '__gnu_cxx::__ops::_Iter_less_iter'
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:1880:11: error: no matching function for call to object of type '__gnu_cxx::__ops::_Iter_less_iter'
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:1819:8: error: no matching function for call to object of type '__gnu_cxx::__ops::_Iter_less_iter'
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/predefined_ops.h:98:22: error: invalid operands to binary expression ('Point' and 'Point')
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/bits/stl_algo.h:1864:2: error: no matching function for call to '__insertion_sort'
deep03.cpp:14:10: note: in instantiation of function template specialization 'std::sort<__gnu_cxx::__normal_iterator<Point *, std::vector<Point>>>' requested here
```

- ★★★ **에러 줄이 전부 표준 헤더 안이다** — `predefined_ops.h:45` · `stl_algo.h:1637` … . **내 파일의 줄은 `deep03.cpp:14`(g++ `required from here` · clang `requested here`) 하나뿐이고 에러마다 되풀이된다.**
- ★★ **g++ 는 `: error:` 3줄 · clang 은 9줄** — 같은 실수 하나에서. **에러 수는 실수의 수가 아니다.**

★★★ **`-DRANGES` 로 `std::ranges::sort(v)` 를 쓰면** — `ranges::sort` 는 **C++20 컨셉으로 제약된** 알고리즘이다.

- ★★★ (8)의 격자에서 **첫 에러가 `deep03.cpp:12`(호출 줄) · 두 컴파일러 다 `: error:` 1줄** — 에러가 **라이브러리 안에서 내 호출 자리로** 옮겨 왔다. 줄 수는 g++ 78 → 34 · clang 220 → 36(이 판의 관찰).

### (7) ★★★ 컨셉을 걸면 — 에러가 호출 줄로 온다

**언제 쓰나** — 내가 쓴 템플릿의 오류를 **쓰는 사람의 자리**로 끌어오고 싶을 때. 컨셉 자체의 정본은 [목록의 **36번 주제**](../36-concepts-and-requires/)다.

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

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic deep02.cpp -o ex (cc exit=1) =====
deep02.cpp: In function ‘int main()’:
deep02.cpp:23:20: error: no matching function for call to ‘validate(Point [2])’
   23 |     return validate(ps);
      |            ~~~~~~~~^~~~
deep02.cpp:18:24: note: candidate: ‘template<class T>  requires  Less<T> bool validate(const T (&)[2])’
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                        ^~~~~~~~
deep02.cpp:18:24: note:   template argument deduction/substitution failed:
deep02.cpp:18:24: note: constraints not satisfied
deep02.cpp: In substitution of ‘template<class T>  requires  Less<T> bool validate(const T (&)[2]) [with T = Point]’:
deep02.cpp:23:20:   required from here
deep02.cpp:10:9:   required for the satisfaction of ‘Less<T>’ [with T = Point]
deep02.cpp:10:16:   in requirements with ‘const T& a’, ‘const T& b’ [with T = Point]
deep02.cpp:10:53: note: the required expression ‘(a < b)’ is invalid
   10 | concept Less = requires(const T& a, const T& b) { a < b; };
      |                                                   ~~^~~
cc1plus: note: set ‘-fconcepts-diagnostics-depth=’ to at least 2 for more detail
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic deep02.cpp -o ex (cc exit=1) =====
deep02.cpp:23:12: error: no matching function for call to 'validate'
   23 |     return validate(ps);
      |            ^~~~~~~~
deep02.cpp:18:24: note: candidate template ignored: constraints not satisfied [with T = Point]
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                        ^
deep02.cpp:18:11: note: because 'Point' does not satisfy 'Less'
   18 | template <Less T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |           ^
deep02.cpp:10:53: note: because 'a < b' would be invalid: invalid operands to binary expression ('const Point' and 'const Point')
   10 | concept Less = requires(const T& a, const T& b) { a < b; };
      |                                                     ^
1 error generated.
```

- ★★★ **첫 에러가 23행(`return validate(ps);`) — 호출 줄이다** · 두 컴파일러 같다. (5)의 `deep01` 은 **6행(템플릿 몸통)** 이었다. **안쪽 세 겹(`check_pair`·`ordered`·`less_than`)은 인스턴스화조차 안 됐다** — 진단에 그 이름이 **한 번도 안 나온다.**
- ★★ **이유를 컨셉의 줄로 말한다** — g++ `the required expression ‘(a < b)’ is invalid`(10행) · clang `because 'a < b' would be invalid`(10행).

★★ **직접 쓴 `Less` 대신 표준 `std::totally_ordered` 를 걸면** —

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -DSTD_CONCEPT deep02.cpp -o ex (cc exit=1) =====
deep02.cpp: In function ‘int main()’:
deep02.cpp:23:20: error: no matching function for call to ‘validate(Point [2])’
   23 |     return validate(ps);
      |            ~~~~~~~~^~~~
deep02.cpp:16:40: note: candidate: ‘template<class T>  requires  totally_ordered<T> bool validate(const T (&)[2])’
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                        ^~~~~~~~
deep02.cpp:16:40: note:   template argument deduction/substitution failed:
deep02.cpp:16:40: note: constraints not satisfied
In file included from deep02.cpp:3:
/usr/include/c++/13/concepts: In substitution of ‘template<class T>  requires  totally_ordered<T> bool validate(const T (&)[2]) [with T = Point]’:
deep02.cpp:23:20:   required from here
/usr/include/c++/13/concepts:294:15:   required for the satisfaction of ‘__weakly_eq_cmp_with<_Tp, _Tp>’ [with _Tp = Point]
/usr/include/c++/13/concepts:304:13:   required for the satisfaction of ‘equality_comparable<_Tp>’ [with _Tp = Point]
/usr/include/c++/13/concepts:333:13:   required for the satisfaction of ‘totally_ordered<T>’ [with T = Point]
/usr/include/c++/13/concepts:295:4:   in requirements with ‘std::remove_reference_t<_Tp>& __t’, ‘std::remove_reference_t<_Up>& __u’ [with _Tp = Point; _Up = Point]
/usr/include/c++/13/concepts:296:17: note: the required expression ‘(__t == __u)’ is invalid
  296 |           { __t == __u } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:297:17: note: the required expression ‘(__t != __u)’ is invalid
  297 |           { __t != __u } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:298:17: note: the required expression ‘(__u == __t)’ is invalid
  298 |           { __u == __t } -> __boolean_testable;
      |             ~~~~^~~~~~
/usr/include/c++/13/concepts:299:17: note: the required expression ‘(__u != __t)’ is invalid
  299 |           { __u != __t } -> __boolean_testable;
      |             ~~~~^~~~~~
cc1plus: note: set ‘-fconcepts-diagnostics-depth=’ to at least 2 for more detail
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -DSTD_CONCEPT deep02.cpp -o ex (cc exit=1) =====
deep02.cpp:23:12: error: no matching function for call to 'validate'
   23 |     return validate(ps);
      |            ^~~~~~~~
deep02.cpp:16:40: note: candidate template ignored: constraints not satisfied [with T = Point]
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |                                        ^
deep02.cpp:16:11: note: because 'Point' does not satisfy 'totally_ordered'
   16 | template <std::totally_ordered T> bool validate(const T (&arr)[2]) { return check_pair(arr); }
      |           ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:334:9: note: because 'Point' does not satisfy 'equality_comparable'
  334 |       = equality_comparable<_Tp>
      |         ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:304:35: note: because '__detail::__weakly_eq_cmp_with<Point, Point>' evaluated to false
  304 |     concept equality_comparable = __detail::__weakly_eq_cmp_with<_Tp, _Tp>;
      |                                   ^
/usr/bin/../lib/gcc/x86_64-linux-gnu/13/../../../../include/c++/13/concepts:296:10: note: because '__t == __u' would be invalid: invalid operands to binary expression ('const remove_reference_t<Point>' (aka 'const Point') and 'const remove_reference_t<Point>' (aka 'const Point'))
  296 |           { __t == __u } -> __boolean_testable;
      |                 ^
1 error generated.
```

- ★★★ **여전히 첫 에러는 23행** — 그런데 **이유가 `<` 가 아니라 `==` 다**(g++ `the required expression ‘(__t == __u)’ is invalid` · clang `does not satisfy 'equality_comparable'`). **`totally_ordered` 는 `==` 도 요구**하고 컴파일러는 **처음 막힌 요구**를 적는다. ★ **컨셉이 원인을 「바꿔 말하는」 자리**다 — `<` 만 넣어 줘도 이 에러는 안 사라진다.
- ★★ **줄 수는 늘었다** — g++ 17 → 29 · clang 13 → 19. 표준 헤더 `<concepts>` 의 요구 사슬이 붙기 때문이다.

### (8) ★★★ 세기 격자 — 경우 8 × 컴파일러 2

**언제 쓰나** — 「컨셉을 쓰면 오류가 짧아진다」 같은 말을 **숫자로** 확인하고 싶을 때. ★★ **줄 수는 이 판의 관찰이다** — 규칙이 아니다.

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

```text
===== bash err-count.sh (exit=0) =====
경우	컴파일러	cc exit	총 줄	: error: 줄	첫 error 가 가리키는 곳	그곳이 호출 줄인가	호출 줄이 처음 나오는 줄
deep01.cpp	g++	1	8	1	deep01.cpp:6	X	5
deep01.cpp	clang++	1	16	1	deep01.cpp:6	X	13
deep02.cpp	g++	1	17	1	deep02.cpp:23	O	2
deep02.cpp	clang++	1	13	1	deep02.cpp:23	O	1
deep02.cpp -DSTD_CONCEPT	g++	1	29	1	deep02.cpp:23	O	2
deep02.cpp -DSTD_CONCEPT	clang++	1	19	1	deep02.cpp:23	O	1
deep03.cpp	g++	1	78	3	predefined_ops.h:45	X	9
deep03.cpp	clang++	1	220	9	predefined_ops.h:45	X	28
deep03.cpp -DRANGES	g++	1	34	1	deep03.cpp:12	O	2
deep03.cpp -DRANGES	clang++	1	36	1	deep03.cpp:12	O	1
deep01.cpp -ftemplate-backtrace-limit=1	g++	1	7	1	deep01.cpp:6	X	4
deep01.cpp -ftemplate-backtrace-limit=1	clang++	1	10	1	deep01.cpp:6	X	-
deep03.cpp -ftemplate-backtrace-limit=1	g++	1	67	3	predefined_ops.h:45	X	7
deep03.cpp -ftemplate-backtrace-limit=1	clang++	1	133	9	predefined_ops.h:45	X	-
deep02.cpp -DSTD_CONCEPT -fconcepts-diagnostics-depth=2	g++	1	32	5	deep02.cpp:23	O	2
deep02.cpp -DSTD_CONCEPT -fconcepts-diagnostics-depth=2	clang++	1	1	1	(clang++ 자체)	X	-
첫 error 가 호출 줄을 가리킨 칸 7 / 16 · 호출 줄이 아예 안 나온 칸 3 / 16
```

- ★★★ **첫 에러가 호출 줄을 가리킨 칸 7 / 16** — **`deep02` 네 칸 · `ranges::sort` 두 칸 · g++ 의 `-fconcepts-diagnostics-depth=2` 한 칸.** 제약 없는 템플릿(`deep01` · `std::sort`)은 **한 칸도** 호출 줄을 가리키지 않았다.
- ★★★ **「컨셉이면 짧다」는 반만 맞다** — 호출 줄로 오는 것은 **16칸 중 컨셉이 걸린 칸 전부**지만, **줄 수는 `deep01` g++ 8 → `deep02` g++ 17**(직접 쓴 컨셉) · **29**(`totally_ordered`)로 **늘었다.** 짧아진 것은 **표준 라이브러리** 쪽(78 → 34 · 220 → 36)이다. **바뀌는 것은 길이가 아니라 자리**다.
- ★★★ **`-ftemplate-backtrace-limit=1` 은 두 컴파일러가 다르게 자른다** — g++ 는 **첫 문맥과 마지막 문맥**을 남기고 가운데를 `[ skipping 2 instantiation contexts … ]` 로 접어 **호출 줄(13행)이 살아남는다**(4번째 줄). clang 은 **앞쪽 하나만** 남기고 `(skipping 3 contexts …)` — **호출 줄이 아예 사라졌다**(`-`). 아래 두 블록.
- ★★ **`-fconcepts-diagnostics-depth=2` 는 g++ 만의 옵션**이다 — g++ 는 `: error:` 가 1 → 5 줄로 **더 자세해지고**, clang 은 **`unknown argument`** 로 컴파일 자체를 거절한다(1줄 — 아래 블록).
- ★ **호출 줄이 아예 안 나온 칸 3 / 16** — clang 의 백트레이스 제한 두 칸 · clang 의 모르는 옵션 한 칸.

```text
===== g++ -std=c++20 -Wall -Wextra -pedantic -ftemplate-backtrace-limit=1 deep01.cpp -o ex (cc exit=1) =====
deep01.cpp: In instantiation of ‘bool less_than(const T&, const T&) [with T = Point]’:
deep01.cpp:7:75:   [ skipping 2 instantiation contexts, use -ftemplate-backtrace-limit=0 to disable ]
deep01.cpp:9:72:   required from ‘bool validate(const T (&)[2]) [with T = Point]’
deep01.cpp:13:20:   required from here
deep01.cpp:6:70: error: no match for ‘operator<’ (operand types are ‘const Point’ and ‘const Point’)
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~~^~~
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -ftemplate-backtrace-limit=1 deep01.cpp -o ex (cc exit=1) =====
deep01.cpp:6:70: error: invalid operands to binary expression ('const Point' and 'const Point')
    6 | template <class T> bool less_than(const T& a, const T& b) { return a < b; }
      |                                                                    ~ ^ ~
deep01.cpp:7:66: note: in instantiation of function template specialization 'less_than<Point>' requested here
    7 | template <class T> bool ordered(const T& a, const T& b) { return less_than(a, b); }
      |                                                                  ^
deep01.cpp:8:64: note: (skipping 3 contexts in backtrace; use -ftemplate-backtrace-limit=0 to see all)
    8 | template <class T> bool check_pair(const T (&arr)[2]) { return ordered(arr[0], arr[1]); }
      |                                                                ^
1 error generated.
```

```text
===== clang++ -std=c++20 -Wall -Wextra -pedantic -fconcepts-diagnostics-depth=2 deep02.cpp -o ex (cc exit=1) =====
clang++: error: unknown argument: '-fconcepts-diagnostics-depth=2'
```

```text
   원인 줄 찾기 — 이 판에서 통한 순서
   1. 첫 「error:」 줄의 파일을 본다     내 파일이면 거기부터 · /usr/include 면 2 로
   2. 사용자 파일 이름으로 grep 한다      g++  「required from here」   ← 에러 위 사슬의 끝
                                         clang 「requested here」 중 내 파일 줄 ← 에러 아래 사슬의 끝
   3. 백트레이스를 줄이려면              g++ 은 -ftemplate-backtrace-limit=1 이 호출 줄을 남긴다
                                         ★ clang 은 같은 옵션이 호출 줄을 지운다
```

## 문법 — 형태와 규칙

### 형태

```text
   template <class T> struct Box { T get() const { … } };   헤더에 정의 — 쓰는 곳마다 인스턴스(W)
   template struct Box<int>;                                명시적 인스턴스화 정의 — 멤버 전부
   template int Box<int>::get() const;                      명시적 인스턴스화 — 멤버 하나
   extern template struct Box<int>;                         명시적 인스턴스화 선언 — 여기서는 만들지 않는다 (C++11)
   template <Less T> bool validate(…);                      컨셉 제약 — 에러가 호출 줄로 (C++20)
```

★ 이 그림은 **형태 요약**이다 — 각 줄의 실제 동작은 (2)\~(4)(7)이 **실행한 소스**로 보였다.

### 규칙

- ★★★ **템플릿 정의는 쓰는 번역 단위에서 보여야 한다** — 안 보이면 `U` 만 남고 `undefined reference`((1)).
- ★★★ **헤더 정의의 인스턴스는 `.o` 마다 `W` 로 생기고 링커가 하나만 남긴다**((3)).
- ★★★ **클래스의 명시적 인스턴스화는 멤버를 전부 만든다** — 안 되는 멤버가 있으면 멤버 단위로((2)).
- ★★ **`extern template` 은 인스턴스를 막고, 인라인은 막지 않는다** — 짝이 되는 명시적 인스턴스화가 **한 곳**에 있어야 한다((4)).
- ★★★ **사용자 줄은 사슬의 끝이다** — g++ `required from here`, clang 의 마지막 `requested here`((5)).
- ★★★ **컨셉은 에러를 호출 줄로 옮긴다 — 길이를 줄이는 것은 아니다**((7)(8)).

### 금지 사례 — 표로 적는다

| 쓴 꼴 | g++ / ld 진단 | clang / ld 진단 | 어디서 |
|---|---|---|---|
| 정의를 `.cpp` 에만 두고 다른 `.cpp` 에서 `Box<int>` | `undefined reference to 'Box<int>::get() const'` | 같음(같은 ld) | (1) |
| 안 되는 멤버가 있는 클래스를 `template struct Box<int>;` | `request for member … non-class type` | `member reference base type 'const int'` | (2) |
| `extern template` 만 쓰고 명시적 인스턴스화 없음 | `undefined reference` | 같음 | (4) |
| clang 에 `-fconcepts-diagnostics-depth=2` | — | `unknown argument` | (8) |

## 어디서 틀리나

### 1. ★★★ 「템플릿도 선언은 헤더, 정의는 `.cpp` 에 두면 된다」

(1)이 반증이다 — **`undefined reference`** · 정의 쪽 `.o` 는 **기호 0개**.

### 2. ★★★ 「헤더에 함수를 정의하면 두 `.cpp` 가 포함할 때 다중 정의다」

(3)이 반증이다 — **템플릿 인스턴스는 `W`** 로 합쳐진다. 다중 정의가 나는 것은 25편 (1)의 **`B`**(비인라인 정의)다.

### 3. ★★★ 「명시적 인스턴스화는 쓰는 멤버만 만든다」

(2)가 반증이다 — **`template struct Box<int>;` 는 안 쓰는 `odd()` 까지 만들어 에러.**

### 4. ★★ 「`extern template` 을 쓰면 그 번역 단위에는 그 함수의 코드가 없다」

(4)가 반증이다 — **`-O2` 에서는 인라인되어 펼쳐진다**(`U` 가 사라졌다).

### 5. ★★★ 「첫 `error:` 줄이 내 실수의 자리다」

(5)(6)이 반증이다 — **첫 에러는 템플릿 몸통(6행)이나 표준 헤더(`predefined_ops.h:45`)** 다. **내 줄은 사슬 끝**에 있다.

### 6. ★★★ 「컨셉을 걸면 오류가 짧아진다」

(8)이 반증이다 — **직접 만든 템플릿에서는 g++ 8 → 17 → 29 로 늘었다.** 바뀐 것은 **자리**(호출 줄)다. 짧아진 것은 표준 라이브러리 쪽뿐이다(이 판의 관찰).

### 7. ★★ 「`-ftemplate-backtrace-limit` 은 두 컴파일러에서 같은 것을 자른다」

(8)이 반증이다 — **g++ 는 호출 줄을 남기고 clang 은 지운다.**

## 구현 세부사항 대 언어 보장

C++ 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★★ **이 주제는 표준과 「컴파일러의 것」이 반씩이다** — 링크가 되나·어느 인스턴스가 생기나는 **표준(ODR)** 이고, **진단의 모양·순서·줄 수·옵션**은 **전부 컴파일러의 것**이다. 오류 읽기 절반은 **표준이 아무것도 약속하지 않는 자리**다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | ★★★ **정의가 안 보이면 인스턴스화 불가**((1)) · **여러 번역 단위의 같은 인스턴스는 허용**((3)) · **명시적 인스턴스화는 멤버 전부**((2)) · **`extern template` 은 다른 곳의 정의를 쓴다**((4)) · **컨셉 불만족은 후보 탈락 — 호출 자리에서 에러**((7)) | 링크 결과 · cppreference | ★★ **`undefined reference` 는 컴파일러가 못 본다** — 링커까지 가야 난다 |
| **조건부 표준** | 특정 판에서만 | ★★ **`extern template` 은 C++11부터 · 컨셉은 C++20부터** | ★ 판을 바꿔 던지지 않았다 | — |
| **구현 정의 · ABI** | 문서화 의무 | ★★★ **`nm` 의 `W`**(인스턴스·명시적 인스턴스화 모두) · **`-O2` 의 인라인**((4)) · **`__stack_chk_fail`**(배포판 기본 플래그) | `nm -C` · 두 최적화 판 | ★ **다른 ABI·링커(예: COMDAT 그룹)에서는 글자가 다를 수 있다** — 던지지 않았다 |
| **컴파일러의 것** | 표준 밖 | ★★★ **진단 모양 · `required from` 대 `requested here` · 에러 순서 · 줄 수 · `-ftemplate-backtrace-limit` 의 자르는 법 · `-fconcepts-diagnostics-depth`(g++ 전용)**((5)\~(8)) | 두 컴파일러 · 세기 격자 | ★★★ **줄 수는 이 판 값** — 판이 바뀌면 바뀐다(규칙 24) |
| **UB** | 아무 일이나 | ★ **이 편의 코드는 UB 가 없다** — ★ 단 **ODR 위반**(번역 단위마다 다른 정의)은 진단 없이 UB 가 될 수 있다 — 이 편은 **던지지 않았다**(목록의 **55번 주제**) | — | ★★ **두 `W` 의 정의가 서로 다를 때 링커가 무엇을 하나는 던지지 않았다** — 같은 정의일 때 조용히 합친 것만 봤다((3)) |

### 「도구가 못 보는 것」을 층마다

| 사실 | 층 | 컴파일러 | 링커 | 기호표 |
|---|---|---|---|---|
| ★★★ **정의를 `.cpp` 에만 둔 템플릿** | ill-formed 아님 — 링크 실패 | ★★★ **두 번 다 경고 0 · exit 0** | ★★★ **`undefined reference`** | `U` · 기호 0개 |
| ★★ **`extern template` + 명시적 인스턴스화 없음** | 링크 실패 | **경고 0** | **`undefined reference`** | `U` |
| ★★ **두 `.o` 의 같은 인스턴스** | 허용 | **경고 0** | **조용히 합친다** | `W` · `W` |

- ★★ **이 표의 결론** — **헤더 배치의 사고는 컴파일러가 아니라 링커가 말한다.** 그래서 이 편의 블록은 전부 **`-c` 두 번 + 링크**다.

### ★ 종료 코드 0인데 ill-formed — 이 편에서는 못 찾았다

- ★ 링크가 실패한 판은 전부 **`cc exit=1`** 이었다. (1)의 **각 번역 단위의 컴파일**은 `exit 0` 이지만 그것은 **ill-formed 가 아니다** — 번역 단위 하나만 보면 옳은 코드다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 고르는 것 | 왜 |
|---|---|---|
| 일반 템플릿 · 쓰일 `T` 를 모른다 | ★★★ **헤더에 정의** | (3) — 링커가 `W` 를 합친다 |
| 쓰일 `T` 가 몇 개로 정해져 있고 정의를 감추고 싶다 | ★★ **`.cpp` 정의 + 명시적 인스턴스화** | (2) — 목록 밖 `T` 는 `undefined reference` |
| 헤더 정의 + 인스턴스를 한 곳에서만 | ★★ **`extern template` + 한 `.cpp` 의 명시적 인스턴스화** | (4) — 크기·시간 이득은 **이 문서가 재지 않았다** |
| 안 되는 멤버가 있는 클래스를 미리 만든다 | ★★ **멤버 단위 명시적 인스턴스화** | (2) |
| 템플릿 오류에서 내 줄을 찾는다 | ★★★ **파일 이름으로 grep** — g++ `required from here` · clang 마지막 `requested here` | (5)(8) |
| 내 템플릿의 오류를 쓰는 사람 자리로 | ★★★ **컨셉 제약**([목록의 **36번 주제**](../36-concepts-and-requires/)) | (7) — 자리가 호출 줄로 |
| 백트레이스를 줄인다 | ★ **g++ 는 `-ftemplate-backtrace-limit=1`** · clang 은 **호출 줄이 사라지니 주의** | (8) |

## 핵심 문장

- ★★★ **정의를 `.cpp` 에만 두면 정의 쪽 `.o` 는 기호 0개, 쓰는 쪽은 `U` — `undefined reference`.**
- ★★★ **헤더 정의는 두 `.o` 에 `W` 로 생기고 링커가 하나로 합친다** — 25편의 `B`(다중 정의)와 대비된다.
- ★★★ **`template struct Box<int>;` 는 멤버를 전부 만든다** — 안 쓰는 `odd()` 에서도 에러.
- ★★ **`extern template` 판은 `-O0` 에서 `U`, `-O2` 에서 `U` 가 사라진다** — 인스턴스는 막아도 인라인은 안 막는다.
- ★★★ **내 줄은 사슬의 끝** — g++ 는 에러 위 `required from here`, clang 은 에러 아래 마지막 `requested here`.
- ★★★ **컨셉은 에러의 길이가 아니라 자리를 바꾼다** — 첫 에러가 호출 줄인 칸 7 / 16, 컨셉 판 g++ 줄 수는 오히려 8 → 17 → 29.

## 관련 자료

- [31번](../31-function-templates-and-argument-deduction/) (5) — ★★ 인스턴스를 **`nm -C` 로 세고 `W` 를 본** 첫 편. 여기는 그 `W` 가 **링크에서 무엇을 하나**까지다.
- [32번](../32-class-templates-and-ctad/) (6) — ★★★ **멤버는 쓰일 때만** — (1)의 「기호 0개」와 (2)의 「명시적 인스턴스화는 전부」의 전제.
- [25번](../25-static-members-and-inline-variables/) (1) — ★★★ **`B` 대 `u`/`V`** — 헤더에 둔 정의가 두 번역 단위에서 무엇이 되나의 **변수 쪽** 답. 여기는 **함수 템플릿 쪽**(`W`).
- [33번](../33-template-specialization-and-partial-specialization/) — 특수화도 쓰는 번역 단위에서 보여야 한다.
- C 갈래 44번(헤더와 분할 컴파일 — 폴더가 아직 없다) — 「선언은 헤더, 정의는 `.c`」 — **템플릿에서 깨지는 규칙**의 원래 모양.
- Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (1)(3) — ★★ **Rust 는 경계가 빠지면 정의 자리·호출 자리에서 막는다** — C++ 은 컨셉을 걸어야 (7)처럼 호출 자리로 온다. (8)은 **단형화를 센다.**
- [`compiler-pipeline/`](../../../../compiler-pipeline/) — 컴파일·링크 단계 일반.
- [목록의 **36번 주제**](../36-concepts-and-requires/)(컨셉) · 목록의 **55번 주제**(모듈·ODR).

## 용어 풀이

> **번역 단위(translation unit)** — 전처리가 끝난 `.cpp` 하나. 컴파일러는 한 번에 하나만 본다.\
> 예: (1)의 `box_def.cpp` 와 `use_box.cpp`.

> **명시적 인스턴스화 정의(explicit instantiation definition)** — `template struct Box<int>;` 처럼 **이 자리에서 만들라**는 선언. 클래스면 멤버 전부.\
> 예: (2).

> **명시적 인스턴스화 선언(explicit instantiation declaration)** — `extern template struct Box<int>;`. **여기서는 만들지 말고 다른 곳의 것을 쓰라.**\
> 예: (4).

> **약한 기호(weak symbol) `W`** — 여러 오브젝트에 있어도 링커가 **하나만 남기는** 기호. 이 판에서 템플릿 인스턴스가 이것으로 나왔다.\
> 예: (3)의 `W HBox<int>::get() const` 두 벌.

> **미정의 기호 `U`** — 이 오브젝트가 **쓰기만 하고 갖고 있지 않은** 기호. 링크 때 다른 오브젝트에서 찾는다.\
> 예: (1)의 `U Box<int>::get() const`.

> **인스턴스화 사슬(instantiation backtrace)** — 에러가 난 인스턴스를 **누가 요구했나**를 거슬러 올라간 목록. g++ `required from`, clang `requested here`.\
> 예: (5).

> **컨셉(concept)** — C++20. 템플릿 인자가 만족해야 할 요구를 이름 붙인 것. 만족하지 않으면 그 템플릿은 **후보에서 빠진다.**\
> 예: (7)의 `Less`.

## 더 들어가면

- **C++20 모듈** — 템플릿 정의를 헤더 대신 모듈 인터페이스에 둔다. 목록의 **55번 주제** — 이 머신의 지원 상태부터 거기서 본다.
- **ODR 위반 — 두 번역 단위가 같은 템플릿을 다르게 정의하면** — (3)의 링커가 같은 정의 둘을 **조용히** 합친 것까지만 봤다. 다른 정의 둘은 이 문서가 던지지 않았다(목록의 **55번 주제**).
- **`-fno-implicit-templates`(g++)** — 암묵 인스턴스화를 통째로 끄는 옛 옵션. 이 문서는 던지지 않았다.
- **코드 크기** — 「템플릿이 코드를 부풀린다」는 이 문서가 **재지 않았다.** 재려면 `size`·`nm -S` 로 바이트를 견줘야 한다 — Rust 갈래 [31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/) (8)이 단형화 쪽에서 `nm -S` 로 벌 수와 바이트를 쟀다.
