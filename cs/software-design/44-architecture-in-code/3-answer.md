# software-design/44-architecture-in-code — 정답

## 정답

### 1. 다섯 결정

- ① 포트 인터페이스 위치 ② 어댑터가 무엇을 import하나(방향) ③ 매핑 횟수와 주체 ④ 트랜잭션 경계 ⑤ 도메인 예외를 HTTP 등으로 번역하는 위치.
- 이것을 안 정하면 "이름만 헥사고날"이나 "1:1 매핑만 반복하는 의례적 구조"가 된다.

### 2. 세 구조의 화살표

```text
 계층형   web → service → repository → domain(@Entity) → jakarta.persistence
 헥사고날 adapter.in.web → port.in ← application.Service → port.out ← adapter.out.persistence ;  application → domain
 클린     controllers → InputBoundary ← Interactor → OutputBoundary ← presenters ; gateways → AccountGateway ; Interactor → entities
```

- 반대인 곳: 제어 흐름은 유스케이스 → DB(그리고 → 프레젠터)인데, 소스 의존은 영속 어댑터 → `AccountStore`(안쪽), 프레젠터 → `OutputBoundary`(안쪽)다. 인터페이스를 안쪽에 둬서 의존을 뒤집었다(Martin 2012 "Crossing boundaries").

### 3. 원전의 정의

- Cockburn(2005): 애플리케이션이 사용자·프로그램·자동 테스트·배치 스크립트에 의해 똑같이 구동되고, 실행 장치·DB와 격리되어 개발·테스트될 수 있게 한다.
- 주도하는(primary/driving): HTTP 컨트롤러, 테스트 하네스(FIT). 주도되는(secondary/driven): DB, 외부 서비스, 목.
- Martin(2012) 의존성 규칙: 소스 의존은 안쪽으로만. 안쪽 원은 바깥 원에 선언된 이름(함수·클래스·변수)을 언급하지 않는다. 바깥 프레임워크가 만든 데이터 형식도 안쪽에서 쓰지 않는다.

### 4. 크기와 순수성

(실험 A, base 스냅샷, Main 제외)

```text
layered(base): 파일 4개, 48줄 (Main 제외)
hexagonal(base): 파일 8개, 75줄 (Main 제외)
clean(base): 파일 12개, 78줄 (Main 제외)
```

- 계층형만 `points.domain -> jakarta.persistence`(jdeps)이고, ArchUnit 규칙에서 `[FAIL] ... layered — was violated (5 times)`. 헥사고날·클린은 PASS.

### 5. `@Version` 추가

(실험 B, C1)

- 계층형: `domain/PointAccount.java` 1줄 추가 — 가장 짧지만 도메인 파일이다.
- 헥사고날: `adapter/out/persistence/PointAccountJpaEntity.java` +1, `AccountPersistenceAdapter.java` +5 −1. 클린: `AccountRecord.java` +1, `JpaAccountGateway.java` +5 −1.
- 이유: 도메인 객체에 버전이 없어서, 저장할 때 새 영속 객체를 만들면 버전이 사라진다. 기존 행을 찾아 값만 바꾸도록 매핑을 고쳐야 했다. 모델을 나눈 대가다.

### 6. 값 하나 내보내기와 도메인 규칙

- C2 등급 추가: 계층형 2파일(도메인·컨트롤러), 헥사고날 4파일(도메인·포트 결과 타입·서비스·컨트롤러), 클린 4파일(엔티티·응답 모델·인터랙터·프레젠터).
- C3 1회 한도: 세 구조 모두 도메인 파일 1개.

### 7. "항상"은 아니다

- 실험에서 C1은 계층형이 줄 수로 가장 짧았고, C2는 계층형이 파일 수로 절반이었다. C3은 같았다.
- 헥사고날·클린이 지킨 것은 "영속 변경이 도메인 파일을 건드리지 않는다"와 "도메인이 프레임워크를 모른다"다.
- 고르는 기준: 바깥(DB·프레임워크·외부 API)이 자주 바뀌고 도메인 규칙이 복잡하면 격리 쪽. 화면 필드 추가가 잦은 CRUD 위주면 계층형의 짧은 경로가 싸다.

### 8. 이름만 헥사고날

- 확인: `jdeps -verbose:package`에서 도메인 패키지 → `jakarta.persistence` 간선, ArchUnit 도메인 순수성 규칙(`is annotated with <jakarta.persistence.Entity>`).
- 대처: 영속 엔티티를 어댑터 패키지로 옮기고(package-private), 도메인 객체와 매핑한다. 순수성 규칙을 CI에 둬서 다시 들어오지 않게 한다.

### 9. 기술 이름의 포트

- 원인: 포트를 애플리케이션의 필요가 아니라 도구 API에 맞췄다(이름·메서드·반환 타입에 JPA·Spring Data가 새어 들어옴). Graça: 포트는 코어의 필요에 맞추고 도구 API를 흉내 내지 않는다.
- 대처: 유스케이스 언어로 포트를 다시 정의(`AccountStore.load/save`)하고, 쿼리 메서드·페이지 타입 같은 기술 세부는 어댑터 안에서 번역한다.

### 10. 트랜잭션 경계

- 계층형: 서비스 메서드. 헥사고날: 애플리케이션 서비스(유스케이스). 클린: 인터랙터, 또는 인터랙터를 감싼 바깥 데코레이터(예제 코드의 주석 위치).
- 어댑터 메서드마다 열면 유스케이스 하나가 여러 트랜잭션으로 쪼개져, 중간 예외 때 일부만 커밋된다(포인트 차감은 됐는데 내역은 없음). 이 노트에서는 실행하지 않은 원칙·해석이다.
