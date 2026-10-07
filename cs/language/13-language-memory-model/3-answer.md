# language/13-language-memory-model — 정답

## 정답

### 1. 언어 모델이 필요한 이유

- 순서를 바꾸는 주체: 컴파일러(JIT·gcc·clang의 재정렬·레지스터 캐싱), CPU(저장 버퍼 등), 그리고 둘의 조합.
- 프로그래머가 CPU마다(x86·ARM) 다른 규칙과 컴파일러 최적화를 다 따질 수 없다. 언어가 "가능한 결과"를 정하고, 구현(컴파일러·런타임)이 어떤 하드웨어에서든 그 계약을 지키게 한다.

### 2. happens-before 그림

```text
  A: data = 42  ─po→  ready = true (volatile 쓰기)
                              │ synchronizes-with
                              ▼
  B:                     ready 읽기(true를 봄)  ─po→  r = data
  hb(data=42, r=data) — 추이적 폐포
```

- 간선 종류(JLS 17.4.4): 모니터 unlock → 이후 lock, volatile 쓰기 → 이후 읽기, `Thread.start()` → 시작된 스레드의 첫 동작, 스레드 마지막 동작 → 종료 감지(`join`·`isAlive`), 기본값 쓰기 → 각 스레드 첫 동작, interrupt → 인터럽트 감지.

### 3. hb ≠ 실행 순서

- 틀리다. JLS 17.4.5: hb 관계가 있다고 구현이 꼭 그 순서로 실행해야 하는 것은 아니고, 결과가 합법적 실행과 같으면 재정렬해도 된다. hb는 "보임"의 약속이다.

### 4. race의 정의와 보장

- Java: 충돌 접근 두 개가 hb로 정렬되지 않으면 race(17.4.5). race가 있어도 의미가 정의된다 — "a data race cannot cause incorrect behavior such as returning the wrong length for an array". 이유는 안전·보안(POPL 2005: 틀린 코드도 타입 안전을 깨면 안 된다).
- C11: 다른 스레드의 충돌 동작, 하나 이상 비원자적, 서로 hb 아님 → "Any such data race results in undefined behavior"(N1570 5.1.2.4 ¶25). 단일 스레드 최적화를 거의 모두 허용하기 위해서다(¶26 NOTE 12).
- race가 없을 때: Java는 순차 일관성을 준다(DRF-SC, JLS 17.4.5). C11은 뮤텍스와 `memory_order_seq_cst` 연산만 쓰는 race 없는 프로그램에 한해 순차 일관성을 준다(¶26 NOTE 12). 더 약한 메모리 순서(acquire/release·relaxed)를 쓰면 race가 없어도 순차 일관이 아닐 수 있다.

### 5. SB 리트머스 (실험 1, 5회)

| 모드 | (0,0) |
|---|---|
| plain | 150,683~264,441 |
| volatile | 0 |
| acquire/release | 117,611~354,723 |
| opaque | 124,715~199,860 |
| release + fullFence + acquire | 0 |

- `-Xint` plain(20만 회): 24,164~27,772 — JIT 없이도 나왔다. 어떤 끼워 넣기로도 (0, 0)은 안 나오고 바이트코드도 저장 → 읽기 순서 그대로이니(`javap -c`), `-Xint` 실행에서는 CPU 저장 버퍼가 원인이라는 해석이다(JIT 실행에 컴파일러 재정렬이 섞였는지는 가르지 못했다).
- 0은 관찰일 뿐이고, volatile에서 (0,0)이 금지라는 근거는 명세(volatile 동작의 전체 순서)다.

### 6. MP vs SB

- `VarHandle` 문서: acquire 읽기와 그 뒤 접근은 짝 맞는 release 쓰기와 그 앞 접근 뒤에 정렬된다. MP는 "앞의 쓰기(data) → release(ready)" ∥ "acquire(ready) → 뒤의 읽기(data)"라 이 규칙 하나로 된다.
- SB는 같은 스레드 안의 **저장 → 다른 변수 읽기** 순서가 필요하다. release는 "앞의 접근"을, acquire는 "뒤의 접근"을 묶을 뿐, release 쓰기 뒤의 acquire 읽기가 앞서 보이는 것을 막지 않는다. volatile 동작끼리의 전체 순서(또는 전체 펜스)가 있어야 막힌다.

### 7. C 깃발 루프 (실험 2)

- `gcc -O0`: `data=42`로 끝남.
- `gcc -O2`: 3회 모두 3초 타임아웃. objdump: `ready`를 한 번 읽고(`mov ... # ready`), 0이면 `jmp 10f5`로 자기 자신에게 점프. race가 UB라 컴파일러가 "다른 스레드가 안 바꾼다"고 보고 읽기를 루프 밖으로 뺐다(이 컴파일러·옵션에서 관찰).
- `clang -O1 -fsanitize=thread`: `WARNING: ThreadSanitizer: data race`(쓰기 producer, 읽기 main), exit 66. atomic + release/acquire 판은 보고 없음.

### 8. final과 DCL

- 조건(JLS 17.5): final 필드를 생성자에서 설정하고, 생성자가 끝나기 전에 `this`를 다른 스레드가 볼 곳에 쓰지 않는다. 그러면 race로 참조를 받아도 final 필드의 올바른 값을 본다.
- DCL 고치기: (1) 참조를 `volatile`, (2) 대상이 모든 필드 final인 불변 객체 + 락 밖 읽기를 지역 변수로 한 번만, (3) 클래스 초기화를 쓰는 holder 관용구. 세부는 [architecture/14 §7](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md).

### 9. acquire/release "최적화" 뒤 상호 배제 실패

- 원인: "내 깃발 세우기 → 상대 깃발 읽기"는 SB 패턴이다. release/acquire는 저장 → 읽기 순서를 약속하지 않아, 둘 다 상대 깃발을 0으로 읽고 들어갈 수 있다(실험 1에서 acquire/release (0,0) 약 6~18%).
- 대처: volatile로 되돌리거나 저장과 읽기 사이에 `VarHandle.fullFence()`. 근본적으로는 직접 만든 상호 배제 대신 락.

### 10. 결정 순서와 `volatile` 카운터

- 순서: 공유되나 → 쓰기가 있나 → 불변이면 final / 플래그·참조 교체 하나면 volatile·`AtomicReference` / 읽고-고치고-쓰기면 `Atomic*`·`LongAdder` / 여러 변수 함께면 락 / acquire/release는 SB 패턴이 없음을 증명할 수 있을 때만.
- `volatile int++`는 읽기·더하기·쓰기 세 단계다. volatile은 각 읽기·쓰기를 보이게 할 뿐 셋을 원자적으로 묶지 않아 갱신이 유실된다([architecture/14 실험 3](../../architecture/14-cache-coherence-and-memory-ordering/2-summary.md): 2천만 중 약 1,593만~1,958만).
