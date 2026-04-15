pipeline {
    agent any

    environment {
        // Replace 'mihirbindal' with your actual Docker Hub username if different
        DOCKER_HUB_USER = 'mihirbindal'
        
        // These are the names of the images we will create
        IMAGE_INGEST = "${DOCKER_HUB_USER}/spe-ingest"
        IMAGE_GENERATE = "${DOCKER_HUB_USER}/spe-generate"
        IMAGE_FRONTEND = "${DOCKER_HUB_USER}/spe-frontend"
        
        // This will tag the images with the Jenkins Build Number (e.g., v1, v2, v3)
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

        stage('Push to Docker Hub') {
            steps {
                // IMPORTANT: You must have a Jenkins credential saved named 'docker-hub-credentials'
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
    }

    post {
        always {
            echo "Cleaning up local Docker images to save space..."
            sh "docker image prune -f"
        }
        success {
            echo "✅ Pipeline completed successfully! Images are live on Docker Hub."
        }
        failure {
            echo "❌ Pipeline failed. Check the logs."
        }
    }
}