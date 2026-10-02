# software-design/51-legacy-change-techniques — 질문

## 질문

1. (왜) Feathers는 레거시 코드를 무엇으로 정의하나? 레거시 코드를 바꿀 때의 "닭과 달걀" 순환을 설명하라.
2. (그림) 레거시 코드 변경 알고리즘의 다섯 단계를 순서대로 그려라. 변경점과 테스트 지점은 왜 다를 수 있나?
3. (경계) seam과 enabling point를 정의하라. `buildMartSheet()` 안에서 `new FormulaCell(...)`을 만들고 `cell.Recalculate()`를 부르면 seam인가? 어떻게 바꾸면 seam이 되나?
4. (경계) sprout method와 wrap method는 각각 언제 쓰나? sprout method의 한계는?
5. (예측) 메서드 안에서 운영 DB에 직접 연결하는 `TransactionGate.postEntries()`를 테스트에서 그대로 부르면? 생성을 `openDatabase()`로 빼고 테스트 서브클래스에서 오버라이드하면? 실험 출력으로 답하라.
6. (예측) 호출처 40곳인 `charge(long, long)`를 `charge(long, Money)`로 바꾼다. 시그니처만 먼저 바꾸면 컴파일 오류가 몇 건인가? parallel change로 하면 커밋별 변경 파일 수는 어떻게 되나?
7. (장애 진단) 시그니처 변경 PR을 병합했더니 git은 "충돌 없음"인데 빌드가 깨졌다. 무슨 일이고, parallel change였다면 왜 괜찮았나?
8. (장애 진단) 리팩터링 뒤 새 테스트는 다 통과하는데 운영에서 금액이 1원씩 다르다. 알고리즘의 어느 단계를 건너뛰었나?
9. (경계) contract를 언제 해도 되나? 같은 빌드 안의 호출처와 다른 배포 단위의 호출처는 확인 방법이 어떻게 다른가?
10. (연결) 의존 끊기 기법 중 Parameterize Constructor와 Extract Interface는 25(DI)·50(branch by abstraction)과 어떻게 이어지나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
