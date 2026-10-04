# engineering-practice/06-ci-cd-pipelines — 지속적 통합·전달·배포: 변경 하나가 운영까지 가는 자동화된 DAG — 정리 (힌트)

## 해결하는 문제

통합과 배포를 사람이 가끔, 손으로 하면 두 가지가 깨진다.

```text
  1) 통합을 미루면                     2) 배포를 손으로 하면
  A ──(3주 작업)──┐                    서버 8대 목록을 작업자가 입력
  B ──(3주 작업)──┼─> 한꺼번에 병합       s1 s2 s3 s4 s5 s6 s7   ← s8 누락
  C ──(3주 작업)──┘    → 충돌·깨진 빌드     검증 단계 없음 → "성공"으로 보고
                       → 누가 깨뜨렸나?     → s8만 옛 코드로 운영 트래픽 처리
```

- 통합을 미루면 충돌과 깨짐이 한꺼번에 몰린다. 원인 후보가 많아 범인 찾기가 어렵다.
- 손으로 하는 배포는 단계 하나를 빠뜨려도 아무도 모를 수 있다.

쉬운 예: 공장 조립 라인이다.
- 부품을 만들 때마다 바로 조립해 보면(통합), 맞지 않는 부품을 그날 안다.
- 라인의 각 공정이 자동 검사를 거치면, 검사에 떨어진 제품은 다음 공정으로 가지 않는다.

똑같은 구조다.\
코드 변경 = 부품, 파이프라인 = 조립 라인, 테스트 = 공정 검사다.

실무 예:
- 두 PR이 각각 초록인데 둘 다 병합한 main은 빨갛다(아래 실험).
- main이 며칠째 빨간데 "원래 깨져 있던 테스트"라며 다들 무시한다. 새로 깨진 것을 아무도 못 알아챈다.
- Knight Capital(2012-08-01): 작업자가 새 코드를 서버 8대 중 1대에 복사하지 않았다. 두 번째 사람의 확인 절차도 없었다(SEC 명령 34-70694 요약). 그 1대에서 재사용된 플래그가 옛 Power Peg 코드를 깨웠다. 자세한 경과는 [reliability/04](../../reliability/04-failure-modes-catalog/2-summary.md)·[reliability/23](../../reliability/23-deployment-strategies/2-summary.md).

## 동작·원리

### 1. 세 용어 — CI, 지속적 전달, 지속적 배포

```text
  커밋 ─> [빌드·단위 테스트] ─> [통합·인수 테스트] ─> [스테이징 배포] ─> (승인?) ─> [운영 배포]
         └──── CI ─────────┘
         └──────────────── 지속적 전달(CD): 언제든 운영에 낼 수 있는 상태 ─────┘
         └──────────────── 지속적 배포: 승인 없이 자동으로 운영까지 ─────────────────────────┘
```

- *지속적 통합(CI, Continuous Integration)*: 팀원이 작업을 자주 통합하고, 통합마다 자동 빌드(테스트 포함)로 검증하는 실천.
  - SWE@G 23장이 Fowler의 정의를 인용한다: "integrate their work frequently … Each integration is verified by an automated build (including test)".
  - 흔한 오해: "CI 서버(Jenkins 등)를 깔면 CI다." Fowler의 실천 목록에는 "Everyone Pushes Commits To the Mainline Every Day"가 들어 있다. 도구가 있어도 브랜치가 몇 주씩 떨어져 있으면 통합이 지속적이지 않다.
- *지속적 전달(Continuous Delivery)*: 소프트웨어를 언제든 운영에 릴리스할 수 있게 만드는 규율(Fowler bliki "ContinuousDelivery").
- *지속적 배포(Continuous Deployment)*: 모든 변경이 파이프라인을 지나 **자동으로** 운영에 들어간다(같은 글). 전달은 "할 수 있다", 배포는 "실제로 한다"다.
  - 흔한 오해: CD를 늘 지속적 배포로 읽는다. 약어 CD는 두 뜻으로 쓰인다. 문서마다 어느 쪽인지 확인한다.
- 출처마다 강조가 다르다.
  - Fowler·Humble–Farley: 파이프라인과 자동화 실천을 중심으로 정의.
  - SWE@G 24장(Google 관례): "smaller batches of changes result in higher quality; in other words, faster is safer". 이것은 Google의 경험에서 나온 주장이다. 측정 근거는 [09 DORA 지표](../09-dora-metrics/2-summary.md)가 다룬다.

### 2. 파이프라인 = 작업 DAG

```text
                 ┌─> compile(3) ─┬─> unit-test(5) ─────────┐
  checkout(1) ───┤               └─> integration-test(8) ──┼─> package(2) ─> deploy-staging(3) ─> smoke(2) ─> deploy-prod(3)
                 └─> lint(2) ──────────────────────────────┘
  (괄호 = 소요 분, 예시)        가장 긴 경로(임계 경로) = 1+3+8+2+3+2+3 = 22분
```

- *배포 파이프라인(deployment pipeline)*: "버전 관리에서 사용자 손까지 소프트웨어를 옮기는 과정을 자동화해 드러낸 것"(Humble–Farley 『Continuous Delivery』 5장 "Anatomy of the Deployment Pipeline").
- 작업(job) 사이의 "먼저 끝나야 한다" 관계는 방향 그래프다. 순환이 있으면 실행 순서를 정할 수 없으니 DAG여야 한다.
- 실행기는 위상정렬 순서로 작업을 꺼낸다. 의존이 없는 작업(compile·lint)은 동시에 돈다.
- 총 시간은 작업 합(29분, 예시)이 아니라 **임계 경로**(22분)다. 빠르게 하려면 임계 경로 위 작업을 줄여야 한다.
  - *임계 경로(critical path)*: 시작에서 끝까지 소요 시간 합이 가장 큰 경로. 이 경로 위 작업이 늦어지면 전체가 늦어진다.
- 앞 작업이 실패하면 후손 작업은 건너뛴다. 실패한 산출물이 다음 공정으로 가지 않는다.

### 3. 커밋 단계와 이후 단계 — 빠른 것 먼저

```text
  커밋 단계(빠름, 개발자가 기다림)        이후 단계(느림, 비동기)
  컴파일·단위 테스트·정적 분석             통합·인수·성능 테스트, 스테이징
  Humble–Farley: 5분 미만이 이상적,       실패해도 커밋 단계보다 늦게 알게 됨
  10분은 넘기지 말 것
```

- Humble–Farley 5장: "The commit stage should ideally take less than five minutes to run, and certainly no more than ten minutes."
- Fowler "Continuous Integration"(2024-01-18 개정판): XP의 "ten minute build" 지침을 대부분 프로젝트에 합당하다고 본다.
- SWE@G 23장(Google 관례): 제출 전(presubmit)에는 "only fast, reliable ones"를 돌린다. 느리고 큰 테스트는 제출 뒤(post-submit) 비동기로 돌린다.
  - *presubmit / post-submit*: 변경을 저장소에 넣기 전 / 넣은 뒤에 도는 검사.

### 4. 파이프라인 실천 — 한 번 빌드, 같은 방식으로 배포

Humble–Farley 5장 "Deployment Pipeline Practices"의 절 제목:

| 실천 | 막는 장애 |
|---|---|
| Only Build Your Binaries Once | 환경마다 다시 빌드 → 테스트한 것과 다른 바이너리가 운영에 감 |
| Deploy the Same Way to Every Environment | 운영 배포 절차만 수동·특수 → 운영에서 처음 실행되는 절차 |
| Smoke-Test Your Deployments | 배포는 "성공"인데 서비스가 안 뜸 |
| Deploy into a Copy of Production | 운영과 다른 환경에서만 검증 |
| Each Change Should Propagate through the Pipeline Instantly | 변경이 쌓여 한꺼번에 통과 → 범인 찾기 어려움 |
| If Any Part of the Pipeline Fails, Stop the Line | 빨간 파이프라인 위에 변경이 계속 쌓임 |

- "한 번 빌드"는 [07 빌드 시스템](../07-build-systems-and-reproducibility/2-summary.md)의 재현 가능성과 짝이다. 같은 산출물(해시)을 스테이징과 운영에 그대로 올린다.

### 실험: 각자 초록인 두 브랜치, 병합하면 빨강

같은 파일을 건드리지 않아 git은 충돌 없이 병합한다. 그래도 프로그램은 깨진다.

```text
  base: Price.total(unit, qty)
   ├─ feature-a: total → totalWithTax(unit, qty, rate) 로 바꾸고 호출처 갱신   CI 초록
   └─ feature-b: 새 파일 Invoice.java 에서 Price.total(500, 2) 호출             CI 초록
  main = base + a + b  → 텍스트 충돌 0, 컴파일 실패
```

(실험, git 2.43.0 / eclipse-temurin:21-jdk javac, 2026-10-05 — `scratchpad/ep/06/e1-semantic-merge/run.sh`)

```text
== feature-a 단독 CI
CI: GREEN
== feature-b 단독 CI
CI: GREEN
== main + A 병합
Merge made by the 'ort' strategy.
 src/Invoice.java | 3 +++
 1 file changed, 3 insertions(+)
 create mode 100644 src/Invoice.java
== 병합 충돌 여부: 0개 파일
== 병합 결과 main CI
src/Invoice.java:2: error: cannot find symbol
    public static long amount() { return Price.total(500, 2); }
                                              ^
  symbol:   method total(int,int)
  location: class Price
1 error
CI: RED
```

- 출력의 `== main + A 병합` 아래 줄은 A를 먼저 병합한 main에 B를 병합한 결과다(스크립트의 구획 표시).
- 관찰: 브랜치별 CI는 "그 브랜치"를 검사했을 뿐이다. 병합 결과는 아무도 검사하지 않았다.
- Fowler는 이것을 *의미 충돌(semantic conflict)*이라 부른다. 함수 이름을 바꾼 사람과 그 함수를 새로 호출한 사람의 충돌은 버전 관리 도구가 못 잡는다. 정적 타입 언어는 컴파일 오류로 잡지만, 함수 본문의 미묘한 의미 변경은 컴파일도 못 잡는다. 그래서 자기 테스트 코드(self-testing code)가 필요하다("Continuous Integration", Semantic Conflicts 절).
- SWE@G 23장은 같은 현상을 "mid-air collision"이라 부른다. 서로 다른 파일을 건드린 두 변경이 테스트를 깨뜨린다. 작은 저장소는 제출을 직렬화해 피할 수 있다고 쓴다.

## 쓰이는 자료구조·알고리즘

- **DAG와 위상정렬** — 파이프라인 작업의 실행 순서. Kahn 알고리즘(진입 차수 0부터 꺼냄)이나 DFS 종료 순서의 역순 → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)(위상정렬 절).
- **임계 경로(DAG 최장 경로)** — 위상정렬 순서로 "가장 이른 시작 = 선행 작업 끝 시각의 최댓값"을 구한다. O(V+E).
- **실패 전파 = 후손 집합** — 실패한 작업에서 간선을 따라 도달하는 모든 작업을 건너뛴다(그래프 탐색).
- **이분 탐색으로 범인 찾기** — 여러 변경을 묶어 돌린 배치가 실패하면 반으로 나눠 다시 돌린다. SWE@G 23장: TAP은 실패한 배치를 개별 변경으로 쪼개 다시 돌린다. `git bisect`도 같은 원리다 → [03 git 내부](../03-version-control-and-git-internals/2-summary.md).
- **큐(병합 큐)** — 병합 대기 변경을 줄 세워, "현재 main + 내 변경" 결과를 검사한 뒤 넣는다. 직렬화로 mid-air collision을 막는다.

### 실험: 파이프라인 DAG의 위상정렬·임계 경로·실패 전파

```java
// PipelineDag.java 핵심 — Kahn 위상정렬 + 가장 이른 시작 시각 + 실패한 작업의 후손 skip
while (!ready.isEmpty()) {
    String n = ready.poll();
    Job j = byName.get(n);
    int est = j.needs().stream().mapToInt(finish::get).max().orElse(0);       // 선행이 다 끝난 시각
    boolean upstreamBad = j.needs().stream().anyMatch(p -> !status.get(p).equals("ok"));
    if (upstreamBad) { status.put(n, "skipped"); finish.put(n, est); }
    else if (n.equals(failing)) { status.put(n, "FAILED"); finish.put(n, est + j.minutes()); }
    else { status.put(n, "ok"); finish.put(n, est + j.minutes()); }
    for (String c : children.getOrDefault(n, List.of()))
        if (indeg.merge(c, -1, Integer::sum) == 0) ready.add(c);              // 진입 차수 0이 되면 실행 가능
}
```

(실험, eclipse-temurin:21-jdk `java PipelineDag.java` 다음 `java PipelineDag.java unit-test`, 2026-10-05 — 소요 분은 예시 값, `---` 아래가 두 번째 실행)

```text
checkout          start= 0 end= 1 ok
compile           start= 1 end= 4 ok
lint              start= 1 end= 3 ok
unit-test         start= 4 end= 9 ok
integration-test  start= 4 end=12 ok
package           start=12 end=14 ok
deploy-staging    start=14 end=17 ok
smoke-test        start=17 end=19 ok
deploy-prod       start=19 end=22 ok
topo order = [checkout, compile, lint, unit-test, integration-test, package, deploy-staging, smoke-test, deploy-prod]
sequential sum = 29 min, DAG(parallel) = 22 min
---
checkout          start= 0 end= 1 ok
compile           start= 1 end= 4 ok
lint              start= 1 end= 3 ok
unit-test         start= 4 end= 9 FAILED
integration-test  start= 4 end=12 ok
package           start=12 end=12 skipped
deploy-staging    start=12 end=12 skipped
smoke-test        start=12 end=12 skipped
deploy-prod       start=12 end=12 skipped
topo order = [checkout, compile, lint, unit-test, integration-test, package, deploy-staging, smoke-test, deploy-prod]
sequential sum = 29 min, DAG(parallel) = 12 min
```

- 단위 테스트가 9분에 실패해도 integration-test는 12분까지 돈다. 형제 작업이라 서로 모른다. 실패 즉시 형제를 취소할지는 CI 제품의 설정이다.

## 적용 — 풀어나가는 법

### 1. 파이프라인을 DAG로 선언한다

GitHub Actions 형식 예시(실행하지 않은 설정 모양, 액션 버전 태그는 예시):

```yaml
on:
  pull_request:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mvn -B -q verify -DskipITs        # 커밋 단계: 컴파일 + 단위 테스트
      - uses: actions/upload-artifact@v4     # 한 번 빌드한 산출물을 다음 작업에 넘긴다
        with: { name: app, path: target/*.jar }
  integration:
    needs: build                             # 간선: build → integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mvn -B -q verify                    # pom에 failsafe의 integration-test·verify goal을 연결했을 때만 통합 테스트가 돈다. 단위 테스트도 다시 돈다
                                               # (surefire에는 단위 테스트만 건너뛰는 기본 사용자 속성이 없다 — skipTests는 failsafe도 건너뜀)
  deploy-staging:
    needs: [build, integration]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4            # deploy.sh·smoke.sh를 쓰려면 이 작업에서도 받는다(작업마다 새 실행 환경)
      - uses: actions/download-artifact@v4   # 다시 빌드하지 않고 같은 jar를 받는다
        with: { name: app }
      - run: ./deploy.sh staging app.jar && ./smoke.sh staging
```

- GitHub Actions 문서(workflow syntax, `jobs.<job_id>.needs`): 작업은 기본적으로 병렬로 돈다. `needs`로 의존을 걸면, 선행 작업이 실패하거나 건너뛰어진 경우 그 작업도 건너뛴다(`if: always()` 같은 조건식이 없으면). 위 DAG 실험의 skip 전파와 같은 규칙이다.
- 원칙: 빠른 검사를 앞에, 느린 검사를 뒤에. 산출물은 한 번 만들어 넘긴다. 운영 배포도 같은 스크립트(`deploy.sh`)를 쓴다.
- 이 예시의 빈틈: `integration` 작업은 소스에서 다시 빌드한다. 그래서 통합 테스트가 검사한 jar와 스테이징에 올리는 jar(`build` 작업 산출물)는 서로 다른 빌드다. Humble–Farley는 운영에 가는 바이너리가 인수 테스트를 거친 것과 "exactly the same"이어야 한다고 쓴다. 지키려면 `integration`도 산출물을 받아 그 jar를 띄운 뒤 테스트한다.
- Maven 문서(Failsafe "Usage"): Failsafe는 `pom.xml`에 `integration-test`·`verify` goal을 추가해야 쓰인다. 기본 jar 프로젝트에서 `mvn verify`만으로 통합 테스트(`*IT`)가 돌지 않는다.
- GitHub 문서: GitHub 호스팅 러너는 작업마다 새 VM이다(단일 CPU 러너는 공유 VM의 컨테이너). 앞 작업이 받은 저장소 파일은 다음 작업에 없다.

### 2. 병합 결과를 검사한다

- PR의 CI는 "PR 브랜치"가 아니라 "대상 브랜치 + PR"의 병합 결과를 검사해야 의미 충돌을 잡는다.
- 변경이 많으면 병합 직전에 다시 검사하는 큐를 둔다(GitHub merge queue, GitLab merge trains 같은 기능). GitHub 문서는 merge queue가 "Require branches to be up to date before merging" 보호 규칙과 같은 이득을 주되, 작성자가 브랜치를 갱신하고 기다릴 필요가 없다고 설명한다.
- 큐 없이도: PR을 병합하기 전에 최신 main을 받아(rebase/merge) 다시 돌린다.

### 3. 빨간 main은 그 자리에서 되돌린다

- Fowler: "Usually the best way to fix the build is to revert the latest commit from the mainline". 고치는 동안 나머지 팀이 계속 일할 수 있다.
- SWE@G 23장: "Rolling a change back is often the fastest and safest route to fix a build."
- 경계: SWE@G 23장은 "CI가 초록이 아니면 아무도 커밋 못 한다"는 정책을 "probably misguided"라고 본다. 원인을 알고 운영에 영향이 없음이 분명하면 커밋을 막는 것은 지나치다는 것이다. 핵심은 **실패를 조사하지 않은 채 쌓지 않는 것**이다.

### 4. 배포에서 사람 손을 뺀다 — 그리고 검증한다

- 배포 대상 목록은 사람이 입력하지 않고 인벤토리(코드)에서 읽는다.
- 배포 뒤 모든 대상이 같은 산출물(해시·버전)을 돌리는지 확인한다. 스모크 테스트를 돈다.
- 롤백도 같은 파이프라인으로 한다. 손 롤백은 또 하나의 수동 배포다([reliability/23](../../reliability/23-deployment-strategies/2-summary.md)).

### 실험: 수동 배포 누락을 검증 단계가 잡는다 (시뮬레이션)

디렉터리 8개를 서버로 보고, 파일 복사를 배포로 본 **시뮬레이션**이다. 실제 Knight 시스템을 재현한 것이 아니다.

```text
(실험, bash + sha256sum, 2026-10-05 — scratchpad/ep/06/e3-deploy-drift/run.sh)
== 수동 배포 (작업자가 입력한 목록: s1..s7)
수동 절차 종료 — 검증 단계 없음, 성공으로 보고
== 같은 상태에서 자동 검증 단계만 돌리면
      1 29bbb1d48f8c
      7 bd899fbbbdb9
VERIFY: FAIL (drift)
s8 v1 old-flag=PowerPeg
== 자동 배포 (인벤토리 전체) + 검증
      8 bd899fbbbdb9
VERIFY: OK (all identical)
```

- 관찰: 수동 절차는 "끝났다"만 안다. 검증 단계는 "8대가 같은가"를 묻는다. 해시 종류가 2개면 누락이다.
- SEC 명령(요약)은 Knight에 배포를 두 번째 기술자가 확인하게 하는 서면 절차가 없었다고 지적한다. 사람의 이중 확인 대신 위처럼 자동 검증을 둘 수도 있다(해석).

### 진단 — 파이프라인 건강을 보는 숫자

| 보는 것 | 나쁜 신호 | 의미 |
|---|---|---|
| 커밋 단계 소요 | 10분을 넘김 | 개발자가 결과를 기다리지 않고 다음 일로 넘어감 → 실패를 늦게 앎 |
| main 빨간 시간 | 몇 시간~며칠 | 새 실패가 옛 실패에 묻힘 |
| 재실행으로 초록이 된 비율 | 높음 | 불안정 테스트 → [testing/09](../../testing/09-flaky-tests/2-summary.md) |
| 수동 승인·수동 단계 수 | 늘어남 | 배포가 사람 기억에 의존 |
| 배포 빈도·변경 리드 타임·변경 실패율·복구 시간 | — | [09 DORA 지표](../09-dora-metrics/2-summary.md) |

## 장애 시나리오와 대처

### 1. 빨간 main 방치 → 모두 막힘 (⚠)

- 현상: main이 며칠째 빨갛다. 새 PR도 기준선이 빨가니 자기 변경이 무엇을 깨뜨렸는지 모른다.
- 보이는 형태: 대시보드에 "failing since 3 days"류 표시. PR 리뷰에서 "그 테스트는 원래 깨져 있어요". 실패 테스트 목록이 계속 길어진다.
- 원인: 실패를 소유한 사람이 없다. 불안정 테스트가 섞여 실패를 무시하는 습관이 생겼다.
- 대처
  - 깨뜨린 커밋을 먼저 되돌린다(Fowler·SWE@G). 고치기는 그 다음.
  - 불안정 테스트는 격리 목록으로 옮기고 버그로 추적한다(SWE@G 23장: hotlist, 일시 비활성화 + 추적). 지운 채 잊으면 안 된다.
  - 빨간 시간 자체를 지표로 본다.

### 2. 각자 초록, 합치면 빨강 (의미 충돌·mid-air collision)

- 현상: PR A·B 모두 초록. 둘 다 병합한 뒤 main 빌드가 실패한다.
- 보이는 형태: 위 실험의 `cannot find symbol`. 동적 언어나 의미 변경이면 컴파일은 되고 테스트·운영에서 터진다.
- 원인: CI가 병합 결과가 아니라 브랜치를 검사했다.
- 대처: 병합 결과 검사, 병합 큐, 짧은 브랜치([04 브랜치 전략](../04-branching-strategies/2-summary.md)).

### 3. 배포 수동 단계 → 절차 누락 (⚠, Knight Capital)

- 현상: 일부 서버만 옛 버전이다. 같은 요청이 서버에 따라 다르게 처리된다.
- 보이는 형태: 인스턴스별 버전·해시가 섞임. 특정 호스트에서만 오류·이상 주문.
- 원인: 대상 목록·복사·확인을 사람이 한다. 확인 절차가 없다.
- 대처: 인벤토리 기반 자동 배포, 배포 후 버전 일치 검증, 스모크 테스트. 플래그 재사용 금지는 [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md).
- 사실 메모: 손실 규모는 출처마다 표현이 다르다. SEC 명령서 기준으로는 약 45분 동안 쌓인 포지션에서 4억 6천만 달러 넘는 손실이다("lost over $460 million" ¶1, "realized a $460 million loss" ¶17 — 45분은 주문이 나간 시간이고, 손실은 그 포지션에서 결국 실현된 액수다). 회사 보도자료(2012-08-02)는 세전 실현 손실 약 4.4억 달러다. 명령서 원문(Internet Archive 사본) 대조는 [20](../20-practice-incidents/2-summary.md)에 있다.

### 4. 환경마다 다시 빌드 → 테스트한 것과 다른 것이 운영에

- 현상: 스테이징에서는 되는데 운영에서 깨진다.
- 보이는 형태: 스테이징과 운영 산출물의 해시가 다르다. 의존성 버전이 다르다.
- 원인: 배포 단계마다 소스에서 다시 빌드한다. 그 사이 의존성(범위 버전·`latest` 태그)이 바뀐다.
- 대처: 한 번 빌드해 저장소(아티팩트·이미지 레지스트리)에 올리고, 해시로 지정해 배포한다 → [07](../07-build-systems-and-reproducibility/2-summary.md)·[08](../08-container-image-optimization/2-summary.md).

### 5. 느린 파이프라인 → 큰 배치 → 실패가 커짐

- 현상: 커밋 단계가 40분이다. 개발자는 변경을 모아서 올린다.
- 보이는 형태: PR 크기 증가, 한 실행에 여러 변경, 실패 원인 찾기에 시간.
- 원인: 느린 테스트를 커밋 단계에 다 넣었다. 임계 경로를 안 봤다.
- 대처: 임계 경로 위 작업부터 줄인다(병렬화·테스트 분할·빌드 캐시 → [07](../07-build-systems-and-reproducibility/2-summary.md)). 느린 테스트는 이후 단계로 옮긴다.

## 핵심 문장

- CI는 "자주 통합하고, 통합마다 자동 빌드·테스트로 검증"하는 실천이다. 서버 도구가 아니다.
- 지속적 전달은 "언제든 운영에 낼 수 있음", 지속적 배포는 "모든 변경이 자동으로 운영에 들어감"이다.
- 파이프라인은 작업 DAG다. 위상정렬로 순서를 정하고, 총 시간은 임계 경로가 정한다.
- 브랜치별 초록은 병합 결과의 초록을 보장하지 않는다. 병합 결과를 검사해야 의미 충돌을 잡는다.
- 빨간 main은 되돌려서 먼저 초록으로 만든다. 실패를 쌓아 두면 새 실패가 묻힌다.
- 배포의 수동 단계는 빠뜨려도 아무도 모른다. 대상 목록은 코드에서 읽고, 배포 뒤 일치를 자동 검증한다.

## 관련 주제·근거

- 선행
  - [04-branching-strategies](../04-branching-strategies/2-summary.md) — 짧은 브랜치, trunk-based
  - [testing/01-why-test-and-pyramid](../../testing/01-why-test-and-pyramid/2-summary.md) — 어떤 테스트를 어느 단계에
- 후속·연결
  - [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md) — 빌드 DAG·캐시·한 번 빌드한 산출물의 재현성
  - [08-container-image-optimization](../08-container-image-optimization/2-summary.md) — 파이프라인이 만드는 이미지
  - [09-dora-metrics](../09-dora-metrics/2-summary.md) — 배포 빈도·리드 타임·변경 실패율·복구 시간
  - [03-version-control-and-git-internals](../03-version-control-and-git-internals/2-summary.md) — 병합(ort)·bisect
  - [05-code-review](../05-code-review/2-summary.md) — 사람의 검사와 자동 검사의 분담
  - [testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md) — CI 불신의 주원인
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) · [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) · [reliability/04-failure-modes-catalog](../../reliability/04-failure-modes-catalog/2-summary.md)(Knight)
  - [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) — 위상정렬
- 근거
  - SWE@G 23장 "Continuous Integration"(Rachel Tannenbaum) — CI 정의 인용, presubmit vs post-submit("only fast, reliable ones"), mid-air collision, TAP 배치 분할, "Rolling a change back is often the fastest and safest route", "Nobody can commit … probably misguided" <https://abseil.io/resources/swe-book/html/ch23.html>
  - SWE@G 24장 "Continuous Delivery" — "smaller batches … faster is safer", flag guarding, release train <https://abseil.io/resources/swe-book/html/ch24.html>
  - Fowler, "Continuous Integration"(2024-01-18 개정) — 실천 11개, Semantic Conflicts, ten minute build, deployment pipeline(= build pipeline·staged build), 커밋 되돌리기 <https://martinfowler.com/articles/continuousIntegration.html>
  - Fowler, bliki "ContinuousDelivery" — 전달 vs 배포 <https://martinfowler.com/bliki/ContinuousDelivery.html>
  - GitHub Docs — Workflow syntax `jobs.<job_id>.needs`(기본 병렬, 실패·skip 전파, `always()`) <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax> · "Managing a merge queue" · GitLab Docs "Merge trains" <https://docs.gitlab.com/ci/pipelines/merge_trains/>
  - Humble–Farley 『Continuous Delivery』(2010) 5장 "Anatomy of the Deployment Pipeline" — 정의, Deployment Pipeline Practices 6개, 커밋 단계 5분·10분, 배포 바이너리 = 인수 테스트를 거친 바이너리(InformIT 발췌 <https://www.informit.com/articles/article.aspx?p=1621865>, seqNum=3·4 — 커밋 단계 5분·10분은 seqNum=4)
  - Maven Failsafe Plugin "Usage" — `integration-test`·`verify` goal 설정 필요 <https://maven.apache.org/surefire/maven-failsafe-plugin/usage.html> · GitHub Docs "GitHub-hosted runners" — 작업마다 새 VM <https://docs.github.com/en/actions/concepts/runners/github-hosted-runners>
  - SWEBOK v4.0a — Software Configuration Management KA(8장 §6 "Software Release Management and Delivery")·Software Engineering Operations KA(6장 §3.2 "Deployment/Release Engineering"). computer.org PDF 목차로 확인 <https://ieeecs-media.computer.org/media/education/swebok/swebok-v4.pdf>
  - Knight Capital — SEC Release No. 34-70694(2013-10-16): "one of Knight's technicians did not copy the new code to one of the eight SMARS computer servers. Knight did not have a second technician review this deployment … Knight had no written procedures that required such a review." — 원문 인용을 실은 Doug Seven, "Knightmare: A DevOps Cautionary Tale"(2014) <https://dougseven.com/2014/04/17/knightmare-a-devops-cautionary-tale/>로 대조. 손실 표현은 Wikipedia "Knight Capital Group"·[reliability/04](../../reliability/04-failure-modes-catalog/2-summary.md)
- 실험 목록(모두 2026-10-05, 이 노트의 수치는 아래 출력 그대로)
  - 의미 충돌: 일회용 git 저장소(git 2.43.0, author Example) + eclipse-temurin:21-jdk `javac` — 두 브랜치 GREEN, 병합(ort, 충돌 0) RED
  - 파이프라인 DAG: `PipelineDag.java`(JDK 21) — 위상정렬·임계 경로 22분 vs 합 29분(예시 소요), 실패 전파
  - 배포 누락 검증: bash + `sha256sum` 시뮬레이션 — 수동(7/8) 해시 2종 FAIL, 자동 8/8 OK
