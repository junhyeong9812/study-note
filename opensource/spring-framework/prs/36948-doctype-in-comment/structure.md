# PR #36948 — 무대의 실구조와 워크플로우

> PR #36948의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main 526c706d1c3. 이 문서의 `파일:줄` 인용은 모두 이 커밋 기준이며, PR 시점의 base 코드와 다른 곳은 본문에서 명시한다.

이 문서가 다루는 것은 `XmlValidationModeDetector`가 XML 앞부분을 한 줄씩 훑으며 굴리는 **작은 상태 기계**의 실구조다.\
상태는 `inComment` 필드 하나뿐이고, 전이를 일으키는 사건은 `<!--`와 `-->` 두 토큰뿐이다.\
PR이 바꾼 줄은 한 줄이지만, 그 줄은 상태 기계의 한 전이 경로가 상태를 읽지 않고 있던 사각지대를 메운다.

> **상태 기계(state machine)** — 정해진 몇 개의 상태 중 하나에 머물다가, 특정 사건이 오면 다른 상태로 옮겨 가는 구조.\
> 예: 여기서는 상태가 "주석 밖"·"주석 안" 둘이고, 사건은 `<!--` 발견과 `-->` 발견 둘이다.

> **토큰(token)** — 파싱할 때 의미 단위로 잘라 내는 문자열 조각.\
> 예: 이 검출기가 아는 토큰은 `DOCTYPE`·`<!--`·`-->` 셋뿐이다.

---

## 1. 무대 — 실구조

**검출기는 상수 네 개, 토큰 세 개, 상태 필드 하나, 그리고 그 위에 얹힌 메서드 일곱 개로 이루어진 단일 클래스다.**\
외부와의 접점은 `detectValidationMode(InputStream)` 하나뿐이고, 나머지는 전부 private이다.

```text
  org.springframework.util.xml
  ┌────────────────────────────────────────────────────────────────────────┐
  │ public class XmlValidationModeDetector    XmlValidationModeDetector.java:37 │
  │                                                                        │
  │  ── 결과 상수 (public) ──────────────────────────────────────────────  │
  │    VALIDATION_NONE = 0   검증 안 함                             (:42)  │
  │    VALIDATION_AUTO = 1   판별 실패, 호출자에게 위임               (:48)  │
  │    VALIDATION_DTD  = 2   DOCTYPE 발견                           (:53)  │
  │    VALIDATION_XSD  = 3   DOCTYPE 없이 여는 태그 도달             (:58)  │
  │                                                                        │
  │  ── 토큰 상수 (private static final) ────────────────────────────────  │
  │    DOCTYPE       = "DOCTYPE"                                    (:65)  │
  │    START_COMMENT = "<!--"                                       (:70)  │
  │    END_COMMENT   = "-->"                                        (:75)  │
  │                                                                        │
  │  ── 상태 (인스턴스 필드, 단 하나) ───────────────────────────────────  │
  │    private boolean inComment;                                   (:81)  │
  │        "현재 파싱 위치가 XML 주석 안인가"                              │
  │        detectValidationMode 진입 시마다 false 로 리셋            (:93)  │
  │                                                                        │
  │  ── 진입점 ─────────────────────────────────────────────────────────  │
  │    public int detectValidationMode(InputStream) throws IOException     │
  │                                                                 (:92)  │
  └────────────────────────────────────────────────────────────────────────┘
             │
             │ 줄마다 호출
             ▼
  ┌─────────────────────────────┐        ┌──────────────────────────────────┐
  │ consumeCommentTokens(String)│        │ 판정 메서드 2개                   │
  │                      (:151) │        │  hasDoctype(String)       (:126) │
  │  주석을 걷어내고 내용만 반환 │        │    content.contains("DOCTYPE")   │
  │  ← PR이 바꾼 메서드          │        │    ▶ inComment 가드 없음         │
  │  자기 자신을 재귀 호출 (:167)│        │                                  │
  └──────────┬──────────────────┘        │  hasOpeningTag(String)    (:137) │
             │ 사용                       │    if (this.inComment) return false;
             ▼                            │                          (:138) │
  ┌─────────────────────────────┐        │    ▶ inComment 가드 있음 (*)      │
  │ consume(String) : @Nullable │        └──────────────────────────────────┘
  │                      (:176) │
  │  inComment 에 따라 찾을      │        (*) 같은 층위의 두 판정 메서드가
  │  토큰을 고른다               │          같은 위험에 서로 다르게 방어한다.
  └──────────┬──────────────────┘          이 비대칭이 결함의 표지판이었다.
             │
    ┌────────┴────────┐
    ▼                 ▼
 startComment      endComment
   (:185)            (:193)
    │                 │
    └────────┬────────┘
             ▼
  ┌───────────────────────────────────────────────────────────────┐
  │ commentToken(String line, String token, boolean flag)  (:203) │
  │   int index = line.indexOf(token);                     (:204) │
  │   if (index > -1) { this.inComment = flag; }         (:205~207)│  ◀ 상태를 바꾸는
  │   return (index == -1 ? index : index + token.length());(:208)│    유일한 지점
  └───────────────────────────────────────────────────────────────┘
```

구조에서 세 가지를 짚어 둔다.

첫째, **상태를 바꾸는 곳은 `commentToken`의 `:206` 한 줄뿐이다.**\
`startComment`(`:186`)가 `inCommentIfPresent = true`로, `endComment`(`:194`)가 `false`로 호출하므로, 토큰을 실제로 찾았을 때만 상태가 뒤집힌다.\
상태 변경 지점이 하나라는 점이 이 클래스를 상태 기계로 읽을 수 있게 만든다.

둘째, **`consumeCommentTokens`는 자기 자신을 재귀 호출한다**(`:167`).\
한 줄 안에 주석이 여러 개 있거나, 주석이 줄 중간에서 시작해 줄 끝을 넘어가는 경우를 이 재귀가 흡수한다.\
재귀의 종료 조건은 두 가지다.\
`consume`이 `null`을 돌려줄 때(`:166`의 조건이 거짓)와 조기 반환에 걸릴 때(`:153~157`)다.

> **조기 반환(early return)** — 함수 본체를 다 돌기 전에 특정 조건에서 곧장 값을 돌려주고 빠져나가는 단축 경로.\
> 예: 여기서는 "주석 마커가 한 개도 없는 줄"이 본체를 건너뛰고 바로 반환된다.

셋째, **인스턴스 필드로 상태를 들고 있으므로 검출기는 재진입 불가(non-reentrant)다.**\
대신 `detectValidationMode`가 진입 즉시 `this.inComment = false`로 리셋하므로(`:93`), 같은 인스턴스를 순차적으로 재사용하는 것은 안전하다.\
`XmlBeanDefinitionReader`가 검출기를 `final` 필드 하나로 들고 재사용하는 배치(`XmlBeanDefinitionReader.java:136`)가 이 리셋에 기대고 있다.

> **재진입 불가(non-reentrant)** — 한 실행이 끝나기 전에 같은 객체로 다시 들어오면 서로의 상태를 망가뜨리는 성질.\
> 예: 두 스레드가 같은 검출기의 `detectValidationMode`를 동시에 부르면 `inComment` 하나를 서로 덮어쓴다.

---

## 2. 수정 전 동작 워크플로우

**검출기는 파일을 한 줄씩 읽어 "주석을 걷어낸 나머지"만 판정에 넘기고, `DOCTYPE`을 만나거나 여는 태그를 만나면 즉시 멈춘다.**\
진입점의 루프 구조가 그 계약을 그대로 보여 준다.

```text
 detectValidationMode(inputStream)                                     (:92)
   │
   ├─ this.inComment = false;                                          (:93)  ◀ 상태 리셋
   │
   ├─ try (BufferedReader reader = new BufferedReader(
   │            new InputStreamReader(inputStream)))                   (:96)
   │      boolean isDtdValidated = false;                              (:97)
   │
   │      while ((content = reader.readLine()) != null) {              (:99)
   │        │
   │        ├─ content = consumeCommentTokens(content);               (:100)  ◀ 주석 제거
   │        │      ▶ 주석 필터링의 책임은 전적으로 여기 있다.
   │        │        루프 자신은 inComment 를 다시 확인하지 않는다.
   │        │
   │        ├─ if (!StringUtils.hasText(content)) continue;      (:101~103)  ◀ 빈 줄 건너뛰기
   │        │
   │        ├─ if (hasDoctype(content)) {                             (:104)
   │        │        isDtdValidated = true; break;              (:105~106)
   │        │  }
   │        │
   │        └─ if (hasOpeningTag(content)) break;               (:108~111)  "의미 있는 데이터 끝"
   │      }
   │
   │      return (isDtdValidated ? VALIDATION_DTD : VALIDATION_XSD);   (:113)
   │
   └─ catch (CharConversionException ex)                              (:115)
          return VALIDATION_AUTO;                                     (:118)  ◀ 인코딩 문제는 판단 보류
```

`:100`과 `:101`의 조합이 이 설계의 계약이다.\
`consumeCommentTokens`가 "주석이 아닌 내용"만 돌려주고, 그 결과가 공백이면 루프가 그냥 넘어간다.\
즉 **주석 본문을 걸러 내는 유일한 장치가 "빈 문자열을 돌려주는 것"**이다.\
이 사실이 수정 방향을 결정한다.

아래는 PR이 추가한 픽스처 `spring-core/src/test/resources/org/springframework/util/xml/xsdWithDoctypeInMultiLineCommentBody.xml`을 **수정 전** 코드로 돌렸을 때의 줄별 추적이다.

```text
 입력 파일
   1: <?xml version="1.0" encoding="UTF-8"?>
   2: <!--
   3: \tSee the DOCTYPE notes for legacy configs
   4: -->
   5: <beans xmlns="http://www.springframework.org/schema/beans"
   ...

 줄 1  inComment=false  →  마커 없음 → 조기 반환 (:156) → 줄 전체 반환
       루프: hasText 참 / hasDoctype 거짓 / hasOpeningTag 거짓('<' 다음이 '?')
             → 계속

 줄 2  inComment=false  →  idx("<!--")=0 → 조기 반환 통과, 본체 진입
       앞부분 "" 을 result 로 분리 (:162)
       consume → startComment 히트 → inComment := true  (:206)
       꼬리 "" 재귀 → "" (:167)                        반환: ""
       루프: hasText 거짓 → continue
       inComment: false → true

 줄 3  inComment=true   →  마커 없음 → 조기 반환 (:153)
       수정 전: 상태를 보지 않고 무조건 line 반환      반환: 줄 전체
                루프: hasText 참 / hasDoctype 참
                      → isDtdValidated = true; break     ◀ 결함이 살던 자리
       수정 후: return (this.inComment ? "" : line)     반환: ""
                루프: hasText 거짓 → continue

 줄 4  inComment=true   →  "-->" 포함 → 조기 반환 통과, 본체 진입
       !inComment 거짓이므로 앞부분 분리 안 함 (:161)
       consume → endComment 히트 → inComment := false (:206)
                                                        반환: ""
       루프: hasText 거짓 → continue
       inComment: true → false

 줄 5  inComment=false  →  마커 없음 → 조기 반환 (:156) → 줄 전체 반환
       루프: hasText 참 / hasDoctype 거짓 / hasOpeningTag 참('<' 다음이 'b')
             → break


 수정 전 결과: 3행에서 break → isDtdValidated = true  → VALIDATION_DTD   (오판)
 수정 후 결과: 5행에서 break → isDtdValidated = false → VALIDATION_XSD  (정답)
```

수정 전 코드에서는 4행과 5행이 아예 읽히지 않는다는 점을 눈여겨볼 만하다.\
3행의 `break`(`:106`)가 루프를 끝내므로, 실제 문서가 XSD 설정이라는 증거(`<beans xmlns=... xsi:schemaLocation=...>`)는 판정에 참여하지 못한다.

두 번째 시나리오로 재귀가 실제로 도는 경우를 보자.\
기존 픽스처 `xsdWithDoctypeInOpenCommentWithAdditionalCommentOnSameLine.xml`의 3행은 한 줄 안에서 상태가 두 번 뒤집힌다.\
이 경로는 수정 전후로 동일하다.

```text
 입력 3행 (진입 시 inComment = true, 2행의 "<!--" 때문)
   <!DOCTYPE beans PUBLIC "..."> -->    <!-- additional comment on same line -->
   └──────── 주석 본문 ─────────┘└┬┘    └────── 두 번째 주석 ──────────────┘
                                  종료

 consumeCommentTokens(3행)                                            (:151)
   idx("<!--") = 두 번째 주석 위치 (≠ -1) → 조기 반환 통과            (:152)
   !inComment 거짓 → 앞부분 분리 안 함 (currLine = 줄 전체)      (:161~164)
   consume(currLine)                                                  (:166)
     inComment=true → endComment → "-->" 히트 → inComment := false
     반환: "    <!-- additional comment on same line -->"
   ├─ 재귀 1                                                          (:167)
   │    idx("<!--") = 4 → 조기 반환 통과
   │    !inComment 참 && idx>=0 → result = "    " (앞 4칸 공백)       (:162)
   │                              currLine = "<!-- additional ... -->"(:163)
   │    consume → startComment 히트 → inComment := true
   │      반환: " additional comment on same line -->"
   │    ├─ 재귀 2
   │    │    idx = -1 이지만 "-->" 포함 → 조기 반환 통과
   │    │    consume → endComment 히트 → inComment := false
   │    │      반환: ""
   │    │    └─ 재귀 3: "" → 조기 반환, inComment=false → ""
   │    │    결과 ""
   │    결과: "    " + "" = "    "
   결과: "" + "    " = "    "
   │
   ▼ 루프: hasText("    ") 거짓 → continue                            (:101)
```

이 추적이 보여 주는 것은 **주석 마커가 하나라도 있는 줄은 조기 반환을 지나쳐 본체의 재귀로 들어간다**는 사실이다.\
본체는 `inComment`를 성실히 확인한다(`:161`, `:177`).\
그래서 gh-27915가 추가한 기존 픽스처들은 전부 정상 동작했고, **마커가 전혀 없는 순수 본문 줄만이 잔여 사례로 남았다.**

> **잔여 사례(residual case)** — 예전 수정이 문제의 일부만 덮어서, 아직 고쳐지지 않은 채 남아 있는 나머지 경우.\
> 예: gh-27915는 마커가 같은 줄에 있는 경우만 덮었고, 마커가 전혀 없는 본문 줄이 남았다.

---

## 3. 분기 처리 워크플로우 — 상태 전이도

**상태는 `inComment` 하나로 `OUT`(주석 밖)과 `IN`(주석 안) 두 개뿐이고, 전이를 일으키는 사건은 토큰 발견 두 가지뿐이다.**\
아래가 그 전이도이며, `[BUG]`로 표시한 자기 루프가 결함이 살던 전이다.

> **자기 루프(self-loop)** — 상태 전이도에서 사건을 처리한 뒤에도 같은 상태에 그대로 머무는 전이.\
> 예: 주석 안에서 마커 없는 줄을 만나면 여전히 주석 안이므로, `IN`에서 `IN`으로 돌아오는 화살표가 된다.

```text
                         ┌──────────────────────────┐
                         │  detectValidationMode    │
                         │  진입 (:93) inComment=false│
                         └────────────┬─────────────┘
                                      ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │                        상태 OUT  (inComment == false)                │
   │                   "여기서 나온 텍스트는 판정 대상"                    │
   └──────────────────────────────────────────────────────────────────────┘
        │  ▲                                                        │
        │  │                                                        │  자기 루프
        │  │                                                        │  마커 없는 줄
        │  │                                                        │  → 조기 반환 (:156)
        │  │                                                        │  → 줄 전체가 내용
        │  │                                                        └──▶ (정상)
        │  │
        │  │  사건 B: "-->" 발견
        │  │    endComment (:193) → commentToken(line,"-->",false)  (:206)
        │  │    inComment := false, 토큰 뒤부터 계속 소비            (:208)
        │  │
        │  │                              사건 A: "<!--" 발견
        │  │                                startComment (:185)
        │  │                                → commentToken(line,"<!--",true) (:206)
        │  │                                inComment := true
        │  │                                토큰 앞부분은 내용으로 보존 (:162)
        │  │                                토큰 뒤부터 계속 소비      (:163, :208)
        │  │                                        │
        │  └────────────────────────────────────────┼───────────────┐
        │                                           ▼               │
   ┌──────────────────────────────────────────────────────────────────────┐
   │                        상태 IN  (inComment == true)                  │
   │                   "여기서 나온 텍스트는 판정 대상이 아니어야"          │
   └──────────────────────────────────────────────────────────────────────┘
                                      │
                                      │  자기 루프: 마커 없는 줄
                                      │    → 조기 반환 (:153)
                                      │
                                      │  [BUG] 수정 전:  return line;
                                      │        줄 전체가 "내용"으로 루프에 넘어간다
                                      │        → hasDoctype 이 산문 속 DOCTYPE 을 잡는다
                                      │
                                      │  수정 후:  return (this.inComment ? "" : line);
                                      │        → "" 가 :101 의 hasText 필터에 걸려 폐기
                                      └──▶ (여러 줄 주석의 본문 줄)
```

이제 같은 것을 코드 경로 분기도로 펼치면, 조기 반환이 상태 기계의 어느 자리에 있는지 정확히 보인다.

```text
 루프 1회 (한 줄 처리)                        XmlValidationModeDetector.java:99
 │
 ├── consumeCommentTokens(line)                                      (:151)
 │   │
 │   ├── 분기 1: 조기 반환 게이트                                     (:152~157)
 │   │   조건: indexOf("<!--") == -1  AND  !contains("-->")
 │   │   │      "이 줄에는 걷어낼 주석 경계가 없다"
 │   │   │
 │   │   ├─ 조건 거짓 ──────────────────────▶ 분기 2로 (본체)
 │   │   │
 │   │   └─ 조건 참
 │   │        │
 │   │        ├─ inComment == false ────────▶ return line     (:156)
 │   │        │     "주석 밖의 마커 없는 줄 = 전부 내용"  (정상)
 │   │        │
 │   │        └─ inComment == true  ────────▶ [BUG] 수정 전: return line
 │   │              "주석 안의 마커 없는 줄 = 전부 주석 본문"
 │   │                                        수정 후: return ""      (:156)
 │   │
 │   ├── 분기 2: 앞부분 분리                                    (:161~164)
 │   │   조건: !inComment  AND  indexOf("<!--") >= 0
 │   │   │
 │   │   ├─ 참 ─── result  = line[0 .. idx)   ◀ 주석 앞은 진짜 내용   (:162)
 │   │   │         currLine = line[idx ..]                            (:163)
 │   │   │
 │   │   └─ 거짓 ─ result  = ""  (초기값)                             (:159)
 │   │             currLine = line                                    (:160)
 │   │             ▶ inComment == true 이거나, OUT인데 "-->"만 있는 줄.
 │   │               후자는 앞부분을 내용으로 살리지 않고 통째로 버린다.
 │   │
 │   └── 분기 3: 토큰 소비와 재귀                                (:166~169)
 │       consume(currLine)                                            (:176)
 │       │   inComment ? endComment(line) : startComment(line)        (:177)
 │       │
 │       ├─ 토큰 못 찾음 → index == -1 → consume 이 null 반환   (:178)
 │       │     ▶ 재귀 종료. 지금까지의 result 를 반환.                (:169)
 │       │
 │       └─ 토큰 찾음 → inComment 뒤집힘 (:206), 꼬리 반환 (:208)
 │             result += consumeCommentTokens(꼬리)                   (:167)
 │             ▶ 같은 줄 안에서 상태가 여러 번 뒤집힐 수 있다.
 │
 ├── 분기 4: 빈 내용 필터                                            (:101)
 │   !StringUtils.hasText(content) ──────────▶ continue (다음 줄)
 │   ▶ 수정이 만들어 낸 "" 가 여기서 걸러진다. 이 필터가 있기에
 │     수정은 새 분기를 만들지 않고 기존 필터에 태우는 것으로 끝난다.
 │
 ├── 분기 5: DOCTYPE 판정                                     (:104, :126)
 │   content.contains("DOCTYPE") ────────────▶ isDtdValidated = true; break
 │   ▶ inComment 가드가 없다.  "<!DOCTYPE" 형태의 진짜 선언이 아니라
 │     산문 속 단어 하나로도 걸린다.
 │
 └── 분기 6: 여는 태그 판정                                   (:108, :137)
     if (this.inComment) return false;   ◀ 여기에는 가드가 있다 (:138)
     '<' 다음 문자가 letter 인가                                (:141~143)
     ──────────────────────────────────────▶ break ("의미 있는 데이터 끝")
```

분기 5와 분기 6의 비대칭이 이 결함의 표지판이었다.\
같은 층위의 두 판정 메서드가 같은 위험(주석 안의 텍스트가 내용으로 넘어옴)에 대해 한쪽만 방어하고 있었다.\
`hasOpeningTag`의 Javadoc(`:132~135`)은 그 가드를 "sanity check"라 부르며 "원칙적으로는 주석이 이미 다 걷혔어야 하지만"이라는 단서를 단다.\
그 단서가 참이 아닌 경우가 정확히 분기 1의 `[BUG]` 갈래였다.

> **sanity check(온전성 검사)** — "여기까지 왔으면 당연히 참이어야 하는 조건"을 혹시 몰라 한 번 더 확인해 두는 방어 코드.\
> 예: `hasOpeningTag`의 `if (this.inComment) return false;`(`:138`)가 그것이다.

`consumeCommentTokens`의 Javadoc(`:146~150`)도 이 PR의 근거로 읽힌다.\
"Consume all comments in the given String and return the remaining content, **which may be empty since the supplied content might be all comment data**"와 "This method **takes the current 'in comment' parsing state into account**"라는 두 문장이 이미 선언돼 있었다.\
여러 줄 주석의 본문 줄이야말로 "all comment data"의 교과서적 사례이고, 조기 반환만이 그 선언을 지키지 않았다.\
수정은 새 규칙을 도입한 것이 아니라 선언된 규칙을 코드가 지키게 한 것이다.

---

## 4. 스프링 전역에서의 자리

**이 검출기는 `spring-beans`의 XML 설정 로딩 파이프라인에서, 실제 파싱을 시작하기 전에 파일을 한 번 미리 훑는 사전 단계다.**\
grep으로 확인한 프로덕션 참조는 `XmlBeanDefinitionReader`와 `DefaultDocumentLoader` 두 클래스뿐이며, 실제로 `detectValidationMode`를 호출하는 곳은 `XmlBeanDefinitionReader.java:499` 한 자리다.

```text
 [진입 경로]

  loadBeanDefinitions(Resource)              XmlBeanDefinitionReader.java:317
  loadBeanDefinitions(EncodedResource)       XmlBeanDefinitionReader.java:328
  loadBeanDefinitions(InputSource)           XmlBeanDefinitionReader.java:370
  loadBeanDefinitions(InputSource, String)   XmlBeanDefinitionReader.java:382
        │  (ClassPathXmlApplicationContext 등 XML 기반 컨텍스트의 기동 경로)
        ▼
  doLoadBeanDefinitions(inputSource, resource)   XmlBeanDefinitionReader.java:398
        │
        ▼
  doLoadDocument(inputSource, resource)          XmlBeanDefinitionReader.java:443
        this.documentLoader.loadDocument(
            inputSource, getEntityResolver(), this.errorHandler,
            getValidationModeForResource(resource),   ◀ 여기서 검출기가 불린다 (:445)
            isNamespaceAware());
        │
        ├─▶ getValidationModeForResource(resource)  XmlBeanDefinitionReader.java:456
        │      │
        │      ├─ getValidationMode() != VALIDATION_AUTO ──▶ 그 값 그대로 반환 (:458)
        │      │     ▶ 사용자가 명시했으면 검출 자체를 하지 않는다.
        │      │
        │      ├─ detectValidationMode(resource)            (:461 → :478)
        │      │      │
        │      │      ├─ resource.isOpen() 이면 예외          (:479~485)
        │      │      │     "스트림을 다시 열 수 없는 리소스는 검출 불가"
        │      │      ├─ inputStream = resource.getInputStream()   (:489)
        │      │      └─ this.validationModeDetector
        │      │             .detectValidationMode(inputStream)    (:499)  (*)
        │      │                 └─▶ XmlValidationModeDetector.java:92
        │      │
        │      └─ 검출 결과가 VALIDATION_AUTO 면 XSD 로 가정      (:463~466)
        │
        ▼
  DefaultDocumentLoader#loadDocument             DefaultDocumentLoader.java:69
        │
        ├─ createDocumentBuilderFactory(validationMode, namespaceAware)
        │                                        DefaultDocumentLoader.java:88
        │      if (validationMode != VALIDATION_NONE) {           (:97)
        │          factory.setValidating(true);                   (:98)
        │          if (validationMode == VALIDATION_XSD) {        (:99)
        │              factory.setNamespaceAware(true);          (:101)
        │              factory.setAttribute(SCHEMA_LANGUAGE_ATTRIBUTE,
        │                                   XSD_SCHEMA_LANGUAGE); (:103)
        │          }
        │      }
        │      ▶ DTD 로 판정되면 setValidating(true) 만 켜고
        │        스키마 관련 설정은 하지 않는다.
        │
        └─ builder.parse(inputSource)            DefaultDocumentLoader.java:77
```

(*) 표시한 `XmlBeanDefinitionReader.java:499`가 이 클래스로 들어오는 유일한 프로덕션 진입점이다.\
검출기 인스턴스는 리더의 `final` 필드 하나로 재사용되며(`XmlBeanDefinitionReader.java:136`), 리더는 검출기의 상수들을 자기 이름으로 다시 노출한다(`XmlBeanDefinitionReader.java:86~101`).

**오판의 대가는 조용한 성능 저하가 아니라 기동 실패다.**\
XSD 문서를 DTD 모드로 파싱하면 `DefaultDocumentLoader.java:98`이 `setValidating(true)`만 켠 채 파서를 만들고, 파서는 DTD 문법을 기대하는데 문서에 `DOCTYPE`이 없으므로 검증 오류를 보고한다.\
그 오류는 `XmlBeanDefinitionReader`의 오류 처리기를 거쳐 `doLoadBeanDefinitions`의 `catch (SAXParseException ex)`(`XmlBeanDefinitionReader.java:412`)에 잡히고, `XmlBeanDefinitionStoreException`으로 감싸져 컨텍스트 기동을 중단시킨다.

> **SAXParseException** — XML 파서가 문서를 읽다가 문법·검증 오류를 만났을 때 던지는 예외.\
> 예: DTD 모드로 켠 파서가 `DOCTYPE` 없는 문서를 만나면 검증 오류로 이 예외가 나온다.

XXE(XML External Entity) 맥락은 정확히 선을 그어야 한다.\
**이 검출기는 XXE 방어 장치가 아니다.**\
`DOCTYPE`을 찾는 목적은 외부 엔티티 차단이 아니라 검증 문법 선택이다.\
`DefaultDocumentLoader`의 소스 주석이 그 판단을 명시해 두고 있다(`DefaultDocumentLoader.java:91~93`).

> **XXE(XML External Entity)** — XML 문서의 `DOCTYPE` 선언으로 외부 파일이나 URL을 끌어오게 만들어 정보를 빼내는 공격 기법.\
> 예: 공격자가 설정 파일에 외부 엔티티 선언을 심어 서버의 로컬 파일을 읽어 가게 만드는 것.

```java
// This document loader is used for loading application configuration files.
// As a result, attackers would need complete write access to application configuration
// to leverage XXE attacks. This does not qualify as privilege escalation.
```

다만 `DOCTYPE` 문자열의 존재 여부가 파서 구성 방식을 바꾸는 것은 사실이므로, 검출 판정의 신뢰성 요구는 그대로다.\
이 PR이 고치는 것이 그 신뢰성이다.

---

## 5. 관련 개념

`../../concepts/`에는 이 문서가 참조할 만한 기존 개념 문서가 없으므로, 필요한 개념을 여기에 직접 서술한다.

### 5.1 DTD와 XSD — 왜 미리 알려 줘야 하는가

XML에는 두 가지 스키마 체계가 공존한다.\
문서 상단의 `<!DOCTYPE ...>` 선언으로 DTD를 가리키는 옛 방식과, 루트 태그의 `xsi:schemaLocation` 속성으로 XSD를 가리키는 현대 방식이다.\
JAXP의 `DocumentBuilderFactory`는 이 둘을 자동으로 구분해 주지 않는다.\
검증을 켜려면 어느 쪽인지 **파서를 만들기 전에** 알려 줘야 한다.

> **DTD(Document Type Definition)** — XML 문서의 구조 규칙을 적어 두는 옛 방식의 스키마.\
> 예: `<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN 2.0//EN" ...>` 선언이 그 스키마를 가리킨다.

> **XSD(XML Schema Definition)** — XML 자체 문법으로 쓰인 현대식 스키마.\
> 예: 루트 태그의 `xsi:schemaLocation="... spring-beans.xsd"`가 그 스키마 위치를 가리킨다.

> **JAXP** — 자바 표준 XML 처리 API 묶음.\
> 예: `DocumentBuilderFactory`로 파서를 만들고 `builder.parse(...)`로 DOM을 얻는 것이 그 API다.

그래서 Spring은 같은 파일을 두 번 읽는다.\
첫 번째 읽기가 이 검출기이고(`XmlBeanDefinitionReader.java:499`), 그 결론으로 파서를 구성한 뒤(`DefaultDocumentLoader.java:88`) 두 번째 읽기에서 실제 DOM을 만든다(`DefaultDocumentLoader.java:77`).\
검출기가 완전한 XML 파서가 아니라 문자열 스캐너인 이유가 여기 있다.\
파서를 만들기 위한 정보를 얻는 단계이므로 파서를 쓸 수 없다.

```text
 같은 파일을 두 번 읽는다

 1차 읽기 - 문자열 스캐너                  2차 읽기 - 진짜 XML 파서
 +-------------------------------+       +---------------------------------+
 | XmlValidationModeDetector     |       | DocumentBuilder                 |
 |   detectValidationMode(...)   |       |   builder.parse(inputSource)    |
 |   호출: XmlBeanDefinition     |       |   DefaultDocumentLoader.java:77 |
 |         Reader.java:499       |       |                                 |
 +-------------------------------+       +---------------------------------+
        |                                           ^
        | 결과: VALIDATION_DTD(2)                   | 입력: 1차 결론대로
        |       또는 VALIDATION_XSD(3)              |       구성된 파서
        v                                           |
   createDocumentBuilderFactory(mode, nsAware) -----+
   DefaultDocumentLoader.java:88
     mode != NONE -> setValidating(true)          :98
     mode == XSD  -> setNamespaceAware(true)      :101
                     setAttribute(SCHEMA_...)     :103

 1차가 파서를 못 쓰는 이유: 파서를 만들려면 1차의 결론이 먼저 있어야 한다
```

### 5.2 조기 반환이 상태 기계의 사각지대가 되는 이유

`consumeCommentTokens`의 본체(`:159~169`)는 `inComment`를 두 곳에서 확인한다.\
앞부분을 분리할지 정할 때(`:161`)와 어떤 토큰을 찾을지 정할 때(`:177`)다.\
반면 앞에 붙은 조기 반환(`:152~157`)은 상태를 전혀 보지 않았다.

조기 반환의 조건 `indexOf("<!--") == -1 && !contains("-->")`가 암묵적으로 가정한 것은 "마커가 없으면 주석 밖"이다.\
이 가정은 대부분 맞지만, 정확히 한 값에서 틀린다.\
여러 줄 주석의 본문 줄이 그것이다.\
**상태를 들고 다니는 메서드에 짧은 단축 경로를 낼 때는 그 경로가 상태의 모든 값에 대해 옳은지 따져야 한다**는 것이 이 결함의 일반형이다.

수정이 새 분기를 만들지 않고 삼항식 하나로 끝난 것도 구조 덕분이다.\
루프에 이미 빈 내용 필터(`:101`)가 있으므로, 주석 본문 줄을 `""`로 만들기만 하면 기존 필터가 나머지를 처리한다.

> **삼항식(ternary expression)** — `조건 ? A : B` 형태로 조건에 따라 두 값 중 하나를 고르는 짧은 식.\
> 예: `return (this.inComment ? "" : line);`이 그것이다.

### 5.3 이 구멍이 생긴 이력

2022년 커밋 `4b1b25496bf`(gh-27915, "Improve comment parsing in DTD/XSD detection algorithm")가 지금의 재귀 알고리즘을 도입하면서 루프의 가드를 함께 제거했다.

```diff
-				if (this.inComment || !StringUtils.hasText(content)) {
+				if (!StringUtils.hasText(content)) {
```

그 전까지는 루프(`:101` 자리)가 `this.inComment`를 직접 확인해 주석 안이면 무조건 건너뛰었다.\
새 알고리즘은 그 책임을 `consumeCommentTokens`로 옮겼는데, 조기 반환 경로만 상태 확인 없이 남으면서 방어선이 한 겹 사라졌다.\
즉 이 결함은 **책임 이전이 완결되지 않은 자리**에 생긴 것이며, 기존 수정이 있는 자리를 다시 고칠 때 그 수정이 무엇을 옮기고 무엇을 지웠는지 확인하는 것이 잔여 사례를 찾는 지름길이라는 사례가 된다.

같은 입력(마커 없는 주석 본문 줄)을 두 시기에 각각 넣어 보면 방어선이 어디서 사라졌는지가 보인다.

```text
 gh-27915 이전                             gh-27915 이후 (이 PR 직전)
 +-----------------------------------+    +-----------------------------------+
 | 루프 :101                         |    | 루프 :101                         |
 |   if (this.inComment ||           |    |   if (!hasText(content))          |
 |       !hasText(content))          |    |     continue;                     |
 |     continue;                     |    |                                   |
 |   -> 주석 안이면 무조건 건너뛴다   |    |   -> inComment 를 보지 않는다      |
 +-----------------------------------+    +-----------------------------------+
 | 주석 제거 책임: 루프가 함께 짐     |    | 주석 제거 책임:                   |
 |                                   |    |   consumeCommentTokens 로 이전    |
 |                                   |    |     본체    : inComment 확인 O    |
 |                                   |    |     조기반환: inComment 확인 X    |
 |                                   |    |                        <- 구멍    |
 +-----------------------------------+    +-----------------------------------+
   결과: 줄이 판정에 도달하지 않는다        결과: 줄 전체가 내용으로 흘러나와
                                                 hasDoctype 이 참이 된다
```

### 5.4 `hasDoctype`이 부분 문자열 매칭인 것의 의미

`hasDoctype`은 `content.contains(DOCTYPE)`(`:127`)일 뿐이다.\
`<!DOCTYPE` 형태의 진짜 선언을 파싱하지 않으므로, 산문 속 단어 하나로도 참이 된다.\
PR이 추가한 픽스처의 "See the DOCTYPE notes for legacy configs"가 정확히 그런 경우이며, XSD로 이관하면서 옛 설정에 대한 안내를 주석으로 남기는, 충분히 있을 법한 문장이다.

이 느슨함 자체를 조이는 대안(`<!DOCTYPE` 전체를 요구하도록 바꾸기)도 상상할 수 있지만 그 방향은 채택되지 않았다.\
검출기는 완전한 파서가 아니라 휴리스틱 스캐너이고, 판정 기준을 조이면 공백이나 개행이 낀 변형 선언을 놓칠 위험이 생긴다.\
대신 `hasOpeningTag`와 대칭이 되도록 `hasDoctype`에도 `if (this.inComment) return false;` 가드를 추가하는 안이 PR 본문에서 제안되었으나, 근본 원인은 조기 반환의 상태 무시이고 가드 추가는 증상 차단이라는 판단으로 적용되지 않았다.

> **휴리스틱 스캐너(heuristic scanner)** — 정확한 문법 해석 대신 몇 가지 어림 규칙만으로 필요한 정보를 뽑아내는 간이 읽기 장치.\
> 예: 이 검출기는 `DOCTYPE`·`<!--`·`-->` 세 문자열만 보고 판정한다.

### 5.5 상태 필드와 인스턴스 재사용

`inComment`(`:81`)는 인스턴스 필드이므로 검출기는 동시 호출에 안전하지 않다.\
그러나 `detectValidationMode`가 진입 즉시 `false`로 리셋하므로(`:93`) 순차 재사용은 안전하다.\
`XmlBeanDefinitionReader`가 검출기를 `final` 필드로 하나만 들고 모든 리소스에 재사용하는 배치(`XmlBeanDefinitionReader.java:136`)가 이 리셋에 기대고 있고, 테스트가 파라미터화 케이스들 사이에서 같은 인스턴스를 공유해도 오염되지 않는 이유도 같다.
