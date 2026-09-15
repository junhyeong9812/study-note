# issue14 — compose 동봉: 이미지는 고정, 기동 정의도 고정

- 원본 PR: infra #31 · devlog: `jun-bank/infra/docs/devlog/pr-31-compose-embed.md`

## 1. 무엇이 문제였나

이미지는 digest로 내용이 고정돼 있었지만 기동 정의(compose)는 호스트 파일이었다.\
"이미지에서 막은 구멍이 compose에서 다시 열려 있다"는 비대칭이 출발점이다.

> **manifest** — 이 배포가 무엇을 어떻게 띄울지 적은, 서명된 지시서.\
> 예: 여기에 compose까지 담으면 기동 정의도 서명 안으로 들어온다.

이슈 본문이 문제를 정확히 잡았다.\
compose revision·config version 두 값이 비어 있지 않은지만 검사하고 이후 쓰이지 않아, 호스트 compose가 낡거나 변조돼도 이미지 digest만 맞으면 배포가 COMPLETED로 통과한다 — 이미지는 고정되는데 기동 정의는 고정되지 않는 갭이다.

구현에 들어가며 하위 문제들이 드러났다.\
기존 `ParseManifest`는 표준 JSON 언마샬이라 미지 필드를 무시하고 중복 키는 뒤엣것이 이긴다(무시된 필드가 곧 무시된 결박이다).\
base64는 개행을 건너뛰어 디코드 성공만으로 같은 바이트가 보장되지 않고, compose의 보간 표면(`.env` 자동 로드·env 상속·`${X:-y}`)은 전부 서명 밖이며, 검증한 파일과 실행되는 파일 사이 TOCTOU 창은 블루-그린에서 분 단위다.

> **TOCTOU** — 검사한 시점(time-of-check)과 쓰는 시점(time-of-use) 사이에 대상이 바뀌는 창.\
> 예: compose를 검증한 뒤 기동·헬스·전환·드레인을 다 지나 마지막 down까지 창이 열려 있다.

## 2. 무엇을 고민했나

- **manifest 판정 — embedded/legacy 2분법, 값 vs 키 존재.**\
  키의 존재로 판정했다. null이 디코드하면 빈 문자열이라 값으로는 부재와 구별되지 않는다.
- **YAML 검증 — typed struct 위임 vs `yaml.Node` 직접 순회.**\
  직접 순회를 골랐다. 검증기와 compose가 같은 구조를 보게 하려면 typed struct에 위임하면 안 된다.
- **subprocess env — 금지 목록 vs 허용 집합.**\
  허용 집합(PATH + 주입값)을 골랐다. "빈 슬라이스면 상속"이라는 암묵 규칙은 주입값이 없는 순간 격리를 무음으로 푼다.
- **TOCTOU — 재검증 시점 미루기 vs 검증한 바이트 굳히기.**\
  바이트 굳히기를 골랐다. 시점을 미루면 창이 좁아질 뿐 없어지지 않는다(§5).

## 3. 그래서 이렇게

manifest를 embedded(composeContent + appService + composeRevision)와 legacy로 가르고, strict YAML 검증기로 문서 1개·서비스 정확 1개·닫힌 키 목록·앵커/병합/태그 거절·`$` 전면 금지를 강제한다.\
candidate를 해시 명명 파일로 O_EXCL 기록 후 재해시하고, 배포 성공 후에만 target 단위 `applied.json`으로 승격한다.

```text
서명 manifest 수신
        ↓
키 존재로 embedded / legacy 판정  (무동봉 legacy → 422 거절)
        ↓
strict YAML 검증 (yaml.Node 순회 · $ 전면 금지)
        ↓
검증된 바이트를 compose.sha256-<hex>.yml 로 O_EXCL 기록 → 재해시
        ↓
그 세대 파일로만 기동 (실행 결박)
        ↓
배포 성공 후 applied.json 원자 회전 (record 상태로 승격 판정)
```

## 4. 코드 — 실제 커밋에서

`$` 전면 금지는 필드 검증보다 앞서고, 디코드 후 값에서 본다.

```go
// internal/compose/validate.go:255-281 (발췌) — $ 전면 금지가 필드 검증보다 앞선다
// checkNoInterpolation은 디코드된 모든 스칼라(값과 키)에서 $를 금지한다. 면제는 완전일치
// 2형식(${이미지변수}, ${DEPLOY_HOST_PORT}:8080)뿐이다.
// 디코드 후 값을 보는 것이 핵심이다: 원문 바이트 스캔은 "\x24" 같은 YAML 이스케이프를
// 놓치지만, 디코드 후 값은 compose가 실제로 볼 문자열 그대로다.
```

승격은 revision이 아니라 record 상태로 판정한다.

```go
// internal/compose/workspace.go:540-563 (발췌) — 승격은 record 상태로 판정
// ⚠️ revision만 비교하면 안 되는 이유(리뷰 E-1): compose 정의는 릴리스마다 바뀌지 않는다.
// 같은 compose에 새 이미지를 올리는 것이 정상 배포의 대다수인데, revision 비교는 그 전부를
// "같은 것"으로 보고 승격을 통째로 삼킨다 — 그 목록을 보고 복원하면 예전 이미지가 뜬다.
```

TOCTOU는 검증한 바이트를 별도 파일로 굳혀 실행기에 결박하는 방식으로 닫았다.

```go
// internal/compose/workspace.go:221-232 (발췌)
// 검증한 바이트 자체를 별도 파일로 굳혀 실행기에 결박하면, 원본이 그 뒤 어떻게 바뀌든
// 실행되는 내용은 검증된 것 그대로다.
```

## 5. 구현 중 마주친 문제

승격 판정이 특히 교훈적이었다.\
compose revision만으로 판정하면, 같은 compose에 새 이미지를 올리는 정상 배포의 대다수를 "같은 것"으로 보고 승격을 통째로 삼킨다 — 복원 재료가 옛 이미지에 머문다.\
그래서 판정을 record 상태로 옮겼다.

TOCTOU도 처음엔 재검증 시점을 뒤로 미루는 방향이었는데, 그러면 창이 좁아질 뿐 없어지지 않았다.\
검증한 바이트 자체를 별도 파일로 굳혀 실행기에 결박하는 방식으로 바꿔, 원본이 뒤에 어떻게 바뀌든 실행 내용이 검증된 것 그대로이게 했다.

브랜치 위생 사고도 하나 있었다.\
워커의 `git add -A`로 세션 상태 파일이 커밋에 혼입됐고(미push), 히스토리 재작성으로 정리한 뒤 바이너리를 재빌드·재검증했다.

## 6. 결론

머지 후 실전 CD에서, green 컨테이너의 compose 라벨이 workspace 세대 파일을 가리키는 것으로 실행 결박이 실증됐고, 2차 배포에서 applied가 회전해 새 이미지가 새 record로 승격되며 이전 것이 previous로 보존됐다.\
무동봉 legacy manifest는 HTTP 422로 거절됐고, 동일 상태 재배포는 멱등하게 처리됐다.

#19가 닫히며 S2가 완주됐다 — 호스트 파일 실행 경로가 철회됐다.\
남은 반쪽은 config다 — manifest의 configVersion은 아직 고정 문자열이고, ConfigVersion 결박은 별건으로 남아 있다.\
compose는 내용 결박(sha256), config는 버전 단언 결박이라는 강도 차이를 ADR-030(v1.3)이 정직하게 적어 둔 자리다.
