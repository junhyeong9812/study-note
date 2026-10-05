# software-design/53-code-forensics-hotspots — 정답

## 정답

### 1. 크기만 보면 빠지는 것

- 빠지는 것: **얼마나 자주 그 코드를 고치나**.
- 이자 비유: 나쁜 코드의 비용은 고칠 때마다 더 드는 시간(이자)이다. 안 바뀌는 코드는 복잡해도 이자를 거의 안 낸다. 그런 코드를 고치면 원금만 갚고 아끼는 이자가 없다.
- 그래서 "자주 바뀌면서 복잡한 곳"부터 고친다.

### 2. 두 축 그림

```text
 복잡도 ^  LegacyReport(크지만 안 바뀜)     PriceEngine(핫스팟)
        │                                Order
        │                     StringUtil(자주 바뀌지만 단순)
        └──────────────────────────────> 변경 빈도
```

- 핫스팟은 확률적 우선순위다(Tornhill 2판 목차 「Be Aware That Hotspots Reflect Probabilities」). "먼저 볼 곳"을 정할 뿐, 거기에 결함이 있다는 증명이 아니다.

### 3. degree와 신뢰도

- degree = 공동 커밋 ÷ 두 파일 커밋 수의 평균 × 100 (code-maat `logical_coupling.clj`).
- 55 ÷ ((60 + 55) / 2) × 100 = 55 ÷ 57.5 × 100 ≈ 95.7 → 정수로 95. 실험 E 출력·code-maat 출력 모두 95.
- 신뢰도 Order→OrderMapper = 55/60 ≈ 0.92, OrderMapper→Order = 55/55 = 1.00.

### 4. LegacyReport의 순위

(실험 E, 2026-10-02)

```text
   3   0.05    3   2006      7000   src/report/LegacyReport.java
  (참고) 줄 수 1위: src/report/LegacyReport.java — 핫스팟 순위 3위
```

- 3위. 복잡도(들여쓰기 합 7000)는 최대지만 분석 기간 변경이 3회뿐이라 곱한 점수가 낮다. 1위는 643줄이지만 40회 바뀐 PriceEngine이다.
- 순위는 이 실험의 점수 정의(정규화한 두 값의 곱)에 따른 것이다. 정의를 바꾸면 순서가 바뀔 수 있다.

### 5. 기본 거르기와 큰 커밋

- `--min-revs 5`, `--min-shared-revs 5`, `--min-coupling 30`, `--max-changeset-size 30`(code-maat 1.0.4 README).
- 커밋 하나에 파일 k개면 쌍이 k(k−1)/2개다. 40파일 커밋 하나가 780쌍을 만든다. 포매터·이름 일괄 변경 같은 커밋은 진짜 결합이 아니므로 뺀다.

### 6. 두 주 작성자 지표

(code-maat 1.0.4, 실험 E 로그)

```text
src/auth/TokenStore.java,exp,202,213,0.95        ← main-dev(추가 줄 수)
src/auth/TokenStore.java,dev-e,10,12,0.83        ← main-dev-by-revs(커밋 수)
```

- `main-dev`: `exp`(최초 import 작성자). 파일을 만든 커밋이 추가 줄 수 202/213을 차지한다.
- `main-dev-by-revs`: `dev-e`(실제 유지보수자, 12커밋 중 10).
- 원인: 파일 생성·대량 커밋이 줄 수 기준을 지배한다. 두 기준을 함께 보고, 대량 커밋을 뺀다.

### 7. 숨은 결합 진단

- 확인: change coupling 분석. 실험 E처럼 Order↔OrderMapper degree 95%, Order→OrderMapper 신뢰도 0.92. 커밋 메시지에서 "Mapper 누락" 핫픽스를 찾는다.
- 고치기: 같은 지식(필드 목록)이 두 곳에 있으므로 하나로 모은다(매핑 생성·공유 정의·한 파일로 합치기). 당장은 CODEOWNERS·리뷰 체크리스트로 함께 보게 한다.

### 8. 지식 섬

- 미리 알 방법: 파일별 작성자 수·주 작성자 비율. 실험 E에서 TokenStore는 대량 커밋을 빼면 작성자 1명(dev-e 10/10). 중요 모듈 + 작성자 1명 목록을 정기적으로 뽑는다.
- 대량 커밋이 가리는 길: 포매터·import 커밋이 작성자를 늘린다. 대량 커밋을 포함한 code-maat `authors`는 TokenStore 작성자를 3명으로 셌다(`src/auth/TokenStore.java,3,12`). 지식 섬이 "여러 명이 아는 파일"처럼 보인다.

### 9. 점수를 목표로 삼으면

- 점수를 낮추려고 파일을 기계적으로 쪼개거나 커밋을 몰아서 한다. 점수는 내려가도 변경 비용은 그대로이거나 늘어난다(측정 대상이 바뀐다).
- 성과는 변경 비용으로 잰다 — 변경당 수정 파일 수, 리드타임, 그 영역의 버그 커밋 비율.

### 10. 연결

- 52: 핫스팟의 "복잡도" 축을 공급한다(순환·인지 복잡도, 줄 수). 핫스팟은 지표에 "얼마나 자주"를 곱해 지표의 맥락 부족을 메운다.
- 51: 핫스팟으로 고른 곳은 대개 테스트가 부족한 레거시다. 고칠 때 seam·sprout·parallel change를 쓴다.
- [engineering-practice/10](../../engineering-practice/10-technical-debt/2-summary.md): 기술 부채 상환 순서를 이자(변경 빈도) 기준으로 정하는 데이터가 된다.
