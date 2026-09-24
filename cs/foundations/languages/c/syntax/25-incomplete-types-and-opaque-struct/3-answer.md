# c/syntax/25 — 불완전 타입과 opaque struct: 「**도면 없이 열쇠만 받은 방**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s25a.c`\~`s25i.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ 5번의 **`%p` 주소 두 줄** — ASLR 로 실행마다 바뀐다 | ★★★ **컴파일 진단의 본문과 플래그 이름** |
> | 진단의 **줄 번호**(소스를 고치면 밀린다) | ★★★ **종료 코드** — `cc exit=0` \| `cc exit=1` · `run exit=0` |
> | — | ★★★ **6번의 네 벌 격자** — 경고 0건·`exit=0`·`cget = 6`·`tag = 6 · n = 3` |
> | — | ★★ **주소들 사이의 차이** — 5번의 `vp + 1` 과 `vp` 의 차 `1` |
> | — | ★★ **`sizeof(Counter *)` = 8** · `sizeof(Node)` = 16 · `sizeof(struct Edge)` = 16 |
> | — | ★ **에러 건수** — 1번은 두 컴파일러 다 **4건** |
>
> ★ **같은 바이너리를 다시 돌려도 6번의 격자는 한 가지**였다 — 이 주제에서 흔들리는 것은 **주소뿐**이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 선언만 해 둔 구조체로 여섯 가지를 해 보면 — **포인터만 되고 나머지 넷은 에러** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25a.c -o x (cc exit=1) =====
s25a.c: In function ‘main’:
s25a.c:12:19: error: storage size of ‘v’ isn’t known
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
s25a.c:13:19: error: array type has incomplete element type ‘struct Hidden’
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                   ^
s25a.c:14:28: error: invalid application of ‘sizeof’ to incomplete type ‘struct Hidden’
   14 |     printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
      |                            ^~~~~~
s25a.c:15:21: error: invalid use of undefined type ‘struct Hidden’
   15 |     printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */
      |                     ^~
s25a.c:13:19: warning: unused variable ‘a’ [-Wunused-variable]
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                   ^
s25a.c:12:19: warning: unused variable ‘v’ [-Wunused-variable]
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s25a.c -o x (cc exit=1) =====
s25a.c:12:19: error: variable has incomplete type 'struct Hidden'
   12 |     struct Hidden v;                /* (1) 변수로 못 만든다 */
      |                   ^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:13:20: error: array has incomplete element type 'struct Hidden'
   13 |     struct Hidden a[3];             /* (2) 배열 원소로 못 쓴다 */
      |                    ^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:14:21: error: invalid application of 'sizeof' to an incomplete type 'struct Hidden'
   14 |     printf("%zu\n", sizeof(struct Hidden));   /* (3) 크기를 못 묻는다 */
      |                     ^     ~~~~~~~~~~~~~~~
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
s25a.c:15:21: error: incomplete definition of type 'struct Hidden'
   15 |     printf("%d\n", p->x);           /* (4) 멤버를 못 만진다 */
      |                    ~^
s25a.c:3:8: note: forward declaration of 'struct Hidden'
    3 | struct Hidden;                      /* 선언만 했다 — 불완전 타입 */
      |        ^
4 errors generated.
```

**왜 그런가**

- ★★★ **`(가)`·`(나)` 두 선언은 아무 말 없이 통과한다.** `struct Hidden *` 은 **완전한 타입**이기 때문이다 — 무엇을 가리키든 포인터의 크기는 정해져 있다.
- ★★★ **`(1)`\~`(4)` 는 전부 에러**이고 `cc exit=1` 이다.

  | 무엇 | gcc | clang |
  |---|---|---|
  | `struct Hidden v;` | `storage size of 'v' isn't known` | `variable has incomplete type 'struct Hidden'` |
  | `struct Hidden a[3];` | `array type has incomplete element type` | `array has incomplete element type` |
  | `sizeof(struct Hidden)` | `invalid application of 'sizeof' to incomplete type` | `invalid application of 'sizeof' to an incomplete type` |
  | `p->x` | `invalid use of undefined type` | `incomplete definition of type 'struct Hidden'` |

- ★★ **네 가지가 막히는 이유는 하나다 — 「크기를 알아야 하는 일」이기 때문이다.**\
  변수·배열 원소는 **저장 공간을 잡아야** 하고, `sizeof` 는 **크기 자체**이며, `p->x` 는 **멤버가 몇 바이트 떨어져 있는지**를 알아야 한다.
- ★ **덧붙이는 것이 다르다.** clang 은 에러마다 `note: forward declaration of 'struct Hidden'` 으로 **3번 줄을 가리킨다.**\
  gcc 는 그 note 가 없는 대신 **`unused variable` 경고 2건**을 더 낸다 — 에러로 죽은 변수를 **여전히 「안 쓴 변수」로 센다.**\
  ★★ 그래서 **진단 줄 수로 두 컴파일러를 견주면 안 된다** — 줄 수는 다르고 **에러 건수는 둘 다 4** 다.
- ★ **실행 시간까지 새어 나가는 것은 없다.** 이 주제의 금지는 **전부 컴파일 시간에 드러난다.**

### 2. 경계는 왜 하필 거기인가 — **「크기를 쓰는 일」만 막힌다** ★★

**왜 그런가**

- ★★★ **포인터는 가리키는 대상의 크기를 몰라도 만들 수 있다.** 주소를 담는 상자의 크기는 대상과 무관하게 정해져 있다(이 환경에서 8바이트). 그래서 **불완전 타입을 가리키는 포인터는 언제나 완전한 타입**이다.
- ★★ **`struct Hidden *p;` 와 `struct Hidden a[3];` 를 가르는 것**은 「몇 바이트를 잡아야 하나」다.\
  포인터 변수는 **8바이트**를 잡으면 되지만, 배열은 **한 칸이 몇 바이트인지** 알아야 세 칸을 나란히 놓을 수 있다.
- ★★ 「**그 지점에서의 상태**」라는 말 — 불완전은 타입의 영구 성질이 아니다.\
  `struct S;` 다음 줄에 `struct S { int x; };` 가 오면 **그 줄부터 같은 타입이 완전하다.** 그래서 **한 파일 안에서도 위쪽은 불완전, 아래쪽은 완전**일 수 있다.
- ★ **불완전 타입을 만드는 방법은 세 가지**다.

  | 만드는 법 | 완성하는 법 |
  |---|---|
  | `struct S;`(태그만) | 같은 스코프에 `struct S { … };` 를 쓴다 |
  | `extern char msg[];`(크기 없는 배열) | 어딘가에 `char msg[6] = …;` 라는 **정의**가 있다 |
  | `void` | ★★ **없다** |

- ★★ **`void` 는 영원히 완성할 수 없다** — **완성할 문법 자체가 없기** 때문이다. `void { … }` 같은 것은 존재하지 않는다.\
  그래서 `void *` 는 「**무엇이든 가리키지만 역참조는 못 하는**」 포인터가 된다([19번 형제](../19-void-pointer-null-pointer-and-null/)가 정본).

### 3. 헤더에 이름만 두고 셋으로 나눠 빌드하면 — **성공한다 · `ctr_get = 15` · `sizeof(Counter *) = 8`** ★★★

**출력**

```text
===== gcc -c 로 따로 번역한 뒤 링크한다 (exit=0) =====
s25b.o      OK  (정의가 있는 쪽)
s25b_main.o OK  (이름만 아는 쪽)
링크 OK
ctr_get = 15
포인터 크기는 안다 : sizeof(Counter *) = 8
```

**왜 그런가**

- ★★★ **두 `.c` 가 따로 번역되고 링크된다.** `s25b_main.c` 는 `struct Counter` 의 멤버를 **한 글자도 모르는 채** 오브젝트 파일이 된다.
- **`ctr_get` 은 `15`** 다 — `ctr_new(5)` 로 `step = 5` 를 주고 `ctr_tick` 을 세 번 불렀다.
- ★★ **쓰는 쪽이 아는 크기는 `sizeof(Counter *)` = 8** 뿐이다. **포인터는 완전한 타입**이라는 (1)·(2)의 규칙이 실행으로 확인된 자리다.\
  ★ **`sizeof(Counter)` 는 못 묻는다**(4번이 그 에러다).
- ★★★ **`sizeof *c` 를 쓰는 곳은 `ctr_new` 한 군데**다. 크기를 아는 곳이 하나면 **그 한 곳만 고쳐 레이아웃을 바꿀 수 있다** — 쓰는 쪽은 **다시 컴파일할 필요조차 없다**(오브젝트 파일에 레이아웃이 없으니까).
- ★ **`ctr_free` 가 반드시 있어야 하는 이유** — 쓰는 쪽은 내부를 모르므로 **무엇을 해제해야 하는지 판단할 수 없다.**\
  내부에 또 다른 할당이 있을 수도 있다. **생성 함수를 내놓았으면 짝이 되는 해제 함수도 같이 내놓는다**(목록의 **38번 주제**).
- ★ **`struct` 를 안 써도 되는 이유** — 헤더의 `typedef struct Counter Counter;` 덕이다. **별칭은 불완전한 타입에도 붙는다**([6번 형제](../06-typedef-and-type-aliases/)).

### 4. 쓰는 쪽에서 값으로 품거나 스택에 놓으면 — **네 줄 다 에러 · `cc exit=1`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25c.c -o x (cc exit=1) =====
s25c.c:5:13: error: field ‘c’ has incomplete type
    5 |     Counter c;          /* (1) 값으로 품을 수 없다 */
      |             ^
s25c.c: In function ‘main’:
s25c.c:10:13: error: storage size of ‘local’ isn’t known
   10 |     Counter local;              /* (2) 스택에 못 놓는다 */
      |             ^~~~~
s25c.c:12:22: error: invalid use of incomplete typedef ‘Counter’
   12 |     printf("%ld\n", p->n);      /* (3) 멤버를 못 읽는다 */
      |                      ^~
s25c.c:13:28: error: invalid application of ‘sizeof’ to incomplete type ‘Counter’
   13 |     printf("%zu\n", sizeof *p); /* (4) 크기를 못 묻는다 */
      |                            ^
s25c.c:10:13: warning: unused variable ‘local’ [-Wunused-variable]
   10 |     Counter local;              /* (2) 스택에 못 놓는다 */
      |             ^~~~~
```

**왜 그런가**

- ★★ **네 에러의 원인이 하나다 — 「크기를 모른다」.**

  | 줄 | 진단 | 왜 |
  |---|---|---|
  | `Counter c;`(멤버) | `field 'c' has incomplete type` | 바깥 구조체의 크기를 계산할 수 없다 |
  | `Counter local;` | `storage size of 'local' isn't known` | 스택에서 몇 바이트를 비울지 모른다 |
  | `p->n` | `invalid use of incomplete typedef 'Counter'` | 멤버가 몇 바이트 떨어져 있는지 모른다 |
  | `sizeof *p` | `invalid application of 'sizeof' to incomplete type 'Counter'` | 크기 그 자체다 |

- ★ **진단이 별칭으로 부른다** — `struct Counter` 가 아니라 **`incomplete typedef 'Counter'`** 라고 적는다. 소스에 쓴 이름 그대로라 **원인 추적에 바로 쓸 수 있다.**
- ★★ **그래서 opaque 객체는 거의 언제나 할당 저장 기간에 놓인다.** 스택에 못 놓고 정적 변수로도 못 만드니\
  **생성 함수 안의 `malloc` 이 유일한 통로**가 된다([28번 형제](../28-choosing-among-four-storage-durations/)와 맞물리는 자리다).
- ★ **대가는 전부 컴파일 시간에 드러난다.** `cc exit=1` 이고 실행 시간으로 새어 나가는 것이 없다 — 이 주제가 **안전한 거래**인 이유다.

### 5. `sizeof(void)` 를 묻고 `void *` 에 1 을 더하면 — **`1` 이 나오고 `cc exit=0` · `-pedantic-errors` 라야 `1`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25d.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(void)  = 1
vp        = 0x7ffe7f3764f0
vp + 1    = 0x7ffe7f3764f1   <- 몇 바이트 갔나?
차이      = 1 바이트
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25d.c -o x (cc exit=0) =====
s25d.c: In function ‘main’:
s25d.c:5:44: warning: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    5 |     printf("sizeof(void)  = %zu\n", sizeof(void));
      |                                            ^~~~
s25d.c:10:65: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   10 |     printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
      |                                                                 ^
s25d.c:11:52: warning: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   11 |     printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
      |                                                    ^
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic-errors s25d.c -o x (cc exit=1) =====
s25d.c: In function ‘main’:
s25d.c:5:44: error: invalid application of ‘sizeof’ to a void type [-Wpointer-arith]
    5 |     printf("sizeof(void)  = %zu\n", sizeof(void));
      |                                            ^~~~
s25d.c:10:65: error: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   10 |     printf("vp + 1    = %p   <- 몇 바이트 갔나?\n", (void *)(vp + 1));
      |                                                                 ^
s25d.c:11:52: error: pointer of type ‘void *’ used in arithmetic [-Wpointer-arith]
   11 |     printf("차이      = %td 바이트\n", (char *)(vp + 1) - (char *)vp);
      |                                                    ^
```

**왜 그런가**

- ★★★ **컴파일된다. `cc exit=0` 이고 실행되어 `sizeof(void)` 가 `1` 을 답한다.**\
  표준에는 그런 값이 없다 — **gcc·clang 의 확장**이다. 그 확장 덕에 `void *` 산술이 `char *` 산술처럼 **1바이트씩** 움직여 `vp + 1` 과 `vp` 의 차가 **`1`** 이 된다.
- ★★★ **`-pedantic` → `-pedantic-errors` 로 바꾸면 바뀌는 것은 심각도뿐**이다.

  | | `-pedantic` | `-pedantic-errors` |
  |---|---|---|
  | 진단 건수 | 3건 | 3건 |
  | 진단 본문 | `invalid application of 'sizeof' to a void type` … | **같다** |
  | 플래그 이름 | `[-Wpointer-arith]` | **같다** |
  | 심각도 | `warning:` | **`error:`** |
  | **`cc exit`** | **0** | **1** |

- ★★★ **「`-pedantic` 을 붙였으니 표준으로 검증했다」가 여기서 깨진다.**\
  진단은 났는데 **빌드가 통과**하고 바이너리가 나온다. **경고 건수만 세는 빌드 스크립트는 이것을 「통과」로 기록한다.**\
  ★ 표준 준수를 **주장**하려면 `-pedantic`, **강제**하려면 `-pedantic-errors` 다.
- ★ **흔들리는 칸은 `%p` 두 줄**(ASLR)이고, **안 흔들리는 칸은 `sizeof(void) = 1` 과 두 주소의 차 `1`** 이다.\
  대조할 것은 주소가 아니라 「**차이가 1이다**」라는 성질이다.
- ★ `void` 는 **완성될 수 없는 불완전 타입**이라 표준에서는 `sizeof` 도 산술도 정의되지 않는다. 이식하려면 **`char *`·`unsigned char *` 로 캐스트**한다.

### 6. 두 `.c` 가 같은 태그를 다르게 정의하면 — **네 벌 전부 침묵 · 값까지 그럴듯하다** ★★★ 본체

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25e.c s25e_main.c -o x ; ./x (cc exit=0 · run exit=0) =====
저쪽 함수로 읽으면 cget = 6
이쪽 정의로 읽으면 tag = 6 · n = 3
```

```text
===== 네 벌로 던져 본다 — 아무도 말하지 않는다 (exit=0) =====
gcc   none                         cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
clang none                         cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
gcc   -flto                        cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
gcc   -fsanitize=address,undefined cc exit=0 경고 0건 | 저쪽 함수로 읽으면 cget = 6
```

**왜 그런가**

- ★★★ **컴파일되고 링크되고 실행된다.** 네 벌 전부 **`cc exit=0` · 경고 0건 · `run exit=0`** 이다.

  | 벌 | 경고 | `cc exit` | 출력 |
  |---|---|---|---|
  | gcc(플래그 없음) | 0건 | 0 | `cget = 6` |
  | clang(플래그 없음) | 0건 | 0 | `cget = 6` |
  | gcc `-flto` | 0건 | 0 | `cget = 6` |
  | gcc `-fsanitize=address,undefined` | 0건 | 0 | `cget = 6` |

- ★★ **숫자가 어디서 왔나** — `s25e.c` 는 `{ long n; long step; }` 로 16바이트를 잡고 `n = 6`(= 3 × 2회), `step = 3` 을 담았다.\
  `s25e_main.c` 는 같은 16바이트를 `{ char tag; long n; }` 로 읽는다.

  ```text
     실제 메모리 (s25e.c 가 만든 것)
     +----------------+----------------+
     |    n = 6 (8)   |  step = 3 (8)  |
     +----------------+----------------+
      0                8

     s25e_main.c 가 읽는 법 — { char tag; long n; }
     +--+------------+----------------+
     |t |   패딩 7    |    n (8)       |
     +--+------------+----------------+
      0  1            8
      ^ n 의 최하위 바이트 = 6        ^ 실은 step = 3

     -> tag = 6 · n = 3
  ```

  ★★★ **둘 다 실제로 쓰인 수**다. 「이상한 값이 나왔네」로도 안 걸린다.
- ★★★ **아무도 안 잡는 원리상의 이유** — **구조체 레이아웃은 오브젝트 파일에 실리지 않는다.**\
  링커가 맞추는 것은 **심볼 이름**뿐이고, ASan·UBSan 이 볼 것도 없다 — 메모리 접근은 **할당된 16바이트 안**이고 산술 문제도 아니다.\
  `-flto` 도 **시그니처만** 보는데 여기서는 양쪽 시그니처가 **글자까지 같다**(7번 참조).
- ★★★ **막는 방법은 도구가 아니라 규율이다** — **정의를 한 곳에만 둔다.**\
  헤더를 `#include` 하면 정의가 하나뿐이라 이 사고가 원리상 안 난다. 그리고 **opaque 로 만들면 헤더에 정의가 아예 없어** 베낄 도면 자체가 사라진다.\
  ★ **이것이 opaque struct 의 두 번째 값**이다 — 숨기는 것보다 **못 베끼게 하는 것**이 크다.

### 7. `-flto` 는 무엇을 보고 무엇을 못 보나 — **시그니처는 보고 구조체 정의는 못 본다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25e.c s25f_main.c -o x (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -flto s25e.c s25f_main.c -o x (cc exit=0) =====
s25f_main.c:3:6: warning: type of ‘ctick’ does not match original declaration [-Wlto-type-mismatch]
    3 | void ctick(int x);          /* ★ 이번에는 ★ 시그니처 ★ 가 어긋난다 */
      |      ^
s25e.c:6:6: note: type mismatch in parameter 1
    6 | void ctick(struct Counter *c)   { c->n += c->step; }
      |      ^
s25e.c:6:6: note: ‘ctick’ was previously declared here
s25e.c:6:6: note: code may be misoptimized unless ‘-fno-strict-aliasing’ is used
```

**왜 그런가**

- ★★ **`-flto` 없이는 아무 말도 없다** — 블록이 배너뿐이다. 각 번역 단위는 **저쪽 정의를 볼 방법이 없고**, 링커는 이름만 맞춘다.
- ★★★ **`-flto` 를 켜면 `[-Wlto-type-mismatch]` 가 1건 나온다.**\
  `type of 'ctick' does not match original declaration` + `note: type mismatch in parameter 1` + `note: 'ctick' was previously declared here` + `note: code may be misoptimized unless '-fno-strict-aliasing' is used`.
- ★★★ **그런데 `cc exit=0`** 이다. 「misoptimized 될 수 있다」고까지 적어 놓고 **빌드는 성공한다.** 5번과 **같은 집안**이다.
- ★★★ **6번이 안 잡히는 이유** — 6번에서는 **양쪽 시그니처가 글자까지 같았다**(`void ctick(struct Counter *)`).\
  다른 것은 **그 이름이 가리키는 구조체의 내용**뿐인데, LTO 의 타입 대조는 **이름이 같으면 통과**시킨다.\
  ★ 즉 **`-flto` 가 보는 것은 「함수의 모양」이고 「타입의 속」이 아니다.**
- ★★★ **그래서 이 주제의 「네 번째 창」은 「없다」가 답**이다.\
  다른 주제들은 세 창이 놓친 것을 잡는 네 번째 창을 찾았지만, 여기서는 **후보였던 `-flto` 마저 못 본다.**\
  ★ 결론은 「**창을 찾지 말고 그 상태를 못 만들게 하라**」이고, 그 장치가 **opaque struct** 다.

### 8. 함수 선언의 괄호 안에서 `struct` 가 처음 나오면 — **경고 1건 + 에러 1건 · `cc exit=1`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25g.c -o x (cc exit=1) =====
s25g.c:3:18: warning: ‘struct Point’ declared inside parameter list will not be visible outside of this definition or declaration
    3 | void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */
      |                  ^~~~~
s25g.c:7:6: error: conflicting types for ‘show’; have ‘void(struct Point *)’
    7 | void show(struct Point *p) { printf("(%d,%d)\n", p->x, p->y); }
      |      ^~~~
s25g.c:3:6: note: previous declaration of ‘show’ with type ‘void(struct Point *)’
    3 | void show(struct Point *p);         /* ★ struct Point 가 여기서 처음 나온다 */
      |      ^~~~
```

**왜 그런가**

- ★★★ **에러의 두 줄이 글자까지 같다.**\
  `have 'void(struct Point *)'` 와 `previous declaration of 'show' with type 'void(struct Point *)'` — **눈으로는 왜 충돌인지 알 수 없다.**
- ★★★ **이유는 두 `struct Point` 가 서로 다른 타입이기 때문**이다.

  ```text
     void show(struct Point *p);      <- ★ 이 괄호 안에서 struct Point 태그가 태어난다
                                         스코프가 ★ 괄호 끝에서 죽는다

     struct Point { int x, y; };      <- ★ 파일 스코프의 ★ 다른 struct Point

     void show(struct Point *p) {…}   <- 파일 스코프 쪽을 가리킨다
                                         그래서 선언과 정의가 다른 타입을 받는다
  ```

- ★★ 이유를 알려 주는 줄은 「**경고**」다 — `'struct Point' declared inside parameter list will not be visible outside of this definition or declaration`.\
  ★ **경고가 원인이고 에러가 증상**이다. 진단은 **위에서부터** 읽어야 한다.
- ★ **고치는 법은 한 줄** — `struct Point;` 를 선언 위에 두거나, 정의 자체를 선언보다 위로 올린다. 그러면 괄호 안의 이름이 **이미 있는 태그**를 가리킨다.
- ★ **조용히 지나갈 수 없다.** 정의를 쓰는 순간 `cc exit=1` 로 멈춘다 — **6번과 정반대**의 성격이다.

### 9. 크기를 안 적은 `extern` 배열 — **읽기·인덱싱은 되고 `sizeof` 만 에러** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25h_main.c s25h.c -o x (cc exit=1) =====
s25h_main.c: In function ‘main’:
s25h_main.c:8:36: error: invalid application of ‘sizeof’ to incomplete type ‘char[]’
    8 |     printf("sizeof= %zu\n", sizeof msg);   /* ★ 크기는 못 묻는다 */
      |                                    ^~~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25h_ok.c s25h.c -o x ; ./x (cc exit=0 · run exit=0) =====
msg    = hello
msg[1] = e
★ sizeof msg 는 이 번역 단위에서 쓸 수 없다
```

**왜 그런가**

- ★★ **에러는 `sizeof msg` 한 줄뿐**이고 `cc exit=1` 이다. 진단이 타입을 **`char[]`** 라고 적는다 — 「원소 타입은 아는데 개수를 모른다」가 그대로 보인다.
- ★★ **읽기와 인덱싱은 된다.** 둘 다 **포인터로 감쇠**해 크기를 쓰지 않기 때문이다([16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본).\
  `msg` 는 `&msg[0]` 이 되고 `msg[1]` 은 `*(msg + 1)` 이다 — **원소 크기(1)만 알면 되고 전체 크기는 필요 없다.**
- ★★ **무엇이 가르나 — 그 번역 단위에 정의가 보이느냐**다.\
  `s25h.c` 에는 `char msg[6] = "hello";` 가 있어 크기를 알고, `s25h_main.c` 에는 `extern char msg[];` 뿐이라 끝까지 모른다.\
  ★ **「크기를 아느냐」는 객체의 성질이 아니라 번역 단위의 상태**다.
- ★★ **헤더에 `extern char msg[6];` 라고 적으면** — `sizeof` 를 얻고, 대신 **크기를 바꿀 때 양쪽을 같이 고쳐야** 한다.\
  안 고치면 **6번과 같은 무음 사고**가 난다(선언과 정의의 불일치를 아무도 안 본다). **둘 중 하나를 고르는 자리**다.

### 10. 서로를 가리키는 두 구조체 — **포인터라서 풀린다 · `typedef` 반복은 C11 부터** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s25i.c -o x ; ./x (cc exit=0 · run exit=0) =====
a.v=1 -> w=7 -> v=2
sizeof(Node)=16 sizeof(struct Edge)=16
```

```text
===== gcc -std=c99 -Wall -Wextra -pedantic s25i.c -o x (cc exit=0) =====
s25i.c:4:21: warning: redefinition of typedef ‘Node’ [-Wpedantic]
    4 | typedef struct Node Node;           /* ② 같은 typedef 를 또 쓴다 — C11 부터 허용 */
      |                     ^~~~
s25i.c:3:21: note: previous declaration of ‘Node’ with type ‘Node’
    3 | typedef struct Node Node;           /* ① 불완전한 채로 별칭을 만든다 */
      |                     ^~~~
```

**왜 그런가**

- ★★★ **`struct Edge *out` 은 크기를 안 쓴다.** `Edge` 가 불완전해도 **포인터는 완전한 타입**이므로 `Node` 의 크기를 계산할 수 있다.\
  그래서 `struct Edge;` **한 줄**이 순환을 푼다.
- ★★★ **값으로 품으면 안 풀린다.** `struct Node { struct Edge e; };` 와 `struct Edge { struct Node n; };` 는\
  **`Node` 의 크기가 `Edge` 의 크기를 요구하고 그 반대도 마찬가지**라 어느 쪽도 계산할 수 없다 — 원리상 무한이다.
- ★★ **같은 `typedef` 를 두 번 쓰는 것은 C11 부터**다.\
  `-std=c99 -pedantic` 에서는 `redefinition of typedef 'Node' [-Wpedantic]` + `note: previous declaration` 이 나오고 **`cc exit=0`** 이다(5번과 같은 모양).\
  ★ 이 성질이 값을 내는 자리는 **두 헤더가 같은 `typedef` 를 들여올 때**다 — C11 이후로는 문제가 없다.
- ★ **`sizeof(Node) = 16`** 은 `int v`(4) + **패딩 4** + `struct Edge *out`(8) 이다. `sizeof(struct Edge) = 16` 은 `Node *to`(8) + `int w`(4) + **꼬리 패딩 4** 다.\
  ★ 패딩 규칙은 [22번 형제](../22-struct-padding-and-alignment/), 재는 도구는 [8번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.

### 11. 다섯 층과 무게중심 — **표준이 본체 · UB 는 한 자리 · 「exit 0 인데 ill-formed」가 세 군데** ★★★

**왜 그런가**

| 층 | 이 주제에서 | 근거 |
|---|---|---|
| ★★★ **표준 (본체)** | 불완전 타입 세 가지 · **변수·배열 원소·구조체 멤버·`sizeof`·멤버 접근이 전부 에러**인 것 · **포인터는 완전**한 것 · 정의가 오면 **그 자리부터 완전**해지는 것 · **매개변수 목록 안의 태그가 괄호 안에서만 사는 것** · 상호 참조가 **포인터로만** 풀리는 것 · `typedef` 반복이 **C11 부터**인 것 | gcc·clang 에러 전문 4벌(`cc exit=1`) · `sizeof(Counter *)` = 8 · 3파일 분할 빌드 성공 · `conflicting types` 두 줄이 **글자까지 같은** 진단 |
| **조건부 표준** | ★ **해당 없음** — 매크로로 켜고 꺼지는 보장이 없다 | — |
| ★ **구현 정의 (얇다)** | 포인터 크기(8) · 진단 문구와 플래그 이름 · **`-flto` 가 무엇까지 대조하는가** | `sizeof(Counter *)` = 8 · `[-Wlto-type-mismatch]` 가 **시그니처만** 잡음 |
| **미명시** | ★★ **없다.** 여기서 값이 갈리는 자리는 **미명시가 아니라 UB** 다 | — |
| ★★ **UB (자리는 하나)** | ★★★ **두 번역 단위가 같은 태그를 다르게 정의하고 그 포인터를 주고받는 것** | ★★ **네 벌** 전부 `cc exit=0` · 경고 0건 · `run exit=0` · 값은 `tag = 6 · n = 3` |

- ★★ 비어 있는 칸은 「**조건부 표준」과 「미명시**」다. `void *` 산술·`sizeof(void)` 는 **UB 가 아니라 확장**이라 UB 칸에 넣지 않는다(구현이 정의한다).
- ★★★ 가장 두꺼운 칸은 「**표준**」이고, 이것이 [24번 형제](../24-bit-fields/)와 **정반대**다.\
  거기서는 「폭만 내가 정하고 자리·방향·단위·부호는 구현이 정한다」였는데, 여기서는 **무엇이 되고 안 되는지가 전부 표준에 적혀 있고 두 컴파일러가 짝을 이룬다.**
- ★★ **도구가 침묵하는 자리**

  | 층 | 침묵하는 자리 |
  |---|---|
  | 표준 | ★ 거의 다 본다. 다만 **`conflicting types` 의 원인은 안 알려 준다** — 두 줄의 글자가 같아 **그 위의 경고를 읽어야** 안다 |
  | 조건부 표준 | 해당 없음 |
  | 구현 정의 | ★★ **`-flto` 가 무엇을 대조하는지 말해 주지 않는다** — 시그니처는 잡고 구조체 내용은 안 잡는데, **던져 봐야** 안다 |
  | 미명시 | 해당 없음 |
  | UB | ★★★ **두 정의를 보는 도구가 없다.** 레이아웃이 오브젝트 파일에 없어 링커가 볼 것이 없고, ASan·UBSan 은 **할당 범위 안의 접근**이라 원리상 무력하다 |

- ★★★ **「종료 코드가 0인데 ill-formed」는 세 군데**다.

  | # | 어디 | 무엇이 났나 | `cc exit` |
  |---|---|---|---|
  | ① | `sizeof(void)`·`void *` 산술 | `warning` 3건 `[-Wpointer-arith]` | **0** (`-pedantic-errors` 라야 1) |
  | ② | `-flto` 시그니처 불일치 | `warning` 1건 `[-Wlto-type-mismatch]` + 「misoptimized 될 수 있다」 | **0** |
  | ③ | `-std=c99` 의 `typedef` 반복 | `warning` 1건 `[-Wpedantic]` | **0** |

  ★ 세 자리 전부 **경고 건수만 세는 빌드는 「통과」로 기록**한다.

### 12. 경계 — 어디까지가 이 주제인가 ★

| 무엇 | 정본 |
|---|---|
| **`void *` 를 어떻게 쓰나** · `NULL`·`nullptr` | [19번 형제](../19-void-pointer-null-pointer-and-null/) |
| **`sizeof`·`_Alignof`·`offsetof` 라는 도구** | [8번 형제](../08-sizeof-alignment-and-offsetof/) |
| **구조체 선언·초기화·지정 초기자** | [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) |
| **`typedef` 가 새 타입을 만들지 않는 것** | [6번 형제](../06-typedef-and-type-aliases/) |
| **배열이 포인터로 감쇠하는 규칙** | [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
| **패딩·정렬** | [22번 형제](../22-struct-padding-and-alignment/) |
| **무엇을 헤더에 두나 · include guard** | 목록의 **44번 주제** |
| **`undefined reference`·`multiple definition` 읽기** | 목록의 **45번 주제** |
| **`malloc`/`free` 의 계약과 실패 처리** | 목록의 **37번 주제** |
| **`_new`/`_free` 짝을 시그니처로 표현하기** | 목록의 **38번 주제** |
| **`enum` 의 선언·상수 규칙** | [7번 형제](../07-enum-and-enumeration-constants/) |

- ★ **이 주제가 끝까지 책임지는 것 셋**
  - ★★★ **불완전 타입으로 무엇이 막히고 왜 거기까지인가** — 「크기를 쓰는 일」 하나로 묶인다.
  - ★★★ **두 정의를 아무 도구도 안 본다는 것**과, 그래서 opaque struct 가 숨김 이전에 「**못 베끼게 하는 장치**」라는 것.
  - ★★ **`-pedantic` 과 `-pedantic-errors` 가 종료 코드에서 갈린다는 것** — 「exit 0 인데 ill-formed」 세 자리.
- ★★ **C++ 에서 한 칸 좁아지는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) 쪽이다.\
  C 에서는 헤더에 **포인터만** 두면 끝인데, **C++ 의 `std::unique_ptr<Counter>` 는 소멸자를 만드는 자리에서 완전한 타입을 요구**한다.\
  그래서 소멸자를 헤더에 두면 컴파일이 안 되고 `.cpp` 로 내려야 한다.\
  ★ 그 대신 C++ 에서는 `struct` 없이 **`Counter` 라고만** 써도 된다 — 클래스 이름이 곧 타입 이름이다.\
  ★ **이 문서는 C++ 쪽을 던지지 않았다**(규칙 진술만 하고 실측하지 않았다).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s25a.c` (25-a) | 불완전 타입으로 **네 가지가 에러**(`cc exit=1`) · 포인터 선언·매개변수·반환은 **통과** · clang 은 `note: forward declaration` 을 매번 붙이고 gcc 는 `unused variable` 2건을 더 낸다 | gcc 1벌 · clang 1벌 |
| `s25b.h`·`s25b.c`·`s25b_main.c` (25-b) | `gcc -c` 분할 번역 + 링크 **성공** · `ctr_get = 15` · **`sizeof(Counter *) = 8`** | gcc 1벌(3단계) |
| `s25c.c` (25-c) | 값 멤버·스택 변수·멤버 접근·`sizeof` **네 가지가 에러** · 진단이 **`incomplete typedef 'Counter'`** 로 별칭을 부른다 | gcc 1벌 |
| `s25d.c` (25-d) | **`sizeof(void) = 1`** · `void *` 산술이 **1바이트** · `-pedantic` 에서 **경고 3건 · `cc exit=0`** · `-pedantic-errors` 에서 **에러 3건 · `cc exit=1`**(본문·플래그 이름은 동일) | gcc 3벌(실행·진단·`-pedantic-errors`) |
| `s25e.c`·`s25e_main.c` (25-e) | 두 정의 불일치가 **네 벌 전부 침묵** — `cc exit=0` · 경고 0건 · `run exit=0` · `cget = 6` · `tag = 6 · n = 3` | ★★ **4벌**(gcc · clang · `-flto` · ASan+UBSan) |
| `s25f_main.c` (25-f) | 시그니처 불일치는 `-flto` 가 **잡는다**(`[-Wlto-type-mismatch]` 1건) — 그런데 **`cc exit=0`** · `-flto` 없이는 **침묵** | gcc 2벌(`-flto` 유·무) |
| `s25g.c` (25-g) | `declared inside parameter list` **경고** + `conflicting types` **에러**(두 줄의 타입 표기가 **글자까지 같다**) · `cc exit=1` | gcc 1벌 |
| `s25h.c`·`s25h_main.c`·`s25h_ok.c` (25-h) | `sizeof msg` 만 **에러**(`char[]`) · 읽기·인덱싱은 **성공**(`hello` · `e`) | gcc 2벌(에러·성공) |
| `s25i.c` (25-i) | 상호 참조가 **포인터로 풀린다** · `sizeof(Node) = 16` · `sizeof(struct Edge) = 16` · `-std=c99 -pedantic` 에서 `redefinition of typedef` **경고 · `cc exit=0`** | gcc 2벌(c17 실행 · c99 진단) |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- ★★ **`sizeof(void)` 가 `1` 인 것**과 **`void *` 산술이 되는 것** — gcc·clang 의 **확장**이다. 표준에는 없다.
- ★★ **`-flto` 가 시그니처를 대조해 주는 것** — gcc 의 기능이고, **무엇까지 보는지도 구현의 선택**이다.
- ★ **포인터 크기가 8인 것** · **`sizeof(Node)` 가 16인 것**(패딩 규칙이 걸린다).
- ★ **진단 문구와 플래그 이름 전부** — 버전이 오르면 문구 대조가 깨진다.
- ★ **6번에서 나온 `tag = 6 · n = 3`** — 이 ABI 의 레이아웃에 달렸다. ★ **결론은 「값」이 아니라 「아무도 안 본다」는 사실**이다.

**불완전 타입으로 무엇이 막히는가 · 포인터가 완전한 타입인 것 · 매개변수 목록 태그의 스코프 · 상호 참조가 포인터로만 풀리는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `enum E;` 만 쓰는 **불완전 `enum`**(C23 이전 표준 밖) · **`void *` 핸들**로 내부를 숨기는 다른 관용구 ·\
  **불완전 타입을 값으로 반환하는 함수 선언** · **`-fsanitize=cfi`·`-Wodr`** 가 6번을 잡는지 ·\
  **`-g` 로 넣은 DWARF 를 대조하는 도구**가 6번을 잡는지 · **opaque 로 만들었을 때의 호출 비용**(재지 않았다) ·\
  **C++ 에서의 pImpl 과 `std::unique_ptr` 의 완전 타입 요구**(규칙만 적고 던지지 않았다).
- ★ **못 잰 것** — **6번의 사고가 실제로 얼마나 자주 나는가.**\
  이 문서가 보인 것은 「**나면 아무도 안 본다**」이지 「**얼마나 자주 나나**」가 아니다.\
  빈도는 **코드베이스의 헤더 규율에 달린 것**이라 이 실험 밖의 일이다 — 「안 돌려 본 것」이 아니라 「**측정 방법이 전제를 요구해 잴 수 없는 것**」이라 따로 적는다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **`-flto` 가 구조체 정의까지 보게 됐는지**(지금은 시그니처만 본다). 이 편의 결론이 바뀌는 유일한 자리다.
- ★★ **`sizeof(void)`·`void *` 산술을 gcc·clang 이 계속 확장으로 두는지**, 그리고 **`-pedantic` 의 심각도가 그대로인지**.
- ★ **진단 문구 전부** — 특히 `conflicting types` 의 타입 표기 방식(8번의 「글자가 같다」가 그것에 달렸다).
- ★ **clang 이 `note: forward declaration` 을 계속 붙이는지**(1번의 비교가 그것에 달렸다).
- **불완전 타입의 규칙 자체는 다시 돌릴 필요가 없다** — C89 이후 바뀐 적이 없다.
