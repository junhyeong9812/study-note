# software-design/30-pattern-languages-and-catalogs — 정답

## 정답

### 1. 이름만 주고받을 때

- (1) 힘을 안 본다 → 문제가 없는 곳에 간접 계층이 생긴다.
- (2) 같은 이름이 카탈로그마다 다른 뜻이다 → 리뷰에서 서로 다른 것을 말한다.
- Fowler(「Writing Software Patterns」, 2006): 힘은 그 패턴의 적응증과 금기(indications and contra-indications), 즉 쓸 때와 쓰지 말 때를 탐색하는 방법이다. 그는 패턴이 생각나면 "언제 안 쓸까"를 따져 보고, 그것이 대안 패턴으로 이어진다고 쓴다.

### 2. 패턴의 칸

```text
 이름 → 맥락 → 문제 → 힘 → 해법 → 결과(얻는 것·잃는 것·다음 패턴)
```

- GoF(Wikipedia 정리): Name·Intent·Also Known As·Motivation·Applicability·Structure·Participants·Collaborations·Consequences·Implementation·Sample Code·Known Uses·Related Patterns.
- microservices.io(API Gateway 페이지): Context·Problem·Forces·Solution·Resulting context·Related patterns.
- 이 밖에 Alexandrian(굵은 문제 헤드라인 → 굵은 해법 지시문), Portland(문제 문단 → 강조된 "therefore" → 해법 문단), Coplien(Problem·Context·Forces·Solution), POSA, PoEAA(how it works·when to use it·examples) 형식이 있다(Fowler).

### 3. 패턴 언어

- 패턴들이 선행·조합·대안 관계로 엮여 한 패턴의 결과가 다음 패턴의 맥락이 되는 체계.
- Alexander 『A Pattern Language』(1977): 253개 패턴이 "함께 하나의 언어를 이룬다". 각 패턴 끝에 그것을 완성할 더 작은 패턴들을 잇는다.
- EIP: 65개 패턴을 메시지 흐름(채널 → 라우팅 → 변환)을 따라 배열한 패턴 언어.
- microservices.io: 패턴마다 Related patterns(예: API Gateway는 Microservice Architecture가 필요를 만들고, Service Discovery를 쓰고, Circuit Breaker를 쓴다).
- Azure: 「Combine patterns」 절(Retry + Circuit Breaker, Saga는 Compensating Transaction 위에 등).

### 4. 같은 이름 다른 뜻

- Repository
  - 같은 점: 저장소를 메모리 컬렉션처럼 보이게 하고, 질의·저장 기술을 숨긴다. Fowler의 PoEAA 페이지도 DDD에 좋은 설명이 있다고 연결한다.
  - 다른 점: PoEAA는 데이터 매퍼 위에 질의 구성 코드를 모으는 계층(도메인 클래스·질의가 많을 때). DDD는 **전역 접근이 필요한 애그리게이트 타입마다**, **직접 접근이 필요한 애그리게이트 루트에만** 둔다(DDD 레퍼런스 2015).
- Gateway
  - PoEAA: 외부 시스템·자원 접근을 감싸는 **객체**(코드 안 클래스).
  - API Gateway(microservices.io): 클라이언트 전체의 단일 진입점인 **서버**(배포 단위). Azure는 이를 Routing·Aggregation·Offloading으로 나눈다.

### 5. 변경 1·2

(실험 A, git 2.43.0)

- 무게 할증: direct `3 files changed`, patterned `4 files changed` — 인터페이스 시그니처까지 고쳤다.
- 회원 무료배송: direct는 기존 규칙 파일(`ShippingFee.java`)을 고쳤다(수정 여부 1). patterned는 기존 규칙 클래스를 건드리지 않고(0) `MemberShippingFeePolicy.java`를 추가하고 팩토리를 고쳤다.
- 해석: 변형(두 번째 정책)이 실제로 왔을 때 비로소 패턴의 이점이 보였다.

### 6. 변경 3

```text
  direct 변경 3 (할증 2000→2500):  1 file changed, 1 insertion(+), 1 deletion(-) | ShippingFee.java 
  patterned 변경 3 (할증 2000→2500):  2 files changed, 2 insertions(+), 2 deletions(-) | DefaultShippingFeePolicy.java MemberShippingFeePolicy.java 
```

- direct 1파일, patterned 2파일.
- 원인: 무게 할증이라는 공통 규칙이 두 전략 클래스에 복제됐다. 변하는 축(회원 여부)과 공통 규칙을 구분하지 않고 전략을 통째로 나눴다. 공통 규칙을 한 곳(공용 함수·데코레이터)에 두면 1곳이 된다.

### 7. 관계 그래프

- 자료구조: 노드 = 패턴, 간선 = (from, 관계, to, 출처). 선행은 방향 간선, 조합·대안은 양방향으로 인접 리스트에 넣는다.
- 질의: 한 패턴의 인접 리스트 = 함께 보게 되는 패턴(실험 B의 `Circuit Breaker → Retry, API Gateway`).
- 위상 정렬(Kahn): 선행 간선만으로 정렬하면 먼저 이해·도입할 패턴 순서 후보가 나온다. 실험 B에서 `Compensating Transaction(2) < Saga(18)`, `Microservice Architecture(9) < API Gateway(20)`.
- 간선에 출처를 달아 두어 "왜 함께 나오나"에 답할 수 있게 한다.

### 8. 리뷰 바로잡기

- Repository 모양이 PR마다 다름
  - 묻기: "어느 카탈로그의 Repository인가? 단위는 테이블인가 애그리게이트 루트인가?"
  - 바로잡기: 팀 용어집과 설계 문서에 출처를 붙여 정의한다(예: "DDD Repository — 애그리게이트 루트당 하나, 직접 접근이 필요한 것만").
- 구현 하나짜리 인터페이스·팩토리 증가
  - 묻기: "이 구조가 해결하는 변경이 지금 있나, 예상인가?" "두 번째 구현이 언제 오나?"
  - 바로잡기: 인라인한다. 변형이 실제로 오면 그때 추출한다(실험 A 변경 1의 추가 비용, 변경 2의 이점). 목 대역이 필요한 경계 인터페이스는 예외로 둔다.
