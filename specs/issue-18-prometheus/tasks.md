# Tasks: issue-18-prometheus

## 実装タスク（順序付き）

- [ ] **T1: vault.yml にシークレットを追加する** 対応AC: AC7
  - `inventory/group_vars/all/vault.yml` を `ansible-vault edit --vault-password-file ~/.vault_pass` で開き以下を追記する:
    ```yaml
    cloudflare_api_token: "<Cloudflare API Token（DNS 編集権限）>"
    grafana_admin_password: "<任意の管理者パスワード>"
    ```
  - Cloudflare API Token は https://dash.cloudflare.com/profile/api-tokens で「Edit zone DNS」権限で発行する

- [ ] **T2: vars.yml に prometheus 変数を追加する** 対応AC: AC1〜AC6
  - `inventory/group_vars/all/vars.yml` に以下を追記する:
    ```yaml
    base_domain: "yourdomain.com"  # 実際のドメインに変更
    ```

- [ ] **T3: `roles/prometheus/defaults/main.yml` を作成する** 対応AC: AC1〜AC8
  - 内容:
    ```yaml
    ---
    prometheus_manifest_dir: /var/lib/rancher/k3s/server/manifests
    prometheus_namespace: monitoring
    cert_manager_namespace: cert-manager
    cert_manager_version: v1.16.3
    kube_prometheus_stack_version: "68.4.0"
    dcgm_exporter_version: "3.3.9"
    prometheus_retention: 30d
    prometheus_storage_size: 50Gi
    letsencrypt_email: toshi402@gmail.com
    letsencrypt_server: https://acme-v02.api.letsencrypt.org/directory
    grafana_domain: "grafana.{{ base_domain }}"
    prometheus_domain: "prometheus.{{ base_domain }}"
    ```
  - バージョンは最新を確認する:
    - cert-manager: https://github.com/cert-manager/cert-manager/releases
    - kube-prometheus-stack: https://github.com/prometheus-community/helm-charts/releases
    - dcgm-exporter: https://github.com/NVIDIA/dcgm-exporter/releases

- [ ] **T4: `roles/prometheus/templates/cluster-issuer.yml.j2` を作成する** 対応AC: AC6, AC7
  - 内容:
    ```yaml
    ---
    apiVersion: v1
    kind: Secret
    metadata:
      name: cloudflare-api-token
      namespace: {{ cert_manager_namespace }}
    type: Opaque
    stringData:
      api-token: "{{ cloudflare_api_token }}"
    ---
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-prod
    spec:
      acme:
        server: {{ letsencrypt_server }}
        email: {{ letsencrypt_email }}
        privateKeySecretRef:
          name: letsencrypt-prod-key
        solvers:
          - dns01:
              cloudflare:
                apiTokenSecretRef:
                  name: cloudflare-api-token
                  key: api-token
    ```

- [ ] **T5: `roles/prometheus/templates/prometheus-pv.yml.j2` を作成する** 対応AC: AC2
  - 内容:
    ```yaml
    ---
    apiVersion: v1
    kind: PersistentVolume
    metadata:
      name: prometheus-data-pv
    spec:
      capacity:
        storage: {{ prometheus_storage_size }}
      accessModes:
        - ReadWriteOnce
      persistentVolumeReclaimPolicy: Retain
      storageClassName: ""
      hostPath:
        path: /opt/prometheus-data
        type: DirectoryOrCreate
    ```

- [ ] **T6: `roles/prometheus/tasks/main.yml` を作成する** 対応AC: AC1〜AC8
  - 以下のタスクを順番に記述する:

  **① cert-manager HelmChart 配置**
  ```yaml
  ---
  - name: Deploy cert-manager HelmChart addon
    ansible.builtin.copy:
      dest: "{{ prometheus_manifest_dir }}/cert-manager.yaml"
      owner: root
      group: root
      mode: "0600"
      content: |
        apiVersion: helm.cattle.io/v1
        kind: HelmChart
        metadata:
          name: cert-manager
          namespace: kube-system
        spec:
          repo: https://charts.jetstack.io
          chart: cert-manager
          version: "{{ cert_manager_version }}"
          targetNamespace: "{{ cert_manager_namespace }}"
          createNamespace: true
          set:
            crds.enabled: "true"
    become: true
    tags:
      - prometheus
  ```

  **② cert-manager 起動待機**
  ```yaml
  - name: Wait for cert-manager namespace
    ansible.builtin.command: k3s kubectl get namespace {{ cert_manager_namespace }}
    register: cert_manager_ns
    retries: 60
    delay: 5
    until: cert_manager_ns.rc == 0
    changed_when: false
    become: true
    tags:
      - prometheus

  - name: Wait for cert-manager webhook rollout
    ansible.builtin.command: >-
      k3s kubectl -n {{ cert_manager_namespace }}
      rollout status deployment/cert-manager-webhook
      --timeout=300s
    register: cert_manager_rollout
    changed_when: false
    become: true
    tags:
      - prometheus

  - name: Wait for ClusterIssuer CRD to be established
    ansible.builtin.command: k3s kubectl get crd clusterissuers.cert-manager.io
    register: clusterissuer_crd
    retries: 30
    delay: 10
    until: clusterissuer_crd.rc == 0
    changed_when: false
    become: true
    tags:
      - prometheus
  ```

  **③ ClusterIssuer 適用（no_log 必須）**
  ```yaml
  - name: Render Cloudflare Secret and ClusterIssuer manifest
    ansible.builtin.template:
      src: cluster-issuer.yml.j2
      dest: /tmp/cluster-issuer.yml
      mode: "0600"
    no_log: true
    become: true
    tags:
      - prometheus

  - name: Apply Cloudflare Secret and ClusterIssuer
    ansible.builtin.command: k3s kubectl apply -f /tmp/cluster-issuer.yml
    register: clusterissuer_apply
    changed_when: >-
      'configured' in clusterissuer_apply.stdout or
      'created' in clusterissuer_apply.stdout
    no_log: true
    become: true
    tags:
      - prometheus

  - name: Remove ClusterIssuer manifest from /tmp
    ansible.builtin.file:
      path: /tmp/cluster-issuer.yml
      state: absent
    become: true
    tags:
      - prometheus
  ```

  **④ Prometheus PersistentVolume 適用**
  ```yaml
  - name: Render Prometheus PV manifest
    ansible.builtin.template:
      src: prometheus-pv.yml.j2
      dest: /tmp/prometheus-pv.yml
      mode: "0644"
    become: true
    tags:
      - prometheus

  - name: Apply Prometheus PersistentVolume
    ansible.builtin.command: k3s kubectl apply -f /tmp/prometheus-pv.yml
    register: prometheus_pv_apply
    changed_when: >-
      'configured' in prometheus_pv_apply.stdout or
      'created' in prometheus_pv_apply.stdout
    become: true
    tags:
      - prometheus

  - name: Remove Prometheus PV manifest from /tmp
    ansible.builtin.file:
      path: /tmp/prometheus-pv.yml
      state: absent
    become: true
    tags:
      - prometheus
  ```

  **⑤ kube-prometheus-stack HelmChart 配置（no_log 必須）**
  ```yaml
  - name: Deploy kube-prometheus-stack HelmChart addon
    ansible.builtin.copy:
      dest: "{{ prometheus_manifest_dir }}/kube-prometheus-stack.yaml"
      owner: root
      group: root
      mode: "0600"
      content: |
        apiVersion: helm.cattle.io/v1
        kind: HelmChart
        metadata:
          name: kube-prometheus-stack
          namespace: kube-system
        spec:
          repo: https://prometheus-community.github.io/helm-charts
          chart: kube-prometheus-stack
          version: "{{ kube_prometheus_stack_version }}"
          targetNamespace: "{{ prometheus_namespace }}"
          createNamespace: true
          valuesContent: |-
            alertmanager:
              enabled: false
            grafana:
              adminPassword: "{{ grafana_admin_password }}"
              ingress:
                enabled: true
                ingressClassName: traefik
                annotations:
                  cert-manager.io/cluster-issuer: letsencrypt-prod
                hosts:
                  - "{{ grafana_domain }}"
                tls:
                  - secretName: grafana-tls
                    hosts:
                      - "{{ grafana_domain }}"
            prometheus:
              ingress:
                enabled: true
                ingressClassName: traefik
                annotations:
                  cert-manager.io/cluster-issuer: letsencrypt-prod
                hosts:
                  - "{{ prometheus_domain }}"
                tls:
                  - secretName: prometheus-tls
                    hosts:
                      - "{{ prometheus_domain }}"
              prometheusSpec:
                retention: "{{ prometheus_retention }}"
                serviceMonitorSelectorNilUsesHelmValues: false
                serviceMonitorSelector: {}
                serviceMonitorNamespaceSelector: {}
                storageSpec:
                  volumeClaimTemplate:
                    spec:
                      storageClassName: ""
                      volumeName: prometheus-data-pv
                      accessModes:
                        - ReadWriteOnce
                      resources:
                        requests:
                          storage: "{{ prometheus_storage_size }}"
    no_log: true
    become: true
    tags:
      - prometheus
  ```

  **⑥ kube-prometheus-stack 起動待機**
  ```yaml
  - name: Wait for monitoring namespace
    ansible.builtin.command: k3s kubectl get namespace {{ prometheus_namespace }}
    register: monitoring_ns
    retries: 60
    delay: 5
    until: monitoring_ns.rc == 0
    changed_when: false
    become: true
    tags:
      - prometheus

  - name: Wait for Prometheus StatefulSet rollout
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }}
      rollout status statefulset/prometheus-kube-prometheus-stack-prometheus
      --timeout=600s
    register: prometheus_rollout
    changed_when: false
    become: true
    tags:
      - prometheus

  - name: Wait for Grafana Deployment rollout
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }}
      rollout status deployment/kube-prometheus-stack-grafana
      --timeout=300s
    register: grafana_rollout
    changed_when: false
    become: true
    tags:
      - prometheus
  ```

  **⑦ DCGM Exporter HelmChart 配置**
  ```yaml
  - name: Deploy DCGM Exporter HelmChart addon
    ansible.builtin.copy:
      dest: "{{ prometheus_manifest_dir }}/dcgm-exporter.yaml"
      owner: root
      group: root
      mode: "0600"
      content: |
        apiVersion: helm.cattle.io/v1
        kind: HelmChart
        metadata:
          name: dcgm-exporter
          namespace: kube-system
        spec:
          repo: https://nvidia.github.io/dcgm-exporter/helm-charts
          chart: dcgm-exporter
          version: "{{ dcgm_exporter_version }}"
          targetNamespace: "{{ prometheus_namespace }}"
          createNamespace: false
          valuesContent: |-
            runtimeClassName: nvidia
            tolerations:
              - key: nvidia.com/gpu
                operator: Exists
                effect: NoSchedule
            serviceMonitor:
              enabled: true
    become: true
    tags:
      - prometheus

  - name: Wait for DCGM Exporter DaemonSet rollout
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }}
      rollout status daemonset/dcgm-exporter
      --timeout=300s
    register: dcgm_rollout
    changed_when: false
    become: true
    tags:
      - prometheus
  ```

  **⑧ verify タスク（受け入れ基準確認）**
  ```yaml
  - name: Verify Prometheus pod is Running
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }} get pod
      -l app.kubernetes.io/name=prometheus
      -o jsonpath='{.items[0].status.phase}'
    register: prometheus_phase
    failed_when: prometheus_phase.stdout != "Running"
    changed_when: false
    become: true
    tags:
      - prometheus
      - verify

  - name: Verify Grafana pod is Running
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }} get pod
      -l app.kubernetes.io/name=grafana
      -o jsonpath='{.items[0].status.phase}'
    register: grafana_phase
    failed_when: grafana_phase.stdout != "Running"
    changed_when: false
    become: true
    tags:
      - prometheus
      - verify

  - name: Verify node-exporter metrics are scraped by Prometheus
    ansible.builtin.shell: |
      set -o pipefail
      k3s kubectl -n {{ prometheus_namespace }} exec \
        "$(k3s kubectl -n {{ prometheus_namespace }} get pod \
          -l app.kubernetes.io/name=prometheus \
          -o jsonpath='{.items[0].metadata.name}')" \
        -c prometheus -- \
        wget -q -O- \
        'http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22node-exporter%22%7D' | \
        grep -q '"value"'
    args:
      executable: /bin/bash
    changed_when: false
    become: true
    tags:
      - prometheus
      - verify

  - name: Verify DCGM Exporter metrics are scraped by Prometheus
    ansible.builtin.shell: |
      set -o pipefail
      k3s kubectl -n {{ prometheus_namespace }} exec \
        "$(k3s kubectl -n {{ prometheus_namespace }} get pod \
          -l app.kubernetes.io/name=prometheus \
          -o jsonpath='{.items[0].metadata.name}')" \
        -c prometheus -- \
        wget -q -O- \
        'http://localhost:9090/api/v1/query?query=up%7Bjob%3D%22dcgm-exporter%22%7D' | \
        grep -q '"value"'
    args:
      executable: /bin/bash
    changed_when: false
    become: true
    tags:
      - prometheus
      - verify

  - name: Verify Grafana TLS certificate is Ready
    ansible.builtin.command: >-
      k3s kubectl -n {{ prometheus_namespace }} get certificate grafana-tls
      -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
    register: grafana_cert
    failed_when: grafana_cert.stdout != "True"
    changed_when: false
    become: true
    tags:
      - prometheus
      - verify
  ```

- [ ] **T7: `playbooks/08-prometheus.yml` を作成する** 対応AC: AC1〜AC8
  - 内容:
    ```yaml
    ---
    - name: Configure Prometheus monitoring stack
      hosts: llm01
      become: true
      roles:
        - prometheus
    ```

- [ ] **T8: ansible-lint と yamllint を実行し無エラーを確認する** 対応AC: AC8
  - 実行コマンド:
    ```bash
    ansible-lint roles/prometheus/ playbooks/08-prometheus.yml
    yamllint roles/prometheus/ playbooks/08-prometheus.yml
    ```
  - エラーがあれば修正してから次に進む

- [ ] **T9: `docs/software-stack.md` を更新する** 対応AC: AC1
  - 「周辺サービス」セクションの Prometheus / Grafana の記述を実装内容に合わせて更新する:
    - デプロイ方式（k3s HelmChart addon）
    - アクセス URL（`https://grafana.<base_domain>`、`https://prometheus.<base_domain>`）
    - chart バージョン
    - `ansible-playbook playbooks/08-prometheus.yml` コマンド

## テスト（受入条件との対応）

- [ ] AC1（冪等性）→ `08-prometheus.yml` を 2 回実行し 2 回目は HelmChart copy タスク以外 changed=0
- [ ] AC2（Pod Running）→ verify タスク（Prometheus / Grafana pod Running チェック）
- [ ] AC3（Grafana HTTPS アクセス）→ `https://grafana.<base_domain>` にブラウザでアクセスしてログイン画面確認
- [ ] AC4（node-exporter up）→ verify タスク（Prometheus API クエリ）
- [ ] AC5（DCGM up）→ verify タスク（Prometheus API クエリ）
- [ ] AC6（TLS 有効）→ verify タスク（Certificate Ready チェック）
- [ ] AC7（シークレット非露出）→ `no_log: true` を vault 関連タスクに付与、ansible-playbook 出力に `cloudflare_api_token` / `grafana_admin_password` が含まれないことを確認
- [ ] AC8（lint）→ T8 の lint 実行結果が無エラー

## 完了の定義

- [ ] 全 AC 対応の確認手順が実行結果で追跡できる
- [ ] `ansible-lint` / `yamllint`（変更対象）を実行した結果を提示できる
- [ ] verify フェーズで sdd-reviewer を実行して合格する
