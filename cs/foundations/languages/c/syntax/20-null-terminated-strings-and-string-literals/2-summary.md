# c/syntax/20 — 널 종단 문자열과 문자열 리터럴: 「**문자열은 타입이 아니라 0 하나로 맺는 약속이다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **이 문서는 외부 문서를 새로 열지 않았다.** 규칙 진술의 출처는
> [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 연 목록과 같고(WG14 공개 작업 초안 목록 · cppreference · gcc/clang 진단 문서),\
> **이 문서의 모든 값·바이트·진단·종료 코드는 실행으로 접지했다.** ★ **표준 조항 번호는 인용하지 않는다.**
> **실행 검증** — 모든 출력·진단·sanitizer 리포트는 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과\
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 작업 디렉터리는 `/tmp/c17b/20`, 소스는 `ex.c`\~`ex7.c` 다 — sanitizer 출력에 경로가 박히기 때문이다.\
> ★★ **죽는 프로그램(`ex2.c`·`ex6.c`)에는 `setvbuf(stdout, NULL, _IONBF, 0)` 를 넣었다** —\
> 그러지 않으면 **버퍼에 남은 `printf` 가 통째로 사라져** 「어디까지 찍혔나」가 재현되지 않는다.\
> ASan 리포트는 `| sed -n '1,/^SUMMARY/p'` 로 잘랐다(자른 명령을 배너에 적어 두었다).
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 의 주소 · `pc`/`bp`/`sp` · PID · `BuildId` | ★★ **바이트 격자**(`61 62 63 00` · `61 62 00 63 64 00`) |
> | `objdump -h` 의 섹션 주소·오프셋 | ★ 섹션 **이름**(`.rodata` ↔ `.data`)과 그 대비 |
> | 리터럴의 실제 번지 | ★★ **공유/따로 판정**(`a == b` · `e == d+6`)과 그것이 **벌마다 갈린다는 사실** |
> | — | ★★ **종료 코드**(`cc exit` · `run exit=0`/`139`/`1`) · 진단 본문 · **플래그 이름** · `sizeof`/`strlen` 값 |
>
> **버전** — 널 종단 관례와 「**리터럴을 고치면 UB**」다 는 **C89 이후 바뀐 적이 없다.**\
> ★ 리터럴의 타입이 `const char[]` 가 되는 것은 **C++ 이야기**이고 **C 에서는 지금도 `char[]`** 다 — 그래서 경고가 기본으로 안 난다.\
> ★ `-std=` 를 바꿔도 이 주제의 결론은 안 바뀐다. 이 문서는 `-std=c17` 로 고정했다.
> ★★ **경계** — `strlen`·`strcpy`·`strcat`·`strncpy` 같은 **`<string.h>` 함수들의 계약 전반**은 목록의 **49번 주제**가 정본이다.\
> 여기서는 **널 종단이라는 약속 자체**와 **리터럴이 어디 사는가**만 본다(`strncpy` 는 「**널을 안 붙일 수 있다**」는 한 가지만).\
> ★ **배열이 포인터로 감쇠하는 규칙**과 `char s[] = "hi"` ↔ `char *q = "hi"` 의 `sizeof` 대비는\
> [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다 — 여기서는 **결론만 되짚고** 「**왜 복사인가·고치면 무엇이 일어나나**」를 판다.\
> ★ **배열 밖 접근이 무엇을 만드나**는 목록의 **56번 주제**, **`sizeof` 일반 규칙**은 [08번 형제](../08-sizeof-alignment-and-offsetof/)가 정본이다.
> 선행 — [16번 형제](../16-array-pointer-decay-and-function-parameters/) · [15번 형제](../15-pointer-arithmetic-and-indexing/) · [14번 형제](../14-pointers-address-dereference-and-pointer-types/).

## 한눈에 — 쉽게 말하면

**C 에는 「문자열」이라는 타입이 없다.** 있는 것은 **`char` 배열**과 **「끝에 0 을 하나 둔다」는 약속**뿐이다.

기차를 세워 둔다고 하자.\
칸이 몇 개인지는 **차량 기지 장부**(`sizeof`)에 적혀 있다.\
그런데 승객은 장부를 못 본다 — 대신 **빨간 깃발이 꽂힌 칸**을 보고 「여기가 끝이구나」 한다(`strlen`).\
★ **깃발을 안 꽂으면** 승객은 **다음 기차까지 걸어 들어간다.** 그래도 대개는 아무 일이 안 난다 — **그게 이 주제의 무서운 점**이다.

그리고 **「abc」라고 적힌 안내판**은 역 벽에 **볼트로 박혀 있다**(문자열 리터럴).\
그 판을 떼어다 글자를 고치려 들면 **역이 무너진다**(UB) — 고치고 싶으면 **베껴 적은 종이**를 쓴다(`char s[] = "abc"`).

| 비유 | 실체 | 층 |
|---|---|---|
| 기차 칸 수가 적힌 장부 | `sizeof arr` — 배열 크기, **컴파일 시간** | **표준** |
| 빨간 깃발이 꽂힌 칸 | 널 종단자 `'\0'` | **표준** |
| 깃발까지 세어 보는 것 | `strlen` — **실행 시간**에 첫 0 까지 | **표준** |
| 벽에 볼트로 박힌 안내판 | 문자열 리터럴 — **정적 저장 기간** | **표준** |
| 안내판을 베껴 적은 종이 | `char s[] = "abc"` — ★ **복사본** | **표준** |
| 안내판을 손가락으로 가리키기 | `char *p = "abc"` — 가리킬 뿐 | **표준** |
| 판을 어느 벽에 박았나 | `.rodata` 섹션 · 쓰기 금지 매핑 | **구현 정의** |
| 같은 문구의 판이 하나인가 둘인가 | ★★ **리터럴 공유 여부** | ★★ **미명시** |
| 박힌 판의 글자를 고치는 것 | `p[0] = 'A'` | ★★★ **UB (본체)** |
| 깃발 없는 기차를 끝까지 걷는 것 | 널 없는 배열에 `strlen`/`%s` | ★★★ **UB** |

```text
   문자열 "abc" 의 정체 — ★ 네 칸이다

        [0]  [1]  [2]  [3]
       +----+----+----+----+
       | 61 | 62 | 63 | 00 |      <- 바이트 (16진)
       +----+----+----+----+
       | 'a'| 'b'| 'c'| \0 |      <- 글자
       +----+----+----+----+
         |              |
         |<-- strlen=3 -->|        strlen : 첫 0 을 만날 때까지 센다 (0 은 안 센다)
       |<---- sizeof=4 ---->|      sizeof : 배열 전체 (0 까지 포함)

   ★ 이 격자에 "문자열 타입" 은 없다. char 네 칸과 ★ 마지막 00 하나가 전부다.
```

- ★★★ **이 주제는 UB 가 본체**다 — **리터럴 수정**이 그것이고, 던져 보면 **`run exit=139`** 로 죽는다.\
  [16번 형제](../16-array-pointer-decay-and-function-parameters/)·[15번 형제](../15-pointer-arithmetic-and-indexing/)와 같은 모양이지만 **UB 의 성격이 다르다** —\
  15·16번의 UB 는 **길이를 잃어서** 나는 것이고, 여기 UB 는 **쓰면 안 되는 것에 쓴 것**이다.
- ★★ 두 번째 무게중심은 「**미명시**」다. [16번 형제](../16-array-pointer-decay-and-function-parameters/)에서는 그 칸이 비어 있었는데,\
  여기서는 **리터럴 공유 여부**가 들어가고 **다섯 벌을 돌려야 갈린다**(한 벌만 보면 반대 결론이 난다).
- ★★★ 이 주제의 네 번째 창은 「**바이트 격자를 직접 찍는 것**」이다.\
  `%s` 로 찍으면 **셋 다 `abc`** 로 보인다 — **널이 있는 것·없는 것·중간에 있는 것**이 화면에서 구분되지 않는다.

> **널 종단(null-terminated)** — 문자열의 끝을 **값 0 인 바이트 하나**로 표시하는 관례.\
> 예: `"abc"` 는 `61 62 63 00` 네 바이트이고, 길이 정보는 **어디에도 따로 없다.**

> **문자열 리터럴(string literal)** — 소스에 `"abc"` 라고 쓴 것. **`char` 배열**이고 **정적 저장 기간**을 가진다.\
> 예: `char *p = "abc";` 에서 `p` 는 프로그램이 끝날 때까지 살아 있는 배열을 가리킨다.

> **정적 저장 기간(static storage duration)** — 프로그램 시작부터 끝까지 살아 있는 것.\
> 예: 함수 안에서 `return "hello";` 를 해도 **댕글링이 아니다** — 리터럴은 그 함수와 함께 사라지지 않는다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **문자열은 타입인가 관례인가** — `char arr[] = "abc"` 와 손으로 쓴 `{'a','b','c','\0'}` 의 바이트를 대 본다.
2. ★★★ **`char *p = "abc"` 의 글자를 고치면 무슨 일이 나나** — 그리고 **왜 `char s[] = "abc"` 는 고쳐지나.**
3. ★★ **널이 없으면 무엇이 일어나나** — 그리고 **왜 아무도 말해 주지 않나.**

## 동작 방식

### (1) ★★★ 문자열은 타입이 아니라 관례다 — 바이트를 대 본다

**언제 쓰나** — 「`char[]` 와 문자열은 다른 것 아닌가」라고 생각했을 때. **바이트를 찍으면 끝난다.**

```c
/* ex.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char arr[] = "abc";          /* 배열 — 복사본이 만들어진다 */
    char *lit  = "abc";          /* 포인터 — 리터럴을 가리킨다 */
    char raw[4] = {'a', 'b', 'c', '\0'};   /* 손으로 쓴 같은 것 */

    printf("sizeof arr = %zu · strlen(arr) = %zu\n", sizeof arr, strlen(arr));
    printf("sizeof lit = %zu · strlen(lit) = %zu   (★ 포인터 크기다)\n", sizeof lit, strlen(lit));
    printf("sizeof raw = %zu · strlen(raw) = %zu\n", sizeof raw, strlen(raw));
    printf("arr 과 raw 의 바이트가 같은가 : memcmp = %d\n", memcmp(arr, raw, 4));

    printf("\n바이트를 직접 본다\n");
    for (size_t k = 0; k < sizeof arr; k++)
        printf("  arr[%zu] = 0x%02x %s\n", k, (unsigned char)arr[k],
               arr[k] ? "" : "<- 널 종단자");

    printf("\n널이 중간에 있으면 — 「길이」가 둘로 갈린다\n");
    char mid[] = "ab\0cd";
    printf("  sizeof mid = %zu · strlen(mid) = %zu\n", sizeof mid, strlen(mid));
    printf("  바이트 : ");
    for (size_t k = 0; k < sizeof mid; k++) printf("%02x ", (unsigned char)mid[k]);
    printf("\n");
    printf("  printf(\"%%s\") 로 찍으면 : [%s]   <- 첫 널에서 멈춘다\n", mid);
    printf("  여섯 바이트를 눈에 보이게 : [");
    for (size_t k = 0; k < sizeof mid; k++)
        printf("%s", mid[k] ? (char[2]){mid[k], 0} : "\\0");
    printf("]\n");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof arr = 4 · strlen(arr) = 3
sizeof lit = 8 · strlen(lit) = 3   (★ 포인터 크기다)
sizeof raw = 4 · strlen(raw) = 3
arr 과 raw 의 바이트가 같은가 : memcmp = 0

바이트를 직접 본다
  arr[0] = 0x61 
  arr[1] = 0x62 
  arr[2] = 0x63 
  arr[3] = 0x00 <- 널 종단자

널이 중간에 있으면 — 「길이」가 둘로 갈린다
  sizeof mid = 6 · strlen(mid) = 2
  바이트 : 61 62 00 63 64 00 
  printf("%s") 로 찍으면 : [ab]   <- 첫 널에서 멈춘다
  여섯 바이트를 눈에 보이게 : [ab\0cd\0]
```

```text
   ★ 리터럴로 만든 배열 과 ★ 손으로 쓴 배열 — 나란히 놓으면

   char arr[] = "abc";            char raw[4] = {'a','b','c','\0'};
   +----+----+----+----+          +----+----+----+----+
   | 61 | 62 | 63 | 00 |          | 61 | 62 | 63 | 00 |
   +----+----+----+----+          +----+----+----+----+
     sizeof arr = 4                 sizeof raw = 4
     strlen(arr) = 3                strlen(raw) = 3

              memcmp(arr, raw, 4) = 0     <- ★ 네 바이트가 한 글자도 다르지 않다

   ★ 그래서 "문자열" 은 타입이 아니다. char 배열 + 끝의 00 하나 = 그것이 전부다.
```

```text
   ★ 널이 중간에 있으면 — 「길이」라는 낱말이 둘로 갈린다

   char mid[] = "ab\0cd";

        [0]  [1]  [2]  [3]  [4]  [5]
       +----+----+----+----+----+----+
       | 61 | 62 | 00 | 63 | 64 | 00 |
       +----+----+----+----+----+----+
       | 'a'| 'b'| \0 | 'c'| 'd'| \0 |
       +----+----+----+----+----+----+
       |<-strlen=2->|
       |<---------- sizeof=6 --------->|

   printf("%s", mid)  ->  [ab]        <- ★ 첫 0 에서 멈춘다. 뒤의 cd 는 못 본다
   눈에 보이게 펼치면  ->  [ab\0cd\0]   <- 실제로는 여섯 바이트가 다 있다
```

그림 해설 (한 단계씩):

- ★★★ **`memcmp` 가 0** 이다. `"abc"` 로 초기화한 배열과 **손으로 쓴 네 글자 배열**의 바이트가 **같다.**\
  ★ 「문자열 리터럴로 만들면 특별한 무언가가 된다」가 아니다 — **`char` 네 칸이 될 뿐**이다.
- **`sizeof arr` 는 4, `strlen(arr)` 은 3** 이다. **차이는 널 종단자 한 칸**이다.
- ★★ **`sizeof lit` 은 8** 이다. `lit` 은 **포인터**라 재는 대상이 다르다 —\
  ★ 이 대비는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다. 여기서 되짚을 결론은 한 줄이다 —\
  「**`sizeof` 는 눈앞의 변수를 재고, `strlen` 은 가리키는 곳을 걸어간다.**」
- ★★★ **`mid` 에서 「길이」가 갈라진다** — **`sizeof` 6, `strlen` 2.**\
  **둘 다 맞다.** 다른 질문에 답한 것이다 — 하나는 **상자 크기**, 하나는 **약속상의 끝**.
- ★ **`%s` 는 `[ab]` 만 찍는다.** 뒤의 `63 64 00` 은 메모리에 멀쩡히 있는데 **관례가 거기서 끊는다.**

비용 — 없다. 대신 **길이를 알고 싶을 때마다 `strlen` 이 배열을 한 번 걷는다**(O(n)).\
★ 길이를 자주 쓰면 **따로 들고 다니는 쪽**이 싸다 — 그것이 다른 언어의 「문자열 타입」이 하는 일이다.

### (2) ★★★ 리터럴을 고치면 — **이 주제의 본체**

**언제 쓰나** — `char *p = "abc"; p[0] = 'A';` 를 처음 써 보고 **왜 죽는지** 물을 때.\
★ **복사본은 고쳐지고 리터럴은 안 고쳐진다** — 한 프로그램에 둘을 나란히 두고 던진다.

```c
/* ex2.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char arr[] = "abc";          /* 배열 = 복사본 */
    char *lit  = "abc";          /* 리터럴 그 자체 */

    arr[0] = 'A';                /* (가) 복사본은 고쳐도 된다 */
    printf("(가) arr 를 고쳤다 : %s\n", arr);

    printf("(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'\n");
    lit[0] = 'A';                /* (나) 리터럴 수정 = UB */
    printf("(나) 살아남았다 : %s\n", lit);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex2.c -o x2 ; ./x2 (cc exit=0 · run exit=139) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex2.c -o x2c ; ./x2c (cc exit=0 · run exit=139) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex2.c -o x2a ; ./x2a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
(가) arr 를 고쳤다 : Abc
(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'
AddressSanitizer:DEADLYSIGNAL
=================================================================
==85373==ERROR: AddressSanitizer: SEGV on unknown address 0x5a077fa98040 (pc 0x5a077fa97456 bp 0x7fff53a45c80 sp 0x7fff53a45bf0 T0)
==85373==The signal is caused by a WRITE memory access.
    #0 0x5a077fa97456 in main /tmp/c17b/20/ex2.c:12
    #1 0x71117682a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x71117682a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5a077fa971e4 in _start (/tmp/c17b/20/x2a+0x11e4) (BuildId: 0cb573e04e8c9b7d8af12058870b40bb9d193bf1)

AddressSanitizer can not provide additional info.
SUMMARY: AddressSanitizer: SEGV /tmp/c17b/20/ex2.c:12 in main
```

```text
   같은 "abc" 인데 ★ 사는 곳이 다르다

   char arr[] = "abc";                    char *lit = "abc";
   (스택 — 이 함수의 것)                   (정적 — 프로그램 전체의 것)

   스택                                    .rodata (읽기 전용으로 매핑)
   +----+----+----+----+                  +----+----+----+----+
   | 61 | 62 | 63 | 00 |                  | 61 | 62 | 63 | 00 |
   +----+----+----+----+                  +----+----+----+----+
     ^                                      ^
     arr (배열 그 자체)                       |
                                          lit : [주소] ------+

   arr[0] = 'A'   ->  +----+  61->41 로 바뀐다  ->  "Abc" 가 찍힌다   (★ 완전히 합법)
   lit[0] = 'A'   ->  ★ 쓰기 금지 페이지에 쓴다 ->  SIGSEGV          (★ UB · run exit=139)
```

그림 해설 (한 단계씩):

- ★★ 두 줄의 차이는 「**복사본인가 원본인가**」다. `arr` 는 리터럴을 **베껴 만든 배열**이고,\
  `lit` 는 **리터럴 그 자체**를 가리킨다. **고쳐도 되는 것은 내가 만든 복사본뿐**이다.
- ★★★ **평범한 실행은 `run exit=139`** 다. 마지막 `printf("(나) 살아남았다 …")` 는 **찍히지 않았다** —\
  ★ **출력이 어디서 끊겼는지가 증거**다(그래서 `setvbuf` 로 버퍼링을 껐다).
- ★★ **gcc 와 clang 이 똑같이 139** 였다. **두 컴파일러가 같다는 것은 보장이 아니다** —\
  둘 다 같은 OS 위에서 같은 방식으로 리터럴을 놓았을 뿐이다.
- ★★★ **ASan 은 「죽었다」가 아니라 「무엇을 했는지」를 말한다** —\
  「**The signal is caused by a WRITE memory access**」. **읽기가 아니라 쓰기**라는 것이 핵심이다.\
  ★ 그리고 **`run exit=1`** 로 바뀐다 — 같은 UB 가 **도구에 따라 다른 종료 코드**를 낸다.
- ★ **ASan 도 여기서는 반쪽이다** — `stack-buffer-overflow` 처럼 **무엇을 넘었는지는 말하지 못하고**\
  「**AddressSanitizer can not provide additional info**」로 끝난다. **리터럴 수정은 ASan 에게도 그냥 SEGV** 다.

비용 — **없다.** 복사본을 만드는 쪽(`char s[] = …`)이 **배열 크기만큼의 스택**을 쓰고,\
리터럴을 가리키는 쪽(`char *p = …`)은 **포인터 8바이트**만 쓴다. ★ **고칠 것이면 전자, 읽기만 하면 후자**다.

### (2-나) 그런데 **`-Wall -Wextra -pedantic` 은 한 마디도 안 한다**

**언제 쓰나** — 「경고가 없으니 괜찮겠지」라고 생각했을 때. ★ **위 블록의 배너를 다시 보라** — `cc exit=0` 에 **경고가 0건**이다.

```c
/* ex2.c */
#include <stdio.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char arr[] = "abc";          /* 배열 = 복사본 */
    char *lit  = "abc";          /* 리터럴 그 자체 */

    arr[0] = 'A';                /* (가) 복사본은 고쳐도 된다 */
    printf("(가) arr 를 고쳤다 : %s\n", arr);

    printf("(나) 이제 리터럴을 고쳐 본다 — lit[0] = 'A'\n");
    lit[0] = 'A';                /* (나) 리터럴 수정 = UB */
    printf("(나) 살아남았다 : %s\n", lit);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -Wwrite-strings ex2.c -o /dev/null (cc exit=0) =====
ex2.c: In function ‘main’:
ex2.c:6:18: warning: initialization discards ‘const’ qualifier from pointer target type [-Wdiscarded-qualifiers]
    6 |     char *lit  = "abc";          /* 리터럴 그 자체 */
      |                  ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -Wwrite-strings ex2.c -o /dev/null (cc exit=0) =====
ex2.c:6:11: warning: initializing 'char *' with an expression of type 'const char[4]' discards qualifiers [-Wincompatible-pointer-types-discards-qualifiers]
    6 |     char *lit  = "abc";          /* 리터럴 그 자체 */
      |           ^      ~~~~~
1 warning generated.
```

```text
===== gcc -std=c17 ex2.c -o x2s && objdump -h x2s | grep -E 'rodata|[.]data' (exit=0) =====
 17 .rodata       00000085  0000000000002000  0000000000002000  00002000  2**3
 24 .data         00000010  0000000000004000  0000000000004000  00003000  2**3
```

```text
   ★ 누가 언제 말해 주는가 — 위에서 아래로 갈수록 늦다

   컴파일 시간  -Wall -Wextra -pedantic        ->  ★ 0 건  (아무 말도 없다)
                       |
                       v
   컴파일 시간  + -Wwrite-strings               ->  1 건
                 gcc  : -Wdiscarded-qualifiers
                 clang: -Wincompatible-pointer-types-discards-qualifiers
                 ★ 단 "수정" 이 아니라 "초기화에서 const 를 버렸다" 를 잡는다
                       |
                       v
   링크 뒤     objdump -h                       ->  .rodata 에 있다는 "배치" 만 보인다
                       |
                       v
   실행 시간   그냥 실행                          ->  SIGSEGV · run exit=139  (★ 여기서야 안다)
                       |
                       v
   실행 시간   ASan                              ->  "WRITE memory access" · run exit=1
```

그림 해설 (한 단계씩):

- ★★★ **기본 플래그로는 경고가 0건**이다. **C 에서 문자열 리터럴의 타입이 `char[]` 이기 때문**이다 —\
  `char *lit = "abc";` 는 **타입이 맞는 대입**이라 수상할 게 없다. (C++ 이라면 `const char[]` 라 바로 걸린다.)
- ★★ **`-Wwrite-strings` 를 켜면 리터럴의 타입을 `const char[]` 로 바꿔 준다.**\
  그제서야 `char *` 로 받는 것이 **const 를 버리는 짓**이 되어 진단이 난다.\
  ★ **플래그 이름이 두 컴파일러에서 완전히 다르다** — gcc 는 `-Wdiscarded-qualifiers`,\
  clang 은 `-Wincompatible-pointer-types-discards-qualifiers`.
- ★★ **그래도 경고이지 에러가 아니다**(`cc exit=0`). 빌드는 그대로 나온다.
- ★★ **진단이 가리키는 줄은 `lit[0] = 'A';` 가 아니라 `char *lit = "abc";`** 다 —\
  ★ 도구가 잡은 것은 「수정」이 아니라 「**수정할 수 있는 포인터로 받은 것**」이다. **한 발 앞을 잡는다.**
- ★ **`objdump -h` 는 `.rodata` 와 `.data` 가 따로 있다는 것**을 보여 준다.\
  ★ **이것은 구현 정의(사실은 이 플랫폼의 ABI)이지 표준이 말하는 것이 아니다.** 표준이 말하는 것은 「**고치면 UB**」까지다.

비용 — `-Wwrite-strings` 는 **기존 코드에서 경고가 쏟아질 수 있다**(`char *` 로 리터럴을 받는 코드가 전부 걸린다).\
★ 새 코드라면 **`const char *` 로 받는 습관**이 같은 효과를 공짜로 낸다.

### (3) ★★ 왜 「복사」인가 — 초기화의 두 꼴

**언제 쓰나** — 「`char s[] = "abc"` 는 왜 고쳐지나」를 물을 때.\
★ **`sizeof` 대비(3 대 8)와 감쇠 규칙 자체**는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다 — 여기서는 **왜 복사인지**만 판다.

```text
   ★ 두 줄은 문법이 비슷할 뿐 ★ 하는 일이 다르다

   (가) char s[] = "abc";          "배열을 만들고 그 안을 채워라"
        +----+----+----+----+
   s -> | 61 | 62 | 63 | 00 |      <- ★ 이 네 칸은 s 의 것이다 (스택)
        +----+----+----+----+      <- 리터럴은 "초기값의 모양" 으로만 쓰였다
        s[0]='A' -> 내 배열을 고치는 것    ★ 합법

   (나) char *p = "abc";           "저기 있는 배열의 첫 칸 주소를 가져라"
        p -> [주소] ----+
                        v
        .rodata  +----+----+----+----+
                 | 61 | 62 | 63 | 00 |   <- ★ 이 네 칸은 프로그램의 것이다
                 +----+----+----+----+
        p[0]='A' -> 남의 것을 고치는 것     ★ UB

   ★ 가름선 한 줄 : 왼쪽에 "배열" 이 선언되면 복사, "포인터" 가 선언되면 가리킴.
```

그림 해설 (한 단계씩):

- ★★ **`char s[] = "abc"` 에서 리터럴은 감쇠하지 않는다.** 배열 초기화는 **원소를 채우는 일**이라\
  리터럴이 **주소로 변하지 않고 「바이트 넷」으로 쓰인다.** 그래서 **복사**다.\
  ★ 이것이 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 말한 **감쇠가 안 일어나는 세 자리 중 하나**다.
- ★★ **`char *p = "abc"` 에서는 감쇠한다.** 리터럴이 **첫 원소의 주소**가 되어 포인터에 들어간다.\
  ★ **복사는 한 바이트도 안 일어난다.** 그래서 싸고, 그래서 **남의 것**이다.
- ★ **크기가 다르다** — 복사본은 **스택에 네 칸**을 쓰고, 포인터는 **8바이트**를 쓴다.\
  값은 (1)의 출력에 있다(`sizeof arr` 4, `sizeof lit` 8).
- ★★ **저장 기간도 다르다** — 복사본은 **그 블록이 끝나면 사라지고**,\
  리터럴은 **프로그램이 끝날 때까지 산다.**\
  ★ 그래서 **`return "hello";` 는 댕글링이 아니고**(목록의 **57번 주제**와 갈리는 자리),\
  **`char s[] = "hello"; return s;` 는 댕글링**이다.
- ★ **고칠 수 있게 만드는 가장 싼 고침은 `[]` 한 쌍**이다 — `char *p` 를 `char p[]` 로 바꾸면 된다.\
  ★ 읽기만 할 것이면 **`const char *p`** 로 받아 **컴파일러에게 검사를 시킨다.**

비용 — 복사본은 **매번 바이트를 복사**한다(짧으면 무시할 만하고, 긴 리터럴을 루프 안에서 복사하면 비용이 보인다).\
리터럴을 가리키는 쪽은 **공짜**다 — 대신 **고칠 수 없다.**

### (4) ★★★ 같은 글자의 리터럴 둘은 같은 주소인가 — **미명시**

**언제 쓰나** — 「리터럴을 `==` 로 비교해도 되나」를 물을 때. ★ 답은 「**되는 날도 있다**」이고, 그것이 곧 **하면 안 된다**는 뜻이다.\
★★ **한 벌만 돌리면 반대 결론이 난다** — 그래서 **다섯 벌**을 돌린다.

```c
/* ex3.c */
#include <stdio.h>
#include <string.h>

static const char *f(void) { return "hello"; }

int main(void) {
    const char *a = "hello";
    const char *b = "hello";          /* 같은 글자의 리터럴 둘 */
    const char *c = f();              /* 다른 함수 안의 같은 리터럴 */
    const char *d = "hello world";    /* 더 긴 리터럴 */
    const char *tail = d + 6;         /* 그 꼬리 "world" */
    const char *e = "world";          /* 꼬리와 같은 글자 */

    printf("a == b            : %s   (같은 파일 안의 같은 리터럴)\n", a == b ? "★ 공유" : "따로");
    printf("a == c            : %s   (다른 함수 안의 같은 리터럴)\n", a == c ? "★ 공유" : "따로");
    printf("e == d+6          : %s   (꼬리 겹침)\n", e == tail ? "★ 공유" : "따로");
    printf("strcmp(a,b) = %d · strcmp(e,tail) = %d  (글자는 어차피 같다)\n",
           strcmp(a, b), strcmp(e, tail));
    printf("a-b 의 바이트 차  : %td\n", a - b);
    printf("d 와 a 의 차가 0 인가 : %s\n", d == a ? "그렇다" : "아니다");
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 ex3.c -o x3_O0 ; ./x3_O0 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : 따로   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 ex3.c -o x3_O2 ; ./x3_O2 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -fno-merge-constants ex3.c -o x3_nm ; ./x3_nm (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : 따로   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 ex3.c -o x3c_O0 ; ./x3c_O0 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 ex3.c -o x3c_O2 ; ./x3c_O2 (cc exit=0 · run exit=0) =====
a == b            : ★ 공유   (같은 파일 안의 같은 리터럴)
a == c            : ★ 공유   (다른 함수 안의 같은 리터럴)
e == d+6          : ★ 공유   (꼬리 겹침)
strcmp(a,b) = 0 · strcmp(e,tail) = 0  (글자는 어차피 같다)
a-b 의 바이트 차  : 0
d 와 a 의 차가 0 인가 : 아니다
```

**다섯 벌을 한 표로**

| 빌드 | `a == b`(같은 글자 둘) | `a == c`(다른 함수 안) | ★★ `e == d+6`(꼬리 겹침) |
|---|---|---|---|
| gcc `-O0` | **공유** | **공유** | ★ **따로** |
| gcc `-O2` | **공유** | **공유** | ★ **공유** |
| gcc `-O2 -fno-merge-constants` | **공유** | **공유** | ★ **따로** |
| clang `-O0` | **공유** | **공유** | ★ **공유** |
| clang `-O2` | **공유** | **공유** | ★ **공유** |

```text
   ★ 꼬리 겹침이란 무엇인가 —  "hello world" 와 "world"

   (가) 따로 놓은 판 (gcc -O0 · gcc -O2 -fno-merge-constants)

   .rodata  | h e l l o _ w o r l d \0 | w o r l d \0 |
             ^                          ^
             d                          e            <- ★ e != d+6

   (나) 꼬리를 겹쳐 놓은 판 (gcc -O2 · clang -O0 · clang -O2)

   .rodata  | h e l l o _ w o r l d \0 |
             ^                 ^
             d                 e = d+6               <- ★ 같은 주소. 6바이트를 아꼈다

   ★ 두 판 모두 ★ 적법하다. strcmp 는 어느 판에서도 0 이고,
     "같은 주소인가" 만 갈린다 — 그것이 ★ 미명시라는 뜻이다.
```

그림 해설 (한 단계씩):

- ★★ **같은 글자의 리터럴 둘(`a`·`b`)은 다섯 벌 전부 공유**했다. **다른 함수 안의 같은 리터럴(`c`)도 마찬가지**였다.\
  ★ **그래서 더 위험하다** — 다섯 벌이 한 글자도 다르지 않으면 **보장이라고 믿게 된다.**
- ★★★ **갈리는 자리는 꼬리 겹침**이다. **gcc 는 `-O2` 에서만 겹치고**,\
  **`-fno-merge-constants` 를 주면 `-O2` 에서도 안 겹친다.** **clang 은 `-O0` 부터 겹친다.**\
  ★ **같은 소스·같은 표준·같은 머신에서 결과가 갈렸다.** 갈린 축은 **컴파일러와 최적화 플래그**다.
- ★★ **`strcmp` 는 어느 벌에서도 0** 이다. **글자는 언제나 같다** — 갈리는 것은 **주소뿐**이다.\
  ★ **그래서 문자열 비교는 `==` 가 아니라 `strcmp`** 다. `==` 는 「**같은 판을 가리키나**」를 묻는 것이지\
  「**같은 글자인가**」를 묻는 것이 아니다.
- ★ **`d == a` 는 어느 벌에서도** 「**아니다**」였다 — `"hello world"` 의 **머리**는 `"hello"` 와 안 겹쳤다.\
  ★ **겹칠 수 있는 것은 꼬리뿐**이다. 널 종단 때문에 **머리를 공유하면 끝을 표시할 방법이 없다.**
- ★★★ **결론 한 줄** — 「**리터럴의 주소가 같은가**」에 **어떤 코드도 의지해서는 안 된다.**\
  표준은 **공유해도 되고 안 해도 된다**고만 정한다.

비용 — 공유는 **바이너리를 줄인다**(꼬리 겹침으로 6바이트를 아꼈다).\
★ 그 대가로 **「리터럴 두 개가 정말 두 개인가」가 빌드마다 달라진다.**

### (5) ★★ `char s[3] = "abc"` — **되는데 널이 없다**

**언제 쓰나** — 배열 크기를 손으로 셀 때. ★ **한 칸을 덜 세면 조용히 널이 빠진다.**

```c
/* ex4.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    char exact[4] = "abc";     /* 딱 맞는다 — 널까지 들어간다 */
    char tight[3] = "abc";     /* ★ 널이 안 들어간다 (표준이 허용한다) */
    char big[6]   = "abc";     /* 남는 칸은 0 으로 채워진다 */

    printf("exact : sizeof %zu · 바이트 ", sizeof exact);
    for (size_t k = 0; k < sizeof exact; k++) printf("%02x ", (unsigned char)exact[k]);
    printf("· strlen %zu\n", strlen(exact));

    printf("tight : sizeof %zu · 바이트 ", sizeof tight);
    for (size_t k = 0; k < sizeof tight; k++) printf("%02x ", (unsigned char)tight[k]);
    printf("· ★ 널이 없다 -> strlen 은 배열 밖을 읽는다(UB)\n");

    printf("big   : sizeof %zu · 바이트 ", sizeof big);
    for (size_t k = 0; k < sizeof big; k++) printf("%02x ", (unsigned char)big[k]);
    printf("· strlen %zu\n", strlen(big));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex4.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex4.c -o x4 ; ./x4 (cc exit=0 · run exit=0) =====
exact : sizeof 4 · 바이트 61 62 63 00 · strlen 3
tight : sizeof 3 · 바이트 61 62 63 · ★ 널이 없다 -> strlen 은 배열 밖을 읽는다(UB)
big   : sizeof 6 · 바이트 61 62 63 00 00 00 · strlen 3
```

```text
   같은 "abc" · 배열 크기만 다르다

   char exact[4] = "abc";     +----+----+----+----+
                              | 61 | 62 | 63 | 00 |     strlen 3   ★ 정상
                              +----+----+----+----+

   char tight[3] = "abc";     +----+----+----+
                              | 61 | 62 | 63 |          ★ 널이 없다
                              +----+----+----+
                                              ^
                                              여기부터는 ★ 이 배열이 아니다

   char big[6]   = "abc";     +----+----+----+----+----+----+
                              | 61 | 62 | 63 | 00 | 00 | 00 |     strlen 3
                              +----+----+----+----+----+----+
                                              ^-- 남는 칸은 ★ 0 으로 채운다 (쓰레기가 아니다)
```

그림 해설 (한 단계씩):

- ★★★ **`char tight[3] = "abc"` 는 적법하다.** 컴파일이 되고(`cc exit=0`) **경고가 0건**이다.\
  ★ **표준이 이 한 자리를 특별히 허용한다** — 「**널 종단자만 안 들어가는 경우**」는 초과 초기화가 아니다.
- ★★★ **gcc 도 clang 도 한 마디도 안 한다.** 두 진단 블록이 **비어 있다** — 그것이 이 절의 결론이다.\
  ★ **gcc 13 에는 이것을 잡는 옵션 자체가 없다**(`-Wunterminated-string-initialization` 을 주면\
  `unrecognized command-line option` 으로 **컴파일이 시작도 안 된다**).\
  ★ 이 문서는 **그 실패를 진단 블록으로 싣지 않았다** — 배너 규칙상 「옵션이 없다」는 컴파일 실패라 따로 다룬다.
- ★★ **`big[6]` 의 남는 칸은 0 으로 채워진다.** **쓰레기가 아니다** — 바이트가 `61 62 63 00 00 00` 이다.\
  ★ 그래서 **`strlen(big)` 은 3** 이고, **남는 칸이 있는 쪽은 안전**하다.
- ★ **위험한 것은 딱 한 칸 모자란 경우**다. `tight` 는 **글자는 다 들어갔는데 끝 표시만 없다** —\
  ★ **이 상태가 (6)에서 어떻게 조용히 넘어가는지**가 이 주제의 가장 나쁜 자리다.

비용 — 없다. ★ **비용이 없다는 것이 문제**다 — 컴파일러도 런타임도 아무것도 청구하지 않는다.

### (5-나) 한 칸을 더 줄이면 — **거기서는 말해 준다**

**언제 쓰나** — 「그럼 컴파일러는 언제 말해 주나」의 **경계선**을 그을 때.

```c
/* ex5.c */
#include <stdio.h>

int main(void) {
    char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
    printf("%c%c\n", over[0], over[1]);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=0) =====
ex5.c: In function ‘main’:
ex5.c:4:20: warning: initializer-string for array of ‘char’ is too long
    4 |     char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
      |                    ^~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic ex5.c -o /dev/null (cc exit=0) =====
ex5.c:4:20: warning: initializer-string for char array is too long [-Wexcess-initializers]
    4 |     char over[2] = "abc";      /* 두 칸에 네 바이트 — 넘친다 */
      |                    ^~~~~
1 warning generated.
```

```text
   ★ 경계선은 "널 한 칸" 이다

   char exact[4] = "abc";   61 62 63 00   4칸에 4바이트        -> 진단 ★ 0건
   char tight[3] = "abc";   61 62 63      3칸에 ★ 널만 못 넣음  -> 진단 ★ 0건  (표준이 허용)
   char over [2] = "abc";   61 62         2칸에 ★ 글자가 넘침   -> 진단 ★ 1건  (양쪽 다)

                                          ^ 여기서부터가 "초과 초기화" 다
```

그림 해설 (한 단계씩):

- ★★ 경계선은 「**널 한 칸이 모자란가, 글자가 모자란가**」다.\
  **널만 못 넣는 것은 허용**이고, **글자가 잘리는 것은 진단**이다.
- ★★ **양쪽 다 경고이고 에러가 아니다**(`cc exit=0`). 실행 파일은 그대로 나온다.
- ★ **gcc 의 진단에는 플래그 이름이 안 붙는다**(`initializer-string for array of ‘char’ is too long`).\
  **clang 은 `-Wexcess-initializers` 라고 이름을 댄다.**\
  ★ **플래그 이름이 없다는 것은 `-Wno-…` 로 끌 수 없다는 뜻**이기도 하다.
- ★ **넘친 글자는 버려진다** — 두 칸에 들어갈 수 있는 것은 **두 바이트뿐**이다.\
  ★ **이 문서는 `ex5.c` 를 실행하지 않았다** — **컴파일 진단까지만** 보았다.

비용 — 없다. **한 칸 차이로 도구의 태도가 통째로 바뀐다**는 것만 기억하면 된다.

### (6) ★★★ 널이 없는 배열에 `strlen` — **조용히 맞아 보인다**

**언제 쓰나** — (5)의 `tight` 를 그대로 쓰는 코드를 만났을 때. ★ **이 절이 이 주제에서 가장 나쁜 자리**다.

```c
/* ex6.c */
#include <stdio.h>
#include <string.h>

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    char tight[3] = "abc";     /* 널이 없다 */
    printf("strlen 직전\n");
    printf("strlen(tight) = %zu\n", strlen(tight));
    printf("%%s 로 찍으면 : [%s]\n", tight);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g ex6.c -o x6 ; ./x6 (cc exit=0 · run exit=0) =====
strlen 직전
strlen(tight) = 3
%s 로 찍으면 : [abc]
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -g -fsanitize=address ex6.c -o x6a ; ./x6a | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
strlen 직전
=================================================================
==85590==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7918f4500023 at pc 0x7918f6a7d96f bp 0x7ffd35694930 sp 0x7ffd356940d8
READ of size 4 at 0x7918f4500023 thread T0
    #0 0x7918f6a7d96e in strlen ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391
    #1 0x5cbda230c3fe in main /tmp/c17b/20/ex6.c:8
    #2 0x7918f662a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x7918f662a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x5cbda230c1e4 in _start (/tmp/c17b/20/x6a+0x11e4) (BuildId: c31ad5242638fd215017d60788a2581d5d156168)

Address 0x7918f4500023 is located in stack of thread T0 at offset 35 in frame
    #0 0x5cbda230c2b8 in main /tmp/c17b/20/ex6.c:4

  This frame has 1 object(s):
    [32, 35) 'tight' (line 6) <== Memory access at offset 35 overflows this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-buffer-overflow ../../../../src/libsanitizer/sanitizer_common/sanitizer_common_interceptors.inc:391 in strlen
```

```text
   ★ strlen 은 "이 배열" 이라는 것을 모른다 — 0 을 만날 때까지 걷는다

   스택          [32] [33] [34] | [35] [36] ...
                +----+----+----+ +----+----+
                | 61 | 62 | 63 | | ?? | ?? |
                +----+----+----+ +----+----+
                |<- tight[3] ->| |<- ★ 여기는 tight 가 아니다 ->
                 a    b    c

   strlen(tight) 이 걸어간 길 :
      [32] 61 아니다 -> [33] 62 아니다 -> [34] 63 아니다 -> [35] ★ 배열 밖을 읽는다
                                                              그 자리가 마침 0 이라서 3 을 돌려줬다

   ★ 평범한 실행 : strlen = 3 · [abc] · run exit=0   <- ★ 어디서 봐도 정상이다
   ★ ASan       : stack-buffer-overflow READ · run exit=1
```

그림 해설 (한 단계씩):

- ★★★ **평범한 실행이 「맞는 답」을 냈다.** `strlen` 이 **3** 을 돌려주고 `%s` 가 **`[abc]`** 를 찍고\
  **`run exit=0`** 으로 얌전히 끝났다. ★ **틀린 값이 나왔다면 오히려 다행**이었을 것이다.
- ★★★ **그런데 UB 다.** ASan 이 **`stack-buffer-overflow`** 로 잡고,\
  **`[32, 35) 'tight'`** 라고 **배열의 범위까지 찍어 준 뒤** 「**offset 35 에서 넘쳤다**」고 말한다.
- ★★ **`READ of size 4`** 다 — 배열은 **세 칸인데 네 바이트가 읽은 범위로 잡혔다.**\
  ★ 셈은 단순하다 — **글자 3 + 끝 표시 1**. `strlen` 은 **0 을 실제로 읽어야** 끝을 알기 때문에\
  **네 번째 바이트를 반드시 읽고**, 그 네 번째 칸이 **이 배열의 것이 아니다.**\
  ★ **못 가른 것** — 그 `4` 가 **ASan 가로채기의 셈법**인지 **실제 읽기 폭**인지는 이 문서가 확인하지 못했다\
  (ASan 리포트는 `strlen` 안을 가리킬 뿐 몇 바이트씩 걸었는지는 말하지 않는다).
- ★★ **리포트가 가리키는 곳은 `strlen` 안**이다(sanitizer 의 가로채기 코드) — **내 소스 줄은 그 다음 프레임**이다.\
  ★ **ASan 스택은 위에서 아래로 「누가 읽었나 → 누가 불렀나」** 순서로 읽는다.
- ★★★ **(5)와 이어 붙이면 이 주제의 최악 조합이 된다** —\
  **컴파일 경고 0건**(5) + **평범한 실행 `exit=0` 에 맞는 답**(6). **두 창이 다 초록인데 UB 다.**

비용 — ASan 은 **느리다**(대략 두 배 이상). 대신 **이 자리는 ASan 없이는 보이지 않는다.**

### (7) ★★ `strncpy` 는 **널을 안 붙일 수 있다**

**언제 쓰나** — 「`strcpy` 는 위험하다니 `strncpy` 를 쓰자」고 했을 때.\
★ **`strncpy` 의 `n` 은 「널까지 n 바이트」가 아니라** 「**딱 n 바이트를 쓴다**」는 뜻이다.\
★ **함수 계약 전반은 목록의 49번 주제가 정본**이고, 여기서는 **널 종단과 얽힌 한 가지**만 본다.

```c
/* ex7.c */
#include <stdio.h>
#include <string.h>

static void dump(const char *tag, const char buf[5]) {
    printf("%s : ", tag);
    for (int k = 0; k < 5; k++) printf("%02x ", (unsigned char)buf[k]);
    printf("\n");
}

int main(void) {
    /* (가) 원본이 짧으면 — 남는 칸을 전부 0 으로 채운다 */
    char a[5];
    memset(a, 0x7e, sizeof a);
    strncpy(a, "ab", 5);
    dump("(가) strncpy(a,\"ab\",5)   ", a);

    /* (나) 원본이 딱 맞으면 — 널이 안 붙는다 */
    char b[5];
    memset(b, 0x7e, sizeof b);
    strncpy(b, "abcde", 5);
    dump("(나) strncpy(b,\"abcde\",5)", b);

    /* (다) 원본이 길면 — 잘리고 널도 없다 */
    char c[5];
    memset(c, 0x7e, sizeof c);
    strncpy(c, "abcdefgh", 5);
    dump("(다) strncpy(c,\"abcdefgh\",5)", c);

    /* (라) 안전하게 쓰는 꼴 — 마지막 칸을 직접 0 으로 */
    char d[5];
    strncpy(d, "abcdefgh", sizeof d - 1);
    d[sizeof d - 1] = '\0';
    dump("(라) 마지막 칸을 손으로 0", d);
    printf("     d = [%s] · strlen = %zu\n", d, strlen(d));
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 (cc exit=0) =====
ex7.c: In function ‘main’:
ex7.c:20:5: warning: ‘strncpy’ output truncated before terminating nul copying 5 bytes from a string of the same length [-Wstringop-truncation]
   20 |     strncpy(b, "abcde", 5);
      |     ^~~~~~~~~~~~~~~~~~~~~~
ex7.c:26:5: warning: ‘strncpy’ output truncated copying 5 bytes from a string of length 8 [-Wstringop-truncation]
   26 |     strncpy(c, "abcdefgh", 5);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 ex7.c -o /dev/null (cc exit=0) =====
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 ex7.c -o /dev/null (cc exit=0) =====
ex7.c: In function ‘main’:
ex7.c:20:5: warning: ‘__builtin_strncpy’ output truncated before terminating nul copying 5 bytes from a string of the same length [-Wstringop-truncation]
   20 |     strncpy(b, "abcde", 5);
      |     ^
ex7.c:26:5: warning: ‘__builtin_strncpy’ output truncated copying 5 bytes from a string of length 8 [-Wstringop-truncation]
   26 |     strncpy(c, "abcdefgh", 5);
      |     ^
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic ex7.c -o x7 ; ./x7 (cc exit=0 · run exit=0) =====
(가) strncpy(a,"ab",5)    : 61 62 00 00 00 
(나) strncpy(b,"abcde",5) : 61 62 63 64 65 
(다) strncpy(c,"abcdefgh",5) : 61 62 63 64 65 
(라) 마지막 칸을 손으로 0 : 61 62 63 64 00 
     d = [abcd] · strlen = 4
```

```text
   ★ 미리 0x7e 로 채워 두고 던진다 — "무엇이 덮였나" 를 눈에 보이게 하려고

   시작 상태        7e 7e 7e 7e 7e

   (가) strncpy(a, "ab", 5)        61 62 00 00 00   ★ 남는 칸을 전부 0 으로 채웠다
   (나) strncpy(b, "abcde", 5)     61 62 63 64 65   ★ 널이 없다 (딱 맞았다)
   (다) strncpy(c, "abcdefgh", 5)  61 62 63 64 65   ★ 잘리고 널도 없다
   (라) strncpy(d, "abcdefgh", 4)  61 62 63 64 ??
        d[4] = '\0';               61 62 63 64 00   ★ 마지막 칸을 손으로 0 으로
                                                      -> [abcd] · strlen 4
```

그림 해설 (한 단계씩):

- ★★ **(가) 짧으면 0 으로 꽉 채운다.** `7e` 가 **한 칸도 안 남고** 사라졌다 —\
  ★ **`strncpy` 는 「복사」가 아니라** 「**n 바이트를 통째로 쓴다**」에 가깝다. 긴 버퍼에 짧은 문자열을 넣으면 **그만큼 일한다.**
- ★★★ **(나)·(다)는 널이 없다.** 원본이 **딱 맞거나 길면** 끝 표시가 **안 붙는다.**\
  ★ 그 뒤에 `%s` 나 `strlen` 을 쓰면 **(6)과 같은 자리**가 된다 — **UB 인데 조용하다.**
- ★★ **gcc 는 두 건을 잡는다**(`-Wstringop-truncation`) — **(나)와 (다)** 다. **(가)는 안 잡는다**(널이 붙었으니까).\
  ★ **`-O2` 에서는 같은 두 건인데 함수 이름이 `__builtin_strncpy` 로 바뀐다** —\
  ★ **진단 문구를 문자열로 대조하는 검사는 최적화 수준에서 깨진다.**
- ★★★ **clang 은 `-O2` 에서도 0건**이다. **같은 코드·같은 표준인데 한쪽만 말해 준다.**\
  ★ **「경고가 없다」가 「안전하다」가 아니라는 것**이 이 대비의 결론이다.
- ★ **(라)가 안전하게 쓰는 꼴**이다 — **`sizeof d - 1` 만 복사하고 마지막 칸을 직접 0** 으로 만든다.\
  ★ **여전히 보장되지 않는 것** — **잘렸는지 아닌지는 알려 주지 않는다**(`d` 는 `abcd` 이고 원본은 `abcdefgh` 였다).\
  잘림을 알아야 하면 **길이를 먼저 재거나 반환값을 쓰는 다른 함수**가 필요하다(목록의 **49번 주제**).

비용 — **(가)의 0 채우기가 공짜가 아니다.** 4KB 버퍼에 다섯 글자를 넣으면 **4KB 를 쓴다.**\
★ 그래서 `strncpy` 는 「**고정 폭 레코드를 만드는 함수**」로 보는 것이 맞고, **「안전한 `strcpy`」가 아니다.**

## 문법 — 형태와 규칙

### 형태 — 문자열을 만드는 네 가지

```c
char  a[] = "abc";        /* ① 복사본. 크기는 4 (널 포함). ★ 고칠 수 있다 */
char  b[4] = "abc";       /* ② ①과 같다. 크기를 손으로 적었을 뿐 */
char  c[3] = "abc";       /* ③ ★ 적법하다 — 널만 안 들어간다. 경고 0건 */
char *d = "abc";          /* ④ 리터럴을 가리킨다. ★ 고치면 UB */
const char *e = "abc";    /* ★ ④의 올바른 꼴 — 컴파일러가 대신 막아 준다 */

char  f[6] = "abc";       /* 남는 칸은 0 으로 채워진다 : 61 62 63 00 00 00 */
char  g[] = {'a','b','c','\0'};   /* ★ ①과 바이트가 같다 (memcmp = 0) */
```

### 금지 사례 — 어느 것이 무슨 층인가

```c
char *p = "abc";
p[0] = 'A';                      /* ★★★ UB — 리터럴 수정. 실측 run exit=139 */

char t[3] = "abc";
size_t n = strlen(t);            /* ★★ UB — 널이 없다. 실측은 3 을 내고 exit=0 (조용하다) */
printf("%s", t);                 /* ★★ 같은 UB — %s 도 널까지 걷는다 */

char dst[5];
strncpy(dst, "abcde", 5);
printf("%s", dst);               /* ★★ UB — strncpy 가 널을 안 붙였다 */

char over[2] = "abc";            /* ★ 초과 초기화 — 양쪽 다 경고 (에러는 아니다) */

if (p == "abc") { … }            /* ★ 미명시에 의지하는 것 — 공유 여부는 빌드마다 갈린다 */

char *q = get();                 /* 계약을 모르는 포인터에 */
q[strlen(q) - 1] = '\0';         /* ★ 빈 문자열이면 UB — strlen 이 0 이면 q[-1] 이다 */
```

### 규칙 불릿

- ★★★ **문자열은 타입이 아니다.** `char` 배열과 **끝의 0 하나**가 전부다(`memcmp` 가 0 이었다).
- ★★ **`sizeof` 는 상자를 재고 `strlen` 은 약속을 센다.** 중간에 널이 있으면 **6 과 2** 로 갈린다.
- ★★★ **문자열 리터럴은 정적 저장 기간**을 가진다. 함수가 끝나도 **살아 있다.**
- ★★★ **리터럴을 수정하면 UB** 다. C 에서 리터럴의 타입이 **`const` 가 아니라서** 기본 경고가 **0건**이다.
- ★★ **배열 초기화에 쓰면 복사**되고, **포인터 초기화에 쓰면 가리킨다.** 앞엣것만 고칠 수 있다.
- ★★ **`char s[3] = "abc"` 는 적법**하다 — **널만 안 들어간다.** 글자가 넘치면 그때는 **경고**다.
- ★★ **남는 칸은 0 으로 채워진다.** 쓰레기가 아니다.
- ★★★ **널 없는 배열에 `strlen`·`%s` 를 쓰면 UB** 인데 **평범한 실행은 조용히 맞는 답을 낼 수 있다.**
- ★★ **`strncpy` 는 널 종단을 보장하지 않는다.** 짧으면 0 으로 채우고, **딱 맞거나 길면 널이 없다.**
- ★ **문자열 비교는 `strcmp`** 다. `==` 는 **주소 비교**이고 그 결과는 **미명시**에 걸린다.
- ★ **읽기만 할 포인터는 `const char *`** 로 받는다 — **가장 싼 방어선**이다.

## 어디서 틀리나

### 1. ★★★ 「`char *p = "abc"` 도 문자열이니 고칠 수 있겠지」

- **UB** 다. 실측에서 **`run exit=139`** 로 죽었고 **gcc·clang 이 같았다.**
- ★★ **`-Wall -Wextra -pedantic` 이 0건**이다. **`-Wwrite-strings` 를 켜야** 보인다.
- ★ **고칠 것이면 `char p[]`**, 읽기만 하면 **`const char *p`**.
- ★ 「**죽어서 알았다**」는 운이다 — **정적 데이터가 쓰기 가능하게 매핑된 환경이면 조용히 성공**할 수도 있다.\
  ★ **이 문서는 그런 환경을 던지지 않았다**(이 머신에서는 언제나 139 였다).

### 2. ★★★ 「경고가 없으니 이 배열은 문자열이 맞겠지」

- **`char s[3] = "abc"` 는 경고가 0건**인데 **널이 없다.** 두 컴파일러 다 침묵했다.
- ★ **gcc 13 에는 그것을 잡는 옵션 자체가 없다.**
- ★★ 그 뒤 **`strlen` 이 3 을 내고 `%s` 가 `[abc]` 를 찍고 `run exit=0`** 이었다 — **두 창이 다 초록**이다.
- ★ **ASan 만이 `stack-buffer-overflow` 로 말한다.**

### 3. ★★ 「같은 글자면 같은 주소겠지 / 다를 테니 안전하겠지」

- **둘 다 틀린 단정**이다. **같은 글자 리터럴 둘은 다섯 벌 전부 공유**했고,\
  **꼬리 겹침은 벌마다 갈렸다**(gcc `-O0` 따로 / gcc `-O2` 공유 / clang 은 `-O0` 부터 공유).
- ★★ **한 벌만 돌리고 결론을 세우면 반대로 적는다.**
- ★ **`strcmp` 를 쓰면 이 질문 자체가 사라진다.**

### 4. ★★ 「`strncpy` 는 안전한 `strcpy` 다」

- **아니다.** **딱 맞거나 길면 널을 안 붙인다**(실측 `61 62 63 64 65`).
- ★ **짧으면 남는 칸을 전부 0 으로 채운다** — **비용이 `n` 에 비례**한다.
- ★ **gcc 는 두 건을 잡지만 clang 은 `-O2` 에서도 0건**이었다. **경고에 기대면 안 된다.**
- ★ 쓸 것이면 **`n-1` 만 복사하고 마지막 칸을 직접 0** 으로 — 그래도 **잘림은 안 알려 준다.**

### 5. ★★ 「`sizeof` 로 길이를 재면 되겠지」

- **배열이면 널까지 포함한 칸 수**이고(`sizeof "abc"` 자리의 배열은 4), **포인터면 8** 이다.
- ★ **중간에 널이 있으면 `sizeof` 6 대 `strlen` 2** 로 갈린다. **둘 다 맞고 질문이 다르다.**
- ★ 포인터에서 `sizeof` 가 8 인 이유는 [16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본이다.

### 6. ★ 「`%s` 로 찍어 보면 안다」

- **안 된다.** `abc`(널 있음)와 `abc`(널 없음)가 **화면에서 똑같이 보인다.**
- ★ **바이트를 찍는 것이 유일한 창**이다 — `for (k…) printf("%02x ", (unsigned char)buf[k]);`
- ★ 그리고 **`%s` 자체가 널 없는 배열에서는 UB** 다.

### 7. ★ 「함수가 끝나면 리터럴도 사라지겠지」

- **아니다.** 리터럴은 **정적 저장 기간**이라 `return "hello";` 는 **댕글링이 아니다.**
- ★ 댕글링이 되는 것은 **복사본을 돌려줄 때**다 — `char s[] = "hello"; return s;`\
  ★ 그쪽이 목록의 **57번 주제**다.

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 UB 칸이 가장 두껍다** — **리터럴 수정**이 본체이고, **널 없는 배열에 `strlen`/`%s`** 가 그 옆에 선다.\
★★ **두 번째로 두꺼운 칸은 미명시**다 — [16번 형제](../16-array-pointer-decay-and-function-parameters/)에서 **비어 있던 칸**이 여기서는 **다섯 벌로 갈리는 실측**으로 채워진다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| **표준** | 어느 구현에서도 같다 | **널 종단 관례**(문자열 = 첫 0 까지) · **리터럴의 정적 저장 기간** · **배열 초기화는 복사**(포인터 초기화는 가리킴) · **`char s[3] = "abc"` 가 적법한 것** · **남는 칸이 0 으로 채워지는 것** · **`strncpy` 의 계약**(n 바이트를 쓴다 · 널을 보장하지 않는다) · `sizeof` 와 `strlen` 이 **다른 질문**이라는 것 | `memcmp = 0` · `sizeof` 4·6 대 `strlen` 3·2 · `61 62 63`(널 없음) · `61 62 63 00 00 00` · `strncpy` 세 경우의 바이트 |
| **조건부 표준** | 매크로가 정의될 때만 | ★ **없다** — 널 종단과 리터럴에는 **매크로로 켜지고 꺼지는 보장이 없다.** ★ 굳이 대면 널 종단을 보장하는 **선택적 부속서의 `_s` 계열**이 있으나 **이 문서는 던지지 않았고** 그쪽은 목록의 **49번 주제**의 몫이다 | — |
| **구현 정의** | 문서화 의무가 있다 | 리터럴이 놓이는 **섹션**(`.rodata`) · 그 영역이 **쓰기 금지로 매핑되는 것**(그래서 139 로 죽는다) · `sizeof(char *)` = 8 · 실행 문자 집합에서 `'a'` 가 **0x61** 인 것 | `objdump -h` 의 `.rodata` ↔ `.data` · `sizeof lit = 8` · 바이트 덤프 `61 62 63` |
| ★★ **미명시** | 몇 가지 중 하나 · **문서화 의무도 없다** | ★★★ **같은 글자의 리터럴을 공유하는가** · ★★★ **꼬리를 겹치는가**(`"hello world"` 의 뒤 6바이트와 `"world"`) · 그래서 **리터럴끼리의 `==` 결과** | ★ **다섯 벌**(gcc `-O0`/`-O2`/`-O2 -fno-merge-constants` · clang `-O0`/`-O2`) — 공유는 다섯 벌 같고 **꼬리 겹침만 갈렸다** |
| ★★★ **UB (본체)** | 아무 일이나 | ★★★ **문자열 리터럴 수정**(`p[0] = 'A'`) · ★★★ **널 없는 배열에 `strlen`** · ★★ **널 없는 배열에 `%s`** · ★★ **`strncpy` 로 널이 안 붙은 버퍼를 문자열로 쓰는 것** · 빈 문자열에 `q[strlen(q)-1]`(★ **이 한 항목은 던지지 않았다**) | 평범한 실행 **`run exit=139`**(양쪽 컴파일러) · ASan **`WRITE memory access`** · **`run exit=1`** · ASan **`stack-buffer-overflow READ of size 4`**·`[32, 35) 'tight'` · 평범한 실행은 **`3`·`[abc]`·`run exit=0`** |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| **표준** | ★★★ **`char s[3] = "abc"` 에 경고가 0건**이다 — gcc·clang 둘 다. **표준이 허용하므로 진단할 것이 없다.** ★ **gcc 13 에는 그것을 잡는 옵션 자체가 없다**(주면 `unrecognized command-line option`) |
| **조건부 표준** | ★ **해당 없음** — 볼 것이 없으니 도구도 할 말이 없다 |
| **구현 정의** | ★ **컴파일러는 「어디에 놓았는지」를 말하지 않는다.** `objdump -h` 로 **링크 결과를 봐야** `.rodata` 가 보인다 |
| **미명시** | ★★ **어떤 경고도 「이 리터럴은 공유됩니다」라고 말하지 않는다.** 주소를 **직접 비교하는 프로그램**을 짜야 보이고, ★★ **한 벌만 돌리면 갈린다는 사실 자체가 안 보인다** — `-O` 와 컴파일러를 **둘 다 흔들어야** 나온다 |
| **UB** | ★★★ **`-Wall -Wextra -pedantic` 이 리터럴 수정에 0건**이다(`-Wwrite-strings` 를 켜야 하고, 그것도 **「수정」이 아니라 「초기화」를 잡는다**). ★★★ **널 없는 배열의 `strlen` 은 평범한 실행에서 `3` 을 내고 `exit=0`** 이다 — **ASan 만이 잡는다.** ★★ **ASan 도 리터럴 수정에는 반쪽**이다 — 「`can not provide additional info`」로 끝난다. ★★ **clang 은 `strncpy` 의 널 누락을 `-O2` 에서도 0건**이었다 |

- ★★ **이 표의 결론 네 줄**
  - ★★★ **이 주제에서 가장 조용한 자리는 「표준이 허용하는 것」과 「UB」가 맞닿는 지점**이다 —\
    **`char s[3] = "abc"`(경고 0건, 적법)** 에 **`strlen`(UB, exit=0)** 을 붙이면 **모든 창이 초록**이다.
  - ★★ **리터럴 수정은 UB 중에서도 특이하다** — **컴파일러는 침묵하고 OS 가 죽인다.**\
    ★ 「죽는 것」은 **보장이 아니라 이 플랫폼의 친절**이다.
  - ★★ **미명시 칸은 「여러 벌을 돌려야만」 보인다** — 한 벌짜리 실험은 **반대 결론을 준다.**
  - ★ **`-pedantic` 이 이 주제에서 더해 주는 것은 없다** — [16번 형제](../16-array-pointer-decay-and-function-parameters/)와 같고 [13번](../13-goto-cleanup-idiom/)·[14번 형제](../14-pointers-address-dereference-and-pointer-types/)와 다르다.

### 이 주제의 네 번째 창 — **바이트 격자**와 **다섯 벌**

- **컴파일 진단**은 `char s[3] = "abc"` 를 안 잡고, 리터럴 수정도 기본 플래그로는 안 잡는다.
- **화면 출력**은 거짓말을 한다 — 널이 있든 없든 **`%s` 는 똑같이 `abc`** 를 찍는다.
- **UBSan** 은 여기서 할 일이 별로 없다 — 리터럴 수정은 **타입·산술의 문제가 아니라 접근 권한의 문제**다.
- ★★ **그래서 창을 둘 더 썼다.**
  - ★★★ **바이트를 한 칸씩 찍는 것** — `61 62 63 00` 인가 `61 62 63` 인가. **널의 유무는 여기서만 보인다.**
  - ★★★ **같은 프로그램을 다섯 벌로 빌드해 주소를 비교하는 것** — **미명시 칸은 이 창으로만 열린다.**

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 형태 | 쓰면 안 되는 것 |
|---|---|---|
| 문자열을 고칠 것이다 | `char s[] = "abc";`(복사본) | `char *p = "abc";` |
| 읽기만 할 것이다 | `const char *p = "abc";` | `char *p = "abc";`(경고도 안 난다) |
| 함수에서 고정 문구를 돌려준다 | `return "hello";`(정적이라 안전) | `char s[] = "hello"; return s;`(댕글링) |
| 두 문자열이 같은지 본다 | `strcmp(a, b) == 0` | `a == b`(주소 비교 · **미명시**) |
| 배열의 칸 수를 센다 | `sizeof arr`(배열일 때만) | 포인터에 `sizeof`(8 이 나온다) |
| 글자 수를 센다 | `strlen(s)`(★ 널이 있을 때만) | 널이 없는 배열에 `strlen` |
| 크기를 딱 맞춘다 | `char s[] = "abc";`(컴파일러가 센다) | `char s[3] = "abc";`(널이 빠진다) |
| 잘라서 복사한다 | `n-1` 만 `strncpy` 하고 **끝 칸을 0 으로** | `strncpy(d, src, sizeof d)` 뒤 바로 `%s` |
| 널의 유무를 확인한다 | **바이트를 찍는다**(`%02x`) | `%s` 로 찍어 보기 |
| 리터럴 수정 여부를 확인한다 | **ASan** 또는 `-Wwrite-strings` | 기본 경고(0건이다) |
| 함수들의 계약을 따진다 | 목록의 **49번 주제** | 여기서 `strcpy`·`strcat` 까지 외우기 |

판단 규칙 두 줄.

- **고칠 것이면 복사본을 만든다**(`char s[]`), **안 고칠 것이면 `const` 를 붙인다**(`const char *`).
- **널이 있는지 모르면 문자열 함수를 부르지 않는다** — `strlen` 은 **모르면 그냥 걸어간다.**

## 핵심 문장

- ★★★ **문자열은 타입이 아니다.** `char arr[] = "abc"` 와 손으로 쓴 `{'a','b','c','\0'}` 의 바이트가 **`memcmp = 0`** 이었다.
- ★★★ **문자열 리터럴을 수정하면 UB** 다. 실측에서 **`run exit=139`**(gcc·clang 같음)로 죽었고,\
  **ASan 은 「`WRITE memory access`」라고 말하며 `run exit=1`** 이었다.
- ★★★ **그런데 `-Wall -Wextra -pedantic` 은 경고 0건**이다 — **C 에서 리터럴의 타입이 `const` 가 아니기 때문**이다.\
  **`-Wwrite-strings`** 를 켜야 보이고, 그것도 **`char *lit = "abc";` 라는 초기화 줄**을 잡는다.\
  ★ 이름은 gcc `-Wdiscarded-qualifiers` · clang `-Wincompatible-pointer-types-discards-qualifiers`.
- ★★★ **`char s[] = "abc"` 는 복사본이라 고칠 수 있다.** 배열 초기화에서는 **리터럴이 감쇠하지 않고 바이트로 쓰인다.**\
  ★ 그 규칙의 정본은 [16번 형제](../16-array-pointer-decay-and-function-parameters/)다.
- ★★★ **같은 글자 리터럴의 공유 여부는 미명시**다. 다섯 벌에서 **`a == b` 는 전부 공유**였지만\
  **꼬리 겹침(`"world"` 와 `"hello world"+6`)은 갈렸다.**\
  **gcc `-O0` 따로 · gcc `-O2` 공유 · gcc `-O2 -fno-merge-constants` 따로 · clang 은 `-O0` 부터 공유**다.
- ★★★ **`char s[3] = "abc"` 는 적법한데 널이 없다.** **gcc·clang 둘 다 경고 0건**이고,\
  ★ **gcc 13 에는 그것을 잡는 옵션 자체가 없다.**
- ★★★ **널 없는 배열에 `strlen` 을 쓰면 UB 인데 실측은 `3` 을 내고 `[abc]` 를 찍고 `run exit=0`** 이었다.\
  **ASan 만이 `stack-buffer-overflow READ of size 4`·`[32, 35) 'tight'` 로 말한다.**
- ★★ **`sizeof` 와 `strlen` 은 다른 질문에 답한다.** `char mid[] = "ab\0cd"` 에서 **6 과 2** 로 갈렸다.
- ★★ **`strncpy` 는 널을 안 붙일 수 있다** — **딱 맞거나 길면** `61 62 63 64 65` 로 끝난다.\
  ★ **gcc 는 두 건을 잡고**(`-Wstringop-truncation`, `-O2` 에서는 문구가 `__builtin_strncpy` 로 바뀐다)\
  ★★ **clang 은 `-O2` 에서도 0건**이었다.
- ★★ **리터럴은 정적 저장 기간**이라 **`return "hello";` 는 댕글링이 아니다.** 복사본을 돌려주면 댕글링이다.
- ★ **`%s` 로는 널의 유무가 안 보인다.** **바이트를 찍는 것**이 이 주제의 유일한 창이다.

## 관련 자료

- [`../README.md`](../README.md) — C 문법·API 주제 목록(이 주제는 20번)
- [`16-array-pointer-decay-and-function-parameters/`](../16-array-pointer-decay-and-function-parameters/) — ★★ **감쇠 규칙의 정본.**\
  그쪽은 「`char s[] = "hi"` 는 `sizeof` 3, `char *q = "hi"` 는 8」까지, **여기는 「왜 복사인가·고치면 무엇이 일어나나」부터**
- [`15-pointer-arithmetic-and-indexing/`](../15-pointer-arithmetic-and-indexing/) — `p + 1` 의 보폭과 `a[i]` == `*(a+i)`. **`strlen` 이 걷는 방식의 바탕**
- [`14-pointers-address-dereference-and-pointer-types/`](../14-pointers-address-dereference-and-pointer-types/) — `char *` 와 `const char *` 의 타입 규칙
- [`08-sizeof-alignment-and-offsetof/`](../08-sizeof-alignment-and-offsetof/) — ★ **`sizeof` 일반 규칙의 정본.** 여기는 **`strlen` 과 갈리는 자리**만
- [`13-goto-cleanup-idiom/`](../13-goto-cleanup-idiom/) — **표준이 본체인 형제.** 층 분포가 이 주제와 정반대다
- 목록의 **49번 주제** (`<string.h>` 문자열 함수와 함정) — ★★ **함수 계약의 정본.**\
  `strcpy`·`strcat`·`strncat`·`strlen` 의 경계 조건은 거기, 여기는 **널 종단이라는 약속 자체**
- 목록의 **56번 주제** (공간 위반 — 배열 밖 접근) — ★ **널 없는 배열을 걷는 것이 만드는 것**
- 목록의 **57번 주제** (시간 위반 — 댕글링) — 복사본을 돌려줄 때. **리터럴은 여기에 해당하지 않는다**
- 목록의 **58번 주제** (UB 를 잡는 도구) — `-Wwrite-strings`·ASan 을 **묶어서** 다루는 자리
- [목록의 **19번 주제**](../19-void-pointer-null-pointer-and-null/) (`void *`·널 포인터·`NULL`) — ★ **널 포인터와 널 문자는 다른 것**이다(`NULL` ↔ `'\0'`)

## 용어 풀이

- **널 종단(null-terminated)** — 끝을 값 0 인 바이트 하나로 표시하는 관례. 예: `"abc"` 는 `61 62 63 00` 네 바이트.
- **널 문자(`'\0'`)** — 값이 0 인 `char`. ★ **널 포인터(`NULL`)와 다른 것**이다 — 하나는 문자, 하나는 주소다.
- **문자열 리터럴(string literal)** — 소스에 쓴 `"abc"`. **`char` 배열**이고 **정적 저장 기간**을 가진다.\
  예: `char *p = "abc";` 의 `p` 는 프로그램이 끝날 때까지 유효한 곳을 가리킨다.
- **정적 저장 기간(static storage duration)** — 프로그램 시작부터 끝까지 사는 것.\
  예: 함수 안의 `return "hello";` 는 댕글링이 아니다.
- **복사본 초기화** — `char s[] = "abc"` 처럼 **배열을 선언하고 리터럴의 바이트로 채우는 것**.\
  예: `sizeof s` 가 4 이고 `s[0] = 'A'` 가 합법이다.
- **`.rodata`** — 읽기 전용 데이터가 놓이는 섹션. 예: `objdump -h` 에서 `.data` 와 따로 보인다.\
  ★ **구현 정의**이지 표준 용어가 아니다.
- **미명시 동작(unspecified behavior)** — 표준이 **여러 가능성 중 하나**를 허용하고 **어느 것인지 문서화도 요구하지 않는** 것.\
  예: 같은 글자 리터럴 둘이 같은 주소인가 — 다섯 벌 중 일부가 갈렸다.
- **구현 정의 동작(implementation-defined behavior)** — 구현이 고르되 **문서화 의무가 있는** 것.\
  예: 리터럴이 쓰기 금지 영역에 놓이는가.
- **미정의 동작(undefined behavior, UB)** — 표준이 **아무 요구도 하지 않는** 것. 예: 리터럴 수정 · 널 없는 배열에 `strlen`.
- **꼬리 겹침(tail merging)** — 긴 리터럴의 **뒷부분**을 짧은 리터럴로 재사용하는 배치.\
  예: `"world"` 를 `"hello world"` 의 7번째 바이트로 삼는 것.
- **`-Wwrite-strings`** — 리터럴의 타입을 `const char[]` 로 바꿔 **`char *` 로 받는 것**을 진단하게 하는 플래그.\
  ★ gcc 는 `-Wdiscarded-qualifiers`, clang 은 `-Wincompatible-pointer-types-discards-qualifiers` 라는 이름으로 낸다.
- **`-Wstringop-truncation`** — `strncpy` 가 **널을 붙이지 못하고 잘랐다**는 gcc 의 진단.\
  ★ `-O2` 에서는 함수 이름이 `__builtin_strncpy` 로 바뀌어 나온다.
- **`-Wexcess-initializers`** — 초기자가 배열보다 길 때 clang 이 내는 진단. ★ gcc 의 같은 진단에는 **플래그 이름이 없다.**
- **`-fno-merge-constants`** — 같은 상수를 합치지 말라고 gcc 에게 이르는 플래그.\
  예: `-O2` 에서 겹쳤던 꼬리가 이 플래그로 다시 따로 놓였다.

---

## 더 들어가면

- ★ **「리터럴을 고치면 죽는다」는 플랫폼 이야기다.** 표준이 말하는 것은 **UB 까지**이고,\
  정적 데이터가 **쓰기 가능하게 매핑된 환경**(일부 임베디드·구형 시스템)에서는 **조용히 성공**할 수 있다.\
  ★ **이 문서는 그런 환경을 던지지 않았다** — 이 머신에서는 다섯 번 던져 전부 139 였다.
- ★ **`-Wwrite-strings` 가 왜 기본이 아닌가**는 확인하지 않았다.\
  **기존 코드에서 경고가 쏟아진다**는 것이 흔한 설명이지만 ★ **컴파일러 문서로 확인하지 않았다.**
- ★★ **공유 판정이 갈린 축이 「최적화」뿐인지**는 못 가른다.\
  실측은 **gcc `-O0` 따로 / `-O2` 공유 / `-O2 -fno-merge-constants` 따로**였으니 **그 플래그가 관여한다**는 것까지는 말할 수 있지만,\
  **clang 이 `-O0` 부터 겹친 이유**(기본 배치 전략인지 다른 스위치인지)는 **던져 보지 않았다.**
- ★ **번역 단위가 여럿일 때의 공유**는 던지지 않았다. 이 문서의 실측은 **한 파일 안**의 리터럴들이다.\
  ★ **다른 `.c` 파일의 같은 리터럴이 링커에서 합쳐지는가**는 **다른 실험**이다.
- ★ **와이드 문자열(`L"abc"`)·`char8_t` 류**는 이 문서의 범위 밖이다. 널 종단 관례는 같지만 **칸의 크기가 다르다.**
- ★ **`strlen` 이 실제로 몇 바이트씩 걷는지**는 못 쟀다 — ASan 리포트의 `READ of size 4` 가\
  **가로채기의 셈법인지 실제 읽기 폭인지**를 가르려면 **어셈블리나 다른 도구**가 필요하다.
- ★ **`%s` 가 널 없는 배열에서 실제로 어디까지 찍는지**는 실측에서 **`[abc]` 에서 멈췄다** —\
  ★ 그 다음 바이트가 마침 0 이었다는 뜻이고 **다른 실행에서 같으리라는 보장은 없다.**
