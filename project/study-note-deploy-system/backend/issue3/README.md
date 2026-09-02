# issue3 — 콘텐츠 API: 문서 목록과 원문만 준다 (그리는 건 front)

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-backend
- 이슈 #5 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/6

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "선택 / 대안 탈락" 요약          ──▶     각 갈림길: 무엇이 문제였나
>                                          → 무엇을 고민했나 → 그래서 이렇게
> isSafe 한 줄만 인용             ──▶     ContentController 실제 diff 전체 인용
>                                          (ce4f1f5) — 봉투·404·422 판정까지
> 트래버설 용어 던짐             ──▶     그 자리에서 한 줄 풀이
> "빈 본문" 진단은 이미 좋음       ──▶     그대로 살려 서사로 재배치
> ```

---

## 1. 배경 — backend는 왜 HTML을 안 만드나

위키 화면이 필요로 하는 건 두 가지다 — "무슨 문서가 있나"(네비게이션)와 "이 문서 내용은
뭔가"(본문). 여기서 한 가지 설계 결정이 앞서 있었다: **front가 Next.js SSR로 화면을 렌더한다.**

> 용어 — SSR(Server-Side Rendering): 브라우저가 아니라 front 서버가 HTML을 미리 그려서 내려주는 방식.

이 결정 때문에 backend는 **HTML을 만들지 않는다.** md 원문과 메타(주제·문서 종류)만 JSON으로
넘기고, 그걸 화면으로 그리는 일은 front가 한다. 덕분에 "완성된 HTML 파일을 서버 사이에 옮기는"
번거로운 문제가 통째로 사라진다 — backend는 그냥 데이터만 주면 된다.

---

## 2. 갈림길마다의 판단

### 갈림길 (1) — 트리를 누가 만드나: backend vs front

**무엇이 문제였나:** 네비게이션은 보통 폴더 트리 모양이다. 그럼 backend가 트리 JSON을 만들어
주는 게 자연스러워 보인다.

**무엇을 고민했나:** 트리의 모양(어떻게 접고, 어떤 순서로 보이고, 무엇을 그룹으로 묶는지)은
**화면의 관심사**다. 화면 구조가 바뀔 때마다 backend를 고쳐야 한다면 경계가 잘못 그어진 것이다.

**그래서 이렇게 했다:** backend는 **평면 목록**(전 문서의 경로·주제·종류)만 준다. 그 평면
목록으로 트리를 조립하는 건 front의 몫이다. "화면 관심사는 front 한 곳에"라는 원칙을 지켰다.

> 참고: 이 결정은 이후 issue7에서 부분적으로 번복된다 — "트리는 sync 때만 변하니 backend가
> 만들어 캐시해도 된다"는 새 근거가 생겨 `/api/tree`가 추가된다. 하지만 이 시점의 판단은 평면 목록이다.

### 갈림길 (2) — HTML 생성 (탈락)

**무엇이 문제였나:** backend가 md를 HTML로 렌더해서 주면 front가 편하지 않을까?

**그래서 이렇게 했다:** 안 한다. 렌더는 SSR 결정에 따라 front 책임이고, backend가 HTML을 만들면
화면 관심사가 다시 backend로 넘어온다. backend는 md 원문(`markdown` 필드)만 준다.

**결론적으로 API는 둘:**
- `GET /api/docs` — 전 문서의 메타 목록(경로·주제·종류). front가 이걸로 트리를 만든다.
- `GET /api/doc?path=` — 한 문서의 md 원문 + 메타.

---

## 3. 구현 워크플로우 — 원문 요청의 관문

`/api/doc`은 파일 경로를 받아 원문을 준다. 여기서 **경로 검사**가 핵심 보안 장치다.

> 용어 — 경로 트래버설(path traversal): `path=../../etc/passwd.md`처럼 `..`(상위 폴더로 이동)를
> 섞어, 허용된 폴더 **밖으로 기어 올라가** 아무 파일이나 읽어내려는 공격.

```
GET /api/doc?path=cs/lsm-tree/2-summary.md
  ▼
[경로 검사] .md 인가? 절대경로(/)·~ 없나? 경로 조각에 .. / .git 없나?  → 아니면 422 invalid_request
  ▼
git 볼륨에서 파일 읽기 → 없으면 404 not_found  (I/O 장애는 500 봉투 — issue5 리뷰 후 구분)
  ▼
{"success":true,"data":{"path","topic","subject","doc_kind","form","markdown":"# ..."}}
```

LAN 전용이라도 backend는 이후 front를 통해 외부 요청을 받게 되므로, 트래버설은 처음부터 닫는다.

> 용어 — 봉투(envelope): 모든 응답을 `{"success":..., "data":.../"error":...}`라는 같은 껍데기로
> 감싸는 규약. front가 성공/실패를 한 가지 방식으로 처리하게 해준다.

---

## 4. 코드 변경 (핵심)

`src/main/kotlin/xyz/junproject/backend/content/ContentController.kt` (커밋 ce4f1f5):
```kotlin
@GetMapping("/doc")
fun getDoc(@RequestParam path: String, ...): ResponseEntity<Map<String, Any?>> {
    val requestId = incomingId ?: requestLog.newRequestId()
    if (!isSafe(path)) {
        requestLog.log(requestId, "doc rejected: unsafe path $path", "warning")
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(Envelope.fail("invalid_request", detail = "path must be a repo-relative .md"))
    }
    val content = try {
        git.readFile(path)
    } catch (_: Exception) {
        requestLog.log(requestId, "doc not found: $path", "warning")
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Envelope.fail("not_found"))
    }
    val meta = DocClassifier.classify(path)
    requestLog.log(requestId, "doc ok $path ${content.length}chars")
    return ResponseEntity.ok(Envelope.ok(mapOf(
        "path" to meta.path, "topic" to meta.topic, "subject" to meta.subject,
        "doc_kind" to meta.docKind, "form" to meta.form, "markdown" to content,
    )))
}

/** 경로 트래버설 차단 — repo 상대 .md 경로만 허용 */
internal fun isSafe(path: String): Boolean =
    path.endsWith(".md") && !path.startsWith("/") && !path.startsWith("~") &&
    !path.split("/").any { it == ".." || it == ".git" } && path.isNotBlank()
```
`isSafe`는 "허용 목록"이 아니라 "금지 목록"에 가깝지만, `.md`로 끝나야 하고 경로 조각 어디에도
`..`·`.git`이 없어야 한다는 조건이 트래버설의 핵심 통로를 막는다. (이 시점의 404/422 구분은
issue5 리뷰에서 "파일 부재 = 404, I/O 장애 = 500"으로 더 정밀해진다.)

목록 API `GET /api/docs`는 `git.allMarkdown()`으로 전 문서 경로를 훑고, 각 경로를
`DocClassifier.classify`로 분류해 메타만 배열로 돌려준다.

---

## 5. 구현 중 마주친 문제 — 한글 경로 문서를 조회하니 본문이 빈 문자열

**상황:** 스모크에서 한글 경로 문서를 조회했더니 원문이 비어 있었다.
```
$ curl --get .../api/doc --data-urlencode "path=programmers/힙/01-더 맵게/1-question.md"
{"success":true,"data":{...,"doc_kind":"question","form":"chapter","markdown":""}}
                                                                    ^^^^^^^^^^^ 비어 있음
```

**무엇을 고민했나:** issue2에서 한글 경로 때문에 이미 한 번 데였던 터라, "또 인코딩 문제인가"
싶었다. 하지만 코드를 고치기 전에 **데이터 실태부터** 확인하기로 했다 — 원본 쪽으로 한 단계씩
거슬러 올라가며.

**진단:**
```
① 서버의 clone 볼륨:  wc -c ".../1-question.md"  →  0        (0바이트)
   같은 폴더의 ES 청크 수:  _count path prefix    →  count: 0  (색인도 0개 — 일관됨)
② 내 로컬 원본:       wc -c "programmers/힙/01-더 맵게/1-question.md"  →  0
   0바이트 파일 전수:  find programmers -name '*.md' -size 0 | wc -l   →  94   (전부!)
③ rename 이전 이력:   git show cbc84bb:"programmers/힙/01-더 맵게/problem.md" | wc -c  →  0
```

③이 결정타였다 — 우리가 rename(`problem.md`→`1-question.md`)하기 **이전 커밋에서도 0바이트**였다.
즉 시스템 어디에서도 내용을 잃지 않았고, **programmers 94개는 원래부터 안 쓴 빈 자리표(placeholder)**였다.

**어떻게 고쳤나:** 고칠 게 없었다(결함이 아니다). 색인 파이프라인은 빈 파일을 "청크 0개 → 건너뜀"으로
이미 정상 처리하고 있었다(①에서 확인). API도 있는 그대로 빈 `markdown`을 돌려준 것뿐이다.

**교훈:** "버그처럼 보이는 것"의 절반은 데이터 실태다. 코드를 고치기 전에 **서버 사본 → 로컬
원본 → git 이력** 순서로 거슬러 확인하면 멀쩡한 코드를 고치는 헛수고를 막을 수 있다. 특히
③처럼 "우리 작업 이전에도 그랬나"를 이력으로 확정하는 단계가 중요하다 — 우리 rename이 내용을
날렸을 가능성을 배제해준다.

---

## 6. 결론

616건 목록 조회, 한글 경로 조회, 트래버설 요청 422 거절, 실문서 6037자 서빙 확인. PR: #6
