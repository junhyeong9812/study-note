# cs/issue/data/key-normalization-consistency — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **검사 맵과 저장 맵의 정규화 불일치.**\
   누적 맵이 대소문자를 구분하므로 `charset`과 `CHARSET`을 **다른 키**로 보고 둘 다 넣는다 → 중복 거부가 발동하지 않고, 최종 저장(대소문자 무시 맵)에서는 뒤 값이 앞 값을 덮어 **조용히 채택**된다. 같은 대소문자의 중복은 정상 거부되니 결함이 눈에 띄지 않는다.\
   누적 맵을 **대소문자 무시 맵**(`Locale.ROOT`)으로 바꾸면 `put()`이 대소문자만 다른 기존 키에도 **이전 값을 반환**하므로, 이미 있던 `if (put(...) != null) throw` 로직이 코드 수정 없이 발동한다 — 검사 단계가 저장 단계와 같은 키 동등성을 갖게 된 것이다.

2. **저장은 소문자, 조회는 원본.**\
   username에 대문자가 있는 사용자(`"Admin"`)만 실패한다 — 인증 등 다른 연산은 소문자로 조회하므로 되는데, 비밀번호 변경만 원본으로 조회해 "현재 사용자가 존재하지 않음" 예외가 난다.\
   착시: 이름이 "대문자 사용자 비밀번호 변경" 같은 기존 테스트가 실제로는 **다른 메서드**를 호출하고 있었다 — 테스트 이름이 아니라 호출 대상을 확인해야 한다.\
   `Locale.ROOT`는 로캘 의존 대소문자 변환(터키어 `I` → 점 없는 `ı` 등)을 피하고, 저장 쪽과 **같은 로캘**을 쓰기 위해서다.
   > **로캘 의존 케이스 변환** — `toLowerCase()`가 기본 로캘을 따르면 같은 문자열이 환경마다 다른 결과가 된다.

3. **한쪽만 trim → 방향만 바뀐다.**\
   DB의 그룹 키는 콜레이션 규칙(PAD SPACE면 후행 공백 무시, NO PAD면 구분)과 생성 컬럼으로 계산되고, 앱은 원본 `equals`로 계산한다.\
   앱만 `trim()`하면 후행 공백 차이는 맞춰지지만 **선행 공백·NO PAD 콜레이션**에서는 이번엔 앱이 같다고 보고 DB가 다르다고 본다 — 페이지 경계를 넘어 병합되지 않고 경고도 침묵했다. 불일치가 사라진 게 아니라 **방향만 바뀌었다**.\
   같은 결함을 두 번 고쳐도 깨졌다면 **토대가 틀린 것**이다 — polish를 멈추고 설계를 되돌렸다: 양쪽 모두 **raw 정확 일치**로 복원 + raw로는 안 맞지만 정규화하면 맞는 후보를 검출하는 순수 함수 + 경고(콜레이션 폴딩을 가시화), "공백 변형이 없다"는 데이터 가정은 명시.\
   덧: 스트리밍 dedup은 정렬 키가 중복을 **인접**시켜야 가능하다 — 같은 식별자의 여러 표기가 정렬상 멀리 떨어지면 배치 dedup으로는 못 잡으므로 리더의 정렬 축을 식별자 기준으로 바꿨다.

4. **표기 차이 조인.**\
   동등 비교는 "같다/다르다"만 답하고 "형식이 다르다"는 말하지 않는다 → 조인 결과가 0건이거나 해당 기능이 **아무 일도 안 하는 것처럼** 보일 뿐 예외가 없다(실측: UI 접기 기능이 사실상 무동작, 한 검색 기능의 결과가 항상 0건, 괄호 주석 유무로 일부 행 매핑 실패).\
   평가에서는 정답이 있는데도 식별자 형식이 달라 **"미검출"로 집계** → 히트율이 크게 과소 측정됐고, 형식을 맞추자 실제 수준으로 올라왔다. 지표 하락이 모델이 아니라 조인 키 문제였다.\
   교정: 경계에서 정규화하되, 조회 때마다 정규식을 돌리지 말고 **맵 구축 시 대체 키를 1회 추가 등록**(기존 키와 충돌하면 추가하지 않음). 의미를 가진 괄호 표기는 보존.

5. **요청 echo 대신 정규형.**\
   소비자는 정규형(대문자 코드)으로 exact-match 필터를 걸어 두는데, 응답이 호출자 입력(소문자)을 그대로 돌려주면 **전부 걸러져** "결과가 안 보인다" — 조회는 성공했는데.\
   경계에서는 라우팅을 위해 이미 파싱한 enum의 **정규 이름**을 내보낸다. 덤으로 입력 검증을 빈 결과 검사보다 먼저 둬, 잘못된 코드는 404가 아니라 400이 되게 한다.

6. **유니코드의 두 경우.**\
   **위치 형태**(어말 `ς` U+03C2 vs 중간 `σ` U+03C3)는 같은 문자의 표기 변형이므로 **양쪽을 같은 규칙으로 정규화**한다 — 입력은 발음 구별 기호 제거 과정에서 `σ`로 바뀌고 사전 키는 `ς` 그대로라 룩업이 실패했다 → `ς→σ` 한 줄로 누락 해소.\
   **동형문자**(키릴 `С`·`Р` vs 라틴 `C`·`P`)는 서로 다른 문자이므로 정규화 대상이 아니다 — 사람 검토는 통과하고 검색·비교에서만 어긋나므로, **비ASCII 스크립트 스캔**(키릴·그리스·아르메니아·히브리·아랍)으로 찾아 교체하고 0건을 확인한다.
   > **동형문자(homoglyph)** — 다른 코드포인트인데 같은 글리프로 보이는 문자.

7. **정규화의 경계.**\
   **하면 안 되는 곳**: URL 경로는 대소문자를 구분하므로 수집용 인터셉터가 URI를 소문자화하면 camelCase 라우트가 다른 키가 된다 → context-path와 후행 슬래시만 제거하고 대소문자는 보존.\
   **검증으로 착각**: `trim()`은 양끝만 지운다 — "공백 없음"을 보장하지 않아 `a b@c.com`이 통과했다 → 내부 공백은 `contains(whitespace)`로 따로 검사.\
   **순서**: `"Bearer "`(공백 포함) 접두 검사 전에 `trim()`하면 `"Bearer "` → `"Bearer"`가 되어 접두가 안 맞고 원문이 토큰으로 넘어간다(기록상 이 값은 뒤 단계의 토큰 파싱에서 거부되므로 테스트 단언을 실제 동작에 맞췄다).

## 문제 구조 (추상화 코드)

### 변형 A — 검사 단계만 정규화가 다름
① 문제 코드
```java
Map<String, String> params = new LinkedHashMap<>();            // 대소문자 구분
for (String p : tokens) {
    // ... attribute, value 파싱
    if (params.put(attribute, value) != null)                  // charset vs CHARSET → 다른 키
        throw new InvalidFormatException("duplicate parameter '" + p + "'");
}
return new Result(caseInsensitiveCopy(params));                // 저장은 대소문자 무시 → 뒤 값 채택
```
② 고친 코드
```java
Map<String, String> params = new CaseInsensitiveMap<>(4, Locale.ROOT);   // 저장과 같은 동등성
// 나머지 동일 — put()이 case-variant 중복에도 이전 값을 반환해 거부 발동
```
무엇이 깨졌나: 비교 의미론(대소문자 무시)과 검사용 자료구조의 키 동등성(구분)이 달라 검사가 우회됐다.

### 변형 B — 조회 단계만 정규화가 다름
① 문제 코드
```java
void changePassword(String oldPw, String newPw) {
    String username = currentUser().getName();
    User user = this.users.get(username);                      // 저장은 toLowerCase(ROOT)
    if (user == null) throw new IllegalStateException("Current user doesn't exist");
    // ...
}
```
② 고친 코드
```java
User user = this.users.get(username.toLowerCase(Locale.ROOT));
```
무엇이 깨졌나: 저장 키 규칙을 한 메서드만 따르지 않았다.

```java
// 같은 구조: 선언 맵은 lowerCase(provider.nameToUse(name)) 로 넣었는데 반환값 분기만 raw 이름으로 조회
param = declared.get(returnName);                              // 실패
if (param == null) param = declared.get(firstOutName);         // 휴리스틱 폴백이 OUT 값을 반환값으로 채택
// 고친 코드: 조회와 폴백 모두 같은 정규화를 거친다
param = declared.get(nameToCheck);
if (param == null) param = declared.get(lowerCase(provider.nameToUse(returnName)));
if (param == null && !outNames.isEmpty())
    param = declared.get(lowerCase(provider.nameToUse(outNames.get(0))));
```
무엇이 깨졌나: 선언 순서에 따라 벤더 A에서는 반환값 대신 OUT 값이 무예외로 반환되고, 벤더 B에서는 올바른 선언이 예외로 거부됐다.

### 변형 C — 두 축(DB·앱)의 비교 규칙 불일치
① 문제 코드
```java
// SQL: GROUP BY id_num  (콜레이션 PAD SPACE: 후행 공백 무시)
// 앱:  key = row.idNum()                       → 1차 수정: row.idNum().trim()
//      선행 공백·NO PAD 콜레이션에서 여전히 불일치 (방향만 바뀜) + warn 침묵
```
② 고친 코드
```java
String key = row.idNum();                                     // 양축 raw 정확 일치
List<String> suspects = foldedOnlyCandidates(requested, got); // raw 불일치지만 폴딩하면 같은 후보
if (!suspects.isEmpty()) log.warn("collation-folded keys: {}", suspects);
// 가정 명시: 공백 변형 부재. 스트리밍 dedup은 리더 정렬 축을 식별자 기준으로
```
무엇이 깨졌나: 그룹 키를 두 곳에서 계산하면서 비교 규칙을 한쪽만 바꿨다.

### 변형 D — 시스템 간 표기 차이
① 문제 코드
```ts
const collapsedCodes = ["A0101", "B0101"];             // API 형식
if (!collapsedCodes.includes(`${groupCode}-01-01`)) { /* ... */ }   // UI 형식 → 항상 false, 기능 무동작
```
② 고친 코드
```ts
const collapsedCodes = ["A-01-01", "B-01-01"];        // 비교 쪽과 같은 형식으로 (API→UI 변환 규칙 문서화)
```
무엇이 깨졌나: 같은 식별자를 서로 다른 표기로 저장·비교해 동등 비교가 항상 실패했지만 예외가 없었다.

```python
# 같은 구조: 조인 키 표기(괄호 원어 병기 주석) 차이 → 맵 구축 시 대체 키 1회 등록
ANNOT_PAREN_RE = re.compile(r"\([A-Za-z ]+\)")
for k, v in rows:
    m[k] = v
    alt = ANNOT_PAREN_RE.sub("", k)
    if alt != k and alt not in m: m[alt] = v            # 기존 키 충돌 방지, 의미 있는 괄호는 보존
```
```java
// 같은 구조: 응답에 요청값 echo → 경계에서 정규형
Code resolved = Code.from(input);                      // 검증을 빈 결과 검사보다 먼저 (잘못된 입력 = 400)
// ...
return Response.from(result, resolved.name());         // input 그대로가 아니라 정규 이름
```
- 같은 구조: 두 저장소가 같은 식별자를 다른 규칙으로 정규화 → 검색 결과 항상 0건 → 규칙 통일.
- 같은 구조: 평가 조인 키 형식 차이 → 정답이 "미검출"로 집계(과소 측정) → 정규화 후 재측정.

### 변형 E — 유니코드 형태 변형
① 문제 코드
```ts
const key = removeAccents(word);                     // 어말 ς(U+03C2) → σ(U+03C3)
dict.get(key);                                         // 사전 키는 ς 그대로 → 룩업 실패
```
② 고친 코드
```ts
const norm = (s: string) => removeAccents(s).replace(/ς/g, "σ");   // 키·입력 동일 정규화
dict.get(norm(word));                                  // 사전 구축에도 norm 적용
```
무엇이 깨졌나: 비교 대상 두 쪽이 서로 다른 정규화를 거쳐 같은 단어가 다른 코드포인트가 됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

위 변형들의 기본 방안은 "모든 지점이 같은 정규화 함수를 거친다"이다. 같은 원리에서 정규화가 **답이 아니거나 한계가 있는** 사례는 다른 대응을 요구한다.

### 방안 1 — 동일 정규화 (기본)
```java
static String key(String s) { return s.toLowerCase(Locale.ROOT); }   // 검사·저장·조회 모두 key()
```

### 방안 2 — 정규화로 안 잡히는 것은 스캔 (동형문자)
```sh
# 비ASCII 스크립트 문자 탐지 (키릴·그리스·아르메니아·히브리·아랍) → 교체 후 0건 확인
# (예시 명령 — 원 스캔 명령은 기록되지 않았고 대상 스크립트 목록만 남아 있다)
grep -nP '[\p{Cyrillic}\p{Greek}\p{Armenian}\p{Hebrew}\p{Arabic}]' docs/**/*.md
```

### 방안 3 — 정규화와 검증을 분리
```rust
let s = raw.trim();                                           // 정규화: 양끝만
if s.contains(char::is_whitespace) { return Err(Invalid); }   // 검증: 내부 공백은 따로
```

### 방안 4 — 정규화의 범위·순서를 도메인에 맞춘다
```java
// URL 경로: 대소문자 보존, context-path·후행 슬래시만 제거
String path = stripTrailingSlash(dropContextPath(uri));      // toLowerCase 금지
```
```java
// 순서 문제: trim이 공백 포함 접두어를 먼저 망가뜨림
String t = header.trim();                                     // "Bearer " → "Bearer"
if (t.startsWith("Bearer ")) t = t.substring(7);              // 매칭 실패 → 원문 "Bearer"가 토큰으로
```

| | 방안 1 동일 정규화 | 방안 2 스캔 | 방안 3 정규화 ≠ 검증 | 방안 4 범위·순서 |
|---|---|---|---|---|
| 전제 | 차이가 "같은 것의 표기 변형" | 차이가 "다른 문자인데 같아 보임" | 정규화 후에도 남는 불법 입력이 있음 | 도메인이 일부 차이를 의미로 씀 |
| 비용 | 공용 함수 하나 + 모든 지점 적용 | 스캔 단계 추가 | 검사 추가 | 도메인 규칙 확인 |
| 실패 모드 | 한 지점 누락 → 이 카드의 변형들 | 스캔 범위 밖 스크립트 누락 | 정규화만 보고 통과시킴 | 과잉 정규화로 서로 다른 키가 합쳐짐 |
| 맞는 조건 | 검사·저장·조회·조인 키 | 사람이 쓴 텍스트·식별자 | 입력 검증 | URL·토큰 접두 등 형식 규약 |

**결론**: 기본은 방안 1이지만, 적용 전에 "이 차이가 표기 변형인가, 다른 의미인가"를 먼저 판정한다.\
표기 변형이면 한 함수로 모든 지점을 묶고, 다른 문자면 스캔으로, 의미 있는 차이(URL 대소문자)면 정규화하지 않는다.\
정규화는 검증을 대신하지 못하며, 접두·구분자 검사처럼 공백이 의미를 갖는 규칙 앞에서는 **순서**가 결과를 바꾼다.
