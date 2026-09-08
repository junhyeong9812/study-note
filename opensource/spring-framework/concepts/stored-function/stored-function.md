# 개념: 저장 함수란 무엇인가 — 이름 없는 반환 슬롯을 가진 호출 대상

> J5(`CallMetaDataContext.reconcileParameters`의 반환 파라미터 처리 결함) 작업의 배경 개념
> 문서. 짝 문서: [저장 프로시저](../stored-procedure/stored-procedure.md).

## 한 줄 정의 — 호출식이 값이 되는 서브프로그램

저장 함수는 DB 안에 저장된 서브프로그램이되 **호출식 자체가 값을 갖는다**. `x := f(a)`나
`SELECT f(a) FROM dual`처럼 쓸 수 있고, 그 값이 나오는 자리가 시그니처의 `RETURN` 절이다.
결정적인 것은 **그 반환 슬롯에 이름이 없다**는 점 — 파라미터는 `a IN NUMBER`처럼 이름과
방향을 갖지만 반환 슬롯은 타입만 갖는다. 이름 없음이라는 성질 하나가, 이름으로 짝을 짓는
Spring의 매칭 구조와 마찰을 일으키는 모든 지점의 출발점이다.

## DB별 시그니처 문법

볼 것은 파라미터 목록 뒤에 붙은 `RETURN <타입>`이 이름을 갖지 않는다는 점이다.

```sql
-- Oracle
CREATE FUNCTION get_total(amount IN NUMBER, out_status OUT NUMBER) RETURN NUMBER AS
BEGIN ... RETURN 42; END;

-- SQL Server (스칼라 함수)
CREATE FUNCTION dbo.get_total(@amount INT) RETURNS INT AS BEGIN ... RETURN 42; END;
```

Oracle 예에서 보듯 함수도 OUT 파라미터를 함께 가질 수 있다 — **반환 슬롯과 OUT 파라미터가
공존하는 이 형태**가 J5 결함이 발동하는 무대다.

## JDBC 메타데이터에서 함수는 어떻게 보이는가

Spring이 읽는 것은 실행 결과가 아니라 시그니처 설명서다 — 파라미터당 한 행에 이름
(`COLUMN_NAME`), 방향(`COLUMN_TYPE`), 타입이 담긴다. 함수의 반환 행에서 이 설명서가 하는 말은
"방향은 반환, 이름은 없음"이고, Oracle 드라이버는 그것을 `COLUMN_TYPE=5`, `COLUMN_NAME=null`로
보고한다. 테스트 목이 그렇게 모사한다(`SimpleJdbcCallTests.java:420-421`, 헬퍼
`initializeGetTotalFunctionWithMetaData`):

```java
given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn(null, "amount", "out_status");
given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(5, 1, 4);
```

첫 행이 무명 반환이다. 같은 패턴은 더 오래된 헬퍼 `initializeAddInvoiceWithMetaData`의 함수
분기에도 있다(`SimpleJdbcCallTests.java:376-377`의 `willReturn(null, "amount", "custid")`) —
이 코드베이스가 오래전부터 모델링해 온 사실이다. 그 행이 버려지지 않는 이유도 코드에 있다 —
`GenericCallMetaDataProvider`는 이름이 null인 행을 스킵하되 **방향이 IN/OUT/INOUT일 때만**
스킵하므로(:368의 `columnName == null && isInOrOutColumn(...)`, `isInOrOutColumn`은 :443-454),
무명 반환 행은 그물을 통과해 살아남고 무명 IN 행(컬렉션 멤버 등)만 걸러진다.

함정 하나. `java.sql.DatabaseMetaData`의 방향 상수는 procedure 계열과 function 계열이 **따로
있고 값이 어긋난다** — 같은 숫자가 계열에 따라 다른 뜻이다.

| 숫자 | procedure 계열 | function 계열 |
|---|---|---|
| 3 | `procedureColumnResult` | `functionColumnOut` |
| 4 | `procedureColumnOut` | `functionReturn` |
| 5 | `procedureColumnReturn` | `functionColumnResult` |

1·2(IN·INOUT)만 일치하고 3·4·5가 어긋난다. 이 어긋남 때문에 `CallParameterMetaData`는 자신이 어느 계열에서 왔는지를 `function`
플래그로 들고 다니며 판정을 갈라 쓴다 — `isReturnParameter()`는 플래그가 true면
`functionReturn`(4)을, false면 `procedureColumnReturn`(5) 또는 `procedureColumnResult`(3)를
본다(`CallParameterMetaData.java:91-95`). 이 플래그는 `withFunctionName()` 여부가 아니라 **메타데이터를 어느 API로 읽었는지**에서 온다.
`getProcedures()`가 hit하면 `getProcedureColumns()`로 읽고 플래그는 false이며(Oracle의 통상
경로 — 위 테스트 목이 그렇다), hit이 0이면 `getFunctions()`/`getFunctionColumns()`로 폴백하며
플래그가 true다(`GenericCallMetaDataProvider.java:312-316`, :404-432 — PostgreSQL 드라이버
42.2.11 이후 함수가 프로시저로 노출되지 않게 되면서 생긴 경로). 즉 "함수인가"에는 서로 다른
두 답이 있다 — 사용자가 선언한 호출 종류(`CallMetaDataContext.isFunction()`)와 메타데이터
출처(`CallParameterMetaData.isFunction()`).

## Spring 진입 경로 — withFunctionName과 이름 없는 반환값에 이름 붙이기

함수 호출의 진입점은 `withFunctionName()`이고, 하는 일은 이름 설정과 함수 플래그 세팅이다
(`SimpleJdbcCall.java:93-98`). 그 플래그가 호출문을 `{? = call ...}`로 만들어 첫 자리를 반환에
내준다(`CallMetaDataContext.java:630-633`).

문제는 결과를 돌려줄 때다. 실행 결과의 OUT 값은 `CallableStatement.getObject(index)`로
**위치 기반**으로만 오고 이름은 Spring이 `callParameters` 목록의 이름으로 붙이는데
(`JdbcTemplate.java:1316-1325`), 함수 반환에는 DB가 준 이름이 없다. 그래서 Spring이 이름을
**스스로 정한다** — `getFunctionReturnName()`은 `actualFunctionReturnName`이 있으면 그것,
없으면 기본값 `"return"`이다(`CallMetaDataContext.java:107-109`). 그 필드를 채우는 경로는
셋으로, 사용자의 `setFunctionReturnName()`, reconcile 1단계 휴리스틱, 3단계 반환 행 처리의
덮어쓰기다. 휴리스틱은 "**메타데이터에 없는 첫 OUT 선언이 함수 반환**"이라는 규칙이다
(`CallMetaDataContext.java:343-350`):

```java
if (isFunction() && !metaDataParamNames.contains(paramNameToMatch) && !returnDeclared) {
    ...
    this.actualFunctionReturnName = paramName;
    returnDeclared = true;
}
```

읽어볼 만한 추론이다 — 함수의 OUT 선언 중 실제 컬럼 목록에 없는 것이 있다면 그것은 이름 없는
반환 슬롯을 가리키려는 선언일 수밖에 없다. 실행 시 `executeFunction()`은 이 이름으로 결과 맵을
조회한다(`getScalarOutParameterName()`이 함수일 때 `getFunctionReturnName()`을 돌려주므로 —
`CallMetaDataContext.java:280-283`, `SimpleJdbcCall.java:154-156`).

## 프로시저와의 차이

가르는 축은 반환 슬롯의 유무, 그 슬롯의 이름 유무, Spring 진입점이다.

| 축 | 저장 함수 | 저장 프로시저 |
|---|---|---|
| 시그니처 반환 절 | `RETURN <타입>` 있음 | 없음 |
| 반환 슬롯의 이름 | 없음 — Spring이 지어낸다(`"return"` 또는 선언 OUT 이름) | (해당 없음) SQL Server 상태 코드만 `@RETURN_VALUE` |
| 메타데이터 반환 행 | `COLUMN_TYPE=5`, `COLUMN_NAME=null`(Oracle) | 원칙적으로 없음 |
| Spring 진입점 | `withFunctionName()` | `withProcedureName()` (+ `withReturnValue()`) |
| 반환값 조회 키 | `getFunctionReturnName()` | `getOutParameterNames().get(0)` |
| J5 증상 | 조용한 오답 | 스퓨리어스 예외 |

## J5 결함에서 함수 쪽이 만드는 갈림 — 조용한 오답

함수 경로가 결함에 걸리는 조건은 **반환용 OUT 파라미터보다 다른 OUT 파라미터를 먼저 선언할
때**다. 결함의 자리는 반환 분기 두 줄이다(`CallMetaDataContext.java:377-379`):

```java
param = declaredParams.get(getFunctionReturnName());
if (param == null && !getOutParameterNames().isEmpty()) {
    param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
}
```

`declaredParams`의 키는 `lowerCase(provider.parameterNameToUse(name))`로 정규화돼 있는데
(`CallMetaDataContext.java:339`) 이 두 줄만 그 정규화를 쓰지 않는다. 재현 테스트
`functionWithAdditionalOutParameterDeclaredBeforeReturn`(`SimpleJdbcCallTests.java:270-283`)의
선언은 `out_status`, `RESULT` 순서다. 1단계에서 `out_status`는 메타 컬럼에 있으니 반환 후보가
아니고 `RESULT`가 휴리스틱에 걸려 `actualFunctionReturnName = "RESULT"`가 된다. 3단계 반환
행에서 첫 줄이 원표기 `"RESULT"`로 조회하는데 맵 키는 `"result"`라 miss하고, 폴백 줄이 첫 OUT
`"out_status"`를 집어 **hit해 버린다**. 반환 슬롯을 `out_status`가 차지하고
`actualFunctionReturnName`도 `"out_status"`로 덮인다.

증상이 조용한 이유가 여기 있다. 슬롯 개수는 그대로라 SQL은 `{? = call GET_TOTAL(?, ?)}`로 정상
생성되고 실행도 성공한다. 다만 `out_status`라는 같은 이름이 목록에 두 번 들어가 결과 맵에서
뒤의 값이 앞을 덮고, `executeFunction()`은 그 이름으로 조회하므로 **반환값 대신 OUT 값**을
받는다. 선언한 `RESULT`는 타입 정보까지 사라지는데 예외도 경고도 없다.

두 갈래를 묶는 문장은 이렇다. **반환 슬롯에 이름이 없다는 함수의 성질 때문에 Spring은 이름을
지어내야 했고, 지어낸 이름을 조회하는 그 한 줄이 나머지 코드가 지키는 정규화 규약을 빠뜨렸다.**
같은 줄이 프로시저 쪽에서 예외가 되는 것은 반환 행에 이름이 있어 바깥 매치가 먼저 성공하기
때문이고([저장 프로시저](../stored-procedure/stored-procedure.md)에 추적), 함수 쪽에서 조용한 오답이 되는 것은
폴백이 "첫 OUT"이라는 순서 휴리스틱에 기대기 때문이다. 둘 다 선언 순서를 뒤집으면 우연히 정상
동작하며, 그 순서 요구는 어디에도 문서화돼 있지 않다.

## 정리

함수 쪽에서 기억할 것은 이름 없는 반환 슬롯이 만드는 네 가지 따름결과다.

- 정의적 성질은 **이름 없는 반환 슬롯**이다. 파라미터에는 이름이 있고 반환에는 없다.
- 이름이 없으니 Spring이 이름을 만든다 — 기본값 `"return"`, 또는 "메타데이터에 없는 첫 OUT
  선언"이라는 휴리스틱이 정한 이름.
- 방향 상수는 두 계열의 값이 어긋나고, 어느 계열로 읽을지는 `getProcedures()` hit 여부가 정한다
  (`CallParameterMetaData.isFunction()`은 출처 플래그이지 `withFunctionName()` 여부가 아니다).
- J5 증상은 **조용한 오답**이다. 슬롯 수가 맞아 SQL은 성공하고, 결과 맵에서 같은 이름이 덮이며
  틀린 값이 예외 없이 돌아온다.

## 관련

- [저장 프로시저](../stored-procedure/stored-procedure.md) — 이름 있는 결과와 스퓨리어스 예외 갈래
- `../../prs/37206-callmetadata-return-lookup/analysis.md` — 결함 전수 추적(정본)
