# 通过 SageMaker 与 Step Functions 实现MLOps方案
在传统的机器学习工作流程当中，经常会面临两个问题：
（1）数据迭代迅速，需要定期对模型进行重新训练，每次训练完成后，都需要重新部署模型，如何实现训练与部署过程的的自动化，从而提升工作效率；
（2）算法团队不断地对算法进行开发与变更，并且需要尝试不同的特征工程，每次变更都需要做单元测试，如何将SageMaker与CI/CD工具整合，在提升开发效率的同时减少运维团队的工作负担。

本文会介绍通过SageMaker与Step Functions进行模型自动训练与部署的方法，并会与CodeCommit、CodeBuild、CodePipeline集成，实现机器学习MLOps方案。

### 流程架构图与过程简介

（1）配置CodePipeline来集成CodeCommit、CodeBuild；

（2）开发人员push代码到CodeCommit后触发CodePipeline，代码在CodeBuild中封装成docker image，并推送到ECR当中（注：在本实验中，为了方便在CI/CD过程中对代码版本进行控制，会通过BYOC的方式在SageMaker中使用自定义算法，该方式需要自己编写Dockerfile并将算法build为docker image，然后上传到ECR当中

（3）触发Step Functions执行SageMaker训练与部署的步骤；

（4）SageMaker从ECR中加载docker image与S3中的数据进行训练；

（5）训练完成后对模型进行部署，暴露供推理使用的endpoint。

### 实现过程
1、在Step Functions中定义使用SageMaker训练与部署模型的步骤
（1）在SageMaker中创建一台笔记本实例，输入名称并保持其他默认配置，待创建完成后打开JupterLab，在初始界面下拉找到Terminal，点击进入执行cd SageMaker命令；
![create-notebook](/pics/create-notebook.jpg)

（2）打开IAM console，找到SageMaker自动创建的新角色，添加AdministratorAccess权限；
（3）在Terminal中执行命令：
![open-teeminal](/pics/open-teminal.png)
```
git clone https://github.com/comdaze/sagemaker-mlops.git
```
（4）进入下载好的文件夹，执行unzip package.zip命令进行解压，待解压完成后在Jupyter notebook左侧的工作目录中打开sfn_deploy_byoc.ipynb文件；

（5）按照该notebook中的步骤执行一遍即可；

（6）执行完成后，打开Step Functions控制台，会看到多出一个状态机;

（7）选中该状态机，点击定义，可以看到如下所示的工作流，其中定义了SageMaker从训练到部署所需的步骤：
![step-function-workflow](/pics/step-functions-workflow.png)


2、创建CodeCommit与CodeBuild
（1）打开CodeCommit控制台，点击创建存储库；
![create-codecommit-repo](/pics/create-codecommit-repo.png)
 
（2）输入存储库名称并点击创建；
![create-codecommit-repo-step1](/pics/create-codecommit-repo-step1.png)
 
（3）回到CodeCommit控制台，选择第二步中创建好的存储库，克隆HTTPS URL，
![create-codecommit-repo-step2](/pics/create-codemmit-repo-step2.png)
在Notebook Terminal执行git clone；
```
cd /home/ec2-user/Sagemaker
git clone https://git-codecommit.cn-northwest-1.amazonaws.com.cn/v1/repos/ml-ops-codecommit
cp -r sagemaker-mlops/* ml-ops-codecommit
cd ml-ops-codecommit
git add .
git commit -m 'update'
git push
```
push成功之后，回到CodeCommit控制台，打开存储库，发现代码已经上传完成；

 在cifar10文件夹中包含了使用tensorflow对cifar-10数据集进行训练与创建tersorflow serving的代码，会通过Dockerfile文件与build_and_push.sh打包封装成docker image并上传到ECR当中，上传完成后会执行invoke_sfn.py脚本，运行已经定义好的Step Functions状态机，从而完成SageMaker训练与部署的过程。

（4）打开CodeBuild控制台，按照下述信息创建项目；
![create-codebuild-step1](/pics/create-codebuild-step1.png)

构建项目名称
![create-codebuild-step2](/pics/create-codebuild-step2.png)

选择源
![create-codebuild-step3](/pics/create-codebuild-step3.png)

构建运行环境
![create-codebuild-step4](/pics/create-codebuild-step4.png)

修改Buildspec文件
![create-codebuild-step5](/pics/create-codebuild-step5.png)

日志设置
![codebuild-logs](/pics/codebuild-logs.png)

Buildspec中定义的代码即为在构建编译过程中所需要执行的命令，可以把该过程理解为：
1）下载执行脚本所需的依赖包boto3；
2）执行build_and_push.sh脚本将算法封装成docker image并上传到ECR；
3）执行invoke_sfn.py脚本，触发Step Functions状态机进行模型的训练与部署。在build commands下复制粘贴以下代码：
```
- pip install boto3
- chmod 777 build_and_push.sh
- ./build_and_push.sh sagemaker-tf-cifar10-example
- python invoke_sfn.py
``` 
 
其他配置保持默认即可，点击创建构建项目。
（5）打开iam role的控制台，赋予codebuild-ml-ops-service-role角色AmazonEC2ContainerRegistryFullAccess与AWSStepFunctionsFullAccess的权限；
![add-policy](/pics/add-policy.png)

3、 采用CodePipeline将CodeCommit、CodeBuild集成
（1）创建CodePipeline流水线；
![create-codepipeline](/pics/create-codepipeline.png)
 (2)流水线设置；
![create-codepipeline-step1](/pics/create-codepipeline-step1.png)
（3）添加源阶段
![create-codepipeline-step2](/pics/create-codepipeline-step2.png)
（4）添加构建阶段
![create-codepipeline-step3](/pics/create-codepipeline-step3.png)
（5）跳过部署阶段
![create-codepipeline-step4](/pics/create-codepipeline-step4.png)
（6）最后创建完成流水线可以看到第一次执行
![run-codepipeline](/pics/run-codepipeline.png)