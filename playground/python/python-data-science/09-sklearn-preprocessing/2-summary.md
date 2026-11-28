# python/python-data-science/09 — scikit-learn 전처리 — 정리 (힌트)

> 출처 — study-site 항목 `python/sklearn-preprocessing`(항목 데이터 `data/python/data-science.json`) · 정답 코드 study-practice `python/python-data-science/reference/sklearn-preprocessing.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**전처리 변환기는 「환산표」다.**
키는 cm, 몸무게는 kg, 연봉은 원처럼 단위가 제각각인 숫자를 한 눈금으로 맞추려면 먼저 환산표를 만들고, 그 표로 숫자를 바꾼다.
환산표는 **한 번만, 기준이 되는 자료로** 만든다.
나중에 들어온 자료는 새 표를 만들지 않고 이미 만든 표로 바꾼다.
scikit-learn 의 전처리도 똑같은 구조다.
`fit` 이 환산표를 만들고, `transform` 이 그 표로 바꾸며, `Pipeline` 은 환산과 예측을 한 줄로 잇는 컨베이어다.

| 비유 | 실체 |
|---|---|
| 환산표 만들기 | `fit` (평균 · 표준편차 · 범주 목록을 배운다) |
| 환산표로 바꾸기 | `transform` |
| 만들면서 바로 바꾸기 | `fit_transform` |
| 환산표를 거꾸로 읽기 | `inverse_transform` |
| 기준이 되는 자료 | 학습 데이터(`X_train`) |
| 나중에 들어온 자료 | 테스트 데이터(`X_test`) |
| 표에 없는 단위 | 학습 때 못 본 범주(미지 카테고리) |
| 환산 → 판정 컨베이어 | `Pipeline` |

```text
  학습 데이터 ──fit──▶ [환산표: 평균·표준편차·범주목록]
                              │
  학습 데이터 ──transform──────┤──▶ 바뀐 학습 데이터 ──▶ 모델 학습
  테스트 데이터 ─transform─────┘──▶ 바뀐 테스트 데이터 ─▶ 모델 평가
  (테스트 데이터로는 fit 하지 않는다)
```

## 이 주제가 답하려는 질문

1. 열마다 크기가 수백 배씩 다른 숫자를 어떻게 같은 눈금으로 맞추나?
2. `'cat'` · `'red'` · `'low'` 같은 글자 범주를 모델이 먹는 숫자로 어떻게 바꾸나?
3. 테스트 데이터의 정보가 학습에 새지 않게 하려면 무엇을 지켜야 하나?
4. 수치 열과 범주 열에 서로 다른 처리를 어떻게 한 번에 묶나?

## 동작 방식

### (1) `fit` 과 `transform` — 모든 변환기의 두 단계

**언제 쓰나** — scikit-learn 의 모든 전처리 변환기를 쓸 때다.
학습 데이터로 기준을 배우고, 그 기준으로 어떤 데이터든 바꾼다.

```text
scaler.fit(data)           → 열마다 평균(mean_) · 표준편차(scale_)를 계산해 저장
scaler.transform(data)     → 저장된 값으로 (x - mean) / std 를 계산
scaler.inverse_transform() → x' * std + mean 으로 원래 값을 되돌림
scaler.fit_transform(data) → fit 과 transform 을 한 번에
```

- `fit` 은 데이터를 바꾸지 않고, 변환에 쓸 통계만 객체 안에 저장한다.
- 저장된 값은 밑줄로 끝나는 속성(`mean_` · `scale_` · `classes_` · `categories_`)으로 읽는다.
- `transform` 은 저장된 통계로 계산만 한다 — 다시 배우지 않는다.
- `inverse_transform` 은 같은 통계로 계산을 거꾸로 돌려 원래 값을 되찾는다.
- `fit_transform` 은 학습 데이터에 쓰는 지름길이다.

원본의 데이터 `[[100, 0.1], [200, 0.2], [300, 0.3], [400, 0.4]]` 라면 첫째 열의 평균은 250, 둘째 열의 평균은 0.25 다(손으로 계산한 값).
두 열은 크기가 1,000배 다르지만 표준화하면 둘 다 평균 0 · 표준편차 1 의 같은 눈금에 놓인다.

> **표준화** — 값에서 평균을 빼고 표준편차로 나눠 평균 0, 표준편차 1 로 맞추는 변환.\
> 예: `StandardScaler` 가 하는 일.

### (2) 스케일러 다섯 가지 — 무엇을 기준으로 줄이나

**언제 쓰나** — 수치 열의 크기를 맞출 때다.
데이터에 이상치가 있는지, 희소 행렬인지, 열이 아니라 행을 맞출지에 따라 고른다.

```text
StandardScaler : (x - 평균) / 표준편차           → 평균 0, 표준편차 1
MinMaxScaler   : (x - 최솟값) / (최댓값 - 최솟값) → 0 ~ 1
RobustScaler   : (x - 중앙값) / IQR               → 이상치에 강건
MaxAbsScaler   : x / |x|의 최댓값                 → -1 ~ 1 (희소 행렬에 적합)
Normalizer     : 행마다 x / ‖행‖₂                 → 행 벡터 길이 1
```

- 앞의 넷은 **열(특성) 단위**로 통계를 낸다.
- `Normalizer` 만 **행(샘플) 단위**로, 한 샘플의 벡터 길이(L2)를 1 로 맞춘다.
- 원본의 `[[1, 100], [2, 200], [3, 300], [100, 400]]` 에서 첫째 열의 100 이 이상치다.
- 평균 · 표준편차 · 최솟값 · 최댓값은 이 100 한 개에 크게 끌려간다 — 그래서 `StandardScaler` 와 `MinMaxScaler` 는 이상치에 민감하다.
- 중앙값과 IQR 은 가운데 값들로 정해지므로 끝에 있는 100 한 개에 덜 흔들린다 — 그래서 `RobustScaler` 가 이상치에 강건하다.

> **IQR(사분위 범위)** — 데이터의 75% 지점 값에서 25% 지점 값을 뺀 폭.\
> 예: 가운데 절반의 데이터가 퍼진 너비.

> **이상치** — 다른 값들과 동떨어지게 크거나 작은 값.\
> 예: 1, 2, 3 사이의 100.

### (3) `LabelEncoder` — 범주를 정수 하나로

**언제 쓰나** — 한 열(레이블)의 범주를 정수로 바꿀 때다.

```text
labels  = ['cat', 'dog', 'cat', 'bird', 'dog', 'bird']
fit     → 범주를 정렬해 classes_ = ['bird', 'cat', 'dog'] 로 저장
transform → 각 값을 classes_ 속 자리 번호로: bird=0, cat=1, dog=2
결과    → [1, 2, 1, 0, 2, 0]   (원본 주석이 적은 값)
inverse_transform([0, 1, 2]) → ['bird', 'cat', 'dog']
```

- `classes_` 는 등장 순서가 아니라 정렬된 순서다(원본 주석 기준).
- 번호는 그 정렬된 목록 속 자리다.
- 문제는 번호에 크기가 생긴다는 점이다 — `bird=0 < cat=1 < dog=2`.
- 동물에는 순서가 없는데, 모델은 이 크기 관계를 의미 있는 것으로 배울 수 있다.
- 그래서 순서 없는 범주에는 `OneHotEncoder` 를 권한다.

### (4) `OneHotEncoder` — 범주를 0/1 벡터로

**언제 쓰나** — 순서 없는 범주를 크기 관계 없이 숫자로 바꿀 때다.

```text
data = [['red'], ['blue'], ['green'], ['red'], ['blue']]
fit  → categories_ = [['blue', 'green', 'red']]   (정렬된 목록)
transform → 범주마다 열 하나, 해당 열만 1
   red   → [0. 0. 1.]
   blue  → [1. 0. 0.]
   green → [0. 1. 0.]
```

- 범주 수만큼 열이 생기고, 한 행에는 1 이 하나만 있다.
- 어느 범주도 다른 범주보다 「크지」 않다 — 크기 관계가 사라진다.
- `sparse_output=False` 는 결과를 0 이 대부분인 희소 행렬이 아니라 보통 배열(밀집 배열)로 돌려 달라는 뜻이다.
- `inverse_transform` 은 1 이 있는 열을 보고 범주 이름을 되찾는다.
- `handle_unknown='ignore'` 를 주면 학습 때 못 본 범주(`'yellow'`)는 모든 열이 0 인 행 `[0, 0, 0]` 이 된다.

> **원-핫 인코딩** — 범주 하나를 「그 범주 자리만 1, 나머지는 0」인 벡터로 바꾸는 방식.\
> 예: blue → `[1, 0, 0]`.

### (5) `OrdinalEncoder` — 순서를 내가 정해 정수로

**언제 쓰나** — `low < medium < high` 처럼 범주에 진짜 순서가 있을 때다.

```text
OrdinalEncoder(categories=[['low', 'medium', 'high']])
data = [['low'], ['medium'], ['high'], ['medium']]
→ low=0, medium=1, high=2
→ [0. 1. 2. 1.]   (원본 주석이 적은 값)
```

- `categories` 인자에 넘긴 목록의 순서가 곧 번호다.
- 여기서는 정수의 크기 관계가 실제 순서와 맞으므로 `LabelEncoder` 의 문제가 오히려 쓸모가 된다.
- `categories` 는 열마다 목록 하나씩이라 리스트의 리스트로 넘긴다.

### (6) `Pipeline` — 전처리와 모델을 한 줄로

**언제 쓰나** — 전처리 단계와 모델을 묶어 `fit` · `predict` 한 번으로 돌리고, 누수를 막을 때다.

```text
pipe = Pipeline([('scaler', StandardScaler()), ('model', LogisticRegression())])

pipe.fit(X_train, y_train)
  └ scaler.fit_transform(X_train) → 바뀐 X_train
  └ model.fit(바뀐 X_train, y_train)          (마지막 단계만 fit)

pipe.score(X_test, y_test) / pipe.predict(X_test)
  └ scaler.transform(X_test)                  (다시 fit 하지 않음)
  └ model.predict(바뀐 X_test)
```

- 단계는 `(이름, 객체)` 쌍의 리스트로 적고, 적은 순서대로 흐른다.
- `fit` 때 중간 단계는 `fit_transform`, 마지막 단계는 `fit` 만 한다.
- 예측 · 평가 때 중간 단계는 `transform` 만 한다 — 그래서 테스트 데이터에는 학습 데이터의 평균 · 표준편차가 쓰인다.
- `cross_val_score(pipe, X, y, cv=5)` 처럼 교차 검증에 파이프라인을 통째로 넘기면, 매 분할에서 파이프라인 전체가 그 분할의 학습 부분으로 다시 `fit` 된다.
- 그래서 검증 부분의 통계가 스케일러에 섞이지 않는다.
- 원본이 꼽은 장점은 넷이다 — 코드 간결화, 데이터 누수 방지, 교차 검증 호환, `GridSearchCV` 로 전체 파이프라인을 튜닝.

> **데이터 누수** — 학습 과정에 테스트(평가) 데이터의 정보가 새어 들어가 성능이 실제보다 좋게 나오는 일.\
> 예: 전체 데이터로 스케일러를 `fit` 한 뒤 나누기.

> **교차 검증** — 데이터를 여러 조각으로 나눠 조각마다 한 번씩 평가용으로 돌리며 성능을 재는 방법.\
> 예: `cv=5` 는 다섯 조각.

### (7) `ColumnTransformer` — 열마다 다른 처리

**언제 쓰나** — 수치 열과 범주 열이 섞인 표에 서로 다른 변환기를 걸 때다.

```text
ColumnTransformer(transformers=[
    ('num', StandardScaler(), ['age', 'salary']),
    ('cat', OneHotEncoder(),  ['city', 'department']),
], remainder='drop')

입력 표 ─┬─ age, salary        → StandardScaler ─┐
         ├─ city, department   → OneHotEncoder  ─┼─▶ 옆으로 이어 붙인 결과
         └─ 나머지 열          → remainder 규칙 ─┘
```

- `transformers` 는 `(이름, 변환기, 열 목록)` 셋짝의 리스트다.
- 각 열 묶음은 자기 변환기만 지나고, 결과는 옆으로 이어 붙는다.
- 어디에도 적지 않은 열은 `remainder` 가 정한다 — `'drop'` 은 버리고 `'passthrough'` 는 그대로 넘긴다.
- `ColumnTransformer` 자체도 변환기라서 `Pipeline` 의 한 단계로 넣을 수 있다.
- 원본의 정리: 수치형은 `StandardScaler` · `MinMaxScaler`, 범주형은 `OneHotEncoder` · `OrdinalEncoder`, 결측치는 `SimpleImputer` 를 파이프라인에 넣는다.

## 문법 — 형태와 규칙

```python
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)   # 학습 데이터: 배우고 바꾸기
X_test_s = scaler.transform(X_test)         # 테스트 데이터: 바꾸기만

ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

pipe = Pipeline([('scaler', StandardScaler()),
                 ('model', LogisticRegression(max_iter=200))])
pipe.fit(X_train, y_train)
print(pipe.score(X_test, y_test))
```

- 변환기는 `객체 = 클래스(옵션)` 으로 만들고, 메서드는 `fit` · `transform` · `fit_transform` · `inverse_transform` 넷이다.
- 배운 값은 밑줄 끝 속성(`mean_` · `scale_` · `classes_` · `categories_`)에 있다.
- 입력은 2차원(행 = 샘플, 열 = 특성)이다 — 열 하나짜리 범주도 `[['red'], ['blue']]` 처럼 감싼다.
- `LabelEncoder` 는 1차원 리스트(`['cat', 'dog']`)를 받는다.
- `Pipeline` 은 `[(이름, 객체), …]`, `ColumnTransformer` 는 `[(이름, 변환기, 열), …]` 꼴이다.
- `OrdinalEncoder(categories=[[…]])` 는 열마다 순서 목록 하나씩이다.

## 어디서 틀리나

### 1. 테스트 데이터로 `fit` 한다

`fit` 은 반드시 학습 데이터에만 한다.
테스트 데이터에 `fit_transform` 을 부르면 테스트 데이터의 평균 · 표준편차로 새 환산표를 만들게 된다.
그러면 학습 때와 다른 눈금으로 바뀌고, 평가 데이터의 정보가 전처리에 들어간다.
나누기 전에 전체 데이터로 `fit` 하는 것도 같은 누수다.
`Pipeline` 을 쓰면 이 순서를 자동으로 지킨다.

### 2. 이상치가 많은데 `StandardScaler` 를 쓴다

`StandardScaler` 는 평균 0, 표준편차 1 로 바꾸지만, 평균과 표준편차는 이상치 하나에 크게 끌려간다.
이상치가 많으면 중앙값과 IQR 을 쓰는 `RobustScaler` 가 낫다.

### 3. 순서 없는 범주에 정수를 준다

`LabelEncoder` 의 `bird=0 < cat=1 < dog=2` 는 가짜 크기 관계다.
모델이 이것을 배울 수 있으니 순서 없는 범주에는 `OneHotEncoder` 를 쓴다.
진짜 순서가 있으면 `OrdinalEncoder` 에 `categories` 로 순서를 적는다.

### 4. 학습 때 못 본 범주

`handle_unknown='ignore'` 없이 만든 `OneHotEncoder` 는 미지 카테고리를 안전하게 처리하지 않는다 — 원본은 이를 위해 `ohe_safe` 를 따로 만든다.
`'ignore'` 를 주면 그 행은 모든 열이 0 이 된다.
`ColumnTransformer` 예의 `OneHotEncoder()` 는 이 옵션이 없다는 점을 눈여겨본다.

### 5. 열 단위와 행 단위를 헷갈린다

`Normalizer` 는 이름과 달리 열을 맞추지 않는다.
행(샘플) 하나의 벡터 길이를 1 로 만든다.

### 6. `remainder` 를 잊는다

`ColumnTransformer` 에 적지 않은 열은 `remainder='drop'` 이면 결과에서 사라진다.
남겨야 하는 열이 있으면 `'passthrough'` 를 준다.

### 7. 삼중 따옴표 문자열 속의 `\n`

원본 예제는 각 절의 코드를 `print("""…""")` 로 **문자열째 화면에 보여 준다** — 문자열 안의 코드는 실행되지 않는다.
그래서 주석의 `# [1, 2, 1, 0, 2, 0]` 같은 값은 코드 주석이 주장하는 값이다.
또 그 문자열 안의 `print(f"변환 전:\n{data}")` 에 있는 `\n` 은 문자열 리터럴의 이스케이프로 처리되어 진짜 줄바꿈이 된다.
글자 `\n` 을 그대로 보이려면 `r"""…"""` 나 `\\n` 을 쓴다.

> **이스케이프** — 역슬래시로 시작해 특별한 글자를 나타내는 표기.\
> 예: `\n` 은 줄바꿈 한 글자.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 일반 문자열 리터럴의 `\n` 은 줄바꿈이 된다 | Python 언어 |
| `fit` · `transform` · `fit_transform` · `inverse_transform` 의 나뉨 | scikit-learn 라이브러리의 API 약속 |
| `classes_` · `categories_` 가 정렬된 순서다 | scikit-learn 의 동작(원본 주석 기준) — 언어와 무관 |
| `sparse_output` 이라는 인자 이름 | scikit-learn 의 버전에 따라 다르다 (확인 필요) |
| `Pipeline.fit` 이 중간 단계는 `fit_transform`, 마지막은 `fit` 만 한다 | scikit-learn |
| 이상치에 대한 강건함 | 수학적 성질(중앙값 · IQR) — 라이브러리 구현과 무관 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 수치 열, 이상치 적음 | `StandardScaler` · `MinMaxScaler` | 스케일링 생략 |
| 수치 열, 이상치 많음 | `RobustScaler` | `StandardScaler` |
| 희소 행렬 | `MaxAbsScaler` | 평균을 빼는 스케일러 |
| 샘플 벡터의 길이를 맞춤 | `Normalizer` | 열 단위 스케일러 |
| 순서 없는 범주 특성 | `OneHotEncoder` | `LabelEncoder` |
| 순서 있는 범주 | `OrdinalEncoder(categories=…)` | 순서를 잃는 원-핫만 고집 |
| 전처리 + 모델 + 교차 검증 | `Pipeline` | 전체 데이터로 미리 `fit` |
| 수치 · 범주 섞인 표 | `ColumnTransformer` | 열을 손으로 잘라 붙이기 |

## 핵심 문장

1. **`fit` 은 기준을 배우고 `transform` 은 그 기준으로 바꾼다** — `fit` 은 학습 데이터에만 한다.
2. **스케일러는 기준 통계가 다르다** — 평균 · 최대최소는 이상치에 끌리고, 중앙값 · IQR 은 덜 끌린다.
3. **정수 인코딩은 크기 관계를 만든다** — 순서 없으면 원-핫, 순서 있으면 순서를 적은 `OrdinalEncoder`.
4. **`Pipeline` 은 순서를 강제해 누수를 막는다** — 교차 검증 때도 분할마다 다시 `fit` 한다.
5. **`ColumnTransformer` 는 열 묶음마다 다른 변환기를 걸고 결과를 이어 붙인다.**

## 관련 자료

- `sklearn-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [sklearn-models](../10-sklearn-models/2-summary.md)
- [scipy-stats](../01-scipy-stats/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/data-science.json` 의 `sklearn-preprocessing`

## 용어 풀이

- **전처리** — 모델에 넣기 전에 데이터를 고르고 바꾸는 일.
- **변환기** — `fit` · `transform` 을 가진 scikit-learn 객체.
- **표준화** — 평균 0, 표준편차 1 로 맞추는 변환.
- **정규화(Min-Max)** — 최솟값 0, 최댓값 1 로 맞추는 변환.
- **L2 정규화** — 벡터를 자기 길이로 나눠 길이를 1 로 만드는 변환.
- **이상치** — 다른 값과 동떨어진 값.
- **IQR** — 75% 지점 값 − 25% 지점 값.
- **희소 행렬** — 대부분이 0 이라 0 이 아닌 값만 저장하는 행렬.
- **밀집 배열** — 모든 칸을 저장하는 보통 배열.
- **레이블 인코딩** — 범주를 정수 하나로 바꾸기.
- **원-핫 인코딩** — 범주를 「한 칸만 1」인 벡터로 바꾸기.
- **순서형 인코딩** — 정해 준 순서대로 범주에 정수를 주기.
- **미지 카테고리** — 학습 때 없던 범주 값.
- **데이터 누수** — 평가 데이터의 정보가 학습에 섞이는 일.
- **교차 검증** — 데이터를 조각내 돌아가며 평가하는 방법.
- **파이프라인** — 여러 단계를 순서대로 잇는 객체.
- **이스케이프** — `\n` 처럼 역슬래시로 특별한 글자를 쓰는 표기.

## 더 들어가면

- `LabelEncoder` 는 본래 특성이 아니라 타깃(`y`)을 인코딩하라고 만든 도구로 안내된다 (확인 필요).
- `OneHotEncoder` 의 `handle_unknown` 기본값은 `'error'` 라서 미지 카테고리를 만나면 예외가 난다 (확인 필요).
- 예전 버전에서는 `sparse_output` 대신 `sparse` 라는 인자를 썼다 (확인 필요).
- `StandardScaler` 의 표준편차는 표본 표준편차(n−1)가 아니라 모표준편차(n)로 계산된다 (확인 필요).
- `ColumnTransformer` 에 열 이름(`'age'`)을 쓰려면 입력이 열 이름을 가진 pandas `DataFrame` 이어야 한다 (확인 필요).
- 파이프라인 단계의 인자는 `GridSearchCV` 에서 `'model__C'` 처럼 `단계이름__인자` 꼴로 가리킨다 (확인 필요).
- `OrdinalEncoder` 에 `categories` 를 주지 않으면 범주를 정렬한 순서로 번호를 매긴다 (확인 필요).
