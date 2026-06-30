// Jenkinsfile - Pipeline CI/CD Planning-Estiam
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'planning-estiam'
        REGISTRY = 'ghcr.io/wiscod'
        IMAGE_TAG = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
        SONARQUBE_TOKEN = credentials('sonar-token')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Branche : ${env.BRANCH_NAME}"
                echo "Commit  : ${env.GIT_COMMIT}"
                sh 'git log --oneline -5'
            }
        }
        
        stage('Lint') {
            steps {
                sh '''
                echo "pip install flake8 -q && flake8 src/ --max-line-length=100" > lint.sh
                docker run --rm \
                --volumes-from jenkins \
                -w $WORKSPACE \
                python:3.12-slim \
                sh lint.sh
                '''
            }
        }
        
        stage('Build & Test') {
            steps {
                sh '''
                docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .
                
                # Supprimer un éventuel conteneur test-runner résiduel
                docker rm -f test-runner 2>/dev/null || true
                
                set +e
                docker run \
                -e CI=true \
                --name test-runner \
                --entrypoint "" \
                ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
                pytest tests/ -v \
                --cov=src \
                --cov-report=xml:/tmp/coverage.xml \
                --cov-report=term-missing
                TEST_EXIT_CODE=$?
                set -e
                
                # Copier coverage.xml depuis le conteneur vers le workspace
                docker cp test-runner:/tmp/coverage.xml ./coverage.xml 2>/dev/null || true
                docker rm -f test-runner 2>/dev/null || true
                
                # Fix paths in coverage.xml for SonarQube
                sed -i "s|/app/src|src|g" ./coverage.xml || true
                sed -i "s|/app/|${WORKSPACE}/|g" ./coverage.xml || true
                
                exit $TEST_EXIT_CODE
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonarqube') {
                    sh '''
                    docker run --rm \
                    --network cicd-network \
                    --volumes-from jenkins \
                    -w "$WORKSPACE" \
                    -e SONAR_HOST_URL="$SONAR_HOST_URL" \
                    -e SONAR_TOKEN="$SONARQUBE_TOKEN" \
                    sonarsource/sonar-scanner-cli:latest \
                    sonar-scanner \
                    -Dsonar.projectKey=planning-estiam \
                    -Dsonar.projectName=Planning-Estiam \
                    -Dsonar.projectBaseDir="$WORKSPACE" \
                    -Dsonar.sources=src \
                    -Dsonar.python.version=3.12 \
                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                    -Dsonar.sourceEncoding=UTF-8 \
                    -Dsonar.scanner.metadataFilePath=$WORKSPACE/report-task.txt
                    '''
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh """
                docker run --rm \\
                -v /var/run/docker.sock:/var/run/docker.sock \\
                -v trivy-cache:/root/.cache/trivy \\
                --volumes-from jenkins \\
                aquasec/trivy:latest image \\
                --severity HIGH,CRITICAL \\
                --ignore-unfixed \\
                --ignorefile ${env.WORKSPACE}/.trivyignore \\
                --exit-code 1 \\
                --format table \\
                ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                """
            }
        }

        
        stage('Push') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                }
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'github-token',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    sh '''
                    echo $REGISTRY_PASS | docker login ghcr.io \\
                    -u $REGISTRY_USER --password-stdin
                    
                    docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
                    
                    docker tag ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:latest
                    docker push ${REGISTRY}/${IMAGE_NAME}:latest
                    '''
                }
            }
        }
        
        stage('IaC Apply') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                }
            }
            steps {
                sh """
                docker network create cicd-network 2>/dev/null || true
                docker stop planning-estiam-staging 2>/dev/null || true
                docker rm -f planning-estiam-staging 2>/dev/null || true

                docker run --rm \\
                    -v /var/run/docker.sock:/var/run/docker.sock \\
                    --volumes-from jenkins \\
                    -w ${env.WORKSPACE}/infra \\
                    -e TF_VAR_image_name="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \\
                    -e TF_VAR_ics_url="https://example.com/dummy.ics" \\
                    --entrypoint sh \\
                    hashicorp/terraform:latest \\
                    -c "terraform init -input=false && terraform apply -auto-approve && terraform output"

                echo "Staging provisionne via Terraform sur http://localhost:8001"
                """
            }
        }

        stage('Smoke Test') {
            when {
                anyOf {
                    branch 'main'
                    expression { env.GIT_BRANCH == 'origin/main' || env.GIT_BRANCH == 'main' }
                }
            }
            steps {
                sh '''
                echo "Attente du demarrage du conteneur staging..."
                sleep 5
                docker run --rm --network cicd-network curlimages/curl:latest -f http://planning-estiam-staging:8000/health
                echo "Smoke Test OK — /health repond 200"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker stop planning-estiam-staging 2>/dev/null || true; docker rm -f planning-estiam-staging 2>/dev/null || true'
        }
        success {
            echo "Pipeline réussi ! Image : ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo 'Pipeline échoué. Consultez les logs ci-dessus.'
        }
    }
}
