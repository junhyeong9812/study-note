# PR #37008 — 테스트 해설 (테스트 하나하나)

> PR #37008 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR이 추가한 테스트는 `MimeTypeTests`의 중첩 클래스 `InvalidMimeTypeTests`에 들어간
한 건이고, 그 한 건은 수정 전에 실패하는 red 테스트다. 새 가드 테스트는 추가되지
않았으며, 보존해야 할 동작은 같은 파일에 이미 있던 정확 중복 테스트와 따옴표·다중
파라미터 테스트들이 지킨다. 배치도 의도적이어서, 새 테스트가 기존
`valueOfDuplicateParameter` 바로 아래에 놓여 둘이 같은 규칙의 두 사례임을 코드 순서로
드러낸다.

## 1. valueOfDuplicateParameterWithDifferentCase — red

이 PR이 추가한 유일한 테스트는 케이스만 다른 중복 파라미터가 예외로 거부되는지를 본다.

```java
@Test
void valueOfDuplicateParameterWithDifferentCase() {
	assertThatThrownBy(() -> MimeType.valueOf("text/plain;dupe=\"1\";DUPE=\"2\"")).isInstanceOf(InvalidMimeTypeException.class)
			.hasMessageContaining("Invalid mime type \"text/plain;dupe=\"1\";DUPE=\"2\"\": duplicate parameter 'DUPE=\"2\"'");
}
```

- **주장**: 대소문자만 다른 중복 파라미터(`dupe`와 `DUPE`)는 정확 중복과 똑같이
  거부되어야 하며, 예외 타입은 `InvalidMimeTypeException`이고, 메시지에는 원본 입력
  문자열과 문제가 된 파라미터가 **원래 대소문자 그대로** 들어가야 한다.

- **fix 전 결과와 이유**: red다. `MimeTypeParser.putParameter`가 누산 맵으로
  `LinkedHashMap`을 쓰는데, `LinkedHashMap`은 `dupe`와 `DUPE`를 서로 다른 키로 본다.
  따라서 두 번째 `put`이 이전 값이 아니라 null을 반환하고, `!= null` 검사가 통과하지
  못해 예외가 던져지지 않는다. 파싱은 성공하고 마지막 값 `"2"`만 조용히 남는다.
  `assertThatThrownBy`는 예외가 아예 없으면 실패하므로 첫 단언에서 깨진다. 결함이
  "잘못된 예외"가 아니라 **예외 부재**라는 점이 중요하다. 조용한 데이터 손실이라
  단언 없이는 관측되지 않는다.

- **fix 후**: 누산 맵이 `new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)`로 바뀌면서
  `DUPE`가 `dupe`와 같은 키로 취급되고, `put`이 이전 값 `"1"`을 반환해 기존 검사가
  그대로 발동한다. 검사 로직은 한 글자도 바뀌지 않았고 자료구조만 바뀌었다는 점이
  진단의 결과다. 규칙이 누산 맵과 결과 맵 두 곳에 각각 구현돼 있었고 한쪽만 옳았으므로,
  새 검사를 더하는 대신 옳은 쪽에 나머지를 맞춘 것이다.

- **메시지 단언이 따로 있는 이유**: 이 테스트는 "던지는가"에서 멈추지 않고 메시지에
  `DUPE="2"`가 대문자 그대로 들어가는지까지 본다. `LinkedCaseInsensitiveMap`은 비교만
  대소문자 무시로 하고 키의 원래 표기는 보존하므로, 예외 메시지가 `dupe="2"`로
  정규화돼 나오지 않는다. 진단 메시지가 사용자가 실제로 보낸 문자열을 그대로 보여줘야
  쓸모가 있으므로, 이 단언은 자료구조 교체의 부작용이 진단 품질을 떨어뜨리지 않았음을
  고정한다. 예외 타입 단언 역시 호출자가 잡던 타입이 바뀌지 않았음을 뜻한다.

- **fixture와 mock**: 없다. 입력이 MIME 타입 문자열 리터럴 하나이고 검증 대상이
  순수 파서이므로 대체물이 필요 없다. `text/plain;dupe="1";DUPE="2"`가 흉내 내는
  실제 상황은 HTTP `Content-Type`이나 `Accept` 헤더에서 클라이언트가 같은 파라미터를
  대소문자만 바꿔 두 번 보내는 경우다. `charset`과 `CHARSET`이 대표적인데, 테스트가
  실제 파라미터 이름 대신 `dupe`라는 중립적인 이름을 쓴 것은 바로 위 정확 중복
  테스트와 이름을 맞춰 두 케이스의 유일한 차이가 대소문자임을 드러내기 위해서다.
  따옴표 값(`"1"`, `"2"`)도 같은 이유로 기존 테스트에서 그대로 가져왔다.

## 2. 보존 동작은 기존 테스트가 지킨다

새 가드 테스트는 없다. 이 수정이 깨뜨릴 수 있는 것은 두 방향인데, 둘 다 기존
테스트가 담당한다.

첫째 방향은 정확 중복이 여전히 거부되는가다. 바로 위 테스트가 지킨다.

```java
@Test
void valueOfDuplicateParameter() {
	assertThatThrownBy(() -> MimeType.valueOf("text/plain;dupe=\"1\";dupe=\"2\"")).isInstanceOf(InvalidMimeTypeException.class)
			.hasMessageContaining("Invalid mime type \"text/plain;dupe=\"1\";dupe=\"2\"\": duplicate parameter 'dupe=\"2\"'");
}
```

- **fix 전후 모두 green**: `LinkedHashMap`도 `LinkedCaseInsensitiveMap`도 완전히
  동일한 키에 대해서는 이전 값을 반환하므로 검사가 똑같이 발동한다. gh-36841이 도입한
  이 계약이 이번 자료구조 교체로 흔들리지 않았음을 이 테스트가 그대로 증명한다.

둘째 방향은 정상 입력이 깨지지 않는가다. 같은 파일의 `parseQuotedCharset`,
`parseQuotedParameterValue` 같은 따옴표·다중 파라미터 케이스들이 담당한다. 이들이
계속 통과해야 "누산 맵 교체가 키 표기와 삽입 순서를 보존한다"는 논거가 실증된다.
`LinkedCaseInsensitiveMap`은 이름 그대로 삽입 순서를 유지하고 원래 표기를 보존하므로
중복이 아닌 입력에서는 이전과 구별되지 않는다. 최종 `MimeType`도 영향을 받지 않는데,
생성자가 파라미터를 자기 `LinkedCaseInsensitiveMap`으로 다시 복사하기 때문이다.
바뀐 것은 오직 중복 탐지의 민감도다.

## 이 테스트가 동시에 문서화하는 동작 변경

주의할 점은 이것이 순수한 버그 수정이 아니라 **파싱 동작 변경**이라는 사실이다. 아래는
같은 두 입력이 수정 전후에 어떻게 갈리는지다.

| 입력 | 수정 전 | 수정 후 |
| --- | --- | --- |
| `text/plain;dupe="1";dupe="2"` | 거부 | 거부 |
| `text/plain;dupe="1";DUPE="2"` | 통과, `"2"`만 남음 | 거부 |

두 번째 행이 이 PR이 바꾼 전부다. 대소문자가 다른 중복 파라미터를 보내던 클라이언트는
이제 성공 대신 예외를 받으므로, 새 테스트는 회귀 방지인 동시에 그 계약 변경을 명시하는
문서 역할을 한다. PR 본문에 "Note on impact" 절이 따로 있는 이유이며, 근거는 MIME
파라미터 이름이 대소문자 무시라는 RFC 2045와 중복 파라미터를 오류로 보는 RFC 6838
4.3절이다.

## 실측·역할 요약

PR이 아직 OPEN이므로 이 테스트는 업스트림 코드에 반영되지 않았고, 로컬
`MimeTypeTests`에는 `valueOfDuplicateParameter`까지만 있다. 위 코드는 PR diff의
최종 상태에서 옮긴 것이다.

역할을 한 줄로 정리하면, 새 한 건은 "대소문자만 다른 중복도 같은 중복이다"를 red로
고정하고, 바로 위 기존 한 건은 "정확 중복 거부는 그대로다"를 green으로 유지하며, 파일
전체의 정상 파싱 테스트들이 "무해한 입력은 건드리지 않았다"를 받쳐 준다. 검사 로직이
아니라 자료구조 한 줄이 바뀐 수정이므로, 테스트도 검사의 존재가 아니라 검사가 발동하는
경계가 어디까지 넓어졌는지를 겨눈다.
