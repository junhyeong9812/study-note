# language/11-gc-tuning-and-gc-logs — 질문

## 질문

1. (예측) `eclipse-temurin:21-jdk`를 `--cpus=2 --memory=1g`와 `--cpus=2 --memory=4g`로 띄웠다. 각각 어느 수집기를 고르고 최대 힙은 얼마인가? `--cpus=1 --memory=4g`는?
2. (경계) 1791MiB와 1792MiB 컨테이너에서 기본 수집기가 갈린다. 이 경계는 어디서 오나(문서·소스)? CPU 조건은?
3. (왜) `MaxGCPauseMillis`가 "soft goal"이라는 것은 무슨 뜻인가? G1 가이드가 `-Xmn`으로 젊은 세대를 고정하지 말라고 하는 이유는?
4. (계산) 아래 로그로 할당률과 이번 GC의 승격량을 계산하라.
   `[1.318s] GC(14) ... 467M->226M(512M)` (끝) / `[1.445s] GC(15) 시작` / `GC(15) Old regions: 206->211`, 영역 1MB.
5. (그림) G1 힙의 영역 구조를 그리고, Young GC와 Mixed GC의 collection set이 어떻게 다른지, "Garbage-First"라는 이름이 어디서 왔는지 설명하라.
6. (예측) 산 데이터 200MB인 부하를 G1 `-Xmx512m`(목표 기본), `-Xmx512m -XX:MaxGCPauseMillis=20`, `-Xmx1g`로 돌렸다. evacuation failure·Full GC·Young 평균은 어떻게 달라졌나? 이 결과에서 얻는 교훈은?
7. (경계) `(Evacuation Failure)`가 찍힌 GC 자체는 위험한가? G1 문서는 무엇이 위험하다고 하나?
8. (예측) G1 영역 1MB에서 400KB 배열과 600KB 배열을 4000번씩 할당했다. GC 횟수와 GC 원인은 어떻게 다른가? 600KB 쪽의 메모리 낭비율은?
9. (장애 진단) 2 vCPU·1GiB 파드로 줄인 뒤 p99가 크게 나빠졌다. GC 로그 첫 줄에서 무엇을 확인하고, 어떻게 고치나?
10. (장애 진단) `-Xmx`를 컨테이너 한도의 90%로 올린 뒤 부하 때 파드가 로그 없이 재시작된다. 무슨 일이 났고, 힙과 힙 밖을 어떻게 나눠 잡나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
