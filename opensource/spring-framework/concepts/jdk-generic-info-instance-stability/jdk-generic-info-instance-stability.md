# 개념: JDK 제네릭 정보의 인스턴스 안정성 — "정본"이 존재하는 이유

> PR #37186(forClassWithGenerics 직렬화) 설계의 토대가 된 JDK 성질. 질문의 형태:
> "정본 인스턴스의 identity가 정확히 어떻게 존재하는가?"

## 한 줄 요약

JVM은 클래스의 제네릭 리플렉션 정보(타입 파라미터 `TypeVariable` 등)를 클래스당
**한 번만 생성해 내부에 캐시**하고, 이후 `List.class.getTypeParameters()`를 몇 번
호출하든 **매번 같은 객체(`==`)**를 돌려준다. 이 "JVM 안에 하나뿐인 객체"를 이
문서에서 정본(canonical instance)이라 부른다.

## 어디서 오는 성질인가

`Class` 객체는 제네릭 서명(`Signature` 속성)을 파싱한 결과를 내부 필드
(`genericInfo` — JDK 17+ 기준 강참조 volatile)에 담아둔다. 첫 호출 때 파싱해
채우고, 이후는 캐시를 반환한다. 배열을 반환하는 API(`getTypeParameters()` 등)는
배열 자체는 방어 복제하지만 **원소 객체는 캐시된 동일 인스턴스**다.

실측(2026-08-20, JDK 25):

```java
List.class.getTypeParameters()[0] == List.class.getTypeParameters()[0]   // true — 반복 호출 동일
Class.getGenericSuperclass(), getGenericInterfaces()[i] 도 동일             // instance-stable
```

## 이 성질이 왜 중요한가 — identity가 계약이 되는 곳

`TypeVariableImpl.equals()`는 `o.getClass() == TypeVariableImpl.class`를 요구하는
**클래스 검사형 equals**다(프록시·다른 구현과 비대칭). 그래서 TypeVariable을 키나
비교 대상으로 쓰는 코드는 사실상 **정본 identity에 기대는 것이 가장 안전**하다:

- Spring `ResolvableType`의 변수 해석(`resolveVariable`)이 변수 매칭을 할 때
- #37186의 직렬화 프록시가 "이 인자는 rawType의 i번째 파라미터"를 판별할 때
  (`variables[i] == argument` — identity 비교가 성립하는 근거가 바로 이 성질)
- 역직렬화가 `getTypeParameters()[i]` **재조회**로 복원할 때 — 복원본이 그 JVM의
  정본과 `==`이므로 equals/hashCode/기존 캐시된 hash까지 전부 정합

## 경계 — 성질이 보장하는 범위

- **같은 JVM, 같은 클래스로더** 안에서의 성질이다. 다른 JVM에는 "그쪽의 정본"이
  따로 있다(주소가 아니라 좌표로 건너가는 이유 —
  [serialization-proxy-and-version-skew.md](../serialization-proxy-and-version-skew/serialization-proxy-and-version-skew.md)).
- 클래스로더가 다르면 같은 이름의 클래스도 다른 `Class` 객체 -> 다른 정본.
- JDK 명세가 "캐시하라"고 강제하는 것은 아니고 구현 성질이다 — 그래서 이 성질에
  기대는 코드는 실패 시 안전한 폴백(예: #37186의 "미스면 기존 직렬화로 축퇴")을
  함께 두는 것이 좋다.

## 관련

- `serialization-proxy-and-version-skew.md` — 이 성질을 이용한 좌표 기반 직렬화
- `reflection-type-metadata-layer.md` — ResolvableType이 이 층 위에 서는 방식
- `../../prs/37153-enum-array-annotation-probe/enum-annotation-name-resolution.md` — "이름으로 재조회"의 annotation 판
