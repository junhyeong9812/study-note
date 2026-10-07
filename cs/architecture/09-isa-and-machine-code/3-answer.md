# architecture/09-isa-and-machine-code — 정답

## 정답

### 1. ISA = 소프트웨어와 CPU 사이의 계약

- ISA는 "어떤 바이트가 어떤 명령인가, 레지스터는 무엇인가, 메모리는 어떻게 읽나"를 정한다. 컴파일러는 이 계약대로 기계어를 만들고, CPU는 이 계약대로 해독한다.
- 마이크로아키텍처는 그 계약을 지키는 회로 설계다. 파이프라인·캐시·분기 예측기가 여기에 든다. 같은 ISA라도 설계가 다르면 속도가 다르다.
- 이 호스트 i7-13700HX는 x86-64 코어를 두 종류 섞는다. `lscpu -e`에서 최대 클록이 P 코어 4.8GHz(그중 2코어는 5.0GHz), E 코어 3.7GHz다. [18번](../18-pipelining-and-branch-prediction/2-summary.md) 실험에서 같은 바이너리가 E 코어(`taskset -c 20`)에서 더 느렸다.

### 2. `big`의 두 ISA 기계어

```text
  x86-64:  f3 0f 1e fa            endbr64                     (간접 분기 보호 표식, 덧셈과 무관)
           48 8d 87 78 56 34 12   lea 0x12345678(%rdi),%rax   (7바이트, 상수 통째로)
           c3                     ret
  ARM64:   528acf08  mov  w8, #0x5678
           72a24688  movk w8, #0x1234, lsl #16                 (상수를 16비트씩 둘로)
           8b080000  add x0, x0, x8
           d65f03c0  ret                                       (명령 4개 × 4바이트)
```

- x86-64는 가변 길이라 4바이트 상수를 한 명령 안에 넣는다(`78 56 34 12` = 리틀 엔디안).
- ARM64는 이 출력에서 명령마다 4바이트다. 4바이트 안에 opcode·레지스터와 32비트 상수를 함께 담을 수 없으니 `mov`+`movk`로 나눈다.
- 대가의 교환: 가변 길이는 코드가 작고 해독이 어렵다. 고정 길이는 해독이 쉽고 명령 수가 늘 수 있다.

### 3. `exit7-arm64` 실행 결과

```text
  ① bash:   bash: line 1: ./exit7-arm64: cannot execute binary file: Exec format error   → 126
  ② docker: exec /w/exit7-arm64: exec format error                                     → 255
```

- 둘 다 커널 `execve`가 `ENOEXEC`(errno 8)을 돌려준 결과다. Python `os.execv`로 부르면 `OSError 8 ENOEXEC 'Exec format error'`가 그대로 보인다.
- 126은 bash의 "실행할 수 없음" 코드다. 255는 이 Docker 29.1.3에서 관찰한 값이다.
- 대조군 `exit7-amd64`는 두 경우 모두 7로 끝났다.

### 4. ELF 헤더에서 아키텍처 읽기

```text
  7f 45 4c 46 | 02 | 01 | 01 ...      0x12: b7 00
  \x7fELF 매직  64비트  리틀엔디안       e_machine = 0x00b7 = 183 = EM_AARCH64
```

- 오프셋 0x12의 2바이트 `e_machine`이 아키텍처다. 리틀 엔디안이라 `b7 00`은 0x00b7이다. `/usr/include/elf.h`에서 183은 `EM_AARCH64`, 62(`3e 00`)는 `EM_X86_64`다.
- `file`은 매직으로 ELF임을 알고, 이 필드를 읽어 `ARM aarch64`라고 출력한다.

### 5. 커널의 거절과 에뮬레이션

- 커널 `search_binary_handler`(`fs/exec.c`)가 등록된 형식 처리기 목록을 앞에서부터 시도한다(`binfmt_misc`가 목록 맨 앞). `binfmt_elf`는 `elf_check_arch`에서 아키텍처가 다르면 `-ENOEXEC`를 낸다. 끝까지 맡을 처리기가 없으면 `ENOEXEC`다.
- `binfmt_misc`에 QEMU 규칙(AArch64 ELF 매직 → `qemu-aarch64`)이 등록돼 있으면 그 처리기가 받아 QEMU로 실행한다. 리눅스 호스트에서는 `tonistiigi/binfmt` 이미지가 QEMU를 설치하고 이 규칙을 등록한다. Docker Desktop은 자기 VM에 들어 있는 QEMU를 쓴다(Docker 문서). Apple Silicon에서는 설정("Use Rosetta for x86_64/amd64 emulation on Apple Silicon")에 따라 amd64 에뮬레이션에 Rosetta를 쓸 수도 있다(Docker Desktop Settings 문서 <https://docs.docker.com/desktop/settings-and-maintenance/settings/>).
- 대가는 속도다. QEMU가 남의 ISA 명령을 번역해 돌린다. Docker 문서는 "much slower ... especially for compute-heavy tasks like compilation and compression"이라고 적는다. 이 환경엔 QEMU가 없어 배수를 재지 못했다.

### 6. `Illegal instruction`, exit 132

- exit 132 = 128 + 4(`SIGILL`). CPU가 모르는 명령을 만나 #UD 예외 → 커널이 `SIGILL`을 보냈다.
- 원인 후보: `-march=native`나 `x86-64-v4`로 빌드해 AVX-512 같은 확장을 썼다. 실험에서 `vpxorq %zmm0,...` 한 줄로 이 호스트(AVX-512 없음)가 그대로 죽었다.
- 확인: `objdump -d bin | grep zmm` 같은 명령 검색, 대상의 `grep -o -w avx512f /proc/cpuinfo`, `/lib64/ld-linux-x86-64.so.2 --help | grep x86-64-v`.
- 재발 방지: 배포 빌드는 공통 최소 수준(예: `-march=x86-64-v2`)으로 하고, 빠른 경로는 실행 시 CPU 기능을 검사해 고른다.
- JVM은 시작할 때 CPU 기능을 감지해 JIT가 쓸 명령을 정한다. 이 호스트 컨테이너에서 `UseAVX=2`, `UseSSE=4`였다. 그래서 같은 바이트코드가 CPU마다 맞는 기계어가 된다.

### 7. Java 이식성의 경계

- 바이트코드(.class)는 아키텍처 중립이다. JVM 자신(`java` 실행 파일, `e_machine`=0x3e)과 JNI `.so`는 특정 ISA의 기계어다.
- 앞 문구 `cannot open shared object file: No such file or directory`는 glibc `dlopen`의 오류다. 파일이 있어도 이렇게 나왔다(실험).
- 괄호 안 `(Possible cause: can't load AARCH64 .so on a AMD 64 platform)`은 HotSpot이 ELF 헤더 `e_machine`을 직접 읽어 붙인 진단이다(`os_linux.cpp`). 이쪽이 진짜 원인을 말한다.
- ARM64 서버라면 방향이 반대로 `can't load AMD 64 .so on a AARCH64 platform`이 된다. jar 안 `.so` 목록을 보고 ARM64판 의존성으로 바꾼다.

### 8. 괄호의 의미 — 장난감 ISA vs x86-64

- `mov (%rdi),%rax`는 `rdi`에 든 주소에서 8바이트를 **한 번** 읽어 `rax`에 넣는다(실험 `add_mem`). 레지스터 간접 주소 지정이다.
- 원고의 `[0x02]`는 그 책이 설계해 보이는 장난감 CPU(원고 §9의 "8비트 컴퓨터")가 정한 "간접 주소 방식"이다. 주소 → 그 안의 주소 → 데이터로 두 번 읽는다.
- ISA마다 문법과 뜻이 다르다. 그래서 어셈블리를 읽을 때는 먼저 어느 ISA·어느 문법(AT&T `(%rdi)` / Intel `[rdi]`)인지 확인한다.

### 9. 맥북 빌드 → x86-64 노드 `CrashLoopBackOff`

- 컨테이너 로그(`kubectl logs --previous`)에 `exec /app/...: exec format error` 한 줄이 있으면 아키텍처 불일치다. 이 줄은 런타임이 컨테이너 stderr로 쓴 것이라 로그에 남는다(Docker에서 `-a stderr` 재실험으로 확인). `kubectl describe pod`의 상태·이벤트(재시작 횟수, `CrashLoopBackOff`)도 함께 본다. 애플리케이션 로그가 한 줄도 없이 즉시 죽는 것도 신호다.
- 확인 명령
  - `docker image inspect --format '{{.Os}}/{{.Architecture}}' myimg` → `linux/arm64`면 범인
  - `file /app/server`(이미지 안 바이너리) → `ARM aarch64`
  - 노드에서 `uname -m` → `x86_64`
- 고침: `docker buildx build --platform linux/amd64`(또는 `linux/amd64,linux/arm64` 다중 플랫폼)로 다시 빌드한다. 가능하면 대상 아키텍처의 네이티브 빌드 노드나 교차 컴파일을 쓴다(에뮬레이션 빌드는 느리다).
