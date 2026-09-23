# cs/issue/reliability/deserialization-trust-boundary — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **캐스트는 검증이 아니다.** `as Mode`는 컴파일러에게 "믿어라"고 말할 뿐 런타임 값을 확인하지 않는다 — 손상값이 union 불변식을 깬 채 들어온다. 얕은 머지는 배열이어야 할 자리에 문자열이 와도 그대로 받아 소비 측 `.filter`·`.length`에서 터진다.\
영속 저장소가 돌려주는 값의 출처: ① **이전 버전 코드**가 다른 스키마로 쓴 값 ② **버그 입력**(범위 밖 숫자 -5·1000) ③ **수동 편집·손상**.\
교정: 필드별 타입 검증 후 복원(`strArr`처럼 원소 단위 필터), 수치는 로드와 세터 **양쪽에서** clamp, 색상 같은 값은 키 화이트리스트 + 형식 검증, 비정형이면 기본값(크래시 대신 "설정 초기화").
   > **역직렬화 경계** — 바이트/텍스트가 프로그램의 타입 있는 값으로 바뀌는 지점. 컴파일 타임 보장이 여기서 끝난다.

2. **all-or-nothing 컬렉션.** `Vec<T>` 역직렬화는 요소 하나가 실패하면 컬렉션 전체가 실패한다 — 한 레코드 안에서 블록 하나가 깨지면 **정상 형제 블록까지 통째로** 사라진다(부분 손상이 전체 손실로 증폭).\
요소별로 `Value`로 받아 각각 파싱하고 실패만 건너뛰면 정상 요소를 살린다.\
대가: 실패를 흡수하면 **무엇을 못 읽었는지 보이지 않는다** — 외부 포맷이 바뀌어 새 블록 종류가 생기면 에러 없이 기능이 조용히 빠진다.\
되찾는 법: 드롭한 줄·블록을 **카운터·로그로 관측**한다(원문에서는 후속 과제로 남은 미해결 위험).
   > **관용 파싱(tolerant parsing)** — 모르는·깨진 부분을 오류로 만들지 않고 건너뛰는 파싱. 견고성과 관측성을 맞바꾼다.

3. **스키마 진화의 두 방향.** 과거 방향: 엄격한 역직렬화는 구버전 파일에 없는 새 필드를 "missing field"로 보고 **로드 전체를 실패**시킨다 → 새 필드에 `default`를 선언하고 "구버전 파일 로드" 테스트를 둔다(UI도 새 필드가 비면 옛 필드로 폴백).\
(serde 기준: `Option<T>` 필드는 입력에 없으면 `default` 없이도 None으로 채워지므로, missing field 실패는 `String`·`Vec` 같은 비-Option 필드에서 난다.)\
미래 방향: "모양만 맞으면 수용"하면, 미래 버전이 **같은 필드 이름의 의미를 바꿨을 때** 현재 코드가 그것을 옛 의미로 해석해 계약이 조용히 깨진다. 손상 데이터도 모양만 맞으면 통과한다.\
교정: 버전이 **정확히 일치할 때만** 구조를 채택하고, 상위 버전은 안전하게 뽑을 수 있는 일부만 best-effort로 추출, 나머지는 기본값. 구조 검사에 더해 **의미 불변식**(예: 주 항목 정확히 1개·빈 분할 금지)까지 검증한다.

4. **재귀 검증의 예산.** 재귀 검증은 입력 깊이만큼 스택을 쓴다 — 12k 깊이로 중첩된 **문법상 유효한** JSON이 스택 오버플로(JS에서는 `RangeError`)를 일으키고, 그 예외를 잡지 못하면 앱 시작 자체가 크래시한다.\
순환 참조는 `JSON.parse` 결과에서는 생길 수 없다 — 순환 가드는 이미 객체로 받은 입력(메모리 상태·structured clone 등)을 검증할 때의 방어다.\
예외 경계가 `JSON.parse`만 감싸면 파싱 1단계의 오류만 잡히고, 그 뒤 **검증 단계에서 던진 예외**는 경계 밖으로 샌다.\
교정: 깊이·노드 수 예산(초과 시 오류 → 손상 취급) + 순환 가드, 그리고 파서 **전체**를 예외 경계로 감싸 어떤 throw든 "손상 → 기본값"으로 수렴시킨다.
   > **깊이 공격** — 과도하게 중첩된 입력으로 재귀 처리기의 스택·시간을 고갈시키는 공격.

5. **모르는 열거값과 Debug 누출.** 확장 가능한 열거값은 상대가 언제든 새 값을 보낼 수 있다. 처리 분기가 아는 값뿐이면 새 값의 데이터는 **무음 드롭**된다 → "모름" 분기를 명시적으로 정의한다(예: 미지 확장 채널 데이터를 표준 출력으로 합침 + 테스트).\
내부 Debug 표현(`Custom("FOO")`)은 구현 세부이지 외부 계약이 아니다 — 와이어에 쓰면 소비자가 그 형식에 의존하게 되고 라이브러리 버전에 따라 바뀐다 → 표준 이름(TERM·KILL 등)으로 정규화하고, 사용자 정의 값만 원문 그대로 쓴다.

6. **선언적 요청 모델.** 선언적 모델의 계약은 "**선언된 이름·타입만** 채운다"이다.\
선언 안 된 키는 파싱 단계에서 버려지고(Pydantic 기본 `extra='ignore'`) 필드는 기본값 `None`이 된다 → 필터가 **에러 없이 미적용**. 내부 파생용으로 `exclude`된 필드와 같은 이름의 키를 보내도 반영되지 않는다.\
타입이 다르면 결과가 갈린다 — 필드 타입이 느슨해(`str`·`Any` 등) 강제 변환 validator(`mode='before'`)가 빠지면 원시 문자열이 그대로 하위 코드로 흘러가 **먼 곳에서 속성 오류(500)**로 터지고, 선언 타입이 엄격하면 Pydantic은 기본적으로 검증 오류(422)로 거부한다(이 경우는 조용하지 않다 — 조용히 꺼지는 것은 키가 선언과 어긋나 무시되거나, 검증을 거치지 않는 경로로 값을 읽을 때다).\
파생(computed) 필드는 **모델 인스턴스에만** 존재하므로 원본 dict에서 읽으면 없다 → 원본을 모델로 한 번 통과시킨 뒤 읽는다.\
교정: 모델 타입을 **실제 송신 형태**에 맞추고(`Optional[List[str]]`), 필드를 선언하고, 변환 validator를 연결한다. validator의 허용 목록은 하드코딩하지 말고 매핑 테이블 키를 동적으로 참조해 동기화한다.

7. **관용과 엄격의 분담.** 둘은 서로 다른 층에서 공존한다.\
**엄격(거부)** 쪽: 버전 게이트·의미 불변식·타입 검증·깊이 예산 — "이 데이터를 신뢰해도 되는가"를 판정한다.\
**관용(수용)** 쪽: 요소별 파싱으로 부분 손상 격리·새 필드 default·모르는 열거값 분기 — "신뢰할 수 있는 부분은 살린다".\
둘을 잇는 것이 **관측**이다 — 관용으로 버린 것은 반드시 세어서 보이게 해야, 견고성이 무음 기능 소실로 변하지 않는다.

## 문제 구조 (추상화 코드)

### 변형 A — 영속값을 무검증으로 신뢰
① 문제 코드
```ts
const saved = JSON.parse(localStorage.getItem(KEY) ?? "{}")
setState({ ...defaults, ...saved })                     // 얕은 머지 — 배열 자리에 문자열이 와도 통과
const mode = localStorage.getItem(MODE_KEY) as Mode      // 캐스트 — 손상값이 union 불변식 파괴
applyFontSize(saved.fontSize)                            // -5 / 1000 그대로
```
② 고친 코드
```ts
const strArr = (x: unknown): string[] =>
  Array.isArray(x) ? x.filter((p): p is string => typeof p === "string") : []
const clampFontSize = (n: number) => Math.max(MIN, Math.min(MAX, Math.round(n) || DEFAULT))  // 로드·세터 양쪽
const mode = MODES.includes(raw as Mode) ? (raw as Mode) : DEFAULT_MODE
const colors = pickWhitelisted(saved.colors, COLOR_KEYS).filter(isHexColor)   // 비객체 → null
```
무엇이 깨졌나: 경계에서 타입을 주장만 하고 검증하지 않았다.\
같은 구조: 패널 id를 밀리초 타임스탬프로 생성 → 같은 ms에 두 번 만들면 충돌 → 단조 카운터.

### 변형 B — all-or-nothing 컬렉션 (부분 손상 증폭)
① 문제 코드
```rust
#[derive(Deserialize)]
#[serde(untagged)]
enum Content { Text(String), Blocks(Vec<Block>) }   // 블록 하나 실패 → Blocks 전체 실패 → 형제 유실
```
② 고친 코드
```rust
#[derive(Deserialize)]
#[serde(untagged)]
enum Content { Text(String), Blocks(Vec<serde_json::Value>), Other(serde_json::Value) }  // catch-all은 마지막
let blocks: Vec<Block> = raw.into_iter()
    .filter_map(|v| serde_json::from_value::<Block>(v).ok())   // 요소별 격리
    .collect();
#[test] fn malformed_block_does_not_drop_valid_siblings() { /* ... */ }
```
무엇이 깨졌나: 컬렉션 역직렬화의 실패 단위가 요소가 아니라 컬렉션 전체였다.\
함정: `untagged`는 variant를 위에서부터 시도하므로 catch-all을 맨 뒤에 둔다.\
선택하지 않은 방법: 모르는 필드 전면 거부(외부 포맷의 마이너 업데이트마다 깨짐), 전부 `Value` 수동 탐색(타입 안전성 상실).

### 변형 C — 드롭을 관측하지 않는 관용 파싱
① 문제 코드
```rust
fn parse_line(line: &str) -> Option<Record> { serde_json::from_str(line).ok() }   // 실패가 사라짐
```
② 필요한 것 (원문은 후속 과제로 남긴 미해결 위험)
```rust
fn parse_line(line: &str, stats: &mut ParseStats) -> Option<Record> {
    match serde_json::from_str(line) {
        Ok(r) => Some(r),
        Err(e) => { stats.dropped += 1; log_once(&e); None }   // 드롭을 셈
    }
}
```
무엇이 깨졌나: 견고성을 위해 흡수한 실패가 관측되지 않아, 포맷 드리프트가 기능의 무음 소실로 나타났다.

### 변형 D — 스키마 진화: 과거는 default, 미래는 버전 게이트
① 문제 코드
```rust
#[derive(Deserialize)] struct Snapshot { items: Vec<Item>, title: String }  // 구버전 파일: missing field
// (Option<String>이었다면 serde가 None으로 채워 실패하지 않는다)
```
```ts
function parseTree(raw: unknown): Tree { return isWellShaped(raw) ? raw : emptyTree() }   // 모양만 검사
```
② 고친 코드
```rust
#[derive(Deserialize)] struct Snapshot { items: Vec<Item>, #[serde(default)] title: String }
#[test] fn loads_legacy() { /* 구버전 JSON 로드 성공 */ }
```
```ts
function parseTree(raw: any): Tree {
  if (raw?.version === VERSION && isValidTree(raw.root)) return raw   // 정확 일치 + 의미 검증
  if (raw?.version > VERSION) return extractSafeSubset(raw)          // 미래: 안전한 일부만 best-effort
  return emptyTree()
}
// isValidTree: 구조 + 의미 불변식 (주 항목 정확히 1개, 빈 분할 금지, ...)
```
무엇이 깨졌나: 과거 방향은 너무 엄격해 로드가 실패했고, 미래 방향은 모양만 봐서 의미가 바뀐 데이터를 정상으로 받았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "로드 시 검증·정규화, 부분 손상 격리, 스키마 진화 명시"이다. 같은 원리(경계에서 타입 보장이 끊긴다)에 위협·경계 종류가 달라 다른 방안이 쓰인 사례:

### 방안 1 — 재귀 검증에 깊이·노드 예산 + 파서 전체 예외 경계
```ts
// 문제
function readTree() {
  let raw; try { raw = JSON.parse(stored) } catch { return emptyTree() }   // parse만 보호
  return parseTree(raw)                     // 12k 깊이·순환 → 검증 재귀가 스택 오버플로 → 시작 크래시
}
// 고친
const MAX_DEPTH = 64, MAX_NODES = 4096
function isValidTree(n: unknown, depth = 0, budget = { nodes: 0 }, seen = new Set()): boolean {
  if (depth > MAX_DEPTH || ++budget.nodes > MAX_NODES) throw new RangeError("tree budget")
  if (seen.has(n)) throw new RangeError("cycle"); seen.add(n)
  // ... 자식 재귀
}
function readTree() {
  try { return parseTree(JSON.parse(stored)) } catch { return emptyTree() }   // 어떤 throw든 손상 취급
}
```

### 방안 2 — 확장 열거값의 "모름" 분기 + 표준 이름 정규화
```rust
// 문제
match ext { 1 => stderr.extend(data), _ => {} }            // 미지 채널 무음 드롭
send(format!("{:?}", signal));                              // Custom("FOO") 같은 Debug 표현이 와이어로
// 고친
match ext { 1 => stderr.extend(data), _ => stdout.extend(data) }   // 모르는 채널은 stdout으로 fold (테스트)
fn sig_name(s: &Sig) -> String {
    match s { Sig::Term => "TERM".into(), Sig::Kill => "KILL".into(), /* ... */ Sig::Custom(n) => n.clone() }
}
```

### 방안 3 — 요청 모델을 실제 송신 형태에 맞추고 변환 강제
```python
# 문제
class SearchParams(BaseModel):
    filter_flag: Optional[bool] = None                     # 프론트는 ["no_x"] 리스트를 보냄 → 미적용
    checkbox_filter: Optional[List[str]] = Field(default=None, exclude=True)   # 내부 파생용 → 같은 이름 입력 무시
    # 다른 필터는 아예 미선언 → 키가 버려져 None
report = raw_obj["filtered_ids"]                          # computed_field는 dict에 없음 → 오류
# 고친
class SearchParams(BaseModel):
    filter_flag: Optional[List[str]] = None                # 실제 송신 형태
    other_filter: Optional[List[str]] = None               # 선언
    checkbox_filter: Optional[List[Status]] = Field(default=None, exclude=True)
    @field_validator("checkbox_filter", mode="before")     # 원시 문자열 → enum
    @classmethod
    def coerce_checkbox(cls, v): return to_enum_list(v)
report = ReportRequest(**raw_obj).filtered_ids            # 모델을 거쳐 파생 필드 사용
ALLOWED = set(LABEL_TO_STATUS.keys())                      # 허용 목록은 매핑 키를 동적 참조
```
원문의 대응은 필드 선언·타입 정렬·validator 연결이었다 — 선언 밖 키를 거부하는 설정(`extra='forbid'`)으로 불일치를 조기 검출하는 대안은 기록에 없다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 로드 시 검증·격리·진화 | 데이터를 우리 코드(과거·미래 버전)가 썼다 | 필드별 검증 코드 | 드롭 관측이 없으면 무음 소실 | 설정·스냅샷·로컬 영속 |
| 1. 깊이·노드 예산 | 입력 크기를 공격자·손상이 정한다 | 예산 카운터 | 정상 대형 입력도 거절(상한 튜닝 필요) | 재귀 구조 파싱 |
| 2. 모름 분기 + 정규화 | 상대가 열거값을 확장할 수 있다 | 분기·이름 매핑 | 모름 처리 정책이 틀리면 섞임 | 외부 프로토콜 수신·송신 |
| 3. 요청 모델 정렬 | 송신 측이 다른 팀·다른 코드다 | 양쪽 계약 동기화 | 새 필드 추가 시 다시 어긋남 | API 입력 경계 |

**결론**: 경계의 데이터가 **자기 코드가 쓴 것**이면 기본 방안(검증·default·버전 게이트·격리+관측)으로 충분하다.\
입력의 **크기·모양을 남이 정할 수 있으면** 검증 자체가 공격 표면이 되므로 예산을 먼저 건다(1).\
열거값·요청 스키마처럼 **상대가 계약을 확장·변경하는 경계**에서는 모르는 값의 처리를 명시하고(2), 선언과 실제 송신 형태를 한 기준으로 맞춘다(3) — 어느 쪽이든 "조용히 버려짐"을 보이게 만드는 것이 공통 목표다.
