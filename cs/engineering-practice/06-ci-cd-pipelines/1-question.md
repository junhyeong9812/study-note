# engineering-practice/06-ci-cd-pipelines — 질문

## 질문

1. (왜) 지속적 통합이 없으면 무엇이 몰리나? "CI 서버를 깔았다"와 "CI를 한다"는 무엇이 다른가(Fowler의 실천 하나를 들어라)?
2. (경계) 지속적 통합·지속적 전달·지속적 배포를 한 문장씩 구분하라. 약어 CD를 읽을 때 무엇을 확인해야 하나?
3. (그림·계산) checkout(1)→compile(3)·lint(2), compile→unit-test(5)·integration-test(8), unit-test·integration-test·lint→package(2)→deploy-staging(3)→smoke(2)→deploy-prod(3)인 파이프라인(분, 예시)을 DAG로 그려라. 모든 작업을 차례로 돌린 합과, 의존만 지키며 병렬로 돌린 총 시간은? 총 시간을 줄이려면 어느 작업을 줄여야 하나?
4. (예측) 3번 파이프라인에서 unit-test가 실패하면 integration-test와 package 이후 작업은 각각 어떻게 되나? GitHub Actions의 `needs` 규칙으로도 설명하라.
5. (예측) 브랜치 A는 `Price.total(unit, qty)`를 `totalWithTax(unit, qty, rate)`로 바꾸고 호출처를 고쳤다. 브랜치 B는 새 파일에서 `Price.total(500, 2)`를 호출한다. 각 브랜치의 CI, `git merge` 결과, 병합된 main의 컴파일은 각각 어떻게 되나? 이 현상의 이름(Fowler·SWE@G)과 막는 법은?
6. (연결) 커밋 단계에 어떤 테스트를 넣고 어떤 테스트를 뒤로 미루나? Humble–Farley의 시간 기준과 SWE@G의 presubmit 기준을 들어라.
7. (장애 진단) main이 사흘째 빨갛고 팀은 "원래 깨진 테스트"라며 병합을 계속한다. 무엇이 위험하고, 무엇부터 하나? "초록이 아니면 아무도 커밋 금지" 정책에 대해 SWE@G는 어떻게 말하나?
8. (장애 진단) 배포 뒤 일부 인스턴스에서만 이상 동작이 나온다. Knight Capital 사례에서 어떤 절차 결함이 겹쳤나? 파이프라인에 무엇을 넣으면 같은 누락을 잡나?
9. (경계) "스테이징용으로 한 번, 운영용으로 한 번 소스에서 빌드한다"는 무엇이 문제인가? Humble–Farley의 어떤 실천과 어긋나며, 07·08과 어떻게 이어지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
