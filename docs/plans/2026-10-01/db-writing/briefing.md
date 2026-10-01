# 집필 브리핑 — 커리큘럼 leaf 새 노트 (데이터베이스, 2026-10-01)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」.
> 형식 참고(내용 복사 금지): `cs/os/19-deadlock/`, `cs/network/15-tcp-handshake-and-backlog/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §5 운영체제 표에서 담당 slug를 찾는다.
  - 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다.
- **영역 표**: `cs/database/README.md` — 번호·선행·다른 영역 노트 링크 대상.
- **근거**
  - PostgreSQL 17 문서(postgresql.org/docs/17), MySQL 8.4 Reference Manual(dev.mysql.com/doc/refman/8.4), 소스(postgres/postgres, mysql/mysql-server — GitHub raw), CMU 15-445 Fall 2024 강의, DDIA 1판, 논문(Berenson 1995, ARIES 1992 등), JDBC·Hibernate·HikariCP 등 공식 문서.
  - WebSearch·WebFetch·curl이나 로컬 재현(§5)으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/database/<NN-slug>/`의 3파일

헤더와 틀은 네트워크와 같다. 차이는 영역 이름 `database/`뿐이다.

### 2-summary.md

```
# database/<NN-slug> — <한 줄 제목> — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> ⚠️ 이 서머리는 Claude 초안(2026-10-01) — 근거는 아래 「관련 주제·근거」. 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

절마다 쓸 내용:

- **해결하는 문제**: 이것이 없으면 무엇이 안 되는지 쓴다. 쉬운 예 → "똑같은 구조다" → 실무 예 순서로.
- **동작·원리**: 본문의 중심이다.
  - ASCII 그림을 먼저 두고, 글은 그 해설로 쓴다.
  - 그림 예: 페이지·튜플 배치도, B+트리, 트랜잭션 시간축(세션 A/B 교차), 실행 계획 트리.
- **쓰이는 자료구조·알고리즘**: 예) B+트리, 해시 인덱스, LSM·블룸 필터, 버퍼 풀 LRU/clock, 조인 알고리즘(NL·hash·merge), 락 테이블·wait-for 그래프, 버전 체인. 가능하면 cs 노트로 링크한다.
- **적용 — 풀어나가는 법**: 실무 순서로 쓴다.
  - SQL과 진단을 넣는다: `EXPLAIN (ANALYZE, BUFFERS)`, `EXPLAIN FORMAT=TREE/ANALYZE`, `pg_stat_activity`·`pg_locks`·`pg_stat_statements`, `SHOW ENGINE INNODB STATUS`, `performance_schema.data_locks`, 슬로 쿼리 로그 등.
- **장애 시나리오와 대처**: 3~5개. 각각 **현상 → 보이는 형태(에러·exit code·로그·지표) → 원인 → 대처**로 쓰고, ⚠ 칸을 포함한다.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**
  - 선행·후속 노트를 링크한다.
    - 새 노트: `../NN-slug/2-summary.md`
    - 아직 없는 DB 주제: 영역 표 `../README.md` 링크와 함께 "미작성"이라고 적는다.
    - 다른 영역 노트: 실제 경로를 확인하고 링크한다.
  - man 섹션, 문서 URL, 소스 경로, 교재 장을 적는다.

### 1-question.md / 3-answer.md

네트워크와 같은 틀이다(`cs/network/15-*/1-question.md`, `3-answer.md` 참고).

- 질문은 6~10개로, 유형은 왜 / 예측 / 경계 / 연결 / 장애 진단이다.
- 정답은 질문과 번호·개수가 같아야 한다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순 ASCII를 쓴다. 복잡한 그림 하나보다 단순한 그림 여러 개가 낫다.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식은 `  - *용어*: 설명`이다.
3. 한 문장에 한 개념만 담는다. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드 스니펫**: DB 동작은 SQL로 보여 준다(PostgreSQL·MySQL 문법 차이는 표시). 앱 쪽은 Java(JDBC·JPA/Hibernate·Spring `@Transactional`)·TS(Node 드라이버)로 쓴다.
5. **사실 규칙**
   - 수치·기본값·버전은 출처를 확인했을 때만 쓴다.
   - 확인하지 못하면 `[?]`를 붙인다.
   - **지어내지 않는다.** 예시 수치에는 "(예시)"를 붙인다.

## 3-1. 네트워크에서 나온 주의 (시범 + 2차 리뷰 약 130건의 유형)

- **`[?]` 기준**: 1차 출처로 **확인하지 못한 것에만** 붙인다. 확인했으면 근거(절·URL·소스 경로)를 쓴다.
- **규범 수준을 정확히**: SQL 표준·공식 문서의 "must/should/may", "implementation-defined"를 바꾸지 않는다.
- **"항상·모든·반드시·절대" 금지**: 예외가 있으면 조건을 붙인다. 네트워크에서 가장 많이 나온 지적이다.
  - 예) "close()는 FIN" → 읽지 않은 데이터가 있으면 RST
  - 예) "스위치는 프레임을 안 바꾼다" → VLAN 태그를 붙이고 뗄 때는 바뀐다
- **노트 안 모순 금지**: 그림과 식, 요약과 정답, 정답 N과 정답 M이 같은 말을 해야 한다.
  - 네트워크 예: CUBIC 그림이 식과 반대 방향이었다. NAT 그림이 본문의 MUST를 어겼다.
  - 다 쓰고 나서 스스로 대조한다.
- **기본값·동작은 버전 조건과 함께**: 설정 기본값(예: `innodb_lock_wait_timeout`, `default_transaction_isolation`)은 해당 버전 문서로 확인하고 "PostgreSQL 17 / MySQL 8.4 기준"을 적는다. 이전 버전과 다른 점은 따로 적는다.
- **방향·경우를 섞지 않는다**: RX에 대한 설명을 TX에, 한 모드(예: 레벨 트리거)에 대한 설명을 다른 모드에 그대로 쓰지 않는다.
- **제품·버전을 섞지 않는다 (DB 특칙)**: PostgreSQL과 MySQL InnoDB는 격리 수준 이름이 같아도 동작이 다르다(예: REPEATABLE READ의 팬텀·갭 락). 한 제품의 동작은 "PostgreSQL 17에서는", "MySQL 8.4 InnoDB에서는"처럼 한정하고, SQL 표준 정의와 구현 동작을 구분한다.
- **계층을 섞지 않는다**: DB 엔진 동작과 드라이버·ORM·커넥션 풀 동작을 구분한다(예: 타임아웃이 어느 층의 것인가).
- **에러가 드러나는 방식은 구현 의존이다**: SQLSTATE·에러 번호(예: PG 40001·40P01, MySQL 1213·1205) → JDBC·Spring 예외 매핑은 문서·소스로 확인하고 한정한다.
- **진단 명령의 옵션은 실제 문서와 대조한다**. 로컬 `man`과 `--help`로 확인한다.

## 4. 원고·기존 초안 이어받기 (23·26·30·32·33·38·43·44·45 담당자)

- 원고와 기존 초안은 **수정하지 않는다**. 각 담당 주제의 원본:
  - 32 → `cs/systems/server-design/03-data-layer.md`
  - 23 → `cs/engineering/data-access`
  - 26 → `cs/systems/server-design/08-deployment-ops.md`
  - 30 → `cs/systems/server-design/04-caching.md`
  - 43 → `cs/systems/postgres-rls`
  - 45 → `cs/systems/clickhouse-mergetree`
  - 38 → `cs/systems/lsm-tree`(초안)
  - 33 → `cs/systems/partitioning-vs-sharding`(초안)
  - 44 → `cs/systems/timeseries-resolution-tiers`(초안)
- 해당 부분을 먼저 **읽는다**. 새 leaf는 원본이 이미 설명한 것을 길게 되풀이하지 않는다. "기초는 원본 §N"으로 링크하고 한두 줄로 요약한다.
- 빈 곳을 채운다: 엔진 내부 동작, 커리큘럼 ⚠ 장애, 자료구조, 적용(SQL·진단), 질문·정답.
- 원본에 틀린 내용이 있으면 새 leaf에 올바른 설명을 쓰고, `> 참고: 원본 §N의 "…"는 …(근거)` 한 줄로 짚는다.

## 5. 로컬 재현 (허용 — 안전 규칙)

- **컨테이너**: 메인이 미리 띄웠다. 워커는 새 컨테이너를 만들지 않는다.
  - `sn-dbw-pg`: PostgreSQL 17.11, 사용자 postgres
  - `sn-dbw-my`: MySQL 8.4.10, root / 비밀번호 `sndbw`
- **접속**: 반드시 `docker exec`로 한다.
  - PG: `docker exec sn-dbw-pg psql -U postgres -d <db> -c "..."`
  - MySQL: `docker exec sn-dbw-my mysql -uroot -psndbw <db> -e "..."`
- **전용 DB만 쓴다**: 이름은 `w<담당 첫 번호>`(예: `w08`). 시작할 때 만들고 끝나면 `DROP DATABASE`한다. 다른 워커의 DB, 기본 DB의 전역 설정(`ALTER SYSTEM`, `SET GLOBAL`)은 건드리지 않는다. 세션 단위 `SET`은 된다.
- **psql 주의**: `-c "여러 문장"` 하나는 한 트랜잭션으로 묶인다. `CREATE DATABASE`나 `VACUUM`처럼 트랜잭션 밖에서 돌아야 하는 문장은 `-c`를 따로 쓴다.
- **동시 세션 재현**(격리 수준·락·데드락): 백그라운드 세션 2~3개로 짧게(몇 초) 한다. 끝나면 남은 세션이 없는지 확인한다.
  - PG: `pg_stat_activity`
  - MySQL: `SHOW PROCESSLIST`
- **부하 상한**: 수십만 행, 쿼리 수 초 이내, 동시 세션 몇 개. 대량 적재·장시간 벤치·디스크를 채우는 실험은 하지 않는다.
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/db/<담당번호>/`에만 둔다(절대 경로). **저장소 루트나 노트 폴더에 파일을 만들지 않는다.** 명령에 `cd`를 쓰면 절대 경로로 쓴다(OS 작업에서 루트 유출이 두 번 있었다).
- **기존 컨테이너 금지**: `payment-codex-*` 등 이 작업이 만들지 않은 컨테이너·볼륨은 조회도 하지 않는다.
- **노트에 넣는 출력**: `(예시, PostgreSQL 17.11)` 또는 `(예시, MySQL 8.4.10)`을 붙이고, 근거 목록에 "로컬 재현"이라고 적는다.

## 6. 하지 말 것

- 담당 폴더 밖 파일(원고·다른 영역·커리큘럼·README 등)을 수정하지 않는다.
- git 명령은 조회만 한다.
- 리프 폴더와 저장소 루트에 md가 아닌 파일을 두지 않는다. SQL 스크립트·로그는 scratchpad에 둔다.
- 하위 에이전트나 fork를 띄우지 않는다.

## 7. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>`을 실행해 전부 PASS여야 한다.
- 제출 전 §3-1의 "노트 안 모순"을 스스로 대조한다. 대상은 그림과 식, 요약과 정답의 수치·결론이다.

## 8. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(man 섹션, 문서 URL, 소스 경로, 교재 장)
- 로컬 재현 목록(무엇을 돌려 무엇을 확인했나) + 전용 DB를 DROP했는지
- `[?]` 목록
- 커리큘럼 ⚠ 칸 커버 여부
- 미완료 항목
