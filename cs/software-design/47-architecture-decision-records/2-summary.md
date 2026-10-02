# software-design/47-architecture-decision-records — ADR: 결정·맥락·결과를 코드 옆에 남긴다 — 정리 (힌트)

## 해결하는 문제

코드는 **무엇을** 하는지 보여 준다. **왜** 그렇게 했는지는 보여 주지 않는다.
6개월 뒤 새로 온 사람이 이상해 보이는 결정을 만나면 선택지는 둘뿐이다.

```text
 "결제 재시도가 왜 2회지?"
      │
      ├─ 맹목적으로 따른다 → 맥락이 바뀌어 다시 볼 때가 됐는데도 아무도 못 건드린다
      └─ 맹목적으로 바꾼다 → 그 결정이 막고 있던 장애(재시도 폭주)가 되살아난다
```

- Nygard(2011)는 이 두 선택지를 "blindly accept"와 "blindly change"로 적는다. 앞쪽이 쌓이면 팀이 아무것도 못 바꾸게 되고, 뒤쪽은 결정이 지키던 비기능 요구를 모르는 채 깨뜨린다고 쓴다.
- *ADR(Architecture Decision Record)*: 아키텍처적으로 중요한 결정 하나와 그 근거를 짧은 텍스트 파일 하나에 적은 기록.
- *아키텍처적으로 중요한 결정*: Nygard의 기준으로 구조·비기능 특성·의존성·인터페이스·구성 기법에 영향을 주는 결정.

쉬운 예: 집 수리 기록부. "2024년 배관을 동관에서 PVC로 바꿈 — 겨울 동파 때문. 대신 온수 온도 60도 이하로 쓸 것." 이 한 줄이 없으면 다음 집주인이 온수기를 80도로 올린다.\
똑같은 구조다.\
실무 예: "주문 서비스는 결제 DB를 직접 읽지 않는다 — 결제 팀 스키마 변경 때 장애 2회. 대가: 주문 목록의 결제 상태는 이벤트로 받아 최대 수 초 늦다."

## 동작·원리

### 1. Nygard 형식 — 다섯 부분

```text
 doc/adr/0004-payment-retry.md
 ┌──────────────────────────────────────────────┐
 │ # 4. 결제 재시도는 최대 2회        ← 제목: 짧은 명사구 │
 │ ## Status   Accepted              ← 제안·수락·폐기·대체 │
 │ ## Context  힘(force)들, 가치 중립적 사실        │
 │ ## Decision "We will …" 능동태 완전한 문장      │
 │ ## Consequences 좋은 것·나쁜 것·중립 모두        │
 └──────────────────────────────────────────────┘
```

- Nygard, "Documenting Architecture Decisions"(2011-11-15)의 규칙:
  - 저장소 안 `doc/arch/adr-NNN.md`에 Markdown 같은 가벼운 형식으로 둔다.
  - 번호는 순서대로 늘고 **재사용하지 않는다**.
  - 결정을 뒤집으면 옛 ADR을 지우지 않고 **superseded로 표시**한다("그것이 결정이었다"는 사실도 의미가 있다).
  - 문서 하나는 한두 쪽. 미래 개발자와 대화하듯 완전한 문장으로 쓴다.
  - **결과(Consequences)에는 긍정만이 아니라 모든 결과**를 적는다. 한 ADR의 결과는 다음 ADR의 맥락이 되기 쉽다.
- 그 글 자체가 ADR 형식(Context·Decision·Status·Consequences)으로 쓰여 있다.

### 2. 상태 전이와 대체 사슬

```text
 proposed ──합의──> accepted ──새 ADR이 뒤집음──> superseded by N
                       │
                       └──더 이상 해당 없음──> deprecated

 ADR 2 "재시도는 라이브러리 기본값"  ◀── Supercedes ──  ADR 4 "재시도 최대 2회"
           Superceded by ──────────────────────────▶
```

- 옛 기록은 남고, 양방향 링크가 "지금의 결정"과 "예전의 결정"을 잇는다.
- 그림의 deprecated 화살표("더 이상 해당 없음")는 이 노트의 정리다. Nygard 원문은 "나중 ADR이 결정을 바꾸거나 뒤집으면 deprecated 또는 superseded로 표시하고 대체 ADR을 가리킨다"고만 적어, 두 상태를 구분하는 기준은 두지 않는다.

### 실험: adr-tools로 만들고 대체하기

Nat Pryce의 `adr-tools`(GitHub `npryce/adr-tools`, 3.0.0 이후 커밋 `b3279ba`)로 ADR 넷을 만들고, 4번이 2번을 대체하게 했다.

```bash
adr init doc/adr
adr new "결제 재시도는 클라이언트 라이브러리 기본값을 쓴다"
adr new "주문 조회에 Redis 캐시를 둔다"
adr new -s 2 "결제 재시도는 최대 2회, 지수 백오프와 지터"     # -s 2: 2번을 대체
adr list; adr generate toc; adr generate graph
# 노트에 싣느라 출력의 마크다운 링크 문법은 sed로 "[제목] → 파일" 꼴로 바꿨다(스크립트에 그대로 있음)
```

(실험, adr-tools `b3279ba`(2020-03-30), GNU coreutils `tr` 9.4, 로캘 ko_KR.UTF-8, `scratchpad/sd/45/e47/adr_demo.sh`, 2026-10-02 — 결정적)

```text
### adr list
doc/adr/0001-record-architecture-decisions.md
doc/adr/0002-.md
doc/adr/0003-redis.md
doc/adr/0004-2.md
### 0002 상태 절
## Status

Superceded by [4. 결제 재시도는 최대 2회, 지수 백오프와 지터] → 0004-2.md

## Context
### 0004 상태 절
## Status

Accepted

Supercedes [2. 결제 재시도는 클라이언트 라이브러리 기본값을 쓴다] → 0002-.md
```

```text
### adr generate graph
digraph {
  node [shape=plaintext];
  subgraph {
    _1 [label="1. Record architecture decisions"; URL="0001-record-architecture-decisions.html"];
    _2 [label="2. 결제 재시도는 클라이언트 라이브러리 기본값을 쓴다"; URL="0002-.html"];
    _1 -> _2 [style="dotted", weight=1];
    _3 [label="3. 주문 조회에 Redis 캐시를 둔다"; URL="0003-redis.html"];
    _2 -> _3 [style="dotted", weight=1];
    _4 [label="4. 결제 재시도는 최대 2회, 지수 백오프와 지터"; URL="0004-2.html"];
    _3 -> _4 [style="dotted", weight=1];
  }
  _4 -> _2 [label="Supercedes", weight=0]
}
```

- 관찰 1 — `-s 2`는 2번의 상태를 `Accepted`에서 `Superceded by [4 …]`로 바꾸고, 4번에 `Supercedes [2 …]`를 단다. 링크가 양쪽에 생긴다. 철자는 도구 소스 그대로 `Superceded`다(`adr-new` 117·119행).
- 관찰 2 — **한글 제목의 파일 이름이 비었다**(`0002-.md`, `0004-2.md`). `adr-new` 103행이 `tr -Ccs [:alnum:] -`로 slug를 만드는데, GNU `tr`는 바이트 단위로 동작해 한글 바이트를 영숫자로 보지 않는다(같은 호스트에서 `echo -n "결제 abc" | tr -Ccs '[:alnum:]' -` → `-abc`). 파일 이름만으로는 무슨 결정인지 알 수 없다. 대처: 제목에 영문 키워드를 넣거나(`payment-retry`), 파일을 만든 뒤 이름을 바꾼다(링크도 함께).
- 관찰 3 — `adr init`이 만든 1번 ADR이 "우리는 ADR을 쓰기로 한다"는 결정 자체다.

### 실험: 6개월 뒤 "왜 2회지?"를 git으로 찾기

같은 설정 변경(`max-attempts=5` → `2`)을 (1) 커밋 메시지 "fix"로만, (2) ADR 파일과 함께 커밋한 두 저장소에서, 값이 들어온 커밋을 `git log -S`로 찾았다.

(실험, git 2.43.0, `scratchpad/sd/45/e47/why_demo.sh`, 2026-10-02 — 해시와 날짜는 실행마다 다르다. ADR 본문의 장애 날짜·수치는 예시)

```text
########## [no-adr] git log -S'max-attempts=2' --format='%h %ad %s' --date=short
6730ffe 2026-10-02 fix
## 그 커밋이 바꾼 파일
   src/application.properties | 2 +-
   1 file changed, 1 insertion(+), 1 deletion(-)
########## [with-adr] git log -S'max-attempts=2' --format='%h %ad %s' --date=short
5aa7bdb 2026-10-02 결제 재시도 5→2 (ADR-0004)
## 그 커밋이 바꾼 파일
   doc/adr/0004-payment-retry.md | 17 +++++++++++++++++
   src/application.properties    |  2 +-
   2 files changed, 18 insertions(+), 1 deletion(-)
## git grep -n 'ADR-\|max-attempts'
src/application.properties:1:payment.retry.max-attempts=2
```

- 기록이 없는 쪽은 "fix" 한 단어에서 끝난다. 이유·대안·재검토 조건은 커밋을 만든 사람의 기억에만 있다.
- ADR이 같은 커밋에 있으면 `git log -S` 한 번으로 맥락(장애 사후 검토)·결정·대가·재검토 조건까지 닿는다.
- 그래도 마지막 `git grep`에서 설정 줄 자체에는 ADR 표시가 없다. 값을 처음 보는 사람이 `git log -S`를 모르면 못 찾는다. 설정 옆에 `# ADR-0004` 주석 한 줄을 두면 길이 하나 더 생긴다(주석의 자리는 09).

### 3. 다른 형식 — MADR

```text
 Nygard                 MADR 4.0.0 (2024-09-17)
 ──────────            ───────────────────────────────────────
 Title                 # 제목 (해결한 문제와 찾은 해법을 대표)
 Status                (선택 메타데이터: status, date, decision-makers, consulted, informed)
 Context               ## Context and Problem Statement
                       ## Decision Drivers                       (전체판)
                       ## Considered Options                     ← 검토한 대안
 Decision              ## Decision Outcome  "Chosen option: …, because …"
 Consequences          ### Consequences  Good, because … / Bad, because …
                       ### Confirmation                          (전체판: 결정을 지키는지 확인하는 법)
                       ## Pros and Cons of the Options           (전체판)
```

- MADR(Markdown Architectural Decision Records)는 adr GitHub 조직의 템플릿이다. Nygard 형식에 없는 **검토한 대안**과 **확인 방법(Confirmation)**이 들어 있다.
- Thoughtworks Technology Radar는 "Lightweight Architecture Decision Records"를 2017-11과 2018-05에 Adopt로 올렸고, 위키·웹사이트 대신 **소스 관리에 두라**고 권한다. 코드와 동기화된 기록이 되기 때문이라고 적는다.

## 쓰이는 자료구조·알고리즘

- **추가 전용 로그(append-only log)** — 번호는 단조 증가하고 재사용하지 않으며, 바뀐 결정도 지우지 않고 새 항목을 덧붙인다. 이벤트 소싱과 같은 모양이다([distributed/22-event-sourcing](../../distributed/22-event-sourcing/2-summary.md)).
- **방향 그래프(대체 사슬)** — `Supercedes` 간선. "지금 유효한 결정"은 들어오는 대체 간선이 없는 노드다. `adr generate graph`가 Graphviz `digraph`로 출력한다.
- **문자열 검색 인덱스로서의 git** — `git log -S`(pickaxe)는 어떤 문자열의 등장 횟수를 바꾼 커밋을 찾는다. ADR이 그 커밋에 있으면 검색 한 번으로 이유에 닿는다.
- **slug 생성** — 제목 → 파일 이름. 문자 집합 처리가 바이트 단위면 비ASCII 제목이 사라진다(실험 관찰 2).

## 적용 — 풀어나가는 법

### 1. 순서

1. **첫 ADR은 "ADR을 쓰기로 한다"**(adr-tools `init`이 만드는 1번과 같다). 위치(`doc/adr/`)와 형식(Nygard·MADR)을 정한다.
2. **언제 쓰나**: 되돌리기 어려운 결정(데이터 모델·서비스 경계·공개 API·저장소 종류), 품질 속성을 맞교환한 결정(46), 팀이 두 번 이상 논쟁한 결정.
3. **결정과 같은 PR에 넣는다.** 코드 리뷰가 ADR 리뷰가 된다. 상태는 `proposed`로 올리고 합의되면 `accepted`.
4. **결과에 나쁜 것과 재검토 조건을 적는다.** "PG가 멱등 키를 지원하면 다시 본다" 같은 조건이 있으면 나중에 뒤집을 때를 안다.
5. **뒤집을 때는 새 ADR + supersede.** 옛 파일을 고쳐 쓰지 않는다.
6. **코드에서 ADR로 가는 길을 만든다.** 커밋 메시지에 `ADR-0004`, 놀라운 설정 옆에 주석 한 줄.

### 2. 예시 ADR (Nygard 형식)

```markdown
# 4. payment-retry: 결제 재시도는 최대 2회, 지수 백오프와 지터

## Status

Accepted. Supercedes ADR 2 (0002-payment-retry-default.md)

## Context

PG 장애 때 재시도 5회 × 인스턴스 20대로 PG 요청이 평소의 몇 배가 되어 회복이 늦었다(예시).
라이브러리 기본값은 우리 부하 형태를 고려하지 않는다.

## Decision

We will 결제 재시도를 최대 2회로 하고, 지수 백오프와 전체 지터를 쓴다.
재시도 예산은 전체 요청의 10%로 제한한다.

## Consequences

- 좋음: PG 장애 때 우리가 만드는 추가 부하가 상한을 갖는다.
- 나쁨: 순간 오류에 대한 성공률이 조금 낮아진다. 일부 결제는 사용자가 다시 눌러야 한다.
- 재검토 조건: PG가 멱등 키를 지원하면 횟수를 다시 본다.
```

### 3. 진단·점검 스크립트

```bash
# 대체됐다고 표시됐는데 상대편에 역링크가 없는 ADR 찾기 (adr-tools 철자 기준)
for f in doc/adr/[0-9]*.md; do
  n=$(sed -n 's/^Superceded by \[\([0-9]*\)\..*/\1/p' "$f")
  [ -z "$n" ] && continue
  me=$(basename "$f" | cut -d- -f1 | sed 's/^0*//')
  t=$(ls doc/adr/$(printf '%04d' "$n")-*.md)
  grep -q "^Supercedes \[$me\." "$t" || echo "역링크 없음: $f -> $t"
done
# 지난 90일 동안 설정 파일을 바꾼 커밋 중 메시지에 ADR 번호가 없는 것
git log --since=90.days --format='%h %s' -- '*.properties' '*.yml' | grep -v 'ADR-'
```

(실험 저장소에서 점검, 2026-10-02 — `scratchpad/sd/45/e47/check_links.sh`)

```text
== 정상
== 0004의 역링크를 지운 뒤
역링크 없음: doc/adr/0002-.md -> doc/adr/0004-2.md
```

## 장애 시나리오와 대처

### 1. 결정 근거 소실 → 같은 논쟁 반복 (⚠ 커리큘럼)

- 현상: 분기마다 "왜 공유 DB를 안 쓰나", "왜 이 캐시를 두나"를 처음부터 다시 논쟁한다.
- 보이는 형태: 같은 주제의 회의·슬랙 스레드가 반복된다. 결론은 매번 사람 기억에 기대고, 그 사람이 떠나면 결론이 바뀐다.
- 원인: 결정·맥락·대안이 남아 있지 않다. 실험에서 기록이 없는 저장소는 `git log -S`가 "fix"에서 끝났다.
- 대처: 반복된 논쟁부터 ADR로 쓴다. 다음 논쟁은 "그 ADR의 맥락이 바뀌었나"부터 묻는다.

### 2. 반대 결정으로 회귀 (⚠ 커리큘럼)

- 현상: 재시도를 5회에서 2회로 줄인 이유를 모르는 사람이 "성공률을 올리자"며 다시 5회로 올린다. 다음 PG 장애 때 예전 장애가 재현된다.
- 보이는 형태: 같은 설정 값이 커밋 이력에서 왔다 갔다 한다(`git log -S`로 같은 값의 추가·삭제가 반복). 사후 검토에 "예전에도 있었던 문제".
- 원인: 결정이 무엇을 막고 있었는지(결과 중 나쁜 것, 지키던 비기능 요구)가 보이지 않았다.
- 대처: ADR 결과 절에 막고 있는 위험을 적는다. 설정 옆 주석·커밋 메시지로 ADR에 연결한다. 그 값을 지키는 테스트를 둔다(46의 시나리오 테스트).

### 3. ADR이 위키에 있어 코드와 어긋난다

- 현상: 위키의 결정 문서는 "Kafka 사용"인데 코드는 이미 SQS로 바뀌었다.
- 보이는 형태: 문서 수정일이 코드 변경보다 한참 오래됐다. 문서 링크가 깨져 있다.
- 원인: 결정과 코드가 다른 곳에서 다른 리뷰 과정을 거친다.
- 대처: 저장소 안 `doc/adr/`에 두고 코드와 같은 PR로 바꾼다(Thoughtworks Radar 권고).

### 4. 옛 ADR을 고쳐 써서 이력이 사라진다

- 현상: 2번 ADR의 결정 문장을 새 결정으로 덮어썼다. "언제부터, 왜 바뀌었나"가 사라졌다.
- 보이는 형태: ADR 파일의 `git log`에 큰 수정이 있고, 대체 링크가 없다.
- 원인: ADR을 "현재 상태 문서"로 다뤘다.
- 대처: 새 번호로 쓰고 옛 것은 `Superceded by`로 표시한다(`adr new -s N`). 위 점검 스크립트로 역링크 누락을 찾는다.

### 5. 파일 이름이 비어 무슨 결정인지 알 수 없다

- 현상: `doc/adr/0002-.md`, `0004-2.md` 같은 파일이 생긴다.
- 보이는 형태: 파일 목록만 보고는 결정을 찾을 수 없다. 검색도 제목 본문을 뒤져야 한다.
- 원인: adr-tools의 slug 생성(`tr -Ccs [:alnum:] -`)이 바이트 단위라 한글이 빠진다(실험 관찰 2).
- 대처: 제목 앞에 영문 키워드를 넣거나(`payment-retry: …`), 만든 뒤 파일 이름을 바꾸고 링크를 고친다.

## 핵심 문장

- 코드는 무엇을 하는지 보여 주고, ADR은 왜 그렇게 했는지를 남긴다. 기록이 없으면 맹목적으로 따르거나 맹목적으로 바꾸는 수밖에 없다.
- Nygard 형식은 제목·상태·맥락·결정·결과 다섯 부분이고, 결과에는 좋은 것만이 아니라 모든 결과를 적는다.
- 번호는 재사용하지 않고, 뒤집힌 결정은 지우지 않고 superseded로 표시한다. 추가 전용 로그다.
- ADR은 코드 저장소 안에 두고 결정과 같은 커밋에 넣는다. 실험에서 그렇게 한 저장소는 `git log -S` 한 번으로 이유에 닿았고, 기록 없는 저장소는 "fix"에서 끝났다.
- adr-tools는 한글 제목을 파일 이름에서 지운다. 제목에 영문 키워드를 함께 둔다.

## 관련 주제·근거

- 선행
  - [46-quality-attributes-and-tradeoffs](../46-quality-attributes-and-tradeoffs/2-summary.md) — ADR이 남기는 결정의 대부분은 품질 속성 맞교환이다
- 원본·연결
  - [engineering/engineering-axes/maintainability.md](../../engineering/engineering-axes/maintainability.md) — 「⑥ 문서화」: 남길 것은 "왜"·버린 대안·제약·함정, ADR 네 칸
  - [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md) — 코드 옆 "왜" 주석의 자리
  - [48-configuration-and-12factor](../48-configuration-and-12factor/2-summary.md) — 설정 값의 이유를 어디에 남기나
  - [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md) — 사후 검토가 ADR의 맥락이 된다
- 글·문서
  - Michael Nygard, "Documenting Architecture Decisions", Cognitect 블로그, 2011-11-15 <https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
  - adr GitHub 조직 홈 — AD·ASR·ADR·decision log 정의 <https://adr.github.io/> · MADR 4.0.0 템플릿 <https://github.com/adr/madr/tree/4.0.0/template>
  - Thoughtworks Technology Radar, "Lightweight Architecture Decision Records"(Adopt, 2017-11·2018-05) <https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records>
  - Nat Pryce, adr-tools 소스 `src/adr-new`(slug 103행, 대체 링크 117·119행), `src/init.md` <https://github.com/npryce/adr-tools>
- 실험 목록
  - adr-tools로 init·new·`-s` 대체·toc·graph, 한글 slug 소실 — `scratchpad/sd/45/e47/adr_demo.sh`, adr-tools `b3279ba`, GNU coreutils 9.4
  - "왜 2회지?" — 기록 없음 vs ADR 동반 커밋의 `git log -S` — `scratchpad/sd/45/e47/why_demo.sh`, git 2.43.0
