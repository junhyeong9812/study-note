# python/python-data-science/11 — Seaborn 시각화 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 코드 문자열이 그대로 찍힐 뿐, 그림 파일은 생기지 않는다

**출력**

```text
=== Pairplot: 변수 쌍 시각화 ===

import seaborn as sns
import matplotlib.pyplot as plt

iris = sns.load_dataset('iris')

# 기본 pairplot
sns.pairplot(
    iris,
    hue='species',           # 색상 구분
    diag_kind='kde',         # 대각선: 'kde' 또는 'hist'
    plot_kws={'alpha': 0.6}, # 산점도 투명도
    height=2.5               # 각 서브플롯 크기
)
plt.suptitle('Iris Pairplot', y=1.02)
plt.savefig('pairplot.png', dpi=150)

# 선택한 변수만
sns.pairplot(iris, vars=['sepal_length', 'petal_length'],
             hue='species', kind='reg')  # 회귀선 포함
```

**왜 그런가**
코드 전체가 `"""..."""` 안의 문자열이고, `print` 는 그 문자열을 글자 그대로 출력할 뿐이다.
`sns.pairplot` 도 `plt.savefig` 도 호출되지 않으므로 `pairplot.png` 는 생기지 않는다.
문자열이 줄바꿈으로 시작하므로 제목 줄 바로 아래에 빈 줄이 하나 생긴다.
근거: 2-summary 「어디서 틀리나 6」.

### 2. 36 만 점으로 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
IQR = 20 - 10 = 10 이다.
위쪽 경계는 Q3 + 1.5×IQR = 20 + 15 = 35 다.
34 는 35 이하라 수염 안쪽이고, 36 은 35 를 넘으므로 이상치 점으로 찍힌다.

**왜 그런가**
boxplot 은 `Q3 + 1.5×IQR` 보다 큰 값을 수염 바깥의 이상치로 본다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 7」.

### 3. 8개 — x 범주마다 hue 범주 수만큼 나란히

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
요일 4개 각각에 성별 2개의 상자가 나란히 서므로 4 × 2 = 8 개다.

**왜 그런가**
`hue` 는 x 범주 하나를 hue 범주별 하위 그룹으로 다시 나눠 서로 다른 색 상자로 그린다.
근거: 2-summary 「동작 방식 (4)」.

### 4. seaborn 이 matplotlib 위에 구축되어 있어서

seaborn 함수는 그림을 결국 matplotlib 의 `Axes` 에 그린다.
그래서 matplotlib 의 제목 · 축 이름 함수가 그 그림에 그대로 적용된다.
근거: 2-summary 「동작 방식 (7)」, 「어디서 틀리나 1」.

### 5. 상관계수의 이론 범위에 색을 맞추고 「상관 없음」을 중립색에 두려고

상관계수는 -1 ~ 1 사이 값이므로 색 눈금의 양 끝을 그 범위에 고정하면 색의 진하기가 곧 상관의 세기가 된다.
`center=0` 은 0(상관 없음)을 컬러맵의 가운데 색에 두어, 양의 상관과 음의 상관이 반대쪽 색으로 갈리게 한다.
근거: 2-summary 「동작 방식 (2)」.

### 6. 상관계수는 수치 변수끼리만 계산하는 값이라서

`tips` 에는 `day`, `sex` 같은 범주 열이 섞여 있다.
상관 행렬은 수치 열 쌍마다 상관계수를 구한 것이므로, 범주 열은 먼저 빼야 한다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 5」.

### 7. 두 그룹 — 바이올린의 왼쪽 반과 오른쪽 반

`split=True` 는 hue 의 두 그룹을 바이올린 하나의 왼쪽 반 · 오른쪽 반에 나눠 그린다.
반쪽이 둘뿐이므로 원본처럼 두 그룹(남 · 여) 비교에 쓴다.
셋 이상일 때의 동작은 정리에서 다루지 않는다.
근거: 2-summary 「동작 방식 (5)」.

### 8. heatmap 은 숫자 하나로 요약, pairplot 은 점 전체를 보여 준다

heatmap 의 한 칸에는 두 변수의 상관계수라는 수 하나가 색과 숫자로 담긴다.
pairplot 의 한 칸에는 두 변수의 산점도(대각선은 한 변수의 분포)가 담겨 모든 데이터 점이 보인다.
그래서 heatmap 은 많은 변수의 상관을 한눈에 훑기 좋고, pairplot 은 관계의 모양 · 품종별 차이(`hue`)까지 탐색하는 EDA 의 시작점으로 좋다.
근거: 2-summary 「동작 방식 (2)」, 「동작 방식 (3)」.

### 9. boxplot 은 봉우리가 안 보이고, violinplot 은 보인다

boxplot 은 사분위수 · 수염 · 이상치만 그리므로 봉우리가 하나인지 둘인지 구별되지 않는다.
violinplot 은 boxplot 에 KDE 윤곽을 더한 그림이라, 봉우리 둘이면 허리가 잘록한 모양으로 드러난다.
근거: 2-summary 「동작 방식 (5)」, 「언제 쓰고 언제 안 쓰나」.

### 10. 같은 서브플롯 한 칸에 두 그림을 겹쳐 그리는 일이다

`plt.subplots(1, 3)` 가 만든 칸 가운데 세 번째 `Axes` 를 두 함수가 함께 그림판으로 쓴다.
그래서 안쪽을 비운 바이올린(분포 모양) 위에 개별 데이터 점이 겹쳐 보인다.
근거: 2-summary 「동작 방식 (5)」, 「동작 방식 (7)」.

## 실습 정답

### 실습 1. Seaborn 플롯 치트시트 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1단계 기본 설정 절 | `print("=== Seaborn 기본 설정 ===")` 와 `sns.set_theme(style='whitegrid')`, `sns.set_palette('husl')`, `sns.load_dataset(...)` 세 줄, `print(tips.head())` 가 든 문자열 |
| 2단계 Heatmap 절 | `select_dtypes(include='number')`, `.corr()`, `sns.heatmap(corr, annot=True, fmt='.2f', ..., linewidths=0.5)`, `np.random.rand(5, 7)` 와 `xticklabels`/`yticklabels` 히트맵 |
| 3단계 Pairplot 절 | `sns.pairplot(iris, hue='species', diag_kind='kde', plot_kws=..., height=2.5)`, `plt.suptitle`, `vars=[...]`, `kind='reg'` |
| 4단계 Boxplot 절 | `plt.subplots(1, 3, ...)`, `ax=axes[0]`~`axes[2]` 세 boxplot(`hue='sex'`, `orient='h'`), `# Boxplot 해석:` 주석 네 줄 |
| 5단계 Violinplot 절 | `sns.violinplot` 세 번(`split=True, inner='quart'`, `inner=None`), `sns.stripplot(..., ax=axes[2])` |
| 6단계 기타 플롯 절 | `sns.countplot`, `sns.scatterplot`, `sns.lineplot(data=fmri, ...)`, `sns.barplot`, `sns.histplot`, `sns.kdeplot`, `sns.FacetGrid(...)`, `g.map_dataframe`, `g.add_legend()` |
| 7단계 선택 가이드 | `print("=== Seaborn 플롯 선택 가이드 ===")` 와 여섯 줄의 `print` |
| 절 사이 빈 줄 | 각 절 앞의 `print()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-science/reference/seaborn-plots.py`

```python
# [데이터 과학 & 수학] Seaborn 시각화
# 설명: Seaborn, heatmap, pairplot, boxplot, violinplot 구조
# 팁: Seaborn은 matplotlib 위에 구축되어 plt.title(), plt.xlabel() 등을 함께 사용할 수 있다. hue 파라미터로 범주별 색상 구분이 가능하다. set_theme()으로 전체 스타일을 한 번에 설정한다. pairplot은 탐색적 분석(EDA)의 시작점으로 좋다.

# Seaborn - 통계 시각화 라이브러리
# pip install seaborn matplotlib pandas numpy

# 섹션 제목: 테마/팔레트 설정과 내장 데이터셋 로드
print("=== Seaborn 기본 설정 ===")
# set_theme/set_palette로 전체 차트 스타일 일괄 설정 가능
print("""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 스타일 설정
sns.set_theme(style='whitegrid')  # 'darkgrid', 'white', 'ticks'
sns.set_palette('husl')           # 'deep', 'muted', 'bright', 'Set2'

# 내장 데이터셋
tips = sns.load_dataset('tips')
iris = sns.load_dataset('iris')
titanic = sns.load_dataset('titanic')
print(tips.head())
""")

# 줄바꿈 출력
print()
# 섹션 제목: 행렬 형태 데이터를 색상 강도로 시각화
print("=== Heatmap: 상관관계 시각화 ===")
# DataFrame.corr()의 결과를 heatmap에 넣으면 변수 간 상관 패턴 한눈에 파악
print("""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 상관 행렬 히트맵
tips = sns.load_dataset('tips')
numeric_cols = tips.select_dtypes(include='number')
corr = numeric_cols.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(
    corr,
    annot=True,         # 셀에 값 표시
    fmt='.2f',          # 소수점 2자리
    cmap='coolwarm',    # 컬러맵
    vmin=-1, vmax=1,    # 값 범위
    center=0,           # 중심값
    square=True,        # 정사각형 셀
    linewidths=0.5      # 셀 경계선
)
plt.title('상관관계 히트맵')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=150)

# 커스텀 데이터 히트맵
data = np.random.rand(5, 7)
months = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
hours = ['9AM', '10AM', '11AM', '12PM', '1PM']
sns.heatmap(data, xticklabels=months, yticklabels=hours,
            cmap='YlOrRd', annot=True, fmt='.2f')
plt.title('시간대별 활동량')
""")

# 줄바꿈 출력
print()
# 섹션 제목: 모든 변수 쌍의 산점도와 분포를 한꺼번에 그리는 pairplot
print("=== Pairplot: 변수 쌍 시각화 ===")
# EDA의 시작점으로 자주 사용되며, hue로 범주별 색상 구분 가능
print("""
import seaborn as sns
import matplotlib.pyplot as plt

iris = sns.load_dataset('iris')

# 기본 pairplot
sns.pairplot(
    iris,
    hue='species',           # 색상 구분
    diag_kind='kde',         # 대각선: 'kde' 또는 'hist'
    plot_kws={'alpha': 0.6}, # 산점도 투명도
    height=2.5               # 각 서브플롯 크기
)
plt.suptitle('Iris Pairplot', y=1.02)
plt.savefig('pairplot.png', dpi=150)

# 선택한 변수만
sns.pairplot(iris, vars=['sepal_length', 'petal_length'],
             hue='species', kind='reg')  # 회귀선 포함
""")

# 줄바꿈 출력
print()
# 섹션 제목: 사분위수와 이상치를 한 번에 보여주는 boxplot
print("=== Boxplot: 상자 그림 ===")
# IQR(Q1~Q3)과 수염, 이상치를 시각화하여 분포의 산포 파악
print("""
import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 기본 boxplot
sns.boxplot(data=tips, x='day', y='total_bill', ax=axes[0])
axes[0].set_title('기본 Boxplot')

# hue로 그룹 비교
sns.boxplot(data=tips, x='day', y='total_bill',
            hue='sex', palette='Set2', ax=axes[1])
axes[1].set_title('성별 비교 Boxplot')

# 수평 boxplot
sns.boxplot(data=tips, x='total_bill', y='day',
            orient='h', ax=axes[2])
axes[2].set_title('수평 Boxplot')

plt.tight_layout()
plt.savefig('boxplot.png', dpi=150)

# Boxplot 해석:
# 상자 = IQR (Q1~Q3)
# 중앙선 = 중앙값 (Q2)
# 수염 = Q1 - 1.5*IQR ~ Q3 + 1.5*IQR
# 점 = 이상치 (수염 바깥)
""")

# 줄바꿈 출력
print()
# 섹션 제목: boxplot에 KDE를 결합한 violinplot
print("=== Violinplot: 바이올린 그림 ===")
# 분포의 모양까지 보여줘서 단봉/다봉성 파악에 유리
print("""
import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 기본 violinplot (boxplot + KDE)
sns.violinplot(data=tips, x='day', y='total_bill', ax=axes[0])
axes[0].set_title('기본 Violinplot')

# split: 두 그룹 비교
sns.violinplot(data=tips, x='day', y='total_bill',
               hue='sex', split=True,
               inner='quart',  # 'box', 'quart', 'point', 'stick'
               palette='muted', ax=axes[1])
axes[1].set_title('Split Violinplot')

# 개별 데이터 포인트 함께 표시
sns.violinplot(data=tips, x='day', y='total_bill',
               inner=None, color='lightblue', ax=axes[2])
sns.stripplot(data=tips, x='day', y='total_bill',
              size=3, color='black', alpha=0.3, ax=axes[2])
axes[2].set_title('Violin + Strip')

plt.tight_layout()
plt.savefig('violinplot.png', dpi=150)
""")

# 줄바꿈 출력
print()
# 섹션 제목: 빈도/산점/시계열/회귀/히스토 등 기타 플롯
print("=== 기타 유용한 플롯 ===")
# countplot, scatterplot, lineplot, barplot, histplot, FacetGrid 활용
print("""
import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

# --- Countplot (범주형 빈도) ---
sns.countplot(data=tips, x='day', hue='sex', palette='pastel')
plt.title('요일별 방문 빈도')

# --- Scatterplot (산점도) ---
sns.scatterplot(data=tips, x='total_bill', y='tip',
                hue='day', size='size', sizes=(20, 200))

# --- Lineplot (시계열) ---
fmri = sns.load_dataset('fmri')
sns.lineplot(data=fmri, x='timepoint', y='signal',
             hue='event', style='region',
             ci=95)  # 95% 신뢰구간

# --- Barplot (평균 + 신뢰구간) ---
sns.barplot(data=tips, x='day', y='total_bill',
            hue='sex', ci=95, palette='Set2')

# --- Histplot / KDEplot ---
sns.histplot(data=tips, x='total_bill', bins=20,
             kde=True, hue='time')
sns.kdeplot(data=tips, x='total_bill', hue='time',
            fill=True, alpha=0.3)

# --- FacetGrid (조건별 서브플롯) ---
g = sns.FacetGrid(tips, col='time', row='sex', margin_titles=True)
g.map_dataframe(sns.histplot, x='total_bill')
g.add_legend()
""")

# 줄바꿈 출력
print()
# 섹션 제목: 분석 목적별 Seaborn 플롯 선택 가이드
print("=== Seaborn 플롯 선택 가이드 ===")
# 분포 시각화에 적합한 플롯들
print("분포 비교: boxplot, violinplot, histplot, kdeplot")
# 두 변수 간 관계 시각화
print("관계 탐색: scatterplot, pairplot, lmplot (회귀)")
# 행렬 시각화
print("상관관계: heatmap")
# 범주별 비교
print("범주별 비교: barplot, countplot, catplot")
# 시간 순 변화
print("시계열: lineplot")
# 다차원 조건별 비교
print("조건별 분석: FacetGrid, catplot(kind='...')")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== Seaborn 기본 설정 ===

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 스타일 설정
sns.set_theme(style='whitegrid')  # 'darkgrid', 'white', 'ticks'
sns.set_palette('husl')           # 'deep', 'muted', 'bright', 'Set2'

# 내장 데이터셋
tips = sns.load_dataset('tips')
iris = sns.load_dataset('iris')
titanic = sns.load_dataset('titanic')
print(tips.head())


=== Heatmap: 상관관계 시각화 ===

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 상관 행렬 히트맵
tips = sns.load_dataset('tips')
numeric_cols = tips.select_dtypes(include='number')
corr = numeric_cols.corr()

plt.figure(figsize=(8, 6))
sns.heatmap(
    corr,
    annot=True,         # 셀에 값 표시
    fmt='.2f',          # 소수점 2자리
    cmap='coolwarm',    # 컬러맵
    vmin=-1, vmax=1,    # 값 범위
    center=0,           # 중심값
    square=True,        # 정사각형 셀
    linewidths=0.5      # 셀 경계선
)
plt.title('상관관계 히트맵')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=150)

# 커스텀 데이터 히트맵
data = np.random.rand(5, 7)
months = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
hours = ['9AM', '10AM', '11AM', '12PM', '1PM']
sns.heatmap(data, xticklabels=months, yticklabels=hours,
            cmap='YlOrRd', annot=True, fmt='.2f')
plt.title('시간대별 활동량')


=== Pairplot: 변수 쌍 시각화 ===

import seaborn as sns
import matplotlib.pyplot as plt

iris = sns.load_dataset('iris')

# 기본 pairplot
sns.pairplot(
    iris,
    hue='species',           # 색상 구분
    diag_kind='kde',         # 대각선: 'kde' 또는 'hist'
    plot_kws={'alpha': 0.6}, # 산점도 투명도
    height=2.5               # 각 서브플롯 크기
)
plt.suptitle('Iris Pairplot', y=1.02)
plt.savefig('pairplot.png', dpi=150)

# 선택한 변수만
sns.pairplot(iris, vars=['sepal_length', 'petal_length'],
             hue='species', kind='reg')  # 회귀선 포함


=== Boxplot: 상자 그림 ===

import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 기본 boxplot
sns.boxplot(data=tips, x='day', y='total_bill', ax=axes[0])
axes[0].set_title('기본 Boxplot')

# hue로 그룹 비교
sns.boxplot(data=tips, x='day', y='total_bill',
            hue='sex', palette='Set2', ax=axes[1])
axes[1].set_title('성별 비교 Boxplot')

# 수평 boxplot
sns.boxplot(data=tips, x='total_bill', y='day',
            orient='h', ax=axes[2])
axes[2].set_title('수평 Boxplot')

plt.tight_layout()
plt.savefig('boxplot.png', dpi=150)

# Boxplot 해석:
# 상자 = IQR (Q1~Q3)
# 중앙선 = 중앙값 (Q2)
# 수염 = Q1 - 1.5*IQR ~ Q3 + 1.5*IQR
# 점 = 이상치 (수염 바깥)


=== Violinplot: 바이올린 그림 ===

import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# 기본 violinplot (boxplot + KDE)
sns.violinplot(data=tips, x='day', y='total_bill', ax=axes[0])
axes[0].set_title('기본 Violinplot')

# split: 두 그룹 비교
sns.violinplot(data=tips, x='day', y='total_bill',
               hue='sex', split=True,
               inner='quart',  # 'box', 'quart', 'point', 'stick'
               palette='muted', ax=axes[1])
axes[1].set_title('Split Violinplot')

# 개별 데이터 포인트 함께 표시
sns.violinplot(data=tips, x='day', y='total_bill',
               inner=None, color='lightblue', ax=axes[2])
sns.stripplot(data=tips, x='day', y='total_bill',
              size=3, color='black', alpha=0.3, ax=axes[2])
axes[2].set_title('Violin + Strip')

plt.tight_layout()
plt.savefig('violinplot.png', dpi=150)


=== 기타 유용한 플롯 ===

import seaborn as sns
import matplotlib.pyplot as plt

tips = sns.load_dataset('tips')

# --- Countplot (범주형 빈도) ---
sns.countplot(data=tips, x='day', hue='sex', palette='pastel')
plt.title('요일별 방문 빈도')

# --- Scatterplot (산점도) ---
sns.scatterplot(data=tips, x='total_bill', y='tip',
                hue='day', size='size', sizes=(20, 200))

# --- Lineplot (시계열) ---
fmri = sns.load_dataset('fmri')
sns.lineplot(data=fmri, x='timepoint', y='signal',
             hue='event', style='region',
             ci=95)  # 95% 신뢰구간

# --- Barplot (평균 + 신뢰구간) ---
sns.barplot(data=tips, x='day', y='total_bill',
            hue='sex', ci=95, palette='Set2')

# --- Histplot / KDEplot ---
sns.histplot(data=tips, x='total_bill', bins=20,
             kde=True, hue='time')
sns.kdeplot(data=tips, x='total_bill', hue='time',
            fill=True, alpha=0.3)

# --- FacetGrid (조건별 서브플롯) ---
g = sns.FacetGrid(tips, col='time', row='sex', margin_titles=True)
g.map_dataframe(sns.histplot, x='total_bill')
g.add_legend()


=== Seaborn 플롯 선택 가이드 ===
분포 비교: boxplot, violinplot, histplot, kdeplot
관계 탐색: scatterplot, pairplot, lmplot (회귀)
상관관계: heatmap
범주별 비교: barplot, countplot, catplot
시계열: lineplot
조건별 분석: FacetGrid, catplot(kind='...')
````

**풀이 요점**
- 이 스크립트는 그림을 그리지 않는다 — 각 절의 코드를 문자열로 출력하는 치트시트다.
- 상관 히트맵은 「수치 열만 → `.corr()` → `heatmap`」 차례가 핵심이고, `vmin`/`vmax`/`center` 가 상관계수의 범위와 맞물린다.
- boxplot · violinplot 절은 `plt.subplots` 로 칸을 만들고 `ax=` 로 칸을 골라 그리는 matplotlib 연동을 보여 준다.
- `hue` 는 거의 모든 절에 등장한다 — 범주별 색 구분이 seaborn 의 기본 도구다.
- 문자열 속 `ci=95` 는 버전에 따라 다른 인자로 바뀌었을 수 있으니, 떼어 돌릴 때 경고가 나면 그 부분을 의심한다(확인 필요).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
