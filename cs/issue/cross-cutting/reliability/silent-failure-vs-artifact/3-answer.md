# cs/issue/cross-cutting/reliability/silent-failure-vs-artifact — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답

<!-- 질문 1:1 대응 -->

1. **성공 신호는 "됐다는 주장", 산출물은 "됐다면 남았을 흔적"이다.** 로그의 success·exit 0·HTTP 202는 전부 어떤 단계가 스스로 보고한 값이다 — 그 단계가 실패를 삼켰거나 성공/실패를 잘못 판정했으면 그 값은 거짓이 된다. 산출물은 그 일이 정말 일어났어야만 존재하는 독립된 증거(저장된 레코드 수, 컨테이너의 실제 이미지, 응답하는 헬스 URL)라서, 신호를 믿는 대신 산출물을 되물으면 삼켜진 실패가 드러난다.
   > **산출물(artifact)** — 작업이 실제로 완료됐다면 관찰 가능하게 남았어야 하는 결과물. 신호와 달리 작업 주체의 자기보고에 의존하지 않는다.

2. silent failure는 **실패가 발생했지만 그 실패가 호출자·상위 단계로 전파되지 못한** 상태다. "실패가 났다"는 정상(시끄럽게 알리면 됨)이고, 문제는 "실패가 신호에 반영되지 않는 것"이다. 흔한 원인 셋: (a) 예외를 의도적으로 삼키는 경로("실패해도 무해" 설계), (b) 성공과 실패를 구분 못 하는 호출(4xx/5xx를 성공으로 받는 `curl`), (c) 실패를 실패로 안 보는 관대한 도구(없는 산출물을 오류로 안 보는 빌드, 상태코드만 보는 healthcheck).
   > **silent failure(조용한 실패)** — 실패했는데도 성공 신호가 나가, 아무도 실패를 알아채지 못하는 사고 유형.

3. B가 실패를 삼키고 성공을 반환하면, C는 "B가 됐다"를 전제로 자기 일을 하거나 건너뛰고, 최종 success는 "A·B·C가 다 됐다"가 아니라 **"아무도 실패를 보고하지 않았다"** 만 의미하게 된다. 신뢰의 사슬은 가장 약한 고리(실패를 삼키는 단계)에서 끊기고, 그 뒤로 전달되는 모든 신호가 거짓이 된다. 그래서 파이프라인의 "성공"은 각 단계가 **실패를 전파해야만** 의미가 있다.

4. 네 가지의 공통 구조는 **"주장을 무시하고 독립된 산출물을 되묻는다"** 이다. (a) 넣으려던 청크 수와 저장소가 실제로 가진 수를 비교, (b) 배포 로그 대신 `docker inspect`로 이미지·생성 시각, (c) 빌드 성공 메시지 대신 라우트 표를 grep, (d) exit 코드 대신 헬스 URL로 실제 요청. 넷 다 "그 일이 됐다면 X가 참이어야 한다"는 **사후 조건(postcondition)** 을 세우고 X를 직접 측정한다.
   > **사후 조건(postcondition)** — 연산이 성공적으로 끝났다면 반드시 참이어야 하는 상태. 검증은 이것을 신호가 아니라 실측으로 확인한다.

5. 일반화: **"접수/기동/시작"을 알리는 신호를 "완료/정상/반영"으로 오해하지 마라.** 202는 요청을 큐에 넣었다는 뜻이고 실제 처리는 뒤에서 일어나며 실패할 수 있다. `compose up` 종료 0은 컨테이너를 띄우라고 도커에 지시했다는 뜻이고, 그 안의 프로세스가 즉시 크래시 루프에 빠져도 도커는 "띄웠음"이라 답한다. 둘 다 **"명령을 접수한 시점의 신호"를 "결과가 확정된 시점의 신호"로 착각**하는 함정이다.

6. 검증 코드가 틀리면(예: 에러 상세를 넣으려던 문자열 템플릿을 잘못 써 진짜 에러가 리터럴로 가려짐) 실패는 나는데 원인이 안 보여 디버깅 비용이 배가 된다. 검증 도구가 관대하면(없는 라우트를 오류로 안 봄, 상태코드만 보는 healthcheck) **실패 자체가 초록불로 바뀐다.** "테스트 초록불인데 제품이 틀렸다"는, 검증 장치가 계약이 아니라 엉뚱한 것을 재고 있어 *검증이라는 산출물마저 거짓 성공 신호가 된* 특수한 silent failure다. 그래서 "테스트 통과 ≠ 검증 완료"이고, 검증기 자신도 실측으로 한 번 의심해야 한다(그린 위장 점검).

7. 데이터 작업은 "예외가 안 났다"가 "다 들어갔다"를 보장하지 않는다 — bulk 저장이 부분 실패해도 예외 없이 끝날 수 있고, 필터가 조용히 레코드를 스킵하거나 인코딩이 값을 절단해도 프로세스는 성공으로 끝난다. 그래서 record-level 검증이 필요하다: **count**(넣으려던 수 == 저장된 수), **sample**(표본을 되읽어 내용 확인), **orphan 정리**(더 이상 소스에 없는데 저장소에 남은 것 제거). 이것만이 부분 실패·무음 스킵·조용한 절단을 명시적으로 반증한다.
   > **record-level 검증** — 집계 성공 여부가 아니라 개별 레코드 수·내용·정합성을 실제로 세어 확인하는 것. 데이터 사고의 최다 유형인 silent failure를 잡는 최후 방어선.

## 이번 프로젝트 사례

- [backend/issue2](../../../../../project/study-note-deploy-system/backend/issue2/) — bulk 색인 후 `count(path) == 청크 수`를 되물어 "돌았다"가 아니라 "들어갔다"를 검증(코드 `IndexingService.kt`의 `check(count == doc.chunks.size.toLong())`), 그리고 에러 메시지 조립 버그(`$response` 리터럴)가 진짜 UTF-8 에러를 가렸던 사례.
- [backend/issue10](../../../../../project/study-note-deploy-system/backend/issue10/) — 머지·Actions 초록불인데 운영에 필드가 없던 사건. 배포 `curl`에 `-f`가 없어 401 거절이 성공으로 위장됐고, "초록불" 대신 운영 실값·배포 이력·http 코드로 좁혀 원인을 잡았다.
- [front/issue3](../../../../../project/study-note-deploy-system/front/issue3/) — 리다이렉션(`> 경로`)이 없는 디렉토리 때문에 실패했는데 Next 빌드는 성공. "빌드 성공 로그"가 아니라 **빌드 라우트 표에 기대 경로가 있나**를 산출물로 확인.
- [llm/issue1](../../../../../project/study-note-deploy-system/llm/issue1/) — 모델 미설치인데 `/health`가 200(몸통만 model_missing)을 줘 docker healthcheck가 healthy로 판정. 부재를 503으로 바꿔(`api.py` model_missing→503) "정상인 척"을 막았다.
- [llm/issue3](../../../../../project/study-note-deploy-system/llm/issue3/) — `python -m pytest`로는 통과하고 `pytest`로는 import 에러로 죽던 환경 차이. "누가 맞나 따지지 말고 직접 실행해 재현"으로 초록불 위장을 실측으로 갈랐다.
- [ci-cd/issue2](../../../../../project/study-note-deploy-system/ci-cd/issue2/) — `compose pull wrapper`가 610ms에 "deploy ok"를 찍었지만 `image:`+`build:` 병존 때문에 실제로는 Skipped. "성공 로그" 대신 `docker inspect`의 실제 이미지·생성 시각(산출물)을 봐야 했다.
- [ci-cd/issue3](../../../../../project/study-note-deploy-system/ci-cd/issue3/) — F7: `compose up` 종료 0 ≠ 서비스 정상. 배포 후 헬스 URL을 90초 폴링해 200을 받아야 진짜 ok(코드 `agent.go`의 `waitHealthy(healthURL, 90*time.Second)`). F6: master의 202(접수)를 배포됨으로 오해하던 무음 유실을 접수 시점 409로 교정.

## 검증 기록

- 2026-09-23: 이슈 README 7건 + 코드 대조 작성 (Claude 초안). 코드 확인: `backend .../indexing/usecase/IndexingService.kt` L53·L73-74 (vectors/count 검증), `llm .../app/api.py` L111-112 (model_missing→503), `ci-cd .../agent/agent.go` L95-98·L135 (waitHealthy 90s), `ci-cd .../master/master.go` L87-93 (per-service inFlight 409).
