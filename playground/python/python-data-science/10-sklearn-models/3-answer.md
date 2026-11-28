# python/python-data-science/10 — scikit-learn 모델 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 숫자가 아니라 코드 글자가 찍힌다

**출력**

```text
=== LinearRegression: 선형 회귀 ===

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
```

**왜 그런가**
scikit-learn 코드가 삼중 따옴표 문자열 안에 있으므로 `print` 는 그 글자를 그대로 찍을 뿐이다.
모델은 학습되지 않으므로 R² 같은 숫자는 나오지 않고, `print(f"R² 점수: ...")` 줄도 글자 그대로 나온다.
문자열이 줄바꿈으로 시작하므로 제목 다음에 빈 줄이 하나 있다.
근거: 2-summary 「동작 방식 (7)」.

### 2. 빈 줄 두 개

**출력**

```text
print(f"Lasso R²: {lasso.score(X_test, y_test):.4f}")


=== DecisionTree: 결정 트리 ===
```

**왜 그런가**
문자열이 줄바꿈으로 끝나 마지막 코드 줄 뒤에 빈 줄 하나가 생기고, `print` 가 붙이는 줄바꿈이 그 줄을 닫는다.
이어서 `print()` 가 빈 줄을 하나 더 찍으므로 빈 줄이 둘이 된다.
근거: 2-summary 「동작 방식 (7)」.

### 3. 대략 `[3, 2, -1]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`coef_` 는 `[3, 2, -1]` 에 가까운 값(소수점 아래가 조금씩 어긋난 값)으로 나올 것이다.

**왜 그런가**
`y` 를 정확히 `3·X0 + 2·X1 − 1·X2` 로 만들고 표준편차 0.1 의 작은 잡음만 더했다.
선형 회귀는 이 직선 관계의 기울기를 찾으므로, 잡음 탓에 조금 어긋날 뿐 만든 규칙에 가깝게 되찾는다.
원본 주석도 `# ≈ [3, 2, -1]` 이라 적어 두었다.
정확한 소수점 값은 데이터와 잡음에 달려 있어 보장되지 않는다.
근거: 2-summary 「동작 방식 (2)」, 「구현 세부사항 대 언어 보장」.

### 4. 질문 수를 제한해 잡음까지 쪼개지 못하게 한다

트리는 「특성 ≤ 기준값?」 질문을 쌓을수록 데이터를 잘게 쪼개고, 끝까지 쪼개면 학습 데이터의 우연한 잡음까지 리프 하나하나로 외운다.
`max_depth` 는 질문을 쌓을 층수를 막아 규칙을 단순하게 유지하므로, 학습 데이터에만 맞는 세세한 규칙이 생기지 않는다.
너무 얕게 잡으면 필요한 규칙조차 못 배우므로 적당한 값을 교차 검증으로 고른다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 6」.

### 5. 서로 다른 실수를 하는 트리들의 투표가 실수를 상쇄한다

트리마다 부트스트랩으로 다른 표본을 보고, 분할마다 특성 일부(`max_features='sqrt'`)만 후보로 올리므로 트리들이 서로 다른 실수를 한다.
투표로 합치면 한 트리의 엉뚱한 판단이 다른 트리들에 묻혀 사라진다.
다만 「거의 항상 낫다」는 경향일 뿐 보장은 아니다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 6. 시간은 트리 수만큼 늘고, 성능은 어느 선에서 멈춘다

학습 · 예측 시간은 트리 수에 비례해 늘어난다.
성능은 처음에는 오르지만 투표 결과가 안정된 뒤로는 거의 변하지 않는다 — 트리가 많아져도 각 트리가 똑똑해지는 것은 아니기 때문이다.
그래서 원본 팁의 「늘리면 성능이 올라간다」는 「어느 정도까지」로 읽어야 한다.
근거: 2-summary 「어디서 틀리나 5」 (성능이 멈춘다는 부분은 원본에 근거 없음 — 추론).

### 7. 모델 비교는 `import` 가, 튜닝은 데이터가 빠져 있다

「모델 비교」 조각은 `DecisionTreeClassifier` 를 사전에 넣지만 그 조각 안에서 가져오지 않으므로 `NameError` 가 난다.
「하이퍼파라미터 튜닝」 조각은 `X`, `y` 를 만들지 않고 `grid.fit(X, y)` 를 부르므로, 앞 조각의 변수가 없으면 깨진다.
조각들은 한 흐름으로 읽도록 쓰였을 뿐 각자 독립 실행되도록 쓰이지 않았다.
근거: 2-summary 「어디서 틀리나 2」.

### 8. 둘 다 「보지 않은 데이터로 채점」이지만 OOB 는 추가 학습이 없다

OOB 점수는 각 트리가 부트스트랩에서 뽑지 못한 샘플로 그 트리를 채점하므로, 학습에 쓰지 않은 데이터로 잰다는 점에서 교차 검증의 시험 조각과 같은 역할을 한다.
차이는 비용이다 — `cross_val_score(cv=5)` 는 모델을 5번 새로 학습시키지만, OOB 는 포레스트를 한 번 학습시키는 김에 얻는다.
그래서 원본은 OOB 를 「교차 검증 없이 성능 추정」이라 부른다.
OOB 는 부트스트랩을 쓰는 랜덤 포레스트에만 있고, `cross_val_score` 는 어떤 모델에나 쓸 수 있다.
근거: 2-summary 「동작 방식 (4)」, 「동작 방식 (5)」.

### 9. Lasso 는 빼 버리는 방식으로, 트리는 점수를 매기는 방식으로 답한다

Lasso 는 L1 규제로 쓸모없는 특성의 계수를 정확히 0 으로 만들어, 그 특성을 모델에서 아예 빼 버린다 — 특성 선택이다.
트리 · 포레스트의 `feature_importances_` 는 특성을 빼지 않고, 분할에 얼마나 기여했는지 점수를 매겨 순위를 보여 준다.
Lasso 의 판단은 선형 관계를 전제로 하고, 트리의 중요도는 비선형 관계도 반영하지만 「이 모델이 썼다」일 뿐 원인이라는 뜻은 아니다.
근거: 2-summary 「동작 방식 (2)」, 「동작 방식 (3)」, 「어디서 틀리나 7」.

### 10. 그리드는 180번, 무작위 탐색은 100번

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
그리드 탐색은 3 × 4 × 3 = 36 조합을 모두 시험하고, 조합마다 5겹 교차 검증이므로 36 × 5 = 180번 학습한다.
무작위 탐색은 20 조합 × 5겹 = 100번 학습한다.

**왜 그런가**
그리드 탐색은 적어 둔 값의 모든 조합을 빠짐없이 돌리므로 후보가 늘면 학습 횟수가 곱으로 불어난다.
무작위 탐색은 `n_iter` 로 횟수를 정해 두고 그 안에서 분포(`randint`)로 넓은 범위를 훑는다.
탐색이 끝난 뒤 최적 조합으로 한 번 더 학습하는 단계는 이 셈에 넣지 않았다(원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (6)」.

## 실습 정답

### 실습 1. scikit-learn 모델 치트시트를 찍는 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 섹션 제목 여섯 개 | `print("=== LinearRegression: 선형 회귀 ===")` … `print("=== 모델 선택 가이드 ===")` |
| 2. 섹션 사이 빈 줄 | 각 섹션 앞의 `print()` |
| 3. 조각을 삼중 따옴표 문자열로 출력 | `print("""` … `""")` 다섯 덩어리 |
| 4. 데이터 생성 | `np.random.seed(42)`, `X = np.random.rand(100, 3)`, `y = 3*X[:, 0] + 2*X[:, 1] - X[:, 2] + np.random.normal(0, 0.1, 100)` |
| 5. 분할 · 선형 회귀 출력 | `train_test_split(X, y, test_size=0.2)`, `LinearRegression()`, `model.coef_.round(4)`, `model.intercept_`, `model.score`, `mean_squared_error` |
| 6. Ridge · Lasso | `Ridge(alpha=1.0)`, `Lasso(alpha=0.01)`, `lasso.coef_.round(4)` |
| 7. iris 분할 | `train_test_split(iris.data, iris.target, test_size=0.2, random_state=42)` |
| 8. 분류 트리 · 정확도 · 깊이 · 리프 | `DecisionTreeClassifier(max_depth=3, min_samples_split=5, min_samples_leaf=2, random_state=42)`, `tree.get_depth()`, `tree.get_n_leaves()` |
| 9. 중요도 · 텍스트 트리 | `zip(iris.feature_names, importances)`, `export_text(tree, feature_names=..., max_depth=2)` |
| 10. 회귀 트리 생성만 | `reg_tree = DecisionTreeRegressor(max_depth=4)`, `# reg_tree.fit(...)` |
| 11. 포레스트 · 정확도 · 트리 수 | `RandomForestClassifier(n_estimators=100, …, n_jobs=-1)`, `rf.n_estimators` |
| 12. 중요도 정렬 | `sorted(zip(...), key=lambda x: -x[1])` |
| 13. OOB | `RandomForestClassifier(n_estimators=100, oob_score=True, random_state=42)`, `rf_oob.oob_score_` |
| 14. 일곱 모델 사전 | `models = { 'Logistic Regression': …, 'AdaBoost': … }` |
| 15. 교차 검증 출력 | `cross_val_score(model, X, y, cv=5, scoring='accuracy')`, `f"{name:>22}: {scores.mean():.4f} ± {scores.std():.4f}"` |
| 16. 그리드 탐색 | `param_grid`, `GridSearchCV(..., cv=5, scoring='accuracy', n_jobs=-1)`, `best_params_` · `best_score_` · `best_estimator_` |
| 17. 무작위 탐색 | `randint(50, 300)`, `randint(2, 20)`, `RandomizedSearchCV(..., n_iter=20, cv=5, random_state=42)` |
| 18. 가이드 다섯 줄 | `print("작은 데이터, 선형 관계 → …")` … `print("빠른 프로토타입 → KNN")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/sklearn-models.py`

```python
# [데이터 과학 & 수학] scikit-learn 모델
# 설명: LinearRegression, DecisionTree, RandomForest 개념과 코드
# 팁: RandomForest는 단일 DecisionTree보다 거의 항상 성능이 좋다. n_estimators를 늘리면 성능이 올라가지만 속도가 느려진다. max_depth로 과적합을 제어한다. feature_importances_로 어떤 특성이 중요한지 파악할 수 있다.

# scikit-learn 주요 모델
# pip install scikit-learn numpy

# 섹션 제목: 선형 회귀 + Ridge(L2) + Lasso(L1) 규제 비교
print("=== LinearRegression: 선형 회귀 ===")
# LinearRegression의 coef_/intercept_, Ridge의 다중공선성 완화, Lasso의 특성 선택 효과
print("""
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# 데이터 생성
np.random.seed(42)
X = np.random.rand(100, 3)  # 3개 특성
y = 3*X[:, 0] + 2*X[:, 1] - X[:, 2] + np.random.normal(0, 0.1, 100)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 선형 회귀
model = LinearRegression()
model.fit(X_train, y_train)

print(f"계수 (기울기): {model.coef_.round(4)}")  # ≈ [3, 2, -1]
print(f"절편: {model.intercept_:.4f}")
print(f"R² 점수: {model.score(X_test, y_test):.4f}")

y_pred = model.predict(X_test)
print(f"MSE: {mean_squared_error(y_test, y_pred):.6f}")

# Ridge (L2 규제): 다중공선성, 과적합 방지
ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)
print(f"Ridge R²: {ridge.score(X_test, y_test):.4f}")

# Lasso (L1 규제): 특성 선택 (불필요한 계수 → 0)
lasso = Lasso(alpha=0.01)
lasso.fit(X_train, y_train)
print(f"Lasso 계수: {lasso.coef_.round(4)}")
print(f"Lasso R²: {lasso.score(X_test, y_test):.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 결정 트리 - 해석 가능한 모델
print("=== DecisionTree: 결정 트리 ===")
# max_depth/min_samples_*로 과적합 제어, feature_importances_로 중요 변수 확인
print("""
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

# 분류용 결정 트리
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

tree = DecisionTreeClassifier(
    max_depth=3,           # 최대 깊이 (과적합 방지)
    min_samples_split=5,   # 분할 최소 샘플 수
    min_samples_leaf=2,    # 리프 최소 샘플 수
    random_state=42
)
tree.fit(X_train, y_train)

print(f"정확도: {tree.score(X_test, y_test):.4f}")
print(f"트리 깊이: {tree.get_depth()}")
print(f"리프 노드 수: {tree.get_n_leaves()}")

# 특성 중요도
importances = tree.feature_importances_
for name, imp in zip(iris.feature_names, importances):
    print(f"  {name}: {imp:.4f}")

# 트리 시각화 (텍스트)
from sklearn.tree import export_text
print(export_text(tree, feature_names=iris.feature_names, max_depth=2))

# 회귀용 결정 트리
reg_tree = DecisionTreeRegressor(max_depth=4)
# reg_tree.fit(X_train, y_train)
""")

# 줄바꿈 출력
print()
# 섹션 제목: 여러 결정 트리를 앙상블한 RandomForest
print("=== RandomForest: 랜덤 포레스트 ===")
# n_estimators(트리 수), n_jobs=-1(병렬), oob_score(검증 없이 평가) 활용
print("""
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

# 랜덤 포레스트 분류
rf = RandomForestClassifier(
    n_estimators=100,      # 트리 개수
    max_depth=5,           # 각 트리 최대 깊이
    min_samples_split=5,
    max_features='sqrt',   # 특성 선택: 'sqrt', 'log2', 0.5(비율)
    random_state=42,
    n_jobs=-1              # 병렬 처리 (모든 코어 사용)
)
rf.fit(X_train, y_train)

print(f"정확도: {rf.score(X_test, y_test):.4f}")
print(f"트리 수: {rf.n_estimators}")

# 특성 중요도 (모든 트리의 평균)
importances = rf.feature_importances_
for name, imp in sorted(zip(iris.feature_names, importances),
                         key=lambda x: -x[1]):
    print(f"  {name}: {imp:.4f}")

# OOB (Out-of-Bag) 점수 - 교차 검증 없이 성능 추정
rf_oob = RandomForestClassifier(
    n_estimators=100, oob_score=True, random_state=42
)
rf_oob.fit(X_train, y_train)
print(f"OOB 점수: {rf_oob.oob_score_:.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 다양한 분류기를 cross_val_score로 한 번에 비교
print("=== 모델 비교 ===")
# 같은 데이터에 여러 모델을 적용해 성능 차이 관찰
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
    'Logistic Regression': LogisticRegression(max_iter=200),
    'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
    'SVM (RBF)': SVC(kernel='rbf'),
    'Decision Tree': DecisionTreeClassifier(max_depth=3),
    'Random Forest': RandomForestClassifier(n_estimators=100),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100),
    'AdaBoost': AdaBoostClassifier(n_estimators=100, algorithm='SAMME'),
}

for name, model in models.items():
    scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"{name:>22}: {scores.mean():.4f} ± {scores.std():.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: GridSearchCV/RandomizedSearchCV로 하이퍼파라미터 탐색
print("=== 하이퍼파라미터 튜닝 ===")
# Grid는 모든 조합 탐색, Random은 무작위 n회 - 후자가 더 효율적인 경우 多
print("""
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier

# Grid Search: 모든 조합 탐색
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 10, None],
    'min_samples_split': [2, 5, 10]
}

grid = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)
grid.fit(X, y)
print(f"최적 파라미터: {grid.best_params_}")
print(f"최적 점수: {grid.best_score_:.4f}")
print(f"최적 모델: {grid.best_estimator_}")

# Random Search: 무작위 조합 탐색 (더 효율적)
from scipy.stats import randint
param_dist = {
    'n_estimators': randint(50, 300),
    'max_depth': [3, 5, 10, 15, None],
    'min_samples_split': randint(2, 20)
}
random_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    param_dist, n_iter=20, cv=5, random_state=42
)
random_search.fit(X, y)
print(f"Random Search 최적: {random_search.best_params_}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 데이터 특성과 요구사항에 따른 모델 선택 가이드
print("=== 모델 선택 가이드 ===")
# 작고 선형적인 문제 - 선형 모델
print("작은 데이터, 선형 관계 → LogisticRegression, LinearRegression")
# 비선형 + 해석성 - 결정 트리
print("비선형, 해석력 필요 → DecisionTree")
# 높은 정확도 우선 - 앙상블
print("높은 성능 필요 → RandomForest, GradientBoosting")
# 고차원 - SVM/규제
print("차원이 높음 → SVM, Ridge/Lasso")
# 빠른 베이스라인 - KNN
print("빠른 프로토타입 → KNN")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== LinearRegression: 선형 회귀 ===

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# 데이터 생성
np.random.seed(42)
X = np.random.rand(100, 3)  # 3개 특성
y = 3*X[:, 0] + 2*X[:, 1] - X[:, 2] + np.random.normal(0, 0.1, 100)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 선형 회귀
model = LinearRegression()
model.fit(X_train, y_train)

print(f"계수 (기울기): {model.coef_.round(4)}")  # ≈ [3, 2, -1]
print(f"절편: {model.intercept_:.4f}")
print(f"R² 점수: {model.score(X_test, y_test):.4f}")

y_pred = model.predict(X_test)
print(f"MSE: {mean_squared_error(y_test, y_pred):.6f}")

# Ridge (L2 규제): 다중공선성, 과적합 방지
ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)
print(f"Ridge R²: {ridge.score(X_test, y_test):.4f}")

# Lasso (L1 규제): 특성 선택 (불필요한 계수 → 0)
lasso = Lasso(alpha=0.01)
lasso.fit(X_train, y_train)
print(f"Lasso 계수: {lasso.coef_.round(4)}")
print(f"Lasso R²: {lasso.score(X_test, y_test):.4f}")


=== DecisionTree: 결정 트리 ===

from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

# 분류용 결정 트리
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

tree = DecisionTreeClassifier(
    max_depth=3,           # 최대 깊이 (과적합 방지)
    min_samples_split=5,   # 분할 최소 샘플 수
    min_samples_leaf=2,    # 리프 최소 샘플 수
    random_state=42
)
tree.fit(X_train, y_train)

print(f"정확도: {tree.score(X_test, y_test):.4f}")
print(f"트리 깊이: {tree.get_depth()}")
print(f"리프 노드 수: {tree.get_n_leaves()}")

# 특성 중요도
importances = tree.feature_importances_
for name, imp in zip(iris.feature_names, importances):
    print(f"  {name}: {imp:.4f}")

# 트리 시각화 (텍스트)
from sklearn.tree import export_text
print(export_text(tree, feature_names=iris.feature_names, max_depth=2))

# 회귀용 결정 트리
reg_tree = DecisionTreeRegressor(max_depth=4)
# reg_tree.fit(X_train, y_train)


=== RandomForest: 랜덤 포레스트 ===

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import numpy as np

iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42
)

# 랜덤 포레스트 분류
rf = RandomForestClassifier(
    n_estimators=100,      # 트리 개수
    max_depth=5,           # 각 트리 최대 깊이
    min_samples_split=5,
    max_features='sqrt',   # 특성 선택: 'sqrt', 'log2', 0.5(비율)
    random_state=42,
    n_jobs=-1              # 병렬 처리 (모든 코어 사용)
)
rf.fit(X_train, y_train)

print(f"정확도: {rf.score(X_test, y_test):.4f}")
print(f"트리 수: {rf.n_estimators}")

# 특성 중요도 (모든 트리의 평균)
importances = rf.feature_importances_
for name, imp in sorted(zip(iris.feature_names, importances),
                         key=lambda x: -x[1]):
    print(f"  {name}: {imp:.4f}")

# OOB (Out-of-Bag) 점수 - 교차 검증 없이 성능 추정
rf_oob = RandomForestClassifier(
    n_estimators=100, oob_score=True, random_state=42
)
rf_oob.fit(X_train, y_train)
print(f"OOB 점수: {rf_oob.oob_score_:.4f}")


=== 모델 비교 ===

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
    'Logistic Regression': LogisticRegression(max_iter=200),
    'KNN (k=5)': KNeighborsClassifier(n_neighbors=5),
    'SVM (RBF)': SVC(kernel='rbf'),
    'Decision Tree': DecisionTreeClassifier(max_depth=3),
    'Random Forest': RandomForestClassifier(n_estimators=100),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=100),
    'AdaBoost': AdaBoostClassifier(n_estimators=100, algorithm='SAMME'),
}

for name, model in models.items():
    scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"{name:>22}: {scores.mean():.4f} ± {scores.std():.4f}")


=== 하이퍼파라미터 튜닝 ===

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier

# Grid Search: 모든 조합 탐색
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 10, None],
    'min_samples_split': [2, 5, 10]
}

grid = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)
grid.fit(X, y)
print(f"최적 파라미터: {grid.best_params_}")
print(f"최적 점수: {grid.best_score_:.4f}")
print(f"최적 모델: {grid.best_estimator_}")

# Random Search: 무작위 조합 탐색 (더 효율적)
from scipy.stats import randint
param_dist = {
    'n_estimators': randint(50, 300),
    'max_depth': [3, 5, 10, 15, None],
    'min_samples_split': randint(2, 20)
}
random_search = RandomizedSearchCV(
    RandomForestClassifier(random_state=42),
    param_dist, n_iter=20, cv=5, random_state=42
)
random_search.fit(X, y)
print(f"Random Search 최적: {random_search.best_params_}")


=== 모델 선택 가이드 ===
작은 데이터, 선형 관계 → LogisticRegression, LinearRegression
비선형, 해석력 필요 → DecisionTree
높은 성능 필요 → RandomForest, GradientBoosting
차원이 높음 → SVM, Ridge/Lasso
빠른 프로토타입 → KNN
````

**풀이 요점**
- 코드 조각은 문자열이라 실행되지 않는다 — 출력에는 숫자 대신 코드 글자가 나온다.
- 문자열 앞뒤의 줄바꿈과 `print()` 가 겹쳐 섹션 사이에 빈 줄 둘이 생긴다.
- 모든 모델이 `fit` · `score` 틀을 공유하므로 모델 비교는 사전 하나와 `for` 하나로 끝난다.
- 트리의 과적합 손잡이는 `max_depth` · `min_samples_split` · `min_samples_leaf` 이고, 포레스트는 여기에 `n_estimators` · `max_features` 가 더해진다.
- 「모델 비교」 조각의 `DecisionTreeClassifier` 와 「튜닝」 조각의 `X`, `y` 는 앞 조각에 기대므로, 조각을 따로 돌릴 때는 보충해야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
