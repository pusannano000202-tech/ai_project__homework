# TRD — 신경망 기초 인터랙티브 학습 앱
**Technical Requirements Document**

| 항목 | 내용 |
|------|------|
| 과목 | AI와 머신러닝 (PH2002141-033) |
| 주차 | Week 3 — 신경망 기초 |
| 제출자 | 김충현 |
| 제출일 | 2026-04-01 |
| 버전 | v1.0 |

---

## 1. 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| GUI 프레임워크 | PySide6 | 6.x |
| 수치 연산 | NumPy | ≥1.24 |
| 시각화 | Matplotlib (QtAgg 백엔드) | ≥3.7 |
| 언어 | Python | ≥3.10 |
| 패키지 관리 | uv | — |

### Matplotlib ↔ PySide6 연동

```python
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
```

`FigureCanvas`를 PySide6 위젯처럼 레이아웃에 추가하여 Qt 이벤트 루프 안에서 matplotlib 그래프를 렌더링한다.

---

## 2. 아키텍처

```
MainWindow (QMainWindow)
└── QTabWidget
    ├── Lab1Tab  (QWidget)
    ├── Lab2Tab  (QWidget)
    ├── Lab3Tab  (QWidget)
    ├── Lab4Tab  (QWidget)
    └── Lab5Tab  (QWidget)
```

각 `Tab` 클래스는 독립적인 모델 클래스와 `FigureCanvas`를 포함한다.

---

## 3. 모델 클래스 설계

### 3-1. PerceptronLogic (Lab 1)

```
클래스: PerceptronLogic
속성:
  - weights: ndarray(2,)   — 랜덤 초기화
  - bias:    float          — 랜덤 초기화
  - lr:      float          — 학습률

메서드:
  - predict(x) → int       — 계단 함수 적용
  - train(X, y, epochs)    — 퍼셉트론 학습 규칙 적용
    w ← w + η·(y - ŷ)·x
    b ← b + η·(y - ŷ)
```

### 3-2. SimpleNetwork (Lab 3)

```
클래스: SimpleNetwork
구조: 2 → 3 → 1  (고정, 시드 지원)
활성화: ReLU(은닉) + Sigmoid(출력)

메서드:
  - forward(X) → ndarray   — z1, a1, z2, a2 계산 후 저장
    z1 = X @ W1 + b1
    a1 = ReLU(z1)
    z2 = a1 @ W2 + b2
    a2 = σ(z2)
```

### 3-3. MLPModel (Lab 4)

```
클래스: MLPModel
구조: 2 → hidden → 1  (동적)
초기화: Xavier (√2/n_in)

메서드:
  - forward(X) → ndarray
  - train_step(X, y) → float loss
    역전파 (MSE loss + Sigmoid 출력):
    dz2 = (a2 - y)
    dW2 = (1/m) a1ᵀ @ dz2
    da1 = dz2 @ W2ᵀ
    dz1 = da1 ⊙ σ'(z1)
    dW1 = (1/m) Xᵀ @ dz1
    W ← W - α·dW
```

### 3-4. UniversalApproximator (Lab 5)

```
클래스: UniversalApproximator
구조: 1 → n_hidden → 1
초기화: Xavier Uniform

지원 활성화 함수: tanh / relu / sigmoid
역전파: 일반 SGD (배치 전체)
```

---

## 4. 공통 수학 함수

```python
sigmoid(x)         = 1 / (1 + exp(-clip(x, -500, 500)))
sigmoid_deriv(x)   = sigmoid(x) · (1 - sigmoid(x))
relu(x)            = max(0, x)
relu_deriv(x)      = where(x > 0, 1, 0)
tanh_fn(x)         = np.tanh(x)
tanh_deriv(x)      = 1 - tanh(x)²
leaky_relu(x, α)   = where(x > 0, x, α·x)   α=0.01
leaky_relu_deriv   = where(x > 0, 1, α)
```

---

## 5. UI 컴포넌트 상세

### 공통 패턴

각 탭의 레이아웃:
```
QVBoxLayout
├── QLabel (탭 제목)
├── QHBoxLayout (컨트롤: 스핀박스, 콤보박스, 버튼)
├── FigureCanvas (matplotlib 그래프)
└── QTextEdit (결과/설명 텍스트, ReadOnly)
```

### 컨트롤 위젯 목록

| Lab | 위젯 | 파라미터 | 범위 |
|-----|------|----------|------|
| 1 | QDoubleSpinBox | 학습률 | 0.01 ~ 1.0 |
| 1 | QSpinBox | 에폭 | 10 ~ 2,000 |
| 2 | QSpinBox | x 범위 | 3 ~ 15 |
| 3 | QDoubleSpinBox × 2 | x₁, x₂ | -2.0 ~ 2.0 |
| 3 | QPushButton | 가중치 재초기화 | — |
| 4 | QSpinBox | 은닉 뉴런 | 2 ~ 16 |
| 4 | QDoubleSpinBox | 학습률 | 0.01 ~ 2.0 |
| 4 | QSpinBox | 에폭 | 100 ~ 50,000 |
| 5 | QComboBox | 활성화 함수 | tanh/relu/sigmoid |
| 5 | QSpinBox | 에폭 | 500 ~ 20,000 |

---

## 6. 시각화 명세

| Lab | 서브플롯 | 내용 |
|-----|----------|------|
| 1 | 1×3 | AND / OR / XOR 결정 경계 (`contourf`) |
| 2 | 2×2 | 함수 비교 / Gradient / Sigmoid vs Tanh / ReLU vs Leaky |
| 3 | 2×2 | 네트워크 다이어그램 / Layer1 막대 / Layer2 수평막대 / 수식 |
| 4 | 1×3 | Loss 곡선(log) / 결정 경계 컬러맵 / 은닉층 활성화 히트맵 |
| 5 | 3×3 | 함수(행) × 뉴런수(열) 근사 결과 |

---

## 7. 한글 폰트 처리

```python
def setup_korean_font():
    font_list = [f.name for f in fm.fontManager.ttflist]
    for font in ["Malgun Gothic", "Gulim", "Batang", "AppleGothic"]:
        if font in font_list:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False
```

앱 시작 시 1회 호출. 폰트가 없으면 matplotlib 기본 폰트로 fallback.

---

## 8. 실행 방법

```bash
# 의존성 확인
uv pip install pyside6 numpy matplotlib

# 실행
cd week3
uv run hw3_pyside6_app.py
```

---

## 9. 파일 구조

```
week3/
├── hw3_pyside6_app.py     ← 메인 앱 (본 제출물)
├── PRD.md                 ← 제품 요구사항 문서
├── TRD.md                 ← 기술 요구사항 문서 (이 파일)
├── 01_perceptron.py       ← 원본 Lab 1
├── 02_activation_functions.py
├── 03_forward_propagation.py
├── 04_mlp_numpy.py
├── 05_universal_approximation.py
└── outputs/               ← 원본 스크립트 출력 이미지
```

---

## 10. 알려진 제약 및 한계

| 제약 | 설명 |
|------|------|
| 단일 스레드 | 학습 중 UI 업데이트는 `QApplication.processEvents()`로 처리 (Lab 4/5) |
| CPU 전용 | NumPy 기반으로 GPU 미사용 |
| 모델 비저장 | 학습 결과는 앱 종료 시 소멸 |
| Lab 5 소요 시간 | 50뉴런 × 3함수 × 5,000에폭 기준 약 10~30초 |
