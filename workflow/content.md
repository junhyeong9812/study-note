# content — 트리·문서·히스토리

```
[트리]   GET /api/tree ──▶ 캐시 반환 {commit_sha, tree}
         · 트리는 sync 성공 시에만 재생성(그때만 변하므로) · 재시작 후엔 첫 요청 때 lazy 생성
         · 노드: {name, path, prev(상위 경로 — 뒤로가기 링크), docs[], children[], is_subject}
         · 리프 폴더 = 주제(subject) — 안은 1/2/3 챕터 또는 단일 post

[문서]   GET /api/doc?path=cs/…/2-summary.md [&at=<sha>]
         ├─ 경로 검증: .md·상대경로만, ..·.git 차단 (트래버설)
         ├─ at 있으면 hex 검증 → git show <sha>:<path> (그 시점의 내용)
         └─ 원문 markdown + 메타 반환 — HTML 렌더는 front(SSR)

[이력]   GET /api/history ──▶ git log 최근 30 {sha, message, at}
```

**절차 핵심**: 문서 내용의 정본은 git — backend는 그것을 "읽어줄" 뿐, 별도 저장소를
만들지 않는다. 트리는 파생물이라 캐시하고, 원문은 매번 git에서.
