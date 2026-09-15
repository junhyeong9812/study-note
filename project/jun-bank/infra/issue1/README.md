# issue1 — 레이아웃과 배포 스키마 DDL: 기록의 계약부터

- 원본 PR: infra #2 · devlog: `jun-bank/infra/docs/devlog/pr-02-layout-schema.md`

## 1. 무엇이 문제였나

infra의 첫 코드는 Go 파일이 아니라 DDL이었다.\
이 PR 직전까지 배포 오케스트레이션의 결정은 전부 문서 안에만 있었고, 실행되는 것은 하나도 없었다.\
그 상태에서 가장 먼저 세운 것은 "배포 기록을 어디에 어떤 계약으로 남기나"였다.

이 스키마가 생긴 경위 자체가 하나의 사건이다.\
원래 운영 규칙은 "agent에게 DB 계정을 주지 않는다"였고, 근거는 권한 매트릭스에 배포 주체 계정이 **없다**는 것이었다.\
재검에서 이게 오독으로 판정됐다 — "표가 그 계정을 갖고 있지 않다"는 사실이지 "가지면 안 된다"는 판정이 아닌데, 사실이 판정처럼 쓰이고 있었다.

그 오독이 만든 실제 문제가 둘이었다.

- **제공자 순환** — 락 조작의 제공자가 코어라, 코어가 응답하지 않으면 락을 잡을 수 없고 배포도 롤백도 불가능하다.\
  그런데 롤백이 필요한 순간이 바로 코어가 죽은 그 순간이다.
- **대조 불가** — 락은 코어 스키마의 DB 행이고 배포 이력은 agent 로컬 파일이라, "락을 잡은 시각과 배포 이력이 맞나"를 한 곳에서 판정할 수 없었다.

## 2. 무엇을 고민했나

권한을 어디에 어떻게 둘지 세 방향이 있었다.

- **agent에 DB 계정을 아예 안 준다** — 원래 규칙(오독 기반).\
  제공자 순환과 대조 불가를 그대로 남긴다. (기각)
- **배포 전용 스키마 + raw DML 계정** — 기록할 자리는 생기지만 "자유롭게 갱신되는 행"이 남는다.\
  배포 안전을 writer의 선의에 맡기게 된다. (기각)
- **배포 전용 스키마 + 정의된 연산만**(채택) — 새 서버 제품이 아니라 이미 있는 MySQL의 스키마 하나라 도구가 늘지 않고(도구 최소주의 C-08), 어느 계정도 raw DML을 갖지 않는다.

> **raw DML** — 저장 프로시저를 거치지 않고 계정이 직접 던지는 INSERT·UPDATE·DELETE.\
> 예: 계정에 UPDATE 권한을 주면 락 행을 아무 값으로나 덮을 수 있다 — 그 길 자체를 없앤 것이 이 결정이다.

## 3. 그래서 이렇게

핵심 결정(DT-12)은 권한의 단위를 테이블이 아니라 "정의된 연산"으로 잡은 것이다.\
락 행은 일곱 가지 전이(획득·lease 갱신·PREEMPT 기록·안전 경계 ACK·override 획득·채무 해소·해제) 각각의 저장 프로시저로만 바뀌고, 이력 테이블은 append-only(INSERT만)다.\
그래서 배포 스키마에 "자유롭게 갱신되는 행"은 하나도 없다.

> **append-only** — 추가만 되고 수정·삭제는 안 되는 테이블.\
> 예: 장부에 줄을 긋지 않고 새 줄만 더하듯, 이력은 쌓이기만 하므로 과거를 조용히 고칠 수 없다.

같은 규칙을 코드 계층에서도 막았다 — 동일한 규칙을 두 계층에서 강제한다.

```text
배포 계정
   ↓ raw DML 없음 (GRANT에서 차단)
저장 프로시저 7종 · 이력은 INSERT 전용        EXECUTE 권한만 부여
   ↓
락 행 / 이력 테이블                           자유 갱신 행이 하나도 없음
   ↓ 같은 규칙을 코드에서도
internal/store                               일반 Exec/Query를 아예 노출 안 함
```

GRANT에서 금지된 것이 코드에서도 도달 불가능하다.

## 4. 코드 — 실제 커밋에서

재전송 방어를 UNIQUE 제약에 맡긴다 — writer의 선의가 아니라 INSERT 시점의 제약이 판정한다.

```sql
-- deploy/schema/01_tables.sql:59-71 (발췌) — 재전송 방어를 UNIQUE 제약에 맡긴다
-- Append-only. requestId와 jti는 어떤 부작용이 있기 전에 예약된다; UNIQUE 제약은
-- 재생(동일 requestId, 또는 재사용된 OIDC jti)을 재실행 대신 INSERT 시점에 요란하게
-- 실패시킨다. 예약은 삭제할 수 없으므로(append-only, DT-12 ⑵) 재생 방어는 writer의
-- 선의에 의존하지 않는다.
CREATE TABLE IF NOT EXISTS `deploy_request_ledger` (
  `request_id`  VARCHAR(255) NOT NULL,
  `jti`         VARCHAR(255) NULL,
  `body_digest` VARCHAR(128) NOT NULL,
  PRIMARY KEY (`request_id`),
  UNIQUE KEY `uq_jti` (`jti`)
) ENGINE=InnoDB;
```

GRANT를 안 쓴 것 자체가 결정이다 — 부재가 곧 강제다.

```sql
-- deploy/schema/03_grants.sql:50-51 — GRANT를 안 쓴 것이 결정이다
-- 다른 어떤 스키마에도 GRANT 없음. 그 부재가 곧 강제다(DT-10 ⑵): deploy-agent는
-- core/settlement/ledger에 접근이 전혀 없다 — 읽기 포함(R7).
```

컴파일 타임 단언과 "없는 메서드"로 코드 계층을 막는다.

```go
// internal/store/store.go:239-254 (발췌) — 컴파일 타임 단언과 "없는 메서드"
// SQLStore가 모든 store 인터페이스를 만족한다는 컴파일 타임 단언.
var (
    _ LockStore    = (*SQLStore)(nil)
    _ LedgerStore  = (*SQLStore)(nil)   // Reserve(INSERT)만 노출 — 삭제 메서드가 없다
    _ ModeStore    = (*SQLStore)(nil)
    _ HistoryStore = (*SQLStore)(nil)
)
```

## 5. 구현 중 마주친 문제

시크릿 스캔이 코드를 바꾼 기록이 있다 — 하드코딩된 포트가 발견돼 env 조회로 바꾸고 해당 커밋을 재작성했다.

이 PR이 만든 구조 하나는 곧바로 뒤집혔다.\
별도 프로세스로 세운 `cmd/dispatcher`는 다음 PR(#7)에서 삭제된다 — 그 사이에 토폴로지 재판정(단일 바이너리 + ROLE 모드)이 있었기 때문이다.

## 6. 결론

배포 기록의 계약이 스키마로 섰다 — 정의된 연산만, append-only, 두 계층 강제.\
계약 스모크로 agent 계정의 raw UPDATE 거부, 핸드셰이크 ACK 전 override 거절, fencing 단조 증가, requestId 재전송 UNIQUE 거부, EXECUTE 전용 계정의 프로시저 경유 변경 성공(SQL SECURITY DEFINER 성립)을 실 MySQL 8 컨테이너에서 확인했다.

> **fencing token** — 매번 1씩 커지고 리셋되지 않는 번호표.\
> 예: 낡은 보유자가 예전 번호를 들고 오면 다음 재확인에서 토큰 불일치로 감지된다.

남은 빚: 이 스키마는 "세웠다"이지 "안전하다"가 아니다.\
S2-1(#16)에서 실행 있는 리뷰가 반대 계정의 락 해제·0초 lease·유령 락 3건을 실 MySQL에서 실증하고, 수정은 역할별 wrapper 프로시저로 간다(issue6).
