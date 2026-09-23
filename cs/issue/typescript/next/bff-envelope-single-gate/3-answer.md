# cs/issue/typescript/next/bff-envelope-single-gate — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답

<!-- 질문 1:1 대응 -->

1. 봉투 해제를 호출처마다 하면, 어느 한 페이지에서 `success` 검사를 빠뜨리는 순간 **오류 봉투를 정상 데이터인 척 화면에 그리게 된다.** `{success:false, error:{...}}`가 왔는데 `body.data`(존재하지 않거나 의미 없는 값)를 바로 렌더하면, 사용자에게는 "빈 화면"이나 "이상한 데이터"로 보이고 에러 경로는 아무도 타지 않는다. 실패가 났는데 실패 신호가 나가지 않는 것 — silent failure다.
   > **봉투(envelope)** — 실제 페이로드를 `{success, data|error}`처럼 성공/실패 표시로 감싼 응답 포맷. 데이터를 쓰려면 반드시 성공 여부를 먼저 검사해야 한다.

2. 진짜 위험은 **"빠뜨릴 자리의 개수"** 다. 호출처가 N개면 검사를 잊을 수 있는 지점도 N개고, 새 페이지를 추가할 때마다 하나씩 늘어난다. 사람이 매번 규율로 기억해야 하는 검사는 언젠가 반드시 한 곳에서 빠진다. "N개가 각자 검사"는 방어가 N개의 규율에 분산돼 있어 최약점이 전체를 결정하는 구조고, "한 곳에 강제"는 방어가 코드 경로 하나로 수렴해 **빠뜨릴 자리 자체가 없다**(단, 창구를 우회하는 새 호출 경로를 린트·리뷰로 막는다는 전제에서). 중복 제거는 부산물이고, 본질은 신뢰성이다.

3. 세 경우를 **전부** 실패로 정규화해야 한다: (a) `fetch` 자체가 던짐 → `ApiError("backend_unreachable", 503)`, (b) 응답 본문이 봉투 모양이 아님(`success`가 boolean이 아님) → `ApiError("invalid_envelope", status)`, (c) 봉투인데 `success=false` → `ApiError(error.code, status, detail)`. 셋 다 **예외로 던지고**, 성공일 때만 `body.data`를 반환한다. 그러면 호출처의 계약은 "리턴을 받으면 그건 확실히 유효한 `data`, 아니면 예외"로 단순해져, 호출처는 세 실패를 구분할 필요가 없다.
   > **정규화(normalization)** — 여러 모양의 실패(네트워크·형식·논리)를 하나의 표현(여기선 `ApiError` 예외)으로 통일해, 호출처가 경우를 나눠 다루지 않게 만드는 것.

4. 일반 원칙: **"검사는 없애는 게 아니라 반드시 거치는 지점 하나로 수렴시킨다."** 넓게는 "신뢰할 수 없는 입력은 신뢰 경계를 넘는 지점에서 한 번, 확실히 검증하고, 그 안쪽에서는 검증된 타입으로만 다룬다"와 같은 원칙이다. 봉투 해제도 "백엔드 응답이라는 외부 입력"을 `apiGet`이라는 경계에서 한 번 검증해 신뢰 가능한 `data:T`로 바꾸는 것이고, 그 뒤 페이지들은 `T`만 본다 — 검증의 DRY이자 신뢰 경계의 단일화다.
   > **검증 DRY(Don't Repeat Yourself)** — 같은 검증을 여러 곳에서 반복하지 않고 한 곳에 두는 것. 검증은 특히 빠뜨리면 조용히 깨지므로 중복 제거의 이득이 "가독성"이 아니라 "안전"이다.

5. 이 정규화를 BFF에서 하는 게 자연스러운 이유는, BFF가 **브라우저와 진짜 백엔드 사이의 유일한 통로**이기 때문이다. 브라우저는 백엔드 주소를 아예 모르고 BFF(서버)만 부르며, 화면 데이터는 BFF가 서버 안에서(SSR) 백엔드에 대신 물어 채운다. 그러니 백엔드 응답이 처음 프론트 영역으로 들어오는 지점이 곧 BFF다 — "외부 응답이 들어오는 유일한 문"과 "그 응답을 검증하는 문"을 같은 곳에 두면, 검증을 우회할 경로가 없다. 클라이언트에서 하면 백엔드를 직접 노출해야 하고 검증 지점도 흩어진다.
   > **BFF(Backend For Frontend)** — 브라우저와 진짜 백엔드 사이에 두는 전용 중간 서버. 브라우저는 이 중간 서버하고만 통신하고 진짜 백엔드는 외부에 노출되지 않는다.

6. 그 순서가 의도적인 이유는, 엣지(리버스 프록시) 설정 재활용 가정이 **틀렸다면 그 위에 쌓을 이후 작업 전부가 재설계 대상**이 되기 때문이다. 가장 위험한(=틀렸을 때 손실이 큰) 가정을 맨 앞에서 실호출로 깨뜨려 보면, 통과하면 나머지를 안심하고 쌓을 수 있고, 실패하면 아무것도 쌓기 전에 알게 돼 버리는 작업이 최소가 된다. "가장 위험한 가정 먼저 실증"은 load-bearing 가정을 조기 스모크로 검증하라는 원칙의 구체형이다. 실제로 배포 직후 엣지를 통한 `curl`이 200/157ms로 통과해, 뼈대가 검증된 자리 위에 서게 됐다.
   > **load-bearing 가정** — 그 위에 다른 결정들이 얹히는, 틀리면 연쇄 붕괴하는 전제. 이런 가정은 쌓기 전에 먼저 실증한다.

7. 로깅을 창구에 얹되 그 실패를 격리한 것은, **단일 창구의 부수 기능이 본 기능을 막지 못하게** 하려는 것이다. 단일 창구는 모든 요청이 지나므로 로깅·추적·타임아웃 같은 횡단 관심사를 얹기 좋은 자리지만, 그 부수 기능(로그 저장소 Redis)이 죽으면 모든 요청이 같이 죽는다면 창구가 단일 실패점이 된다. 그래서 로그 전송 실패는 삼키고 백오프로 물러나되(요청은 진행), 데이터 조회 실패만 예외로 올린다. 경계: **본질 기능(데이터 정규화)의 실패는 시끄럽게, 부수 기능(로깅)의 실패는 조용하되 요청을 인질로 잡지 않게.**
   > **횡단 관심사(cross-cutting concern)** — 로깅·인증·추적처럼 여러 기능에 공통으로 얹히는 부가 로직. 단일 창구에 모으기 좋지만, 그 실패가 본 기능을 막지 않게 격리해야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 호출처마다 봉투를 열던 것을 단일 창구로
① 문제 코드
```ts
// page A
const body = await (await fetch(`${API}/tree`)).json();
if (body.success) render(body.data); else reportError(body.error);
// page B — 검사 누락
const body = await (await fetch(`${API}/docs`)).json();
render(body.data);                                  // 오류 봉투면 undefined 를 정상처럼 렌더
```
② 고친 코드
```ts
// BFF 안의 유일한 창구
export async function apiGet<T>(path: string, reqId: string): Promise<T> {
  let res: Response;
  try { res = await fetch(BACKEND + path, withRequestId(reqId)); }
  catch { log("unreachable", path); throw new ApiError("backend_unreachable", 503); }
  const body = await res.json().catch(() => null);
  if (typeof body?.success !== "boolean") throw new ApiError("invalid_envelope", res.status);
  if (!body.success) throw new ApiError(body.error?.code ?? "unknown_error", res.status, body.error);   // error 누락 봉투도 방어
  return body.data as T;                            // 호출처는 data(T)만 안다
}
// page
const tree = await apiGet<Tree>("/api/tree", reqId);
```
```ts
// 로거: 저장소 실패가 요청을 막지 않게
function log(/* ... */) {
  if (Date.now() < pausedUntil) return;
  store.push(entry).catch(() => { pausedUntil = Date.now() + BACKOFF_MS; });   // 삼키고 물러남
}
```
무엇이 깨졌나: 잊을 수 있는 검사가 N개 호출처에 흩어져 있었다.

### 변형 B — 방어적 빈 값 폴백이 계약 불일치를 장기간 은폐
① 문제 코드
```js
function normalize(raw) {
  const list = raw?.wrapperA?.items;               // 서버는 wrapperB.items 로 보냄 — 존재한 적 없는 키
  if (!Array.isArray(list)) return [];             // "안전하게" 빈 배열
  return list.map(/* ... */);
}
async function load() {
  try { return normalize(await getJson(url)); }
  catch { return []; }                             // 실패도 빈 배열
}
// 결과: 뱃지 카운트가 오랫동안 0 고정, 날짜 "-" 고정, 에러 없음
```
② 고친 코드
```js
// 서버 응답을 평탄한 한 형태로: { scope, message, total_hits, results }
function normalize(raw) {
  if (!Array.isArray(raw?.results)) throw new Error("invalid response shape");   // 형태 불일치는 빈 값이 아니라 실패로
  return raw.results;                              // 진짜 "결과 없음"만 빈 배열
}
// load()의 catch { return [] } 도 제거하거나, 최소한 오류 상태를 따로 표시한다
// + 누락 필드 매핑 추가, 이름 변경 시 저장된 구 값 표시 호환 유지
```
무엇이 깨졌나: 형태 검증 없이 "없으면 빈 값"으로 수렴해, 계약 불일치가 정상적인 "결과 없음"으로 위장됐다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A·B)은 "봉투 해제·형태 검증을 반드시 거치는 창구 하나에서 하고 실패는 시끄럽게"이다. 같은 원리(봉투·래핑 책임이 흩어지면 오류가 정상 데이터로 렌더됨)에 다른 방안이 쓰인 사례:

### 방안 1 — 래핑 책임을 한 계층으로: 이미 감싼 값을 다시 감싸지 않음
```python
# 문제: 헬퍼가 이미 {"sort": [...]} 를 반환하는데 호출부가 또 감쌈
def build_sort():
    sort_options = SortSpec.score_sort()     # 이미 {"sort": [...]}
    return {"sort": sort_options}                  # {"sort": {"sort": [...]}}
# 소비측은 바깥 키 하나만 벗김 → 리스트 자리에 dict → 검색 엔진 400 (특정 경로에서만)
# 고친: 래핑은 헬퍼 한 곳 — 호출부는 그대로 반환
def build_sort():
    return SortSpec.score_sort()
```

### 방안 2 — 프레젠테이션 계층의 재포장 제거 + 배포 순서 원칙
```python
# 문제: 유즈케이스는 {total_hits, results} 를 주는데 핸들러가 다시 감쌈
return {"results": {}, "metadata": {"items": result["results"]}}
#   → 계층마다 필드명이 어긋날 기회, 소비자는 없는 키를 읽어 빈 값(빈 배열로 보였을 가능성 높음)
# 고친: 재포장 없이 평탄 4키
return {"scope": s, "message": m, "total_hits": n, "results": items}
```
```text
경로 변경(/old → /new)을 동반하면 프론트 배포 전까지 404
→ 원칙: 백엔드 먼저 배포 → 수동 확인 → 프론트 배포
→ 후속: 응답 모델(스키마) 선언으로 필드 누락을 서버에서 방어
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 소비측 단일 창구 | 생산측 형태를 바꿀 수 없거나 여러 백엔드가 같은 봉투를 쓴다 | 창구 함수 하나 | 창구를 우회하는 새 호출 경로 | BFF·API 클라이언트 계층이 있을 때 |
| 1. 래핑 책임 한 계층 | 감싸는 쪽과 벗기는 쪽이 같은 코드베이스다 | 호출부 수정 | 어느 계층이 감싸는지 문서화 안 하면 재발 | 빌더·헬퍼가 중첩 구조를 반환할 때 |
| 2. 생산측 재포장 제거 | 생산측(서버) 응답을 바꿀 수 있다 | 계약 변경 + 배포 순서 관리 | 순서를 어기면 일시 404·빈 화면 | 계층마다 응답을 다시 감싸는 서버 |

**결론**: 형태 변환·검증은 **한 계층**에서만 한다 — 생산측을 고칠 수 있으면 재포장을 없애 형태를 하나로(1·2), 없으면 소비측 창구에서 검증한다(기본).\
어느 쪽이든 "없으면 빈 값"으로 수렴하는 방어 코드는 계약 불일치를 정상 결과로 위장하므로, 형태가 틀리면 **실패로** 올린다.
