# PR #37206 — 착수 분석: reconcileParameters의 함수 반환값 조회 결함

> 원본: `docs/plans/2026-08-27/j5-callmetadata-return-reconcile/analysis.md`(착수 전
> 작성). 학습 문서로 옮기면서 작업 진행용 절(인터뷰 항목)을 덜어내고, 수정이 적용된
> 현재 시점에 맞춰 시제를 정리했다. 결론은 PR #37206으로 반영됐다(커밋 `8f9027a995f`).
>
> **좌표 주의**: 본문의 `L3xx`는 **수정 전** 파일(upstream main `b28569119fe`) 기준이다.
> 수정 후 좌표와 분기도는 [structure.md](structure.md)를 본다. 문제·수정 요약은
> [README.md](README.md), 테스트는 [tests.md](tests.md).

## 0. 결론 먼저

`reconcileParameters()`는 선언 파라미터를 **정규화된 키**(`lowerCase(provider.parameterNameToUse(name))`)로
맵에 넣어 두고 메타데이터 파라미터와 대조한다. 그런데 **함수 반환값 행**을 처리하는
분기(L377-379)만 그 정규화를 건너뛰었다.

```java
param = declaredParams.get(getFunctionReturnName());                                      // L377 raw 이름
if (param == null && !getOutParameterNames().isEmpty()) {
    param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));   // L379 첫 OUT 무조건 + parameterNameToUse 미적용
}
```

결과는 두 갈래다. **(A) Oracle류 함수 + 추가 OUT 파라미터를 반환값보다 먼저 선언** ->
첫 OUT이 반환 슬롯을 점유해 선언한 반환 파라미터가 조용히 소실되고 `executeFunction()`이
OUT 값을 돌려준다(무예외). **(B) SQL Server/Sybase 프로시저 `withReturnValue()` +
`@`접두 OUT을 먼저 선언** -> 올바른 선언인데 `InvalidDataAccessApiUsageException`.
둘 다 **선언 순서에 의존**하며, 그 순서 의존은 어디에도 문서화되어 있지 않다. 수정은
반환 분기의 조회를 맵과 **같은 정규화**로 맞추는 것 — 구조 변경 없이 세 줄이다.

## 1. 무대 — 객체와 역할

결함은 빌더에서 드라이버까지 이어지는 네 층 가운데 셋째 층에 산다. 각 층이 무엇을 맡는지부터 편다.

```
 SimpleJdbcCall (public API, 빌더)                            spring-jdbc/core/simple/SimpleJdbcCall.java
   │  withFunctionName() → setFunction(true)                  :94-96
   │  withReturnValue()  → setReturnValueRequired(true)       :113-114
   │  declareParameters() → addDeclaredParameter()            (AbstractJdbcCall:250)
   │  executeFunction()/executeObject() → doExecute().get(getScalarOutParameterName())   :154-185
   ▼
 AbstractJdbcCall (compile/execute 골격)                      spring-jdbc/core/simple/AbstractJdbcCall.java
   │  compile() → compileInternal()                           :294, :325
   │  doExecute(...) → matchInParameterValues... → executeCallInternal() → JdbcTemplate.call()   :382-431
   ▼
 CallMetaDataContext (이번 무대 — 선언 vs 메타데이터 reconcile)   spring-jdbc/core/metadata/CallMetaDataContext.java
   ├─ 필드: procedureName / catalogName / schemaName / callParameters(List<SqlParameter>)
   │        actualFunctionReturnName(@Nullable) / limitedInParameterNames / outParameterNames
   │        function / returnValueRequired / accessCallParameterMetaData / namedBinding / metaDataProvider
   ├─ initializeMetaData(ds) → CallMetaDataProviderFactory.createMetaDataProvider     :244
   ├─ processParameters(list) → reconcileParameters(list)  ★ 결함 위치                :305, :312
   ├─ createCallString()  ({? = call ...} 조립, 반환 슬롯은 parameterCount=-1로 건너뜀)   :610
   ├─ getFunctionReturnName() = actualFunctionReturnName ?: "return"                   :107
   └─ getScalarOutParameterName() = isFunction ? getFunctionReturnName() : outNames[0] :280
   ▼
 CallMetaDataProvider (DB별 이름 정규화·메타데이터 공급)         spring-jdbc/core/metadata/*Provider.java
   ├─ GenericCallMetaDataProvider.parameterNameToUse = identifierNameToUse (storesUpper/Lower 폴딩)  :163
   ├─ SqlServer/Sybase: parameterNameToUse가 "@" 접두 스트립 후 super           SqlServer:45-53, Sybase:45-53
   ├─ byPassReturnParameter: SqlServer "@RETURN_VALUE" / Sybase "RETURN_VALUE" / Postgres "returnValue"
   ├─ getCallParameterMetaData() → List<CallParameterMetaData>(processProcedureColumns가 채움)   Generic:355-395
   └─ CallParameterMetaData.isReturnParameter(): function이면 functionReturn, 아니면 procedureColumnReturn/Result  :91-95
   ▼
 JdbcTemplate.extractOutputParameters(cs, params)                       spring-jdbc/core/JdbcTemplate.java
      SqlOutParameter마다 results.put(outParam.getName(), cs.getObject(sqlColIndex)) — **이름이 키** (같은 이름이면 뒤가 덮음)
```

## 2. 전체 메서드 그래프

### 2.1 컴파일 경로 (선언 -> 호출문 확정)

선언한 파라미터가 실제 호출문으로 굳는 경로는 다음과 같고, 결함은 그 한복판의 reconcile에 있다.

```
SimpleJdbcCall.withFunctionName("get_total")                 setFunction(true)
  .declareParameters(p1, p2, ...)                            declaredParameters += p
  .executeFunction(...)  ──► doExecute() ──► checkCompiled() ──► compile()
                                                                   │
                                                                   ▼
                                               AbstractJdbcCall.compileInternal()            :325
                                                 ├─ callMetaDataContext.initializeMetaData(ds)      provider 결정 (제품명 → Oracle/SqlServer/... )
                                                 ├─ declaredRowMappers → createReturnResultSetParameter
                                                 ├─ callMetaDataContext.processParameters(declaredParameters)
                                                 │      └─ reconcileParameters(parameters)  ★     :312-466
                                                 │           └─ this.callParameters = 결과
                                                 ├─ callString = createCallString()                  :610
                                                 └─ callableStatementFactory = new CSCF(callString, callParameters)
```

### 2.2 실행 경로 (값 바인딩 -> 결과 맵 -> 반환값 추출)

확정된 목록이 실행 시 어떻게 소비되는지를 보면 잘못된 목록의 여파가 어디까지 가는지 드러난다.

```
doExecute(args) ──► matchInParameterValuesWithCallParameters(args)   (callParameters 기준으로 IN 값 매칭)
                ──► executeCallInternal(params) ──► JdbcTemplate.call(csc, callParameters)
                                                       └─ extractOutputParameters(cs, callParameters)
                                                            for param in callParameters:      (위치 = sqlColIndex, 이름 = outParam.getName())
                                                              results.put(name, cs.getObject(idx))
                ──► .get(getScalarOutParameterName())        isFunction ? getFunctionReturnName() : outParameterNames[0]
```

그래프에서 결함이 전파되는 길: **reconcileParameters가 잘못된 SqlParameter 목록을
`callParameters`에 넣으면** -> createCallString의 슬롯 수·순서, extractOutputParameters의
이름 키, getScalarOutParameterName의 키가 **전부 그 목록에서 파생**되므로 하류 셋이
동시에 어긋난다. 반대로 말하면 reconcile 한 곳만 맞추면 하류는 자동으로 정합해진다.

## 2.5 핵심 이름표 사전 — 이 흐름에 등장하는 변수·메서드의 역할

reconcile을 읽을 때 헷갈리는 것은 "이름"이 네 가지 표기로 돌아다닌다는 점이다:
사용자가 선언한 원본 표기, provider가 DB 규칙으로 바꾼 표기, 맵 키용 소문자 표기,
메타데이터가 준 표기. 아래 표의 각 항목은 그중 무엇을 들고 있는지를 명시한다.
(예시 값은 변형 A = Oracle 함수 `get_total`, 선언 `out_status`·`RESULT` / 변형 B =
SQL Server 프로시저, 선언 `@out_total`·`RETURN_VALUE`. 값은 **수정 전** 동작 기준이다.)

| 이름표 | 무엇인가 | 언제 정해지나 | 변형 A에서의 값 | 변형 B에서의 값 |
|---|---|---|---|---|
| `provider.parameterNameToUse(name)` | **DB 표기 규칙 적용** — Oracle은 대문자 폴딩, SQL Server/Sybase는 `@` 제거 후 폴딩 | provider가 제품명으로 결정된 뒤(`initializeMetaData`) | `"RESULT"`->`"RESULT"`, `"out_status"`->`"OUT_STATUS"` | `"@out_total"`->`"out_total"`(폴딩 없음 가정) |
| `lowerCase(...)` | 맵 키를 대소문자 무관하게 만드는 **최종 정규화** | 위 결과에 항상 덧씌움 | `"result"`, `"out_status"` | `"out_total"`, `"return_value"` |
| `declaredParams` | 선언 파라미터 맵. **키 = `lowerCase(parameterNameToUse(원본))`**, 값 = 원본 `SqlParameter`(이름은 원본 표기 유지) | 1단계(선언 순회) | `{out_status->P1, result->P2(RESULT)}` | `{out_total->P1, return_value->P2}` |
| `metaDataParamNames` | 메타데이터의 **비-반환** 파라미터 이름(소문자) 목록 — "이 선언이 실제 컬럼인가"를 판별하는 참조표 | 0단계 | `[amount, out_status]` | `[amount, out_total]` |
| `outParamNames` / `getOutParameterNames()` | 선언된 OUT 파라미터의 **원본 표기**를 선언 순서대로 | 1단계에서 append, `setOutParameterNames` | `["out_status", "RESULT"]` — **0번째가 반환이 아님** | `["@out_total", "RETURN_VALUE"]` — 0번째에 `@` 포함 |
| `returnDeclared` | "함수의 반환 파라미터가 선언에 있다"는 플래그 | 1단계: `isFunction()` && 선언 OUT의 키가 `metaDataParamNames`에 없을 때 첫 번째만 | true (RESULT에서) | false (프로시저라 이 탐지 자체가 안 돎) |
| `actualFunctionReturnName` | 반환 파라미터의 **원본 표기** 캐시(@Nullable). 나중에 결과 맵에서 값을 꺼낼 키의 재료 | 1단계 탐지 시 / 3단계 반환 행 처리 시 덮어씀 / 사용자 `setFunctionReturnName` | 1단계 후 `"RESULT"` -> 3단계 폴백 후 **`"out_status"`로 덮임** | null 유지 |
| `getFunctionReturnName()` | `actualFunctionReturnName`이 있으면 그것, 없으면 기본값 **`"return"`** — 반환값을 부르는 이름 | 호출 시점 계산 | `"RESULT"` (raw 표기 — 키와 불일치) | `"return"` |
| `meta` / `meta.isReturnParameter()` | DB가 준 파라미터 한 행 / 그 행이 반환 슬롯인가(`COLUMN_TYPE` 5 = functionReturn·procedureColumnReturn) | 메타데이터 로딩 | 반환 행의 `getParameterName()` = **null** (Oracle 함수 반환은 무명) | 반환 행 이름 = `"@RETURN_VALUE"` |
| `paramNameToCheck` | 메타 행 이름에 **선언 맵과 같은 정규화**를 적용한 키 — "이 메타 행에 대응하는 선언이 있나"의 조회 키 | 3단계 각 행마다 | 반환 행: **null** (이름이 없으니 정규화할 것도 없음) / OUT 행: `"out_status"` | 반환 행: `"return_value"` -> 선언과 **이미 매치** |
| `paramNameToUse` | 메타 행 이름의 DB 표기(소문자화 전) — 기본 파라미터를 새로 만들 때 쓰는 이름 | 3단계 | 반환 행: null / OUT 행: `"OUT_STATUS"` | `"RETURN_VALUE"` |
| `workParams` -> `callParameters` | 최종 호출 파라미터 목록. **메타데이터 순서**로 쌓이며 이 목록이 SQL 슬롯·바인딩·결과 키를 전부 결정 | 3단계 누적 | 버그 시 `[P1(out_status), AMOUNT, P1(out_status)]` | 버그 시 예외로 도달 못 함 |
| `getScalarOutParameterName()` | `executeFunction()`이 결과 맵에서 값을 꺼낼 키 = 함수면 `getFunctionReturnName()` | 실행 시 | 버그 시 `"out_status"` | — |

이 표에서 결함이 한 줄로 보인다: **L377은 `getFunctionReturnName()`(원본 표기 `"RESULT"`)로
`declaredParams`(키 `"result"`)를 조회한다** — 같은 이름의 두 표기를 섞은 것이고,
L379는 `outParamNames`(원본 표기, 0번째가 반환이라는 보장 없음)에 `toLowerCase`만
적용해 `parameterNameToUse`(`@` 제거)를 건너뛴다. 수정안 6.1은 세 조회 모두를 표의
`declaredParams` 키 규칙으로 통일한 것이다.

## 2.6 "행"이 세 종류라는 것 — 메타데이터 행 vs OUT 값 vs 결과셋

reconcile이 다루는 "행"은 쿼리 결과가 아니라 **`DatabaseMetaData.getProcedureColumns()`가
돌려주는 시그니처 설명서**다(파라미터당 1행: 이름·방향(`COLUMN_TYPE`)·타입). 실행
결과의 OUT 값은 `CallableStatement.getObject(index)`로 **위치 기반**으로만 오고,
이름은 Spring이 `callParameters`의 이름으로 붙여준다 — 그래서 목록의 이름 정확성이
결과 맵의 정확성이다. 결과셋(SELECT)은 별개.

함수 반환값은 시그니처 문법상 이름이 없다(`... RETURN NUMBER`). Oracle 드라이버는
이를 `COLUMN_TYPE=5, COLUMN_NAME=null` 행으로 보고하고(기존 테스트
`initializeAddInvoiceWithMetaData`의 `willReturn(null, "amount", "custid")`가 그
모델링), SQL Server는 상태 코드 RETURN을 `@RETURN_VALUE`라는 이름 있는 의사
파라미터로 노출한다. 수정안 (1)/(2)의 갈림(메타 이름 매치 vs 선언 이름 조회)은 이
DB별 차이에서 온다 — (2)는 예외 케이스가 아니라 **Oracle 함수의 기본 경로**다.

## 2.7 배경 — "반환값"은 SELECT/CUD의 문제가 아니라 함수 vs 프로시저의 문제

혼동하기 쉬운 지점이라 명시한다. 여기서 "반환값"은 쿼리(SELECT/CUD)의 결과가 아니라
**저장 함수(stored function)의 RETURN 슬롯**이다.

- **프로시저**(`CREATE PROCEDURE ... (a IN, b OUT)`) — 반환 슬롯이 없다. 결과는 전부
  이름 있는 OUT 파라미터로 나온다. `isReturnParameter()` 행이 아예 없으므로 이 결함
  경로에 들어오지 않는다.
- **함수**(`CREATE FUNCTION ... RETURN NUMBER`) — 반환 슬롯이 있고 시그니처상 이름이
  없다. Oracle 드라이버는 `COLUMN_TYPE=5, COLUMN_NAME=null` 행으로 보고한다.
  `SimpleJdbcCall.withFunctionName()` 경로.
- **SQL Server 프로시저의 RETURN 상태코드** — 프로시저지만 정수 상태값 슬롯이 있고,
  드라이버가 `@RETURN_VALUE`라는 **이름 있는** 행으로 보고한다.
  `withProcedureName().withReturnValue()` 경로.

그리고 "항상 문제"가 아니었다. 반환 행이 오면 수정 전 코드는 (1) `getFunctionReturnName()`
정확 키 조회 -> (2) 첫 번째 OUT 이름 소문자 조회로 폴백하는데, (2)가 **사용자가 반환
파라미터를 OUT 목록의 첫 번째로 선언했을 때만** 우연히 맞았다. 즉 결함 발동 조건 =
함수(또는 withReturnValue) **+ 반환 파라미터보다 앞에 다른 OUT 파라미터를 선언**.
그 밖의 경우는 (2)의 우연으로 수정 전에도 동작했다(§4 변형 A/B가 정확히 그 조건).

## 3. reconcileParameters 내부 흐름 (수정 전 L312-466)

메서드 본문을 네 구간으로 쪼개 의사코드로 옮기면 결함이 어느 구간의 어느 줄인지가 보인다.

```
[0] metaDataParamNames ← 메타데이터 중 비-반환 파라미터 이름을 lowerCase로            :321-325

[1] 선언 파라미터 순회 (사용자가 declareParameters로 넘긴 순서)                    :328-351
     key = lowerCase(provider.parameterNameToUse(name))     ← ★ 맵 키 정규화 규칙     :339
     declaredParams.put(key, param)
     if SqlOutParameter:
        outParamNames += rawName
        if isFunction && key ∉ metaDataParamNames && !returnDeclared:
             actualFunctionReturnName = rawName ; returnDeclared = true     ← "메타에 없는 첫 OUT = 함수 반환" 휴리스틱
     setOutParameterNames(outParamNames)

[2] 메타데이터 미사용이면 → declaredReturnParams + declaredParams.values() 반환 (끝)   :353-357

[3] 메타데이터 파라미터 순회 (DB가 알려준 순서 = 실제 호출 슬롯 순서)               :364-463
     paramNameToCheck = lowerCase(provider.parameterNameToUse(metaName))   ← 같은 정규화     :368-370
     ┌ declaredParams.containsKey(paramNameToCheck) || (meta.isReturnParameter() && returnDeclared)
     │   ├ meta.isReturnParameter():
     │   │     param = declaredParams.get(getFunctionReturnName())            ★ L377 — raw 이름 (정규화 없음)
     │   │     if null && outParamNames 비어있지 않음:
     │   │         param = declaredParams.get(outParamNames[0].toLowerCase)   ★ L379 — 첫 OUT 무조건 + parameterNameToUse 없음
     │   │     if null → throw InvalidDataAccessApiUsageException            L381
     │   │     else actualFunctionReturnName = param.getName()                L386
     │   └ else: param = declaredParams.get(paramNameToCheck)                 (일반 파라미터는 정규화 키로 정상 조회)
     │   workParams += param
     └ else (선언에 없음):
         반환 행이면 byPass 판단 후 기본 OUT 파라미터 생성 / 아니면 IN·OUT·INOUT 기본 생성
```

### 분기도로 본 결함의 자리

같은 흐름을 반환 행 처리만 떼어 분기도로 그리면 두 변형이 어느 갈래에서 갈리는지가 드러난다.

```
                 meta.isReturnParameter() 행에 도달
                            │
        ┌───────────────────┴────────────────────┐
  선언에 반환 파라미터 있음                   선언에 없음 → 기본 OUT 생성 (정상, 이 문서 범위 밖)
        │
  L377  declaredParams.get( getFunctionReturnName() )      ← 키는 정규화돼 있는데 raw로 조회
        │
   ┌────┴─────┐
  hit        miss  ← 반환 이름이 전부 소문자가 아니거나(예: "RESULT"), provider가 "@"를 스트립하는 경우
   │           │
  정상    L379  declaredParams.get( outParamNames[0].toLowerCase )   ← "첫 OUT"이 반환값이라는 보장 없음 + "@" 미스트립
              │
         ┌────┴─────┐
        hit         miss
         │            │
   ★ 변형 A     ★ 변형 B
   잘못된 파라미터를   올바른 선언인데
   반환 슬롯에 채택    예외
```

## 4. 오류 지점 정밀 추적 (수정 전 코드 규칙으로 단계 재현)

### 변형 A — Oracle 함수 + 추가 OUT (조용한 오답)

설정: 메타데이터 = [반환(type 5, 이름 null), IN `AMOUNT`, OUT `OUT_STATUS`], Oracle은
`storesUpperCaseIdentifiers` -> `parameterNameToUse`가 대문자화, 맵 키는 다시 lowerCase.

```java
new SimpleJdbcCall(ds).withFunctionName("get_total").declareParameters(
        new SqlOutParameter("out_status", Types.VARCHAR),   // 메타데이터 OUT 컬럼과 매치
        new SqlOutParameter("RESULT", Types.NUMERIC));      // 의도한 함수 반환
```

이 입력을 수정 전 코드 규칙으로 단계마다 따라가면 다음과 같다.

| 단계 | 동작 | 상태 |
|---|---|---|
| [1] `out_status` | key `"out_status"`가 metaDataParamNames에 있음 -> 반환 후보 아님 | declaredParams={out_status} |
| [1] `RESULT` | key `"result"`가 메타에 없음 -> `actualFunctionReturnName="RESULT"`, returnDeclared | declaredParams={out_status, result}, outParamNames=[out_status, RESULT] |
| [3] 반환 행(이름 null) | containsKey(null)=false지만 `returnDeclared`로 진입. **L377 `get("RESULT")` -> 키는 `"result"` -> miss** | |
| | **L379 `get("out_status")` -> hit** -> `param = out_status`, `actualFunctionReturnName="out_status"` | workParams=[out_status] |
| [3] IN `AMOUNT` | 선언 없음 -> 기본 IN 생성 | [out_status, AMOUNT] |
| [3] OUT `OUT_STATUS` | containsKey("out_status") -> **같은 인스턴스 재추가** | [out_status, AMOUNT, out_status] |

하류: `createCallString` = `{? = call GET_TOTAL(?, ?)}`(슬롯 수는 맞아 SQL은 성공).
`extractOutputParameters`가 `results.put("out_status", 위치1)` 뒤
`results.put("out_status", 위치3)` -> **위치 3(OUT)이 위치 1(반환)을 덮음**.
`getScalarOutParameterName()` = `"out_status"` -> `executeFunction()`이 **OUT 값을
반환**. 선언한 `RESULT`(NUMERIC 타입 포함)는 어디에도 없다. 예외·경고 없음.
`RESULT`를 먼저 선언하면 L379의 outParamNames[0]이 `RESULT`라 우연히 정상.

### 변형 B — SQL Server 프로시저 + 반환값 (스퓨리어스 예외)

설정: 메타데이터 = [`@RETURN_VALUE`(type 5), IN `@amount`, OUT `@out_total`], provider가
`@` 스트립(SqlServer:45-53), `isFunction()=false`(프로시저), `withReturnValue()`.

```java
new SimpleJdbcCall(ds).withProcedureName("my_proc").withReturnValue().declareParameters(
        new SqlOutParameter("@out_total", Types.INTEGER),
        new SqlOutParameter("RETURN_VALUE", Types.INTEGER));
```

같은 방식으로 따라가면 이번에는 매치가 있는데도 예외에 도달한다.

| 단계 | 동작 | 상태 |
|---|---|---|
| [1] `@out_total` | key = lowerCase(parameterNameToUse) = `"out_total"` (`@` 제거). 프로시저라 반환 탐지 없음 | declaredParams={out_total} |
| [1] `RETURN_VALUE` | key `"return_value"` | {out_total, return_value}, outParamNames=[@out_total, RETURN_VALUE] |
| [3] `@RETURN_VALUE` 행 | paramNameToCheck = `"return_value"` -> **containsKey true — 이미 매치됨** | |
| | 그런데 L377 `get(getFunctionReturnName())` = `get("return")` -> miss (actualFunctionReturnName 미설정) | |
| | L379 `get("@out_total".toLowerCase())` = `get("@out_total")` -> 키는 `"out_total"` -> **miss** | |
| | -> **`InvalidDataAccessApiUsageException: Unable to locate declared parameter for function return value`** | |

즉 L374에서 `paramNameToCheck`로 **이미 찾아놓은 매치를 L377이 버리고** raw 조회를
다시 한다. `RETURN_VALUE`를 먼저 선언하면 L379가 `"return_value"`를 조회해 우연히 통과.

## 5. 관련 계약 정리

이 무대가 지키기로 한 약속을 여섯 줄로 세우고 수정 전 코드가 그중 무엇을 어겼는지 대조한다.

| 계약 | 출처 | 수정 전 위반 여부 |
|---|---|---|
| 선언 파라미터는 `lowerCase(provider.parameterNameToUse(name))`로 정규화해 매칭한다 | L339, L368-370 (일반 파라미터 경로 전부) | 반환 분기(L377·L379)만 예외적으로 위반 |
| `declareParameters(...)`의 **순서는 의미가 없다** — 메타데이터 순서가 실제 슬롯 순서를 정한다 | L364 메타 순회가 슬롯을 정함; javadoc 어디에도 순서 요구 없음 | 위반 — 반환 파라미터는 "첫 OUT으로 선언해야" 정상 동작하는 숨은 요구 |
| `withFunctionName()` 함수의 반환값은 `getFunctionReturnName()`(선언 OUT 이름 또는 `"return"`)으로 결과 맵에서 꺼낸다 | :107, :280, SimpleJdbcCall:154 | 변형 A에서 이름이 OUT 파라미터 이름으로 바뀌어 **같은 키에 두 값이 실림** |
| `withReturnValue()` 프로시저의 반환 슬롯은 `{? = call}` 첫 자리이며 선언 OUT과 매칭돼야 한다 | createCallString:632-634 | 변형 B에서 매칭 성공 후 조회 실패로 예외 |
| provider별 이름 규칙(SQL Server/Sybase `@` 스트립, Oracle 대문자 폴딩)은 `parameterNameToUse`에 **캡슐화**돼 있고 컨텍스트는 그것만 호출한다 | Provider 인터페이스 :104 | L379가 `toLowerCase`만 직접 호출해 캡슐화 우회 |
| 결과 맵은 **이름 키** — 같은 이름의 OUT이 둘이면 뒤가 앞을 덮는다 | JdbcTemplate.extractOutputParameters | 결함이 아니라 전제 — 이 전제 때문에 변형 A가 "예외 없이 틀린 값"이 된다 |

## 6. 수정안

### 6.1 최소 수정 — 반환 분기의 조회를 맵과 같은 정규화로

착수 시점의 권장안이자, 실제로 채택된 안이다.

```java
// before (L376-386)
if (meta.isReturnParameter()) {
    param = declaredParams.get(getFunctionReturnName());
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
    }
    ...

// after
if (meta.isReturnParameter()) {
    // 1) 메타데이터 이름이 선언과 직접 매치된 경우(SQL Server의 @RETURN_VALUE 등)는 그 매치를 사용
    param = declaredParams.get(paramNameToCheck);
    // 2) 함수 반환 이름은 맵 키와 동일한 정규화로 조회
    if (param == null) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getFunctionReturnName())));
    }
    // 3) 최후 폴백(첫 OUT)도 동일 정규화 — 순서 의존 휴리스틱 자체는 유지
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getOutParameterNames().get(0))));
    }
    ...
```

변형별 효과: **A** — 1)은 null(이름 없는 반환 행), 2)가 `"RESULT"`->`"result"`로 hit ->
올바른 반환 파라미터, `out_status`는 자기 OUT 슬롯에만 들어감 ->
`[RESULT, AMOUNT, out_status]`. **B** — 1)이 `"return_value"`로 즉시 hit -> 예외 소멸.
두 변형 모두 **선언 순서 무관**해진다. 기존 테스트(`SimpleJdbcCallTests`의 `"return"`
소문자 선언)는 2)에서 그대로 hit — 무회귀.

(최종 커밋의 주석은 위 세 줄 대신 한 자리에 두 줄로 축약됐다 — Spring 관례상 조회마다
주석을 다는 것이 과하다는 리뷰 판단. 최종 형태는 [README.md](README.md) §4.)

### 6.2 검토했으나 채택하지 않은 대안 — 폴백 휴리스틱 강화

3)의 "첫 OUT" 폴백은 여전히 순서 휴리스틱이다. 더 정확한 규칙은 [1]단계가 함수에 이미
쓰는 것과 같은 **"메타데이터에 없는 선언 OUT"**을 고르는 것(프로시저 `withReturnValue()`에도
적용). 다만 이는 동작 확장이라 최소 수정과 분리해 판단할 항목이었고, 이 PR은 6.1만
반영했다.

### 6.3 영향 범위와 검증 계획

변경 범위는 파일 둘이고, 검증은 test-first로 두 변형의 재현과 순서 역전 가드를 함께 세운다.

- 변경 파일: `CallMetaDataContext.java` 반환 분기 + `SimpleJdbcCallTests.java` 테스트.
- 테스트(test-first): 변형 A 재현(callParameters 구성·`executeFunction` 반환값이 함수
  반환 슬롯인지) / 변형 B 재현(예외 소멸·callString `{? = call my_proc(?, ?)}`) /
  순서 역전 양성 가드(반환 먼저 선언 — 전후 green) / 기존 `add_invoice` 함수 테스트
  무회귀. 목 셋업은 `initializeAddInvoiceWithMetaData`(COLUMN_TYPE 5/1/4 스텁)를 미러.
- 실물 스모크는 목 기반(실DB 없음). 실제 결과는 [tests.md](tests.md)의 실측 요약.

### 6.4 fix 후 세 번째 조회(첫 OUT 폴백)의 도달 가능성 — 불가

L374 진입 조건은 `declaredParams.containsKey(paramNameToCheck) ||
(meta.isReturnParameter() && returnDeclared)` 두 갈래다. 전자로 들어오면 step 1이 같은
키로 조회하므로 반드시 맞고, 후자로 들어오면 `returnDeclared`를 세운 L343-350이 그
직전 L339에서 같은 규칙의 키로 맵에 넣은 파라미터의 원본 이름을
`actualFunctionReturnName`에 저장했으므로 step 2의 정규화 키가 반드시 맞는다. 따라서
**정규화된 step 1·2 아래에서 step 3은 도달 불가**다. 수정 전에는 step 1이 원본 케이스
키로 항상 빗나가서 step 3이 실제 일을 했고(그래서 변형 A가 `out_status`를 골랐다),
수정 후에는 방어적 잔재가 된다. 실측: step 3만 구 코드로 되돌려도 22/22 green.

가드 테스트로 커버할 수 없는 줄이므로 유지·삭제는 리뷰 비용과 gh-25707 계열의 계약
축소 여부로 판단했고, **유지(정규화)**를 선택했다. 판단 근거는 [README.md](README.md) §4.

## 7. 범위 밖 (같은 계열이지만 이번에 안 건드린 것)

같은 클래스·같은 계열이지만 이번 PR이 손대지 않은 항목과, 이 영역 수정이 수용된 선례를 남긴다.

- **J12** `matchInParameterValuesWithCallParameters(Object[])`의 raw AIOOBE(:594-604) — 별건.
- **#33514**(OPEN, 2024-09) Informix 함수 + `withoutProcedureColumnMetaDataAccess`
  파라미터 수 오류 — `createCallString`의 `parameterCount=-1` 슬롯 건너뛰기가 메타데이터
  미사용 경로에서 사용자 IN을 삼키는 가설. 원인 지점이 다르고 실드라이버 확인 불가 ->
  PR 본문에 "인접 리포트"로만 언급 가능, 동일 결함 주장 금지.
- **J13** SQL Server named binding의 `@` 소실 — 실드라이버 필요, 보류.
- 선례: 같은 메서드의 반환 이름 처리를 손본 커밋 "Restore original 4.x behavior for
  initialization of function return name"(2020, gh-25707 계열) — 이 영역 수정이 수용된 이력.
