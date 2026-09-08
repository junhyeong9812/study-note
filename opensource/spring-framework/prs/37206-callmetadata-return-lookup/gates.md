# PR #37206 — 이해 게이트 기록

> 출처: 세션 1761423a (2026-08-25~27), 작업 폴더 `docs/plans/2026-08-27/j5-callmetadata-return-reconcile/`.
> 모드 lazy — 매 diff마다 사용자가 주관식으로 설명하고 독립 판정 워커가 pass/fail을 매긴다. 최대 2회, 2회째 fail은 정답을 제시하고 통과 처리한다.
> 답변은 대화에 남은 원문 그대로 옮겼다(오타·비문 포함). 판정과 정답은 대화에 기록된 것만 적었고, 기록에 없는 내용은 추가하지 않았다.
> 판정 워커 원문은 세션 JSONL의 서브에이전트 기록(`subagents/agent-<task-id>.jsonl`의 최종 메시지)에서 직접 회수했다.

## 게이트 목록

게이트는 계획 1건과 diff 3건으로 모두 네 번 있었다.

| 번호 | 대상 | 시도 | 최종 판정 |
|---|---|---|---|
| G0 | 계획 게이트 (analysis.md 3~6절 — 변형 A의 하류 사슬 + 수정안 3단계의 역할 분담) | 2 | fail-통과처리 (2/2) |
| G1 | diff 01 — `SimpleJdbcCallTests` 재현·가드 테스트 4건 (T1~T4, red 2 + green 2) | 2 | pass (통과 처리, 2/2) |
| G2 | diff 02 — `CallMetaDataContext.reconcileParameters` 반환 분기 조회 3줄 | 2 | pass (통과 처리, 2/2) |
| G3 | diff 03 — 리뷰 반영 주석 2줄 + 테스트 파일 빈 줄 관례 | 2 | pass (통과 처리, 2/2) |

작업 브리핑에는 게이트가 3개로 되어 있었으나, 대화 기록에는 diff 게이트 3개 앞에 계획 게이트가 하나 더 있어 G0으로 함께 남긴다. 네 게이트 모두 1회차 fail, 2회차 통과 처리로 동일한 패턴이었다.

---

## G0 — 계획 게이트 (fix 착수 전, analysis.md 기준)

브랜치 `fix/callmetadata-function-return-lookup` 분기 직후, 코드를 건드리기 전에 설계 이해를 확인한 게이트다.

**질문** (원문)

> 1. **변형 A가 "예외 없이 틀린 값"이 되는 경로**: L377의 raw 조회가 왜 miss하고(키는 어떻게 만들어졌고 `getFunctionReturnName()`은 무엇을 돌려주는지), L379 폴백이 무엇을 고르며, 그 결과가 `callParameters`·결과 맵을 거쳐 `executeFunction()` 반환값까지 어떻게 이어지는지를 단계로 설명해 주세요. (힌트: 결과 맵의 **키가 이름**이라는 점이 마지막 고리입니다)
> 2. **수정안 6.1의 세 단계가 각각 어느 변형을 막는가**: (1) `paramNameToCheck` 우선 조회는 왜 변형 B를 바로 해결하고, 그런데 변형 A에는 왜 (2)(`getFunctionReturnName()`의 정규화 조회)가 따로 필요한가요? (힌트: Oracle 메타데이터의 반환 행은 **이름이 null**입니다)

**시도 1 — 답변** (사용자 원문)

> 우선 1번 SqlOutParameter에서는 원본 객체 RESULT로 저장하지만, raw조회를 할때는 생성한 key의 lowerCase로 인해 result로 저장하여 서로 일치하지 않는 오류가 발생한다. 그리고 이때 outParamNames에 대해서, 파라미터가 여러개라면 0번째에 그 파라미터가 없을수도 있는거 아니야 그리고 수정에서 1번 메타데이터 이름이 선언과 직접 매칭이 되는 케이스라는데, 아 어노테이션의 선언과 실제 파라미터 선언이 일치하는 케이스는 바로 매치시키고,
> 그 후 함수 반환 이름은 맵 키와 동일한 정규화로 조회한다 로워케이스를 적용해서 같은 로워케이스로 확인하도록, 처리한다는거네

**판정 1** — fail (1/2)

판정 워커 결과 원문:

> {fail, 부족점: (1) 키 정규화 불일치(miss)까지는 맞지만, 그 다음 폴백이 어떤 파라미터를 반환 슬롯에 채택하고 그것이 callParameters·결과 맵·executeFunction()까지 어떻게 흘러가 "예외 없이 틀린 값"이 되는지 하류 경로 서술이 없음("0번째가 아닐 수도"는 되물음에 그침). (2) 두 조회 단계가 각각 무엇을 하는지는 짚었으나, 왜 (1)만으로 변형 A를 못 잡고 (2)가 따로 필요한지(반환 메타 행의 특성)와 변형 B가 어느 단계에서 해결되는지 역할 분담 이유가 빠짐.}

계획 게이트는 판정 워커가 정답 비노출 형식(`{pass|fail, 부족점 1~2줄}`)으로만 답하도록 되어 있어, diff 게이트들보다 판정문이 짧다.

**시도 2 — 답변** (사용자 원문)

> a에서는 RESULT,out_status이지만 이때 b에서 키로 채울때 result,out_status로 lowerCase로 변환되서 채우잖아? 그래서 C에서 매핑이 안된다는거잖아? 아 paramNameToCheck자체는 메타데이터의 반환 행에 이름을 반환하니깐 null이 되고,
> 2에서는 해당 함수의 이름을 반환받는다는건가. 2번에서? 그런데 getFunctionReturnName()과 paramNameToCheck에 대한 설명은 analysis에 왜없어? 이런걸 각 어떤역할을 하는지 적으라는거였는데?

**판정 2** — fail-통과처리 (2회차 규칙)

판정 워커 결과 원문 요약:

- (1)은 틀림. 결과 맵의 키는 `outParam.getName()`, 즉 **원본 표기**이며 lowerCase 변환은 하류 실패의 원인이 아니다. 실제 사슬은 L379 폴백이 `out_status`의 `SqlOutParameter`를 반환 슬롯에 채택 -> 같은 인스턴스가 OUT 메타 행에서 다시 추가되어 `callParameters=[out_status, AMOUNT, out_status]`가 되고 `RESULT`는 소실 -> `extractOutputParameters`가 이름을 키로 `results.put`하므로 위치 3(OUT 값)이 위치 1(반환값)을 덮어씀 -> `executeFunction()`이 `getScalarOutParameterName()="out_status"`로 OUT 값을 반환.
- (2)는 실질 통과. "반환 행 이름이 null -> `paramNameToCheck`가 null -> step 1의 `declaredParams.get` miss -> step 2가 `getFunctionReturnName()`(1단계에서 기록된 `"RESULT"`)을 맵과 같은 정규화로 조회해 hit"를 짚었다. 다만 변형 B(SQL Server)는 반환 행 이름이 `"@RETURN_VALUE"`라 `paramNameToCheck="return_value"`가 선언 키와 이미 매치되어 step 1에서 끝난다는 대비가 빠졌다.
- 문서 비판(이름표 역할 사전 부재)은 정당한 요청으로 인정되어 판정 외로 분류. `analysis.md` 2.5절로 반영.

**정답 정리**

두 질문의 답을 재구성하려면 먼저 이름표별로 무엇을 들고 있는지를 고정해야 한다.

| 이름표 | 무엇인가 | 변형 A에서의 값 |
|---|---|---|
| `declaredParams` | 선언 파라미터 맵. 키 = `lowerCase(provider.parameterNameToUse(원본))` (L339), 값은 원본 표기 유지 | `{out_status -> P1, result -> P2(RESULT)}` |
| `getFunctionReturnName()` | `actualFunctionReturnName`이 있으면 그것(원본 표기), 없으면 `"return"` (L107-108) | `"RESULT"` — 키 `"result"`와 불일치 |
| `outParamNames` | 선언 OUT의 원본 표기, 선언 순서 | `["out_status", "RESULT"]` — 0번째가 반환이 아님 |
| `paramNameToCheck` | 메타데이터 행 이름에 선언 맵과 같은 정규화를 적용한 조회 키 (L371) | 반환 행은 null (Oracle 함수 반환은 무명) |
| `callParameters` | 메타 순서로 쌓인 최종 목록. SQL 슬롯·바인딩·결과 키를 모두 결정 | 버그 시 `[P1, AMOUNT, P1]` |

하류 사슬(대화에 기록된 형태 그대로):

```
폴백이 P1(out_status)을 반환 슬롯에 채택
  -> 뒤의 OUT 메타 행에서 P1이 또 추가 -> callParameters = [P1, AMOUNT, P1]   (RESULT는 어디에도 없음)
  -> 결과 맵: put("out_status", 슬롯1의 함수 반환값) 다음 put("out_status", 슬롯3의 OUT 값)  <- 같은 키, 뒤가 앞을 덮음
  -> executeFunction()이 getScalarOutParameterName()="out_status"로 꺼냄 -> OUT 값
```

---

## G1 — diff 01 (재현 테스트 4건)

대상 diff: `SimpleJdbcCallTests`에 헬퍼 2개(`initializeGetTotalFunctionWithMetaData`, `initializeSqlServerProcedureWithReturnValue`)와 테스트 4건 추가. T1(변형 A)·T3(변형 B)는 red, T2·T4는 가드로 전후 green.

**질문** (원문)

> 1. T2·T4(가드)는 왜 **fix 전에도 green**인가요? 현행 코드의 폴백(L379)이 그 선언 순서에서는 무엇을 집어서 우연히 맞는지 설명해 주세요. 그리고 이 가드 2건이 fix 후에 지키는 것은 무엇인가요?
> 2. T1의 단언 `containsExactly("RESULT", "AMOUNT", "out_status")`에서 **가운데 `AMOUNT`가 대문자**인 이유와, 마지막이 `out_status`(소문자)인 이유는 각각 무엇인가요? (힌트: 둘은 태어난 곳이 다릅니다 — 하나는 메타데이터에서 만든 기본 파라미터, 하나는 사용자 선언)

**시도 1 — 답변** (사용자 원문)

> 아 select가 아닌 cud같은 경우 리턴값이 지정안된 케이스가 있을꺼고 이 케이스가 항상 문제가 된다는거네? 이 내용도 analysis에 배경지식으로 필요하겠네.
> 1. 폴백에 문제가 없는 지 보는건데 이때 애초에 사용자가 지정한 메타데이터를 바로 읽어들여서 green인 이유인거고 어차피 바꾼 후에도 1번과정에선 null이고 2번에서 사용자 지정으로 채워지기에 그대로 지켜지는 것 즉 사용자가 지정한 내용으로 그대로 매핑이 되는지 이 부분이 지켜지는지 보기 위함이며, 대소문자가 서로 다른 케이스의 문제는 따로 봐야된다느거네
> 2.amount인 경우 기존 컬럼 값 자체가 대문자라서 그대로 대문자로 표시,out_status는 소문자인ㄱ 이유가 디클리어파라미터로 소문자 이름으로 정의되었기 때문에,

**판정 1** — verdict: fail

판정 워커 원문 요약:

- Q1: "가드 = 기존에 통하던 선언 순서가 fix 후에도 유지되는지 본다"는 취지와 T2에서 사용자 선언명으로 매핑되는 점은 절반 인정. 그러나 fix 전 green의 실제 메커니즘이 틀렸다 — 현행 코드에서 "사용자 지정 이름을 바로 읽어들이는" 1차 조회는 T2·T4 둘 다 실패하며 green은 그 다음 줄에서만 나온다. 또 "1번 과정에선 null"은 두 테스트에 다 적용되지 않는다 — T4(SQL Server)에서 메타 `COLUMN_NAME`이 `"@RETURN_VALUE"`일 때 `paramNameToCheck`가 실제로 무슨 문자열이 되는지 다시 확인하라. (참고로 T4는 `isFunction()`이 false라 `returnDeclared`가 어떻게 되는지도 함께 볼 것.)
- Q2: `out_status`가 소문자인 이유(선언한 `SqlParameter` 객체가 그대로 재사용됨)는 정확. 반면 `AMOUNT`의 이유는 사실과 다르다 — 스텁의 `COLUMN_NAME` 값을 직접 보라(`SimpleJdbcCallTests` L420). 대문자로 바뀌는 진짜 경로(어느 provider의 어느 메서드가 어떤 `DatabaseMetaData` 스텁 값 때문에 그렇게 만드는지)가 답변에 없다.

**시도 2 — 답변** (사용자 원문)

> 우선 프로시저와 함수 각각 개념문서로 study폴더 내에 concepts문서에 각각 마크다운문서로 설명좀 써줄래? 이 둘의 차이와 이로 이러한 특성에 따라 위 내용이 갈리는걸 알아야되겠다는거구나.
> T2는 RESULT를 첫번째로 선언 T4에서는 아웃토탈을 두번쨰로 선언했네.
> 우선 1차에서는 아 우리가 직접 입력한 마라미터 값을 파라미터로 넣고, 해당 이름 즉 RESULT를 가지고 디클리어 파람에서 보내면 null이 되지않나? 일치하는게 안나올텐데?
>  2차에서 RESULT가 도달이 아 null일때니깐, RESULT가 result가 되겠네.  2차에서 그리고, else에서 어노테이셔으로 시작하면 RETURN_VALUE라는 값으로 반환 되겠네.
> 아 sqlOut에서 이미 비교할때 out_status를 직접 입력해서 일치가 되었고, 그래서 파라미터가 null이 아니라 그런건데 어마운트는 없으니 그대로 if 분기로 들어가서
> else if (isStoresUpperCaseIdentifiers()) {
>       return identifierName.toUpperCase(Locale.ROOT);
>   }
>   메타
> 여기서 어퍼가 적용된다는거구나.

**판정 2** — verdict: pass (시도 2/2 통과 처리)

맞은 점: T2/T4의 선언 순서 차이, T2에서 1차 조회 `declaredParams.get(getFunctionReturnName())`가 null이라는 판정, T2에서 2차 조회는 `RESULT`가 `result`로 소문자화되어 맞는다는 판정, T4에서 `@`로 시작하면 `@`를 떼고 `RETURN_VALUE`가 된다는 점(`SqlServerCallMetaDataProvider` L45-54).

틀리거나 빠진 점(정답 원문 요약):

1. 1차가 null인 진짜 이유는 "직접 입력한 값이라서"가 아니라 **키 정규화 불일치**다. 선언 파라미터는 L339-340에서 `lowerCase(provider.parameterNameToUse(paramName))` 키로 저장되어 T2의 키는 `"result"`인데, L377의 조회 키 `getFunctionReturnName()`은 L348에서 `this.actualFunctionReturnName = paramName`으로 원본 케이스 그대로 들어간 `"RESULT"`를 돌려준다(L107-108). `get("RESULT")` vs 키 `"result"` -> null. 조회 키만 소문자화를 안 한 것이 버그의 본체이고, 예정 fix의 step 2가 정확히 이 줄을 고친다.
2. 2차가 왜 맞는지의 메커니즘이 빠졌다. L378-380의 폴백은 `getOutParameterNames().get(0)`, 즉 **선언 순서상 첫 번째 OUT**을 소문자화해 조회한다. 반환 파라미터를 먼저 선언하면 그게 우연히 0번째라 맞고, 나중에 선언하면 0번째가 엉뚱한 OUT이라 T1처럼 `[out_status, AMOUNT, out_status]`가 되어 42 대신 7이 반환되거나 T3처럼 `InvalidDataAccessApiUsageException`이 난다. T2·T4의 green은 "맞아서"가 아니라 "0번째가 우연히 반환 파라미터라서"이며, 이것이 두 가드의 존재 이유다.
3. T4의 세 값이 빠졌다.
   - `paramNameToCheck`(L371) = `lowerCase(parameterNameToUse("@RETURN_VALUE"))` = `"return_value"` -> L374 `declaredParams.containsKey("return_value")`가 true라 분기에 진입한다. T4는 `withReturnValue()` 프로시저라 `isFunction()`이 false -> L343 블록을 타지 않으므로 `returnDeclared`는 끝까지 false다. 즉 진입 조건은 `containsKey` 쪽이지 `returnDeclared` 쪽이 아니다.
   - 1차 조회 키 `getFunctionReturnName()` = `"return"`(L108 기본값, `actualFunctionReturnName`이 한 번도 세팅되지 않음). `get("return")` -> null.
   - 2차 조회 키 = `getOutParameterNames().get(0).toLowerCase()` = `"RETURN_VALUE"` -> `"return_value"` -> hit. T3가 터지는 이유도 여기서 드러난다. 0번째가 `"@out_total"`이라 소문자화만 하면 `"@out_total"`인데 저장된 키는 `@`가 제거된 `"out_total"` -> null -> L381-385 throw.
   - "2차에서 else에서 @로 시작하면 RETURN_VALUE로 반환"은 위치가 어긋났다. `@` 제거는 `paramNameToCheck` 계산(L371)에서 일어나고, 2차 폴백(L379)에는 현재 `parameterNameToUse`가 없다(그래서 T3가 red다).
4. "fix 후 이 두 테스트가 지키는 것"이 답변에 전혀 없다. 정답은 **무회귀 가드**다. fix는 조회 키를 `lowerCase(parameterNameToUse(...))`로 바꾸는데, 반환 파라미터를 먼저 선언해 온 기존 사용자 코드가 fix 후에도 똑같이 매핑되어야 한다(T2 = `[RESULT, AMOUNT, out_status]`, T4 = `[RETURN_VALUE, amount, @out_total]` + 콜 스트링 동일). fix 전에는 "0번째 우연 폴백"이 답을 맞혔지만 fix 후에는 "정규화된 이름 매칭"이 답을 맞혀야 하고, T2·T4는 그 경로 교체가 결과를 바꾸지 않았음을 증명한다.

Q2 정답:

- `out_status`가 소문자인 이유는 사실상 맞았다. 사용자가 `new SqlOutParameter("out_status", ...)`로 선언했고 L371의 `paramNameToCheck = "out_status"`가 L340의 저장 키와 일치 -> L391 `param = declaredParams.get(paramNameToCheck)`로 선언된 `SqlParameter` 객체를 그대로 재사용하므로 사용자가 쓴 이름이 보존된다.
- `AMOUNT`가 대문자인 이유: `amount`는 선언되지 않아 L374가 false -> L401 else 분기로 가서 L424-446이 `provider.createDefaultInParameter(paramNameToUse, meta)`로 새 파라미터를 만드는데, 그 이름 `paramNameToUse`(L373) = `provider.parameterNameToUse("amount")` -> `GenericCallMetaDataProvider` L163-164 -> `identifierNameToUse` L280-281 `isStoresUpperCaseIdentifiers()` -> `toUpperCase(Locale.ROOT)` = `"AMOUNT"`. 스텁은 헬퍼의 `given(databaseMetaData.storesUpperCaseIdentifiers()).willReturn(true)`(Oracle)이다. 시도 1의 "COLUMN_NAME 값 자체가 대문자"는 오답이었고(스텁 값은 소문자 `"amount"`), 시도 2에서 정정되었다.
- 표현 정정: "그대로 if 분기로 들어가서"는 반대다. `declaredParams.containsKey(...)`가 false여서 L401 else 분기로 간다.
- 한 문장 정리: **선언 매칭이 먼저이고(선언된 것은 사용자 이름 그대로 보존), 매칭에 실패한 메타 파라미터만 provider 정규화 이름으로 새로 생성된다.** 그래서 같은 단언 안에 `RESULT`(선언·원본)·`AMOUNT`(메타·대문자화)·`out_status`(선언·원본)가 섞인다. 이 순서 감각이 fix의 핵심 — 조회 키만 정규화하고 파라미터 이름 자체는 절대 건드리지 않아야 T1의 기대값이 성립한다.

---

## G2 — diff 02 (fix 3줄)

대상 diff (`CallMetaDataContext.java` L376-382):

```java
// before
if (meta.isReturnParameter()) {
    param = declaredParams.get(getFunctionReturnName());
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
    }
```
```java
// after
if (meta.isReturnParameter()) {
    param = declaredParams.get(paramNameToCheck);
    if (param == null) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getFunctionReturnName())));
    }
    if (param == null && !getOutParameterNames().isEmpty()) {
        param = declaredParams.get(lowerCase(provider.parameterNameToUse(getOutParameterNames().get(0))));
    }
```

**질문** (원문)

> 1. 새로 추가된 첫 줄 `declaredParams.get(paramNameToCheck)`는 T1(Oracle)과 T3(SQL Server)에서 각각 무엇을 찾아내는가(또는 못 찾는가)? 그리고 Oracle에서 `paramNameToCheck`가 null일 때 이 조회가 안전한 이유는?
> 2. 세 번째 조회(첫 OUT 폴백)를 삭제하지 않고 정규화만 해서 남긴 이유는 무엇이라고 보는가? 이 폴백이 fix 후에도 여전히 필요한 사용자 코드 형태를 하나 들어 보세요.

**시도 1 — 답변** (사용자 원문)

> 1번 메타데이터의 값을 기반으로 파라미터를 확인하고 이때 SQL Server자체는 파라미터와 객체 어노테이션 리턴값이 일치하면 바로 찾지만 Oracle은 기본적으로 리턴 객체 선언이 null이기에 다음 탐색으로 넘어가고 이때 null일때 파라미터이름이 사용되는걸 프로바이터에서 리턴이름으로 검색하기에 2번째 if(param == null)에서 처리가 된다.
> 2번에서 남긴 이유는 객체가 1개만 있는 경우 빠르게 탐색 가능하고
> 3번쨰 분기 조건에서
> param = declaredParams.get(getOutParameterNames().get(0).toLowerCase(Locale.ROOT));
> 이걸 그래도 쓰는게 좋지않나
> param = declaredParams.get(lowerCase(provider.parameterNameToUse(getOutParameterNames().get(0))));
> 이걸로 수정하게 되면 사실 변경포인트가 2개가 된는건데, 이렇게 바꾸면 0번째 객체 꺼내서 그걸 프로바이터 내에 파라미터 이름과 일치하는 지 검사한번 해서 그 값을 꺼내서 소문자로 바꾸고 결국 객체값이랑 실체 DB메타데이터값이 서로 로워로 통일시키려는 작업인건 알겠는데.

**판정 1** — verdict: fail

- Q1: 두 경로의 골격은 맞다(step 1이 메타데이터에서 나온 키로 조회한다는 점, SQL Server는 거기서 바로 걸리고 Oracle은 그 조회가 비어 다음 단계에서 provider 정규화를 거친 반환 이름으로 잡힌다는 점). 다만 (a) 명시적으로 물은 "`paramNameToCheck`가 null일 때 그 조회가 안전한 이유"에 대한 서술이 아예 없고, (b) "Oracle은 리턴 객체 선언이 null"은 null인 주체를 잘못 지목한 표현으로 읽힌다. L316의 맵 타입과 L333-338의 익명 파라미터 처리, 테스트 헬퍼의 `COLUMN_NAME` 스텁(L418 vs L437)을 다시 보고, Oracle이 step 2에서 정확히 어떤 문자열 키로 걸리는지를 L343-350과 L339로 특정하라.
- Q2: 정규화의 목적 서술은 맞다. 그러나 폴백을 남긴 이유로 든 "객체가 1개일 때 빠른 탐색"은 이 분기의 존재 이유가 아니다 — 성능·개수 최적화와 무관하며, 도입 경위가 커밋 이력에 있다(`git show 33c031df4f3`). 또 "fix 후에도 필요한 사용자 코드 형태"의 예시가 없다.

**시도 2 — 답변** (사용자 원문)

> A+가드로 할꺼고,
> Q1에서 null로 들어가도 파라미터 이름이 null일때 아 String이라 null이면 null인 객체 그대로 반환하겠구나. 반환 자체에는 문제가 없겠구나.
> bㅇ에서 null인것은 메타데이터이며, 스탭2에서 사용자가 직접 입력한 SQL파라미터를 쓰는 거 아니야? 사용자가 입력한 값 그대로 들어가게 되고 이걸로 비교하잖아?
> Q2에서 메타데이터도 없고, 사용자 지정도 없으면 그냥 초기 쿼리 자체 객체필드를 가져오는 거 아니야?

**판정 2** — verdict: pass (시도 2/2 통과 처리)

Q1 맞은 점: "null인 것은 메타데이터"라는 정정된 지목은 맞다(Oracle 함수의 반환 행은 `COLUMN_NAME`이 null — 스텁 `getString("COLUMN_NAME")).willReturn(null, "amount", "out_status")`).

Q1 정답:

- (a) null 안전성: `declaredParams`는 L316 `new LinkedHashMap<>()`이고 `LinkedHashMap`은 null 키를 허용하므로 `get(null)`은 예외 없이 null을 돌려준다(NPE를 던지는 것은 `Hashtable`/`ConcurrentHashMap` 계열). "String이라 null이면 null 반환"이 아니라 **맵 조회가 null 키에 안전**한 것이 근거다. 게다가 익명 파라미터는 L332-338에서 `IllegalArgumentException("Anonymous parameters not supported for calls...")`로 걸러지므로 맵에 null 키가 들어갈 수 없고, `get(null)`은 항상 미스로 확정된다.
- (b) T3(SQL Server): 메타 반환 행 이름 `@RETURN_VALUE` -> `paramNameToCheck = lowerCase(parameterNameToUse("@RETURN_VALUE"))` -> `@` 제거(L48-50) -> `identifierNameToUse`(storesUpper/Lower 모두 false) -> `"return_value"`. 선언 `new SqlOutParameter("RETURN_VALUE", ...)`의 맵 키도 L339에서 같은 규칙으로 `"return_value"` -> step 1에서 직행 히트. (수정 전에는 step 1이 `get("return")`, step 3이 `"@out_total".toLowerCase()`라 둘 다 미스 -> `InvalidDataAccessApiUsageException`.)
- (b) T1(Oracle): step 1 미스 후 step 2. 여기서 `getFunctionReturnName()`은 기본값 `"return"`(L107-109)이 아니라, L343-350의 `isFunction() && !metaDataParamNames.contains(paramNameToMatch) && !returnDeclared` 조건이 첫 선언 OUT을 잡아 `this.actualFunctionReturnName = paramName`으로 넣은 `"RESULT"`다. 그리고 시도 2의 "사용자가 입력한 값 그대로 비교"는 틀렸다 — step 2는 그 이름을 `lowerCase(provider.parameterNameToUse("RESULT"))` = `"result"`로 **정규화한 키**로 조회한다(Oracle은 storesUpperCase=true). 맵 키가 L339에서 같은 변환으로 만들어졌으니 "그대로"가 아니라 **같은 규칙으로 변환해서 맞추는 것**이 이 fix의 핵심이다.

Q2 정답:

- 맞은 점 없음(가장 마지막 폴백이라는 위치 감각만). "초기 쿼리 자체 객체필드를 가져온다"는 오답이다. step 3은 쿼리나 객체 필드가 아니라 **사용자가 선언한 파라미터 목록의 첫 OUT**(`getOutParameterNames().get(0)`)을 다시 `declaredParams`에서 찾는 조회다.
- 삭제하지 않은 이유: 이 줄은 `33c031df4f3`(gh-25707, "Restore original 4.x behavior for initialization of function return name")이 지켜온 4.x 관례다 — 메타데이터 이름으로도 함수 반환 이름으로도 선언 파라미터를 못 찾으면 "선언된 첫 OUT 파라미터가 반환값"으로 간주한다는 하위호환 폴백. 이번 작업의 범위는 조회 키 정규화이므로 관례의 존재 여부는 건드리지 않고 키 규칙만 L339와 일치시켰다. 성능이나 빠른 탐색과는 무관하다.
- step 3 도달 가능성: 판정 워커가 독립 검증한 결과 **fix 후에는 도달 불가**다. L374 진입 조건이 두 갈래인데, `declaredParams.containsKey(paramNameToCheck)`로 진입한 경우 step 1이 정확히 같은 키로 조회하므로 반드시 히트하고, `meta.isReturnParameter() && returnDeclared`로 진입한 경우 `returnDeclared`를 세운 L348의 이름이 바로 직전 L339가 맵에 넣은 키와 같은 규칙이라 step 2가 반드시 히트한다. 따라서 "fix 후에도 필요한 사용자 코드 형태"를 요구한 질문의 전제 자체가 틀렸다. 실측도 일치한다 — step 3만 구 코드로 되돌려도 `SimpleJdbcCallTests` 22/22 green(현 테스트가 step 3을 실행하지 않음).

**게이트 밖 결정 (이 게이트에서 파생)**

사용자의 Q2 후반 이견("변경 포인트가 2개가 되는 것 아니냐")이 실측으로 확인되어, step 3 처리를 놓고 선택지를 다시 받았다. 처음 제시된 A / B / A+가드 중 사용자는 A+가드를 골랐으나, 위 도달 불가 판정으로 가드 테스트를 쓸 수 없게 되어 A / B / C(삭제)로 재제시되었고 최종 선택은 **A(step 3도 정규화해서 유지)**였다. 근거는 `analysis.md` 6.3절에 기록.

---

## G3 — diff 03 (리뷰 반영 주석)

대상 diff (`CallMetaDataContext.java` L376-378) + `SimpleJdbcCallTests` 빈 줄 1 -> 2:

```java
if (meta.isReturnParameter()) {
    // Same normalization as the declaredParams keys above; the function
    // return name may have been adopted from a declared out parameter
    param = declaredParams.get(paramNameToCheck);
```

**질문** (원문 — 최종본)

> 이 주석의 두 절이 각각 무엇을 가리키는지 답해 주세요 — (1) "same normalization"의 정규화 식은 코드로 정확히 무엇인가, (2) "the function return name may have been adopted from a declared out parameter"는 코드의 **어느 줄**에서 일어나는 일이고, 그게 왜 step 2가 반드시 맞는 근거가 되는가.

주석이 1줄이었을 때 먼저 나갔던 질문은 다음과 같았고, codex 감사 A1로 주석이 2줄로 보완되면서 위 질문으로 교체되었다.

> 이 주석이 "위의 declaredParams 키와 같은 정규화"라고 말하는데, 그 정규화 식이 정확히 무엇이고(코드 한 줄로), 이 주석 한 줄이 리뷰어에게 어떤 질문(F1이 걱정한)을 미리 막아주는지 설명해 주세요.

**시도 1 — 답변** (사용자 원문)

> 아니 맵에 넣을때는 어차피 정규화해서 넣으면 조회때는 정규화할 필요가 없잖아. 이때 조회할때 넣는 파라미터를 정규화해서 저장할떄 같은 규칙으로 검색어를 변경해서 조회한다는거 맞지?
> 그리고 2번에 대해서는 아 메타에 없어도 사용자 지정은 그대로 채택한다는거구나. 그리고 메타기반으로 넣을 때 사용자랑 중복 된느건 객체 그대로 사용자껄 사용하고 없으면 메타에 값을 그대로 사용하여 아웃파라미터를 만든다는거구나.

**판정 1** — verdict: fail

- (1) 맞은 점: "조회 검색어를 저장 시와 같은 규칙으로 변환해서 조회한다"는 메커니즘 서술은 정확하고, 저장 측 키 생성(L339-340)과 반환 분기 조회 측을 같은 규칙으로 맞춘다는 관계도 잡았다. 부족한 점: (a) 첫 문장 "저장 때 정규화했으면 조회 때는 정규화 불필요"가 뒤 문장에서 뒤집히긴 하나, 조회 입력이 어디서 오길래 변환이 필요한지 — 세 조회 중 어느 것이 이미 정규화된 값이고 어느 것이 원본 이름인지 — 를 구분하지 못한 채 남아 있다. 세 조회가 모두 같은 처지가 아니다. (b) 정규화 식을 코드로 지목하지 않아, 기존 코드가 어느 부분만 적용했다가 어긋났는지가 답변에 없다.
- (2) 맞은 점: 메타 순회에서 선언 파라미터와 겹치면 사용자 객체를 그대로 쓰고(L396), 겹치지 않으면 메타 값으로 파라미터를 만들어 넣는다(L428-448)는 서술은 정확하다. 틀리거나 빠진 점: (a) "메타에 없어도 사용자 지정은 그대로 채택"은 과잉 일반화다. 채택(L343-350)은 세 조건이 동시에 성립할 때만, 대상도 하나로 제한되어 일어나며, 채택되는 것은 "파라미터를 호출 목록에 넣는 것"이 아니라 다른 무엇이다. (b) 질문의 핵심인 "그게 왜 step 2가 반드시 맞는 근거가 되는가"에 대한 답이 없다. (c) L392의 사후 갱신도 언급되지 않았다.

**시도 2 — 답변** (사용자 원문)

> 아 메타데이터가 아닌 사용자가 어노테이션 이름을 직접 파라미터명을 작성했을때 필요할 수 있겠구나.
> 2번은 사용자가 지정한값에 없으면서, 메타에만 있으면 그 값은 그대로 객체 배열에 생성된다는거 아니야?

**판정 2** — verdict: pass (시도 2/2 통과 처리)

(1) 맞은 점: "사용자가 `@`를 붙인 이름을 직접 선언했을 때 정규화가 필요하다"는 정확한 한 사례다. `SqlServerCallMetaDataProvider.parameterNameToUse`(L45-55)가 `@`(REMOVABLE_COLUMN_PREFIX, L34)로 시작하면 한 글자를 잘라 super로 넘기므로 사용자가 `@out_id`로 선언해도 맵 키는 `out_id`로 저장된다.

(1) 정답:

- 정규화 식 = `lowerCase(provider.parameterNameToUse(name))`. L339 `String paramNameToMatch = lowerCase(provider.parameterNameToUse(paramName));`, L340 `declaredParams.put(paramNameToMatch, param);` — 이 식이 곧 `declaredParams`의 저장 키 규칙이다. `parameterNameToUse`는 `@` 제거(SQL Server) + `identifierNameToUse`의 DB별 대소문자 폴딩(`GenericCallMetaDataProvider` L163-165)이고, `lowerCase`는 `toLowerCase(Locale.ROOT)`(L679-681, null이면 빈 문자열). 주석의 "same normalization"은 조회 키를 저장 키 규칙과 동일하게 맞춘다는 뜻이다.
- 세 조회의 입력 성격이 다르다.
  - step 1 `paramNameToCheck` — **이미 정규화된 값**. L371에서 메타데이터 컬럼명(L369)에 그 식을 적용해 계산해 둔 것이라 추가 변환이 필요 없다.
  - step 2 `getFunctionReturnName()` — **원본**. `setFunctionReturnName`(L100-102)으로 설정된 값이거나 L348에서 채택된 선언 원본명, 아니면 기본 `"return"`(L107-108). 변환 필요.
  - step 3 `getOutParameterNames().get(0)` — **원본**. L342 `outParamNames.add(paramName);`이 `paramNameToMatch`가 아닌 원본 `paramName`을 담는다. 변환 필요.
- 기존 코드가 적용했던 부분: step 1은 `declaredParams.get(getFunctionReturnName())`으로 **변환 0회**(lowerCase도 parameterNameToUse도 없음), step 3은 `toLowerCase`만 있고 `parameterNameToUse`가 빠져 `@` 미제거 + DB별 폴딩 규칙 불일치. 저장 키는 두 단계를 다 거치므로 조회가 어긋난다.

(2) 맞은 점: "사용자가 지정한 값에 없으면서 메타에만 있으면 그 값 그대로 생성된다"는 서술 자체는 사실이지만, 그건 else 분기(L406 이하, `provider.createDefaultOutParameter(returnNameToUse, meta)` L410 및 L419/L426/L437 계열)의 이야기이고 질문이 물은 "채택(adopted)"과는 다른 코드 경로다. 게이트 도중 나온 "프로바이더에 넣는 거 아니야?"는 오답 — 프로바이더는 조회와 변환만 하고 아무것도 저장하지 않는다.

(2) 정답:

- 채택이 일어나는 줄 = L348 `this.actualFunctionReturnName = paramName;`(직후 L349 `returnDeclared = true;`). 채택되는 것은 **컨텍스트 필드 `actualFunctionReturnName`에 그 선언 out 파라미터의 원본 이름이 대입되는 것**이고, 그 결과 `getFunctionReturnName()`(L107)이 `"return"` 대신 그 이름을 돌려준다.
- 조건 = L343 `if (isFunction() && !metaDataParamNames.contains(paramNameToMatch) && !returnDeclared)` — 함수 호출이고, 그 이름이 메타데이터 파라미터 목록에 없고(실인자가 아니라 반환값으로 보이고), 아직 채택된 것이 없을 때. `returnDeclared` 때문에 선언 out 파라미터 중 첫 하나만 채택된다.
- step 2가 반드시 맞는 이유(구성상 보장): L339-340이 바로 그 파라미터를 `lowerCase(parameterNameToUse(paramName))` 키로 맵에 넣은 **직후** 같은 루프 바디의 L348이 그 `paramName`(원본)을 `actualFunctionReturnName`에 저장한다. 따라서 step 2의 조회 키 `lowerCase(provider.parameterNameToUse(getFunctionReturnName()))`(L381)는 정의상 그 맵 키와 문자 그대로 동일하며, 채택이 일어난 이상 조회는 실패할 수 없다. step 1이 먼저 실패하는 경우는 메타 반환 컬럼명과 선언 이름이 다를 때이고, L374의 `meta.isReturnParameter() && returnDeclared`가 그 진입을 열어준다.
- 매치도 채택도 안 된 선언 파라미터는 L374 조건 밖이라 `workParams`에 추가되지 않아 호출 목록에서 제외된다(조용한 누락 — 이 수정이 막는 실패 모드의 이면).
- 사후 갱신: 조회 성공 시 L392 `this.actualFunctionReturnName = param.getName();` — step 1이나 step 3으로 찾은 경우에도 실제 사용된 선언 파라미터 이름으로 필드를 다시 맞춘다.

---

## 게이트 중 보조 질문

게이트 답변과 별개로 사용자가 던진 질문들이다. 판정 대상은 아니었고, 대부분 그 자리에서 `analysis.md`나 개념 문서로 반영되었다.

### 1. 이름표 역할 사전이 왜 문서에 없냐 (G0 시도 2 중)

> 그런데 getFunctionReturnName()과 paramNameToCheck에 대한 설명은 analysis에 왜없어? 이런걸 각 어떤역할을 하는지 적으라는거였는데?

정당한 지적으로 인정되어 `analysis.md` 2.5절 "핵심 이름표 사전"이 추가되었다(위 G0 정답 정리의 표). 판정 워커도 "문서 비판은 정당한 요청 — 판정 외"로 분류했다.

### 2. DB가 반환 행에 이름을 안 주는 케이스가 정말 있냐 (G1 직전)

> 그럼 DB자체 행 이름 자체면 문제없지만 사용자가 별도 객체로 파라미터 파인딩을 결과로 하려면 DB가 반환행에 이름을 보통 다 딕셔너리 형태나 배열 안에 객체형태로 데이터를 반환하지않아? 애초에 DB 쿼리결과 자체가? 그런데 2번같은 케이스가 나온다고?

답: 여기서 말하는 "행"은 쿼리 결과 행이 아니다. 섞여 있던 세 가지를 분리하면 풀린다.

| 구분 | 무엇 | 형태 | 이름이 있나 |
|---|---|---|---|
| 메타데이터 행 (reconcile이 다루는 것) | `DatabaseMetaData.getProcedureColumns()`가 돌려주는 프로시저 시그니처 설명서 — 파라미터당 1행(이름·방향·타입) | 실행 전에 시그니처를 기술 | 파라미터는 있음. 함수 반환값은 없을 수 있음 |
| 실행 결과의 OUT 값 | `CallableStatement.getObject(index)` | 위치 기반. 이름은 Spring이 `callParameters`로 붙여줌 | 없음 |
| 결과셋 | SELECT 결과 | 딕셔너리/객체 형태 — 컬럼명 있음 | 있음 |

함수의 반환값은 파라미터가 아니라 선언 문법상 이름이 없다(`CREATE FUNCTION get_total(amount IN NUMBER, out_status OUT VARCHAR2) RETURN NUMBER`). 그래서 Oracle JDBC 드라이버는 반환값을 `COLUMN_TYPE=5, COLUMN_NAME=null` 행으로 보고한다. 반면 SQL Server 프로시저는 정수 상태 코드를 `@RETURN_VALUE`라는 이름 있는 의사 파라미터로 노출한다. 그리고 이는 희귀 케이스가 아니라 Oracle 함수의 기본 경로다 — 기존 테스트 `initializeAddInvoiceWithMetaData`가 `COLUMN_NAME`을 `willReturn(null, "amount", "custid")`로 스텁하는 그 첫 번째 null이 바로 무명 반환 행이다. 이 설명은 `analysis.md` 2.6절로 들어갔다.

### 3. SELECT가 아니라 CUD라서 생기는 문제냐 (G1 시도 1 앞부분)

> 아 select가 아닌 cud같은 경우 리턴값이 지정안된 케이스가 있을꺼고 이 케이스가 항상 문제가 된다는거네?

답: SELECT vs CUD의 문제가 아니라 **프로시저 vs 함수**의 문제다. 프로시저는 반환 슬롯 자체가 없어 결과가 전부 이름 있는 OUT으로 나오므로 이 결함 경로에 아예 들어오지 않는다. 함수는 반환 슬롯이 있고 시그니처상 이름이 없어 Oracle 드라이버가 `COLUMN_NAME=null` 행으로 보고한다. SQL Server 프로시저는 예외적으로 정수 상태코드 슬롯을 `@RETURN_VALUE`라는 이름 있는 행으로 보고한다(`withReturnValue()` 경로). 또 "항상 문제"도 아니다 — 발동 조건은 함수(또는 `withReturnValue`) + 반환 파라미터 앞에 다른 OUT 파라미터를 선언한 경우다. `analysis.md` 2.7절.

### 4. 프로시저와 함수 개념 문서 요청 (G1 시도 2 앞부분)

> 우선 프로시저와 함수 각각 개념문서로 study폴더 내에 concepts문서에 각각 마크다운문서로 설명좀 써줄래?

`docs/study/concepts/stored-procedure.md`, `docs/study/concepts/stored-function.md` 2편이 작성되고 README 색인에 "JDBC 저장 루틴 계열"이 추가되었다. 그 과정에서 확인된 것: JDBC 방향 상수가 두 계열이고 값이 어긋난다(`procedureColumnReturn=5`, `functionReturn=4`이고 5는 `functionColumnResult`). 그래서 `CallParameterMetaData.isReturnParameter()`(L91-93)가 `function` 플래그로 판정을 가르고, 그 플래그는 `withFunctionName()` 여부가 아니라 메타데이터를 `getProcedureColumns`로 읽었는지 `getFunctionColumns`로 읽었는지(`GenericCallMetaDataProvider` L312-316)에서 온다.

### 5. step 3까지 정규화할 필요가 있냐 (G2 시도 1 후반의 설계 이견)

> 이걸로 수정하게 되면 사실 변경포인트가 2개가 된는건데

실측으로 확인: step 3만 구 코드(`toLowerCase`)로 되돌려도 `SimpleJdbcCallTests` 22/22 green — step 3 변경은 현 테스트 4건이 한 번도 실행하지 않는 변경이었다. 이후 판정 워커의 독립 검증으로 fix 후 step 3이 도달 불가라는 결론이 나와, 선택지가 A(정규화 유지) / B(원형 유지) / C(삭제)로 재제시되었고 사용자는 A를 선택했다.

### 6. 주석 해석 선확인 (G3 시도 1 직전)

> 우선 질문 같은 정규화를 할때 체크를 한다는건 실제 메타데이터를 정규화하는 식은 그대로 라는의미이고, 메서드가 리턴하는 이름 즉 사용자가 파라미터로 지정한 이름 자체에 대한 아웃파라미터만 아돕트한다는거 아니야?

답: 절반은 맞고 절반은 어긋난다. "같은 정규화"는 메타데이터 정규화 식이 그대로라는 뜻이 아니라 **L339에서 사용자 선언 이름으로 맵 키를 만든 그 식을 조회 키에도 똑같이 쓴다**는 뜻이다. "adopted"는 방향은 맞지만 조건이 더 있다 — L343의 세 조건이 동시에 성립할 때 첫 번째로 만나는 선언 OUT 하나만 채택된다.

### 7. result/amount 예시 probe (G3 시도 1 직전)

> 사용자 지정한값과 메타값이 서로 일치하면 일치하는 애는 그대로 쓸텐데 만약 일치하는 값이 없다면 순서대로 매핑하는거야? 예시로 사용자는 result,amount로만 적었고, 실제 메타데이터는 null,amount,out_status라 하자 그럼 이건 전체 파라미터 매핑 리턴네임객체 자체가 어떻게 되는거지?

임시 probe 테스트를 실제로 돌려 답했다(실행 후 제거·파일 원복 확인). 결과: `names=[result, amount, OUT_STATUS]`, `callString={? = call GET_TOTAL(?, ?)}`, `executeFunction=42`.

단계별로는, 선언 순회(L318-355)에서 `result`가 키 `"result"`로 저장되고 메타 이름 목록 `["amount","out_status"]`에 없으므로 L348에서 `actualFunctionReturnName = "result"`로 채택되고, `amount`는 메타에 있으니 일반 파라미터가 된다. 메타 순회(L367~)에서는 반환 행(이름 null)이 `paramNameToCheck=null`이지만 `returnDeclared`라 분기에 진입해 step 1 미스 후 step 2에서 `"result"`로 hit하고, `amount`는 선언과 매치되어 사용자 객체가 그대로 쓰이며, `out_status`는 선언에 없어 else 분기에서 메타 기반 기본 OUT 파라미터가 Oracle 대문자화된 `OUT_STATUS`로 자동 생성된다.

결론: "일치하는 게 없으면 순서대로 매핑"은 아니다. 규칙은 전부 이름 기반이고, 예외는 "함수의 반환값은 이름이 없으니 메타에 없는 첫 선언 OUT을 반환으로 채택"(L343-350) 하나뿐이다. 순서 기반 규칙은 step 3(첫 OUT 폴백)이 유일했는데 fix 후엔 도달하지 않는다.

### 8. 프로바이더가 최종 목록을 갖고 있냐 (G3 시도 2 직후)

> 프로바이더에 넣는거 아니야?
> 결국 프로바이더에서는 완성된 전체 목록 사용자 지정 및 메타데이터로 완성된 프로바이더에 파라미터 이름을 ㅗ사용되는 파라미터 명이 전부 있고 이걸 순서 상관없이 조회해서
> 애초에 여기서 다 Ok가 된다는거ㅣㅈ

답: 그릇이 세 개다.

| 그릇 | 어디 | 내용 | 순서 |
|---|---|---|---|
| `provider.getCallParameterMetaData()` | 프로바이더 | DB 시그니처 행만(메타데이터) | DB 순서 |
| `declaredParams` | `reconcileParameters` 지역 `LinkedHashMap` | 사용자 선언만, 키 = 정규화 이름 | 이름 조회(순서 무관) |
| `workParams` -> `callParameters` | 컨텍스트 결과 | 합쳐진 최종 목록 | DB 순서 |

프로바이더는 DB 쪽 정보와 이름 변환 규칙만 갖고 사용자 선언은 모른다. 합쳐진 목록은 메타 행을 DB 순서대로 돌면서 각 행의 이름으로 `declaredParams`를 조회해 만들어진다 — 매치되면 사용자 객체, 아니면 메타 기반 생성. 결과가 선언 순서와 무관한 것은 맞고, 그 무관함은 "이름으로 맵을 조회"하는 데서 온다. "여기서 다 OK"가 "fix 후에는 반환 행도 이름 조회로 맞춰지므로 순서 폴백에 기대지 않는다"는 뜻이라면 맞다.

---

## 반복된 오해 패턴

네 게이트에서 같은 종류의 착오가 반복됐다.

1. **"그대로 쓴다" vs "같은 규칙으로 변환한다"** — G0에서 "함수 반환 이름은 맵 키와 동일한 정규화로 조회"라고 옳게 쓰고도, G2에서는 "사용자가 입력한 값 그대로 들어가게 되고 이걸로 비교"로 되돌아갔다. 이 버그의 본체가 정확히 "조회 키만 원본 그대로 썼다"이므로, 이 구분이 흐려지면 버그 자체가 안 보인다. G3 시도 1의 "저장 때 정규화했으면 조회 때는 정규화할 필요가 없잖아"도 같은 뿌리다.
2. **정규화가 어디에서 일어나는지 위치를 한 칸씩 옮겨 짚음** — G1에서 `@` 제거를 step 2(L379 폴백)의 일로 봤으나 실제로는 `paramNameToCheck` 계산(L371)의 일이고, L379에는 `parameterNameToUse`가 없었다(그래서 T3가 red였다). G0에서는 lowerCase 변환을 결과 맵 키(`extractOutputParameters`)에서 일어나는 일로 잘못 놓았다.
3. **null인 주체를 잘못 지목** — G2에서 "Oracle은 리턴 객체 선언이 null"이라 했으나 null인 것은 사용자 선언이 아니라 메타데이터의 `COLUMN_NAME`이다. 시도 2에서 스스로 정정했다.
4. **"안전한 이유"를 언어 차원으로 축소** — G2의 `get(null)` 안전성을 "String이라 null이면 null 반환"으로 설명했으나, 근거는 `LinkedHashMap`이 null 키 조회에 예외를 던지지 않는다는 점과 익명 파라미터가 L332-338에서 미리 IAE로 걸러진다는 점이다.
5. **범위 과잉 일반화** — G3의 "메타에 없어도 사용자 지정은 그대로 채택"은 L343의 세 조건과 "첫 하나만"이라는 제한을 지웠다. 실제로는 매치도 채택도 안 된 선언 파라미터는 호출 목록에서 조용히 빠진다.
6. **동작 관찰은 되는데 "왜"가 빠짐** — G1에서 T2/T4의 선언 순서 차이를 정확히 관찰하고도 "그 순서가 왜 결과를 바꾸는가"(폴백이 `getOutParameterNames().get(0)`을 본다)를 말하지 않았고, "이 가드가 fix 후에 지키는 것"(무회귀)은 아예 답에 없었다.
7. **질문의 전제 자체가 틀린 경우** — G2 Q2의 "fix 후에도 폴백이 필요한 사용자 코드 형태를 들라"는 질문은 실제로는 답이 존재하지 않았다(fix 후 step 3 도달 불가). 사용자가 못 맞힌 것이 아니라 질문이 틀렸던 사례다.

## 교훈

이 기록이 남긴 것은 결함의 한 문장 요약, 이름표를 표로 고정해야 하는 이유, 그리고 게이트가 산출물을 바꾼 사례다.

- 이 결함의 학습 핵심은 한 문장으로 압축된다: **저장 키와 조회 키가 같은 식으로 만들어져야 하고, 그 식은 `lowerCase(provider.parameterNameToUse(name))`(L339)이다.** 네 게이트의 질문이 전부 이 문장의 다른 각도였다.
- "이름"이 네 가지 표기로 돌아다니는 코드(원본 / provider 규칙 적용 / 소문자 키 / 메타데이터 표기)에서는, 변수 이름표별로 "지금 무엇을 들고 있나"를 표로 고정하지 않으면 설명이 계속 한 칸씩 어긋난다. 사용자의 "역할 사전이 왜 없냐"는 지적이 문서(`analysis.md` 2.5절)를 실제로 개선했다.
- 게이트 답변에 섞인 설계 이견이 실제 산출물을 바꿨다. G2의 "변경 포인트가 2개가 되는 것 아니냐"가 실측(step 3만 되돌려도 22/22 green) -> 워커 독립 검증(step 3 도달 불가) -> 선택지 재제시(A/B/C) -> `analysis.md` 6.3절 기록으로 이어졌다. 이해 게이트는 채점만 하는 장치가 아니었다.
- 사용자의 즉석 예시(선언 `result`·`amount` / 메타 `null`·`amount`·`out_status`)를 임시 probe 테스트로 실제 실행해 답한 것이, 말로 하는 설명보다 "순서 매핑이 아니라 이름 매핑"이라는 규칙을 확실하게 굳혔다. 답을 모를 때는 돌려보는 편이 빠르다.
- 판정 워커에는 메인의 해설이 아니라 실제 코드와 사용자 답변만 넘어간다. 그 덕분에 G0에서 메인이 이미 정답을 알려준 뒤에도 워커가 "(1)은 틀림"을 독립적으로 판정했고, G2에서는 질문 자체의 전제 오류(step 3 도달 불가)까지 잡아냈다.
