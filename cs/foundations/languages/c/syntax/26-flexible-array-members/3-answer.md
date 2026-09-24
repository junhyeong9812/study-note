# c/syntax/26 — 유연 배열 멤버: 「**머리와 꼬리를 한 번에 잡는다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s26a.c`\~`s26i.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★ 5번 ASan 리포트의 **PID**(`==NNNN==`) · **`pc`/`bp`/`sp` 주소** · **모듈 오프셋**(`x+0x13f4`) · **BuildId** | ★★★ **`sizeof`·`offsetof` 수치 전부** — 4/4 · 8/5 · 16/16 · 8/4 |
> | 진단의 **줄 번호**(소스를 고치면 밀린다) | ★★★ **바이트 덤프** — `05 00 00 00 68 65 6c 6c 6f` · 복사본의 `00 00 00 00 00` |
> | — | ★★★ **ASan 의 에러 종류·`WRITE of size 1`·`0 bytes after 9-byte region`** |
> | — | ★★★ **종료 코드** — `cc exit=0` \| `cc exit=1` · `run exit=0` \| `run exit=1` |
> | — | ★★ **진단 본문과 플래그 이름** · **경고 건수** |
> | — | ★★ **`m0[1].len` = `1684234817`** — 같은 바이트를 읽으므로 결정적이다 |
>
> ★ **이 주제에서 흔들리는 것은 ASan 리포트의 주소뿐**이다 — 나머지는 재실행해도 한 글자도 같았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 네 가지 구조체의 `sizeof` 와 `offsetof` 를 나란히 재면 — **`Gap` 에서 8 대 5 로 갈린다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26a.c -o x ; ./x (cc exit=0 · run exit=0) =====
struct sizeof   offsetof   sizeof - offsetof
Msg    4        4          0
Gap    8        5          3
Wide   16       16         0
Old    8        4          4

★ sizeof 에 data 는 안 들어간다. Gap 은 sizeof 가 offsetof 보다 3 크다 (꼬리 패딩)
```

**왜 그런가**

- ★★★ **`sizeof` 에 유연 배열 멤버가 안 들어간다.** `struct Msg` 는 `int` 하나짜리와 똑같이 **4** 다.

  | 구조체 | `sizeof` | `offsetof(data)` | 차 | 왜 |
  |---|---|---|---|---|
  | `Msg { int len; char data[]; }` | 4 | 4 | 0 | 꼬리 패딩이 없다 |
  | `Gap { int n; char c; char data[]; }` | **8** | **5** | **3** | ★ `c` 뒤에 **꼬리 패딩 3바이트** |
  | `Wide { char c; double d; char data[]; }` | 16 | 16 | 0 | `d`(8바이트, 정렬 8) 뒤라 남는 자리가 없다 |
  | `Old { int len; char data[1]; }` | 8 | 4 | **4** | `data[0]` 1바이트 + 꼬리 패딩 3 |

- ★★★ **갈리는 것은 `Gap` 이고 차이는 3** 이다. `data` 는 **5번 바이트**에서 시작하는데 구조체 정렬이 4라 `sizeof` 가 **8** 로 올라간다.
- ★★★ **`sizeof + n` 은 절대 모자라지 않는다.** `sizeof` 가 세는 5\~7번 세 바이트는 **`data` 가 쓸 자리**이므로 `sizeof + n` 은 그 셋을 **두 번 센다** — 늘 넉넉한 쪽으로 틀린다.\
  ★ `offsetof + n` 이 **꼭 맞는 값**이다(`Gap`, n=5 에서 **10**, `sizeof + n` 은 **13**).
- ★ **`Old` 의 차이 4 는 두 조각**이다 — `data[0]` **한 바이트**가 `sizeof` 에 들어 있고, 그 뒤에 **꼬리 패딩 3바이트**가 더 있다.
- ★ **층을 가르면** — 「`sizeof` 에 FAM 이 안 들어간다」는 **표준**이고, 「꼬리 패딩이 몇 바이트냐」는 **구현 정의**다([22번 형제](../22-struct-padding-and-alignment/)가 정본).

### 2. 한 번의 할당으로 머리와 꼬리를 묶으면 — **`05 00 00 00 68 65 6c 6c 6f`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26b.c -o x ; ./x (cc exit=0 · run exit=0) =====
len=5  data=hello
malloc 한 바이트 = sizeof(struct Msg)(4) + 5 = 9
꼭 필요한 바이트  = offsetof(data)(4) + 5 = 9
바이트 : 05 00 00 00 68 65 6c 6c 6f
         ^^^^^^^^^^^ len(4바이트)  ^^^^^^^^^^^^^^ data 5바이트
```

**왜 그런가**

- ★★ **바이트 덤프가 `05 00 00 00 68 65 6c 6c 6f`** 다.\
  앞 4바이트가 `len = 5`(리틀 엔디언), 뒤 5바이트가 `hello`(`68 65 6c 6c 6f`)다 — **머리와 꼬리가 한 덩어리**임이 그대로 보인다.
- ★ **`sizeof *m + 5` 와 `offsetof(…, data) + 5` 가 둘 다 9** 다. `struct Msg` 에는 **꼬리 패딩이 없어서** 두 값이 같다.\
  ★ **1번의 `Gap` 이었다면 13 과 10 으로 갈렸을 것**이다 — 「여기서 같았다」를 「언제나 같다」로 읽으면 안 된다.
- ★★ **`char *data;` 방식과 견주면**

  | | `char *data;`(두 번 할당) | `char data[];`(FAM) |
  |---|---|---|
  | 할당·해제 | 2회 · 2회 | **1회 · 1회** |
  | 구조체 크기 | 포인터 8바이트가 더 든다 | **0바이트** |
  | 머리와 꼬리의 거리 | 멀다(캐시가 갈린다) | **붙어 있다** |
  | 꼬리만 늘리기 | ★ `realloc` 으로 된다 | ★★ **통째로 다시 잡아야 한다** |
  | 복사 | ★ 대입이 포인터를 복사한다(얕은 복사) | ★★★ 대입이 **꼬리를 빠뜨린다**(4번) |

- ★ **`sizeof *m` 을 쓴 이유** — 타입 이름을 두 번 안 적으면 **타입을 바꿔도 이 줄을 안 고친다.** `malloc` 관용구의 표준형이다(목록의 **37번 주제**).

### 3. 다섯 가지 배치를 던져 보면 — **에러 둘 · 확장 셋(전부 `cc exit=0`)** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26c.c -o x (cc exit=1) =====
s26c.c:1:23: error: flexible array member in a struct with no named members
    1 | struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
      |                       ^
s26c.c:2:23: error: flexible array member not at end of struct
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                       ^
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s26c.c -o x (cc exit=1) =====
s26c.c:1:23: error: flexible array member 'd' not allowed in otherwise empty struct
    1 | struct NoName  { char d[]; };           /* (1) 이름 있는 멤버가 하나도 없다 */
      |                       ^
s26c.c:2:23: error: flexible array member 'd' with type 'char[]' is not at the end of struct
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                       ^
s26c.c:2:32: note: next field declaration is here
    2 | struct NotLast { char d[]; int n; };    /* (2) 마지막이 아니다 */
      |                                ^
2 errors generated.
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26c2.c -o x (cc exit=0) =====
s26c2.c:2:25: warning: invalid use of structure with flexible array member [-Wpedantic]
    2 | struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
      |                         ^
s26c2.c:3:13: warning: invalid use of structure with flexible array member [-Wpedantic]
    3 | struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
      |             ^~~
s26c2.c:4:27: warning: ISO C forbids zero-size array ‘d’ [-Wpedantic]
    4 | struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */
      |                           ^
```

```text
===== gcc -std=c17 -Wall -Wextra s26c2.c -o x (cc exit=0) =====
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic s26c2.c -o x (cc exit=0) =====
s26c2.c:2:25: warning: 'c' may not be nested in a struct due to flexible array member [-Wflexible-array-extensions]
    2 | struct Nest { struct Ok c; };           /* (3) 다른 구조체가 값으로 품는다 */
      |                         ^
s26c2.c:3:16: warning: 'struct Ok' may not be used as an array element due to flexible array member [-Wflexible-array-extensions]
    3 | struct Ok   arr[4];                     /* (4) 배열 원소로 쓴다 */
      |                ^
s26c2.c:4:29: warning: zero size arrays are an extension [-Wzero-length-array]
    4 | struct Zero { int n; char d[0]; };      /* (5) 길이 0 배열 */
      |                             ^
3 warnings generated.
```

**왜 그런가**

- ★★★ **앞 파일의 둘은 진짜 에러**이고 `cc exit=1` 이다.

  | 무엇 | gcc | clang |
  |---|---|---|
  | 이름 있는 멤버가 없다 | `flexible array member in a struct with no named members` | `flexible array member 'd' not allowed in otherwise empty struct` |
  | 마지막이 아니다 | `flexible array member not at end of struct` | `flexible array member 'd' with type 'char[]' is not at the end of struct` |

  ★ **clang 은 두 번째에 `note: next field declaration is here` 를 덧붙여** 범인 줄까지 가리킨다.
- ★★★ **뒤 파일의 셋은 경고뿐**이고 **`cc exit=0`** 이다 — 중첩 · 배열 원소 · 길이 0 배열.
- ★★★ **`-pedantic` 을 빼면 gcc 는 진단이 0건**이 된다 — 블록이 **배너뿐**이다. 셋이 조용히 들어온다.
- ★★ **플래그 이름이 다르다.**

  | | gcc | clang |
  |---|---|---|
  | 중첩·배열 원소 | `[-Wpedantic]` | `[-Wflexible-array-extensions]` |
  | 길이 0 배열 | `[-Wpedantic]` | `[-Wzero-length-array]` |

  ★★ **gcc 는 전부 `[-Wpedantic]` 으로 뭉친다** — 그래서 **확장 하나만 골라 끄거나 켤 수가 없다.** clang 은 된다.
- ★ **「이름 있는 멤버가 하나는 있어야 하는」 이유** — FAM 은 `sizeof` 에 0바이트로 들어가므로, 그것뿐이면 **크기 0 짜리 구조체**가 된다. C 의 객체는 **크기가 1 이상**이어야 한다.

### 4. 이 구조체를 대입하면 — **`len` 만 가고 `data` 는 `00 00 00 00 00` · 여섯 벌 전부 침묵** ★★★ 본체

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26d.c -o x ; ./x (cc exit=0 · run exit=0) =====
원본   : len=5 data=hello
복사본 : len=5 data=
data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
memcpy(sizeof *a) 도 같다 — 옮기는 것은 4 바이트뿐이다
```

```text
===== 구조체 대입이 꼬리를 옮기나 — 네 벌 + 도구 (exit=0) =====
gcc   -O0                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -O2                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
clang -O0                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
clang -O2                          cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -fsanitize=address,undefined cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
gcc   -D_FORTIFY_SOURCE=2 -O2      cc=0 경고 0건 run=0 | data 5바이트 : 00 00 00 00 00   <- 원본은 68 65 6c 6c 6f 였다
```

**왜 그런가**

- ★★★ **복사본의 `len` 은 `5` 인데 `data` 는 `00 00 00 00 00`** 이다.\
  **구조체 대입은 `sizeof` 만큼만 옮기는데 `sizeof(struct Msg)` 가 4** 이기 때문이다 — 1번의 규칙이 그대로 여기로 온다.
- ★★★ **여섯 벌 전부 경고 0건 · `run exit=0` · 같은 출력**이다.

  | 벌 | 경고 | `run exit` |
  |---|---|---|
  | gcc `-O0` · gcc `-O2` | 0건 | 0 |
  | clang `-O0` · clang `-O2` | 0건 | 0 |
  | gcc `-fsanitize=address,undefined` | 0건 | 0 |
  | gcc `-D_FORTIFY_SOURCE=2 -O2` | 0건 | 0 |

- ★★★ **이것은 UB 가 아니다.** `*b = *a` 는 **완전히 적법한 표준 동작**이고 옮기는 바이트 수도 표준이 정한 그대로다.\
  ★ **그래서 도구가 말릴 근거가 없다** — 잘못된 코드가 아니라 **내 기대가 틀린 것**이다.\
  ★★ 이것이 이 주제의 가장 중요한 한 줄이다: **「어느 도구가 잡나」를 물을 자리가 아니라 「왜 아무도 안 잡나」를 알아야 하는 자리**다.
- ★★ **`memcpy(b, a, sizeof *a)` 도 똑같다.** 같은 수(`4`)를 쓰니 같은 결과다.
- ★ **옳은 복사법** — `memcpy(dst, src, sizeof *src + src->len);`\
  ★ 꼬리 길이는 **내 구조체의 `len` 멤버**가 알고 있다. 그것을 안 넣으면 컴파일러는 알 길이 없다.
- ★★ **제5의 상태인 이유** — 컴파일도 되고 실행도 되고 `len` 도 맞다. 틀린 것은 값이 아니라 「**무엇이 복사됐는가**」다.\
  ★ 세 창(진단 · 실행 출력 · sanitizer)이 전부 정상이고, **복사본의 `data` 를 바이트로 찍어야만** 보인다.

### 5. 꼬리를 한 칸 넘겨 쓰면 — **그냥 빌드는 무증상 · ASan 은 `heap-buffer-overflow`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26e.c -o x ; ./x (cc exit=0 · run exit=0) =====
여기까지는 정상이다 : hello
★ 한 칸 넘겨 썼다 — 이 줄이 보이나? 빌드에 달렸다
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -fsanitize=address s26e.c -o x ; ASAN_OPTIONS=strip_path_prefix=/src/ ./x 2>&1 | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
여기까지는 정상이다 : hello
=================================================================
==1011083==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x502000000019 at pc 0x621d859883f5 bp 0x7ffed6c90380 sp 0x7ffed6c90370
WRITE of size 1 at 0x502000000019 thread T0
    #0 0x621d859883f4 in main (x+0x13f4) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)
    #1 0x75d55202a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x75d55202a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x621d85988204 in _start (x+0x1204) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)

0x502000000019 is located 0 bytes after 9-byte region [0x502000000010,0x502000000019)
allocated by thread T0 here:
    #0 0x75d5524fd9c7 in malloc libsanitizer/asan/asan_malloc_linux.cpp:69
    #1 0x621d8598832e in main (x+0x132e) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)
    #2 0x75d55202a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #3 0x75d55202a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #4 0x621d85988204 in _start (x+0x1204) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3)

SUMMARY: AddressSanitizer: heap-buffer-overflow (x+0x13f4) (BuildId: cb3166a5fdc38669d84d4f672e4605647ad835c3) in main
```

**왜 그런가**

- ★★★ **그냥 빌드하면 아무 일도 안 난다.** `run exit=0` 이고 **다음 줄까지 찍힌다** — 9바이트 할당의 바로 뒤 한 바이트는 대개 **힙의 여유 공간**이다.\
  ★★ **「안 터졌다」는 「안전하다」가 아니다.**
- ★★★ **ASan 은 정확히 잡는다** — `AddressSanitizer: heap-buffer-overflow` · **`WRITE of size 1`** · **`0 bytes after 9-byte region`** · `run exit=1`.
- ★★★ **리포트가 적는 `9-byte region` 이 바로 `sizeof *m + n` = 4 + 5** 다. **리포트만 보고 할당식을 역산할 수 있다.**
- ★★ **`setvbuf(stdout, NULL, _IONBF, 0)` 가 없으면** ASan 이 `abort()` 할 때 **버퍼에 남은 `printf` 줄이 통째로 사라진다.**\
  순서가 밀리는 게 아니라 **없어진다** — 터미널에서 본 대로 옮겨 적으면 재현이 안 되는 자리다.
- ★★ **컴파일러가 못 보는 이유** — `n` 이 실행 시간에 정해지고, 무엇보다 **FAM 의 길이는 타입에 아예 없다.** 정적 분석이 볼 정보 자체가 없다.
- ★ **흔들리는 칸** — `==NNNN==` PID · `pc`/`bp`/`sp` 주소 · 모듈 오프셋 · BuildId.\
  **안 흔들리는 칸** — 에러 종류 · `WRITE of size 1` · `9-byte region` · `run exit=1`.

### 6. C99 이전의 「길이 1 배열」과 나란히 놓으면 — **출력도 진단도 같고 할당만 3바이트 더** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26f.c -o x ; ./x (cc exit=0 · run exit=0) =====
New sizeof=4  Old sizeof=8   (Old 는 data[1] 한 바이트를 포함한다)
New 할당식 sizeof+n       = 9
Old 할당식 sizeof-1+n     = 12   <- ★ 3 바이트 더 잡았다
꼭 필요한 바이트 offsetof+n = 9

둘 다 읽힌다 : new=hello old=hello
★ 출력도 같고 진단도 없다 — 갈리는 것은 할당 산술과 ★ 표준이 보장하느냐 ★ 뿐이다
```

**왜 그런가**

- ★★★ **출력이 같다**(둘 다 `hello`). **진단도 같다** — `-Wall -Wextra -pedantic` 에서 **둘 다 0건**이다.
- ★★ **갈리는 것은 둘뿐**이다.

  | | `char data[];`(FAM) | `char data[1];`(관용구) |
  |---|---|---|
  | `sizeof` | **4** | **8** |
  | 할당식 | `sizeof + n` = **9** | `sizeof - 1 + n` = **12** |
  | 꼭 필요한 바이트 | 9 | 9 |
  | 표준이 보장하나 | ★ **C99 부터 보장** | ★★ **아니다** — `data[1]` 을 넘겨 쓰는 것은 형식상 배열 밖 접근이다 |

- ★★ **`- 1` 은 `data[0]` 한 바이트를 빼는 것**이다. 그런데 `sizeof` 안에는 **꼬리 패딩 3바이트**도 들어 있는데 그건 못 뺀다 — 그 셋도 `data` 가 쓸 자리라 **두 번 세어진다.**\
  그래서 **12 바이트**를 잡아 **3바이트를 버린다.** 안전하지만 낭비다.
- ★ **`- 1` 을 지우면** 13 바이트를 잡는다 — **더 잡는 쪽이라 안전하다.** 「버그를 고쳤다」가 아니라 **낭비를 늘린 것**이다.\
  ★ 새로 쓰는 코드라면 **FAM 으로 바꾸는 쪽**이 맞다.
- ★ **두 방식이 실행으로 안 갈린다**는 사실 자체가 중요하다 — **「돌려 봤더니 되던데」로는 이 둘을 못 가른다.**

### 7. `-D_FORTIFY_SOURCE=2 -O2` 는 무엇을 보나 — **크기를 아는 정적 객체만 본다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -D_FORTIFY_SOURCE=2 s26g.c -o x (cc exit=0) =====
In file included from /usr/include/string.h:548,
                 from s26g.c:2:
In function ‘strcpy’,
    inlined from ‘main’ at s26g.c:11:5:
/usr/include/x86_64-linux-gnu/bits/string_fortified.h:79:10: warning: ‘__builtin___memcpy_chk’ offset [4, 9] is out of the bounds [0, 4] of object ‘g_new’ with type ‘struct New’ [-Warray-bounds=]
   79 |   return __builtin___strcpy_chk (__dest, __src, __glibc_objsize (__dest));
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s26g.c: In function ‘main’:
s26g.c:7:19: note: ‘g_new’ declared here
    7 | static struct New g_new;        /* 크기를 아는 객체 — data 는 0바이트다 */
      |                   ^~~~~
In function ‘strcpy’,
    inlined from ‘main’ at s26g.c:12:5:
/usr/include/x86_64-linux-gnu/bits/string_fortified.h:79:10: warning: ‘__builtin___memcpy_chk’ forming offset [8, 9] is out of the bounds [0, 8] of object ‘g_old’ with type ‘struct Old’ [-Warray-bounds=]
   79 |   return __builtin___strcpy_chk (__dest, __src, __glibc_objsize (__dest));
      |          ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s26g.c: In function ‘main’:
s26g.c:8:19: note: ‘g_old’ declared here
    8 | static struct Old g_old;        /* 크기를 아는 객체 — data 는 1바이트다 */
      |                   ^~~~~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -D_FORTIFY_SOURCE=2 s26f.c -o x (cc exit=0) =====
```

**왜 그런가**

- ★★ **정적 객체에서는 둘 다 잡는다.**

  | 객체 | 진단 | `cc exit` |
  |---|---|---|
  | `static struct New g_new;`(FAM, `data` 0바이트) | `offset [4, 9] is out of the bounds [0, 4] of object 'g_new'` | **0** |
  | `static struct Old g_old;`(`data[1]`, 8바이트) | `forming offset [8, 9] is out of the bounds [0, 8] of object 'g_old'` | **0** |

  ★ 둘 다 `[-Warray-bounds=]` 이고 **`cc exit=0`** 이다 — 넘치는 것이 확실한데도 빌드가 통과한다.
- ★★★ **`malloc` 으로 잡은 객체에서는 경고 0건**이다(`s26f.c` 블록이 배너뿐이다).
- ★★★ 그래서 갈리는 축은 「**FAM 이냐 길이 1 배열이냐」가 아니라 「그 객체의 크기를 컴파일러가 아느냐**」다.\
  ★ **내가 처음에 세운 전제가 뒤집힌 자리**다 — 「관용구는 잡히고 FAM 은 안 잡힌다」를 기대하고 던졌는데 **둘 다 같았다.**
- ★★ **실전에서 뜻하는 것** — FAM 구조체는 **8번 때문에 거의 언제나 `malloc` 으로만** 만들어진다.\
  즉 **정적 진단이 볼 수 있는 형태로는 거의 안 쓰인다.**
- ★ **경계를 지키는 것은 둘뿐**이다 — **내 코드의 `len` 검사**와 **ASan**(5번).

### 8. 초기자로 만들려 하면 — **정적은 확장으로 통과 · 자동은 에러** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26h.c -o x (cc exit=1) =====
s26h.c:5:28: warning: initialization of a flexible array member [-Wpedantic]
    5 | static struct Msg g = { 3, { 'a', 'b', 'c' } };   /* (1) 정적 저장 기간 */
      |                            ^
s26h.c:5:28: note: (near initialization for ‘g.data’)
s26h.c: In function ‘main’:
s26h.c:8:25: warning: initialization of a flexible array member [-Wpedantic]
    8 |     struct Msg m = { 3, { 'a', 'b', 'c' } };      /* (2) 자동 저장 기간 */
      |                         ^
s26h.c:8:25: note: (near initialization for ‘m.data’)
s26h.c:8:25: error: non-static initialization of a flexible array member
s26h.c:8:25: note: (near initialization for ‘m’)
```

**왜 그런가**

- ★★ **세 줄이 각각 다르다.**

  | 줄 | 결과 |
  |---|---|
  | `static struct Msg g = { 3, {'a','b','c'} };` | ★ **경고** `[-Wpedantic]` + `note: (near initialization for 'g.data')` — **확장으로 통과** |
  | `struct Msg m = { 3, {'a','b','c'} };` | ★ **에러** `non-static initialization of a flexible array member` |
  | `struct Msg z = { 3 };` | ★ **아무 말 없음** |

  전체 `cc exit=1` 이다(자동 쪽 에러 때문).
- ★★ **정적과 자동이 갈리는 이유** — 정적 객체는 **컴파일 시간에 크기를 정해 실행 파일에 자리를 잡아 둘 수 있다.**\
  자동 객체는 **스택 프레임의 크기가 함수 진입 때 정해져야** 하는데, 초기자로 꼬리를 늘리면 그 크기를 타입에서 읽을 수 없다.
- ★ **`{ 3 }` 은 통과하지만 쓸모가 없다** — 그 객체의 `data` 에는 **쓸 공간이 0바이트**다. **「되는 것」과 「쓸모 있는 것」이 다르다.**
- ★★ **그래서 FAM 구조체는 거의 언제나 할당 저장 기간**에 놓인다([28번 형제](../28-choosing-among-four-storage-durations/)).\
  ★ [25번 형제](../25-incomplete-types-and-opaque-struct/)의 opaque struct 가 같은 자리로 떠밀리는 것과 **원인은 다르고 결과는 같다.**
- ★ **정적 쪽만 남기면 `cc exit=0`** 이 된다 — **확장이 조용히 들어오는 자리**가 하나 더 생기는 것이다(3번과 같은 모양).

### 9. 한 덩어리에 셋을 담고 인덱싱하면 — **`m0 + 1` 은 4바이트 · `m0[1].len` 은 `"abcd"`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s26i.c -o x ; ./x (cc exit=0 · run exit=0) =====
sizeof(struct Msg) = 4 · 내가 쓴 stride = 12
m0 + 1 은 4 바이트 뒤다   <- ★ stride 가 아니다
m0[1].len = 1684234817   <- 두 번째 칸의 len 이 아니다

손으로 stride 를 곱해 읽으면
  칸 0 : len=0 data=Abcdefgh
  칸 1 : len=1 data=Bbcdefgh
  칸 2 : len=2 data=Cbcdefgh
```

**왜 그런가**

- ★★★ **`sizeof(struct Msg) = 4` 인데 내가 쓴 stride 는 12** 다. 그런데 **`m0 + 1` 은 4바이트만 간다.**\
  포인터 산술은 **`sizeof` 를 걸음으로 쓴다**([15번 형제](../15-pointer-arithmetic-and-indexing/)가 정본) — 그리고 그 `sizeof` 에는 **꼬리가 없다.**
- ★★★ **`m0[1].len` 이 `1684234817`** 이다. 16진으로 **`0x64636261`** — 리틀 엔디언으로 읽으면 **`61 62 63 64` = `"abcd"`** 다.\
  ★ **칸 0 의 `data` 한복판을 `int` 로 읽은 값**이다.
- ★ **이 수가 알아보기 쉬웠던 것은 운**이다. `data` 를 **`memset` 으로 0 으로 채워 뒀다면 `m0[1].len` 이 `0`** 으로 나와 **그럴듯해 보였을 것**이다.\
  ★★ 그래서 **「값이 이상해 보이나」로 판단하면 안 된다.**
- ★★ **제대로 읽으려면 손으로 stride 를 곱한다** — `(struct Msg *)((char *)buf + i * stride)`. 그러면 세 칸이 `A…`/`B…`/`C…` 로 제대로 읽힌다.
- ★ **옳은 형태는 포인터 배열**(`struct Msg *arr[3]`)이다. 각각을 따로 `malloc` 하면 인덱싱이 정상으로 돌아온다.
- ★ **ASan 도 이것은 못 잡는다** — `m0[1]` 이 읽는 자리는 **할당 범위 안**이기 때문이다(5번과 다른 점이다).

### 10. 왜 마지막이어야 하고 왜 혼자 있으면 안 되나 ★★

**왜 그런가**

- ★★★ **마지막이어야 하는 이유** — FAM 뒤에 다른 멤버가 오면 **그 멤버의 오프셋을 정할 수 없다.**\
  꼬리의 길이는 **실행 시간에 정해지는데** 오프셋은 **컴파일 시간에 고정**되어야 한다. 둘이 양립하지 않는다.
- ★★★ **이름 있는 멤버가 최소 하나 필요한 이유** — FAM 은 `sizeof` 에 **0바이트**로 들어간다.\
  그것뿐이면 **크기 0 짜리 구조체**가 되는데, C 의 객체는 **크기가 1 이상**이어야 서로 다른 주소를 가질 수 있다.
- ★★ **다른 구조체가 값으로 품으면 무엇이 무너지나** — 바깥 구조체의 `sizeof` 에는 **꼬리가 0바이트로 들어간다.**\
  그 뒤에 멤버가 오면 **꼬리를 쓰는 순간 그 멤버를 덮어쓴다.** gcc·clang 은 **확장으로 받아 주지만**(경고 + `cc exit=0`) 실제로 쓰면 그렇게 무너진다.
- ★★ **`struct Ok arr[4];` 가 무너지는 이유는 9번과 같은 이유**다 — **stride 가 `sizeof` 인데 거기에 꼬리가 없다.**\
  ★ 즉 「배열 원소로 쓰기」와 「`m + 1`」은 **같은 규칙의 앞뒤 면**이다.
- ★★ **표준이 막는 것과 구현이 받아 주는 것**

  | | 표준이 **에러**로 막는다 | 구현이 **확장**으로 받는다(경고 · `cc exit=0`) |
  |---|---|---|
  | 무엇 | ① 이름 있는 멤버가 없다 ② 마지막이 아니다 | ③ 다른 구조체가 값으로 품기 ④ 배열 원소 ⑤ 길이 0 배열 ⑥ 정적 FAM 초기자 |

  ★ **①②는 타입 자체가 성립하지 않는 것**이고, **③\~⑥은 성립하는데 쓰면 무너지는 것**이다 — 그래서 심각도가 갈린다.

### 11. 다섯 층과 무게중심 — **표준이 본체 · 그런데 가장 위험한 자리는 층 밖이다** ★★★

**왜 그런가**

| 층 | 이 주제에서 | 근거 |
|---|---|---|
| ★★★ **표준 (본체)** | **`sizeof` 에 FAM 이 안 들어가는 것** · **마지막 멤버여야 하는 것** · **이름 있는 멤버가 최소 하나 필요한 것** · **자동 저장 기간에서 초기화 못 하는 것** · **구조체 대입이 `sizeof` 만큼만 옮기는 것** · 포인터 산술이 `sizeof` 를 걸음으로 쓰는 것 · C99 부터인 것 | `sizeof(struct Msg)` = **4** · 에러 2건 두 컴파일러(`cc exit=1`) · `non-static initialization` 에러 · 복사본 `data` 가 **`00 00 00 00 00`**(여섯 벌 동일) · `m0 + 1` 이 **4바이트** |
| **조건부 표준** | ★ **해당 없음** | — |
| ★★ **구현 정의** | ★★ **꼬리 패딩** — `sizeof` 가 `offsetof` 보다 큰가·얼마나 · 진단 문구와 플래그 이름 · **어떤 확장을 받아 주는가** | `Msg` 4/4 · **`Gap` 8/5** · `Wide` 16/16 · `Old` 8/4 · gcc 는 `[-Wpedantic]` 로 뭉치고 clang 은 `[-Wflexible-array-extensions]`·`[-Wzero-length-array]` 로 가른다 |
| **미명시** | ★ **꼬리 패딩 바이트의 값**([22번 형제](../22-struct-padding-and-alignment/)가 정본) | ★ 이 편은 **패딩 값 자체를 던지지 않았다** |
| ★ **UB** | ★ **할당 범위를 넘겨 읽고 쓰는 것**(`m->data[n]`) · **`m0[1]` 처럼 `sizeof` 로 건너뛴 자리를 읽는 것** | ASan `heap-buffer-overflow` · `WRITE of size 1` · `0 bytes after 9-byte region` · `run exit=1` / `m0[1].len` = `1684234817` |

- ★★ 비어 있는 칸은 「**조건부 표준**」이다. **미명시 칸은 있지만 얇고**, 그 내용은 22번 형제가 정본이다.
- ★★ 가장 두꺼운 칸은 「**표준**」, 두 번째는 「**구현 정의**」(꼬리 패딩)다.
- ★★★ **4번의 사고는 어느 칸에도 안 들어간다.** UB 가 아니고 구현 정의도 아니고 미명시도 아니다 — **표준이 정한 그대로 동작한 것**이다.\
  ★★★ 그 답이 말해 주는 것: **다섯 층 표는 「이 코드가 틀렸나」를 가를 뿐 「내 기대가 틀렸나」는 못 가른다.**\
  ★ 그래서 이 주제에서는 **층 표를 다 외워도 4번을 못 피한다** — 피하는 법은 **`sizeof` 를 쓰는 연산을 전부 의심하는 습관**이다.
- ★★ **도구가 침묵하는 자리**

  | 층 | 침묵하는 자리 |
  |---|---|
  | 표준 | ★★★ **`*b = *a` 를 아무도 안 말린다** — 적법한 동작이라 말릴 근거가 없다(여섯 벌 경고 0건) |
  | 조건부 표준 | 해당 없음 |
  | 구현 정의 | ★★ **`sizeof` 와 `offsetof` 가 갈린다고 말해 주는 경고가 없다** — 둘을 직접 찍어야 보인다 |
  | 미명시 | ★ **패딩 바이트 값은 어떤 도구도 안 본다** |
  | UB | ★★ **정적 진단은 `malloc` 객체를 못 본다**(7번). ★ **`m0[1]` 은 ASan 도 못 잡는다**(할당 범위 안이다) |

- ★★★ **「종료 코드가 0인데 ill-formed」는 다섯 군데**다 — ① 중첩 ② 배열 원소 ③ 길이 0 배열 ④ 정적 FAM 초기자 ⑤ g++ 의 FAM 전부.\
  ★ 다섯 자리 **모두 `-pedantic` 이라야 보이고, 보여도 `cc exit=0`** 이다. 강제하려면 **`-pedantic-errors`** 다.

### 12. 경계 — 어디까지가 이 주제인가 ★

| 무엇 | 정본 |
|---|---|
| **왜 패딩이 생기나** · **패딩 바이트의 값** | [22번 형제](../22-struct-padding-and-alignment/) |
| **`sizeof`·`_Alignof`·`offsetof` 라는 도구** | [8번 형제](../08-sizeof-alignment-and-offsetof/) |
| **`a[i]` 가 `*(a+i)` 이고 걸음이 `sizeof` 인 것** | [15번 형제](../15-pointer-arithmetic-and-indexing/) |
| **구조체 선언·초기화·지정 초기자** | [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) |
| **배열이 포인터로 감쇠하는 규칙** | [16번 형제](../16-array-pointer-decay-and-function-parameters/) |
| **`malloc`/`realloc` 의 계약과 실패 처리** | 목록의 **37번 주제** |
| **배열 밖 접근이 「성공할 수 있는 것」인 이유** | 목록의 **56번 주제** |
| **sanitizer 와 경고 플래그** | 목록의 **58번 주제** |
| **저장 기간을 고르는 법** | [28번 형제](../28-choosing-among-four-storage-durations/) |

- ★ **「크기를 모르는 배열」과 무엇이 다른가** — [25번 형제](../25-incomplete-types-and-opaque-struct/)의 `extern char msg[];` 는 **타입 전체가 불완전**해서 `sizeof` 가 **에러**다.\
  ★ 여기는 **구조체가 완전하고 꼬리만 비어 있다** — `sizeof` 가 에러가 아니라 「**뜻이 다른 값**」을 준다. **훨씬 더 조용하다.**
- ★ **이 주제가 끝까지 책임지는 것 셋**
  - ★★★ **`sizeof` 에 꼬리가 없다는 것**과, 그래서 **`sizeof` 를 쓰는 모든 연산**(대입·`memcpy`·포인터 산술·인덱싱)**이 꼬리를 빠뜨린다는 것.**
  - ★★★ **그 사고가 UB 가 아니라 표준 동작이라 원리상 도구가 못 잡는다는 것.**
  - ★★ **할당 산술 두 가지**(`sizeof + n` 과 `offsetof + n`)와 **꼬리 패딩이 그 둘을 가르는 것.**
- ★★ **C++ 에서 갈라지는 자리** — C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) 쪽이다.\
  **유연 배열 멤버는 C++ 표준에 없다** — g++ 는 `ISO C++ forbids flexible array member` 로 **경고만** 내고 `cc exit=0` 으로 받아 준다.\
  ★ 즉 C 에서 「**표준 기능」이던 것이 C++ 에서는 「확장**」이 된다. 공용 헤더에 두면 한쪽만 이식된다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s26a.c` (26-a) | `sizeof`/`offsetof` 격자 — `Msg` **4/4** · `Gap` **8/5** · `Wide` **16/16** · `Old` **8/4** | gcc 1벌 |
| `s26b.c` (26-b) | 한 번의 할당 · 바이트 덤프 **`05 00 00 00 68 65 6c 6c 6f`** · `sizeof + 5` = `offsetof + 5` = **9** | gcc 1벌 |
| `s26c.c`·`s26c2.c` (26-c) | 에러 2건(`cc exit=1`) · 확장 3건(**경고 · `cc exit=0`**) · **`-pedantic` 을 빼면 gcc 진단 0건** · clang 은 플래그 이름을 갈라 준다 | gcc 2벌(`-pedantic` 유·무) · clang 2벌 |
| `s26d.c` (26-d) | 구조체 대입이 **머리만** 옮긴다 — `len=5` · `data` **`00 00 00 00 00`** | ★★ **6벌**(gcc·clang × `-O0`/`-O2` + ASan·UBSan + FORTIFY) — **전부 경고 0건 · `run exit=0`** |
| `s26e.c` (26-e) | 그냥 빌드 **무증상 · `run exit=0`** · ASan **`heap-buffer-overflow` · `WRITE of size 1` · `0 bytes after 9-byte region` · `run exit=1`** | gcc 2벌(평문·ASan) |
| `s26f.c` (26-f) | FAM **9바이트** 대 관용구 **12바이트**(3 낭비) · 꼭 필요한 것 **9** · **출력도 진단도 같다**(경고 0건) | gcc 2벌(실행 · FORTIFY) |
| `s26g.c` (26-g) | 크기를 아는 **정적 객체**는 FORTIFY 가 **둘 다 잡는다**(`[-Warray-bounds=]` · **`cc exit=0`**) | gcc 1벌 |
| `s26h.c` (26-h) | 정적 초기자는 **경고로 통과**(확장) · 자동 초기자는 **에러** · `{ 3 }` 은 **침묵** · `cc exit=1` | gcc 1벌 |
| `s26i.c` (26-i) | `m0 + 1` 이 **4바이트** · `m0[1].len` = **`1684234817`**(= `0x64636261` = `"abcd"`) · 손으로 곱한 stride 로는 정상 | gcc 1벌 |
| `s26c2.c` → g++ (26-j) | **C++ 에서는 FAM 이 확장**이다 — `ISO C++ forbids flexible array member` 외 2건, **`cc exit=0`** | g++ 1벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3)에서만** 그렇다.

- ★★ **꼬리 패딩의 크기**(`Gap` 의 3바이트) — **구현 정의**다. 정렬 규칙이 다르면 값이 달라진다.
- ★★ **`sizeof` 값 전부**(4 · 8 · 16 · 8) — 타입 크기와 정렬에 달렸다.
- ★★ **어떤 확장을 받아 주는가** — 중첩·배열 원소·길이 0 배열·정적 초기자는 **gcc·clang 의 선택**이다.
- ★ **진단 문구와 플래그 이름 전부.** 특히 **gcc 가 `[-Wpedantic]` 으로 뭉치는 것**은 버전에 따라 바뀔 수 있다.
- ★ **`m0[1].len` = `1684234817`** — 리틀 엔디언이라 나온 값이다. 빅엔디언이면 다른 수가 나온다.
- ★ **`-D_FORTIFY_SOURCE=2` 의 동작** — glibc 의 구현에 달렸다.

**`sizeof` 에 FAM 이 안 들어가는 것 · 마지막이어야 하는 것 · 이름 있는 멤버가 필요한 것 · 구조체 대입이 `sizeof` 만큼 옮기는 것 · 포인터 산술이 `sizeof` 를 걸음으로 쓰는 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `realloc` 으로 FAM 구조체를 늘리는 것 · **`double data[]` 처럼 정렬이 올라가는 FAM** ·\
  `union` 안의 FAM 구조체 · **gcc 14 의 `-Wflex-array-member-not-at-end` 를 실제로 켠 결과**(gcc 13 에는 옵션 자체가 없다 — `cc exit=1` 로 확인) ·\
  `__builtin_object_size` 를 **직접** 부르는 것 · **빅엔디언 머신**(9번의 `"abcd"` 가 뒤집히는지) · **`-Os`·`-O3`**(4번은 `-O0`/`-O2` 까지만 흔들었다).
- ★ **못 잰 것** — **「한 번 할당이 두 번 할당보다 빠른가」.**\
  이 문서는 **할당 횟수와 구조체 크기만** 셌고 **시간은 재지 않았다.** 캐시 지역성까지 걸리는 측정이라\
  **부하 조건·데이터 크기를 먼저 정해야** 성립한다 — 「안 돌려 본 것」이 아니라 「**측정 방법이 전제를 요구해 잴 수 없는 것**」이라 따로 적는다.\
  ★★ **그래서 이 문서 어디에도 「더 빠르다」는 말이 없다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **gcc 가 확장 셋을 계속 `[-Wpedantic]` 으로 뭉치는지** — 갈라 주면 3번의 결론이 바뀐다.
- ★★ **gcc 14 이상에서 `-Wflex-array-member-not-at-end` 가 무엇을 더 잡는지** — 확장 ③이 경고에서 에러로 올라갈 수 있다.
- ★★ **`-D_FORTIFY_SOURCE` 가 할당된 객체까지 보게 됐는지**(지금은 못 본다). 7번의 결론이 바뀌는 자리다.
- ★ **진단 문구 전부** · **ASan 리포트의 형식**(5번의 `9-byte region` 표기).
- **`sizeof` 규칙·금지 두 가지·대입의 동작은 다시 돌릴 필요가 없다** — C99 이후 바뀐 적이 없다.
