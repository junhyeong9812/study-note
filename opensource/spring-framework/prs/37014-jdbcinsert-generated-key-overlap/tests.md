# PR #37014 — 테스트 해설 (테스트 하나하나)

> PR #37014 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

`spring-jdbc/src/test/java/org/springframework/jdbc/core/simple/TableMetaDataContextTests.java`에
세 건이 추가됐다. 세 건 모두 수정 전에 실패하는 red이며, 서로 다른 겹침 형태(부분 겹침,
완전 겹침, 대소문자 다른 겹침)를 하나씩 맡는다. 아래 red/green 판별은 실행 결과가 아니라
diff 논리 — 수정 전 `reconcileColumnsToUse`가 선언 컬럼을 무필터로 반환한다는 사실 — 에서
유도한 것이다.

## 0. 세 테스트가 공유하는 무대

세 테스트는 실제 DB 없이 `TableMetaDataContext`를 직접 호출한다. `SimpleJdbcInsert`를
거치지 않고 `processMetaData` -> `matchInParameterValuesWithInsertColumns` ->
`createInsertString` -> `createInsertTypes` 순서를 손으로 재현하는데, 이 순서는
`AbstractJdbcInsert.compileInternal()`이 하는 일과 같다. 결함이 사는 이음매를 그대로
겨냥하되 JDBC 드라이버는 개입시키지 않는 배치다.

mock이 흉내 내는 실제 상황은 다음과 같다.

- `dataSource`·`connection`·`databaseMetaData` (클래스 필드, `@BeforeEach`에서 연결):
  JDBC 드라이버가 제공하는 메타데이터 창구. 실제 DB에 붙지 않고도 "이 테이블에는
  이런 컬럼이 있다"를 테스트가 정할 수 있게 한다.
- `metaDataResultSet`: `DatabaseMetaData.getTables(...)`의 결과 집합.
  `next()`가 `true, false`를 순서대로 돌려주는 것은 "조회된 테이블이 정확히 한 건이고
  그 뒤는 없다"는 뜻이다. `TABLE_SCHEM`/`TABLE_NAME`/`TABLE_TYPE`은 스키마 탐색이
  `me` 스키마에서 `customers`라는 테이블을 찾았다는 상황을 만든다.
- `columnsResultSet`: `DatabaseMetaData.getColumns(...)`의 결과 집합. 여기서 지정하는
  `COLUMN_NAME`/`DATA_TYPE`/`NULLABLE`이 곧 가상의 테이블 스키마다.
- `storesLowerCaseIdentifiers()`가 `true`인 것은 드라이버가 식별자를 소문자로 저장한다는
  선언이며, 생성되는 SQL에 `INSERT INTO customers`처럼 소문자 이름이 나오는 이유다.
- `getUserName()`이 `USER`인 것은 `getColumns(null, USER, TABLE, null)` 호출의 스키마
  인자로 쓰이기 위한 것이다.
- `MapSqlParameterSource`는 사용자가 실행 시점에 넘기는 값 Map이고,
  `List.of("id", "name")`은 `usingColumns("id", "name")`에,
  `keyCols`는 `usingGeneratedKeyColumns("id")`에 대응한다.

## 1. 부분 겹침 — red

첫 테스트는 선언 컬럼 둘 중 하나가 generated key와 겹치는 표준 재현이다.

```java
@Test
void declaredColumnsIncludingGeneratedKeyAreExcluded() throws Exception {
	final String TABLE = "customers";
	final String USER = "me";

	ResultSet metaDataResultSet = mock();
	given(metaDataResultSet.next()).willReturn(true, false);
	given(metaDataResultSet.getString("TABLE_SCHEM")).willReturn(USER);
	given(metaDataResultSet.getString("TABLE_NAME")).willReturn(TABLE);
	given(metaDataResultSet.getString("TABLE_TYPE")).willReturn("TABLE");

	ResultSet columnsResultSet = mock();
	given(columnsResultSet.next()).willReturn(true, true, false);
	given(columnsResultSet.getString("COLUMN_NAME")).willReturn("id", "name");
	given(columnsResultSet.getInt("DATA_TYPE")).willReturn(Types.INTEGER, Types.VARCHAR);
	given(columnsResultSet.getBoolean("NULLABLE")).willReturn(false, true);

	given(databaseMetaData.getDatabaseProductName()).willReturn("MyDB");
	given(databaseMetaData.getDatabaseProductVersion()).willReturn("1.0");
	given(databaseMetaData.getUserName()).willReturn(USER);
	given(databaseMetaData.storesLowerCaseIdentifiers()).willReturn(true);
	given(databaseMetaData.getTables(null, null, TABLE, null)).willReturn(metaDataResultSet);
	given(databaseMetaData.getColumns(null, USER, TABLE, null)).willReturn(columnsResultSet);

	MapSqlParameterSource map = new MapSqlParameterSource();
	map.addValue("id", 1);
	map.addValue("name", "Sven");
	String[] keyCols = new String[] { "id" };
	context.setTableName(TABLE);
	context.processMetaData(dataSource, List.of("id", "name"), keyCols);
	List<Object> values = context.matchInParameterValuesWithInsertColumns(map);
	String insertString = context.createInsertString(keyCols);
	int[] insertTypes = context.createInsertTypes();

	assertThat(insertString).as("insert string should exclude the declared generated key column")
			.isEqualTo("INSERT INTO customers (name) VALUES(?)");
	assertThat(values).as("values should exclude the declared generated key column").containsExactly("Sven");
	assertThat(insertTypes.length).as("types array must match the number of placeholders").isEqualTo(1);
	verify(metaDataResultSet, atLeastOnce()).next();
	verify(columnsResultSet, atLeastOnce()).next();
	verify(metaDataResultSet).close();
	verify(columnsResultSet).close();
}
```

- **주장**: `usingColumns("id", "name")`와 `usingGeneratedKeyColumns("id")`가 겹칠 때
  SQL의 물음표 개수, 바인딩 값 개수, 타입 배열 길이가 모두 1로 일치해야 한다.
- **mock이 흉내 내는 것**: `columnsResultSet`이 만드는 `id INTEGER NOT NULL`,
  `name VARCHAR NULL` 두 컬럼은 auto-increment PK를 가진 평범한 테이블이다. 사용자가
  "테이블에 있는 컬럼을 그대로 적었을 뿐"인 상황을 두 줄로 재현한다.
- **fix 전 결과와 이유**: `reconcileColumnsToUse`가 선언 컬럼을 그대로 복사하므로
  `tableColumns`는 `["id", "name"]`이다. 여기서 세 단언의 운명이 갈린다.
  첫째 단언은 **fix 전에도 통과한다** — `createInsertString`이 자체 필터로 `id`를
  걸러내기 때문이다. 실패하는 것은 둘째와 셋째다. `values`는 `tableColumns` 전체를
  순회해 `[1, "Sven"]`이 되므로 `containsExactly("Sven")`이 깨지고, `insertTypes.length`는
  2라 1과 다르다. 즉 이 테스트는 "SQL만 옳고 값과 타입은 틀린" 어긋남 자체를 red로
  드러낸다.
- **역할**: 이 버그의 표준 재현. 세 단언이 3절에서 갈라졌던 세 산출물을 하나씩
  겨냥하도록 배치돼 있어, 어느 산출물이 어긋났는지가 실패 메시지에서 바로 읽힌다.
- **verify 네 줄**: 메타데이터 결과 집합이 실제로 소비되고 닫혔는지를 본다. 이 수정과
  무관해 전후 모두 green이며, 이웃 테스트 `tableWithSingleColumnGeneratedKey`의 관용구를
  그대로 따른 것이다. 선언 경로에서도 메타데이터 조회 자체는 여전히 일어난다는 사실을
  부수적으로 고정하는 효과가 있다.

## 2. 완전 겹침 — red

mock 준비는 1번과 같은 형태이고, 차이는 컬럼이 `id` 하나뿐이라는 점과 선언 컬럼이
`List.of("id")`라는 점이다.

```java
	ResultSet columnsResultSet = mock();
	given(columnsResultSet.next()).willReturn(true, false);
	given(columnsResultSet.getString("COLUMN_NAME")).willReturn("id");
	given(columnsResultSet.getInt("DATA_TYPE")).willReturn(Types.INTEGER);
	given(columnsResultSet.getBoolean("NULLABLE")).willReturn(false);
```

```java
	MapSqlParameterSource map = new MapSqlParameterSource();
	map.addValue("id", 1);
	String[] keyCols = new String[] { "id" };
	context.setTableName(TABLE);
	context.processMetaData(dataSource, List.of("id"), keyCols);
	List<Object> values = context.matchInParameterValuesWithInsertColumns(map);
	String insertString = context.createInsertString(keyCols);
	int[] insertTypes = context.createInsertTypes();

	assertThat(insertString).as("empty insert not generated correctly")
			.isEqualTo("INSERT INTO customers () VALUES()");
	assertThat(values).as("no values should remain once the only declared column is the generated key").isEmpty();
	assertThat(insertTypes).as("no types should remain once the only declared column is the generated key").isEmpty();
```

- **주장**: 선언 컬럼이 전부 generated key면 남는 컬럼이 없고, 그 결과는 빈 INSERT여야
  한다. 그리고 그 빈 INSERT는 예외가 아니라 정상 산출물이다.
- **fix 전 결과와 이유**: `tableColumns`가 `["id"]`이므로 `values`는 `[1]`,
  `insertTypes`는 길이 1이다. 둘째·셋째 단언이 실패해 red다. 첫째 단언은 여기서도
  fix 전에 통과한다 — `createInsertString`의 자체 필터가 `id`를 빼면 `columnCount`가
  0이 되어 `INSERT INTO customers () VALUES()`가 나오기 때문이다.
- **왜 예외가 아닌가**: `generatedKeyColumnsUsed` 플래그가 `true`라서
  `createInsertString`이 debug 로그만 남기고 빈 컬럼 목록을 허용한다. 이 테스트는 그
  경로가 유지됨을 함께 고정한다.
- **역할**: 경계값 재현. 기대 문자열은 새로 지어낸 값이 아니라 기존
  `tableWithSingleColumnGeneratedKey`가 자동탐색 경로에 대해 이미 고정해 둔 문자열과
  같다. **두 경로(선언·자동탐색)가 같은 입력에 같은 결과를 낸다**는 것이 이 테스트의
  진짜 주장이다.

## 3. 대소문자 무시 겹침 — red, 그리고 구현 방식까지 못박는 가드

mock 준비는 1번과 동일하고, 선언 컬럼과 값 Map의 키만 `"ID"`로 바뀐다.

```java
	MapSqlParameterSource map = new MapSqlParameterSource();
	map.addValue("ID", 1);
	map.addValue("name", "Sven");
	String[] keyCols = new String[] { "id" };
	context.setTableName(TABLE);
	context.processMetaData(dataSource, List.of("ID", "name"), keyCols);
	List<Object> values = context.matchInParameterValuesWithInsertColumns(map);
	String insertString = context.createInsertString(keyCols);

	assertThat(insertString).as("insert string should exclude the declared generated key column regardless of case")
			.isEqualTo("INSERT INTO customers (name) VALUES(?)");
	assertThat(values).as("values should exclude the declared generated key column regardless of case")
			.containsExactly("Sven");
```

- **주장**: 선언은 `"ID"`, key 이름은 `"id"`처럼 표기가 달라도 같은 컬럼으로 보고
  제외해야 한다.
- **mock이 흉내 내는 것**: DB 메타데이터의 식별자 대소문자는 드라이버마다 다르고,
  사용자가 `usingColumns`에 적는 표기와 `usingGeneratedKeyColumns`에 적는 표기가
  일치한다는 보장이 없다. 그 어긋남을 `"ID"` 대 `"id"` 한 쌍으로 압축했다.
- **fix 전 결과와 이유**: `tableColumns`가 `["ID", "name"]`이라 `values`는
  `[1, "Sven"]`이다. 둘째 단언이 실패해 red다. 첫째 단언은 fix 전에도 통과한다.
  `createInsertString`의 자체 필터가 이미 `toUpperCase(Locale.ROOT)` 정규화 후
  비교하기 때문이다.
- **역할이 앞의 둘과 다른 지점**: 이 테스트는 재현이면서 동시에 **fix의 구현 방식을
  제약하는 가드**다. `declaredColumns.removeAll(List.of(generatedKeyNames))` 같은
  대소문자 민감 구현으로 고치면 1·2번은 통과하고 이것만 깨진다. 즉 "제외한다"가
  아니라 "대소문자를 무시하고 제외한다"까지를 계약으로 못박는다.
- **`insertTypes`를 보지 않는 이유**: 대소문자 축은 컬럼 선정 단계에서 결정되므로,
  선정 결과를 대표하는 SQL 문자열과 값 목록 둘만 보면 충분하다. 세 산출물의 개수
  일치는 1번이 이미 맡고 있다.

## fixture

이 PR은 새 fixture를 만들지 않았다. 세 테스트가 쓰는 재료는 모두 기존
`TableMetaDataContextTests`의 클래스 필드와 `@BeforeEach`다.

```java
private DataSource dataSource = mock();

private Connection connection = mock();

private DatabaseMetaData databaseMetaData = mock();

private TableMetaDataContext context = new TableMetaDataContext();


@BeforeEach
void setUp() throws Exception {
	given(connection.getMetaData()).willReturn(databaseMetaData);
	given(dataSource.getConnection()).willReturn(connection);
}
```

`dataSource.getConnection().getMetaData()`가 mock `databaseMetaData`로 이어지는 이
두 줄이, 각 테스트가 `given(databaseMetaData.getColumns(...))`로 스키마를 직접 짜 넣을 수
있게 하는 통로다. 테이블별 `ResultSet` mock은 각 테스트 안에서 지역 변수로 만든다 —
테스트마다 스키마가 다르기 때문이며, 이 역시 기존 테스트들의 관용구다.

## 분류와 역할 요약

세 테스트를 fix 전 결과와 역할로 정리하면 다음과 같다. 판별 근거는 diff 논리이며
실행으로 측정한 값이 아니다.

| 테스트 | 겹침 형태 | fix 전 | 실패하는 단언 |
|---|---|---|---|
| `declaredColumnsIncludingGeneratedKeyAreExcluded` | 부분 (`id`,`name` 중 `id`) | red | values, insertTypes.length |
| `declaredColumnsMatchingGeneratedKeysProduceEmptyInsert` | 완전 (`id`만) | red | values, insertTypes |
| `declaredColumnsExcludeGeneratedKeyRegardlessOfCase` | 대소문자 불일치 (`ID` 대 `id`) | red | values |

세 테스트 모두 red라는 점은 이 결함의 성격을 그대로 반영한다. 겹침 조합은 수정 전에
어차피 실행이 실패했으므로, 보존해야 할 기존 동작이 그 조합에는 존재하지 않는다.
그래서 이 PR에는 "fix 전에도 green인 별도 가드 테스트"가 없다. 대신 보존 축은 두 곳이
맡는다. 하나는 각 테스트 안의 `insertString` 단언 — fix 전후 모두 통과하며, 수정이
SQL 생성 쪽을 건드리지 않았음을 고정한다. 다른 하나는 기존 스위트, 특히
`tableWithSingleColumnGeneratedKey`를 비롯한 자동탐색 경로 테스트들이며, 키 집합 계산을
분기 밖으로 끌어올린 변경이 그 경로를 그대로 두었는지를 지킨다.

마지막으로 3번 테스트는 red이면서 동시에 구현 방식 가드라는 이중 역할을 한다. red/가드는
테스트 파일 안의 배타적 분류가 아니라, "fix 전 결과"와 "이 테스트를 깨뜨리는 잘못된
수정이 무엇인가"라는 두 질문에 대한 각각의 답이다.

## 리뷰 재작업 후 테스트 (2026-09-07, append)

위 절들이 해설한 제외 단언 3건은 리뷰(fail-fast 방향 전환)로 커밋 f8705a2f2be에서 교체됐다. 현재 구성: `overlappingDeclaredAndGeneratedKeyColumnsAreRejected`(선언 [id, name] + 키 [id] -> IDAAUE, withMessage "...[id] must not overlap..."), `...RegardlessOfCase`(선언 [ID, name] -> 메시지 "[ID]" — 보고가 원본 표기임을 고정), `declaredColumnsWithoutOverlapAreUsedAsIs`(선언 [name] + 키 [id] -> INSERT INTO customers (name) VALUES(?) — 비겹침 회귀 가드), 공유 헬퍼 `initializeTwoColumnCustomersTable()`. 예외 단언은 `processMetaData` 호출을 람다로 감싼다 — throw가 그 안(reconcileColumnsToUse)에서 나와 후속 문장이 실행되지 않기 때문. 재작업 상세와 절차 도식은 README 7절.
