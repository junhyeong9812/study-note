# cs/issue/data/ad-hoc-parsing-of-structured-text — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **정규식 주석 마스킹.** 정규식은 "지금 라인 주석 안인지, 문자열 안인지"를 모른다.\
   그래서 `// note /*`의 `/*`나 문자열 속 `/*`를 블록 주석 시작으로 오인하고, 닫는 `*/`가 없으면 `$`까지 — 즉 **문서 잔여 전체**를 주석으로 마스킹한다.\
   주석·문자열 경계는 현재 문맥이라는 **상태**에 의존하는 문법이라 정규 언어로 표현되지 않는다. 패턴을 더 정교하게 해도 새 반례가 나온다 — 실제로 첫 수정(정규식 개선)이 post-fix 재점검에서 다시 회귀했다.
   > **상태 기계 스캐너** — 문자를 하나씩 읽으며 현재 상태(code·line·block·str·chr)에 따라 다음 상태를 정하는 파서. 문맥 의존 경계를 정확히 잡는다.

2. **first-`{` ~ last-`}` 슬라이스.** 유효한 JSON 뒤에 설명 산문이 오고 그 안에 `}`가 있으면, 마지막 `}`까지 잘라 **산문이 섞인 문자열**을 파싱하게 된다.\
   올바른 스캔은 첫 `{`부터 깊이를 세되, **문자열 리터럴 안의 괄호(와 이스케이프)**는 세지 않아야 한다 — 깊이가 0이 되는 지점이 객체의 끝이다.

3. **구조화 텍스트 일괄 편집.** 에러는 **나지 않는다**. 비탐욕 `</div>\s*</div>`는 중첩을 모르므로 "처음 만나는 닫힘 쌍"에서 끊거나 뒤 블록까지 삼켜, 한 쪽 분량 블록이 전체 경력을 포함해 여러 쪽으로 번졌다.\
   `**` 일괄 치환은 문서 주석 여는 표시 `/**`의 뒤 `**`를 굵게 표시로 잡아 `/`만 남기는 바람에 한 줄짜리 문서 주석이 든 파일 21개가 컴파일 불가가 됐다(손상 파일 141개).\
   추적되지 않은(untracked) 파일은 버전 관리로 복구할 수 없어 수동 복구가 필요했다 — 산출물은 받자마자 커밋한다.

4. **중첩 구분자.** 따옴표 체크 → 괄호 체크를 **한 번씩** 하면 `( "a b" )`는 괄호만 벗겨지고 드러난 따옴표가 남는다.\
   구분자를 벗긴 뒤 드러난 안쪽 층을 다시 검사해야 한다 — **변화가 없을 때까지 반복**(고정점)하되, 괄호는 **깊이를 추적해 첫 `(`의 짝이 마지막 `)`일 때만** 벗긴다(`(a) b (c)` 같은 값의 내부 괄호 보존).\
   같은 정규화가 여러 경로(쿼리 파서·하이라이트 추출·상세검색)에 흩어져 있으면 한 곳만 고쳐진다 — 한 함수로 단일화한다.

5. **EOF 미검사와 불균형.** 한 단계 괄호만 가정한 파서가 닫는 괄호를 찾는 루프에서 EOF를 확인하지 않으면 **무한 루프**가 된다.\
   중첩은 재귀로 처리하고, 불균형을 감지하면 명시적 결과를 돌려준다 — 이 사례에서는 에러 대신 **원문 문자열 그대로 검색**으로 degrade했다.

6. **줄 단위 정규식 + 첫 매칭.** YAML의 주석 행도 같은 텍스트 패턴(`"9200:9200"` 류)을 가진다.\
   파일 위쪽에 주석 처리된 옛 설정이 있으면 "첫 매칭 채택" 규칙에서 **주석이 실설정을 이긴다** → 옛 포트를 바라봤다.\
   최소 수정은 `#`로 시작하는 행 건너뛰기, 근본적으로는 실파서를 쓴다.

7. **무음 오작동 드러내기.** 정규식은 틀려도 예외 없이 "덜/더" 매칭만 하므로 결과를 **숫자로** 검증해야 한다.\
   변환 전: 매치 개수 assert(기대 1개인데 3개면 중단 — 실제로 오배치를 막은 사례 있음), 치환 대상 자기검증 케이스.\
   변환 후: 조각이 다른 조각을 침범했는지, 행수·페이지 수 같은 지표가 이전과 비교해 이상한지(0건·과다), 실제 원문 샘플을 열어 대조.

## 문제 구조 (추상화 코드)

### 변형 A — 정규식 주석 마스킹 → 상태 스캐너

```ts
// 문제: 라인 주석·문자열 속 "/*" 를 블록 주석 시작으로 오인
const masked = src.replace(/\/\*[\s\S]*?(?:\*\/|$)/g, m => " ".repeat(m.length));
```

```ts
// 고침: 상태 기계, 길이 보존 마스킹(오프셋을 원본에 그대로 사용), 문자열은 EOL에서 재동기
let state: "code" | "line" | "block" | "str" | "chr" = "code";
for (let i = 0; i < src.length; ) {
  const c = src[i], n = src[i + 1];
  if (state === "code") {
    if (c === "/" && n === "/") { state = "line"; i += 2; }
    else if (c === "/" && n === "*") { state = "block"; out[i] = out[i + 1] = " "; i += 2; }
    else { if (c === '"') state = "str"; else if (c === "'") state = "chr"; i++; }
  }
  // ... line: EOL 에서 code, block: "*/" 에서 code(내용은 공백), str/chr: 닫는 따옴표 또는 EOL
}
```
무엇이 깨졌나: 주석 안의 import 문을 실코드로 오인해 없는 오류를 표시하고, 자동 삽입이 주석 안이나 패키지 선언 앞에 들어갔다.\
같은 구조: 자동완성 인덱싱의 주석 판정 오류 → 같은 상태 스캐너로 교체.\
선택하지 않은 방법: 에디터의 구문 트리 사용 — 삽입 시점의 비용과 결합도 때문.

### 변형 B — 양끝 슬라이스로 JSON 추출

```rust
// 문제
let s = &text[text.find('{')?..=text.rfind('}')?];   // 뒤 산문의 '}' 포함

// 고침: 문자열 추적 포함 균형 스캔
let (mut depth, mut inside_quote, mut esc) = (0, false, false);
for (i, ch) in text[start..].char_indices() {
    if inside_quote { if esc { esc = false } else if ch == '\\' { esc = true } else if ch == '"' { inside_quote = false } continue; }
    match ch { '"' => inside_quote = true, '{' => depth += 1, '}' => { depth -= 1; if depth == 0 { return Some(&text[start..=start + i]); } }, _ => {} }
}
```
무엇이 깨졌나: 유효 JSON 뒤 산문에 중괄호가 있으면 파싱이 실패했다.\
관련 설계: 모델 출력은 JSON 대신 고정 마커 + 방어 파서로 받고 이탈한 항목은 건너뛰게 했다(JSON 요구는 한 번 이탈하면 전체 실패).

### 변형 C — 정규식으로 구조화 텍스트 일괄 편집

```python
# 문제: 중첩을 모르는 평면 패턴
block = re.search(r'<div class="item">.*?</div>\s*</div>', html, re.S)  # 다음 블록까지 삼킴
src = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', src)                      # "/**" 의 "**" 를 여는 표시로 오인
```

```python
# 고침: 앵커 기준 슬라이스 + 개수 assert + 구분자 먼저 떼고 알맹이만 치환
start = html.index(START_MARKER); end = html.index(NEXT_BLOCK_MARKER, start)
block = html[start:end]
matches = pattern.findall(doc); assert len(matches) == 1, len(matches)  # 오배치면 중단
body = strip_comment_delimiters(line)   # "/**", "*/" 를 먼저 분리
body = convert_bold(body)               # 자기검증 케이스 통과 후 실행
```
무엇이 깨졌나: 에러 없이 엉뚱한 범위를 바꿨다 — 한 블록이 이웃 블록을 삼킴, 목차 16개 중 1개만 매칭, 도식 생성 함수 16개가 통째로 삭제, 태그 제거가 도식 안 화살표 `<-- -->`를 태그로 보고 줄을 넘어 삼켜 코드펜스 짝이 깨짐.\
같은 구조: 원문의 raw `->`를 이스케이프된 `&gt;`로 찾아 0건 매칭.

### 변형 D — 중첩 구분자를 한 번씩 벗기기

```python
# 문제: 순서대로 한 번씩 → 안쪽 층 잔존
if s[:1] in "\"'" and s[0] == s[-1]: s = s[1:-1]
if s.startswith("(") and s.endswith(")"): s = s[1:-1]      # "( \"a b\" )" → "\"a b\"" 남음

# 고침: 깊이 추적 + 고정점까지 반복, 모든 추출 경로가 이 함수를 공유
def strip_value(s):
    while True:
        prev = s
        if len(s) >= 2 and s[0] == "(" and matching_paren(s, 0) == len(s) - 1:
            s = s[1:-1].strip()
        if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
            s = s[1:-1].strip()
        if s == prev: return s
```
무엇이 깨졌나: 괄호가 남은 값이 검색어·하이라이트에 그대로 들어가 매칭이 실패했고, 파서만 고치자 하이라이트는 별도 경로라 여전히 실패했다.\
곁가지: 공백을 OR 분리로 쓰는 문법에서 공백 포함 구문을 표현하려면 토크나이저 단계에서 구문 토큰(`'[^']*'`)을 하나로 잡아야 후속 분리 로직을 건드리지 않는다.

### 변형 E — 1단계 괄호 가정 + EOF 미검사

```python
# 문제
while tokens[i] != ")": i += 1          # 닫는 괄호가 없으면 무한 루프, 중첩 미지원

# 고침: 재귀 + EOF 검사 + 불균형이면 원문으로 degrade
def parse_expr(ts):
    node = parse_token(ts)
    while ts.peek() in ("AND", "OR"): ...
    return node
def parse_token(ts):
    if ts.peek() == "(":
        ts.next(); node = parse_expr(ts)
        if ts.at_eof(): raise Unbalanced
        ts.expect(")"); return node
try: ast = parse_expr(tokens)
except Unbalanced: ast = RawQuery(original)
```
무엇이 깨졌나: 중첩 괄호 쿼리가 파싱에 실패했고, 닫는 괄호가 없으면 무한 루프에 빠졌다.

### 변형 F — 설정 파일을 줄 단위 정규식으로

```python
# 문제: 주석 처리된 옛 설정도 매칭, 첫 매칭 채택
for line in path.read_text().splitlines():
    if m := PORT_RE.search(line): return m.group(1)

# 고침(최소): 주석 행 건너뛰기 — 근본적으로는 YAML 파서
for line in path.read_text().splitlines():
    if line.lstrip().startswith("#"): continue
    if m := PORT_RE.search(line): return m.group(1)
```
무엇이 깨졌나: 수집기가 새 클러스터가 아닌 옛 클러스터 포트를 바라봤다.

### 변형 G — 대량 추출 정규식의 과대·과소 매칭

```python
# 문제
SECTION_END = re.compile(r"^\{\{-[a-z]{2,3}-\}\}", re.M)  # 3자 기능 템플릿도 섹션 끝으로 오인 → 내용 잘림
LIST_BLOCK  = re.compile(r"((?:[#:*].*\n)+)")             # 넓은 prefix → 인접 목록까지 흡수
TEMPLATE    = "{{-nonexistent-}}"                          # 존재하지 않는 이름 → 0건
# 헤딩 없는 페이지 → 암묵적 전체-본문 fallback

# 고침: 실제 원문 샘플로 형식 확인 후 패턴을 좁히고, 암묵 fallback은 명시 옵션으로
SECTION_END = re.compile(r"^\{\{-[a-z]{2}-\}\}", re.M)    # 트레이드오프(3자 코드 불가)를 문서화
LIST_BLOCK  = re.compile(r"((?:#:\*[^\n]*\n)+)")
parse(page, body_fallback=cfg.body_fallback)
```
무엇이 깨졌나: 전체 실행이 에러 없이 끝났고, 품질 점검에서 행수만 비정상이었다(0건, 잘림, 수십 개 혼입, 3건뿐).\
고친 뒤 0건 → 5,757건, 3건 → 184건. 검증은 소형 덤프 smoke → 전체 실행 → 지표 비교 순.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
