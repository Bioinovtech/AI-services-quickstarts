#!/bin/bash

set -e

# Configuration
CLUSTER_NAME='ml-cluster'
CLUSTER_SERVER='https://10.3.10.1:6443'
CLUSTER_HOST='10.3.10.1'
CLUSTER_PORT='6443'
USERNAME='CHANGEME'
OIDC_SERVER='https://auth.ml-cluster.dei.uc.pt'
OIDC_ISSUER_URL="${OIDC_SERVER}/realms/ml-cluster"
OIDC_CLIENT_ID='k8s'

echo "Setting up kubectl for ML cluster authentication..."

# Check if kubectl oidc-login plugin is installed
echo "Checking for kubectl oidc-login plugin..."
if ! kubectl oidc-login --help &>/dev/null; then
    echo "kubectl oidc-login plugin not found. Installing..."
    
    # Detect OS and architecture
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case "${OS}_${ARCH}" in
        "darwin_arm64")
            BINARY_URL="https://github.com/int128/kubelogin/releases/latest/download/kubelogin_darwin_arm64.zip"
            ;;
        "darwin_x86_64")
            BINARY_URL="https://github.com/int128/kubelogin/releases/latest/download/kubelogin_darwin_amd64.zip"
            ;;
        "linux_x86_64")
            BINARY_URL="https://github.com/int128/kubelogin/releases/latest/download/kubelogin_linux_amd64.zip"
            ;;
        "linux_aarch64")
            BINARY_URL="https://github.com/int128/kubelogin/releases/latest/download/kubelogin_linux_arm64.zip"
            ;;
        *)
            echo "Unsupported OS/Architecture: ${OS}/${ARCH}"
            echo "Please install kubectl oidc-login manually from:"
            echo "https://github.com/int128/kubelogin/releases"
            exit 1
            ;;
    esac
    
    # Create temporary directory for download
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    echo "Downloading kubectl oidc-login for ${OS}/${ARCH}..."
    curl -LO "$BINARY_URL"
    
    # Extract the binary (following the reference pattern)
    unzip -q "$(basename "$BINARY_URL")"
    
    # Install to /usr/local/bin (like the reference)
    echo "Installing kubectl-oidc_login to /usr/local/bin..."
    sudo mv kubelogin /usr/local/bin/kubectl-oidc_login
    sudo chmod +x /usr/local/bin/kubectl-oidc_login
    
    # Clean up
    cd - >/dev/null
    rm -rf "$TEMP_DIR"
    
    # Verify installation
    if kubectl oidc-login --help &>/dev/null; then
        echo "kubectl oidc-login plugin installed successfully!"
    else
        echo "Failed to install kubectl oidc-login plugin."
        echo "Please install manually and try again."
        exit 1
    fi
else
    echo "kubectl oidc-login plugin is already installed."
fi

# Extract cluster CA certificate
echo "Fetching cluster CA certificate from ${CLUSTER_HOST}:${CLUSTER_PORT}..."
CLUSTER_CA_PEM=$(echo | openssl s_client -connect "${CLUSTER_HOST}:${CLUSTER_PORT}" -servername "${CLUSTER_HOST}" 2>/dev/null | \
  openssl x509 -outform PEM 2>/dev/null)

if [ -z "$CLUSTER_CA_PEM" ]; then
  echo "Error: Could not obtain cluster CA certificate from ${CLUSTER_HOST}:${CLUSTER_PORT}"
  echo "Please check network connectivity to the cluster."
  exit 1
fi

# Write certificate to temporary file for kubectl
TEMP_CA_FILE=$(mktemp)
echo "$CLUSTER_CA_PEM" > "$TEMP_CA_FILE"
echo "Successfully extracted cluster CA certificate"

# Clean up existing configuration
echo "Cleaning up existing kubectl configuration..."
kubectl config delete-context "${USERNAME}" 2>/dev/null || true
kubectl config delete-user "${USERNAME}" 2>/dev/null || true
kubectl config delete-cluster "${CLUSTER_NAME}" 2>/dev/null || true

# Configure cluster
echo "Configuring cluster..."
kubectl config set-cluster "${CLUSTER_NAME}" \
  --server="${CLUSTER_SERVER}" \
  --certificate-authority="$TEMP_CA_FILE" \
  --embed-certs=true

# Configure OIDC user
echo "Configuring OIDC authentication..."
kubectl config set-credentials "${USERNAME}" \
  --exec-api-version=client.authentication.k8s.io/v1beta1 \
  --exec-command=kubectl \
  --exec-arg=oidc-login \
  --exec-arg=get-token \
  --exec-arg=--oidc-issuer-url="${OIDC_ISSUER_URL}" \
  --exec-arg=--oidc-client-id="${OIDC_CLIENT_ID}" \
  --exec-arg=--oidc-extra-scope=openid \
  --exec-arg=--oidc-extra-scope=profile \
  --exec-arg=--oidc-extra-scope=email \
  --exec-arg=--oidc-extra-scope=groups \
  --exec-arg=--insecure-skip-tls-verify

# Create context
echo "Creating kubectl context..."
kubectl config set-context "${USERNAME}" \
  --cluster="${CLUSTER_NAME}" \
  --user="${USERNAME}" \
  --namespace=default

# Clean up temporary file
rm -f "$TEMP_CA_FILE"


# Test authentication
echo "Testing kubectl authentication..."
kubectl --context=${USERNAME} get pods -A


echo "In order to switch to new context, run:"
echo "kubectl config use-context "${USERNAME}"

kubectl config use-context "${USERNAME}"