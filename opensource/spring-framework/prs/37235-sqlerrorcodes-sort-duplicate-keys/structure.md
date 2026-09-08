# PR #37235 - 무대의 실구조와 워크플로우

> PR #37235의 무대가 되는 실구조와 워크플로우. 문제와 수정은 [README.md](README.md),
> 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: 로컬 HEAD `e0704925b9a`(브랜치 `fix/sqlerrorcodes-sort-duplicate-key-codes` =
> upstream main `136dddb67d1` 리베이스 + fix 커밋). **이 시점의 `SQLErrorCodes.java`에는
> 이미 수정이 반영돼 있다** - 아래 file:line은 "수정 후" 좌표이고, 2절의 수정 전
> 동작은 커밋의 `-`쪽으로 재구성한 것이다.

## 1. 무대 - 실구조

이 결함의 무대는 **JDBC 벤더 에러코드를 Spring의 `DataAccessException` 계층으로
번역하는 파이프라인**이고, 그 파이프라인의 데이터 원장이 `SQLErrorCodes`라는
JavaBean 하나다. 이 빈은 벤더별 코드 목록 열한 종을 배열로 들고 있을 뿐이지만,
그 배열을 **어떤 순서로 저장하느냐**가 소비자의 조회 알고리즘과 맞물려 있다.
계층을 위에서 아래로 그리면 이렇다.

```
+------------------------------------------------------------------------------+
| 설정 소스                                                                      |
|   spring-jdbc.jar 안의 기본값                                                  |
|     org/springframework/jdbc/support/sql-error-codes.xml                      |
|     SQLErrorCodesFactory.SQL_ERROR_CODE_DEFAULT_PATH            Factory:64    |
|   클래스패스 루트의 사용자 오버라이드                                            |
|     /sql-error-codes.xml                                                      |
|     SQLErrorCodesFactory.SQL_ERROR_CODE_OVERRIDE_PATH           Factory:59    |
|   또는 코드로 직접 new SQLErrorCodes() + setter 호출                            |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| SQLErrorCodesFactory (싱글턴)          jdbc/support/SQLErrorCodesFactory.java  |
|   getInstance()                                                    :80-86    |
|   생성자: DefaultListableBeanFactory + XmlBeanDefinitionReader     :108-145   |
|     bdr.loadBeanDefinitions(기본 XML)                              :118-120   |
|     bdr.loadBeanDefinitions(오버라이드 XML)  <- 있으면 기본값을 덮어씀  :127-131   |
|     errorCodesMap = lbf.getBeansOfType(SQLErrorCodes.class, ...)   :134      |
|   getErrorCodes(String dbName) / getErrorCodes(DataSource)        :171, :208 |
|                                                                              |
|   ** XML의 <property name="duplicateKeyCodes"><value>1062</value> 는          |
|      빈 프로퍼티 주입이므로 반드시 setter 를 통과한다 **                          |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| SQLErrorCodes (이번 무대)                jdbc/support/SQLErrorCodes.java       |
|                                                                              |
|  [상태] 코드 배열 필드 열 개 - 전부 String[], 기본값 new String[0]     :43-61   |
|    badSqlGrammarCodes / invalidResultSetAccessCodes /                        |
|    duplicateKeyCodes / dataIntegrityViolationCodes /                         |
|    permissionDeniedCodes / dataAccessResourceFailureCodes /                  |
|    transientDataAccessResourceCodes / cannotAcquireLockCodes /               |
|    deadlockLoserCodes / cannotSerializeTransactionCodes                      |
|    + customTranslations / customSqlExceptionTranslator            :63-65     |
|                                                                              |
|  [setter 관례] 열 개 모두 같은 한 줄                                            |
|    this.xxxCodes = StringUtils.sortStringArray(xxxCodes);                    |
|    L106 / L114 / L126 / L130 / L138 / L146 / L154 / L162 / L170 / L178       |
|            ^^^^ L126 이 이번 수정으로 관례에 합류한 자리                          |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| StringUtils.sortStringArray            spring-core util/StringUtils.java     |
|   ObjectUtils.isEmpty(array) 면 그대로 반환                          :1067-1069|
|   Arrays.sort(array); return array;   <- 제자리 정렬, 복사본 아님      :1071-1072|
|   => 사전식(String 자연 순서) 정렬. 저장측 불변식을 확립한다.                     |
+------------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------------+
| SQLErrorCodeSQLExceptionTranslator                                           |
|                          jdbc/support/SQLErrorCodeSQLExceptionTranslator.java|
|   doTranslate(task, sql, ex)                                        :183     |
|     errorCode = Integer.toString(현재 예외의 getErrorCode())         :217-224 |
|       (useSqlStateForTranslation 이면 getSQLState())                :213-215 |
|     커스텀 번역 먼저: binarySearch(customTranslation.getErrorCodes()) :231     |
|     그룹 코드 아홉 종을 순서대로 binarySearch                          :242-281 |
|       ...getDuplicateKeyCodes() 조회 -> DuplicateKeyException        :250-253 |
|     하나도 못 맞히면 return null (폴백에 넘김)                          :297    |
+------------------------------------------------------------------------------+
```

이 그림에서 읽어야 할 사실은 하나다. **저장은 setter 열 개가, 조회는
`Arrays.binarySearch` 열 곳이 담당하고, 둘 사이의 유일한 약속이 "배열은 사전식으로
정렬돼 있다"는 것이다.** 그 약속을 코드로 강제하는 장치는 어디에도 없다 -
setter가 스스로 지키는 관례일 뿐이고, 관례를 어긴 setter가 하나 있으면 그 배열만
조용히 어긋난다.

`SQLErrorCodes`를 소비하는 곳은 `SQLErrorCodeSQLExceptionTranslator` 하나뿐이다.
`getDuplicateKeyCodes()`의 호출처는 번역기 L250의 `binarySearch` 인자 자리가
유일하고(프로덕션 코드 기준), 그래서 "정렬 저장"이라는 불변식의 수혜자도 정확히
그 한 줄이다.

## 2. 수정 전 동작 워크플로우

설정이 한 번 로드되면 코드 배열은 그대로 굳고, 이후 모든 예외 번역은 그 배열을
읽기만 한다. 두 단계로 나눠 본다.

```
[설정 로드 - 애플리케이션당 한 번]
JdbcTemplate.setDataSource(ds)  ->  SQLErrorCodeSQLExceptionTranslator(ds)
  |
  +- SQLErrorCodesFactory.getInstance().getErrorCodes(dataSource)   Factory:208
       |
       +- 기본 sql-error-codes.xml 로드 -> 벤더 빈 11개                Factory:118
       +- 클래스패스 루트에 사용자 sql-error-codes.xml 이 있으면 덮어씀    Factory:127
       +- 각 빈은 XmlBeanDefinitionReader 가 setter 로 주입
            <property name="duplicateKeyCodes"><value>2601,2627</value></property>
              -> setDuplicateKeyCodes("2601", "2627")
                   [수정 전] this.duplicateKeyCodes = duplicateKeyCodes;   <- 입력 순서 그대로
                   [수정 후] this.duplicateKeyCodes = sortStringArray(...); <- 사전식 정렬

[예외 번역 - 예외 한 건마다]
JdbcTemplate ... catch (SQLException ex)
  -> translateException(task, sql, ex)                       JdbcTemplate:1548
       |
       +- getExceptionTranslator().translate(task, sql, ex)
       |    AbstractFallbackSQLExceptionTranslator.translate            :90-115
       |      customTranslator 있으면 먼저                                :93-99
       |      doTranslate(...)  <- SQLErrorCode 번역기 본체                :102
       |      null 이면 fallback.translate(...)                          :108-112
       |
       +- 결과가 null 이면 new UncategorizedSQLException(...)  JdbcTemplate:1550
```

수정 전의 결함은 이 그림의 첫 단계(setter 한 줄) 안에서만 일어나지만, 증상은 둘째
단계에서 관측된다. 미정렬 `["90002", "1586", "1062"]`를 이 워크플로우에 얹으면
이렇게 전파된다.

```
setDuplicateKeyCodes("90002", "1586", "1062")
   |
   +- 저장 배열 ["90002", "1586", "1062"]     <- 사전식 순서가 아니다
   |
   +- 에러코드 90002 발생
        Arrays.binarySearch(["90002","1586","1062"], "90002")
          mid=1 "1586" < "90002" -> low=2
          mid=2 "1062" < "90002" -> low=3 > high=2
          => -4 (miss)                        <- 배열 0번에 정답이 있는데도 못 찾는다
   |
   +- 나머지 여덟 그룹도 전부 miss -> doTranslate 가 null 반환         Translator:297
   |
   +- 폴백 1: SQLExceptionSubclassTranslator - 순수 SQLException 이라 무매치
   +- 폴백 2: SQLStateSQLExceptionTranslator - SQLState 값에 따라 갈림
   |
   +- 최종 결과가 SQLState 에 따라 세 갈래로 흩어진다 (3절)
```

## 3. 세 단 폴백 체인 - 미스가 어디로 흘러가나

`getDuplicateKeyCodes()`의 `binarySearch`가 빗나가도 예외가 나지는 않는다. 번역기가
`null`을 돌려주면 상위 골격이 다음 번역기에게 넘기고, 그 연쇄의 끝에서야 결과가
정해진다. 그래서 이 결함의 증상이 **하나가 아니라 여럿**이다.

```
                    binarySearch(getDuplicateKeyCodes(), "90002")
                                     |
                +--------------------+--------------------+
              hit (>=0)                                 miss (<0)
                |                                          |
    DuplicateKeyException                    나머지 그룹 여덟 종도 전부 miss
    (Translator:250-253)                                   |
                                              doTranslate -> null   (:297)
                                                           |
                                    AbstractFallback:108 fallback.translate(...)
                                                           |
                                     SQLExceptionSubclassTranslator.doTranslate  (:75)
                                       예외가 SQLTransientException /
                                       SQLNonTransientException /
                                       SQLRecoverableException 중 하나인가?
                                                           |
                                          +----------------+----------------+
                                        예    (드라이버가 JDBC4 서브클래스를 던짐)  아니오 (순수 SQLException)
                                          |                                  |
                            SQLIntegrityConstraintViolationException 이면      |
                            indicatesDuplicateKey 로 DuplicateKey (:102-106)  |
                                                                             v
                                                    SQLStateSQLExceptionTranslator.doTranslate (:107)
                                                      sqlState 이 null 이거나 length < 2 이면 통과 (:128)
                                                                             |
                                          +----------------+-----------------+------------------+
                                    sqlState "23505"        sqlState "23000"           그 외/없음
                                          |                        |                        |
                                  DuplicateKeyException     DUPLICATE_KEY_ERROR_CODES        |
                                     (:137-139)             에 벤더 코드가 있나? (:96-104)     |
                                                                   |                        |
                                                        +----------+----------+             |
                                                      있음                   없음             |
                                                        |                     |             |
                                              DuplicateKeyException  DataIntegrityViolation  |
                                                  (:138)                  (:140)            |
                                                                                            v
                                                                              return null (:166)
                                                                                            |
                                                                    JdbcTemplate:1550
                                                                    UncategorizedSQLException
```

이 분기도가 이 결함의 **관측 난이도**를 설명한다. 미정렬 배열에서 코드 하나가
빗나가도 사용자는 "예외가 안 났다"를 보지 않는다. 여전히 `DataAccessException`이
날아오고, 다만 그 타입이 `DuplicateKeyException`이 아닐 뿐이다. 그리고 어떤 타입이
되는지는 드라이버가 채운 SQLState에 달려 있어서, 같은 설정에서도 DB와 상황에 따라
달라진다.

폴백이 결함을 **가려 주는** 경우도 있다. `SQLStateSQLExceptionTranslator`의
`DUPLICATE_KEY_ERROR_CODES`는 well-known 벤더 코드 일곱 종을 갖고 있다.

```java
private static final Set<Integer> DUPLICATE_KEY_ERROR_CODES = Set.of(
		1,     // Oracle
		301,   // SAP HANA
		1062,  // MySQL/MariaDB
		2601,  // MS SQL Server
		2627,  // MS SQL Server
		-239,  // Informix
		-268   // Informix
	);
```
(SQLStateSQLExceptionTranslator.java:96-104)

이 일곱 코드는 SQLState가 `23000`이기만 하면 폴백이 결국 `DuplicateKeyException`을
만들어 준다(:137-139, :197-200). 즉 **가장 흔한 코드들이 결함을 덮는다**. 그래서
결함이 드러나는 자리는 well-known 목록 밖의 코드 - 사용자가 커스텀 XML이나 코드로
직접 넣은 애플리케이션 정의 코드 쪽이다.

## 4. 두 개의 순서 - 사전식과 숫자식

이 결함을 만드는 인지적 함정은 하나다. **사람은 에러코드를 숫자로 읽고, 배열은
문자열로 정렬된다.** 고정 축으로 비교하면 이렇다.

| 목록 | 숫자로 정렬돼 있나 | 사전식으로 정렬돼 있나 | binarySearch 결과 |
|---|---|---|---|
| `["1062", "1586", "90002"]` | 예 | 예 | 세 코드 전부 hit |
| `["90002", "1586", "1062"]` | 아니오 | 아니오 | 90002 miss, 1586 hit(우연), 1062 miss |
| `["-239", "-268", "-6017"]` (Informix 기본값) | 아니오 (-6017 < -268 < -239) | 예 | 전부 hit |
| `["900", "17006", "6550"]` (Oracle badSqlGrammarCodes XML 원문 `900,903,904,917,936,942,17006,6550`에서 발췌) | 아니오 | 아니오 -> **setter가 정렬** | 전부 hit |

마지막 두 행이 요점이다. 배포 XML은 사람이 읽기 좋은 순서(벤더 문서 순서, 숫자
순서)로 적혀 있고 사전식 정렬이 아닌 경우가 흔하다. 그래도 동작하는 이유는 setter가
정렬하기 때문이다. `duplicateKeyCodes`만 그 보호를 받지 못했는데, 하필 그 항목의
배포 XML 값 열한 개가 전부 우연히 사전식 정렬 상태였다(2절의 `2601,2627` /
`23001,23505` / `-239,-268,-6017` 등). 그래서 기본 구성에서는 아무 증상이 없었다.

## 5. 스프링 전역에서의 자리

`SQLErrorCodes`는 spring-jdbc의 **예외 번역(exception translation) 계층에서 "벤더
방언을 Spring 계층으로 사상하는" 데이터 원장**이다. 같은 계층에 번역 전략이 셋
있고, 셋의 차이는 정확히 "무엇을 근거로 판단하는가"다.

```
[벤더 코드 기반]  SQLErrorCodeSQLExceptionTranslator
                    근거 = SQLException.getErrorCode() (벤더 고유 정수)
                    데이터 = SQLErrorCodes (sql-error-codes.xml)
                    가장 정밀하지만 벤더별 설정이 필요하다.  <- 이 PR의 무대

[JDBC4 서브클래스 기반]  SQLExceptionSubclassTranslator
                    근거 = 예외의 자바 타입 (SQLTransientException 등)
                    드라이버가 JDBC 4 서브클래스를 제대로 던질 때만 동작.

[SQLState 기반]  SQLStateSQLExceptionTranslator
                    근거 = SQLException.getSQLState() 의 앞 두 글자(class code)
                    표준이라 이식성은 높지만 해상도가 낮다(23xxx = 무결성 위반).
```

세 전략은 경쟁 관계가 아니라 **폴백 사슬**이다(3절). 코드 기반이 가장 앞에 서고,
못 맞히면 서브클래스 기반, 그다음 SQLState 기반으로 내려간다. 이 배치가 곧 이
결함의 성격을 정한다 - 맨 앞 단계가 조용히 빗나가도 사슬이 끊기지 않으므로,
사용자는 예외를 받긴 받는다. 다만 **덜 정밀한 예외**를 받는다.

영향권은 `duplicateKeyCodes`를 **직접 구성한** 사용자다. 배포 기본값을 쓰는 한
증상이 없고(4절), 클래스패스 루트에 `/sql-error-codes.xml`을 두어 벤더 빈을
오버라이드했거나 `new SQLErrorCodes()`에 코드로 주입한 경우에만 발화한다. 그중에서도
목록이 두 개 이상이고 사전식 미정렬인 경우다.

## 6. 관련 개념

이 무대를 이해하는 데 필요한 배경은 이미 문서화돼 있으므로 링크로 연결한다.

- [Java varargs 실체](../../concepts/java-varargs-mechanics/java-varargs-mechanics.md) - `String...`이
  바이트코드에서 무엇인지, 값 나열 호출과 배열 전달 호출이 왜 갈리는지. 이 setter가
  받는 배열의 **주인이 누구인가**와, `sortStringArray`의 제자리 정렬이 호출자에게
  보이는 조건이 여기서 나온다. 이 PR의 이해 게이트에서 파생된 문서다.
