# cs/issue/infra/llm-serving-vram-and-backend — LLM 서빙: VRAM 예산과 GPU 세대별 커널 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-24).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. (왜) 4bit 양자화 7B 모델 가중치는 약 5.2GB인데, 약 7.6GB VRAM GPU에서 서빙 엔진이 `CUDA out of memory ... warming up sampler with 256 dummy requests`로 죽었다. 가중치 말고 VRAM을 먹는 것은 무엇이며, 왜 "워밍업" 단계에서 터지는가.
2. (예측) 동시 시퀀스 상한(`max_num_seqs`)을 256→8로 줄이면 VRAM 사용과 처리량은 각각 어떻게 변하는가. 단일 사용자 서비스에서 이 교환이 왜 합리적인가.
3. (왜) OOM을 넘긴 뒤 엔진은 기동·health까지 OK였는데, 첫 추론 요청에서 `BatchPrefillWithPagedKVCache failed: invalid argument`로 500이 났다. health는 통과하고 추론만 깨지는 이유는 무엇인가(prefill이 언제 실행되는가).
4. (연결) GPU compute capability 7.5(Turing)가 왜 문제의 뿌리인가 — FlashAttention-2 요구 사양, 엔진의 백엔드 자동 선택, 그 대체 커널의 지원 범위를 잇는 3단 인과로 설명하라.
5. (경계) 백엔드를 env 변수로 강제하려 했지만 엔진 버전이 그 env를 무시했다. 외부 이미지의 동작을 설정으로 바꿀 수 없을 때 선택지는 무엇이며, 왜 "엔진 교체"가 싸게 끝났는가(소비자가 의존한 계약).
6. (경계) 튜닝 인자를 운영 compose에만 넣고 보존용 compose 사본에는 넣지 않았다. 나중에 그 사본으로 재시도하면 무슨 일이 생기는가.

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
