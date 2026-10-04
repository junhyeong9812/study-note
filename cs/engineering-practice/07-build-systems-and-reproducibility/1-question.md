# engineering-practice/07-build-systems-and-reproducibility — 질문

## 질문

1. (왜) 매번 전부 다시 빌드하는 것과 바뀐 것만 다시 빌드하는 것은 각각 무엇을 얻고 무엇을 잃나? 셋(빠름·정확함·재현성)을 함께 얻으려면 빌드 시스템이 무엇을 알아야 하나?
2. (그림) app→api·service, api→domain, service→domain·util, domain→util(화살표 = "의존")인 모듈 그래프의 빌드 순서를 Kahn 알고리즘으로 구하라. util이 바뀌면, api가 바뀌면 각각 무엇을 다시 빌드하나? Maven에서 이 집합을 고르는 옵션은?
3. (예측) `out.txt: in.txt` 규칙의 make에서 (a) 내용은 그대로 두고 `touch in.txt`, (b) 내용을 바꾸고 mtime을 2000년으로 되돌림 — 각각 어떻게 되나? Docker의 `COPY` 캐시는 (a)에서 어떻게 다른가?
4. (예측) 캐시 키를 소스 해시만으로 만든 빌드가 설정(API_URL)을 산출물에 굽는다. 스테이징으로 한 번 빌드한 뒤 운영 URL로 빌드하면 무슨 일이 생기나? 로그에는 무엇이 보이나?
5. (예측) Maven 3.9에서 같은 소스를 3초 간격으로 `clean package` 두 번 하면 jar sha256은 같나? `project.build.outputTimestamp`를 주면? 차이는 jar의 어디에 있나?
6. (경계) reproducible-builds.org의 재현 가능 빌드 정의를 말하라. Maven 가이드가 `outputTimestamp`를 줘도 남는다고 꼽는 차이는? `SOURCE_DATE_EPOCH`는 무엇을 나타내나?
7. (연결) SWE@G 18장은 Maven·Gradle을 어떤 종류로 분류하고, 그 종류의 약점으로 무엇을 드나? 원격 캐시가 성립하려면 무엇이 보장돼야 한다고 하나? 이것은 저자 주장인가 측정인가?
8. (장애 진단) 개발자 PC(서울, ko_KR)에서는 통과하는 테스트가 UTC CI와 de_DE 환경에서 실패한다. 실험에서 각각 무엇이 달라졌나? 고치는 코드는?
9. (장애 진단) 삭제한 클래스가 운영 jar에 여전히 들어 있다. maven-compiler-plugin 3.15.0과 손으로 짠 `javac -d out` 스크립트는 소스 삭제에 각각 어떻게 반응했나? 이 플러그인의 증분 단위는?
10. (장애 진단) Maven이 `The projects in the reactor contain a cyclic reference`를 내며 시작도 못 한다. 왜 위상정렬이 실패하며, 구조적으로 어떻게 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
