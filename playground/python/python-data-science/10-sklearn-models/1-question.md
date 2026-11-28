# python/python-data-science/10 — scikit-learn 모델 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 스크립트를 실행했을 때 첫 섹션 제목 다음 화면 (예측)

```python
# 질문용 발췌
print("=== LinearRegression: 선형 회귀 ===")
print("""
from sklearn.linear_model import LinearRegression, Ridge, Lasso
...
print(f"R² 점수: {model.score(X_test, y_test):.4f}")
...
""")
```

- 제목 바로 다음 몇 줄에는 무엇이 찍히나 — R² 숫자인가, 다른 것인가?

### 2. 한 섹션이 끝나고 다음 섹션 제목이 나올 때까지의 빈 줄 (예측)

```python
# 질문용 발췌
print("""
...
print(f"Lasso R²: {lasso.score(X_test, y_test):.4f}")
""")

print()
print("=== DecisionTree: 결정 트리 ===")
```

- 마지막 코드 줄과 다음 섹션 제목 사이에는 빈 줄이 몇 개 생기나?

### 3. 만든 규칙을 아는 데이터에 선형 회귀를 학습시키면 (예측)

```python
# 질문용 발췌
np.random.seed(42)
X = np.random.rand(100, 3)
y = 3*X[:, 0] + 2*X[:, 1] - X[:, 2] + np.random.normal(0, 0.1, 100)
model = LinearRegression().fit(X, y)
print(model.coef_.round(4))
```

- 이 조각을 실제로 실행한다면 `coef_` 는 대략 어떤 값으로 나올 것 같은가?

### 4. `max_depth` 를 작게 잡으면 과적합이 줄어드는 이유 (왜)

- 결정 트리의 깊이를 제한하는 것이 왜 학습 데이터 외우기를 막나?

### 5. 랜덤 포레스트가 단일 결정 트리보다 대개 나은 이유 (왜)

- 트리를 여러 그루 키워 투표시키는 것이 왜 한 그루보다 실수를 줄이나?

### 6. `n_estimators` 를 계속 늘리는 것의 한계 (경계)

- 트리 수를 10배, 100배로 늘리면 성능과 시간은 각각 어떻게 되나?

### 7. 「모델 비교」 조각과 「하이퍼파라미터 튜닝」 조각을 따로 떼어 실행하면 (경계)

- 각 조각은 무엇이 없어서 혼자서는 돌아가지 않나?

### 8. OOB 점수와 `cross_val_score` (연결)

- 두 방법은 「학습에 쓰지 않은 데이터로 잰다」는 점에서 어떻게 닮았고, 비용은 어떻게 다른가?

### 9. Lasso 의 0 이 된 계수와 트리의 `feature_importances_` (연결)

- 두 값은 「어떤 특성이 필요한가」라는 질문에 각각 어떤 방식으로 답하나?

### 10. 원본의 `GridSearchCV` 가 하는 학습 횟수 (예측)

- `param_grid` 의 세 목록과 `cv=5` 로 보면, 모델 학습은 몇 번 일어나고 `RandomizedSearchCV(n_iter=20, cv=5)` 와 견주면 어떤가?

## 실습

### 실습 1. scikit-learn 모델 치트시트를 찍는 스크립트

**만들 것** — 선형 회귀 · 결정 트리 · 랜덤 포레스트 · 모델 비교 · 하이퍼파라미터 튜닝 코드를 삼중 따옴표 문자열로 담아 섹션별로 화면에 찍고, 끝에 모델 선택 가이드를 찍는 Python 스크립트를 만든다.

**준비물** — 스크립트 자체는 표준 Python 만 있으면 돈다(코드 조각은 문자열로 찍힐 뿐 실행되지 않는다). 조각을 따로 실행해 보려면 `scikit-learn` · `numpy` · `scipy` 가 필요하다.

**요구 조건**

1단계 — 뼈대
1. 섹션 제목 여섯 개를 `=== LinearRegression: 선형 회귀 ===`, `=== DecisionTree: 결정 트리 ===`, `=== RandomForest: 랜덤 포레스트 ===`, `=== 모델 비교 ===`, `=== 하이퍼파라미터 튜닝 ===`, `=== 모델 선택 가이드 ===` 순서로 찍는다.
2. 섹션 사이에는 `print()` 로 빈 줄을 넣는다.
3. 앞의 다섯 섹션은 코드 조각을 줄바꿈으로 시작하고 끝나는 삼중 따옴표 문자열로 `print` 한다.

2단계 — 선형 회귀 조각
4. `np.random.seed(42)` 로 100행 × 3열 난수 `X` 를 만들고 `y = 3·X0 + 2·X1 − X2 + 잡음(0, 0.1)` 을 만든다.
5. `train_test_split(X, y, test_size=0.2)` 로 나누고 `LinearRegression` 을 학습시켜 계수(`coef_.round(4)`) · 절편 · R² · MSE 를 찍는다.
6. `Ridge(alpha=1.0)` 의 R² 와 `Lasso(alpha=0.01)` 의 계수 · R² 를 찍는다.

3단계 — 결정 트리 조각
7. iris 를 `test_size=0.2, random_state=42` 로 나눈다.
8. `DecisionTreeClassifier(max_depth=3, min_samples_split=5, min_samples_leaf=2, random_state=42)` 를 학습시켜 정확도 · 트리 깊이 · 리프 노드 수를 찍는다.
9. `feature_importances_` 를 특성 이름과 짝지어 한 줄씩 찍고, `export_text(..., max_depth=2)` 로 트리를 글자로 찍는다.
10. `DecisionTreeRegressor(max_depth=4)` 를 만들기만 하고 학습 줄은 주석으로 둔다.

4단계 — 랜덤 포레스트 조각
11. `RandomForestClassifier(n_estimators=100, max_depth=5, min_samples_split=5, max_features='sqrt', random_state=42, n_jobs=-1)` 를 학습시켜 정확도와 트리 수를 찍는다.
12. 특성 중요도를 큰 순서로 정렬해 찍는다.
13. `oob_score=True` 인 포레스트를 따로 학습시켜 OOB 점수를 찍는다.

5단계 — 모델 비교 조각
14. 로지스틱 회귀 · KNN(k=5) · SVM(RBF) · 결정 트리(max_depth=3) · 랜덤 포레스트 · 그래디언트 부스팅 · AdaBoost 일곱 모델을 이름 → 모델 사전에 담는다.
15. 모델마다 `cross_val_score(cv=5, scoring='accuracy')` 의 평균 ± 표준편차를 이름을 22칸 오른쪽 정렬해 찍는다.

6단계 — 하이퍼파라미터 튜닝 조각
16. `n_estimators` [50, 100, 200] · `max_depth` [3, 5, 10, None] · `min_samples_split` [2, 5, 10] 그리드로 `GridSearchCV(cv=5, scoring='accuracy', n_jobs=-1)` 를 돌려 최적 파라미터 · 최적 점수 · 최적 모델을 찍는다.
17. `randint` 분포를 쓴 `RandomizedSearchCV(n_iter=20, cv=5, random_state=42)` 를 돌려 최적 파라미터를 찍는다.

7단계 — 가이드
18. 마지막 섹션은 문자열이 아니라 「데이터 상황 → 추천 모델」 다섯 줄을 직접 `print` 한다.

**시작 코드**

```python
# scikit-learn 주요 모델
# pip install scikit-learn numpy

print("=== LinearRegression: 선형 회귀 ===")
print("""
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# 데이터 생성
np.random.seed(42)
# TODO: X (100 × 3) 와 y = 3*X0 + 2*X1 - X2 + 잡음

# TODO: 학습/시험 분할 (test_size=0.2)

# 선형 회귀
# TODO: LinearRegression 학습 → 계수, 절편, R², MSE 출력

# Ridge (L2 규제): 다중공선성, 과적합 방지
# TODO: Ridge(alpha=1.0) 학습 → R² 출력

# Lasso (L1 규제): 특성 선택 (불필요한 계수 → 0)
# TODO: Lasso(alpha=0.01) 학습 → 계수, R² 출력
""")

print()
print("=== DecisionTree: 결정 트리 ===")
print("""
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

iris = load_iris()
# TODO: 분할 (test_size=0.2, random_state=42)

# TODO: DecisionTreeClassifier (max_depth, min_samples_split, min_samples_leaf, random_state)
# TODO: 정확도, 트리 깊이, 리프 노드 수 출력

# 특성 중요도
# TODO: 특성 이름과 중요도를 한 줄씩 출력

# 트리 시각화 (텍스트)
from sklearn.tree import export_text
# TODO: export_text 로 위 2층까지 출력

# 회귀용 결정 트리
# TODO: DecisionTreeRegressor(max_depth=4) 생성 (학습 줄은 주석)
""")

print()
print("=== RandomForest: 랜덤 포레스트 ===")
print("""
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

iris = load_iris()
# TODO: 분할 (test_size=0.2, random_state=42)

# 랜덤 포레스트 분류
# TODO: RandomForestClassifier(트리 개수, 깊이, 분할 최소 샘플, 특성 선택, 난수, 병렬)
# TODO: 정확도, 트리 수 출력

# 특성 중요도 (모든 트리의 평균)
# TODO: 중요도 큰 순으로 정렬해 출력

# OOB (Out-of-Bag) 점수 - 교차 검증 없이 성능 추정
# TODO: oob_score=True 포레스트 학습 → OOB 점수 출력
""")

print()
print("=== 모델 비교 ===")
print("""
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier,
    AdaBoostClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y=True)

models = {
    # TODO: 일곱 모델
}

# TODO: 모델마다 5겹 교차 검증 → "이름(22칸 오른쪽 정렬): 평균 ± 표준편차"
""")

print()
print("=== 하이퍼파라미터 튜닝 ===")
print("""
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier

# Grid Search: 모든 조합 탐색
# TODO: param_grid 와 GridSearchCV → 최적 파라미터, 최적 점수, 최적 모델 출력

# Random Search: 무작위 조합 탐색 (더 효율적)
from scipy.stats import randint
# TODO: param_dist 와 RandomizedSearchCV → 최적 파라미터 출력
""")

print()
print("=== 모델 선택 가이드 ===")
# TODO: 「상황 → 추천 모델」 다섯 줄을 직접 print
```

**확인 방법** — `python sklearn-models.py` 로 실행해 섹션 제목 여섯 개, 문자열로 찍힌 코드 조각 다섯 개, 가이드 다섯 줄이 차례로 나오는지 본다. 조각의 동작까지 보려면 조각 하나를 새 파일로 옮겨(필요한 `import` · 데이터를 보충해) 실행한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
