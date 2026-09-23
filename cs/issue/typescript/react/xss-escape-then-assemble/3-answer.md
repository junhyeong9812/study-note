# cs/issue/typescript/react/xss-escape-then-assemble — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `least-privilege`

## 정답

<!-- 질문 1:1 대응 -->

1. 백엔드가 `<mark>정렬</mark>` 같은 HTML을 만들어 보내고 프론트가 그걸 화면에 그대로 꽂으면, 브라우저는 그 문자열을 **HTML로 해석**한다. 그런데 그 문자열에는 강조 태그뿐 아니라 노트 본문에서 온 내용도 섞여 있고, 본문에 `<script>…</script>`나 `<img onerror=...>` 같은 게 들어 있으면 그것도 함께 HTML로 해석돼 **실행**된다. 검색 스니펫은 사용자가 저장한 노트 내용에서 오므로, 강조를 위해 HTML을 통으로 삽입하는 순간 저장된 임의의 HTML이 실행 가능한 XSS 통로가 열린다.
   > **XSS(Cross-Site Scripting)** — 화면에 공격자가 넣은 HTML/스크립트를 심어 다른 사용자의 브라우저에서 실행시키는 공격. 신뢰할 수 없는 입력을 이스케이프 없이 HTML로 렌더하면 발생한다.

2. `dangerouslySetInnerHTML`은 이름 그대로 **위험한 통로**다. React는 평소 `{text}`로 텍스트를 넣으면 `<`·`>`·`&` 같은 특수문자를 `&lt;`·`&gt;`로 **자동 이스케이프**해 "글자 그대로" 보이게 한다 — 그래서 기본적으로 XSS가 안 난다. 그런데 `dangerouslySetInnerHTML`은 이 자동 이스케이프를 **끄고** 주어진 문자열을 날 HTML로 DOM에 삽입한다. 그러니 이 통로에 신뢰할 수 없는 문자열을 넣으면 React의 기본 방어가 무력화돼, "글자"로 보여야 할 `<script>`가 "코드"로 실행된다.
   > **이스케이프(escape)** — `<`, `>`, `&` 같은 특수문자를 화면에 글자 그대로 보이게 치환하는 것(`<`→`&lt;`). 이스케이프된 문자열은 HTML로 해석되지 않아 스크립트가 실행되지 않는다.

3. 마커 방식에서 본문에 `<script>`가 있으면, 프론트는 그 텍스트를 통째로 이스케이프해 React 텍스트로 넣으므로 화면에는 **`<script>`라는 글자 그대로** 보이고 실행되지 않는다. 실행되지 않는 이유는, 프론트가 HTML 문자열을 만들어 삽입하는 게 아니라 **React 요소 배열을 조립**하기 때문이다 — 일반 조각은 텍스트 노드(자동 이스케이프), 마커 안 조각만 우리가 만든 `<mark>` 요소. HTML을 파싱하는 단계가 없으니 본문의 `<script>`는 그냥 문자 데이터일 뿐이다. 이스케이프를 우회할 길 자체가 코드 경로에 없다.

4. 일반 원칙: **"신뢰할 수 없는 텍스트는 먼저 전부 무력화(escape)하고, 신뢰할 수 있는 구조(강조)만 나중에 얹는다(assemble)."** 이 순서를 뒤집으면 안전이 깨진다 — assemble을 먼저 하면(HTML로 강조를 조립한 뒤 넣으면) 그 시점엔 이미 신뢰 못 할 본문과 강조가 한 HTML 문자열에 섞여, 나중에 이스케이프하려 해도 강조 태그까지 이스케이프되거나(강조가 글자로 보임) 아예 이스케이프를 못 하고 통째로 실행된다. escape가 먼저여야 "무력화된 텍스트 위에 통제된 구조만 얹는" 불변식이 성립한다.
   > **출력 이스케이프(output escaping)** — 데이터를 출력 맥락(HTML)에 넣기 직전에 그 맥락에서 위험한 문자를 무력화하는 것. XSS의 1차 방어선이며, "조립보다 먼저"가 순서 규칙이다.

5. 마커 문자열은 **일반 입력으로는 나오지 않는 문자**여야 한다(여기선 `⟦ ⟧` 같은 특수 괄호). 그래야 "마커 = 강조 경계"라는 해석이 본문 텍스트와 충돌하지 않는다. 만약 본문에 우연히/악의로 `⟦m⟧`가 들어 있으면 프론트가 그걸 강조 경계로 오해해 **엉뚱한 강조**가 생길 수 있다. 그러나 결정적으로 — 그 경우에도 조각들은 여전히 텍스트로 이스케이프되므로 **HTML 실행 위험은 없다.** 최악의 결과가 "잘못된 강조 표시"지 "코드 실행"이 아니라는 점이 이 설계의 안전 여유다. 그래서 마커는 "충돌 가능성이 실질적으로 0에 가까운 희귀 문자"를 고르는 것으로 충분하다.

6. 강조는 백엔드와 프론트가 걸쳐 있는 **프로토콜**이고, 책임 분담은: 백엔드는 검색엔진 highlight의 `pre_tags`/`post_tags`를 `⟦m⟧`/`⟦/m⟧`로 지정해 "어디가 일치인가"만 마커로 표시한다(**HTML을 만들지 않는다**). 프론트는 그 마커 텍스트를 받아 이스케이프 후 마커→`<mark>`로 조립한다. 백엔드가 HTML을 만들지 않는 게 핵심인 이유는, 만약 백엔드가 `<mark>`를 만들어 보내면 프론트는 그 신뢰를 검증할 수 없어 결국 HTML을 통으로 삽입해야 하고, 그 순간 위 1번의 XSS로 돌아가기 때문이다. "강조 표시는 데이터(마커)로 전달하고, HTML 구조 생성은 오직 출력하는 쪽에서"가 이 프로토콜의 규칙이다.

7. 디바운스는 XSS(정확성)와 다른 축인 **부하/성능**의 방어다. 자동완성은 사용자가 검색창에 글자를 칠 때마다 호출될 수 있어, 그대로 두면 타자 한 글자마다 요청이 쏟아져 백엔드와 검색엔진에 부담을 주고 화면도 버벅인다. 디바운스는 "입력이 멈추고 200ms 지난 뒤에만 요청"해 요청 수를 줄인다. 두 방어가 한 기능에 함께 필요한 이유는, 자동완성이 **신뢰할 수 없는 사용자 입력을 실시간으로 처리**하는 기능이기 때문이다 — 입력의 내용은 XSS로(이스케이프+조립), 입력의 빈도는 부하로(디바운스) 각각 방어해야 안전하고도 쓸 만해진다.
   > **디바운스(debounce)** — 연속으로 발생하는 이벤트(타자 입력 등)에서 마지막 이벤트 후 일정 시간이 지나야 한 번만 처리하는 기법. 요청 폭주를 막는다.

## 문제 구조 (추상화 코드)

### 변형 A — 백엔드가 만든 강조 HTML을 그대로 삽입
① 문제 코드 (설계 단계에서 선택하지 않은 방법)
```ts
// backend: 검색엔진 highlight 기본 태그
highlight: { fields: { body: {} }, pre_tags: ["<mark>"], post_tags: ["</mark>"] }
```
```tsx
// front: 본문과 강조가 섞인 HTML 문자열을 날로 삽입
<span dangerouslySetInnerHTML={{ __html: hit.snippet }} />
```
② 고친 코드
```ts
// backend: HTML이 아닌, 일반 입력에 안 나올 마커만 표시
highlight: { fields: { body: {} }, pre_tags: ["⟦m⟧"], post_tags: ["⟦/m⟧"] }
```
```tsx
// front: 텍스트는 React가 이스케이프, 마커 안만 <mark> 요소로 조립
export function renderHighlighted(text: string) {
  return text.split("⟦m⟧").flatMap((part, i) => {
    if (i === 0) return [part];
    const [marked, rest] = part.split("⟦/m⟧");
    return [<mark key={i}>{marked}</mark>, rest];
  });
}
// 입력은 200ms 디바운스 후 요청
useEffect(() => { const t = setTimeout(() => fetchSuggest(q), 200); return () => clearTimeout(t); }, [q]);
```
무엇이 깨졌나: 강조(신뢰)와 본문(비신뢰)이 한 HTML 문자열로 합쳐진 뒤 삽입돼, 본문의 마크업까지 실행 대상이 됐다.

### 변형 B — 템플릿 문자열 조립 시 외부 값 미이스케이프 (서버 측 HTML 메일)
① 문제 코드
```java
html = template.replace("{{title}}", legacy.getTitle())      // 외부 유래 텍스트 그대로
               .replace("{{link}}", legacy.getServiceUrl());
```
② 고친 코드
```java
html = template.replace("{{title}}", escapeHtml(orDash(legacy.getTitle())))   // 모든 삽입값 이스케이프
               .replace("{{link}}", escapeHtml(orDash(legacy.getServiceUrl())));
// 계약 테스트: 실제 템플릿을 렌더해 placeholder 목록 ↔ 치환 키 목록이 1:1인지 확인
```
무엇이 깨졌나: 조립 지점마다 이스케이프를 기억해야 하는 구조에서 일부 삽입값이 빠졌다.

### 변형 C — 저장된 값을 innerHTML로 결합 (stored XSS)
① 문제 코드
```js
list.innerHTML = history.map(h => `<li>${h.sha} ${h.branch}</li>`).join("");   // 저장값이 렌더 시 마크업
```
② 고친 코드
```js
list.innerHTML = "";                         // innerHTML은 비우기에만
for (const h of history) {
  const li = document.createElement("li");
  li.textContent = `${h.sha} ${h.branch}`;   // 데이터는 전부 textContent
  list.appendChild(li);
}
```
무엇이 깨졌나: 저장 시점의 입력이 렌더 시점에 HTML로 해석됐다.

## 검증 기록
- 2026-09-23: 출처 원문 대조(Claude 초안) — 근거는 작업 log
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log (B2 전환·신규 멤버 추가)

## 방안 비교

기본 방안(위 변형 A~C)은 "신뢰 불가 텍스트를 전부 이스케이프(또는 텍스트 노드로 삽입)하고 우리가 통제하는 마커·요소만 조립한다"이다.\
같은 원리(신뢰 불가 텍스트가 HTML·스크립트 위치에 들어가면 XSS)에 다른 방안이 쓰인 사례:

### 방안 1 — HTML이 필요한 입력(마크다운)은 sanitizer + 원격 리소스 태그 금지
```tsx
// 문제: 마크다운 파서는 변환기일 뿐 정화기가 아니다 → raw HTML이 그대로 통과
setHtml(markdownParse(text));                                   // + dangerouslySetInnerHTML
// 고친
setHtml(sanitize(markdownParse(text)));                         // 파싱 후 sanitizer
setHtml(sanitize(markdownParse(text), { FORBID_TAGS: ["img", "video", "iframe" /* ... */] }));
// 도구 출력 뷰: 기본 허용 태그라도 원격 리소스 자동 로드(추적·유출)를 막는다
// 선택지 본문처럼 서식이 필요 없는 곳은 React 텍스트 노드로만 렌더
```
남은 확인점: 링크 scheme(`javascript:`) 처리 충분성.

### 방안 2 — 렌더러 통합 시 sanitize 정책을 파라미터로 드러냄
```tsx
// 문제: 겉보기 같은 두 렌더러가 다른 정책(원격 미디어 차단 / 허용)을 담고 있었다
//       → 한쪽으로 "중복 제거"하면 다른 쪽 이미지가 에러 없이 사라진다
// 고친: 정책을 순수 함수의 인자로
export function sanitizeMarkdown(text: string, blockMedia: boolean): string {
  const parsed = markdownParse(text);
  return blockMedia ? sanitize(parsed, { FORBID_TAGS: MEDIA_TAGS }) : sanitize(parsed);
}
<Markdown blockMedia />            // 외부 유래 출력 뷰 = true, 로컬 문서 뷰어 = false
// fetch·로딩·에러는 호출부에 유지 → 정책 단위 테스트를 DOM 없이
// 부수: 비마크다운 파일을 마크다운으로 렌더하던 fallback에 경로 가드 추가
```

### 방안 3 — `<script>` 안에 싣는 데이터는 JSON 데이터 채널 + textContent
```rust
// 문제: 신뢰 불가 텍스트가 인라인 <script> 안에 들어가면 "</script>"로 요소를 닫고 탈출
// 고친: 직렬화 후 '<'를 JSON·JS 양쪽에서 같은 문자로 복원되는 이스케이프로
let json = to_json(data).unwrap_or_else(|_| "null".into())
    .replace('<', "\\u003c")
    .replace('\u{2028}', "\\u2028")      // 구형 JS 엔진에서 문자열 리터럴을 깨는 줄 구분자
    .replace('\u{2029}', "\\u2029");
// 내장 렌더러는 createElement + textContent 전용, 유일한 HTML 슬롯(제목)만 html_escape
// 테스트: 페이로드 부재 검증과 페이로드 실재 검증을 쌍으로
```
선택하지 않은 방법: 서버측에서 삽입 위치마다 이스케이프해 조립 — 누락 지점이 많다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 전체 이스케이프 후 마커·요소 조립 | 서식이 필요 없거나, 필요한 구조가 소수(강조)다 | 마커 프로토콜 합의 | 마커 충돌 시 잘못된 강조(실행은 없음) · 조립 지점이 흩어지면 누락 | 검색 강조·목록·템플릿 치환 |
| 1. sanitizer + 태그 금지 | 입력이 HTML 서식을 가져야 한다(마크다운) | 라이브러리 의존·정책 설정 | 기본 허용 태그의 원격 로드 · 링크 scheme 처리 | 사용자·모델이 쓴 마크다운 렌더 |
| 2. 정책 파라미터화 | 출처별로 정책이 달라야 한다 | 호출부마다 정책 선택 | 기본값을 잘못 고르면 조용한 동작 변화 | 여러 뷰가 한 렌더러를 공유할 때 |
| 3. JSON 데이터 채널 + textContent | 데이터를 스크립트와 함께 한 파일에 실어야 한다 | 직렬화 이스케이프·DOM API 렌더러 | `<`·줄 구분자 이스케이프 누락 | 자기완결 HTML·인라인 부트스트랩 데이터 |

**결론**: 서식이 필요 없으면 **텍스트 노드로 넣고 통제된 구조만 조립**하는 기본 방안이 실행 경로 자체를 없애므로 가장 단단하다.\
HTML 서식이 입력의 일부면(마크다운) sanitizer가 필요하고, 그 정책(원격 리소스 허용 여부)은 출처마다 다르므로 **파라미터로 드러내야** 통합 때 조용히 바뀌지 않는다(1·2).\
데이터가 `<script>` 안에 들어가야 하면 마크업 위치가 아니라 **이스케이프된 데이터 채널**로 싣고 DOM API로 붙인다(3).
