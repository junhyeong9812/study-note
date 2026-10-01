# os/09-address-space — 프로세스마다 주어지는 가짜 메모리 지도, 가상 주소 공간 — 정리 (힌트)

## 해결하는 문제

기초는 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §4(가상 주소 공간과 4개 세그먼트)·§6(가상 메모리)·§7(MMU)·§13(세그먼테이션과 페이징)에 있다.\
요약: 프로세스는 자기만의 주소 공간을 가진 것처럼 코드·데이터·힙·스택을 배치하고, 하드웨어(MMU)가 그 주소를 실제 메모리 주소로 바꾼다.

가상 주소 공간이 없으면 세 가지가 안 된다(OSTEP 13).

```text
  목표          없으면 생기는 일
  투명성         프로그램마다 "메모리 몇 번지부터 써도 되는지"를 알아야 한다
  보호·격리       한 프로그램의 버그가 다른 프로그램·커널의 메모리를 덮어쓴다
  효율          격리를 소프트웨어로 매 접근마다 검사하면 너무 느리다
```

쉬운 예: 아파트 호수다.
- 모든 집의 방 번호는 "1번 방, 2번 방"으로 같다. 집 안 사람은 자기 집 번호만 쓴다.
- 관리실(MMU)이 "302호의 1번 방 = 건물 전체의 몇 번째 방"으로 바꿔 준다.
- 남의 집 방 번호를 부르면 관리실이 막는다.

똑같은 구조다.\
프로세스가 쓰는 모든 주소는 가상 주소다. 실제 위치로 바꾸는 일과 막는 일은 하드웨어와 커널이 한다.

실무 예:
- C·네이티브 모듈에서 널 포인터를 읽어 컨테이너가 `exit 139`로 죽는다.
- 해제한 메모리를 읽었는데 죽지 않고 이상한 값이 나온다. 몇 시간 뒤 전혀 다른 곳에서 크래시가 난다.

## 동작·원리

### 리눅스 x86-64 프로세스의 실제 지도

로컬에서 `/proc/<pid>/maps`로 본 모습이다(예시, 리눅스 7.0, 공유 라이브러리 줄은 생략).

```text
  높은 주소
  ffffffffff600000  --xp  [vsyscall]            (레거시 호환 페이지)
  ---------------- 커널 공간 (유저는 접근 불가) ----------------
  ~0000800000000000 ~ ffff7fffffffffff : 쓸 수 없는 비정규(non-canonical) 구멍
  ---------------- 유저 공간 끝 (00007fffffffefff) ------------
  7ffdbfebe000      rw-p  [stack]      <- 메인 스레드 스택, 아래로 자란다
  76cef13c0000      r-xp  [vdso]       <- 커널이 넣어 준 빠른 시스템 콜 코드
  76cef1299000      rw-p  (익명)       <- malloc(1 MB) → mmap 영역
        ...               libc.so, ld.so (mmap 영역, 아래로 쌓인다)
  59289b38f000      rw-p  [heap]       <- brk 힙, 위로 자란다. malloc(64)이 여기
  59285ebcf000      rw-p  ./layout     <- .data(g_init) + .bss(g_zero)
  59285ebcd000      r--p  ./layout     <- .rodata(문자열 상수)
  59285ebcc000      r-xp  ./layout     <- .text(main)
  (0 ~ 0x10000 미만) 매핑 금지 영역 (vm.mmap_min_addr = 65536)
  낮은 주소
```

- 유저 공간은 4단계 페이지 테이블에서 약 128 TB(`0` ~ `00007fffffffefff`)다. 커널은 위쪽 절반에 있고, 사이는 쓸 수 없는 구멍이다(Documentation/arch/x86/x86_64/mm.rst).
- 5단계 페이지 테이블(57비트 가상 주소)을 쓰면 유저 공간이 약 64 PB로 512배 커진다(같은 문서 "48- and 57-bit virtual addresses").
- **힙(brk)은 위로, 스택은 아래로** 자란다. 큰 `malloc`·공유 라이브러리·스레드 스택은 그 사이 mmap 영역에 놓인다.
- glibc `malloc`은 기본적으로 128 KB 이상 요청을 `mmap`으로 받는다. 이 문턱은 동적으로 오른다(mallopt(3) `M_MMAP_THRESHOLD`). 문턱 이상이어도 기존 빈 청크로 채울 수 있으면 그쪽을 쓰고, 메인 스레드가 아닌 스레드의 작은 요청은 `mmap`으로 만든 별도 arena에서 나올 수 있다(glibc `malloc/arena.c`). 위 예(메인 스레드)에서 64바이트는 `[heap]`, 1 MB는 익명 mmap 영역에 있었다.
- 주소가 매번 다른 것은 ASLR이다. `randomize_va_space = 2`면 스택·mmap·vDSO·힙까지 무작위 배치한다(proc_sys_kernel(5)).

  - *VMA(가상 메모리 영역)*: `maps`의 한 줄이다. 시작·끝 주소, 권한(`rwxp`), 원본 파일로 이뤄진 연속 구간이다.
  - *익명 매핑*: 파일 없이 0으로 채워진 메모리다. 힙·스택·큰 `malloc`이 여기에 속한다.

**실행 파일 → 세그먼트.** `size`의 text·data·bss가 위 지도의 앞부분이다.

```text
  $ size layout                   $ readelf -lW layout  (마지막 LOAD)
     text  data  bss               FileSiz 0x2c0   MemSiz 0x2d0   RW
     3773   704   16                          └── 0x10 = 16바이트 = .bss
```

- `.bss`는 파일에 크기만 적혀 있다. 적재 때 0으로 채운 메모리로 만든다(`MemSiz − FileSiz`). 원고 §4의 설명과 같다.
  - 이 차이는 세그먼트 끝의 "0으로 채울 전체 크기"라 정렬 패딩이 끼면 `.bss`보다 클 수 있다. 이 예에서는 16으로 같았다. `.bss` 자체 크기는 `readelf -SW`의 섹션 크기로 본다(elf(5)).

> 참고: 원고 §4의 "32비트면 4GB 중 2GB 커널, 2GB 유저"는 한 설정의 예다. 리눅스 x86-32 커널의 기본은 3GB 유저 / 1GB 커널이다(arch/x86/Kconfig `default VMSPLIT_3G`).\
> 참고: 원고 §4의 "스택 프레임 기본 1MB"는 Windows 링커의 기본값이다(MSVC `/STACK` 문서 "default stack size is 1 MB"). 리눅스 메인 스레드 스택 한도는 `RLIMIT_STACK`(`ulimit -s`, 이 환경 8192 KB)이다. JVM 스레드는 `-Xss`(리눅스 x86-64 기본 1024 KB)다.

### 가장 단순한 변환 — 베이스/바운드

```text
  CPU가 낸 가상 주소 va
        |
        v
   va < bounds ? --- 아니오 ---> 예외 → 커널 → 프로세스 종료(SIGSEGV)
        | 예
        v
   물리 주소 = va + base
```

- 프로세스마다 `base`(시작 위치)와 `bounds`(크기) 두 값만 둔다. 컨텍스트 스위칭 때 커널이 이 두 레지스터를 바꾼다(OSTEP 15, dynamic relocation).
- 문제: 주소 공간 전체를 연속으로 잡아야 한다. 힙과 스택 사이의 빈 공간까지 물리 메모리를 차지한다.

### 세그먼테이션 — 영역마다 베이스/바운드

```text
  세그먼트   base    size   자라는 방향   권한
  code      32 KB   2 KB   +            r-x
  heap      34 KB   3 KB   +            rw-
  stack     28 KB   2 KB   -  (아래로)    rw-
                  (base·size는 OSTEP 16의 예시 값, 방향·권한 열은 같은 장 뒤쪽 표를 합친 것)
```

- 코드·힙·스택마다 베이스/바운드를 따로 둔다. 빈 공간은 물리 메모리를 쓰지 않는다(OSTEP 16).
- 세그먼트별 권한 비트로 코드를 읽기 전용으로 만들고 공유할 수 있다.
- **"세그멘테이션 폴트"라는 이름이 여기서 왔다.** 세그먼트 밖 주소 접근을 가리키던 말이다(OSTEP 16). 지금 리눅스에서는 페이지 단위 검사로 나는 SIGSEGV를 여전히 이렇게 부른다.
- 문제: 세그먼트 크기가 제각각이라 물리 메모리에 구멍이 생긴다(외부 단편화). 그래서 고정 크기로 쪼개는 페이징이 이어진다(10번).
- x86-64 리눅스는 세그먼트 베이스를 사실상 0으로 둔 평면(flat) 모델이다. FS·GS 레지스터의 베이스만 실제로 쓰인다. 유저 공간 TLS는 보통 FS를 쓴다(arch_prctl(2) `ARCH_SET_FS`). 유저 GS는 정해진 용도가 없고, 커널은 GS를 CPU별 데이터에 쓴다(Documentation/arch/x86/x86_64/fsgs.rst).

### 리눅스가 주소 하나를 판정하는 법

```text
  접근한 주소 addr
     |
     v
  addr가 속한 VMA가 있나? ---- 없음 ----> 스택 VMA 바로 아래면 스택을 늘려 처리(한도 안)
     |                                    그 밖이면 SIGSEGV (si_code = SEGV_MAPERR)
     | 있음
     v
  VMA 권한이 이 접근(읽기/쓰기/실행)을 허용하나? ---- 아니오 ----> SIGSEGV (SEGV_ACCERR)
     | 예
     v
  페이지 테이블에 실제 페이지가 있나? ---- 없음 ----> 페이지 폴트 처리(0 페이지 할당·파일 읽기) 후 재실행
     | 있음                                        (10번 요구 페이징. 실패 경로도 있다:
     |                                             파일 끝을 넘은 파일 매핑 접근 → SIGBUS, mmap(2))
     v
  접근 성공
```

- `SEGV_MAPERR`는 "매핑되지 않은 주소", `SEGV_ACCERR`는 "매핑됐지만 권한 없음"이다(sigaction(2)).
- 그림은 흔한 경우다. VMA와 권한이 있어도 SIGSEGV가 나는 예외가 있다: 리눅스 6.13+의 경량 가드(`madvise(MADV_GUARD_INSTALL)`, 로컬 재현에서 `SEGV_MAPERR`), x86 보호 키 위반(`SEGV_PKUERR`, pkeys(7)).
- 로컬 재현(예시, 리눅스 7.0)
  - `*(int *)NULL` 읽기 → `SIGSEGV addr=(nil) code=SEGV_MAPERR`, 종료 코드 139.
  - 문자열 상수(`.rodata`, `r--p`)에 쓰기 → `SEGV_ACCERR`, 139.
- 0번지 근처가 보통 비어 있는 이유: `vm.mmap_min_addr`(이 환경 65536) 아래는 `CAP_SYS_RAWIO`가 없는 프로세스가 매핑할 수 없다(security/commoncap.c `cap_mmap_addr`, Documentation/admin-guide/sysctl/vm.rst). 그래서 널 포인터와 작은 오프셋(`p->field`) 접근은 매핑 없는 주소가 된다.

## 쓰이는 자료구조·알고리즘

- **베이스/바운드 레지스터 쌍** — 덧셈 한 번과 비교 한 번으로 변환과 보호를 동시에 한다(OSTEP 15).
- **세그먼트 테이블** — 세그먼트 번호로 인덱싱하는 (base, size, 방향, 권한) 배열이다(OSTEP 16).
- **VMA 트리 = 메이플 트리(B-tree 계열)** — 리눅스 6.1부터 프로세스의 VMA들을 `mm_struct`의 `mm_mt`(maple tree)에 둔다(include/linux/mm_types.h). 메이플 트리는 겹치지 않는 구간을 저장하도록 최적화한 B-tree다(Documentation/core-api/maple_tree.rst). 폴트마다 "이 주소가 어느 VMA인가"를 로그 시간에 찾는다. [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md) · [data-structure/30-interval-tree](../../data-structure/30-interval-tree/2-summary.md)
- **스택** — 스택 세그먼트는 함수 호출 스택 그대로다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md) · [systems/call-stack](../../systems/call-stack/README.md)

## 적용 — 풀어나가는 법

### 1. 주소 공간을 읽는다

```bash
cat /proc/<pid>/maps                 # VMA 목록: 주소 범위, 권한, 파일
pmap -x <pid>                        # VMA별 크기·RSS
grep -E 'VmSize|VmRSS|VmStk|VmData' /proc/<pid>/status
size ./app                           # text / data / bss 크기
readelf -lW ./app                    # 적재할 세그먼트(LOAD)와 권한
ulimit -s                            # 메인 스레드 스택 한도 (KB)
cat /proc/sys/vm/mmap_min_addr /proc/sys/kernel/randomize_va_space
```

- `VmSize`(가상 크기)가 커도 놀라지 않는다. 예약만 한 영역(JVM 힙, 스레드 스택)이 포함된다. 실제 사용은 `VmRSS`·`smaps_rollup`의 PSS로 본다.

### 2. SIGSEGV 원인 주소를 잡는다 — C

```c
#include <signal.h>
#include <unistd.h>
#include <stdio.h>

static void on_segv(int sig, siginfo_t *si, void *ctx) {
    char buf[96];
    int n = snprintf(buf, sizeof buf, "SIGSEGV at %p (%s)\n", si->si_addr,
                     si->si_code == SEGV_MAPERR ? "unmapped" : "no permission");
    write(2, buf, n);   /* write는 async-signal-safe. snprintf는 목록에 없다 — 진단용 타협 */
    _exit(139);         /* 주의: 이건 시그널 사망이 아니라 exit(139)다. wait로 보면 WIFEXITED */
}

int main(void) {
    struct sigaction sa = {0};
    sa.sa_sigaction = on_segv;
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, NULL);
    /* ... */
}
```

- 운영에서는 핸들러보다 코어 덤프가 낫다. 이 환경의 `core_pattern`은 apport로 넘긴다. systemd 환경이면 `coredumpctl`로 찾는다.
- 크래시 주소 `si_addr`가 0 근처면 널 포인터, 스택 한도 근처면 스택 오버플로다.

### 3. Java·Node에서는 어떻게 보이나

- Java의 `null` 필드 접근은 보통 프로세스를 죽이지 않는다. HotSpot은 컴파일한 코드에서 널 검사를 SIGSEGV 트랩으로 대신할 수 있다(`ImplicitNullChecks`, OpenJDK `globals.hpp`). 트랩을 `NullPointerException`으로 바꿔 던진다.
- 같은 SIGSEGV라도 JNI·네이티브 라이브러리 안에서 나면 JVM은 `hs_err_pid<pid>.log`를 남기고 `abort()`한다(`CreateCoredumpOnCrash` 기본 true → `os::abort` → `::abort()`, OpenJDK `os_posix.cpp`). 이때 종료 코드는 SIGABRT의 134다.
- Node의 `undefined` 접근은 `TypeError` 예외다. 네이티브 애드온 크래시는 SIGSEGV(139)로 끝난다.
- 깊은 재귀: Java는 `StackOverflowError`, Node는 `RangeError: Maximum call stack size exceeded`로 잡힌다. C는 스택 끝의 가드 영역을 건드려 SIGSEGV로 죽는다.

## 장애 시나리오와 대처

### 1. 널 포인터 역참조 → `SIGSEGV`, `exit 139`

- **현상**: 네이티브 프로세스·사이드카가 갑자기 죽고 재시작을 반복한다.
- **보이는 형태**
  - 셸·컨테이너 종료 코드 139(`128 + 11`). 셸 메시지 `Segmentation fault (core dumped)`.
  - 커널 로그 `segfault at 0 ip … sp … error …`(`dmesg`, 이 환경은 `dmesg_restrict=1`이라 일반 사용자는 못 읽는다).
- **원인**: 주소 0 근처에는 VMA가 없다(`mmap_min_addr`). 널 포인터나 널 구조체의 필드 읽기가 `SEGV_MAPERR`가 된다.
- **대처**: 코어 덤프로 크래시 지점을 찾는다(`gdb app core`, `bt`). 널이 들어온 경로(실패한 `malloc`, 초기화 안 된 포인터)를 막는다.

### 2. 해제한 메모리 접근 — 죽을 때도, 안 죽을 때도

- **현상**: 해제 후 사용(use-after-free) 버그가 있는데 테스트에서는 멀쩡하다. 운영에서 가끔 엉뚱한 곳이 죽는다.
- **보이는 형태**
  - 로컬 재현(예시, 리눅스 7.0 · glibc 2.39)
    - `malloc(64)` → 42 저장 → `free` → 읽기: **죽지 않았다**. 값은 42가 아니라 1681751075였다. 해제된 청크가 `[heap]` VMA 안에 그대로 남아 있고, 할당기가 그 자리에 관리 정보를 썼다.
    - `malloc(1 MB)` → `free` → 읽기: **SIGSEGV `SEGV_MAPERR`**. 128 KB 이상은 `mmap`으로 받았고 `free`가 `munmap`해 VMA 자체가 사라졌다.
- **원인**: SIGSEGV는 주로 "VMA가 없거나 권한이 없을 때" 난다(위 판정 그림, 예외는 가드·보호 키). 해제는 할당기 수준의 일이라 VMA가 남아 있으면 커널은 모른다. 결과는 정의되지 않은 동작이라, 위 크기별 결과도 이 재현의 관찰일 뿐이다(병합·힙 축소·재사용으로 달라진다).
- **대처**
  - "죽지 않았다"를 "문제없다"로 읽지 않는다.
  - 테스트에서 AddressSanitizer(`-fsanitize=address`)나 Valgrind로 잡는다.
  - 해제 직후 포인터를 `NULL`로 둔다.

### 3. 스택 오버플로 → `SIGSEGV`

- **현상**: 깊은 재귀나 큰 지역 배열이 있는 함수에서 죽는다. 입력 크기에 따라 재현된다.
- **보이는 형태**: 종료 코드 139. 크래시 주소가 `[stack]` VMA 바로 아래다.
  - 로컬 재현(예시, 리눅스 7.0): 프레임마다 1 KB를 쓰는 무한 재귀가 `ulimit -s` 8192에서도, 1024에서도 139로 끝났다.
- **원인**: 스택은 `RLIMIT_STACK` 이상 자랄 수 없다. glibc가 기본 속성으로 할당한 스레드 스택은 끝에 가드 페이지가 있다(07번 로컬 확인: 8 MiB + 4 KiB 간격). `pthread_attr_setguardsize(0)`이나 직접 준 스택(`pthread_attr_setstack`)에는 없다(pthread_attr_setguardsize(3)).
- **대처**
  - 재귀를 반복문·명시적 스택으로 바꾼다.
  - 큰 배열은 힙에 둔다.
  - 꼭 필요하면 `ulimit -s`나 `pthread_attr_setstacksize`, JVM `-Xss`를 늘린다.

### 4. 읽기 전용 영역에 쓰기 → `SEGV_ACCERR`

- **현상**: 문자열 상수를 고치는 C 코드가 어떤 환경에서만 죽는다.
- **보이는 형태**: `si_code = SEGV_ACCERR`. 크래시 주소가 `maps`의 `r--p`(.rodata) 또는 `r-xp`(.text) 구간이다.
- **원인**: 문자열 리터럴은 읽기 전용 VMA에 놓인다. 쓰기는 권한 위반이다.
- **대처**: 고칠 문자열은 `char buf[] = "…"`(스택 복사)나 `strdup`(힙)으로 만든다.

### 5. JVM이 `hs_err_pid*.log`를 남기고 죽음

- **현상**: Java 서비스가 예외 로그 없이 죽고 작업 디렉터리에 `hs_err_pid<pid>.log`가 생긴다.
- **보이는 형태**: 종료 코드 134(SIGABRT). 로그 앞부분에 `SIGSEGV`와 `Problematic frame:`이 적힌다.
- **원인**: 흔한 것은 JNI·네이티브 라이브러리(압축, 암호, DB 드라이버)의 메모리 오류다. JVM이 자기 트랩으로 처리할 수 없는 SIGSEGV라 치명 오류로 끝낸다(OpenJDK `vmError.cpp` → `os::abort`). 다만 `hs_err`는 JVM 자체 버그, JIT가 만든 코드, 네이티브 메모리 할당 실패에서도 생긴다(Oracle "Troubleshoot System Crashes").
- **대처**: `Problematic frame`은 오류가 드러난 지점이지 원인 확정이 아니다. 앞선 메모리 손상이 다른 곳에서 드러날 수 있다. 그 라이브러리를 첫 후보로 두고 버전 올리기·교체를 검토한다. 코어 덤프를 남기도록 `ulimit -c`와 컨테이너 설정을 확인한다.

## 핵심 문장

- 프로세스가 보는 주소는 전부 가상 주소다. 목표는 투명성·보호·효율이다.
- 리눅스 x86-64 유저 공간은 약 128 TB이고, 아래부터 코드·데이터·bss·힙(위로) … mmap 영역 … 스택(아래로) 순이다. 커널은 위쪽 절반에 있다.
- 베이스/바운드 → 세그먼테이션 → 페이징 순으로 발전했다. 세그먼테이션은 빈 공간 낭비를 줄였지만 외부 단편화를 남겼다.
- 리눅스는 주소가 VMA 밖이면(스택 확장 대상이 아니면) `SEGV_MAPERR`, 권한 밖이면 `SEGV_ACCERR`로 SIGSEGV를 보낸다. 셸 종료 코드는 보통 139다.
- 해제한 메모리 접근은 VMA가 남아 있으면 죽지 않고 조용히 틀린 값을 읽는다. SIGSEGV가 없다고 안전한 것이 아니다.

## 관련 주제·근거

- 선행: [04-process-and-lifecycle](../04-process-and-lifecycle/2-summary.md). 원고 [foundations/memory-management](../../foundations/memory-management/README.md) §4·§6·§7·§13.
- 후속·연결
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) — VMA 안의 페이지를 실제로 찾는 페이지 테이블과 TLB.
  - [06-signals](../06-signals/2-summary.md) — SIGSEGV 전달, 128+N 종료 코드.
  - [07-threads-and-context-switch](../07-threads-and-context-switch/2-summary.md) — 스레드 스택과 가드 페이지.
  - [11-heap-allocation](../11-heap-allocation/2-summary.md) — malloc·mmap 문턱, free list.
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 파일 매핑.
  - [29-linking-and-loading](../29-linking-and-loading/2-summary.md) — ELF 적재·PIE.
  - [architecture/README](../../architecture/README.md) — `10-calling-convention-and-stack-frame`.
- Kernel 문서·소스
  - Documentation/arch/x86/x86_64/mm.rst — 4단계 유저 공간 `0000000000000000 - 00007fffffffefff` ~128 TB, 비정규 구멍 `0000800000000000 - ffff7fffffffffff`, 5단계(57비트) ~64 PB
  - security/commoncap.c `cap_mmap_addr()` — `mmap_min_addr` 아래는 `CAP_SYS_RAWIO` 필요 · Documentation/admin-guide/sysctl/vm.rst `mmap_min_addr` <https://docs.kernel.org/arch/x86/x86_64/mm.html>
  - arch/x86/Kconfig — `default VMSPLIT_3G`(x86-32)
  - include/linux/mm_types.h — `struct maple_tree mm_mt` · Documentation/core-api/maple_tree.rst
- Documentation/arch/x86/x86_64/fsgs.rst — FS는 보통 TLS, 유저 GS는 공통 용도 없음 <https://docs.kernel.org/arch/x86/x86_64/fsgs.html> · mm/mmap.c `expand_stack()`(스택 VMA 아래 접근 시 확장)
- glibc 2.42 `nptl/allocatestack.c` `setup_stack_prot()` — `MADV_GUARD_INSTALL` 우선, 실패 시 `PROT_NONE` 폴백(2.41까지는 `PROT_NONE`만)
- Linux man-pages 6.7(로컬): madvise(2) `MADV_GUARD_INSTALL`(리눅스 6.13+) · pkeys(7) · mmap(2) SIGBUS · elf(5) · pthread_attr_setguardsize(3) · proc_pid_maps(5) · sigaction(2) `SEGV_MAPERR`·`SEGV_ACCERR`·`SEGV_PKUERR` · mallopt(3) `M_MMAP_THRESHOLD`(128 KB, 동적 조정) · proc_sys_kernel(5) `randomize_va_space` · arch_prctl(2)
- Oracle "Troubleshoot System Crashes" — `hs_err`가 생기는 여러 원인 <https://docs.oracle.com/en/java/javase/24/troubleshoot/troubleshoot-system-crashes.html>
- OpenJDK: `src/hotspot/share/runtime/globals.hpp`(`ImplicitNullChecks`, `CreateCoredumpOnCrash`) · `src/hotspot/os/posix/os_posix.cpp`(`os::abort` → `::abort()`) · `src/hotspot/share/utilities/vmError.cpp`
- Microsoft Learn "/STACK (Stack allocations)" — 기본 1 MB <https://learn.microsoft.com/en-us/cpp/build/reference/stack-stack-allocations>
- 교재: OSTEP 13 "The Abstraction: Address Spaces", 15 "Mechanism: Address Translation"(base and bounds), 16 "Segmentation" · CS:APP 3판 9.2 Address Spaces, 9.7.2 Linux Virtual Memory System, 9.11 Common Memory-Related Bugs in C Programs
- 로컬 재현(리눅스 7.0 · glibc 2.39 · gcc 13.3): `/proc/self/maps` 배치, `size`·`readelf`의 bss, 널 역참조 `SEGV_MAPERR`, `.rodata` 쓰기 `SEGV_ACCERR`, 작은/큰 블록 use-after-free 차이, 재귀 스택 오버플로 139, `MADV_GUARD_INSTALL` 가드 접근 → `SEGV_MAPERR`
