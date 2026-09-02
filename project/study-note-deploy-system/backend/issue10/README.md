# issue10 — 트리 노드에 prev 링크, 그리고 "머지는 됐는데 배포가 조용히 안 나가던" 사건

- 이슈 #21 · PR: #23

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "front가 경로를 잘라 계산하던 걸       ──▶   왜 문자열 자르기가 나빴나 → 왜 트리 생성
>  prev로 바꿈" (한 줄 요약)                    시점에 넣기로 했나 → 실제 재귀 diff
> 401 사건을 문단으로만 서술          ──▶   진단 과정을 [증상→좁힘→원인] ASCII로
> "-f가 없어 초록불 위장" 던짐         ──▶   그 자리에서 curl -f / silent failure 풀이
> ```
> 표현도 순화: "prev를 박아넣어" → "prev를 채워".

---

## 1. 배경 — 뒤로가기를 누가 계산할 것인가

front(위키 화면)에는 문서를 열었다가 **상위 폴더로 돌아가는 "뒤로가기"** 가 있다. 이걸
누가 계산하느냐가 이 이슈의 질문이었다.

기존 front는 지금 열려 있는 경로 문자열을 직접 잘라서 상위 경로를 만들었다. 예를 들어
`cs/db/lsm-tree`를 보고 있으면 마지막 `/lsm-tree`를 문자열에서 떼어 `cs/db`를 만드는
식이다. 동작은 하지만 두 가지가 불편했다.

- **front가 경로 규칙을 알아야 한다.** 구분자가 `/`라는 것, 루트는 빈 문자열이라는 것을
  front 코드가 가정하고 자른다. 경로 규칙은 원래 backend(트리를 만드는 쪽)의 몫인데
  그 지식이 front로 새어 나가 있었다.
- **자르기는 깨지기 쉽다.** 끝에 슬래시가 붙거나, 경로에 특수한 문자가 들어오면 자르기
  로직이 어긋난다. "문자열을 파싱해서 구조를 복원"하는 코드는 항상 예외 처리가 는다.

> 용어 — 트리(tree): 폴더/문서를 상위-하위 관계로 담은 계층 구조. backend는 sync가
> 성공할 때 전체 문서 경로 목록으로 이 트리를 한 번 만들어 front에 내려준다(issue7).

---

## 2. 결정 — 계산하지 말고, 만들 때 넣어둔다

고민의 핵심은 "상위 경로를 **매번 계산**할 것인가, **한 번 저장**할 것인가"였다.
트리는 sync가 성공할 때 딱 한 번 만들어진다. 그 순간 각 노드는 자기가 어느 폴더의
자식인지 이미 알고 있다 — 부모가 자식을 만들면서 재귀로 내려가기 때문이다. 그렇다면
**만드는 그 순간에 각 노드에 "내 상위 폴더 경로"(prev)를 채워두면**, front는 아무것도
계산할 필요 없이 노드에 붙어 온 링크를 그대로 따라가면 된다.

`TreeBuilder`는 입력(경로 목록)만으로 출력(트리)이 정해지는 순수 함수라, 이 변경은
재귀 함수에 인자 하나를 추가하는 작은 일이었다.

`src/main/kotlin/xyz/junproject/backend/content/domain/TreeBuilder.kt`

```kotlin
// [기존] Node에 prev 없음, buildNode는 name·path만 넘김
data class Node(
    val name: String,
    val path: String,                       // repo 상대 폴더 경로 ("" = 루트)
    val docs: List<DocRef>,
    val children: List<Node>,
)
...
private fun buildNode(name: String, path: String, metas: List<DocMeta>, depth: Int): Node {
    ...
    val childPath = if (path.isEmpty()) childName else "$path/$childName"
    buildNode(childName, childPath, childMetas, depth + 1)
    ...
    return Node(name, path, docs, children)
}
```

```kotlin
// [변경] Node에 prev 추가, 자식의 prev = "지금 내 path"
data class Node(
    val name: String,
    val path: String,                       // repo 상대 폴더 경로 ("" = 루트)
    val prev: String?,                      // 상위 폴더 경로 — 루트는 null (#22: front 뒤로가기용)
    val docs: List<DocRef>,
    val children: List<Node>,
)
...
private fun buildNode(name: String, path: String, prev: String?, metas: List<DocMeta>, depth: Int): Node {
    ...
    val childPath = if (path.isEmpty()) childName else "$path/$childName"
    buildNode(childName, childPath, prev = path, metas = childMetas, depth = depth + 1)
    ...
    return Node(name, path, prev, docs, children)
}
```

핵심은 `buildNode(..., prev = path, ...)` 한 줄이다 — **자식을 만들 때 "지금 내 경로"를
자식의 prev로 넘긴다.** 루트는 상위가 없으니 `prev = null`. front는 노드의 prev만 보고
링크를 만든다.

```
[기존]  front가 매 화면에서 계산
  "cs/db/lsm-tree" ── 문자열 자르기 ──▶ "cs/db"   (front가 / 규칙을 앎)

[변경]  backend가 트리 만들 때 1회 채움
  build(paths)
    └ buildNode(prev=null)                 루트
        └ buildNode(prev="")               cs        (부모 path="")
            └ buildNode(prev="cs")         cs/db
                └ buildNode(prev="cs/db")  cs/db/lsm-tree
  front는 node.prev 를 그대로 링크로 사용   (계산 0)
```

### 같은 PR에 함께 들어간 "시점 조회" (문서 이력)

이 커밋(f4c27da)에는 prev 말고도 **"과거 커밋 시점의 문서 원문 보기"** 가 함께 들어갔다.
`recentCommits`(최근 커밋 목록)와 `readFileAt`(특정 sha 시점의 파일 내용을 `git show`로
읽기)를 포트에 추가하고, `/api/doc?path=…&at=<sha>` 로 그 시점 원문을 준다. 이때도
`at`은 hex 형식(커밋 sha)만 허용해 주입을 막는다.

`src/main/kotlin/xyz/junproject/backend/shared/infra/GitRepository.kt`

```kotlin
override fun readFileAt(sha: String, path: String): String =
    try {
        run("git", "-c", "core.quotepath=off", "show", "$sha:$path")
    } catch (error: IllegalStateException) {
        throw java.io.FileNotFoundException("$sha:$path")   // 부재·잘못된 sha → 404 계약
    }
```

`src/main/kotlin/xyz/junproject/backend/content/api/ContentController.kt`

```kotlin
if (at != null && !at.matches(Regex("^[0-9a-f]{7,64}$"))) {   // 시점 조회 — hex만 (주입 차단)
    return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
        .body(Envelope.fail("invalid_request", detail = "at must be a commit sha"))
}
val content = try {
    if (at != null) git.readFileAt(at, path) else git.readFile(path)
} catch (_: java.io.FileNotFoundException) { ... }
```

---

## 3. 구현 중 마주친 사건 — 머지했는데 운영에 안 나가고 있었다

여기서부터가 이 이슈의 진짜 이야기다. prev 코드는 작았지만, **머지한 변경이 운영
서버에 반영이 안 되고 있었다는 걸** 이 작업에서 발견했다.

**상황:** PR을 머지했고 GitHub Actions는 초록불("success")이었다. 그런데 운영 API를
직접 호출해 보니 트리 노드에 prev가 없었다(값이 None). 방금 넣은 필드가 운영에 없다.

**증상을 좁혀간 순서:**

```
① 운영 /api/tree 실호출     ──▶  prev=None  (내 변경이 라이브에 없다)
② 배포 서버(master) 이력 조회 ──▶ 이 배포가 이력에 아예 없음 (배포가 시작조차 안 됨)
③ Actions 로그를 열어봄      ──▶ 아래 응답 발견
```

```
{"error":{"code":"unauthorized"},"success":false}
http:401                    ← 그런데 Actions 결론은 "success"(초록불)
```

**원인은 두 겹이었다:**

① **배포 시크릿 오등록.** 배포를 부를 때 쓰는 `DEPLOY_SECRET` 값을 시크릿 대장(사람이
보는 md 문서)에서 꺼내면서 `grep`으로 "첫 32자리 hex"를 집었는데, 그게 하필 표의
**첫 행인 `SYNC_SECRET`** 이었다. 그래서 backend·front 리포에 배포용이 아닌 엉뚱한 값이
등록돼 있었고, 배포 서버는 당연히 401(권한 없음)로 거절했다.

② **실패가 초록불로 위장됐다.** 워크플로가 배포를 부를 때 쓴 `curl`에 `-f` 옵션이 없었다.

> 용어 — `curl -f`(`--fail`): 서버가 4xx/5xx로 답하면 curl이 **실패(0이 아닌 종료 코드)**
> 로 끝나게 하는 옵션. 이게 없으면 curl은 401 응답을 "정상적으로 받아왔다"며 성공(0)으로
> 끝나고, 워크플로는 그 단계를 초록불로 지나간다.

즉 배포 요청은 401로 거절당했는데, `-f`가 없어 curl은 성공으로 끝났고, Actions는
초록불이 됐다. **아무도 배포가 한 번도 안 나갔다는 걸 몰랐다** — 전형적인 silent failure
(조용한 실패). 이건 배포 서버 issue3의 "202는 접수일 뿐 배포됨이 아니다"와 정확히 같은
계열의 함정이다: 한 단계가 실패를 삼키면 전체 신호가 거짓이 된다.

**해결:**

```
시크릿을 정본(master 서버의 .env)에서 직접 다시 등록 (backend·front 전 리포)
   │
   └─▶ Actions 재실행 ──▶ 202(접수) ──▶ 75초 뒤 배포 ok ──▶ prev 라이브 확인
```

`curl -f` 추가(초록불 위장 자체를 막는 근본 수정)는 배포 서버(ci-cd) 쪽 워크플로의
남은 수정 목록으로 넘겼다 — 이 리포가 아니라 CI 파이프라인의 문제이기 때문이다.

---

## 4. 결론과 배운 것

prev 자체는 순수 함수에 인자 하나를 더한 작은 변경이었지만, 이 작업의 실제 교훈은 배포
파이프라인에 있었다.

- **시크릿의 정본은 문서가 아니라 "실제 쓰이는 곳"이다.** 사람이 보는 대장(md)은 사본일
  뿐이고, `grep`으로 사본에서 값을 긁으면 표 구조가 조금만 어긋나도 엉뚱한 값을 집는다.
  정본(운영 서버의 .env)에서 직접 등록하는 것이 맞다.
- **파이프라인의 "성공"은 각 단계가 실패를 전파해야 의미가 있다.** 실패를 삼키는 단계
  하나(`curl -f` 누락)가 전체 신호를 거짓으로 만들었다. "Actions 초록불"을 증거로 치지
  않고 운영 실값·배포 이력·http 코드로 좁힌 것이 원인을 잡은 핵심이었다.

PR #23
