# issue/kotlin/spring/validate-before-migrate — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **마이그레이션은 컨텍스트 초기화 중에, Runner는 그 뒤에 돈다.**\
   Spring Boot의 Flyway 자동 구성은 마이그레이션을 실행하는 초기화 빈을 등록하고, 그 빈은 컨텍스트 refresh **도중**(DataSource 다음, 그 DataSource를 쓰는 빈들보다 먼저) `migrate()`를 부른다.\
   `ApplicationRunner`는 refresh가 끝나고 컨텍스트가 다 뜬 **뒤**에 불린다.\
   그래서 Runner의 검사가 거부하기 전에 이미 기본 위치의 마이그레이션(트리거 추가·다음 버전)이 DB에 적용돼 있었다 — 거부는 기동만 막고 스키마 변경은 막지 못했다.\
   안내대로 키를 고쳐 같은 DB에 다시 띄우면, 고친 방식에서는 있으면 안 되는 트리거가 남아 있어 **다른 이유로 또 거부**된다 — 사용자는 새 DB를 만들지 않는 한 빠져나올 수 없다.
   > **ApplicationRunner** — 컨텍스트가 완전히 뜬 뒤 한 번 실행되는 Spring Boot 콜백. "기동 직후 검사"에 흔히 쓰지만, 그 전에 끝난 초기화(마이그레이션 포함)를 되돌리지 못한다.

2. **그 훅이 안 불리므로 뒤 검사를 남긴다.**\
   `FlywayMigrationStrategy` 빈을 두면 자동 구성은 `migrate()`를 직접 부르는 대신 그 전략을 부른다 — 전략 안에서 설정 검사를 먼저 돌리고 통과할 때만 `flyway.migrate()`를 부르면, 거부된 기동은 스키마를 건드리지 않는다.\
   하지만 Flyway 자동 구성이 꺼져 있거나(`spring.flyway.enabled=false`) 테스트가 검사 객체를 직접 만들면 그 전략은 불리지 않는다.\
   그래서 Runner 첫머리에서 같은 설정 검사를 **다시** 부른다 — 중복처럼 보이지만 "검사가 어떤 경로에서도 빠지지 않는다"를 지키는 보험이다.
   > **FlywayMigrationStrategy** — Spring Boot가 Flyway 마이그레이션을 실행하는 방식을 바꾸는 확장 지점. 구현체가 있으면 자동 구성이 `migrate()` 대신 이것을 부른다.

3. **"판정에 필요한 사실이 마이그레이션 앞에 이미 있는가"로 가른다.**\
   설정 값(바인딩된 속성·활성 프로필)만 보는 검사는 앞에서 그대로 판정된다.\
   지금의 DB 상태(이미 있는 인덱스·DB 서버 설정 값)를 보는 검사도 앞에서 판정할 수 있다 — DB를 읽기만 하면 된다.\
   어려운 것은 "마이그레이션 **뒤**의 스키마"를 보는 검사(예: 이 방식이면 트리거가 있어야 한다/없어야 한다)다 — 첫 수정은 설정 검사만 앞으로 옮겨서, 방식↔마이그레이션 위치의 대응·DB 서버 설정 검사가 여전히 마이그레이션 뒤에 남아 있었다(리뷰 2회차에서 발견).\
   두 번째 수정은 **지금 스키마를 읽고, 설정된 마이그레이션 위치가 무엇을 만들지 더해 "뒤 스키마"를 예측**한 다음 같은 판정 함수에 넣었다.

4. **예측은 "위치가 있으면 그 객체가 있다"는 가정 위에 있다.**\
   그래서 적용된 객체를 손으로 지운 DB, 검증을 끈 채 다른 판의 같은 버전이 적용된 DB, 기준 버전(baseline)이 높게 잡힌 DB에서는 예측이 실제와 다르다.\
   또 Flyway 검증 오류 중 `migrate()`가 허용하는 종류(반복 마이그레이션 체크섬 변경 등)가 있으면 예측 판정을 건너뛴다.\
   이때 마지막 방어선은 **남겨 둔 마이그레이션 뒤 검사**다 — 예측이 틀려도 뒤 검사가 실제 스키마로 거부하므로 실패는 시끄럽다(다만 그 경로에서는 스키마가 이미 바뀐 뒤다).

5. **앞 검사가 마이그레이션 결과에 의존하는 빈을 기다리면 순환이 된다.**\
   자동 구성에서 `JdbcTemplate` 같은 DB 접근 빈은 마이그레이션 초기화 **뒤**에 만들어지도록 묶여 있다 — 그런 빈을 마이그레이션 전략이 주입받으면 "마이그레이션 → 전략 → JdbcTemplate → 마이그레이션"이 된다.\
   그래서 전략은 설정 객체·환경만 주입받고, DB를 읽어야 할 때는 Flyway 설정이 가진 DataSource로 그 자리에서 읽기 전용 접근을 만든다.\
   또 Flyway는 같은 버전이 두 위치에 있으면 마이그레이션 **해석 단계**에서 스스로 거부한다(스키마 무변경) — 앞 검사가 이 조합을 먼저 자기 예외로 막으면 "이 조합은 Flyway 예외로 거부된다"는 기존 계약(그것을 단언하던 테스트)이 깨진다.\
   그래서 전략은 먼저 읽기 전용 `validate` 결과를 보고, **아직 적용하지 않은 버전(pending)을 뺀** 오류가 있으면 예측 판정을 건너뛰어 `migrate()`가 Flyway 예외로 거부하게 둔다.

6. **세 번째 덧대기 대신 범위를 정하고 기록했다.**\
   두 번째 수정 뒤에도 측정 전용 조합 두 가지는 DB 상태로만 판정돼 마이그레이션 뒤에 거부되는 경로가 남았다 — 같은 불변식의 세 번째 구멍이다.\
   같은 결함을 두 번 고쳐도 또 깨지면 토대를 다듬는 중이라는 신호라, 덧대지 않고 "이 불변식의 범위 밖"으로 명시해 기록했다 — 대신 거부 메시지가 "마이그레이션 위치 전체를 명시하라"고 안내하고, 측정 도구는 위치를 늘 명시한다.\
   받아들일 수 있는 조건은 두 가지다: 남은 경로가 비표준(측정 전용)이고, 그 경로에서도 **조용히 통과하지 않고 거부된다**는 것.\
   회귀 방지는 "거부 → 안내 키로 같은 DB 재기동 → 뜬다 · 거부 뒤 스키마 버전이 그대로" 순서 테스트로 했다 — 수정 전 코드로 되돌리면 4건 중 3건이 실패하는 것을 확인했다.

## 문제 구조 (추상화 코드)

### 변형 A — 거부 검사를 Runner에만 둠
① 문제 코드
```kotlin
@Component
class StartupCheck(private val props: Props, private val jdbc: JdbcTemplate) : ApplicationRunner {
    override fun run(args: ApplicationArguments) {       // 컨텍스트가 다 뜬 뒤 — 마이그레이션은 이미 끝남
        require(props.mode.isValidWith(props.options)) { "잘못된 조합 — 키 X를 주라" }
        checkSchema(readSchema(jdbc))
    }
}
// spring.flyway.locations 기본값 → 기본 위치의 DDL이 refresh 중에 이미 적용됨
```
② 고친 코드
```kotlin
@Configuration
class MigrationGate {
    @Bean
    fun gateStrategy(props: Props, env: Environment) = FlywayMigrationStrategy { flyway ->
        StartupCheck.checkConfig(props, env)              // 설정만 — DB 접근 빈에 기대지 않는다(순환 없음)
        flyway.migrate()                                   // 통과할 때만 DDL
    }
}

@Component
class StartupCheck(private val props: Props, private val env: Environment, private val jdbc: JdbcTemplate) : ApplicationRunner {
    override fun run(args: ApplicationArguments) {
        checkConfig(props, env)                            // Flyway가 꺼진 구성에서도 빠지지 않게 다시
        checkSchema(readSchema(jdbc))                      // DB 상태가 필요한 검사
    }
    companion object {
        fun checkConfig(props: Props, env: Environment) { /* 설정 조합 거부 */ }
    }
}
```
무엇이 깨졌나: 거부 검사가 되돌릴 수 없는 단계 뒤에 있어, 거부된 기동이 다음 기동의 전제를 바꿨다.

### 변형 B — 마이그레이션 뒤 스키마를 보는 검사가 뒤에 남음 → 예측해 앞에서 판정
① 문제 코드
```kotlin
FlywayMigrationStrategy { flyway ->
    checkConfig(props, env)                                // 설정만 앞으로 옮김
    flyway.migrate()                                       // "방식 ↔ 위치" 대응·DB 서버 설정은 여전히 Runner(뒤)에서
}
```
② 고친 코드
```kotlin
FlywayMigrationStrategy { flyway ->
    checkConfig(props, env)
    val cfg = flyway.configuration
    val toolRejects = cfg.isValidateOnMigrate &&
        flyway.validateWithResult().invalidMigrations.orEmpty()
            .any { it.errorDetails?.errorCode !in PENDING }        // 아직 안 적용한 버전은 거부 사유가 아님
    if (!toolRejects) {                                            // 도구가 스스로 막을 조합은 도구의 예외로 남김
        val predicted = readSchema(JdbcTemplate(cfg.dataSource))   // 주입 빈 대신 Flyway 설정의 DataSource
            .afterLocations(cfg.locations.map { it.path })         // 가정: 위치가 있으면 그 객체가 생긴다
        checkSchema(props, predicted)                              // Runner와 같은 판정 함수
    }
    flyway.migrate()
}
// 예측이 어긋나는 비표준 DB(손으로 지운 객체 · 검증 끈 다른 판 · 높은 baseline)는
// Runner의 실제 스키마 검사가 거부한다 — 조용히 통과하지 않음 (범위 밖으로 기록)
```
무엇이 깨졌나: "설정만 보는 검사"만 앞으로 옮겨, 마이그레이션 결과에 달린 거부가 여전히 DDL 뒤에 있었다.

### 테스트 기법 — 거부 뒤 같은 DB 재기동
```kotlin
@Test
fun `잘못된 조합은 마이그레이션 전에 거부 — 같은 DB를 안내 키로 다시 띄우면 뜬다`() {
    val url = freshDbUrl()
    assertFails { boot(url, "--mode=bad-combo").close() }
    assertTrue(maxAppliedVersion(url) <= BASE_VERSION)        // 거부 뒤 스키마 그대로
    boot(url, "--mode=bad-combo", "--fix-key=value").close()  // 안내대로 고치면 같은 DB에서 뜬다
}
// 수정 전 코드로 되돌려 이 테스트들이 실패하는지 확인(4건 중 3건 실패)
```
무엇이 드러나나: "거부했다"가 아니라 "거부가 다음 기동의 전제를 바꾸지 않았다"를 단언한다.

## 검증 기록
- 2026-10-23: 사건 기록 대조·추상화(Claude 초안)

## 관련 카드
- [non-transactional-multi-step](../../../cross-cutting/reliability/non-transactional-multi-step/) — 트랜잭션 없는 다단계 변경은 실패 가능한 쪽을 먼저 하고 그 결과로 되돌릴 수 없는 단계를 게이트한다(이 카드는 프레임워크 기동 순서 안에서 그 지점을 찾는 문제).
- [migration-discipline](../../../cross-cutting/database/migration-discipline/) — 적용된 마이그레이션은 불변 이력이다 — 그래서 거부된 기동이 남긴 DDL은 "되돌리기"가 아니라 앞으로 가는 새 마이그레이션(또는 수동 정리)으로 지운다.
- [framework-default-contracts](../../../java/spring/framework-default-contracts/) — Spring의 기본 순서·조건 평가는 명시하지 않으면 직관과 다르게 동작한다.
