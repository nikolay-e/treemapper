import pytest

from tests.utils import DiffTestCase, DiffTestRunner

K8S_DEPLOYMENT_CASES = [
    DiffTestCase(
        name="k8s_401_deployment_image",
        initial_files={
            "Dockerfile": 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ["python", "main.py"]\n',
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  replicas: 1\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:v1.0\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  replicas: 1\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:v2.0\n",
        },
        must_include=["image: myapp:v2.0"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update image",
    ),
    DiffTestCase(
        name="k8s_402_replicas_change",
        initial_files={
            "hpa.yaml": "apiVersion: autoscaling/v2\nkind: HorizontalPodAutoscaler\nmetadata:\n  name: myapp-hpa\nspec:\n  minReplicas: 2\n  maxReplicas: 10\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  replicas: 2\n",
            "unrelated.txt": "garbage_marker_k8s402 = True\nunused_marker_k8s402 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  replicas: 5\n",
        },
        must_include=["replicas: 5"],
        must_not_include=["garbage_marker_k8s402", "unused_marker_k8s402"],
        commit_message="Update replicas",
    ),
    DiffTestCase(
        name="k8s_403_container_port",
        initial_files={
            "main.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello'\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8080)\n",
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  ports:\n  - port: 80\n    targetPort: 8080\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        ports:\n        - containerPort: 3000\n",
            "unrelated.txt": "garbage_marker_k8s403 = True\nunused_marker_k8s403 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        ports:\n        - containerPort: 8080\n",
        },
        must_include=["containerPort: 8080"],
        must_not_include=["garbage_marker_k8s403", "unused_marker_k8s403"],
        commit_message="Update container port",
    ),
    DiffTestCase(
        name="k8s_404_environment_variable",
        initial_files={
            "app.py": "import os\n\nDATABASE_URL = os.environ.get('DATABASE_URL')\nprint(f'Connecting to {DATABASE_URL}')\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env: []\n",
            "unrelated.txt": "garbage_marker_k8s404 = True\nunused_marker_k8s404 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: DATABASE_URL\n          value: "postgres://db:5432/myapp"\n',
        },
        must_include=["DATABASE_URL"],
        must_not_include=["garbage_marker_k8s404", "unused_marker_k8s404"],
        commit_message="Add environment variable",
    ),
    DiffTestCase(
        name="k8s_405_configmap_reference",
        initial_files={
            "configmap.yaml": 'apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: app-config\ndata:\n  LOG_LEVEL: info\n  MAX_CONNECTIONS: "100"\n',
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env: []\n",
            "unrelated.txt": "garbage_marker_k8s405 = True\nunused_marker_k8s405 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: LOG_LEVEL\n          valueFrom:\n            configMapKeyRef:\n              name: app-config\n              key: LOG_LEVEL\n",
        },
        must_include=["configMapKeyRef"],
        must_not_include=["garbage_marker_k8s405", "unused_marker_k8s405"],
        commit_message="Add ConfigMap reference",
    ),
    DiffTestCase(
        name="k8s_406_secret_reference",
        initial_files={
            "secret.yaml": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: db-secret\ntype: Opaque\ndata:\n  password: dGVzdA==\n",  # pragma: allowlist secret  # gitleaks:allow
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env: []\n",
            "unrelated.txt": "garbage_marker_k8s406 = True\nunused_marker_k8s406 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        env:\n        - name: DB_PASSWORD\n          valueFrom:\n            secretKeyRef:\n              name: db-secret\n              key: password\n",
        },
        must_include=["secretKeyRef"],
        must_not_include=["garbage_marker_k8s406", "unused_marker_k8s406"],
        commit_message="Add Secret reference",
    ),
    DiffTestCase(
        name="k8s_407_volume_mount",
        initial_files={
            "config.yaml": "server:\n  port: 8080\n  host: 0.0.0.0\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        volumeMounts: []\n      volumes: []\n",
            "unrelated.txt": "garbage_marker_k8s407 = True\nunused_marker_k8s407 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        volumeMounts:\n        - name: config\n          mountPath: /app/config\n          readOnly: true\n      volumes:\n      - name: config\n        configMap:\n          name: app-config\n",
        },
        must_include=["volumeMounts"],
        must_not_include=["garbage_marker_k8s407", "unused_marker_k8s407"],
        commit_message="Add volume mount",
    ),
    DiffTestCase(
        name="k8s_408_resource_limits",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        resources: {}\n",
            "unrelated.txt": "garbage_marker_k8s408 = True\nunused_marker_k8s408 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        resources:\n          requests:\n            memory: "256Mi"\n            cpu: "250m"\n          limits:\n            memory: "512Mi"\n            cpu: "500m"\n',
        },
        must_include=["resources:"],
        must_not_include=["garbage_marker_k8s408", "unused_marker_k8s408"],
        commit_message="Add resource limits",
    ),
    DiffTestCase(
        name="k8s_409_liveness_probe",
        initial_files={
            "app.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/health')\ndef health():\n    return {'status': 'healthy'}, 200\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s409 = True\nunused_marker_k8s409 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n        livenessProbe:\n          httpGet:\n            path: /health\n            port: 8080\n          initialDelaySeconds: 30\n          periodSeconds: 10\n",
        },
        must_include=["livenessProbe"],
        must_not_include=["garbage_marker_k8s409", "unused_marker_k8s409"],
        commit_message="Add liveness probe",
    ),
    DiffTestCase(
        name="k8s_410_readiness_probe",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        ports:\n        - containerPort: 8080\n",
            "unrelated.txt": "garbage_marker_k8s410 = True\nunused_marker_k8s410 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        ports:\n        - containerPort: 8080\n        readinessProbe:\n          tcpSocket:\n            port: 8080\n          initialDelaySeconds: 5\n          periodSeconds: 5\n",
        },
        must_include=["readinessProbe"],
        must_not_include=["garbage_marker_k8s410", "unused_marker_k8s410"],
        commit_message="Add readiness probe",
    ),
    DiffTestCase(
        name="k8s_411_init_container",
        initial_files={
            "init-db.sh": '#!/bin/bash\nuntil pg_isready -h $DB_HOST; do\n  echo "Waiting for database..."\n  sleep 2\ndone\necho "Database is ready"\n',
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s411 = True\nunused_marker_k8s411 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      initContainers:\n      - name: init-db\n        image: postgres:13\n        command: ['sh', '-c', 'until pg_isready -h $DB_HOST; do sleep 2; done']\n        env:\n        - name: DB_HOST\n          value: \"postgres\"\n      containers:\n      - name: app\n        image: myapp:latest\n",
        },
        must_include=["initContainers"],
        must_not_include=["garbage_marker_k8s411", "unused_marker_k8s411"],
        commit_message="Add init container",
    ),
    DiffTestCase(
        name="k8s_412_sidecar_container",
        initial_files={
            "fluent-bit.conf": "[INPUT]\n    Name tail\n    Path /var/log/app/*.log\n[OUTPUT]\n    Name stdout\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s412 = True\nunused_marker_k8s412 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n        volumeMounts:\n        - name: logs\n          mountPath: /var/log/app\n      - name: log-agent\n        image: fluent/fluent-bit:latest\n        volumeMounts:\n        - name: logs\n          mountPath: /var/log/app\n          readOnly: true\n      volumes:\n      - name: logs\n        emptyDir: {}\n",
        },
        must_include=["log-agent"],
        must_not_include=["garbage_marker_k8s412", "unused_marker_k8s412"],
        commit_message="Add sidecar container",
    ),
    DiffTestCase(
        name="k8s_413_pod_affinity",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    metadata:\n      labels:\n        app: myapp\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s413 = True\nunused_marker_k8s413 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    metadata:\n      labels:\n        app: myapp\n    spec:\n      affinity:\n        podAffinity:\n          requiredDuringSchedulingIgnoredDuringExecution:\n          - labelSelector:\n              matchLabels:\n                app: cache\n            topologyKey: kubernetes.io/hostname\n      containers:\n      - name: app\n        image: myapp:latest\n",
        },
        must_include=["podAffinity"],
        must_not_include=["garbage_marker_k8s413", "unused_marker_k8s413"],
        commit_message="Add pod affinity",
    ),
    DiffTestCase(
        name="k8s_414_node_selector",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: ml-training\nspec:\n  template:\n    spec:\n      containers:\n      - name: trainer\n        image: ml-trainer:latest\n",
            "unrelated.txt": "garbage_marker_k8s414 = True\nunused_marker_k8s414 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: ml-training\nspec:\n  template:\n    spec:\n      nodeSelector:\n        gpu: "true"\n        accelerator: nvidia-tesla-v100\n      containers:\n      - name: trainer\n        image: ml-trainer:latest\n',
        },
        must_include=["nodeSelector"],
        must_not_include=["garbage_marker_k8s414", "unused_marker_k8s414"],
        commit_message="Add node selector",
    ),
    DiffTestCase(
        name="k8s_415_toleration",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: dedicated-app\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s415 = True\nunused_marker_k8s415 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: dedicated-app\nspec:\n  template:\n    spec:\n      tolerations:\n      - key: "dedicated"\n        operator: "Equal"\n        value: "high-priority"\n        effect: "NoSchedule"\n      containers:\n      - name: app\n        image: myapp:latest\n',
        },
        must_include=["tolerations"],
        must_not_include=["garbage_marker_k8s415", "unused_marker_k8s415"],
        commit_message="Add toleration",
    ),
    DiffTestCase(
        name="k8s_416_security_context",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: secure-app\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s416 = True\nunused_marker_k8s416 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: secure-app\nspec:\n  template:\n    spec:\n      securityContext:\n        runAsNonRoot: true\n        runAsUser: 1000\n        fsGroup: 2000\n      containers:\n      - name: app\n        image: myapp:latest\n        securityContext:\n          allowPrivilegeEscalation: false\n          readOnlyRootFilesystem: true\n          capabilities:\n            drop:\n            - ALL\n",
        },
        must_include=["securityContext"],
        must_not_include=["garbage_marker_k8s416", "unused_marker_k8s416"],
        commit_message="Add security context",
    ),
    DiffTestCase(
        name="k8s_417_service_account",
        initial_files={
            "serviceaccount.yaml": 'apiVersion: v1\nkind: ServiceAccount\nmetadata:\n  name: app-sa\n---\napiVersion: rbac.authorization.k8s.io/v1\nkind: Role\nmetadata:\n  name: app-role\nrules:\n- apiGroups: [""]\n  resources: ["secrets"]\n  verbs: ["get", "list"]\n',
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s417 = True\nunused_marker_k8s417 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      serviceAccountName: app-sa\n      containers:\n      - name: app\n        image: myapp:latest\n",
        },
        must_include=["serviceAccountName"],
        must_not_include=["garbage_marker_k8s417", "unused_marker_k8s417"],
        commit_message="Add service account",
    ),
    DiffTestCase(
        name="k8s_418_image_pull_secret",
        initial_files={
            "registry-secret.yaml": "apiVersion: v1\nkind: Secret\nmetadata:\n  name: registry-cred\ntype: kubernetes.io/dockerconfigjson\ndata:\n  .dockerconfigjson: eyJhdXRocyI6e319\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: private-registry.io/myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s418 = True\nunused_marker_k8s418 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      imagePullSecrets:\n      - name: registry-cred\n      containers:\n      - name: app\n        image: private-registry.io/myapp:latest\n",
        },
        must_include=["imagePullSecrets"],
        must_not_include=["garbage_marker_k8s418", "unused_marker_k8s418"],
        commit_message="Add image pull secret",
    ),
    DiffTestCase(
        name="k8s_419_lifecycle_hooks",
        initial_files={
            "shutdown.sh": '#!/bin/bash\necho "Graceful shutdown..."\nkill -SIGTERM $(cat /var/run/app.pid)\nsleep 10\n',
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s419 = True\nunused_marker_k8s419 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n        lifecycle:\n          postStart:\n            exec:\n              command: ["/bin/sh", "-c", "echo Started"]\n          preStop:\n            exec:\n              command: ["/bin/sh", "-c", "/shutdown.sh"]\n',
        },
        must_include=["lifecycle"],
        must_not_include=["garbage_marker_k8s419", "unused_marker_k8s419"],
        commit_message="Add lifecycle hooks",
    ),
    DiffTestCase(
        name="k8s_420_pod_disruption_budget",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  replicas: 5\n  selector:\n    matchLabels:\n      app: myapp\n  template:\n    metadata:\n      labels:\n        app: myapp\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "pdb.yaml": "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: myapp-pdb\nspec:\n  minAvailable: 1\n  selector:\n    matchLabels:\n      app: myapp\n",
            "unrelated.txt": "garbage_marker_k8s420 = True\nunused_marker_k8s420 = False\n",
        },
        changed_files={
            "pdb.yaml": "apiVersion: policy/v1\nkind: PodDisruptionBudget\nmetadata:\n  name: myapp-pdb\nspec:\n  minAvailable: 2\n  selector:\n    matchLabels:\n      app: myapp\n",
        },
        must_include=["minAvailable: 2"],
        must_not_include=["garbage_marker_k8s420", "unused_marker_k8s420"],
        commit_message="Update PDB",
    ),
]


K8S_NETWORKING_CASES = [
    DiffTestCase(
        name="k8s_421_service_selector",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    metadata:\n      labels:\n        app: myapp\n        version: v1\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  selector:\n    app: old-app\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s421 = True\nunused_marker_k8s421 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  selector:\n    app: myapp\n  ports:\n  - port: 80\n",
        },
        must_include=["selector:"],
        must_not_include=["garbage_marker_k8s421", "unused_marker_k8s421"],
        commit_message="Update service selector",
    ),
    DiffTestCase(
        name="k8s_422_service_port",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        ports:\n        - containerPort: 8080\n",
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  ports:\n  - port: 80\n    targetPort: 3000\n",
            "unrelated.txt": "garbage_marker_k8s422 = True\nunused_marker_k8s422 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  ports:\n  - port: 80\n    targetPort: 8080\n",
        },
        must_include=["targetPort: 8080"],
        must_not_include=["garbage_marker_k8s422", "unused_marker_k8s422"],
        commit_message="Update service port",
    ),
    DiffTestCase(
        name="k8s_423_nodeport",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  type: ClusterIP\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s423 = True\nunused_marker_k8s423 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  type: NodePort\n  ports:\n  - port: 80\n    nodePort: 30080\n",
        },
        must_include=["NodePort"],
        must_not_include=["garbage_marker_k8s423", "unused_marker_k8s423"],
        commit_message="Add NodePort",
    ),
    DiffTestCase(
        name="k8s_424_loadbalancer",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  type: ClusterIP\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s424 = True\nunused_marker_k8s424 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\n  annotations:\n    service.beta.kubernetes.io/aws-load-balancer-type: nlb\nspec:\n  type: LoadBalancer\n  ports:\n  - port: 80\n",
        },
        must_include=["LoadBalancer"],
        must_not_include=["garbage_marker_k8s424", "unused_marker_k8s424"],
        commit_message="Add LoadBalancer",
    ),
    DiffTestCase(
        name="k8s_425_headless_service",
        initial_files={
            "statefulset.yaml": "apiVersion: apps/v1\nkind: StatefulSet\nmetadata:\n  name: postgres\nspec:\n  serviceName: postgres\n  replicas: 3\n  template:\n    spec:\n      containers:\n      - name: postgres\n        image: postgres:13\n",
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: postgres\nspec:\n  ports:\n  - port: 5432\n",
            "unrelated.txt": "garbage_marker_k8s425 = True\nunused_marker_k8s425 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: postgres\nspec:\n  clusterIP: None\n  ports:\n  - port: 5432\n",
        },
        must_include=["clusterIP: None"],
        must_not_include=["garbage_marker_k8s425", "unused_marker_k8s425"],
        commit_message="Add headless service",
    ),
    DiffTestCase(
        name="k8s_426_ingress_rules",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: api\nspec:\n  ports:\n  - port: 80\n",
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  rules: []\n",
            "unrelated.txt": "garbage_marker_k8s426 = True\nunused_marker_k8s426 = False\n",
        },
        changed_files={
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  rules:\n  - host: api.example.com\n    http:\n      paths:\n      - path: /\n        pathType: Prefix\n        backend:\n          service:\n            name: api\n            port:\n              number: 80\n",
        },
        must_include=["api.example.com"],
        must_not_include=["garbage_marker_k8s426", "unused_marker_k8s426"],
        commit_message="Add ingress rules",
    ),
    DiffTestCase(
        name="k8s_427_ingress_tls",
        initial_files={
            "certificate.yaml": "apiVersion: cert-manager.io/v1\nkind: Certificate\nmetadata:\n  name: api-tls\nspec:\n  secretName: tls-cert\n  issuerRef:\n    name: letsencrypt-prod\n  dnsNames:\n  - api.example.com\n",
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  rules:\n  - host: api.example.com\n",
            "unrelated.txt": "garbage_marker_k8s427 = True\nunused_marker_k8s427 = False\n",
        },
        changed_files={
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  tls:\n  - hosts:\n    - api.example.com\n    secretName: tls-cert\n  rules:\n  - host: api.example.com\n",
        },
        must_include=["tls:"],
        must_not_include=["garbage_marker_k8s427", "unused_marker_k8s427"],
        commit_message="Add ingress TLS",
    ),
    DiffTestCase(
        name="k8s_428_ingress_annotations",
        initial_files={
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  rules:\n  - host: api.example.com\n    http:\n      paths:\n      - path: /api\n        pathType: Prefix\n        backend:\n          service:\n            name: api\n            port:\n              number: 80\n",
            "unrelated.txt": "garbage_marker_k8s428 = True\nunused_marker_k8s428 = False\n",
        },
        changed_files={
            "ingress.yaml": 'apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\n  annotations:\n    nginx.ingress.kubernetes.io/rewrite-target: /\n    nginx.ingress.kubernetes.io/ssl-redirect: "true"\nspec:\n  rules:\n  - host: api.example.com\n    http:\n      paths:\n      - path: /api\n        pathType: Prefix\n        backend:\n          service:\n            name: api\n            port:\n              number: 80\n',
        },
        must_include=["annotations:"],
        must_not_include=["garbage_marker_k8s428", "unused_marker_k8s428"],
        commit_message="Add ingress annotations",
    ),
    DiffTestCase(
        name="k8s_429_network_policy_ingress",
        initial_files={
            "networkpolicy.yaml": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: default-deny\nspec:\n  podSelector: {}\n  policyTypes:\n  - Ingress\n",
            "unrelated.txt": "garbage_marker_k8s429 = True\nunused_marker_k8s429 = False\n",
        },
        changed_files={
            "networkpolicy.yaml": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: api-policy\nspec:\n  podSelector:\n    matchLabels:\n      app: api\n  ingress:\n  - from:\n    - podSelector:\n        matchLabels:\n          role: frontend\n    ports:\n    - port: 8080\n",
        },
        must_include=["NetworkPolicy"],
        must_not_include=["garbage_marker_k8s429", "unused_marker_k8s429"],
        commit_message="Add network policy ingress",
    ),
    DiffTestCase(
        name="k8s_430_network_policy_egress",
        initial_files={
            "networkpolicy.yaml": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: default-deny\nspec:\n  podSelector: {}\n  policyTypes:\n  - Egress\n",
            "unrelated.txt": "garbage_marker_k8s430 = True\nunused_marker_k8s430 = False\n",
        },
        changed_files={
            "networkpolicy.yaml": "apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: api-policy\nspec:\n  podSelector:\n    matchLabels:\n      app: api\n  egress:\n  - to:\n    - namespaceSelector:\n        matchLabels:\n          name: database\n    ports:\n    - port: 5432\n",
        },
        must_include=["egress:"],
        must_not_include=["garbage_marker_k8s430", "unused_marker_k8s430"],
        commit_message="Add network policy egress",
    ),
    DiffTestCase(
        name="k8s_431_istio_virtual_service",
        initial_files={
            "destination-rule.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: DestinationRule\nmetadata:\n  name: api\nspec:\n  host: api\n  subsets:\n  - name: v1\n    labels:\n      version: v1\n  - name: v2\n    labels:\n      version: v2\n",
            "virtual-service.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: VirtualService\nmetadata:\n  name: api\nspec:\n  hosts:\n  - api\n",
            "unrelated.txt": "garbage_marker_k8s431 = True\nunused_marker_k8s431 = False\n",
        },
        changed_files={
            "virtual-service.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: VirtualService\nmetadata:\n  name: api\nspec:\n  hosts:\n  - api\n  http:\n  - route:\n    - destination:\n        host: api\n        subset: v1\n      weight: 90\n    - destination:\n        host: api\n        subset: v2\n      weight: 10\n",
        },
        must_include=["VirtualService"],
        must_not_include=["garbage_marker_k8s431", "unused_marker_k8s431"],
        commit_message="Add Istio virtual service",
    ),
    DiffTestCase(
        name="k8s_432_gateway",
        initial_files={
            "virtual-service.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: VirtualService\nmetadata:\n  name: api\nspec:\n  hosts:\n  - api.example.com\n  gateways:\n  - api-gateway\n",
            "gateway.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: Gateway\nmetadata:\n  name: api-gateway\nspec:\n  selector:\n    istio: ingressgateway\n  servers:\n  - port:\n      number: 80\n      protocol: HTTP\n",
            "unrelated.txt": "garbage_marker_k8s432 = True\nunused_marker_k8s432 = False\n",
        },
        changed_files={
            "gateway.yaml": "apiVersion: networking.istio.io/v1beta1\nkind: Gateway\nmetadata:\n  name: api-gateway\nspec:\n  selector:\n    istio: ingressgateway\n  servers:\n  - port:\n      number: 443\n      protocol: HTTPS\n    tls:\n      mode: SIMPLE\n      credentialName: api-tls\n    hosts:\n    - api.example.com\n",
        },
        must_include=["Gateway"],
        must_not_include=["garbage_marker_k8s432", "unused_marker_k8s432"],
        commit_message="Add Gateway TLS",
    ),
    DiffTestCase(
        name="k8s_433_ingress_class",
        initial_files={
            "ingress-class.yaml": "apiVersion: networking.k8s.io/v1\nkind: IngressClass\nmetadata:\n  name: nginx\nspec:\n  controller: k8s.io/ingress-nginx\n",
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  rules:\n  - host: api.example.com\n",
            "unrelated.txt": "garbage_marker_k8s433 = True\nunused_marker_k8s433 = False\n",
        },
        changed_files={
            "ingress.yaml": "apiVersion: networking.k8s.io/v1\nkind: Ingress\nmetadata:\n  name: api-ingress\nspec:\n  ingressClassName: nginx\n  rules:\n  - host: api.example.com\n",
        },
        must_include=["ingressClassName"],
        must_not_include=["garbage_marker_k8s433", "unused_marker_k8s433"],
        commit_message="Add ingress class",
    ),
    DiffTestCase(
        name="k8s_434_external_name",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: external-db\nspec:\n  type: ClusterIP\n  ports:\n  - port: 5432\n",
            "unrelated.txt": "garbage_marker_k8s434 = True\nunused_marker_k8s434 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: external-db\nspec:\n  type: ExternalName\n  externalName: db.external.com\n",
        },
        must_include=["ExternalName"],
        must_not_include=["garbage_marker_k8s434", "unused_marker_k8s434"],
        commit_message="Add ExternalName",
    ),
    DiffTestCase(
        name="k8s_435_endpoints",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: external-api\nspec:\n  ports:\n  - port: 443\n",
            "endpoints.yaml": "apiVersion: v1\nkind: Endpoints\nmetadata:\n  name: external-api\nsubsets: []\n",
            "unrelated.txt": "garbage_marker_k8s435 = True\nunused_marker_k8s435 = False\n",
        },
        changed_files={
            "endpoints.yaml": "apiVersion: v1\nkind: Endpoints\nmetadata:\n  name: external-api\nsubsets:\n- addresses:\n  - ip: 10.0.0.1\n  - ip: 10.0.0.2\n  ports:\n  - port: 443\n",
        },
        must_include=["Endpoints"],
        must_not_include=["garbage_marker_k8s435", "unused_marker_k8s435"],
        commit_message="Add Endpoints",
    ),
    DiffTestCase(
        name="k8s_436_dns_config",
        initial_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s436 = True\nunused_marker_k8s436 = False\n",
        },
        changed_files={
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      dnsPolicy: ClusterFirst\n      dnsConfig:\n        nameservers:\n        - 8.8.8.8\n        searches:\n        - default.svc.cluster.local\n      containers:\n      - name: app\n        image: myapp:latest\n",
        },
        must_include=["dnsConfig"],
        must_not_include=["garbage_marker_k8s436", "unused_marker_k8s436"],
        commit_message="Add DNS config",
    ),
    DiffTestCase(
        name="k8s_437_host_aliases",
        initial_files={
            "app.py": "import socket\nhost = socket.gethostbyname('legacy-service')\nprint(f'Connecting to {host}')\n",
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      containers:\n      - name: app\n        image: myapp:latest\n",
            "unrelated.txt": "garbage_marker_k8s437 = True\nunused_marker_k8s437 = False\n",
        },
        changed_files={
            "deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: myapp\nspec:\n  template:\n    spec:\n      hostAliases:\n      - ip: "10.0.0.1"\n        hostnames:\n        - "legacy-service"\n        - "legacy.local"\n      containers:\n      - name: app\n        image: myapp:latest\n',
        },
        must_include=["hostAliases"],
        must_not_include=["garbage_marker_k8s437", "unused_marker_k8s437"],
        commit_message="Add host aliases",
    ),
    DiffTestCase(
        name="k8s_438_service_topology",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  selector:\n    app: myapp\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s438 = True\nunused_marker_k8s438 = False\n",
        },
        changed_files={
            "service.yaml": 'apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  selector:\n    app: myapp\n  ports:\n  - port: 80\n  topologyKeys:\n  - "kubernetes.io/hostname"\n  - "topology.kubernetes.io/zone"\n  - "*"\n',
        },
        must_include=["topologyKeys"],
        must_not_include=["garbage_marker_k8s438", "unused_marker_k8s438"],
        commit_message="Add service topology",
    ),
    DiffTestCase(
        name="k8s_439_multiport_service",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s439 = True\nunused_marker_k8s439 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: myapp\nspec:\n  ports:\n  - name: http\n    port: 80\n    targetPort: 8080\n  - name: grpc\n    port: 9090\n    targetPort: 9090\n  - name: metrics\n    port: 9100\n    targetPort: 9100\n",
        },
        must_include=["grpc"],
        must_not_include=["garbage_marker_k8s439", "unused_marker_k8s439"],
        commit_message="Add multi-port service",
    ),
    DiffTestCase(
        name="k8s_440_session_affinity",
        initial_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: stateful-app\nspec:\n  selector:\n    app: stateful-app\n  ports:\n  - port: 80\n",
            "unrelated.txt": "garbage_marker_k8s440 = True\nunused_marker_k8s440 = False\n",
        },
        changed_files={
            "service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: stateful-app\nspec:\n  selector:\n    app: stateful-app\n  sessionAffinity: ClientIP\n  sessionAffinityConfig:\n    clientIP:\n      timeoutSeconds: 3600\n  ports:\n  - port: 80\n",
        },
        must_include=["sessionAffinity"],
        must_not_include=["garbage_marker_k8s440", "unused_marker_k8s440"],
        commit_message="Add session affinity",
    ),
]


ALL_K8S_CASES = K8S_DEPLOYMENT_CASES + K8S_NETWORKING_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_K8S_CASES, ids=lambda c: c.name)
def test_k8s_context_selection(diff_test_runner, case):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
