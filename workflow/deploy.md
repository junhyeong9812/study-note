# deploy — 서비스 push가 재배포되기까지 (ci-cd)

```
[GitHub] 서비스 리포 main push
   │  Actions: curl (X-Deploy-Secret + {service, commit_sha, request_id})  — 빌드 없음
   ▼
[front] POST /api/deploy — 4KB 상한·requestId 전파·비밀 패스스루(무저장)
   ▼
[ci-cd master :15000  (.9 — docker.sock 없음: 접수·라우팅만)]
   ├─ 시크릿(상수시간·fail-closed) → 401
   ├─ commit_sha hex 검증 → 422 (로그 주입·엉터리 202 차단)
   ├─ 서비스 allowlist(env 고정 열거) → 422
   ├─ 서비스별 single-flight → 진행 중이면 명시적 409 (무음 유실 금지)
   └─ 202 + 백그라운드로 해당 호스트 agent 호출
        ▼
[ci-cd agent :15001  (각 호스트 — docker.sock·저장소 마운트는 여기만)]
   ├─ 디렉토리 allowlist(env) + sha 재검증 + single-flight
   ├─ git fetch(depth 50) + reset --hard <sha>   ← 설정(compose)도 함께 도착
   ├─ docker compose up -d --build <대상 서비스만>  ← 호스트 재빌드 (전달 채널 = git 하나)
   └─ 배포 후 헬스 폴링(90s) — compose 성공 ≠ 서비스 정상
   결과 → master 이력(/status, 최근 50 — 롤백 참고용 sha 축적)
```

**절차 핵심**: "배포된 것 = 그 커밋"이 항상 성립(git 단일 채널). 실행 표면은 3중
allowlist(서비스·디렉토리·sha 형식)로 고정 열거 밖을 못 벗어난다.
