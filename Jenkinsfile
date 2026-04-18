pipeline {
    agent any

    environment {
        DOCKER_HUB_USER = 'mihirbindal'
        
        IMAGE_INGEST = "${DOCKER_HUB_USER}/spe-ingest"
        IMAGE_GENERATE = "${DOCKER_HUB_USER}/spe-generate"
        IMAGE_FRONTEND = "${DOCKER_HUB_USER}/spe-frontend"

        IMAGE_TAG = "v${env.BUILD_ID}"
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Fetching the latest code from GitHub..."
                checkout scm
            }
        }

        stage('Build Docker Images') {
            steps {
                echo "Building Ingest Service..."
                sh "docker build -t ${IMAGE_INGEST}:latest -t ${IMAGE_INGEST}:${IMAGE_TAG} ./ingest"
                
                echo "Building Generate Service..."
                sh "docker build -t ${IMAGE_GENERATE}:latest -t ${IMAGE_GENERATE}:${IMAGE_TAG} ./generate"
                
                echo "Building Frontend Service..."
                sh "docker build -t ${IMAGE_FRONTEND}:latest -t ${IMAGE_FRONTEND}:${IMAGE_TAG} ./frontend"
            }
        }

        stage('Run Automated Tests') {
            steps {
                echo "Installing test dependencies..."
                sh "pip3 install -r requirements.txt --break-system-packages || pip3 install -r requirements.txt"
                
                echo "Executing Pytest (Positive & Negative Tests)..."
                sh "export PYTHONPATH=\$PYTHONPATH:. && pytest tests/test_api.py"
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhubcredentials', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    echo "Logging into Docker Hub..."
                    sh "echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin"
                    
                    echo "Pushing Ingest Image..."
                    sh "docker push ${IMAGE_INGEST}:latest"
                    sh "docker push ${IMAGE_INGEST}:${IMAGE_TAG}"
                    
                    echo "Pushing Generate Image..."
                    sh "docker push ${IMAGE_GENERATE}:latest"
                    sh "docker push ${IMAGE_GENERATE}:${IMAGE_TAG}"
                    
                    echo "Pushing Frontend Image..."
                    sh "docker push ${IMAGE_FRONTEND}:latest"
                    sh "docker push ${IMAGE_FRONTEND}:${IMAGE_TAG}"
                }
            }
        }
        stage('Deploy to Production (Ansible)') {
            steps {
                echo "Triggering Ansible Playbook for deployment..."
                dir('devops/ansible') {
                    sh "pip3 install kubernetes --break-system-packages || pip3 install kubernetes"
                    sh "KUBECONFIG=/home/mihir/.kube/config ansible-playbook deploy.yml"
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up local Docker images to save space..."
            sh "docker image prune -f"
        }
        success {
            echo "Pipeline completed successfully! Images are live on Docker Hub."
        }
        failure {
            echo "Pipeline failed. Check the logs."
        }
    }
}