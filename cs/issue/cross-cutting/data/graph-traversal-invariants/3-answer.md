# cs/issue/data/graph-traversal-invariants — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **스택 오버플로 → 전체 언마운트.**\
   파싱 결과에 자기참조나 순환이 있으면 visited 가드 없는 상호재귀(항목 → 하위 에이전트 → 항목 …)가 끝나지 않아 `Maximum call stack size exceeded`가 난다.\
   이 예외가 렌더 도중 발생하면, UI 프레임워크는 에러 경계(error boundary)가 없는 한 상위 트리 전체를 언마운트한다 — 그래서 "한 목록이 깨짐"이 아니라 "창 전체가 빈 화면"이 된다.\
   진단의 요령은 원인 공간을 줄이는 것이었다: 소프트웨어 렌더링으로도 재현되면 GPU가 아니고, 특정 창에서만 나면 그 창 전용 컴포넌트다 — 그다음 devtools 스택트레이스로 상호재귀 함수 쌍을 특정했다.
   > **error boundary** — 하위 컴포넌트의 렌더 예외를 잡아 그 부분만 대체 UI로 바꾸는 경계 컴포넌트.

2. **visited vs 깊이 제한.**\
   깊이 제한은 "몇 단계 이상은 비정상"이라는 추정이라, 사이클은 막지만 **정상적인 깊은 트리를 자른다**.\
   visited 집합은 "같은 노드를 두 번 방문하지 않는다"는 사실만 쓰므로 정상 데이터는 그대로 그리고 사이클만 유한하게 끝낸다(중복 렌더 key도 함께 막는다).\
   원인 데이터가 어디서 생겼는지 모르는 상태에서 백엔드 정제에 기대는 것도 선택하지 않았다 — 방어는 순회하는 쪽에 둔다.

3. **본문에서 다음 포인터를 읽을 때.**\
   막 재기동된 head처럼 본문(스냅샷)이 아직 없는 노드는 `load()`가 None을 준다 — 다음 포인터도 그 본문 안에 있었다면 순회가 거기서 멈춰 **체인 전체가 사라진다**(부재가 종단으로 오인).\
   다음 포인터는 항상 존재하는 별도 메타(사이드카)에서 먼저 읽고, 본문은 렌더용으로만 쓰면 본문 없는 노드는 결과에서 빠질 뿐 순회는 이어진다.\
   "head = 아무도 가리키지 않는 노드"는 순수 사이클에서 진입차 0인 노드가 없으므로 **head가 0개** → 그 체인은 목록에서 통째로 무음 누락된다. head 순회를 마친 뒤 **미방문 노드를 fallback head로 내보내야** 한다.

4. **DAG 레인 중복 배치.**\
   같은 부모가 두 레인에 동시에 대기하면, 그 부모 커밋이 도착했을 때 두 레인이 모두 이어져 **한 커밋이 두 줄**로 그려지거나 레인이 끊긴다 — 합류(수렴)가 표현되지 않는다.\
   첫 부모가 이미 다른 레인에서 대기 중이면 **현재 레인을 종료(null)** 하고, 합류 대각선은 렌더러가 그린다. 부모가 셋 이상(octopus)·0개(root)인 경우도 같은 indexOf 가드와 뒤쪽 빈 레인 정리로 처리한다.

5. **심링크와 종료 보장.**\
   심링크를 따라가면 탐색 범위 밖으로 벗어나거나, 링크가 조상을 가리킬 때 **같은 경로를 반복 방문**한다(실측: 볼륨이 원자 교체용 타임스탬프 디렉터리 + 심링크로 구성돼 재귀 탐색기가 "같은 경로가 두 번 나타났다"며 중단).\
   링크 미추적만으로는 부족하다 — 깊이·루트 개수 상한만 있으면 넓고 얕은 트리에서 깊이 한도까지 전수 방문해 지연된다. **방문 디렉터리 수 예산**까지 더하고, 예산 소진 시 재귀 복귀에서 조기 종료한다.\
   함정: 링크를 따라가는 메타데이터 조회(`metadata()`)가 아니라 **링크 자체의 타입**(`DirEntry::file_type()`)으로 판정해야 링크를 링크로 본다.

6. **"삽입 후 제거" 이동의 자기 붕괴.**\
   자기 pane의 마지막 탭을 가장자리로 드롭하면: 분할로 새 leaf 생성 → 원본에서 탭 제거 → 원본 leaf가 비어 제거(형제 끌어올림) → **새 leaf 하나만 남아** "분할"이라는 의도와 결과가 어긋난다.\
   원본 = 대상이고 원본의 유일 원소일 때는 no-op로 막는다. 불변식은 "레이아웃에는 leaf가 최소 1개".

7. **자원 상한과의 관계.**\
   visited·예산·중복 배치 방지는 모두 "입력이 트리이고 유한하다"는 가정을 코드가 **강제**하는 장치다 — 입력이 그 가정을 어겨도 순회가 유한 시간·유한 스택 안에 끝난다.\
   한 문장: **순회의 종료는 입력이 아니라 순회자가 보장한다 — 재방문 차단과 폭·깊이 예산을 함께 둔다.**

## 문제 구조 (추상화 코드)

### 변형 A — 사이클 있는 링크를 가드 없이 상호재귀
① 문제 코드
```ts
const pushItem = (it: Item) => {
  entries.push({ kind: "item", item: it });
  for (const [childId, children] of childrenByParent.get(it.id) ?? [])
    pushChildGroup(childId, children);          // → 다시 pushItem(...)
};
// 렌더도 renderItem ↔ renderGroup 상호재귀. 사이클 → 스택 오버플로 → 앱 전체 언마운트
```
② 고친 코드
```ts
const seenItem = new Set<string>();
const pushItem = (it: Item) => {
  if (seenItem.has(it.id)) return; seenItem.add(it.id);
  entries.push({ kind: "item", item: it });
  for (const [childId, children] of childrenByParent.get(it.id) ?? [])
    pushChildGroup(childId, children);          // 그룹 쪽에도 seenGroup 가드
};
// 목록 빌더와 렌더 양쪽에 같은 가드
```
무엇이 깨졌나: 외부 데이터 링크를 트리로 가정했고, 렌더 예외를 격리할 경계도 없었다.

### 변형 B — 체인 순회: 부재 노드·사이클·head 없는 사이클
① 문제 코드
```rust
while let Some(id) = cur {
    let node = load(id)?;            // 본문 없음 → None → 순회 종료 (체인 상실)
    chain.push(node.clone());
    cur = node.prev_id;              // 사이클이면 무한 루프
}
// heads = 아무도 prev로 가리키지 않는 노드  → 순수 사이클이면 heads = ∅
```
② 고친 코드
```rust
while let Some(id) = cur {
    if !seen.insert(id.clone()) { break; }              // cycle guard
    let next = read_meta(&id).and_then(|m| m.prev_id);   // 포인터는 사이드카에서
    if let Some(node) = load(&id) { chain.push(node); }  // 본문은 렌더용
    cur = next;
}
// head 순회 후 미방문 노드를 fallback head로 emit
```
무엇이 깨졌나: "다음"을 없을 수 있는 곳에서 읽었고, 사이클과 head 정의의 공집합을 고려하지 않았다.

### 변형 C — DAG 레인 배치에서 합류 노드 중복 대기
① 문제 코드
```ts
const fp = node.parents[0] ?? null;
lanes[col] = fp;                         // 이미 다른 레인이 fp를 기다려도 또 배치
```
② 고친 코드
```ts
const fp = node.parents[0] ?? null;
lanes[col] = fp !== null && lanes.indexOf(fp) !== -1 ? null : fp;   // 이미 대기 중이면 이 레인 종료(합류)
// ...부모 3+ / 0 도 indexOf 가드 + 뒤쪽 null 정리
```
무엇이 깨졌나: "추적 중인 노드"를 중복 배정해 합류가 표현되지 않고 한 노드가 두 줄로 그려졌다.

### 변형 D — 트리 편집 "삽입 후 제거"의 자기 붕괴
① 문제 코드
```ts
function onDropToEdge(src: Leaf, tab: Tab, target: Leaf, edge: Edge) {
  splitLeaf(target, edge, tab);          // 새 leaf 생성
  removeTab(src, tab);                   // src === target 이고 탭이 1개면
  if (src.tabs.length === 0) removeLeaf(src);   // → 방금 분할한 구조가 붕괴
}
```
② 고친 코드
```ts
function onDropToEdge(src: Leaf, tab: Tab, target: Leaf, edge: Edge) {
  if (src.id === target.id && src.tabs.length <= 1) return;   // no-op
  // ... 이하 동일. 불변식: 레이아웃에 leaf ≥ 1
}
```
무엇이 깨졌나: 원본과 대상이 같은 노드인 경계에서 제거 단계가 삽입 결과를 지웠다.

### 변형 E — 심링크 구조를 가진 디렉터리를 재귀 탐색
① 문제 구조
```yaml
volumes:
  - name: dags
    configMap: { name: dag-files }       # 원자 교체용: <timestamp>/ 디렉터리 + ..data 심링크
volumeMounts:
  - { name: dags, mountPath: /opt/app/dags }   # 재귀 탐색기가 같은 경로를 두 번 만남 → 중단
```
② 고친 구조
```yaml
initContainers:
  - command: [sh, -c, "mkdir -p /opt/app/dags && cat > /opt/app/dags/job.py << 'EOF' ... EOF"]
# 탐색 대상은 일반 파일만 있는 볼륨(PVC). 링크 구조 마운트는 탐색 경로에서 분리
```
무엇이 깨졌나: 탐색기가 따라가는 심링크가 입력 안에 있어 같은 경로가 반복됐다. (이 사례는 탐색기를 고치지 않고 입력 쪽에서 링크 구조를 없앴다 — 아래 방안 비교.)

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

순회 종료를 보장하는 방법은 셋이다.

### 방안 1 — visited 집합 (변형 A·B)
```ts
if (seen.has(id)) return; seen.add(id);
```

### 방안 2 — 링크 미추적 + 경계 + 예산 (파일시스템 워크)
```rust
fn scan(dir: &Path, depth: usize, roots: &mut Set, count: &mut usize, visited: &mut usize) {
    if depth > MAX_DEPTH || *count >= MAX_ROOTS || *visited >= MAX_VISITED { return; }
    for entry in read_dir(dir).ok().into_iter().flatten().flatten() {   // 읽기 실패는 skip
        let Ok(ft) = entry.file_type() else { continue };   // 링크 자체의 타입 (metadata()는 링크를 따라감)
        if ft.is_symlink() || !ft.is_dir() { continue; }
        if is_heavy(&entry) { continue; }             // node_modules·target·dist·.git
        let path = entry.path();
        if path.join(".git").exists() {               // 경계: 루트 기록 후 그 안으로는 내려가지 않음
            roots.insert(path); *count += 1;
            if *count >= MAX_ROOTS { return; }
            continue;
        }
        *visited += 1;
        scan(&path, depth + 1, roots, count, visited);
        if *count >= MAX_ROOTS || *visited >= MAX_VISITED { return; }   // 복귀 시 조기 종료
    }
}
// 커맨드는 never-fail: 실패해도 빈 목록
```

### 방안 3 — 입력에서 순환 구조 제거 (변형 E)
탐색기가 따라갈 링크 구조를 탐색 경로에 두지 않는다(일반 파일로 복사한 볼륨을 탐색).

| | 방안 1 visited | 방안 2 미추적+예산 | 방안 3 입력 정리 |
|---|---|---|---|
| 전제 | 노드에 안정 id가 있음 | 링크를 "따라가지 않아도 되는" 탐색 | 탐색기 코드를 바꿀 수 없거나 바꿀 필요가 없음 |
| 비용 | 방문 집합 메모리 | 상한 튜닝, 넓은 트리에서 누락 가능 | 배포 구성 변경(복사 단계) |
| 실패 모드 | id가 불안정하면 가드 무력 | 예산 소진 시 결과가 잘림(의도된 절단) | 다른 입력 경로로 링크가 다시 들어오면 재발 |
| 맞는 조건 | 사이클 가능한 논리 그래프(파싱 데이터) | 규모·형태를 모르는 외부 파일시스템 | 제3자 탐색기 + 입력을 우리가 통제 |

**결론**: 논리 그래프는 visited가 기본이다(깊이 제한은 정상 데이터를 자르므로 선택하지 않음).\
파일시스템처럼 규모 자체가 무한에 가까운 입력은 사이클 차단만으로 부족하고 예산이 함께 있어야 종료 **시간**까지 보장된다.\
탐색기를 우리가 소유하지 않을 때는 입력 쪽에서 순환을 없애는 것이 유일한 선택지다.
