# 컴퓨터 구조 — `cs/architecture/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §4에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 23 · 검수 완료 0

> 비트 → 게이트 → CPU → 메모리 계층 → 저장장치. 백엔드가 여기서 만나는 장애: 정수 오버플로, 부동소수 오차, 인코딩 깨짐, 아키텍처 불일치 바이너리, false sharing, SSD 지연 스파이크.
> 뼈대: CS:APP 3판(2·3·4·5·6장), OSTEP 36·37·44, Patterson&Hennessy 『Computer Organization and Design』(이하 P&H — 장 번호 `[?]`).

## 4.1 데이터 표현

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `number-systems-twos-complement` | 진수 변환·2의 보수·부호/무부호 | 필수 | 초안(Claude) | [01-number-systems-twos-complement](01-number-systems-twos-complement/) · [../foundations/data-representation](../foundations/data-representation/) |
| 02 | `integer-overflow-and-truncation` | 오버플로 wrap, 좁히기 캐스팅 절단 | 필수 | 초안(Claude) | [02-integer-overflow-and-truncation](02-integer-overflow-and-truncation/) |
| 03 | `floating-point-ieee754` | 부호·지수·가수, ε, 특수값(NaN·Inf) | 필수 | 초안(Claude) | [03-floating-point-ieee754](03-floating-point-ieee754/) · [../foundations/data-representation](../foundations/data-representation/) |
| 04 | `character-encoding-unicode` | 코드 포인트·UTF-8/16·서로게이트·정규화 | 필수 | 초안(Claude) | [04-character-encoding-unicode](04-character-encoding-unicode/) · [../foundations/data-representation](../foundations/data-representation/) |
| 05 | `text-length-segmentation-and-case` | 길이의 4가지 뜻(바이트·UTF-16 단위·코드포인트·그래핌), 안전한 자르기, 대소문자 변환·케이스 폴딩의 로캘 의존, 혼동 문자 | 필수 | 초안(Claude) | [05-text-length-segmentation-and-case](05-text-length-segmentation-and-case/) |
| 06 | `byte-order-and-alignment` | 엔디안·정렬·구조체 패딩 | 권장 | 초안(Claude) | [06-byte-order-and-alignment](06-byte-order-and-alignment/) · [../foundations/data-representation](../foundations/data-representation/) |

## 4.2 논리 회로에서 명령어까지

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 07 | `logic-gates-to-adder` | 트랜지스터→게이트→가산기·ALU | 권장 | 초안(Claude) | [07-logic-gates-to-adder](07-logic-gates-to-adder/) · [../foundations/hardware-basics](../foundations/hardware-basics/) |
| 08 | `sequential-logic-clock` | 플립플롭·클록·레지스터·상태 기계 | 권장 | 초안(Claude) | [08-sequential-logic-clock](08-sequential-logic-clock/) · [../foundations/hardware-basics](../foundations/hardware-basics/) |
| 09 | `isa-and-machine-code` | ISA·레지스터·어셈블리(x86-64/ARM64) | 필수 | 초안(Claude) | [09-isa-and-machine-code](09-isa-and-machine-code/) · [../foundations/hardware-basics](../foundations/hardware-basics/) |
| 10 | `calling-convention-and-stack-frame` | 호출 규약·스택 프레임·ESP/RSP | 필수 | 초안(Claude) | [10-calling-convention-and-stack-frame](10-calling-convention-and-stack-frame/) · [../systems/call-stack](../systems/call-stack/) · [../foundations/memory-management](../foundations/memory-management/) |
| 18 | `pipelining-and-branch-prediction` | 파이프라인·해저드·분기 예측 | 심화 | 초안(Claude) | [18-pipelining-and-branch-prediction](18-pipelining-and-branch-prediction/) |
| 19 | `out-of-order-and-speculation` | 비순차·투기 실행과 부채널 | 심화 | 초안(Claude) | [19-out-of-order-and-speculation](19-out-of-order-and-speculation/) |

## 4.3 메모리 계층

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 11 | `memory-hierarchy-and-locality` | 레지스터→캐시→DRAM→SSD, 시간·공간 지역성 | 필수 | 초안(Claude) | [11-memory-hierarchy-and-locality](11-memory-hierarchy-and-locality/) · [../foundations/memory-management](../foundations/memory-management/) |
| 12 | `cache-organization` | 라인·집합 연관·쓰기 정책·교체 | 필수 | 초안(Claude) | [12-cache-organization](12-cache-organization/) |
| 13 | `latency-numbers` | 지연 자릿수 감각·AMAT | 필수 | 초안(Claude) | [13-latency-numbers](13-latency-numbers/) |
| 14 | `cache-coherence-and-memory-ordering` | MESI·저장 버퍼·재정렬·배리어·CAS | 필수 | 초안(Claude) | [14-cache-coherence-and-memory-ordering](14-cache-coherence-and-memory-ordering/) |

## 4.4 I/O·저장장치·병렬

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `io-devices-interrupts-dma` | 폴링 vs 인터럽트, DMA, 장치 레지스터 | 필수 | 초안(Claude) | [15-io-devices-interrupts-dma](15-io-devices-interrupts-dma/) |
| 16 | `storage-media-workload` | HDD 탐색·회전 vs SSD, 순차/랜덤 IOPS 유도 | 필수 | 초안(Claude) | [16-storage-media-workload](16-storage-media-workload/) · [../systems/storage-media-workload](../systems/storage-media-workload/) |
| 17 | `nand-flash-ftl` | 셀·블록·FTL·GC·쓰기 증폭 | 권장 | 초안(Claude) | [../systems/nand-flash](../systems/nand-flash/) |
| 20 | `multicore-and-numa` | 멀티코어·SMT·NUMA 원격 메모리 | 심화 | 초안(Claude) | [20-multicore-and-numa](20-multicore-and-numa/) |
| 21 | `simd-and-gpu` | 데이터 병렬(SIMD·GPU)의 모양 | 심화 | 초안(Claude) | [21-simd-and-gpu](21-simd-and-gpu/) |

## 4.5 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 22 | `arch-symptom-index` | 역색인: `SIGSEGV`/`SIGBUS`/`SIGILL`, `exec format error`, 음수 금액, 합계 불일치, 모지바케, 멀티스레드가 더 느림, SSD 지연 톱니 | 필수 | 초안(Claude) | [22-arch-symptom-index](22-arch-symptom-index/) |
| 23 | `arch-incidents` | 실사건: Patriot 미사일 시계 오차 누적(1991) · Ariane 5 64→16비트 변환(1996) · Intel FDIV(1994) · Spectre/Meltdown(2018) · 2038년 문제 | 권장 | 초안(Claude) | [23-arch-incidents](23-arch-incidents/) |
