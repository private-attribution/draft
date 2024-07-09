#!/bin/bash

# Check if the CERT_DIR environment variable is set
if [ -z "$CERT_DIR" ]; then
  echo "Error: CERT_DIR environment variable is not set."
  exit 1
fi

# Directory where the cert files will be written
CERT_DIR="$1"
# Ensure the directory exists
mkdir -p "$CERT_DIR"

# load cert.pem file
aws secretsmanager get-secret-value \
    --secret-id cert.pem \
    --region {{ aws_region }} \
    --query SecretString \
    --output text \
    > "${CERT_DIR}"/cert.pem

# load key.pem file
aws secretsmanager get-secret-value \
    --secret-id key.pem \
    --region {{ aws_region }} \
    --query SecretString \
    --output text \
    > ${CERT_DIR}/key.pem

# set environmental variables
aws secretsmanager get-secret-value \
    --secret-id {{ env_secret_id }} \
    --region {{ aws_region }} \
    --query SecretString \
    | jq -r 'fromjson | to_entries | .[] | "export \(.key)=\(.value|tostring)"' \
    | while read -r line; do eval "$line"; done
