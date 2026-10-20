# java — Java 언어·JVM·Spring

Java 언어 규칙과 JVM 위 프레임워크(Spring·JPA)에 뿌리내린 패턴이다.\
공통 원리: **컴파일을 통과한 코드도 언어 규칙·프레임워크 기본값이 직관과 다른 지점에서 조용히 오동작한다** — 기본값에 기대지 말고 명시한다.\
언어 레벨 카드는 이 폴더에, 프레임워크 카드는 하위 폴더에 있다.

## 공통 원리

```
  소스 ──▶ javac (통과) ──▶ JVM 런타임 ──▶ 프레임워크 기본값
                               │                 │
                               ├─ 초기화 순서     ├─ 프록시 self-invocation
                               ├─ 제네릭 소거     ├─ 자동설정 back-off
                               └─ 직렬화 캡처     └─ save = merge
                                        ▼
                    컴파일 OK · 런타임에서만 드러나는 오동작
```

## 하위 폴더

| 폴더 | 카드 수 | 무엇 |
|------|---------|------|
| [spring/](spring/) | 1 | Spring·JPA 기본 동작 |

## 패턴 카드 (이 폴더 직속)

- [container-gc-ergonomics](container-gc-ergonomics/) — 수집기를 지정하지 않은 JVM은 실행 환경(컨테이너 한도)을 보고 수집기를 고른다 — 메모리 한도가 서버급 기준 아래면 Serial이 골라져 주기적 Full GC가 고정 도착률 부하의 꼬리 지연이 된다, 수집기를 명시하고 실제 적용값을 회차마다 대조한다.
- [language-semantics-traps](language-semantics-traps/) — Java 언어 규칙(Error≠Exception·정적 초기화 순서·제네릭 불변성·소거·오버로드 모호성·주석 렉싱·인자 평가 순서)이 직관과 달라 컴파일은 통과하고 런타임에서 틀린다.
- [lazy-resolution-context-propagation](lazy-resolution-context-propagation/) — 이름처럼 나중에 해석되는 값은 해석 문맥(ClassLoader)과 한 쌍이다 — 파생 객체가 문맥을 떨어뜨리고 null을 기본 로더로 대체하면 예외 또는 이름만 같은 다른 Class(조용한 오답)가 나온다, 파생 팩토리가 문맥을 운반하는지 형제 팩토리와 대칭으로 점검하고 테스트는 정체성을 단언한다.
- [serializable-capture-contract](serializable-capture-contract/) — Serializable을 선언한 객체·람다가 비직렬화 객체(리플렉션 타입·TypeVariable)를 캡처하면 직렬화 계약이 조용히 깨진다.

> 이 폴더의 메타 태그: `contract-drift`(1) · `environment-drift`(2) · `identity`(1) · `silent-failure`(1) — 태그별 전체 목록은 [issue 태그 역인덱스](../README.md#태그-역인덱스).
