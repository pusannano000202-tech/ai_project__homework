# PRD — 신경망 기초 인터랙티브 학습 앱
**Product Requirements Document**

| 항목 | 내용 |
|------|------|
| 과목 | AI와 머신러닝 (PH2002141-033) |
| 주차 | Week 3 — 신경망 기초 (Neural Networks Fundamentals) |
| 제출자 | 김충현 |
| 제출일 | 2026-04-01 |
| 버전 | v1.0 |

---

## 1. 배경 및 목적

Week 3 수업에서 학습한 신경망 기초 개념(퍼셉트론, 활성화 함수, 순전파, 역전파, Universal Approximation)을 **PySide6 GUI 앱**으로 구현하여, 파라미터를 실시간으로 조작하며 학습 효과를 체험할 수 있도록 한다.

기존 콘솔·matplotlib 기반 스크립트(5개 `.py` 파일)를 단일 통합 GUI 앱으로 재구현하는 것이 핵심 목표이다.

---

## 2. 사용자 및 사용 환경

| 항목 | 내용 |
|------|------|
| 주 사용자 | 신경망을 처음 배우는 수강생 |
| 실행 환경 | Windows 11, Python 3.10+, PySide6, NumPy, Matplotlib |
| 실행 방법 | `uv run hw3_pyside6_app.py` |

---

## 3. 기능 요구사항

### FR-01: 탭 기반 멀티 랩 UI

앱은 5개의 탭으로 구성되며, 각 탭은 하나의 신경망 개념 실습에 대응한다.

| 탭 번호 | 탭 이름 | 대응 Lab |
|---------|---------|----------|
| 1 | Perceptron | `01_perceptron.py` |
| 2 | Activation Functions | `02_activation_functions.py` |
| 3 | Forward Propagation | `03_forward_propagation.py` |
| 4 | MLP / Backpropagation | `04_mlp_numpy.py` |
| 5 | Universal Approximation | `05_universal_approximation.py` |

---

### FR-02: Lab 1 — 퍼셉트론

- AND / OR / XOR 게이트를 단일 퍼셉트론으로 학습
- **학습률(LR)** 과 **에폭** 수를 GUI에서 조절 가능
- 결정 경계(Decision Boundary)를 컬러맵으로 시각화
- XOR의 선형 분리 불가능성을 직관적으로 보여줌
- 학습 결과(오류 개수)를 텍스트로 출력

**수용 기준:**
- AND/OR: 정확도 100%
- XOR: 오류 ≥ 1개 (선형 분리 불가)

---

### FR-03: Lab 2 — 활성화 함수 비교

- Sigmoid, Tanh, ReLU, Leaky ReLU 함수와 미분(Gradient) 동시 비교
- **x 범위** 슬라이더로 x축 조절 가능
- 2×2 서브플롯: ① 함수 비교 ② Gradient 비교 ③ Sigmoid vs Tanh ④ ReLU vs Leaky ReLU
- 각 함수의 특징(장단점, 권장 용도)을 텍스트로 안내

---

### FR-04: Lab 3 — 순전파 시각화

- 2→3→1 신경망 구조를 다이어그램으로 표시 (원 + 연결선)
- **x₁, x₂** 입력값을 실시간으로 변경하여 순전파 결과 즉시 갱신
- **가중치 재초기화** 버튼으로 다양한 가중치 탐색 가능
- z₁ → a₁(ReLU) → z₂ → a₂(Sigmoid) 각 단계 값 시각화
- 수식 요약 패널 표시

---

### FR-05: Lab 4 — MLP + Backpropagation

- XOR 문제를 MLP로 해결
- 조절 가능 파라미터:
  - 은닉층 뉴런 수 (2~16)
  - 학습률 (0.01~2.0)
  - 에폭 수 (100~50,000)
- 학습 후 출력:
  - Training Loss 그래프 (log 스케일)
  - 결정 경계 컬러맵
  - 은닉층 활성화 히트맵
  - 입력별 예측값 표

**수용 기준:**
- 기본 파라미터(hidden=4, lr=0.5, epoch=10,000)로 정확도 100% 달성

---

### FR-06: Lab 5 — Universal Approximation

- Sine Wave, Step Function, Complex Function 세 가지 함수 근사
- 뉴런 수 3 / 10 / 50 비교 (3×3 서브플롯)
- **활성화 함수** (tanh/relu/sigmoid) 선택 가능
- **에폭 수** 조절 가능
- MSE(Mean Squared Error)로 근사 품질 수치 표시

---

## 4. 비기능 요구사항

| ID | 요구사항 |
|----|----------|
| NFR-01 | Lab 1~4는 5초 이내 실행 완료 |
| NFR-02 | Lab 5는 30초 이내 실행 완료 (50뉴런×3함수×5,000 에폭) |
| NFR-03 | 창 크기 1200×820 기본값, 리사이즈 지원 |
| NFR-04 | 한글 폰트 자동 감지 (Malgun Gothic → Gulim 순 fallback) |
| NFR-05 | 학습 중 버튼 비활성화로 중복 실행 방지 |

---

## 5. 범위 외 (Out of Scope)

- GPU 가속 (순수 NumPy만 사용)
- 모델 저장/불러오기
- YouTube 시청 인증
- 실제 데이터셋(MNIST 등) 사용

---

## 6. 성공 기준

1. 5개 탭 모두 오류 없이 실행
2. Lab 4에서 XOR 정확도 100% 달성
3. Lab 5에서 50뉴런이 3뉴런보다 낮은 MSE 달성
4. 파라미터 변경 후 즉시 결과 갱신
