# engineering-practice/18-engineering-virtues — 정답

## 정답

### 1. 원문 속 과녁

- 게으름: "reduce **overall** energy expenditure" — 지금 나의 수고가 아니라 전체 수고.
- 조급함: "the anger you feel when **the computer** is being lazy" — 화내는 대상이 컴퓨터다.
- 오만: "programs that **other people** won't want to say bad things about", 그리고 "write **(and maintain)**" — 기준이 남의 평가이고, 유지보수까지 간다.

### 2. 문서화가 게으름인 근거

- 게으름 정의의 둘째 문장: "It makes you write labor-saving programs that other people will find useful, and then document what you wrote so you don't have to answer so many questions about it."
- 문서는 지금의 추가 노동이다. 원문은 질문을 "없앤다"가 아니라 "그렇게 많이(so many) 답하지 않아도 된다"고 쓴다. 같은 질문에 답하는 미래 노동을 줄인다. 전체 수고가 실제로 주는지는 작성·유지 비용과 이용량에 달렸다(정리 노트 손익분기 계산의 "같은 질문 → 문서"는 남는 수작업 1분·유지 0.1h/주를 가정하고 4주).
- 정의 끝의 "Also hence, this book."도 같은 농담이다. 책 자체가 게으름의 산물이라는 뜻이다.

### 3. 두 판 비교

- 뜻이 바뀌는 차이는 없었다.
- 실제 차이(git 2.43 `--word-diff=plain`)
  - 게으름: "and document" → "and **then** document".
  - 오만: "the sort of thing Zeus zaps you for" → "the sort of thing **for which** Zeus zaps you".
- 조급함 항목은 두 판이 같았다.

### 4. laziness vs 지연 평가

- 다른 개념이다. 이름만 같다.
- 지연 평가: 값이 실제로 필요할 때까지 계산을 미루는 평가 전략.
- Wall의 게으름: 전체 수고를 줄이려고 **지금** 큰 수고(자동화·문서)를 들이는 태도. 오히려 일을 앞당기는 쪽이다.

### 5. 배포 체크리스트 손익분기

- 수작업 누적: 주당 30분 × 5회 = 150분.
- 자동화 누적: 처음 360분 + 주당(유지 15분 + 남는 수작업 2분 × 5회 = 10분) = 360 + 25w분.
- 360 + 25w ≤ 150w → w ≥ 2.88 → **3주째**. 계산 출력도 "3주"였다.

### 6. 분기 보고서 자동화

- 1년 안에 본전을 못 찾는다(계산 출력: "이득 없음").
  - 수작업은 주당 60분 × 1/13회 ≈ 4.6분. 자동화는 처음 480분 + 주당 약 0.4분(남는 5분 × 1/13회)이다. 본전까지 약 114주가 걸린다.
- 계산에 빠진 것: 실수 방지 효과, 사람이 그 일을 기억해 내는 비용, 업무 인수인계 쉬움, 반대로 환경이 바뀌어 스크립트가 깨지는 위험. 계산은 판단의 재료이지 판단 자체가 아니다. 드문 일은 체크리스트 문서로 충분할 수 있다.

### 7. 공동체의 미덕

- 근면(diligence)·인내(patience)·겸손(humility).
- 원문: 세 미덕은 "virtues of passion", "virtues of an individual"이고 "not, however, virtues of community"다. 공동체의 미덕은 "sound like their opposites"지만 "They're not really opposites, because you can do them all at the same time."
- 같은 글은 "If you think a single community can't embrace opposing values, then you should spend more time with Perl."이라고도 쓴다.
- 근거: Larry Wall, "Diligence, Patience, and Humility", 『Open Sources』(O'Reilly, 1999), oreilly.com 공개본.

### 8. 조급함이 사람에게 겨눠짐

- 잘못 겨눈 것: 조급함이 기계의 대기 시간이 아니라 **사람(리뷰어)과 검증 절차**를 향했다. 원문 정의의 과녁은 "the computer"다.
- 바꿀 것
  - 기다림의 원인을 잰다. PR이 커서 리뷰가 늦나, CI가 느린가.
  - PR을 작게 쪼개 리뷰 대기를 줄이고, CI 시간을 캐시·병렬화로 줄인다.
  - 검증 단계는 빼지 않고 빠르게 만든다.
  - 사람에게는 공동체의 미덕(인내)을 쓴다. 원문대로 둘은 동시에 할 수 있다.

### 9. 세 미덕과 실천

- 게으름 → CI/CD(반복 배포 절차를 기계에 맡김), 문서(같은 질문에 답하는 시간을 줄임), 회고 행동 자동화.
- 조급함 → 빌드 캐시·증분 빌드·병렬 테스트(피드백 루프의 대기를 줄임), 작은 PR(리뷰 대기를 줄임).
- 오만 → 리뷰 전 셀프 리뷰, 배포 뒤 지표·알림 확인("and maintain"), 남이 읽기 좋은 커밋·문서.
