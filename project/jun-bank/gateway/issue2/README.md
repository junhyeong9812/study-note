# issue2 — gateway CD: 네 번째 배포 대상이 되다

- 원본 PR: gateway #4 · devlog: `jun-bank/gateway/docs/devlog/pr-04-gateway-cd.md`

## 1. 무엇이 문제였나

블루-그린 전환 구현(issue1)으로 gateway는 배포 대상 4번째가 됐다.\
그런데 정작 자신은 CI(이미지 빌드)만 있고 CD가 없어, .9 서버에서 jar 볼륨 방식으로 수동으로 떠 있었다.

> **CI / CD** — CI는 코드가 올라올 때마다 자동으로 빌드·테스트하는 것, CD는 그 산출물을 자동으로 배포까지 하는 것.\
> 예: CI만 있으면 "이미지는 만들어지는데 서버에 올리는 건 사람이 손으로" 하는 상태다.

배포 대상이 된 서비스가 수동 부트스트랩으로 떠 있으면 배포 경로가 두 벌이 된다.

gateway에는 구조적 특수성도 있었다.\
블루-그린 전환 수단(SCG 라우트)의 소유자가 자기 자신이라, 자기 배포를 블루-그린으로 할 수 없다(자기 참조).\
이 판단은 ADR-027 DO-20에서 이미 내려져 있었다 — **재기동 교체**로 배포하고 짧은 중단을 수용한다.

> **재기동 교체** — 슬롯을 옮기는 대신, 같은 자리의 컨테이너를 내리고 새 이미지로 다시 띄우는 방식.\
> 예: 창구를 하나만 두고 잠깐 닫았다가 새 직원으로 다시 여는 것 — 그 잠깐이 짧은 중단이다.

## 2. 무엇을 고민했나

핵심 판단은 "gateway CD를 core와 얼마나 같게 두는가"였다.

- **core deploy.yml을 원형으로 복제** — 워크플로가 만드는 것은 서명된 요청 하나뿐이고 실행 주체는 agent 하나다.\
  계약을 바이트 수준으로 같게 유지하면 다른 곳은 이미지 저장소·target·동시성 그룹 등 7곳뿐이다. (채택)
- 배포 모드만 core와 다르게 둔다 — 워크플로가 만드는 요청의 계약은 코어와 같고, 무중단 여부는 agent 쪽 배포 모드가 정한다.

allowlist 설계에서도 한 안이 뒤집혔다.

- **단일 env 모드**(allowlist 없이 한 target만 허용하는 하위호환)를 남기려 했다.\
  그러나 "무결박 우회 모드의 존속"이라는 지적으로 폐지하고, 1항목 allowlist로 정규화했다. (기각→폐지)

> **allowlist(허용 목록)** — "이 repo는 이 target만 배포할 수 있다"를 미리 못박아 둔 목록.\
> 예: gateway repo가 실수로 core를 배포하려 해도, 목록에 없으니 agent가 거부한다.

## 3. 그래서 이렇게

계약은 core와 같게, 배포 모드만 다르게 뒀다.\
CD는 core의 deploy.yml을 복제해 서명 계약(HMAC canonical 문자열과 OIDC claim 행렬)을 그대로 유지했다.\
배포 요청은 동시에 하나만 돌도록 직렬화하고(`concurrency.group: deploy-gateway`), 응답은 2xx만 성공으로 인정한다.

이 작업은 infra의 OIDC repo별 allowlist(infra#28)와 한 슬라이스로 묶였다.\
두 번째 repo가 실제로 배포를 요청해 봐야 "repo가 자기 target만 배포한다"는 결박이 검증되기 때문이다.

```text
gateway repo가 서명된 배포 요청 생성    워크플로가 만드는 건 요청 하나뿐
        ↓
agent가 OIDC claim 검증                job_workflow_ref가 정확히 일치해야 통과
        ↓
allowlist에서 repo↔target 1:1 확인     gateway repo는 gateway target만
        ↓
배포 모드로 실행                       gateway는 재기동 교체(블루-그린 아님)
```

## 4. 코드 — 실제 커밋에서

워크플로 머리에 gateway가 왜 재기동 교체인지가 그대로 적혀 있다.

```yaml
# .github/workflows/deploy.yml:19-23 (발췌)
# ⚠️ target=gateway 의 배포 방식은 코어와 다르다 — 재기동 교체이지 블루-그린이 아니다
#    (ADR-027 DO-20 v0.5 ⓐ): 게이트웨이는 블루-그린 전환 수단(SCG 라우트)의 소유자라
#    자기 자신의 전환을 자기가 할 수 없다(자기 참조). ... 이 워크플로가 만드는 요청의
#    계약은 코어와 같고, 무중단 여부는 agent 쪽 배포 모드가 정한다.
```

`job_workflow_ref` 결박은 이 파일의 경로·이름·브랜치가 agent 설정과 정확히 일치해야 한다는 운영 계약을 만든다.

```yaml
# 같은 파일 :14-17 (발췌)
# ⚠️ job_workflow_ref 결박: 이 파일 경로·이름(deploy.yml)·브랜치(main)가 agent의
#    OIDC_JOB_WORKFLOW_REF=jun-bank/gateway/.github/workflows/deploy.yml@refs/heads/main 과
#    정확히 같아야 게이트 2를 통과한다. 파일명·위치를 바꾸면 agent 설정도 함께 바꿔야 한다.
```

## 5. 구현 중 마주친 문제

음성 e2e(위반 요청 거부)에서 1차 시도가 뜻밖의 실증이 됐다.\
allowlist 한 줄만 스왑해 "core 신원이 gateway target을 요청"하는 위반을 만들었더니, agent가 "target을 두 저장소가 주장한다"며 **기동 자체를 거부**했다.\
1:1 결박 검증이 설계대로 먼저 동작한 것이다.\
교차 스왑으로 다시 만든 위반 요청은 HTTP 403과 이력 `REJECTED`/`TARGET_FORBIDDEN`으로 거절됐고, 원장 선점 0행 — 부작용이 전혀 없었다.

양성(gateway) e2e는 구조적으로 머지 후에만 가능했다.\
deploy.yml이 main에 있어야 `workflow_run` 트리거와 `job_workflow_ref` 결박이 성립하기 때문이다.\
머지 후 첫 실행에서 배포 모드 부재로 fail-closed(설계대로), 모드 등록 후 재발화로 HTTP 200 배포를 완주했다.

이 배포가 issue1의 상태 파일 수정을 실전 검증했다.\
.9의 gateway를 이미지 기반으로 전환하고 재기동했을 때, 활성 슬롯이 env 기본값(blue)이 아니라 **파일값(green, token 9)으로 복원**됐다 — "state restored from file" 로그가 그 증거다.

## 6. 결론

gateway가 정식 CD 경로 안에 들어왔고, 배포 경로 두 벌 문제가 하나로 합쳐졌다.\
agent의 allowlist에는 gateway의 repo 수치 ID가 등재되어, repo↔target 1:1 결박이 두 항목으로 실동작하기 시작했다.

이후 PR #5(issue3, CI 테스트)와 #9(issue6, compose 동봉)가 같은 deploy.yml 위에 쌓인다.
