# c/syntax/32 — `volatile` 이 실제로 보장하는 것: 「**매번 가서 본다 — 그것뿐이다**」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [ISO/IEC 9899 공개 작업 초안 — WG14 프로젝트 문서 목록](https://www.open-std.org/jtc1/sc22/wg14/www/projects)(C23 대응 초안 [**N3220**](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf) — 「`volatile` 객체에 대한 **접근이 무엇인지는 구현 정의**」라는 문장, 데이터 경쟁의 UB, 시그널 핸들러와 `volatile sig_atomic_t`, `longjmp` 뒤 비-`volatile` 지역 변수의 불확정을 **본문에서 직접 찾아 읽었다**) · [cppreference — `volatile` type qualifier (C)](https://en.cppreference.com/w/c/language/volatile)
> ★ **표준 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **어셈블리·종료 코드·센 수는 전부 실행으로** 접지했다.
> **실행 검증** — 이 문서의 모든 출력·진단은 아래 판에서 실제로 돌려 **파일로 캡처한 것**이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> ★★ **최적화 수준이 결과를 바꾸는 자리는 전부 판 격자**(컴파일러 2 × `-O0`/`-O2`, `setjmp` 는 × 3)로 돌렸다.\
> ★★ **블록은 전부 캡처 파일에서 조립했다** — 손으로 옮겨 적은 출력이 하나도 없다.
> **버전** — `volatile` 은 **C89 부터**, `_Atomic`/`<stdatomic.h>` 와 **메모리 모델(데이터 경쟁)은 C11 부터**다. ★ **C11 의 원자성은 선택 기능**이다(`__STDC_NO_ATOMICS__`) — 아래 다섯 층 표.
> ★★★ **재지 않은 성능 주장은 하지 않는다.** 「`volatile` 은 느리다」는 **시간으로 재지 않았다** — 이 편은 **어셈블리의 명령 수**만 센다.
> ★★ **경계** — **동시성 개념 자체**(경쟁·가시성·락)는 [`foundations/process-thread/`](../../../../process-thread/)가 정본이다. 여기는 「**`volatile` 이라는 낱말이 무엇을 바꾸고 무엇을 안 바꾸나**」만 본다.\
> ★ **`const`** 는 [31번 형제](../31-const-and-pointer-const-placement/)가 정본이다. **`setjmp`/`longjmp` 자체**는 이 목록에 주제가 없다 — 이 편은 **`volatile` 이 필요한 자리**만 본다. **sanitizer 사용법**은 목록의 **58번 주제**다.\
> ★ 이 목록은 `<stdatomic.h>` 를 **주제로 세우지 않았다**(README 「뺀 것」) — 여기서는 **`volatile` 의 대조군**으로만 쓴다.
> 선행 — [31번 형제](../31-const-and-pointer-const-placement/).
> 이 본문은 Claude 작성이다(원고 없음).

★★★ **본체는 넷째 창 — `-O2` 어셈블리다.** 같은 함수를 `volatile` 있이/없이 컴파일해 **로드·스토어가 몇 개 남는지**를 센다.
★★★ 그리고 **「못 막는 것」은 어셈블리로는 안 보인다** — 원자성과 하드웨어 순서는 **실행해서 센 수**(잃은 수 · 둘 다 0 을 본 판 수)로만 보인다.

## 이 주제가 쓰는 창

| 창 | 이 주제에서 | 상태 |
|---|---|---|
| ① 컴파일 진단 | `setjmp` 뒤 지역 변수에 `-Wclobbered` 를 켜도 **0건**((6)) | 씀(침묵) |
| ② 실행 출력 | ★★ **잃은 수** · ★★ **둘 다 0 을 본 판 수** · 시그널 깃발 루프의 `timeout` · `longjmp` 뒤 값 | 씀 |
| ③ sanitizer | ★★ **TSan** — `volatile int` 의 `++` 를 **데이터 경쟁**으로 잡는다 · `_Atomic` 은 침묵 | 씀 |
| ★★★ ④ **`-O2` 어셈블리** | ★ **본체** — 로드가 루프 밖으로 빠지고 · 세 읽기가 하나로 · 두 쓰기가 하나로 · **`volatile` 이면 전부 남는다** | 씀 |
| ⑤ `-O0` 어셈블리 | 대조군 — `-O0` 에서는 `volatile` 이 없어도 대부분 남는다((1)) | 씀 |
| 시간 측정 | 「`volatile` 은 느리다」 | ★ **안 쟀다**(규칙 — 재지 않은 성능 주장 금지) |
| ★ 제5의 상태 | 「순서가 지켜지나」를 **어셈블리로 물었더니 명령은 순서대로**였다 — 그래서 **실행해서 결과를 세는 창**으로 바꿔 물었다((5)) | 창을 바꿔 답함 |

★ **바꾼 창(실행해서 세기)이 못 보는 것** — 「**있다**」는 증명하지만 「**없다**」는 증명하지 못한다. `_Atomic` 의 `0 / 200000` 은 **이 판의 관찰**이고, 「없다」는 **표준(seq_cst)이 보장**한다.

## 이 판

```text
===== gcc --version | sed -n 1p (cc exit=0) =====
gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
```

```text
===== clang --version | sed -n 1p (cc exit=0) =====
Ubuntu clang version 18.1.3 (1ubuntu1)
```

```text
===== nproc (exit=0) =====
24
```

★ 논리 CPU 가 여럿이라 두 스레드 실험이 실제로 **동시에** 돈다.

## 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | ★★★ **`volatile int` 의 잃은 수**(`잃은 수 : N`) | 두 스레드의 끼어듦이 실행마다 다르다 |
| **흔들린다** | ★★★ **`volatile` 판의 둘 다 0 을 본 판 수**(`판 수 : N`) | 하드웨어 저장 버퍼가 비워지는 때가 실행마다 다르다 |
| **흔들린다** | TSan 리포트의 **`(pid=N)`** · gcc TSan `FATAL` 줄의 **주소** | 실행마다 다르다 |
| 안 흔들린다 | ★★★ **「잃었나 = 예 / 아니오」** · **「있다 / 없다」** | 10 번 돌려도 **10 대 0** 이었다((3)) |
| 안 흔들린다 | ★★★ **`_Atomic` 의 `잃은 수 : 0` · `0 / 200000`** | 표준이 보장한다(그리고 관찰도 그렇다) |
| 안 흔들린다 | ★★★ **어셈블리 전부** · 명령 수 격자 | 같은 컴파일러 · 같은 플래그면 같다 |
| 안 흔들린다 | 시그널 격자의 **`run exit`(`0` · `124`)** · `setjmp` 격자 | `timeout 3` 과 `alarm(1)` 의 차이가 커서 판이 안 갈린다 |
| 안 흔들린다 | TSan 의 **`SUMMARY` 줄**(`s32j.c:8:43 in work`) · `reported 1 warnings` | 두 스레드가 **같은 줄**을 밟는다 |

★★ **정규화 규칙은 기본 둘(주소 · PID) + 이 편 고유 셋**이다 — 위 표의 「흔들린다」 세 줄과 **정확히 같은 목록**이다.

```text
   --rule '(volatile int : .*잃은 수 : )[0-9]+=\1<n>'
   --rule '(volatile : .*판 수 : )[0-9]+=\1<n>'
   --rule '\(pid.[0-9]+\)=(pid=<pid>)'
```

★ **`_Atomic` 줄은 정규화 대상이 아니다** — 패턴이 `volatile` 줄에만 걸리게 짰다. `_Atomic` 이 1 이라도 잃으면 **「고칠 것」으로 떠야** 하기 때문이다.

## 한눈에 — 쉽게 말하면

**`volatile` 은 「메모를 믿지 말고 매번 우편함에 가서 봐라」다.**

- **우편함을 한 번 보고 「비었네」라고 적어 둔 뒤 그 메모만 보는 사람** — 편지가 와도 모른다. → **`volatile` 없는 `while (!flag)`** — 로드가 루프 밖으로 빠진다
- **「매번 우편함에 가라」고 시킨 사람** — 매번 간다. → **`volatile`** — 로드가 루프 안에 남는다
- **그런데 두 사람이 한 장부에 「+1」을 동시에 적으면** — 둘 다 **5 를 읽고 6 을 적는다.** 한 번이 사라진다. 「매번 장부를 봐라」는 **이것을 못 막는다.** → **원자성**
- **「편지를 넣은 뒤 깃발을 올려라」라고 해도** — 우체부가 **깃발을 먼저 올리고 편지는 나중에** 넣을 수 있다. → **순서**

| 비유 | 실체 | `volatile` 이 막나 |
|---|---|---|
| 메모를 믿는다 | 로드를 루프 밖으로 · 세 읽기를 하나로 | ★★★ **막는다** — 어셈블리에 로드가 남는다 |
| 같은 말을 두 번 한다 | `x = 1; x = 2;` 의 앞 쓰기 | ★★★ **막는다** — 두 스토어가 남는다 |
| 한 장부에 동시에 +1 | 두 스레드의 `v++` | ★★★ **못 막는다** — 이 판에서 수백만 번을 잃었다 |
| 편지와 깃발의 순서(컴파일러) | 비-`volatile` 쓰기와 `volatile` 쓰기 | ★★ **못 막는다** — `data = 1` 이 **사라졌다** |
| 편지와 깃발의 순서(하드웨어) | 쓰고 나서 남의 것을 읽기 | ★★ **못 막는다** — 둘 다 0 을 본 판이 **있다** |
| ★ 대조군 | `_Atomic` | ★★★ 셋 다 막는다 — 잃은 수 0 · 판 수 0 |

```text
   while (!flag) { }     -O2

   flag 가 volatile 이 아니면                flag 가 volatile 이면
   ---------------------------------------   ---------------------------------------
   gcc   : mov eax, [flag]   ← 한 번 읽고     gcc   : .L6: mov eax, [flag]  ← 매번 읽는다
           test / jne .L1                            test / je .L6
     .L3:  jmp .L3           ← ★ 읽지 않고 영원히
   clang : ret               ← ★ 루프째 없다  clang : .LBB1_1: cmp [flag], 0 / je .LBB1_1
```

- ★★★ **이 주제는 「표준」 칸이 본체**다 — `volatile` 접근이 **관찰 가능한 부수 효과**라서 지우거나 합칠 수 없다는 것이 표준이다.
- ★★★ 그런데 **「무엇이 접근인가」는 구현 정의**다 — 표준이 **그 자리를 비워 두고** 구현에 넘겼다. 이 편에서 **가장 정밀하게 갈라야 하는 칸**이다.
- ★★★ 그리고 **「UB」 칸이 두껍다** — **두 스레드가 `volatile` 을 같이 고치는 것은 데이터 경쟁**이고, `volatile` 은 **데이터 경쟁을 면제해 주지 않는다.**
- ★★ **「조건부 표준」 칸이 드물게 찬다** — `_Atomic` 자체가 **선택 기능**이다.

> **관찰 가능한 부수 효과(observable side effect)** — 프로그램 **바깥에서 보일 수 있는** 일. 컴파일러가 없애거나 합칠 수 없다.\
> 예: `volatile` 객체의 읽기·쓰기, 파일 출력.

> **데이터 경쟁(data race)** — 두 스레드가 같은 자리를 건드리고 **적어도 하나가 쓰기이며**, 적어도 하나가 원자적이지 않고, **둘 사이에 앞뒤가 없는** 것. **UB** 다.\
> 예: 두 스레드가 `volatile int v` 에 `v++`.

> **저장 버퍼(store buffer)** — CPU 가 쓰기를 **잠깐 모아 두는** 곳. 그 사이에 **뒤의 읽기가 먼저** 메모리에 갈 수 있다.\
> 예: x86 에서 「쓰고 나서 남의 것을 읽기」가 둘 다 옛 값을 볼 수 있다((5)).

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. ★★★ **`volatile` 이 막는 것은 무엇인가** — 어셈블리의 로드·스토어 수로.
2. ★★★ **`volatile` 이 못 막는 것은 무엇인가** — 원자성과 순서, 실행해서 센 수로.
3. ★★ **그러면 `volatile` 이 정당한 자리는 어디인가** — 셋(장치 레지스터 · `setjmp` · 시그널).

## 동작 방식

### (1) ★★★ 막는 것 — 접근을 지우고 합치는 것

**언제 쓰나** — 「컴파일러가 이 읽기를 없앨 수 있나」를 물을 때. ★★★ **이 편의 본체**다.

```c
/* s32a.c */
int          plain_flag;
volatile int vol_flag;

void wait_plain(void)   { while (!plain_flag) { } }
void wait_vol(void)     { while (!vol_flag) { } }

int  read3_plain(void)  { return plain_flag + plain_flag + plain_flag; }
int  read3_vol(void)    { return vol_flag + vol_flag + vol_flag; }

void write2_plain(void) { plain_flag = 1; plain_flag = 2; }
void write2_vol(void)   { vol_flag = 1; vol_flag = 2; }
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
wait_plain:
	endbr64
	mov	eax, DWORD PTR plain_flag[rip]
	test	eax, eax
	jne	.L1
.L3:
	jmp	.L3
.L1:
	ret
wait_vol:
	endbr64
.L6:
	mov	eax, DWORD PTR vol_flag[rip]
	test	eax, eax
	je	.L6
	ret
read3_plain:
	endbr64
	mov	eax, DWORD PTR plain_flag[rip]
	lea	eax, [rax+rax*2]
	ret
read3_vol:
	endbr64
	mov	eax, DWORD PTR vol_flag[rip]
	mov	ecx, DWORD PTR vol_flag[rip]
	mov	edx, DWORD PTR vol_flag[rip]
	add	eax, ecx
	add	eax, edx
	ret
write2_plain:
	endbr64
	mov	DWORD PTR plain_flag[rip], 2
	ret
write2_vol:
	endbr64
	mov	DWORD PTR vol_flag[rip], 1
	mov	DWORD PTR vol_flag[rip], 2
	ret
vol_flag:
plain_flag:
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
wait_plain:                             # @wait_plain
# %bb.0:
	ret
.Lfunc_end0:
                                        # -- End function
wait_vol:                               # @wait_vol
# %bb.0:
.LBB1_1:                                # =>This Inner Loop Header: Depth=1
	cmp	dword ptr [rip + vol_flag], 0
	je	.LBB1_1
# %bb.2:
	ret
.Lfunc_end1:
                                        # -- End function
read3_plain:                            # @read3_plain
# %bb.0:
	mov	eax, dword ptr [rip + plain_flag]
	lea	eax, [rax + 2*rax]
	ret
.Lfunc_end2:
                                        # -- End function
read3_vol:                              # @read3_vol
# %bb.0:
	mov	eax, dword ptr [rip + vol_flag]
	add	eax, dword ptr [rip + vol_flag]
	add	eax, dword ptr [rip + vol_flag]
	ret
.Lfunc_end3:
                                        # -- End function
write2_plain:                           # @write2_plain
# %bb.0:
	mov	dword ptr [rip + plain_flag], 2
	ret
.Lfunc_end4:
                                        # -- End function
write2_vol:                             # @write2_vol
# %bb.0:
	mov	dword ptr [rip + vol_flag], 1
	mov	dword ptr [rip + vol_flag], 2
	ret
.Lfunc_end5:
                                        # -- End function
plain_flag:

vol_flag:

```

```text
===== 플래그를 건드리는 명령 수 — 함수 6 × 컴파일러 2 × 최적화 2 (exit=0) =====
함수          | gcc -O0   | gcc -O2   | clang -O0 | clang -O2
wait_plain    | 1 번      | 1 번      | 1 번      | 0 번     
wait_vol      | 1 번      | 1 번      | 1 번      | 1 번     
read3_plain   | 1 번      | 1 번      | 3 번      | 1 번     
read3_vol     | 3 번      | 3 번      | 3 번      | 3 번     
write2_plain  | 2 번      | 1 번      | 2 번      | 1 번     
write2_vol    | 2 번      | 2 번      | 2 번      | 2 번     
(칸 = 그 함수의 명령 중 flag 를 건드리는 줄 수 — 루프 안이면 한 번 돌 때마다 다시 실행된다)
```

```text
===== gcc -std=c17 -O0 -S -masm=intel -fno-asynchronous-unwind-tables s32a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | sed -n '/^wait_plain:/,/ret$/p;/^read3_plain:/,/ret$/p' (cc exit=0) =====
wait_plain:
	endbr64
	push	rbp
	mov	rbp, rsp
	nop
.L2:
	mov	eax, DWORD PTR plain_flag[rip]
	test	eax, eax
	je	.L2
	nop
	nop
	pop	rbp
	ret
read3_plain:
	endbr64
	push	rbp
	mov	rbp, rsp
	mov	edx, DWORD PTR plain_flag[rip]
	mov	eax, edx
	add	eax, eax
	add	eax, edx
	pop	rbp
	ret
```

그림 해설 (한 단계씩):

- ★★★ **`wait_plain` 을 gcc `-O2` 는 「한 번 읽고 영원히 돈다」로 바꿨다** — `.L3: jmp .L3` 에는 **로드가 없다.** clang `-O2` 는 **루프째 지우고 `ret`** 했다(명령 수 격자의 **`0 번`**).
- ★★★ **`wait_vol` 은 두 컴파일러 다 루프 안에 로드가 있다** — gcc `.L6: mov eax, [vol_flag]` · clang `.LBB1_1: cmp [vol_flag], 0`.
- ★★★ **`read3` — 비-`volatile` 은 로드 1개 + `lea`(×3), `volatile` 은 로드 3개**(네 벌 다). **`write2` — 비-`volatile` 은 스토어 1개(`2` 만), `volatile` 은 2개**(`1` 과 `2`).
- ★★ **격자의 `wait_plain` 「1 번」은 뜻이 다르다** — gcc `-O0` 의 1번은 **루프 안**(`.L2:` 뒤)이고 gcc `-O2` 의 1번은 **루프 밖**이다. **센 수가 같아도 자리가 다르다** — 그래서 어셈블리를 같이 싣는다.
- ★★ **`-O0` 도 「아무것도 안 접는다」가 아니다** — gcc `-O0` 의 `read3_plain` 이 **로드 1개**다(`plain_flag + plain_flag + plain_flag` 를 접었다). clang `-O0` 은 3개다. **두 컴파일러가 갈린 자리**다.
- ★ **clang 이 루프를 지운 것** — C 는 「부수 효과가 없는 루프는 끝난다고 가정해도 된다」고 허용한다. `volatile` 접근은 **부수 효과**라 그 가정이 안 선다.

비용 — **`volatile` 은 이 접기를 전부 막는다.** 필요 없는 자리에 붙이면 **막을 필요 없는 접기까지** 막는다(시간은 **재지 않았다**).

### (2) ★★ 정당한 자리 ① — 시그널 핸들러가 세우는 깃발

**언제 쓰나** — 시그널 핸들러와 메인 루프가 변수 하나로 대화할 때. ★ 이 자리는 **표준이 `volatile sig_atomic_t` 를 이름으로 지정**한 곳이다.

```c
/* s32b.c */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static int got;                          /* ★ volatile 이 없다 */

static void on_alarm(int sig) { (void)sig; got = 1; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGALRM, on_alarm);
    alarm(1);                            /* 1초 뒤 핸들러가 got = 1 */
    printf("기다린다\n");
    while (!got) { }
    printf("깼다 · got = %d\n", (int)got);
    return 0;
}
```

```c
/* s32b2.c */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static int got;                          /* ★ volatile 이 없다 — 루프 뒤에 got 을 다시 안 읽는 판 */

static void on_alarm(int sig) { (void)sig; got = 1; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGALRM, on_alarm);
    alarm(1);                            /* 1초 뒤 핸들러가 got = 1 */
    printf("기다린다\n");
    while (!got) { }
    printf("깼다\n");
    return 0;
}
```

```c
/* s32c.c */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdio.h>
#include <unistd.h>

static volatile sig_atomic_t got;        /* ★ 표준이 시그널 핸들러에 허락한 형태 */

static void on_alarm(int sig) { (void)sig; got = 1; }

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    signal(SIGALRM, on_alarm);
    alarm(1);
    printf("기다린다\n");
    while (!got) { }
    printf("깼다 · got = %d\n", (int)got);
    return 0;
}
```

```text
===== 시그널 핸들러가 세우는 깃발 — 파일 3 × 컴파일러 2 × 최적화 2 (timeout 3) (exit=0) =====
s32b   gcc    -O0  run exit=0   | 기다린다|깼다 · got = 1|
s32b   gcc    -O2  run exit=124 | 기다린다|
s32b   clang  -O0  run exit=0   | 기다린다|깼다 · got = 1|
s32b   clang  -O2  run exit=124 | 기다린다|
s32b2  gcc    -O0  run exit=0   | 기다린다|깼다|
s32b2  gcc    -O2  run exit=124 | 기다린다|
s32b2  clang  -O0  run exit=0   | 기다린다|깼다|
s32b2  clang  -O2  run exit=0   | 기다린다|깼다|
s32c   gcc    -O0  run exit=0   | 기다린다|깼다 · got = 1|
s32c   gcc    -O2  run exit=0   | 기다린다|깼다 · got = 1|
s32c   clang  -O0  run exit=0   | 기다린다|깼다 · got = 1|
s32c   clang  -O2  run exit=0   | 기다린다|깼다 · got = 1|
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s32b.c -o x ; timeout 3 ./x (cc exit=0 · run exit=124) =====
기다린다
```

- ★★★ **`volatile sig_atomic_t`(`s32c`)는 네 벌 다 1초 뒤 깬다** — `run exit=0` · `got = 1`.
- ★★★ **`volatile` 없는 `int`(`s32b`)는 `-O2` 두 벌이 `run exit=124`**(`timeout 3` 에 죽음) — 루프가 `got` 을 **다시 안 읽는다.** `-O0` 두 벌은 깬다.
- ★★★ **`s32b2` 의 clang `-O2` 는 「기다리지 않고」 깬다** — `run exit=0` · `깼다`. 아래 어셈블리가 이유다.

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32b.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | sed -n '/^main:/,/End function/p' (cc exit=0) =====
main:                                   # @main
# %bb.0:
	push	rax
	mov	rax, qword ptr [rip + stdout@GOTPCREL]
	mov	rdi, qword ptr [rax]
	xor	esi, esi
	mov	edx, 2
	xor	ecx, ecx
	call	setvbuf@PLT
	lea	rsi, [rip + on_alarm]
	mov	edi, 14
	call	__sysv_signal@PLT
	mov	edi, 1
	call	alarm@PLT
	lea	rdi, [rip + .Lstr]
	call	puts@PLT
	cmp	byte ptr [rip + got], 0
	je	.LBB0_1
# %bb.2:
	lea	rdi, [rip + .L.str.1]
	mov	esi, 1
	xor	eax, eax
	call	printf@PLT
	xor	eax, eax
	pop	rcx
	ret
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	jmp	.LBB0_1
.Lfunc_end0:
                                        # -- End function
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32b2.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | sed -n '/^main:/,/End function/p' (cc exit=0) =====
main:                                   # @main
# %bb.0:
	push	rax
	mov	rax, qword ptr [rip + stdout@GOTPCREL]
	mov	rdi, qword ptr [rax]
	xor	esi, esi
	mov	edx, 2
	xor	ecx, ecx
	call	setvbuf@PLT
	lea	rsi, [rip + on_alarm]
	mov	edi, 14
	call	__sysv_signal@PLT
	mov	edi, 1
	call	alarm@PLT
	lea	rdi, [rip + .Lstr]
	call	puts@PLT
	lea	rdi, [rip + .Lstr.2]
	call	puts@PLT
	xor	eax, eax
	pop	rcx
	ret
.Lfunc_end0:
                                        # -- End function
```

- ★★★ **`s32b2` 의 `main` 에는 루프가 없다** — `puts` 두 번이 연달아 나온다. **루프 뒤에 `got` 을 다시 안 읽는 판**이라 clang 이 **루프째 지웠다**((1)의 `wait_plain` 과 같다).
- ★★★ **`s32b` 의 `main` 은 `got` 을 한 번 읽고 `.LBB0_1: jmp .LBB0_1`** — 읽지 않고 영원히 돈다. 그리고 루프를 빠져나온 쪽의 `printf` 에는 **`mov esi, 1`** — `got` 을 **다시 읽지 않고 `1` 로 접었다.**
- ★★ **한 글자(루프 뒤의 읽기)가 「멈춘다 / 안 기다린다」를 가른다** — 둘 다 **UB 의 이 판 결과**다. 표준은 핸들러가 **`volatile sig_atomic_t` 가 아닌 정적 객체**를 건드리면 UB 라고 한다.

비용 — **깃발은 `volatile sig_atomic_t` 로만** 둔다. 그 밖의 것을 핸들러에서 고치면 **판에 따라 멈추거나 건너뛴다.**

### (3) ★★★ 못 막는 것 ① — 원자성

**언제 쓰나** — 「두 스레드가 같이 쓰는 카운터니까 `volatile` 을 붙이자」고 할 때.

```c
/* s32e.c */
int          p;
volatile int v;
_Atomic int  a;

void inc_plain(void)  { p++; }
void inc_vol(void)    { v++; }
void inc_atomic(void) { a++; }
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32e.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
inc_plain:
	endbr64
	add	DWORD PTR p[rip], 1
	ret
inc_vol:
	endbr64
	mov	eax, DWORD PTR v[rip]
	add	eax, 1
	mov	DWORD PTR v[rip], eax
	ret
inc_atomic:
	endbr64
	lock add	DWORD PTR a[rip], 1
	ret
a:
v:
p:
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32e.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
inc_plain:                              # @inc_plain
# %bb.0:
	inc	dword ptr [rip + p]
	ret
.Lfunc_end0:
                                        # -- End function
inc_vol:                                # @inc_vol
# %bb.0:
	inc	dword ptr [rip + v]
	ret
.Lfunc_end1:
                                        # -- End function
inc_atomic:                             # @inc_atomic
# %bb.0:
	lock		inc	dword ptr [rip + a]
	ret
.Lfunc_end2:
                                        # -- End function
p:

v:

a:

```

```c
/* s32d.c */
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>

#define N 10000000

static volatile int v_counter;           /* ★ volatile */
static _Atomic int  a_counter;           /* ★ _Atomic */
static atomic_int   go;                  /* 두 스레드를 같이 출발시키는 깃발 */

static void *work_v(void *arg) { (void)arg; while (!go) { } for (int i = 0; i < N; i++) v_counter++; return NULL; }
static void *work_a(void *arg) { (void)arg; while (!go) { } for (int i = 0; i < N; i++) a_counter++; return NULL; }

static int run(void *(*fn)(void *)) {
    pthread_t t1, t2;
    go = 0;
    pthread_create(&t1, NULL, fn, NULL);
    pthread_create(&t2, NULL, fn, NULL);
    go = 1;
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    return 0;
}

int main(void) {
    run(work_v);
    int lost_v = 2 * N - v_counter;
    printf("volatile int : 잃었나 = %s · 잃은 수 : %d\n", lost_v > 0 ? "예" : "아니오", lost_v);
    run(work_a);
    int lost_a = 2 * N - a_counter;
    printf("_Atomic int  : 잃었나 = %s · 잃은 수 : %d\n", lost_a > 0 ? "예" : "아니오", lost_a);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -pthread s32d.c -o x ; ./x (cc exit=0 · run exit=0) =====
volatile int : 잃었나 = 예 · 잃은 수 : 9810460
_Atomic int  : 잃었나 = 아니오 · 잃은 수 : 0
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -pthread s32d.c -o x ; ./x (cc exit=0 · run exit=0) =====
volatile int : 잃었나 = 예 · 잃은 수 : 6781970
_Atomic int  : 잃었나 = 아니오 · 잃은 수 : 0
```

```text
===== 같은 바이너리를 10 번 — 「잃었나」만 모아 센다 (gcc -O2) (exit=0) =====
     10 _Atomic int  : 잃었나 = 아니오
     10 volatile int : 잃었나 = 예
```

```text
   v++ 가 번역된 것 (-O2)

   gcc   volatile : mov eax, [v] / add eax, 1 / mov [v], eax   ← ★ 읽기·더하기·쓰기 세 명령
   clang volatile : inc dword ptr [v]                           ← ★ 한 명령 — 그런데 lock 이 없다
   둘 다 _Atomic  : lock add [a], 1   /   lock inc [a]          ← ★ lock 이 붙는다

   스레드 A : 읽기(5) ───────────── 쓰기(6)
   스레드 B :        읽기(5) ── 쓰기(6)          ← ★ +1 이 하나 사라진다
```

그림 해설 (한 단계씩):

- ★★★ **`volatile int` 는 두 컴파일러 모두 잃는다** — 「잃었나 = 예」. **gcc 바이너리를 10 번 돌려 10 번 다 「예」**, `_Atomic` 은 **10 번 다 「아니오」**.
- ★★★ **잃은 수 자체는 흔들리는 칸**이다 — 이 판에서 **백만 단위**였지만 숫자는 결론이 아니다. **「잃었나」만 안 흔들린다.**
- ★★★ **clang 은 `volatile` 의 `++` 를 명령 하나(`inc dword ptr [v]`)로 번역했는데도 잃었다.** **명령 하나 ≠ 원자적**이다 — 다른 코어가 **그 명령의 읽기와 쓰기 사이에** 끼어든다. `lock` 접두어가 그것을 막는다.
- ★★ **`_Atomic` 의 `++` 는 `lock add`(gcc) · `lock inc`(clang)** 다. **`volatile` 과의 차이는 `lock` 한 글자**이고, 그 한 글자가 잃은 수를 **0** 으로 만든다.
- ★ **비-`volatile` 의 `p++` 는 `-O2` 에서 `add [p], 1` 한 명령**이다 — 이것도 원자적이 아니다. 이 편은 그것을 **돌려 보지 않았다**(어셈블리만).

비용 — **`volatile` 은 원자성을 한 번도 약속한 적이 없다.** 카운터는 **`_Atomic`**(또는 락)이다.

### (4) ★★ 못 막는 것 ② — 순서(컴파일러)

**언제 쓰나** — 「데이터를 쓰고 `ready` 를 올리면, `ready` 를 본 쪽은 데이터를 본다」고 믿을 때.

```c
/* s32f.c */
int          data;
volatile int ready;

void publish(void) {
    data = 1;                            /* ① */
    ready = 1;                           /* ★ volatile 쓰기 */
    data = 2;                            /* ② */
}

int consume(void) {
    int a = data;                        /* ① */
    int r = ready;                       /* ★ volatile 읽기 */
    int b = data;                        /* ② */
    return a + r + b;
}
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32f.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
publish:
	endbr64
	mov	DWORD PTR ready[rip], 1
	mov	DWORD PTR data[rip], 2
	ret
consume:
	endbr64
	mov	eax, DWORD PTR ready[rip]
	mov	edx, DWORD PTR data[rip]
	lea	eax, [rax+rdx*2]
	ret
ready:
data:
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32f.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
publish:                                # @publish
# %bb.0:
	mov	dword ptr [rip + ready], 1
	mov	dword ptr [rip + data], 2
	ret
.Lfunc_end0:
                                        # -- End function
consume:                                # @consume
# %bb.0:
	mov	eax, dword ptr [rip + data]
	add	eax, eax
	add	eax, dword ptr [rip + ready]
	ret
.Lfunc_end1:
                                        # -- End function
data:

ready:

```

```text
   publish (-O2)           소스                    두 컴파일러가 남긴 것
                           data  = 1;   ①          (없다)                ← ★ 사라졌다
                           ready = 1;   volatile   mov [ready], 1
                           data  = 2;   ②          mov [data], 2

   consume (-O2)           a = data;    ①          gcc   : [ready] 먼저, [data] 한 번
                           r = ready;   volatile   clang : [data] 한 번, [ready] 나중
                           b = data;    ②          ★ 두 data 읽기가 하나로 합쳐졌다
```

- ★★★ **`data = 1` 이 사라졌다** — 두 컴파일러 다. `volatile` 쓰기 `ready = 1` 을 **사이에 두고도** 비-`volatile` 쓰기 둘을 **하나(`= 2`)로 합쳤다.** `ready` 를 본 쪽이 **`data = 1` 을 볼 기회가 원리상 없다.**
- ★★★ **`consume` 의 두 `data` 읽기가 하나가 됐다** — gcc 는 **`ready` 뒤로**, clang 은 **`ready` 앞으로** 옮겼다. **`volatile` 읽기가 벽이 아니다.**
- ★★ **`volatile` 은 `volatile` 접근끼리의 순서만** 지킨다. 비-`volatile` 접근은 그 주위를 **마음대로 넘나든다.**

비용 — **`volatile` 깃발로 데이터를 넘기는 코드는 컴파일러 단계에서 이미 깨진다.** 필요한 것은 **획득·해제 순서**(`_Atomic` 의 기본 순서 또는 락)다.

### (5) ★★ 못 막는 것 ③ — 순서(하드웨어) · 제5의 상태

**언제 쓰나** — (4)를 보고 「그럼 둘 다 `volatile` 로 두면 되겠네」라고 할 때.

```c
/* s32g2.c */
volatile int vx, vy;
_Atomic int  ax, ay;

int body_vol(void)    { vx = 1; return vy; }   /* 쓰고 나서 남의 것을 읽는다 */
int body_atomic(void) { ax = 1; return ay; }
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32g2.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
body_vol:
	endbr64
	mov	DWORD PTR vx[rip], 1
	mov	eax, DWORD PTR vy[rip]
	ret
body_atomic:
	endbr64
	mov	eax, 1
	xchg	eax, DWORD PTR ax[rip]
	mov	eax, DWORD PTR ay[rip]
	ret
ay:
ax:
vy:
vx:
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32g2.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
body_vol:                               # @body_vol
# %bb.0:
	mov	dword ptr [rip + vx], 1
	mov	eax, dword ptr [rip + vy]
	ret
.Lfunc_end0:
                                        # -- End function
body_atomic:                            # @body_atomic
# %bb.0:
	mov	eax, 1
	xchg	dword ptr [rip + ax], eax
	mov	eax, dword ptr [rip + ay]
	ret
.Lfunc_end1:
                                        # -- End function
vx:

vy:

ax:

ay:

```

- ★★ **`body_vol` 은 소스 순서 그대로**다 — `mov [vx], 1` 뒤에 `mov eax, [vy]`. 컴파일러는 **아무것도 안 바꿨다.**
- ★★ **`body_atomic` 은 `xchg`** 가 붙는다(두 컴파일러) — x86 에서 메모리를 건드리는 `xchg` 는 **암묵적으로 잠기는 명령**이라 앞의 쓰기가 끝나기 전에 뒤의 읽기가 못 나간다. ★ 이 문서가 **잰 것은 결과(아래의 0 판)뿐**이고, CPU 안에서 무슨 일이 났는지는 **재지 않았다.**
- ★★★ **어셈블리로는 순서 문제가 안 보인다** — 명령이 순서대로이기 때문이다. 그래서 **창을 바꿔** 실행해서 센다. ★ 이것이 **제5의 상태**다.

```c
/* s32g.c */
#include <pthread.h>
#include <stdio.h>
#include <stdatomic.h>

#define TRIALS 200000

static volatile int vx, vy, vr1, vr2;    /* ★ volatile 판 */
static atomic_int   ax, ay;              /* ★ _Atomic 판 (기본 순서 = seq_cst) */
static int          ar1, ar2;
static atomic_int   turn1, turn2, done1, done2;
static int          use_atomic;

static void *t1(void *arg) {
    (void)arg;
    for (int t = 1; t <= TRIALS; t++) {
        while (atomic_load(&turn1) != t) { }
        if (use_atomic) { atomic_store(&ax, 1); ar1 = atomic_load(&ay); }
        else            { vx = 1; vr1 = vy; }            /* 쓰고 나서 남의 것을 읽는다 */
        atomic_store(&done1, t);
    }
    return NULL;
}

static void *t2(void *arg) {
    (void)arg;
    for (int t = 1; t <= TRIALS; t++) {
        while (atomic_load(&turn2) != t) { }
        if (use_atomic) { atomic_store(&ay, 1); ar2 = atomic_load(&ax); }
        else            { vy = 1; vr2 = vx; }
        atomic_store(&done2, t);
    }
    return NULL;
}

static int both_zero(int atomic_mode) {
    pthread_t a, b;
    int count = 0;
    use_atomic = atomic_mode;
    atomic_store(&turn1, 0); atomic_store(&turn2, 0);
    atomic_store(&done1, 0); atomic_store(&done2, 0);
    pthread_create(&a, NULL, t1, NULL);
    pthread_create(&b, NULL, t2, NULL);
    for (int t = 1; t <= TRIALS; t++) {
        vx = vy = 0; atomic_store(&ax, 0); atomic_store(&ay, 0);
        atomic_store(&turn1, t); atomic_store(&turn2, t);
        while (atomic_load(&done1) != t || atomic_load(&done2) != t) { }
        if (atomic_mode ? (ar1 == 0 && ar2 == 0) : (vr1 == 0 && vr2 == 0)) count++;
    }
    pthread_join(a, NULL);
    pthread_join(b, NULL);
    return count;
}

int main(void) {
    int v = both_zero(0);
    printf("volatile : 두 스레드가 둘 다 0 을 읽은 판이 있나 = %s · 판 수 : %d / %d\n",
           v > 0 ? "있다" : "없다", v, TRIALS);
    int a = both_zero(1);
    printf("_Atomic  : 두 스레드가 둘 다 0 을 읽은 판이 있나 = %s · 판 수 : %d / %d\n",
           a > 0 ? "있다" : "없다", a, TRIALS);
    return 0;
}
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -pthread s32g.c -o x ; ./x (cc exit=0 · run exit=0) =====
volatile : 두 스레드가 둘 다 0 을 읽은 판이 있나 = 있다 · 판 수 : 2670 / 200000
_Atomic  : 두 스레드가 둘 다 0 을 읽은 판이 있나 = 없다 · 판 수 : 0 / 200000
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -pthread s32g.c -o x ; ./x (cc exit=0 · run exit=0) =====
volatile : 두 스레드가 둘 다 0 을 읽은 판이 있나 = 있다 · 판 수 : 15458 / 200000
_Atomic  : 두 스레드가 둘 다 0 을 읽은 판이 있나 = 없다 · 판 수 : 0 / 200000
```

```text
   스레드 A : vx = 1;  r1 = vy;          스레드 B : vy = 1;  r2 = vx;

   「소스 순서대로」라면 둘 중 적어도 하나는 1 을 봐야 한다
   ★ 그런데 volatile 판에서 r1 = 0 · r2 = 0 이 「있다」

   A 의 vx = 1 ──► [A 의 저장 버퍼] ····· (아직 메모리에 안 감)
   A 의 r1 = vy ─────────────────────────► 메모리 : vy = 0   ★ 먼저 도착
   (B 도 똑같이)                                              -> r1 = r2 = 0
```

그림 해설 (한 단계씩):

- ★★★ **`volatile` 판에서 둘 다 0 을 본 판이 「있다」** — 두 컴파일러 다. 명령은 순서대로인데 **결과는 순서대로가 아니다.** CPU 가 쓰기를 **저장 버퍼에 잠깐 두는 사이** 뒤의 읽기가 먼저 갔다 — 이것이 이 결과를 설명하는 통상의 모형이고, ★ 이 문서는 **모형이 아니라 결과만** 셌다.
- ★★★ **`_Atomic`(기본 순서 seq_cst) 판은 `0 / 200000`** — `xchg` 가 저장 버퍼를 비운다.
- ★★ **판 수는 흔들리는 칸**이다 — 결론은 「**있다 / 없다**」다.
- ★★ **「없다」는 이 창이 증명하지 못한다** — 20만 판에서 0 이었다는 것은 **관찰**이다. `_Atomic` 에서 이 결과가 **불가능하다는 것**은 표준의 seq_cst 규칙이 말한다.
- ★ **`volatile` 판은 데이터 경쟁이라 UB** 다 — 「둘 다 0」이 나오는 것도 **UB 의 한 결과**다. 결론은 「`volatile` 이 이것을 막아 주지 않는다」까지다.

비용 — **`volatile` 은 CPU 에게 아무것도 말하지 않는다.** 순서가 필요하면 **`_Atomic`**, 또는 **`atomic_thread_fence`** 다.

### (6) ★★ 정당한 자리 ② — `setjmp` 뒤의 지역 변수

**언제 쓰나** — `setjmp`/`longjmp` 로 오류를 되돌리는 코드에서 **되돌아온 뒤 지역 변수를 읽을** 때.

```c
/* s32h.c */
#include <setjmp.h>
#include <stdio.h>

static jmp_buf jb;

static void jump(void) { longjmp(jb, 1); }

int main(void) {
    int          plain = 1;
    volatile int vol   = 1;
    if (setjmp(jb) == 0) {
        plain = 2;                       /* ★ setjmp 뒤에 바꾼 지역 변수 */
        vol   = 2;
        jump();
    }
    printf("longjmp 뒤 : plain = %d · vol = %d\n", plain, vol);
    return 0;
}
```

```text
===== setjmp/longjmp 뒤의 지역 변수 — 컴파일러 2 × 최적화 3 (exit=0) =====
gcc    -O0  cc exit=0 경고 0건 | longjmp 뒤 : plain = 2 · vol = 2
gcc    -O1  cc exit=0 경고 0건 | longjmp 뒤 : plain = 1 · vol = 2
gcc    -O2  cc exit=0 경고 0건 | longjmp 뒤 : plain = 1 · vol = 2
clang  -O0  cc exit=0 경고 0건 | longjmp 뒤 : plain = 2 · vol = 2
clang  -O1  cc exit=0 경고 0건 | longjmp 뒤 : plain = 1 · vol = 2
clang  -O2  cc exit=0 경고 0건 | longjmp 뒤 : plain = 1 · vol = 2
gcc -O2 -Wclobbered 를 따로 켜도 경고 0건
```

- ★★★ **`vol` 은 여섯 벌 다 `2`** — `volatile` 지역 변수는 **`longjmp` 뒤에도 값을 지킨다**(표준).
- ★★★ **`plain` 은 `-O0` 에서 `2`, `-O1`·`-O2` 에서 `1`** — `setjmp` 시점의 **레지스터 값으로 되돌려졌다.** 두 컴파일러가 **같은 모양**으로 갈렸다.
- ★★ **표준** — `setjmp` 를 부른 함수의 지역 변수 중 **`volatile` 이 아니고** `setjmp` 와 `longjmp` 사이에 **바뀐 것**은 `longjmp` 뒤 **불확정**이다. `1` 도 `2` 도 **보장이 아니다.**
- ★★ **경고가 0건**이다 — gcc 의 `-Wclobbered` 를 **따로 켜도 0건**. **도구가 침묵하는 자리**다.

비용 — **`setjmp` 뒤에 읽을 지역 변수는 `volatile`** 로 둔다. 안 두면 **최적화 수준이 값을 정한다.**

### (7) ★ 정당한 자리 ③ — 장치 레지스터(메모리 맵 I/O)

**언제 쓰나** — 특정 주소에 쓰는 것 자체가 **장치에 명령을 보내는** 자리. ★ 이 머신에는 그런 장치가 없어 **실행하지 않았다** — **어셈블리만** 본다.

```c
/* s32i.c */
#include <stdint.h>

#define REG_PLAIN (*(uint32_t *)0x40001000u)            /* 장치 레지스터라고 치자 */
#define REG_VOL   (*(volatile uint32_t *)0x40001000u)

void kick_plain(void) { REG_PLAIN = 1; REG_PLAIN = 1; }  /* 같은 값을 두 번 쓴다 */
void kick_vol(void)   { REG_VOL = 1; REG_VOL = 1; }
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32i.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
kick_plain:
	endbr64
	mov	DWORD PTR ds:1073745920, 1
	ret
kick_vol:
	endbr64
	mov	DWORD PTR ds:1073745920, 1
	mov	DWORD PTR ds:1073745920, 1
	ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s32i.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' (cc exit=0) =====
kick_plain:                             # @kick_plain
# %bb.0:
	mov	dword ptr [1073745920], 1
	ret
.Lfunc_end0:
                                        # -- End function
kick_vol:                               # @kick_vol
# %bb.0:
	mov	dword ptr [1073745920], 1
	mov	dword ptr [1073745920], 1
	ret
.Lfunc_end1:
                                        # -- End function
```

- ★★★ **비-`volatile` 은 같은 값을 두 번 쓰는 것을 한 번으로 합쳤다** — 두 컴파일러 다. 장치에게는 **「두 번 두드려라」가 한 번이 된다.**
- ★★★ **`volatile` 은 두 번 다 남는다** — 이것이 `volatile` 이 **원래 만들어진 자리**다.
- ★ **정수를 포인터로 바꾸는 것**(`(uint32_t *)0x40001000u`)은 **구현 정의**다. 이 주소가 무엇인지는 플랫폼이 정한다.
- ★ **실행 창은 「못 잰 것」이다** — 쓰면 이 머신에서는 그 주소가 매핑되지 않아 죽는다. **그 결과는 장치 레지스터의 동작과 무관**하므로 싣지 않는다.

### (8) ★★ TSan 은 `volatile` 을 무엇으로 보나

**언제 쓰나** — 「`volatile` 을 붙였으니 경쟁 검사기도 봐주겠지」라고 할 때.

```c
/* s32j.c */
#include <pthread.h>
#include <stdio.h>

static volatile int counter;             /* ★ volatile 만 붙였다 */

static void *work(void *arg) {
    (void)arg;
    for (int i = 0; i < 1000; i++) counter++;
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, work, NULL);
    pthread_create(&t2, NULL, work, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    fprintf(stderr, "끝 — counter 를 찍지 않는다(값은 흔들린다)\n");
    return 0;
}
```

```c
/* s32k.c */
#include <pthread.h>
#include <stdio.h>

static _Atomic int counter;              /* ★ _Atomic */

static void *work(void *arg) {
    (void)arg;
    for (int i = 0; i < 1000; i++) counter++;
    return NULL;
}

int main(void) {
    pthread_t t1, t2;
    pthread_create(&t1, NULL, work, NULL);
    pthread_create(&t2, NULL, work, NULL);
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);
    printf("counter = %d\n", counter);
    return 0;
}
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O1 -g -fsanitize=thread -ffile-prefix-map="$PWD"=. s32j.c -o tj && ./tj 2>&1 >/dev/null | grep -E '^(WARNING|SUMMARY)|reported|^끝' (exit=66) =====
WARNING: ThreadSanitizer: data race (pid=4100636)
SUMMARY: ThreadSanitizer: data race s32j.c:8:43 in work
끝 — counter 를 찍지 않는다(값은 흔들린다)
ThreadSanitizer: reported 1 warnings
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O1 -g -fsanitize=thread -ffile-prefix-map="$PWD"=. s32k.c -o tk && ./tk (exit=0) =====
counter = 2000
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -g -fsanitize=thread -ffile-prefix-map="$PWD"=. s32j.c -o gj && ./gj 2>&1 >/dev/null (exit=66) =====
FATAL: ThreadSanitizer: unexpected memory mapping 0x6196e95bd000-0x6196e95be000
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -g -fsanitize=thread -ffile-prefix-map="$PWD"=. s32j.c -o gj && setarch -R ./gj 2>&1 >/dev/null | grep -E '^(WARNING|SUMMARY)|reported|^끝' (exit=66) =====
WARNING: ThreadSanitizer: data race (pid=4101696)
SUMMARY: ThreadSanitizer: data race s32j.c:8 in work
끝 — counter 를 찍지 않는다(값은 흔들린다)
ThreadSanitizer: reported 1 warnings
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O1 -g -fsanitize=thread -ffile-prefix-map="$PWD"=. s32k.c -o gk && setarch -R ./gk (exit=0) =====
counter = 2000
```

- ★★★ **TSan 은 `volatile int` 의 `++` 를 `data race` 로 잡는다** — 두 컴파일러 다, `SUMMARY … s32j.c:8 … in work` · **`exit=66`**. **`volatile` 은 TSan 에게 아무 뜻도 없다.**
- ★★ **`_Atomic` 판은 침묵** · `counter = 2000` · `exit=0`.
- ★★★ **gcc 의 TSan 은 이 머신에서 그대로는 안 돈다** — **`FATAL: ThreadSanitizer: unexpected memory mapping`** · `exit=66`. **`setarch -R`**(주소 무작위화 끄기)로 돌리면 된다. clang 18 의 TSan 은 그대로 돌았다.\
  ★ 「gcc 에 TSan 이 없다」고 적을 뻔한 자리다 — **도구가 없는 것이 아니라 환경이 맞지 않은 것**이었다.
- ★ gcc 는 `s32j.c:8`, clang 은 `s32j.c:8:43` — **칸 번호는 clang 만** 준다.
- ★ **리포트의 「어느 스레드가 먼저 썼나」 줄은 싣지 않았다** — 실행마다 바뀔 수 있는 칸이라 `grep` 으로 걸렀고, 배너에 그 명령을 적었다.

비용 — **`volatile` 로는 TSan 을 조용히 시킬 수 없다** — 그리고 그것이 옳다. TSan 이 말하는 것이 **표준의 판정(데이터 경쟁 = UB)이다**.

### (9) ★ Java 의 `volatile` 은 이름만 같다

- ★★★ **Java 의 `volatile` 은 메모리 순서를 보장한다** — 한 스레드의 `volatile` 쓰기와 다른 스레드의 그 읽기 사이에 **앞뒤 관계(happens-before)** 가 선다. (4)·(5)가 **Java 에서는 안 난다.**
- ★★ **그런데 원자성은 Java 도 없다** — `volatile int++` 가 잃는 것은 같다. 정본은 [Java 33 — `synchronized`·`volatile`](../../../java/syntax/33-synchronized-and-volatile/)이다.
- ★ 이 편은 **Java 를 던지지 않았다** — 비교는 그 편의 실측과 JLS 인용에 기댄다.

```text
                     C volatile           Java volatile          C _Atomic (기본)
   접근을 지우지 않음    ★ 보장               보장                    보장
   원자성(++)          ✗                    ✗                      ★ 보장
   스레드 사이 순서     ✗ (UB — 데이터 경쟁)   ★ 보장(happens-before)   ★ 보장(seq_cst)
```

## 문법 — 형태와 규칙

### 형태

(1)의 `s32a.c` · (2)의 `s32c.c` · (6)의 `s32h.c` 가 이 절의 **실제로 컴파일되는 형태**다. 쓰는 자리를 한 줄씩:

| 쓴 꼴 | 자리 | 무엇을 막나 | 층 |
|---|---|---|---|
| `volatile int flag;` | 바깥이 바꾸는 값을 **매번 읽기** | 로드 제거·합치기 | ★★★ 표준(무엇이 접근인가는 구현 정의) |
| `static volatile sig_atomic_t got;` | 시그널 핸들러 ↔ 메인 | 위 + ★ **핸들러에서 써도 UB 가 아닌 유일한 비원자 객체** | 표준 |
| `volatile int v = 1;`(`setjmp` 함수 안) | `longjmp` 뒤에 읽기 | ★ 되돌려지는 것 | 표준 |
| `*(volatile uint32_t *)ADDR = 1;` | 장치 레지스터 | 스토어 합치기 | 표준 + 주소 변환은 구현 정의 |
| `_Atomic int a;` · `a++` | 스레드 사이 카운터 | ★★★ **원자성 · 순서까지** | ★ 조건부 표준(선택 기능) |

### 금지 사례 — 어느 것이 무슨 층인가

| 쓴 꼴 | 진단 · 종료 코드 | 층 | 어느 절 |
|---|---|---|---|
| 두 스레드가 `volatile int v` 에 `v++` | 경고 0 · 잃었나 **예** · TSan `data race` **`exit=66`** | ★★★ UB(데이터 경쟁) | (3)·(8) |
| `volatile` 깃발로 비-`volatile` 데이터 넘기기 | 경고 0 · 어셈블리에서 **`data = 1` 이 사라짐** | ★★ 스레드 사이면 UB(데이터 경쟁) | (4) |
| 핸들러가 비-`volatile` `static int` 에 쓰기 | 경고 0 · `-O2` **`run exit=124`** 또는 **안 기다림** | ★★★ UB | (2) |
| `setjmp` 뒤 바뀐 비-`volatile` 지역 변수 읽기 | ★ `-Wclobbered` 까지 **경고 0** · `-O0` 2 / `-O2` 1 | ★★ 불확정 표현 | (6) |

### 규칙 불릿

- ★★★ **`volatile` 접근은 관찰 가능한 부수 효과**다 — 컴파일러가 **지우거나 합치거나 루프 밖으로 뺄 수 없다.**
- ★★★ **「무엇이 `volatile` 접근인가」는 구현 정의**다 — 표준이 그 정의를 구현에 넘겼다.
- ★★★ **`volatile` 은 원자성을 안 준다** — clang 은 `++` 를 명령 하나로 만들었는데도 잃었다(`lock` 이 없다).
- ★★★ **`volatile` 은 비-`volatile` 접근과의 순서를 안 준다** — `data = 1` 이 사라졌고, 두 `data` 읽기가 `ready` 를 넘어 합쳐졌다.
- ★★★ **`volatile` 은 CPU 의 순서를 안 준다** — 둘 다 0 을 본 판이 **있었다.**
- ★★★ **두 스레드가 `volatile` 을 같이 고치면 데이터 경쟁 — UB** 다. TSan 이 잡는다.
- ★★ **정당한 자리는 셋** — 장치 레지스터 · `setjmp` 뒤 지역 변수 · 시그널 핸들러의 `volatile sig_atomic_t`.
- ★★ **스레드 사이의 값은 `_Atomic`** 이다 — 잃은 수 0 · 판 수 0. 단 **선택 기능**이다.
- ★ **`-O0` 은 대조군이지 기준이 아니다** — `volatile` 없이도 대부분 남고, 그래서 **`-O0` 에서만 시험하면 문제가 안 보인다.**

## 어디서 틀리나

### 1. ★★★ 「두 스레드가 쓰는 변수니까 `volatile`」

**원자성도 순서도 안 준다**((3)·(4)·(5)). 이 판에서 **수백만 번을 잃었고**, TSan 은 **데이터 경쟁**이라고 말했다.

### 2. ★★★ 「clang 은 `v++` 를 명령 하나로 만드니까 안전하다」

**명령 하나 ≠ 원자적**이다((3)). `inc dword ptr [v]` 도 잃었다 — **`lock`** 이 없기 때문이다.

### 3. ★★★ 「`ready` 가 `volatile` 이니 그 앞의 쓰기는 먼저 보인다」

**컴파일러가 이미 `data = 1` 을 지웠다**((4)). 설령 안 지워도 **CPU 가 순서를 바꾼다**((5)).

### 4. ★★ 「`-O0` 에서 돌려 봤더니 괜찮다」

**`-O0` 은 `volatile` 이 없어도 대부분 다시 읽는다**((1)·(2)). 시그널 깃발은 `-O0` 에서 깨고 **`-O2` 에서 멈췄다.** 판 격자를 돌려라.

### 5. ★★ 「`volatile` 은 느리니까 빼자」

**재지 않았다** — 이 편은 **명령 수**만 셌다. 빼도 되는지는 **속도가 아니라 그 자리가 셋 중 하나냐**로 정한다.

### 6. ★★ 「`setjmp` 뒤에 값이 이상한데 경고가 없다」

**`-Wclobbered` 를 켜도 0건**이었다((6)). 그 값은 **불확정**이다 — `volatile` 로 둔다.

### 7. ★ 「gcc 에는 TSan 이 안 된다」

**환경 문제**였다((8)). `FATAL: unexpected memory mapping` 은 **`setarch -R`** 로 풀렸다. 없다고 적기 전에 **돌려 본 블록**을 남겨라.

### 8. ★ 「Java 에서 `volatile` 이면 되던데」

**Java 의 `volatile` 은 순서를 보장한다**((9)). C 의 `volatile` 은 **이름만 같다.**

## 구현 세부사항 대 언어 보장

C 에서는 「**돌아갔다**」가 아무것도 증명하지 못한다. 다섯 층을 갈라야 한다.\
★★★ **이 주제는 「표준」과 「구현 정의」의 경계가 가장 가늘다** — `volatile` 접근을 지울 수 없다는 것은 표준인데, **무엇이 접근인가는 구현 정의**다.\
★★★ **「UB」가 가장 두껍다** — 스레드 사이의 `volatile` 은 전부 데이터 경쟁이다.

| 층 | 뜻 | 이 주제에서 해당하는 것 | 어떻게 확인했나 |
|---|---|---|---|
| ★★★ **표준** | 어느 구현에서도 같다 | ★★★ **`volatile` 접근은 관찰 가능한 부수 효과**(지우거나 합칠 수 없다) · **데이터 경쟁은 UB** · 시그널 핸들러는 **`volatile sig_atomic_t`(와 lock-free 원자 객체)만** 쓸 수 있다 · **`longjmp` 뒤 비-`volatile` 로 바뀐 지역 변수는 불확정** · `_Atomic` 연산의 원자성과 기본 순서(seq_cst) | 어셈블리 격자 · `s32c` 네 벌 깸 · `vol = 2` 여섯 벌 · `_Atomic` 잃은 수 0 · 판 수 0 |
| ★★ **조건부 표준** | 매크로가 정의될 때만 | ★★ **`_Atomic`/`<stdatomic.h>` 는 선택 기능** — `__STDC_NO_ATOMICS__` 가 정의되면 없다 · 이 편의 스레드는 **POSIX `pthread`**(ISO C 밖) | 이 판에서는 **있었다**(`lock add`) |
| ★★★ **구현 정의** | 문서화 의무가 있다 | ★★★ **「`volatile` 객체에 대한 접근이 무엇인가」** — 표준이 이 한 문장으로 구현에 넘겼다(부록 J 의 구현 정의 목록 — 한정자 항의 첫 줄에도 있다) · ★ 정수 → 포인터 변환(`0x40001000u`) · 명령 선택(clang `inc` 대 gcc `mov/add/mov`) | 어셈블리 — **읽기·쓰기가 명령 몇 개로 번역되나** |
| ★★ **미명시** | 몇 가지 중 하나 · 문서화 의무도 없다 | ★★ **`longjmp` 뒤 `plain` 의 값**(불확정 표현 — `int` 라 이 구현에서는 미명시 값) | `-O0` 2 · `-O1`/`-O2` 1 — 두 컴파일러가 같은 모양 |
| ★★★ **UB** | 아무 일이나 | ★★★ **스레드 사이 `volatile` 접근**(`++` 경쟁 · 깃발로 데이터 넘기기 · 저장 버퍼 실험) · ★★ **핸들러가 비-`volatile` 정적 객체에 쓰기** | 잃었나 **예**(10/10) · `data = 1` 소멸 · 둘 다 0 **있다** · `run exit=124` / 안 기다림 · TSan `exit=66` |

### ★★ 「도구가 못 보는 것」을 층마다

| 층 | 그 층에서 **도구가 침묵하는 자리** |
|---|---|
| ★★★ **표준** | ★★ **`volatile` 이 「필요한데 빠진」 자리를 말해 주는 경고가 없다** — 시그널 깃발 `int got` 은 **경고 0건**으로 `-O2` 에서 멈췄다 |
| ★★ **조건부 표준** | ★ `_Atomic` 이 **없는 판**에서는 컴파일 에러가 날 것이다 — 이 판에는 있어 **던질 수 없었다** |
| ★★★ **구현 정의** | ★★★ **「무엇이 접근인가」를 말해 주는 것은 어셈블리뿐**이다 — 컴파일러 진단은 아무 말도 안 한다. ★ clang 의 `inc [v]` 가 **읽기+쓰기 한 번씩**인지는 명령만 봐서는 **CPU 의 일**이다 |
| ★★ **미명시** | ★★★ **`-Wclobbered` 를 켜도 `setjmp` 뒤 값에 경고 0건** |
| ★★★ **UB** | ★★★ **컴파일러는 스레드 사이 `volatile` 에 경고 0건** — TSan 만 잡는다. ★★ **TSan 은 「순서」 실험(5)을 던지지 않았다** — 이 편은 `++` 경쟁에만 TSan 을 썼다. ★ **gcc TSan 은 환경에 따라 `FATAL`** 로 아예 안 돈다 |
| ★★ **(층을 가로지름)** | ★ **「종료 코드가 0인데 ill-formed」는 이 편에 새 항목이 없다** — `volatile` 의 오용은 **문법이 아니라 의미**의 문제라 전부 **적격한 프로그램**이다. ★★ 대신 **「종료 코드 0인데 UB」가 넷**이다(금지 사례 표 — 전부 `cc exit=0`) |

- ★★ **이 표의 결론 세 줄**
  - ★★★ **`volatile` 의 보장은 컴파일러 안에서 끝난다** — 어셈블리가 그 보장을 보여 주고, 그 밖(원자성·CPU 순서)은 **실행해서 세야만** 보인다.
  - ★★★ **가장 위험한 칸은 `-O0` 에서 되는 시그널 깃발**이다 — 테스트는 `-O0`, 배포는 `-O2` 인 빌드에서 **배포판만 멈춘다.**
  - ★★ **TSan 이 `volatile` 을 봐주지 않는 것이 이 편의 가장 강한 근거**다 — 표준의 판정(데이터 경쟁)을 **도구가 그대로** 말했다.

## 언제 쓰고 언제 안 쓰나

| 하고 싶은 것 | 옳은 선택 | 쓰면 안 되는 것 |
|---|---|---|
| 장치 레지스터 읽기·쓰기 | ★★★ **`volatile`** 포인터 | 보통 포인터(쓰기가 합쳐진다) |
| 시그널 핸들러가 세우는 깃발 | ★★★ **`static volatile sig_atomic_t`** | `int`·`bool`(판에 따라 멈춘다) |
| `setjmp` 뒤에 읽을 지역 변수 | ★★ **`volatile`** | 보통 지역 변수(되돌려진다) |
| 두 스레드가 같이 쓰는 카운터 | ★★★ **`_Atomic`**(또는 락) | ★★★ `volatile`(잃는다) |
| 스레드 사이의 준비 깃발 + 데이터 | ★★★ **`_Atomic` 깃발(획득·해제)** 또는 락 | ★★★ `volatile` 깃발(데이터가 사라지고 순서가 뒤집힌다) |
| 스레드 코드를 검사 | ★★ **TSan**(gcc 는 `setarch -R` 이 필요할 수 있다) | `-O0` 에서 돌려 보기 |

판단 규칙 두 줄.

- ★★★ **「이 값을 바꾸는 것이 다른 스레드인가」를 먼저 묻는다** — 그렇다면 `volatile` 은 **답이 아니다.**
- ★★ **아니라면 「장치 · `longjmp` · 시그널」 중 하나인가를 묻는다** — 그 셋이 `volatile` 의 자리다.

## 핵심 문장

- ★★★ **`volatile` 은 「매번 가서 본다」만 약속한다** — 로드를 루프 밖으로 빼거나, 세 읽기를 하나로, 두 쓰기를 하나로 합치지 못하게 한다.
- ★★★ **gcc `-O2` 는 `volatile` 없는 대기 루프를 `jmp .L3`(읽지 않고 영원히)로, clang 은 `ret`(루프째 삭제)로 만들었다.**
- ★★★ **`volatile int` 의 두 스레드 `++` 는 10 번 중 10 번 잃었다** — clang 이 `inc` 한 명령으로 만들었는데도. `_Atomic` 은 `lock` 이 붙어 0 이었다.
- ★★★ **`volatile` 쓰기를 사이에 두고도 `data = 1` 이 사라졌다** — 비-`volatile` 접근과의 순서는 안 지킨다.
- ★★★ **CPU 의 저장 버퍼 때문에 `volatile` 판에서 둘 다 0 을 본 판이 있었다** — `_Atomic`(`xchg`)은 0 판.
- ★★★ **「`volatile` 접근이 무엇인가」는 구현 정의**이고, **스레드 사이 `volatile` 은 데이터 경쟁 — UB** 다. TSan 이 `data race` 로 잡았다.
- ★★ **정당한 자리는 셋** — 장치 레지스터 · `setjmp` 뒤 지역 변수(`vol = 2` 여섯 벌) · `volatile sig_atomic_t`(네 벌 깸).
- ★ **Java 의 `volatile` 은 순서를 보장한다** — 이름만 같다.

## 관련 자료

- [31번 형제 — `const` 와 포인터 const 위치](../31-const-and-pointer-const-placement/) — ★★★ **직접 선행 — 한정자 사슬.** `const` 는 「안 고친다」, `volatile` 은 「매번 본다」. 31 에서 `const volatile` 포인터로 **메모리를 다시 읽은 것**이 이 편의 첫 쓰임이었다.
- [`foundations/process-thread/`](../../../../process-thread/) — ★★ **경계.** 경쟁·가시성·락의 개념은 그쪽이 정본이다.
- [28번 형제 — 저장 기간](../28-choosing-among-four-storage-durations/) — ★ `_Thread_local` 은 **공유하지 않는** 쪽의 답이다. 이 편은 **공유하는** 쪽.
- [30번 형제 — 초기화 규칙과 불확정 값](../30-initialization-rules-and-indeterminate-values/) — ★ (6)의 **불확정 표현**이 무엇인지의 정본.
- 목록의 **58번 주제** — UB 를 잡는 도구. TSan **사용법**의 정본.
- ★ **Java 갈래** — [Java 33 — `synchronized`·`volatile`](../../../java/syntax/33-synchronized-and-volatile/). **이름은 같고 뜻이 다른** 짝.

## 용어 풀이

> **`volatile`** — 「이 객체의 읽기·쓰기는 **매번 실제로 한다**」는 한정자. 지우거나 합치지 못한다.\
> 예: `volatile int flag;` 를 기다리는 루프는 매번 메모리를 읽는다.

> **관찰 가능한 부수 효과** — 프로그램 밖에서 보일 수 있는 일. `volatile` 접근·입출력이 여기 든다.\
> 예: 장치 레지스터에 쓰기.

> **`sig_atomic_t`** — 시그널 핸들러와 주고받을 수 있게 표준이 정한 정수 타입. **`volatile` 과 함께** 써야 한다.\
> 예: `static volatile sig_atomic_t got;`.

> **`_Atomic`** — C11 의 원자 타입 한정자. 연산이 **나뉘지 않고**, 기본 순서(seq_cst)로 스레드 사이 **순서까지** 준다. 선택 기능이다.\
> 예: `_Atomic int a; a++;` → `lock add`.

> **`lock` 접두어(x86)** — 명령의 읽기·쓰기를 **다른 코어가 끼어들 수 없게** 묶는다.\
> 예: `lock inc dword ptr [a]`.

> **데이터 경쟁(data race)** — 앞뒤 관계 없이 두 스레드가 같은 자리를 건드리고 하나라도 쓰기이며 하나라도 비원자인 것. **UB**.\
> 예: `volatile int` 에 두 스레드가 `++`.

> **저장 버퍼(store buffer)** — CPU 가 쓰기를 잠깐 모아 두는 곳. 뒤의 읽기가 앞의 쓰기를 **앞지를 수 있다.**\
> 예: (5)의 「둘 다 0」.

> **TSan(ThreadSanitizer)** — 실행 중 **데이터 경쟁**을 찾는 도구. `volatile` 을 특별 취급하지 않는다.\
> 예: `SUMMARY: ThreadSanitizer: data race s32j.c:8:43 in work`.

## 더 들어가면

- ★★ **`atomic_thread_fence` 와 `memory_order_acquire`/`release`** — seq_cst 보다 가벼운 순서. ★ **던지지 않았다.**
- ★★ **TSan 에 (5)의 저장 버퍼 실험을 주면** — 데이터 경쟁으로 잡을 것이다. ★ **던지지 않았다.**
- ★ **비-`volatile` `p++` 를 두 스레드로 돌리면** — `-O2` 에서 `add [p], 1` 한 명령이다. 루프째 접히면 **안 잃은 것처럼** 보일 수 있다. ★ **돌려 보지 않았다**(어셈블리만).
- ★ **`volatile` 구조체의 멤버 접근이 명령 몇 개가 되나** — 구현 정의 칸의 더 깊은 자리. ★ **던지지 않았다.**
- ★ **ARM 같은 약한 메모리 모델에서의 (5)** — x86 보다 더 많은 재배치가 허용된다. ★ **못 잰 것** — 이 머신은 x86-64 다.
- ★ **Java 의 저장 버퍼 실험** — ★ **던지지 않았다**. [Java 33](../../../java/syntax/33-synchronized-and-volatile/)의 실측에 기댄다.
