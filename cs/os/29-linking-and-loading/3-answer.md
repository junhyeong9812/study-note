# os/29-linking-and-loading — 정답

## 정답

### 1. 링커의 두 가지 일

- **심볼 해석**: 각 이름("add")을 정의 하나에 연결한다. `nm`의 `U add`는 "이 파일은 add를 쓰지만 정의가 없다"는 표시다. 링커는 다른 파일의 `T add`와 짝짓는다.
- **재배치**: 정의가 놓일 주소를 정하고, 코드·데이터의 주소 자리를 채운다. `readelf -r`의 `0x13 R_X86_64_PLT32 add - 4`는 "`.text` 0x13 자리에 add로 가는 PC 상대 값을 넣어라"는 지시다(CS:APP 7.7).

### 2. 정적 라이브러리 순서

- 링커는 명령줄을 왼쪽부터 읽으며 "아직 못 푼 이름" 집합을 유지한다.
- `.a`를 만나면 그 순간 집합에 있는 이름을 정의하는 멤버 목적 파일만 꺼낸다(CS:APP 7.6.3).
- 라이브러리가 먼저 오면 집합이 비어 있어 아무것도 안 꺼낸다. 그 뒤 `main.o`가 `add`를 요구해도 되돌아가지 않는다 → `undefined reference to 'add'`.
- `main.o`가 먼저 오면 `add`가 집합에 들어간 상태로 `libadd.a`를 만나 꺼낸다 → 성공(로컬 재현).

### 3. execve에서 main까지

```text
  execve("./app")
   커널 (fs/binfmt_elf.c)
     - ELF·프로그램 헤더를 읽고 PT_LOAD 세그먼트를 mmap
     - PT_INTERP(/lib64/ld-linux-x86-64.so.2)를 읽어 로더도 mmap
     - auxv에 AT_ENTRY(=프로그램의 _start), AT_BASE(=로더 주소) 등을 넣는다
     - 로더의 시작점으로 점프
   동적 로더 ld.so
     - DT_NEEDED 라이브러리를 탐색 순서대로 찾아 open + mmap
     - 심볼 버전 확인, 재배치(GOT 채우기)
     - 라이브러리 초기화 후 AT_ENTRY로 점프
   _start -> __libc_start_main -> main
```

- `PT_INTERP`는 실행 파일의 프로그램 헤더(`readelf -l`)에 있다.
- `AT_ENTRY`는 커널이 만든 보조 벡터에 있다(`LD_SHOW_AUXV=1 ./app`로 볼 수 있다).

### 4. 빌드 경로 ≠ 실행 경로

- `-L`은 **링커**가 빌드 때 라이브러리를 찾는 경로다. 실행 파일에는 `DT_NEEDED`로 **이름**(`libfoo.so.1`)만 남는다.
- 실행 때 **로더**는 자기 탐색 순서로 그 이름을 찾는다(ld.so(8)).
  1. DT_RPATH(RUNPATH가 없을 때만, 폐기 예정)
  2. LD_LIBRARY_PATH(보안 실행 모드면 무시)
  3. DT_RUNPATH(직접 의존성에만)
  4. /etc/ld.so.cache
  5. 기본 경로 /lib, /usr/lib
- 폴더째 배포: `-Wl,-rpath,'$ORIGIN'`(필요하면 `$ORIGIN/lib`)로 링크한다. 로더가 실행 파일 위치 기준으로 찾는다.

### 5. PLT·GOT

```text
  .text (공유, 읽기 전용)          .got (프로세스별)
  call add@plt
  add@plt: jmp *GOT[add] ------>  GOT[add] = libadd.so 안 add의 실제 주소 (로더가 채움)
```

- 공유 라이브러리는 프로세스마다 다른 주소에 올라온다. 코드에 주소를 박으면 프로세스마다 코드를 고쳐야 하고, 고친 코드 페이지는 공유할 수 없다.
- 그래서 바뀌는 주소는 데이터 영역의 **GOT 한 칸**에만 두고, 코드는 PC 상대로 GOT를 읽는다. 코드는 그대로 여러 프로세스가 공유한다.
- **지연 바인딩**: 첫 호출 때 로더가 주소를 찾아 GOT를 채운다. 시작이 빠르지만 첫 호출이 느리다.
- **BIND_NOW**: 시작할 때 전부 채운다. 없는 심볼을 시작 시점에 바로 발견한다. 작성 환경의 Ubuntu gcc 기본 산출물이 `BIND_NOW`였다(로컬 재현).

### 6. `GLIBC_2.34 not found`

- 확인
  - 바이너리가 요구하는 판: `objdump -T ./app | grep GLIBC`(예: `__libc_start_main`의 `GLIBC_2.34`).
  - 서버의 glibc: `ldd --version`.
- 원인: 빌드한 glibc가 새 판 심볼을 걸었고, 운영의 glibc에는 그 판이 없다. 로더가 시작 전에 멈춘다.
- 고치기
  - 운영과 같거나 더 오래된 glibc 환경(같은 베이스 이미지)에서 빌드한다.
  - 또는 운영 환경을 올리거나, 정적 링크를 검토한다.
- 반대 방향이 대개 되는 이유: glibc가 옛 판 심볼을 계속 남겨 둔다(예: `memcpy@GLIBC_2.2.5`와 `memcpy@GLIBC_2.14`가 함께 있다). 옛 판을 요구하는 바이너리는 새 glibc에서도 찾는다.

### 7. alpine의 `not found`

- `strace ./app`: `execve("./app", ...) = -1 ENOENT`.
- 파일은 있다. 없는 것은 **ELF 인터프리터**다. glibc 바이너리의 `PT_INTERP`는 `/lib64/ld-linux-x86-64.so.2`인데, musl 기반 alpine에는 없다.
- 커널은 인터프리터를 못 찾으면 `execve`를 `ENOENT`로 실패시킨다(execve(2)). 셸은 이것을 "not found"로 보여 준다. 작성 환경에서 없는 인터프리터 경로로 링크해 같은 증상을 재현했다.
- 대처: glibc 기반 이미지를 쓰거나 musl로 다시 빌드하거나 정적 링크한다.

### 8. `UnsatisfiedLinkError`·`ERR_DLOPEN_FAILED`

- 둘 다 **실행 중 `dlopen` 단계**(동적 로더가 라이브러리를 찾고, 올리고, 심볼을 맞추는 단계)의 실패가 런타임 예외로 드러난 것이다.
- 원인 후보: 라이브러리 파일 없음(탐색 경로), 그 라이브러리의 의존성 없음, glibc 판 불일치, 아키텍처 불일치.
- 좁히기: `LD_DEBUG=libs`(어디를 뒤졌나)나 `LD_DEBUG=bindings`(무엇에 묶였나)를 켜고 실행한다. Node는 에러 메시지에 로더 메시지(`cannot open shared object file` 등)가 그대로 들어 있다(로컬 재현).
