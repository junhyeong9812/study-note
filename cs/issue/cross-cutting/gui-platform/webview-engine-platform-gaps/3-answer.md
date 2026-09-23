# cs/issue/gui-platform/webview-engine-platform-gaps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **① 네이티브 셸이 드래그를 먼저 가로챈다 ② 엔진이 `dataTransfer`가 채워져야 드래그로 승격한다.**\
   사용한 데스크톱 셸은 기본값으로 OS 파일 드래그앤드롭을 네이티브에서 처리하도록 가로채, 웹뷰 DOM의 DnD 이벤트를 삼켰다(셸마다 기본값이 다르다).\
   또 관측된 웹뷰 엔진(리눅스 계열 WebKit)은 `dragstart`에서 `dataTransfer.setData(...)`가 호출돼야 실제 드래그로 시작했다 — 크로미엄은 종종 그냥 동작해 엔진·버전마다 결과가 다르다.\
   두 조건이 모두 있어야 동작했다: 창 설정에서 네이티브 가로채기 끄기 + `setData` 호출.\
   포인터 이벤트로 드래그를 직접 구현하는 안은 과설계라 선택하지 않았다.

2. **파일 드롭 전용 보조 창을 따로 연다.**\
   셸이 창 단위로 "네이티브 드롭 vs DOM 드래그"를 택일하게 설계돼 있어, 네이티브 드롭을 켜면 그 창의 DOM 드래그(탭 도킹 등 라이브러리 내부 DnD)가 통째로 꺼진다.\
   그래서 메인 창은 끄고, 런타임에 만든 보조 창만 켜서 OS 파일을 받는다.\
   메인 영역에는 드래그 타입이 `Files`일 때만 `preventDefault`하는 전역 가드를 두어, 떨어진 파일로 웹뷰가 이동하는 것을 막는다.

3. **소스 창이 판정해 IPC로 알리고, `dragend` 좌표는 믿지 않는다.**\
   이 셸·엔진 조합에서는 드래그 이벤트가 시작한 문서 밖으로 전달되지 않아 다른 웹뷰가 `dragover`를 한 번도 받지 못했다(관측).\
   일반 브라우저에서는 HTML5 DnD가 OS 드래그 세션 위에서 돌아 다른 창·앱에도 `dragover`/`drop`이 전달되므로, 이는 표준이 아니라 대상 엔진·셸 설정(네이티브 드롭 끔 등)에 따른 결과다.\
   소스가 커서 밑 창을 판정해 **대상이 바뀔 때만** "드롭 대상" 메시지를 보내고, 대상 창이 스스로 강조한다(창 bounds는 드래그 시작 때 한 번 저장해 이동마다 IPC가 나가지 않게).\
   창 밖 드롭의 `dragend` 좌표는 (0,0)이나 NaN으로 올 수 있어, 유한값이면서 (0,0)이 아닌지 검사하고 추적한 마지막 유효점으로 대체한다.\
   주의: `dragover`는 커서가 소스 문서 위에 있을 때만 발생한다 — 창 밖 추적은 소스 요소의 `drag` 이벤트(엔진에 따라 좌표 0일 수 있음)나 OS 커서 조회로 보강해야 한다.
   > **역채널(back-channel) IPC** — 이벤트가 닿지 않는 쪽에 별도 프로세스 간 메시지로 상태를 전하는 것.

4. **아니다 — 나열 순서는 z-order가 아니다.**\
   이식 가능한 z-order 조회 API가 없어 휴리스틱을 단계적으로 고쳤다.\
   첫 매치: 목록 순서라 가려진 창이 뽑혔다.\
   최소 면적: 겹치면 작은 창을 고르는 규칙 — 여전히 실제 쌓임 순서는 보지 않는다.\
   숨김/최소화 제외: 안 보이는 창이 뽑히던 것을 막았다.\
   focus 최근성: 창이 focus될 때마다 전역으로 알리고 모든 창이 공유 순서를 유지해 "가장 최근 focus = 위"로 판정한다(관측 안 된 창은 최하위, 동률이면 면적).\
   OS별 창 트리 질의는 플랫폼 종속·취약해 선택하지 않은 방법이 됐다.

5. **엔진이 브라우저의 내장 PDF 뷰어를 보장하지 않기 때문이다.**\
   iframe PDF 표시는 브라우저(UA)가 내장 뷰어를 갖췄을 때의 선택 기능이다 — HTML 표준도 인라인 PDF 표시를 UA 재량으로 두고 지원 여부를 `navigator.pdfViewerEnabled`로 노출한다(일반론 — 원 기록은 "해당 엔진에서 iframe PDF 불가"까지만). 해당 웹뷰 엔진은 렌더하지 못했다.\
   엔진 무관하게: JS PDF 렌더러로 페이지별 canvas에 그린다.\
   같은 부류로, 바이너리 파일을 텍스트 읽기 경로에 넣으면 (엄격한 UTF-8 디코딩 API라면) 오류가 나고, 느슨한 API라면 깨진 문자열이 된다 — 확장자로 판별해 읽기 시도 없이 안내한다(확장자는 근사 판별이다).

6. **플랫폼 동작을 "가정"이 아니라 "검증 대상"으로 표시한다.**\
   브라우저에서 되는 것 ≠ 웹뷰에서 되는 것.\
   설계에 "이 동작은 대상 엔진 GUI 스모크로 확인"을 명시하고(예: 네이티브 드롭을 끈 창에서 DOM drop이 파일 목록을 주는가), 확인 전에는 그 위에 쌓지 않는다.\
   휴리스틱처럼 근사로 해결한 부분은 한계를 함께 적는다.

## 문제 구조 (추상화 코드)

### 변형 A — 네이티브 가로채기 + 승격 조건
① 문제 코드
```ts
// 창 설정: 네이티브 파일 드롭 기본값 ON
<Tab draggable onDragStart={() => setDragged(id)} onDrop={reorder} />
```
② 고친 코드
```ts
// 창 설정: { nativeDragDrop: false }
<Tab draggable onDragStart={(e) => {
  setDragged(id);
  e.dataTransfer.setData("text/plain", id);   // 엔진이 드래그로 승격하는 조건
  e.dataTransfer.effectAllowed = "move";
}} onDrop={reorder} />
```
깨진 것: 셸이 이벤트를 삼켰고, 엔진은 빈 dataTransfer를 드래그로 인정하지 않았다.

### 변형 B — 네이티브 드롭과 DOM 드래그의 창 단위 택일
① 문제 코드
```ts
// 메인 창: nativeDragDrop: true  → OS 파일은 받지만 탭 도킹 DnD 전부 꺼짐
```
② 고친 코드
```ts
// 메인 창: nativeDragDrop: false (DOM DnD 유지)
openWindow("dropzone", { nativeDragDrop: true });   // 파일 수신 전용 보조 창
const isFileDrag = (e: DragEvent) => !!e.dataTransfer?.types.includes("Files");
const guard = (e: DragEvent) => { if (isFileDrag(e)) e.preventDefault(); };
window.addEventListener("dragover", guard);
window.addEventListener("drop", guard);            // 웹뷰 navigate 차단
```
깨진 것: 한 창에서 두 드롭 모델을 동시에 쓸 수 없었다.

### 변형 C — 문서 경계를 못 넘는 드래그 + 망가진 좌표
① 문제 코드
```ts
// 대상 창
onDragOver(e) { showDropIndicator(); }   // 다른 창에서 시작한 드래그면 호출 0회
// 소스 창
onDragEnd(e) { route(e.screenX, e.screenY); }   // 창 밖이면 (0,0)/NaN
```
② 고친 코드
```ts
// 소스 창
onDragStart() { boundsSnapshot = allWindowBounds(); }
onDragOver(e) {                    // 소스 문서 위에서만 발생 — 창 밖은 drag 이벤트·OS 커서 조회로 보강
  last = { x: e.screenX, y: e.screenY };
  const t = pickWindow(boundsSnapshot, last);
  if (t !== current) { current = t; ipc.emit("drop-target", t); }   // 바뀔 때만
}
onDragEnd(e) {
  const p = isValidPoint(e) ? { x: e.screenX, y: e.screenY } : last;   // 유한값 + (0,0) 아님
  ipc.emit("drop-end"); route(p);
}
// 대상 창: ipc.on("drop-target", id => highlight(id === self));
```
깨진 것: 이벤트는 시작 문서에만 흐르고, 창 밖 dragend 좌표는 신뢰할 수 없었다.

### 변형 D — z-order 조회 API 부재
① 문제 코드
```ts
const target = windows.find(w => contains(w.bounds, p));   // 목록 순서 = z-order 가정
```
② 고친 코드
```ts
function pickWindow(ws, p) {
  let best = null;
  for (const w of ws) {
    if (w.hidden || w.minimized || !contains(w.bounds, p)) continue;
    const rank = focusOrder.indexOf(w.id); const r = rank < 0 ? Infinity : rank;
    const area = w.bounds.w * w.bounds.h;
    if (!best || r < best.rank || (r === best.rank && area < best.area)) best = { w, rank: r, area };
  }
  return best?.w;
}
// 각 창: onFocus → ipc.emit("window-focused", id); 수신 측은 상태만 갱신(재방송 없음)
```
깨진 것: 나열 순서를 쌓임 순서로 오인했다.

### 변형 E — 내장 뷰어·텍스트 경로 가정
① 문제 코드
```tsx
<iframe src={fileUrl} />        // PDF: 엔진에 내장 뷰어 없음
<TextViewer text={readText(path)} />   // 바이너리도 텍스트로 읽음 → I/O 에러
```
② 고친 코드
```tsx
if (isPdf(path)) return <PdfCanvas pages={renderWithJsPdfLib(path)} />;
if (isBinaryExt(path)) return <Notice>미리보기를 지원하지 않는 형식</Notice>;
return <TextViewer text={readText(path)} />;
```
깨진 것: 크롬의 내장 기능과 "모든 파일은 텍스트" 가정이 대상 엔진에서 성립하지 않았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
