# cs/issue/reliability/sibling-path-invariant-drift — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **이진 탐색은 정렬을 전제한다.** 형제 setter 9개가 저장 시 정렬하므로 소비자는 "저장된 배열은 정렬돼 있다"를 가정하고 이진 탐색한다. 한 setter만 정렬을 빠뜨리면 그 배열에 대한 탐색은 **값의 위치에 따라** 우연히 맞거나 조용히 빗나간다.\
기본 설정 파일은 작성자가 우연히 사전순으로 적어 두어 문제가 없었고, 잘 알려진 코드들은 다른 폴백 경로(표준 상태 코드 기반 분류)가 처리해 가렸다. 그래서 사용자가 자기 순서로 적은 커스텀 값에서만 드러났다 — 결과는 "중복 키" 대신 일반 무결성 위반 예외(또는 미번역 예외)가 나오는 것이다 — `catch (중복 키 예외)`에 의존한 코드(upsert 관용구 등)가 깨질 수 있다는 것은 일반론적 영향이다.\
교정은 형제 관례에 합류하는 1줄(저장 시 정렬)이고, 테스트는 사전식 비교("1062" < "121")까지 고려해 자릿수를 섞는다.
   > **저장측 불변식** — 저장 시점에 보장해 두면 모든 소비자가 따로 검사하지 않아도 되는 성질(정렬·정규화 등). 저장 경로 하나라도 빠지면 소비자 전부가 틀린다.

2. **부분 매치를 되감지 않은 매처.** 매처 기반 클래스는 "불일치 시 후퇴는 서브클래스가 한다"는 계약이었다. 일반 KMP 매처는 실패 함수로 되감지만, 2바이트 전용 매처만 그 오버라이드가 없어 `\r`을 본 뒤 `X`가 와도 "1바이트 매치" 상태에 얼어붙었다.\
그 뒤 떨어진 위치의 `\n`이 오면 비연속 두 바이트로 매치가 완성되고, 디코더는 "구분자 길이(2)만큼 제거"하므로 실제 데이터 1바이트가 사라진다. 예외도 로그도 없다.\
줄 안에 단독 `\r`이 있는 입력(구형 개행·CSV)에서만 발생해 오래 잠복했다. 교정은 서브클래스에 되감기 오버라이드(2바이트는 실패 함수의 목적지가 0뿐이라 `while`이 `if` 하나가 된다) — 기반 클래스를 리셋하게 고치면 KMP 형제의 백트랙이 깨지므로 수정 범위를 서브클래스에 국한했다.

3. **분기마다 따로 구현하면 한 분기만 빠진다.** 자동 탐색 분기는 생성 키를 제외했지만 명시 컬럼 분기는 제외하지 않아, INSERT placeholder 1개 vs 값 배열 2개가 되어 드라이버 파라미터 인덱스 오류가 났다.\
누락 분기에 복사하면 지금은 맞지만 불변식이 여전히 두 곳에 있어 다음 변경에서 또 갈린다. 필터 집합 생성을 **두 분기의 공통 지점으로 끌어올리면** 불변식이 한 곳에만 존재한다.\
(이 사례는 리뷰어 요청으로 "조용히 제외" 대신 "겹치면 즉시 거부(fail-fast)"로 의미를 바꿔 최종 반영됐다 — 비대칭을 고칠 때 어느 쪽 의미가 맞는지도 다시 묻게 된다.)

4. **N벌 사본은 N번 고쳐야 한다.** 한 벌만 고치면 나머지는 에러 없이 옛 동작으로 계속 돈다 — 사본끼리는 서로를 참조하지 않으므로 아무것도 깨지지 않는다.\
실제로 와일드카드 감지를 한 사본에만 넣어 나머지 사본들에서는 와일드카드가 문법 파서를 우회했고, 다른 개선은 반대로 일부 사본에만 들어가고 원본에는 빠졌다.\
누락은 **구조가 비대칭인 모듈**(다른 사본과 필드 구성이 다른 모듈)에서 나기 쉽다 — 기계적으로 옮기기 어렵기 때문이다(원 기록의 집계가 아니라 사례에서 끌어낸 해석).

5. **빈 값은 유효한 값이다.** 원본은 `if 주 입력 있음 … elif 보조 입력만 있음 …`이었는데, 재구현이 "단일 흐름"으로 다시 쓰면서 `elif` 쪽(보조 입력에서 필드 채우기)을 옮기지 않았다.\
그 결과 필드가 빈 문자열로 저장됐지만, 빈 문자열은 타입·널 검사를 모두 통과하는 정상 값이라 어떤 검사에도 걸리지 않았고 그 필드 기반 기능만 조용히 매칭 불가가 됐다.\
탐지는 원본과 재구현을 **줄 단위로 대조한 차이표**다. 교정은 누락 분기 추가 + 이미 저장된 데이터의 재처리(재색인).

6. **손으로 맞추는 병렬 구현은 한 곳이 빠진다.** 필드 하나가 직렬화·equals·hashCode·복제 네 곳에 나타나야 하는데, 구조가 이를 강제하지 않으면 한 곳 누락이 남는다.\
equals에서 빠지면 다른 값이 같다고 판정되고, 직렬화에서 빠지면(equals에는 있어도) 원격으로 보낸 값이 사라지는 기능 버그가 된다.\
변이 기반 테스트는 "필드 하나를 바꾼 인스턴스는 달라야 한다"를 필드별로 검사해야 하는데, 그 변이 목록이 비어 있거나 새 필드를 안 다루면 누락을 못 잡는다.

7. **형제 전수 대조.** 결함 하나를 찾으면 "같은 불변식을 지켜야 하는 다른 경로"를 전부 나열하고(다른 setter, 다른 분기, 다른 서브클래스, 다른 복사본, 포팅 원본, 반대편 직렬화) 하나씩 같은 가드가 있는지 확인한다 — 비교표로 남긴다.\
이 대조로 오히려 **형제 쪽의 다른 비대칭**(예: 한 접근자만 이벤트 타입 가드가 없어 예외 타입이 경로마다 다름)이 추가로 발견되기도 한다.\
근본 대책은 불변식이 한 지점에만 존재하는 구조다: 공통 지점으로 끌어올리기, 공통 베이스 클래스로 승격, 저장 시 정규화, 주입된 추상화(시계 등)만 쓰기.

## 문제 구조 (추상화 코드)

### 변형 A — 형제 setter·접근자 중 하나만 가드·정규화 누락
① 문제 코드
```java
class ErrorCodes {
  void setGrammarCodes(String... c)  { this.badGrammar  = sortStringArray(c); }
  void setIntegrityCodes(String... c)   { this.integrity   = sortStringArray(c); }
  // ... 형제 8개 모두 정렬
  void setDuplicateCodes(String... c){ this.duplicateKey = c; }            // 이것만 정렬 누락
}
// 소비자
else if (Arrays.binarySearch(codes.getDuplicateKeyCodes(), errorCode) >= 0) { ... }   // 정렬 전제
```
② 고친 코드
```java
void setDuplicateCodes(String... c) { this.duplicateKey = sortStringArray(c); }   // 형제 관례 합류
// 테스트: 임의 순서·자릿수 혼합("90002","1586","1062") 에서 모든 값이 매칭되는지
```
무엇이 깨졌나: 저장측 불변식(정렬)을 형제 중 하나가 지키지 않아, 소비자의 전제가 그 배열에서만 거짓이 됐다.\
같은 구조:\
- setter가 파라미터 대신 **필드**를 null 검사(복붙 오타) → null이 저장되고 다음 사용 시 지연 NPE. 교정: 파라미터 검사.\
- 시계(Clock)를 주입해 놓고 만료 정리 경로 하나만 시스템 시계를 직접 호출 → 고정 시계 테스트에서 미만료 토큰이 삭제됨. 교정: 주입된 시계 사용(확인만 하고 기여는 보류).\
- 검증 메서드가 인터페이스가 강제한 이름 파라미터를 무시(no-op 단언) + 형제 접근자 중 하나만 이벤트 타입 가드 부재로 예외 타입이 경로마다 다름 → 이름 대조 추가, 가드 부재는 별도 후보로 이월.

### 변형 B — 형제 서브클래스 중 하나만 계약된 오버라이드 누락
① 문제 코드
```java
abstract class DelimiterMatcher {
  boolean match(byte b) { if (b == delimiter()[matches]) matches++; ... }   // 불일치 후퇴는 서브클래스 몫 (계약)
}
class KmpMatcher extends DelimiterMatcher {
  boolean match(byte b) {
    while (matches > 0 && b != delimiter()[matches]) matches = table[matches - 1];   // 후퇴 ✓
    return super.match(b);
  }
}
class PairMatcher extends DelimiterMatcher { }                           // 후퇴 오버라이드 없음 ✗
// "\r X \n" → matches=1 에 얼어붙음 → 뒤늦은 \n 이 비연속 매치 완성 → 디코더가 2바이트 제거 → 데이터 1바이트 유실
```
② 고친 코드
```java
class PairMatcher extends DelimiterMatcher {
  boolean match(byte b) {
    if (matches > 0 && b != delimiter()[matches]) matches = 0;             // 상태 공간 {0,1} → while 이 if 하나
    return super.match(b);
  }
}
// 기반 클래스를 고치지 않는다 (KMP 형제의 백트랙이 깨짐)
// 테스트: 입력을 여러 버퍼로 쪼개 버퍼 경계를 넘는 부분 매치 상태까지 검증
```
무엇이 깨졌나: 기반 클래스가 서브클래스에 위임한 불변식을 형제 중 하나만 구현하지 않았다.

### 변형 C — 분기·케이스 중 하나만 불변식 누락
① 문제 코드
```java
Set<String> keys = null;
if (declaredColumns.isEmpty()) {
  keys = toUpper(generatedKeyNames);
  for (col : discovered) if (!keys.contains(col.upper())) use.add(col);    // 자동 탐색 분기: 생성 키 제외 ✓
} else {
  use.addAll(declaredColumns);                                            // 명시 분기: 제외 누락 ✗ → placeholder 수 ≠ 값 수
}
```
② 고친 코드
```java
Set<String> keys = toUpper(generatedKeyNames);                            // 공통 지점으로 끌어올림
List<String> source = declaredColumns.isEmpty() ? discoveredNames() : declaredColumns;
for (String col : source) if (!keys.contains(col.toUpperCase())) use.add(col);
// (최종 반영은 리뷰 요청에 따라 "겹치면 즉시 거부" 로 의미 반전)
```
무엇이 깨졌나: 같은 불변식을 분기마다 따로 구현해 한 분기에서만 빠졌다.\
같은 구조:\
- 줄 사이에 유지되는 "주석 안" 상태를 한 판정 함수만 존중하고, 주석 소비 함수의 조기 반환(마커 없는 줄)은 무시 → 주석 본문 속 문서형 선언 문자열로 문서 종류를 오판. 교정은 증상 지점이 아니라 계약 지점(주석 소비 함수가 "주석 제외 내용"을 반환)에서 `inComment ? "" : line`.\
- 지연 예외가 날 수 있는 속성을 미리 호출해 보는 판정식이 단일 열거형·클래스만 포함하고 **열거형 배열·중첩 애너테이션**을 누락 → 오염된 값이 맵에 들어가고 타입 접근 시 원시 예외 누출. 교정: 판정식에 두 형태 추가 + 중첩이면 재귀 확인(중첩 타입 자체가 없는 경우는 파싱 단계 오류라 원리적으로 방어 불가 — 한계 명시).\
- 원시 타입 배열 8종 중 스트림 변환 메서드가 있는 3종만 원시 배열로 만들고 나머지 5종은 기본 분기에서 박싱 → 타입 불일치 예외. 빈 배열은 조기 반환이라 기존 테스트(정수 배열·빈 배열)가 못 잡음. 교정: 5종 케이스 추가.\
- 같은 메서드의 반환 타입 경로는 이전에 헬퍼로 고쳤지만 파라미터 경로만 단순 문자열 조립(`packageName + "." + name`)으로 남아 원시·배열 타입이 `.int`로 출력. 교정: 파라미터도 같은 헬퍼.

### 변형 D — 모듈 N벌 복사본 간 드리프트
① 문제 코드
```python
# module_a/parser.py
def contains_grammar(value):
    if any(ch in value for ch in "*?%"): return True     # 이 사본에만 추가됨
    # ...
# module_b/parser.py, module_c/parser.py, ...
def contains_grammar(value):
    # ... 와일드카드 감지 없음 → 와일드카드가 문법 파서를 우회
```
② 고친 코드
```python
class BaseQueryParser(ABC):                             # 공통 베이스로 승격 (장기 계획)
    def contains_grammar(self, value):
        if any(ch in value for ch in "*?%"): return True
        # ...
class ModuleAParser(BaseQueryParser): config = A_CONFIG   # 사본마다 다른 것은 설정 1줄뿐
# 즉시 조치: 누락 사본에 같은 패치 + 사본 전수 비교표로 확인, 가드는 공통 validator 로 이동
```
무엇이 깨졌나: 같은 로직의 N벌 사본 중 일부만 고쳐져, 나머지가 조용히 옛 동작을 유지했다.\
같은 구조: OR 처리 개선이 한 사본에만 적용·미전파, 변환 규칙 개선이 일부 사본에만 있고 원본에 누락, 위험 패턴 가드가 사본·경로별로 비대칭, 파서 파사드가 설정 1줄 차이로 N벌 복사.

### 변형 E — 포팅·재구현·추출 리팩토링 중 원본의 분기·가드 누락
① 문제 코드
```python
# 원본
if primary:
    derived = build_from_primary(primary)
elif secondary_only:
    derived = build_from_secondary(secondary)            # 보조 입력만 있을 때 채우는 분기
# 재구현 ("단일 흐름")
derived = build_from_primary(primary)                    # primary 가 없으면 "" → 에러 없이 빈 필드 저장
```
② 고친 코드
```python
derived = build_from_primary(primary)
if secondary and not primary:                            # 원본과 줄 단위 대조표로 찾은 누락 분기
    derived = build_from_secondary(secondary)
# + 이미 저장된 데이터 재처리
```
무엇이 깨졌나: 재구현이 원본의 드문 분기를 옮기지 않았고, 빈 값은 유효한 값이라 아무 검사도 못 잡았다.\
같은 구조:\
- 적재 경로를 새로 옮기면서 옛 경로에만 있던 전처리(원천별 구분자 분할)가 빠짐 → 구분자를 파라미터로 주입하는 공통 함수로 통합.\
- 증분 기준을 부모 테이블 갱신 시각만 봐서 자식 테이블만 바뀐 행을 놓칠 수 있음 → 결과에 기여하는 모든 테이블의 변경을 봐야 함(설계만 기록, 보류된 잠재 리스크).\
- 옛 구현을 새 코어로 옮길 때 옛 코드에 있던 **주소 family 가드**가 빠져, 4바이트/16바이트 주소를 길이 비교 없이 바이트 루프로 비교 → IPv4 매처가 IPv6 주소에 참, 반대 방향은 배열 범위 초과. 교정: `if (a.length != b.length) return false;`(이미 상류에 같은 수정이 있어 기여는 하지 않음).\
- 메서드 추출 리팩토링에서 파라미터 누락·null 검사 소실이 반복 → 추출 전후 호출 인자 1:1 대조 + 기존 테스트 우선 실행.

### 변형 F — 직렬화 ↔ equals·hashCode 병렬 구현의 비대칭
① 문제 코드
```java
void writeTo(Out out) { out.writeInt(size); out.writeBool(keyed); ... }
boolean equals(Object o) { return keyed == ((Builder) o).keyed; }        // size 누락
int hashCode() { return Objects.hash(keyed); }
// 테스트의 변이 함수가 비어 있음(null) → 필드별 동등성 검사가 돌지 않음
```
② 고친 코드
```java
boolean equals(Object o) { var b = (Builder) o; return keyed == b.keyed && size == b.size; }
int hashCode() { return Objects.hash(keyed, size); }
Builder mutate(Builder in) { return switch (rnd(2)) { case 0 -> in.withKeyed(!in.keyed); default -> in.withSize(in.size + 1); }; }
// 역방향(equals 에는 있으나 직렬화 누락)은 기능 버그 → 직렬화 추가 + 와이어 버전 증가
```
무엇이 깨졌나: 한 필드가 나타나야 할 네 곳을 손으로 맞추는 구조에서 한 곳이 빠졌고, 변이 테스트가 비어 있어 드러나지 않았다.\
같은 구조: 비교에서 실제 필드 대신 항상 null인 흔적 필드를 비교, 내부 값 객체의 필드 누락.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~F)은 "누락 형제를 관례에 합류시키고, 가능하면 불변식을 한 지점으로 모은다"이다. 같은 원리(형제 사이의 대응·규약이 한쪽만 바뀌는 비대칭)에 다른 방안이 쓰인 사례:

### 방안 1 — 병렬 배열의 1:1 대응: append 순서 교정
```python
# 문제: 두 리스트를 인덱스로 짝지어 쓰는데 한쪽만 조건부로 건너뛰거나 먼저 append
for hit in hits:
    keys.append(key_of(hit))                             # 먼저 무조건 추가
    try:
        results.append(normalize(hit))                   # 실패하면 results 만 빠짐 → keys[i] ↔ results[i] 밀림
    except Exception:
        pass
# 고친: 성공 이후에 양쪽을 함께 추가, 조건부 제거(빈 값도 ""로 추가), 실패면 양쪽 모두 건너뜀
for hit in hits:
    try:
        r = normalize(hit)
        results.append(r)
        keys.append(key_of(hit) or "")
    except Exception:
        continue
```
형제 = 서로 대응해야 하는 두 컬렉션. 기록된 교정은 추가 순서의 원자화이며, 쌍(튜플) 하나의 리스트로 합치는 구조적 대안은 원 기록에서 채택되지 않았다(대응 자체를 구조로 없애는 일반적 선택지로만 언급).

### 방안 2 — 경계 재배치 시 반환 형태·식별자 규약을 한쪽만 변경
```python
# 문제: 구현부는 dict 를 반환하도록 바뀌었는데 호출부는 여전히 list 로 취급
normalized = normalizer.normalize(hits)                  # {"results": [...], "keys": [...]}
for r in normalized: ...                                 # dict 를 순회 → 키 문자열을 결과로 오인
# 고친: 반환 형태를 모든 구현에서 통일 + 호출부에서 명시 분해
normalized = normalizer.normalize(hits)
results, keys = normalized["results"], normalized["keys"]
# 식별자 규약: 클라이언트가 보낸 코드 문자열 ≠ 서버 열거형 값 → 422 → 클라이언트 매핑 교정(서버 무변경)
# 요청 본문: raw dict 직접 접근 → 요청 모델(스키마 검증)로
```
타입 강제가 없는 dict·문자열 경계에서는 구현부와 호출부가 서로 다른 형태를 가정해도 로드 시점에 아무것도 깨지지 않는다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 형제 합류 + 한 지점으로 모으기 | 같은 불변식을 지켜야 할 형제를 나열할 수 있다 | 형제 전수 대조·리팩토링 | 모으지 않고 합류만 하면 다음 변경에서 재발 | setter·분기·서브클래스·사본·포팅 |
| 1. 대응 컬렉션의 추가 원자화 | 두 컬렉션을 계속 따로 유지해야 한다 | 추가 순서 규율 | 새 조건부 분기가 한쪽만 건너뛰면 재발 | 기존 인터페이스가 병렬 배열을 요구할 때 |
| 2. 경계 형태 통일 + 명시 분해·스키마 | 경계에 타입 강제가 없다 | 호출부·구현부 동시 수정 | 한쪽만 고치면 런타임에만 드러남 | dict·문자열로 주고받는 모듈 경계 |

**결론**: 형제가 **같은 불변식을 각자 구현**하는 경우(기본)는 즉시 합류시키고 불변식을 한 지점으로 모으는 것이 재발을 막는다.\
형제가 **서로 대응해야 하는 두 표면**(병렬 배열·호출부↔구현부)인 경우는 대응을 원자적으로 갱신하거나(1), 경계에 형태를 명시하고 검증하는 것(2)이 맞다.\
어느 쪽이든 한 곳에서 결함을 찾은 순간 형제 전수를 대조하는 것이 첫 동작이다.
