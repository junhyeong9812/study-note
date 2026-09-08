# PR #36948 분석 — XmlValidationModeDetector의 여러 줄 주석 본문 DOCTYPE 오탐

> 기준: 수정 전 = `1277279527c^`(이 문서의 `XmlValidationModeDetector.java` 줄 번호는 이 커밋 기준), 수정 후·호출처 = `upstream/main` `7daf1013aa8`.
> 머지: 커밋 `1277279527c`("Ignore DOCTYPE inside a multi-line comment body", `Closes gh-36948`)로 `main`·`7.0.x` 반영. GitHub PR 상태가 CLOSED·`mergeCommit: null`인 것은 메인테이너가 커밋을 직접 적용한 뒤 닫았기 때문이며, sbrannen이 머지 사실을 코멘트로 확인했다. 후속 `4074155d76a`("Polish contribution")가 픽스처 2개를 보강했다.
> 관련 작업 폴더: `docs/plans/2026-06-16/spring-core-bug-hunt-round2/B11-xmlvalidation-doctype-in-comment/task.md`.
> README(서사)·structure.md(무대 지도)·tests.md(테스트 해설)와 중복을 피하고, 호출 그래프·이름표 사전·단계 추적·수정안 판단에 집중한다.

## 0. 결론

`consumeCommentTokens(String)`의 조기 반환 경로가 **`this.inComment` 상태를 확인하지 않아**, 주석 마커(`<!--`·`-->`)가 하나도 없는 여러 줄 주석의 본문 줄을 통째로 "내용"으로 돌려주었고, 그 결과 산문 속 `DOCTYPE`이라는 단어 하나가 XSD 문서를 DTD로 오판하게 만들었다. 수정은 그 조기 반환을 `return (this.inComment ? "" : line);`으로 바꿔 주석 본문 줄이 기존의 빈 내용 필터에 걸리게 하는 실질 한 줄이다. `main`과 `7.0.x` 양쪽에 머지되었다.

## 1. 무대

결함이 사는 자리와 그 주변 좌표를 먼저 고정한다. 아래 표는 모듈·파일·메서드·호출처·테스트를 한 항목씩 나열한 것이다.

| 항목 | 값 |
|---|---|
| 모듈 | `spring-core` (호출처는 `spring-beans`) |
| 결함 파일 | `spring-core/src/main/java/org/springframework/util/xml/XmlValidationModeDetector.java` |
| 결함 메서드 | `consumeCommentTokens(String)` (`:151-168`), 그중 조기 반환 `:153-155` |
| 공개 진입 API | `XmlValidationModeDetector.detectValidationMode(InputStream)` (`:92`, public) |
| 유일한 프로덕션 호출처 | `XmlBeanDefinitionReader.detectValidationMode(Resource)` -> `XmlBeanDefinitionReader.java:499` |
| 결과 소비처 | `DefaultDocumentLoader.createDocumentBuilderFactory(int, boolean)` (`DefaultDocumentLoader.java:88`) |
| 테스트 | `spring-core/src/test/java/org/springframework/util/xml/XmlValidationModeDetectorTests.java` + `src/test/resources/org/springframework/util/xml/*.xml` |

이 클래스가 하는 일은 **파서를 만들기 위한 정보를 파서 없이 얻는 것**이다. XML에는 두 스키마 체계가 공존하고(상단 `<!DOCTYPE ...>`로 DTD를 가리키는 옛 방식, 루트 태그 `xsi:schemaLocation`으로 XSD를 가리키는 현대 방식), JAXP의 `DocumentBuilderFactory`는 둘을 자동 구분하지 않는다. 그래서 Spring은 같은 파일을 두 번 읽는다 — 첫 번째가 이 문자열 스캐너이고, 그 결론으로 파서를 구성한 뒤 두 번째 읽기에서 DOM을 만든다.

언제 불리는가에는 조건이 하나 붙는다. `XmlBeanDefinitionReader.getValidationModeForResource`(`:456`)는 사용자가 검증 모드를 명시하지 않아 `VALIDATION_AUTO`로 남아 있을 때만 검출을 수행하고, 명시했으면 그 값을 그대로 돌려준다(`:453-455`). 즉 결함은 **기본 설정으로 XML 빈 정의를 로딩하는 모든 애플리케이션**에 노출되지만, `setValidationMode`를 명시한 애플리케이션은 비껴간다.

오판의 대가는 조용한 성능 저하가 아니라 **기동 실패**다. XSD 문서를 DTD 모드로 파싱하면 `DefaultDocumentLoader.java:98`이 `setValidating(true)`만 켠 채 파서를 만들고(XSD 분기 `:99-113`은 건너뛴다), 파서는 DTD 문법을 기대하는데 문서에 `DOCTYPE`이 없으므로 검증 오류를 보고한다. 그 오류는 `SimpleSaxErrorHandler`가 다시 던지고 `XmlBeanDefinitionReader.java:412`의 `catch (SAXParseException ex)`에 잡혀 `XmlBeanDefinitionStoreException`으로 올라간다.

## 2. 전체 메서드 그래프

컨텍스트 기동에서 스캐너 내부의 조기 반환까지, 한 줄이 판정에 이르는 경로 전체를 두 덩어리로 나눠 그린다.

```
[진입 경로 — spring-beans]
 ClassPathXmlApplicationContext 등 XML 기반 컨텍스트 기동
   -> XmlBeanDefinitionReader.loadBeanDefinitions(Resource ...)
      -> doLoadBeanDefinitions(inputSource, resource)          XmlBeanDefinitionReader.java:398
         -> doLoadDocument(inputSource, resource)              XmlBeanDefinitionReader.java:443
            -> getValidationModeForResource(resource)          XmlBeanDefinitionReader.java:456
               |  명시 모드가 있으면 그대로 반환                :453-455
               -> detectValidationMode(resource)               XmlBeanDefinitionReader.java:478
                  |  resource.isOpen() 이면 예외               :474-480 (재열람 불가)
                  -> this.validationModeDetector               필드, :136 (인스턴스 1개 재사용)
                       .detectValidationMode(inputStream)      :499  (!) 유일한 프로덕션 진입
            -> DefaultDocumentLoader.loadDocument(...)         DefaultDocumentLoader.java:69
               -> createDocumentBuilderFactory(mode, nsAware)  DefaultDocumentLoader.java:88
                  |  mode != NONE -> setValidating(true)       :97-98
                  |  mode == XSD  -> setNamespaceAware(true)   :101
                  |                  setAttribute(SCHEMA_...)  :103
               -> builder.parse(inputSource)                   DefaultDocumentLoader.java:77

[스캐너 내부 — spring-core, 줄 번호는 수정 전 1277279527c^ 기준]
 detectValidationMode(InputStream)                                            :92
   this.inComment = false;                                                    :93   상태 리셋
   BufferedReader 로 한 줄씩                                                  :96, :99
     |
     +-- content = consumeCommentTokens(content);                             :100
     |     |
     |     +-- indexOfStartComment = line.indexOf(START_COMMENT)              :152
     |     +-- [분기 1 조기 반환] idx == -1 && !line.contains(END_COMMENT)     :153
     |     |      수정 전: return line;                                       :154  [BUG]
     |     |      수정 후: return (this.inComment ? "" : line);
     |     |
     |     +-- [분기 2 앞부분 분리] !inComment && idx >= 0                     :159
     |     |      result   = line.substring(0, idx)                           :160
     |     |      currLine = line.substring(idx)                              :161
     |     |
     |     +-- [분기 3 토큰 소비 + 재귀]                                       :164-166
     |            consume(currLine)                                           :174-177
     |              inComment ? endComment(line) : startComment(line)         :175
     |                -> commentToken(line, token, inCommentIfPresent)        :201-207
     |                     if (index > -1) this.inComment = flag;             :203-205  (!) 상태 변경 유일 지점
     |                     return index == -1 ? -1 : index + token.length()   :206
     |            result += consumeCommentTokens(꼬리)                        :165  자기 재귀
     |
     +-- [필터] if (!StringUtils.hasText(content)) continue;                   :101-103
     +-- [판정 1] if (hasDoctype(content))                                     :104
     |               return content.contains(DOCTYPE);                        :126-128  (!) inComment 가드 없음
     |               -> isDtdValidated = true; break;                         :105-106
     +-- [판정 2] if (hasOpeningTag(content))                                  :108
                     if (this.inComment) return false;                        :138-140  (!) inComment 가드 있음
                     '<' 다음 문자가 letter 인가                              :141-143
                     -> break ("의미 있는 데이터 끝")                          :110
   return (isDtdValidated ? VALIDATION_DTD : VALIDATION_XSD);                 :113
   catch (CharConversionException) -> return VALIDATION_AUTO;                 :115-119
```

그래프가 드러내는 비대칭이 결함의 표지판이다. 같은 층위의 두 판정 메서드 중 `hasOpeningTag`는 `inComment` 가드를 갖는데(`:138`) `hasDoctype`은 갖지 않는다(`:126-128`). 그리고 `hasOpeningTag`의 javadoc(`:130-136`)은 그 가드를 "sanity check"라 부르며 "원칙적으로는 주석이 이미 다 걷혔어야 하지만"이라는 단서를 단다 — 그 단서가 참이 아닌 경우가 정확히 분기 1의 `[BUG]` 갈래였다.

## 2.5 핵심 이름표 사전

이 스캐너의 이름표는 세 종류로 나뉜다: 상태를 나타내는 것, 토큰 위치를 나타내는 것, 그리고 "지금까지 걷어낸 뒤 남은 문자열"을 나르는 것. 세 번째 계열이 특히 헷갈리는데 `line`·`currLine`·`result`·`content`가 서로 다른 단계의 문자열이기 때문이다. 예시 값은 픽스처 `xsdWithDoctypeInMultiLineCommentBody.xml`의 3행(`\tSee the DOCTYPE notes for legacy configs`) 처리 시점 기준이다.

| 이름표 | 역할 | 입력 -> 출력 | 누가 언제 부르나 | 이 결함과의 관계 |
|---|---|---|---|---|
| `inComment` (필드, `:81`) | **유일한 상태** — 현재 파싱 위치가 XML 주석 안인가 | boolean. `:93`이 리셋, `:203-205`만 변경 | `consume`(`:175`), `consumeCommentTokens`(`:159`), `hasOpeningTag`(`:138`)가 읽음 | 3행 진입 시 `true`. 수정 전 조기 반환이 이 값을 **읽지 않은 것**이 결함 자체 |
| `detectValidationMode(InputStream)` (`:92-120`) | 공개 진입점. 파일 앞부분을 훑어 정수 판정 | InputStream -> `VALIDATION_DTD`(2) / `VALIDATION_XSD`(3) / `VALIDATION_AUTO`(1) | `XmlBeanDefinitionReader.java:499` | 결함의 결과가 관측되는 지점. 3행에서 `break`가 걸려 4·5행을 읽지도 못한다 |
| `isDtdValidated` (지역변수, `:97`) | "DOCTYPE을 봤다" 플래그 | false -> `:105`에서 true | `:113`이 최종 반환값으로 변환 | 결함이 만든 잘못된 true가 그대로 `VALIDATION_DTD`가 된다 |
| `content` (지역변수, `:98`) | 한 줄을 읽어 주석을 걷어낸 **판정 대상** 문자열 | `readLine()` -> `consumeCommentTokens(...)`의 반환값 | `:101` 필터, `:104`·`:108` 판정 | 수정 전 3행에서 `"\tSee the DOCTYPE notes..."`, 수정 후 `""` |
| `consumeCommentTokens(String)` (`:151-168`) | 한 줄에서 주석을 전부 걷어내고 남은 내용 반환 | line -> 내용(빈 문자열 가능) | 루프가 매 줄 1회 + 자기 재귀(`:165`) | 결함 본체. javadoc(`:146-150`)이 "takes the current 'in comment' parsing state into account"를 선언했는데 조기 반환만 지키지 않았다 |
| `line` (파라미터) | 이번 호출이 처리할 문자열(원본 줄 또는 재귀 꼬리) | `"\tSee the DOCTYPE notes for legacy configs"` | 재귀 깊이마다 다른 값 | 수정 전 조기 반환이 이 값을 무조건 그대로 돌려줬다 |
| `indexOfStartComment` (지역변수, `:152`) | `<!--`의 위치, 없으면 -1 | 3행에서 `-1` | `:153` 조기 반환 조건, `:159` 앞부분 분리 조건 | 조기 반환 조건의 절반. `-1`이 "주석 밖"을 뜻한다는 **암묵적 가정**이 틀린 지점 |
| `line.contains(END_COMMENT)` (`:153`) | `-->`가 이 줄에 있는가 | 3행에서 `false` | 조기 반환 조건의 나머지 절반 | 두 조건이 모두 참일 때 "걷어낼 주석 경계가 없다"로 판단한다. 참이지만 "주석 밖"은 아니다 |
| `result` (지역변수, `:157`) | 이번 호출이 누적한 **내용** 부분 | `""`에서 시작, `:160`·`:165`가 누적 | `:167`이 반환 | 정상 경로에서 주석 앞부분과 재귀 결과를 이어 붙인다. 조기 반환 경로는 이 변수에 도달하지 않는다 |
| `currLine` (지역변수, `:158`) | 아직 소비하지 않은 **꼬리** 문자열 | `line`에서 시작, `:161`·`:164`가 갱신 | `consume`에 넘겨짐 | 재귀가 같은 줄 안에서 상태를 여러 번 뒤집을 수 있게 하는 장치 |
| `consume(String)` (`:174-177`) | 다음 주석 토큰 하나를 소비하고 꼬리 반환 | line -> 토큰 뒤 문자열 또는 `null` | `consumeCommentTokens:164` | `inComment`에 따라 찾을 토큰을 고른다(`:175`) — 본체는 상태를 성실히 본다는 증거 |
| `startComment` / `endComment` (`:183-185` / `:191-193`) | `<!--` / `-->` 소비 시도 | line -> 토큰 뒤 인덱스 또는 -1 | `consume:175`가 택일 호출 | 각각 `inCommentIfPresent = true` / `false`로 `commentToken`을 부른다 |
| `commentToken(String,String,boolean)` (`:201-207`) | 토큰을 찾고 **상태를 뒤집는** 유일한 지점 | (line, token, flag) -> 인덱스 | `startComment`·`endComment` | `if (index > -1) this.inComment = flag;`(`:203-205`). 토큰을 실제로 찾았을 때만 상태가 바뀐다 |
| `hasDoctype(String)` (`:126-128`) | 내용에 DOCTYPE 토큰이 있는가 | content -> `content.contains("DOCTYPE")` | `:104` | **부분 문자열 매칭일 뿐**이라 `<!DOCTYPE` 형태의 선언이 아니라 산문 속 단어로도 참이 된다. 그리고 `inComment` 가드가 없다 |
| `hasOpeningTag(String)` (`:137-144`) | 내용에 여는 태그가 있는가 | content -> `<` 다음이 letter인가 | `:108` | `if (this.inComment) return false;`(`:138-140`) 가드를 갖는다. `hasDoctype`과의 이 비대칭이 결함을 찾는 단서였다 |
| `StringUtils.hasText(content)` (`:101`) | 내용이 공백뿐인가 | content -> boolean | 루프가 매 줄 1회 | **수정이 기대는 기존 필터.** 주석 본문을 `""`로 만들기만 하면 이 줄이 나머지를 처리하므로 새 분기가 필요 없다 |
| `DOCTYPE` / `START_COMMENT` / `END_COMMENT` (`:65`·`:70`·`:75`) | 토큰 상수 `"DOCTYPE"`·`"<!--"`·`"-->"` | — | 위 판정·소비 메서드들 | 스캐너가 인식하는 어휘 전부. 이것이 전부라는 사실이 "완전한 파서가 아닌 휴리스틱"임을 규정한다 |
| `VALIDATION_NONE/AUTO/DTD/XSD` (`:42`·`:48`·`:53`·`:58`) | 판정 결과 상수 0/1/2/3 | — | `:113`·`:118`이 반환, `DefaultDocumentLoader:97-99`가 소비 | `DTD`와 `XSD`가 뒤바뀌면 파서 구성이 통째로 달라져 기동이 깨진다 |

표를 관통하는 사실 하나. 상태를 바꾸는 곳은 `commentToken`의 `:204` 한 줄뿐이고, 상태를 **읽는** 곳은 네 곳(`:159`, `:175`, `:138`, 그리고 수정이 추가한 조기 반환)이다. 수정 전에는 읽는 곳이 셋이었고, 빠진 하나가 정확히 결함의 자리였다.

## 3. 결함 경로 단계 추적

픽스처 `xsdWithDoctypeInMultiLineCommentBody.xml`을 줄 단위로 따라간다. 정상 케이스(수정 후)와 결함 케이스(수정 전)를 같은 표에 놓는다.

```
1: <?xml version="1.0" encoding="UTF-8"?>
2: <!--
3: \tSee the DOCTYPE notes for legacy configs
4: -->
5: <beans xmlns="http://www.springframework.org/schema/beans"
...
```

| 줄 | 진입 시 `inComment` | `consumeCommentTokens` 경로 | 수정 전 반환 `content` | 수정 후 반환 `content` | 루프 판정 |
|---|---|---|---|---|---|
| 1 | false | 마커 없음 -> 조기 반환(`:153`) | 줄 전체 | 줄 전체 (동일) | `hasText` 참 / `hasDoctype` 거짓 / `hasOpeningTag` 거짓(`<` 다음이 `?`) -> 계속 |
| 2 | false | `idx("<!--") = 0` -> 본체. 앞부분 `""`를 `result`로(`:160`), `consume`이 `<!--` 소비하며 `inComment := true`(`:204`), 꼬리 `""` 재귀 | `""` | `""` (동일) | `hasText` 거짓 -> continue. 상태 false -> true |
| 3 | **true** | 마커 없음 -> 조기 반환(`:153`) | **줄 전체** [BUG] | `""` | 수정 전: `hasDoctype` 참 -> `isDtdValidated = true`, `break`(`:105-106`) / 수정 후: `hasText` 거짓 -> continue |
| 4 | true | `-->` 포함 -> 본체. `!inComment` 거짓이라 앞부분 분리 안 함(`:159`), `consume`이 `-->` 소비하며 `inComment := false` | (도달 안 함) | `""` | `hasText` 거짓 -> continue. 상태 true -> false |
| 5 | false | 마커 없음 -> 조기 반환 | (도달 안 함) | 줄 전체 | `hasOpeningTag` 참(`<` 다음이 `b`) -> `break`(`:110`) |
| 최종 | | | `VALIDATION_DTD`(2) — **오판** | `VALIDATION_XSD`(3) — 정답 | |

수정 전 경로에서 4·5행이 **아예 읽히지 않는다**는 점을 짚어 둘 만하다. 3행의 `break`가 루프를 끝내므로, 이 문서가 XSD 설정이라는 결정적 증거(`<beans xmlns=... xsi:schemaLocation=...>`)는 판정에 참여할 기회조차 없다.

발동 조건은 세 개가 **동시에** 성립할 때다: (a) 주석이 두 줄 이상에 걸친다, (b) 그 본문 줄에 `<!--`도 `-->`도 없다, (c) 그 줄에 `DOCTYPE`이라는 문자열이 있다. (b)가 빠지면(마커가 하나라도 있으면) 조기 반환을 지나쳐 본체로 들어가고, 본체는 `inComment`를 성실히 확인하므로 정상 동작한다. 대조군으로 기존 픽스처 `xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`의 3행을 보면 한 줄 안에서 상태가 두 번 뒤집히지만(`-->` 소비 -> `<!--` 소비 -> `-->` 소비) 결과는 공백 `"    "`이고 `hasText` 필터가 걸러 낸다. gh-27915(2022)가 추가한 픽스처들이 전부 이 (b) 위반 부류였고, 그래서 **마커가 전혀 없는 순수 본문 줄만 잔여 사례로 남았다**.

이 구멍이 생긴 경위도 `git log`에 남아 있다. 2022년 커밋 `4b1b25496bf`(gh-27915)가 지금의 재귀 알고리즘을 도입하면서 루프의 가드를 함께 제거했다.

```diff
-				if (this.inComment || !StringUtils.hasText(content)) {
+				if (!StringUtils.hasText(content)) {
```

그전까지는 루프가 `this.inComment`를 직접 확인해 주석 안이면 무조건 건너뛰었다. 새 알고리즘은 그 책임을 `consumeCommentTokens`로 옮겼는데, 조기 반환 경로만 상태 확인 없이 남으면서 방어선이 한 겹 사라졌다. **책임 이전이 완결되지 않은 자리**에 생긴 결함이다.

## 4. 계약과 위반

이 결함은 외부 표준이 아니라 **소스에 적힌 계약**을 어긴다.

- **(C1)** `consumeCommentTokens`의 javadoc(`:146-150`): "Consume all comments in the given String and return the remaining content, **which may be empty since the supplied content might be all comment data**." 여러 줄 주석의 본문 줄이야말로 "all comment data"의 교과서적 사례인데, 조기 반환은 빈 문자열을 만들지 않았다.
- **(C2)** 같은 javadoc: "This method **takes the current 'in comment' parsing state into account**." 본체(`:159`, `:175`)는 지켰고 조기 반환(`:153-155`)만 지키지 않았다. 선언과 구현의 부분 불일치다.
- **(C3)** 루프의 설계 계약(`:100-103`): 주석 필터링의 책임은 전적으로 `consumeCommentTokens`에 있고, 루프 자신은 `inComment`를 다시 확인하지 않는다. 이 계약이 성립하려면 (C1)(C2)가 성립해야 한다.
- **(C4)** `hasOpeningTag`의 javadoc(`:130-136`): "It is expected that all comment tokens will have been consumed ... However, as a sanity check, if the parse state is currently in an XML comment this method always returns `false`." 이 문장의 "expected"가 참이 아닌 경우가 있었고, `hasDoctype`에는 같은 sanity check가 없어 그 경우를 흡수하지 못했다.

기존 테스트가 고정하던 것은 (C1)(C2)를 마커가 있는 줄에 대해서만이었다. `xsdWithDoctypeInComment.xml`(한 줄에 `<!--`·`DOCTYPE`·`-->` 전부), `xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`(`DOCTYPE`과 종료 마커가 같은 줄), `xsdWithMultipleComments.xml`(본문 도달 전에 여는 태그로 `break`) 어느 것도 (b) 조건을 만족하지 않는다.

## 5. 수정안

프로덕션 diff는 실질 한 줄이다(`spring-core/src/main/java/org/springframework/util/xml/XmlValidationModeDetector.java`).

```java
// before (1277279527c^:151-155)
	private String consumeCommentTokens(String line) {
		int indexOfStartComment = line.indexOf(START_COMMENT);
		if (indexOfStartComment == -1 && !line.contains(END_COMMENT)) {
			return line;
		}

// after (upstream/main:151-157)
	private String consumeCommentTokens(String line) {
		int indexOfStartComment = line.indexOf(START_COMMENT);
		if (indexOfStartComment == -1 && !line.contains(END_COMMENT)) {
			// If we are inside a multi-line comment, the entire line is comment
			// data and must not be treated as content.
			return (this.inComment ? "" : line);
		}
```

**왜 그 위치인가.** 논리는 단순하다 — 마커가 없는 줄은 두 경우뿐이다. 주석 밖이면 그 줄 전체가 내용이고, 주석 안이면 그 줄 전체가 주석 본문이다. 수정 전 코드는 두 경우를 구분하지 않고 전자로만 취급했으므로, 구분을 도입하는 것이 정확히 결함의 크기다. 그리고 루프에 이미 빈 내용 필터(`:101`)가 있으므로 후자를 `""`로 만들기만 하면 나머지는 기존 장치가 처리한다 — **새 분기도, 새 필드도, 상태 갱신 시점 변경도 없다**. `consume`·`startComment`·`endComment`·`commentToken`의 의미는 그대로다.

**기존 동작이 보존된다는 논증.** `this.inComment`가 `false`인 모든 호출에서 삼항식은 `line`으로 평가되며, 이는 수정 전 표현식과 문자 그대로 동일하다. 따라서 관측 가능한 차이가 생기는 경우는 `inComment == true`인 조기 반환 경로 **하나**뿐이고, 그 경로가 바로 결함이 살던 자리다. 기존 픽스처 열 건이 green을 유지한다는 사실이 이 논증을 실행으로 확인해 준다.

**검토한 대안과 기각 이유.**

첫째, `hasDoctype(String)`에 `hasOpeningTag`와 대칭인 `if (this.inComment) return false;` 가드를 추가하는 안. PR 본문에 `Note`로 제시하되 적용하지 않았다. **근본 원인은 조기 반환의 상태 무시이고, 가드 추가는 증상 차단**이기 때문이다 — 주석 본문이 여전히 `content`로 흘러나오는 상태에서 판정 메서드 하나만 막으면, 나중에 세 번째 판정 메서드가 추가될 때 같은 구멍이 다시 열린다. 최소 변경을 유지하고 메인테이너 판단에 맡기는 쪽을 택했으며, 리뷰 결과 추가 가드 없이 그대로 머지되었다.

둘째, `hasDoctype`을 `<!DOCTYPE` 전체 매칭으로 조여 산문 속 단어를 배제하는 안. 채택하지 않았다. 이 클래스는 완전한 파서가 아니라 휴리스틱 스캐너이고, 판정 기준을 조이면 공백이나 개행이 낀 변형 선언을 놓칠 위험이 생긴다. 오탐(XSD를 DTD로)을 막으려다 미탐(진짜 DTD를 놓침)을 만드는 교환이다.

셋째, 루프에 `this.inComment ||` 가드를 되돌려 놓는 안(gh-27915 이전 형태). 채택하지 않았다. 2022년 리팩터링이 의도적으로 옮긴 책임 배치를 되돌리는 것이고, `consumeCommentTokens`의 javadoc이 이미 그 책임을 자기 것으로 선언하고 있으므로 선언과 구현을 맞추는 쪽이 일관된다.

**테스트.** 이 PR이 추가한 것은 파라미터 케이스 하나(`xsdWithDoctypeInMultiLineCommentBody.xml`)이며, 3절의 재현 시나리오를 그대로 고정한다. 픽스처는 결함을 유도하려고 비튼 구조가 아니라 헤더 주석의 가장 흔한 형태(`<!--`가 한 줄, 설명이 다음 줄, `-->`가 다시 한 줄)이고, `DOCTYPE`이 선언이 아니라 산문 속 단어("See the DOCTYPE notes for legacy configs")로 등장하며, 본문이 진짜 XSD 설정이라 오판 시 실제로 기동이 깨지는 문서다. 머지 시 sbrannen이 `4074155d76a`로 픽스처 2개를 보탰다.

| 픽스처 | 기대값 | 고정하는 명제 | 출처 |
|---|---|---|---|
| `xsdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 주석 본문의 `DOCTYPE`은 무시된다 (원 결함, red) | 이 PR |
| `xsdWithMultipleDoctypesInMultiLineCommentBody.xml` | `VALIDATION_XSD` | 본문 줄이 여러 개여도, `DOCTYPE`이 여러 번 나와도 무시된다 | 폴리시 커밋 |
| `dtdWithDoctypeInMultiLineCommentBody.xml` | `VALIDATION_DTD` | 주석을 지나 등장하는 **진짜** 선언은 여전히 검출된다 (음성 가드) | 폴리시 커밋 |

셋째 항목이 이 수정의 과잉 형태 — 무시 규칙을 너무 넓게 적용해 진짜 `<!DOCTYPE` 선언까지 놓치는 것 — 을 한 파일 안에서 직접 겨눈다. 3행의 `DOCTYPE`은 무시되어야 하고 5행의 선언은 잡혀야 하므로 두 요구가 동시에 검증된다. 원 PR이 red 케이스만 추가하고 음성 가드는 메인테이너가 채웠다는 사실 자체가 남겨 둘 만한 관찰이다.

## 6. 범위 밖과 인접 영향

**blast radius.** `detectValidationMode`의 프로덕션 호출처는 `XmlBeanDefinitionReader.java:499` 하나이고, 결과를 소비하는 곳은 `DefaultDocumentLoader.createDocumentBuilderFactory`(`:88`) 하나다. 수정은 `spring-core`의 private 메서드 한 줄이므로 API 표면 변화가 없다.

**하위호환.** 5절의 삼항식 논증대로, `inComment == false`인 모든 경로에서 수정 전후 식이 항등이다. 동작이 달라지는 것은 (a) 주석이 여러 줄에 걸치고 (b) 본문 줄에 마커가 없고 (c) 그 줄에 `DOCTYPE`이 있는 문서뿐이며, 그 문서들의 이전 판정은 **오판**이었다. 오판에 의존하던 설정이 존재할 수는 있으나(주석 안 `DOCTYPE` 단어로 DTD 모드를 유도하던 문서), 그것은 문서화된 동작이 아니다.

**같은 패턴의 다른 위치.** `hasDoctype`(`:126-128`)의 `inComment` 가드 부재는 이번 수정으로 도달 불가가 되었을 뿐 **제거되지 않았다**. 조기 반환이 주석 본문을 차단하므로 현재는 `hasDoctype`에 주석 텍스트가 들어올 경로가 없지만, `hasOpeningTag`와의 비대칭은 코드에 그대로 남아 있다. 메인테이너가 대칭 가드를 적용하지 않기로 판단한 결과다.

`hasDoctype`이 부분 문자열 매칭이라는 느슨함도 그대로다(`content.contains("DOCTYPE")`). 주석 밖 산문에 `DOCTYPE`이 나오는 경우는 여전히 오탐이지만, XML에서 루트 태그 이전의 주석 밖 텍스트는 문법상 허용되지 않으므로 실사용 시나리오가 좁다. 이 판단은 미검증 추정이며 확정하려면 실제 파서 동작 확인이 필요하다.

**인접 리포트.** 이 결함은 gh-27915(2022, CLOSED as COMPLETED)의 **잔여 사례**다. 그 이슈와 fix PR gh-27927은 마커가 같은 줄에 있는 경우를 커버했고, 이번 PR이 마커 없는 본문 줄을 채워 그 fix를 완성한다. 커밋 메시지가 "completing the fix for gh-27915 which only covered comment markers on the same line"으로 그 관계를 명시한다. **기존 수정이 있는 자리를 다시 고칠 때 그 수정이 무엇을 옮기고 무엇을 지웠는지 `git log`로 확인하는 것**이 잔여 사례를 찾는 지름길이라는 사례다.

**상태 필드와 재사용.** `inComment`는 인스턴스 필드이므로 검출기는 동시 호출에 안전하지 않다(재진입 불가). 그러나 `detectValidationMode`가 진입 즉시 `false`로 리셋하므로(`:93`) 순차 재사용은 안전하고, `XmlBeanDefinitionReader`가 검출기를 `final` 필드 하나로 모든 리소스에 재사용하는 배치(`XmlBeanDefinitionReader.java:136`)가 이 리셋에 기대고 있다. 이번 수정은 상태의 수명이나 리셋 시점을 바꾸지 않았으므로 이 성질도 그대로다.
