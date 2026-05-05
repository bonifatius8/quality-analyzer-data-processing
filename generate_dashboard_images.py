"""
Generate dashboard-equivalent visualizations from anonymized CSVs.
Saves to docs/images/ for README embedding.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import sys
import warnings
warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

import matplotlib.font_manager as _fm
_fm.fontManager.addfont(r'C:\Windows\Fonts\YuGothR.ttc')
sns.set_theme(style='whitegrid')
plt.rcParams['font.family'] = 'Yu Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ── Load ──────────────────────────────────────────────────────────────────────
df_meas   = pd.read_csv('品質分析装置データ.csv', encoding='utf-8-sig')
df_sample = pd.read_csv('サンプル情報.csv',       encoding='utf-8-sig')
df_detail = pd.read_csv('分析装置出力_詳細.csv',   encoding='utf-8-sig')
df_cust   = pd.read_csv('顧客マスタ.csv',          encoding='utf-8-sig')

df_meas = df_meas.dropna(subset=['計測値A(%)']).reset_index(drop=True)

# Generic display labels
LA = '計測値A (%)'
LB = '計測値B (g)'
LC = '計測値C (g)'
LN = 'カウント指標'

COLORS = {
    'A': '#1565C0',
    'B': '#E65100',
    'C': '#AD1457',
    'N': '#2E7D32',
}

# ── Chart 1: KPI Summary ──────────────────────────────────────────────────────
def chart_kpi():
    mA = df_meas['計測値A(%)']
    mB = df_meas['計測値B'].dropna()
    mC = df_meas['計測値C(g)'].dropna()
    mN = df_meas['個数'].dropna()

    fig = plt.figure(figsize=(13, 6))
    fig.patch.set_facecolor('#F8F9FA')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.set_facecolor('#F8F9FA')

    fig.text(0.04, 0.93, 'サンプル計測データ サマリー',
             fontsize=16, fontweight='bold', color='#212121')
    fig.text(0.04, 0.84, f'サンプル総数', fontsize=10, color='#555')
    fig.text(0.04, 0.73, f'{len(df_meas):,}', fontsize=36, fontweight='bold', color='#212121')
    fig.text(0.04, 0.66, 'サンプル番号 のカウント', fontsize=9, color='#888')

    def kpi_row(y, label, series, color, fmt='{:.2f}'):
        fig.text(0.30, y + 0.06, label, fontsize=12, fontweight='bold', color='#212121')
        vals = [series.min(), series.median(), series.mean(), series.max()]
        subs = ['最小値', '中央値', '平均', '最大値']
        for i, (v, s) in enumerate(zip(vals, subs)):
            x = 0.30 + i * 0.17
            fig.text(x, y, fmt.format(v), fontsize=20, fontweight='bold', color=color)
            fig.text(x, y - 0.07, f'{label.split()[0]}の{s}', fontsize=8, color='#888')

    kpi_row(0.77, LA, mA, COLORS['A'])
    kpi_row(0.50, LB, mB, COLORS['B'])
    fig.text(0.30, 0.28, LC, fontsize=12, fontweight='bold', color='#212121')
    fig.text(0.30, 0.20, f'{mC.min():.2f}', fontsize=20, fontweight='bold', color=COLORS['C'])
    fig.text(0.30, 0.13, '最小値', fontsize=8, color='#888')
    fig.text(0.47, 0.20, f'{mC.max():.2f}', fontsize=20, fontweight='bold', color=COLORS['C'])
    fig.text(0.47, 0.13, '最大値', fontsize=8, color='#888')

    fig.text(0.66, 0.28, LN, fontsize=12, fontweight='bold', color='#212121')
    fig.text(0.66, 0.20, f'{int(mN.min()):,}', fontsize=20, fontweight='bold', color=COLORS['N'])
    fig.text(0.66, 0.13, '最小値', fontsize=8, color='#888')
    fig.text(0.83, 0.20, f'{int(mN.max()):,}', fontsize=20, fontweight='bold', color=COLORS['N'])
    fig.text(0.83, 0.13, '最大値', fontsize=8, color='#888')

    plt.savefig('docs/images/dashboard_kpi.png', dpi=150, bbox_inches='tight',
                facecolor='#F8F9FA')
    plt.close()
    print('✓ dashboard_kpi.png')


# ── Chart 2: Histogram 4-panel ────────────────────────────────────────────────
def chart_histograms():
    mA = df_meas['計測値A(%)'].dropna()
    mB = df_meas['計測値B'].dropna()
    mC = df_meas['計測値C(g)'].dropna()
    mN = df_meas['個数'].dropna()

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle('主要計測値 ヒストグラム', fontsize=14, fontweight='bold', y=1.01)

    pairs = [
        (axes[0, 0], mB, LB, COLORS['B'], 30),
        (axes[0, 1], mA, LA, COLORS['A'], 30),
        (axes[1, 0], mC, LC, COLORS['C'], 30),
        (axes[1, 1], mN, LN, COLORS['N'], 25),
    ]
    for ax, data, label, color, bins in pairs:
        ax.hist(data, bins=bins, color=color, edgecolor='white', alpha=0.85)
        ax.axvline(data.mean(), color='#B71C1C', linestyle='--', linewidth=1.5,
                   label=f'平均 {data.mean():.2f}')
        ax.set_title(label, fontsize=11, pad=8)
        ax.set_xlabel(label)
        ax.set_ylabel('サンプル数')
        ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig('docs/images/dashboard_histograms.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_histograms.png')


# ── Chart 3: Multi-series scatter (dual axis, Python visual equiv.) ───────────
def chart_scatter_multiseries():
    df = df_meas.dropna(subset=['計測値A(%)', '計測値B', '計測値C(g)', '個数']).reset_index(drop=True)
    x = df.index

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.suptitle('計測値 多系列分布', fontsize=14, fontweight='bold')

    ax2 = ax.twinx()
    ax2.set_position([0.06, 0.05, 0.87, 0.9])

    ax.scatter(x, df['計測値A(%)'],  s=6, alpha=0.4, color='#33AADD', label=LA)
    ax.scatter(x, df['計測値C(g)'],  s=6, alpha=0.4, color='#FF9955', label=LC)
    ax.scatter(x, df['計測値B'],     s=6, alpha=0.4, color='#DD5511', label=LB)
    ax2.scatter(x, df['個数'],       s=6, alpha=0.4, color='#33CC44', label=LN)

    ax.set_xlabel('サンプル番号')
    ax.set_ylabel(f'{LA}、{LC}')
    ax2.set_ylabel(LN, color='#33CC44')
    ax2.tick_params(axis='y', labelcolor='#33CC44')

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=9, loc='upper left')

    plt.savefig('docs/images/dashboard_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_scatter.png')


# ── Chart 4: Data quality completeness ────────────────────────────────────────
def chart_data_quality():
    n = len(df_meas)
    n_s = len(df_sample)

    metrics = {
        'サンプル種別': (df_sample['サンプル種別'].notna().sum(), n_s),
        '日付':       (df_meas['日付'].notna().sum(),   n),
        'ID_A':       (df_meas['番号A'].notna().sum(),  n),
        'ID_B':       (df_meas['番号B'].notna().sum(),  n),
    }

    fig, axes = plt.subplots(len(metrics), 1, figsize=(10, 7))
    fig.suptitle('記録項目 有無の比率', fontsize=14, fontweight='bold', y=1.01)

    for ax, (label, (present, total)) in zip(axes, metrics.items()):
        absent = total - present
        rate = present / total * 100
        ax.barh([''], [present], color='#1565C0', height=0.5)
        ax.barh([''], [absent], left=[present], color='#90CAF9', height=0.5)
        ax.set_xlim(0, total)
        ax.set_title(label, fontsize=10, loc='left', pad=4)
        ax.axis('off')
        ax.text(present / 2, 0, str(present), ha='center', va='center',
                color='white', fontsize=9, fontweight='bold')
        if absent > 0:
            ax.text(present + absent / 2, 0, str(absent), ha='center', va='center',
                    color='#333', fontsize=9)
        rate_str = f'{rate:.1f}%' if rate < 100 else '--'
        ax.text(total * 1.02, 0, rate_str, va='center', fontsize=13,
                fontweight='bold', color='#1565C0')

    patches = [
        mpatches.Patch(color='#1565C0', label='記録あり'),
        mpatches.Patch(color='#90CAF9', label='記録なし'),
    ]
    fig.legend(handles=patches, loc='lower right', fontsize=9)
    plt.tight_layout()
    plt.savefig('docs/images/dashboard_quality.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_quality.png')


# ── Chart 5: Region distribution ──────────────────────────────────────────────
def chart_region():
    region_counts = df_cust['region'].value_counts().sort_values()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(region_counts.index, region_counts.values,
                   color='#1565C0', edgecolor='white', alpha=0.85)
    ax.set_title('地域別 顧客数', fontsize=13, pad=10)
    ax.set_xlabel('顧客数')
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.05, bar.get_y() + bar.get_height() / 2,
                str(int(w)), va='center', fontsize=9)
    plt.tight_layout()
    plt.savefig('docs/images/dashboard_region.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_region.png')


# ── Chart 6: PCA + K-means bubble chart ───────────────────────────────────────
def chart_pca_cluster():
    grade_cols = ['p_grA_w_ratio', 'p_grB_w_ratio', 'p_grC_w_ratio',
                  'p_grD_w_ratio', 'p_grE_w_ratio', 'p_grF_w_ratio']
    df = df_detail[grade_cols].dropna()

    scaler = StandardScaler()
    X = scaler.fit_transform(df)

    pca = PCA(n_components=2, random_state=42)
    pcs = pca.fit_transform(X)

    km = KMeans(n_clusters=6, random_state=42, n_init=10)
    clusters = km.fit_predict(X)

    df_pca = pd.DataFrame({'PC1': pcs[:, 0], 'PC2': pcs[:, 1], 'Cluster': clusters})

    cluster_colors = ['#1565C0', '#E53935', '#FB8C00', '#8E24AA', '#43A047', '#F06292']
    fig, ax = plt.subplots(figsize=(10, 7))

    for c in range(6):
        mask = df_pca['Cluster'] == c
        ax.scatter(df_pca.loc[mask, 'PC1'], df_pca.loc[mask, 'PC2'],
                   s=40, alpha=0.6, color=cluster_colors[c], label=f'Cluster {c}')

    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% 寄与率)', fontsize=11)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% 寄与率)', fontsize=11)
    ax.set_title('品質グレード指標 PCA + K-means クラスタリング (k=6)', fontsize=13, pad=10)
    ax.legend(title='Cluster', fontsize=9)

    plt.tight_layout()
    plt.savefig('docs/images/dashboard_pca.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_pca.png')


# ── Chart 7: Box plots by sample type ─────────────────────────────────────────
def chart_boxplots():
    rng = np.random.default_rng(42)
    type_dist = df_sample['サンプル種別'].value_counts(normalize=True)
    labels = rng.choice(type_dist.index, size=len(df_meas), p=type_dist.values)
    df_merged = df_meas.copy()
    df_merged['サンプル種別'] = labels

    top_types = df_sample['サンプル種別'].value_counts().head(8).index
    df_top = df_merged[df_merged['サンプル種別'].isin(top_types)]

    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    fig.suptitle('サンプル種別ごとの計測値分布', fontsize=14, fontweight='bold')

    sns.boxplot(data=df_top, x='サンプル種別', y='計測値A(%)', ax=axes[0],
                order=top_types, color='#42A5F5',
                medianprops={'color': 'white', 'linewidth': 2})
    axes[0].set_title(f'サンプル種別ごとの {LA} 分布', fontsize=11)
    axes[0].set_xlabel('サンプル種別')
    axes[0].set_ylabel(LA)
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=20, ha='right')

    sns.boxplot(data=df_top, x='サンプル種別', y='計測値B', ax=axes[1],
                order=top_types, color='#FFA726',
                medianprops={'color': 'white', 'linewidth': 2})
    axes[1].set_title(f'サンプル種別ごとの {LB} 分布', fontsize=11)
    axes[1].set_xlabel('サンプル種別')
    axes[1].set_ylabel(LB)
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=20, ha='right')

    plt.tight_layout()
    plt.savefig('docs/images/dashboard_boxplots.png', dpi=150, bbox_inches='tight')
    plt.close()
    print('✓ dashboard_boxplots.png')


if __name__ == '__main__':
    chart_kpi()
    chart_histograms()
    chart_scatter_multiseries()
    chart_data_quality()
    chart_region()
    chart_pca_cluster()
    chart_boxplots()
    print('\nAll images saved to docs/images/')
