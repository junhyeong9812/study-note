# issue/cross-cutting/infra/shallow-clone-history-boundary — 정답

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **git 은 커밋과 그 부모의 트리를 비교해 diff 를 만든다. 경계 커밋은 부모가 로컬에 없다.**\
   얕은 clone 은 지정한 깊이까지만 커밋을 받고, 가장 오래된 커밋(경계 커밋)의 목록을 `.git/shallow` 에 적는다.\
   경계 커밋의 부모 객체는 받지 않았으므로 git 은 그 커밋을 부모가 없는 커밋처럼 다룬다 — 빈 트리와 비교하니 파일 전체가 "추가"로 나온다.\
   직접 확인(git 2.43 임시 저장소): 이력의 가장 오래된 커밋의 `show` 가 그 커밋이 실제로 바꾼 줄이 아니라 파일 전체(31줄)를 추가로 표시했다.
   > **얕은 clone(shallow clone)** — 이력을 지정한 깊이까지만 받은 저장소. 경계 커밋 너머의 객체는 없고, 경계 목록은 `.git/shallow` 에 있다.

2. **B 에서 거꾸로 걸은 길이 A 에 닿기 전에 경계에서 끊기면 "조상 아님"이 나온다. 참이 아니다.**\
   배포마다 `fetch --depth=50` 을 하면 깊이 창이 새 커밋 쪽으로 밀린다. 예전 fetch 로 받은 A 의 객체는 그대로 남지만, B 에서 A 까지 잇는 커밋들은 이번 창 밖이라 로컬에 없다.\
   `merge-base --is-ancestor` 는 로컬 그래프만 걷는다. 길이 끊겼으니 "도달 못 함 = 조상 아님"으로 답한다.\
   재현: 커밋 c10→c20 인 저장소를 depth 5 로 다시 받은 뒤 A=c10, B=c20 을 물으면 200 · `not_ancestor` · 빈 목록이 나왔다(실제로는 A 가 B 의 조상).

3. **B 의 조상 순회가 경계에 닿았는지로 가른다.**\
   순회가 경계에 닿지 않았다면 B 의 이력이 로컬에 온전히 있다는 뜻이고, 그 안에 A 가 없으니 "조상 아님"은 참이다.\
   경계에 닿았다면 A 는 경계 너머에 있을 수 있으므로 모른다.\
   다만 B 가 A 의 조상이면(배포를 되돌린 경우) 경계와 무관하게 "A 가 B 의 조상이 아님"이 확실하다 — 그래서 이 경우만 `not_ancestor` 로 살린다.\
   나머지는 `unknown` 으로 답하고 커밋 목록은 비우며 "이 저장소 이력으로는 알 수 없음"을 표시한다.

4. **오류가 아니라 정상 응답처럼 보여서, 소비자가 틀린 것을 알 방법이 없다.**\
   전부 추가된 diff 는 진짜 "새 파일을 만든 커밋"과 모양이 같고, 빈 목록은 "되돌린 배포"와 모양이 같다.\
   상태 코드도 200 이므로 화면은 그럴듯한 거짓을 그대로 보여 준다 — 조용한 실패다.

5. **"모르는 것을 없다고 답한다"는 같은 문장으로 묶인다.**\
   조회 실패를 빈 목록으로 돌려주는 코드([absent-vs-empty](../../data/absent-vs-empty/))도, 얕은 이력에서 끊긴 길을 "조상 아님"으로 돌려주는 git 도 같은 구조다.\
   세 번째 값을 두면 소비자는 그 값을 별도 표시로 다뤄야 한다 — 여기서는 "알 수 없음" 문구와 원격 저장소의 비교 화면 링크를 함께 보였다.
   > **3값 응답** — 참·거짓 외에 "판정 불가"를 따로 두는 응답. 소비자가 세 번째 값을 무시하면 다시 두 값으로 뭉개진다.

6. **판정이 기댄 경계 목록이 판정 도중 바뀌지 않는다는 가정에 기댄다.**\
   배포의 fetch 가 조회 도중 경계를 옮기면, 경계 검사는 옛 목록으로 하고 git 명령은 새 이력을 보게 된다 — 이 사례에서는 실제로 부모 없는 diff 가 다시 200 으로 나갔다.\
   그래서 경계 판정은 git 명령들 앞뒤로 읽은 같은 목록 위에서만 한다([optimistic-read-validation](../../concurrency/optimistic-read-validation/)).

## 문제 구조 (추상화 코드)

### 변형 A — 경계 커밋의 diff 를 그대로 낸다
① 문제 코드
```go
func commitDetail(repo Repo, sha string) (Detail, error) {
    full, err := repo.verifyCommit(sha)          // 객체가 있으면 통과 — 경계 커밋도 있다
    if err != nil { return Detail{}, errNotFound }
    return repo.show(full)                       // 부모 없음 → 빈 트리와 비교 → 파일 전체가 "추가"
}
```
② 고친 코드
```go
func commitDetail(repo Repo, sha string, boundary map[string]bool) (Detail, error) {
    full, err := repo.verifyCommit(sha)
    if err != nil { return Detail{}, errNotFound }
    if boundary[full] {                          // .git/shallow 에 든 커밋 — 부모가 로컬에 없다
        return Detail{}, errParentMissing        // 404 의 별도 갈래 — 소비자는 원격 비교 화면으로 넘긴다
    }
    return repo.show(full)
}
```
깨진 것: "부모가 없다"를 "최초 커밋이다"로 읽었다 — 로컬에 없는 것과 존재하지 않는 것을 구분하지 않았다.

### 변형 B — 끊긴 길을 "조상 아님"으로 단정한다
① 문제 코드
```go
ancestor, err := repo.mergeBaseIsAncestor(from, to)        // merge-base --is-ancestor
if err != nil { return nil, err }
if !ancestor {
    return Range{Relation: "not_ancestor", Commits: []Commit{}}, nil   // 끊긴 이력도 여기로
}
```
② 고친 코드
```go
func relationBetween(repo Repo, from, to string, boundary map[string]bool) (string, error) {
    if ok, err := repo.mergeBaseIsAncestor(from, to); err != nil || ok {
        return "ancestor", err
    }
    hit, err := repo.walkHitsBoundary(to, boundary)   // to 의 조상 목록(rev-list)에 경계 커밋이 있나
                                                      // 출력 상한에 걸려 끝까지 못 봤으면 "닿았다"로 본다
    if err != nil { return "", err }
    if !hit {
        return "not_ancestor", nil                    // 이력이 온전하다 — 믿는다
    }
    if back, err := repo.mergeBaseIsAncestor(to, from); err != nil || back {
        return "not_ancestor", err                    // 확실한 되돌림
    }
    return "unknown", nil                             // 목록 없음 · rangeComplete=false
}
```
깨진 것: 로컬 그래프에서 "도달 못 함"이 "존재하지 않음"을 뜻한다고 가정했다 — 얕은 저장소에서는 경계 너머가 비어 있을 뿐이다.

## 검증 기록
- 2026-11-23: 사건 기록·명세·리뷰 기록·수정 전후 코드 대조·추상화. 경계 커밋 diff(31줄 추가 표시)는 git 2.43 임시 저장소 실측, 조상 오판은 리뷰한 커밋을 빌드해 임시 저장소(c10→c20, depth 5)로 재현한 값(200 · `not_ancestor`)이다. 범위 목록에 경계 커밋이 들어 있으면 그 너머가 잘렸을 수 있어 "온전함" 표시를 거짓으로 둔 것도 같은 명세에서 정했다.
