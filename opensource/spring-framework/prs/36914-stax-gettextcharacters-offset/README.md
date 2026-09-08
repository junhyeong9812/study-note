# PR #36914 — Fix getTextCharacters to honor sourceStart offset

## 0. 정향

이 문서는 `spring-core`의 StAX 어댑터 `AbstractXMLStreamReader`에서 발생하던
`ArrayIndexOutOfBoundsException` 수정 PR을 처음부터 이해하기 위한 해설이다. 고친
코드는 한 줄이지만, 왜 그 한 줄이 틀렸는지는 StAX
`XMLStreamReader#getTextCharacters(int, char[], int, int)`의 계약 — 특히
`sourceStart`가 무엇을 뜻하는가 — 을 알아야 보인다. 다 읽으면 "긴 텍스트 노드를
조각내어 읽는 루프가 왜 두 번째 반복에서 터지는가"를 설명할 수 있어야 한다.

## 1. 배경 — 이 어댑터는 무엇이고 sourceStart는 무엇인가

StAX에는 XML을 읽는 API가 두 가지다. `XMLStreamReader`는 커서형(cursor)으로,
"현재 이벤트"에 커서를 두고 `getText()`·`getName()` 같은 접근자로 값을 뽑는다.
`XMLEventReader`는 객체형(iterator)으로, 이벤트마다 `XMLEvent` 객체를 하나씩
돌려준다. 표준 `XMLInputFactory`는 스트림 리더에서 이벤트 리더를 만들어 주지만,
그 반대는 만들어 주지 않는다.

Spring은 그 빈자리를 어댑터로 메운다. `XMLEventStreamReader`는 `XMLEventReader`를
감싸 `XMLStreamReader`처럼 보이게 하는 클래스이고, 공개 진입점은
`StaxUtils.createEventStreamReader(XMLEventReader)`다. 이 클래스의 javadoc이 그
동기를 그대로 적어 둔다.

```java
/**
 * Implementation of the {@link javax.xml.stream.XMLStreamReader} interface that wraps a
 * {@link XMLEventReader}. Useful because the StAX {@link javax.xml.stream.XMLInputFactory}
 * allows one to create an event reader from a stream reader, but not vice-versa.
 */
class XMLEventStreamReader extends AbstractXMLStreamReader {
```

`AbstractXMLStreamReader`는 그 어댑터의 추상 상위 클래스다. 서브클래스가 반드시
구현해야 하는 것은 `getEventType()`·`getText()`·`getName()` 같은 최소 접근자이고,
상위 클래스는 그 최소 접근자만으로 계산할 수 있는 나머지 인터페이스 메서드를
기본 구현으로 채운다. 예컨대 `getLocalName()`은 `getName().getLocalPart()`,
`getTextCharacters()`는 `getText().toCharArray()`다. 이번 버그가 있던 자리도 그런
파생 구현 중 하나다. 참고로 이 상위 클래스를 상속하는 구체 클래스는 현재 저장소에
`XMLEventStreamReader` 하나뿐이다.

`sourceStart`의 의미는 StAX 인터페이스 javadoc(JDK 21의
`java.xml/javax/xml/stream/XMLStreamReader.java`)이 규정한다. 원문 그대로다.

```
   * Gets the text associated with a CHARACTERS, SPACE or CDATA event.
   * Text starting a "sourceStart" is copied into "target" starting at "targetStart".
   * Up to "length" characters are copied.  The number of characters actually copied is returned.
   *
   * The "sourceStart" argument must be greater or equal to 0 and less than or equal to
   * the number of characters associated with the event.  Usually, one requests text starting at a "sourceStart" of 0.
   * If the number of characters actually copied is less than the "length", then there is no more text.
   * Otherwise, subsequent calls need to be made until all text has been retrieved.
```

핵심은 세 가지다. 첫째, `sourceStart`는 **원본 텍스트 안의 시작 인덱스**이지 대상
버퍼의 인덱스가 아니다(대상 쪽은 `targetStart`다). 둘째, `length`는 "최대 이만큼"이지
"반드시 이만큼"이 아니다. 셋째, 반환값은 **실제로 복사된 문자 수**이며, 그것이
`length`보다 작다는 사실이 곧 "텍스트가 여기서 끝났다"는 신호다.

그래서 이 메서드는 애초에 한 번에 다 읽으라고 만든 API가 아니다. 같은 javadoc이
권장 사용 패턴을 코드로 못박아 둔다.

```java
   * int length = 1024;
   * char[] myBuffer = new char[ length ];
   *
   * for ( int sourceStart = 0 ; ; sourceStart += length )
   * {
   *    int nCopied = stream.getTextCharacters( sourceStart, myBuffer, 0, length );
   *
   *   if (nCopied < length)
   *       break;
   * }
```

호출자는 고정 버퍼를 재사용하면서 `sourceStart`를 전진시키고, 복사량이 요청량보다
적어지는 순간 멈춘다. 즉 `sourceStart > 0`인 호출은 예외적 사용이 아니라 이 API의
정상적이고 의도된 사용이다.

## 2. 수정 전 동작 방식 — 실코드와 서사

수정 전 구현은 세 줄이었다. 상위 클래스의 `getTextCharacters()`(인자 없는 쪽)를
불러 전체 텍스트를 char 배열로 얻고, 길이를 자른 뒤, `System.arraycopy`로 옮긴다.

```java
	@Override
	public char[] getTextCharacters() {
		return getText().toCharArray();
	}

	@Override
	public int getTextCharacters(int sourceStart, char[] target, int targetStart, int length) {
		char[] source = getTextCharacters();
		length = Math.min(length, source.length);
		System.arraycopy(source, sourceStart, target, targetStart, length);
		return length;
	}
```

가운데 줄이 이 이야기의 전부다. 의도는 "요청한 `length`가 원본보다 크면 원본
크기까지만 복사한다"이고, 그 자체로는 합리적인 방어다. 그러나 기준이 `source.length`
— 원본의 **전체 길이** — 다. 복사가 실제로 시작되는 지점은 `sourceStart`인데, 길이
상한은 마치 항상 0부터 복사하는 것처럼 계산된다. 상한 계산과 복사 시작점이 서로
다른 전제를 쓰는 셈이다.

`sourceStart == 0`일 때는 두 전제가 우연히 일치하므로 코드가 정확히 맞게 동작한다.
버그가 오래 살아남은 이유이기도 하다. 대부분의 호출자는 javadoc이 말한 대로
"usually, one requests text starting at a sourceStart of 0"으로 쓰고, 저장소 안에서
이 오버로드를 호출하는 곳은 없다(`StaxStreamXMLReader`는 인자 없는
`getTextCharacters()`만 쓴다). 그래서 이 결함은 외부 호출자가 계약대로 조각 읽기를
시도할 때만 드러난다.

## 3. 무엇이 문제였나 — offset 무시가 만드는 잘못된 복사

결론부터 말하면, `sourceStart > 0`이고 남은 문자 수가 요청한 `length`보다 적으면
`System.arraycopy`가 원본 배열 끝을 넘어 읽으려 하고 `ArrayIndexOutOfBoundsException`이
던져진다. 계약상으로는 "남은 만큼만 복사하고 그 수를 반환"해야 하는 자리다.

구체적으로 재현해 보자. 텍스트 노드가 `"content"`(7자)이고 호출자가 4자짜리 버퍼로
javadoc의 루프를 도는 상황이다. 아래는 수정 전·후 상한 계산식을 그대로 옮겨
JDK 21로 실행한 결과다.

```
buggy sourceStart=0 -> 4 'cont'
buggy sourceStart=4 -> java.lang.ArrayIndexOutOfBoundsException: arraycopy: last source index 8 out of bounds for char[7]
fixed sourceStart=4 -> 3 'ent'
```

첫 번째 반복은 정상이다. `length = min(4, 7) = 4`, `arraycopy(source, 0, target, 0, 4)`가
`"cont"`를 복사하고 4를 반환한다. 반환값이 요청량과 같으니 호출자는 규약대로
`sourceStart += 4`로 전진해 다시 부른다.

두 번째 반복에서 어긋난다. 남은 문자는 인덱스 4~6의 세 자(`"ent"`)뿐인데,
상한 계산은 여전히 `min(4, 7) = 4`를 내놓는다. `arraycopy`는 인덱스 4부터 4자를,
즉 인덱스 7까지를 읽으려 하고, 길이 7인 배열에는 인덱스 7이 없으므로 예외가 난다.
예외 메시지의 "last source index 8 out of bounds for char[7]"이 정확히 그 초과를
가리킨다.

여기서 값 세 개만 비교하면 어긋남이 분명해진다.

| 항목 | sourceStart=0 | sourceStart=4 |
|---|---|---|
| 남은 문자 수 (7 - sourceStart) | 7 | 3 |
| 수정 전 상한 `min(4, 7)` | 4 | 4 |
| 수정 후 상한 `min(4, 7 - sourceStart)` | 4 | 3 |

첫 열에서는 두 상한이 같아 차이가 보이지 않고, 둘째 열에서만 수정 전 값이 남은
문자 수를 초과한다. 버그의 조건이 "offset이 0이 아니고, 남은 길이가 요청 길이보다
작을 때"임을 이 두 열이 그대로 보여 준다.

문제의 성격도 짚어 둘 만하다. 이것은 조용히 잘못된 값을 돌려주는 결함이 아니라
즉시 예외로 터지는 결함이고, 그 예외가 공개 API 경로에서 난다.
`StaxUtils.createEventStreamReader(XMLEventReader)`는 public이고, 그 반환값은
`XMLStreamReader` 타입이므로 호출자는 인터페이스 javadoc이 보장한 대로 쓸 권리가
있다. 계약이 권장한 사용 패턴이 곧 크래시 재현 절차가 되는 상태였다.

## 4. 수정 해설 — 무엇을 왜 바꿨나

수정은 상한의 기준을 "원본 전체 길이"에서 "`sourceStart` 이후 남은 길이"로 바꾼다.
diff는 한 줄이다.

```java
	public int getTextCharacters(int sourceStart, char[] target, int targetStart, int length) {
		char[] source = getTextCharacters();
-		length = Math.min(length, source.length);
+		length = Math.min(length, source.length - sourceStart);
		System.arraycopy(source, sourceStart, target, targetStart, length);
		return length;
	}
```

이 한 줄로 상한 계산과 복사 시작점이 같은 전제를 공유하게 된다. `source.length -
sourceStart`는 곧 "이 위치에서 아직 읽을 수 있는 문자 수"이므로, `arraycopy`가
원본 끝을 넘길 수 없다. 그리고 잘려서 줄어든 `length`가 그대로 반환되므로,
"복사한 수가 요청한 수보다 작다 = 더 이상 텍스트가 없다"는 계약상의 종료 신호도
자동으로 맞아떨어진다. 위 실행 결과의 `fixed sourceStart=4 -> 3 'ent'`가 그
두 가지를 동시에 보여 준다 — 예외 없이 3을 반환하고, 3 < 4이므로 호출자의 루프가
정상 종료한다.

경계 몇 가지도 확인해 두면 좋다. `sourceStart == source.length`(텍스트를 정확히
다 읽고 한 번 더 부른 경우)이면 상한이 0이 되어 아무것도 복사하지 않고 0을
반환한다 — javadoc이 `sourceStart`를 "less than or equal to the number of
characters"로 허용하므로 이는 유효한 호출이고, 0 반환이 올바른 답이다.
`sourceStart`가 그보다 더 크면 상한이 음수가 되어 `arraycopy`가
`IndexOutOfBoundsException`을 던지는데, 이는 javadoc이 규정한 범위를 벗어난
입력이므로 예외가 나는 것이 정상이다. 즉 수정은 유효 입력에서 예외를 없애되
무효 입력을 조용히 삼키지 않는다.

수정 범위를 최소로 유지한 판단도 의식적이다. `getTextCharacters()`가 호출될 때마다
`getText().toCharArray()`로 새 배열을 만들기 때문에, 조각 읽기 루프는 조각 수에
비례해 전체 텍스트를 반복 복사한다(성능상 O(n^2)). 캐싱으로 개선할 여지가 있지만,
그것은 정확성 결함이 아니라 별개의 성능 주제다. 버그 수정 PR에서 함께 건드리면
리뷰 대상이 흐려지므로 이번 변경은 상한 계산 한 줄에만 손댔다.

## 5. 검증 — 테스트가 무엇을 고정하나

테스트는 `XMLEventStreamReaderTests`에 회귀 테스트 하나로 추가된다. 이 테스트
클래스는 이미 `"<?pi content?><root xmlns='namespace'><prefix:child
xmlns:prefix='namespace2'>content</prefix:child></root>"`를 파싱하는 픽스처를 갖고
있어서, `"content"`라는 7자 텍스트 노드를 그대로 쓸 수 있다.

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

	private void advanceToCharacters() throws Exception {
		while (streamReader.getEventType() != XMLStreamConstants.CHARACTERS) {
			streamReader.next();
		}
	}
```

이 테스트가 고정하는 것은 두 가지다. 첫째, `sourceStart=4`에 남은 길이보다 큰
`length=10`을 줘도 예외 없이 끝난다 — 수정 전이라면 `assertThat`에 닿기도 전에
`ArrayIndexOutOfBoundsException`으로 실패한다. 둘째, 반환값이 실제 복사량인 3이고
버퍼 앞부분이 `"ent"`다 — 즉 예외만 막은 것이 아니라 **오프셋 이후의 올바른 구간**을
복사했음을 확인한다. 반환값 단언만 있고 내용 단언이 없으면 "0을 반환하고 아무것도
안 하는" 구현도 통과하므로, 두 단언이 함께 있어야 계약을 실제로 붙잡는다.

`advanceToCharacters()` 헬퍼는 커서를 CHARACTERS 이벤트까지 전진시킨다. 픽스처 XML은
처리 명령(`<?pi content?>`)과 두 개의 시작 태그를 먼저 지나야 텍스트에 닿기 때문에,
`next()` 횟수를 상수로 박는 대신 이벤트 타입으로 조건을 거는 편이 파서 구현 차이에
덜 민감하다.

## 6. 상태와 교훈

PR은 현재 OPEN이며 리뷰나 라벨은 아직 붙지 않았다(2026-08-15 기준, `mergedAt`
없음). 트리아지 참고용 코멘트를 한 번 남겨 두었는데, 요지는 "공개 API 경로에서
나는 `ArrayIndexOutOfBoundsException`이고, 계약이 권장한 조각 읽기 루프가 곧
재현 절차"라는 점이었다.

교훈 하나. **경계 계산은 복사 시작점과 같은 전제를 써야 한다.** 이 버그의 정체는
"상한은 0부터 센 길이, 복사는 offset부터"라는 전제 불일치였고, `sourceStart == 0`인
흔한 경로에서는 두 전제가 겹쳐서 증상이 나오지 않았다. 인덱스와 길이를 함께 받는
API를 구현할 때는 "이 상한이 어느 지점을 기준으로 한 값인가"를 한 번 소리 내어
확인하는 편이 안전하다.

교훈 둘. **인터페이스 javadoc의 예제 코드는 곧 테스트 시나리오다.** StAX가
`sourceStart += length` 루프를 예제로 실어 둔 것은 그 사용법이 지원 대상임을
선언한 것이다. 라이브러리 인터페이스를 구현할 때 그 예제를 그대로 돌려 보는 것만으로
이 결함은 즉시 드러났을 것이다. 구현이 "보통의 호출"만 만족시키고 있지는 않은지,
계약 문서가 명시한 사용 패턴을 기준으로 점검할 필요가 있다.

## 7. 머지와 후속 polish — 단일 케이스가 경계 스펙트럼으로 펼쳐졌다

2026-09-04에 Sam Brannen이 `2b276311ebe`로 7.0.x와 main 양쪽에 머지했다(마일스톤
7.0.10). 프로덕션 diff는 제출본 그대로 상한 계산 한 줄이고 author도 유지됐다. 다만
커밋 메시지는 메인테이너가 다시 썼다 — 제목이 `Honor sourceStart offset in
AbstractXMLStreamReader#getTextCharacters`로 바뀌고 본문에 `Closes gh-36914`가
붙었으며, 테스트 주석도 설명문에서 `// gh-36914` 이슈 참조로 정리됐다. 커밋 제목을
"무엇을 고쳤다"가 아니라 "무엇을 지키게 했다"로 쓰는 관례, 그리고 이슈 번호 주석
관례는 다음 제출에서 미리 맞출 수 있는 부분이다.

이어서 같은 날 `ea2a26206cc`("Polish contribution", See gh-36914)로 **테스트만**
바뀌었다. 우리가 낸 단일 케이스(`sourceStart = 4`)가 파라미터화 테스트로 펼쳐졌다.

```java
	@ParameterizedTest  // gh-36914
	@CsvSource(textBlock = """
			0, content
			1, ontent
			4, ent
			6, t
			7, ''
			""")
	void getTextCharactersHonorsSourceStart(int sourceStart, String expected) throws Exception {
		advanceToCharacters();

		// text node is "content" (7 chars); request an oversized buffer to ensure
		// getTextCharacters(sourceStart, ...) does not read past the source
		char[] target = new char[10];
		int count = streamReader.getTextCharacters(sourceStart, target, 0, 10);

		assertThat(count).isEqualTo(expected.length());
		assertThat(new String(target, 0, count)).isEqualTo(expected);
	}
```

다섯 값이 임의로 고른 샘플이 아니라 스펙트럼의 양 끝과 그 사이다. `0`은 오프셋이
없어 수정 전에도 통과하던 경로(회귀 가드), `1`과 `4`는 중간, `6`은 남은 문자가 하나뿐인
직전 경계, `7`은 텍스트 길이와 같은 값이라 남은 문자가 0이다. 7이 빈 문자열 경계인
이유는 상한식 자체에 있다. 수정된 상한은 `source.length - sourceStart`이고 `"content"`는
7자이므로 `sourceStart = 7`이면 상한이 0이 되어 아무것도 복사하지 않고 0을 반환한다.
javadoc이 `sourceStart`를 "문자 수 이하"로 허용하므로 이는 유효 입력이고, 0 반환이
올바른 답이다(4절에서 서술만 해 둔 경계가 여기서 테스트로 박혔다).

기대값 칼럼 하나가 두 단언을 동시에 먹인다는 점도 눈여겨볼 만하다. `count`를 별도
칼럼으로 두지 않고 `expected.length()`로 유도해서, CSV 행이 늘어도 손으로 맞춰야 할
숫자가 없다. 빈 문자열은 `''`로 표기한다.

다음 PR에서 먼저 쓸 수 있는 교훈은 분명하다. **경계 계산식을 바꾸는 수정이면 그 식의
정의역 끝을 테스트 파라미터로 먼저 펼쳐라.** 우리 단일 케이스는 버그의 존재는 증명했지만
새 식이 옳다는 것은 한 점에서만 보였다. 만약 수정이 `source.length - sourceStart + 1`
같은 off-by-one이었다면 `sourceStart = 4`는 여전히 통과했을 수 있고, 그것을 잡아내는
것은 정확히 `6`과 `7`이다. 즉 파라미터화는 가독성 개선이 아니라 이 수정에서 검증
강도 자체를 올린다. 회귀 테스트를 "결함을 재현하는 한 점"으로 끝내지 말고 "고친 식이
정의된 구간 전체"로 잡는 편이 낫다.

## 부록 — 읽은 파일

이 해설의 근거가 된 실파일은 다섯이다. 넷은 저장소 안의 어댑터·테스트 코드이고, 하나는
계약의 출처인 JDK 인터페이스 소스다.

- `spring-core/src/main/java/org/springframework/util/xml/AbstractXMLStreamReader.java` (upstream/main)
- `spring-core/src/main/java/org/springframework/util/xml/XMLEventStreamReader.java` (upstream/main)
- `spring-core/src/main/java/org/springframework/util/xml/StaxUtils.java` (upstream/main, `createEventStreamReader` 부분)
- `spring-core/src/test/java/org/springframework/util/xml/XMLEventStreamReaderTests.java` (upstream/main)
- JDK 21 `java.xml/javax/xml/stream/XMLStreamReader.java` (src.zip, `getTextCharacters` javadoc)

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
