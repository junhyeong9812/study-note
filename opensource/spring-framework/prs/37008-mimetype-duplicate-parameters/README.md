# PR #37008 — Reject MIME type parameters differing only in case

## 0. 정향

이 PR은 `Content-Type: text/plain;dupe="1";DUPE="2"` 처럼 **대소문자만 다른 중복 파라미터**가 예외 없이 통과하던 문제를 고친다.\
고친 지점은 `spring-core`의 `MimeTypeUtils.MimeTypeParser#putParameter` 한 곳이고, 본문 변경은 사실상 누산용 맵을 `LinkedHashMap`에서 `LinkedCaseInsensitiveMap`으로 바꾼 세 줄이다.

다만 그 세 줄이 왜 정답인지 알려면 두 가지를 먼저 봐야 한다.\
MIME 타입 파서가 파라미터를 어떻게 모으는지, 그리고 `MimeType` 자신은 파라미터 이름을 어떤 규칙으로 다루는지다.\
이 문서는 그 맥락에서 출발해 재현·수정·검증 순으로 따라간다.

> **MIME 타입(미디어 타입)** — 내용물의 종류를 `type/subtype` 한 쌍으로 적고, 뒤에 부가 정보를 `;이름=값`으로 붙이는 문자열 형식.\
> 예: `text/plain;charset=utf-8`에서 `text`가 type, `plain`이 subtype, `charset=utf-8`이 파라미터다.

> **파라미터(parameter)** — 미디어 타입 뒤에 `;`로 이어 붙는 `이름=값` 한 쌍.\
> 예: `text/plain;dupe="1";DUPE="2"`에는 이름이 `dupe`인 것과 `DUPE`인 것, 둘이 붙어 있다.

- PR: https://github.com/spring-projects/spring-framework/pull/37008
- 브랜치: `fix/mimetype-duplicate-parameter-case` (커밋 `019c822ff69`)
- 변경 파일: `spring-core/src/main/java/org/springframework/util/MimeTypeUtils.java`, `spring-core/src/test/java/org/springframework/util/MimeTypeTests.java`
- 상태: OPEN (라벨 `status: waiting-for-triage`, `in: web` / 리뷰어 요청 `bclozel`)

## 1. 배경 — MIME 타입 파라미터는 어떻게 파싱되는가

### 1.1 문자열이 객체가 되는 유일한 길목

`MimeType`은 `type/subtype;name=value;name=value` 형태의 문자열을 표현하는 값 객체이고, 그 문자열을 객체로 바꾸는 책임은 `MimeTypeUtils`가 진다.\
진입점은 `MimeTypeUtils.parseMimeType(String)`이며, `MediaType.parseMediaType`, `MimeType.valueOf`, HTTP `Content-Type`·`Accept` 헤더 처리가 모두 결국 이 길목을 지난다.\
즉 서버로 들어오는 거의 모든 미디어 타입 문자열이 여기를 통과한다.

> **값 객체(value object)** — 식별자가 아니라 담고 있는 값 자체로 동일성이 정해지는 불변 객체.\
> 예: `text/plain;charset=utf-8`을 두 번 파싱해 얻은 두 `MimeType`은 서로 다른 인스턴스여도 같은 것으로 취급된다.

```java
public static MimeType parseMimeType(String mimeType) {
    if (!StringUtils.hasLength(mimeType)) {
        throw new InvalidMimeTypeException(mimeType, "'mimeType' must not be empty");
    }
    // do not cache multipart mime types with random boundaries
    if (mimeType.startsWith("multipart")) {
        return parseMimeTypeInternal(mimeType);
    }
    return cachedMimeTypes.get(mimeType);
}
```
(`MimeTypeUtils#parseMimeType`)

### 1.2 파서는 상태 기계다

2026년 7월 커밋 `0799920` "Improve MimeType parser for RFC compliance"(gh-36729, Brian Clozel)가 이 파서를 통째로 다시 썼다.\
그전에는 문자열을 인덱스로 잘라 나가는 절차형 코드였지만, 지금은 입력을 한 글자씩 먹으면서 상태를 옮기는 **상태 기계(state machine)** 다.\
실제 루프는 다음 한 덩어리가 전부다.

> **상태 기계(state machine)** — 현재 상태와 들어온 입력 하나로 다음 상태를 정하는 방식의 계산 모델.\
> 예: 여기서는 `SUBTYPE` 상태에서 `;`를 만나면 subtype을 확정하고 `WHITESPACE` 상태로 넘어간다.

```java
private MimeType parse() {
    ParserState state = ParserState.INITIAL;
    for (; this.index < this.input.length(); this.index++) {
        char c = this.input.charAt(this.index);
        state = state.process(c, this);
    }
    state.onEof(this);
    if (this.parsed == null) {
        throw new InvalidMimeTypeException(this.input, "'mimeType' must not be empty");
    }
    return this.parsed;
}
```
(`MimeTypeUtils.MimeTypeParser#parse`)

상태는 `ParserState` enum에 정의돼 있고 `INITIAL -> TYPE -> SUBTYPE -> WHITESPACE -> PARAM_NAME -> PARAM_NAME_END -> PARAM_VALUE_START -> PARAM_VALUE_TOKEN | PARAM_VALUE_QUOTED -> PARAM_VALUE_ESCAPED` 로 이어진다.\
파서 인스턴스(`MimeTypeParser`)는 상태들이 공유하는 가변 컨텍스트 역할을 하며 `index`, `mark`, `type`, `subtype`, `parameters`, `paramName` 필드를 들고 있다.\
각 상태는 구분자를 만나면 `mark`부터 현재 위치까지를 잘라 컨텍스트에 쓰고 다음 상태를 반환한다.

파라미터 하나가 완성되는 순간은 값 상태가 종료될 때다.\
`PARAM_VALUE_TOKEN`은 `;`·공백·탭에서, `PARAM_VALUE_QUOTED`는 닫는 `"`에서 값을 확정하고, 입력이 그대로 끝나면 각 상태의 `onEof`가 마지막 조각을 흘려보낸다.\
그 공통 경로가 `extractParameter`다.

```java
private static void extractParameter(MimeTypeParser parser, String input) {
    Assert.hasText(parser.paramName, "'paramName' must not be empty");
    parser.putParameter(parser.paramName, input);
}
```
(`MimeTypeUtils.ParserState#extractParameter`)

### 1.3 RFC가 정한 규칙 — 파라미터 이름은 대소문자를 가리지 않는다

여기서 중요한 규칙 하나가 RFC 쪽에서 온다.\
**MIME 파라미터 이름은 대소문자를 구분하지 않는다.**\
RFC 2045 §5.1은 type·subtype·파라미터 이름이 case-insensitive라고 못박고, HTTP 명세도 같은 입장이다.\
그래서 `charset=utf-8`과 `CHARSET=utf-8`은 같은 파라미터를 가리킨다.

> **RFC 2045 §5.1 / RFC 6838 §4.3** — MIME 형식을 규정하는 표준 문서의 해당 조항.\
> 예: 전자는 "파라미터 이름은 대소문자 무시"를, 후자는 "같은 파라미터가 두 번 나오면 오류"를 정한다 — 이 PR의 근거 두 줄이 정확히 이 둘이다.

`MimeType`도 그 규칙을 코드로 지키고 있다.\
생성자가 받은 파라미터를 자기 맵으로 복사할 때 `LinkedCaseInsensitiveMap`을 쓴다.

```java
private Map<String, String> createParametersMap(@Nullable Map<String, String> parameters) {
    if (!CollectionUtils.isEmpty(parameters)) {
        Map<String, String> map = new LinkedCaseInsensitiveMap<>(parameters.size(), Locale.ROOT);
        parameters.forEach((parameter, value) -> {
            checkParameters(parameter, value);
            map.put(parameter, value);
        });
        return Collections.unmodifiableMap(map);
    }
    else {
        return Collections.emptyMap();
    }
}
```
(`MimeType#createParametersMap`)

`LinkedCaseInsensitiveMap`은 "키의 원래 순서와 원래 대소문자를 보존하면서, 조회·포함·삭제는 어떤 대소문자로도 되게 하는" `LinkedHashMap` 변종이다.\
`Locale.ROOT`를 넘기는 이유는 키 정규화(소문자 변환)를 로케일에 좌우되지 않게 하기 위해서다.\
터키어 로케일의 점 없는 i 같은 함정을 피하는 관용구다.\
덕분에 `getParameter("CHARSET")`과 `getParameter("charset")`은 같은 값을 돌려준다.

> **`LinkedHashMap`** — 넣은 순서를 기억하는 자바 표준 맵.\
> 예: 키를 글자 그대로 비교하므로 `dupe`와 `DUPE`는 서로 다른 두 칸을 차지한다.

> **`LinkedCaseInsensitiveMap`** — 스프링이 만든 `LinkedHashMap` 변종. 표기와 순서는 보존하되 키 비교만 대소문자를 무시한다.\
> 예: `put("dupe", ...)` 뒤에 `put("DUPE", ...)`를 하면 새 칸을 만들지 않고 앞 항목을 대체한다.

> **`Locale.ROOT`** — 어느 나라 말에도 치우치지 않는 중립 로케일.\
> 예: 키를 소문자로 바꿀 때 이것을 주지 않으면 터키어 로케일에서 `I`가 점 없는 소문자로 변해 `charset`과 `Charset`이 다른 키가 될 수 있다.

## 2. 수정 전 동작 방식 — 중복 파라미터는 어떻게 걸렀나

### 2.1 중복 검사는 `put`의 반환값으로 한다

중복 파라미터를 거절하는 규칙 자체는 이 PR 이전에 이미 있었다.\
커밋 `25e8395df80` "Reject duplicate MIME type parameters"(gh-36841)가 RFC 6838 §4.3을 근거로 `text/plain; dupe=1; dupe=2` 같은 입력을 오류로 처리하도록 바꿨다.\
그전에는 뒤 값이 앞 값을 조용히 덮어썼다.

그 검사는 별도의 조회 로직이 아니라 `Map#put`의 반환값을 쓰는 방식으로 구현됐다.\
파서가 파라미터를 누적하는 맵에 넣을 때, `put`이 `null`이 아닌 이전 값을 돌려주면 그 키가 이미 있었다는 뜻이므로 예외를 던진다.\
상태 기계로 재작성된 지금도 이 아이디어는 그대로 살아 있고, 위치만 `MimeTypeParser#putParameter`로 옮겨졌다.

```java
private void putParameter(String name, String value) {
    if (this.parameters == null) {
        this.parameters = new LinkedHashMap<>(4);
    }
    if (this.parameters.put(name, value) != null) {
        throw new InvalidMimeTypeException(this.input, "duplicate parameter '" + name + "=" + value + "'");
    }
}
```
(수정 전 `MimeTypeUtils.MimeTypeParser#putParameter`)

### 2.2 파라미터 맵은 두 번 등장한다

여기서 파싱의 전체 서사를 정리하면 이렇다.\
상태 기계가 파라미터를 하나씩 확정할 때마다 `putParameter`가 **누산 맵**에 담고, 입력이 끝나면 `buildMimeType`이 그 누산 맵을 `MimeType` 생성자에 넘긴다.

> **누산 맵 / 결과 맵** — 앞은 파서가 파싱 도중 파라미터를 모아 두는 임시 맵, 뒤는 완성된 `MimeType`이 최종 보관하는 맵.\
> 예: `dupe="1"`은 먼저 누산 맵에 들어갔다가, `new MimeType(...)` 시점에 결과 맵으로 복사된다.

```java
private MimeType buildMimeType() {
    if (MimeType.WILDCARD_TYPE.equals(this.type) && !MimeType.WILDCARD_TYPE.equals(this.subtype)) {
        throw new InvalidMimeTypeException(this.input, "wildcard type is legal only in '*/*' (all mime types)");
    }
    try {
        return new MimeType(this.type, this.subtype, this.parameters);
    }
    ...
}
```
(`MimeTypeUtils.MimeTypeParser#buildMimeType`)

문자열 한 개가 `MimeType` 하나가 되기까지, 파라미터가 어디서 맵에 들어가고 어디서 검사를 받는지를 세로로 펴면 이렇다.

```text
"text/plain;dupe=\"1\";DUPE=\"2\""      입력 문자열 한 개
        |
        v
MimeTypeUtils.parseMimeType             빈 문자열 거르고 캐시 조회
        |
        v
MimeTypeParser.parse()                  한 글자씩 먹으며 상태 전이
        |
        +--> type    = "text"           TYPE 상태가 '/' 에서 확정
        +--> subtype = "plain"          SUBTYPE 상태가 ';' 에서 확정
        |
        v
extractParameter(parser, value)         파라미터 확정 경로가 모두 여기로 모인다
        |
        v
putParameter(name, value)               [검사 1] 누산 맵에 넣는 지점
        |                                   put 반환값 != null 이면 중복 예외
        v
buildMimeType()
        |
        v
new MimeType(type, subtype, 누산 맵)
        |
        v
createParametersMap(누산 맵)            누산 맵 -> 결과 맵 복사
        |
        +--> checkParameters(k, v)      [검사 2] 이름·값이 토큰 형식인가
        +--> map.put(k, v)              LinkedCaseInsensitiveMap 에 담는다
                                            put 반환값은 람다가 버린다
```

파라미터에 걸리는 검사는 두 군데뿐이다 — 누산 맵에 넣을 때의 중복 검사와, 결과 맵으로 복사할 때의 토큰 형식 검사다.

> **토큰(token)** — RFC 2616 2.2가 정한, 따옴표 없이 쓸 수 있는 문자들로만 이루어진 낱말.\
> 예: `checkParameters`는 이름이 토큰인지, 값이 토큰이거나 따옴표로 감싼 문자열인지만 보고 대소문자는 보지 않는다.

즉 파라미터 맵은 두 개다.\
파서가 파싱 도중 쓰는 **누산 맵**과, `MimeType`이 최종적으로 보관하는 **결과 맵**.\
중복 검사는 전자에서, 대소문자 무시 조회는 후자에서 일어난다.\
문제는 정확히 이 둘의 규칙이 서로 달랐다는 데 있다.

## 3. 무엇이 문제였나 — 케이스만 다른 중복은 검사망을 빠져나간다

### 3.1 검사망을 통과하고, 그다음 조용히 사라진다

누산 맵이 `LinkedHashMap`이라 `dupe`와 `DUPE`를 서로 다른 키로 취급한다는 것이 문제의 전부다.\
서로 다른 키이므로 두 번째 `put`은 이전 값이 아니라 `null`을 돌려주고, 중복 검사는 발동하지 않는다.\
파싱은 그대로 성공한다.

그다음이 더 나쁘다.\
검사망을 통과한 두 항목은 `MimeType` 생성자에서 `LinkedCaseInsensitiveMap`으로 복사되는데, 이 맵은 두 키를 같은 키로 본다.\
그래서 앞 항목이 조용히 사라지고 뒤 항목만 남는다.\
`LinkedCaseInsensitiveMap#put`의 구현이 그 동작을 그대로 보여준다.

```java
@Override
public @Nullable V put(String key, @Nullable V value) {
    String oldKey = this.caseInsensitiveKeys.put(convertKey(key), key);
    V oldKeyValue = null;
    if (oldKey != null && !oldKey.equals(key)) {
        oldKeyValue = this.targetMap.remove(oldKey);
    }
    V oldValue = this.targetMap.put(key, value);
    return (oldKeyValue != null ? oldKeyValue : oldValue);
}
```
(`LinkedCaseInsensitiveMap#put`)

`put("DUPE", "\"2\"")`는 정규화 키 `dupe`가 이미 있음을 발견하고 기존 항목 `dupe -> "1"`을 `targetMap`에서 제거한 뒤 `DUPE -> "2"`를 넣는다.\
반환값은 제거된 `"1"`이다.\
문제는 이 반환값을 파서가 아니라 `createParametersMap`의 `forEach`가 받고 버린다는 점이다.\
아무도 보지 않는 곳에서 값이 하나 증발한다.\
gh-36841이 없애려던 "조용히 마지막 값만 남기는" 동작이 케이스가 다른 경우에만 그대로 살아남아 있었던 셈이다.

> **무음 실패(silent failure)** — 잘못된 결과가 예외도 로그도 없이 정상처럼 흘러가는 실패.\
> 예: `dupe="1"`이 사라진 채 파싱이 성공하므로, 호출자는 자기가 보낸 파라미터 하나가 없어졌다는 사실을 알 길이 없다.

> **마지막 값 우선(last-wins)** — 같은 키가 여러 번 오면 나중 것으로 덮어쓰는 처리 방식.\
> 예: 수정 전 `dupe="1";DUPE="2"`의 결과는 `DUPE="2"` 하나뿐이다 — gh-36841이 없애려던 바로 그 동작이다.

### 3.2 같은 논리적 중복인데 결과가 갈린다

동일한 입력을 대소문자만 바꿔 넣었을 때의 결과 차이가 그 비일관성을 가장 압축해서 보여준다.

| 입력 | 수정 전 | 수정 후 |
| --- | --- | --- |
| `text/plain;dupe="1";dupe="2"` | `InvalidMimeTypeException` | `InvalidMimeTypeException` |
| `text/plain;dupe="1";DUPE="2"` | 파싱 성공, `"2"`만 남음 | `InvalidMimeTypeException` |

같은 입력 `text/plain;dupe="1";DUPE="2"` 한 줄이 두 세계에서 어떻게 끝나는지를 나란히 놓으면 이렇다.

```text
수정 전 (누산 맵 = LinkedHashMap)        수정 후 (누산 맵 = LinkedCaseInsensitiveMap)
+--------------------------------+      +--------------------------------+
| put("dupe")  -> null   통과    |      | put("dupe")  -> null   통과    |
| put("DUPE")  -> null   통과    |      | put("DUPE")  -> "1"    중복!   |
| 결과 맵 복사 시 dupe 항목 제거 |      | InvalidMimeTypeException       |
| 최종: text/plain;DUPE="2"      |      | 최종: 없음 (예외로 종료)       |
+--------------------------------+      +--------------------------------+
  -> 값 하나가 소리 없이 사라진다          -> 중복이라고 호출자에게 말해 준다
```

수정 전에는 `put`이 두 번 다 `null`을 돌려주므로 검사가 한 번도 발동하지 않고, 손실은 그 뒤 결과 맵에서 조용히 일어난다.

`MimeType`은 파라미터 이름을 대소문자 무시로 다루겠다고 선언해 놓고(`getParameter("CHARSET") == getParameter("charset")`), 중복 판정만 대소문자를 구분했다.\
근거 RFC로 보면 판정은 분명하다.\
이름이 case-insensitive라면(RFC 2045) `Charset=utf-8`과 `charset=utf-8`은 같은 파라미터이고, 같은 파라미터가 두 번 나오면 오류다(RFC 6838 §4.3, gh-36841이 인용한 조항).\
실무적으로도 `Content-Type: text/plain;Charset=utf-8;charset=euc-kr` 같은 헤더가 들어왔을 때 어느 charset이 이겼는지 아무 신호 없이 결정되는 편보다, 거절하는 편이 낫다.

> **charset** — 바이트를 글자로 읽는 규칙을 가리키는 파라미터 이름.\
> 예: `text/plain;charset=euc-kr`과 `charset=utf-8` 중 어느 쪽이 이기느냐에 따라 같은 바이트가 다른 글자로 읽힌다.

## 4. 수정 해설 — 누산 맵의 규칙을 결과 맵에 맞춘다

### 4.1 자료구조 한 줄

고칠 지점을 고르는 기준은 "두 맵의 규칙이 어긋났다"는 진단에서 바로 나온다.\
결과 맵이 이미 옳은 규칙(case-insensitive)을 쓰고 있으므로, 누산 맵을 거기에 맞추면 된다.\
중복 검사 로직 자체는 손대지 않는다.

```java
private void putParameter(String name, String value) {
    if (this.parameters == null) {
        // Parameter names are case-insensitive, so use a case-insensitive
        // map in order to reject duplicates that differ only in case.
        this.parameters = new LinkedCaseInsensitiveMap<>(4, Locale.ROOT);
    }
    if (this.parameters.put(name, value) != null) {
        throw new InvalidMimeTypeException(this.input, "duplicate parameter '" + name + "=" + value + "'");
    }
}
```
(수정 후 `MimeTypeUtils.MimeTypeParser#putParameter`)

이 한 줄 교체로 앞서 본 `LinkedCaseInsensitiveMap#put`의 반환 규칙이 파서 쪽에서 처음으로 의미를 갖게 된다.\
`DUPE`를 넣을 때 `put`이 이전 값 `"1"`을 돌려주므로, 원래 있던 `!= null` 검사가 그대로 발동해 `InvalidMimeTypeException`을 던진다.\
즉 새 분기를 만든 것이 아니라, 이미 있던 분기가 도달하지 못하던 입력에 도달하게 만든 수정이다.

> **`InvalidMimeTypeException`** — 미디어 타입 문자열이 형식에 맞지 않을 때 스프링이 던지는 예외.\
> 예: 중복 파라미터에 대해 던지는 메시지는 `duplicate parameter 'DUPE="2"'`처럼 문제의 파라미터를 그대로 품는다.

같은 `putParameter`를 수정 전후로 나란히 놓으면 바뀐 칸이 한 칸뿐이라는 점이 보인다.

```text
수정 전 putParameter                     수정 후 putParameter
+--------------------------------+      +--------------------------------+
| parameters == null 이면        |      | parameters == null 이면        |
|   new LinkedHashMap<>(4)       |      |   new LinkedCaseInsensitiveMap |
|                                |      |        <>(4, Locale.ROOT)      |
| put(name, value) != null ?     |      | put(name, value) != null ?     |
|   -> throw Invalid...Exception |      |   -> throw Invalid...Exception |
+--------------------------------+      +--------------------------------+
  -> 검사 분기는 그대로, 재료만 교체      -> dupe / DUPE 가 같은 키가 된다
```

분기는 하나도 늘지 않았고, `put`이 값을 돌려주는 자료구조로 갈아 끼운 것이 전부다.

### 4.2 `Locale.ROOT`를 명시한 이유

`Locale.ROOT`를 명시한 것은 `MimeType#createParametersMap`이 쓰는 인자와 똑같이 맞추기 위해서다.\
인자 없는 생성자는 `Locale.getDefault()`를 쓰므로 JVM 로케일에 따라 키 정규화가 달라질 수 있고, 그러면 "중복인지 아닌지"가 실행 환경에 좌우된다.\
파싱 판정에 그런 변수를 들이지 않는다.

### 4.3 중복 없는 입력은 아무것도 달라지지 않는다

중복이 없는 입력에 대해서는 관측 가능한 변화가 없다.\
`LinkedCaseInsensitiveMap`은 키의 원래 대소문자와 삽입 순서를 보존하므로, 누산 맵의 키·값·순회 순서가 이전 `LinkedHashMap`과 동일하다.\
게다가 그 맵은 `MimeType` 생성자에서 다시 `LinkedCaseInsensitiveMap`으로 복사되고 버려진다.\
결과 객체의 형태는 그대로다.\
바뀌는 것은 오직 중복 판정의 민감도 하나다.

### 4.4 PR이 이 모양이 된 경위

한편 이 PR이 지금 이 모양이 된 경위 자체가 하나의 사건이다.\
PR은 7월 6일 옛 절차형 파서 기준으로 열렸지만, 7월 24일 커밋 `0799920`이 파서를 상태 기계로 전면 재작성하면서 수정 대상 메서드가 사라졌다.

8월 13일 커뮤니티 기여자 `yashsiwacha`가 코멘트로 그 사실과 함께 새 파서에서의 정확한 수정 지점 — `MimeTypeParser.putParameter`의 누산 맵을 `new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)`로 — 을 제안했다.\
브랜치를 최신 `main` 위로 rebase하고 그 제안대로 재작성한 뒤, 커밋에 `Co-authored-by: Yash <...>` 크레딧을 넣고 코멘트로 감사와 반영 결과를 알렸다.\
제안을 그대로 받되 실제 코드로 검증하고 크레딧을 남기는 것이 이런 상황의 기본 처리다.

> **rebase(리베이스)** — 내 커밋들을 최신 기준 브랜치 위로 옮겨 다시 얹는 git 조작.\
> 예: 7월 6일 브랜치를 8월의 `main` 위로 rebase하자, 고치려던 메서드가 이미 사라진 상태의 코드와 마주치게 됐다.

## 5. 검증 — 테스트가 무엇을 고정하나

테스트는 `MimeTypeTests`의 `@Nested class InvalidMimeTypeTests` 블록에 한 개 추가됐다.\
기존 정확 중복 테스트인 `valueOfDuplicateParameter` 바로 옆에 케이스 변형 짝을 두어, 둘이 같은 규칙 아래 있다는 점을 코드 배치로도 드러낸다.

```java
@Test
void valueOfDuplicateParameterWithDifferentCase() {
    assertThatThrownBy(() -> MimeType.valueOf("text/plain;dupe=\"1\";DUPE=\"2\"")).isInstanceOf(InvalidMimeTypeException.class)
            .hasMessageContaining("Invalid mime type \"text/plain;dupe=\"1\";DUPE=\"2\"\": duplicate parameter 'DUPE=\"2\"'");
}
```
(`MimeTypeTests.InvalidMimeTypeTests#valueOfDuplicateParameterWithDifferentCase`)

이 테스트가 고정하는 것은 세 가지다.\
첫째, 케이스만 다른 중복이 **예외를 던진다**는 것 — 이것이 회귀 방지의 본체다.\
둘째, 예외 타입이 `InvalidMimeTypeException`이라는 것 — 호출자가 잡는 타입이 바뀌지 않았음을 뜻한다.\
셋째, 메시지에 **원본 입력 문자열과 문제가 된 파라미터가 원래 대소문자 그대로** 들어간다는 것이다.

`DUPE="2"`가 소문자로 정규화돼 나오지 않아야 진단 메시지로서 쓸모가 있다.\
`LinkedCaseInsensitiveMap`이 키의 원래 표기를 보존한다는 성질이 여기서 눈에 보이는 계약이 된다.

기존 테스트 쪽에서 확인해야 할 반증 질문은 "정상 입력이 깨지지 않는가"다.\
같은 파일의 `parseQuotedCharset`, `parseQuotedParameterValue` 등 따옴표·다중 파라미터 케이스가 그대로 통과해야 하고, 이는 누산 맵 교체가 순서·키 표기를 보존한다는 앞의 논거와 대응한다.

반대로 이 변경은 **파싱 동작 변경**이므로, 대소문자가 다른 중복 파라미터를 보내던 클라이언트는 이제 성공 대신 예외를 받는다.\
PR 본문에 "Note on impact" 절을 따로 둔 이유가 그것이다.\
gh-36841이 이미 정확 중복에 대해 같은 성격의 변경을 했으므로, 이 PR은 그 결정의 사각지대를 메우는 후속이라는 자리매김이 된다.

> **파싱 동작 변경(behavior change)** — 버그 수정과 달리, 이전에는 성공하던 입력이 실패하게 되는 변경.\
> 예: `text/plain;dupe="1";DUPE="2"`를 보내던 클라이언트는 이 PR 이후 예외를 받는다 — 그래서 "Note on impact" 절이 따로 필요했다.

## 6. 상태와 교훈

PR은 현재 OPEN이며 `status: waiting-for-triage` 라벨이 붙은 채 `bclozel` 리뷰 요청 상태다.\
팀 리뷰는 붙지 않았고, 8월 13일 재작성 이후 업데이트가 마지막이다.\
Spring 팀의 트리아지는 며칠 안에 라우팅되거나 그대로 남거나 둘 중 하나이므로, 지금 할 일은 기다리는 것이다.

이 PR에서 남길 만한 것은 세 가지다.

첫째, **버그의 형태가 "규칙이 두 곳에 있고 서로 다르다"** 였다는 점이다.\
파라미터 이름의 대소문자 규칙이 누산 맵과 결과 맵 두 군데에 각각 구현돼 있었고, 한쪽만 옳았다.\
이런 종류의 결함은 새 검사를 추가해서 고치는 것이 아니라, 이미 옳은 쪽에 나머지를 맞춰 규칙의 출처를 하나로 만들어서 고친다.\
실제 diff가 검사 로직이 아니라 자료구조 한 줄인 것은 그 진단의 결과다.

둘째, **오래 열려 있는 PR은 대상 코드가 발밑에서 사라질 수 있다.**\
7월 6일에 연 PR이 7월 24일 파서 전면 재작성으로 무효화됐다.\
재작성된 코드를 실제로 읽고 같은 진단이 여전히 유효한지 다시 확인한 뒤에야 수정 지점을 옮길 수 있었다.\
기억이나 원래 diff를 기준으로 리베이스만 했다면 엉뚱한 곳을 고쳤을 것이다.

셋째, **커뮤니티 제안은 검증하고, 받았으면 크레딧을 남긴다.**\
`yashsiwacha`의 코멘트는 파서 재작성 사실과 새 수정 지점을 정확히 짚었다.\
제안을 실코드로 확인해 채택한 뒤 `Co-authored-by`로 크레딧을 넣고, 반영 완료를 코멘트로 한 번 알렸다.\
남의 제안을 조용히 흡수하지 않는 것이 OSS에서 협업 비용을 낮추는 방식이다.

---

연관 ko-docs (모듈 지도): `spring-core/07-유틸리티와-부가-인프라.md`
