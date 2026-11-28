# python/python-data-science/09 — scikit-learn 전처리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 여섯 개 동물 레이블을 `LabelEncoder` 로 (예측)

```python
# 질문용 발췌
le = LabelEncoder()
encoded = le.fit_transform(['cat', 'dog', 'cat', 'bird', 'dog', 'bird'])
```

- `encoded` 는 어떤 정수 배열인가?
- `le.classes_` 에는 범주가 어떤 순서로 들어 있나?

### 2. 학습 때 없던 `'yellow'` 를 넣으면 (예측)

```python
# 질문용 발췌
data = np.array([['red'], ['blue'], ['green'], ['red'], ['blue']])
ohe_safe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ohe_safe.fit(data)
result = ohe_safe.transform([['red'], ['yellow']])
```

- `result` 의 두 행은 각각 어떤 벡터인가?

### 3. 삼중 따옴표 문자열 속의 `\n` (예측)

```python
# 질문용 발췌
print("""
print(f"변환 전:\n{data}")
""")
```

- 가운데 코드 줄은 화면에 어떤 모양으로 찍히나?

### 4. `fit` 을 학습 데이터에만 하는 까닭 (왜)

- 테스트 데이터에 `fit_transform` 을 부르면 무엇이 잘못되나?

### 5. 순서 없는 범주에 `OneHotEncoder` 를 권하는 까닭 (왜)

- `LabelEncoder` 의 정수를 그대로 특성으로 쓰면 모델이 무엇을 잘못 배울 수 있나?

### 6. 이상치가 섞인 열의 스케일링 (경계)

- `[1, 2, 3, 100]` 같은 열에서 `StandardScaler` 가 흔들리고 `RobustScaler` 가 덜 흔들리는 것은 각각 어떤 통계를 쓰기 때문인가?

### 7. `ColumnTransformer` 에 적지 않은 열 (경계)

- `remainder='drop'` 일 때와 `'passthrough'` 일 때 목록에 없는 열은 각각 어떻게 되나?

### 8. `Pipeline` 의 `fit` 과 `predict` 가 각 단계에서 하는 일 (연결)

- `pipe.fit` 과 `pipe.predict` 는 스케일러 단계와 모델 단계에서 각각 어떤 메서드를 부르나?

### 9. 교차 검증에 전체 `X` 를 넘겨도 되는 까닭 (연결)

- `cross_val_score(pipe, X, y, cv=5)` 가 스케일러를 품고 있어도 누수가 생기지 않는 것은 어째서인가?

## 실습

### 실습 1. 전처리 절 여덟 개를 보여 주는 안내 스크립트

**만들 것** — scikit-learn 전처리의 각 도구를 절 제목과 함께 예제 코드 문자열로 화면에 보여 주고, 끝에 `Pipeline` 의 장점 네 줄을 찍는 스크립트.

**준비물** — Python 3. 스크립트는 예제 코드를 문자열로 보여 주기만 하지만, 문자열 속 코드를 직접 돌려 보려면 `pip install scikit-learn numpy` 가 필요하다.

**요구 조건**

1. 절마다 `print("=== … ===")` 로 제목을 찍고, 예제 코드는 `print("""…""")` 로 문자열째 찍는다. 절과 절 사이는 `print()` 로 빈 줄을 둔다.
2. 1단계 `StandardScaler` 절 — 2열 4행 배열을 만들고 `fit` 한 뒤 `mean_` · `scale_` 을 찍고, `transform` · `inverse_transform` · `fit_transform` 을 차례로 보인다.
3. 2단계 다양한 스케일러 절 — 스케일러 다섯 개를 한 번에 import 하며 줄마다 특징을 주석으로 달고, 이상치가 낀 배열에 `StandardScaler` · `MinMaxScaler` · `RobustScaler` 를 각각 `fit_transform` 해 `round(3)` 으로 찍는다.
4. 3단계 `LabelEncoder` 절 — 동물 레이블 여섯 개를 인코딩해 원본 · 인코딩 · `classes_` 를 찍고, `inverse_transform([0, 1, 2])` 로 되돌린 뒤 순서 문제를 주석으로 경고한다.
5. 4단계 `OneHotEncoder` 절 — 색 다섯 개를 밀집 배열로 인코딩해 `categories_` 와 결과를 찍고, 역변환한 뒤, `handle_unknown='ignore'` 인 인코더로 학습에 없던 색을 변환해 보인다.
6. 5단계 `OrdinalEncoder` 절 — `low` · `medium` · `high` 순서를 `categories` 로 지정해 인코딩한다.
7. 6단계 `Pipeline` 절 — iris 데이터를 8:2 로 나누고, 스케일러와 로지스틱 회귀를 묶은 파이프라인으로 학습 · 정확도 평가 · 5겹 교차 검증을 보인다.
8. 7단계 `ColumnTransformer` 절 — 수치 열 둘에 `StandardScaler`, 범주 열 둘에 `OneHotEncoder` 를 걸고 나머지 열은 버리는 전처리기를 만들어 파이프라인에 넣고, 열 종류별 추천 도구와 누수 방지 문장을 찍는다.
9. 8단계 — 마지막 절은 문자열 블록 없이 `Pipeline` 의 장점 네 가지를 번호 붙인 `print` 네 줄로 찍는다.

**시작 코드**

```python
# scikit-learn 전처리와 Pipeline
# pip install scikit-learn numpy

print("=== StandardScaler: 표준화 ===")
print("""
# TODO: 2열 4행 배열, fit, mean_/scale_, transform, inverse_transform, fit_transform
""")

print()
print("=== 다양한 스케일러 ===")
print("""
# TODO: 스케일러 다섯 개 import(주석 포함), 이상치 배열, 세 스케일러 비교
""")

print()
print("=== LabelEncoder: 레이블 인코딩 ===")
print("""
# TODO: 레이블 인코딩, classes_, 역변환, 순서 문제 경고
""")

print()
print("=== OneHotEncoder: 원-핫 인코딩 ===")
print("""
# TODO: 밀집 배열 인코딩, categories_, 역변환, handle_unknown='ignore'
""")

print()
print("=== OrdinalEncoder: 순서형 인코딩 ===")
print("""
# TODO: categories 로 순서 지정
""")

print()
print("=== Pipeline: 전처리 + 모델 결합 ===")
print("""
# TODO: iris 분할, Pipeline 구성, fit, score, cross_val_score
""")

print()
print("=== ColumnTransformer: 열별 전처리 ===")
print("""
# TODO: 수치/범주 열별 전처리기, Pipeline 조합, 추천 도구 안내
""")

print()
print("=== Pipeline 장점 정리 ===")
# TODO: 장점 네 줄을 print 로
```

**확인 방법** — `python sklearn-preprocessing.py` 로 돌려 절 제목 여덟 개가 차례로 나오는지, 각 제목 아래 예제 코드가 문자열 그대로 보이는지, 맨 끝에 번호 붙은 장점 네 줄이 있는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
