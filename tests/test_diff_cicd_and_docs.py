import pytest

from tests.utils import DiffTestCase, DiffTestRunner

GITHUB_ACTIONS_CASES = [
    DiffTestCase(
        name="cicd_001_gha_workflow_trigger",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_002_gha_workflow_jobs",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
  test:
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - run: npm test
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_003_gha_checkout_action",
        initial_files={
            "package.json": """{
  "name": "myapp",
  "scripts": { "build": "echo build" }
}
""",
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo "no checkout"
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_004_gha_setup_action",
        initial_files={
            "package.json": """{
  "name": "myapp",
  "engines": { "node": ">=18" }
}
""",
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: npm
      - run: npm install
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_005_gha_run_step",
        initial_files={
            "package.json": """{
  "scripts": {
    "test": "jest",
    "lint": "eslint ."
  }
}
""",
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm install
      - run: npm test
      - run: npm run lint
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_006_gha_env_variables",
        initial_files={
            "app.js": """const isCI = process.env.CI === 'true';
console.log('Running in CI:', isCI);
""",
            ".github/workflows/ci.yml": """name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: node app.js
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      CI: true
      NODE_ENV: test
    steps:
      - uses: actions/checkout@v4
      - run: node app.js
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_007_gha_secrets",
        initial_files={
            ".github/workflows/deploy.yml": """name: Deploy
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "deploy"
""",
        },
        changed_files={
            ".github/workflows/deploy.yml": """name: Deploy
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
          AWS_ACCESS_KEY: ${{ secrets.AWS_ACCESS_KEY }}
        run: ./deploy.sh
""",
        },
        must_include=["deploy.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_008_gha_matrix",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node: [16, 18, 20]
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - run: npm test
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_009_gha_needs",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test
  deploy:
    runs-on: ubuntu-latest
    needs: [build, test]
    steps:
      - run: ./deploy.sh
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_010_gha_if_conditional",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - run: ./deploy.sh
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_011_gha_artifacts",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_012_gha_cache",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v4
        with:
          path: ~/.npm
          key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-
      - run: npm ci
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_013_gha_concurrency",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_014_gha_permissions",
        initial_files={
            ".github/workflows/release.yml": """name: Release
on:
  push:
    tags: ['v*']
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - run: echo "release"
""",
        },
        changed_files={
            ".github/workflows/release.yml": """name: Release
on:
  push:
    tags: ['v*']
jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Create Release
        uses: softprops/action-gh-release@v1
""",
        },
        must_include=["release.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_015_gha_reusable_workflow",
        initial_files={
            ".github/workflows/deploy.yml": """name: Deploy
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - run: ./deploy.sh
""",
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
  deploy:
    needs: build
    uses: ./.github/workflows/deploy.yml
    with:
      environment: production
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_016_gha_composite_action",
        initial_files={
            ".github/actions/setup/action.yml": """name: Setup
description: Setup environment
""",
        },
        changed_files={
            ".github/actions/setup/action.yml": """name: Setup
description: Setup environment
runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: 18
    - run: npm ci
      shell: bash
    - run: npm run build
      shell: bash
""",
        },
        must_include=["action.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_017_gha_service_container",
        initial_files={
            "tests/db.test.js": """const { Pool } = require('pg');
test('connects to database', async () => {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  await pool.query('SELECT 1');
});
""",
            ".github/workflows/test.yml": """name: Test
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: npm test
""",
        },
        changed_files={
            ".github/workflows/test.yml": """name: Test
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm test
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
""",
        },
        must_include=["test.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_018_gha_environment",
        initial_files={
            ".github/workflows/deploy.yml": """name: Deploy
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
""",
        },
        changed_files={
            ".github/workflows/deploy.yml": """name: Deploy
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
""",
        },
        must_include=["deploy.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_019_gha_outputs",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  version:
    runs-on: ubuntu-latest
    steps:
      - run: echo "1.0.0"
  deploy:
    needs: version
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  version:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}
    steps:
      - id: version
        run: echo "value=1.0.0" >> $GITHUB_OUTPUT
  deploy:
    needs: version
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh --version ${{ needs.version.outputs.version }}
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_020_gha_timeout",
        initial_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
""",
        },
        changed_files={
            ".github/workflows/ci.yml": """name: CI
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - run: npm run build
        timeout-minutes: 15
""",
        },
        must_include=["ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]

GITLAB_CI_CASES = [
    DiffTestCase(
        name="cicd_021_gitlab_stages",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
""",
        },
        changed_files={
            ".gitlab-ci.yml": """stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - npm run build

test:
  stage: test
  script:
    - npm test

deploy:
  stage: deploy
  script:
    - ./deploy.sh
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_022_gitlab_image",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
""",
        },
        changed_files={
            ".gitlab-ci.yml": """image: node:18-alpine

build:
  script:
    - npm ci
    - npm run build
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_023_gitlab_script",
        initial_files={
            "package.json": """{
  "scripts": {
    "test": "jest",
    "build": "tsc"
  }
}
""",
            ".gitlab-ci.yml": """test:
  script:
    - echo "test"
""",
        },
        changed_files={
            ".gitlab-ci.yml": """test:
  script:
    - npm ci
    - npm test
    - npm run build
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_024_gitlab_before_script",
        initial_files={
            ".gitlab-ci.yml": """test:
  script:
    - npm test
""",
        },
        changed_files={
            ".gitlab-ci.yml": """test:
  before_script:
    - apt-get update
    - apt-get install -y curl
  script:
    - npm test
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_025_gitlab_after_script",
        initial_files={
            "cleanup.sh": """#!/bin/bash
rm -rf /tmp/test-*
""",
            ".gitlab-ci.yml": """test:
  script:
    - npm test
""",
        },
        changed_files={
            ".gitlab-ci.yml": """test:
  script:
    - npm test
  after_script:
    - ./cleanup.sh
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_026_gitlab_variables",
        initial_files={
            "app.js": """console.log('NODE_ENV:', process.env.NODE_ENV);
""",
            ".gitlab-ci.yml": """test:
  script:
    - node app.js
""",
        },
        changed_files={
            ".gitlab-ci.yml": """variables:
  NODE_ENV: production
  CI_DEBUG: "true"

test:
  script:
    - node app.js
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_027_gitlab_rules",
        initial_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG
      when: always
    - when: never
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_028_gitlab_only_except",
        initial_files={
            ".gitlab-ci.yml": """release:
  script:
    - ./release.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """release:
  script:
    - ./release.sh
  only:
    - tags
  except:
    - branches
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_029_gitlab_artifacts",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
""",
        },
        changed_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_030_gitlab_cache",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm ci
""",
        },
        changed_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm ci
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - node_modules/
    policy: pull-push
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_031_gitlab_needs",
        initial_files={
            ".gitlab-ci.yml": """stages:
  - build
  - deploy

build:
  stage: build
  script:
    - npm run build

deploy:
  stage: deploy
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """stages:
  - build
  - deploy

build:
  stage: build
  script:
    - npm run build

deploy:
  stage: deploy
  needs: [build]
  script:
    - ./deploy.sh
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_032_gitlab_dependencies",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

deploy:
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

deploy:
  dependencies:
    - build
  script:
    - ./deploy.sh dist/
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_033_gitlab_include",
        initial_files={
            ".gitlab/ci/deploy.yml": """deploy:
  script:
    - ./deploy.sh
""",
            ".gitlab-ci.yml": """build:
  script:
    - npm run build
""",
        },
        changed_files={
            ".gitlab-ci.yml": """include:
  - local: .gitlab/ci/deploy.yml

build:
  script:
    - npm run build
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_034_gitlab_extends",
        initial_files={
            ".gitlab-ci.yml": """build:
  script:
    - npm run build

test:
  script:
    - npm test
""",
        },
        changed_files={
            ".gitlab-ci.yml": """.base-job:
  image: node:18
  before_script:
    - npm ci

build:
  extends: .base-job
  script:
    - npm run build

test:
  extends: .base-job
  script:
    - npm test
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_035_gitlab_trigger",
        initial_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """deploy:
  trigger:
    project: team/deploy
    branch: main
    strategy: depend
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_036_gitlab_environment",
        initial_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
  environment:
    name: production
    url: https://app.example.com
    on_stop: stop_production
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_037_gitlab_services",
        initial_files={
            "tests/db.test.js": """test('database', () => {});
""",
            ".gitlab-ci.yml": """test:
  script:
    - npm test
""",
        },
        changed_files={
            ".gitlab-ci.yml": """test:
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
  script:
    - npm test
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_038_gitlab_when",
        initial_files={
            ".gitlab-ci.yml": """deploy_prod:
  script:
    - ./deploy.sh production
""",
        },
        changed_files={
            ".gitlab-ci.yml": """deploy_prod:
  script:
    - ./deploy.sh production
  when: manual
  allow_failure: false
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_039_gitlab_parallel",
        initial_files={
            "tests/browser.test.js": """const browser = process.env.BROWSER;
test('works in ' + browser, () => {});
""",
            ".gitlab-ci.yml": """e2e:
  script:
    - npm run test:e2e
""",
        },
        changed_files={
            ".gitlab-ci.yml": """e2e:
  parallel:
    matrix:
      - BROWSER: [chrome, firefox, safari]
  script:
    - npm run test:e2e -- --browser=$BROWSER
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="cicd_040_gitlab_resource_group",
        initial_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
""",
        },
        changed_files={
            ".gitlab-ci.yml": """deploy:
  script:
    - ./deploy.sh
  resource_group: production
""",
        },
        must_include=[".gitlab-ci.yml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]

DOCUMENTATION_CASES = [
    DiffTestCase(
        name="docs_001_readme_code_example",
        initial_files={
            "README.md": """# My Library

## Usage

```python
from mylib import process

result = process(data)
print(result)
```
""",
            "examples/basic_usage.py": """from mylib import process

data = [1, 2, 3]
result = process(data)
print(result)
""",
        },
        changed_files={
            "README.md": """# My Library

## Usage

```python
from mylib import process, transform

# Basic usage
result = process(data)
print(result)

# Advanced usage with transformation
transformed = transform(data, options={'format': 'json'})
result = process(transformed)
```

## Configuration

See `examples/basic_usage.py` for more examples.
""",
        },
        must_include=["README.md"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_002_jsdoc_param_type",
        initial_files={
            "src/types.ts": """export interface User {
    id: number;
    name: string;
}

export interface Order {
    id: number;
    userId: number;
}
""",
            "src/service.ts": """import { User, Order } from './types';

/**
 * Process an order for a user
 * @param {User} user - The user placing the order
 * @param {Order} order - The order to process
 * @returns {boolean} Success status
 */
function processOrder(user: User, order: Order): boolean {
    return true;
}
""",
        },
        changed_files={
            "src/service.ts": """import { User, Order, PaymentMethod } from './types';

/**
 * Process an order for a user
 * @param {User} user - The user placing the order
 * @param {Order} order - The order to process
 * @param {PaymentMethod} payment - Payment method to use
 * @returns {Promise<ProcessResult>} Processing result
 * @throws {ValidationError} If order is invalid
 */
async function processOrder(
    user: User,
    order: Order,
    payment: PaymentMethod
): Promise<ProcessResult> {
    validateOrder(order);
    return { success: true, orderId: order.id };
}
""",
        },
        must_include=["service.ts"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_003_tsdoc_link",
        initial_files={
            "src/utils/formatter.ts": """export class Formatter {
    format(value: string): string {
        return value.trim();
    }
}
""",
            "src/services/data.ts": """import { Formatter } from '../utils/formatter';

/**
 * Data processor that uses {@link Formatter} for output
 */
export class DataProcessor {
    private formatter: Formatter;

    constructor() {
        this.formatter = new Formatter();
    }
}
""",
        },
        changed_files={
            "src/services/data.ts": """import { Formatter, JsonFormatter } from '../utils/formatter';

/**
 * Data processor that uses {@link Formatter} for output
 *
 * @remarks
 * This class provides data processing capabilities.
 * See {@link JsonFormatter} for JSON-specific formatting.
 *
 * @example
 * ```typescript
 * const processor = new DataProcessor();
 * const result = processor.process(data);
 * ```
 */
export class DataProcessor {
    private formatter: Formatter;

    constructor(formatter?: Formatter) {
        this.formatter = formatter ?? new Formatter();
    }

    /**
     * Process data and return formatted result
     * @param data - Input data to process
     * @returns Formatted output string
     */
    process(data: unknown): string {
        return this.formatter.format(String(data));
    }
}
""",
        },
        must_include=["data.ts"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_004_sphinx_func_reference",
        initial_files={
            "docs/api.rst": """API Reference
=============

Functions
---------

.. autofunction:: mylib.process

See :func:`mylib.process` for data processing.
""",
            "src/mylib/core.py": """def process(data):
    return [x * 2 for x in data]
""",
        },
        changed_files={
            "docs/api.rst": """API Reference
=============

Functions
---------

.. autofunction:: mylib.process
.. autofunction:: mylib.transform
.. autofunction:: mylib.validate

See :func:`mylib.process` for data processing.
Use :func:`mylib.transform` to convert data formats.
Call :func:`mylib.validate` before processing.

Classes
-------

.. autoclass:: mylib.Processor
   :members:
""",
        },
        must_include=["api.rst"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_005_doctest_example",
        initial_files={
            "src/calculator.py": '''def add(a, b):
    """Add two numbers.

    >>> add(2, 3)
    5
    """
    return a + b
''',
        },
        changed_files={
            "src/calculator.py": '''def add(a, b):
    """Add two numbers.

    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    >>> add(0.1, 0.2)  # doctest: +ELLIPSIS
    0.3...
    """
    return a + b


def multiply(a, b):
    """Multiply two numbers.

    >>> multiply(2, 3)
    6
    >>> multiply(0, 100)
    0
    """
    return a * b
''',
        },
        must_include=["calculator.py"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_006_example_annotation",
        initial_files={
            "src/parser.ts": """/**
 * Parse JSON string
 * @example
 * const data = parse('{"key": "value"}');
 */
export function parse(input: string): object {
    return JSON.parse(input);
}
""",
            "examples/parsing.ts": """import { parse } from '../src/parser';

const data = parse('{"key": "value"}');
console.log(data);
""",
        },
        changed_files={
            "src/parser.ts": """/**
 * Parse JSON string with validation
 * @example
 * // Basic usage
 * const data = parse('{"key": "value"}');
 *
 * @example
 * // With schema validation
 * const schema = { type: 'object', required: ['key'] };
 * const data = parse('{"key": "value"}', { schema });
 *
 * @example
 * // See examples/parsing.ts for more examples
 */
export function parse(input: string, options?: ParseOptions): object {
    const parsed = JSON.parse(input);
    if (options?.schema) {
        validate(parsed, options.schema);
    }
    return parsed;
}
""",
        },
        must_include=["parser.ts"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_007_api_endpoint_docs",
        initial_files={
            "docs/api/users.md": """# Users API

## GET /api/users

Returns a list of users.

### Response

```json
[{"id": 1, "name": "John"}]
```
""",
            "src/handlers/users.py": """def list_users():
    return [{"id": 1, "name": "John"}]
""",
        },
        changed_files={
            "docs/api/users.md": """# Users API

## GET /api/users

Returns a list of users.

### Parameters

| Name | Type | Description |
|------|------|-------------|
| limit | integer | Max results (default: 10) |
| offset | integer | Pagination offset |

### Response

```json
{
    "data": [{"id": 1, "name": "John"}],
    "total": 100,
    "limit": 10,
    "offset": 0
}
```

## POST /api/users

Create a new user.

### Request Body

```json
{"name": "John", "email": "john@example.com"}
```
""",
        },
        must_include=["users.md"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_008_architecture_module_mention",
        initial_files={
            "docs/architecture.md": """# Architecture

## Overview

The system consists of several modules:

- `auth` - Authentication
- `api` - REST API endpoints
""",
            "src/auth/login.py": """def login(username, password):
    return {"token": "abc123"}
""",
            "src/api/routes.py": """from auth.login import login

def setup_routes(app):
    app.post("/login", login)
""",
        },
        changed_files={
            "docs/architecture.md": """# Architecture

## Overview

The system consists of several modules:

- `auth` - Authentication and authorization
- `api` - REST API endpoints
- `cache` - Redis caching layer
- `events` - Event publishing and handling

## Module Dependencies

```
api -> auth -> cache
api -> events
```

## Data Flow

1. Request hits `api` module
2. `auth` validates token
3. `cache` checks for cached response
4. `events` publishes audit event
""",
        },
        must_include=["architecture.md"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_009_changelog_pr_reference",
        initial_files={
            "CHANGELOG.md": """# Changelog

## [1.0.0] - 2024-01-01

### Added
- Initial release
""",
            "src/feature.py": """def new_feature():
    pass
""",
        },
        changed_files={
            "CHANGELOG.md": """# Changelog

## [1.1.0] - 2024-02-01

### Added
- User authentication (#123)
- OAuth2 support (#125)

### Fixed
- Login timeout issue (#124)

### Changed
- Updated API response format (#126)

## [1.0.0] - 2024-01-01

### Added
- Initial release
""",
        },
        must_include=["CHANGELOG.md"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_010_see_other_class",
        initial_files={
            "src/base_handler.py": """class BaseHandler:
    def handle(self, request):
        raise NotImplementedError
""",
            "src/user_handler.py": '''class UserHandler:
    """Handle user requests.

    @see BaseHandler for the base implementation
    """
    def handle(self, request):
        return {"user": "data"}
''',
        },
        changed_files={
            "src/user_handler.py": '''from base_handler import BaseHandler

class UserHandler(BaseHandler):
    """Handle user requests.

    This handler processes user-related API requests.

    @see BaseHandler for the base implementation
    @see OrderHandler for order processing
    @see AuthMiddleware for authentication

    Attributes:
        cache: Redis cache instance
        logger: Logger instance
    """
    def __init__(self, cache, logger):
        self.cache = cache
        self.logger = logger

    def handle(self, request):
        self.logger.info("Handling user request")
        return {"user": "data"}
''',
        },
        must_include=["user_handler.py"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]

API_SPECS_CASES = [
    DiffTestCase(
        name="docs_011_openapi_paths",
        initial_files={
            "openapi.yaml": """openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      responses:
        '200':
          description: List of users
""",
            "src/handlers/users.py": """from flask import jsonify

def list_users():
    return jsonify([{"id": 1, "name": "John"}])
""",
        },
        changed_files={
            "openapi.yaml": """openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: List of users
    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUser'
      responses:
        '201':
          description: User created
""",
        },
        must_include=["openapi.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_012_openapi_ref_schema",
        initial_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /users/{id}:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
""",
        },
        changed_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /users/{id}:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        address:
          $ref: '#/components/schemas/Address'
    Address:
      type: object
      properties:
        street:
          type: string
        city:
          type: string
        country:
          type: string
""",
        },
        must_include=["openapi.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_013_openapi_request_body",
        initial_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /orders:
    post:
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
""",
            "src/validators/order_validator.py": """def validate_order(data):
    if 'items' not in data:
        raise ValueError("Items required")
    return True
""",
        },
        changed_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /orders:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - items
                - shipping_address
              properties:
                items:
                  type: array
                  minItems: 1
                shipping_address:
                  type: string
                notes:
                  type: string
                  maxLength: 500
""",
        },
        must_include=["openapi.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_014_openapi_responses",
        initial_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /products/{id}:
    get:
      responses:
        '200':
          description: Product found
          content:
            application/json:
              schema:
                type: object
""",
            "src/serializers/product.py": """def serialize_product(product):
    return {"id": product.id, "name": product.name}
""",
        },
        changed_files={
            "openapi.yaml": """openapi: 3.0.0
paths:
  /products/{id}:
    get:
      responses:
        '200':
          description: Product found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProductResponse'
        '404':
          description: Product not found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
        '500':
          description: Internal server error
components:
  schemas:
    ProductResponse:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        price:
          type: number
    Error:
      type: object
      properties:
        code:
          type: string
        message:
          type: string
""",
        },
        must_include=["openapi.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_015_graphql_query",
        initial_files={
            "schema.graphql": """type Query {
    user(id: ID!): User
    users: [User!]!
}

type User {
    id: ID!
    name: String!
}
""",
            "src/resolvers/user_resolver.py": """def resolve_user(obj, info, id):
    return get_user_by_id(id)

def resolve_users(obj, info):
    return get_all_users()
""",
        },
        changed_files={
            "schema.graphql": """type Query {
    user(id: ID!): User
    users(limit: Int = 10, offset: Int = 0): [User!]!
    searchUsers(query: String!): [User!]!
}

type User {
    id: ID!
    name: String!
    email: String
    orders: [Order!]!
}

type Order {
    id: ID!
    total: Float!
}
""",
        },
        must_include=["schema.graphql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_016_graphql_mutation",
        initial_files={
            "schema.graphql": """type Mutation {
    createUser(input: CreateUserInput!): User!
}

input CreateUserInput {
    name: String!
    email: String!
}
""",
            "src/resolvers/mutations.py": """def resolve_create_user(obj, info, input):
    return create_user(input['name'], input['email'])
""",
        },
        changed_files={
            "schema.graphql": """type Mutation {
    createUser(input: CreateUserInput!): User!
    updateUser(id: ID!, input: UpdateUserInput!): User!
    deleteUser(id: ID!): Boolean!
}

input CreateUserInput {
    name: String!
    email: String!
    role: UserRole = USER
}

input UpdateUserInput {
    name: String
    email: String
}

enum UserRole {
    USER
    ADMIN
    MODERATOR
}
""",
        },
        must_include=["schema.graphql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_017_graphql_extend_type",
        initial_files={
            "schema/base.graphql": """type Query {
    health: String!
}

type User {
    id: ID!
    name: String!
}
""",
            "schema/orders.graphql": """extend type Query {
    orders: [Order!]!
}

extend type User {
    orders: [Order!]!
}

type Order {
    id: ID!
    total: Float!
}
""",
        },
        changed_files={
            "schema/orders.graphql": """extend type Query {
    orders(status: OrderStatus): [Order!]!
    order(id: ID!): Order
}

extend type User {
    orders(limit: Int = 10): [Order!]!
    totalSpent: Float!
}

type Order {
    id: ID!
    total: Float!
    status: OrderStatus!
    items: [OrderItem!]!
}

type OrderItem {
    id: ID!
    product: String!
    quantity: Int!
}

enum OrderStatus {
    PENDING
    CONFIRMED
    SHIPPED
    DELIVERED
}
""",
        },
        must_include=["orders.graphql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_018_protobuf_message",
        initial_files={
            "proto/user.proto": """syntax = "proto3";

package user;

message User {
    int64 id = 1;
    string name = 2;
}
""",
            "src/services/user_service.py": """from proto import user_pb2

def create_user_proto(user):
    proto = user_pb2.User()
    proto.id = user.id
    proto.name = user.name
    return proto
""",
        },
        changed_files={
            "proto/user.proto": """syntax = "proto3";

package user;

import "google/protobuf/timestamp.proto";

message User {
    int64 id = 1;
    string name = 2;
    string email = 3;
    UserStatus status = 4;
    google.protobuf.Timestamp created_at = 5;
}

enum UserStatus {
    USER_STATUS_UNSPECIFIED = 0;
    USER_STATUS_ACTIVE = 1;
    USER_STATUS_INACTIVE = 2;
    USER_STATUS_BANNED = 3;
}
""",
        },
        must_include=["user.proto"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_019_protobuf_service",
        initial_files={
            "proto/user_service.proto": """syntax = "proto3";

package user;

service UserService {
    rpc GetUser(GetUserRequest) returns (User);
}

message GetUserRequest {
    int64 id = 1;
}

message User {
    int64 id = 1;
    string name = 2;
}
""",
            "src/grpc/user_service.py": """class UserServiceServicer:
    def GetUser(self, request, context):
        user = get_user(request.id)
        return User(id=user.id, name=user.name)
""",
        },
        changed_files={
            "proto/user_service.proto": """syntax = "proto3";

package user;

service UserService {
    rpc GetUser(GetUserRequest) returns (User);
    rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
    rpc CreateUser(CreateUserRequest) returns (User);
    rpc UpdateUser(UpdateUserRequest) returns (User);
    rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
}

message GetUserRequest {
    int64 id = 1;
}

message ListUsersRequest {
    int32 page_size = 1;
    string page_token = 2;
}

message ListUsersResponse {
    repeated User users = 1;
    string next_page_token = 2;
}

message CreateUserRequest {
    string name = 1;
    string email = 2;
}

message UpdateUserRequest {
    int64 id = 1;
    string name = 2;
    string email = 3;
}

message DeleteUserRequest {
    int64 id = 1;
}

message DeleteUserResponse {
    bool success = 1;
}

message User {
    int64 id = 1;
    string name = 2;
    string email = 3;
}
""",
        },
        must_include=["user_service.proto"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_020_protobuf_import",
        initial_files={
            "proto/common.proto": """syntax = "proto3";

package common;

message Pagination {
    int32 page = 1;
    int32 page_size = 2;
}
""",
            "proto/orders.proto": """syntax = "proto3";

package orders;

import "proto/common.proto";

message ListOrdersRequest {
    common.Pagination pagination = 1;
}
""",
        },
        changed_files={
            "proto/common.proto": """syntax = "proto3";

package common;

message Pagination {
    int32 page = 1;
    int32 page_size = 2;
    string sort_by = 3;
    SortOrder sort_order = 4;
}

enum SortOrder {
    SORT_ORDER_UNSPECIFIED = 0;
    SORT_ORDER_ASC = 1;
    SORT_ORDER_DESC = 2;
}

message DateRange {
    string start_date = 1;
    string end_date = 2;
}
""",
        },
        must_include=["common.proto"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_021_asyncapi_channels",
        initial_files={
            "asyncapi.yaml": """asyncapi: 2.6.0
info:
  title: Order Events
  version: 1.0.0
channels:
  orders/created:
    publish:
      message:
        payload:
          type: object
          properties:
            orderId:
              type: string
""",
            "src/events/order_publisher.py": """def publish_order_created(order_id):
    publish('orders/created', {'orderId': order_id})
""",
        },
        changed_files={
            "asyncapi.yaml": """asyncapi: 2.6.0
info:
  title: Order Events
  version: 1.0.0
channels:
  orders/created:
    publish:
      message:
        payload:
          $ref: '#/components/schemas/OrderCreatedEvent'
  orders/updated:
    publish:
      message:
        payload:
          $ref: '#/components/schemas/OrderUpdatedEvent'
  orders/shipped:
    subscribe:
      message:
        payload:
          $ref: '#/components/schemas/OrderShippedEvent'
components:
  schemas:
    OrderCreatedEvent:
      type: object
      properties:
        orderId:
          type: string
        userId:
          type: string
        timestamp:
          type: string
          format: date-time
    OrderUpdatedEvent:
      type: object
      properties:
        orderId:
          type: string
        changes:
          type: object
    OrderShippedEvent:
      type: object
      properties:
        orderId:
          type: string
        trackingNumber:
          type: string
""",
        },
        must_include=["asyncapi.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_022_json_schema_ref",
        initial_files={
            "schemas/user.json": """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"}
    }
}
""",
            "schemas/order.json": """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "user": {"$ref": "user.json"}
    }
}
""",
        },
        changed_files={
            "schemas/user.json": """{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://example.com/schemas/user.json",
    "type": "object",
    "required": ["id", "name", "email"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "address": {"$ref": "address.json"}
    }
}
""",
        },
        must_include=["user.json"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_023_swagger_security",
        initial_files={
            "swagger.yaml": """swagger: "2.0"
info:
  title: API
  version: 1.0.0
securityDefinitions:
  apiKey:
    type: apiKey
    in: header
    name: X-API-Key
paths:
  /users:
    get:
      security:
        - apiKey: []
      responses:
        200:
          description: Success
""",
            "src/middleware/auth.py": """def require_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return {'error': 'API key required'}, 401
        return func(*args, **kwargs)
    return wrapper
""",
        },
        changed_files={
            "swagger.yaml": """swagger: "2.0"
info:
  title: API
  version: 1.0.0
securityDefinitions:
  apiKey:
    type: apiKey
    in: header
    name: X-API-Key
  oauth2:
    type: oauth2
    flow: accessCode
    authorizationUrl: https://auth.example.com/authorize
    tokenUrl: https://auth.example.com/token
    scopes:
      read:users: Read user data
      write:users: Modify user data
  bearerAuth:
    type: apiKey
    in: header
    name: Authorization
paths:
  /users:
    get:
      security:
        - apiKey: []
        - oauth2: [read:users]
      responses:
        200:
          description: Success
        401:
          description: Unauthorized
""",
        },
        must_include=["swagger.yaml"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_024_grpc_stream",
        initial_files={
            "proto/stream.proto": """syntax = "proto3";

package stream;

service DataService {
    rpc GetData(GetDataRequest) returns (DataResponse);
}

message GetDataRequest {
    string id = 1;
}

message DataResponse {
    bytes data = 1;
}
""",
            "src/grpc/stream_service.py": """class DataServiceServicer:
    def GetData(self, request, context):
        data = get_data(request.id)
        return DataResponse(data=data)
""",
        },
        changed_files={
            "proto/stream.proto": """syntax = "proto3";

package stream;

service DataService {
    rpc GetData(GetDataRequest) returns (DataResponse);
    rpc StreamData(GetDataRequest) returns (stream DataChunk);
    rpc UploadData(stream DataChunk) returns (UploadResponse);
    rpc BiDirectionalStream(stream DataChunk) returns (stream DataChunk);
}

message GetDataRequest {
    string id = 1;
}

message DataResponse {
    bytes data = 1;
}

message DataChunk {
    bytes content = 1;
    int64 offset = 2;
    bool is_last = 3;
}

message UploadResponse {
    string id = 1;
    int64 total_bytes = 2;
    bool success = 3;
}
""",
        },
        must_include=["stream.proto"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]

SQL_CASES = [
    DiffTestCase(
        name="docs_025_sql_migration_adds_column",
        initial_files={
            "migrations/001_create_users.sql": """CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);
""",
            "src/models/user.py": """from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
""",
        },
        changed_files={
            "migrations/002_add_user_status.sql": """ALTER TABLE users
ADD COLUMN status VARCHAR(50) DEFAULT 'active';

CREATE INDEX idx_users_status ON users(status);
""",
        },
        must_include=["002_add_user_status.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_026_sql_migration_adds_table",
        initial_files={
            "migrations/001_create_orders.sql": """CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10, 2)
);
""",
        },
        changed_files={
            "migrations/002_create_order_items.sql": """CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
""",
            "src/models/order_item.py": """from dataclasses import dataclass
from decimal import Decimal

@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    quantity: int
    price: Decimal
""",
        },
        must_include=["002_create_order_items.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_027_sql_migration_adds_index",
        initial_files={
            "migrations/001_create_products.sql": """CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2)
);
""",
            "src/repository/product_repository.py": """class ProductRepository:
    def find_by_category(self, category: str):
        return self.db.query(
            "SELECT * FROM products WHERE category = %s", [category]
        )
""",
        },
        changed_files={
            "migrations/002_add_product_indexes.sql": """CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_name_search ON products USING gin(to_tsvector('english', name));
""",
        },
        must_include=["002_add_product_indexes.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_028_sql_migration_adds_fk",
        initial_files={
            "migrations/001_create_tables.sql": """CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INTEGER
);
""",
        },
        changed_files={
            "migrations/002_add_category_fk.sql": """ALTER TABLE products
ADD CONSTRAINT fk_products_category
FOREIGN KEY (category_id) REFERENCES categories(id)
ON DELETE SET NULL;
""",
        },
        must_include=["002_add_category_fk.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_029_sql_stored_procedure",
        initial_files={
            "sql/procedures/calculate_order_total.sql": """CREATE OR REPLACE FUNCTION calculate_order_total(order_id INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    total DECIMAL;
BEGIN
    SELECT SUM(quantity * price) INTO total
    FROM order_items
    WHERE order_items.order_id = calculate_order_total.order_id;

    RETURN COALESCE(total, 0);
END;
$$ LANGUAGE plpgsql;
""",
            "src/services/order_service.py": """class OrderService:
    def get_order_total(self, order_id: int) -> float:
        result = self.db.execute(
            "SELECT calculate_order_total(%s)", [order_id]
        )
        return float(result[0][0])
""",
        },
        changed_files={
            "sql/procedures/calculate_order_total.sql": """CREATE OR REPLACE FUNCTION calculate_order_total(
    order_id INTEGER,
    include_tax BOOLEAN DEFAULT FALSE
)
RETURNS DECIMAL AS $$
DECLARE
    subtotal DECIMAL;
    tax_rate DECIMAL := 0.1;
BEGIN
    SELECT SUM(quantity * price) INTO subtotal
    FROM order_items
    WHERE order_items.order_id = calculate_order_total.order_id;

    subtotal := COALESCE(subtotal, 0);

    IF include_tax THEN
        RETURN subtotal * (1 + tax_rate);
    END IF;

    RETURN subtotal;
END;
$$ LANGUAGE plpgsql;
""",
        },
        must_include=["calculate_order_total.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_030_sql_view_definition",
        initial_files={
            "sql/views/user_orders_view.sql": """CREATE OR REPLACE VIEW user_orders_summary AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;
""",
            "src/reports/user_report.py": """class UserReport:
    def get_summary(self, user_id: int):
        return self.db.query(
            "SELECT * FROM user_orders_summary WHERE user_id = %s",
            [user_id]
        )
""",
        },
        changed_files={
            "sql/views/user_orders_view.sql": """CREATE OR REPLACE VIEW user_orders_summary AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    u.email AS user_email,
    COUNT(o.id) AS order_count,
    SUM(o.total) AS total_spent,
    AVG(o.total) AS avg_order_value,
    MAX(o.created_at) AS last_order_date
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name, u.email;
""",
        },
        must_include=["user_orders_view.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_031_sql_trigger",
        initial_files={
            "sql/triggers/audit_trigger.sql": """CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, operation, old_data, new_data, created_at)
    VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
""",
            "src/services/user_service.py": """class UserService:
    def update_user(self, user_id: int, name: str):
        self.db.execute(
            "UPDATE users SET name = %s WHERE id = %s",
            [name, user_id]
        )
""",
        },
        changed_files={
            "sql/triggers/audit_trigger.sql": """CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        operation,
        old_data,
        new_data,
        user_id,
        ip_address,
        created_at
    )
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        row_to_json(OLD),
        row_to_json(NEW),
        current_setting('app.current_user_id', TRUE)::INTEGER,
        current_setting('app.client_ip', TRUE),
        NOW()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_audit
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER orders_audit
AFTER INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
""",
        },
        must_include=["audit_trigger.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_032_sql_create_type_enum",
        initial_files={
            "sql/types/order_status.sql": """CREATE TYPE order_status AS ENUM (
    'pending',
    'confirmed',
    'shipped',
    'delivered'
);
""",
            "src/models/order.py": """from enum import Enum

class OrderStatus(Enum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
""",
        },
        changed_files={
            "sql/types/order_status.sql": """-- Note: In PostgreSQL, you need to add values to existing enum
ALTER TYPE order_status ADD VALUE 'processing' AFTER 'pending';
ALTER TYPE order_status ADD VALUE 'cancelled' AFTER 'delivered';
ALTER TYPE order_status ADD VALUE 'refunded' AFTER 'cancelled';
""",
        },
        must_include=["order_status.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_033_sql_schema_change_queries",
        initial_files={
            "sql/queries/get_user_orders.sql": """SELECT
    o.id,
    o.total,
    o.created_at
FROM orders o
WHERE o.user_id = :user_id
ORDER BY o.created_at DESC;
""",
        },
        changed_files={
            "sql/queries/get_user_orders.sql": """SELECT
    o.id,
    o.total,
    o.status,
    o.created_at,
    o.updated_at
FROM orders o
WHERE o.user_id = :user_id
  AND o.status != 'cancelled'
ORDER BY o.created_at DESC
LIMIT :limit OFFSET :offset;
""",
        },
        must_include=["get_user_orders.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_034_sql_insert_into_table",
        initial_files={
            "sql/seed/initial_data.sql": """INSERT INTO categories (name) VALUES
    ('Electronics'),
    ('Clothing'),
    ('Books');
""",
            "src/models/category.py": """from dataclasses import dataclass

@dataclass
class Category:
    id: int
    name: str
""",
        },
        changed_files={
            "sql/seed/initial_data.sql": """INSERT INTO categories (name, description, active) VALUES
    ('Electronics', 'Electronic devices and accessories', TRUE),
    ('Clothing', 'Apparel and fashion items', TRUE),
    ('Books', 'Physical and digital books', TRUE),
    ('Home & Garden', 'Home improvement and garden supplies', TRUE),
    ('Sports', 'Sports equipment and gear', TRUE);
""",
        },
        must_include=["initial_data.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_035_sql_join_tables",
        initial_files={
            "sql/queries/order_details.sql": """SELECT
    o.id AS order_id,
    u.name AS customer_name,
    p.name AS product_name,
    oi.quantity,
    oi.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.id = :order_id;
""",
        },
        changed_files={
            "sql/queries/order_details.sql": """SELECT
    o.id AS order_id,
    o.status,
    u.name AS customer_name,
    u.email AS customer_email,
    p.name AS product_name,
    c.name AS category_name,
    oi.quantity,
    oi.price,
    (oi.quantity * oi.price) AS line_total
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
LEFT JOIN categories c ON p.category_id = c.id
WHERE o.id = :order_id;
""",
        },
        must_include=["order_details.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_036_sql_subquery",
        initial_files={
            "sql/queries/top_customers.sql": """SELECT
    u.id,
    u.name,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count
FROM users u
ORDER BY order_count DESC
LIMIT 10;
""",
        },
        changed_files={
            "sql/queries/top_customers.sql": """SELECT
    u.id,
    u.name,
    u.email,
    (SELECT COUNT(*) FROM orders WHERE user_id = u.id) AS order_count,
    (SELECT COALESCE(SUM(total), 0) FROM orders WHERE user_id = u.id) AS total_spent,
    (
        SELECT MAX(created_at)
        FROM orders
        WHERE user_id = u.id
    ) AS last_order_date
FROM users u
WHERE EXISTS (SELECT 1 FROM orders WHERE user_id = u.id)
ORDER BY total_spent DESC
LIMIT 10;
""",
        },
        must_include=["top_customers.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_037_sql_cte",
        initial_files={
            "sql/queries/monthly_sales.sql": """WITH monthly_totals AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(total) AS revenue
    FROM orders
    GROUP BY DATE_TRUNC('month', created_at)
)
SELECT * FROM monthly_totals ORDER BY month;
""",
        },
        changed_files={
            "sql/queries/monthly_sales.sql": """WITH monthly_totals AS (
    SELECT
        DATE_TRUNC('month', created_at) AS month,
        SUM(total) AS revenue,
        COUNT(*) AS order_count
    FROM orders
    WHERE status != 'cancelled'
    GROUP BY DATE_TRUNC('month', created_at)
),
monthly_growth AS (
    SELECT
        month,
        revenue,
        order_count,
        LAG(revenue) OVER (ORDER BY month) AS prev_revenue,
        ROUND(
            (revenue - LAG(revenue) OVER (ORDER BY month)) /
            NULLIF(LAG(revenue) OVER (ORDER BY month), 0) * 100,
            2
        ) AS growth_percent
    FROM monthly_totals
)
SELECT * FROM monthly_growth ORDER BY month DESC;
""",
        },
        must_include=["monthly_sales.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_038_sql_create_function",
        initial_files={
            "sql/functions/format_currency.sql": """CREATE OR REPLACE FUNCTION format_currency(amount DECIMAL)
RETURNS TEXT AS $$
BEGIN
    RETURN '$' || TO_CHAR(amount, 'FM999,999,990.00');
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""",
            "sql/queries/order_report.sql": """SELECT
    id,
    format_currency(total) AS formatted_total
FROM orders;
""",
        },
        changed_files={
            "sql/functions/format_currency.sql": """CREATE OR REPLACE FUNCTION format_currency(
    amount DECIMAL,
    currency_code TEXT DEFAULT 'USD'
)
RETURNS TEXT AS $$
DECLARE
    symbol TEXT;
BEGIN
    symbol := CASE currency_code
        WHEN 'USD' THEN '$'
        WHEN 'EUR' THEN '€'
        WHEN 'GBP' THEN '£'
        ELSE currency_code || ' '
    END;
    RETURN symbol || TO_CHAR(amount, 'FM999,999,990.00');
END;
$$ LANGUAGE plpgsql IMMUTABLE;
""",
        },
        must_include=["format_currency.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
    DiffTestCase(
        name="docs_039_sql_materialized_view",
        initial_files={
            "sql/views/sales_summary_mv.sql": """CREATE MATERIALIZED VIEW sales_summary AS
SELECT
    DATE_TRUNC('day', o.created_at) AS day,
    COUNT(*) AS order_count,
    SUM(o.total) AS revenue
FROM orders o
GROUP BY DATE_TRUNC('day', o.created_at)
WITH DATA;

CREATE UNIQUE INDEX idx_sales_summary_day ON sales_summary(day);
""",
            "sql/jobs/refresh_views.sql": """REFRESH MATERIALIZED VIEW CONCURRENTLY sales_summary;
""",
        },
        changed_files={
            "sql/views/sales_summary_mv.sql": """CREATE MATERIALIZED VIEW sales_summary AS
SELECT
    DATE_TRUNC('day', o.created_at) AS day,
    COUNT(*) AS order_count,
    SUM(o.total) AS revenue,
    AVG(o.total) AS avg_order_value,
    COUNT(DISTINCT o.user_id) AS unique_customers,
    SUM(CASE WHEN o.status = 'refunded' THEN o.total ELSE 0 END) AS refunded_amount
FROM orders o
WHERE o.status != 'cancelled'
GROUP BY DATE_TRUNC('day', o.created_at)
WITH DATA;

CREATE UNIQUE INDEX idx_sales_summary_day ON sales_summary(day);
CREATE INDEX idx_sales_summary_revenue ON sales_summary(revenue);
""",
        },
        must_include=["sales_summary_mv.sql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
    ),
]

ALL_CICD_CASES = GITHUB_ACTIONS_CASES + GITLAB_CI_CASES + DOCUMENTATION_CASES + API_SPECS_CASES + SQL_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_CICD_CASES, ids=lambda c: c.name)
def test_cicd_docs_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
