# architecture/14-cache-coherence-and-memory-ordering — 정답

## 정답

### 1. 일관성 vs 순서

- 캐시 일관성: **한 주소**의 사본들에 대해 모든 코어가 같은 쓰기 순서를 본다. 하드웨어 프로토콜(MESI 등)이 맡는다.
- 메모리 순서: **서로 다른 주소들**의 읽기·쓰기가 다른 코어에 어떤 순서로 보일 수 있는지. 아키텍처(x86-TSO, ARM)와 언어(JMM)가 정한다.
- 틀린 이유: 쓰기는 캐시에 닿기 전에 저장 버퍼에 머문다. 그 사이 뒤의 다른 주소 읽기가 먼저 실행된다. 일관성은 지켜져도 "쓰기 → 다른 주소 읽기" 순서는 어긋난다(3번).

### 2. MESI

| 상태 | 뜻 | 내가 쓰려면 |
|---|---|---|
| M | 고쳤고 나만 가짐 | 그냥 씀 |
| E | 안 고쳤고 나만 가짐 | 조용히 M으로 |
| S | 안 고쳤고 남도 가질 수 있음 | RFO로 남의 사본 무효화 후 M |
| I | 무효 | 읽어 와야 함 |

```text
  E 라인에 쓰기:  [E] ──로컬 쓰기──> [M]           버스 알림 없음
  S 라인에 쓰기:  [S] ──RFO 보냄──> 다른 코어 [S]→[I] ──> 내 라인 [M]
```

- RFO가 필요한 때: 남이 사본을 가졌을 수 있는 라인에 쓸 때, 남의 M 라인을 쓰려고 가져올 때. Drepper §3.3.4는 E → M이 S → M보다 훨씬 빠르다고 적는다.

### 3. SB 리트머스

- 나온다. 이 호스트(cpu2·cpu4, 컴파일러 펜스만)에서 200만 회 중 **9~4905회**(15번 실행). seq_cst 펜스(gcc가 `lock orq $0x0,(%rsp)`로 냄)를 넣으면 **0회**(8번 실행).
- 이유: 각 코어의 `x=1`·`y=1`이 저장 버퍼에 머무는 동안 뒤의 읽기가 캐시에서 상대의 옛 값 0을 읽는다. x86-TSO 논문이 이 결과를 허용 상태로 제시한다. 잠금 명령·`mfence`는 저장 버퍼를 비운 뒤 읽게 한다.

### 4. 배리어

- x86에서는 일반 프로그램 메모리 기준으로 **StoreLoad만** 명령이 필요하다(Cookbook 표: LoadLoad·LoadStore·StoreStore는 no-op, StoreLoad는 mfence/locked 명령. 표 아래 Notes: write-combining 메모리의 StoreStore `sfence`, streaming SSE2 명령의 LoadLoad `lfence`는 예외).
- TSO는 쓰기끼리·읽기끼리·읽기 → 쓰기 순서를 지키고, "쓰기 → 뒤의 다른 주소 읽기"만 저장 버퍼 때문에 어긋날 수 있다.
- ARM(v7+)은 Cookbook 표에서 네 가지 모두 `dmb` 계열이다(LoadLoad·LoadStore 칸은 "see below" — 의존 관계로 대신할 수 있는 경우를 따로 적는다). 그래서 x86에서 맞던 data race 코드가 ARM에서 깨질 수 있다.

### 5. 종료 플래그

- 일반 `boolean`: **10회 중 9회 안 끝남**(재실행 첫 회는 JIT 전이라 끝났다는 해석). `volatile`: **10/10회 끝남**(JDK 21.0.12).
- 원인은 컴파일러(JIT)다. 루프 안 읽기를 한 번으로 줄여 값이 레지스터에 고정된다(JLS §17.3의 `this.done` 예). 하드웨어 캐시는 MESI로 일관되다. java/33 노트에서 `-Xint`면 일반 필드도 멈췄다.
- 관찰이지 보장이 아니다. JMM은 안 멈추는 것을 허용할 뿐이다.

### 6. 카운터

- `volatile int++`: 안 된다. 15,928,396~19,578,627(6회, 기대 20,000,000). 읽기·더하기·쓰기 세 단계가 원자적이지 않다.
- `AtomicInteger`: 6회 모두 20,000,000.
- x86 명령(gcc `-O2`, `objdump`): 원자적 증가 `atomic_fetch_add` → `lock xadd`, CAS `atomic_compare_exchange_strong` → `lock cmpxchg`. `lock`은 라인을 M으로 잡은 채 갱신을 끝낸다.

### 7. DCL

```text
  스레드 A (락 안)                       스레드 B
  17: new           ← 할당, port=0
  24: putstatic     ← 공개가 먼저 보이면  ─>  getstatic: instance != null → 락 없이 반환
  21: invokespecial ← port=8080 (늦게 보임)    b.port → 0
```

- 바이트코드 순서는 new → invokespecial → putstatic이지만, 컴파일러·(약한 순서 CPU의) 하드웨어가 생성자 안 쓰기와 공개를 바꿔 보이게 할 수 있다(DCL 선언문).
- JDK5+ 해법: ① `instance`를 `volatile`로 ② 홀더 클래스 관용구(`static final` 필드를 가진 중첩 클래스) ③ `enum` 싱글턴. 모든 필드가 `final`인 불변 객체면 `volatile` 없이도 된다(선언문·JLS §17.5). 단 락 밖에서 `instance`를 한 번만 읽어 지역 변수로 반환해야 한다 — 위 코드처럼 두 번 읽으면 두 번째 읽기가 `null`을 볼 수 있다(JLS §17.4.5).
- 이 호스트(x86)에서는 재현하지 않았다. 문서 근거로 대신했다.

### 8. happens-before

- 프로그램 순서(한 스레드 안) + synchronizes-with(volatile 쓰기 → 동기화 순서상 뒤의 같은 변수 읽기 전부, 모니터 해제 → 뒤의 획득, `start`, `join` 등, JLS §17.4.4)를 이어 붙인 부분 순서(§17.4.5). §17.4.5는 여기에 "생성자 끝 → 그 객체 finalizer 시작" 간선도 따로 둔다.

```text
  A: data = 42  ─(프로그램 순서)→  ready = true (volatile 쓰기)
                                         │ synchronizes-with
  B:                               if (ready) (volatile 읽기, true를 봄) ─(프로그램 순서)→ r = data  → 42 보장
```

- HotSpot(x86)은 필요한 StoreLoad를 `lock add [esp-C], 0`으로 구현한다(`assembler_x86.cpp` `Assembler::membar` — "We only have to handle StoreLoad"). 캐시를 플러시하는 명령이 아니다.

### 9. 안 내려가는 인스턴스

- 스레드 덤프(`jcmd <pid> Thread.print`): 워커가 `RUNNABLE`로 같은 루프 줄에 있고, 락 대기는 없다. CPU 한 코어 100%.
- 코드: 종료 조건 `while (running)`의 `running`이 일반 필드인지, 다른 스레드가 바꾸는지.
- 고침: `volatile boolean` 또는 `AtomicBoolean`, 또는 `Thread.interrupt()` + `isInterrupted()`. 블로킹 대기가 있으면 인터럽트 쪽이 낫다.

### 10. x86 통과, ARM 실패

- 가설: 락 없이 "데이터 쓰기 → 플래그 쓰기 / 플래그 읽기 → 데이터 읽기"를 하는 data race. x86(TSO)은 StoreStore·LoadLoad 순서를 하드웨어가 지켜 우연히 맞았고, ARM은 지키지 않는다.
- 대처: 공유 변수 쌍마다 happens-before를 만든다(`volatile` 플래그, 락, `Atomic*`, `java.util.concurrent` 큐). CI에 ARM 실행을 추가한다. 테스트 통과는 증명이 아니다(3번처럼 200만 번에 9번일 수도 있다).
