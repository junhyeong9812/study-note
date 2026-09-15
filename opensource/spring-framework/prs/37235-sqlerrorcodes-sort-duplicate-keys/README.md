# PR #37235 - Sort duplicate key codes in SQLErrorCodes

## 0. 정향

이 문서는 `spring-jdbc`의 `SQLErrorCodes.setDuplicateKeyCodes`가 **형제 setter 아홉 개와 달리 입력 배열을 정렬하지 않고 저장하던** 결함의 해설이다.\
결함 자체는 한 줄 누락이고 수정도 한 줄이지만, 그 한 줄이 만든 증상은 관측하기 까다로웠다.\
예외가 나지 않고, 같은 설정에서 코드에 따라 결과가 갈리고, 배포 기본값에서는 아예 나타나지 않는다.

> **setter(세터)** — 객체 바깥에서 넘긴 값을 필드에 저장하는 메서드.\
> 예: `setDuplicateKeyCodes("1062")`를 부르면 `duplicateKeyCodes` 필드에 그 값이 들어간다.

다 읽으면 다음 셋을 설명할 수 있어야 한다.

- "왜 정렬 누락이 조회 실패가 되는가"
- "왜 배열 맨 앞에 있는 값이 못 찾아지는가"
- "왜 이 결함이 십 년 넘게 안 보였는가"

상태: **리뷰 대기**(2026-09-04 제출, 커밋 `e0704925b9a`).

같은 폴더: [테스트 해설](tests.md) - [실구조](structure.md) - [착수 분석](analysis.md) -
[이해 게이트 기록](gates.md).
개념 문서: [Java varargs 실체](../../concepts/java-varargs-mechanics/java-varargs-mechanics.md).

## 1. 배경 - 저장은 열 곳, 조회는 한 종류

Spring은 JDBC 드라이버가 던진 벤더 고유 에러코드를 자기 예외 계층으로 번역한다.\
그 사상표가 `SQLErrorCodes`라는 JavaBean이고, 벤더별 인스턴스가 `sql-error-codes.xml`에 정의돼 있다.

> **벤더 고유 에러코드(vendor error code)** — DB 제품이 자기 방식으로 매긴 오류 번호.\
> 예: 같은 "중복 키" 오류를 MySQL은 `1062`, H2는 `23001`로 알린다.

> **JavaBean** — 기본 생성자와 getter/setter만으로 값을 채울 수 있게 만든 자바 클래스 관례.\
> 예: XML에 `<property name="duplicateKeyCodes">`라고 적으면 Spring이 `setDuplicateKeyCodes`를 대신 불러 준다.

```xml
<bean id="MySQL" class="org.springframework.jdbc.support.SQLErrorCodes">
	...
	<property name="duplicateKeyCodes">
		<value>1062</value>
	</property>
```
(sql-error-codes.xml:189, :199-201)

이 빈은 코드 목록 열 종을 `String[]` 필드로 들고 있다.\
`badSqlGrammarCodes`, `duplicateKeyCodes`, `dataIntegrityViolationCodes` 등이다(SQLErrorCodes.java:43-61).\
XML의 `<property>`는 빈 프로퍼티 주입이므로 반드시 setter를 통과하고, 그 setter들이 하나같이 같은 한 줄이다.

> **프로퍼티 주입(property injection)** — 컨테이너가 객체를 만든 뒤 setter를 불러 값을 채워 넣는 방식.\
> 예: XML의 `<value>1062</value>`는 필드에 직접 꽂히는 게 아니라 setter를 한 번 거쳐 들어간다.

```java
public void setBadSqlGrammarCodes(String... badSqlGrammarCodes) {
	this.badSqlGrammarCodes = StringUtils.sortStringArray(badSqlGrammarCodes);   // SQLErrorCodes.java:106
}
```

**정렬해서 저장하는 이 관례가 이 클래스의 계약**이다.\
소비자인 `SQLErrorCodeSQLExceptionTranslator`가 코드 목록을 전부 `Arrays.binarySearch`로 조회하기 때문이다.

```java
else if (Arrays.binarySearch(sqlErrorCodes.getDuplicateKeyCodes(), errorCode) >= 0) {
	logTranslation(task, sql, sqlEx, false);
	return new DuplicateKeyException(buildMessage(task, sql, sqlEx), sqlEx);
}
```
(SQLErrorCodeSQLExceptionTranslator.java:250-253)

이진 탐색은 정렬을 전제로만 성립한다.\
즉 저장측 열 개 setter와 조회측 `binarySearch` 사이에 **"배열은 사전식 정렬"이라는 암묵의 약속**이 있다.\
그 약속을 강제하는 장치는 setter가 스스로 부르는 `sortStringArray` 호출뿐이다.\
컴파일러도 타입도 이것을 검사하지 않는다.

> **이진 탐색(binary search)** — 정렬된 배열의 가운데를 보고 찾는 값이 왼쪽인지 오른쪽인지 판단해 절반씩 버리며 들어가는 조회.\
> 예: 사전에서 "ㅅ"으로 시작하는 단어를 찾을 때 책 중간을 펴 보고 앞뒤 절반 중 하나를 통째로 버리는 것과 같다.

> **불변식(invariant)** — 코드가 어떤 경로로 돌든 항상 참이어야 하는 문장.\
> 예: "코드 배열 필드는 언제나 사전식 정렬 상태다"가 이 클래스의 불변식이다.

계약이 맺어지는 자리를 한 장으로 세워 두면 이렇다.

```text
sql-error-codes.xml  <property name="duplicateKeyCodes">
        |
        v
  프로퍼티 주입 (Spring 컨테이너가 setter 호출)
        |
        v
  setXxxCodes(String... codes)        <- 저장측: 여기가 정렬을 책임진다
        |
        v
  String[] 필드 (열 종)               <- 약속: 사전식 정렬 상태
        |
        v
  getXxxCodes()
        |
        v
  Arrays.binarySearch(배열, "1062")   <- 조회측: 정렬을 전제로만 성립
```

여기에 함정이 하나 더 있다.\
조회 키는 정수가 아니라 문자열이다 - 번역기가 `Integer.toString(current.getErrorCode())`로 만든다(:223).\
그래서 정렬 기준도 사전식이고, **자릿수가 다른 코드가 섞이면 사람이 읽는 숫자 순서와 어긋난다.**\
Oracle의 `badSqlGrammarCodes`가 XML에 `900,...,17006,6550`으로 적혀 있어도 동작하는 이유는 setter가 그것을 사전식으로 다시 줄 세우기 때문이다.

> **사전식 정렬(lexicographic order)** — 숫자 크기가 아니라 글자를 앞에서부터 비교해 세우는 순서.\
> 예: 숫자로는 `900 < 6550`이지만 문자열로는 `"6550" < "900"`이다(첫 글자 `6` < `9`).

## 2. 수정 전 동작 - 열 개 중 하나만 관례 밖

수정 전 코드에서 `setDuplicateKeyCodes`만 그 관례에 없었다.

```java
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = duplicateKeyCodes;
}
```
(수정 전 SQLErrorCodes.java:125-127)

형제 아홉 개(L105/113/129/137/145/153/161/169/177)와 나란히 놓고 보면 `String...`을 받아 같은 이름의 필드에 대입하는 모양까지 똑같다.\
`StringUtils.sortStringArray(...)` 호출 하나만 빠져 있다.\
같은 파일 계열의 `CustomSQLErrorCodesTranslation.setErrorCodes`(L43-45)도 정렬하므로, 이 setter 하나가 열한 곳 중 유일한 예외였다.

> **varargs(가변 인자, `String...`)** — 인자를 몇 개 나열해 넘겨도 메서드 안에서는 배열 하나로 받는 문법.\
> 예: `setDuplicateKeyCodes("a", "b")`는 컴파일러가 `new String[]{"a","b"}`를 만들어 넘긴 것과 같다.

같은 XML 한 줄이 프로퍼티 이름에 따라 어디서 갈라지는지 세로로 따라가면 이렇다.

```text
        <property name="...Codes"><value>90002,1586,1062</value></property>
                          |
                          v
              Spring 컨테이너가 setter 호출
                          |
        +-----------------+------------------+
        |                                    |
        v                                    v
  형제 setter 아홉 개                   setDuplicateKeyCodes
  (badSqlGrammar, dataIntegrity, ...)   (수정 전)
        |                                    |
        v                                    v
  sortStringArray(codes)               (정렬 호출 없음)
        |                                    |
        v                                    v
  ["1062","1586","90002"]              ["90002","1586","1062"]
        |                                    |
        +-----------------+------------------+
                          |
                          v
              Arrays.binarySearch(배열, "90002")
                          |
        +-----------------+------------------+
        |                                    |
        v                                    v
      hit (index 2)                       miss (-4)
```

결과적으로 `duplicateKeyCodes` 배열만 사용자가 적은 순서 그대로 저장되고, 조회는 정렬을 전제한 `binarySearch`로 이루어진다.\
**저장 규칙과 조회 규칙이 이 한 프로퍼티에서만 어긋나 있었다.**

## 3. 문제 - 있는데 못 찾고, 예외는 나지 않는다

발동 조건은 하나다.\
**`duplicateKeyCodes`를 두 개 이상, 사전식 미정렬 순서로 준 경우**다.\
사용자 커스텀 `sql-error-codes.xml`이나 프로그래밍 주입이 그 경로다.\
커스텀 파일은 클래스패스 루트에 두면 기본값을 오버라이드한다(`SQLErrorCodesFactory.SQL_ERROR_CODE_OVERRIDE_PATH`:59).

> **클래스패스(classpath)** — JVM이 클래스와 리소스 파일을 찾아 뒤지는 경로 목록.\
> 예: `src/main/resources/sql-error-codes.xml`에 파일을 두면 클래스패스 루트에 놓인 것이 되어 Spring 기본 파일보다 먼저 읽힌다.

### 증상 1 - 배열 맨 앞의 값이 miss

`setDuplicateKeyCodes("90002", "1586", "1062")`로 저장하고 코드 `90002`를 조회하면 이렇게 흐른다.

```text
배열 ["90002", "1586", "1062"]        찾는 값 "90002"

low=0 high=2  mid=1  "1586" < "90002"  ->  오른쪽 절반으로   low=2
low=2 high=2  mid=2  "1062" < "90002"  ->  또 오른쪽으로     low=3
low=3 > high=2                          ->  miss (-4)
```

index 0에 답이 **버젓이 있는데도** 탐색은 그 자리를 한 번도 보지 않는다.\
이진 탐색은 배열을 앞에서부터 읽지 않고 가운데에서 시작해 절반씩 버리며 들어가기 때문이다.\
정렬 전제가 거짓이면 그 "버리는 판단"이 답이 있는 쪽을 버린다.

같은 배열에서 세 코드의 운명이 갈린다.

```text
배열 ["90002", "1586", "1062"]   (첫 mid 는 언제나 index 1 = "1586")

찾는 값 "90002"   mid "1586" 보다 큼 -> 오른쪽 -> "1062" 도 작음 -> 오른쪽 -> miss
찾는 값 "1586"    mid 가 곧 그 자리                                  -> hit
찾는 값 "1062"    mid "1586" 보다 작음 -> 왼쪽 -> "90002" 도 큼 -> 왼쪽 -> miss
```

`1062`는 반대 방향으로 빗나가고, `1586`은 3원소 배열의 첫 `mid`가 바로 그 자리라 **우연히 맞는다**.\
같은 설정, 같은 목록인데 코드에 따라 결과가 갈린다는 것이 이 결함의 성격이다.

### 증상 2 - 미스가 예외가 아니라 등급 강등으로 나온다

조회가 빗나가도 사용자에게 아무 신호가 가지 않는다.\
번역기는 나머지 그룹 배열을 계속 조회하다 `doTranslate`에서 null을 반환하고(:297), 그 null이 폴백 두 단을 지나 최종 결과를 정한다.

> **폴백(fallback)** — 앞 단계가 실패했을 때 대신 시도하는 뒷단 경로.\
> 예: 에러코드 조회가 빗나가면 번역기는 SQLState 값으로 다시 한 번 예외 종류를 정해 본다.

> **SQLState** — DB 제품과 무관하게 표준으로 정해진 다섯 글자 오류 분류 코드.\
> 예: `23000`은 "무결성 제약 위반"이라는 뜻이고, 벤더 코드 `1062`와 달리 제품이 달라도 같은 의미다.

| SQLState | 정렬 저장(형제와 동일) | 수정 전(미정렬) |
|---|---|---|
| null 또는 두 글자 미만 | DuplicateKeyException | UncategorizedSQLException (미번역) |
| `23000` | DuplicateKeyException | **DataIntegrityViolationException** |
| `HY000` 등 무관한 값 | DuplicateKeyException | UncategorizedSQLException |

같은 입력이 수정 전후로 어디까지 내려가는지 나란히 놓으면 이렇다.

```text
  정렬 저장 (형제와 동일)              수정 전 (미정렬)
+------------------------+          +------------------------+
| 코드 배열 조회 "90002" |          | 코드 배열 조회 "90002" |
|   -> hit               |          |   -> miss (-4)         |
+------------------------+          +------------------------+
          |                                     |
          v                                     v
+------------------------+          +------------------------+
| DuplicateKeyException  |          | doTranslate 가 null    |
+------------------------+          | -> SQLState 폴백       |
                                    | -> 23000 이면          |
                                    |    DataIntegrity...    |
                                    | -> 아니면              |
                                    |    UncategorizedSQL... |
                                    +------------------------+
```

-> 왼쪽은 원하던 예외를 받고, 오른쪽은 **예외는 받지만 덜 정밀한 예외**를 받는다.

즉 `catch (DuplicateKeyException e)`로 중복 삽입을 처리하려던 코드가 **조용히 안 잡는다**.\
예외는 여전히 날아오고 로그에도 특별한 것이 남지 않으므로, 원인을 setter 한 줄로 되짚기가 어렵다.

> **무음 실패(silent failure)** — 실패했는데도 에러·로그 같은 신호가 남지 않아 정상처럼 보이는 실패.\
> 예: 중복 키 예외가 다른 이름의 예외로 바뀌어 올라오면, 잡으려던 `catch` 블록만 조용히 건너뛴다.

### 왜 지금까지 안 보였나

세 겹의 우연이 이 결함을 덮고 있었다.

1. **배포 XML이 우연히 정렬 상태다.**\
   `duplicateKeyCodes` 프로퍼티는 벤더 빈 열한 개에 하나씩 있는데, 절반은 원소가 하나고 나머지도 전부 사전식 정렬이었다(`2601,2627` / `23001,23505` / `-239,-268,-6017`).\
   다른 프로퍼티라면 미정렬이어도 setter가 고쳐 줬을 텐데, 하필 보호가 없는 이 프로퍼티만 우연에 기대고 있었다.
2. **well-known 코드는 SQLState 폴백이 가려 준다.**\
   `SQLStateSQLExceptionTranslator.DUPLICATE_KEY_ERROR_CODES`(:96-104)가 1, 301, 1062, 2601, 2627, -239, -268 일곱 종을 갖고 있다.\
   그래서 SQLState가 `23000`이면 코드 배열 조회가 빗나가도 결국 `DuplicateKeyException`이 만들어진다.\
   **가장 흔한 코드일수록 결함이 안 보인다** - 그래서 증상은 well-known 목록 밖의 코드, 즉 애플리케이션이 정의한 코드 쪽에서 드러난다.
3. **결함이 예외를 만들지 않는다.**\
   증상 2에서 본 대로다.

세 겹이 어떻게 겹쳐 증상을 막고 있었는지 한 장으로 보면 이렇다.

```text
          미정렬 배열 저장 (결함)
                  |
                  v
      [1겹] 배포 XML 이 이미 정렬 상태인가?
                  |
       예 --------+-------- 아니오
       |                      |
       v                      v
   증상 없음          [2겹] well-known 코드인가?
                              |
                   예 --------+-------- 아니오
                   |                      |
                   v                      v
        SQLState 폴백이 덮음        [3겹] 예외가 나는가?
                                          |
                                          v
                                  아니오 - 등급만 강등
                                          |
                                          v
                                  사용자에게 보이는 것은
                                  "catch 가 안 걸린다" 뿐
```

## 4. 수정 해설 - 관례에 합류시키는 한 줄

수정은 동작을 더하지 않는다.\
**형제 아홉 개와 같은 줄을 쓰는 것**이 전부다.

```java
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = StringUtils.sortStringArray(duplicateKeyCodes);
}
```
(SQLErrorCodes.java:125-127)

```text
   수정 전 setter                        수정 후 setter
+----------------------------+      +----------------------------+
| this.duplicateKeyCodes     |      | this.duplicateKeyCodes     |
|     = duplicateKeyCodes;   |      |     = sortStringArray(     |
|                            |      |         duplicateKeyCodes);|
+----------------------------+      +----------------------------+
 입력 ("90002","1586","1062")        입력 ("90002","1586","1062")
            |                                    |
            v                                    v
 필드 ["90002","1586","1062"]        필드 ["1062","1586","90002"]
            |                                    |
            v                                    v
 binarySearch("90002") -> miss       binarySearch("90002") -> hit
```

-> 같은 입력인데 저장 순서 한 가지만 달라져 조회 결과가 뒤집힌다.

`StringUtils`는 이미 임포트돼 있고(L22) 새 의존도 새 분기도 없다.\
수정 후 이 파일의 코드 배열 setter 열 개는 글자 그대로 같은 모양이 된다.\
"코드 배열 setter는 입력 순서와 무관하게 사전식 정렬 배열을 저장한다"는 불변식이 열 개 전부에 성립한다.

호출하는 유틸리티의 몸체도 함께 봐 두는 편이 좋다.

```java
public static String[] sortStringArray(String[] array) {
	if (ObjectUtils.isEmpty(array)) {
		return array;
	}

	Arrays.sort(array);
	return array;
}
```
(spring-core StringUtils.java:1066-1073)

**복사본을 만들지 않는 제자리 정렬**이다.\
그래서 `setDuplicateKeyCodes(myArray)`처럼 배열 변수를 직접 넘기면 호출자의 `myArray`도 정렬된다.

> **제자리 정렬(in-place sort)** — 새 배열을 만들지 않고 받은 배열 자체의 원소 순서를 바꾸는 정렬.\
> 예: `Arrays.sort(myArray)`를 부르면 호출한 쪽이 들고 있던 `myArray`의 내용이 그 자리에서 바뀐다.

이 부수 효과는 형제 아홉 개가 이미 갖고 있던 동작이므로 이 PR이 들여온 것이 아니다.\
방어적 복사가 필요하다는 판단이 선다면 그것은 setter 하나가 아니라 열 곳 전체에 대한 별개의 API 변경 논의다.\
값을 나열해 부르는 흔한 형태(`setDuplicateKeyCodes("a", "b")`)에서는 컴파일러가 호출 지점에서 새 배열을 만들어 넘기므로 훼손될 호출자 배열 자체가 없다.\
자세한 것은 [Java varargs 실체](../../concepts/java-varargs-mechanics/java-varargs-mechanics.md).

> **방어적 복사(defensive copy)** — 받은 객체를 그대로 쓰지 않고 복사본을 만들어 저장해, 바깥의 변경이 안쪽에 새지 않게 하는 기법.\
> 예: `this.codes = codes.clone()`으로 저장하면 호출자가 나중에 원본 배열을 바꿔도 필드는 그대로다.

### 검토했으나 기각한 대안

소비자 쪽에서 `binarySearch` 대신 선형 탐색을 쓰면 정렬 전제 자체가 사라진다.\
기각한 이유는 둘이다.\
형제 아홉 종과 조회 규칙이 어긋나 한 배열만 다른 방식으로 조회하게 된다.\
그리고 조회는 예외 한 건마다 최대 열 번 일어나므로 성능이 후퇴한다.\
이 파일의 관례는 **저장측이 정렬을 책임진다**이고, 결함은 관례 위반이지 관례의 결함이 아니다.

> **선형 탐색(linear search)** — 배열을 앞에서부터 하나씩 훑어 값을 찾는 조회.\
> 예: 정렬돼 있지 않아도 항상 찾아내지만, 원소가 n개면 최대 n번 비교해야 한다.

### 호환성

배포 `sql-error-codes.xml`의 `duplicateKeyCodes` 열한 개 목록이 전부 이미 사전식 정렬이므로 기본 구성의 동작은 문자 그대로 불변이다.\
이미 정렬해 넣던 사용자도 불변이다.\
동작이 바뀌는 것은 미정렬로 넣던 사용자뿐이고, 그 변화가 곧 수정 목적이다.\
지금까지 조용히 강등되던 예외가 설정한 대로 `DuplicateKeyException`이 된다.

## 5. 검증

테스트를 먼저 쓰고 red를 확인한 뒤 fix했다.\
`SQLErrorCodeSQLExceptionTranslatorTests`에 미정렬 목록 재현 1건을 추가했고, 코드 세 개(`90002` / `1586` / `1062`)가 각각 "맨 앞인데 miss" / "우연 hit" / "반대 방향 miss"를 대표한다.

> **red(레드)** — 고치기 전에 새 테스트를 돌려 일부러 실패를 확인하는 단계.\
> 예: 여기서 실패하지 않으면 그 테스트는 결함을 잡아내는 테스트가 아니라는 뜻이다.

fix 전 실측은 **8 tests, 1 failed**였다.\
실패 메시지가 `Expecting actual not to be null`이었다는 점이 "이 결함은 예외 타입이 틀리는 것이 아니라 번역 자체가 안 되는 것"을 그대로 보여 준다.\
fix 후 같은 파일 8/8 green, `spring-jdbc` 전체 **961 tests, 0 failures**, checkstyle EXIT=0.\
상세는 [tests.md](tests.md).

기존 `errorCodeTranslation`(정렬 입력 `"10"`)이 무회귀 가드를 맡는다.\
커밋 외에 프로브를 두 번 돌렸다 - 착수 전에 결함을 확정하려고 한 번, fix 후 실제 실행 경로를 밟아 보려고 한 번.

> **무회귀 가드(regression guard)** — 이미 잘 돌던 동작이 이번 수정으로 깨지지 않았음을 지켜 주는 기존 테스트.\
> 예: 정렬된 입력 `"10"`을 쓰던 기존 테스트가 그대로 통과하면, 수정이 기존 사용자를 건드리지 않았다는 증거가 된다.

stakes는 **낮음**으로 판정했다(blast radius 한 줄, 불변식이 한 문장, 기본 구성 불변, 기존 테스트가 회귀를 막음).\
그래서 리뷰는 셀프체크 + diff self-review였고 듀얼 리뷰는 돌리지 않았다.\
이 폴더에 `review.md`가 없는 것은 누락이 아니라 그 판정의 결과다.

> **blast radius(폭발 반경)** — 이 변경이 잘못됐을 때 영향이 미치는 범위.\
> 예: 한 setter의 한 줄만 바뀌고 소비처가 한 곳뿐이면 반경이 작다.

셀프 리뷰에서 확인한 것은 셋이다.

- diff 2파일 +15/-1로 의도 외 변경 없음
- `getDuplicateKeyCodes()`의 소비처가 번역기 L250 하나뿐임
- null varargs 입력에서의 동작이 형제 아홉 개와 동일함(기존 동작)

## 6. 교훈

이 한 줄짜리 결함이 남긴 것은 암묵의 관례, 이진 탐색의 전제, 우연의 은폐, 폴백의 양면성 넷이다.

1. **관례로만 유지되는 불변식은 한 곳이 빠져도 아무도 못 본다.**\
   저장측 열 곳과 조회측 한 종류 사이의 약속은 코드 어디에도 적혀 있지 않았고 컴파일러도 검사하지 않는다.\
   실제 탐지 방법은 논리 추적이 아니라 **같은 모양의 setter를 나란히 놓고 한 줄이 없는 것을 세어 보는 것**이었다.
2. **이진 탐색은 "있으면 찾는다"가 아니라 "정렬돼 있으면 찾는다"다.**\
   정렬 전제가 깨지면 배열 맨 앞의 값도 못 찾는다.\
   컬렉션에 넣어 두었으니 조회되겠거니 하는 직관이 여기서 깨진다.
3. **우연히 맞는 값이 결함을 숨긴다.**\
   미정렬 배열에서도 가운데 원소는 항상 첫 비교에서 맞고, 배포 XML의 목록은 하필 전부 정렬 상태였으며, 가장 흔한 벤더 코드들은 SQLState 폴백이 덮어 줬다.\
   세 우연이 겹쳐 십 년 넘게 증상이 보고되지 않았다.
4. **폴백 사슬은 결함을 완화하는 동시에 은폐한다.**\
   조회가 빗나가도 사용자는 예외를 받으므로 "동작한다"고 느끼지만, 받는 것은 덜 정밀한 예외다.\
   실패가 조용할수록 반증 질문을 먼저 던져야 한다 - 이 경우에는 "미스 이후 결과가 어디서 정해지는가"가 그 질문이었다.
