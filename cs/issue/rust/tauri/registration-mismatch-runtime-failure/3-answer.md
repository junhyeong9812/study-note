# cs/issue/rust/tauri/registration-mismatch-runtime-failure — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **무음 사망의 두 원인.** 정적 capability는 빌드 시 바이너리에 박히는 ACL이라, 선언되지 않은 plugin 커맨드는 사용자에게 묻는 절차 없이 **그냥 거부(throw)**된다.\
창 좌표로 대상 창을 찾는 함수가 창 열거·가시성·최소화 조회에서 throw하자, 그 함수를 쓰는 드롭 처리 전체가 fallback까지 포함해 실패했다.\
예외가 사용자에게 표시되는 경로가 없었으므로 결과는 "에러"가 아니라 "기능이 없는 것처럼 보임"이었다.
   > **capability(정적 ACL)** — 어떤 창이 어떤 커맨드를 부를 수 있는지 빌드 타임에 고정한 허용 목록. 런타임에 권한을 요청·승인하는 단계가 없다.

2. **창 단위 권한.** capability 파일은 창 라벨 패턴(메인 창 / 팝아웃 창)별 화이트리스트다.\
메인 창 파일에만 알림 권한을 넣으면 메인 창의 호출만 허용되고, 팝아웃 창의 같은 호출은 조용히 거부된다.\
"앱에 권한이 있다"는 개념은 없고 "이 창에 권한이 있다"만 있다 — 그래서 새 권한은 창 라벨별 파일 **둘 다**에 선언해야 한다.

3. **타입 키 불일치 예측.** 컴파일은 된다 — `State<T>`는 제네릭이라 어떤 `T`든 받는다.\
단위 테스트도 통과한다(4번).\
실제 앱에서는 컨테이너가 `TypeId(Arc<T>)`를 찾는데 등록된 것은 `TypeId(T)`뿐이라 매 호출 `state not managed` 오류로 커맨드가 **한 번도 실행되지 않는다**.
   > **TypeId 키 DI** — 타입 자체를 키로 상태를 저장·조회하는 컨테이너. 래퍼 타입(`Arc<T>`)은 원 타입(`T`)과 다른 키다.

4. **테스트가 놓친 이유.** 테스트는 커맨드를 평범한 함수로 불러 필요한 상태를 인자로 직접 넘겼다 — invoke 계층(권한 검사·DI 조회)을 통째로 건너뛴 것이다.\
결함은 바로 그 건너뛴 계층에 있었으므로, 테스트가 아무리 많아도 원리적으로 볼 수 없었다.\
해당 런타임의 mock은 특정 제네릭 형태의 커맨드만 받아 invoke를 태우는 테스트도 불가능했다 — 그래서 한계를 문서화하고 **등록 목록 대조 테스트**로 대체했다.

5. **공통 구조.** 두 사건 모두 "선언(권한 목록·등록 목록)"과 "사용(invoke·State 요구)"이 **다른 파일에** 있고, 둘을 대조하는 장치가 컴파일러에 없다.\
그래서 불일치는 컴파일·테스트를 통과해 런타임까지 살아남는다.\
재발 방지 장치는 선언과 사용을 **같이 보는 곳**에 둔다 — 새 커맨드를 추가할 때 권한을 동반하는 규칙, 등록을 한 함수로 모으고 "요구되는 모든 `State<T>`가 등록 목록에 있는가"를 검사하는 테스트.\
그 테스트는 `Arc<...>`를 되돌리면 그것만 실패한다(이빨 확인).

6. **폴백의 정당성.** 폴백은 실패를 숨기는 게 아니라 **보조 경로의 실패가 핵심 기능을 인질로 잡지 않게** 하는 것이다.\
창 열거에 실패하면 "대상 창 없음 = 새 창으로 분리"로 처리해 최소한 드래그아웃은 유지된다.\
정당한 조건: ① 근본 원인(권한 누락)은 따로 고쳤다 ② 폴백 결과가 사용자에게 안전하고 예측 가능하다 ③ 폴백이 없으면 권한이 또 빠질 때 기능 전체가 다시 무음으로 죽는다.

7. **권한 요청 1회성.** 권한 API는 사용자 제스처 문맥 밖이나 중복 요청에서 실패하거나 무시된다.\
여러 곳에서 동시에 요청하면 요청이 겹치고, 알림을 보낼 때마다(발화 경로에서) 재요청하면 제스처 문맥이 아니라 계속 실패한다.\
in-flight Promise 공유로 요청을 한 번으로 모으고, 거부·실패는 캐시해 발화 경로에서 재시도하지 않으며, 수동 재시도는 설정 버튼(제스처 경로)으로만 한다.\
실패하면 무음 강등 + 경고 1회로, 알림과 독립인 표시(배지)는 그대로 동작하게 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 정적 권한 목록에 새 커맨드의 권한이 빠짐
① 문제 코드
```json
// capabilities/main.json
{ "windows": ["main"], "permissions": ["core:default"] }       // 창 열거 권한 없음
```
```ts
async function windowAtPoint(x: number, y: number) {
  const wins = await getAllWindows();                            // 권한 없음 → throw
  for (const w of wins) if (await w.isVisible() && !(await w.isMinimized())) { /* ... */ }
}
async function dropPanelAt(x: number, y: number) {
  const target = await windowAtPoint(x, y);                      // throw → fallback 포함 전체 실패
  // ... target 없으면 새 창으로 분리 (도달 못 함)
}
```
② 고친 코드
```json
// capabilities/main.json, capabilities/panel.json  (둘 다)
"permissions": ["core:default", "core:window:allow-get-all-windows",
                "core:window:allow-is-visible", "core:window:allow-is-minimized"]
```
```ts
async function windowAtPoint(x: number, y: number) {
  try { /* ... 열거 ... */ }
  catch { return null; }                                         // null = 새 창 (드래그아웃은 유지)
}
```
무엇이 깨졌나: 새 plugin 커맨드를 쓰면서 권한 선언을 동반하지 않았고, 호출부의 예외가 기능 전체를 무음으로 멈췄다.\
같은 구조: 이후 커서 위치·포커스 조회 커맨드도 같은 방식으로 권한을 명시 추가.

### 변형 B — 권한을 한 창에만 선언
① 문제 코드
```json
// capabilities/main.json
"permissions": ["notification:default"]
// capabilities/panel.json  — 없음 → 팝아웃 창 알림이 권한 오류로 무음 실패
```
② 고친 코드
```json
// capabilities/main.json, capabilities/panel.json 둘 다
"permissions": ["notification:default"]
```
```ts
let pending: Promise<Permission> | null = null;
function ensurePermission() {                                    // 동시 요청은 한 Promise 공유
  return (pending ??= requestPermission().then(cacheResult));   // 거부·실패는 캐시, 발화 경로 재시도 금지
}
```
무엇이 깨졌나: 권한의 단위가 앱이 아니라 창 라벨이라는 점을 놓쳤다.

### 변형 C — 타입 키 DI에서 등록 타입과 요청 타입 불일치
① 문제 코드
```rust
builder.manage(Manager::new());                                  // 키 = TypeId(Manager)

#[command]
fn attach(mgr: State<'_, Arc<Manager>>) { /* ... */ }            // 키 = TypeId(Arc<Manager>) → 런타임 "state not managed"

#[test]
fn attach_works() { attach_inner(&mgr) /* 함수 직접 호출 — DI 우회 */ }
```
② 고친 코드
```rust
#[command]
fn attach(mgr: State<'_, Manager>) { /* ... */ }                 // 형제 커맨드와 타입 일치

pub fn register(b: Builder) -> Builder {                         // 등록·커맨드 목록을 한 곳에
    b.manage(Manager::new()).invoke_handler(generate_handler![attach /* , ... */])
}

#[test]
fn every_required_state_is_managed() {
    // 커맨드들이 요구하는 State<T> 목록 ⊆ .manage() 목록 인지 대조
}
```
무엇이 깨졌나: 제네릭 `State<T>`가 타입 불일치를 컴파일 오류로 만들지 못했고, 테스트가 DI 계층을 우회했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
