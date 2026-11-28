# python/python-data-science/11 — Seaborn 시각화 — 정리 (힌트)

> 출처 — study-site 항목 `python/seaborn-plots`(항목 데이터 `data/python/data-science.json`) · 정답 코드 study-practice `python/python-data-science/reference/seaborn-plots.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Seaborn 은 「matplotlib 주방 위에 차린 통계 그림 밀키트」다.**
matplotlib 은 축 · 선 · 점을 하나하나 손질해 요리하는 주방이다.
Seaborn 은 그 주방을 그대로 쓰면서, 「표 + 열 이름」만 넣으면 상자 그림 · 히트맵 같은 통계 그림이 완성되어 나오는 밀키트를 준다.
요리가 끝난 뒤 접시에 장식을 더하듯, 다 그린 그림에 `plt.title()` 같은 matplotlib 함수로 제목과 축 이름을 덧붙일 수 있다.
Seaborn 시각화도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주방(조리 도구 전체) | matplotlib (`plt`, `Figure`, `Axes`) |
| 밀키트 | `sns.heatmap`, `sns.boxplot` 같은 seaborn 함수 |
| 재료 상자 | pandas `DataFrame` (예: `tips`, `iris`) |
| 레시피에 적힌 재료 이름 | `x='day'`, `y='total_bill'` 같은 열 이름 |
| 접시 장식 | `plt.title()`, `axes[0].set_title()` |
| 주방 전체의 조명 · 식기 통일 | `sns.set_theme()`, `sns.set_palette()` |

```text
 DataFrame (표)            seaborn 함수                 matplotlib 그림
┌──────────────┐   x, y,  ┌─────────────────┐  그린다  ┌──────────────┐
│ day │ bill │ sex│ ──────▶ │ sns.boxplot(...) │ ───────▶ │  Axes 위의 그림 │
└──────────────┘   hue    └─────────────────┘         └──────┬───────┘
                                                               │ plt.title()
                                                               ▼  plt.savefig()
                                                          heatmap.png 등
```

## 이 주제가 답하려는 질문

1. 표(`DataFrame`)와 열 이름만으로 통계 그림을 어떻게 그리나?
2. 변수끼리의 관계는 어떤 그림으로 보나 — `heatmap` 과 `pairplot` 은 무엇이 다른가?
3. 범주별 분포는 어떤 그림으로 비교하나 — `boxplot` 과 `violinplot` 은 무엇이 다른가?
4. Seaborn 그림에 matplotlib 의 제목 · 서브플롯 · 저장 기능을 어떻게 섞어 쓰나?

## 동작 방식

### (1) 기본 설정 — 테마 · 팔레트 · 내장 데이터셋

**언제 쓰나** — 그림을 그리기 전에 한 번, 모든 그림의 모양을 한꺼번에 맞출 때 쓴다.

```text
sns.set_theme(style='whitegrid')   →  이후 모든 그림의 배경 · 격자 스타일이 바뀐다
sns.set_palette('husl')            →  이후 모든 그림의 기본 색 묶음이 바뀐다
tips = sns.load_dataset('tips')    →  연습용 표(DataFrame)를 받는다
```

- `set_theme` 은 전체 스타일을 한 번에 설정한다. `style` 값은 `'whitegrid'`, `'darkgrid'`, `'white'`, `'ticks'` 가 예로 나온다.
- `set_palette` 는 기본 색 묶음을 정한다. 예로 `'husl'`, `'deep'`, `'muted'`, `'bright'`, `'Set2'` 가 나온다.
- `load_dataset` 은 `tips`(식당 계산서), `iris`(붓꽃), `titanic`, `fmri` 같은 연습용 표를 준다.
- `tips.head()` 는 표의 앞 몇 줄을 보여 준다.

> **팔레트(palette)** — 그림에서 범주마다 돌려 쓰는 색의 묶음.\
> 예: `'Set2'` 팔레트면 남 · 여 두 범주에 서로 다른 두 색이 붙는다.

### (2) Heatmap — 행렬을 색의 진하기로

**언제 쓰나** — 숫자로 된 행렬(특히 상관 행렬)의 패턴을 한눈에 볼 때 쓴다.

```text
tips ──select_dtypes(include='number')──▶ 수치 열만 남은 표
     ──.corr()──▶ 변수×변수 상관 행렬 (값 범위 -1 ~ 1)
     ──sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)──▶
        칸마다 색이 칠해지고, 칸 안에 숫자(소수 둘째 자리)가 적힌 격자
```

- 먼저 `select_dtypes(include='number')` 로 수치 열만 고른다.
- `.corr()` 은 열 쌍마다 상관계수를 계산해 정사각 행렬을 만든다.
- `annot=True` 는 칸 안에 값을 적고, `fmt='.2f'` 는 그 값을 소수 둘째 자리로 적는다.
- `cmap` 은 값을 색으로 바꾸는 규칙(컬러맵)이다.
- `vmin=-1, vmax=1` 은 색 눈금의 양 끝을 상관계수의 이론 범위에 맞춘다.
- `center=0` 은 0(상관 없음)을 컬러맵의 가운데 색에 둔다 — 그래서 양의 상관과 음의 상관이 서로 반대쪽 색으로 갈린다.
- `square=True` 는 칸을 정사각형으로, `linewidths=0.5` 는 칸 사이에 경계선을 넣는다.
- 상관 행렬이 아닌 임의의 행렬도 그릴 수 있다. 원본은 `np.random.rand(5, 7)` 로 만든 5×7 행렬에 `xticklabels`, `yticklabels` 로 축 눈금 이름(요일 · 시간)을 붙인다.

> **상관계수** — 두 변수가 함께 커지거나 작아지는 정도를 -1 ~ 1 로 나타낸 값.\
> 예: 계산 금액과 팁이 같이 커지면 양수, 관계가 없으면 0 근처다.

> **컬러맵(cmap)** — 연속된 숫자를 연속된 색으로 바꾸는 규칙.\
> 예: `'coolwarm'` 은 낮은 값을 파랑 계열, 높은 값을 빨강 계열로 칠한다.

### (3) Pairplot — 모든 변수 쌍을 한 장에

**언제 쓰나** — 처음 받은 데이터에서 어떤 변수끼리 관계가 있는지 훑어볼 때(탐색적 분석의 시작점) 쓴다.

```text
iris (수치 열 4개 + species)
   └─ sns.pairplot(iris, hue='species', diag_kind='kde')
        ┌──────┬──────┬──────┬──────┐
        │ KDE  │ 산점 │ 산점 │ 산점 │   대각선: 변수 하나의 분포
        ├──────┼──────┼──────┼──────┤   그 밖: 두 변수의 산점도
        │ 산점 │ KDE  │ 산점 │ 산점 │   점 색: species 별로 다름
        ├──────┼──────┼──────┼──────┤
        │ ...  │ ...  │ KDE  │ ...  │
        └──────┴──────┴──────┴──────┘
```

- 수치 변수가 n 개면 n×n 격자가 생긴다.
- 대각선 칸에는 그 변수 하나의 분포가 그려진다. `diag_kind` 로 `'kde'`(매끈한 곡선) 또는 `'hist'`(막대)를 고른다.
- 대각선 밖의 칸에는 두 변수의 산점도가 그려진다.
- `hue='species'` 는 품종마다 다른 색으로 점을 칠한다.
- `plot_kws={'alpha': 0.6}` 는 산점도 점을 반투명하게, `height=2.5` 는 칸 하나의 크기를 정한다.
- `vars=[...]` 로 그릴 변수를 고를 수 있고, `kind='reg'` 는 산점도에 회귀선을 넣는다.
- 전체 그림 위 제목은 `plt.suptitle('Iris Pairplot', y=1.02)` 로 단다.

> **EDA(탐색적 데이터 분석)** — 가설을 세우기 전에 데이터를 그려 보고 요약해 특징을 찾는 단계.\
> 예: pairplot 으로 꽃잎 길이와 너비가 같이 움직이는지 먼저 본다.

> **KDE(커널 밀도 추정)** — 데이터 점들로부터 분포를 매끈한 곡선으로 추정한 것.\
> 예: 히스토그램의 막대 윤곽을 부드럽게 이은 듯한 곡선.

### (4) Boxplot — 사분위수와 이상치

**언제 쓰나** — 범주(요일 등)마다 수치(계산 금액 등)의 퍼짐과 이상치를 비교할 때 쓴다.

```text
값 ▲
   │      ●          ← 이상치: 수염 바깥 점
   │      ┬          ← 수염 끝 (원본 기준: Q3 + 1.5×IQR)
   │    ┌─┴─┐        ← Q3
   │    │───│        ← 중앙값 Q2
   │    └─┬─┘        ← Q1         상자 높이 = IQR = Q3 - Q1
   │      ┴          ← 수염 끝 (원본 기준: Q1 - 1.5×IQR)
   └──────────────▶ 범주(x)
```

- 상자는 IQR, 즉 Q1 부터 Q3 까지다.
- 상자 안의 선은 중앙값(Q2)이다.
- 원본의 해석에서 수염은 `Q1 - 1.5*IQR ~ Q3 + 1.5*IQR` 이다(이 서술의 정확도는 「어디서 틀리나」 7번을 보라).
- 수염 바깥의 점은 이상치다 — 즉 `Q3 + 1.5×IQR` 보다 크거나 `Q1 - 1.5×IQR` 보다 작은 값이다.
- `hue='sex'` 를 주면 x 범주 하나마다 hue 범주 수만큼 상자가 나란히 선다. x 범주가 a 개, hue 범주가 b 개면 상자는 a×b 개다.
- x 와 y 를 바꾸고 `orient='h'` 를 주면 상자가 가로로 눕는다.

> **사분위수(Q1 · Q2 · Q3)** — 정렬한 값을 4등분하는 세 경계값.\
> 예: Q1 은 아래에서 25% 지점, Q2 는 50%(중앙값), Q3 는 75% 지점.

> **IQR(사분위 범위)** — Q3 - Q1, 가운데 50% 값이 퍼진 폭.\
> 예: Q1=10, Q3=20 이면 IQR=10.

> **이상치** — 나머지 값들에서 동떨어진 값. boxplot 에서는 수염 바깥 점으로 찍힌다.\
> 예: 대부분 10~30 달러인 계산서 사이의 50 달러 계산서.

### (5) Violinplot — 상자 그림 + 분포 모양

**언제 쓰나** — 퍼짐뿐 아니라 분포의 **모양**(봉우리가 하나인지 여럿인지)까지 비교할 때 쓴다.

```text
boxplot:  ┌─┐  봉우리 정보 없음      violinplot:   ╱╲     봉우리 둘이면
          │─│                                    ╲╱     허리가 잘록하게
          └─┘                                    ╱  ╲   드러난다
                                                 ╲__╱
split=True + hue(두 그룹):  왼쪽 반 = 그룹 A 의 KDE,  오른쪽 반 = 그룹 B 의 KDE
```

- 원본은 violinplot 을 「boxplot + KDE」로 설명한다 — 바깥 윤곽이 KDE 곡선을 좌우 대칭으로 펼친 모양이다.
- 그래서 단봉(봉우리 하나)인지 다봉(봉우리 여럿)인지 보기 좋다. boxplot 의 상자만으로는 이것이 보이지 않는다.
- `split=True` 는 hue 의 두 그룹을 바이올린 하나의 왼쪽 반 · 오른쪽 반에 나눠 그린다. 원본은 이것을 「두 그룹 비교」로 쓴다.
- `inner` 는 바이올린 안쪽에 그릴 것을 정한다: `'box'`, `'quart'`(사분위 선), `'point'`, `'stick'`, 그리고 `None`(안쪽을 비움).
- `inner=None` 인 바이올린 위에 `sns.stripplot` 을 같은 `ax` 로 겹치면 개별 데이터 점까지 함께 보인다.

> **단봉 · 다봉** — 분포의 봉우리가 하나(단봉)인지 둘 이상(다봉)인지.\
> 예: 점심 손님과 저녁 손님의 금액대가 다르면 봉우리가 둘로 갈릴 수 있다.

### (6) 그 밖의 플롯과 FacetGrid

**언제 쓰나** — 목적별로 알맞은 그림을 고를 때 쓴다.

```text
countplot(x='day', hue='sex')          → 범주별 「개수」 막대
scatterplot(x, y, hue='day', size=..)  → 두 수치의 산점도, 점 색 · 크기에 변수 추가
lineplot(x='timepoint', y='signal')    → 시간에 따른 변화 선 + 신뢰구간 띠
barplot(x='day', y='total_bill')       → 범주별 「평균」 막대 + 신뢰구간
histplot(x, bins=20, kde=True)         → 히스토그램 (+ KDE 곡선)
kdeplot(x, hue, fill=True)             → KDE 곡선 (면 채움)
FacetGrid(col='time', row='sex')       → 조건 조합마다 작은 그림 격자
```

- `countplot` 은 y 없이 x 범주마다 행의 개수를 센다.
- `scatterplot` 은 `hue` 로 색, `size` 로 점 크기에 변수를 하나씩 더 싣는다. `sizes=(20, 200)` 은 점 크기의 범위다.
- `lineplot` 은 `hue` 와 `style` 로 선을 나누고, 원본은 `ci=95` 로 95% 신뢰구간을 표시한다.
- `barplot` 은 막대 높이가 평균이고 신뢰구간을 함께 그린다 — 개수를 세는 `countplot` 과 다르다.
- `FacetGrid(tips, col='time', row='sex')` 는 열 방향으로 time, 행 방향으로 sex 를 나눈 격자를 만들고, `g.map_dataframe(sns.histplot, x='total_bill')` 로 칸마다 같은 그림을 그린다. `margin_titles=True` 는 칸 제목을 가장자리에, `g.add_legend()` 는 범례를 단다.

> **신뢰구간** — 표본으로 추정한 값(평균 등)이 있을 법한 범위.\
> 예: 막대 위 검은 세로줄이 「평균이 대략 이 안쪽」임을 보여 준다.

### (7) matplotlib 과 섞어 쓰기

**언제 쓰나** — 제목 · 여러 칸 배치 · 파일 저장처럼 seaborn 이 직접 하지 않는 일을 할 때 쓴다.

```text
fig, axes = plt.subplots(1, 3, figsize=(15, 5))   →  가로로 칸 3개
sns.boxplot(..., ax=axes[0])                      →  첫 칸에 그린다
axes[0].set_title('기본 Boxplot')                  →  첫 칸 제목
plt.tight_layout()                                →  칸끼리 글자가 겹치지 않게 간격 조정
plt.savefig('boxplot.png', dpi=150)               →  파일로 저장
```

- Seaborn 은 matplotlib 위에 만들어졌으므로 그림은 결국 matplotlib 의 `Axes` 에 그려진다.
- 그래서 `plt.title()`, `plt.xlabel()` 같은 matplotlib 함수를 seaborn 그림에 그대로 쓸 수 있다.
- `ax=` 인자로 어느 칸(서브플롯)에 그릴지 정한다. 같은 `ax` 를 두 번 주면 두 그림이 한 칸에 겹친다(violin + strip).
- `plt.figure(figsize=(8, 6))` 은 새 그림판 크기를, `dpi=150` 은 저장 해상도를 정한다.

> **서브플롯** — 그림판 하나를 나눈 칸 하나(matplotlib 의 `Axes`).\
> 예: `plt.subplots(1, 3)` 은 가로로 서브플롯 세 개를 만든다.

## 문법 — 형태와 규칙

```python
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_theme(style='whitegrid')          # 전체 스타일 한 번에
tips = sns.load_dataset('tips')

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
sns.boxplot(data=tips, x='day', y='tip', hue='sex', ax=axes[0])
sns.violinplot(data=tips, x='day', y='tip', inner='quart', ax=axes[1])
axes[0].set_title('Box')
axes[1].set_title('Violin')
plt.tight_layout()
plt.savefig('compare.png', dpi=150)
```

- 꼴은 대개 `sns.함수(data=표, x='열', y='열', hue='열', ax=칸)` 이다.
- `x`, `y`, `hue` 에는 값이 아니라 **열 이름 문자열**을 준다.
- `hue` 는 범주별 색 구분이다 — 거의 모든 플롯이 받는다.
- `palette` 로 그 그림 하나의 색 묶음을, `color` 로 단색을 정한다.
- 숫자 행렬을 받는 `heatmap` 은 `data=` 꼴이 아니라 행렬을 첫 인자로 받는다.

| 파라미터 | 쓰인 곳 | 뜻 |
|---|---|---|
| `hue` | 대부분 | 범주별 색 구분 |
| `ax` | box · violin · strip | 그릴 서브플롯 |
| `annot`, `fmt` | heatmap | 칸 안 값 표시 · 표시 형식 |
| `cmap`, `vmin`, `vmax`, `center` | heatmap | 컬러맵 · 색 눈금 양 끝 · 중심값 |
| `square`, `linewidths` | heatmap | 정사각 칸 · 칸 경계선 |
| `diag_kind`, `plot_kws`, `height`, `vars`, `kind` | pairplot | 대각선 종류 · 산점도 옵션 · 칸 크기 · 변수 선택 · 회귀선 |
| `orient` | boxplot | 가로(`'h'`) 배치 |
| `split`, `inner` | violinplot | 두 그룹 반쪽 비교 · 안쪽 표시 |
| `size`, `sizes` | scatterplot | 점 크기에 실을 변수 · 크기 범위 |
| `style` | lineplot | 선 모양으로 나눌 변수 |
| `ci` | lineplot · barplot | 신뢰구간(원본 기준 — 「어디서 틀리나」 8번) |
| `bins`, `kde`, `fill`, `alpha` | histplot · kdeplot | 구간 수 · KDE 곡선 추가 · 면 채움 · 투명도 |
| `col`, `row`, `margin_titles` | FacetGrid | 열 · 행 방향 분할 · 가장자리 제목 |

## 어디서 틀리나

### 1. seaborn 만으로 제목까지 달려 한다
Seaborn 은 matplotlib 위에 구축되어 있다.
제목 · 축 이름은 `plt.title()`, `plt.xlabel()`, 서브플롯이면 `axes[i].set_title()` 처럼 matplotlib 쪽 함수로 단다.

### 2. 범주 색을 손으로 나눠 그린다
범주별로 데이터를 잘라 여러 번 그릴 필요가 없다.
`hue` 파라미터 하나로 범주별 색 구분이 된다.

### 3. 그림마다 스타일을 따로 맞춘다
`set_theme()` 으로 전체 스타일을 한 번에 설정한다.
그 뒤에 그리는 모든 그림에 적용되므로 그림마다 반복할 필요가 없다.

### 4. 무엇부터 그릴지 몰라 헤맨다
`pairplot` 은 탐색적 분석(EDA)의 시작점으로 좋다.
모든 변수 쌍을 한 장에 보여 주므로, 관계가 있어 보이는 쌍을 골라 자세히 들여다보면 된다.

### 5. 범주 열까지 넣고 상관 행렬을 만든다
상관계수는 수치 변수끼리 계산하는 값이다.
그래서 원본은 `select_dtypes(include='number')` 로 수치 열만 고른 뒤 `.corr()` 을 부른다.

### 6. 이 예제 파일을 돌리면 그림이 생긴다고 여긴다
원본 예제 파일은 각 절의 코드를 `print("""...""")` 안의 **문자열**로 담아 출력할 뿐이다.
문자열 속 코드는 실행되지 않으므로 `heatmap.png` 같은 파일은 생기지 않는다.
그림을 보려면 문자열 속 코드를 따로 떼어 실행해야 한다.

### 7. 수염 끝 = `Q3 + 1.5×IQR` 로 단정한다
원본의 주장 → 「수염 = Q1 - 1.5*IQR ~ Q3 + 1.5*IQR」.
왜 의심스러운가 → 흔히 쓰는 정의에서 `Q1 - 1.5×IQR` · `Q3 + 1.5×IQR` 은 **경계선**이고, 수염은 그 경계 안쪽에 있는 가장 먼 실제 데이터 값까지만 그려진다(확인 필요).
이상치 판정(경계 바깥 = 점)은 어느 쪽 해석이든 같다.

### 8. `ci=95` 를 어느 버전에서나 쓴다
원본의 주장 → `lineplot` · `barplot` 에 `ci=95` 로 95% 신뢰구간을 준다.
왜 의심스러운가 → 최근 seaborn 버전에서는 이 인자가 다른 이름(`errorbar`)으로 바뀌어 경고가 날 수 있다(확인 필요).

### 9. 무작위 히트맵이 늘 같은 그림이라고 여긴다
`np.random.rand(5, 7)` 는 부를 때마다 다른 값을 만든다.
시드를 고정하지 않았으므로 「시간대별 활동량」 히트맵은 그릴 때마다 색이 달라진다.
또 원본의 변수 이름 `months` 에는 실제로 요일(`'Mon'` … `'Sun'`)이 들어 있다 — 이름과 내용이 어긋날 뿐 동작에는 영향이 없다.

### 10. 저장 순서를 뒤섞는다
원본은 그리기 → 제목 → `plt.tight_layout()` → `plt.savefig()` 차례를 지킨다.
간격 조정은 저장 전에 해야 저장된 파일에 반영된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `print("""...""")` 는 문자열을 그대로 출력하고 그 속 코드를 실행하지 않는다 | Python 언어 |
| seaborn 은 matplotlib 위에서 그린다, `ax=` 로 칸을 고른다 | seaborn 라이브러리의 설계 |
| `set_theme` 이 이후 그림 전체에 적용된다 | seaborn 라이브러리 |
| `hue` · `split` · `inner` 등 파라미터 이름과 동작 | seaborn 라이브러리 — 버전마다 바뀔 수 있음 |
| `ci=95` 가 신뢰구간을 그린다 | seaborn 의 특정 버전 (확인 필요) |
| 수염 끝 위치의 정의 | seaborn(내부적으로 matplotlib) 의 기본 설정 (확인 필요) |
| `select_dtypes`, `.corr()` 의 동작 | pandas 라이브러리 |
| `np.random.rand` 가 실행마다 다른 값을 낸다 | NumPy — 시드를 고정하지 않았을 때 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 범주별 분포 비교 | `boxplot`, `violinplot`, `histplot`, `kdeplot` | `lineplot`(순서 없는 범주를 선으로 잇게 된다) |
| 분포 모양(단봉/다봉)이 궁금하다 | `violinplot`, `kdeplot` | `boxplot` 단독(모양이 안 보인다) |
| 두 수치 변수의 관계 | `scatterplot`, `pairplot`, `lmplot`(회귀) | `countplot` |
| 여러 변수의 상관을 한 장에 | `heatmap`(상관 행렬) | 범주 열이 섞인 상관 행렬 |
| 범주별 개수 · 평균 | `countplot`(개수), `barplot`(평균), `catplot` | 개수가 궁금한데 `barplot` |
| 시간에 따른 변화 | `lineplot` | `boxplot` |
| 조건 조합마다 같은 그림 | `FacetGrid`, `catplot(kind='...')` | 조건별로 복사한 코드 |

## 핵심 문장

1. **Seaborn 은 matplotlib 위의 통계 그림 도구다** — 그림은 matplotlib `Axes` 에 그려지므로 제목 · 칸 배치 · 저장은 matplotlib 함수로 한다.
2. **꼴은 `data=표, x='열', y='열', hue='열'` 이다** — `hue` 하나로 범주별 색이 나뉜다.
3. **관계는 heatmap · pairplot, 분포는 boxplot · violinplot** — heatmap 은 수치 하나(상관계수)로 요약하고, pairplot 은 점 자체를 보여 준다.
4. **boxplot 은 사분위수와 이상치, violinplot 은 거기에 분포 모양(KDE)을 더한다.**
5. **`set_theme()` 은 한 번만** — 전체 스타일을 한꺼번에 정한다.

## 관련 자료

- [plotly-interactive](../12-plotly-interactive/2-summary.md)
- [scipy-stats](../01-scipy-stats/2-summary.md)
- `sklearn-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/data-science.json` 의 `seaborn-plots`

## 용어 풀이

- **Seaborn** — matplotlib 위에서 통계 그림을 그리는 Python 라이브러리.
- **matplotlib** — Python 의 기본 그림 라이브러리. `plt` 로 불러 쓴다.
- **DataFrame** — pandas 의 행 · 열로 된 표.
- **hue** — 범주별로 색을 나누는 파라미터.
- **팔레트** — 범주마다 돌려 쓰는 색 묶음.
- **컬러맵** — 연속된 숫자를 연속된 색으로 바꾸는 규칙.
- **상관계수** — 두 변수가 함께 움직이는 정도(-1 ~ 1).
- **상관 행렬** — 변수 쌍마다 상관계수를 담은 정사각 표.
- **EDA** — 데이터를 그려 보고 요약해 특징을 찾는 탐색 단계.
- **KDE** — 데이터로부터 분포를 매끈한 곡선으로 추정한 것.
- **사분위수** — 정렬한 값을 4등분하는 경계값 Q1 · Q2 · Q3.
- **IQR** — Q3 - Q1.
- **이상치** — 다른 값에서 동떨어진 값. boxplot 에서 수염 바깥 점.
- **단봉 · 다봉** — 분포 봉우리가 하나 · 여럿.
- **신뢰구간** — 추정값이 있을 법한 범위.
- **서브플롯** — 그림판을 나눈 칸 하나(`Axes`).
- **회귀선** — 산점도에 맞춘 추세 직선.

## 더 들어가면

- seaborn 함수는 크게 「한 `Axes` 에 그리는 함수」(`boxplot`, `heatmap` 등 — `ax=` 를 받는다)와 「그림판 전체를 직접 만드는 함수」(`pairplot`, `FacetGrid`, `catplot`, `lmplot`)로 나뉜다고 알려져 있다. 후자는 `ax=` 대신 자체 격자 객체를 돌려준다(확인 필요).
- 최근 버전에서는 `ci=95` 대신 `errorbar=('ci', 95)` 꼴을 쓴다(확인 필요).
- `sns.load_dataset` 은 데이터를 인터넷의 저장소에서 내려받아 캐시해 둔다고 알려져 있어, 네트워크가 없으면 실패할 수 있다(확인 필요).
- matplotlib 의 기본 글꼴에는 한글이 없어, `'상관관계 히트맵'` 같은 한글 제목이 네모로 깨질 수 있다. 한글 글꼴을 따로 지정해야 한다(확인 필요).
- `hue` 없이 `split=True` 를 주거나 hue 범주가 셋 이상일 때의 동작은 버전마다 다르다(확인 필요).
- KDE 곡선의 매끈함은 대역폭(bandwidth) 설정에 따라 달라지며, 데이터가 적으면 실제와 다른 봉우리가 보일 수 있다(확인 필요).
