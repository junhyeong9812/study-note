# PR #37014 — Exclude declared generated key columns from SimpleJdbcInsert

## 0. 정향

이 PR은 `SimpleJdbcInsert`에서 `usingColumns(...)`와 `usingGeneratedKeyColumns(...)`에 같은 컬럼을 동시에 선언했을 때 실행이 깨지는 문제를 고친다.\
원인은 컬럼 목록을 확정하는 `TableMetaDataContext.reconcileColumnsToUse()`가 메타데이터 자동탐색 경로에서만 generated key를 걸러내고, 명시 선언 경로에서는 걸러내지 않았기 때문이다.\
그 결과 SQL의 물음표 개수와 바인딩되는 값 개수가 어긋나 JDBC 드라이버 단계에서 실패한다.\
수정은 자동탐색 경로가 이미 쓰던 필터를 명시 선언 경로에도 똑같이 적용하는 것이다.

> **generated key(생성 키)** — DB가 INSERT 시점에 값을 스스로 만들어 주는 컬럼.\
> 예: `customers(id, name)`에서 `id`가 auto-increment PK면, 애플리케이션은 `id`를 보내지 않고 DB가 채운 값을 돌려받는다.

- 대상 파일: `spring-jdbc/src/main/java/org/springframework/jdbc/core/metadata/TableMetaDataContext.java`
- PR: https://github.com/spring-projects/spring-framework/pull/37014 (상태 OPEN, 리뷰 대기)

---

## 1. 배경 — `SimpleJdbcInsert`란 무엇인가

`SimpleJdbcInsert`는 테이블 이름과 값 Map만 주면 INSERT 문을 대신 만들어 주는 객체다.\
클래스 Javadoc이 그 계약을 직접 밝힌다.

```java
/**
 * A {@code SimpleJdbcInsert} is a multi-threaded, reusable object providing easy
 * (batch) insert capabilities for a table. It provides meta-data processing to
 * simplify the code needed to construct a basic insert statement. All you need
 * to provide is the name of the table and a {@code Map} containing the column
 * names and the column values.
 *
 * <p>The meta-data processing is based on the {@code DatabaseMetaData} provided
 * by the JDBC driver. As long as the JDBC driver can provide the names of the columns
 * for a specified table then we can rely on this auto-detection feature. If that
 * is not the case, then the column names must be specified explicitly.
 */
public class SimpleJdbcInsert extends AbstractJdbcInsert implements SimpleJdbcInsertOperations {
```

핵심은 "메타데이터 기반"이라는 말이다.\
`GenericTableMetaDataProvider.processTableColumns()`가 `DatabaseMetaData.getColumns(...)`를 호출해 테이블의 컬럼 이름과 SQL 타입을 읽어 `TableParameterMetaData` 목록으로 쌓아 둔다.\
`SimpleJdbcInsert`는 그 목록을 근거로 INSERT 문자열과 타입 배열을 조립하므로, 사용자는 SQL을 한 줄도 쓰지 않는다.

> **테이블 메타데이터(DatabaseMetaData)** — JDBC 드라이버가 제공하는 "이 DB에 무슨 테이블·컬럼이 있는지"를 묻는 창구.\
> 예: `getColumns(null, "me", "customers", null)`을 부르면 `id INTEGER NOT NULL`, `name VARCHAR NULL` 같은 행이 돌아온다.

`SimpleJdbcInsert` 자체는 얇은 fluent 껍데기다.\
설정 메서드는 전부 부모 `AbstractJdbcInsert`의 setter로 위임하고 자기 자신을 돌려준다.

```java
	@Override
	public SimpleJdbcInsert usingColumns(String... columnNames) {
		setColumnNames(Arrays.asList(columnNames));
		return this;
	}

	@Override
	public SimpleJdbcInsert usingGeneratedKeyColumns(String... columnNames) {
		setGeneratedKeyNames(columnNames);
		return this;
	}
```

두 메서드가 채우는 상태는 `AbstractJdbcInsert`의 서로 다른 필드 두 개다.\
이 분리가 이번 버그의 무대이므로 필드 선언을 그대로 본다.

```java
	/** List of column names to be used in insert statement. */
	private final List<String> declaredColumns = new ArrayList<>();

	/** The names of the columns holding the generated key. */
	private String[] generatedKeyNames = new String[0];
```

**generated key란 DB가 INSERT 시점에 값을 스스로 만들어 주는 컬럼이다.**\
auto-increment PK나 시퀀스 기본값이 대표적이다.\
애플리케이션이 값을 보내지 않아야 DB가 채울 수 있으므로, generated key 컬럼은 INSERT의 컬럼 목록에서 빠져야 한다.\
그 대신 Spring은 `executeAndReturnKey(...)`로 DB가 만든 값을 되돌려 준다.\
`usingGeneratedKeyColumns("id")`는 "이 컬럼은 내가 안 넣을 테니 너희가 채우고, 채운 값을 나에게 알려 달라"는 선언이다.

> **자동 증가 컬럼(auto-increment PK)** — 행이 들어올 때마다 DB가 1씩 올려 채우는 기본키 컬럼.\
> 예: `customers` 테이블의 `id`가 그것이며, 그래서 사용자 코드에는 `id` 값이 아예 없다.

> **`executeAndReturnKey(...)`** — INSERT를 실행하고 DB가 만든 키 값을 되돌려 받는 실행 메서드.\
> 예: `insert.executeAndReturnKey(Map.of("name", "Sven"))`을 부르면 DB가 채운 `id` 값이 반환된다.

레퍼런스 문서의 표준 예제도 이 규칙을 전제로 쓰여 있다.\
`framework-docs/modules/ROOT/pages/data-access/jdbc/simple.adoc`의 "Specifying Columns for a `SimpleJdbcInsert`" 절은 `usingColumns`에 key 컬럼을 넣지 않는다.

```java
			this.insertActor = new SimpleJdbcInsert(dataSource)
					.withTableName("t_actor")
					.usingColumns("first_name", "last_name")
					.usingGeneratedKeyColumns("id");
```

`usingColumns`에 `id`가 빠져 있는 것이 우연이 아니라 정답이었다는 사실이, 뒤에서 볼 문제의 성격을 미리 알려 준다.

---

## 2. 수정 전 동작 방식 — 컬럼 결정과 키 컬럼 처리

### 2.1 컬럼은 compile 시점에 딱 한 번 확정된다

컬럼 결정은 `compile()` 시점에 딱 한 번 일어난다.\
`AbstractJdbcInsert.compileInternal()`이 그 파이프라인 전체다.

```java
	protected void compileInternal() {
		DataSource dataSource = getJdbcTemplate().getDataSource();
		Assert.state(dataSource != null, "No DataSource set");
		this.tableMetaDataContext.processMetaData(dataSource, getColumnNames(), getGeneratedKeyNames());
		this.insertString = this.tableMetaDataContext.createInsertString(getGeneratedKeyNames());
		this.insertTypes = this.tableMetaDataContext.createInsertTypes();
		...
	}
```

세 줄이 순서대로 컬럼 목록, SQL 문자열, 타입 배열을 확정한다.\
사용자 호출부터 이 세 줄까지가 한 줄기로 내려간다.

```text
execute(params) / executeAndReturnKey(params)      사용자 호출
        |
        v
checkCompiled()                                    최초 1회만 compile() 실행
        |
        v
compileInternal()
        |
        +-- (1) processMetaData(ds, 선언목록, 키목록)
        |          -> reconcileColumnsToUse(...)    여기서 키 목록과 컬럼 목록이 만난다
        |          -> tableColumns 확정
        |
        +-- (2) createInsertString(키목록)
        |          -> "INSERT INTO customers (name) VALUES(?)"
        |
        +-- (3) createInsertTypes()
                   -> [Types.VARCHAR]
```

키 목록(`generatedKeyNames`)이 컬럼 목록과 만나는 자리는 (1)과 (2) 두 곳이며, 이 중복이 뒤에서 문제의 모양을 결정한다.

> **compile(컴파일)** — 설정을 읽어 SQL 문자열·타입 배열·컬럼 목록을 한 번 계산해 두고 이후 실행에서 재사용하는 단계.\
> 예: `insert.execute(...)`를 백 번 불러도 `INSERT INTO customers (name) VALUES(?)` 문자열은 첫 호출에서 한 번만 만들어진다.

`processMetaData`는 결과를 `tableColumns` 필드에 저장한다.

```java
	public void processMetaData(DataSource dataSource, List<String> declaredColumns, String[] generatedKeyNames) {
		this.metaDataProvider = TableMetaDataProviderFactory.createMetaDataProvider(dataSource, this);
		this.tableColumns = reconcileColumnsToUse(declaredColumns, generatedKeyNames);
	}
```

**따라서 `tableColumns`가 이 클래스의 단일 진실 원천이다.**\
SQL 문자열, 타입 배열, 실행 시 바인딩할 값 목록이 모두 이 리스트에서 파생된다.

> **단일 진실 원천(single source of truth)** — 같은 사실을 여러 곳이 각자 들고 있지 않고 한 곳에서만 계산해 나머지가 그것을 참조하는 구조.\
> 예: 여기서는 `tableColumns` 하나가 물음표 개수·타입 배열 길이·값 목록 길이를 전부 결정한다.

### 2.2 키 제외 필터가 한쪽 분기에만 있었다

그 리스트를 만드는 메서드가 수정 전에는 이렇게 생겼다.

```java
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
		for (TableParameterMetaData meta : obtainMetaDataProvider().getTableParameterMetaData()) {
			if (!keys.contains(meta.getParameterName().toUpperCase(Locale.ROOT))) {
				columns.add(meta.getParameterName());
			}
		}
		return columns;
	}
```

메서드는 두 갈래로 나뉜다.\
사용자가 `usingColumns(...)`로 컬럼을 선언했으면 그 목록을 그대로 복사해 반환하고 끝난다.\
선언하지 않았으면 아래로 내려가 메타데이터가 준 전체 컬럼에서 generated key 이름을 **대문자 정규화 후 집합 비교로 제외**한다.

> **대소문자 정규화(`toUpperCase(Locale.ROOT)`)** — 이름을 비교하기 전에 전부 대문자로 접어 표기 차이를 없애는 것.\
> 예: 사용자가 적은 `"ID"`와 드라이버가 돌려준 `"id"`가 같은 컬럼임을 알아보려면 둘 다 `"ID"`로 접어 비교해야 한다.

`customers(id, name)` 테이블에 `usingColumns("id","name")`과 `usingGeneratedKeyColumns("id")`를 준 입력으로 두 갈래를 나란히 놓으면 이렇다.

```text
reconcileColumnsToUse(["id","name"], ["id"])
        |
        v
declaredColumns 가 비어 있나?
        |
  +-----+--------------------------------+
  | 아니오 (선언 경로)                     | 예 (메타데이터 자동탐색 경로)
  v                                      v
return new ArrayList<>(declaredColumns)  keys = {"ID"}   (대문자 정규화 집합)
  키 필터를 거치지 않는다                  메타데이터 컬럼 중 keys 에 없는 것만 수집
  tableColumns = ["id", "name"]           tableColumns = ["name"]
  -> 키가 그대로 남는다                    -> 키가 빠져 있다
```

즉 키 제외 로직은 자동탐색 경로에만 존재했고, 위쪽 조기 반환은 아무 필터도 거치지 않았다.

### 2.3 세 소비자 중 하나만 자체 필터를 갖고 있다

`tableColumns`의 세 소비자 중 SQL 문자열을 만드는 `createInsertString`만 자체 필터를 갖고 있다.

```java
	public String createInsertString(String... generatedKeyNames) {
		Set<String> keys = CollectionUtils.newLinkedHashSet(generatedKeyNames.length);
		for (String key : generatedKeyNames) {
			keys.add(key.toUpperCase(Locale.ROOT));
		}
		...
		insertStatement.append(" (");
		int columnCount = 0;
		for (String columnName : getTableColumns()) {
			if (!keys.contains(columnName.toUpperCase(Locale.ROOT))) {
				columnCount++;
				...
			}
		}
		insertStatement.append(") VALUES(");
		...
		String params = String.join(", ", Collections.nCopies(columnCount, "?"));
```

물음표 개수는 `columnCount`, 곧 **키를 걸러낸 뒤의 개수**다.\
반면 나머지 두 소비자는 `tableColumns`를 통째로 순회한다.

```java
	public int[] createInsertTypes() {
		int[] types = new int[getTableColumns().size()];
		...
		for (String column : getTableColumns()) {
```

```java
	public List<Object> matchInParameterValuesWithInsertColumns(SqlParameterSource parameterSource) {
		List<Object> values = new ArrayList<>();
		...
		for (String column : this.tableColumns) {
```

**여기서 계약이 하나 드러난다. `tableColumns`는 이미 generated key가 제외된 상태여야 한다.**\
자동탐색 경로에서는 그 계약이 지켜졌으므로 `createInsertString`의 자체 필터는 아무것도 걸러내지 않는 무해한 중복이었고, 세 소비자의 개수가 항상 일치했다.\
선언 경로만 그 계약을 깨뜨렸다.

---

## 3. 무엇이 문제였나

### 3.1 세 산출물의 개수가 갈라진다

**선언 경로에서 key 컬럼이 `tableColumns`에 남으면, 물음표 개수와 바인딩 값 개수가 갈라진다.**\
`customers(id, name)` 테이블에 `id`가 generated key인 상황을 그대로 따라가 본다.

```java
new SimpleJdbcInsert(dataSource)
        .withTableName("customers")
        .usingColumns("id", "name")
        .usingGeneratedKeyColumns("id");
```

`reconcileColumnsToUse`는 `declaredColumns`가 비어 있지 않으므로 `["id", "name"]`을 그대로 반환한다.\
이어서 `createInsertString`은 자체 필터로 `id`를 빼고 SQL을 만든다.

```
INSERT INTO customers (name) VALUES(?)
```

그런데 `createInsertTypes()`는 크기 2의 배열을, `matchInParameterValuesWithInsertColumns(...)`는 원소 2개의 값 목록을 만든다.\
세 산출물의 개수를 나란히 놓으면 어긋남이 한눈에 보인다.

| 산출물 | 순회 대상 | 수정 전 개수 |
|---|---|---|
| `insertString`의 물음표 | 키를 제외한 `tableColumns` | 1 |
| `insertTypes` | `tableColumns` 전체 | 2 |
| 바인딩 값 목록 | `tableColumns` 전체 | 2 |

### 3.2 Spring은 못 막고 드라이버가 거부한다

실행은 `AbstractJdbcInsert.executeInsertInternal()`에서 이 셋을 한꺼번에 넘긴다.

```java
		return getJdbcTemplate().update(getInsertString(), values.toArray(), getInsertTypes());
```

값 배열과 타입 배열은 둘 다 2로 길이가 같으므로 `ArgumentTypePreparedStatementSetter`의 생성자 검증("args and argTypes parameters must match")은 통과한다.\
Spring은 여기서 막아 주지 못한다.\
그 다음 `setValues`가 파라미터 위치를 1부터 증가시키며 값을 세팅한다.

```java
	public void setValues(PreparedStatement ps) throws SQLException {
		int parameterPosition = 1;
		if (this.args != null && this.argTypes != null) {
			for (int i = 0; i < this.args.length; i++) {
				...
					doSetValue(ps, parameterPosition, this.argTypes[i], arg);
					parameterPosition++;
```

> **`PreparedStatement` / 컬럼 바인딩** — 물음표 자리를 뚫어 둔 SQL 문장에 값을 위치 번호로 끼워 넣는 JDBC 객체.\
> 예: `INSERT INTO customers (name) VALUES(?)`에는 위치 1 하나뿐이라, 위치 2에 값을 넣으려 하면 드라이버가 거부한다.

물음표가 하나뿐인 `PreparedStatement`에 위치 2를 세팅하는 순간 드라이버가 파라미터 인덱스 범위 오류를 던진다.

```text
SQL     INSERT INTO customers (name) VALUES(?)
                                            ^
                                            |  물음표는 이 하나뿐
바인딩
  위치 1  <- 값 1        (id 값, Types.INTEGER)   name 자리에 id 값이 들어간다
  위치 2  <- 값 "Sven"   (Types.VARCHAR)          물음표가 없는 위치
                 |
                 v
        드라이버가 파라미터 인덱스 범위 오류를 던진다
        (개수 검증이 느슨한 드라이버라면 예외 없이 그대로 들어간다)
```

**예외 메시지는 드라이버마다 다르지만 실패 지점은 동일하다.**\
Spring이 아니라 JDBC 드라이버가 거부하므로, 사용자 입장에서는 자기 설정과 무관해 보이는 저수준 예외를 받게 되고 원인 추적이 어렵다.

> **JDBC 드라이버** — DB 제품별로 JDBC 표준을 구현한 라이브러리. 최종적으로 SQL과 파라미터를 DB에 보내는 주체.\
> 예: 여기서 예외를 던지는 것은 스프링 코드가 아니라 PostgreSQL·MySQL 등의 드라이버 구현이다.

### 3.3 더 조용한 위험 — 정렬 어긋남

더 조용한 위험도 함께 있다.\
위치 1에 들어가는 값은 `tableColumns`의 첫 원소인 `id`의 값인데, SQL의 첫 물음표는 `name` 컬럼 자리다.\
타입도 `id`의 `Types.INTEGER`가 따라간다.\
즉 개수 검증을 느슨하게 처리하는 드라이버를 만나면 예외 대신 **엉뚱한 컬럼에 엉뚱한 값이 들어가는 정렬 어긋남**이 남는다.

> **무음 실패(silent failure)** — 잘못된 결과가 예외도 로그도 없이 정상처럼 저장되는 실패.\
> 예: `name` 컬럼에 `id` 값 `1`이 문자열로 들어가도 아무도 오류를 보지 못한 채 INSERT가 "성공"한다.

### 3.4 피하기 어려운 경로가 있다

이 조합을 피하기 어려운 경로도 있다.\
`compile()`은 따옴표 식별자를 쓰면 명시 컬럼을 요구한다.

```java
			if (isQuoteIdentifiers() && this.declaredColumns.isEmpty()) {
				throw new InvalidDataAccessApiUsageException(
						"Explicit column names must be provided when using quoted identifiers");
			}
```

> **따옴표 식별자(quoted identifiers)** — 컬럼·테이블 이름을 DB의 인용 부호로 감싸 대소문자나 예약어를 그대로 쓰게 하는 옵션.\
> 예: `usingQuotedIdentifiers()`를 켜면 `INSERT INTO "customers" ("name")`처럼 이름이 감싸지고, 그 대신 `usingColumns(...)`가 필수가 된다.

`usingQuotedIdentifiers()`나 `withoutTableColumnMetaDataAccess()`를 쓰는 사용자는 반드시 `usingColumns(...)`로 컬럼을 나열해야 한다.\
그때 테이블의 컬럼을 그대로 적는 것은 자연스러운 행동이고, 거기에 PK가 들어가면 곧바로 이 버그를 밟는다.\
`usingColumns`의 Javadoc이 "the column names that the insert statement should be limited to use"라고만 말할 뿐 key 컬럼 배제 의무를 언급하지 않는 점도 오해를 돕는다.

---

## 4. 수정 해설 — 무엇을 왜 바꿨나

**수정은 키 제외 필터를 선언 경로에도 적용해 두 경로가 같은 계약을 지키게 만든 것이다.**\
키 집합 생성 코드를 분기 위로 끌어올리고, 조기 반환을 필터링 반환으로 바꿨다.

```java
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
		for (TableParameterMetaData meta : obtainMetaDataProvider().getTableParameterMetaData()) {
			if (!keys.contains(meta.getParameterName().toUpperCase(Locale.ROOT))) {
				columns.add(meta.getParameterName());
			}
		}
		return columns;
	}
```

같은 입력이 수정 전후로 어떻게 달라지는지를 나란히 놓으면 이렇다.

```text
입력: usingColumns("id","name") + usingGeneratedKeyColumns("id")

수정 전                                 수정 후 (최초 제출본)
+-----------------------------------+  +-----------------------------------+
| tableColumns = ["id", "name"]     |  | tableColumns = ["name"]           |
| SQL    ... (name) VALUES(?)    1  |  | SQL    ... (name) VALUES(?)    1  |
| types  [INTEGER, VARCHAR]      2  |  | types  [VARCHAR]               1  |
| values [1, "Sven"]             2  |  | values ["Sven"]                1  |
+-----------------------------------+  +-----------------------------------+
  -> 드라이버가 위치 2에서 거부한다        -> 세 산출물이 모두 1로 맞는다
```

설계상의 선택 세 가지를 짚어 둔다.

첫째, **소비자가 아니라 생산자를 고쳤다.**\
`createInsertTypes`와 `matchInParameterValuesWithInsertColumns`에 각각 필터를 추가할 수도 있었지만, 그러면 같은 규칙이 네 곳에 흩어진다.\
`tableColumns`를 만들 때 한 번 걸러 두면 모든 소비자가 자동으로 일관된다.

둘째, **비교 방식을 기존 코드와 동일하게 맞췄다.**\
`toUpperCase(Locale.ROOT)`로 정규화한 뒤 `Set`으로 비교하는 것은 아래 자동탐색 루프가 이미 쓰던 방식이다.\
DB 메타데이터의 식별자 대소문자가 드라이버마다 다르기 때문에 대소문자 무시 비교가 필수인데, 새 규칙을 발명하는 대신 있던 규칙을 재사용했다.

셋째, **키 집합 계산을 분기 밖으로 올렸다.**\
`generatedKeyNames`가 비어 있으면 집합도 비고 필터는 통과만 하므로, 선언 컬럼만 쓰고 key를 쓰지 않는 기존 사용자에게는 결과가 그대로다.\
즉 동작이 달라지는 대상은 두 목록이 겹치는 조합뿐이다.

호환성 판단의 근거는 명확하다.\
**겹치는 조합은 수정 전에도 실행이 실패했으므로, 그 동작에 의존하는 정상 코드는 존재할 수 없다.**\
다만 `reconcileColumnsToUse`가 `protected` 확장점이라 하위 클래스가 오버라이드했을 가능성이 있다.\
PR 본문은 이 점을 "Note on impact"로 따로 분리해 밝히고, 조용히 제외하는 대신 겹침을 명시적으로 거부하는 대안도 함께 제시했다.\
변경 자체보다 그 변경이 건드리는 표면을 리뷰어에게 먼저 알린 것이다.

> **`protected` 확장점** — 하위 클래스가 상속해서 덮어쓸 수 있도록 열어 둔 메서드. 외부 코드가 이미 오버라이드했을 수 있어 함부로 바꾸기 어렵다.\
> 예: 누군가 `reconcileColumnsToUse`를 오버라이드해 두었다면, 이 PR의 필터는 그 코드에는 적용되지 않는다.

`TableMetaDataContext`는 저장소 전체에서 `AbstractJdbcInsert`만이 인스턴스로 보유한다.\
blast radius가 JDBC insert 경로 하나로 닫혀 있다는 뜻이다.

> **blast radius(영향 반경)** — 어떤 변경이 잘못됐을 때 피해가 번질 수 있는 최대 범위.\
> 예: 이 클래스를 쓰는 곳이 `AbstractJdbcInsert` 한 군데뿐이므로, 영향은 JDBC INSERT 경로 밖으로 나가지 않는다.

---

## 5. 검증 — 테스트가 무엇을 고정하나

테스트는 `spring-jdbc/src/test/java/org/springframework/jdbc/core/simple/TableMetaDataContextTests.java`에 세 개가 추가됐다.\
이 테스트 클래스는 Mockito로 `DatabaseMetaData`와 `ResultSet`을 흉내 내므로 실제 DB 없이 컬럼 메타데이터를 원하는 대로 지정할 수 있다.

> **mock(목 객체)** — 진짜 객체 대신 "이 메서드를 부르면 이 값을 돌려준다"만 정해 둔 가짜 객체.\
> 예: `given(columnsResultSet.getString("COLUMN_NAME")).willReturn("id", "name")`으로 실제 DB 없이 `customers(id, name)` 스키마를 만들어 낸다.

`declaredColumnsIncludingGeneratedKeyAreExcluded`는 부분 겹침, 곧 이 버그의 표준 재현을 고정한다.\
단정문이 3절에서 어긋났던 세 산출물을 정확히 하나씩 겨냥한다.

```java
		context.processMetaData(dataSource, List.of("id", "name"), keyCols);
		List<Object> values = context.matchInParameterValuesWithInsertColumns(map);
		String insertString = context.createInsertString(keyCols);
		int[] insertTypes = context.createInsertTypes();

		assertThat(insertString).as("insert string should exclude the declared generated key column")
				.isEqualTo("INSERT INTO customers (name) VALUES(?)");
		assertThat(values).as("values should exclude the declared generated key column").containsExactly("Sven");
		assertThat(insertTypes.length).as("types array must match the number of placeholders").isEqualTo(1);
```

`declaredColumnsMatchingGeneratedKeysProduceEmptyInsert`는 완전 겹침을 고정한다.\
선언 컬럼이 전부 generated key면 남는 컬럼이 없다.

```java
		assertThat(insertString).as("empty insert not generated correctly")
				.isEqualTo("INSERT INTO customers () VALUES()");
		assertThat(values).as("no values should remain once the only declared column is the generated key").isEmpty();
		assertThat(insertTypes).as("no types should remain once the only declared column is the generated key").isEmpty();
```

이 기대값은 새로 만든 것이 아니라 기존 `tableWithSingleColumnGeneratedKey` 테스트가 자동탐색 경로에 대해 이미 고정해 둔 문자열과 같다.\
**두 경로가 같은 입력에 같은 결과를 내야 한다는 것이 이 테스트의 진짜 주장이다.**\
빈 INSERT가 예외로 번지지 않는 이유는 `generatedKeyColumnsUsed` 플래그가 `true`라 `createInsertString`이 debug 로그만 남기고 넘어가기 때문이다.

`declaredColumnsExcludeGeneratedKeyRegardlessOfCase`는 대소문자 무시 비교를 고정한다.\
선언은 `"ID"`, key 이름은 `"id"`다.

```java
		context.processMetaData(dataSource, List.of("ID", "name"), keyCols);
		...
		assertThat(insertString).as("insert string should exclude the declared generated key column regardless of case")
				.isEqualTo("INSERT INTO customers (name) VALUES(?)");
```

이 세 번째 테스트가 특히 중요하다.\
단순 `List.remove` 같은 대소문자 민감 구현으로 리팩터링하면 앞의 두 테스트는 통과하지만 이것만 깨지기 때문이다.\
즉 "제외한다"가 아니라 "대소문자를 무시하고 제외한다"까지를 계약으로 못박는다.

---

## 6. 상태와 교훈

PR은 2026-07-07에 열렸고 현재까지 `OPEN` 상태다.\
리뷰도 코멘트도 아직 붙지 않았으며 라벨 라우팅을 기다리는 중이다.

**교훈 하나. 파생 값이 여럿이면 규칙은 파생물이 아니라 원천에 두어야 한다.**\
`createInsertString`이 자기 자리에서 키를 한 번 더 걸러낸 것은 방어적으로 보이지만, 실제로는 `tableColumns`가 이미 걸러져 있다는 계약을 흐려 놓았다.\
그 중복 덕분에 SQL만 옳고 타입과 값은 틀린 상태가 만들어졌고, 셋이 다 같이 틀렸다면 오히려 더 빨리 발견됐을 것이다.\
같은 규칙이 두 곳에 있으면 한쪽이 빠졌을 때 증상이 부분적으로만 나타나 진단이 늦어진다.

**교훈 둘. 조기 반환은 그 아래 코드가 지키던 불변식을 조용히 건너뛴다.**\
`if (!declaredColumns.isEmpty()) return new ArrayList<>(declaredColumns);`는 그 자체로는 흠잡을 데 없는 최적화처럼 읽힌다.\
문제는 아래에 있던 "generated key는 제외한다"는 후처리를 함께 건너뛴다는 사실이 그 줄만 봐서는 보이지 않는다는 점이다.\
분기마다 반환값이 지켜야 할 사후조건을 메서드 계약으로 먼저 적어 두면, 새 분기를 추가할 때 무엇을 함께 지켜야 하는지가 드러난다.

> **불변식(invariant)** — 코드가 어느 경로로 흐르든 항상 참이어야 하는 규칙.\
> 예: 여기서는 "`tableColumns`에는 generated key가 들어 있지 않다"가 불변식이고, 선언 경로만 그것을 깼다.

---

연관 ko-docs (모듈 지도): `spring-jdbc/04-jdbcclient-와-simple-연산.md`

## 7. 리뷰 재작업 (2026-09-07, append) — 조용한 제외에서 fail-fast로

이 절부터는 위 1~6절이 서술한 최초 제출본(제외 방식)이 리뷰로 **방향이 뒤집힌** 기록이다.\
위 절들은 제출 시점 기준 그대로 두고(append-only), 여기서 무엇이 왜 바뀌었는지를 잇는다.

### 7.1 추가 요구사항 (sbrannen 리뷰, 2026-09-05, CHANGES_REQUESTED)

리뷰가 요구한 것은 구현 세부가 아니라 방향 자체였다.\
아래는 그 요구사항과 배경 교훈이다.

> **CHANGES_REQUESTED** — GitHub 리뷰 상태 중 "이대로는 머지할 수 없으니 고쳐 달라"는 판정.\
> 예: 여기서는 sbrannen이 "조용한 제외" 방식 자체를 되돌리라고 요구했다.

> **fail-fast** — 잘못된 상태를 안고 계속 가지 않고 발견 즉시 예외로 멈추는 설계.\
> 예: 겹치는 컬럼을 조용히 빼는 대신 `InvalidDataAccessApiUsageException`을 던져 설정 오류임을 알린다.

- "조용한 제외보다 **명시적 실패**를 원한다" — `usingColumns(...)`와 `usingGeneratedKeyColumns(...)`에 같은 컬럼을 선언한 것은 설정 오류이므로, 컬럼이 SQL에서 조용히 사라지게 하지 말고 명확한 메시지로 fail-fast.
- 구체 지시 2가지: (1) `reconcileColumnsToUse()`에서 겹침 발견 시 제외 대신 `InvalidDataAccessApiUsageException`(문제 컬럼명 명시)을 throw — `AbstractJdbcInsert.compile()`의 기존 검증("Table name is required" 등)과 일관. (2) 테스트를 제외 단언에서 예외(메시지 포함) 단언으로 교체.
- 부수 조치: PR 제목을 "Reject overlapping declared and generated key columns in SimpleJdbcInsert"로 변경, draft 전환, `type: enhancement` 라벨.
- 배경 교훈: 이 방향은 최초 설계에서 우리가 **기각했던 B안** 그대로다. 당시 기각 사유는 "auto-discovery의 '조용히 제외' 관례와 불일치"였는데, 메인테이너의 판단은 자동 추론(메타데이터가 채운 것)과 명시 선언(사용자가 적은 두 목록)의 성격이 다르다는 것 — **자동 경로의 관례를 명시 경로에 이식하면 설정 오류를 삼키게 된다.** 같은 판별에서 #36912는 우리 해석이 맞았고(#36917은 반대), 이번엔 상대가 맞았다.

### 7.2 변경사항 (커밋 f8705a2f2be, 이전 15d9e57760b를 amend + force-push)

같은 자리에서 필터링을 겹침 수집과 예외로 바꿨고, keys 호이스팅과 auto-discovery 분기는 그대로 두었다.

> **amend + force-push** — 직전 커밋을 새 내용으로 덮어쓰고, 그 바뀐 이력을 원격 브랜치에 강제로 밀어 넣는 것.\
> 예: 커밋 `15d9e57760b`가 `f8705a2f2be`로 바뀌면서 PR에는 커밋 하나짜리 이력이 그대로 유지된다.

```java
// 최초 제출본(제외) — keys를 두 분기 위로 끌어올리고, 선언 분기에서 겹치는 컬럼을 걸러냄
if (!declaredColumns.isEmpty()) {
    List<String> columns = new ArrayList<>();
    for (String column : declaredColumns) {
        if (!keys.contains(column.toUpperCase(Locale.ROOT))) {
            columns.add(column);
        }
    }
    return columns;
}
```
```java
// 재작업본(fail-fast) — 같은 자리에서 겹침을 수집해 예외. keys 호이스팅은 유지
if (!declaredColumns.isEmpty()) {
    List<String> overlapping = new ArrayList<>();
    for (String column : declaredColumns) {
        if (keys.contains(column.toUpperCase(Locale.ROOT))) {
            overlapping.add(column);
        }
    }
    if (!overlapping.isEmpty()) {
        throw new InvalidDataAccessApiUsageException(
                "Declared columns " + overlapping + " must not overlap with generated key columns");
    }
    return new ArrayList<>(declaredColumns);
}
```

같은 설정이 두 방식에서 어떻게 끝나는지를 나란히 놓으면 이렇다.

```text
설정: usingColumns("id","name") + usingGeneratedKeyColumns("id")

최초 제출본 (조용한 제외)               재작업본 (fail-fast)
+-----------------------------------+  +-----------------------------------+
| tableColumns = ["name"]           |  | overlapping = ["id"]              |
| SQL  ... (name) VALUES(?)         |  | throw InvalidDataAccess           |
| INSERT 는 그대로 실행된다          |  |       ApiUsageException           |
| id 는 SQL 에서 사라진다            |  | "Declared columns [id] must not   |
|                                   |  |  overlap with generated key ..."  |
+-----------------------------------+  +-----------------------------------+
  -> 설정 오류가 삼켜진다                 -> 설정 오류가 컴파일 단계에서 드러난다
```

- 비교는 대문자 정규화(매칭 전용), `overlapping`에는 **선언 원본 표기 그대로** 담는다 — 오류 메시지는 사용자가 자기 코드에 타이핑한 문자열로 되돌려줘야 찾기 쉽다.
- auto-discovery 분기는 바이트 동일 — keys Set 구성이 `generatedKeyNames` 인자에만 의존하는 순수 계산이라 호이스팅이 무부작용.
- 테스트: 제외 단언 3건 -> 예외 단언 2건(`[id]` / 대소문자 변형 `[ID]` — 원본 표기 고정) + 비겹침 가드 1건 + 공유 목 헬퍼(중복 셋업 제거).

> **호이스팅(hoisting)** — 여러 분기가 공통으로 쓰는 계산을 분기 위로 끌어올려 한 번만 수행하게 하는 것.\
> 예: `keys` 집합 계산이 조기 반환 아래에 있던 것을 위로 올려, 선언 분기도 같은 집합을 보게 만들었다.

### 7.3 절차 구조 도식 — 사용자 호출에서 예외까지

겹침이 있는 설정은 첫 실행에서 컴파일 단계에 들어가자마자 예외로 끝난다.\
사용자 호출부터 그 예외까지의 경로는 다음과 같다.

```text
사용자 코드
  new SimpleJdbcInsert(ds).withTableName("customers")
      .usingColumns("id", "name")              <- 선언 목록
      .usingGeneratedKeyColumns("id")          <- 생성 키 목록 (겹침!)
   |
   | insert.execute(params)          (compile()을 직접 불러도 동일 지점 도달)
   v
SimpleJdbcInsert.execute (L124)
   -> AbstractJdbcInsert.doExecute (L359)
        checkCompiled()  (L331)     <- 모든 doExecute*의 첫 줄
          isCompiled() == false -> compile() (L271)
            -> compileInternal() (L299)
                 (1) tableMetaDataContext.processMetaData(ds, 선언목록, 키목록)  (L302)
                       -> reconcileColumnsToUse (L204)
                            keys = 키목록 대문자 Set              (호이스팅, 순수 계산)
                            선언 분기: 컬럼 대문자화 비교
                              겹침 발견 -> overlapping에 원본 표기 수집
                              -> throw InvalidDataAccessApiUsageException  ***
                 (2) createInsertString  (L303)  <- 도달 못 함
                 (3) createInsertTypes   (L304)  <- 도달 못 함
                 this.compiled = true            <- 실행 안 됨
   <- 예외가 콜스택을 타고 첫 execute 호출자까지 전파
```

요점: 실행 때마다 반복되는 런타임 오류가 아니라 **최초 실행(또는 명시적 compile) 한 번에서 설정 오류로** 드러난다.\
겹침이 없으면 (1)(2)(3)이 순서대로 완료되고 이후 execute는 컴파일 산출물을 재사용한다.

### 7.4 머지 (2026-09-07, append)

재작업 force-push 약 6시간 뒤 sbrannen이 approve(08:32)하고 main에 머지했다(머지 커밋 e06482ad519 — GitHub 머지, author 크레딧 유지, 우리 커밋과 diff 0).\
코멘트: "This has been merged into main. Thanks".\
최초 제출(7/8) 기준 두 달, 리뷰 방향 전환(9/5)부터는 이틀 — **방향이 정해진 재작업은 빠르게 처리된다**는 것과, CHANGES_REQUESTED가 거절이 아니라 머지로 가는 가장 확실한 경로였다는 것이 이 PR의 마지막 교훈.\
감사 답글 게시(9/8).
