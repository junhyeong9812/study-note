# PR #37523 - 착수 분석: EmbeddedDatabaseFactoryBean.destroy의 shutdown 누락

## 0. 결론 먼저

`EmbeddedDatabaseFactoryBean#destroy`가 database cleaner를 실행한 다음 줄에서 `shutdownDatabase()`를 부르는데, 둘 사이에 try/finally가 없다.\
cleaner가 예외를 던지면 shutdown이 건너뛰어지고, 컨테이너는 그 예외를 WARN 한 줄로 삼키며, 인메모리 DB는 같은 JVM에 남아 같은 이름으로 뜨는 다음 컨텍스트에 이전 스키마를 넘겨준다.\
수정은 `destroy()` 본문을 try로 감싸고 finally에서 `shutdownDatabase()`를 부르는 것이다.

> **착수 분석(analysis)** — 코드를 고치기 전에 실파일을 읽어 결함의 위치·경로·영향 범위를 확정해 두는 문서.\
> 예: 여기서 INIT 쪽에 이미 "실패하면 끈다"가 있음을 먼저 확인했기 때문에 수정을 "기존 원칙과의 대칭"으로 정당화할 수 있었다.

후보 출처는 버그헌트 후보 J7이다.\
사전 분석은 2026-09-08 upstream/main `4c8c6409a27` 기준으로 끝나 있었고, 2026-10-19 upstream/main `49adc91c7e4`에서 결함이 현존함(`destroy()` L84-91, 파일 무변경)과 이 결함을 다루는 열린 PR·이슈가 없음(`EmbeddedDatabaseFactoryBean`, `databaseCleaner`, `embedded database destroy` 검색)을 다시 확인한 뒤 착수했다.

## 1. 무대 - 두 단계가 위아래로 놓인 destroy

```java
@Override
public void destroy() {
	DatabasePopulator cleaner = this.databaseCleaner;
	if (cleaner != null && getDataSource() != null) {
		DatabasePopulatorUtils.execute(cleaner, getDataSource());
	}
	shutdownDatabase();
}
```
(수정 전 EmbeddedDatabaseFactoryBean.java:84-91)

이 메서드를 부르는 것은 컨테이너의 `DisposableBeanAdapter.destroy()`(DisposableBeanAdapter.java:197, 호출 :209)이고, cleaner를 넣는 길은 둘이다.\
XML `<jdbc:script execution="DESTROY">`(DatabasePopulatorConfigUtils.java:47)와 프로그래매틱 `setDatabaseCleaner`(EmbeddedDatabaseFactoryBean.java:58-60)다([structure.md](structure.md) 1절).

## 2. 핵심 이름표

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `EmbeddedDatabaseFactoryBean.destroy` (:84-95) | cleaner 실행 후 DB 종료 | 결함이 사는 자리 |
| `DatabasePopulatorUtils.execute` (:48-69) | populator 실행, `ScriptException`은 그대로 재던짐 | 예외의 출발점 |
| `ResourceDatabasePopulator` (:71, :73) | `continueOnError`·`ignoreFailedDrops` 기본 false | 발화를 현실적으로 만드는 기본값 |
| `EmbeddedDatabaseFactory.shutdownDatabase` (:223-239) | configurer.shutdown 후 `dataSource = null` | **건너뛰어지는 단계** |
| `AbstractEmbeddedDatabaseConfigurer.shutdown` (:41-68) | `SHUTDOWN` 실행, `SQLException`은 info 로그 | TO-1 판단 근거 |
| `HsqlEmbeddedDatabaseConfigurer` (:63) | `jdbc:hsqldb:mem:<이름>` | 기본 타입. SHUTDOWN 전까지 잔존 |
| `H2EmbeddedDatabaseConfigurer` (:64) | `...;DB_CLOSE_DELAY=-1;...` | H2 사용자의 잔존 이유 |
| `EmbeddedDatabaseFactory` (:73, :77, :79, :187-189) | 기본 이름 `testdb`, 고유 이름 off, 기본 타입 HSQL | 다음 컨텍스트로 전이시키는 기본값 |
| `EmbeddedDatabaseFactory.initDatabase` (:205-214) | populate 실패 시 shutdown 후 rethrow | **선례 - 같은 원칙이 INIT에는 있다** |
| `DisposableBeanAdapter.destroy` (:208-222) | `catch (Throwable)` 후 WARN만 | 신호를 한 줄로 줄이는 쪽 |

> **DatabasePopulator** — 커넥션 하나를 받아 SQL 스크립트를 실행하는 전략 인터페이스.\
> 예: `ResourceDatabasePopulator`는 `.sql` 리소스 목록을 문장 단위로 실행한다.

## 3. 결함 경로 단계 추적

DESTROY 스크립트가 이미 없는 테이블을 DROP하는 경우를 따라가면 이렇다.

| 단계 | 동작 | 결과 |
|---|---|---|
| 1 | 컨텍스트 A close -> `DisposableBeanAdapter.destroy()` | `bean.destroy()` 호출 |
| 2 | `DatabasePopulatorUtils.execute(cleaner, ds)` | `drop table ...` 실행 |
| 3 | `ScriptUtils`: DROP 실패, `continueOnError`·`ignoreFailedDrops` 둘 다 false | `ScriptStatementFailedException`(ScriptUtils.java:293) |
| 4 | `execute`의 `catch (ScriptException ex) { throw ex; }` | 같은 예외가 `destroy()` 밖으로 |
| 5 | `shutdownDatabase()` | **실행 안 됨** |
| 6 | `DisposableBeanAdapter`의 `catch (Throwable)` | WARN 한 줄, 재던짐 없음 -> A는 정상 종료처럼 보임 |
| 7 | 인메모리 DB | `SHUTDOWN`이 없었으므로 JVM에 잔존 |
| 8 | 컨텍스트 B가 같은 이름으로 접속 | A의 스키마·데이터를 그대로 받음 -> init의 `CREATE TABLE`이 "already exists" |

## 4. 발화 조건과 확률 - 정직하게

**노출면.**\
XML 네임스페이스나 `setDatabaseCleaner`로 cleaner를 쓰는 사용자 중 cleaner가 실패하는 경우다.\
사전 분석은 Spring Boot의 기본 경로가 이 FactoryBean을 쓰지 않는다고 적었다.\
**절대 빈도는 낮다.**

**발화 조건은 이론적이지 않다.**\
`ResourceDatabasePopulator`의 엄격한 기본값 때문에 DROP 대상이 없거나(앱이 런타임에 이미 지웠거나 INIT이 부분 실패), 스크립트 경로가 깨지면 바로 예외다.

**발화 시 비용은 높다.**\
신호가 WARN 한 줄뿐이고, 실패가 다음 컨텍스트의 무관해 보이는 오류로 전이되므로 진단이 어렵다.\
컨텍스트를 여러 번 띄우는 테스트 스위트가 주 피해자다.

> **load-bearing 가정** — 그것이 참이어야 계획 전체가 성립하는, 아직 확인되지 않은 전제.\
> 예: "cleaner 실패 후 같은 이름의 DB가 정말 살아남는다"가 거짓이면 이 결함은 관측 불가능하고 테스트도 쓸 수 없다.

## 5. 계약과 선례

**계약.**\
`DisposableBean#destroy`의 예외는 컨테이너가 로그로 남기고 종료를 계속한다 - `DisposableBeanAdapter`의 `catch (Throwable)`이 그 구현이다.\
그러므로 `destroy()`가 예외를 던지는 것 자체는 계약 위반이 아니다.\
문제는 예외가 나는 순간 **정리의 나머지가 함께 사라진다**는 것이다.

**선례.**\
`EmbeddedDatabaseFactory.initDatabase`의 주석 "failed to populate, so leave it as not initialized" 아래 `shutdownDatabase(); throw ex;`(EmbeddedDatabaseFactory.java:209-213).\
스크립트 실패 시 DB를 끄고 예외는 그대로 알린다는 원칙이 INIT 쪽에는 있다.

## 6. 수정안

### 6.1 채택안 - try/finally

```java
public void destroy() {
	try {
		DatabasePopulator cleaner = this.databaseCleaner;
		if (cleaner != null && getDataSource() != null) {
			DatabasePopulatorUtils.execute(cleaner, getDataSource());
		}
	}
	finally {
		shutdownDatabase();
	}
}
```

정당화는 세 겹이다.

1. **불변식.** `destroy()`가 끝나면(정상 반환이든 예외든) 임베디드 DB는 종료되어 있다.
2. **보존.** cleaner 예외는 잡지 않으므로 그대로 전파된다 - 컨테이너가 WARN으로 기록하는 현행 동작 불변. 정상 경로의 실행 순서(cleaner -> shutdown)와 cleaner 없음/DataSource null 분기도 불변.
3. **선례와의 대칭.** INIT의 catch-cleanup-rethrow와 형태는 다르지만 의도는 같다. destroy는 무조건 닫아야 하므로 finally가 동치이면서 더 단순하다.

### 6.2 검토했으나 기각한 대안

| 대안 | 기각 이유 |
|---|---|
| initDatabase와 같은 catch-cleanup-rethrow | destroy는 rethrow 외에 할 일이 없어 finally와 동치. shutdown을 두 번 써야 하고 `RuntimeException`만 잡으면 `Error`가 샌다 |
| catch로 잡고 삼킨 뒤 shutdown | WARN 한 줄이라는 유일한 실패 신호마저 사라진다 |
| `addSuppressed`로 두 예외 보존 (TO-1 B) | 정확하지만 코드 약 3배, 이 코드베이스의 destroy 관용구와 다름 |

### 6.3 트레이드오프

| 결정 | 안 | 선택 |
|---|---|---|
| TO-1 shutdown 자체가 던질 때 | (A) 단순 try/finally - shutdown 예외가 cleaner 예외를 대체할 수 있음 / (B) catch로 보관 + `addSuppressed` | **A** - 대체되어도 현행(shutdown 미실행)보다 나쁘지 않고, configurer shutdown은 `SQLException`을 로그로 처리해 통상 성공 |
| TO-2 테스트의 실패 cleaner | (A) 존재하지 않는 테이블을 DROP하는 실제 `ResourceDatabasePopulator` / (B) 항상 던지는 람다 `DatabasePopulator` | **A** - 현실의 발화 조건(엄격한 기본값 + DROP 실패)을 그대로 재현 |

두 결정은 사용자가 "우선 스터디노트 main에 합치고 A로 두자"로 한꺼번에 확정했다.

## 7. 착수 시점의 열린 결정과 그 해소

**인터뷰.**\
범위 = `destroy()`만(J8 `EmbeddedDatabaseConfigurerDelegate` shutdown 미위임은 별건), stakes = 중간(부분 실패 경로의 리소스 정리), 모드 = lazy, 테스트 = 예외 전파 + DB 실제 종료 관측, 브랜치 = upstream/main 기반 `fix/embedded-database-destroy-shutdown` -> main PR(백포트는 메인테이너 판단).

**가정 1 - 수정 전에는 cleaner 실패 후 같은 이름의 인메모리 DB가 살아남아 이전 테이블이 보인다.**\
diff 1 적용 후 신규 테스트가 L74 `isZero`에서 `expected: 0 but was: 1`로 실패했다.\
예외 전파 단언(L66)은 통과했다.\
성립.

**가정 2 - `shutdownDatabase()`는 cleaner 실패와 독립적으로 성공한다.**\
diff 2 적용 후 같은 테스트가 통과했다.\
성립.

**예상 밖 발견 - 근거로 든 DB가 기본 DB가 아니었다.**\
착수 시 가정 1의 근거는 H2의 `DB_CLOSE_DELAY=-1`이었다.\
그런데 테스트는 타입을 지정하지 않으므로 HSQL로 돌았고, 리뷰(Opus OQ-1)가 이것을 짚었다.\
HSQL mem 카탈로그도 `SHUTDOWN` 전까지 남으므로 가정 1은 그대로 성립했지만(실측 red가 HSQL에서 난 것), spec §8·§10 4곳과 커밋 본문을 "기본 HSQL, H2도 동일"로 정정했다.

## 8. 범위 밖

> **범위 밖(out of scope)** — 눈에 띄었지만 이번 변경에서 일부러 손대지 않기로 정한 것.\
> 예: 바로 옆 `EmbeddedDatabaseConfigurerDelegate`의 shutdown 미위임(J8)은 보이지만, 이번 PR은 `destroy()` 하나로 좁혀 둔다.

- **J8 `EmbeddedDatabaseConfigurerDelegate`** - shutdown 미위임. #37523에 반응이 온 뒤 판단하도록 미뤘다.
- **`DataSourceInitializer.destroy()`** - cleaner를 실행하지만 외부 DB 대상이라 "건너뛰어지는 shutdown"이 없다. 동일 결함 아님.
- **`EmbeddedDataSourceProxy.shutdown()`**(EmbeddedDatabaseFactory.java:307-310) - cleaner 없이 `shutdownDatabase()`만 부르므로 영향 없음(리뷰 확인).
- **백포트** - 메인테이너 트리아지 소관. PR은 main 대상.

## 출처

착수 시점(2026-10-19~20)의 명세·log와 2026-09-08 사전 분석을 학습용으로 다듬은 것이다.\
기준 upstream/main `49adc91c7e4`, 결함 위치 `spring-jdbc/src/main/java/org/springframework/jdbc/datasource/embedded/EmbeddedDatabaseFactoryBean.java:84-91`(수정 전).\
작업 폴더: spring-framework-fork `docs/plans/2026-10-19/j7-embedded-destroy-shutdown/`.
