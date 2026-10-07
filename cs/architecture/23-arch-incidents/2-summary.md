# architecture/23-arch-incidents — 실사건: Patriot 시계 오차 누적(1991) · Ariane 5 64→16비트 변환(1996) · Intel FDIV(1994) · Spectre/Meltdown(2018) · 2038년 문제 — 컴퓨터 구조 관점 — 정리 (힌트)

## 해결하는 문제

다섯 사건은 모두 **표현이나 하드웨어의 한계가 오래 숨어 있다가** 조건이 바뀌자 드러난 경우다.

```text
  Patriot 1991       0.1초 틱을 24비트 레지스터의 실수로 ── 100시간 연속 가동 ─────▶ 시각 오차 0.3433초 → 추적 창이 687 m 밀림 → 요격 실패
  Ariane 5 1996      64비트 실수 → 16비트 정수 변환 ──────── Ariane 5의 큰 수평 속도 ─▶ Operand Error → 관성 장치 2대 정지 → 39초에 분해
  Intel FDIV 1994    나눗셈 조회표의 빈 칸 5개 ──────────────── 드문 제수 비트 패턴 ─────▶ 몫이 틀림(최악: 소수점 아래 12번째 비트 — 백서는 "4th significant decimal digit")
  Spectre/Meltdown   투기·비순차 실행이 캐시에 남긴 흔적 ─────── 공격자가 고른 코드 ───────▶ 권한 밖 메모리를 시간 측정으로 읽음
  2038년 문제         부호 있는 32비트 초 카운터 ─────────────── 2038-01-19 03:14:08 UTC ──▶ 표현 불가(감기면 1901-12-13, 인터페이스에 따라 EOVERFLOW)
```

쉬운 예: 다 쓴 달력이다.\
1년짜리 탁상 달력은 12월 31일까지는 완벽하다. 다음 날 아침 달력에는 넘길 장이 없다.\
달력이 틀린 것이 아니라 **칸 수**가 정해져 있었다.

똑같은 구조다.\
24비트 레지스터, 16비트 정수, 32비트 초는 각자 칸 수가 정해진 달력이다. 투기 실행도 "설계 때 가정한 위협" 안에서는 옳다.\
가정 밖 입력(오래 켜 둠, 더 빠른 로켓, 공격자 코드, 미래 날짜)이 오면 무너진다. FDIV는 다르다 — 정상 입력에서도 처음부터 틀렸고, 드문 비트 패턴에서만 드러나 숨어 있었다.

실무 예:
- 오래 켜 두는 서버·장비의 경과 시간 카운터, 다른 제품에서 재사용한 모듈의 범위 가정, 4바이트 시각 필드를 가진 프로토콜·DB 컬럼이 백엔드에서 같은 모양이다.
- 하드웨어 결함은 코드 리뷰로 보이지 않는다. 대신 "결과 검증", "완화 상태 확인"이 운영 절차가 된다. 부채널은 원인이 하드웨어지만, Spectre 변형 1의 위험 경로(검사 뒤 투기 접근)처럼 코드 패턴이라 코드 검토·수정의 대상이 되는 부분도 있다(커널 hw-vuln/spectre — `nospec` 접근자).

  - *1차 출처*: 당사자나 조사 기관이 직접 쓴 문서 — GAO 보고서, 조사위원회 보고서, Intel 백서, 발견자의 글, 논문, 커널·glibc 문서. 이 노트는 날짜·수치를 원문 그대로 옮기고, 원문에 없는 연결은 "해석"이라고 표시한다.
  - *증상 → 사건*: 이 노트의 사건은 [22-arch-symptom-index](../22-arch-symptom-index/2-summary.md)의 증상(2절 숫자, 3절 합계, 9절 간헐)이 실제 사고가 된 모습이다.

## 동작·원리

### 사건 1 — Patriot 미사일 방어: 시계 오차 누적 (1991-02-25 · GAO 보고서 1992-02-04)

출처
- GAO, "Patriot Missile Defense: Software Problem Led to System Failure at Dhahran, Saudi Arabia", GAO/IMTEC-92-26, 1992-02-04. <https://www.gao.gov/products/imtec-92-26> — 2026-10-07에 gao.gov는 접근 거부(403)라 Internet Archive 사본 PDF로 읽었다 <https://web.archive.org/web/20241207021820/https://www.gao.gov/assets/imtec-92-26.pdf>(스캔본, 20쪽).

#### 사실 (원문)

- 1991-02-25, 사우디아라비아 다란의 Patriot 포대가 날아오는 Scud를 추적·요격하지 못했다. Scud는 육군 막사에 떨어져 미국인 28명이 숨졌다.
- 원인은 무기 통제 컴퓨터의 소프트웨어 문제로, "an inaccurate tracking calculation that became worse the longer the system operated". 사고 당시 포대는 100시간 넘게 연속 가동 중이었다.
- 시간은 내부 시계가 **10분의 1초 단위의 정수**로 센다. 예측에는 시간을 실수로 바꿔야 하는데, 레지스터가 24비트라 "the conversion of time from an integer to a real number cannot be any more precise than 24 bits". 오차가 추적 창(range gate)에 주는 영향은 표적 속도와 가동 시간에 비례한다.
- 1991-02-11, 이스라엘 자료가 8시간 연속 가동 뒤 추적 창이 20% 밀린 것을 보였다. Patriot 사업단은 50% 이상 밀리면 Scud를 추적하지 못한다고 했고, 이를 외삽해 약 20시간 연속 가동이면 50%가 된다고 봤다.
- 재부팅(약 60~90초)이 시계를 0으로 되돌려 밀림을 없앤다. 보정 소프트웨어는 1991-02-16에 배포됐지만 다란에는 사고 다음 날인 02-26에 도착했다.
- 원래 설계는 유럽에서 항공기·순항미사일을 상대로, 한 위치에서 몇 시간만 운용하는 것이었다.
- 부록 II 표(원문 그대로)

```text
  Hours   Seconds   Calculated Time (s)   Inaccuracy (s)   Approximate Shift In Range Gate (m)
    0          0              0                  0                  0
    1       3600        3599.9966              .0034                  7
    8      28800       28799.9725              .0275                 55
   20ᵃ     72000       71999.9313              .0687                137
   48     172800      172799.8352              .1648                330
   72     259200      259199.7528              .2472                494
  100ᵇ    360000      359999.6667              .3433                687
  ᵃ Continuous operation exceeding about 20 hours—target outside range gate
  ᵇ Alpha Battery ran continuously for about 100 hours
```

- 해석(계산): 100시간 행의 360000 − 359999.6667 = 0.3333으로, 같은 행의 오차 칸 .3433과 0.01초 어긋난다. 다른 행은 두 칸이 서로 맞는다. 오차 칸은 시간에 정확히 비례하므로(1시간 .0034 × 100 ≈ .34) 계산 시간 칸의 표기 오류로 보인다. 이 노트는 오차 칸(.3433)을 쓴다.

#### 원리 — 0.1은 2진으로 끝나지 않는다

```text
  0.1 (10진) = 0.000110011001100110011001100110011... (2진, 0011 반복)

  소수점 아래 23비트에서 버림(chop):
  0.00011001100110011001100 | 1100110011...   ← 이 꼬리를 버림
                            버린 값 ≈ 0.000000095 (9.5 × 10⁻⁸)

  시각 = 틱 수 × (버린 0.1)
       = 틱 수 × 0.1  −  틱 수 × 9.5 × 10⁻⁸
                         └── 틱이 쌓일수록 선형으로 커지는 오차
```

- 0.1 상수 하나의 절단 오차는 작다. 그런데 그 오차가 **늘 같은 방향**(작은 쪽)이고 틱 수와 곱해지므로, 상쇄되지 않고 가동 시간에 비례해 커진다.
- 이 표현 문제의 바탕은 [03-floating-point-ieee754](../03-floating-point-ieee754/2-summary.md)(10진 소수의 2진 표현)와 같다. 차이는 Patriot이 24비트 고정 소수점 레지스터였다는 점이다(GAO 원문은 "24 bits"까지만 적는다. "24 bit fixed point register"는 D. Arnold의 정리 <https://www-users.cse.umn.edu/~arnold/disasters/patriot.html> — 2차 출처).
  - *고정 소수점*: 소수점 위치를 비트 몇 번째로 미리 정해 두고 정수처럼 계산하는 표현. 지수가 없어 범위는 좁지만 연산이 단순하다.

#### 실험 A: 23비트 절단으로 GAO 부록 II 재현 (`patriot.py`)

GAO는 24비트 레지스터라고만 적고, 0.1을 몇 비트에서 어떻게 잘랐는지는 적지 않는다. 소수부 비트 수 k를 바꿔 가며 정확한 유리수 연산(`fractions.Fraction`)으로 오차를 계산해 표와 비교했다.

```python
from fractions import Fraction as F
def chopped_tenth(k):            # 0.1을 소수부 k비트에서 버림(chop)
    return F(int(F(1,10) * 2**k), 2**k)
for k in (23, 24):
    e = F(1,10) - chopped_tenth(k)
    for h in (1, 8, 20, 48, 72, 100):
        print(h, float(e * h * 3600 * 10))
```

(실험, Python 3 표준 라이브러리, 호스트 Ubuntu 24.04, 2026-10-07 — 결정적 계산)

```text
k=23: 0.1 저장값 = 0.099999904633  틱당 오차 = 9.5367e-08 s
     1 h  ticks=   36,000  오차=0.0034 s   (GAO 0.0034)
     8 h  ticks=  288,000  오차=0.0275 s   (GAO 0.0275)
    20 h  ticks=  720,000  오차=0.0687 s   (GAO 0.0687)
    48 h  ticks=1,728,000  오차=0.1648 s   (GAO 0.1648)
    72 h  ticks=2,592,000  오차=0.2472 s   (GAO 0.2472)
   100 h  ticks=3,600,000  오차=0.3433 s   (GAO 0.3433)
k=24: 0.1 저장값 = 0.099999964237  틱당 오차 = 3.5763e-08 s
     1 h  ticks=   36,000  오차=0.0013 s   (GAO 0.0034)
   100 h  ticks=3,600,000  오차=0.1287 s   (GAO 0.3433)
687 m / 0.3433 s = 2001 m/s ;  Mach 5 = 3750 mph = 1676 m/s
```

- 관찰: 소수점 아래 23비트에서 버린 0.1이 GAO 오차 칸 여섯 행을 소수 넷째 자리까지 모두 재현했다. 24비트에서 버리면 맞지 않았다.
- 해석: 24비트 레지스터 중 1비트가 다른 용도(부호 등)였다면 소수부 23비트가 된다. 원문은 이 배치를 밝히지 않으므로 이것은 수치가 맞는다는 데서 나온 추정이다.
- 해석(계산): 687 m / 0.3433 s ≈ 2,001 m/s다. GAO가 본문에 적은 Scud 속도 "approximately MACH 5 (3750 mph)"(≈ 1,676 m/s)와 다르다. GAO는 밀림 계산에 쓴 속도를 밝히지 않는다.

같은 100시간을 다른 표현으로 세면(`patriot2.py`, 같은 환경):

```text
double 곱셈   ticks*0.1      = 360000.0
double 누적   0.1을 3,600,000번 더함 = 359999.999987987  (차 -1.201e-05 s)
float32 누적  0.1을 3,600,000번 더함 = 347024.78125  (차 -12975.2 s)
정수 틱       ticks // 10    = 360000 s (오차 0)
```

- 관찰: binary64 곱셈 한 번은 이 경우 정확한 360000.0으로 반올림됐다. 같은 일을 덧셈 누적으로 하면 double도 1.2 × 10⁻⁵초 틀렸다. float32 누적은 약 3.6시간(12,975초) 틀렸다. 누적값이 커지면 binary32의 간격(ulp)이 0.1에 비해 무시할 수 없을 만큼 커진다(최종값 347024.78 근처에서 0.03125 — 계산). 그러면 매 덧셈의 반올림 오차(최대 반 ulp)가 0.1의 수 %에 이르고, 같은 크기 구간에서는 같은 방향으로 반복돼 쌓인다(해석 — [math/15](../../math/15-numerical-stability/2-summary.md)의 큰 수 + 작은 수와 같은 꼴). Patriot의 메커니즘(곱셈 쪽 상수 절단)과는 다른 오차지만, "시각을 실수로 쌓지 말라"는 교훈은 같다.
- 정수 틱을 그대로 두고 필요한 순간에만 나누면 오차가 없다.

#### 막았을 장치 (해석)

- 표현: 경과 시간을 정수 틱으로 유지하고 차(Δ틱)만 실수로 바꾼다. 또는 단위 자체를 정수로 센다(정수 0.1초 틱·정수 밀리초). 2진으로 끝나는 틱(1/1024초 등)을 쓰려면 0.1초가 102.4틱이라 시계 간격 자체를 바꿔야 한다.
- 운용: 원문이 적은 대로 재부팅이 오차를 지운다. 연속 가동 한도를 명시한 지침이 필요했다. 원문은 02-21 메시지가 "very long run times"가 얼마인지 밝히지 않았다고 적는다.
- 시험: 원문은 사고 뒤 연속 가동 시험(endurance test)을 했다고 적는다. 설계 가정(몇 시간 운용) 밖의 가동 시간을 시험에 넣는 것이 핵심이다.
- leaf: [03](../03-floating-point-ieee754/2-summary.md) · [02-4](../02-integer-overflow-and-truncation/2-summary.md)(248일 카운터 — 오래 켜 둔 장비만 고장)

### 사건 2 — Ariane 5 501편: 64비트 → 16비트 변환 (1996-06-04 · 보고서 1996-07-19)

출처
- "ARIANE 5 Flight 501 Failure — Report by the Inquiry Board", 의장 J. L. Lions, Paris, 1996-07-19. ESA PDF <https://esamultimedia.esa.int/docs/esa-x-1819eng.pdf>(스캔본), 본문 텍스트 사본 <https://www-users.cse.umn.edu/~arnold/disasters/ariane5rep.html>(2026-10-07 열람). 같은 사건을 [02](../02-integer-overflow-and-truncation/2-summary.md) 장애 2가 다룬다 — 아래 사실은 그 노트와 같은 원문에서 옮겼다.

#### 사실 (원문)

- 1996-06-04 첫 비행. 비행 시퀀스 시작 약 40초 뒤, 고도 약 3700 m에서 궤도를 벗어나 분해·폭발했다(Foreword).
- 연대기(3.1): H0 + 36.7초(이륙 약 30초 뒤)에 대기 중이던 예비 관성 기준 장치(SRI)가 멈췄다. 약 0.05초 뒤 같은 하드웨어·소프트웨어의 주 SRI가 같은 이유로 멈췄다. 주 SRI는 진단 정보를 내보냈고, 주 컴퓨터가 그것을 비행 데이터로 해석해 노즐을 크게 꺾었다. H0 + 39초에 공력 하중으로 분해됐다.
- 원인(2.1): "a data conversion from 64-bit floating point to 16-bit signed integer value". 변환된 값이 16비트 부호 있는 정수로 표현할 수 있는 값보다 커서 Operand Error가 났다. 이 변환은 보호되지 않았다. 같은 자리의 비슷한 변수 변환은 보호돼 있었다.
- 값은 정렬 함수의 결과 BH(Horizontal Bias)였다. 이 함수는 이륙 전에만 의미가 있는데, Ariane 4 요구사항 때문에 이륙 뒤 약 40초까지 돌았다. Ariane 5의 초기 궤적은 수평 속도가 훨씬 커서 BH가 예상보다 컸다.
- 2.2: 변환 위험 변수 7개 중 4개만 보호했다. 이유로 SRI 컴퓨터 작업량 목표 80%가 언급됐다. 나머지 3개는 "physically limited or that there was a large margin of safety"라는 추론이었고, BH에서는 틀렸다. Ariane 5 궤적 데이터를 SRI 요구사항·명세에 넣지 않기로 합의돼 있었다.
- 2.2: 예외가 나면 실패를 버스에 알리고, 문맥을 EEPROM에 저장하고, 프로세서를 멈추도록 명세돼 있었다. "It was the decision to cease the processor operation which finally proved fatal." 같은 소프트웨어가 두 SRI에서 돌아 건강한 장비 둘이 함께 꺼졌다.
- 2.3: Ariane 5 궤적으로 SRI를 지상 시험(가속도 신호 주입·회전대)했다면 실패 메커니즘이 드러났을 것이라고 적는다.
- 권고(4): R3 "Do not allow any sensor, such as the inertial reference system, to stop sending best effort data." R5 코드의 암묵적 가정을 찾아 장비 제약과 대조하고 변수 값의 범위를 검증할 것. R10 "Include trajectory data in specifications and test requirements."

#### 원리 — 좁히기 변환의 세 가지 결말

```text
  64비트 실수 BH ──▶ 16비트 부호 있는 정수 (−32768 … 32767)
                      │
     범위 안 ─────────┴──▶ 정상 변환
     범위 밖 ──┬── Ada (Ariane SRI)  : Operand Error 예외 → 보호 없음 → 명세대로 프로세서 정지
               ├── Java (short)      : 예외 없음, 감긴 값 (40000.7 → −25536)
               └── C (short)         : 미정의 동작 (gcc -O0 x86에서 −25536, 02번 실험)
```

- [02](../02-integer-overflow-and-truncation/2-summary.md)의 실험(OpenJDK 21·gcc 13.3): `(short) 40000.7 = -25536`, C `(short)40000.7 = -25536`, `-fsanitize=float-cast-overflow`에서 `40000.7 is outside the range of representable values of type 'short int'`.
- 해석: Ariane는 "예외가 났고, 그 예외를 정지로 처리"해서 실패했다. Java라면 예외 없이 틀린 값이 계속 흘렀을 것이다. 두 결말 모두 "범위 가정이 깨졌다"는 같은 원인의 다른 얼굴이다. 어느 쪽이 덜 나쁜지는 시스템이 정한다 — R3는 정지 대신 "best effort data"를 계속 보내라고 권한다.

#### 막았을 장치 (해석 — 원문 권고에 기댐)

- 범위: 좁히기 전에 범위를 검사하고, 넘치면 포화(최댓값으로 고정)하거나 오류 표시와 함께 최선값을 보낸다(R3·R5).
- 재사용: 다른 제품에서 가져온 모듈은 **새 환경의 입력 범위**(Ariane 5 궤적)로 다시 시험한다(R10, 2.3).
- 예외 처리: 하드웨어 무작위 고장용 정책(정지 후 예비로 전환)을 같은 소프트웨어가 도는 중복 장비에 그대로 쓰지 않는다(2.2 — 예비도 같은 소프트웨어라 같은 순간 멈췄다).
- leaf: [02-2](../02-integer-overflow-and-truncation/2-summary.md) · [22](../22-arch-symptom-index/2-summary.md) 2절

### 사건 3 — Intel Pentium FDIV: 나눗셈 조회표의 빈 칸 (보고 1994-10-30 · Intel 백서 1994-11-30)

출처
- Intel, "Statistical Analysis of Floating Point Flaw in the Pentium Processor"(백서, 1994-11-30) — Intel 사이트의 원래 주소는 2026-10-07에 403이라 Internet Archive 사본(2001년 수집, `support.intel.com/support/processors/pentium/fdiv/wp/`)의 1·3·4·7절을 읽었다 <https://web.archive.org/web/2001/http://support.intel.com/support/processors/pentium/fdiv/wp/>.
- Thomas R. Nicely, "Pentium FDIV flaw FAQ"(2010-08-20 판)와 원 보고 메일(1994-10-30) — Internet Archive 사본 <https://web.archive.org/web/20101115104939/http://www.trnicely.net/pentbug/pentbug.html> · <https://web.archive.org/web/20130121011357/http://www.trnicely.net/pentbug/bugmail1.html>.
- A. Edelman, "The Mathematics of the Pentium Division Bug", SIAM Review 1997 <https://math.mit.edu/~edelman/homepage/papers/pentiumbug.pdf>(4절 — 표의 별 다섯 칸).

#### 사실 (원문)

- Nicely(FAQ Q2): 쌍둥이 소수의 역수 합을 계산하다 1994-10-04에 Pentium-60과 486DX-33의 결과가 반올림으로 설명할 수 없을 만큼 다른 것을 발견했다. 1994-10-30 메일에서 `1/824633702441.0`이 8번째 유효숫자 뒤부터 틀린다고 보고했다.
- Nicely(FAQ Q1·Q5): Coe가 찾은 최악의 예

```text
  4195835.0/3145727.0 = 1.333 820 449 136 241 002 5  (Correct value)
  4195835.0/3145727.0 = 1.333 739 068 902 037 589 4  (Flawed Pentium)
```

- Intel 백서 3절: 특정 입력에서 부동소수 나눗셈 명령이 부정확한 결과를 낸다. 단·배·확장 정밀도 모두에서 날 수 있다. 무작위 나눗셈·나머지 명령 "1 in 9 billion"이 부정확하다. 최악 오차는 가수의 소수점 아래 12번째 비트, 즉 4번째 유효 10진 숫자다. 원인은 "a few missing entries in a lookup table".
- Intel 백서 4절: 486은 클록당 몫 1비트를 만드는 "shift and subtract"를 썼다. Pentium은 클록당 2비트를 만드는 radix 4 SRT를 골랐다. 몫 자릿수 조회표(P-D plot)를 하드웨어 PLA에 내려받는 스크립트의 오류로 표의 일부 칸이 빠졌다. "The 5 critical entries" — 이 칸에 닿으면 몫 자릿수를 +2 대신 0으로 읽는다. 위험한 제수의 앞 비트 패턴은 1.0001, 1.0100, 1.0111, 1.1010, 1.1101이고, 뒤에 1이 길게 이어질수록 확률이 높다.
- Intel 백서 7절: 평균 PC 사용자는 "once in 27,000 years" 만날 것이라 결론 냈다.
- Nicely FAQ의 연표: 1994-12-20 Intel이 결함 프로세서의 전면 교체를 발표했다. 1995-01-17 교체 관련 세전 비용 4억 7,500만 달러를 발표했다.

#### 원리 — 몫 자릿수를 표에서 고르는 나눗셈

```text
  SRT radix 4 한 단계 (Intel 백서 4.1)
    ① 나머지 P와 제수 D의 앞 몇 비트를 샘플     (D는 소수점 아래 4비트, P는 7비트)
    ② 조회표[P, D] → 몫 자릿수 q ∈ {−2, −1, 0, +1, +2}
    ③ P ← 4·P − q·D                            (q는 2비트어치 몫)
    ④ 반복

  조회표 (P-D plot) 의 한 귀퉁이 — 개념도 (실제 모양은 백서 그림 4-3·Edelman 그림 4.1)
        D: 1.0001  1.0100  1.0111  1.1010  1.1101
    P 위쪽 [ +2* ]  [ +2* ]  [ +2* ]  [ +2* ]  [ +2* ]   ← * 결함 칩은 0을 돌려줌
           [ +2  ]  [ +2  ]  [ +2  ]  [ +2  ]  [ +2  ]
           ...
```

- 칸 하나가 틀리면 그 단계의 나머지가 범위를 벗어난다. 뒤 단계가 이를 고치지 못해 그 자리 이후 몫이 틀린다(Edelman 3절: SRT가 오류를 스스로 고친다는 것은 "popular misconception").
- 이 영역의 연결: 가산기·ALU가 회로로 만든 "계산"이라는 것([07](../07-logic-gates-to-adder/2-summary.md)), 그 회로가 틀릴 수 있다는 것([07-2](../07-logic-gates-to-adder/2-summary.md) 조용한 데이터 손상).

#### 실험 C: Coe의 예를 이 호스트에서 (`fdiv.py`)

```python
from decimal import Decimal, getcontext
getcontext().prec = 30
x, y = 4195835, 3145727
exact = Decimal(x) / Decimal(y)
flawed = Decimal("1.3337390689020375894")      # Nicely FAQ의 'Flawed Pentium' 값
rel = (exact - flawed) / exact
b = bin(y)[2:]                                  # 제수의 비트 패턴
```

(실험, Python 3 표준 라이브러리 `decimal`, i7-13700HX, 2026-10-07 — 결정적 계산)

```text
이 호스트 binary64 x/y = 1.333820449136241
정확값(30자리)         = 1.33382044913624100247732877011
결함 Pentium 값(FAQ)   = 1.3337390689020375894
상대 오차 = 6.101e-5  ≈ 2^ -14.0
검산 x - (x/y)*y : 정답 = -1e-23  결함 = 256.0
제수 3145727 = 0x2FFFFF = 2진 1011111111111111111111 (22비트)
가수 표기: 1.0111 11111111111111111  -> 앞 4비트 패턴 1.0111
```

- 관찰
  - 이 호스트의 나눗셈은 정확값과 binary64 정밀도까지 맞았다.
  - 결함 값의 상대 오차는 약 2⁻¹⁴이다. Nicely는 이 예를 "only 12 matching bits and 14 significant bits"라고 적는다(FAQ Q5).
  - 두 값을 2진으로 펼치면 소수점 아래 12번째 비트에서 처음 갈린다(계산 — 정확값 `0101 0101 0111…`, 결함 값 `0101 0101 0110…`). Intel 백서 3절의 최악 위치 "12th bit position to the right of the binary point"와 같다. 10진으로는 소수점 아래 4번째 자리(`1.3338…` vs `1.3337…`), 유효숫자로는 5번째부터 다르다. 백서의 "4th significant decimal digit"는 2진 비트 위치를 10진으로 근사한 표현이다(해석).
  - 제수 3145727의 가수는 `1.0111` 뒤에 1이 17개 이어진다. Intel 백서 4.2절의 위험 패턴(1.0111 + 긴 1의 열)과 정확히 같은 모양이다.
  - 결함 몫으로 `x - (x/y)*y`를 다시 계산하면 256이 남는다(정답은 0에 가까움). 몫을 곱해 되돌려 보는 검산이 결함을 드러낸다.

#### 막았을 장치 (해석)

- 검증: 조회표처럼 **생성된 데이터를 하드웨어에 옮기는 단계**를 독립적으로 검증한다(Intel 4.2절 — 원인은 내려받기 스크립트). Edelman 4절은 빠진 칸이 "접근되지 않는 칸"으로 오인되기 쉽다고 적는다.
- 운영: 중요한 계산은 다른 방법·다른 CPU로 이중 계산한다. Nicely는 같은 역수 합을 Pentium-60과 486DX-33 두 기계에서 돌려 결과가 어긋난 것에서 결함을 찾았다(FAQ Q2). 그는 역수 합을 x87 FPU와 정수 다배정밀도 두 방법으로도 계산해 검산하고 있었다. FAQ Q4도 결과가 중요한 계산은 다른 CPU·OS·소프트웨어로 두 번 하라고 권한다.
- 백엔드로 옮기면: 금액·집계는 역연산 검산(합계 = 항목 합, 몫 × 제수 = 피제수)을 대사 단계에 둔다. 하드웨어 결함의 현대판은 [07-2](../07-logic-gates-to-adder/2-summary.md)의 결함 코어다.

### 사건 4 — Spectre·Meltdown: 투기 실행의 흔적으로 메모리를 읽음 (공개 2018-01-03)

이 노트는 원리·영향·완화까지만 다룬다. 공격 재현은 하지 않는다.

출처
- Jann Horn(Google Project Zero), "Reading privileged memory with a side-channel", 2018-01-03 <https://googleprojectzero.blogspot.com/2018/01/reading-privileged-memory-with-side.html>
- Kocher 외, "Spectre Attacks: Exploiting Speculative Execution", IEEE S&P 2019 — 초록 <https://spectreattack.com/spectre.pdf>
- Lipp 외, "Meltdown: Reading Kernel Memory from User Space", USENIX Security 2018 — 초록·1장 <https://meltdownattack.com/meltdown.pdf>
- Linux 커널 문서 "Spectre Side Channels" <https://docs.kernel.org/admin-guide/hw-vuln/spectre.html> · "Page Table Isolation (PTI)" <https://docs.kernel.org/arch/x86/pti.html>
- 원리 정본: [19-out-of-order-and-speculation](../19-out-of-order-and-speculation/2-summary.md)

#### 사실 (원문)

- Project Zero(2018-01-03): CPU 데이터 캐시 타이밍으로 잘못 투기된 실행에서 정보를 빼낼 수 있고, 최악에는 로컬 보안 경계를 넘어 임의 가상 메모리를 읽는다. Intel·AMD·ARM에 2017-06-01 보고했다(각주 [1]: 이 첫 보고에는 변형 3이 없었고, 뒤에 시험해 따로 보고했다). 변형 셋:
  - Variant 1: bounds check bypass (CVE-2017-5753)
  - Variant 2: branch target injection (CVE-2017-5715)
  - Variant 3: rogue data cache load (CVE-2017-5754)
  - 변형 1·2는 Spectre, 변형 3은 Meltdown으로 공개됐다.
- Kocher 외(초록): 투기 실행 구현이 운영체제 프로세스 분리, 컨테이너화, JIT 컴파일 같은 소프트웨어 보안 장치의 가정을 깬다. Intel·AMD·ARM 마이크로프로세서에 있다. 근본 해결에는 프로세서 설계 수정과 ISA 갱신이 필요하다고 적는다.
- Lipp 외(초록·1장): Meltdown은 비순차 실행의 부작용으로 사용자 공간에서 커널 메모리를 읽는다. 운영체제와 무관하고 소프트웨어 취약점에 기대지 않는다. 3.2 KB/s~503 KB/s로 커널·물리 메모리를 덤프했다. KASLR용 방어 KAISER가 Meltdown을 상당 부분 막는다.
- 커널 문서: Spectre 관련 CVE로 CVE-2017-5753·CVE-2017-5715·CVE-2019-1125(swapgs)를 든다. 영향 여부와 완화 상태는 sysfs의 vulnerabilities 파일로 읽는다. PTI는 사용자 모드 페이지 테이블에서 커널을 대부분 빼는 완화다.

#### 원리 — 버린 실행이 캐시에 남긴 것

```text
  if (x < size)            ← 분기 예측기가 "참"이라고 추측 (과거 학습)
      y = table[ data[x] * 64 ]      ← 투기로 먼저 실행: 범위 밖 data[x]를 읽고 그 값으로 table의 한 줄을 캐시에 올림
                                       ↓
  나중에 "x < size는 거짓" 판명 → 레지스터 결과는 버림(retire 안 함)
                                     하지만 캐시에 올라온 table의 줄은 남음
                                       ↓
  table 각 줄의 접근 시간을 재면 빠른 줄 하나 = data[x] 값
```

- 아키텍처 상태(레지스터·메모리)는 되돌려지지만 **마이크로아키텍처 상태**(캐시)는 남는다. 이 구분과 비순차·투기 실행의 바탕은 [18](../18-pipelining-and-branch-prediction/2-summary.md)·[19](../19-out-of-order-and-speculation/2-summary.md), 캐시 시간 차는 [11](../11-memory-hierarchy-and-locality/2-summary.md)·[13](../13-latency-numbers/2-summary.md).
- Meltdown은 권한 검사보다 값 읽기가 먼저 투기적으로 일어나는 비순차 실행을 썼다. 완화(PTI)는 사용자 모드일 때 커널 주소를 페이지 테이블에서 빼서 "읽을 주소 자체"를 없앤다.

#### 관찰: 이 호스트의 완화 상태

(실험, i7-13700HX, Linux 7.0.0-34-generic, `grep . /sys/devices/system/cpu/vulnerabilities/{meltdown,spectre_v1,spectre_v2}`, 2026-10-07 — 읽기만)

```text
spectre_v2:Mitigation: Enhanced / Automatic IBRS; IBPB: conditional; PBRSB-eIBRS: SW sequence; BHI: BHI_DIS_S
meltdown:Not affected
spectre_v1:Mitigation: usercopy/swapgs barriers and __user pointer sanitization
```

- 이 CPU는 Meltdown에 영향받지 않는다고 커널이 판단했다. Spectre 변형 1·2에는 완화가 켜져 있다. 같은 값과 그 해석은 [19](../19-out-of-order-and-speculation/2-summary.md) 5절과 같다.

#### 영향과 막는 장치 (해석 — 커널 문서·[19](../19-out-of-order-and-speculation/2-summary.md)에 기댐)

- 성능: PTI는 커널 진입·탈출마다 CR3를 바꿔 시스템 콜이 많은 서비스일수록 비용이 크다. IBPB 같은 완화는 문맥 전환 등에서 조건부로 비용을 더한다([19-1](../19-out-of-order-and-speculation/2-summary.md)).
- 격리: 컨테이너는 커널·코어·캐시를 공유한다. 신뢰 수준이 다른 작업은 VM·전용 호스트로 나누고, 필요하면 SMT를 끈다([19-2](../19-out-of-order-and-speculation/2-summary.md)).
- 운영: 커널·마이크로코드를 갱신하고 `vulnerabilities`로 상태를 확인한다. 완화를 끄는 것(`mitigations=off`)은 위험 수용 결정이다.
- 해석: 앞 세 사건이 "기능이 틀린 결과를 냈다"였다면, 이 사건은 **결과는 맞는데 부수 효과(시간)가 비밀을 흘린** 경우다. 정확성 테스트로는 찾을 수 없다.

### 사건 5 — 2038년 문제: 부호 있는 32비트 초 (2038-01-19 03:14:07 UTC가 마지막 초)

출처
- Linux 커널 문서 "ktime accessors" — Deprecated time interfaces: `struct timeval`·`struct timespec`을 돌려주는 인터페이스는 "the tv_sec member overflows in year 2038 on 32-bit architectures"라서 교체됐다 <https://docs.kernel.org/core-api/timekeeping.html>
- Linux 소스 `include/linux/time64.h`: `typedef __s64 time64_t;` <https://raw.githubusercontent.com/torvalds/linux/master/include/linux/time64.h>
- glibc 2.34 릴리스 공지(2021-08-02) NEWS: x86처럼 `time_t`가 전통적으로 32비트인 구성에 64비트 `time_t` 지원 추가, `_TIME_BITS=64`로 켜고 `_FILE_OFFSET_BITS=64`가 함께 필요, Linux 전용, 완전한 지원은 커널 5.1 이상 <https://sourceware.org/pipermail/libc-alpha/2021-August/129718.html>(Internet Archive 사본으로 열람)
- glibc 매뉴얼 "Feature Test Macros" — `_TIME_BITS` <https://www.gnu.org/software/libc/manual/html_node/Feature-Test-Macros.html>(Internet Archive 사본으로 열람)
- J. Corbet, "System call conversion for year 2038", LWN, 2015-05-05 <https://lwn.net/Articles/643234/>

#### 사실 (원문)

- LWN(2015): 유닉스 계열의 시간 값은 1970년 시작부터 센 초다. 32비트 시스템에서 그 수는 부호 있는 32비트이고, 2038년 1월에 비트가 바닥난다.
- 커널 문서: `struct timeval`·`struct timespec`을 돌려주는 옛 인터페이스는 32비트 아키텍처에서 2038년에 `tv_sec`이 넘치므로 `*_ts64`·`ktime_t` 계열로 대체됐다. 커널 안 `time64_t`는 부호 있는 64비트다.
- glibc 매뉴얼: `_TIME_BITS`가 없으면 `time_t` 크기는 아키텍처에 따른다. 대부분 64비트이고 i686·ARM 같은 전통 아키텍처에서는 32비트다(바뀔 예정이니 기본값에 기대지 말 것). `_TIME_BITS=32`는 "32-bit time_t stops working in the year 2038"이라 권하지 않는다. 64로 정의하면 "immune to the Y2038 problem". 커널 5.1 위에서는 64비트 시간 시스템 콜을 쓰고, 그 아래에서는 옛 32비트 시스템 콜로 대체한다.
- 같은 상한이 DB에도 있다: MySQL `TIMESTAMP` 범위는 `'2038-01-19 03:14:07'` UTC까지다([database/27](../../database/27-temporal-types-and-session-timezone/2-summary.md) — 문서 13.2.2와 로컬 재현).

#### 원리 — 2의 보수 원을 한 칸 넘는다

```text
  초 (부호 있는 32비트)
   0x7FFFFFFF =  2147483647  →  2038-01-19 03:14:07 UTC   (마지막 초)
   + 1
   0x80000000 = -2147483648  →  1901-12-13 20:45:52 UTC   (부호 비트가 켜져 음수)

  무부호로 읽으면   0xFFFFFFFF = 4294967295 → 2106-02-07 06:28:15 UTC 까지 (다른 상한)
  부호 있는 64비트  약 2920억 년 뒤                               (사실상 상한 없음)
```

- 이 감김은 [01](../01-number-systems-twos-complement/2-summary.md)의 2의 보수 원, [02](../02-integer-overflow-and-truncation/2-summary.md)의 wrap과 같은 현상이다. 차이는 **날짜가 정해져 있다**는 점이다. 그래서 미래 날짜(만료일·예약 시각·30년 만기 대출)를 다루는 코드는 2038년 전에 이미 부딪힌다(해석).
- 64비트 Linux(x86-64)에서는 `time_t`가 이미 64비트다. 남은 위험은 32비트 플랫폼, 그리고 **4바이트 필드에 시각을 담는 데이터 형식**(파일 형식·프로토콜·DB 컬럼)이다(해석).

#### 실험 D: 넘침 시각과 4바이트 필드 (`y2038.c`·`Y2038.java`)

```c
int32_t s32 = INT32_MAX;
show("INT32_MAX", s32);
int32_t wrapped = (int32_t)((uint32_t)s32 + 1u);   /* 32비트로 저장한 다음 1초 */
show("INT32_MAX+1 (32비트 저장)", wrapped);
show("INT32_MAX+1 (64비트)", (int64_t)s32 + 1);
```

(실험, gcc 13.3.0 `-O2`, glibc 2.39, x86-64 Linux 7.0.0-34-generic, 2026-10-07)

```text
sizeof(time_t) = 8
INT32_MAX                      2147483647 -> 2038-01-19 03:14:07 UTC
INT32_MAX+1 (32비트 저장)  -2147483648 -> 1901-12-13 20:45:52 UTC
INT32_MAX+1 (64비트)         2147483648 -> 2038-01-19 03:14:08 UTC
```

```java
long next = Instant.parse("2038-01-19T03:14:08Z").getEpochSecond();
int narrowed = (int) next;                                         // 4바이트 필드·int 컬럼에 담기
byte[] wire = ByteBuffer.allocate(4).putInt((int) next).array();   // 프로토콜의 4바이트 시각 필드
int readBack = ByteBuffer.wrap(wire).getInt();
Math.toIntExact(next);                                             // 넘치면 예외
```

(실험, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-07)

```text
Integer.MAX_VALUE 초 = 2038-01-19T03:14:07Z
2038-01-19T03:14:08Z -> long 2147483648 -> (int) -2147483648 -> 1901-12-13T20:45:52Z
4바이트 필드 왕복: 1901-12-13T20:45:52Z / 무부호로 읽으면: 2038-01-19T03:14:08Z
무부호 32비트 상한: 2106-02-07T06:28:15Z
Math.toIntExact: java.lang.ArithmeticException: integer overflow
```

- 관찰
  - 이 호스트(x86-64)의 `time_t`는 8바이트였다. 64비트로 계산하면 2038-01-19 03:14:08이 정상으로 나왔다.
  - 같은 값을 32비트에 담으면 1901-12-13 20:45:52 UTC로 감겼다. C와 Java가 같은 시각을 보였다. C의 `uint32_t` → `int32_t` 범위 밖 변환은 구현 정의(C11 6.3.1.3)이고 gcc는 "reduced modulo 2^N"으로 정의한다(GCC 매뉴얼 Integers implementation) — 이 결과는 이 구현의 값이다. 32비트 `time_t` 실행 파일이 64비트 커널에서 `time()`을 부르면 감기는 대신 `EOVERFLOW`가 날 수 있다(time(2)).
  - 4바이트 필드를 무부호로 읽으면 2106년까지 버틴다. 다만 이것은 형식을 읽는 쪽 전부가 무부호로 합의해야 한다.
  - `Math.toIntExact`는 감기는 대신 예외를 냈다.
- 이 호스트에는 32비트 glibc 개발 파일이 없어 `gcc -m32`(32비트 `time_t`, `_TIME_BITS=64` 비교)는 컴파일되지 않았다(`bits/libc-header-start.h` 없음). 32비트 플랫폼 동작은 위 glibc 매뉴얼·NEWS로 대신한다.

#### 막는 장치

- 플랫폼: 64비트 `time_t`(64비트 아키텍처, 32비트에서는 `_TIME_BITS=64` + `_FILE_OFFSET_BITS=64`, 커널 5.1 이상 — glibc 문서).
- 데이터 형식: 4바이트 초 필드를 새로 만들지 않는다. 기존 필드는 범위 검사(`Math.toIntExact`)로 조용한 감김을 막고, 8바이트로 옮기는 판 변경을 계획한다(해석).
- DB: MySQL에서 2038년 이후 값이 올 수 있으면 `DATETIME`(+ UTC 저장 규약)을 쓴다([database/27](../../database/27-temporal-types-and-session-timezone/2-summary.md)).
- 시험: 시계를 2038년 근처로 옮기거나 경계값(`2147483647`·`2147483648`)을 넣는 테스트(해석).

### 다섯 사건을 나란히 (해석)

| | 깨진 것 | 표현·하드웨어 | 숨어 있던 가정 | 드러난 조건 | leaf |
|---|---|---|---|---|---|
| Patriot | 0.1의 2진 절단 오차가 선형 누적 | 24비트 레지스터, 고정 소수점(2차 출처) | "몇 시간만 운용" | 100시간 연속 가동 | [03](../03-floating-point-ieee754/2-summary.md) · [02-4](../02-integer-overflow-and-truncation/2-summary.md) |
| Ariane 5 | 64비트 실수 → 16비트 정수 범위 밖 | 16비트 부호 있는 정수, Ada 예외 → 정지 | "BH는 물리적으로 제한된다"(Ariane 4 궤적) | 더 큰 수평 속도 | [02-2](../02-integer-overflow-and-truncation/2-summary.md) |
| FDIV | 몫 자릿수 조회표의 빈 칸 5개 | radix 4 SRT 나눗셈기 | "표가 옳게 내려받혔다" | 드문 제수 비트 패턴 | [07](../07-logic-gates-to-adder/2-summary.md) · [07-2](../07-logic-gates-to-adder/2-summary.md) |
| Spectre/Meltdown | 버린 투기 실행의 캐시 흔적 | 분기 예측·비순차 실행·캐시 | "버린 실행은 흔적이 없다" | 공격자가 고른 코드·시간 측정 | [18](../18-pipelining-and-branch-prediction/2-summary.md) · [19](../19-out-of-order-and-speculation/2-summary.md) |
| 2038 | 부호 있는 32비트 초의 wrap | 32비트 `time_t`·4바이트 필드 | "2038년은 멀다" | 미래 날짜, 오래 남는 형식 | [01](../01-number-systems-twos-complement/2-summary.md) · [02](../02-integer-overflow-and-truncation/2-summary.md) |

- 공통점: Patriot·Ariane·Spectre/Meltdown·2038은 **설계 당시의 가정 범위**(가동 시간·속도·실행 코드·날짜) 안에서는 옳았고, 범위가 바뀌는 것을 알리는 장치가 없었다. FDIV는 예외다 — 명령이 허용하는 정상 피연산자에서도 처음부터 틀렸고(조회표 결함), 드문 제수 비트 패턴에서만 드러나 숨어 있었다.
- 차이: Patriot·Ariane·2038은 **표현 폭**이 원인이라 코드에서 범위 검사로 막을 수 있다. FDIV·Spectre는 **하드웨어 구현**이 원인이라 검산·완화 상태 확인·하드웨어 교체로 대응한다. FDIV는 코드 리뷰로 보이지 않지만, Spectre 변형 1의 위험 경로는 코드 패턴이라 커널처럼 코드 검토·`nospec` 수정도 완화에 든다(커널 hw-vuln/spectre).

## 쓰이는 자료구조·알고리즘

- **고정 소수점·2의 보수**: Patriot의 시각 표현, 2038의 초 카운터([01](../01-number-systems-twos-complement/2-summary.md)).
- **좁히기 변환과 포화 산술**: Ariane의 64 → 16비트([02](../02-integer-overflow-and-truncation/2-summary.md)).
- **SRT 나눗셈(조회표 기반 자릿수 선택)**: FDIV. 조회표는 2차원 배열 — 표 생성·전송의 독립 검증이 교훈이다.
- **분기 예측기·재정렬 버퍼·캐시**: Spectre/Meltdown([18](../18-pipelining-and-branch-prediction/2-summary.md) 2비트 포화 카운터, [19](../19-out-of-order-and-speculation/2-summary.md) 재정렬 버퍼).
- **정확한 유리수·10진 연산**: 실험 A(`fractions.Fraction`)와 C(`decimal`)는 오차를 재는 쪽이 오차를 만들지 않게 정확한 수 표현을 썼다([math/15](../../math/15-numerical-stability/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 내 코드로 옮길 점검 목록

```text
  □ 경과 시간·틱은 정수로 쌓고, 실수 변환은 차(Δ)에만 하나?                     (Patriot)
  □ 오래 켜 두는 프로세스·장비의 카운터 폭 × 증가 속도가 수명 안에 넘치지 않나?     (Patriot · 02-4)
  □ 다른 제품·버전에서 가져온 모듈의 입력 범위를 새 환경 값으로 다시 시험했나?        (Ariane)
  □ 좁히기 변환마다 범위 검사가 있나? 넘치면 정지·포화·오류 표시 중 무엇인가?        (Ariane)
  □ 중요한 계산 결과를 역연산·다른 경로로 검산하나?                              (FDIV)
  □ 서버의 vulnerabilities·커널·마이크로코드 상태를 기록·갱신하나?                 (Spectre/Meltdown)
  □ 신뢰 수준이 다른 작업이 같은 호스트·같은 코어에 있나?                          (Spectre/Meltdown)
  □ 4바이트 시각 필드(파일 형식·프로토콜·int 컬럼·MySQL TIMESTAMP)가 남아 있나?     (2038)
```

### 2. 코드 — Java 21

```java
import java.time.Duration;
import java.time.Instant;

final class TimeAndRange {
    // Patriot형: 시각을 실수로 쌓지 않는다 — 정수 나노초(단조 시계)로 두고 차만 변환
    static double elapsedSeconds(long startNanos, long nowNanos) {
        return (nowNanos - startNanos) / 1e9;          // 차는 작아 double로 바꿔도 오차가 누적되지 않는다
    }

    // Ariane형: 좁히기 전에 범위 검사 — 예외 대신 포화가 맞는 시스템이면 clamp를 쓰고 표시를 남긴다
    static short toShortChecked(double v) {
        if (Double.isNaN(v) || v < Short.MIN_VALUE || v > Short.MAX_VALUE)
            throw new ArithmeticException("out of 16-bit range: " + v);
        return (short) v;
    }
    static short toShortSaturated(double v) {           // R3식 "best effort": 범위 끝으로 고정
        if (Double.isNaN(v)) return 0;
        return (short) Math.max(Short.MIN_VALUE, Math.min(Short.MAX_VALUE, Math.round(v)));
    }

    // FDIV형: 몫을 곱해 되돌려 보는 검산
    static boolean divisionChecks(double x, double y, double q) {
        return Math.abs(x - q * y) <= Math.ulp(x) * 4;    // 허용 오차는 예시
    }

    // 2038형: 4바이트 시각 필드에 넣기 전에 검사
    static int toEpochSeconds32(Instant t) {
        return Math.toIntExact(t.getEpochSecond());     // 2038-01-19T03:14:08Z부터 ArithmeticException
    }

    public static void main(String[] args) {
        System.out.println(toShortSaturated(40000.7));                       // 32767
        System.out.println(divisionChecks(4195835.0, 3145727.0, 4195835.0 / 3145727.0));     // true
        System.out.println(divisionChecks(4195835.0, 3145727.0, 1.3337390689020375894));     // false
        System.out.println(Duration.ofSeconds(Integer.MAX_VALUE).toDays() + " days");     // 24855
    }
}
```

- 위 `main`의 출력(실행, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, 2026-10-07): `32767`, `true`, `false`, `24855 days`.
- `Duration.ofSeconds(Integer.MAX_VALUE).toDays()`는 24,855일(약 68년)이다(계산: 2147483647 / 86400 = 24855.13). 1970년 + 68년 = 2038년이다.
- 셸에서 확인: `grep . /sys/devices/system/cpu/vulnerabilities/*`(Spectre/Meltdown), `getconf LONG_BIT`와 `file`(32비트 바이너리 여부), MySQL `SHOW CREATE TABLE`에서 `timestamp` 컬럼(2038).

## 장애 시나리오와 대처

### 1. 오래 켠 프로세스만 시각·주기가 어긋난다 — Patriot형

- **현상**: 재시작 직후에는 정상인 스케줄러·레이트 리미터가 몇 주 가동한 인스턴스에서만 주기가 밀리거나 만료 판정이 틀린다.
- **보이는 형태**: 오차가 가동 시간에 비례해 커진다. 재시작하면 사라진다.
- **원인**: 경과 시간을 `float`·`double`에 반복 덧셈으로 쌓았거나, 틱을 근삿값 상수로 곱했다(실험 A·`patriot2.py`: float32 누적 100시간에 12,975초 오차).
- **대처**: 단조 시계의 정수 값(`System.nanoTime()`)을 두고 차만 변환한다. 가동 시간을 지표로 내보내 오차와 상관을 본다. 재시작으로 덮지 않는다.

### 2. 다른 제품에서 가져온 모듈이 새 입력 범위에서 멈춘다 — Ariane형

- **현상**: 기존 서비스에서 수년 문제없던 파서·계산 모듈을 새 서비스에 붙였더니 특정 값에서 예외로 요청 처리 스레드가 죽는다.
- **보이는 형태**: `ArithmeticException`·`NumberFormatException` 또는 조용히 틀린 값(−25536 같은). 기존 서비스의 데이터에는 그 범위가 없었다.
- **원인**: 모듈의 암묵적 범위 가정("이 값은 16비트 안")이 새 데이터에서 깨졌다. 예외 처리 정책이 "전체 중단"이었다.
- **대처**: 재사용 모듈의 입력 범위를 문서·코드로 드러내고 새 환경 데이터로 시험한다(R5·R10). 예외가 났을 때 정지·포화·대체값 중 무엇이 맞는지 시스템 수준에서 정한다(R3·R6).

### 3. 특정 서버에서만 계산이 가끔 틀린다 — FDIV형

- **현상**: 같은 배치를 서버 A에서 돌리면 합계가 맞고, 서버 B에서 돌리면 가끔 틀린다. 코드·입력은 같다.
- **보이는 형태**: 커널·애플리케이션 로그에 오류 없음. 틀린 결과는 특정 입력 값에 몰린다.
- **원인**: 하드웨어 결함(FDIV형 설계 결함 또는 [07-2](../07-logic-gates-to-adder/2-summary.md)의 결함 코어).
- **대처**: 서버·코어를 고정해 재현한다. 역연산 검산·이중 계산을 대사 단계에 둔다. 재현되면 장비를 격리하고 제조사 공지(에라타)를 확인한다.

### 4. 보안 패치 뒤 시스템 콜 많은 서비스가 느려진다 — Spectre/Meltdown형

- **현상**: 커널·마이크로코드 업데이트 뒤 같은 부하에서 CPU `sys` 비중이 오르고 처리량이 몇 % 떨어진다.
- **보이는 형태**: 사용자 코드 시간은 같고 `sys`만 증가. 호스트마다 정도가 다르다.
- **원인**: 켜진 완화(PTI의 CR3 전환 등)의 비용이 커널 진입 빈도에 비례한다([19-1](../19-out-of-order-and-speculation/2-summary.md)). CPU 세대마다 켜지는 완화가 다르다(19-3).
- **대처**: `vulnerabilities`로 무엇이 켜졌는지 기록한다. 시스템 콜을 묶는다(배치 I/O). 완화를 끄는 결정은 성능이 아니라 위험 수용으로 따로 다룬다.

### 5. 2038년 이후 날짜가 1901년으로 저장된다 — 2038형

- **현상**: 만기 2040년 상품의 만기일이 1901년으로 저장되거나, MySQL `TIMESTAMP` 컬럼 삽입이 실패한다(strict 모드. 비-strict면 경고와 함께 zero 값으로 저장 — database/27).
- **보이는 형태**: 날짜 `1901-12-13T20:45:52Z` 근처 값, 또는 MySQL `ERROR 1292 (22007): Incorrect datetime value`([database/27](../../database/27-temporal-types-and-session-timezone/2-summary.md)).
- **원인**: 초를 `int`·4바이트 필드·`TIMESTAMP`에 담았다(실험 D).
- **대처**: 64비트 초·`Instant`·`DATETIME`(UTC 규약)으로 바꾼다. 경계 테스트(`2147483647`·`2147483648`)를 둔다. 형식을 바꿀 수 없으면 `Math.toIntExact`로 조용한 감김을 예외로 바꾸고 판 변경을 계획한다.

## 핵심 문장

- 네 사건(Patriot·Ariane·Spectre/Meltdown·2038)은 설계 당시의 가정 범위 안에서는 옳았다. 사고는 가동 시간·속도·실행 코드·날짜가 그 범위를 벗어날 때 났다. FDIV는 정상 입력에서도 틀렸고 드문 비트 패턴이라 숨어 있었다.
- Patriot: 0.1은 2진으로 끝나지 않는다. 같은 방향의 작은 절단 오차가 틱마다 쌓여 100시간에 0.3433초가 됐다. 23비트 절단 계산이 GAO 표를 그대로 재현한다.
- Ariane 5: 범위 밖 좁히기가 예외를 냈고, 예외 = 정지라는 설계가 같은 소프트웨어의 두 장치를 함께 껐다.
- FDIV: 조회표 빈 칸 5개가 드문 제수에서 몫을 틀리게 했다(최악 소수점 아래 12번째 비트, 백서 표현으로 "4th significant decimal digit"). 역연산 검산과 이중 계산이 그것을 드러낸다.
- Spectre/Meltdown: 결과는 맞는데 투기 실행이 캐시에 남긴 시간 흔적이 비밀을 흘렸다. 정확성 테스트로는 못 찾고, 완화 상태 확인과 격리로 대응한다.
- 2038: 부호 있는 32비트 초는 2038-01-19 03:14:07 UTC 다음 값을 표현할 수 없다. 감기면 1901년이 되고(실험 D), 인터페이스에 따라 `EOVERFLOW` 같은 실패가 된다(time(2)). 남은 위험은 32비트 플랫폼과 4바이트 시각 필드다.

## 관련 주제·근거

- 선행: [22-arch-symptom-index](../22-arch-symptom-index/2-summary.md)(증상 역색인)
- 사건별 leaf: [01](../01-number-systems-twos-complement/2-summary.md) · [02](../02-integer-overflow-and-truncation/2-summary.md)(장애 2 Ariane, 장애 4 248일 카운터) · [03](../03-floating-point-ieee754/2-summary.md) · [07](../07-logic-gates-to-adder/2-summary.md) · [11](../11-memory-hierarchy-and-locality/2-summary.md) · [13](../13-latency-numbers/2-summary.md) · [18](../18-pipelining-and-branch-prediction/2-summary.md) · [19](../19-out-of-order-and-speculation/2-summary.md)
- 다른 영역: [math/15-numerical-stability](../../math/15-numerical-stability/2-summary.md) · [math/17-math-incidents](../../math/17-math-incidents/2-summary.md) · [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) · [os/38-os-incidents](../../os/38-os-incidents/2-summary.md) · [security/30-security-incidents](../../security/30-security-incidents/2-summary.md) · [algorithm/43-alg-incidents](../../algorithm/43-alg-incidents/2-summary.md)
- 1차 출처
  - GAO/IMTEC-92-26(1992-02-04) — 본문, 부록 II 표. Internet Archive 사본 <https://web.archive.org/web/20241207021820/https://www.gao.gov/assets/imtec-92-26.pdf>
  - Ariane 501 Inquiry Board 보고서(1996-07-19) — Foreword, 2.1·2.2·2.3·3.1, 권고 R3·R5·R10 <https://www-users.cse.umn.edu/~arnold/disasters/ariane5rep.html>
  - Intel FDIV 백서(1994-11-30) 1·3·4·7절(Internet Archive 사본) · Nicely FAQ(2010)·원 메일(1994-10-30) · Edelman, SIAM Review 1997
  - Project Zero 블로그(2018-01-03) · Kocher 외 IEEE S&P 2019 · Lipp 외 USENIX Security 2018 · 커널 문서 hw-vuln/spectre·x86/pti
  - 커널 문서 core-api/timekeeping · `include/linux/time64.h` · glibc 2.34 NEWS(2021-08-02) · glibc 매뉴얼 `_TIME_BITS` · LWN 643234(2015-05-05)
- 실험 목록
  - `patriot.py`·`patriot2.py` — Python 3 표준 라이브러리(`fractions`·`struct`), 호스트: 0.1의 23·24비트 절단 오차 × 틱 수 vs GAO 표, double·float32 누적 비교
  - `fdiv.py` — Python `decimal`(정밀도 30), 호스트: Coe의 예의 정확값·결함 값 상대 오차·검산 잔차·제수 비트 패턴
  - `y2038.c` — gcc 13.3.0 `-O2`, glibc 2.39, x86-64: 32비트 넘침 시각(`gmtime_r`), `-m32`는 32비트 glibc 헤더 없음으로 실패
  - `Y2038.java` — eclipse-temurin:21-jdk(OpenJDK 21.0.12), docker `--rm --pull never --network none --cpus=2 -u`: `(int)` 좁히기·4바이트 필드 왕복·`Math.toIntExact`
  - `/sys/devices/system/cpu/vulnerabilities/{meltdown,spectre_v1,spectre_v2}` 읽기(i7-13700HX, 커널 7.0.0-34-generic) — 공격 재현 없음
