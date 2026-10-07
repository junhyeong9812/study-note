# architecture/22-arch-symptom-index — 증상 사전: SIGSEGV·SIGBUS·SIGILL·exec format error·음수 금액·합계 불일치·모지바케·멀티스레드가 더 느림·SSD 지연 톱니 → 표현·하드웨어 원인·확인 명령·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **표현·하드웨어에서 증상으로** 간다.\
"Java `int`는 32비트 2의 보수라 2,147,483,647 다음이 −2,147,483,648이다 → 합계가 음수가 된다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. "`Segmentation fault (core dumped)`", "`exec /app/server: exec format error`", "법인 계좌 누계가 음수", "`cafÃ©`", "스레드를 늘렸더니 더 느리다", "SSD인데 p99가 주기적으로 튄다".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                      이 노트 (역방향)
  표현·하드웨어 --> 깨지는 조건 --> 보이는 증상              증상 --> 보이는 형태 --> 원인 후보 --> 확인 명령 --> leaf
  "int는 2^31-1 다음이 -2^31"                              "로그에 -1994967296. 먼저 DTO·누적 변수의 타입 폭"
```

쉬운 예: 자동차 계기판의 경고등이다.\
엔진 경고등 하나에 원인이 여럿이다(센서 고장, 점화 불량, 연료 문제).\
정비사는 경고등 → 진단기 코드 → 부품 순서로 좁힌다. 경고등만 보고 엔진을 내리지 않는다.

똑같은 구조다.\
"프로세스가 exit 139로 죽었다"는 같은 증상에 원인이 여럿이다.
- 깊은 재귀가 스택 한도를 넘었다([10-2](../10-calling-convention-and-stack-frame/2-summary.md)).
- 무부호로 바뀐 음수 길이로 거대한 복사를 했다([01-1](../01-number-systems-twos-complement/2-summary.md) · [02-3](../02-integer-overflow-and-truncation/2-summary.md)).
- 오버클록·결함 코어가 틀린 주소를 계산했다([07-1](../07-logic-gates-to-adder/2-summary.md) · [07-2](../07-logic-gates-to-adder/2-summary.md)).

처방이 셋 다 다르다. 그래서 원인을 고르기 전에 **보이는 형태**(신호 번호·메시지·지표)와 **조건**(어느 CPU, 어느 입력 크기, 스레드 몇 개)을 먼저 모은다.

실무 예:
- 표현·하드웨어 증상의 대부분은 **가정한 폭·순서·위치가 실제와 다를 때** 보인다. 정수 폭(32비트), 바이트 순서(빅/리틀), 문자 부호화(UTF-8/Latin-1), 아키텍처(x86-64/ARM64), 캐시 라인(64B), 코어 종류(P/E), 저장 매체(HDD/SSD)가 그 가정이다.
- 그래서 첫 질문은 "그때 어떤 기계에서, 어떤 값으로 돌았나"다.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `NN-k`*: 이 영역 NN번 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `06-3` = [06-byte-order-and-alignment](../06-byte-order-and-alignment/2-summary.md)의 시나리오 3(ARM 비정렬 접근 `SIGBUS`). 커리큘럼 17번(nand-flash-ftl)은 기존 노트 [systems/nand-flash](../../systems/nand-flash/2-summary.md)가 맡아 `nand-flash §8`처럼 절 번호로 적는다.
  - *첫 확인*: 고치기 전에 원인 후보를 가르는 가장 싼 확인 한 가지.

## 동작·원리

### 0. 증상은 어느 층의 가정이 깨진 것인가

```text
   증상                                  깨진 가정                                층(노트)                 이 노트의 절
   ────                                  ────────                                ────────                 ─────────
   SIGSEGV·SIGBUS·SIGILL·exec format     "주소·정렬·명령이 이 CPU에서 유효하다"       ISA·스택·정렬(06,09,10,21)   1절
   음수 금액·4294967295                    "값이 타입 폭 안에 든다"                    정수 표현(01,02,07)        2절
   합계 불일치                            "실수 연산이 정확하고 순서와 무관하다"         부동소수(03,21), 동시성(14)  3절
   모지바케·�·길이 초과                    "바이트 = 글자, 쓰는 쪽과 읽는 쪽 부호화가 같다"  문자(04,05)               4절
   필드가 256배·포트가 뒤집힘              "바이트 순서·배치가 양쪽에서 같다"             바이트 순서·패딩(06,01)     5절
   멀티스레드가 더 느림                    "스레드를 늘리면 일이 나뉜다"                캐시 라인·코어(12,14,20)    6절
   같은 O(n)인데 수~수십 배 느림            "메모리 접근·분기 비용은 일정하다"            계층·파이프라인(11~13,18,19,21)  7절
   SSD 지연 톱니·HDD 지연 폭증              "저장 장치 지연은 일정하다"                  I/O·저장(15,16,17)         8절
   가끔 멈추거나 가끔 틀림                  "다른 코어·회로가 같은 값을 같은 때 본다"       일관성·회로(07,08,14,19)    9절
```

- 커리큘럼 22번 행이 든 일곱 증상이 1·2·3·4·6·8절의 머리다. 5·7·9절은 leaf 시나리오의 나머지 증상이다.
- 다른 영역 색인과 겹치는 곳: 종료 코드·errno는 [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md)가 정본이다. 합계 불일치의 수학 쪽(결합법칙·파국적 상쇄)은 [math/16-math-symptom-index](../../math/16-math-symptom-index/2-summary.md) 4절이 정본이다. 이 노트는 그 증상의 **표현·하드웨어 원인**을 맡는다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 원문     신호 이름·종료 코드(128+N), 예외 전체, 로그의 수치 원문(16진 함께)
  ② 기계     uname -m, CPU 모델(lscpu), 코어 종류(P/E), 커널, 컨테이너 이미지의 플랫폼
  ③ 값       그때의 입력 값·길이·바이트(xxd), 경계값(2^31, 2^53, 0x80) 근처인가
  ④ 비율     크기·스레드 수·입력 순서를 바꿨을 때 시간이 몇 배인가 (같은 기계, 코어 고정)
```

- ②가 빠지면 1·6·7·9절의 원인을 고를 수 없다. 같은 코드가 x86에서는 맞고 ARM에서 틀리는 증상([14-4](../14-cache-coherence-and-memory-ordering/2-summary.md)), 코어 종류에 따라 갈리는 지연([20-4](../20-multicore-and-numa/2-summary.md))이 그 예다.
- ③의 16진은 원인을 바로 보인다. `4294967295`는 `0xFFFFFFFF`(−1의 32비트 표현), `65536`은 `0x00010000`(리틀 엔디안 256 `00 01 00 00`을 빅 엔디안으로 읽은 값)이다([01-5](../01-number-systems-twos-complement/2-summary.md) · [06-2](../06-byte-order-and-alignment/2-summary.md)).

### 1. 프로세스가 신호로 죽는다 — `SIGSEGV`·`SIGBUS`·`SIGILL`·`exec format error`

먼저 **종료 코드**로 신호를 가른다. bash는 신호로 죽은 프로세스를 128 + 신호 번호로 보인다(bash 매뉴얼 Exit Status, [os/37](../../os/37-os-symptom-index/2-summary.md) 1절). 이 호스트의 `docker run`도 컨테이너 안 SIGSEGV를 139로 보였다. POSIX는 "128보다 큰 값"만 요구하고 계산은 구현이 정한다. 또 프로그램이 직접 `exit(139)`를 해도 같은 값이라 종료 코드만으로는 신호 종료와 구별되지 않는다.

```text
  프로세스가 시작하자마자 / 실행 중 죽음
     │
     ├─ exec ... exec format error, exit 126(셸)·CrashLoopBackOff ─────▶ 실행 파일 아키텍처 ≠ CPU(대표 원인)       09-1
     ├─ Illegal instruction, exit 132 (SIGILL) ────────────────────▶ 이 CPU에 없는 명령(AVX-512 등)·의도적 트랩  09-3 · 21-3
     ├─ Bus error, exit 135 (SIGBUS) ─────────────────────────────▶ 비정렬 접근(일부 ARM) / 잘린 mmap 파일       06-3 · os/14
     ├─ Segmentation fault, exit 139 (SIGSEGV), 큰 입력에서만 ────────▶ 스택 한도 초과(깊이 × 프레임)              10-2
     ├─ stack smashing detected, exit 134 / 139 ───────────────────▶ 지역 버퍼 넘침이 반환 주소를 덮음           10-3
     ├─ SIGSEGV, 길이·크기 값이 음수·거대 ───────────────────────────▶ 부호/무부호 혼용·size_t 언더플로           01-1 · 02-3 · 07-4
     ├─ SIGSEGV·체크섬 불일치, 오버클록·특정 코어에서만 ────────────────▶ 타이밍 위반·결함 코어(SDC)                07-1 · 07-2
     └─ Java: StackOverflowError (그 스레드만 끝날 수 있음) ─────────▶ 재귀 깊이 ∝ 입력 중첩                     10-1
```

| 보이는 것 (메시지·종료 코드·로그) | 원인 후보 (표현·하드웨어) | 첫 확인 (명령) | leaf |
|---|---|---|---|
| `exec /app/server: exec format error`, 쿠버네티스 `CrashLoopBackOff`, 셸 `cannot execute binary file: Exec format error`(exit 126) | ELF 헤더의 `e_machine`이 노드 CPU와 다름. QEMU binfmt 규칙이 없어 커널이 `ENOEXEC`(execve(2): 인식 못 하는 형식·다른 아키텍처·그 밖의 형식 오류 — 아키텍처 불일치는 그중 하나) | `docker image inspect --format '{{.Os}}/{{.Architecture}}' <이미지>`, `file <엔트리포인트>`, 노드 `uname -m` | [09-1](../09-isa-and-machine-code/2-summary.md) |
| 오류 없이 수배 느림, 컨테이너 안 `uname -m`이 호스트와 다름 | QEMU 사용자 모드·Rosetta 번역 실행 | `uname -m`(안·밖), `ls /proc/sys/fs/binfmt_misc/` | [09-2](../09-isa-and-machine-code/2-summary.md) |
| `Illegal instruction (core dumped)`, exit 132, `dmesg`의 `trap invalid opcode` | `-march=native`·`x86-64-v4`로 빌드한 바이너리를 확장 없는 CPU에서 실행 | `grep -o -w avx512f /proc/cpuinfo`, `ld.so --help`의 지원 수준 | [09-3](../09-isa-and-machine-code/2-summary.md) · [21-3](../21-simd-and-gpu/2-summary.md) |
| `java.lang.UnsatisfiedLinkError: ... (Possible cause: can't load AMD 64 .so on a AARCH64 platform)` 꼴(09번 실험의 반대 방향) | jar 안 JNI `.so`가 한 아키텍처용뿐 | jar 안 `.so` 목록, `file *.so` | [09-4](../09-isa-and-machine-code/2-summary.md) |
| `Bus error (core dumped)`, exit 135, ARM 장비에서만 | `packed` 구조체·바이트 버퍼를 `uint32_t*`로 캐스트한 비정렬 load | 코어의 fault 주소가 4·8의 배수인가, `-Wcast-align=strict` 경고 | [06-3](../06-byte-order-and-alignment/2-summary.md) |
| `Bus error`, x86에서도, 로그 회전·파일 교체 직후 | `mmap`한 파일이 뒤에서 잘림 | 파일 교체 시각 대조, `/proc/<pid>/maps` | [os/14](../../os/14-mmap-and-page-cache/2-summary.md) · [os/37](../../os/37-os-symptom-index/2-summary.md) |
| `Segmentation fault (core dumped)`, exit 139, 코어 덤프 스택이 같은 함수로 수십만 줄 | 깊이 × 프레임 크기 > 스택 한도(8 MiB에서 프레임 32 B 약 26만 단계, 지역 배열 1 KiB면 약 7,900단계 — 10번 실험) | `ulimit -s`, 코어 `bt`의 깊이, `objdump -d`의 `sub $N,%rsp` | [10-2](../10-calling-convention-and-stack-frame/2-summary.md) |
| `*** stack smashing detected ***: terminated`, exit 134(카나리 off면 security/24 실험에서 139, 죽지 않고 계속 돌 수도 있음) | 경계 없는 복사가 카나리·반환 주소를 덮음 | 입력 길이, 해당 함수의 지역 배열 크기 | [10-3](../10-calling-convention-and-stack-frame/2-summary.md) · [security/24](../../security/24-memory-safety-exploits/2-summary.md) |
| `SIGSEGV`, 직전 로그의 길이가 `18446744073709551612`·음수 | `total - hdr`의 무부호 언더플로, `int` → `size_t` 변환, `-1 > 0u` | 로그 값을 16진으로(`0xff…fc`), 빼기 전 `total < hdr` 검사 유무, `-Wsign-compare`. 무부호 감김은 UB가 아니라 `-fsanitize=undefined`에 안 잡힌다 — Clang은 `-fsanitize=unsigned-integer-overflow,implicit-integer-sign-change`를 따로 켠다(Clang UBSan 문서) | [02-3](../02-integer-overflow-and-truncation/2-summary.md) · [01-1](../01-number-systems-twos-complement/2-summary.md) · [07-4](../07-logic-gates-to-adder/2-summary.md) |
| 엉뚱한 곳의 `SIGSEGV`·체크섬 불일치, 다시 돌리면 맞기도 함, 클록·전압을 바꾼 장비 | 캐리 경로가 클록 주기를 넘는 타이밍 위반 | 제조사 기본 클록·전압으로 되돌려 재현 | [07-1](../07-logic-gates-to-adder/2-summary.md) |
| 커널·이벤트 로그는 깨끗한데 특정 값이 가끔 틀림(Meta 사례: `Int(1.1^53)`이 0) | 결함 코어의 조용한 데이터 손상(SDC) | `taskset -c N`으로 코어 하나씩 고정해 같은 계산 | [07-2](../07-logic-gates-to-adder/2-summary.md) |
| Java `StackOverflowError`, 트레이스 1,024줄, 요청 스레드만 끝나고 서버는 계속(다른 비데몬 스레드가 있을 때 — 마지막 비데몬 스레드면 JVM도 끝남, JLS §12.8) | 재귀 깊이가 입력 중첩에 비례, 스레드 스택(Linux/x64 기본 1 MiB) 소진 | 실패 입력의 중첩 깊이 | [10-1](../10-calling-convention-and-stack-frame/2-summary.md) |

- 처방의 방향: 아키텍처 불일치 → 빌드 시 `--platform`·다중 플랫폼 이미지·공통 최소 명령 수준. 정렬 → `memcpy`로 읽기. 스택 → 깊이 상한·명시적 스택·큰 배열은 힙. 정수 → 빼기·곱하기 **전에** 검사.

#### 실험: 세 신호를 실제 하드웨어 예외로 만들고 종료 코드를 읽는다 (`sig.c`)

NULL 쓰기(페이지 폴트), `__builtin_trap()`(x86-64 gcc에서 `ud2` 명령), 잘린 `mmap` 파일 읽기로 세 신호를 냈다.

```c
if (!strcmp(m, "segv")) { volatile int *p = 0; *p = 1; }
if (!strcmp(m, "ill"))  { __builtin_trap(); }                 /* objdump: 0f 0b  ud2 */
if (!strcmp(m, "bus"))  {
    int fd = open("bus.tmp", O_RDWR | O_CREAT | O_TRUNC, 0600);
    ftruncate(fd, 4096);
    volatile char *p = mmap(0, 4096, PROT_READ, MAP_SHARED, fd, 0);
    ftruncate(fd, 0);                                         /* 매핑 뒤 파일을 0바이트로 */
    printf("read %d\n", p[0]);
}
```

(실험, i7-13700HX, Linux 7.0.0-34-generic, gcc 13.3.0 `-O0`, bash `LC_ALL=C`, 2026-10-07)

```text
bash: line 1: PID Segmentation fault      (core dumped) bash -c './sig segv'
exit=139
bash: line 1: PID Illegal instruction     (core dumped) bash -c './sig ill'
exit=132
bash: line 1: PID Bus error               (core dumped) bash -c './sig bus'
exit=135
```

- 관찰: 종료 코드는 128 + 신호 번호(x86-64 Linux의 SIGSEGV 11, SIGILL 4, SIGBUS 7)였다. 여기서 132는 없는 확장이 아니라 의도적 트랩(`ud2`)으로 낸 SIGILL이다. 메시지는 프로세스가 아니라 **부모 셸**이 찍는다. 로캘이 한국어면 "세그멘테이션 오류"처럼 번역돼 찍혔다(같은 실험, 기본 로캘). 로그 검색은 종료 코드로 하는 편이 안전하다.
- x86-64에서는 비정렬 load가 기본으로 허용되므로 SIGBUS를 내려고 `mmap` 경로를 썼다. ARM의 비정렬 SIGBUS와 x86의 EFLAGS.AC 재현은 [06](../06-byte-order-and-alignment/2-summary.md) 실험에 있다.
- `exec format error`의 재현(ARM64 정적 바이너리를 x86-64에서 실행)은 [09](../09-isa-and-machine-code/2-summary.md) 4절 실험에 있다. 이 호스트의 `file`은 자기 바이너리를 `ELF 64-bit LSB pie executable, x86-64`로, 로컬 이미지 `eclipse-temurin:21-jdk`의 플랫폼을 `linux/amd64`로 보였다(같은 날).

### 2. 금액·카운터가 음수가 되거나 거대한 값이 된다

먼저 **값을 16진으로** 본다. 32비트 경계(`0x7FFFFFFF`·`0x80000000`·`0xFFFFFFFF`) 근처면 정수 폭 문제다.

```text
  숫자가 갑자기 음수 / 거대
     │
     ├─ 21억(2,147,483,647)을 넘는 순간 음수, 예외 없음 ─────────────▶ int 덧셈 wrap                     02-1 · 07-3
     ├─ 4294967295 / 18446744073709551612 같은 거대 값 ────────────▶ −1·음수를 무부호로 해석·출력          01-5 · 02-3
     ├─ 해시 % n 이 음수, 수십억 건 중 드물게 ───────────────────────▶ Math.abs(Integer.MIN_VALUE) < 0      01-4
     ├─ 길이 128 이상에서만 NegativeArraySizeException: -56 ─────────▶ byte 부호 확장                       01-2
     ├─ 오래 켜 둔 장비만 고장(248일 등) ────────────────────────────▶ 경과 시간 카운터 넘침                  02-4 · 23 사건 5
     ├─ 넘침 검사 코드가 있는데 통과 ─────────────────────────────────▶ C 부호 있는 넘침 UB → 검사가 접힘       02-5
     └─ 실수 → 정수 변환 뒤 2147483647·−32768·−25536 ─────────────────▶ 좁히기 변환(포화·감김·예외)            02-2 · 23 사건 2
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 법인 계좌 누계가 음수, 로그 `-1994967296`, DB는 `BIGINT`로 맞음 | 2,147,483,647원 초과를 `int`로 더함(Java는 넘침을 알리지 않음, JLS §4.2.2) | DTO·누적 변수·JSON 매핑의 타입 폭, 값이 2³¹ 근처인가 | [02-1](../02-integer-overflow-and-truncation/2-summary.md) |
| 합계 −2147483648 근처, 예외 없음 | 가산기는 V 플래그를 계산하지만 Java `int +`는 하위 32비트만 남김(C의 부호 있는 `+` 넘침은 UB) | 같은 계산을 `Math.addExact`로 → `ArithmeticException` | [07-3](../07-logic-gates-to-adder/2-summary.md) |
| 모니터링 "남은 재시도 4294967295회", 종료 코드 255 | 0 아래로 감긴 무부호 카운터, −1을 무부호로 출력 | 로그에 `0xFFFFFFFF`를 함께 찍기 | [01-5](../01-number-systems-twos-complement/2-summary.md) |
| `ArrayIndexOutOfBoundsException: -3`, 드묾 | `hashCode()`가 `Integer.MIN_VALUE`일 때 `Math.abs`가 음수 | 그 키의 `hashCode()` 값 | [01-4](../01-number-systems-twos-complement/2-summary.md) · [math/11](../../math/11-modular-arithmetic/2-summary.md) |
| `NegativeArraySizeException: -56`, 길이 127까지는 통과 | `int len = buf[i]`가 `byte` 0xC8을 부호 확장 | 경계값 127·128·255 테스트 | [01-2](../01-number-systems-twos-complement/2-summary.md) |
| `std::bad_alloc`·`Cannot allocate memory`, 길이 로그 `18446744073709551612` | 무부호 `total - hdr` 언더플로, `cnt * 4` 32비트 감김 | 빼기 전 `total < hdr` 검사 유무 | [02-3](../02-integer-overflow-and-truncation/2-summary.md) |
| 248일 연속 가동 뒤 장비 failsafe(FAA AD 2015-09-07) | 경과 시간 카운터 넘침(2³¹ / 100 / 86400 = 248.55일 — 02번의 추정 계산) | 가동 일수 × 틱 주파수가 2³¹·2³²에 닿나 | [02-4](../02-integer-overflow-and-truncation/2-summary.md) |
| `if (x + 1 < x)` 검사가 있는데 넘침이 통과, `-O2`에서 검사가 `xor %eax,%eax; ret` | C 부호 있는 넘침은 미정의 동작 | `objdump -d`로 검사 코드가 남았나, `-fsanitize=undefined` | [02-5](../02-integer-overflow-and-truncation/2-summary.md) |
| 부동소수에서 온 정수가 2147483647·−2147483648에 붙음, 또는 −25536 같은 엉뚱한 값 | 범위 밖 좁히기(Java 포화·`(short)` 감김, C UB, Ariane SRI는 Operand Error — Ada 규격의 변환 범위 검사 실패는 `Constraint_Error`, Ada RM 4.6) | 변환 전 값의 범위 | [02-2](../02-integer-overflow-and-truncation/2-summary.md) |

- 처방의 방향: 금액은 `long` 최소 단위·`BigDecimal`, 누적은 `Math.addExact`. 경과 시간은 64비트로 세고 차(`now - start`)로 비교한다. 경계값(2³¹ − 1, 2³¹, 0x80)을 테스트에 넣는다.

### 3. 합계가 맞지 않는다 — 표현·하드웨어 쪽 원인

먼저 **차이의 모양**을 본다. 작은 소수(0.01·…0000004)면 10진 소수의 2진 표현, 빌드·CPU마다 다르면 덧셈 순서, 부하가 클수록 모자라면 동시성이다.

```text
  합계·건수가 기준과 다름
     │
     ├─ ...0000004 · 차액 0.01 행, 예외 없음 ──────────────────────────▶ 0.1·4.35를 2진으로 정확히 못 담음        03-1 · 03-3
     ├─ 빌드 옵션·CPU마다 끝자리가 다름(-ffast-math 유무) ───────────────▶ 벡터화가 덧셈 순서를 바꿈                21-2 · math/15
     ├─ 처리 건수 카운터가 로그보다 몇 % 적음, 부하가 클수록 ─────────────▶ volatile int++ 비원자 → 갱신 유실       14-3
     ├─ 집계표에 0.0과 -0.0 행이 따로 ─────────────────────────────────▶ −0.0의 equals·hashCode가 0.0과 다름    03-4
     ├─ 중복 제거 뒤 원소 수가 줄었다 / 최댓값이 NaN 위치에 따라 다름 ──────▶ NaN이 비교자의 추이성을 깨뜨림           03-2
     ├─ 64비트 ID가 끝자리만 바뀜 ──────────────────────────────────────▶ 2^53 초과 정수를 double로              03-5
     └─ float 카운터가 16,777,216 근처에서 멈춤 ─────────────────────────▶ float 가수 24비트                       math/16 4절
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `if (sum == expected)`가 가끔 실패, 로그의 `0.30000000000000004` | 0.1·0.2·0.3이 각각 반올림돼 저장되고 합도 반올림 | 같은 값을 `new BigDecimal(double)`로 찍어 긴 꼬리 확인 | [03-1](../03-floating-point-ieee754/2-summary.md) |
| 4.35달러가 434센트, 대사 배치의 "차액 0.01" | 4.35가 4.3499…로 저장되고 `(long)`이 0 쪽으로 버림 | 금액이 `double`을 거치는 경로가 있나 | [03-3](../03-floating-point-ieee754/2-summary.md) · [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) |
| `fsum`이 `-ffast-math` 유무로 2.919377e+05 ↔ 2.919381e+05(21번 실험) | 벡터화된 축약이 칸별 부분합을 따로 쌓음 | 빌드 옵션별 같은 입력 합계, `-fopt-info-vec` | [21-2](../21-simd-and-gpu/2-summary.md) · [math/16](../../math/16-math-symptom-index/2-summary.md) 4절 |
| 처리 건수가 로그 건수보다 몇 % 적음, 예외 없음 | `volatile int++` 비원자(14번 실험: 2천만 중 42만~407만 유실) | 카운터 타입·증가 코드 | [14-3](../14-cache-coherence-and-memory-ordering/2-summary.md) |
| 집계표에 `0.0`과 `-0.0` 행 | `-1e-300 * 1e-300` 같은 언더플로가 −0.0을 만듦 | `Double.doubleToRawLongBits`로 부호 비트 | [03-4](../03-floating-point-ieee754/2-summary.md) |
| 정렬이 섞이고 `TreeSet` 원소가 사라짐 | `<`·`>` 비교자 + NaN | 데이터에 NaN이 있나, `Double::compare`로 바꿔 재실행 | [03-2](../03-floating-point-ieee754/2-summary.md) |
| ID `9007199254740993`이 `…992`로 | binary64 유효숫자 53비트 | ID가 `double`·JS `Number`를 거치나 | [03-5](../03-floating-point-ieee754/2-summary.md) · [api-design/29](../../api-design/29-api-incidents/2-summary.md) |

- 수학 쪽 원인(큰 수 + 작은 수 누적, 파국적 상쇄, 3치 논리)과 처방(Kahan 합·웰퍼드)은 [math/16](../../math/16-math-symptom-index/2-summary.md) 4절로 간다. 이 표와 겹치는 행은 `-ffast-math`(math/16의 15-4)다.

### 4. 글자가 깨진다 — 모지바케·`�`·길이 초과·대소문자

먼저 **바이트를 본다**(`xxd`). 글자 수가 아니라 바이트로 보면 원인이 갈린다.

```text
  글자가 이상함
     │
     ├─ é → Ã©, 오류 로그 없음, 값 길이가 한 글자씩 늘어 있음 ──────────▶ UTF-8을 Latin-1·CP1252로 디코딩       04-1
     ├─ 끝 이모지가 ? 또는 � ─────────────────────────────────────────▶ UTF-16 단위·바이트 단위로 자름         04-2 · 05-2
     ├─ 같은 이름 파일이 두 개, 이름으로 찾으면 없음 ─────────────────────▶ NFC vs NFD                           04-3
     ├─ ERROR 1366 Incorrect string value (MySQL) ────────────────────▶ utf8(=utf8mb3)에 4바이트 문자          04-4
     ├─ value too long / Data too long, 검증은 통과했는데 ──────────────▶ 길이 단위가 다름(그래핌·UTF-16·문자)    05-1
     ├─ 특정 지역 서버에서만 enum 파싱 실패 · tıtle ─────────────────────▶ 로캘 의존 대소문자(터키어 I/i)          05-3
     ├─ 다른 사람 계정 비밀번호가 바뀜 ────────────────────────────────▶ 멱등이 아닌 정규화                      05-4
     ├─ 똑같아 보이는 사칭 계정이 UNIQUE를 통과 ─────────────────────────▶ 다른 스크립트의 닮은 글자               05-5
     └─ .. 금지 검사를 통과한 경로 탐색, 요청 바이트에 C0 AE ──────────────▶ 관대한 디코딩 + 검사 순서              04-5
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| `cafÃ©`, `café` 4자 → 5자, 두 번 거치면 `Ã`·`Â`가 더 붙음 | 쓰는 쪽 UTF-8, 읽는 쪽 ISO-8859-1·Windows-1252. HTTP `charset` 없음 | 저장 값 `xxd`(`c3 83 c2 a9`면 이중 인코딩), 응답 `Content-Type` | [04-1](../04-character-encoding-unicode/2-summary.md) |
| 잘린 닉네임 끝이 `?`(Java `3F`) 또는 `�`(JS `EF BF BD`) | 서로게이트 쌍·UTF-8 시퀀스 중간 절단 + 대체 문자 | 자른 문자열 끝의 `D83C` 같은 외톨이 서로게이트 | [04-2](../04-character-encoding-unicode/2-summary.md) · [05-2](../05-text-length-segmentation-and-case/2-summary.md) |
| `ls`에 같은 이름 두 개, `length()` 6 대 10, `ls \| xxd`에 `e1 84 92` | NFD(자모 분리) vs NFC | `Normalizer.isNormalized(s, NFC)` | [04-3](../04-character-encoding-unicode/2-summary.md) |
| `ERROR 1366 (HY000): Incorrect string value: ... for column ...` | MySQL `utf8`은 `utf8mb3` 별칭, 4바이트 UTF-8 불가 | 컬럼 문자셋, 입력에 U+10000 이상 코드 포인트 | [04-4](../04-character-encoding-unicode/2-summary.md) |
| PostgreSQL `value too long for type character varying(10)`, MySQL strict `ERROR 1406 (22001): Data too long` | 검증은 그래핌·JS `length`, DB는 "문자" 수(국기 10개 = 그래핌 10, 코드 포인트 20, `length` 40. DB의 "문자"가 코드 포인트라는 것은 05의 해석 `[?]`) | 네 단위(바이트·UTF-16·코드 포인트·그래핌)로 길이 출력 | [05-1](../05-text-length-segmentation-and-case/2-summary.md) |
| `IllegalArgumentException: No enum constant …İNFO`, `"TITLE".toLowerCase()` → `tıtle` | 인자 없는 대소문자 변환이 JVM 기본 로캘(터키어) 사용 | `Locale.getDefault()`, `-Duser.language=tr`로 재현 | [05-3](../05-text-length-segmentation-and-case/2-summary.md) |
| 다른 사람 계정의 비밀번호가 바뀜, 오류 없음. 가입 이름 `ᴮᴵᴳᴮᴵᴿᴰ`을 정규화하면 1회 `BIGBIRD`, 2회 `bigbird`(Spotify 2013 원문) | 정규화 함수가 멱등이 아님 | `canon(x) == canon(canon(x))` 검사 | [05-4](../05-text-length-segmentation-and-case/2-summary.md) |
| `pаypаl`(키릴 а)이 UNIQUE 통과 | 정규화는 다른 스크립트를 합치지 않음 | 코드 포인트의 스크립트 섞임 | [05-5](../05-text-length-segmentation-and-case/2-summary.md) |
| 경로 검사를 통과한 `..`, 요청 바이트 `2F C0 AE 2E 2F` | 과잉 길이 UTF-8을 관대하게 디코딩 + 디코딩 전에 검사 | 검사 시점의 값과 사용 시점의 값이 같은 단계인가 | [04-5](../04-character-encoding-unicode/2-summary.md) |

- 처방의 방향: 디코딩 지점마다 문자셋을 명시하고, 들어오는 순간 NFC로 맞추고, 자르기는 그래핌 경계 함수 하나로 모은다. 로캘 무관 문자열은 `Locale.ROOT`.

### 5. 필드 값이 256의 거듭제곱 배로 틀리거나 순서가 뒤섞인다

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 8080에서 듣게 했는데 `ss -ltn`에 `:36895`, `Connection refused`, 덤프 `90 1f` | `htons` 누락 — 호스트(리틀) 순서 그대로 | 값을 16진으로 써서 바이트를 뒤집으면 원래 값인가(0x1F90 ↔ 0x901F) | [06-1](../06-byte-order-and-alignment/2-summary.md) |
| 길이 로그 65536·16777216, `BufferUnderflowException` | 리틀 엔디안 형식을 `ByteBuffer` 기본(BIG_ENDIAN)으로 읽음 | 원시 바이트 `xxd`, 파서의 `order(...)` | [06-2](../06-byte-order-and-alignment/2-summary.md) |
| 32비트·다른 컴파일러 클라이언트가 `id`를 4바이트 밀려 읽음, 같은 메시지의 해시가 매번 다름 | 패딩 포함 구조체 직렬화(`-m64` 24바이트 vs `-m32` 20바이트), 패딩 값 미정 | `sizeof`·`offsetof` 출력, 패딩 칸 바이트 | [06-4](../06-byte-order-and-alignment/2-summary.md) |
| "최근 100건" 범위 조회 순서가 뒤섞임, 음수 키가 맨 뒤 | 리틀 엔디안 키 또는 부호 비트 그대로의 빅 엔디안 키 | 키 바이트를 사전순으로 정렬해 숫자 순서와 비교 | [06-5](../06-byte-order-and-alignment/2-summary.md) |
| Java와 C 모듈이 비ASCII 키에서만 다른 샤드 선택 | UTF-8 바이트 0x80 이상을 `byte`(음수) vs `unsigned char`로 더함 | 0x80 이상 바이트가 든 테스트 벡터 | [01-3](../01-number-systems-twos-complement/2-summary.md) |

### 6. 스레드·코어를 늘렸더니 더 느리다

먼저 **스레드 덤프와 CPU 사용률**을 같이 본다. 락 대기(`BLOCKED`)가 없는데 `RUNNABLE`로 CPU만 쓰면 캐시 라인 경합을, 실행 대기(`r`)·문맥 전환(`cs`)이 크면 코어 수 초과를 의심한다.

```text
  스레드·코어를 늘렸는데 처리량이 같거나 줄었다
     │
     ├─ 락 대기 없음(RUNNABLE), CPU는 오름, 스레드별 카운터 ──────────────▶ false sharing(같은 64B 라인)         12-1
     ├─ 스레드 수 > 코어 수, vmstat r·cs 증가, 같은 락 대기 다수 ──────────▶ 코어 수 이상 스레드 경합              20-2
     ├─ 코어가 남는데 두 작업이 각자 반 속도, psr이 SMT 형제 ──────────────▶ 실행 유닛 공유                       20-3
     ├─ 기계를 바꾸니 결론이 뒤집힘(패딩 효과 유/무) ──────────────────────▶ 스레드가 같은 물리 코어에 배정됐나      12-3
     ├─ 패딩을 넣었는데 효과 없음 ─────────────────────────────────────▶ JVM이 필드 배치를 바꿈                 12-4
     ├─ 같은 코드인데 인스턴스·시간대마다 p99 편차, 힙 페이지가 다른 노드 ────▶ NUMA 원격 메모리                      20-1
     └─ 응답 시간이 두 무리로, 느린 쪽 psr이 E코어 ──────────────────────▶ 하이브리드 P/E 코어                    20-4 · 11-4
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 스레드별 카운터로 바꿨더니 처리량 감소, 덤프는 `RUNNABLE`뿐 | 스레드별 칸이 같은 64B 라인 — 원자적 증가마다 라인 이동(이 호스트 3~6배(C), 3~7배(Java) 느림) | 칸 간격을 128B로 띄워 스레드 수별 처리량 비교 | [12-1](../12-cache-organization/2-summary.md) |
| CPU 2개에서 스레드 2개 96,535~105,211 ops/s → 32개 64,511~78,384 ops/s, 최악 지연 60~125ms(20번 실험) | 처리량 상한은 일할 수 있는 CPU 몫(실험은 2개), 락 보유자 선점도 가능한 원인(실험은 직접 재지 않음) | `vmstat 1`의 `r`·`cs`, `nproc`과 풀 크기, 컨테이너 쿼터 | [20-2](../20-multicore-and-numa/2-summary.md) |
| `ps -eLo pid,tid,psr,pcpu,comm`의 `psr`이 같은 물리 코어 형제(이 호스트 예 4와 5), 스레드당 426~469 → 200~223 Mops/s | SMT 형제가 실행 유닛을 나눠 씀 | `lscpu -e`의 CORE 열로 형제 확인, `taskset`으로 다른 코어에 고정 | [20-3](../20-multicore-and-numa/2-summary.md) |
| 개발 PC에서는 "패딩 효과 없음", 운영에서는 몇 배 | 같은 물리 코어의 두 하드웨어 스레드는 L1을 공유해 false sharing이 안 보임 | 결과에 CPU 번호·토폴로지 기록, 코어 쌍 고정 | [12-3](../12-cache-organization/2-summary.md) |
| `long p1..p7` 패딩 전후 처리량이 같음 | 필드 배치는 JVM 재량 | `Unsafe.objectFieldOffset`·JOL로 실제 오프셋 | [12-4](../12-cache-organization/2-summary.md) |
| `/proc/<pid>/numa_maps`·`numastat -p <pid>`에서 힙 페이지가 스레드가 도는 노드가 아닌 `N1=`에 몰림(`numastat`의 `numa_miss`·`other_node`는 할당 통계라 할당 뒤 스레드 이동으로 생긴 원격 접근에는 안 늘 수 있음) | 처음 건드린 노드에 할당 + 스레드 이동 | `numactl -H`, `numastat -p <pid>` | [20-1](../20-multicore-and-numa/2-summary.md) |
| 지연 분포가 두 봉우리, 느린 요청 스레드의 `psr`이 16~23(이 호스트 E코어) | P/E 코어의 클록·캐시 차이(이 호스트 L1D 48KB vs 32KB) | `taskset -c`로 코어 종류별로 따로 측정 | [20-4](../20-multicore-and-numa/2-summary.md) · [11-4](../11-memory-hierarchy-and-locality/2-summary.md) |

- 처방의 방향: 스레드별 누적은 `LongAdder`·스레드 로컬 후 합산. 계산 풀은 코어 수 근처. 무거운 계산은 서로 다른 물리 코어에. 지연 민감 서비스는 cpuset으로 코어 종류·NUMA 노드를 고정한다. 바꾼 뒤 **스레드 수별 처리량 곡선**으로 확인한다.

### 7. 같은 알고리즘인데 수~수십 배 느리다 — 메모리·분기·지연

먼저 **같은 기계에서 한 가지만 바꿔** 비율을 잰다(크기, 순회 방향, 입력 순서, 컴파일 옵션). 하드웨어 카운터(`perf`)가 없으면 "캐시 미스 때문"은 실험 설계와 문헌이 뒷받침하는 해석이다.

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| 데이터 10배에 배치 시간 30배, CPU 100%, GC 평범 | 가설: 작업 집합이 L3(이 호스트 30MB)를 넘어 무작위 포인터 추적이 DRAM까지 감(확정은 LLC 미스 카운터나 크기별 곡선) | 원소당 시간을 크기별로 그려 꺾이는 크기 | [11-1](../11-memory-hierarchy-and-locality/2-summary.md) |
| 열 방향 처리가 행 방향보다 수~십수 배(C에서 캐시를 넘는 크기 2~16배, Java `int[2048][2048]` 15~35배) | 행 우선 배치에서 열 방향은 매 접근이 다른 캐시 라인 | 루프 순서만 바꿔 비교 | [11-2](../11-memory-hierarchy-and-locality/2-summary.md) |
| `GC.class_histogram`에 `java.lang.Long` 수백만, 순회가 `long[]`의 10~40배 | 박싱 객체 — 원소마다 헤더 + 참조를 한 번 더 따라가는 간접 참조(객체가 흩어져 있으면 라인마다 미스) | `jcmd <pid> GC.class_histogram` | [11-3](../11-memory-hierarchy-and-locality/2-summary.md) |
| 1000×1000은 빠른데 1024×1024에서 몇 배, 2의 거듭제곱마다 봉우리 | 행 길이 4096B → 열 방향 접근이 한두 집합에 몰리는 충돌 미스 | N=1000·1024·1040으로 같은 처리 | [12-2](../12-cache-organization/2-summary.md) |
| 어제 5분, 오늘 40분, 데이터 양은 같고 입력이 섞여 옴 | 뜨거운 루프의 분기 예측 실패(18번 실험 약 11배) | 같은 데이터를 정렬/셔플해 비교 | [18-1](../18-pipelining-and-branch-prediction/2-summary.md) |
| 벤치마크는 빨랐는데 운영 처리량이 몇 분의 1 | 벤치마크 데이터가 단조로워 분기 예측이 다 맞음 | 운영 분포를 닮은 무작위 데이터로 재측정 | [18-2](../18-pipelining-and-branch-prediction/2-summary.md) |
| 브랜치리스로 바꿨더니 회귀(sorted에서 분기 60 ms vs 브랜치리스 160 ms) | 한쪽으로 쏠린 분기는 원래 예측이 잘 맞았음 | 대표 분포 여러 개로 측정 | [18-3](../18-pipelining-and-branch-prediction/2-summary.md) |
| 정렬/무작위 시간이 같음(C `-O2` 0.061s vs 0.067s) | 컴파일러가 분기를 없앰 — 이 실험의 `-O2`·`-O3`는 자동 벡터화의 마스크 연산, `-O1`은 `cmov` | `objdump -d`에 조건 분기가 남았나 | [18-4](../18-pipelining-and-branch-prediction/2-summary.md) |
| 단순 합계 루프가 기대의 4분의 1 속도(누적기 1개 0.19s vs 4개 0.05s) | 의존 사슬 하나 — 비순차 코어가 겹칠 일이 없음 | 누적기를 나눈 판과 비교 | [19-4](../19-out-of-order-and-speculation/2-summary.md) |
| SIMD로 마이크로벤치마크 4배, 대용량은 그대로(64MiB 1.77~2.03 → 1.53~1.56ns) | 데이터가 캐시 밖이면 메모리(대역폭·지연)가 상한이 되기 쉬움(해석 — 실험은 시간만 잼) | 배열 크기를 L1 안 / 64MiB로 바꿔 비교 | [21-4](../21-simd-and-gpu/2-summary.md) |
| GPU로 옮긴 규칙 엔진이 CPU보다 느림 | 워프 안 분기 — 갈래마다 차례 실행 | 원소별 경로 다양성, 프로파일러의 워프 실행 효율 `[?]` | [21-1](../21-simd-and-gpu/2-summary.md) |
| 목록 API가 건수에 비례해 느림, DB CPU는 한가, 짧은 DB 스팬 수백 개 | 루프 안 원격 호출(N+1) — 왕복 × 건수 | 요청당 쿼리 수 | [13-1](../13-latency-numbers/2-summary.md) |
| 히트율 99% → 95%인데 지연이 몇 배 | AMAT = 히트 + 미스율 × 페널티 | 초당 미스 수 × 미스 페널티 | [13-2](../13-latency-numbers/2-summary.md) |
| 10만 건 적재가 몇 분, 행당 수 ms 일정 | 커밋마다 `fsync`(이 호스트 4KB 쓰기 + `fdatasync` 2.6~2.9ms) | 커밋 횟수, `iostat`의 쓰기 요청 수 | [13-3](../13-latency-numbers/2-summary.md) |
| 특정 리전 사용자만 수백 ms, 외부 호출 하나가 150ms 안팎 | 대륙 간 왕복(빛의 속도 하한) | 트레이스의 외부 호출 시간과 횟수 | [13-4](../13-latency-numbers/2-summary.md) |

### 8. 저장장치·I/O 지연 — SSD 지연 톱니, HDD 지연 폭증, 패킷 드롭

먼저 **장치 종류와 큐 깊이**를 본다(`lsblk -d -o NAME,ROTA`, `iostat -x 1`의 `aqu-sz`·`r_await`·`w_await`).

```text
  저장·네트워크 I/O 지연
     │
     ├─ SSD, 쓰기 많은 구간에 p99가 주기적으로 튐(톱니), 읽기만이면 평평 ──────▶ SSD 내부 GC·지우기                nand-flash §8 · OSTEP 44.4·44.8
     ├─ SSD가 차갈수록 쓰기 대역폭 급락 ──────────────────────────────────▶ 빈 블록 고갈·SLC 캐시 소진          nand-flash §3·§8
     ├─ HDD, 트래픽 조금 늘자 r_await 수백 ms, r/s가 수백에 붙음 ───────────▶ 랜덤 I/O의 IOPS 한계               16-1
     ├─ NVMe인데 안 빨라짐, aqu-sz ≈ 1 ──────────────────────────────────▶ 큐 깊이 1                          16-2
     ├─ 벤치마크 µs, 운영 수십~수백 배 ─────────────────────────────────────▶ 페이지 캐시를 잼                    16-3
     ├─ HDD에 순차 스트림 여럿 → 합계 대역폭 급락 ─────────────────────────────▶ 헤드 왕복으로 랜덤화               16-4
     ├─ 평균은 좋은데 일부 요청만 타임아웃 ──────────────────────────────────▶ 가까운 요청 우선 → 굶김             16-5
     ├─ 한 코어 %soft 100%, 다른 코어 한가 ─────────────────────────────────▶ 인터럽트·softirq가 한 CPU에 몰림    15-1
     ├─ rx_missed_errors 증가(+ time_squeeze), 앱 로그는 깨끗 ──────────────▶ DMA 링 가득 / softirq 예산 소진    15-2
     ├─ 패킷률이 어느 선을 넘자 처리량이 오히려 하락 ──────────────────────────▶ 수신 livelock                     15-3
     ├─ 한가할 때도 CPU 100%, nr_throttled 증가 ────────────────────────────▶ 바쁜 대기(폴링)                    15-4
     └─ 저부하에서 p50이 오히려 높음 ────────────────────────────────────────▶ 과한 인터럽트 병합                 15-5
```

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| SSD 쓰기 부하에서 p99가 주기적으로 튀는 톱니, 지연이 평소의 몇 배 | 후보: 덮어쓰기 불가 → FTL이 새 페이지에 쓰고, GC가 유효 페이지를 옮기고 블록을 지움. 지우기는 "a few milliseconds"(OSTEP 44.4), GC는 "expensive"(44.8). 관찰만으로 내부 GC가 확정되지는 않는다 | `iostat -x 1`에서 `w_await` 봉우리와 쓰기량의 시간 대조, `lsblk -D`·`/sys/block/<dev>/queue/discard_max_bytes`로 TRIM 지원, `systemctl is-enabled fstrim.timer` | [nand-flash §8](../../systems/nand-flash/2-summary.md) · [16](../16-storage-media-workload/2-summary.md) |
| 지속 쓰기 대역폭이 처음보다 크게 떨어짐, `SMART` 마모 경고 | SLC 캐시 소진, 빈 블록 고갈(foreground GC), 쓰기 증폭으로 수명 소진 | 드라이브가 얼마나 찼나(`df`), SMART 마모 지표(`smartctl -a`·`nvme smart-log`, 이 호스트에는 미설치 — 필드 이름 `[?]`) | [nand-flash §3·§8·§9](../../systems/nand-flash/2-summary.md) |
| `iostat -x`의 `r/s`가 수백 근처, `r_await` 수십~수백 ms, `D` 상태 누적 | HDD 랜덤 4KiB 1회 ≈ 12ms → 수백 IOPS가 상한, 이용률 1 근처의 비선형 대기 | `lsblk -d -o NAME,ROTA`(1이면 회전 매체), `aqu-sz` | [16-1](../16-storage-media-workload/2-summary.md) |
| `aqu-sz` ≈ 1, `r_await` 약 0.1ms, `r/s` 1만 근처(QD1 6,950~9,780 vs QD32 213,818~223,337 IOPS) | 앱이 한 번에 읽기 하나만 냄 | 동시 요청 수 | [16-2](../16-storage-media-workload/2-summary.md) |
| 같은 랜덤 4KiB가 캐시면 2.1~2.3µs, 캐시를 비우면 89~91µs | 테스트가 페이지 캐시를 잼 | 테스트 파일 크기 대 RAM, `O_DIRECT`로 재측정 | [16-3](../16-storage-media-workload/2-summary.md) |
| `rareq-sz` 작아지고 `r_await` 커짐, 동시 스트림 10개 | 순차 스트림이 섞여 장치 입장에서 랜덤 | 동시 스트림 수, `read_ahead_kb` | [16-4](../16-storage-media-workload/2-summary.md) |
| 특정 영역 파일만 타임아웃, p99.9 튐 | SSTF식 재정렬의 굶김 | I/O 스케줄러(`/sys/block/<dev>/queue/scheduler`) | [16-5](../16-storage-media-workload/2-summary.md) |
| `mpstat -P ALL`에서 한 CPU의 `%soft`만 높음, `/proc/interrupts`의 NIC 줄이 한 열만 증가 | 단일 큐 NIC·IRQ 친화도가 한 CPU로 | `ethtool -l <if>`, `/proc/softirqs`의 `NET_RX` | [15-1](../15-io-devices-interrupts-dma/2-summary.md) |
| `rx_missed_errors`·`rx_fifo_errors` 증가(이 호스트 `rx_missed_errors` 30,278), 같은 시간대 `time_squeeze` 증가 | 장치 쪽 드롭(`rx_missed_errors`)은 수신 디스크립터 링이 찼다는 후보, `time_squeeze`는 softirq 한 주기의 budget·시간 한도 소진이라 그 자체로 링 포화는 아니다 — 둘을 따로 보고 같은 시간대에 겹치면 "소비가 늦어 링이 참"을 의심(해석) | `ethtool -S <if>`, `ethtool -g <if>`, `/proc/net/softnet_stat` | [15-2](../15-io-devices-interrupts-dma/2-summary.md) |
| CPU가 `%irq`·`%soft`로 꽉 차고 `%usr`는 작음, 처리량 하락 | 패킷마다 인터럽트(livelock) | `ethtool -c <if>`의 병합 설정 | [15-3](../15-io-devices-interrupts-dma/2-summary.md) |
| 한가할 때도 코어 수만큼 CPU 사용, `cpu.stat`의 `nr_throttled` 증가 | busy polling·스핀 대기 | 폴링 설정, 소비자 스레드의 CPU | [15-4](../15-io-devices-interrupts-dma/2-summary.md) |
| 저부하 p50이 오히려 높고 NIC 인터럽트 수는 크게 줄음 | 병합 대기 시간이 지연에 더해짐 | `ethtool -c <if>`의 `rx-usecs`·adaptive | [15-5](../15-io-devices-interrupts-dma/2-summary.md) |

- SSD 톱니는 이 영역 leaf가 아니라 [systems/nand-flash](../../systems/nand-flash/2-summary.md)(커리큘럼 17 자리)가 메커니즘을 맡는다. 그 노트의 "평소 100µs가 GC와 겹치면 수 ms" 같은 수치는 그 노트 안에서 출처가 밝혀져 있지 않다. 이 색인은 OSTEP 44.4·44.8의 정성적 서술(지우기가 수 ms, GC는 비쌈)까지만 근거로 쓴다.
- 쓰기 증폭을 줄이는 쪽(순차 append·세그먼트 통째 삭제·TRIM·여유 공간)이 톱니를 줄이는 방향이라는 것은 nand-flash §8·§10의 설명이다. 이 호스트에서 톱니를 재현하지는 않았다(장시간 쓰기 부하가 실험 상한을 넘는다).

### 9. 가끔 멈추거나 가끔 틀린다 — 일관성·회로·투기 실행

| 보이는 것 | 원인 후보 | 첫 확인 | leaf |
|---|---|---|---|
| graceful shutdown이 안 끝나 SIGKILL, 워커가 `RUNNABLE`로 같은 루프·한 코어 100% | 일반 필드 플래그를 JIT가 루프 밖으로 끌어냄(14번 실험 10회 중 9회 안 멈춤) | 플래그 필드에 `volatile`이 있나 | [14-1](../14-cache-coherence-and-memory-ordering/2-summary.md) |
| 기동 직후 드물게 포트 0·설정 `null`, 재현 안 됨 | `volatile` 없는 DCL — 참조 공개가 생성자 쓰기보다 먼저 보임 | 싱글턴 생성 코드 | [14-2](../14-cache-coherence-and-memory-ordering/2-summary.md) |
| x86에서 통과, ARM(Graviton·Apple Silicon)에서 간헐 실패 | x86 TSO는 숨겨 주던 재정렬을 ARM은 함 — data race | 락 없이 플래그 + 데이터를 주고받는 코드, ARM CI | [14-4](../14-cache-coherence-and-memory-ordering/2-summary.md) |
| 몇 주에 한 번 "불가능한" 상태 조합, 재현 안 됨(하드웨어) | 비동기 신호의 메타안정성 | 클록 도메인 경계마다 동기화기가 있나 | [08-1](../08-sequential-logic-clock/2-summary.md) · [08-2](../08-sequential-logic-clock/2-summary.md) · [08-3](../08-sequential-logic-clock/2-summary.md) · [08-4](../08-sequential-logic-clock/2-summary.md) |
| 상태 이력에 `CANCELLED → PAID`, 오류 로그 없음 | 전이표 없이 들어온 이벤트로 덮어씀 | 상태 갱신 코드가 전이표를 검사하나 | [08-5](../08-sequential-logic-clock/2-summary.md) |
| 커널·마이크로코드 업데이트 뒤 같은 부하에서 `sys` 비중 증가 | Spectre·Meltdown 완화 — PTI는 커널 진입·탈출마다 CR3 전환(시스템 콜 빈도에 비례), IBPB 등은 문맥 전환 등에서 조건부로 | `grep . /sys/devices/system/cpu/vulnerabilities/*`, `/proc/cmdline` | [19-1](../19-out-of-order-and-speculation/2-summary.md) · [23 사건 4](../23-arch-incidents/2-summary.md) |
| 같은 인스턴스 유형인데 호스트마다 `sys` 시간만 다름 | CPU 세대마다 취약 여부·켜진 완화가 다름 | 호스트별 `vulnerabilities` 출력 비교 | [19-3](../19-out-of-order-and-speculation/2-summary.md) |
| 컨테이너 안에서도 호스트와 같은 `vulnerabilities` 값 | 컨테이너는 커널·코어·캐시를 공유 | 신뢰 수준이 다른 작업이 같은 호스트에 있나 | [19-2](../19-out-of-order-and-speculation/2-summary.md) |
| flame graph에 `[unknown]`, 중간 함수가 통째로 빠짐 | 프레임 포인터 생략(`-O2`, HotSpot `PreserveFramePointer` 기본 꺼짐) | 빌드 플래그, `objdump -d`의 `push %rbp; mov %rsp,%rbp` 유무 | [10-4](../10-calling-convention-and-stack-frame/2-summary.md) |

### 10. 증상별 "하지 말 것" 한 줄

| 하지 말 것 | 이유 | 대신 |
|---|---|---|
| `exec format error`·`Illegal instruction`에 재시작·재배포만 반복 | 이미지·바이너리가 그대로면 매번 같다 | `file`·`docker image inspect`로 아키텍처, `/proc/cpuinfo`로 명령 확장 |
| 음수 금액을 `Math.abs`나 `if (x < 0) x = 0`으로 덮음 | 넘친 값은 이미 정보를 잃었다 | 타입 폭을 넓히고 `Math.addExact`로 넘침을 예외로 |
| 합계 차이를 전부 "부동소수 오차"로 분류 | 동시성 유실(14-3)·좁히기·순서 변경(21-2)이 섞여 있다 | 차이의 모양(소수·빌드별·부하 비례)으로 먼저 가른다 |
| 모지바케를 `replace("Ã©", "é")`로 고침 | 원인 디코딩 지점이 그대로라 다른 글자가 계속 깨진다 | 디코딩 지점에 문자셋을 명시, 저장값은 확실할 때만 역변환 |
| "멀티스레드가 느리다"에 스레드를 더 늘림 | 경합·라인 이동이 늘 뿐이다 | 스레드 수별 처리량 곡선, 라인 분리, 코어 수 근처로 |
| 다른 기계·코어에서 잰 벤치마크로 결론 | 코어 종류·SMT 배치·완화 설정이 결과를 뒤집는다 | CPU 모델·코어 번호·`vulnerabilities`를 결과와 함께 기록 |
| SSD 톱니에 타임아웃만 늘림 | 장치 안의 GC는 그대로다 | 쓰기 패턴(순차·통째 삭제)·TRIM·여유 공간 점검 |

## 쓰이는 자료구조·알고리즘

- **역색인**: 증상(키) → leaf 목록. 이 노트 자체가 손으로 만든 역색인이다([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
- **결정 트리**: 각 절의 트리는 "가장 싼 관찰로 후보를 반으로 가르는" 순서다. 종료 코드 → 메시지 → 기계 정보 → 값의 16진 → 비율 측정 순으로 비용이 커진다.
- **비율 측정(두 배 실험)**: 크기·스레드 수·입력 순서 하나만 바꿔 시간 비율을 본다. 같은 방법을 알고리즘 영역은 복잡도 판정에 쓴다([algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md) 1절). 이 영역은 캐시 계층의 꺾임(11-1)·충돌(12-2)·분기 예측(18-1)을 가르는 데 쓴다.
- **2의 보수·16진 해석**: 로그의 거대한 값·음수를 비트로 다시 읽는 일([01](../01-number-systems-twos-complement/2-summary.md)).
- 관련 색인: [os/37](../../os/37-os-symptom-index/2-summary.md)(종료 코드·errno) · [math/16](../../math/16-math-symptom-index/2-summary.md)(합계 불일치의 수학) · [algorithm/42](../../algorithm/42-alg-symptom-index/2-summary.md)(복잡도) · [data-structure/43](../../data-structure/43-ds-symptom-index/2-summary.md) · [database/56](../../database/56-db-symptom-index/2-summary.md)(`1366`·`1292` 등 DB 오류 코드) · [network/52](../../network/52-network-symptom-index/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

```text
  ① 원문 보존     종료 코드, 신호 이름, 예외 전체, 로그 수치(16진 함께)
  ② 기계 고정     uname -m · lscpu · 커널 · 이미지 플랫폼 · 코어 번호(psr)
  ③ 절 고르기     0절의 표로 층을 고른다 (신호 / 숫자 / 합계 / 글자 / 필드 / 스레드 / 속도 / I/O / 간헐)
  ④ 첫 확인       그 절 표의 "첫 확인" 한 가지로 후보를 줄인다
  ⑤ leaf로        원인이 하나로 줄면 leaf의 대처를 따른다. 줄지 않으면 ④의 다음 확인
```

### 2. 첫 확인 명령 모음

```bash
# 아키텍처·명령 확장 (1절)
uname -m; file ./app; docker image inspect --format '{{.Os}}/{{.Architecture}}' <image>
grep -o -w -m1 avx512f /proc/cpuinfo; ls /proc/sys/fs/binfmt_misc/
# 값을 비트로 (2·5절)
printf '%x\n' 4294967295; printf '%s' "$s" | xxd | head
# 문자 (4절)
printf 'café' | xxd; printf 'cafÃ©' | iconv -f utf-8 -t latin1 | xxd     # 이중 인코딩 되돌려 보기
# 코어·NUMA (6절)
lscpu -e; numactl -H; ps -eLo pid,tid,psr,pcpu,comm | sort -k4 -nr | head; vmstat 1 5
# 메모리·JVM (7절)
jcmd <pid> GC.class_histogram | head; objdump -d ./app | less
# 저장·네트워크 (8절)
lsblk -d -o NAME,ROTA; iostat -x 1; cat /sys/block/nvme0n1/queue/discard_max_bytes; systemctl is-enabled fstrim.timer
grep -E 'CPU|eth|eno|nvme' /proc/interrupts | head; ethtool -S <if> | grep -E 'missed|fifo|drop'
# 투기 실행 완화 (9절)
grep . /sys/devices/system/cpu/vulnerabilities/*; cat /proc/cmdline
```

- 이 호스트(i7-13700HX, 2026-10-07)에서 읽은 값 예: `/sys/block/nvme0n1/queue/discard_max_bytes` = 2199023255040(TRIM 지원), `rotational` = 0, `fstrim.timer` = `enabled`, 루트 파일 시스템 `ext4 rw,relatime`(`discard` 마운트 옵션 없음 — 주기적 TRIM 방식). 다른 기계에서는 값이 다르다.

### 3. 증상을 미리 드러내는 테스트 — Java 21

```java
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.text.Normalizer;
import java.util.Locale;

class ArchGuards {
    // 2절: 넘침을 예외로 — 음수 금액 대신 실패
    static long addMoney(long a, long b) { return Math.addExact(a, b); }

    // 2절·23 사건 5: 32비트 필드에 시각을 담기 전에 범위 검사
    static int epochSecondsFor32bitField(long epochSeconds) { return Math.toIntExact(epochSeconds); }

    // 5절: 형식의 바이트 순서를 코드에 박는다
    static int readLength(byte[] wire, ByteOrder order) { return ByteBuffer.wrap(wire).order(order).getInt(); }

    // 4절: 들어오는 순간 NFC, 로캘 무관 소문자
    static String canonicalName(String s) {
        return Normalizer.normalize(s, Normalizer.Form.NFC).toLowerCase(Locale.ROOT);
    }

    // 4절: 바이트 한도 검사는 바이트로
    static boolean fitsBytes(String s, int maxBytes) {
        return s.getBytes(StandardCharsets.UTF_8).length <= maxBytes;
    }
}
```

- 테스트 입력에 넣을 경계값: `Integer.MAX_VALUE`·2³¹초(2038-01-19T03:14:08Z), 길이 바이트 127·128·255, `😀`(4바이트)·`🇰🇷`(코드 포인트 2개), NFD 한글, 터키어 로캘(`-Duser.language=tr`), 리틀 엔디안 길이 `00 01 00 00`.
- 성능 쪽 경계: 데이터 크기를 L1·L3·RAM 경계를 넘게 바꿔 보고, 입력을 정렬/셔플해 보고, 스레드 수를 1·2·코어 수·코어 수 × 4로 바꿔 본다.

## 장애 시나리오와 대처

### 1. `exec format error`를 "이미지가 깨졌다"로 읽고 재빌드만 반복

- **현상**: 새 이미지 배포 뒤 파드가 `CrashLoopBackOff`. 같은 Dockerfile로 다시 빌드해 올려도 같다.
- **보이는 형태**: 컨테이너 로그 한 줄 `exec /app/server: exec format error`. 개발자 노트북에서는 잘 돈다.
- **원인**: 노트북(ARM64)에서 `--platform` 없이 빌드해 ARM64 단일 이미지가 올라갔다. 재빌드도 같은 노트북에서 했다([09-1](../09-isa-and-machine-code/2-summary.md)).
- **대처**: `docker image inspect`로 플랫폼을 보고 `file`로 엔트리포인트를 본다. CI에서 `--platform`을 명시하거나 다중 플랫폼 이미지를 만든다. 노드 아키텍처 레이블로 배치를 제한한다.

### 2. 음수 금액을 화면에서만 0으로 막음

- **현상**: 정산 리포트에 음수가 보여 표시 로직에 `max(0, x)`를 넣었다. 다음 달 대사에서 수십억 원 차이가 난다.
- **보이는 형태**: 표시는 0. 표시 전의 원시 합계(로그 값)와 원장 합계의 차이가 2³²(4,294,967,296)의 배수다.
- **원인**: 누적 변수가 `int`라 21억을 넘을 때마다 2³²만큼 감겼다([02-1](../02-integer-overflow-and-truncation/2-summary.md)). 표시만 고쳐 원인이 남았다.
- **대처**: 차이가 2³²의 배수인지 먼저 본다(정수 감김의 지문). 누적 타입을 `long`으로, 덧셈은 `Math.addExact`로 바꾸고 과거 데이터를 다시 집계한다.

### 3. "멀티스레드가 더 느리다"에 스레드 풀을 키움

- **현상**: 처리량을 올리려 풀을 8 → 64로 키웠더니 처리량이 줄고 p99가 늘었다.
- **보이는 형태**: CPU 사용률은 올랐다. `vmstat`의 `r`·`cs`가 크다. 덤프에 같은 락 대기, 또는 락 없는 `RUNNABLE` 스레드가 같은 카운터 객체를 갱신.
- **원인**: 코어 수 초과 경합([20-2](../20-multicore-and-numa/2-summary.md))과 스레드별 카운터의 false sharing([12-1](../12-cache-organization/2-summary.md))이 겹쳤다.
- **대처**: 풀을 코어 수 근처로 되돌리고, 카운터를 `LongAdder`로 바꾼다. 스레드 수 1·2·코어 수·코어 수 × 4에서 처리량 곡선을 그려 확인한다.

### 4. SSD 지연 톱니를 애플리케이션 GC로 오인

- **현상**: 쓰기 많은 배치 시간대에 DB p99가 주기적으로 튄다. JVM GC 로그를 튜닝했지만 그대로다.
- **보이는 형태**: 톱니 시각이 JVM GC 시각과 맞지 않는다. `iostat -x 1`의 `w_await` 봉우리와 맞는다. 읽기만 하는 시간대에는 평평하다.
- **원인**: 장치 쪽 후보로 SSD 내부 GC·블록 지우기([nand-flash §8](../../systems/nand-flash/2-summary.md), OSTEP 44.4·44.8). `w_await`는 큐 대기와 서비스 시간을 함께 담으므로(sysstat iostat 매뉴얼) 시각 일치만으로 내부 GC가 확정되지는 않는다(해석). 디스크가 거의 차 있고 TRIM이 돌지 않으면 GC가 옮길 유효 페이지가 많아진다(nand-flash §8 설명).
- **대처**: 시각 대조로 층을 먼저 가른다(앱 GC 로그 vs `iostat`). 여유 공간·TRIM(`fstrim.timer`)·쓰기 패턴(순차 append, 통째 삭제)을 점검한다. 지연 목표가 엄격하면 쓰기 많은 작업을 다른 장치로 나눈다.

### 5. 하드웨어 증상을 소프트웨어 버그로만 쫓음

- **현상**: 특정 서버에서만 압축 해제 결과가 가끔 틀리거나, 특정 서버에서만 바이너리가 `Illegal instruction`으로 죽는다. 코드 리뷰로는 원인이 안 나온다.
- **보이는 형태**: 같은 입력을 다른 서버에서 돌리면 맞는다. 커널·이벤트 로그는 깨끗하다.
- **원인**: 결함 코어의 조용한 데이터 손상([07-2](../07-logic-gates-to-adder/2-summary.md)), 또는 그 서버 CPU에 없는 명령 확장([09-3](../09-isa-and-machine-code/2-summary.md)).
- **대처**: 서버·코어를 고정해 재현한다(`taskset -c N`). `/proc/cpuinfo` 플래그를 비교한다. 재현되면 코어·서버를 격리하고, 중요한 계산에는 결과 검증(체크섬·이중 계산)을 둔다.

## 핵심 문장

- 표현·하드웨어 증상은 "가정한 폭·순서·부호화·아키텍처·코어·매체가 실제와 다를 때" 보인다. 첫 질문은 "어느 기계에서, 어떤 값으로"다.
- 신호로 죽으면 종료 코드(bash·Docker의 128 + N)로 먼저 가른다. x86-64 Linux에서 132는 잘못된 명령(없는 확장 또는 `ud2` 같은 의도적 트랩), 135는 정렬·잘린 매핑(SIGBUS 7 — MIPS 등은 번호가 다르다, signal(7)), 139는 잘못된 주소다. `exec format error`는 대개 아키텍처 불일치다(그 밖의 형식 오류도 같은 `ENOEXEC`).
- 숫자가 이상하면 16진으로 다시 본다. `0xFFFFFFFF`·`0x80000000`·256의 거듭제곱·2³²의 배수 차이는 표현 문제의 지문이다.
- 글자가 이상하면 바이트를 본다(`xxd`). `c3 83 c2 a9`는 이중 인코딩, 끝의 `ef bf bd`는 중간 절단이다.
- 스레드를 늘려 느려지면 더 늘리지 말고 스레드 수별 곡선을 그린다. 같은 라인·같은 코어·같은 락이 원인 후보다.
- 성능 증상은 같은 기계·같은 코어에서 한 가지만 바꾼 비율로 가르고, 측정 조건(CPU·코어 번호·완화 설정)을 결과와 함께 남긴다.

## 관련 주제·근거

- 이 영역 leaf(시나리오 번호는 각 노트의 「장애 시나리오와 대처」)
  - 데이터 표현: [01](../01-number-systems-twos-complement/2-summary.md) · [02](../02-integer-overflow-and-truncation/2-summary.md) · [03](../03-floating-point-ieee754/2-summary.md) · [04](../04-character-encoding-unicode/2-summary.md) · [05](../05-text-length-segmentation-and-case/2-summary.md) · [06](../06-byte-order-and-alignment/2-summary.md)
  - 회로·명령어: [07](../07-logic-gates-to-adder/2-summary.md) · [08](../08-sequential-logic-clock/2-summary.md) · [09](../09-isa-and-machine-code/2-summary.md) · [10](../10-calling-convention-and-stack-frame/2-summary.md) · [18](../18-pipelining-and-branch-prediction/2-summary.md) · [19](../19-out-of-order-and-speculation/2-summary.md)
  - 메모리 계층: [11](../11-memory-hierarchy-and-locality/2-summary.md) · [12](../12-cache-organization/2-summary.md) · [13](../13-latency-numbers/2-summary.md) · [14](../14-cache-coherence-and-memory-ordering/2-summary.md)
  - I/O·저장·병렬: [15](../15-io-devices-interrupts-dma/2-summary.md) · [16](../16-storage-media-workload/2-summary.md) · [systems/nand-flash](../../systems/nand-flash/2-summary.md)(커리큘럼 17) · [20](../20-multicore-and-numa/2-summary.md) · [21](../21-simd-and-gpu/2-summary.md)
  - 후속: [23-arch-incidents](../23-arch-incidents/2-summary.md) — 이 색인의 증상이 실제 사고가 된 다섯 사건
- 다른 영역 색인: [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md) · [math/16-math-symptom-index](../../math/16-math-symptom-index/2-summary.md) · [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md) · [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md) · [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md) · [network/52-network-symptom-index](../../network/52-network-symptom-index/2-summary.md) · [security/29-security-symptom-index](../../security/29-security-symptom-index/2-summary.md)
- 근거
  - 각 행의 수치·메시지는 해당 leaf의 실험·출처에서 옮겼다(그 노트의 「관련 주제·근거」에 원 출처).
  - OSTEP 44 "Flash-based SSDs" — 44.4(읽기 수십 µs, 지우기 "a few milliseconds"), 44.8 Garbage Collection("garbage collection can be expensive") <https://pages.cs.wisc.edu/~remzi/OSTEP/file-ssd.pdf>
  - CS:APP 3판 8.5 Signals(3판 서문·목차 PDF <https://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>에서 절 번호 확인), 종료 코드 128 + N 규칙은 [os/37](../../os/37-os-symptom-index/2-summary.md) 1절의 실험
  - 이 노트의 실험
    - `sig.c` — NULL 쓰기·`__builtin_trap`(`ud2`)·잘린 `mmap` 읽기로 SIGSEGV·SIGILL·SIGBUS, 종료 코드 139·132·135(i7-13700HX, Linux 7.0.0-34-generic, gcc 13.3.0 `-O0`, bash `LC_ALL=C`와 기본 로캘)
    - 읽기만 한 값: `file`·`docker image inspect`(로컬 이미지, pull 없음)·`/sys/block/nvme0n1/queue/{discard_max_bytes,rotational}`·`systemctl is-enabled fstrim.timer`·`findmnt`(2026-10-07)
