# PR #37523 - 무대의 실구조와 워크플로우

## 1. 무대 - 실구조

이 결함의 무대는 **스프링 컨테이너의 빈 파괴 콜백이 임베디드 DB 팩토리에 닿는 자리**다.\
위로는 예외를 삼키는 어댑터가 있고, 아래로는 DB를 실제로 없애는 configurer가 있으며, 그 사이의 `destroy()` 한 메서드가 두 단계를 순서대로 부른다.

> **DisposableBeanAdapter** — 컨테이너가 빈 하나의 파괴 콜백(`DisposableBean#destroy`, `AutoCloseable#close`, 커스텀 destroy 메서드)을 대신 불러 주는 spring-beans의 어댑터.\
> 예: 컨텍스트 close 때 파괴 콜백이 있는 빈마다 불려, 콜백의 예외를 잡아 로그로 남기고 다음 빈으로 넘어간다.

계층을 위에서 아래로 그리면 이렇다.

```text
+------------------------------------------------------------------------------+
| 설정                                                                         |
|   <jdbc:embedded-database id="dataSource">                                   |
|     <jdbc:script location="drop.sql" execution="DESTROY"/>                   |
|   EmbeddedDatabaseBeanDefinitionParser                                       |
|     DatabasePopulatorConfigUtils.setDatabasePopulator     :47                |
|       -> databaseCleaner 프로퍼티 (ResourceDatabasePopulator)                |
|   또는 프로그래매틱 setDatabaseCleaner(...)   EmbeddedDatabaseFactoryBean:58  |
+------------------------------------------------------------------------------+
                                    |  컨텍스트 close
                                    v
+------------------------------------------------------------------------------+
| DisposableBeanAdapter.destroy()                    (spring-beans) :197       |
|   try { ((DisposableBean) bean).destroy(); }                      :208-210   |
|   catch (Throwable ex) { logger.warn(...); }   <- 재던짐 없음     :211-222   |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| EmbeddedDatabaseFactoryBean.destroy()                             :84-95     |
|   try {                                                                      |
|     DatabasePopulatorUtils.execute(cleaner, getDataSource())      :89        |
|       -> ResourceDatabasePopulator -> ScriptUtils.executeSqlScript           |
|          DROP 실패 + 기본값 엄격 -> ScriptStatementFailedException  :293      |
|   }                                                                          |
|   finally {                                                                  |
|     shutdownDatabase()                  <- 수정 전에는 try 밖 한 줄 :90       |
|   }                                                                          |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| EmbeddedDatabaseFactory.shutdownDatabase()                        :223-239   |
|   databaseConfigurer.shutdown(dataSource, databaseName)           :234-235   |
|   this.dataSource = null                                          :237       |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| AbstractEmbeddedDatabaseConfigurer.shutdown()                     :41-68     |
|   stmt.execute("SHUTDOWN")                                        :48        |
|   catch (SQLException) -> logger.info(...)     <- 던지지 않는다   :52-53     |
|     HSQL  jdbc:hsqldb:mem:<이름>                   (기본)  Hsql...:63         |
|     H2    jdbc:h2:mem:<이름>;DB_CLOSE_DELAY=-1;...         H2...:64           |
+------------------------------------------------------------------------------+
```

이 그림에서 읽어야 할 사실은 셋이다.\
첫째, **예외가 올라가는 길과 DB가 사라지는 길이 갈라진다.**\
cleaner 예외는 위로(어댑터로) 올라가고, DB 종료는 아래로(configurer로) 내려가야 한다.\
수정 전에는 예외가 위로 올라가는 순간 아래로 내려가는 길이 끊겼다.\
둘째, **위쪽 어댑터는 예외를 한 줄로 줄인다.**\
그래서 "끊긴 것"이 거의 보이지 않는다.\
셋째, **아래쪽 configurer는 실패를 던지지 않는다.**\
`SHUTDOWN`이 실패해도 info 로그뿐이라, finally에 넣은 shutdown이 cleaner 예외를 덮어쓸 가능성(TO-1)이 사실상 없다.

> **SHUTDOWN 문** — HSQL과 H2에서 DB를 닫고 인메모리 DB면 그 내용을 메모리에서 지우는 SQL 명령.\
> 예: `jdbc:hsqldb:mem:testdb`에 `SHUTDOWN`을 실행하면, 다음에 같은 URL로 접속할 때 빈 DB가 새로 만들어진다.

## 2. 한 컨텍스트의 일생 - 수정 전후

같은 JVM에서 컨텍스트 A가 닫히고 B가 뜨는 장면을 단계별로 추적한다.

```text
[수정 전]
  컨텍스트 A start
    initDatabase()      configurer 없음 -> HSQL                    :187-189
                        jdbc:hsqldb:mem:testdb 생성
    populator           CREATE TABLE T_TEST ...

  컨텍스트 A close
    DisposableBeanAdapter -> destroy()
      cleaner           drop table T_MISSING  -> ScriptStatementFailedException
      shutdownDatabase  (도달 못 함)
    DisposableBeanAdapter catch -> WARN 한 줄
    -> A 는 정상 종료처럼 보인다. testdb 는 메모리에 남아 있다

  컨텍스트 B start
    jdbc:hsqldb:mem:testdb 접속 -> A 의 DB 를 그대로 받음
    populator           CREATE TABLE T_TEST ... -> "already exists"

[수정 후]  같은 시나리오
  컨텍스트 A close
    destroy()
      try: cleaner      -> ScriptStatementFailedException (try 중단)
      finally:          shutdownDatabase() -> SHUTDOWN -> testdb 소멸
      그 뒤 같은 예외가 destroy() 밖으로
    DisposableBeanAdapter catch -> WARN 한 줄   (신호는 수정 전과 같다)

  컨텍스트 B start
    jdbc:hsqldb:mem:testdb 접속 -> 새 빈 DB
    populator           CREATE TABLE T_TEST ... -> 성공
```

**바뀌는 것은 A의 DB가 사라지느냐 하나다.**\
WARN 한 줄은 수정 전후 똑같이 남는다 - 예외를 잡지 않았으므로 어댑터에 그대로 도착하기 때문이다.

## 3. 세 가지 형태의 비교 - 예외와 정리의 행방

[README 4절](README.md)의 표를 실행 흐름으로 다시 그리면 이렇다.

```text
  수정 전                   catch 로 삼킴 (가상)        finally (수정)
  ------------------        --------------------        --------------------
  cleaner 예외              cleaner 예외                cleaner 예외
     |                         |                           |
     |                      catch 에서 소멸                finally: shutdown
     |                         |                           |
     |                      shutdown                       |
     v                         v                           v
  destroy 밖으로            정상 반환                    destroy 밖으로
     |                         |                           |
  어댑터 WARN               어댑터: 받을 것 없음         어댑터 WARN
  DB 잔존                   DB 종료, 신호 소실           DB 종료, 신호 유지
```

이 그림은 계획 게이트에서 사용자가 "내부 메서드에서 캐치로 이미 예외를 처리하면 외부에서는 캐치로 잡을 수가 없어서 이러한 문제가 생기는거거나"라고 물었을 때 메인이 표로 정리한 것과 같은 내용이다([gates.md](gates.md)).\
가운데 열이 "안에서 잡으면 밖에서는 못 본다"이고, 오른쪽 열만 두 목표를 동시에 만족한다.

## 4. 이름이 전이의 열쇠 - 기본값의 연쇄

A의 DB가 B에게 넘어가려면 두 컨텍스트가 같은 이름을 써야 한다.\
기본값이 그렇게 되어 있다.

| 설정 경로 | 이름 결정 | 근거 |
|---|---|---|
| 프로그래매틱 (`EmbeddedDatabaseFactory`) | `databaseName` 기본 `"testdb"`, `generateUniqueDatabaseName` 기본 false | EmbeddedDatabaseFactory.java:73, :77, :79 |
| XML `<jdbc:embedded-database>` | `database-name` -> 없으면 빈 `id` -> 둘 다 없으면 `testdb` | EmbeddedDatabaseBeanDefinitionParser.java:80-92 |
| 고유 이름을 켠 경우 | `initDatabase`가 UUID로 덮어씀 | EmbeddedDatabaseFactory.java:182-184 |

> **generateUniqueDatabaseName** — 켜면 `initDatabase` 때마다 DB 이름을 무작위 UUID로 바꿔, 같은 JVM의 컨텍스트끼리 DB를 공유하지 않게 하는 옵션. 기본 false.\
> 예: XML에서는 `generate-name="true"`로 켠다.

고유 이름을 켠 사용자는 B가 다른 DB를 받으므로 전이가 일어나지 않는다.\
다만 그 경우에도 A의 DB는 여전히 메모리에 남는다 - 누수는 그대로이고 증상만 숨는다.

PR 본문과 게이트 설명은 "기본 이름 `testdb`"로 요약했는데, XML 경로에서는 정확히는 빈 `id`가 이름이 된다.\
같은 설정 파일을 다시 띄우면 `id`도 같으므로 결론("같은 이름으로 재접속")은 바뀌지 않는다.

## 5. 기본 타입 - 근거 코드가 실행되는가

이 작업에서 바로잡힌 사실은 "어느 configurer가 기본으로 불리는가"였다.

```text
  initDatabase()
    if (this.databaseConfigurer == null)                       :187
        databaseConfigurer = getConfigurer(HSQL)               :188    <- 타입 미지정이면 여기
    configureConnectionProperties(...)

  HsqlEmbeddedDatabaseConfigurer   jdbc:hsqldb:mem:<이름>         :63    <- 기본 경로
  H2EmbeddedDatabaseConfigurer     ...;DB_CLOSE_DELAY=-1;...      :64    <- type="H2" 일 때만
```

착수 분석과 게이트 브리핑은 아래 줄(H2)을 근거로 들었고, 테스트는 위 줄(HSQL)로 돌았다.\
두 DB 모두 `SHUTDOWN` 전까지 인메모리 DB를 유지하므로 결함은 같지만, 근거 코드가 기본 경로에서 실행되지 않는다는 점을 리뷰(Opus OQ-1)가 찾았다.

## 6. 스프링 전역에서의 자리

`EmbeddedDatabaseFactoryBean`은 XML 네임스페이스 `<jdbc:embedded-database>`의 구현 빈이다.\
같은 기능의 자바 API인 `EmbeddedDatabaseBuilder`는 `EmbeddedDatabaseFactory`를 직접 쓰고 cleaner 개념이 없으므로 이 결함과 무관하다.

같은 모듈에서 cleaner를 실행하는 곳은 둘이다.

```text
  EmbeddedDatabaseFactoryBean.destroy()   cleaner + 임베디드 DB shutdown   <- 결함 (shutdown 이 건너뛰어짐)
  DataSourceInitializer.destroy()         cleaner 만 (외부 DB, 끌 것이 없음) <- 해당 없음
```

이 결함이 실제로 사용자에게 닿으려면 조건을 차례로 통과해야 한다.

```text
EmbeddedDatabaseFactoryBean 을 쓰나?          -- 아니오 -->  해당 없음
(XML <jdbc:embedded-database> 또는 직접 등록)
        |
       예
        v
cleaner 가 등록돼 있나?                       -- 아니오 -->  destroy 는 shutdown 만, 정상
(execution="DESTROY" 또는 setDatabaseCleaner)
        |
       예
        v
cleaner 가 실패하나?                          -- 아니오 -->  정상
(DROP 대상 없음, 스크립트 경로 깨짐 등)
        |
       예
        v
  발화 - shutdown 이 건너뛰어지고 DB 가 JVM 에 남는다
        |
        v
같은 JVM 에서 같은 이름으로 다시 뜨나?        -- 아니오 -->  메모리 누수만 (증상 없음)
        |
       예
        v
  전이 - 다음 컨텍스트가 이전 스키마를 보고, init 스크립트가 실패한다
```

## 출처

기준: 로컬 브랜치 `fix/embedded-database-destroy-shutdown`의 HEAD `23d42a988ae`(base upstream/main `49adc91c7e4`).\
**본문의 file:line은 수정 후 좌표다** - `destroy()`는 수정 전 L84-91(execute L88, shutdown L90), 수정 후 L84-95(execute L89, finally L92-94)다. 그 밖의 파일은 이 커밋에서 바뀌지 않았다.
