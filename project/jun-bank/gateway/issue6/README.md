# issue6 — 정본 compose 신설 + CD manifest 동봉

- 원본 PR: gateway #9 · devlog: `jun-bank/gateway/docs/devlog/pr-09-compose-embed.md`

## 1. 무엇이 문제였나

gateway의 기동 정의(compose)가 호스트 파일에만 있어, 낡거나 변조된 정의가 실행될 수 있었다.\
그래서 compose를 서명된 배포 manifest에 동봉해 옮기는 작업이다.

> **compose 동봉(embed)** — 컨테이너 기동 정의(compose)를 호스트에 두지 않고, 서명된 배포 묶음 안에 넣어 함께 배포하는 것.\
> 예: "무엇을 어떻게 띄울지"까지 서명 안에 넣으면, 호스트에서 몰래 바뀐 정의로 뜨는 길이 막힌다.

배경 문제는 core 쪽과 같지만, gateway에는 고유한 문제 셋이 더 있었다.

**첫째, 리터럴 값 4종.**\
호스트 compose에 `CORE_BLUE_URI` 같은 리터럴 값 4종이 박혀 있었다.\
이 값을 서명 정본에 그대로 옮기면 서명된 정본과 실제 배선이 두 벌로 갈라진다 — 값을 바꿀 때마다 재서명·재배포가 필요해지거나, 정본과 실물이 어긋난 채 굴러간다.

**둘째, 기본값 문법.**\
호스트 compose는 `${CORE_IMAGE:-...latest}` 형태의 기본값 문법을 쓰고 있었다.\
정본에서 이 문법은 금지다 — 주입이 실패했을 때 조용히 latest로 뜨는 길이기 때문이다.

**셋째, healthcheck 부재.**\
gateway는 재기동 교체라 배포 중 짧은 중단이 있는데, 준비성 판정을 받쳐줄 컨테이너 내부 검사가 없었다.

## 2. 무엇을 고민했나

핵심 논점은 `environment`를 어떻게 처리하는가였고, 여기서 한 안이 실제로 뒤집혔다.

- **리터럴 값 동봉** — compose 정본에 `CORE_BLUE_URI=...` 값을 그대로 적는다.\
  그러나 이건 "설정 값은 호스트 소유"(CP-5)·"리터럴 시크릿 거부"(CP-7)와 정면 충돌한다. (기각)
- **값 없는 pass-through 목록** — 키 이름만 적고 값은 호스트 `.env`가 소유한다.\
  agent가 자기 프로세스 env에서 그 키의 값을 읽어 compose 서브프로세스로 넘긴다. (채택)

> **pass-through(통과 전달)** — 값을 파일에 적지 않고 키 이름만 선언해 둔 뒤, 실행 주체가 자기 환경에서 값을 읽어 넘기는 방식.\
> 예: compose에는 `CORE_BLUE_URI`라고 이름만 두고, 실제 주소는 호스트 `.env`에서 agent가 읽어 채운다.

이 방식의 힘은 "시크릿 미포함"이 약속이 아니라 **파서가 강제하는 성질**이 된다는 데 있다 — agent의 allowlist가 값이 붙은 형태 자체를 거절한다.\
등재된 키가 호스트에 없으면 배포가 거절되므로(fail-closed), 값 누락도 조용히 지나가지 않는다.

## 3. 그래서 이렇게

`environment`는 값 없는 pass-through 목록으로, 나머지 셋은 정본 규칙에 맞춰 이관했다.

- **상태 볼륨은 정본에 남겼다** — issue1에서 만든 라우트 상태 파일(활성 슬롯·token의 재기동 보존)이 이 볼륨 없이는 무력화되기 때문이다.\
  볼륨은 agent의 target별 정확 튜플 allowlist에 등재된 것만 허용된다.
- **healthcheck는 고정 패턴 1형식으로 신설했다** — 자유 문자열 셸 명령은 allowlist가 거부한다.\
  신설 전에 .9의 실컨테이너에서 wget 존재와 actuator 응답을 먼저 확인해 실패하지 않을 근거를 잡았다.
- **기본값 문법은 제거했다** — `:-latest` 폴백을 없앴다.

```text
호스트 compose (동봉 전)              정본 compose (동봉 후)
+-------------------------+          +-------------------------+
| CORE_BLUE_URI=리터럴값  |          | environment: 키 이름만  |
| ${CORE_IMAGE:-...latest}|          | 포트는 주입             |
| healthcheck 없음        |          | healthcheck 고정 패턴   |
+-------------------------+          +-------------------------+
  → 정본과 실물이 갈라짐               → allowlist가 형태를 강제
```

## 4. 코드 — 실제 커밋에서

채택된 pass-through 계약이다.

```yaml
# deploy/compose.yml:47-55
# 값 없는 pass-through 목록이다 — 값은 이 파일이 아니라 호스트 .env가 소유한다(CP-5).
# 여기에 리터럴 값을 적으면 서명된 정본과 실제 배선이 두 벌로 갈라지고, allowlist도
# 값이 붙은 형태를 거절한다. agent가 자기 프로세스 env에서 아래 키의 값을 읽어
# compose 서브프로세스로 넘기며, 등재된 키가 호스트에 없으면 배포를 거절한다.
environment:
  - CORE_BLUE_URI
  - CORE_GREEN_URI
  - CORE_ACTIVE_SLOT
  - CORE_STATE_FILE
```

`composeRevision`의 의미도 바뀌었다.\
gateway는 슬롯이 없어 `"gateway-v1"`이라는 이름표를 쓰고 있었는데, 동봉 후에는 내용의 sha256이 된다.

```yaml
# .github/workflows/deploy.yml:166-168
# composeRevision은 더 이상 사람이 붙인 이름표가 아니라 내용의 해시다 — gateway가
# 슬롯 없는 재기동 교체라는 사실(DO-20 v0.5 ⓐ)은 이 값에 나타나지 않는다.
```

## 5. 구현 중 마주친 문제

이관 직전 드리프트 대조(.9 읽기 전용)에서 호스트 compose와 repo 정본의 차이가 전부 예상 내임을 확인했다.\
포트 하드코딩은 주입으로, `:-latest` 기본값은 의도된 제거로, 리터럴 4종은 pass-through로(값은 호스트 `.env`로 이동), healthcheck는 신설로 — 어긋난 항목이 없었다.\
agent 검증기의 env 4키·볼륨 튜플 실통과도 수기 대조로 확인했다.

머지 후 실전 배포에서 gateway 재기동 교체가 동봉 결박으로 완주했다.\
컨테이너의 compose 라벨이 workspace의 해시 명명 파일을 가리키고, pass-through 4키와 포트 주입이 기록에 남았으며, 라우트 상태(slot·token)는 재기동을 넘어 보존됐다.\
같은 상태의 재배포는 멱등하게 처리됐다(컨테이너 무재생성).

## 6. 결론

gateway의 기동 정의가 호스트 파일에서 서명 동봉으로 옮겨졌고, 시크릿 미포함이 파서가 강제하는 성질이 됐다.\
infra#19가 세 PR(core#3·gateway#9·infra#31)로 닫히며 S2가 완주됐다.

남은 것: `CORE_IMAGE`라는 이름이 gateway compose에도 쓰이는 어색함(agent의 전역 이미지 변수 계약)이 정리 후보로 남아 있다.\
gateway의 다음은 G3(#8 채널별 라우팅 — SCG의 본목적)다.
