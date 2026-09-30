# os/35-virtualization-hypervisor — OS 밑에 OS를 하나 더: 하이퍼바이저가 CPU·메모리를 속이는 법과 steal time — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-09-30) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제

OS는 "기계 전체가 내 것"이라고 가정하고 만든다. 특권 명령을 쓰고, 페이지 테이블을 직접 바꾸고, 장치 레지스터를 만진다.\
그런데 한 물리 서버에 OS를 여러 개 올리고 싶다.

```text
  원하는 것                                  왜
  리눅스 VM 10개를 서버 1대에                   서버 활용률, 클라우드 판매 단위
  윈도·리눅스를 같이                            서로 다른 OS·커널 버전
  VM 하나가 망가져도 나머지는 무사                커널까지 분리된 격리 (컨테이너보다 강함)
  VM을 통째로 다른 서버로 옮기기                  하드웨어 교체·장애 회피
```

OS가 프로세스에게 "CPU·메모리가 네 것인 것처럼" 보여 줬듯이(01번), **하이퍼바이저(VMM)**는 OS에게 "기계가 네 것인 것처럼" 보여 준다.

  - *하이퍼바이저(VMM, virtual machine monitor)*: OS들 아래에서 CPU·메모리·장치를 나눠 주며, 각 OS가 기계를 독점한다고 믿게 하는 소프트웨어다.
  - *게스트 OS*: VM 안에서 도는 OS. *호스트*: 실제 하드웨어 쪽.

쉬운 예: 셰어하우스 관리인이다.
- 입주자(게스트 OS)는 "내 집"처럼 산다. 방 배치도 자기 마음대로 적는다.
- 전기·수도 계량기와 현관(특권 동작)은 관리인(하이퍼바이저)만 만진다. 입주자가 만지려 하면 관리인이 대신 처리한다.
- 한 입주자가 전기를 많이 쓰면 다른 입주자는 차례를 기다린다. 입주자는 이유를 모른다(steal time).

똑같은 구조다.\
AWS EC2·GCE의 VM이 이렇게 돈다. 클라우드 VM에서 "코드는 그대로인데 가끔 느리다"의 흔한 원인이 옆 입주자(noisy neighbor)다.

## 동작·원리

### 1. CPU — 제한된 직접 실행을 한 층 더

```text
   특권 수준        가상화 없음           가상화 (하드웨어 지원, VT-x/AMD-V)
   ------------------------------------------------------------------------
   게스트 사용자                           앱          \
   게스트 커널                             게스트 OS    |  non-root 모드: 대부분 명령을 CPU가 직접 실행
                                                    /
   커널             OS                   하이퍼바이저     root 모드
   사용자           앱

   게스트가 민감한 일을 하면 (I/O 포트, 특정 레지스터, HLT ...)
        --> VM exit (하드웨어가 하이퍼바이저로 넘김) --> 하이퍼바이저가 흉내(emulate) --> VM entry로 복귀
```

- 핵심은 OS의 **제한된 직접 실행**을 한 층 더 쓰는 것이다. 게스트 코드는 CPU에서 직접 돈다. 민감한 순간에만 하이퍼바이저가 끼어든다(OSTEP 부록 B.3).
- 게스트 앱의 시스템 콜 트랩은 먼저 하이퍼바이저로 가고, 하이퍼바이저가 게스트 OS의 트랩 핸들러로 넘긴다. 게스트 OS가 부팅 때 트랩 테이블을 설치하려 한 순간(특권 동작)을 하이퍼바이저가 가로채 기억해 뒀기 때문이다(OSTEP B.3, 소프트웨어 방식 설명).
- **trap-and-emulate**가 되려면 "민감한 명령은 전부 특권 명령이어서 사용자 모드에서 트랩이 나야 한다". Popek·Goldberg(1974)가 정리한 조건이다.
  - 옛 x86은 이 조건을 어긴 명령이 있어서(트랩 없이 조용히 다르게 동작) 고전 방식이 안 됐다. Robin·Irvine(2000)은 펜티엄 명령 중 17개가 "민감하지만 특권이 아닌" 명령이라고 셌다.
    - 예: `POPF`. 특권 없이 실행하면 예외 없이 EFLAGS의 일부 비트(인터럽트 플래그 등)만 조용히 안 바뀐다. 트랩이 안 나니 하이퍼바이저가 가로챌 수 없다.
  - 우회 방법이 세 가지 나왔다.
    - 이진 번역(VMware): 문제 명령을 실행 전에 바꿔 쓴다.
    - 반가상화(Xen): 게스트 OS를 고쳐 하이퍼바이저를 직접 부르게 한다(OSTEP B.4 aside "para-virtualization").
    - 하드웨어 지원(Intel VT-x, AMD-V): CPU에 root/non-root 모드와 VM exit를 넣었다.

  - *VM exit*: 게스트 실행을 멈추고 하이퍼바이저로 제어가 넘어가는 하드웨어 전환이다. 비싸다.

### 2. KVM — 리눅스 커널이 하이퍼바이저가 된다

```text
   +--------------------------+   +--------------------------+
   |  QEMU 프로세스 (VM 1)       |   |  QEMU 프로세스 (VM 2)       |  <- 호스트에서는 보통 프로세스
   |  vCPU 스레드 x N           |   |  vCPU 스레드 x M           |     (ps·top에 보인다)
   |  장치 흉내(디스크·NIC)       |   |                          |
   +------------|-------------+   +------------|-------------+
                | ioctl(KVM_RUN)               |
   -------------v------------------------------v---------------- 호스트 리눅스 커널
                kvm.ko + kvm_intel/kvm_amd  (VM entry/exit 처리)
                fair 스케줄러(6.6 전 CFS, 6.6부터 EEVDF)가 vCPU 스레드를 함께 스케줄
```

- KVM은 리눅스 2.6.20(2007)에 들어온, Intel·AMD 하드웨어 가상화 확장용 드라이버다(kernelnewbies Linux 2.6.20).
- 사용자 공간 프로그램이 `/dev/kvm`에 ioctl로 VM·vCPU를 만들고 `KVM_RUN`으로 게스트를 돌린다. 게스트가 커널이 처리 못 하는 일(예: I/O 포트)을 하면 `KVM_RUN`이 끝나고 `exit_reason`을 돌려준다.
- **vCPU = 호스트 스레드**다. 호스트 스케줄러 입장에서는 다른 스레드와 똑같이 CPU를 나눠 받는다. 이것이 steal time의 뿌리다(4절).

작성 환경에서 최소 KVM 프로그램으로 확인했다(로컬 재현, 리눅스 7.0, i7-13700HX, 예시).

```text
  게스트 코드(16비트): out 명령으로 직렬 포트(0x3f8)에 문자 출력, hlt
  결과: "4\n" 출력, VM exit 3번 (out 2번 + hlt 1번)

  게스트 코드: out 명령 65,535번 반복 후 hlt
  결과: VM exit 65,536번, exit 1번당 약 3.1 us (호스트 사용자 공간까지 왕복 포함)
  비교: 같은 기계에서 getppid 시스템 콜 1번 약 0.13 us
```

- 사용자 공간까지 돌아오는 VM exit는 시스템 콜보다 한 자릿수 이상 비쌌다(이 측정 조건에서 약 24배). 커널 안에서 끝나는 exit는 더 싸다 [?].
- 그래서 가상화 성능 작업의 상당 부분은 **exit 줄이기**다(반가상 장치, 하드웨어 기능).

### 3. 메모리 — 주소 변환이 두 겹이 된다

```text
   가상화 없음:   가상 주소 --(OS 페이지 테이블)--> 물리 주소

   가상화:       게스트 가상(GVA) --(게스트 페이지 테이블)--> 게스트 물리(GPA)
                                                          --(하이퍼바이저 표)--> 호스트 물리(HPA, machine)
```

- 게스트 OS는 "물리 주소"를 관리한다고 믿는다. 실제로는 하이퍼바이저가 그 주소를 다시 진짜 메모리로 옮긴다. OSTEP은 이 세 층을 virtual → physical → machine으로 부른다(OSTEP B.4).
- 두 겹을 하드웨어 TLB에 어떻게 싣나. 방법이 둘이다.

```text
  (A) 섀도 페이지 테이블 (소프트웨어)
      하이퍼바이저가 GVA -> HPA 를 바로 잇는 "섀도" 표를 따로 유지
      CPU에는 섀도 표를 걸어 둔다
      게스트가 자기 페이지 테이블을 바꾸면 -> 트랩 -> 섀도 표도 고친다   (exit 많음)

  (B) 중첩 페이지 테이블 (하드웨어: Intel EPT, AMD NPT)
      CPU가 두 표를 직접 차례로 걷는다 (2차원 걷기)
      게스트의 페이지 테이블 수정에 트랩 없음. 대신 TLB 미스 한 번이 비싸다
```

- (A): 하드웨어가 페이지 테이블을 걷는 x86에서, 하이퍼바이저는 OS의 페이지 테이블 변경을 감시하며 섀도 표를 유지한다(OSTEP B.4 aside, [AA06] 인용).
- (B)의 TLB 미스 비용 계산(4단계 × 4단계, 예시):

```text
  게스트 표 4단계를 걷는다. 그런데 각 단계 표의 주소가 GPA라서, 읽기 전에 호스트 표 4단계를 걸어야 한다.
    게스트 단계 4개 x (호스트 걷기 4 + 그 게스트 항목 읽기 1) = 20
    마지막 결과(데이터의 GPA)를 HPA로 바꾸는 호스트 걷기          =  4
    합계 최대 24번 메모리 참조  ((4+1) x (4+1) - 1)
  가상화 없음: 4번
```

- 이 최악값은 페이지 걷기 캐시·TLB가 대부분 가려 준다. 하지만 메모리를 넓게 흩어 쓰는 워크로드는 TLB 미스가 많아 차이가 드러난다. 큰 페이지(huge page)가 TLB 미스 수를 줄여 준다(10번).
- 작성 환경의 호스트는 EPT를 지원했다(`/proc/cpuinfo` 플래그 `ept`, `kvm_intel` 파라미터 `ept=Y`, 로컬 확인).

### 4. steal time — 게스트가 모르는 사이 흘러간 시간

```text
   물리 CPU 3번 시간축 (호스트 스케줄러)
   |--VM A vCPU0--|--VM B vCPU1--|--VM A vCPU0--|--VM B vCPU1--|
   VM A 입장:   실행     (멈춤: 나는 실행할 게 있었는데 못 돌았다)   실행
                              ^^^^^^^^^^^^^^^^^^^^
                              steal time (도둑맞은 시간)
```

- steal은 "vCPU가 돌고 싶었는데 못 돈 시간"이다. KVM은 게스트와 공유하는 구조체(`MSR_KVM_STEAL_TIME`)의 `steal` 필드에 나노초로 채운다. **vCPU가 idle인 시간은 steal로 치지 않는다**(커널 문서 KVM MSR).
- 게스트 리눅스는 이것을 `/proc/stat`의 8번째 값 `steal`(2.6.11+)로 보여 준다(proc_stat(5)).
  - `top`의 `st`: "hypervisor가 이 VM에서 훔쳐 간 시간"(top(1)).
  - `mpstat`의 `%steal`: 하이퍼바이저가 다른 가상 프로세서를 처리하는 동안 가상 CPU가 비자발적으로 기다린 시간 비율(mpstat(1)).
- steal이 생기는 이유: 물리 CPU보다 vCPU를 많이 팔았거나(과할당), 이웃 VM이 바쁘거나, 호스트 자체 작업이 돌았다.
- 게스트 안에서는 steal을 **줄일 방법이 없다**. 보이기만 한다. 이 VM의 코드가 느린 게 아니라 "시간이 사라진" 것이다.
- 작성 환경은 가상화되지 않은 호스트라 steal이 0이었다(`systemd-detect-virt` = none, 예시).

### 5. 컨테이너와 비교

```text
                    VM                                  컨테이너 (28번)
  격리 경계          하이퍼바이저 (커널까지 분리)              커널 공유 + namespace·cgroup
  게스트 커널         VM마다 따로                           없음 (호스트 커널)
  주소 변환           두 겹 (GVA->GPA->HPA)                 한 겹 (보통 프로세스)
  CPU 한도가 보이는 곳  steal (게스트 /proc/stat)             cgroup cpu.stat의 throttled
  시작 시간           OS 부팅                                프로세스 시작
```

## 쓰이는 자료구조·알고리즘

- **다단계 페이지 테이블 × 2 (2차원 걷기)** — 게스트 표의 각 노드 주소를 호스트 표로 다시 번역한다. 트리 탐색 안의 트리 탐색이다. 최악 참조 수 = (n+1)(m+1) − 1. 페이지 테이블 기초는 10번(원고 [foundations/memory-management](../../foundations/memory-management/README.md)).
- **섀도 표 = 캐시된 합성 매핑** — 두 함수(GVA→GPA, GPA→HPA)를 합성한 결과를 미리 계산해 둔 표다. 원본이 바뀌면 무효화(트랩)해야 하는 캐시 일관성 문제가 따라온다. Disco는 이 비용을 줄이려 VMM 수준 "소프트웨어 TLB"를 뒀다(OSTEP B.4).
- **공유 메모리 + 시퀀스 카운터(steal time)** — `kvm_steal_time.version`은 갱신 중이면 홀수다. 게스트는 읽기 전후 값이 같고 짝수인지 확인한다(커널 문서 KVM MSR). seqlock과 같은 방식이다.
- **스케줄링** — vCPU는 호스트 fair 스케줄러(6.6 전 CFS, 6.6부터 EEVDF)의 스레드다. 공정 스케줄링의 결과가 게스트에게는 steal로 보인다(08번).

## 적용 — 풀어나가는 법

### 1. 내가 VM 안에 있는지, steal이 있는지

```bash
systemd-detect-virt                      # kvm, vmware, xen, none ...
grep -m1 -o hypervisor /proc/cpuinfo     # 게스트면 보통 hypervisor 플래그 (X86_FEATURE_HYPERVISOR "Running on a hypervisor", x86)
lscpu | grep -iE 'hypervisor|virtuali'   # 게스트면 "Hypervisor vendor:" 줄, 호스트는 "Virtualization: VT-x" 같은 줄 (util-linux lscpu.c, 영어 로캘 기준)
vmstat 1 5                               # CPU 칸의 st (procps-ng 4.x는 뒤에 gu 칸이 더 있다)
mpstat -P ALL 1                          # CPU별 %steal
head -1 /proc/stat                       # cpu user nice system idle iowait irq softirq steal ...
```

### 2. 지연이 튀는데 코드는 그대로일 때 — 순서

1. 앱 지표에서 지연 급등 시각을 잡는다.
2. 같은 시각 게스트의 `%steal`(`mpstat`, 모니터링 에이전트의 `cpu steal`)을 본다.
3. steal이 오를 때 지연도 오르면 원인은 VM 밖이다.
4. 대처는 VM 밖에서 한다: 인스턴스 유형 변경(전용·고정 성능), 다른 호스트로 이동(재시작·재배치), 클라우드 업체 문의.
5. steal이 낮은데 느리면 VM 안 원인(GC, I/O, 락)으로 돌아간다(31번 순서).

### 3. 앱 런타임에서 보이는 모습

- **JVM**: steal은 GC 일시 정지를 늘린다. GC 로그의 real 시간이 user+sys보다 크게 늘어난다 [?] (GC 로그 형식은 JDK 버전마다 다르다). 스레드 수는 vCPU 수 기준으로 잡힌다.
- **Node**: 이벤트 루프 지연(`perf_hooks.monitorEventLoopDelay()`)이 steal 구간에 함께 튄다.
- 둘 다 **코드 프로파일에는 원인이 안 나온다**. 프로파일러는 "실행된 시간"을 세는데, steal은 실행되지 못한 시간이기 때문이다.

### 4. 하이퍼바이저를 직접 만져 보기 (KVM API 골격)

```c
int kvm  = open("/dev/kvm", O_RDWR);
int vm   = ioctl(kvm, KVM_CREATE_VM, 0);
ioctl(vm, KVM_SET_USER_MEMORY_REGION, &region);   /* 게스트 물리 0x1000 = 내 프로세스의 mmap 영역 */
int vcpu = ioctl(vm, KVM_CREATE_VCPU, 0);
struct kvm_run *run = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, vcpu, 0);
for (;;) {
    ioctl(vcpu, KVM_RUN, NULL);                    /* 게스트 실행. VM exit가 나면 돌아온다 */
    switch (run->exit_reason) {
    case KVM_EXIT_IO:  /* 게스트가 out 명령 -> 장치 흉내 */ break;
    case KVM_EXIT_HLT: return 0;
    }
}
```

- "게스트 물리 메모리 = 호스트 프로세스의 가상 메모리 일부"라는 점이 그대로 보인다. GPA → (프로세스 가상 주소) → HPA로 두 번 번역되는 이유다.

## 장애 시나리오와 대처

### 1. noisy neighbor → steal time 증가 → 원인 모를 지연

- **현상**: 배포도 트래픽 변화도 없는데 특정 VM들만 p99 지연이 오른다. 재시작하면 나아지기도 한다.
- **보이는 형태**
  - `mpstat`의 `%steal`, `top`·`vmstat`의 `st`가 평소보다 높다.
  - 앱 프로파일·GC 로그에는 뚜렷한 원인이 없다. CPU 사용률은 한도 안이다.
- **원인**: 같은 물리 호스트의 다른 VM(이웃)이 CPU를 많이 써서 이 VM의 vCPU 스레드가 호스트에서 차례를 못 받았다. 또는 vCPU 과할당.
- **대처**
  - `%steal`에 경보를 건다. 앱 지연 그래프와 겹쳐 본다.
  - 성능이 고정된 인스턴스 유형, 전용 호스트를 쓴다.
  - 인스턴스를 교체해 다른 호스트로 옮긴다.
  - 스케일 판단에서 steal을 뺀 실사용 CPU를 본다.

### 2. 버스트형 인스턴스의 CPU 크레딧 소진

- **현상**: 저가 VM이 한동안 잘 돌다가 부하가 계속되면 갑자기 느려진다.
- **보이는 형태**: 게스트 `%steal`이 크게 오르고, 클라우드 콘솔의 CPU 크레딧 잔량이 0에 가깝다 [?] (표시 방식은 업체·유형마다 다르다).
- **원인**: 기준 성능 이상을 크레딧으로 빌려 쓰는 유형에서 크레딧이 떨어지면 하이퍼바이저가 기준선으로 제한한다 [?].
- **대처**: 지속 부하면 고정 성능 유형으로 바꾸거나, 크레딧 잔량을 모니터링한다.

### 3. 메모리 집약 워크로드가 VM에서만 느리다

- **현상**: 같은 코드가 베어메탈보다 VM에서 눈에 띄게 느리다. CPU 연산 위주 코드는 차이가 작다.
- **보이는 형태**: 큰 해시 테이블·그래프 순회처럼 메모리를 넓게 흩어 쓰는 구간이 느리다. steal은 낮다.
- **원인**: TLB 미스마다 2차원 페이지 걷기(최악 24번 참조, 3절)라 미스 비용이 크다.
- **대처**: 게스트·호스트 모두 큰 페이지(huge page)를 쓴다. 데이터 지역성을 높인다(10번).

### 4. VM exit 폭주 → 호스트·게스트 sys 시간 증가

- **현상**: 네트워크·디스크 I/O가 많은 VM에서 처리량이 기대보다 낮고 CPU가 많이 든다.
- **보이는 형태**: 게스트의 sys·softirq 비중이 높다. 호스트에서 해당 QEMU 프로세스 CPU가 높다.
- **원인**: 장치를 **흉내 내는** 방식은 게스트가 장치 레지스터를 건드릴 때마다 VM exit가 난다(작성 환경 측정: 사용자 공간 exit 1번 약 3 µs, 예시).
- **대처**: 반가상 장치(virtio 계열) 드라이버를 쓴다. 고성능이 필요하면 장치 할당(패스스루) 같은 하드웨어 기능을 검토한다 [?] (업체별 지원 확인).

## 핵심 문장

- 하이퍼바이저는 OS의 **제한된 직접 실행을 한 층 더** 쓴다. 게스트 코드는 CPU에서 직접 돌고, 민감한 순간에만 VM exit로 하이퍼바이저가 끼어든다.
- 트랩으로 흉내 내려면 민감 명령이 모두 트랩을 내야 한다. 옛 x86은 아니어서 이진 번역·반가상화를 거쳐 VT-x/AMD-V가 나왔다.
- 메모리는 GVA → GPA → HPA 두 겹이다. 섀도 표는 소프트웨어로 합성하고, EPT/NPT는 하드웨어가 2차원으로 걷는다(TLB 미스 최악 24번 참조).
- vCPU는 호스트의 스레드다. 돌고 싶었는데 못 돈 시간이 **steal**이고, 게스트는 보기만 할 뿐 줄일 수 없다.
- 클라우드 VM의 원인 모를 지연은 `%steal`부터 본다. 프로파일러는 실행되지 못한 시간을 세지 않는다.

## 관련 주제·근거

- 선행: [01-kernel-and-user-mode](../01-kernel-and-user-mode/2-summary.md) — 보호 링, 제한된 직접 실행
- 연결
  - [10-paging-and-tlb](../10-paging-and-tlb/2-summary.md) — 다단계 페이지 테이블, TLB. 원고는 [foundations/memory-management](../../foundations/memory-management/README.md)
  - [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — vCPU를 나눠 주는 호스트 스케줄러. 원고는 [foundations/process-thread](../../foundations/process-thread/README.md)
  - [28-containers-namespaces-cgroups](../28-containers-namespaces-cgroups/2-summary.md) — 커널을 공유하는 격리와의 비교
  - [31-os-observability-tools](../31-os-observability-tools/2-summary.md) — `st`·`%steal`을 보는 도구와 순서
- 교재
  - OSTEP 부록 B "Virtual Machine Monitors" — B.3 CPU 가상화(제한된 직접 실행 확장), B.4 메모리 가상화(virtual/physical/machine, 섀도 페이지 테이블 aside, 반가상화 aside), B.5 정보 격차(idle 루프, 이중 zeroing) <https://pages.cs.wisc.edu/~remzi/OSTEP/vmm-intro.pdf>
  - G. Popek, R. Goldberg, "Formal Requirements for Virtualizable Third Generation Architectures", CACM 17(7), 1974
  - J. Robin, C. Irvine, "Analysis of the Intel Pentium's Ability to Support a Secure Virtual Machine Monitor", USENIX Security 2000 — 민감·비특권 명령 17개, `POPF`(3.1.3) <https://www.usenix.org/legacy/events/sec2000/full_papers/robin/robin.pdf>
  - K. Adams, O. Agesen, "A Comparison of Software and Hardware Techniques for x86 Virtualization", ASPLOS 2006 (OSTEP 인용 [AA06]) [?] (본문 직접 확인 못 함)
- 커널
  - 커널 문서 KVM x86 MSR — `MSR_KVM_STEAL_TIME`, `struct kvm_steal_time`(steal ns, version 홀짝, idle 제외) <https://docs.kernel.org/virt/kvm/x86/msr.html>
  - kernelnewbies Linux 2.6.20 — KVM 병합(2007-02-05) <https://kernelnewbies.org/Linux_2_6_20>
  - KVM API 문서 <https://docs.kernel.org/virt/kvm/api.html>
  - arch/x86/include/asm/cpufeatures.h — `X86_FEATURE_HYPERVISOR`("hypervisor" 플래그)
- util-linux sys-utils/lscpu.c — "Hypervisor vendor:", "Virtualization:" 출력
- Linux man-pages: proc_stat(5) — `steal`(2.6.11+) · top(1) — `st` · mpstat(1) — `%steal`
- 로컬 재현(리눅스 7.0, i7-13700HX, VT-x/EPT, `/dev/kvm` 사용자 ACL): 최소 KVM 프로그램으로 VM exit 횟수·비용(약 3.1 µs/exit) 측정과 getppid(약 0.13 µs) 비교, `ept` 플래그·`kvm_intel ept=Y` 확인, `systemd-detect-virt` = none, `/proc/stat` steal 0
