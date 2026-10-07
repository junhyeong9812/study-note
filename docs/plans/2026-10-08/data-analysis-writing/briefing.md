# 집필 브리핑 — 커리큘럼 leaf 새 노트 (데이터 분석·통계, 2026-10-08)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」(2026-10-01 머리말 정리 반영판).
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/math/08-expectation-variance-tails/`, `cs/data-engineering/10-data-quality-and-data-observability/`

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §18 데이터 분석·통계 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §18 머리 문단(데이터 출처 → 요약 → 추론 → 관계·모델 → 실험 → 실무, **확률·분포 기초는 math/07~09가 단일 출처 — 반복하지 않고 링크**)도 읽는다.
- **이 영역의 목표**: 백엔드 개발자가 "숫자로 판단할 때 어떻게 틀리는지"로 배운다. 각 편은 ⚠ 칸의 증상(평균만 보고 p99를 놓침·표본 편향·p-해킹·A/B 비율 틀어짐·합계가 안 맞음·부분군 반전·날짜 경계)에서 출발해 통계 원리로 내려갔다가, 코드·SQL로 확인하는 법으로 돌아온다.
- **원고 없음** — 28편 모두 신규. 커리큘럼 '기존' 칸의 연결 노트(domain-modeling/advanced/27-ab-assign, languages/sql/syntax/26~33, data-engineering/10)는 읽고 링크한다.
- **겹치는 기존 노트(먼저 읽고 링크, 되풀이하지 않는다)**: `cs/math/{07-probability-and-bayes,08-expectation-variance-tails,09-common-distributions,10-queueing-and-littles-law,13-linear-algebra-essentials,15-numerical-stability}`(분포·기댓값·선형대수 — 여기서 다시 설명하지 않는다), `cs/database/05-window-functions-and-cte`·`04-sql-joins-and-aggregation`·`27-temporal-types-and-session-timezone`, `cs/data-engineering/{03-dimensional-modeling,10-data-quality-and-data-observability,17-de-incidents}`(PHE 사건은 17이 파이프라인 관점 — 28은 분석 관점), `cs/reliability/` 지표·SLO·백분위 노트(ls로), `cs/data-structure/`(스케치·힙 — 대응표 `cs/data-structure/curriculum.md`), `cs/algorithm/`(선택 알고리즘 — 대응표 `cs/algorithm/curriculum.md`). 다른 영역 노트가 data-analysis를 "미작성"으로 가리키는 곳은 packet에 보고(정합 단계에서 링크 교정).
- **근거와 열 수 있는 1차 출처(검색 한도 대비 — 주소를 알고 curl/WebFetch로 직접 연다)**:
  - OpenIntro Statistics 4판(무료 PDF): https://www.openintro.org/book/os/ — 장·절 번호는 이 PDF 목차로 확인(커리큘럼이 OpenIntro 절 번호를 지정했으면 그대로 맞는지 확인)
  - Kohavi·Tang·Xu 『Trustworthy Online Controlled Experiments』(2020) — 본문은 열 수 없다. 장 번호는 열 수 있는 목차(출판사 Cambridge 페이지·저자 사이트 https://experimentguide.com/)로만, 아니면 `[?]`
  - Fabijan 외 KDD 2019 "Diagnosing Sample Ratio Mismatch" (Microsoft Research 페이지·PDF)
  - Ioannidis 2005 PLoS Med "Why Most Published Research Findings Are False" https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124
  - Benjamini–Hochberg 1995 (JRSS B — 열 수 있는 사본이 없으면 서지 `[?]`)
  - Dunning–Ertl t-digest(arXiv 1902.04023) https://arxiv.org/abs/1902.04023 · HdrHistogram https://hdrhistogram.github.io/HdrHistogram/
  - Wickham "Tidy Data" 2014 JSS https://www.jstatsoft.org/article/view/v059i10
  - Wilke 『Fundamentals of Data Visualization』 온라인판 https://clauswilke.com/dataviz/
  - Hyndman–Athanasopoulos 『Forecasting: Principles and Practice』 3판 온라인 https://otexts.com/fpp3/
  - Wilson 외 2017 "Good Enough Practices in Scientific Computing" PLoS Comput Biol https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005510
  - Downey 『Think Stats』 2판·『Think Bayes』 온라인 https://greenteapress.com/
  - Tukey 1977 EDA, Pearl 외 Primer, Angrist–Pischke — 본문 못 열면 서지만 `[?]`
  - 사고(28): Squire 1988(Literary Digest 1936 여론조사, Public Opinion Quarterly — JSTOR 초록·2차 출처는 그렇게 밝힌다), Lazer 외 Science 2014 "The Parable of Google Flu" (DOI 10.1126/science.1248506 — 초록·저자 사본), Herndon·Ash·Pollin 2013 (Reinhart–Rogoff 재현, PERI 워킹페이퍼 https://peri.umass.edu/), 영국 PHE 2020-10(GOV.UK 성명 — data-engineering/17과 같은 원문, 모순 없게)
  - Python `statistics` 모듈 문서 https://docs.python.org/3.12/library/statistics.html · PostgreSQL 17 집계·윈도 함수 문서(percentile_cont 등)
- WebSearch는 한도 소진일 수 있다 — 위 주소를 먼저 쓰고, 못 열면 Internet Archive. 그래도 못 열면 `[?]`. **기억으로 쓴 절·장·페이지·연도 번호에는 반드시 `[?]`**.

## 2. 출력 — `cs/data-analysis/<NN-slug>/`의 4파일

- **새 형식(2026-10-01)**: 제목 다음 줄부터 바로 본문이다. **제목 아래 `>` 머리말·복습 안내·"Claude 초안" 표식 줄을 두지 않는다.** 진행 단계는 같은 폴더 `metadata.md`에 둔다.

### metadata.md (그대로)

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-07 (Claude) |
| 검수 | — |
| 학습 | — |
```

### 2-summary.md

```
# data-analysis/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- 최상위 `## ` 헤딩은 이 7개만, 이 순서로 둔다(하위는 `###`). 실험 절은 `## 동작·원리`나 `## 적용` 안의 `### 실험: …`로 둔다.
- **해결하는 문제**: 이것이 없으면 무엇이 안 되나. 쉬운 예 → "똑같은 구조다" → 실무 예.
- **동작·원리**: 중심. ASCII 그림 먼저(측정 척도 사다리, 모집단→표본 깔때기, 분포 막대 그림(텍스트 히스토그램)·박스플롯, 백분위 위치, 표본분포가 좁아지는 그림, 신뢰구간 여러 개, 귀무·대립 분포와 α·β, 다중 비교 누적, 2×2 분할표, 산점도·회귀선, 인과 DAG, 무작위 배정·해시 버킷, 시계열 이동 평균), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 🔧 칸의 구조·알고리즘을 적고 기존 노트로 링크(대응표로 실제 폴더).
- **적용 — 풀어나가는 법**: 실무 순서: 증상(판단이 틀린 모양·숫자) → 통계 원리 → 코드·SQL로 확인. 코드는 Python 3.12 표준 라이브러리(`statistics`·`random`·`math`) 기본, 필요하면 Java 21, 분석 SQL은 PostgreSQL 17. numpy·scipy·pandas는 없다 — 필요한 계산은 직접 짜고(작게), 표준 라이브러리 결과와 대조한다.
- **장애 시나리오와 대처**: 3~5개. **현상 → 보이는 형태(어느 숫자·판단이 어떻게 틀리나·대시보드·리포트) → 원인 → 대처**, ⚠ 칸 포함.
- **핵심 문장**: 3~6문장.
- **관련 주제·근거**: 선행·후속 링크(이번 새 노트 `../NN-slug/2-summary.md`, 아직 없는 같은 영역 주제는 `../README.md`, 다른 영역은 실제 경로 확인), 문서 URL·명세 절, **실험 목록**(무엇을 어떤 환경에서 돌렸나).

### 1-question.md / 3-answer.md

`cs/database/16-mvcc/`와 같은 틀(머리말 없음). 질문 6~10개(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답은 번호·개수 일치. 예측형 질문은 실험 출력으로 답을 확인할 수 있게 쓴다.

## 3. 쓰는 방식 (사용자와 합의된 기준)

1. **그림 먼저, 글은 그림 해설.** 단순한 그림 여러 개 > 복잡한 그림 하나.
2. **용어는 처음 나오는 자리 바로 아래에서 푼다.** 형식 `  - *용어*: 설명`. 헷갈리기 쉬운 용어에만 그 아래 `    - 흔한 오해: …` 한 줄(근거 있는 오해만).
3. 한 문장에 한 개념. 용어가 셋 넘게 든 문장은 쪼갠다.
4. **코드**: Java 21(기본)·SQL·JS·TS. 셸은 진단·실험 구동에만.
5. **사실 규칙**: 수치·기본값·버전은 출처나 실험으로 확인했을 때만. 확인 못 하면 `[?]`. **지어내지 않는다.** 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의 (2차 리뷰 수백 건의 유형)

- **`[?]`는 확인 못 한 것에만.** 확인했으면 근거(절·URL·소스·실험)를 쓴다.
- **"항상·모든·반드시·절대" 금지** — 예외가 있으면 조건. 통계 정리는 전제(독립·동일 분포·표본 크기·분산 유한 등)를 반드시 적는다(수학 영역 지적의 대부분이 전제 누락이었다).
- **노트 안 모순 금지**: 그림과 글, 요약과 정답, 정답 N과 M, 실험 출력과 해석, 계산 산술.
- **근사 vs 정확 구분**: 정규 근사·CLT·t 분포 근사를 정확한 결과처럼 쓰지 않는다. 시뮬레이션 결과는 "시뮬레이션(시드·반복 수)"로 표시.
- **p값·신뢰구간 해석 정확히**: "귀무가설이 참일 확률", "모수가 구간에 있을 확률 95%" 같은 흔한 오해를 노트 본문이 저지르지 않는다(ASA 2016 p값 성명 https://www.amstat.org/asa/files/pdfs/p-valuestatements.pdf).
- **도구·버전 한정**: "Python 3.12 `statistics`에서", "PostgreSQL 17 `percentile_cont`에서" — 백분위 정의(보간 방식)가 도구마다 다르다는 것처럼 구현 차이를 일반 원리로 쓰지 않는다.
- **사고 보고의 날짜·수치는 원문 그대로**, 해석은 "해석".

## 4. (원고 없음)

- 이 영역은 원고가 없다. 겹치는 설명(분포·기댓값·선형대수)은 math 노트로 링크하고 한두 줄 요약만 둔다. 다른 영역 노트의 오류를 발견하면 고치지 말고 packet에 보고.

## 5. 실험 근거 (명세 I7 — 필수)

- 편마다 실행으로 보일 수 있는 핵심 주장 1개 이상(종합 27·28 선택). 시뮬레이션은 시드를 고정하고 반복 수를 적는다. 예:
  - 01·04·06: 척도별로 의미 있는 요약(평균 vs 중앙값), 이상값 하나가 평균을 끄는 것, 텍스트 히스토그램·박스플롯 다섯 수치.
  - 02·03: 편향 추출(응답자만)이 모집단 평균을 어떻게 어긋나게 하나, 층화 vs 단순 무작위.
  - 05: 지연 분포의 평균 vs p50·p99, 백분위의 평균을 내면 틀리는 것(병합 오류), 히스토그램 버킷 병합(HdrHistogram 개념)·간단한 분위 스케치 오차.
  - 07·08: 왜곡 분포에서 표본 평균의 분포가 정규에 가까워지는 크기(시뮬레이션), 부트스트랩 신뢰구간, 95% 구간 100개 중 포함 비율.
  - 09·10·11: 귀무가 참일 때 p값 분포가 균등인 것, 검정력·표본 크기 계산과 시뮬레이션 대조, 20개 지표 중 우연 유의 개수·Bonferroni·BH.
  - 12·25: 교란 변수로 생기는 상관·심슨의 역설(부분군 반전), 인과 DAG에서 조정해야 할 변수.
  - 13·22: 최소제곱 직접 구현 vs `statistics.linear_regression`, 외삽 실패, 로지스틱 회귀 경사 하강(작게).
  - 14·15·16: 해시 기반 결정적 배정(같은 사용자 같은 버킷), SRM 카이제곱 적합도, 엿보기(peeking)로 거짓 양성 증가 시뮬레이션, 비율 지표 vs 사용자 평균 지표.
  - 17: PostgreSQL 윈도 함수·gaps-and-islands, `percentile_cont` vs `percentile_disc`, 시간대 경계 일별 집계.
  - 18: 중복 제거·레코드 연결 실패로 합계가 어긋나는 것.
  - 19: 축 자르기·이중 축이 인상을 바꾸는 텍스트/ASCII 예(그림 대신 수치로).
  - 20·21: 카이제곱 독립성 검정·t 검정을 표준 라이브러리로 직접 계산하고 표 값과 대조.
  - 23: EWMA·이동 평균, 계절성 있는 데이터에서 전주 대비 vs 전일 대비.
  - 24: 시드·버전 고정 유무로 결과가 달라지는 재현 실험.
  - 26: 켤레 사전분포(베타-이항) 갱신, 리뷰 1개짜리 5.0의 사후 평균.
- 노트에 싣는 것: 실험 코드 핵심, 환경(호스트·이미지 버전), **실제 출력**, 관찰과 해석.

## 6. 실행 환경과 안전 규칙

- **공용 컨테이너 없음** — 필요하면 **자기 전용 일회용 컨테이너**: 이름 `sn-da-w<NN>-*`, `--rm`, `--cpus=2` 이하, 가능하면 `--network none`(postgres는 컨테이너 안에서 `psql`로 접속하면 네트워크 불필요). 두 컨테이너가 통신해야 하면 `docker network create sn-da-w<NN>-net --internal`로 만들고 끝나면 지운다. **이미 있는 이미지만**(`postgres:17`, `eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`) — **이미지 받기(`pull`)·빌드·`rmi`·`prune` 금지**(실행은 `--pull never`). 볼륨은 가능하면 만들지 않는다(익명 볼륨은 `--rm`으로 같이 지워진다). 끝나면 `docker ps -a --filter name=sn-da-w<NN>`·`docker network ls --filter name=sn-da`가 비었는지 확인.
- **Java 실행**: 호스트 java는 8이다. `docker run --rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <scratchpad 절대경로>:/w -w /w eclipse-temurin:21-jdk java X.java`. 외부 라이브러리는 쓰지 않는다(JDK만). JDBC 드라이버가 없으므로 DB 실험은 `psql`(postgres 컨테이너 안)로 한다.
- **호스트 도구**: python3(표준 라이브러리·sqlite3 모듈)만. **sudo·패키지 설치 금지**(pip·apt·npm install 포함). 실험은 수십 초~몇 분 이내·메모리 1GB 이하.
- **데이터**: 합성 데이터만(사람 이름·이메일·전화번호 같은 실제 개인정보 금지 — `user_001` 형식).
- **파일 위치**: 모든 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/da/<담당 첫 번호>/`에만(절대 경로). **저장소 루트·노트 폴더에 파일을 만들지 않는다.** 컨테이너는 `-u`로 돌려 root 소유 파일을 남기지 않는다(postgres 공식 이미지는 바인드 마운트 없이 쓰고, 결과는 `docker exec … psql` 출력을 호스트 파일로 리다이렉트).
- **개인정보 금지(2026-10-01 사고)**: HTTP 요청(User-Agent·헤더·쿼리)·파일·노트 어디에도 사용자의 이메일·이름 등 개인 식별 정보를 넣지 않는다.
- **프로세스**: 자기 PID만 종료(`pkill -f` 금지).
- **금지**: `sn-lang-*`·`sn-de-*`·`sn-arch-*`·`payment-*`·`jun-bank-*`·`text-*` 등 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지는 건드리지 않는다.

## 7. 하지 말 것

- 담당 폴더 밖 파일(다른 영역·커리큘럼·README 등)을 수정하지 않는다. git은 조회만.
- 리프 폴더에는 md만(1-question·2-summary·3-answer·metadata).
- 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS(머리말 금지·metadata 검사 포함).
- §3-1 노트 안 모순 자기 대조. 실험 출력과 본문·정답의 수치가 같은지 대조.

## 9. 반환 packet

- 폴더 목록과 check 결과
- 편별 주요 근거(문서 URL·명세 절·논문)
- **실험 목록**(주장 · 코드 경로 · 명령 · 환경 · 출력 요지) + 전용 컨테이너·네트워크를 지웠는지
- `[?]` 목록, 커리큘럼 ⚠ 칸 커버 여부, 미완료 항목
