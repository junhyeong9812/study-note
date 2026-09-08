# PR #37008 분석 — MIME 파라미터 대소문자 중복이 검사망을 빠져나가는 결함

> 기준: PR head `019c822ff69`(base `68e6acd37ed`). 이하 `MimeTypeUtils.java:NNN`은 **PR head 기준**이며,
> 수정으로 주석 2줄이 늘었으므로 base에서는 `:440` 이후가 2씩 작다. `MimeType.java`·`LinkedCaseInsensitiveMap.java`는
> 이 PR이 건드리지 않아 base와 동일하다.
>
> 이 문서는 결함의 인과 사슬만 다룬다. 서사 해설은 README.md, 무대 지도는 structure.md, 테스트별 해설은 tests.md,
> 이해 게이트 문답은 gates.md가 소유한다.

## 0. 결론

**결함**: `MimeTypeParser`가 파라미터를 모으는 누산 맵이 `LinkedHashMap`이라 `dupe`와 `DUPE`를 다른 키로 보고,
그 결과 이미 존재하던 중복 검사(`put(...) != null`)가 대소문자만 다른 중복 파라미터에 대해 발동하지 않는다.
검사망을 통과한 두 항목은 곧바로 `MimeType` 생성자의 `LinkedCaseInsensitiveMap`에서 같은 키로 병합되어
앞 값이 예외도 로그도 없이 사라진다.

**수정**: 누산 맵을 `new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)`로 교체한다(`MimeTypeUtils.java:442`).
검사 로직은 한 글자도 바뀌지 않는다 — 이미 있던 분기가 도달하지 못하던 입력에 도달하게 만드는 수정이다.

**상태**: OPEN. 라벨 `status: waiting-for-triage`, `in: web`. 2026-07-06에 구 파서 기준으로 열렸고
2026-07-24 커밋 `079992021cf`가 파서를 상태 기계로 전면 재작성해 수정 대상이 사라졌으며,
2026-08-13에 새 파서 기준으로 재작성해 force-push했다(6.3절).

## 1. 무대

결함이 사는 좌표는 모듈·파일·메서드 세 축으로 좁혀진다.

| 축 | 값 |
|---|---|
| 모듈 | `spring-core` |
| 파일 | `spring-core/src/main/java/org/springframework/util/MimeTypeUtils.java` |
| 결함 지점 | `MimeTypeUtils.MimeTypeParser#putParameter` (`:438-447`, 문제의 줄은 `:442`) |
| 협력 클래스 | `MimeType`(`MimeType.java`), `LinkedCaseInsensitiveMap`(`LinkedCaseInsensitiveMap.java`) |
| 공개 진입 API | `MimeTypeUtils.parseMimeType(String)` `:194` / `MimeTypeUtils.parseMimeTypes(String)` `:216` / `MimeType.valueOf(String)` `MimeType.java:738` |

`MimeTypeUtils`는 인스턴스를 만들 수 없는 정적 파사드이고, 파싱 1회분의 가변 상태는 private static final 중첩
클래스 `MimeTypeParser`(`:382`)가 들고 있다. 문자열에서 `MimeType`으로 가는 변환은 이 클래스가 유일한 통로다.

누가 부르나. `MediaType.parseMediaType`을 거쳐 HTTP `Content-Type`·`Accept` 헤더 처리가 전부 여기로 오고,
`spring-messaging`의 STOMP `content-type` 헤더, `DefaultContentTypeResolver`, RSocket의 data/metadata mime type,
`MediaTypeFactory`의 `mime.types` 정적 초기화가 같은 길목을 지난다(호출처 지도는 structure.md 4절).
즉 서버로 들어오는 거의 모든 미디어 타입 문자열이 이 파서를 통과하며, 그래서 `putParameter` 한 줄의 판정 변화는
**순수 버그 픽스가 아니라 파싱 계약의 변경**으로 다뤄야 한다.

## 2. 전체 메서드 그래프

파싱은 "정적 진입점 -> 캐시 -> 파서 인스턴스 -> 문자 루프 -> 값 객체 생성" 다섯 단계다. 결함은 넷째 단계에서
심어지고 다섯째 단계에서 손실로 확정된다.

```
  MimeType.valueOf(String)                                   MimeType.java:738
      |
      v
  MimeTypeUtils.parseMimeType(String)                        MimeTypeUtils.java:194
      |-- !StringUtils.hasLength      -> InvalidMimeTypeException      :195-197
      |-- startsWith("multipart")     -> parseMimeTypeInternal 직행    :199-201
      +-- 그 외 -> cachedMimeTypes.get(input)                          :202
                      (ConcurrentLruCache<String, MimeType>, 용량 64)  :166
                      miss -> generator = MimeTypeUtils::parseMimeTypeInternal
                                  |
                                  v
                    parseMimeTypeInternal(String)                      :205
                        return new MimeTypeParser(mimeType).parse()    :206
                                  |
                                  v
  MimeTypeParser.parse()                                               :410
      for (index = 0 .. input.length()-1)
          c = input.charAt(index)                                      :413
          state = state.process(c, this)                               :414
      state.onEof(this)                                                :416
      parsed == null -> InvalidMimeTypeException                       :417-419
                                  |
      ParserState 전이 (enum, 상태는 전이 함수만 갖고 데이터는 파서가 보유)  :469
        INITIAL :471 -> TYPE :482 -> SUBTYPE :507 -> WHITESPACE :524
          -> PARAM_NAME :541 -> PARAM_NAME_END :556 -> PARAM_VALUE_START :569
          -> PARAM_VALUE_TOKEN :584 | PARAM_VALUE_QUOTED :600 -> PARAM_VALUE_ESCAPED :619
                                  |
        파라미터 확정 경로는 전부 한 점으로 모인다
                                  v
      ParserState.extractParameter(parser, value)                      :631
          Assert.hasText(parser.paramName, ...)                        :632
          parser.putParameter(parser.paramName, value)                 :633
                                  |
                                  v
  MimeTypeParser.putParameter(name, value)            [!] 결함이 사는 곳  :438
      if (this.parameters == null)
          this.parameters = new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)  :442
          (base 에서는 이 자리가 new LinkedHashMap<>(4))
      if (this.parameters.put(name, value) != null)                    :444
          throw new InvalidMimeTypeException(input, "duplicate parameter '...'")  :445
                                  |
      입력 끝 -> 각 상태의 onEof -> parser.emitMimeType()               :449
                                  v
  MimeTypeParser.buildMimeType()                                       :453
      wildcard 검증 후 new MimeType(type, subtype, this.parameters)     :458
                                  |
                                  v
  MimeType(String, String, Map)                            MimeType.java:153
      checkToken(type) / checkToken(subtype)                           :156-157
      this.type/subtype = toLowerCase(Locale.ROOT)                     :158-159
      this.parameters = createParametersMap(parameters)                :160
             |
             v
      createParametersMap(Map)                                         :230
          map = new LinkedCaseInsensitiveMap<>(parameters.size(), Locale.ROOT)  :232
          parameters.forEach((k, v) -> { checkParameters(k, v); map.put(k, v); }) :233-236
                                       ^^^^^^^^^^^^^^^^^^^^^^
                                       [!] put 반환값을 람다가 버린다 = 조용한 소실
          return Collections.unmodifiableMap(map)                      :237
      containsKey("charset") -> resolvedCharset = Charset.forName(...)  :161-163
```

데이터 흐름의 요점은 **파라미터 맵이 두 번 등장한다**는 것이다. 파서가 파싱 도중 쓰는 누산 맵
(`MimeTypeParser.parameters` `:394`)과, `MimeType`이 최종 보관하는 결과 맵(`MimeType.parameters` `MimeType.java:104`).
중복 검사는 전자에서(`:444`), 대소문자 무시 조회는 후자에서(`MimeType.java:232`) 일어난다.
두 맵의 키 규칙이 어긋난 것이 결함의 전부다.

## 2.5 핵심 이름표 사전

이 흐름에서 헷갈리는 것은 "키"가 세 가지 표기로 돌아다닌다는 점이다. 사용자가 실제로 보낸 원본 표기,
`convertKey`가 만드는 소문자 정규화 표기, 그리고 그 둘을 잇는 색인. 아래 항목은 각각 무엇을 들고 있는지를 밝힌다.

### 2.5.1 파서 쪽 (`MimeTypeUtils.java`)

파서 쪽 이름표는 파싱 1회분의 가변 컨텍스트와 그 위를 오가는 상태 전이 함수로 나뉜다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `parseMimeType(String)` `:194` | 공개 진입점. 빈 문자열 거르고 멀티파트만 캐시 우회 | `String` -> `MimeType` | `MimeType.valueOf`, `MediaType.parseMediaType`, STOMP/RSocket 헤더 처리 | 결함의 노출면 전체가 이 메서드 뒤에 있다 |
| `cachedMimeTypes` `:166` | 파싱 결과 LRU 캐시(용량 64), 생성자는 `parseMimeTypeInternal` | 원본 문자열 -> `MimeType` | `parseMimeType`이 매 호출마다 | 예외가 난 입력은 캐시에 안 들어가므로, 수정 후 "처음엔 통과 나중엔 거절" 같은 캐시 기인 비결정성이 없다 |
| `parseMimeTypeInternal(String)` `:205` | 파서 인스턴스를 새로 만들어 1회 파싱 | `String` -> `MimeType` | 캐시 miss 시, 멀티파트 직행 시 | 파싱 1회분 상태가 인스턴스에 갇힌다는 보장 |
| `MimeTypeParser` `:382` | 파싱 1회분 **가변 컨텍스트**. 상태 enum이 공유하는 데이터 홀더 | - | `parseMimeTypeInternal`이 생성 | 상태가 여기 있으므로 enum 상수를 공유해도 안전 |
| `input` `:384` | 원본 입력 문자열(final) | - | 모든 상태가 `substring`으로 조각을 뜬다 | 예외 메시지에 원본이 그대로 들어가는 근거 |
| `index` `:386` | 지금 읽는 문자 위치 | - | `parse()`의 for가 전진시킴 | 직접 관련 없음 |
| `mark` `:388` | 현재 토큰이 시작된 위치 | - | 각 상태가 구분자를 만나기 직전에 설정 | 직접 관련 없음 |
| `type` / `subtype` `:390` / `:392` | 확정된 type·subtype(기본값 빈 문자열) | - | `TYPE`/`SUBTYPE` 상태가 채움 | `WHITESPACE.onEof`가 `type.isEmpty()`로 emit 여부를 가르는 데 씀 `:535` |
| `parameters` `:394` | **누산 맵**(@Nullable, 첫 파라미터에서 지연 생성) | 이름 -> 값 | `putParameter`가 쓰고 `buildMimeType`이 읽어 넘김 | **이 필드의 구현 타입이 결함 그 자체** |
| `paramName` `:396` | 값이 오기 전에 잡아 둔 파라미터 이름(원본 표기) | - | `PARAM_NAME`이 설정, `extractParameter`가 소비 | 원본 표기 그대로 `putParameter`에 전달되므로 예외 메시지의 `DUPE`가 대문자로 남는다 |
| `parsed` `:398` | 완성된 결과(@Nullable) | - | `emitMimeType`이 설정, `parse()`가 null 검사 | `a/b;x`처럼 값 없이 끝난 입력을 잡는 최후 방어선 `:417` |
| `parse()` `:410` | 문자 하나마다 상태를 갈아 끼우는 단일 루프 | 없음 -> `MimeType` | `parseMimeTypeInternal` | 결함과 무관하지만 모든 파라미터가 이 루프를 통과 |
| `resolveBareType(String)` `:430` | 슬래시 없이 끝난 후보를 `*`일 때만 `*/*`로 승격 | `String` -> void(필드 설정) | `TYPE.process`/`TYPE.onEof` | 범위 밖 |
| `putParameter(String, String)` `:438` | 누산 맵에 넣고 **put 반환값으로 중복 판정** | (이름, 값) -> void 또는 throw | `extractParameter`가 파라미터를 확정할 때마다 | 결함 지점. 로직이 아니라 `:442`의 자료구조가 문제 |
| `emitMimeType()` `:449` / `buildMimeType()` `:453` | 누산 맵을 `MimeType` 생성자에 넘겨 결과 확정 | -> `MimeType` | 각 상태의 `onEof`, 구분자 종료 | 누산 맵이 여기서 결과 맵으로 복사되며 병합이 일어난다 |
| `ParserState` `:469` | 전이 함수의 묶음(enum). **자기 상태를 갖지 않는다** | (char, parser) -> 다음 상태 | `parse()`가 매 문자마다 | 상태 공유 안전성의 전제 |
| `ParserState.process(char, parser)` `:636` | 각 상수가 오버라이드하는 전이 함수(abstract) | (char, parser) -> `ParserState` | `parse()` | 직접 관련 없음 |
| `ParserState.onEof(parser)` `:638` | 입력이 갑자기 끝났을 때 마지막 조각을 흘려보낼지 결정. 기본은 빈 구현 | (parser) -> void | `parse()`가 루프 후 1회 | `PARAM_NAME`이 오버라이드하지 않는 것이 값 없는 입력을 거르는 장치 |
| `ParserState.extractParameter(parser, value)` `:631` | 모든 파라미터 확정 경로의 **단일 합류점** | (parser, 값) -> void | `PARAM_VALUE_TOKEN`/`QUOTED`/`ESCAPED`의 process·onEof | 중복 판정을 한 곳에서 고칠 수 있는 이유 |

### 2.5.2 값 객체 쪽 (`MimeType.java`)

값 객체 쪽 이름표는 파싱이 끝난 결과를 보관하고 조회하는 계약을 담는다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `MimeType(String, String, Map)` `:153` | 파서가 부르는 생성자. type·subtype 소문자화 + 파라미터 복사 | (type, subtype, 누산 맵) -> 인스턴스 | `buildMimeType` `:458` | 병합이 실제로 일어나는 자리 |
| `parameters` (필드) `:104` | **결과 맵**. `unmodifiableMap`으로 봉인 | - | `getParameter`/`getParameters`/`toString` | 이쪽 규칙(대소문자 무시)이 처음부터 옳았다 |
| `createParametersMap(Map)` `:230` | 누산 맵을 `LinkedCaseInsensitiveMap`으로 복사하며 토큰 검사 | `Map` -> 봉인된 `Map` | 생성자 `:160` | `map.put(k, v)`의 반환값을 `forEach` 람다가 버린다. 소실이 무음이 되는 지점 `:235` |
| `checkParameters(String, String)` `:244` | 이름은 토큰, 값은 토큰이거나 따옴표 문자열이어야 함 | (이름, 값) -> void 또는 IAE | `createParametersMap`의 forEach | 대소문자는 보지 않으므로 이 검사로는 결함이 안 걸린다 |
| `PARAM_CHARSET` `:59` | 상수 `"charset"` | - | 생성자 `:161`, `getCharset` | 결과 맵이 대소문자 무시라 `CHARSET=`로 와도 여기서 잡힌다 |
| `TOKEN` `:61` | RFC 2616 2.2 토큰 문자 집합(BitSet) | - | `checkToken` | 범위 밖 |
| `resolvedCharset` `:106` | `charset` 파라미터를 미리 해석해 둔 캐시(transient) | - | 생성자 `:161-163` | 결함 케이스에서 "어느 charset이 이겼는지"가 조용히 결정되던 자리 |
| `getParameter(String)` `:353` | 결과 맵 조회. 대소문자 무시 | 이름 -> 값 또는 null | 호출자 전반 | 결과 맵이 case-insensitive라고 선언하는 공개 계약 |
| `valueOf(String)` `:738` | 정적 팩터리. 그대로 `parseMimeType`에 위임 | `String` -> `MimeType` | 테스트·`DefaultContentTypeResolver` 등 | 테스트가 쓰는 진입점 |

### 2.5.3 자료구조 쪽 (`LinkedCaseInsensitiveMap.java`)

자료구조 쪽 이름표는 원본 표기 보존과 대소문자 무시 판정을 나눠 맡는 두 맵과 그 사이를 잇는 지역 변수들이다.

| 이름표 | 역할 | 입력에서 출력 | 누가 언제 부르나 | 결함과의 관계 |
|---|---|---|---|---|
| `targetMap` `:57` | **원래 표기 그대로**의 키에서 값으로, 삽입 순서 보존(`LinkedHashMap`) | - | 순회·`toString`·`get`의 최종 조회 | 예외 메시지·파싱 결과에서 원본 대소문자가 유지되는 근거 |
| `caseInsensitiveKeys` `:59` | 소문자 정규화 키에서 원래 표기 키로 가는 색인(`HashMap`) | - | `containsKey` `:158`, `get` `:168`, `put` `:191` | 대소문자 무시 판정의 실체 |
| `locale` `:61` | 키 정규화에 쓸 로케일. 생성자 인자가 null이면 `Locale.getDefault()` `:131` | - | `convertKey` | `Locale.ROOT`를 명시하지 않으면 "중복인가"가 JVM 로케일에 좌우된다 |
| `convertKey(String)` `:332` | `key.toLowerCase(getLocale())` | 키 -> 정규화 키 | `put`/`get`/`containsKey` | 터키어 로케일에서 대문자 I가 점 없는 소문자(U+0131)가 되는 문제의 자리 |
| `put(String, V)` `:190` | 정규화 키 충돌 시 옛 표기 항목을 제거하고 **그 값을 반환** | (키, 값) -> 이전 값 또는 null | 이 PR이 만든 첫 호출자가 `putParameter` `:444` | 이 반환 규칙이 중복 신호가 된다 |
| `oldKey` (지역) `:191` | `caseInsensitiveKeys.put`이 돌려준 이전 원본 표기 키 | - | `put` 내부 | null이면 새 키, non-null이고 표기가 다르면 케이스 충돌 |
| `oldKeyValue` (지역) `:192,:194` | 표기가 달라 `targetMap`에서 제거된 옛 값 | - | `put` 내부 | `dupe="1"`이면 `"1"`. 이 값이 중복 신호로 돌아온다 |
| `oldValue` (지역) `:196` | 완전히 같은 표기로 덮어썼을 때의 이전 값 | - | `put` 내부 | 정확 중복(`dupe`/`dupe`)에서 발동하던 기존 경로 |
| `LinkedCaseInsensitiveMap(int, Locale)` `:114` | 초기 용량과 로케일을 받는 생성자 | - | `MimeType.createParametersMap` `:232`, 수정 후 `putParameter` `:442` | 두 맵이 **같은 인자**를 쓰게 맞추는 것이 수정의 요점 |

## 3. 결함 경로 단계 추적

세 입력을 같은 축으로 비교한다. A는 정상, B는 정확 중복(수정 전에도 걸리던 것), C는 결함 케이스다.
`put` 반환 열은 `MimeTypeParser.putParameter` `:444`의 `this.parameters.put(name, value)` 반환값이다.

| 단계 | A `text/plain;charset=utf-8` | B `text/plain;dupe="1";dupe="2"` (수정 전) | C `text/plain;dupe="1";DUPE="2"` (수정 전) |
|---|---|---|---|
| 파라미터 1 확정 | `extractParameter(parser, "utf-8")`, `paramName="charset"` | `paramName="dupe"`, 값 `"1"`(따옴표 포함) | `paramName="dupe"`, 값 `"1"`(따옴표 포함) |
| 누산 맵 생성 `:442` | `LinkedHashMap` (base) | `LinkedHashMap` | `LinkedHashMap` |
| put 1 반환 | null, 통과 | null, 통과 | null, 통과 |
| 파라미터 2 확정 | 없음 | `paramName="dupe"`, 값 `"2"` | `paramName="DUPE"`, 값 `"2"` |
| put 2 반환 | 해당 없음 | `"1"` (같은 키) | **null** (`LinkedHashMap`은 `dupe`와 `DUPE`를 다른 키로 본다) |
| `:444` 판정 | 해당 없음 | `!= null` 참, throw | `!= null` 거짓, **통과** [!] |
| `buildMimeType` `:453` | 도달 | 미도달 | 도달. 누산 맵 = `{dupe=1, DUPE=2}` |
| `createParametersMap` `MimeType.java:232` | `{charset=utf-8}` | 해당 없음 | `put("dupe", ...)`로 targetMap `{dupe=1}` |
| 같은 메서드 두 번째 put | 해당 없음 | 해당 없음 | `put("DUPE", ...)`가 `caseInsensitiveKeys["dupe"]` 충돌 감지 -> `targetMap.remove("dupe")` -> `"1"` 반환 |
| 그 반환값의 소비 | 해당 없음 | 해당 없음 | `forEach` 람다가 **버린다** `:235`. [!] 조용한 소실 |
| 최종 결과 | `text/plain;charset=utf-8` | `InvalidMimeTypeException` | `text/plain;DUPE="2"` (예외 없음) |

수정 후에는 C의 두 번째 행부터 갈린다.

| 단계 | C, 수정 후 |
|---|---|
| 누산 맵 생성 `:442` | `new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)` |
| put 1 (`dupe`) | `caseInsensitiveKeys` 신규 -> `oldKey=null` -> `oldKeyValue=null`, `oldValue=null` -> **null 반환**, 통과 |
| put 2 (`DUPE`) | `caseInsensitiveKeys.put("dupe","DUPE")`가 옛 표기 `"dupe"` 반환 -> `oldKey != null && !oldKey.equals("DUPE")` 참 -> `targetMap.remove("dupe")`로 옛 값 회수 -> **그 값 반환** |
| `:444` 판정 | `!= null` 참 -> `InvalidMimeTypeException(input, "duplicate parameter 'DUPE=...'")` |
| 메시지의 표기 | `paramName`이 원본 `"DUPE"`이고 `input`이 원본 문자열이므로 둘 다 대문자 그대로 나온다 |

A(정상 입력)는 수정 전후 관측 가능한 차이가 없다. `LinkedCaseInsensitiveMap`은 키의 원래 표기와 삽입 순서를
보존하므로 누산 맵의 키·값·순회 순서가 이전과 동일하고, 그 맵은 어차피 `MimeType` 생성자에서
또 하나의 `LinkedCaseInsensitiveMap`으로 복사된 뒤 버려진다.

## 4. 계약과 위반

이 무대가 지키기로 되어 있던 계약과, 결함이 그중 무엇을 어기는지를 나란히 놓는다.

| 계약 | 출처 | 결함이 어기는가 |
|---|---|---|
| MIME 파라미터 이름은 대소문자를 구분하지 않는다 | RFC 2045 5.1 / `MimeType.createParametersMap`이 `LinkedCaseInsensitiveMap` 사용 `MimeType.java:232` | 위반. 파서 쪽만 대소문자를 구분한다 |
| 같은 파라미터가 두 번 나오면 오류다 | RFC 6838 4.3 / 커밋 `25e8395df80`(gh-36841)이 도입, 테스트 `valueOfDuplicateParameter`가 고정 | 위반. 케이스 변형만 사각지대로 남았다 |
| `getParameter("CHARSET")`과 `getParameter("charset")`은 같은 값을 준다 | `MimeType.getParameter` `:353` + 결과 맵 타입 | 결함이 아니라 전제. 이 전제 때문에 C에서 앞 값이 병합·소실된다 |
| 파라미터 이름의 **원래 표기**는 보존된다(`toString`·예외 메시지에 그대로) | `LinkedCaseInsensitiveMap.targetMap` `:57`, 새 테스트의 메시지 단언 | 수정 후에도 지켜진다. 자료구조 교체가 표기를 바꾸지 않는다 |
| 파싱 판정은 실행 환경에 좌우되지 않는다 | `MimeType`이 `Locale.ROOT`를 명시 `MimeType.java:232`, `LinkedCaseInsensitiveMap` 생성자의 폴백 `:131` | 수정에서 `Locale.ROOT`를 함께 넘겨 유지 |
| 던져지는 예외 타입은 `InvalidMimeTypeException` | `putParameter` `:445`, `spring-web` 경계에서 `InvalidMediaTypeException`으로 감쌈 | 유지. 새 예외 타입을 도입하지 않았다 |
| 파싱 결과 객체의 형태는 바뀌지 않는다 | `MimeType` 생성자가 파라미터를 재복사 `:160` | 유지. 누산 맵은 결과에 도달하지 않는다 |

한 문장으로 줄이면 **규칙이 두 곳에 있었고 한쪽만 옳았다**. 파라미터 이름의 대소문자 규칙이 누산 맵과 결과 맵에
각각 구현돼 있었고, 중복 판정이 있는 쪽(누산 맵)에는 케이스 감각이 없었고 케이스 감각이 있는 쪽(결과 맵)에는
판정이 없었다.

## 5. 수정안

### 5.1 채택한 수정 — 누산 맵의 규칙을 결과 맵에 맞춘다

바뀌는 것은 누산 맵의 구현 타입 한 줄이고, 검사 로직은 그대로다. before/after를 나란히 놓으면 그 범위가 보인다.

```java
// before (base 68e6acd37ed, MimeTypeUtils.java:438-445)
private void putParameter(String name, String value) {
	if (this.parameters == null) {
		this.parameters = new LinkedHashMap<>(4);
	}
	if (this.parameters.put(name, value) != null) {
		throw new InvalidMimeTypeException(this.input, "duplicate parameter '" + name + "=" + value + "'");
	}
}

// after (PR head 019c822ff69, MimeTypeUtils.java:438-447)
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

import도 함께 바뀐다. `java.util.LinkedHashMap` 제거, `java.util.Locale` 추가.
`LinkedCaseInsensitiveMap`은 같은 `org.springframework.util` 패키지라 import가 필요 없다.

**왜 그 위치인가.** 모든 파라미터 확정 경로(토큰 값과 따옴표 값, 구분자 종료와 EOF 종료의 조합)가
`ParserState.extractParameter` `:631` 한 점을 지나 `putParameter` 한 줄로 모인다. 따라서 판정 지점은 하나뿐이고,
그 지점에서 판정의 재료(맵)만 바꾸면 모든 입력 형태에 동시에 적용된다. 검사 로직에는 손댈 곳이 없다.
`put(...) != null` 분기는 이미 옳았고, 다만 그 분기가 도달하지 못하는 입력이 있었을 뿐이다.

**`Locale.ROOT`가 필요한 이유.** 인자 없는 생성자는 `Locale.getDefault()`로 폴백하고(`:131`),
`convertKey`는 그 로케일로 `toLowerCase`를 부른다(`:332-333`). 터키어 로케일에서 대문자 I의 소문자는
점 없는 U+0131이라 보통의 소문자 i와 매칭되지 않으므로, `Charset`과 `charset` 같은 이름이 그 환경에서만
다른 키로 갈려 중복 검사가 환경 의존이 된다. `MimeType.createParametersMap`이 이미 `Locale.ROOT`를 쓰므로
(`MimeType.java:232`) 누산 맵도 같은 인자를 써야 두 맵의 판정이 어긋나지 않는다.

### 5.2 검토하고 기각한 대안

같은 증상을 없애는 다른 네 가지 접근을 검토했고, 각각 다음 이유로 밀렸다.

| 대안 | 기각 이유 |
|---|---|
| 키를 `toLowerCase`해서 `LinkedHashMap`에 저장 | 원본 대소문자 표기가 손실된다. `toString`과 예외 메시지가 사용자가 실제로 보낸 문자열을 보여줘야 진단으로 쓸모가 있다 |
| `LinkedHashMap` 유지 + 정규화 키를 담는 별도 `HashSet` 추적 | 같은 이중 자료구조를 손으로 다시 구현하는 것이고, 코드만 늘어난다 |
| put마다 기존 키를 `equalsIgnoreCase`로 순회 | O(n^2). 파라미터가 보통 0~2개라 실측 차이는 없겠지만, 하우스 자료구조가 있는데 손 루프를 쓸 이유가 없다 |
| 검사를 `MimeType` 생성자 쪽으로 옮겨 결과 맵에서 판정 | 예외 메시지가 원본 입력 문자열(`this.input`)을 잃는다. 생성자는 `MimeType(type, subtype, map)` 형태로도 공개돼 있어 프로그래밍 방식 생성까지 계약이 바뀐다 |

`LinkedCaseInsensitiveMap`을 고른 결정적 이유는 **Spring이 정확히 이 용도로 만든 하우스 자료구조**라는 점이다.
파서와 저장소가 같은 키 의미론을 쓴다는 의도가 코드에 드러나고, diff가 한 줄이라 업스트림이 받아들이기 쉽다.
비용도 사실상 0이다. 초기 용량 4에 항목 0~2개다.

### 5.3 테스트

추가된 테스트는 한 건이고, 기존 정확 중복 테스트 바로 아래에 놓였다.

```java
// spring-core/src/test/java/org/springframework/util/MimeTypeTests.java (PR head :177-181)
@Test
void valueOfDuplicateParameterWithDifferentCase() {
	assertThatThrownBy(() -> MimeType.valueOf("text/plain;dupe=\"1\";DUPE=\"2\"")).isInstanceOf(InvalidMimeTypeException.class)
			.hasMessageContaining("Invalid mime type \"text/plain;dupe=\"1\";DUPE=\"2\"\": duplicate parameter 'DUPE=\"2\"'");
}
```

기존 정확 중복 테스트 `valueOfDuplicateParameter`(`:171-175`) 바로 아래에 두어 둘이 같은 규칙의 두 사례임을
코드 배치로 드러낸다. 단언 세 가지 — 예외가 던져지는가, 타입이 `InvalidMimeTypeException`인가,
메시지에 원본 입력과 문제의 파라미터가 **원래 대소문자 그대로** 들어가는가 — 중 셋째가
`LinkedCaseInsensitiveMap`의 표기 보존 성질을 눈에 보이는 계약으로 만든다. 테스트별 상세는 tests.md 소유.

## 6. 범위 밖과 인접 영향

### 6.1 하위 호환 — 이것은 동작 변경이다

입력 세 갈래를 수정 전후로 비교하면 바뀌는 지점이 한 줄임이 드러난다.

| 입력 | 수정 전 | 수정 후 |
|---|---|---|
| `text/plain;dupe="1";dupe="2"` | 거부 | 거부 |
| `text/plain;dupe="1";DUPE="2"` | 통과, 뒤 값만 남음 | 거부 |
| 중복 없는 모든 입력 | 통과 | 통과(결과 객체 동일) |

둘째 행이 바뀌는 전부다. 대소문자가 다른 중복 파라미터를 보내던 클라이언트는 성공 대신 예외를 받으므로,
PR 본문에 "Note on impact" 절을 따로 두었다. 자리매김은 "gh-36841이 정확 중복에 대해 이미 내린 결정의
사각지대를 메우는 후속"이다. 예외 타입이 그대로이므로 어느 호출자도 catch 절을 고칠 필요는 없다.

### 6.2 같은 패턴을 찾아볼 만한 곳

"규칙이 두 곳에 있다"는 형태를 인접 영역에서 찾아보면 네 자리가 후보로 걸리고, 그중 실제 사각지대는 없었다.

- **`MimeType`의 type·subtype**: 이쪽은 생성자에서 아예 소문자로 정규화해 저장하므로(`MimeType.java:158-159`)
  같은 종류의 사각지대가 없다. 파라미터 이름만 "정규화하지 않고 비교만 대소문자 무시"를 택했고, 그 이유는
  `toString`과 예외 메시지가 사용자 표기를 보여줘야 하기 때문이다.
- **파라미터 값(value)**: 이 규칙의 대상이 아니다. `charset=UTF-8`과 `charset=utf-8`이 같은지는 `Charset`
  쪽 규칙이지 맵의 규칙이 아니다. 이 PR은 값을 건드리지 않는다.
- **`MediaType`**: `MimeType`을 상속하고 파싱은 그대로 `MimeTypeUtils.parseMimeType`에 위임하므로
  자동으로 같은 판정을 받는다. 별도 수정 지점이 없다.
- **`HttpHeaders`의 다른 헤더 파서**: 미확인. 이 PR의 조사 범위에 넣지 않았다.

### 6.3 구 파서 시절의 첫 구현과 무엇이 달랐나

PR은 2026-07-06에 열렸고, 그때의 `MimeTypeUtils`는 인덱스로 문자열을 잘라 나가는 절차형 코드였다.
누산 맵과 중복 검사가 `parseMimeTypeInternal` 본문 한가운데 인라인으로 있었다.

```java
// 079992021cf^ (구 파서), MimeTypeUtils.java:230-259 발췌
Map<String, String> parameters = null;
do {
	...
	String parameter = mimeType.substring(index + 1, nextIndex).trim();
	if (parameter.length() > 0) {
		if (parameters == null) {
			parameters = new LinkedHashMap<>(4);                       // <- 첫 구현의 수정 대상 (:249)
		}
		int eqIndex = parameter.indexOf('=');
		if (eqIndex >= 0) {
			String attribute = parameter.substring(0, eqIndex).trim();
			String value = parameter.substring(eqIndex + 1).trim();
			if (parameters.put(attribute, value) != null) {            // (:255)
				throw new InvalidMimeTypeException(mimeType, "duplicate parameter '" + parameter + "'");
			}
		}
	}
	index = nextIndex;
}
while (index < mimeType.length());
```

첫 구현은 이 `:249` 한 줄을 `new LinkedCaseInsensitiveMap<>(4, Locale.ROOT)`로 바꾸는 것이었고,
테스트 이름은 `rejectsDuplicateParameterWithDifferentCase`였다(당시 정확 중복 테스트는 `rejectsDuplicateParameter`).
2026-07-24 커밋 `079992021cf`("Improve MimeType parser for RFC compliance", gh-36729, Brian Clozel)가
파서를 상태 기계로 전면 재작성하면서 이 메서드 본문이 통째로 사라졌다.

현재 head와 비교하면 차이는 네 가지다.

| 축 | 구 파서 첫 구현 | 새 파서 재작성본 |
|---|---|---|
| 수정 지점 | `parseMimeTypeInternal` 본문 인라인(`:249`) | 중첩 클래스 메서드 `MimeTypeParser.putParameter`(`:442`) |
| 판정 지점 개수 | 1개(do-while 안 한 곳) | 1개. `extractParameter`가 모든 경로를 모아 주므로 여전히 한 곳 |
| 예외 메시지 재료 | 원본 세그먼트 `parameter`(`name=value` 통째) | `name + "=" + value` 조립 |
| 테스트 이름 | `rejectsDuplicateParameterWithDifferentCase` | `valueOfDuplicateParameterWithDifferentCase`. 인접 기존 테스트가 이름을 바꿨으므로 짝을 맞춤 |

진단(두 맵의 규칙 불일치)과 수정 전략(누산 맵을 결과 맵에 맞춘다)은 그대로 유효했다. 바뀐 것은 그 전략을
꽂을 좌표뿐이다. 다만 그 사실은 **재작성된 코드를 실제로 읽어야만** 확인할 수 있었다.
원래 diff를 기준으로 rebase만 했다면 존재하지 않는 메서드를 고치는 충돌 해결을 하게 된다.
재작성 사실과 새 수정 지점은 2026-08-13에 커뮤니티 기여자 `yashsiwacha`가 코멘트로 짚어 주었고,
제안을 실코드로 확인한 뒤 채택해 커밋에 `Co-authored-by` 크레딧을 넣고 반영 결과를 코멘트로 알렸다.
