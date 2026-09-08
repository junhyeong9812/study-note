# 학습 문서 인덱스 — C4 작업에서 나온 Java/JVM 개념 정리

> 출생지: `docs/plans/2026-08-04/c4-typedescriptor-serialization/`(C4=#37109 작업 학습문서)에서 2026-08-20 concepts로 이전. 사례 연구(09)는 #37109, 인접 후속은 R8 작업 폴더(`docs/plans/2026-08-20/r8-elementtype-serialization/`) 참조.

> 2026-08-04, C4(`TypeDescriptor` 직렬화 회귀) 작업 중 대화에서 걸렸던 개념들을 주제별로 정리한 문서 묶음.
> 이 폴더의 `requirement-spec.md`·`log.md`가 **작업 기록**이라면, 아래 문서들은 **학습용**이다. 손으로 따라 치며 확인하는 용도.

## 읽는 순서

앞 문서가 세운 개념 위에 뒤 문서가 얹히므로 번호순으로 읽는 것이 기본이다.

| # | 문서 | 한 줄 |
|---|------|------|
| 01 | [컴파일 시점 vs 런타임 시점](01-compile-vs-runtime.md) | javac가 검사하는 것과 안 하는 것 — "직렬화 불가"는 왜 컴파일 오류가 아닌가 |
| 02 | [힙과 객체 그래프](02-heap-and-object-graph.md) | 객체가 만들어지고 참조로 이어지는 구조, 생성 주기, 도달 가능성 |
| 03 | [직렬화·역직렬화 기본](03-serialization-basics.md) | 방향·워크플로우·무엇이 실리고 무엇이 안 실리나 |
| 04 | [transient와 volatile](04-transient-and-volatile.md) | 자주 헷갈리는 두 키워드, 각각 누구에게 하는 말인가 |
| 05 | [직렬화 훅 메서드](05-serialization-hooks.md) | `writeObject`/`readObject`/`readResolve` — 생성자를 우회하는 객체 생성 |
| 06 | [람다 내부 동작](06-lambda-internals.md) | 람다가 컴파일되는 방식, 캡처, `SerializedLambda` |
| 07 | [리플렉션 객체](07-reflection-objects.md) | `Field`/`Method`/`MethodParameter`가 무엇이고 왜 직렬화가 안 되나 |
| 08 | [동일성과 싱글턴](08-identity-and-singleton.md) | `==` vs `equals`, 역직렬화가 싱글턴을 깨는 이유 |
| 09 | [케이스 스터디: C4 전체 복기](09-case-study-typedescriptor.md) | 위 개념들로 이번 버그를 처음부터 끝까지 재구성 |
| 10 | [오해 체크리스트](10-misconception-checklist.md) | 이번 대화에서 실제로 걸렸던 지점들 — 자가 점검용 Q&A |
| 11 | [serialVersionUID와 클래스 호환성](11-serialversionuid.md) | 리뷰 finding R2 — 필드 수식어가 wire 호환을 바꾸는 원리 |

> 11번은 듀얼 리뷰에서 나온 지적(R2)을 실측으로 확정하며 추가한 문서다. 작업 기록은 `log.md`의 리뷰 ledger, 서사형 정리는 [해설.md](해설.md).

## 이 묶음을 관통하는 한 문장

> **자바에는 "컴파일 시점에 정해지는 것"과 "런타임에 정해지는 것"의 경계가 있고, 직렬화·람다·리플렉션은 전부 그 경계 위에서 동작한다.**

C4 버그는 이 경계를 잘못 읽으면 절대 안 보이는 버그였다 — 컴파일도 되고, 평소 실행도 잘 되고, 심지어 테스트도 통과했는데, **특정 런타임 동작(직렬화)에서만** 터졌다.

## 실습 환경

```bash
# 이 저장소에서 spring-core jar 빌드
./gradlew :spring-core:jar

# 실습 코드 컴파일·실행 (예시)
CP=spring-core/build/libs/spring-core-7.1.0-SNAPSHOT.jar
javac -cp "$CP" -d /tmp/study Study.java
java -cp "$CP:/tmp/study" Study
```

각 문서의 코드 스니펫은 이 방식으로 바로 돌려볼 수 있게 작성했다.
