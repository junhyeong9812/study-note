# architecture/19-out-of-order-and-speculation — 비순차·투기 실행과 부채널: 빨리 하려고 미리 한 일이 흔적을 남긴다 — 정리 (힌트)

## 해결하는 문제

프로그램 순서대로 하나씩 기다리며 실행하면, 느린 명령 하나(메모리 읽기 등) 뒤의 명령들이 줄줄이 논다.

```text
  순서대로만 실행 (in-order)
  load  r1 ← [메모리]      ████████████████ (오래 걸림)
  add   r2 ← r1 + 1                         █      ← r1을 기다려야 함 (맞음)
  mul   r3 ← r4 * r5                         █     ← r1과 무관한데도 기다림 (낭비)

  비순차 실행 (out-of-order)
  load  r1 ← [메모리]      ████████████████
  mul   r3 ← r4 * r5        █                      ← 준비된 명령부터 먼저 실행
  add   r2 ← r1 + 1                         █
  결과 반영(retire)은 프로그램 순서대로: load → add → mul
```

- *비순차 실행(out-of-order execution)*: 입력이 준비된 명령부터 실행하고, 결과는 프로그램 순서대로 확정하는 방식.
- *투기 실행(speculative execution)*: 분기 결과를 모를 때 예측한 쪽([18](../18-pipelining-and-branch-prediction/2-summary.md))을 미리 실행하는 것. 예측이 틀리면 결과를 버린다.
- 이 둘은 성능의 핵심이다. 그런데 2018년, "버린 실행"도 캐시에 흔적을 남겨 그 흔적으로 비밀을 읽을 수 있다는 것이 공개됐다(Spectre·Meltdown).

쉬운 예: 식당 주방이다.
- 주문서 순서는 1·2·3번이지만, 1번 스테이크가 굽는 동안 3번 샐러드를 먼저 만든다. 손님에게 내가는 순서는 주문 순서를 지킨다.
- 단골이 늘 시키는 메뉴를 주문 전에 미리 만들기 시작한다. 다른 걸 시키면 버린다. 그런데 버린 재료가 도마에 남아 있으면, 옆 사람이 "아까 뭘 만들려 했는지" 알아챌 수 있다.

똑같은 구조다.\
결과(손님 접시 = 레지스터·메모리)는 되돌리지만, 도마(캐시) 상태는 되돌리지 않는다.

실무 예:
- 같은 덧셈 개수인데 누적 변수를 1개에서 4개로 나누자 P 코어에서 약 4배(E 코어 약 3.2배) 빨라졌다(아래 실험).
- 2018년 커널 완화 패치(KPTI) 뒤 시스템 콜이 많은 워크로드(예: DB)일수록 성능 손해가 컸다(Gregg 2018 측정 — 마이크로벤치마크와 MySQL OLTP).

## 동작·원리

### 1. 비순차 코어의 모양

```text
   명령 가져오기·해독 ──▶ 마이크로 연산(μop)으로 쪼갬
            │
            ▼  레지스터 이름 바꾸기(renaming): 가짜 의존 제거
   ┌──────────────── 재정렬 버퍼(ROB, 프로그램 순서 기록) ───────────────┐
   │ μop1 load  [대기]  μop2 add [r1 대기]  μop3 mul [준비 → 실행 중] ...  │
   └─────────────────────────────────────────────────────────────────────┘
            │ 준비된 것부터 실행 유닛으로(ALU·곱셈·load/store 여러 개)
            ▼
   실행 완료 → ROB 맨 앞부터 순서대로 은퇴(retire) = 아키텍처 상태에 반영
            틀린 예측·예외 → 그 뒤 μop을 모두 버림 (아키텍처 상태는 되돌려짐)
```

- Spectre 논문 II-A: 현대 프로세서는 명령을 μop으로 해독하고, 앞선 명령이 모두 끝나면 순서대로 은퇴시키며 ROB 자리를 비운다.
  - *재정렬 버퍼(ROB, reorder buffer)*: 실행은 뒤섞여도 확정은 프로그램 순서로 하기 위해 μop을 순서대로 담아 두는 버퍼.
  - *은퇴(retire)*: μop의 결과를 레지스터·메모리(아키텍처 상태)에 확정해 되돌릴 수 없게 하는 것(Spectre 논문 II-A).
    - 흔한 오해: "은퇴 = 메모리에 써짐". 저장(store)은 은퇴 뒤에도 저장 버퍼에 남았다가 나중에 캐시에 쓰일 수 있다. 다른 코어가 언제 보느냐는 [14](../14-cache-coherence-and-memory-ordering/2-summary.md)(저장 버퍼).
- 얼마나 앞질러 갈 수 있나: Spectre 논문은 Haswell의 ROB가 μop 192개를 담는다고 적고, i7-4650U에서 분기와 접근 사이에 단순 명령 188개까지 넣어도 공격 예제가 동작했다고 보고한다(II-B, IV).
- 두 종류의 상태를 구분한다.
  - *아키텍처 상태*: ISA가 약속한 레지스터·메모리 값. 틀린 투기는 여기 남지 않는다.
  - *마이크로아키텍처 상태*: 캐시·분기 예측기·버퍼의 내용. 틀린 투기 뒤에도 바뀐 채 남을 수 있다(Spectre 논문 II-B: "microarchitectural elements may be in a different (but valid) state").
    - 흔한 오해: "버려진 실행은 아무 일도 없었던 것과 같다". 프로그램이 보는 값은 그렇지만, 캐시에 올라온 줄은 그대로라 접근 시간으로 드러난다.

### 2. 실험: 서로 독립인 일은 겹쳐 돈다

```c
// 같은 덧셈 개수(4096 × 20000). 누적기 1개 = 앞 결과를 기다리는 사슬, 4개 = 서로 독립인 사슬 4개
double chain1(const double *a) { double s = 0; for (...) s += a[i]; return s; }
double chain4(const double *a) {
    double s0 = 0, s1 = 0, s2 = 0, s3 = 0;
    for (... i += 4) { s0 += a[i]; s1 += a[i+1]; s2 += a[i+2]; s3 += a[i+3]; }
    return s0 + s1 + s2 + s3;
}
```

(실험, `ilp.c`, gcc 13.3.0 `-O2 -fno-tree-vectorize`(스칼라 `addsd` 유지, objdump 확인), 2026-10-07 — 집필 각 3회 + 점검 재실행 각 9회를 합친 범위)

```text
                       1 accumulator   4 accumulators   비율
  P 코어(taskset -c 0)  0.160~0.198s    0.039~0.053s     3.34~4.41
  E 코어(taskset -c 20) 0.259~0.315s    0.078~0.095s     3.14~3.41
  두 판의 합은 같다(122,850,000)
```

- 누적기 1개면 덧셈마다 앞 덧셈 결과를 기다린다. 덧셈 **지연**이 속도를 정한다.
- 4개로 나누면 사슬 4개가 서로 기다리지 않는다. 비순차 코어가 이들을 겹쳐 실행해 덧셈 장치의 **처리량**에 가까워진다(CS:APP 5.7 Understanding Modern Processors, 5.9.1 Multiple Accumulators).
- 컴파일러가 알아서 해 주지 않은 이유: 부동소수 덧셈은 결합 법칙이 성립하지 않아(반올림) 순서를 바꾸면 결과가 달라질 수 있다. 그래서 `-ffast-math` 없이는 재배치하지 않는다([math/15](../../math/15-numerical-stability/2-summary.md)). 이 실험의 값은 0.5의 배수라 순서와 무관하게 정확히 같다.
- 해석: E 코어의 비율이 더 낮은 것은 실행 자원이 P 코어보다 적어서일 것으로 본다. 하드웨어 카운터를 못 써 직접 확인하지 못했다 [?].

### 3. 투기가 남긴 흔적 — Spectre 변형 1의 모양 (개념)

```text
  피해 코드의 모양(경계 검사):      if (x < len)  y = table[ secret_dependent_index(x) ]
  1. 공격자가 x를 범위 안 값으로 여러 번 → 예측기가 "검사 통과"를 학습
  2. 범위 밖 x를 줌. len을 읽는 동안 CPU가 "통과"로 예측해 미리 실행
     → 범위 밖 메모리(비밀)를 읽고, 그 값에 따라 table의 특정 줄을 캐시에 올림
  3. 검사 결과 확정 → 틀린 예측이라 y는 버림 (아키텍처 상태 깨끗)
  4. 그러나 table의 어느 줄이 캐시에 있는지는 남는다 → 접근 시간을 재서 비밀을 추정
```

- 그림은 Spectre 논문 I장의 예(`if (x < array1_size) y = array2[array1[x] * 4096];`)를 줄인 것이다. 커널 문서의 정의는 이렇다. Spectre 변형 1(Bounds Check Bypass)은 조건 분기의 투기 실행으로 경계 검사를 건너뛴 메모리 접근이 캐시에 부작용을 남기는 것이다. 변형 2(Branch Target Injection)는 간접 분기 예측기(BTB)를 오염시켜 피해자가 공격자가 고른 코드 조각을 투기 실행하게 한다(커널 문서 hw-vuln/spectre).
- 이 노트는 원리와 완화책 관찰까지만 다룬다. 타이밍 측정 코드는 싣지 않는다.
  - *부채널(side channel)*: 정상 출력이 아니라 시간·전력·캐시 상태 같은 부수 효과로 정보가 새는 경로.
- 논문이 보인 범위: Spectre는 Intel·AMD·ARM 프로세서에서 동작하고, JavaScript로도 자신을 실행하는 브라우저 프로세스의 주소 공간을 읽었다(Kocher 외 2019 초록·I장). 프로세스 분리·컨테이너·JIT 같은 소프트웨어 경계의 가정을 깬다고 적는다.

### 4. Meltdown — 권한 검사보다 먼저 읽은 값

```text
  사용자 코드:  v = *(커널 주소)        ← 권한 없음 → 결국 예외
  취약한 CPU: 권한 예외가 은퇴 시점에 처리되는 사이, 읽은 값이 뒤 μop으로 투기적으로 전달됨
            → 그 값에 따라 캐시 줄을 건드림 → 예외로 결과는 버려지지만 흔적은 남음
  완화(PTI): 사용자 모드일 때는 커널 메모리를 페이지 테이블에서 거의 다 빼 둔다(진입·탈출에 필요한 최소한만 남김)
            → 읽을 커널 데이터의 주소 자체가 없음
```

- Meltdown(Lipp 외 2018)은 비순차 실행의 부작용으로 사용자 공간에서 커널 메모리를 읽었다. 논문은 3.2 KB/s~503 KB/s 속도를 보고한다. Intel CPU와 Samsung Exynos M1에서 성공했고, 다른 ARM 코어와 AMD에서는 재현하지 못했다고 적는다(6.3).
- *PTI(Page Table Isolation, KPTI)*: 사용자 모드용 페이지 테이블에는 커널 진입·탈출에 필요한 최소한만 매핑하고, 커널에 들어갈 때 전체 테이블로 바꾸는 완화책(커널 문서 x86/pti).
  - 비용(같은 문서): 시스템 콜·인터럽트·예외의 진입과 탈출마다 CR3를 바꾸고, 그 명령이 "on the order of a hundred cycles"다. PCID가 없으면 CR3를 쓸 때마다 TLB 전체가 비워진다.

### 5. 완화책 관찰 — 이 호스트는 무엇에 취약하고 무엇을 켰나

(실험, i7-13700HX, 커널 7.0.0-34-generic, `grep . /sys/devices/system/cpu/vulnerabilities/*`, 2026-10-07 — 일부 발췌)

```text
  meltdown             Not affected
  spectre_v1           Mitigation: usercopy/swapgs barriers and __user pointer sanitization
  spectre_v2           Mitigation: Enhanced / Automatic IBRS; IBPB: conditional; PBRSB-eIBRS: SW sequence; BHI: BHI_DIS_S
  spec_store_bypass    Mitigation: Speculative Store Bypass disabled via prctl
  reg_file_data_sampling Mitigation: Clear Register File
  vmscape              Mitigation: IBPB before exit to userspace
  mds, l1tf, retbleed, srbds, ...   Not affected
  CPU 플래그: ibrs ibpb stibp ibrs_enhanced ssbd md_clear flush_l1d   (/proc/cpuinfo)
```

- `meltdown: Not affected` → 이 CPU에는 PTI가 필요 없다. 다만 `pti=on`이면 취약 여부와 무관하게 켤 수 있으므로(커널 매개변수 문서, 지정 안 하면 `pti=auto`) 실제 상태는 따로 본다. 이 호스트는 `/proc/cmdline`에 `pti=` 지정이 없고 `/proc/cpuinfo`에 `pti` 플래그가 0개였다. 그래서 [os/02](../../os/02-system-calls/2-summary.md)의 시스템 콜 비용(약 109 ns)은 PTI가 꺼진 상태의 값으로 본다.
- `spectre_v1`의 문구는 커널 문서의 정의 그대로다. 커널 안에서 사례별로 포인터 정리·`LFENCE` 장벽을 넣었다는 뜻이고, 문서는 이것이 변형 1의 공격 경로를 다 막는다는 보장은 없다고 적는다("no guarantee that all possible attack vectors ... are covered").
- `spectre_v2`의 Enhanced IBRS는 하드웨어 쪽 완화다(커널 문서: "Hardware-focused mitigation"). 이 커널은 "Enhanced / Automatic IBRS"로 표기했는데, 문서 판의 표기("Enhanced IBRS")와 문구가 조금 다르다. `IBPB: conditional`은 SECCOMP·간접 분기 제한 태스크에만 IBPB를 쓴다는 뜻이다.
- 컨테이너(`python:3.12-slim`) 안에서 읽어도 같은 값이 나왔다. 컨테이너는 호스트 커널·CPU를 공유하므로 완화 상태도 호스트 것이다.

프로세스 단위 완화도 볼 수 있다. 커널 매개변수 문서(`spec_store_bypass_disable=`)의 x86 기본값은 `prctl`(프로세스가 요청할 때만 끔)이고, 이 호스트의 sysfs 문구도 "disabled via prctl"이다.

(실험, `ssbd.c` — 자기 스레드에 `prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_DISABLE)`만 호출. 공격 코드 아님)

```text
  GET = 0x3                       ← PR_SPEC_PRCTL(1) | PR_SPEC_ENABLE(2): 제어 가능, 투기 허용 중
  before   Speculation_Store_Bypass:	thread vulnerable
  SET(PR_SPEC_DISABLE) = 0
  GET = 0x5                       ← PR_SPEC_PRCTL(1) | PR_SPEC_DISABLE(4)
  after    Speculation_Store_Bypass:	thread mitigated
```

- 같은 줄은 `/proc/<pid>/status`에도 있다. 컨테이너 안의 셸(Seccomp 2, 필터 1개)도 `thread vulnerable`이었다. 이 커널 기본값이 `seccomp`(seccomp 스레드면 자동으로 끔)가 아니라 `prctl`이기 때문이다.

### 6. 완화의 비용은 "커널을 얼마나 자주 드나드나"에 비례한다

```text
  PTI의 비용 ∝ (시스템 콜 + 컨텍스트 스위치 + 인터럽트) 횟수 × 진입·탈출당 추가 비용
              + TLB가 비워져 생기는 추가 미스 (작업 집합이 클수록)
```

- 이 식은 PTI(Gregg 측정) 기준이다. 다른 완화는 비용이 붙는 자리가 다르다. `IBPB: conditional`은 SECCOMP·간접 분기 제한 태스크로 전환할 때만 쓰고, SSBD는 `prctl`로 요청한 스레드에만 걸린다(커널 문서 hw-vuln/spectre·spec_ctrl).

- Gregg(2018, KPTI 측정): CPU당 초당 5만 시스템 콜에서 약 2% 손해, 횟수가 늘수록 커진다. 작업 집합이 10 MB를 넘으면 TLB 비움 때문에 1%가 7%가 될 수 있다. PCID(리눅스 4.14부터 완전 지원)와 huge page가 줄여 준다.
- 커널 매개변수 `mitigations=off`는 선택적 완화를 모두 끈다. 문서는 "improves system performance, but it may also expose users to several CPU vulnerabilities"라고 적는다.

## 쓰이는 자료구조·알고리즘

- **재정렬 버퍼 = 순서를 지키는 FIFO** — 들어온 순서대로 담고 맨 앞부터 은퇴시킨다. 고정 크기로 돌려 쓰는 원형 버퍼로 설명되는 경우가 많다 [?]. [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)
- **의존 그래프 = DAG** — 명령은 입력이 준비되면 실행된다. 실행 가능한 순서는 의존 그래프의 위상 정렬 중 하나다. 최장 경로(임계 경로)가 시간의 하한을 정한다(실험의 누적기 1개 = 길이 N의 사슬). 독립 명령이 많아도 실행 장치 수·처리량이 모자라면 그보다 더 걸린다. [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **레지스터 이름 바꾸기 = 매핑 표 + 빈 칸 목록** — 논리 레지스터 → 물리 레지스터 표를 두고, 쓸 때마다 빈 물리 레지스터를 새로 배정해 가짜 의존(같은 이름 재사용)을 없앤다 [?]. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **캐시 = 주소로 찾는 표** — 부채널은 "이 주소가 표에 있나"를 시간으로 묻는 것이다. 커리큘럼 12(캐시 구성)는 [12-cache-organization](../12-cache-organization/2-summary.md)에서 다룬다.

## 적용 — 풀어나가는 법

### 1. 내 서버의 상태를 본다

```bash
grep . /sys/devices/system/cpu/vulnerabilities/*      # 취약 여부와 켜진 완화
lscpu | grep -i -E 'vulnerab|취약'                     # 같은 정보 요약
grep -i spec /proc/<pid>/status                        # 프로세스 단위 투기 제어 상태
grep -o -w -E 'pti|pcid|ibrs_enhanced|md_clear' /proc/cpuinfo | sort | uniq -c
cat /proc/cmdline                                      # mitigations=·nopti 같은 부팅 매개변수
```

- 같은 서비스인데 호스트마다 성능이 다르면, 먼저 CPU 모델과 이 파일들을 비교한다.

### 2. "패치 뒤 느려졌다"를 판단한다

1. 시스템 콜·컨텍스트 스위치 빈도를 잰다(`strace -c`, `vmstat 1`의 `cs`, `pidstat -w`). CPU당 초당 수만 건이면 완화 비용이 보일 수 있다(Gregg).
2. `sys` 시간 비중이 늘었는지 본다([os/01](../../os/01-kernel-and-user-mode/2-summary.md)).
3. 줄이는 쪽은 코드다. 작은 `read`/`write`를 묶고([os/02](../../os/02-system-calls/2-summary.md)), 큐에 모아 한 번에 제출하는 방식(`io_uring`, [os/34](../../os/34-zero-copy-and-io-uring/2-summary.md))을 검토한다.
4. 완화를 끄는 것(`mitigations=off`)은 그 호스트에서 신뢰하지 않는 코드가 돌지 않는다는 판단이 선 경우의 위험 수용 결정이다. 멀티테넌트·브라우저·사용자 코드 실행 환경에서는 해당하지 않는다.

### 3. 코드 쪽 — 비순차 실행을 돕는다

- 긴 의존 사슬을 끊는다: 누적 변수를 여러 개로 나누고 끝에서 합친다(실험 약 4배). 정수는 컴파일러가 해 주는 경우가 많고, 부동소수는 결과가 달라질 수 있어 직접 정해야 한다.
- 포인터 추적(연결 리스트)은 다음 주소가 앞 load 결과에 달려 겹쳐 실행할 수 없다. 배열이 빠른 이유 중 하나다(커리큘럼 11 메모리 계층, [11-memory-hierarchy-and-locality](../11-memory-hierarchy-and-locality/2-summary.md)).

## 장애 시나리오와 대처

### 1. 커널 업데이트 뒤 DB·프록시 CPU가 오른다

- **현상**: 코드는 그대로인데 커널·마이크로코드 업데이트 뒤 같은 부하에서 CPU 사용률·지연이 오른다.
- **보이는 형태**: `sys` 비중 증가, 처리량 몇 % 감소. 작은 I/O를 많이 하는 서비스일수록 심하다.
- **원인**: 완화 코드가 추가됐다. PTI는 커널 진입·탈출마다 CR3를 바꾸므로 비용이 시스템 콜 빈도에 비례한다. IBPB 같은 완화는 문맥 전환 등 다른 자리에서, 조건에 맞는 태스크에만 비용을 더한다.
- **대처**: `/sys/.../vulnerabilities/*`로 무엇이 켜졌는지 본다. 시스템 콜을 묶고, PCID·huge page 지원을 확인한다. 끄는 것은 위험 수용 결정으로 따로 다룬다.

### 2. "컨테이너로 격리했으니 안전하다"

- **현상**: 신뢰하지 않는 코드를 컨테이너로 돌리며 CPU 취약점을 고려하지 않는다.
- **보이는 형태**: 컨테이너 안에서도 호스트와 같은 `vulnerabilities` 값, 같은 `Speculation_Store_Bypass: thread vulnerable`(실험).
- **원인**: 컨테이너는 같은 커널·같은 CPU 코어·캐시를 공유한다. Spectre 논문은 컨테이너화가 깨지는 경계 중 하나라고 적는다.
- **대처**: 커널·마이크로코드를 최신으로 유지하고 완화를 켠다. 신뢰 수준이 다른 작업은 VM·전용 호스트로 나누고, 필요하면 SMT를 끈다(`mitigations=auto,nosmt`, 처리량 손해 감수).

### 3. 같은 벤치마크가 호스트마다 다르다

- **현상**: 같은 인스턴스 유형·같은 코드인데 시스템 콜이 많은 벤치마크 결과가 호스트마다 다르다.
- **보이는 형태**: 사용자 코드 시간은 같고 `sys` 시간만 다르다.
- **원인**: CPU 세대에 따라 취약 여부가 다르다. 그래서 켜진 완화(PTI 유무, IBRS 방식)와 비용이 다르다. 이 호스트는 `meltdown: Not affected`이고 `pti` 플래그·`pti=` 지정이 없어 PTI가 꺼져 있다.
- **대처**: 벤치마크 기록에 CPU 모델·커널·`vulnerabilities` 출력·부팅 매개변수를 함께 남긴다.

### 4. 계산 루프가 기대보다 4배 느리다

- **현상**: 단순 합계 루프가 CPU 성능에 비해 느리다.
- **보이는 형태**: 위 실험의 누적기 1개 판(0.19s vs 4개 판 0.05s).
- **원인**: 덧셈 전체가 하나의 의존 사슬이라 비순차 코어가 겹쳐 실행할 것이 없다. 덧셈 지연이 그대로 시간이다.
- **대처**: 누적기를 나누거나 벡터 연산을 쓴다. 부동소수면 결과가 바뀔 수 있음을 검토한다([math/15](../../math/15-numerical-stability/2-summary.md)).

## 핵심 문장

- 비순차 실행은 준비된 명령부터 실행하고, 결과는 재정렬 버퍼로 프로그램 순서대로 확정한다.
- 서로 독립인 일은 겹쳐 돈다. 누적기를 1개에서 4개로 나누자 같은 덧셈이 약 4배 빨라졌다.
- 틀린 투기의 결과는 버려지지만 캐시 같은 마이크로아키텍처 상태는 남는다. Spectre·Meltdown은 그 흔적을 시간으로 읽는다.
- 완화책은 붙는 자리가 다르다. PTI는 커널 진입·탈출마다 비용을 더하므로 시스템 콜이 많은 서비스일수록 손해가 크고, IBPB·SSBD는 조건에 맞는 태스크(전환·`prctl` 요청)에만 걸린다.
- 완화 상태는 `/sys/devices/system/cpu/vulnerabilities/*`와 `/proc/<pid>/status`로 보고, 컨테이너는 호스트 것을 그대로 공유한다.

## 관련 주제·근거

- 선행
  - [18-pipelining-and-branch-prediction](../18-pipelining-and-branch-prediction/2-summary.md) — 분기 예측과 버리는 비용
  - [09-isa-and-machine-code](../09-isa-and-machine-code/2-summary.md) — ISA(아키텍처 상태) vs 마이크로아키텍처
- 후속·연결
  - 컴퓨터 구조 [11 메모리 계층](../11-memory-hierarchy-and-locality/2-summary.md)·[12 캐시 구성](../12-cache-organization/2-summary.md)·[14 메모리 순서](../14-cache-coherence-and-memory-ordering/2-summary.md)·[20 멀티코어](../20-multicore-and-numa/2-summary.md)
  - [os/01-kernel-and-user-mode](../../os/01-kernel-and-user-mode/2-summary.md) · [os/02-system-calls](../../os/02-system-calls/2-summary.md) — 모드 전환 비용(이 호스트는 PTI 없음)
  - [os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md) — 페이지 테이블·TLB(PTI가 건드리는 곳)
  - [os/35-virtualization-hypervisor](../../os/35-virtualization-hypervisor/2-summary.md) · [os/28-containers-namespaces-cgroups](../../os/28-containers-namespaces-cgroups/2-summary.md) — 공유 하드웨어 위의 격리
  - [security/24-memory-safety-exploits](../../security/24-memory-safety-exploits/2-summary.md) — 소프트웨어 버그형 메모리 유출과의 대비
  - [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) — 부동소수 덧셈 순서
- 논문
  - Kocher 외, "Spectre Attacks: Exploiting Speculative Execution", IEEE S&P 2019 — 초록, II-A Out-of-order Execution, II-B Speculative Execution(ROB 192 μop, Haswell), IV(188개 명령) <https://spectreattack.com/spectre.pdf>
  - Lipp 외, "Meltdown: Reading Kernel Memory from User Space", USENIX Security 2018 — 초록, 3.2~503 KB/s, 6.3 Limitations on ARM and AMD <https://meltdownattack.com/meltdown.pdf>
- 교재
  - CS:APP 3판 5.7 Understanding Modern Processors, 5.9 Enhancing Parallelism(5.9.1 Multiple Accumulators), 5.11.2 Branch Prediction and Misprediction Penalties(절 번호: 3판 목차 <http://csapp.cs.cmu.edu/3e/pieces/preface3e.pdf>)
- 문서
  - Linux 커널 문서 Spectre Side Channels(변형 1·2, sysfs 값의 뜻) <https://docs.kernel.org/admin-guide/hw-vuln/spectre.html>
  - Linux 커널 문서 Page Table Isolation(PTI) — 개요, 23.3 Overhead(CR3 약 100사이클, PCID) <https://docs.kernel.org/arch/x86/pti.html>
  - Linux 커널 문서 Speculation Control — `PR_GET/SET_SPECULATION_CTRL`, `PR_SPEC_STORE_BYPASS` <https://docs.kernel.org/userspace-api/spec_ctrl.html>
  - Linux 커널 매개변수 문서 — `mitigations=`(off·auto·auto,nosmt), `spec_store_bypass_disable=`(x86 기본 `prctl`) <https://docs.kernel.org/admin-guide/kernel-parameters.html>
  - Brendan Gregg, "KPTI/KAISER Meltdown Initial Performance Regressions"(2018-02-09) <https://www.brendangregg.com/blog/2018-02-09/kpti-kaiser-meltdown-performance.html>
- 실험 목록(모두 2026-10-07, i7-13700HX, Ubuntu 24.04.4, 커널 7.0.0-34-generic — 공격·타이밍 측정 코드 없음)
  - `ilp.c`(gcc 13.3.0 `-O2 -fno-tree-vectorize`): 누적기 1개 vs 4개, P 코어·E 코어 집필 각 3회 + 점검 재실행 각 9회
  - `/sys/devices/system/cpu/vulnerabilities/*`·`/proc/cpuinfo` 플래그·`/proc/cmdline` 읽기(호스트), 같은 파일과 `/proc/self/status`를 `python:3.12-slim` 컨테이너(`--network none`)에서 읽기
  - `ssbd.c`: 자기 스레드의 `PR_SPEC_STORE_BYPASS` 상태 읽기·끄기 → `thread vulnerable` → `thread mitigated`
