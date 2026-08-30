# issue3 — 리뷰 반영과 전 서비스 E2E: 헬스체크가 첫 실전에서 오배포를 잡다

- 이슈 #9 · PR: https://github.com/junhyeong9812/study-note-deploy-system-ci-cd/pull/10

## 1. 배경

원격 실행 서버(명세 stakes 중간~높음)라 코드 리뷰 1회를 명세에 박아뒀었다. 전체 소스를
리뷰어에게 보내 9건을 받았고, 채택 6·기각 2·이연 1로 판정 후 반영했다. 이어서
backend·front 리포에도 배포 호출 Actions를 붙여 **세 서비스 전부**를 자동 배포 대상으로.

## 2. 리뷰 판정 — 채택한 것과 기각한 것

### 채택 6 (전부 "권한·유실·거짓 성공" 계열)

**F4 — master에 docker.sock이 왜 붙어 있나** (가장 아픈 지적)

**상황**: compose가 서비스 하나(ci-cd)를 MODE만 바꿔 재사용 → 볼륨 마운트가 공통이라
**외부 요청을 받는 master 컨테이너에도** docker.sock과 저장소 3개가 마운트돼 있었다.

**문제**: master가 뚫리면(취약점 하나면) 그 즉시 호스트 docker 제어권 — master의 일은
접수·라우팅뿐인데 침해 반경은 agent와 같았다.

**결론**: compose를 master/agent **두 서비스로 분리**(profiles) — master는 마운트 0:

```yaml
master:                          # docker inspect 실측: Mounts 없음
  profiles: ["master"]
  env_file: .env.master          # 볼륨 없음
agent:
  profiles: ["agent"]
  volumes: [docker.sock, 저장소 3개]   # 실행 권한은 agent에만
```

**원칙**: 편의(서비스 정의 재사용)가 **최소 권한**을 침식하면 편의를 버린다.

**F6 — 연속 push 두 번이면 두 번째가 조용히 사라진다**

**상황**: master는 요청마다 202를 주고 고루틴으로 dispatch, agent는 배포 중이면 409.
**문제**: push A 직후 push B → 둘 다 202(호출자는 성공으로 인식) → B는 agent 409로
버려지는데 **아무도 모른다**(비동기 뒤라서). "접수됨 ≠ 배포됨"의 함정.
**결론**: master가 서비스별 in-flight를 추적, 진행 중이면 **접수 시점에 명시적 409** —
실패가 시끄러워졌다(Actions 로그에 바로 보임). 부수 효과로 고루틴 수도 서비스 수로 유계.

**F5·F7·F8·F9 (요약)**: sha 검증을 master 접수 전으로(개행 섞은 sha로 로그에 가짜 줄을
꽂는 로그 주입 + 엉터리 202 차단) · **배포 후 헬스 확인**(compose 성공 ≠ 서비스 정상 —
DEPLOY_HEALTH_* URL을 90초 폴링) · master healthcheck가 agent 포트를 보던 정합 오류 ·
http 서버 read/idle 타임아웃(슬로우 커넥션이 인증 전 자원을 무는 것 방지).

### 기각 2 · 이연 1

- **"ghcr 방식으로 되돌려라"(Critical)** — 리뷰어가 본 명세가 전환 전 버전. 코드가 아니라
  **명세 문서를 갱신**하는 게 맞다(사용자 결정이 정본). 단 리뷰어의 부수 지적은 유효해서
  수용 리스크로 명문화: git-pull 방식에선 저장소 커밋이 compose를 바꿀 수 있다 —
  main의 PR 게이트 + 자기 소유 repo가 신뢰 경계다.
- **"go.mod가 없어 빌드 불가"** — 리뷰 입력(packet)을 만들 때 내가 파일을 빠뜨림.
  **두 번째 같은 사고**라 "packet 자기검증"이 후속 과제로 확정됐다.
- **HMAC+타임스탬프**(재전송 방지) — 현 구조(엣지 HTTPS + LAN)에서 위험이 낮아 후속
  이슈로 이연, 명세 표현은 "공유 시크릿(상수시간)"으로 정정.

## 3. 전 서비스 E2E — 그리고 헬스체크의 첫 실전

```
llm     push → 15초  → 자동 재배포 ok
front   push → 56초  → ok (약한 CPU에서 Next 빌드 포함 — 감당됨)
backend push → 1차 deploy_unhealthy ← ★ 방금 넣은 F7이 잡은 것
              2차 38초 ok (gradle 증분 — 도커 레이어 캐시 덕에 수 분이 아니었다)
```

### backend 1차 실패의 전말

**상황**: agent(.158, host 네트워크)가 backend 배포 후 `http://127.0.0.1:8090/actuator/health`를 폴링.

**문제**:
```
agent deploy unhealthy backend: health 미도달: dial tcp 127.0.0.1:8090: connect: connection refused
```
그런데 backend는 멀쩡히 떠 있었다 — `http://192.168.55.x:8090`으로는 200.

**접근**: "떠 있는데 127.0.0.1이 거부"면 바인딩 주소 문제. backend compose를 보니 예전
보안 리뷰 때 넣은 **fail-closed 바인딩** `${BIND_ADDR:?}:8090:8090` — LAN IP에만 바인딩
되어 있어서 루프백(127.0.0.1)으로는 아예 열려 있지 않았다.

**결론**: 헬스 URL을 LAN 주소로 교정. — 이 사건의 진짜 의미: **compose가 "성공"이라고
말한 배포를 헬스체크가 "정상 아님"으로 뒤집은 첫 사례**다. F7이 없었다면 "deploy ok"
로그를 믿고 넘어갔을 것. 두 보안·검증 장치(fail-closed 바인딩, 배포 후 헬스)가 충돌한
것처럼 보이지만, 실은 서로를 검증해준 셈.

## 4. 결론

세 서비스 push→자동 배포 가동. 남긴 것: HMAC(후속)·롤백(sha 이력은 /status에 축적 중)·
리뷰 packet 자기검증. PR: #10
