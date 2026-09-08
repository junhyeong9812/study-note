# PR #37206 — 테스트 해설 (테스트 하나하나)

> `SimpleJdbcCallTests`에 추가된 4건 + 목 헬퍼 2개. 각 테스트를 "무엇을 주장하나 /
> 왜 red 또는 가드인가 / 단언 하나하나의 의미"로 해설한다. red와 가드의 역할 분담
> 개념은 [../37153/guard-tests.md](../37153-enum-array-annotation-probe/guard-tests.md), 형식 원본은
> [../37153/tests.md](../37153-enum-array-annotation-probe/tests.md).

배치 전체를 먼저 본다. 이 결함은 **선언 순서 의존**이므로, 재현과 가드가 정확히
"같은 선언을 순서만 바꾼 쌍"으로 짝지어진다. 그래야 fix가 "순서를 무의미하게
만들었다"를 증명한다.

| 무대 | 반환 파라미터를 뒤에 선언 | 반환 파라미터를 먼저 선언 |
|---|---|---|
| Oracle 함수 + 추가 OUT (변형 A) | T1 `functionWithAdditionalOutParameterDeclaredBeforeReturn` — **red** | T2 `functionWithAdditionalOutParameterDeclaredAfterReturn` — 가드 |
| SQL Server 프로시저 + `withReturnValue()` (변형 B) | T3 `sqlServerProcedureWithReturnValueDeclaredAfterOutParameter` — **red** | T4 `sqlServerProcedureWithReturnValueDeclaredFirst` — 가드 |

## T1. 변형 A 재현 — red

첫 테스트는 Oracle 함수에서 반환 파라미터를 두 번째로 선언한 경우를 세운다.

```java
@Test
void functionWithAdditionalOutParameterDeclaredBeforeReturn() throws Exception {
	initializeGetTotalFunctionWithMetaData();
	SimpleJdbcCall function = new SimpleJdbcCall(dataSource).withFunctionName("get_total");
	function.declareParameters(
			new SqlOutParameter("out_status", Types.INTEGER),
			new SqlOutParameter("RESULT", Types.INTEGER));
	function.compile();
	assertThat(function.getCallParameters()).extracting(SqlParameter::getName)
			.containsExactly("RESULT", "AMOUNT", "out_status");
	verifyStatement(function, "{? = call GET_TOTAL(?, ?)}");
	Integer total = function.executeFunction(Integer.class, 5);
	assertThat(total).isEqualTo(42);
}
```
(SimpleJdbcCallTests.java:270-283)

- **주장**: 함수의 반환 파라미터를 **두 번째로** 선언해도 반환 슬롯에는 그것이
  들어가고, `executeFunction()`은 함수 반환값을 돌려준다.
- **fix 전 red인 이유**: `get("RESULT")`가 키 `"result"`를 못 찾고 폴백이
  `outParamNames[0]` = `"out_status"`를 집는다. 첫 단언에서 실패하며 실측 actual은
  `["out_status", "AMOUNT", "out_status"]`였다 — `out_status`가 반환 슬롯과 자기
  슬롯에 **두 번** 들어가고 `RESULT`는 사라진다.

**`containsExactly("RESULT", "AMOUNT", "out_status")`의 세 원소가 각각 다른 것을
말한다.** 대소문자가 뒤섞인 것이 우연이 아니라, 이 목록이 어떻게 만들어졌는지의
지표다.

- 순서 `[반환, IN, OUT]`은 **선언 순서가 아니라 메타데이터 순서**다. `reconcileParameters`의
  두 번째 순회가 DB가 준 행 순서로 목록을 쌓기 때문이고(CallMetaDataContext.java:367),
  그 순서가 곧 `{? = call ...}`의 슬롯 순서가 된다. 선언은 `out_status` -> `RESULT`
  순인데 결과가 뒤집혀 있다는 것 자체가 "선언 순서는 의미 없다"는 계약의 표현이다.
- `"RESULT"` — 대문자인 이유는 **사용자가 그렇게 선언했고, 선언 인스턴스가 그대로
  채택됐기 때문**이다. 매칭은 정규화된 키 `"result"`로 하지만, 목록에 들어가는 것은
  `SqlParameter` 원본이라 이름 표기가 보존된다.
- `"AMOUNT"` — 대문자인 이유는 정반대다. 메타데이터의 `amount` 컬럼에 대응하는 선언이
  없으므로 provider가 **새로 만든** 기본 IN 파라미터이고(:450), 그 이름은
  `provider.parameterNameToUse("amount")`다. 목이 Oracle + `storesUpperCaseIdentifiers=true`이므로
  대문자로 접힌다.
- `"out_status"` — 소문자인 이유는 `"RESULT"`와 같다. 메타 컬럼 `out_status`가 선언
  키 `"out_status"`와 매치되어 **선언 인스턴스가 재사용**됐다.

즉 이 한 줄이 "어느 파라미터가 선언에서 채택됐고 어느 것이 메타데이터에서
생성됐는가"를 이름 표기만으로 구분해 준다.

- `verifyStatement(function, "{? = call GET_TOTAL(?, ?)}")` — 반환 슬롯은
  `createCallString`이 `parameterCount = -1`로 시작해 건너뛰므로(:635-638, :652-662)
  `?`는 두 개다. 슬롯 **수**는 fix 전에도 맞았다는 점이 중요하다. SQL이 문법적으로
  멀쩡했기 때문에 이 결함이 예외 없이 지나갈 수 있었다.
- `assertThat(total).isEqualTo(42)` — 목이 `getObject(1)`(반환 슬롯)에 42,
  `getObject(3)`(OUT 슬롯)에 7을 넣어 뒀다. **두 값을 다르게 둔 것이 이 테스트의
  관측 장치**다. 같은 값이었다면 결과 맵의 키 충돌이 아무 차이도 만들지 않아 결함이
  보이지 않는다. fix 전에는 7이 나왔다.

## T2. 선언 순서 역전 — 가드 (전후 green)

둘째 테스트는 T1의 선언 순서만 뒤집어 같은 결과를 요구한다.

```java
	function.declareParameters(
			new SqlOutParameter("RESULT", Types.INTEGER),
			new SqlOutParameter("out_status", Types.INTEGER));
```
(SimpleJdbcCallTests.java:285-297 — 나머지 단언은 T1과 동일, `verifyStatement`만 없음)

- **주장**: 반환 파라미터를 먼저 선언한 경우의 결과는 T1과 **완전히 같다**.
- **fix 전에도 green인 이유**: 1차 조회 `get("RESULT")`는 여전히 빗나가지만, 폴백이
  집는 `outParamNames[0]`이 이번에는 `"RESULT"`이고 `toLowerCase`하면 `"result"` —
  키와 우연히 일치한다. **우연히 맞는 폴백**이 이 결함을 오래 숨긴 바로 그 경로다.
- **fix 후 green인 이유는 다르다**: 이제는 폴백까지 가지 않고 2차 조회
  `lowerCase(parameterNameToUse("RESULT"))` = `"result"`가 맞는다. 결과는 같고 경로가
  바뀐 것 — 그래서 이 테스트의 역할은 **무회귀 가드**다. 수정이 "잘 되던 순서"를
  깨뜨리지 않았음을 고정한다.
- T1과 짝을 이뤄 "두 선언 순서의 결과가 동일하다"를 함께 주장한다. 어느 한쪽만으로는
  순서 무관 계약을 표현할 수 없다.

## T3. 변형 B 재현 — red

셋째 테스트는 무대를 SQL Server 프로시저로 옮겨 `@` 접두 OUT을 먼저 선언한다.

```java
@Test
void sqlServerProcedureWithReturnValueDeclaredAfterOutParameter() throws Exception {
	initializeSqlServerProcedureWithReturnValue();
	SimpleJdbcCall procedure = new SimpleJdbcCall(dataSource).withProcedureName("my_proc").withReturnValue();
	procedure.declareParameters(
			new SqlOutParameter("@out_total", Types.INTEGER),
			new SqlOutParameter("RETURN_VALUE", Types.INTEGER));
	procedure.compile();
	assertThat(procedure.getCallParameters()).extracting(SqlParameter::getName)
			.containsExactly("RETURN_VALUE", "amount", "@out_total");
	verifyStatement(procedure, "{? = call my_proc(?, ?)}");
}
```
(SimpleJdbcCallTests.java:299-310)

- **주장**: `@` 접두 OUT을 먼저 선언해도 `compile()`이 성공하고, 반환 파라미터가 반환
  슬롯에 들어간다.
- **fix 전 red인 이유**: `compile()` 자체가
  `InvalidDataAccessApiUsageException: Unable to locate declared parameter for function
  return value - add an SqlOutParameter with name 'return'`으로 터진다. 단언에 닿지도
  못한다. 메시지의 `'return'`은 `getFunctionReturnName()`의 기본값 — 프로시저 경로라
  `actualFunctionReturnName`이 설정되지 않았음을 그대로 드러낸다.
- **`compile()`이 예외 없이 끝나는 것 자체가 첫 단언**이다. 별도의
  `assertThatNoException`을 쓰지 않은 것은 이 파일의 기존 관례(`compile()` 후 곧바로
  `verifyStatement`)를 따른 것이다.

세 이름의 의미는 T1과 같은 방식으로 읽는다.

- `"RETURN_VALUE"` — 선언 인스턴스가 채택돼 원본 표기 유지. 매칭은 메타 이름
  `@RETURN_VALUE`를 정규화한 `"return_value"`로 이루어졌다(수정된 1차 조회).
- `"amount"` — 메타 컬럼 `@amount`에 대응하는 선언이 없어 새로 생성된 IN 파라미터.
  이름은 `parameterNameToUse("@amount")` = `"amount"`다. SQL Server provider가 `@`를
  떼고(SqlServerCallMetaDataProvider.java:44-55), 목이 `storesUpperCaseIdentifiers`를
  스텁하지 않아 폴딩은 일어나지 않는다.
- `"@out_total"` — 선언 인스턴스라 `@`가 **그대로 남는다**. 정규화는 조회 키에만
  적용되고 파라미터 이름 자체는 건드리지 않는다는 것을 이 원소가 증명한다. 즉 수정이
  결과 맵의 키(사용자가 값을 꺼낼 이름)를 바꾸지 않는다는 뜻이다.
- `verifyStatement(procedure, "{? = call my_proc(?, ?)}")` — `withReturnValue()`가
  `isReturnValueRequired()`를 켜므로 `{? = call` 형태이고(:635), 반환 슬롯을 건너뛴
  `?`가 둘이다. 프로시저 이름은 폴딩 없이 `my_proc` 그대로.

## T4. 선언 순서 역전 — 가드 (전후 green)

넷째 테스트는 T3의 선언 순서를 뒤집은 짝이다.

```java
	procedure.declareParameters(
			new SqlOutParameter("RETURN_VALUE", Types.INTEGER),
			new SqlOutParameter("@out_total", Types.INTEGER));
```
(SimpleJdbcCallTests.java:312-323 — 단언은 T3과 동일)

- **fix 전에도 green인 이유**: 1차 조회는 `get("return")`으로 빗나가지만, 폴백이
  `outParamNames[0]` = `"RETURN_VALUE"`를 소문자화해 `"return_value"`를 조회하고 —
  선언 키와 일치한다. T2와 같은 종류의 우연이다.
- **fix 후**: 수정된 1차 조회 `get(paramNameToCheck)`가 곧바로 맞는다. T3와 동일한
  경로가 되므로, 이 가드는 "두 순서가 이제 **같은 코드 경로**를 탄다"까지 함께
  고정한다.

## 목 헬퍼 두 개

테스트가 red를 결정론적으로 만들려면 목 메타데이터가 실드라이버의 보고 형태를 정확히
모사해야 한다. 두 헬퍼가 그 형태를 각각 담당한다.

```java
private void initializeGetTotalFunctionWithMetaData() throws SQLException {
	...
	given(databaseMetaData.getDatabaseProductName()).willReturn("Oracle");
	given(databaseMetaData.getUserName()).willReturn("ME");
	given(databaseMetaData.storesUpperCaseIdentifiers()).willReturn(true);
	given(databaseMetaData.getProcedures("", "ME", "GET_TOTAL")).willReturn(proceduresResultSet);
	given(databaseMetaData.getProcedureColumns("", "ME", "GET_TOTAL", null)).willReturn(procedureColumnsResultSet);
	...
	given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn(null, "amount", "out_status");
	given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(5, 1, 4);
	given(connection.prepareCall("{? = call GET_TOTAL(?, ?)}")).willReturn(callableStatement);
	...
	given(callableStatement.getObject(1)).willReturn(42);
	given(callableStatement.getObject(3)).willReturn(7);
}
```
(SimpleJdbcCallTests.java:409-428, 발췌)

- 이름·방향 3행이 핵심이다. `COLUMN_NAME`의 첫 값 `null`이 **이름 없는 함수 반환
  슬롯**이고, `COLUMN_TYPE` `5, 1, 4`가 각각 반환·IN·OUT이다. 기존 헬퍼
  `initializeAddInvoiceWithMetaData`(:362-389)의 함수 분기가 쓰는
  `willReturn(null, "amount", "custid")` / `willReturn(5, 1, 1)`을 그대로 답습하되,
  세 번째 행을 IN에서 **OUT(4)**으로 바꾼 것이 이 헬퍼의 전부다. 그 한 칸이
  "함수 반환 슬롯과 별도 OUT이 공존하는" 변형 A의 무대를 만든다.
- 카탈로그 `""`·스키마 `"ME"`는 Oracle provider의 이름 규칙에서 나온다 — 카탈로그는
  패키지 이름 자리라 없으면 빈 문자열, 스키마는 지정이 없으면 현재 사용자
  (OracleCallMetaDataProvider.java:62-71). 프로시저 이름은 대문자로 접혀 `GET_TOTAL`.
- 메타데이터를 `getProcedures`/`getProcedureColumns`로 스텁하므로 드라이버 조회는
  **프로시저 시그니처로 성립**하고, 그 결과 `CallParameterMetaData`의 function 플래그는
  false다. 따라서 `COLUMN_TYPE=5`는 `procedureColumnReturn`으로 해석되어
  `isReturnParameter()`가 true가 된다(CallParameterMetaData.java:91-95). 컨텍스트 쪽
  `isFunction()`은 `withFunctionName()` 때문에 true라, "함수 컨텍스트 + 프로시저 형태
  메타데이터"라는 기존 테스트의 모델링을 그대로 이어받는다.
- `getObject(1)`과 `getObject(3)`을 다른 값으로 둔 이유는 T1 해설대로다.

```java
private void initializeSqlServerProcedureWithReturnValue() throws SQLException {
	...
	given(databaseMetaData.getDatabaseProductName()).willReturn("Microsoft SQL Server");
	given(databaseMetaData.getProcedures(null, null, "my_proc")).willReturn(proceduresResultSet);
	given(databaseMetaData.getProcedureColumns(null, null, "my_proc", null)).willReturn(procedureColumnsResultSet);
	...
	given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn("@RETURN_VALUE", "@amount", "@out_total");
	given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(5, 1, 4);
}
```
(SimpleJdbcCallTests.java:430-442, 발췌)

- 제품명이 `"Microsoft SQL Server"`여야 `SqlServerCallMetaDataProvider`가 선택되고,
  그래야 `@` 스트립이 발동한다.
- 카탈로그·스키마가 `null`인 것은 `supportsCatalogsInProcedureCalls` 등을 스텁하지
  않아 목이 false를 돌려주고, 그때 `metaDataCatalogNameToUse`/`metaDataSchemaNameToUse`가
  null을 반환하기 때문이다(GenericCallMetaDataProvider.java:142-160). 같은 이유로
  `storesUpperCaseIdentifiers`도 false라 이름 폴딩이 없다 — 이 헬퍼의 관심사는 오직
  `@` 스트립이므로 폴딩을 끄는 편이 관측을 단순하게 한다.
- 세 행 모두 `@`로 시작하는 것이 SQL Server 드라이버의 실제 보고 형태다.
  `@RETURN_VALUE`는 상태 코드 슬롯의 의사 파라미터
  ([저장 프로시저](../../concepts/stored-procedure/stored-procedure.md)).
- 실행 스텁(`prepareCall`·`getObject`)이 없다. T3·T4가 `compile()` 단계까지만
  검증하기 때문이다 — 변형 B의 증상이 실행이 아니라 컴파일 시점의 예외라서 그
  단계에서 결론이 난다.

## 실측 요약

실행 결과는 red 둘과 가드 둘이라는 예측과 일치했고, 도달 불가 판정도 여기서 실측으로 확인됐다.

- **fix 전**: T1 실패(actual `["out_status", "AMOUNT", "out_status"]`), T3 실패
  (`InvalidDataAccessApiUsageException ... name 'return'`). T2·T4는 green — 예측대로
  "반환 파라미터를 먼저 선언한" 두 케이스는 원래 동작했다.
- **fix 후**: `SimpleJdbcCallTests` **22/22 green**(기존 18 + 신규 4),
  `core.metadata` 패키지 green, `spring-jdbc` 전체 **958 tests, 6 skipped,
  0 failures, 0 errors**. checkstyle(`checkstyleMain checkstyleTest`) EXIT=0.
- **세 번째 조회의 미실행 실측**: 3차 폴백만 구 코드(`toLowerCase`)로 되돌려도
  22/22 green이었다. 현재 테스트 4건이 그 줄을 실행하지 않는다는 뜻이고,
  [analysis.md](analysis.md) §6.3의 "fix 후 도달 불가" 판정과 정합한다. 가드
  테스트를 쓸 수 없는 줄이라는 사실이 여기서 실측으로 확인됐다.

## 실측 probe — 커밋에 남기지 않은 두 번의 확인

리뷰·질의 과정에서 **임시 테스트를 붙여 돌려 보고 결과만 취한 뒤 파일을 원복한**
확인이 둘 있다. 커밋에는 없지만 판단의 근거이므로 기록해 둔다(원본: 작업 로그).

**probe 1 — `withReturnValue()` 없이 `RETURN_VALUE`를 선언한 경우.** 리뷰에서
"수정된 1차 조회가 인접 시나리오의 동작을 바꾸지 않는가"라는 지적이 나와, SQL Server
프로시저를 `withReturnValue()` 없이 `@out_total` -> `RETURN_VALUE` 순으로 선언해
돌렸다. 결과는 파라미터 `[RETURN_VALUE, amount, @out_total]`, callString
`{call my_proc(?, ?, ?)}` — 반환 파라미터가 **일반 슬롯**으로 바인딩된다(실행하면
드라이버 오류). fix 전에는 이 순서에서 예외가 났지만, 반환 파라미터를 먼저 선언하면
fix 전에도 같은 결과였다. 즉 새 구멍이 아니라 기존 구멍이 두 순서에 일관되게
적용된 것이고, `withReturnValue()` 없이 반환 파라미터를 선언하는 것 자체가 API
오용이라는 판단으로 별도 이슈화는 하지 않았다.

**probe 2 — 반환 파라미터를 먼저, IN 파라미터도 함께 선언한 경우.** 사용자가 제시한
형태(선언 `result` -> `amount`, 메타 `[null, amount, out_status]`)로 돌린 결과는
파라미터 `[result, amount, OUT_STATUS]`, callString `{? = call GET_TOTAL(?, ?)}`,
`executeFunction` = 42였다. T1과 정확히 거울상이다 — 이번에는 `amount`가 선언에서
채택돼 소문자로 남고, 선언되지 않은 `out_status`가 새로 생성돼 `OUT_STATUS`로
대문자가 된다. "채택이면 원본 표기, 생성이면 provider 표기"라는 규칙을 반대 방향에서
확인한 셈이다.

## 머지 후 polish — 같은 계약을 한 층 아래에서 다시 잰다

머지(`ec6b9251916`) 직후 Sam Brannen이 `ee7a0d48c56`("Polish contribution", See
gh-37206)로 테스트를 보강했다. 위 T1~T4는 그대로 남았고, 바뀐 것은 두 가지다.

**우리 테스트에 대한 손질은 표기뿐이다.** `SimpleJdbcCallTests`의 4건에
`@Test  // gh-37206` 주석이 붙었고, T1 위의 빈 줄 두 개가 하나로 줄었다. 단언·픽스처·
목 헬퍼는 한 글자도 바뀌지 않았다. 이슈 번호 주석은 이 파일의 관례라기보다 프로젝트
전반의 관례인데, 제출 때는 붙이지 않았다 — 회귀 테스트가 어느 이슈에서 왔는지를
테스트 자체에 남기는 것이 나중에 그 테스트를 지워도 되는지 판단하는 근거가 된다.

**새로 추가된 것은 `CallMetaDataContextTests`의 2건이다.** 이 파일은 우리가 만든 것이
아니라 Thomas Risberg가 쓴 기존 목 기반 단위 테스트이고, 폴리시는 거기에 같은 결함을
겨냥한 쌍을 더했다(그리고 `@author Sam Brannen`을 추가했다).

```java
	@Test  // gh-37206
	void reconcileParametersMatchesFunctionReturnParameterDeclaredBeforeOutParameter() throws Exception {
		initializeGetTotalFunctionMetaData();

		List<SqlParameter> parameters = List.of(
				new SqlOutParameter("RESULT", Types.INTEGER),
				new SqlOutParameter("out_status", Types.INTEGER));

		context.setFunction(true);
		context.setProcedureName("GET_TOTAL");
		context.initializeMetaData(dataSource);
		context.processParameters(parameters);

		assertThat(context.getCallParameters()).extracting(SqlParameter::getName)
				.containsExactly("RESULT", "AMOUNT", "out_status");
	}
```

두 번째 테스트(`...DeclaredAfterOutParameter`)는 `List.of`의 두 원소 순서만 뒤집고
나머지는 같다. 즉 T1/T2와 **똑같은 순서 쌍 구조**를 한 층 아래에서 반복한다.

층위 차이가 이 추가의 전부이자 요점이다. T1~T4는 `SimpleJdbcCall`이라는 사용자 API를
입구로 삼아 `compile()` -> callString -> `executeFunction()`까지 흐르는 경로를 재현했다.
폴리시의 2건은 그 껍질을 벗기고 결함이 실제로 사는 클래스를 직접 세운다 —
`setFunction(true)` · `setProcedureName("GET_TOTAL")` · `initializeMetaData(dataSource)` ·
`processParameters(parameters)`를 손으로 호출하고, 관측은
`getCallParameters()`의 이름 목록 한 줄로 끝낸다. `verifyStatement`도
`executeFunction`도 없다. 결함이 파라미터 **매칭**이지 실행이 아니기 때문에, 매칭
결과만 보면 판정이 난다.

목 헬퍼 `initializeGetTotalFunctionMetaData()`도 그 축소를 그대로 반영한다.

```java
	private void initializeGetTotalFunctionMetaData() throws SQLException {
		ResultSet proceduresResultSet = mock();
		ResultSet procedureColumnsResultSet = mock();
		given(databaseMetaData.getDatabaseProductName()).willReturn("Oracle");
		given(databaseMetaData.getUserName()).willReturn("ME");
		given(databaseMetaData.storesUpperCaseIdentifiers()).willReturn(true);
		given(databaseMetaData.getProcedures("", "ME", "GET_TOTAL")).willReturn(proceduresResultSet);
		given(databaseMetaData.getProcedureColumns("", "ME", "GET_TOTAL", null)).willReturn(procedureColumnsResultSet);
		given(proceduresResultSet.next()).willReturn(true, false);
		given(proceduresResultSet.getString("PROCEDURE_NAME")).willReturn("GET_TOTAL");
		given(procedureColumnsResultSet.next()).willReturn(true, true, true, false);
		given(procedureColumnsResultSet.getInt("DATA_TYPE")).willReturn(Types.INTEGER);
		given(procedureColumnsResultSet.getString("COLUMN_NAME")).willReturn(null, "amount", "out_status");
		given(procedureColumnsResultSet.getInt("COLUMN_TYPE")).willReturn(5, 1, 4);
	}
```

우리 쪽 `initializeGetTotalFunctionWithMetaData()`와 메타데이터 스텁은 동일하다 —
Oracle · 대문자 폴딩 · `COLUMN_NAME`이 `null, "amount", "out_status"` ·
`COLUMN_TYPE`이 `5, 1, 4`. 없는 것은 실행 스텁이다. `prepareCall`도 `getObject(1)`/
`getObject(3)`도 스텁하지 않는다. T1 해설에서 "42와 7을 다르게 둔 것이 관측 장치"라고
적었는데, 이 층위에서는 그 장치가 필요 없다. 반환 슬롯에 어떤 `SqlParameter`가
들어갔는지가 이름 목록으로 직접 보이기 때문이다.

정리하면 폴리시는 우리 테스트를 대체한 것이 아니라 **다른 질문을 하는 테스트를 옆에
세웠다**. 통합 경로 4건은 "사용자가 받는 값이 뒤바뀌는가"를 묻고, 단위 2건은
"`reconcileParameters()`가 어느 파라미터를 반환 슬롯에 넣는가"를 묻는다. 앞의 질문은
결함의 손해를 보여 주고, 뒤의 질문은 결함의 소재를 좁혀 준다. 배울 점은 이것이다 —
결함이 사는 클래스에 그 클래스만 세우는 테스트 파일이 이미 있다면, 통합 재현만으로
끝내지 말고 그 파일에도 한 줄 걸어 두는 편이 낫다. 나중에 이 로직을 만지는 사람이
`SimpleJdbcCall`까지 거슬러 올라가지 않아도 계약을 마주치게 된다.
