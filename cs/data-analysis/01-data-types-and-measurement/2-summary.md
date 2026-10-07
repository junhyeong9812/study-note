# data-analysis/01-data-types-and-measurement — 변수 유형과 측정 척도: 어떤 계산이 의미 있나 — 정리 (힌트)

## 해결하는 문제

숫자로 저장돼 있다고 해서 숫자처럼 계산해도 되는 것은 아니다.

```text
  설문 "만족도" 응답            1 = 매우 불만 … 5 = 매우 만족
  대시보드                      평균 만족도 3.4점  ← 이 숫자는 무엇을 뜻하나?
  우편번호 컬럼(int)            avg(zip) = 3735     ← 계산은 되지만 뜻이 없다
```

- 계산기는 값의 **뜻**을 모른다. "더해도 되나, 순서를 매겨도 되나, 비율을 말해도 되나"는 값이 무엇을 재는지에 달렸다.
  - *변수(variable)*: 관찰 대상(사용자·주문 등)마다 기록하는 하나의 특성. 표에서는 한 열이다.
  - *측정 척도(level of measurement)*: 값 사이에 어떤 관계(같다·크다·차이·비율)가 의미 있는지에 따른 분류.

쉬운 예: 등번호 10번 선수가 5번 선수보다 "두 배" 잘하지 않는다.\
등번호는 이름표다. 숫자 모양이지만 크기 비교도 덧셈도 뜻이 없다.

똑같은 구조다.\
주문 상태 코드(`10`=접수, `20`=결제, `30`=배송), 우편번호, 전화 국번, 설문 점수가 모두 "숫자 모양의 이름표"이거나 "순서만 있는 숫자"다.

실무 예:
- 설문 만족도(1~5)를 평균 내 "3.4점 → 3.6점, 개선"이라고 보고한다. 점수 간격이 같다는 가정이 숨어 있다.
- 우편번호를 정수로 적재해 `01234`가 `1234`가 된다. 지역별 집계가 깨진다.
- 섭씨 온도로 "어제보다 두 배 덥다"고 말한다.

## 동작·원리

### 1. 변수 유형 — 나무 하나

```text
                        변수
              ┌──────────┴──────────┐
           수치형                  범주형
        (더하고 평균 냄)          (값이 범주)
        ┌─────┴─────┐          ┌─────┴─────┐
      연속형      이산형        명목형      순서형
     (지연 ms)   (주문 수)    (국가·OS)   (만족도·등급)
```

- 출처: OpenIntro Statistics 4판 1.2절 "Types of variables"(그림 "Breakdown of variables into their respective types"). 이 노트의 장·절 번호는 OpenIntro GitHub LaTeX 원본(`ch_intro_to_data.tex`)의 `\section`·`\subsection` 순서와 4판 PDF(화면 낭독용판, Internet Archive 사본) 목차로 확인했다(1.2.2는 PDF 17쪽).
  - *수치형(numerical)*: 값을 더하고 빼고 평균 내는 것이 뜻이 있는 변수. OpenIntro의 기준이 바로 "sensible to add, subtract, or take averages"다.
  - *이산형(discrete)*: 값이 띄엄띄엄(0, 1, 2…) 있는 수치형. 세는 값이 대표적이다.
  - *연속형(continuous)*: 구간 안 어떤 값이든 될 수 있는 수치형.
  - *범주형(categorical)*: 값이 범주인 변수. 가능한 값을 *수준(level)*이라 한다.
  - *명목형(nominal)*: 수준 사이에 순서가 없는 범주형.
  - *순서형(ordinal)*: 수준 사이에 자연스러운 순서가 있는 범주형.
    - 흔한 오해: "숫자로 적혀 있으면 수치형이다." OpenIntro는 전화 지역번호(area code)를 예로 든다. 평균·합·차가 뜻이 없으니 수치형이 아니다.
- OpenIntro는 단순화를 위해 책 안에서 순서형을 명목형처럼 다룬다고 밝힌다. 순서를 버리는 쪽이 안전하다는 선택이다.

### 2. 측정 척도 사다리 — 위로 갈수록 허용 연산이 늘어난다

```text
  척도         의미 있는 관계          예                          의미 있는 중심값
  ─────────────────────────────────────────────────────────────────────────────
  비율(ratio)   =  <  차이  비율      지연 ms, 금액, 주문 수        평균·중앙값·최빈값 (+기하평균)
     ▲         (진짜 0이 있다)
  구간(interval) =  <  차이           섭씨 온도, 날짜(달력)        평균·중앙값·최빈값
     ▲         (0이 임의)
  순서(ordinal)  =  <                 만족도, 등급, 순위           중앙값·최빈값
     ▲
  명목(nominal)  =                    국가, OS, 우편번호, 상태코드  최빈값
  ─────────────────────────────────────────────────────────────────────────────
  아래 척도에서 쓸 수 있는 것은 위 척도에서도 쓸 수 있다(그 역은 아니다)
```

- 이 네 단계 분류는 S. S. Stevens, "On the Theory of Scales of Measurement", *Science* 103(2684):677–680, 1946이다. 원문은 열지 못했고, 서지와 척도별 허용 통계량은 Wikipedia "Level of measurement"(2차 출처)로 확인했다.
  - *구간 척도*: 차이는 의미가 있지만 0이 임의로 정해진 척도. 20°C는 10°C의 "두 배 더운" 것이 아니다.
  - *비율 척도*: 0이 "없음"을 뜻해 비율까지 의미가 있는 척도. 200ms는 100ms의 두 배다.
- 같은 Wikipedia 항목은 이 분류에 대한 비판도 함께 싣는다(측정 이론가들의 반론, "통계학자들이 일반적으로 받아들이지 않은 제한"). 그래서 이 노트는 척도를 **금지 규칙**이 아니라 **질문 목록**으로 쓴다: "이 계산 결과가 코딩을 바꿔도 같은 결론을 주나?"
- OpenIntro의 4분류(연속·이산·명목·순서)와 Stevens의 4척도는 축이 다르다. 연속·이산은 "값이 어떻게 놓이나", 척도는 "어떤 관계가 의미 있나"다.

### 3. 순서형 평균의 함정 — 코딩을 바꾸면 결론이 바뀐다

```text
  응답 분포(예시, 각 100명)
           매우불만  불만  보통  만족  매우만족
  상품 A      0       0    60    40     0
  상품 B     20       0    25     0    55

  코딩(순서는 같음)           평균 A   평균 B   평균이 고른 쪽    중앙값 A / B
  1, 2, 3, 4, 5              3.40     3.70      B               보통 / 매우만족
  1, 2, 3, 4, 4.2            3.40     3.26      A               보통 / 매우만족
  1, 2, 3, 4, 9              3.40     5.90      B               보통 / 매우만족
```

- 순서형은 "보통 < 만족 < 매우 만족"만 안다. "매우 만족"이 5점인지 4.2점인지 9점인지는 정해져 있지 않다.
- 순서를 지키는 코딩(단조 변환)을 바꾸면 **평균이 고르는 승자가 바뀐다.** 중앙값은 순서만 쓰므로 어느 코딩에서도 같은 수준을 가리킨다.
  - *단조 변환(monotone transformation)*: 순서를 지키는 값 바꾸기. 1<2<3이면 바꾼 뒤에도 f(1)<f(2)<f(3).
- 그래서 순서형에 평균을 쓰면 "점수 간격이 같다"는 가정을 더한 셈이다. 이 가정이 맞는지는 데이터가 아니라 설문 설계가 말해 준다.

### 실험: 코딩·코드값·온도 (Python 3.12 `statistics`, PostgreSQL 17)

```python
code2 = {"매우 불만": 1, "불만": 2, "보통": 3, "만족": 4, "매우 만족": 4.2}
a, b = expand(A, code), expand(B, code)
print(st.fmean(a), st.fmean(b), st.median_low(a), st.median_low(b))
zips = ["01234", "06236", "13529", "48058", "63309"]; as_int = [int(z) for z in zips]
```

(실험 환경: 호스트 Python 3.12.3과 `python:3.12-slim`(Python 3.12.14) 컨테이너에서 출력이 같았다. 무작위 없음.)

```text
코딩 1..5         평균 A=3.40 B=3.70 -> B 우세 | 중앙값(low) A=보통 B=매우 만족
코딩 1,2,3,4,4.2  평균 A=3.40 B=3.26 -> A 우세 | 중앙값(low) A=보통 B=매우 만족
코딩 1,2,3,4,9    평균 A=3.40 B=5.90 -> B 우세 | 중앙값(low) A=보통 B=매우 만족
우편번호 int 변환: [1234, 6236, 13529, 48058, 63309] 평균: 26473.2
앞자리 0 복원 실패: 1234 != 01234
섭씨 20.0/10.0 = 2.000, 켈빈 1.035
```

- 관찰 1: A의 평균 3.40은 코딩과 무관하게 같다(A는 보통·만족만 있다). B의 평균만 3.26~5.90으로 움직여 승자가 바뀐다.
- 관찰 2: 우편번호 평균 26473.2는 어떤 지역도 아니다. 정수 변환이 앞자리 0을 지웠다.
- 관찰 3: 섭씨로는 "2배", 절대 0이 있는 켈빈으로는 1.035배다. 구간 척도에서 비율은 0을 어디 두느냐에 달렸다.

PostgreSQL 17.11(`postgres:17` 컨테이너, `psql`):

```text
 user_id  | zip_int | zip_text | repaired
 user_001 |    1234 | 01234    | 01234
  avg_zip_meaningless = 3735.0000000000000000
 median_level | mode_level        ← percentile_disc(0.5)·mode() on ENUM
 보통         | 보통
ERROR:  function avg(sat) does not exist
```

- 관찰 4: 순서형을 `ENUM`으로 두면 `percentile_disc`·`mode()`는 되고 `avg()`는 타입 오류로 막힌다. 타입이 "이 계산은 뜻이 없다"를 대신 말해 준다.
- 관찰 5: `lpad(zip_int::text, 5, '0')`로 되살릴 수는 있다. 단, 자릿수가 고정이라는 것을 알 때만이다. 처음부터 문자열로 두는 편이 낫다.

## 쓰이는 자료구조·알고리즘

- 이 편에는 커리큘럼 🔧 칸이 비어 있다(—). 대신 쓰는 도구는 **타입**이다.
  - 명목형 = 문자열·열거형(`ENUM`), 순서형 = 순서가 정의된 열거형(PostgreSQL 17 `ENUM`은 선언 순서로 정렬된다, 8.7.2), 수치형 = 정수·실수·`numeric`.
- 명목형의 요약은 **빈도 세기**다 — 해시맵 카운터. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- 순서형의 중앙값은 정렬 또는 선택으로 구한다 — [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md)에서 자세히.
- 시각 값의 척도(인스턴트 = 구간 척도의 점, 기간 = 비율 척도)는 [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md)의 저장 문제와 이어진다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상(숫자가 틀린 모양) | 원리 | 확인 |
|---|---|---|
| "평균 만족도 3.4 → 3.6" | 순서형 평균은 간격 가정에 의존 | 수준별 분포표·중앙값·"만족 이상" 비율을 같이 본다 |
| 지역별 매출에 `1234` 같은 지역이 있다 | 코드값을 정수로 저장 | `length(zip_text) <> 5`인 행 수 |
| `sum(status_code)`, `avg(category_id)` | 명목형에 산술 | 스키마에서 그 열이 이름표인지 확인 |
| "온도가 두 배" "작년 대비 날짜가 …" | 구간 척도에 비율 | 차이로 말한다(+10°C) |

### 2. 순서형 응답은 분포로 보고한다

```sql
-- PostgreSQL 17: 수준별 비율과 '만족 이상' 비율(top-2-box)
SELECT s, count(*) AS n, round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM survey GROUP BY s ORDER BY s;

SELECT round(100.0 * count(*) FILTER (WHERE s >= '만족') / count(*), 1) AS top2_pct,
       percentile_disc(0.5) WITHIN GROUP (ORDER BY s) AS median_level
FROM survey;
```

- `s >= '만족'`은 `ENUM` 선언 순서로 비교된다. 문자열 비교가 아니다.
- 평균을 꼭 내야 하면(예: 내부 추세 비교) 같은 코딩을 고정하고, 분포표를 함께 싣는다. "평균은 1~5 등간격 코딩 가정"이라고 적는다.

### 3. 코드값은 처음부터 문자열로

```java
// Java 21: 우편번호·전화번호·상품코드는 값 객체 + 문자열
record ZipCode(String value) {
    ZipCode {
        if (!value.matches("\\d{5}")) throw new IllegalArgumentException("zip: " + value);
    }
}
```

- 실행 확인(OpenJDK 21.0.12, `eclipse-temurin:21-jdk`): `new ZipCode("01234")`는 통과, `new ZipCode("1234")`는 `IllegalArgumentException`.
- 숫자 연산이 필요 없는 식별자는 문자열(또는 값 객체)로 둔다. 앞자리 0, 자릿수, 하이픈이 보존된다.
- CSV를 스프레드시트나 자동 타입 추론 도구로 열 때도 같은 일이 생긴다(해석 — 도구마다 동작이 다르므로 열 타입을 명시해 읽는다).

## 장애 시나리오와 대처

### 1. "만족도 평균 3.4점" 보고 → 개선 판단이 뒤집힌다 (⚠ 커리큘럼)

- 현상: 리뉴얼 뒤 평균 만족도가 3.40 → 3.70으로 "올랐다"고 발표했다.
- 보이는 형태: 분포를 보면 "매우 불만"이 0% → 20%로 늘었다. 평균은 "매우 만족" 증가에 끌려 올라갔다(위 실험의 A→B).
- 원인: 순서형에 등간격을 가정한 평균. 양극화가 평균에 묻혔다.
- 대처: 수준별 분포표 + 중앙값 + top-2-box·bottom-2-box를 함께 보고한다. 평균은 보조 지표로, 코딩을 명시한다.

### 2. 우편번호를 정수로 적재 → 지역 집계가 깨진다 (⚠ 커리큘럼)

- 현상: 서울 일부(`0`으로 시작하는 우편번호) 지역 매출이 사라지고, 4자리 "지역"이 생겼다.
- 보이는 형태: 지역별 리포트의 행 수가 줄고, `zip`의 `avg`·`sum`이 대시보드에 숫자로 뜬다.
- 원인: 명목형 코드값을 수치형으로 저장. 앞자리 0 손실.
- 대처: 열을 `text`/`char(5)`로 바꾸고, 자릿수가 고정인 것이 확실할 때만 `lpad`로 복구한다. 적재 단계에 형식 검사(`~ '^\d{5}$'`)를 둔다 — [data-engineering/10-data-quality-and-data-observability](../../data-engineering/10-data-quality-and-data-observability/2-summary.md).

### 3. 상태 코드를 평균 냄 → "평균 상태 23.7"(예시)

- 현상: 주문 상태 `10/20/30/40`을 `avg(status)`로 모니터링했다. 평균이 내려가자 "주문이 덜 진행된다"고 판단했다.
- 보이는 형태: 주문의 실제 진행은 그대로인데, 새 상태 `15`(보류)가 추가돼 일부 주문이 그 코드로 기록되자 평균이 움직였다.
- 원인: 명목형(또는 기껏해야 순서형) 코드에 산술. 코드 번호 체계를 바꾸면 지표가 바뀐다.
- 대처: 상태별 건수·비율로 본다. 순서가 정말 있으면 "상태 X 이상 비율"처럼 순서만 쓰는 지표로 바꾼다.

### 4. 구간 척도에 비율 → "두 배 더 늦게 가입"

- 현상: "가입 연도 평균이 2010 → 2020, 두 배 최근"처럼 달력 값에 비율을 썼다.
- 원인: 달력 날짜는 원점이 임의인 구간 척도다. 차이(10년)만 의미가 있다.
- 대처: 기준 시점부터의 **경과 시간**(비율 척도)으로 바꿔 말한다. "가입 후 경과 일수 중앙값 400일 → 200일".

## 핵심 문장

- 숫자 모양이라고 수치형이 아니다. 더하고 평균 낸 결과에 뜻이 있을 때만 수치형이다(OpenIntro 1.2).
- 명목 → 순서 → 구간 → 비율로 올라갈수록 의미 있는 연산이 늘어난다(Stevens 1946). 척도는 금지 규칙이라기보다 "이 결론이 코딩에 흔들리나"를 묻는 질문이다.
- 순서형의 평균은 순서를 지키는 코딩만 바꿔도 승자가 바뀔 수 있다. 중앙값·분포표는 그렇지 않다.
- 코드값(우편번호·상태 코드)은 문자열·열거형으로 저장해 산술을 타입으로 막는다.
- 구간 척도(섭씨·달력 날짜)에는 차이로 말하고, 비율은 진짜 0이 있는 척도에서만 말한다.

## 관련 주제·근거

- 후속: [02-sampling-and-bias](../02-sampling-and-bias/2-summary.md) · [04-descriptive-statistics](../04-descriptive-statistics/2-summary.md)(척도별 중심·산포) · 범주형 추론([20](../20-categorical-inference/2-summary.md))
- 다른 영역: [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md)(시각 값) · [data-engineering/10-data-quality-and-data-observability](../../data-engineering/10-data-quality-and-data-observability/2-summary.md)(허용값·형식 검사) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)(빈도 세기)
- 근거
  - OpenIntro Statistics 4판 1.2 "Data basics" — 1.2.2 "Types of variables"(지역번호 예, 순서형·명목형 정의, 책에서 순서형을 명목형으로 취급). 확인 경로: https://www.openintro.org/book/os/ 목차 + GitHub `OpenIntroStat/openintro-statistics` `ch_intro_to_data/TeX/ch_intro_to_data.tex` + 4판 PDF(`openintro.org/go/?id=os4_for_screen_reader`의 Internet Archive 사본) 목차·본문
  - Stevens, S. S. (1946) "On the Theory of Scales of Measurement", *Science* 103(2684):677–680, doi:10.1126/science.103.2684.677 — 원문 미열람, 서지·척도별 허용 통계량·비판은 Wikipedia "Level of measurement"(2차)
  - Python 3.12 `statistics` 문서 https://docs.python.org/3.12/library/statistics.html — `median_low`/`median_high`는 "ordinal (supports order operations) but not numeric" 데이터용, `mode`는 "discrete or nominal data"용
  - PostgreSQL 17 문서 "Aggregate Functions"(`percentile_disc`는 정렬 가능한 `anyelement`, `mode()`) https://www.postgresql.org/docs/17/functions-aggregate.html · 8.7 "Enumerated Types" 8.7.2 Ordering(선언 순서로 정렬, 비교 연산자·관련 집계 지원) https://www.postgresql.org/docs/17/datatype-enum.html
- 실험 목록
  - 순서형 코딩 3종의 평균·중앙값, 우편번호 정수 변환, 섭씨/켈빈 비율 — Python 3.12.3(호스트)·3.12.14(`python:3.12-slim`), 출력 동일
  - `ZipCode` 값 객체의 형식 검사 — OpenJDK 21.0.12(`eclipse-temurin:21-jdk`)
  - `ENUM` 위 `percentile_disc`·`mode()`·`avg()` 오류, 우편번호 `int` 저장과 `lpad` 복구 — PostgreSQL 17.11(`postgres:17`, `--network none`, `psql`)
