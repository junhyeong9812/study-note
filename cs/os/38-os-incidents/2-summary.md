# os/38-os-incidents — 실사건 넷: Mars Pathfinder 우선순위 역전 · PostgreSQL fsyncgate · 2012 윤초 hrtimer · ext4 지연 할당 0바이트 파일 — 정리 (힌트)

## 해결하는 문제

leaf 노트는 메커니즘을 **하나씩** 설명한다.\
우선순위 역전은 20번, fsync는 24번, 저널링은 23번, 시간 제한 대기는 17번이다.\
실제 장애에서는 이 메커니즘이 **가정 하나**와 만나 터진다.\
그리고 그 가정은 대개 "지금까지 잘 됐으니까"에서 나온다.

```text
  leaf 노트:  [우선순위 스케줄링] [뮤텍스] [fsync] [writeback] [저널] [타이머]   <- 각각 따로 이해
  실사건:     "라이브러리 뮤텍스는 상속이 켜져 있겠지"   -> 화성에서 리셋
              "fsync 재시도가 성공하면 데이터는 디스크에" -> 조용한 유실
              "벽시계는 앞으로만 간다"                   -> 윤초에 CPU 폭주
              "ext3에서 5초면 디스크에 있었으니까"         -> 0바이트 설정 파일
```

쉬운 예: 오래된 다리다.\
설계 하중을 넘는 트럭이 몇 년째 무사히 지나갔다. 모두 "이 다리는 버틴다"고 믿게 됐다.\
사고는 그 믿음이 **보장**이 아니라 **우연**이었다는 것을 드러낸다.

똑같은 구조다.\
ext3는 저널 커밋의 부산물로 "5초면 데이터도 디스크에" 있게 해 줬다. POSIX는 그것을 약속한 적이 없다.\
ext4가 그 부산물을 없애자, 그 우연에 기댄 애플리케이션의 설정 파일이 0바이트가 됐다.

이 노트는 1차 출처(당사자 메일, 메일링 리스트, 커널 커밋, 벤더 문서)로 네 사건을 복원한다.
- **Mars Pathfinder(1997)**: 상속 없는 뮤텍스 하나가 화성의 착륙선을 반복 리셋시켰다.
- **fsyncgate(2018)**: fsync가 한 번 `EIO`를 내고, 재시도는 "성공"했다. 데이터는 이미 버려져 있었다.
- **2012 윤초**: 윤초 뒤 커널 hrtimer가 1초 어긋나, 시간 제한 대기가 줄줄이 즉시 끝났다. Java·MySQL 등이 CPU를 태웠다.
- **ext4 지연 할당(2009)**: 크래시 뒤 최근에 고친 파일이 0바이트가 됐다.

  - *1차 출처*: 사건 당사자(JPL, PostgreSQL 개발자, 커널 개발자)나 벤더(Red Hat)가 직접 쓴 문서다.

## 동작·원리

### 사건 1 — Mars Pathfinder 우선순위 역전 (1997)

#### 타임라인

```text
  1997-07-04   Pathfinder 화성 착륙                                  (Jones)
  착륙 며칠 뒤  기상 데이터 수집을 시작한 뒤부터 전체 시스템 리셋 반복       (Jones)
               JPL: 같은 활동을 실험실 복제기에서 반복 실행
               "18시간이 안 돼" 재현, 트레이스로 우선순위 역전 확인         (Reeves)
               select 뮤텍스에 우선순위 상속을 켜는 패치를 우주선에 올림     (Reeves)
  1997-12      IEEE RTSS 기조 강연(Wind River CTO David Wilner)           (Jones)
  1997-12-07   Mike Jones가 강연 요약 메일 "What really happened on Mars?"
  1997-12-15   JPL 비행 소프트웨어 책임자 Glenn Reeves의 "공식 설명" 답장
```

- 리셋 날짜별 목록은 두 글에 없다. 이 노트는 날짜를 적지 않는다.

#### 메커니즘 — Reeves의 설명

```text
  우선순위    태스크                     하는 일
  ---------  ------------------------  ----------------------------------------------
  최고        bc_sched                  8 Hz 주기마다 1553 버스 거래 준비, bc_dist 완료 확인
  3위         bc_dist                   버스 결과를 나눠 줌. ASI/MET에는 파이프(IPC)로 보냄
  중간 여럿    그 밖의 우주선 기능 태스크 (Jones는 '통신 태스크'로 요약)
  낮음        ASI/MET(기상 관측)          select()로 파이프 메시지를 기다림

  시간 --->
  ASI/MET  [select -> pipeIoctl -> selNodeAdd: select 뮤텍스 쥔 채 선점당함]
  중간들                                [실행][실행][실행]........
  bc_dist                         [pipeWrite -> 같은 뮤텍스 요청 -> 대기]
  bc_sched                                                     [깨어남: bc_dist 미완료!]
                                                                 -> 오류 선언 -> 전체 리셋
```

- 공유 자원은 VxWorks `select()`가 파일 디스크립터 대기 목록을 보호하려고 만든 **뮤텍스 세마포어**였다. 응용이 직접 만든 락이 아니었다.
- 높은 bc_dist가 낮은 ASI/MET를 기다리는 동안, 중간 태스크들이 ASI/MET를 선점했다. 높은 쪽이 사실상 **중간 태스크들보다 낮은** 우선순위로 떨어졌다.
- 다음 주기에 bc_sched가 "bc_dist가 끝나지 않았다"를 감지했다. 우주선의 대응은 컴퓨터 **전체 리셋**이었다. 그날 남은 지상 명령 활동은 다음 날로 밀렸다.
- 대처: 우선순위 상속을 켰다. VxWorks는 select 서비스가 쓰는 `semMCreate`의 옵션을 **전역 변수**로 제공했다. 이것은 문서에 없던 기능이었다(Reeves). 전역 변수를 바꾸면 이후 만드는 모든 select 세마포어에 적용된다. 그래서 전체 시스템 영향을 분석·시험한 뒤 바꿨다.
- 우선순위 상속 옵션은 Wind River가 성능 때문에 select의 기본값에서 **일부러 뺀** 것이었다(Reeves).

  - *우선순위 역전(priority inversion)*: 높은 우선순위 작업이 낮은 우선순위 작업이 쥔 락을 기다리는데, 중간 우선순위 작업이 낮은 쪽을 선점해 높은 쪽이 무한정 밀리는 현상이다(20번).
  - *우선순위 상속(priority inheritance)*: 락을 쥔 작업이 그 락을 기다리는 가장 높은 우선순위를 잠시 물려받는 것이다. 리눅스 유저 공간에서는 `PTHREAD_PRIO_INHERIT`·PI futex다(20번).

#### 두 1차 기록의 차이

| 항목 | Mike Jones(강연 요약, 12-07) | Glenn Reeves(JPL, 12-15) |
|---|---|---|
| 리셋을 건 것 | 워치독 타이머 | bc_sched가 bc_dist의 주기 미완료를 감지 |
| 공유 자원 | 정보 버스 접근 뮤텍스 | `select()` 내부의 fd 대기 목록 뮤텍스 |
| 패치 방법 | 켜 둔 C 인터프리터로 짧은 프로그램 업로드 | 셸은 쓰지 않음. 차이분을 올리는 전용 패치 절차 |
| 디버그 기능 | "다행히(fortuitously)" 켜 둔 채 발사 | "우연이 아니라 설계" — 시험한 대로 난다 |
| 발사 전 | 한두 번 리셋을 "하드웨어 결함"으로 넘김 | 착륙 전에 봤지만 재현 못 함. 착륙 소프트웨어에 집중, 낮은 우선순위로 둠 |
| 데이터 손실 | 리셋마다 데이터 손실 | 이미 모은 데이터는 잃지 않음(전원이 유지되면 RAM 복구) |

- 두 글이 같이 말하는 것: 원인은 우선순위 역전이고, 해법은 우선순위 상속이며, **트레이스 없이는 찾을 수 없었다**.
- 이 노트는 세부가 다를 때 Reeves(당사자)를 따른다. 20번 노트도 둘의 차이를 짚는다.

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 에러 메시지 없는 전체 리셋, 가끔만 | [20](../20-concurrency-bugs/2-summary.md) · [37](../37-os-symptom-index/2-summary.md) §6 |
| 특정 활동(기상 데이터 수집 + 중간 태스크 부하)이 있을 때만 | [08](../08-cpu-scheduling/2-summary.md) |
| 트레이스: 높은 태스크가 락 대기 → 락 주인은 실행 대기 → 중간 태스크가 CPU 점유 | [20](../20-concurrency-bugs/2-summary.md) · [31](../31-os-observability-tools/2-summary.md) |

### 사건 2 — PostgreSQL fsyncgate (2018)

#### 타임라인

```text
  (이전)        Craig Ringer가 XFS에서 스토리지 오류 뒤 데이터 손상 사례를 겪음
  2018-03-28   pgsql-hackers에 "PostgreSQL's handling of fsync() errors is unsafe
               and risks data loss at least on XFS" 게시
  2018-04-18   LWN "PostgreSQL's fsync() surprise" (Jonathan Corbet)
  2018-04-23   LSFMM 시작 — LWN은 여기서 논의가 이어질 것이라 적음
  2018-04-30   커널에 errseq 수정 병합(병합 커밋 fff75eb2a08c, v4.17-rc4에 포함)
               — 열기 전 오류도 한 번은 보고
  2018-11-19   PostgreSQL 커밋 "PANIC on fsync() failure" (Craig Ringer 작성, Thomas Munro 수정·커밋)
               새 설정 data_sync_retry(기본 off), 지원 중인 모든 판에 백포트
  2019-02-14   PostgreSQL 11.2 등 릴리스 — "fsync() 실패 뒤 재시도 대신 panic"
```

#### 메커니즘 — Ringer의 첫 메일

```text
  PostgreSQL                      커널(XFS)                            디스크
  ----------                      ---------                            ------
  write(블록) ---> 페이지 캐시 (dirty)
                                  백그라운드 writeback ---------------> 오류!
                                  매핑에 AS_EIO 표시(Ringer), 페이지는 clean 처리(LWN)
  checkpoint: fsync() <---------- EIO  (표시를 보고 한 번 알림, 표시를 지움)
  "체크포인트 실패, 재시도"
  checkpoint: fsync() <---------- 0 (성공)  -- 보낼 dirty 페이지가 없다
  "체크포인트 완료" -> redo 시작점 전진 -> 그 블록을 다시 쓸 WAL 기준이 사라짐
                                                                     데이터: 없음
```

- Ringer의 요약: PostgreSQL은 fsync 성공을 "**마지막 성공한** fsync 이후의 쓰기가 모두 디스크에 있다"로 믿었다. 실제 뜻은 "**마지막** fsync 이후"였다.
- Ringer는 ext3·ext4를 `errors=remount-ro`로 썼다면 첫 I/O 오류에서 읽기 전용이 되어 이 일이 없었을 것이라 적었다. XFS에는 그 옵션이 없다고 적었다.
  - 단서: 이것은 Ringer의 주장이다. `errors=`는 파일 시스템(메타데이터·저널) 오류에 반응한다. 파일 **데이터** 쓰기 오류는 기본값 `data_err=ignore`에서 메시지만 찍는다(커널 문서 ext4 admin guide). 저널 중단을 원하면 `data_err=abort`가 필요하다(v7.0 `fs/ext4/page-io.c`, v4.16 `fs/jbd2/commit.c`).
- 복구: 잘못 성공한 첫 체크포인트 **이전**의 백업 레이블을 꾸며 넣어, redo가 잃어버린 블록을 다시 쓰게 했다(Ringer).

LWN이 정리한 두 번째 구멍 — **오류 전에 열린 fd만 오류를 본다**:

- PostgreSQL에서 fsync는 checkpointer 프로세스 하나가 한다. checkpointer는 파일을 늘 열어 두지 않고, fsync 직전에 연다.
- LWN(2018-04-18) 시점 설명: 4.13 이후 커널도 **파일을 열기 전에** 난 writeback 오류는 그 fd에 보고하지 않았다. 그러면 뒤이은 fsync는 성공한다.
  - 4.13의 errseq_t가 "열기 전 오류는 관심 없다"고 가정했기 때문이다. 커널 커밋 b4678df184b3 "errseq: Always report a writeback error once"(Matthew Wilcox, 2018-04-24 작성, 4.17 개발 주기 병합, stable Cc)가 이것을 "아직 아무 fd에도 보고되지 않은 오류는 나중에 연 fd에도 한 번 보고"로 되돌렸다. 커밋은 이 동작 변화를 PostgreSQL에 대한 회귀라고 적었다.
  - 그래도 오류는 **한 번만** 보고된다. 재시도가 안전해진 것은 아니다.
- 커널 쪽 이유(Ts'o, LWN): I/O 오류의 가장 흔한 원인은 USB 장치를 잘못 뽑는 것이다. 실패한 dirty 페이지를 계속 쥐면 메모리가 고갈될 수 있다. 그래서 버린다.
- Chinner·Ts'o의 장기 권고: Direct I/O로 옮겨 어떤 쓰기가 실패했는지 직접 알라(LWN).

PostgreSQL 위키 "Fsync Errors"의 리눅스 판별 정리:

| 커널 | 동작 |
|---|---|
| 4.13 이전 | fsync 오류를 여러 경로로 잃을 수 있음. 오류 뒤 버퍼는 clean → 재시도가 거짓 성공 |
| 4.13, 4.15 | `open()` **뒤에** 난 writeback 오류만 보고 → 닫았다 다시 여는 방식이 오류를 숨김. 재시도 거짓 성공 |
| 4.14, 4.16 이상 | 오류 카운터 초기화가 달라져, 닫았다 연 경우에도 누군가는 inode의 첫 오류를 받음. 단 **한 번만** 받음 → 재시도는 여전히 안전하지 않음. 버퍼는 여전히 버려짐 |

- 같은 위키: FreeBSD는 버퍼를 dirty로 유지해 다음 fsync가 다시 시도한다(11.1부터는 장치가 사라지면 버림). NetBSD·OpenBSD·macOS는 버퍼를 무효화한다. ZFS는 페이지 캐시를 쓰지 않아 특수한 경우다.
- 같은 위키: InnoDB/MySQL, WiredTiger/MongoDB도 이 일을 계기로 비슷하게 바꿨다.

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 커널 로그의 블록 장치 I/O 오류 | [24](../24-fsync-and-durability/2-summary.md) · [32](../32-raid/2-summary.md) |
| 앱 로그: fsync 실패 **1회** 뒤 재시도 성공, 이후 조용 | [24](../24-fsync-and-durability/2-summary.md) · [37](../37-os-symptom-index/2-summary.md) §2 `EIO` |
| 한참 뒤 옛 값·빠진 블록·체크섬 오류 | [33](../33-data-integrity-checksums/2-summary.md) · [23](../23-crash-consistency-and-journaling/2-summary.md) |
| 수정 이후: `could not fsync file "...": Input/output error`로 PANIC | [24](../24-fsync-and-durability/2-summary.md) |

### 사건 3 — 2012 윤초와 hrtimer (2012-06-30)

#### 타임라인 (UTC)

```text
  2012-01-05   IERS Bulletin C 43: 2012-06-30 끝에 양의 윤초 삽입 공지
  2012-06-30   23:59:59 -> 23:59:60 -> 2012-07-01 00:00:00      (Bulletin C 43)
               리눅스는 00:00 뒤 첫 시계 갱신에서 시스템 시계를 1초 뒤로 되돌려 삽입 (Red Hat)
  그 뒤         futex를 많이 쓰는 앱, 특히 java의 CPU 사용률 급증 (Red Hat, RHEL 6 GA~6.3)
               MySQL CPU 급증 사례와 우회책 date -s "`date`" (커널 커밋이 인용한 글)
  2012-07-10   John Stultz 수정 패치 작성 ("Fix leapsecond triggered load spike issue" 등)
  2012-07-11   Thomas Gleixner가 커밋 (Cc: stable)
  2012-07-14   Linux 3.5-rc7 태그 — 수정 포함
```

- Red Hat은 같은 윤초의 **다른** 문제도 따로 적었다: 윤초 삽입 알림을 받은 시스템이 livelock으로 멈추고 NMI 워치독이 잡는 경우(RHEL 6.1~6.3). 이 노트의 CPU 폭주와 별개의 버그다.
- 어느 커널 판부터 이 버그가 있었는지는 이 노트가 읽은 출처에 없다 [?].
- MySQL 사례는 커널 커밋이 근거로 인용한 글(`sheeri.com/content/mysql-and-leap-second-high-cpu-and-fix`)의 제목과 커밋 본문으로만 확인했다. 그 글 자체는 작성 시점에 열리지 않았다(보관본도 없음).

#### 메커니즘 — 커밋 메시지 기준

```text
  timekeeping (벽시계)            hrtimer (CLOCK_REALTIME 타이머의 기준)
  -------------------            -------------------------------------
  윤초: 벽시계 1초 되돌림            기준 오프셋 갱신 안 됨 (clock_was_set() 누락)
          |                                  |
          +--------- 두 시계가 1초 어긋남 ------+
                                             v
               CLOCK_REALTIME 기준 타이머가 1초 **일찍** 만료 (삽입의 경우)
               이 어긋남은 누가 clock_was_set()을 부를 때까지 영원히 남는다

  앱: "지금 + 0.3초까지 기다려" (절대 기한, CLOCK_REALTIME)
      -> 타이머 입장에서는 이미 0.7초 지난 기한 -> 즉시 타임아웃
      -> 루프가 다시 "지금 + 0.3초" -> 즉시 타임아웃 -> ... CPU 폭주
```

- 커밋 "timekeeping: Fix leapsecond triggered load spike issue": 윤초 뒤 타임키핑 코드가 hrtimer 서브시스템 갱신을 빠뜨렸다. CLOCK_REALTIME 기반 타이머가 윤초 삽입이면 1초 일찍, 삭제면 1초 늦게 만료된다. 다른 경로로 갱신될 때까지 이 차이가 **영원히** 남는다.
- 우회책 ``date -s "`date`"``가 통한 이유: 시계를 설정하면 `clock_was_set()`이 불려 hrtimer 자료가 갱신된다(같은 커밋).
- 수정: 윤초 이벤트 때 `update_wall_time()`에서 `clock_was_set()`을 부르게 했다. 이 갱신은 모든 CPU에 함수 호출을 보내야 해서 하드 인터럽트 문맥에서 못 한다. 그래서 softirq로 미룬다(`clock_was_set_delayed()` 커밋). 또 `hrtimer_interrupt`가 매번 오프셋을 갱신하게 했다. 시계 변경과 `clock_was_set()` 사이의 틈에 온 인터럽트가 새 시각과 낡은 오프셋을 섞어 쓰지 않게 하려는 것이다(5baefd6d8416 커밋 메시지).
- **futex와의 연결은 추론이 섞여 있다.** Red Hat은 "futex를 많이 쓰는 앱"이라고만 적는다. 시간 제한 대기(`pthread_cond_timedwait`의 기본 시계는 CLOCK_REALTIME, 17번)가 futex로 내려가고, 기한이 1초 안쪽이면 즉시 만료되어 재시도 루프가 돈다는 설명은 커밋 내용과 17번에서 이어지는 추론이다. Java·MySQL의 정확한 코드 경로는 이 노트가 읽은 출처에 없다 [?].

로컬 흉내(예시, 리눅스 7.0): 커널 버그를 재현할 수는 없다(시계 변경은 root). 대신 "기한이 1초 과거"인 상황을 코드로 만들었다.

```text
  pthread_cond_timedwait(기한 = 지금 + 0.5초), 2초 동안 반복
    정상                   : 4회,          sys 0.00초
    기한에서 1초를 뺌(흉내)  : 1,354,048회,  sys 1.79초  (한 코어가 커널 시간으로 가득)
```

- 이 흉내는 CPU가 **sys** 시간으로 차는 모양을 보여 준다. 앱 프로파일러에는 뜨거운 함수가 안 보이는 유형이다(37번 §5 "`sy` > `us`").

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 배포·트래픽 변화 없이 **특정 시각**(UTC 자정 직후)부터 여러 서버 CPU 동시 상승 | [37](../37-os-symptom-index/2-summary.md) §5 |
| `sy` 비중이 크고 `strace -c`에 `futex`가 많음 | [16](../16-locks-and-spinlocks/2-summary.md) · [02](../02-system-calls/2-summary.md) |
| 재시작하지 않아도 시계를 다시 설정하면 가라앉음 | [17](../17-condition-variables-and-monitors/2-summary.md) |

### 사건 4 — ext4 지연 할당과 0바이트 파일 (2009)

#### 타임라인

```text
  2009-01-16   Ubuntu Launchpad 버그 #317781 "Ext4 data loss" 등록
               (Ubuntu 9.04 개발판, 커널 2.6.28, ext4 기본 설정)
               "크래시 뒤 재부팅하니 직전 부팅에서 앱이 쓴 거의 모든 파일이 0바이트"
  2009-03-06~07  Ted Ts'o가 같은 버그에 원인과 안전한 쓰기 패턴을 설명
  2009-03-11   LWN "ext4 and data loss" (Jonathan Corbet)
               완화 패치 셋이 2.6.30에 들어갈 예정
  2009-06-09   Linux 2.6.30 릴리스(커널 git 태그 v2.6.30, 미국 시각) — rename·truncate 시
               지연 할당 블록 자동 할당 (LWN·Ts'o 댓글: 2.6.30 병합 예정 패치),
               auto_da_alloc 마운트 옵션
```

#### 메커니즘 — ext3의 우연, ext4의 지연 할당

```text
  앱 패턴 (Ts'o의 분류)
   (1) open(O_TRUNC) -> write -> close                         위험
   (2) open(new) -> write -> close -> rename(new, old)          위험
   (3) open(new) -> write -> fsync(+오류 확인) -> close -> rename 이것만 보장

  ext3 data=ordered                          ext4 (지연 할당)
  ------------------                         --------------------------------
  5초마다 저널 커밋                            5초마다 저널 커밋
  커밋 전에 바뀐 데이터 블록을 먼저 기록          블록이 아직 **할당 안 됨** -> 커밋에 딸려 가지 않음
  -> "5초 뒤면 데이터도 디스크에" (우연)          -> 메타데이터(크기 0, rename)만 먼저 영속
                                             데이터는 writeback이 할 때 (기본 설정에서 1분 가까이)
  크래시: 잃는 건 5초 정도                      크래시: 파일 이름은 새것, 내용은 0바이트
```

- ext3의 "5초 보장"은 data=ordered 설계의 부산물이었다. 파일 시스템 저자도, POSIX도 약속하지 않았다(LWN, Ts'o).
- 지연 할당은 블록 할당을 최대한 늦춘다. 짧게 살다 지워지는 임시 파일은 디스크에 아예 안 쓰고, 오래 사는 파일은 연속 블록을 받게 한다. 성능 최적화다(LWN).
- 할당되지 않은 블록은 "다른 사람의 옛 데이터를 읽을" 보안 문제가 없어 저널 커밋 전에 서둘러 쓸 이유가 없다. 그래서 다음 커밋에 딸려 나가지 않는다(LWN).
- LWN이 든 writeback 기본값: `dirty_expire_centisecs` 30초, `dirty_writeback_centisecs` 5초(2009년 글 기준).
- Ts'o의 입장: 파일 시스템이 파일을 자른 것이 아니라 **애플리케이션이** 잘랐다(`O_TRUNC`). (3)만이 데이터 손실이 없음을 보장한다. XFS도 지연 할당을 한다.

2.6.30의 완화책(LWN, kernelnewbies):
- `EXT4_IOC_ALLOC_DA_BLKS` ioctl: 파일의 지연 할당 블록을 강제로 할당한다.
- truncate된 파일을 close할 때 지연 할당 블록을 할당한다.
- 다른 파일 위로 rename할 때 블록을 할당한다.
- 이것이 오늘의 `auto_da_alloc`(기본 켜짐)이다. ext4 문서: rename·truncate로 바꾸는 패턴을 감지해, data=ordered에서 rename 커밋 **전에** 새 파일 데이터를 디스크로 보낸다. "대략 ext3 수준"의 보장이다.
- 23번 노트가 적듯 이것은 흔한 패턴의 완화이지 보장이 아니다. 새 파일·디렉터리 fsync 순서는 24번이 정본이다.

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 크래시·정전 뒤 **최근에 고친** 설정 파일들이 0바이트, 에러 로그 없음 | [23](../23-crash-consistency-and-journaling/2-summary.md) · [37](../37-os-symptom-index/2-summary.md) §6 |
| ext3에서 ext4로 바꾼 뒤에만 나타남 | [22](../22-file-system-implementation/2-summary.md) · [23](../23-crash-consistency-and-journaling/2-summary.md) |
| 앱 코드에 `fsync` 없는 `O_TRUNC` 덮어쓰기·rename 교체 | [24](../24-fsync-and-durability/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **우선순위 큐 스케줄링 + 대기 사슬** — Pathfinder의 태스크는 고정 우선순위 선점 스케줄링으로 돌았다. 우선순위 상속은 "누가 누구를 기다리나" 사슬을 따라 우선순위를 올린다. 리눅스 PI futex는 커널 안에서 rt-mutex(우선순위 상속을 아는 뮤텍스)로 이 사슬을 관리한다(커널 문서 pi-futex, 20번). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **링 버퍼 트레이스** — Pathfinder의 trace/log 기능은 시작부터 링 버퍼에 이벤트를 모으고, 오류 시 멈춰 덤프했다(Reeves). 최근 N개만 싸게 유지하는 구조다. [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)
- **errseq_t — 오류 코드 + 순번 카운터 + "봤음" 비트** — 커널 4.13의 writeback 오류 보고 구조다. 32비트 안에 마지막 오류 코드와 카운터를 넣는다. 구독자(fd)는 값을 표본으로 저장했다가 바뀌었는지 비교한다(`lib/errseq.c`). fsyncgate의 "누가 언제 오류를 보나" 논쟁이 이 구조의 표본 시점 문제다.
- **레드블랙 트리 타이머 큐** — hrtimer는 만료 시각 순으로 레드블랙 트리(`lib/timerqueue.c`)에 타이머를 둔다. 윤초 버그는 트리가 아니라 **기준 시각 오프셋**이 낡은 문제였다. 정렬은 맞는데 "지금"이 1초 틀렸다. [data-structure/16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)
- **저널 + 지연 할당** — 메타데이터 저널이 커밋 순서를 정하고, 지연 할당이 데이터 블록 할당을 뒤로 미룬다. 둘의 순서 관계가 0바이트 파일을 만들었다(23번).

## 적용 — 풀어나가는 법

### 1. 사후 분석을 읽는 순서

```text
  1) 타임라인       관측 시각(누가 봤나)과 원인 시각을 구분한다
  2) 믿었던 가정     "상속이 켜져 있겠지", "재시도 성공 = 안전", "시계는 앞으로만", "5초면 디스크"
  3) 그 가정의 출처   문서·표준인가, 관찰된 우연인가
  4) 보인 신호       밖에서 무엇으로 알 수 있었나 -> 37번 색인과 대조
  5) 복구 수단       트레이스·패치 경로·WAL·시계 재설정 — 미리 있었나
  6) 교훈           "누가 틀렸나"가 아니라 "무엇이 우연을 보장으로 착각하게 했나"
```

### 2. 네 사건에서 내 시스템으로 옮길 점검 목록

- **Pathfinder 형**
  - 우선순위가 다른 스레드가 공유하는 락은 PI 뮤텍스인가(`PTHREAD_PRIO_INHERIT`). 라이브러리 **내부** 락은 어떻게 만들어지나.
  - 실시간 스레드에서 유저 공간 스핀락을 쓰지 않는가(20번).
  - 재현되지 않는 리셋·재시작을 "하드웨어 탓"으로 닫지 않는가. 운영에서 켜 둘 수 있는 트레이스가 있는가.
- **fsyncgate 형**
  - fsync 실패를 재시도로 덮는 코드가 있는가. 실패하면 로그(WAL)·복제본에서 다시 만드는가(24번).
  - fsync를 부르는 fd가 **쓰기 전부터** 열려 있었나.
  - 블록 장치 오류를 커널 로그에서 감시하는가.
- **윤초 형**
  - 기한·간격 측정에 CLOCK_REALTIME을 쓰는가. `CLOCK_MONOTONIC`·`pthread_cond_clockwait`로 바꿀 수 있는가(17번).
  - 시계 이벤트(윤초·NTP 스텝) 직후의 CPU·지연을 감시하는가. 시간 서버가 윤초를 한 번에 되돌리지 않고 천천히 나눠 반영(smear)하는지 확인한다. Red Hat 문서: RHEL 6.8·7.2의 chrony 서버 옵션이며, 클라이언트는 모두 같은 방식의 서버만 봐야 한다.
- **ext4 형**
  - 설정·상태 파일을 "임시 파일 + fsync + rename + 디렉터리 fsync"로 쓰는가(24번).
  - `O_TRUNC` 뒤 덮어쓰기를 하는가.
  - 파일 시스템을 바꿀 때 "지금까지 잘 된 이유"가 보장인지 우연인지 확인했나.

### 3. 확인 명령

```bash
# fsyncgate 형: 블록 장치 오류와 앱의 fsync 반환값
journalctl -k | grep -iE 'I/O error|blk_update_request|Buffer I/O error'   # 권한 필요
strace -f -e trace=fsync,fdatasync -p <pid> 2>&1 | grep -v '= 0$'           # 0이 아닌 반환만

# 윤초 형: 시계 상태와 futex 비중
timedatectl; chronyc tracking 2>/dev/null || ntpq -p                       # 동기화 상태
timeout 5 strace -f -c -p <pid> 2>&1 | head -15                             # futex 호출 비중

# ext4 형: 마운트 옵션과 쓰기 패턴
cat /proc/fs/ext4/<dev>/options | grep -E 'data=|auto_da_alloc'           # 기본값까지 보인다
grep -E ' ext4 ' /proc/mounts                                              # 기본값이 아닌 옵션만(noauto_da_alloc, data=writeback 등)
strace -f -e trace=openat,write,fsync,fdatasync,rename,renameat2 <명령>    # O_TRUNC·fsync·rename 순서

# Pathfinder 형: 리눅스에서 PI 뮤텍스 여부 (glibc)
#   pthread_mutexattr_getprotocol() == PTHREAD_PRIO_INHERIT 인지 코드에서 확인
```

- 명령의 상세와 오버헤드는 [31-os-observability-tools](../31-os-observability-tools/2-summary.md)에 있다.

## 장애 시나리오와 대처

### 1. 가끔 나는 재시작을 "하드웨어 탓"으로 닫는다 — Pathfinder 형

- **현상**: 임베디드 장비·실시간 서비스가 드물게 전체 리셋·워치독 재시작을 한다. 재현이 안 된다.
- **보이는 형태**
  - 에러 로그 없는 재시작, 마감 초과 경보.
  - 특정 작업 조합(낮은 우선순위 작업 + 중간 부하)일 때만.
- **원인**: 낮은 우선순위 작업이 쥔 락을 높은 작업이 기다리는데, 중간 작업이 낮은 쪽을 선점했다. 락이 **상속 없는** 뮤텍스였다. Pathfinder에서는 라이브러리(`select`) 내부 락이라 응용 코드만 봐서는 보이지 않았다.
- **대처**
  - 공유 락을 우선순위 상속 뮤텍스로 만든다([20](../20-concurrency-bugs/2-summary.md), [16](../16-locks-and-spinlocks/2-summary.md)).
  - 운영에서 켜 둘 수 있는 트레이스(링 버퍼)를 두고, 오류 시 덤프를 남긴다. Reeves: 트레이스 덕에 18시간 안에 재현·확인했다.
  - 외부 구성 요소는 **어떻게 동작하는지 확인하고** 쓴다(Reeves의 교훈: "COTS를 쓸 때는 어떻게 동작하는지 알아 두라").

### 2. fsync `EIO` 뒤 재시도 성공을 믿는다 — fsyncgate 형

- **현상**: 스토리지 순간 장애 뒤 DB가 계속 돌았다. 며칠 뒤 일부 데이터가 없거나 옛 값이다.
- **보이는 형태**: 장애 시각 커널 로그의 블록 장치 오류, 앱 로그의 fsync 실패 1회 → 재시도 성공. 그 뒤 에러 없음.
- **원인**: writeback 실패로 페이지가 clean 처리되어 버려졌다. 첫 fsync가 오류를 한 번 알렸고, 재시도는 보낼 것이 없어 성공했다. 또는 오류 뒤에 연 fd라 오류를 아예 못 봤다(4.13·4.15, PostgreSQL 위키).
- **대처**
  - fsync 실패를 재시도로 덮지 않는다. PostgreSQL처럼 멈추고 WAL에서 다시 만든다([24](../24-fsync-and-durability/2-summary.md)).
  - 오래 쓰는 파일은 쓰기 전부터 열어 둔 fd로 fsync한다.
  - 커널 로그의 I/O 오류를 경보로 올린다. 데이터 체크섬으로 사후에라도 잡는다([33](../33-data-integrity-checksums/2-summary.md)).

### 3. 시계 이벤트 뒤 CPU가 차오른다 — 윤초 형

- **현상**: 배포도 트래픽 변화도 없는데 UTC 자정 직후부터 많은 서버의 CPU가 동시에 오른다. 재시작하면 가라앉는다.
- **보이는 형태**: `sy` 비중이 크다. `strace -c`에 `futex`가 많다. 여러 제품(JVM, DB)이 동시에 영향을 받는다.
- **원인**: 윤초 뒤 커널 hrtimer의 CLOCK_REALTIME 기준이 1초 어긋나 절대 기한 대기가 즉시 끝났다. 대기 루프가 헛돌았다(2012 커널 커밋).
- **대처**
  - 당시 우회책: 시계를 다시 설정(``date -s "`date`"``)해 `clock_was_set()`을 부른다(커밋 메시지). 근본은 수정 커널로 올리는 것이다.
  - 간격·기한 측정에는 `CLOCK_MONOTONIC`을 쓴다([17](../17-condition-variables-and-monitors/2-summary.md) 시나리오 5).
  - "많은 서버가 같은 시각에"는 공통 외부 사건(시계·인증서 만료·설정 배포)을 먼저 의심하는 신호다.

### 4. 재부팅 뒤 설정 파일이 0바이트 — ext4 형

- **현상**: 정전·크래시 뒤 앱이 설정을 못 읽고 기본값으로 뜬다. 최근에 저장한 파일들이다.
- **보이는 형태**: `ls -l`에 크기 0, 파서 에러(`Unexpected end of JSON input` 류). 저장 당시 에러는 없었다.
- **원인**: `O_TRUNC` 덮어쓰기나 fsync 없는 rename 교체. 지연 할당 때문에 메타데이터(크기 0, 새 이름)가 데이터보다 먼저 영속됐다(LWN 322823).
- **대처**
  - 임시 파일 + fsync + rename + 디렉터리 fsync로 쓴다([24](../24-fsync-and-durability/2-summary.md)).
  - `auto_da_alloc`은 흔한 패턴의 완화책일 뿐이다. `noauto_da_alloc`으로 마운트된 곳도 있을 수 있다([23](../23-crash-consistency-and-journaling/2-summary.md)).
  - 읽을 때 빈 파일·파싱 실패를 감지해 백업 사본으로 되돌린다.

### 5. "지금까지 잘 됐다"를 보장으로 착각한다 — 네 사건 공통

- **현상**: 환경 하나(파일 시스템, 커널, 라이브러리 기본값, 데이터 양)를 바꾼 뒤 오래된 코드가 깨진다.
- **보이는 형태**: 바뀐 것은 환경인데 깨진 것은 앱이다. "우리 코드는 몇 년째 그대로"라는 반응.
- **원인**
  - ext3의 5초, Wind River의 성능 우선 기본값, "재시도 성공 = 안전", "벽시계는 1초씩 앞으로" — 모두 **관찰된 동작**이었지 문서화된 약속이 아니었다.
  - Pathfinder에서는 화성 표면의 데이터 속도가 예상보다 높아 부하 조건이 시험 범위 밖으로 나갔다(Reeves: "기대 이상으로 좋은 경우"를 시험하지 않았다).
- **대처**
  - 의존하는 동작마다 **근거 문서**(POSIX, man, 벤더 문서)를 찾는다. 없으면 우연으로 취급하고 방어 코드를 둔다.
  - 시험 범위를 "최선의 경우"만이 아니라 부하·장애·시계 이벤트까지 넓힌다.

## 핵심 문장

- 네 사건 모두 메커니즘 하나가 **보장이 아닌 가정**과 만나 터졌다. 증상은 에러 없는 리셋, 조용한 유실, 이유 없는 CPU, 0바이트 파일이었다.
- Pathfinder(1997): select 내부 뮤텍스에 우선순위 상속이 꺼져 있어, 중간 태스크가 낮은 태스크를 선점하는 동안 높은 태스크가 마감을 놓쳤다. 전역 변수로 상속을 켜 고쳤고, 트레이스가 없었으면 찾지 못했다.
- fsyncgate(2018): 리눅스는 writeback 실패 페이지를 clean으로 버리고 오류를 한 번만 알린다. fsync 재시도 성공은 데이터가 디스크에 있다는 뜻이 아니다. PostgreSQL은 fsync 실패에 PANIC하도록 바꿨다.
- 2012 윤초: 윤초 뒤 hrtimer 기준 갱신이 빠져 CLOCK_REALTIME 타이머가 1초 일찍 만료됐다. 시간 제한 대기가 헛돌아 Java·MySQL 등이 CPU를 태웠다. 3.5-rc7에 수정이 들어갔다.
- ext4(2009): 지연 할당은 ext3가 우연히 주던 "5초 뒤 디스크"를 없앴다. fsync 없는 덮어쓰기·교체가 0바이트 파일을 만들었고, 2.6.30의 `auto_da_alloc`이 흔한 패턴만 완화했다.

## 관련 주제·근거

- 선행
  - [37-os-symptom-index](../37-os-symptom-index/2-summary.md) — 사건마다 보인 신호를 원인 leaf로 잇는 색인
  - [20-concurrency-bugs](../20-concurrency-bugs/2-summary.md) — 우선순위 역전, Pathfinder 요약
  - [24-fsync-and-durability](../24-fsync-and-durability/2-summary.md) — fsyncgate 메커니즘, 안전한 교체 순서
  - [23-crash-consistency-and-journaling](../23-crash-consistency-and-journaling/2-summary.md) — 지연 할당·0바이트 파일·`auto_da_alloc`
  - [17-condition-variables-and-monitors](../17-condition-variables-and-monitors/2-summary.md) — CLOCK_REALTIME 기한 대기(시나리오 5)
- 연결
  - 커널 문서 Documentation/locking/pi-futex.rst — PI futex의 rt-mutex <https://docs.kernel.org/locking/pi-futex.html>
  - [16-locks-and-spinlocks](../16-locks-and-spinlocks/2-summary.md) — futex, PI · [08-cpu-scheduling](../08-cpu-scheduling/2-summary.md) — 우선순위·실시간 정책 · [14-mmap-and-page-cache](../14-mmap-and-page-cache/2-summary.md) — dirty writeback · [33-data-integrity-checksums](../33-data-integrity-checksums/2-summary.md) · [31-os-observability-tools](../31-os-observability-tools/2-summary.md)
  - 물리 시계·NTP·윤초는 [distributed/04-physical-clocks-and-ntp](../../distributed/04-physical-clocks-and-ntp/2-summary.md)
- Mars Pathfinder
  - Mike Jones, "What really happened on Mars?"(1997-12-07) — 착륙 1997-07-04, RTSS 기조 강연 요약, Sha·Rajkumar·Lehoczky 1990 <https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html> · 사본 <http://web.archive.org/web/2010/http://research.microsoft.com/en-us/um/people/mbj/Mars_Pathfinder/Mars_Pathfinder.html>
  - Glenn Reeves(JPL), "What really happened on Mars? — Authoritative Account"(1997-12-15) — 태스크 구조, select 뮤텍스, 18시간 재현, 전역 변수 패치, 교훈 <https://www.cs.unc.edu/~anderson/teach/comp790/papers/mars_pathfinder_long_version.html> · RISKS 게시본 <https://users.cs.duke.edu/~carla/mars.html>
- fsyncgate
  - Craig Ringer, pgsql-hackers "PostgreSQL's handling of fsync() errors is unsafe and risks data loss at least on XFS"(2018-03-28) <https://www.postgresql.org/message-id/CAMsr%2BYHh%2B5Oq4xziwwoEfhoTZgr07vdGG%2Bhu%3D1adXx59aTeaoQ%40mail.gmail.com>
  - LWN, Jonathan Corbet, "PostgreSQL's fsync() surprise"(2018-04-18) <https://lwn.net/Articles/752063/>
  - PostgreSQL wiki "Fsync Errors" — 커널 판별 동작, 다른 OS, 백포트 <https://wiki.postgresql.org/wiki/Fsync_Errors>
  - PostgreSQL 커밋 9ccdd7f66e33 "PANIC on fsync() failure"(2018-11-19, Author: Craig Ringer, with some adjustments by Thomas Munro) <https://github.com/postgres/postgres/commit/9ccdd7f66e3324d2b6d3dec282cfa9ff084083f1> · 11.2 릴리스 노트(2019-02-14) <https://www.postgresql.org/docs/release/11.2/>
  - 커널 `lib/errseq.c` — errseq_t 구조 설명 <https://github.com/torvalds/linux/blob/master/lib/errseq.c> · 커밋 b4678df184b3 "errseq: Always report a writeback error once"(2018-04-24, 병합 2018-04-30 `errseq-v4.17`, 병합 커밋 fff75eb2a08c — inode가 캐시에서 밀려나면 여전히 잃을 수 있음) <https://github.com/torvalds/linux/commit/b4678df184b314a2bd47d2329feca2c2534aa12b>
- 2012 윤초
  - IERS Bulletin C 43(2012-01-05) <https://hpiers.obspm.fr/iers/bul/bulc/bulletinc.43>
  - 커널 커밋 4873fa070ae8 "timekeeping: Fix leapsecond triggered load spike issue"(John Stultz, 2012-07-10) <https://github.com/torvalds/linux/commit/4873fa070ae84a4115f0b3c9dfabc224f1bc7c51> · f55a6faa3843 "hrtimer: Provide clock_was_set_delayed()" · 5baefd6d8416 "hrtimer: Update hrtimer base offsets each hrtimer_interrupt" — 모두 v3.5-rc7(2012-07-14)에 포함, LKML 링크 `1341960205-56738-*-git-send-email-johnstul@us.ibm.com`
  - Red Hat, "Resolve Leap Second Issues in Red Hat Enterprise Linux" — 리눅스의 삽입 방식(1초 되돌림), RHEL 6 문제 목록 <https://access.redhat.com/articles/15145> · Solution 154793(현재 제목 "High CPU usage after inserting leap second", 15145 문서의 링크 이름은 "Why is there high CPU usage after inserting the leap second?") — Issue 절 "notably java", Environment RHEL 6 GA~6.3, 본문은 구독자 전용 <https://access.redhat.com/solutions/154793> · Solution 154713 "Systems hang due to leap-second livelock"(Issue: NMI 워치독이 hang 감지, RHEL 6.1~6.3) <https://access.redhat.com/solutions/154713>
- ext4 2009
  - Ubuntu Launchpad 버그 #317781 "Ext4 data loss"(2009-01-16 등록), Ted Ts'o 댓글(2009-03-06~07) <https://bugs.launchpad.net/ubuntu/+source/linux/+bug/317781>
  - LWN, Jonathan Corbet, "ext4 and data loss"(2009-03-11) <https://lwn.net/Articles/322823/>
  - kernelnewbies "Linux 2.6.30"(ext4 rename·close 시 자동 할당, `auto_da_alloc` 옵션 커밋 목록) <https://kernelnewbies.org/Linux_2_6_30> · 릴리스 날짜는 커널 git 태그 v2.6.30(커밋 07a2039b8eb0)
  - 커널 문서 ext4 admin guide `auto_da_alloc`, `errors=remount-ro`, `data_err=ignore(*)`/`abort` <https://docs.kernel.org/admin-guide/ext4.html>
  - Linux v7.0 `fs/ext4/page-io.c`(writeback 실패 시 `DATA_ERR_ABORT`면 `jbd2_journal_abort`), `fs/ext4/super.c` `_ext4_show_options()`(`nodefs`: `/proc/mounts`는 기본값 생략); v4.16 `fs/jbd2/commit.c`(`JBD2_ABORT_ON_SYNCDATA_ERR`일 때만 abort) <https://github.com/torvalds/linux>
  - 로컬 재현(리눅스 7.0): `/proc/mounts`는 `rw,relatime`만, `/proc/fs/ext4/<dev>/options`는 `data=ordered`·`auto_da_alloc`까지 보임
- 로컬 재현(2026-09-30, 리눅스 7.0, gcc 13.3): `pthread_cond_timedwait` 기한을 1초 과거로 흉내 — 2초에 4회 대 135만 회, sys 1.79초
