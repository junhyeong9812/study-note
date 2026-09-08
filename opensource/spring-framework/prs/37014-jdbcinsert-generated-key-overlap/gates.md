# PR #37014 — 이해 게이트 기록

> 출처: 세션 a23b513a (2026-07-08), 작업 폴더 `docs/plans/2026-07-08/simplejdbcinsert-generated-key-mismatch/`. 모드는 lazy-implements(당시 하네스 v3 명칭), 판정은 독립 서브에이전트 워커가 수행했고 메인은 verdict만 수신했다. 답변은 사용자 원문 그대로이며 오타도 고치지 않았다. 판정과 정답은 대화에 실제로 기록된 것만 옮겼다.

## 게이트 목록

이 작업에서 거친 게이트는 계획 하나와 diff 셋, 모두 네 건이다.

| 번호 | 대상 | 시도 | 최종 판정 |
|------|------|------|-----------|
| G1 | 계획 게이트 (트레이드오프 A 착수 전) | 1회 | pass (워커 판정 없음, 방향 확인만) |
| G2 | diff 1 — `reconcileColumnsToUse` 필터링 대칭화 | 2회 (fail 후 pass) | pass |
| G3 | diff 2 — 회귀 테스트 `declaredColumnsIncludingGeneratedKeyAreExcluded` | 1회 | pass |
| G4 | diff 3 — 리뷰 반영 테스트 2건 (전체 겹침, 대소문자 불일치) | 1회 | pass |

시도 합계 5회, 판정은 pass 4 / fail 1이다. 워커가 정식으로 채점한 것은 G2 두 번, G3 한 번, G4 한 번으로 총 4회다.

---

## G1 — 계획 게이트 (트레이드오프 A)

**질문** (07:27, 원문)

> `reconcileColumnsToUse`가 정확히 어떻게 바뀌고, 그 변경이 왜 J3 버그(placeholder 수 vs values/types 배열 크기 불일치)를 고치는지 본인 말로 설명해주실 수 있나요?

**시도 1 — 답변** (07:30, 사용자 원문)

> task문서부터 만들어야되지않아?
> 1번은 keys set 생성에 대한 분기를 올려서 isEmpty에 대해서 동일한 필터링이 되도록한다. 그렇게 처리해서 실수로 usingColumns에 포함시켜도 흡수하도록한다. 기존에는 데이터 자체가 잘못되서 실패였다면, 지금은 그렇게 잘못 넣어도 알아서 처리하게 되는거지

**판정 1** — pass. 단 워커 판정이 아니다. task.md에 다음과 같이 기록돼 있다.

> 판정: pass (워커 판정 없이 방향 확인 — 이후 diff 1 게이트에서 정식 판정)

즉 이 게이트는 방향만 확인하고 정식 채점은 G2로 미뤄졌다. 답변 앞머리의 "task문서부터 만들어야되지않아?"는 절차 지적으로, 실제로 이 지적 직후 task.md 템플릿이 로드됐다.

**정답 정리** — 계획(트레이드오프 A)에 명시된 변경 내용 자체가 정답이며, 사용자 답변이 그 내용과 일치한다.

- `keys` Set 생성을 두 분기(`declaredColumns` 비어있음 / 비어있지 않음) 위 공통 지점으로 끌어올린다.
- `!declaredColumns.isEmpty()` 분기가 `new ArrayList<>(declaredColumns)`를 그대로 반환하는 대신 `keys`로 필터링한 새 리스트를 반환한다.
- 근거: auto-discovery 분기(구 L211-220)가 이미 같은 필터를 쓰고 있었으므로 대칭을 맞추는 변경이다.

---

## G2 — diff 1: `reconcileColumnsToUse` 필터링 대칭화

**질문** — diff 1의 before/after 스니펫 제시(07:31)와 함께 G1의 질문이 그대로 채점 대상으로 이어졌다. 대화에 diff 1 전용으로 새로 적힌 질문 문장은 없고, 판정 워커의 이름이 "Judge diff understanding gate for J3 fix"였으며 task.md도 아래 두 답변을 diff 1 이해 게이트의 1차와 2차로 기록한다.

**되묻기** (07:34, 사용자 원문 — 답변으로 기록)

> 잠시만 이렇게 했을 때 디클리어 컬럼이 비여있지 않으면 빈배열인데 이걸 바꿈으로 써 그냥 빈 배열이 아닌 키 셋 형태로 변형된걸 포문으로 더해서 해당 리스트를 반환하는거면, 이건 동작 방식이 바뀌는건데 약속에 대해 맞아?

메인의 답(07:35): 계약이 실제로 바뀌는 것이 맞고, 그것이 트레이드오프 A의 정의 그 자체다. 다만 겹치는 케이스는 지금까지 100퍼센트 실패했으므로 하위호환 파손이 아니며, 겹치지 않는 경우는 동작이 100퍼센트 동일하다.

**시도 1 — 답변** (07:36, 사용자 원문)

> 이해했어. 그러니깐 원래는 그냥 무시해서 빈 배열이였다면, 이제는 선언한 제너레이트 키 자체를 반환할 수 있도록 하겠다는거잖아? 이게 맞을까?

**판정 1** — fail. 워커 피드백 원문:

> 전제와 방향이 모두 반대다. declaredColumns가 비어있지 않은 분기는 before/after 어느 쪽에서도 '빈 배열'을 반환한 적이 없다(항상 declaredColumns 기반 리스트를 반환). 그리고 이번 변경은 generated key를 결과에 '포함'시키는 게 아니라, declaredColumns 안에 있는 generated key 컬럼을 '제외'하도록 필터를 추가한 것이다 — 방향을 뒤집어 이해했다.

메인이 판정 도착 전에 준 힌트(07:37)는 정답을 노출하지 않고 구체 값 대입을 요구하는 형태였다.

> before에서 `declaredColumns`가 `["id","name"]`이고 `generatedKeyNames`가 `["id"]`일 때, 반환되는 리스트는 정확히 무엇이었을까요? (빈 배열일까요, 아니면 뭔가 들어있을까요?)
> after에서는 같은 입력에 대해 반환되는 리스트가 어떻게 달라지나요?

**시도 2 — 답변** (07:39, 사용자 원문)

> 아 id,name이 들어갈꺼 같아. 그리고 제네레이트 키가 id이면 id,name 그대로 나오지만 after에서는 name만 들어가겠지 아 이거구나. 디클리어로 명시되어야 하는건 키이름이 아닌 애들만 되어야 하니깐?

**판정 2** — pass. 워커 피드백 원문:

> before=id,name 그대로, after=generatedKeyNames와 겹치는 id 제외하고 name만 반환 - 방향과 필터링 메커니즘(declaredColumns를 키이름 아닌 것만 남기도록 필터링)을 정확히 짚었음.

**정답 정리** (대화에 제시된 정답, 코드 줄 근거)

- before의 `!declaredColumns.isEmpty()` 분기는 `return new ArrayList<>(declaredColumns);` 한 줄이다. 입력이 `["id","name"]`이면 반환도 `["id","name"]`이며, 빈 배열이 된 적은 없다.
- 빈 배열이 나올 수 있는 곳은 아래쪽 auto-discovery 분기(구 L211-220)로, `keys.contains(meta.getParameterName().toUpperCase(Locale.ROOT))`로 걸러 `columns`를 만드는 완전히 다른 경로다.
- after는 같은 분기에서 `declaredColumns`를 순회하며 `!keys.contains(column.toUpperCase(Locale.ROOT))`인 것만 담아 `["name"]`을 반환한다. 방향은 포함이 아니라 제외다.
- 이 필터가 버그를 고치는 이유: `createInsertString`은 원래부터 `generatedKeyNames`로 key를 걸러 placeholder를 만들었는데(L291, L322), `matchInParameterValuesWithInsertColumns`와 `createInsertTypes`는 필터되지 않은 `this.tableColumns` 전체를 순회했다. reconcile 단계에서 미리 걸러 두면 세 곳이 같은 목록을 보게 되어 개수가 일치한다.

---

## G3 — diff 2: 회귀 테스트 `declaredColumnsIncludingGeneratedKeyAreExcluded`

**질문** (07:41, 원문)

> 이 테스트가 검증하는 게 정확히 뭔지, 왜 이 assertion들(3개: insertString, values, insertTypes.length)이 필요한지 설명해주시겠어요?

**시도 1 — 답변** (07:44, 사용자 원문)

> 아 id가 키값이고 id는 키값이라 인서트문에 들어가면 안된다 그리고 실제 쿼리는 name만 인식해서 적용해야된다. 그리고 values에 들어가는 객체에 대해서는 Sven하나만 있는게 맞고, 들어가는 벨류값 타임은 1이여야 name의 value만 된거니깐, 저렇게 설계한거 아니야?

**판정 1** — pass. 워커 피드백 원문:

> id가 키라서 SQL/values/types 모두에서 빠져야 한다는 방향과 세 assertion이 각각 다른 지점(SQL 문자열, 바인딩 값, 타입 배열)의 개수 일치를 검증한다는 취지를 정확히 짚었습니다.

**정답 정리**

- 테스트는 `processMetaData(dataSource, List.of("id","name"), new String[]{"id"})`로 `usingColumns("id","name")`과 `usingGeneratedKeyColumns("id")` 조합을 그대로 재현한다.
- 세 assertion은 서로 다른 세 산출 지점을 각각 고정한다. `insertString`은 `createInsertString`이 만든 SQL 문자열, `values`는 `matchInParameterValuesWithInsertColumns`가 만든 바인딩 값 리스트, `insertTypes.length`는 `createInsertTypes`가 만든 타입 배열 크기다. 이 셋의 개수가 어긋나는 것이 J3 버그의 실체이므로 셋을 함께 봐야 한다.
- 이 게이트 이후 메인이 스스로 정정한 사실관계 하나(07:55)가 있다. pre-fix에서 처음 FAIL한 지점을 `insertString` assertion이라고 말했으나 실제로는 `values` assertion이었다. `createInsertString`은 이번 diff와 무관하게 원래도 자체 필터로 key를 제외했으므로 pre-fix에서도 `insertString`은 이미 `"INSERT INTO customers (name) VALUES(?)"`로 옳았고, 실제로 어긋난 것은 `values`(pre-fix에서 `[1,"Sven"]`, 크기 2)와 `insertTypes.length`(pre-fix에서 2)였다. codex 리뷰 2회가 독립적으로 같은 지적을 해서 발견됐다.

---

## G4 — diff 3: 리뷰 반영 테스트 2건

**질문** (07:56, 원문)

> 이 두 신규 테스트가 각각 왜 필요한지(어떤 엣지케이스를 방어하는지) 설명해주시겠어요?

대상 테스트 두 건은 다음과 같다.

- `declaredColumnsMatchingGeneratedKeysProduceEmptyInsert` — declaredColumns가 `["id"]`, key가 `["id"]`로 전체가 겹치는 경우
- `declaredColumnsExcludeGeneratedKeyRegardlessOfCase` — declaredColumns가 `["ID","name"]`, key가 `["id"]`로 대소문자가 다른 경우

**되묻기** (08:00, 사용자 원문 — 답변으로 기록)

> 3번은 만약 대문자로 넣었을때 키가 소문자일 경우 upper로 대소문자 일치를 안하는데 3번은 이거 의도일 수 도 있지않아? 컬럼 자체는 대소문자 분별하잖아? 아니면 주석이나 계약에 3번으로 비교하지않는다고 되어있어?
> 2번은 기존에 위와 같이 겹쳤을때 안들어가야되는데 기존에는 빼지않으니 id일 경우 id를 제거해서 빈값이여야 하는데 기존에는 그대로 id로 나올꺼라 2번은 계약상 틀려서 그런 거 아니야?

메인의 답(08:00) 요지는 아래 정답 정리와 같으며, 답변 후 같은 질문으로 다시 정리해 달라고 요청해 정식 채점으로 넘어갔다.

**시도 1 — 답변** (08:02, 사용자 원문)

> 2번은 insertStringd세너느 자기 스스로 id를 걸러서 빈 값이 되는데 벨류랑 인서트 탕비에서는 키값을 제외한 데이터를 조회해서 가져와야되는데, 그게 아니라 순수 테이블 컬럼을 바라보기에 일관성이 깨지고 3번은 해당 내용은 기존에 키값일치를 대소문자 무시하는 계약이 있는데 이게 제대로 지켜지는 지 확인하는거구나 위 내가 한 질문과 내용도 나중에 문서화에 추가해줘

**판정 1** — pass. 워커 피드백 원문:

> 테스트 A는 insertString의 자체 필터링과 values/insertTypes가 순수 declaredColumns(테이블 컬럼)를 그대로 참조해 소스가 어긋난다는 일관성 붕괴 메커니즘을 정확히 짚었고, 테스트 B는 대소문자 무시가 새 규칙이 아니라 기존 계약이며 새 필터가 이를 지키는지 확인한다는 점도 정확히 짚었다.

**정답 정리** (메인이 08:00에 제시한 답)

- 전체 겹침 케이스: pre-fix에서 declaredColumns가 `["id"]`, key가 `["id"]`이면 `reconcileColumnsToUse`가 필터링하지 않으므로 `tableColumns`는 `["id"]` 그대로다. 그런데 `createInsertString`은 자기 필터로 "id"를 걸러 placeholder 0개짜리 `"INSERT INTO customers () VALUES()"`를 만들고, `values`와 `insertTypes`는 필터되지 않은 `tableColumns`를 순회해 크기 1이 된다. SQL은 0개인데 값은 1개인 불일치가 극단 케이스에서도 재현된다. after-fix는 `tableColumns`가 빈 리스트가 되어 값도 0개로 맞는다.
- 대소문자 케이스: 대소문자 무시 매칭은 이번 diff가 새로 만든 규칙이 아니다. `createInsertString`의 원래 필터(`keys.contains(columnName.toUpperCase(Locale.ROOT))`), `reconcileColumnsToUse`의 auto-discovery 분기(`keys.contains(meta.getParameterName().toUpperCase(Locale.ROOT))`), `matchInParameterValuesWithInsertColumns`의 lowerCaseName 폴백이 모두 이미 대소문자를 무시한다. 클래스에 `storesLowerCaseIdentifiers()` 같은 메서드가 있는 데서 보이듯 JDBC 드라이버마다 컬럼명 대소문자 반환이 달라 이 클래스는 애초에 대소문자에 관대하게 설계돼 있다. 트레이드오프 A의 기준소스로 정한 것이 `createInsertString`의 기존 필터였으므로, 새 필터는 그 규칙을 그대로 재사용한 것이고 이 테스트는 새 설계 결정이 아니라 기존 관례 준수를 확인한다.

---

## 반복된 오해 패턴

네 게이트에 걸쳐 되풀이된 패턴은 셋이고, 그중 마지막 하나는 오해가 아니라 유효한 검증 반사였다.

1. **방향 뒤집기 — 제외를 포함으로 읽음.** G2 시도 1에서 "선언한 제너레이트 키 자체를 반환할 수 있도록"이라고 이해했으나 실제는 정반대로 generated key를 빼는 필터였다. 워커가 "방향을 뒤집어 이해했다"로 직격했다.
2. **분기 혼동 — 다른 분기의 결과를 현재 분기에 귀속.** 같은 시도에서 "원래는 그냥 무시해서 빈 배열이였다"고 했는데, 빈 배열이 나올 수 있는 것은 auto-discovery 분기지 `declaredColumns` non-empty 분기가 아니었다. 메서드 하나 안에 분기가 둘이면 어느 분기 이야기인지부터 고정해야 한다.
3. **계약 변경 여부를 먼저 되묻는 습관.** G2의 07:34, G4의 08:00 두 번 모두 "이건 동작 방식이 바뀌는 건데 약속에 맞아?", "주석이나 계약에 그렇게 되어있어?"로 물었다. 이것은 오해가 아니라 유효한 검증 반사로, 07:34의 지적에 대해 메인도 "정확히 짚으셨고 그게 트레이드오프 A의 본질"이라고 인정했다.

## 교훈

이 게이트 기록에서 남길 만한 것은 네 가지다.

- **구체 값을 대입하면 방향 오해가 즉시 드러난다.** G2에서 메인이 정답 대신 "입력이 `["id","name"]`, key가 `["id"]`일 때 before의 반환은 정확히 무엇인가"를 되물은 직후 시도 2가 바로 pass했다. 추상적으로 "필터링한다"를 반복하는 것보다 입력 하나를 넣어 보는 것이 빠르다.
- **워커 판정이 없는 게이트는 정식 판정이 아니다.** G1은 pass로 기록됐지만 task.md 자체가 "워커 판정 없이 방향 확인"이라고 단서를 달았고, 실제로 같은 내용이 G2에서 정식 채점되어 1차 fail이 났다. 방향이 맞아 보인다고 이해가 확인된 것은 아니다.
- **메인의 해설도 그라운드 트루스가 아니다.** G3 이후 메인이 "pre-fix에서 insertString assertion이 FAIL했다"고 말한 것이 틀렸고, codex 리뷰 2회의 독립 지적으로 정정됐다. 게이트 판정 워커에게 메인의 해설이 아니라 실제 코드를 대조 기준으로 주는 규칙(lazymode 플레이북 4절)이 이런 상황을 겨냥한다.
- **되묻기는 게이트를 늦추지 않는다.** G4는 사용자가 두 건을 먼저 되물어 계약 근거를 확보한 뒤 답했고 1차에 pass했다. 이해가 서지 않은 채 복창하는 것보다 근거를 물어 확인하고 답하는 편이 판정에도 유리했다.
