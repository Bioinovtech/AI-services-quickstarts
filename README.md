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

The job-submission quickstarts provide tools for submitting and managing GPU-accelerated training jobs on the cluster.

### Scripts

#### `submit-job.sh`
Simple job submission script for deploying Kubernetes jobs. It actually just runs:
```bash
kubectl apply -f gpu-training-job.yaml
```

**Purpose**: Quickly deploy predefined job configurations to the cluster.

**What it does**:
- Applies the GPU training job YAML configuration to the cluster using kubectl

**🚀 USAGE - QUICK START**:
1. **Ensure authentication**: Make sure you're authenticated to the cluster (use user-login scripts first)
2. **Submit the job**: `./submit-job.sh`
3. **Monitor progress**: Check job status with `kubectl get jobs` and `kubectl get pods`

#### `gpu-training-job.yaml`
Kubernetes Job specification for GPU-accelerated machine learning training workloads.

**Purpose**: Provides a template for running LLM training jobs with GPU resources on the cluster.

**What it includes**:
- NVIDIA CUDA runtime environment (Ubuntu 22.04 + CUDA 11.8.0)
- GPU resource allocation (1 GPU with 16Gi memory, 4 CPU cores)
- Persistent volume mounts for training data and model checkpoints
- Node selection and tolerations for GPU nodes
- Proper environment variables for NVIDIA GPU access

**Configuration**: 
- **Training data**: Mounted at `/data` (requires `training-data-pvc` PVC)
- **Model checkpoints**: Mounted at `/checkpoints` (requires `model-checkpoints-pvc` PVC)
- **GPU requirements**: Targets nodes with `nvidia.com/gpu: "true"` label

**Usage**: Customize the container image, command, and volume claims as needed for your specific training workload.

