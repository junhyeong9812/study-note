# issue10 — false-UNKNOWN: 배포는 됐는데 배포가 실패했다

- 원본 PR: infra #25 · devlog: `jun-bank/infra/docs/devlog/pr-25-false-unknown.md`

## 1. 무엇이 문제였나

전 파이프라인이 실서버에서 처음 도는 순간 모순 상태가 나왔다.\
응답은 HTTP 409 "원격 실행 UNKNOWN — 사람 개입 필요(락 유지)"였는데, 서버를 보면 요청한 digest 그대로의 컨테이너가 healthy로 떠 있었다.\
배포는 성공했는데 agent는 실패로 판정한 것 — 이것이 false-UNKNOWN이다.

> **UNKNOWN** — 배포가 됐는지 안 됐는지 agent가 단정하지 못하는 상태.\
> 예: "완료"로 위장하면 위험하므로 락을 쥔 채 사람을 부른다.

> **digest** — 이미지 내용을 그대로 지목하는 지문.\
> 예: 태그(`:latest`)는 옮겨 붙을 수 있지만 digest는 그 내용이 아니면 안 맞는다.

원인 규명이 오래 걸린 이유는 dispatch 오류가 어디에도 안 남았기 때문이다.\
agent 로그는 기동 한 줄뿐이고, DB의 detail 컬럼은 NULL이었다.\
coordinator가 UNKNOWN 분기에서 "invalid compose project"라는 정확한 단서를 버렸고, 이력 이벤트엔 detail 필드 자체가 없었다 — "사람 개입 필요"라면서 정작 사람에게 줄 단서를 안 남긴 관측 공백이다.

## 2. 무엇을 고민했나

근본 결함에 두 안이 명시적으로 기록되고 기각 사유까지 남았다.

- **A-1 — agent가 모든 compose 하위 명령에 image env 주입.**\
  이미지 주입은 agent의 책임이고, fallback 이미지가 compose 파일에 새지 않아 digest 고정 원칙이 흐려지지 않는다.
- **A-2 — compose 파일에 `${CORE_IMAGE:-placeholder}` 기본값.**\
  파일 한 줄로 끝나지만, fallback 이미지가 파일에 남아 "digest만 실행한다"는 원칙에 구멍을 낸다.

A-1을 택했다.

## 3. 그래서 이렇게

agent의 dispatch 순서를 펼쳐 서버에서 손으로 하나씩 재현하자 원인이 드러났다.

```text
STEP 3  up    (CORE_IMAGE 주입)   컨테이너 Running · exit 0     성공
STEP 4  ps -q (env 없음)          invalid compose project      즉시 실패
STEP 1  down  (env 없음)          같은 오류 · exit 1           즉시 실패
```

호스트 compose가 `image: ${CORE_IMAGE}`(기본값 없음)인데 Executor는 `CORE_IMAGE`를 `up`에만 주입했다.\
compose는 어떤 하위 명령이든 프로젝트를 로드할 때 모든 서비스의 image를 먼저 검증하므로, 변수가 비면 프로젝트 자체가 무효가 된다.

```text
호스트 compose: image: ${CORE_IMAGE}  (기본값 없음)
        ↓
Executor는 CORE_IMAGE 를 up 에만 주입
        ↓
compose는 어느 하위 명령이든 프로젝트 로드 시 모든 image 를 먼저 검증
        ↓
env 없는 ps -q · down 은 프로젝트가 무효라 즉시 실패
        ↓
정리(down) 실패 = 계약상 UNKNOWN = false-UNKNOWN
```

판정 문장이 사건의 성격을 정확히 규정한다.\
로직은 계약대로 동작했고, 입력(compose 명령이 성립하지 않음)이 틀렸다.\
fail-closed는 옳게 작동해서 잘못된 "완료"로 위장되지 않았다 — 0.36초의 정체도 앱 부팅과 무관한 같은 config 오류로 두 명령이 즉시 실패한 것이다.

> **fail-closed** — 확신이 없으면 통과가 아니라 정지 쪽으로 닫는 설계.\
> 예: 정리에 실패하면 "됐겠지"가 아니라 UNKNOWN으로 사람을 부른다.

## 4. 코드 — 실제 커밋에서

`ps`·`down`에는 실행에 안 쓰이는 placeholder를 주입하고, `up`만 실제 pinned digest를 주입한다.

```go
// internal/dispatch/dispatch.go:112-119 (발췌) — placeholder 상수에 사건의 결론을 박았다
// 이 명령들은 기존 컨테이너를 프로젝트 라벨로 다루므로 image 값 자체는 실행에 쓰이지 않는다 —
// 파싱만 되면 되고, pull되지 않을 값으로 두어 오용을 눈에 띄게 한다. up은 별도로 실제 pinned
// digest를 주입한다(digest 고정은 up이 늘 실주입하므로 유지된다).
const composeImagePlaceholder = "noncreate.invalid/unused:noncreate-ops-only"
```

## 5. 구현 중 마주친 문제

원인에 닿기 전 두 해석이 빗나갔고, 그 오독을 일부러 기록으로 남겼다.\
첫째는 "CI 빌드 실패" — 빨간 X는 이미지 빌드가 아니라 그 다음 CD 배포-요청 워크플로였다.\
둘째는 "Spring 부팅 경합" — 시작과 UNKNOWN 기록 사이가 0.36초뿐이라 그럴듯했지만, 헬스에 90초 deadline이 있어 0.36초에 끝날 수 없었다.\
오독을 깬 것은 새 데이터가 아니라 기존 계약과의 산술적 모순이었다.

관측 공백을 메우려고 detail을 쓰기 시작한 1차 수정이 새 치명 결함을 만들었다.\
detail 컬럼은 JSON 타입이라 평문을 그대로 바인딩하면 MySQL이 INSERT 전체를 거부한다 — 하필 실제 UNKNOWN이 나는 순간에만 이력이 통째로 유실되고 재전송이 재실행될 수 있었다.\
실 컬럼에 롤백 트랜잭션으로 재현해 확인한 뒤 JSON 인코딩으로 고쳤다.

## 6. 결론

agent를 재빌드·재배포하자 전 파이프라인(push→CI→GHCR→서명요청→게이트1·2→모드→락→pull→up→verify→헬스→완료)이 HTTP 200으로 그린이 됐다.\
첫 무결 실배포다.

이 사건의 교훈이 그대로 다음 작업의 입력이 됐다 — "통합에서 처음 실행되는 명령"은 단위 테스트가 못 잡는다.\
dispatch는 이미 여러 리뷰를 거쳤지만, 실제 compose 파일 + 실제 env 주입 경로는 이번이 처음이었고, up만 env를 주는 비대칭은 실환경에서만 드러났다.
