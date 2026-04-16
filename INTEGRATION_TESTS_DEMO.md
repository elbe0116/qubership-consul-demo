# Документация по Integration Tests Demo

## Обзор

Данная документация описывает архитектуру и реализацию системы интеграционного тестирования с возможностью публикации результатов в S3-совместимое хранилище.

---

## 1. Репозиторий `qubership-docker-integration-tests-demo`

**Путь:** `C:\Users\elbe0116\Documents\qubership-docker-integration-tests-demo`

**Назначение:** Базовый Docker-образ с библиотекой для запуска Robot Framework тестов и модульной системой публикации результатов в S3.

### Структура репозитория

```
qubership-docker-integration-tests-demo/
├── Dockerfile                    # Основной Dockerfile для базового образа
├── requirements.txt              # Python зависимости
├── library/                      # Библиотека методов для тестов
│   └── integration_library_builtIn/
│       ├── PlatformLibrary.py    # Основная библиотека для K8s
│       ├── KubernetesClient.py   # Клиент Kubernetes API
│       ├── OpenShiftClient.py    # Клиент OpenShift API
│       ├── MonitoringLibrary.py  # Библиотека для работы с Prometheus
│       ├── FileSystemS3.py       # Работа с S3
│       └── S3BackupLibrary.py    # Бэкапы в S3
└── scripts/                      # Скрипты запуска и публикации
    ├── docker-entrypoint.sh      # Точка входа контейнера
    ├── analyze_result.py         # Анализ результатов тестов
    ├── write_status.py           # Запись статуса в K8s CR
    ├── robot_tags_resolver.py    # Резолвер тегов тестов
    └── adapter-S3/               # 🆕 ДОБАВЛЕННЫЕ СКРИПТЫ для S3
```

### 🆕 Добавленные скрипты `adapter-S3/`

| Скрипт | Назначение |
|--------|-----------|
| **`adapter-S3-entrypoint.sh`** | Главный координатор - объединяет все модули и управляет workflow: инициализация → мониторинг загрузки → запуск тестов → финализация |
| **`init.sh`** | Инициализация окружения: настройка S3 credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY), создание temp директорий |
| **`test-runner.sh`** | Модуль запуска тестов: создаёт директории для Allure, очищает credentials перед тестами, запускает `start_tests.sh` |
| **`start_tests.sh`** | Непосредственно запускает Robot Framework с параметрами для Allure listener и сохранения отчётов |
| **`upload-monitor.sh`** | Мониторинг и загрузка в S3: использует `inotifywait` для отслеживания новых файлов и `s5cmd` для upload в реальном времени |
| **`native-report.sh`** | Сохранение нативных отчётов Robot Framework в attachments для загрузки |
| **`git-clone.sh`** | Клонирование репозитория с тестами (для внешних тестов) |
| **`runtime-setup.sh`** | Настройка runtime окружения (PYTHONPATH и т.д.) |
| **`email-notification/`** | Скрипты для генерации email-уведомлений о результатах |

### Детальное описание скриптов

#### `adapter-S3-entrypoint.sh`
Главная точка входа для запуска тестов с S3 интеграцией:
```bash
# Workflow:
1. init_environment        # Инициализация S3 credentials и директорий
2. start_upload_monitoring # Запуск фонового мониторинга файлов (если S3 включен)
3. run_tests "$@"          # Запуск Robot Framework тестов
4. finalize_upload         # Финальная синхронизация с S3 (если S3 включен)
```

#### `init.sh`
Инициализация окружения:
- Вычисляет текущую дату/время для путей в S3
- Проверяет наличие `ATP_STORAGE_BUCKET` (флаг включения S3)
- Настраивает AWS credentials из переменных окружения
- Создаёт временные директории

#### `upload-monitor.sh`
Мониторинг и загрузка файлов:
- Использует `inotifywait` для отслеживания новых файлов в реальном времени
- Поддерживает два метода: `sync` (синхронизация директории) и `cp` (копирование файлов)
- Использует `s5cmd` для быстрой загрузки в S3
- Генерирует URL для просмотра результатов

#### `start_tests.sh`
Запуск Robot Framework:
```bash
robot --output "${OUTPUT_DIR}/output.xml" \
      --log "${TMP_DIR}/log.html" \
      --report "${TMP_DIR}/report.html" \
      --listener "allure_robotframework;${TMP_DIR}/allure-results" \
      "$@"
```

### 🆕 Добавленные переменные окружения

| Переменная | Описание | Обязательность |
|-----------|----------|----------------|
| `ATP_STORAGE_PROVIDER` | Тип S3 провайдера: `aws`, `minio`, `s3` | Да (если S3 включен) |
| `ATP_STORAGE_SERVER_URL` | URL S3 API (например `https://s3.us-east-1.amazonaws.com`) | Да (если S3 включен) |
| `ATP_STORAGE_SERVER_UI_URL` | URL UI для просмотра файлов в S3 | Нет |
| `ATP_STORAGE_BUCKET` | Имя бакета. **Если пустой - S3 интеграция отключена** | **Это флаг включения S3** |
| `ATP_STORAGE_REGION` | Регион S3 (обязателен для AWS) | Да (для AWS) |
| `ATP_STORAGE_USERNAME` | Access Key для S3 | Да (если S3 включен) |
| `ATP_STORAGE_PASSWORD` | Secret Key для S3 | Да (если S3 включен) |
| `ATP_REPORT_VIEW_UI_URL` | URL для просмотра Allure отчётов | Нет |
| `ENVIRONMENT_NAME` | Имя окружения (для организации путей в S3) | Нет |
| `ENABLE_JIRA_INTEGRATION` | Флаг интеграции с Jira | Нет |
| `UPLOAD_METHOD` | Метод загрузки: `sync` (по умолчанию) или `cp` | Нет |

### 🆕 Флаг включения/выключения S3

**Флаг:** `ATP_STORAGE_BUCKET`

| Значение | Результат |
|----------|-----------|
| **Пустой/не задан** | S3 отключен, результаты остаются локально |
| **Указан bucket** | S3 включен, требуются credentials |

Проверка в коде:
```bash
# В adapter-S3-entrypoint.sh:
if [[ -n "${ATP_STORAGE_BUCKET}" ]]; then
    start_upload_monitoring
else
    echo "⚠️ Skipping upload monitoring (S3 integration disabled)"
fi
```

### 🆕 Изменения в Dockerfile

```dockerfile
# Добавлен s5cmd для быстрой загрузки в S3
RUN echo 'https://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories \
    && apk add --update --no-cache s5cmd

# Добавлен inotify-tools для мониторинга файлов
RUN apk add --update --no-cache inotify-tools

# Копирование скриптов adapter-S3
COPY scripts/adapter-S3 ${ROBOT_HOME}/scripts/adapter-S3
RUN chmod -R 775 ${ROBOT_HOME}/scripts/adapter-S3
```

### Библиотека `PlatformLibrary`

Основная Robot Framework библиотека с методами для:

**Deployments:**
- `Get Deployment Entity` / `Get Deployment Entities`
- `Create Deployment Entity` / `Delete Deployment Entity`
- `Scale Up/Down Deployment Entity`
- `Set Replicas For Deployment Entity`

**StatefulSets:**
- `Get Stateful Set` / `Get Stateful Sets`
- `Get Stateful Set Replicas Count` / `Get Stateful Set Ready Replicas Count`
- `Scale Up/Down Stateful Set`
- `Set Replicas For Stateful Set`

**Pods:**
- `Get Pod` / `Get Pods`
- `Delete Pod By Pod Name` / `Delete Pod By Pod Ip`
- `Execute Command In Pod`
- `Get Pod Names By Service Name`

**Services, ConfigMaps, Secrets:**
- `Get Service` / `Create Service` / `Delete Service`
- `Get Config Map` / `Create Config Map From File`
- `Get Secret` / `Create Secret` / `Patch Secret`

**Custom Resources (CRDs):**
- `Get Custom Resource` / `Get Custom Resources`
- `Create/Replace/Patch/Delete Namespaced Custom Object`

**Ingress/Routes (OpenShift):**
- `Get Ingress` / `Get Ingresses` / `Get Ingress Url`
- `Get Route` / `Get Routes` / `Get Route Url`

---

## 2. Репозиторий `qubership-consul-demo`

**Путь:** `C:\Users\elbe0116\Documents\qubership-consul-demo`

**Назначение:** Helm chart для установки Consul + интеграционные тесты. Использует базовый образ из `qubership-docker-integration-tests-demo`.

### Ключевые файлы

```
qubership-consul-demo/
├── .github/workflows/
│   └── install_consul_to_aws.yaml     # 🆕 Workflow для установки в AWS
├── charts/helm/consul-service/
│   ├── values.yaml                    # 🆕 Добавлены параметры integrationTests.atpStorage
│   └── templates/integration_tests/
│       ├── deployment.yaml            # 🆕 Добавлены env для S3
│       └── atp-storage-secret.yaml    # 🆕 Secret для S3 credentials
└── integration-tests/docker/
    └── Dockerfile                     # Наследуется от базового образа
```

### 🆕 Workflow `install_consul_to_aws.yaml`

**Расположение:** `.github/workflows/install_consul_to_aws.yaml`

**Что делает:**
1. Настраивает kubectl и helm
2. Конфигурирует AWS credentials
3. Подключается к EKS кластеру
4. Устанавливает Consul через helm с параметрами для integration tests

**Шаги workflow:**
```yaml
steps:
  - Checkout Code
  - Setup kubectl (v1.32.0)
  - Setup Helm
  - Verify tools
  - Configure AWS credentials
  - Configure kubeconfig for EKS
  - Verify cluster access
  - Install Consul (helm install с параметрами)
```

**Передаваемые параметры для S3:**
```yaml
helm install --namespace=${{ vars.CONSUL_INSTALL_NAMESPACE }} \
  --create-namespace \
  -f ./charts/helm/consul-service/values.yaml \
  consul-service ./charts/helm/consul-service \
  --set integrationTests.atpStorage.username=${{ secrets.ATP_STORAGE_USERNAME }} \
  --set integrationTests.atpStorage.password=${{ secrets.ATP_STORAGE_PASSWORD }} \
  --set integrationTests.atpStorage.provider=s3 \
  --set integrationTests.atpStorage.serverUrl=${{ vars.ATP_STORAGE_SERVER_URL }} \
  --set integrationTests.atpStorage.serverUiUrl=${{ vars.ATP_STORAGE_SERVER_UI_URL }} \
  --set integrationTests.atpStorage.bucket=${{ vars.ATP_STORAGE_BUCKET }} \
  --set integrationTests.atpStorage.region=${{ vars.AWS_REGION || 'us-east-1' }} \
  --set integrationTests.atpReportViewUiUrl=${{ vars.ATP_REPORT_VIEW_UI_URL }} \
  --set integrationTests.environmentName=${{ vars.ENVIRONMENT_NAME || github.event.inputs.environment }}
```

### 🆕 Добавленные параметры в `values.yaml`

**Расположение:** `charts/helm/consul-service/values.yaml`

```yaml
integrationTests:
  enabled: true
  image: ghcr.io/netcracker/qubership-docker-integration-tests:main
  
  # 🆕 ATP Storage для S3
  atpStorage:
    # S3 provider type: aws, minio, s3
    provider: ""
    # S3 API server URL (e.g., https://s3.amazonaws.com or https://minio.example.com)
    serverUrl: ""
    # S3 UI URL for browsing results (e.g., https://minio.example.com)
    serverUiUrl: ""
    # S3 bucket name. If empty - S3 integration is disabled and results stay local
    bucket: ""
    # S3 region (required for AWS S3)
    region: ""
    # S3 credentials (will be stored in secret)
    username: ""
    password: ""

  # URL for viewing Allure reports (e.g., https://reports.example.com)
  atpReportViewUiUrl: ""

  # Environment name for organizing test results path in S3
  environmentName: ""

  # Enable Jira integration (writes to marker file for external processing)
  enableJiraIntegration: false
```

### 🆕 Deployment template (`deployment.yaml`)

**Расположение:** `charts/helm/consul-service/templates/integration_tests/deployment.yaml`

Добавлены environment variables в контейнер:
```yaml
env:
  # ATP Storage variables for S3 integration
  - name: ATP_STORAGE_PROVIDER
    value: {{ .Values.integrationTests.atpStorage.provider | quote }}
  - name: ATP_STORAGE_SERVER_URL
    value: {{ .Values.integrationTests.atpStorage.serverUrl | quote }}
  - name: ATP_STORAGE_SERVER_UI_URL
    value: {{ .Values.integrationTests.atpStorage.serverUiUrl | quote }}
  - name: ATP_STORAGE_BUCKET
    value: {{ .Values.integrationTests.atpStorage.bucket | quote }}
  - name: ATP_STORAGE_REGION
    value: {{ .Values.integrationTests.atpStorage.region | quote }}
  {{- if .Values.integrationTests.atpStorage.bucket }}
  - name: ATP_STORAGE_USERNAME
    valueFrom:
      secretKeyRef:
        name: {{ template "consul-integration-tests.name" . }}-atp-storage-secret
        key: username
  - name: ATP_STORAGE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ template "consul-integration-tests.name" . }}-atp-storage-secret
        key: password
  {{- end }}
  - name: ATP_REPORT_VIEW_UI_URL
    value: {{ .Values.integrationTests.atpReportViewUiUrl | quote }}
  - name: ENVIRONMENT_NAME
    value: {{ .Values.integrationTests.environmentName | quote }}
  - name: ENABLE_JIRA_INTEGRATION
    value: {{ .Values.integrationTests.enableJiraIntegration | quote }}
```

### 🆕 ATP Storage Secret (`atp-storage-secret.yaml`)

**Расположение:** `charts/helm/consul-service/templates/integration_tests/atp-storage-secret.yaml`

```yaml
{{- if and .Values.integrationTests.enabled .Values.integrationTests.atpStorage.bucket }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ template "consul-integration-tests.name" . }}-atp-storage-secret
type: Opaque
data:
  username: {{ .Values.integrationTests.atpStorage.username | b64enc | quote }}
  password: {{ .Values.integrationTests.atpStorage.password | b64enc | quote }}
{{- end }}
```

### Dockerfile для Consul Integration Tests

**Расположение:** `integration-tests/docker/Dockerfile`

```dockerfile
FROM ghcr.io/netcracker/qubership-docker-integration-tests:main

ENV ROBOT_OUTPUT=/opt/robot/output \
    SERVICE_CHECKER_SCRIPT=${ROBOT_HOME}/consul_pods_checker.py

ENV STATUS_CUSTOM_RESOURCE_GROUP=apps
ENV STATUS_CUSTOM_RESOURCE_VERSION=v1
ENV STATUS_CUSTOM_RESOURCE_PLURAL=deployments
ENV STATUS_CUSTOM_RESOURCE_NAME=consul-integration-tests-runner

RUN mkdir -p ${ROBOT_OUTPUT}

COPY integration-tests/docker/requirements.txt ${ROBOT_HOME}/requirements.txt
COPY integration-tests/docker/consul_pods_checker.py ${ROBOT_HOME}/consul_pods_checker.py
COPY integration-tests/robot ${ROBOT_HOME}

RUN set -x \
    && pip3 install -r ${ROBOT_HOME}/requirements.txt \
    && rm -rf /var/cache/apk/*

USER 1000:0

EXPOSE 8080
VOLUME ["${ROBOT_OUTPUT}"]
```

---

## 3. Настройка GitHub Secrets и Variables

### Необходимые GitHub Secrets

**Repository или Environment secrets:**

| Secret | Описание |
|--------|----------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key для доступа к EKS |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key для доступа к EKS |
| `ATP_STORAGE_USERNAME` | S3 Access Key (может совпадать с AWS_ACCESS_KEY_ID) |
| `ATP_STORAGE_PASSWORD` | S3 Secret Key (может совпадать с AWS_SECRET_ACCESS_KEY) |

### Необходимые GitHub Variables

**Repository или Environment variables:**

| Variable | Описание | Пример |
|----------|----------|--------|
| `AWS_REGION` | Регион AWS | `us-east-1` |
| `AWS_CLUSTERNAME` | Имя EKS кластера | `my-eks-cluster` |
| `CONSUL_INSTALL_NAMESPACE` | Namespace для установки Consul | `consul` |
| `ATP_STORAGE_SERVER_URL` | URL S3 API | `https://s3.us-east-1.amazonaws.com` |
| `ATP_STORAGE_SERVER_UI_URL` | URL S3 UI (для MinIO) | `https://minio.example.com` |
| `ATP_STORAGE_BUCKET` | Имя S3 бакета | `test-results` |
| `ATP_REPORT_VIEW_UI_URL` | URL для Allure отчётов | `https://reports.example.com` |
| `ENVIRONMENT_NAME` | Имя окружения | `dev` |

---

## 4. Схема взаимодействия

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         install_consul_to_aws.yaml                   │   │
│  │                                                      │   │
│  │  1. Setup kubectl + helm                            │   │
│  │  2. Configure AWS credentials                       │   │
│  │  3. Connect to EKS cluster                          │   │
│  │  4. helm install consul-service                     │   │
│  │     └─> Передаёт S3 параметры через --set           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes (EKS)                          │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │   Consul Server      │    │ Integration Tests Pod     │  │
│  │   StatefulSet        │    │                          │  │
│  │                      │    │  ENV:                    │  │
│  │  - consul-server-0   │◄───│  - ATP_STORAGE_BUCKET   │  │
│  │  - consul-server-1   │    │  - ATP_STORAGE_USERNAME │  │
│  │  - consul-server-2   │    │  - ATP_STORAGE_PASSWORD │  │
│  └──────────────────────┘    │  - ENVIRONMENT_NAME     │  │
│                              │  - ...                   │  │
│                              └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Integration Tests Container                     │
│                                                              │
│  FROM qubership-docker-integration-tests:TAG                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              docker-entrypoint.sh                    │   │
│  │                       │                              │   │
│  │                       ▼                              │   │
│  │         adapter-S3-entrypoint.sh                     │   │
│  │                       │                              │   │
│  │    ┌──────────────────┼──────────────────┐          │   │
│  │    ▼                  ▼                  ▼          │   │
│  │ init.sh        test-runner.sh    upload-monitor.sh  │   │
│  │    │                  │                  │          │   │
│  │    ▼                  ▼                  ▼          │   │
│  │ Setup S3        start_tests.sh    inotifywait +    │   │
│  │ credentials          │             s5cmd upload    │   │
│  │                       ▼                             │   │
│  │                 Robot Framework                     │   │
│  │                 + Allure Listener                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 Storage                                │
│                                                              │
│  bucket/                                                    │
│  ├── Result/                                                │
│  │   └── {ENVIRONMENT_NAME}/                                │
│  │       └── {DATE}/                                        │
│  │           └── {TIME}/                                    │
│  │               ├── allure-results/                        │
│  │               │   ├── *-result.json                      │
│  │               │   └── ...                                │
│  │               └── allure-results.uploaded                │
│  └── Report/                                                │
│      └── {ENVIRONMENT_NAME}/                                │
│          └── {DATE}/                                        │
│              └── {TIME}/                                    │
│                  ├── allure-report/                         │
│                  └── attachments/                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Запуск без S3 (локальные результаты)

Если S3 интеграция не нужна, просто не указывайте `ATP_STORAGE_BUCKET`:

```yaml
# В values.yaml или через --set
integrationTests:
  atpStorage:
    bucket: ""  # Пустой = S3 отключен
```

В этом случае:
- Тесты будут выполняться нормально
- Результаты останутся локально в `/tmp/clone/`
- В логах будет: `⚠️ S3 integration disabled (ATP_STORAGE_BUCKET is not set)`

---

## 6. Troubleshooting

### Ошибка: "ATP_STORAGE_USERNAME is required but not set"

**Причина:** Указан `ATP_STORAGE_BUCKET`, но не указаны credentials.

**Решение:** Добавьте secrets `ATP_STORAGE_USERNAME` и `ATP_STORAGE_PASSWORD` в GitHub.

### Ошибка: Тесты не запускаются

**Проверьте:**
1. Все необходимые secrets и variables настроены в GitHub
2. Environment `dev` существует и содержит нужные variables
3. EKS кластер доступен и credentials корректны

### Просмотр логов контейнера

```bash
kubectl logs -n <namespace> deployment/consul-integration-tests-runner
```

---

*Документация создана: Январь 2026*




