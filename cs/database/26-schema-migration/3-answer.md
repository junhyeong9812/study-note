# database/26-schema-migration — 정답

## 정답

### 1. 한 번의 ALTER가 위험한 세 이유

| 층 | 문제 |
|---|---|
| DB 안 | DDL은 강한 테이블 락(PG ACCESS EXCLUSIVE, MySQL 배타 MDL)을 잡는다. 재작성형이면 그 락을 행 수만큼 오래 쥔다 |
| 앱 쪽 | 롤링·카나리 배포 중에는 구버전·신버전 코드가 같은 테이블을 본다. 구버전이 모르는 스키마면 에러 |
| 데이터 | 코드는 이미지로 되돌리지만, DROP한 컬럼·덮어쓴 값은 돌아오지 않는다 |

- 그래서 짧게 잠그는 단계들로 쪼개고(expand/contract), 각 단계가 모든 살아 있는 코드 버전과 호환되게 한다.

### 2. ALTER 뒤에 줄 서는 SELECT

```text
  A: ACCESS SHARE 보유(커밋 안 함)
  B: ACCESS EXCLUSIVE 요청 → A와 충돌 → 대기
  C: ACCESS SHARE 요청 → A와는 충돌 안 하지만, 앞에서 기다리는 B의 요청과 충돌 → B 뒤에서 대기
```

- B와 C 모두 A가 끝날 때까지 멈춘다. A가 커밋하면 B가 수 ms에 끝나고, 그다음 C가 실행된다.
- `ALTER`의 실행 시간이 아니라 **락 획득 대기**가 문제다. 로컬 재현(PostgreSQL 17.11)에서 `pg_locks`는 B의 AccessExclusiveLock `granted = f`, C의 AccessShareLock `granted = f`를 보였다. `pg_blocking_pids(C)`는 B를 가리켰다.
- 방어: `SET lock_timeout = '1s'` 후 `ALTER` → 못 잡으면 `55P03`으로 포기하고 재시도. 적용 전에 장기 트랜잭션을 확인한다.

### 3. 재작성 여부

| | 재작성 | 근거 |
|---|---|---|
| (a) `NOT NULL DEFAULT 0` | 없음 | 비휘발 기본값은 메타데이터에 저장(문서 Notes). PostgreSQL 11부터 |
| (b) `DEFAULT clock_timestamp()` | 있음 | 휘발 기본값은 행마다 값이 달라 전체 재작성 |
| (c) int → bigint | 있음 | 저장 형식이 바뀜 |
| (d) varchar(50) → varchar(100) | 없음 | 이진 호환, 길이 제한만 완화 |

- 확인: 변경 전후 `SELECT pg_relation_filenode('t')`를 비교한다. 값이 바뀌면 새 파일로 재작성된 것이다. 로컬 재현(20만 행)에서 (a)·(d)는 그대로, (b)·(c)는 바뀌었다.
- 재작성이 없어도 1번의 락 대기는 똑같이 생긴다.

### 4. NOT NULL을 긴 락 없이

```sql
ALTER TABLE users ADD CONSTRAINT email_nn CHECK (email IS NOT NULL) NOT VALID;  -- 짧은 락, 스캔 없음
-- 이 시점부터 새 INSERT/UPDATE의 NULL은 거절된다
UPDATE users SET email = ... WHERE email IS NULL;       -- 기존 NULL 정리(청크로)
ALTER TABLE users VALIDATE CONSTRAINT email_nn;         -- SHARE UPDATE EXCLUSIVE, 읽기·쓰기와 공존하며 스캔
ALTER TABLE users ALTER COLUMN email SET NOT NULL;      -- 유효한 CHECK가 증명하므로 스캔 생략
ALTER TABLE users DROP CONSTRAINT email_nn;             -- (선택) 중복 제약 제거
```

- 로컬 재현(PostgreSQL 17.11): 위반 행이 남은 채 `VALIDATE`하면 `check constraint "name_nn" ... is violated by some row`로 실패했다. 정리 후 성공했고, `SET NOT NULL`은 2.7 ms였다.
- `SET NOT NULL`과 `DROP CONSTRAINT`는 여전히 ACCESS EXCLUSIVE다. 짧지만 락 대기가 있으므로 `lock_timeout`을 함께 쓴다.

### 5. expand/contract와 코드 버전

```text
  ① expand   full_name 추가(nullable)          살아 있는 코드: v1
  ② 양쪽 쓰기  v2 배포(name·full_name 둘 다 씀)    v1, v2
  ③ 백필     기존 행의 full_name 채움            v2  ← v1이 모두 내려간 뒤(아니면 v1이 쓴 행이 다시 낡음)
  ④ 읽기 전환  v3 배포(full_name 읽기, 양쪽 쓰기 유지)  v2, v3
  ⑤ contract name 삭제                          v4(full_name만)  ← v1~v3이 모두 내려간 뒤
```

- 규칙: **어느 시점이든 살아 있는 모든 코드 버전이 현재 스키마에서 동작해야 한다.**
- ①~④는 코드를 이전 버전으로 돌리면 된다. ⑤ 이후로는 name 데이터가 없으므로 롤백이 불가능하다. 그래서 ⑤는 맨 끝, 별도 배포, 충분한 관찰 뒤에 한다.

### 6. DDL과 ROLLBACK

| | 결과(로컬 재현) | 이유 |
|---|---|---|
| PostgreSQL 17.11 | 행도 컬럼도 없다 | DDL이 트랜잭션에 참여한다 |
| MySQL 8.4.10 | 행도 컬럼도 남는다 | `ALTER`가 앞 트랜잭션을 암묵 커밋한다. "Atomic DDL is not transactional DDL"(문서 15.1.1) |

- 함의: MySQL에서는 다문장 마이그레이션이 중간에 실패하면 **거기까지 적용된 상태**로 남는다. 한 파일에 한 변경씩 두고, 재실행 가능하게(`IF NOT EXISTS` 류) 쓴다.
- PostgreSQL도 `CREATE INDEX CONCURRENTLY`처럼 트랜잭션 블록 안에서 못 도는 문장이 있다. 도구가 파일 전체를 트랜잭션으로 감싸면 실패한다.

### 7. INSTANT인데 MDL 대기

- 원인: 어떤 트랜잭션이 테이블을 건드린 채 끝나지 않아 공유 MDL을 쥐었다. `ALTER`는 정의를 바꾸려고 배타 MDL을 기다렸다. 이 대기 중인 배타 요청이 뒤이은 모든 조회를 막았다(문서 17.12.2 "a pending exclusive metadata lock ... blocks subsequent transactions").
- INSTANT는 **데이터 재작성**을 없앨 뿐이다. 정의 교체를 위한 배타 MDL은 여전히 필요하다.
- 즉시 조치: `ALTER` 세션을 `KILL QUERY`로 끊으면 줄이 풀린다. 막고 있던 장기 트랜잭션을 `information_schema.innodb_trx`와 `performance_schema.metadata_locks`로 찾는다.
- 재발 방지: `SET SESSION lock_wait_timeout = 2` 같은 짧은 상한 + 재시도, 적용 전 장기 트랜잭션 확인, 앱의 트랜잭션 방치 제거.

### 8. 백필과 복제 지연

- 지표: MySQL `SHOW REPLICA STATUS`의 `Seconds_Behind_Source`, PostgreSQL `pg_stat_replication.replay_lag`. 원본의 binlog·WAL 생성량.
- 원인: 한 번에 너무 많이 썼다. MySQL은 트랜잭션 변경을 커밋 때 한 번에 binlog에 쓰므로(문서 7.4.4), 거대 트랜잭션 하나가 복제본에서도 한 덩어리로 재생된다. 복제본에서 읽는 화면은 그동안 옛 데이터를 본다.
- 바꾸는 법:

```sql
-- keyset 청크: 청크마다 커밋
UPDATE users SET full_name = name
WHERE id > :last_id AND id <= :last_id + 5000 AND full_name IS NULL;
-- 커밋 → 복제 지연 확인 → 임계 초과면 sleep → :last_id 기록(중단 시 재시작 지점)
```

### 9. CIC 실패 뒤의 INVALID 인덱스

- 남는 것: 카탈로그에 INVALID 표시된 인덱스(`\d`에 `INVALID`, `pg_index.indisvalid = false`). 로컬 재현(PostgreSQL 17.11)에서 중복 값 때문에 실패한 `t_name_uq`가 그대로 남았다.
- 문제: 쿼리 계획에는 안 쓰이지만 쓰기마다 갱신 비용이 든다. 유니크 인덱스가 두 번째 스캔에서 실패했다면 **유니크 제약도 계속 강제**한다(문서).
- 정리: `DROP INDEX CONCURRENTLY t_name_uq;` → 원인(중복 값) 제거 → 다시 `CREATE UNIQUE INDEX CONCURRENTLY`. 또는 `REINDEX INDEX CONCURRENTLY`.

### 10. 같은 1205, 다른 락

| 변수 | 무엇을 기다리나 | 8.4 기본값 |
|---|---|---|
| `lock_wait_timeout` | 메타데이터 락(서버 계층, DDL·테이블 정의) | 31536000초(1년) |
| `innodb_lock_wait_timeout` | InnoDB 행 락 | 50초 |

- 둘 다 초과하면 `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`으로 보인다(로컬 재현에서 MDL 대기 초과도 1205). 에러 번호만으로 원인을 구분할 수 없다. `SHOW PROCESSLIST`의 State(`Waiting for table metadata lock`)와 `performance_schema.metadata_locks`·`data_locks`로 가른다.
- 기본값은 로컬 MySQL 8.4.10에서 `SELECT @@lock_wait_timeout, @@innodb_lock_wait_timeout`으로 확인했다.
