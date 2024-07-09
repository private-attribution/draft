#!/bin/bash

# Check if the CERT_DIR environment variable is set
if [ -z "$CERT_DIR" ]; then
  echo "Error: CERT_DIR environment variable is not set."
  return 1 2>/dev/null || exit 1  # return when sourced, exit otherwise
fi

# Ensure the directory exists
mkdir -p "$CERT_DIR"

# load cert.pem file
aws secretsmanager get-secret-value \
    --secret-id cert.pem \
    --region us-west-2 \
    --query SecretString \
    --output text \
    > "${CERT_DIR}"/cert.pem

# load key.pem file
aws secretsmanager get-secret-value \
    --secret-id key.pem \
    --region us-west-2 \
    --query SecretString \
    --output text \
    > ${CERT_DIR}/key.pem

# set environmental variables
env_vars=$(aws secretsmanager get-secret-value \
    --secret-id prod-draft-env \
    --region us-west-2 \
    --query SecretString \
    | jq -r 'fromjson | to_entries | .[] | "export \(.key)=\(.value|tostring)"')

eval "$env_vars"
