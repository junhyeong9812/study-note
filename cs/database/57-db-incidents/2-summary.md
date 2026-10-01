# database/57-db-incidents — 실사건 셋: GitLab DB 삭제와 백업 전멸(2017) · Sentry XID wraparound(2015) · GitHub MySQL 페일오버 불일치(2018) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 메커니즘을 **하나씩** 설명한다.\
WAL 보존은 19·32번, 백업과 PITR은 20번, XID 동결은 16번, 비동기 페일오버는 32번이다.\
실제 장애에서는 메커니즘 여러 개가 **한 줄로 이어져** 터진다.\
그리고 그 사슬의 고리마다 "이건 괜찮겠지"라는 가정이 하나씩 있다.

```text
  leaf 노트:  [WAL 보존] [복제] [백업·PITR] [XID 동결] [autovacuum] [페일오버] [복제 지연]  <- 각각 따로
  실사건:
    GitLab  부하 -> 복제 끊김 -> 수동 재구축 -> 잘못된 서버에서 삭제 -> 백업 셋 못 씀, 스테이징용 LVM 스냅숏으로 복구
    Sentry  쓰기 많은 거대 테이블 -> 동결이 못 따라감 -> 쓰기 거부 -> 몇 시간 대기
    GitHub  43초 네트워크 단절 -> 자동 승격 -> 양쪽에 서로 없는 쓰기 -> 24시간 11분
```

쉬운 예: 건물의 방화 설비다.\
스프링클러·소화기·방화문·비상계단이 다 있다. 점검표에도 모두 "있음"이다.\
불이 나서야 스프링클러 밸브가 잠겨 있었고, 방화문은 받쳐 놓았다는 것을 안다.\
설비가 **있다**와 **작동한다**는 다른 말이다.

똑같은 구조다.\
GitLab은 백업 절차를 넷 두었다. 사고 당일 바로 쓸 수 있는 것은 없었다.\
결국 쓴 것은 백업용이 아닌 스테이징 복사용 LVM 스냅숏이었다.

이 노트는 사건 당사자가 직접 쓴 사후 분석(1차 출처)으로 세 사건을 복원한다.
- **GitLab.com(2017-01-31)**: 복제를 다시 맞추다 운영 DB 디렉터리를 지웠다. `pg_dump` 백업·Azure 디스크 스냅숏·복제는 쓸 수 없었고, 백업용이 아닌 스테이징 복사용 LVM 스냅숏(약 6시간 전)으로 복구했다.
- **Sentry(2015-07-20)**: PostgreSQL이 XID wraparound 보호로 쓰기를 멈췄다. 미국 업무 시간 대부분 동안 서비스가 내려갔다.
- **GitHub(2018-10-21)**: 43초 네트워크 단절에 MySQL 주 서버가 다른 리전으로 자동 승격됐다. 양쪽에 서로 없는 쓰기가 생겨 24시간 11분 동안 서비스가 저하됐다.

  - *사후 분석(postmortem)*: 장애 뒤 당사자가 타임라인·원인·재발 방지를 정리한 글이다. 이 노트의 시각과 수치는 모두 세 글에서만 가져왔다.

## 동작·원리

### 사건 1 — GitLab.com DB 삭제와 백업 전멸 (2017-01-31)

#### 타임라인 (UTC, 2017-02-10 포스트모템)

```text
  2017-01-31
  ± 17:20   엔지니어가 pgpool-II 시험을 위해 운영 DB의 LVM 스냅숏을 수동으로 떠 스테이징에 올림
            (평소에는 24시간마다 01:00 UTC에 자동)
  ± 19:00   DB 부하 증가 — 스팸으로 추정. 나중에 보니 일부는 신고로 잘못 삭제 예약된
            직원 계정과 그 데이터를 지우는 백그라운드 작업
  ± 23:00   부하로 보조 서버(db2) 복제가 뒤처짐. 필요한 WAL 세그먼트가 주 서버에서 이미 지워져 복제 실패
            WAL 아카이빙을 안 써서 수동 재동기화: 보조의 데이터 디렉터리를 지우고 pg_basebackup
            pg_basebackup이 출력 없이 멈춤 -> max_wal_senders 3 -> 32로 올림
            -> 재시작 거부(세마포어 과다) -> max_connections 8000 -> 2000으로 낮춰 재시작
            strace: pg_basebackup이 poll에서 대기
  ± 23:30   "이전 시도가 남긴 파일 때문"이라 보고 데이터 디렉터리를 지움 -- 그런데 주 서버(db1)에서
            1~2초 뒤 알아채고 멈췄으나 약 300 GB가 이미 삭제
            백업을 찾기 시작 -> 모든 백업 절차가 실패
  2017-02-01
    17:00   웹훅을 뺀 상태로 DB 복구 (스테이징 -> 운영 복사에 약 18시간)
  ± 18:00   웹훅 복원 등 마무리
```

- 포스트모템의 "5 Whys"는 두 문제로 나눈다. "GitLab.com이 약 18시간 내려갔다"와 "복구에 18시간 넘게 걸렸다"이다.
- 잃은 데이터: 프로젝트·댓글·사용자 계정·이슈·스니펫 등 DB 변경. 추정 약 5,000개 프로젝트, 5,000개 댓글, 700명 신규 사용자. Git 저장소와 위키는 따로 저장되어 영향이 없었다.
- 잃은 구간은 글 안에서 두 번 다르게 적혀 있다. 서두는 "17:20 ~ 00:00 UTC", 「Data loss impact」 절은 "17:20 ~ 23:30 UTC"다. 이 노트는 두 표현을 모두 남긴다.

#### 메커니즘 — 네 백업 절차가 각각 왜 못 썼나

```text
  절차                             목적               사고 당일 상태                                 leaf
  -------------------------------  -----------------  ---------------------------------------------  ------
  pg_dump -> S3 (24시간마다)          백업               S3 버킷이 비어 있음. 9.2 pg_dump로 9.6 서버를       20
                                                        덤프하다 오류 종료. 실패 메일은 DMARC 미서명으로 거절
  LVM 스냅숏 (24시간마다)              스테이징 복사       약 24시간 전 것 / 수동으로 뜬 약 6시간 전 것 존재    20
                                                        -> 6시간 전 것으로 복구 (유일한 선택)
  Azure 디스크 스냅숏                  디스크 장애 복구     DB 서버에는 켜져 있지 않음                        20
  PostgreSQL 복제 (hot standby)       페일오버            복제가 이미 끊겼고, 보조의 데이터는 재구축하며 지움    32 · 20
```

- 포스트모템이 나열한 절차는 **넷**이다. 커리큘럼 행의 "백업 5종"은 이 글에서 확인하지 못했다 [?]. 당일 공개 작업 문서의 표현일 수 있으나 그 문서는 이 노트의 근거로 읽지 않았다.
- `pg_dump`가 9.2였던 이유: Omnibus 패키지는 데이터 디렉터리의 `PG_VERSION`을 보고 바이너리 판을 고른다. 덤프는 데이터 디렉터리가 없는 앱 서버에서 돌았다. 그래서 기본값 9.2가 쓰였다.
  - PostgreSQL `pg_dump`는 자기보다 새 메이저 판 서버를 덤프하지 않는다(20번).
- 백업의 "실패"는 조용했다. cron 오류 알림은 메일로만 갔고, 그 메일이 거절됐다. 포스트모템의 결론: 백업 절차를 정기적으로 시험할 **책임자(ownership)**가 없었다.
- 복구 과정의 한 단계: **모든 DB 시퀀스를 100,000씩 올렸다.** 사고 전에 쓰였을 수 있는 ID를 다시 쓰지 않기 위해서다(32번 시나리오 2).
- 복구가 느린 이유: 스테이징은 Premium Storage가 아닌 Azure classic 디스크였다. 약 60 Mbps로 제한된 네트워크 디스크가 병목이었다.

```text
  복제가 끊긴 첫 고리 (19·32번)

  주 서버 db1:  WAL 000..41  000..42  000..43  ...  (부하로 WAL 생성 급증)
                 ^ 재활용·삭제됨
  보조 서버 db2: "000..41부터 주세요"  -->  이미 없음  --> 복제 실패
                 WAL 아카이브가 있었다면 그곳에서 가져올 수 있었다. GitLab은 아카이빙을 쓰지 않았다
```

  - *WAL 아카이빙*: 다 쓴 WAL 세그먼트를 `archive_command`로 별도 저장소에 복사해 두는 것이다. PITR과 뒤처진 대기 서버 복구에 쓴다(20번).
  - 이 노트의 판단: 복제 슬롯(`pg_replication_slots`)이나 `wal_keep_size` 같은 보존 설정도 같은 고리를 막는 장치다(32번). 포스트모템은 이 설정의 당시 값을 적지 않았다.

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| DB 부하 급증, 댓글 작성 실패 | [21](../21-connection-pooling/2-summary.md) · [56](../56-db-symptom-index/2-summary.md) §3 |
| 보조 서버 복제 지연 → "필요한 WAL 세그먼트가 이미 제거됨" | [32](../32-replication-leader-follower/2-summary.md) · [19](../19-wal-and-logging/2-summary.md) |
| `pg_basebackup`이 출력 없이 대기(정상 동작이었으나 문서화되지 않음) | [20](../20-backup-and-pitr/2-summary.md) |
| `max_connections` 8000 — 1년 가까이 "잘 됐던" 과대 설정이 재시작 때 드러남 | [21](../21-connection-pooling/2-summary.md) |
| 백업 저장소가 비어 있음, 알림 메일 거절 | [20](../20-backup-and-pitr/2-summary.md) · [56](../56-db-symptom-index/2-summary.md) §4 |

### 사건 2 — Sentry PostgreSQL XID wraparound (2015-07-20)

#### 타임라인 (Sentry 블로그, David Cramer, 2015-07-23)

```text
  2015-07-20(월)  PostgreSQL이 XID wraparound 보호를 시작 -> 쓰기 거부. 미국 업무 시간 대부분 서비스 중단
                  XID 문제를 확인하자마자 주 서버를 새로 들인 하드웨어(유지보수용 메모리·CPU 증설)로 페일오버
                  읽기는 복제본으로 유지(읽기 전용 운영), 쓰기 불가
                  이벤트 큐 적체·Redis 버퍼 폭증 -> 적체된 이벤트 백로그 전체를 버림(flush)
                  "재시작하면 더 길어질까" -> 진행 중인 autovacuum을 끝까지 기다리기로 결정
  약 3시간 뒤      autovacuum 종료. 그래도 쓰기 거부가 풀리지 않음
                  남은 선택은 DB를 내리고 단일 사용자 모드로 재시작하는 것뿐이라고 판단
                  내부 통계로 확인: 거대한 한 테이블만 끝나지 않음
                  (이벤트 -> 롤업 매핑, 이벤트마다 한 행. 용도는 ID 조회·중복 방지로 제한적)
                  그 테이블의 데이터를 포기하고 TRUNCATE
  5분 뒤          시스템 완전 복구
  이틀 뒤          옛 하드웨어 시험 기계의 단일 사용자 모드 VACUUM이 24시간째 진행 중
```

#### 메커니즘 — 동결이 쓰기 속도를 못 따라갔다

```text
  XID (32비트, 원형)           현재 XID
     ... ────────────────────────●──────────────────────────────▶
                                 |<── 과거로 보이는 약 20억 ──>|<── 미래 ──>
  동결 안 된 가장 오래된 행의 XID ●
        나이 = 현재 - 그 XID  ──▶ 한계에 다가가면: 경고 -> 새 XID 할당 거부 (쓰기 불가, 읽기 가능)

  예방: VACUUM이 오래된 행을 "동결"(frozen) 표시 -> 그 행은 나이 계산에서 빠짐   (16번)
  Sentry: 쓰기가 매우 많고, 행 수·크기가 거대한 테이블 -> 동결 작업이 따라잡지 못함
```

- 한계 근처의 동작은 **PostgreSQL 판마다 문구와 수치가 다르다.**
  - Sentry 글: 최대치까지 "백만 개 미만" 남으면 명령을 받지 않는다.
  - 9.4 문서: 1천만 남으면 경고, 1백만 미만이면 `database is not accepting commands to avoid wraparound data loss`로 새 트랜잭션 거부. (9.4 소스 `varsup.c`의 경고 문턱은 거부 문턱 − 1천만, 곧 1,100만 남았을 때다.)
  - 14~16 문서: 4천만 남으면 경고, 3백만 미만이면 새 XID 할당 거부. 문구는 9.4와 같다.
  - 17 문서: 문턱은 같고, 문구가 `... not accepting commands that assign new transaction IDs ...`로 바뀌었다(16번). 거부 상태에서도 VACUUM은 돌지만, 레코드를 바꾸거나 relation을 TRUNCATE하는 작업은 실패한다.
  - Sentry가 쓴 판은 글에 없다 [?].
- 단일 사용자 모드: Sentry 글은 "일반적 조언"으로 소개했다. PostgreSQL 17 문서 24.1.5는 예전 판에서는 필요했지만 지금은 대개 필요 없고 피해야 한다고 적는다. wraparound 보호를 끄는 위험이 있어서다. 이 모드가 필요한 유일한 이유로 문서가 드는 것은 불필요한 테이블을 `TRUNCATE`·`DROP`해 VACUUM을 피하려는 경우다(거부 상태의 일반 모드에서는 TRUNCATE가 실패하기 때문이다). Sentry가 실제로 택한 길(거대 테이블 TRUNCATE)과 같은 방향이다. Sentry 글은 TRUNCATE를 어느 모드에서 실행했는지 적지 않았다.
- Sentry가 밝힌 설정 문제
  - 이전: `autovacuum_freeze_max_age`가 너무 높았고, autovacuum 작업자는 기본값 3이었고, vacuum 지연(cost delay)이 너무 컸다.
  - 이후: `autovacuum_freeze_max_age = 500000000`, `autovacuum_max_workers = 6`, `autovacuum_naptime = '15s'`, `autovacuum_vacuum_cost_delay = 0`, `maintenance_work_mem = '10GB'`, `vacuum_freeze_min_age = 10000000`.
  - 글 뒤의 갱신: `maintenance_work_mem`에는 관련 경로에서 1 GB 내부 한도가 있어 100 GB를 줘도 쓰이지 않았다고 정정했다. PostgreSQL 17 릴리스 노트는 "vacuum이 더는 1GB로 조용히 제한되지 않는다"고 적는다. 그러니 이 정정은 **16 이하** 판의 이야기다.
- Sentry의 장기 방향: 관계를 여러 DB로 나누기. 궁극적으로는 SQL 기반 구조에서 벗어나겠다고 적었다.

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 쓰기만 실패, 읽기는 됨 | [16](../16-mvcc/2-summary.md) · [56](../56-db-symptom-index/2-summary.md) §1 |
| autovacuum이 끝났는데도 풀리지 않음 → 테이블별 진행 확인 필요 | [16](../16-mvcc/2-summary.md) |
| 로그에 실패 흔적 없음(autovacuum 로그 상세도를 켜지 않았음) | [16](../16-mvcc/2-summary.md) · [06](../06-pages-and-tuple-layout/2-summary.md) |
| 큐·버퍼 적체(DB 밖으로 번짐) | [30](../30-caching-with-databases/2-summary.md) |

### 사건 3 — GitHub MySQL 페일오버 불일치 (2018-10-21)

#### 타임라인 (UTC, GitHub 블로그 "October 21 post-incident analysis", 2018-10-30)

```text
  10-21 22:52  100G 광장비 교체 작업 중 미 동부 네트워크 허브 <-> 미 동부 주 데이터센터 연결 끊김
               43초 만에 복구
               그 사이 Orchestrator(Raft)가 리더 재선출. 미 서부 DC + 미 동부 퍼블릭 클라우드 노드가
               정족수를 이뤄 클러스터들의 쓰기를 서부로 페일오버
               연결 복구 뒤 앱 계층이 곧바로 서부의 새 주 서버로 쓰기를 보냄
               동부 DB에는 서부로 복제되지 않은 짧은 구간의 쓰기가 남음 -> 동부로 되돌릴 수 없음
  22:54        내부 모니터링 경보
  23:02        여러 클러스터 토폴로지가 서부 서버만 포함한 상태임을 확인
  23:07        배포 도구 잠금 / 23:09 노랑 / 23:11 코디네이터 합류 / 23:13 빨강
  23:13        원문: 조사 시점에 서부는 "거의 40분" 쓰기를 받은 상태 + 동부에만 있는 몇 초의 쓰기
               (22:52~23:13은 21분이라, 이 "40분"은 23:13 이후 조사 중의 시점으로 읽힌다)
               -> "fail-forward"만 가능하다고 판단. 대가: 동부 앱이 대륙 횡단 왕복으로 서부에 써야 함
  23:19        푸시 등 메타데이터를 쓰는 작업 중단: 웹훅 전달·Pages 빌드 일시 정지
  10-22 00:05  계획: 백업에서 복원 -> 두 사이트 복제 맞춤 -> 안정 토폴로지로 복귀 -> 대기 작업 재개
               MySQL 백업은 4시간마다, 원격 퍼블릭 클라우드 blob에 보관 -> 수 TB 복원에 수 시간
  00:41        영향받은 모든 클러스터의 백업 복원 시작
  06:51        일부 클러스터가 동부에서 복원을 마치고 서부에서 복제 시작
  07:46        블로그 공지
  11:12        모든 주 서버가 다시 동부. 그러나 읽기 복제본 수십 대가 몇 시간 뒤처짐
               -> 사용자가 요청마다 다른(오래된) 데이터를 봄
               복제 따라잡기가 선형이 아니라 "power decay"로 느려짐(유럽·미국 업무 시작 부하)
  13:15        피크 부하 접근. 동부 퍼블릭 클라우드에 읽기 복제본을 추가해 읽기 부하 분산 -> 복제가 따라잡음
  16:24        복제본 동기화 완료, 원래 토폴로지로 페일오버. 상태는 빨강 유지(백로그 처리)
  16:45        대기 중: 웹훅 이벤트 5백만 건 이상, Pages 빌드 8만 건
               내부 TTL을 넘긴 웹훅 페이로드 약 20만 건이 버려짐 -> 처리 멈추고 TTL 상향
  23:03        모든 대기 작업 처리, 녹색. 총 24시간 11분 저하
```

#### 메커니즘 — 비동기 복제 + 자동 승격 + 짧은 분할

```text
   동부(원래 주)                          서부(새 주)
   ──────────────                          ──────────────
   쓰기 w1 w2 w3 ─ 복제 ─▶ (w3는 도착 못 함)
        |<── 43초 단절 ──>|
                                          Orchestrator 정족수(서부 + 동부 클라우드)가 서부를 승격
   연결 복구                               앱이 새 쓰기 w4 w5 ... 를 서부로 (원문: 거의 40분)
   동부에만: w3 (몇 초분)                  서부에만: w4, w5, ...
                  ↓
   어느 쪽도 다른 쪽의 "앞선 복사본"이 아니다 -> 한쪽으로 그냥 되돌릴 수 없다
```

- 비동기 복제에서 커밋 응답은 "주 서버 로컬에 기록됨"만 뜻한다. 승격 직전의 지연만큼 새 주 서버에 없는 트랜잭션이 생긴다(32번 시나리오 2).
- GitHub의 경우 옛 주 서버가 **죽지 않았다.** 단절이 43초로 짧아 동부 DB가 곧 다시 보였고, 거기에는 서부로 복제되지 않은 몇 초의 쓰기가 남아 있었다. 연결 복구 뒤 새 쓰기는 서부로 갔다. 그래서 양쪽에 서로 없는 쓰기가 생겼다(글의 사실을 이 노트가 엮은 해석).
- GitHub는 동부에만 남은 쓰기를 MySQL 바이너리 로그로 뽑아 두었다. 가장 바쁜 클러스터 하나에서 영향 구간의 쓰기는 954건이었다. 글 발행 시점에 자동 조정과 사용자 연락이 필요한 것을 분류하는 중이었다.
  - 이는 32번의 대처 "옛 리더의 남은 트랜잭션은 따로 뽑아 사람이 판단한다"와 같다.
- Orchestrator는 "설정된 대로" 동작했다. 문제는 앱 계층이 **리전 간 주 서버 이동**을 감당하지 못한다는 점이 설정에 반영되지 않은 것이었다. GitHub는 리전 경계를 넘는 승격을 막도록 설정을 바꾸겠다고 적었다.
- 백업은 "매일 최소 한 번" 복원을 시험하고 있어 복구 시간은 예상 범위였다. 다만 클러스터 **전체**를 백업에서 다시 만든 것은 처음이었다. 이전에는 지연 복제본 같은 다른 전략에 기댔다.
- 분할·합의(Raft)·페일오버의 분산 관점은 distributed `36-distributed-incidents`에서 다룬다(미작성, [distributed/README](../../distributed/README.md)).

#### 밖에서 보인 신호

| 신호 | 연결 leaf |
|---|---|
| 토폴로지 조회에 서부 서버만 있음 | [32](../32-replication-leader-follower/2-summary.md) |
| 동부 앱의 쓰기가 대륙 횡단 왕복 → 사이트가 느려짐 | [55](../55-distributed-databases/2-summary.md) |
| 복원 뒤 읽기 복제본이 몇 시간 뒤처짐 → 요청마다 다른 데이터 | [32](../32-replication-leader-follower/2-summary.md) · [56](../56-db-symptom-index/2-summary.md) §3 |
| 백로그 처리 중 TTL 만료로 웹훅 약 20만 건 유실 | [56](../56-db-symptom-index/2-summary.md) §4 |

## 쓰이는 자료구조·알고리즘

- **WAL·binlog(추가 전용 로그)** — 세 사건 모두의 중심이다. GitLab은 WAL 세그먼트가 사라져 복제가 끊겼고, GitHub는 binlog로 남은 쓰기를 뽑았다([19](../19-wal-and-logging/2-summary.md), [32](../32-replication-leader-follower/2-summary.md)).
- **32비트 원형 카운터와 나이 비교** — XID는 모듈러 비교로 과거·미래를 가른다. 동결은 비교에서 빼는 표시다([16](../16-mvcc/2-summary.md)).
- **합의(Raft) 기반 리더 선출** — Orchestrator가 정족수로 새 주 서버를 정했다. 정족수가 "옳은" 결정을 해도 앱이 그 토폴로지를 감당하는지는 별개다([55](../55-distributed-databases/2-summary.md)).
- **백업 사슬과 복원 경로** — 전체 백업 + 로그 재생(PITR). GitLab에는 로그 아카이브가 없어 스냅숏 시점으로만 돌아갈 수 있었다([20](../20-backup-and-pitr/2-summary.md)).
- **5 Whys** — GitLab 포스트모템의 원인 분석 방법. 질문을 사슬로 이어 기술 원인 뒤의 조직 원인(책임자 부재)까지 간다.

```text
  세 사건을 같은 틀로: 방아쇠 -> 증폭기 -> 마지막 방어선 -> 그것도 실패한 이유

  GitLab  스팸·삭제 작업 부하 -> 복제 끊김·수동 절차 -> 백업 넷   -> 시험·알림·책임자 없음
  Sentry  쓰기 부하           -> 거대 테이블의 느린 동결 -> autovacuum -> 설정(작업자·지연·freeze age)
  GitHub  43초 단절           -> 리전 간 자동 승격     -> 백업 복원 -> 원격 전송 + 압축 해제·검증·적재 시간
```

## 적용 — 풀어나가는 법

### 1. 사후 분석을 읽는 순서

1. 타임라인에서 **방아쇠**와 **첫 신호** 사이의 간격을 찾는다. GitHub는 22:52 단절 → 22:54 경보, 그러나 23:13에야 여러 클러스터 문제로 인식했다.
2. 각 고리를 leaf 메커니즘에 붙인다(위 표).
3. "왜 마지막 방어선도 실패했나"를 찾는다. 대개 거기에 가장 큰 교훈이 있다.
4. 수치는 원문에서만 가져온다. 글 안에서 수치가 어긋나면(GitLab의 00:00 / 23:30) 둘 다 적는다.

### 2. 세 사건에서 내 시스템으로 옮길 점검 목록

- **GitLab 형 — 백업이 작동하는가**
  - 백업 성공을 exit code가 아니라 **복원된 결과**로 판정한다. 정기 자동 복원 + 데이터 대조(20번).
  - 실패 알림 경로 자체를 시험한다. 메일이 거절되면 알림은 없는 것과 같다.
  - 백업 도구 판 = 서버 판인지 본다(`pg_dump --version` vs `SELECT version()`).
  - WAL 아카이빙·보존으로 뒤처진 복제본을 재구축 없이 따라잡게 한다(19·20·32번).
  - 파괴적 명령 직전에 호스트를 확인한다. GitLab은 호스트·환경을 더 분명히 보이도록 모든 호스트의 프롬프트(PS1)를 바꾸는 작업을 개선 항목에 넣었다.
  - 복구 뒤 시퀀스를 건너뛴다(ID 재사용 방지).
- **Sentry 형 — 동결이 따라가는가**
  - `age(datfrozenxid)`·테이블별 `age(relfrozenxid)`에 경보를 건다(16번).
  - autovacuum 로그를 남긴다(`log_autovacuum_min_duration`). Sentry는 상세도를 켜지 않아 실패 여부를 몰랐다.
  - 쓰기가 몰리는 거대 테이블은 파티션으로 나눠 동결 단위를 작게 한다(33번).
  - "이 테이블을 버려도 되나"를 평소에 분류해 둔다. Sentry의 복구는 그 판단 하나로 5분 만에 끝났다.
- **GitHub 형 — 자동 페일오버가 앱과 맞는가**
  - 승격 범위(리전 내부만)를 앱의 지연 한계에 맞춘다.
  - 비동기 복제에서 승격 뒤 옛 주 서버의 남은 트랜잭션을 뽑는 절차(binlog·GTID 비교)를 준비한다(32번).
  - 복원 시간을 백업 **위치**까지 포함해 잰다. GitHub 글은 원격 백업 서비스에서 받는 데 상당한 시간이 들었고, 큰 백업 파일을 압축 해제·체크섬·준비·적재하는 데 대부분의 시간이 들었다고 적었다.
  - 복구 뒤 읽기 복제본 지연이 사용자에게 보이지 않게, 지연 임계치를 넘은 복제본을 읽기 풀에서 뺀다(32번).
  - 백로그 재처리 때 TTL·다운스트림 과부하를 미리 계산한다.

### 3. 확인 명령

```sql
-- GitLab 형: 아카이브와 복제 보존
SELECT archived_count, failed_count, last_failed_wal, last_failed_time FROM pg_stat_archiver;
SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) FROM pg_replication_slots;
SHOW wal_keep_size;

-- Sentry 형: XID 나이
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
SELECT c.oid::regclass AS table_name,                       -- 문서 24.1.5의 쿼리: TOAST 나이까지 본다
       greatest(age(c.relfrozenxid), age(t.relfrozenxid)) AS age
FROM pg_class c LEFT JOIN pg_class t ON c.reltoastrelid = t.oid
WHERE c.relkind IN ('r', 'm') ORDER BY 2 DESC LIMIT 10;

-- GitHub 형 (MySQL): 복제 지연과 GTID 차이
SHOW REPLICA STATUS\G          -- Seconds_Behind_Source, Retrieved/Executed_Gtid_Set
SELECT @@gtid_executed;        -- 옛 주 서버와 새 주 서버에서 비교
```

- PostgreSQL 쿼리의 열 이름은 이 노트 작성 환경(PostgreSQL 17.11)에서 확인했다. `wal_keep_size`는 13부터의 이름이다. 12 이하는 `wal_keep_segments`였다(PostgreSQL 13.0 릴리스 노트: `wal_keep_size = wal_keep_segments * wal_segment_size`).

## 장애 시나리오와 대처

### 1. "백업이 있다"를 "복원할 수 있다"로 읽는다 — GitLab 형

- **현상**: 사고가 나서 백업을 찾았는데 비어 있거나, 판이 달라 쓸 수 없다.
- **보이는 형태**: 백업 저장소가 비어 있음. cron은 오류로 끝났지만 알림이 닿지 않음. 남은 것은 백업 목적이 아닌 스냅숏뿐.
- **원인**: 백업 "작업"을 돌리는 것과 "결과"를 확인하는 것이 분리돼 있었다. 도구 판이 서버와 달랐다. 시험할 책임자가 없었다.
- **대처**: 자동 복원 + 대조를 파이프라인으로. 마지막 **복원** 성공 시각을 지표로 경보. 백업 수단마다 따로 복원해 본다(20번).

### 2. 복제본을 백업으로 여긴다 — GitLab 형

- **현상**: 주 서버의 데이터를 잃었는데 복제본도 쓸 수 없다.
- **보이는 형태**: GitLab은 복제를 다시 맞추려고 보조 서버의 데이터를 먼저 지운 상태였다.
- **원인**: 복제는 페일오버용이다. GitLab 포스트모템도 복제를 "주로 페일오버용이지 재해 복구용이 아니다"라고 적었다. 실수(`DELETE`, 디렉터리 삭제)는 복제되거나, 재구축 과정에서 복제본도 비게 된다.
- **대처**: 복제와 별도로 PITR 가능한 백업을 둔다(20번 시나리오 5).

### 3. wraparound 경고를 "나중에"로 미룬다 — Sentry 형

- **현상**: 어느 날 모든 쓰기가 거부된다. 읽기는 된다.
- **보이는 형태**: 먼저 `WARNING: database "…" must be vacuumed within N transactions`, 이어서 새 XID를 받지 않는다는 `ERROR`(문구는 판마다 다르다, 16번).
- **원인**: 쓰기가 많은 거대 테이블의 동결이 따라가지 못했다. autovacuum 작업자 수·지연 설정이 부하에 비해 보수적이었다.
- **대처**: `age(datfrozenxid)`에 경보. autovacuum 작업자·비용 지연 조정. 거대 테이블은 파티션. 한계에 닿으면 PostgreSQL 17 문서 24.1.5 순서(오래된 prepared transaction·긴 트랜잭션·슬롯 정리 → VACUUM)를 따른다. 버릴 수 있는 테이블이면 TRUNCATE가 가장 빠를 수 있다(Sentry). 단, 거부 상태에서는 일반 모드의 TRUNCATE가 실패하므로 문서는 이 경우에만 단일 사용자 모드를 인정한다.

### 4. 짧은 네트워크 단절에 자동 승격 → 양쪽에 쓰기 — GitHub 형

- **현상**: 단절은 1분도 안 됐는데 복구에 하루가 걸린다.
- **보이는 형태**: 토폴로지가 다른 리전의 서버만 포함. 양쪽 주 서버에 서로 없는 트랜잭션. 앱은 대륙 횡단 지연으로 느려짐.
- **원인**: 비동기 복제 + 리전을 넘는 자동 승격 + 옛 주 서버가 살아 있음. 승격 도구의 설정이 앱의 한계를 반영하지 않았다.
- **대처**: 승격 범위 제한, 옛 주 서버 펜싱, 승격 후 남은 트랜잭션 추출 절차. 잃으면 안 되는 쓰기는 준동기·동기 복제(32번).

### 5. 복구 예상 시간을 선형으로 잡는다 — GitHub 형

- **현상**: "2시간 뒤 복구"라고 공지했는데 훨씬 오래 걸린다.
- **보이는 형태**: 복제 지연이 줄다가 업무 시간 부하가 오르자 다시 늘어난다.
- **원인**: 복제 따라잡기 속도는 적용 속도 − 새 쓰기 속도다. 새 쓰기가 늘면 따라잡는 속도가 급감한다. GitHub는 이것이 선형이 아니라 "power decay"를 따랐다고 적었다.
- **대처**: 읽기 복제본을 늘려 복제본 한 대당 부하를 낮췄다(GitHub). 예상 시간은 부하 변화를 넣어 보수적으로 공지한다.

## 핵심 문장

- 실사건은 메커니즘 여러 개가 한 줄로 이어진 것이다. 고리마다 "지금까지 괜찮았다"는 가정이 있다(GitLab의 `max_connections` 8000은 1년 가까이 문제없었다).
- GitLab: 백업 절차 넷 중 셋을 쓸 수 없었고, 남은 것은 백업용이 아닌 스테이징 복사용 LVM 스냅숏이었다. 백업은 **복원해 본 결과**로만 믿는다. 알림 경로와 도구 판, 책임자까지 시험 대상이다.
- 복제는 백업이 아니다. 실수도 복제되고, 재구축 과정에서 복제본도 빈다.
- Sentry: XID wraparound는 쓰기만 막는다. `age(datfrozenxid)` 경보와 거대 테이블의 동결 속도가 방어선이며, 한계 수치와 문구는 PostgreSQL 판마다 다르다.
- GitHub: 43초 단절 + 비동기 복제 + 리전 간 자동 승격이 양쪽에 서로 없는 쓰기를 만들었다. 승격 도구의 설정은 앱이 감당할 수 있는 토폴로지와 맞아야 한다.
- 복구 시간은 백업 위치(원격 전송)·복원 준비(압축 해제·검증·적재)와 복구 중 부하(복제 따라잡기)가 정한다. 모두 평소에 재 둔다.

## 관련 주제·근거

- 선행: [56-db-symptom-index](../56-db-symptom-index/2-summary.md) — 세 사건의 신호가 색인의 어디에 있나
- 메커니즘 leaf
  - [20-backup-and-pitr](../20-backup-and-pitr/2-summary.md) — 백업·PITR·복원 시험 (GitLab)
  - [19-wal-and-logging](../19-wal-and-logging/2-summary.md) · [32-replication-leader-follower](../32-replication-leader-follower/2-summary.md) — WAL 보존, 복제, 비동기 페일오버 (GitLab·GitHub)
  - [16-mvcc](../16-mvcc/2-summary.md) · [06-pages-and-tuple-layout](../06-pages-and-tuple-layout/2-summary.md) — XID·동결 (Sentry)
  - [42-recovery-aries-checkpoints](../42-recovery-aries-checkpoints/2-summary.md) — 복구가 로그를 어떻게 쓰나
  - [21-connection-pooling](../21-connection-pooling/2-summary.md) — `max_connections` 과대 (GitLab)
  - [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md) · [55-distributed-databases](../55-distributed-databases/2-summary.md) — 거대 테이블 나누기, 합의·리전 간 지연
- 다른 영역
  - distributed `36-distributed-incidents`(GitHub 2018의 분할·합의 관점) — 미작성, [distributed/README](../../distributed/README.md)
  - [os/38-os-incidents](../../os/38-os-incidents/2-summary.md) — PostgreSQL fsyncgate 등 OS 쪽 실사건
- 1차 출처
  - GitLab, "Postmortem of database outage of January 31", 2017-02-10 <https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/>
  - David Cramer(Sentry), "Transaction ID Wraparound in Postgres", 2015-07-23 <https://blog.sentry.io/transaction-id-wraparound-in-postgres/>
  - Jason Warner(GitHub), "October 21 post-incident analysis", 2018-10-30 <https://github.blog/2018-10-30-oct21-post-incident-analysis/>
- PostgreSQL 문서 "Routine Vacuuming" — 9.4판(1천만 경고·1백만 거부), 13판(1,100만·1백만), 14~17판(4천만·3백만, 단일 사용자 모드는 대개 불필요). 거부 문구 변경은 17판(REL_16_STABLE·REL_17_STABLE `src/backend/access/transam/varsup.c` 대조) <https://www.postgresql.org/docs/17/routine-vacuuming.html> · <https://www.postgresql.org/docs/9.4/routine-vacuuming.html>
- PostgreSQL 17.0 릴리스 노트 — "vacuum is no longer silently limited to one gigabyte of memory" <https://www.postgresql.org/docs/release/17.0/> · 13.0 릴리스 노트 — `wal_keep_segments` → `wal_keep_size` <https://www.postgresql.org/docs/release/13.0/>
- 로컬 재현(2026-10-01, PostgreSQL 17.11 컨테이너, 전용 DB `w56` — 끝나고 삭제): §적용 3의 PostgreSQL 진단 쿼리 문법·열 이름 확인(테이블별 XID 나이 쿼리는 판정 때 문서 24.1.5 형태로 바꿔 전용 DB `fa54`에서 다시 실행, 끝나고 삭제). 사건 자체는 재현하지 않았다.
