# ai-engineering/26-ai-incidents — 정답

## 정답

### 1. Mata v. Avianca의 제재 근거

- 결정문 첫 문단: "there is nothing inherently improper about using a reliable artificial intelligence tool for assistance." 그러나 기존 규칙(Rule 11)은 변호사에게 제출 서면의 정확성을 지키는 "gatekeeping role"을 지운다.
- 제재 근거: 존재하지 않는 판결과 가짜 인용을 제출하고, 법원 명령으로 존재가 의심된 뒤에도 고수했다. 개별 변호사에게 "conscious avoidance and false and misleading statements to the Court"에 근거한 bad faith를 인정했다.
- 생성기에게 진위를 물은 장면(사실 인정 45항): "Is Varghese a real case", "Are the other cases you provided fake"라고 물었고, ChatGPT는 Westlaw·LexisNexis·Federal Reporter에서 찾을 수 있는 "real" 판례라고 답했다.
- 검증이 아닌 이유: 같은 생성기가 같은 방식으로 또 한 번 생성한 것이라 모델 밖의 사실과 대조되지 않는다(해석). 상대방은 3월 15일에 이미 판례 데이터베이스에서 "찾을 수 없다"고 적었다 — 모델 밖 대조가 가능했다.

### 2. RAG로 옮긴 Mata

- 증상: 답 끝의 근거 문서·조항이 존재하지 않는다. 링크가 404이거나 원문에 인용 문장이 없다.
- 막는 장치: 인용은 시스템이 검색해 건넨 청크 ID로만 하게 하고, 건넨 ID 집합 밖의 인용은 거부한다. 링크는 응답 텍스트를 파싱하지 않고 검증된 ID로 메타데이터에서 만든다([15-5](../15-rag-pipeline/2-summary.md)).
- 색인: [25](../25-ai-symptom-index/2-summary.md) 6절(검색이 엉뚱함 — 출처 링크가 존재하지 않음 행). 근거가 필요한 업무를 가중치 지식에 맡긴 경우는 25의 11절 [24-4](../24-fine-tuning-vs-rag-decision/2-summary.md) 행.

### 3. 세 버그

- ① 문맥 창 라우팅 오류 — 2025-08-05 시작. 일부 Sonnet 4 요청이 1M 토큰 문맥 창용 서버로 잘못 감. 09-04 수정 배포, 1st-party·Vertex 09-16, Bedrock 09-18 완료.
- ② 출력 손상 — 2025-08-25 TPU 서버 설정 오류. 영어 질문에 태국어·중국어 문자, 코드 문법 오류. Opus 4.1·Opus 4는 08-25~28, Sonnet 4는 08-25~09-02. 09-02 롤백, 이상 문자 출력 탐지 테스트 추가. 3rd-party 플랫폼 영향 없음.
- ③ 근사 top-k XLA:TPU 컴파일러 버그 — 2025-08-25 배포한 토큰 선택 코드가 잠복 버그를 드러냄. Haiku 3.5에서 확인(09-04 롤백), Opus 3(09-12 롤백), Sonnet 4는 재현 못 했지만 롤백. 정확 top-k + 정밀도 강화로 교체. (원문은 샘플링 코드 재작성 배포를 다른 곳에서 08-26으로 적는다.)
- 0.8%: 버그 ①이 처음 영향을 준 **Sonnet 4 요청의 비율**. 16%: 08-29 부하 분산 변경 뒤 **08-31 최악 시간대**에 영향받은 Sonnet 4 요청의 비율. 별도로 이 기간 요청한 Claude Code 사용자의 약 30%가 적어도 한 메시지를 잘못된 서버로 보냈다.

### 4. 탐지가 늦은 이유와 대응

- 원문의 이유
  - 평가가 저하를 잡지 못했다 — "Claude often recovers well from isolated mistakes."
  - 버그마다 플랫폼별로 증상·비율이 달라 "random, inconsistent degradation"처럼 보였다.
  - 개인정보 보호 통제로 엔지니어가 문제 대화를 보기 어려웠다.
  - 노이즈가 큰 평가에 너무 기댔고, 08-29 보고 급증을 같은 날의 부하 분산 변경과 바로 연결하지 못했다.
- API를 쓰는 쪽의 대응(해석)
  - 평가 미탐지 → 고정 평가셋을 운영과 같은 경로로 주기적으로 돌려 날짜별 점수를 남긴다([19](../19-llm-evaluation/2-summary.md) · [07-5](../07-decoding-and-nondeterminism/2-summary.md)).
  - 플랫폼·경로별 증상 차이 → 응답 모델·경로·리전을 기록하고 품질 지표를 그 차원과 사용자 단위로 나눈다([13-3](../13-model-routing-and-fallback/2-summary.md)).
  - 변경과 연결 실패 → 우리 변경 이력과 제공자 공지를 한 시간축에 둔다([25](../25-ai-symptom-index/2-summary.md) 장애 4).
  - 출력 손상 → 기대 언어 밖 문자 비율 같은 출력 이상 지표.

### 5. `sticky.py`

- p = 0.008, sticky 없음: 요청 영향 0.8%, 사용자 1건 이상 32.7~33.1%, 영향 사용자당 평균 1.2건.
- p = 0.008, sticky: 요청 영향 0.8~0.9%, 사용자 1건 이상 3.9~4.2%, 영향 사용자당 평균 10.2건(= 세션 하나 분량).
- 확인 계산: sticky 없음은 메시지 50개가 독립이라 1 − (1 − 0.008)^50 ≈ 33.1%. sticky는 세션 5개의 첫 배정만 독립이라 1 − (1 − 0.008)^5 ≈ 3.9%.
- 말해 주는 것: 요청 단위 비율이 같아도, sticky 라우팅은 문제를 **소수 사용자에게 세션째** 몰아준다. 요청 단위 지표나 전체 평균으로는 안 보이고, 사용자·경로 단위로 나눠야 보인다. "일부 사용자만"은 잡음이 아니라 경로 차이일 수 있다(해석 — 모형이며 실제 비율의 재현이 아니다).

### 6. Greshake 외의 세 관찰

- 1) 간접으로 주입된 지시도 모델을 조종한다 — "the data and instruction modalities are not disentangled."
- 2) 채팅 인터페이스에서 보통 걸러지는 프롬프트가 간접 주입에서는 걸러지지 않았다.
- 3) 대부분의 경우 모델이 대화 세션 내내 주입을 유지했다.
- 입력 필터의 위치는 2)다. 사용자 입력 쪽에 둔 필터는 검색 경로로 들어온 내용을 보지 못했다. 해석: 신뢰 경계는 "사용자가 입력한 것"이 아니라 **"모델이 읽는 모든 것"**(검색 문서·메일·웹·도구 결과)에 그어야 한다.

### 7. 완화책과 방어 목표

- 원문(5.6절 요지): RLHF 같은 대응은 "Whack-A-Mole" 양상이다. 검색 입력에서 지시를 걸러 내는 방법에는 딜레마가 있다 — 거르는 모델이 같은 함정에 빠지지 않으려면 덜 일반적인 모델이 필요한데, 그런 모델은 복잡하게 인코딩된 입력을 못 잡을 수 있다. "it is currently hard to imagine a foolproof solution for the adversarial prompting vulnerability."
- 목표의 변화: "모델이 속지 않게"에서 **"속아도 할 수 있는 일이 적게"**로.
- [22](../22-prompt-injection-and-llm-security/2-summary.md)의 장치
  - 작업별 도구 허용 목록과 인자 출처·수신자 허용 목록(모델 밖 게이트웨이).
  - 외부 전송·결제·삭제 같은 고위험 행동의 사람 확인.
  - 모델 출력을 불신 데이터로 보고 문맥별 인코딩·스키마 검증([22-2](../22-prompt-injection-and-llm-security/2-summary.md)).

### 8. Moffatt v. Air Canada

- 회사의 주장(27항): 챗봇을 포함한 대리인의 정보에 책임지지 않는다 — 사실상 챗봇이 별개의 법적 주체라는 주장.
- 재판소의 답: "a remarkable submission." 챗봇은 "still just a part of Air Canada's website", 회사는 "responsible for all the information on its website", 정적 페이지든 챗봇이든 차이가 없다. 또 고객이 웹사이트 한 곳의 정보를 다른 곳에서 다시 확인해야 할 이유를 회사가 설명하지 않았다(28항).
- 금액(44항): 총 $812.02 = 손해 $650.88 + 판결 전 이자 $36.14 + CRT 수수료 $125. 신청인의 청구는 $880이었다.
- 알 수 없는 것: 챗봇의 기술. 결정문 14항은 "Air Canada did not provide any information about the nature of its chatbot"이라 적는다. LLM 기반이었는지는 이 원문으로 알 수 없다.

### 9. 공통 교훈과 장치의 위치

- 공통 교훈: 대부분 출력의 형식은 그럴듯했지만 **형식은 내용을 보증하지 않는다**(해석). 사건 2의 출력 손상(이상 문자·코드 문법 오류)처럼 형식부터 깨지는 경우도 있어, 형식 검사와 내용 검증을 둘 다 둔다.
- 장치의 위치 — 넷 다 모델 **밖**
  - Mata: 인용을 원 데이터베이스·건넨 ID 집합과 대조하는 코드.
  - Anthropic: 운영 경로에서 계속 도는 평가와 이상 출력 탐지(제공자 쪽), 날짜별 평가·경로 기록(사용자 쪽).
  - Greshake: 도구 권한·사람 확인·출력 처리를 맡는 게이트웨이.
  - Air Canada: 규정 원천에 묶인 검색과 근거 인용, 규정 질의 회귀 평가.
