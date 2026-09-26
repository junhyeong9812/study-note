# backend-labs — 주제별 API 구현 실험 기록

백엔드 정합성·동시성(commerce 01~09)과 멀티테넌시·인증/인가(tenancy 10~17)를 **직접 구현하고 부하·장애를 걸어 검증**하는 17개 실험의 기록.

- **실 구현** = 코드 repo `/home/jun/project/lab/backend-labs-{commerce,tenancy}/<주제>/` (주제별 독립 git repo · Kotlin 2.2 · Spring Boot 3.5 · JDK 21)
- **기록** = 이 폴더 `lab/backend-labs/{commerce,tenancy}/<주제>/README.md`
- 목록·상태·선행 cs 챕터 = [index.md](index.md)

## README 규칙 — 원본 위 고정, 아래로 append-only

각 주제 README의 상단은 **원본 설계 문서 그대로**다(Questions · Architecture · Load Profile · Results · ADR). 원본 부분은 고치지 않는다.
구현하면서 생긴 기록은 **파일 끝에만 덧붙인다**. 이미 쓴 기록도 고치지 않는다 — 틀린 게 드러나면 새 기록에서 정정한다.

```markdown
---

## 작업 기록

### YYYY-MM-DD — <이번에 구현한 API/기능 한 줄>
- 대응 질문: Q1, Q3            ← 원본 Questions 번호
- 코드: <repo> @ <commit 해시>
- 한 것: 엔드포인트·핵심 로직·선택한 방식(왜)
- 도식: 흐름·상태 전이·시퀀스 (mermaid/ASCII — 기능마다 1개 이상)
- 확인: 테스트·부하·정합성 체크 결과 (수치는 실제 측정만 — 추정 금지, 없으면 "미측정")
- 막힌 것 / 틀렸던 가정
- cs/ 추출 후보: <새로 알게 된 개념 → 넣을 cs 챕터>
```

- `## 작업 기록` 헤더는 첫 기록 때 한 번만 붙인다.
- 원본 Results·Load Test Results 표의 빈칸은 원본 위치를 채우지 않는다 — 작업 기록에 측정값을 쓰고, 랩이 끝나면 README 끝에 `## 종합 결론`을 추가한다.

## 진행 순서 (주제 하나)

```
선행 cs 챕터 인출 (index.md "선행 cs")
  → 원본 Questions 중 하나를 고른다
  → 코드 repo에서 API 구현 + 그 질문을 재현하는 테스트
  → README 끝에 작업 기록 append
  → Questions를 다 돌면 종합 결론 · index.md 상태 갱신
```

## 서버 실행

기본 `java`가 1.8이므로 JDK 21을 지정한다.

```bash
export JAVA_HOME=~/.sdkman/candidates/java/21.0.5-tem
cd /home/jun/project/lab/backend-labs-commerce/seat-reservation-lab
./gradlew bootRun        # 포트는 index.md 참조
```
