"""
auth.py – Azure credential factory supporting three auth methods.

Methods:
  service_principal – client-id / client-secret (CI/CD, automation)
  device_code       – interactive browser login (developer use)
  cli               – delegates to 'az login' token (developer use)
"""

from __future__ import annotations

from config import PipelineConfig


def get_credential(cfg: PipelineConfig):
    """
    Return an azure-identity credential appropriate for the configured auth method.
    The returned object is compatible with azure-storage-file-datalake.
    """
    method = cfg.auth_method.lower()

    if method == "service_principal":
        from azure.identity import ClientSecretCredential
        return ClientSecretCredential(
            tenant_id=cfg.tenant_id,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
        )

    elif method == "device_code":
        from azure.identity import DeviceCodeCredential
        print(
            "[auth] Using device-code flow. "
            "Follow the printed instructions to sign in interactively."
        )
        return DeviceCodeCredential(tenant_id=cfg.tenant_id)

    elif method == "cli":
        from azure.identity import AzureCliCredential
        print("[auth] Using Azure CLI credential (requires 'az login').")
        return AzureCliCredential()

    else:
        raise ValueError(
            f"Unknown AUTH_METHOD '{method}'. "
            "Choose: service_principal | device_code | cli"
        )
