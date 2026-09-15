# PR #37008 — 무대 구조와 워크플로우: MIME 타입 파서

> PR #37008의 무대가 되는 실구조·워크플로우. 문제·수정은 README.md, 테스트는 tests.md 참조.
>
> 기준: upstream main `526c706d1c3`. 이하 file:line은 모두 이 커밋의 작업 트리 기준이며, `putParameter`의 누산 맵은 아직 PR 이전 상태(`LinkedHashMap`)다.

## 1. 무대 — 실구조

이 PR의 무대는 세 덩어리다.\
문자열을 상태 기계로 씹는 **파서**(`MimeTypeUtils.MimeTypeParser` + `ParserState`), 파싱 결과를 담는 **값 객체**(`MimeType`), 그리고 파라미터 이름의 대소문자 규칙을 실제로 구현하는 **자료구조**(`LinkedCaseInsensitiveMap`)다.\
버그는 이 셋 중 어느 하나가 틀려서가 아니라, 파서와 값 객체가 서로 다른 자료구조를 쓰는 바람에 같은 규칙이 두 벌 존재한 데서 나왔다.

> **MIME 타입(MIME type / media type)** — 데이터가 어떤 종류인지를 `type/subtype` 형태로 적은 문자열. 뒤에 세미콜론으로 부가 정보를 붙일 수 있다.\
> 예: `text/plain;charset=utf-8`은 "평문 텍스트이고 문자 인코딩은 UTF-8"이라는 뜻이다.

> **media type 파라미터(parameter)** — 미디어 타입 뒤에 `;이름=값` 형태로 붙는 부가 정보 한 쌍.\
> 예: `charset=utf-8`에서 이름은 `charset`, 값은 `utf-8`이다.

> **상태 기계(state machine) 파서** — 지금 어떤 상태인지를 들고 문자를 하나씩 읽으며 상태를 갈아 끼우는 방식의 파서.\
> 예: `TYPE` 상태에서 `/`를 만나면 type을 확정하고 `SUBTYPE` 상태로 넘어간다.

먼저 소유 관계다.\
`MimeTypeUtils`는 인스턴스를 만들 수 없는 정적 파사드(`spring-core/src/main/java/org/springframework/util/MimeTypeUtils.java:44`)이고, 그 안에 파싱 1회분의 가변 컨텍스트인 `MimeTypeParser`를 private static final 중첩 클래스로 감춰 둔다.

> **정적 파사드(static facade)** — 인스턴스를 만들지 않고 정적 메서드만으로 기능을 내주는 진입용 클래스.\
> 예: `MimeTypeUtils.parseMimeType("text/plain")`처럼 클래스 이름으로 바로 부른다.

```text
MimeTypeUtils (abstract, static facade)                MimeTypeUtils.java:44
 ├─ static final ConcurrentLruCache<String, MimeType>
 │     cachedMimeTypes = new ConcurrentLruCache<>(64, MimeTypeUtils::parseMimeTypeInternal)   :166
 ├─ static MimeType parseMimeType(String)              :194   ← 공개 진입점
 ├─ static MimeType parseMimeTypeInternal(String)      :205   ← new MimeTypeParser(s).parse()
 ├─ static List<MimeType> parseMimeTypes(String)       :216
 │
 ├─ private static final class MimeTypeParser          :382   ← 파싱 1회분 가변 컨텍스트
 │    ├─ final String input                            :384
 │    ├─ int index                                     :386   ← 현재 읽는 문자 위치
 │    ├─ int mark                                      :388   ← 현재 토큰이 시작된 위치
 │    ├─ String type / String subtype                  :390 / :392
 │    ├─ @Nullable Map<String,String> parameters       :394   ← 누산 맵 (문제의 필드)
 │    ├─ @Nullable String paramName                    :396   ← 값이 오기 전 잡아 둔 이름
 │    ├─ @Nullable MimeType parsed                     :398   ← 완성된 결과
 │    ├─ MimeType parse()                              :410   ← 문자 루프
 │    ├─ void resolveBareType(String)                  :430
 │    ├─ void putParameter(String, String)             :438   ← 중복 판정이 사는 곳
 │    ├─ void emitMimeType()                           :447
 │    └─ MimeType buildMimeType()                      :451   ← new MimeType(type, subtype, parameters)
 │
 └─ enum ParserState                                   :467   ← 상태 = 전이 함수의 묶음
      INITIAL :469 · TYPE :480 · SUBTYPE :505 · WHITESPACE :522
      PARAM_NAME :539 · PARAM_NAME_END :554 · PARAM_VALUE_START :567
      PARAM_VALUE_TOKEN :582 · PARAM_VALUE_QUOTED :598 · PARAM_VALUE_ESCAPED :617
      ├─ abstract ParserState process(char, MimeTypeParser)   :634
      ├─ void onEof(MimeTypeParser)                           :636   ← 기본은 빈 구현
      └─ static void extractParameter(MimeTypeParser, String) :629   → parser.putParameter(...)
```

여기서 눈여겨볼 설계는 상태와 컨텍스트의 분리다.\
`ParserState`는 enum 상수마다 `process`를 오버라이드한 **전이 함수의 묶음**일 뿐 자기 상태를 갖지 않고, 진짜 상태(어디까지 읽었나, 무엇을 모았나)는 전부 `MimeTypeParser` 인스턴스에 있다.\
그래서 enum 상수들이 파싱 세션 간에 공유돼도 안전하다.\
각 상태는 구분자를 만나면 `mark`부터 `index`까지를 잘라 컨텍스트에 쓰고 다음 상태를 돌려준다.

> **누산 맵(accumulator map)** — 파싱 도중 결과 조각을 하나씩 쌓아 두는 임시 맵.\
> 예: 여기서는 `MimeTypeParser.parameters`가 `charset=utf-8` 같은 파라미터를 나오는 대로 담는다.

파싱이 끝나면 결과는 `MimeType` 값 객체로 넘어간다.\
이쪽 구조는 훨씬 단순하지만, 파라미터 맵의 타입이 파서 쪽과 다르다는 한 가지가 이 PR의 전부다.

> **값 객체(value object)** — 만들어진 뒤 내용이 바뀌지 않고, 내용이 같으면 같은 것으로 취급되는 객체.\
> 예: `MimeType`은 생성자에서 파라미터 맵을 복사·봉인하므로 만든 뒤에 바꿀 수 없다.

```text
MimeType (Comparable<MimeType>, Serializable)          MimeType.java:52
 ├─ static final String WILDCARD_TYPE = "*"            :57
 ├─ static final String PARAM_CHARSET = "charset"      :59
 ├─ static final BitSet TOKEN                          :61    ← RFC 2616 2.2 토큰 문자 집합
 ├─ final String type / final String subtype           :99 / :101   ← 생성자에서 소문자화 :158-159
 ├─ final Map<String,String> parameters                :104   ← 결과 맵
 ├─ transient @Nullable Charset resolvedCharset        :106
 ├─ MimeType(String, String, @Nullable Map)            :153   ← 파서가 부르는 생성자
 ├─ Map<String,String> createParametersMap(Map)        :230   ← LinkedCaseInsensitiveMap 으로 복사
 ├─ void checkParameters(String, String)               :244   ← 이름·값 토큰 검사
 ├─ @Nullable String getParameter(String)              :353
 └─ static MimeType valueOf(String)                    :738   → MimeTypeUtils.parseMimeType

LinkedCaseInsensitiveMap<V> implements Map<String,V>   LinkedCaseInsensitiveMap.java:51
 ├─ final LinkedHashMap<String,V> targetMap            :57    ← 원래 표기 키 → 값 (삽입 순서 보존)
 ├─ final HashMap<String,String> caseInsensitiveKeys   :59    ← 소문자 키 → 원래 표기 키
 ├─ final Locale locale                                :61    ← null 이면 Locale.getDefault()  :132
 ├─ LinkedCaseInsensitiveMap(int, @Nullable Locale)    :114
 ├─ boolean containsKey(Object)                        :158
 ├─ @Nullable V put(String, @Nullable V)               :190   ← 케이스 충돌 시 옛 항목 제거 후 반환
 └─ protected String convertKey(String)                :332   ← key.toLowerCase(getLocale())
```

`LinkedCaseInsensitiveMap`의 핵심은 맵을 두 개 들고 있다는 점이다.\
`targetMap`은 사용자가 넣은 **원래 표기 그대로**의 키를 삽입 순서대로 보관하고, `caseInsensitiveKeys`는 소문자 정규화 키에서 원래 표기 키로 가는 색인이다.\
조회·포함·삭제는 색인을 거치므로 대소문자를 가리지 않고, 순회와 출력은 `targetMap`을 쓰므로 원래 표기와 순서가 살아남는다.\
두 맵의 역할 분담이 곧 이 클래스의 계약이다.

> **`LinkedHashMap`** — 넣은 순서를 기억하는 자바 표준 맵. 키 비교는 `equals` 그대로라 대소문자를 구분한다.\
> 예: `dupe`와 `DUPE`를 넣으면 서로 다른 키 두 개가 된다.

> **`LinkedCaseInsensitiveMap`** — 스프링이 만든 맵. 조회·중복 판정은 대소문자를 무시하되 키의 원래 표기와 삽입 순서는 보존한다.\
> 예: `Charset`으로 넣고 `CHARSET`으로 꺼내도 값이 나오지만, 출력에는 넣을 때의 `Charset`이 그대로 보인다.

> **정규화 키(normalized key)** — 비교하기 좋게 한 가지 형태로 바꿔 둔 키.\
> 예: 여기서는 `convertKey`가 `DUPE`를 소문자 `dupe`로 바꾼 것이 정규화 키다.

세 덩어리를 하나로 겹치면 이런 그림이 된다.\
파라미터 맵이 파싱 도중과 결과 보관 시점에 각각 하나씩, 총 두 번 등장한다는 사실이 눈에 들어와야 한다.

```text
  입력 문자열 "text/plain;dupe=\"1\";DUPE=\"2\""
        │
        ▼
  MimeTypeParser.parameters   ← 누산 맵 (HEAD 기준 LinkedHashMap, MimeTypeUtils.java:440)
        │   putParameter 가 put 반환값으로 중복 판정          :442
        ▼
  new MimeType(type, subtype, parameters)                     :456
        │   createParametersMap 이 통째로 복사                MimeType.java:230
        ▼
  MimeType.parameters         ← 결과 맵 (LinkedCaseInsensitiveMap, Locale.ROOT)  :232
```

## 2. 수정 전 동작 워크플로우

수정 전 기준으로 파싱은 "정적 진입점 -> 캐시 -> 파서 인스턴스 -> 문자 루프 -> 값 객체 생성" 다섯 단계를 밟는다.\
대표 시나리오 두 개를 따라가면 구조 전체가 드러난다.

먼저 다섯 단계를 한 장으로 세워 놓고, 파라미터 값이 어느 칸에서 갈라지는지부터 본다.

```text
 수정 전 전체 워크플로우 — 입력 "text/plain;dupe=\"1\";DUPE=\"2\""

 MimeType.valueOf(input)                          MimeType.java:738
        |
        v
 MimeTypeUtils.parseMimeType(input)               MimeTypeUtils.java:194
        |  빈 문자열이면 예외 / multipart 면 캐시 우회
        v
 cachedMimeTypes.get(input)   (ConcurrentLruCache, 용량 64)       :166
        |  miss
        v
 parseMimeTypeInternal(input) -> new MimeTypeParser(input).parse() :205
        |
        v
 문자 루프: state = state.process(c, this)                        :410
        |  파라미터가 확정될 때마다
        v
 ParserState.extractParameter(parser, value)                      :629
        |  모든 확정 경로가 여기 한 점으로 모인다
        v
 MimeTypeParser.putParameter(name, value)                         :438
        |
        +-- 누산 맵 = LinkedHashMap        <-- 규칙 A: 대소문자 구분
        |      put("dupe","\"1\"") -> null  -> 통과
        |      put("DUPE","\"2\"") -> null  -> 통과   [!] 여기서 갈라진다
        v
 buildMimeType() -> new MimeType(type, subtype, parameters)       :451
        |
        v
 MimeType.createParametersMap(parameters)            MimeType.java:230
        |
        +-- 결과 맵 = LinkedCaseInsensitiveMap  <-- 규칙 B: 대소문자 무시
        |      put("dupe","\"1\"") -> targetMap {dupe=1}
        |      put("DUPE","\"2\"") -> 충돌 감지, 옛 값 "1" 반환
        |                             그 반환값을 forEach 람다가 버린다
        v
 결과: text/plain;DUPE="2"   (예외 없음, 앞 값 소실)
```

두 갈래의 이름표는 "규칙 A가 통과시킨 것을 규칙 B가 조용히 지운다"이다.\
판정이 있는 칸과 대소문자 감각이 있는 칸이 서로 다른 칸이라는 것이 그림 하나로 보인다.

### 시나리오 A — 정상 입력 `text/plain;charset=utf-8`

먼저 바깥 껍질이다.\
`parseMimeType`은 빈 문자열을 거르고, `multipart`로 시작하면 캐시를 건너뛴다.\
멀티파트는 경계 문자열이 매번 랜덤이라 캐시가 오염되기 때문이다(`MimeTypeUtils.java:198-201`).

> **LRU 캐시(least recently used cache)** — 정해진 개수만 담고, 넘치면 가장 오래 안 쓴 항목부터 버리는 캐시.\
> 예: 여기서는 파싱 결과 64개를 담아 같은 `Content-Type` 문자열의 재파싱을 피한다.

```text
MimeType.valueOf("text/plain;charset=utf-8")          MimeType.java:738
  └→ MimeTypeUtils.parseMimeType(String)              MimeTypeUtils.java:194
       ├─ !StringUtils.hasLength → InvalidMimeTypeException  :195
       ├─ startsWith("multipart") → parseMimeTypeInternal 직행 :199
       └─ cachedMimeTypes.get(input)                  :202
            └(miss)→ parseMimeTypeInternal(input)     :205
                       └→ new MimeTypeParser(input).parse()  :206
```

파서 안쪽은 문자 하나마다 상태를 갈아 끼우는 단일 루프다(`MimeTypeUtils.java:410-421`).\
아래는 위 입력이 상태를 어떻게 지나가는지 문자 단위로 편 것이다.\
`mark`가 토큰 시작을, `index`가 현재 문자를 가리키며, 구분자를 만난 상태가 `substring(mark, index)`로 조각을 확정한다.

> **토큰(token)** — 문자열에서 의미 단위로 잘라 낸 한 조각.\
> 예: `text/plain;charset=utf-8`에서 `text`·`plain`·`charset`·`utf-8`이 각각 토큰이다.

```text
 index :  0..3   4      5..9      10      11..17   18       19..23    EOF
 char  :  t e x t  '/'   p l a i n  ';'    charset  '='      utf-8
 state :  INITIAL
            └→ TYPE ────'/'───→ type="text",  mark=5           :483-489
                 SUBTYPE ──';'──→ subtype="plain"              :508-510
                   WHITESPACE ──'c'──→ mark=11                 :525-529
                     PARAM_NAME ──'='──→ paramName="charset"   :542-544
                       PARAM_VALUE_START ──'u'──→ mark=19      :577-578
                         PARAM_VALUE_TOKEN ──EOF──┐            :591-595
                                                  │
                          extractParameter(parser, "utf-8")    :629
                            └→ parser.putParameter("charset","utf-8")   :438
                                 └→ parameters = new LinkedHashMap<>(4) :440
                                    parameters.put(...) == null → 통과   :442
                          parser.emitMimeType()                 :447
                            └→ buildMimeType()                  :451
                                 └→ new MimeType("text","plain", parameters)  :456
```

마지막 `new MimeType(...)`이 값 객체 쪽 규칙을 적용한다.\
type·subtype은 `Locale.ROOT`로 소문자화되고(`MimeType.java:158-159`), 파라미터는 `createParametersMap`이 항목마다 `checkParameters`로 토큰 검사를 하면서 새 `LinkedCaseInsensitiveMap`에 복사한 뒤 `unmodifiableMap`으로 봉인한다(`MimeType.java:230-242`).\
`charset` 키가 있으면 그 자리에서 `Charset.forName`으로 해석해 `resolvedCharset`에 캐시한다(`MimeType.java:161-163`).

> **charset(문자 집합)** — 바이트를 어떤 문자 인코딩으로 읽을지 정하는 파라미터.\
> 예: `charset=utf-8`이면 본문 바이트를 UTF-8로 해석한다.

> **`Locale.ROOT`** — 어느 나라 규칙도 따르지 않는 중립 로케일. 대소문자 변환 결과가 실행 환경과 무관하게 같아진다.\
> 예: 터키어 로케일에서는 `I`의 소문자가 점 없는 `ı`가 되지만, `Locale.ROOT`에서는 항상 `i`가 된다.

```text
new MimeType("text","plain", {charset=utf-8})          MimeType.java:153
  ├─ Assert.hasLength(type/subtype)                    :154-155
  ├─ checkToken(type), checkToken(subtype)             :156-157  (BitSet TOKEN :61)
  ├─ this.type/subtype = toLowerCase(Locale.ROOT)      :158-159
  ├─ this.parameters = createParametersMap(params)     :160
  │     └─ new LinkedCaseInsensitiveMap<>(size, Locale.ROOT)   :232
  │        forEach: checkParameters(k,v) → map.put(k,v)        :233-236
  │        Collections.unmodifiableMap(map)                    :237
  └─ containsKey("charset") → resolvedCharset = Charset.forName(unquote(...))  :161-163
```

### 시나리오 B — 케이스만 다른 중복 `text/plain;dupe="1";DUPE="2"`

같은 경로를 타지만 파라미터가 두 번 확정된다는 점만 다르다.\
문제는 두 번째 확정이 아무 저항 없이 통과한다는 것이다.

```text
... SUBTYPE ──';'──→ WHITESPACE ──'d'──→ PARAM_NAME("dupe")
      PARAM_VALUE_START ──'"'──→ mark, PARAM_VALUE_QUOTED           :573-575
        ──닫는 '"'──→ extractParameter(parser, "\"1\"")             :601-603
             putParameter("dupe", "\"1\"")
               parameters = new LinkedHashMap<>(4)                  :440
               put("dupe", "\"1\"") → null 반환 → 통과              :442
      WHITESPACE ──'D'──→ PARAM_NAME("DUPE") → ... PARAM_VALUE_QUOTED
        ──닫는 '"'──→ extractParameter(parser, "\"2\"")
             putParameter("DUPE", "\"2\"")
               put("DUPE", "\"2\"") → null 반환 (LinkedHashMap 에게 dupe ≠ DUPE)
                                    → 검사 미발동  ★ 버그가 사는 지점
      EOF → WHITESPACE.onEof → emitMimeType()                       :532-536
             buildMimeType → new MimeType("text","plain", {dupe="1", DUPE="2"})
               createParametersMap: LinkedCaseInsensitiveMap 이 두 키를 하나로 병합
                 put("dupe","\"1\"")  → targetMap {dupe="1"}
                 put("DUPE","\"2\"")  → caseInsensitiveKeys["dupe"] 충돌 감지
                                        targetMap.remove("dupe") → 옛 값 "1" 소멸
                                        targetMap.put("DUPE","\"2\"")
                                        반환값 "1" 은 forEach 가 버림  ★ 조용한 소실
             결과: MimeType text/plain;DUPE="2"   (예외 없음)
```

이 흐름의 요점은 두 맵의 규칙이 서로 다르다는 것 하나다.\
누산 맵은 `dupe`와 `DUPE`를 다른 키로 보고 통과시키고, 결과 맵은 같은 키로 보고 앞 값을 지운다.\
`LinkedCaseInsensitiveMap.put`은 제거된 옛 값을 성실히 반환하지만(`LinkedCaseInsensitiveMap.java:190-198`), 그 반환값을 받는 쪽이 `createParametersMap`의 `forEach` 람다라서 아무도 보지 않는다.\
중복 판정이 있는 곳에는 케이스 감각이 없고, 케이스 감각이 있는 곳에는 판정이 없다.

같은 입력 `text/plain;dupe="1";DUPE="2"`가 두 맵을 지날 때의 최종 상태를 나란히 놓으면 이렇다.

```text
 누산 맵 (LinkedHashMap)              결과 맵 (LinkedCaseInsensitiveMap)
 +-----------------------------+     +-----------------------------+
 | dupe -> "1"                 |     | DUPE -> "2"                 |
 | DUPE -> "2"                 |     |   ("1" 은 remove 로 사라짐)  |
 | 키 2개                      |     | 키 1개                      |
 +-----------------------------+     +-----------------------------+
  put 이 둘 다 null 을 반환            put 이 "1" 을 반환했지만
   -> 중복 검사 미발동                  forEach 람다가 버린다
   -> 예외 없음                        -> 예외 없음
```

두 칸 모두 예외가 없다는 것이 이 결함의 성격이다.

## 3. 분기 처리 워크플로우

이 무대의 조건 분기는 세 층에 나뉘어 있다.\
진입점의 캐시 분기, 상태 기계의 문자별 전이 분기, 그리고 파라미터 확정 시점의 중복 판정 분기다.\
버그는 마지막 층에 있다.

### 3-1. 진입점 분기

공개 진입점은 빈 문자열을 거르고 멀티파트만 캐시를 우회시킨 뒤 나머지를 캐시에 맡긴다.

```text
parseMimeType(input)                                   MimeTypeUtils.java:194
  │
  ├─ hasLength(input) == false ──→ throw InvalidMimeTypeException("'mimeType' must not be empty")  :196
  │
  ├─ input.startsWith("multipart") ──→ parseMimeTypeInternal(input)   :200
  │        (경계 문자열이 랜덤이라 캐시하면 LRU 가 오염된다)
  │
  └─ 그 외 ──→ cachedMimeTypes.get(input)                             :202
                ├─ hit  ──→ 이전에 만든 MimeType 인스턴스 재사용
                └─ miss ──→ generator = parseMimeTypeInternal          :167
```

캐시 분기는 이 PR에서 부작용을 하나 갖는다.\
파싱이 예외를 던지면 `ConcurrentLruCache`에 아무것도 남지 않으므로, 같은 잘못된 입력은 매번 다시 파싱돼 매번 같은 예외를 던진다.\
즉 수정 후에도 "처음엔 통과했는데 나중엔 거절" 같은 캐시 기인 비결정성은 생기지 않는다.

> **비결정성(non-determinism)** — 같은 입력에 같은 결과가 나온다고 보장할 수 없는 성질.\
> 예: 첫 호출만 예외가 나고 이후 캐시 히트로 통과한다면 그것이 비결정성이다.

### 3-2. 상태 기계 전이 분기

각 상태의 `process`가 문자 하나를 보고 자기 자신 또는 다음 상태를 반환한다.\
아래는 전이 조건과 그때 확정되는 조각을 한 장으로 편 것이다.

> **EOF(end of file)** — 읽을 것이 더 없는 지점. 여기서는 입력 문자열의 끝을 뜻한다.\
> 예: `text/plain`처럼 세미콜론 없이 끝나면 `SUBTYPE.onEof`가 마지막 조각을 확정한다.

```text
INITIAL :469
  ├─ ' ' | '\t' ──→ INITIAL (선행 공백 흡수)
  └─ 그 외      ──→ mark=index, TYPE

TYPE :480
  ├─ '/'                ──→ type=[mark,index)  (빈 문자열이면 예외 :486) → mark=index+1, SUBTYPE
  ├─ ';' | ' ' | '\t'   ──→ resolveBareType([mark,index)) → WHITESPACE
  │                          └ candidate != "*" 이면 예외 "does not contain '/'"  :431-433
  ├─ 그 외              ──→ TYPE
  └─ onEof              ──→ resolveBareType([mark,)) → emitMimeType    :499-502

SUBTYPE :505
  ├─ ';' | ' ' | '\t'   ──→ subtype=[mark,index) → WHITESPACE
  ├─ 그 외              ──→ SUBTYPE
  └─ onEof              ──→ subtype=[mark,) → emitMimeType             :516-519

WHITESPACE :522                          ← 파라미터 사이의 중립 지대
  ├─ ' ' | '\t' | ';'   ──→ WHITESPACE
  ├─ 그 외              ──→ mark=index, PARAM_NAME
  └─ onEof              ──→ type 이 비어 있지 않으면 emitMimeType       :532-536

PARAM_NAME :539
  ├─ '='                ──→ paramName=[mark,index) → PARAM_VALUE_START
  ├─ ' ' | '\t'         ──→ paramName=[mark,index) → PARAM_NAME_END
  └─ 그 외              ──→ PARAM_NAME
        (onEof 없음: "a/b;x" 처럼 값 없이 끝나면 아무것도 emit 되지 않아
         parse() 의 parsed == null 검사가 예외를 던진다  :417-419)

PARAM_NAME_END :554
  ├─ ' ' | '\t'         ──→ PARAM_NAME_END
  ├─ '='                ──→ PARAM_VALUE_START
  └─ 그 외              ──→ 예외 "Unexpected character '<c>' after parameter name"  :563

PARAM_VALUE_START :567
  ├─ ' ' | '\t'         ──→ PARAM_VALUE_START
  ├─ '"'                ──→ mark=index (따옴표 포함), PARAM_VALUE_QUOTED
  └─ 그 외              ──→ mark=index, PARAM_VALUE_TOKEN

PARAM_VALUE_TOKEN :582
  ├─ ';' | ' ' | '\t'   ──→ extractParameter([mark,index)) → WHITESPACE
  ├─ 그 외              ──→ PARAM_VALUE_TOKEN
  └─ onEof              ──→ extractParameter([mark,)) → emitMimeType

PARAM_VALUE_QUOTED :598
  ├─ '"'                ──→ extractParameter([mark,index+1))  (닫는 따옴표 포함) → WHITESPACE
  ├─ '\\'               ──→ PARAM_VALUE_ESCAPED
  ├─ 그 외              ──→ PARAM_VALUE_QUOTED
  └─ onEof              ──→ extractParameter([mark,)) → emitMimeType

PARAM_VALUE_ESCAPED :617
  ├─ 아무 문자          ──→ PARAM_VALUE_QUOTED  (다음 한 글자를 무조건 소비)
  └─ onEof              ──→ extractParameter([mark,)) → emitMimeType
```

모든 파라미터 확정 경로가 `extractParameter`(`MimeTypeUtils.java:629`) 한 점으로 모인다는 것이 중요하다.\
토큰 값이든 따옴표 값이든, 구분자로 끝났든 입력이 끝나 `onEof`로 흘렀든, 결국 `parser.putParameter(paramName, value)` 한 줄을 지난다.\
그래서 중복 판정을 한 곳에서 고칠 수 있다.

### 3-3. 중복 판정 분기 — 버그가 살던 자리

파라미터 확정은 누산 맵을 지연 생성하고 `put` 반환값으로 중복을 판정하는 두 분기가 전부다.

> **지연 생성(lazy initialization)** — 필요해지는 순간에야 객체를 만드는 것.\
> 예: 파라미터가 하나도 없는 `text/plain`은 누산 맵을 아예 만들지 않는다.

```text
putParameter(name, value)                              MimeTypeUtils.java:438
  │
  ├─ this.parameters == null ?                                          :439
  │    ├─ 예 ──→ this.parameters = new LinkedHashMap<>(4)   ★ 여기가 수정 대상 :440
  │    └─ 아니오 ──→ 그대로 사용
  │
  └─ this.parameters.put(name, value) != null ?                         :442
       ├─ 예   ──→ throw InvalidMimeTypeException(input,
       │             "duplicate parameter '<name>=<value>'")            :443
       └─ 아니오 ──→ 통과 (정상 누적)

  입력별 귀결 (수정 전)
    dupe / dupe  →  LinkedHashMap 이 같은 키로 봄  → put 이 "1" 반환 → 예외      (의도대로)
    dupe / DUPE  →  LinkedHashMap 이 다른 키로 봄  → put 이 null 반환 → 통과  ★ 결함
                     이후 MimeType 생성자에서 앞 값이 조용히 사라짐

  입력별 귀결 (PR 적용 후: LinkedCaseInsensitiveMap<>(4, Locale.ROOT))
    dupe / dupe  →  동일 키 → put 이 "1" 반환 → 예외
    dupe / DUPE  →  caseInsensitiveKeys["dupe"] 충돌 → targetMap 에서 옛 값 제거 후
                     그 값을 반환 → 이미 있던 !=null 검사가 발동 → 예외
```

분기 자체는 하나도 늘지 않는다.\
`put`의 반환 규칙을 갖는 자료구조로 갈아 끼워, 원래 있던 `!= null` 분기가 도달하지 못하던 입력에 도달하게 만드는 것이 수정의 전부다.\
반환값이 왜 그렇게 나오는지는 `LinkedCaseInsensitiveMap.put`의 세 줄에 있다.

```text
put(key, value)                        LinkedCaseInsensitiveMap.java:190
  ├─ oldKey = caseInsensitiveKeys.put(convertKey(key), key)     :191
  │     convertKey = key.toLowerCase(locale)                    :332
  ├─ oldKey != null && !oldKey.equals(key) ?                    :193
  │     ├─ 예 ──→ oldKeyValue = targetMap.remove(oldKey)        :194   ← 표기가 다른 옛 항목 제거
  │     └─ 아니오 ──→ oldKeyValue = null
  ├─ oldValue = targetMap.put(key, value)                       :196
  └─ return (oldKeyValue != null ? oldKeyValue : oldValue)      :197
        ↑ 표기가 달라도 이전 값이 나온다 = 중복 신호
```

`Locale.ROOT`를 넘기는 이유도 이 분기에 있다.\
생성자에 로케일을 주지 않으면 `Locale.getDefault()`가 쓰이고(`LinkedCaseInsensitiveMap.java:132`), 터키어 로케일처럼 `I`의 소문자화가 다른 환경에서는 `convertKey`의 결과가 달라져 "중복인지 아닌지"가 JVM 설정에 좌우된다.\
`MimeType.createParametersMap`이 이미 `Locale.ROOT`를 쓰므로(`MimeType.java:232`), 누산 맵도 같은 인자를 써야 두 맵의 판정이 어긋나지 않는다.

## 4. 스프링 전역에서의 자리

이 파서는 스프링에서 미디어 타입 문자열이 객체가 되는 **유일한 길목**이다.\
HTTP 헤더 처리, 메시징(STOMP·RSocket), 콘텐츠 협상이 모두 여기로 수렴한다.\
아래 진입점은 grep으로 실확인한 것만 적었다.

> **콘텐츠 협상(content negotiation)** — 클라이언트가 받고 싶은 표현과 서버가 낼 수 있는 표현을 맞춰 고르는 절차.\
> 예: 요청의 `Accept: application/json` 헤더를 보고 JSON 응답을 고른다.

```text
[ spring-web — HTTP 헤더 ]
  HttpHeaders.getContentType()                    HttpHeaders.java:1094
    └→ MediaType.parseMediaType(value)            HttpHeaders.java:1096
         └→ MimeTypeUtils.parseMimeType(mediaType)  MediaType.java:680  (메서드 :677)
              └→ MimeTypeParser.parse()             MimeTypeUtils.java:410
         InvalidMimeTypeException 은 InvalidMediaTypeException 으로 감싸 던진다  MediaType.java:681-683

  HttpHeaders.getAccept()                         HttpHeaders.java:553
    └→ MediaType.parseMediaTypes(get(ACCEPT))
         └→ MimeTypeUtils.parseMimeTypes(...)     MediaType.java:706 → MimeTypeUtils.java:216
              └→ 토큰마다 parseMimeType                              MimeTypeUtils.java:223
  HttpHeaders.getAcceptPatch()                    HttpHeaders.java:648   (같은 경로)

  MediaTypeFactory                                MediaTypeFactory.java:49, :68
    └→ 클래스패스의 mime.types 매핑을 정적 초기화 시 파싱 (확장자 → MediaType)

[ spring-messaging — STOMP ]
  StompHeaderAccessor (content-type 헤더 수신)      StompHeaderAccessor.java:148
    └→ MimeTypeUtils.parseMimeType(value)
  StompHeaders#getContentType                      StompHeaders.java:152
    └→ MimeTypeUtils.parseMimeType(value)

[ spring-messaging — 메시지 변환·콘텐츠 협상 ]
  DefaultContentTypeResolver#resolve               DefaultContentTypeResolver.java:70
    └→ MimeType.valueOf(text)  → MimeTypeUtils.parseMimeType          MimeType.java:739
  MessageHeaderAccessor#getMimeType 계열            MessageHeaderAccessor.java:441
    └→ MimeType.valueOf(value.toString())

[ spring-messaging — RSocket ]
  RSocketMessageHandler (data/metadata mime type)  RSocketMessageHandler.java:101, :436, :441
    └→ MimeTypeUtils.parseMimeType(str)
  DefaultRSocketRequesterBuilder                   DefaultRSocketRequesterBuilder.java:218
    └→ MimeTypeUtils.parseMimeType(WellKnownMimeType...)
  PayloadMethodArgumentResolver                    PayloadMethodArgumentResolver.java:204
    └→ MimeTypeUtils.parseMimeType(stringHeader)
```

이 지도가 말해 주는 것은 두 가지다.\
첫째, `putParameter` 한 줄의 판정 변화는 위 모든 진입점에 동시에 반영된다 — 그래서 이 수정은 순수한 버그 픽스가 아니라 **파싱 계약의 변경**으로 다뤄야 하고, README가 영향 절을 따로 두는 이유가 된다.\
둘째, 예외 타입은 경계에서 한 번 감싸인다.\
`spring-web` 쪽 호출자는 `InvalidMediaTypeException`을 보고, `spring-messaging` 쪽은 `InvalidMimeTypeException`을 그대로 본다.\
새 예외 타입이 도입되지 않았으므로 어느 쪽에서도 catch 절을 고칠 일은 없다.

## 5. 관련 개념

### 5-1. 상태 기계 파서와 "상태 없는 상태"

이 파서의 `ParserState`는 enum 상수마다 `process`를 오버라이드한 형태다.\
enum 상수는 JVM에 클래스당 하나씩만 존재하므로, 상태가 필드를 갖는 순간 모든 파싱 세션이 그것을 공유해 버린다.\
그래서 여기서는 상태를 **전이 함수**로만 쓰고 데이터는 전부 `MimeTypeParser` 인스턴스가 들고 있다(`MimeTypeUtils.java:384-398`).\
스프링 코드베이스에서 반복되는 관용구이며, "상태 객체는 로직, 컨텍스트 객체는 데이터"라는 분업으로 읽으면 된다.

> **전이 함수(transition function)** — 지금 상태와 입력 하나를 받아 다음 상태를 돌려주는 함수.\
> 예: `TYPE.process('/', parser)`는 type을 확정하고 `SUBTYPE`을 돌려준다.

`onEof`가 기본 빈 구현(`MimeTypeUtils.java:636-638`)이고 필요한 상태만 오버라이드한다는 점도 같은 맥락이다.\
입력이 갑자기 끝났을 때 "지금까지 모은 것을 흘려보내도 되는 상태"인지가 상태마다 다르기 때문에, 그 판단을 상태 자신이 갖는다.\
`PARAM_NAME`이 `onEof`를 오버라이드하지 않는 것이 대표적이다 — `a/b;x`처럼 값 없이 끝난 입력은 아무것도 emit하지 않고, `parse()`의 `parsed == null` 검사가 예외로 마무리한다(`MimeTypeUtils.java:417-419`).

### 5-2. MIME 파라미터 이름의 대소문자 규칙

RFC 2045 5.1은 type·subtype·파라미터 이름이 대소문자를 구분하지 않는다고 규정하고, HTTP 명세도 같다.\
`MimeType`은 이를 두 방식으로 지킨다.\
type·subtype은 생성자에서 아예 소문자로 정규화해 저장하고(`MimeType.java:158-159`), 파라미터 이름은 정규화하지 않고 **비교만 대소문자 무시**로 하는 자료구조에 담는다(`MimeType.java:232`).\
후자를 택한 이유는 `toString`과 예외 메시지가 사용자가 실제로 보낸 표기를 그대로 보여줘야 하기 때문이다.\
값(value)은 이 규칙에서 제외된다 — `charset=UTF-8`과 `charset=utf-8`이 같은지는 `Charset` 쪽 규칙이지 맵의 규칙이 아니다.

> **RFC(request for comments)** — 인터넷 표준을 적어 둔 문서 묶음. 번호로 인용한다.\
> 예: RFC 2045는 MIME의 메시지 형식을, RFC 6838은 미디어 타입 등록 절차를 정한다.

### 5-3. LinkedCaseInsensitiveMap의 두 맵 구조

앞서 본 대로 이 클래스는 `targetMap`(원래 표기 키 -> 값, 삽입 순서 보존)과 `caseInsensitiveKeys`(소문자 키 -> 원래 표기 키) 두 개를 동기화하며 유지한다.\
그 결과 세 가지 성질이 동시에 성립한다.

```text
  put("Charset", "utf-8")
    caseInsensitiveKeys : {"charset" → "Charset"}
    targetMap           : {"Charset" → "utf-8"}         ← 표기·순서 보존

  get("CHARSET")
    convertKey → "charset" → caseInsensitiveKeys 조회 → "Charset" → targetMap 조회 → "utf-8"

  put("CHARSET", "euc-kr")
    caseInsensitiveKeys.put("charset","CHARSET") → 옛 표기 "Charset" 반환
    targetMap.remove("Charset") → "utf-8" 회수
    targetMap.put("CHARSET","euc-kr")
    반환값 = "utf-8"                                    ← 이 반환값이 중복 신호가 된다
```

즉 이 맵은 "대소문자 무시 조회"와 "원래 표기 보존"을 함께 주는 대신, 표기가 다른 덮어쓰기가 일어나면 `put` 반환값으로 그 사실을 알린다.\
PR #37008은 그 신호를 쓰는 첫 호출자를 만든 셈이다.\
표기가 보존된다는 성질 덕분에 예외 메시지의 `duplicate parameter 'DUPE="2"'`도 대문자 그대로 나온다.

### 5-4. 파싱 결과 캐싱 (ConcurrentLruCache)

`MimeTypeUtils`는 파싱 결과를 용량 64의 `ConcurrentLruCache`에 담아 재사용한다(`MimeTypeUtils.java:166-167`, `ConcurrentLruCache.java:51`).\
같은 `Content-Type` 문자열이 요청마다 반복해서 들어오는 서버 환경을 겨냥한 최적화다.\
캐시 키는 원본 문자열이므로 `text/plain;charset=utf-8`과 `text/plain;CHARSET=utf-8`은 서로 다른 캐시 항목이 되고, 각각 별도로 파싱된다.\
예외가 던져진 입력은 캐시에 들어가지 않으므로 잘못된 입력은 매번 같은 결과를 받는다.\
이 성질이 3-1에서 말한 "캐시 기인 비결정성 없음"의 근거다.

### 5-5. 참고 — 이미 있는 개념 문서

이 무대와 직접 겹치는 개념 문서는 아직 `../../concepts/`에 없다.\
인접 문서로는 컴파일·런타임 층 구분을 다룬 [`../../concepts/compile-runtime-layers/compile-runtime-layers.md`](../../concepts/compile-runtime-layers/compile-runtime-layers.md)가 있으나 이 PR의 주제와는 무관하다.
