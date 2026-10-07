# architecture/05-text-length-segmentation-and-case — 길이의 네 가지 뜻, 안전한 자르기, 로캘 의존 대소문자, 혼동 문자 — 정리 (힌트)

## 해결하는 문제

"글자 수"라는 말은 하나인데, 컴퓨터가 셀 수 있는 단위는 넷이다.\
어느 단위로 세느냐에 따라 같은 문자열의 길이가 1이 되기도, 18이 되기도 한다.

```text
  "👨‍👩‍👧" (가족 이모지 하나)
   사람이 보는 칸(그래핌)     1
   코드 포인트               5   (남자 + ZWJ + 여자 + ZWJ + 여자아이)
   UTF-16 코드 유닛(length)  8
   UTF-8 바이트             18   (Java 21 실험 1)
```

- 검증·저장·자르기·비교를 서로 다른 단위로 하면, 각각은 맞는데 합쳐서 틀린다.

쉬운 예: 이삿짐을 "10개까지"라고 했다.
- 보내는 사람은 상자를 셌고, 받는 사람은 상자 안 물건을 셌다. 같은 짐이 한쪽에서는 통과, 다른 쪽에서는 초과다.

똑같은 구조다.\
화면은 그래핌으로, Java·JS의 `length`는 UTF-16 단위로, DB는 "문자"로, 바이트 한도는 UTF-8 바이트로 센다.

실무 예:
- 프론트는 "10자까지" 통과시켰는데, DB `VARCHAR(10)` 저장에서 `value too long`이 난다. 국기 이모지 10개는 코드 포인트 20개다.
- 알림 미리보기를 잘랐더니 🇰🇷가 🇰 하나(파란 글자 K 모양)로 남는다.
- 터키어 로캘 서버에서 `"TITLE".toLowerCase()`가 `tıtle`이 되어 설정 키 비교가 실패한다.
- Spotify가 2013년 글에서 공개한 사고: `ᴮᴵᴳᴮᴵᴿᴰ`라는 이름으로 가입해 다른 사람 계정(원문의 예시 이름 `bigbird`)의 비밀번호를 바꿀 수 있었다. 사고 자체는 글보다 몇 년 앞서 일어났다(원문 "Some years ago").

## 동작·원리

### 1. 네 개의 자

```text
  문자열          그래핌  코드포인트  UTF-16(length)  UTF-8 바이트
  abc               3        3            3              3
  한글 (NFC)        2        2            2              6
  한글 (NFD)        2        6            6             18
  é (e + U+0301)    1        2            2              3
  😀                1        1            2              4
  👍🏽 (피부색)       1        2            4              8
  👨‍👩‍👧 (ZWJ 가족)   1        5            8             18
  🇰🇷 (국기)         1        2            4              8
  (Java 21 BreakIterator·정규식 \X 둘 다 같은 그래핌 수, 실험 1)
```

- *그래핌 클러스터(grapheme cluster)*: 사람이 "한 글자"로 보는 단위. Unicode는 기본 규칙으로 *확장 그래핌 클러스터*를 정의한다(UAX #29 §3).
- *코드 포인트*·*UTF-16 코드 유닛*·*UTF-8 바이트*는 [04](../04-character-encoding-unicode/2-summary.md)에서 다뤘다.
- 단위 사이의 관계: 그래핌 ≤ 코드 포인트 ≤ UTF-16 단위 ≤ UTF-8 바이트(ASCII는 셋째·넷째가 같다). 하지만 비율은 글자마다 다르다. 한 단위로 다른 단위를 환산할 수 없다.
- Java 21 `BreakIterator.getCharacterInstance()`의 기본 구현은 확장 그래핌 클러스터 경계를 따른다(Java SE 21 `BreakIterator` 문서). 정규식 `\X`도 확장 그래핌 클러스터다(`Pattern` 문서).
- JS 쪽(`length`, `[...s]`, `Intl.Segmenter`)은 [languages/js/syntax/04-strings-and-utf16](../../../languages/js/syntax/04-strings-and-utf16/2-summary.md)에 자세하다. Node 22.23.2(ICU 78.2)에서도 실험 2와 같은 수가 나왔다.

### 2. 그래핌 경계는 규칙 표(상태 기계)로 정한다

```text
  UAX #29 §3.1.1 규칙 일부 (× = 여기서 끊지 않음, ÷ = 끊음)
  GB3    CR × LF
  GB6~8  한글 자모: L × (L|V|LV|LVT) …          → NFD 한글 ᄒ+ᅡ+ᆫ 이 한 칸
  GB9    × (Extend | ZWJ)                        → e + ́ , 👍 + 🏽 가 한 칸
  GB11   그림문자 Extend* ZWJ × 그림문자          → 👨 ZWJ 👩 ZWJ 👧 가 한 칸
  GB12/13 RI 가 홀수 개 쌓였을 때만 다음 RI 와 붙음 → 🇰🇷🇯🇵 = (🇰🇷)(🇯🇵)
  GB999  나머지는 모두 ÷

  국기 짝짓기 상태 기계 (RI = Regional Indicator 문자)
     ┌────────┐  RI   ┌────────┐
     │ 짝수개  │──────>│ 홀수개  │   홀수개 상태에서 RI 가 오면 × (붙임) 하고 짝수개로
     └────────┘<──────└────────┘   짝수개 상태에서 RI 가 오면 ÷ (새 국기 시작)
                 RI(붙임)
```

- *Regional Indicator(RI)*: U+1F1E6~1F1FF의 알파벳 모양 문자. 두 개가 짝을 지어 국기가 된다. 🇰🇷 = 🇰(U+1F1F0) + 🇷(U+1F1F7).
- *ZWJ(zero width joiner, U+200D)*: 앞뒤 그림문자를 한 모양으로 이어 달라는 보이지 않는 문자.
- 규칙은 Unicode 판마다 바뀐다. UAX #29 rev. 49(Unicode 18.0)는 GB9c를 고쳤다(문서 수정 이력). Java 21의 문자 데이터는 Unicode 15.0이다(`Character` 문서). 그래서 라이브러리마다 최신 이모지의 경계가 다를 수 있다.

### 3. 자르기 — 어느 경계에서 자르나

```text
  "🇰🇷🇯🇵🇺🇸" 에서 "앞 3글자" 미리보기 (실험 3)
  UTF-16 단위 3개   🇰 + D83C(외톨이 서로게이트)   ← 인코딩하면 ? 또는 �
  코드 포인트 3개   🇰🇷 🇯                         ← 국기 하나가 반쪽
  그래핌 3개       🇰🇷 🇯🇵 🇺🇸                    ← 사람이 기대한 결과

  "가나다😀라"(16바이트)를 UTF-8 10바이트 이내로
  바이트 배열을 10에서 자름   가나다 + �              ← 😀의 첫 바이트만 남음
  그래핌 경계에서 자름        가나다 (9바이트)
```

- 코드 포인트 단위 자르기는 서로게이트는 지켜 주지만 그래핌은 깬다. `👨‍👩‍👧 안녕`을 코드 포인트 2개로 자르면 `👨 + ZWJ`가 남는다(실험 3).
- 바이트 한도가 있을 때(메시지 큐 헤더, 푸시 알림 본문, 바이트 단위 컬럼)는 "그래핌 경계 중 바이트 한도를 넘지 않는 마지막 것"에서 자른다. UTF-8에서는 04의 역방향 탐색으로 글자 시작까지 물러날 수 있지만, 그래핌까지 지키려면 경계 목록이 필요하다.

### 4. DB는 무엇을 세나

- PostgreSQL 17: `character varying(n)`은 "n characters (not bytes)"까지 담는다. 넘으면 보통 `ERROR: value too long for type character varying(n)`(8.3절). 예외: 넘는 부분이 모두 공백이면 오류 없이 잘리고, `'…'::varchar(n)`처럼 명시 형변환한 값도 n자로 잘린다(같은 절, SQL 표준 요구).
- MySQL 8.0: `CHAR(30)`은 "30 characters"까지. strict SQL 모드가 아니면 잘라 넣고 경고, strict 모드면 오류다. 단 strict 오류는 공백 아닌 문자가 잘릴 때이고, 넘는 끝 공백은 모드와 상관없이 잘린다(`VARCHAR`는 경고, `CHAR`는 조용히)(13.3.2절). 오류 코드는 1406 `Data too long for column '%s' at row %ld`(오류 참조).
- 두 문서는 "문자"라고만 쓴다. 이것이 코드 포인트라는 것은 이 작업에서 DB를 띄워 확인하지 못했다 [?]. 국기 10개(그래핌 10, 코드 포인트 20)가 `VARCHAR(10)`을 넘는 것은 이 해석에 기댄 예측이다.
- 커리큘럼 칸의 "MySQL 문자 수 vs PG" 대비는 위 문서 기준으로는 둘 다 "문자" 단위다. 실제 어긋남은 **앱(그래핌·UTF-16)과 DB(문자) 사이**, 그리고 바이트로 재는 한도(MySQL 행 크기 65,535바이트, 인덱스 키 바이트 한도, [04](../04-character-encoding-unicode/2-summary.md) 장애 4)에서 생긴다.

### 5. 대소문자 — 로캘에 따라, 길이도 바뀐다

```text
  "TITLE".toLowerCase(tr)    → "tıtle"   I → ı(U+0131, 점 없는 i)
  "title".toUpperCase(tr)    → "TİTLE"   i → İ(U+0130, 점 있는 I)
  "ß".toUpperCase(ROOT)      → "SS"      길이 1 → 2
  "ﬁ".toUpperCase(ROOT)      → "FI"
  "İ".toLowerCase(ROOT)      → "i̇"       U+0069 U+0307, 길이 1 → 2
  (Java 21, 실험 4)
```

- Java `toLowerCase()`·`toUpperCase()`는 **기본 로캘**을 쓴다. 문서가 직접 `"TITLE".toLowerCase()`가 터키어 로캘에서 `"tıtle"`이 된다고 경고하고, 로캘과 무관한 문자열(식별자·프로토콜 키·HTML 태그)에는 `Locale.ROOT`를 쓰라고 한다(Java SE 21 `String` 문서).
  - 흔한 오해: "`toLowerCase()`는 어디서나 같은 결과." 인자 없는 판은 JVM 기본 로캘(`-Duser.language`, OS 설정)에 따라 바뀐다.
- 대소문자 매핑은 1:1이 아니다. 결과 길이가 달라질 수 있다(`String.toLowerCase(Locale)` 문서). 그래서 "변환 뒤 같은 인덱스" 가정은 깨진다.
- *케이스 폴딩(case folding)*: 대소문자 차이를 지운 비교용 형태로 바꾸는 것. 표시용 변환(toUpper/toLower)과 목적이 다르다.
  - Java `equalsIgnoreCase`·`compareToIgnoreCase`는 코드 포인트마다 `Character.toLowerCase(Character.toUpperCase(c))`를 비교한다(문서). 한 글자 단위라 `ß`↔`SS`처럼 길이가 바뀌는 대응은 못 맞춘다. 실험에서 `"STRASSE".equalsIgnoreCase("straße")`는 false였다.
  - 로캘을 보지 않으므로 `"TITLE".equalsIgnoreCase("tıtle")`이 true다(ı의 대문자가 I).
- JS도 `toLowerCase()`는 로캘 무관, `toLocaleLowerCase('tr')`는 터키어 규칙이다(Node 22 실험: `tıtle` / `title`).

### 6. 식별자 정규화 — 같은 함수를 두 번 써도 같아야 한다

```text
  Spotify 사고 (Goldmann, Spotify Labs 2013년 글 — bigbird는 원문의 예시 이름)
  가입:        canon("ᴮᴵᴳᴮᴵᴿᴰ") = "BIGBIRD"  → 기존 "bigbird"와 안 겹침 → 가입 허용
  재설정 요청:  canon("ᴮᴵᴳᴮᴵᴿᴰ") = "BIGBIRD"  → 새 계정 메일로 링크 발송
  링크 사용:   canon("BIGBIRD")  = "bigbird"  → bigbird 계정의 비밀번호가 바뀜
  원인: canon(canon(x)) ≠ canon(x)
```

- *멱등(idempotent)*: 두 번 적용해도 한 번 적용한 것과 같은 성질. `f(f(x)) = f(x)`.
- Spotify는 XMPP nodeprep(Twisted 구현)을 정규화 함수로 썼다. 이 함수는 Unicode 3.2 입력만 전제했는데, 입력 검사를 하지 않았고 Python 2.5의 `unicodedata` 변경 뒤 3.2 밖 문자(`ᴮ` 등)에서 멱등이 아니게 됐다(원문).
- 같은 함정을 Java로 재현했다(실험 5, Unicode 15.0 데이터).

```text
  입력 "ᴮᴵᴳᴮᴵᴿᴰ" (U+1D2E … 수식용 대문자)
  NFKC(lower(x))  → "BIGBIRD", 한 번 더 → "bigbird"     ← 순서가 틀리면 멱등이 아님
  lower(NFKC(x))  → "bigbird", 한 번 더 → "bigbird"
  전 코드 포인트 검사: NFKC(lower(x)) 멱등 아님 629개(예 U+03D2 ϒ→Υ→υ) / lower(NFKC(x)) 0개
```

- `ᴮ`는 소문자 짝이 없어 `lower`가 그대로 둔다. NFKC가 이것을 `B`로 바꾸므로, 소문자화를 **먼저** 하면 결과에 대문자가 남는다.
- Spotify의 즉시 대처는 "`X == canonical_username(X)`인 이름만 가입 허용", 최종 대처는 "두 번 적용한 결과가 다르면 거부"였다(원문). 고정점만 받는 검사다.
- 이 실험의 0개는 Unicode 15.0·Java 21 기준이다. 판이 바뀌면 다시 돌려야 한다 — Spotify 사고가 바로 라이브러리 판 변경에서 생겼다.

### 7. 혼동 문자 — 정규화로는 다 합쳐지지 않는다

```text
  "paypal"  p a y p a l          U+0061 (라틴 a)
  "pаypаl"  p а y p а l          U+0430 (키릴 а)
  equals false · NFKC 뒤에도 false · lower 뒤에도 false   (실험 6)
  스크립트 집합: {LATIN} vs {LATIN, CYRILLIC} ← 혼합
```

- *혼동 문자(confusable)*: 모양이 같거나 비슷한데 코드 포인트가 다른 문자.
  - 정규화와의 관계: 옴 기호 `Ω`(U+2126)처럼 정준 동등인 일부는 NFC에서 그리스 `Ω`(U+03A9)로 합쳐진다(UAX #15, Python `unicodedata` 15.0 확인). 라틴 `a`와 키릴 `а`처럼 다른 스크립트의 글자는 합쳐지지 않는다.
- UTS #39는 두 가지 도구를 정의한다.
  - *skeleton*: 혼동 문자를 대표 문자로 바꾼 형태. `skeleton(X) = skeleton(Y)`면 혼동 가능으로 본다(§4).
  - *혼합 스크립트 검사*·*제한 수준*: 문자열이 어떤 스크립트로 이뤄졌는지 본다(§5.1·§5.2). "Highly Restrictive"는 라틴+한자+한글(Latn + Kore) 같은 조합을 허용하고, "Moderately Restrictive"도 라틴 + 키릴·그리스 조합은 허용하지 않는다.
- 실험의 단순 검사는 `한글abc`도 "혼합"으로 잡았다. 실제 정책은 UTS #39 §5.2처럼 허용 조합을 정해야 한다. Java 표준 라이브러리에는 skeleton 함수가 없다(ICU4J의 `SpoofChecker`가 이 일을 한다고 알려져 있으나 여기서 쓰지 않았다 [?]).

### 실험: 네 개의 자, 자르기, 터키어 로캘, 멱등성, 혼동 문자

환경: i7-13700HX, Linux 7.0.0-34, Docker `eclipse-temurin:21-jdk`(OpenJDK 21.0.12, Unicode 15.0) `--cpus=2 --network none`, 같은 코드를 `-Duser.language=en -Duser.country=US`와 `tr TR`로 두 번 실행. JS는 `node:22-bookworm-slim`(Node 22.23.2, ICU 78.2, Unicode 17.0). 2026-10-07. 결정적 실험이다.

```java
// Len05.java 핵심
BreakIterator bi = BreakIterator.getCharacterInstance(Locale.ROOT);   // 그래핌 경계
bi.setText(s); int n = 0; while (bi.next() != BreakIterator.DONE) n++;
s.offsetByCodePoints(0, k);                                           // 코드 포인트 k개 위치
UnaryOperator<String> bad  = x -> nfkc(lower(x));                     // 순서가 틀린 정규화
UnaryOperator<String> good = x -> lower(nfkc(x));
for (int c = 0; c <= 0x10FFFF; c++) { /* 서로게이트 제외, f(f(c)) != f(c) 세기 */ }
Level.valueOf(in.toUpperCase());                                      // 기본 로캘 대문자화
```

```text
== 2. "10자 제한" — 같은 입력을 세 기준으로 ==
  가나다라마바사아자차   그래핌 10 | UTF-16 10 | 코드포인트 10 | UTF-8 30바이트 → length<=10:true  코드포인트<=10:true  그래핌<=10:true
  😀×6                  그래핌  6 | UTF-16 12 | 코드포인트  6 | UTF-8 24바이트 → length<=10:false 코드포인트<=10:true  그래핌<=10:true
  🇰🇷×10                그래핌 10 | UTF-16 40 | 코드포인트 20 | UTF-8 80바이트 → length<=10:false 코드포인트<=10:false 그래핌<=10:true
  👨‍👩‍👧×2               그래핌  2 | UTF-16 16 | 코드포인트 10 | UTF-8 36바이트 → length<=10:false 코드포인트<=10:true  그래핌<=10:true
== 4. (기본 로캘 tr_TR로 실행) ==
  "TITLE".toLowerCase()     = "tıtle"   (기본 로캘 tr_TR)
  "TITLE".toLowerCase(ROOT) = "title"
  Level.valueOf("info".toUpperCase()) → java.lang.IllegalArgumentException: No enum constant Len05.Level.İNFO
  Level.valueOf("title".toUpperCase()) → java.lang.IllegalArgumentException: No enum constant Len05.Level.TİTLE
  (en_US로 실행하면 각각 "title", INFO, TITLE)
== JS (Node 22.23.2) ==
  slice(0,3) = "🇰\ud83c" → TextEncoder f09f87b0efbfbd      ← 외톨이 서로게이트가 EF BF BD 로
  'TITLE'.toLocaleLowerCase('tr') = tıtle | 'TITLE'.toLowerCase() = title
```

관찰과 해석
- 2: "10자"의 판정이 단위마다 다르다. 그래핌 10개인 국기 문자열은 사람 기준으로 통과하지만 코드 포인트 기준으로는 20이다. 반대로 `😀×6`은 사람 기준 6자인데 `length` 검사(12)에서 막힌다.
- 4: 같은 바이트코드가 JVM 기본 로캘만 바꿨을 때 `enum` 조회에서 예외를 냈다. 코드에 로캘이 안 보이는 버그다.
- 5: 정규화 함수의 **순서**가 멱등성을 정했다. 정규화 단계 각각(NFKC, lower)은 멱등이었다(0개). 합성 순서가 틀리면 629개 코드 포인트에서 깨졌다.

## 쓰이는 자료구조·알고리즘

- **그래핌 경계 상태 기계**: UAX #29 규칙은 "직전까지 본 문자 종류" 상태와 다음 문자 속성으로 끊을지 정한다. 국기 짝(RI 홀짝), 이모지 ZWJ 연쇄가 상태다. 상태 기계의 하드웨어 판은 [08-sequential-logic-clock](../08-sequential-logic-clock/2-summary.md), 문자열 오토마톤은 [algorithm/25-string-matching](../../algorithm/25-string-matching/2-summary.md).
- **가변 길이 역방향 탐색**: UTF-8에서 `10xxxxxx`를 건너 글자 시작으로 물러난다([04](../04-character-encoding-unicode/2-summary.md) 실험 7). UTF-16에서는 하위 서로게이트면 한 칸 더 물러난다(`Character.isLowSurrogate`). 바이트 예산 자르기의 바탕이다.
- **고정점·멱등 검사**: `canon(x) == x`만 받으면 저장된 키가 모두 고정점이 되어, 어느 경로에서 정규화를 몇 번 하든 같은 키가 나온다. 불변식으로 보는 법은 [math/02-induction-and-invariants](../../math/02-induction-and-invariants/2-summary.md).
- **정규화 키 + 해시·트라이**: 사용자명 유일성은 "정규화한 키"의 해시 인덱스·UNIQUE 제약이다 — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) 장애 2, DB 쪽은 [database/10](../../database/10-collation-and-text-comparison/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 필드마다 "무엇을 셀지"를 먼저 정한다

| 제한의 목적 | 셀 단위 | Java 21 |
|---|---|---|
| 화면에 보이는 글자 수(닉네임 "10자") | 그래핌 | `BreakIterator.getCharacterInstance()` |
| DB `VARCHAR(n)` 길이 한도 | DB가 세는 "문자"(코드 포인트로 추정 [?]) | `s.codePointCount(0, s.length())` |
| 바이트 한도(헤더, 푸시, 인덱스 키) | UTF-8 바이트 | `s.getBytes(UTF_8).length` |
| 다른 Java·JS 코드와의 인덱스 호환 | UTF-16 단위 | `s.length()` |

- 코드 포인트 수는 길이 검사일 뿐, 저장 가능 여부 전체가 아니다. 예: PostgreSQL 문자형은 NUL(U+0000)을 담지 못한다(8.3절).
- 사용자에게 "10자"라고 보여 주면 그래핌으로 세고, DB 컬럼은 그래핌 10개가 들어갈 만큼(코드 포인트·바이트 여유) 크게 잡는다. 아니면 두 검사를 함께 하고 오류 문구를 나눈다.

```java
static int graphemes(String s) {
    BreakIterator bi = BreakIterator.getCharacterInstance(Locale.ROOT);
    bi.setText(s);
    int n = 0;
    while (bi.next() != BreakIterator.DONE) n++;
    return n;
}
static String cutGraphemes(String s, int max) {          // 미리보기 자르기
    BreakIterator bi = BreakIterator.getCharacterInstance(Locale.ROOT);
    bi.setText(s);
    int end = 0;
    for (int i = 0; i < max; i++) { int e = bi.next(); if (e == BreakIterator.DONE) break; end = e; }
    return s.substring(0, end);
}
```

### 2. 로캘과 무관한 문자열은 `Locale.ROOT`

- 설정 키, HTTP 헤더 이름, enum 이름, 파일 확장자, SQL 키워드 비교는 `toLowerCase(Locale.ROOT)`·`toUpperCase(Locale.ROOT)`로 한다.
- 정적 분석으로 인자 없는 `toLowerCase()`·`toUpperCase()`·`String.format`을 찾는다. 테스트를 `-Duser.language=tr -Duser.country=TR`로 한 번 돌리면 숨은 곳이 드러난다(실험 4).

### 3. 사용자명 정규화 파이프라인

```text
  입력 → NFKC → toLowerCase(ROOT) → 허용 문자·스크립트 검사(UTS #39 §5.2) → 고정점 검사 canon(x)==x → 저장 키
                                                                              (표시용 원문은 따로 저장)
```

```java
static String canon(String s) {
    return Normalizer.normalize(s, Normalizer.Form.NFKC).toLowerCase(Locale.ROOT);
}
static boolean acceptable(String raw) {
    String c = canon(raw);
    return c.equals(canon(c));       // Spotify 대처: 두 번 적용해 다르면 거부
}
```

- 정규화 함수는 한 곳에만 둔다. 가입·로그인·재설정·관리 도구가 같은 함수를 부른다.
- 라이브러리(JDK·ICU) 판을 올릴 때 저장된 키를 새 함수로 다시 계산해 바뀌는 행이 있는지 본다.

## 장애 시나리오와 대처

### 1. "10자 제한" 검증과 DB `VARCHAR(10)`이 다르게 센다 (⚠ 커리큘럼)

- **현상**: 프론트·서버 검증을 통과한 닉네임이 저장 단계에서 실패한다. 또는 정상 입력이 "너무 길다"며 막힌다.
- **보이는 형태**
  - PostgreSQL: `ERROR: value too long for type character varying(10)`(문서 8.3의 예와 같은 문구). JDBC에서는 `PSQLException`, Spring이면 `DataIntegrityViolationException` 계열로 번역된다 [?].
  - MySQL strict 모드: `ERROR 1406 (22001): Data too long for column 'nickname' at row 1`. 비strict 모드면 오류 없이 **잘려서** 저장되고 경고만 남는다(매뉴얼 13.3.2).
- **원인**: 검증은 그래핌(또는 JS `length`)으로, DB는 "문자"로 센다. 국기 10개는 그래핌 10, 코드 포인트 20, `length` 40이다(실험 2).
- **대처**: 적용 1의 표처럼 목적별 단위를 정하고, DB 한도는 그래핌 한도보다 넉넉하게 둔다. MySQL은 strict 모드를 켜서 조용한 절단을 막는다.

### 2. 이모지·국기를 중간에서 잘라 깨진 미리보기 (⚠ 커리큘럼)

- **현상**: 알림 미리보기 끝에 🇰 하나, `?`, `�`가 보인다. 가족 이모지가 사람 한 명으로 바뀐다.
- **보이는 형태**: `substring`이 외톨이 서로게이트로 끝난다(`D83C`). 인코딩 뒤 Java는 `3F`, JS는 `EF BF BD`(실험 3·JS).
- **원인**: UTF-16 단위나 코드 포인트 단위로 잘랐다. 국기·ZWJ 연쇄·피부색은 코드 포인트 여러 개가 한 그래핌이다.
- **대처**: 미리보기 자르기를 그래핌 경계 함수 하나로 모은다(`cutGraphemes`). 바이트 한도가 있으면 그래핌 경계 중 한도 안의 마지막에서 자른다.

### 3. 터키어 로캘에서 `toLowerCase()` 비교 실패 (⚠ 커리큘럼)

- **현상**: 특정 지역 서버나 사용자 PC에서만 설정이 안 먹고, enum 파싱이 예외를 낸다.
- **보이는 형태**: `"TITLE".toLowerCase()` → `tıtle`. `Level.valueOf("info".toUpperCase())` → `IllegalArgumentException: No enum constant …İNFO`(실험 4).
- **원인**: 인자 없는 대소문자 변환이 JVM 기본 로캘을 쓴다. 터키어 규칙에서 I/i의 짝이 다르다(`String` 문서 표).
- **대처**: 로캘과 무관한 문자열에는 `Locale.ROOT`. 대소문자 무시 비교가 목적이면 양쪽에 같은 `toLowerCase(Locale.ROOT)`를 적용하거나 `equalsIgnoreCase`(로캘 무관)를 쓴다. 터키어 로캘로 테스트를 한 번 돌린다.

### 4. 멱등이 아닌 사용자명 정규화 → 계정 탈취(Spotify, 2013년 공개) (⚠ 커리큘럼)

- **현상**: 공격자가 만든 계정으로 비밀번호 재설정을 요청했는데, 다른 사람 계정의 비밀번호가 바뀐다.
- **보이는 형태**: 오류는 없다. 원문에서는 포럼 관리자 계정에 몇 분 만에 새 플레이리스트와 새 비밀번호가 생겼고, 탈취 관련 로그 줄을 보고서야 정규 사용자명 도출에 문제가 있다고 짐작했다. 함수를 직접 두 번 호출해 보니 결과가 `BIGBIRD` → `bigbird`로 달랐다(원문).
- **원인**: 정규화 함수가 멱등이 아니었다. 경로마다 정규화를 적용한 횟수가 달라 같은 입력이 다른 키가 됐다. 원문에 따르면 nodeprep이 Unicode 3.2 밖 입력을 검사하지 않았고, Python 2.5 `unicodedata` 변경이 동작을 바꿨다. Twisted 11.0.0에서 고쳐졌다.
- **대처**
  - 정규화 순서를 고정점이 되게 짠다(실험 5: `lower(NFKC(x))`는 0개, 반대 순서는 629개).
  - 가입 시 `canon(x) == canon(canon(x))`를 검사해 고정점만 받는다.
  - 저장 키와 비교 키를 같은 함수로 만든다. 라이브러리 업그레이드 때 키를 재계산해 비교한다.

### 5. 혼동 문자로 만든 사칭 계정

- **현상**: `paypal`과 똑같아 보이는 `pаypаl` 계정이 가입되어 사용자를 속인다.
- **보이는 형태**: 두 이름이 NFKC·소문자화 뒤에도 다르다(실험 6). UNIQUE 제약은 통과한다.
- **원인**: 정규화는 "같은 글자의 다른 표현"만 합친다. 다른 스크립트의 닮은 글자는 합치지 않는다.
- **대처**: UTS #39 혼합 스크립트·제한 수준 검사로 라틴 + 키릴 같은 조합을 거부하고, skeleton으로 기존 이름과 혼동되는지 검사한다(ICU 등 구현 사용). 식별자 열거·사칭 일반은 [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md).

## 핵심 문장

- 길이는 넷이다. 그래핌(사람), 코드 포인트(DB "문자"로 추정), UTF-16 단위(Java·JS `length`), UTF-8 바이트(저장·전송 한도). 검증·저장·자르기는 같은 단위끼리 맞춘다.
- 그래핌 경계는 UAX #29 규칙 표(상태 기계)로 정하고, Java는 `BreakIterator`·`\X`로 쓴다. 국기·ZWJ 이모지·결합 문자는 코드 포인트 여러 개가 한 칸이다.
- 자르기는 그래핌 경계에서, 바이트 한도가 있으면 그 안의 마지막 그래핌 경계에서 한다.
- 인자 없는 `toLowerCase()`는 기본 로캘을 쓴다. 로캘 무관 문자열에는 `Locale.ROOT`.
- 식별자 정규화는 멱등이어야 한다. `canon(canon(x)) == canon(x)`를 검사하고, 순서(NFKC 다음 소문자화)를 지킨다.
- 정규화만으로는 혼동 문자를 다 합치지 못한다(옴 기호 같은 일부만 합쳐진다). 사칭 방지는 UTS #39의 스크립트 검사·skeleton이 맡는다.

## 관련 주제·근거

- 선행: [04-character-encoding-unicode](../04-character-encoding-unicode/2-summary.md)
- 원고: 없음(신규). 문자열 기초는 [foundations/data-representation](../../foundations/data-representation/README.md) §3.
- 연결
  - [languages/js/syntax/04-strings-and-utf16](../../../languages/js/syntax/04-strings-and-utf16/2-summary.md) — JS `length`·`Intl.Segmenter`·`isWellFormed`
  - [web-platform/12-internationalization-and-localization](../../web-platform/12-internationalization-and-localization/2-summary.md) — 브라우저 실험 9(길이 vs 그래핌)
  - [database/10-collation-and-text-comparison](../../database/10-collation-and-text-comparison/2-summary.md) — 대소문자 무시 비교, ci collation, `lower()` 인덱스
  - [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md) — 식별자 설계
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md) — 정규화 없이 넣은 키
  - 다음(이 영역): [06-byte-order-and-alignment](../06-byte-order-and-alignment/2-summary.md)
- 근거
  - UAX #29 "Unicode Text Segmentation"(Unicode 18.0.0, rev. 49, 2026-09-01) — §3 확장 그래핌 클러스터, §3.1.1 규칙 GB1~GB999 <https://www.unicode.org/reports/tr29/>
  - UTS #39 "Unicode Security Mechanisms"(18.0.0, rev. 34) — §4 skeleton·혼동 검출, §5.1 혼합 스크립트, §5.2 제한 수준 <https://www.unicode.org/reports/tr39/>
  - UAX #15(정규화·멱등성) <https://www.unicode.org/reports/tr15/>
  - M. Goldmann, "Creative usernames and Spotify account hijacking", Spotify Labs, 2013-06-18 (Internet Archive 사본 <https://web.archive.org/web/2014/http://labs.spotify.com/2013/06/18/creative-usernames/>)
  - Java SE 21 API — `String`(`toLowerCase()`의 터키어 예와 `Locale.ROOT` 권고, 매핑 길이 변화, `equalsIgnoreCase`·`compareToIgnoreCase` 정의), `BreakIterator`(확장 그래핌 클러스터), `Pattern`(`\X`, `\b{g}`), `Character`(Unicode 15.0) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html>
  - PostgreSQL 17 문서 8.3 Character Types("n characters (not bytes)", `value too long`) <https://www.postgresql.org/docs/17/datatype-character.html>
  - MySQL 8.0 Reference Manual 13.3.2 The CHAR and VARCHAR Types(문자 단위 길이, strict 모드와 절단) <https://dev.mysql.com/doc/refman/8.0/en/char.html> (Internet Archive 사본으로 열람) · Error Reference 1406 ER_DATA_TOO_LONG
- 실험 목록
  - `Len05.java` — 1. 여덟 문자열의 바이트·UTF-16·코드 포인트·그래핌(BreakIterator·`\X`), 2. "10자" 세 기준 판정, 3. UTF-16/코드 포인트/그래핌/바이트 예산 자르기, 4. 터키어 로캘 대소문자·enum `valueOf`·`ß`·`ﬁ`·`İ`·`equalsIgnoreCase`, 5. Spotify 입력과 전 코드 포인트 멱등성 검사, 6. 혼동 문자와 스크립트 집합. OpenJDK 21.0.12, Docker `--cpus=2 --network none`, 기본 로캘 en_US·tr_TR 두 번.
  - `len05.js` — 같은 입력의 `length`·코드 포인트·`Intl.Segmenter`·UTF-8, `slice` 절단의 `TextEncoder` 결과, `toLocaleLowerCase('tr')`. Node 22.23.2(ICU 78.2).
  - 호스트 Python 3 `unicodedata`(Unicode 15.0) — `normalize("NFC", "\u2126") == "\u03a9"`가 True(옴 기호가 정규화로 합쳐지는 예).
  - DB(PostgreSQL·MySQL)는 띄우지 않았다. DB 동작은 문서 근거다.
  - 파일 위치: scratchpad `arch/05/`(Len05.java, len05.js, out-len05*.txt).
