# issue9 — 자동 배포 호출 편입, 그리고 바인딩과 헬스체크가 부딪친 사건

- 이슈 #18 · PR: https://github.com/junhyeong9812/study-note-deploy-system-backend/pull/19

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "자동 배포 편입" 3문단 요약        ──▶     왜 git-pull 방식인가 → 실제 워크플로
>                                           yml → 배포 흐름 플로우차트
> 첫 배포 실패를 서술로만 언급        ──▶     증상 로그 → 진단 → 원인(바인딩) →
>                                           교정을 단계로, before/after 바인딩 diff
> BIND_ADDR·fail-closed 용어 던짐     ──▶     그 자리에서 한 줄 풀이
> ```

---

## 1. 무엇을 만들었나 — main에 push하면 자동으로 배포되게

목표는 llm·front와 동일한 방식이었다. main 브랜치에 push가 되면 GitHub Actions가 **배포
서버에 "배포해줘"라고 호출만** 하고, 실제 빌드는 대상 호스트(.158 에이전트)가 한다.

여기서 결정할 게 하나 있었다 — **이미지를 미리 빌드해 밀어 넣을 것인가(ghcr push), 아니면
호스트가 git pull 후 직접 빌드할 것인가.** ci-cd(배포 서버)가 git-pull 방식으로 정리돼 있었고,
backend는 gradle 빌드라 "호스트에서 빌드하면 느리지 않을까"가 걱정이었다.

> 용어 — ghcr: GitHub Container Registry. 빌드한 도커 이미지를 올려두는 저장소. "push 방식"은
> Actions가 이미지를 만들어 여기 올리고 호스트가 내려받는 흐름을 말한다.
> 용어 — gradle: JVM(코틀린/자바) 빌드 도구. 의존성을 받아 컴파일·패키징하는데, 처음엔 오래
> 걸린다.

실제로 재보니 걱정만큼 느리지 않았다. **도커 레이어 캐시** 덕분에 증분 빌드가 38초로 끝났다.

> 용어 — 도커 레이어 캐시: 도커 이미지는 여러 "층(layer)"으로 쌓이는데, 바뀌지 않은 층은
> 다시 만들지 않고 재사용한다. 의존성을 받는 층은 `build.gradle`이 안 바뀌면 그대로 재사용되니,
> 코드만 고친 배포는 컴파일 층만 새로 만들면 된다.

이 결과로 git-pull 방식을 택했다. Actions는 호출만 하니 가볍고, 캐시가 빌드 비용을 눌러준다.

Actions 워크플로는 15줄짜리 "호출 전용"이다.

파일: `.github/workflows/deploy.yml` (커밋 `7cb6190`, 신규)

```yaml
name: deploy
on:
  push:
    branches: [main]
jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: trigger deploy (빌드는 대상 호스트에서 — git pull 방식)
        run: |
          curl -sS -X POST "https://www.junproject.xyz/api/deploy" \
            -H "X-Deploy-Secret: ${{ secrets.DEPLOY_SECRET }}" \
            -H "Content-Type: application/json" \
            -d "{\"service\": \"backend\", \"commit_sha\": \"${{ github.sha }}\", \"request_id\": \"gh-${GITHUB_RUN_ID}\"}" \
            -w "\nhttp:%{http_code}\n"
```

전체 배포 흐름은 이렇다.

```
main push
   │
   ▼
GitHub Actions (deploy.yml) ── POST /api/deploy {service:backend, commit_sha}
   │                                (X-Deploy-Secret 헤더로 인증)
   ▼
ci-cd master → agent(.158) 라우팅
   │
   ▼
agent: git pull → gradle 빌드(레이어 캐시로 증분 38s) → docker compose up
   │
   ▼
agent: 배포 후 헬스 URL 폴링 → 200 이어야 "deploy ok"   ← 여기서 사건 발생 (§2)
```

---

## 2. 첫 자동 배포가 "정상인데 unhealthy"로 실패한 사건

### 증상

첫 자동 배포에서 agent가 backend를 배포한 뒤 헬스 확인 단계에서 실패로 찍혔다. 그런데
backend 자체는 멀쩡히 돌고 있었다.

### 진단 — 왜 backend만 이랬나

backend 리포에는 다른 서비스에 없는 특이점이 있다. 보안 리뷰(issue5) 때 도입한
**fail-closed 바인딩**이다.

> 용어 — 바인딩: 서버가 "어느 주소로 귀를 열지" 정하는 것. `127.0.0.1`은 자기 자신(루프백)만,
> LAN IP는 그 주소로만 연다.
> 용어 — fail-closed: "설정이 빠지면 열어두는(open) 게 아니라 아예 안 뜨게(closed)" 하는
> 안전 기본값. 여기서는 배포 `.env`에 `BIND_ADDR`가 없으면 컨테이너가 기동을 거부한다.

파일: `docker-compose.yml` (커밋 `8ea60a4`)

```diff
-      - "8090:8090"          # LAN — front가 호출
+      # 전제: 호스트는 사설 LAN 단일 인터페이스(공유기 뒤). 공인 인터페이스가 생기면 BIND_ADDR로 제한 (리뷰 B14)
+      - "${BIND_ADDR:?set-in-env}:8090:8090"   # fail-closed — 배포 .env가 LAN 주소 지정 (감사 반영)
```

`${BIND_ADDR:?set-in-env}`는 "이 변수가 비어 있으면 기동을 실패시켜라"라는 표기다. 그리고
그 값으로 앱이 LAN IP에만 열린다 — 즉 **루프백(127.0.0.1)으로는 안 연다.**

그런데 agent의 배포 후 헬스 확인은 `127.0.0.1`(자기 루프백)을 두드리고 있었다. 그러니
`connection refused`가 났다. 상황을 한 줄로 정리하면 이렇다.

```
[문제의 대치]
  backend 바인딩:  LAN IP:8090 에만 연다 (127.0.0.1 은 거부)   ← 보안 (fail-closed)
  agent 헬스확인:  http://127.0.0.1:8090/actuator/health 를 두드림  ← 대상 주소가 틀림
  결과:           배포는 정상 · 헬스 URL만 틀림 → 헬스체크가 "실패"로 정직하게 보고
```

여기서 중요한 건 헬스체크가 **거짓 성공을 내지 않았다**는 점이다. compose가 `up` 했다는 것만
믿었다면 "deploy ok"로 넘어갔을 텐데, 실제로 응답을 확인하는 헬스체크였기에 "127.0.0.1로는
정말 안 열린다"를 잡아냈다. 전말과 그 의미(두 검증 장치가 서로를 검증한 사례)는 ci-cd issue3
§3에 정리돼 있다.

### 교정

바인딩을 바꾸는 게 아니라(그건 의도된 보안이다) **agent의 헬스 URL을 LAN 주소로** 맞췄다
— `DEPLOY_HEALTH_BACKEND`를 127.0.0.1이 아니라 backend가 실제로 여는 LAN 주소로 지정.
이 값은 ci-cd(배포 서버) 쪽 설정이라 교정도 그쪽에서 이뤄졌다.

> 참고 — 함께 있던 문서 교정(#17, 커밋 `2d7e0ef`): 설계 문서에서 "코테 문서에 2-summary가
> 없는 것"을 의도된 설계처럼 적어뒀던 부분을 "그냥 아직 미작성일 뿐"으로 정정했다. 안 한 걸
> 한 척하지 않기 위한 문구 교정이다.

---

## 3. 결론

backend도 push → 자동 배포(증분 38초) 상태가 됐다. 그리고 운영 지식 한 줄을 얻었다 —
**특이 설정(BIND_ADDR로 루프백을 막는 것)이 있는 서비스는 헬스 URL도 그 설정을 따라야 한다.**
헬스체크의 대상 주소를 서비스의 바인딩과 맞추지 않으면, 멀쩡한 서비스가 "unhealthy"로 찍힌다.
PR #19
