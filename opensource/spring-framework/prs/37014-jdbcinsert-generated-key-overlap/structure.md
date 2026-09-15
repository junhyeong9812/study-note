# PR #37014 — 무대 구조와 워크플로우: SimpleJdbcInsert 메타데이터 파이프라인

> PR #37014의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이하 file:line은 모두 이 커밋의 작업 트리 기준이며, `reconcileColumnsToUse`는 아직 PR 이전 상태(선언 경로 조기 반환)다.

## 1. 무대 — 실구조

이 PR의 무대는 `SimpleJdbcInsert`가 SQL을 조립하기까지 거치는 **메타데이터 파이프라인** 전체다.\
사용자 API(`SimpleJdbcInsert`)와 실행 엔진(`AbstractJdbcInsert`), 그 둘이 공유하는 계산 창구(`TableMetaDataContext`), 그리고 JDBC 드라이버에서 컬럼 정보를 실제로 긁어 오는 제공자 계층(`TableMetaDataProvider` 구현들)이 한 줄로 늘어서 있다.\
버그는 이 중 계산 창구 한 메서드의 분기 하나에 있었지만, 왜 그것이 조용히 잘못된 SQL을 만드는지는 파이프라인 전체를 봐야 보인다.

> **`SimpleJdbcInsert`** — INSERT SQL을 손으로 쓰지 않고 테이블 이름과 컬럼 이름만 알려 주면 문장을 대신 만들어 주는 스프링 JDBC의 헬퍼 객체.\
> 예: `withTableName("customers").usingColumns("id","name")`라고 설정해 두면 `INSERT INTO customers (id, name) VALUES(?, ?)`가 만들어진다.

> **메타데이터 파이프라인(metadata pipeline)** — 사용자 설정과 DB가 알려 준 테이블 정보를 차례로 거쳐 최종 SQL·타입 배열을 확정하는 처리 사슬.\
> 예: 여기서는 `SimpleJdbcInsert` → `AbstractJdbcInsert` → `TableMetaDataContext` → `TableMetaDataProvider` → JDBC 드라이버 순으로 이어진다.

> **generated key(생성 키)** — DB가 INSERT 시점에 값을 스스로 만들어 주는 컬럼.\
> 예: auto-increment 기본키 `id`는 애플리케이션이 값을 보내지 않아야 DB가 채울 자리가 생긴다.

먼저 큰 그림이다.\
왼쪽이 사용자, 오른쪽이 드라이버 방향이며, 화살표는 소유·호출 관계다.

```text
 사용자 코드
    │  .withTableName("customers").usingColumns("id","name").usingGeneratedKeyColumns("id")
    ▼
 SimpleJdbcInsert                                     SimpleJdbcInsert.java:53
   implements SimpleJdbcInsertOperations              SimpleJdbcInsertOperations.java:34
   (fluent 껍데기 — 전부 부모 setter 로 위임하고 this 반환)
    ├─ usingColumns(String...)            :94  → setColumnNames(...)         AbstractJdbcInsert.java:171
    └─ usingGeneratedKeyColumns(String...) :100 → setGeneratedKeyNames(...)  AbstractJdbcInsert.java:195
    │
    ▼ extends
 AbstractJdbcInsert                                   AbstractJdbcInsert.java:64
    ├─ final JdbcTemplate jdbcTemplate                :70
    ├─ final TableMetaDataContext tableMetaDataContext = new TableMetaDataContext()   :73  ★ 유일한 보유자
    ├─ final List<String> declaredColumns             :76   ← usingColumns 가 채움
    ├─ String[] generatedKeyNames                     :79   ← usingGeneratedKeyColumns 가 채움
    ├─ volatile boolean compiled                      :85
    ├─ String insertString                            :88   ← compile 산출물 1
    ├─ int[] insertTypes                              :91   ← compile 산출물 2
    ├─ compile()                                      :271
    ├─ compileInternal()                              :299  ← 파이프라인의 심장
    ├─ checkCompiled()                                :331  ← 첫 실행 시 지연 compile
    └─ executeInsertInternal(List)                    :379  → jdbcTemplate.update(sql, values, types)  :383
    │
    ▼ 보유
 TableMetaDataContext                                 TableMetaDataContext.java:50
    ├─ @Nullable String tableName / catalogName / schemaName        :56 / :59 / :62
    ├─ boolean accessTableColumnMetaData = true                     :65
    ├─ boolean quoteIdentifiers = false                             :71
    ├─ @Nullable TableMetaDataProvider metaDataProvider             :74
    ├─ List<String> tableColumns                                    :77  ★ 단일 진실 원천
    ├─ boolean generatedKeyColumnsUsed                              :80
    ├─ processMetaData(DataSource, List<String>, String[])          :189
    ├─ reconcileColumnsToUse(List<String>, String[])   protected    :204 ★ 버그가 살던 메서드
    ├─ matchInParameterValuesWithInsertColumns(SqlParameterSource)  :228   소비자 1
    ├─ matchInParameterValuesWithInsertColumns(Map)                 :267   소비자 1'
    ├─ createInsertString(String...)                                :291   소비자 2
    ├─ createInsertTypes()                                          :357   소비자 3
    └─ private static final class QuoteHandler                      :420
    │
    ▼ 생성 위임
 TableMetaDataProviderFactory.createMetaDataProvider(...)  TableMetaDataProviderFactory.java:50
    │   databaseProductName 으로 구현 선택 :56-74 → initializeWithMetaData :79
    │   → context.isAccessTableColumnMetaData() 이면 initializeWithTableColumnMetaData :81-84
    ▼
 TableMetaDataProvider (interface)                    TableMetaDataProvider.java:34
    ├─ initializeWithMetaData(DatabaseMetaData)                     :41
    ├─ initializeWithTableColumnMetaData(DatabaseMetaData, cat, schema, table)  :53
    ├─ List<TableParameterMetaData> getTableParameterMetaData()     :60
    ├─ boolean isGetGeneratedKeysSupported()                        :114
    └─ String getIdentifierQuoteString()                            :144
    │
    ▼ 기본 구현 + DB별 서브클래스
 GenericTableMetaDataProvider                         GenericTableMetaDataProvider.java:45
    ├─ final List<TableParameterMetaData> tableParameterMetaData    :75   ← 컬럼 목록의 원본
    ├─ boolean storesUpperCaseIdentifiers = true / storesLowerCaseIdentifiers = false  :66 / :69
    ├─ locateTableAndProcessMetaData(...)   private                 :273  → getTables(...)  :279
    └─ processTableColumns(...)             private                 :347  → getColumns(...) :357
       └ Oracle/PostgreSQL/Derby/HSQL/MySQL 서브클래스가 식별자 규칙만 덮어씀
          OracleTableMetaDataProvider:43 · PostgresTableMetaDataProvider:34
          DerbyTableMetaDataProvider:29 · HsqlTableMetaDataProvider:30 · MySQLTableMetaDataProvider:29

 TableParameterMetaData (값 객체)                      TableParameterMetaData.java:26
    ├─ final String parameterName  :28   ├─ final int sqlType :30   └─ final boolean nullable :32
```

여기서 구조적으로 중요한 사실 하나.\
`TableMetaDataContext`를 인스턴스로 보유하는 곳은 저장소 전체에서 `AbstractJdbcInsert.java:73` 한 줄뿐이다(팩토리가 파라미터로 받는 것 제외).\
즉 이 클래스의 blast radius는 JDBC insert 경로 하나로 닫혀 있다.

> **blast radius(영향 반경)** — 어떤 변경이나 결함이 잘못됐을 때 피해가 번질 수 있는 최대 범위.\
> 예: 여기서는 `SimpleJdbcInsert`로 INSERT를 실행하는 코드만 영향을 받고, `JdbcTemplate`으로 직접 SQL을 쓰는 코드는 무관하다.

그리고 이 무대의 핵심 데이터 흐름은 `tableColumns` 리스트 하나로 요약된다.\
아래처럼 하나가 만들어지고 셋이 소비한다.

```text
                    reconcileColumnsToUse(declaredColumns, generatedKeyNames)   :204
                                        │
                                        ▼
                          tableColumns : List<String>   :77
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
            createInsertString    createInsertTypes    matchInParameterValues...
                  :291                 :357                  :228 / :267
             물음표 개수 결정        int[] 길이 결정        값 List 길이 결정
             (자체 key 필터 有)      (필터 없음)            (필터 없음)
                    │                    │                     │
                    └────────────────────┴─────────────────────┘
                                         ▼
                    jdbcTemplate.update(sql, values.toArray(), types)
                                AbstractJdbcInsert.java:383
                    → 셋의 개수가 서로 맞아야 한다는 것이 암묵 불변식
```

세 소비자 중 `createInsertString`만 자기 자리에서 generated key를 한 번 더 걸러낸다(`TableMetaDataContext.java:321-329`).\
이 비대칭이 결함의 형태를 결정했다.

## 2. 수정 전 동작 워크플로우

컬럼 확정은 실행 때마다가 아니라 **compile 시점에 딱 한 번** 일어난다.\
`compile()`은 `synchronized`이고 `compiled` 플래그로 재진입을 막으므로(`AbstractJdbcInsert.java:271-292`), 한 번 정해진 `tableColumns`·`insertString`·`insertTypes`가 이후 모든 실행에 재사용된다.\
시나리오 두 개로 따라간다.

> **compile(컴파일)** — 설정을 읽어 SQL 문자열·타입 배열·컬럼 목록을 한 번 계산해 두고 이후 실행에서 그대로 재사용하는 단계.\
> 예: `insert.execute(...)`를 백 번 불러도 SQL 조립은 첫 호출 때 한 번만 일어난다.

먼저 두 시나리오가 어디서 갈라지고 어디서 다시 합쳐지는지를 세로로 놓으면 이렇다.\
갈림은 한 곳뿐이고, 그 아래는 두 경로가 같은 코드를 탄다.

```text
 사용자 설정
   withTableName("customers")
   usingGeneratedKeyColumns("id")
   (+ usingColumns 를 쓸 수도, 안 쓸 수도 있다)
         |
         v
 첫 execute(...) 한 번만  ->  checkCompiled() -> compile() -> compileInternal()
         |
         v
 processMetaData(ds, declaredColumns, generatedKeyNames)
         |
         v
 reconcileColumnsToUse(declaredColumns=?, generatedKeyNames=["id"])   <-- 유일한 갈림길
         |
         +--- declaredColumns 가 비었나? --- 예 ---> 메타데이터 경로 (시나리오 A)
         |                                            드라이버가 준 [id, name] 에서
         |                                            키 [id] 를 빼고  -> ["name"]
         |
         +--------------------------------- 아니오 -> 선언 경로 (시나리오 B, 수정 전)
                                                      declaredColumns 를 그대로 복사
                                                      -> ["id", "name"]   (키가 남는다)
         |
         v
 tableColumns  (여기서 두 경로가 다시 합쳐진다 — 이후 코드는 완전히 같다)
         |
         +--> createInsertString()  : 키를 한 번 더 걸러 물음표 개수를 센다
         +--> createInsertTypes()   : 거르지 않고 개수를 센다
         +--> matchInParameterValues: 거르지 않고 값을 채운다
         |
         v
 jdbcTemplate.update(sql, values, types)  -> JDBC 드라이버
```

갈림길 위쪽은 두 시나리오가 같고, 아래쪽도 같다.\
다른 것은 `reconcileColumnsToUse`가 어느 가지를 타느냐 한 번뿐이며, 그 한 번이 `tableColumns`의 내용을 바꾼다.

### 시나리오 A — 메타데이터 자동탐색 경로 (`usingColumns` 미사용)

사용자가 컬럼을 선언하지 않으면 파이프라인이 드라이버까지 내려가 테이블 컬럼을 읽어 온다.

> **`TableParameterMetaData`** — 드라이버가 알려 준 컬럼 하나의 정보(이름·SQL 타입·널 허용 여부)를 담은 값 객체.\
> 예: `customers` 테이블을 읽으면 `(id, INTEGER, not null)`과 `(name, VARCHAR, nullable)` 두 개가 만들어진다.

```text
insert.execute(Map.of("name","Sven"))         SimpleJdbcInsertOperations.java:115
  └→ doExecute(Map)                            AbstractJdbcInsert.java:359
       ├─ checkCompiled()                      :331
       │    └(최초 1회)→ compile()             :271
       │         ├─ tableName == null 이면 예외                       :273-275
       │         ├─ quoteIdentifiers && declaredColumns.isEmpty() 이면 예외 :276-279
       │         └─ compileInternal()                                  :299
       │              ├─ tableMetaDataContext.processMetaData(ds, getColumnNames(), getGeneratedKeyNames())  :302
       │              │    ├─ metaDataProvider = TableMetaDataProviderFactory.createMetaDataProvider(...)
       │              │    │       TableMetaDataProviderFactory.java:50
       │              │    │    ├─ JdbcUtils.extractDatabaseMetaData 로 Connection 확보           :52
       │              │    │    ├─ databaseProductName 분기 → Oracle/Postgres/Derby/HSQL/MySQL/Generic :56-74
       │              │    │    ├─ provider.initializeWithMetaData(dbmd)                         :79
       │              │    │    │     supportsGetGeneratedKeys · storesUpper/LowerCaseIdentifiers
       │              │    │    │     · getIdentifierQuoteString 를 읽어 필드에 캐시
       │              │    │    │                       GenericTableMetaDataProvider.java:88-134
       │              │    │    └─ accessTableColumnMetaData 이면
       │              │    │         provider.initializeWithTableColumnMetaData(dbmd, cat, schema, table)  :81-84
       │              │    │           └→ locateTableAndProcessMetaData(...)  GenericTableMetaDataProvider.java:273
       │              │    │                ├─ dbmd.getTables(cat, schema, table, null)          :279
       │              │    │                ├─ findTableMetaData(...) 로 스키마 후보 좁힘          :311
       │              │    │                └─ processTableColumns(...)                          :347
       │              │    │                     ├─ dbmd.getColumns(cat, schema, table, null)    :357
       │              │    │                     ├─ COLUMN_NAME / DATA_TYPE / NULLABLE 읽어      :360-375
       │              │    │                     │    TableParameterMetaData 로 적재             :376-377
       │              │    │                     └─ SQLException 이면 목록을 통째로 clear         :391
       │              │    └─ tableColumns = reconcileColumnsToUse(declaredColumns, generatedKeyNames)  :191
       │              │         declaredColumns 가 비었으므로 메타데이터 경로:
       │              │           keys = {generatedKeyNames 를 대문자화한 집합}                   :211-214
       │              │           메타데이터 컬럼 중 keys 에 없는 것만 수집                        :215-221
       │              │           → tableColumns = ["name"]        (id 는 제외됨)
       │              ├─ insertString = createInsertString(getGeneratedKeyNames())                :303
       │              │     → "INSERT INTO customers (name) VALUES(?)"
       │              └─ insertTypes = createInsertTypes()                                        :304
       │                    → [Types.VARCHAR]
       ├─ values = matchInParameterValuesWithInsertColumns(args)   :361  → ["Sven"]
       └─ executeInsertInternal(values)                            :379
            └→ jdbcTemplate.update(insertString, values.toArray(), insertTypes)   :383
                 물음표 1 · 값 1 · 타입 1  → 정합
```

이 경로에서 `createInsertString`의 자체 key 필터는 **아무것도 걸러내지 않는 무해한 중복**이다.\
`tableColumns`가 이미 걸러진 상태로 들어오기 때문이다.\
그래서 "tableColumns는 generated key가 이미 빠진 목록"이라는 불변식이 성립하고, 세 산출물의 개수가 자동으로 맞는다.

> **불변식(invariant)** — 코드가 어느 경로로 흐르든 항상 참이어야 하는 규칙.\
> 예: 여기서는 "물음표 개수 = 값 개수 = 타입 개수"가 지켜져야 INSERT가 성립한다.

### 시나리오 B — 선언 경로에서 키 컬럼이 겹칠 때 (수정 전)

같은 파이프라인이지만 `reconcileColumnsToUse`가 위쪽 분기에서 조기 반환한다는 점만 다르다.\
그 한 줄이 불변식을 깬다.

> **조기 반환(early return)** — 메서드 중간에서 조건이 맞으면 나머지 코드를 실행하지 않고 바로 값을 돌려주는 것.\
> 예: 여기서는 `return new ArrayList<>(declaredColumns)` 한 줄이 그 아래 키 제외 루프를 통째로 건너뛰게 만든다.

```text
 .usingColumns("id","name").usingGeneratedKeyColumns("id")

 reconcileColumnsToUse(["id","name"], ["id"])            TableMetaDataContext.java:204
   ├─ generatedKeyNames.length > 0 → generatedKeyColumnsUsed = true        :205-207
   └─ !declaredColumns.isEmpty() → return new ArrayList<>(declaredColumns) :208-210
          ★ 아래의 키 제외 로직(:211-221)을 통째로 건너뛴다
      tableColumns = ["id", "name"]        ← key 가 남아 있음 (불변식 위반)

 세 소비자가 같은 리스트를 서로 다르게 읽는다
   createInsertString(["id"])                                   :291
     keys = {"ID"}                                              :292-295
     for (columnName : tableColumns)                            :321
       "id"  → keys.contains("ID") → 건너뜀                      :322
       "name"→ columnCount = 1, 컬럼 목록에 추가
     params = "?" 1개                                            :347
     → "INSERT INTO customers (name) VALUES(?)"          물음표 1

   createInsertTypes()                                          :357
     int[] types = new int[tableColumns.size()]  → 길이 2        :358
     "id" → Types.INTEGER, "name" → Types.VARCHAR               :365-379
     → [INTEGER, VARCHAR]                                타입 2

   matchInParameterValuesWithInsertColumns(source)              :228
     for (column : tableColumns) → "id" 값, "name" 값            :234-259
     → [1, "Sven"]                                       값 2

 executeInsertInternal([1,"Sven"])                 AbstractJdbcInsert.java:379
   └→ jdbcTemplate.update(sql, [1,"Sven"], [INTEGER,VARCHAR])   :383
        └→ new ArgumentTypePreparedStatementSetter(args, argTypes)
             ArgumentTypePreparedStatementSetter.java:48
             args.length(2) == argTypes.length(2) → 검증 통과 ★ 스프링은 못 막는다  :49-51
           setValues(ps)                                        :58
             i=0 → doSetValue(ps, 1, INTEGER, 1)      ← SQL 의 1번 물음표는 name 자리
             i=1 → doSetValue(ps, 2, VARCHAR, "Sven") ← 물음표가 없는 위치 2
                     └→ 드라이버가 파라미터 인덱스 범위 오류를 던진다
                        (느슨한 드라이버라면 예외 없이 엉뚱한 컬럼에 값이 들어간다)
```

실패가 스프링 코드가 아니라 JDBC 드라이버에서 일어난다는 점이 이 결함의 성질을 결정한다.\
값 배열과 타입 배열은 둘 다 길이 2라 `ArgumentTypePreparedStatementSetter`의 생성자 검증을 그대로 통과하고, 어긋나는 것은 **SQL 문자열의 물음표 개수**뿐이기 때문이다.\
셋 중 둘이 같고 하나만 다르면 어떤 검증도 그 하나를 지목하지 못한다.

> **바인딩 파라미터(bind parameter)** — SQL 문장에 값을 직접 문자열로 끼워 넣지 않고 물음표 자리를 뚫어 두었다가 위치 번호로 값을 채우는 방식.\
> 예: `VALUES(?)`의 1번 자리에 `"Sven"`을 넣으면 `name` 컬럼에 그 값이 들어간다.

### 참고 — generated key를 되돌려 받는 경로

`executeAndReturnKey` 계열은 위와 같은 `insertString`·`insertTypes`를 쓰되, 문장 준비 방식만 다르다.\
키가 왜 INSERT 컬럼 목록에서 빠져야 하는지를 이 경로가 보여 준다.

```text
 doExecuteAndReturnKey(args)                       AbstractJdbcInsert.java:392
   └→ executeInsertAndReturnKeyInternal(values)                       :437
        └→ executeInsertAndReturnKeyHolderInternal(values)            :451
             ├─ isGetGeneratedKeysSupported() ?           TableMetaDataContext.java:388
             │    ├─ 예 ──→ prepareStatementForGeneratedKeys(con)     :540
             │    │           ├─ 컬럼명 배열 지원 → con.prepareStatement(sql, generatedKeyNames)  :550
             │    │           └─ 아니면 con.prepareStatement(sql, RETURN_GENERATED_KEYS)          :556
             │    │         setParameterValues(ps, values, getInsertTypes())                       :461
             │    └─ 아니오 ──→ isGetGeneratedKeysSimulated() 검사 :468
             │                   키 이름 0개 / 2개 이상이면 예외      :472-480
             │                   getSimpleQueryForGetGeneratedKey(...)  TableMetaDataContext.java:407
             │                   ├─ "RETURNING ..." 이면 INSERT 뒤에 붙여 queryForObject  :491-497
             │                   └─ 아니면 같은 Connection 에서 INSERT 후 별도 조회       :499-529
             └─ KeyHolder 반환
```

DB가 값을 채워 넣으려면 INSERT가 그 컬럼을 언급하지 않아야 한다.\
`usingGeneratedKeyColumns("id")`는 "id는 내가 안 보낼 테니 너희가 채우고 그 값을 알려 달라"는 선언이므로, `id`가 컬럼 목록에 남아 있는 상태 자체가 모순이다.

## 3. 분기 처리 워크플로우

이 파이프라인의 조건 분기는 네 층이다.\
컴파일 진입 조건, 제공자 선택, 컬럼 확정, 그리고 SQL 조립이다.\
버그는 셋째 층에 있다.

### 3-1. compile 진입 분기

첫 실행에서만 컴파일이 돌고, 그 진입에 세 가지 사전 검증이 걸려 있다.

```text
doExecute*(...)                                   AbstractJdbcInsert.java:359 / :370 / :392
  └─ checkCompiled()                              :331
       ├─ compiled == true  ──→ 아무것도 하지 않음 (산출물 재사용)
       └─ compiled == false ──→ compile()          :271  (synchronized)
            ├─ getTableName() == null ──→ InvalidDataAccessApiUsageException("Table name is required")  :273-275
            ├─ isQuoteIdentifiers() && declaredColumns.isEmpty()                                        :276-279
            │     ──→ InvalidDataAccessApiUsageException("Explicit column names must be provided ...")
            │         ★ 따옴표 식별자를 쓰면 usingColumns 가 강제된다 = 선언 경로가 필수인 사용자층
            ├─ jdbcTemplate.afterPropertiesSet() 실패 ──→ 같은 예외로 변환                              :280-285
            └─ compileInternal() → compiled = true                                                      :286-287
```

이 분기가 결함의 노출 빈도에 직접 관여한다.\
`usingQuotedIdentifiers()`나 `withoutTableColumnMetaDataAccess()`를 쓰는 사용자는 컬럼을 직접 나열할 수밖에 없고, 테이블 컬럼을 그대로 적다 보면 PK가 목록에 들어간다.

> **따옴표 식별자(quoted identifiers)** — 컬럼·테이블 이름을 DB의 인용 부호로 감싸 대소문자나 예약어를 그대로 쓰게 하는 옵션.\
> 예: `usingQuotedIdentifiers()`를 켜면 `"Name"`처럼 대소문자가 보존되지만, 대신 컬럼을 직접 나열해야 한다.

### 3-2. 제공자 선택·초기화 분기

제공자는 DB 제품명으로 고르고, 초기화의 각 항목은 실패해도 기본값으로 계속 간다.

```text
createMetaDataProvider(dataSource, context)       TableMetaDataProviderFactory.java:50
  ├─ databaseProductName 스위치                                        :56-74
  │    "Oracle"        → OracleTableMetaDataProvider(dbmd, overrideIncludeSynonymsDefault)
  │    "PostgreSQL"    → PostgresTableMetaDataProvider(dbmd)
  │    "Apache Derby"  → DerbyTableMetaDataProvider(dbmd)
  │    "HSQL Database Engine" → HsqlTableMetaDataProvider(dbmd)
  │    "MySQL"|"MariaDB"      → MySQLTableMetaDataProvider(dbmd)
  │    그 외           → GenericTableMetaDataProvider(dbmd)
  ├─ initializeWithMetaData(dbmd)                                      :79
  │    각 항목이 try/catch 로 감싸여 있어 실패해도 기본값으로 계속 간다
  │      supportsGetGeneratedKeys 실패 → 기본 true 유지    GenericTableMetaDataProvider.java:89-97
  │      storesUpperCaseIdentifiers 실패 → 기본 true 유지                                 :108-115
  │      storesLowerCaseIdentifiers 실패 → 기본 false 유지                                :117-124
  └─ context.isAccessTableColumnMetaData() ?                           :81
       ├─ 예   ──→ initializeWithTableColumnMetaData(...)              :82-84
       │             locateTableAndProcessMetaData                     GenericTableMetaDataProvider.java:273
       │               ├─ getTables 결과가 비면 info 로그만 남기고 컬럼 목록은 빈 채로 둔다  :301-305
       │               └─ 아니면 findTableMetaData → processTableColumns                     :307
       │                    ├─ schemaName != null 이면 그 스키마에서 못 찾을 때 예외          :314-320
       │                    ├─ 후보가 하나면 그것                                             :322-323
       │                    └─ 아니면 defaultSchema → userName → "PUBLIC" → "DBO" 순 폴백     :326-339
       │                    processTableColumns 내부:
       │                      DECIMAL 이면서 typeName=="NUMBER" && decimalDigits==0 → NUMERIC 으로 교정  :362-374
       │                      SQLException → 부분 목록을 남기지 않으려고 clear()                        :391
       └─ 아니오 ──→ 컬럼 메타데이터를 아예 읽지 않음 (withoutTableColumnMetaDataAccess)
                     → tableParameterMetaData 가 빈 목록 → 선언 컬럼이 없으면 SQL 을 만들 수 없다
```

### 3-3. 컬럼 확정 분기 — 버그가 살던 자리

이 메서드는 선언 경로와 메타데이터 경로 둘로 갈리는데, 키 제외 로직이 후자에만 있었다.

```text
reconcileColumnsToUse(declaredColumns, generatedKeyNames)   TableMetaDataContext.java:204
  │
  ├─ generatedKeyNames.length > 0 ?                                   :205
  │     └─ 예 ──→ this.generatedKeyColumnsUsed = true                 :206
  │               (뒤에서 "빈 INSERT" 를 허용할지 판정하는 데 쓰인다)
  │
  ├─ !declaredColumns.isEmpty() ?                                     :208   ← 선언 경로
  │     ├─ 예 ──→ return new ArrayList<>(declaredColumns)             :209   ★ 결함
  │     │          필터 없음. generated key 가 그대로 남는다.
  │     │          아래 :211-221 의 키 제외 로직을 건너뛴다.
  │     └─ 아니오 ──→ 계속
  │
  └─ 메타데이터 경로                                                    :211-221
       keys = generatedKeyNames 를 toUpperCase(Locale.ROOT) 한 LinkedHashSet   :211-214
       for (meta : provider.getTableParameterMetaData())                        :216
         !keys.contains(meta.getParameterName().toUpperCase(ROOT)) 이면 수집     :217-219
       return columns          ← generated key 가 제외된 목록 (불변식 준수)

  PR 적용 후의 형태 (키 집합 계산을 분기 위로 끌어올리고 선언 경로에도 같은 필터 적용)
       keys 계산                                     ← 분기 밖으로 이동
       ├─ 선언 경로 ──→ declaredColumns 중 keys 에 없는 것만 수집해 반환
       └─ 메타데이터 경로 ──→ 기존과 동일
       generatedKeyNames 가 비면 keys 도 비므로 기존 선언 경로 사용자는 결과 불변
```

### 3-4. SQL 조립 분기

`createInsertString`은 키 필터 외에도 조건이 몇 개 더 있다.\
특히 컬럼이 하나도 남지 않았을 때의 처리가 "빈 INSERT"를 정상으로 볼지 오류로 볼지를 가른다.

```text
createInsertString(generatedKeyNames)              TableMetaDataContext.java:291
  ├─ keys = 대문자 정규화 집합                                        :292-295
  ├─ isQuoteIdentifiers() ?                                           :297-299
  │     ├─ 예 ──→ provider.getIdentifierQuoteString() 으로 QuoteHandler 구성
  │     └─ 아니오 ──→ 인용 없이 그대로 이어 붙임          QuoteHandler:420-439
  ├─ catalogName != null 이면 "catalog." 접두                          :304-308
  ├─ schemaName  != null 이면 "schema."  접두                          :310-314
  ├─ for (columnName : getTableColumns())                              :321
  │     keys.contains(columnName.toUpperCase(ROOT)) ?                  :322
  │       ├─ 예 ──→ 건너뜀 (SQL 에 넣지 않음)   ← 자체 키 필터 = 중복 규칙
  │       └─ 아니오 ──→ columnCount++ 후 컬럼명 append                 :323-327
  ├─ columnCount < 1 ?                                                 :331
  │     ├─ generatedKeyColumnsUsed == true ──→ debug 로그만 남기고 빈 INSERT 허용   :332-337
  │     │     "INSERT INTO customers () VALUES()"
  │     └─ 아니면 ──→ InvalidDataAccessApiUsageException                            :338-345
  │           "Unable to locate columns for table ... so an insert statement can't be generated."
  │           (isAccessTableColumnMetaData 이면 usingColumns 안내 문구를 덧붙임)
  └─ params = "?" 를 columnCount 개 join                                :347-349
        ★ 물음표 개수의 유일한 출처. 아래 두 소비자와 다른 기준을 쓴다.

createInsertTypes()                                                    :357
  ├─ types = new int[getTableColumns().size()]        ← 필터 없음      :358
  ├─ 메타데이터를 대문자 키 맵으로 인덱싱                                :359-363
  └─ for (column : getTableColumns())                                   :365
       ├─ column == null ──→ SqlTypeValue.TYPE_UNKNOWN                  :366-368
       ├─ 메타데이터에 있음 ──→ tpmd.getSqlType()                        :370-373
       └─ 없음 ──→ SqlTypeValue.TYPE_UNKNOWN                            :374-376

matchInParameterValuesWithInsertColumns(SqlParameterSource)             :228
  └─ for (column : tableColumns)   ← 필터 없음                          :234
       ├─ parameterSource.hasValue(column)          ──→ 그 값            :235-237
       ├─ hasValue(column.toLowerCase(ROOT))        ──→ 그 값            :239-242
       ├─ hasValue(underscore→property 변환 이름)    ──→ 그 값            :244-247
       ├─ 대소문자 무시 이름 맵에 있음               ──→ 그 값            :249-252
       └─ 아무것도 없음                              ──→ null 추가       :254
```

세 소비자의 순회 기준을 나란히 놓으면 어긋남의 위치가 분명해진다.

```text
                      순회 대상                 필터              수정 전 개수(시나리오 B)
 insertString  :321   getTableColumns()        keys 제외 有       1
 insertTypes   :365   getTableColumns()        없음               2
 values        :234   this.tableColumns        없음               2
                                                                 ↑ 이 불일치가 드라이버까지 간다
```

같은 입력이 수정 전과 수정 후에 어떤 최종 상태로 끝나는지를 같은 칸 폭으로 놓으면 이렇다.\
입력은 둘 다 `.usingColumns("id","name").usingGeneratedKeyColumns("id")`이고, 값은 `id=1`·`name="Sven"`이다.

```text
 수정 전 (선언 경로 무필터)          수정 후 (선언 경로에도 같은 필터)
 +----------------------------+     +----------------------------+
 | tableColumns  ["id","name"]|     | tableColumns  ["name"]     |
 | 물음표          1 개        |     | 물음표          1 개        |
 | 타입 배열       2 개        |     | 타입 배열       1 개        |
 | 값 목록         2 개        |     | 값 목록         1 개        |
 +----------------------------+     +----------------------------+
   -> 1 대 2 대 2 로 갈린다            -> 1 대 1 대 1 로 맞는다
   -> 드라이버가 인덱스 오류            -> INSERT INTO customers
      (느슨한 드라이버는 값이 밀린다)       (name) VALUES(?) 가 정상 실행
```

수정은 왼쪽 칸의 첫 줄 하나만 바꾼다.\
`tableColumns`에서 키가 빠지면 아래 세 줄은 그 결과로 따라온다.

## 4. 스프링 전역에서의 자리

이 코드는 스프링 JDBC의 "SQL을 쓰지 않는 INSERT" 기능 전체를 떠받친다.\
진입점은 `SimpleJdbcInsert`의 실행 메서드 여섯 개이고, 그 아래로는 위에서 본 파이프라인 하나로 수렴한다.\
grep으로 확인한 실제 소유·호출 관계는 다음과 같다.

```text
[ 사용자 진입점 — spring-jdbc/core/simple ]
  SimpleJdbcInsertOperations                        SimpleJdbcInsertOperations.java:34
    execute(Map) :115 · execute(SqlParameterSource) :122
    executeAndReturnKey(Map) :132 · executeAndReturnKey(SqlParameterSource) :142
    executeAndReturnKeyHolder(Map) :152 · executeAndReturnKeyHolder(SqlParameterSource) :162
      └ 구현: SimpleJdbcInsert                       SimpleJdbcInsert.java:53
          └→ AbstractJdbcInsert.doExecute* → checkCompiled → compileInternal
                                             AbstractJdbcInsert.java:359 / :331 / :299

[ TableMetaDataContext 의 실제 보유·호출처 (grep 결과 전부) ]
  AbstractJdbcInsert.java:73    private final TableMetaDataContext tableMetaDataContext = new TableMetaDataContext();
    :302  processMetaData(dataSource, getColumnNames(), getGeneratedKeyNames())
    :303  createInsertString(getGeneratedKeyNames())
    :304  createInsertTypes()
    :457  isGetGeneratedKeysSupported()
    :468  isGetGeneratedKeysSimulated()
    :483  getSimpleQueryForGetGeneratedKey(tableName, generatedKeyNames[0])
    :546  isGeneratedKeysColumnNameArraySupported()
  TableMetaDataProviderFactory.java:50  createMetaDataProvider(DataSource, TableMetaDataContext)  ← 파라미터로만 사용
    → 이 두 곳 외에 저장소 안에 TableMetaDataContext 사용처는 없다

[ 드라이버 경계 ]
  GenericTableMetaDataProvider.java:279   DatabaseMetaData.getTables(...)
  GenericTableMetaDataProvider.java:357   DatabaseMetaData.getColumns(...)
  GenericTableMetaDataProvider.java:90    DatabaseMetaData.supportsGetGeneratedKeys()
  GenericTableMetaDataProvider.java:109/118  storesUpperCaseIdentifiers / storesLowerCaseIdentifiers
  GenericTableMetaDataProvider.java:127   getIdentifierQuoteString()

[ 실행 경계 — spring-jdbc/core ]
  AbstractJdbcInsert.java:383  JdbcTemplate.update(sql, args, argTypes)
    └→ ArgumentTypePreparedStatementSetter                ArgumentTypePreparedStatementSetter.java:35
         생성자 검증: args.length == argTypes.length                       :48-51
         setValues: parameterPosition 을 1부터 증가시키며 doSetValue         :58-83
```

전역 자리라는 관점에서 두 가지를 짚어 둘 만하다.\
첫째, `SimpleJdbcInsert`는 `JdbcTemplate`·`JdbcClient` 같은 범용 API와 달리 **DB 메타데이터에 런타임 의존**하는 몇 안 되는 스프링 JDBC 기능이다(`StoredProcedure` 계열의 `CallMetaDataContext`가 대칭 짝이다).\
그래서 같은 코드가 드라이버마다 다르게 동작할 여지가 크고, 식별자 대소문자 정규화를 곳곳에서 `toUpperCase(Locale.ROOT)`로 처리하는 관용구가 반복된다.\
둘째, `reconcileColumnsToUse`는 `protected` 확장점이므로 하위 클래스가 오버라이드했을 수 있다.\
저장소 안에는 오버라이드가 없지만, 외부 코드에는 있을 수 있다는 점이 PR 본문의 영향 절이 다루는 표면이다.

> **`protected` 확장점** — 하위 클래스가 상속해서 덮어쓸 수 있도록 열어 둔 메서드.\
> 예: 외부 프로젝트가 `reconcileColumnsToUse`를 이미 오버라이드했다면 이 PR의 수정이 그쪽에는 적용되지 않는다.

## 5. 관련 개념

### 5-1. generated key — DB가 채우는 컬럼

auto-increment PK나 시퀀스 기본값처럼 INSERT 시점에 DB가 값을 만들어 주는 컬럼을 말한다.\
애플리케이션이 값을 보내면 DB가 채울 자리가 없어지므로, generated key는 INSERT의 컬럼 목록에서 빠져야 한다.\
대신 JDBC는 `Statement.RETURN_GENERATED_KEYS` 또는 컬럼명 배열을 넘겨 만들어진 값을 되돌려 받는 표준 경로를 제공하고, 스프링은 그것을 `KeyHolder`로 감싼다(`AbstractJdbcInsert.java:540-558`).\
이 표준을 지원하지 않는 DB(HSQL, 구버전 PostgreSQL 등)를 위해 "INSERT 뒤에 RETURNING을 붙이거나, 같은 커넥션에서 별도 조회를 한 번 더 하는" 시뮬레이션 경로도 있다(`AbstractJdbcInsert.java:467-529`).

> **`KeyHolder`** — DB가 만들어 돌려준 키 값을 담아 오는 스프링의 그릇.\
> 예: `executeAndReturnKey(map)`이 내부적으로 `KeyHolder`에서 `id` 값을 꺼내 반환한다.

`usingGeneratedKeyColumns("id")`는 따라서 두 가지를 동시에 선언하는 셈이다.\
"id는 내가 안 보낸다"와 "id의 값을 돌려 달라".\
앞의 절반을 실제로 집행하는 코드가 `reconcileColumnsToUse`이고, 그것이 한쪽 분기에서만 집행됐다는 것이 이 PR의 전부다.

### 5-2. compile 모델 — 한 번 계산하고 재사용하는 객체

`SimpleJdbcInsert`는 스레드 안전한 재사용 객체다.\
설정을 마친 뒤 첫 실행에서 `compile()`이 한 번 돌아 `insertString`·`insertTypes`·`tableColumns`를 확정하고, 그 뒤로는 설정 변경이 금지된다(`checkIfConfigurationModificationIsAllowed`, `AbstractJdbcInsert.java:342-347`).\
이 모델의 장점은 메타데이터 조회 비용을 한 번만 치른다는 것이고, 단점은 **잘못 계산된 산출물도 그대로 굳는다**는 것이다.\
시나리오 B의 어긋남이 매 실행마다 재현되는 이유이며, 반대로 수정이 compile 시점 한 곳에서 끝나는 이유이기도 하다.

### 5-3. 식별자 대소문자 — 왜 어디서나 `toUpperCase(Locale.ROOT)`인가

JDBC 드라이버는 식별자를 저장할 때 대문자로 접기도(`storesUpperCaseIdentifiers`), 소문자로 접기도(`storesLowerCaseIdentifiers`) 한다.\
그래서 사용자가 `"id"`라고 쓴 이름과 `DatabaseMetaData.getColumns`가 돌려준 `"ID"`가 같은 컬럼일 수 있다.\
스프링은 이 문제를 두 층에서 다룬다.

> **식별자(identifier)** — SQL에서 테이블·컬럼 같은 대상을 가리키는 이름.\
> 예: `customers`와 `id`가 식별자이고, DB마다 이 이름을 대문자나 소문자로 접어 저장한다.

```text
 층 1: 드라이버에 질의를 보낼 때
   identifierNameToUse(name)                GenericTableMetaDataProvider.java:169
     ├─ storesUpperCaseIdentifiers → toUpperCase(Locale.ROOT)   :173-175
     ├─ storesLowerCaseIdentifiers → toLowerCase(Locale.ROOT)   :176-178
     └─ 그 외 → 그대로                                          :179-181

 층 2: 이름끼리 비교할 때
   전부 toUpperCase(Locale.ROOT) 로 정규화한 뒤 Set/Map 으로 비교
     reconcileColumnsToUse   TableMetaDataContext.java:213, :217
     createInsertString                              :294, :322
     createInsertTypes                               :362, :370
```

`Locale.ROOT`를 명시하는 이유는 터키어 로케일에서 `"id".toUpperCase()`가 점 있는 `İ`가 되는 것 같은 로케일 의존 함정을 피하기 위해서다.\
PR의 수정이 새 비교 규칙을 발명하지 않고 층 2의 기존 관용구를 그대로 재사용한 것, 그리고 테스트가 `"ID"` 선언 대 `"id"` 키 이름 조합을 따로 고정한 것이 모두 이 층 때문이다.

### 5-4. 값 파라미터 매칭의 폴백 사슬

`matchInParameterValuesWithInsertColumns`는 컬럼 이름으로 사용자 파라미터를 찾을 때 네 단계 폴백을 거친다(`TableMetaDataContext.java:234-259`).\
정확 일치 -> 소문자 일치 -> 언더스코어를 카멜케이스로 바꾼 프로퍼티 이름 -> 대소문자 무시 이름 맵 순이고, 넷 다 실패하면 `null`을 넣는다.\
마지막의 `null` 추가가 중요하다.\
**값을 못 찾아도 리스트 길이는 줄지 않는다.**\
즉 이 메서드가 만드는 값 목록의 길이는 언제나 `tableColumns.size()`와 같고, 그래서 `tableColumns`가 틀리면 값 목록도 정확히 그만큼 틀린다.

> **폴백(fallback)** — 첫 방법이 실패하면 다음 방법을 차례로 시도하는 대비책 사슬.\
> 예: 컬럼 `first_name`의 값을 찾을 때 `first_name` → `first_name`(소문자) → `firstName` → 대소문자 무시 순으로 찾아본다.

### 5-5. 참고 — 이미 있는 개념 문서

이 무대와 직접 겹치는 개념 문서는 아직 `../../concepts/`에 없다.\
JDBC 메타데이터 파이프라인은 이 문서 안에서 자기완결로 다뤘다.
