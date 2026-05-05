# PowerBI ダッシュボード構築プロセス

品質分析装置の計測データを PowerBI でダッシュボード化するためのデータ処理・分析リポジトリ。

> **Note:** 本リポジトリは技術デモンストレーション用に独立して構築したものです。データはすべてダミーです。
---

## Overview

- 対象データ: 品質分析装置の計測出力（グレード分類 × 100 指標）
- サンプル数: 1,100 件 / 顧客数: 50 社
- DAX メジャー: 20 本超 / PowerQuery クエリ: 5 本 / ダッシュボードページ: 7 ページ
- 主要品質指標: 平均 58.1%  標準偏差 14.3%
- 計測値A: 平均 14.34%  標準偏差 0.71%

## Tech Stack

- **PowerBI** — DAX・PowerQuery・Python ビジュアル
- **Python** — データ探索・可視化・ML（scikit-learn）
  - `pandas` / `numpy` — データ処理
  - `matplotlib` / `seaborn` — 可視化
  - `scikit-learn` — PCA・K-means クラスタリング
  - `csv` / `utf-8-sig` — データ I/O

---

## PowerBI Dashboard

### Data Model

`品質分析装置データ.csv` をファクトテーブルとする 5 テーブルのスタースキーマ。
PowerQuery で `customer_id`・`region` を結合し、各ディメンションに直接接続。

```text
                             ┌─ 分析装置出力_詳細.csv  (1:1)  Cluster / PC1 / PC2
                             ├─ サンプル情報.csv       (1:1)  サンプル受付情報
品質分析装置データ.csv ──────┤
    (ファクト中心)           ├─ 顧客マスタ.csv         (多:1) customer_id で結合
                             └─ 地域マスタ            (多:1) region で結合 ※PowerBI 内部
                                                             東西 > 地方 > 地域区分 > 県（4 階層）
```

---

### PowerQuery データ取込・加工処理

クエリ 5 本でデータ統合・変換を実施。

#### 標準 データ取込ステップ（全クエリ共通）

- ソース読み込み → ヘッダー昇格 → 型変換 → フィルタ → 列リネーム

#### Python 統合ステップ（分析装置出力_詳細.csv）

PowerQuery 内で Python スクリプトを実行し、105 指標から次元削減・クラスタリングを行う：

```python
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

pca = PCA(n_components=2)
pcs = pca.fit_transform(X)          # → PC1, PC2

km = KMeans(n_clusters=6, n_init=10)
clusters = km.fit_predict(X)        # → Cluster (0–5)
```

出力列 `Cluster` / `PC1` / `PC2` をデータモデルに統合し、ビジュアル側でそのまま利用。

---

### DAX Measures

#### 統計メジャー

```dax
計測値B DW =
AVERAGEX('品質分析装置データ', '品質分析装置データ'[計測値B] * '品質分析装置データ'[計測値C])

計測値A CV% =
DIVIDE(
    STDEV.P('品質分析装置データ'[計測値A]),
    AVERAGE('品質分析装置データ'[計測値A])
)
```

#### 動的クロステーブル集計

```dax
地域別種別数 =
VAR SelectedValue = SELECTEDVALUE('顧客マスタ'[region])
RETURN
    CALCULATE(
        DISTINCTCOUNT('品質分析装置データ'[サンプル種別]),
        FILTER('顧客マスタ', '顧客マスタ'[region] = SelectedValue)
    )
```

地図ビジュアルの選択状態を `SELECTEDVALUE` で捕捉し、`CALCULATE + FILTER` でクロステーブル集計。

#### フォールバック計算列

```dax
サンプル種別 =
VAR v1 = '品質分析装置データ'[サンプル種別]
VAR v2 = '品質分析装置データ'[サンプル名推測]
VAR v3 = '品質分析装置データ'[サンプル名]
RETURN SWITCH(TRUE(),
    NOT(ISBLANK(v1)), v1,
    NOT(ISBLANK(v2)), v2,
    NOT(ISBLANK(v3)), v3,
    BLANK()
)
```

3 列の優先順位フォールバックで欠損データを補完。

その他: `種別あり比率` / `日付あり比率` / `ID_Aあり比率` / `計測値B/計測値A` など 20 本超。

---

### Dashboard Pages

#### KPI サマリー

スライサー（サンプル種別）連動。計測値 A・B・C・カウント指標を min / median / mean / max で表示。

![KPI summary](docs/images/dashboard_kpi.png)

---

#### 主要計測値 ヒストグラム（4 面）

計測値 A・B・C・カウント指標を同一スライサーで連動フィルタ。

![histograms](docs/images/dashboard_histograms.png)

---

#### 多系列散布図（Python ビジュアル）

PowerBI の Python ビジュアルとして `matplotlib` を使用。`twinx()` で二軸を実装。

```python
fig, ax = plt.subplots()
ax2 = ax.twinx()
ax.scatter(x, metric_a,    color='#33AADD', label='計測値A')
ax.scatter(x, metric_c,    color='#FF9955', label='計測値C')
ax.scatter(x, metric_b,    color='#DD5511', label='計測値B')
ax2.scatter(x, count,      color='#33CC44', label='個数')
```

![scatter](docs/images/dashboard_scatter.png)

---

#### データ品質ダッシュボード

記録項目（サンプル種別・日付・ID_A・ID_B）の有無比率を積み上げ棒グラフで可視化。

![data quality](docs/images/dashboard_quality.png)

---

#### 地域別分布

顧客マスタ（地域マスタ 4 階層）を使った地域別集計。

![region](docs/images/dashboard_region.png)

---

#### PCA + K-means クラスタリング

PowerQuery で生成した PC1 / PC2 / Cluster をバブルチャートで表示。品質グレード指標 6 次元の構造を可視化。

![PCA cluster](docs/images/dashboard_pca.png)

---

#### 箱ひげ図（サンプル種別比較）

サンプル種別ごとの計測値分布を箱ひげ図で比較。カスタムビジュアルを使用。

![boxplots](docs/images/dashboard_boxplots.png)

---

## Python Analysis

詳細なデータ探索・分析は [`quality_analysis.ipynb`](quality_analysis.ipynb) を参照。

### 品質グレード構成比 / 主要指標分布

![quality overview](docs/images/quality_overview.png)

Grade A 平均 58.1% / Grade G 33.9%。

### 計測値A 分析

![measurement analysis](docs/images/measurement_analysis.png)

計測値A 平均 14.34%（目標値 14.5%）。計測値A vs 計測値B: r = 0.044。

### 品質指標 相関マトリクス

![correlation heatmap](docs/images/correlation_heatmap.png)

Grade A vs Grade F: r = −0.06。

### 顧客規模分布

![customer overview](docs/images/customer_overview.png)

---

## Files

- `quality_analysis.ipynb` — データ探索・分析ノートブック
- `generate_dashboard_images.py` — ダッシュボード相当グラフ生成スクリプト
- `分析装置出力_詳細.csv` — 品質分析装置出力（匿名化済み・1,100 件・100 指標）
- `品質分析装置データ.csv` — 基本計測値（計測値 A・B・C）
- `サンプル情報.csv` — サンプル受付情報
- `顧客マスタ.csv` — 顧客・規模・地域データ
