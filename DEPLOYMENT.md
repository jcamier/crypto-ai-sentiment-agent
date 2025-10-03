# Deployment Guide

This guide covers how to deploy your crypto sentiment agent to AWS using either GitHub Actions or manual deployment.

## 🚀 Deployment Options

### Option 1: GitHub Actions (Recommended)
Automated deployment on every push to main branch.

### Option 2: Manual Deployment
Deploy manually using scripts when needed.

## 📋 Prerequisites

1. **ECR Repository**: `crypto-sentiment-agent` (already created)
2. **EC2 Instance**: t3.medium with Ubuntu 22.04 LTS (already created)
3. **AWS CLI**: Configured with appropriate permissions
4. **Docker**: Installed locally for manual deployment

## 🔧 GitHub Actions Setup

### 1. Create IAM Role for GitHub Actions

Create an IAM role with the following trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_USERNAME/YOUR_REPO:*"
        }
      }
    }
  ]
}
```

### 2. Attach Required Policies

Attach these policies to the role:
- `AmazonEC2ContainerRegistryFullAccess`
- `AmazonEC2FullAccess`
- `CloudFrontFullAccess`

### 3. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

```yaml
AWS_ROLE_ARN: arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActionsRole
EC2_HOST: your-ec2-public-ip
EC2_USER: ubuntu
EC2_SSH_KEY: your-private-ssh-key-content
CLOUDFRONT_DOMAIN: your-cloudfront-domain.cloudfront.net
```

### 4. Deploy

Push to main branch and GitHub Actions will automatically:
1. Run tests
2. Build Docker image
3. Push to ECR
4. Deploy to EC2
5. Run health checks

## 🛠️ Manual Deployment

### 1. Configure the Script

Edit `scripts/manual-deploy.sh`:

```bash
EC2_HOST="your-ec2-public-ip"
SSH_KEY_PATH="path/to/your/key.pem"
```

### 2. Run Deployment

```bash
chmod +x scripts/manual-deploy.sh
./scripts/manual-deploy.sh
```

## 📁 Deployment Files

### `.github/workflows/deploy.yml`
- GitHub Actions workflow
- Runs tests, builds image, deploys to EC2

### `scripts/deploy.sh`
- Deployment script that runs on EC2
- Pulls latest image, updates containers, runs health checks

### `scripts/manual-deploy.sh`
- Manual deployment script
- Builds locally, pushes to ECR, deploys to EC2

## 🔍 Troubleshooting

### Common Issues

1. **ECR Login Failed**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **SSH Connection Failed**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. **Docker Compose Failed**
   ```bash
   # Check logs
   docker-compose logs

   # Restart services
   docker-compose down && docker-compose up -d
   ```

4. **Health Check Failed**
   ```bash
   curl http://your-ec2-ip:8000/health
   ```

### Logs and Monitoring

```bash
# SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Check application logs
cd /opt/crypto-agent
docker-compose logs crypto-agent

# Check system resources
htop
df -h
```

## 🎯 Next Steps

After successful deployment:

1. **Update Environment Variables**: Edit `/opt/crypto-agent/.env` on EC2
2. **Configure CloudFront**: Point to your EC2 instance
3. **Set up Monitoring**: Add CloudWatch alarms
4. **Configure SSL**: Set up HTTPS with Let's Encrypt or AWS Certificate Manager

## 💰 Cost Optimization

- **Stop EC2 when not in use**: Use AWS Instance Scheduler
- **Use Spot Instances**: For development environments
- **Implement Auto Scaling**: For production workloads
- **Monitor ECR Storage**: Set up lifecycle policies
