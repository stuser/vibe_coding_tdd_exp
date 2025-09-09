# Trip Splitter — 多人旅行分帳（FastAPI）

以小步快跑的 TDD 與 Tidy First 原則打造的一頁式旅行分帳系統：支援多幣別換匯、部分參與分攤，並以最少轉帳筆數結清。

- 目標情境：Alice、Bob、Carol 瑞美聯遊，旅程中輪流付款，回國要公平結清。
- 成功標準：單頁輸入與即時結果、JSON API、Decimal 高精度、可設定四捨五入、最少轉帳建議、餘額長條圖。


## 功能特色
- 多幣別：以 Base 幣別（預設 USD）統一結算，所有金額/匯率均採 `decimal.Decimal`。
- 部分參與：每筆支出可指定參與者與可選權重，非參與者不分攤。
- 最少轉帳：以貪婪演算法配對債權/債務，實務上達成最少筆數（n 位非零人時 ≤ n-1）。
- 輸出四捨五入：預設 HALF_UP 至 2 位；以「最後一位調整」確保餘額和為 0。
- API 與單頁 UI：`POST /api/settle` 回傳 balances/transfers/chart；首頁以 Chart.js 顯示長條圖。


## 專案結構
```
app/
  main.py                # FastAPI 啟動與路由掛載
  api.py                 # API 路由（/api/settle）
  domain/
    models.py            # Pydantic v2 模型（請求/回應）
    money.py             # Decimal 精度與換匯
    share.py             # 等分/權重分攤
    settle.py            # 餘額計算與最少轉帳（貪婪）
  web/
    templates/index.html # 單頁（Jinja2 + Chart.js）
    static/app.js        # [預留] HTMX/互動強化
  utils/
    errors.py            # 網域錯誤（422）
    validation.py        # 驗證輔助

tests/
  test_money.py
  test_share.py
  test_settle_unit.py
  test_settle_e2e.py

requirements.txt
pyproject.toml
README.md
AGENTS.md               # 需求與 TDD 指南
```
關鍵檔案：`app/main.py:1`、`app/api.py:1`、`app/domain/settle.py:1`、`app/domain/models.py:1`、`tests/test_settle_e2e.py:1`。


## 安裝與啟動
前置需求：Python 3.10+（建議 3.11）。

1) 建立虛擬環境並安裝套件
```
python -m venv .venv
# Windows
. .venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

2) 執行測試（TDD）
```
pytest -q
```

3) 啟動開發伺服器
```
uvicorn app.main:app --reload
```
- 健康檢查：GET http://localhost:8000/health → `{ "status": "ok" }`
- 單頁 UI：GET http://localhost:8000/


## API 說明
### POST /api/settle
- 以 Base 幣別統一結算，`rates` 表示「1 單位外幣 = x 單位 Base」。
- 預設 `rounding.mode = HALF_UP`、`rounding.places = 2`。

請求（範例）
```json
{
  "people": ["Alice", "Bob", "Carol"],
  "base_currency": "USD",
  "rates": {"USD": "1", "CHF": "1.10", "EUR": "1.08"},
  "rounding": {"mode": "HALF_UP", "places": 2},
  "expenses": [
    {"id": "e1", "payer": "Alice", "amount": "90",  "currency": "CHF", "participants": ["Alice", "Bob"], "note": "Swiss pass"},
    {"id": "e2", "payer": "Bob",   "amount": "150", "currency": "USD", "participants": ["Alice", "Bob", "Carol"], "note": "Hotel"},
    {"id": "e3", "payer": "Carol", "amount": "120", "currency": "EUR", "participants": ["Alice", "Carol"], "note": "Tour"}
  ],
  "optimize": "greedy"
}
```
回應（範例）
```json
{
  "base_currency": "USD",
  "balances": [
    {"person": "Alice", "amount": "-65.30"},
    {"person": "Bob",   "amount": "+50.50"},
    {"person": "Carol", "amount": "+14.80"}
  ],
  "transfers": [
    {"from": "Alice", "to": "Bob",   "amount": "50.50", "currency": "USD"},
    {"from": "Alice", "to": "Carol", "amount": "14.80", "currency": "USD"}
  ],
  "chart": {
    "labels": ["Alice", "Bob", "Carol"],
    "values": [-65.30, 50.50, 14.80]
  }
}
```
錯誤：資料驗證失敗回傳 422（例如金額 ≤ 0、缺少幣別匯率、參與者不在名單中、權重長度不符）。


## 商業規則與演算法
- 金額換匯：`amount_base = amount * rates[currency]`。
- 分攤：
  - 無 `weights` → 參與者等分；
  - 有 `weights` → 依相對權重分配（權重可任意比例，僅需 > 0）。
- 餘額定義（以 Base 計價）：付款人餘額 += 該筆金額；每位參與者餘額 -= 其分攤份額。
- 精度與四捨五入：
  - 全程使用 `Decimal`（`getcontext().prec = 28`），計算途中不提早四捨五入；
  - 輸出前以 HALF_UP 量化至 `places` 位（預設 2）；
  - 採「Largest Remainder」調整最後一位，保證餘額總和為 0。
- 最少轉帳（貪婪）：
  - 以四捨五入至分後的餘額，建立債權/債務集合；
  - 每回合配對最大債權人與最大債務人，轉帳較小者金額；
  - 結清一方後移除，直到任一集合為空；複雜度 O(n log n)，筆數 ≤ 非零人數 − 1。
- 精確最佳化（可選）：支援小 n 的 ILP/網路流以最少邊，但目前非預設（尚未實作）。


## TDD 循環與測試清單
- 採用 Red → Green → Refactor，小而頻繁的提交，結構先於行為（Tidy First）。
- 已覆蓋的測試方向：
  - Money：換匯、Decimal 無精度損失（`tests/test_money.py:1`）。
  - Share：等分、權重分攤（`tests/test_share.py:1`）。
  - Settle（單元）：混合幣別餘額、三人最少轉帳、多人貪婪結清、四捨五入與總和為 0、輸入驗證（`tests/test_settle_unit.py:1`）。
  - E2E：`POST /api/settle` 回傳結構與數值、錯誤 422、`GET /` 能渲染包含 Chart.js（`tests/test_settle_e2e.py:1`）。


## 開發工作流程
- 格式化與靜態分析
```
black .
ruff check .
mypy app
```
- 啟動與驗證
```
uvicorn app.main:app --reload
curl http://localhost:8000/health
```
- 推薦 Commit 訊息模板
  - Structural：`chore(structure): extract money module and add rounding policy`
  - Behavioral：`feat(settle): compute balances from mixed currencies`
  - Fix：`fix(validation): reject expenses with missing currency rate`
  - Refactor：`refactor(transfer): greedy pairing and remove duplication`


## 已知限制與後續路線圖
- `optimize=exact` 尚未實作（將限制在小 n，預計以 ILP/最少邊網路流）。若指定 `optimize="exact"`，API 將回傳 501，訊息為 `exact mode not implemented`。
- 單頁 UI 目前為最小可用，尚未串接 HTMX 表單互動與即時刷新。
- 依幣別決定顯示位數（如 JPY 0 位）可透過 `rounding.places` 調整，但尚未做幣別級策略表。

里程碑：
- M0：專案骨架、健康檢查、黑盒測試。
- M1：Money/Share/Balance 單元測試與實作、最少轉帳（貪婪）。
- M2：`POST /api/settle` E2E 打通。
- M3：一頁式 UI（HTMX + Chart.js）。
- M4（可選）：Exact 模式、小規模 ILP、CSV 匯入/匯出、在地化與幣符號。


## 設計準則摘要
- Decimal Only：嚴禁浮點參與金額與匯率計算。
- 驗證嚴謹：金額 > 0、幣別需在 `rates`、`participants ⊆ people`、`weights` 長度需相等且皆 > 0。
- 小函式、好命名：`compute_balances`、`suggest_transfers_greedy`、`split_shares`。
- 例外處理：資料錯誤以 422 回覆、訊息明確（`app/utils/errors.py:1`）。


## 範例（驗收）
- 換匯：CHF 90 × 1.10 = USD 99（Alice & Bob 各 49.50）
- USD 150 / 3 = 50（Alice, Bob, Carol）
- EUR 120 × 1.08 = USD 129.60（Alice & Carol 各 64.80）
- 餘額：Alice = −65.30、Bob = +50.50、Carol = +14.80
- 最少轉帳：Alice→Bob 50.50、Alice→Carol 14.80（共 2 筆）

---
若需我協助強化 UI（HTMX 表單、動態新增成員/支出、即時 Chart 更新），或加入 exact 最佳化，請告知需求與優先順序。
