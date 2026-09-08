# PR #37206 — Normalize function return parameter lookup in CallMetaDataContext

## 0. 정향

이 문서는 `spring-jdbc`의 `CallMetaDataContext.reconcileParameters()`가 저장 함수의
**반환 파라미터만 다른 규칙으로 조회하던** 결함의 해설이다. 결함 자체는 세 줄짜리
불일치지만, 그 세 줄이 만든 증상은 두 얼굴이었다 — 한쪽에서는 예외 없이 **틀린 값**이
돌아오고, 다른 쪽에서는 올바른 선언인데 **예외가 났다**. 다 읽으면 "왜 같은 한 줄이
어떤 사용자에게는 조용한 오답이고 어떤 사용자에게는 스퓨리어스 예외인가"와 "왜 수정이
동작 추가가 아니라 규칙 통일인가"를 설명할 수 있어야 한다.

상태: **머지**(2026-09-03, `ec6b9251916` — 7.0.x + main). 제출 커밋 `8f9027a995f`의
코드와 바이트 단위로 동일하고, 후속 폴리시 `ee7a0d48c56`이 테스트를 보강했다. 상세는
§7.

같은 폴더: [테스트 해설](tests.md) · [실구조](structure.md) · [착수 분석](analysis.md).
개념 문서: [저장 프로시저](../../concepts/stored-procedure/stored-procedure.md) ·
[저장 함수](../../concepts/stored-function/stored-function.md).

## 1. 배경 — 이름으로 짝을 짓는 구조와, 이름이 없는 슬롯 하나

`SimpleJdbcCall`은 사용자가 선언한 파라미터와 DB가 보고한 파라미터를 **이름으로**
짝짓는다. 사용자는 `declareParameters(new SqlOutParameter("out_status", ...))`처럼
쓰고, Spring은 `DatabaseMetaData.getProcedureColumns()`가 준 시그니처 설명서와 그
선언을 대조해 최종 호출 파라미터 목록을 만든다. 이름 표기가 DB마다 다르므로
(Oracle은 식별자를 대문자로 저장하고, SQL Server/Sybase는 파라미터에 `@`를 붙인다)
대조에 쓰는 키는 provider가 정규화한다.

```java
String paramNameToMatch = lowerCase(provider.parameterNameToUse(paramName));   // CallMetaDataContext.java:339
declaredParams.put(paramNameToMatch, param);                                   // :340
```

`lowerCase(provider.parameterNameToUse(name))` — 이 한 식이 **선언 파라미터 맵의 키를
만드는 유일한 규칙**이고, 메타데이터 쪽 이름도 같은 식으로 변환해(:371) 조회한다.
키를 만드는 곳과 조회하는 곳이 같은 식을 쓰는 한 대소문자도 `@`도 문제가 되지 않는다.

문제는 **함수의 반환 슬롯에는 이름이 없다**는 데서 시작한다. `CREATE FUNCTION
get_total(...) RETURN NUMBER`의 반환 자리는 타입만 갖고, Oracle 드라이버는 그것을
`COLUMN_TYPE=5, COLUMN_NAME=null` 행으로 보고한다([저장 함수](../../concepts/stored-function/stored-function.md)).
이름이 없으니 이름으로 짝지을 수 없고, Spring은 대신 "사용자가 선언한 OUT 중 어느
것이 반환값인가"를 따로 골라야 한다. 그 고르는 코드가 이번 무대다.
(SQL Server 프로시저의 정수 상태 코드 반환은 반대로 `@RETURN_VALUE`라는 **이름 있는**
행으로 오는데, 이것도 같은 분기를 탄다 — [저장 프로시저](../../concepts/stored-procedure/stored-procedure.md).)

## 2. 수정 전 동작 — 반환 행만 두 갈래 raw 조회

메타데이터 행을 순회하다 반환 행을 만나면, 수정 전 코드는 이렇게 선언 파라미터를
찾았다.

```java
if (meta.isReturnParameter()) {
    param = declaredParams.get(getFunctionReturnName());
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
    }
    if (param == null) {
        throw new InvalidDataAccessApiUsageException(...);
    }
```

두 조회 모두 **맵의 키 규칙과 다르다**.

- 1차 `getFunctionReturnName()`은 사용자가 선언한 **원본 표기**를 그대로 돌려준다
  (:107-109 — `actualFunctionReturnName`이 있으면 그것, 없으면 `"return"`).
  맵의 키는 소문자인데 조회는 원본 케이스이므로, 반환 파라미터를 `"RESULT"`처럼
  선언한 순간 이 조회는 **항상 빗나간다**.
- 2차 폴백은 `toLowerCase`만 적용하고 `provider.parameterNameToUse`를 건너뛴다.
  SQL Server/Sybase에서 `@`가 제거되지 않으니 `"@out_total"`은 키 `"out_total"`을
  찾지 못한다. 게다가 **"선언된 첫 OUT이 반환값"**이라는 순서 가정이 들어 있다.

즉 반환 분기만 정규화의 바깥에 있었고, 그래서 반환 파라미터의 매칭 성패가 **이름 표기와
선언 순서**에 달려 있었다. 그리고 그 순서 요구는 어디에도 문서화돼 있지 않다 —
`SimpleJdbcCallOperations.declareParameters`의 javadoc은 선언이 "메타데이터로
보충된다"고만 말한다(구형 `StoredProcedure.declareParameter`가 "DB 파라미터 목록과
같은 순서로 선언해야 한다"고 명시하는 것과 대조된다).

## 3. 문제 — 같은 세 줄, 두 개의 증상

발동 조건은 하나다: **함수(또는 `withReturnValue()` 프로시저)이면서, 반환 파라미터보다
앞에 다른 OUT 파라미터를 선언한 경우.** 반환 파라미터를 첫 OUT으로 선언하면 2차
폴백이 우연히 맞아 오늘도 정상 동작한다. 그 우연이 결함을 오래 숨겨 왔다.

### 변형 A — 조용한 오답 (Oracle 함수 + 추가 OUT)

첫 변형은 Oracle 함수에 추가 OUT을 반환 파라미터보다 먼저 선언한 경우다.

```java
new SimpleJdbcCall(dataSource).withFunctionName("get_total").declareParameters(
        new SqlOutParameter("out_status", Types.INTEGER),
        new SqlOutParameter("RESULT", Types.INTEGER));
```

1차 조회 `get("RESULT")`가 키 `"result"`를 못 찾고, 2차 폴백이 `outParamNames[0]`인
`"out_status"`를 집는다. 결과적으로 **`out_status`가 반환 슬롯을 겸직**한다. 호출
파라미터 목록에 같은 인스턴스가 두 번 들어가고, `JdbcTemplate.extractOutputParameters`가
이름을 키로 결과 맵을 만들기 때문에(:1340) 위치 3(OUT)의 값이 위치 1(반환)의 값을
덮는다. 게다가 `actualFunctionReturnName`이 `"out_status"`로 덮이므로(:392)
`executeFunction()`이 꺼내는 키도 `"out_status"`가 된다. 사용자가 선언한 `RESULT`는
목록 어디에도 없고, 예외도 경고도 없다.

### 변형 B — 스퓨리어스 예외 (SQL Server 프로시저 + 반환값)

둘째 변형은 SQL Server 프로시저에서 `@` 접두 OUT을 반환값보다 먼저 선언한 경우다.

```java
new SimpleJdbcCall(dataSource).withProcedureName("my_proc").withReturnValue().declareParameters(
        new SqlOutParameter("@out_total", Types.INTEGER),
        new SqlOutParameter("RETURN_VALUE", Types.INTEGER));
```

메타데이터의 `@RETURN_VALUE` 행은 정규화하면 `"return_value"`이고, 선언
`RETURN_VALUE`의 키도 `"return_value"`다 — **분기 진입 조건(:374)에서 이미 매치가
확인된 상태**다. 그런데 1차 조회는 그 매치를 쓰지 않고 `get("return")`을 하고(프로시저라
`actualFunctionReturnName`이 설정되지 않아 기본값), 2차 폴백은 `"@out_total"`을
소문자화만 해서 조회하므로 `@`가 남아 또 빗나간다. 그래서 올바른 선언인데
`InvalidDataAccessApiUsageException: Unable to locate declared parameter for function
return value - add an SqlOutParameter with name 'return'`으로 끝난다.

### before/after

두 변형의 관측값을 같은 축으로 비교하면 이렇다(값은 [tests.md](tests.md)의 실측).

| 변형 | 선언 순서 | fix 전 | fix 후 |
|---|---|---|---|
| A (Oracle 함수) | `out_status` -> `RESULT` | 파라미터 `[out_status, AMOUNT, out_status]`, `executeFunction` = **7**(OUT 값) | `[RESULT, AMOUNT, out_status]`, `executeFunction` = **42**(반환값) |
| A (역순) | `RESULT` -> `out_status` | `[RESULT, AMOUNT, out_status]`, 42 | 동일 (무회귀) |
| B (SQL Server 프로시저) | `@out_total` -> `RETURN_VALUE` | **InvalidDataAccessApiUsageException** | `[RETURN_VALUE, amount, @out_total]`, `{? = call my_proc(?, ?)}` |
| B (역순) | `RETURN_VALUE` -> `@out_total` | 정상 | 동일 (무회귀) |

## 4. 수정 해설 — 조회 셋을 한 규칙으로

수정은 동작을 더하지 않는다. **반환 분기의 조회를 맵의 키 규칙에 맞추는 것**이
전부다(CallMetaDataContext.java:376-385).

```java
if (meta.isReturnParameter()) {
    // Same normalization as the declaredParams keys above; the function
    // return name may have been adopted from a declared out parameter
    param = declaredParams.get(paramNameToCheck);
    if (param == null) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getFunctionReturnName())));
    }
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getOutParameterNames().get(0))));
    }
```

세 조회의 역할이 각각 다르다.

1. **`paramNameToCheck`** — 메타데이터가 이름을 준 반환 행(SQL Server `@RETURN_VALUE`)은
   이미 :371에서 정규화돼 있고 분기 진입 조건이 그 키로 매치를 확인했다. 새로 조회할
   것 없이 그 매치를 그대로 쓴다. 변형 B가 여기서 해결된다. 메타 이름이 없으면
   `paramNameToCheck`는 null이고, `LinkedHashMap.get(null)`은 null을 돌려준다
   (맵의 키는 `lowerCase`가 null을 `""`로 바꾸므로 :679-681 null 키가 존재하지 않는다).
2. **`getFunctionReturnName()`의 정규화 조회** — 이름 없는 함수 반환 행의 정규 경로다.
   `getFunctionReturnName()`은 선언 순회 단계(:343-350)가 "메타데이터에 없는 첫 OUT"을
   반환 파라미터로 채택하며 저장해 둔 **원본 표기**이므로, 같은 식으로 정규화하면
   그 파라미터를 넣을 때 쓴 키(:339)와 **구성상 반드시 같다**. 변형 A가 여기서 해결된다.
3. **첫 OUT 폴백** — 기존 휴리스틱을 그대로 두되 정규화만 맞췄다.

주석은 두 줄이다. 첫 줄은 "위 `declaredParams` 키와 같은 정규화"라는 규칙을, 둘째
줄은 리뷰에서 지적된 숨은 의존 — 2)의 반환 이름이 provider가 준 것이 아니라 **선언
OUT에서 채택된 이름**이라는 사실 — 을 밝힌다. 이 한 줄이 없으면 2)가 왜 반드시
맞는지를 코드만 보고 재구성하기 어렵다.

### 3)은 도달 불가인데 왜 남겼는가

fix 이후 3)에는 도달할 수 없다. 분기 진입 조건은 두 갈래인데, `containsKey(paramNameToCheck)`로
들어오면 1)이 같은 키로 조회하므로 반드시 맞고, `returnDeclared`로 들어오면 그
플래그를 세운 :343-350이 직전 :339와 같은 규칙의 키로 넣은 파라미터의 원본 이름을
저장했으므로 2)가 반드시 맞는다. 실측으로도 3)만 구 코드로 되돌려 놓아도 테스트
22건이 전부 green이었다 — 현 테스트가 3)을 실행하지 않는다는 뜻이다.

그래서 **가드 테스트로 고정할 수 없는 줄**이 되었고, 선택지는 "정규화한 채 유지"와
"삭제" 둘이었다. 유지를 택했다. 이 폴백은 4.x 시절 함수 반환 이름 처리 관례에서
유래한 것이라 삭제는 계약 축소가 되고, 반면 정규화한 채 남겨 두면 세 조회가 하나의
규칙 아래 있다는 사실이 코드에서 그대로 읽힌다. 도달 불가라는 판정 자체는
[analysis.md](analysis.md)의 §6.3에
근거와 함께 남겼다.

### 수용한 인접 영향

`withReturnValue()` 없이 SQL Server 프로시저에 `RETURN_VALUE`라는 OUT을 선언하고 다른
OUT을 먼저 선언하면, fix 전에는 예외가 났지만 fix 후에는 1)이 매치를 잡아 반환
파라미터가 **일반 슬롯**으로 바인딩된다(`{call my_proc(?, ?, ?)}` — 실행 시 드라이버
오류). 다만 반환 파라미터를 먼저 선언했을 때는 fix 전에도 똑같이 그랬다. 즉 새로
생긴 구멍이 아니라 기존 구멍이 두 선언 순서에 **일관되게** 적용된 것이고, 애초에
`withReturnValue()` 없이 반환 파라미터를 선언하는 것이 API 오용이다. 반환 슬롯을 쓸지
말지는 여전히 `withFunctionName()`/`withReturnValue()`가 결정한다 — PR 본문에 그
원칙 문장만 남기고 시나리오 상세는 작업 로그에 두었다. 실측은 [tests.md](tests.md)의
probe 절에 있다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다. `SimpleJdbcCallTests`에 두 변형의 재현
2건(red)과 선언 순서를 뒤집은 양성 가드 2건(전후 green), 목 헬퍼 2개를 추가했다.
fix 전 실측은 변형 A가 `["out_status", "AMOUNT", "out_status"]`, 변형 B가
`InvalidDataAccessApiUsageException` — 예측과 일치했다. fix 후 `SimpleJdbcCallTests`
22/22, `spring-jdbc` 전체 **958 tests 6 skipped 0 failures 0 errors**, checkstyle
EXIT=0. 상세는 [tests.md](tests.md).

리뷰는 듀얼 1패스였다(병렬 리뷰 -> 종합 -> 감사 -> post-fix 재점검). 채택 3건(주석
보강, PR 본문에 사용자 가시 동작 변경 명시, 테스트 파일 빈 줄 관례 복원), 기각 3건,
인접 영향 1건은 위 절에 서술한 대로 재분류했다. 재점검에서 신규 지적 0건.

## 6. 교훈

이 결함이 남긴 것은 키 규칙의 단일성, 우연히 맞는 폴백의 위험, 증상과 원인의 관계, 그리고 도달 불가 코드의 판단 기준 넷이다.

1. **키를 만드는 규칙이 하나면, 조회도 하나여야 한다.** 이 결함은 로직 오류가 아니라
   같은 맵에 대해 규칙이 둘이었던 문제다. 컴파일러도 타입도 잡아 주지 않는 종류라,
   `lowerCase(provider.parameterNameToUse(x))`라는 식이 코드에 몇 번 등장하는지를
   세어 보는 것이 실제 탐지 방법이었다.
2. **우연히 맞는 폴백은 결함을 숨긴다.** "선언된 첫 OUT"이라는 폴백이 흔한 사용 형태
   (반환 파라미터를 먼저 선언)에서 계속 맞아떨어졌기 때문에, 1차 조회가 Oracle에서
   **항상** 빗나간다는 사실이 오래 드러나지 않았다.
3. **같은 한 줄이 조용한 오답도, 스퓨리어스 예외도 만든다.** 폴백이 잘못 맞으면
   무예외 오답, 안 맞으면 예외다. 결함을 증상 단위로 쫓으면 별개 버그로 보이지만
   원인 단위로 쫓으면 하나다.
4. **도달 불가 코드는 테스트로 지킬 수 없다.** 가드 테스트를 쓸 수 없다는 사실이
   확인된 순간, 유지·삭제는 검증이 아니라 계약 이력으로 판단할 문제가 된다.

## 7. 머지와 후속 polish

머지는 `ec6b9251916`으로 7.0.x에 적용됐고(적용 2026-09-02), 이후 `136dddb67d1`
("Merge branch '7.0.x'")를 타고 main으로 올라왔다. **크레딧은 유지됐다** — author가
`junhyeong9812 <pickjog@gmail.com>`, author date가 제출일 그대로이고 `Signed-off-by`도
남아 있다.

**코드는 무변경이다.** 제출 커밋 `8f9027a995f`와 머지 커밋의 두 대상 파일
(`CallMetaDataContext.java`, `SimpleJdbcCallTests.java`)을 직접 비교하면 차이가 없다.
바뀐 것은 커밋 메시지뿐이고, 그 수정도 세 갈래로 정리된다. 메서드 이름에 괄호를 붙여
`reconcileParameters` -> `reconcileParameters()`, `toLowerCase` -> `toLowerCase()`,
`executeFunction` -> `executeFunction()`으로 통일했다. JDBC 용어 표기를 `out parameter`
-> `OUT parameter`로 대문자 고정했다. 그리고 이슈를 닫는 트레일러 `Closes gh-37206`을
붙였다. 서술 내용과 문단 구성은 손대지 않았으므로, 제출 시점에 메시지를 세 문단
(현상 -> 원인 -> 수정)으로 짠 판단 자체는 통과한 셈이다.

폴리시 커밋은 그다음이다. `ee7a0d48c56`("Polish contribution", See gh-37206, Sam
Brannen, 2026-09-03)이 **테스트만** 건드렸다. 기존 파일 `CallMetaDataContextTests`에
같은 결함을 겨냥한 테스트 2건과 목 헬퍼 1개를 더했고(55줄 추가), 우리가 넣은
`SimpleJdbcCallTests`의 4건에는 `@Test  // gh-37206` 주석과 빈 줄 정리만 적용했다
(9줄 변경, 단언과 픽스처는 그대로).

핵심은 검증 층위를 하나 더 깐 것이다. 우리 테스트 4건은 `SimpleJdbcCall`을 통과하는
**end-to-end 경로**를 검증했다 — `compile()` -> callString 생성 -> `executeFunction()`
반환값까지. 폴리시가 추가한 2건은 같은 계약을 `CallMetaDataContext`에 직접 대고
검증한다. `context.setFunction(true)` -> `setProcedureName("GET_TOTAL")` ->
`initializeMetaData(dataSource)` -> `processParameters(parameters)`를 손으로 호출한 뒤
`getCallParameters()`의 이름 세 개만 본다. 결함이 사는 클래스가
`CallMetaDataContext.reconcileParameters()`이므로, 그 클래스의 단위 테스트 파일에
직접 걸어 두면 나중에 이 로직을 만지는 사람이 `SimpleJdbcCall` 쪽까지 찾아가지 않아도
계약을 본다. 테스트 이름도 그 층위를 그대로 말한다 —
`reconcileParametersMatchesFunctionReturnParameterDeclaredBeforeOutParameter`.

폴리시가 우리 배치를 **대체하지 않고 병렬로 추가했다**는 점도 기록해 둘 만하다. 통합
경로의 재현(반환값이 42냐 7이냐)은 단위 테스트가 표현할 수 없고, 반대로 단위 테스트는
결함의 소재를 좁혀 준다. 상세는 [tests.md](tests.md) 마지막 절.
