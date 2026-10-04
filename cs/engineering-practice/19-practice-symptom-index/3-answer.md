# engineering-practice/19-practice-symptom-index — 정답

## 정답

### 1. 흐름의 일곱 칸과 다섯 증상

```text
  작성 ──▶ 리뷰 ──▶ 통합 ──▶ 빌드·CI ──▶ 배포 ──▶ 운영 ──▶ 기억
           리뷰 병목  머지 지옥  CI 불신     배포 공포          "이건 왜 이렇게 했지?"
```

- 흐름의 한 칸이 막히면 **앞 칸에 일이 쌓인다.** 막힌 변경은 결국 오른쪽 칸에서 터지므로, 원인 칸이 증상 칸보다 한두 칸 앞(왼쪽)에 있는 경우가 많다. 아래 예들이 모두 그렇다.
- 예 1: 머지 지옥(통합 칸)의 원인이 리뷰 대기(리뷰 칸)다. PR이 며칠 대기하는 동안 작성자가 그 위에 작업을 쌓아 브랜치가 길어진다([05-2](../05-code-review/2-summary.md) → [04-1](../04-branching-strategies/2-summary.md)).
- 예 2: 배포 공포·큰 배치(배포 칸)의 원인이 느린 파이프라인(CI 칸)이다. 커밋 단계가 40분이면 개발자가 변경을 모아서 올린다([06-5](../06-ci-cd-pipelines/2-summary.md)).
- 다른 예: 캐시 키 누락(빌드 칸)이 운영의 잘못된 설정(운영 칸)으로 보인다([07-2](../07-build-systems-and-reproducibility/2-summary.md)).

### 2. "CI가 빨갛다"를 가르는 질문

| 질문 (싼 것부터) | "예"이면 | 처방 | leaf |
|---|---|---|---|
| 같은 커밋을 재실행하면 초록이 되나? | 불안정 테스트 | 격리 목록 + 버그로 추적 | [06-1](../06-ci-cd-pipelines/2-summary.md) · [testing/09](../../testing/09-flaky-tests/2-summary.md) |
| 각 브랜치는 초록이고 병합 결과에서만 빨강인가? | 의미 충돌 | 병합 결과(병합 큐)에 CI | [06-2](../06-ci-cd-pipelines/2-summary.md) · [04-2](../04-branching-strategies/2-summary.md) |
| 로컬은 초록, CI만 빨강인가? | 선언되지 않은 입력(시간대·로캘·도구 판) | 코드에서 입력 명시, 도구 판 고정 | [07-1](../07-build-systems-and-reproducibility/2-summary.md) |

- 하나 더: 도구를 켠 첫날부터 계속 빨강이면 레거시 전체에 건 게이트다. 기준선(래칫)으로 새 위반만 막는다([14-2](../14-quality-standards/2-summary.md)).
- 한 원인으로 묶어 재시도를 켜면: 재실행해도 빨간 의미 충돌·환경 의존은 그대로 남고, 진짜 경쟁 조건까지 "재시도로 초록"이 되어 숨는다. 결국 빨강을 아무도 안 보게 된다([19 장애 2](2-summary.md)).

### 3. 각자 초록, 합치면 빨강

(06 실험, git 2.43.0 / eclipse-temurin:21-jdk javac)

```text
== feature-a 단독 CI
CI: GREEN
== feature-b 단독 CI
CI: GREEN
...
== 병합 충돌 여부: 0개 파일
== 병합 결과 main CI
src/Invoice.java:2: error: cannot find symbol
    public static long amount() { return Price.total(500, 2); }
...
CI: RED
```

- 텍스트 병합(git의 3-way merge)은 내용을 **줄** 단위로 맞춘다(이름 바꾸기·삭제 같은 파일 단위 충돌도 잡지만 — [03](../03-version-control-and-git-internals/2-summary.md) — 코드의 의미는 검사하지 않는다). 한 브랜치가 메서드 시그니처를 바꾸고 다른 브랜치가 옛 시그니처를 새로 호출하면, 겹치는 줄이 없어 충돌 0개로 병합된다. 의미가 맞는지는 컴파일·테스트만 안다.
- 처방: CI를 브랜치가 아니라 **병합 결과**에 돌린다(병합 큐). 브랜치를 짧게 두어 넓은 변경(이름 바꾸기)을 다른 브랜치가 일찍 따라가게 한다([06-2](../06-ci-cd-pipelines/2-summary.md), [04-2](../04-branching-strategies/2-summary.md)).

### 4. 통합 주기 시뮬레이션

(04 시뮬레이션, git 2.43.0 / Node 18.19.1, 시드 1~5 — 스크립트로 만든 커밋, 실측 아님)

| 통합 주기 | 충돌 난 병합 1회당 줄 | 충돌 줄 합계 |
|---|---|---|
| 1일 | 6.6~9.8 | 94~151 |
| 5일 | 39.1~44.1 | 453~529 |
| 20일 | 267.3~288.0 | 802~864 |

- 충돌 줄 합계는 20일 주기가 1일 주기의 약 5.3~9.1배(802/151 ~ 854/94).
- 덩어리 수의 오해: 덩어리 수는 5일 주기가 20일보다 많거나 같았다(20일 43~51, 5일 48~61). 덩어리 수만 보면 "오래 갈라져도 충돌이 적다"고 오해한다. 04 노트의 해석은 오래 갈라질수록 인접한 충돌이 큰 덩어리 하나로 합쳐진다는 것이다(덩어리 크기 분포는 따로 세지 않았다). 그래서 줄 수와 "가장 오래된 편집이 며칠 전 것인가"를 함께 본다.

### 5. 한 서버만 이상하다

- 모을 것: 서버별 **실행 중인 산출물의 해시**(또는 빌드 해시). 사람이 친 목록이 아니라 인벤토리 전체에서 모은다.
- 읽는 법: 해시 종류 수를 센다. 1이면 일치, 2 이상이면 배포 누락·혼재다.

(06 모형 실험, bash + sha256sum — 디렉터리 8개를 서버로 본 시뮬레이션이며 실제 Knight 시스템이 아니다)

```text
== 수동 배포 (작업자가 입력한 목록: s1..s7)
수동 절차 종료 — 검증 단계 없음, 성공으로 보고
== 같은 상태에서 자동 검증 단계만 돌리면
      1 29bbb1d48f8c
      7 bd899fbbbdb9
VERIFY: FAIL (drift)
s8 v1 old-flag=PowerPeg
```

- 수동 절차는 "끝났다"만 알고, 검증 단계는 "8대가 같은가"를 묻는다.
- 응답하지 않는 서버는 건너뛰지 않고 **실패로 센다**(`UNREACHABLE`). 건너뛰면 바로 그 서버가 누락된 서버일 때 검증이 초록이 된다. 해시 종류 수만 보면 전부 `UNREACHABLE`일 때 종류가 1개라 초록이 되므로, 응답 실패는 종류 수와 따로 판정한다([19 적용 3](2-summary.md)).

### 6. 운영 번들에 스테이징 주소

- 갈래 1 — **캐시 키에서 입력이 빠졌다.** 07의 직접 만든 해시 캐시(JDK 21)에서 키를 소스만으로 만들자, `API_URL`을 운영 값으로 바꿔도 키가 같아 스테이징 산출물을 재사용했다.

```text
== keyMode=src
HIT  key=70af500bf94e  requested API_URL=https://prod.example.invalid  artifact -> const API = "https://staging.example.invalid";
== keyMode=src+conf
MISS key=289c76ee06ca  requested API_URL=https://prod.example.invalid  artifact -> const API = "https://prod.example.invalid";
```

- 갈래 2 — **시각 기반 판정이 틀렸다.** GNU Make 4.3 실험에서 입력 내용을 바꾸고 mtime을 2000-01-01로 돌리자 `make: 'out.txt' is up to date.`가 나왔고 산출물은 옛 내용(`out.txt = a`)이었다. 캐시 복원·체크아웃이 mtime을 바꾸는 환경에서 같은 일이 생긴다.
- 확인: 캐시 없이 깨끗한 환경에서 다시 빌드해 산출물 해시를 비교한다. 다르면 캐시가 오염됐다. 재발 방지는 키에 모든 입력(설정·플래그·도구 판)을 넣고, 릴리스 빌드는 깨끗한 환경에서 한다([07-2](../07-build-systems-and-reproducibility/2-summary.md)).

### 7. 리뷰 병목의 두 문제

| | 시간 문제 | 질 문제 |
|---|---|---|
| 모양 | PR이 며칠 대기, 열린 PR 증가 | 거대 PR이 몇 분 만에 LGTM |
| 결과 | 장수 브랜치·머지 지옥 | 동작 변경이 묻혀 버그 통과 |
| leaf | [05-2](../05-code-review/2-summary.md) | [05-1](../05-code-review/2-summary.md) |

- 05 실험(git 2.43.0): 섞인 PR은 `31 files changed, 31 insertions(+), 31 deletions(-)`. 그중 동작 변경은 `<=` → `<` **한 줄**(추가·삭제 합 2줄)이다. 전체 62줄 중 2줄. `-w`로도 걸러지지 않는다(이름 바꾸기는 공백 변경이 아니다). 커밋을 목적별로 나누면 동작 커밋은 `1 file changed, 1 insertion(+), 1 deletion(-)`이다.
- 공통 처방: **작은 PR**. 작으면 리뷰어가 이해할 수 있는 양이라 질이 오르고, 빨리 볼 수 있어 대기가 준다. 대기가 줄면 작성자가 위에 쌓지 않아 PR이 덜 커진다. 목적별 분리(리팩터링 / 동작 변경)도 같은 효과다.

### 8. "이건 왜?" — 세율 복사본

- 순서
  1. 같은 규칙이 어디에 있는지 찾는다: `git grep -n '0.10'`, `git grep -n 'tax'`.
  2. 이유를 이력에서 찾는다: `git log -S '<상수나 식>' --oneline`(병합 해결에서 사라졌을 수 있으면 `-m`), `git blame -w -C <파일>`. 커밋 메시지·PR 설명에 이유가 있으면 끝.
  3. 복사본마다 같은 입력을 넣어 결과를 비교한다.
- 10 실험 출력(git 2.43.0 · OpenJDK 21.0.12):

```text
== 동작: 브랜치 debt-missed
OrderService    FOOD  100  BOOK    0
InvoiceService  FOOD  100  BOOK    0
RefundService   FOOD  100  BOOK  100
QuoteService    FOOD  100  BOOK    0
```

- 네 복사본 중 `RefundService`만 BOOK 면세 변경이 빠졌다. 예외·에러는 없다.
- 처방: 규칙을 한 곳으로 모은다(10의 repay 브랜치는 `TaxPolicy` 하나로). 당장 못 모으면 모든 복사본에 같은 입력을 넣는 비교 테스트를 둔다.
- 이유를 끝내 못 찾으면: 지금 알아낸 사실과 판단을 **결정 기록(ADR)**으로 남긴다([software-design/47](../../software-design/47-architecture-decision-records/2-summary.md)). 요구라면 요구 ID를 코드·테스트에 단다([02-3](../02-requirements-engineering/2-summary.md)).

### 9. 지표 게이밍

(09 실험, git 2.43.0 / Node 18.19.1)

| 지표 | honest | gamed | 판정 |
|---|---|---|---|
| 배포 빈도 | 2.6회/주 | 7.6회/주 | 좋아짐 |
| 변경 리드 타임 중앙값 | 50.0h | 50.0h | 그대로 |
| 변경 실패율 | 22.2% | 7.7% | 좋아짐 |
| 실패 배포 복구 시간 중앙값 | 3.38h | 3.38h | 그대로 |
| 배포 재작업률 | 11.1% | 0.0% | 좋아짐 |

- 좋아진 셋은 분모(배포 수)와 분류를 조작해 움직였다. 실패 건수(2건)와 리드 타임·복구 시간은 그대로다.
- 점검 줄: `(점검) 새 커밋 없는 배포 17회`(honest는 0회). 같은 버전 재배포로 분모를 늘린 흔적이다.
- 같은 모양: 날짜만 올린 문서 신선도(경고 7건 → 4건, 내용 문제는 그대로 — [11-5](../11-documentation-practices/2-summary.md)), 미사용 변수를 `unused…`로 바꾼 위반 수 감소([14-4](../14-quality-standards/2-summary.md)), 억제 주석이 늘어난 부채 점수([10-5](../10-technical-debt/2-summary.md)), 스토리 포인트 인플레이션([01-3](../01-lifecycle-and-agile/2-summary.md)).

### 10. "누가 실수했다"에서 멈춘 회고

- 놓친 것: 그 실수를 **가능하게 만든 구조**. 사람이 대상 목록을 치고, 끝났는지 확인하는 단계가 없었다. 다른 사람이 해도 같은 일이 난다.
- SEC 명령 34-70694(Knight Capital, 2013)는 회사를 상대로 한 명령이다. 기술자의 복사 누락을 사실로 적되(이름은 없다), 위반으로 지적한 것은 그 누락을 잡을 통제·절차의 부재였다. 두 번째 기술자가 배포를 검토하지 않았고 그것을 요구하는 서면 절차가 없었다(¶15·¶26). 배포를 "간단히 다시 확인하는" 서면 절차가 있었다면 빠진 서버를 찾아 8월 1일의 사건을 막을 수 있었다고 적었다(¶41). 자세한 것은 [20](../20-practice-incidents/2-summary.md).
- 장치 세 개
  1. 인벤토리 기반 자동 배포 — 대상 목록을 사람이 치지 않는다([06-3](../06-ci-cd-pipelines/2-summary.md)).
  2. 배포 후 해시 대조 — 종류가 2개 이상이거나 응답 없는 인스턴스가 있으면 배포 실패([19 적용 3](2-summary.md)).
  3. 플래그 이름 재사용 금지와 다 쓴 플래그·죽은 코드 삭제 — 누락된 서버가 있어도 옛 코드가 깨어나지 않게 한다([04-4](../04-branching-strategies/2-summary.md), [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md)).
- 사고 회고 형식(비난 없는 포스트모템)은 [reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md).
