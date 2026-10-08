# study-note 전체 색인 (2026-09-28 기준)

이 저장소의 최상위 지도다. 폴더마다 성격이 다르므로, 무엇을 찾을 때 어디로 가는지를 이 표 하나로 정한다. 각 폴더의 진행 상태와 세부 목록은 그 폴더의 index가 정본이고, 이 문서는 구조와 입구만 담는다.

| 폴더 | 성격 | 현재 규모 | 입구 |
|------|------|----------|------|
| [cs](cs/) | 개념 지식 — 질문/서머리/정답 3종 루프 (작성 규칙: [cs/README.md](cs/README.md)) | 커리큘럼 19영역·644 주제(영역 README = 생성 문서) + 기존 컬렉션(myway 5종·foundations·systems·engineering) | [cs/index.md](cs/index.md) |
| [languages](languages/) | 언어 레퍼런스 — 언어별 문법·표준 API(syntax 3파일)·언어 특성·브라우저 Web API (cs 밖) | 13개 언어(c·cpp·csharp·css·go·html·java·js·kotlin·python·rust·sql·ts) + web-api | [languages/README.md](languages/README.md) |
| [issue](issue/) | 실전 이슈에서 뽑은 CS 패턴 카드 — 질문/서머리/정답·방안 비교 (하네스 issue-archive 대상) | 카드 162 — cross-cutting·java·kotlin·python·rust·shell·typescript | [issue/README.md](issue/README.md) |
| [opensource](opensource/) | 오픈소스 기여·코드 읽기 아카이브 — PR별 표준 5종 + concepts + 아키텍처 지도 | spring-framework · spring-security · elasticsearch · nextjs · react · mysql · postgres · keycloak · nginx · redis | [opensource/index.md](opensource/index.md) |
| [practice](practice/) | 훈련 — 문제를 풀고 남기는 기록 | programmers (챕터별) | [practice/index.md](practice/index.md) |
| [project](project/) | 만든 것의 기록 — 이슈 단위 해설 | db-engine · study-note-deploy-system · jun-bank | [project/index.md](project/index.md) |
| [lab](lab/) | 실험 프로젝트 — 가설과 측정 | 9건 (backend-labs 17랩 스캐폴드 · cache-lab · redis-atomicity-lab 등) | [lab/index.md](lab/index.md) |
| [portfolio](portfolio/) | 대외용 산문 정리 — project·lab에서 추림 | markview · k-brand-guard | [portfolio/index.md](portfolio/index.md) |
| [history](history/) | 기술 변천사 — 왜 지금 모양이 되었나(읽는 문서) | 8주제 91편 (database·java·js·network·python·rust·spring·web) | [history/README.md](history/README.md) |
| [독후감](독후감/) | 책 후기 — 책=폴더, 챕터별 | 아키텍트-첫걸음 | [독후감/index.md](독후감/index.md) |
| [세미나](세미나/) | 컨퍼런스·세미나 후기 | nerdcon | [세미나/index.md](세미나/index.md) |
| [reference](reference/) | 작성·공부 방법의 근거 문서 | study-note-guide · organize-guide · render-rules · writing · learning · tools | [reference/index.md](reference/index.md) |
| [templates](templates/) | 1-question/2-summary/3-answer 포맷 | 3종 + project-issue | [templates/README.md](templates/README.md) |
| [workflow](workflow/) | 이 저장소 배포 시스템의 동작 흐름 문서 | content · sync · search · chat-design · streaming · deploy · logging | [workflow/README.md](workflow/README.md) |

구조 규칙 세 가지가 전체를 관통한다. 첫째, 배포 트리는 "하위 폴더 없이 md만 있는 폴더"를 주제(리프)로 렌더하므로 리프 폴더에는 md만 둔다. 둘째, 단일 문서 주제는 폴더명과 같은 이름의 md 하나로 둔다(`concepts/stored-procedure/stored-procedure.md`). 셋째, 각 갈래의 진행 상태는 그 갈래의 index.md에서만 갱신하고 이 문서는 구조가 바뀔 때만 고친다.

문체와 형식의 정본은 [reference/writing/README.md](reference/writing/README.md)(작성 방법론)이고, 공부 루프의 원리는 [README.md](README.md)에 있다.
