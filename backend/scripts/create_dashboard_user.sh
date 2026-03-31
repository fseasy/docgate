#!/bin/bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${ENV?env-var ENV is required}"
source "$SCRIPT_DIR/../src/docgate/.env.server.${ENV}"
source $SCRIPT_DIR/.env.supertokens_account

: "${SUPERTOKENS_CONNECTION_URI?env-var SUPERTOKENS_CONNECTION_URI is required}"
: "${SUPERTOKENS_API_KEY?env-var SUPERTOKENS_API_KEY is required}"
: "${EMAIL?env-var EMAIL should be set before run this}"
: "${PASSWD?env-var PASSWD should be set before run this}"

# set -x

curl --location --request POST "${SUPERTOKENS_CONNECTION_URI}/recipe/dashboard/user" \
	--header 'rid: dashboard' \
	--header "api-key: ${SUPERTOKENS_API_KEY}" \
	--header 'Content-Type: application/json' \
	--data-raw "$(jq -n --arg email "$EMAIL" --arg pw "$PASSWD" '{email: $email, password: $pw}')"
