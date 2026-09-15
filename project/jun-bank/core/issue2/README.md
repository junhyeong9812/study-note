# issue2 — 정본 compose 신설 + CD manifest 동봉

- 원본 PR: core #3 · devlog: `jun-bank/core/docs/devlog/pr-03-compose-embed.md`

---

## 1. 무엇이 문제였나

core의 기동 정의(compose)가 호스트에 놓인 파일이었다.\
이미지는 이미 digest로 내용이 고정돼 있었지만, 정작 `docker compose up` 이 읽는 compose는 서명 밖의 호스트 파일이라 낡거나 변조된 정의가 조용히 실행될 수 있었다.\
"이미지에서 막은 구멍이 compose에서 다시 열려 있다"(ADR-030 CP-1)는 비대칭이 출발점이다.

> **digest / compose / manifest** — digest는 이미지 내용을 해시로 고정한 지문(내용이 바뀌면 지문도 바뀐다).\
> compose는 "무엇을 어떻게 띄울지"를 적은 기동 정의 파일, manifest는 배포 엣지로 보내는 서명된 배포 요청서다.\
> 예: 이미지는 지문으로 못 바꾸게 묶어 놨는데, 그 이미지를 띄우는 방법(compose)은 아무나 고칠 수 있는 파일로 남아 있던 상태.

문제는 세 갈래였다.

**식별자가 내용에서 유도되지 않았다.**\
이 PR 이전의 manifest에는 `composeRevision: "core-green-v1"` 같은 사람이 붙인 이름표가 placeholder로 들어가 있었다.\
식별자가 내용에서 나오지 않으니, 배포 이력에 남은 revision이 실제로 실행된 정의를 증명하지 못한다.

**실행 파일이 서명 밖에 있었다.**\
`docker compose up` 이 읽는 파일은 서명 밖의 호스트 파일이라, 낡거나 변조된 정의가 조용히 실행될 수 있었다.

**시점이 어긋났다.**\
CD 워크플로는 항상 main ref에서 도는데 배포 대상은 특정 SHA다.\
워크플로 ref의 compose를 그대로 쓰면 "배포하는 커밋"과 "실행될 compose"가 서로 다른 시점에서 온다.

---

## 2. 무엇을 고민했나

인터뷰와 설계에서 몇 갈래를 저울질했다. 안 고른 안도 남긴다.

**정본 compose를 어디에 둘까.**\
후보 A는 각 서비스 repo(`deploy/compose.yml`), 후보 B는 중앙 infra repo 보관이었다.\
서비스마다 자기 기동 정의를 자기 repo에 두면 "배포하는 커밋"과 함께 버전이 움직이므로, **각 서비스 repo**로 확정됐다.

**슬롯 포트를 어떻게 다룰까.**\
후보 A는 슬롯(블루/그린)마다 compose를 두 벌 만드는 것, 후보 B는 한 벌 + agent 주입이었다.\
두 벌은 파일이 두 개로 갈라져 표류할 자리가 생기므로, **한 벌 + agent 주입**을 택했다 — 슬롯별 차이는 파일이 아니라 주입값이 정한다.

**롤백 재료를 로컬에 남길까(CP-4).**\
처음엔 없애는 쪽으로 기울었으나, 사용자가 **유지**로 정정했다.\
CI 발급이 안 될 때 이전 것으로 복원할 수 있어야 한다는 안정성 요구이고, 자동 소비 경로는 없는 수동 비상 재료다.

**시크릿은 어떻게 가르나(CP-5).**\
compose는 구조(이미지는 `${env}` digest 참조, 설정 값은 호스트 env 참조)라 시크릿이 없으므로 동봉해도 되고, 설정 값·시크릿은 호스트에 남긴다.\
즉 "구조는 서명에 동봉, 값은 호스트"로 갈랐다.

---

## 3. 그래서 이렇게

채택된 구조는 ADR-030 CP-1의 논리 그대로다.\
서명 payload 안에 내용 자체가 있으면 식별자와 내용이 한 서명으로 묶여, agent가 **해시 대조만으로** 둘의 일치를 증명한다.\
그리고 정본 파일은 자기 규정을 머리에 달고, allowlist는 닫힌 목록이라 여기 없는 키·문법을 하나라도 더하면 agent가 배포를 거절한다.

> **allowlist / pass-through** — allowlist는 "허용된 것만 통과시키는 닫힌 목록"이다.\
> compose의 `environment` 는 값을 적지 않고 이름만 나열하는 **pass-through** 목록 — 값은 호스트 env에서 흘러 들어오고 파일에는 남지 않는다.\
> 예: `- DB_PASSWORD` 라고만 쓰면 값은 호스트가 채우고, 서명 대상 파일에는 비밀이 없다.

```text
수정 전:  manifest(서명) ── composeRevision: "core-green-v1"  ← 사람이 붙인 이름표
              │                                                 (내용과 무관)
          docker compose up ──읽음──> 호스트의 compose 파일     ← 서명 밖
                                          → 낡거나 변조돼도 조용히 실행

수정 후:  대상 커밋 SHA 에서 compose 체크아웃
              ↓
          한 프로세스가 한 번 읽은 버퍼  raw
              ├── sha256(raw)  ──> composeRevision
              └── base64(raw)  ──> composeContent
              ↓
          한 서명 payload 안에  revision + 내용  함께 묶임
              ↓
          agent: 해시 대조로 일치 증명 · allowlist 밖이면 거절
```

세로 흐름 해설.\
"대상 SHA 체크아웃 → 한 번 읽은 버퍼에서 해시·base64 동시 산출 → 한 서명에 함께 묶기 → agent 해시 대조"로, 식별자와 내용을 같은 바이트에서 뽑아 어긋날 자리를 없앤다.\
왼쪽 수정 전과 나란히 두면, 이름표가 내용으로 바뀌고 실행 파일이 서명 안으로 들어온 대비가 보인다.

---

## 4. 코드 — 실제 커밋에서

> jun-bank는 git repo가 아니라 PR 번호로만 대조한다. 좌표는 devlog가 박아 둔 파일:줄이다.

정본 파일은 자기 규정을 머리에 달고 있다 — allowlist 통과 형태만 허용한다.

```yaml
# deploy/compose.yml:8-18 (발췌)
# ⚠️ 이 파일은 서명 동봉 정본이다 — agent의 allowlist 통과 형태만 허용한다.
#   - 최상위 키는 services 하나뿐. 서비스는 정확히 1개(= manifest의 appService).
#   - 변수 치환은 CORE_IMAGE 와 DEPLOY_HOST_PORT 두 개만, 정확한 형태로만.
#     기본값 문법(중괄호 안의 :- 표기)은 금지다 — 주입이 실패했을 때 조용히 latest 같은
#     엉뚱한 이미지로 뜨는 길을 열기 때문이다. 값이 없으면 뜨지 않는 편이 맞다.
```

"값이 없으면 뜨지 않는 편이 맞다"가 이 파일의 태도다 — 조용한 폴백보다 명시적 실패를 택한다.

동봉할 compose는 워크플로가 도는 ref가 아니라 배포 대상 커밋의 것이어야 한다.

```yaml
# .github/workflows/deploy.yml:100-111 (발췌)
- name: 정본 compose 체크아웃 (배포 대상 커밋의 것)
  uses: actions/checkout@v4
  with:
    ref: ${{ steps.sha.outputs.sha }}
    persist-credentials: false   # push 할 일이 없다 — 토큰을 남기지 않는다
```

해시와 base64는 한 프로세스가 한 번 읽은 같은 버퍼에서 산출한다 — 두 번 읽으면 그 사이의 사소한 차이가 revision과 내용의 불일치로 남고, 그건 배포 현장에서야 드러난다.

```python
# 같은 파일 :180-190 (발췌)
with open(path, "rb") as f:
    raw = f.read()          # 정본 compose는 여기서 딱 한 번 읽는다
revision = "sha256:" + hashlib.sha256(raw).hexdigest()
content = base64.b64encode(raw).decode("ascii")
```

그리고 발행 전에 자기가 만든 manifest를 다시 뜯어서 검증한다 — agent가 거절해 주기를 기대하지 않는다.

```python
# 같은 파일 :200-215 (발췌) — self-assertion 5종
got = json.loads(body.decode("utf-8"))
decoded = base64.b64decode(got["composeContent"], validate=True)
if decoded != raw:
    fail("composeContent 디코드 결과가 원본 compose 바이트와 다르다")
if "sha256:" + hashlib.sha256(decoded).hexdigest() != got["composeRevision"]:
    fail("composeRevision이 동봉 내용의 sha256과 불일치 — 발행 중단")
if len(body) > 32768:
    fail("manifest 크기 %d바이트 > 32768 상한(CP-6)" % len(body))
```

---

## 5. 구현 중 마주친 문제

설계 도중 `environment` 정의가 한 번 뒤집혔다.\
처음엔 리터럴 값(실제 값을 파일에 적는 형태)이 설계에 들어갔다가, CP-5/CP-7 충돌 지적으로 **값 없는 pass-through 목록**으로 반전됐다.\
"구조는 동봉, 값·시크릿은 호스트"라는 경계를 지키려면 `environment` 에 값이 남아선 안 됐기 때문이다 — 값이 남으면 서명 동봉물에 설정·시크릿이 섞여 CP-5가 깨진다.

---

## 6. 결론

지금 상태 — compose가 호스트 파일에서 서명 동봉 정본으로 옮겨졌고, 식별자(revision)와 내용이 같은 바이트에서 유도돼 한 서명으로 묶였다.\
gateway#9가 같은 계약의 gateway 판이고, infra#31이 수신 측(검증기·workspace·불변 스냅샷)이다.\
셋이 함께 머지되며 상위 이슈 infra#19가 닫혔고, ADR-030은 v1.3으로 "compose 부분 구현됨"이 됐다.

남은 빚.\
남은 반쪽은 config다 — manifest의 `configVersion` 은 아직 "v1" 고정 문자열이고, ConfigVersion 결박(#19-config)은 별건으로 남아 있다.
