# engineering-practice/04-branching-strategies — 브랜치 전략: git-flow vs trunk-based·피처 플래그 — 정리 (힌트)

## 해결하는 문제

브랜치 전략은 "갈라진 작업을 **언제·얼마나 자주** 합치나"를 정하는 팀 규칙이다.

```text
  통합을 미룰 때
  dev A ──●──●──●──●──●──●──●──●──●──●──┐
  dev B ──●──●──●──●──●──●──●──●──●──●──┤  20일 뒤 한꺼번에 병합
  dev C ──●──●──●──●──●──●──●──●──●──●──┘  → 수백 줄 충돌 + 서로 모르는 변경끼리 의미 충돌
  main  ────────────────────────────────●

  매일 통합할 때
  main ──●─●─●──●─●─●──●─●─●──●─●─●──   하루치 변경끼리만 부딪힌다 → 작은 충돌, 바로 해결
```

- 브랜치는 git에서 싸다([03](../03-version-control-and-git-internals/2-summary.md) — 포인터 파일 하나). 비싼 것은 **브랜치가 갈라져 있는 시간**이다.
- 갈라져 있는 동안 쌓이는 것
  - 텍스트 충돌: 같은 줄을 서로 다르게 고침.
  - 의미 충돌: 텍스트는 안 겹치는데 합치면 깨짐(이름 바꾸기 vs 옛 이름 호출).
  - 통합 공포: 병합이 아프니 더 미루고, 더 미루니 더 아프다(Fowler, "Patterns for Managing Source Code Branches", 2020).

쉬운 예: 여럿이 같은 문서를 각자 사본으로 한 달 고친 뒤 합치는 것과, 매일 저녁 한 번씩 합치는 것.
- 한 달 뒤에는 "누가 이 문단을 왜 지웠나"를 아무도 기억 못 한다.
- 매일 합치면 충돌이 생겨도 어제 일이라 작성자가 바로 안다.

똑같은 구조다.\
브랜치 전략은 결국 **통합 주기**와 **미완성 기능을 어디에 숨기나**(브랜치 vs 런타임 플래그)의 선택이다.

실무 예:
- 분기마다 `release/x.y` 브랜치를 따서 몇 주간 안정화하는 설치형 제품.
- 하루에 수십 번 `main`에서 배포하는 웹 서비스. 미완성 기능은 피처 플래그로 꺼 둔다.
- 석 달 산 기능 브랜치를 병합하는 날 팀 전체가 하루를 충돌 해결에 쓴다(장애 1).

## 동작·원리

### 1. 두 계열 — 출처별 정의

```text
  git-flow (Driessen, 2010-01-05)
  master  ──●───────────────────●──────────●──── 태그 v1.0, v1.1
             \                 /          /
  release     \          ●──●─●   hotfix ●
               \        /      \        / \
  develop  ──●──●──●──●──●──●───●──●──●───●──
              \     /   \       /
  feature      ●──●      ●──●──●

  trunk-based (trunkbaseddevelopment.com)
  trunk ──●──●──●──●──●──●──●──●──●──●──●──
           \_/   \_/    \__/              짧은 기능 브랜치(리뷰·CI용, 이틀 이내)
                       └─ release/1.2 ──●(체리픽)  필요할 때만, 릴리스 끝나면 삭제
```

- *git-flow*: `master`·`develop` 두 장수 브랜치에 feature·release·hotfix 보조 브랜치를 더한 모델(Vincent Driessen, "A successful Git branching model", 2010-01-05).
  - 2020-03-05에 저자가 덧붙인 "Note of reflection": 지속적으로 전달하는 웹 앱은 처음 글을 쓸 때 염두에 둔 종류가 아니었다. 그런 팀에는 GitHub flow 같은 훨씬 단순한 흐름을 권한다. **명시적으로 버전을 매기는 소프트웨어, 또는 여러 버전을 동시에 지원해야 하는 소프트웨어**라면 git-flow가 여전히 맞을 수 있다고 쓴다.
    - 흔한 오해: "git-flow가 표준 git 사용법이다." 저자 스스로 적용 범위를 버전 소프트웨어로 한정했다.
- *trunk-based development*(정의 출처마다 다르다)
  - trunkbaseddevelopment.com: 개발자들이 "trunk"라는 단일 브랜치에서 협업하고, 문서화된 기법으로 **다른 장수 개발 브랜치를 만들라는 압력에 저항하는** 모델. 짧은 기능 브랜치는 허용하되 "a couple of days"만, 이틀을 넘으면 장수 브랜치가 될 위험이 있다고 한다. 한 사람(페어면 둘)만 쓴다.
  - DORA(dora.dev capability, 2016·2017 State of DevOps 보고서 근거): 활성 브랜치 **3개 이하**, 트렁크로 **최소 하루 한 번** 병합, 코드 동결·통합 단계 없음.
  - SWE@G 16장: 개발 브랜치 대신 "trunk-based development, rely heavily on testing and CI, keep the build green, and disable incomplete/untested features at runtime". DORA 연구를 인용해 trunk-based와 고성과 조직 사이에 "predictive relationship"이 있다고 쓴다.
  - 세 출처 모두 "짧게 자주 합친다"는 방향은 같다. 수치 기준(이틀 / 하루 1회·3개 이하 / 수치 없음)은 다르다.
- *GitHub flow*: `main` 하나 + 짧은 기능 브랜치 + PR 리뷰 후 병합·배포. trunk-based의 한 형태로 볼 수 있다(해석).

### 2. 미완성 기능을 숨기는 두 자리

```text
  브랜치에 숨김                          런타임에 숨김
  feature/new-pay ──●──●──●──●──(병합)    main ──●──●──●──●──   코드는 매일 main에 들어간다
  main            ─────────────●          if (flags.on("new-pay")) newPay() else oldPay()
  → 통합이 병합일까지 미뤄짐              → 통합은 매일, "켜기"는 따로 결정
```

- *피처 플래그(feature toggle)*: 런타임에 코드 경로를 고르는 스위치. 배포 없이 값을 바꿀 수 있는지는 설정 방식에 달렸다(Hodgson: Release 토글은 새 릴리스로 설정을 바꿔도 괜찮은 경우가 많다). Pete Hodgson("Feature Toggles", martinfowler.com, 2017-10-09)의 네 분류:

| 분류 | 수명 | 동적성 | 예 |
|---|---|---|---|
| Release | 짧음(주 단위) | 정적 | 미완성 기능 숨기기 |
| Experiment | 시간~주 | 요청마다 | A/B 테스트 |
| Ops | 짧음~무기한 | 동적 | 부하 시 기능 끄기(킬 스위치) |
| Permissioning | 김(년 단위) | 요청마다 | 유료 사용자 전용 |

- 플래그는 공짜가 아니다. Hodgson: "Savvy teams view their Feature Toggles as inventory which comes with a carrying cost". 만들 때 제거 작업을 같이 만들고, 만료일·개수 상한을 두라고 권한다. 수명 관리는 [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md).
- *Branch by Abstraction*: 오래 걸리는 교체를 브랜치 없이 트렁크에서 하는 기법. trunkbaseddevelopment.com "Ideal steps"의 다섯 단계: ① 교체 대상 주위에 추상(인터페이스)을 도입해 커밋(여러 커밋 가능, 빌드는 깨지 않음) ② 추상 뒤에 새 구현을 작성하되 트렁크 안에서 꺼 둠 ③ 스위치를 켬 ④ 옛 구현 제거 ⑤ 추상 제거.

### 3. 릴리스 브랜치 — 고치는 방향

```text
  trunk  ──●──●──[fix+test]──●──●──     ① 트렁크에서 재현·수정·CI 통과
                     │ cherry-pick
  release/1.2 ──●────●                  ② 릴리스 브랜치로 체리픽
  (역방향: 릴리스에서 고치고 나중에 트렁크로 옮기기 → 잊으면 다음 릴리스에서 회귀)
```

- trunkbaseddevelopment.com "Branch for release": 버그는 트렁크에서 테스트와 함께 고친 뒤 릴리스 브랜치로 체리픽한다. 릴리스 브랜치에서 고치고 나중에 트렁크로 옮기면, 잊었을 때 몇 주 뒤 운영 회귀가 된다. 릴리스 브랜치는 트렁크로 병합하지 않고 수명이 끝나면 지운다.
- SWE@G 16장: 릴리스 브랜치는 대체로 무해(benign)하다. 문제는 개발 브랜치다. DORA가 본 최고 성과 조직에서는 릴리스 브랜치조차 거의 없다고 쓴다.

### 실험: 같은 변경 흐름을 통합 주기만 바꿔 재생한다 (시뮬레이션)

실측 데이터가 아니라 **스크립트로 만든 커밋**이다. 조건을 고정하고 통합 주기만 바꿨다.

- 조건: 개발자 4명, 20일, 하루에 1인당 편집 3개(파일 5개 × 60줄 중 무작위 위치의 1~3줄을 덮어씀). 같은 시드면 편집 흐름이 같다.
- 통합 주기: 1일(매일 병합) / 5일 / 20일(끝에 한 번). 통합 때 개발자 브랜치를 순서대로 `main`에 `--no-ff` 병합하고, 충돌 덩어리(`<<<<<<<`) 수와 덩어리 안 줄 수를 센다. 집계 후 시뮬레이션을 이어 가려고 `-X theirs`로 다시 병합한다(실제 해결이 아니다).

```javascript
// branchsim.js 핵심 (Node 18, git 2.43)
const plan = [...Array(DAYS)].map(() => [...Array(DEVS)].map(() =>
  [...Array(EDITS)].map(() => ({ file: Math.floor(r() * FILES), line: Math.floor(r() * (LINES - 2)), len: 1 + Math.floor(r() * 3) }))));
for (let day = 0; day < DAYS; day++) {
  for (let d = 0; d < DEVS; d++) { git('checkout', '-q', `dev${d}`); apply(d, day); }   // 각자 자기 브랜치에 커밋
  if ((day + 1) % every === 0 || day === DAYS - 1) integrate();                          // every일마다 main에 병합
}
// integrate(): merge 실패 시 충돌 파일의 <<<<<<< 수와 덩어리 줄 수를 센 뒤 abort → -X theirs로 재병합,
//              끝나면 모든 dev 브랜치를 main으로 맞춘다
```

(시뮬레이션, git 2.43.0 / Node 18.19.1, 시드 1~5, 2026-10-05)

```text
{"seed":1,"every":1,"merges":80,"conflictedMerges":23,"conflictHunks":24,"conflictLines":151}
{"seed":1,"every":5,"merges":16,"conflictedMerges":12,"conflictHunks":61,"conflictLines":474}
{"seed":1,"every":20,"merges":4,"conflictedMerges":3,"conflictHunks":50,"conflictLines":802}
{"seed":2,"every":1,"merges":80,"conflictedMerges":14,"conflictHunks":15,"conflictLines":94}
{"seed":2,"every":5,"merges":16,"conflictedMerges":12,"conflictHunks":60,"conflictLines":529}
{"seed":2,"every":20,"merges":4,"conflictedMerges":3,"conflictHunks":49,"conflictLines":854}
...(시드 3~5 생략, 아래 표에 범위)
```

| 통합 주기 | 병합 수 | 충돌 난 병합 | 충돌 덩어리 | 충돌 줄 합계 | 충돌 난 병합 1회당 줄 |
|---|---|---|---|---|---|
| 1일 | 80 | 11~23 | 13~24 | 94~151 | 6.6~9.8 |
| 5일 | 16 | 11~12 | 48~61 | 453~529 | 39.1~44.1 |
| 20일 | 4 | 3 | 43~51 | 802~864 | 267.3~288.0 |

- 관찰
  - 충돌 줄 합계는 20일 주기가 1일 주기의 약 5.3~9.1배다(시드별 비율: 802/151 = 5.3 ~ 854/94 = 9.1).
  - 1일 주기는 충돌이 **자주** 나지만 한 번에 7~10줄 안팎이다. 하루 전 자기 작업이라 작성자가 바로 판단할 수 있다.
  - 20일 주기는 마지막 날 한 번의 통합(병합 4회 중 충돌 3회)에서 충돌 난 병합당 평균 267~288줄을 풀어야 한다. 가장 오래된 편집은 20일 전 것이다.
  - 덩어리 수는 5일 주기가 20일보다 많거나 같았다(시드 3은 둘 다 48). 덩어리 수만 보면 "오래 갈라져도 충돌이 적다"고 오해한다. 원인은 오래 갈라질수록 인접한 충돌이 **큰 덩어리 하나로 합쳐지기** 때문으로 보인다(해석 — 덩어리 크기 분포는 따로 세지 않았다).
- 한계(해석): 편집은 줄 덮어쓰기만, 위치는 균등 무작위(실제 코드는 핫스팟에 몰린다), 의미 충돌은 세지 않았다. 숫자 자체보다 **같은 흐름에서 주기만 바꿨을 때의 방향**을 보는 실험이다.

### 실험: 충돌 없는 병합이 빌드를 깬다 (의미 충돌)

```text
  base:    Pricing.total()  ← Checkout이 호출
  rename:  total → totalWithShipping (Pricing·Checkout 둘 다 고침)
  refund:  새 파일 Refund.java 에서 Pricing.total() 호출
```

(실험, git 2.43.0 + eclipse-temurin:21-jdk OpenJDK 21.0.12, 2026-10-05)

```text
Merge made by the 'ort' strategy.
 Refund.java | 3 +++
 1 file changed, 3 insertions(+)
== 충돌 표식 수: 0
Refund.java:2: error: cannot find symbol
    static long refund(long amount) { return -Pricing.total(amount); }
                                                     ^
  symbol:   method total(long)
  location: class Pricing
1 error
javac exit=1
```

- 두 브랜치는 서로 다른 파일을 건드렸으니 git은 깨끗이 병합한다. 깨짐은 **컴파일·테스트가 돌아야** 보인다.
- Fowler는 이를 semantic conflict라 부른다. 브랜치가 오래 살수록 "상대가 바꾼 것을 모른 채 쓴 코드"가 늘어난다.
- 그래서 trunk-based의 전제는 "자주 병합"만이 아니라 **병합마다 CI가 빌드·테스트**하는 것이다(SWE@G 16장 "rely heavily on testing and CI, keep the build green").

## 쓰이는 자료구조·알고리즘

- **커밋 DAG와 merge-base(LCA)**: 브랜치가 오래 갈라질수록 merge-base가 과거로 멀어지고, base 이후 양쪽 변경이 커져 겹칠 확률이 오른다. git 내부는 [03](../03-version-control-and-git-internals/2-summary.md).
- **충돌 확률 직관(생일 문제와 같은 꼴, 해석)**: 변경 k개가 N개 위치에 무작위로 흩어지면 겹치는 쌍의 수는 대략 k²에 비례해 늘어난다. 통합 주기가 길면 한 병합에 들어가는 k가 커진다. 시뮬레이션에서 충돌 줄 합계가 주기에 따라 늘어난 방향과 맞는다(정확한 비례식은 이 모델에서 검증하지 않았다).
- **피처 플래그 = 설정 조회 + 분기**: 플래그 이름 → 값의 해시맵, 실험용이면 사용자 ID 해시로 버킷 배정. 평가 일관성은 [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md).
- **Branch by Abstraction = 인터페이스(간접 계층)**: 호출부를 추상에 묶어 두 구현을 동시에 둔다. [software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md)의 작은 단계 이동과 같은 생각이다.

## 적용 — 풀어나가는 법

### 1. 제품 성격으로 고른다

| 질문 | 예 → 쪽 |
|---|---|
| 운영 중인 버전이 하나인가(웹 서비스) | 예 → trunk-based / GitHub flow |
| 고객이 여러 버전을 오래 쓰나(설치형·SDK) | 예 → 릴리스 브랜치 필요(git-flow류 또는 trunk + release branch) |
| 병합마다 빌드·테스트가 자동으로 도나 | 아니오 → 먼저 CI부터([06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md)) |
| 미완성 기능을 꺼 둘 수단이 있나 | 아니오 → 플래그·Branch by Abstraction부터 |

- git-flow 저자의 2020 노트와 SWE@G 16장 모두 지속적으로 배포하는 서비스에는 단순한 흐름을 권한다. 버전 여러 개를 지원하는 제품은 릴리스 브랜치가 정당하다.

### 2. trunk-based를 굴리는 일상

```bash
git switch -c feat/limit-check            # 짧은 브랜치 (이틀 이내 목표)
# ... 작은 커밋 몇 개
git fetch origin && git rebase origin/main   # 자기 브랜치만 rebase (공유 브랜치는 X)
git push --force-with-lease --force-if-includes origin feat/limit-check
# PR → 리뷰 → CI 통과 → main 병합 → 브랜치 삭제
```

- 하루 이상 걸리는 기능은 쪼개 매일 병합하고, 미완성 부분은 플래그로 끈다.

```java
// Release 플래그: 미완성 기능을 main에 넣되 기본은 꺼 둔다
public interface Flags { boolean isOn(String name); }

public final class PaymentService {
    private final Flags flags;
    private final LegacyPay legacy;
    private final NewPay next;          // 아직 미완성 — main에는 있지만 꺼져 있다

    public PaymentService(Flags flags, LegacyPay legacy, NewPay next) {
        this.flags = flags; this.legacy = legacy; this.next = next;
    }

    public Receipt pay(Order o) {
        // TODO(flag-expiry 2026-11-30): new-pay 전면 전환 후 이 분기와 LegacyPay 제거
        return flags.isOn("new-pay") ? next.pay(o) : legacy.pay(o);
    }
}
```

- 플래그에 만료일과 제거 작업을 같이 단다(Hodgson의 권고). 끝난 플래그를 지우지 않으면 죽은 분기가 쌓인다.

### 3. 지표로 확인한다

```bash
# 원격 추적 참조 목록과 각 끝 커밋의 나이 (활성 여부는 이 목록에 기준을 정해 따로 센다. DORA: 활성 브랜치 3개 이하 권장)
git for-each-ref --sort=committerdate refs/remotes/origin \
  --format='%(committerdate:relative)%09%(refname:short)'
# 브랜치가 main에서 얼마나 갈라졌나 (main에만 있는 커밋 / 브랜치에만 있는 커밋)
git rev-list --left-right --count origin/main...origin/feat/x
```

- DORA capability 페이지의 측정 항목: 활성 브랜치 수, 코드 동결 빈도·기간, 하루 병합 횟수, 리뷰 승인 시간.

## 장애 시나리오와 대처

### 1. 장수 브랜치 → 머지 지옥 (⚠ 커리큘럼)

- **현상**: 석 달 된 기능 브랜치 병합에 며칠이 걸리고, 그동안 `main`이 막힌다.
- **보이는 형태**: 수십 파일 `CONFLICT (content)`, `git rev-list --left-right --count`가 양쪽 수백. 시뮬레이션에서는 20일 주기의 충돌 난 병합 1회당 충돌 줄 267~288.
- **원인**: merge-base 이후 양쪽 변경이 커졌다. 충돌을 푸는 사람이 상대 변경의 의도를 모른다.
- **대처**
  - 당장: 큰 병합을 한 번에 하지 말고, `main`을 기능 브랜치로 먼저 여러 번 나눠 병합하며 작성자들과 함께 푼다. 해결 후 `git show --remerge-diff`로 해결 내용을 리뷰한다([03](../03-version-control-and-git-internals/2-summary.md)).
  - 구조: 기능을 쪼개 매일 병합하고, 미완성은 플래그·Branch by Abstraction으로 숨긴다.

### 2. 병합은 깨끗한데 통합 버그 (⚠ 커리큘럼)

- **현상**: 각 브랜치에서는 테스트가 다 통과했는데 병합 후 `main`이 빌드·테스트 실패, 또는 운영에서 동작 오류.
- **보이는 형태**: `Merge made by the 'ort' strategy.` 직후 `cannot find symbol`(실험), 또는 컴파일은 되지만 기본값·계약이 바뀌어 테스트 실패.
- **원인**: 의미 충돌. 텍스트 병합은 의미를 보지 않는다.
- **대처**: 병합 결과(병합 커밋 또는 병합 큐의 예상 결과)에 대해 CI를 돌린다. 이름 바꾸기 같은 넓은 변경은 작게, 빨리 병합해 다른 브랜치가 일찍 따라가게 한다.

### 3. 릴리스 브랜치에서만 고친 버그가 다음 릴리스에서 재발

- **현상**: 1.2에서 고친 버그가 1.3에서 다시 나온다.
- **원인**: 수정이 릴리스 브랜치에만 들어가고 트렁크로 옮겨지지 않았다.
- **대처**: 트렁크에서 테스트와 함께 고친 뒤 릴리스 브랜치로 체리픽(trunkbaseddevelopment.com). `git cherry -v main release/1.2`로 릴리스 브랜치에만 있는 수정(main에서 같은 패치를 못 찾은 커밋이 `+` — 다른 코드로 고쳤는지는 판정하지 않는다)을 정기 점검한다(실험, git 2.43: 인자 순서를 바꾼 `cherry -v release/1.2 main`은 main 쪽 커밋만 보여 줬다).

### 4. 플래그가 부채가 된다

- **현상**: 코드에 `if (flags.isOn(...))` 분기가 수십 개, 어떤 조합이 운영에서 쓰이는지 아무도 모른다. 오래된 플래그 이름을 새 기능에 재사용했다가 옛 코드가 깨어난다.
- **원인**: Release 플래그를 전환 후 지우지 않았다.
- **대처**: 만료일·담당자·개수 상한, 만료 지나면 실패하는 테스트(Hodgson의 "time bomb"). 플래그 이름 재사용 금지. 실사건(옛 플래그 재사용 + 수동 배포 누락)은 [20-practice-incidents](../20-practice-incidents/2-summary.md)와 [reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md).

### 5. trunk-based인데 CI·리뷰가 따라오지 못한다

- **현상**: 모두 매일 `main`에 넣는데 `main`이 자주 빨갛다. 또는 PR이 리뷰를 기다리며 며칠씩 쌓여 사실상 장수 브랜치가 된다.
- **원인**: DORA가 꼽은 함정 — 무거운 리뷰(여러 승인 필수), 비동기 리뷰 대기, 커밋 전 자동 테스트 미실행.
- **대처**: 커밋 전 테스트, 작은 PR과 빠른 리뷰([05](../05-code-review/2-summary.md)), 빨간 `main`은 최우선으로 되돌리기.

## 핵심 문장

- 브랜치 전략의 본질은 "갈라진 작업을 얼마나 자주 합치나"와 "미완성 기능을 브랜치에 숨기나 런타임에 숨기나"의 선택이다.
- git-flow는 여러 버전을 지원하는 소프트웨어용으로 설계됐고, 저자도 지속 배포 웹 앱에는 더 단순한 흐름을 권한다.
- trunk-based의 수치 기준은 출처마다 다르다(이틀 이내 기능 브랜치 / 하루 1회 병합·활성 브랜치 3개 이하) — 방향은 "짧게, 자주"로 같다.
- 같은 변경 흐름을 재생한 시뮬레이션에서 20일 주기 통합은 1일 주기보다 충돌 줄이 약 5.3~9.1배였고, 그 전부가 마지막 날 한 번의 통합에 몰렸다.
- 충돌 없는 병합도 의미 충돌로 빌드를 깰 수 있으므로, 자주 병합하는 것은 병합마다 CI가 도는 것과 짝이다.
- 피처 플래그는 통합과 출시를 떼어 주지만, 제거하지 않으면 그 자체가 부채가 된다.

## 관련 주제·근거

- 선행
  - [03-version-control-and-git-internals](../03-version-control-and-git-internals/2-summary.md) — 커밋 DAG, merge-base, 3-way 병합
- 후속·연결
  - [05-code-review](../05-code-review/2-summary.md) — 작은 PR·빠른 리뷰가 짧은 브랜치의 조건
  - [09-dora-metrics](../09-dora-metrics/2-summary.md) — 배포 빈도·리드 타임으로 통합 주기의 효과를 본다
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [20-practice-incidents](../20-practice-incidents/2-summary.md)
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 플래그 유형·평가 일관성·제거
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 카나리·롤백과 플래그
  - [software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md) · [software-design/14-tidy-first](../../software-design/14-tidy-first/2-summary.md) — 작은 단계, 구조 변경 분리
- 문서·글
  - Vincent Driessen, "A successful Git branching model"(2010-01-05, 2020-03-05 Note of reflection) <https://nvie.com/posts/a-successful-git-branching-model/>
  - trunkbaseddevelopment.com — 정의, Short-Lived Feature Branches("a couple of days"), Branch for Release(트렁크에서 고치고 체리픽, 릴리스 브랜치는 병합하지 않음), Branch by Abstraction(5단계) <https://trunkbaseddevelopment.com/>
  - DORA capability "Trunk-based development" — 활성 브랜치 3개 이하, 하루 1회 이상 병합, 코드 동결 없음, 함정(무거운 리뷰·비동기 리뷰·테스트 미실행), 2016·2017 State of DevOps 보고서 <https://dora.dev/capabilities/trunk-based-development/>
  - SWE@G 16장 "Version Control and Branch Management"(Titus Winters) — 개발 브랜치 비판, "predictive relationship", 릴리스 브랜치는 benign <https://abseil.io/resources/swe-book/html/ch16.html>
  - Martin Fowler, "Patterns for Managing Source Code Branches"(2020-05-28) — 통합 빈도, semantic conflict, integration fear <https://martinfowler.com/articles/branching-patterns.html>
  - Pete Hodgson, "Feature Toggles (aka Feature Flags)"(2017-10-09) — 네 분류, carrying cost <https://martinfowler.com/articles/feature-toggles.html>
- 실험 목록
  - 통합 주기 시뮬레이션: `branchsim.js`(Node 18.19.1 → git 2.43.0 일회용 저장소), 개발자 4·20일·편집 3/일·파일 5×60줄, 주기 1/5/20일 × 시드 1~5. 스크립트로 만든 커밋이며 실측이 아니다.
  - 의미 충돌: rename 브랜치 + 옛 이름 호출 브랜치를 병합(충돌 0) → eclipse-temurin:21-jdk `javac` 실패(`--network none`)
  - `git cherry` 인자 순서: 릴리스에만 커밋 1개를 둔 일회용 저장소에서 `cherry -v main release/1.2`는 그 커밋을 `+`로, `cherry -v release/1.2 main`은 main 쪽 커밋만 보여 줬다(git 2.43.0)
