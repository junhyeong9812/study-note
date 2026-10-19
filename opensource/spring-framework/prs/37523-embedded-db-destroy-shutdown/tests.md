# PR #37523 - 테스트 해설 (테스트 하나하나)

배치 전체를 먼저 본다.\
이 결함은 **cleaner가 실패하는 destroy에서만** 드러난다.\
그래서 새 테스트 하나가 "cleaner가 실패해도 DB가 꺼지는가"를 맡고, 기존 테스트 하나가 "cleaner가 없거나 성공하는 정상 경로는 그대로인가"를 맡는 구도가 된다.\
새 테스트 안에서도 단언이 둘로 나뉜다 - 하나는 수정 전에 실패하는 red, 하나는 수정 전후 모두 통과해야 하는 보존 단언이다.

> **red 테스트 / 가드 테스트** — red는 수정 전에 반드시 실패해야 하는 테스트, 가드는 수정 전후 모두 통과해야 하는 테스트.\
> 예: red 가 없으면 결함을 겨냥하지 못한 것이고, 가드가 깨지면 기존 동작을 망가뜨린 것이다.

| | cleaner 성공/없음 | cleaner 실패 |
|---|---|---|
| 예외가 그대로 전파되나 | - | T2-(4) `assertThatExceptionOfType` - 보존 가드 |
| DB가 실제로 꺼졌나 | T1 `factoryBeanLifecycle` (init/destroy 정상 수행) - 가드 | **T2-(6) 같은 이름 재접속 후 `T_TEST` count 0 - red** |

같은 배치를 fix 전후 결과까지 넣은 격자로 보면 각 칸이 무엇을 덮는지가 드러난다.

```text
                                       |  fix 전  |  fix 후  |  덮는 것
---------------------------------------+----------+----------+------------------------------
T2-(6) 재접속 후 T_TEST count == 0     |  FAIL    |  PASS    |  cleaner 실패 후에도
       "expected: 0 but was: 1"        |          |          |  shutdown 이 일어났나
---------------------------------------+----------+----------+------------------------------
T2-(4) ScriptStatementFailedException  |  PASS    |  PASS    |  수정이 예외를 삼키거나
       전파                            |          |          |  바꾸지 않았나
---------------------------------------+----------+----------+------------------------------
T1 factoryBeanLifecycle                |  PASS    |  PASS    |  정상 경로 무회귀
```

-> 오른쪽 위 칸(cleaner 실패 경로)이 비어 있었던 것이 이 결함이 살아남은 이유다. 기존 테스트는 처음부터 정상 경로 하나뿐이었다.

## T2. `shutdownDatabaseWhenDatabaseCleanerFails` - red

새로 추가한 유일한 테스트다.\
전문은 이렇다.

```java
@Test
void shutdownDatabaseWhenDatabaseCleanerFails() {
	EmbeddedDatabaseFactoryBean bean = new EmbeddedDatabaseFactoryBean();
	bean.setDatabaseName("cleanerFailure");                                              // (1)
	bean.setDatabasePopulator(new ResourceDatabasePopulator(resource("db-schema.sql")));  // (2)
	bean.setDatabaseCleaner(new ResourceDatabasePopulator(
			new ByteArrayResource("drop table T_MISSING".getBytes(), "inline SQL")));     // (3)
	bean.afterPropertiesSet();
	assertThatExceptionOfType(ScriptStatementFailedException.class).isThrownBy(bean::destroy);  // (4)

	EmbeddedDatabaseFactoryBean next = new EmbeddedDatabaseFactoryBean();
	next.setDatabaseName("cleanerFailure");                                              // (5)
	next.afterPropertiesSet();
	JdbcTemplate template = new JdbcTemplate(next.getObject());
	assertThat(template.queryForObject(
			"select count(*) from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'T_TEST'", Integer.class))
			.isZero();                                                                   // (6)
	next.destroy();
}
```
(EmbeddedDatabaseFactoryBeanTests.java:58-76. 번호 주석은 게이트 질문에서 붙인 것이고 실제 코드에는 없다.)

이 테스트가 주장하는 것과 수정 전에 red가 되는 이유를 먼저 두 줄로 적어 둔다.

- **주장**: cleaner가 실패해 `destroy()`가 예외를 던져도, 그 예외는 원래 타입 그대로 나오고, 같은 이름의 DB를 새로 열면 이전 테이블이 없다 - 즉 DB가 실제로 종료됐다.
- **fix 전 red인 이유**: cleaner 예외 때문에 `shutdownDatabase()`가 건너뛰어지고, HSQL mem DB `cleanerFailure`가 메모리에 남아 (5)가 그 DB에 다시 붙는다.\
  실측 red는 `expected: 0 but was: 1`(L74 `isZero`).

테스트가 세 국면으로 나뉜다는 것을 먼저 보면 이후 설명이 붙을 자리가 생긴다.

```text
  [1] 첫 번째 빈 - 실패할 cleaner 를 품은 DB
      (1) 이름 cleanerFailure   (2) init 때 T_TEST 생성   (3) destroy 때 실행될 cleaner 등록
      afterPropertiesSet() -> jdbc:hsqldb:mem:cleanerFailure 생성 + T_TEST 생성
              |
              v
  [2] destroy - cleaner 실패
      (4) bean::destroy -> drop table T_MISSING 실패 -> ScriptStatementFailedException
          수정 전: shutdown 건너뜀 / 수정 후: finally 에서 shutdown 후 예외 전파
              |
              v
  [3] 두 번째 빈 - 같은 이름으로 재접속해 흔적 확인
      (5) 이름 cleanerFailure, populator 없음
      (6) INFORMATION_SCHEMA 에서 T_TEST 개수 == 0 ?
          수정 전: 1 (이전 DB 그대로) / 수정 후: 0 (새 빈 DB)
```

### (3)은 무엇을 지우는가 - 아무것도 지우지 않는다

이해 게이트에서 가장 오래 걸린 지점이다([gates.md](gates.md)).\
(3)의 `drop table T_MISSING`은 테이블을 정리하는 단계가 아니라 **실패를 일으키는 장치**다.\
`T_MISSING`은 어디에도 만들어진 적이 없으므로 DROP은 반드시 실패하고, `ResourceDatabasePopulator`의 기본값(`continueOnError=false`, `ignoreFailedDrops=false`)이 그 실패를 `ScriptStatementFailedException`으로 바꾼다(ScriptUtils.java:287-293).

그러면 (6)에서 `T_TEST`를 없애는 것은 누구인가.\
**DROP이 아니라 SHUTDOWN이다.**\
(2)가 만든 `T_TEST`는 `SHUTDOWN`이 DB 자체를 메모리에서 지워야만 사라진다.\
그래서 (6)은 "테이블이 지워졌나"가 아니라 **"shutdown이 실제로 일어났나"**를 확인하는 단언이다.

> **INFORMATION_SCHEMA.TABLES** — SQL 표준의 시스템 뷰로, DB 안에 있는 테이블 목록을 행으로 돌려준다.\
> 예: `TABLE_NAME = 'T_TEST'`인 행 수를 세면 그 테이블이 존재하는지 알 수 있다. HSQL은 대문자로 저장하므로 `'T_TEST'`로 비교한다.

### 왜 실제 `ResourceDatabasePopulator`인가 (TO-2)

| 안 | 방식 | 장단 |
|---|---|---|
| **A (채택)** | 존재하지 않는 테이블을 DROP하는 실제 `ResourceDatabasePopulator` | 현실의 발화 조건(엄격한 기본값 + DROP 실패)을 그대로 재현 |
| B | 항상 던지는 람다 `DatabasePopulator` | 가장 단순하지만 원인과 무관한 인공 실패 |

인라인 SQL은 `ByteArrayResource`로 넣어, 테스트 리소스 파일을 새로 만들지 않았다(spec §4 "테스트는 `EmbeddedDatabaseFactoryBeanTests.java`만").

### 왜 (4)는 수정 전에도 통과하는가 - 보존 단언

(4)는 red가 아니다.\
cleaner는 수정 전이든 후든 똑같이 실패하므로 예외는 원래부터 나고 있었다.\
이 테스트에는 스프링 컨테이너도 `DisposableBeanAdapter`도 없다 - `bean::destroy`를 **테스트 코드 자신이** `isThrownBy`로 직접 부르고, 던져진 예외를 직접 받는다.

그러면 (4)는 왜 있나.\
spec §2의 보존 조건 "cleaner 예외는 그대로 전파" 때문이다.\
수정이 예외를 catch로 삼키거나 다른 예외로 감싸면 (4)가 실패해서 그것을 잡아낸다.\
finally에는 catch가 없으므로 cleaner가 던진 바로 그 `ScriptStatementFailedException` 객체가 나오고, `isThrownBy`가 그 타입을 확인한다.

### 왜 이름을 `cleanerFailure`로 따로 주는가

기본 이름 `testdb`를 쓰면 같은 클래스의 `factoryBeanLifecycle`이나 다른 테스트와 DB를 공유할 수 있다.\
고유 이름을 주면 (5)가 붙는 DB가 (1)의 DB뿐임이 보장되고, 테스트가 실패해 `next.destroy()`가 실행되지 않더라도 다른 테스트에 흔적이 번지지 않는다(리뷰 OQ-3, 이름은 spring-jdbc 테스트에서 L61과 L69에만 나온다).

### 왜 두 번째 빈에는 populator가 없는가

(5)의 `next`에 populator를 주면 `db-schema.sql`이 `T_TEST`를 다시 만들어 (6)이 항상 1이 된다.\
populator 없이 열어야 (6)의 개수가 순수하게 "이전 DB가 남았는가"만 반영한다.\
(참고로 `db-schema.sql`은 `drop table T_TEST if exists;`로 시작하므로, 첫 번째 빈의 init은 이전 실행의 흔적이 있어도 실패하지 않는다.)

## T1. `factoryBeanLifecycle` - 무회귀 가드 (전후 green)

기존 테스트다.

```java
@Test
void factoryBeanLifecycle() {
	EmbeddedDatabaseFactoryBean bean = new EmbeddedDatabaseFactoryBean();
	ResourceDatabasePopulator populator = new ResourceDatabasePopulator(resource("db-schema.sql"),
		resource("db-test-data.sql"));
	bean.setDatabasePopulator(populator);
	bean.afterPropertiesSet();
	DataSource ds = bean.getObject();
	JdbcTemplate template = new JdbcTemplate(ds);
	assertThat(template.queryForObject("select NAME from T_TEST", String.class)).isEqualTo("Keith");
	bean.destroy();
}
```
(EmbeddedDatabaseFactoryBeanTests.java:45-56)

이 테스트가 결함을 못 잡은 이유와 지금 맡는 역할은 같은 사실의 두 면이다.

- **못 잡은 이유**: cleaner를 등록하지 않는다.\
  `destroy()`는 cleaner 분기를 건너뛰고 바로 `shutdownDatabase()`로 가므로, 수정 전에도 결함 경로를 지나지 않는다.\
  게다가 destroy 이후 DB 상태를 확인하지도 않는다.
- **지금 맡는 역할**: 정상 경로의 init -> 사용 -> destroy가 수정 후에도 예외 없이 돈다는 것을 고정한다.\
  정상 경로에서는 수정 전후 모두 cleaner 분기 판정 1번 -> shutdown 1번으로 실행 순서가 같다(diff 2 게이트의 결론 "관측 동작은 같고 코드 구조만 다르다").

## 실측 요약

| 시점 | 대상 | 결과 |
|---|---|---|
| fix 전 | `EmbeddedDatabaseFactoryBeanTests` | 2건 중 신규 1건만 FAIL - `expected: 0 but was: 1`(L74). (4)는 통과 -> 가정 1 성립 |
| fix 후 | `:spring-jdbc:check` | exit 0 - spring-jdbc **1,034 tests, 0 failures**, checkstyle 통과. 신규·`factoryBeanLifecycle` PASS |
| 리뷰 수정 후 | `:spring-jdbc:check` 재실행 | exit 0, 1,034건 0 실패 (codex 감사 Q2 대응) |
| 반증 | 기존 `jdbc-destroy-*.xml` 사용 테스트 | 전체 스위트 green에 포함 |

- **diff 규모**: 2파일 +31/-4. 프로덕션은 `destroy()`를 try/finally로 감싼 것(+8/-4), 테스트는 메서드 1개와 import 3줄(`ByteArrayResource`, `ScriptStatementFailedException`, `assertThatExceptionOfType`).
- **실행된 DB**: 테스트가 타입을 지정하지 않으므로 HSQL(`jdbc:hsqldb:mem:cleanerFailure`)에서 돌았다.\
  게이트 패킷은 이 테스트를 H2 URL(`jdbc:h2:mem:cleanerFailure;DB_CLOSE_DELAY=-1`)로 설명했는데, 리뷰에서 HSQL로 바로잡혔다.\
  수정 전 red가 HSQL에서 났다는 사실 자체가 "HSQL mem DB도 SHUTDOWN 전까지 남는다"의 실측이다.

## 리뷰가 남긴 테스트 관련 판단

| id | 지적 | 처리 |
|---|---|---|
| OQ-2 / A2 | L73이 109열(AGENTS.md 105 acceptable 초과, 120 max 이내) | 줄바꿈을 diff 3으로 올렸다가 사용자 결정으로 원복 - 기각 |
| OQ-3 / Q1 | (4)나 (6)이 실패하면 `next.destroy()` 미실행 | 기각 - 고유 이름이라 다른 테스트 영향 없음, try/finally를 더할 가치 없음(리뷰어 스스로 결론) |

diff 3으로 올렸던 줄바꿈은 이렇다.

```java
// 원래 (커밋에 남은 형태)
assertThat(template.queryForObject(
		"select count(*) from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'T_TEST'", Integer.class))
		.isZero();

// diff 3 (원복됨)
assertThat(template.queryForObject(
		"select count(*) from INFORMATION_SCHEMA.TABLES where TABLE_NAME = 'T_TEST'",
		Integer.class)).isZero();
```

원래 형태는 쿼리 인자(문자열과 `Integer.class`)가 한 줄에 모이고 `.isZero()` 단언이 따로 떨어진다.\
diff 3은 `Integer.class)).isZero()`에 인자와 단언이 섞인다.\
검증 내용은 둘이 완전히 같고, 차이는 가독성뿐이다.
