# engineering-practice/19-practice-symptom-index — 증상 사전: 머지 지옥·CI 불신·배포 공포·리뷰 병목·"이건 왜 이렇게 했지?" → 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"브랜치를 오래 두면 merge-base 이후 변경이 쌓인다 → 충돌이 커진다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. "병합에 사흘째 매달려 있다", "CI는 원래 빨개요", "금요일엔 배포 안 해요", "PR이 일주일째 리뷰 대기", "이 상수는 왜 여기 또 있지?".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                   이 노트 (역방향)
  실천의 빈틈 --> 결함 --> 보이는 증상                    증상 --> 어디서·어떤 모양으로 --> 흔한 원인 --> 첫 진단 --> leaf
  "배포 대상 목록을 사람이 친다"                          "한 서버만 이상하다. 먼저 서버별 산출물 해시를 모은다"
```

쉬운 예: 병원 응급실의 분류표다.\
"배가 아프다"만으로 수술하지 않는다. 표가 "먼저 어디가, 언제부터 아픈지 묻고 피검사를 하라"고 정해 준다.\
표는 치료하지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
"CI가 빨갛다"라는 같은 증상에 원인이 여럿이다.
- 두 PR이 각자 초록이었는데 합친 뒤 빨갛다면 의미 충돌이다([06-2](../06-ci-cd-pipelines/2-summary.md)). 병합 결과를 검사하면 된다.
- 개발자 PC에서는 초록인데 CI에서만 빨갛다면 선언되지 않은 입력(시간대·로캘)이다([07-1](../07-build-systems-and-reproducibility/2-summary.md)). 입력을 고정하면 된다.
- 정적 분석을 켠 첫날부터 빨갛다면 기존 위반과 새 위반을 섞은 게이트다([14-2](../14-quality-standards/2-summary.md)). 기준선을 두면 된다.

처방이 셋 다 다르다. 증상만 보고 "CI를 고친다"고 하면 엉뚱한 곳을 손댄다.

실무 예:
- 엔지니어링 실천의 증상은 **코드 한 줄**보다 **흐름**에서 보인다. 변경이 작성 → 리뷰 → 통합 → 빌드 → 배포 → 운영 → 기억(문서·이력)으로 흐르다 어느 칸에서 막히거나 새는지가 증상이다.
- 실패가 보이는 칸과 원인이 있는 칸이 다를 수 있다. 리뷰 대기(리뷰 칸)가 머지 지옥(통합 칸)을 만들고([05-2](../05-code-review/2-summary.md) → [04-1](../04-branching-strategies/2-summary.md)), 캐시 키 누락(빌드 칸)이 운영의 이상한 설정(운영 칸)으로 보인다([07-2](../07-build-systems-and-reproducibility/2-summary.md)).
- 숫자가 좋아졌는데 아무것도 나아지지 않은 경우가 이 영역에 유난히 많다. 지표를 목표로 건 순간 지표가 증상을 가린다(7절).

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: 이 영역 `NN`번 노트의 「장애 시나리오와 대처」 `k`번째 시나리오다. 예: `06-3` = 06번 노트의 시나리오 3(배포 수동 단계 → 절차 누락).
  - *메시지 옆 버전*: 각 leaf 실험에서 실제로 찍힌 메시지와 도구 판이다. 판이 다르면 문구가 다를 수 있다. "시뮬레이션"이라고 적힌 수치는 스크립트로 만든 모형의 값이고 실측이 아니다.

## 동작·원리

### 0. 증상은 변경의 흐름 위 어느 칸에서 보이나

```text
  작성 ──▶ 리뷰 ──▶ 통합(병합) ──▶ 빌드·CI ──▶ 배포 ──▶ 운영 ──▶ 기억(이력·문서·결정)
   │        │          │             │           │        │            │
   │        │          │             │           │        │            └─ "이건 왜 이렇게 했지?"   (5절)
   │        │          │             │           │        └─ "사고 때 따라갈 수가 없다"          (9절)
   │        │          │             │           └─ "배포가 무섭다"                              (3절)
   │        │          │             └─ "CI를 못 믿겠다"                                         (2절)
   │        │          └─ "머지 지옥"                                                           (1절)
   │        └─ "리뷰가 병목이다"                                                                (4절)
   └─ (흐름 밖) 일정·재작업 6절 · 지표 7절 · 반복되는 의식 8절 · 감사·법무 10절 · 도입·벤더 11절 · 커밋이 사라짐 12절
```

- 커리큘럼의 다섯 증상(머지 지옥·CI 불신·배포 공포·리뷰 병목·"이건 왜 이렇게 했지?")이 1~5절이다. 6~12절은 leaf 시나리오에 나오는 나머지 증상이다.
- 흐름의 한 칸이 막히면 **앞 칸에 일이 쌓인다**. 리뷰가 막히면 브랜치가 길어지고, 파이프라인이 느리면 변경이 큰 덩어리로 모인다([06-5](../06-ci-cd-pipelines/2-summary.md)). 그래서 증상이 보이는 칸의 **한두 칸 앞(왼쪽)**을 함께 본다.

### 0-1. 늦게 보일수록 비싸다 — 같은 결함을 앞 칸으로 당긴 예

| 결함 | 늦게 보일 때의 모양 | 앞으로 당긴 장치 | 당긴 뒤 보이는 형태 (실험) | leaf |
|---|---|---|---|---|
| 이름 바꾼 메서드를 다른 브랜치가 호출 | 병합 뒤 main 빌드 실패, 동적 언어면 운영 오류 | 병합 결과(병합 큐)에 CI | `CI: GREEN` 두 번 뒤 병합 결과 `error: cannot find symbol` → `CI: RED`(git 2.43.0 · JDK 21 javac) | [06-2](../06-ci-cd-pipelines/2-summary.md) · [04-2](../04-branching-strategies/2-summary.md) |
| 8대 중 1대에 배포 누락 | 운영에서 한 서버만 다른 동작 | 배포 후 산출물 해시 대조 | `VERIFY: FAIL (drift)`, `s8 v1 old-flag=PowerPeg`(bash + sha256sum 모형 — 실제 Knight 시스템이 아님) | [06-3](../06-ci-cd-pipelines/2-summary.md) |
| 캐시 키에 설정 값이 빠짐 | 운영 번들에 스테이징 주소 | 캐시 키에 모든 입력 | 키에서 빠지면 `HIT … requested API_URL=https://prod.example.invalid artifact -> … "https://staging.example.invalid"`, 넣으면 `MISS`(JDK 21 직접 만든 해시 캐시) | [07-2](../07-build-systems-and-reproducibility/2-summary.md) |
| 기본 시간대에 기대는 날짜 계산 | "로컬은 초록, CI는 빨강" | CI에서 `TZ`·로캘을 일부러 다르게 | `zone=UTC … day=2026-10-04 … -> test FAIL`, `de_DE … amount=1,5 -> test FAIL`(JDK 21) | [07-1](../07-build-systems-and-reproducibility/2-summary.md) |
| 런북의 옵션이 코드에서 사라짐 | 새벽 장애 중 `unknown option: --promote`, 종료 코드 2 | 런북 내용 검사를 CI에 | 검사기가 `scripts/failover.sh 에 --promote 처리 분기 없음`을 미리 보고(git 2.43.0 · Node 18.19.1) | [11-1](../11-documentation-practices/2-summary.md) |
| 출시 때만 의존성 스캔 | 외부 연구자가 먼저 알려 줌 | 배포된 버전으로 정기 재질의 | log4j-core 2.25.2에 권고 4건(api.osv.dev, 2026-10-05 질의 — 날짜마다 바뀜) | [15-3](../15-security-standards/2-summary.md) |

- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: 에러 메시지·명령 출력 전체, 도구 판(git·Maven·Docker), 어느 커밋·어느 서버·어느 환경인지.
  - **시점과 모양**: 위 흐름의 어느 칸에서 처음 보였나. 매번 그런가, 가끔인가. 특정 변경·사람·날짜와 겹치나.

### 1. "머지 지옥" — 병합이 며칠씩 걸리고 main이 막힌다

먼저 **merge-base 이후 양쪽이 얼마나 갈라졌나**를 숫자로 본다(`git rev-list --left-right --count main...feature`).

```text
  병합이 고통스럽다
     │
     ├─ 충돌 파일이 수십 개, 양쪽 커밋 수백 ────────────────▶ 장수 브랜치                  04-1
     ├─ 브랜치가 긴 이유가 리뷰 대기 ───────────────────────▶ 리뷰 병목이 원인 칸           05-2 · 04-5
     ├─ 포맷 변경과 기능 변경이 한 PR에 ─────────────────────▶ diff 폭증                    14-5
     ├─ 충돌은 0개인데 병합 뒤 빌드·테스트 실패 ───────────────▶ 의미 충돌 (머지 지옥의 조용한 형태)  04-2 · 06-2
     ├─ 병합 뒤 고쳤던 버그가 재발, 이력엔 수정 커밋이 있음 ──────▶ 충돌 오해결로 코드 소실       03-2
     └─ 릴리스마다 같은 버그가 되돌아옴 ──────────────────────▶ 릴리스 브랜치에서만 수정       04-3
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 수십 파일 `CONFLICT (content)`. 통합 주기 시뮬레이션에서 20일 주기는 충돌 난 병합 1회당 267.3~288.0줄, 1일 주기는 6.6~9.8줄. 충돌 줄 합계는 20일 주기가 1일 주기의 약 5.3~9.1배(시뮬레이션, git 2.43.0 · Node 18.19.1, 시드 1~5) | merge-base 이후 변경 누적. 푸는 사람이 상대 변경의 의도를 모름 | `git rev-list --left-right --count`, 가장 오래된 미통합 커밋 날짜 | [04-1](../04-branching-strategies/2-summary.md) |
| `Merge made by the 'ort' strategy.`, 충돌 표식 0, 그런데 `Refund.java:2: error: cannot find symbol`(git 2.43.0 · JDK 21.0.12) | 텍스트 병합은 의미를 보지 않음 | 병합 결과 커밋에서 빌드·테스트를 돌렸나 | [04-2](../04-branching-strategies/2-summary.md) · [06-2](../06-ci-cd-pipelines/2-summary.md) |
| PR이 며칠 대기, 그 위에 다음 작업이 쌓임. 열린 PR 수 증가 | 리뷰 우선순위 낮음, 필수 승인 과다, 소유자 집중 | 첫 응답까지 시간 분포(Sadowski 2018의 Google 중앙값: 작은 변경 1시간 미만 — 비교 기준일 뿐) | [05-2](../05-code-review/2-summary.md) · [04-5](../04-branching-strategies/2-summary.md) |
| 같은 PR에 줄바꿈·import 순서 변경이 기능 변경과 섞여 diff가 큼 | 포매터가 자동화되지 않음 | PR을 포맷 커밋과 기능 커밋으로 나누면 기능 diff가 몇 줄인가 | [14-5](../14-quality-standards/2-summary.md) |
| `git log`엔 수정 커밋이 있는데 `git grep`으로 코드가 없음. 수정 브랜치 재병합은 `Already up to date.` | 충돌을 `--ours`/`--theirs`로 통째로 고르거나 한쪽 덩어리 삭제 | `git show --remerge-diff <merge>`(2.36+), `git log -m -S '<사라진 코드>'`(기본 `log -S`는 병합 커밋의 diff를 보지 않는다 — 03 실험) | [03-2](../03-version-control-and-git-internals/2-summary.md) |
| 1.2에서 고친 버그가 1.3에서 재발 | 수정이 릴리스 브랜치에만 | `git cherry -v main release/1.2`(main에서 같은 패치를 못 찾은 수정이 `+`. 인자 순서를 바꾸면 main 쪽만 보인다 — 04 실험, git 2.43) | [04-3](../04-branching-strategies/2-summary.md) |

- 처방의 방향은 하나다. **자주, 작게 통합**한다. 미완성 기능은 플래그·Branch by Abstraction으로 숨긴다([04-1](../04-branching-strategies/2-summary.md)).
- 단, 플래그로 숨기기 시작하면 플래그 자체가 부채가 된다([04-4](../04-branching-strategies/2-summary.md), 3절).

### 2. "CI를 못 믿겠다" — 빨강을 아무도 안 본다

먼저 **빨강이 무엇에 따라 바뀌나**로 가른다.

```text
  CI가 빨갛다 / 빨강을 무시한다
     │
     ├─ main이 며칠째 빨강, "원래 깨져 있어요" ─────────────▶ 실패 소유자 없음            06-1
     ├─ 각 PR은 초록, 합치면 빨강 ─────────────────────────▶ 의미 충돌                  06-2 · 04-2
     ├─ 로컬은 초록, CI만 빨강 ────────────────────────────▶ 선언되지 않은 입력          07-1
     ├─ 같은 커밋인데 재실행하면 초록 ──────────────────────▶ 불안정 테스트              testing/09 · 06-1
     ├─ 도구를 켠 첫날부터 계속 빨강 → 누군가 skip ────────────▶ 레거시 전체에 게이트        14-2
     ├─ 무관한 한 줄 변경에 위반 수십 건 ───────────────────▶ 줄 번호 기준선              14-3
     ├─ 경고가 수백 건이라 아무도 안 읽음 ───────────────────▶ 범주 없는 게이트(소음)       15-2
     ├─ 빌드가 시작도 안 됨 (cyclic reference) ──────────────▶ 순환 의존                  07-4
     └─ 결과가 40분 뒤에 나옴 → 변경을 모아서 올림 ─────────────▶ 느린 파이프라인            06-5 · 08-2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 대시보드 "failing since 3 days", 실패 테스트 목록이 계속 길어짐 | 실패를 소유한 사람이 없음. 불안정 테스트가 무시 습관을 만듦 | main 빨간 시간, 깨뜨린 첫 커밋 | [06-1](../06-ci-cd-pipelines/2-summary.md) |
| `zone=UTC locale=en_US day=2026-10-04 … -> test FAIL`, `locale=de_DE … amount=1,5 -> test FAIL`(eclipse-temurin:21-jdk, `TZ`·`-Duser.language`만 바꿈) | 기본 시간대·로캘·도구 판이 선언되지 않은 입력 | CI와 로컬의 `TZ`·로캘·JDK 판 비교 | [07-1](../07-build-systems-and-reproducibility/2-summary.md) |
| `PMD 7.7.0 has found 3 violations`로 빌드 실패 → 며칠 뒤 CI에 `-Dpmd.skip=true` | 기존 위반과 새 위반을 구분하지 않음 | 위반 중 이번 변경이 만든 것은 몇 건인가 | [14-2](../14-quality-standards/2-summary.md) |
| import 한 줄 추가에 "새 위반" 5건, 실제 새 위반은 2건(PMD 7.7.0 · maven-pmd-plugin 3.26.0) | 기준선 키에 줄 번호 | 기준선 지문이 무엇으로 만들어지나 | [14-3](../14-quality-standards/2-summary.md) |
| 보안 3건이 품질 경고와 섞여 같은 `[ERROR]` 줄로, `failed with 9 bugs and 0 errors`(SpotBugs 4.9.3 + FindSecBugs 1.14.0) | 범주·심각도를 나누지 않은 한 게이트 | 경고를 범주별로 세면 보안 고심각도는 몇 건인가 | [15-2](../15-security-standards/2-summary.md) |
| `The projects in the reactor contain a cyclic reference: … ex:app:1 --> ex:service:1 --> ex:util:1 --> ex:app:1`(Maven 3.9.16) | 하위 모듈이 상위 모듈을 의존 | 사이클 경로의 어느 간선이 방향을 거스르나 | [07-4](../07-build-systems-and-reproducibility/2-summary.md) |
| 커밋 단계 40분, PR 크기 증가. 파이프라인 모형에서 순차 합 29분 vs DAG 병렬 22분(소요 분은 예시 값) | 임계 경로를 안 봄, 느린 테스트를 커밋 단계에 다 넣음 | 임계 경로 위 작업이 무엇인가 | [06-5](../06-ci-cd-pipelines/2-summary.md) |
| 이미지 빌드가 코드 한 줄 수정에 11.7s, 순서를 바꾸면 2.5s(Docker 29.1.3 레거시 빌더) | `COPY . .`가 의존성 설치 앞 | 어느 단계부터 캐시가 깨지나(`CACHED`·`Running in`) | [08-2](../08-container-image-optimization/2-summary.md) |

- **"CI를 못 믿는다"의 끝 상태는 빨강을 아무도 안 보는 것**이다. 그러면 진짜 회귀도 옛 빨강에 묻힌다([06-1](../06-ci-cd-pipelines/2-summary.md)).
- 불안정 테스트(재실행하면 초록)는 테스트 영역 색인이 정본이다 — [testing/20-test-symptom-index](../../testing/20-test-symptom-index/2-summary.md) 1절, [testing/09-flaky-tests](../../testing/09-flaky-tests/2-summary.md).
- 게이트를 끄는 것(`-Dpmd.skip=true`, "경고만")은 처방이 아니다. 기준선(래칫)으로 새 위반만 막는다([14-2](../14-quality-standards/2-summary.md)).

### 3. "배포가 무섭다" — 금요일엔 안 한다, 한 번에 모아서 한다

먼저 **배포된 것이 의도한 것과 같은가**를 확인할 수 있는지 본다. 확인 수단이 없으면 공포는 합리적이다.

```text
  배포가 무섭다
     │
     ├─ 한두 서버만 이상하게 동작 ──────────────────────────▶ 수동 단계·배포 누락          06-3
     ├─ 스테이징에선 됐는데 운영에서 깨짐 ───────────────────▶ 환경마다 다시 빌드          06-4
     ├─ 수정한 코드가 반영 안 됨 / 옛 설정이 박힘 ──────────────▶ 캐시 오염                  07-2
     ├─ 지운 엔드포인트가 운영에서 여전히 동작 ───────────────▶ 지운 코드가 산출물에 남음    07-5
     ├─ 다시 빌드하면 해시가 다름 → "이게 그 소스인가?" ─────────▶ 재현 불가 빌드             07-3
     ├─ 롤백·스케일 아웃이 느림, ImagePullBackOff ────────────▶ 큰 이미지                  08-1
     ├─ 옛 플래그를 재사용했더니 옛 코드가 깨어남 ─────────────▶ 플래그 부채                 04-4
     ├─ 비밀번호가 이미지 안에 ────────────────────────────▶ 컨텍스트에 비밀              08-5
     └─ 사고 때 런북대로 쳤더니 실패 ───────────────────────▶ 낡은 런북                  11-1
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 인스턴스별 버전·해시가 섞임. 모형에서 수동 절차는 "성공으로 보고", 검증 단계는 해시 2종(`1 29bbb1d48f8c` / `7 bd899fbbbdb9`) → `VERIFY: FAIL (drift)` | 대상 목록·복사·확인을 사람이 함. 2차 확인 없음 | 서버별 산출물 해시를 모아 종류 수를 센다 | [06-3](../06-ci-cd-pipelines/2-summary.md) · [20](../20-practice-incidents/2-summary.md) |
| 스테이징과 운영 산출물 해시가 다름, 의존성 판이 다름 | 단계마다 소스에서 다시 빌드, 범위 버전·`latest` | 두 환경 산출물의 해시·의존성 목록 diff | [06-4](../06-ci-cd-pipelines/2-summary.md) |
| 빌드 로그는 "cache hit"·"up to date"뿐. 시각 판정 모형에서 내용을 바꾸고 mtime을 과거로 돌리자 `make: 'out.txt' is up to date.`인데 `out.txt = a`(GNU Make 4.3) | 캐시 키에서 입력 누락, 또는 시각 기반 판정 | 캐시 없이 다시 빌드해 해시 비교 | [07-2](../07-build-systems-and-reproducibility/2-summary.md) |
| jar 안에 소스 없는 `Legacy.class`(손 스크립트 증분 빌드 실험) | 출력 폴더를 비우지 않는 증분 빌드 | 산출물 클래스 목록 vs 소스 목록. 참고로 maven-compiler-plugin 3.15.0은 `Recompiling the module because of added or removed source files.`로 삭제를 반영했다 | [07-5](../07-build-systems-and-reproducibility/2-summary.md) |
| 같은 소스 두 빌드가 `bf0b98304c05ce73` / `aeeff60013ea9cfc`, `outputTimestamp` 고정 뒤 둘 다 `f418ea6b2a18687e`(Maven 3.9.16 · JDK 21.0.11 · maven-jar-plugin 3.5.1) | 현재 시각·나열 순서·빌드 경로·JDK 메이저 | `jar tvf`로 엔트리 시각 비교, diffoscope | [07-3](../07-build-systems-and-reproducibility/2-summary.md) |
| 새 파드가 `ContainerCreating`에 오래, 실패하면 `ImagePullBackOff`(Kubernetes 재시도 상한 300초 — 08 노트의 문서 인용) | 빌드 도구·캐시가 든 큰 이미지, 베이스가 제각각 | 파드 이벤트 메시지(이름 오타·인증 누락도 같은 상태) | [08-1](../08-container-image-optimization/2-summary.md) |
| `if (flags.isOn(...))` 수십 개, 옛 플래그 이름 재사용 뒤 옛 코드가 깨어남 | 릴리스 플래그를 지우지 않음 | 플래그 등록부와 코드의 키 대조, 만료일 | [04-4](../04-branching-strategies/2-summary.md) |
| 이미지 안 `/app/.env`에서 `DB_PASSWORD=dummy-not-real`, 컨텍스트 150MB(`.dockerignore` 뒤 11.78kB)(Docker 29.1.3) | `.dockerignore` 없이 `COPY . .` | `docker history`, 이미지 파일 목록 | [08-5](../08-container-image-optimization/2-summary.md) |
| `unknown option: --promote`, 종료 코드 2 | 코드는 6월에, 런북은 3월 그대로 | 런북이 가리키는 스크립트·설정 키가 지금 있나 | [11-1](../11-documentation-practices/2-summary.md) |

- 배포 공포의 해독제는 용기가 아니라 **확인 수단**이다: 한 번 빌드해 해시로 지정한 산출물([06-4](../06-ci-cd-pipelines/2-summary.md)), 배포 후 해시 대조([06-3](../06-ci-cd-pipelines/2-summary.md)), 재현 가능 빌드([07-3](../07-build-systems-and-reproducibility/2-summary.md)), 작은 이미지로 빠른 롤백([08-1](../08-container-image-optimization/2-summary.md)).
- 단계 배포·카나리·롤백 판단은 운영 영역이 정본이다 — [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md), 플래그 수명은 [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md).
- 이 칸의 실사건(배포 누락 + 재사용 플래그, 규칙의 전역 즉시 배포)은 [20-practice-incidents](../20-practice-incidents/2-summary.md).

### 4. "리뷰가 병목이다" — 대기는 길고, 승인은 형식적이다

먼저 **기다리는 시간이 문제인지, 승인의 질이 문제인지** 가른다. 둘은 서로를 키운다.

```text
  리뷰가 병목
     │
     ├─ 수천 줄 PR이 몇 분 만에 LGTM ──────────────────────▶ 거대 PR (질 문제)          05-1
     ├─ PR이 며칠 대기, 그 위에 작업이 쌓임 ─────────────────▶ 대기 (시간 문제)          05-2
     ├─ 댓글 대부분이 스타일·이름 ──────────────────────────▶ 기계가 할 일을 사람이       05-3 · 14-5
     ├─ 리뷰어마다 통과 기준이 다름, "리뷰어 운" ──────────────▶ 기준 부재                 14-1
     ├─ 늘 같은 사람만 리뷰할 수 있음 ──────────────────────▶ 지식 집중                 05-4
     ├─ "LGTM 빨리요", 리뷰 없이 머지 ──────────────────────▶ 조급함이 사람을 향함        18-2
     └─ 리뷰 스레드가 길고 결론이 안 남 ─────────────────────▶ 오만이 자아를 향함          18-3
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 섞인 PR `31 files changed, 31 insertions(+), 31 deletions(-)` 속에 동작 변경은 `<=` → `<` 한 줄. 62줄 중 2줄이 동작 변경. `-w`로도 못 걸러냄(git 2.43.0) | 기계적 변경과 동작 변경이 한 PR에 | 커밋을 목적별로 나누면 동작 커밋은 몇 줄인가(`--word-diff`) | [05-1](../05-code-review/2-summary.md) |
| 크기 대비 리뷰 시간·댓글이 비정상적으로 적음. Cisco 사례 연구: 시간당 450줄을 넘은 리뷰의 87%가 결함 밀도 평균 미만(벤더 사례 연구 수치) | 리뷰어가 이해할 수 있는 양을 넘음 | PR 크기 분포, 크기 대비 댓글 수 | [05-1](../05-code-review/2-summary.md) |
| 첫 응답이 며칠, 열린 PR이 계속 늘어남 | 리뷰 우선순위 낮음, 필수 승인 과다, 소유자 1~2명 | 첫 응답 시간 분포, 리뷰어별 대기 건수 | [05-2](../05-code-review/2-summary.md) |
| 같은 PR에 스타일 댓글 수십 개, 설계 문제는 놓침 | 포매터·린터 미자동화, 기준 문서 없음 | 댓글을 "자동화 가능 / 판단 필요"로 분류 | [05-3](../05-code-review/2-summary.md) · [14-5](../14-quality-standards/2-summary.md) |
| 같은 패턴이 어떤 PR은 통과, 어떤 PR은 막힘. "제 취향은…" | 판정 기준이 사람에게 있음 | 반복 지적을 모아 결정적인 것과 판단할 것으로 분류 | [14-1](../14-quality-standards/2-summary.md) |
| 한 모듈은 늘 같은 작성자·같은 리뷰어 | 리뷰어 배정이 소유자 1인에 고정 | 파일별 작성자·리뷰어 분포([software-design/53](../../software-design/53-code-forensics-hotspots/2-summary.md)) | [05-4](../05-code-review/2-summary.md) |
| "LGTM 빨리요", 테스트 스킵 플래그가 붙은 배포 뒤 롤백 | 대기의 원인(큰 PR·느린 CI) 대신 사람과 절차에 화를 냄 | 기다림을 잰다: 리뷰 대기, CI 시간 | [18-2](../18-engineering-virtues/2-summary.md) |
| 지적에 방어적 답변, 같은 기능의 사내 구현이 여럿 | 기준이 "결과물"에서 "나"로 | "기준이 결과물인가, 나인가?" | [18-3](../18-engineering-virtues/2-summary.md) |

- 시간 문제와 질 문제는 **같은 처방으로 함께 준다**: 작은 PR이다. 작으면 빨리 보고, 빨리 보면 PR이 덜 커진다([05-2](../05-code-review/2-summary.md)).
- 리뷰 크기 기준은 출처마다 성격이 다르다(Google 지침·Sadowski 측정·벤더 사례 연구). 고정 기준으로 쓰지 않는다([05](../05-code-review/2-summary.md) 동작·원리).

### 5. "이건 왜 이렇게 했지?" — 이유를 아는 사람도 기록도 없다

먼저 **이유가 어디에 있어야 했나**를 묻는다. 커밋·PR·요구 ID·결정 기록·문서 중 어디에도 없으면 그것이 증상의 원인이다.

```text
  "이건 왜 이렇게 했지?"
     │
     ├─ 같은 규칙 상수가 여러 곳에, 한 곳만 값이 다름 ───────────▶ 복사본 누락                10-2 · 02-3
     ├─ 요구 ID로 검색해도 코드·테스트가 안 나옴 ──────────────▶ 추적 끊김                 02-3
     ├─ 고쳤던 코드가 사라졌는데 이력엔 수정이 있음 ─────────────▶ 충돌 오해결                03-2
     ├─ "배포 방법" 문서가 셋, 내용이 서로 다름 ───────────────▶ 정본 없음                 11-3
     ├─ 검색 상위 문서가 3년 전 것 ─────────────────────────▶ 소유자 없는 위키           11-4
     ├─ 신입은 "시작하기" 중간에 길을 잃고, 숙련자는 한 단계를 못 찾음 ──▶ 문서 유형이 섞임           11-2
     ├─ 그 코드를 아는 사람이 한 명 ─────────────────────────▶ 지식 집중                 05-4
     ├─ 아무도 요청하지 않은 기능이 있음 ─────────────────────▶ 골드 플레이팅              02-4
     └─ 이유는 알겠는데 지금도 맞는지 모름 ─────────────────────▶ 결정 기록·재검토 조건 없음    13-2 · software-design/47
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 세율 변경 뒤 환불만 고객 문의. 예외 없음. 실험의 `debt-missed`: `RefundService FOOD 100 BOOK 100`, 나머지 셋은 `BOOK 0`(git 2.43.0 · JDK 21.0.12) | 같은 규칙의 복사본 중 일부만 바뀜 | `git grep`으로 같은 규칙의 복사본 찾기, 같은 입력을 모든 복사본에 넣어 비교 | [10-2](../10-technical-debt/2-summary.md) |
| 정책이 "24시간 → 48시간"으로 바뀌었는데 일부 화면·배치는 옛 기준. 요구 ID 검색 결과 0 | 요구와 코드·테스트 사이 연결 없음. 추적 검사 v1: `요구 커버 1/3`(JDK 21) | 요구 ID를 테스트 태그·커밋·설정 키에 달았나 | [02-3](../02-requirements-engineering/2-summary.md) |
| `git log`엔 수정이 있는데 코드가 없음 | 충돌 해결에서 한쪽을 버림 | `git show --remerge-diff`, `git log -m -S` | [03-2](../03-version-control-and-git-internals/2-summary.md) |
| 같은 주제 문서 여러 벌, 서로 다름 | 소유자와 정본 위치 없음(SWE@G 10장: GooWiki의 Borg 설정 문서 7~10개) | 정본 하나를 정하고 나머지에 폐기 표시 | [11-3](../11-documentation-practices/2-summary.md) |
| 조회·수정이 없는 문서가 대부분(GooWiki 폐기 때 약 90%가 직전 몇 달 조회·수정 없음 — SWE@G 10장 각주) | 소유자·검토일 없음 | 문서별 마지막 수정·조회 | [11-4](../11-documentation-practices/2-summary.md) |
| "시작하기" 문서 중간에 운영 옵션, 숙련자는 긴 설명을 스크롤 | 배움(튜토리얼)과 일(방법 가이드)을 한 문서에. diataxis.fr은 이 둘이 합쳐지는 것을 최악의 경우로 듦 | 문단마다 "배우는 중인가, 일하는 중인가"(나침반 질문) | [11-2](../11-documentation-practices/2-summary.md) |
| 특정 모듈은 한 사람만 고침 | 리뷰가 지식 공유를 못 함 | 파일별 작성자 분포 | [05-4](../05-code-review/2-summary.md) |
| 추적 매트릭스 위쪽(이해관계자 필요)에 연결되지 않는 요구·코드 | 개발자 짐작으로 추가, 변경 관리 없음 | 요구마다 "부모 필요"가 있나. 추적 검사의 고아 테스트(`REQ-9 <- [old_coupon_rule]`) | [02-4](../02-requirements-engineering/2-summary.md) |
| 벤더 SDK 타입이 코드 곳곳에, 왜 이 벤더인지·언제 다시 볼지 기록 없음 | 결정 기록에 재검토 조건이 없음 | 결정 기록(ADR)이 있나, 재검토 조건(가격·API 수명)이 적혔나 | [13-2](../13-build-vs-buy-and-adoption/2-summary.md) |

- 코드에서 이유를 찾는 첫 명령은 `git log -S '<문자열>'`(그 문자열이 생기거나 사라진 커밋)과 `git blame -w -C`다. 병합 해결에서 사라졌을 수 있으면 `-m`을 붙인다(기본 `log -S`는 병합 커밋의 diff를 보지 않는다 — [03-2](../03-version-control-and-git-internals/2-summary.md)). 커밋 메시지·PR 설명이 이유를 담았다면 여기서 끝난다.
- 이유가 어디에도 없으면, 지금 알아낸 이유를 **결정 기록**으로 남긴다. 결정 기록 형식은 [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md)가 정본이다.
- 코드 주석이 낡아 거꾸로 잘못된 판단을 부르는 경우는 [software-design/09-comments-and-conventions](../../software-design/09-comments-and-conventions/2-summary.md)(11-1이 인용).

### 6. "일정이 늘 밀린다·만들고 나서 다시 만든다"

```text
  일정·재작업
     │
     ├─ 매번 일정 초과, 계획엔 숫자 하나 ────────────────────▶ 단일 점 추정               12-1
     ├─ 추정 회의 전에 날짜가 정해져 있음 ─────────────────────▶ 목표가 추정으로 둔갑          12-2
     ├─ 기획 초기에 준 날짜가 계약이 됨 ──────────────────────▶ 원뿔 초입의 약속             12-3
     ├─ 추정이 너무 커서 거절됨 ─────────────────────────────▶ 최악끼리 더한 버퍼           12-4
     ├─ 사람을 더 넣었는데 더 늦어짐 ─────────────────────────▶ Brooks의 법칙              12-5
     ├─ 데모에서 "이건 우리가 말한 게 아닌데요" ────────────────▶ 모호 요구                  02-1
     ├─ 기능 테스트는 통과, 출시 직전 부하 테스트에서 느림 ──────────▶ 비기능 요구 누락            02-2
     ├─ 요구대로 만들었는데 아무도 안 씀 ──────────────────────▶ validation 없음             02-5
     ├─ 요구 목록이 계속 길어짐 ─────────────────────────────▶ 범위 크리프                 02-4 · 01-5
     ├─ 스프린트 마지막 날 테스트 몰림 ────────────────────────▶ 스프린트 안의 미니 폭포수       01-2
     └─ 같은 크기 기능이 분기마다 더 오래 걸림 ──────────────────▶ 보이지 않는 부채              10-1
```

| 보이는 것 (실험·출처) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 가능성 최대 합 30일로 약속. 몬테카를로에서 P(합≤30일) = 1.0%(시뮬레이션, JDK 21, 10만 회, 작업 8개 예시) | 오른쪽 꼬리가 긴 분포의 최빈값을 더함 | 실적 대비 추정 비율 기록이 있나 | [12-1](../12-estimation-and-planning/2-summary.md) |
| 추정이 날짜에 딱 맞게 나옴 | 추정과 목표를 섞음(McConnell 1.2) | 추정과 목표를 따로 적었나 | [12-2](../12-estimation-and-planning/2-summary.md) |
| 약속 시점이 "초기 구상" | 원뿔이 가장 넓을 때(최대 4배 오차) 약속 | 이후 다시 추정한 기록 | [12-3](../12-estimation-and-planning/2-summary.md) |
| 작업별 최악 합 68일 vs 합의 분포 P99 48.7일(같은 시뮬레이션) | 모든 작업이 동시에 최악일 확률을 무시 | 계획 숫자가 무엇의 합인가 | [12-4](../12-estimation-and-planning/2-summary.md) |
| 투입 뒤 회의·인계가 늘어남 | 나눌 수 있는 일과 소통 비용의 한계 | 독립적으로 나눌 일이 있나, 남은 기간은 | [12-5](../12-estimation-and-planning/2-summary.md) |
| 요구 문서에 "빠르게·적절히". 추적 검사 v1 `REQ-1  F  모호어=[빨라]  수치기준=없음`, `REQ-1  테스트 0개 <-- 검증 수단 없음` | 검증 가능한 문장이 아님 | 요구마다 측정 대상·조건·임계값이 있나 | [02-1](../02-requirements-engineering/2-summary.md) |
| v1 요약 `요구 3개(비기능 0)` — v1의 속도 요구(`REQ-1  F  모호어=[빨라]`)가 기능(F)으로 적혀 비기능이 0으로 보인다 | 도출 때 운영·보안·법무를 안 부름, 품질 요구를 기능 요구로 적음 | 품질 속성 체크리스트로 다시 묻기 | [02-2](../02-requirements-engineering/2-summary.md) |
| 시제품·데모 없이 바로 구현 | verification만, validation 없음 | 이해관계자가 동작하는 것을 본 적이 있나 | [02-5](../02-requirements-engineering/2-summary.md) |
| 스프린트 시작 뒤 추가된 항목이 많음 | 스프린트 목표를 지킬 장치 없음, 유입형 일 | 추가 요청의 경로(PO를 거쳤나) | [01-5](../01-lifecycle-and-agile/2-summary.md) · [02-4](../02-requirements-engineering/2-summary.md) |
| 번다운이 마지막 2~3일까지 평평 | 스프린트 안에서 설계 → 구현 → 테스트 순차 | 진행 중 작업 수, 스토리 크기 | [01-2](../01-lifecycle-and-agile/2-summary.md) |
| 리드 타임 증가, 변경당 파일 수 증가. 같은 기능 3개를 넣는 데 부채 브랜치는 누적 파일 12·줄 24, 상환 브랜치는 정리 포함 8·20(git 2.43.0) | 이자를 기록하지 않음 | 변경당 건드리는 파일 수 추세 | [10-1](../10-technical-debt/2-summary.md) |

### 7. "숫자는 좋아졌는데 나아진 게 없다" — 지표가 증상을 가린다

이 영역에서 가장 자주 반복되는 모양이다. 측정을 목표로 걸면 측정을 맞추는 행동이 나온다(굿하트의 법칙, [09](../09-dora-metrics/2-summary.md)).

```text
  지표 ↑, 실제 ─
     │
     ├─ 배포 빈도 3배, 기능 출시 속도는 그대로 ────────────────▶ DORA 지표 게이밍            09-1
     ├─ 팀별 순위표, 하위 팀은 "우리는 다르다" 자료 ─────────────▶ 맥락 없는 비교              09-2
     ├─ 도구 바꾼 날 리드 타임 50h → 4h ──────────────────────▶ 정의 변경                  09-3
     ├─ 클라우드 장애 달에 복구 시간 폭등 ──────────────────────▶ 외부 장애가 섞임            09-4
     ├─ 지표 파이프라인만 석 달째 ────────────────────────────▶ 측정에 몰두                 09-5
     ├─ 스토리 포인트 합계 ↑, 나가는 기능은 그대로 ──────────────▶ 속도를 목표로               01-3
     ├─ 부채 비율 게이트 통과, 억제 주석 ↑ ────────────────────▶ 부채 점수를 목표로           10-5
     ├─ 위반 수 ↓, 변수 이름만 unused… ───────────────────────▶ 품질 지표 우회               14-4
     ├─ 신선도 대시보드 초록, 런북은 여전히 틀림 ─────────────────▶ 검토일만 올림               11-5
     ├─ Scorecard 7점 규칙으로 도입·거절 ──────────────────────▶ 집계 점수 하나에 의존          13-5
     └─ "일단 부채로" 반복, 상환 기록 없음 ──────────────────────▶ 부채 은유를 핑계로           10-4
```

| 보이는 것 (실험·도구 판) | 무엇이 조작·왜곡됐나 | 첫 진단 | leaf |
|---|---|---|---|
| gamed: 배포 빈도 7.6회/주, 변경 실패율 7.7%, 재작업률 0.0%, 리드 타임 중앙값 50.0h 그대로, `(점검) 새 커밋 없는 배포 17회`(git 2.43.0 · Node 18.19.1) | 같은 버전 재배포로 분모를 늘리고 분류를 바꿈 | 다섯 지표를 묶음으로, 새 커밋 없는 배포 수 | [09-1](../09-dora-metrics/2-summary.md) |
| 펌웨어·결제 코어 팀이 늘 꼴찌 | 서로 다른 시스템을 같은 잣대로(dora.dev "Making disparate comparisons") | 비교 대상이 같은 서비스의 과거인가 | [09-2](../09-dora-metrics/2-summary.md) |
| rebase 후 작성자 날짜는 `2026-09-02T09:00:00+00:00` 그대로, 커미터 날짜는 `2026-09-09T09:00:00+00:00`(git 2.43.0) | 측정 시작점 정의 변경, 커미터 날짜 사용 | 시작점이 문서로 정해져 있나 | [09-3](../09-dora-metrics/2-summary.md) |
| 배포를 안 한 달에 복구 시간 폭등 | MTTR식 정의는 원인을 가리지 않음(DORA 2023 정의 변경) | 배포 원인 사고와 외부 사고를 나눴나 | [09-4](../09-dora-metrics/2-summary.md) |
| 병목은 하나도 안 고침 | 정밀도에 과투자(dora.dev 함정) | 가장 큰 병목이 무엇인지 이미 아나 | [09-5](../09-dora-metrics/2-summary.md) |
| 같은 크기 일의 포인트가 커짐 | 계획용 관찰값을 성과 지표로 | 팀 간 속도 비교표가 있나 | [01-3](../01-lifecycle-and-agile/2-summary.md) |
| "부채 비율 5% 이하" 뒤 억제 주석·의미 없는 분할 증가 | 도구 점수 = 규칙 위반의 합 | 억제 주석 수 추세 | [10-5](../10-technical-debt/2-summary.md) |
| 미사용 변수 이름이 `unused…`로(PMD UnusedLocalVariable이 거르는 이름) | 규칙의 의도된 예외가 우회로 | 억제·예외 사용 수 | [14-4](../14-quality-standards/2-summary.md) |
| 날짜만 올리자 경고 7건 → 4건, 옵션·설정 키·링크 문제는 그대로(git 2.43.0 · Node 18.19.1) | 날짜는 사람이 바꾸는 대리값 | 남은 경고가 날짜류인가 내용류인가 | [11-5](../11-documentation-practices/2-summary.md) |
| 옛 이름(junit5) 스캔 2025-06-22의 8.3, 새 이름 7.9. Guava Code-Review 0(Node 18.19.1, 2026-10-05 조회 — 스캔마다 바뀜) | 집계 점수는 무엇을 하는지 알려 주지 않음 | 스캔 날짜·저장소 이름, 개별 항목 | [13-5](../13-build-vs-buy-and-adoption/2-summary.md) |
| 급할 때마다 "부채로 지고 가자" | 은유가 품질 방치를 정당화(Fowler 2019) | 의도적 부채에 상환 조건·기한이 있나 | [10-4](../10-technical-debt/2-summary.md) |

- 공통 처방: 지표는 **어디를 볼지** 정하는 데 쓰고 목표·평가·순위에 직접 묶지 않는다. 지표 하나만 좋아지면 의심한다. 원시 이벤트(새 커밋 없는 배포, 억제 주석, 날짜만 바뀐 커밋)를 따로 센다.
- 테스트 지표(커버리지·변이 점수)의 같은 모양은 [testing/20-test-symptom-index](../../testing/20-test-symptom-index/2-summary.md) 장애 5.

### 8. "같은 문제가 계속 반복된다" — 의식은 있는데 학습이 없다

```text
  같은 문제 반복
     │
     ├─ 회고마다 같은 문장, 사고 원인 태그가 같음 ───────────────▶ 회고 루프가 끊김            01-1
     ├─ 팀 이름만 스쿼드, 일하는 방식은 그대로 ──────────────────▶ 모양만 복사               01-4
     ├─ 고친 SQL 인젝션과 같은 모양이 다른 모듈에서 ────────────────▶ 패턴이 아니라 한 곳만 고침    15-1
     ├─ 릴리스마다 같은 버그 ───────────────────────────────▶ 수정이 한 브랜치에만         04-3
     ├─ "오만은 미덕"이 무례함의 핑계 ─────────────────────────▶ 단어만 떼어 씀             18-4
     └─ 이틀 들여 만든 자동화가 다음 분기엔 깨져 있음 ─────────────▶ 계산 없는 자동화           18-1
```

| 보이는 것 (실험·출처) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 같은 원인이 반복되는 모형에서 12회 반복 동안 반복된 문제: 회고 없음 20.21, 의식만 17.65, 행동까지 4.37(시뮬레이션, JDK 21, 2000회 평균) | 회고가 행동 항목·백로그·효과 확인에서 끊김 | 지난 회고 행동 항목의 담당·기한·효과 확인 기록 | [01-1](../01-lifecycle-and-agile/2-summary.md) |
| 스쿼드가 배포하려면 다른 팀 승인 필요 | 해결할 문제 없이 모양을 복사 | "독립 배포가 안 되는 이유"를 구체적으로 | [01-4](../01-lifecycle-and-agile/2-summary.md) |
| 같은 CWE가 보고서마다. 실험에서 SpotBugs가 `SQL_INJECTION_JDBC`를 `OrderDao.java:[line 13]`에서 보고 | 기준과 자동 대조 없음 | 신고된 패턴을 저장소 전체에서 검색 | [15-1](../15-security-standards/2-summary.md) |
| 1.2에서 고친 버그가 1.3에 | 트렁크로 옮기지 않음 | `git cherry -v main release/1.2` | [04-3](../04-branching-strategies/2-summary.md) |
| 리뷰 말투가 공격적, 새 사람이 질문 안 함 | 정의 없이 단어만 씀 | 세 단어의 과녁을 함께 말하나 | [18-4](../18-engineering-virtues/2-summary.md) |
| 스크립트 마지막 실행이 몇 달 전 | 손익분기 계산 없음(18 계산: 분기 1회 보고서는 52주 안에 이득 없음) | 빈도·수작업 시간·제작·유지 비용 | [18-1](../18-engineering-virtues/2-summary.md) |

### 9. "사고 때 따라갈 수가 없다" — 운영 형식이 제각각이다

```text
  사고 대응이 막힘
     │
     ├─ 한 요청을 서비스마다 다른 검색어로 ─────────────────────▶ 로그 필드 제각각           16-1
     ├─ 타임라인에서 원인이 결과보다 늦게 적힘 ───────────────────▶ 시각 표기 혼재            16-2
     ├─ ERROR 건수가 이상, 스택트레이스가 조각 ───────────────────▶ 멀티라인 로그              16-3
     ├─ 한 서비스만 1000배 느려 보임, 지표 저장소 메모리 급증 ────────▶ 단위·이름·레이블 혼재       16-4
     ├─ 새 서비스에 경보·런북이 없음 ─────────────────────────▶ 표준이 문서에만             16-5
     ├─ 런북대로 쳤는데 실패 ────────────────────────────────▶ 낡은 런북                 11-1
     └─ 컨테이너에 들어가 볼 수 없음 ───────────────────────────▶ 셸 없는 이미지            08-3 · 08-4
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 같은 trace ID가 `trace_id`(c.log 팀 표준)와 `traceId`(d.log 첫 줄)로 갈림. 표준 필드 검색에서 d.log의 이벤트 1건이 빠짐(Logback 1.5.12 · JDK 21.0.12) | 운영 형식을 팀마다 정함 | 로그 필드 이름 목록을 서비스별로 뽑아 비교 | [16-1](../16-operational-standards/2-summary.md) |
| `02:10:59.499`(Logback 기본, 날짜·오프셋 없음), `Oct 05, 2026 2:11:01 AM`(JUL 기본), `2026-10-04T17:11:04.411773918Z`(팀 표준)가 섞임(Logback 1.5.12 · JDK 21.0.12, TZ=Asia/Seoul) | 시각 형식이 표준에 없음 | 각 서비스 로그의 시각 형식·오프셋 | [16-2](../16-operational-standards/2-summary.md) |
| 이벤트 3건이 13줄, `\tat java.base/...` 줄이 레벨 없는 별개 이벤트 | 한 이벤트 = 한 줄 규칙 없음 | 수집기의 이벤트 수 vs 애플리케이션의 로그 호출 수 | [16-3](../16-operational-standards/2-summary.md) |
| `payment_latency_ms`·`shipping_label_user_10234_total` 같은 이름(검사기 `위반 이름 4개`, JDK 21.0.12 — 이름 목록은 예시) | 이름·단위·레이블 규칙 없음 | 단위 접미사, 레이블 값의 종류 수 | [16-4](../16-operational-standards/2-summary.md) |
| 출시 체크리스트에 운영 항목 없음 | 강제가 "읽고 따르기"뿐 | 서비스 템플릿 기본값에 표준이 들어 있나 | [16-5](../16-operational-standards/2-summary.md) |
| `exec: "sh": executable file not found in $PATH`, exit=127(Docker 29.1.3, `FROM scratch` 정적 바이너리) | 셸 없는 이미지 — 의도된 설계 | 임시 디버그 컨테이너(`kubectl debug --target`) | [08-3](../08-container-image-optimization/2-summary.md) |
| 파일이 있는데 `exec /opt/java/bin/java: no such file or directory`, exit=255(Alpine 3.24.1) | glibc 바이너리의 로더 `/lib64/ld-linux-x86-64.so.2`가 없음 | `readelf -l`로 인터프리터 확인 | [08-4](../08-container-image-optimization/2-summary.md) |

- 사고 대응 절차 자체(지휘·소통·포스트모템)는 [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md), 런북 준비는 [reliability/44-runbooks-and-operational-readiness](../../reliability/44-runbooks-and-operational-readiness/2-summary.md)가 정본이다.

### 10. "감사·보안 점검·법무에서 걸렸다"

```text
  외부 점검에서 발견
     │
     ├─ 알려진 취약점이 몇 달째 ───────────────────────────────▶ 출시 때만 스캔            15-3
     ├─ "그 라이브러리 안 쓴다"고 답했는데 들어 있음 ─────────────▶ 전이 의존성               15-4 · 17-1
     ├─ 인증 서버 타임아웃 때 요청이 승인됨 ─────────────────────▶ 예외 경로 fail-open       15-5
     ├─ 고객 설치형 제품에서 GPL 계열 발견 ──────────────────────▶ 라이선스 검사 없음         17-1
     ├─ 도구 보고서와 공식 사이트의 라이선스가 다름 ──────────────▶ 메타데이터를 그대로 믿음    17-3
     ├─ 수정한 AGPL 컴포넌트를 SaaS로 운영 ─────────────────────▶ AGPL §13 미검토           17-4
     ├─ 탈퇴 2년 회원의 이메일이 발송 목록에 ─────────────────────▶ 보관 기한 모델 없음        17-2
     ├─ 유출 의심인데 "확정되면 통지" ─────────────────────────▶ 개정 법령 미반영           17-5
     ├─ 레지스트리 접근만으로 DB 비밀번호가 읽힘 ──────────────────▶ 비밀이 이미지에           08-5
     └─ 의존 OSS 새 버전이 소스 공개 라이선스로 ───────────────────▶ 라이선스 변경 미감시        13-3
```

| 보이는 것 (실험·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| log4j-core 2.25.2에 권고 4건(`GHSA-445c-vh5m-36rj` 포함), 출시 때는 깨끗했을 판(api.osv.dev, 2026-10-05 질의) | SCA를 PR 시점에만 | 배포된 버전 목록으로 오늘 다시 질의 | [15-3](../15-security-standards/2-summary.md) |
| `pom.xml`엔 없는데 산출물엔 있음 | 직접 의존성만 확인 | `mvn dependency:tree`, SBOM | [15-4](../15-security-standards/2-summary.md) · [17-1](../17-legal-standards/2-summary.md) |
| `catch`에서 로그만 남기고 진행, 장애 중 인가 거부 로그 0건 | 체크리스트가 정상 경로만 물음 | 의존 서버를 죽인 상태의 테스트 | [15-5](../15-security-standards/2-summary.md) |
| 산출물 jar 목록에 GPL 계열, 전이 의존성으로 들어옴(license-maven-plugin 2.4.0) | 빌드에 라이선스 정책 검사 없음 | 펼친 라이선스 목록 + 정책(모르는 것 = 실패) | [17-1](../17-legal-standards/2-summary.md) |
| logback 1.5.12의 POM은 `Eclipse Public License - v 1.0`, 공식 페이지는 EPL v2.0 | POM 라이선스 칸은 자유 텍스트 | 소스 저장소 LICENSE 원문 | [17-3](../17-legal-standards/2-summary.md) |
| 라이선스 목록에 `AGPL-3.0-only`, 저장소에 패치 | GPL 기준으로만 "배포 안 하니 괜찮다" | 수정 여부·제공 방식(법무 판단 — 해석·법률 자문 아님) | [17-4](../17-legal-standards/2-summary.md) |
| `member`에 `deleted_at`만, 행은 그대로 | 보존 기한·근거·분리 보관 개념 없음 | 기록 유형마다 `retain_until`과 근거가 있나 | [17-2](../17-legal-standards/2-summary.md) |
| 런북 인용 조문이 개정 전. law.go.kr 대조에서 법 제34조 `바뀐 곳 10`(2026-09-11 시행) | 인용 조문을 현행과 대조하지 않음 | 런북 인용 조문 목록 vs 현행 원문 | [17-5](../17-legal-standards/2-summary.md) |
| `DB_PASSWORD=dummy-not-real`이 이미지 안 `/app/.env`에서(Docker 29.1.3) | `.dockerignore` 없이 `COPY . .`. 뒤에서 `rm`해도 아래 레이어에 남음 | 이미지 레이어별 파일 목록 | [08-5](../08-container-image-optimization/2-summary.md) |
| 새 버전에서 라이선스 경고, 보안 패치가 새 라이선스 판에만(HashiCorp 2023-08-10, Redis 2024-03-20) | 라이선스를 도입 때 한 번만 봄 | 의존성 라이선스를 판마다 CI에서 확인 | [13-3](../13-build-vs-buy-and-adoption/2-summary.md) |

### 11. "사 온 것·만든 것이 발목을 잡는다"

```text
  도입 판단의 후유증
     │
     ├─ 1년째 자체 로그인·MFA를 고치는 중 ──────────────────────▶ 범용 기능 자체 구현        13-1
     ├─ 벤더 가격 인상·API 폐기 공지, 대안 없음 ─────────────────▶ 차별화 기능을 SaaS에       13-2
     ├─ 산 ERP를 고치느라 직접 개발비 초과 ──────────────────────▶ 범용 패키지 커스터마이징    13-4
     ├─ 같은 기능 사내 구현이 여럿 ─────────────────────────────▶ NIH (오만이 자아를 향함)   18-3
     └─ "가장 지저분한 모듈"부터 정리했는데 그 모듈은 1년에 한 번 바뀜 ───▶ 이자 대신 원금만 봄       10-3
```

| 보이는 것 (실험·출처) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 3년 TCO 예시: 좁게 보면 직접 6,000 vs 구독 10,800, 전체로 보면 직접 22,200 vs 구매 13,600(만원, 예시 가정 — JDK 21 결정적 계산) | 초기 개발비만 비교 | 유지보수·온콜·보안 패치가 계산에 들어 있나 | [13-1](../13-build-vs-buy-and-adoption/2-summary.md) |
| 같은 예시에서 구독료가 매년 약 46% 오르면 구매 + 종료비용이 직접보다 비싸짐 | 차별화 기능을 남과 같은 도구에, 종료 계획 없음 | 벤더 SDK가 몇 곳에 퍼졌나, 데이터 반출 형식 | [13-2](../13-build-vs-buy-and-adoption/2-summary.md) |
| 커스터마이징 비용 > 직접 개발비, 업그레이드 불가 | 업무 대신 소프트웨어를 바꿈(Fowler) | 커스터마이징마다 "차별화 요소인가" | [13-4](../13-build-vs-buy-and-adoption/2-summary.md) |
| 같은 기능의 사내 구현이 여럿 | 기준이 "나" | 직접 만들기 전 도입 판단을 거쳤나 | [18-3](../18-engineering-virtues/2-summary.md) |
| 정리한 모듈이 1년에 한 번 바뀜 | 변경 빈도(이자)를 안 봄(Fowler 2019) | 파일별 변경 횟수(실험: 복사본 4개 파일이 각 4회) | [10-3](../10-technical-debt/2-summary.md) |

### 12. "커밋이 사라졌다" — 또는 지운 것이 남았다

```text
  있어야 할 것이 없다 / 없어야 할 것이 있다
     │
     ├─ 동료의 커밋이 main에서 사라짐, 새 클론엔 아예 없음 ─────────▶ force push               03-1
     ├─ "안전한 강제 push"를 썼는데도 사라짐 ─────────────────────▶ fetch 뒤 --force-with-lease 03-3
     ├─ reset --hard 뒤 내 커밋이 안 보임 ───────────────────────▶ 이름표만 옮겨짐(reflog)     03-4
     ├─ 병합 뒤 고친 코드가 없음 ─────────────────────────────▶ 충돌 오해결                03-2
     └─ 지운 클래스가 운영에서 동작 ───────────────────────────▶ 증분 빌드 잔여물            07-5
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `+ 0fdcdac...ef56ee6 main -> main (forced update)`, 새 클론에서 `fatal: Not a valid object name 0fdcdac`, 서버엔 `unreachable commit 0fdcdac…`(git 2.43.0) | fast-forward 아닌 갱신을 `--force`로. bare 원격엔 reflog 없음 | 그 커밋을 아직 가진 사람(작성자 로컬·reflog) | [03-1](../03-version-control-and-git-internals/2-summary.md) |
| `--force-with-lease`가 통과(fetch 뒤). `--force-if-includes`를 붙이면 `(remote ref updated since checkout)`로 거부(git 2.43.0) | lease 기대값이 fetch로 최신이 됨 | IDE 백그라운드 fetch 설정 | [03-3](../03-version-control-and-git-internals/2-summary.md) |
| `git reset --hard origin/main` 뒤 로컬 커밋이 안 보임 | 커밋은 남고 이름표만 옮겨짐 | `git reflog`(도달 불가 reflog 기본 만료 30일) | [03-4](../03-version-control-and-git-internals/2-summary.md) |
| `git log`엔 있는데 코드엔 없음 | 충돌 해결에서 한쪽을 버림 | `git show --remerge-diff` | [03-2](../03-version-control-and-git-internals/2-summary.md) |
| jar 안에 소스 없는 `.class` | 출력 폴더를 비우지 않는 증분 빌드 | 산출물 vs 소스 목록 | [07-5](../07-build-systems-and-reproducibility/2-summary.md) |

### 13. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 왜 | leaf |
|---|---|---|---|
| 머지 지옥 | 큰 병합을 한 사람이 한 번에 풀기 | 상대 변경의 의도를 모르고 한쪽을 버린다 | [04-1](../04-branching-strategies/2-summary.md) · [03-2](../03-version-control-and-git-internals/2-summary.md) |
| CI 불신 | 게이트 끄기(`-Dpmd.skip=true`)·실패 테스트 삭제 | 새 회귀가 옛 빨강에 묻힌다 | [14-2](../14-quality-standards/2-summary.md) · [06-1](../06-ci-cd-pipelines/2-summary.md) |
| 배포 공포 | 배포를 모아서 드물게 | 한 번에 바뀌는 것이 커져 실패도, 원인 찾기도 커진다 | [06-5](../06-ci-cd-pipelines/2-summary.md) |
| 리뷰 병목 | 리뷰 생략·재촉 | 대기의 원인(큰 PR·느린 CI)은 그대로고 검증만 빠진다 | [18-2](../18-engineering-virtues/2-summary.md) · [05-1](../05-code-review/2-summary.md) |
| "이건 왜?" | 이유를 짐작해 지우거나 고치기 | 복사본·숨은 의존이 남는다. 먼저 `git log -S`·결정 기록 | [10-2](../10-technical-debt/2-summary.md) |
| 숫자는 좋은데 | 지표 목표를 더 올리기 | 지표를 맞추는 행동이 더 늘어난다 | [09-1](../09-dora-metrics/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인** — 이 노트 자체. "leaf 시나리오 → 증상"을 "증상 → leaf 시나리오"로 뒤집었다. 한 증상에 여러 leaf가 걸리고 한 leaf가 여러 증상에 걸린다(다대다).
- **결정 트리** — 각 절의 그림. 싼 질문(재실행·로컬 비교·해시 비교)부터 묻고 답에 따라 갈라진다.
- **콘텐츠 해시로 "같은가"를 묻기** — 증상의 상당수가 "같아야 할 두 개가 다르다"이다. 서버 8대의 산출물([06-3](../06-ci-cd-pipelines/2-summary.md)), 스테이징과 운영의 산출물([06-4](../06-ci-cd-pipelines/2-summary.md)), 같은 소스의 두 빌드([07-3](../07-build-systems-and-reproducibility/2-summary.md)), 캐시 키와 실제 입력([07-2](../07-build-systems-and-reproducibility/2-summary.md)). 해시가 같으면 같은 내용이다(충돌을 무시할 수 있는 해시 기준). git 객체 모델이 같은 원리다 — [03](../03-version-control-and-git-internals/2-summary.md), [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md).
- **DAG와 merge-base** — 머지 지옥의 크기는 merge-base 이후 양쪽 경로의 길이다([03](../03-version-control-and-git-internals/2-summary.md), [04](../04-branching-strategies/2-summary.md)). 빌드·파이프라인의 임계 경로는 DAG의 최장 경로다([06](../06-ci-cd-pipelines/2-summary.md), [07](../07-build-systems-and-reproducibility/2-summary.md)).
- **이분 탐색** — "언제부터 깨졌나"는 `git bisect`로 커밋 이력을 이분 탐색한다. 이력 n개에서 약 log₂ n번 빌드·테스트로 첫 나쁜 커밋을 찾는다(예: 1,000커밋이면 약 10번).
- **분포와 백분위** — 일정 증상(6절)은 점이 아니라 분포의 문제다. 몬테카를로로 합의 분포를 만든다([12](../12-estimation-and-planning/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

```text
  ① 원문을 모은다     메시지·출력 전체, 도구 판, 커밋·서버·환경
  ② 칸을 정한다       흐름(0절)의 어느 칸에서 처음 보였나 → 1~12절 중 하나
  ③ 한두 칸 앞을 본다  리뷰 대기 → 머지 지옥, 느린 CI → 큰 배치 → 배포 공포
  ④ 싼 질문부터       재실행하면? 로컬에선? 해시가 같은가? 언제부터?(bisect)
  ⑤ leaf로 간다       표의 NN-k 시나리오의 "대처"를 읽고, 그 leaf의 실험을 다시 돌려 본다
```

### 2. 첫 진단 명령 모음

```bash
# 머지 지옥: 얼마나 갈라졌나 (왼쪽 = main에만, 오른쪽 = feature에만)
git rev-list --left-right --count main...feature

# 충돌 해결 내용 리뷰 / 사라진 코드 찾기 (git 2.36+의 --remerge-diff)
git show --remerge-diff <merge-commit>
git log -m -S 'if (amount <= 0) return 0;' --oneline   # -m: 병합 커밋의 diff도 본다

# 언제부터 깨졌나: 이력 이분 탐색
git bisect start <bad> <good>
git bisect run mvn -q -o test

# 릴리스 브랜치에만 있는 수정 (+ = main에서 같은 패치를 못 찾음 — 다른 코드로 고쳤을 수는 있다)
git cherry -v main release/1.2

# 배포 공포: 서버별 산출물 해시 종류 수 (1이면 일치)
for h in s1 s2 s3 s4 s5 s6 s7 s8; do ssh "$h" sha256sum /opt/app/app.jar; done | awk '{print $1}' | sort | uniq -c

# 이미지 레이어별 크기와 만든 명령
docker history --no-trunc <image>
```

- `git bisect run`은 명령의 종료 코드로 좋고 나쁨을 판단한다(0 = 좋음, 125 = 건너뜀, 그 밖의 1~127 = 나쁨, 그 밖의 값(128 이상)은 bisect 자체를 중단 — git-bisect 문서, git 2.43.0 man 페이지로 확인). 파이프로 종료 코드를 가리지 않는다.
- `ssh` 반복문은 진단 예시다. 운영에서는 배포 도구가 인벤토리 전체의 실행 버전을 보고하게 한다([06-3](../06-ci-cd-pipelines/2-summary.md)).

### 3. 배포 뒤 "인스턴스가 다 같은 판인가"를 코드로 — Java

배포 공포(3절)와 Knight형 사고([20](../20-practice-incidents/2-summary.md))의 첫 진단을 자동화한 모양이다. 각 인스턴스의 `/version`이 빌드 해시를 돌려준다고 가정한다(가정 — 엔드포인트 이름은 예시).

```java
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import java.util.stream.*;

public class VersionDrift {
    public static void main(String[] args) throws Exception {
        List<String> hosts = List.of(args);                 // 인벤토리 전체(사람이 친 목록이 아니라)
        HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(2)).build();
        Map<String, List<String>> byHash = new TreeMap<>();
        for (String h : hosts) {
            String hash;
            try {
                var res = http.send(HttpRequest.newBuilder(URI.create("http://" + h + "/version"))
                        .timeout(Duration.ofSeconds(2)).build(), HttpResponse.BodyHandlers.ofString());
                hash = res.statusCode() == 200 ? res.body().strip() : "HTTP " + res.statusCode();
            } catch (Exception e) {
                hash = "UNREACHABLE";                       // 응답 없음은 실패로 센다
            }
            byHash.computeIfAbsent(hash, k -> new ArrayList<>()).add(h);
        }
        byHash.forEach((k, v) -> System.out.println(v.size() + "  " + k + "  " + v));
        boolean anyFailed = byHash.keySet().stream()
                .anyMatch(k -> k.equals("UNREACHABLE") || k.startsWith("HTTP "));
        System.exit(byHash.size() == 1 && !anyFailed ? 0 : 1);  // 종류가 2개 이상이거나 응답 실패가 하나라도 있으면 배포 실패
    }
}
```

- 응답하지 않는 인스턴스를 건너뛰지 않고 실패로 센다. 건너뛰면 Knight의 8번째 서버 같은 것이 조용히 빠진다.
- 해시 종류가 1개인지만 보면 안 된다. 모든 인스턴스가 `UNREACHABLE`(또는 같은 HTTP 오류)이면 종류가 1개라 성공으로 끝난다. 그래서 응답 실패가 하나라도 있으면 따로 실패시킨다.

## 장애 시나리오와 대처

### 1. 증상만 끄는 처방 — 게이트 끄기·날짜 올리기·재촉

- **현상**: CI는 초록, 신선도 대시보드도 초록, 리뷰 대기도 짧아졌다. 그런데 사고와 재작업은 그대로다.
- **보이는 형태**: CI 설정에 `-Dpmd.skip=true`([14-2](../14-quality-standards/2-summary.md)), 날짜만 바뀐 문서 커밋(경고 7건 → 4건, [11-5](../11-documentation-practices/2-summary.md)), 리뷰 없이 머지된 PR과 그 뒤 롤백([18-2](../18-engineering-virtues/2-summary.md)).
- **원인**: 증상(빨강·경고·대기)을 없애는 것과 원인을 고치는 것을 혼동했다.
- **대처**: 증상을 끄는 변경(게이트 비활성화, 기준선 재생성, 검토일만 갱신)은 리뷰에서 원인 설명을 요구한다. 끈 게이트 수·억제 주석 수를 따로 센다.

### 2. 같은 증상에 반대 처방 — "CI가 빨갛다"를 하나로 봄

- **현상**: CI 빨강이 잦아 팀이 "불안정 테스트"로 결론 내리고 재시도를 켰다. 다음 달 병합 뒤 main이 깨지는 일이 계속된다.
- **보이는 형태**: 재시도로 초록이 된 실행 비율이 높다. 깨진 실행의 상당수는 재실행해도 빨갛고, 병합 직후에 몰린다.
- **원인**: 불안정 테스트(재실행하면 바뀜), 의미 충돌(병합 결과에서만 빨강, [06-2](../06-ci-cd-pipelines/2-summary.md)), 환경 의존(로컬에선 초록, [07-1](../07-build-systems-and-reproducibility/2-summary.md))을 구별하지 않았다.
- **대처**: 2절의 결정 트리 순서로 가른다 — 재실행하면 바뀌나, 병합 결과에서만인가, 로컬과 CI가 다른가. 처방은 각각 격리·추적, 병합 큐, 입력 고정이다.

### 3. 증상이 보인 칸을 원인 칸으로 착각

- **현상**: 머지 지옥을 풀려고 병합 도구와 충돌 해결 교육에 투자했다. 몇 달 뒤 같은 고통이 돌아온다.
- **보이는 형태**: 브랜치 수명의 대부분이 리뷰 대기다. 또는 파이프라인이 느려 변경을 모아 올린다.
- **원인**: 증상은 통합 칸에서 보였지만 원인은 리뷰 칸([05-2](../05-code-review/2-summary.md))이나 CI 칸([06-5](../06-ci-cd-pipelines/2-summary.md))에 있었다.
- **대처**: 증상 칸의 한두 칸 앞(왼쪽)을 함께 잰다(0절). 브랜치 수명을 "작성 / 리뷰 대기 / CI 대기"로 나눠 어디가 긴지 본다.

### 4. 지표로 증상을 재다가 지표가 증상이 됨

- **현상**: 증상(배포가 드물다, 문서가 낡았다, 품질이 낮다)을 지표로 재기 시작했고 그 지표를 목표로 걸었다. 지표는 좋아졌다.
- **보이는 형태**: 7절의 모양들 — 새 커밋 없는 배포 17회([09-1](../09-dora-metrics/2-summary.md)), `unused…` 이름([14-4](../14-quality-standards/2-summary.md)), 억제 주석([10-5](../10-technical-debt/2-summary.md)).
- **원인**: 측정이 목표가 되면 측정을 맞추는 행동이 나온다(굿하트).
- **대처**: 지표는 "어디를 볼지" 정하는 데 쓴다. 지표마다 그것을 속이는 가장 싼 방법을 미리 적고, 그 방법의 흔적(원시 이벤트)을 따로 센다.

### 5. 사람 탓으로 결론 — "누가 실수했다"에서 멈춤

- **현상**: 사고 회고가 "작업자가 서버 하나를 빠뜨렸다", "리뷰어가 대충 봤다"로 끝난다. 같은 모양의 사고가 다른 사람에게서 다시 난다.
- **보이는 형태**: 재발 방지 항목이 "주의하자", "교육"뿐이다. 회고 기록에 같은 문장이 반복된다([01-1](../01-lifecycle-and-agile/2-summary.md)).
- **원인**: 사람의 실수를 가능하게 만든 구조(수동 목록, 검증 단계 없음, 거대 PR)를 보지 않았다. Knight 사건에서 SEC가 지적한 것도 개인의 실수가 아니라 2차 확인 절차·서면 절차의 부재였다([20](../20-practice-incidents/2-summary.md)).
- **대처**: "그 실수가 왜 가능했나, 어느 장치가 그것을 잡았어야 했나"를 묻는다. 대처는 장치(자동 검증, 크기 상한, 체크리스트의 자동화)로 적는다. 사고 회고 형식은 [reliability/26](../../reliability/26-incident-response-and-postmortem/2-summary.md).

## 핵심 문장

- 이 노트는 **증상 → 흐름의 칸 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 엔지니어링 실천의 증상은 변경의 흐름(작성 → 리뷰 → 통합 → 빌드 → 배포 → 운영 → 기억) 위에서 보인다. 한 칸이 막히면 앞 칸에 일이 쌓이므로, 증상 칸의 한두 칸 앞(왼쪽)을 함께 본다.
- 머지 지옥·배포 공포·CI 불신의 공통 처방은 "작게, 자주, 그리고 확인 수단과 함께"다. 확인 수단 없이 자주 하면 공포가 합리적이다.
- "같아야 할 두 개가 다르다"는 증상이 많다. 서버별 산출물, 환경별 산출물, 같은 소스의 두 빌드를 해시로 비교하는 것이 가장 싼 첫 진단이다.
- "숫자는 좋아졌는데 나아진 게 없다"는 이 영역의 반복 패턴이다. 지표를 목표로 걸면 지표를 맞추는 행동이 나오므로, 지표를 속이는 가장 싼 방법의 흔적을 따로 센다.
- 회고가 "누가 실수했다"에서 멈추면 같은 사고가 다른 사람에게서 다시 난다. 실수를 가능하게 한 구조를 장치로 고친다.

## 관련 주제·근거

- 선행: 이 영역 leaf 01~18 전체([../README.md](../README.md)). 이 노트의 `NN-k` 링크는 각 leaf 「장애 시나리오와 대처」의 `### k.` 시나리오를 가리킨다.
- leaf 노트
  - [01-lifecycle-and-agile](../01-lifecycle-and-agile/2-summary.md) · [02-requirements-engineering](../02-requirements-engineering/2-summary.md) · [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md) — 수명 주기, 요구, 추정
  - [03-version-control-and-git-internals](../03-version-control-and-git-internals/2-summary.md) · [04-branching-strategies](../04-branching-strategies/2-summary.md) · [05-code-review](../05-code-review/2-summary.md) — git, 브랜치, 리뷰
  - [06-ci-cd-pipelines](../06-ci-cd-pipelines/2-summary.md) · [07-build-systems-and-reproducibility](../07-build-systems-and-reproducibility/2-summary.md) · [08-container-image-optimization](../08-container-image-optimization/2-summary.md) — 파이프라인, 빌드, 이미지
  - [09-dora-metrics](../09-dora-metrics/2-summary.md) · [10-technical-debt](../10-technical-debt/2-summary.md) · [11-documentation-practices](../11-documentation-practices/2-summary.md) · [13-build-vs-buy-and-adoption](../13-build-vs-buy-and-adoption/2-summary.md) — 지표, 부채, 문서, 도입
  - [14-quality-standards](../14-quality-standards/2-summary.md) · [15-security-standards](../15-security-standards/2-summary.md) · [16-operational-standards](../16-operational-standards/2-summary.md) · [17-legal-standards](../17-legal-standards/2-summary.md) · [18-engineering-virtues](../18-engineering-virtues/2-summary.md) — 표준 4축, 태도
- 후속: [20-practice-incidents](../20-practice-incidents/2-summary.md) — 실사건(Knight Capital 2012, Cloudflare 2019)에서 3절 "배포 공포"의 원인들이 어떻게 겹쳤나
- 다른 영역 색인: [testing/20-test-symptom-index](../../testing/20-test-symptom-index/2-summary.md)(불안정 테스트·초록인데 운영 장애) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [software-design/55-design-symptom-index](../../software-design/55-design-symptom-index/2-summary.md) · [api-design/28-api-symptom-index](../../api-design/28-api-symptom-index/2-summary.md) · [web-platform/23-web-symptom-index](../../web-platform/23-web-symptom-index/2-summary.md)
- 운영 쪽 정본: [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) · [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) · [reliability/26-incident-response-and-postmortem](../../reliability/26-incident-response-and-postmortem/2-summary.md) · [reliability/44-runbooks-and-operational-readiness](../../reliability/44-runbooks-and-operational-readiness/2-summary.md) · 결정 기록 [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md)
- 근거 문서
  - git-bisect 문서 — `bisect run` 종료 코드 규칙 <https://git-scm.com/docs/git-bisect>
  - git-show `--remerge-diff`(git 2.36+) — 03 노트에서 확인한 범위 <https://git-scm.com/docs/git-show>
  - 표의 수치·메시지는 각 leaf의 실험 출력과 인용을 따른다: git 2.43.0(03·04·05·09·10·11), JDK 21.0.12 temurin(01·02·04·07·10·12·13·14·15·16·17), Maven 3.9.16(07·14·15·17)·JDK 21.0.11(07 재현 빌드), maven-jar-plugin 3.5.1·maven-compiler-plugin 3.15.0(07), GNU Make 4.3(07), Docker Engine 29.1.3 레거시 빌더·Alpine 3.24.1(08), Node 18.19.1(04·05·09·11·13), PMD 7.7.0·maven-pmd-plugin 3.26.0(14), SpotBugs 4.9.3·FindSecBugs 1.14.0(15), api.osv.dev 2026-10-05(15), Logback 1.5.12·SLF4J 2.0.16(16), license-maven-plugin 2.4.0(17), law.go.kr DRF 2026-10-05(17). 외부 수치(Cisco 사례 연구·Sadowski 2018·SWE@G 10장·DORA)는 05·09·11 노트의 인용이다.
- 실험 목록
  - 이 노트는 새 실험을 돌리지 않았다(종합 노트 — 브리핑 §5에서 선택). 메시지·수치는 leaf 01~18의 실험 출력에서 옮겼다(2026-10-05 판).
  - 대조: leaf 01~18의 「장애 시나리오와 대처」를 스크립트로 다시 뽑아(`### k.` 87개), 이 노트에 87개가 모두 `[NN-k](../NN-slug/2-summary.md)`로 걸렸는지, 링크 경로가 실재하는지 확인했다(`scratchpad/ep/19/work/verify19.py`). 표의 메시지·수치는 각 leaf 실험 출력 블록과 다시 대조했다.
