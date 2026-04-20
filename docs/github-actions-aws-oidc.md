# GitHub Actions: AWS access with OIDC

This repository’s deploy workflow assumes AWS credentials via **OpenID Connect (OIDC)**. GitHub issues short-lived tokens; AWS validates them and returns **temporary** credentials for an IAM role. You do **not** store long-lived `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in GitHub.

## What you configure

1. An **IAM OIDC identity provider** for GitHub in your AWS account (once per account, unless it already exists).
2. An **IAM role** that trusts that provider and is limited to the repositories and refs you choose.
3. **Permissions** on that role sufficient for Serverless deploy, S3 upload, and CloudFront invalidation (see below).
4. GitHub repository secret **`AWS_ROLE_TO_ASSUME`** set to that role’s ARN.

The workflow uses [`aws-actions/configure-aws-credentials`](https://github.com/aws-actions/configure-aws-credentials) with `role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}` and `id-token: write` in job permissions.

## 1. OIDC identity provider (IAM)

In the AWS console: **IAM → Identity providers → Add provider**.

- **Provider type:** OpenID Connect  
- **Provider URL:** `https://token.actions.githubusercontent.com`  
- **Audience:** `sts.amazonaws.com`  

Alternatively, with AWS CLI (replace nothing; these values are fixed for GitHub):

```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

If the provider already exists in the account, reuse it; you cannot create a duplicate.

## 2. Trust policy on the IAM role

Create an IAM role with **Custom trust policy**. Replace:

- `ACCOUNT_ID` — your 12-digit AWS account id  
- `ORG` / `REPO` — GitHub organization or user name, and repository name  

**Restrict to one repository (any branch or tag):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:*"
        }
      }
    }
  ]
}
```

**Restrict to the `main` branch only** (typical for deploy workflows):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:ORG/REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

For **`workflow_dispatch`**, subjects can include environment-specific claims; if deploys from manual runs fail with access denied, widen the `sub` condition carefully (for example allow `repo:ORG/REPO:*` only on a dedicated deploy role) or add a second statement for the needed ref pattern. See GitHub’s documentation on [OIDC claims](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#understanding-the-oidc-token).

## 3. Permissions the role needs

The deploy job in this template:

- Runs **Serverless Framework** in `backend/` (CloudFormation, Lambda, API Gateway HTTP API, IAM for execution roles, CloudWatch Logs, S3 buckets created by the stack, etc.).
- Runs **`scripts/deploy-frontend.sh`**: reads CloudFormation outputs, **`aws s3 sync`** to the frontend bucket, **`aws cloudfront create-invalidation`**.

Exact least-privilege policies depend on your naming conventions and optional resource boundaries. Practical approaches:

1. **Start with a broad policy** on a non-production account, run a full deploy, then tighten using CloudTrail and IAM Access Analyzer.  
2. **Attach managed policies** only in sandboxes; for production, prefer a custom policy scoped to the stack name prefix (from `service` in `backend/serverless.yml`) and the created S3/CloudFront resources.

At minimum, the role must allow:

- **CloudFormation** — create/update/describe/delete stacks and change sets for your stack(s).  
- **Lambda**, **API Gateway v2**, **IAM** (create roles/policies the Serverless template attaches to the function; often includes `iam:PassRole` for the Lambda execution role).  
- **S3** — bucket and object operations for the Serverless-managed buckets and `s3 sync` targets.  
- **CloudFront** — `CreateInvalidation` (and read distribution metadata if your scripts list distributions).  
- **CloudWatch Logs** — log groups for Lambda.  
- **ACM** — if Serverless or CloudFront integration reads certificate metadata in your region; CloudFront custom certs are in **us-east-1**.  
- **STS** — `GetCallerIdentity` is commonly used by tooling.

If you use **organization SCPs** or **permission boundaries**, ensure they allow these calls for the role.

## 4. GitHub configuration

1. Copy the **role ARN** (for example `arn:aws:iam::ACCOUNT_ID:role/MyGitHubDeployRole`).  
2. In the GitHub repo: **Settings → Secrets and variables → Actions**.  
3. Create a **repository secret** named **`AWS_ROLE_TO_ASSUME`** with that ARN.  

Optional: set **`AWS_REGION`** under **Variables** if you do not want the workflow default (`eu-central-1`).

The deploy workflow already includes:

```yaml
permissions:
  id-token: write
  contents: read
```

`id-token: write` is required so GitHub can mint the OIDC JWT.

## 5. Verify

- Open **Actions**, run the deploy workflow (push to `main` or **Run workflow**).  
- If assumption fails, check CloudTrail **AssumeRoleWithWebIdentity** errors and compare the token **`sub`** claim to your trust policy `StringEquals` / `StringLike` conditions.  
- If deployment fails after a successful assumption, the role lacks permissions for the failing API; add the missing action/resource and redeploy.

## Security notes

- Prefer **narrow `sub` conditions** (one repo, one branch) on production roles.  
- Use **separate AWS accounts** or roles for production and development when possible.  
- Rotate and review role policies regularly; OIDC avoids static keys but the role’s permissions are still critical.

For AWS’s overview, see [IAM OIDC identity providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html) and GitHub’s [Configuring OpenID Connect in Amazon Web Services](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services).
