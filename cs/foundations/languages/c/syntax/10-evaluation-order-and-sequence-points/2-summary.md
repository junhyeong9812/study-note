# c/syntax/10 — 평가 순서와 시퀀스 포인트: 무엇이 먼저 **도나** — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects) · [cppreference — Order of evaluation (C)](https://en.cppreference.com/w/c/language/eval_order) · [GCC 13 Warning Options](https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Warning-Options.html) · [Clang Diagnostic flags](https://clang.llvm.org/docs/DiagnosticsReference.html)
> **실행 검증** — 이 문서의 모든 출력·경고는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다.\
> ★ **이 주제는 컴파일러 한 대로는 아무것도 증명할 수 없다.** 그래서 **모든 실험을 둘 다에서** 돌렸고,\
> 최적화 수준도 `-O0`·`-O1`·`-O2`·`-O3`·`-Os` 다섯 벌로 나눠 돌렸다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.
> **버전** — C89\~C99 는 「**시퀀스 포인트**」로, **C11 부터는 「시퀀스 관계**」(sequenced before / indeterminately sequenced /\
> unsequenced)로 같은 것을 더 정밀하게 말한다. **규칙이 바뀐 것이 아니라 말이 바뀐 것**이고,\
> gcc 의 경고 이름은 아직 `-Wsequence-point` 다. C23 도 이 주제를 건드리지 않았다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.
> ★★ **경계 — [09번 형제](../09-operator-precedence-and-associativity/)는 「무엇이 먼저 **묶이나**」(문법)이고 여기는 「무엇이 먼저 **도나**」(의미)다.**\
> 승격·변환은 [03번 형제](../03-integer-promotion-and-usual-arithmetic-conversions/), 부호 있는 오버플로 자체는 목록의 **54번 주제**가 정본이다.

## 한눈에 — 쉽게 말하면

**C 는 「한 문장 안에서 무엇을 먼저 할지」를 대부분 정해 주지 않는다. 그리고 그것을 어겨도 아무도 말해 주지 않는다.**

요리법에 비유하면 이렇다.\
「**양파를 볶고 마늘을 볶아 함께 넣어라**」라고 적힌 요리법은 **순서를 정하지 않은 것**이다.\
마늘을 먼저 볶아도 요리법을 어긴 게 아니다 — 다만 **맛이 달라진다.**\
그런데 「**같은 냄비에 소금을 넣으면서 동시에 국물 간을 봐라**」는 **요리법 자체가 성립하지 않는다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 | 층 |
|---|---|---|
| 「둘 다 하라」고만 적혀 있다 | 함수 인자 평가 순서 | ★ **미명시** |
| 요리사마다 순서가 다르다 | gcc 는 오른쪽부터, clang 은 왼쪽부터 | 둘 다 **적법** |
| 한 요리사는 **늘 같은 순서**로 한다 | 같은 컴파일러는 같은 답을 낸다 | **보장이 아니다** |
| 「소금을 넣으면서 간을 봐라」 | `i = i++` — 한 객체를 바꾸며 읽는다 | ★ **UB** |
| 「양파 다 볶고 나서 마늘」 | `&&`·`\|\|`·`?:`·`,`·문 끝 | **시퀀스 포인트** |
| 두 요리를 **번갈아 젓지는 않는다** | `F() + G()` 의 두 호출은 **섞이지 않는다** | indeterminately sequenced |

```text
   printf("%d %d\n", pop(), pop());        스택 = [10, 20, 30, 40]

   gcc 13.3.0                        clang 18.1.3
   +--------------------------+     +--------------------------+
   | 오른쪽 pop() 을 먼저      |     | 왼쪽 pop() 을 먼저        |
   |   -> 40 을 꺼냄           |     |   -> 40 을 꺼냄           |
   | 그 다음 왼쪽              |     | 그 다음 오른쪽            |
   |   -> 30 을 꺼냄           |     |   -> 30 을 꺼냄           |
   | 출력: ★ 30 40            |     | 출력: ★ 40 30            |
   +--------------------------+     +--------------------------+
     경고 0건 · UBSan 침묵           경고 0건 · UBSan 침묵

   ★ 둘 다 맞다. 표준이 순서를 안 정했기 때문이다.
```

- 그래서 이 주제의 결론은 「**한 문(statement) 안에서 부작용을 두 번 일으키지 마라**」다.
- 그리고 ★★ **미명시는 sanitizer 가 원리상 못 잡는다** — UB 가 아니기 때문이다. 아래 (9)에서 실측으로 보인다.

> **부작용(side effect)** — 값을 계산하는 것 말고 **바깥 상태를 바꾸는 것**. 대입·증감·`volatile` 접근·입출력.\
> 예: `i++` 은 값 `i` 를 내는 동시에 `i` 를 1 늘린다. 뒤엣것이 부작용이다.

> **시퀀스 포인트(sequence point)** — 그 지점까지의 부작용이 **전부 끝났음이 보장되는** 자리.\
> 예: 문 끝의 `;`. 그래서 `i++; j = i;` 는 안전하고 `j = i++ + i;` 는 아니다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★ **미명시와 UB 의 경계는 어디인가** — 같은 「순서를 모른다」인데 왜 하나는 「값이 둘 중 하나」이고 하나는 「아무 일이나」인가.
2. **시퀀스 포인트는 어디에 있고**, 그래서 어떤 코드가 안전해지는가.
3. ★★ **도구가 어디까지 봐 주는가** — 그리고 **원리상 못 보는 것**은 무엇인가.

## 동작 방식

### (1) ★★ 함수 인자 평가 순서는 미명시다 — 컴파일러 둘로 증명한다

**언제 쓰나** — 한 호출의 인자가 둘 이상이고 그중 하나라도 부작용이 있을 때.

```text
===== 소스: ex.c =====
#include <stdio.h>
static int order = 0;
static int f(void) { printf("  f 가 %d 번째\n", ++order); return 1; }
static int g(void) { printf("  g 가 %d 번째\n", ++order); return 2; }
static int h(void) { printf("  h 가 %d 번째\n", ++order); return 3; }
static void take(int a, int b, int c) { printf("  받은 값 = %d %d %d\n", a, b, c); }
int main(void) {
    printf("take(f(), g(), h()):\n");
    take(f(), g(), h());
    order = 0;
    printf("f() + g() * h() = ");
    int v = f() + g() * h();
    printf("  결과 %d\n", v);
    return 0;
}
```

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

```text
   take(f(), g(), h())

   gcc                          clang
   +---------------------+     +---------------------+
   | h  g  f             |     | f  g  h             |
   | 오른쪽 -> 왼쪽       |     | 왼쪽 -> 오른쪽       |
   +---------------------+     +---------------------+

   ★ 받은 값은 양쪽 다 "1 2 3" 이다.
      인자가 어느 매개변수로 가느냐는 정해져 있다 —
      ★ 정해지지 않은 것은 "언제 계산되느냐" 뿐이다.
```

그림 해설 (한 단계씩):

- **gcc 는 오른쪽부터, clang 은 왼쪽부터** 인자를 평가했다. **둘 다 적법**하다.
- **받은 값은 양쪽 다 `1 2 3`** 이다 — 순서가 달라도 **어느 인자가 어느 자리로 가는지는 바뀌지 않는다.**
- ★ **인자 개수를 2·3·7 로 바꿔도 각 컴파일러의 방향은 그대로**였다.

```text
===== 소스: ex.c =====
#include <stdio.h>
static char buf[32]; static int n;
static int A(void){ buf[n++]='A'; return 1; }
static int B(void){ buf[n++]='B'; return 1; }
static int C(void){ buf[n++]='C'; return 1; }
static int D(void){ buf[n++]='D'; return 1; }
static int E(void){ buf[n++]='E'; return 1; }
static int F(void){ buf[n++]='F'; return 1; }
static int G(void){ buf[n++]='G'; return 1; }
static void t2(int a,int b){ (void)a;(void)b; }
static void t3(int a,int b,int c){ (void)a;(void)b;(void)c; }
static void t7(int a,int b,int c,int d,int e,int f,int g)
{ (void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g; }
static int inner(int x,int y){ return x+y; }
static int outer(int x,int y){ return x+y; }
int main(void){
    n=0; t2(A(),B());                     buf[n]=0; printf("인자 2개 : %s\n", buf);
    n=0; t3(A(),B(),C());                 buf[n]=0; printf("인자 3개 : %s\n", buf);
    n=0; t7(A(),B(),C(),D(),E(),F(),G()); buf[n]=0; printf("인자 7개 : %s\n", buf);
    n=0; (void)outer(A(), inner(B(),C())); buf[n]=0; printf("중첩 outer(A(), inner(B(),C())) : %s\n", buf);
    return 0;
}
```

```text
=== gcc ===
인자 2개 : BA
인자 3개 : CBA
인자 7개 : GFEDCBA
중첩 outer(A(), inner(B(),C())) : CBA
=== clang ===
인자 2개 : AB
인자 3개 : ABC
인자 7개 : ABCDEFG
중첩 outer(A(), inner(B(),C())) : ABC
```

> ★ **이 「중첩」 줄은 `outer(A(), inner(B(),C()))` 꼴이다** — 바깥 호출의 **둘째 인자가 또 호출**인 모양.\
> **`A(B(),C())` 꼴(= `A` 자신이 바깥 호출)로 착각하면 안 된다.** 그쪽은 `A` 의 몸통이 인자 뒤에 오므로\
> 같은 환경에서 **gcc `CBA` · clang `BCA`** 가 나온다(둘 다 실측). **라벨 한 줄이 답을 바꾼다.**

- 최적화 수준 다섯 벌(`-O0`·`-O1`·`-O2`·`-O3`·`-Os`)에서도 **각 컴파일러 안에서는 한 글자도 안 바뀌었다.**
- ★★ **그래서 더 위험하다.** 「다섯 번 돌려 봤는데 같다」는 **보장이 아니라 관찰**이다 —\
  **컴파일러를 바꾸는 순간 뒤집힌다**는 것을 바로 옆 칸이 보여 주고 있다.
- ★ `f() + g() * h()` 는 **양쪽 다 `f`·`g`·`h`** 순이었다. [09번 형제](../09-operator-precedence-and-associativity/)의 우선순위로는\
  `g()*h()` 가 먼저 묶이는데도 그렇다 — **묶이는 순서와 도는 순서는 무관하다.**

비용 — 없다. **인자에 부작용을 넣지 않으면** 이 문제 자체가 사라진다.

### (2) 실무에서 이렇게 나온다 — `pop()` 두 번

**언제 쓰나** — 스택·큐·이터레이터에서 값을 두 개 꺼내 한 줄로 찍을 때.

```text
===== 소스: ex.c =====
#include <stdio.h>
static int stack[4] = {10, 20, 30, 40};
static int top = 4;
static int pop(void) { return stack[--top]; }
int main(void) {
    printf("pop() 두 번을 한 printf 에 : %d %d\n", pop(), pop());
    top = 4;
    int first = pop();
    int second = pop();
    printf("문을 나눠 부르면            : %d %d\n", first, second);
    return 0;
}
```

```text
===== gcc -Wall -Wextra -pedantic =====
(경고 없음)
pop() 두 번을 한 printf 에 : 30 40
문을 나눠 부르면            : 40 30
===== clang -Wall -Wextra =====
(경고 없음)
pop() 두 번을 한 printf 에 : 40 30
문을 나눠 부르면            : 40 30
===== UBSan(gcc) =====
pop() 두 번을 한 printf 에 : 30 40
문을 나눠 부르면            : 40 30
exit=0
```

```text
   스택 = [10, 20, 30, 40]   top = 4

   한 printf 안에서                  문을 나누면
   +--------------------------+     +--------------------------+
   | gcc   -> ★ 30 40         |     | gcc   -> 40 30           |
   | clang -> ★ 40 30         |     | clang -> 40 30           |
   +--------------------------+     +--------------------------+
     ★ 답이 다르다                     ★ 양쪽이 같다

   경고 0건 · UBSan 0줄 · exit=0 — 아무도 말해 주지 않는다.
```

그림 해설 (한 단계씩):

- **같은 소스가 두 컴파일러에서 다른 답을 낸다.** 이 문서에서 가장 강한 근거다.
- **경고가 한 건도 안 난다.** `-Wall -Wextra -pedantic` 을 다 켜도 그렇다.
- **UBSan 도 아무 말이 없다.** UB 가 아니기 때문이다 — 「둘 중 하나」이지 「아무 일이나」가 아니다.
- **문을 나누면 양쪽이 같아진다.** 고치는 법이 이것뿐이다.

비용 — 임시 변수 두 개. 그게 전부다.

### (3) ★★ 미명시와 UB 의 경계

**언제 쓰나** — 「순서를 모른다」는 말을 들었을 때. 두 가지가 섞여 있다.

```text
   한 식 안에서 두 가지 일이 있다.

   ① 두 부작용이 서로 순서가 없다
      + 하지만 서로 다른 객체를 건드린다
      -> ★ 미명시 (unspecified)
         값은 "가능한 것들 중 하나" 다. 프로그램은 멀쩡하다.
         예: printf("%d %d", pop(), pop())

   ② 두 부작용이 서로 순서가 없다
      + 그런데 ★ 같은 객체를 건드린다
        (또는 하나가 바꾸고 하나가 다른 목적으로 읽는다)
      -> ★ UB (undefined behavior)
         값이 정해지지 않는 게 아니라 ★ 프로그램의 뜻 자체가 없다.
         예: i = i++
```

- **①은** 「**어느 쪽이 먼저인지 모른다**」이고 **②는** 「**그런 프로그램이 아니다**」다.
- ★ 경계는 「**같은 객체냐**」에 있다. 두 `pop()` 은 `top` 을 둘 다 건드리는데 — **함수 호출이라 다르다**(아래 (4)).
- 구분이 중요한 이유: **미명시는 최악이라도 「둘 중 하나」이고, UB 는 컴파일러가 코드를 지워도 된다.**

비용 — 없다. 다만 **이 구분을 못 하면 도구의 침묵을 잘못 읽는다.**

### (4) 함수 호출은 섞이지 않는다 — indeterminately sequenced

**언제 쓰나** — 「그럼 두 `pop()` 이 서로 반쯤 겹쳐 돌 수도 있나?」가 궁금할 때.

```text
===== 소스: ex.c =====
#include <stdio.h>
static int F(void) { printf("  F 들어감\n"); printf("  F 나옴\n");  return 1; }
static int G(void) { printf("  G 들어감\n"); printf("  G 나옴\n");  return 2; }
int main(void) {
    printf("F() + G() :\n");
    int v = F() + G();
    printf("  = %d\n", v);
    return 0;
}
```

```text
===== gcc -O0 =====
F() + G() :
  F 들어감
  F 나옴
  G 들어감
  G 나옴
  = 3
===== clang -O0 =====
F() + G() :
  F 들어감
  F 나옴
  G 들어감
  G 나옴
  = 3
```

```text
   일어날 수 있는 것            ★ 절대 안 일어나는 것
   +----------------------+   +----------------------+
   | F 들어감              |   | F 들어감              |
   | F 나옴                |   | G 들어감   <- 끼어듦   |
   | G 들어감              |   | F 나옴                |
   | G 나옴                |   | G 나옴                |
   +----------------------+   +----------------------+
   또는 G 가 통째로 먼저         ★ 이것이 indeterminately
                                  sequenced 의 뜻이다
```

그림 해설 (한 단계씩):

- **두 호출 중 하나가 통째로 끝난 뒤에 다른 하나가 시작된다.** 순서는 모르지만 **겹치지는 않는다.**
- 그래서 두 `pop()` 이 **`top` 을 각자 하나씩 줄인다**는 것은 보장된다 — 다만 **누가 먼저인지 모른다.**
- ★ **미명시와 다른 말이다.** 미명시는 「값이 둘 중 하나」이고 이쪽은 「**섞이지 않는다**」는 **보장**이다.
- ★ **이 관찰은 「둘 다 F 부터였다」이지 「F 가 먼저다」가 아니다.** 섞이지 않는다는 것만이 표준의 보장이다.

비용 — 없다.

### (5) `i = i++` 은 UB 다 — 그리고 값으로는 안 드러난다

**언제 쓰나** — 「`i = i++` 이 뭐가 되지?」가 궁금할 때. **값을 외우면 안 되는 자리다.**

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
===== gcc -std=c17 -Wall -Wextra -pedantic =====
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

```text
=== gcc -O0 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== gcc -O1 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== gcc -O2 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== gcc -O3 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== gcc -Os ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== clang -O0 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== clang -O2 ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
=== gcc UBSan ===
i = i++      -> i = 5
j++ + j++    -> k = 11, j = 7
a[n] = n++   -> n = 3, a[2] = 0, a[3] = 2
m = m++ + ++m -> m = 4
exit=0
```

```text
   ★ 여덟 벌이 한 글자도 다르지 않다.
     gcc -O0 -O1 -O2 -O3 -Os · clang -O0 -O2 · gcc UBSan

   "안 터졌다" 와 "값이 늘 같다" 는
   ★ "안전하다" 와 아무 관계가 없다.

   이 자리에서 위험을 말해 준 것은 딱 하나 —
   ★ 컴파일 타임 경고 -Wsequence-point 다.
```

그림 해설 (한 단계씩):

- ★★ **값을 외우면 안 된다.** 여기서 `i = 5`, `k = 11` 이 나왔다고 그게 「정답」이 아니다.\
  UB 는 **답이 없는 것**이지 **다른 답이 있는 것**이 아니다.
- **UBSan 이 한 줄도 안 낸다.** 「한 식 안에서 같은 객체를 두 번 바꾸는 것」에 대한 **런타임 검사가 없다.**
- `a[n] = n++` 의 결과를 보면 무엇이 일어났는지 보인다 — **`a[3]` 에 2 가 들어갔다.**\
  왼쪽 `a[n]` 의 주소를 **증가한 뒤의 `n`** 으로 계산했다는 뜻이다.
- ★ 그래서 이 주제의 검사는 **런타임이 아니라 컴파일 타임**에 있다.

비용 — 없다. **문을 나누면 된다.**

### (6) `-Wsequence-point` 가 어디에 있나 — 세어서 확인

**언제 쓰나** — 빌드 플래그를 정할 때.

```text
[-std=c17] 0 건  exit=0
[-std=c17 -Wall] 5 건  exit=0
[-std=c17 -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra] 5 건  exit=0
[-std=c17 -Wsequence-point] 5 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 5 건  exit=0
[-std=c17 -O2 -Wall -Wextra] 5 건  exit=0
```

- ★ **`-Wall` 에 있다.** `-Wextra` 단독은 0건이다([09번 형제](../09-operator-precedence-and-associativity/)의 `-Wparentheses` 와 같은 자리다).
- 최적화를 켜도 건수가 같다 — **컴파일 타임 검사**이기 때문이다.

clang 은 **플래그 이름도 건수도 다르다.**

```text
[clang -std=c17 -Wall -Wextra] 4 건 exit=0
[clang -std=c17 -Wall -Wextra -pedantic] 4 건 exit=0
```

> ★ **세는 법 주의** — 위 4 건은 **진단 줄**을 센 것이다. clang 은 끝에 `4 warnings generated.` 를 **한 줄 더** 찍으므로\
> `grep -c warning` 으로 세면 **5** 가 나온다(gcc 는 그 요약 줄이 없어 5 가 그대로 5 다).\
> **`grep -c 'warning:'` 으로 세면 양쪽 다 진단 수와 같다** — 실측으로 확인했다.

```text
ex.c:4:10: warning: multiple unsequenced modifications to 'i' [-Wunsequenced]
    4 |     i = i++;
      |       ~  ^
ex.c:7:14: warning: multiple unsequenced modifications to 'j' [-Wunsequenced]
    7 |     int k = j++ + j++;
      |              ^     ~~
ex.c:11:13: warning: unsequenced modification and access to 'n' [-Wunsequenced]
   11 |     a[n] = n++;
      |       ~     ^
ex.c:14:10: warning: multiple unsequenced modifications to 'm' [-Wunsequenced]
   14 |     m = m++ + ++m;
      |          ^    ~~
4 warnings generated.
```

- gcc 는 **5건**(`m` 에 두 건), clang 은 **4건**(`m` 에 한 건)이다.
- ★ clang 의 문구가 **C11 의 말(`unsequenced`)을 그대로 쓴다.** gcc 는 아직 옛 이름(`sequence-point`)이다.
- ★ clang 은 **두 종류를 구분해 말한다** — 「multiple unsequenced **modifications**」와 「unsequenced modification **and access**」.\
  UB 의 두 조항이 그대로 문구가 된 것이다.

비용 — 없다.

### (7) 시퀀스 포인트가 있는 자리 — 그래서 `x && x->f` 가 안전하다

**언제 쓰나** — 널 검사와 역참조를 한 줄에 쓸 때. C 에서 매일 쓰는 형태다.

```text
===== 소스: ex.c =====
#include <stdio.h>
struct Node { int val; };
static int calls = 0;
static int side(int r) { calls++; return r; }
int main(void) {
    struct Node *p = NULL;
    /* (1) && 는 시퀀스 포인트 — 왼쪽이 거짓이면 오른쪽을 아예 안 본다 */
    if (p && p->val == 3) printf("안 찍힌다\n");
    printf("(1) p && p->val  -> 살아서 여기까지 왔다\n");
    /* (2) 단락 평가: 오른쪽이 실행되지 않은 것을 부작용 수로 센다 */
    calls = 0; (void)(0 && side(1)); printf("(2) 0 && side()  -> side 호출 %d 회\n", calls);
    calls = 0; (void)(1 || side(1)); printf("(2) 1 || side()  -> side 호출 %d 회\n", calls);
    /* (3) ?: 도 시퀀스 포인트 */
    calls = 0; (void)(0 ? side(1) : side(2)); printf("(3) 0 ? side : side -> side 호출 %d 회\n", calls);
    /* (4) 콤마도 시퀀스 포인트 — i++ , i++ 는 UB 가 아니다 */
    int i = 5;
    i = (i++, i++);
    printf("(4) i = (i++, i++)  -> i = %d\n", i);
    /* (5) && 사이의 증감도 UB 가 아니다 */
    int k = 5;
    int r = k++ && k++;
    printf("(5) k++ && k++      -> r = %d, k = %d\n", r, k);
    return 0;
}
```

```text
===== gcc -Wall -Wextra -pedantic =====
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

```text
   시퀀스 포인트가 있는 자리

   1. 문 끝의  ;                       가장 흔한 자리
   2. &&  의 왼쪽과 오른쪽 사이          -> 단락 평가가 여기서 나온다
   3. ||  의 왼쪽과 오른쪽 사이
   4. ?:  의 조건과 선택된 가지 사이
   5. ,   (콤마 연산자) 의 왼쪽과 오른쪽 사이
   6. 함수 호출에서 ★ 인자 평가가 다 끝난 뒤, 몸통에 들어가기 전
   7. 완전식(full expression) 의 끝 — 초기자, if/switch/while 의 제어식,
      for 의 세 칸 각각, return 의 식

   ★ 여기 없는 것 : 인자들 사이 · 이항 연산자의 양쪽 · 대입의 양쪽
```

그림 해설 (한 단계씩):

- **`p && p->val` 이 안전한 이유**가 2번이다. 왼쪽이 거짓이면 **오른쪽을 아예 평가하지 않는다.**\
  `p` 가 `NULL` 인데도 프로그램이 살아서 다음 줄을 찍었다.
- **단락 평가를 부작용 수로 셌다** — `0 && side(1)` 에서 `side` 가 **0회** 호출됐다.
- **`?:` 도 한 가지만 평가한다** — 두 가지가 있는데 `side` 가 **1회**만 불렸다.
- ★ **`k++ && k++` 은 UB 가 아니다.** 경고가 안 난다 — 둘 사이에 시퀀스 포인트가 있기 때문이다.
- ★★ **그런데 `i = (i++, i++)` 은 UB 다.** 다음 절에서 본다.

비용 — 없다. **단락 평가는 공짜로 얻는 안전장치**다.

### (8) ★★ 콤마가 시퀀스 포인트라고 `i = (i++, i++)` 이 안전해지지는 않는다

**언제 쓰나** — 「콤마가 시퀀스 포인트라니까 이건 되겠지」라고 생각한 순간.

앞 절의 경고 한 건이 바로 그 자리였다.

```text
ex.c:17:7: warning: operation on ‘i’ may be undefined [-Wsequence-point]
   17 |     i = (i++, i++);
      |     ~~^~~~~~~~~~~~
```

```text
ex.c:17:16: warning: multiple unsequenced modifications to 'i' [-Wunsequenced]
   17 |     i = (i++, i++);
      |       ~        ^
```

```text
   i = (i++, i++)

   두 i++ 사이에는 시퀀스 포인트가 있다.       -> 여기는 괜찮다
   그런데 ★ 바깥의 대입 i = ... 이
      두 i++ 어느 쪽과도 순서 관계가 없다.     -> ★ 여기가 UB 다

   "콤마가 있으니 안전" 은 ★ 안쪽만 본 것이다.
```

대입 대상을 **다른 변수**로 바꾸면 경고가 사라진다.

```text
===== 소스: ex.c =====
#include <stdio.h>
int main(void) {
    int i = 5;
    int t = (i++, i++);          /* 대입 대상이 i 가 아니다 */
    printf("t = (i++, i++)   -> t = %d, i = %d\n", t, i);
    int j = 5;
    int u = j++ && j++;          /* && 사이에 시퀀스 포인트가 있다 */
    printf("u = j++ && j++   -> u = %d, j = %d\n", u, j);
    int k = 5;
    int w = k++ ? k++ : k++;     /* ?: 도 시퀀스 포인트 */
    printf("w = k++ ? k++ : k++ -> w = %d, k = %d\n", w, k);
    return 0;
}
```

```text
[-std=c17 -Wall -Wextra -pedantic] 0 건  exit=0
```

```text
t = (i++, i++)   -> t = 6, i = 7
u = j++ && j++   -> u = 1, j = 7
w = k++ ? k++ : k++ -> w = 6, k = 7
```

- **gcc 도 clang 도 0건**이다. 같은 `i++` 두 개인데 **대입 대상만 바꿨을 뿐**이다.
- ★ **UB 인지 아닌지는 「부작용이 몇 개냐」가 아니라 「같은 객체에 순서 없는 부작용이 둘이냐」로 갈린다.**

비용 — 없다.

### (9) ★★ UBSan 은 미명시를 원리상 못 잡는다 — 실측

**언제 쓰나** — 「sanitizer 돌렸는데 깨끗하다」는 말을 들었을 때.

(1)의 프로그램을 **UBSan 으로 다시 돌렸다.**

```text
=== UBSan ===
take(f(), g(), h()):
  h 가 1 번째
  g 가 2 번째
  f 가 3 번째
  받은 값 = 1 2 3
f() + g() * h() =   f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  결과 7
exit=0
=== clang UBSan ===
take(f(), g(), h()):
  f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  받은 값 = 1 2 3
f() + g() * h() =   f 가 1 번째
  g 가 2 번째
  h 가 3 번째
  결과 7
exit=0
```

```text
   -fsanitize=undefined -fno-sanitize-recover=all

   gcc  UBSan  -> 진단 0줄, exit=0, 출력 "h g f"
   clang UBSan -> 진단 0줄, exit=0, 출력 "f g h"

   ★ 두 실행의 결과가 다른데 둘 다 "깨끗" 하다.

   당연하다 — UBSan 은 U(ndefined) B(ehavior) sanitizer 다.
   미명시는 undefined 가 아니다. ★ 검출 대상 자체가 아니다.
```

그림 해설 (한 단계씩):

- **미명시는 UB 가 아니다.** 그러므로 **UB 를 찾는 도구가 원리상 찾을 수 없다.**\
  버그가 아니라 **범위 밖**이다.
- 플래그도 침묵한다 — 아래 넷 전부 0건이었다.

```text
[-std=c17 -Wall -Wextra] 0 건  exit=0
[-std=c17 -Wall -Wextra -pedantic] 0 건  exit=0
[-std=c17 -Wsequence-point] 0 건  exit=0
[-std=c17 -Wall -Wextra -Wconversion] 0 건  exit=0
```

- ★★ **그래서 이 주제의 유일한 검사는 「컴파일러를 두 대 돌려 답이 같은지 보는 것」이다.**\
  이 문서가 모든 실험을 gcc·clang 두 벌로 돌린 이유가 그것이다.
- ★ 그마저도 **증명이 아니라 반증 도구**다 — 답이 다르면 확실히 문제이고, 같아도 아무것도 보장되지 않는다.

비용 — 컴파일러 한 대 더. 이 주제에서는 그게 유일한 값싼 검사다.

### (10) ★★ 측정 코드 자체가 걸린다

**언제 쓰나** — 부작용이 있는 식을 **재려고** 할 때. 이 문서를 쓰면서 실제로 당했다.

[09번 형제](../09-operator-precedence-and-associativity/)의 `*p++` 실험을 처음에 이렇게 썼다.

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

문을 나눠 다시 쟀다.

```text
===== 소스: ex.c (고친 측정 코드) =====
#include <stdio.h>
#include <stddef.h>
int main(void) {
    int arr[4] = {10, 20, 30, 40};
    int *p = arr, v;
    v = *p++;                       /* 문을 나눈다 — 한 printf 안에서 재지 않는다 */
    printf("*p++   = %d,  p - arr = %td\n", v, p - arr);
    p = arr;
    v = (*p)++;
    printf("(*p)++ = %d,  arr[0] = %d,  p - arr = %td\n", v, arr[0], p - arr);
    arr[0] = 10; p = arr;
    v = *++p;
    printf("*++p   = %d,  p - arr = %td\n", v, p - arr);
    return 0;
}
```

```text
*p++   = 10,  p - arr = 1
(*p)++ = 10,  arr[0] = 11,  p - arr = 0
*++p   = 20,  p - arr = 1
```

```text
   같은 세 줄인데 답이 다르다.

   한 printf 안에서 잰 것        문을 나눠 잰 것
   +------------------------+   +------------------------+
   | p - arr  = 0           |   | p - arr  = 1           |
   | arr[0]   = 10          |   | arr[0]   = 11          |
   | p - arr  = 0           |   | p - arr  = 1           |
   +------------------------+   +------------------------+
     ★ "아무것도 안 변했다"        ★ 실제로는 다 변했다

   -> 틀린 쪽이 "아무 일도 안 일어난 것처럼" 보인다.
      이게 이 사고가 무서운 이유다.
```

그림 해설 (한 단계씩):

- 틀린 쪽은 「**포인터가 안 움직였다**」·「**값이 안 늘었다**」는 **정반대의 결론**을 내게 한다.
- **`-Wsequence-point` 가 말해 줬다.** 경고를 안 봤으면 그대로 문서에 실렸을 것이다.
- ★ [05번 형제](../05-explicit-casts-and-pointer-conversions/)에도 같은 사고가 적혀 있다 — [08번 형제](../08-sizeof-alignment-and-offsetof/)의 `sizeof` 실험에서\
  한 `printf` 안에 부작용과 그것을 읽는 식을 같이 넣었다가 **「호출 수가 안 늘었다」는 틀린 관찰**이 나왔다.
- ★★ **같은 사고가 이 갈래에서 세 번째다.** 우연이 아니라 **측정 코드의 구조적 함정**이다.

비용 — 임시 변수 하나. **부작용을 재려면 문을 나눈다**가 규칙이 된다.

## 문법 — 형태와 규칙

### 형태 — 시퀀스 포인트가 있는 곳 / 없는 곳

```c
/* ===== 있는 곳 (안전하다) ===== */
i++; j = i;                  /* 문 끝의 ; */
if (p && p->val) { }         /* && 의 좌우 사이 */
x = (p ? p->val : 0);        /* ?: 의 조건과 가지 사이 */
for (i = 0, j = n; i < j; i++, j--) { }   /* 콤마 연산자의 좌우 사이 */
f(g(), h());                 /* g·h 각각의 "인자 끝~몸통 시작" 사이 */

/* ===== 없는 곳 (위험하다) ===== */
f(i++, i);                   /* ★ 인자들 사이 — 없다 */
x = i++ + i;                 /* ★ 이항 연산자의 좌우 — 없다 */
a[i] = i++;                  /* ★ 대입의 좌우 — 없다 */
x = i++ * i++;               /* ★ 없다 */
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
/* (1) 한 식에서 같은 객체를 두 번 바꾼다 -> ★ UB */
i = i++;
int k = j++ + j++;

/* (2) 바꾸면서 "다른 목적으로" 읽는다 -> ★ UB */
a[i] = i++;

/* (3) 부작용 있는 함수를 한 호출의 인자로 두 번 -> ★ 미명시 (UB 아님) */
printf("%d %d\n", pop(), pop());

/* (4) 부작용 있는 식을 한 printf 안에서 잰다 -> ★ 측정이 틀린다 */
printf("%d %td\n", *p++, p - arr);          /* 이건 UB 다 (p 를 바꾸며 읽는다) */

/* (5) 안전한 것 — 시퀀스 포인트가 사이에 있다 */
int u = j++ && j++;
int t = (i++, i++);
```

- (1)·(2)·(4)는 **`-Wall` 이 잡는다**(`-Wsequence-point`).
- ★ **(3)은 아무도 안 잡는다.** 경고도 sanitizer 도 없다. **컴파일러 둘로 돌려 답을 비교하는 것**뿐이다.

### 규칙 불릿

- **부작용의 순서는 시퀀스 포인트로만 보장된다.** 우선순위·결합성은 순서와 무관하다([09번 형제](../09-operator-precedence-and-associativity/)).
- **시퀀스 포인트는 일곱 자리**에 있다 — 문 끝 · `&&` · `||` · `?:` · `,`(연산자) · 함수 인자 평가 끝 · 완전식 끝.
- **인자들 사이·이항 연산자 좌우·대입 좌우에는 없다.**
- ★ **한 식에서 같은 스칼라 객체를 두 번 바꾸면 UB**다. **바꾸면서 다른 목적으로 읽어도 UB**다.
- ★ **부작용 있는 부분식들의 상대 순서는 미명시**다 — UB 가 아니라 「가능한 것 중 하나」다.
- ★ **두 함수 호출은 섞이지 않는다**(indeterminately sequenced). 순서는 모르지만 **겹치지는 않는다.**
- **`&&`·`||`·`?:` 는 단락 평가**를 한다 — 안 고른 쪽은 **평가 자체를 안 한다.**
- **C11 부터 말이 바뀌었다** — 「시퀀스 포인트」 → 「sequenced before / indeterminately sequenced / unsequenced」.\
  **규칙은 같고**, gcc 의 경고 이름은 아직 옛 말이다(clang 은 새 말을 쓴다).
- ★ **`-Wsequence-point` 는 `-Wall` 에 있다.** clang 의 대응은 `-Wunsequenced` 다.

## 어디서 틀리나

### 1. ★★ 「같은 컴파일러에서 늘 같은 답이 나오니까 괜찮다」

```text
   gcc  -O0 -O1 -O2 -O3 -Os -> 전부 "h g f"
   clang -O0 -O2            -> 전부 "f g h"
```

- **한 컴파일러 안에서는 다섯 벌이 한 글자도 안 다르다.** 그래서 **보장처럼 보인다.**
- **다른 컴파일러를 대면 즉시 뒤집힌다.** 관찰은 관찰이고 보장은 표준이다.
- 막는 법: **인자에 부작용을 넣지 않는다.**

### 2. 「sanitizer 가 깨끗하니까 괜찮다」 ★★

- UBSan 은 **UB 를 찾는 도구**다. **미명시는 UB 가 아니라서 검출 대상이 아니다.**
- 실측에서 **gcc UBSan 과 clang UBSan 이 서로 다른 출력을 내면서 둘 다 진단 0줄**이었다.
- 막는 법: **컴파일러 둘로 돌려 답을 비교한다.** 다르면 확실히 문제다(같아도 보장은 아니다).

### 3. 「`i = i++` 이 5 가 나오니까 그게 답이다」

```text
   여덟 벌(gcc 5 · clang 2 · UBSan 1)이 전부 i = 5
```

- **UB 는 「다른 답이 있는 것」이 아니라 「답이 없는 것」이다.** 오늘 5 였다고 내일도 5 가 아니다.
- 이 자리에서 **값은 아무 정보도 주지 않는다.** 정보를 준 것은 **컴파일 타임 경고 하나**뿐이다.
- 막는 법: **`-Wall` 을 켜고 `-Werror` 로 못 박는다.**

### 4. 「콤마가 시퀀스 포인트니까 `i = (i++, i++)` 은 된다」 ★

- **안 된다.** 두 `i++` 사이는 괜찮지만 **바깥의 대입이 어느 쪽과도 순서가 없다.**
- `int t = (i++, i++);` 처럼 **대입 대상을 바꾸면** 0건이 된다.
- 막는 법: **「부작용 개수」가 아니라 「같은 객체에 순서 없는 부작용이 둘인가」로 본다.**

### 5. ★★ 측정 코드가 자기가 재려던 것을 망가뜨린다

```text
   한 printf 안에서 잰 것 : p - arr = 0,  arr[0] = 10   ★ 틀림
   문을 나눠 잰 것        : p - arr = 1,  arr[0] = 11   ★ 맞음
```

- **틀린 쪽이 「아무 일도 안 일어났다」로 보인다** — 그래서 의심이 안 간다.
- 이 갈래에서 **같은 사고가 세 번째**다([05](../05-explicit-casts-and-pointer-conversions/)·[08](../08-sizeof-alignment-and-offsetof/)번 형제, 그리고 이 문서).
- 막는 법: **부작용을 재려면 문을 나눈다.** 그리고 **경고를 읽는다.**

### 6. 「`printf` 인자 순서는 왼쪽부터겠지」

- **gcc 는 오른쪽부터**다. 인자 2·3·7개에서 전부 그랬다.
- `printf("%d %d\n", pop(), pop())` 이 gcc 에서 `30 40`, clang 에서 `40 30` 이었다.
- 막는 법: **꺼낸 값을 변수에 받고 나서 찍는다.**

## 구현 세부사항 대 언어 보장

C 에서는 **「돌아갔다」가 아무것도 증명하지 못한다.** 다섯 층을 갈라야 한다.\
★★ **이 주제는 「미명시」 칸이 본체다.** 다른 주제에서 비어 있던 그 칸이 여기서는 가장 두껍고,\
★ **구현 정의 칸이 비어 있다** — 평가 순서는 **문서화 의무가 없기 때문**이다. 그 차이가 이 주제의 핵심이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 | **도구가 못 보는 것** |
|---|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | 시퀀스 포인트 일곱 자리 · **단락 평가**(`&&`·`\|\|`·`?:` 가 안 고른 쪽을 평가하지 않는 것) · 두 함수 호출이 **섞이지 않는 것** · 인자가 어느 매개변수로 가는지 · 완전식 끝에서 모든 부작용이 끝나는 것 | 부작용 호출 수 세기(0회·1회) · 들어감/나옴 로그 · gcc·clang 양쪽 | — |
| **조건부 표준** | 매크로가 정의될 때만 | **해당 없음** — 이 주제에 조건부 보장은 없다 | — | — |
| **구현 정의** | 문서화 의무가 있다 | ★ **해당 없음** — 평가 순서는 구현 정의가 **아니다.**\
표준이 「구현이 문서화하라」고 하지 않는다 — 그래서 「gcc 는 오른쪽부터」를 **약속으로 인용할 자리가 없다** | 층 구분으로 확인(★ gcc 문서 전문을 훑지는 않았다) | — |
| **미명시** | 몇 가지 중 하나 | ★★ **본체** — **함수 인자들의 평가 순서** · **부분식들의 평가 순서** · 두 함수 호출 중 **어느 쪽이 먼저인지** · 함수 지시자와 인자의 상대 순서 | **gcc ↔ clang 이 반대**(`h g f` ↔ `f g h`, `30 40` ↔ `40 30`) · `-O0`\~`-Os` 다섯 벌은 각 컴파일러 안에서 불변 | ★★ **경고 0건 · UBSan 0줄 · exit=0.**\
**UB 가 아니므로 UBSan 이 원리상 못 잡는다** |
| **UB** | 아무 일이나 | **한 식에서 같은 스칼라 객체를 두 번 바꾸는 것**(`i = i++`, `j++ + j++`) · **바꾸면서 다른 목적으로 읽는 것**(`a[i] = i++`) · 그 둘이 섞인 것(`m = m++ + ++m`) | `-Wsequence-point` 5건 / clang `-Wunsequenced` 4건 | ★ **UBSan 에 이 검사가 없다** — 8벌이 전부 같은 값을 내고 진단 0줄 |

### 「미명시」를 실측으로 — 같은 소스, 다른 답

```text
===== gcc -Wall -Wextra -pedantic =====
(경고 없음)
pop() 두 번을 한 printf 에 : 30 40
문을 나눠 부르면            : 40 30
===== clang -Wall -Wextra =====
(경고 없음)
pop() 두 번을 한 printf 에 : 40 30
문을 나눠 부르면            : 40 30
```

- **같은 파일·같은 표준·같은 경고 플래그**에서 답이 다르다.
- 둘 다 **경고 0건**이고 둘 다 **적법**하다. **어느 쪽도 버그가 아니다** — 코드가 버그다.

### 「도구가 못 보는 것」을 층마다

| 사실 | gcc `-Wall` | gcc `+-pedantic` | clang `-Wall -Wextra` | UBSan | 무엇이 잡나 |
|---|---|---|---|---|---|
| `i = i++` | **1건** | 1건 | **1건**(`-Wunsequenced`) | **0줄** | 컴파일 타임 경고만 |
| `j++ + j++` | **1건** | 1건 | **1건** | **0줄** | 〃 |
| `a[i] = i++` | **1건** | 1건 | **1건** | **0줄** | 〃 |
| `m = m++ + ++m` | **2건** | 2건 | **1건** | **0줄** | 〃 (건수가 다르다) |
| `i = (i++, i++)` | **1건** | 1건 | **1건** | **0줄** | 〃 |
| ★ 인자 평가 순서 | **0건** | **0건** | **0건** | **0줄** | ★ **컴파일러 두 대뿐** |
| ★ `pop(), pop()` | **0건** | **0건** | **0건** | **0줄** | ★ **컴파일러 두 대뿐** |
| `k++ && k++` | 0건 | 0건 | 0건 | 0줄 | (UB 가 아니다 — 정상) |
| `int t = (i++, i++)` | 0건 | 0건 | 0건 | 0줄 | (UB 가 아니다 — 정상) |

- ★★ **이 표의 결론은 아래 두 줄이다.**
  - **UB 는 컴파일 타임 경고가 잡는다** — 단, **UBSan 은 이 UB 를 못 잡는다**(검사 자체가 없다).
  - **미명시는 아무 도구도 못 잡는다** — **컴파일러를 두 대 돌리는 것**만 남는다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 값 두 개를 꺼내 찍기 | `a = pop(); b = pop(); printf(..., a, b);` | `printf(..., pop(), pop())` |
| 인덱스를 쓰며 늘리기 | `a[i] = v; i++;` | `a[i] = i++;` |
| 증감한 값을 쓰기 | `i++; x = i;` 또는 `x = i + 1; i++;` | `x = i++ + i;` |
| 널 검사 후 역참조 | `if (p && p->val)` | `if (p->val && p)` |
| 두 조건 중 비싼 쪽을 뒤로 | `if (cheap() && expensive())` | 순서를 뒤집기 |
| 부작용 있는 식을 **재기** | **문을 나눈다** | 한 `printf` 안에서 재기 |
| 루프 두 변수 동시 갱신 | `for (i=0, j=n; i<j; i++, j--)`(콤마는 시퀀스 포인트) | 인자 자리에 콤마 |
| 매크로 인자를 여러 번 쓰기 | 인자를 지역 변수에 한 번 받기 | `#define MAX(a,b) ((a)>(b)?(a):(b))` 에 `i++` 넘기기 |
| 평가 순서 확인 | **gcc 와 clang 둘 다 돌린다** | 한 대만 돌리고 단정 |
| 이 주제의 UB 확인 | **`-Wall`**(`-Wsequence-point`) | `-fsanitize=undefined` |

판단 규칙 두 줄.

- **한 문(statement)에 부작용은 하나.** 이 한 줄이 이 주제의 함정 전부를 덮는다.
- **미명시를 찾는 도구는 없다.** 컴파일러를 두 대 돌려 **다르면 잡고, 같아도 안심하지 않는다.**

## 핵심 문장

- **우선순위는 「무엇이 먼저 묶이나」이고 평가 순서는 「무엇이 먼저 도나」다.** 둘은 무관하다 —\
  `f() + g() * h()` 에서 `*` 가 세지만 **`f` 가 먼저 돌았다.**
- ★★ **함수 인자의 평가 순서는 미명시다.** 실측에서 **gcc 는 오른쪽부터, clang 은 왼쪽부터**였고,\
  같은 `printf("%d %d", pop(), pop())` 이 **`30 40`** 과 **`40 30`** 으로 갈렸다.
- ★ **그 자리에서 경고는 0건, UBSan 은 0줄, `exit` 은 0 이었다.** **미명시는 UB 가 아니라 sanitizer 의 검출 대상이 아니다.**
- **한 식에서 같은 객체를 두 번 바꾸면 UB** 이고, **바꾸면서 다른 목적으로 읽어도 UB** 다.\
  `-Wsequence-point`(gcc, `-Wall`)·`-Wunsequenced`(clang)가 잡는다 — **UBSan 은 못 잡는다.**
- ★ **`i = i++` 은 여덟 벌에서 전부 `5`** 였다. **「값이 늘 같다」는 「안전하다」가 아니다.**
- **시퀀스 포인트는 일곱 자리** — 문 끝 · `&&` · `||` · `?:` · `,` · 인자 평가 끝 · 완전식 끝.\
  그래서 **`x && x->f` 가 안전**하고 `0 && side()` 에서 `side` 가 **0회** 불린다.
- ★ **두 함수 호출은 섞이지 않는다**(indeterminately sequenced) — 미명시와 **다른 말**이다.
- ★★ **콤마가 시퀀스 포인트라고 `i = (i++, i++)` 이 안전해지지 않는다.** 바깥의 대입이 걸린다.
- ★★ **측정 코드 자체가 이 주제에 걸린다.** 이 갈래에서 **세 번째** 나온 사고다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 10번)
- [`09-operator-precedence-and-associativity/`](../09-operator-precedence-and-associativity/) — ★★ **그쪽은 「무엇이 먼저 묶이나」, 여기는 「무엇이 먼저 도나」.** 09 의 다섯 층 표에서 네 칸이 비어 있는 이유가 여기 있다
- [`05-explicit-casts-and-pointer-conversions/`](../05-explicit-casts-and-pointer-conversions/) — **「미명시」 층을 처음 세운 형제.** 거기 실린 측정 사고가 여기의 (10)과 같은 집안이다
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — 그 측정 사고가 **처음 난 자리**. `sizeof` 실험이 한 `printf` 안에서 뒤집혔다
- [`03-integer-promotion-and-usual-arithmetic-conversions/`](../03-integer-promotion-and-usual-arithmetic-conversions/) — **UB 를 최적화 수준으로 흔들어 보는 수법**의 정본. 거기서는 값이 갈렸고 여기서는 **안 갈렸다**
- [`11-bitwise-operations-and-shifts/`](../11-bitwise-operations-and-shifts/) — **UB 가 본체인 주제.** 거기서는 UBSan 이 말을 하고 여기서는 침묵한다 — **같은 도구의 두 얼굴**
- 목록의 **42번 주제** (함수형 매크로의 함정) — **인자 중복 평가**의 정본. `MAX(i++, j)` 가 이 주제의 사고를 매크로로 옮긴 형태다
- 목록의 **54번 주제** (부호 있는 정수 오버플로) — UB 의 정본 중 하나
- 목록의 **58번 주제** (UB 를 잡는 도구) — ★ **「sanitizer 가 못 보는 것」의 정본.** 이 문서의 (9)가 그 목록에 한 줄을 더한다
- 목록의 **47번 주제** (`<stdio.h>` 서식 출력) — `printf` 인자 자리에 부작용을 넣는 사고가 실제로 나는 자리

## 용어 풀이

- **부작용(side effect)** — 값을 내는 것 말고 바깥 상태를 바꾸는 것. 예: `i++` 이 `i` 를 늘리는 것.
- **시퀀스 포인트(sequence point)** — 그 지점까지의 부작용이 전부 끝났음이 보장되는 자리. 예: 문 끝의 `;`.
- **시퀀스 관계(C11)** — 같은 것을 더 정밀하게 말한 것. **sequenced before**(A 가 B 보다 확실히 먼저) ·\
  **indeterminately sequenced**(순서는 모르나 **겹치지 않음**) · **unsequenced**(겹쳐도 됨).
- **완전식(full expression)** — 다른 식의 일부가 아닌 식. 문 하나의 식, `if`/`while` 의 제어식, `return` 의 식, 초기자.
- **단락 평가(short-circuit evaluation)** — `&&`·`||` 가 결과가 정해지면 나머지를 **평가하지 않는 것**. 예: `0 && f()` 에서 `f` 는 안 불린다.
- **미명시 동작(unspecified behavior)** — 표준이 **여러 가능성을 허용하고 어느 것인지 정하지 않은** 것. **문서화 의무가 없다.**
- **구현 정의 동작(implementation-defined behavior)** — 구현마다 다르되 **문서화 의무가 있는** 것. ★ 평가 순서는 여기에 **속하지 않는다.**
- **미정의 동작(UB)** — 표준이 아무 요구도 하지 않는 것. **그런 프로그램이 아니다**는 뜻이다.
- **`-Wsequence-point`** — 한 식에서 같은 객체를 두 번 건드리는 것을 경고하는 gcc 플래그. **`-Wall` 에 포함.**
- **`-Wunsequenced`** — 같은 것의 clang 쪽 이름. **C11 의 말을 그대로 쓴다.**
- **UBSan(`-fsanitize=undefined`)** — UB 를 런타임에 잡는 도구. ★ **이 주제의 UB 는 검사 항목에 없고, 미명시는 원리상 대상이 아니다.**

---

## 더 들어가면

- ★ **C++17 은 이 주제를 크게 바꿨다.** 함수 인자 평가 순서는 **여전히 미명시**지만,\
  `a[i] = i++` 류의 일부가 **정의된 동작**이 되었고 `<<` 체인의 순서가 확정됐다.\
  **C 는 그 변경을 따라가지 않았다.** 이 문서에서는 **C++ 를 던져 보지 않았다** — `../../cpp/syntax/` 의 몫이다.

- **gcc 가 인자를 오른쪽부터 평가하는 것은 문서화된 약속이 아니다.**\
  x86-64 System V ABI 에서 스택 인자를 오른쪽부터 밀어 넣던 관례와 이어져 있다는 설명이 흔하지만,\
  ★ **이 문서에서 그 인과를 확인하지 않았다.** 관찰된 것은 **순서가 그랬다**는 사실뿐이다.

- ★ **`-Wsequence-point` 가 못 잡는 형태가 있다.** 포인터나 함수를 거쳐 같은 객체에 닿는 경우\
  (`*p = (*q)++` 에서 `p == q` 인 것)는 컴파일 시간에 알 수 없다.\
  **이 문서에서는 그런 예를 던져 보지 않았다.**

- **`volatile` 접근도 부작용**이라 같은 규칙에 걸린다. `v = v++` 에서 `v` 가 `volatile` 이어도 UB 다.\
  **이 문서에서는 `volatile` 판을 던져 보지 않았다.**

- ★ 「**이 UB 를 잡는 런타임 도구가 정말 없는가**」는 더 확인할 자리다.\
  이 문서가 확인한 것은 **gcc·clang 의 `-fsanitize=undefined` 기본 집합에 없다**는 것까지다.\
  `-fsanitize=list` 로 전체 목록을 훑어보지는 않았다.

- **평가 순서를 강제하는 표준적 방법은 없다.** 있는 것은 **문을 나누는 것**뿐이다.\
  시퀀스 포인트를 「만드는」 연산자(`,`·`&&`)로 우회하는 관용구가 있지만 **읽기가 나빠진다.**
