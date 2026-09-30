# log — os-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-09-30 | 인터뷰 6건: 범위 미작성 30 + 원고 7 보강(새 leaf 폴더) + 18 같은 방식 · 검증 네트워크와 같게 · 2차 리뷰 codex 우선(막히면 Opus) · 로컬 재현 허용 → 명세 합의, auto | SPEC=1·MODE=auto, 브랜치 docs/os-writing(main fb3bf94c) |
| 2026-09-30 | 스모크(A2): gcc 13.3 컴파일·fork/waitpid 실행·`strace -f`(clone·wait4·SIGCHLD) 성공, gdb 있음, perf_event_paranoid=4(perf 대부분 불가), 커널 7.0.0-31 | A2 확인 — 브리핑 §5에 환경·제약 기록 |
| 2026-09-30 | gen_area_readme.py: 새 leaf 폴더가 있으면 원고보다 먼저 링크(원고 링크 유지) — 재생성 결과 기존 문서 변화 0 | — |
| 2026-09-30 | briefing.md 작성(네트워크 브리핑 + §3-1 2차 리뷰 교훈 유형 + §4 원고 이어받기 + §5 로컬 재현 안전 규칙) | — |
| 2026-09-30 | Opus 집필 워커 7개 발사(공통 지시 scratchpad/os/writer-prompt.md): 01~05 · 06~10 · 11~15 · 16~20 · 21~24,32,33 · 25~27,34,36 · 28~31,35 = 36편. 종합 37·38은 후속 | 회수 대기 |
| 2026-09-30 | 회수 1/7: 11~15(Opus) — check 5 PASS 재확인, [?] 2, ⚠ 5/5, 로컬 재현 다수(brk/mmap 경계·malloc_trim RSS·double free exit 134·Belady FIFO 9→10·oom_score 공식·mmap truncate SIGBUS 135·mincore·count++ 유실·TSan) | man vs 소스 불일치 기록(oom_score_adj root 3% 보너스 현 소스엔 없음), 원고 참고 줄 2(memory-management §11 수치 근거 없음, process-thread §10 CPython 3.12 미재현). 환경: overcommit_memory=1·swap 거의 가득 — 예시 값에 명시 |
| 2026-09-30 | 회수 2/7: 28~31·35(Opus) — check 5 PASS 재확인, [?] 약 13, ⚠ 5/5, 로컬 재현(taskset으로 nproc 2 vs Node os.cpus 24·JVM 2, 링커 에러 재현, 파이프 65536·70KB 데드락, load avg D 상태, /dev/kvm 최소 VM 프로그램 VM exit ~3.1µs) | 실험 객체(shm·mq·소켓) 정리 확인 보고. /dev/kvm은 사용자 ACL로 허용된 범위 |
| 2026-09-30 | 회수 3/7: 25~27·34·36(Opus) — check 5 PASS 재확인, [?] 약 9, ⚠ 5/5, 로컬 재현 14건(EAGAIN 바쁜 루프·epoll LT vs ET·FD_SET 1102 fortify abort·poll vs epoll 지연·Node 루프 블로킹 558ms·libuv 스레드풀 4·Node libuv 1.48 io_uring SQPOLL strace·sendfile 1 syscall·raw io_uring·seccomp로 io_uring EPERM 시 Node 폴백·스레드 1000개 VmSize) | 128MB 테스트 파일 삭제·잔여 프로세스 없음 보고 |
| 2026-09-30 | 회수 4/7: 06~10(Opus) — check 5 PASS 재확인, [?] 3(08), ⚠ 5/5, 로컬 재현(pending 시그널 비트마스크·핸들러 malloc 데드락 gdb 확인·exit 141/143/137/139, 파이프 핑퐁 3.5µs·스레드 400개 cs 1.97M/s, nice 가중치 75/24%, SEGV_MAPERR/ACCERR, pagemap 요구 페이징·THP 167→137ns·TLB shootdown) | 원고 참고 줄: 09 32비트 2G/2G 분할·스택 1MB는 Windows, 10 present=0 의미, 08 리눅스는 가중 비례(CFS→EEVDF 6.6). man 지연: sched(7) RT throttling vs 소스 fair deadline server |
| 2026-09-30 | 회수 5/7: 21~24·32·33(Opus) — check 6 PASS 재확인, [?] 5, ⚠ 6/6, 로컬 재현(fd 공유·삭제된 열린 파일 df 불변·lsof +L1, Java/Node EMFILE 문구, ext4 이미지 inode 고갈 ENOSPC·e2fsck 비트맵 차이, fsync 비용 200회 1076ms·Java/Node rename 원자 저장 strace, RAID5 write hole C 재현, 1비트 손상 e2fsck 통과 vs inode csum 검출) | root 없이 불가: 실제 fsync EIO·md·btrfs — 소스 근거만 |
| 2026-09-30 | 회수 6/7: 01~05(Opus) — check 5 PASS 재확인, [?] 2, ⚠ 5/5(01 ⚠ 정정: x86 특권 명령은 SIGSEGV, SIGILL은 미정의 명령 — 로컬 재현), 로컬 재현(CS=0x33, syscall 비용 109ns vs vDSO 18ns, EINTR/SA_RESTART, major fault 폭주, 좀비·RLIMIT_NPROC fork EAGAIN, COW 256MB fork, SOCK_CLOEXEC 포트 점유) | 웹 검색 한도(200) 소진 보고 — raw GitHub·man7·로컬로 대체. 원고 참고 줄 3(04 Ready를 Waiting, 소멸 서술, 03 page fault=디스크만) |
| 2026-09-30 | factcheck-briefing.md(네트워크 것 OS용 수정: 규범·버전 조건·노트 안 모순·원고 참고 줄 대조 추가, WebSearch 소진 대비 curl·로컬 man) → 독립 Opus 사실 점검 6개 발사(01~05·06~10·11~15·21~24,32,33·25~27,34,36·28~31,35 = 31편). 16~20 집필 중 | 회수 대기 |
| 2026-09-30 | 회수 7/7: 16~20(Opus) — check 5 PASS 재확인, [?] 0(2차 인용은 '원문 미열람' 표기), ⚠ 5/5, 로컬 재현(스핀락 vs mutex 처리량·1CPU 1.15s vs 0.48s, futex 호출 수, cond if vs while 빈 큐 pop, Java Semaphore release 누락·과다, 데드락 jstack·gdb·TSan lock-order-inversion, livelock 백오프 16배, PI futex). **36편 집필 완료** | ⚠ 안전 규칙 이탈 보고: 96스레드 스핀락 1회 ~1,200 CPU초(브리핑 §5 '시스템 부담 실험 금지' 취지 초과) — 반복 없음, 이후 워커 지시에 강조 |
| 2026-09-30 | 사실 점검 16~20 발사(무거운 벤치 재실행 금지 명시) ∥ 종합 37·38 집필 발사(리프 36편 장애 절 전수 읽기·노트 간 모순 보고) | 회수 대기 |
| 2026-09-30 | 사실 점검 회수 1/7: 01~05 — 중간 5(02 SO_RCVTIMEO/SNDTIMEO 구분, 03 major fault 표 조건 MADV_RANDOM — 요약·정답 불일치, 04 pid_max 순환은 RESERVED_PIDS 300부터·vmstat b=I/O 대기만, 05 THP COW는 5.8부터 4KB 분할 — [?] 주장이 틀렸음), 경미 약 9, [?] 2→0, 노트 간 모순 0, check 5 PASS | CMU 15-213 강의 PDF 404 → f15 아카이브 URL로 메인이 교체(200 확인) |
| 2026-09-30 | 사실 점검 회수 2/7: 06~10 — 중대 1(08 EEVDF base slice 0.7ms는 정규화 값, 실제는 1+ilog2(min(ncpu,8)) 배 → 8코어+ 2.8ms), 중간 7(06 HotSpot SIGPIPE는 SIG_IGN이 아닌 빈 핸들러, 07 가상 스레드 unmount 예외·JEP 491, 08 fair server 6.12, 09 비정규 구멍 경계·57비트·mmap_min_addr 예외, 10 PSE 비트는 PMD/PUD만), 경미 약 8, [?] 3→1, check 5 PASS | — |
| 2026-09-30 | 사실 점검 회수 3/7: 28~31·35 — 중대 1(31 jstack nid는 JDK 18부터 10진수, JDK-8268425), 중간 약 8(28 libuv 1.49+ cgroup cpu.max 반영, 29 라이브러리 검색 순서 vs 심볼 조회 순서 혼동·musl 버전 서술·static getaddrinfo 경고 로컬 재현, 30 SIGPIPE Node/HotSpot 소스 확인, 35 x86 POPF 예시 Robin&Irvine 2000), [?] 17→7, check 5 PASS | **안전 분류기 미가용 상태로 실행된 워커** → 메인 확인: repo 변경은 cs/os 담당 폴더 + 기존 작업 파일뿐, 리프 비-md 0, ~/.claude 변경 없음 |
| 2026-09-30 | 사실 점검 회수 4/7: 21~24·32·33 — 중대 1(21 fork 공유 fd 쓰기 덮어씀 서술 — 3.14부터 공유 OFD write는 원자적, 덮어쓰기는 별도 open; 로컬 재현 40000 vs 20000 줄, Q9 문구 조정), 중간 3(22 ENOSPC Java 예외 형태, 23 journal_async_commit vs journal_checksum·torn write 끄는 조건 출처화), 경미 5, 24 무수정, [?] 5→4, check 6 PASS | — |
| 2026-09-30 | 사실 점검 회수 5/7: 11~15 — 중간 약 8(12 CLOCK 그림 vs 본문 모순·MGLRU 환경 조건·파일 페이지 스래싱 지표, 13 native thread 실패 errno는 EAGAIN(glibc가 ENOMEM 변환), 14 dirty_ratio 초과 시 구현은 (bg+dirty)/2부터 스로틀·기록은 flusher, 15 CPython 3.12 eval breaker 위치로 [?] 해소·C data race 정의), 경미 약 12, [?] 3→0, check 5 PASS | 절차 사고: 워커 curl이 cwd를 저장소 루트로 떨어뜨려 웹 문서 12개가 루트에 생성 → 워커가 scratchpad로 이동, **메인 재확인: 루트 잔여 0·git status 범위 정상** |
| 2026-09-30 | 사실 점검 회수 6/7: 25~27·34·36 — 중대 1(34 mmap 뒤 truncate 후 write는 SIGBUS가 아니라 EFAULT — 로컬 재현, 2003 LJ 서술은 역사 주석), 중간 6(libuv io_uring 1.45~1.48 켜짐·1.49부터 기본 꺼짐 — 25·27·34 노트 간 불일치 해소, D 상태 TASK_KILLABLE 예외, SO_REUSEPORT는 해시/BPF 선택), [?] 12→3, check 5 PASS | — |
| 2026-09-30 22:55 | codex 가용 확인 → 아직 한도("try again at 11:18 PM") | codex 러너 준비(scratchpad/os/codex/run1.sh, 한도 감지 시 즉시 중단). 23:18 이후 16~20·37·38 점검 완료분 포함 실행 예정 |
| 2026-09-30 | 사실 점검 회수 7/7: 16~20 — 중간 8(16 glibc 기본 뮤텍스는 스핀 없음 — ADAPTIVE만, 17 OSTEP 30.11 추적 단계 누락, 18 그림 31.11 순서·flock 해제 조건, 19 POSIX EDEADLK 가능·InnoDB LOCK TABLES 조건, 20 OSTEP 31.5 링크), 경미 6, [?] 0→0, 무거운 벤치 재실행 없음(표 수치 내부 일관 확인), check 5 PASS. **36편 1차 점검 완료** | — |
| 2026-09-30 | 종합 37·38 회수(Opus): check 2 PASS, [?] 3(38 윤초 버그 도입 커널 버전·Java/MySQL 경로 추론·MySQL 블로그 미열람), 커리큘럼 [?] 2건(윤초·ext4) 1차 출처로 확인, 로컬 재현(exit code 129~143 표·126/127·Node/JDK 종료 코드·cond_timedwait 과거 기한 루프) | 리프 모순 보고 5: ①30 SIGPIPE [?]·②13 ENOMEM — **메인 확인: 둘 다 1차 점검에서 이미 수정됨**, ③24 커밋 인용(이미 인용), ④04 vs 05·28 bash 메시지(둘 다 실재), ⑤28 143 WIFEXITED/WIFSIGNALED 구분 → 일관성 패스 |
| 2026-09-30 | 37·38 사실 점검 발사(리프 현행 텍스트 대조, 알려진 리프 정정 목록 전달) · codex 2차 리뷰 36편은 23:19 자동 시작 대기(3병렬) | 회수 대기 |
| 2026-09-30 | 사실 점검 37·38 회수: 37 중간 7(hung_task 'in I/O wait'은 7.1부터, EPIPE 가시 조건, ENOSPC 시나리오의 예약 블록은 리프 22와 모순 → max_dir_size_kb, EAGAIN 스레드 생성 조건, SIGBUS vs EFAULT, dirty 스로틀 서술을 리프 14에 맞춤), 38 경미 8(PG 커밋 작성자·errseq 머지 v4.17-rc4 등), 타임라인 1차 출처 전부 일치, check 2 PASS | 리프 20:296 '38 미작성' 표기 낡음 → 링크 전환 패스 |
| 2026-09-30 23:31 | codex 2차 리뷰(high, 3병렬): 01~09 9편 완료(지적 편당 7~12, 합계 87) → 10번째부터 **사용 한도**(다음 리셋 10-01 04:19), 27편 QUOTA 즉시 중단 | 명세대로 대체: codex 01~09 → Opus 판정 2개 발사 · 남은 29편(10~38) → Opus 적대 리뷰 6개(codex 출력 3편으로 보정) 발사. OS용 adjudicate-briefing.md 작성 |
| 2026-09-30 | 대체 리뷰 회수 25~29: 3건(25 논블로킹 connect EINPROGRESS 조건·UNIX 소켓 EAGAIN, 28 unshare Time ns도 자식만, 29 bash 5.1+ 'required file not found' 로컬 재현), 26·27 없음 | 판정 워커 발사(25·28·29) |
| 2026-09-30 | 대체 리뷰 회수 30~34: 9건(30 파이프 용량 soft 한도 도달 시 최소 크기·빈 파이프 EOF 예외·EPIPE 가시 조건, 31 strace -e/-c는 정지 안 줄임(--seccomp-bpf는 -p 불가)·D 상태 TASK_KILLABLE·시스템 cpu PSI full 5.13+ 항상 0, 32 PPL 배열은 dirty+degraded 기동, 33 btrfs +C는 빈 파일에만, 34 JDK 17은 sendfile만) | 판정 워커 발사 |
| 2026-09-30 | 판정 회수 25·28·29: 3건 전부 채택(connect EINPROGRESS 조건, unshare Time ns, bash 5.2 메시지 로컬 재현), check 3 PASS | — |
| 2026-09-30 | 판정 회수 01~05(codex 45건): 채택 29·부분 15·기각 1(02 do_syscall_64 위치 — v6.19·7.0은 syscall_64.c, codex는 6.12 근거 → 버전 주석만), 로컬 재현 2(SA_SIGINFO 핸들러 async-signal-safe 수정, /proc stat comm 공백 파싱), check 5 PASS | 핸들러 코드 snprintf 비안전 → write 직접 변환 등 코드 결함도 교정 |
| 2026-09-30 | 판정 회수 06~09(codex 42건): 채택 38·부분 4·기각 0(버전 조건 다수 — EEVDF deadline 트리 6.8+, sched_setattr slice 6.12+, glibc 2.39 clone3 우선(로컬 strace), JEP 491 Object.wait, glibc 2.42 MADV_GUARD_INSTALL(로컬 재현)), check 4 PASS | — |
| 2026-09-30 | 대체 리뷰 회수 35~38: 9건(35 procps-ng 4.x vmstat 마지막 칸 gu·EEVDF, 36 사용자 공간 큐 드롭은 TCP 재전송 안 됨·IOCP는 SPSC 아님·nginx 구조·HikariCP 문구, 37 OOM 희생자 oom_badness+adj 조건, 38 errors=remount-ro는 데이터 쓰기 에러에 작동 안 함(data_err=ignore)·/proc/mounts 기본 옵션 숨김) | 판정 워커 발사. 리프 20·23·24의 '38 미작성' 표기 → 링크 패스 |
| 2026-09-30 | 대체 리뷰 회수 15~19: 5건(15 O_EXCL NFS 조건·OSTEP race/data race 용어, 16 ReentrantLock 재진입이라 누수 스레드는 통과, 19 DEFAULT 뮤텍스 재잠금은 UB(요약과 정답 모순)·멀티코어 교착), 17·18 없음 · 20~24: 6건(20 ctxt는 메인 스레드만, 21 mmap 참조·rm은 unlinkat, 22 inode_ratio 크기별 usage type, 23 journal_async_commit은 data=ordered에서 거부, 24 fallocate unwritten extent면 fdatasync 이득 없음) | 판정 워커 2개 발사 |
| 2026-09-30 | 대체 리뷰 회수 10~14: 12건(10 THP COW 5.8+ 4KB — 리프 05와 불일치, 11 arena 64MiB는 heap 상한·동적 문턱 꺼짐 조건·brk는 main arena만, 12 MGLRU swappiness=0·shmem 스왑·핵심 문장 모순, 13 MaxDirectMemorySize 기본=maxMemory·작은 limit MinRAMPercentage, 14 mincore 권한·Kafka SSL은 sendfile 안 씀) | 판정 워커 발사. **대체 리뷰 29편 전부 회수** |
| 2026-09-30 | 판정 회수 15·16·19: 5건 전부 채택(O_EXCL NFS 조건, OSTEP 용어, ReentrantLock 재진입 — 장애 4 제목 문구 교정, DEFAULT 뮤텍스 재잠금 UB·glibc는 NORMAL, 멀티코어 교착), 19 요약·정답 모순 해소, check 3 PASS | — |
| 2026-09-30 | 판정 회수 30~34: 9건 채택 7·부분 2(31 --seccomp-bpf 버전 미확인 제외, 33 chattr(1) 인용 유지 + 현 소스 더 엄격 주의·도입 버전 [?]), 34 JDK transferTo는 jdk19u까지 sendfile만·jdk20u부터 copy_file_range 먼저(소스 확인), check 5 PASS | — |
| 2026-09-30 | 판정 회수 35~38: 9건 채택 7·부분 2(36 HikariCP 버전 경계, 38 Ringer 주장 유지 + data_err 주의 — 리뷰어 문구 중 v7.0에 낡은 부분은 소스 대조로 제외), 로컬 재현(vmstat gu 칸, /proc/mounts vs /proc/fs/ext4 options), check 4 PASS | — |
| 2026-09-30 | 판정 회수 20~24: 6건 채택 5·부분 1(21 close(2) 문구 유지 + mmap 참조 주의), 23 journal_async_commit data=ordered 거부·descriptor 블록 대기 생략(super.c·jbd2 소스), 24 fallocate 파일 fdatasync 1556ms vs 492ms 로컬 재현, rm=unlinkat strace, check 5 PASS | — |
| 2026-09-30 | 판정 회수 10~14: 13건 전부 채택(10 THP COW 5.8+ 4KB로 리프 05와 일치, 11 arena vs heap 64MiB·동적 문턱 꺼짐·brk는 main arena만·small bin 비정렬, 12 swappiness=0 MGLRU/cgroup 예외·shmem 스왑·핵심 문장 모순 해소, 13 MaxDirectMemorySize 기본=maxMemory·작은 limit 50%(로컬), 14 mincore 권한 조건 — 리뷰어의 v5.0은 틀려 v5.2로 교정(compare API)). **2차 리뷰 판정 전부 완료: 38편**, 전체 check 38 PASS | — |
| 2026-09-30 | post-fix 일관성 재점검 발사(Opus, 공통 사실 15종 + 미작성 링크 전환) · web-sample.md 24건 작성(교차 확인은 일관성 패스 뒤) | 회수 대기 |
| 2026-09-30 | post-fix 일관성 재점검 회수: 공통 사실 15종 — 9곳 정정(01 RT 95%는 6.11까지·6.12 fair server, 07 EEVDF 6.12+ 오독, 31 load D 예외, 25·03 vmstat b=I/O 대기, 30 HotSpot SIGPIPE, 37 SIGBUS 읽기·쓰기, 28 작은 limit 50%), 미작성 → 링크 12곳(13링크), check 38 PASS | 검증 완료 |
| 2026-09-30 | README 재생성: os 미작성 0·초안 38(원고 있는 04·07·08·09·10·11·15·18은 새 leaf 먼저 + 원고 링크 유지), network 변화 없음 · linkcheck main 211 → 212, 신규 1건은 02/3-answer 인라인 코드 `sys_call_table[nr](regs)` 오탐(check_new는 인라인 코드 제외) — 노트 실제 신규 깨짐 0 | 웹 교차 24건 워커 실행 중 |
| 2026-09-30 | 웹 교차 표본 회수: 24/24 일치(불일치 0·확인 불가 0), 커밋 3건 최초 태그(v5.8-rc1·v4.17-rc4·v3.5-rc7) 노트와 일치. 참고 지적 반영: 08 cpu.max 적용 대상에 sched_ext BPF 스케줄러 한 구절(메인) | check 38 PASS |
| 2026-09-30 | 저장소 루트 유출 파일 발견: `h`·`h.c`(23:33, 01~05 판정 워커의 SA_SIGINFO 핸들러 재현 산출물 — 노트 01 코드와 동일) → scratchpad/os/stray로 이동(삭제 아님). 이번 작업 두 번째 루트 유출 | 워커 브리핑에 "작업 디렉토리 절대 경로 + 명령마다 cd 확인" 보강 필요 → NEXT 교훈 |
| 2026-09-30 | 마감: 완료 요약·생략한 검증·NEXT(N0-c 갱신·N0-g 추가)·측정로그 1행. 아카이브: CS 이슈 0건 — 사건형 문제 없음(발견 사실은 노트 본문 반영, 루트 유출·codex 한도는 도구 사정) | 커밋 → push 확인 요청 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 01~05 | Opus 독립 | 0 | 5 | ~9 | 2→0 | 웹 표본 15 |
| 06~10 | Opus 독립 | 1 | 7 | ~8 | 3→1 | 웹 표본 15 |
| 28~31·35 | Opus 독립 | 1 | ~8 | ~7 | 17→7 | 웹 표본 15, 분류기 미가용 — 메인 변경 범위 확인 |
| 21~24·32·33 | Opus 독립 | 1 | 3 | 5 | 5→4 | 웹 표본 18 |
| 11~15 | Opus 독립 | 0 | ~8 | ~12 | 3→0 | 웹 표본 15, 루트 파일 유출 사고(복구 확인) |
| 25~27·34·36 | Opus 독립 | 1 | 6 | ~7 | 12→3 | 웹 표본 15 |
| 16~20 | Opus 독립 | 0 | 8 | 6 | 0→0 | 웹 표본 15 |
| 37·38 | Opus 독립(리프 대조) | 0 | 7 | ~10 | 2→2 | 웹 표본 6 |
| 01~05 판정 | Opus(codex 지적 45) | 채택 29 | 부분 15 | 기각 1 | | |
| 25·28·29 판정 | Opus(대체 리뷰 3) | 채택 3 | 부분 0 | 기각 0 | | |
| 06~09 판정 | Opus(codex 지적 42) | 채택 38 | 부분 4 | 기각 0 | | |
| 15·16·19 판정 | Opus(대체 리뷰 5) | 채택 5 | 부분 0 | 기각 0 | | 19 내부 모순 해소 |
| 30~34 판정 | Opus(대체 리뷰 9) | 채택 7 | 부분 2 | 기각 0 | | |
| 35~38 판정 | Opus(대체 리뷰 9) | 채택 7 | 부분 2 | 기각 0 | | |
| 20~24 판정 | Opus(대체 리뷰 6) | 채택 5 | 부분 1 | 기각 0 | | |
| 10~14 판정 | Opus(대체 리뷰 13) | 채택 13 | 부분 0 | 기각 0 | | 리뷰어 커밋 버전 오기 1 교정 |
| post-fix 일관성 | Opus | 정정 9 | | | | 링크 전환 12 |
| 웹 교차 | Opus 독립 | 24/24 일치 | | | | web-sample.md |

## 생략한 검증

- codex 2차 리뷰는 01~09(9편)만 — 10편째부터 사용 한도(다음 리셋 10-01 04:19). 명세대로 Opus 적대 리뷰로 대체(10~38, 29편). 대체 리뷰는 codex보다 편당 지적이 적었다(codex 평균 ~9.7 vs 대체 ~1.6) — 모델 다양성 손실 가능성. 선택 후속: 한도 해제 뒤 codex로 10~38 표본 재리뷰.
- root·cgroup 쓰기·userns가 필요한 재현(실제 OOM kill, fsync EIO, md·btrfs, D 상태 hung_task, 윤초, 컨테이너 PID 1)은 소스·문서 근거만.

## 완료 요약

- **산출**: `cs/os/` 38편 × 3파일 = 114파일, 약 16,400줄, 질문 364개. 미작성 30 + 원고 보강 7(04·07·08·09·10·11·15, 원고는 수정 없이 링크·참고 줄) + 기존 초안 보강 1(18). 영역 README: 미작성 0·초안 38.
- **파이프라인**: Opus 집필 ×8(종합 1 포함) → Opus 사실 점검 ×8 → 2차 리뷰(codex high 9편 + Opus 적대 리뷰 ×6이 29편) → Opus 판정 ×10 → Opus 일관성 재점검 → 웹 교차 24.
- **수치**: 1차 점검 중대 4·중간 약 45 · 2차 지적 133건(codex 87 + 대체 46) → 채택 약 108·부분 약 24·기각 1 · 일관성 정정 9 · 웹 24/24 일치 · 남은 [?] 18 · check 38 PASS · 노트 신규 깨진 링크 0.
- **before → after(대표, 실파일 반영)**: 21 "fork 공유 fd 쓰기는 서로 덮어씀" → "3.14부터 원자적, 덮어쓰기는 별도 open(로컬 40000 vs 20000줄)" · 34 "truncate된 mmap을 write → SIGBUS" → "EFAULT, 매핑 직접 접근이 SIGBUS(로컬 재현)" · 08 "EEVDF base slice 0.7ms" → "정규화 값, 8코어+ 2.8ms" · 31 "jstack nid는 16진" → "JDK 18부터 10진" · 10 "THP fork 뒤 2MB COW" → "5.8+ 4KB 분할 복사".
- **로컬 재현**: 워커별 C·strace·gdb·/proc 실험 수십 건(모두 scratchpad, 일반 사용자 권한).
- **사고**: 저장소 루트 유출 2회(웹 문서 12개, h·h.c) — 둘 다 scratchpad로 이동, 커밋 전 git status로 확인. 워커 1개 96스레드 벤치로 ~1,200 CPU초(브리핑 취지 초과).
