# software-design/14-tidy-first — Tidy First: 구조 변경과 동작 변경을 섞지 않는다 — 정리 (힌트)

## 해결하는 문제

코드를 고치다 보면 "온 김에" 이름도 바꾸고 함수도 정리하고 싶다. 그 정리를 동작 변경과 한 커밋·한 PR에 넣으면 세 가지가 어려워진다.

```text
 섞은 PR (44줄, 그중 정책 변경 2줄)               나눈 PR
 ┌────────────────────────────────────┐          ┌────────────────────────────┐
 │ - Lib.proc(d, m) ...               │          │ PR 1: 정리 (동작 그대로)    │ 43줄, 특성 테스트 지문 동일
 │ + LateFees.lateFee(daysOverdue,...)│          │  → 빠르게 훑고 승인         │
 │ ... rename 수십 줄 ...              │          ├────────────────────────────┤
 │ + member ? MEMBER_CAP : CAP   ← 여기│          │ PR 2: 회원 상한 3000        │ 3줄
 └────────────────────────────────────┘          │  → 이 줄만 꼼꼼히           │
  ① 리뷰: 정책 변경 2줄이 정리 속에 묻힌다         └────────────────────────────┘
  ② 확인: "정리는 동작을 안 바꿨나"를 따로 못 잰다
  ③ 되돌리기: 정책만 되돌리려 해도 정리까지 같이 되돌아간다
```

- *정리(tidying)*: Beck 『Tidy First?』(O'Reilly, 2023)의 용어. 동작을 바꾸지 않는 작은 구조 개선(가드 절, 죽은 코드 삭제, 설명 변수 등). 리팩터링의 아주 작은 단위다.
- *구조 변경*: 코드의 모양(이름·경계·순서)만 바꾸는 것. 동작은 그대로.
- *동작 변경*: 바깥에서 보이는 결과가 바뀌는 것(기능 추가·버그 수정·정책 변경).

쉬운 예: 이사하며 짐 정리(구조)와 가구 교체(동작)를 같은 날 하면, 나중에 "새 소파가 문제"라서 돌려보내려 할 때 정리해 둔 수납까지 원래대로 되돌려야 한다.\
똑같은 구조다.\
실무 예: 연체료 계산 함수 이름을 바꾸고 가드 절로 펴면서 회원 상한 정책도 바꿨다. 리뷰어는 이름 변경 수십 줄 사이의 정책 한 줄을 놓친다.

## 동작·원리

### 1. 두 종류의 변경은 되돌리기 쉬움이 다르다

```text
            되돌리기         리뷰에 필요한 주의          검증 방법
 구조 변경   쉽다(인라인하면 끝) 낮음 — 훑어보기         "전후 출력이 같다" (특성 테스트)
 동작 변경   어렵다(이미 고객·    높음 — 한 줄씩          "새 출력이 맞다" (새 기대값)
            데이터에 영향)
```

- Kent Beck, "Structure & Behavior"(뉴스레터, 2021-02-09): 구조 변경과 동작 변경은 근본적으로 다르며, 둘을 가르는 것은 **되돌릴 수 있음(reversibility)** 이다. 추출한 도우미 함수는 인라인하면 없던 일이 된다. 보고서 값이나 판매 과정을 바꾼 결과는 되돌리기 어렵다.
- 그래서 Beck은 되돌리기 쉬운 구조 변경은 가볍게, 되돌리기 어려운 동작 변경은 꼼꼼히 보라고 권한다(같은 글). 서비스 분리처럼 되돌리기 비싼 구조 변경은 예외로 신중히 다룬다.
- Beck, "Management: Separate Tidying"(2022-03-15)은 "정리를 동작 변경과 함께 넣었더니 리뷰어가 PR이 너무 길다고 불평한다"는 상황에서 출발한다(공개된 도입부까지만 확인).

### 2. 정리 목록 (Part I)

```text
 가드 절            if (d > 0) { ...깊은 본문... }      →  if (d <= 0) return 0;  본문
 죽은 코드 삭제      아무도 안 부르는 메서드               →  삭제 (git이 기억한다)
 대칭 맞추기         같은 일을 두 방식으로                  →  한 방식으로 통일
 설명 변수          return d * 200 > 5000 ? ...          →  long perDay = ...;
 설명 상수          5000                                 →  CAP
 읽는 순서·응집 순서  관련 코드가 흩어짐                    →  함께 읽히게 옮김
 도우미 추출         긴 함수의 한 덩어리                   →  이름 붙은 함수
```

- 『Tidy First?』 Part I은 정리 15개를 장마다 하나씩 다룬다: Guard Clauses, Dead Code, Normalize Symmetries, New Interface Old Implementation, Reading Order, Cohesion Order, Move Declaration and Initialization Together, Explaining Variables, Explaining Constants, Explicit Parameters, Chunk Statements, Extract Helper, One Pile, Explaining Comments, Delete Redundant Comments. 목차는 독자 요약 두 곳(workingsoftware.dev, danlebrero.com)으로 확인했다. 원서 목차는 직접 열지 못했다 [?].
- 각 정리는 Fowler 카탈로그의 작은 리팩터링과 겹친다(Extract Variable, Extract Function, Slide Statements 등 — [13-refactoring](../13-refactoring/2-summary.md)).

### 3. 언제 정리하나 — 먼저·나중·나중에 따로·안 함 (Part II)

```text
  이 코드를 다시 만질 일이 없다 ─────────────────────> 안 함 (Never)
  정리하면 지금 바꿀 동작이 쉬워진다 ─────────────────> 먼저 (First)
  방금 바꿨고 곧 같은 곳을 또 바꾼다 ─────────────────> 바로 뒤 (After)
  지금은 시간이 없다 / 크다 ─────────────────────────> 나중에 따로 (Later, 목록에 적어 둔다)
```

- Part II(Managing)의 장: Separate Tidying, Chaining, Batch Sizes, Rhythm, Getting Untangled, First After Later Never(독자 요약으로 확인 [?]).
- 판단 기준 요지(독자 노트 인용 — 원문 직접 확인 못 함 [?]): 다시 안 만질 코드면 안 함, 시간이 부족하면 나중, 같은 곳을 곧 또 바꾸면 바로 뒤, 정리하면 변경이 쉬워지면 먼저.
- "먼저"의 원형은 Beck의 2012년 트윗이다: "for each desired change, make the change easy (warning: this may be hard), then make the easy change". Fowler "An example of preparatory refactoring"(2015-01-05)이 이 문장을 인용하며 준비 리팩터링(preparatory refactoring)을 보인다.
- *Getting Untangled*(독자 노트 인용 [?]): 정리와 변경이 뒤엉켜 버렸다면 버리고 정리부터 다시 하는 것도 선택지다.

### 4. 커밋·PR 분리

```text
  main ──●───────────●──────────────●──────────>
         │  PR 1: 정리  │  PR 2: 동작   │  (나중에 따로) PR 3: 정리
         │  지문 동일    │  3줄          │
         └ 리뷰 짧게    └ 리뷰 꼼꼼히
```

- 정리 커밋: 동작이 그대로임을 특성 테스트(출력 지문)로 보인다. 리뷰어는 "이름이 좋아졌나"만 본다.
- 동작 커밋: 바뀐 줄만 담는다. 리뷰어는 정책·경계값만 본다.
- 한 PR에 둘을 담아야 한다면 최소한 커밋을 나눈다(리뷰어가 커밋 단위로 볼 수 있게).

### 5. 결합·응집의 경제학 (Part III, 요지)

- Part III(Theory)의 장: Beneficially Relating Elements, Structure and Behavior, Economics: Time Value and Optionality, A Dollar Today > A Dollar Tomorrow, Options, Options Versus Cash Flows, Reversible Structure Changes, Coupling, Constantine's Equivalence, Coupling Versus Decoupling, Cohesion(독자 요약으로 확인 [?]).
- 두 힘(해석을 섞은 요지):
  - *시간 가치*: 오늘의 돈이 내일의 돈보다 값지다 → 동작(가치)을 먼저 내고 정리는 미루고 싶다.
  - *옵션 가치*: 구조가 좋으면 "내일 할 수 있는 일"의 선택지가 늘어난다 → 정리를 먼저 하고 싶다. 23장 요지로 소개되는 문장: 소프트웨어는 오늘 하는 일(동작)과 내일 하게 만들 수 있는 일(옵션)로 가치를 만든다(독자 노트 인용 [?]).
- *Constantine의 등가(독자 노트의 정리 [?])*: 소프트웨어 비용 ≈ 변경 비용 ≈ 큰 변경의 비용 ≈ 결합. 큰 변경이 비싼 이유는 한 요소를 바꿀 때 함께 바꿔야 하는 요소(결합)가 연쇄되기 때문이다.
- 결합·응집 기초는 [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md).

### 실험: 섞은 커밋 vs 나눈 커밋 — 리뷰 크기, 정리만의 검증, 되돌리기

연체료 계산을 정리(이름 `Lib.proc` → `LateFees.lateFee`, 가드 절, 설명 상수)하고, 정책(회원 상한 3,000원)을 바꿨다. 이후 다른 사람이 새 이름을 쓰는 `Kiosk.java`를 커밋했다. 그 뒤 정책을 되돌려야 하는 상황이다.

```java
// 정리 뒤 (동작 그대로)
static long lateFee(int daysOverdue, boolean member) {
  if (daysOverdue <= 0) return 0;
  long perDay = member ? MEMBER_PER_DAY : GUEST_PER_DAY;
  return Math.min(daysOverdue * perDay, CAP);
}
// 동작 변경 (회원 상한 3000)
return Math.min(daysOverdue * perDay, member ? MEMBER_CAP : CAP);
```

- 특성 테스트(`Golden.java`): 연체일 −1~80, 회원/비회원, 합계 경로의 출력을 이어 붙여 해시(지문)로 찍는다.

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, `scratchpad/sd/11/e14/build.sh`·`measure.sh`, 2026-10-02)

```text
=== 리뷰어가 읽을 diff ===
--- mixed-change: 연체료 정리 + 회원 상한 3000
 5 files changed, 21 insertions(+), 23 deletions(-)
--- split-tidy: 정리: 이름·가드 절·설명 상수 (동작 그대로)
 5 files changed, 20 insertions(+), 23 deletions(-)
--- split-change: 회원 상한 3000
 1 file changed, 2 insertions(+), 1 deletion(-)
--- split-change 전체 diff:
+  private static final long MEMBER_CAP = 3000;
-    return Math.min(daysOverdue * perDay, CAP);
+    return Math.min(daysOverdue * perDay, member ? MEMBER_CAP : CAP);
=== 특성 테스트 지문 (정리만 한 커밋은 시작과 같아야 한다) ===
@start: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
@split-tidy: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
@split-change: fingerprint=73c1301d  one(40)=3000 guest(40)=5000
@mixed-change: fingerprint=73c1301d  one(40)=3000 guest(40)=5000
=== 회원 상한 정책을 되돌려야 한다 (키오스크 커밋 뒤) ===
--- split: git revert split-change → exit=0, 충돌 0건, 되돌린 파일:  1 file changed, 1 insertion(+), 2 deletions(-)
    javac exit=0
@rev-split: fingerprint=4cf83b86  one(40)=4000 guest(40)=5000
--- mixed: git revert mixed-change → exit=0, 충돌 0건, 되돌린 파일:  5 files changed, 23 insertions(+), 21 deletions(-)
    Kiosk.java:2: error: cannot find symbol
    javac exit=1
```

- 관찰 1(리뷰) — 섞은 커밋은 44줄이고 정책 변경은 그중 2줄이다. 게다가 `Lib.java` 삭제 + `LateFees.java` 새 파일로 보이므로, 상한 줄은 "바뀐 줄"이 아니라 새 파일의 한 줄로 나타난다. 나눈 쪽의 동작 커밋은 3줄짜리 diff 전체가 정책이다.
- 관찰 2(검증) — 정리 커밋의 지문 `4cf83b86`이 시작과 같다. "정리는 동작을 안 바꿨다"를 따로 증명할 수 있다. 섞은 커밋은 지문이 바뀌는데, 그 원인이 정책인지 정리 실수인지 지문만으로는 구별할 수 없다.
- 관찰 3(되돌리기) — 나눈 쪽은 정책 커밋만 revert해 1파일이 바뀌었고 컴파일·지문(`4cf83b86`)이 시작 동작으로 돌아왔다. 섞은 쪽은 revert가 **텍스트 충돌 없이** 끝났지만 정리(이름 변경)까지 되돌려, 새 이름을 쓰던 `Kiosk.java`가 컴파일되지 않았다.
- 해석: 섞인 커밋은 "정책만 되돌리기"라는 선택지를 없앤다. 수동으로 정책 줄만 되돌리는 새 커밋을 써야 한다.

## 쓰이는 자료구조·알고리즘

- **git 커밋 DAG와 revert**: revert는 지정한 커밋의 diff를 역으로 적용한 새 커밋이다. 되돌릴 수 있는 단위 = 커밋 단위다. 섞인 커밋은 역적용 단위도 섞인다(실험 관찰 3).
- **출력 지문(해시)**: 큰 출력 문자열을 해시 하나로 줄여 전후 동일성을 빠르게 비교한다. 해시가 같으면 출력이 같다고 보는 것은 충돌 확률이 무시할 만할 때의 가정이다. 다르면 원본 출력을 비교해 원인을 본다.
- **diff의 이름 변경 탐지**: `git diff -M`은 삭제된 파일과 추가된 파일의 내용 유사도로 rename을 짝짓는다. 내용이 많이 바뀌면 rename으로 안 보이고 "삭제 + 새 파일"로 보인다(실험 관찰 1의 `Lib.java`/`LateFees.java`). 이름 변경 커밋을 내용 변경과 나누면 rename 탐지도 잘 된다(해석).
- **이동 감지**: `git diff --color-moved`는 줄이 옮겨졌을 뿐인지 색으로 구분한다. 정리 커밋 리뷰에서 "옮기기만 했나"를 빠르게 확인하는 도구다.

## 적용 — 풀어나가는 법

1. **동작 변경을 시작하기 전에 묻는다.** 이 코드를 정리하면 변경이 쉬워지나(먼저)? 곧 또 만지나(바로 뒤)? 시간이 없나(나중에, 목록에 적기)? 다시 안 만지나(안 함)?
2. **정리는 따로 커밋한다.** 커밋 메시지에 "동작 그대로"를 밝히고, 특성 테스트나 기존 테스트가 그대로 초록임을 확인한다.
3. **정리와 변경이 이미 섞였으면 나눈다.**

```bash
git add -p                 # 덩어리 단위로 정리만 골라 스테이징
git commit -m "정리: 이름·가드 절 (동작 그대로)"
git add -A && git commit -m "회원 상한 3000"
# 너무 엉켰으면: 변경을 stash 하고 정리부터 다시 (Getting Untangled)
git stash && <정리> && git commit -m "정리 ..." && git stash pop
```

4. **리뷰를 돕는 옵션**: `git diff -M`(이름 변경 짝짓기), `git diff --color-moved`(이동만 한 줄), `git diff -w`(공백만 바뀐 줄 무시)로 정리 커밋이 정말 정리뿐인지 빠르게 본다.
5. **PR 크기**: 정리 PR은 작게 여러 개(Beck은 정리 PR에 정리를 가능한 적게 넣으라고 권한다 — 독자 노트 인용 [?]). 리뷰 정책은 engineering-practice 05 code-review([engineering-practice/README](../../engineering-practice/README.md), 미작성).
6. **정리에 시간을 상한한다.** 정리가 기능 PR을 며칠씩 막으면 "나중에 따로"로 넘기고 목록에 남긴다.

## 장애 시나리오와 대처

### 1. 이름 변경 300줄과 로직 수정 5줄이 한 PR — 리뷰어가 버그를 못 본다 (⚠ 커리큘럼)

- 현상: 승인된 PR이 배포된 뒤 정책 버그가 나온다. 리뷰 코멘트는 이름에 관한 것뿐이었다.
- 보이는 형태: PR diff 수백 줄, 로직 변경은 새 파일 안의 한 줄로 묻혀 있다(실험 관찰 1).
- 원인: 되돌리기 쉬운 변경과 어려운 변경이 같은 주의 수준으로 리뷰됐다.
- 대처: 정리 PR과 동작 PR을 나눈다. 이미 섞였으면 `git add -p`로 커밋을 나눠 다시 올린다.

### 2. 섞인 커밋을 revert하면 정리까지 날아가 되돌리기 불가 (⚠ 커리큘럼)

- 현상: 정책 장애로 급히 revert했더니 빌드가 깨진다.
- 보이는 형태: `git revert`는 충돌 없이 끝났는데 `cannot find symbol`(실험: `Kiosk.java`). 그 사이 다른 사람이 새 이름에 의존했다.
- 원인: 되돌릴 단위(커밋)에 정리와 동작이 같이 들어 있다.
- 대처: 당장은 정책 줄만 손으로 되돌리는 새 커밋을 만든다(roll-forward). 다음부터 동작 변경은 독립 커밋으로 둔다.

### 3. "정리하느라" 기능 PR이 2주 지연, 충돌 누적 (⚠ 커리큘럼)

- 현상: 기능 하나에 붙은 정리가 계속 늘어 PR이 2주째 열려 있다. main과 충돌이 쌓인다.
- 보이는 형태: 리베이스할 때마다 충돌, 리뷰어 피로, "이것도 고치는 김에" 커밋이 계속 붙는다.
- 원인: 정리 범위에 상한이 없었다. "먼저"가 아니라 "나중에 따로"였어야 할 정리까지 붙었다.
- 대처: 변경을 쉽게 만드는 데 필요한 정리만 먼저 하고, 나머지는 목록에 적어 따로 낸다. 정리 PR은 작게 자주 합친다([13-refactoring](../13-refactoring/2-summary.md) 실험 B: 오래 사는 브랜치의 충돌).

### 4. 정리 커밋이 사실은 동작을 바꿨다

- 현상: "동작 그대로"라고 쓴 정리 커밋 뒤 숫자가 달라졌다.
- 보이는 형태: 특성 테스트 지문이 바뀐다. 테스트가 없으면 한참 뒤에 드러난다.
- 원인: 가드 절로 펴며 경계 조건을 잘못 뒤집는(`d > 0`의 반대를 `d <= 0`이 아니라 `d < 0`으로 써서 d = 0이 본문으로 들어감) 등, 정리가 동작을 건드렸다.
- 대처: 정리 커밋마다 지문 비교를 돌린다(실험: 시작과 `split-tidy`의 지문이 같았다). 다르면 그 커밋은 정리가 아니다 — 되돌리고 다시.

## 핵심 문장

- 구조 변경과 동작 변경은 되돌리기 쉬움이 다르다(Beck). 그래서 따로 커밋하고 따로 리뷰한다.
- 정리 커밋은 "출력이 그대로다"로 검증하고, 동작 커밋은 "새 출력이 맞다"로 검증한다. 섞으면 둘 다 못 한다.
- 정리 시점은 먼저·바로 뒤·나중에 따로·안 함 중 고른다. "변경을 쉽게 만든 뒤 쉬운 변경을 하라"가 "먼저"의 근거다.
- 실험에서 섞은 커밋은 44줄 중 정책 2줄이 묻혔고, revert하자 충돌 없이 정리까지 되돌아가 다른 사람 코드가 컴파일되지 않았다. 나눈 쪽은 3줄짜리 정책 커밋만 깔끔히 되돌렸다.
- 정리에도 상한을 둔다. 기능을 막는 정리는 "나중에 따로"로 넘긴다.

## 관련 주제·근거

- 선행
  - [13-refactoring](../13-refactoring/2-summary.md) — 동작 보존 변환, 작은 단계, 특성 테스트
  - engineering-practice 05 code-review — 리뷰의 목적·크기([engineering-practice/README](../../engineering-practice/README.md), 미작성)
- 후속·연결
  - [02-modularity-coupling-cohesion](../02-modularity-coupling-cohesion/2-summary.md) — 결합·응집 기초
  - [11-when-to-abstract](../11-when-to-abstract/2-summary.md) — 정리의 하나인 도우미 추출을 언제 하나
  - [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md) — 테스트 없는 코드에서 먼저 테스트 지점 만들기
  - [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md) — 죽은 코드 삭제
- 글·문서
  - Kent Beck, 『Tidy First?: A Personal Exercise in Empirical Software Design』, O'Reilly, 2023-10-17 출간(Google Books 서지). 1·2·3부 목차는 독자 요약으로 확인 [?] — <https://www.workingsoftware.dev/summary-of-tidy-first-book/>, <https://danlebrero.com/2024/08/07/tidy-first-summary/>
  - Kent Beck, "Structure & Behavior", 2021-02-09 <https://newsletter.kentbeck.com/p/structure-and-behavior>
  - Kent Beck, "Management: Separate Tidying", 2022-03-15(도입부만 공개) <https://newsletter.kentbeck.com/p/management-separate-tidying>
  - Martin Fowler, "An example of preparatory refactoring" — Beck의 "make the change easy" 인용 <https://martinfowler.com/articles/preparatory-refactoring-example.html>
  - git 문서 `git revert`·`git diff`(`-M`, `--color-moved`) <https://git-scm.com/docs/git-diff>
- 실험 목록 (코드: scratchpad `sd/11/e14/build.sh`·`measure.sh`, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0)
  - 섞은 커밋 vs 나눈 커밋: diff 크기, 특성 테스트 지문(시작·정리·변경), 후속 커밋 뒤 정책만 revert 했을 때 충돌·컴파일·지문
