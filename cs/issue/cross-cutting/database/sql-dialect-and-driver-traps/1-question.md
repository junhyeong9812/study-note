# cs/issue/database/sql-dialect-and-driver-traps — 실제 엔진에서만 드러나는 것: SQL 방언·드라이버·엔진 설정 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-24).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. `UNIQUE (parent_id, name)` 제약을 걸었는데 `parent_id` 가 NULL 인 루트 행은 같은 이름으로 여러 개 들어간다(이 사례: MySQL). SQL 에서 NULL 끼리의 비교는 어떤 결과이며, 그래서 이 엔진의 UNIQUE 가 무엇을 못 막는가. 모든 엔진이 똑같이 동작하는가, 대안은?
2. 단위 테스트(대체 DB·ORM 매핑)는 모두 통과했는데 실제 MySQL 에 마이그레이션을 적용하자 문법 오류·잘림이 났다. `DROP COLUMN IF EXISTS`, `INSERT…SELECT…JOIN…ON … ON DUPLICATE KEY UPDATE`, 예약어 컬럼명은 각각 왜 실제 엔진에서만 드러나는가.
3. 예측: 운영 DB 에선 잘 돌던 2.8MB 짜리 시드 INSERT 가 테스트 컨테이너에서만 실패했다. 무엇이 다른가. 같은 계열로, "초기화 후 변경 불가"한 서버 설정(테이블명 대소문자)과 FK 양쪽의 charset/collation 불일치는 어떤 증상으로 나타나나.
4. 같은 식별자를 담는 컬럼이 한 테이블은 `VARCHAR(100)`, 참조 테이블은 `VARCHAR(20)` 이다. 평소 채번 규칙(20자)으로는 문제가 없다가 어떤 순간 터지는가. "가장 좁은 곳이 잠복 상한"이라는 말의 의미는?
5. 대형 테이블에 `ALGORITHM=INPLACE, LOCK=NONE` 온라인 인덱스를 걸었는데 `Waiting for table metadata lock` 에서 멈췄다. "온라인"인데 왜 막히며, 그 뒤에 들어온 요청들은 어떻게 되는가. SQLite 가 WAL 모드에서도 `database is locked` 를 내는 이유는?
6. 경계: 다음 세 가지는 "SQL 이 쓴 대로 동작하지 않는" 엔진 의미다 — 지연 모드(`INITIALLY DEFERRED` 또는 `SET CONSTRAINTS … DEFERRED`)로 둔 제약 위반이 언제 터지는가 / 마이그레이션 `UPDATE` 가 `updated_at` 트리거를 발화시키는가 / REPLACE 계열 upsert 가 FK `ON DELETE CASCADE` 자식에게 무엇을 하는가. `SET FOREIGN_KEY_CHECKS=0` 은 트랜잭션 롤백으로 원복되는가?
7. 연결: 프로시저 OUT 값을 세션 변수(`@ok`)로 받아 `CALL` 다음 `SELECT @ok` 로 읽는다. 커넥션 풀을 쓰면 왜 값이 조용히 어긋날 수 있나. "세션 상태는 무엇에 귀속되는가"를 기준으로 답하라.

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
