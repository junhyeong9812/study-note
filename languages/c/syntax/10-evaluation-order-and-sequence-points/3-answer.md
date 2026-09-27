# c/syntax/10 — 평가 순서와 시퀀스 포인트: 무엇이 먼저 **도나** — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과 **clang 18.1.3** ·
> x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본 플래그는 `-std=c17 -Wall -Wextra -pedantic`.\
> ★ **최적화 수준은 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 벌로 나눠 돌렸다** — UB 가 걸린 문항에서는 그 목록을 그대로 싣는다.
> ★★ **이 주제의 답은 「값」이 아니라 「누가 말해 주나」다.** 값이 같아도 안전하지 않다는 것이 본문이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 한 `printf` 안에서 두 번 꺼내면 — **컴파일러가 답을 바꾼다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
(경고 없음)
pop() 두 번을 한 printf 에 : 30 40
문을 나눠 부르면            : 40 30
===== clang -std=c17 -Wall -Wextra =====
(경고 없음)
pop() 두 번을 한 printf 에 : 40 30
문을 나눠 부르면            : 40 30
===== gcc UBSan(-fsanitize=undefined -fno-sanitize-recover=all) =====
pop() 두 번을 한 printf 에 : 30 40
문을 나눠 부르면            : 40 30
exit=0
===== clang UBSan =====
pop() 두 번을 한 printf 에 : 40 30
문을 나눠 부르면            : 40 30
exit=0
```

**왜 그런가**

```text
   스택 = [10, 20, 30, 40]   top = 4

   한 printf 안에서                  문을 나누면
   +--------------------------+     +--------------------------+
   | gcc   -> ★ 30 40         |     | gcc   -> 40 30           |
   | clang -> ★ 40 30         |     | clang -> 40 30           |
   +--------------------------+     +--------------------------+
     ★ 답이 다르다                     ★ 양쪽이 같다
```

- **gcc 는 오른쪽 인자를 먼저** 평가해 `40` 을 먼저 꺼내고, 그것이 **둘째 자리**로 간다 → `30 40`.
- **clang 은 왼쪽부터** 평가해 `40` 이 **첫 자리**로 간다 → `40 30`.
- **둘 다 적법하다.** 인자들의 평가 순서는 **미명시**이고, 그래서 **어느 쪽도 버그가 아니다 — 코드가 버그다.**
- **경고 0건 · UBSan 진단 0줄 · `exit=0`.** 다섯 최적화 수준에서도 각 컴파일러 안에서는 한 글자도 안 바뀌었다.
- 고치는 법은 **문을 나누는 것 하나**다. 나누면 양쪽이 `40 30` 으로 같아진다.

### 2. 세 함수를 한 호출의 인자로 넣으면 — 방향이 컴파일러마다 다르다 ★★

**출력**

```text
===== gcc 13.3.0 -O0 =====
take(f(), g(), h()):
  h 가 1 번째
  g 가 2 번째
  f 가 3 번째
  받은 값 = 1 2 3
f() + g() * h() =   f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  결과 7
===== clang 18.1.3 -O0 =====
take(f(), g(), h()):
  f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  받은 값 = 1 2 3
f() + g() * h() =   f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  결과 7
```

**받은 값 · 인자 개수 · 최적화 수준**

```text
=== gcc ===                         === clang ===
인자 2개 : BA                       인자 2개 : AB
인자 3개 : CBA                      인자 3개 : ABC
인자 7개 : GFEDCBA                  인자 7개 : ABCDEFG
중첩 outer(A(), inner(B(),C())) : CBA   중첩 outer(A(), inner(B(),C())) : ABC

gcc  -O0 -O1 -O2 -O3 -Os -> 전부 "h g f"
clang -O0 -O1 -O2 -O3 -Os -> 전부 "f g h"
```

**왜 그런가**

- **받은 값은 양쪽 다 `1 2 3`** 이다. **어느 인자가 어느 매개변수로 가는지는 표준이 정한다** —\
  정해지지 않은 것은 **「언제 계산되느냐」 하나뿐**이다.
- `f() + g() * h()` 는 **양쪽 다 `f`·`g`·`h`** 순이었다. [09번 형제](../09-operator-precedence-and-associativity/)의 우선순위로는 `g()*h()` 가 먼저 묶이는데도 그렇다 —\
  **묶이는 순서와 도는 순서는 무관하다.**
- 인자를 2·7개로 늘려도, 다섯 최적화 수준으로 바꿔도 **각 컴파일러 안에서는 한 글자도 안 흔들렸다.**\
  ★★ **그래서 더 위험하다.** 「다섯 번 돌려 봤는데 같다」는 **보장이 아니라 관찰**이고,\
  **컴파일러를 바꾸는 순간 뒤집힌다**는 것을 바로 옆 칸이 보여 준다.
- ★ **라벨을 정확히 읽어라** — 위 「중첩」은 `outer(A(), inner(B(),C()))` 꼴(바깥 호출의 **둘째 인자가 또 호출**)이다.\
  `A(B(),C())` 꼴(= `A` 자신이 바깥 호출)은 `A` 의 **몸통이 인자 뒤**에 오므로 같은 환경에서 **gcc `CBA` · clang `BCA`** 다.

### 3. 같은 객체를 한 식에서 두 번 건드리면 — 여덟 벌이 같은 값 ★★

**출력**

```text
=== gcc -O0 ===          === gcc -O1 ===          === gcc -O2 ===
=== gcc -O3 ===          === gcc -Os ===          === clang -O0 ===
=== clang -O2 ===        === gcc UBSan ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
(여덟 벌 전부 위 네 줄이 한 글자도 다르지 않다 · UBSan exit=0 · 진단 0줄)
```

**컴파일 타임 경고 — 이것만이 말해 줬다**

```text
===== 소스: ex.c =====
#include <stdio.h>
int main(void) {
    int i = 5;
    i = i++;
    printf("i = i++      -> i = %d\n", i);
    int j = 5;
    int k = j++ + j++;
    printf("j++ + j++    -> k = %d, j = %d\n", k, j);
    int a[8] = {0};
    int n = 2;
    a[n] = n++;
    printf("a[n] = n++   -> n = %d, a[2] = %d, a[3] = %d\n", n, a[2], a[3]);
    int m = 1;
    m = m++ + ++m;
    printf("m = m++ + ++m -> m = %d\n", m);
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:4:7: warning: operation on ‘i’ may be undefined [-Wsequence-point]
    4 |     i = i++;
      |     ~~^~~~~
ex.c:7:20: warning: operation on ‘j’ may be undefined [-Wsequence-point]
    7 |     int k = j++ + j++;
      |                   ~^~
ex.c:11:13: warning: operation on ‘n’ may be undefined [-Wsequence-point]
   11 |     a[n] = n++;
      |            ~^~
ex.c:14:7: warning: operation on ‘m’ may be undefined [-Wsequence-point]
   14 |     m = m++ + ++m;
      |     ~~^~~~~~~~~~~
ex.c:14:7: warning: operation on ‘m’ may be undefined [-Wsequence-point]
```

**왜 그런가**

- ★★ **이 값들을 「정답」이라고 부르면 안 된다.** UB 는 **다른 답이 있는 것**이 아니라 **답이 없는 것**이다.\
  오늘 `i = 5` 였다고 내일도 5 가 아니다.
- **`a[n] = n++` 이 `a[3]` 에 2 를 넣었다** — 왼쪽 `a[n]` 의 주소를 **증가한 뒤의 `n`** 으로 계산했다는 뜻이다.\
  이 판에서는 그랬다는 관찰일 뿐이고, 보장이 아니다.
- **여덟 벌이 전부 같은 값을 냈고 UBSan 도 침묵했다.** 위험을 말해 준 것은 **컴파일 타임 경고 하나**다.
- ★ **「값이 늘 같다」는 「안전하다」와 아무 관계가 없다.**

### 4. 시퀀스 포인트가 사이에 있을 때 — 단락 평가를 호출 수로 센다

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic =====
ex.c: In function ‘main’:
ex.c:17:7: warning: operation on ‘i’ may be undefined [-Wsequence-point]
   17 |     i = (i++, i++);
      |     ~~^~~~~~~~~~~~
--- 실행 ---
(1) p && p->val  -> 살아서 여기까지 왔다
(2) 0 && side()  -> side 호출 0 회
(2) 1 || side()  -> side 호출 0 회
(3) 0 ? side : side -> side 호출 1 회
(4) i = (i++, i++)  -> i = 6
(5) k++ && k++      -> r = 1, k = 7
exit=0
```

**왜 그런가**

```text
   시퀀스 포인트가 있는 자리

   1. 문 끝의  ;                       가장 흔한 자리
   2. &&  의 왼쪽과 오른쪽 사이          -> 단락 평가가 여기서 나온다
   3. ||  의 왼쪽과 오른쪽 사이
   4. ?:  의 조건과 선택된 가지 사이
   5. ,   (콤마 연산자) 의 왼쪽과 오른쪽 사이
   6. 함수 호출에서 ★ 인자 평가가 다 끝난 뒤, 몸통에 들어가기 전
   7. 완전식(full expression) 의 끝
```

- `p` 가 `NULL` 인데도 **죽지 않았다** — `&&` 의 왼쪽이 거짓이면 **오른쪽을 아예 평가하지 않는다.**\
  이것이 `if (p && p->val)` 이 C 에서 매일 쓰이는 이유다.
- `side` 호출 수가 **0·0·1** 이다. 「안 불렸다」를 **부작용 수로 세서** 보인 것이다 — 출력이 없다는 것을 출력으로 만들었다.
- `k++ && k++` 은 **UB 가 아니다.** 둘 사이에 시퀀스 포인트가 있어 경고가 안 난다.
- ★ **경고는 딱 한 건이고 `i = (i++, i++)` 줄이다.** 다음 문항이 그 이야기다.

### 5. 대입 대상만 바꾸면 — 경고가 사라진다 ★

**출력**

```text
[gcc   -std=c17 -Wall -Wextra -pedantic] 0 건  exit=0
[clang -std=c17 -Wall -Wextra -pedantic] 0 건  exit=0

t = (i++, i++)   -> t = 6, i = 7
u = j++ && j++   -> u = 1, j = 7
w = k++ ? k++ : k++ -> w = 6, k = 7
```

**왜 그런가**

```text
   i = (i++, i++)                     int t = (i++, i++)

   두 i++ 사이 -> 시퀀스 포인트 O       두 i++ 사이 -> 시퀀스 포인트 O
   바깥의 대입 i = ...                 바깥의 대입 대상이 t 다
     -> ★ i 에 순서 없는 부작용 둘        -> i 를 바꾸는 것은 안쪽 둘뿐
     -> ★ UB                            -> ★ UB 아님 (0 건)
```

- 같은 `i++` 두 개인데 **대입 대상만 바꿨을 뿐**이고, 경고가 1건에서 0건이 됐다.
- ★ **UB 인지 아닌지는 「부작용이 몇 개냐」가 아니라 「같은 객체에 순서 없는 부작용이 둘이냐」로 갈린다.**
- 「부작용 개수」로 세면 `u = j++ && j++`(둘) 도 `w = k++ ? k++ : k++`(셋) 도 위험해 보이는데 **둘 다 0건**이다.

### 6. 부작용을 한 `printf` 안에서 재면 — 측정이 틀린다 ★★

**출력**

```text
===== 소스: ex.c (틀린 측정 코드) =====
#include <stddef.h>
#include <stdio.h>
int main(void) {
    int arr[4] = {10, 20, 30, 40};
    int *p = arr;
    printf("*p++   = %d, p 는 이제 arr[%td]\n", *p++, (ptrdiff_t)(p - arr));
    p = arr;
    printf("(*p)++ = %d, arr[0] 은 이제 %d\n", (*p)++, arr[0]);
    arr[0] = 10;
    p = arr;
    printf("*++p   = %d, p 는 이제 arr[%td]\n", *++p, (ptrdiff_t)(p - arr));
    return 0;
}
```

```text
ex.c: In function ‘main’:
ex.c:6:51: warning: operation on ‘p’ may be undefined [-Wsequence-point]
    6 |     printf("*p++   = %d, p 는 이제 arr[%td]\n", *p++, (ptrdiff_t)(p - arr));
      |                                                  ~^~
ex.c:11:50: warning: operation on ‘p’ may be undefined [-Wsequence-point]
   11 |     printf("*++p   = %d, p 는 이제 arr[%td]\n", *++p, (ptrdiff_t)(p - arr));
      |                                                  ^~~
*p++   = 10, p 는 이제 arr[0]
(*p)++ = 10, arr[0] 은 이제 10
*++p   = 20, p 는 이제 arr[0]
```

**문을 나눠 다시 재면**

```text
*p++   = 10,  p - arr = 1
(*p)++ = 10,  arr[0] = 11,  p - arr = 0
*++p   = 20,  p - arr = 1
```

**왜 그런가**

```text
   한 printf 안에서 잰 것        문을 나눠 잰 것
   +------------------------+   +------------------------+
   | p - arr  = 0           |   | p - arr  = 1           |
   | arr[0]   = 10          |   | arr[0]   = 11          |
   | p - arr  = 0           |   | p - arr  = 1           |
   +------------------------+   +------------------------+
     ★ "아무것도 안 변했다"        ★ 실제로는 다 변했다
```

- **틀린 쪽이 「아무 일도 안 일어났다」로 보인다** — 그래서 의심이 안 간다. 이게 이 사고가 무서운 이유다.
- 말해 준 것은 **`-Wsequence-point` 하나**다. 경고를 안 봤으면 그대로 문서에 실렸을 것이다.
- ★ **이 갈래에서 세 번째 나온 같은 사고**다 — [05번 형제](../05-explicit-casts-and-pointer-conversions/)·[08번 형제](../08-sizeof-alignment-and-offsetof/), 그리고 이 문서.\
  우연이 아니라 **측정 코드의 구조적 함정**이고, 규칙은 「**부작용을 재려면 문을 나눈다**」다.

### 7. 미명시와 UB 를 가르는 것 — **같은 객체냐** ★★★

**답**

```text
   ① 두 부작용에 순서가 없다 + 서로 다른 객체
      -> ★ 미명시 : 값은 "가능한 것들 중 하나". 프로그램은 멀쩡하다.
         예: printf("%d %d", pop(), pop())     최악 = 30 40 이거나 40 30

   ② 두 부작용에 순서가 없다 + ★ 같은 객체
      (또는 하나가 바꾸고 하나가 다른 목적으로 읽는다)
      -> ★ UB : 값이 안 정해지는 게 아니라 ★ 프로그램의 뜻 자체가 없다.
         예: i = i++                            최악 = 무엇이든
```

- **①은** 「**어느 쪽이 먼저인지 모른다**」이고 **②는** 「**그런 프로그램이 아니다**」다.
- **미명시의 최악은** 「**둘 중 하나**」이고 **UB 의 최악은** 「**컴파일러가 그 코드를 지워도 된다**」다.
- ★ 두 `pop()` 은 `top` 을 둘 다 건드리는데도 미명시다 — **함수 호출이라 서로 섞이지 않기 때문**이다(11번 답).
- **이 구분을 못 하면 도구의 침묵을 잘못 읽는다** — 미명시 자리의 침묵은 「**검사 대상이 아님**」인데
  그것을 「**검사해 봤더니 깨끗함**」으로 읽게 된다.

### 8. 평가 순서가 「구현 정의」가 아닌 이유 — **문서화 의무**

**답**

| | 구현 정의 | 미명시 |
|---|---|---|
| 구현마다 다른가 | 그렇다 | 그렇다 |
| **문서화 의무** | ★ **있다** | ★ **없다** |
| 그래서 독자는 | 그 구현의 문서를 읽고 **기댈 수 있다** | 기댈 근거가 **아예 없다** |

- gcc 가 다섯 최적화 수준에서 늘 오른쪽부터 평가해도 그것은 **관찰**이다.\
  표준이 **「구현이 문서화하라」고 요구하지 않았기 때문에** 구현은 다음 판에서 방향을 바꿔도 된다.
- 그래서 「gcc 는 오른쪽부터 평가한다」를 **약속으로 인용할 자리가 없다.**\
  ★ 이 문서가 확인한 것은 **층 구분**(표준이 그 의무를 지우지 않는다)까지이고, **gcc 문서 전문을 훑지는 않았다.**
- [02번 형제](../02-basic-types-sizes-and-fixed-width-integers/)의 `sizeof(int)` 나 [11번 형제](../11-bitwise-operations-and-shifts/)의 `-1 >> 1` 이 **구현 정의**의 예다 —\
  그쪽은 **구현의 문서에 적혀 있고**, 여기는 적힐 의무가 없다.

### 9. sanitizer 의 두 침묵 — **원리상 못 보는 것**과 **지금 안 보는 것** ★★

**출력**

```text
   -fsanitize=undefined -fno-sanitize-recover=all

   gcc  UBSan  -> 진단 0줄, exit=0, 출력 "h g f"
   clang UBSan -> 진단 0줄, exit=0, 출력 "f g h"
   ★ 두 실행의 결과가 다른데 둘 다 "깨끗" 하다.

[-std=c17 -Wall -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 0 건  exit=0
[-std=c17 -Wsequence-point] 0 건  exit=0
[-std=c17 -Wall -Wextra -Wconversion] 0 건  exit=0
```

**왜 그런가 — 두 침묵은 종류가 다르다**

| 자리 | 층 | 침묵의 종류 |
|---|---|---|
| 인자 평가 순서 | **미명시** | ★★ **원리상 못 본다** — UBSan 은 U(ndefined) B(ehavior) sanitizer 다. 미명시는 **검출 대상 자체가 아니다** |
| `i = i++` | **UB** | ★ **지금 안 본다** — UB 는 맞는데 **기본 검사 집합에 이 항목이 없다.** 도구가 커지면 잡힐 수 있다 |

- 그래서 이 주제에 남는 검사는 **「컴파일러를 두 대 돌려 답이 같은지 보는 것」** 하나다.
- ★ 그마저도 **증명이 아니라 반증 도구**다 — 답이 다르면 확실히 문제이고, 같아도 아무것도 보장되지 않는다.
- ★ `i = i++` 쪽은 **컴파일 타임 경고가 전담**한다. 런타임 도구를 기다릴 이유가 없다.

### 10. 경고 이름·건수·세는 법

**출력**

```text
[-std=c17] 0 건  exit=0
[-std=c17 -Wall] 5 건  exit=0
[-std=c17 -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra] 5 건  exit=0
[-std=c17 -Wsequence-point] 5 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 5 건  exit=0
[-std=c17 -O2 -Wall -Wextra] 5 건  exit=0

[clang -std=c17 -Wall -Wextra] 4 건 exit=0
[clang -std=c17 -Wall -Wextra -pedantic] 4 건 exit=0
```

```text
===== 소스: ex.c (3번 답과 같은 프로그램 — 줄 번호가 맞는다) =====
#include <stdio.h>
int main(void) {
    int i = 5;
    i = i++;
    printf("i = i++      -> i = %d\n", i);
    int j = 5;
    int k = j++ + j++;
    printf("j++ + j++    -> k = %d, j = %d\n", k, j);
    int a[8] = {0};
    int n = 2;
    a[n] = n++;
    printf("a[n] = n++   -> n = %d, a[2] = %d, a[3] = %d\n", n, a[2], a[3]);
    int m = 1;
    m = m++ + ++m;
    printf("m = m++ + ++m -> m = %d\n", m);
    return 0;
}
```

```text
ex.c:4:10: warning: multiple unsequenced modifications to 'i' [-Wunsequenced]
ex.c:7:14: warning: multiple unsequenced modifications to 'j' [-Wunsequenced]
ex.c:11:13: warning: unsequenced modification and access to 'n' [-Wunsequenced]
ex.c:14:10: warning: multiple unsequenced modifications to 'm' [-Wunsequenced]
4 warnings generated.
```

**왜 그런가**

- ★ **`-Wsequence-point` 는 `-Wall` 에 있다.** `-Wextra` 단독은 0건이다 —\
  [09번 형제](../09-operator-precedence-and-associativity/)의 `-Wparentheses` 와 같은 자리다. 최적화를 켜도 건수가 같다(**컴파일 타임 검사**다).
- clang 의 이름은 **`-Wunsequenced`** 이고 **C11 의 말**(`unsequenced`)을 그대로 쓴다. gcc 는 아직 옛 말(`sequence-point`)이다.
- ★ clang 은 **두 종류를 구분해 말한다** — 「multiple unsequenced **modifications**」와 「unsequenced modification **and access**」.\
  **UB 의 두 조항이 그대로 문구가 된 것**이다.
- **건수가 갈리는 줄은 `m = m++ + ++m`** 이다 — gcc 2건, clang 1건. 나머지 네 줄은 양쪽 다 1건씩이다.
- ★ **`grep -c warning` 으로 세면 clang 쪽이 5 로 나온다** — 끝의 `4 warnings generated.` 한 줄이 같이 잡히기 때문이다.\
  **`grep -c 'warning:'` 으로 세면** 양쪽 다 진단 수와 같아진다(gcc 5 · clang 4).\
  ★ 이것이 [09번 형제](../09-operator-precedence-and-associativity/)의 「없는 플래그로 거짓 0건」과 **같은 집안**이다 — **세는 방법 자체가 측정 대상**이다.

### 11. 두 함수 호출은 섞이지 않는다 — indeterminately sequenced

**출력**

```text
===== gcc -O0 =====            ===== clang -O0 =====
F() + G() :                    F() + G() :
  F 들어감                      F 들어감
  F 나옴                        F 나옴
  G 들어감                      G 들어감
  G 나옴                        G 나옴
  = 3                          = 3
```

**왜 그런가**

```text
   일어날 수 있는 것            ★ 절대 안 일어나는 것
   +----------------------+   +----------------------+
   | F 들어감              |   | F 들어감              |
   | F 나옴                |   | G 들어감   <- 끼어듦   |
   | G 들어감              |   | F 나옴                |
   | G 나옴                |   | G 나옴                |
   +----------------------+   +----------------------+
   또는 G 가 통째로 먼저
```

- **번갈아 실행될 수 없다.** 하나가 통째로 끝난 뒤에 다른 하나가 시작된다. 이름은 **indeterminately sequenced** 다.
- **「미명시」와 다른 말이다.** 미명시는 「값이 둘 중 하나」이고 이쪽은 **「섞이지 않는다」는 보장**이다.\
  그래서 두 `pop()` 이 `top` 을 **각자 하나씩** 줄인다는 것은 보장되고, **누가 먼저인지만** 모른다.
- ★ **이 관찰에서 주장할 수 있는 것은 「섞이지 않았다」까지다.** 「`F` 가 먼저다」는 주장할 수 없다 —\
  양쪽이 다 `F` 부터였던 것은 **이 판의 결과**이고, 표준의 보장은 **겹치지 않는다는 것 하나**다.

### 12. 그래서 어떻게 쓰나

**규칙 한 줄**

```text
   ★ 한 문(statement) 에 부작용은 하나.
     이 한 줄이 이 주제의 함정 전부를 덮는다.
```

**빌드 플래그와 그 한계**

```text
개발·운영 빌드
  gcc   -std=c17 -O2 -Wall -Wextra -Werror     (-Wsequence-point 가 -Wall 에 있다)
  clang -std=c17 -O2 -Wall -Wextra -Werror     (-Wunsequenced)

이것이 잡는 것   : 같은 객체를 한 식에서 두 번 건드리는 UB
★ 못 잡는 것     : 인자 평가 순서 · pop(), pop()  = 미명시
                   -> 경고 0건 · UBSan 0줄. 컴파일러 두 대를 돌리는 것뿐이다.
```

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 값 두 개를 꺼내 찍기 | `a = pop(); b = pop(); printf(..., a, b);` | `printf(..., pop(), pop())` |
| 인덱스를 쓰며 늘리기 | `a[i] = v; i++;` | `a[i] = i++;` |
| 부작용 있는 식을 **재기** | **문을 나눈다** | 한 `printf` 안에서 재기 |
| 평가 순서 확인 | **gcc 와 clang 둘 다 돌린다** | 한 대만 돌리고 단정 |
| 이 주제의 UB 확인 | **`-Wall`**(`-Wsequence-point`) | `-fsanitize=undefined` |

**형제 주제**

- 「무엇이 먼저 **묶이나**」의 정본은 [09번 형제](../09-operator-precedence-and-associativity/)다. **묶는 순서는 도는 순서를 정하지 않는다.**
- ★ **UB 가 본체인 주제**는 [11번 형제](../11-bitwise-operations-and-shifts/)다 — 거기서는 **UBSan 이 세 번 말을 하고** 여기서는 침묵한다.\
  **같은 도구의 두 얼굴**이고, 그 차이가 「미명시 대 UB」의 실측 증거다.

---

## 실행 검증

| 프로그램 | 무엇을 확인했나 | 어느 컴파일러·플래그로 돌렸나 |
|---|---|---|
| 인자 평가 순서 | `take(f(),g(),h())` 가 gcc `h g f` · clang `f g h` · **받은 값은 양쪽 `1 2 3`** | gcc·clang `-O0`\~`-Os` 다섯 벌 · 양쪽 UBSan |
| 인자 개수·중첩 | 2·3·7개에서 방향 불변 · 중첩 `outer(A(), inner(B(),C()))` = gcc `CBA` · clang `ABC` | gcc·clang `-O0`·`-O2`·`-Os` |
| ★ 중첩 라벨 반례 | **`A(B(),C())` 꼴은 gcc `CBA` · clang `BCA`** — 라벨 하나가 답을 바꾼다 | gcc·clang `-O0` |
| `pop()` 두 번 | gcc `30 40` ↔ clang `40 30` · 문을 나누면 양쪽 `40 30` · **경고 0건** | gcc·clang `-O0`\~`-Os` · 양쪽 UBSan |
| `i = i++` 4종 | 여덟 벌 전부 `i=5 k=11 j=7 n=3 a[3]=2 m=4` · gcc 5건 / clang 4건 | gcc 5벌 · clang 2벌 · UBSan |
| 플래그 소속 | `-Wsequence-point` = **`-Wall`** · `-Wextra` 단독 0건 · `-O2` 에서도 5건 | gcc 7벌 · clang 2벌 |
| ★ 세는 법 | `grep -c warning` 은 clang 을 **5** 로 센다(요약 줄) · `grep -c 'warning:'` 은 **4** | gcc·clang |
| 시퀀스 포인트 | `side` 호출 **0·0·1 회** · `p && p->val` 이 `NULL` 에서 살아남음 · 경고 1건 | gcc·clang `-Wall -Wextra -pedantic` |
| 대입 대상 바꾸기 | `t=6 i=7` · `u=1 j=7` · `w=6 k=7` · **0건** | gcc·clang `-Wall -Wextra -pedantic` |
| 측정 사고 | 한 `printf` 안 = `p-arr 0`·`arr[0] 10`(틀림) ↔ 문을 나눔 = `1`·`11`(맞음) · 경고 2건 | gcc `-Wall -Wextra -pedantic` |
| 층별 도구 | 다섯 구문 각각의 gcc `-Wall` / `+pedantic` / clang / UBSan 건수 | 구문마다 파일을 나눠 4벌씩 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)의 관찰**이다.

- gcc 가 인자를 **오른쪽부터**, clang 이 **왼쪽부터** 평가하는 것 — ★ **구현 정의가 아니라 미명시**다. **문서화 의무가 없다.**
- `i = i++` 이 `5`, `k` 가 `11`, `m` 이 `4` 인 것 — **UB 이므로 값 자체가 근거가 못 된다.**
- `a[3]` 에 `2` 가 들어간 것 — 같은 이유로 관찰일 뿐이다.
- gcc 가 `m = m++ + ++m` 에 **2건**, clang 이 **1건**을 내는 것 — 진단 구현의 차이다.

**시퀀스 포인트 규칙 자체는 구현 의존이 아니다.** 일곱 자리와 단락 평가는 **어느 C 구현에서도 같다.**

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `volatile` 을 붙인 판 · `*p = (*q)++` 에서 `p == q` 인 판 ·\
  C++ 의 평가 순서(C++17 이 바꾼 자리) · `-fsanitize=list` 로 검사 항목 전수 훑기 · gcc 문서 전수 검색.
- **못 잰 것** — **「UB 라서 오늘 이 값이 나왔다」의 원인**. 컴파일러 내부 결정이라 값으로는 확인할 수 없다.\
  확인할 수 있는 것은 「**경고가 났다**」까지다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- gcc·clang 의 **인자 평가 방향**(`h g f` ↔ `f g h`)이 그대로인지 — **보장이 아니므로 언제든 바뀔 수 있다.**
- `-Wsequence-point` 의 소속(`-Wall`)과 **건수**(gcc 5 / clang 4).
- UBSan 의 기본 검사 집합에 **이 UB 가 추가됐는지** — 9번 답의 「지금 안 본다」가 바뀌는 자리다.
- **시퀀스 포인트 일곱 자리는 다시 돌릴 필요가 없다** — C89 이후 규칙이 바뀐 적이 없다(C11 은 말만 바꿨다).
