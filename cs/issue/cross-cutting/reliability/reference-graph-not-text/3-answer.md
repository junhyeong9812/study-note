# cs/issue/reliability/reference-graph-not-text — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **이름 ≠ 의존.** 이름은 작성자가 붙인 라벨일 뿐, "누가 이 심볼을 호출하는가"는 이름에 적혀 있지 않다.\
구버전 기능 이름이 붙은 함수라도 새 경로(예: 뷰어·스냅샷 모듈)가 쓰고 있을 수 있다 — 실제로 이름만 보고 구버전 전용으로 분류한 함수 2개가 새 경로의 의존 대상이었고, 지웠다면 빌드가 깨졌다.\
삭제 범위는 "이름이 무엇 같은가"가 아니라 "실제로 누가 참조하는가"로 정한다.
   > **참조 그래프(reference graph)** — 심볼(함수·타입·설정 키)을 노드, "A가 B를 쓴다"를 간선으로 둔 그래프. 삭제 안전성은 이 그래프에서 들어오는 간선이 0인지로 판정한다.

2. **컴파일러 주도 제거.** 먼저 제거 대상 모듈을 의존 목록(워크스페이스 멤버·빌드 의존)에서 빼면, 컴파일러가 그 모듈을 쓰던 **모든 지점**을 오류로 짚는다.\
그 지점만 지우면 "아직 쓰는 곳"은 도구가 판정하고, 공유 모듈은 오류가 안 나므로 자연히 보존된다.\
라인 단위 일괄 삭제는 사람의 분류(이름·파일 위치)에 의존해 누락·과잉 삭제가 둘 다 난다.

3. **컴파일러 밖의 참조.** 컴파일러는 소스 코드의 정적 참조만 본다. 다음은 그래프 밖이다:\
① 이름 문자열로 하는 주입(`@Qualifier("x")`, 이름 지정 리소스 주입, XML `ref=`),\
② 설정·리소스 속 FQCN(`Class.forName`, 조건부 설정의 클래스명 문자열, AOP 포인트컷 식, 직렬화 다형 타입 정보),\
③ SQL 매퍼·문자열 SQL 속 테이블·컬럼 이름.\
이들은 지우거나 옮겨도 컴파일은 통과하고, 오류가 **실행 시점**(기동 실패·500·`Unknown column`)으로 미뤄진다.
   > **FQCN** — 패키지까지 포함한 완전한 클래스 이름(`a.b.c.Foo`). 문자열로 적히면 컴파일러가 추적하지 못한다.

4. **같은 패키지 암묵 참조.** 같은 패키지의 클래스는 import 없이 쓸 수 있으므로, 그 사용처엔 치환할 문자열(`import a.b.Foo`)이 애초에 없다.\
`Foo`가 하위 패키지로 이동하면 그 클래스는 `cannot find symbol`로 깨진다 — 문자열 치환은 **표기된 참조만** 바꾸기 때문이다.\
이 경우는 컴파일러가 잡아 주므로 치환 뒤 clean compile이 안전망이 된다.

5. **파생된 이름은 계약이 된다.** 컴포넌트 기본 이름이 클래스명에서 만들어지면, 어딘가 그 **이름으로** 주입받는 곳이 있는 순간 클래스 개명은 곧 계약 변경이다(이름 조회가 실패해 기동이 멈춘다).\
타입으로만 주입받는 곳은 이름이 바뀌어도 해석이 같으므로 안전하다 — 단 타입 주입은 **구현이 정확히 하나**일 때만 해석되므로, 인터페이스 구현이 2개가 되면 단일 주입이 모호해져 기동이 실패한다.\
대응: 이름 계약이 있는 곳만 이름을 명시적으로 고정하고, 여러 구현은 `List<T>`로 받아 키로 라우팅한다(중복 키는 컨텍스트 로드가 검출).

6. **치환 전 범주 분류 + 치환 후 3중 검증.** 치환 전에 참조를 범주로 나눠 전수 grep한다: package/import · 문자열 리터럴(이름 주입·`forName`) · 리소스(yml/properties/xml/json) · 직렬화 타입 정보 · 스캔 범위 설정(`basePackages` 류).\
import/package 외 범주가 전부 0건이면 "문자열 치환 = 동작 불변"으로 판정할 수 있다.\
치환 범위는 소스 디렉토리의 소스 파일로 한정해 빌드 산출물·문서 오염을 막고, 치환 뒤엔 **잔여 grep 0 + clean compile + 테스트**로 검증한다. 배선(주입 그래프)은 mock 없는 컨텍스트 부팅 테스트로 확인한다.

7. **테스트도 그래프의 일부.** 테스트가 mock 대상으로 참조하는 인터페이스는 운영 코드에서 안 쓰여도 **들어오는 간선**이 있다.\
삭제 계획이 "운영 코드 참조 0"만 보고 "검증된 사실"로 적었다면, 그것은 그래프의 절반만 본 것이다 — 실제로 인터페이스 제거 뒤 그것을 mock하던 통합 테스트 5개가 컴파일 실패했다.\
확인 수단은 테스트 소스까지 포함한 전체 컴파일(그리고 grep 범위에 테스트 디렉토리 포함)이다.

## 문제 구조 (추상화 코드)

### 변형 A — 이름으로 판단한 대량 삭제 (컴파일러 주도 제거로 교정)
① 문제 코드
```text
# "legacy_" 접두 = 구버전 전용이라고 가정하고 일괄 삭제
delete: legacy_read_file()        # 실제로는 새 경로의 뷰어가 호출
delete: legacy_store::shared_key() # 실제로는 스냅샷 모듈이 호출
→ 새 경로 빌드 파괴
```
② 고친 코드
```text
1) workspace members 에서 legacy 모듈 제거, app 의존에서 legacy 제거   # 의존선부터 끊는다
2) build check → 컴파일러가 짚는 legacy 참조 지점만 삭제
3) 공유 모듈(timeline·snapshot 등)은 오류가 없으므로 보존
4) 이름이 모호한 심볼은 삭제 전 실코드에서 호출처 확인
```
무엇이 깨졌나: 삭제 범위를 참조 그래프가 아니라 이름으로 정했다.

### 변형 B — 문자열 치환 리팩토링이 못 보는 참조
① 문제 코드
```bash
# import 경로 일괄 치환
sed -i 's/import app\.shared\.Foo/import app.shared.sub.Foo/' $(grep -rl 'app.shared.Foo' .)
# → 같은 패키지에서 import 없이 쓰던 클래스: cannot find symbol
# → 제거한 인터페이스를 mock 하던 테스트: 컴파일 실패
```
② 고친 코드
```bash
# 1) 치환 전 범주별 전수 분류 — import/package 외 범주가 0건인지 확인
grep -rn '@Qualifier\|@Resource(name=\|ref=\|forName(' src
grep -rn 'ComponentScan\|basePackages\|execution(\|@Pointcut\|@JsonTypeInfo' src/main
grep -rn 'app\.shared' src/main/resources
# 2) 치환 범위를 소스로 한정 (빌드 산출물·문서 제외)
find src/main/java src/test/java -name '*.java' -exec sed -i 's/app\.shared/app.common/g' {} +
# 3) 3중 검증
grep -rn 'app\.shared' src --include=*.java   # 0건
build clean compile                            # 테스트 소스 포함
build test                                     # + mock 없는 컨텍스트 부팅 테스트
```
무엇이 깨졌나: 표기된 참조만 바꾸고, 암묵 참조·테스트 참조를 그래프에서 빠뜨렸다.

### 변형 C — 컴파일러 그래프 밖(SQL·설정 문자열)의 잔재
① 문제 코드
```xml
<!-- 회원 테이블 제거 후에도 매퍼가 조인 → 컴파일 통과, 목록/상세 500 -->
<select id="list">
  SELECT a.*, u.name FROM post a JOIN user_master u ON a.author_id = u.id
</select>
```
```java
// 여러 자식 테이블 SQL 을 하나로 일반화 — 한 테이블엔 del_flag 컬럼이 없음 → Unknown column
String sql = "SELECT " + cols + " FROM " + table + " WHERE key IN (:keys) AND del_flag = 0";
```
② 고친 코드
```xml
<select id="list">
  SELECT a.*, COALESCE(NULLIF(a.author_name, ''), a.author_id) AS name FROM post a   <!-- 조인 제거 -->
</select>
```
```java
// 특례를 계약(플래그)으로 드러내고, 실행 SQL 전문을 골든으로 캡처해 문자 수준 등가 강제
String sql = "SELECT " + cols + " FROM " + table + " WHERE key IN (:keys)"
           + (spec.softDelete() ? " AND del_flag = 0" : "")
           + " ORDER BY " + spec.orderBy();
// + 패키지 이동 후 리소스·설정 속 옛 FQCN 잔존 grep
```
무엇이 깨졌나: SQL·설정 문자열은 컴파일러가 모르는 참조라, 삭제·이동의 오류가 런타임으로 미뤄졌다.\
(조인 제거로 표시 이름의 의미가 "계정 실명"에서 "게시 당시 입력명"으로 바뀌는 점은 회귀 주의로 따로 기록했다.)

### 변형 D — 컴포넌트 이름이 클래스명에서 파생 (개명 = 계약 변경)
① 문제 코드
```java
@Component class ImportServiceImpl implements ImportPort { }     // 기본 이름 = 클래스명 파생
// ...
@Autowired @Qualifier("importServiceImpl") ImportPort port;           // 이름으로 주입
// → 클래스를 개명하면 이름 조회 실패; 구현이 2개가 되면 타입 단일 주입도 실패
```
② 고친 코드
```java
@Service("importService") class ImportServiceV2 implements ImportPort { }          // 계약 있는 곳만 이름 고정

// 여러 구현은 목록으로 받아 키로 라우팅 (중복 키는 컨텍스트 로드가 검출)
Map<String, Runner> byRegion = runners.stream()
    .collect(toUnmodifiableMap(Runner::region, identity()));
```
무엇이 깨졌나: 클래스명에서 파생된 이름이 문자열 계약으로 쓰이고 있어, 개명이 곧 주입 그래프 변경이었다.\
(예방·설계 기록 — 실제 기동 실패 사고 기록은 없다.)

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
