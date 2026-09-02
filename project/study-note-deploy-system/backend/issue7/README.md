# issue7 — /api/tree: "트리는 sync 때만 변한다"로 한 번 기각했던 결정을 뒤집다

- 이슈 #12 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/14

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "기각을 뒤집었다"고 결론만 서술   ──▶     왜 기각했나 → 무엇이 관찰을 바꿨나
>                                           → 왜 이번엔 채택인가 (번복의 3단 서사)
> snake_case 수정을 diff만 제시     ──▶     [기존 흐름]↔[변경 흐름] 나란히 +
>                                           스모크가 어떻게 잡았는지까지
> is_subject·lazy 등 용어 던짐      ──▶     그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 한 번 기각했던 결정을 되짚은 기록

트리 API(왼쪽 사이드바에 폴더 구조를 펼쳐 보여줄 데이터)는 issue5의 게이트 리뷰에서 **한 번
기각됐던** 기능이다. 그때의 판단은 이랬다.

```
[issue5의 기각 논리]
  backend는 "평면 목록"만 준다 (/api/docs 가 문서 경로 배열을 반환)
  front가 그 경로들을 조립해서 트리 모양을 만든다
  근거: "화면 구조(네비게이션 모양)가 바뀔 때마다 backend를 고치긴 싫다"
```

그런데 게이트 리뷰 도중 사용자가 한 가지를 다시 짚었다. **트리는 문서가 바뀔 때만 변한다.**
그리고 문서가 바뀌는 시점은 딱 하나 — sync(원격 저장소를 당겨와 색인하는 그 순간)뿐이다.
그렇다면 매 요청마다 조립할 필요도, front가 매번 조립할 필요도 없다. **backend가 sync 한 번에
트리를 만들어 캐시에 얹어두면**, 그 뒤로는 캐시를 그대로 내려주면 끝이다.

여기서 "기각을 뒤집는 것"이 문제였다. 한 번 내린 결정을 가볍게 번복하면 나중에 왜 그렇게 됐는지
아무도 모른다. 그래서 **이전 기각이 왜 틀리지 않았는지**부터 정리했다. 이전 기각의 근거는
"화면 구조가 바뀔 때마다 backend 수정"이었다. 그건 backend가 **네비게이션 모양**(어떤 순서로,
어떤 그룹으로 보일지 같은 표현)을 만들 때 성립하는 걱정이다. 이번에 만드는 건 모양이 아니라
**폴더 구조 그 자체**다 — 리프(leaf) 폴더가 곧 하나의 주제이고, 그 안에 단일 문서가 있거나
1/2/3 챕터 문서가 들어 있다. 이건 화면이 어떻게 생겼든 변하지 않는, git 저장소의 사실이다.
그래서 "표현은 여전히 front, 구조라는 사실만 backend"로 경계를 다시 그으니 번복이 아니라
정합이 됐다.

> 용어 — 리프(leaf) 폴더: 트리에서 더 이상 하위 폴더가 없는 맨 끝 폴더. 여기서는 "그 아래로는
> 문서만 있고 하위 폴더가 없는 폴더 = 하나의 주제(subject)"라는 규칙으로 썼다.

곁가지로 "flyway 같은 걸로 트리 이력을 추적하면 되지 않나"라는 아이디어도 나왔는데 부적합했다.

> 용어 — flyway: **DB 스키마 마이그레이션** 도구(테이블 구조 변경을 버전으로 관리). 트리는
> DB에 저장되는 게 아니라 git 저장소의 파생물이라 flyway의 대상이 아니다.

트리는 DB에 없고 git의 파생물이다. 그래서 **트리에 그 트리를 만든 커밋 해시(commit_sha)를
태깅**해두면 "이 트리 = 이 커밋"이 되고, 이력 추적은 git이 공짜로 해준다. 별도 추적 장치가 필요 없다.

---

## 2. 구현 워크플로우 — 트리는 언제 만들어지고 언제 그대로 나가나

핵심 원칙은 하나다. **트리를 다시 만드는 유일한 순간은 "sync가 성공했을 때"뿐**이다.

```
[sync 성공 경로 — 트리가 갱신되는 유일한 지점]
  push → /api/deploy → sync 수행 → (전량 성공) → tree.rebuild(headSha)
                                    실패한 sync는 여기 도달 못 함 → 트리 안 바뀜
                                                                     └ 낡은 sha의 트리가
                                                                       남는 게 아니라
                                                                       "직전 성공 트리" 유지

[요청 경로 — 캐시를 그대로 내려줌]
  GET /api/tree → 캐시 있음 → {commit_sha, tree} 그대로 반환 (조립 없음)
                → 캐시 없음(재시작 직후) → 현재 clone의 HEAD 기준 lazy 생성 후 캐시
```

> 용어 — lazy 생성: "필요해지는 첫 순간까지 미뤘다가 그때 한 번 만드는" 방식. 서버가 재시작하면
> 메모리 캐시가 비므로, 그 뒤 **첫 GET 요청**이 올 때 clone된 저장소 기준으로 트리를 만들어 채운다.

실제로 `tree.rebuild(...)` 호출은 sync가 전량 성공한 뒤, `last_sha`를 전진시키기 직전에 딱 한 번
끼어든다. 아래는 sync 성공 처리에 이 한 줄이 추가된 실제 diff다.

파일: `src/main/kotlin/xyz/junproject/backend/usecase/SyncService.kt` (커밋 `65198ef`)

```diff
 class SyncService(
     private val git: GitRepository,
     private val indexing: IndexingService,
+    private val tree: TreeService,
     private val requestLog: RequestLog,
 ) {
...
             if (effectiveFull) indexing.deleteStale(requestId, headSha)   // 고아 정리 (B7)
+            tree.rebuild(requestId, headSha)   // 트리는 sync 성공 시에만 변한다 (#12)
             writeLastSha(headSha)      // 전량 성공 후에만 전진 (D5-3)
```

캐시와 lazy 생성은 `TreeService`가 맡는다. `@Volatile`로 잡은 캐시 한 칸을 두고, 없으면
`synchronized`로 한 번만 만든다(재시작 직후 요청이 동시에 여러 개 와도 중복 생성 방지).

파일: `src/main/kotlin/xyz/junproject/backend/usecase/TreeService.kt` (커밋 `65198ef`)

```kotlin
@Service
class TreeService(private val git: GitRepository, private val requestLog: RequestLog) {

    data class CachedTree(val commitSha: String, val tree: TreeBuilder.Node)

    @Volatile private var cached: CachedTree? = null

    fun rebuild(requestId: String, commitSha: String) {
        val tree = TreeBuilder.build(git.allMarkdown())
        cached = CachedTree(commitSha, tree)
        requestLog.log(requestId, "tree rebuilt sha=$commitSha")
    }

    /** 캐시 반환 — 없으면 현재 clone 기준으로 생성 (sha는 clone의 HEAD) */
    fun get(requestId: String): CachedTree {
        cached?.let { return it }
        synchronized(this) {
            cached?.let { return it }
            val headSha = git.currentHead()
            val tree = TreeBuilder.build(git.allMarkdown())
            return CachedTree(headSha, tree).also {
                cached = it
                requestLog.log(requestId, "tree built lazily sha=$headSha")
            }
        }
    }
}
```

실제 트리를 만드는 `TreeBuilder`는 domain 계층의 **순수 함수**다 — 경로 문자열 목록을 받아
중첩 노드를 돌려줄 뿐, git도 ES(엘라스틱서치)도 모른다. 그래서 테스트를 문자열 목록만 넘겨
끝낼 수 있다(외부 시스템 없이 검증).

파일: `src/main/kotlin/xyz/junproject/backend/domain/TreeBuilder.kt` (커밋 `65198ef`)

```kotlin
object TreeBuilder {
    data class DocRef(val path: String, val docKind: String, val form: String)
    data class Node(
        val name: String,
        val path: String,                       // repo 상대 폴더 경로 ("" = 루트)
        val docs: List<DocRef>,                 // 이 폴더 직속 문서
        val children: List<Node>,               // 하위 폴더 (이름순)
    ) {
        val isSubject: Boolean get() = docs.isNotEmpty() && children.isEmpty()   // 리프 폴더 = 주제
    }

    fun build(paths: List<String>): Node { ... }   // 경로를 depth별로 partition → 재귀 조립
}
```

컨트롤러는 캐시를 받아 봉투(envelope — 모든 응답을 `{success, data}` 형태로 감싸는 공통 포장)에
`commit_sha`와 `tree`를 담아 내려준다.

파일: `src/main/kotlin/xyz/junproject/backend/api/ContentController.kt` (커밋 `65198ef`)

```kotlin
@GetMapping("/tree")
fun tree(@RequestHeader("X-Request-Id", required = false) incomingId: String?):
        ResponseEntity<Map<String, Any?>> {
    val requestId = requestLog.acceptOrIssue(incomingId)
    val cached = treeService.get(requestId)
    return ResponseEntity.ok(Envelope.ok(mapOf(
        "commit_sha" to cached.commitSha, "tree" to cached.tree)))
}
```

응답 예시:

```
GET /api/tree → {"success":true,"data":{"commit_sha":"ecf910e1...","tree":{
  "name":"", "children":[ {"name":"cs", "docs":[...index.md...], "children":[
      {"name":"systems","children":[{"name":"lsm-tree","is_subject":true,
        "docs":[{"path":"...","doc_kind":"question"},{"doc_kind":"summary"},{"doc_kind":"answer"}]}...]}]}...]}}}
```

---

## 3. 구현 중 마주친 문제 — 트리 JSON만 camelCase로 새어 나갔다

### 무엇이 문제였나

스모크(배포 직후 실제 엔드포인트를 찔러 확인하는 최소 점검) 스크립트가 트리를 파싱하다 터졌다.

```
$ curl .../api/tree | python3 -c "... doc[\"doc_kind\"] ..."
KeyError: 'doc_kind'
```

응답을 열어보니 필드가 `"doc_kind"`·`"is_subject"`가 아니라 `"docKind"`·`"isSubject"`
(camelCase — 단어를 붙이고 중간을 대문자로 구분하는 표기)로 나가고 있었다. 우리 API 계약은
전부 snake_case(`doc_kind`·`chunk_no`처럼 밑줄로 구분)로 통일돼 있는데(/api/docs·/api/search가
그렇게 준다) **트리만 달랐다.**

### 무엇을 고민했나

원인은 직렬화 방식의 차이였다. 다른 API는 응답을 `mapOf("doc_kind" to ...)`처럼 **손으로**
조립해서 필드명을 직접 정한다. 그런데 트리는 Kotlin의 data class(`DocRef(val docKind: ...)`)를
Jackson(스프링이 객체를 JSON으로 바꿔주는 라이브러리)에 **그대로** 던졌다. 그러니 필드명이
코드 내부 관례(camelCase)로 새어 나간 것이다.

```
[기존 흐름]                              [변경 흐름]
data class DocRef(val docKind)          data class DocRef(
  → Jackson 자동 직렬화                    @get:JsonProperty("doc_kind") val docKind
  → "docKind" (코드 관례가 계약으로 샘)   )
                                          → Jackson이 지정 이름을 씀
                                          → "doc_kind" (계약을 명시적으로 고정)
```

자동 직렬화는 편하지만 **외부 계약을 코드 내부 관례에 묶어버린다.** 나중에 코드 필드명을
리팩토링하면 계약(=front가 의존하는 필드명)이 조용히 깨진다. 그래서 "편하니까 자동으로 두자"가
아니라 "계약이 되는 필드는 이름을 명시적으로 선언한다"를 택했다.

### 그래서 이렇게 했다

`@get:JsonProperty`로 계약 필드명을 코드에 고정했다.

파일: `src/main/kotlin/xyz/junproject/backend/domain/TreeBuilder.kt` (커밋 `b5be35e`)

```diff
 package xyz.junproject.backend.domain
+
+import com.fasterxml.jackson.annotation.JsonProperty

 object TreeBuilder {

-    data class DocRef(val path: String, val docKind: String, val form: String)
+    data class DocRef(
+        val path: String,
+        @get:JsonProperty("doc_kind") val docKind: String,   // API 계약은 snake_case 통일
+        val form: String,
+    )
     data class Node(
         ...
     ) {
+        @get:JsonProperty("is_subject")
         val isSubject: Boolean get() = docs.isNotEmpty() && children.isEmpty()   // 리프 폴더 = 주제
     }
```

이 사건에서 얻은 교훈이 하나 더 있다. 스모크 스크립트가 기대 필드명(`doc_kind`)을 하드코딩해
파싱한 덕에 계약 불일치가 **즉시** 드러났다. 스모크는 "200이 떴나"만 보지 말고 **응답 몸통을
실제로 파싱**해야 한다 — 200은 뜨는데 필드명이 틀린 이런 함정을 잡아주는 건 파싱뿐이다.

---

## 4. 결론

실기동 결과, 트리의 루트 자식은 재구조화한 버킷 8개(cs·practice·project·lab·portfolio·
reference·templates·세미나)로 나왔고, lsm-tree가 `is_subject=true`로 `[question, summary,
answer]` 세 문서를 담았다. front는 이 트리를 그대로 그리기만 하면 된다.

정리하면, 한 번 기각했던 기능을 되살리되 그 근거("표현은 front, 구조라는 사실만 backend")를
명시적으로 남겼고, 트리를 sync 성공 시점에만 만들도록 묶어 "언제 변하는지"를 결정론적으로
확정했다. 24건 green. PR #14
