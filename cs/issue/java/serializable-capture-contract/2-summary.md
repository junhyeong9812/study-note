# cs/issue/java/serializable-capture-contract — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
class Desc implements Serializable
   ├─ 필드들 (직렬화 가능)
   └─ supplier = (Supplier & Serializable) () -> resolve(field)     ← 지연 초기화 최적화
                         │
                         └─ 캡처값: Field / MethodParameter          ← 비직렬화 객체

writeObject(desc)
   └─ supplier도 non-transient → 직렬화 대상
        └─ 직렬화 람다 = SerializedLambda{ capturedArgs = [Field] }
             └─ NotSerializableException: Field                     ✗ 계약 회귀

기존 테스트: 어노테이션 배열을 캡처하는 생성자만 사용 (어노테이션 프록시는 Serializable) → 우연히 통과

[교정 1 — 캡처 차단]
   supplier → transient (non-final)
   writeObject: 결과를 먼저 강제 해석해 캐시 필드에 채움 → defaultWriteObject
   readObject : 캐시에서 supplier 재구성 + 빈 결과를 싱글턴으로 정규화 (생성자 우회 대비)

[교정 2 — 비직렬화 내부 타입]
   필드가 TypeVariable(JDK 내부, 비직렬화) 보유
   writeReplace → (선언 클래스, 타입 파라미터 인덱스) 마커
   readResolve  → rawClass.getTypeParameters()[index] 재조회 (같은 인스턴스 → equals 보존)
                  검증 실패 시 InvalidObjectException
```

## 핵심 문장

- `Serializable` 선언은 **객체 그래프 전체**에 대한 약속이다 — 필드·람다 캡처값 중 하나라도 비직렬화면 계약이 깨지고, 컴파일러는 이를 검사하지 않는다.
- 직렬화 가능한 람다는 **캡처한 값을 그대로** 스트림에 싣는다. 지연 초기화용 람다가 리플렉션 객체를 캡처하면 최적화가 곧 계약 위반이 된다.
- 역직렬화는 **생성자를 우회**한다 — 생성자에서 보장하던 정규화(빈 싱글턴 등)는 `readObject`에서 다시 해야 한다.
- 직렬화 불가 객체는 **객체 대신 재조회 좌표**(선언 클래스 + 인덱스)를 보내고 복원 시 다시 찾는다 — enum이 이름을 보내는 것과 같다.
- 구 스트림을 조용히 불완전하게 읽는 것보다 **시끄럽게 실패**(`InvalidClassException`)하는 편이 낫다.
