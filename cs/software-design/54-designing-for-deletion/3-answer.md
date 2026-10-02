# software-design/54-designing-for-deletion — 정답

## 정답

### 1. 지우기 쉬운 코드

- 코드는 쓰는 순간부터 유지보수 비용이 든다. tef는 Dijkstra(EWD 1036)를 인용해 코드 줄을 "생산한 줄"이 아니라 "쓴(지출한) 줄"로 보자고 한다.
- 그렇게 보면 지우는 것이 비용을 낮추는 일이다. 확장하기 쉬운 코드는 "석 달 뒤에도 내가 다 맞았기를" 바라는 것이고, 지우기 쉬운 코드는 그 반대 가정 위에서 일한다(같은 글).

### 2. 반복과 DRY

- 정면 충돌은 아니다. tef가 말하는 것은 **반복의 목적**이다.
  - 의존을 피하려는 반복(작은 코드를 두 곳에 두어 공유 의존을 안 만듦)은 괜찮다.
  - 이미 생긴 의존을 관리하려고 같은 처리를 여러 곳에 반복하는 것은 피하라.
- 공유 API가 어려워지는 이유: 호출자가 늘수록 바꿀 때 다시 써야 할 코드가 늘고, 호출자는 문서가 아니라 관찰한 동작(의도하지 않은 동작 포함)에 기댄다. 그래서 "함수 안의 코드를 지우는 것이 함수를 지우는 것보다 쉽다".
- DRY의 "지식의 단일 표현"과 "글자 중복 제거"의 구분은 11 when-to-abstract에서 다룬다.

### 3. 도달성 그림과 놓치는 간선

```text
 루트(main·핸들러·스케줄러·리스너) → 참조 간선을 따라 BFS → 닿은 집합
 전체 − 닿은 집합 = 죽은 코드 후보
```

- 놓치는 간선: 리플렉션(`Class.forName` 문자열), 설정 파일의 클래스·빈 이름, DI 컨테이너의 스캔·자동 연결, 직렬화·ORM 프레임워크가 만드는 객체, 다른 서비스·배치가 부르는 외부 엔드포인트.
- 그래서 정적 결과는 "후보"다. 실행 시 관측으로 확인한다.

### 4. jdeps 기본값

(실험 F1, JDK 21.0.12, 2026-10-02)

```text
$ jdeps -verbose:class out  (기본 -filter:package)
0
  도달 불가(죽은 코드 후보): [shop.LegacyCsvExporter, shop.OldPriceCalc, shop.OrderService, shop.PriceCalc, shop.RoundingHelper]
...
  루트 shop.App에서 도달: [shop.App, shop.OrderService, shop.PriceCalc]
  도달 불가(죽은 코드 후보): [shop.LegacyCsvExporter, shop.OldPriceCalc, shop.RoundingHelper]
```

- 기본(`-filter:package` — 같은 패키지 의존을 거른다): `shop.*` 간선 0개. 루트 자신 외 전부가 후보로 나온다(틀린 결과).
- `-filter:none`: 간선 3개가 보이고, 후보는 셋.

### 5. 정적 후보를 다 지우면

```text
$ (정적 분석의 죽은 코드 후보 3개를 지우고 빌드) javac 종료코드 0
3000
Exception in thread "main" java.lang.ClassNotFoundException: shop.LegacyCsvExporter
exit=1
```

- 컴파일: 성공(정적 참조가 없으니까).
- 실행: `ClassNotFoundException`. `LegacyCsvExporter`는 설정 문자열로 `Class.forName` 되는 클래스였다. `-Xlog:class+load` 출력에도 적재된 것으로 나왔다.
- 진짜 죽은 것은 `OldPriceCalc`와, 그것만 부르던 `RoundingHelper` 둘이다.

### 6. 플래그 제거 커밋

(실험 F2)

```text
== scattered 제거 커밋
 6 files changed, 6 insertions(+), 26 deletions(-)
== central 제거 커밋
 2 files changed, 1 insertion(+), 4 deletions(-)
```

- 흩어진 설계 6파일(분기 5곳 + 플래그 정의), 모인 설계 2파일(팩토리 수정 + 옛 구현 삭제).
- 처음 구조: central이 파일 9개(인터페이스·구현 2개·팩토리 추가)로 scattered 7개보다 많았다(scattered 쪽 7에는 실험용 `Main` 1개 포함). 줄 수는 분기 중복이 없는 central이 적었다(33 대 54). 분기가 한두 곳뿐이라면 central 구조가 과할 수 있다.

### 7. 설정만 지운 플래그

```text
플래그 있음: Cart:new Order:new Payment:new Receipt:new Mail:new
플래그 설정 삭제: Cart:old Order:old Payment:old Receipt:old Mail:old
```

- 원인: 코드에 `else`(옛 경로)가 남아 있고, "없는 플래그"의 기본값이 false(= 옛 경로)다. 설정 한 줄 삭제가 옛 동작을 되살렸다. 에러는 없다.
- 대처: 플래그를 100%로 고정했으면 코드의 분기부터 지우고 설정은 그다음에 지운다. 플래그 키를 재사용하지 않는다. 만료일·시한폭탄 테스트로 남은 플래그를 드러낸다.
- 같은 유형: Knight Capital(2012) — 옛 기능용 플래그를 재사용했고, 새 코드가 배포되지 않은 서버에서 그 플래그가 옛 코드를 켰다([reliability/24](../../reliability/24-feature-flag-lifecycle/2-summary.md)).

### 8. forRemoval만으로 못 막는 이유

(실험 F3)

```text
$ javac Dep.java
Dep.java:8: warning: [removal] sendOld(String) in LegacyApi has been deprecated and marked for removal
exit=0
$ javac -Werror Dep.java
error: warnings found and -Werror specified
exit=1
```

- 경고는 나오지만 빌드는 성공한다(exit 0). CI가 경고를 오류로 다루지 않으면 새 호출이 들어온다.
- 막으려면: `-Werror`(또는 빌드 도구의 경고-오류 설정), 대체 API를 `{@link}`로 안내, 런타임 호출 카운터로 0 유지 확인.
- JEP 277: `@SuppressWarnings("deprecation")`은 removal 경고를 끄지 않는다. 기존에 일반 deprecation 경고를 꺼 둔 호출처에서도 제거 예정 경고가 보이게 하려는 설계다.

### 9. 주석 처리 코드 대신 git

- 지운다. 이력은 git이 갖고 있다. 주석 처리 코드는 컴파일·테스트를 안 거쳐 낡고, 읽는 사람이 살아 있는지 매번 판단해야 한다.
- 찾기: `git log -S'<문자열>'`(그 문자열의 등장 횟수가 바뀐 커밋) → `git show <hash>~1:<path>`(지우기 전 내용). 실험 F2 저장소에서 `git log -S':old"'`가 제거 커밋과 최초 커밋을 찾았다.

### 10. carrying cost를 줄이는 실천

- Hodgson "Feature Toggles" 「Managing the carrying cost」:
  - 릴리스 토글을 만들 때 제거 작업을 백로그에 같이 넣는다.
  - 토글에 만료일을 붙인다.
  - 만료가 지나면 테스트를 실패시키거나 기동을 거부하는 "시한폭탄"을 둔다.
  - 동시에 둘 수 있는 플래그 수에 상한을 두고, 넘으면 하나를 지워야 새로 만든다.
- 50과의 연결: Strangler Fig도 전환을 라우팅 비율(플래그와 같은 구조)로 한다. 100% 전환 뒤 구 경로·라우팅 규칙을 지우는 단계가 빠지면 두 시스템이 영구 병존한다. 같은 "지울 날을 처음부터 계획하라"는 규칙이다.
