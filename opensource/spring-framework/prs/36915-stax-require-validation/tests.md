# PR #36915 — 테스트 해설 (테스트 하나하나)

> PR #36915 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `XMLEventStreamReaderTests`에 하나이고, 헬퍼가 하나 딸린다.\
테스트 메서드는 하나지만 그 안에 다섯 개의 호출이 들어 있고, 앞의 셋은 수정 전에도 통과하는 가드, 뒤의 둘은 수정 전에 반드시 실패하는 red다.\
즉 **한 메서드 안에 가드와 red가 함께 배치**된 형태다.

> **red 단언** — 수정 전 코드에서 반드시 실패하도록 설계한 단언. 결함이 실제로 존재함을 테스트가 재현한다는 뜻이다.\
> 예: `require(START_ELEMENT, null, "wrong")`이 예외를 던지는지 보는 두 줄은 수정 전에는 예외가 없어 실패한다.

> **양성 가드 (positive guard)** — 수정 전후 모두 통과해야 하는 단언. 새 검증이 정상 경로까지 막아 버리지 않았음을 고정한다.\
> 예: `require(START_ELEMENT, "namespace", null)`은 값이 맞는 호출이므로 수정 후에도 예외가 없어야 한다.

## 1. require의 이름·네임스페이스 검증 — red (가드 단언 3 + red 단언 2)

유일한 테스트 메서드는 맞는 조합 세 호출과 틀린 조합 두 호출을 한 자리에 모아, 계약의 세 규칙을 한 번에 못 박는다.

```java
@Test  // require(type, namespaceURI, localName) must validate the name and namespace
void requireValidatesNamespaceAndLocalName() throws Exception {
	advanceToStartElement("root");

	streamReader.require(XMLStreamConstants.START_ELEMENT, null, "root");
	streamReader.require(XMLStreamConstants.START_ELEMENT, "namespace", "root");
	streamReader.require(XMLStreamConstants.START_ELEMENT, "namespace", null);

	assertThatExceptionOfType(XMLStreamException.class).isThrownBy(() ->
			streamReader.require(XMLStreamConstants.START_ELEMENT, null, "wrong"));
	assertThatExceptionOfType(XMLStreamException.class).isThrownBy(() ->
			streamReader.require(XMLStreamConstants.START_ELEMENT, "wrong-namespace", "root"));
}
```

전체 주장은 하나다.\
`require`는 이벤트 타입만이 아니라 비-null로 넘어온 `localName`과 `namespaceURI`를 실제로 대조해야 하며, null 인자는 와일드카드로 건너뛴다.

다섯 호출이 인자 조합으로 어떤 축을 시험하는지 나란히 놓으면 설계가 보인다.\
커서는 다섯 호출 모두 `{namespace}root`의 START_ELEMENT에 있다.

```text
인자 (namespaceURI, localName)     시험하는 축              fix 전     fix 후
---------------------------------  ----------------------  ---------  ---------
(null, "root")                     이름만 대조              통과       통과
("namespace", "root")              이름 + 네임스페이스      통과       통과
("namespace", null)                네임스페이스만 대조      통과       통과
(null, "wrong")                    이름 불일치만 격리       통과       예외
("wrong-namespace", "root")        네임스페이스 불일치만    통과       예외
```

`fix 전` 열이 다섯 줄 모두 "통과"인 것이 결함 그 자체다.

### 앞의 세 호출 — 항상 green (양성 가드)

앞의 세 호출은 수정 전후 모두 통과하지만 통과하는 이유가 다르고, 그 차이가 이 세 줄의 존재 이유다.

- **주장**: 값이 맞는 경우 세 조합 모두 통과한다. 이름만 준 경우, 이름과 네임스페이스를
  모두 준 경우, 네임스페이스만 준 경우다.
- **단언 형태**: `assertThat`이 없다. 예외를 던지면 테스트가 실패하므로 **호출 자체가
  단언**이다. 37153의 `validateWhenDoesNotHave...ThrowsNothing`과 같은 형태다.
- **fix 전 green인 이유**: 수정 전 `require`는 타입만 비교하고 끝났으므로 이름·네임스페이스
  인자가 무엇이든 통과했다. 즉 이 세 줄은 수정 전에는 "아무것도 검사하지 않아서" 통과했고,
  수정 후에는 "검사했는데 실제로 맞아서" 통과한다. 같은 green이지만 의미가 완전히 다르다.
- **존재 이유는 fix 후**: 새로 넣은 검증이 정상 경로를 좁히지 않았음을 고정한다. 특히
  셋째 호출(`"namespace", null`)이 중요하다. 계약의 null 와일드카드 규칙을 지키지 않고
  "localName이 null이면 불일치"로 잘못 조이는 수정이 있었다면 이 줄에서 걸린다. 과잉
  필터링 방지의 자리다.

### 뒤의 두 단언 — red

뒤의 두 단언이 실제 회귀 방어선이며, 이름과 네임스페이스를 각각 하나씩만 어긋나게 한 대조 설계다.

- **주장**: 이름이 다르면(`"wrong"`) 그리고 네임스페이스가 다르면(`"wrong-namespace"`)
  각각 `XMLStreamException`이 던져진다.
- **fix 전**: 두 호출 모두 조용히 통과하므로 `isThrownBy`가 "예외가 던져지지 않았다"로
  실패한다. 두 줄 다 red다.
- **두 줄로 나눈 이유**: 검증 대상이 서로 다른 필드이고 수정에서도 서로 다른 if 블록이
  담당하기 때문이다. 한 줄로 합쳐 `require(START_ELEMENT, "wrong-namespace", "wrong")`을
  던졌다면, localName 검사만 구현하고 namespace 검사를 빠뜨린 절반 수정도 통과한다.
  실제 수정 코드에서 localName 검사가 namespace 검사보다 먼저 오므로 그 위험은 실재한다.
- **첫 red가 `null, "wrong"`인 점**: 네임스페이스를 null로 두어 이름 불일치만 격리한다.
  둘째 red는 반대로 이름을 맞는 값 `"root"`로 두어 네임스페이스 불일치만 격리한다.
  두 줄이 각각 변수 하나씩만 어긋나게 하는 대조 설계다.

### 이 테스트가 다루지 않은 경계

수정 본문에는 세 번째 방어선이 하나 더 있다.\
요소 이벤트가 아닌 상태에서 비-null 이름이 들어오면 `IllegalStateException` 대신 `XMLStreamException`으로 보고하는 가드다.

```java
if ((namespaceURI != null || localName != null) &&
		eventType != XMLStreamConstants.START_ELEMENT && eventType != XMLStreamConstants.END_ELEMENT) {
	throw new XMLStreamException("Current event is not a START_ELEMENT or END_ELEMENT");
}
```

테스트는 이 경로를 밟지 않는다.\
`require(COMMENT, null, "x")` 같은 호출로 예외 **타입**이 `XMLStreamException`인지 확인하는 단언이 없기 때문이다.\
이 가드가 지워지면 해당 호출은 계약 위반인 `IllegalStateException`으로 새어 나가는데, 현재 테스트로는 잡히지 않는다.\
README가 이 가드를 "이 수정의 핵심 판단"으로 지목한 것에 비하면 검증이 비어 있는 자리이고, 37153에서 리뷰 open question으로 음성 가드가 추가된 것과 같은 종류의 보강 여지다.

## 2. 헬퍼 — 커서를 특정 시작 요소로 전진

테스트가 검증에만 집중할 수 있도록, 커서를 이름으로 지정한 시작 요소까지 옮기는 일은 헬퍼가 맡는다.

```java
private void advanceToStartElement(String localName) throws Exception {
	while (streamReader.getEventType() != XMLStreamConstants.START_ELEMENT ||
			!streamReader.getLocalName().equals(localName)) {
		streamReader.next();
	}
}
```

픽스처 문서에서 이 루프가 실제로 밟는 자리를 세로로 펴면 이렇다.

```text
커서 시작 (생성자 직후)    START_DOCUMENT
        |                  왼쪽 조건 참 -> getLocalName() 호출 안 함 -> next()
        v
next() 1회                 PROCESSING_INSTRUCTION  (<?pi content?>)
        |                  왼쪽 조건 참 -> getLocalName() 호출 안 함 -> next()
        v
next() 2회                 START_ELEMENT root
        |                  왼쪽 조건 거짓 -> 오른쪽 평가 -> "root".equals("root")
        v
루프 종료                  커서가 {namespace}root 에 놓인 채 테스트 본문 시작
```

- **역할**: 문서 앞머리의 START_DOCUMENT와 처리 명령(`<?pi content?>`)을 지나 `root`
  시작 태그에 커서를 놓는다.
- **조건식 순서가 곧 계약 지식이다**: `getEventType()` 검사를 `||`의 왼쪽에 둔 것은
  단락 평가를 노린 배치다. 요소 이벤트가 아니면 오른쪽 `getLocalName()`을 아예 호출하지
  않는다. 호출했다면 `getName()`이 요소 이벤트 밖에서 `IllegalStateException`을 던지므로
  헬퍼가 먼저 터진다. 수정 본문에서 이벤트 타입 가드를 이름 비교보다 앞에 둔 것과 정확히
  같은 이유이고, 테스트 코드가 그 설계 제약을 두 번째로 실증하는 셈이다.
- **이름으로 조건을 건 이유**: 이 XML에는 시작 요소가 둘(`root`, `prefix:child`)이라,
  단순히 "첫 START_ELEMENT"로 멈추면 어느 쪽인지 코드만 봐서는 확신할 수 없다. 이름을
  인자로 받아 의도를 명시했다.

## fixture

이 PR도 새 fixture를 만들지 않고 클래스의 기존 것을 그대로 쓴다.

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

> **fixture (픽스처)** — 모든 테스트가 같은 출발 상태에서 시작하도록 미리 준비해 두는 입력·객체.\
> 예: `@BeforeEach`가 매 테스트 전에 같은 XML 문자열로 `XMLEventStreamReader`를 새로 만든다.

이 XML이 이번 테스트에 적합한 이유는 **기본 네임스페이스가 실제로 붙어 있기** 때문이다.\
`root`에 `xmlns='namespace'`가 선언돼 있어 `getNamespaceURI()`가 빈 문자열이 아닌 값을 돌려주고, 그래야 `"wrong-namespace"`와의 불일치가 의미 있는 대조가 된다.\
네임스페이스가 없는 문서였다면 네임스페이스 검증을 제대로 시험할 수 없다.

fixture가 흉내 내는 실제 상황은 **공개 진입점으로 얻은 어댑터를 표준 인터페이스로 쓰는 외부 코드**다.\
`StaxUtils.createEventStreamReader(XMLEventReader)`가 반환하는 것이 이 `XMLEventStreamReader`이고, 그 외부 코드는 `XMLStreamReader` javadoc이 약속한 대로 `require`를 어서션으로 쓸 권리가 있다.\
저장소 안에는 `require` 호출처가 하나도 없으므로, 이 테스트가 그 사각지대에 놓인 첫 호출자 역할을 대신한다.\
mock이 없는 것도 같은 이유다 — 검증 대상이 협력자와의 상호작용이 아니라 실제 파싱된 이벤트의 이름·네임스페이스이므로, JDK 표준 파서로 진짜 문서를 읽어야 한다.

## 실측·역할 요약

fix 전 기준으로 단언 단위로 정리하면 다음과 같다.

| 단언 | 분류 | fix 전 결과 |
|---|---|---|
| `require(START_ELEMENT, null, "root")` | 양성 가드 | 통과(검사 안 함) |
| `require(START_ELEMENT, "namespace", "root")` | 양성 가드 | 통과(검사 안 함) |
| `require(START_ELEMENT, "namespace", null)` | 양성 가드 | 통과(검사 안 함) |
| 이름 불일치 -> `XMLStreamException` | red | 예외 없음으로 실패 |
| 네임스페이스 불일치 -> `XMLStreamException` | red | 예외 없음으로 실패 |

테스트 메서드 단위로는 1건이며, 수정 전 실행하면 넷째 단언에서 실패한다.

역할은 두 겹이다.\
red 두 줄이 "비-null 이름·네임스페이스가 조용히 통과했다"는 결함을 필드별로 재현하고, 가드 세 줄이 null 와일드카드 규칙을 포함한 정상 경로가 좁아지지 않았음을 고정한다.\
여기에 기존 테스트 `readAll`과 `readCorrect`가 일반 읽기·변환 경로의 무회귀를 계속 지킨다.\
다만 이벤트 타입 가드(비요소 이벤트에서의 예외 타입)는 현재 테스트가 덮지 않는 빈칸으로 남아 있다.
