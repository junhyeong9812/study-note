# PR #37206 — 무대의 실구조와 워크플로우

> PR #37206의 무대가 되는 실구조·워크플로우. 문제와 수정은 [README.md](README.md),
> 테스트는 [tests.md](tests.md), 착수 시점 분석은 [analysis.md](analysis.md) 참조.
>
> 기준: 로컬 HEAD `8f9027a995f`(브랜치 `fix/callmetadata-function-return-lookup` =
> upstream main `7daf1013aa8` 리베이스 + fix 커밋). **이 시점의
> `CallMetaDataContext.java`에는 이미 수정이 반영돼 있다** — 아래 file:line은
> "수정 후" 좌표이고, 2절의 수정 전 워크플로우는 커밋의 `-`쪽으로 재구성한 것이다.

## 1. 무대 — 실구조

이 결함의 무대는 **`SimpleJdbcCall`이 컴파일될 때 딱 한 번 도는 대조 루프**다.
사용자 선언과 DB 메타데이터를 맞춰 최종 호출 파라미터 목록을 만드는 그 루프가
`CallMetaDataContext.reconcileParameters()` 하나이고, 그 산출물이 하류 전부의 입력이
된다. 계층을 위에서 아래로 그리면 이렇다.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ SimpleJdbcCall (공개 빌더 API)          core/simple/SimpleJdbcCall.java       │
│   withProcedureName()  → setFunction(false)                          :87-91  │
│   withFunctionName()   → setFunction(true)                           :93-98  │
│   withReturnValue()    → setReturnValueRequired(true)               :112-116 │
│   declareParameters()  → addDeclaredParameter()                     :118-126 │
│   executeFunction()    → doExecute(args).get(getScalarOutParameterName())    │
│                                                                     :152-156 │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────────────────────┐
│ AbstractJdbcCall (compile/execute 골격)  core/simple/AbstractJdbcCall.java    │
│   private final CallMetaDataContext callMetaDataContext              :63     │
│   compile() → compileInternal()                              :294 → :325-343 │
│   doExecute(...) → executeCallInternal() → JdbcTemplate.call()      :394-426 │
│   getCallParameters() → context.getCallParameters()                 :441-442 │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────────────────────┐
│ CallMetaDataContext (이번 무대)   core/metadata/CallMetaDataContext.java      │
│                                                                               │
│  [상태]                                                                       │
│   List<SqlParameter> callParameters     :70  ← reconcile 의 산출물             │
│   String  actualFunctionReturnName      :73  ← 반환값을 부르는 이름(@Nullable) │
│   List<String> outParameterNames        :79  ← 선언 OUT 의 원본 표기, 선언 순서 │
│   boolean function / returnValueRequired :82 / :85                            │
│   CallMetaDataProvider metaDataProvider :94                                   │
│                                                                               │
│  [흐름]                                                                       │
│   initializeMetaData(ds) → CallMetaDataProviderFactory                :244    │
│   processParameters(list) → reconcileParameters(list)     ★ 결함 위치 :305,:312│
│   createCallString()  ({? = call ...} 조립)                            :615    │
│   getFunctionReturnName() = actualFunctionReturnName ?: "return"       :107    │
│   getScalarOutParameterName() = isFunction ? 위 값 : outParameterNames[0] :280 │
│   lowerCase(s) = (s != null ? s.toLowerCase(ROOT) : "")               :679    │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────────────────────┐
│ CallMetaDataProvider 계층 (DB별 이름 규칙·메타데이터 공급)                      │
│   interface  parameterNameToUse(String)         CallMetaDataProvider.java:104 │
│              byPassReturnParameter(String)                              :175 │
│   Generic    parameterNameToUse = identifierNameToUse   Generic:162-165       │
│              identifierNameToUse: storesUpper/Lower 폴딩 또는 원본  :276-289   │
│              processProcedureColumns → CallParameterMetaData 목록      :294   │
│   Oracle     metaDataCatalogNameToUse/SchemaNameToUse 재정의     Oracle:62-71 │
│   SqlServer  "@" 스트립 후 super,  byPass "@RETURN_VALUE"   SqlServer:44-65  │
│   Sybase     "@" 스트립 후 super,  byPass "RETURN_VALUE"       Sybase:45-66  │
│   Postgres   byPass "returnValue"                            Postgres:39,:84 │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    v
┌──────────────────────────────────────────────────────────────────────────────┐
│ JdbcTemplate.extractOutputParameters(cs, params)   core/JdbcTemplate.java:1311│
│   sqlColIndex = 1                                                     :1315  │
│   for param in params: if SqlOutParameter                                     │
│        results.put(outParam.getName(), cs.getObject(sqlColIndex))     :1340  │
│        ⇒ 값은 위치로 오고, 키는 목록의 이름이 붙는다. 같은 이름이면 뒤가 덮는다.  │
└──────────────────────────────────────────────────────────────────────────────┘
```

이 그림에서 읽어야 할 사실은 하나다. **`reconcileParameters`가 만든 목록 하나가
호출문의 슬롯 순서, 바인딩 위치, 결과 맵의 키를 전부 결정한다.** 그래서 그 목록이
어긋나면 하류 셋이 동시에 어긋나고, 반대로 그 한 곳만 맞추면 하류는 자동으로
정합해진다 — 수정이 세 줄로 끝난 이유다.

`CallMetaDataContext`를 인스턴스로 보유하는 곳은 `AbstractJdbcCall` 하나뿐이다(:63 —
그 밖에서는 `CallMetaDataProviderFactory`가 provider를 만들 때 인자로 받을 뿐이다). 즉 이 결함의
노출면은 정확히 `SimpleJdbcCall` 계열이고, 구형 `org.springframework.jdbc.object`의
`StoredProcedure` 계열은 메타데이터 대조를 하지 않으므로 이 경로에 들어오지 않는다.

## 2. 수정 전 동작 워크플로우

`compile()`이 한 번 돌면 호출문과 파라미터 목록이 확정되고, 이후 실행은 그 목록을
읽기만 한다. 두 단계로 나눠 본다.

```
[컴파일]
SimpleJdbcCall.withFunctionName("get_total").declareParameters(p1, p2)
  └─ .compile()                                        AbstractJdbcCall:294
       └─ compileInternal()                                          :325
            ├─ callMetaDataContext.initializeMetaData(dataSource)     :328
            │     └─ 제품명으로 provider 결정 → getProcedureColumns() 로 시그니처 로딩
            ├─ declaredRowMappers → createReturnResultSetParameter    :331
            ├─ callMetaDataContext.processParameters(declaredParameters) :332
            │     └─ reconcileParameters(...)  ★ 이 안에서 결정이 난다  Context:312
            │           └─ this.callParameters = 결과 목록
            ├─ callString = createCallString()                        :334
            │     └─ isFunction() || isReturnValueRequired() → "{? = call " + parameterCount = -1
            │                                                  Context:635-638
            └─ new CallableStatementCreatorFactory(callString, getCallParameters()) :339

[실행]
executeFunction(Integer.class, 5)                        SimpleJdbcCall:154
  └─ doExecute(args)                                   AbstractJdbcCall:394
       ├─ matchInParameterValuesWithCallParameters(args)   callParameters 순서로 IN 값 매칭
       ├─ executeCallInternal(params) → JdbcTemplate.call(csc, getCallParameters())  :425
       │     └─ extractOutputParameters(cs, params)      JdbcTemplate:1311
       │           results.put(param.getName(), cs.getObject(sqlColIndex))    :1340
       └─ .get(getScalarOutParameterName())                Context:280
             isFunction() ? getFunctionReturnName() : outParameterNames[0]
```

수정 전의 결함은 이 그림의 `reconcileParameters` 안쪽에서만 일어나지만, 증상은 실행
단계에서 관측된다. 변형 A를 이 워크플로우에 얹으면 이렇게 전파된다.

```
reconcile 결과   [out_status, AMOUNT, out_status]     ← 같은 인스턴스가 두 자리에
   │
   ├─ createCallString  "{? = call GET_TOTAL(?, ?)}"   ← 슬롯 수는 정상. SQL 은 성공한다.
   │
   ├─ extractOutputParameters
   │     위치 1 (반환) → results.put("out_status", 42)
   │     위치 3 (OUT)  → results.put("out_status", 7)   ← 같은 키, 뒤가 앞을 덮는다
   │
   └─ getScalarOutParameterName() = getFunctionReturnName() = "out_status"
          (reconcile 의 :392 가 actualFunctionReturnName 을 덮어썼기 때문)
          ⇒ executeFunction() 이 7 을 돌려준다. 예외도 경고도 없다.
```

## 3. reconcileParameters 내부 — 두 번의 순회와 반환 분기

메서드는 `[0] 메타 이름 수집 -> [1] 선언 순회 -> [2] 메타데이터 미사용이면 조기 반환
-> [3] 메타데이터 순회`의 네 구간이다. 결함은 [3]의 반환 행 분기 안에 있었다.

```
reconcileParameters(parameters)                                          :312
 │
 ├─[0] metaDataParamNames ← 비-반환 메타 파라미터 이름을 lowerCase 로     :321-326
 │        "이 선언이 실제 컬럼인가"를 판별할 참조표
 │
 ├─[1] 선언 파라미터 순회 (사용자가 declareParameters 로 넘긴 순서)       :328-353
 │        paramNameToMatch = lowerCase(provider.parameterNameToUse(name)) :339  ★ 키 규칙
 │        declaredParams.put(paramNameToMatch, param)                    :340
 │        if (param instanceof SqlOutParameter):                         :341
 │            outParamNames += 원본 이름                                  :342
 │            if (isFunction() && 키 ∉ metaDataParamNames && !returnDeclared):  :343
 │                 actualFunctionReturnName = 원본 이름 ; returnDeclared = true  :348-349
 │                 ← "메타데이터에 없는 첫 OUT = 함수의 반환값" 휴리스틱
 │        setOutParameterNames(outParamNames)                            :354
 │
 ├─[2] provider.isProcedureColumnMetaDataUsed() 가 false 면                :357-360
 │        선언만으로 목록을 만들어 반환 (withoutProcedureColumnMetaDataAccess 경로)
 │
 └─[3] 메타데이터 파라미터 순회 (DB 가 준 순서 = 실제 슬롯 순서)          :367-464
          paramNameToCheck = 이름이 있으면 lowerCase(parameterNameToUse(이름))  :368-372
                             이름이 없으면 null 그대로
          paramNameToUse   = parameterNameToUse(이름)   ← 새로 만들 때 쓸 표기   :373
          │
          ├─ 진입: declaredParams.containsKey(paramNameToCheck)
          │        || (meta.isReturnParameter() && returnDeclared)              :374
          │     ├─ meta.isReturnParameter() → ★ 반환 분기 (아래 상세)           :376-394
          │     └─ 아니면 param = declaredParams.get(paramNameToCheck)          :396
          │        workParams += param                                          :399
          │
          └─ 미진입(선언에 없음):                                                :406-463
                반환 행이면 byPassReturnParameter 판단 후 기본 OUT 생성          :407-427
                아니면 방향에 따라 기본 IN / OUT / INOUT 생성                    :428-462
```

### 반환 분기 — 수정 전과 수정 후

결함이 살던 분기를 수정 전후로 나란히 그리면 조회가 둘에서 셋으로 늘어난 것이 아니라 규칙이 하나로 모인 것임이 보인다.

```
                     meta.isReturnParameter() 행에 도달
                                  │
      ┌───────────────────────────┴───────────────────────────┐
  선언에 반환 파라미터가 있다(:374 진입)                    없다 → 기본 OUT 생성(:415-426)
      │
      v
  [수정 전]                                   [수정 후 :376-385]
  ① get( getFunctionReturnName() )            ① get( paramNameToCheck )
       원본 표기 — 키 규칙과 불일치                 이미 :371 에서 정규화된 키
       │                                            (이름 없는 반환 행이면 null → miss)
       ├ hit → 정상                                 │
       └ miss                                       ├ hit → 변형 B 해결
           │                                        └ miss
           v                                            v
  ② get( outParamNames[0].toLowerCase() )      ② get( lowerCase(parameterNameToUse(
       parameterNameToUse 미적용                        getFunctionReturnName() )) )
       "첫 OUT = 반환값" 가정                          [1]이 채택한 원본 이름을 :339 와
       │                                               같은 식으로 정규화 → 구성상 hit
       ├ hit ─ 우연히 맞음 → ★ 변형 A(오답)            │
       └ miss → ★ 변형 B(예외 :387)                    ├ hit → 변형 A 해결
                                                       └ miss
                                                           v
                                              ③ get( lowerCase(parameterNameToUse(
                                                     outParamNames[0] )) )
                                                     기존 휴리스틱, 정규화만 정렬
                                                     (fix 후에는 도달 불가 — README §4)
                                                       │
                                                       └ miss → InvalidDataAccessApiUsageException :387
```

수정 후 분기에서 `param`을 찾으면 `actualFunctionReturnName = param.getName()`으로
확정된다(:392). 이 대입이 결과 맵에서 값을 꺼낼 키를 정하므로, 여기서 잘못된
파라미터를 고르면 **호출문·바인딩·결과 키가 한꺼번에 어긋난다**(2절의 전파도).

## 4. 그릇 세 개 — 무엇이 어디에 담기는가

이 메서드를 읽을 때 헷갈리는 것은 "파라미터 목록"처럼 보이는 그릇이 셋이고, 각각
담는 것도 키도 순서도 다르다는 점이다. 고정 축으로 비교하면 이렇다.

| 그릇 | 담기는 것 | 키 / 순서 | 만들어지는 곳 | 소비처 |
|---|---|---|---|---|
| `provider.getCallParameterMetaData()` | DB가 보고한 시그니처 행(`CallParameterMetaData`) — 이름·방향·타입 | 순서 = DB가 준 순서 = **실제 슬롯 순서**. 이름은 DB 표기(함수 반환은 null) | provider 생성 시 `processProcedureColumns`(Generic:294) | [0]의 참조표, [3]의 순회 대상 |
| `declaredParams` | 사용자가 선언한 `SqlParameter` 원본 인스턴스 | 키 = `lowerCase(parameterNameToUse(원본 이름))`(:339~340). 순서는 선언 순서지만 **의미 없음**(조회용 맵) | [1] 선언 순회 | [3]의 조회 대상 |
| `workParams` -> `callParameters` | 최종 호출 파라미터 — 선언에서 **채택**된 인스턴스와 메타데이터에서 **생성**된 인스턴스가 섞임 | 순서 = 메타데이터 순서 | [3]에서 누적, :466 반환 -> :306 대입 | `createCallString`·바인딩·`extractOutputParameters` |

여기에 보조 그릇이 둘 더 있다. `metaDataParamNames`는 [1]이 "이 선언 OUT이 실제
컬럼인가, 아니면 반환값인가"를 판별할 때만 쓰는 소문자 이름 목록이고,
`outParamNames`(-> `outParameterNames` 필드)는 선언 OUT의 **원본 표기**를 선언 순서로
담는다. 결함의 폴백이 참조하던 `outParamNames[0]`이 바로 이 그릇의 첫 원소이고,
"첫 번째로 선언된 OUT"이라는 것 외에 아무 의미도 보장하지 않는다.

세 그릇의 관계를 변형 A로 채워 보면 결함이 한눈에 보인다.

```
메타데이터    [ (이름 null, 반환) , (amount, IN) , (out_status, OUT) ]
declaredParams { "out_status" → SqlOutParameter("out_status"),
                 "result"     → SqlOutParameter("RESULT")          }
outParamNames  [ "out_status", "RESULT" ]        ← 0번째가 반환이 아니다
actualFunctionReturnName = "RESULT"              ← [1]이 채택

수정 전 workParams  [ out_status , AMOUNT , out_status ]   ← RESULT 가 사라졌다
수정 후 workParams  [ RESULT     , AMOUNT , out_status ]
```

## 5. 스프링 전역에서의 자리

`CallMetaDataContext`는 `spring-jdbc`의 **저장 루틴 호출 계열에서 "선언과 DB 사실을
합의시키는" 유일한 지점**이다. 사용자가 전부 선언하는 구형 API와, 메타데이터로
보충받는 신형 API의 차이가 정확히 이 클래스의 유무다.

```
[구형]  org.springframework.jdbc.object.StoredProcedure  (→ SqlCall → RdbmsOperation)
          declareParameter(...) 를 DB 파라미터 순서대로 직접 나열
          javadoc: "Calls to declareParameter must be made in the same order as
                    they appear in the database's stored procedure parameter list."
                                                          StoredProcedure.java:88-89
          ⇒ 순서 의존이 계약으로 명시돼 있다. 메타데이터 대조 없음 = 이 결함과 무관.

[신형]  org.springframework.jdbc.core.simple.SimpleJdbcCall  (→ AbstractJdbcCall)
          declareParameters(...) 는 선택 — "will be supplemented with any parameter
          information retrieved from the database meta-data"
                                            SimpleJdbcCallOperations.java:74-84
          ⇒ 순서 요구가 없다. 슬롯 순서는 메타데이터가 정한다.
             그런데 반환 파라미터만 실제로는 순서에 의존하고 있었다 = 이 PR이 고친 것.
```

두 javadoc의 대비가 이 PR의 계약 근거다. 신형 API는 "순서는 우리가 맞춰 준다"고
약속했는데 반환 파라미터에서만 그 약속이 지켜지지 않았고, 그 예외는 어디에도
문서화돼 있지 않았다. 수정은 새 동작을 만든 것이 아니라 **이미 문서화된 계약을
반환 분기까지 확장**한 것이다.

영향권은 `SimpleJdbcCall`을 쓰면서 반환 슬롯을 갖는 호출 전부다 — `withFunctionName()`
함수 호출(Oracle·PostgreSQL 등)과 `withReturnValue()` 프로시저 호출(SQL Server·Sybase).
그중에서도 **반환 파라미터를 명시적으로 선언하고, 그보다 앞에 다른 OUT을 선언한**
경우만 증상이 나타난다. 반환 파라미터를 선언하지 않으면 [3]의 미진입 갈래가 기본
OUT을 만들어 주므로(:415-426) 이 분기 자체를 타지 않는다.

## 6. 관련 개념

이 무대를 이해하는 데 필요한 배경은 이미 문서화돼 있으므로 링크로 연결한다.

- [저장 함수](../../concepts/stored-function/stored-function.md) — 이름 없는 반환 슬롯이 왜 존재하고,
  Spring이 그 이름을 어떻게 지어내는지. 1절의 `actualFunctionReturnName`과 3절 [1]의
  채택 휴리스틱이 여기서 나온다. 변형 A(조용한 오답) 갈래의 배경.
- [저장 프로시저](../../concepts/stored-procedure/stored-procedure.md) — 반환 슬롯이 없는 호출 대상과,
  그 예외인 SQL Server의 정수 상태 코드(`@RETURN_VALUE`). 변형 B(스퓨리어스 예외)
  갈래의 배경이자, `byPassReturnParameter`가 왜 provider마다 다른지의 근거.
- [analysis.md](analysis.md) — 착수 시점에 작성한 전체 메서드 그래프와 이름표 사전.
  "같은 이름이 네 가지 표기로 돌아다닌다"는 혼란을 표로 정리한 §2.5가 이 문서 4절의
  전신이다.
