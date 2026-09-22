# PR #36915 분석 — AbstractXMLStreamReader.require의 네임스페이스·로컬명 검증 누락

> 기준: PR base `0c60266986` = 현재 `upstream/main` `7daf1013aa8` (`AbstractXMLStreamReader.java`·`XMLEventStreamReader.java`는 두 커밋 사이 무변경 — `git diff`로 확인).
> PR head: `refs/pr/36915`. 상태 OPEN, 라벨 `status: waiting-for-triage` 하나, 코멘트 0건. 2026-06-13 생성.
> 관련 작업 폴더: `docs/plans/2026-06-13/spring-core-bug-hunt/B8-xmlstreamreader-require/task.md`(발견·재현), `docs/plans/2026-08-06/pr36915-scope-hardening/`(경계 확정 계획 — 계획만 수립, 실행 보류).
> README(서사)·structure.md(무대 지도)·tests.md(테스트 해설)와 중복을 피하고, 호출 그래프·이름표 사전·단계 추적·수정안 판단에 집중한다.

## 0. 결론

`AbstractXMLStreamReader.require(int expectedType, String namespaceURI, String localName)`는 이벤트 타입만 비교하고 **나머지 두 파라미터를 본문에서 한 번도 읽지 않아**, JSR-173이 "비-null이면 반드시 대조하라"고 규정한 이름·네임스페이스 검증이 통째로 사라진 채 어서션이 항상 성공했다.\
수정은 이벤트 타입 가드 한 블록과 `equals` 대조 두 블록을 더해 계약대로 검증하게 하고, 시그니처에 `@Nullable`을 붙여 null 허용을 타입 수준에 기록한다.\
PR은 제출 후 리뷰 대기 상태이며, 라벨이 붙지 않은 채 정체되어 있다.

> **JSR-173 (StAX 명세)** — `javax.xml.stream` 패키지의 동작을 정의한 자바 표준 명세.\
> 예: `require(int, String, String)`의 "null이면 검사하지 않는다" 규칙이 이 명세와 그 javadoc에 적혀 있다.

> **어서션 (assertion)** — 값을 계산해 돌려주는 대신 조건이 참임을 확인하고, 아니면 즉시 실패시키는 장치.\
> 예: `require(START_ELEMENT, "namespace", "root")`은 반환값이 없고, 커서가 그 요소가 아니면 `XMLStreamException`을 던진다.

## 1. 무대

결함은 StAX 어댑터 상위 클래스의 어서션 메서드 하나에 있고, 그 메서드는 저장소 안에 호출처가 하나도 없는 순수한 공개 계약 표면이다.\
다음 표는 그 좌표를 항목별로 정리한 것이다.

> **공개 계약 표면 (public contract surface)** — 외부 코드가 호출할 수 있고 그 동작이 문서로 약속돼 있는 API 표면.\
> 예: `StaxUtils.createEventStreamReader()`가 `XMLStreamReader` 타입으로 돌려준 객체의 `require()`는 구현 클래스가 package-private이어도 외부가 계약대로 쓸 권리가 있다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 패키지 | `org.springframework.util.xml` |
| 결함 파일 | `spring-core/src/main/java/org/springframework/util/xml/AbstractXMLStreamReader.java` |
| 결함 메서드 | `require(int, String, String)` (수정 전 `:155-161`, 수정 후 `:155-175`) |
| 유일한 서브클래스 | `XMLEventStreamReader` (`XMLEventStreamReader.java:45`) |
| 공개 진입 API | `StaxUtils.createEventStreamReader(XMLEventReader)` (`StaxUtils.java:303`) |
| 테스트 | `spring-core/src/test/java/org/springframework/util/xml/XMLEventStreamReaderTests.java` |

`require()`가 존재하는 이유는 계산이 아니라 **어서션**이다.\
파싱 코드가 "여기까지 왔으면 커서는 반드시 이 요소여야 한다"를 코드로 못 박아, 문서 형식이 기대와 다르면 엉뚱한 값을 읽어 내려가는 대신 그 자리에서 실패하게 만든다.

누가 부르는가가 이 결함의 성격을 결정한다.\
`git grep "\.require("`를 base 커밋에 돌리면 **저장소 전체에 호출처가 0건**이다(프로덕션도 테스트도).\
어댑터 자체는 `XStreamMarshaller.unmarshalXmlEventReader`(`XStreamMarshaller.java:784-787`)가 만들어 XStream의 `StaxReader`에 넘기지만, 그 라이브러리가 `require()`를 쓰는지는 Spring이 통제하지 않는다.\
즉 `require()`는 **내부 소비자가 없는 공개 계약 표면**이고, 내부 테스트가 결코 밟지 않는 사각지대다.\
결함이 2012년 모듈 리네이밍(`02a4473c62d`) 시점 형태 그대로 살아남은 구조적 이유가 여기 있다.

## 2. 전체 메서드 그래프

아래 그래프는 어댑터가 만들어져 소비되는 경로, 결함이 있던 수정 전 본문, 수정이 새로 잇는 간선, 그리고 같은 클래스에 이미 있던 대조군을 차례로 놓은 것이다.\
오른쪽 숫자는 각 파일의 줄 번호다.

```text
[어댑터 생성]
 StaxUtils.createEventStreamReader(eventReader)                 StaxUtils.java:303  (public static)
   -> new XMLEventStreamReader(eventReader)                     XMLEventStreamReader.java:52-55
        this.eventReader = eventReader                          :53
        this.event = eventReader.nextEvent()                    :54   커서가 첫 이벤트에 이미 놓임
   -> 반환 타입은 javax.xml.stream.XMLStreamReader (JDK 표준 인터페이스)

[호출자가 커서를 전진시키며 소비]
 reader.next()                                                  XMLEventStreamReader.java:274-278
   this.event = this.eventReader.nextEvent()                     :276
   return this.event.getEventType()                              :277

[결함 경로 — 호출자가 위치를 못 박으려 할 때]
 (호출자) reader.require(START_ELEMENT, "wrong-namespace", "wrong")
    |
    v
 AbstractXMLStreamReader.require(expectedType, namespaceURI, localName)      :155-161 (수정 전)
    |
    +-- (1) int eventType = getEventType();                                  :157
    |         -> XMLEventStreamReader.getEventType()                         :76-79
    |              -> this.event.getEventType()                              :78
    |
    +-- (2) if (eventType != expectedType) throw XMLStreamException          :158-160
    |
    +-- (3) (본문 끝 — return)                                                :161  [BUG]
              namespaceURI, localName 은 어느 줄에도 등장하지 않는다.

[수정이 새로 잇는 간선 — 이미 존재하던 접근자를 부르기만 하면 된다]
 require(...) (수정 후)                                                       :155-175
    +-- (2') 이벤트 타입 가드                                                 :165-168
    |         (namespaceURI != null || localName != null)
    |         && eventType != START_ELEMENT && eventType != END_ELEMENT
    |         -> throw XMLStreamException("Current event is not a START_ELEMENT or END_ELEMENT")
    |
    +-- (3') localName 대조                                                   :169-171
    |         -> AbstractXMLStreamReader.getLocalName()                       :180-183
    |              -> return getName().getLocalPart();      (!) 이벤트 타입 가드 없음
    |                   -> XMLEventStreamReader.getName()                     :58-69
    |                        isStartElement() -> asStartElement().getName()   :60-61
    |                        isEndElement()   -> asEndElement().getName()     :63-64
    |                        그 외            -> throw IllegalStateException  :67
    |
    +-- (4') namespaceURI 대조                                                :172-174
              -> AbstractXMLStreamReader.getNamespaceURI()                    :80-89
                   eventType in {START_ELEMENT, END_ELEMENT} ?
                     getName().getNamespaceURI()                              :84
                   : throw IllegalStateException("Parser must be on ...")     :87

[대조군 — 같은 클래스에 이미 "null = 와일드카드" 규칙 구현체가 있었다]
 AbstractXMLStreamReader.getAttributeValue(namespaceURI, localName)          :163-173
   name.getLocalPart().equals(localName)
       && (namespaceURI == null || name.getNamespaceURI().equals(namespaceURI))   :167-168
```

그래프의 요점은 **수정이 새 자료를 끌어오지 않는다**는 것이다.\
`getLocalName()`도 `getNamespaceURI()`도 이미 같은 클래스에 있었고, `require()`가 그것을 부르지 않았을 뿐이다.\
그리고 (3')이 지나가는 `getLocalName()`에는 이벤트 타입 가드가 없어 `getName()`의 `IllegalStateException`이 그대로 새어 나온다 — 그래서 (2')가 (3')보다 **앞에** 와야 한다.\
이 순서 제약이 수정의 유일한 설계 판단이다.

## 2.5 핵심 이름표 사전

이 흐름의 함정은 "이름"이 세 종류라는 점이다: 호출자가 요구하는 기대값, 현재 이벤트가 실제로 가진 값, 그리고 "검사하지 마라"를 뜻하는 null.\
아래 표는 각 이름표가 그중 무엇을 들고 있고 언제 평가되는지를 명시한다.\
예시는 픽스처 `<?pi content?><root xmlns='namespace'><prefix:child xmlns:prefix='namespace2'>content</prefix:child></root>`에서 커서가 `root`의 START_ELEMENT에 있을 때다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `require(int,String,String)` (`:155`) | 커서 위치 어서션. 불일치면 `XMLStreamException` | (expectedType, namespaceURI, localName) -> void 또는 예외 | 저장소 내 호출처 0건. 외부 호출자 전용 | 결함 본체. 수정 전 본문 5줄이 세 인자 중 하나만 읽었다 |
| `expectedType` (파라미터) | 호출자가 기대하는 이벤트 타입 상수 | 예: `XMLStreamConstants.START_ELEMENT`(=1) | `:158`(수정 후 `:160`)이 1회 소비 | 유일하게 검증되던 인자. 이 부분은 수정 전후 무변경 |
| `namespaceURI` (파라미터) | 기대 네임스페이스 URI. **null = 검사 안 함** | `"namespace"` 또는 `null` | 수정 전 소비처 0. 수정 후 `:165`(가드)와 `:172`(대조) | 결함의 절반. 비-null인데 무시되어 틀린 네임스페이스가 통과 |
| `localName` (파라미터) | 기대 로컬 이름. **null = 검사 안 함** | `"root"` 또는 `null` | 수정 전 소비처 0. 수정 후 `:165`(가드)와 `:169`(대조) | 결함의 나머지 절반 |
| `eventType` (지역변수, `:157`) | 현재 이벤트의 실제 타입 | `getEventType()` -> 1 (START_ELEMENT) | `:158` 비교, 수정 후 `:166` 가드가 재사용 | 한 번 읽어 두 판정에 재사용된다. 가드가 별도 호출을 하지 않는 이유 |
| `getEventType()` (`XMLEventStreamReader.java:76-79`) | 현재 이벤트 타입 조회 | () -> `this.event.getEventType()` | `require`·`hasName`·`hasText`·`isStartElement` 등 다수 | 결함 전후 모두 유일하게 안전한(예외 없는) 접근자 |
| `getLocalName()` (`:180-183`) | 현재 요소의 로컬 이름 | () -> `getName().getLocalPart()` -> `"root"` | 수정 후 `:169`·`:170`이 부름(대조 1회 + 메시지 1회) | **이벤트 타입 가드가 없다.** 요소 이벤트 밖에서 `IllegalStateException`. 가드 블록이 필요한 직접 원인 |
| `getNamespaceURI()` (`:80-89`) | 현재 요소의 네임스페이스 URI | () -> `"namespace"`, 요소 아니면 `IllegalStateException` | 수정 후 `:172`·`:173` | 자체 가드가 있으나 예외 타입이 `IllegalStateException`이라 계약(`XMLStreamException`)과 어긋난다 |
| `getName()` (`XMLEventStreamReader.java:58-69`) | 현재 요소의 `QName` | () -> `{namespace}root`, 요소 아니면 `IllegalStateException`(`:67`) | `getLocalName()`·`getNamespaceURI()`·`getPrefix()`가 경유 | 이름 관련 모든 경로의 종착점이자 예외 발생원 |
| `getPrefix()` (`:104-113`) | 접두사 조회 (가드 있음) | () -> `""`(기본 네임스페이스) 또는 `"prefix"` | `require`는 부르지 않음 | 대조군. `getNamespaceURI`와 함께 가드를 가진 두 접근자 — `getLocalName()`만 없다는 비대칭을 드러낸다 |
| `hasName()` (`:115-119`) | 현재 이벤트가 이름을 갖는가 | () -> `eventType in {START_ELEMENT, END_ELEMENT}` | `require`는 부르지 않음 | 수정의 가드 조건과 논리적으로 같다. 재사용하지 않고 조건을 인라인한 것은 `eventType` 지역변수를 이미 들고 있기 때문 |
| `getAttributeValue(String,String)` (`:163-173`) | 속성 값 조회 | (ns, localName) -> 값 또는 null | 외부 호출자 | **선례**. 같은 클래스가 이미 "localName은 equals, namespaceURI는 null이면 건너뜀"을 구현하고 있었다. `require`만 그 규칙을 빠뜨렸다 |
| `QName` (JDK) | `{namespaceURI, localPart, prefix}` 3조 | `getName()`의 반환 | 이름 관련 접근자 전부 | `require`의 두 파라미터가 정확히 이 3조 중 두 개에 대응한다. 접두사는 문서마다 바뀌므로 비교 대상이 아니다 |
| `@Nullable` (`org.jspecify.annotations`) | null 허용을 타입 수준에 기록 | 수정이 두 파라미터에 부착 | 정적 분석·IDE | 계약상 null 허용이라는 사실이 코드에 없던 것을 채운다. 이 파일은 `getAttributeValue`에서 이미 쓰고 있어 import 변경 0 |
| `advanceToStartElement(String)` (테스트 헬퍼) | 커서를 지정 이름의 START_ELEMENT까지 전진 | (localName) -> void | 회귀 테스트 1회 | 조건식에서 `getEventType()`를 `\|\|` **왼쪽**에 두어 단락 평가로 `getLocalName()` 호출을 피한다. 수정 본문의 가드 순서와 같은 제약을 테스트 코드가 두 번째로 실증한다 |

표가 드러내는 것은 두 겹이다.\
겉의 결함은 "비-null 인자를 안 읽는다"이고, 그 아래 숨은 제약은 "이름을 읽으려면 먼저 이벤트 타입을 확인해야 한다 — `getLocalName()`이 스스로 방어하지 않으므로"다.

## 3. 결함 경로 단계 추적

커서가 `root`(네임스페이스 `namespace`)의 START_ELEMENT에 놓인 상태에서, 계약상 예외가 나야 하는 호출 `require(START_ELEMENT, null, "wrong")`을 수정 전후로 추적한다.

| 단계 | 코드 | 수정 전 (결함) | 수정 후 (정상) |
|---|---|---|---|
| (1) 실제 타입 조회 | `:157` `eventType = getEventType()` | `1` (START_ELEMENT) | 동일 |
| (2) 타입 비교 | `:158` `eventType != expectedType` | `1 != 1` 거짓 -> 통과 | 동일 |
| (3) 이벤트 타입 가드 | (없음) / `:165-168` | 단계 자체가 없음 | `localName != null` 참이지만 `eventType == START_ELEMENT`라 조건 거짓 -> 통과 |
| (4) localName 대조 | (없음) / `:169-171` | 단계 자체가 없음 | `"wrong".equals(getLocalName())` -> `"wrong".equals("root")` 거짓 -> **`XMLStreamException("Expected local name [wrong] but read [root]")`** |
| (5) namespaceURI 대조 | (없음) / `:172-174` | 단계 자체가 없음 | (4)에서 던져 도달 안 함 |
| (6) 결과 | | **정상 반환 — 호출자는 "검증했다"고 믿는다** | 예외 |

두 번째 변형 `require(START_ELEMENT, "wrong-namespace", "root")`은 (4)를 `"root".equals("root")` 참으로 통과한 뒤 (5)에서 `"wrong-namespace".equals("namespace")` 거짓으로 `XMLStreamException("Expected namespace [wrong-namespace] but read [namespace]")`을 던진다.\
두 변형이 각각 한 필드씩만 어긋나게 설계된 이유는, 한 줄로 합치면 "localName 검사만 구현하고 namespace 검사를 빠뜨린 절반 수정"이 통과하기 때문이다 — 실제 수정 코드에서 localName 검사가 먼저 오므로 그 위험은 실재한다.

세 번째 경로가 이 수정의 숨은 위험이다.\
커서를 CHARACTERS 이벤트에 두고 `require(CHARACTERS, null, "x")`를 부르는 경우다.

| 단계 | 가드가 **없다면** | 가드가 있으면 (수정안) |
|---|---|---|
| (2) 타입 비교 | `CHARACTERS == CHARACTERS` -> 통과 | 동일 |
| (3) 가드 | 단계 없음 | `localName != null` 참 && `eventType`이 요소가 아님 -> `XMLStreamException("Current event is not a START_ELEMENT or END_ELEMENT")` |
| (4) localName 대조 | `getLocalName()` -> `getName()` -> `XMLEventStreamReader:67` **`IllegalStateException`** | 도달 안 함 |
| 결과 | 시그니처가 약속한 checked `XMLStreamException` 대신 unchecked 런타임 예외가 호출자의 catch를 뚫고 나간다 | 계약이 정한 예외 타입으로 보고 |

즉 가드는 장식이 아니라 **load-bearing**이다.\
이 판정은 `docs/plans/2026-08-06/pr36915-scope-hardening/log.md`가 "핵심 발견"으로 기록한 내용과 같으며, 근거는 `getLocalName()`(`:180-183`)에 가드가 없다는 실코드 사실이다.

> **load-bearing (하중을 받는)** — 있어도 그만인 장식이 아니라, 빼면 다른 부분이 곧바로 무너지는 필수 요소.\
> 예: 이벤트 타입 가드를 지우면 `require(CHARACTERS, null, "x")`가 계약 밖 `IllegalStateException`으로 새어 나간다.

## 4. 계약과 위반

`javax.xml.stream.XMLStreamReader#require(int, String, String)`의 javadoc이 고정하는 것은 셋이다.

- **(C1)** "Test if the current event is of the given type" — 타입 불일치는 예외.
- **(C2)** "and if the namespace and name match the current namespace and name of the current event" — 비-null 인자는 현재 이벤트의 값과 일치해야 한다.
- **(C3)** "If the namespaceURI is null it is not checked for equality, if the localName is null it is not checked for equality" — null은 **와일드카드**다. 무시 신호가 아니라 "이 축은 검사하지 마라"는 지시이며, 뒤집으면 비-null은 반드시 검사되어야 한다.
- 그리고 시그니처의 `@throws XMLStreamException if the required values are not matched` — 불일치의 보고 수단은 checked `XMLStreamException`이다.

수정 전 코드는 (C2)를 전면 위반하고, (C3)의 후반(비-null은 검사)을 위반한다.\
(C1)만 지켰다.\
위반의 형태가 "틀린 값을 돌려준다"가 아니라 "**어서션이 성공을 반환한다**"라는 점이 핵심이다 — 어서션이 무력화되면 아무 값도 흘러나오지 않고, 스택트레이스도 남지 않으며, 호출자는 확인했다고 믿는다.\
실제 실패는 훨씬 뒤 엉뚱한 자리에서 나타난다.

> **무음 실패 (silent failure)** — 잘못된 상태를 알려 주는 신호(예외·로그·틀린 반환값)가 하나도 남지 않은 채 진행되는 실패.\
> 예: 수정 전 `require(START_ELEMENT, null, "wrong")`은 예외도 로그도 없이 정상 반환한다.

같은 계약을 JDK 기본 스트림 리더는 정확히 지킨다.\
그러므로 이 어댑터는 **같은 인터페이스인데 다르게 행동한다** — 어댑터에서 가장 나쁜 종류의 계약 위반이다.

기존 테스트가 고정하던 것은 이 계약이 아니다.\
`XMLEventStreamReaderTests`의 `readAll`·`readCorrect`는 문서 전체를 훑어 변환 결과를 비교하는 통합형이고 `require()`를 부르지 않는다.\
base 기준 `require()`에 대한 테스트는 **0건**이었다.

## 5. 수정안

프로덕션 diff는 `AbstractXMLStreamReader.java`의 `require()` 한 메서드에 국한된다.

```java
// before (base 0c60266986:155-161)
	@Override
	public void require(int expectedType, String namespaceURI, String localName) throws XMLStreamException {
		int eventType = getEventType();
		if (eventType != expectedType) {
			throw new XMLStreamException("Expected [" + expectedType + "] but read [" + eventType + "]");
		}
	}

// after (refs/pr/36915:155-175)
	@Override
	public void require(int expectedType, @Nullable String namespaceURI, @Nullable String localName)
			throws XMLStreamException {

		int eventType = getEventType();
		if (eventType != expectedType) {
			throw new XMLStreamException("Expected [" + expectedType + "] but read [" + eventType + "]");
		}
		// This reader only exposes a name and namespace for START_ELEMENT and END_ELEMENT,
		// so a non-null namespace or local name can only ever match one of those events.
		if ((namespaceURI != null || localName != null) &&
				eventType != XMLStreamConstants.START_ELEMENT && eventType != XMLStreamConstants.END_ELEMENT) {
			throw new XMLStreamException("Current event is not a START_ELEMENT or END_ELEMENT");
		}
		if (localName != null && !localName.equals(getLocalName())) {
			throw new XMLStreamException("Expected local name [" + localName + "] but read [" + getLocalName() + "]");
		}
		if (namespaceURI != null && !namespaceURI.equals(getNamespaceURI())) {
			throw new XMLStreamException("Expected namespace [" + namespaceURI + "] but read [" + getNamespaceURI() + "]");
		}
	}
```

**왜 그 위치인가.**\
결함은 "다른 곳에서 계산된 잘못된 값이 흘러들어온" 것이 아니라 **이 메서드 본문에 코드가 없는** 것이다.\
따라서 수정 지점은 본문 그 자체 외에 선택지가 없다.\
검증에 필요한 접근자(`getLocalName()`·`getNamespaceURI()`)는 이미 같은 클래스에 있으므로 새 자료도, 새 필드도 필요 없다.

**블록 순서가 유일한 설계 판단이다.**\
타입 가드가 이름 비교보다 앞에 와야 하는 이유는 3절 세 번째 표가 보인 대로다 — `getLocalName()`이 스스로 방어하지 않으므로, 가드가 없으면 계약 위반이 `IllegalStateException`으로 새어 나가 "검증을 고쳤더니 다른 계약을 깼다"가 된다.\
`localName`을 `namespaceURI`보다 먼저 검사한 것은 이름 불일치가 대개 더 이해하기 쉬운 진단이기 때문이며, 계약상 순서 요구는 없다.

**검토한 대안과 기각 이유.**

첫째, `getLocalName()`에 `getNamespaceURI()`·`getPrefix()`와 같은 이벤트 타입 가드를 추가해 근본 비대칭을 없애는 안.\
이번 범위에서 **제외**했다.\
별개 결함이고, `getLocalName()`은 이 PR 밖에도 호출자가 있을 수 있으므로 예외 동작을 바꾸면 범위가 번진다.\
`docs/plans/2026-08-06/pr36915-scope-hardening/log.md`의 "이월 기록"에 별도 PR 후보로 남겼다.

둘째, `ENTITY_REFERENCE`에 대해서도 로컬 이름을 검증하는 안.\
스펙은 이를 허용하지만 이 어댑터는 엔티티 이름을 노출할 방법이 없다 — `getName()`(`XMLEventStreamReader.java:58-69`)이 요소 이벤트 밖에서는 예외를 던진다.\
"리더가 실제로 관측할 수 있는 범위 안에서 정직하게 만든다"는 경계를 택하고, PR 본문에 `## Note on scope`로 명시해 메인테이너가 다른 경계를 원하면 조정할 여지를 남겼다.

셋째, 가드 조건을 `hasName()`(`:115-119`)으로 대체하는 안.\
논리적으로 동일하나 채택하지 않았다 — `eventType` 지역변수를 이미 들고 있으므로 `getEventType()`를 다시 부를 이유가 없고, 조건을 인라인하면 "어느 두 타입을 허용하는가"가 그 줄에서 바로 읽힌다.

**테스트가 덮는 것과 덮지 않는 것.**\
추가된 테스트 `requireValidatesNamespaceAndLocalName`은 단언 5개를 담는다 — 양성 가드 3개(`null, "root"` / `"namespace", "root"` / `"namespace", null`)와 red 2개(이름 불일치, 네임스페이스 불일치).\
셋째 양성 가드가 (C3)의 null 와일드카드를 지키며, "localName이 null이면 불일치"로 잘못 조이는 과잉 수정을 배제한다.\
**덮지 않는 것은 이벤트 타입 가드 블록이다** — 비요소 이벤트에서 예외 **타입**이 `XMLStreamException`인지 확인하는 단언이 없어, 그 블록을 지워도 현재 테스트로는 잡히지 않는다.\
3절이 그 블록을 load-bearing으로 판정한 것에 비하면 비어 있는 자리다.\
`docs/plans/2026-08-06/pr36915-scope-hardening/`가 이 빈칸을 포함해 다섯 개를 식별하고 테스트 4종 추가 계획을 세웠으나, 사용자 판단으로 실행은 보류되었다.

## 6. 범위 밖과 인접 영향

**blast radius.**\
서브클래스는 `XMLEventStreamReader` 하나뿐이므로(`git grep "extends AbstractXMLStreamReader"`) 영향 범위는 `StaxUtils.createEventStreamReader`가 돌려주는 인스턴스로 닫혀 있다.

> **blast radius (영향 반경)** — 어떤 변경이 잘못됐을 때 피해가 미칠 수 있는 최대 범위.\
> 예: 여기서는 상속 대상이 `XMLEventStreamReader` 하나뿐이라 반경이 그 어댑터 인스턴스로 닫힌다.

**하위호환 — 이것이 이 PR의 논쟁점이다.**\
다른 두 PR과 달리 이 수정은 **이전에 성공하던 호출을 실패하게 만든다**.\
구체적으로 (a) 비-null 이름·네임스페이스가 실제와 다른 호출, (b) 비요소 이벤트에서 비-null 이름을 요구하는 호출이 이제 예외를 던진다.\
계약 관점에서는 둘 다 원래 예외여야 했던 호출이지만, 잘못된 어서션에 의존하던 코드가 있었다면 깨진다.\
정상 경로(값이 맞는 호출, null 와일드카드 호출)는 좁아지지 않으며 테스트의 양성 가드 3건이 그것을 고정한다.\
`docs/plans/2026-08-05/pr-backlog-triage/`의 판정이 이 PR을 "correctness fix가 아니라 동작 변경, 메인테이너 판단 필요"로 분류한 근거가 이 지점이다.

**같은 파일의 인접 결함 — PR #36914.**\
같은 클래스의 `getTextCharacters(int, char[], int, int)`(`:190-196`)가 `sourceStart`를 상한 계산에서 빠뜨리는 별건이 있고 별도 PR로 제출되어 있다.\
발견 당시 문서(`B3-...`, `B8-...`)는 "같은 파일이므로 JSR-173 계약 준수 묶음 PR"을 후보로 남겼으나 분리 제출을 택했다.

**아직 남아 있는 인접 결함 — `getLocalName()`의 가드 부재.**\
`AbstractXMLStreamReader`의 이름 관련 접근자 셋 중 `getNamespaceURI()`(`:80-89`)와 `getPrefix()`(`:104-113`)는 이벤트 타입 가드를 갖는데 `getLocalName()`(`:180-183`)만 없다.\
이번 수정은 `require()` 안에서 가드를 앞세워 우회했을 뿐 그 비대칭 자체는 그대로다.\
별도 PR 후보로 이월되어 있으며, 이번 PR에 포함하면 범위가 번져 정체 원인을 늘린다는 판단이었다.

**계약 관점에서 남은 항목.**\
`ENTITY_REFERENCE`의 로컬 이름 검증은 스펙이 허용하지만 이 어댑터가 관측할 수 없어 미구현이다.\
이 경계가 코드나 javadoc이 아니라 **PR 본문에만** 적혀 있다는 점은 리뷰어가 매번 같은 판단을 반복하게 만드는 구조적 약점이며, 스코프 하드닝 계획이 javadoc으로 못 박으려던 항목이 바로 이것이다(미실행).
