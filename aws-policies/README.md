# AWS IAM Policies for Crypto Sentiment Agent

This folder contains the IAM policies required for the crypto sentiment agent to access AWS services.

## Required Policies

### 1. `s3-bedrock-policy.json`
**Main policy for the bootcamp** - includes both S3 and Bedrock permissions.

**Permissions:**
- Read access to instructor's S3 bucket (`crypto-news-pdfs-sep-2025`)
- Full access to your student S3 bucket
- Invoke Bedrock models (Claude Haiku and Titan Embeddings)

**Usage:**
1. Replace `YOUR_STUDENT_BUCKET_NAME` with your actual bucket name
2. Attach this policy to your IAM user

### 2. `bedrock-models-policy.json`
**Bedrock-specific permissions** - if you want to separate Bedrock access.

**Permissions:**
- Invoke Claude 3 Haiku model
- Invoke Titan Embeddings model
- List available foundation models

## Setup Instructions

### Step 1: Create IAM User
1. Go to AWS IAM Console
2. Create new user with programmatic access
3. Attach the `s3-bedrock-policy.json` policy
4. Generate Access Key ID and Secret Access Key

### Step 2: Create S3 Bucket
1. Go to S3 Console
2. Create bucket with your name (e.g., `your-name-crypto-news`)
3. Update the policy with your bucket name
4. Ensure bucket is in `us-east-1` region

### Step 3: Configure Environment
1. Copy `env.example` to `.env`
2. Add your AWS credentials
3. Set your S3 bucket name
4. Add CoinGecko API key

## Security Notes

- **Least Privilege**: These policies only grant necessary permissions
- **Cost Control**: Bedrock usage is pay-per-use, monitor your costs
- **Region**: All resources are in `us-east-1` for consistency
- **Bucket Access**: Student buckets are private by default

## Troubleshooting

### Common Issues:
1. **Access Denied**: Check IAM policy is attached correctly
2. **Bucket Not Found**: Verify bucket name and region
3. **Bedrock Not Available**: Ensure Bedrock is enabled in your region
4. **Rate Limits**: CoinGecko free tier has rate limits

### Testing AWS Access:
```bash
# Test S3 access
aws s3 ls s3://crypto-news-pdfs-sep-2025/

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```
