# quickstarts
This repo has all required quickstarts, namely: user-login, job-submission

## User-login

The login quickstarts provide tools for managing Kubernetes cluster authentication and access with OpenID connect.

### Scripts

#### `user-login-script.sh`
Comprehensive setup script for kubectl authentication to ML cluster using OIDC (OpenID Connect).

**Purpose**: Automates the complete process of configuring kubectl for cluster access with OIDC authentication.

**What it does**:
- Installs kubectl oidc-login plugin if not present (supports macOS/Linux and amd64/arm64 architectures)
- Fetches and configures cluster CA certificate
- Sets up OIDC user credentials and cluster configuration
- Creates and switches to the appropriate kubectl context
- Tests authentication by listing pods

**🚀 USAGE - QUICK START**:
1. **Edit the script**: Update the `USERNAME` variable (line 10) with your actual username
2. **Run the script**: `./user-login-script.sh`
3. **Follow prompts**: Complete OIDC authentication in your browser when prompted
4. **You're ready**: The script automatically switches to the new context - start using kubectl!

#### `clear-login-cache.sh`
Simple cache cleanup utility for Kubernetes authentication.
This is important if you would like to force re-authentication to get, e.g., new group membership information for the user.

**Purpose**: Clears kubectl cache to resolve authentication or connection issues.

**What it does**:
- Removes the `~/.kube/cache` directory to clear cached credentials and cluster information


## Job-submission

The job-submission quickstarts provide tools for submitting and managing jobs on the cluster.

