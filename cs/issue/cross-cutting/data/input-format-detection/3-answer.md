# cs/issue/data/input-format-detection — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **예외 없는 오답.**\
   파서는 "찾으라는 것"을 찾는다 — 다른 형식의 입력에서 그것이 없으면 **빈 결과**, 구분자가 다르면 **다르게 자른 결과**, 스칼라를 기대하면 **첫 값**을 돌려줄 뿐 형식이 틀렸다는 사실을 모른다.\
   에러는 그 자리에서 멈추고 드러나지만, 그럴듯한 오답은 다음 단계로 **흘러가 적재·집계·표시**되고 사용자가 이상을 느낄 때에야 발견된다. 그 사이 오염 범위가 커진다.

2. **이름은 RSS, 내용은 Atom.**\
   Atom은 항목이 `<item>`이 아니라 **네임스페이스가 있는 `<entry>`** 이고, 링크가 텍스트 노드가 아니라 **`href` 속성**이다.\
   RSS 파서의 `findall("item")`과 네임스페이스 없는 검색은 둘 다 0건 — HTTP는 200이라 "수집 성공, 새 글 없음"처럼 보인다.\
   교정: 네임스페이스 맵으로 `entry`를 찾고, `link.get("href")`, id가 없으면 link로 폴백.
   > **XML 네임스페이스** — 요소 이름에 URI를 붙여 구분하는 방식. 네임스페이스가 있는 요소는 접두어 없는 이름으로 검색되지 않는다.

3. **다중값 절단의 발견과 검증.**\
   절단은 에러를 내지 않으므로 **값 분포**로 드러난다(일반론 — 이 사례의 발견 경위는 기록돼 있지 않다). 실측: 한 소스에서 행의 36%가 쌍을 2개 담고 있었는데 첫 쌍만 남고 나머지가 소실됐다.\
   교정은 다중값을 1급으로 다루는 것: 자식 테이블 + 날짜를 인식하는 무손실 페어링 파서, CSV 필드 크기 한도 상향(480KB가 넘는 셀 대응).\
   검증은 **같은 변환으로 기대 카디널리티를 독립 계산**해 DB `COUNT`와 대조한다. 빈 필드는 파서가 아니라 수집 실패(소스 부재)로 판명된 경우도 있으니 원인을 분리한다.\
   멀티라인 CSV는 한 레코드가 여러 줄에 걸치므로(RFC4180 인용 필드 안 개행) 줄 단위 `head`로 자르면 레코드가 중간에서 끊긴다 — 샘플도 CSV 리더로 뽑는다.

4. **소스별 구분자.**\
   구분자 기반 파싱은 가정이 틀려도 **예외 없이** 다르게 자른 결과를 낸다(실측: 에러 없이 진행돼 사용자가 발견).\
   파이프라인 안에서 잡으려면 소스별로 형식을 **명세하고 검증**해야 한다 — 예: 분리 후 조각 수·조각 길이 분포가 소스 간에 같은 모양인지, 알려진 샘플 값이 기대대로 분리되는지. 실제 대응은 전처리 사양 재정의 후 재적재였다.

5. **렌더러 형식 가정.**\
   마크다운 렌더러는 입력을 마크다운(+HTML)으로 해석하므로, HTML·CSS·JS 코드 파일의 태그가 **해석되어** 에러 없이 뭉개진다. 반대로 마크다운 분석문을 평문으로 출력하면 `**중요**`·`## 요약`이 그대로 노출된다.\
   판정 → 경로: `domain === 'code' || 코드 확장자` **이중 신호**면 `<pre>`(white-space: pre)로, 분석문은 마크다운 렌더러로.\
   사각지대: domain과 경로가 **둘 다 없으면** 여전히 마크다운으로 샌다 — 판정 신호가 없을 때의 기본값이 남은 위험이다.

6. **glob과 UNIQUE.**\
   재귀 glob은 **종류를 가리지 않고** 모든 파일을 흡수한다. UNIQUE 제약은 "같은 것이 두 번"만 막을 뿐 "들어오면 안 되는 것"은 막지 못한다 — 비대상 파일도 저마다 유일하니까.\
   blocklist는 모르는 종류가 새로 나타나면 다시 샌다 → 삭제 후 **언어별 확장자 allowlist**로 재수집했다.\
   같은 배치의 곁가지: `//` 라인 주석을 전제한 헤더 추출 파서는 설명이 다음 줄에 오는 `/* */` 블록 주석을 코드로 판정해 CSS에서 0건이었다(의도적으로 보류).

## 문제 구조 (추상화 코드)

### 변형 A — 이름으로 형식 추정 (피드)
① 문제 코드
```python
root = ET.fromstring(body)
for item in root.iter("item"):                       # Atom이면 0건, HTTP 200
    link = item.findtext("link")
    # ...
```
② 고친 코드
```python
ns = {"a": "http://www.w3.org/2005/Atom"}
for entry in root.findall("a:entry", ns):
    link_el = entry.find("a:link", ns)
    link = link_el.get("href") if link_el is not None else None   # 링크는 속성
    eid = entry.findtext("a:id", namespaces=ns) or link             # id 없으면 link 폴백
    # ...
```
무엇이 깨졌나: URL 경로명을 형식 정보로 믿었다.

### 변형 B — 다중값 셀을 스칼라로 파싱
① 문제 코드
```python
def split_first_pair(cell):
    num, date = first_pair(cell)                     # (번호,날짜) 반복 중 첫 쌍만
    return num, date
```
② 고친 코드
```python
csv.field_size_limit(2**31 - 1)                     # 거대 셀
def parse_pairs(cell) -> list[Pair]:
    return pair_all_date_aware(cell)                 # 무손실 페어링 → 자식 테이블에 N행
# 검증: expected = sum(len(parse_pairs(r[col])) for r in csv.DictReader(f)); assert expected == db_count()
```
무엇이 깨졌나: 스칼라 가정이 다중값을 오류 없이 첫 값으로 잘랐다.

- 같은 구조: 소스마다 구분자가 다른 필드에 `desc.split(",")` 일괄 적용 → 전처리 사양을 소스별로 재정의 후 재적재.

### 변형 C — 렌더 경로를 형식 판정 없이 선택
① 문제 코드
```tsx
<Markdown>{doc.body}</Markdown>                      // 코드 파일도 마크다운으로 해석
```
② 고친 코드
```tsx
const isCode = doc.domain === "code" || CODE_EXT.test(doc.path ?? "");
return isCode
  ? <pre className="code-block">{doc.body}</pre>     // white-space: pre
  : <Markdown>{doc.body}</Markdown>;
// 사각지대: domain·path 둘 다 없으면 마크다운으로 샘
```
무엇이 깨졌나: 렌더러가 입력 형식을 가정해, 다른 형식의 데이터를 에러 없이 잘못 해석했다.

### 변형 D — 수집 대상 종류 미판정
① 문제 코드
```python
files = glob.glob(os.path.join(d, "**", "*"), recursive=True)   # 레퍼런스 .html 까지 흡수
```
② 고친 코드
```python
EXT = {"java": "*.java", "js": "*.js", "python": "*.py", "rust": "*.rs", "css": "*.css"}
files = glob.glob(os.path.join(d, "**", EXT[lang]), recursive=True)   # allowlist
```
무엇이 깨졌나: 재귀 glob과 UNIQUE 제약만으로는 "들어오면 안 되는 것"을 막지 못했다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
