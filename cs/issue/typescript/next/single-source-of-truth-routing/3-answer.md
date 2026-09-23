# cs/issue/typescript/next/single-source-of-truth-routing — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `single-source-of-truth`

## 정답

<!-- 질문 1:1 대응 -->

1. 라우트를 셋으로 나누면 "이 경로가 폴더인가 주제인가 문서인가"라는 판단을 **URL 설계에 한 번, 백엔드 트리 모델에 한 번 — 두 곳에** 유지하게 된다. 그런데 그 판단은 트리의 `isLeafTopic` 값 하나가 이미 준다. 같은 사실을 두 곳에서 관리하면, 트리가 바뀌었는데 URL 라우팅 규칙이 안 따라오거나 그 반대일 때 두 곳이 어긋난다. 판단이 두 번 존재하는 순간 정합성은 사람의 규율에 의존하게 되고, 규율은 언젠가 깨진다.
   > **단일 진실원(single source of truth)** — 하나의 사실을 저장·판단하는 권위 있는 위치를 한 곳으로 정하는 것. 같은 사실이 동기화 장치 없이 두 곳에 있으면 언젠가 서로 달라지기 쉽다(drift).

2. `isLeafTopic`가 단일 진실원이라면, URL 구조(`/folder/...` vs `/subject/...`)에 종류를 또 심는 것은 **중복된 두 번째 진실원**을 만드는 것이다 — 그리고 두 진실원은 동기화 장치가 없으면 어긋난다. 구체적 예: 어떤 폴더가 하위 폴더를 모두 잃어 백엔드가 그것을 `isLeafTopic=true`(주제 리프)로 재판정했는데, URL은 여전히 `/folder/...`로 접근되도록 라우팅돼 있으면, 주제여야 할 노드가 폴더 화면(하위 목록)으로 잘못 렌더된다. 반대 방향도 마찬가지다.

3. 캐치올 라우트 하나만 두고 그 안에서 `isLeafTopic`로 분기하면, **새 노드 종류가 추가돼도 URL 설계는 손대지 않고 분기 코드 한 곳(그 라우트의 분기문)만** 고치면 된다. 라우트 셋을 유지하는 설계에서는 새 종류마다 새 라우트를 추가하고, URL 판정과 백엔드 판정을 동시에 맞춰야 해 변경 지점이 여러 곳으로 흩어진다. 단일 라우트는 변경을 한 곳으로 국소화한다.
   > **캐치올 라우트(catch-all route)** — `[...slug]`처럼 슬래시로 이어진 경로 전체를 하나의 처리기가 받는 라우트. 경로별로 처리기를 나누지 않고 한 곳에서 분기한다.

4. "트리 노드 → 폴더/주제 분기"와 "트리에 없음 → 문서 직접 조회 폴백"을 한 라우트가 모두 처리하면, **경로를 어떻게 해석할지가 한 군데로 수렴**한다. 트리에서 못 찾은 경로(예: `cs/index` 같은 폴더 직속 문서)를 "그럼 문서일 수 있다"고 마지막에 조회해보고, 그래도 없으면 404. 이 폴백이 별도 라우트였다면 "트리에 있나/없나"라는 같은 판단이 또 두 곳으로 갈릴 것이다. 한 라우트가 순서대로(노드 있음→종류 분기, 없음→문서 폴백→404) 처리하니, 경로 해석의 진실원도 하나로 유지된다.
   > **폴백(fallback)** — 우선 경로가 실패했을 때 시도하는 대체 경로. 여기선 "트리에서 못 찾으면 문서로 직접 조회, 그것도 실패하면 404".

5. 상대 링크 치환을 렌더 시점(프론트)에 한 이유는 **"콘텐츠 JSON은 백엔드, 보이는 모양·경로는 프론트"라는 경계**를 설계 때 정했기 때문이다. 백엔드는 노트 원문 문자열만 주고, 그 원문 안의 `](../foo/)`를 `/wiki/...`라는 **웹 경로**로 바꾸는 것은 "화면이 어떻게 이동하는가"에 대한 지식이라 프론트의 책임이다. 백엔드가 웹 경로를 미리 박아 보내면, 백엔드가 프론트의 URL 구조를 알아야 하는 역방향 결합이 생긴다. 경계를 지키면 백엔드는 URL 스키마 변경에 영향받지 않는다.

6. `toWebPath` 결함이 빌드·화면 통과로 안 잡히는 이유는, 그 버그가 **특정 입력(`.md` 뒤에 `#`/`?`가 붙은 링크)이 실제로 들어와야만** 발현되기 때문이다. 대부분의 링크(`../foo/`, `bar.md`)는 정상 변환되므로 빌드도 통과하고 화면도 뜬다 — 컴파일러와 렌더러는 "이 코드가 모든 입력을 옳게 다루는가"를 검사하지 않는다. `other.md#절` 같은 hash 링크가 실제로 눌릴 때에야 `.md.md` 같은 잘못된 경로로 이동해 드러난다. 즉 **입력 공간의 특정 코너 케이스**를 재현하는 입력이 있어야 잡히는 결함이다.

7. 일반화: **빌드·화면 통과는 "타입이 맞고 흔한 경로가 돈다"만 보장하지, "모든 입력을 옳게 다룬다"를 보장하지 않는다.** "순항한 이슈의 코드가 무결한 코드는 아니다"는, 구현이 매끄럽게 끝나 빌드가 초록불이어도 다루지 못하는 입력(edge case)이 남아 있을 수 있다는 뜻이다. 빌드·타입체크가 잡는 것은 문법·타입 정합성이고, 잡지 못하는 것은 "이 함수가 명세의 모든 입력에 대해 옳은 출력을 내는가"라는 의미론적 정확성이다. 그래서 순항했더라도 입력 경계(hash·query·빈 값·중복)를 반증하는 리뷰/테스트가 별도로 필요하다 — 이 결함은 실제로 이후 이슈의 코드 리뷰에서 잡혀 hash/query를 먼저 분리·보존하도록 고쳐졌다.

## 문제 구조 (추상화 코드)

### 변형 A — 노드 종류 판단을 URL 구조와 데이터 모델 두 곳에 둠
① 문제 코드 (선택하지 않은 설계)
```text
app/folder/[...slug]/page.tsx     ← URL 이 "종류"를 말함 (판단 #1)
app/subject/[...slug]/page.tsx
app/doc/[...slug]/page.tsx
+ 트리 노드의 isLeafTopic 필드 ← 같은 판단 (판단 #2) → 언젠가 어긋남
```
② 고친 코드
```tsx
// app/wiki/[...slug]/page.tsx — 캐치올 라우트 하나
export default async function Page({ params }) {
  const path = params.slug.join("/");                                // Next 15+ 는 params 가 Promise — (await params).slug
  const node = lookupNode(tree, path);
  if (node && !node.isLeafTopic) return <FolderPane node={node} />;   // README + 하위 목록
  if (node && node.isLeafTopic)  return <TopicTabs node={node} />;    // 고정 탭
  const doc = await fetchDoc(path + ".md").catch(() => null);         // 트리에 없음 → 문서 폴백
                                                                      // (엄밀히는 "없음"만 null — 그 외 오류까지 404로 삼키면 장애가 404로 위장된다)
  if (!doc) notFound();
  return <DocView doc={doc} />;
}
```
```ts
// 상대 링크 → 웹 경로 (렌더 시점, 프론트 책임)
function toWebPath(href: string, base: string) {
  const cut = href.search(/[#?]/);                         // hash/query 먼저 분리해 보존
  const suffix = cut >= 0 ? href.slice(cut) : "";
  let p = (cut >= 0 ? href.slice(0, cut) : href).replace(/\.md$/, "");
  // ... base 기준으로 . / .. 를 스택으로 해소
  return "/wiki/" + resolved + suffix;                     // 수정 전: "other.md#절" → ".md.md" 조회
}
```
무엇이 깨졌나(선택하지 않은 설계): 같은 사실을 두 곳에서 관리하면 동기화 장치 없이는 어긋난다.\
같은 구조: 라우트가 "하위 폴더 있음 = README 본문, 리프 = 주제 뷰"처럼 종류를 **파일시스템 구조에서 추론**하자, 콘텐츠에 하위 폴더를 추가한 순간 외부 문서의 링크 41개가 본문 대신 목록을 보여 줌 → 사례 본문을 README로 옮겨 폴더 URL로 복귀(우회), 부작용(README 종류는 검색 제외)은 후속 과제로 기록. 상대 링크 전수 존재 검사로 깊이 오류 2건도 검출.

### 변형 B — 같은 파생 값을 두 경로가 각자 계산
① 문제 코드
```python
def extract_final_holders(doc):      # max-rank 로직 사본 1
    # ...
def extract_records(doc):      # max-rank 로직 사본 2 → 한쪽만 마이그레이션 → 화면 A·B 이름이 다름
    # ...
query = make_query(parse_operators(param))       # 질의는 파서 결과로
highlight = keywords_from(param)                  # 하이라이트는 원본 파라미터를 다시 읽음 → "a || b" 원문 노출
```
② 고친 코드
```python
regs = extract_records(doc)
holders = extract_final_holders(regs)             # 한 번 순회한 결과를 입력으로 (신규 필드 우선, 구 로직은 폴백)
query, collected = make_query_with_collection(param)   # 빌드 중 파싱 결과 수집
highlight = keywords_from(param, collected=collected)   # 같은 파싱 결과 사용 (수집값이 로그 payload에 섞이는 점 주의)
```
무엇이 깨졌나: 같은 의미의 값을 독립적으로 두 번 도출해, 한쪽 변경이 불일치가 됐다.\
같은 구조: 목록(경량 필드, 점수 null) 기준으로 모달 칩을 계산하고 카드는 등급 라벨을 써서, 상세 도착 후 칩이 뒤집힘 → 칩 판정 소스를 카드와 통일하고 상세 로딩 중엔 상세 표만 로딩 표시.\
같은 구조: URL 정확 일치 판정 때문에 한 페이지는 DB 트리, 하위 페이지는 하드코딩 폴백을 써 메뉴 순서가 달랐음 → DB 그룹 매칭 우선, 미커버만 폴백.\
같은 구조: 표시 정책(기준월·격자·등급)이 프론트 두 어댑터와 서버에 반복 구현 → 서버 단일 출처로 이관, 프론트는 형태 변환·라벨만, 응답 래퍼 파싱은 fetch 경계에서.\
같은 구조(계획 단계): 본 쿼리에 최소 점수를 도입할 때 집계 쿼리 빌더도 같은 조건을 쓰지 않으면 "N건"과 "상태별 M건"이 어긋나므로 3곳에 같은 조건 + 테스트.

### 변형 C — 색인 측과 질의 측이 같은 변환을 따로 보유
① 문제 코드
```text
질의 서버:   transform_v1(text)   (언어 X 구현)
색인 파이프: transform_v1'(text)  (복사본, 또는 검색 엔진 플러그인의 언어 Y 재구현)
→ 한쪽만 수정 → 같은 입력에 다른 토큰 → 매칭 실패 (재색인 전까지 지속)
```
② 고친 코드
```text
색인 파이프라인이 변환 결과를 미리 계산해 필드로 저장 (플러그인 분석 제거)
질의 측은 같은 구현을 사용 → 변환 구현 한 곳
(저비용 경로를 택한 곳은 "N곳 동시 수정 필수" 규칙 + 동일 패치 동기 커밋 + 재색인, 패키지화는 후보)
```
무엇이 깨졌나: 대칭이어야 하는 두 변환이 각자 진화했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~C)은 "판단·파생 값을 권위 있는 한 곳에서 계산하고 나머지는 그 결과를 쓴다"이다. 같은 원리(같은 사실을 두 곳에서 관리하면 어긋남)에 다른 방안이 쓰인 사례:

### 방안 1 — 플랫폼이 이미 소유한 상태를 진실원으로
```ts
// 문제: 현재 패널을 수동 카운터로 추적 → 클릭 등 다른 경로의 포커스 변경과 어긋남
let current = 0; function nav(d) { current += d; panels[current].focus(); }
// 고친: 브라우저가 소유한 activeElement 에서 매번 판별
function nav(d) {
  const panels = [...document.querySelectorAll<HTMLElement>(".pane")];
  const i = panels.findIndex(p => p.contains(document.activeElement));
  panels[(i + d + panels.length) % panels.length]?.focus();
}
```

### 방안 2 — 동일 파이프라인 두 벌을 공유 구현으로
```rust
// 문제: GUI 경로와 CLI 경로가 같은 아카이브 계약을 각자 구현
//   GUI만 "변경 없음 스킵"·완료 마커, CLI만 재시도 → CLI 산출물을 GUI가 인식 못해 매번 1~3분 재추출
// 고친: core 에 순수 파이프라인 하나, 양쪽은 호출만
pub fn run_archive(req: &Request<'_>, extract: &dyn Fn(&str) -> Result<String, String>) { /* ... */ }
// 특성 테스트: CLI 로 만든 산출물 → GUI 재실행 시 "변경 없음" 스킵
```
같은 구조: CLI 사전 스캔이 내용 비교 없이 스킵해 "자란" 원본이 영영 갱신 안 됨 → 보수 판정 + id 충돌은 모호(후보 유지) + 바이트 일치 시 전문 비교로 확정, 프로젝트 범위 필터.

### 방안 3 — 편집 버퍼를 DOM이 아닌 JS 상태 단일 출처로
```js
// 문제: 편집 내용을 "포커스된 textarea"에서 읽음 → 무관한 재렌더가 textarea 를 캐시로 리셋, 잘못된 pane 을 dirty 검사
// 고친
state.editValue = "";      // 버퍼 (textarea 는 여기서 init, input 마다 갱신)
state.editPaneId = null;   // 편집 대상 식별
function leavingEditedPath(path) {        // 닫기·이동·분할·전환 = 떠나는 경로 일원화
  const leaf = editingLeaf();
  if (leaf && leaf.active === path) {
    if (!confirmLeaveEdit()) return false;
    state.editPaneId = null; state.editValue = "";
  }
  return true;
}
```

### 방안 4 — 여러 소비자가 한 목록을 공유 + 겹침은 fail-fast
```java
// 문제: 컬럼 목록 하나를 SQL·값·타입 세 소비자가 공유해야 하는데, 선언 경로가 생성키를 빼지 않음
//   SQL 생성기만 자체 필터 → "INSERT (name) VALUES (?)" 에 값 2개 바인딩 → 위치 기반 바인딩 오류
// 고친(리뷰 반영): 선언 컬럼이 생성키와 겹치면 조용히 빼지 않고 즉시 예외
if (!declared.isEmpty()) {
  List<String> overlap = declared.stream().filter(c -> keys.contains(c.toUpperCase(Locale.ROOT))).toList();
  if (!overlap.isEmpty()) throw new InvalidUsageException("Declared columns " + overlap + " must not overlap with generated key columns");
  return new ArrayList<>(declared);
}
```

### 방안 5 — 이중 상태를 하나로 + 값 import 의 바인딩 시점
```python
# 문제: 실행 중 여부를 모듈 dict 와 인스턴스 필드 두 곳에 저장
#   백그라운드 작업에 인스턴스 메서드를 직접 등록 → dict 는 아무도 내리지 않음 → 재시도가 영원히 409
#   from mod import status  → import 시점 바인딩이라 원 모듈의 재할당을 못 따라감
# 고친: 인스턴스를 유일한 진실원으로, 지연 import + 모듈 속성 접근
def is_running() -> bool:
    import app.routers.runner as r
    return bool(r.instance and r.instance.is_running())
# dict 의 is_running 키 삭제, 게이트·응답 필드는 전부 파생값
```

### 방안 6 — 전역 설정을 탭별 스냅샷에서 분리
```tsx
// 문제: 탭과 무관한 컬럼 순서를 탭 데이터 스냅샷에 같이 저장 → 탭 전환·삭제 시 오래된 기본값이 덮음
setCurrent(item.data);
// 고친: 복원 시 전역 값은 현재 것을 유지
setCurrent(prev => ({ ...item.data, orders: prev.orders }));
```

### 방안 7 — 같은 URL을 요구하는 두 페이지가 조용히 하나만 활성화됨(사건 환경)
```text
문제: app/[locale]/page.tsx (redirect → /dashboard)
      app/[locale]/(group)/page.tsx (대시보드 본문)  ← route group 은 URL 무영향 → 둘 다 /[locale]/
      빌드는 통과(한쪽만 활성), /[locale]/dashboard 는 존재하지 않아 404
      (사건 환경 기준 — Next 문서는 같은 URL로 해석되는 그룹 간 페이지를 오류로 규정하며,
       버전·구성에 따라 빌드 오류로 잡히기도 한다. 잡힌다고 가정하지 말 것)
고친: app/[locale]/(group)/dashboard/page.tsx 로 이동 — URL 하나에 페이지 하나
교훈: 빌드 통과 ≠ 라우트 동작 (dev 진입으로 확인)
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 권위 있는 한 곳에서 계산 | 판단·파생의 주인을 정할 수 있다 | 호출 경로 재배선 | 새 경로가 옛 사본을 다시 만듦 | 서버·프론트·색인에 같은 로직이 흩어질 때 |
| 1. 플랫폼 소유 상태 사용 | 플랫폼이 이미 그 사실을 관리한다 | 매번 조회 | 플랫폼 동작 차이(엔진별) | 포커스·선택·스크롤 등 브라우저 상태 |
| 2. 공유 구현 | 여러 진입점이 같은 계약을 수행한다 | 모듈 경계 재설계 | 진입점별 특수 처리가 다시 새어 나옴 | GUI·CLI·배치가 같은 파이프라인일 때 |
| 3. JS 상태 버퍼 | 뷰(DOM)가 수시로 재생성된다 | 버퍼·대상 id 관리 | 떠나는 경로 하나라도 누락 | 다중 뷰 편집기 |
| 4. 공유 목록 + fail-fast | 여러 소비자가 같은 목록을 본다 | 검증 코드 | 조용한 보정은 불일치를 숨김 | 사용자 선언과 자동 추론이 섞일 때 |
| 5. 이중 상태 제거 | 상태의 주인이 하나로 정해진다 | 게이트·응답 전부 교체 | 값 import 로 다시 복사하면 재발 | 모듈 전역 + 인스턴스 상태가 공존할 때 |
| 6. 전역/국소 상태 분리 | 상태마다 수명 범위가 다르다 | 복원 로직에 병합 | 새 전역 필드 추가 시 병합 누락 | 탭·스냅샷 복원 UI |
| 7. URL당 페이지 하나 | 라우팅 도구가 충돌을 오류로 내지 않는다 | 폴더 재배치 | 그룹이 늘면 재발 | 파일 기반 라우팅 + 그룹 폴더 |

**결론**: 먼저 "이 사실의 주인은 누구인가"를 정한다 — 서버·데이터 모델이면 기본, 플랫폼이면 1, 여러 진입점이 공유하는 계약이면 2.\
주인을 정한 뒤에도 사본이 생기는 경로(DOM 읽기·값 import·스냅샷 복원·라우트 그룹)를 막는 것이 3·5·6·7이다.\
불일치를 조용히 보정하지 말고 드러낸다(4) — 보정은 두 번째 진실원을 하나 더 만드는 것이다.
