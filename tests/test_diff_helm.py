import pytest

from tests.utils import DiffTestCase, DiffTestRunner

HELM_VALUES_CASES = [
    DiffTestCase(
        name="helm_531_values_image",
        initial_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY . .\nCMD ["python", "app.py"]\n',
            "values.yaml": "replicaCount: 1\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "values.yaml": "replicaCount: 1\nimage:\n  repository: myapp\n  tag: latest\n  pullPolicy: IfNotPresent\n",
        },
        must_include=["image:", "repository: myapp"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add image values",
    ),
    DiffTestCase(
        name="helm_532_values_replicas",
        initial_files={
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  replicas: {{ .Values.replicaCount }}\n",
            "values.yaml": "replicaCount: 1\n",
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "values.yaml": "replicaCount: 3\n",
        },
        must_include=["replicaCount: 3"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update replicas",
    ),
    DiffTestCase(
        name="helm_533_values_resources",
        initial_files={
            "values.yaml": "replicaCount: 1\nresources: {}\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "values.yaml": "replicaCount: 1\nresources:\n  limits:\n    cpu: 500m\n    memory: 512Mi\n  requests:\n    cpu: 250m\n    memory: 256Mi\n",
        },
        must_include=["resources:", "cpu: 500m"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add resources",
    ),
    DiffTestCase(
        name="helm_534_values_env",
        initial_files={
            "app.py": "import os\nlog_level = os.environ.get('LOG_LEVEL', 'info')\n",
            "values.yaml": "replicaCount: 1\nenv: []\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "values.yaml": "replicaCount: 1\nenv:\n  - name: LOG_LEVEL\n    value: debug\n  - name: DATABASE_URL\n    valueFrom:\n      secretKeyRef:\n        name: db-secret\n        key: url\n",
        },
        must_include=["env:", "LOG_LEVEL"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add env values",
    ),
    DiffTestCase(
        name="helm_535_chart_dependency",
        initial_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\nversion: 1.0.0\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\nversion: 1.0.0\ndependencies:\n  - name: postgresql\n    version: 12.1.0\n    repository: https://charts.bitnami.com/bitnami\n    condition: postgresql.enabled\n",
        },
        must_include=["dependencies:", "postgresql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add dependency",
    ),
    DiffTestCase(
        name="helm_536_chart_version",
        initial_files={
            "CHANGELOG.md": "# Changelog\n\n## 2.0.0\n- Breaking: Changed API endpoint format\n- Added new authentication method\n",
            "Chart.yaml": "apiVersion: v2\nname: myapp\nversion: 1.0.0\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Chart.yaml": 'apiVersion: v2\nname: myapp\nversion: 2.0.0\nappVersion: "2.0.0"\n',
        },
        must_include=["version: 2.0.0"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Bump version",
    ),
]

HELM_TEMPLATE_CASES = [
    DiffTestCase(
        name="helm_537_template_deployment",
        initial_files={
            "values.yaml": "image:\n  repository: myapp\n  tag: latest\n",
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}\n",
        },
        must_include=["{{ .Values.image.repository }}"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add template values",
    ),
    DiffTestCase(
        name="helm_538_template_service",
        initial_files={
            "values.yaml": "service:\n  type: ClusterIP\n  port: 80\n",
            "templates/service.yaml": "apiVersion: v1\nkind: Service\nspec:\n  type: ClusterIP\n  ports:\n  - port: 80\n",
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/service.yaml": "apiVersion: v1\nkind: Service\nspec:\n  type: {{ .Values.service.type }}\n  ports:\n  - port: {{ .Values.service.port }}\n",
        },
        must_include=["{{ .Values.service.type }}"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add service template",
    ),
    DiffTestCase(
        name="helm_539_template_configmap",
        initial_files={
            "values.yaml": "config:\n  logLevel: info\n  maxConnections: 100\n",
            "templates/configmap.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\ndata: {}\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/configmap.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: {{ .Release.Name }}-config\ndata:\n{{ toYaml .Values.config | indent 2 }}\n",
        },
        must_include=["{{ .Release.Name }}-config"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add configmap template",
    ),
    DiffTestCase(
        name="helm_540_template_secret",
        initial_files={
            "values.yaml": 'db:\n  password: ""\n',
            "templates/secret.yaml": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: db-secret\ndata: {}\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "templates/secret.yaml": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: {{ .Release.Name }}-db-secret\ntype: Opaque\ndata:\n  password: {{ .Values.db.password | b64enc }}\n",
        },
        must_include=["{{ .Values.db.password | b64enc }}"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add secret template",
    ),
    DiffTestCase(
        name="helm_541_helpers_tpl",
        initial_files={
            "templates/_helpers.tpl": "{{/* Common labels */}}\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/_helpers.tpl": """{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
""",
        },
        must_include=["define", "app.name"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add helpers",
    ),
    DiffTestCase(
        name="helm_542_template_include",
        initial_files={
            "templates/_helpers.tpl": '{{- define "app.labels" -}}\napp.kubernetes.io/name: {{ .Chart.Name }}\napp.kubernetes.io/instance: {{ .Release.Name }}\n{{- end }}\n',
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  labels:\n    app: myapp\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  labels:\n{{ include "app.labels" . | indent 4 }}\n',
        },
        must_include=["include", "app.labels"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add include",
    ),
    DiffTestCase(
        name="helm_543_template_range",
        initial_files={
            "values.yaml": "ingress:\n  hosts:\n    - host: app.example.com\n      paths:\n        - path: /\n          pathType: Prefix\n",
            "templates/ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nspec:\n  rules: []\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "templates/ingress.yaml": """apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ $.Release.Name }}
                port:
                  number: 80
          {{- end }}
    {{- end }}
""",
        },
        must_include=["range .Values.ingress.hosts"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add range",
    ),
    DiffTestCase(
        name="helm_544_template_if",
        initial_files={
            "values.yaml": "ingress:\n  enabled: false\n",
            "templates/ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\n",
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/ingress.yaml": "{{- if .Values.ingress.enabled -}}\napiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: {{ .Release.Name }}-ingress\nspec:\n  rules:\n    - host: {{ .Values.ingress.host }}\n{{- end }}\n",
        },
        must_include=["if .Values.ingress.enabled"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add if condition",
    ),
    DiffTestCase(
        name="helm_545_template_with",
        initial_files={
            "values.yaml": "nodeSelector:\n  kubernetes.io/os: linux\n",
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      {{- with .Values.nodeSelector }}\n      nodeSelector:\n{{ toYaml . | indent 8 }}\n      {{- end }}\n      containers:\n      - name: app\n",
        },
        must_include=["with .Values.nodeSelector"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add with",
    ),
    DiffTestCase(
        name="helm_546_template_default",
        initial_files={
            "values.yaml": "# timeout not set\n",
            "templates/deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: TIMEOUT\n          value: "30"\n',
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "templates/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: TIMEOUT\n          value: {{ .Values.timeout | default 30 | quote }}\n",
        },
        must_include=["default 30"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add default",
    ),
    DiffTestCase(
        name="helm_547_template_required",
        initial_files={
            "values.yaml": 'apiKey: ""\n',
            "templates/secret.yaml": "apiVersion: v1\nkind: Secret\ndata:\n  api-key: {{ .Values.apiKey | b64enc }}\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/secret.yaml": 'apiVersion: v1\nkind: Secret\ndata:\n  api-key: {{ required "apiKey is required" .Values.apiKey | b64enc }}\n',
        },
        must_include=["required"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add required",
    ),
    DiffTestCase(
        name="helm_548_template_lookup",
        initial_files={
            "templates/secret.yaml": "apiVersion: v1\nkind: Secret\ndata:\n  password: {{ randAlphaNum 20 | b64enc }}\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/secret.yaml": """{{- $secret := lookup "v1" "Secret" .Release.Namespace "existing-secret" -}}
apiVersion: v1
kind: Secret
data:
  {{- if $secret }}
  password: {{ index $secret.data "password" }}
  {{- else }}
  password: {{ randAlphaNum 20 | b64enc }}
  {{- end }}
""",
        },
        must_include=["lookup"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add lookup",
    ),
    DiffTestCase(
        name="helm_549_notes_txt",
        initial_files={
            "templates/service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: {{ .Release.Name }}\n",
            "templates/NOTES.txt": "Thank you for installing {{ .Chart.Name }}.\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "templates/NOTES.txt": """Thank you for installing {{ .Chart.Name }}.

Get the application URL by running these commands:
{{- if .Values.ingress.enabled }}
  http{{ if .Values.ingress.tls }}s{{ end }}://{{ .Values.ingress.host }}
{{- else }}
  kubectl port-forward svc/{{ .Release.Name }} 8080:80
{{- end }}
""",
        },
        must_include=["kubectl port-forward"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update NOTES",
    ),
    DiffTestCase(
        name="helm_550_tests",
        initial_files={
            "templates/tests/test-connection.yaml": "# Test placeholder\n",
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/tests/test-connection.yaml": """apiVersion: v1
kind: Pod
metadata:
  name: {{ .Release.Name }}-test
  annotations:
    "helm.sh/hook": test
spec:
  containers:
  - name: test
    image: busybox
    command: ['wget', '-qO-', 'http://{{ .Release.Name }}:80']
  restartPolicy: Never
""",
        },
        must_include=["helm.sh/hook", "test"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add test",
    ),
]

HELM_ADVANCED_CASES = [
    DiffTestCase(
        name="helm_551_hooks",
        initial_files={
            "templates/hooks/pre-install.yaml": "# Hook placeholder\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/hooks/pre-install.yaml": """apiVersion: batch/v1
kind: Job
metadata:
  name: {{ .Release.Name }}-db-init
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
      - name: init
        image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
        command: ["./init-db.sh"]
      restartPolicy: Never
""",
        },
        must_include=["helm.sh/hook", "pre-install"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add hook",
    ),
    DiffTestCase(
        name="helm_552_subchart_values",
        initial_files={
            "charts/postgresql/values.yaml": 'auth:\n  username: postgres\n  password: ""\n  database: postgres\n',
            "values.yaml": "postgresql:\n  enabled: true\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "values.yaml": "postgresql:\n  enabled: true\n  auth:\n    username: myapp\n    database: myapp\n    existingSecret: db-secret\n",
        },
        must_include=["postgresql:", "existingSecret"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add subchart values",
    ),
    DiffTestCase(
        name="helm_553_global_values",
        initial_files={
            "values.yaml": "image:\n  repository: myapp\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "values.yaml": "global:\n  imageRegistry: registry.example.com\n  imagePullSecrets:\n    - name: registry-secret\n\nimage:\n  repository: myapp\n",
        },
        must_include=["global:", "imageRegistry"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add global values",
    ),
    DiffTestCase(
        name="helm_554_values_schema",
        initial_files={
            "values.schema.json": "{}\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "values.schema.json": """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image", "replicaCount"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1
    },
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": { "type": "string" },
        "tag": { "type": "string" }
      }
    }
  }
}
""",
        },
        must_include=["$schema", "replicaCount"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add values schema",
    ),
    DiffTestCase(
        name="helm_555_umbrella_chart",
        initial_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\nversion: 1.0.0\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\nversion: 1.0.0\ndependencies:\n  - name: frontend\n    version: 1.0.0\n    repository: file://./charts/frontend\n  - name: backend\n    version: 1.0.0\n    repository: file://./charts/backend\n  - name: redis\n    version: 17.0.0\n    repository: https://charts.bitnami.com/bitnami\n",
        },
        must_include=["dependencies:", "frontend"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add umbrella dependencies",
    ),
    DiffTestCase(
        name="helm_556_condition",
        initial_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: backend\n    version: 1.0.0\n",
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: backend\n    version: 1.0.0\n    condition: backend.enabled\n",
        },
        must_include=["condition: backend.enabled"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add condition",
    ),
    DiffTestCase(
        name="helm_557_alias",
        initial_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: postgresql\n    version: 12.0.0\n    repository: https://charts.bitnami.com/bitnami\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: postgresql\n    version: 12.0.0\n    repository: https://charts.bitnami.com/bitnami\n    alias: postgres\n",
        },
        must_include=["alias: postgres"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add alias",
    ),
    DiffTestCase(
        name="helm_558_import_values",
        initial_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: backend\n    version: 1.0.0\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "Chart.yaml": "apiVersion: v2\nname: myapp\ndependencies:\n  - name: backend\n    version: 1.0.0\n    import-values:\n      - child: exports\n        parent: config\n",
        },
        must_include=["import-values:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add import-values",
    ),
    DiffTestCase(
        name="helm_559_capabilities",
        initial_files={
            "templates/ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/ingress.yaml": '{{- if .Capabilities.APIVersions.Has "networking.k8s.io/v1" }}\napiVersion: networking.k8s.io/v1\n{{- else }}\napiVersion: extensions/v1beta1\n{{- end }}\nkind: Ingress\n',
        },
        must_include=["Capabilities.APIVersions"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add capabilities check",
    ),
    DiffTestCase(
        name="helm_560_release_values",
        initial_files={
            "templates/configmap.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "templates/configmap.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: {{ .Release.Name }}-config\n  namespace: {{ .Release.Namespace }}\n  labels:\n    app.kubernetes.io/managed-by: {{ .Release.Service }}\n    helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}\n",
        },
        must_include=["{{ .Release.Name }}", "{{ .Release.Namespace }}"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add release values",
    ),
]

ALL_HELM_CASES = HELM_VALUES_CASES + HELM_TEMPLATE_CASES + HELM_ADVANCED_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_HELM_CASES, ids=lambda c: c.name)
def test_helm_context_selection(diff_test_runner, case):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
