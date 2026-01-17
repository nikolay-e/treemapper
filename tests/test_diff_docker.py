import pytest

from tests.utils import DiffTestCase, DiffTestRunner

DOCKERFILE_CASES = [
    DiffTestCase(
        name="docker_501_from_base_image",
        initial_files={
            "requirements.txt": "flask==2.0.0\ngunicorn==20.1.0\n",
            "Dockerfile": 'FROM alpine:3.14\nCMD ["echo", "hello"]\n',
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "Dockerfile": "FROM python:3.11-slim\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\n",
        },
        must_include=["FROM python:3.11-slim"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update base image",
    ),
    DiffTestCase(
        name="docker_502_multi_stage_build",
        initial_files={
            "Dockerfile": 'FROM node:18\nCOPY . .\nRUN npm run build\nCMD ["node", "dist/index.js"]\n',
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": """FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/index.js"]
""",
        },
        must_include=["FROM node:18 AS builder", "COPY --from=builder"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add multi-stage build",
    ),
    DiffTestCase(
        name="docker_503_copy_source",
        initial_files={
            "requirements.txt": "flask==2.0.0\nrequests==2.26.0\n",
            "Dockerfile": "FROM python:3.11-slim\nRUN pip install flask\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": "FROM python:3.11-slim\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\n",
        },
        must_include=["COPY requirements.txt"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add COPY",
    ),
    DiffTestCase(
        name="docker_504_run_command",
        initial_files={
            "requirements.txt": "flask==2.0.0\ngunicorn==20.1.0\npsycopg2-binary==2.9.0\n",
            "Dockerfile": "FROM python:3.11-slim\nCOPY requirements.txt .\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "Dockerfile": "FROM python:3.11-slim\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n",
        },
        must_include=["RUN pip install --no-cache-dir"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add RUN",
    ),
    DiffTestCase(
        name="docker_505_workdir",
        initial_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY . /app\nRUN cd /app && pip install -r requirements.txt\nCMD ["python", "/app/main.py"]\n',
            "unrelated.txt": "garbage_marker_12345 unused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ["python", "main.py"]\n',
        },
        must_include=["WORKDIR /app"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add WORKDIR",
    ),
    DiffTestCase(
        name="docker_506_env",
        initial_files={
            "app.js": "const env = process.env.NODE_ENV || 'development';\nconsole.log(`Running in ${env} mode`);\n",
            "Dockerfile": 'FROM node:18\nCOPY . .\nCMD ["node", "app.js"]\n',
            "junk.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM node:18\nENV NODE_ENV=production\nCOPY . .\nCMD ["node", "app.js"]\n',
        },
        must_include=["ENV NODE_ENV=production"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ENV",
    ),
    DiffTestCase(
        name="docker_507_arg",
        initial_files={
            "Dockerfile": "FROM node:18\nCOPY . .\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "Dockerfile": 'ARG VERSION=latest\nFROM node:18\nARG BUILD_DATE\nLABEL version="${VERSION}" build-date="${BUILD_DATE}"\nCOPY . .\n',
        },
        must_include=["ARG VERSION=latest"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ARG",
    ),
    DiffTestCase(
        name="docker_508_expose",
        initial_files={
            "app.py": "from flask import Flask\napp = Flask(__name__)\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8080)\n",
            "Dockerfile": 'FROM python:3.11-slim\nCOPY . .\nCMD ["python", "app.py"]\n',
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY . .\nEXPOSE 8080\nCMD ["python", "app.py"]\n',
        },
        must_include=["EXPOSE 8080"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add EXPOSE",
    ),
    DiffTestCase(
        name="docker_509_entrypoint",
        initial_files={
            "app.py": "import sys\nprint(f'Args: {sys.argv[1:]}')\n",
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nCMD ["python", "app.py"]\n',
            "junk.txt": "garbage_marker_12345 unused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nENTRYPOINT ["python", "app.py"]\nCMD ["--default-arg"]\n',
        },
        must_include=["ENTRYPOINT"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ENTRYPOINT",
    ),
    DiffTestCase(
        name="docker_510_cmd",
        initial_files={
            "app.py": "import argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--port', default=8080)\nargs = parser.parse_args()\nprint(f'Port: {args.port}')\n",
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nENTRYPOINT ["python", "app.py"]\n',
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nENTRYPOINT ["python", "app.py"]\nCMD ["--port", "8080"]\n',
        },
        must_include=["CMD"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add CMD",
    ),
    DiffTestCase(
        name="docker_511_healthcheck",
        initial_files={
            "app.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/health')\ndef health():\n    return 'OK', 200\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=8080)\n",
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nRUN pip install flask\nCMD ["python", "app.py"]\n',
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nRUN pip install flask\nHEALTHCHECK --interval=30s --timeout=3s --start-period=5s \\\n    CMD curl -f http://localhost:8080/health || exit 1\nCMD ["python", "app.py"]\n',
        },
        must_include=["HEALTHCHECK"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add HEALTHCHECK",
    ),
    DiffTestCase(
        name="docker_512_user",
        initial_files={
            "Dockerfile": 'FROM python:3.11-slim\nCOPY . /app\nCMD ["python", "/app/main.py"]\n',
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nRUN useradd -m appuser\nCOPY --chown=appuser:appuser . /app\nUSER appuser\nWORKDIR /app\nCMD ["python", "main.py"]\n',
        },
        must_include=["USER appuser"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add USER",
    ),
    DiffTestCase(
        name="docker_513_volume",
        initial_files={
            "app.py": "import os\ndata_dir = '/data'\nos.makedirs(data_dir, exist_ok=True)\nwith open(os.path.join(data_dir, 'test.txt'), 'w') as f:\n    f.write('test')\n",
            "Dockerfile": 'FROM python:3.11-slim\nCOPY app.py .\nCMD ["python", "app.py"]\n',
            "junk.txt": "garbage_marker_12345 unused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nVOLUME /data\nCOPY app.py .\nCMD ["python", "app.py"]\n',
        },
        must_include=["VOLUME /data"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add VOLUME",
    ),
    DiffTestCase(
        name="docker_514_label",
        initial_files={
            "Dockerfile": "FROM python:3.11-slim\nCOPY . .\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "Dockerfile": 'FROM python:3.11-slim\nLABEL version="1.0" \\\n      maintainer="team@example.com" \\\n      description="My application"\nCOPY . .\n',
        },
        must_include=["LABEL"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add LABEL",
    ),
    DiffTestCase(
        name="docker_515_add_vs_copy",
        initial_files={
            "Dockerfile": "FROM python:3.11-slim\nCOPY files.tar.gz /app/\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "Dockerfile": "FROM python:3.11-slim\nADD files.tar.gz /app/\nADD https://example.com/config.json /app/config.json\n",
        },
        must_include=["ADD files.tar.gz"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Use ADD",
    ),
]

COMPOSE_CASES = [
    DiffTestCase(
        name="docker_516_compose_service",
        initial_files={
            "api/Dockerfile": 'FROM python:3.11-slim\nCOPY . .\nCMD ["python", "app.py"]\n',
            "docker-compose.yml": "version: '3.8'\nservices: {}\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: ./api
    ports:
      - "8080:8080"
""",
        },
        must_include=["build: ./api"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add compose service",
    ),
    DiffTestCase(
        name="docker_517_compose_volumes",
        initial_files={
            "app.py": "import os\ndata = open('/app/data/config.json').read()\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    volumes:
      - ./data:/app/data
      - logs:/app/logs
volumes:
  logs:
""",
        },
        must_include=["volumes:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add compose volumes",
    ),
    DiffTestCase(
        name="docker_518_compose_environment",
        initial_files={
            ".env": "DB_URL=postgres://localhost:5432/mydb\nSECRET_KEY=mysecret\n",
            "app.py": "import os\ndb_url = os.environ.get('DATABASE_URL')\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    environment:
      - DATABASE_URL=${DB_URL}
      - SECRET_KEY=${SECRET_KEY}
""",
        },
        must_include=["environment:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add compose environment",
    ),
    DiffTestCase(
        name="docker_519_compose_depends_on",
        initial_files={
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n  db:\n    image: postgres:13\n",
            "junk.txt": "garbage_marker_12345 unused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:13
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
""",
        },
        must_include=["depends_on:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add depends_on",
    ),
    DiffTestCase(
        name="docker_520_compose_networks",
        initial_files={
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n  db:\n    image: postgres:13\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    networks:
      - frontend
      - backend
  db:
    image: postgres:13
    networks:
      - backend
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
""",
        },
        must_include=["networks:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add networks",
    ),
    DiffTestCase(
        name="docker_521_compose_ports",
        initial_files={
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:80"
      - "127.0.0.1:9090:9090"
""",
        },
        must_include=["ports:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add ports",
    ),
    DiffTestCase(
        name="docker_522_compose_healthcheck",
        initial_files={
            "app.py": "from flask import Flask\napp = Flask(__name__)\n\n@app.route('/health')\ndef health():\n    return 'OK'\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
""",
        },
        must_include=["healthcheck:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add healthcheck",
    ),
    DiffTestCase(
        name="docker_523_compose_profiles",
        initial_files={
            "docker-compose.yml": 'version: \'3.8\'\nservices:\n  api:\n    build: .\n  debug:\n    image: busybox\n    command: ["tail", "-f", "/dev/null"]\n',
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
  debug:
    image: busybox
    command: ["tail", "-f", "/dev/null"]
    profiles:
      - debug
""",
        },
        must_include=["profiles:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add profiles",
    ),
    DiffTestCase(
        name="docker_524_compose_secrets",
        initial_files={
            "db_password.txt": "supersecret123",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    secrets:
      - db_password
secrets:
  db_password:
    file: ./db_password.txt
""",
        },
        must_include=["secrets:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add secrets",
    ),
    DiffTestCase(
        name="docker_525_compose_configs",
        initial_files={
            "nginx.conf": "server {\n    listen 80;\n    location / {\n        proxy_pass http://api:8080;\n    }\n}\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  nginx:\n    image: nginx:latest\n",
            "junk.txt": "garbage_marker_12345 unused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  nginx:
    image: nginx:latest
    configs:
      - source: nginx_conf
        target: /etc/nginx/conf.d/default.conf
configs:
  nginx_conf:
    file: ./nginx.conf
""",
        },
        must_include=["configs:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add configs",
    ),
    DiffTestCase(
        name="docker_526_compose_deploy",
        initial_files={
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "unrelated.py": "garbage_marker_12345 = True\nunused_marker_67890 = False\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
""",
        },
        must_include=["deploy:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add deploy",
    ),
    DiffTestCase(
        name="docker_527_compose_extends",
        initial_files={
            "common.yml": "version: '3.8'\nservices:\n  base:\n    environment:\n      - LOG_LEVEL=info\n    logging:\n      driver: json-file\n      options:\n        max-size: \"10m\"\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "junk.md": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    extends:
      file: common.yml
      service: base
    build: .
""",
        },
        must_include=["extends:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add extends",
    ),
    DiffTestCase(
        name="docker_528_compose_env_file",
        initial_files={
            ".env.local": "DATABASE_URL=postgres://localhost:5432/dev\nDEBUG=true\n",
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n",
            "unrelated.txt": "garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    env_file:
      - .env.local
""",
        },
        must_include=["env_file:"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add env_file",
    ),
    DiffTestCase(
        name="docker_529_dockerignore",
        initial_files={
            ".dockerignore": "*.log\n",
            "junk.py": "garbage_marker_12345 = 1\nunused_marker_67890 = 2\n",
        },
        changed_files={
            ".dockerignore": "node_modules\n*.log\n.git\n.env*\n__pycache__\n*.pyc\n.pytest_cache\ncoverage/\ndist/\n",
        },
        must_include=["node_modules"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Update dockerignore",
    ),
    DiffTestCase(
        name="docker_530_compose_override",
        initial_files={
            "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .\n    environment:\n      - NODE_ENV=production\n",
            "docker-compose.override.yml": "version: '3.8'\n",
            "unrelated.md": "# garbage_marker_12345\nunused_marker_67890\n",
        },
        changed_files={
            "docker-compose.override.yml": """version: '3.8'
services:
  api:
    environment:
      - NODE_ENV=development
      - DEBUG=true
    volumes:
      - .:/app
    ports:
      - "3000:3000"
""",
        },
        must_include=["NODE_ENV=development"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add override",
    ),
]

ALL_DOCKER_CASES = DOCKERFILE_CASES + COMPOSE_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_DOCKER_CASES, ids=lambda c: c.name)
def test_docker_context_selection(diff_test_runner, case):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
