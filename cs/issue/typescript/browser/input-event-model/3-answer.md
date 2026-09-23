# cs/issue/typescript/browser/input-event-model — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **두 경로로 오는 조합 텍스트.** 해당 웹뷰 엔진에서 한글은 음절마다 `compositionend`가 따로 발생하고, 그 시점엔 이미 `composing=false`다.\
그 뒤 터미널 라이브러리가 같은 음절(또는 누적 문자열)을 `onData`로 다시 흘려, 조합 확정 텍스트와 데이터 이벤트가 이중으로 전송됐다.\
composing 플래그로 onData를 막는 가설은, onData가 도착할 때 플래그가 이미 false라 막을 게 없어 실패했다.\
해결: 조합 텍스트는 `compositionend.data`로 한 번만 보내고, `onData`에서 비ASCII(멀티바이트) 데이터는 버린다 — 이 앱에서 IME 밖 키 입력의 onData는 ASCII·제어문자뿐이라는 가정에 기댄 것이다(비ASCII를 직접 내는 자판 배열·dead key 입력이 있는 환경이면 성립하지 않는다).\
결정타는 추측이 아니라 dev 콘솔로 이벤트 순서를 계측한 것이었다. 남은 한계: 비ASCII 붙여넣기도 함께 버려진다.
   > **IME 조합(composition)** — 입력기가 여러 키 입력을 모아 한 글자를 만드는 과정. 확정 전의 미완성 텍스트를 preedit이라 한다.

2. **조합 중 덮어쓰기.** `input` 이벤트는 compositionstart~end 사이에도 매 키마다 발생한다.\
그때 value를 잘라 다시 쓰면 입력기의 조합 상태가 파괴되어 글자가 강제 확정되거나 깨진다.\
조합 중(ref 플래그)에는 자르지 않고(카운트만 하고 state에는 원값 그대로 반영 — React controlled 입력은 state를 갱신하지 않으면 DOM 값을 이전 state로 되돌려 역시 조합을 깨뜨린다), `compositionEnd`에서 절삭·동기화를 한다.\
(compositionend와 마지막 input의 순서는 브라우저마다 다를 수 있으므로 양쪽 경로 모두 "조합 중이 아니면 절삭"으로 수렴시킨다.)

3. **"처리됨" ≠ 전파 차단.** 라이브러리 핸들러의 `return false`는 **라이브러리 내부의** 기본 처리(PTY로 보내기 등)만 막는다 — DOM 이벤트는 그대로 버블된다.\
`preventDefault()`는 브라우저 기본 동작만, `stopPropagation()`은 상위로의 전파만 막는다 — 서로 대체되지 않는다.\
그래서 둘 다 호출한 뒤 `return false`를 한다.\
반대로 의도적인 2단 Esc(안쪽이 먼저 닫힘)는 `stopPropagation`으로 상위 Esc를 한 단계 삼켜 구현한다.

4. **modifier 미검사.** `e.key === "v"`만 보면 Ctrl+V도 `v`다 — 토글이 붙여넣기를 삼킨다.\
단축키는 `!ctrl && !meta && !alt` 가드를 둔다.\
같은 부류: 코드블록의 가로 스크롤이 Ctrl+←/→까지 받아 패널 이동과 **둘 다** 실행됐다 → 가로 스크롤은 modifier 없을 때만, Ctrl+화살표는 패널 이동 전용.\
공유 스크롤 헬퍼는 onKeyDown의 **마지막 분기**에 두고, 처리하지 않은 키에는 preventDefault를 부르지 않는 계약으로 고정했다.

5. **포커스 소유권.** 키보드 탐색은 "지금 누가 포커스를 쥐는가"라는 단일 사실에 의존한다.\
자식이 열리면서 포커스를 가져가면 사이드바의 키 입력이 자식으로 가고, 포커스된 요소가 사라지면 포커스는 body로 떨어져 컴포넌트에 붙은 키 핸들러는 아무것도 받지 못한다(document·window 수준 리스너만 받는다).\
교정: 자식 자동 포커스를 없애고 사이드바가 스스로 포커스를 유지, 닫을 때 목록으로 명시적으로 포커스 이양.\
setState 직후에는 새 DOM이 아직 없어 focus()가 효과가 없으므로 `requestAnimationFrame` 뒤에 했다 — rAF는 흔한 우회일 뿐 커밋 이후를 보장하지는 않으므로, 커밋 뒤 실행되는 `useEffect`·ref 콜백에서 focus하는 쪽이 더 확실하다.
   > **포커스 소유권** — 키보드 이벤트를 받는 요소는 한순간 하나뿐이다. 그 하나를 누가 정하는지가 명확해야 탐색이 끊기지 않는다.

6. **drop 없는 종료.** Esc로 취소, 창 밖에서 놓기, 다른 드롭 대상이 먼저 소비 — 이때 `drop`은 이 요소에 오지 않는다.\
dragleave/drop 두 경로에서만 정리하면 하이라이트가 남는다.\
dragleave는 자식 경계를 넘을 때마다 발생하고, 일부 엔진은 `relatedTarget`을 null로 줘 "진짜 떠남"을 판별할 수 없어 60Hz로 깜빡였다.\
`dragover`에서 `preventDefault()`를 빼면 브라우저는 그 요소를 드롭 불가로 보고 `drop`을 아예 발생시키지 않는다 — 기본값이 "거부"이고 기본 동작을 취소하는 것이 "드롭 대상" 신호다.

7. **계층을 먼저 가른다.** 이벤트 계층 교정은 "이벤트가 오긴 오는데 순서·경로·전파가 가정과 다르다"를 다루고, 환경 계층 교정은 "이벤트를 만들 입력기 자체가 연결되지 않았다"를 다룬다.\
한글이 **아예** 안 되면 환경(입력기 데몬·IM 모듈 설정) → 입력은 되는데 **중복·깨짐**이면 이벤트 경로 순으로 의심한다.\
환경 보정을 제거해 보는 실험에서 한글이 아예 안 되자, 그 보정이 필수이고 중복 문제는 별개 계층임이 확인됐다.

## 문제 구조 (추상화 코드)

### 변형 A — IME 조합 텍스트를 두 경로로 소비
① 문제 코드
```ts
term.onData(d => send(d));        // compositionend 뒤에도 같은 음절(누적)이 onData로 옴
// 계측: compositionend "로" → onData "로", onData "로" / compositionend "젝" → onData "젝", onData "로젝"
```
② 고친 코드
```ts
term.textarea.addEventListener("compositionend", e => send(e.data));   // 조합 텍스트는 여기서 1회
term.onData(d => {
  if (/[^\x00-\x7F]/.test(d)) return;                                  // 비ASCII는 버림
  send(d);
});
```
무엇이 깨졌나: 조합 확정 텍스트가 두 이벤트 경로로 모두 전송됐다.

### 변형 B — 조합 중 controlled value 덮어쓰기
① 문제 코드
```tsx
<textarea value={v} onInput={e => setV(truncateBytes(e.currentTarget.value, MAX))} />
// 조합 중에도 매 키 절삭 → preedit 파괴
```
② 고친 코드
```tsx
const composing = useRef(false);
<textarea value={v}
  onCompositionStart={() => { composing.current = true; }}
  onCompositionEnd={e => { composing.current = false; setV(truncateBytes(e.currentTarget.value, MAX)); }}
  onInput={e => {
    const raw = e.currentTarget.value;
    setV(composing.current ? raw : truncateBytes(raw, MAX));   // 조합 중엔 원값 반영(카운트만) — 미반영 시 React가 DOM 값을 되돌림
  }} />
```
무엇이 깨졌나: 입력기가 소유한 조합 버퍼를 프로그램이 덮어썼다.

### 변형 C — 라이브러리 "처리됨"과 DOM 전파의 혼동, modifier 미검사
① 문제 코드
```ts
term.attachCustomKeyEventHandler(e => {
  if (e.ctrlKey && e.key === "ArrowRight") { navPane(1); return false; }   // 상위 keydown도 또 실행
  return true;
});
function onKeyDown(e: KeyboardEvent) { if (e.key === "v") toggle(); }     // Ctrl+V 삼킴
```
② 고친 코드
```ts
term.attachCustomKeyEventHandler(e => {
  if (e.type === "keydown" && e.ctrlKey && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
    e.preventDefault(); e.stopPropagation();
    navPane(e.key === "ArrowRight" ? 1 : -1);
    return false;
  }
  return true;
});
function onKeyDown(e: KeyboardEvent) {
  if (e.key === "v" && !e.ctrlKey && !e.metaKey && !e.altKey) { toggle(); return; }
  // ... 고유 키
  if (handleScrollKey(e, scroller)) return;     // 마지막 분기, 미처리 키엔 preventDefault 안 함
}
```
무엇이 깨졌나: 반환값·기본 동작·전파가 서로 다른 스위치라는 점, 키 판정에 modifier가 포함된다는 점을 놓쳤다.

### 변형 D — 포커스 소유권 분열
① 문제 코드
```ts
openPeek(path);                       // 자식이 자동 focus → 사이드바 ↑↓ 멈춤
closeViewer();                        // 포커스된 요소 제거 → body로 떨어짐
setPeekFile(path); peekEl?.focus();   // 아직 렌더 전 → 무효
```
② 고친 코드
```ts
openPeek(path);                                                    // 렌더만, 포커스는 사이드바가 유지
closeViewer(); listEl.focus();                                     // 닫을 때 명시 이양
setPeekFile(path);
requestAnimationFrame(() => document.querySelector<HTMLElement>(".peek")?.focus());
```
무엇이 깨졌나: 여러 컴포넌트가 포커스를 각자 옮기거나 방치했다.\
같은 구조: `role="menu"` 포털 메뉴 — 포털이 DOM 순서를 바꿔 Tab이 다음 툴바로 새고, 열 때 첫 항목 포커스·닫을 때 트리거 복원·비활성 항목 건너뛰기를 직접 구현해야 했다(키보드 계약 테스트로 고정).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~D)은 "이벤트 핸들러 안에서 경로·시점·전파를 바로잡는다"이다. 같은 원리(입력 이벤트가 가정과 다르게 흐름)에 다른 방안이 쓰인 사례:

### 방안 1 — 환경 계층 정합: 실제 입력기 데몬에 IM 모듈 설정을 맞춤
```text
문제: IM_MODULE=fcitx 인데 실제 실행 중인 입력기 데몬은 ibus
      → GTK가 설정이 가리키는(떠 있지 않은) 모듈에 연결 → 조합 입력 불가 (영어는 됨)
고친: 앱 시작 시(GUI 툴킷 init 전) 프로세스 목록에서 실행 중인 데몬을 감지
      → 우리 프로세스의 env만 보정 (시스템 설정은 건드리지 않음)
```

### 방안 2 — DnD 생명주기를 창 단위 백스톱으로 정리
```ts
// 문제: 정리 경로가 로컬 dragleave/drop 둘뿐, dragleave 즉시 클리어, 렌더 state로 드롭 판정
el.addEventListener("dragleave", () => clearHighlight());         // 자식 경계마다 튐 → 깜빡임
// 고친
useEffect(() => {
  const end = () => clearHighlight();
  window.addEventListener("dragend", end, true);                   // capture 백스톱: Esc·창 밖·타 타깃 소비
                                                                   // (페이지 안에서 시작한 드래그 한정 — OS에서 들어온 파일 드래그는 dragend가 오지 않음)
  window.addEventListener("drop", end, true);
  return () => { window.removeEventListener("dragend", end, true); window.removeEventListener("drop", end, true); };
}, []);
el.addEventListener("dragleave", () => { timer = setTimeout(clearHighlight, 120); });
el.addEventListener("dragover", e => {
  e.preventDefault(); e.dataTransfer!.dropEffect = "move";        // 필수: 없으면 drop 미발생
  clearTimeout(timer);
});
el.addEventListener("drop", e => { const zone = zoneAt(e.clientX, e.clientY); /* 드롭 시점 좌표로 재계산 */ });
// 드래그 데이터는 전용 MIME + JSON 문자열(setData는 객체 불가), 파싱 실패는 무시
```
같은 구조: 행 전체를 `draggable`로 두면 내부 버튼 클릭이 침식되고, dragstart의 target은 항상 draggable 행이라 어느 자식에서 시작했는지 모른다 → mousedown 캡처로 원점을 기록해 버튼 위 드래그를 차단.\
같은 구조: 기존에 하드닝된 드롭존 훅을 인라인 복제하면서 가드를 누락해 같은 결함이 재발 — 동형 포팅으로 복구.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 핸들러에서 경로·시점·전파 교정 | 이벤트는 오지만 순서·경로가 가정과 다르다 | 이벤트별 가드 | 엔진마다 순서가 달라 계측 없이는 추측 | IME 중복·깨짐, 키 이중 실행, 포커스 끊김 |
| 1. 환경 정합 | 이벤트를 만들 입력기 연결 자체가 없다 | 시작 시 감지 코드 | 새 입력기 종류는 감지 목록에 추가 필요 | 조합이 아예 안 될 때 (특정 OS·툴킷) |
| 2. 창 단위 백스톱 | 종료 이벤트가 로컬 요소에 보장되지 않는다 | 전역 리스너 관리 | 다른 DnD와 섞이면 오정리 → 전용 MIME으로 격리 | 드래그·모달처럼 여러 방식으로 끝나는 상호작용 |

**결론**: 입력이 **아예 없으면** 환경 계층(1)을, **오긴 오는데 이상하면** 이벤트 계층(기본)을 먼저 본다.\
종료 방식이 여러 개인 상호작용은 로컬 이벤트로 정리를 보장할 수 없으므로 창 단위 백스톱(2)을 기본 장치로 둔다.\
어느 경우든 추측이 반복 실패하면 이벤트 순서를 계측해 사실부터 확정한다.
