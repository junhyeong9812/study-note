# software-design/03-deep-modules-and-abstraction — 질문

## 질문

1. (왜) 모듈 경계를 많이 그으면 왜 꼭 단순해지지 않나? 깊은 모듈과 얕은 모듈을 그림 하나로 구분하라.
2. (경계) 깊이는 줄 수로 재나? Unix 파일 입출력과 setter·통과 메서드를 깊이로 비교하라.
3. (예측) 1 MiB 파일을 1바이트씩 읽을 때 `FileInputStream`, `BufferedInputStream`, `Files.newInputStream`의 시간은 어떻게 갈리나? 읽은 바이트 수는?
4. (왜) 실험 3의 결과를 "흔한 경우를 단순하게"라는 원칙으로 설명하라. `Files.newBufferedReader(Path)`는 무엇과 같은가?
5. (예측) 특수 목적 Text(backspace·delete·deleteSelection)와 범용 Text(insert·delete·changePosition)에 단어 삭제 2종을 추가하면 바뀐 파일 수와 Text 공개 메서드 수는?
6. (경계) 실험 5에서 줄 수는 왜 같았나? 범용 설계의 이득이 작게 보인 이유와 남은 숙제는?
7. (예측) Controller → Service → Manager → Dao(가운데 둘은 통과)와 Controller → Dao에 `includeDeleted` 인자를 추가하면 diff와 Dao에서 센 스택 깊이는?
8. (경계) 가운데 계층이 있으면 무조건 통과 계층인가? 무엇을 보고 판단하나?
9. (장애 진단) 모든 시그니처에 `tenantId`가 붙어 있고 새 값을 내려보낼 때마다 수십 파일이 바뀐다. 이름과 처방은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
