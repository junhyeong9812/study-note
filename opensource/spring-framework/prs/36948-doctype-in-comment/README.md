# PR #36948 — Ignore DOCTYPE inside a multi-line comment body

## 0. 정향

이 PR은 `XmlValidationModeDetector`가 여러 줄짜리 XML 주석 **본문**에 들어 있는 `DOCTYPE`이라는 단어를 실제 DTD 선언으로 오인하던 버그를 고친다. 고친 코드는 단 한 줄이지만, 그 한 줄이 서 있는 자리를 이해하려면 Spring이 XML 설정 파일을 읽기 직전에 무엇을 하는지부터 알아야 한다. 이 문서는 검출기의 정체와 호출 경로에서 출발해, 수정 전 상태 추적 로직을 한 줄씩 따라가고, 오탐이 발생하는 지점을 재현한 뒤, 수정과 검증을 설명한다.

핵심 파일은 `spring-core/src/main/java/org/springframework/util/xml/XmlValidationModeDetector.java` 하나다. 커밋은 `1277279527c`로 `main`과 `7.0.x`에 반영되었다.

---

## 1. 배경 — 이 검출기는 무엇인가

`XmlValidationModeDetector`는 XML 문서를 **본격적으로 파싱하기 전에** 앞부분만 훔쳐보고 검증 방식을 결정하는 작은 스캐너다. XML에는 두 가지 스키마 체계가 공존한다. 하나는 문서 상단의 `<!DOCTYPE ...>` 선언으로 DTD를 가리키는 옛 방식이고, 다른 하나는 루트 태그의 `xsi:schemaLocation` 속성으로 XSD를 가리키는 현대 방식이다. JAXP의 `DocumentBuilderFactory`는 이 둘을 자동으로 구분해 주지 않는다. 검증을 켜려면 **어느 쪽인지 미리 알려줘야** 한다.

그래서 Spring은 파일을 두 번 읽는다. 첫 번째 읽기가 이 검출기이고, 여기서 나온 결론에 따라 파서를 구성한 뒤 두 번째 읽기에서 실제 DOM을 만든다. 검출기의 판별 기준은 지극히 단순하다. 의미 있는 첫 내용 안에 `DOCTYPE`이라는 토큰이 보이면 DTD, 안 보인 채로 여는 태그(`<beans` 같은 것)에 도달하면 XSD다. 클래스가 내보내는 상수 네 개가 그 결과를 표현한다.

```java
public static final int VALIDATION_NONE = 0;
public static final int VALIDATION_AUTO = 1;
public static final int VALIDATION_DTD = 2;
public static final int VALIDATION_XSD = 3;
```

호출 경로는 `spring-beans`의 XML 설정 로딩 파이프라인이다. `XmlBeanDefinitionReader`가 검출기 인스턴스를 필드로 하나 들고 있고(`private final XmlValidationModeDetector validationModeDetector = new XmlValidationModeDetector();`), 사용자가 검증 모드를 명시하지 않아 `VALIDATION_AUTO`로 남아 있을 때만 검출을 수행한다.

```java
protected int getValidationModeForResource(Resource resource) {
	int validationModeToUse = getValidationMode();
	if (validationModeToUse != VALIDATION_AUTO) {
		return validationModeToUse;
	}
	int detectedMode = detectValidationMode(resource);
	if (detectedMode != VALIDATION_AUTO) {
		return detectedMode;
	}
	// Hmm, we didn't get a clear indication... Let's assume XSD,
	// since apparently no DTD declaration has been found up until
	// detection stopped (before finding the document's root tag).
	return VALIDATION_XSD;
}
```

여기서 나온 정수는 `DefaultDocumentLoader.createDocumentBuilderFactory(int, boolean)`로 흘러가 파서 설정을 결정한다. XSD로 판정되면 네임스페이스 인식을 강제하고 스키마 언어 속성을 심는 반면, DTD로 판정되면 `setValidating(true)`만 켜고 스키마 관련 설정은 하지 않는다.

```java
if (validationMode != XmlValidationModeDetector.VALIDATION_NONE) {
	factory.setValidating(true);
	if (validationMode == XmlValidationModeDetector.VALIDATION_XSD) {
		// Enforce namespace aware for XSD...
		factory.setNamespaceAware(true);
		try {
			factory.setAttribute(SCHEMA_LANGUAGE_ATTRIBUTE, XSD_SCHEMA_LANGUAGE);
		}
```

**오판의 대가는 조용한 성능 저하가 아니라 기동 실패다.** XSD 문서를 DTD 모드로 파싱하면 파서는 DTD 문법을 기대하는데 문서에 `DOCTYPE`이 없으므로 검증 오류를 보고한다. `XmlBeanDefinitionReader`의 기본 오류 처리기인 `SimpleSaxErrorHandler`는 `error(SAXParseException)`에서 예외를 그대로 다시 던지므로, 이 오류는 삼켜지지 않고 `BeanDefinitionStoreException`으로 올라가 컨텍스트 기동을 중단시킨다.

XXE(XML External Entity) 맥락도 짚어 둘 필요가 있는데, 오해를 피하려면 정확히 구분해야 한다. **이 검출기는 XXE 방어 장치가 아니다.** `DOCTYPE`을 찾는 목적은 외부 엔티티를 차단하려는 것이 아니라 검증 문법을 고르려는 것이다. Spring은 이 로더에 대한 XXE 위험 판단을 소스 주석으로 명시해 두었다.

```java
// This document loader is used for loading application configuration files.
// As a result, attackers would need complete write access to application configuration
// to leverage XXE attacks. This does not qualify as privilege escalation.
```

다만 `DOCTYPE` 문자열의 존재 여부가 파서 구성 방식을 바꾼다는 점에서, 검출기의 판정이 신뢰할 수 있어야 한다는 요구는 그대로다. 이 PR이 고치는 것은 그 신뢰성이다.

---

## 2. 수정 전 동작 방식 — 상태 추적 로직

검출기의 본체는 한 줄씩 읽는 루프이며, 각 줄에서 주석을 걷어낸 나머지만 판정에 쓴다. 진입점 `detectValidationMode(InputStream)`의 골격은 다음과 같다.

```java
public int detectValidationMode(InputStream inputStream) throws IOException {
	this.inComment = false;

	// Peek into the file to look for DOCTYPE.
	try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
		boolean isDtdValidated = false;
		String content;
		while ((content = reader.readLine()) != null) {
			content = consumeCommentTokens(content);
			if (!StringUtils.hasText(content)) {
				continue;
			}
			if (hasDoctype(content)) {
				isDtdValidated = true;
				break;
			}
			if (hasOpeningTag(content)) {
				// End of meaningful data...
				break;
			}
		}
		return (isDtdValidated ? VALIDATION_DTD : VALIDATION_XSD);
	}
	catch (CharConversionException ex) {
		// Choked on some character encoding...
		// Leave the decision up to the caller.
		return VALIDATION_AUTO;
	}
}
```

루프의 계약은 명확하다. `consumeCommentTokens`가 주석을 제거한 **내용만** 돌려주고, 그 내용이 공백이면 건너뛰며, 내용이 있으면 `DOCTYPE`인지 여는 태그인지 검사한다. 즉 주석 필터링의 책임은 전적으로 `consumeCommentTokens`에 있다. 루프 자신은 주석 상태를 다시 확인하지 않는다.

주석은 줄 경계를 넘나들 수 있으므로 파서는 필드 하나로 상태를 기억한다. `private boolean inComment;`가 그것이고, 매 검출 시작 시 `false`로 초기화된다. 이 필드를 갱신하는 유일한 지점은 토큰 소비 헬퍼들이다.

```java
private @Nullable String consume(String line) {
	int index = (this.inComment ? endComment(line) : startComment(line));
	return (index == -1 ? null : line.substring(index));
}
```

```java
private int commentToken(String line, String token, boolean inCommentIfPresent) {
	int index = line.indexOf(token);
	if (index > - 1) {
		this.inComment = inCommentIfPresent;
	}
	return (index == -1 ? index : index + token.length());
}
```

읽는 방식은 이렇다. 현재 주석 밖이면 `<!--`를 찾고, 찾으면 `inComment`를 `true`로 올린 뒤 그 토큰 **뒤쪽** 문자열을 반환한다. 현재 주석 안이면 반대로 `-->`를 찾고, 찾으면 `inComment`를 `false`로 내린 뒤 그 뒤쪽을 반환한다. 어느 쪽도 찾지 못하면 `null`을 반환해 "이 줄에서 더 소비할 토큰이 없다"고 알린다.

이 헬퍼들을 엮어 한 줄 전체를 처리하는 것이 문제의 메서드다. 아래는 **수정 전** 원본이다.

```java
private String consumeCommentTokens(String line) {
	int indexOfStartComment = line.indexOf(START_COMMENT);
	if (indexOfStartComment == -1 && !line.contains(END_COMMENT)) {
		return line;
	}

	String result = "";
	String currLine = line;
	if (!this.inComment && (indexOfStartComment >= 0)) {
		result = line.substring(0, indexOfStartComment);
		currLine = line.substring(indexOfStartComment);
	}

	if ((currLine = consume(currLine)) != null) {
		result += consumeCommentTokens(currLine);
	}
	return result;
}
```

메서드는 세 단계로 읽힌다. 첫째, **조기 반환**이다. 줄 안에 `<!--`도 `-->`도 없으면 걷어낼 주석 경계가 없다고 보고 줄을 그대로 돌려준다. 둘째, 주석 밖에서 `<!--`를 만났다면 그 앞부분은 진짜 내용이므로 `result`에 떼어 두고, 나머지를 `currLine`으로 삼는다. 셋째, `consume`으로 토큰 하나를 소비하고 남은 꼬리에 대해 **자기 자신을 재귀 호출**해 누적한다. 한 줄에 주석이 여러 개 있어도, 주석이 줄 중간에서 시작해 다음 줄로 이어져도 이 재귀가 처리한다.

메서드의 Javadoc은 계약을 이렇게 못 박는다.

```java
/**
 * Consume all comments in the given String and return the remaining content,
 * which may be empty since the supplied content might be all comment data.
 * <p>This method takes the current "in comment" parsing state into account.
 */
```

마지막 문장이 이 PR의 근거다. 메서드는 "in comment" 상태를 고려한다고 선언했지만, 첫 단계인 조기 반환만은 그 상태를 전혀 보지 않았다.

한편 형제 메서드 `hasOpeningTag`는 같은 위험을 이미 방어하고 있었다. 이 비대칭이 문제의 냄새를 맡는 단서였다.

```java
private boolean hasOpeningTag(String content) {
	if (this.inComment) {
		return false;
	}
	int openTagIndex = content.indexOf('<');
	return (openTagIndex > -1 && (content.length() > openTagIndex + 1) &&
			Character.isLetter(content.charAt(openTagIndex + 1)));
}
```

Javadoc은 이 가드를 "sanity check"라고 부른다. 원칙적으로는 주석이 이미 다 걷혔어야 하니 필요 없지만, 만약을 대비한 안전망이라는 뜻이다. 그런데 `hasDoctype`에는 대응하는 안전망이 없다.

```java
private boolean hasDoctype(String content) {
	return content.contains(DOCTYPE);
}
```

**왜 이런 구멍이 생겼는지는 이력을 보면 드러난다.** 2022년 커밋 `4b1b25496bf`(gh-27915, "Improve comment parsing in DTD/XSD detection algorithm")가 재귀 알고리즘을 도입하면서 루프의 가드를 함께 제거했다.

```java
-				if (this.inComment || !StringUtils.hasText(content)) {
+				if (!StringUtils.hasText(content)) {
```

그 전까지는 루프가 `this.inComment`를 직접 확인해 주석 안이면 무조건 건너뛰었다. 새 알고리즘은 그 책임을 `consumeCommentTokens`로 옮겼는데, 조기 반환 경로만 상태 확인 없이 남으면서 방어선이 한 겹 사라졌다.

---

## 3. 무엇이 문제였나 — 오탐 재현

**주석이 여러 줄에 걸치고, 마커가 없는 가운데 줄에 `DOCTYPE`이라는 단어가 있으면 XSD 문서가 DTD로 오판된다.** 재현 파일은 특별할 것이 없는 평범한 설정 파일이다.

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

3행이 문제의 줄이다. 이 줄에는 `<!--`도 `-->`도 없다. 실행을 줄 단위로 따라가 보자.

1행 `<?xml ... ?>`은 주석 마커가 없어 조기 반환으로 그대로 통과한다. `inComment`는 `false`다. `hasDoctype`은 거짓이고, `hasOpeningTag`도 `<` 다음 글자가 `?`라 문자가 아니므로 거짓이다. 루프가 계속된다.

2행 `<!--`에서 조기 반환 조건이 깨진다. `inComment`가 `false`이고 시작 마커가 0번 위치이므로 앞부분 `""`이 `result`로 떨어지고, `consume`이 `<!--`를 소비하며 **`inComment`를 `true`로 올린다**. 남은 꼬리는 빈 문자열이라 재귀는 곧 끝나고 `result`는 `""`다. `StringUtils.hasText("")`가 거짓이므로 루프는 이 줄을 건너뛴다.

3행 `\tSee the DOCTYPE notes for legacy configs`에서 오탐이 일어난다. 이 줄에는 마커가 없으므로 조기 반환 조건 `indexOfStartComment == -1 && !line.contains(END_COMMENT)`가 참이 되고, 수정 전 코드는 **`inComment`가 `true`인데도 줄을 그대로 반환**한다. 루프 입장에서 이 문자열은 주석이 아니라 내용이다. `hasText`가 참, `hasDoctype`이 참이 되어 `isDtdValidated = true`로 설정되고 `break`가 걸린다. 4행 이후는 읽히지도 않는다. 결과는 `VALIDATION_DTD`다.

정리하면 실패의 조건은 세 가지가 동시에 성립할 때다. 첫째, 주석이 두 줄 이상에 걸쳐 있다. 둘째, 그 본문 줄에 `<!--`나 `-->`가 없다. 셋째, 그 줄에 `DOCTYPE`이라는 문자열이 있다. 세 번째 조건이 특히 함정인데, `hasDoctype`은 `content.contains(DOCTYPE)`일 뿐이라 `<!DOCTYPE` 형태의 진짜 선언이 아니라 **산문 속 단어 하나로도 충분히 걸린다**. 위 재현 파일의 "See the DOCTYPE notes for legacy configs"가 정확히 그런 경우다.

gh-27915의 수정이 이 사례를 놓친 이유도 분명하다. 그 커밋이 추가한 픽스처들은 모두 마커가 있는 줄을 다룬다. `xsdWithDoctypeInComment.xml`은 `<!--`, `DOCTYPE`, `-->`가 한 줄에 다 있고, `xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`은 `DOCTYPE`과 종료 마커가 같은 줄에 있다. 마커가 하나라도 있으면 조기 반환을 지나쳐 정상 경로로 들어가므로 문제가 드러나지 않는다. **마커가 전혀 없는 순수 본문 줄만이 잔여 사례로 남았다.**

---

## 4. 수정 해설

**수정은 조기 반환이 파싱 상태를 존중하도록 만드는 것이다.** 프로덕션 변경은 실질 한 줄이다.

```java
	private String consumeCommentTokens(String line) {
		int indexOfStartComment = line.indexOf(START_COMMENT);
		if (indexOfStartComment == -1 && !line.contains(END_COMMENT)) {
-			return line;
+			// If we are inside a multi-line comment, the entire line is comment
+			// data and must not be treated as content.
+			return (this.inComment ? "" : line);
		}
```

논리는 직관적이다. 마커가 없는 줄은 두 경우뿐이다. 주석 밖이라면 그 줄 전체가 내용이고, 주석 안이라면 그 줄 전체가 주석 본문이다. 수정 전 코드는 두 경우를 구분하지 않고 전자로만 취급했다. 이제 후자는 빈 문자열을 반환한다. 루프의 `if (!StringUtils.hasText(content)) continue;`가 그 빈 문자열을 걸러 주므로, 주석 본문은 판정에 아예 도달하지 않는다.

**기존 동작은 정확히 보존된다.** `this.inComment`가 `false`인 모든 호출에서 삼항식은 `line`으로 평가되며, 이는 수정 전 표현식과 문자 그대로 동일하다. 즉 이 변경이 관측 가능한 차이를 만드는 경우는 `inComment == true`인 조기 반환 경로 하나뿐이고, 그 경로가 바로 결함이 살던 자리다. 상태 필드를 새로 만들지도, 갱신 시점을 옮기지도 않았으므로 `consume` / `startComment` / `endComment` / `commentToken`의 의미는 그대로다.

이 수정이 **문서화된 계약을 회복시킨다**는 점도 중요하다. `consumeCommentTokens`의 Javadoc은 이미 "returns the remaining content, which may be empty since the supplied content might be all comment data"와 "takes the current 'in comment' parsing state into account"를 약속하고 있었다. 주석 본문 줄이야말로 "supplied content might be all comment data"의 교과서적 사례다. 새 규칙을 도입한 것이 아니라 선언된 규칙을 코드가 지키게 한 것이다.

대안도 검토했다. `hasDoctype(String)`에 `hasOpeningTag`와 같은 `if (this.inComment) return false;` 가드를 대칭적으로 추가하면 내용이 어떻게 만들어졌든 주석 안에서는 `DOCTYPE` 매칭이 성립하지 않게 된다. PR 본문은 이 옵션을 제안하되 적용하지 않았다. **근본 원인은 조기 반환의 상태 무시이고, 가드 추가는 증상 차단이기 때문이다.** 최소 변경을 유지하고 메인테이너 판단에 맡기는 쪽을 택했으며, 리뷰 결과 추가 가드 없이 그대로 머지되었다.

---

## 5. 검증

**테스트는 파라미터화된 회귀 픽스처로 구성된다.** `XmlValidationModeDetectorTests`는 파일 이름 목록을 받아 각각의 기대 검증 모드를 확인하는 구조이며, 새 사례를 추가한다는 것은 XML 파일 하나와 목록 한 줄을 추가한다는 뜻이다. 확인 로직 자체는 공통 헬퍼에 있다.

```java
private void assertValidationMode(String fileName, int expectedValidationMode) throws IOException {
	try (InputStream inputStream = getClass().getResourceAsStream(fileName)) {
		assertThat(xmlValidationModeDetector.detectValidationMode(inputStream))
			.as("Validation Mode")
			.isEqualTo(expectedValidationMode);
	}
}
```

PR이 추가한 것은 `xsdWithDoctypeInMultiLineCommentBody.xml` 하나이며, `xsdDetection`의 목록에 등재된다.

```java
		"xsdWithDoctypeInComment.xml",
		"xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml",
		"xsdWithDoctypeInMultiLineCommentBody.xml"
	})
	void xsdDetection(String fileName) throws Exception {
		assertValidationMode(fileName, VALIDATION_XSD);
	}
```

이 픽스처가 고정하는 것은 **3절의 재현 시나리오 그 자체**다. 마커 없는 주석 본문 줄에 `DOCTYPE`이 등장할 때 결과가 `VALIDATION_XSD`여야 한다는 명제다. 수정 전 코드에 이 테스트를 걸면 실패하므로, 결함을 실제로 재현하는 회귀 테스트로서 자격을 갖춘다.

머지 시 Sam Brannen이 후속 커밋 `4074155d76a`("Polish contribution")로 픽스처 두 개를 더 보탰다. 세 파일이 각각 무엇을 고정하는지 비교하면 커버리지 의도가 드러난다.

| 픽스처 | 기대값 | 고정하는 명제 |
|---|---|---|
| `xsdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 주석 본문의 `DOCTYPE`은 무시된다 (원 결함) |
| `xsdWithMultipleDoctypesInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 본문 줄이 여러 개여도, `DOCTYPE`이 여러 번 나와도 무시된다 |
| `dtdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_DTD` | 주석을 지나 등장하는 **진짜** 선언은 여전히 검출된다 |

세 번째가 특히 중요하다. 무시 규칙을 너무 넓게 적용해 실제 `DOCTYPE`까지 놓치는 과잉 수정을 막는 반대 방향 테스트이기 때문이다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--
	DOCTYPE
-->
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN 2.0//EN" "https://www.springframework.org/dtd/spring-beans-2.0.dtd">
<beans>

</beans>
```

3행의 `DOCTYPE`은 무시되어야 하고 5행의 선언은 잡혀야 한다. 수정 후 코드는 3행에서 빈 문자열을 반환해 건너뛰고, 4행에서 `-->`를 소비하며 `inComment`를 `false`로 되돌린 뒤, 5행을 정상 내용으로 판정해 `VALIDATION_DTD`를 낸다. 두 요구가 한 파일 안에서 동시에 검증된다.

기존 픽스처들이 그대로 통과한다는 사실도 회귀 방어의 일부다. `dtdWithNoComments.xml`, `dtdWithLeadingComment.xml`, `dtdWithTrailingComment.xml`, `dtdWithTrailingCommentAcrossMultipleLines.xml`, `dtdWithCommentOnNextLine.xml`, `dtdWithMultipleComments.xml`, `xsdWithNoComments.xml`, `xsdWithMultipleComments.xml` 등이 목록에 남아 있으며, 이들은 대부분 `inComment`가 `false`인 경로를 지나므로 4절에서 논증한 동작 보존을 실행으로 확인해 준다.

---

## 6. 상태와 교훈

**PR은 승인되어 `main`과 `7.0.x` 양쪽에 반영되었다.** 커밋 `1277279527c`("Ignore DOCTYPE inside a multi-line comment body", `Closes gh-36948`)가 본 수정이고, 며칠 뒤 `4074155d76a`가 픽스처를 보강했다. GitHub의 PR 상태가 `CLOSED`로 보이는 것은 자동 머지가 아니라 메인테이너가 커밋을 적용한 뒤 닫았기 때문이며, sbrannen이 "This has been merged into `7.0.x` and `main`."이라고 확인해 주었다. 리뷰 코멘트나 변경 요청은 없었다.

**첫째 교훈은 조기 반환이 상태 기계의 사각지대가 되기 쉽다는 것이다.** `consumeCommentTokens`의 본체는 `inComment`를 성실히 확인하는데, 성능을 위해 앞에 붙인 짧은 단축 경로만 그렇지 않았다. 상태를 들고 다니는 메서드에 "빠른 길"을 낼 때는, 그 길이 상태의 모든 값에 대해 옳은지 따져야 한다. 이번 경우 단축 조건은 `<!--`나 `-->`의 부재만 봤고, 그 부재가 "주석 밖"을 뜻한다고 암묵적으로 가정했다. 그 가정이 틀리는 값이 정확히 하나 있었다.

**둘째 교훈은 비대칭이 결함의 표지판이라는 것이다.** `hasOpeningTag`에는 `if (this.inComment) return false;` 가드가 있는데 `hasDoctype`에는 없었다. 같은 층위의 두 판정 메서드가 같은 위험에 대해 서로 다른 수준으로 방어한다면, 둘 중 하나는 대개 틀렸거나 최소한 설명이 필요하다. 여기에 이력 조사를 더하면 그림이 완성되는데, gh-27915가 루프의 `this.inComment ||` 가드를 제거하면서 방어선을 한 겹 걷어냈다는 사실이 `git log`로 바로 드러났다. **기존 수정이 있는 자리를 다시 고칠 때는 그 수정이 무엇을 옮겼고 무엇을 지웠는지 확인하는 것이 잔여 사례를 찾는 가장 빠른 길이다.**

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md` `spring-beans/06-설정-로딩과-팩토리-후처리.md`
