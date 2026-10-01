# os/09-address-space — 정답

## 정답

### 1. 세 가지 목표

- **투명성**: 프로그램은 자기만의 메모리가 있다고 믿고 쓴다. 없으면 프로그램마다 "몇 번지부터 써도 되는지"를 알아야 한다.
- **보호·격리**: 다른 프로세스와 커널의 메모리를 건드리지 못한다. 없으면 한 버그가 시스템 전체를 망가뜨린다.
- **효율**: 변환과 검사를 하드웨어(MMU)가 한다. 없으면 모든 접근을 소프트웨어로 검사해야 해 너무 느리다.

(OSTEP 13)

### 2. x86-64 리눅스 주소 공간

```text
  높은 주소
  [커널 공간]                     <- 위쪽 절반, 유저 접근 불가
  (비정규 구멍)
  00007fffffffefff  유저 공간 끝
  [stack]           ↓ 아래로 자람
  [vdso] 등
  mmap 영역          ↓ 라이브러리·큰 malloc·스레드 스택
  ...
  [heap]            ↑ 위로 자람 (brk)
  .data + .bss
  .rodata
  .text
  (0 ~ mmap_min_addr) 매핑 금지
  낮은 주소
```

- 4단계 페이지 테이블에서 유저 공간은 약 128 TB다(Documentation/arch/x86/x86_64/mm.rst).
- ASLR 때문에 실제 주소는 실행마다 달라진다(`randomize_va_space = 2`).

### 3. `malloc(64)` vs `malloc(1 MB)`

- `malloc(64)` → (메인 스레드에서는) `[heap]` 줄. brk로 늘린 힙에서 잘라 준다. 다른 스레드라면 `mmap`으로 만든 별도 arena에서 나올 수 있다.
- `malloc(1 MB)` → 이름 없는 익명 `rw-p` 줄(mmap 영역). glibc는 기본적으로 128 KB 이상을 `mmap`으로 받는다(mallopt(3) `M_MMAP_THRESHOLD`, 동적으로 오를 수 있음. 기존 빈 청크로 채워지면 그쪽을 쓴다).
- 로컬 확인(예시): 64바이트는 `0x59289b38f2a0`(`[heap]`), 1 MB는 `0x76cef1299010`(익명 매핑).
- 이유: 큰 블록은 `munmap`으로 운영체제에 곧바로 돌려줄 수 있다. 힙은 꼭대기에서만 줄일 수 있다(mallopt(3)).

### 4. FileSiz와 MemSiz

- 마지막(RW) LOAD 세그먼트는 `.data`와 `.bss`를 담는다. `MemSiz − FileSiz`는 0으로 채울 크기로, 보통 bss 크기다(정렬 패딩이 끼면 조금 클 수 있다. 정확한 `.bss`는 `readelf -SW`).
- 로컬 확인(예시): `FileSiz 0x2c0`, `MemSiz 0x2d0` → 차이 0x10 = 16바이트 = `size`의 bss.
- bss는 "0으로 초기화된 변수"다. 값이 전부 0이라 파일에 적을 필요가 없다. 로더가 크기만큼 0으로 채운 메모리를 만든다.

### 5. 베이스/바운드와 세그먼테이션

```text
  va --> [va < bounds?] --아니오--> 예외(SIGSEGV)
             | 예
             v
         pa = va + base
```

- 가장 큰 낭비: 주소 공간 전체를 **연속으로** 물리 메모리에 잡는다. 힙과 스택 사이 안 쓰는 공간까지 차지한다(OSTEP 15).
- 세그먼테이션: 코드·힙·스택마다 베이스/바운드를 따로 둔다. 빈 공간은 물리 메모리를 쓰지 않고, 세그먼트별 권한·공유도 된다(OSTEP 16).
- 남는 문제: 세그먼트 크기가 제각각이라 **외부 단편화**가 생긴다. 이것을 푸는 것이 고정 크기 페이징이다(10번).

### 6. `SEGV_MAPERR` vs `SEGV_ACCERR`

- `SEGV_MAPERR`(매핑 없음): 널 포인터 읽기, `munmap`된 주소 읽기, 메인 스레드 스택 한도를 넘은 재귀.
  - glibc 2.41까지(이 환경 2.39)는 pthread 스택의 가드 페이지가 권한 없는(`PROT_NONE`) 매핑이라, 스레드 스택 오버플로는 `SEGV_ACCERR`로 나올 수 있다. glibc 2.42+·리눅스 6.13+는 `MADV_GUARD_INSTALL` 가드를 먼저 써서 `SEGV_MAPERR`로 보일 수 있다(`nptl/allocatestack.c`).
- `SEGV_ACCERR`(권한 없음): 문자열 상수(`.rodata`, `r--p`)에 쓰기, 코드 영역에 쓰기, 실행 불가 영역 실행.
- 로컬 재현(예시): 널 읽기 → `addr=(nil) code=SEGV_MAPERR`, 상수 쓰기 → `SEGV_ACCERR`. 둘 다 종료 코드 139.
- 널이 매핑 없는 주소인 이유: `vm.mmap_min_addr`(이 환경 65536) 아래는 `CAP_SYS_RAWIO`가 없는 프로세스가 매핑할 수 없다(security/commoncap.c `cap_mmap_addr`). 그래서 0과 작은 오프셋은 보통 빈 영역이다.
  - "항상"은 아니다. 권한 있는 프로세스는 0 근처를 매핑할 수 있고, 널 구조체의 큰 오프셋 필드는 문턱을 넘을 수 있다.

### 7. 해제 후 읽기 — 작은 블록 vs 큰 블록

- 해제한 메모리 접근은 정의되지 않은 동작이다. 아래는 로컬 재현(glibc 2.39)의 전형적 결과다.
- 작은 블록: **죽지 않았다.** `free`는 할당기의 목록에 돌려놓을 뿐이다. `[heap]` VMA는 그대로라 커널은 접근을 막지 않는다. 로컬 재현에서 42 대신 1681751075가 읽혔다. 할당기가 그 자리에 관리 정보를 썼다.
- 큰 블록: **SIGSEGV(`SEGV_MAPERR`)**. `mmap`으로 받은 블록은 `free`가 `munmap`해 VMA가 사라진다. 큰 블록이라도 arena에서 받았거나, 작은 블록이라도 힙 축소로 매핑이 사라지면 결과가 바뀐다.
- 교훈: SIGSEGV는 VMA·권한 수준의 검사다. 할당기 수준의 "해제됨"은 커널이 모른다. ASan·Valgrind로 잡는다.

### 8. `exit 139` vs `hs_err` + 134

- 139 = 128 + 11 = 보통 SIGSEGV로 죽었다는 뜻이다. 단 `exit(139)`도 같은 값이니, 확정은 `wait` 상태(`WIFSIGNALED`·`WTERMSIG`)나 커널 로그 `segfault at`으로 한다.
- 찾는 법: 코어 덤프를 남긴다(`ulimit -c`, `core_pattern`, `coredumpctl`). `gdb app core` → `bt`로 크래시 함수와 주소를 본다. `si_addr`가 0 근처면 널, 스택 경계 근처면 스택 오버플로다.
- JVM의 경우: 네이티브 코드의 SIGSEGV를 JVM이 받아 `hs_err_pid<pid>.log`를 쓰고 스스로 `abort()`한다(OpenJDK `os_posix.cpp` `os::abort`, `CreateCoredumpOnCrash` 기본 true). 그래서 종료 코드는 보통 SIGABRT의 134다. 로그의 `Problematic frame`은 오류가 드러난 지점이라 원인 라이브러리의 첫 후보다(앞선 손상이 다른 곳에서 드러날 수도 있다). `hs_err`는 JVM 자체 버그·네이티브 메모리 부족에서도 생긴다.

### 9. Java NPE와 SIGSEGV

- HotSpot은 컴파일한 코드에서 "이 참조가 null인가"를 매번 비교하는 대신, 그냥 접근하고 널이면 나는 **SIGSEGV 트랩**으로 알아챌 수 있다(`ImplicitNullChecks`, OpenJDK `globals.hpp`).
- JVM의 SIGSEGV 핸들러가 그 주소가 자기가 심어 둔 널 검사 지점인지 확인하고, 맞으면 `NullPointerException`을 던진다.
- 그래서 같은 SIGSEGV라도 JVM이 아는 지점이면 예외, 모르는 네이티브 코드면 치명 오류(8번)다.

### 10. 원고의 두 값

- "32비트면 2 GB 커널 / 2 GB 유저": 리눅스 x86-32 기본이 아니다. 기본은 **3 GB 유저 / 1 GB 커널**이다(arch/x86/Kconfig `default VMSPLIT_3G`). 2G/2G는 선택 가능한 설정 중 하나다.
- "스택 기본 1 MB": **Windows 링커의 기본값**이다(MSVC `/STACK` 문서). 리눅스 메인 스레드 스택 한도는 `RLIMIT_STACK`(`ulimit -s`, 이 환경 8192 KB)이고, 새 pthread의 기본 스택은 **프로그램 시작 때의** 이 값을 따른다(무제한이면 아키텍처 기본값, 대부분 2 MB — pthread_create(3)). JVM 스레드는 `-Xss`(리눅스 x86-64 기본 1024 KB, OpenJDK `globals_linux_x86.hpp`)다.
