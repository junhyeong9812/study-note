# cs/issue/data/absent-vs-empty — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **"비어 있으면 무시" 가드.** update에 필드가 **존재**하면 컬렉션 전체를 대체한다는 의미에서, 빈 컬렉션은 "이제 하나도 없다"는 **유효한 새 값**이다.\
   가드가 빈 값을 무시하면 교체가 일어나지 않아 **옛 항목이 stale로 남는다**. 가드는 absent(필드 없음 = 건드리지 마라)와 empty(필드 있음 = 비워라)를 혼동한 것이다.\
   고침은 "present면 무조건 교체"다.
   > **absent vs empty** — 키/필드 자체가 없는 것과, 있는데 값이 빈 것. 앞은 "모름/변경 없음", 뒤는 "비어 있음이 사실"을 뜻한다.

2. **로드 경로의 null 합치기.** 로드 코드는 보통 "없으면 첫 실행이거나 옛 형식 → 레거시 마이그레이션"으로 분기한다.\
   파싱 실패(손상)를 catch해서 `null`로 돌려주면, 손상된 데이터가 "부재" 경로로 들어가 **레거시 값이 마이그레이션되어 부활**한다. 저장값이 문자열 `"null"`이면 파싱이 성공해 null이 되어 같은 경로로 떨어진다.\
   구조만 맞으면 버전을 확인하지 않고 채택하는 것도 같은 결함 — 모르는 버전의 데이터가 그대로 쓰인다.\
   손상·미지 버전은 **보수적 기본값**으로 가야 한다.

3. **필수 필드의 기본값.** 기본값은 "생산자가 안 보낼 수도 있다"는 선언이다. 생산자가 항상 보내는 필드에 달면, 필드가 빠진 **깨진 메시지**가 "정상 빈 메시지"로 디코드된다.\
   목록이 빠진 델타는 "변화 없음", 시작 시각이 빠진 행은 "1970년", 진행 수치가 빠진 메타는 "아무 일도 안 했음"이 된다. 스트림이면 이 가짜 정상 메시지로 **커서까지 전진**해 이벤트가 영구 소실된다.\
   규칙: 기본값은 생산자가 실제로 생략하는(비어 있으면 직렬화를 건너뛰는) 필드에만. 생산자가 항상 쓰면 소비자도 필수 → 누락은 오류 → 커서 미전진.\
   단, 층을 확인해야 한다 — 중간 브리지가 기본값으로 빈 배열을 채워 항상 보내는 곳이라면, 그 아래 소비자에게는 브리지가 생산자이므로 `?? []`가 오히려 불필요한 것이지 결함이 아니다.

4. **값 타입의 zero value.** 값 타입 필드는 설정하지 않아도 0이다. "0이면 미설정 → 기본값 60"은 운영자가 **명시한 0(가장 엄격)**을 미설정과 구분하지 못해 조용히 60으로 **완화**한다.\
   포인터(또는 Option)로 바꿔 `nil = 미설정`, `0 = 명시`를 구분한다.
   > **zero value** — 값 타입 변수가 초기화 없이 갖는 기본값(0, "", false). "설정 안 함"과 구분되지 않는다.

5. **보안 판정의 fail-open.** 시간 제약 claim이 "있는데 숫자가 아님"일 때 0으로 치환하면, "0 = 없음 → 검사 생략" 분기로 흘러 **서명된 형식 오류 토큰이 통과**한다.\
   "키 없음"은 선택적 claim의 정상 상태일 수 있지만, "키가 있는데 형식 오류"는 **거절**해야 할 입력이다. `(value, malformed)`처럼 두 상태를 분리해 반환한다.

6. **UI 초기값 `[]`.** 응답 전에 "0건"이 먼저 그려지고, 실패해도 "0건"이 그려진다 — 사용자는 "결과 없음"과 "아직 모름"과 "실패"를 구분할 수 없다.\
   최소 `loading | done | error`(필요하면 만료 등 추가)를 파생 상태로 두고, 건수·요약은 done일 때만 보인다. 조회 실패를 `[]`로 삼키면 "없음"으로 보고 생성(POST)과 수정(PUT)을 오분기하는 곁가지 결함도 생긴다.

7. **NULL과 빈 문자열.** 처리 대상을 `WHERE col IS NULL`로 고르면 빈 문자열 행은 "처리됨"으로 간주돼 **조용히 제외**된다. "없음"의 표현을 하나로 정규화해야 한다(대부분의 DBMS 기준 — Oracle처럼 `''`를 NULL로 취급하는 DBMS도 있어 동작은 엔진마다 다르다).\
   이 모두가 silent failure인 이유: 어느 경우도 예외가 나지 않는다. 결함이 **정상 도메인 값**(빈 목록, 0, 기본값)의 모습으로 흘러가기 때문이다.

## 문제 구조 (추상화 코드)

### 변형 A — 컬렉션 교체 update에서 빈 값을 무시

```rust
// 문제
if let Some(content) = update.content {
    let diffs = extract_diffs(&content);
    if !diffs.is_empty() { item.diffs = diffs; }   // 빈 새 값 무시 → 옛 diffs stale
}
// 고침: present 면 무조건 교체
if let Some(content) = update.content { item.diffs = extract_diffs(&content); }
```
무엇이 깨졌나: 내용은 있지만 diff가 없는 update가 와도 이전 diff가 화면에 남았다(병합 경로 두 곳).

### 변형 B — 로드 경로에서 부재·손상·미지 버전을 null로 합침

```ts
// 문제
function load() {
  let parsed = null;
  try { parsed = JSON.parse(storage.get(KEY)); } catch { parsed = null; } // 손상 → null
  if (parsed == null) return migrateLegacy(storage.get(LEGACY));           // 부재 경로 → 옛 데이터 부활
  return parseTree(parsed);                                                // version 미확인
}
```

```ts
// 고침: 세 상태를 분기, 손상·미지 버전은 기본값
function load() {
  const raw = storage.get(KEY);
  if (raw === null) return parseTree(null, storage.get(LEGACY)); // 부재: 이때만 마이그레이션
  let parsed; try { parsed = JSON.parse(raw); } catch { return emptyTree(); } // 손상
  if (parsed?.version !== CURRENT_VERSION) return emptyTree();   // 낮거나 모르는 버전
  return validate(parsed) ? parsed : emptyTree();                 // 구조 불변식 검증
}
```
무엇이 깨졌나: 손상된 저장값에서 레거시 값이나 메타데이터의 임의 경로가 되살아났다.

### 변형 C — 생산자가 항상 쓰는 필드를 소비자가 기본값으로 흡수

```rust
// 문제
#[derive(Deserialize)]
struct Delta { #[serde(default)] items: Vec<Item> }   // 누락 → 빈 델타 → 커서 전진
struct HookEvent { #[serde(default)] key: Option<Key> } // key 없는 구버전 payload가 신버전으로 통과
```

```rust
// 고침: 필수는 필수로, default 는 생산자가 생략하는 필드에만
struct Delta { items: Vec<Item> }                      // 누락 = 디코드 오류 → on_decode_error → 커서 미전진
struct HookEvent { key: Key }                          // Option<Key> 는 #[serde(default)] 를 떼도 누락 시 None — 필수로 만들려면 타입 자체를 바꾼다
struct Timeline {
    items: Vec<Item>,
    #[serde(default)] answers: Map<u64, String>,       // 생산자가 비면 직렬화 생략
}
```

```ts
// 프론트 쪽 같은 구조
items: r.items ?? []          // 문제: 생산자 정지·필드 개명이 조용한 빈 목록
items: required(r, "items")   // 고침: 누락 시 throw
```
무엇이 깨졌나: 증상이 없었다 — 깨진 메시지가 정상 빈 메시지로 번역되고 커서가 전진해 이벤트가 영구 소실될 수 있었다.\
같은 구조: 시작 시각이 빠진 행이 "1970년"으로, 진행 수치가 빠진 메타가 "아무 일도 안 했음"(진행률 0)으로 그려질 수 있음 — 그래서 이런 필드도 필수로 둠.\
같은 구조: 한 경로를 고친 뒤에도 가장 큰 본문 조회 경로 하나에서 `?? []`가 다시 살아났다(교훈의 부분 전이) — 복원 시 테스트가 throw 기대로 물리게 고정.

### 변형 D — 미설정 vs 명시적 0, 부재 vs 형식 오류

```go
// 문제: 값 타입 → 미설정도 0
type Config struct { Skew time.Duration }
if cfg.Skew == 0 { cfg.Skew = 60 * time.Second }   // 명시한 0s(엄격)가 60s로 완화

// 고침: 포인터로 미설정(nil)과 명시 0을 구분
type Config struct { Skew *time.Duration }
if cfg.Skew == nil { d := 60 * time.Second; cfg.Skew = &d }
```

```go
// 문제: 형식 오류 claim → 0 → 검사 생략
func unix(m Claims, k string) int64 { v, _ := m[k].(float64); return int64(v) }
if nbf := unix(m, "nbf"); nbf != 0 && now < nbf { reject() }

// 고침: 부재와 형식 오류를 분리 — 존재하는데 비수치면 거절
func unix(m Claims, k string) (sec int64, present, malformed bool) {
    raw, ok := m[k]; if !ok { return 0, false, false }      // 부재
    f, ok := raw.(float64); if !ok { return 0, true, true } // 형식 오류
    return int64(f), true, false
}
```
무엇이 깨졌나: 운영자가 지정한 엄격 설정이 조용히 완화됐고, 서명은 맞지만 claim이 깨진 토큰이 검사를 건너뛰었다.\
같은 계열(곁가지): 목적 전용 audience를 "포함 관계"로 검사하면 다른 목적 토큰이 섞인다 → 원소 정확히 1개·값 일치.

### 변형 E — UI 목록 상태에서 로딩·실패·0건을 `[]` 하나로

```tsx
// 문제
const [rows, setRows] = useState<Row[]>([]);     // 응답 전 "0건"
fetchRows().then(setRows).catch(() => setRows([])); // 실패도 "0건"
return <p>{rows.length}건</p>;

// 고침: 상태를 구분하고 done 에서만 건수
type Status = "loading" | "done" | "error";
if (status === "loading") return <Spinner/>;
if (status === "error")   return <ErrorBox/>;
return <p>{rows.length}건</p>;
```
무엇이 깨졌나: 검색 결과가 응답 전에 "0건"으로 먼저 그려졌고 실패도 빈 결과로 보였다.\
같은 구조: 조회 실패를 `[]`로 삼켜 "기존 데이터 없음"으로 보고 생성/수정 요청을 잘못 골랐다.

### 변형 F — "없음"의 두 표현(NULL과 빈 문자열)

```sql
-- 문제: 처리 대상 선택이 NULL 만 봄 → '' 행은 영원히 제외
SELECT * FROM item WHERE translated IS NULL;

-- 고침: 표현을 하나로 정규화 후 재처리
UPDATE item SET translated = NULL WHERE translated = '';
```
무엇이 깨졌나: 빈 문자열로 저장된 667건이 번역 대상에서 조용히 빠졌다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
