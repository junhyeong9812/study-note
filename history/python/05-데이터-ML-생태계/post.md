# Python 데이터·ML 생태계의 부상

> 원본: `~/project/python-history/05-데이터-ML-생태계.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·인명·버전·수치·코드블록·표는 원문 그대로다.\
> ASCII 도식 8개(그중 3개는 원문 mermaid 그림을 글자로 옮긴 것)와 「한눈에」의 조립식 선반 비유, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 느린 인터프리터 언어였던 Python이 어떻게 데이터 분석과 머신러닝·딥러닝의 표준 언어가 되었는가 — 배열 라이브러리 하나에서 시작해 LLM 시대까지 이어진 30여 년의 계보

이 문서의 비유는 **나사 규격이 같은 조립식 선반** 하나뿐이다.\
「조종석 + 엔진」은 내 비유가 아니라 원문이 직접 쓴 표현이라 본문에서 그대로 쓴다.

| 비유 | 실체 |
|------|------|
| 나사 규격이 같아서 새로 산 칸이 기존 선반에 그냥 맞는다 | 거의 모든 데이터·ML 라이브러리가 **데이터를 주고받는 단위로 `ndarray`를 채택**했다 |
| 그래서 칸을 계속 위로 덧붙일 수 있다 | **한 라이브러리가 다음 라이브러리의 토대가 되는 누적 구조** |

똑같은 구조다 — 아래 칸이 정해 준 규격 덕분에 위 칸을 만드는 사람이 아래를 다시 만들 필요가 없다.

*(scikit-learn의 「어떤 모델이든 `fit()`·`predict()`로 통일돼 모델을 갈아 끼워도 코드 구조가 그대로다」는 이 선반 비유 **밖**의 별개 사실이다 — 라이브러리 층이 아니라 한 라이브러리 안의 인터페이스 이야기라서, 뒤의 scikit-learn 절에서 따로 다룬다.)*

원문이 타임라인 아래에 한 문장으로 적은 쌓임을 세로로 놓으면 이렇다.

```text
  LLM 시대(2023~)                   한 층을 더 얹었다
        ^
  딥러닝 프레임워크                  다시 그 위에 올라간다
        ^
  SciPy · pandas · scikit-learn      그 위에 쌓인다
        ^
  NumPy 배열(ndarray)                모든 길은 여기로 통한다
```

그림 해설 — 오른쪽 네 마디는 원문 문장 "모든 길은 NumPy 배열로 통하고, 그 위에 SciPy·pandas·scikit-learn이 쌓이며, 다시 그 위에 딥러닝 프레임워크가 올라간다"와, 마지막 절의 "LLM이라는 새 지층을 만나서도 무너지지 않고 한 층을 더 얹었다"에서 그대로 뽑았다.\
위로 향한 화살표 셋 가운데 **아래 둘**은 원문 한 문장에 두 번 나오는 "그 위에"에 대응하고, **맨 위 셋째**(딥러닝 → LLM 시대)는 마지막 절의 "한 층을 더 얹었다"에 대응한다 — 어느 쪽이든 아래가 토대이고 위가 그 위에 얹힌 것이다.

> **인터프리터 언어** — 소스를 미리 기계어로 통째로 번역해 두지 않고, 실행 시점에 인터프리터가 해석해 돌리는 언어.\
> 같은 시리즈 [06 §2.1](06-핵심-개념-진화.md)이 CPython을 두고 적는 대로, Python은 소스를 **바이트코드로 컴파일한 뒤 스택 기반 인터프리터가 실행**한다 — "한 줄씩 읽어 가며 돌린다"가 아니다.\
> 예: 원문이 "Python은 인터프리터 언어라 그 자체로는 느리다"라고 적는 이유가 이것이다.

## 한눈에 보는 타임라인

| 시기 | 사건 | 핵심 인물 / 주체 |
|------|------|------------------|
| 1995 | **Numeric** 등장 — Python 최초의 배열 라이브러리 | Jim Hugunin |
| 2001 | **SciPy** 출범 — 수치 연산 표준 모음 | Travis Oliphant, Eric Jones, Pearu Peterson |
| 2001 | **IPython** 시작 — 대화형 셸 ("논문 미루기 프로젝트") | Fernando Pérez |
| ~2001 | **Numarray** — Numeric의 대형 배열용 대체 구현 | STScI |
| 2003 | **matplotlib** — Python 표준 시각화 도구 | John Hunter |
| 2006 | **NumPy 1.0** — Numeric + Numarray 통합, 생태계의 주춧돌 | Travis Oliphant |
| 2007 | **scikit-learn** 시작 (Google Summer of Code) / **Theano** 첫 공개 | David Cournapeau / MILA(몬트리올대) |
| 2008 | **pandas** 개발 시작 (AQR Capital) | Wes McKinney |
| 2010 | **scikit-learn** 첫 공개 릴리스(v0.1, 2/1) | INRIA 팀 |
| 2011 | **IPython Notebook** — 브라우저 기반 노트북 | Pérez, Brian Granger |
| 2014 | **Project Jupyter** 분리 — 언어 중립 노트북으로 확장 | Jupyter 팀 |
| 2015 | **Keras**(3월) / **TensorFlow**(11월) | François Chollet / Google Brain |
| 2016 | **PyTorch** — define-by-run 동적 그래프 | Facebook AI Research |
| 2023~ | **LLM 시대** — Python이 AI 연구·응용의 사실상 공용어 | (생태계 전반) |

표는 원문 그대로다(14행).

이 계보의 핵심은 **한 라이브러리가 다음 라이브러리의 토대가 되는 누적 구조**다.\
모든 길은 NumPy 배열로 통하고, 그 위에 SciPy·pandas·scikit-learn이 쌓이며, 다시 그 위에 딥러닝 프레임워크가 올라간다.

```text
Numeric (1995)
Numarray (~2001)
      |
      v
NumPy (2006)                 <....모든 것을 묶는 작업대....  IPython (2001) → Jupyter (2014)
ndarray = 공통 데이터 구조                                   대화형 실행 환경
      |
      +--> SciPy (2001→)             수치 알고리즘
      +--> matplotlib (2003)         시각화
      +--> pandas (2008)             DataFrame
      +--> scikit-learn (2007/2010)  전통 ML
      +--> 딥러닝 프레임워크         Theano→TF→PyTorch
```

그림 해설 — 원문 mermaid 그림을 글자로 옮긴 것이다. 마디 여덟과 화살표 일곱의 문구·방향은 원문 그대로다.\
점선 화살표와 그 라벨 「모든 것을 묶는 작업대」도 원문의 것이고, 방향은 IPython·Jupyter 쪽에서 NumPy 쪽으로다.\
화살표는 바로 위 문단이 말한 **토대 관계**("그 위에 …이 쌓이며")이지 연도 순서가 아니다 — 원문 본문은 SciPy가 "NumPy보다 먼저 출범했고, 당시엔 Numeric 배열 위에서 동작했다"고 적는다.

## 1세대: 수치 배열의 탄생 — Numeric에서 NumPy까지

**무엇이 없었나** — Python은 1991년 출범 당시 과학 계산을 염두에 둔 언어가 아니었다.\
순수 Python의 리스트는 유연하지만, 거대한 수치 행렬을 다루기엔 너무 느리고 메모리도 낭비됐다.\
1995년 **Jim Hugunin**이 만든 **Numeric**이 이 공백을 메웠다 — C로 구현된 연속 메모리 배열에 벡터화 연산을 제공해, 루프 없이 배열 전체를 한 번에 계산하게 했다.

**무엇이 문제였나** — 2000년대 초, 우주망원경과학연구소(STScI)는 더 큰 배열과 유연한 자료형을 위해 **Numarray**라는 대체 구현을 내놓았다.\
Numarray는 대형 배열에서 빠른 대신 작은 배열에서는 느려서, 한동안 커뮤니티가 Numeric과 Numarray로 **갈라지는** 문제가 생겼다.\
같은 목적의 배열 라이브러리가 둘로 쪼개진 상황은 생태계 전체의 위협이었다.

**어떻게 끝냈나** — **Travis Oliphant**가 이 분열을 끝냈다.\
2005년 초부터 그는 Numarray의 장점을 Numeric에 이식해 하나로 합치는 작업에 착수했고, 그 결과를 **NumPy 1.0**(2006년 말)으로 발표했다.\
동시에 그는 ndarray 객체·브로드캐스팅 규칙·벡터화 연산을 망라한 『Guide to NumPy』를 펴내 사실상의 표준 레퍼런스를 만들었다.\
이로써 Python 수치 계산은 **단 하나의 배열 타입(`ndarray`)** 위에 다시 통일됐다.

```python
import numpy as np

# 순수 Python 리스트: 원소마다 루프 — 느리다
xs = [1, 2, 3, 4]
ys = [x * 2 + 1 for x in xs]

# NumPy ndarray: C 레벨 벡터화 — 루프 없이 배열 전체를 한 번에
a = np.array([1, 2, 3, 4])
b = a * 2 + 1                 # array([3, 5, 7, 9])

# 브로드캐스팅: 모양이 다른 배열을 규칙에 따라 자동 확장
M = np.arange(12).reshape(3, 4)   # 3×4 행렬
col_mean = M.mean(axis=0)         # 열별 평균 (길이 4 벡터)
centered = M - col_mean           # (3,4) - (4,) → 각 행에서 평균 차감
```

```text
[ 순수 Python 리스트 ]                 [ NumPy ndarray ]

원소마다 루프 — 느리다                 C 레벨 벡터화 — 루프 없이 배열 전체를 한 번에

ys = [x * 2 + 1 for x in xs]           b = a * 2 + 1        # array([3, 5, 7, 9])
```

그림 해설 — 두 칸의 문구는 위 코드블록의 주석 두 줄을 그대로 좌우로 놓은 것이고, 아랫줄은 그 주석이 각각 달린 코드 한 줄씩이다.\
같은 행에 놓인 것은 원문 코드가 같은 계산(`x * 2 + 1`)을 두 방식으로 적은 짝이다.

> **벡터화(vectorization)** — 원소마다 루프를 돌지 않고 배열 전체를 한 번에 계산하는 것.\
> 예: 위 코드의 `b = a * 2 + 1` — 같은 계산을 순수 Python 리스트로 하면 원소마다 루프를 돈다.

> **`ndarray`** — NumPy의 배열 타입. 원문이 Numeric의 기여로 든 "C로 구현된 연속 메모리 배열"이 그 뿌리다.\
> 예: 원문은 NumPy의 진짜 의의가 속도가 아니라 **공통 어휘**라고 적는다 — 뒤에 나오는 거의 모든 라이브러리가 이것으로 데이터를 주고받는다.

> **브로드캐스팅(broadcasting)** — 모양이 다른 배열을 규칙에 따라 자동 확장해 맞추는 것.\
> 예: 위 코드의 `centered = M - col_mean` — 주석 그대로 `(3,4) - (4,)`에서 각 행에서 평균이 차감된다.

NumPy의 진짜 의의는 속도가 아니라 **공통 어휘**다.\
이후 등장하는 거의 모든 데이터·ML 라이브러리가 데이터를 주고받는 단위로 `ndarray`를 채택하면서, NumPy는 생태계 전체가 서로 호환되게 만드는 **공통 기반**(lingua franca)이 되었다.

> **공통 기반(lingua franca)** — 서로 다른 것들이 말을 섞을 때 공통으로 쓰기로 한 하나의 언어.\
> 예: 원문 표현 그대로, 라이브러리들이 각자 자기 배열 타입을 쓰지 않고 `ndarray`로 주고받는 것.

## 과학 계산 스택의 완성 — SciPy와 matplotlib

**무엇이 더 필요했나** — 배열만으로는 부족하다.\
적분·최적화·선형대수·신호처리 같은 **알고리즘**과, 결과를 눈으로 보는 **시각화**가 필요하다.

**SciPy**가 알고리즘 층을 맡았다.\
2001년 Travis Oliphant, Eric Jones, Pearu Peterson이 각자 작성한 모듈을 합쳐 하나의 패키지로 묶은 것이 시작이다(NumPy보다 먼저 출범했고, 당시엔 Numeric 배열 위에서 동작했다).\
SciPy는 검증된 Fortran·C 수치 라이브러리(LAPACK, FFTPACK 등)를 Python에서 호출할 수 있게 감싸, "직접 구현하지 말고 빌려 쓰는" 과학 계산 문화를 정착시켰다.

**matplotlib**은 시각화를 맡았다.\
**John Hunter**가 2003년, 박사후연구원 시절 간질 환자의 뇌파(ECoG) 데이터를 그리려고 만든 도구다.\
MATLAB과 유사한 명령형 인터페이스(`pyplot`)를 제공해, MATLAB 사용자가 Python으로 넘어오는 다리가 되었다.\
matplotlib은 2004년 화성 탐사 로버 임무를 비롯한 수많은 과학 응용의 표준 도구로 자리 잡았다.

```python
import numpy as np
from scipy import optimize
import matplotlib.pyplot as plt

# SciPy: 비선형 함수의 근을 수치적으로 찾기
f = lambda x: x**3 - 2*x - 5
root = optimize.brentq(f, 2, 3)      # ≈ 2.0946

# matplotlib: MATLAB 스타일 명령형 플로팅
x = np.linspace(0, 10, 200)
plt.plot(x, np.sin(x), label="sin")
plt.axhline(0, color="gray", lw=0.5)
plt.legend(); plt.title("scientific Python stack")
```

> **감싼다(wrapping)** — 다른 언어로 된 라이브러리를 Python에서 부를 수 있게 겉을 덮어 주는 것.\
> 예: 원문이 든 대로 SciPy가 Fortran·C 수치 라이브러리(LAPACK, FFTPACK 등)를 Python에서 호출할 수 있게 감싼 것.

NumPy(데이터) + SciPy(알고리즘) + matplotlib(시각화)의 3종 세트는 흔히 "**과학 Python 스택(scientific Python stack)**"으로 불리며, 이후 모든 상위 라이브러리가 전제하는 토대가 되었다.

## 데이터 분석의 결정타 — pandas (2008)

**무엇이 문제였나** — 과학 스택은 균질한 수치 배열에는 강했지만, 현실의 데이터는 그렇지 않다.\
날짜·문자열·결측치(NaN)가 섞인 **표 형태(tabular)** 데이터, 즉 데이터베이스나 엑셀에서 나오는 데이터를 다루기엔 불편했다.

```text
[ 과학 스택이 강했던 것 ]              [ 현실의 데이터 ]

균질한 수치 배열                       날짜·문자열·결측치(NaN)가 섞인
                                       표 형태(tabular) 데이터
                                       = 데이터베이스나 엑셀에서 나오는 데이터
```

그림 해설 — 두 칸은 원문의 한 문장("과학 스택은 균질한 수치 배열에는 강했지만, 현실의 데이터는 그렇지 않다")을 좌우로 나눠 놓은 것이고, 오른쪽 세 줄은 바로 뒤 문장이 "현실의 데이터"로 든 것들이다.

**누가 풀었나** — **Wes McKinney**가 이 문제를 풀었다.\
그는 2007~2010년 헤지펀드 **AQR Capital Management**에서 글로벌 매크로·크레딧 전략을 연구하며, 금융 시계열 데이터를 다루려고 2008년부터 **pandas**를 만들기 시작했다.\
핵심 발명은 **`DataFrame`** — 행과 열에 **라벨**(label)이 붙은 2차원 표 구조로, NumPy 배열 위에 인덱스·정렬·결측치 처리·그룹 연산을 얹은 것이다.\
McKinney는 약 6개월간 상사를 설득한 끝에 2009년 말 pandas를 오픈소스로 공개했다.

```python
import pandas as pd

df = pd.DataFrame({
    "city":  ["Seoul", "Seoul", "Busan", "Busan"],
    "year":  [2023, 2024, 2023, 2024],
    "sales": [100, 130, 80, None],          # 결측치(NaN)
})

# 라벨 기반 인덱싱 + 결측치 처리 + 그룹 집계가 한 줄로
df["sales"] = df["sales"].fillna(df["sales"].mean())
by_city = df.groupby("city")["sales"].sum()     # 도시별 합계

# 시계열·조인·피벗 등 DB/엑셀 작업을 Python 안에서
pivot = df.pivot_table(index="city", columns="year", values="sales")
```

> **`DataFrame`** — 행과 열에 라벨이 붙은 2차원 표 구조.\
> 예: 원문 그대로 **NumPy 배열 위에** 인덱스·정렬·결측치 처리·그룹 연산을 얹은 것이다 — 원문이 「누적 구조」라 부른 쌓임의 한 층이다.

> **결측치(NaN)** — 값이 비어 있는 자리.\
> 예: 위 코드 `"sales": [100, 130, 80, None]`의 `None` — 원문 코드는 이것을 평균으로 채운다(`fillna`).

pandas는 금융을 넘어 모든 분야의 데이터 분석가·과학자에게 폭발적으로 퍼졌다.\
데이터 정제(cleaning)·변환·탐색(EDA)이라는, ML 파이프라인의 가장 앞단이자 시간이 가장 많이 드는 작업을 Python 안에서 끝낼 수 있게 한 것이 결정적이었다.\
pandas는 종종 "**데이터 과학에서 가장 중요한 도구**"로 불린다.

## 머신러닝의 대중화 — scikit-learn (2007 / 2010)

**무엇을 표준화했나** — 데이터를 준비했으면 모델을 학습시킬 차례다.\
**scikit-learn**은 전통적 머신러닝(분류·회귀·클러스터링·차원축소)을 누구나 쓸 수 있게 표준화했다.

시작은 2007년 **David Cournapeau**의 Google Summer of Code 프로젝트였다.\
이후 2010년 2월 1일, 프랑스 국립연구소 **INRIA**의 Fabian Pedregosa·Gaël Varoquaux·Alexandre Gramfort·Vincent Michel이 주도해 첫 공개 릴리스(v0.1)를 냈다.\
scikit-learn의 위대함은 알고리즘 자체가 아니라 **일관된 API 설계**에 있다 — 어떤 모델이든 `fit()`으로 학습하고 `predict()`로 예측하는 동일한 인터페이스를 따른다.\
모델을 갈아 끼워도 코드 구조가 그대로다.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# 어떤 추정기든 fit/predict 동일 인터페이스 — 모델 교체가 한 줄
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)               # 학습
pred = model.predict(X_test)              # 예측
print(accuracy_score(y_test, pred))
```

> **추정기(estimator) 규약** — 어떤 모델이든 `fit()`으로 학습하고 `predict()`로 예측하는 동일한 인터페이스.\
> 예: 위 코드 주석 그대로 "어떤 추정기든 fit/predict 동일 인터페이스 — 모델 교체가 한 줄"이다.

`fit`/`predict`/`transform`으로 통일된 이 추정기(estimator) 규약 덕분에, 전처리→모델→평가를 `Pipeline`으로 조립하고 `GridSearchCV`로 하이퍼파라미터를 탐색하는 일이 표준 워크플로가 됐다.\
scikit-learn은 NumPy 배열을 입출력으로 쓰므로 과학 스택과 매끄럽게 맞물린다 — 누적 구조의 또 한 층이다.

## 대화형 컴퓨팅 — IPython에서 Jupyter로

**무엇을 매끄럽게 했나** — 데이터 작업은 본질적으로 **탐색적**이다.\
코드를 짜고, 결과를 보고, 다시 고치는 짧은 순환을 수없이 반복한다.\
이 순환을 매끄럽게 만든 것이 **IPython → Jupyter** 계보다.

```text
데이터 작업의 짧은 순환

   +--> 코드를 짜고
   |        |
   |        v
   |    결과를 보고
   |        |
   |        v
   |    다시 고치고
   |        |
   +--------+      이 순환을 수없이 반복한다
```

그림 해설 — 세 칸과 되돌아가는 화살표는 원문 문장 "코드를 짜고, 결과를 보고, 다시 고치는 짧은 순환을 수없이 반복한다"를 그대로 옮긴 것이다.\
원문이 **순환**이라 부른 것이라 마지막에서 처음으로 되돌아가는 선을 넣었다.

**Fernando Pérez**가 2001년, 입자물리 박사과정 중 "논문 미루기 프로젝트"로 시작한 **IPython**은 향상된 대화형 셸이었다.\
2011년 Pérez와 **Brian Granger**가 브라우저 기반의 **IPython Notebook**을 내놓으면서, 코드·실행 결과·그래프·설명(Markdown)을 한 문서에 엮는 **노트북** 형식이 탄생했다.\
2014년에는 이 노트북 부분을 분리해 **Project Jupyter**를 출범시켰다 — 이름 **Ju**lia·**Py**thon·**R**에서 보듯, Python을 넘어 여러 언어로 확장한다는 선언이었다(IPython은 Jupyter의 대표 커널로 남았다).

```text
[ Markdown 셀 ]  # 분석 목적 설명
[ 코드 셀     ]  df.groupby("city").sales.sum()
[ 출력 셀     ]  Busan  160 / Seoul  230   ← 즉시 표로 렌더링
[ 코드 셀     ]  plt.plot(...)             ← 그래프가 문서에 인라인
```

> **노트북(notebook)** — 코드·실행 결과·그래프·설명(Markdown)을 한 문서에 엮는 형식.\
> 예: 바로 위 그림의 네 줄 — 코드 셀 바로 아래에 그 실행 결과가 붙는다.

노트북은 데이터 분석·교육·연구 논문 재현의 사실상 표준 매체가 되었다.\
"코드를 짜며 동시에 이야기를 서술한다"는 형식이 데이터 과학의 작업 방식 자체를 규정했고, 이후 Google Colab 같은 클라우드 노트북으로 이어진다.

## 딥러닝의 폭발 — Theano에서 PyTorch까지

**무엇이 필요해졌나** — 2012년 AlexNet의 ImageNet 우승 이후 딥러닝이 폭발하면서, 신경망을 표현하고 **자동 미분**(autograd)으로 학습시키는 전용 프레임워크가 필요해졌다.\
이 영역에서도 Python이 표준 인터페이스가 되었다.

| 프레임워크 | 시기 | 주체 | 특징 |
|------------|------|------|------|
| **Torch** | 2002 | (Lua 기반) | PyTorch의 조상. 스크립팅 언어로 유연성 확보 |
| **Theano** | 2007 첫 공개 | MILA(몬트리올대) | 자동 미분·GPU·계산 그래프 최적화의 선구자 |
| **TensorFlow** | 2015-11 | Google Brain | Theano 아이디어 + 대규모 분산 학습. define-and-run |
| **PyTorch** | 2016 | Facebook AI Research | Torch+NumPy 계승. **define-by-run** 동적 그래프 |

표는 원문 그대로다(4행).

**Theano**(2007, 몬트리올대 MILA — Yoshua Bengio 그룹)가 길을 열었다.\
수식을 **계산 그래프**로 표현해 자동 미분하고 GPU로 컴파일하는 방식을 개척했다.\
**Keras**(2015, **François Chollet**)는 Theano를 백엔드로 한 고수준 API로 출발해 신경망 작성을 극적으로 쉽게 만들었다.\
Theano 자신은 후대 프레임워크에 밀려 2017년 개발을 종료했지만, 그 설계 사상은 후속작에 그대로 흡수됐다.

**TensorFlow**(2015, Google Brain)는 Theano의 그래프 아이디어에 대규모 분산 학습을 더해 산업 표준이 되었다.

**무엇이 까다로웠나** — 다만 초기 TF는 그래프를 **먼저 정의하고 나중에 실행**하는(define-and-run) 정적 방식이라 디버깅이 까다로웠다.

**PyTorch**(2016, Facebook AI Research)는 Torch의 유연함과 NumPy의 친숙함을 Python으로 가져오면서, **실행하면서 그래프를 그리는**(define-by-run) 동적 방식을 택했다.\
일반 Python 코드처럼 디버깅되는 직관성 덕분에 연구 커뮤니티가 빠르게 PyTorch로 이동했고, TensorFlow도 2.0에서 즉시 실행(eager)을 기본화하며 뒤따랐다.

```text
[ define-and-run (초기 TensorFlow) ]     [ define-by-run (PyTorch) ]

그래프를 먼저 정의하고 나중에 실행       실행하면서 그래프를 그린다

디버깅이 까다로웠다                      일반 Python 코드처럼 디버깅되는 직관성
```

그림 해설 — 같은 행에 놓인 두 줄은 원문이 두 프레임워크에 대해 나란히 적은 짝이다.\
윗행은 원문의 괄호 표기 그대로이고, 아랫행은 원문이 각각에 붙인 디버깅 평가다.

```python
import torch

# define-by-run: 연산을 실행하는 즉시 그래프가 그려지고 미분 추적
x = torch.tensor([2.0], requires_grad=True)
y = x**3 - 2*x - 5            # 일반 파이썬 식처럼 작성
y.backward()                 # 자동 미분
print(x.grad)                # dy/dx = 3x^2 - 2 = 10.0
```

> **자동 미분(autograd)** — 식을 미분한 값을 사람이 손으로 구하지 않고 프로그램이 대신 계산해 주는 것.\
> 예: 위 코드의 `y.backward()` 다음 `x.grad` — 주석 그대로 `dy/dx = 3x^2 - 2 = 10.0`이다.

> **계산 그래프** — 수식을 연산 마디와 그 연결로 표현해 둔 것.\
> 예: 원문이 Theano가 개척했다고 적은 방식 — 수식을 이렇게 표현해 두고 자동 미분하고 GPU로 컴파일한다.

> **define-and-run / define-by-run** — 그래프를 먼저 정의하고 나중에 실행 / 실행하면서 그래프를 그림.\
> 예: 위 코드 주석 그대로 PyTorch는 "연산을 실행하는 즉시 그래프가 그려지고 미분 추적"된다.

```text
Torch (2002)             ──>  PyTorch (2016)
Lua, 동적                     define-by-run
                                  ^
NumPy ndarray  ....텐서 인터페이스의 원형....┘


Theano (2007)            ──>  TensorFlow (2015)
그래프 자동미분                define-and-run
      |                           ^
      v                           |
Keras (2015)             ─────────┘
고수준 API
```

그림 해설 — 원문 mermaid 그림을 글자로 옮긴 것이다. 마디 여섯과 화살표 다섯의 문구·방향은 원문 그대로다.\
점선 화살표와 그 라벨 「텐서 인터페이스의 원형」도 원문의 것이고, 방향은 NumPy ndarray 쪽에서 PyTorch 쪽으로다.\
위 묶음과 아래 묶음 사이에 원문은 화살표를 두지 않았다 — 그래서 여기서도 잇지 않았다.

여기서 주목할 점은, 이 모든 프레임워크의 무거운 연산은 **C++/CUDA로 구현된 커널**이고 Python은 그 위에 얹힌 **얇은 조종석**(front-end)이라는 사실이다.\
이것이 다음 절의 핵심 주제다.

## 왜 Python이 데이터·ML의 표준 언어가 됐나

**무엇이 역설인가** — Python은 인터프리터 언어라 그 자체로는 느리다.\
그런데도 성능이 생명인 수치·ML 분야의 표준이 된 것은 역설처럼 보인다.\
답은 세 가지가 맞물린 데 있다.

**① C 확장 — "느린 언어 위의 빠른 라이브러리".**\
Python은 C로 작성한 확장 모듈을 자연스럽게 호출하도록 설계됐다.\
NumPy·SciPy·pandas·딥러닝 프레임워크의 무거운 계산은 전부 C·C++·Fortran·CUDA로 구현돼 있고, Python은 그 빠른 커널을 호출하는 **얇은 제어층**만 담당한다.\
사용자는 느린 Python 루프를 거의 쓰지 않고, 벡터화된 한 줄이 컴파일된 네이티브 코드로 실행된다.

**② 글루(glue) 언어 — 이질적 시스템을 잇는 접착제.**\
Python은 파일·DB·웹 API·메시지 큐·다른 언어의 라이브러리를 손쉽게 엮는다.\
데이터 수집→정제→학습→배포로 이어지는 ML 파이프라인은 본질적으로 이질적인 조각들의 조립인데, Python은 이 조각들을 붙이는 접착제로 탁월하다.

**③ 가독성 — 수학자·과학자가 코드를 읽고 쓴다.**\
ML의 주 사용자는 소프트웨어 엔지니어가 아니라 연구자·분석가다.\
Python의 간결하고 영어에 가까운 문법은 알고리즘을 의사코드처럼 표현하게 해, 비전공자의 진입 장벽을 극적으로 낮췄다.\
대학의 데이터·ML 강의 대부분이 Python을 첫 언어로 가르치면서 이 우위는 자기강화됐다.

```text
+--------------------------------------------------+
| Python 층 — 얇고 읽기 쉬운 조종석                |
|   연구자/분석가가 작성                           |
|   벡터화 1줄 · 파이프라인 조립                   |
+--------------------------------------------------+
      |                                  ^
      | 얇은 바인딩 호출                 | ndarray / tensor 반환
      v                                  |
+--------------------------------------------------+
| 네이티브 층 — 무겁고 빠른 엔진                   |
|   C / C++ / Fortran / CUDA                       |
|   BLAS·LAPACK·cuDNN 커널                         |
+--------------------------------------------------+
```

그림 해설 — 원문 mermaid 그림을 글자로 옮긴 것이다. 두 상자의 제목·내용과 화살표 둘의 라벨·방향은 원문 그대로다.\
위에서 아래로 가는 화살표가 호출이고, 아래에서 위로 오는 화살표가 그 결과의 반환이다.

> **C 확장** — C로 작성해 컴파일해 둔, Python에서 불러 쓸 수 있는 모듈.\
> 예: 원문이 든 대로 NumPy·SciPy·pandas·딥러닝 프레임워크의 무거운 계산이 전부 이 방식이다.

> **글루(glue) 언어** — 이질적 시스템을 잇는 접착제 역할을 하는 언어.\
> 예: 원문이 든 대로 파일·DB·웹 API·메시지 큐·다른 언어의 라이브러리를 손쉽게 엮는 것.

세 요인은 **누적된 생태계**라는 네 번째 요인으로 굳어졌다.\
NumPy 배열이라는 공통 데이터 구조 위에 SciPy·pandas·scikit-learn·딥러닝 프레임워크가 한 층씩 쌓이며 서로 호환됐고, 한번 임계 질량을 넘자 "여기에 다 있으니 여기서 만든다"는 선순환이 다른 언어의 추격을 불가능하게 만들었다.

## 2023~ LLM 시대, Python의 위치

대규모 언어 모델(LLM) 시대에도 Python의 지배력은 오히려 강화됐다.

- **연구·학습의 공용어.**\
  GPT·Llama·Mistral 등 거의 모든 기반 모델이 **PyTorch**(일부 JAX)로 학습된다.\
  트랜스포머 구현, 분산 학습(DeepSpeed·Megatron), 미세조정(PEFT·LoRA)의 표준 도구가 모두 Python 라이브러리다.\
  Hugging Face `transformers`가 사실상의 모델 허브이자 공통 인터페이스로 자리 잡았다.
- **응용 개발의 접착제.**\
  RAG·에이전트·툴 호출을 엮는 LangChain·LlamaIndex 같은 오케스트레이션 프레임워크의 주력 언어가 Python이다.\
  모델 API 호출, 벡터 DB 연결, 도구 정의를 잇는 **글루 역할**이 여기서도 그대로 발휘된다.
- **2층 구조의 재현.**\
  추론 성능이 중요한 부분(어텐션 커널, 양자화, 서빙 엔진 vLLM 등)은 C++/CUDA로 내려가고, 그 위를 Python이 얇게 감싼다.\
  20년 전 NumPy가 확립한 "느린 조종석 + 빠른 엔진" 패턴이 LLM 인프라에서 똑같이 반복된다.

요컨대 Numeric에서 시작해 NumPy로 통일되고 pandas·scikit-learn·PyTorch로 쌓여 올라간 생태계는, LLM이라는 새 지층을 만나서도 무너지지 않고 한 층을 더 얹었다.\
**데이터에서 시작해 ML을 거쳐 AI까지, Python은 30년에 걸쳐 한 번도 표준의 자리를 내준 적이 없다.**

## 용어 풀이

- **인터프리터 언어** — 소스를 미리 기계어로 통째로 번역해 두지 않고, 실행 시점에 인터프리터가 해석해 돌리는 언어(CPython은 바이트코드로 컴파일한 뒤 인터프리터가 실행한다 — 06 §2.1).
- **벡터화(vectorization)** — 원소마다 루프를 돌지 않고 배열 전체를 한 번에 계산하는 것.
- **`ndarray`** — NumPy의 배열 타입. "C로 구현된 연속 메모리 배열"이 그 뿌리다.
- **브로드캐스팅(broadcasting)** — 모양이 다른 배열을 규칙에 따라 자동 확장해 맞추는 것.
- **공통 기반(lingua franca)** — 서로 다른 것들이 주고받을 때 공통으로 쓰기로 한 하나의 형식.
- **감싼다(wrapping)** — 다른 언어로 된 라이브러리를 Python에서 부를 수 있게 겉을 덮어 주는 것.
- **과학 Python 스택** — NumPy(데이터) + SciPy(알고리즘) + matplotlib(시각화)의 3종 세트.
- **`DataFrame`** — 행과 열에 라벨이 붙은 2차원 표 구조. NumPy 배열 위에 얹혀 있다.
- **결측치(NaN)** — 값이 비어 있는 자리.
- **추정기(estimator) 규약** — 어떤 모델이든 `fit()`으로 학습하고 `predict()`로 예측하는 동일한 인터페이스.
- **노트북(notebook)** — 코드·실행 결과·그래프·설명(Markdown)을 한 문서에 엮는 형식.
- **자동 미분(autograd)** — 식을 미분한 값을 프로그램이 대신 계산해 주는 것.
- **계산 그래프** — 수식을 연산 마디와 그 연결로 표현해 둔 것.
- **define-and-run / define-by-run** — 그래프를 먼저 정의하고 나중에 실행 / 실행하면서 그래프를 그림.
- **C 확장** — C로 작성해 컴파일해 둔, Python에서 불러 쓸 수 있는 모듈.
- **글루(glue) 언어** — 이질적 시스템을 잇는 접착제 역할을 하는 언어.

## 참고 출처

- [NumPy — Wikipedia](https://en.wikipedia.org/wiki/NumPy)
- [Travis Oliphant — Wikipedia](https://en.wikipedia.org/wiki/Travis_Oliphant)
- [Guide to NumPy (Travis E. Oliphant, 2006)](https://web.mit.edu/dvp/Public/numpybook.pdf)
- [SciPy — Wikipedia](https://en.wikipedia.org/wiki/SciPy)
- [History of SciPy (SciPy wiki)](https://scipy.github.io/old-wiki/pages/History_of_SciPy)
- [John D. Hunter — Wikipedia](https://en.wikipedia.org/wiki/John_D._Hunter)
- [History — Matplotlib documentation](https://matplotlib.org/stable/project/history.html)
- [Wes McKinney — Wikipedia](https://en.wikipedia.org/wiki/Wes_McKinney)
- [pandas (software) — Wikipedia](https://en.wikipedia.org/wiki/Pandas_(software))
- [pandas — About](https://pandas.pydata.org/about/)
- [scikit-learn — Wikipedia](https://en.wikipedia.org/wiki/Scikit-learn)
- [About us — scikit-learn documentation](https://scikit-learn.org/stable/about.html)
- [IPython — Wikipedia](https://en.wikipedia.org/wiki/IPython)
- [Project Jupyter — Wikipedia](https://en.wikipedia.org/wiki/Project_Jupyter)
- [Fernando Pérez — Wikipedia](https://en.wikipedia.org/wiki/Fernando_P%C3%A9rez_(software_developer))
- [Theano (software) — Wikipedia](https://en.wikipedia.org/wiki/Theano_(software))
- [François Chollet — Wikipedia](https://en.wikipedia.org/wiki/Fran%C3%A7ois_Chollet)
- [A Brief History of Deep Learning Frameworks (Towards Data Science)](https://towardsdatascience.com/a-brief-history-of-deep-learning-frameworks-8debf3ba6607/)
- [Why is Python such a popular choice in data science and ML? (Institute of Data)](https://www.institutedata.com/blog/why-is-python-programming-such-a-popular-choice-in-data-science-and-machine-learning/)
