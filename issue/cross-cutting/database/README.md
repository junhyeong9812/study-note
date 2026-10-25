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

- [add-column-default-shared-value](add-column-default-shared-value/) — 비휘발 DEFAULT로 더한 열(빠른 기본값)은 기존 행 전부에 같은 값(열을 더한 트랜잭션의 now())을 준다 — 그 열로 "하한 뒤 바뀐 행"을 찾는 증분은 첫 창이 열 추가 시각을 덮으면 오류 없이 기존 행 전부를 읽으므로, 기동 때 카탈로그 값을 읽어 그 값 앞뒤 두 인덱스 범위로 빼고 키셋 페이지로 틱 비용을 묶는다(단일 열 인덱스의 같은 값 묶음은 예외).
- [catalog-presence-vs-enabled](catalog-presence-vs-enabled/) — 카탈로그 행은 존재를 말할 뿐 효력을 말하지 않는다 — 트리거 존재를 이름으로만 세면 `DISABLE TRIGGER`로 꺼진 트리거도 통과해 그 트리거를 전제로 한 기능이 조용히 유실하므로, "있어야 한다"는 `tgenabled` 허용 목록(O·A)으로, "없어야 한다"는 존재로 판정하고 거부 메시지에 관측 상태와 고치는 문장을 넣는다.
- [hot-update-and-indexed-columns](hot-update-and-indexed-columns/) — HOT 갱신은 인덱스 열이 안 바뀐 UPDATE에만 일어난다 — 갱신마다 바뀌는 변경 추적 열(updated_at)에 B-tree 인덱스를 걸면 HOT이 사실상 0이 되어 갱신마다 모든 인덱스에 새 항목이 생기고, 제자리 갱신 테이블에서는 BRIN이 최근 창을 거르지 못하므로, 비용을 측정 부하에서 재어 판정하고 운영 위험으로 기록한다.
- [migration-discipline](migration-discipline/) — 마이그레이션은 적용된 순간 불변(append-only) 이력이며 순번은 공유 번호공간이다 — 제자리 수정·병렬 브랜치 채번·빌드 산출물 잔존·미생성 리비전이 기동 실패와 누락을 만든다.
- [periodic-full-scan-cost-growth](periodic-full-scan-cost-growth/) — 매 바퀴 전체를 훑는 주기 작업(대조·정리)의 비용은 누적 행 수에 비례해 자라고, fixed delay 스케줄에서는 점유 비율도 함께 커진다 — 짧은 측정은 이를 숨기므로 목표 규모에서 켜고 끄기로 재며, 대처는 풀 분리로 병목을 가른 뒤 증분 대조(+ 드문 전체 훑기)·복제본 탐지·CDC 순으로 고른다.
- [rolled-back-write-cost](rolled-back-write-cost/) — 롤백은 결과만 되돌리고 비용은 되돌리지 않는다(로그·죽은 행) — 시도 대부분이 지는 흐름에서는 쓰기 전에 싼 거절(잠금 없는 선조회)을 두고 최종 판정은 원자 연산에 남기며, 감소만 하는 행에는 정리 주체를 둔다.
- [sql-dialect-and-driver-traps](sql-dialect-and-driver-traps/) — SQL 방언·드라이버·엔진 설정(NULL 유니크·세션 변수·패킷 상한·collation·MDL·SQLite 단일 writer)은 실 DB에서만 드러난다 — 대체 DB·ORM 추정이 아니라 실제 엔진으로 검증한다.
- [temp-spill-on-bounded-storage](temp-spill-on-bounded-storage/) — DB 데이터 디렉터리의 고정 상한은 데이터 크기가 아니라 데이터 + 로그 + 가장 큰 쿼리의 정렬·해시 임시 파일을 담아야 한다 — 임시 파일은 쿼리 동안만 있어 큰 작업 뒤에 공간을 재고, 메모리 파일시스템이면 메모리 한도도 함께 키우며, 요청 크기와 적용 크기를 대조한다.
- [transaction-boundary-scope](transaction-boundary-scope/) — 트랜잭션 경계가 곧 원자성 단위다 — 너무 넓으면 한 건 실패가 전부를 되돌리고, 쪼개면 부분 성공이 생기며, 트랜잭션 밖 부수효과(캐시·발행)는 커밋 결과와 따로 논다.
