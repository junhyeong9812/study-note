# architecture/10-calling-convention-and-stack-frame — 호출 규약과 스택 프레임: 함수 호출 한 번의 약속 — 정리 (힌트)

## 해결하는 문제

함수 호출은 점프 한 번이 아니다. 네 가지를 누군가 처리해야 한다.

```text
  caller ──호출──▶ callee
   1. 인자를 어디에 둘까?          (레지스터? 스택?)
   2. 끝나면 어디로 돌아올까?      (반환 주소를 어디에 저장?)
   3. 결과는 어디서 받을까?        (rax? x0?)
   4. callee가 내 레지스터를 망가뜨려도 되나? (누가 저장·복원?)
```

- 이 네 가지를 미리 정한 약속이 호출 규약이다.
  - *호출 규약(calling convention)*: 인자·반환값·반환 주소·레지스터 보존·스택 정렬을 caller와 callee가 어떻게 나눠 맡는지 정한 규칙. ABI의 일부다.
  - *ABI(Application Binary Interface)*: 따로 컴파일한 기계어끼리 맞물리게 하는 이진 수준의 약속. 호출 규약, 자료형 크기·정렬, 시스템 콜 방식 등을 정한다.
- 규약이 없으면 gcc로 만든 내 코드가 clang으로 만든 라이브러리 함수를 부를 수 없다. JVM이 네이티브 함수를 부를 수도 없다.

쉬운 예: 이어달리기 바통 터치다.
- 넘겨주는 구역(인자 위치), 받는 손(반환값 위치), 다음 주자에게 무엇을 남기고 갈지(보존 레지스터)를 미리 정해 둬야 한다.
- 각 주자의 짐(지역 변수)은 자기 칸에 쌓았다가 떠날 때 비운다. 이 칸이 *스택 프레임*이다.

똑같은 구조다.\
호출하면 보통 스택에 프레임 하나를 쌓고, 돌아올 때 걷는다(최적화 빌드는 프레임을 생략하거나 꼬리 호출에서 재사용하기도 한다 — 아래 `-O2` 실험). 스택은 크기가 정해져 있다.

실무 예:
- 깊은 재귀나 깊이 중첩된 JSON 파싱 → Java `StackOverflowError`, C는 `SIGSEGV`(exit 139).
- 경계 없는 `strcpy`로 지역 버퍼를 길게 넘치게 쓰면 프레임 위쪽의 반환 주소까지 덮일 수 있다([security/24](../../security/24-memory-safety-exploits/2-summary.md)).
- 프로파일러의 호출 그래프(flame graph)가 끊겨 보인다 — 프레임 포인터가 빠진 빌드.

## 동작·원리

### 1. 원고가 다룬 것 — 32비트 x86 cdecl

- 원고 [systems/call-stack](../../systems/call-stack/README.md)는 `subl $8, %esp`로 공간을 잡고 `addl $8, %esp`로 돌려주는 짝, `call`이 반환 주소를 push하는 흐름을 그림으로 설명한다.
- 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §3·§5는 `adder(a, b, n)` 예로 cdecl 전 과정(인자 push → `call` → `push ebp; mov ebp, esp; sub esp, N` → `mov esp, ebp; pop ebp; ret` → caller가 `add esp, 12`)을 정리한다.
- 여기서는 그 위에 64비트 규약 두 개(x86-64 System V, ARM64 AAPCS64)와 실험을 얹는다.

> 참고: 원고 memory-management §3의 첫 그림("함수 호출 전 (main)")은 위에서부터 a, b, n 순서로 그렸다. cdecl은 인자를 뒤에서부터 push하므로 n이 가장 높은 주소, a가 반환 주소 바로 위다. 같은 절 두 번째 그림(위에서 n, b, a)이 맞다. 아래 `-m32` 실험의 `push $0x2`(n) → `push $0x14`(b) → `push $0xa`(a) 순서가 근거다. §5의 "지역 변수가 n → b → a로 쌓인다"에서 n·b·a는 지역 변수가 아니라 **인자**다.

### 2. 세 규약 한눈에

| | 32비트 x86 cdecl | x86-64 System V (리눅스·macOS) | ARM64 AAPCS64 |
|---|---|---|---|
| 정수 인자(64비트 이하 정수·포인터 기준) | 전부 스택(뒤에서부터 push) | `rdi, rsi, rdx, rcx, r8, r9` → 7번째부터 스택 | `x0`~`x7` → 9번째부터 스택 |
| 정수 반환값 | `eax`(64비트 `long long`은 `edx:eax`) | `rax`(둘째 `rdx`) | `x0`(128비트는 `x0:x1`) |
| 반환 주소 | `call`이 스택에 push | `call`이 스택에 push | `bl`이 **레지스터** `x30`(LR)에 넣음 |
| callee가 보존 | `ebx, esi, edi, ebp` (+`esp`) | `rbx, rbp, r12`~`r15` (+`rsp`) | `x19`~`x29` (+SP) |
| 스택 정렬 | 4바이트(워드) — 원판 i386 ABI 기준 | 함수 진입 시 `(rsp + 8)`이 16의 배수 | 공개 함수 경계와 SP로 메모리에 접근할 때 `SP mod 16 = 0` |
| 인자 정리 | caller(`add esp, N`) | caller | caller |

- 근거: System V AMD64 ABI Draft 0.99.6 3.2.2 The Stack Frame·3.2.3 Parameter Passing·그림 3.4 Register Usage, AAPCS64(2025Q4) General-purpose Registers·The Frame Pointer·Universal stack constraints("at any point at which memory is accessed via SP")·Stack constraints at a public interface(둘 다 "SP mod 16 = 0"). `__int128`처럼 16바이트 정수는 레지스터 두 개를 쓰므로(System V `__int128` 분류, AAPCS64 "x[NGRN] and x[NGRN+1]"), 스택으로 넘어가는 인자 번호가 앞당겨질 수 있다. 32비트 `long long` 반환 `edx:eax`와 ARM64 128비트 반환 `x0:x1`은 `gcc -m32 -O2`·`clang --target=aarch64` 디스어셈블로 확인했다. 32비트 열은 System V i386 ABI 4판(1997) 3장 Function Calling Sequence("Registers %ebp, %ebx, %edi, %esi, and %esp 'belong' to the calling function", "the stack be aligned on a word boundary")이다. 현재 리눅스 gcc의 32비트 코드는 더 큰 16바이트 정렬을 쓴다는 것이 일반 설명이지만 개정판 i386 psABI를 열어 확인하지 못했다 [?].
  - *caller-saved(호출자 저장)*: callee가 마음대로 써도 되는 레지스터. 호출 뒤에도 값이 필요하면 caller가 미리 저장한다.
  - *callee-saved(피호출자 저장)*: callee가 쓰려면 입구에서 저장하고 나갈 때 되돌려 놓아야 하는 레지스터.
    - 흔한 오해: "함수가 레지스터를 다 저장해 준다". 규약은 레지스터를 두 무리로 나눈다. 호출을 건너 살아남는 것은 callee-saved 무리뿐이다.

### 3. x86-64 System V 스택 프레임

```text
  높은 주소
  ┌──────────────────────────┐
  │ 7번째 이후 인자            │  16(%rbp), 24(%rbp) ...   ← caller 프레임 끝
  ├──────────────────────────┤
  │ 반환 주소                  │   8(%rbp)                 ← call이 push
  ├──────────────────────────┤
  │ 이전 %rbp                 │   0(%rbp)  ← %rbp          ← push %rbp (프레임 포인터를 쓸 때)
  ├──────────────────────────┤
  │ callee-saved 레지스터·지역 │  -8(%rbp) ...
  │ 변수·카나리                │
  ├──────────────────────────┤ ← %rsp
  │ red zone 128바이트         │  -128(%rsp)까지: 시그널·인터럽트 처리기가 건드리지 않음
  └──────────────────────────┘
  낮은 주소  (스택은 아래로 자란다)
```

- 이 그림은 System V ABI 그림 3.3(Stack Frame with Base Pointer)을 옮긴 것이다.
  - *프레임 포인터(frame pointer)*: 현재 프레임의 기준 주소를 담은 레지스터(`rbp`, ARM64는 `x29`). 이전 프레임 포인터가 저장된 자리를 가리키므로 프레임들이 **연결 리스트**처럼 이어진다.
  - *red zone*: `rsp` 아래 128바이트. 다른 함수를 부르지 않는 *잎(leaf) 함수*는 `rsp`를 움직이지 않고 여기를 지역 변수 자리로 쓸 수 있다(ABI 3.2.2). 리눅스 커널은 red zone을 지키지 않으므로 커널 코드는 `-mno-red-zone`으로 컴파일한다(ABI A.2.2).

### 4. 실험: 같은 함수, 최적화·규약별 기계어

```c
int adder(int a, int b, int n) { int c = a * n; int d = b * n; int e = c + d; return e; }
int sum7(long a, long b, long c, long d, long e, long f, long g) { return a+b+c+d+e+f+g; }
int caller(void) { return adder(10, 20, 2) + sum7(1,2,3,4,5,6,7); }
```

(실험, gcc 13.3.0 `-fno-inline -fcf-protection=none`, clang 18.1.3, objdump 2.42, 2026-10-07)

```text
  x86-64 -O0 adder                          x86-64 -O2 adder
   push %rbp             ← 프롤로그           lea (%rsi,%rdi,1),%eax   ← (a+b)
   mov  %rsp,%rbp                             imul %edx,%eax           ← ×n  (프레임 없음)
   mov  %edi,-0x14(%rbp) ← 인자를 red zone에   ret
   mov  %esi,-0x18(%rbp)
   mov  %edx,-0x1c(%rbp)
   ... imul / add ...
   pop  %rbp             ← 에필로그 (sub %rsp 없음 = 잎 함수가 red zone 사용)
   ret

  x86-64 -O2 caller → sum7 (인자 7개)        32비트 -m32 -O0 caller → adder
   mov $0x2,%edx ; mov $0x14,%esi            push $0x2      ← n 먼저
   mov $0xa,%edi ; mov $0x6,%r9d             push $0x14     ← b
   call adder                                push $0xa      ← a 마지막
   push $0x7                ← 7번째만 스택    call adder
   mov $0x5,%r8d ... mov $0x1,%edi           add  $0xc,%esp ← caller가 인자 12바이트 정리
   call sum7
   pop  %rdx                ← 7번째 인자 정리
  sum7 -O2:  add 0x8(%rsp),%r9d  ← 스택의 7번째 인자를 메모리 피연산자로 바로 더함

  ARM64 -O0 caller
   sub sp, sp, #0x20
   stp x29, x30, [sp, #0x10]   ← 프레임 포인터(x29)와 반환 주소(x30=LR)를 한 쌍으로 저장
   add x29, sp, #0x10
   mov w0,#0xa ; mov w1,#0x14 ; mov w2,#0x2 ; bl adder     ← 인자 x0~x2, bl이 LR에 반환 주소
   mov x0,#1 ... mov x6,#7 ; bl sum7                       ← 7개 모두 레지스터(x0~x6)
   ldp x29, x30, [sp, #0x10] ; add sp, sp, #0x20 ; ret
```

- `-O0`은 원고의 32비트 그림과 모양이 같다(`push %rbp; mov %rsp,%rbp`). 다만 인자는 스택이 아니라 레지스터로 들어와서, 함수가 스스로 red zone에 옮겨 적었다.
- `-O2`는 프레임을 아예 만들지 않았다. 인자·중간값이 전부 레지스터에 있다. `a*n + b*n`을 `(a+b)*n`으로 바꾸기까지 했다. C 표준상 부호 있는 `int`의 넘침은 정의되지 않은 동작(C11 §6.5 ¶5)이라, 컴파일러는 넘치지 않는 입력에서만 결과가 같으면 된다. 그 범위에서는 분배 법칙으로 같다. 넘치는 입력이라도 이 기계어는 하위 32비트로 계산하므로 2^32 모듈로 분배 법칙에 따라 같은 비트가 나온다(기계어 수준의 해석, [math/11](../../math/11-modular-arithmetic/2-summary.md)).
- ARM64는 반환 주소를 스택이 아닌 `x30`에 받는다. 다른 함수를 다시 부르면 `x30`이 덮이므로 정상 복귀에 필요한 반환 주소를 어딘가에 보존해야 한다. 이 `-O0` 출력은 `stp x29, x30`으로 스택에 frame record를 만들어 보존했다(AAPCS64 The Frame Pointer: "frame record of two 64-bit values" — 단 frame record 유지 수준은 플랫폼이 정하고, 꼬리 호출이면 받은 LR을 그대로 넘기기도 한다).

### 5. 실험: 프레임 포인터 사슬로 호출 경로를 걷는다

프로파일러는 "지금 어느 함수들을 거쳐 왔나"를 스택에서 읽는다. 가장 싼 방법이 `rbp` 사슬을 따라가는 것이다.

```text
   [rbp]   → 호출자의 rbp ─┐
   [rbp+8] → 반환 주소      │  이것을 반복하면 c → b → a → main
            ┌──────────────┘
```

(실험, `fpwalk.c` — `a → b → c → walk()`에서 `__builtin_frame_address(0)`부터 `[rbp]`·`[rbp+8]`을 따라감, gcc 13.3.0 `-O2 -rdynamic`)

```text
  -O2 -fomit-frame-pointer           -O2 -fno-omit-frame-pointer
   frame 0: ret=... in c              frame 0: ret=... in c
   frame 1: ret=... in __libc_start_main   frame 1: ret=... in b
   frame 2: ret=... in _start         frame 2: ret=... in a
                                      frame 3: ret=... in main
                                      frame 4: ret=... in ?
                                      frame 5: ret=... in __libc_start_main
                                      frame 6: ret=... in _start
```

- 프레임 포인터를 생략하면 `rbp`가 일반 레지스터로 쓰여 사슬이 끊긴다. `b`·`a`·`main`이 사라졌다.
- gcc `-O2`의 기본값은 생략이다(`gcc -Q --help=common -O2`: `-fomit-frame-pointer [enabled]`). 한편 이 Ubuntu 24.04의 패키지 빌드 플래그(`dpkg-buildflags --get CFLAGS`)에는 `-fno-omit-frame-pointer -mno-omit-leaf-frame-pointer`가 들어 있다. 배포판 패키지는 프로파일링을 위해 프레임 포인터를 남기는 쪽을 골랐다.
- 디버거(gdb)는 프레임 포인터 없이도 DWARF 되감기 정보(`.eh_frame`)로 스택을 복원한다 [?]. 사슬 걷기는 그보다 싸서 상시 프로파일러가 선호한다(해석).
- HotSpot에도 같은 선택지가 있다. `-XX:+PreserveFramePointer`(이 JDK 21 기본 `false`, `-XX:+PrintFlagsFinal`)다.

### 6. 실험: 스택 한도 ÷ 프레임 크기 = 재귀 깊이

```c
__attribute__((noinline)) long down(long n) {
    volatile char pad[PAD + 1];        // 프레임을 PAD 바이트만큼 키운다
    pad[0] = (char)n;
    depth = n;
    /* n==1, n==2일 때 지역 변수 주소 차이 = 프레임 한 개 크기 */
    return down(n + 1) + pad[0];       // 꼬리 호출이 아니게 해서 프레임이 쌓이게 한다
}
// SIGSEGV는 sigaltstack(대체 스택)의 처리기에서 잡아 도달 깊이를 출력한다
```

(실험, `recurse.c`, gcc 13.3.0, 호스트 `ulimit -s` = 8192 KB — 집필 때 실행과 점검 재실행(행마다 3회)을 합친 범위)

```text
  PAD     최적화  프레임 크기   SIGSEGV 깊이        8 MiB ÷ 프레임
  0       -O1     32 B         261,758~261,976     262,144
  0       -O0     48 B         174,594~174,672     174,762
  1000    -O1     1,056 B      7,933~7,938         7,943
  1000    -O0     1,072 B      7,814~7,819         7,825
  ulimit -s 16384:  PAD 0 → 524,041~524,110 / PAD 1000 → 15,877~15,881   (한도 2배 → 깊이 약 2배)
```

```text
  -O1 down의 32바이트 = 반환 주소 8 + push %rbx 8 + sub $0x10,%rsp 16
                        (16 안에 카나리 %fs:0x28 사본 8 + pad 배열)
```

- 깊이 ≈ 스택 한도 ÷ 프레임 크기다. 모자란 몇백 단계는 `main`·환경 변수·인자 몫이다. 같은 바이너리도 실행마다 수십~백 단계 흔들렸다(스택 시작 위치 무작위화 등 — 해석).
- 카나리가 들어간 것은 Ubuntu gcc가 `-fstack-protector-strong`을 기본으로 켜고, 이 함수가 배열을 지역 변수로 두기 때문이다([security/24](../../security/24-memory-safety-exploits/2-summary.md)).
- 스택 끝을 넘는 순간 커널이 `SIGSEGV`를 보낸다. 그 처리기조차 같은 스택에서 돌면 실행할 자리가 없다. 그래서 대체 스택(`sigaltstack`)에서 처리했다.

Java도 같은 원리다. JVM 스택 한도를 넘으면 `StackOverflowError`다(JVMS SE21 §2.5.2).

- HotSpot 스레드 스택 기본값은 Linux/x64 1024 KB(`globals_linux_x86.hpp`의 `ThreadStackSize 1024`, `java` 도구 문서), Linux/AArch64 약 2 MB다(`java` 도구 문서는 2048 KB, 소스 `globals_linux_aarch64.hpp`는 2 MB에서 두 페이지 뺀 `ThreadStackSize 2040`). **같은 jar도 아키텍처에 따라 깊이가 다르다.**
- 크기·JIT별 깊이 측정은 [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) 실험에 있다. 이번에 따로 돌린 결과(Temurin 21.0.12, `-Xss1m`, `Deep.java`): 인터프리터만(`-Xint`) 인자 1개 함수 9,069·인자 8개 함수 3,368로 한 측정 묶음 안에서는 실행마다 같았다. 점검 재실행에서는 9,081·3,372로 역시 실행마다 같았지만 앞 묶음과 열몇 단계 달랐다. JIT를 켜면 인자 1개 함수가 9,069~59,026으로 흔들렸다(두 묶음 합산). 예외의 스택 트레이스는 깊이와 무관하게 1,024줄에서 잘렸다(`MaxJavaStackTraceDepth = 1024`).

### 7. 반환 주소가 지역 버퍼 **위**에 있다는 것

```text
  높은 주소  [ 반환 주소 ][ 이전 rbp ][ 카나리 ][ char buf[16] ]  낮은 주소
                 ▲                                   │
                 └──── buf[0]부터 높은 주소로 쓴다 ───┘  넘치면 카나리 → rbp → 반환 주소 순으로 덮인다
```

- 스택은 아래로 자라지만 배열은 위로 채운다. 그래서 지역 배열을 넘친 길이가 충분하면 자기 프레임의 반환 주소까지 덮인다. 실제 배치(카나리·다른 지역 변수의 자리)는 컴파일러·옵션에 따라 다르고, C 표준은 범위 밖 쓰기의 결과를 정하지 않는다(정의되지 않은 동작).
- 카나리·ASLR·NX와 실험(`stack smashing detected`, exit 134)은 [security/24](../../security/24-memory-safety-exploits/2-summary.md)에 있다.

## 쓰이는 자료구조·알고리즘

- **스택(LIFO)** — 마지막에 부른 함수가 먼저 끝난다. 프레임을 push·pop하는 것이 그대로 스택이다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)
- **연결 리스트** — 저장된 프레임 포인터들이 이전 프레임을 가리키는 단일 연결 리스트다. 프로파일러·디버거가 이것을 따라간다. [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **재귀 ↔ 명시적 스택** — 재귀를 반복문 + 힙에 둔 스택으로 바꾸면 깊이 한계가 "스레드 스택"에서 "힙 메모리"로 옮겨 간다. [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 크래시가 스택 오버플로인지 가른다

| 보이는 것 | 뜻 |
|---|---|
| Java `java.lang.StackOverflowError` + 같은 몇 줄이 반복되는 트레이스(1,024줄에서 잘림) | 재귀 사이클이 스레드 스택을 다 썼다 |
| C/네이티브 exit 139, `Segmentation fault`, 코어 덤프의 크래시 주소가 스택 영역 끝 | 스택 한도 초과([os/09](../../os/09-address-space/2-summary.md) 장애 3) |
| exit 134 `*** stack smashing detected ***` | 지역 버퍼 넘침을 카나리가 잡음 — 오버플로가 아니라 **오버런** |

- 반복되는 프레임 묶음이 재귀 경로다. 그 경로의 입력(중첩 깊이, 그래프 깊이, 연결 리스트 길이)을 찾는다.

### 2. 고치는 순서

1. 깊이가 입력 크기에 비례하는 재귀를 반복문·명시적 스택으로 바꾼다.
2. 입력에 깊이 상한을 둔다(예: JSON 중첩 상한 — [algorithm/03](../../algorithm/03-recursion/2-summary.md)의 Jackson 사례).
3. 그래도 필요하면 스택을 키운다. 전체 스레드에 걸리는 `-Xss`보다, 그 작업만 큰 스택 스레드에서 돌리는 쪽이 메모리를 아낀다.

```java
// 깊은 재귀 작업만 64 MiB 스택 스레드에서 실행 (예시 크기)
Thread t = new Thread(null, () -> parseDeep(input), "deep-parser", 64L * 1024 * 1024);
t.start();
t.join();
```

- 이 생성자의 `stackSize`는 플랫폼에 따라 무시될 수 있다(Javadoc: "may have no effect whatsoever"). 적용 여부는 측정으로 확인한다.
- C 스레드는 `pthread_attr_setstacksize`다. glibc 새 스레드의 기본 스택은 시작 시 `RLIMIT_STACK`이 무제한이 아니면 그 값이다(`pthread_create(3)`).

### 3. 기계어로 프레임을 읽는다

```bash
gcc -O2 -c f.c && objdump -d --no-show-raw-insn f.o     # 프롤로그: push %rbp / sub $N,%rsp
gcc -O2 -fno-omit-frame-pointer ...                      # 프로파일링 빌드
gcc -m32 -O0 -fno-pic -c f.c && objdump -d f.o           # 원고와 같은 32비트 cdecl 모양
```

- 읽는 순서: `sub $N,%rsp`(프레임 크기) → `push`되는 callee-saved 레지스터 → 인자가 오는 레지스터(`%rdi`…) → `call` 앞의 `push`(7번째 이후 인자) → `%fs:0x28`(카나리).

## 장애 시나리오와 대처

### 1. 깊게 중첩된 입력 하나로 요청 스레드가 죽는다 (Java)

- **현상**: 특정 요청만 500으로 실패한다. 서버는 살아 있다.
- **보이는 형태**: 로그에 `java.lang.StackOverflowError`와 같은 메서드(파서·재귀 탐색) 몇 개가 반복되는 트레이스 1,024줄.
- **원인**: 재귀 깊이가 입력 중첩 깊이에 비례한다. 스레드 스택(Linux/x64 기본 1 MiB)을 다 썼다. JIT 상태에 따라 한계 깊이가 실행마다 다르다(위 실험 9,069~59,026).
- **대처**: 입력 깊이 상한을 두고, 재귀를 명시적 스택으로 바꾼다. `StackOverflowError`는 `Error`라 `catch (Exception e)`로 잡히지 않는다.

### 2. 네이티브 프로세스가 `SIGSEGV`(exit 139)로 죽는다 — 스택 한도

- **현상**: C/C++·네이티브 확장이 큰 입력에서 갑자기 죽는다. 작은 입력은 멀쩡하다.
- **보이는 형태**: `Segmentation fault (core dumped)`, exit 139. 코어 덤프의 스택 트레이스가 같은 함수로 수십만 줄.
- **원인**: 깊이 × 프레임 크기 > 스택 한도. 위 실험에서 프레임 32 B면 8 MiB에서 약 26만 단계, 큰 지역 배열(1 KiB)이 있으면 약 7,900단계였다. 지역 배열 하나가 깊이 한계를 33배 줄였다.
- **대처**: 큰 지역 배열을 힙으로 옮긴다. 재귀를 반복으로 바꾼다. 작업 스레드라면 스택 크기를 명시한다. `ulimit -s`는 메인 스레드와 glibc 기본 스레드 스택에 영향을 준다.

### 3. 지역 버퍼 넘침으로 반환 주소가 덮인다

- **현상**: 긴 입력에서만 죽거나, 엉뚱한 곳으로 점프한다.
- **보이는 형태**: `*** stack smashing detected ***: terminated`, exit 134(카나리 on). 카나리 off면 [security/24](../../security/24-memory-safety-exploits/2-summary.md) 실험(16 B 버퍼에 64 B)에서는 `SIGSEGV` 139였다. 넘친 길이·배치에 따라 죽지 않고 엉뚱하게 계속 돌 수도 있다.
- **원인**: 배열은 위로 채워지고 반환 주소는 그 위에 있다. 경계 없는 복사가 프레임 위쪽을 덮었다.
- **대처**: 길이를 받는 API로 바꾼다. 상세 실험·완화책은 [security/24](../../security/24-memory-safety-exploits/2-summary.md) 장애 2.

### 4. 프로파일 결과의 호출 경로가 끊겨 있다

- **현상**: flame graph에 `[unknown]`이 많거나, 함수가 엉뚱한 부모 아래 붙는다.
- **보이는 형태**: 프레임 포인터 기반 샘플링에서 스택이 1~2단계로 짧다. 위 실험의 `-fomit-frame-pointer` 판처럼 중간 함수가 통째로 빠진다.
- **원인**: `-O2`가 기본으로 프레임 포인터를 생략해 `rbp` 사슬이 없다. JIT 코드는 HotSpot `PreserveFramePointer`가 꺼져 있으면(기본) 같은 문제가 난다.
- **대처**: 프로파일링 대상은 `-fno-omit-frame-pointer`로 빌드하고, Java는 `-XX:+PreserveFramePointer`를 켠다(성능 비용은 측정해서 판단). 또는 DWARF 되감기를 쓰는 도구를 쓴다.

## 핵심 문장

- 호출 규약은 인자·반환값·반환 주소·보존 레지스터·스택 정렬을 caller와 callee가 어떻게 나누는지 정한 ABI 약속이다.
- 32비트 cdecl은 인자를 전부 스택에, x86-64 System V는 앞 6개를 레지스터에, ARM64는 앞 8개를 레지스터에 둔다. ARM64는 반환 주소도 레지스터(x30)에 받는다.
- 프레임 포인터는 프레임들을 연결 리스트로 잇는다. `-O2`가 이것을 빼면 싼 스택 걷기가 끊긴다.
- 재귀 깊이 한계 ≈ 스택 한도 ÷ 프레임 크기다. 실험에서 8 MiB ÷ 32 B ≈ 26만 단계, 큰 지역 배열 하나로 약 7,900단계였다.
- 배열은 위로 채우고 반환 주소는 그 위에 있어서, 지역 버퍼 넘침이 길면 반환 주소를 덮는다.

## 관련 주제·근거

- 선행
  - [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) — 레지스터 이름과 기계어 읽기
  - [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) — 커리큘럼 자료구조 05 stack
  - 원고 [systems/call-stack](../../systems/call-stack/README.md)(ESP 예약·반납), [foundations/memory-management](../../foundations/memory-management/README.md) §3 함수 호출과 스택 프레임 전체 흐름·§5 어셈블리 관점
- 후속·연결
  - [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md) — `-Xss`·프레임 크기별 깊이, JIT 흔들림
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — 스택 버퍼 오버플로·카나리·ASLR·NX
  - [os/09-address-space](../../os/09-address-space/2-summary.md) — 스택 영역·`RLIMIT_STACK`·가드 페이지
  - [os/06-signals](../../os/06-signals/2-summary.md) — 시그널 전달과 처리기(`SIGSEGV`)
  - [os/02-system-calls](../../os/02-system-calls/2-summary.md) — 시스템 콜의 레지스터 약속(사용자 함수 규약과 다르다)
  - [math/11-modular-arithmetic](../../math/11-modular-arithmetic/2-summary.md) — `-O2`의 `(a+b)*n` 재배치가 정수에서 안전한 이유
  - 컴퓨터 구조 18·19(같은 기계어의 실행 방식) — [18](../18-pipelining-and-branch-prediction/2-summary.md) · [19](../19-out-of-order-and-speculation/2-summary.md)
- 교재
  - CS:APP 3판 3.7 Procedures(3.7.1 The Run-Time Stack ~ 3.7.6 Recursive Procedures), 3.10.3 Out-of-Bounds Memory References and Buffer Overflow(절 번호: 3판 목차 <http://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
- 명세·문서
  - System V AMD64 ABI Draft 0.99.6 — 3.2.2 The Stack Frame(그림 3.3, 16바이트 정렬, red zone 128바이트), 3.2.3 Parameter Passing, 그림 3.4 Register Usage <https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf>
  - Arm AAPCS64(2025Q4) — General-purpose Registers(r0–r7 인자, r29 FP, r30 LR), The Frame Pointer(frame record), Subroutine calls(BL → LR), Universal stack constraints·Stack constraints at a public interface(SP mod 16 = 0) <https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst>
  - JVMS SE21 §2.5.2 Java Virtual Machine Stacks(`StackOverflowError`) <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html>
  - Oracle JDK 21 `java` 도구 문서 `-Xss`(Linux/x64 1024 KB, Linux/Aarch64 2048 KB) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html> · Java 21 API `Thread(ThreadGroup, Runnable, String, long)` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html>
  - OpenJDK jdk21u `src/hotspot/os_cpu/linux_x86/globals_linux_x86.hpp` — AMD64 `ThreadStackSize 1024` · `src/hotspot/os_cpu/linux_aarch64/globals_linux_aarch64.hpp` — `ThreadStackSize 2040`
  - System V ABI Intel386 Architecture Processor Supplement 4판 — 3장 Function Calling Sequence(보존 레지스터, 워드 정렬, 인자 역순) <https://refspecs.linuxbase.org/elf/abi386-4.pdf>
  - `pthread_create(3)` — 새 스레드 기본 스택 = `RLIMIT_STACK`
  - ISO C 위원회 초안 N1570(C11) §6.5 ¶5 — 표현 범위를 넘는 산술 결과는 정의되지 않은 동작 <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>
- 실험 목록(모두 2026-10-07, i7-13700HX, Ubuntu 24.04.4, 커널 7.0.0-34-generic)
  - gcc 13.3.0 `-O0`/`-O2`/`-O2 -fno-omit-frame-pointer`/`-m32 -O0`, clang 18.1.3 ARM64 `-O0`로 `adder`·`sum7`·`caller` 디스어셈블 — red zone, 7번째 인자 `push`, cdecl 역순 push, `stp x29, x30`
  - `fpwalk.c`: `rbp` 사슬 걷기, 프레임 포인터 생략 시 `b`·`a`·`main` 누락 · `dpkg-buildflags`, `gcc -Q --help=common`
  - `recurse.c`: 프레임 32/48/1,056/1,072 B별 `SIGSEGV` 깊이(8 MiB·16 MiB 스택), `down` 디스어셈블
  - Temurin 21.0.12 docker `--cpus=2`: `Deep.java` `-Xss256k/1m/4m`·`-Xint` 깊이, 트레이스 1,024줄, `ThreadStackSize=1024`·`MaxJavaStackTraceDepth=1024`·`PreserveFramePointer=false`
