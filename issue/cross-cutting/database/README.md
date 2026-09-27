# database — 스키마 이력·방언·트랜잭션

관계형 DB를 쓸 때 코드 밖(마이그레이션 이력·엔진 설정·트랜잭션 경계)에서 결정되는 패턴이다.\
공통 원리: **DB의 실제 동작은 실 엔진·실 이력에서만 드러난다** — 대체 DB·ORM 추상화·제자리 수정된 이력은 그것을 가린다.

## 공통 원리

```
  코드의 가정 ──▶ ORM/드라이버 ──▶ 실 DB 엔진
                                   │
      ├─ 이력: 적용된 마이그레이션은 불변(append-only)
      ├─ 방언: NULL 유니크·collation·세션 변수·락
      └─ 경계: 트랜잭션 범위 = 원자성 단위
                                   ▼
          대체 DB에서 초록 / 실 DB에서 실패
```

## 패턴 카드

- [migration-discipline](migration-discipline/) — 마이그레이션은 적용된 순간 불변(append-only) 이력이며 순번은 공유 번호공간이다 — 제자리 수정·병렬 브랜치 채번·빌드 산출물 잔존·미생성 리비전이 기동 실패와 누락을 만든다.
- [sql-dialect-and-driver-traps](sql-dialect-and-driver-traps/) — SQL 방언·드라이버·엔진 설정(NULL 유니크·세션 변수·패킷 상한·collation·MDL·SQLite 단일 writer)은 실 DB에서만 드러난다 — 대체 DB·ORM 추정이 아니라 실제 엔진으로 검증한다.
- [transaction-boundary-scope](transaction-boundary-scope/) — 트랜잭션 경계가 곧 원자성 단위다 — 너무 넓으면 한 건 실패가 전부를 되돌리고, 쪼개면 부분 성공이 생기며, 트랜잭션 밖 부수효과(캐시·발행)는 커밋 결과와 따로 논다.
