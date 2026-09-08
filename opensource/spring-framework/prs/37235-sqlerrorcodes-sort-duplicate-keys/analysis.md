# PR #37235 - 착수 분석: setDuplicateKeyCodes의 정렬 누락

> 원본: `docs/plans/2026-08-29/j6-sqlerrorcodes-duplicate-key-sort/analysis.md`(착수 전
> 작성). 학습 문서로 옮기면서 작업 진행용 절을 덜어내고, 수정이 적용된 현재 시점에
> 맞춰 시제를 정리했으며 실측 근거를 절로 승격했다. 결론은 PR #37235로 반영됐다
> (커밋 `e0704925b9a`).
>
> **좌표 주의**: 본문의 `SQLErrorCodes.java L125-127`은 **수정 전** 파일(upstream main
> `5d6a56fe4a0`) 기준이다. 수정 후 좌표와 분기도는 [structure.md](structure.md)를
> 본다. 문제와 수정 요약은 [README.md](README.md), 테스트는 [tests.md](tests.md).

## 0. 결론 먼저

`SQLErrorCodes`의 코드 배열 setter 열 개 중 아홉 개는 `StringUtils.sortStringArray`로
정렬해 저장하는데 `setDuplicateKeyCodes`만 입력 배열을 그대로 저장했다(L125-127).
유일한 소비자 `SQLErrorCodeSQLExceptionTranslator.doTranslate`는 모든 코드 배열을
`Arrays.binarySearch`로 조회하므로(L250), 정렬되지 않은 배열은 **값의 배치에 따라
우연히 맞거나 조용히 빗나간다**.

```java
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = duplicateKeyCodes;        // 형제 아홉 개만 sortStringArray 를 거친다
}
```

빗나가면 `DuplicateKeyException` 대신 SQLState 폴백의 결과
(`DataIntegrityViolationException`)나 미번역(`UncategorizedSQLException`)이 나온다.
예외가 아예 안 나는 것이 아니라 **덜 정밀한 예외가 조용히 나오는** 결함이다. 수정은
setter에 정렬 한 줄을 넣어 관례에 합류시키는 것이다.

## 1. 무대 - 객체와 역할

결함은 설정에서 폴백까지 이어지는 사슬의 한가운데, 값을 저장하는 JavaBean에 있다. 각 층이 무엇을 맡는지부터 편다.

```
 설정 (XML 또는 코드)
   sql-error-codes.xml (jar 기본값) / 클래스패스 루트 오버라이드 / new SQLErrorCodes()
   |
   v
 SQLErrorCodesFactory (싱글턴)                spring-jdbc/support/SQLErrorCodesFactory.java
   |  getInstance()                                                        :80
   |  생성자: DefaultListableBeanFactory 로 XML 로드 -> setter 주입          :108-145
   |  SQL_ERROR_CODE_DEFAULT_PATH = org/springframework/jdbc/support/sql-error-codes.xml  :64
   |  SQL_ERROR_CODE_OVERRIDE_PATH = sql-error-codes.xml (클래스패스 루트)     :59
   |  getErrorCodes(String) / getErrorCodes(DataSource)                     :171 / :208
   v
 SQLErrorCodes (이번 무대 - 벤더별 에러코드 묶음 JavaBean)   spring-jdbc/support/SQLErrorCodes.java
   |  코드 배열 필드 10개, 전부 String[] 기본값 new String[0]                  :43-61
   |  setter 10개 - 아홉은 sortStringArray, 하나(L125)만 raw 대입              :105-183
   |  getDuplicateKeyCodes()                                                :121-123
   v
 SQLErrorCodeSQLExceptionTranslator          spring-jdbc/support/SQLErrorCodeSQLExceptionTranslator.java
   |  doTranslate: getErrorCode() 를 문자열로 만들어                          :183, :217-224
   |  커스텀 번역 binarySearch                                               :231
   |  그룹 코드 9종 binarySearch (duplicateKey 는 세 번째)                     :242-281 (:250)
   |  전부 miss 면 return null                                              :297
   v
 폴백 (AbstractFallbackSQLExceptionTranslator:108-112 이 연결)
   SQLExceptionSubclassTranslator      (JDBC4 예외 서브클래스 기반)            :75
   -> SQLStateSQLExceptionTranslator   (SQLState class code 기반)            :107
      23505 이거나 23000 + well-known 벤더 코드 7종이면 DuplicateKey           :137-139, :197-200
      그 외 23xxx 는 DataIntegrityViolation                                  :140
      아무것도 아니면 null                                                    :166
   -> JdbcTemplate 이 UncategorizedSQLException 으로 감쌈                     JdbcTemplate:1550
```

## 2. 핵심 이름표

이 결함을 읽을 때 헷갈리는 것은 "코드 목록"처럼 보이는 것이 저장측과 조회측 두
얼굴을 갖는다는 점이다. 아래 표는 각 이름표가 **저장 규칙 쪽인지 조회 규칙 쪽인지**를
명시한다.

| 이름 | 역할 | 결함과의 관계 |
|---|---|---|
| `duplicateKeyCodes` (String[]) | `DuplicateKeyException`으로 번역할 벤더 코드 목록. 기본값 `new String[0]`(L47) | 열 개 필드 중 유일하게 미정렬로 저장됐다 |
| `setDuplicateKeyCodes(String...)` L125 | XML `<property name="duplicateKeyCodes">`와 프로그래밍 주입의 진입점 | `this.duplicateKeyCodes = duplicateKeyCodes;` - 정렬 없음 |
| 형제 setter 9개 (L105/113/129/137/145/153/161/169/177) | 같은 역할, 같은 시그니처 | 전부 `StringUtils.sortStringArray(...)`를 거친다 |
| `StringUtils.sortStringArray` | 문자열 자연 순서(사전식)로 배열을 제자리 정렬해 그 배열을 반환. `Arrays.sort` - 복사본이 아니다 (StringUtils.java:1066-1073) | 저장측 불변식 "배열은 사전식 정렬"을 확립한다 |
| `Arrays.binarySearch(String[], String)` L250 | 사전식 정렬을 전제로 O(log n) 조회 | 전제가 깨지면 결과가 값 배치에 따라 달라진다 |
| `CustomSQLErrorCodesTranslation.setErrorCodes` L43-45 | 커스텀 번역용 코드 목록 | 이쪽도 정렬한다 - 비대칭의 또 다른 증거 |
| `SQLStateSQLExceptionTranslator.DUPLICATE_KEY_ERROR_CODES` L96-104 | well-known 중복키 코드 7종 (1, 301, 1062, 2601, 2627, -239, -268) | 이 코드들은 SQLState 23000일 때 폴백이 가려 준다 - 결함이 **커스텀 코드**에서 드러나는 이유 |
| `errorCode` (Translator L212-224) | `getErrorCode()`를 `Integer.toString` 한 값. `useSqlStateForTranslation`이면 SQLState 문자열 | 조회 키. **정수가 아니라 문자열**이라는 점이 사전식 정렬과 맞물린다 |

이 표에서 결함이 한 줄로 보인다. **저장 규칙은 열 개 setter가 각자 지키는 관례이고,
조회 규칙은 `binarySearch` 한 종류다.** 관례를 지키지 않은 setter가 하나 있으면
그 배열만 조회 규칙과 어긋나는데, 컴파일러도 타입도 그것을 잡아 주지 않는다.

## 3. 왜 "정렬"이 계약인가 - 숫자 순서와 사전식 순서

에러코드는 사람에게 정수로 보이지만 `SQLErrorCodes`는 전부 `String`으로 다룬다.
번역기가 `Integer.toString(current.getErrorCode())`로 조회 키를 만들기 때문이다
(L223). 그래서 정렬 기준도 사전식이고, **자릿수가 다른 코드가 섞이면 숫자 순서와
사전식 순서가 갈린다**.

```
숫자 순서   1062 < 1586 < 90002
사전식      "1062" < "1586" < "90002"      (이 경우는 우연히 일치)

숫자 순서   900 < 6550 < 17006
사전식      "17006" < "6550" < "900"       (완전히 뒤집힌다)
```

사용자가 코드 목록을 "숫자 순서로" 또는 "벤더 문서에 나온 순서로" 적는 것은 자연스러운
일이고, 배포 `sql-error-codes.xml`도 그렇게 적혀 있다(Oracle `badSqlGrammarCodes`가
`900,...,17006,6550`). 그래도 동작하는 이유는 setter가 정렬하기 때문이다.
즉 **"입력 순서는 자유"가 이 클래스의 사실상 계약**이고, 그 계약을 지키는 장치가
setter의 `sortStringArray` 호출이다.

## 4. 결함 경로 단계 추적 (실측)

입력: `setDuplicateKeyCodes("90002", "1586", "1062")`(사용자가 적은 순서). 사전식으로
정렬하면 `["1062", "1586", "90002"]`다. probe로 실제 실행해 확인한 결과가 아래다.

| 단계 | 정렬 저장(형제 setter와 동일) | 현행(미정렬) |
|---|---|---|
| 저장 배열 | `["1062", "1586", "90002"]` | `["90002", "1586", "1062"]` |
| `binarySearch(.., "90002")` | mid=1 `"1586"`<`"90002"` -> low=2 -> mid=2 hit | mid=1 `"1586"`<`"90002"` -> low=2 -> mid=2 `"1062"`<`"90002"` -> low=3 -> **miss(-4)** |
| 결과 (SQLState null) | DuplicateKeyException | null -> UncategorizedSQLException |
| 결과 (SQLState 23000) | DuplicateKeyException | **DataIntegrityViolationException** (23xxx 일반 폴백) |
| 결과 (SQLState HY000) | DuplicateKeyException | null -> UncategorizedSQLException |
| 같은 배열, 코드 `"1586"` | hit | hit (mid=1이 우연히 일치) |
| 같은 배열, 코드 `"1062"` | hit | mid=1 `"1586"`>`"1062"` -> mid=0 `"90002"`>`"1062"` -> **miss(-1)** |

같은 설정에서 코드에 따라 번역이 갈린다는 것이 이 결함의 핵심이다. 배열 0번 자리에
`"90002"`가 **버젓이 들어 있는데도** 조회가 못 찾는다 - 이진 탐색은 배열을 앞에서부터
읽지 않고 가운데에서 시작해 절반씩 버리며 들어가기 때문에, 정렬 전제가 깨지면
"있는데 못 찾는" 결과가 정상적으로 발생한다.

## 5. 계약

이 무대가 지키기로 한 약속을 네 줄로 세우고 수정 전 코드가 그중 무엇을 어겼는지 대조한다.

| 계약 | 출처 | 수정 전 위반 여부 |
|---|---|---|
| 코드 배열 setter는 입력 순서와 무관하게 사전식 정렬 배열을 저장한다 | 형제 setter 9개(L105-183) + `CustomSQLErrorCodesTranslation.setErrorCodes`(L43-45) | `setDuplicateKeyCodes`(L125)만 위반 |
| 코드 배열은 `Arrays.binarySearch`로 조회한다 | Translator L231, L242-281 (커스텀 1 + 그룹 9) | 위반 아님 - 소비측은 일관됐다 |
| 사용자에게 정렬 요구를 노출하지 않는다 | `SQLErrorCodes` 클래스 javadoc "JavaBean for holding JDBC error codes for a particular database"(L24-36) - 순서 언급 없음 | 위반 - 문서화되지 않은 순서 요구가 한 프로퍼티에만 있었다 |
| 배포 기본 구성은 그대로 동작한다 | `sql-error-codes.xml`의 duplicateKeyCodes 11개 목록 | 위반 아님 - 전부 우연히 사전식 정렬 상태(6절) |

## 6. 발화 조건 - 왜 아무도 못 봤나

세 겹의 우연이 이 결함을 가려 왔다.

**첫째, 배포 XML이 우연히 정렬 상태다.** `sql-error-codes.xml`의
`duplicateKeyCodes` 프로퍼티는 열한 개 벤더 빈에 하나씩 있고(L25, 52, 73, 106, 136,
154, 172, 199, 223, 250, 283), 그 값이 전부 사전식 정렬이다.

```
DB2        -803              Derby      23505          H2      23001,23505
HDB        301               HSQL       -104           Informix -239,-268,-6017
MS-SQL     2601,2627         MySQL      1062           Oracle   1
PostgreSQL 21000,23505       Sybase     2601,2615,2626
```

절반은 원소가 하나라 정렬 여부를 물을 것도 없고, 나머지도 우연히 맞았다. Informix의
`-239,-268,-6017`은 숫자로는 내림차순이지만 사전식으로는 오름차순이라 통과한다 -
누군가 사전식 기준으로 맞춰 놓은 흔적으로 읽힌다. 다른 프로퍼티였다면 미정렬이어도
setter가 고쳐 줬을 텐데, 하필 이 프로퍼티만 보호가 없는 채로 우연에 기대고 있었다.

**둘째, well-known 코드는 SQLState 폴백이 가려 준다.** 사용자가 커스텀 목록을
미정렬로 적어 `1062`(MySQL 중복키)가 miss 나더라도, 드라이버가 SQLState `23000`을
채워 보내면 `SQLStateSQLExceptionTranslator`가 `DUPLICATE_KEY_ERROR_CODES`에서
1062를 찾아 결국 `DuplicateKeyException`을 만든다(:96-104, :137-139, :197-200).
즉 **가장 흔한 코드일수록 결함이 안 보인다**. 결함이 드러나는 자리는 well-known
목록 밖의 코드 - 애플리케이션이 정의한 코드나 그 목록에 없는 벤더 코드다.

**셋째, 결함이 예외를 만들지 않는다.** 조회가 빗나가도 `binarySearch`는 음수를
돌려줄 뿐이고 사슬은 계속 흐른다. 사용자는 여전히 `DataAccessException`을 받는다 -
다만 `catch (DuplicateKeyException e)`로 잡으려던 코드가 안 잡을 뿐이다. 로그에
남는 것도 없다.

정리하면 발화 조건은 이렇다: **사용자 커스텀 `SQLErrorCodes`(오버라이드 XML 또는
프로그래밍 주입)에서 `duplicateKeyCodes`를 두 개 이상, 사전식 미정렬 순서로 준 경우.**
예를 들어 MySQL에 `1062, 1586`은 사전식 정렬이지만 `1586, 1062`는 아니고, 애플리케이션
정의 코드(`90002`)를 앞에 두는 경우도 그렇다.

## 7. 수정안

### 7.1 채택안 - setter에 정렬 한 줄

채택한 수정은 형제 setter가 이미 쓰던 줄을 그대로 가져오는 것이다.

```java
// before (L125-127)
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = duplicateKeyCodes;
}

// after
public void setDuplicateKeyCodes(String... duplicateKeyCodes) {
	this.duplicateKeyCodes = StringUtils.sortStringArray(duplicateKeyCodes);
}
```

`StringUtils`는 이미 임포트돼 있고(L22) 형제 setter 아홉 개가 같은 형태이므로,
새 의존도 새 동작도 생기지 않는다. 수정 후 이 파일의 코드 배열 setter 열 개는
글자 그대로 같은 모양이 된다.

### 7.2 기각한 대안 - 소비자에서 선형 탐색

`binarySearch` 대신 선형 탐색으로 바꾸면 정렬 전제 자체가 사라진다. 기각한 이유는
둘이다. (a) 형제 아홉 종과 규칙이 어긋나 한 배열만 다른 방식으로 조회하게 되고,
(b) 조회는 예외 한 건마다 최대 열 번 일어나므로 성능이 후퇴한다. 무엇보다 이 파일의
관례는 **저장측이 정렬을 책임진다**이고, 결함은 관례 위반이지 관례의 결함이 아니다.

### 7.3 영향 범위와 검증 계획

변경 범위는 파일 둘이고, 회귀 위험은 배포 기본값이 이미 정렬 상태라는 사실로 좁혀진다.

- 변경 파일: `SQLErrorCodes.java` 한 줄 + `SQLErrorCodeSQLExceptionTranslatorTests.java`
  테스트 추가.
- 회귀 위험: 배포 XML의 duplicateKeyCodes가 이미 정렬 상태이므로(6절) 기본 구성의
  동작은 문자 그대로 불변이다. 이미 정렬해 넣던 사용자도 불변이다. 동작이 바뀌는
  것은 미정렬로 넣던 사용자뿐이고, 그 변화가 곧 수정 목적이다.
- 테스트(test-first): 미정렬 `duplicateKeyCodes`로 구성한 translator가 세 코드
  전부를 `DuplicateKeyException`으로 번역하는지. 기존 `errorCodeTranslation`(정렬
  입력 `"10"`)이 양성 가드.
- 스모크: probe 재실행으로 fix 후 `unsorted -> DuplicateKeyException` 확인.

## 8. 범위 밖 - 인접하지만 이번에 안 건드린 것

같은 파일·같은 계열이지만 이번 PR이 손대지 않은 항목과, 확인하지 않은 이력을 남긴다.

- **getter가 내부 배열을 그대로 노출한다**(L121-123, 형제도 동일). 호출자가 반환
  배열을 변이하면 정렬이 깨지지만 기존 설계이고, 이 PR의 범위는 저장측이다.
- **varargs 배열의 주인 문제**. `sortStringArray`가 제자리 정렬이므로 사용자가
  `String[]` 변수를 넘기면 그 변수의 내용도 정렬된다. 이 역시 형제 아홉 개가 이미
  갖고 있던 동작이라 이 수정이 들여온 것이 아니다. 방어적 복사가 필요하다는 판단이
  선다면 그것은 setter 하나가 아니라 열 곳 전체에 대한 별개의 API 변경 논의다.
  자세한 것은 [Java varargs 실체](../../concepts/java-varargs-mechanics/java-varargs-mechanics.md).
- **`SQLErrorCodesFactory.getInstance()`의 지연 초기화 동기화**, **공유 빈 변이** -
  같은 파일 계열이지만 별건이다.
- **도입 시점**: `sortStringArray` 호출은 2012년 모듈 리네임 커밋(`02a4473c62d`)
  이전부터 존재한다. 이 setter만 처음부터 빠져 있었던 것으로 보이나 그 이전 이력은
  확인하지 않았다.
