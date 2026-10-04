# engineering-practice/06-ci-cd-pipelines — 정답

## 정답

### 1. CI가 없으면 몰리는 것

- 통합을 미루면 충돌과 깨진 빌드가 병합 날 한꺼번에 몰린다. 원인 후보가 많아 범인을 찾기 어렵다.
- CI는 도구가 아니라 실천이다. 정의: 작업을 자주 통합하고, 통합마다 자동 빌드(테스트 포함)로 검증한다(SWE@G 23장이 인용한 Fowler 정의).
- Fowler의 실천 "Everyone Pushes Commits To the Mainline Every Day" — CI 서버가 있어도 브랜치가 몇 주씩 떨어져 있으면 지속적 통합이 아니다.

### 2. 세 용어

| 용어 | 한 문장 |
|---|---|
| 지속적 통합 | 자주 통합하고 통합마다 자동 빌드·테스트로 검증한다 |
| 지속적 전달 | 언제든 운영에 릴리스할 수 있는 상태를 유지한다(Fowler) |
| 지속적 배포 | 모든 변경이 파이프라인을 지나 자동으로 운영에 들어간다(Fowler) |

- CD는 전달과 배포 두 뜻으로 쓰인다. 문서가 "운영 배포까지 자동인가, 배포할 수 있는 상태까지인가"를 확인한다.

### 3. 파이프라인 DAG

```text
                 ┌─> compile(3) ─┬─> unit-test(5) ─────────┐
  checkout(1) ───┤               └─> integration-test(8) ──┼─> package(2) ─> deploy-staging(3) ─> smoke(2) ─> deploy-prod(3)
                 └─> lint(2) ──────────────────────────────┘
```

- 차례로 돌린 합: 1+3+2+5+8+2+3+2+3 = **29분**.
- 병렬 총 시간 = 임계 경로 checkout→compile→integration-test→package→deploy-staging→smoke→deploy-prod = 1+3+8+2+3+2+3 = **22분**. 실험 출력 `sequential sum = 29 min, DAG(parallel) = 22 min`과 같다.
- 줄일 곳: 임계 경로 위 작업, 특히 integration-test(8분). lint·unit-test를 줄여도 총 시간은 그대로다(임계 경로 밖).

### 4. unit-test 실패 시

- integration-test: 형제 작업이라 계속 돈다. 실험에서 `start= 4 end=12 ok`.
- package·deploy-staging·smoke-test·deploy-prod: 선행이 실패했으니 건너뛴다(`skipped`).
- GitHub Actions 문서: `needs`로 의존한 작업은 선행 작업이 실패하거나 건너뛰어지면 함께 건너뛴다. `always()` 같은 조건식을 쓰면 예외. 실패 전파는 의존 사슬 전체에 적용된다.

### 5. 각자 초록, 합치면 빨강

- A 단독 CI: `CI: GREEN`. B 단독 CI: `CI: GREEN`.
- `git merge`: `Merge made by the 'ort' strategy.` 충돌 파일 0개 — 서로 다른 파일을 고쳤다.
- 병합된 main: `src/Invoice.java:2: error: cannot find symbol … method total(int,int)` → `CI: RED`.
- 이름: Fowler "semantic conflict", SWE@G 23장 "mid-air collision".
- 막는 법: CI가 "대상 브랜치 + PR" 병합 결과를 검사, 병합 큐(GitHub merge queue·GitLab merge trains), 짧은 브랜치. 컴파일이 못 잡는 의미 변경은 자기 테스트 코드가 잡아야 한다(Fowler).

### 6. 커밋 단계에 넣을 것

- Humble–Farley 5장: 커밋 단계는 5분 미만이 이상적, 10분은 넘기지 않는다. 컴파일·단위 테스트·정적 분석처럼 빠른 것.
- SWE@G 23장(Google 관례): presubmit에는 "only fast, reliable ones". 크고 느린 테스트는 post-submit에서 비동기로, 놓친 것은 롤백으로 감수한다.
- SWE@G 23장: 자기 변경과 상관없는 불안정(flaky) 실패로 presubmit에서 막히는 것은 엔지니어에게 비싸다("it's expensive for engineers to be blocked on presubmit by failures arising from instability or flakiness that has nothing to do with their code change"). 그래서 불안정 테스트는 presubmit에서 잠시 빼고 조사한다.

### 7. 사흘째 빨간 main

- 위험: 기준선이 빨가니 새로 깨진 것이 옛 실패에 묻힌다. 실패를 무시하는 습관이 생기고 CI 신호를 아무도 믿지 않는다.
- 먼저: 깨뜨린 커밋을 되돌려 초록으로(Fowler "revert the latest commit", SWE@G "Rolling a change back is often the fastest and safest route"). 불안정 테스트는 격리하고 버그로 추적한다(hotlist).
- SWE@G 23장은 "Nobody can commit if our latest CI results aren't green" 정책을 "probably misguided"라고 본다. 실패는 조사해야 하지만, 원인이 분명하고 운영에 영향이 없으면 커밋을 막을 이유는 없다는 것이다. 핵심은 조사하지 않은 실패를 쌓지 않는 것이다.

### 8. 일부 인스턴스만 이상 — Knight Capital

- 겹친 결함(SEC 명령 34-70694 요약): 기술자가 새 코드를 8대 중 1대에 복사하지 않았다. 두 번째 기술자가 확인하는 절차가 없었다. 새 코드가 옛 Power Peg 기능의 플래그를 재사용해, 그 1대에서 옛 코드가 깨어났다.
- 파이프라인에 넣을 것: 인벤토리(코드)에서 대상 목록 읽기, 배포 후 모든 대상의 산출물 해시·버전 일치 검증, 스모크 테스트.
- 실험(시뮬레이션): 수동 7/8 배포 뒤 검증하면 해시가 `1 29bbb1d48f8c` / `7 bd899fbbbdb9` 두 종류 → `VERIFY: FAIL (drift)`, `s8 v1 old-flag=PowerPeg`. 자동 배포 뒤 `8 bd899fbbbdb9` → OK.

### 9. 환경마다 다시 빌드

- 문제: 스테이징에서 테스트한 바이너리와 운영 바이너리가 다를 수 있다. 그 사이 범위 버전 의존성·`latest` 태그·빌드 환경이 바뀌면 다른 산출물이 나온다.
- 어긋나는 실천: Humble–Farley "Only Build Your Binaries Once"(와 "Deploy the Same Way to Every Environment").
- 연결: 한 번 만든 산출물을 해시로 지정해 승격한다. 그 산출물이 같은 입력에서 같게 나오는지는 07(재현 가능 빌드), 컨테이너 이미지로 담는 법은 08.
