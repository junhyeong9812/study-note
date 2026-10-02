# software-design/41-architecture-fitness-rules — 정답

## 정답

### 1. 가시성 밖의 규칙

- 가시성은 "숨긴 것을 밖에서 쓰기"만 막는다. 공개된 타입 사이의 방향은 못 정한다.
- 못 막는 예: ① 도메인 → 웹 import(웹 타입이 `public`이면 가능) ② 패키지·모듈 사이 순환(같은 컴파일 단위 안) ③ 명명·배치 규칙("…Controller는 web 패키지에").
- 이런 규칙이 문서에만 있으면 리뷰어가 매번 잡아야 하고, 놓친 것은 조용히 쌓인다.

### 2. 검사 흐름

```text
 .class 파일 ──> 의존 그래프(클래스 간 호출·필드 접근·타입 참조) ──> 규칙(패키지 패턴) 대조 ──> 위반(파일:줄)
```

- ArchUnit은 Java **바이트코드**를 읽는다(가이드 소개). 그래서 컴파일 뒤에 돈다.

### 3. 간선 하나, 순환 셋

(실험 A, ArchUnit 1.5.1)

```text
Cycle detected: Slice domain -> Slice web -> Slice repository -> Slice domain
Cycle detected: Slice domain -> Slice web -> Slice service -> Slice domain
Cycle detected: Slice domain -> Slice web -> Slice service -> Slice repository -> Slice domain
```

(출력의 줄바꿈을 한 줄로 이어 적었다.)

- 3개. 웹은 이미 서비스·리포지토리(우회 포함)를 거쳐 도메인에 닿는 경로가 여럿이다. 도메인 → 웹 간선 하나가 그 경로마다 고리를 닫는다.

### 4. 동결의 동작

(실험 B)

- 첫 실행: 3건을 저장소에 기록하고 **PASS**.
- 새 위반 2건: 기존 3건은 조용하고 새 2건만 **FAIL**(`NewController.n()` 두 줄).
- 기존 위반을 고침: 저장소가 3줄 → **0줄**로 줄었다(가이드: 고친 위반은 자동으로 줄여 회귀를 막는다).

### 5. 상수 인라인의 사각

(실험, `run3.sh`)

```text
[PASS] 계층 규칙
[PASS] 순환 없음
  public static int pageSize();
    Code:
       0: bipush        20
       2: ireturn
```

- 둘 다 통과했다. JLS 13.1절에 따르면 상수 변수 참조는 컴파일 때 값으로 바뀌어 바이트코드에 `bipush 20`만 남는다. `import`도 바이트코드에 남지 않는다.
- 바이트코드 도구(ArchUnit·jdeps)는 이 의존을 못 본다. 상수 소유자를 바로잡는 것이 해법이다.

### 6. 순환이 있어도 돈다

(실험 C, node v22.23.2)

```text
x 1 dependency violations (1 errors, 0 warnings). 3 modules, 3 dependencies cruised.

exit=1
{ items: [ 1000, 2000 ], invoice: 'INV-3000' }
```

- dependency-cruiser는 실패(exit=1)했지만 프로그램은 정상 출력했다. 함수가 나중에 호출되면 ES 모듈은 순환을 견딘다.
- 실행으로 드러나지 않으니 떼어내려는 순간까지 아무도 모른다. 그래서 검사가 필요하다.

### 7. 순환 제거 기법

- ① DIP 역전(인터페이스를 쓰는 쪽에 두기) ② 공통부 추출 ③ 합치기 ④ 이벤트(컴파일 의존 제거, 흐름 추적은 어려워짐) ⑤ 값의 소유자 바로잡기.
- Java: 도메인이 웹 상수를 읽던 것을 도메인 상수로 옮기고 웹이 읽게 함(⑤, 의존 방향 뒤집기) → `[PASS] 순환 없음`.
- JS: 합계 함수를 `pricing/total.js`로 추출(②) → `✔ no dependency violations found`.

### 8. 새 위반이 통과한 CI

- 동결 저장소가 VCS에 있는지, CI에서 `freeze.store.default.allowStoreCreation=true`로 매번 새로 만들어지지 않는지 확인한다. 매 빌드가 첫 실행이 되면 현재 위반이 전부 기준선이 된다.
- `freeze.refreeze=true`가 켜져 있지 않은지도 본다.
- 그 밖에 위반이 상수 인라인처럼 바이트코드에 안 남는 종류인지(5번) 확인한다.

### 9. 순환과 SCC

- 의존 그래프의 강연결요소(SCC)는 "서로 닿는 정점 묶음"이다. 크기 2 이상인 SCC가 있으면 그 안에 순환이 있다.
- 순환 검사는 결국 "SCC가 모두 크기 1인가"를 묻는 것이다(자기 자신으로 가는 간선, 즉 같은 슬라이스 안의 참조는 순환으로 치지 않는다는 전제). 알고리즘(Tarjan·Kosaraju)은 algorithm/18-scc. ArchUnit은 자체 `CycleDetector`로 개별 순환을 나열한다(상한 기본 100개).
