# architecture/19-out-of-order-and-speculation — 정답

## 정답

### 1. 비순차 실행과 ROB

- 순서대로만 실행하면 메모리 읽기가 끝날 때까지 뒤 명령이 기다린다. 그 값과 무관한 명령까지 기다리는 것이 낭비다.
- 비순차 실행은 입력이 준비된 μop부터 실행하고(실행 순서는 뒤섞임), 결과 확정(은퇴)은 프로그램 순서대로 한다.
- ROB는 μop을 프로그램 순서대로 담아 두고 맨 앞부터 은퇴시킨다. 예측이 틀렸거나 예외가 나면 그 뒤 μop을 버린다(Spectre 논문 II-A·II-B). Haswell의 ROB는 μop 192개다(II-B).

### 2. 두 종류의 상태

- 아키텍처 상태: ISA가 약속한 레지스터·메모리 값. 틀린 투기의 결과는 여기 반영되지 않는다(버려진다).
- 마이크로아키텍처 상태: 캐시·분기 예측기·버퍼. 틀린 투기가 캐시에 올린 줄은 그대로 남을 수 있다.
- 부채널 공격은 이 차이를 이용한다. 값은 버려졌지만 "어느 줄이 캐시에 있나"는 접근 시간으로 드러난다.

### 3. 누적기 1개 vs 4개

- 실험(`ilp.c`, gcc `-O2 -fno-tree-vectorize`, 집필·점검 합산): P 코어 0.160~0.198s vs 0.039~0.053s(3.34~4.41배), E 코어 0.259~0.315s vs 0.078~0.095s(3.14~3.41배).
- 1개면 덧셈마다 앞 결과를 기다리는 사슬 하나라 덧셈 지연이 속도를 정한다. 4개면 독립 사슬 4개를 비순차 코어가 겹쳐 돌린다(CS:APP 5.9.1).
- gcc가 바꾸지 않는 이유: 부동소수 덧셈은 반올림 때문에 결합 법칙이 성립하지 않는다. 순서를 바꾸면 결과가 달라질 수 있어 `-ffast-math` 같은 허락 없이는 재배치하지 않는다.

### 4. Spectre 변형 1·2

```text
  1. 범위 안 x로 반복 호출 → 예측기가 "경계 검사 통과"를 학습
  2. 범위 밖 x → len을 읽는 동안 "통과"로 예측해 투기 실행 → 범위 밖 비밀 읽음
     → 비밀 값에 따라 표의 특정 줄을 캐시에 올림
  3. 검사 결과 확정 → 틀린 예측 → 결과 버림(아키텍처 상태 깨끗)
  4. 표의 어느 줄이 빠른지 재서 비밀을 추정
```

- 변형 2(Branch Target Injection)는 간접 분기 예측기(분기 목표 버퍼)를 오염시켜, 피해자가 공격자가 고른 코드 조각으로 투기 점프하게 한다(커널 문서 hw-vuln/spectre).

### 5. Meltdown vs Spectre, PTI

- Spectre: 피해자 코드가 예측에 속아 **자기 권한 안에서** 하면 안 될 접근을 투기 실행한다.
- Meltdown: 사용자 코드가 커널 주소를 읽으면, 취약한 CPU는 권한 예외가 확정되기 전에 읽은 값을 뒤 μop에 넘긴다. 권한 경계 자체를 넘는다(Lipp 외 2018). 논문은 Intel·Exynos M1에서 성공, AMD·다른 ARM 코어에선 재현 실패를 보고했다.
- PTI: 사용자 모드 페이지 테이블에 커널 메모리를 거의 매핑하지 않는다. 그래서 커널에 들어가고 나올 때마다 페이지 테이블(CR3)을 바꿔야 하고, 커널 문서는 그 비용을 "on the order of a hundred cycles"로 적는다. PCID가 없으면 TLB도 비워진다.

### 6. 업데이트 뒤 `sys` CPU 상승

1. `grep . /sys/devices/system/cpu/vulnerabilities/*`로 무엇이 켜졌는지 본다(업데이트 전 기록이 있으면 비교).
2. 시스템 콜·문맥 전환 빈도를 잰다(`strace -c`, `vmstat`의 `cs`, `pidstat -w`). Gregg(2018)는 CPU당 초당 5만 시스템 콜에서 약 2% 손해, 큰 작업 집합에서 TLB 비움으로 더 커진다고 측정했다.
3. 줄이는 쪽은 코드다. 작은 I/O를 묶고, 일괄 제출(`io_uring`)을 검토한다. PCID·huge page 지원을 확인한다.
- `mitigations=off`는 그 호스트에서 신뢰하지 않는 코드가 전혀 돌지 않는다는 판단 아래의 위험 수용 결정이다. 커널 문서도 성능 향상과 함께 취약점 노출을 경고한다. 멀티테넌트·사용자 코드 실행 환경에서는 고려 대상이 아니다.

### 7. 이 호스트의 값

- `meltdown: Not affected`, `spectre_v2: Mitigation: Enhanced / Automatic IBRS; IBPB: conditional; PBRSB-eIBRS: SW sequence; BHI: BHI_DIS_S`.
- Meltdown에 취약하지 않으니 PTI가 필요 없다. `pti=on`으로 강제로 켤 수는 있지만(커널 매개변수 문서), 이 호스트는 `/proc/cmdline`에 `pti=` 지정이 없고 `/proc/cpuinfo`에 `pti` 플래그가 0개라 PTI가 꺼져 있다. 그래서 [os/02](../../os/02-system-calls/2-summary.md)가 잰 `getppid` 약 109 ns에는 CR3 전환 비용이 들어 있지 않다. PTI가 필요한 CPU에서 같은 측정을 하면 더 클 것으로 예상된다(이 환경에선 비교 불가).
- Enhanced IBRS는 하드웨어 쪽 변형 2 완화라 커널 진입마다 큰 소프트웨어 장벽을 넣지 않아도 된다(커널 문서 "Hardware-focused mitigation").

### 8. SSBD prctl

```text
  GET = 0x3   before: Speculation_Store_Bypass: thread vulnerable
  SET(PR_SPEC_DISABLE) = 0
  GET = 0x5   after:  Speculation_Store_Bypass: thread mitigated
```

- 0x3 = 제어 가능(1) + 허용 중(2), 0x5 = 제어 가능(1) + 끔(4)(`<linux/prctl.h>`).
- 이 커널의 x86 기본값은 `spec_store_bypass_disable=prctl`이다. 프로세스가 요청할 때만 끈다. `seccomp` 모드였다면 seccomp 스레드는 자동으로 껐을 것이다(커널 매개변수 문서). 그래서 seccomp 필터가 걸린 컨테이너 셸도 `thread vulnerable`이었다.

### 9. 컨테이너와 CPU 취약점

- 컨테이너는 호스트와 같은 커널·같은 코어·같은 캐시를 쓴다. 실험에서 컨테이너 안의 `vulnerabilities` 값과 `Speculation_Store_Bypass` 상태가 호스트와 같았다. Spectre 논문도 컨테이너화를 깨지는 경계로 든다.
- 선택지: 커널·마이크로코드를 최신으로 두고 완화를 켠다. 신뢰 수준이 다른 작업은 VM·전용 호스트로 나눈다. SMT를 끄면(`mitigations=auto,nosmt`) 같은 코어를 나눠 쓰는 공격면이 줄지만 처리량을 잃는다. 민감 프로세스는 `prctl`로 투기 제어를 켤 수 있다.
