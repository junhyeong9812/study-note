# os/28-containers-namespaces-cgroups — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고, 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> ⚠️ 이 질문 목록은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 질문

1. (왜) 컨테이너를 "namespace + cgroup + 이미지 레이어"로 설명한다. 셋이 각각 무엇을 바꾸나? VM과 비교해 컨테이너가 **공유하는 것**은 무엇인가?
2. (그림) 컨테이너 안에서 `ps`를 치면 앱이 pid 1인데, 호스트에서는 pid가 48213이다. PID namespace 중첩을 그림으로 그려 이 현상을 설명하라. 두 프로세스가 같은 namespace인지 어떻게 확인하나?
3. (예측) `ENTRYPOINT java -jar app.jar`(셸 형식)로 만든 컨테이너에 `docker stop`을 했다. 무슨 일이 일어나고 exit code는 몇인가? exec 형식이면 무엇이 달라지나?
4. (경계) PID namespace의 pid 1이 보통 프로세스와 다른 점 두 가지는? 호스트에서 `kill -9`를 보내면 핸들러가 없어도 죽는 이유는?
5. (계산) `cpu.max`가 `200000 100000`이다. 바쁜 스레드 8개가 코어 8개에서 동시에 돌면 한 기간(100ms) 동안 어떤 일이 생기나? 평균 CPU 사용률 그래프로는 왜 안 보이나?
6. (연결) 24코어 호스트의 `--cpus=2` 컨테이너에서 Node `os.cpus().length`, 최신 JVM의 `availableProcessors()`는 각각 무엇을 돌려줄 가능성이 큰가? `cpu.weight`(shares)는 JDK 19부터 왜 CPU 수 계산에서 빠졌나?
7. (그림) 이미지 레이어 3개 위에서 컨테이너가 (a) 아래층 파일을 읽고, (b) 수정하고, (c) 삭제할 때 overlayfs가 각각 무엇을 하나?
8. (장애 진단) 컨테이너가 부하 중 exit 137로 재시작한다. OOM kill인지 `docker stop`의 SIGKILL인지 어떻게 가려내나? 어떤 파일·로그를 보나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
