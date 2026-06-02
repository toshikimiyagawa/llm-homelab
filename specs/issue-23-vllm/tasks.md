# Tasks: issue-23-vllm

## 実装タスク（順序付き）

- [ ] **T1: `roles/vllm/defaults/main.yml` を作成する** 対応AC: AC1〜AC7
  - `mkdir -p roles/vllm/defaults roles/vllm/tasks roles/vllm/templates` を実行
  - 内容:
    ```yaml
    ---
    vllm_namespace: vllm
    vllm_image_tag: latest
    vllm_model: Qwen/Qwen3-30B-A3B
    vllm_served_model_name: default
    vllm_gpu_uuid: GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a
    vllm_models_host_path: /opt/models
    vllm_domain: "vllm.{{ base_domain }}"
    vllm_gpu_memory_utilization: "0.90"
    vllm_port: 8000
    ```

- [ ] **T2: `roles/vllm/templates/vllm-deployment.yml.j2` を作成する** 対応AC: AC2, AC3
  - 内容:
    ```yaml
    ---
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: vllm
      namespace: {{ vllm_namespace }}
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: vllm
      template:
        metadata:
          labels:
            app: vllm
        spec:
          runtimeClassName: nvidia
          containers:
            - name: vllm
              image: "vllm/vllm-openai:{{ vllm_image_tag }}"
              args:
                - "--model"
                - "{{ vllm_model }}"
                - "--served-model-name"
                - "{{ vllm_served_model_name }}"
                - "--gpu-memory-utilization"
                - "{{ vllm_gpu_memory_utilization }}"
                - "--port"
                - "{{ vllm_port | string }}"
              env:
                - name: NVIDIA_VISIBLE_DEVICES
                  value: "{{ vllm_gpu_uuid }}"
                - name: HF_HOME
                  value: /models
              ports:
                - containerPort: {{ vllm_port }}
              resources:
                limits:
                  nvidia.com/gpu: "1"
              readinessProbe:
                httpGet:
                  path: /health
                  port: {{ vllm_port }}
                initialDelaySeconds: 300
                periodSeconds: 30
                failureThreshold: 20
              volumeMounts:
                - name: models
                  mountPath: /models
                  readOnly: true
          volumes:
            - name: models
              hostPath:
                path: {{ vllm_models_host_path }}
                type: Directory
    ```

- [ ] **T3: `roles/vllm/templates/vllm-service.yml.j2` を作成する** 対応AC: AC4, AC5
  - 内容:
    ```yaml
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: vllm
      namespace: {{ vllm_namespace }}
    spec:
      selector:
        app: vllm
      ports:
        - port: 80
          targetPort: {{ vllm_port }}
      type: ClusterIP
    ```

- [ ] **T4: `roles/vllm/templates/vllm-ingress.yml.j2` を作成する** 対応AC: AC5, AC6
  - 内容:
    ```yaml
    ---
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
      name: vllm
      namespace: {{ vllm_namespace }}
      annotations:
        cert-manager.io/cluster-issuer: letsencrypt-prod
    spec:
      ingressClassName: traefik
      rules:
        - host: "{{ vllm_domain }}"
          http:
            paths:
              - path: /
                pathType: Prefix
                backend:
                  service:
                    name: vllm
                    port:
                      number: 80
      tls:
        - secretName: vllm-tls
          hosts:
            - "{{ vllm_domain }}"
    ```

- [ ] **T5: `roles/vllm/tasks/main.yml` を作成する** 対応AC: AC1〜AC6
  - 以下のタスクを順番に記述する:

  **① Namespace 作成**
  ```yaml
  ---
  - name: Ensure vllm namespace exists
    ansible.builtin.command: k3s kubectl create namespace {{ vllm_namespace }}
    register: vllm_ns_result
    changed_when: vllm_ns_result.rc == 0
    failed_when: >-
      vllm_ns_result.rc != 0 and
      'already exists' not in vllm_ns_result.stderr
    become: true
    tags:
      - vllm
  ```

  **② Deployment 適用**
  ```yaml
  - name: Deploy vLLM manifests
    block:
      - name: Render vLLM Deployment manifest
        ansible.builtin.template:
          src: vllm-deployment.yml.j2
          dest: /tmp/vllm-deployment.yml
          mode: "0600"

      - name: Apply vLLM Deployment
        ansible.builtin.command: k3s kubectl apply -f /tmp/vllm-deployment.yml
        register: vllm_deployment_apply
        changed_when: >-
          'configured' in vllm_deployment_apply.stdout or
          'created' in vllm_deployment_apply.stdout
    always:
      - name: Remove vLLM Deployment manifest from /tmp
        ansible.builtin.file:
          path: /tmp/vllm-deployment.yml
          state: absent
    become: true
    tags:
      - vllm
  ```

  **③ Service 適用**
  ```yaml
  - name: Deploy vLLM Service
    block:
      - name: Render vLLM Service manifest
        ansible.builtin.template:
          src: vllm-service.yml.j2
          dest: /tmp/vllm-service.yml
          mode: "0600"

      - name: Apply vLLM Service
        ansible.builtin.command: k3s kubectl apply -f /tmp/vllm-service.yml
        register: vllm_service_apply
        changed_when: >-
          'configured' in vllm_service_apply.stdout or
          'created' in vllm_service_apply.stdout
    always:
      - name: Remove vLLM Service manifest from /tmp
        ansible.builtin.file:
          path: /tmp/vllm-service.yml
          state: absent
    become: true
    tags:
      - vllm
  ```

  **④ Ingress 適用**
  ```yaml
  - name: Deploy vLLM Ingress
    block:
      - name: Render vLLM Ingress manifest
        ansible.builtin.template:
          src: vllm-ingress.yml.j2
          dest: /tmp/vllm-ingress.yml
          mode: "0600"

      - name: Apply vLLM Ingress
        ansible.builtin.command: k3s kubectl apply -f /tmp/vllm-ingress.yml
        register: vllm_ingress_apply
        changed_when: >-
          'configured' in vllm_ingress_apply.stdout or
          'created' in vllm_ingress_apply.stdout
    always:
      - name: Remove vLLM Ingress manifest from /tmp
        ansible.builtin.file:
          path: /tmp/vllm-ingress.yml
          state: absent
    become: true
    tags:
      - vllm
  ```

  **⑤ Deployment 起動待機（モデルロードに最大30分を想定）**
  ```yaml
  - name: Wait for vLLM Deployment rollout
    ansible.builtin.command: >-
      k3s kubectl -n {{ vllm_namespace }}
      rollout status deployment/vllm
      --timeout=120s
    register: vllm_rollout
    retries: 15
    delay: 120
    until: vllm_rollout.rc == 0
    changed_when: false
    become: true
    tags:
      - vllm
  ```

  **⑥ verify タスク（受け入れ基準確認）**
  ```yaml
  - name: Verify vLLM pod is Running
    ansible.builtin.command: >-
      k3s kubectl -n {{ vllm_namespace }} get pod
      -l app=vllm
      -o jsonpath='{.items[0].status.phase}'
    register: vllm_phase
    failed_when: vllm_phase.stdout != "Running"
    changed_when: false
    become: true
    tags:
      - vllm
      - verify

  - name: Verify GPU UUID is set in Deployment
    ansible.builtin.shell: |
      set -o pipefail
      k3s kubectl -n {{ vllm_namespace }} get deployment vllm -o json | \
        grep -q '{{ vllm_gpu_uuid }}'
    args:
      executable: /bin/bash
    changed_when: false
    become: true
    tags:
      - vllm
      - verify

  - name: Verify vLLM API responds to /v1/models
    ansible.builtin.shell: |
      set -o pipefail
      k3s kubectl -n {{ vllm_namespace }} exec \
        "$(k3s kubectl -n {{ vllm_namespace }} get pod \
          -l app=vllm \
          -o jsonpath='{.items[0].metadata.name}')" \
        -- wget -q -O- http://localhost:{{ vllm_port }}/v1/models | \
        grep -q '"object":"list"'
    args:
      executable: /bin/bash
    changed_when: false
    become: true
    tags:
      - vllm
      - verify

  - name: Verify vLLM TLS certificate is Ready
    ansible.builtin.command: >-
      k3s kubectl -n {{ vllm_namespace }} get certificate vllm-tls
      -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
    register: vllm_cert
    failed_when: vllm_cert.stdout != "True"
    changed_when: false
    become: true
    tags:
      - vllm
      - verify
  ```

- [ ] **T6: `playbooks/09-vllm.yml` を作成する** 対応AC: AC1〜AC7
  - 内容:
    ```yaml
    ---
    - name: Deploy vLLM inference server
      hosts: llm_servers
      become: true
      gather_facts: true
      roles:
        - vllm
    ```

- [ ] **T7: `docs/software-stack.md` の vLLM セクションを更新する** 対応AC: AC1
  - 「推論エンジン」セクション以降に以下を追記・更新する:

    ```markdown
    ### vLLM

    k3s Deployment として `vllm` namespace に導入する。

    | 項目 | 設定値 |
    |------|--------|
    | image | `vllm/vllm-openai:latest` |
    | GPU | RTX Pro 6000（UUID: `GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a`） |
    | モデル | `/opt/models` に手動配置（例: `Qwen/Qwen3-30B-A3B`） |
    | API | OpenAI 互換（`/v1/chat/completions`, `/v1/models`） |

    アクセス URL（要 Tailscale 接続）:

    - API: `https://vllm.solvelio.com/v1`

    事前に Cloudflare で以下の DNS A レコードを手動登録する（Tailscale IP）:

    - `vllm.solvelio.com` → `100.107.191.51`

    Ansible での適用:

    ```bash
    ansible-playbook playbooks/09-vllm.yml --vault-password-file ~/.vault_pass
    ```
    ```

- [ ] **T8: ansible-lint と yamllint を実行し無エラーを確認する** 対応AC: AC7
  - 実行コマンド:
    ```bash
    ansible-lint roles/vllm/ playbooks/09-vllm.yml
    yamllint roles/vllm/ playbooks/09-vllm.yml
    ```
  - `var-naming[no-role-prefix]` は既存 role と同様の既知の非ブロッキング警告として許容する
  - それ以外のエラーは修正してから次に進む

## テスト（受入条件との対応）

- [ ] AC1（冪等性）→ `09-vllm.yml` を 2 回実行し 2 回目は changed=0
- [ ] AC2（Pod Running）→ verify タスク（vllm pod Running チェック）
- [ ] AC3（GPU UUID 設定）→ verify タスク（Deployment の NVIDIA_VISIBLE_DEVICES 確認）
- [ ] AC4（API 応答）→ verify タスク（`/v1/models` HTTP チェック）
- [ ] AC5（HTTPS アクセス）→ `https://vllm.solvelio.com/v1/models` にブラウザ確認（手動）
- [ ] AC6（TLS 有効）→ verify タスク（Certificate Ready チェック）
- [ ] AC7（lint）→ T8 の lint 実行結果が無エラー

## 完了の定義

- [ ] 全 AC 対応の確認手順が実行結果で追跡できる
- [ ] `ansible-lint` / `yamllint`（変更対象）を実行した結果を提示できる
- [ ] verify フェーズで sdd-reviewer を実行して合格する
