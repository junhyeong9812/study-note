# c/syntax/27 — 복합 리터럴: 「**이름 없는 변수를 식 한가운데 세운다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · **g++ 13.3.0** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s27a.c`\~`s27e.c` 와 `s27f.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **UB 가 걸린 문항(4·5·6)은 「컴파일러 2 × 최적화 3」 여섯 벌**을 돌렸다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **UB 격자의 스택 잔해 두 칸** — gcc `-O1` 의 `289313584 32767` · clang `-O2` 의 `518988784 32765` | ★★★ **「여섯 벌이 서로 다르다」는 사실 자체** — 어느 벌이 어느 모양인지는 재실행에도 같았다 |
> | ★ 7번 ASan 리포트의 **PID** · **`pc`/`bp`/`sp`** · **스택 주소** · **모듈 오프셋** · **BuildId** | ★★★ **경고 건수 격자** — gcc 1 / 5 / 7 · clang 0 / 0 / 0 |
> | 진단의 **줄 번호**(소스를 고치면 밀린다) | ★★★ **종료 코드** — `cc exit` 여섯 벌 전부 0 · `run exit=139`(1번) · `run exit=1`(7번) |
> | — | ★★ **주소 동일성 판정** — `a0==a1` = 1 · `a1==a2` = 1 |
> | — | ★★ **`sizeof (int[]){1,2,3}` = 12** · `(struct P){.y=5}` → `(0,5)` |
> | — | ★★ **진단 본문·플래그 이름** · ASan 의 `stack-use-after-scope`·`READ of size 4`·`This frame has 1 object(s)` |
>
> ★★ **스택 잔해 두 칸에 대해 대조할 것은 숫자가 아니라 「쓰레기가 나온다」는 성질**이다.\
> ★ 나머지는 재실행해도 한 글자도 같았다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 복합 리터럴로 다섯 가지를 해 보면 — **넷은 되고 문자열 리터럴만 죽는다(`run exit=139`)** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27b.c -o x ; ./x (cc exit=0 · run exit=139) =====
1) 좌변값이다 — 멤버를 고칠 수 있다
   (99,2)
2) 배열 복합 리터럴 — sizeof 가 배열 크기다
   sizeof (int[]){1,2,3} = 12 · 원소 3 개
3) 지정 초기자를 쓰면 나머지는 0 이다
   (0,5)
4) (char[]){"abc"} 는 고칠 수 있다
   Xbc
5) "abc" 는 문자열 리터럴이라 고치면 죽는다 — 다음 줄에서 끝난다
```

**왜 그런가**

- ★★★ **`1)` — `(99,2)`.** 주소를 잡아(`&`) 멤버를 고쳤다(`p->x = 99`). **복합 리터럴은 좌변값**이라 둘 다 된다.
- ★★ **`2)` — `sizeof (int[]){1,2,3}` 가 `12`, 원소 `3`개.**\
  ★ **포인터로 감쇠하지 않는다** — 이것은 **배열 객체 그 자체**이고, `sizeof` 의 피연산자 자리는 감쇠가 일어나지 않는 자리다([16번 형제](../16-array-pointer-decay-and-function-parameters/)가 정본).
- ★★ **`3)` — `(0,5)`.** 지정 초기자로 `.y` 만 줬더니 `.x` 는 **0** 이 됐다([21번 형제](../21-struct-declaration-initialization-and-designated-initializers/)의 규칙 그대로다).
- ★★★ **`4)` 와 `5)` 가 정반대다.**

  | | 무엇인가 | 고칠 수 있나 | 결과 |
  |---|---|---|---|
  | `(char[]){"abc"}` | ★ **내 `char` 배열 객체** | **된다** | `Xbc` |
  | `"abc"` | ★ **문자열 리터럴** | ★★ **안 된다** | **`run exit=139`**(SIGSEGV) |

  ★ `5)` 의 마지막 줄이 **안 찍혔다** — 그 줄에 닿기 전에 죽었다.
- ★★ **`setvbuf(stdout, NULL, _IONBF, 0)` 가 없으면** 죽기 전 네 항목이 **통째로 사라진다.**\
  stdout 은 파이프·파일로 받으면 **블록 버퍼**라, 프로세스가 비정상 종료하면 버퍼가 flush 되지 않는다.
- ★ **층** — `1)`\~`4)` 는 전부 **표준**이고, `5)` 는 **UB**(문자열 리터럴 수정)다. 「죽는다」는 보장이 아니라 **이 구현에서 일어난 일**이다([20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본).

### 2. 왜 값이 아니라 객체인가 — **좌변값이기 때문이다** ★★

**왜 그런가**

- ★★★ **리터럴과 다른 점은 「객체가 생긴다」는 것**이다.

  | | `3` · `"abc"` 의 값 | `(struct P){1,2}` |
  |---|---|---|
  | `&` 를 붙일 수 있나 | `&3` 은 ★ **에러** | ★ **된다** |
  | 고칠 수 있나 | `3 = 4` 는 ★ **에러** | ★ **된다** |
  | 저장 공간 | 없다(상수) | ★ **실제로 잡힌다** |

  ★ `"abc"` 는 예외적으로 객체이긴 하지만 **수정이 UB** 다 — 그래서 `(char[]){"abc"}` 와 갈린다(1번).
- ★★ **좌변값이라는 말이 여기서 뜻하는 것 두 가지** — ① **주소를 잡을 수 있다** ② **대입의 왼쪽에 놓일 수 있다**(멤버 대입 포함).
- ★ **저장 공간은 실제로 잡힌다.** 블록 안이면 **그 블록에 들어갈 때**, 파일 스코프면 **프로그램이 시작할 때**다.
- ★★ **새 저장 기간을 만들지 않는다.** 복합 리터럴은 **자동이거나 정적**이고, 그 규칙은 [28번 형제](../28-choosing-among-four-storage-durations/)의 것 그대로다.\
  ★ **C23 부터 `static` 을 붙여 정적으로 고를 수 있게 됐다**(8번).
- ★ **「이름표가 없는 변수」는 어디까지 맞나** — **수명과 좌변값성까지는 정확히 맞다.**\
  ★ 틀리기 시작하는 곳은 「**몇 개 생기나**」다 — 루프를 돌아도 **하나**였다(6번). 이름 있는 변수라면 선언이 한 번이니 당연한데, 복합 리터럴은 **식 안에 있어서** 「매번 새로 생길 것 같은」 착각을 부른다.

### 3. 파일 스코프와 블록 스코프에 하나씩 놓으면 — **`10 20` · `1 2` · `(2,4)` 셋 · 주소가 같다** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27a.c -o x ; ./x (cc exit=0 · run exit=0) =====
파일 스코프 : 10 20   <- 프로그램이 끝날 때까지 산다
블록 스코프 : 1 2   <- 블록이 끝난 뒤에 읽었다
루프 세 번  : (2,4) (2,4) (2,4)
주소가 같나 : a0==a1 1 · a1==a2 1
```

**왜 그런가**

- ★★★ **`파일 스코프 : 10 20`** — 파일 스코프의 복합 리터럴은 **정적 저장 기간**이라 프로그램이 끝날 때까지 산다. **믿을 수 있는 값**이다.
- ★★★ **`블록 스코프 : 1 2`** — **믿으면 안 되는 값**이다.\
  `set()` 의 닫는 중괄호에서 그 객체가 죽었고, `keep` 은 **댕글링 포인터**다. **읽는 것 자체가 UB** 이며\
  ★★ **이 값이 맞아 보이는 것은 이 빌드(`-O0`)의 우연**이다 — 4번에서 흔들면 갈린다.
- ★★ **`루프 세 번 : (2,4) (2,4) (2,4)`** — 세 포인터가 같은 값을 준다.
- ★★ **`주소가 같나 : a0==a1 1 · a1==a2 1`** — **세 포인터가 같은 객체**를 가리킨다. 6번에서 다시 본다.
- ★ **경고는 1건**이고 플래그는 **`[-Wdangling-pointer=]`** 다 — `storing the address of local variable '({anonymous})' in 'keep'`.\
  ★ gcc 가 그 객체를 **`({anonymous})`** 라고 부른다 — **이름 없는 객체**라는 것이 진단 문구에 그대로 드러난다.

### 4. 같은 소스를 여섯 벌로 던지면 — **여섯 칸이 전부 다르고 두 칸이 맞아 보인다** ★★★ 본체

**출력**

```text
===== 블록이 끝난 복합 리터럴을 읽으면 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : 1 2 | (2,4) (2,4) (2,4)
gcc   -O1 : -1225351904 32766 | (0,0) (0,0) (0,0)
gcc   -O2 : 0 0 | (0,0) (0,0) (0,0)
clang -O0 : 1 2 | (2,4) (2,4) (2,4)
clang -O1 : 0 0 | (2,4) (2,4) (2,4)
clang -O2 : 672393392 32766 | (2,4) (2,4) (2,4)
```

**왜 그런가**

- ★★★ **여섯 칸이 전부 다르다.**

  | 벌 | 블록 스코프 | 루프 세 번 |
  |---|---|---|
  | gcc `-O0` | ★ **`1 2`**(맞아 보인다) | `(2,4)` 셋 |
  | gcc `-O1` | `289313584 32767`(스택 잔해) | `(0,0)` 셋 |
  | gcc `-O2` | `0 0` | `(0,0)` 셋 |
  | clang `-O0` | ★ **`1 2`**(맞아 보인다) | `(2,4)` 셋 |
  | clang `-O1` | `0 0` | `(2,4)` 셋 |
  | clang `-O2` | `518988784 32765`(스택 잔해) | `(2,4)` 셋 |

- ★★★ **「맞아 보이는」 칸은 2개**다 — **gcc `-O0` 과 clang `-O0`.**\
  ★★★ **하필 가장 흔한 개발 빌드**다. 디버그 빌드로 테스트하고 릴리스로 배포하면 **거기서 처음 갈린다.**
- ★★ **「루프 세 번」 열은 컴파일러로 갈린다** — gcc 는 `-O1` 부터 `(0,0)`, clang 은 세 벌 다 `(2,4)` 다.\
  ★ **두 열이 서로 다른 축으로 갈린다** — 블록 스코프 열은 최적화 수준으로, 루프 열은 컴파일러로 갈렸다.
- ★ **`cc exit` 는 여섯 벌 전부 0**, **`run exit` 도 여섯 벌 전부 0** 이다. **UB 인데 빌드도 실행도 다 통과한다.**
- ★★ **실행마다 바뀌는 칸은 두 개** — gcc `-O1` 과 clang `-O2` 의 숫자다(스택 잔해).\
  ★ **대조할 것은 그 숫자가 아니라 「여섯 벌이 서로 다르다」는 성질**이고, **어느 벌이 어느 모양인가**(맞아 보임 / 쓰레기 / `0 0`)는 재실행에도 같았다.
- ★★★ **「`-O0` 에서 잘 되던데」가 틀리는 이유** — 그것은 **여섯 벌 중 하나를 본 것**이고, 하필 **가장 그럴듯한 거짓말을 하는 벌**이다.\
  ★ UB 에는 **「어디에 넣으면 갈린다」는 처방이 없다** — 값·조건·누산을 다 던져 보고 **갈린 자리를 적는 것**뿐이다.

### 5. 경고를 컴파일러·최적화별로 세면 — **gcc 1/5/7 대 clang 0/0/0** ★★★

**출력**

```text
===== 같은 소스에 경고가 몇 건 나오나 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc   -O0 : cc exit=0 · 경고 1건 : [-Wdangling-pointer=] 
gcc   -O1 : cc exit=0 · 경고 5건 : [-Wdangling-pointer=] [-Wuninitialized] 
gcc   -O2 : cc exit=0 · 경고 7건 : [-Wdangling-pointer=] [-Wuninitialized] 
clang -O0 : cc exit=0 · 경고 0건 : 
clang -O1 : cc exit=0 · 경고 0건 : 
clang -O2 : cc exit=0 · 경고 0건 : 
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s27a.c -o x (cc exit=0) =====
s27a.c: In function ‘set’:
s27a.c:9:10: warning: storing the address of local variable ‘({anonymous})’ in ‘keep’ [-Wdangling-pointer=]
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |     ~~~~~^~~~~~~~~~~~~~~~~~~
s27a.c:9:23: note: ‘({anonymous})’ declared here
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |                       ^
s27a.c:6:18: note: ‘keep’ declared here
    6 | static struct P *keep;
      |                  ^~~~
s27a.c: In function ‘main’:
s27a.c:15:5: warning: using a dangling pointer to an unnamed temporary [-Wdangling-pointer=]
   15 |     printf("블록 스코프 : %d %d   <- 블록이 끝난 뒤에 읽었다\n", keep->x, keep->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:9:23: note: unnamed temporary defined here
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |                       ^
s27a.c:15:5: warning: using a dangling pointer to an unnamed temporary [-Wdangling-pointer=]
   15 |     printf("블록 스코프 : %d %d   <- 블록이 끝난 뒤에 읽었다\n", keep->x, keep->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:9:23: note: unnamed temporary defined here
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |                       ^
s27a.c:15:5: warning: ‘<U2090>.y’ is used uninitialized [-Wuninitialized]
   15 |     printf("블록 스코프 : %d %d   <- 블록이 끝난 뒤에 읽었다\n", keep->x, keep->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:9:23: note: ‘({anonymous})’ declared here
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |                       ^
s27a.c:15:5: warning: ‘<U2090>.x’ is used uninitialized [-Wuninitialized]
   15 |     printf("블록 스코프 : %d %d   <- 블록이 끝난 뒤에 읽었다\n", keep->x, keep->y);
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:9:23: note: ‘({anonymous})’ declared here
    9 |     keep = &(struct P){1, 2};               /* 블록 스코프 → 자동 저장 기간 */
      |                       ^
s27a.c:19:5: warning: ‘<U13f0>.y’ is used uninitialized [-Wuninitialized]
   19 |     printf("루프 세 번  : (%d,%d) (%d,%d) (%d,%d)\n",
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   20 |            a[0]->x, a[0]->y, a[1]->x, a[1]->y, a[2]->x, a[2]->y);
      |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:18:51: note: ‘({anonymous})’ declared here
   18 |     for (int i = 0; i < 3; i++) a[i] = &(struct P){i, i * i};
      |                                                   ^
s27a.c:19:5: warning: ‘<U13f0>.x’ is used uninitialized [-Wuninitialized]
   19 |     printf("루프 세 번  : (%d,%d) (%d,%d) (%d,%d)\n",
      |     ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
   20 |            a[0]->x, a[0]->y, a[1]->x, a[1]->y, a[2]->x, a[2]->y);
      |            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
s27a.c:18:51: note: ‘({anonymous})’ declared here
   18 |     for (int i = 0; i < 3; i++) a[i] = &(struct P){i, i * i};
      |                                                   ^
```

**왜 그런가**

- ★★★ **경고 건수 격자**

  | | `-O0` | `-O1` | `-O2` | 플래그 |
  |---|---|---|---|---|
  | gcc | **1건** | **5건** | **7건** | `[-Wdangling-pointer=]` · `[-Wuninitialized]` |
  | clang | **0건** | **0건** | **0건** | — |

- ★★★ **clang 18 은 여섯 벌 전부 침묵**이다. 「경고 0건이니 괜찮다」가 **여기서 깨진다.**\
  ★★ **실무에서 뜻하는 것** — **clang 만 쓰는 빌드에서는 이 주제 전체가 정적 진단에 안 걸린다.**\
  방어선은 **ASan 하나**(7번)이거나, **gcc 로도 한 번 컴파일해 보는 것**이다.
- ★★★ **gcc 는 최적화를 올려야 더 본다**(1 → 5 → 7).\
  `-O0` 에서는 **`[-Wdangling-pointer=]` 1건**뿐이고, `-O1` 부터 **`[-Wuninitialized]`** 가 붙는다 —\
  ★ 최적화 단계에서 **값 흐름 분석**이 돌아야 「이 객체는 이미 죽어서 안 쓰인 값이다」가 보이기 때문이다.
- ★★ **「빠른 빌드로 검사하고 느린 빌드로 배포」가 거꾸로**다. 검사용 빌드야말로 `-O2` 로 한 번 돌려 봐야 한다.
- ★ **`cc exit` 는 여섯 벌 전부 0** 이다.\
  ★★ 규칙 「경고 0건은 종료 코드를 같이 봐야 뜻이 있다」가 여기서는 **한 걸음 더 간다** — **경고 건수와 종료 코드를 둘 다 봐도 이 UB 는 안 잡힌다.**\
  clang 쪽은 **(0건, exit 0)** 이고 gcc 쪽은 **(7건, exit 0)** 인데 **결과는 같은 바이너리가 나온다.**

### 6. 루프에서 주소를 세 개 모으면 — **셋이 같은 객체다(`a0==a1` = 1)** ★★★

**왜 그런가**

- ★★★ **`a[0] == a[1]` 이 `1`, `a[1] == a[2]` 도 `1`** 이다. **세 포인터가 한 객체**를 가리킨다.

  ```text
     기대 — 객체 세 개                       실제 — 객체 하나
     ------------------------------------   ------------------------------------
     a[0] -> (0,0)                          a[0] ─┐
     a[1] -> (1,1)                          a[1] ─┼─> ★ 같은 객체
     a[2] -> (2,4)                          a[2] ─┘

     값만 보면       (2,4) (2,4) (2,4)       <- 「덮어쓴 건가?」로 읽힌다
     주소를 비교하면  a0==a1 1 · a1==a2 1    <- ★ 「애초에 하나였다」
  ```

- ★★★ **값만 보고는 두 가설을 못 가른다.**\
  「루프 마지막 값이 앞의 것을 덮어썼다」와 「애초에 객체가 하나였다」는 **같은 출력**을 낸다.\
  ★ 앞엣것이면 「포인터를 어디서 잘못 넣었나」를 찾게 되고, 뒤엣것이면 「배열을 따로 만들어야겠다」가 답이다 — **고칠 곳이 다르다.**
- ★★★ 그래서 이 주제의 네 번째 창은 「**포인터끼리 `==` 로 비교하는 것**」이다.\
  세 창(컴파일 진단 · 실행 출력 · sanitizer)이 전부 이 질문에 답하지 않는다 — UB 가 아니라 「**몇 개 생겼나**」를 묻는 것이기 때문이다.\
  ★ 비용은 `printf("%d", a[0]==a[1])` **한 줄**이다.
- ★★ **관찰이지 보장이 아니다.** 이 구현에서 **여섯 벌 전부 하나**였고 ASan 도 `This frame has 1 object(s)` 라고 적었지만,\
  **「매 반복마다 새 객체」로 잡는 구현이 있어도 이 문서는 그것을 반증하지 못한다.** 그래서 **미명시 칸**에 넣는다.
- ★ **객체를 정말 셋 만들려면** — **이름 있는 배열**을 쓴다.

  ```text
     struct P buf[3];
     for (int i = 0; i < 3; i++) { buf[i] = (struct P){i, i*i}; a[i] = &buf[i]; }
  ```

  ★ 그러면 `buf` 가 **선언된 스코프만큼** 살고 세 주소가 서로 다르다.

### 7. 죽은 복합 리터럴을 ASan 으로 읽으면 — **`stack-use-after-scope` · `run exit=1`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -fsanitize=address s27d.c -o x ; ASAN_OPTIONS=strip_path_prefix=/src/ ./x 2>&1 | sed -n '1,/^SUMMARY/p' (cc exit=0 · run exit=1) =====
블록이 끝난 복합 리터럴을 읽는다
=================================================================
==1123143==ERROR: AddressSanitizer: stack-use-after-scope on address 0x79dfbe300024 at pc 0x5edb2d4f9476 bp 0x7fff9ea21bb0 sp 0x7fff9ea21ba0
READ of size 4 at 0x79dfbe300024 thread T0
    #0 0x5edb2d4f9475 in main (x+0x1475) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)
    #1 0x79dfc042a1c9 in __libc_start_call_main ../sysdeps/nptl/libc_start_call_main.h:58
    #2 0x79dfc042a28a in __libc_start_main_impl ../csu/libc-start.c:360
    #3 0x5edb2d4f91c4 in _start (x+0x11c4) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)

Address 0x79dfbe300024 is located in stack of thread T0 at offset 36 in frame
    #0 0x5edb2d4f9298 in main (x+0x1298) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec)

  This frame has 1 object(s):
    [32, 40) '<unknown>' <== Memory access at offset 36 is inside this variable
HINT: this may be a false positive if your program uses some custom stack unwind mechanism, swapcontext or vfork
      (longjmp and C++ exceptions *are* supported)
SUMMARY: AddressSanitizer: stack-use-after-scope (x+0x1475) (BuildId: 49350468275f3bc46b1dbfcfa2fa4c157f2b23ec) in main
```

**왜 그런가**

- ★★★ **에러 이름은 `stack-use-after-scope`** 이고 **`run exit=1`** 이다.\
  「해제 후 사용」이 아니라 「**스코프가 끝난 뒤 사용**」이라고 정확히 구분해 부른다.
- ★★ **`READ of size 4`** — `keep->x` 를 읽었다(`int` 4바이트).\
  **`Address … is located in stack of thread T0 at offset 36 in frame`** — `main` 의 스택 프레임 안 **오프셋 36** 이다.
- ★★★ **`This frame has 1 object(s)`** 라고 적고 **`[32, 40) '<unknown>'`** 을 가리킨다.\
  ★★ **8바이트짜리 객체가 하나**다 — `struct P` 가 `int` 둘이니 8바이트다.\
  ★★★ **6번의 「객체가 하나」를 ASan 이 독립적으로 확인해 준 셈**이다. 이름이 없어 `'<unknown>'` 이라고 부른다.
- ★ **흔들리는 칸** — `==NNNN==` PID · `pc`/`bp`/`sp` · 스택 주소(`0x7f5f49b00024`) · 모듈 오프셋(`x+0x1475`) · BuildId.\
  **안 흔들리는 칸** — `stack-use-after-scope` · `READ of size 4` · `offset 36 in frame` · `This frame has 1 object(s)` · `[32, 40)` · `run exit=1`.
- ★★ **clang 빌드에서 특히 중요한 이유** — 5번에서 clang 의 정적 진단이 **0건**이었다.\
  ★ 즉 **clang + ASan 없음** 조합에서는 이 주제의 UB 를 **아무것도 안 잡는다.** ASan 이 **유일한 자동 방어선**이다.

### 8. 복합 리터럴에 `static` 을 붙이면 — **gcc 만 되고 `-std=c17` 에서도 `cc exit=0`** ★★

**출력**

```text
===== gcc -std=c2x -Wall -Wextra -pedantic -O2 s27e.c -o x ; ./x (cc exit=0 · run exit=0) =====
static 복합 리터럴 : 1 2
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27e.c -o x (cc exit=0) =====
s27e.c: In function ‘set’:
s27e.c:7:50: warning: ISO C forbids storage class specifiers in compound literals before C2X [-Wpedantic]
    7 | static void set(void) { keep = &(static struct P){1, 2}; }
      |                                                  ^
```

```text
===== clang -std=c2x -Wall -Wextra -pedantic s27e.c -o x (cc exit=1) =====
s27e.c:7:34: error: expected expression
    7 | static void set(void) { keep = &(static struct P){1, 2}; }
      |                                  ^
1 error generated.
```

**왜 그런가**

- ★★★ **세 가지 결과**

  | 명령 | 결과 | `cc exit` |
  |---|---|---|
  | `gcc -std=c2x -pedantic -O2` | 실행되어 **`1 2`** | **0** |
  | `gcc -std=c17 -pedantic` | **경고 1건** `ISO C forbids storage class specifiers in compound literals before C2X [-Wpedantic]` | **0** |
  | `clang -std=c2x -pedantic` | **에러** `expected expression` | **1** |

- ★★★ **`-O2` 인데도 `1 2` 가 나오는 이유** — `static` 을 붙이면 그 객체가 **정적 저장 기간**이 된다.\
  블록이 끝나도 **안 죽으므로 UB 자체가 사라진다.** 4번의 격자가 **문법 한 낱말로 무의미해진다.**
- ★★★ **`-std=c17` 에서도 gcc 가 받아 준다** — 경고 1건에 **`cc exit=0`**, 바이너리가 나온다.\
  ★★ 「`-std=c17` 로 돌렸으니 C17 코드다」가 **여기서 깨진다.** `-std=` 는 **강제가 아니라 기본값 선택**이다.\
  ★ **막으려면 `-pedantic-errors`** 다.
- ★★★ **clang 18 은 `-std=c2x` 에서도 못 알아듣는다** — 파서가 `static` 을 만나 **`expected expression`** 으로 죽는다(`cc exit=1`).\
  ★ **「C23 기능이니까 쓰면 된다」가 아니다** — **기능마다 구현 지원이 다르다.**
- ★ **C23 부터**이고, **지금 쓰면 한쪽에서만 빌드된다.** 이식성을 생각하면 아직 이르다.
- ★ **이식되는 대안** — **이름 있는 `static` 변수**를 만든다.

  ```text
     static void set(void) { static struct P p = {1, 2}; keep = &p; }
  ```

  ★ 어느 컴파일러에서도 빌드되고 수명도 같다.
- ★★★ **덤으로 — `-std=` 철자 자체도 컴파일러마다 다르다.**\
  **`-std=c23` 은 gcc 13 에 없고**(`unrecognized command-line option` · **`cc exit=1`** · **경고 0건**) **clang 18 은 받아 준다**(`cc exit=0`).\
  ★★ 「경고 0건」만 세면 **컴파일이 아예 안 된 것을 「깨끗한 빌드」로** 기록한다 — **종료 코드를 같이 봐야** 뜻이 산다.\
  ★ 그래서 이 문서는 **둘 다 받는 `-std=c2x`** 로 고정했다.

```text
===== 같은 철자의 -std= 를 두 컴파일러에 던져 본다 — s27e.c 대신 최소 프로그램으로 (exit=0) =====
gcc   -std=c17  : cc exit=0 · 경고 0건  
clang -std=c17  : cc exit=0 · 경고 0건  
gcc   -std=c2x  : cc exit=0 · 경고 0건  
clang -std=c2x  : cc exit=0 · 경고 0건  
gcc   -std=c23  : cc exit=1 · 경고 0건  gcc: error: unrecognized command-line option ‘-std=c23’; did you mean ‘-std=c2x’?
clang -std=c23  : cc exit=0 · 경고 0건  
```

### 9. 함수 인자 자리에 쓰면 — **셋 다 정상 · 경고 0건 · 이것이 본래 용도다** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic s27c.c -o x ; ./x (cc exit=0 · run exit=0) =====
db       retries=3 timeout=500ms tag=primary
cache    retries=0 timeout=50ms tag=(없음)
log      retries=0 timeout=0ms tag=(없음)
sum = 15
```

**왜 그런가**

- ★★ **지정 초기자와 짝을 이루면 「이름 붙은 인자」처럼 읽힌다.**

  | 호출 | 결과 |
  |---|---|
  | `(struct Opt){.retries=3, .timeout_ms=500, .tag="primary"}` | `retries=3 timeout=500ms tag=primary` |
  | `(struct Opt){.timeout_ms=50}` | `retries=0 timeout=50ms tag=(없음)` |
  | `(struct Opt){0}` | `retries=0 timeout=0ms tag=(없음)` |

- ★ `(struct Opt){0}` 하나가 「**전부 기본값**」이다. 안 적은 멤버는 **0**(포인터면 널 포인터)이 된다.
- ★ **`sum((int[]){1,2,3,4,5}, 5)` 는 `15`** 다. 배열도 그 자리에서 만들어 넘길 수 있다.
- ★★★ **이 용법은 안전하다.** 4번의 UB 와 갈리는 점은 하나다 — **주소를 그 블록 밖으로 저장하지 않는다.**\
  호출이 진행되는 동안 **그 블록은 아직 안 끝났으므로** 객체가 살아 있다.
- ★ **경고 0건**이다 — gcc 도 clang 도 할 말이 없다. 4번과 **같은 문법인데 진단이 정반대**인 이유가 그것이다.
- ★★ **값을 내는 자리 한 줄** — **「선택 인자가 많은 함수에 그 자리에서 옵션 묶음을 만들어 넘기는 것」.**\
  변수를 하나 더 만들지 않아도 되고, 인자 순서를 외우지 않아도 되며, 안 적은 것은 기본값이 된다.

### 10. C++ 로 같은 줄을 던지면 — **`error: taking address of rvalue`** ★★

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic s27f.cpp -o x (cc exit=1) =====
s27f.cpp: In function ‘void set()’:
s27f.cpp:6:41: warning: ISO C++ forbids compound-literals [-Wpedantic]
    6 | static void set(void) { keep = &(P){1, 2}; }   /* C 에서는 되던 줄 */
      |                                         ^
s27f.cpp:6:36: error: taking address of rvalue [-fpermissive]
    6 | static void set(void) { keep = &(P){1, 2}; }   /* C 에서는 되던 줄 */
      |                                    ^~~~~~
```

**왜 그런가**

- ★★ **진단은 경고 1건 + 에러 1건**이고 **`cc exit=1`** 이다.\
  `warning: ISO C++ forbids compound-literals [-Wpedantic]` + `error: taking address of rvalue [-fpermissive]`.
- ★★★ **값 범주가 다르다.**

  | | C | C++ |
  |---|---|---|
  | `(P){1,2}` 는 | ★ **좌변값** | ★ **우변값** |
  | `&` 를 붙이면 | **된다** | ★ **에러** |
  | 수명 | **블록 끝까지** | (g++ 확장에서) **완전 식의 끝까지** |
  | 표준에 있나 | ★ **C99 부터 있다** | ★ **없다**(g++ 확장) |

- ★★★ **그래서 4번의 UB 가 C++ 에서는 문법 단계에서 막힌다.**\
  ★ **같은 이름의 문법인데 위험의 모양이 다르다** — C 에서는 「되지만 조심해야 하는 것」이고 C++ 에서는 「애초에 안 되는 것」이다.
- ★ **ISO C++ 에는 복합 리터럴이 없다.** g++ 는 확장으로 받고 `-pedantic` 으로만 알린다.
- ★ **공용 헤더에서는 쓰지 않는다.** 쓰려면 `#ifdef __cplusplus` 로 갈라야 하는데, 그럴 바에는 **이름 있는 변수**가 낫다.\
  ★ 자세한 것은 C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md)) 쪽이다.

### 11. 다섯 층과 무게중심 — **표준이 본체 · UB 는 한 자리인데 여섯 벌로 갈린다** ★★★

**왜 그런가**

| 층 | 이 주제에서 | 근거 |
|---|---|---|
| ★★★ **표준 (본체)** | **좌변값인 것**(주소·수정) · **블록 안이면 자동, 파일 스코프면 정적**인 것 · **배열 복합 리터럴의 `sizeof` 가 배열 크기**인 것 · 지정 초기자의 **나머지 0** 규칙 · **`(char[]){"abc"}` 는 수정 가능**한 것 · C99 부터인 것 | `p->x = 99` → `(99,2)` · 파일 스코프 `10 20` · `sizeof (int[]){1,2,3}` = **12** · `(struct P){.y=5}` → `(0,5)` · `(char[]){"abc"}[0]='X'` → `Xbc` |
| **조건부 표준** | ★ **해당 없음** | — |
| ★ **구현 정의 (얇다)** | 진단 문구와 플래그 이름 · **C23 저장 클래스 지정자의 지원 여부** · `-pedantic` 의 심각도 | gcc `[-Wdangling-pointer=]`·`[-Wuninitialized]` 대 clang **0건** · gcc `-std=c2x` 통과 대 clang 18 **`cc exit=1`** |
| ★★ **미명시** | ★★★ **루프를 돌 때 같은 객체가 재사용되는가** | `a0==a1` = 1 · `a1==a2` = 1(여섯 벌 전부) · ASan `This frame has 1 object(s)` · `[32, 40)` |
| ★★ **UB (자리는 하나)** | ★★★ **블록이 끝난 뒤에 그 객체를 읽는 것** · ★ 문자열 리터럴을 고치는 것(1번의 `5)`, [20번 형제](../20-null-terminated-strings-and-string-literals/)가 정본) | ★★ **여섯 벌** — `1 2` · `289313584 32767` · `0 0` · `1 2` · `0 0` · `518988784 32765`. 전부 **`cc exit=0` · `run exit=0`** · ASan `stack-use-after-scope`(`run exit=1`) |

- ★★ 비어 있는 칸은 「**조건부 표준**」이다. **구현 정의 칸은 있지만 얇다** — 이 주제의 값은 거기 있지 않다.
- ★★★ **UB 는 자리가 하나뿐인데 이 주제에서 가장 크다.** 이유는 두 가지다 —\
  ① **여섯 벌이 전부 다르고** ② **그중 둘이 「맞아 보이는」 값**을 주는데 하필 **가장 흔한 빌드**다.
- ★★★ 미명시 칸의 한 자리는 「**루프에서 객체가 하나인가**」다.\
  ★ **UB 가 아니다** — 객체가 하나여도 그 자체로는 아무 규칙도 안 깨진다. **몇 개 생기는지가 안 정해져 있을 뿐**이다.
- ★★ **도구가 침묵하는 자리**

  | 층 | 침묵하는 자리 |
  |---|---|
  | 표준 | ★★ **「이것이 객체다」라고 말해 주는 도구가 없다** — `&` 가 통과한다는 사실 말고는 표시가 없어 **값처럼 읽고 지나가기 쉽다** |
  | 조건부 표준 | 해당 없음 |
  | 구현 정의 | ★★ **`-std=` 만 보고는 C23 지원 여부를 알 수 없다** — gcc 는 `-std=c17` 에서도 받고 clang 은 `-std=c2x` 에서도 안 받는다. **던져 봐야** 안다 |
  | 미명시 | ★★★ **「객체가 하나인가 셋인가」를 말해 주는 경고가 없다.** 값은 그럴듯하게 나오고 **주소를 비교해야만** 보인다 |
  | UB | ★★★ **clang 18 은 여섯 벌 전부 0건**이다. ★★ gcc 도 `-O0` 에서는 1건뿐이고 **최적화를 올려야** 는다(1 → 5 → 7). ★ **ASan 이 유일하게 확실하다** |

- ★★★ **「종료 코드가 0인데 ill-formed」는 두 군데**다.

  | # | 어디 | 무엇이 났나 | `cc exit` | 막을 수 있나 |
  |---|---|---|---|---|
  | ① | `-std=c17` 의 `(static struct P){…}` | `warning` 1건 `[-Wpedantic]` | **0** | ★ **`-pedantic-errors` 로 막힌다** |
  | ② | 블록이 끝난 뒤 읽는 UB | gcc 1\~7건 · clang 0건 | **0**(여섯 벌 전부) | ★★★ **막을 플래그가 없다** — 경고를 에러로 올려도 clang 은 애초에 경고를 안 낸다 |

  ★★ ②가 이 주제에서 가장 나쁜 자리다 — **빌드를 실패시킬 방법이 없고**, 막으려면 **ASan 을 켠 테스트가 그 경로를 지나가야** 한다.

### 12. 경계 — 어디까지가 이 주제인가 ★

| 무엇 | 정본 |
|---|---|
| **`{.x = 1}` 이라는 초기자 문법 · 나머지가 0 이 되는 규칙** | [21번 형제](../21-struct-declaration-initialization-and-designated-initializers/) |
| **자동·정적 저장 기간의 수명 규칙** | [28번 형제](../28-choosing-among-four-storage-durations/) |
| **`"abc"` 를 고치면 왜 죽나 · 문자열 리터럴의 저장 기간** | [20번 형제](../20-null-terminated-strings-and-string-literals/) |
| **`sizeof` 의 피연산자에서 감쇠가 안 일어나는 것** | [16번 형제](../16-array-pointer-decay-and-function-parameters/) · [8번 형제](../08-sizeof-alignment-and-offsetof/) |
| **포인터의 값과 가리키는 값을 가르는 것** | [14번 형제](../14-pointers-address-dereference-and-pointer-types/) |
| **댕글링 포인터가 왜 최악인가 · 코드 패턴** | 목록의 **57번 주제** |
| **sanitizer 와 경고 플래그 사용법** | 목록의 **58번 주제** |
| **불확정 값을 읽는 것** | [목록의 **30번 주제**](../30-initialization-rules-and-indeterminate-values/) |
| **매크로와 결합하는 관용구** | 목록의 **42번 주제** |

- ★ **이 주제가 끝까지 책임지는 것 셋**
  - ★★★ **이것이 값이 아니라 좌변값인 객체**라는 것과, 그래서 **주소·수정·`sizeof` 가 전부 된다**는 것.
  - ★★★ **블록이 끝나면 죽는다**는 것과, **죽은 뒤에 읽으면 여섯 벌이 전부 다르고 그중 둘이 맞아 보인다**는 것.
  - ★★ **루프를 돌아도 객체가 하나**라는 것과, 그것을 **주소 비교로만 확인할 수 있다**는 것.
- ★★ **쓰면 안 되는 자리 두 가지**
  - ★★★ **주소를 그 블록 밖으로 내보내는 자리** — 전역에 저장하기, 반환하기, 콜백에 등록하기.\
    ★ 대신 `malloc` 하거나 **이름 있는 `static` 변수**를 쓴다.
  - ★★ **객체가 여러 개 필요한 자리**(루프 안에서 주소 모으기) — **이름 있는 배열**을 쓴다.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s27a.c` (27-a) | 파일 스코프 **`10 20`** · 블록 스코프 **`1 2`**(UB) · 루프 **`(2,4)` 셋** · **`a0==a1` = 1** · 경고 **1건** `[-Wdangling-pointer=]` | gcc 1벌(문서) · ★★ **6벌**(gcc·clang × `-O0`/`-O1`/`-O2`)로 값 격자 · ★★ **6벌**로 경고 건수 격자 · gcc `-O2` 진단 전문 1벌 |
| `s27b.c` (27-b) | 좌변값(`(99,2)`) · `sizeof (int[]){1,2,3}` = **12** · 지정 초기자 `(0,5)` · `(char[]){"abc"}` **수정 가능**(`Xbc`) · `"abc"` 수정은 **`run exit=139`** | gcc 1벌 |
| `s27c.c` (27-c) | 함수 인자 자리 — 지정 초기자 3벌 · `(struct Opt){0}` 이 전부 기본값 · `sum((int[]){…},5)` = **15** · **경고 0건** | gcc 1벌 |
| `s27d.c` (27-d) | ASan **`stack-use-after-scope`** · `READ of size 4` · `offset 36 in frame` · **`This frame has 1 object(s)`** · `[32, 40)` · **`run exit=1`** | gcc 1벌(`-O1` + ASan) |
| `s27e.c` (27-e) | C23 `(static struct P){1,2}` — gcc `-std=c2x -O2` **`1 2`**(`cc exit=0`) · gcc `-std=c17 -pedantic` **경고 1건 · `cc exit=0`** · clang `-std=c2x` **`error: expected expression` · `cc exit=1`** | gcc 2벌 · clang 1벌 |
| `s27f.cpp` (27-f) | C++ 에서는 **우변값** — `ISO C++ forbids compound-literals` 경고 + **`error: taking address of rvalue`** · `cc exit=1` | g++ 1벌 |

**구현 의존 항목** — 다음은 **이 환경(x86-64 Linux · gcc 13.3.0 · clang 18.1.3 · g++ 13.3.0)에서만** 그렇다.

- ★★★ **UB 격자의 여섯 값 전부** — **미정의 동작**이라 어떤 값도 결론이 아니다.\
  ★ 결론은 「**여섯 벌이 서로 다르다**」와 「**`-O0` 두 벌이 맞아 보인다**」이지 **어느 숫자가 나오는가**가 아니다.
- ★★★ **경고 건수 격자**(gcc 1/5/7 · clang 0/0/0) — 컴파일러와 버전의 선택이다.
- ★★ **루프에서 객체가 하나인 것** — **미명시**다. 다른 구현에서 셋이 나와도 적법하다.
- ★★ **C23 저장 클래스 지정자의 지원 여부** — gcc 13 은 되고 clang 18 은 안 된다.
- ★ **`"abc"` 수정이 `run exit=139` 로 죽는 것** — UB 다. 죽지 않는 구현도 있다.
- ★ **ASan 의 `offset 36 in frame`·`[32, 40)`** — 프레임 배치에 달렸다. **「객체가 1개」라는 사실만** 결론에 쓴다.
- ★ **진단 문구와 플래그 이름 전부** — 특히 gcc 가 그 객체를 `({anonymous})` 라고 부르는 것.

**좌변값인 것 · 저장 기간이 자리로 정해지는 것 · `sizeof` 가 배열 크기인 것 · 지정 초기자의 나머지 0 규칙 · C++ 에서 우변값인 것은 구현 의존이 아니다.**\
어느 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `const` 로 한정한 복합 리터럴이 **합쳐지는가**(`(const int){1}` 둘의 주소 비교) ·\
  **매크로와 결합한 관용구**(`#define OPT(...) ((struct Opt){__VA_ARGS__})`) · **VLA 타입의 복합 리터럴**(`(int[n]){…}`) ·\
  **`-Os`·`-O3`**(4·5번은 `-O0`\~`-O2` 까지만 흔들었다) · **clang 의 `-Wdangling` 계열 플래그를 따로 켜면 달라지는지** ·\
  **`switch`·`if` 본문 없는 블록에서의 수명** · **C++ 에서 g++ 확장의 수명이 실제로 완전 식의 끝인지**(규칙만 적었다).
- ★ **못 잰 것** — **「루프에서 객체가 하나인 것이 표준의 요구인가」.**\
  이 문서가 보인 것은 **이 구현에서 여섯 벌 전부 하나였다**는 관찰이고, **「셋이 나오는 구현이 있는가」는 다른 구현이 있어야** 답할 수 있다.\
  이 머신의 두 컴파일러로는 **원리상 반증도 확증도 못 한다** — 「안 돌려 본 것」이 아니라 「**측정 방법이 전제를 요구해 잴 수 없는 것**」이라 따로 적는다.\
  ★★ **그래서 본문은 그 사실을 「보장」이 아니라 「미명시 칸의 관찰」로 적었다.**

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번의 여섯 벌 격자** — UB 라 **코드 생성이 바뀌면 그대로 바뀐다.** 언제든 달라질 수 있다.
- ★★★ **5번의 경고 건수 격자** — **clang 이 `[-Wdangling]` 을 켜기 시작하면 이 편의 결론 하나가 바뀐다.**
- ★★ **clang 이 C23 저장 클래스 지정자를 지원하게 됐는지**(지금은 `error: expected expression`).
- ★★ **gcc 가 `-O0` 에서도 `[-Wuninitialized]` 를 내게 됐는지**(지금은 `-O1` 부터다).
- ★ **진단 문구 전부** · **ASan 리포트의 형식**(`This frame has 1 object(s)` 표기).
- **좌변값성·저장 기간·`sizeof` 규칙은 다시 돌릴 필요가 없다** — C99 이후 바뀐 적이 없다.
