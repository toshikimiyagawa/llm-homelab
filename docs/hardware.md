# Hardware

## 確定構成

確認日: 2026-05-28（`llm01` / Ubuntu上で確認）

| 区分 | 内容 |
|------|------|
| ホスト名 | `llm01` |
| CPU | AMD Ryzen 9 3950X（16C32T、TDP 105W、PPT 142W） |
| マザーボード | ASUS ROG Strix X570-E Gaming |
| BIOS | American Megatrends Inc. 5031（2025-01-13） |
| RAM | 128GB DDR4（32GB x 4、G.Skill F4-3200C16-32GVK、現在2666 MT/s動作） |
| GPU 1 | NVIDIA RTX Pro 6000 Blackwell Workstation Edition（600Wフル版、96GB VRAM） |
| GPU 2 | NVIDIA GeForce GTX 1650（4GB VRAM） |
| ストレージ | NVMe SSD 1TB x 2（CSSD-M2B1TPG3VNF系） |
| ケース | Antec Flux Pro（無印、通常版） |
| 電源 | Seasonic PRIME TX-1600（通常版、80+ Titanium、ATX 3.1、12V-2x6、12年保証） |
| CPUクーラー | Noctua NH-D15（空冷、初代 or D15S） |

## 実機確認状況

- OS: Ubuntu 26.04 LTS
- カーネル: Linux 7.0.0-15-generic
- Secure Boot: Disabled（`mokutil --sb-state`で確認）
- IOMMU: IOMMUグループ作成あり（`/sys/kernel/iommu_groups`で確認）
- NVIDIAドライバ: 導入済み（580.159.03、open kernel module）
- 現在のGPU: GTX 1650のみ装着、NVIDIAドライバで認識済み
- GTX 1650 UUID: `GPU-c6ed26bf-5bbd-7607-07e3-174c54a4e233`
- RTX Pro 6000: 未装着。2026-05-29または2026-05-30に装着予定
- Re-Size BAR / Above 4G Decoding: BIOS設定で有効化必須。RTX Pro 6000装着後にOS側で再確認する

## GPU配置

```text
PCIe x16_1 (CPU直結 x16)       -> RTX Pro 6000
PCIe x16_2 (CPU直結 x8)        -> 空
PCIe x16_3 (チップセット x4)   -> GTX 1650
```

理由:

- RTX Pro 6000はx16フルレーンを維持する。
- GTX 1650は軽量推論用途なのでx4で十分。
- GPU間に空きスロットを設け、熱干渉を避ける。

RTX Pro 6000装着後に確認すること:

```bash
lspci -nn | grep -Ei 'vga|3d|display|nvidia'
nvidia-smi
nvidia-smi -L
sudo lspci -vv -s <RTX_BUS_ID> | grep -E 'LnkCap|LnkSta'
```

## サイズ・クリアランス

| 項目 | サイズ | ケース対応 | 余裕 |
|------|--------|------------|------|
| CPUクーラー高さ | 165mm | 170mm | 5mm |
| PSU長さ | 210mm | 300mm（HDDケージ撤去時） | 90mm |
| GPU長さ | 304mm | 455mm | 151mm |

## ケース・電源方針

- HDDケージは撤去する。TX-1600 210mm搭載のため必須。
- ボトムファンは必要に応じて追加する。
- 3.5インチHDDは内蔵しない。必要ならUSB 3.0ドックまたはNASで対応する。
- TX-1600のセミファンレスモードはOFFにし、コンデンサ寿命のため常時回転させる。
- 12V-2x6は純正ケーブルを使い、急角度で曲げない。

## 設置環境

- 実家の空き部屋に設置する。
- エアコンなし。夏場の室温35度を想定する。
- 24時間稼働。
- 隣の部屋まで爆音でなければ静音性は妥協する。
- 物理アクセスは年数回程度。

冷却、信頼性、メンテ頻度最小化を優先する。
