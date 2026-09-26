# c/syntax/32 — `volatile` 이 실제로 보장하는 것: 「**매번 가서 본다 — 그것뿐이다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s32a.c`\~`s32k.c` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **판 격자** — 1·2번은 컴파일러 2 × `-O0`/`-O2`, 6번은 × `-O0`/`-O1`/`-O2`.
> ★★★ **본체 창은 `-O2` 어셈블리.** ★★ **못 막는 것(3·5)은 실행해서 센 수**로 봤다 — 어셈블리로는 안 보인다.
> ★★★ **시간은 재지 않았다** — 「`volatile` 은 느리다」는 이 문서의 주장이 아니다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ★★★ **`volatile int` 의 잃은 수** | ★★★ **「잃었나 = 예 / 아니오」** — 10 번 중 10 대 0 |
> | ★★★ **`volatile` 판의 둘 다 0 을 본 판 수** | ★★★ **「있다 / 없다」** · `_Atomic` 의 `잃은 수 : 0` · `0 / 200000` |
> | ★ TSan 의 `(pid=N)` · gcc TSan `FATAL` 줄의 주소 | ★★★ **어셈블리 전부** · 명령 수 격자 |
> | — | ★★ 시그널 격자의 `run exit`(`0`·`124`) · `setjmp` 격자 · TSan `SUMMARY` 줄 · 종료 코드 |
>
> ★★ **정규화 규칙 = 기본 둘(주소 · PID) + 이 편 고유 셋**(잃은 수 · 판 수 · `pid=`) — 위 표의 「흔들린다」 세 줄과 같은 목록이다. `_Atomic` 줄에는 걸리지 않게 짰다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `-O2` 어셈블리 — **`volatile` 이 없으면 로드가 빠지고 합쳐지고, 있으면 전부 남는다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`wait_plain`** — gcc `-O2` 는 **한 번 읽고**(`mov eax, [plain_flag]`) 0 이면 **`.L3: jmp .L3`**(읽지 않고 영원히). clang `-O2` 는 **`ret`** — 루프째 지웠다.
- ★★★ **`wait_vol`** — 두 컴파일러 다 **루프 안에서 매번 읽는다**(`.L6:` · `.LBB1_1:`).
- ★★ **`read3`** — 비-`volatile` 로드 **1**(+`lea` 로 ×3) · `volatile` **3**. **`write2`** — 비-`volatile` 스토어 **1**(`2` 만) · `volatile` **2**.
- ★★ **`-O0`** 에서는 비-`volatile` 도 대부분 남는다 — `wait_plain` 이 **루프 안에서** 읽는다. ★ **갈린 칸** — `read3_plain` 을 **gcc `-O0` 은 로드 1**(접었다), **clang `-O0` 은 3**.
- ★ **clang 의 루프 삭제** — C 는 「제어식이 상수가 아니고 입출력·`volatile` 접근·동기화·원자 연산이 없는 루프는 **끝난다고 가정해도 된다**」고 허용한다. **`volatile` 접근이 들어가면 그 가정이 안 선다.**

### 2. 시그널 깃발 — **`volatile sig_atomic_t` 만 네 벌 다 깨고, `int` 는 `-O2` 에서 멈추거나 안 기다린다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`s32c`(`volatile sig_atomic_t`)** — 네 벌 다 **`run exit=0` · `got = 1`**.\
  **`s32b`(`int`)** — `-O0` 둘은 깨고, **`-O2` 둘은 `run exit=124`**(3초 안에 못 깸).\
  **`s32b2`(`int` · 루프 뒤 읽기 없음)** — gcc `-O2` 는 `124`, **clang `-O2` 는 `exit=0` · `깼다`**.
- ★★★ **「기다리지 않고 깨는」 칸은 `s32b2` 의 clang `-O2`** — 1번의 `wait_plain` 처럼 **루프째 지웠다.** 1초를 기다리지 않고 바로 `깼다` 를 찍는다.
- ★★ **한 줄 차이** — clang `-O2` 어셈블리에서 `s32b` 는 **한 번 읽고 `.LBB0_1: jmp .LBB0_1`**(읽지 않고 영원히), 루프 뒤 `printf` 에는 `got` 대신 **`mov esi, 1`**. `s32b2` 는 **루프가 아예 없다**(`puts` 두 번). 둘 다 **UB 의 이 판 결과**다.
- ★★ **표준이 허락한 것** — 핸들러는 **`volatile sig_atomic_t` 에 값을 대입**하는 것(과 lock-free 원자 객체)만 할 수 있다. 그 밖의 정적 객체를 건드리면 **UB** 다.

### 3. `volatile int` 두 스레드 `++` — **잃었다(10/10) · `_Atomic` 은 안 잃었다(10/10)** ★★★

**출력**

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

**왜 그런가**

- ★★★ **두 컴파일러 다 「잃었나 = 예」**, `_Atomic` 은 「아니오」. **10 번 돌려 10 대 0** 이다 — 이 칸은 안 흔들린다.
- ★★ **잃은 수는 답이 아니다** — 실행마다 다르다(흔들리는 칸). 이 판에서 **백만 단위**였다는 것까지만 말한다.
- ★★★ **clang `-O2` 는 `inc dword ptr [rip + v]` 한 명령**이다. 그런데도 잃는다 — 명령 하나 안에서도 **읽기와 쓰기가 따로** 일어나고, 그 사이에 **다른 코어가 끼어든다.** 막는 것은 **`lock` 접두어**다.\
  ★ gcc 는 `mov / add / mov` **세 명령**이다 — 끼어들 틈이 더 눈에 보일 뿐, **둘 다 원자적이 아니다.**
- ★★ **`inc_atomic` 은 `lock`** 한 글자가 다르다 — gcc `lock add` · clang `lock inc`.

### 4. `volatile` 깃발로 데이터 넘기기 — **`data = 1` 이 사라지고, 두 `data` 읽기가 하나가 됐다** ★★

**출력**

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

**왜 그런가**

- ★★★ **`data = 1` 은 남지 않는다** — 두 컴파일러 다 `mov [ready], 1` 뒤에 **`mov [data], 2` 하나**뿐이다. `volatile` 쓰기를 **사이에 두고도** 비-`volatile` 쓰기 둘을 합쳤다.
- ★★★ **두 `data` 읽기는 하나**가 됐다 — gcc 는 **`ready` 뒤**(`mov eax, [ready]` → `mov edx, [data]`), clang 은 **`ready` 앞**(`mov eax, [data]` → `add eax, [ready]`). **두 컴파일러가 반대로 옮겼다.**
- ★★ **증명하는 것** — `volatile` 은 **`volatile` 접근끼리의 순서만** 지킨다. 비-`volatile` 접근은 그 주위를 넘나든다. **`volatile` 은 벽이 아니다.**

### 5. 쓰고 나서 읽기 20만 판 — **`volatile` 은 둘 다 0 이 「있다」, `_Atomic` 은 「없다」** ★★★

**출력**

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

**왜 그런가**

- ★★ **`body_vol` 은 소스 순서대로**(`mov [vx], 1` → `mov eax, [vy]`). **`body_atomic` 에는 `xchg`** 가 붙는다(두 컴파일러).
- ★★★ **`volatile` 판은 둘 다 0 을 본 판이 「있다」**(두 컴파일러) · **`_Atomic` 판은 「없다」**(`0 / 200000`).
- ★★★ **컴파일러가 아니라 CPU 가 순서를 바꿨다** — 명령은 순서대로인데 결과가 순서대로가 아니다. 쓰기가 **저장 버퍼**에 머무는 사이 뒤의 읽기가 먼저 갔다는 것이 통상의 설명이고, **이 문서는 결과만 셌다.**
- ★★ **`0 / 200000` 은 관찰**이다 — 「불가능」을 말하는 것은 **표준의 seq_cst 규칙**(모든 seq_cst 연산에 하나의 전체 순서가 있다)이다.
- ★ **제5의 상태** — 「순서가 지켜지나」를 **어셈블리로 물었더니 명령은 순서대로**였다. 그래서 **실행해서 결과를 세는 창**으로 바꿔 물었다. 바꾼 창은 「있다」는 증명하지만 **「없다」는 증명하지 못한다.**

### 6. `setjmp` 뒤 — **`vol` 은 여섯 벌 다 `2` · `plain` 은 `-O0` 2 · `-O1`/`-O2` 1 · 경고 0** ★★

**출력**

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

**왜 그런가**

- ★★★ **`vol = 2`**(여섯 벌) · **`plain`** — `-O0` 두 벌은 `2`, `-O1`·`-O2` 네 벌은 **`1`**(`setjmp` 시점의 레지스터 값으로 되돌려졌다). 두 컴파일러가 **같은 모양**으로 갈렸다.
- ★★ **경고 0건** — **`-Wclobbered` 를 따로 켜도 0건**이다.
- ★★ **표준** — `setjmp` 를 부른 함수의 지역 변수 중 **`volatile` 이 아니고 그 사이에 바뀐 것**은 `longjmp` 뒤 **불확정**이다. `1` 도 `2` 도 보장이 아니다.

### 7. 장치 레지스터 — **비-`volatile` 은 두 번 쓰기를 한 번으로 합쳤다** ★★

**출력**

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

**왜 그런가**

- ★★ **`kick_plain` 스토어 1 · `kick_vol` 스토어 2** — 두 컴파일러 다.
- ★★ 장치에게는 **「두 번 두드려라」가 「한 번」** 이 된다 — 레지스터에 쓰는 것이 곧 **명령**이면 동작이 바뀐다.
- ★ **실행하지 않은 이유** — 이 머신에는 그 주소에 장치가 없다. 실행하면 **매핑되지 않은 주소**라 죽을 뿐이고, **그 결과는 장치 레지스터의 동작과 무관**하다. 「**못 잰 것**」이다.
- ★ **정수 → 포인터 변환은 구현 정의**다.

### 8. TSan — **`volatile` 을 봐주지 않고 `data race` 로 잡는다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`WARNING: ThreadSanitizer: data race`** · `SUMMARY … s32j.c:8 … in work` · **`exit=66`** — 두 컴파일러 다.
- ★★ **`_Atomic` 은 침묵** · `counter = 2000` · `exit=0`.
- ★★★ **gcc TSan 을 그대로 돌리면 `FATAL: ThreadSanitizer: unexpected memory mapping`** · `exit=66` — 경쟁을 보기도 전에 죽는다. **`setarch -R`**(주소 무작위화 끄기)로 풀었다. clang 18 은 그대로 돌았다.
- ★★ **「도구가 없다」고 적기 전에 돌려 본 블록을 남겨라** — 여기서는 도구가 **있었는데 환경이 안 맞았다.** 그 블록이 곧 판정의 근거다.
- ★ **표준의 판정과 같다** — 두 스레드가 앞뒤 없이 같은 자리를 건드리고 하나라도 쓰기이며 비원자면 **데이터 경쟁 = UB**. `volatile` 은 **원자가 아니다.**

### 9. 정당한 자리 셋 ★★

**왜 그런가**

- ★★★ ① **장치 레지스터** — 장치가 바꾼다(또는 쓰기 자체가 명령) · ② **`setjmp` 뒤 지역 변수** — `longjmp` 가 레지스터를 되돌린다 · ③ **시그널 핸들러의 `volatile sig_atomic_t`** — 핸들러가 바꾼다.
- ★★ **다른 스레드가 없는 이유** — 셋은 전부 **같은 스레드 안에서** 「컴파일러가 모르는 사이에」 값이 바뀌는 자리다. 다른 스레드는 **CPU 순서와 원자성**까지 필요한데 `volatile` 은 **컴파일러에게만** 말한다.
- ★ **스레드 사이는 `_Atomic`**(또는 락). **선택 기능**이라는 것은 `__STDC_NO_ATOMICS__` 를 정의한 구현에는 **없어도 된다**는 뜻이다(이 판에는 있었다).

### 10. Java `volatile` — **이름만 같다** ★★

**왜 그런가**

- ★★★ **Java 는 스레드 사이 순서(happens-before)와 가시성을 보장**한다 — 4·5번 같은 일이 Java `volatile` 에서는 안 난다. **C 는 보장하지 않는다**(데이터 경쟁 — UB).
- ★★ **둘 다 원자성은 없다** — `volatile int++` 는 Java 에서도 잃는다([Java 33](../../../java/syntax/33-synchronized-and-volatile/)의 실측).
- ★ C 에서 가장 가까운 것은 **`_Atomic`**(기본 순서 seq_cst)이다.

### 11. 다섯 층 — **표준과 구현 정의의 경계가 가장 가늘고, UB 가 가장 두껍다** ★★★

**왜 그런가**

- **표준** — `volatile` 접근은 관찰 가능한 부수 효과 · 데이터 경쟁은 UB · 핸들러는 `volatile sig_atomic_t` · `longjmp` 뒤 비-`volatile` 은 불확정 · `_Atomic` 의 원자성과 seq_cst.
- **조건부 표준** — ★★ **`_Atomic`/`<stdatomic.h>` 자체**(선택 기능) · 이 편의 스레드는 **POSIX `pthread`**(ISO C 밖).
- **구현 정의** — ★★★ **「`volatile` 객체에 대한 접근이 무엇인가」** · 정수 → 포인터 · 명령 선택.
- **미명시** — `longjmp` 뒤 `plain` 의 값(불확정 — `int` 라 이 구현에서는 미명시 값).
- **UB** — 스레드 사이 `volatile`(`++` · 깃발 · 저장 버퍼) · 핸들러가 비-`volatile` 정적 객체에 쓰기.
- ★★★ **「무엇이 접근인가」는 구현 정의** — 표준은 「`volatile` 접근을 지우지 마라」까지만 정하고, **그 「접근」의 정의를 한 문장으로 구현에 넘겼다**(부록 J 의 구현 정의 목록에도 있다). 그래서 **어셈블리가 이 칸의 유일한 창**이다.
- ★★ **침묵** — 표준: 빠진 `volatile` 에 경고 0 · 조건부: 없는 판을 못 던짐 · 구현 정의: 진단이 「접근」을 말하지 않음 · 미명시: `-Wclobbered` 0건 · UB: 컴파일러 경고 0건(TSan 만).
- ★★ **「종료 코드 0인데 ill-formed」 새 항목은 없다** — `volatile` 오용은 **의미의 문제**라 전부 적격한 프로그램이다. 대신 **「종료 코드 0인데 UB」가 넷**이다.
- ★ **시간 창은 규칙으로 안 썼다** — 재지 않은 성능 주장을 금지한다. 명령 수만 셌다.

### 12. 경계 ★

**왜 그런가**

- **동시성 개념** — [`foundations/process-thread/`](../../../../process-thread/).
- **불확정 표현** — [30번 형제](../30-initialization-rules-and-indeterminate-values/) · **`const`** — [31번 형제](../31-const-and-pointer-const-placement/).
- **TSan 사용법** — 목록의 **58번 주제**.
- ★ 이 주제가 책임지는 것 — ① **막는 것**(어셈블리의 로드·스토어) ② **못 막는 것**(원자성 · 컴파일러 순서 · CPU 순서) ③ **정당한 자리 셋**.

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s32a.c` | ★★★ `wait_plain` gcc `jmp .L3` · clang `ret` · `volatile` 은 전부 남음 · 명령 수 격자 | 어셈블리 `-O2` 2 · `-O0` 1 · 격자 4벌 × 6함수 |
| `s32b.c`·`s32b2.c`·`s32c.c` | ★★★ `sig_atomic_t` 네 벌 깸 · `int` `-O2` **`124`** · clang `-O2` **안 기다림** | 12칸(`timeout 3`) · 실행 1 |
| `s32d.c`·`s32e.c` | ★★★ **잃었나 예 · `_Atomic` 아니오** · 10/10 · clang `inc` · `lock` | 실행 2 · 10회 · 어셈블리 2 |
| `s32f.c` | ★★ **`data = 1` 소멸** · 두 읽기 합침(앞·뒤 반대) | 어셈블리 2 |
| `s32g.c`·`s32g2.c` | ★★★ **둘 다 0 이 있다 · `_Atomic` 0 / 200000** · `xchg` | 실행 2 · 어셈블리 2 |
| `s32h.c` | ★★ `vol = 2` 여섯 벌 · `plain` `-O0` 2 · `-O1`/`-O2` 1 · 경고 0(`-Wclobbered` 포함) | 6벌 + 1 |
| `s32i.c` | 스토어 1 대 2 | 어셈블리 2 · ★ 실행은 못 잰 것 |
| `s32j.c`·`s32k.c` | ★★★ TSan `data race` · `exit=66` · `_Atomic` 침묵 · gcc `FATAL` → `setarch -R` | clang 2 · gcc 3 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙 + 이 편 고유 셋)로 대조했다. **흔들린 것은 잃은 수 · 판 수 · TSan 의 PID · `FATAL` 주소뿐**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1·4·7번 어셈블리** — 명령 선택은 컴파일러의 것이다. **「`volatile` 접근이 남는다」는 표준**이고 **그 모양**이 구현이다.
- ★★★ **3·5번의 「예」·「있다」** — UB 이고 **CPU 와 스레드 스케줄**에 달렸다. 결론은 「**`volatile` 이 막아 주지 않는다**」까지다.
- ★★ **2·6번 격자** — UB·불확정의 이 판 결과다.
- ★ gcc TSan 의 `FATAL` — **이 커널의 주소 배치**와 gcc 13 TSan 의 조합이다.

**`volatile` 접근을 지우거나 합칠 수 없다는 것 · 데이터 경쟁이 UB 인 것 · 핸들러에 허락된 형태 · `longjmp` 뒤 비-`volatile` 지역 변수가 불확정인 것 · `_Atomic` 의 원자성과 seq_cst 는 구현 의존이 아니다.**\
어느 C 구현에서도 같다(`_Atomic` 을 제공한다면).

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — `atomic_thread_fence` · acquire/release 순서 · TSan 에 5번 실험 · 비-`volatile` `p++` 두 스레드 실행 · `volatile` 구조체 멤버 · Java 의 저장 버퍼 실험.
- ★ **못 잰 것** — **7번의 실행**(장치가 없다) · **ARM 같은 약한 메모리 모델**(이 머신은 x86-64) · **시간**(규칙으로 안 쟀다).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **1번 명령 수 격자** — 최적화가 바뀌면 비-`volatile` 쪽이 움직인다.
- ★★ **2번 격자**(특히 clang 의 루프 삭제) · **6번 격자**.
- ★ **gcc TSan 의 `FATAL`** — 판이 오르면 `setarch` 없이 돌 수 있다.
- **`volatile` 의 규칙 자체는 다시 돌릴 필요가 없다** — C89(원자·메모리 모델은 C11) 이후 바뀐 적이 없다.
