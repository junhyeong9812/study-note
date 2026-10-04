# engineering-practice/08-container-image-optimization — 질문

## 질문

1. (왜) 이미지 크기가 빌드 시간 말고 운영의 어떤 순간들(스케일 아웃·롤백)에 영향을 주나? 노드에 베이스 레이어가 이미 있으면 무엇이 달라지나?
2. (그림) 이미지를 레이어 스택으로 그리고, 레이어가 해시로 이름 붙는 것이 저장·전송에 주는 이득을 설명하라. `RUN rm -rf /opt/java`가 이미지를 줄이지 못하는 이유는(실험의 바이트 수로)?
3. (예측) `COPY . .` → `RUN 의존성 설치` → `RUN 컴파일` 순서의 Dockerfile에서 (a) 소스 한 줄 수정, (b) 컨텍스트에 무관한 로그 파일 생성, (c) 소스 파일 `touch`만 — 각각 어디부터 다시 실행되나? 순서를 바꾼 Dockerfile에서는? 실험의 시간은?
4. (예측) 같은 Java 앱을 JDK 단일 스테이지, JDK→JRE 멀티스테이지, jlink 런타임으로 만들면 크기·레이어 수는 실험에서 어떻게 나왔나? 단일 스테이지 474MB의 대부분은 무엇인가?
5. (경계) jlink로 줄인 런타임은 어떤 앱에서 실행 중에 깨질 수 있나? 모듈 목록은 어떻게 정했나?
6. (경계) slim·distroless·alpine·scratch 베이스는 각각 무엇을 빼나? distroless README가 밝힌 크기 비교는?
7. (장애 진단) 컨텍스트에 150MB `target/`과 `.env`가 있는데 `.dockerignore`가 없다. 빌드 로그·이미지 크기·이미지 내용에서 무엇이 보이나? `.dockerignore`를 넣으면?
8. (장애 진단) distroless 파드에서 `kubectl exec ... sh`가 `exec: "sh": executable file not found in $PATH`로 실패한다. 왜 그렇고, 어떻게 들여다보나(도커 실험과 Kubernetes 방법)?
9. (장애 진단) temurin JRE를 alpine에 복사했더니 `exec /opt/java/bin/java: no such file or directory`가 난다. 파일은 분명히 있다. 무엇이 "없는" 것인가(`readelf` 결과로)? 대처는?
10. (장애 진단) 스케일 아웃한 파드가 `ImagePullBackOff`에 머문다. 이 상태의 뜻과 재시도 상한(Kubernetes 문서)은? 이미지 크기 말고 먼저 확인할 원인은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
