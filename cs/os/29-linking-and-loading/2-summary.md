# os/29-linking-and-loading — 이름을 주소로 바꾸는 두 번의 작업: 빌드 때의 링커, 실행 때의 로더 — 정리 (힌트)

## 해결하는 문제

컴파일러는 파일 하나씩 기계어로 바꾼다. 그 결과물(목적 파일)은 아직 구멍투성이다.

```text
  main.c ──컴파일──> main.o      "add를 부른다. 그런데 add가 어디 있는지 모른다" (구멍)
  add.c  ──컴파일──> add.o       "add는 여기 있다. 내가 몇 번지에 놓일지는 모른다"
  printf ...                      "printf는 libc 어딘가. libc가 몇 번지에 올라올지 모른다"
```

누군가 두 가지를 해 줘야 프로그램이 돈다.

1. **심볼 해석**: "add"라는 이름을 실제 정의 하나에 연결한다.
2. **재배치**: 정의가 놓일 주소를 정하고, 구멍(주소 자리)을 그 값으로 채운다.

이 일을 **빌드 때** 전부 하면 정적 링킹이다. 일부를 **실행 때**로 미루면 동적 링킹이다. 실행 때 이 일을 하는 프로그램이 동적 로더(`ld.so`)다.

쉬운 예: 이사 짐 목록이다.
- 각 방(목적 파일)의 짐 목록에는 "책상 → 서재 옆"처럼 **이름**으로 적혀 있다.
- 이삿날(링크) 누군가 실제 **호수·위치**를 정해 목록을 고친다.
- 공용 창고(공유 라이브러리) 물건은 입주하는 날(실행) 창고 위치를 확인해야 쓸 수 있다.

똑같은 구조다.\
`undefined reference to 'add'`는 이삿날 "책상이 목록에 없다"는 말이다. `error while loading shared libraries`는 입주 날 "창고를 못 찾았다"는 말이다.

실무 예:
- 빌드 서버에서는 되던 바이너리가 운영 서버에서 `version 'GLIBC_2.34' not found`로 안 뜬다.
- alpine 이미지에 복사한 바이너리가 파일이 분명히 있는데 `not found`로 실패한다.

## 동작·원리

기초 흐름(전처리 → 컴파일 → 어셈블 → 링크)은 원고 [foundations/compiler-pipeline §4](../../foundations/compiler-pipeline/README.md)에 있다.\
링크 에러 문구를 원인으로 거꾸로 읽는 법은 [c/syntax/45](../../../languages/c/syntax/45-translation-units-and-reading-link-errors/2-summary.md)가 자세하다. 여기서는 OS 쪽, 곧 **실행 파일이 메모리에 올라와 이름이 주소가 되기까지**를 본다.

### 1. 목적 파일 안의 두 표 — 심볼 테이블과 재배치 항목

```text
$ nm main.o                     $ nm add.o                 (예시, gcc 13.3, 로컬 재현)
                 U add          0000000000000000 T add
0000000000000000 T main         0000000000000000 B counter
                 U printf

$ readelf -r main.o
  Offset   Type             Sym. Name + Addend
  0x13     R_X86_64_PLT32   add - 4        <- ".text의 0x13 자리에 add의 (상대) 주소를 넣어라"
  0x1c     R_X86_64_PC32    .rodata - 4    <- 문자열 "%d\n"의 주소
  0x29     R_X86_64_PLT32   printf - 4
```

- `U`(undefined): 이 파일이 쓰지만 정의는 없는 이름이다. `T`: 코드(.text)에 정의가 있다. `B`: 초기값 없는 전역(.bss)이다.
- 재배치 항목은 "이 오프셋의 구멍을, 이 심볼의 주소로, 이 방식으로 채워라"라는 지시다(CS:APP 7.7).

  - *심볼*: 함수·전역 변수의 이름과 그 위치 정보다.
  - *재배치(relocation)*: 코드·데이터 안의 주소 자리를 최종 주소로 고쳐 쓰는 일이다.

### 2. 정적 링킹 — 빌드 때 전부 채운다

```text
  main.o  [U add, U printf]  ─┐
  add.o   [T add]            ─┼─> ld ─> 실행 파일 (구멍 없음, libc 코드까지 복사)
  libc.a  [printf.o, ...]    ─┘       785,416 바이트 (예시, -static)
                                     vs 동적 링크 15,992 바이트 (예시)
```

- 링커는 명령줄 **왼쪽에서 오른쪽**으로 읽으며 "아직 못 푼 이름" 집합을 들고 간다.
- 정적 라이브러리(`.a`)는 목적 파일 묶음이다. 링커는 그 순간 못 푼 이름을 정의하는 멤버만 꺼낸다(CS:APP 7.6.3).
- 그래서 **라이브러리를 먼저 쓰면** 아직 필요한 이름이 없어 아무것도 안 꺼내고 지나간다. 그 뒤 `main.o`가 `add`를 요구하면 `undefined reference`다.

```text
gcc main.o -L. -Wl,-Bstatic -ladd -Wl,-Bdynamic      -> 성공 (5 출력)
gcc -L. -Wl,-Bstatic -ladd -Wl,-Bdynamic main.o      -> undefined reference to `add'   (로컬 재현)
```

- 같은 강한 정의가 둘이면 `multiple definition of 'add'`다.

### 3. 실행 — 커널이 먼저, 그다음 동적 로더

```text
  execve("./app")
     |
     v
  커널 (fs/binfmt_elf.c)
     1. ELF 헤더·프로그램 헤더를 읽는다
     2. PT_LOAD 세그먼트를 mmap  (코드 R-X, 데이터 RW- ...)
     3. PT_INTERP 가 있으면 그 경로(/lib64/ld-linux-x86-64.so.2)도 mmap
        -> 그 로더 파일이 없으면 execve 자체가 ENOENT (PT_INTERP가 없는 정적 바이너리는 로더 없이 바로 시작)
     4. 보조 벡터(auxv)에 AT_ENTRY(프로그램 시작점), AT_BASE(로더 주소) 등을 넣고
        로더의 시작점으로 점프
     |
     v
  동적 로더 ld.so (사용자 공간)
     5. DT_NEEDED 목록(libadd.so, libc.so.6)을 찾아 open + mmap
     6. 심볼 버전 확인 (GLIBC_2.34 등)
     7. 재배치: GOT 채우기 (지금 하거나 첫 호출 때)
     8. 각 라이브러리 초기화 후 AT_ENTRY(_start)로 점프 -> main
```

- 동적 링크 실행 파일에는 `INTERP` 프로그램 헤더가 있다. 커널은 이 경로의 로더를 같이 올리고 로더부터 실행한다(fs/binfmt_elf.c `load_elf_interp`, `AT_BASE`·`AT_ENTRY`).
- 로더가 없으면 **실행 파일이 있어도** `execve`가 `ENOENT`로 실패한다. execve(2): "The file pathname or a script or ELF interpreter does not exist."

```text
$ readelf -l dyn | grep interpreter
      [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
$ readelf -d dyn | grep -E 'NEEDED|FLAGS'
 (NEEDED)   Shared library: [libadd.so]
 (NEEDED)   Shared library: [libc.so.6]
 (FLAGS)    BIND_NOW
 (FLAGS_1)  Flags: NOW PIE                          (예시, Ubuntu 24.04 gcc 기본값, 로컬 재현)
```

### 4. 로더는 라이브러리를 어디서 찾나

```text
  이름에 '/'가 없는 의존성 (ld.so(8))
  (1) DT_RPATH           — DT_RUNPATH가 없을 때만. 폐기 예정
  (2) LD_LIBRARY_PATH    — 보안 실행 모드(setuid 등)면 무시
  (3) DT_RUNPATH         — 직접 의존성에만 적용 (자식 라이브러리엔 안 물려준다)
  (4) /etc/ld.so.cache   — ldconfig가 만든 캐시
  (5) 기본 경로 /lib, /usr/lib (64비트 일부는 /lib64, /usr/lib64)
```

- 못 찾으면 `error while loading shared libraries: libadd.so: cannot open shared object file: No such file or directory`, exit 127(작성 환경, 로컬 재현).
- `-Wl,-rpath,'$ORIGIN'`로 링크하면 RUNPATH에 "실행 파일이 있는 디렉터리"가 들어간다. 배포 폴더째 옮겨도 찾는다.
  - RUNPATH가 될지 RPATH가 될지는 링커 설정(`--enable-new-dtags`)에 달렸다. ld(1)은 기본을 "새 태그 안 만듦"(RPATH)이라 적지만, 작성 환경 Ubuntu gcc에서는 RUNPATH로 들어갔다(로컬 재현).

### 5. PIC·GOT·PLT — 주소를 모르는 코드가 남의 함수를 부르는 법

공유 라이브러리는 프로세스마다 다른 주소에 올라온다. 그래도 **코드 페이지는 하나를 여러 프로세스가 공유**해야 메모리를 아낀다. 그러려면 코드 안에 절대 주소를 박으면 안 된다.

```text
   코드 (.text, 읽기 전용, 여러 프로세스 공유)           데이터 (프로세스마다 사본)
   +-----------------------------------+              +--------------------------+
   | call add@plt  ----------------+   |              | GOT (전역 오프셋 테이블)     |
   |                                |   |              |  [add]    = 0x7ffff7fb7100 | <- 로더가 채움
   | add@plt:                       v   |              |  [printf] = 0x7ffff7c60100 |
   |   jmp *GOT[add]  ------------------+------------->|  [counter]= ...            |
   +-----------------------------------+              +--------------------------+
   코드에서 GOT까지의 거리는 링크 때 고정 -> PC 상대 주소로 접근 (코드 수정 불필요)
   (주소 값은 예시)
```

- **PIC**(position-independent code): 어느 주소에 올려도 고치지 않고 도는 코드다. 외부 주소는 GOT를 거쳐 간접으로 읽는다(CS:APP 7.12).
- **GOT**: 외부 심볼의 실제 주소를 담는 표다. 데이터 영역이라 프로세스마다 따로 채운다.
- **PLT**: 외부 함수 호출용 작은 점프 코드다. `jmp *GOT[add]`처럼 GOT를 거친다.
- **지연 바인딩(lazy)**: 첫 호출 때 로더가 주소를 찾아 GOT를 채운다. **즉시 바인딩(BIND_NOW)**: 시작할 때 전부 채운다.
  - 작성 환경의 Ubuntu gcc 기본 산출물은 `BIND_NOW`였다. `-Wl,-z,lazy`를 주자 `BIND_NOW`가 사라졌다(로컬 재현).
- `-fPIC` 없이 만든 목적 파일로 공유 라이브러리를 만들면 링커가 거절한다.

```text
$ gcc -c -fno-pic add.c && gcc -shared add.o -o libadd.so
relocation R_X86_64_PC32 against symbol `counter' can not be used when making a shared object; recompile with -fPIC
```

  - 작성 환경은 gcc 기본이 PIE(`--enable-default-pie`)였는데, **PIE용 `.o`로도 같은 에러**가 났다(로컬 재현). PIE는 "실행 파일 자신의 전역은 가로채이지 않는다"고 가정해 GOT를 안 거치기 때문이다. 공유 라이브러리는 `-fPIC`가 따로 필요하다.

### 6. 심볼 버전 — 같은 이름, 다른 판

```text
$ objdump -T app | grep GLIBC                              (예시, glibc 2.39에서 빌드)
  (GLIBC_2.34) __libc_start_main
  (GLIBC_2.2.5) printf
$ readelf -V app  ->  Version needs: libc.so.6  GLIBC_2.2.5, GLIBC_2.34
```

- glibc는 심볼마다 버전 태그를 단다. 실행 파일은 "`__libc_start_main`의 `GLIBC_2.34` 판이 필요하다"를 기록한다.
- 이 바이너리를 glibc 2.34 미만 시스템에서 돌리면 로더가 그 판을 못 찾아 시작 전에 멈춘다. 에러 형태는 아래처럼 같다(작성 환경에서 직접 만든 라이브러리 버전으로 재현).

```text
./app: .../libadd.so: version `LIBADD_2.0' not found (required by ./app)        exit 1
```

- **새 시스템에서 빌드한 바이너리는 옛 시스템에서 안 돌 수 있다.** 반대(옛 시스템에서 빌드 → 새 시스템)는 대개 된다. glibc가 옛 버전 심볼을 남겨 두기 때문이다(예: 작성 환경 libc에 `memcpy`가 `GLIBC_2.2.5`판과 `GLIBC_2.14`판 둘 다 있었다).

## 쓰이는 자료구조·알고리즘

- **심볼 테이블 = 해시 테이블** — 로더는 수천 개 이름을 빠르게 찾아야 한다. 공유 객체에는 `.gnu.hash` 섹션이 있다(로컬 `readelf -S`). glibc 로더는 조회 전에 **블룸 필터 비트마스크**(`l_gnu_bitmask`)로 "이 라이브러리엔 없다"를 먼저 걸러 내고, 통과하면 버킷을 본다(glibc elf/dl-lookup.c). → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)
- **재배치 = 패치 목록** — (오프셋, 심볼, 방식) 목록을 한 번 훑으며 주소를 써 넣는다. 방식(`R_X86_64_PC32` 등)마다 계산식이 다르다(CS:APP 7.7.2).
- **간접 참조 표(GOT)** — "주소가 바뀌는 것은 표 한 칸만"이 되도록 한 단계 간접을 둔다. 가상 함수 테이블(vtable)과 같은 발상이다.
- **탐색 순서 목록(ld.so)** — 파일을 찾을 때: RPATH → LD_LIBRARY_PATH → RUNPATH → 캐시 → 기본 경로. 먼저 찾은 파일이 쓰인다.
- **심볼 조회 순서(전역 범위)** — 이름을 풀 때는 올라온 객체 목록을 앞에서부터 본다. `LD_PRELOAD` 라이브러리는 다른 공유 객체보다 먼저 올라온다(ld.so(8): "loaded before all others"). 그래서 그 함수가 원래 함수를 **가로챈다**(interposition, CS:APP 7.13). 파일 탐색 순서와는 다른 목록이다.

## 적용 — 풀어나가는 법

### 1. 바이너리가 무엇을 요구하는지 본다

```bash
file ./app                                  # statically/dynamically linked, interpreter 경로
readelf -l ./app | grep interpreter         # 필요한 로더 (glibc: /lib64/ld-linux-x86-64.so.2)
readelf -d ./app | grep -E 'NEEDED|RUNPATH|RPATH|FLAGS'
ldd ./app                                   # 해석 결과. "not found" 줄을 찾는다
objdump -T ./app | grep -o 'GLIBC_[0-9.]*' | sort -Vu | tail -1   # 요구하는 최고 glibc 판
ldd --version | head -1                     # 이 시스템의 glibc (작성 환경 2.39)
```

- `ldd`는 신뢰할 수 없는 바이너리에 쓰지 않는다. ldd(1)은 일부 버전·경우에 프로그램을 직접 실행할 수 있다고 경고한다. 그때는 `objdump -p ... | grep NEEDED`(직접 의존성만 보인다)를 쓴다.

### 2. 로더가 무엇을 하는지 본다

```bash
LD_DEBUG=libs ./app        # 어느 경로를 어떤 순서로 뒤졌나 (RUNPATH from file ...)
LD_DEBUG=bindings ./app    # 어느 심볼이 어느 라이브러리로 묶였나
LD_DEBUG=statistics ./app  # 로더 시작 시간, 재배치 수
strace -e trace=openat,mmap ./app   # 커널 쪽에서 본 open·mmap
```

### 3. 라이브러리 경로를 고치는 순서

1. 배포 형태를 정한다. 같은 폴더에 둔다면 `-Wl,-rpath,'$ORIGIN'`.
2. 시스템에 설치한다면 `/usr/local/lib` 등에 두고 `ldconfig`(root)로 캐시를 갱신한다.
3. `LD_LIBRARY_PATH`는 임시 확인용이다. 운영에서 기대면 다른 프로세스까지 영향을 받는다.

### 4. glibc 판 차이를 피한다

- **가장 오래된 대상 시스템(또는 그 컨테이너 이미지)에서 빌드**한다.
- 또는 대상과 같은 베이스 이미지로 빌드·실행한다(멀티스테이지 빌드의 빌드 단계와 실행 단계 베이스를 맞춘다).
- 정적 링크도 방법이다. 단 glibc의 정적 링크는 NSS(`getaddrinfo` 등)·`dlopen`과 얽혀 제약이 있다. 크기도 커진다.
  - 작성 환경에서 `getaddrinfo`를 쓰는 코드를 `-static`으로 링크하자 링커가 경고했다: `warning: Using 'getaddrinfo' in statically linked applications requires at runtime the shared libraries from the glibc version used for linking`(로컬 재현). 정적이어도 실행 때 같은 판 glibc 공유 라이브러리가 필요하다는 뜻이다.

### 5. 앱 런타임에서 보이는 모습

- **Java(JNI)**: `System.loadLibrary("x")`는 `java.library.path`에서 `libx.so`를 찾는다. 못 찾거나 로드에 실패하면 `UnsatisfiedLinkError`다(Java SE API `System.loadLibrary`). 내부적으로 `dlopen`을 쓰므로 위의 탐색 순서·glibc 판 문제가 그대로 온다.
- **Node(네이티브 애드온 `.node`)**: `process.dlopen`이 실패하면 `code: 'ERR_DLOPEN_FAILED'`와 로더 메시지가 그대로 나온다(로컬 재현).

```text
ERR_DLOPEN_FAILED /nonexist/libx.so: cannot open shared object file: No such file or directory
```

```c
/* 실행 중에 라이브러리를 여는 쪽 (dlopen(3)) — 플러그인·JNI·Node 애드온이 모두 이 경로 */
#include <dlfcn.h>
void *h = dlopen("libadd.so", RTLD_NOW);          /* 탐색 순서는 ld.so와 같다 */
if (!h) { fprintf(stderr, "%s\n", dlerror()); }   /* 실패 이유 문자열 */
int (*add)(int, int) = (int (*)(int, int))dlsym(h, "add");
```

## 장애 시나리오와 대처

### 1. `undefined reference to 'add'` — 빌드 실패

- **현상**: 컴파일은 되는데 링크 단계에서 실패한다.
- **보이는 형태**: `/usr/bin/ld: main.o: in function 'main': ... undefined reference to 'add'`, `collect2: error: ld returned 1 exit status`.
- **원인**
  - 정의가 든 목적 파일·라이브러리를 링크에 안 넣었다.
  - 정적 라이브러리를 사용하는 쪽보다 **앞**에 적었다(2절).
  - C++ 이름 변환(mangling)이나 `static`으로 이름이 안 맞는다(45번).
- **대처**: `nm`으로 양쪽 이름(`U`와 `T`)을 확인하고, 라이브러리를 사용하는 목적 파일 뒤로 옮긴다.

### 2. `error while loading shared libraries` — 실행 직후 실패

- **현상**: 빌드한 곳에서는 도는데 다른 서버·컨테이너에서 실행하자마자 끝난다.
- **보이는 형태**: `./app: error while loading shared libraries: libfoo.so.1: cannot open shared object file: No such file or directory`. 셸 exit 127(작성 환경). `ldd`에 `libfoo.so.1 => not found`.
- **원인**: 로더의 탐색 경로(4절) 어디에도 그 라이브러리가 없다. 빌드 때 `-L`로 준 경로는 실행 때 쓰이지 않는다.
- **대처**: 패키지를 설치하거나, RUNPATH(`$ORIGIN`)를 넣거나, 설치 후 `ldconfig`. `LD_DEBUG=libs`로 어디를 뒤졌는지 확인한다.

### 3. `version 'GLIBC_2.xx' not found` — 새 곳에서 빌드, 옛 곳에서 실행

- **현상**: CI(최신 이미지)에서 빌드한 바이너리가 운영(구형 배포판)에서 안 뜬다.
- **보이는 형태**: `./app: /lib/x86_64-linux-gnu/libc.so.6: version 'GLIBC_2.34' not found (required by ./app)`.
- **원인**: 빌드한 glibc가 새 판 심볼(예: `__libc_start_main@GLIBC_2.34`)을 걸었다. 실행하는 glibc에 그 판이 없다(6절).
- **대처**: 대상과 같거나 더 오래된 glibc 환경에서 빌드한다. `objdump -T`로 최고 요구 판을 CI에서 검사한다.

### 4. alpine(musl)에서 glibc 바이너리 → 있는 파일이 `not found`

- **현상**: `COPY`로 넣은 바이너리가 분명히 있는데 실행이 안 된다.
- **보이는 형태**
  - `sh: ./app: not found`(작성 환경의 dash). bash 5.2라면 `bash: ./app: cannot execute: required file not found`(한국어 로캘: "실행할 수 없음: 필요한 파일이 없습니다"). exit 127(로컬 재현).
  - `strace`로 보면 `execve(...) = -1 ENOENT`.
  - 작성 환경에서 인터프리터 경로를 없는 파일로 바꿔 링크해 같은 증상을 재현했다(로컬 재현).
- **원인**
  - alpine은 C 라이브러리가 musl이다. glibc 로더 `/lib64/ld-linux-x86-64.so.2`가 없다.
  - 커널이 `PT_INTERP`의 로더를 못 찾으면 `execve`가 `ENOENT`를 돌려준다. 셸은 이것을 "파일이 없다"로 보여 준다.
  - 로더 경로를 억지로 맞춰도 끝이 아니다. musl 로더는 glibc식 심볼 버전 중 "기본 판 고르기"만 지원한다(musl wiki "Functional differences from glibc" — Symbol versioning). glibc에만 있는 심볼·ABI 차이로 심볼 해석이나 실행 중에 실패할 수 있다.
- **대처**: glibc 기반 베이스(slim·distroless 등)를 쓰거나, musl 환경에서 다시 빌드하거나, 정적 링크한다.

### 5. `LD_PRELOAD`·경로 순서로 엉뚱한 함수가 불린다

- **현상**: 같은 이름 함수가 기대와 다른 결과를 낸다(작성 환경에서 `LD_PRELOAD=./libpre.so`로 `add(2,3)`이 100을 돌려줬다, 로컬 재현).
- **보이는 형태**: `LD_DEBUG=bindings`에 예상과 다른 라이브러리가 찍힌다.
- **원인**: 동적 심볼 해석은 먼저 올라온 객체의 정의가 이긴다. 프리로드·`LD_LIBRARY_PATH`의 다른 판 라이브러리가 끼어들었다.
- **대처**: 환경 변수를 확인하고, 필요하면 심볼 가시성(`-fvisibility=hidden`)·버전 스크립트로 노출 범위를 줄인다.

## 핵심 문장

- 링크는 **심볼 해석**(이름 → 정의 하나)과 **재배치**(구멍 → 주소)다. 정적 링킹은 빌드 때 다 하고, 동적 링킹은 실행 때 `ld.so`가 마저 한다.
- 정적 라이브러리는 "지금 못 푼 이름"만 꺼내므로 **순서가 중요하다**. 라이브러리는 쓰는 쪽 뒤에 둔다.
- 커널은 실행 파일과 `PT_INTERP`의 로더를 올리고 로더부터 실행한다. 로더가 없으면 파일이 있어도 `ENOENT`(`not found`)다.
- PIC 코드는 외부 주소를 **GOT**로 간접 참조한다. 그래서 코드 페이지를 여러 프로세스가 공유하고, 주소는 프로세스별 GOT만 채운다.
- 새 glibc에서 빌드한 바이너리는 옛 glibc에서 `GLIBC_2.xx not found`로 멈출 수 있다. 가장 오래된 대상에서 빌드한다.

## 관련 주제·근거

- 선행
  - [architecture/09-isa-and-machine-code](../../architecture/09-isa-and-machine-code/2-summary.md)(기계어·주소 지정)
  - 원고 [foundations/compiler-pipeline §4](../../foundations/compiler-pipeline/README.md) — 컴파일 전체 흐름과 링커
- 연결
  - [c/syntax/44 헤더와 분할 컴파일](../../../languages/c/syntax/44-headers-and-separate-compilation/2-summary.md) · [c/syntax/45 번역 단위와 링크 에러 읽기](../../../languages/c/syntax/45-translation-units-and-reading-link-errors/2-summary.md)
  - [09-address-space](../09-address-space/2-summary.md) — 세그먼트가 주소 공간 어디에 놓이나. 원고는 [foundations/memory-management](../../foundations/memory-management/README.md)
  - [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — 로더가 라이브러리를 mmap으로 올린다
  - [05-fork-exec-wait](../05-fork-exec-wait/2-summary.md) — `execve`
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — 이미지 베이스(musl·glibc) 선택
  - [language/24-aot-native-image-and-startup](../../language/24-aot-native-image-and-startup/2-summary.md), [language/25-lto-pgo-and-binary-size](../../language/25-lto-pgo-and-binary-size/2-summary.md)
- 교재: CS:APP 3판 7장 — 7.5 심볼과 심볼 테이블, 7.6 심볼 해석(7.6.3 정적 라이브러리로 참조 풀기), 7.7 재배치, 7.9 실행 파일 로딩, 7.10 공유 라이브러리 동적 링킹, 7.11 애플리케이션에서 공유 라이브러리 로딩, 7.12 PIC, 7.13 라이브러리 인터포지셔닝
- Linux man-pages
  - ld.so(8) — 탐색 순서(RPATH·LD_LIBRARY_PATH·RUNPATH·캐시·기본 경로), `LD_DEBUG`, `LD_PRELOAD`, `LD_BIND_NOW` <https://man7.org/linux/man-pages/man8/ld.so.8.html>. "DT_RPATH는 deprecated" 문장은 작성 환경의 로컬 ld.so(8)에 있고 man7.org 최신판에는 없다
  - ld(1) `--enable-new-dtags`(RUNPATH/RPATH 선택)
- musl wiki "Functional differences from glibc" — Symbol versioning <https://wiki.musl-libc.org/functional-differences-from-glibc.html>
  - execve(2) — `ENOENT`: "a script or ELF interpreter does not exist" <https://man7.org/linux/man-pages/man2/execve.2.html>
  - ldd(1) — 신뢰할 수 없는 실행 파일에 쓰지 말 것 · dlopen(3) · elf(5)
- 커널 소스 fs/binfmt_elf.c — `PT_INTERP`, `load_elf_interp`, `AT_BASE`·`AT_ENTRY` <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/fs/binfmt_elf.c>
- glibc 소스 elf/dl-lookup.c — GNU 해시의 블룸 비트마스크(`l_gnu_bitmask`)와 버킷 <https://sourceware.org/git/?p=glibc.git;a=blob;f=elf/dl-lookup.c>
- Java SE `System.loadLibrary` — `UnsatisfiedLinkError` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/System.html>
- 로컬 재현(리눅스 7.0, Ubuntu 24.04, gcc 13.3, glibc 2.39): `nm`·`readelf -r`, 라이브러리 순서 undefined reference, 정적/동적 크기, 라이브러리 없음 exit 127, `$ORIGIN` RUNPATH, `LD_DEBUG=libs/bindings/statistics`, BIND_NOW 기본값과 `-z lazy`, `-fno-pic`·PIE `.o`의 `-shared` 실패, 버전 스크립트로 `version not found` 재현, 없는 인터프리터 → `ENOENT`, `LD_PRELOAD` 가로채기, Node `ERR_DLOPEN_FAILED`, `-static` 링크 시 `getaddrinfo` 경고
