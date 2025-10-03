# Terraform Configuration for Crypto Agent

This Terraform configuration creates a complete infrastructure from scratch for your crypto sentiment agent.

## 🎯 What This Creates

- **EC2 Instance**: t3.medium with Ubuntu 22.04 LTS
- **Security Group**: Properly configured with CloudFront-only access
- **ECR Repository**: For storing Docker images
- **CloudFront Distribution**: For secure web access
- **Complete Setup**: Instance pre-configured with Docker and dependencies

## 📋 Prerequisites

1. **AWS CLI configured** with your credentials
2. **Terraform installed** (version 1.0+)
3. **AWS Account** with appropriate permissions

## 🚀 Quick Start

### 1. Configure Terraform
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars if needed (optional)
```

### 2. Deploy Infrastructure
```bash
terraform init
terraform plan    # Review what will be created
terraform apply   # Create everything (type 'yes' when prompted)
```

### 3. Get Connection Info
```bash
terraform output
```

## 🔧 Configuration Options

### terraform.tfvars
```hcl
# AWS region
aws_region = "us-east-1"

# EC2 Key Pair (optional - leave empty if you don't have one)
key_pair_name = ""

# Additional IPs for SSH access (for traveling)
additional_ssh_ips = [
  "YOUR_HOME_IP/32",
  "YOUR_OFFICE_IP/32"
]
```

## 🏗️ Infrastructure Details

### Security Group Rules
- **SSH (22)**: Your current IP + additional IPs
- **HTTP (80)**: CloudFront IPs only
- **HTTPS (443)**: CloudFront IPs only
- **API (8000)**: CloudFront IPs only
- **PostgreSQL (5432)**: Localhost only

### EC2 Instance
- **Type**: t3.medium (2 vCPU, 4GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 20GB GP3 (encrypted)
- **Pre-installed**: Docker, Docker Compose, AWS CLI, Git

### CloudFront Distribution
- **Origin**: Your EC2 instance
- **SSL**: Automatic HTTPS redirect
- **Caching**: Optimized for API responses

## 📱 After Deployment

### 1. SSH into Your Instance
```bash
# Get the public IP from terraform output
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP
```

### 2. Copy Your Application
```bash
# On your local machine
scp -r -i your-key.pem . ubuntu@YOUR_INSTANCE_IP:/opt/crypto-agent/
```

### 3. Update Environment Variables
```bash
# On the instance
cd /opt/crypto-agent
nano .env
# Update with your actual AWS credentials, API keys, etc.
```

### 4. Start Your Application
```bash
# On the instance
docker-compose up -d
```

## 🔄 Managing Your Infrastructure

### Adding More SSH IPs
```bash
# Edit terraform.tfvars
# Add new IPs to additional_ssh_ips list
terraform apply
```

### Updating Your Current IP
```bash
# Terraform automatically detects your current IP
terraform apply
```

### Scaling Up
```bash
# Edit main.tf to change instance_type
# terraform apply
```

## 🧹 Cleanup

To destroy everything:
```bash
terraform destroy  # Type 'yes' when prompted
```

## 🆘 Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure your AWS credentials have EC2, ECR, and CloudFront permissions
2. **Key Pair Not Found**: Either create a key pair in AWS Console or leave `key_pair_name` empty
3. **CloudFront Slow**: CloudFront distributions can take 15-20 minutes to fully deploy

### Getting Help
```bash
# Check Terraform state
terraform show

# Check AWS resources
aws ec2 describe-instances
aws ec2 describe-security-groups
```

## 💰 Cost Estimation

- **EC2 t3.medium**: ~$30-35/month
- **CloudFront**: ~$1-2/month (depending on traffic)
- **ECR**: ~$0.10/month (for image storage)
- **Total**: ~$35-40/month
