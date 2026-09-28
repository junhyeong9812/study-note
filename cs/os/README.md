# 운영체제 — `cs/os/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §5에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 30 · 원고 있음 7 · 초안(Claude) 1 · 검수 완료 0

> 가상화(CPU·메모리) → 동시성 → 영속성 → I/O·격리. 기존 부트캠프 노트는 프로세스·메모리 기초만 덮는다 — **동기화 심화·시그널·파일시스템·fsync·I/O 모델·컨테이너**가 신규의 중심.
> 뼈대: OSTEP(장 번호 확인), CS:APP 3판 7~12장, Linux man-pages(`signal(7)`·`epoll(7)`·`fsync(2)`).

## 5.1 커널과 프로세스

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `kernel-and-user-mode` | OS의 역할, 보호 링, 제한된 직접 실행 | 필수 | 미작성 | — |
| 02 | `system-calls` | syscall 경로·비용·`strace` | 필수 | 미작성 | — |
| 03 | `interrupts-traps-faults` | 인터럽트·트랩·폴트·예외적 제어흐름 | 필수 | 미작성 | — |
| 04 | `process-and-lifecycle` | 프로세스 추상화·5상태·PCB | 필수 | 원고 있음 | [../foundations/process-thread](../foundations/process-thread/) |
| 05 | `fork-exec-wait` | 프로세스 API | 필수 | 미작성 | — |
| 06 | `signals` | 시그널 전달·핸들러·async-signal-safe | 필수 | 미작성 | — |
| 07 | `threads-and-context-switch` | 스레드·TCB·컨텍스트 스위칭 비용 | 필수 | 원고 있음 | [../foundations/process-thread](../foundations/process-thread/) |
| 08 | `cpu-scheduling` | FIFO·SJF·RR·MLFQ·CFS·멀티코어 | 필수 | 원고 있음 | [../foundations/process-thread](../foundations/process-thread/) |

## 5.2 메모리 가상화

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 09 | `address-space` | 가상 주소 공간·코드/데이터/힙/스택·세그먼트 | 필수 | 원고 있음 | [../foundations/memory-management](../foundations/memory-management/) |
| 10 | `paging-and-tlb` | 페이지 테이블·다단계·TLB | 필수 | 원고 있음 | [../foundations/memory-management](../foundations/memory-management/) |
| 11 | `heap-allocation` | malloc·free list·단편화·buddy·slab | 필수 | 원고 있음 | [../foundations/memory-management](../foundations/memory-management/) |
| 12 | `swapping-and-page-replacement` | 스왑·교체 정책·작업 집합·스래싱 | 필수 | 미작성 | — |
| 13 | `oom-and-memory-limits` | overcommit·OOM killer·cgroup memory | 필수 | 미작성 | — |
| 14 | `mmap-and-page-cache` | 파일 매핑·페이지 캐시·dirty writeback | 권장 | 미작성 | — |

## 5.3 동시성

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 15 | `race-conditions` | 임계 구역·원자성·check-then-act | 필수 | 원고 있음 | [../foundations/process-thread](../foundations/process-thread/) |
| 16 | `locks-and-spinlocks` | test-and-set·CAS·futex·공정성 | 필수 | 미작성 | — |
| 17 | `condition-variables-and-monitors` | 대기/통지·모니터 | 필수 | 미작성 | — |
| 18 | `semaphores` | 카운팅 세마포어·생산자/소비자 | 필수 | 초안(Claude) | [../systems/semaphore](../systems/semaphore/) |
| 19 | `deadlock` | 4조건·예방·회피·탐지 | 필수 | 미작성 | — |
| 20 | `concurrency-bugs` | 원자성 위반·순서 위반·기아·라이브락·우선순위 역전 | 필수 | 미작성 | — |
| 27 | `event-based-concurrency` | 이벤트 루프·reactor·콜백 | 필수 | 미작성 | — |

## 5.4 영속성·I/O

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 21 | `files-and-descriptors` | fd·inode·링크·open/close 의미 | 필수 | 미작성 | — |
| 22 | `file-system-implementation` | 블록·inode·비트맵·디렉터리·VFS·FFS | 필수 | 미작성 | — |
| 23 | `crash-consistency-and-journaling` | fsck·저널링·COW·LFS | 필수 | 미작성 | — |
| 24 | `fsync-and-durability` | write≠디스크, fsync·fdatasync·rename 원자성·디렉터리 fsync | 필수 | 미작성 | — |
| 25 | `io-models` | 블로킹/논블로킹·동기/비동기 4분면 | 필수 | 미작성 | — |
| 26 | `io-multiplexing-epoll` | select/poll/epoll, 레벨 vs 엣지 트리거 | 필수 | 미작성 | — |
| 32 | `raid` | RAID 0/1/5/6/10·재구축 | 권장 | 미작성 | — |
| 33 | `data-integrity-checksums` | 조용한 손상·체크섬·스크러빙 | 권장 | 미작성 | — |
| 34 | `zero-copy-and-io-uring` | sendfile·splice·mmap·io_uring | 심화 | 미작성 | — |
| 36 | `server-concurrency-architectures` | 연결당 스레드 vs Reactor(단일·멀티 리액터) vs Proactor(IOCP·io_uring) vs Half-Sync/Half-Async(NIO 수신 + 워커 풀) vs Leader/Followers, Acceptor-Connector | 권장 | 미작성 | — |

## 5.5 IPC·링킹·격리·관측

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 28 | `containers-namespaces-cgroups` | namespace·cgroup·이미지 레이어 | 필수 | 미작성 | — |
| 29 | `linking-and-loading` | 정적/동적 링킹·심볼 해석·PIC·로더 | 권장 | 미작성 | — |
| 30 | `ipc` | 파이프·공유 메모리·유닉스 소켓·메시지 큐 | 권장 | 미작성 | — |
| 31 | `os-observability-tools` | top·vmstat·iostat·strace·perf·/proc, USE 방법론 | 권장 | 미작성 | — |
| 35 | `virtualization-hypervisor` | 하이퍼바이저·VM·steal time | 권장 | 미작성 | — |

## 5.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 37 | `os-symptom-index` | 역색인: errno(`EINTR`·`EAGAIN`·`EMFILE`·`ENOSPC`·`ENOMEM`·`EIO`), exit code(137·139·143), D 상태, 좀비, load 높은데 CPU 낮음 | 필수 | 미작성 | — |
| 38 | `os-incidents` | 실사건: Mars Pathfinder 우선순위 역전(1997) · fsyncgate(PostgreSQL, 2018) · 2012 윤초 커널 hrtimer 버그로 Java·MySQL CPU 폭주 · ext4 지연 할당 0바이트 파일(2009) [?] | 권장 | 미작성 | — |
