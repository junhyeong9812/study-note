# python/python-data-science/11 — Seaborn 시각화 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. Pairplot 절을 담은 스크립트를 실행하면 (예측)

```python
# 질문용 발췌
print("=== Pairplot: 변수 쌍 시각화 ===")
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
```

- 이 발췌를 실행하면 화면에 무엇이 찍히나?
- 실행이 끝난 뒤 `pairplot.png` 파일이 생기나?

### 2. Q1=10, Q3=20 인 그룹의 값 34 와 36 (예측)

- 이 그룹의 boxplot 에서 34 와 36 가운데 어느 값이 수염 바깥 점으로 찍히나?

### 3. x 범주 4개 × hue 범주 2개의 boxplot (예측)

```python
# 질문용 발췌 — day 에는 범주 4개, sex 에는 범주 2개가 있다고 하자
sns.boxplot(data=tips, x='day', y='total_bill',
            hue='sex', palette='Set2', ax=axes[1])
```

- 이 칸에 상자는 모두 몇 개 그려지나?

### 4. seaborn 그림에 `plt.title()` 이 먹히는 까닭 (왜)

- seaborn 함수로 그린 그림에 matplotlib 의 `plt.title()` · `plt.xlabel()` 을 그대로 쓸 수 있는 까닭은 무엇인가?

### 5. 상관 히트맵에 `vmin=-1, vmax=1, center=0` 을 주는 까닭 (왜)

- 상관 행렬을 히트맵으로 그릴 때 색 눈금을 -1 ~ 1 로 고정하고 0 을 가운데 색에 두는 까닭은 무엇인가?

### 6. `.corr()` 앞의 `select_dtypes(include='number')` (경계)

- 원본이 상관 행렬을 만들기 전에 수치 열만 남기는 까닭은 무엇인가?

### 7. `split=True` 바이올린이 비교할 수 있는 그룹 수 (경계)

- `split=True` 바이올린은 hue 의 그룹을 몇 개까지 한 바이올린 안에서 나눠 보여 주게 되어 있나?

### 8. heatmap 과 pairplot (연결)

- 둘 다 「변수 쌍의 관계」를 보는 그림인데, 한 칸에 담기는 정보는 어떻게 다른가?

### 9. boxplot 대신 violinplot 을 고를 때 (연결)

- 봉우리가 둘인 분포를 boxplot 과 violinplot 으로 각각 그리면 무엇이 보이고 무엇이 안 보이나?

### 10. `ax=axes[2]` 를 두 함수에 같이 주면 (연결)

- violinplot 과 stripplot 에 같은 `ax=axes[2]` 를 주는 것은 matplotlib 의 서브플롯 개념으로 보면 무슨 일인가?

## 실습

### 실습 1. Seaborn 플롯 치트시트 스크립트 만들기

**만들 것** — 실행하면 Seaborn 의 주요 플롯 사용법을 절마다 「제목 줄 + 코드 문자열」로 출력하고, 마지막에 플롯 선택 가이드를 출력하는 Python 스크립트.

**준비물** — 스크립트 자체는 `print` 만 쓰므로 Python 만 있으면 된다. 문자열 속 코드를 따로 떼어 돌려 보려면 `pip install seaborn matplotlib pandas numpy` 가 필요하다.

**요구 조건**

1. 1단계 — `=== Seaborn 기본 설정 ===` 제목 줄을 출력하고, 이어서 네 라이브러리 import, `set_theme`(whitegrid), `set_palette`(husl), 내장 데이터셋 세 개(`tips`, `iris`, `titanic`) 로드, `tips.head()` 출력 코드를 담은 문자열을 출력한다.
2. 2단계 — 빈 줄 뒤 Heatmap 절: `tips` 의 수치 열만 골라 상관 행렬을 만들고, 값 표시 · 소수 둘째 자리 · -1~1 범위 · 중심 0 · 정사각 칸 · 경계선을 준 `heatmap` 을 그려 제목 · 레이아웃 조정 · 저장하는 코드와, 무작위 5×7 행렬에 요일 · 시간 눈금 이름을 붙인 두 번째 `heatmap` 코드를 출력한다.
3. 3단계 — 빈 줄 뒤 Pairplot 절: `iris` 를 품종별 색 · 대각선 KDE · 반투명 산점도 · 칸 크기로 그리고 전체 제목을 달아 저장하는 코드와, 두 변수만 골라 회귀선을 넣은 `pairplot` 코드를 출력한다.
4. 4단계 — 빈 줄 뒤 Boxplot 절: 가로 칸 셋을 만들어 기본 · 성별 hue 비교 · 가로 방향 boxplot 을 칸마다 그리고 칸 제목을 단 뒤 저장하는 코드와, boxplot 해석 주석 네 줄(상자 · 중앙선 · 수염 · 점)을 출력한다.
5. 5단계 — 빈 줄 뒤 Violinplot 절: 가로 칸 셋에 기본 · 성별 split(안쪽 사분위 선) · 안쪽을 비운 바이올린 위에 stripplot 을 겹친 그림을 그리고 저장하는 코드를 출력한다.
6. 6단계 — 빈 줄 뒤 기타 플롯 절: countplot · scatterplot(점 색과 크기에 변수) · `fmri` 의 lineplot(95% 신뢰구간) · barplot · histplot 과 kdeplot · `time` × `sex` FacetGrid 코드를 출력한다.
7. 7단계 — 빈 줄 뒤 `=== Seaborn 플롯 선택 가이드 ===` 와 여섯 줄 가이드(분포 비교 · 관계 탐색 · 상관관계 · 범주별 비교 · 시계열 · 조건별 분석)를 출력한다.

**시작 코드**

```python
# Seaborn - 통계 시각화 라이브러리
# pip install seaborn matplotlib pandas numpy

print("=== Seaborn 기본 설정 ===")
print("""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 스타일 설정
# TODO: 테마(whitegrid)와 팔레트(husl)를 정한다

# 내장 데이터셋
# TODO: tips, iris, titanic 을 불러오고 tips 앞부분을 출력한다
""")

print()
print("=== Heatmap: 상관관계 시각화 ===")
print("""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# 상관 행렬 히트맵
tips = sns.load_dataset('tips')
# TODO: 수치 열만 골라 corr 을 만든다

plt.figure(figsize=(8, 6))
# TODO: corr 히트맵 (annot, fmt, cmap='coolwarm', vmin/vmax, center, square, linewidths=0.5)
plt.title('상관관계 히트맵')
plt.tight_layout()
plt.savefig('heatmap.png', dpi=150)

# 커스텀 데이터 히트맵
# TODO: 5x7 무작위 행렬, 요일/시간 눈금 이름, cmap='YlOrRd'
plt.title('시간대별 활동량')
""")

print()
print("=== Pairplot: 변수 쌍 시각화 ===")
print("""
# TODO: iris pairplot (hue, diag_kind, plot_kws={'alpha': 0.6}, height=2.5)
plt.suptitle('Iris Pairplot', y=1.02)
plt.savefig('pairplot.png', dpi=150)
# TODO: 두 변수만 + 회귀선
""")

print()
print("=== Boxplot: 상자 그림 ===")
print("""
# TODO: fig, axes = plt.subplots(...) 와 boxplot 세 개 (기본 / hue='sex', palette='Set2' / 가로)
plt.tight_layout()
plt.savefig('boxplot.png', dpi=150)
# TODO: Boxplot 해석 주석 네 줄
""")

print()
print("=== Violinplot: 바이올린 그림 ===")
print("""
# TODO: violinplot 세 개 (기본 / split + inner='quart', palette='muted' / inner=None, color='lightblue' + stripplot size=3, color='black', alpha=0.3)
plt.tight_layout()
plt.savefig('violinplot.png', dpi=150)
""")

print()
print("=== 기타 유용한 플롯 ===")
print("""
# TODO: countplot(palette='pastel'), scatterplot(sizes=(20, 200)), lineplot(fmri),
#       barplot(palette='Set2'), histplot(bins=20), kdeplot(alpha=0.3), FacetGrid
""")

print()
print("=== Seaborn 플롯 선택 가이드 ===")
# TODO: 가이드 여섯 줄을 출력한다
```

**확인 방법** — `python seaborn-plots.py` 로 실행해 일곱 절의 제목 줄과 각 절의 코드 문자열, 마지막 가이드 여섯 줄이 차례대로 찍히는지 본다. 문자열 속 코드를 별도 파일로 떼어 돌리면 `heatmap.png` 등의 그림 파일이 생기는지도 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
