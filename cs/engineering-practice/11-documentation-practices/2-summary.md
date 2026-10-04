# engineering-practice/11-documentation-practices — 문서 실천: 네 유형(Diátaxis), 문서를 코드처럼, 신선도 — 정리 (힌트)

## 해결하는 문제

문서가 없으면 아는 사람에게 묻는다. 그 사람이 휴가 중이거나 퇴사했으면 멈춘다. 그런데 **틀린 문서는 없는 문서보다 나쁠 수 있다.** 권위 있어 보이는 채로 사람을 잘못된 행동으로 이끈다.

- SWE@G 10장 "Deprecating Documents": 주인 없는 문서라도 누군가 "이건 더는 안 됩니다!"라고 적어 두는 편이, 아무 말 없이 권위 있어 보이는 문서를 남겨 두는 것보다 도움이 된다.

쉬운 예: 요리에 관한 글이다. Diátaxis가 드는 비유를 그대로 옮긴다.

```text
  아이에게 요리를 가르친다      →  튜토리얼   "같이 해 보자"
  요리책의 레시피               →  방법 가이드 "이렇게 하면 된다"
  식품 포장 뒷면의 성분 표시     →  레퍼런스   "이것은 무엇이다"
  요리의 사회사를 다룬 글        →  설명      "왜 이렇게 되었나"
```

- 넷 다 "요리 문서"지만 읽는 사람의 필요가 다르다. 레시피 중간에 요리의 역사를 늘어놓으면 레시피로도 역사로도 못 쓴다.

똑같은 구조다. 개발 문서도 "배우려는 사람"과 "지금 일을 끝내려는 사람"과 "사실을 찾는 사람"과 "이해하려는 사람"이 다르다.

실무 예:
- 새벽 장애 때 런북의 명령을 그대로 쳤더니 `unknown option: --promote`가 나온다. 석 달 전에 옵션 이름이 바뀌었는데 런북은 그대로였다(장애 1, 아래 실험).
- 위키에 Borg 설정(setting up) 문서가 7~10개 있고 몇 개만 관리된다(SWE@G 10장의 GooWiki 사례). 어느 것이 맞는지 모른다(장애 3).

## 동작·원리

### 1. 네 유형 — Diátaxis 지도

```text
                         행동(action)을 이끈다
                                 ▲
                  튜토리얼        │       방법 가이드
                 (배움 중심)      │      (목표 중심)
   기술 습득 ◄────────────────────┼────────────────────► 기술 적용
  (acquisition, 공부)             │                   (application, 일)
                  설명            │       레퍼런스
                 (이해 중심)      │      (정보 중심)
                                 ▼
                         인지(cognition)를 돕는다
```

- *Diátaxis*: 기술 문서를 사용자의 필요 네 가지와 그에 맞는 문서 형식 네 가지로 나누는 체계(diataxis.fr). 이름은 그리스어 dia("가로질러") + taxis("배열")다.
- diataxis.fr "The map"의 표

| | 튜토리얼 | 방법 가이드 | 레퍼런스 | 설명 |
|---|---|---|---|---|
| 하는 일 | 소개·교육·이끎 | 안내 | 진술·기술·정보 | 설명·명료화·논의 |
| 답하는 질문 | "…하는 법을 가르쳐 줄래?" | "…는 어떻게 하지?" | "…는 무엇이지?" | "왜…?" |
| 지향 | 배움 | 목표 | 정보 | 이해 |
| 형식 | 수업 | 단계 나열 | 건조한 기술 | 논의형 설명 |

- *튜토리얼(tutorial)*: 배우는 사람이 해 보면서 익히게 하는 수업.
- *방법 가이드(how-to guide)*: 이미 아는 사람이 특정 목표를 이루게 하는 단계. 런북은 대개 이 유형이다.
- *레퍼런스(reference)*: 기계(API·설정·명령)를 있는 그대로 기술한 것.
- *설명(explanation)*: 배경·이유·설계 판단을 풀어 쓴 것.
  - 흔한 오해: "튜토리얼 = 방법 가이드". 둘 다 단계가 있어서 섞인다. diataxis.fr은 이 둘이 서로 무너져 합쳐지는 것을 "최악의 경우"로 든다. 튜토리얼은 배우는 사람의 경험이 목적이고, 방법 가이드는 일하는 사람의 목표 달성이 목적이다.

### 2. 나침반 — 두 질문으로 유형을 정한다

diataxis.fr "The compass"의 진리표다.

| 내용이 … | 사용자의 … 에 쓰이면 | 유형 |
|---|---|---|
| 행동을 알려 준다 | 기술 습득 | 튜토리얼 |
| 행동을 알려 준다 | 기술 적용 | 방법 가이드 |
| 인지를 알려 준다 | 기술 적용 | 레퍼런스 |
| 인지를 알려 준다 | 기술 습득 | 설명 |

- 질문 두 개면 된다: **행동인가 인지인가? 습득인가 적용인가?**
- 문서 전체에도, 문단·문장 하나에도 쓴다. "이 문단은 지금 이 문서의 유형에 맞나?"

### 3. 섞이면 무너진다

```text
  한 페이지에 다 넣은 위키                  유형별로 나눈 문서
  ┌──────────────────────────────┐         [튜토리얼] 처음 시작하기
  │ 링크 수십 개(일부 깨짐)        │         [방법]   DB 장애 조치
  │ 시스템 동작 개념 설명          │   ──>   [레퍼런스] 설정 키 목록
  │ API 레퍼런스                  │         [설명]   DB 구성과 그 이유
  │ 설치 단계 · 장애 대응 단계      │         + 서로 링크
  └──────────────────────────────┘
  화면 수십 장을 스크롤 — 아무도 끝까지 안 읽음
```

- SWE@G 10장 "Documentation Types": 문서는 대개 **목적이 하나**여야 한다. 초기 Google 팀 위키의 거대한 페이지(링크·개념·API 레퍼런스가 섞임)는 목적이 하나가 아니어서 실패했다고 쓴다.
- SWE@G의 유형 목록은 Diátaxis와 다르다: 레퍼런스(코드 주석 포함), 설계 문서, 튜토리얼, 개념 문서, 랜딩 페이지. 설계 문서는 설명과 결정 기록의 성격을 함께 갖는다. 결정 기록 형식은 [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md).
- SWE@G 10장 "The Parameters of Good Documentation": 좋은 문서의 세 측면은 완전성·정확성·명료성이고, 한 문서에서 셋을 다 얻기는 드물다. 레퍼런스는 완전성을 위해 명료성을 조금 잃을 수 있다. API 문서에 설계 결정을 섞지 말고 설계 문서로 보내라고 쓴다.

### 4. 문서를 코드처럼 — SWE@G 10장

SWE@G 10장 "Documentation Is Like Code"는 문서가 다음을 갖춰야 한다고 쓴다(Google의 관례이자 저자들의 주장).

1. 따라야 할 내부 정책·규칙
2. 소스 관리 아래에 둔다
3. 유지 책임이 있는 분명한 소유자
4. 변경 리뷰(그리고 문서가 기술하는 코드와 **함께** 바뀜)
5. 이슈를 버그처럼 추적
6. 주기적 평가(어떤 의미에서 테스트)
7. 가능하면 정확성·신선도 같은 측면을 측정 — 책은 "도구가 아직 따라오지 못했다"고 쓴다

- GooWiki 사례: 주인이 없으니 많은 문서가 낡았다. 중복 문서가 생겼다. 위키를 폐기할 때 문서의 약 90%가 직전 몇 달간 조회·수정이 없었다(10장 각주 3).
- 중요한 문서를 코드와 같은 소스 관리로 옮기자 소유자·정본 위치·버그 처리 과정이 생겼고 문서가 "극적으로" 나아졌다고 쓴다. Google은 API마다 `g3doc` 디렉터리에 Markdown 문서를 둔다.
- 리뷰 세 종류(10장 "Documentation Reviews"): 정확성을 보는 **기술 리뷰**(전문가), 명료성을 보는 **독자 리뷰**(그 분야를 모르는 사람), 일관성을 보는 **글쓰기 리뷰**(테크니컬 라이터 등).

### 5. 신선도 — 날짜와 소유자

```text
  # Document freshness: For more information, see go/fresh-source.
  freshness: { owner: `username` reviewed: '2019-02-27' }
```

- SWE@G 10장 "Deprecating Documents": Google은 문서에 **신선도 날짜**를 붙인다. 마지막 검토일을 적고, 예를 들어 석 달간 손대지 않으면 메타데이터가 알림 메일을 보낸다(위가 책의 예시).
- 소유자는 날짜를 최신으로 유지할 동기가 생긴다. 소스 관리 아래라면 날짜 갱신도 코드 리뷰를 거친다. 책은 이것을 "적은 비용으로 문서를 가끔 들여다보게 하는 방법"이라 쓴다.
- 쓸모없어진 문서는 지우거나 낡았다고 표시하고, 새 정보가 있는 곳을 가리킨다.
- *문서 신선도(freshness)*: 문서 내용이 지금의 시스템과 맞는 정도. 마지막 검토일은 그 **대리값**이다.
  - 흔한 오해: "검토일이 최근이면 문서가 맞다". 날짜는 사람이 바꾼다. 아래 실험에서 날짜만 올리자 날짜 기반 검사 두 개가 조용해졌고, 내용 기반 검사는 그대로 문제를 잡았다.

### 실험: 문서 신선도 점검기 — 날짜 검사와 내용 검사

**시뮬레이션 이력이다.** 일회용 저장소에 문서 3개(설명·방법·튜토리얼)와 스크립트·설정을 두고, 6월에 코드만 바꿨다.

```text
  2026-03-02  런북 작성: `failover.sh --promote`, 설정 키 db.replica.host, 링크 ./old-dashboard.md(없는 파일)
  2026-06-10  코드 변경: --promote → --promote-replica, db.replica → db.replicas(목록)   ← 런북은 그대로
  2026-09-20  튜토리얼 작성
  2026-10-05  점검 (검토 경과 상한 90일 — SWE@G 예시의 석 달)
```

점검기 핵심(`docs-check.js`, Node 18). 다섯 가지를 본다.

```js
const lastChange = f => git('log', '-1', '--format=%cs', '--', f);   // 그 파일을 마지막으로 바꾼 커밋 날짜
// 1) 상대 링크가 가리키는 파일이 있나
for (const [, href] of text.matchAll(/\]\((\.[^)#]+)\)/g))
  if (!fs.existsSync(path.join(repo, 'docs', href))) report('링크', rel, `${href} 없음`);
// 2) reviewed 메타데이터가 상한보다 오래됐나
if (days(reviewed, today) > maxDays) report('검토일', rel, `${reviewed} 검토 → ${days(reviewed, today)}일 경과`);
// 3) 문서가 가리키는 코드 파일이 문서보다 나중에 바뀌었나
if (lastChange(r) > lastChange(rel)) report('뒤처짐', rel, `${r} 가 ${lastChange(r)}에 바뀜`);
// 4) 문서 속 명령의 옵션이 지금 스크립트에 있나
if (!new RegExp(`(^|[\\s|(])${flag}\\)`, 'm').test(src)) report('옵션', rel, `${script} 에 ${flag} 처리 분기 없음`);
// 5) 문서 속 설정 키가 지금 설정 파일(YAML 들여쓰기 구조)에 있나
if (!yamlHas('config/application.yml', key)) report('설정키', rel, `${key} 가 config/application.yml 에 없음`);
```

(실험, git 2.43.0 / Node 18.19.1, 2026-10-05 — 입력 고정)

```text
== docs/architecture.md (문서 마지막 수정 2026-03-02)
  검토일    docs/architecture.md: reviewed 메타데이터 없음
== docs/runbook-db-failover.md (문서 마지막 수정 2026-03-02)
  링크     docs/runbook-db-failover.md: ./old-dashboard.md 없음
  검토일    docs/runbook-db-failover.md: 2026-03-02 검토 → 217일 경과 (> 90)
  뒤처짐    docs/runbook-db-failover.md: config/application.yml 가 2026-06-10에 바뀜 (문서는 2026-03-02)
  뒤처짐    docs/runbook-db-failover.md: scripts/failover.sh 가 2026-06-10에 바뀜 (문서는 2026-03-02)
  옵션     docs/runbook-db-failover.md: scripts/failover.sh 에 --promote 처리 분기 없음
  설정키    docs/runbook-db-failover.md: db.replica.host 가 config/application.yml 에 없음
== docs/tutorial-getting-started.md (문서 마지막 수정 2026-09-20)
문제 7건
exit=1
unknown option: --promote
exit=2
```

- 마지막 두 줄은 런북의 명령 `sh scripts/failover.sh --promote`를 그대로 실행한 결과다. 사고 때 이 문서를 따르면 첫 단계에서 막힌다.
- 튜토리얼은 `config/application.yml`을 가리키지만 문서(09-20)가 코드 변경(06-10)보다 나중이라 "뒤처짐"이 아니다.

이어서 **게이밍**: 런북 내용은 그대로 두고 `reviewed`만 2026-10-01로 올려 커밋한 뒤 다시 점검했다.

(실험, 같은 환경)

```text
== docs/architecture.md (문서 마지막 수정 2026-03-02)
  검토일    docs/architecture.md: reviewed 메타데이터 없음
== docs/runbook-db-failover.md (문서 마지막 수정 2026-10-01)
  링크     docs/runbook-db-failover.md: ./old-dashboard.md 없음
  옵션     docs/runbook-db-failover.md: scripts/failover.sh 에 --promote 처리 분기 없음
  설정키    docs/runbook-db-failover.md: db.replica.host 가 config/application.yml 에 없음
== docs/tutorial-getting-started.md (문서 마지막 수정 2026-09-20)
문제 4건
```

- 관찰 1: 날짜 기반 검사 두 개(검토일, 뒤처짐)가 사라졌다. 날짜 커밋이 문서의 "마지막 수정일"까지 올렸기 때문이다.
- 관찰 2: 내용 기반 검사 세 개(링크, 옵션, 설정키)는 그대로 잡았다. 문서가 가리키는 대상이 **지금 실제로 있는지**를 보기 때문이다.
- 해석: 날짜는 "누가 봐야 할 때가 됐다"는 알림으로 쓰고, 맞는지의 판정은 내용 검사로 한다. "뒤처짐"은 휴리스틱이다. 코드가 바뀌어도 문서와 무관한 변경일 수 있다(거짓 양성).
- 한계: 설정 키 검사는 들여쓰기만 보는 단순 YAML 검사다. 목록·따옴표 키는 다루지 않는다. 운영 DB에 확인 SQL을 실제로 돌려 보는 런북 점검기는 [reliability/44-runbooks-and-operational-readiness](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) 4절에 있다.

## 쓰이는 자료구조·알고리즘

- **링크 그래프** — 문서는 노드, 링크는 간선이다. 깨진 링크 = 없는 노드를 가리키는 간선. 랜딩 페이지에서 BFS로 닿지 않는 문서 = 고아 문서(이 노트의 실험은 깨진 링크만 검사했다).
- **의존 간선 + 타임스탬프 비교** — 문서 → 코드 파일 간선을 만들고, 대상의 마지막 변경일이 문서보다 늦으면 표시한다. 빌드 시스템이 "입력이 산출물보다 새로우면 다시 만든다"고 판단하는 것과 같은 모양이다([07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md)).
- **트리 경로 탐색** — 설정 키 `db.replica.host`를 YAML 트리의 경로로 보고 한 단계씩 내려간다.
- **2비트 진리표** — Diátaxis 나침반은 (행동/인지) × (습득/적용) 두 비트로 네 유형을 고른다.

## 적용 — 풀어나가는 법

### 1. 새 문서를 쓸 때

1. 나침반의 두 질문으로 유형을 하나 고른다. 둘 이상이면 문서를 나누고 서로 링크한다.
2. 독자를 정한다(SWE@G 10장 "Know Your Audience").
3. 위치: 기술하는 코드와 같은 저장소, 가능하면 같은 디렉터리(SWE@G의 `g3doc` 관례).
4. 머리에 소유자와 검토일을 적는다.

```markdown
---
owner: team-db
reviewed: 2026-10-05
---
# DB 장애 조치 (방법 가이드)
```

5. 리뷰를 받는다. 최소한 기술 리뷰(정확성) 하나. 중요한 문서는 독자 리뷰(그 분야를 모르는 사람)도.

### 2. CI에서 문서를 검사한다

```yaml
# (예시, GitLab CI) 문서 점검 잡 — 내용 검사는 실패로, 날짜 검사는 경고로
# 점검기에 검사 종류를 고르는 --only 옵션이 있다고 가정했다.
# 실험의 docs-check.js에는 이 옵션이 없다 — 날짜 경고까지 합쳐 문제가 하나라도 있으면 exit 1이다.
docs-content:
  script:
    - node tools/docs-check.js . "$(date -u +%F)" 90 --only=link,option,config-key
docs-dates:
  allow_failure: true   # 실패해도 파이프라인은 성공, 잡에 경고 표시(GitLab 문서)
  script:
    - node tools/docs-check.js . "$(date -u +%F)" 90 --only=reviewed,stale
```

- 링크·옵션·설정 키 같은 **내용 검사**는 머지를 막는다.
- 검토일 경과는 소유자에게 알림만 보낸다. 날짜만 올리는 게이밍을 부르지 않게 한다.
- 코드 PR이 문서가 가리키는 파일을 바꾸면 그 문서 소유자를 리뷰어로 붙인다(SWE@G: 문서는 기술하는 코드와 함께 바뀐다).

### 3. 런북(방법 가이드)은 실행할 수 있게

- 명령은 복사해서 그대로 실행되는 형태로 쓴다. 그래야 기계가 검사할 수 있다.
- 완화 명령에는 대상 재확인이나 `--dry-run`류 단계를 붙인다. 런북 운영 전체는 [reliability/44](../../reliability/44-runbooks-and-operational-readiness/2-summary.md).

### 4. 쓸모없어진 문서

- 지우거나, 맨 위에 "더는 맞지 않음 — 새 문서: …"를 적는다(SWE@G 10장).
- 같은 주제 문서가 여럿이면 정본 하나를 정하고 나머지는 정본으로 합치거나 폐기한다.

## 장애 시나리오와 대처

### 1. 낡은 런북 → 사고 때 잘못된 절차 실행 (⚠ 커리큘럼)

- 현상: 새벽 DB 장애. 런북대로 승격 명령을 쳤는데 실패한다. 다음 단계의 설정 키도 지금 설정에 없다.
- 보이는 형태: `unknown option: --promote`, 종료 코드 2(실험). 확인 단계에서 존재하지 않는 키·대시보드 링크.
- 원인: 코드는 6월에 바뀌었고 런북은 3월 그대로였다. 문서가 코드와 함께 리뷰되지 않았다.
- 대처
  - 사고 중: 런북이 틀렸다고 판단되면 그 자리에서 멈추고 에스컬레이션한다. 추측으로 비슷한 옵션을 시도하지 않는다.
  - 사고 후: 런북을 고치고, 내용 검사(옵션·설정 키·링크)를 CI에 넣는다. 런북이 가리키는 파일이 바뀌면 소유자를 리뷰어로 붙인다.
  - 낡은 문서가 장애 때 잘못된 판단을 부르는 것은 코드 주석에서도 같다([software-design/09-comments-and-conventions](../../software-design/09-comments-and-conventions/2-summary.md) 실험 B).

### 2. 튜토리얼과 방법 가이드가 섞임

- 현상: 신입은 "시작하기" 문서 중간의 운영 옵션에서 길을 잃는다. 숙련자는 필요한 한 단계를 찾으려고 긴 설명을 스크롤한다.
- 원인: 배움(습득)과 일(적용)을 한 문서에 담았다. diataxis.fr은 이 둘이 무너져 합쳐지는 것을 최악의 경우로 든다.
- 대처: 나침반 질문으로 문단마다 유형을 판정해 나눈다. 튜토리얼은 한 길로만 끝까지 데려가고, 방법 가이드는 목표·단계만 둔다.

### 3. 같은 주제 문서가 여러 벌 → 어느 것이 맞나

- 현상: "배포 방법" 문서가 위키에 셋, 저장소에 하나. 내용이 서로 다르다.
- 원인: 소유자와 정본 위치가 없다. SWE@G의 GooWiki에서 Borg 설정 문서가 7~10개였던 상황이다.
- 대처: 정본 하나를 정해 코드 옆에 두고 나머지는 정본으로 합치거나 폐기 표시한다(SWE@G "canonical documentation").

### 4. 소유자 없는 위키 → 대부분 방치

- 현상: 검색 결과 상위 문서가 3년 전 것이다.
- 보이는 형태: 조회·수정이 없는 문서가 대부분이다. GooWiki 폐기 때 약 90%가 직전 몇 달간 조회·수정이 없었다(SWE@G 10장 각주).
- 대처: 문서마다 소유자와 검토일을 적고, 소스 관리·리뷰 흐름에 넣는다. 오래 조회가 없는 문서는 폐기 후보로 본다.

### 5. 검토일만 올리는 게이밍

- 현상: 신선도 대시보드는 초록인데 런북은 여전히 틀리다.
- 보이는 형태: 실험에서 날짜만 올리자 검토일·뒤처짐 경고가 사라졌다(7건 → 4건). 옵션·설정 키·링크 문제는 그대로였다.
- 원인: 날짜는 사람이 바꾸는 대리값이다. 날짜를 목표로 걸면 날짜만 바뀐다(굿하트 — [09-dora-metrics](../09-dora-metrics/2-summary.md)).
- 대처: 날짜는 알림, 판정은 내용 검사로 한다(적용 2). 검토 커밋에 "무엇을 확인했는지"를 적게 한다.

## 핵심 문장

- 문서는 네 유형이다: 튜토리얼(배움)·방법 가이드(목표)·레퍼런스(정보)·설명(이해). 나침반 두 질문(행동/인지, 습득/적용)으로 고른다(Diátaxis).
- 한 문서에는 목적 하나(SWE@G 10장). 튜토리얼과 방법 가이드가 섞이면 둘 다 못 쓴다.
- 문서를 코드처럼 다룬다: 소스 관리, 소유자, 리뷰, 이슈 추적, 주기적 평가. 문서는 기술하는 코드와 함께 바뀐다.
- 틀린 문서는 없는 문서보다 나쁠 수 있다. 실험의 낡은 런북 명령은 `unknown option: --promote`로 첫 단계에서 막혔다.
- 검토일은 신선도의 대리값이다. 날짜만 올리면 날짜 검사는 조용해지고, 링크·옵션·설정 키 같은 내용 검사만 문제를 잡는다.

## 관련 주제·근거

- 선행
  - [02-requirements-engineering](../02-requirements-engineering/2-summary.md) — 문서로 남길 요구
- 후속·연결
  - [reliability/44-runbooks-and-operational-readiness](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) — 런북 구조와 확인 SQL 실행 점검기
  - [software-design/09-comments-and-conventions](../../software-design/09-comments-and-conventions/2-summary.md) — 코드 안의 문서(주석)와 낡음
  - [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md) — 설계 결정 기록
  - [10-technical-debt](../10-technical-debt/2-summary.md) — 낡은 문서도 이자를 낸다
  - [09-dora-metrics](../09-dora-metrics/2-summary.md) — 대리 지표의 게이밍
  - [19-practice-symptom-index](../19-practice-symptom-index/2-summary.md)("이건 왜 이렇게 했지?")
- 글·문서
  - Diátaxis <https://diataxis.fr/> — 네 유형, "The map"(표·비유·Blur), "The compass"(진리표) <https://diataxis.fr/map/> · <https://diataxis.fr/compass/>
  - Winters·Manshreck·Wright, 『Software Engineering at Google』 10장 "Documentation"(온라인판) — Documentation Is Like Code(7항목), GooWiki 사례(각주 3: 약 90%), Documentation Types, Documentation Reviews(3종), Parameters of Good Documentation, Deprecating Documents(신선도 날짜·석 달 알림) <https://abseil.io/resources/swe-book/html/ch10.html>
- 실험 목록
  - 신선도 점검 — `scratchpad/ep/09/docs/gen.sh`(저장소 생성), `docs-check.js`(점검기), `run.sh`(점검 + 런북 명령 실행). git 2.43.0, Node 18.19.1. 출력 `out.txt`.
  - 검토일 게이밍 — `scratchpad/ep/09/docs/bump.sh`(reviewed만 올려 커밋 후 재점검). 출력 `bump-out.txt`.
