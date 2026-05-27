# Storage

## 方針

- RAIDは使わない。
- 2本のNVMeを役割分担する。
- Ubuntuインストーラで作成済みのLVMは維持する。
- k3s/containerdのデータ肥大化に備え、`/var/lib/rancher`をrootから分離する。
- モデル、Hugging Faceキャッシュ、Prometheusデータは`/opt`側に置く。

当初はLVMなしを想定していたが、既存の正常なOSインストールを維持しつつ必要な分離を実現できるため、現行LVM構成を採用する。

## 現在のレイアウト

```text
/dev/nvme0n1 (1TB NVMe) -> システム用
   ├── /boot/efi              (1GB, vfat)
   ├── /boot                  (2GB, ext4)
   └── ubuntu-vg (LVM)
       ├── /                  (100GB, ext4)
       ├── /var/lib/rancher   (300GB, ext4)
       └── 空き               (約528GB)

/dev/nvme1n1 (1TB NVMe) -> モデル・データ用
   └── /opt                   (約916GB, ext4)
       ├── /opt/models
       ├── /opt/huggingface-cache
       └── /opt/prometheus-data
```

## 永続マウント

| マウントポイント | デバイス |
|------------------|----------|
| `/` | `/dev/mapper/ubuntu--vg-ubuntu--lv` |
| `/var/lib/rancher` | `/dev/mapper/ubuntu--vg-rancher` |
| `/opt` | `/dev/nvme1n1p1` |

`/etc/fstab`はUUID指定で管理する。

## 用途

| パス | 用途 |
|------|------|
| `/` | OS、ホームディレクトリ、基本ツール |
| `/var/lib/rancher` | k3sデータ、containerdイメージ |
| `/opt/models` | LLMモデル本体 |
| `/opt/huggingface-cache` | Hugging Faceキャッシュ |
| `/opt/prometheus-data` | Prometheusデータ |

## 監視閾値

```yaml
disk_alerts:
  usage_warning: 75%
  usage_critical: 90%
  nvme_lifetime_warning: 80%
```

LLMモデル本体はHugging Faceから再ダウンロード可能なため、バックアップ対象外とする。
