# cpp/syntax/34 — 가변 인자 템플릿과 팩 확장 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **g++ (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** ·\
> **Ubuntu clang version 18.1.3 (1ubuntu1)** · libstdc++ 13 · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> 소스는 질문 파일과 같다(출력 블록의 배너에 파일 이름이 있다). 블록은 캡처 스크립트가 받은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — 흔들리는 칸은 **진단 문구와 위치(`<command-line>`) · 4번의 `g` 순서(미명시)** 다.\
> 근거로 쓰는 것은 다음이다 — **격자 칸 · 「갈린 칸 N / M」 · copy/move 로그 · `f got N args` · 타입 이름**.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★ **2 · 1 · 0** · **`sum_fold()` 는 컴파일되고 0**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack02.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  sum_rec: first=1, sizeof...(rest)=2
  sum_rec: first=2, sizeof...(rest)=1
  sum_rec: first=3, sizeof...(rest)=0
sum_rec(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=3
sum_fold(1, 2, 3) = 6
  sum_fold: sizeof...(Ts)=0
sum_fold() = 0
```

**왜 그런가**

- ★★ 재귀는 **첫 원소를 떼고 나머지 팩을 넘긴다** — 나머지가 0 이 되면 비템플릿 `sum_rec()` 가 받는다.
- ★★ `sum_fold` 는 **이항 폴드 `(0 + ... + xs)`** 라 빈 팩에서 **`0`(I)** 을 낸다.

### 2. ★★★ **`-` : 5 · 9 · -15 · 9** · **빈 팩 `error` 는 `+`·`-` 의 단항 네 칸**, `,` → `void` · `&&` → `1` · `||` → `0` · **`,` 이항 : 2 · 0** · **0 / 40 · 3 / 10 · 4 / 40**

**출력**

```text
===== bash fold-grid.sh (exit=0) =====
연산자	꼴	g++ 빈 팩	g++ 10,3,2	clang++ 빈 팩	clang++ 10,3,2
+	단항 좌 (... + xs)	error	15	error	15
+	단항 우 (xs + ...)	error	15	error	15
+	이항 좌 (I + ... + xs)	0	15	0	15
+	이항 우 (xs + ... + I)	0	15	0	15
-	단항 좌 (... - xs)	error	5	error	5
-	단항 우 (xs - ...)	error	9	error	9
-	이항 좌 (I - ... - xs)	0	-15	0	-15
-	이항 우 (xs - ... - I)	0	9	0	9
,	단항 좌 (... , xs)	void	2	void	2
,	단항 우 (xs , ...)	void	2	void	2
,	이항 좌 (I , ... , xs)	0	2	0	2
,	이항 우 (xs , ... , I)	0	0	0	0
&&	단항 좌 (... && xs)	1	1	1	1
&&	단항 우 (xs && ...)	1	1	1	1
&&	이항 좌 (I && ... && xs)	1	1	1	1
&&	이항 우 (xs && ... && I)	1	1	1	1
||	단항 좌 (... || xs)	0	1	0	1
||	단항 우 (xs || ...)	0	1	0	1
||	이항 좌 (I || ... || xs)	0	1	0	1
||	이항 우 (xs || ... || I)	0	1	0	1
g++ 대 clang++ 가 갈린 칸 0 / 40 · 좌 대 우가 갈린 짝(10,3,2) 3 / 10 · error 칸(g++) 4 / 40
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic '-DFOLD=(... + xs)' -DINIT=0 -DPACK= pack01.cpp -o ex (cc exit=1) =====
pack01.cpp: In instantiation of ‘auto cell(Ts ...) [with Ts = {}]’:
pack01.cpp:21:25:   required from here
<command-line>: error: fold of empty expansion over operator+
pack01.cpp:8:12: note: in expansion of macro ‘FOLD’
    8 |     return FOLD;
      |            ^~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic '-DFOLD=(... + xs)' -DINIT=0 -DPACK= pack01.cpp -o ex (cc exit=1) =====
pack01.cpp:8:12: error: unary fold expression has empty expansion for operator '+' with no fallback value
    8 |     return FOLD;
      |            ^
<command line>:1:15: note: expanded from macro 'FOLD'
    1 | #define FOLD (... + xs)
      |               ^
pack01.cpp:21:21: note: in instantiation of function template specialization 'cell<>' requested here
   21 |     run([] { return cell(PACK); });
      |                     ^
1 error generated.
```

**왜 그런가**

- ★★★ **점 셋이 왼쪽이면 왼쪽부터** — `((10-3)-2)=5` · `(10-(3-2))=9` · `(((0-10)-3)-2)=-15` · `(10-(3-(2-0)))=9`.
- ★★ **쉼표는 오른쪽 끝 값** — 이항 좌 `((0,10),3),2` 는 2, 이항 우 `10,(3,(2,0))` 은 0.
- ★★★ **빈 팩 단항은 `&&`·`||`·`,` 만 값이 정해져 있다** — 두 컴파일러가 같은 네 칸에서 멈췄다.

### 3. ★★★ **`[2]` move(3) · move(4) · `Duo(&&, &&)`** · **`[5]` copy(3) · copy(4) · `Duo(const&, const&)`** · `[3]` copy(1) · move(5) · `Duo(const&, &&)` · `[6]` copy(1) · copy(5) · `Duo(const&, const&)`

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] make_fwd<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[2] make_fwd<Duo>(Noisy(3), Noisy(4))
    move(3)
    move(4)
    Duo(&&, &&)
[3] make_fwd<Duo>(n1, Noisy(5))
    copy(1)
    move(5)
    Duo(const&, &&)
[4] make_plain<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[5] make_plain<Duo>(Noisy(3), Noisy(4))
    copy(3)
    copy(4)
    Duo(const&, const&)
[6] make_plain<Duo>(n1, Noisy(5))
    copy(1)
    copy(5)
    Duo(const&, const&)
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack03.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] make_fwd<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[2] make_fwd<Duo>(Noisy(3), Noisy(4))
    move(3)
    move(4)
    Duo(&&, &&)
[3] make_fwd<Duo>(n1, Noisy(5))
    copy(1)
    move(5)
    Duo(const&, &&)
[4] make_plain<Duo>(n1, n2)
    copy(1)
    copy(2)
    Duo(const&, const&)
[5] make_plain<Duo>(Noisy(3), Noisy(4))
    copy(3)
    copy(4)
    Duo(const&, const&)
[6] make_plain<Duo>(n1, Noisy(5))
    copy(1)
    copy(5)
    Duo(const&, const&)
```

**왜 그런가**

- ★★★ **`std::forward<Args>(args)...` 는 원소마다 자기 `Args` 로 되돌린다** — 임시는 `Args = Noisy` 라 rvalue, `n1` 은 `Args = Noisy&` 라 lvalue.
- ★★ `make_plain` 은 `args...` 를 **이름 그대로** 넘겨 전부 lvalue — 7번.

### 4. ★★ **`[1]` 3개 · `10 20 30` · `[2]` 1개 · `6`** · ★★★ **g++ `g(3) g(2) g(1)` · clang `g(1) g(2) g(3)`** — 다르다

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(3)
  g(2)
  g(1)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(1)
  g(2)
  g(3)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

**왜 그런가**

- ★★ **`g(args)...` 는 `g(1), g(2), g(3)`, `g(args...)` 는 `g(1, 2, 3)`** — `...` 은 앞의 패턴 전체를 복제한다.
- ★★★ **함수 인자의 계산 순서는 미명시** — 자리(`10 20 30`)는 같고 **계산 순서만** 갈렸다. 8번.
- ★ **`-O2` 로도 같은 갈림**이었다 —

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -O2 pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(3)
  g(2)
  g(1)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
===== clang++ -std=c++17 -Wall -Wextra -pedantic -O2 pack04.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
[1] f(g(args)...) with 1, 2, 3
  g(1)
  g(2)
  g(3)
  f got 3 args: 10 20 30
[2] f(g(args...)) with 1, 2, 3
  g(pack of 3)
  f got 1 args: 6
```

### 5. ★★ **`char` 1 · `short` 2 · `float` 4 · `bool` 1**

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic pack05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  char   sizeof=1
  short  sizeof=2
  float  sizeof=4
  bool   sizeof=1
===== clang++ -std=c++17 -Wall -Wextra -pedantic pack05.cpp -o ex && ./ex (cc exit=0 · run exit=0) =====
  char   sizeof=1
  short  sizeof=2
  float  sizeof=4
  bool   sizeof=1
```

**왜 그런가**

- ★★ `Ts` 가 원소마다 **넘긴 타입 그대로** 추론된다 — 승격이 없다.

### 6. ★★★ **`&&` 는 빈 팩의 값(`true`)을 표준이 정했고 `+` 는 정하지 않았다** — 처방은 **이항 폴드 `(0 + ... + xs)`** 로 빈 팩의 값을 직접 주는 것

- ★ clang 문구가 그대로 말한다 — `with no fallback value`. 그 fallback 이 이항 폴드의 `I` 다.

### 7. ★★★ **받는 쪽 이름 `args` 는 lvalue 이기 때문** — `Args&&` 가 rvalue 를 **받는 것**과, 받은 것을 다음 함수에 **rvalue 로 넘기는 것**은 별개다. 넘기려면 `std::forward<Args>(args)...`

- ★ 09편 (6)의 「`x` 는 언제나 lvalue」가 팩의 원소마다 그대로 선다.

### 8. ★★ **미명시** — 두 컴파일러 다 맞다 · **쉼표 폴드**(`f` 안의 `((std::printf(" %d", xs)), ...)`)가 두 컴파일러 다 `10 20 30` 순서였다

- ★★ 함수 인자 목록의 쉼표는 **구분자**, 폴드의 쉼표는 **연산자**다 — 연산자 쪽만 왼쪽부터 끝낸다.

### 9. ★★ **결합 법칙이 성립하는 연산자라 묶는 방향이 값을 안 바꾼다** · 그래도 **아무렇게나는 안 된다** — `+` 는 빈 팩에서 **단항이면 에러**, 이항이면 `I`

- ★ `&&`·`||` 는 좌·우도, 빈 팩도 문제없었다 — 셋 중 **`+` 만 빈 팩에서 갈린다.**

### 10. 다른 주제와 잇기

- ★★ **C 는 `int`·`int`·`double`·`int` 로 승격하고 꺼내는 쪽이 타입을 짐작한다** — `va_arg(ap, float)` 는 UB(gcc 는 `exit=132`) — C 갈래 [36번](../../../c/syntax/36-variadic-functions-stdarg/) (1)(2). C++ 팩은 넘긴 그대로다.
- ★ **어느 쪽도 아니다** — Go 는 **한 타입의 슬라이스**라 타입은 남지만 원소마다 다를 수 없다(Go 갈래 [12번](../../../go/syntax/12-functions-multiple-returns-named-results-and-variadics/) (4)).

## 실행 검증

| 무엇을 | 몇 번 · 어느 판 | 결과 |
|---|---|---|
| `pack02.cpp` | 두 컴파일러 | ★★ **2 · 1 · 0 · 빈 팩 0** |
| `pack01.cpp` + `fold-grid.sh` | 40칸 × 컴파일러 2 | ★★★ **0 / 40 · 3 / 10 · 4 / 40** |
| `pack01.cpp` 빈 팩 `(... + xs)` | 두 컴파일러 | ★★ **에러 — `no fallback value`** |
| `pack03.cpp` | 두 컴파일러 | ★★★ **forward: move · 없으면 copy** — 로그가 한 글자도 같다 |
| `pack04.cpp` | 두 컴파일러 | ★★★ **`g` 순서가 갈린다(미명시)** · 결과는 같다 |
| `pack05.cpp` | 두 컴파일러 | ★★ **`char` · `short` · `float` · `bool`** |
| `pack04.cpp -O2` | 두 컴파일러 | ★★ **같은 갈림** |
| `pack02.cpp -std=c++14` | 두 컴파일러 × `-pedantic`/`-pedantic-errors` | ★★ **경고만 · exit 0 / 에러 · exit 1** |

**구현 의존 항목** — 다음은 **이 환경(g++ 13 · clang 18)에서만** 그렇다.

- ★★★ **4번의 `g` 순서**(미명시 — 이 판에서는 `-O0`·`-O2` 가 같았지만 판이 바뀌면 바뀔 수 있다) · **진단 문구**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- ★★★ **폴드 40칸** · **빈 팩 세 연산자** · **copy/move 의 종류와 수** · **확장 모양** · **원소 타입 보존.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — ★ **람다 팩 캡처** · **libc++**.
- ★ **「부적용인 창」** — ASan · 어셈블리 · 경고 격자.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번** — 미명시 칸이라 **판마다** 다시 봐야 한다.
