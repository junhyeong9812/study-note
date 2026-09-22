# PR #37235 - 테스트 해설 (테스트 하나하나)

> `SQLErrorCodeSQLExceptionTranslatorTests`에 추가된 1건 + 기존 테스트가 맡은 가드
> 역할. 각 테스트를 "무엇을 주장하나 / 왜 red 또는 가드인가 / 단언 하나하나의 의미"로
> 해설한다. red와 가드의 역할 분담 개념은
> [../37153/guard-tests.md](../37153-enum-array-annotation-probe/guard-tests.md), 형식 원본은
> [../37153/tests.md](../37153-enum-array-annotation-probe/tests.md).

배치 전체를 먼저 본다.\
이 결함은 **한 프로퍼티의 저장 순서**가 원인이므로, 새 테스트 하나가 "미정렬 입력"을 맡고 기존 테스트가 "정렬 입력"을 맡는 구도로 짝이 지어진다.\
그래야 fix가 "입력 순서를 무의미하게 만들었다"를 증명한다.

> **red 테스트** — 수정 전에는 반드시 실패하고 수정 후에 통과하는 테스트.\
> 예: 정렬 누락이 결함이라면, 미정렬 목록을 쓰는 테스트는 fix 전에 실패해야 그 결함을 실제로 겨냥한 것이다.

> **가드 테스트(guard test)** — 수정 전후 모두 통과해야 하는 테스트로, 기존 동작이 깨지지 않았음을 지킨다.\
> 예: 이미 정렬해 넣던 입력이 계속 같은 예외를 내는지 확인하는 테스트가 그 역할이다.

| 무대 | 입력이 사전식 미정렬 | 입력이 사전식 정렬 |
|---|---|---|
| `duplicateKeyCodes` 조회 | T1 `duplicateKeyCodesDeclaredInUnsortedOrder` - **red** | T2 `errorCodeTranslation`(기존) - 가드 |

같은 배치를 격자로 보면 두 테스트가 서로의 반대편을 덮고 있다는 것이 드러난다.

```text
                  |  fix 전       |  fix 후       |  덮는 것
------------------+---------------+---------------+---------------------------
T1 미정렬 입력    |  FAIL (red)   |  PASS         |  수정이 실제로 결함을 고쳤나
  "90002"         |  miss         |  hit          |  맨 앞인데 못 찾던 경우
  "1586"          |  hit (우연)   |  hit          |  우연 hit - 대비용
  "1062"          |  miss         |  hit          |  반대 방향 miss
------------------+---------------+---------------+---------------------------
T2 정렬 입력 "10" |  PASS         |  PASS         |  수정이 기존 동작을 깼나
T2 SQLState 폴백  |  PASS         |  PASS         |  폴백 사슬을 건드리지 않았나
```

-> 왼쪽 열에 하나라도 FAIL 이 없으면 결함을 못 겨냥한 것이고, 오른쪽 열에 FAIL 이 생기면 회귀다.

## T1. 미정렬 목록 재현 - red

새로 추가한 한 건은 사용자가 적은 순서 그대로의 미정렬 목록을 세우고 세 코드를 차례로 번역시킨다.

```java
@Test
void duplicateKeyCodesDeclaredInUnsortedOrder() {
	SQLErrorCodes errorCodes = new SQLErrorCodes();
	errorCodes.setDuplicateKeyCodes("90002", "1586", "1062");
	SQLErrorCodeSQLExceptionTranslator unsortedCodesTranslator = new SQLErrorCodeSQLExceptionTranslator(errorCodes);

	for (int errorCode : new int[] {90002, 1586, 1062}) {
		SQLException sqlException = new SQLException("", "", errorCode);
		assertThat(unsortedCodesTranslator.translate("task", "SQL", sqlException))
				.isInstanceOf(DuplicateKeyException.class)
				.hasCause(sqlException);
	}
}
```
(SQLErrorCodeSQLExceptionTranslatorTests.java:110-122)

- **주장**: 사용자가 적은 순서 그대로의 미정렬 목록에서도 세 코드 전부가 `DuplicateKeyException`으로 번역된다.
- **fix 전 red인 이유**: `setDuplicateKeyCodes`가 배열을 그대로 저장하므로 조회가 `Arrays.binarySearch(["90002","1586","1062"], "90002")`가 된다.\
  이진 탐색이 정렬 전제 위에서만 성립하기 때문에 빗나간다.\
  실측 실패 메시지는 `Expecting actual not to be null` - 8 tests 중 1 failed, 기존 7건은 green이었다.

**세 코드가 각각 다른 케이스를 대표한다.**\
목록을 굳이 셋으로 만든 것이 이 테스트의 설계다.

- `90002` - **배열 맨 앞에 있는데도 miss**.\
  3원소 배열에서 이진 탐색의 첫 `mid`는 index 1이고, `"1586" < "90002"`라 비교 결과가 "오른쪽으로 가라"를 가리킨다.\
  실제 값은 왼쪽 끝(index 0)에 있으므로 탐색은 그 자리를 **한 번도 보지 않고** index 2의 `"1062"`로 갔다가 끝난다(반환 -4).\
  "앞에 있으면 먼저 찾아진다"는 직관의 반례이고, red를 실제로 만드는 코드가 이것이다.
- `1586` - **미정렬에서도 우연히 hit**.\
  3원소 배열의 첫 `mid`가 index 1이고 그 자리에 이 값이 있으므로 첫 비교에서 즉시 맞는다.\
  fix 전에도 후에도 통과하는 코드이고, 그래서 "코드가 목록에 들어 있기만 하면 찾아지는 것이 아니라 **어디에 놓였느냐**가 결과를 가른다"를 대비로 보여 준다.
- `1062` - **반대 방향으로 miss**.\
  `mid`의 `"1586" > "1062"`라 왼쪽으로 가는데, index 0의 `"90002"`도 `"1062"`보다 커서 또 왼쪽으로 가다 범위가 소진된다(반환 -1).\
  90002가 "오른쪽으로 잘못 보내진" 경우라면 1062는 "왼쪽으로 잘못 보내진" 경우로, 둘이 짝을 이뤄 정렬 위반이 양방향으로 실패한다는 것을 고정한다.

세 코드가 같은 배열 위에서 서로 다른 방향으로 흩어지는 모습을 한 장으로 보면 이렇다.

```text
        저장 배열  index 0      index 1      index 2
                 ["90002"]    ["1586"]     ["1062"]
                                 ^
                                 |  첫 mid 는 언제나 여기

  "90002" 찾기 :            mid 보다 큼 -> 오른쪽 -> 오른쪽 -> 범위 소진  (miss, -4)
  "1586"  찾기 :            mid 가 곧 정답                               (hit)
  "1062"  찾기 :            mid 보다 작음 -> 왼쪽 -> 왼쪽 -> 범위 소진    (miss, -1)
```

-> 정답이 index 0 에 있어도 탐색이 그 칸을 한 번도 열어 보지 않는다.

**단언이 `translate(...)`의 반환값을 보는 이유.**\
이 결함은 예외를 던지지 않는다.\
`binarySearch`가 음수를 돌려주면 번역기는 나머지 그룹 배열을 계속 조회하다 `doTranslate`에서 null을 반환하고(SQLErrorCodeSQLExceptionTranslator.java:297), 그 null이 폴백 두 단을 거쳐 최종 null로 나온다.\
그래서 실패 모습이 "잘못된 예외 타입"이 아니라 "**actual not to be null**"이다.

> **단언(assertion)** — 테스트가 "이래야 한다"고 못 박는 검사 한 줄.\
> 예: `isInstanceOf(DuplicateKeyException.class)`는 번역 결과가 그 타입이어야 한다고 못 박는다.

- `new SQLException("", "", errorCode)`의 두 번째 인자가 SQLState다.\
  `""`로 준 것은 이 파일의 기존 관례이고(L71, L76, L103, L126 등 형제 테스트가 전부 같은 꼴), **에러코드 경로만 고립시키는** 효과가 있다.\
  SQLState가 두 글자도 안 되므로 `SQLStateSQLExceptionTranslator`의 가드 `sqlState.length() >= 2`(:128)에 막혀 클래스 코드 추출조차 못 한다.\
  그 덕에 폴백이 red를 덮어 주지 못한다.
- 폴백 1단 `SQLExceptionSubclassTranslator`도 무매치다.\
  테스트가 만든 것이 JDBC 4 서브클래스가 아닌 **순수** `SQLException`이라 `SQLTransientException` / `SQLNonTransientException` / `SQLRecoverableException` 세 분기 어디에도 걸리지 않는다(:75-123).\
  두 폴백이 "설치되지 않아서" null인 것이 아니라 **실행되고도 각자의 사유로** null이라는 점이 중요하다.
- 프로덕션에서는 이 null을 받은 `JdbcTemplate`이 `UncategorizedSQLException`으로 감싼다(JdbcTemplate.java:1550).\
  테스트는 translator를 직접 호출하므로 그 감싸기 단계가 없어 null이 그대로 드러난다.
- `.hasCause(sqlException)` - 번역된 예외가 원본 `SQLException`을 원인으로 물고 있는지.\
  `DuplicateKeyException`은 `buildMessage(...)`와 함께 `sqlEx`를 원인으로 받아 만들어진다(SQLErrorCodeSQLExceptionTranslator.java:252).\
  타입만 맞고 원인이 끊긴 번역을 걸러 내는 단언이다.
- 반복문으로 세 코드를 도는 형태라 **어느 코드에서 깨졌는지**가 실패 메시지만으로는 드러나지 않는다.\
  대신 세 코드가 한 배열을 공유해야 의미가 있는 테스트라(같은 저장 배열에서 결과가 갈리는 것이 주장이다) 파라미터화 대신 반복문을 골랐다.

> **파라미터화 테스트(parameterized test)** — 입력만 바꿔 같은 테스트를 여러 번 돌리고, 실패한 입력을 따로 보고해 주는 형식.\
> 예: 세 코드를 세 케이스로 나누면 어느 코드가 깨졌는지 이름으로 바로 보이지만, 세 코드가 한 배열을 공유한다는 사실은 흐려진다.

## T2. 기존 `errorCodeTranslation` - 가드 (전후 green)

새 테스트가 "미정렬 입력"을 맡는 동안, 정렬 입력에서 아무것도 안 바뀌었음을 고정하는 쪽은 기존 테스트다.\
별도로 추가한 것이 아니라 **이미 있던 테스트가 가드 역할을 하도록 배치를 짠 것**이다.

```java
private static final SQLErrorCodes ERROR_CODES = new SQLErrorCodes();
static {
	ERROR_CODES.setBadSqlGrammarCodes("1", "2");
	ERROR_CODES.setInvalidResultSetAccessCodes("3", "4");
	ERROR_CODES.setDuplicateKeyCodes("10");
	...
}
```
(SQLErrorCodeSQLExceptionTranslatorTests.java:53-63, 발췌)

- 정적 `ERROR_CODES`의 `duplicateKeyCodes`는 원소가 하나(`"10"`)라 정렬 여부를 물을 것도 없이 항상 정렬 상태다.\
  `errorCodeTranslation`(L68-100)이 `checkTranslation(10, DuplicateKeyException.class)`로 그 경로를 확인한다(L86).
- **fix 전후 모두 green**이고, 그것이 이 가드의 요점이다.\
  수정이 "이미 잘 되던 입력"의 결과를 바꾸지 않았음을 고정한다.\
  정렬이 필요 없던 입력에 정렬을 걸어도 결과가 같아야 한다는 것이 회귀 판정 기준이다.
- 같은 테스트가 SQLState 폴백 경로도 함께 지킨다(L96-99: 에러코드 `666666666` + SQLState `"07xxx"` -> `BadSqlGrammarException`).\
  fix가 코드 배열 조회만 건드리고 폴백 사슬은 손대지 않았음을 보증한다.

> **회귀(regression)** — 새 변경 때문에 원래 잘 되던 동작이 도로 망가지는 것.\
> 예: 정렬을 추가했더니 원소가 하나뿐인 목록에서 예외 타입이 달라진다면 그것이 회귀다.

## 실측 요약

실행 결과는 실패 건수뿐 아니라 실패한 코드까지 예측과 일치했다.

- **fix 전**: `SQLErrorCodeSQLExceptionTranslatorTests` **8 tests, 1 failed**.\
  T1이 `Expecting actual not to be null`로 실패했고 기존 7건은 green.\
  실패가 `90002`에서 났다는 것도 예측과 일치했다(1586은 우연 hit이라 그 반복 회차는 통과).
- **fix 후**: 같은 파일 **8/8 green**(red -> green), `org.springframework.jdbc.support` 패키지 green, `spring-jdbc` 전체 **961 tests, 0 failures**.\
  checkstyle EXIT=0.
- **diff 규모**: 2파일 +15/-1.\
  프로덕션 변경은 `SQLErrorCodes.java` 한 줄뿐이다.

> **checkstyle** — 코드 서식과 스타일 규칙을 자동으로 검사하는 도구.\
> 예: 들여쓰기나 임포트 순서가 프로젝트 규칙과 다르면 빌드를 실패시킨다. `EXIT=0`은 지적이 없었다는 뜻이다.

## 실측 probe - 커밋에 남기지 않은 확인

테스트로 커밋한 것 외에, 별도 프로브 클래스를 만들어 돌려 보고 결과만 취한 확인이 둘 있다.\
커밋에는 없지만 결함 판정과 수정 검증의 근거이므로 기록해 둔다(원본: 작업 로그와 세션 scratchpad `j6probe/Probe.java`).

> **프로브(probe)** — 커밋하지 않고 한 번 돌려 사실만 확인하고 버리는 임시 실행 코드.\
> 예: 미정렬 배열을 실제 번역기에 넣어 보고 어떤 예외가 나오는지 눈으로 확인하는 작은 `main` 하나.

**probe 1 - 결함 확정(착수 전).**\
미정렬 `["90002", "1586", "1062"]`를 실제 `SQLErrorCodes`에 넣고 `SQLErrorCodeSQLExceptionTranslator`로 번역해 봤다.\
코드 `90002`는 SQLState가 null이면 미번역(null), SQLState `23000`이면 `DataIntegrityViolationException`이었고, 같은 배열을 정렬해 저장하면 `DuplicateKeyException`이었다.\
같은 배열의 `1586`은 우연히 hit.\
이 실측이 "결함이 예외가 아니라 **예외 등급의 조용한 강등**으로 나타난다"와 "well-known 코드는 SQLState 폴백이 가려 준다"를 동시에 확인해 줬고, analysis.md의 결함 경로 표(4절)가 여기서 나왔다.

**probe 2 - fix 후 스모크(task 03).**\
수정된 jar로 같은 프로브를 다시 돌려 미정렬 3케이스가 전부 `DuplicateKeyException`이 되는 것을 확인했다.\
테스트 green과 별개로 **실제 실행 경로를 한 번 밟아 본다**는 최소 안전선 항목이다.

> **스모크(smoke test)** — 고친 경로를 실제로 한 번 돌려 "연기가 나는지" 보는 최소 확인.\
> 예: 테스트가 전부 초록이어도, 빌드된 jar로 같은 시나리오를 직접 실행해 보는 것이 스모크다.

두 프로브가 같은 입력을 fix 전후로 한 번씩 밟은 결과를 나란히 두면 이렇다.

```text
        probe 1 (fix 전)                    probe 2 (fix 후)
+------------------------------+    +------------------------------+
| 입력 ["90002","1586","1062"] |    | 입력 ["90002","1586","1062"] |
+------------------------------+    +------------------------------+
| 90002, SQLState null         |    | 90002  -> DuplicateKey       |
|   -> 미번역 (null)           |    | 1586   -> DuplicateKey       |
| 90002, SQLState "23000"      |    | 1062   -> DuplicateKey       |
|   -> DataIntegrityViolation  |    |                              |
| 1586   -> DuplicateKey (우연)|    |                              |
+------------------------------+    +------------------------------+
```

-> 같은 입력, 같은 실행 경로인데 저장 순서 한 가지만 달라져 결과가 하나로 모인다.

세 번째 프로브는 성격이 다르다.\
이해 게이트에서 나온 varargs 질문을 확인하려고 `javac`/`javap`로 바이트코드를 뽑고 호출자 배열의 변이를 실측한 것으로, 결과는 개념 문서 [Java varargs 실체](../../concepts/java-varargs-mechanics/java-varargs-mechanics.md)에 정리했다.\
요점만 옮기면, 이 테스트의 `setDuplicateKeyCodes("90002", "1586", "1062")` 호출은 컴파일 시점에 `new String[] {...}`로 바뀐다.\
그래서 `sortStringArray`가 제자리 정렬하는 배열은 **그 호출만을 위해 갓 만들어진 배열**이고, 테스트가 그 배열을 붙잡고 있지 않으므로 정렬을 관측하는 통로는 getter가 아니라 번역 결과다.

> **바이트코드(bytecode)** — 자바 소스가 컴파일돼 JVM이 실제로 실행하는 중간 명령어 형식.\
> 예: `javap -c`로 열어 보면 값 나열 호출이 `new String[]` 생성 명령으로 바뀌어 있는 것이 보인다.
