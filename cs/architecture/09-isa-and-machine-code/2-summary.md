# architecture/09-isa-and-machine-code — ISA와 기계어: 같은 C 한 줄이 CPU마다 다른 바이트가 된다 — 정리 (힌트)

## 해결하는 문제

CPU는 소스 코드를 모른다. 메모리에 놓인 **바이트열**을 명령으로 해석해 실행할 뿐이다.

```text
  long add(long a, long b) { return a + b; }
          │ 컴파일러
          ▼
  x86-64 CPU가 읽는 바이트   48 8d 04 37 c3          (lea + ret)
  ARM64  CPU가 읽는 바이트   20 00 00 8b c0 03 5f d6 (add + ret, 리틀 엔디안 저장)
          │
          ▼
  같은 뜻, 다른 바이트. 서로의 바이트를 주면 같은 함수로 실행되지 않는다
  (다른 명령으로 풀리거나 예외 — ARM64 바이트 `20 00`을 x86-64로 풀면 `and %al,(%rax)`, objdump 확인).
```

- 어떤 바이트가 어떤 명령인지, 레지스터가 몇 개인지를 정한 약속이 필요하다. 그 약속이 ISA다.
  - *ISA(Instruction Set Architecture, 명령어 집합 구조)*: 소프트웨어가 볼 수 있는 CPU의 계약. 명령어 목록과 인코딩, 레지스터, 메모리 접근 방식을 정한다.
  - *기계어(machine code)*: ISA가 정한 형식의 바이트열. CPU가 직접 실행한다.
  - *어셈블리(assembly)*: 기계어를 사람이 읽게 1:1에 가깝게 옮긴 글자 표기(`add x0, x1, x0`).

쉬운 예: 전기 플러그다.
- 한국 콘센트(220V, 둥근 핀)에 맞춘 가전은 미국 콘센트에 바로 꽂히지 않는다.
- 변환 어댑터를 끼우면 쓰지만, 그만큼 손실과 번거로움이 있다.

똑같은 구조다.\
ISA가 콘센트 규격이고, 실행 파일은 한 규격에 맞춰 만든 가전이다. 어댑터에 해당하는 것이 에뮬레이터(QEMU)·번역기(Rosetta)다.

실무 예:
- Apple Silicon(ARM64) 노트북에서 만든 컨테이너 이미지를 x86-64 서버에서 띄우면 `exec /app: exec format error`로 바로 죽는다.
- 같은 이미지를 에뮬레이션으로 돌리거나 빌드하면 된다. 다만 크게 느려질 수 있다(Docker 문서: "much slower", 특히 컴파일·압축).
- 순수 Java 코드는 그 클래스 파일 버전을 지원하는 JVM이 있는 곳이면 아키텍처와 무관하게 돌지만(낮은 버전 JVM은 `UnsupportedClassVersionError` — JVMS §4.1·§5.3.5), JNI 네이티브 라이브러리(`.so`)가 섞이면 `UnsatisfiedLinkError`가 난다.

## 동작·원리

### 1. 소스에서 CPU까지 — 어디에 아키텍처가 박히나

```text
  소스(.c)  ──gcc/clang──▶  어셈블리(.s)  ──어셈블러──▶  기계어 + ELF 헤더(실행 파일)
                                                          │  e_machine = 62(x86-64) / 183(AArch64)
                                                          ▼
                                   커널 execve ── 헤더 검사 ──▶ CPU가 바이트를 해독(decode)·실행
  Java:  소스 ──javac──▶ 바이트코드(.class, 아키텍처 중립)
                          └─ JVM(그 자체는 네이티브 실행 파일)이 해석 실행하다가, HotSpot 기본 설정이면
                             자주 도는 코드를 그 CPU용 기계어로 JIT 컴파일(`-Xint`면 해석만)
```

- 아키텍처는 **컴파일할 때** 정해진다. 실행 파일 헤더에 그 기록이 남는다.
- 기초(CPU 구성·IR·PC·버스·장난감 명령어 `LOAD`/`STORE`·`C = A + B` 어셈블리)는 원고 [hardware-basics](../../foundations/hardware-basics/README.md) §3·§7·§8·§9·§10에 있다. 여기서는 실제 ISA 두 개(x86-64, ARM64)로 넘어간다.
  - *ISA vs 마이크로아키텍처*: ISA는 계약, *마이크로아키텍처(microarchitecture)*는 그 계약을 지키는 회로 설계다. 파이프라인 깊이, 캐시, 분기 예측기가 여기에 속한다([18](../18-pipelining-and-branch-prediction/2-summary.md)·[19](../19-out-of-order-and-speculation/2-summary.md)).
    - 흔한 오해: 같은 ISA면 성능도 같다. 이 실험 호스트 i7-13700HX는 x86-64 코어 두 종류(`lscpu -e` 최대 클록: P 코어 4.8GHz, 그중 2코어는 5.0GHz · E 코어 3.7GHz)를 섞어 쓴다. 같은 바이너리가 어느 코어에 올라가느냐로 속도가 다르다([18](../18-pipelining-and-branch-prediction/2-summary.md) 실험).

### 2. 같은 함수, 두 ISA의 기계어

```c
long add(long a, long b)      { return a + b; }
long add_mem(long *p, long b) { return *p + b; }
long big(long a)              { return a + 0x12345678; }
```

(실험, Ubuntu 24.04 · gcc 13.3.0 `-O2` · clang 18.1.3 `--target=aarch64-linux-gnu -O2` · objdump 2.42 / llvm-objdump 18, 2026-10-07)

```text
  x86-64 (gcc -O2)                              ARM64 (clang -O2)
  add:     f3 0f 1e fa   endbr64                add:     8b000020  add x0, x1, x0
           48 8d 04 37   lea (%rdi,%rsi,1),%rax          d65f03c0  ret
           c3            ret
  add_mem: f3 0f 1e fa   endbr64                add_mem: f9400008  ldr x8, [x0]
           48 8b 07      mov (%rdi),%rax
           48 01 f0      add %rsi,%rax                   8b010100  add x0, x8, x1
           c3            ret                             d65f03c0  ret
  big:     f3 0f 1e fa   endbr64                big:     528acf08  mov  w8, #0x5678
           48 8d 87 78 56 34 12                          72a24688  movk w8, #0x1234, lsl #16
                         lea 0x12345678(%rdi),%rax       8b080000  add x0, x0, x8
           c3            ret                             d65f03c0  ret
  (함수 사이 정렬용 nop 채움은 생략)
```

- **길이**: x86-64 명령은 길이가 제각각이다(이 출력에서 1~7바이트). ARM64(A64) 명령은 이 출력에서 하나같이 4바이트다(고정 길이 32비트 [?]).
  - *가변 길이 인코딩*: 자주 쓰는 명령을 짧게 만들어 코드 크기를 줄인다. 대신 해독기는 "다음 명령이 어디서 시작하나"부터 풀어야 한다.
  - *고정 길이 인코딩*: 분기가 아니면 다음 명령은 +4 위치에 있다. 그래서 여러 개를 한꺼번에 해독하기 쉽다. 대신 큰 상수를 한 명령에 못 담는다.
- **상수**: `big`에서 x86-64는 4바이트 상수(`78 56 34 12`, 리틀 엔디안)를 명령 안에 그대로 넣었다. ARM64는 32비트 명령 안에 32비트 상수를 다 담을 자리가 없다. 그래서 16비트씩 두 번(`mov` + `movk`) 나눠 실었다.
- **메모리 피연산자**: ARM64는 메모리 값을 먼저 `ldr`로 레지스터에 올리고 더했다. ARM64 산술 명령은 메모리를 피연산자로 받지 못한다(레지스터·즉시값만, load/store 구조 — `llvm-mc`로 `add x0, x1, #4`는 인코딩되고 `add x0, x1, [x2]`는 거부됨). x86-64는 산술 명령이 메모리를 직접 읽을 수 있다. [10번 실험](../10-calling-convention-and-stack-frame/2-summary.md)의 `add 0x8(%rsp),%r9d`가 그 예다.
- **`endbr64`**: Ubuntu gcc가 기본으로 켠 `-fcf-protection=full`(`gcc -Q --help=common`)이 함수 입구에 넣은 간접 분기 보호 표식이다. ISA의 일부지만 덧셈과는 무관하다.
- 레지스터도 다르다. x86-64 범용 레지스터는 `%rax`~`%r15`의 16개다(System V AMD64 ABI 3.2.1 "16 general purpose 64-bit registers"·그림 3.4 Register Usage). ARM64는 `x0`~`x30`의 31개와 SP다(AAPCS64 "General-purpose Registers" 절).

> 참고: 원고 §9의 "레지스터는 AX·BX·CX·DX로 대부분 4개가 범용"은 그 책이 설계해 보이는 장난감 CPU(원고 §9: 주소 3비트, "8비트 컴퓨터") 이야기다. x86-64는 범용 레지스터 16개, ARM64는 31개다(위 근거). 원고 §9의 "`LOAD BX, [0x02]`의 `[]` 안 주소는 데이터 주소를 담은 곳의 주소(간접)"도 그 장난감 ISA의 정의다. x86-64에서 괄호는 그 주소의 메모리를 **한 번** 읽는다. 위 `mov (%rdi),%rax`는 `rdi`가 가리키는 8바이트를 읽을 뿐이다.

### 3. 실행 파일 헤더 — 아키텍처는 18번째 바이트에 적혀 있다

같은 일(`exit(7)`)을 하는 최소 ELF 실행 파일 두 개를 직접 만들었다. 헤더 64바이트 + 프로그램 헤더 56바이트 + 명령 3개다(`mkelf.py`).

```text
  $ xxd -l 24 exit7-amd64                      $ xxd -l 24 exit7-arm64
  7f45 4c46 0201 0100 0000 ...                 7f45 4c46 0201 0100 0000 ...
  0200 3e00 0100 0000                          0200 b700 0100 0000
       ^^^^                                         ^^^^
  오프셋 0x12 e_machine = 0x003e = 62           e_machine = 0x00b7 = 183
  /usr/include/elf.h: EM_X86_64 62             EM_AARCH64 183

  $ file exit7-*
  exit7-amd64: ELF 64-bit LSB executable, x86-64, ... statically linked
  exit7-arm64: ELF 64-bit LSB executable, ARM aarch64, ... statically linked
```

- `7f 45 4c 46`는 `\x7fELF` 매직이다. `02`는 64비트, `01`은 리틀 엔디안이다.
- `file`이 아키텍처를 아는 방법이 이것이다. 헤더의 두 바이트를 읽는다.

### 4. 커널은 맞지 않는 실행 파일을 어떻게 거절하나

```text
  execve("./exit7-arm64")
     │
     ▼  fs/exec.c search_binary_handler: 등록된 형식 처리기 목록을 앞에서부터 시도
  ┌─ binfmt_misc ── 등록된 매직과 맞나? ── qemu-aarch64 규칙이 있으면 → QEMU가 대신 실행(느림)
  │   (insert_binfmt로 목록 맨 앞에 등록)     없으면 → -ENOEXEC
  ├─ binfmt_elf ── e_type이 EXEC/DYN인가? ── elf_check_arch(e_machine) ── x86-64 아님 → -ENOEXEC
  └─ binfmt_script ("#!") ─ 해당 없음 → -ENOEXEC      (elf·script는 register_binfmt로 목록 끝에 등록)
     ▼
  모두 실패 → execve가 ENOEXEC 반환 → "Exec format error"
```

- 커널 소스(`fs/binfmt_elf.c`의 `elf_check_arch`, `fs/exec.c`의 `search_binary_handler`)가 이 흐름이다. 처리기 하나가 `-ENOEXEC`를 내면 다음 처리기로 넘어간다. `binfmt_misc`는 `insert_binfmt`(목록 맨 앞)로, `binfmt_elf`·`binfmt_script`는 `register_binfmt`(목록 끝)로 등록하므로 binfmt_misc 규칙이 ELF 처리기보다 먼저 검사된다(`fs/binfmt_misc.c`, `include/linux/binfmts.h`).
- `execve(2)`: `ENOEXEC` — "An executable is not in a recognized format, is for the wrong architecture, ...".
  - *binfmt_misc*: 파일 앞부분 매직 바이트로 형식을 알아보고 지정한 해석기에 넘기는 커널 기능. Docker·QEMU의 다중 아키텍처 실행이 이것을 쓴다(커널 문서 binfmt-misc, Docker 문서).
- 이 호스트의 `/proc/sys/fs/binfmt_misc/`에는 `llvm-18-runtime.binfmt`(LLVM 비트코드, 매직 `BC`)와 `python3.12`(`.pyc`, 매직 `cb0d0d0a`) 두 규칙뿐이고 QEMU 규칙이 없다. 그래서 아래 실험이 실패한다.

(실험, 같은 호스트, 커널 7.0.0-34-generic, Docker 29.1.3, `python:3.12-slim` 이미지(linux/amd64)에 파일을 마운트해 실행)

```text
  $ ./exit7-amd64; echo $?
  7
  $ LANG=C ./exit7-arm64; echo $?
  bash: line 1: ./exit7-arm64: cannot execute binary file: Exec format error
  126
  python: os.execv('./exit7-arm64') → OSError 8 ENOEXEC 'Exec format error'

  $ docker run --rm --network none -v $PWD:/w --entrypoint /w/exit7-arm64 python:3.12-slim
  exec /w/exit7-arm64: exec format error            (docker exit 255)
  $ docker run ... --entrypoint /w/exit7-amd64 ...  (exit 7)
```

- 이 `exec ...: exec format error` 한 줄은 Docker CLI가 아니라 컨테이너의 stderr 스트림으로 나왔다(`docker run -a stderr`에서만 보이고 `-a stdout`에서는 안 보임, 같은 판 재실험). 그래서 컨테이너 로그에 남는다.
- 컨테이너도 결국 호스트 커널의 `execve`를 부른다. 컨테이너는 커널을 공유하므로 호스트 아키텍처와 맞는 코드만 돈다(Docker 문서: "you can't run a linux/amd64 container on an arm64 host (without using emulation)").
- 셸의 126은 "찾았지만 실행 못 함"이라는 bash의 종료 코드다. 컨테이너의 255는 이 Docker 판에서 관찰한 값이다.

### 5. 같은 ISA 안에서도 "확장"이 갈린다

```text
  x86-64 기준선 ─▶ x86-64-v2 ─▶ x86-64-v3(AVX2 등) ─▶ x86-64-v4(AVX-512 등)
  이 호스트(i7-13700HX):  v2 ✔  v3 ✔  v4 ✘    ← /lib64/ld-linux-x86-64.so.2 --help
     x86-64-v4
     x86-64-v3 (supported, searched)
     x86-64-v2 (supported, searched)
```

- 같은 x86-64라도 새 명령(확장)은 CPU마다 있고 없다. 없는 명령을 만나면 CPU가 *#UD*(정의되지 않은 명령) 예외를 내고, 리눅스는 `SIGILL`을 보낸다([os/01 장애 2](../../os/01-kernel-and-user-mode/2-summary.md)).

(실험, 같은 호스트 — `/proc/cpuinfo`에 `avx512f` 0개)

```text
  $ objdump -d avx512 | grep vpxorq
      10a0:  62 f1 fd 48 ef c0   vpxorq %zmm0,%zmm0,%zmm0     ← AVX-512 명령 1개
  $ ./avx512
  before
  bash: line 1: 3331587 Illegal instruction     (core dumped) ./avx512
  exit=132                                                    ← 128 + SIGILL(4)
```

- 빌드는 성공한다. 어셈블러는 그 명령을 안다. 실행하는 CPU만 모른다.
- JVM은 이 문제를 실행 중에 피한다. 시작할 때 CPU 기능을 보고 쓸 명령을 고른다. 이 컨테이너의 HotSpot은 `UseAVX = 2`, `UseSSE = 4`로 잡았다(`-XX:+PrintFlagsFinal`). 바이트코드가 이식되는 이유다.

### 6. Java가 아키텍처를 만나는 곳 — JNI 네이티브 라이브러리

```text
  app.jar ── 순수 바이트코드 ────────────────▶ 어디서나 실행(JVM이 그 CPU용으로 JIT)
         └─ libfoo.so (JNI, 특정 ISA 기계어) ─▶ System.load → dlopen → ISA가 다르면 실패
  JVM 자신: java 실행 파일 헤더 e_machine = 0x3e (이 이미지는 x86-64)
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `LoadArm.java` — ARM64용으로 만든 목적 파일·실행 파일을 `System.load`)

```text
  os.arch=amd64
  java.lang.UnsatisfiedLinkError: /w/add-arm.o: /w/add-arm.o: cannot open shared object file:
      No such file or directory (Possible cause: can't load AARCH64 .so on a AMD 64 platform)
  java.lang.UnsatisfiedLinkError: /w/add-x86.o: /w/add-x86.o: only ET_DYN and ET_EXEC can be loaded
```

- 앞부분은 `dlopen`(glibc)이 준 메시지다. 파일이 있는데도 "No such file or directory"라고 한다. 오해를 부르는 문구다.
- 괄호 안은 HotSpot이 ELF 헤더의 `e_machine`을 직접 읽어 덧붙인 진단이다(`src/hotspot/os/linux/os_linux.cpp`의 `"(Possible cause: can't load %s .so on a %s platform)"`, `EM_AARCH64` → `"AARCH64"` 표).
- 비교용 x86-64 목적 파일은 아키텍처는 맞지만 공유 라이브러리가 아니라서 다른 메시지가 났다. 실험에서는 정식 `.so` 대신 목적 파일·최소 실행 파일을 썼다. 진단은 헤더만 읽으므로 같은 경로를 탄다.

## 쓰이는 자료구조·알고리즘

- **명령어 인코딩 = 가변 길이 vs 고정 길이 부호화** — UTF-8이 문자마다 1~4바이트인 것과 같은 고민이다. 앞 바이트를 봐야 길이를 안다. 커리큘럼 04(문자 인코딩)는 [04-character-encoding-unicode](../04-character-encoding-unicode/2-summary.md)에서 다룬다.
- **명령어 해독 = 표 찾기** — opcode 바이트(와 접두어)로 동작을 고른다. 고정 길이면 비트 필드를 잘라 바로 찾는다.
- **binfmt_misc = 매직 바이트 패턴 매칭** — 오프셋·매직·마스크로 앞부분을 비교한다(커널 문서 binfmt-misc). 처리기 목록은 차례로 시도하는 연결 리스트다(`list_for_each_entry`). [data-structure/02-linked-list](../../data-structure/02-linked-list/2-summary.md)
- **다중 아키텍처 이미지 = 플랫폼 → 매니페스트 맵** — 이미지 하나가 `linux/amd64`, `linux/arm64`마다 다른 매니페스트를 가리키는 목록을 갖는다(Docker 문서 "manifest list"). 런타임이 자기 플랫폼 키로 고른다. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 증상 → 아키텍처 확인 순서

```bash
uname -m                                   # 이 머신: x86_64 / aarch64
file ./app                                 # 실행 파일: "x86-64" / "ARM aarch64"
xxd -s 0x12 -l 2 ./app                     # e_machine 두 바이트: 3e00 / b700
docker image inspect --format '{{.Os}}/{{.Architecture}}' myimg   # 이미지의 플랫폼
unzip -l app.jar | grep -E '\.(so|dylib|dll)$'                     # jar 안 네이티브 라이브러리
/lib64/ld-linux-x86-64.so.2 --help | grep x86-64-v                 # 이 CPU가 지원하는 x86-64 수준
```

- 이 호스트 출력: `x86_64`, `python:3.12-slim`·`eclipse-temurin:21-jdk` 모두 `linux/amd64`, `x86-64-v3 (supported, searched)`.

### 2. 만들 때 막는다

- 배포 대상 아키텍처를 빌드 명령에 적는다. 노트북 아키텍처가 기본값이 되지 않게 한다.

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t myimg:1.0 --push .   # 다중 플랫폼 이미지
```

- Docker 문서는 에뮬레이션(QEMU) 빌드보다 **교차 컴파일**이나 **아키텍처별 네이티브 빌드 노드**를 권한다. Java는 대개 쉽다. 바이트코드를 한 번 만들고, 베이스 이미지(JDK)만 아키텍처별로 고른다.
- C/C++·Go·Rust 바이너리는 대상마다 따로 컴파일한다. `-march=native`는 빌드 머신 CPU에 맞추므로 배포 빌드에 쓰지 않는다. 최소 수준을 명시한다(예: `-march=x86-64-v2`).

### 3. 기계어를 직접 읽는다

```bash
gcc -O2 -c f.c && objdump -d f.o                               # x86-64
clang --target=aarch64-linux-gnu -O2 -c f.c && llvm-objdump-18 -d f.o   # ARM64 (교차 컴파일, 실행은 안 함)
gcc -O2 -S f.c -o -                                            # 어셈블리만
```

- 읽는 순서: 함수 경계(`<add>:`) → 명령 길이와 바이트 → 레지스터 이름(`%rdi`·`x0`)으로 ISA 확인 → 인자가 어느 레지스터로 오는지([10번](../10-calling-convention-and-stack-frame/2-summary.md)).

## 장애 시나리오와 대처

### 1. 배포한 컨테이너가 바로 죽는다 — `exec format error`

- **현상**: 새 이미지로 바꾸자 파드·컨테이너가 시작 즉시 종료하고 재시작을 반복한다.
- **보이는 형태**: 컨테이너 로그 한 줄 `exec /app/server: exec format error`. 쿠버네티스면 `CrashLoopBackOff`. 셸에서는 `cannot execute binary file: Exec format error`(exit 126).
- **원인**: 이미지 안 실행 파일의 `e_machine`이 노드 CPU와 다르다. 흔히 ARM64 노트북에서 `--platform` 없이 빌드해 ARM64 단일 이미지를 올렸다. 노드에 QEMU binfmt 규칙이 없으니 커널이 `ENOEXEC`를 낸다.
- **대처**
  - `docker image inspect`로 플랫폼을 보고, `file`로 엔트리포인트 바이너리를 본다.
  - `--platform`을 명시해 다시 빌드하거나 다중 플랫폼 이미지로 만든다.
  - 쿠버네티스는 노드의 `kubernetes.io/arch` 레이블(kubelet이 Go `runtime.GOARCH` 값, 예 `amd64`로 채움 — Kubernetes 문서 Well-Known Labels)로 배치를 제한할 수 있다.

### 2. 에뮬레이션으로 돌아가는데 수배 느리다

- **현상**: ARM64 맥에서 amd64 이미지를 띄우거나, CI에서 `--platform linux/arm64` 빌드를 x86 러너로 돌리자 시간이 크게 는다.
- **보이는 형태**: 같은 테스트·빌드가 네이티브보다 몇 배 오래 걸린다. 에러는 없다. 컨테이너 안 `uname -m`이 호스트와 다른 값을 낸다.
- **원인**: QEMU 사용자 모드 에뮬레이션이 남의 ISA 명령을 번역·실행한다(binfmt_misc 경유). Docker 문서는 "much slower ... especially for compute-heavy tasks like compilation and compression"이라고 적는다. Apple 문서도 Rosetta 번역 앱이 "launch or run more slowly at times"라고 적는다. 배수는 워크로드마다 다르고, 이 환경에 QEMU가 없어 측정하지 못했다.
- **대처**: 아키텍처별 네이티브 러너(ARM 인스턴스)를 쓰거나 교차 컴파일한다. 개발 머신에서는 네이티브 아키텍처 이미지를 함께 만든다.

### 3. 특정 서버에서만 `Illegal instruction`(exit 132)

- **현상**: 새 서버에선 도는 바이너리가 오래된 서버(또는 다른 클라우드 인스턴스 계열)에서 시작하자마자 죽는다.
- **보이는 형태**: `Illegal instruction (core dumped)`, exit 132. `dmesg`에는 `<프로세스명>[pid] trap invalid opcode ip:… sp:… error:0` 꼴 한 줄이 남을 수 있다(`arch/x86/kernel/traps.c`의 `show_signal` — `show_unhandled_signals`가 켜져 있고 처리기가 없는 시그널일 때, 속도 제한 있음).
- **원인**: `-march=native`나 `x86-64-v4`로 빌드해 대상 CPU에 없는 확장(예: AVX-512)을 썼다. 위 실험처럼 명령 하나로도 죽는다.
- **대처**: 대상 CPU 플래그(`grep -o -w avx512f /proc/cpuinfo`)와 `ld.so --help`의 지원 수준을 확인한다. 배포 빌드는 공통 최소 수준으로 하고, 빠른 경로는 실행 시 CPU 기능을 확인해 고른다(JVM이 하는 방식).

### 4. Graviton(ARM64)으로 옮기자 `UnsatisfiedLinkError`

- **현상**: 순수 Java 서비스라 믿고 ARM64 인스턴스로 옮겼는데 특정 기능을 처음 쓸 때 실패한다.
- **보이는 형태**: `java.lang.UnsatisfiedLinkError: ... cannot open shared object file: No such file or directory (Possible cause: can't load AMD 64 .so on a AARCH64 platform)` 꼴. 메시지 형식은 위 실험의 반대 방향이다.
- **원인**: 의존성 jar 안의 JNI `.so`가 x86-64용 하나만 들어 있다. 바이트코드는 이식되지만 네이티브 라이브러리는 아니다.
- **대처**: jar 안 `.so` 목록을 보고, ARM64 분류자(classifier)가 있는 판으로 바꾸거나 순수 Java 대체로 간다. "No such file"이라는 앞부분 문구에 속지 말고 괄호 안 진단을 읽는다.

## 핵심 문장

- ISA는 소프트웨어와 CPU 사이의 계약이고, 기계어는 그 계약대로 쓴 바이트열이다. 같은 C 함수가 x86-64와 ARM64에서 전혀 다른 바이트가 된다.
- x86-64는 가변 길이(이 실험 1~7바이트)에 메모리 피연산자를 받고, ARM64는 4바이트 고정에 큰 상수를 여러 명령으로 나눠 싣는다.
- 실행 파일은 ELF 헤더 `e_machine`(오프셋 0x12)에 아키텍처를 적는다. 커널은 맞지 않으면 `ENOEXEC`("Exec format error")로 거절한다.
- 컨테이너는 커널을 공유하므로 아키텍처를 바꿔 주지 않는다. 바꾸는 것은 binfmt_misc + QEMU 같은 에뮬레이션이고, 대가는 속도다.
- 같은 ISA 안에서도 확장(AVX-512 등)이 없으면 `SIGILL`이다. 바이트코드는 이식되지만 JNI `.so`는 아키텍처를 탄다.

## 관련 주제·근거

- 선행
  - 컴퓨터 구조 [08 순차 논리·클록](../08-sequential-logic-clock/2-summary.md)(PC·IR 레지스터)
  - 원고 [foundations/hardware-basics](../../foundations/hardware-basics/README.md) §3 CPU 내부 구조, §7 레지스터, §8 시스템 버스, §9 인스트럭션 세트, §10 `C = A + B` 어셈블리
- 후속·연결
  - [10-calling-convention-and-stack-frame](../10-calling-convention-and-stack-frame/2-summary.md) — 인자·반환값이 어느 레지스터로 가나
  - [18-pipelining-and-branch-prediction](../18-pipelining-and-branch-prediction/2-summary.md) · [19-out-of-order-and-speculation](../19-out-of-order-and-speculation/2-summary.md) — 같은 ISA 아래의 마이크로아키텍처
  - [os/01-kernel-and-user-mode](../../os/01-kernel-and-user-mode/2-summary.md) — 특권 명령·`SIGILL`(exit 132)
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — ELF 섹션·동적 로더·`binfmt_elf`의 `PT_INTERP`
  - [os/35-virtualization-hypervisor](../../os/35-virtualization-hypervisor/2-summary.md) — 같은 ISA를 나눠 쓰는 가상화(에뮬레이션과 다르다)
  - [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — 컨테이너는 커널을 공유한다
- 교재
  - CS:APP 3판 3장 Machine-Level Representation of Programs — 3.2 Program Encodings, 3.4.1 Operand Specifiers(장·절 번호는 저자 사이트의 3판 서문·목차 PDF로 확인 <http://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
- 명세·문서
  - System V AMD64 ABI Draft 0.99.6 — 그림 3.4 Register Usage <https://refspecs.linuxbase.org/elf/x86_64-abi-0.99.pdf>
  - Arm AAPCS64(2025Q4) — Machine Registers › General-purpose Registers(r0–r30, SP) <https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst>
  - Linux 커널 문서 Kernel Support for miscellaneous Binary Formats (binfmt_misc) <https://docs.kernel.org/admin-guide/binfmt-misc.html> · 커널 소스 `fs/exec.c`(`search_binary_handler`), `fs/binfmt_elf.c`(`elf_check_arch`), `fs/binfmt_misc.c`(`insert_binfmt`), `arch/x86/kernel/traps.c`(`"invalid opcode"` → `SIGILL`, `show_signal`) <https://github.com/torvalds/linux>
  - Kubernetes 문서 Well-Known Labels, Annotations and Taints — `kubernetes.io/arch` <https://kubernetes.io/docs/reference/labels-annotations-taints/>
  - `execve(2)` man 페이지 — `ENOEXEC` · `/usr/include/elf.h` — `EM_X86_64 62`, `EM_AARCH64 183`
  - Docker 문서 Multi-platform builds — 컨테이너는 호스트 커널 공유, QEMU 에뮬레이션 "much slower", 매니페스트 목록 <https://docs.docker.com/build/building/multi-platform/>
  - Apple Developer, About the Rosetta translation environment — 번역 앱이 느릴 수 있음, AVX-512 미지원 <https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment>
  - JVMS SE21 §4.1(클래스 파일 버전)·§5.3.5(`UnsupportedClassVersionError`) <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html> · Java 21 `java` 명령 `-Xint` <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - OpenJDK jdk21u `src/hotspot/os/linux/os_linux.cpp` — `Possible cause: can't load %s .so on a %s platform` <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/hotspot/os/linux/os_linux.cpp>
- 실험 목록(모두 2026-10-07, i7-13700HX, Ubuntu 24.04.4, 커널 7.0.0-34-generic)
  - gcc 13.3.0 / clang 18.1.3 교차 컴파일로 `add`·`add_mem`·`big`의 x86-64·ARM64 기계어 비교(objdump 2.42, llvm-objdump 18)
  - Python 3.12로 만든 최소 ELF(`exit7-amd64`·`exit7-arm64`)의 `xxd`·`file` 헤더 비교, 호스트 실행(126 / Exec format error, `ENOEXEC`=8), Docker 29.1.3 컨테이너 실행(`exec format error`, exit 255)
  - AVX-512 명령 1개 실행 → `Illegal instruction`, exit 132 · `ld.so --help`의 x86-64-v2/v3 지원
  - Temurin 21.0.12 컨테이너: `System.load`로 ARM64 파일 → `UnsatisfiedLinkError (Possible cause: can't load AARCH64 .so on a AMD 64 platform)`, `UseAVX=2`·`UseSSE=4`, `java` 실행 파일 `e_machine`=0x3e
