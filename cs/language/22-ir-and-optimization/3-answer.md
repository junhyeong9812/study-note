# language/22-ir-and-optimization — 정답

## 정답

### 1. IR을 두는 이유

- 분석이 쉬운 형태가 필요하다. AST는 소스 모양이라 "이 값은 어디서 정의됐나·나중에 쓰이나"를 따지기 어렵다. 3주소 코드·CFG·SSA는 그 질문에 바로 답한다.
- 재사용: 언어 N개 × CPU M개를 N개의 프런트엔드 + M개의 백엔드로 만든다. 최적화(미들엔드)는 하나만 만든다(LLVM).
- "관찰 가능한 동작"은 **언어 명세**가 정한다. C라면 표준이 정의한 동작이다. 명세가 정의하지 않은 동작(UB)과, 아무도 관찰하지 않는 결과는 바뀌어도 위반이 아니다.

### 2. CFG와 SSA

```text
  [entry: c != 0 ? → THEN : ELSE]
     /                 \
  [THEN]             [ELSE]
     \                 /
  [END: x.0 = φ(a ← THEN, b ← ELSE); add = x.0 + 1; ret add]
```

- SSA는 `x`를 대입마다 다른 이름으로 나누고, 합쳐지는 `END`에서 φ로 고른다. 실험(`opt-18 -passes=mem2reg`): `%x.0 = phi i32 [ %a, %if.then ], [ %b, %if.else ]`.
- `clang -O1`은 갈래를 아예 없앴다. `%b.a = select i1 %tobool.not, i32 %b, i32 %a`. 조건에 따라 값을 고르는 명령 하나다.

### 3. `-O0` vs `-O2`

| 함수 | gcc -O0 | gcc -O2 |
|---|---|---|
| `use_square` | `call square`, 인자를 스택에 저장·재로드 | `imul %edi,%edi` + `lea 0x1(%rdi),%eax`(인라이닝) |
| `dead` | `imul $0x3039,…` 후 스택에 저장 | `lea 0x1(%rdi),%eax`(곱셈 제거) |
| `fold` | `mov $0x2a,%eax` | `mov $0x2a,%eax` |

- `-O0`에서도 되는 것: `fold`의 상수 접기(42). 상수식은 IR을 만들 때 이미 접힌 것으로 해석한다.
- 실험: gcc 13.3.0 + `objdump -d`. `-fopt-info-optimized`는 `Inlining square/0 into use_square/1.`을 출력했다.

### 4. 레지스터 색칠

- a–b, a–c 간섭: a에 색1, b와 c에 색2(b·c는 서로 간섭이 없어 같은 레지스터를 써도 된다). 두 색으로 충분하다.
- 색이 모자라면 일부 값을 메모리(스택)에 내려놓는다(spill). 쓸 때마다 읽고 써야 해 느려진다.
- GCC 13.3 IRA: `-fira-algorithm=priority`(Chow의 우선순위 색칠) 또는 `CB`(Chaitin-Briggs). 지원하는 아키텍처에서는 CB가 기본이다. 최소 색 수를 구하는 최적 색칠은 NP-hard(k색 판정은 k≥3에서 NP-완전)라 휴리스틱을 쓴다.

### 5. 0ns 벤치마크

- 실측(호스트, 각 6회): `-O2` 결과 안 씀 0.003~0.004ms, 결과 출력 0.003~0.004ms. 둘 다 사실상 0ns/iter.
- 안 쓸 때: 결과를 안 쓰는 계산 전체가 DCE로 사라졌다(`main`에 `now()` 두 번과 `printf`만).
- 써도 0인 이유: GCC의 최종 값 치환(`-ftree-scev-cprop`, `-O1` 이상 기본). 반복문의 `sum` 최종값을 `(argc+1) × 19999999900000000`(= N(N−1)/2) 곱셈 하나로 바꿨다(`-fdump-tree-sccp-details`의 `final value replacement`). 그 곱셈도 두 번째 `now()` 뒤에 있었다.
- 비교: `-O0`은 반복당 3.5~8.4ns였다.

### 6. `status_of(NULL)`

| 빌드 | 결과 |
|---|---|
| gcc -O0 | SIGSEGV(exit 139) — 역참조를 실제로 함 |
| gcc -O2 | 0 — 기계어가 `xor %eax,%eax; ret` |
| gcc -O2 -fno-delete-null-pointer-checks | -1 — `cmp $0x1,%rdi; sbb %eax,%eax` |
| clang 18 -O2 | -1 |

- "맞는" 결과는 없다. NULL 역참조는 UB이므로 표준은 어떤 결과도 요구하지 않는다. 넷 다 "이 컴파일러·이 옵션에서 관찰된 결과"일 뿐이다.

### 7. null 검사 삭제의 추론

- N1570 §6.5.3.2 ¶4: 잘못된 값의 포인터에 단항 `*`를 쓰면 UB. 각주 102: 잘못된 값에 null 포인터가 포함된다.
- GCC 13.3 `-fdelete-null-pointer-checks`(대부분 타깃 기본): 이미 역참조한 포인터를 나중에 검사하면, 그 포인터는 null일 수 없다고 본다. 그래서 `if (p == 0)`이 죽은 분기가 되어 지워진다. 결과를 안 쓰는 `*p` 읽기도 DCE로 사라졌다.
- 고칠 것: 검사를 역참조 **앞**에 둔다. CI에서 `-fsanitize=address,undefined`로 돌린다. 실험의 보고는 `runtime error: load of null pointer of type 'int'`와 `AddressSanitizer: SEGV on unknown address 0x000000000000`였다.

### 8. 끝나지 않는 대기 루프

- 기계어(gcc 13.3 `-O2`): `mov 0x0(%rip),%eax`로 `stop`을 한 번 읽고, 0이면 `jmp` 자기 자신. 반복문 안에 메모리 읽기가 없다.
- 원인: `stop`이 일반 변수다. 동기화 없이 다른 스레드가 쓰면 데이터 레이스이고 C11에서 UB다(N1570 §5.1.2.4 ¶25). 컴파일러는 이 스레드 안에서 `stop`이 안 바뀐다고 보고 읽기를 반복문 밖으로 뺐다.
- 고침: C11 `_Atomic int stop`과 `atomic_load`/`atomic_store`, Java는 `volatile boolean`·`AtomicBoolean`. `volatile`(C)은 스레드 간 동기화를 보장하지 않는다([c/syntax/32](../../../languages/c/syntax/32-what-volatile-actually-guarantees/2-summary.md)).

### 9. 디버그 빌드 확인

- `-g`가 있었다면 `readelf --debug-dump=info a.out | grep -m1 DW_AT_producer`. 실험 출력: `GNU C17 13.3.0 -mtune=generic -march=x86-64 -g -O0 …`.
- 빌드 시 `-frecord-gcc-switches`를 켜 두면 옵션이 바이너리에 남는다.
- 기계어 흔적: 함수마다 `push %rbp; mov %rsp,%rbp`, 인자를 스택에 저장했다 다시 읽기(`mov %edi,-0x4(%rbp)`·`mov -0x4(%rbp),%eax`), 작은 함수도 `call`.

### 10. JIT가 더 하는 것

- 실행 프로파일을 근거로 **가정**을 넣는다. "이 분기는 안 탄다", "이 호출 지점의 타입은 하나뿐이다" 같은 가정 아래 더 공격적으로 인라이닝·제거한다.
- 대가: 가정이 깨지면 역최적화로 인터프리터·낮은 단계로 돌아가 다시 컴파일해야 한다. 컴파일 자체도 실행 중 CPU를 쓴다(워밍업, 01·23).
- 같은 이유로 Java 마이크로벤치마크도 DCE·상수 접기로 0ns가 나온다. DCE는 결과를 JMH `Blackhole`에 넘겨(또는 반환해) 막는다. 상수 접기는 입력을 `@State` 객체의 final 아닌 필드에서 읽어 막는다(JMH `JMHSample_10_ConstantFold`)([reliability/38](../../reliability/38-microbenchmarking/2-summary.md)).
