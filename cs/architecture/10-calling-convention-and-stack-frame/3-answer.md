# architecture/10-calling-convention-and-stack-frame — 정답

## 정답

### 1. 호출 규약의 네 가지

- ① 인자를 어디에 두나(레지스터·스택) ② 반환 주소를 어디에 두나 ③ 반환값을 어디서 받나 ④ 어떤 레지스터를 누가 보존하나. 여기에 스택 정렬과 인자 정리 책임이 붙는다.
- 규약은 ABI의 일부다. 서로 다른 컴파일러(gcc·clang)로 만든 코드, 미리 컴파일된 라이브러리, JVM이 부르는 네이티브 함수가 맞물리려면 같은 규약을 따라야 한다.

### 2. `sum7` 인자 7개의 자리

```text
  x86-64 SysV:  1→rdi 2→rsi 3→rdx 4→rcx 5→r8 6→r9, 7→스택(push $0x7)   반환 주소: call이 스택에
  32비트 cdecl: 7,6,5,4,3,2,1 순서로 전부 push (1이 가장 낮은 주소)       반환 주소: call이 스택에
  ARM64 AAPCS64: 1~7 → x0~x6 (8개까지 레지스터)                        반환 주소: bl이 x30(LR)에
```

- 실험 디스어셈블: x86-64 `-O2`는 `push $0x7` 뒤 `call sum7`, 돌아와서 `pop %rdx`로 그 8바이트를 정리했다. `-m32`는 `push $0x7`~`push $0x1` 7번 뒤 `add $0x1c,%esp`(28바이트)로 정리했다. ARM64는 `mov x0,#1 … mov x6,#7; bl sum7`이었다.
- ARM64 함수가 다른 함수를 부르면 LR이 덮이므로, 정상 복귀에 필요한 반환 주소를 보존해야 한다. 실험의 `-O0` `caller`는 입구에서 `stp x29, x30, [sp, ...]`로 스택에 저장했다(꼬리 호출이면 받은 LR을 그대로 넘기기도 한다).

### 3. `-O0` `adder`에 `sub %rsp`가 없는 이유

- 지역 변수와 옮겨 적은 인자가 `-0x4(%rbp)`~`-0x1c(%rbp)`, 즉 `rsp` 아래에 있다. 이 구역이 red zone(128바이트)이다.
- System V ABI 3.2.2는 이 128바이트를 시그널·인터럽트 처리기가 건드리지 않는다고 정한다. 다른 함수를 부르지 않는 잎 함수는 `rsp`를 내리지 않고 이 구역을 프레임으로 쓸 수 있다.
- `-O2`에서는 프레임 자체가 없다. `lea (%rsi,%rdi,1),%eax; imul %edx,%eax; ret` — 인자 레지스터만으로 `(a+b)*n`을 계산했다.

### 4. callee-saved vs caller-saved

- caller-saved: callee가 마음대로 덮어써도 된다. 호출 뒤에도 필요하면 caller가 저장한다(`rax, rcx, rdx, rsi, rdi, r8`~`r11`).
- callee-saved: callee가 쓰려면 저장했다가 되돌려야 한다. x86-64 System V에서는 `rbx, rbp, r12`~`r15`(그리고 `rsp`)다(ABI 그림 3.4).
- 실험 `caller`(`-O0`)는 `adder`의 결과를 `%ebx`에 두고 `sum7`을 불렀다. `rbx`가 callee-saved라 살아남는다. 그 대신 자기 입구에서 `push %rbx`로 원래 값을 저장했다.

### 5. 깊이 ≈ 스택 한도 ÷ 프레임 크기

| 프레임 | 8 MiB 예측 | 실측(`-O1`) | 16 MiB 실측 |
|---|---|---|---|
| 32 B | 262,144 | 261,758~261,976 | 524,041~524,110 |
| 1,056 B | 7,943 | 7,933~7,938 | 15,877~15,881 |

- 실측이 조금 모자란 것은 `main`·환경 변수·인자가 이미 쓴 스택 때문이다.
- 지역 배열 하나로 깊이 한계가 약 33배 줄었다. 한도를 2배로 하면 깊이도 약 2배다.

### 6. 프레임 포인터 사슬과 끊긴 flame graph

```text
  walk 프레임: [rbp] ─▶ c의 rbp 저장 자리: [rbp] ─▶ b의 ... ─▶ a ─▶ main
               [rbp+8] = c로 돌아갈 주소   [rbp+8] = b로 돌아갈 주소 ...
```

- 프레임마다 "이전 rbp + 반환 주소" 쌍이 있고, 이전 rbp가 다음 쌍을 가리킨다. 이 연결 리스트를 따라가면 호출 경로가 나온다.
- 실험: `-O2 -fno-omit-frame-pointer`는 `c → b → a → main`을 다 찾았다. `-O2 -fomit-frame-pointer`(gcc `-O2` 기본)는 `c` 다음에 `__libc_start_main`으로 건너뛰었다.
- C: 프로파일링할 바이너리를 `-fno-omit-frame-pointer`로 빌드한다(이 Ubuntu 24.04의 `dpkg-buildflags`가 이미 그렇게 한다). Java: `-XX:+PreserveFramePointer`(JDK 21 기본 `false`)를 켠다. 비용은 측정해서 판단한다. 또는 DWARF 되감기를 쓰는 도구를 쓴다.

### 7. 버퍼 넘침이 반환 주소를 덮는 이유

```text
  높은 주소 [ 반환 주소 ][ 이전 rbp ][ 카나리 ][ buf[15] ... buf[0] ] 낮은 주소
```

- 스택은 아래(낮은 주소)로 자란다. 그래서 함수 입구에서 먼저 놓인 반환 주소·이전 rbp가 위에 있고, 나중에 잡은 지역 배열이 아래에 있다.
- 배열은 `buf[0]`부터 인덱스가 커질수록 **높은** 주소로 간다. 위 그림 배치라면 끝을 넘은 길이만큼 위쪽의 카나리 → 이전 rbp → 반환 주소 순으로 덮는다(실제 배치는 컴파일러·옵션마다 다르고, C 표준상 범위 밖 쓰기는 정의되지 않은 동작).
- 그 함수가 `ret`할 때 덮인 주소로 점프한다. 카나리가 있으면 반환 직전 검사에서 `stack smashing detected`(exit 134)로 멈춘다([security/24](../../security/24-memory-safety-exploits/2-summary.md)).

### 8. JSON 파싱 `StackOverflowError`

- 트레이스가 정확히 1,024줄인 것은 `MaxJavaStackTraceDepth = 1024`에서 잘렸기 때문이다. 실제 깊이는 더 깊다. 반복되는 몇 개 메서드가 재귀 경로다.
- 같은 `-Xss1m`에서도 깊이가 크게 다른 것은 주로 JIT 때문이다(해석). 컴파일된 프레임은 인터프리터 프레임보다 작고, 컴파일 시점이 실행마다 다르다. 다만 `-Xint`도 측정 묶음끼리 열몇 단계 달랐으므로 JIT만이 원인은 아니다(스택 시작 위치 등 — 해석). 실험: `-Xint`는 한 측정 묶음 안에서 고정(9,069, 점검 재실행 9,081), JIT를 켜면 9,069~59,026([algorithm/03](../../algorithm/03-recursion/2-summary.md)도 같은 관찰).
- 근본 대처: 입력 중첩 깊이에 상한을 둔다. 재귀를 명시적 스택으로 바꾼다.
- 임시 대처: 그 작업만 큰 스택 스레드(`new Thread(null, r, name, stackSize)`)에서 돌리거나 `-Xss`를 키운다. `stackSize`가 무시되는 플랫폼도 있으므로(Javadoc) 측정으로 확인한다. 기본값은 Linux/x64 1 MiB, Linux/AArch64 약 2 MiB(문서 2048 KB, 소스 2040 KB)라 같은 jar도 아키텍처마다 한계가 다르다.

### 9. cdecl 인자의 실제 주소 순서

- cdecl은 인자를 **뒤에서부터** push한다. 먼저 push한 n이 가장 높은 주소, 마지막 a가 가장 낮은 주소(반환 주소 바로 위)다.

```text
  높은 주소  n (0x10(%ebp))
             b (0xc(%ebp))
             a (0x8(%ebp))
             반환 주소 (0x4(%ebp))
             이전 ebp  (0x0(%ebp))  ← ebp
```

- 근거: `gcc -m32 -O0` 디스어셈블의 caller가 `push $0x2`(n) → `push $0x14`(b) → `push $0xa`(a) → `call`이다. callee `adder`는 `0x8(%ebp)`에서 a, `0xc(%ebp)`에서 b, `0x10(%ebp)`에서 n을 읽었다.
- 원고 같은 절의 두 번째 그림(위에서 n, b, a)이 이와 맞다.
