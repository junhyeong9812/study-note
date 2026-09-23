# cs/issue/concurrency/single-slot-handoff-loss — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **첫 요청이 영원히 답을 받지 못한다.** 두 번째 요청이 state를 덮어 대화상자는 두 번째만 보여 주고, 첫 연결의 결정은 끝내 전달되지 않아 백엔드가 결정 대기에서 멈춘다(세션 hang).\
   덮어쓰기는 정상적인 state 갱신이라 예외도 로그도 없다 — 그래서 무음이다.\
   응답 의무가 있는 요청은 큐(순차 처리, 각 항목 id로 응답)나 id별 맵으로 보관해야 한다(이 사례의 백엔드 쪽 대기 맵은 id 키라 문제가 없었다).
   > **last-write-wins** — 같은 칸에 여러 쓰기가 오면 마지막 것만 남는 규칙. 칸이 요청함이면 앞선 요청의 유실이다.

2. **네 조건이 모두 필요하다.** (a) 소비자 단일화 — 같은 요청을 소비할 수 있는 컴포넌트가 하나뿐이어야 한다.\
   (b) 행동 가능해진 뒤에만 소비 — 대상 API가 아직 준비되지 않았으면 요청을 **비우지 않고 남긴다**.\
   (c) 성공 후 clear — 부작용이 성공한 뒤에 비우고, 실패하면 남겨 재시도 근거를 보존한다.\
   (d) 준비 신호를 재실행 조건에 — 준비 상태(`apiReady`)가 effect 의존성에 있어야 준비되는 순간 대기 요청이 처리된다(없으면 준비 전 도착한 요청이 영구 대기).
   > **정확히 1회(exactly-once) 전달** — 유실도 중복도 없이 한 번만 처리되는 것. "성공 후 clear"만으로는 유실이 없는 최소 1회(at-least-once)까지다 — 성공~clear 사이 재실행·재시도가 겹치면 중복이 나므로, 항목 id로 멱등 제거·중복 억제(6번)나 진행 중 표시를 함께 둬야 정확히 1회에 가까워진다.

3. **요청이 사라진다.** 먼저 비우면 부작용이 throw하는 순간 요청은 어디에도 없고, 재시도할 근거가 없다.\
   더 나쁜 경우 요청과 함께 정리할 자원(임시 세션)도 먼저 닫아 복구 자체가 불가능해졌다.\
   소비는 ACK(쓰기 성공·패널 추가 성공) 뒤로 옮기고, 대상이 점유 중이면 거부하고 원래 자원을 유지한 채 안내한다.

4. **숨김 ≠ 제외.** `visibility:hidden`은 화면에서만 빠질 뿐 컴포넌트는 마운트 상태라 스토어 구독과 effect가 계속 돈다.\
   그래서 뒤에 숨은 레이어의 소비자가 앞 레이어보다 먼저(또는 함께) 요청을 소비해, 동작이 숨은 쪽에 적용되거나 두 번 소비됐다.\
   요청을 "앞 레이어만 소비하는 뷰 요청"과 "가시성과 무관하게 소유자가 소비하는 세션 요청"으로 나누고, 게이트는 순수 함수(앞 레이어 XOR 판정)로 공유하며, 게이트가 닫힌 소비자는 clear하지 않는다(유실 ≠ 소비).

5. **하류가 1칸이면 유실은 하류에서 난다.** 상류 큐를 드레인하는 코드가 동기 연속으로 하류 슬롯에 쓰면, 하류 소비자가 읽기 전에 덮어써 결국 마지막 것만 남는다.\
   무유실은 파이프라인 전 구간의 용량 계약이다.\
   하류 슬롯을 큐로 바꿀 수 없을 때는, 드레인 판정이 "하류 점유 중이면 wait"를 돌려주고 하류 슬롯이 비는 변화를 구독(effect 의존성)해 1건씩 전달한다.\
   잔여 위험: 하류 소비자가 영영 준비되지 않으면 큐가 멈춘다 — 유실이 아니라 회복 가능한 정지다.
   > **페이싱(pacing)** — 소비 완료 신호를 기다린 뒤 다음 항목을 보내 생산 속도를 소비 속도에 맞추는 것.

6. **이중 전달 방지.** React는 커밋 후 effect를 자식 → 부모 순으로 실행하고, 훅 구독값은 렌더 시점 스냅샷이다.\
   자식의 준비 콜백이 요청을 전달·삭제한 뒤, 부모 effect는 아직 옛 스냅샷의 요청을 보고 다시 전달했다(같은 프롬프트 2회 주입).\
   항목에 고유 id를 붙이고, 전달 직전 스토어의 **최신 상태를 재조회**해 남아 있는지 확인하고, 성공 후 id로 제거(없으면 no-op)한다.\
   두 경로가 같은 드레인 함수를 공유하면 어느 쪽이 먼저 돌든 한 번만 전달된다.

7. **이전 소유자의 요청이 다음 소유자에게 배달된다.** 부 표면이 닫히거나 다른 대상으로 교체될 때 그 칸의 대기 요청을 비우지 않으면, 새 부 표면이 이전 대상의 요청을 처리한다.\
   "새로 마운트되면 처리 기록(ref)이 초기화된다"는 가정은 실제로 리마운트되는 것이 무엇인지에 달려 있다 — 부모는 유지되고 key가 바뀐 자식만 교체되면 부모의 처리 기록 ref가 남아 이전 대상의 요청을 처리할 수 있다.\
   교체·멤버십 변경 시 해당 칸을 명시적으로 비운다(값 칸은 비우도록 고쳤고, 카운터형 칸의 누출은 후속 타깃 수정으로 분류됐으며 최종 적용 결과는 기록되지 않았다).

## 문제 구조 (추상화 코드)

### 변형 A — 응답 의무 요청을 1칸에
```ts
// ① 문제
listen("confirm-prompt", e => setPrompt(e.payload));    // 두 번째가 첫 번째를 덮음 → 첫 요청자 영구 대기

// ② 고침
listen("confirm-prompt", e => setQueue(q => [...q, e.payload]));
const head = queue[0];                                   // 모달은 head만 표시
function decide(ok: boolean) { sendDecision(head.id, ok); setQueue(q => q.slice(1)); }
```
무엇이 깨졌나: 동시 요청이 앞 요청을 조용히 폐기해 응답을 기다리던 쪽이 멈췄다.

### 변형 B — 다수 생산자가 한 칸 공유
```ts
// ① 문제
type Store = { openReq: Req | null };
publish: (req) => set({ openReq: req });                 // 두 표면이 소비 전 발행 → 뒤엣것만 남음

// ② 고침
type Slots<T> = { primary: T | null; secondary: T | null };
const putSlot = <T,>(slots: Slots<T>, id: SurfaceId, v: T): Slots<T> =>
  id === "secondary" ? { primary: slots.primary, secondary: v } : { primary: v, secondary: slots.secondary };
// 소비: slots[mySurfaceId]만 읽고 비움 / 멤버십 변경 시 secondary 칸 비우기
```
무엇이 깨졌나: 공유 "최신값 칸"에서 생산자끼리 lost update가 났다.\
같은 구조: 값 없는 재발화 요청(nonce 카운터) — 부모가 유지되고 key 바뀐 자식만 교체되면 처리 기록 ref가 남아 이전 대상 요청을 처리할 수 있음(값 칸 비우기는 적용, 카운터 누출 처리 결과는 미기록).\
같은 구조: 세션 단위 요청은 표면 칸이 아니라 세션 id로 짝지음.

### 변형 C — 성공 전 소비
```ts
// ① 문제
requestOpen(null);                 // 먼저 비움
api.addPanel(req);                 // throw → 요청 소실
closeTempSession();                // ...쓰기 ACK 전에 정리 세션까지 닫음

// ② 고침
if (!api) return;                  // 준비 전 — 요청 유지 (apiReady가 deps에 있어 준비되면 재실행)
await writeTo(target, prompt);     // ACK — await 동안 effect가 재실행되면 같은 요청을 또 쓸 수 있으므로 진행 중 표시(또는 id 멱등 소비)를 함께 둔다
requestOpen(null);                 // 성공 후에만 소비
closeTempSession();
```
무엇이 깨졌나: 부작용 실패 시 재시도 근거와 복구용 자원이 이미 사라져 있었다.

### 변형 D — 소비자가 둘 (숨긴 레이어 · 교체 전 인스턴스)
```tsx
// ① 문제
useEffect(() => { if (req) { act(req); clear(); } }, [req]);   // 앞·뒤 레이어 모두 마운트 — 둘 다 실행

// ② 고침
useEffect(() => {
  if (!req || !isFront(layer)) return;          // 게이트 닫힌 소비자는 clear도 하지 않음
  if (req.project !== activeProject) return;    // 올바른 인스턴스만
  if (!handleRef.current) return;                  // 준비 전이면 유지
  act(req); clear();
}, [req, apiReady, layer, activeProject]);    // 조건에 쓰는 값은 재실행 조건에도
```
무엇이 깨졌나: 숨겼지만 마운트된 레이어, 또는 `key` 전환 직전의 이전 인스턴스가 요청을 먼저 소비했다.\
같은 구조: 호출 측이 대상 전환(비동기) 완료를 기다리지 않고 요청 → 이전 인스턴스가 소비, `await` 후 요청으로 보완.

### 변형 E — 전달 경로 둘 + 스냅샷 소비
```ts
// ① 문제
onReady = (api) => { seed(api, reqFromRender); consume(); };     // 자식 effect에서 먼저
useEffect(() => { if (reqFromRender) inject(reqFromRender); });  // 부모 effect — 옛 스냅샷으로 재전달

// ② 고침
function drain(api) {
  const head = store.getState().queue.find(r => r.owner === owner);  // 최신 상태 재조회
  if (!head) return;
  deliver(api, head.prompt);
  store.getState().consume(head.id);                                   // id로 멱등 제거
}
// onReady와 effect 모두 drain 호출
```
무엇이 깨졌나: 한 값이 두 경로로 두 번 주입됐다.

### 변형 F — 상류만 큐, 하류는 1칸
```ts
// ① 문제
for (const item of queue) setInjectSlot(item);   // 동기 연속 — 하류가 읽기 전에 덮어씀

// ② 고침
function nextAction(queue, slotOccupied) {
  const head = queue[0];
  if (!head) return { kind: "idle" };
  if (slotOccupied) return { kind: "wait" };     // 비는 변화를 구독해 재개
  return { kind: "inject", id: head.id, prompt: head.prompt };
}
```
무엇이 깨졌나: 한 구간만 큐로 바꿔 유실 지점이 하류로 옮겨 갔을 뿐이었다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
