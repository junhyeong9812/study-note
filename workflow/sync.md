# sync — push가 검색 가능해지기까지

```
[GitHub] study-note main push
   │  Actions: curl (비밀 헤더 + {commit_sha, request_id})
   ▼
[front] POST /api/sync ── 검증 없음, 4KB 상한만 — 비밀 패스스루(판정은 소유자에게)
   ▼
[backend] POST /internal/sync
   ├─ ① 시크릿 검증(상수시간) ── 실패 → 401
   ├─ ② 멱등 판정: commit_sha == 마지막 처리 SHA → 200 {"skipped":"duplicate"}
   │                처리 중 + 같은 SHA → skip / 다른 SHA → 409
   └─ ③ 202 반환 + 백그라운드 파이프라인 시작
        ├─ git fetch + reset (원격 HEAD로 수렴 — sha는 트리거 힌트)
        ├─ diff prev..HEAD (md만; prev 없거나 해석 불가 → 전체 색인 강등)
        ├─ 파일마다: 기존 청크 삭제 → h2 청킹(8KB 초과 시 h3→문단) → BGE-M3 임베딩
        │            → ES bulk(_id=path#chunk_no) → ★ count 대조 (silent failure 차단)
        ├─ (full일 때) 이번 SHA 아닌 문서 삭제 — 고아 정리
        ├─ 트리 재생성(+commit_sha 태깅) — 트리는 이때만 변한다
        └─ 전량 성공 후에만 last_sha 전진 → 실패 재시도 = 자동 재처리
```

**절차 핵심 3가지**
1. **git diff가 색인 입력의 정본** — 스캔·mtime이 아니라 커밋 차이.
2. **성공 후에만 전진** — 부분 실패가 다음 트리거에서 저절로 재처리된다(멱등).
3. **넣은 만큼 들어갔는지 센다** — "에러 없이 돌았다"를 완료로 안 친다.
