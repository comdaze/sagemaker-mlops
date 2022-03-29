pipeline {
    agent any
    stages {
        stage('build') {
            steps {
                awsCodeBuild projectName: 'your_project_name', credentialsType: 'keys', region: 'us-east-1', sourceControlType: 'project'
                echo 'Done................'
            }
        }
    }
}

