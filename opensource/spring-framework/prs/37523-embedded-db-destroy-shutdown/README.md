# PR #37523 - Shut down embedded database when cleaner fails

## 0. 정향

이 문서는 `spring-jdbc`의 `EmbeddedDatabaseFactoryBean`이 컨텍스트 종료 때 **정리 스크립트(cleaner)가 실패하면 임베디드 DB를 끄지 않고 넘어가던** 결함의 해설이다.\
수정은 `destroy()` 본문을 `try { ... } finally { shutdownDatabase(); }`로 감싸는 것뿐이다.\
그런데 그 한 겹이 없을 때 일어나는 일은 "닫힌 줄 알았던 DB가 같은 JVM 안에 살아남아, 다음 컨텍스트가 이전 컨텍스트의 테이블을 보게 되는" 원인 불명의 실패다.

> **임베디드 DB(embedded database)** — 애플리케이션과 같은 JVM 안에서 메모리에 띄우는 데이터베이스(HSQL, H2, Derby).\
> 예: `jdbc:hsqldb:mem:testdb`는 파일 없이 JVM 메모리에만 존재하는 HSQL DB다.

> **DisposableBean#destroy** — 스프링 컨테이너가 닫힐 때 빈에게 "정리하라"고 부르는 콜백.\
> 예: `EmbeddedDatabaseFactoryBean`은 이 콜백에서 cleaner를 돌리고 DB를 끈다.

> **database cleaner** — 빈이 파괴될 때 실행하도록 등록한 SQL 스크립트 실행기(`DatabasePopulator`).\
> 예: XML의 `<jdbc:script location="drop.sql" execution="DESTROY"/>`가 cleaner로 주입된다.

다 읽으면 다음 셋을 설명할 수 있어야 한다.

- "cleaner 하나가 실패했을 뿐인데 왜 다음 컨텍스트가 깨지는가, 그리고 왜 그 사이에 아무 신호도 없는가"
- "왜 `catch`가 아니라 `finally`인가"
- "수정 후 cleaner 예외는 어디로 가고, 정상 경로에서는 무엇이 바뀌었는가"

상태: **OPEN**(2026-10-20 01:11 KST 제출, main 대상, 라벨 `status: waiting-for-triage`).\
CI는 Build Pull Request / DCO / Backport Bot 전부 SUCCESS(2026-10-20 `gh pr view` 확인 기준).

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md) -
[이해 게이트 기록](gates.md).

## 1. 배경 - 컨텍스트가 닫힐 때 하는 두 가지 일

`EmbeddedDatabaseFactoryBean`은 `EmbeddedDatabaseFactory`를 상속해 `FactoryBean<DataSource>`·`InitializingBean`·`DisposableBean`을 붙인 클래스다(EmbeddedDatabaseFactoryBean.java:45-46).\
XML 네임스페이스로 쓰면 이렇게 생긴다.

```xml
<jdbc:embedded-database id="dataSource">
	<jdbc:script location="schema.sql"/>                       <!-- INIT: databasePopulator -->
	<jdbc:script location="drop.sql" execution="DESTROY"/>     <!-- DESTROY: databaseCleaner -->
</jdbc:embedded-database>
```

`execution="DESTROY"` 스크립트는 파서가 `databaseCleaner` 프로퍼티로 주입한다(DatabasePopulatorConfigUtils.java:47).\
컨텍스트가 닫히면 컨테이너가 `destroy()`를 부르고, `destroy()`는 두 가지 일을 순서대로 한다.

```text
  컨텍스트 close
        |
        v
  DisposableBeanAdapter.destroy()                     (spring-beans)
        |   ((DisposableBean) bean).destroy()
        v
  EmbeddedDatabaseFactoryBean.destroy()
    1. cleaner 실행    DatabasePopulatorUtils.execute(cleaner, ds)   <- drop.sql
    2. DB 종료         shutdownDatabase()                            <- "SHUTDOWN"
```

1은 "다른 사람을 위해 DB를 알려진 상태로 정리"하는 선택 기능이고(setDatabaseCleaner javadoc, EmbeddedDatabaseFactoryBean.java:51-57), 2는 DB 자체를 메모리에서 없애는 필수 단계다.\
이 결함은 **1이 실패하면 2가 실행되지 않는다**는 것이다.

## 2. 수정 전 동작 - cleaner 다음 줄에 shutdown

```java
@Override
public void destroy() {
	DatabasePopulator cleaner = this.databaseCleaner;
	if (cleaner != null && getDataSource() != null) {
		DatabasePopulatorUtils.execute(cleaner, getDataSource());   // 던지면
	}
	shutdownDatabase();                                             // 여기 도달하지 못한다
}
```
(수정 전 EmbeddedDatabaseFactoryBean.java:84-91)

두 줄이 그냥 위아래로 놓여 있다.\
`DatabasePopulatorUtils.execute`는 `ScriptException`을 그대로 다시 던지고, 그 밖의 예외는 `UncategorizedScriptException`으로 감싸 던진다(DatabasePopulatorUtils.java:63-68).\
어느 쪽이든 런타임 예외라 `destroy()` 밖으로 빠져나가고, 그 아래 `shutdownDatabase()`는 건너뛰어진다.

## 3. 문제 - 실패 하나가 다음 컨텍스트로 번진다

### 발화 조건 - cleaner는 생각보다 쉽게 실패한다

`ResourceDatabasePopulator`의 기본값은 엄격하다.\
`continueOnError = false`, `ignoreFailedDrops = false`(ResourceDatabasePopulator.java:71, :73)이므로 문장 하나라도 실패하면 즉시 예외다.

| 상황 | 예외 |
|---|---|
| DESTROY 스크립트의 `DROP TABLE` 대상이 이미 없다(앱이 런타임에 지웠거나, INIT이 부분 실패) | `ScriptStatementFailedException`(ScriptUtils.java:287-293) |
| 스크립트 파일 경로가 깨졌다 | `CannotReadScriptException` |
| 그 밖의 실패 | `UncategorizedScriptException` |

> **ignoreFailedDrops** — `DROP` 문이 실패했을 때만 골라서 무시할지 정하는 플래그. 기본값 false.\
> 예: false면 `drop table T_MISSING`이 "테이블 없음"으로 실패하는 순간 스크립트 전체가 예외로 끝난다.

### 결과 1 - 신호가 WARN 한 줄뿐이다

`destroy()`를 부르는 쪽은 `DisposableBeanAdapter`다.

```java
try {
	((DisposableBean) this.bean).destroy();
}
catch (Throwable ex) {
	if (logger.isWarnEnabled()) {
		String msg = "Invocation of destroy method failed on bean with name '" + this.beanName + "'";
		if (logger.isDebugEnabled()) {
			logger.warn(msg, ex);
		}
		else {
			logger.warn(msg + ": " + ex);
		}
	}
}
```
(DisposableBeanAdapter.java:208-222, 주석 생략)

`catch (Throwable)`이 받고, 다시 던지지 않는다.\
debug 레벨이 아니면 스택 트레이스도 없이 WARN 한 줄만 남는다.\
컨텍스트 종료는 정상으로 끝난 것처럼 보인다.

### 결과 2 - DB가 메모리에 남는다

`shutdownDatabase()`는 configurer의 `shutdown`을 불러 `SHUTDOWN` 문을 실행한다(EmbeddedDatabaseFactory.java:223-239, AbstractEmbeddedDatabaseConfigurer.java:41-68).\
이것이 건너뛰어지면 인메모리 DB가 지워지지 않는다.

| DB 타입 | 접속 URL | 왜 남나 |
|---|---|---|
| **HSQL (기본)** | `jdbc:hsqldb:mem:<이름>`(HsqlEmbeddedDatabaseConfigurer.java:63) | mem 카탈로그는 `SHUTDOWN` 전까지 JVM에 유지 |
| H2 | `jdbc:h2:mem:<이름>;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=false`(H2EmbeddedDatabaseConfigurer.java:64) | `DB_CLOSE_DELAY=-1`이라 마지막 커넥션이 닫혀도 유지 |

타입을 지정하지 않으면 HSQL이다 - 코드 기본값(EmbeddedDatabaseFactory.java:187-189)도, XML의 `type` 속성 기본값(spring-jdbc.xsd:66 `default="HSQL"`)도 그렇다.\
이 표의 첫 행은 작업 도중 리뷰가 바로잡은 사실이다(아래 "정정된 오해").

> **DB_CLOSE_DELAY=-1** — H2에서 "마지막 커넥션이 닫혀도 인메모리 DB를 지우지 말라"는 URL 옵션.\
> 예: 이 옵션이 없으면 H2 mem DB는 커넥션이 0개가 되는 순간 사라진다.

### 결과 3 - 같은 이름으로 다음 컨텍스트가 붙는다

DB 이름은 고정이다.\
프로그래매틱 기본값은 `"testdb"`이고 고유 이름 생성 옵션은 꺼져 있다(EmbeddedDatabaseFactory.java:73, :77, :79).\
XML에서는 `database-name`이 없으면 빈 `id`를 이름으로 쓰고, `id`도 없을 때만 `testdb`가 된다(EmbeddedDatabaseBeanDefinitionParser.java:80-92).\
어느 쪽이든 **같은 설정으로 다시 뜨는 컨텍스트는 같은 이름**을 쓴다.

```text
  같은 JVM (예: 컨텍스트를 여러 번 띄우는 테스트 스위트)

  컨텍스트 A
    init: CREATE TABLE T_TEST ...                 -> jdbc:hsqldb:mem:testdb 에 T_TEST 생성
    close: cleaner 실패 -> WARN 한 줄
           shutdownDatabase() 건너뜀              -> testdb 는 메모리에 그대로
        |
        v
  컨텍스트 B (같은 설정)
    jdbc:hsqldb:mem:testdb 접속                    -> A 가 남긴 DB 를 그대로 받는다
    init: CREATE TABLE T_TEST ...                 -> "table already exists" 로 실패
        ^
        증상은 여기서 나타나지만, 원인은 A 의 cleaner 실패다
```

**이중으로 조용한 결함이다.**\
원인 쪽(A)에는 WARN 한 줄만 남고, 증상 쪽(B)은 원인과 무관해 보이는 오류로 나타난다.

### 왜 아무도 못 봤나

1. **노출면이 좁다.**\
   XML 네임스페이스나 `setDatabaseCleaner`로 cleaner를 쓰는 사용자 중, cleaner가 실패하는 경우에만 일어난다.\
   Spring Boot의 기본 경로는 이 FactoryBean을 쓰지 않는다(사전 분석 기록).
2. **기존 테스트는 성공 경로만 본다.**\
   `factoryBeanLifecycle`은 cleaner 없이 init과 destroy를 한 번 돌린다(EmbeddedDatabaseFactoryBeanTests.java:45-56).\
   기존 XML 테스트 리소스 셋(`jdbc-destroy-config.xml` 등)도 DESTROY 스크립트가 성공하는 구성이다.
3. **증상이 원인에서 멀리 떨어져 나타난다.**\
   B의 "already exists"를 본 사람은 B의 스크립트를 의심하지, A의 종료 로그를 뒤지지 않는다.

### 같은 계열 안의 비대칭

이 수정의 가장 강한 근거는 바로 위 부모 클래스에 있다.\
`EmbeddedDatabaseFactory.initDatabase()`는 populator가 실패하면 DB를 끄고 나서 예외를 다시 던진다.

```java
if (this.databasePopulator != null) {
	try {
		DatabasePopulatorUtils.execute(this.databasePopulator, this.dataSource);
	}
	catch (RuntimeException ex) {
		// failed to populate, so leave it as not initialized
		shutdownDatabase();
		throw ex;
	}
}
```
(EmbeddedDatabaseFactory.java:205-214)

"스크립트 실패가 DB를 살려 두면 안 된다"는 판단이 INIT 쪽에는 코드로 이미 있었다.\
DESTROY 쪽만 그 원칙이 빠져 있었다.

## 4. 수정 해설 - try/finally 한 겹

```java
@Override
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
(EmbeddedDatabaseFactoryBean.java:84-95)

cleaner가 던질 때 실행 순서는 이렇다.

```text
  1. try 안에서 cleaner 가 ScriptStatementFailedException 을 던진다 -> try 중단
  2. 메서드를 빠져나가기 "전에" finally 의 shutdownDatabase() 가 실행된다 -> DB 종료
  3. finally 가 끝난 뒤에야 같은 예외 객체가 destroy() 밖으로 나간다
  4. 호출자(DisposableBeanAdapter)가 그것을 받아 WARN 으로 기록한다
```

순서 2와 3은 이해 게이트에서 두 번 뒤집혀 읽힌 지점이다("호출자가 잡고 그 후 finally") - [gates.md](gates.md).\
finally는 예외가 호출자에게 **도달하기 전에** 실행된다.

### 왜 catch가 아니라 finally인가

세 형태를 나란히 놓으면 답이 보인다.

| 형태 | destroy 밖으로 예외가 나가나 | 상위 WARN 로그 | DB shutdown |
|---|---|---|---|
| **수정 전** | 나감 | 남음 | **안 됨** (결함) |
| catch로 잡고 끝냄 (가상) | 안 나감 | **안 남음** | 됨 |
| catch + 다시 던짐 (initDatabase식) | 나감 | 남음 | 됨 |
| **finally (이번 수정)** | 나감 | 남음 | 됨 |

- **catch로 잡고 끝내면** DB는 닫히지만 그나마 남던 WARN 한 줄마저 사라진다. 실패를 숨기는 수정이다.
- **catch + rethrow**는 결과가 finally와 같다. 하지만 정상 경로용 `shutdownDatabase()`를 한 번 더 써야 하고, `RuntimeException`만 잡으면 `Error`류는 빠져나간다.
- **finally**는 예외를 잡지 않으므로 그대로 전파되고, 예외 종류와 상관없이 정상 경로까지 포함해 한 곳에서 한 번 실행된다.

`initDatabase`가 catch를 쓰는 데는 이유가 있다.\
init은 **성공하면 DB를 닫으면 안 되고** 실패할 때만 닫아야 한다.\
destroy는 성공하든 실패하든 무조건 닫으므로 finally가 맞는 형태다(spec §10 "기각: catch-cleanup-rethrow 형태 - finally가 동치이며 더 단순").

> **try/finally** — 블록이 정상 종료하든 예외로 중단되든 finally 블록을 반드시 실행하고, 예외였다면 finally가 끝난 뒤 그 예외를 계속 전파하는 자바 구문.\
> 예: catch가 없으면 예외는 잡히지도 감싸지지도 않고 같은 객체로 밖에 나간다.

### 정상 경로는 바뀌지 않는다

cleaner가 성공하거나 없을 때, 수정 전후 모두 cleaner 1번 -> shutdown 1번이 같은 순서로 실행된다.\
**관측되는 동작은 같고 코드 구조만 바뀌었다.**\
이 수정이 바꾸는 동작은 cleaner가 실패할 때뿐이다(diff 2 게이트에서 사용자가 "try 로 감싸진거? 말곤 그대로 아니야?"라고 되물은 것이 정답이었다).

### 남은 트레이드오프 - TO-1

finally 안의 `shutdownDatabase()`가 다시 예외를 던지면, 그 예외가 원래 cleaner 예외를 덮어쓴다.\
명세에서 두 안을 놓고 골랐다.

| 안 | 내용 | 선택 |
|---|---|---|
| **A** | 단순 try/finally. shutdown 예외가 cleaner 예외를 대체할 수 있음 | **채택** |
| B | catch로 cleaner 예외를 보관하고 shutdown 예외를 `addSuppressed` | 기각 - 코드 약 3배, 이 코드베이스의 destroy 관용구와 다름 |

A를 받아들인 근거는 두 가지다.\
첫째, 대체되더라도 shutdown이 아예 실행되지 않는 현행보다 나쁘지 않다.\
둘째, 실제로는 거의 일어나지 않는다 - `AbstractEmbeddedDatabaseConfigurer.shutdown`은 `SQLException`을 info 로그로 처리하고 던지지 않으며(AbstractEmbeddedDatabaseConfigurer.java:52-53), Derby configurer도 예외를 로그로 삼킨다(DerbyEmbeddedDatabaseConfigurer.java:74-85).\
둘째 근거는 리뷰 단계에서 실코드로 확인해 명세에 보강했다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다.

> **red(레드)** — 고치기 전에 새 테스트를 돌려 일부러 실패를 확인하는 단계.\
> 예: 여기서 실패하지 않으면 그 테스트는 이 결함을 겨냥하지 못한 것이다.

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 새 테스트 `shutdownDatabaseWhenDatabaseCleanerFails` | red - `expected: 0 but was: 1`(L74 `isZero`). 예외 전파 단언(L66)은 통과 | green |
| 기존 `factoryBeanLifecycle` | green | green |
| `:spring-jdbc:check` | - | exit 0, **spring-jdbc 1,034 tests, 0 failures** + checkstyle 통과 |
| diff 규모 | - | 2파일 +31/-4 (프로덕션 `destroy()` 한 겹 + 테스트 메서드 1개, import 3줄) |

stakes는 **중간**으로 판정했다.\
부분 실패 경로의 리소스 정리라 표의 "부분 실패" 행에 해당하고, blast radius는 DESTROY 스크립트 사용자로 작으며, 변경은 try/finally라 되돌리기 쉽다.\
그래서 리뷰는 **듀얼 1패스**(Opus 워커와 codex 병렬, 메인 종합, codex 감사, post-fix 재점검)였다.\
blind 테스트 워커와 설계 선검증은 중간 stakes의 비대상이다.

load-bearing 가정 둘도 실행으로 확인했다.

- **가정 1** - 수정 전에는 cleaner 실패 후 같은 이름의 인메모리 DB가 살아남아 이전 테이블이 보인다 -> 수정 전 red(`but was: 1`)로 성립.
- **가정 2** - `shutdownDatabase()`는 cleaner 실패와 독립적으로 성공한다 -> 수정 후 green으로 성립.

## 6. 리뷰 - 코드 지적 0건, 그러나 설명이 틀려 있었다

**양측 모두 코드 finding 0건**이었다.\
그런데 리뷰가 찾은 것은 코드가 아니라 **설명의 오류**였다.

**(1) 발주.**\
base `49adc91c7e4`..`a8632e9217b`(amend 전 커밋)의 diff와 spec을 담은 읽기 전용 미러를 만들어 Opus 워커와 codex를 병렬로 돌렸다.\
보안 스캔은 0건이었다.

**(2) Opus - finding 0, 열린 질문 셋.**

- **OQ-1(기본 타입은 HSQL)**: 테스트는 DB 타입을 지정하지 않으므로 `EmbeddedDatabaseFactory.java:187-189`에 따라 HSQL로 돈다.\
  그런데 spec, 게이트 설명, 커밋 본문은 DB가 남는 이유를 H2의 `DB_CLOSE_DELAY=-1`로만 설명했다.\
  테스트 자체는 유효하다 - HSQL mem 카탈로그도 `SHUTDOWN` 전까지 남고, 수정 전 red가 바로 HSQL에서 난 실측이다.\
  메인이 실코드로 확인해 사실로 판정했다.
- **OQ-2(줄 길이)**: 테스트 L73이 109열로, AGENTS.md의 "105 acceptable"을 넘는다(120 max 이내).
- **OQ-3(실패 시 정리)**: 단언이 실패하면 `next.destroy()`가 실행되지 않는다. 하지만 이름 `cleanerFailure`가 고유해 다른 테스트에 영향이 없다고 리뷰어 스스로 결론지었다.

**(3) codex - finding 0, 열린 질문 하나.**\
"미러에 실행 결과가 없어 테스트를 실제로 돌렸는지 확인하지 못했다"였다.

**(4) 메인 종합과 codex 감사.**

| id | 내용 | 처리 |
|---|---|---|
| A1 | spec·커밋 본문의 H2 단정 -> 기본 HSQL로 정정 | **채택** - spec §8·§10 4곳 정정, 커밋 본문 amend(`23d42a988ae`) |
| A2 | 테스트 L73 줄바꿈 | 채택했다가 **사용자 결정으로 기각** - diff 3 원복 |
| Q1 | 실패 시 `next.destroy()` 미실행 | 기각 - 고유 이름 |
| Q2 | 테스트 실행 여부 | 응답 - log의 실행 기록 + post-fix 재실행(1,034건 0 실패) |

codex 감사는 2건을 냈고 둘 다 받아들였다.\
(a) Q2는 리뷰 자료만으로는 증명되지 않으므로 재실행으로 다시 입증할 것, (b) A1의 spec 정정 범위를 구체적으로(§8 가정 2의 "H2 SHUTDOWN", §10 TO-1까지) 넓힐 것.

**(5) A2 - 사용자가 되돌린 리뷰 채택.**\
줄바꿈을 diff 3으로 올리자 사용자가 "이건 전자가 더 나을 꺼같은데 어떻게 생각해?"라고 물었다.\
메인은 근거를 다시 따져 원복을 추천했다 - 109열은 120 max 이내이고 checkstyle도 통과했으며, spring-jdbc 테스트에 105열을 넘는 줄이 이미 412개 있고, 원래 형태가 쿼리 인자와 `.isZero()` 단언을 분리해 더 읽기 쉽다.\
사용자가 "응 되돌리고 진행하자"로 결정했다.\
리뷰가 낸 것이라도 규칙 위반이 아닌 권장치 맞춤은 사용자 판단으로 기각할 수 있다는 사례다.

**(6) post-fix 재점검(codex).**\
amend한 커밋 본문의 사실 주장은 전부 정확했다(제목 46자, 본문 72열 이내).\
새로 나온 지적은 AGENTS.md의 `Closes gh-` 줄 누락 1건이었고 기각했다 - 대응 이슈가 없고, PR 번호는 만들기 전엔 모르며, 지난 PR들처럼 메인테이너가 머지 때 추가하는 관례다.

### 정정된 오해 - H2가 아니라 HSQL

게이트 브리핑은 처음부터 끝까지 H2 URL(`jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1`)을 근거로 들었다.\
사전 분석 문서가 H2 URL을 근거로 결론을 썼고, 그 틀이 spec과 게이트 패킷, 커밋 본문까지 그대로 옮겨졌다.\
사용자도 G0 2차 답변에서 "설정이 -1로 되어있어서 직접 명시적 셧다운이 필요하다"고 정확히 그 틀로 이해했다.

결함·수정·테스트의 유효성은 바뀌지 않는다.\
HSQL도 `SHUTDOWN` 전까지 남으므로 같은 결함이 같은 방식으로 일어나고, 오히려 **기본 경로가 HSQL이라 영향 범위는 H2 사용자보다 넓다.**\
바뀐 것은 "왜 남는가"의 설명이고, 커밋 본문은 push 전에 "the default HSQL database lives until SHUTDOWN is executed, and H2 databases are created with DB_CLOSE_DELAY=-1"로 고쳤다.

## 7. 교훈

1. **"기본값이 무엇인가"는 설정을 따라가 확인한다.**\
   H2 configurer의 `DB_CLOSE_DELAY=-1`은 눈에 띄는 근거였지만, 타입을 지정하지 않으면 그 코드는 실행조차 되지 않는다.\
   근거 코드를 찾았다면 "그 코드가 기본 경로에서 실제로 불리는가"를 한 번 더 물어야 한다.
2. **red 실측은 설명보다 강한 증거다.**\
   설명이 H2로 틀려 있었는데도 테스트는 정확히 red가 났다 - HSQL에서 돌았기 때문이다.\
   그래서 리뷰가 오류를 찾았을 때 "결함은 실재하는가"는 다시 따질 필요가 없었고, 설명만 고치면 됐다.
3. **정리 경로에서는 catch보다 finally를 먼저 떠올린다.**\
   "실패해도 반드시 해야 할 일"과 "실패를 알려야 할 의무"가 함께 있으면, catch는 둘 중 하나를 희생시키기 쉽다.\
   finally는 예외를 건드리지 않고 정리만 보장한다.
4. **같은 클래스 계열의 대칭을 본다.**\
   INIT 경로에 이미 있는 "실패하면 끈다"가 DESTROY 경로에 없다는 비대칭이 결함의 발견 단서이자 수정의 정당화였다.
5. **리뷰 채택도 사용자의 가독성 판단으로 되돌릴 수 있다.**\
   A2는 규칙 위반이 아니라 권장치(105열) 맞춤이었고, 결과는 오히려 읽기 어려웠다.

## 출처

작업 폴더: spring-framework-fork `docs/plans/2026-10-19/j7-embedded-destroy-shutdown/`(requirement-spec.md, log.md, pr-body.md), 사전 분석 `docs/plans/2026-09-08/j7-embedded-destroy-shutdown/analysis.md`.\
코드 기준: 커밋 `23d42a988ae`(base upstream/main `49adc91c7e4`). file:line은 수정 후 좌표이고, 수정 전 `destroy()`는 L84-91이었다.\
PR: https://github.com/spring-projects/spring-framework/pull/37523 (상태는 2026-10-20 확인 값).
