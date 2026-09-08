# 개념: 저장 프로시저란 무엇인가 — 반환 슬롯이 없고 결과가 전부 이름을 갖는 호출 대상

> J5(`CallMetaDataContext.reconcileParameters`의 반환 파라미터 처리 결함) 작업의 배경 개념
> 문서. 짝 문서: [저장 함수](../stored-function/stored-function.md).

## 한 줄 정의 — 결과를 파라미터로 돌려주는 서브프로그램

저장 프로시저는 DB 안에 이름을 갖고 저장된 서브프로그램이며, **호출식의 값이 되지
않는다**. `x := proc(...)`처럼 쓸 수 없고, 결과를 받는 정규 통로는 시그니처에 선언된
OUT/IN OUT 파라미터뿐이다. 그리고 파라미터에는 **반드시 이름이 있다** — 이 한 가지가
아래 모든 이야기의 뿌리다. 이름이 있으니 Spring은 사용자가 선언한 파라미터와 DB가 보고한
파라미터를 이름으로 짝지을 수 있다.

## DB별 시그니처 문법

확인할 것은 반환 절이 없다는 점과 각 파라미터가 이름과 방향을 함께 갖는다는 점이다.

```sql
-- Oracle
CREATE PROCEDURE add_invoice(amount IN NUMBER, custid IN NUMBER, newid OUT NUMBER) AS
BEGIN ... END;

-- SQL Server
CREATE PROCEDURE my_proc @amount INT, @out_total INT OUTPUT
AS BEGIN ... RETURN 0; END;   -- RETURN 0 은 값이 아니라 정수 상태 코드
```

어느 쪽에도 `RETURN <타입>` 절이 없다.

## JDBC 메타데이터에서 프로시저는 어떻게 보이는가

Spring이 읽는 것은 실행 결과가 아니라 `DatabaseMetaData.getProcedureColumns()`가 주는
**시그니처 설명서**다 — 파라미터당 한 행이고, 각 행은 이름(`COLUMN_NAME`), 방향
(`COLUMN_TYPE`), 타입을 담는다. 방향 상수는 `java.sql.DatabaseMetaData`의 procedure
계열이며, 이름이 비슷한 function 계열과 값이 다르다(그 함정은 짝 문서에서 다룬다).
procedure 계열의 방향 상수는 여섯 개다.

| 상수 | 값 | 의미 |
|---|---|---|
| `procedureColumnUnknown` | 0 | 방향 미상 |
| `procedureColumnIn` | 1 | 입력 |
| `procedureColumnInOut` | 2 | 입출력 |
| `procedureColumnResult` | 3 | 결과 컬럼 |
| `procedureColumnOut` | 4 | 출력 |
| `procedureColumnReturn` | 5 | 반환 슬롯 |

순수한 프로시저라면 5번 행이 아예 오지 않는다. 기존 테스트의 프로시저 목이 그 모습이다
(`SimpleJdbcCallTests.java:382-383`):

```java
given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn("amount", "custid", "newid");
given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(1, 1, 4);
```

세 행 모두 이름이 있고 방향은 IN·IN·OUT이며, 그래서 호출문은 `{call ADD_INVOICE(?, ?, ?)}`
— 앞에 `? =`가 붙지 않는다. 한편 실행 결과의 OUT 값은 이름으로 오지 않는다.
`JdbcTemplate.extractOutputParameters`는 `callParameters` 목록을 순회하며 위치 인덱스로
값을 꺼내고 **목록의 이름을 키로** 결과 맵에 넣는다(`JdbcTemplate.java:1316-1325`). 결과
이름의 정확성은 DB가 아니라 Spring이 만든 목록의 정확성이다.

## 예외 하나 — SQL Server 프로시저의 상태 코드 반환

프로시저에 반환 슬롯이 없다는 규칙에는 실무상의 예외가 있다. T-SQL 프로시저의 정수 상태
코드를 SQL Server JDBC 드라이버는 `COLUMN_TYPE=5`이면서 **이름이 있는** 의사 파라미터
`@RETURN_VALUE`로 보고한다(`SimpleJdbcCallTests.java:439-440`):

```java
given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn("@RETURN_VALUE", "@amount", "@out_total");
given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(5, 1, 4);
```

여기서 두 가지가 동시에 일어난다. 첫째, 반환 행에 **이름이 있다** — 함수 반환과 결정적으로
다른 점이다. 둘째, 그 이름에 `@` 접두가 붙어 있어 provider가 벗겨야 사용자 선언과 같은 표기가
된다(`SqlServerCallMetaDataProvider.java:44-55`의 `parameterNameToUse`). 대부분의 사용자는
상태 코드를 원하지 않으므로 기본값은 무시다 — provider가 `byPassReturnParameter("@RETURN_VALUE")`에
true를 돌려주고(`SqlServerCallMetaDataProvider.java:62-65`, Postgres는 `"returnValue"`),
컨텍스트가 그 신호로 반환 행을 건너뛴다. 다만 조건이 셋이라 프로시저이고, 반환값을 요구하지
않았고, 이름이 목록에 있을 때만이다(`CallMetaDataContext.java:404-405`). 상태 코드를 원한다고
선언하면 바이패스가 풀린다.

## Spring 진입 경로 — withProcedureName, 그리고 withReturnValue

프로시저 호출의 진입점은 `SimpleJdbcCall.withProcedureName()`이고, 이것이 하는 일은 이름
설정과 **함수 플래그 해제**다(`SimpleJdbcCall.java:86-91`). 상태 코드를 받고 싶으면
`withReturnValue()`를 덧붙이는데, 이것은 별개 플래그 `returnValueRequired`만 켠다
(`SimpleJdbcCall.java:112-116`). 두 플래그는 호출문 조립에서 합류해
`isFunction() || isReturnValueRequired()`이면 `{? = call `로 시작하고 슬롯 카운터를 -1로
두어 첫 자리를 반환에 내준다(`CallMetaDataContext.java:630-636`). 즉
`withProcedureName().withReturnValue()`는 함수가 아니면서도 `{? = call ...}` 형태를 쓴다.
**프로시저이면서 반환 슬롯을 가진 상태** — J5 결함의 한쪽 갈래가 여기서 열린다.

## 함수와의 차이

두 개념을 가르는 축은 반환 슬롯의 유무, 그 슬롯의 이름 유무, 그리고 Spring 진입점이다.

| 축 | 저장 프로시저 | 저장 함수 |
|---|---|---|
| 시그니처 반환 절 | 없음 | `RETURN <타입>` 있음 |
| 결과를 받는 통로 | 이름 있는 OUT/IN OUT 파라미터 | 이름 없는 반환 슬롯(+ 필요하면 OUT) |
| 메타데이터 반환 행 | 원칙적으로 없음. SQL Server만 `@RETURN_VALUE`로 이름 있게 보고 | 있음. Oracle은 `COLUMN_NAME=null`로 보고 |
| Spring 진입점 | `withProcedureName()` (+ 상태 코드는 `withReturnValue()`) | `withFunctionName()` |
| 호출문 | `{call p(?, ?)}` (반환값 요구 시 `{? = call ...}`) | `{? = call f(?)}` |
| 반환값 조회 키 | `getOutParameterNames().get(0)` | `getFunctionReturnName()` |

## J5 결함에서 프로시저 쪽이 만드는 갈림 — 스퓨리어스 예외

프로시저 경로가 결함에 걸리는 조건은 좁다. `withReturnValue()`를 켜서 `@RETURN_VALUE` 행이
바이패스되지 않고, 그 행에 대응하는 OUT 파라미터를 선언하되 **다른 OUT 파라미터를 그보다
먼저 선언했을 때**다. 결함의 자리는 반환 분기 두 줄이다(`CallMetaDataContext.java:374-384`):

```java
if (declaredParams.containsKey(paramNameToCheck) || (meta.isReturnParameter() && returnDeclared)) {
    SqlParameter param;
    if (meta.isReturnParameter()) {
        param = declaredParams.get(getFunctionReturnName());
        if (param == null && !getOutParameterNames().isEmpty()) {
            param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
        }
        if (param == null) {
            throw new InvalidDataAccessApiUsageException(...);   // "Unable to locate declared parameter"
```

`declaredParams`의 키는 `lowerCase(provider.parameterNameToUse(name))`로 정규화돼 있는데
(`CallMetaDataContext.java:339`) 반환 분기만 그 정규화를 쓰지 않는다. 재현 테스트
`sqlServerProcedureWithReturnValueDeclaredAfterOutParameter`(`SimpleJdbcCallTests.java:300-310`)에
대입하면, 선언은 `@out_total`·`RETURN_VALUE` 순서이고 맵 키는 `out_total`·`return_value`다.
바깥 조건의 `paramNameToCheck`(= `return_value`)는 이미 **매치에 성공**한다. 그런데 안쪽 첫
줄은 `getFunctionReturnName()`(프로시저라 기본값 `"return"`)으로 조회해 miss하고, 폴백 줄은
첫 OUT의 원표기 `"@out_total"`을 소문자화만 해서 조회한다 — `@`를 벗기지 않았으니 키
`out_total`과 어긋나 또 miss. 결과는 **올바른 선언인데 예외**다.

여기서 프로시저의 성질이 어떻게 작동했는지가 요점이다. 반환 행에 **이름이 있었기 때문에**
바깥 조건은 통과했고, 그래서 실패가 "못 찾음"이 아니라 "찾아놓고 다시 잃어버림"이 됐다.
그리고 `@` 접두라는 SQL Server 고유 표기 규칙이 `parameterNameToUse`에 캡슐화돼 있는데
폴백 줄이 `toLowerCase`만 직접 불러 그 캡슐화를 우회한 것이 직접 원인이다. 같은 선언을
순서만 뒤집으면(`SimpleJdbcCallTests.java:313-323`) 폴백이 우연히 `return_value`를 조회해
통과한다 — 문서화된 적 없는 **선언 순서 의존**이다.

함수 쪽 갈래는 증상이 정반대로 조용하다. 왜 그런지는 [저장 함수](../stored-function/stored-function.md)에서
이어진다.

## 정리

프로시저 쪽에서 기억할 것은 정의적 성질 하나와 그 예외, 그리고 J5 증상이다.

- 정의적 성질은 반환 슬롯 없음이고, 그 따름결과가 **모든 결과에 이름이 있다**는 것이다.
- 실무의 예외는 SQL Server의 정수 상태 코드 — 프로시저인데 반환 행이 있고, 그 행에도 이름이
  있다. 기본은 바이패스, `withReturnValue()`로 살린다.
- J5 증상은 **스퓨리어스 예외**다. 반환 행에 이름이 있어 매치는 되지만, 반환 분기가 provider
  정규화를 건너뛴 조회를 다시 해서 그 매치를 잃는다.

## 관련

- [저장 함수](../stored-function/stored-function.md) — 이름 없는 반환 슬롯과 조용한 오답 갈래
- `../../prs/37206-callmetadata-return-lookup/analysis.md` — 결함 전수 추적(정본)
