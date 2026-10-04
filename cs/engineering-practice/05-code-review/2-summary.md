# engineering-practice/05-code-review — 코드 리뷰: 목적·기준·크기 — 정리 (힌트)

## 해결하는 문제

혼자 쓴 코드는 혼자만 안다. 그리고 작성자는 자기 실수를 잘 못 본다.

```text
  리뷰 없이
  작성자 ──커밋──> main ──> 운영
   (자기 가정을 의심하지 않음, 이 코드를 아는 사람 = 1명)

  리뷰 있을 때
  작성자 ──PR──> [자동 검사] ──> 리뷰어 ──댓글──> 작성자 수정 ──> 승인(LGTM) ──> main
                  빌드·테스트·린트   이해·설계·정확성     │
                                                         └ 이제 이 코드를 아는 사람 ≥ 2명
```

- 리뷰는 "버그 잡기"만이 아니다. 연구와 회사 기록이 같은 방향을 말한다.
  - Bacchelli & Bird(ICSE 2013, Microsoft): 결함 찾기가 **주된 동기**이지만, 실제 리뷰는 기대보다 결함과 덜 관련됐고 지식 전달·팀 인식·대안 제시 같은 이점이 컸다. 리뷰의 핵심 요소(key aspect)는 **코드와 변경을 이해하는 것**이었고, 그 이해 요구는 당시 도구가 대부분 채워 주지 못했다(논문 초록).
  - Sadowski 외(ICSE-SEIP 2018, Google — 인터뷰 12건·설문 44명·리뷰 로그 약 900만 변경): 인터뷰에서 나온 리뷰 기대 주제는 교육, 규범 유지, 게이트키핑, 사고 예방이다. 논문 표현으로 "Defect finding is welcomed but not the only focus." (기대 주제는 인터뷰 분석, 수치는 로그 분석에서 나왔다.)
  - SWE@G 9장(Code Review, Tom Manshreck·Caitlin Sadowski): "checking for code correctness is not the primary benefit Google accrues from the process of code review."

쉬운 예: 출판 전 원고를 편집자가 읽는 것이다.
- 오탈자도 잡지만, 더 큰 가치는 "독자가 이해할 수 있나"를 작성자 아닌 사람이 확인하는 데 있다.
- 원고가 500쪽이면 편집자는 대충 넘긴다.

똑같은 구조다.\
리뷰어가 **이해할 수 있는 크기**로 나눠야 리뷰가 작동한다. 거대한 변경은 형식적 승인으로 끝나기 쉽다.

실무 예:
- 3,000줄 PR에 "LGTM" 한 줄 승인 → 그 안의 경계 조건 1줄 변경이 운영 장애로(장애 1).
- 리뷰 대기 사흘 → 작성자가 다음 작업을 쌓아 PR이 더 커짐 → 리뷰가 더 늦어짐(장애 2).

## 동작·원리

### 1. 승인은 무엇을 보증하나 — Google의 세 가지

```text
  변경 하나가 병합되려면 (SWE@G 9장)
  ┌────────────────────┬──────────────────────────────────────┐
  │ LGTM               │ 다른 엔지니어의 정확성·이해 확인      │
  │ 소유자(OWNERS) 승인 │ 이 코드 영역에 맞는 변경인가          │
  │ readability 승인    │ 언어 스타일·모범 관례에 맞나          │
  └────────────────────┴──────────────────────────────────────┘
  한 사람이 세 자격을 모두 가지면 리뷰어 1명으로 충족
```

- *LGTM*: "looks good to me". 리뷰의 최종 목표는 다른 엔지니어가 변경에 **동의**하는 것이고, 이를 LGTM으로 표시한다(SWE@G 9장).
- Sadowski 2018: 리뷰어가 2명 이상인 변경은 25% 미만이다("fewer than 25% of changes have more than one reviewer", 리뷰어 수 중앙값 1). SWE@G 9장도 대부분의 리뷰에서 한 사람이 세 역할을 다 맡는다고 쓴다.
- GitHub의 대응물(문서 기준)
  - *CODEOWNERS*: `.github/`·루트·`docs/`에 두는 파일. 경로 패턴 → 소유자. **마지막으로 일치한 패턴이 우선**한다. 보호 브랜치에서 "코드 소유자 리뷰 필수"를 켜면 소유자 **중 한 명**의 승인으로 충족된다.

### 2. 승인 기준 — "완벽"이 아니라 "전보다 낫다"

- Google eng-practices "The Standard of Code Review": 리뷰어는 CL이 **시스템 전체의 코드 건강을 분명히 개선하는 상태**면, 완벽하지 않아도 승인 쪽으로 기운다. "There is no such thing as 'perfect' code—there is only better code."
  - *CL(changelist)*: Google 용어로 리뷰 단위 변경 하나. GitHub의 PR과 대응한다.
- 꼭 고칠 것과 선택 사항을 구분한다. 선택 사항에는 `Nit:`를 붙인다.
- 무엇을 보나(eng-practices "What to look for"): Design, Functionality, Complexity, Tests, Naming, Comments, Style, Consistency, Documentation, Every Line, Context, Good Things.
  - 순서가 중요하다(해석): 설계가 틀렸으면 이름·스타일 댓글은 낭비다. 큰 그림 → 세부.
- 사람이 볼 필요 없는 것은 기계에 맡긴다. SWE@G 9장 모범 사례: "Automate Where Possible". Google에서는 테스트·린트·포맷 기능 대부분을 presubmit이 자동으로 제공하고, 리뷰어에게 보내기 전에 문제를 찾으면 전송을 막을 수 있다.

### 3. 크기 — 공개 자료의 수치

```text
  리뷰어의 주의력 (개념 그림, 실측 곡선 아님)
  결함 발견 ▲
           │ ████
           │ ████ ███
           │ ████ ███ ██
           │ ████ ███ ██ █ ▁ ▁ ▁            ← 크기·속도가 커지면 대충 넘김
           └──────────────────────────────> 리뷰 대상 줄 수 / 검토 속도
```

| 출처 | 성격 | 크기 관련 수치 |
|---|---|---|
| Google eng-practices "Small CLs" | 회사 지침 | "100 lines is usually a reasonable size for a CL, and 1000 lines is usually too large", 최종 판단은 리뷰어 |
| SWE@G 9장 | 회사 관례(책) | "Small" 변경은 대략 200줄 이내. 약 35%가 단일 파일 변경. 대부분 하루 안에 **첫 피드백**(책: 리뷰가 하루 안에 끝난다는 뜻은 아님) |
| Sadowski 외 2018 | 실측(Google 약 900만 변경) | 수정 줄 수 중앙값 24, 35% 초과가 단일 파일, 약 90%가 10개 파일 미만. 첫 피드백 대기 중앙값: 작은 변경 1시간 미만, 매우 큰 변경 약 5시간. 전체 리뷰 지연 중앙값 4시간 미만. 변경당 평균 댓글 수는 줄 수와 함께 늘어 약 1250줄에서 12.5개로 최고 |
| Cohen, "Code Review at Cisco Systems"(『Best Kept Secrets of Peer Code Review』, SmartBear, 2006) | **벤더** 사례 연구(10개월, 리뷰 2,500건, 320만 줄, 개발자 50명) | 리뷰 대상은 200줄 미만, 400줄 넘지 않게. 검토 속도 300줄/시간 미만이 최선, 500 미만도 양호. 한 번에 60분 미만, 90분 넘지 않게. 종합 권고: 한 번에 100~300줄을 30~60분 |

- 수치의 성격이 다르다. Google 두 자료는 **지침·관례**, Sadowski는 한 회사의 **측정**, Cisco 자료는 리뷰 도구 회사의 **사례 연구**다. 셋 다 "작게"를 가리키지만 절대 기준으로 쓰면 안 된다.
- SmartBear 웹 글은 "200-400 LOC over 60 to 90 minutes should yield 70-90% defect discovery"라고 적는다. Cisco 사례 연구 장(PDF 전문)에서는 70~90% 수치를 찾지 못했다 — 웹 글 수치의 근거는 확인하지 못해 `[?]`로 둔다.
- 크기가 작으면 좋은 이유(eng-practices "Small CLs"): 리뷰가 빠르고 꼼꼼해지며, 버그 가능성이 줄고, 거절돼도 버리는 작업이 적고, 병합 충돌이 줄고, 롤백이 쉽다.

### 실험: 거대 PR 속 1줄 동작 변경 — 섞기 vs 나누기

구성: `Limit.allowed(amount, max)`를 30개 서비스 클래스가 호출한다. 한 PR이 ① 이름 바꾸기 `allowed → isWithinLimit`(기계적) ② 경계 조건 `amount <= max` → `amount < max`(동작 변경)를 함께 한다. 같은 최종 결과를 두 커밋으로 나눈 브랜치와 비교했다.

(실험, git 2.43.0, 2026-10-05)

```text
== 섞인 PR
 31 files changed, 31 insertions(+), 31 deletions(-)
== 결과 트리가 같은가
same-tree
== 커밋별
refactor: rename allowed -> isWithinLimit (동작 변경 없음) ::  31 files changed, 31 insertions(+), 31 deletions(-)
fix: 한도와 같은 금액은 거부 ::  1 file changed, 1 insertion(+), 1 deletion(-)
== 동작 커밋 diff 전체
-    static boolean isWithinLimit(long amount, long max) { return amount <= max; }
+    static boolean isWithinLimit(long amount, long max) { return amount < max; }
== 섞인 PR에서 동작 변경 줄을 찾으려면 -w 도 소용없다 (rename은 공백 변경이 아님)
 31 files changed, 31 insertions(+), 31 deletions(-)
== --word-diff 로 줄 안의 바뀐 단어만
    static boolean [-allowed(long-]{+isWithinLimit(long+} amount, long max) { return amount [-<=-]{+<+} max; }
```

- 관찰
  - 최종 트리는 같다(`same-tree`). 나눈다고 바뀌는 줄 수가 줄지는 않는다(둘 다 62줄).
  - 바뀌는 것은 **리뷰어가 동작을 판단해야 할 범위**다. 섞인 PR에서는 31개 파일 62줄 중 어디에 동작 변경이 있는지 리뷰어가 찾아야 한다. 나누면 "동작 변경 없음" 커밋은 기계적 확인(컴파일·테스트), 동작 커밋은 2줄만 깊게 본다.
  - `-w`(공백 무시)는 이름 바꾸기를 걸러 내지 못한다. `--word-diff`는 줄 안의 `<=` → `<`를 드러내지만, 31개 파일을 여전히 다 넘겨야 한다.
- 크기 점검 스크립트(JS)로 커밋별 줄 수를 보면 같은 사실이 숫자로 나온다.

```javascript
// pr-size.js — base..head 전체와 커밋별 변경 줄 수
const { execFileSync } = require('child_process');
const [repo, base, head, limit = '400'] = process.argv.slice(2);
const git = (...a) => execFileSync('git', ['-C', repo, ...a], { encoding: 'utf8' });
const numstat = range => git('diff', '--numstat', range).trim().split('\n').filter(Boolean)
  .map(l => l.split('\t')).reduce((s, [a, d]) => s + Number(a) + Number(d), 0);
const total = numstat(`${base}..${head}`);
console.log(`total changed lines: ${total} (limit ${limit}) -> ${total > Number(limit) ? 'SPLIT?' : 'ok'}`);
for (const c of git('rev-list', '--reverse', `${base}..${head}`).trim().split('\n'))
  console.log(`  ${c.slice(0, 7)} ${String(numstat(`${c}^..${c}`)).padStart(4)}  ${git('log', '-1', '--format=%s', c).trim()}`);
```

(실험, Node 18.19.1, 2026-10-05)

```text
total changed lines: 62 (limit 100) -> ok
  61de1c3   62  rename allowed -> isWithinLimit and tidy
total changed lines: 62 (limit 100) -> ok
  a09638e   62  refactor: rename allowed -> isWithinLimit (동작 변경 없음)
  f36f657    2  fix: 한도와 같은 금액은 거부
```

- 이 실험이 보이는 것은 "나누면 동작 변경이 드러난다"까지다. **리뷰 시간·결함 발견률은 측정하지 않았다**(사람 리뷰어가 필요). 그 부분은 위 표의 공개 자료로 대신한다.

### 실험: 리뷰 반영 뒤 재리뷰 — `git range-diff`

작성자가 리뷰 댓글을 반영해 커밋을 amend하고 force push하면, 리뷰어는 "지난번 본 것 대비 무엇이 바뀌었나"만 보고 싶다.

(실험, git 2.43.0, 2026-10-05)

```text
== range-diff v1 vs v2 (리베이스·amend 뒤 재리뷰 범위)
1:  a09638e = 1:  a09638e refactor: rename allowed -> isWithinLimit (동작 변경 없음)
2:  f36f657 < -:  ------- fix: 한도와 같은 금액은 거부
-:  ------- > 2:  1557497 fix: 한도와 같은 금액은 거부
== --creation-factor=100
1:  a09638e = 1:  a09638e refactor: rename allowed -> isWithinLimit (동작 변경 없음)
2:  f36f657 ! 2:  1557497 fix: 한도와 같은 금액은 거부
    @@ src/Limit.java
     @@
      class Limit {
     -    static boolean isWithinLimit(long amount, long max) { return amount <= max; }
    -+    static boolean isWithinLimit(long amount, long max) { return amount < max; }
    ++    static boolean isWithinLimit(long amount, long max) { return amount < max; }  // 한도 금액 자체는 거부(정책 2026-10)
      }
```

- `=`는 그대로인 커밋, `!`는 바뀐 커밋이다. 리뷰어는 첫 커밋을 다시 볼 필요가 없다.
- 기본값(`--creation-factor` 60)에서는 2줄짜리 작은 커밋에 주석 한 줄을 더한 것을 "삭제 + 새 커밋"으로 판정했다. 패치가 작으면 "diff의 diff"가 패치 크기에 비해 커 보이기 때문이다. git-range-diff 문서는 큰 변경을 통째 재작성으로 오판할 때 값을 키우라고 한다. 100으로 올리자 짝이 맞았다.

## 쓰이는 자료구조·알고리즘

- **diff = 최장 공통 부분수열(LCS)**: `git diff`의 기본은 Myers 알고리즘(git 문서: "basic greedy" — 가장 작은 diff를 보장하려면 `--diff-algorithm=minimal`). 리뷰 화면이 보여 주는 것은 "작은 편집 스크립트"이지 "의도"가 아니다. 기초는 [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md).
  - 그래서 이름 바꾸기·이동이 섞이면 diff가 커지고 의도가 묻힌다. `--color-moved`·`--word-diff`는 표시 방식을 바꿀 뿐이다.
- **`range-diff` = 최소 비용 할당 문제**: 두 커밋 묶음 사이에 "diff의 diff 줄 수"로 비용 행렬을 만들고 least-cost assignment를 푼다. 통째 삭제·추가에는 그 커밋 diff 크기에 creation factor(%)를 곱한 비용을 둬 엉뚱한 짝을 막는다(git-range-diff 문서 ALGORITHM).
- **CODEOWNERS = 경로 패턴 목록, 마지막 일치 우선**: 파일 경로마다 패턴을 위에서 아래로 맞춰 보고 마지막 일치를 쓴다(GitHub 문서).
- **리뷰 큐 = 대기열**: 리뷰 요청이 쌓이는 FIFO(또는 우선순위) 큐다. 도착률이 처리율을 넘으면 대기 시간이 계속 늘어난다(대기열 이론 직관, 해석). 그래서 eng-practices는 응답 속도를 기준으로 둔다.

## 적용 — 풀어나가는 법

### 1. 작성자 — 리뷰받기 쉬운 PR을 만든다

- 하나의 목적만. 구조 변경(이름·이동·포맷)과 동작 변경을 **다른 커밋 또는 다른 PR**로 나눈다([software-design/14-tidy-first](../../software-design/14-tidy-first/2-summary.md)).
  - eng-practices: 리팩터링은 분리하는 편이 리뷰어가 각 변경을 이해하기 쉽다. 단, 작은 이름 정리는 리뷰어와 합의하면 같이 둬도 된다.
- 설명(description)에 **왜**와 **어떻게 확인했나**를 쓴다. SWE@G 9장 모범 사례 "Write Good Change Descriptions".
- 올리기 전 스스로 diff를 읽는다. Cisco 사례 연구는 작성자가 미리 주석·설명을 단 리뷰에서 결함이 훨씬 적었다고 보고하고, 저자들은 그 원인을 작성자의 자가 리뷰로 추정한다.

```bash
git diff --stat main...HEAD                  # 크기 먼저
git log --oneline main..HEAD                 # 커밋이 목적별로 나뉘었나
git diff --color-moved=zebra main...HEAD     # 이동된 블록 구분 표시
```

### 2. 리뷰어 — 순서와 속도

1. 설명을 읽고 **이 변경이 필요한가, 설계가 맞나**부터 본다.
2. 핵심 파일(동작 변경)을 깊게, 기계적 변경은 CI 결과로 확인한다.
3. 테스트가 변경된 동작을 실제로 검증하나 본다([testing/01](../../testing/01-why-test-and-pyramid/2-summary.md)).
4. 댓글은 필수/선택을 구분(`Nit:`)하고, 이유를 붙인다.
5. 응답은 늦어도 1영업일 안에(eng-practices "Speed of Code Reviews": "One business day is the maximum time it should take to respond"). 너무 크면 나눠 달라고 요청한다.

- 사소한 남은 댓글만 있으면 "LGTM with comments"로 승인하고 작성자를 믿는다(eng-practices) — 시간대가 다른 팀에서 하루 대기를 줄인다.

### 3. 저장소 설정으로 받쳐 준다

```text
# .github/CODEOWNERS — 마지막 일치 패턴이 우선
*                     @example-org/team-platform     # 팀은 @조직/팀 형식 (GitHub 문서)
/payment/             @example-org/team-payment
/payment/limits/      @example-org/team-risk
/.github/CODEOWNERS   @example-org/team-platform        # 소유자 파일 자체의 소유자 (GitHub 문서 권고)
```

- 보호 브랜치: 필수 리뷰 수, 코드 소유자 리뷰, 상태 검사(CI) 통과 필수.
- 리뷰 반영 뒤 재리뷰는 `git range-diff`(또는 호스팅의 "changes since last review" 기능)로 바뀐 부분만 본다.

## 장애 시나리오와 대처

### 1. 거대 PR → 형식적 승인(LGTM)으로 버그 통과 (⚠ 커리큘럼)

- **현상**: 수천 줄 PR이 몇 분 만에 승인되고, 그 안의 1줄 동작 변경이 운영 장애를 낸다.
- **보이는 형태**: PR 크기 대비 리뷰 시간·댓글 수가 비정상적으로 적다(예: 2,000줄에 댓글 0). Cisco 사례 연구에서는 검토 속도가 시간당 450줄을 넘은 리뷰의 87%가 결함 밀도 평균 미만이었다.
- **원인**: 리뷰어가 이해할 수 있는 양을 넘었다. 기계적 변경과 동작 변경이 섞여 핵심이 묻혔다(실험: 62줄 중 2줄).
- **대처**
  - PR 크기 상한과 경고(예시 기준 400줄 — 팀이 정한다), 목적별 분리.
  - 리뷰어는 "너무 커서 제대로 볼 수 없다"고 말하고 분할을 요청한다(eng-practices).
  - 회귀 테스트를 PR에 포함시켜 리뷰어가 동작을 테스트로 확인하게 한다.

### 2. 리뷰 병목 — 대기 시간이 PR을 더 키운다

- **현상**: PR이 며칠씩 대기, 작성자는 그 위에 다음 작업을 쌓는다. 결국 장수 브랜치·머지 지옥([04](../04-branching-strategies/2-summary.md)).
- **보이는 형태**: 첫 응답까지 걸린 시간이 길다(Sadowski 2018의 Google 중앙값: 작은 변경 1시간 미만 — 비교 기준). 열린 PR 수가 계속 증가.
- **원인**: 리뷰 우선순위가 낮다, 승인 요구가 과하다(DORA trunk-based 함정 "overly heavy code-review process"), 소유자가 한두 명에 몰렸다.
- **대처**: 1영업일 응답 기준, 필수 승인 수 최소화(Google은 대부분 1명), 소유자 분산, 작은 PR.

### 3. 취향 논쟁으로 리뷰가 멈춘다

- **현상**: 같은 PR에 스타일·이름 댓글이 수십 개, 정작 설계 문제는 놓친다.
- **원인**: 기계가 할 일(포맷·린트)을 사람이 한다. 기준 문서가 없다([14-quality-standards](../14-quality-standards/2-summary.md), 원본 [engineering/development-standards/quality-standards](../../engineering/development-standards/quality-standards/)).
- **대처**: 포매터·린터를 CI에서 강제("Automate Where Possible"), 선택 사항은 `Nit:`, 기준은 문서로.

### 4. 리뷰가 지식 공유를 못 한다 — 한 사람만 아는 코드

- **현상**: 특정 모듈은 늘 같은 사람이 쓰고 같은 사람이 리뷰한다. 그 사람이 휴가면 아무도 못 고친다.
- **원인**: 리뷰어 배정이 소유자 1인에 고정.
- **대처**: 학습 목적 리뷰어를 추가로 붙인다. Bacchelli & Bird·Sadowski 둘 다 지식 전달·교육을 리뷰의 주요 효과로 보고한다. 지식 분포는 [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md)로 측정.

## 핵심 문장

- 코드 리뷰의 가치는 결함 발견만이 아니다 — Microsoft·Google 연구 모두 지식 전달·규범 유지·이해 공유를 주요 효과로 보고했다.
- Google의 승인 기준은 "완벽한 코드"가 아니라 "시스템의 코드 건강을 분명히 개선하는가"다.
- 크기 권고는 출처마다 성격이 다르다 — 지침(100줄 적당·1000줄 과대), 측정(Google 중앙값 24줄), 벤더 사례 연구(한 번에 200~400줄 이하, 60~90분 이하).
- 이름 바꾸기와 동작 변경을 한 PR에 섞으면 줄 수는 같아도 리뷰어가 동작을 판단해야 할 범위가 넓어진다 — 실험에서 62줄 중 2줄이 동작 변경이었다.
- 리뷰 속도는 리뷰 품질만큼 중요하다 — 느린 리뷰는 PR을 키우고, 큰 PR은 형식적 승인을 부른다.
- 재리뷰는 `git range-diff`로 바뀐 커밋만 본다.

## 관련 주제·근거

- 선행
  - [04-branching-strategies](../04-branching-strategies/2-summary.md) — 짧은 브랜치와 빠른 리뷰는 짝
  - [03-version-control-and-git-internals](../03-version-control-and-git-internals/2-summary.md) — diff·병합·`--remerge-diff`
- 후속·연결
  - [14-quality-standards](../14-quality-standards/2-summary.md) — 리뷰 편차를 줄이는 기준(원본 [engineering/development-standards/quality-standards](../../engineering/development-standards/quality-standards/))
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [19-practice-symptom-index](../19-practice-symptom-index/2-summary.md)("리뷰 병목")
  - [software-design/14-tidy-first](../../software-design/14-tidy-first/2-summary.md) — 구조 변경과 동작 변경 분리
  - [software-design/53-code-forensics-hotspots](../../software-design/53-code-forensics-hotspots/2-summary.md) — 지식 분포
  - [testing/01-why-test-and-pyramid](../../testing/01-why-test-and-pyramid/2-summary.md) — 리뷰가 아니라 테스트가 막아야 할 것
  - [algorithm/21-dp-basics](../../algorithm/21-dp-basics/2-summary.md) — diff = LCS
- 문서·연구
  - Google eng-practices — The Standard of Code Review, What to look for, Speed of Code Reviews(1영업일, LGTM with comments), Small CLs(100/1000줄, 리팩터링 분리) <https://google.github.io/eng-practices/>
  - SWE@G 9장 "Code Review"(Tom Manshreck·Caitlin Sadowski) — LGTM·소유자·readability, 이점 목록, 약 200줄·35% 단일 파일·하루 안 첫 피드백·대부분 한 사람이 세 역할, 모범 사례 <https://abseil.io/resources/swe-book/html/ch09.html>
  - C. Sadowski, E. Söderberg, L. Church, M. Sipko, A. Bacchelli, "Modern Code Review: A Case Study at Google", ICSE-SEIP 2018 — 약 900만 변경, 중앙값 24줄, 지연 중앙값 4시간 미만, 리뷰어 중앙값 1, 기대 4종 <https://sback.it/publications/icse2018seip.pdf>
  - A. Bacchelli, C. Bird, "Expectations, Outcomes, and Challenges of Modern Code Review", ICSE 2013 <https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/>
  - J. Cohen, "Code Review at Cisco Systems", 『Best Kept Secrets of Peer Code Review』(SmartBear, 2006) — 벤더 사례 연구 <https://static1.smartbear.co/support/media/resources/cc/book/code-review-cisco-case-study.pdf> · SmartBear 웹 글 "Best Practices for Code Review" <https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/>
  - DORA capability "Trunk-based development" — 무거운 리뷰·비동기 리뷰 함정 <https://dora.dev/capabilities/trunk-based-development/>
  - GitHub Docs "About code owners" — 위치·마지막 일치 우선·소유자 중 1명 승인 <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners>
  - git-range-diff 문서(2.43 man) — ALGORITHM(비용 행렬·최소 비용 할당), `--creation-factor` 기본 60
- 실험 목록(일회용 저장소, git 2.43.0 / Node 18.19.1)
  - 30개 호출부 이름 바꾸기 + 경계 조건 1줄: 섞인 PR vs 두 커밋 분리 — `--shortstat`, `-w`, `--word-diff`, 트리 동일성
  - `pr-size.js`로 커밋별 변경 줄 수
  - amend 뒤 `git range-diff` — 기본 creation factor 60에서 짝 실패, 100에서 짝
  - 측정하지 않은 것: 사람 리뷰어의 시간·결함 발견률(공개 자료로 대신)
