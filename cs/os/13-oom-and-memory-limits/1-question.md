# os/13-oom-and-memory-limits — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고, 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> ⚠️ 이 질문 목록은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 질문

1. (왜) 리눅스에서 `malloc(1GB)`가 성공했는데 나중에 프로세스가 OOM killer에 죽을 수 있는 이유는? "할당"과 "사용"의 시점 차이로 설명하라.
2. (경계) `vm.overcommit_memory` 0·1·2는 각각 무엇을 거절하나? 모드 2의 `CommitLimit` 식을 적고, RAM 38.7GB·스왑 8.4GB·ratio 50이면 얼마인지 계산하라.
3. (예측) 할당 시점에 `ENOMEM`을 받는 경우와 사용 중에 SIGKILL을 받는 경우를 각각 두 가지씩 들어라.
4. (그림) OOM killer가 희생자를 고르는 과정을 그려라. 기본 점수에는 무엇이 들어가고, `oom_score_adj`는 어떻게 더해지나? -1000은 무슨 뜻인가?
5. (계산) `oom_score_adj`가 100이고 메모리를 거의 안 쓰는 셸의 `/proc/self/oom_score`는 대략 얼마인가? 식은 어디서 왔나?
6. (경계) cgroup v2의 `memory.high`와 `memory.max`는 넘었을 때 각각 무슨 일이 생기나? `memory.current`에 페이지 캐시가 들어가는 것이 왜 중요한가?
7. (장애 진단) 파드가 exit 137로 재시작한다. 이것만으로 OOM이라고 할 수 있나? 무엇으로 확정하나?
8. (장애 진단) `-Xmx`는 limit의 절반인데 컨테이너가 `OOMKilled`된다. 힙 밖에서 메모리를 쓰는 JVM 영역을 네 가지 이상 들고, 어떤 도구로 나눠 보나?
9. (연결) 자바의 `OutOfMemoryError: Java heap space`와 커널 OOM kill은 무엇이 다른가? `MaxMetaspaceSize`·`MaxDirectMemorySize`를 걸면 장애의 모습이 어떻게 바뀌나?
10. (설계) 노드 전체 OOM에서 원인과 무관한 DB가 죽었다. 왜 그렇게 되며, 재발을 막는 설정 두 가지는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
