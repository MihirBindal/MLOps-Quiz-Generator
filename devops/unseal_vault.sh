#!/bin/bash
echo "Unsealing Vault..."
kubectl exec -it vault-0 -- vault operator unseal i2J1Cc6tiwecVPuyhdDULTxEwl8GB9zCKU6VfOBN4CQ=
echo "Vault Unsealed Successfully!"
