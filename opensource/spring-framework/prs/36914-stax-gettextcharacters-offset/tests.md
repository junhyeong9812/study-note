# PR #36914 — 테스트 해설 (테스트 하나하나)

> PR #36914 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `XMLEventStreamReaderTests`에 회귀 테스트 하나와 그 헬퍼
하나다. 프로덕션 diff가 상한 계산 한 줄(`Math.min(length, source.length)` ->
`Math.min(length, source.length - sourceStart)`)이므로, 테스트도 그 한 줄이 만드는
차이만 정확히 겨눈다.

## 1. sourceStart 오프셋 존중 — red

유일한 회귀 테스트는 오프셋 4에서 남은 길이보다 큰 버퍼를 요청해, 예외 없이 올바른 구간만
복사되는지 본다.

```java
@Test  // getTextCharacters(sourceStart, ...) must not read past the source
void getTextCharactersHonorsSourceStart() throws Exception {
	advanceToCharacters();
	// text node is "content" (7 chars); copy from index 4 with an oversized buffer
	char[] target = new char[10];
	int count = streamReader.getTextCharacters(4, target, 0, 10);
	assertThat(count).isEqualTo(3);
	assertThat(new String(target, 0, count)).isEqualTo("ent");
}
```

- **주장**: 두 가지를 한꺼번에 주장한다. 첫째, 남은 문자 수보다 큰 `length`를 요청해도
  예외 없이 끝난다. 둘째, 반환값이 실제 복사량 3이고 버퍼 앞부분이 오프셋 이후의 올바른
  구간 `"ent"`다.
- **fix 전**: 상한이 `min(10, 7) = 7`로 계산되고 `System.arraycopy(source, 4, target, 0, 7)`이
  인덱스 4부터 7자, 즉 인덱스 10까지를 읽으려 한다. 길이 7인 배열에는 없는 인덱스이므로
  `ArrayIndexOutOfBoundsException`이 던져지고, 첫 단언에 닿기도 전에 실패한다. 명백한
  red이며, 실패 형태가 단언 실패가 아니라 예외라는 점이 결함의 성격(조용한 오답이 아니라
  즉시 크래시)을 그대로 반영한다.
- **fix 후**: 상한이 `min(10, 7 - 4) = 3`이 되어 `"ent"` 세 자만 복사하고 3을 반환한다.

**입력값 선택이 곧 설계다.** `sourceStart = 4`, `length = 10`, 텍스트 길이 7이라는 조합은
버그의 발생 조건 두 개를 동시에 만족시키는 최소 구성이다. 조건은 "오프셋이 0이 아니다"와
"남은 길이(3)가 요청 길이(10)보다 작다"인데, 둘 중 하나라도 빠지면 수정 전 코드도 정상
동작한다. `sourceStart = 0`이었다면 두 상한 계산식이 같은 값을 내므로 이 테스트는 가드로
전락했을 것이다.

**단언 두 개가 모두 필요한 이유**도 짚어 둘 만하다. 반환값 단언만 있으면 "아무것도
복사하지 않고 3을 반환하는" 엉터리 구현이 통과한다. 내용 단언만 있으면 반환값이
계약(실제 복사 문자 수)과 어긋나도 넘어간다. 특히 내용 단언이 `new String(target, 0, count)`로
**반환값을 길이로 써서** 검사하는 점이 중요하다 — 반환값과 실제 복사량이 서로를 검증하는
구조라, 한쪽만 맞고 다른 쪽이 틀린 구현은 통과할 수 없다.

`"ent"`라는 기대값 자체도 판별력을 갖는다. 만약 수정이 `sourceStart`를 무시하고 항상
0부터 복사하도록 잘못 조여졌다면 예외는 사라지지만 내용이 `"con"`이 되어 이 단언에서
잡힌다. 즉 이 테스트는 "예외만 막고 오프셋은 여전히 무시하는" 오수정도 함께 배제한다.

## 2. 헬퍼 — 커서를 텍스트 이벤트까지 전진

테스트 본문이 오프셋 계산에만 집중할 수 있도록, 커서를 텍스트 이벤트로 옮기는 일은 헬퍼
하나가 맡는다.

```java
private void advanceToCharacters() throws Exception {
	while (streamReader.getEventType() != XMLStreamConstants.CHARACTERS) {
		streamReader.next();
	}
}
```

- **역할**: `getTextCharacters`는 CHARACTERS·SPACE·CDATA 이벤트에서만 의미가 있으므로,
  테스트를 실행하기 전에 커서를 텍스트 노드로 옮겨야 한다.
- **이 형태를 고른 이유**: `next()` 횟수를 상수로 박지 않고 **이벤트 타입으로 조건을
  건다.** 픽스처 XML은 처리 명령(`<?pi content?>`)과 두 개의 시작 태그를 지나야 텍스트에
  닿는데, 파서 구현에 따라 START_DOCUMENT나 공백 이벤트를 내보내는 방식이 미묘하게 다를
  수 있다. 상수 반복은 JDK나 StAX 구현이 바뀌면 조용히 엉뚱한 이벤트에서 멈추는 취약한
  테스트가 된다.
- **테스트의 관심사 분리**: 검증 대상은 "텍스트 복사 계산"이지 "이벤트 순회"가 아니다.
  헬퍼로 전진 로직을 빼내면 테스트 본문에는 오프셋·길이·기대값만 남아 무엇을 주장하는지가
  한눈에 보인다.

## fixture

이 PR은 새 fixture를 만들지 않고 테스트 클래스가 이미 갖고 있던 것을 그대로 쓴다.

```java
private static final String XML =
		"<?pi content?><root xmlns='namespace'><prefix:child xmlns:prefix='namespace2'>content</prefix:child></root>"
		;

@BeforeEach
void createStreamReader() throws Exception {
	XMLInputFactory inputFactory = XMLInputFactory.newInstance();
	XMLEventReader eventReader = inputFactory.createXMLEventReader(new StringReader(XML));
	streamReader = new XMLEventStreamReader(eventReader);
}
```

이 fixture가 흉내 내는 실제 상황은 **StAX 이벤트 리더를 커서형 리더로 바꿔 쓰는 외부
호출자**다. 공개 진입점 `StaxUtils.createEventStreamReader(XMLEventReader)`가 반환하는
객체가 바로 이 `XMLEventStreamReader`이므로, 테스트가 생성자를 직접 부르긴 해도 관측
대상은 공개 API로 얻을 수 있는 것과 같은 인스턴스다. mock은 하나도 쓰지 않는데, 검증
대상이 협력자와의 상호작용이 아니라 **실제 파싱된 텍스트에 대한 산술**이기 때문이다.
JDK 표준 파서로 진짜 XML을 파싱해 얻은 `"content"` 7자가 있어야 경계 계산의 오류가 실제
`ArrayIndexOutOfBoundsException`으로 드러난다.

`"content"`라는 텍스트 노드가 하필 7자라는 점이 이 테스트를 가능하게 한다. 새 XML을
만들지 않고 기존 픽스처를 재사용할 수 있었던 이유이자, 회귀 테스트를 최소 침습으로
붙인 방식이다.

## 실측·역할 요약

수정 전후로 실제 실행한 결과를 건수·실패 형태·통과 값으로 정리하면 다음과 같다.

- 추가된 테스트: 1건(+ private 헬퍼 1개). 분류: red 1건, 가드 0건.
- fix 전 결과: `ArrayIndexOutOfBoundsException: arraycopy: last source index 11 out of
  bounds for char[7]` 계열의 예외로 실패(단언 도달 전). README에 기록된 재현 실행에서는
  버퍼 크기 4로 같은 계산을 돌려 `last source index 8 out of bounds for char[7]`을
  확인했다.
- fix 후 결과: 3 반환, `"ent"` 복사로 통과.

역할은 하나다. StAX javadoc이 예제 코드로 실어 둔 조각 읽기 루프(`sourceStart += length`)의
두 번째 반복을 테스트로 고정한다. 별도의 가드 테스트를 두지 않은 것은 기존 테스트
`readAll`과 `readCorrect`가 이미 일반 읽기·변환 경로 전체를 훑고 있어서, 상한 계산 한
줄이 그 경로를 깨뜨렸다면 그쪽에서 먼저 실패하기 때문이다. `sourceStart = 0`인 흔한
호출은 두 계산식이 같은 값을 내므로 애초에 회귀 위험이 없다는 점도 판단의 근거다.

## 후속 polish — 1건이 파라미터 5행으로

머지(`2b276311ebe`) 직후 Sam Brannen이 `ea2a26206cc`로 이 테스트만 손봤다. `@Test`
단일 케이스가 `@ParameterizedTest` + `@CsvSource(textBlock = ...)`로 바뀌고,
`sourceStart`가 `0, 1, 4, 6, 7` 다섯 행이 됐다. 기대값 칼럼은 문자열
(`content / ontent / ent / t / ''`) 하나뿐이고, 반환값 단언은 그 문자열에서
`assertThat(count).isEqualTo(expected.length())`로 유도한다. 본문 변화는 두 줄로 요약된다.

```java
-		int count = streamReader.getTextCharacters(4, target, 0, 10);
-		assertThat(count).isEqualTo(3);
+		int count = streamReader.getTextCharacters(sourceStart, target, 0, 10);
+		assertThat(count).isEqualTo(expected.length());
```

가드를 따로 두지 않겠다던 위 판단은 결과적으로 뒤집혔다. `0` 행이 바로 그 가드이며,
기존 테스트에 맡기는 대신 같은 메서드의 같은 표에 명시적으로 놓였다. 어느 테스트가
어떤 계약을 지키는지가 한 화면에서 보인다는 점에서 간접 근거보다 낫다. 그리고
`6`(남은 한 글자)과 `7`(남은 0 = 빈 문자열)은 새 상한식 `source.length - sourceStart`의
off-by-one을 잡는 자리다. 우리 케이스 `4`만으로는 상한식이 한 칸 어긋나 있어도
통과했을 수 있다. 재현 케이스 하나로 red를 만든 뒤, 고친 식의 정의역 양 끝을
파라미터로 같이 박아 두는 것이 이 유형의 기본형이다. 자세한 배경은
[README](README.md) 7절에 있다.
