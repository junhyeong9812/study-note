# PR #37014 분석 — SimpleJdbcInsert가 선언된 generated key 컬럼을 제외하지 못하는 결함

> 작성일: 2026-08-27 · 기준: PR base `1700fad16d2`, PR head `15d9e57760b` (spring-jdbc)
> 목적: 착수 시점 관점의 설명 문서 — 전체 메서드 그래프, 이름표 사전, 결함 경로 단계 추적, 계약, 수정안.
> 같은 폴더: [README](README.md) · [테스트 해설](tests.md) · [실구조](structure.md) · [이해 게이트](gates.md).

## 0. 결론 먼저

`TableMetaDataContext.reconcileColumnsToUse()`는 사용자가 `usingColumns(...)`로 컬럼을 명시한 경우 그 목록을 **아무 필터 없이 그대로 반환**하고(L208-210), generated key 제외는 바로 아래 메타데이터 자동탐색 분기(L211-221)에만 존재한다. 그 결과 `usingColumns`와 `usingGeneratedKeyColumns`에 같은 컬럼이 겹치면 `tableColumns`에 key가 남고, SQL의 물음표 개수(키 제외)와 값·타입 배열 길이(키 포함)가 갈라져 JDBC 드라이버 단계에서 실패하거나 값이 한 칸씩 밀린다.

수정은 `keys` 집합 계산을 두 분기 위로 끌어올리고 선언 분기도 같은 필터를 통과시키는 것이다 — 아래 자동탐색 분기가 이미 쓰던 규칙(`toUpperCase(Locale.ROOT)` 정규화 후 `Set` 대조)을 그대로 재사용하므로 새 규칙이 추가되지 않는다.

PR 상태: **OPEN, 리뷰 대기**(2026-07-07 제출, 라벨 `status: waiting-for-triage` / `in: data`, 코멘트·리뷰 없음, 2026-08-27 확인).

## 1. 무대 — 모듈·파일·클래스와 진입 API

무대는 `spring-jdbc`의 `org.springframework.jdbc.core.metadata` 패키지, 그중 `TableMetaDataContext` 한 클래스다. 이 클래스는 저장소 전체에서 `AbstractJdbcInsert`가 필드로 하나 보유하고(`AbstractJdbcInsert.java:73`) `TableMetaDataProviderFactory`가 인자로 받는 것(`TableMetaDataProviderFactory.java:50`)이 전부다. blast radius가 JDBC INSERT 경로 하나로 닫혀 있다.

공개 진입 API는 `SimpleJdbcInsert`의 fluent 설정 메서드 둘이다. 둘 다 얇은 위임이고, 채우는 상태는 `AbstractJdbcInsert`의 서로 **다른 필드 두 개**다 — 이 분리가 이번 결함의 무대다.

```java
	@Override                                                        // SimpleJdbcInsert.java:93
	public SimpleJdbcInsert usingColumns(String... columnNames) {    // :94
		setColumnNames(Arrays.asList(columnNames));
		return this;
	}

	@Override                                                                  // :99
	public SimpleJdbcInsert usingGeneratedKeyColumns(String... columnNames) {  // :100
		setGeneratedKeyNames(columnNames);
		return this;
	}
```

누가 어떤 상황에서 부르나. `usingColumns`는 (1) 메타데이터가 부실한 드라이버를 만나 컬럼을 직접 나열할 때, (2) `withoutTableColumnMetaDataAccess()`로 메타데이터 조회를 껐을 때, (3) `usingQuotedIdentifiers()`를 쓸 때 부른다. 세 번째는 선택이 아니라 **강제**다 — `compile()`이 따옴표 식별자에 명시 컬럼을 요구한다(`AbstractJdbcInsert.java:276-279`). 즉 사용자가 자발적으로 위험 조합에 들어가는 것이 아니라, API가 명시 컬럼을 요구하는 경로가 따로 있고 거기서 테이블 컬럼을 그대로 적으면 PK가 딸려 들어온다.

**자매 구조 — #37206과의 대응.** 이 결함은 같은 패키지의 `CallMetaDataContext.reconcileParameters()` 결함(PR #37206, 저장 함수 반환 파라미터 조회 정규화 누락)과 한 계열이다. 두 클래스 모두 이름이 `*MetaDataContext`이고, 둘 다 "사용자 선언 목록"과 "DB 메타데이터 목록"을 대조해 최종 목록 한 개를 만드는 `reconcile*` 메서드를 가지며, 그 목록이 하류의 SQL 문자열·바인딩·타입을 **전부** 파생시킨다. 결함의 모양까지 같다 — 한 분기만 다른 규칙을 쓴다. #37014는 INSERT 경로에서 **필터를 건너뛰는 분기**, #37206은 CALL 경로에서 **정규화를 건너뛰는 분기**다. 라운드5 findings가 J5를 "라운드4 J3과 같은 declared vs 메타데이터 reconcile 계열 — INSERT 경로에 이어 CALL 경로"로 기록한 것이 이 대응이다.

## 2. 전체 메서드 그래프

### 2.1 컴파일 경로 (선언 -> 컬럼 목록 -> 세 산출물 확정)

사용자의 fluent 설정이 컬럼 목록을 거쳐 SQL·타입 배열로 굳는 경로는 다음 한 줄기다.

```
 SimpleJdbcInsert.withTableName("customers")                        SimpleJdbcInsert.java:76
   .usingColumns("id","name")     -> setColumnNames(...)            :94  -> AbstractJdbcInsert:171
   .usingGeneratedKeyColumns("id")-> setGeneratedKeyNames(...)      :100 -> AbstractJdbcInsert:195
   .execute(map) / .executeAndReturnKey(map)
        |
        v
 AbstractJdbcInsert.doExecute(args)                                 AbstractJdbcInsert.java:359
        |-- checkCompiled() -> compile()                            :331, :271
        |                        |-- tableName null 검사             :273
        |                        +-- quoteIdentifiers && declaredColumns.isEmpty() -> 예외   :276
        v
 AbstractJdbcInsert.compileInternal()                               :299
        |-- tableMetaDataContext.processMetaData(ds, getColumnNames(), getGeneratedKeyNames())   :302
        |        |-- TableMetaDataProviderFactory.createMetaDataProvider(ds, this)
        |        +-- this.tableColumns = reconcileColumnsToUse(declaredColumns, generatedKeyNames)   <<< 결함 지점
        |                                TableMetaDataContext.java:204-222
        |-- this.insertString = tableMetaDataContext.createInsertString(getGeneratedKeyNames())  :303
        +-- this.insertTypes  = tableMetaDataContext.createInsertTypes()                         :304
```

### 2.2 실행 경로 (값 매칭 -> PreparedStatement 바인딩)

실행 시점에는 같은 컬럼 목록에서 값 목록이 만들어져 SQL·타입 배열과 함께 드라이버로 내려간다.

```
 doExecute(args)                                                    AbstractJdbcInsert.java:359
   +-- matchInParameterValuesWithInsertColumns(args)                :647 -> TableMetaDataContext:267
   |         for column in this.tableColumns:  values.add(찾은 값 또는 null)     :269-283
   +-- executeInsertInternal(values)                                :379
             +-- JdbcTemplate.update(getInsertString(), values.toArray(), getInsertTypes())      :383
                       +-- new ArgumentTypePreparedStatementSetter(args, argTypes)
                       |        길이 검증: args.length != argTypes.length 이면 예외    :49-51
                       |        (values 와 insertTypes 는 둘 다 tableColumns 기반이라 항상 같음 -> 통과)
                       +-- setValues(ps): parameterPosition 을 1부터 증가시키며 doSetValue   :58-83
                                          <<< 물음표가 모자라면 여기서 드라이버가 거부
```

**전파 구조.** `tableColumns`가 이 클래스의 단일 진실 원천이고, 세 소비자가 모두 거기서 파생된다. 그런데 셋 중 `createInsertString`만 자기 자리에서 키를 한 번 더 걸러낸다(`:322`). 그래서 `tableColumns`가 오염되면 **셋이 함께 틀리는 것이 아니라 하나만 옳고 둘이 틀린다** — 개수 불일치가 이 비대칭에서 나온다.

## 2.5 핵심 이름표 사전

이 흐름에서 "컬럼 목록"이 네 가지 얼굴로 돌아다닌다: 사용자가 선언한 목록, DB 메타데이터가 준 목록, 둘을 조정한 최종 목록, 그리고 SQL 문자열을 만들 때 한 번 더 걸러진 임시 목록. 아래 표는 각 이름이 그중 무엇을 들고 있는지를 명시한다. (예시 값은 `customers(id INTEGER, name VARCHAR)` 테이블 + `usingColumns("id","name")` + `usingGeneratedKeyColumns("id")` 조합)

| 이름표 | 무엇인가 / 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `declaredColumns` (`AbstractJdbcInsert.java:76`) | 사용자가 명시한 컬럼 이름 목록. final `ArrayList` | `usingColumns` 인자 그대로 | `setColumnNames`(:171)가 채우고 `getColumnNames`(:180)가 읽음 | 결함 분기의 입력. `["id","name"]` |
| `generatedKeyNames` (`:79`) | DB가 채워 줄 컬럼 이름 배열. 기본 길이 0 | `usingGeneratedKeyColumns` 인자 | `setGeneratedKeyNames`(:195) / `getGeneratedKeyNames`(:203) | 필터의 기준. `["id"]` |
| `compileInternal()` (`:299`) | 컬럼·SQL·타입 세 산출물을 순서대로 확정 | (없음) -> 필드 3개 설정 | `compile()`이 최초 실행 직전 1회 | 세 산출물이 여기서 한꺼번에 굳는다 |
| `processMetaData(ds, declared, keys)` (`TableMetaDataContext.java:189`) | provider를 만들고 `tableColumns`를 확정 | 두 목록 -> `this.tableColumns` | `compileInternal`(:302) | 결함으로 가는 유일한 통로 |
| `reconcileColumnsToUse(...)` (`:204`) | **선언 목록과 메타데이터 목록을 조정해 최종 컬럼 목록을 만든다.** `protected` 확장점 | `(List, String[])` -> `List<String>` | `processMetaData`(:191)만 | 결함 본체. 선언 분기(L208-210)가 무필터 |
| `keys` (`:211`, 수정 후 `:208`) | generated key 이름을 `toUpperCase(Locale.ROOT)`로 정규화한 `LinkedHashSet` — 대소문자 무관 대조표 | `String[]` -> `Set<String>` | `reconcileColumnsToUse` 안 | 수정 전에는 **조기 반환 아래**에 있어 선언 분기가 못 봤다. `{"ID"}` |
| `columns` (`:215`) | 자동탐색 분기가 쌓는 결과 리스트 | 메타데이터 순회 -> 필터 통과분 | 같은 메서드 | 수정은 같은 모양의 루프를 선언 분기에도 만든다 |
| `TableParameterMetaData.getParameterName()` | 드라이버가 `DatabaseMetaData.getColumns()`로 준 컬럼 이름 | -> `String` | `GenericTableMetaDataProvider.processTableColumns()`가 채움 | 자동탐색 분기의 원천. 선언 분기는 이걸 안 본다 |
| `tableColumns` (`:77`) | **이 클래스의 단일 진실 원천.** 최종 컬럼 목록 | `reconcileColumnsToUse` 결과 | `getTableColumns()`(:178)로 세 소비자가 읽음 | 오염되는 대상. 결함 시 `["id","name"]` |
| `generatedKeyColumnsUsed` (`:80`) | "키 컬럼을 쓰는 중"이라는 플래그 | `boolean` | `reconcileColumnsToUse`(:205-207)가 세팅, `createInsertString`(:332)이 읽음 | 빈 INSERT를 예외 대신 debug 로그로 넘기게 하는 스위치. 전체 겹침 케이스가 예외로 번지지 않는 이유 |
| `createInsertString(String...)` (`:291`) | INSERT SQL 문자열 조립 | `generatedKeyNames` -> SQL `String` | `compileInternal`(:303) | **자체 키 필터를 갖고 있다**(:292-295, :322) — 이 중복이 "하나만 옳은" 상태를 만든다 |
| `columnCount` (`:320`) | SQL에 실제로 들어간 컬럼 수 = **물음표 개수** | 카운터 | `createInsertString` 안 | 결함 시 1. 값·타입은 2 |
| `createInsertTypes()` (`:357`) | `java.sql.Types` 배열 조립 | (없음) -> `int[]` | `compileInternal`(:304) | `getTableColumns()` **전체**를 순회(:358, :365) — 필터 없음 |
| `parameterMap` (`:360`) | 메타데이터를 대문자 키로 색인한 맵 | -> `Map<String,TableParameterMetaData>` | `createInsertTypes` 안 | 타입 조회용. 결함과 무관하나 여기도 대문자 정규화 관례를 쓴다 |
| `matchInParameterValuesWithInsertColumns(SqlParameterSource)` (`:228`) | 컬럼 순서대로 바인딩 값 목록 조립. 원본 -> 소문자 -> 언더스코어 변환 -> 대소문자 무시 순으로 폴백 | 값 소스 -> `List<Object>` | `AbstractJdbcInsert:637` | `this.tableColumns` **전체**를 순회(:234) — 필터 없음 |
| `matchInParameterValuesWithInsertColumns(Map)` (`:267`) | 위와 같되 `Map` 입력 | `Map` -> `List<Object>` | `AbstractJdbcInsert:647` | 동일 |
| `values` | 위 두 메서드가 만든 바인딩 값 목록 | -> `List<Object>` | `doExecute`(:361, :372) | 결함 시 `[1, "Sven"]` (크기 2) |
| `insertString` / `insertTypes` (`:88` / `:91`) | 컴파일 결과 캐시 | -> `String` / `int[]` | `executeInsertInternal`(:383)이 함께 넘김 | 물음표 1개 vs 타입 2개 |
| `executeInsertInternal(values)` (`:379`) | 셋을 모아 `JdbcTemplate.update` 호출 | `List<?>` -> `int` | `doExecute` | 어긋남이 실제 SQL 실행에 도달하는 지점 |
| `args` / `argTypes` (`ArgumentTypePreparedStatementSetter.java:37-39`) | 바인딩 값·타입 쌍 | 생성자에서 길이 일치 검증(:49-51) | `JdbcTemplate.update` | **둘 다 2라 검증을 통과한다** — Spring이 못 막는 이유 |
| `parameterPosition` (`:59`) | 1부터 증가하는 물음표 위치 | 카운터 | `setValues`(:58) | 위치 2를 세팅하는 순간 드라이버가 거부 |
| `quoteIdentifiers` (`TableMetaDataContext.java:71`) | 식별자 따옴표 여부 | `boolean` | `compile()`(:276)이 명시 컬럼을 강제 | 사용자를 선언 경로로 밀어넣는 경로 |
| `accessTableColumnMetaData` (`:65`) | 메타데이터 조회 사용 여부 | `boolean` | `TableMetaDataProviderFactory` | 끄면 자동탐색 분기가 빈 목록을 주므로 명시 컬럼이 필수 |

이 표에서 결함이 한 줄로 보인다. **`keys`는 `reconcileColumnsToUse` 안에서 조기 반환 아래에 있었고, 선언 분기는 그 아래로 내려가지 않는다.** 같은 규칙이 `createInsertString`에도 복제되어 있었던 탓에 SQL만 옳은 부분 정합 상태가 만들어졌다.

## 3. 결함 경로 단계 추적

두 경로를 같은 입력(`customers(id, name)`, key = `id`)으로 나란히 따라간다. 정상 케이스는 사용자가 `usingColumns`를 쓰지 않은 자동탐색 경로이고, 결함 케이스는 `usingColumns("id","name")`을 쓴 선언 경로다. 각 단계의 변수 값을 함께 적는다.

| 단계 | 정상 (자동탐색: `usingColumns` 미사용) | 결함 (선언: `usingColumns("id","name")`) |
|---|---|---|
| 입력 | `declaredColumns=[]`, `generatedKeyNames=["id"]` | `declaredColumns=["id","name"]`, `generatedKeyNames=["id"]` |
| `reconcileColumnsToUse` L205-207 | `generatedKeyColumnsUsed=true` | `generatedKeyColumnsUsed=true` |
| L208 조기 반환 판정 | `isEmpty()`=true -> 통과해 아래로 | `isEmpty()`=false -> **`new ArrayList<>(declaredColumns)` 즉시 반환** |
| L211-214 `keys` 계산 | `keys={"ID"}` | **실행되지 않음** |
| L215-220 필터 루프 | 메타 `id` -> `"ID"` in keys -> 제외 / 메타 `name` -> 포함 | 실행되지 않음 |
| `tableColumns` | `["name"]` | `["id","name"]` (오염) |
| `createInsertString` L320-329 | `name`만 통과 -> `columnCount=1` | `id`는 자체 필터로 제외, `name`만 -> `columnCount=1` |
| `insertString` | `INSERT INTO customers (name) VALUES(?)` | `INSERT INTO customers (name) VALUES(?)` (**여기까지는 같다**) |
| `createInsertTypes` L358 | `new int[1]` -> `[Types.VARCHAR]` | `new int[2]` -> `[Types.INTEGER, Types.VARCHAR]` |
| `matchInParameterValues...` L234 | `["Sven"]` | `[1, "Sven"]` |
| `ArgumentTypePreparedStatementSetter` 생성자 L49 | 1 == 1 -> 통과 | 2 == 2 -> **통과**(Spring이 못 막음) |
| `setValues` L58-83 | 위치 1에 `"Sven"` -> 정상 | 위치 1에 `1`(id 값, INTEGER), 위치 2 세팅 시도 -> **물음표가 1개뿐** |
| 최종 결과 | INSERT 성공 | 드라이버가 파라미터 인덱스 범위 오류. 개수 검증이 느슨한 드라이버에서는 예외 대신 `name` 자리에 `id` 값이 들어가는 **정렬 어긋남** |

전체 겹침(`usingColumns("id")` + key `["id"]`)은 같은 구조의 극단값이다. 정상 경로는 `tableColumns=[]`, `columnCount=0`, 값 0개로 `INSERT INTO customers () VALUES()`가 나오고 `generatedKeyColumnsUsed` 덕에 예외가 아니다. 결함 경로는 `tableColumns=["id"]`이라 SQL은 물음표 0개인데 값과 타입은 1개가 되어, 어긋남의 방향이 같고 크기만 다르다.

대소문자가 다른 겹침(`usingColumns("ID","name")` + key `["id"]`)도 결함 경로에서는 필터 자체가 실행되지 않으므로 동일하게 어긋난다. 정상 경로는 `keys={"ID"}`와 `meta.getParameterName().toUpperCase()`를 대조하므로 표기 차이를 흡수한다.

## 4. 계약과 그 위반

계약은 javadoc보다 코드의 사용 방식에 더 많이 적혀 있다. 무엇이 고정되어 있고 결함이 어느 것을 어기는지 정리한다.

| 계약 | 출처 | 위반 여부 |
|---|---|---|
| `tableColumns`는 generated key가 **이미 제외된** 목록이다 | `createInsertTypes`(:358, :365)와 `matchInParameterValuesWithInsertColumns`(:234, :269)가 전체를 무필터 순회한다는 사실 | 선언 분기만 위반 |
| 컬럼 이름 대조는 `toUpperCase(Locale.ROOT)` 정규화 후 집합 비교 | 자동탐색 분기(:217), `createInsertString`(:322), `createInsertTypes`(:362)가 모두 같은 관용구 | 선언 분기는 대조 자체를 하지 않으므로 관례 밖 |
| 키 컬럼은 INSERT 컬럼 목록에서 빠지고 값은 `executeAndReturnKey`로 되돌려 받는다 | `usingGeneratedKeyColumns` javadoc(`SimpleJdbcInsertOperations.java:64-69`), 레퍼런스 예제(`data-access/jdbc/simple.adoc`)가 `usingColumns`에 key를 넣지 않음 | 결함 시 키가 목록에 남아 위반 |
| `usingColumns`는 "insert 문이 사용할 컬럼을 제한한다"고만 말한다 — key 배제 의무는 **어디에도 없다** | `SimpleJdbcInsertOperations.java:57-62` | 계약 공백. 사용자가 겹치게 쓰는 것이 문서상 금지되어 있지 않다 |
| 따옴표 식별자를 쓰면 명시 컬럼이 **필수**다 | `AbstractJdbcInsert.java:276-279` | 위반 아님. 다만 결함 조합을 강제로 유발하는 경로 |
| 값 배열과 타입 배열의 길이는 일치해야 한다 | `ArgumentTypePreparedStatementSetter.java:49-51` | 위반 아님 — **둘 다 같은 원천에서 나오므로 항상 일치한다.** 그래서 이 검증이 결함을 잡지 못한다 |
| 컬럼이 하나도 남지 않은 빈 INSERT는 key를 쓰는 중이면 정상 산출물이다 | `createInsertString`(:331-337) | 위반 아님. 전체 겹침 케이스가 예외로 번지지 않는 근거 |
| `reconcileColumnsToUse`는 `protected` — 하위 클래스 확장점 | 선언(:204) | 위반 아님. 수정이 건드리는 **표면**이므로 PR 본문이 별도로 밝힌 항목 |

## 5. 수정안

### 5.1 채택 — 키 집합을 분기 위로 올리고 선언 분기도 같은 필터를 통과시킨다

`keys` 계산을 조기 반환 위로 끌어올리고, 선언 분기에 아래 루프와 같은 모양의 필터를 하나 더 만든다.

```java
	// before (TableMetaDataContext.java:204-222, base 1700fad16d2)
	protected List<String> reconcileColumnsToUse(List<String> declaredColumns, String[] generatedKeyNames) {
		if (generatedKeyNames.length > 0) {
			this.generatedKeyColumnsUsed = true;
		}
		if (!declaredColumns.isEmpty()) {
			return new ArrayList<>(declaredColumns);
		}
		Set<String> keys = CollectionUtils.newLinkedHashSet(generatedKeyNames.length);
		for (String key : generatedKeyNames) {
			keys.add(key.toUpperCase(Locale.ROOT));
		}
		List<String> columns = new ArrayList<>();
		...
```

```java
	// after (TableMetaDataContext.java:204-228, head 15d9e57760b)
	protected List<String> reconcileColumnsToUse(List<String> declaredColumns, String[] generatedKeyNames) {
		if (generatedKeyNames.length > 0) {
			this.generatedKeyColumnsUsed = true;
		}
		Set<String> keys = CollectionUtils.newLinkedHashSet(generatedKeyNames.length);
		for (String key : generatedKeyNames) {
			keys.add(key.toUpperCase(Locale.ROOT));
		}
		if (!declaredColumns.isEmpty()) {
			List<String> columns = new ArrayList<>();
			for (String column : declaredColumns) {
				if (!keys.contains(column.toUpperCase(Locale.ROOT))) {
					columns.add(column);
				}
			}
			return columns;
		}
		List<String> columns = new ArrayList<>();
		...
```

**왜 이 위치인가.** `tableColumns`의 소비자가 셋이므로 규칙을 소비자에 두면 같은 코드가 넷으로 흩어진다. 생산자 한 곳에서 걸러 두면 모든 소비자가 자동으로 일관되고, 이미 `createInsertString`에 복제되어 있던 필터는 아무것도 걸러내지 않는 무해한 중복으로 되돌아간다. 비교 방식을 새로 정하지 않고 바로 아래 자동탐색 루프의 `toUpperCase(Locale.ROOT)` + `Set` 관용구를 그대로 재사용한 것도 같은 이유다 — 새 규칙을 발명하면 그것이 또 하나의 단일 출처 후보가 된다.

**동작이 달라지는 대상.** `generatedKeyNames`가 비면 `keys`도 비고 필터는 전부 통과시키므로, key를 쓰지 않는 기존 사용자에게는 결과가 문자 그대로 동일하다. 달라지는 것은 두 목록이 겹치는 조합뿐이고, 그 조합은 수정 전에 실행이 실패했으므로 의존하는 정상 코드가 존재할 수 없다.

### 5.2 기각한 대안 — 겹침을 명시적 예외로 거부

`usingColumns`와 `usingGeneratedKeyColumns`에 같은 컬럼이 들어오면 `compile()` 시점에 `InvalidDataAccessApiUsageException`을 던지는 안이다. 기각 사유는 셋이다. (1) 새 예외 상황을 계약에 추가하는 것이라 조용한 제외보다 파급이 크다. (2) 바로 아래 자동탐색 분기가 이미 "겹치면 조용히 제외"로 동작하므로 두 분기가 서로 다른 정책을 갖게 된다 — 지금 고치려는 비대칭을 방향만 바꿔 재생산한다. (3) 사용자 경험이 열위다. 테이블 컬럼을 그대로 적은 자연스러운 코드가 예외로 막히는 대신, 자동탐색 경로와 같은 결과를 내는 편이 놀라움이 적다.

### 5.3 하위 클래스 표면

`reconcileColumnsToUse`가 `protected`이므로 하위 클래스가 오버라이드해 선언 목록을 그대로 쓰는 구현이 있을 수 있다. 그런 구현은 이 수정의 영향을 받지 않지만(오버라이드가 이기므로) 여전히 결함 동작을 유지한다. PR 본문은 이 점을 "Note on impact"로 분리해 밝히고 5.2의 대안도 함께 제시했다 — 변경 자체보다 변경이 건드리는 표면을 먼저 알리는 방식이다.

## 6. 범위 밖과 인접 영향

이 PR이 일부러 손대지 않은 인접 코드와, 수정이 남기는 표면은 다음 다섯 갈래로 정리된다.

- **`createInsertString`의 중복 필터**(:292-295, :322)는 이번에 제거하지 않았다. 수정 후에는 아무것도 걸러내지 않지만, 제거하면 `reconcileColumnsToUse`를 오버라이드한 하위 클래스가 즉시 깨질 수 있다. 중복을 남기는 쪽이 안전하다.
- **`matchInParameterValuesWithInsertColumns(Map)`의 대소문자 폴백**(:270-280)은 컬럼 이름을 값 소스의 키와 맞추는 별개 축이다. 이번 필터와 규칙이 비슷해 보이지만 대상이 다르다(값 소스 키 vs generated key 이름) — 건드리지 않았다.
- **같은 패턴의 다른 위치**는 `CallMetaDataContext.reconcileParameters()`다(PR #37206). "한 분기만 다른 규칙을 쓴다"는 형태가 같으므로 §1의 대응 관계가 그대로 적용되지만, 그쪽은 필터 누락이 아니라 이름 정규화 누락이고 증상도 다르다(조용한 오답 + 스퓨리어스 예외). 두 PR을 하나로 묶지 않은 이유는 파일·증상·테스트가 모두 다르기 때문이다.
- **하위호환**: 겹치지 않는 조합은 결과가 완전히 동일하고, 겹치는 조합은 수정 전에 실행이 실패했다. 공개 API 시그니처·DB 스키마·이벤트 계약 변화 없음. 유일한 표면은 5.3의 `protected` 확장점이다.
- **검증**: `TableMetaDataContextTests`에 부분 겹침·전체 겹침·대소문자 겹침 세 건이 추가됐다. 세 건 모두 수정 전 red이며, 각 테스트 안의 `insertString` 단언은 전후 모두 green이라 SQL 생성 쪽을 건드리지 않았음을 함께 고정한다. 상세는 [tests.md](tests.md).
