# language/22-ir-and-optimization — IR·SSA·인라이닝·데드 코드 제거·레지스터 할당 — 정리 (힌트)

## 해결하는 문제

AST(03)를 그대로 기계어로 옮기면 느리다. `gcc -O0`이 그에 가까운 모습이다. `-O0`도 내부 IR(GIMPLE·RTL)을 거치지만 최적화 패스를 대부분 끈다(실험: gcc 13.3 `-O0 -fdump-tree-gimple -fdump-rtl-expand`가 두 IR 덤프를 모두 만들었다).

```text
  int use_square(int a) { return square(a) + 1; }

  gcc 13.3 -O0                         gcc 13.3 -O2
    push %rbp ; mov %rsp,%rbp            imul %edi,%edi
    mov %edi,-0x4(%rbp)   ← 스택에 저장   lea 0x1(%rdi),%eax
    mov -0x4(%rbp),%eax   ← 다시 읽음     ret
    call square           ← 진짜 호출
    add $0x1,%eax ; leave ; ret
```

- 컴파일러는 소스와 기계어 사이에 **분석하기 쉬운 중간 표현**을 두고, 거기서 프로그램을 고쳐 쓴다.
  - *IR(Intermediate Representation, 중간 표현)*: 소스 언어도 기계어도 아닌, 최적화를 위해 컴파일러 안에서 쓰는 프로그램 표현.
  - *최적화*: 프로그램의 관찰 가능한 동작을 바꾸지 않으면서 더 빠르거나 작게 고쳐 쓰는 것.

쉬운 예: 요리 레시피 정리.
- 아무 데도 안 쓰는 재료 손질 단계를 지운다(데드 코드 제거).
- "물 200ml + 50ml"를 미리 "250ml"로 적는다(상수 접기).
- "소스 만들기(3쪽 참고)"를 그 자리에 풀어 쓴다(인라이닝).

똑같은 구조다.\
단, "관찰 가능한 동작"은 **언어 명세가 정의한 동작**이다. 명세가 정의하지 않은 동작(C의 UB)이나, 결과를 아무도 안 보는 계산은 컴파일러가 마음대로 바꿔도 된다. 실무 사고는 여기서 난다.

실무 예:
- 마이크로벤치마크가 0ns가 나왔다. 측정한 반복문이 통째로 사라졌다.
- C 코드의 `if (p == NULL)` 검사가 `-O2` 바이너리에서 없어졌다.
- 디버그 빌드(`-O0`)를 그대로 배포해 운영에서만 느리다.

## 동작·원리

### 1. IR — 3주소 코드와 제어 흐름 그래프

```text
  소스                       3주소 코드(한 명령에 연산 하나)
  int pick(int c,int a,int b)    t0 = (c != 0)
  { int x;                       br t0, THEN, ELSE
    if (c) x = a;              THEN: x = a ; jmp END
    else   x = b;              ELSE: x = b ; jmp END
    return x + 1; }            END:  t1 = x + 1 ; ret t1

  제어 흐름 그래프(CFG)
        [entry: t0 = c != 0; br]
           /               \
     [THEN: x = a]     [ELSE: x = b]
           \               /
        [END: t1 = x + 1; ret t1]
```

- *기본 블록(basic block)*: 중간에 들어오거나 나가는 점프가 없는, 한 줄로 쭉 실행되는 명령 묶음.
- *CFG(Control-Flow Graph)*: 기본 블록을 정점, 점프를 간선으로 둔 그래프([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).
- 프런트엔드(01~04)가 AST를 IR로 내리고, 미들엔드가 IR을 고치고, 백엔드가 기계어로 바꾼다(01의 파이프라인 그림).

### 2. SSA — 변수는 한 번만 대입한다

위 IR에서 `END`의 `x`는 어느 쪽 대입에서 왔나? 분석마다 이걸 따지면 번거롭다.

- *SSA(Static Single Assignment)*: 모든 변수가 프로그램 텍스트에서 **딱 한 번만** 대입되는 형태. 갈래가 합쳐지는 곳에는 φ(phi) 함수를 둔다.
  - *φ 함수*: "어느 선행 블록에서 왔느냐에 따라 값을 고른다"는 표시. LLVM LangRef: "`phi` 명령은 함수를 나타내는 SSA 그래프의 φ 노드를 구현한다."

실험(clang/LLVM 18.1.3) — 같은 `pick`의 LLVM IR 세 단계:

```text
  ① clang -O0 (-Xclang -disable-O0-optnone) : 지역 변수 = 메모리
     %x = alloca i32
     if.then:  %1 = load i32, ptr %a.addr ;  store i32 %1, ptr %x
     if.else:  %2 = load i32, ptr %b.addr ;  store i32 %2, ptr %x
     if.end:   %3 = load i32, ptr %x      ;  %add = add nsw i32 %3, 1

  ② opt-18 -passes=mem2reg : 메모리를 레지스터로 올리며 φ를 놓음 = SSA
     if.end:   %x.0 = phi i32 [ %a, %if.then ], [ %b, %if.else ]
               %add = add nsw i32 %x.0, 1

  ③ clang -O1 : 갈래 자체를 없앰
     %tobool.not = icmp eq i32 %c, 0
     %b.a = select i1 %tobool.not, i32 %b, i32 %a
     %add = add nsw i32 %b.a, 1
```

- LLVM Passes 문서: `mem2reg`는 "지배 경계(dominator frontier)로 φ 노드를 놓고 깊이 우선으로 load·store를 고쳐 쓰는, 표준 SSA 구성 알고리즘"이다.
- SSA에서는 "이 값을 누가 정의했나"가 이름 하나로 정해진다. 그래서 상수 전파·데드 코드 제거가 쉬워진다.

### 3. 데이터 흐름 분석 — 그래프 위에서 사실을 퍼뜨린다

```text
  살아 있는 변수(liveness) — 뒤에서 앞으로
   [x = a*12345]   ← x는 이후 어디서도 안 읽힘 → 죽은 대입 → 지운다(DCE)
   [return a+1]

  상수 전파 — 앞에서 뒤로
   [k = 6] → [m = k*7] → [return m]   ⇒  m = 42 ⇒ return 42
```

- *데이터 흐름 분석*: CFG의 각 지점에서 "이 변수는 상수인가", "이 값은 나중에 쓰이나" 같은 사실을 간선을 따라 퍼뜨려, 더 안 바뀔 때까지(고정점) 반복 계산하는 방법.
- 바뀐 블록만 다시 계산하려고 작업 목록(worklist, 큐)을 쓴다([data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)).

### 4. 대표 최적화 — 실험으로

환경: 호스트 Ubuntu 24.04, gcc 13.3.0, clang 18.1.3, objdump(GNU binutils). `opt.c`를 `-O0`/`-O2`로 컴파일해 `objdump -d`.

```c
static int square(int x) { return x * x; }
int use_square(int a) { return square(a) + 1; }   // 인라이닝 후보
int dead(int a) { int unused = a * 12345; (void)unused; return a + 1; }   // DCE 후보
int fold(void) { return 6 * 7; }                   // 상수 접기
```

| 함수 | gcc -O0 | gcc -O2 | 일어난 일 |
|---|---|---|---|
| `use_square` | `call square` + 스택 저장·읽기 | `imul %edi,%edi` · `lea 0x1(%rdi),%eax` | 인라이닝 + 레지스터 할당 |
| `dead` | `imul $0x3039,%eax,%eax` 후 스택에 저장 | `lea 0x1(%rdi),%eax` | 쓰이지 않는 곱셈 제거(DCE) |
| `fold` | `mov $0x2a,%eax` | `mov $0x2a,%eax` | 상수 접기 — **-O0에서도** 됨 |

- 관찰 — `fold`는 `-O0`에서도 이미 42(0x2a)였다. `6 * 7` 같은 상수식은 최적화 단계 전에, IR을 만들 때 이미 접힌 것으로 **해석**한다.
- `gcc -O2 -fopt-info-optimized`는 `opt.c:3:32: optimized:  Inlining square/0 into use_square/1.`을 출력했다. 어떤 최적화가 적용됐는지 컴파일러가 직접 알려 준다.
- GCC 13.3 문서: `-ftree-dce`(데드 코드 제거)는 `-O1`부터 켜진다. `-finline-small-functions`는 `-O2`부터 켜진다(호출 코드보다 작은 함수를 호출자에 넣음).
- *인라이닝*: 호출을 함수 몸체로 바꾸는 것. 호출 비용이 사라지는 것보다, **호출 너머까지 다른 최적화가 보이게 되는 것**이 더 크다. 위 `use_square`에서 인라이닝 뒤 `x*x+1`이 한 식이 됐다.

### 5. 레지스터 할당 — 그래프 색칠

```text
  동시에 살아 있는 값끼리 간선(간섭)        색 = 레지스터
      a ─── b                               a: rax  b: rdx
      │                                     c: rdx (b와 안 겹치니 재사용)
      c                                     색이 모자라면 → 스택에 내려놓음(spill)
```

- *간섭 그래프*: 값을 정점으로, 동시에 살아 있는 두 값을 간선으로 이은 그래프. 이웃끼리 다른 색(레지스터)을 칠하면 된다.
- 최적 색칠(최소 색 수 구하기)은 일반적으로 어렵다. 최적화 문제로는 NP-hard이고, "k색으로 칠할 수 있나"라는 판정 문제는 k≥3에서 NP-완전이다([algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md)). 그래서 휴리스틱을 쓴다. GCC 13.3 문서: 통합 레지스터 할당기(IRA)의 `-fira-algorithm`은 Chow의 우선순위 색칠(`priority`)과 Chaitin-Briggs 색칠(`CB`) 중 고르며, 지원하는 아키텍처에서는 CB가 기본이다.
- `-O0`은 디버깅이 쉽도록 변수를 스택에 둔다. 위 표의 `mov %edi,-0x4(%rbp)`·`mov -0x4(%rbp),%eax`가 그 흔적이다. 호출 규약과 스택 프레임은 [architecture/10](../../architecture/10-calling-convention-and-stack-frame/2-summary.md).

### 6. 반복문 전체가 공식 하나로 — 그리고 0ns 벤치마크

```c
for (long i = 0; i < N; i++) sum += i * (argc + 1);   // N = 200,000,000
```

실험(호스트, 각 6회 — 집필 3 + 점검 재실행 3):

```text
  gcc -O0 (결과 안 씀)   1312~1686 ms   (6.6~8.4 ns/iter)
  gcc -O0 (결과 printf)   698~1654 ms   (3.5~8.3 ns/iter, 호스트 잡음)
  gcc -O2 (결과 안 씀)   0.003~0.004 ms  → 반복문이 바이너리에 없다
  gcc -O2 (결과 printf)  0.003~0.004 ms  → 그래도 0ns
```

- 결과를 안 쓰면 반복문 전체가 DCE로 사라졌다. `main`의 기계어에 `now()` 두 번과 `printf`만 남았다.
- 결과를 **써도** 0ns였다. `-fdump-tree-sccp-details`가 이유를 보여 준다.

```text
  final value replacement:
    sum_22 = PHI <sum_16(3)>
   with expr: (long int) ((unsigned long) _8 * 19999999900000000)
```

  - 19,999,999,900,000,000 = N(N−1)/2다. 반복문을 "(argc+1) × 상수" 곱셈 하나로 바꿨다. 그 곱셈은 두 번째 `now()` **뒤**로 갔다(`-fdump-tree-optimized`).
  - GCC 13.3 문서 `-ftree-scev-cprop`: "최종 값 치환. 반복문에서 바뀐 변수의 탈출 값을 초기값과 반복 횟수만으로 정할 수 있으면 그 계산으로 바꾼다. `-O1` 이상 기본."
- 교훈: "결과를 출력했다"만으로는 부족하다. **측정 구간 안에서** 계산이 일어나야 하고, 입력이 컴파일 시점에 알 수 없어야 한다. Java에서 같은 문제와 JMH `Blackhole`은 [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md).

### 7. UB를 전제로 한 최적화

C 표준은 null 포인터 역참조를 정의하지 않는다(N1570 §6.5.3.2 ¶4: 잘못된 값의 포인터에 단항 `*`를 쓰면 정의되지 않은 동작, 각주 102: 잘못된 값에 null 포인터가 포함됨).

- *UB(Undefined Behavior, 정의되지 않은 동작)*: 표준이 아무 요구도 하지 않는 동작. 컴파일러는 "이런 일은 안 일어난다"고 가정하고 최적화해도 된다.

```c
int status_of(int *p) {
    int v = *p;              /* 값은 안 쓰지만 역참조는 했다 (p가 NULL이면 UB) */
    (void)v;
    if (p == 0) return -1;   /* "NULL이면 -1" 이라는 의도 */
    return 0;
}
```

```text
  gcc 13.3 -O2 기계어:    xor %eax,%eax ; ret          ← 검사도 역참조도 없음. 항상 0
  gcc -O2 -fno-delete-null-pointer-checks:  cmp $0x1,%rdi ; sbb %eax,%eax ; ret   ← 검사가 남음

  status_of(NULL) 실행 결과(같은 소스, 호스트)
    gcc -O0                                   SIGSEGV(exit 139)
    gcc -O2                                   0
    gcc -O2 -fno-delete-null-pointer-checks   -1
    clang 18 -O0                              SIGSEGV(exit 139)
    clang 18 -O2                              -1
```

- 관찰 — 같은 소스가 컴파일러·옵션에 따라 **죽거나, 0이거나, -1**이었다. 셋 다 표준 위반이 아니다. UB라서다.
- gcc의 추론(GCC 13.3 문서 `-fdelete-null-pointer-checks`): "이미 역참조한 포인터를 나중에 검사하면, 그 포인터는 null일 수 없다." 이 옵션은 대부분의 타깃에서 기본으로 켜져 있다. 그래서 `if (p == 0)`이 죽은 분기가 되고, 쓰이지 않는 `*p` 읽기도 DCE로 사라졌다.
- 역참조 결과를 쓰는 판(`int v = *p; if (!p) return -1; return v;`)은 gcc·clang `-O2` 모두 `mov (%rdi),%eax ; ret`만 남겼다(검사 삭제). 이 판은 실험한 네 빌드(gcc `-O0`·`-O2`·`-O2 -fno-delete-null-pointer-checks`, clang `-O2`) 모두 NULL에서 SIGSEGV였다.
- UB 목록·sanitizer·언어별 안전 경계는 [language 20](../20-undefined-behavior-and-memory-safety/2-summary.md), 정수 오버플로 UB의 최적화 사례는 [architecture/02](../../architecture/02-integer-overflow-and-truncation/2-summary.md).

### 8. 같은 일을 실행 중에 — JIT

- HotSpot C2·V8도 같은 미들엔드 최적화(인라이닝·DCE·탈출 분석·레지스터 할당)를 **실행 중**에 한다(01). 다른 점은 프로파일을 근거로 "이 분기는 안 탄다"고 **가정**할 수 있고, 가정이 깨지면 역최적화로 되돌린다는 것이다.
- 그래서 Java 마이크로벤치마크에서도 0ns가 나온다. 계층 컴파일·역최적화는 [language 23](../23-jit-tiered-compilation-and-warmup/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **제어 흐름 그래프** — 기본 블록 = 정점, 점프 = 간선([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)). 반복문 찾기·지배 관계는 그래프 탐색([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)).
- **데이터 흐름 분석** — 간선을 따라 사실을 전파해 고정점까지 반복. 작업 목록은 큐([data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)). 집합 연산은 비트셋으로([data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)).
- **SSA 구성** — 지배 경계에 φ를 놓는 알고리즘(LLVM `mem2reg` 문서: "표준 SSA 구성 알고리즘", "pruned SSA").
- **그래프 컬러링** — 레지스터 할당. Chaitin-Briggs·우선순위 색칠(GCC IRA). 최적해 구하기는 NP-hard라 휴리스틱(LLVM 기본 할당기는 색칠이 아니라 라이브 구간을 나누는 Greedy — LLVM Code Generator 문서)([algorithm/40-complexity-p-np](../../algorithm/40-complexity-p-np/2-summary.md)).
- **귀납 변수·스칼라 진화** — 반복문 변수의 값을 "초기값 + 단계 × 횟수" 식으로 표현해 최종 값 치환(`-ftree-scev-cprop`).

## 적용 — 풀어나가는 법

1. **"컴파일러가 실제로 무엇을 만들었나"를 본다.**

   ```bash
   gcc -O2 -c f.c && objdump -d --no-show-raw-insn f.o       # 기계어
   gcc -O2 -S -o - f.c                                       # 어셈블리
   gcc -O2 -fdump-tree-optimized -c f.c                      # 최적화 후 GIMPLE(f.c.*.optimized)
   gcc -O2 -fopt-info-optimized -c f.c                       # 적용된 최적화 요약
   clang -O1 -S -emit-llvm -fno-discard-value-names -o - f.c # LLVM IR
   ```

2. **벤치마크가 너무 빠르면 먼저 사라졌는지 의심한다.**
   - 입력을 실행 시점 값으로(인자·파일·난수), 결과를 측정 구간 안에서 쓰게(합산 후 출력, `volatile` 싱크) 한다.
   - N을 2배로 늘려 시간이 2배가 되는지 본다. 그대로면 반복문이 지워졌거나 공식 하나로 바뀌었을 수 있다(6절 실험은 후자). 생성 코드(`objdump -d`·`-fdump-tree-optimized`)로 확인한다.
   - Java는 JMH와 `Blackhole`(reliability/38).
3. **UB를 "동작하니 괜찮다"로 넘기지 않는다.**
   - 검사는 역참조 **앞**에 둔다.
   - 테스트·CI에서 `-fsanitize=address,undefined`로 돌린다. 실험(gcc 13.3)에서 `deref_then_check(NULL)`은 `runtime error: load of null pointer of type 'int'`와 `AddressSanitizer: SEGV on unknown address 0x000000000000`을 냈다.
   - 의존하는 코드가 많으면 `-fno-delete-null-pointer-checks` 같은 옵션으로 가정을 끌 수 있다. 근본 해결은 아니다.
4. **배포 바이너리의 최적화 수준을 확인한다.** `-g`로 빌드했다면 `readelf --debug-dump=info a.out | grep -m1 DW_AT_producer`가 컴파일 옵션을 보여 준다. 실험: `GNU C17 13.3.0 -mtune=generic -march=x86-64 -g -O0 …`.

## 장애 시나리오와 대처

### 1. null 검사가 있는데도 죽거나, 검사가 무시됨 (⚠)

- **현상**: 코드에 `if (p == NULL)`이 분명히 있는데, NULL이 들어오면 크래시하거나 엉뚱한 값을 돌려준다. 디버그 빌드와 릴리스 빌드의 결과가 다르다.
- **보이는 형태**: 릴리스 바이너리 `objdump`에 비교 명령(`test`/`cmp`)이 없다. 실험의 `status_of(NULL)`은 gcc `-O0` SIGSEGV, gcc `-O2` 0, clang `-O2` -1.
- **원인**: 검사보다 역참조가 먼저다. 그 역참조는 NULL이면 UB이므로, 컴파일러는 "여기 왔으면 NULL이 아니다"라고 보고 검사를 지운다(gcc `-fdelete-null-pointer-checks`, 대부분 타깃 기본).
- **대처**: 검사를 역참조 앞으로 옮긴다. UBSan·ASan으로 CI를 돌린다. 프로젝트 단위로 가정을 끄는 옵션은 차선책이다.

### 2. 마이크로벤치마크가 0ns (⚠)

- **현상**: 최적화를 켜자 측정값이 0ns 또는 N과 무관한 상수가 나온다.
- **보이는 형태**: N을 늘려도 시간이 같다. 기계어에 반복문이 없다. 실험에서 `-O2`는 결과를 출력해도 0.003~0.004ms였다.
- **원인**: 결과를 안 쓰는 계산은 DCE로, 닫힌 식이 있는 반복문은 최종 값 치환으로 사라진다. 그 곱셈마저 측정 구간 밖으로 옮겨졌다.
- **대처**: 입력을 실행 시점 값으로, 결과를 측정 구간 안에서 소비하게 한다. 기계어를 확인한다. Java는 JMH(reliability/38).

### 3. 플래그를 기다리는 반복문이 끝나지 않음

- **현상**: 다른 스레드가 `stop = 1`로 바꿨는데 대기 루프가 영원히 돈다. `-O0`에서는 멀쩡하다.
- **보이는 형태**: CPU 한 코어가 100%. 기계어(gcc 13.3 `-O2`):

  ```text
  wait_for_stop:  mov 0x0(%rip),%eax   ← stop을 딱 한 번 읽음
                  test %eax,%eax
                  jne  ret
           here:  jmp  here            ← 자기 자신으로 점프 = 무한 루프
  ```

- **원인**: `int stop;`은 일반 변수다. 동기화 없이 다른 스레드가 쓰는 것은 데이터 레이스이고, C11은 데이터 레이스를 UB로 정한다(N1570 §5.1.2.4 ¶25). 그래서 컴파일러는 반복문 안에서 `stop`이 안 바뀐다고 보고 읽기를 반복문 밖으로 뺐다.
- **대처**: C11 `_Atomic`/`atomic_load`, Java `volatile`·`AtomicBoolean`처럼 언어 메모리 모델이 보장하는 도구를 쓴다. 하드웨어 쪽은 [architecture/14](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md), 언어 규칙은 [language 13](../13-language-memory-model/2-summary.md).

### 4. 디버그 빌드가 운영에 나감

- **현상**: 같은 코드가 운영에서만 수 배 느리다.
- **보이는 형태**: 핫 함수 기계어가 스택 저장·읽기투성이(`mov %edi,-0x4(%rbp)`), 작은 함수도 `call`. `DW_AT_producer`에 `-O0`.
- **원인**: 빌드 스크립트·Dockerfile이 디버그 설정을 썼다. 실험의 반복문은 `-O0`에서 반복당 3.5~8.4ns였다.
- **대처**: 릴리스 빌드 옵션을 CI에서 검사한다(`DW_AT_producer`나 `-frecord-gcc-switches`). 디버깅용은 `-Og` 등 별도 프로필로 둔다.

## 핵심 문장

- 컴파일러는 AST를 IR로 내려 CFG 위에서 분석·최적화한다. SSA는 "변수 하나 = 대입 하나"로 만들고 갈래가 합쳐지는 곳에 φ를 둔다.
- 데이터 흐름 분석이 "이 값은 상수다", "이 값은 안 쓰인다"를 알아내고, 상수 접기·DCE·인라이닝이 그걸로 코드를 줄인다.
- GCC IRA 같은 레지스터 할당기는 간섭 그래프 색칠을 쓴다(LLVM 기본은 Greedy). `-O0`은 변수를 스택에 두어 느리다.
- 컴파일러는 명세가 정의한 동작만 지킨다. 아무도 안 쓰는 결과는 사라지고(0ns 벤치마크), UB 이후의 검사는 지워질 수 있다.
- UB 코드의 결과는 "이 컴파일러·이 옵션에서 관찰된 것"일 뿐이다. 같은 소스가 gcc -O0에서 죽고, gcc -O2에서 0, clang -O2에서 -1이었다.

## 관련 주제·근거

- 선행
  - [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md) — 이름·타입이 정해진 AST가 IR의 입력
  - [01-compile-interpret-jit](../01-compile-interpret-jit/2-summary.md) — 파이프라인 전체 그림
- 후속·연결
  - [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md)(UB·메모리 안전) · [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md)(JIT 계층 컴파일·역최적화) · [25-lto-pgo-and-binary-size](../25-lto-pgo-and-binary-size/2-summary.md)(LTO·PGO·바이너리 크기)
  - [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) — JIT의 DCE·상수 접기와 JMH
  - [architecture/02-integer-overflow-and-truncation](../../architecture/02-integer-overflow-and-truncation/2-summary.md) · [architecture/10-calling-convention-and-stack-frame](../../architecture/10-calling-convention-and-stack-frame/2-summary.md) · [architecture/14-cache-coherence-and-memory-ordering](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md) · [architecture/18-pipelining-and-branch-prediction](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — UB가 공격으로 이어지는 쪽
  - 문법: [c/syntax/19 void 포인터·null](../../../languages/c/syntax/19-void-pointer-null-pointer-and-null/2-summary.md) · [c/syntax/39 inline](../../../languages/c/syntax/39-inline-and-c-inline-rules/2-summary.md) · [c/syntax/32 volatile이 실제로 보장하는 것](../../../languages/c/syntax/32-what-volatile-actually-guarantees/2-summary.md)
- 문서·표준
  - GCC 13.3 Optimize Options — `-O0`, `-ftree-dce`(-O1), `-finline-small-functions`(-O2), `-ftree-scev-cprop`(최종 값 치환, -O1), `-fdelete-null-pointer-checks`(대부분 타깃 기본), `-fira-algorithm`(priority·CB) <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html>
  - LLVM Language Reference — SSA 기반 표현, `phi` 명령 <https://llvm.org/docs/LangRef.html> · LLVM Passes — `mem2reg` <https://llvm.org/docs/Passes.html>
  - C11 표준 초안 N1570 §6.5.3.2 ¶4와 각주 102(null 포인터 역참조), §5.1.2.4 ¶25(데이터 레이스는 UB) <https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf>
  - Aho 외 『Compilers』(Dragon Book) 8·9장 `[?]`
- 실험 목록
  - `opt.c` gcc 13.3 `-O0`/`-O2` objdump(인라이닝·DCE·상수 접기·null 검사 삭제), clang 18 `-O2`, gcc `-fno-delete-null-pointer-checks` — 호스트 Ubuntu 24.04
  - `-O0`도 IR을 거치는지: gcc 13.3 `-O0 -fdump-tree-gimple -fdump-rtl-expand`로 `.gimple`·`.expand` 덤프 생성 확인(`6*7`은 GIMPLE에서 이미 42) — 호스트
  - `ssa.c` clang 18 `-O0`(optnone 해제) → `opt-18 -passes=mem2reg` → clang `-O1` LLVM IR
  - `bench.c` 반복문 2억 회, gcc `-O0`/`-O2` × 결과 사용 여부, 각 6회(집필 3 + 점검 3), `-fdump-tree-sccp-details`·`-fdump-tree-optimized`
  - `ub2.c` `status_of(NULL)` gcc/clang × `-O0`/`-O2`/`-fno-delete-null-pointer-checks` 실행, `-fsanitize=address,undefined` 보고
  - `spin.c` 플래그 대기 루프 gcc `-O2` 기계어 · `DW_AT_producer`로 빌드 옵션 확인
