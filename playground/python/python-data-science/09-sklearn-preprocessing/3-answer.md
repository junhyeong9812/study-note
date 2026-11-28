# python/python-data-science/09 — scikit-learn 전처리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `[1, 2, 1, 0, 2, 0]` — 범주는 정렬된 순서 `['bird', 'cat', 'dog']`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`encoded` 는 `[1, 2, 1, 0, 2, 0]`, `le.classes_` 는 `['bird', 'cat', 'dog']` 다.
원본 주석이 적은 값과 같다.

**왜 그런가**
`fit` 이 범주를 등장 순서가 아니라 정렬된 순서로 `classes_` 에 저장한다.
각 값은 그 목록 속 자리 번호가 된다 — bird=0, cat=1, dog=2.
근거: 2-summary 「동작 방식 (3)」.

### 2. `red` 는 `[0, 0, 1]`, `yellow` 는 `[0, 0, 0]`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 행은 `[0. 0. 1.]`, 둘째 행은 `[0. 0. 0.]` 이다.

**왜 그런가**
`categories_` 는 정렬된 `['blue', 'green', 'red']` 라서 `red` 는 셋째 열만 1 이다.
`yellow` 는 학습 때 없던 범주이고, `handle_unknown='ignore'` 라서 오류 대신 모든 열이 0 인 행이 된다.
근거: 2-summary 「동작 방식 (4)」.

### 3. 두 줄로 쪼개져 찍힌다

**출력**

```text
print(f"변환 전:
{data}")
```

**왜 그런가**
바깥의 `"""…"""` 는 raw 문자열이 아니라서 안쪽의 `\n` 이 이스케이프로 처리되어 진짜 줄바꿈 한 글자가 된다.
그래서 `print(f"변환 전:` 뒤에서 줄이 바뀌고 `{data}")` 가 다음 줄에 나온다.
글자 그대로 보이려면 `r"""…"""` 나 `\\n` 을 쓴다.
근거: 2-summary 「어디서 틀리나 7」.

### 4. 테스트 데이터의 통계로 새 기준을 만들게 된다

`fit` 은 평균 · 표준편차 같은 기준을 배우는 단계다.
테스트 데이터로 `fit` 하면 학습 때와 다른 눈금으로 바뀌어 모델이 배운 것과 입력이 어긋난다.
또 평가 데이터의 정보가 전처리에 들어가 성능이 실제보다 좋게 나오는 데이터 누수가 된다.
테스트 데이터에는 학습 데이터로 `fit` 한 객체의 `transform` 만 부른다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 5. 없는 크기 관계를 배울 수 있다

`LabelEncoder` 는 `bird=0 < cat=1 < dog=2` 처럼 정수를 준다.
동물에는 순서가 없는데 모델은 「dog 가 bird 보다 크다」, 「cat 은 둘의 가운데다」 같은 관계를 의미로 받아들일 수 있다.
`OneHotEncoder` 는 범주마다 따로 열을 두어 어느 범주도 다른 범주보다 크지 않게 만든다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 6. 평균 · 표준편차 대 중앙값 · IQR

`StandardScaler` 는 평균과 표준편차를 쓰는데, 둘 다 100 하나에 크게 끌려가 나머지 값들이 좁은 구간에 뭉친다.
`RobustScaler` 는 중앙값과 IQR 을 쓰는데, 둘 다 가운데 값들로 정해지므로 끝의 100 한 개에 덜 흔들린다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 7. `'drop'` 은 버리고 `'passthrough'` 는 그대로 넘긴다

`transformers` 에 적지 않은 열은 `remainder` 가 처리한다.
`'drop'` 이면 결과에서 사라지고, `'passthrough'` 면 변환 없이 결과에 붙는다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 6」.

### 8. `fit` 은 중간 `fit_transform` → 마지막 `fit`, `predict` 는 중간 `transform` → 마지막 `predict`

`pipe.fit` 은 스케일러에서 `fit_transform` 을 불러 기준을 배우고 바꾼 뒤, 그 결과로 모델의 `fit` 을 부른다.
`pipe.predict`(와 `score`)는 스케일러에서 `transform` 만 불러 학습 때의 기준으로 바꾼 뒤 모델의 `predict` 를 부른다.
그래서 테스트 데이터에 학습 데이터의 평균 · 표준편차가 자동으로 쓰인다.
근거: 2-summary 「동작 방식 (6)」.

### 9. 분할마다 파이프라인 전체를 다시 `fit` 하기 때문이다

교차 검증은 분할마다 학습 부분과 검증 부분을 나눈다.
파이프라인을 통째로 넘기면 매 분할에서 스케일러까지 그 분할의 학습 부분으로만 다시 `fit` 된다.
검증 부분은 `transform` 만 거치므로 그 통계가 스케일러에 섞이지 않는다.
반대로 전체 `X` 로 스케일러를 먼저 `fit` 하고 넘겼다면 누수가 생긴다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 1」.

## 실습 정답

### 실습 1. 전처리 절 여덟 개를 보여 주는 안내 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 절 제목 · 문자열 블록 · 빈 줄 | `print("=== … ===")` · `print("""…""")` · `print()` |
| 2. `StandardScaler` 절 | `scaler.fit(data)` · `scaler.mean_` · `scaler.scale_` · `scaler.transform` · `scaler.inverse_transform` · `scaler.fit_transform` |
| 3. 다양한 스케일러 절 | `from sklearn.preprocessing import (StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler, Normalizer)` · `.fit_transform(data).round(3)` 세 번 |
| 4. `LabelEncoder` 절 | `le.fit_transform(labels)` · `le.classes_` · `le.inverse_transform([0, 1, 2])` · `# 주의:` 주석 |
| 5. `OneHotEncoder` 절 | `OneHotEncoder(sparse_output=False)` · `ohe.categories_` · `ohe.inverse_transform` · `OneHotEncoder(sparse_output=False, handle_unknown='ignore')` · `[['red'], ['yellow']]` |
| 6. `OrdinalEncoder` 절 | `OrdinalEncoder(categories=[['low', 'medium', 'high']])` |
| 7. `Pipeline` 절 | `load_iris(return_X_y=True)` · `train_test_split(…, test_size=0.2, random_state=42)` · `Pipeline([('scaler', …), ('model', LogisticRegression(max_iter=200))])` · `pipe.fit` · `pipe.score` · `cross_val_score(pipe, X, y, cv=5)` |
| 8. `ColumnTransformer` 절 | `ColumnTransformer(transformers=[('num', …), ('cat', …)], remainder='drop')` · `full_pipe = Pipeline([('preprocessor', …), ('model', …)])` · 안내 `print` 네 줄 |
| 9. 장점 네 줄 | `print("1. 코드 간결화 …")` ~ `print("4. 하이퍼파라미터 튜닝 …")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/sklearn-preprocessing.py`

```python
# [데이터 과학 & 수학] scikit-learn 전처리
# 설명: StandardScaler, LabelEncoder, OneHotEncoder, Pipeline 구조
# 팁: StandardScaler는 평균 0, 표준편차 1로 변환한다. 이상치가 많으면 RobustScaler가 낫다. Pipeline을 사용하면 학습 데이터의 통계(mean, std)가 테스트 데이터에 적용되어 데이터 누수를 방지한다. 반드시 fit은 학습 데이터에만 해야 한다.

# scikit-learn 전처리와 Pipeline
# pip install scikit-learn numpy

# 섹션 제목: 표준화 변환기 StandardScaler
print("=== StandardScaler: 표준화 ===")
# fit으로 평균/표준편차 학습 → transform으로 변환, fit_transform이 합친 형태
print("""
from sklearn.preprocessing import StandardScaler
import numpy as np

# 표준화: (x - mean) / std → 평균=0, 표준편차=1
data = np.array([[100, 0.1], [200, 0.2], [300, 0.3], [400, 0.4]])

scaler = StandardScaler()
scaler.fit(data)  # 평균과 표준편차 학습
print(f"평균: {scaler.mean_}")
print(f"표준편차: {scaler.scale_}")

data_scaled = scaler.transform(data)
print(f"변환 전:\n{data}")
print(f"변환 후:\n{data_scaled.round(4)}")

# 역변환
data_original = scaler.inverse_transform(data_scaled)
print(f"역변환:\n{data_original}")

# fit_transform: fit + transform 한번에
data_scaled2 = scaler.fit_transform(data)
""")

# 줄바꿈 출력
print()
# 섹션 제목: 데이터 특성에 따라 선택할 다양한 스케일러
print("=== 다양한 스케일러 ===")
# 이상치가 많으면 RobustScaler, 희소 행렬엔 MaxAbsScaler가 적합
print("""
from sklearn.preprocessing import (
    StandardScaler,    # 표준화 (평균=0, 표준편차=1)
    MinMaxScaler,      # 정규화 (0~1 범위)
    RobustScaler,      # 이상치에 강건 (중앙값, IQR 사용)
    MaxAbsScaler,      # -1~1 범위 (희소 행렬에 적합)
    Normalizer         # 행 단위 L2 정규화 (벡터 크기=1)
)
import numpy as np

data = np.array([[1, 100], [2, 200], [3, 300], [100, 400]])

print("StandardScaler: 이상치에 민감")
print(StandardScaler().fit_transform(data).round(3))

print("MinMaxScaler: [0, 1] 범위")
print(MinMaxScaler().fit_transform(data).round(3))

print("RobustScaler: 이상치에 강건")
print(RobustScaler().fit_transform(data).round(3))
""")

# 줄바꿈 출력
print()
# 섹션 제목: 단일 컬럼 레이블을 정수로 변환
print("=== LabelEncoder: 레이블 인코딩 ===")
# 순서가 없는 범주에 순서를 부여하므로 일반적으로 OneHot 권장
print("""
from sklearn.preprocessing import LabelEncoder

# 범주형 → 정수
le = LabelEncoder()
labels = ['cat', 'dog', 'cat', 'bird', 'dog', 'bird']

encoded = le.fit_transform(labels)
print(f"원본: {labels}")
print(f"인코딩: {encoded}")            # [1, 2, 1, 0, 2, 0]
print(f"클래스: {le.classes_}")         # ['bird', 'cat', 'dog']

# 역변환
decoded = le.inverse_transform([0, 1, 2])
print(f"디코딩: {decoded}")            # ['bird', 'cat', 'dog']

# 주의: 순서가 없는 범주에 정수를 부여하면
# 모델이 크기 관계를 학습할 수 있음 (bird=0 < cat=1 < dog=2)
# → OneHotEncoder 사용 권장
""")

# 줄바꿈 출력
print()
# 섹션 제목: 범주를 이진 벡터로 변환
print("=== OneHotEncoder: 원-핫 인코딩 ===")
# handle_unknown='ignore'로 학습 시 보지 못한 카테고리 안전 처리
print("""
from sklearn.preprocessing import OneHotEncoder
import numpy as np

# 범주형 → 이진 벡터
data = np.array([['red'], ['blue'], ['green'], ['red'], ['blue']])

ohe = OneHotEncoder(sparse_output=False)  # 밀집 배열
encoded = ohe.fit_transform(data)

print(f"원본: {data.flatten()}")
print(f"카테고리: {ohe.categories_}")
print(f"원-핫:\n{encoded}")
# [[0. 0. 1.]   # red
#  [1. 0. 0.]   # blue
#  [0. 1. 0.]   # green
#  [0. 0. 1.]   # red
#  [1. 0. 0.]]  # blue

# 역변환
original = ohe.inverse_transform(encoded)
print(f"역변환: {original.flatten()}")

# 미지 카테고리 처리
ohe_safe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ohe_safe.fit(data)
result = ohe_safe.transform([['red'], ['yellow']])  # yellow는 학습에 없음
print(f"미지 카테고리: {result}")
# yellow는 [0, 0, 0]으로 처리
""")

# 줄바꿈 출력
print()
# 섹션 제목: 순서가 명확한 범주 데이터에 적합한 OrdinalEncoder
print("=== OrdinalEncoder: 순서형 인코딩 ===")
# categories 인자로 순서를 명시 (low < medium < high)
print("""
from sklearn.preprocessing import OrdinalEncoder
import numpy as np

# 순서가 있는 범주형 데이터
data = np.array([['low'], ['medium'], ['high'], ['medium']])

# 순서 지정
oe = OrdinalEncoder(categories=[['low', 'medium', 'high']])
encoded = oe.fit_transform(data)
print(f"순서 인코딩: {encoded.flatten()}")  # [0. 1. 2. 1.]
""")

# 줄바꿈 출력
print()
# 섹션 제목: 전처리와 모델을 묶는 Pipeline (데이터 누수 방지)
print("=== Pipeline: 전처리 + 모델 결합 ===")
# Pipeline.fit()은 step 순서대로 fit_transform → 마지막 step만 fit
print("""
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.datasets import load_iris

# 데이터
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Pipeline 구성
pipe = Pipeline([
    ('scaler', StandardScaler()),         # Step 1: 표준화
    ('model', LogisticRegression(max_iter=200))  # Step 2: 모델
])

# fit → transform(scaler) → fit(model) 자동 실행
pipe.fit(X_train, y_train)

# predict → transform(scaler) → predict(model) 자동 실행
score = pipe.score(X_test, y_test)
print(f"Pipeline 정확도: {score:.4f}")

# 교차 검증도 Pipeline과 함께
scores = cross_val_score(pipe, X, y, cv=5)
print(f"CV 평균: {scores.mean():.4f} ± {scores.std():.4f}")
""")

# 줄바꿈 출력
print()
# 섹션 제목: 컬럼별로 다른 전처리 적용 (수치/범주 등)
print("=== ColumnTransformer: 열별 전처리 ===")
# transformers=[(이름, 변환기, 컬럼)] 형태로 컬럼 그룹별 전처리 정의
print("""
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# 수치형과 범주형 열에 다른 전처리 적용
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), ['age', 'salary']),      # 수치형 → 표준화
        ('cat', OneHotEncoder(), ['city', 'department'])   # 범주형 → 원-핫
    ],
    remainder='drop'  # 나머지 열 처리: 'drop' 또는 'passthrough'
)

# Pipeline으로 조합
full_pipe = Pipeline([
    ('preprocessor', preprocessor),
    ('model', LogisticRegression())
])

print("수치형: StandardScaler, MinMaxScaler")
print("범주형: OneHotEncoder, OrdinalEncoder")
print("결측치: SimpleImputer (Pipeline에 포함)")
print("Pipeline은 데이터 누수(data leakage)를 방지한다")
""")

# 줄바꿈 출력
print()
# 섹션 제목: Pipeline을 쓰는 이유 4가지
print("=== Pipeline 장점 정리 ===")
# 단일 fit/predict로 전체 흐름 실행
print("1. 코드 간결화: fit/predict 한 번으로 전체 파이프라인 실행")
# 학습/테스트 통계가 분리되어 누수 방지
print("2. 데이터 누수 방지: 테스트 데이터에 학습 데이터 정보 유출 차단")
# CV와 자연스럽게 호환
print("3. 교차 검증 호환: cross_val_score와 자연스럽게 통합")
# 전처리 파라미터까지 튜닝 대상으로 포함 가능
print("4. 하이퍼파라미터 튜닝: GridSearchCV로 전체 파이프라인 최적화")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== StandardScaler: 표준화 ===

from sklearn.preprocessing import StandardScaler
import numpy as np

# 표준화: (x - mean) / std → 평균=0, 표준편차=1
data = np.array([[100, 0.1], [200, 0.2], [300, 0.3], [400, 0.4]])

scaler = StandardScaler()
scaler.fit(data)  # 평균과 표준편차 학습
print(f"평균: {scaler.mean_}")
print(f"표준편차: {scaler.scale_}")

data_scaled = scaler.transform(data)
print(f"변환 전:
{data}")
print(f"변환 후:
{data_scaled.round(4)}")

# 역변환
data_original = scaler.inverse_transform(data_scaled)
print(f"역변환:
{data_original}")

# fit_transform: fit + transform 한번에
data_scaled2 = scaler.fit_transform(data)


=== 다양한 스케일러 ===

from sklearn.preprocessing import (
    StandardScaler,    # 표준화 (평균=0, 표준편차=1)
    MinMaxScaler,      # 정규화 (0~1 범위)
    RobustScaler,      # 이상치에 강건 (중앙값, IQR 사용)
    MaxAbsScaler,      # -1~1 범위 (희소 행렬에 적합)
    Normalizer         # 행 단위 L2 정규화 (벡터 크기=1)
)
import numpy as np

data = np.array([[1, 100], [2, 200], [3, 300], [100, 400]])

print("StandardScaler: 이상치에 민감")
print(StandardScaler().fit_transform(data).round(3))

print("MinMaxScaler: [0, 1] 범위")
print(MinMaxScaler().fit_transform(data).round(3))

print("RobustScaler: 이상치에 강건")
print(RobustScaler().fit_transform(data).round(3))


=== LabelEncoder: 레이블 인코딩 ===

from sklearn.preprocessing import LabelEncoder

# 범주형 → 정수
le = LabelEncoder()
labels = ['cat', 'dog', 'cat', 'bird', 'dog', 'bird']

encoded = le.fit_transform(labels)
print(f"원본: {labels}")
print(f"인코딩: {encoded}")            # [1, 2, 1, 0, 2, 0]
print(f"클래스: {le.classes_}")         # ['bird', 'cat', 'dog']

# 역변환
decoded = le.inverse_transform([0, 1, 2])
print(f"디코딩: {decoded}")            # ['bird', 'cat', 'dog']

# 주의: 순서가 없는 범주에 정수를 부여하면
# 모델이 크기 관계를 학습할 수 있음 (bird=0 < cat=1 < dog=2)
# → OneHotEncoder 사용 권장


=== OneHotEncoder: 원-핫 인코딩 ===

from sklearn.preprocessing import OneHotEncoder
import numpy as np

# 범주형 → 이진 벡터
data = np.array([['red'], ['blue'], ['green'], ['red'], ['blue']])

ohe = OneHotEncoder(sparse_output=False)  # 밀집 배열
encoded = ohe.fit_transform(data)

print(f"원본: {data.flatten()}")
print(f"카테고리: {ohe.categories_}")
print(f"원-핫:
{encoded}")
# [[0. 0. 1.]   # red
#  [1. 0. 0.]   # blue
#  [0. 1. 0.]   # green
#  [0. 0. 1.]   # red
#  [1. 0. 0.]]  # blue

# 역변환
original = ohe.inverse_transform(encoded)
print(f"역변환: {original.flatten()}")

# 미지 카테고리 처리
ohe_safe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
ohe_safe.fit(data)
result = ohe_safe.transform([['red'], ['yellow']])  # yellow는 학습에 없음
print(f"미지 카테고리: {result}")
# yellow는 [0, 0, 0]으로 처리


=== OrdinalEncoder: 순서형 인코딩 ===

from sklearn.preprocessing import OrdinalEncoder
import numpy as np

# 순서가 있는 범주형 데이터
data = np.array([['low'], ['medium'], ['high'], ['medium']])

# 순서 지정
oe = OrdinalEncoder(categories=[['low', 'medium', 'high']])
encoded = oe.fit_transform(data)
print(f"순서 인코딩: {encoded.flatten()}")  # [0. 1. 2. 1.]


=== Pipeline: 전처리 + 모델 결합 ===

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.datasets import load_iris

# 데이터
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Pipeline 구성
pipe = Pipeline([
    ('scaler', StandardScaler()),         # Step 1: 표준화
    ('model', LogisticRegression(max_iter=200))  # Step 2: 모델
])

# fit → transform(scaler) → fit(model) 자동 실행
pipe.fit(X_train, y_train)

# predict → transform(scaler) → predict(model) 자동 실행
score = pipe.score(X_test, y_test)
print(f"Pipeline 정확도: {score:.4f}")

# 교차 검증도 Pipeline과 함께
scores = cross_val_score(pipe, X, y, cv=5)
print(f"CV 평균: {scores.mean():.4f} ± {scores.std():.4f}")


=== ColumnTransformer: 열별 전처리 ===

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

# 수치형과 범주형 열에 다른 전처리 적용
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), ['age', 'salary']),      # 수치형 → 표준화
        ('cat', OneHotEncoder(), ['city', 'department'])   # 범주형 → 원-핫
    ],
    remainder='drop'  # 나머지 열 처리: 'drop' 또는 'passthrough'
)

# Pipeline으로 조합
full_pipe = Pipeline([
    ('preprocessor', preprocessor),
    ('model', LogisticRegression())
])

print("수치형: StandardScaler, MinMaxScaler")
print("범주형: OneHotEncoder, OrdinalEncoder")
print("결측치: SimpleImputer (Pipeline에 포함)")
print("Pipeline은 데이터 누수(data leakage)를 방지한다")


=== Pipeline 장점 정리 ===
1. 코드 간결화: fit/predict 한 번으로 전체 파이프라인 실행
2. 데이터 누수 방지: 테스트 데이터에 학습 데이터 정보 유출 차단
3. 교차 검증 호환: cross_val_score와 자연스럽게 통합
4. 하이퍼파라미터 튜닝: GridSearchCV로 전체 파이프라인 최적화
````

**풀이 요점**

- 스크립트는 절마다 예제 코드를 문자열로 보여 주는 구조라서, 문자열 안의 import · 계산은 실제로 돌지 않는다.
- 모든 변환기가 `fit` → `transform`(또는 `fit_transform`) → `inverse_transform` 의 같은 틀을 따른다는 점이 절을 가로지르는 뼈대다.
- 인코더 셋은 크기 관계로 갈린다 — `LabelEncoder` 는 가짜 순서, `OneHotEncoder` 는 순서 없음, `OrdinalEncoder` 는 지정한 순서.
- `Pipeline` 절은 분할 → 묶기 → `fit` → `score` → 교차 검증 순으로 누수 없는 흐름을 보인다.
- `ColumnTransformer` 는 파이프라인의 한 단계로 들어가 열 종류별 처리를 한 객체로 합친다.
- 문자열 안의 `\n` 이 줄바꿈으로 바뀌어 `print(f"변환 전:` 줄이 둘로 쪼개져 보인다는 점에 주의한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
