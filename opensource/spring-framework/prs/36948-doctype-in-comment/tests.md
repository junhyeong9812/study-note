# PR #36948 — 테스트 해설 (테스트 하나하나)

> PR #36948 테스트 해설. 형식·개념은 ../37153/tests.md, ../37153/guard-tests.md 참조.

이 PR의 테스트 변경은 새 `@Test` 메서드가 아니라 **파라미터 케이스 하나**다.
`XmlValidationModeDetectorTests`는 파일 이름 목록을 받아 각각의 기대 검증 모드를
확인하는 파라미터화된 구조이므로, 테스트를 추가한다는 것은 XML 픽스처 파일 하나와
`@ValueSource` 목록 한 줄을 더한다는 뜻이다. 성격은 red다. 이 문서는 그 한 케이스를
해설하고, 픽스처 XML이 흉내 내는 실제 상황과 나머지 목록 항목들이 맡는 가드 역할을
정리한다.

## 1. 여러 줄 주석 본문의 DOCTYPE — red

이 PR이 더한 것은 아래 `@ValueSource` 목록의 마지막 줄 하나이며, 그 한 줄이 결함을 재현하는 red 케이스다.

```java
@ParameterizedTest
@ValueSource(strings = {
	"xsdWithNoComments.xml",
	"xsdWithMultipleComments.xml",
	"xsdWithDoctypeInComment.xml",
	"xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml",
	"xsdWithDoctypeInMultiLineCommentBody.xml"
})
void xsdDetection(String fileName) throws Exception {
	assertValidationMode(fileName, VALIDATION_XSD);
}
```

그 한 케이스가 무엇을 주장하고 수정 전후로 어떻게 갈리는지를 네 항목으로 나눠 정리한다.

- **주장**: 마커 없는 주석 본문 줄에 `DOCTYPE`이라는 단어가 있어도 문서는 여전히
  `VALIDATION_XSD`로 판정된다.
- **fix 전 결과와 이유**: red다. 판별은 diff의 프로덕션 한 줄과 픽스처 파일의 구조로
  확정된다. 수정 전 `consumeCommentTokens`의 조기 반환은 다음과 같았다.

  ```java
  int indexOfStartComment = line.indexOf(START_COMMENT);
  if (indexOfStartComment == -1 && !line.contains(END_COMMENT)) {
      return line;
  }
  ```

  픽스처의 3행 `See the DOCTYPE notes for legacy configs`에는 `<!--`도 `-->`도 없으므로
  이 조건이 참이 되고, 그 시점 `this.inComment`가 `true`인데도 줄이 그대로 반환된다.
  검출 루프는 그 문자열을 내용으로 보고 `hasDoctype(content)`를 참으로 판정해
  `isDtdValidated = true`로 설정한 뒤 `break`한다. 반환값은 `VALIDATION_DTD`가 되어
  기대값 `VALIDATION_XSD`와 어긋난다. 예외가 아니라 정수 불일치로 실패하는 red다.
- **fix 후**: 조기 반환이 `return (this.inComment ? "" : line);`으로 바뀌어 주석 본문
  줄이 빈 문자열이 된다. 루프의 `if (!StringUtils.hasText(content)) continue;`가 그것을
  걸러 내므로 판정에 도달하지 않고, 4행에서 `-->`를 소비해 `inComment`가 `false`로
  돌아간 뒤 5행 `<beans ...`가 여는 태그로 잡혀 `VALIDATION_XSD`가 나온다.
- **주장이 성립하려면 세 조건이 동시에 필요하다**: 주석이 두 줄 이상에 걸칠 것,
  본문 줄에 마커가 없을 것, 그 줄에 `DOCTYPE`이라는 문자열이 있을 것. 이 조합이
  gh-27915가 남긴 잔여 사례이며, 픽스처는 그 세 조건을 정확히 만족하도록 설계되었다.

## 2. 픽스처 XML이 흉내 내는 실제 상황

픽스처는 결함을 유도하려고 비튼 구조가 아니라 실사용 설정 파일의 가장 평범한 모양이다. 파일 전문은 다음과 같다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
	See the DOCTYPE notes for legacy configs
-->
<beans xmlns="http://www.springframework.org/schema/beans"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="https://www.springframework.org/schema/beans
		https://www.springframework.org/schema/beans/spring-beans.xsd">

</beans>
```

이 테스트에는 목이 없다. 흉내 내는 대상이 협력 객체가 아니라 **입력 문서**이기 때문이고,
그래서 시뮬레이션은 XML 파일 하나로 이루어진다. 검출기 자체는 실제 인스턴스를 그대로
쓴다.

파일이 흉내 내는 것은 이 결함이 걸릴 법한 가장 평범한 실사용 설정 파일이다. 세 가지
디테일이 그 현실성을 만든다.

첫째, 주석이 헤더 주석의 관용적 형태를 따른다. `<!--`가 한 줄을 독차지하고, 다음 줄에
설명이 오고, `-->`가 다시 한 줄을 차지한다. 이것은 실제 설정 파일에서 가장 흔한 여러 줄
주석 모양이며, 특별히 결함을 유도하기 위해 비튼 구조가 아니다.

둘째, `DOCTYPE`이 선언이 아니라 **산문 속 단어**로 등장한다. "See the DOCTYPE notes for
legacy configs"는 XSD로 이관하면서 옛 DTD 설정에 대한 안내를 남겨 두는, 충분히 있을 법한
문장이다. 이것이 함정의 핵심인데, `hasDoctype`은 `content.contains(DOCTYPE)`일 뿐이라
`<!DOCTYPE` 형태의 진짜 선언이 아니어도 걸린다.

셋째, 본문이 진짜 XSD 설정이다. `xmlns`, `xmlns:xsi`, `xsi:schemaLocation`을 갖춘 정상적인
`<beans>` 루트를 두었으므로, 이 파일은 "DTD로 오판되면 실제로 기동이 깨지는" 문서다.
오판의 대가가 조용한 성능 저하가 아니라 기동 실패라는 점 — XSD 문서를 DTD 모드로
파싱하면 파서가 검증 오류를 보고하고 그것이 `BeanDefinitionStoreException`으로 올라간다는
점 — 이 픽스처에 반영되어 있다.

파일명 `xsdWithDoctypeInMultiLineCommentBody.xml`도 정보를 담는다. 기존 픽스처
`xsdWithDoctypeInComment.xml`과 `xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`이
쓰던 명명 관용구를 따르면서, `MultiLineCommentBody`라는 부분이 이번 사례를 기존 사례와
구별한다.

## 3. 검증 헬퍼

파라미터 케이스가 실제로 무엇을 재는지는 공통 헬퍼 하나에 고정되어 있다.

```java
private void assertValidationMode(String fileName, int expectedValidationMode) throws IOException {
	try (InputStream inputStream = getClass().getResourceAsStream(fileName)) {
		assertThat(xmlValidationModeDetector.detectValidationMode(inputStream))
			.as("Validation Mode")
			.isEqualTo(expectedValidationMode);
	}
}
```

이 PR은 헬퍼를 건드리지 않았다. 그러나 새 케이스가 무엇을 재는지 이해하려면 이 헬퍼를
읽어야 한다. 검증 대상은 `detectValidationMode(InputStream)`이 돌려주는 정수 하나이고,
그것이 곧 파서 구성 방식을 결정한다. 파일은 클래스패스 리소스로 읽히므로 픽스처 XML은
테스트 클래스와 같은 패키지 경로
(`spring-core/src/test/resources/org/springframework/util/xml/`)에 놓인다.

검출기 인스턴스가 필드로 공유된다는 점도 짚어 둘 만하다.

```java
private final XmlValidationModeDetector xmlValidationModeDetector = new XmlValidationModeDetector();
```

`inComment`는 이 인스턴스의 필드이므로 케이스 간 오염이 우려될 수 있으나,
`detectValidationMode`가 진입 즉시 `this.inComment = false;`로 초기화한다. JUnit이 각
테스트마다 인스턴스를 새로 만드는 것과 별개로, 검출기 자체가 상태를 리셋하므로 파라미터
케이스들은 서로 독립적이다.

## 4. 가드는 기존 목록 항목들이 맡는다

이 PR은 새 가드를 만들지 않았다. 대신 두 `@ValueSource` 목록에 이미 있던 항목 전부가
가드 역할을 한다. `xsdWithNoComments.xml`, `xsdWithMultipleComments.xml`,
`xsdWithDoctypeInComment.xml`,
`xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`, 그리고 `dtdDetection`
쪽의 `dtdWithNoComments.xml`, `dtdWithLeadingComment.xml`,
`dtdWithTrailingComment.xml`, `dtdWithTrailingCommentAcrossMultipleLines.xml`,
`dtdWithCommentOnNextLine.xml`, `dtdWithMultipleComments.xml`이 그것이다.

이들이 수정 전후로 모두 green인 이유는 삼항식의 구조가 보장한다. `this.inComment`가
`false`인 모든 호출에서 `(this.inComment ? "" : line)`은 `line`으로 평가되며, 이는 수정
전 표현식과 문자 그대로 동일하다. 즉 관측 가능한 차이가 생기는 경우는
`inComment == true`인 조기 반환 경로 하나뿐이고, 그 경로가 바로 결함이 살던 자리다.
기존 항목들이 green을 유지한다는 사실이 그 논증을 실행으로 확인해 준다.

가드 중에서도 `dtdDetection` 쪽 항목들이 특히 중요하다. 이 수정의 과잉 형태는 분명히
상상 가능한데, 무시 규칙을 너무 넓게 적용해 **진짜** `<!DOCTYPE` 선언까지 놓치는 것이다.
DTD 목록이 통과한다는 것은 그런 과잉이 일어나지 않았다는 뜻이다.

## 5. 머지 후 보강

머지 시 Sam Brannen이 후속 커밋 `4074155d76a`("Polish contribution")로 픽스처 두 개를
더 보탰고, 현재 저장소의 테스트 파일에는 그 결과가 반영되어 있다. 세 픽스처가 각각
무엇을 고정하는지 비교하면 커버리지 의도가 드러난다.

| 픽스처 | 기대값 | 고정하는 명제 | 성격 |
|---|---|---|---|
| `xsdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 주석 본문의 `DOCTYPE`은 무시된다 | red (이 PR) |
| `xsdWithMultipleDoctypesInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 본문 줄이 여러 개여도, `DOCTYPE`이 여러 번 나와도 무시된다 | 보강 |
| `dtdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_DTD` | 주석을 지나 등장하는 진짜 선언은 여전히 검출된다 | 음성 가드 |

세 번째가 앞 절에서 말한 과잉 수정 방지를 한 파일 안에서 직접 겨눈다. 3행의 `DOCTYPE`은
무시되어야 하고 5행의 진짜 선언은 잡혀야 하므로, 두 요구가 동시에 검증된다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
	DOCTYPE
-->
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN 2.0//EN" "https://www.springframework.org/dtd/spring-beans-2.0.dtd">
<beans>

</beans>
```

이 파일이 이 PR 시점에 없었다는 사실은 그 자체로 남겨 둘 만한 관찰이다. 원 PR은 red
케이스 하나만 추가했고, 반대 방향 음성 가드는 메인테이너가 채웠다. #37153에서
음성 가드를 리뷰 단계에서 채택한 것과 비교하면, 같은 종류의 빈 칸을 누가 언제 채우느냐의
차이가 보인다.

## 실측과 역할 요약

이 PR의 테스트 변경을 실측 기록·구성·특징 세 항목으로 요약한다.

- 실측 기록: PR 본문은 회귀 픽스처를 기존 파라미터화 테스트에 추가했다고만 적었고 실행
  결과 수치는 남기지 않았다. 총 테스트 수나 수정 전 실패 건수는 판별 근거 부족으로
  남긴다.
- 이 PR이 추가한 것은 red 1케이스(파라미터 케이스 + 픽스처 파일 1개). 이 PR이 추가한
  가드는 0건이며, 보존 증명은 기존 목록 항목 열 건이 맡는다.
- 테스트 형태가 데이터 주도라는 점이 이 파일의 특징이다. 검증 로직은 헬퍼 하나에
  고정되어 있고, 새 사례를 추가하는 비용이 "XML 파일 하나 + 목록 한 줄"로 낮다. 그
  낮은 비용이 폴리시 커밋에서 픽스처 두 개가 곧바로 보강될 수 있었던 이유이기도 하다.
