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
1. Create your S3 bucket first (e.g., `your-name-crypto-news`)
2. Replace `YOUR_STUDENT_BUCKET_NAME` in this policy with your actual bucket name
3. Attach the updated policy to your IAM user

### 2. `bedrock-models-policy.json`
**Bedrock-specific permissions** - if you want to separate Bedrock access.

**Permissions:**
- Invoke Claude 3 Haiku model
- Invoke Titan Embeddings model
- List available foundation models

## Setup Instructions

### Step 1: Create S3 Bucket First
1. Go to S3 Console
2. Create bucket with your name (e.g., `john-doe-crypto-news`)
3. Ensure bucket is in `us-east-1` region
4. **Note the exact bucket name** - you'll need it for the next step

### Step 2: Update IAM Policy
1. Open `s3-bedrock-policy.json`
2. Replace `YOUR_STUDENT_BUCKET_NAME` with your actual bucket name
3. Save the file

### Step 3: Create IAM User
1. Go to AWS IAM Console
2. Create new user with programmatic access
3. Attach the updated `s3-bedrock-policy.json` policy
4. Generate Access Key ID and Secret Access Key

### Step 4: Configure Environment
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
