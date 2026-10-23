# issue/kotlin/spring/validate-before-migrate — 정리 (힌트)

## 전체 흐름

```text
[문제 — 검사가 마이그레이션 뒤]
 컨텍스트 refresh
   ├─ DataSource
   ├─ Flyway 초기화 빈 ── migrate() ──▶ 기본 위치의 V9(트리거)·V10 적용   ← 되돌릴 수 없음
   ├─ JdbcTemplate · 나머지 빈
 refresh 끝
   └─ ApplicationRunner ── 설정 조합 검사 ──▶ 거부 (기동 실패)
                                            DB에는 V9·V10이 남음
 안내대로 키를 고쳐 같은 DB로 재기동
   └─ 검사: "이 방식인데 트리거가 있다" ──▶ 또 거부   (고친 설정으로도 못 뜸)

[교정 1 — 설정만 보는 검사를 앞으로]
 Flyway 초기화 빈 ── FlywayMigrationStrategy { checkConfig(); flyway.migrate() }
                       └─ 거부 → migrate 안 함 → 스키마 그대로
 ApplicationRunner ── checkConfig() 다시 (Flyway가 꺼진 구성에서도 빠지지 않게)
                  ── DB 상태 검사 (인덱스·트리거 활성·외부 저장소 등)

[교정 2 — 마이그레이션 뒤 스키마를 보는 검사도 앞으로: 예측]
 FlywayMigrationStrategy {
   checkConfig()
   flywayRejects = 읽기 전용 validate() 결과 중 pending이 아닌 오류가 있나
   if (!flywayRejects) checkSchema(예측 = 지금 스키마 + "위치가 있으면 그 객체가 생긴다")
   flyway.migrate()           ← Flyway가 스스로 막을 조합은 Flyway의 거부로 남김
 }

[남은 경로 — 범위 밖으로 기록]
 예측이 어긋나는 비표준 DB (손으로 지운 객체 · 검증 끈 채 다른 판 적용 · 높은 baseline)
 DB 상태로만 판정되는 측정 전용 조합
   → 마이그레이션 뒤 검사가 거부한다 (조용히 통과하지 않음) · 거부 메시지가 전체 위치 명시를 안내
```

## 핵심 문장

- Spring Boot의 Flyway 마이그레이션은 컨텍스트 초기화 **도중**에 돌고, `ApplicationRunner`는 컨텍스트가 다 뜬 **뒤**에 돈다 — Runner의 거부는 스키마 변경을 막지 못한다.
- 거부할 수 있는 검사는 되돌릴 수 없는 단계(DDL) **앞**에 둔다 — 마이그레이션 직전 지점은 `FlywayMigrationStrategy`다.
- 앞 검사는 **설정만** 보거나, DB를 읽더라도 Flyway 설정의 DataSource를 직접 쓴다 — 마이그레이션에 의존하는 빈을 주입받지 않는다.
- 훅은 그 경로가 돌 때만 돈다 — Flyway가 꺼진 구성을 위해 같은 검사를 뒤에도 남긴다(중복이 아니라 경로 보험).
- 마이그레이션 뒤 상태를 앞에서 판정하려면 **예측**해야 하고, 예측은 비표준 DB에서 어긋난다 — 그래서 뒤 검사는 지우지 않는다.
- 도구가 스스로 하는 거부(같은 버전 둘·체크섬 불일치)는 도구에 맡긴다 — 앞 검사가 그 계약을 다른 예외로 바꾸지 않는다.
- 같은 불변식을 두 번 덧대고도 구멍이 나오면 세 번째 덧대기 대신 범위를 정해 기록한다 — 남은 경로가 **시끄럽게** 실패한다는 것이 조건이다.
