# cs/issue/search-engine/multilingual-analysis-chain — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **folding이 앞에 오면 변환기가 쓸 정보가 사라진다.**\
토큰 필터 체인은 순차 파이프라인이라 앞 필터의 출력이 뒤 필터의 입력이다.\
`asciifolding`이 먼저 `ü → u`로 바꾸면 뒤의 독일어 음차 필터는 `Munchen`을 받아 ü 규칙 대신 u 규칙으로 변환하고, 원문 기반 변환 결과로 검색하면 맞지 않는다.\
선택지 셋(폴딩 제거 / `preserve_original: true` / 분석기 분리로 필드 2배)을 비교해 `preserve_original: true`를 택했다 — 원문 토큰과 폴딩 토큰을 **같은 position**에 둘 다 내보내 두 요구를 모두 만족한다(인덱스 크기 증가는 예상치로 기록).\
분석기 변경이라 새 인덱스 생성 시점에만 적용된다(재색인 필요).
   > **asciifolding** — 악센트·발음 구별 기호가 붙은 문자를 ASCII 기본 문자로 바꾸는 토큰 필터(`é → e`).

2. **char_filter는 lowercase보다 먼저 돈다.**\
실행 순서가 char_filter → tokenizer → token filter이고, lowercase는 token filter로만 존재한다(char_filter 버전 없음).\
그래서 char_filter의 매핑은 **원문 대소문자 그대로**를 본다 — `ph => f`는 `PH`에 걸리지 않는다.\
패턴 치환으로 소문자화하는 방법은 복잡해서, **매핑에 대소문자 조합을 모두 나열**하는 쪽을 택했다(최대 수십 개라 부담이 없다).\
참고로 mapping char_filter는 긴 패턴을 우선 매칭한다(`ph`가 `p`보다 먼저).

3. **원문 통과 vs 기본값 덮어쓰기.**\
(a) 모르는 문자를 **그대로 출력에 붙이면**(pass-through) 다른 스크립트 문자는 원문 그대로 남아, 같은 원문으로 색인된 토큰과 여전히 매칭될 수 있다.\
(b) 모르는 문자를 **기본 출력값으로 처리**하면(default 분기 → 고정 문자) 숫자·타 스크립트·기호가 모두 같은 기본 문자로 바뀐다 — 숫자 `004`도 타 스크립트 세 글자도 `xxx`가 된다.\
(b)가 에러 없이 토큰을 파괴한다: 숫자 문서끼리 같은 쓰레기 토큰을 공유해 유사도 상위를 오염시키고, 이미 대상 표기인 쿼리는 색인된 원문과 매칭되지 않는다.\
여기에 매핑에 `search_analyzer`가 없어 색인용 변환 분석기가 **쿼리에도** 적용되자, 이미 변환된 표기의 쿼리가 한 번 더 변환돼 망가졌다.
   > **fallback 분기** — 어떤 규칙에도 해당하지 않는 입력을 처리하는 마지막 분기. 이 분기의 기본값이 곧 "모르는 입력"에 대한 정책이다.

4. **두 겹 가드와 오버라이드 누락.**\
진입부 passthrough(대상 스크립트가 하나도 없으면 입력을 그대로 반환)는 순수 비대상 입력을 통째로 우회시키지만, 대상 문자와 숫자가 **섞인** 입력은 루프로 들어간다 — 그래서 루프 안에 숫자 skip을 따로 둬 혼합 입력을 보호한다.\
상속 템플릿의 진입 메서드에 가드를 넣어도, 서브클래스가 그 메서드를 **오버라이드**하면 템플릿을 우회해 가드가 적용되지 않는다 — 오버라이드한 서브클래스 여러 곳에 가드를 명시로 추가했다.\
변환기 출력이 바뀌었으므로 이후 재색인이 필요했다.\
같은 계열의 소규모 해결: 한 플러그인 안에서 pass-through가 보장된 쪽 서브필드만 쿼리에 추가하고, 덮어쓰기 쪽 서브필드는 쿼리 시 분석기 override가 필요해 범위에서 뺐다.

5. **`_analyze`와 실제 색인 경로의 입력은 다르다.**\
`_analyze`에 넣은 문자열은 사람이 고른 입력이지만, 실제 색인은 앞단 전처리(이름 split·부분 변환)를 거친 문자열을 받는다.\
쉼표로 결합된 다중 이름을 **공백으로만** split해 "비라틴 문자+쉼표+영어"가 한 토큰으로 남았고, 원 스크립트 문자만 변환하는 음차기가 라틴을 남겨 "변환 문자+쉼표+영어"가 커스텀 필터에 들어갔다 — 이 조합이 필터의 인덱스 계산을 깨뜨렸다.\
최소 재현을 조합으로 좁혔다: 변환 문자+쉼표 OK, 변환 문자+영어 OK, **변환 문자+쉼표+영어만 THROW**.\
교정은 필터가 아니라 **필터의 입력 불변식**을 복원하는 것이었다 — 남은 라틴 런을 음차하고 쉼표·세미콜론을 공백으로 정규화한 뒤, 옳은 매핑으로 인덱스를 재생성해 재색인(실패 0건).\
운영 인덱스가 옛 매핑(분석기가 전체 필드에 걸림)이라 실패 표면이 넓어져 있었던 것도 가중 요인이었다.

6. **경계 없는 문자체계의 부분일치.**\
띄어쓰기가 없으면 기본 분석기가 단어 경계를 얻지 못하고, 단순 substring은 짧은 키워드(2글자)가 **무관한 긴 단어 내부**에 걸려 과매칭한다.\
방법 1: 사전 기반 분절기(`icu_tokenizer`) 서브필드 + `match_phrase`(연속 위치) — 단어 경계를 지키는 부분일치(과매칭 태깅이 줄어든 것을 실측).\
방법 2: 1글자 토큰 + `match_phrase`로 "연속 부분일치"를 만들고, 키워드의 문자체계(한자 포함 여부)를 판정해 **원어 필드 / 영문 필드로 라우팅**(라틴 키워드를 원어 필드에 보내지 않아 오매칭 방지) — 스크래치 인덱스에서 연속 hit / 비연속 miss를 실증했다.\
주의: 방법 2의 1글자 토큰 + phrase는 본질적으로 **연속 substring 매칭**이라 단어 경계를 지키지는 않는다 — 흩어진 글자 매칭은 막지만 긴 단어 내부 매칭은 남는다. 과매칭을 줄이는 몫은 주로 스크립트 라우팅이고, 경계까지 지키려면 방법 1(사전 분절)이 필요하다.
   > **icu_tokenizer** — 유니코드 텍스트 분절 규칙과 사전을 써서 공백 없는 언어도 단어 단위로 나누는 토크나이저(플러그인).

7. **각 단계가 전제하는 입력 형태.**\
동의어 필터는 규칙을 앞 단계 체인(토크나이저 포함)으로 분석해 파싱하는데, 이때 **단일 토큰 경로**를 전제한다 — `decompound_mode: mixed`는 복합어를 원형 + 분해형의 여러 경로(그래프)로 내보내 다중 단어 동의어 빌드가 실패했다 → `discard`로 단일 경로화.\
규칙 파일 파서는 **UTF-8·LF 텍스트**를 전제하는데, BOM과 CRLF가 규칙 문자열에 섞여 해석이 실패했다 → 이미지 빌드 시 `dos2unix`·`iconv` + 로케일 지정.\
편집거리 fuzziness는 **문자(코드포인트) 단위**를 전제하는데, 한글은 자모가 결합된 음절이 한 문자다 — "블랙 → 블렉" 같은 자모 한 개 차이도 음절 1개 치환(거리 1)으로 잡히긴 하지만, 한글 단어는 문자 수가 짧아 `fuzziness: AUTO`에선 허용 편집이 0(2자 이하)이 되기 쉽고, 거리를 허용하면 전혀 다른 음절로의 치환도 같은 거리 1이라 정밀도가 떨어진다(자모 수준 유사도를 표현하지 못함) → edge n-gram(2~4)으로 보완하고 fuzziness는 영문 필드에만 적용하거나 1로 제한했다.\
(이 세 사례는 회고 서술 수준 기록이라 원인 설명은 문서 수준이다.)

## 문제 구조 (추상화 코드)

### 변형 A — 필터 순서가 정보를 먼저 지움
① 문제 코드
```json
"analyzer": { "translit_de": { "tokenizer": "standard",
  "filter": ["lowercase", "asciifolding", "translit_x_de"] } }    // ü → u 후 변환 → 틀린 변환
"char_filter": { "spelling": { "type": "mapping", "mappings": ["ph => f", "ck => k"] } }   // 대문자 미적용
```
② 고친 코드
```json
"filter": { "folding_keep": { "type": "asciifolding", "preserve_original": true } },
"analyzer": { "translit_de": { "tokenizer": "standard",
  "filter": ["lowercase", "folding_keep", "translit_x_de"] } }    // 원문 + 폴딩 두 토큰, 같은 position
"char_filter": { "spelling": { "type": "mapping",
  "mappings": ["ph => f", "PH => f", "Ph => f", "pH => f", "ck => k", "CK => k", "Ck => k", "cK => k"] } }
```
무엇이 깨졌나: 체인의 순서가 곧 정보 손실의 순서라는 걸 놓쳤다.

### 변형 B — 비대상 스크립트를 기본값으로 흡수 + 쿼리 재통과
① 문제 코드
```java
String transliterate(String in) {
    for (char c : in.toCharArray()) {
        out.append(mapOrDefault(c));           // 모르는 문자 → default: 고정 문자 'x'
                                               // '0' → "x"
    }
}
```
```json
"name_translit": { "type": "text", "analyzer": "translit_x" }   // search_analyzer 없음 → 쿼리도 변환
```
② 고친 코드
```java
String transliterate(String in) {
    if (!containsTargetScript(in)) return in.trim();       // 가드2: 비대상 입력 passthrough
    for (int i = 0; i < in.length(); i++) {
        char c = in.charAt(i);
        if (c >= '0' && c <= '9') continue;                 // 가드1: 혼합 입력의 숫자 skip
        // ...
    }
}
// 템플릿을 오버라이드한 서브클래스에도 가드 명시 → 재색인
```
무엇이 깨졌나: "모르는 입력"의 정책이 원문 통과가 아니라 기본값 덮어쓰기였고, 같은 변환이 쿼리에도 걸렸다.\
같은 구조: 한 플러그인의 두 변환기 중 한쪽은 매치 실패 시 `out.append(c)`(통과), 다른 쪽은 기본값 덮어쓰기 → 통과 쪽 서브필드만 쿼리에 추가.

### 변형 C — 혼합 입력이 커스텀 필터의 입력 불변식을 깸
① 문제 코드
```java
for (String name : raw.split("\\s+")) {          // "ชื่อ,Brand" 가 한 토큰으로 남음
    index(partialTransliterate(name));            // 대상 문자만 변환 → "<변환>,Brand" → 필터에서 THROW
}
```
② 고친 코드
```java
for (String name : raw.split("\\s+")) {
    String t = partialTransliterate(name);
    t = transliterateLatinRuns(t);   // 남은 [A-Za-z]+ 런 음차 + 쉼표·세미콜론 → 공백 정규화 → 단일 스크립트
    index(t);
}
```
무엇이 깨졌나: 필터는 단일 스크립트 입력을 전제했는데, 앞단 split과 부분 변환이 혼합 문자열을 만들었다.

### 변형 D — 경계 없는 문자체계의 부분일치
① 문제 코드
```python
matched = [doc for doc in docs if keyword in doc.desc_text]      # substring → 긴 단어 내부 과매칭
field = "desc_en"                                                 # 한자 키워드도 영문 필드로
```
② 고친 코드
```json
"desc_native": { "type": "text", "fields": {
  "morph": { "type": "text", "analyzer": "icu_morph" } } }        // icu_tokenizer + lowercase
```
```java
String field = hasCjk(q) ? "desc_native" : "desc_en";           // 스크립트 판정 라우팅
query = matchPhrase(field, q);                                    // 연속 위치 = 경계를 지키는 부분일치
```
무엇이 깨졌나: 공백을 단어 경계로 가정하는 도구를 공백 없는 문자체계에 썼다.

### 변형 E — 체인 설정 간 전제 충돌
① 문제 코드
```json
"tokenizer": { "ko": { "type": "nori_tokenizer", "decompound_mode": "mixed" } }   // 그래프 × 다중 단어 동의어 → 빌드 실패
// 동의어 파일: BOM + CRLF (Windows 작성)
// 한글 필드에 fuzziness: AUTO
```
② 고친 코드
```json
"tokenizer": { "ko": { "type": "nori_tokenizer", "decompound_mode": "discard",
                       "user_dictionary": "analysis/userdict.txt" } }
// 빌드: dos2unix + iconv(UTF-8) + 로케일 지정
// 한글은 edge n-gram(2~4), fuzziness는 영문 필드에만 적용하거나 1로 제한
```
무엇이 깨졌나: 각 단계가 기대하는 입력 형태(단일 경로·깨끗한 텍스트·문자 단위 거리)를 앞 단계가 보장하지 않았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
