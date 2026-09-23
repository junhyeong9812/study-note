# cs/issue/database/sql-dialect-and-driver-traps — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
작성한 SQL/매핑 ──▶ 대체 DB · ORM 추정 · 단위 테스트  ──▶ 통과 (초록)
                 └▶ 실제 엔진(버전 · 서버 설정 · 드라이버) ──▶ 여기서만 드러남

[실제 엔진에서만 드러나는 것]
 의미     NULL = NULL 은 UNKNOWN → (MySQL·PG 기본 등) UNIQUE 가 NULL 포함 행 중복 허용 — 엔진·옵션마다 다름
 문법     DROP COLUMN IF EXISTS(타 방언) · INSERT…SELECT…ON DUPLICATE 1064(원인 미특정)·VALUES() 폐기 경로 · 대상 테이블 서브쿼리 재참조 · 예약어
 설정     max_allowed_packet(서버·클라이언트 양쪽) · lower_case_table_names(초기화 시 고정) · charset+collation(FK 호환)
 폭·타입  VARCHAR 폭 불일치 → 외부 유입 시 잘림 · 매핑 TEXT ≠ DDL MEDIUMTEXT(실제 적용된 DDL 확인) · 드라이버 엄격 타입(str ≠ timestamp)
 잠금     온라인 DDL 도 시작·끝 MDL · SQLite writer 1개(WAL 도) → 동시 쓰기 가정한 실행기와 충돌(쓰기 직렬화는 가능)
 부수의미 지연 모드(INITIALLY DEFERRED 등) 제약 = 커밋 시 검사 · 트리거는 마이그레이션에도 발화 · REPLACE = DELETE+INSERT(CASCADE)
          FK_CHECKS·사용자 변수 = 세션 상태(롤백 비대상 · 물리 커넥션 귀속)
 이식     원형 SQL 이 가정한 테이블이 대상 DB 에 없음 → 런타임 500

[교정]
 실제 엔진(같은 버전·같은 서버 설정)의 일회용 컨테이너에 실제 적용 → record-level 확인
 테스트 컨테이너 설정을 운영과 정합 · 컬럼 폭/charset 을 식별자 단위로 통일
 세션 상태가 필요한 문장들은 한 물리 커넥션에 고정
```

## 핵심 문장

- SQL 에서 `NULL = NULL` 은 **UNKNOWN** 이다 — MySQL·PostgreSQL(기본) 등에선 NULL 포함 UNIQUE 가 중복을 막지 못한다(NULL 처리는 엔진·옵션마다 다름 — NULLS NOT DISTINCT·부분 인덱스·식 인덱스로 보완).
- 방언·파서 버전·서버 설정·드라이버 타입 규칙은 **대체 DB·ORM 추정으로 검증되지 않는다** — 실제 엔진에서 돌려야 드러난다.
- 운영과 테스트의 **서버 설정 차이**는 "한쪽에서만 실패"를 만든다.
- 같은 식별자를 담는 컬럼들의 폭이 다르면 **가장 좁은 곳이 잠복 상한**이다.
- "온라인" DDL 도 시작·끝에 **짧은 배타 메타데이터 락**이 필요하다 — 장기 트랜잭션 뒤에서 줄줄이 막힌다.
- 트리거·지연 제약·REPLACE upsert 는 SQL 문면에 안 보이는 **부수 의미**를 갖는다.
- 세션 상태(사용자 변수·FK_CHECKS)는 **물리 커넥션**에 귀속되고 트랜잭션 롤백 대상이 아니다.
