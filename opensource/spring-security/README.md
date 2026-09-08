# spring-security — 업스트림 기여 학습 아카이브

이 폴더는 Spring Security 업스트림 기여(2026-06~) 과정에서 작성한 학습 문서의 아카이브다.
기여 자체는 작업 repo(spring-security fork)에서 이루어졌고, 그 repo의 `analyze-docs/`에
core 모듈 분석 노트와 버그 헌트 기록이 남아 있다. 이 폴더는 그 원자료에서 **PR로 이어진
것**만 골라 처음 보는 사람이 재구성할 수 있는 형태로 다시 쓴 것이다. **이후의 새 기여
문서는 이 폴더에 직접 작성한다.**

구성은 `prs/` 한 갈래다. PR 하나당 주제 폴더 하나로, 표준 4종 문서(README 해설,
tests 테스트 해설, structure 실구조, analysis 착수 분석)가 탭으로 배포된다.
spring-framework 아카이브의 다섯째 문서(gates 이해 게이트 기록)는 이 세 건에 해당하는
원자료가 없어 만들지 않았다 - 각 폴더 README가 그 사실을 명시한다. 개념 문서(`concepts/`)는
아직 없다.

세 건 모두 2026-06-14 하루의 버그 헌트에서 나왔다. core 모듈 14개 패키지군을 병렬
에이전트로 감사해 후보 10건을 모으고, 메인이 전수 재현 검증(9건 확정 / 1건 반증)한 뒤,
착수 전 중복 리서치로 이미 남이 제출한 2건을 걸러 내고 남은 것 중 셋을 PR로 냈다. 그
과정의 원자료 위치는 아래와 같다.

| 원자료 | 위치(fork repo) | 내용 |
|---|---|---|
| core 모듈 분석 | `analyze-docs/core/00~03` | 전체 구조·기반 타입·인증·인가 해설 |
| 버그 후보 대장 | `analyze-docs/core/BUGS-후보.md` | 후보 10건 + 검증 결과 |
| 세션 종합 | `analyze-docs/plans/2026-06-14/spring-security-core-bug-hunt/` | findings·중복 리서치·후보별 task/해설/changelog/review-log |

`analyze-docs/`는 fork repo의 git에서 제외돼 있어(`.git/info/exclude`) 로컬에만 존재한다.
이 아카이브가 그 기록의 공개 가능한 요약본 역할을 한다.

## 작성 규칙 (이 폴더의 계약)

- 배포 트리 규칙: 주제(리프) = 하위 폴더 없이 md만 있는 폴더. PR 주제 폴더 안에 하위
  폴더를 만들지 않는다. 단일 문서 개념은 `<슬러그>/<슬러그>.md`.
- 폴더명은 영문 슬러그: PR은 `<번호>-<내용-kebab>`, 개념은 내용 kebab.
- 문체는 study-note 작성 방법론(`reference/writing/README.md`)을 따른다: 산문, 절마다
  topic sentence, 결론 앞, 표는 고정 차원 비교 + lead-in, 이모지·유니코드 특수기호
  금지(ASCII 다이어그램 허용).
- 코드 스니펫은 실파일에서 복사하고 `파일:line`을 표기한다. 좌표가 수정 전인지 후인지를
  문서 머리에 밝힌다.
- 새 PR마다 표준 4종을 채우고 아래 대장에 한 줄을 더한다. 자료가 받쳐 주지 않는 문서는
  만들지 않되, 그 사실을 그 폴더 README에 "이 PR은 N종 구성"으로 명시한다.

## PR 대장

| 폴더 | 상태 | 한 줄 주제 |
|---|---|---|
| prs/19335-anonymous-additional-authorization | 리뷰 대기 (waiting-for-triage) | anonymous()가 javadoc이 제외한 부가 인가를 적용 |
| prs/19337-inmemory-changepassword-case | 머지 2026-08-13 (9fdd2dc6758, 7.0.x, 7.0.7) | changePassword만 조회 키 소문자화 누락 |
| prs/19339-reactive-session-registry-atomic | 리뷰 대기 (waiting-for-triage) | 리액티브 세션 레지스트리의 비원자 save/remove |

상태는 2026-09-08 기준이다. 이후 변동은 각 폴더 README와 이 표를 함께 갱신한다.
