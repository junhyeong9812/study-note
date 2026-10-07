# web-platform/12-internationalization-and-localization — 로캘 협상·메시지 카탈로그·복수형·서식·RTL·이름 가정 — 정리 (힌트)

## 해결하는 문제

한국어 화면만 생각하고 만든 코드는 다른 언어·지역에서 조용히 틀린다.

```text
  같은 데이터, 다른 사용자

  금액 1234567.891     en-US  1,234,567.891      de-DE  1.234.567,891     hi-IN  12,34,567.891
  "장바구니 1개"        en     "1 item" / "2 items"   ru  1·21 / 2~4 / 5~20 이 서로 다른 꼴
  2026-03-01T15:30Z    뉴욕   Mar 1, 2026, 10:30 AM    서울  2026. 3. 2. 오전 12:30   ← 날짜가 바뀐다
  레이아웃              ltr   [아이콘][글자 →]           ar   [← 글자][아이콘]
```

- 금액·날짜 줄은 아래 실험(Chrome 151)의 실제 출력이다. 장바구니 줄의 번역 문자열("1 item" 등)은 예시이고, ru의 꼴 구분은 실험 5의 복수형 범주에서 왔다. 레이아웃 줄은 그림이다(실측은 실험 11).
- 두 단계로 나눠 부른다.
  - *국제화(i18n, internationalization)*: 코드가 특정 언어·지역을 가정하지 않게 만드는 일. 문자열 분리, 서식 API 사용, 방향 독립 CSS.
  - *지역화(l10n, localization)*: 특정 로캘에 맞춘 번역·서식 데이터를 채우는 일.
  - *로캘(locale)*: 언어 + 지역 + 선호(달력·숫자 체계 등)의 묶음. `ko-KR`, `de-CH`, `ja-JP-u-ca-japanese`처럼 BCP 47 태그로 쓴다.

쉬운 예: 해외여행에서 쓰는 전원 어댑터다. 기기(코드)는 그대로인데 콘센트 모양(로캘)마다 끼우는 부분만 바꾼다.

똑같은 구조다.\
코드에는 "어댑터 자리"(메시지 키·서식 API 호출)만 두고, 나라마다 다른 부분은 데이터(번역 카탈로그·CLDR 로캘 데이터)로 뺀다.

실무 예:
- `"총 " + n + "개 상품"`을 그대로 번역 파일에 넣었더니, 어순이 다른 언어에서 문장이 깨진다.
- 독일 사용자가 입력한 `1.234,5`를 서버가 `parseFloat`로 읽어 `1.234`가 된다(아래 실험).
- 성·이름 두 칸을 모두 필수로 받아, 이름이 한 단어뿐인 사용자가 가입하지 못한다.

## 동작·원리

### 1. 로캘 협상 — 누가 어떤 언어를 고르나

```text
  브라우저 설정 언어 목록
     │  navigator.languages = ["de-CH", ...]
     ▼
  요청 헤더  Accept-Language: de-CH            (RFC 9110 예: da, en-gb;q=0.8, en;q=0.7)
     │
     ▼
  서버: 지원 목록 [en, de, fr]과 매칭 (RFC 4647)
     │  lookup: de-CH → 없음 → de → 있음 ✓
     ▼
  응답  Content-Language: de   +   Vary: Accept-Language  (캐시가 언어별로 따로 저장하게)
     │
     ▼
  클라이언트 Intl API: 요청 로캘이 지원 밖이면 기본 로캘로 폴백
```

- *BCP 47(RFC 5646)*: 언어 태그 문법. `언어[-문자][-지역][-변이][-u-확장]`. 예: `zh-Hant-TW`(중국어·번체·대만), `ja-JP-u-ca-japanese`(일본 연호 달력).
- *RFC 4647 lookup*: 태그를 뒤에서부터 한 칸씩 잘라 가며(`zh-Hant-TW` → `zh-Hant` → `zh`) 지원 목록에서 처음 맞는 것을 고른다.
- RFC 9110 §12.5.4는 Accept-Language에 대해 이렇게 적는다.
  - `da, en-gb;q=0.8, en;q=0.7` = "덴마크어를 선호하지만 영국 영어와 다른 영어도 받겠다". 여러 언어를 q값으로 나열한다.
  - 나열 순서를 우선순위로 읽는 수신자도 있지만, 그 동작에 기댈 수는 없다(q값을 본다).
  - 사용자의 언어 선호 전체를 매 요청 보내는 것은 프라이버시 기대에 어긋날 수 있다(§17.13 — 핑거프린팅).
  - 매칭 방식은 RFC 4647 §3의 여러 방식 중 구현이 고른다. 어떤 표현을 보낼지 서버가 고르는 것은 사전 협상(§12.1)의 구조다.
- 실무에서는 헤더를 첫 추정으로만 쓰고, 사용자가 고른 언어(계정 설정·URL 경로 `/de/`·쿠키)를 우선한다(해석).

### 2. 메시지 카탈로그 — 문장 단위로 번역한다

```text
  나쁨: 조각을 이어 붙임                       좋음: 문장 전체가 하나의 메시지
  "총 " + n + "개 상품"                       cart.summary = "{count, plural, one {# item} other {# items}} in total"
     → 번역가는 "총", "개 상품"을                cart.summary(ko) = "총 {count}개 상품"
       따로 받아 어순·조사를 못 맞춘다            → 언어마다 어순·복수형을 메시지 안에서 정한다
```

- *메시지 카탈로그*: 키 → 로캘별 문장의 표. 코드에는 키와 인자만 남는다.
- *ICU MessageFormat*: 인자 자리 `{name}`와 선택 구문(`plural`·`select`)을 가진 메시지 문법. ICU(ICU4J·ICU4C)와 여러 JS 라이브러리가 구현한다.
- *MessageFormat 2(MF2)*: Unicode가 만든 다음 세대 문법. CLDR 47(2025-03-13)에서 Stable이 됐다. 복수형 예시(messageformat.unicode.org):

```text
.input {$count :number}
.match $count
0   {{No items.}}
one {{1 item.}}
*   {{{$count} items.}}
```

### 3. 복수형 규칙 — 언어마다 범주 수가 다르다

```text
  CLDR 범주:  zero · one · two · few · many · other   (언어마다 일부만 쓴다)

  ko  : other                                    → "{n}개" 하나로 충분
  en  : one, other                                → 1 item / 2 items
  ru  : one, few, many, other                     → 1, 21 / 2~4, 22 / 0, 5~20 / 1.5
  ar  : zero, one, two, few, many, other          → 여섯 꼴
```

- 러시아어 규칙(CLDR language plural rules, cardinal)
  - one: `v = 0 and i % 10 = 1 and i % 100 != 11`
  - few: `v = 0 and i % 10 = 2..4 and i % 100 != 12..14`
  - many: `v = 0 and i % 10 = 0 or v = 0 and i % 10 = 5..9 or v = 0 and i % 100 = 11..14`
  - *n·i·v*: n은 수 자체, i는 정수부, v는 보이는 소수 자릿수. `1.5`는 v=1이라 위 셋에 안 걸려 `other`다.
- "1 items" 버그는 `n === 1 ? 'item' : 'items'`처럼 영어 규칙을 코드에 박은 결과다. 이 코드는 프랑스어(0·1.5가 one)·러시아어(21이 one)에서 틀린다.

### 4. 숫자·통화·날짜 서식은 데이터다

- 소수점·자릿수 구분자·묶음 단위·숫자 문자·통화 소수 자릿수·날짜 순서는 로캘 데이터(CLDR)에 있다. 브라우저 `Intl` API(ECMA-402)가 이 데이터로 서식을 만든다.
- 통화 소수 자릿수는 통화마다 다르다. 실험에서 KRW·JPY는 0자리, USD·EUR는 2자리, BHD(바레인 디나르)는 3자리였다.
- 날짜는 **순간(instant)** 과 **표시(로캘 + 시간대)** 를 나눈다. 저장·전송은 UTC 순간, 표시는 사용자 시간대로.

### 5. 방향(RTL)과 문자열 길이

```text
  dir=ltr                                   dir=rtl
  |◀40▶[box]                       |       |                       [box]|     margin-left:40px
  |◀40▶[box]                       |       |                [box]◀40▶|     margin-inline-start:40px
         ↑ 물리 속성은 방향이 바뀌어도 왼쪽 그대로        ↑ 논리 속성은 "시작 쪽"을 따라 뒤집힌다
```

- *논리 속성(CSS Logical Properties)*: `margin-inline-start`, `padding-inline-end`, `inset-inline-start`처럼 "왼쪽·오른쪽" 대신 "시작·끝"으로 쓰는 속성. `dir`에 따라 실제 방향이 정해진다.
- 번역문은 길이가 다르다. 같은 "변경 사항 저장"이 독일어 "Änderungen speichern"이 되면 고정 폭 버튼을 넘친다(실험).
- 문자열 `length`는 UTF-16 코드 단위 수다. 사용자가 보는 "글자"(grapheme)와 다르다(실험 9). [architecture/04-character-encoding-unicode](../../architecture/04-character-encoding-unicode/2-summary.md)

### 실험: Intl 출력·로캘 협상·레이아웃을 실제로 잰다

환경: headless Chrome 151.0.7922.173, playwright-core 1.62.1(Node 20.19), 컨텍스트 `locale: 'en-US'`, `timezoneId: 'UTC'`(1번만 locale을 바꿈), 로컬 서버 127.0.0.1(요청의 `Accept-Language`를 그대로 돌려줌), 2026-10-04. 시간 측정이 없는 결정적 실험이다.

```js
// 핵심 코드(브라우저 안에서 실행)
new Intl.NumberFormat(loc).format(1234567.891);
new Intl.NumberFormat(loc, { style: 'currency', currency: cur }).format(1234.5);
new Intl.PluralRules(loc).select(n);                       // 'one' | 'few' | 'many' | ...
new Intl.DateTimeFormat(loc, { dateStyle: 'medium', timeStyle: 'short', timeZone: tz })
  .format(new Date(Date.UTC(2026, 2, 1, 15, 30)));
new Intl.NumberFormat('xx-YY').resolvedOptions().locale;   // 폴백 결과
[...new Intl.Segmenter('ko', { granularity: 'grapheme' }).segment(s)].length;
// 레이아웃: <button style="width:120px;white-space:nowrap;overflow:hidden"> 의 scrollWidth vs clientWidth
// RTL: dir=ltr/rtl 부모(400px) 안 자식(100px)에 margin-left vs margin-inline-start 40px
```

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04)

```text
== 1. 로캘 협상: 컨텍스트 locale -> Accept-Language / navigator ==
ko-KR | Accept-Language: "ko-KR" | navigator.languages: ["ko-KR"] | Intl 기본: ko-KR
de-CH | Accept-Language: "de-CH" | navigator.languages: ["de-CH"] | Intl 기본: de-CH
ar-EG | Accept-Language: "ar-EG" | navigator.languages: ["ar-EG"] | Intl 기본: ar-EG
== 2. 숫자 ==
en-US  1,234,567.891
de-DE  1.234.567,891
fr-FR  1 234 567,891
de-CH  1'234'567.891
ko-KR  1,234,567.891
hi-IN  12,34,567.891
ar-EG  ١٬٢٣٤٬٥٦٧٫٨٩١
== 3. 통화(같은 숫자 1234.5) ==
en-US USD $1,234.50  maxFrac=2
de-DE EUR 1.234,50 €  maxFrac=2
ko-KR KRW ₩1,235  maxFrac=0
ja-JP JPY ￥1,235  maxFrac=0
ar-BH BHD ‏١٬٢٣٤٫٥٠٠ د.ب.‏  maxFrac=3
== 4. 파싱 함정 ==
parseFloat("1.234,5") = 1.234   Number("1.234,5") = NaN   parseFloat("1,234.5") = 1
== 5. 복수형 범주 (cardinal) ==
n           0     1     2     3     5    11    21    22   101   1.5
en      other   one other other other other other other other other   categories=one,other
ko      other other other other other other other other other other   categories=other
fr        one   one other other other other other other other   one   categories=one,many,other
ru       many   one   few   few  many  many   one   few   one other   categories=one,few,many,other
pl       many   one   few   few  many  many  many   few  many other   categories=one,few,many,other
ar       zero   one   two   few   few  many  many  many other other   categories=zero,one,two,few,many,other
en ordinal: 1:one 2:two 3:few 4:other 11:other 12:other 13:other 21:one 22:two 23:few 101:one
== 6. 날짜: 같은 순간(2026-03-01T15:30:00Z) ==
en-US America/New_York: Mar 1, 2026, 10:30 AM
en-GB Europe/London: 1 Mar 2026, 15:30
de-DE Europe/Berlin: 01.03.2026, 16:30
ko-KR Asia/Seoul: 2026. 3. 2. 오전 12:30
ja-JP-u-ca-japanese Asia/Tokyo: 令和8年3月2日 0:30
ar-SA Asia/Riyadh: ٠١‏/٠٣‏/٢٠٢٦، ٦:٣٠ م
toLocaleDateString 기본(en-US 컨텍스트, UTC): 3/1/2026
== 7. 폴백 ==
de-AT -> de-AT
zh-Hant-TW -> zh-Hant-TW
pt-MZ -> pt-MZ
xx-YY -> en-US
tlh -> en-US
supportedLocalesOf(["tlh","de-AT","xx"]) = ["de-AT"]
"en_US" -> RangeError: Invalid language tag: en_US
== 8. 목록·상대 시간 ==
en: A, B, and C | yesterday
de: A, B und C | gestern
ko: A, B 및 C | 어제
== 9. 길이 vs 글자 ==
"한글" length=2 graphemes=2 NFC.length=2
"한글" length=6 graphemes=2 NFC.length=2
"👍🏽" length=4 graphemes=1 NFC.length=4
"👨‍👩‍👧" length=8 graphemes=1 NFC.length=8
"é" length=1 graphemes=1 NFC.length=1
"é" length=2 graphemes=1 NFC.length=1
== 10. 레이아웃: 고정 폭 버튼 120px, 같은 뜻의 문자열 ==
en "Save changes" scrollWidth=116 clientWidth=116 잘림=false
de "Änderungen speichern" scrollWidth=149 clientWidth=116 잘림=true
fi "Tallenna muutokset" scrollWidth=129 clientWidth=116 잘림=true
ko "변경 사항 저장" scrollWidth=116 clientWidth=116 잘림=false
ja "変更を保存" scrollWidth=116 clientWidth=116 잘림=false
== 11. RTL: margin-left vs margin-inline-start (부모 400px, 자식 100px, 여백 40px) ==
l=dir ltr, r=dir rtl; 1=margin-left, 2=margin-inline-start
l1 왼쪽 간격=40 오른쪽 간격=260
l2 왼쪽 간격=40 오른쪽 간격=260
r1 왼쪽 간격=300 오른쪽 간격=0
r2 왼쪽 간격=260 오른쪽 간격=40
```

관찰과 해석
- 1: Playwright의 `locale` 옵션이 요청의 `Accept-Language`, `navigator.languages`, `Intl` 기본 로캘을 함께 바꿨다. 실제 브라우저는 사용자의 언어 설정 목록을 q값과 함께 보낸다. 여기서는 단일 값만 확인했다.
- 2: 같은 수가 구분자(`,` `.` 공백 `'`)·묶음(인도식 2자리 묶음 `12,34,567`)·숫자 문자(아랍-인도 숫자)까지 바뀐다. `fr-FR`의 공백은 일반 공백(U+0020)이 아니라 좁은 줄바꿈 없는 공백 U+202F다(같은 환경에서 코드 포인트 확인). 화면 문자열을 `split(' ')`하거나 비교하는 코드가 여기서 깨진다.
- 3: KRW·JPY는 소수 0자리라 `1234.5`가 `1,235`로 반올림됐다. 금액을 통화 소수 자릿수에 맞추지 않고 저장·계산하면 화면과 DB 값이 어긋난다.
- 4: `parseFloat`는 첫 숫자가 아닌 문자에서 멈춘다. 독일식 `1.234,5`는 `1.234`, 영어식 `1,234.5`는 `1`이 된다. 에러 없이 틀린 값이 나오는 것이 가장 위험하다.
- 5: `fr`는 0과 1.5가 `one`, `ru`는 21·101이 `one`이고 22가 `few`, `pl`은 21이 `many`(러시아어와 다름)다. 영어 서수는 1·21·101이 `one`(1st), 11~13은 `other`(11th)다.
- 6: 같은 순간인데 뉴욕은 3월 1일, 서울·도쿄는 3월 2일이다. 날짜만 저장·비교하는 코드("오늘 주문")는 시간대 경계에서 하루 어긋난다.
- 7: `de-AT`·`zh-Hant-TW`·`pt-MZ`는 Chrome 151이 데이터를 가졌다. `xx-YY`·`tlh`(클링온어)는 지원 밖이라 기본 로캘 `en-US`로 조용히 폴백했다. 밑줄 `en_US`는 BCP 47이 아니어서 `RangeError`다(Java `Locale.toString()`·POSIX 로캘 형식을 그대로 넘길 때 생긴다).
- 9: 두 "한글"·두 "é"는 화면에서 같아 보이지만 코드 포인트가 다르다. 위는 완성형(U+D55C U+AE00·U+00E9), 아래는 조합형(U+1112 U+1161 U+11AB U+1100 U+1173 U+11AF·`e`+U+0301)이다. 문서를 편집하는 도구가 정규화하면 출력 줄이 같아 보일 수 있다. 조합형 한글(초성·중성·종성 자모 6개)은 `length=6`이지만 보이는 글자는 2개다. NFC 정규화하면 2가 된다. 이모지 가족은 `length=8`, 글자 1개. 입력 길이 제한을 `length`로 걸면 사용자가 보는 글자 수와 다르다.
- 10: 120px 버튼에서 영어·한국어·일본어는 맞았고, 독일어·핀란드어는 잘렸다(`scrollWidth > clientWidth`).
- 11: `dir=rtl`에서 `margin-left`는 효과가 사라졌다(박스가 오른쪽 끝에 붙음, 오른쪽 간격 0). `margin-inline-start`는 오른쪽 40px로 뒤집혔다.

추가로 같은 환경에서 정렬·대소문자를 확인했다.

```text
sort()          Zoo apple zebra Äpfel ähnlich
Collator de     ähnlich Äpfel apple zebra Zoo
Collator sv     apple zebra Zoo ähnlich Äpfel
toUpperCase tr  İSTANBUL vs en ISTANBUL
Intl.Locale("ar").getTextInfo() {"direction":"rtl"}
```

- 기본 `sort()`는 UTF-16 코드 단위 순서라 대문자가 앞, 움라우트가 맨 뒤다. 독일어 정렬은 `ä`를 `a` 근처에, 스웨덴어 정렬은 `ä`를 `z` 뒤에 둔다. "올바른 정렬 순서"도 로캘마다 다르다.
- 터키어는 `i`의 대문자가 점 있는 `İ`다.

## 쓰이는 자료구조·알고리즘

- **복수형 규칙 = 술어 평가** — CLDR 규칙은 피연산자(n·i·v·f·t…)에 대한 `and`·`or`·`%`·범위 비교식이다. 범주 순서대로 술어를 평가해 처음 참인 범주를 고르고, 없으면 `other`다.
- **로캘 폴백 체인 = 접두 축소 탐색** — RFC 4647 lookup은 태그를 서브태그 단위로 뒤에서 잘라 가며 지원 집합(해시 집합)을 찾는다. 지원 로캘을 트라이에 두면 "가장 긴 일치 접두"를 한 번에 찾을 수 있다. [data-structure/09-trie](../../data-structure/09-trie/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **메시지 카탈로그 = 키 → (로캘 → 문장) 2단 맵** — 없는 키는 폴백 로캘의 문장을 쓴다. 번역 누락은 "키가 그대로 보임" 또는 "원문 언어가 섞여 보임"으로 드러난다.
- **정렬 = 다단계 비교 키** — 로캘 정렬(Unicode Collation Algorithm·CLDR 테일러링)은 1차(기본 글자)·2차(악센트)·3차(대소문자) 강도로 비교 키를 만든다. 실험의 독일어 정렬에서 `ähnlich`(1차 키 a-h)가 `Äpfel`(a-p)보다 앞인 이유다. [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md)(비교 정렬)
- **문자 경계 = 유니코드 세그먼트 규칙(UAX #29)** — `Intl.Segmenter`가 grapheme cluster 경계를 계산한다.

## 적용 — 풀어나가는 법

### 1. 로캘 결정 — 우선순위를 명시한다

```ts
// 사용자가 고른 값 > URL > 쿠키 > Accept-Language(첫 추정) > 기본값
const SUPPORTED = ['ko', 'en', 'de', 'ja'];                 // 소문자로 둔다
function pickLocale(requested: readonly string[]): string {
  for (const tag of requested) {
    let t = tag.toLowerCase();                              // RFC 4647 §2: 대소문자 구분 없이 비교
    while (t) {                                             // RFC 4647 §3.4 lookup: 뒤에서부터 잘라 가며
      if (SUPPORTED.includes(t)) return t;
      t = t.includes('-') ? t.slice(0, t.lastIndexOf('-')) : '';
      if (/-[a-z0-9]$/.test(t)) t = t.slice(0, -2);         // 끝에 남은 한 글자 서브태그(x·u 등)도 뗀다
    }
  }
  return 'en';
}
pickLocale(['de-CH', 'fr']);   // 'de'
pickLocale(['DE-CH']);         // 'de' (Node 20.19 확인)
pickLocale(navigator.languages);
```

- 서버가 헤더로 언어를 바꿔 응답하고 그 응답을 캐시할 수 있으면 `Vary: Accept-Language`를 붙인다(RFC 9110 §12.5.5: SHOULD). 안 붙이면 CDN이 첫 사용자의 언어판을 모두에게 줄 수 있다([network/34-http-caching](../../network/34-http-caching/2-summary.md)).
- `<html lang="de">`를 응답 언어와 맞춘다. 스크린리더 발음·하이픈 처리·폰트 선택이 이 값을 쓴다([11-accessibility-basics](../11-accessibility-basics/2-summary.md), WCAG 3.1.1).

### 2. 문장은 메시지 하나로, 서식은 Intl로

```ts
// 카탈로그(예시) — ICU MessageFormat 문법
const messages = {
  en: { cart: '{count, plural, one {# item} other {# items}} in your cart' },
  ko: { cart: '장바구니에 상품 {count}개' },
};
// 라이브러리 없이 복수형만 고를 때
const pr = new Intl.PluralRules(locale);
const forms = { en: { one: '# item', other: '# items' } } as const;
const text = forms.en[pr.select(n) as 'one' | 'other'].replace('#', new Intl.NumberFormat(locale).format(n));

// 금액·날짜·목록
new Intl.NumberFormat(locale, { style: 'currency', currency: 'EUR' }).format(amount);
new Intl.DateTimeFormat(locale, { dateStyle: 'long', timeZone: userTz }).format(instant);
new Intl.ListFormat(locale, { type: 'conjunction' }).format(names);
```

- 같은 로캘·옵션으로 여러 번 서식을 만들면 `Intl.NumberFormat` 객체를 한 번 만들어 재사용한다. MDN은 `toLocaleString`을 반복 호출할 때마다 로캘 데이터 검색을 하므로 formatter 재사용이 효율적이라고 설명한다(목록 렌더 루프 안에서 매번 `new`하지 않는다).
- 서버가 숫자를 문자열로 내려 주지 않는다. 숫자·ISO 8601 순간·ISO 4217 통화 코드를 내려 주고, 표시는 클라이언트 `Intl`이 한다. 서버 로캘 기본값에 기대어 서식을 만들면 서버 설정이 바뀔 때 출력이 바뀐다.

### 3. 입력은 서식을 벗겨서 받는다

```ts
// 사용자의 로캘 구분자를 알아낸 뒤 정규화 (간단판 — ASCII 숫자만, 자릿수 묶음 위치는 검사하지 않음:
// en-US '12,34'도 1234로 받는다. 아랍 숫자(١٢٣)·통화 기호·공백 변형은 별도 정규화가 필요)
function parseLocaleNumber(s: string, locale: string): number {
  const parts = new Intl.NumberFormat(locale).formatToParts(12345.6);
  const group = parts.find(p => p.type === 'group')?.value ?? ',';
  const decimal = parts.find(p => p.type === 'decimal')?.value ?? '.';
  const t = s.trim();
  const n = t === '' ? NaN : Number(t.split(group).join('').replace(decimal, '.'));   // Number('')는 0이라 빈 입력을 먼저 거른다
  if (Number.isNaN(n)) throw new RangeError(`not a number for ${locale}: ${s}`);   // 조용한 절단 금지
  return n;
}
parseLocaleNumber('1.234,5', 'de-DE');   // 1234.5
parseLocaleNumber('', 'de-DE');          // RangeError (Node 20.19 확인)
```

- 금액은 가능하면 `<input inputmode="decimal">` + 정수 최소 단위(센트·원)로 서버에 보낸다.

### 4. 레이아웃·방향

```css
.card { padding-inline-start: 16px; border-inline-start: 4px solid; }   /* left/right 대신 */
.icon-next { transform: scaleX(1); }
[dir="rtl"] .icon-next { transform: scaleX(-1); }                       /* 방향 있는 아이콘만 뒤집기 */
button { min-inline-size: 120px; }                                      /* 고정 width 대신 최소 폭 */
```

```html
<html lang="ar" dir="rtl">
<p>작성자: <bdi>محمد</bdi> — 3 댓글</p>   <!-- 사용자 입력 이름은 bdi로 방향 격리 -->
```

- 디자인 단계에서 가장 긴 번역(독일어·핀란드어 등)과 의사 로캘(pseudo-locale: 글자를 늘리고 악센트를 붙인 가짜 번역)로 화면을 미리 본다(해석 — 흔한 실무 기법).

### 5. 이름·주소 가정을 버린다

- McKenzie "Falsehoods Programmers Believe About Names"(2010)의 목록 중
  - "People have exactly one canonical full name."
  - "People's names fit within a certain defined amount of space."
  - "People's names are written in any single character set."
  - "People's names do not change."
- 실무 처방
  - 이름은 한 칸(전체 이름) + 필요하면 "부를 이름" 한 칸. 성·이름 분리를 강제하지 않는다.
  - 길이 상한은 넉넉히, 문자 집합은 유니코드 전체(정규화 NFC 후 저장).
  - 주소는 국가별 양식으로 받거나 자유 형식 여러 줄로 받는다. 우편번호·주(state) 필수 검증을 국가 무관하게 걸지 않는다.

### 6. 진단

- Chrome DevTools → Sensors 패널에서 Location의 locale·timezone을 바꿔 본다. 자동화는 Playwright `newContext({ locale, timezoneId })`(실험 1).
- 번역 누락 탐지: 빌드에서 카탈로그 키 집합을 로캘마다 비교한다(기준 로캘에 있고 다른 로캘에 없는 키 = 누락).
- 레이아웃 잘림 탐지: 실험 10처럼 `scrollWidth > clientWidth`인 요소를 찾아 로캘마다 보고한다.

## 장애 시나리오와 대처

### 1. 문자열 이어 붙이기 → 어순이 다른 언어에서 문장 붕괴

- **현상**: 번역된 화면에 "Warenkorb 3 in Artikel"처럼 문법이 틀린 문장이 나온다(예시).
- **보이는 형태**: 번역 파일에 "총 ", "개 상품"처럼 조각난 키가 있다. 번역가가 문맥 질문을 반복한다.
- **원인**: 문장을 코드에서 조립했다. 어순·조사·성·격 변화는 언어마다 다르다.
- **대처**: 문장 전체를 메시지 하나로 만들고 인자를 넣는다(ICU MessageFormat·MF2). 조각 키를 린트로 막는다.

### 2. "1 items" — 복수형을 코드에 박음

- **현상**: 영어에서 "1 items", 러시아어에서 "21 товаров"(21은 one 꼴이어야 함).
- **보이는 형태**: 사용자 신고, 스크린숏 리뷰.
- **원인**: `n === 1 ? 단수 : 복수` 규칙. 언어마다 범주 수와 규칙이 다르다(실험 5: ru 21=one, 22=few, pl 21=many, fr 1.5=one).
- **대처**: `Intl.PluralRules`나 MessageFormat의 `plural`로 범주를 고른다. 카탈로그에 그 로캘의 범주(`pluralCategories`)가 다 있는지 빌드에서 검사한다.

### 3. 소수점·구분자 뒤바뀜 → 금액 파싱 오류

- **현상**: 독일 사용자가 `1.234,5`€를 입력했는데 1.23€로 결제된다. 또는 서버가 `1,234.5`를 `1`로 저장한다.
- **보이는 형태**: 에러 없음. 주문 금액 이상, 정산 차이.
- **원인**: `parseFloat`·서버 기본 로캘 파서가 자기 규칙으로 읽었다(실험 4: `parseFloat("1.234,5") = 1.234`). 서버 JVM·OS 기본 로캘이 배포 환경마다 다를 때 특히 생긴다.
- **대처**: 전송 형식은 로캘 무관(점 소수점 문자열이나 최소 단위 정수)으로 고정. 화면 입력만 로캘 파서로 읽고, 읽을 수 없으면 거부한다(조용히 자르지 않는다).

### 4. 시간대 경계 → 날짜가 하루 어긋남

- **현상**: 한국 사용자가 3월 2일 0시 30분에 주문했는데 "3월 1일 주문"으로 보이거나 일별 집계에서 전날로 잡힌다.
- **보이는 형태**: 자정 근처 주문만 틀린다. UTC 서버 로그와 화면 날짜가 다르다.
- **원인**: 순간을 UTC 날짜로 잘라 저장하거나, 서버 시간대로 표시했다(실험 6: 같은 순간이 뉴욕 3/1, 서울 3/2).
- **대처**: 순간(UTC 타임스탬프)과 사용자 시간대를 함께 저장하고, 표시·"일" 경계 계산은 그 시간대로 한다(`Intl.DateTimeFormat(…, { timeZone })`).

### 5. 이름을 성·이름 2칸으로 강제 → 가입 불가

- **현상**: 이름이 한 단어인 사용자, 성이 여러 단어인 사용자, 라틴 문자가 아닌 이름의 사용자가 가입·결제를 못 끝낸다.
- **보이는 형태**: 폼 검증 에러("성을 입력하세요", "영문만 입력"), 특정 국가 가입 이탈.
- **원인**: 한 문화의 이름 구조를 스키마·검증 규칙에 박았다.
- **대처**: 전체 이름 한 칸, 유니코드 허용, 길이 넉넉히. 결제사·배송사가 특정 형식을 요구하면 그 경계에서만 변환한다.

## 핵심 문장

- 로캘은 언어·지역·선호의 묶음이고, BCP 47 태그로 표현하며, 협상은 사용자 선택 > 요청 헤더 순으로 한다. 헤더로 바꾼 응답을 캐시가 언어별로 재사용하게 하려면 `Vary: Accept-Language`를 보낸다.
- 문장은 조립하지 않고 메시지 하나로 번역한다. 어순·복수형은 메시지 안에서 언어마다 정한다.
- 복수형 범주 수는 언어마다 다르다(ko 1개, en 2개, ru 4개, ar 6개 — Chrome 151 `Intl.PluralRules` 실측).
- 숫자·통화·날짜 서식은 CLDR 데이터이고 `Intl` API로 만든다. 전송·저장은 로캘 무관 형식으로 한다.
- 날짜는 순간과 표시를 나눈다. 같은 순간이 시간대에 따라 다른 날짜다.
- 지원 밖 로캘은 `Intl`이 기본 로캘로 조용히 폴백한다. 잘못된 태그(`en_US`)는 `RangeError`다.

## 관련 주제·근거

- 선행
  - [05-fetch-from-browser](../05-fetch-from-browser/2-summary.md) — 요청 헤더·자격 증명
  - [architecture/04-character-encoding-unicode](../../architecture/04-character-encoding-unicode/2-summary.md) — 코드 포인트·UTF-16·정규화(원고는 foundations/data-representation)
  - [network/33-http-semantics](../../network/33-http-semantics/2-summary.md) — 내용 협상, `Vary`
- 후속·연결
  - [11-accessibility-basics](../11-accessibility-basics/2-summary.md) — `lang` 속성, 스크린리더 발음
  - [15-web-font-loading](../15-web-font-loading/2-summary.md) — 언어별 폰트 서브셋·`unicode-range`
  - [network/34-http-caching](../../network/34-http-caching/2-summary.md) — `Vary`와 캐시 키
  - [data-structure/09-trie](../../data-structure/09-trie/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/03-quick-sort](../../algorithm/03-quick-sort/2-summary.md)
- 표준·문서
  - RFC 5646 (BCP 47) Tags for Identifying Languages <https://www.rfc-editor.org/rfc/rfc5646>
  - RFC 4647 Matching of Language Tags(lookup·filtering) <https://www.rfc-editor.org/rfc/rfc4647>
  - RFC 9110 §12.5.4 Accept-Language(예: `da, en-gb;q=0.8, en;q=0.7`, 순서에 기대지 말 것, 프라이버시·핑거프린팅 §17.13), §12.1 Proactive Negotiation, §8.5 Content-Language, §12.5.5 Vary <https://www.rfc-editor.org/rfc/rfc9110.html>
  - Unicode CLDR <https://cldr.unicode.org/> · Language Plural Rules 표 <https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html>
  - Unicode MessageFormat(MF2) <https://messageformat.unicode.org/> · CLDR 47 릴리스(MF2 Stable, 2025-03-13) <https://blog.unicode.org/2025/03/unicode-cldr-47-release-messageformat-2.html>
  - ICU User Guide "Formatting Messages" <https://unicode-org.github.io/icu/userguide/format_parse/messages/>
  - MDN `Number.prototype.toLocaleString` Performance 절(formatter 재사용) <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/toLocaleString>
  - ECMA-402 ECMAScript Internationalization API(`Intl.NumberFormat`·`PluralRules`·`DateTimeFormat`·`Segmenter`·`Collator`) <https://tc39.es/ecma402/>
  - UAX #29 Text Segmentation <https://www.unicode.org/reports/tr29/> · UTS #10 Unicode Collation Algorithm <https://www.unicode.org/reports/tr10/>
  - CSS Logical Properties and Values Level 1 <https://www.w3.org/TR/css-logical-1/>
  - McKenzie, "Falsehoods Programmers Believe About Names" (2010) <https://www.kalzumeus.com/2010/06/17/falsehoods-programmers-believe-about-names/>
  - W3C Internationalization "Personal names around the world" <https://www.w3.org/International/questions/qa-personal-names>
- 실험 목록
  - Intl·협상·레이아웃·RTL: headless Chrome 151.0.7922.173 + playwright-core 1.62.1(Node 20.19), 로컬 Node `http` 서버 127.0.0.1(임의 포트, Accept-Language 반사), 컨텍스트 `locale`·`timezoneId` 지정. 출력 11절.
  - 정렬·대소문자·방향 정보: 같은 브라우저에서 `Intl.Collator`·`toLocaleUpperCase`·`Intl.Locale#getTextInfo()`.
  - 사실 점검 재실행(2026-10-04, 같은 Chrome 151): 두 스크립트를 다시 돌려 위 출력과 바이트 단위로 같았다. `fr-FR` 구분자가 U+202F인 것과 `getTextInfo`가 메서드(속성 `textInfo`는 없음)인 것도 같은 환경에서 확인.
