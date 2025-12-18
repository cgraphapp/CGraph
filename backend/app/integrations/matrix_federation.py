"""
Matrix homeserver federation setup
Enables communication between CGRAPH and other Matrix servers
"""

import json
from typing import Dict

class MatrixFederation:
    """
    Matrix federation allows servers to communicate
    Users can message people on other Matrix servers
    """

    @staticmethod
    def generate_server_config() -> Dict:
        """Generate Matrix server config for federation"""
        return {
            "server_name": "cgraph.org",
            "port": 8448,
            "public_baseurl": "https://matrix.cgraph.org",
            "listeners": [
                {
                    "port": 8008,
                    "bind_addresses": ["0.0.0.0"],
                    "type": "http",
                    "x_forwarded": True,
                    "resources": [
                        {
                            "names": ["client"],
                            "compress": True
                        },
                        {
                            "names": ["federation"],
                            "compress": False
                        }
                    ]
                },
                {
                    "port": 8448,
                    "bind_addresses": ["0.0.0.0"],
                    "type": "http",
                    "tls": True,
                    "x_forwarded": True,
                    "resources": [
                        {
                            "names": ["federation"],
                            "compress": False
                        }
                    ]
                }
            ],
            "database": {
                "name": "psycopg2",
                "args": {
                    "user": "synapse",
                    "password": "password",
                    "database": "synapse",
                    "host": "localhost",
                    "port": 5432,
                    "cp_min": 5,
                    "cp_max": 10
                }
            },
            "log_config": "cgraph.log.config",
            "media_store_path": "/var/lib/synapse/media_store",
            "uploads_path": "/var/lib/synapse/uploads",
            "max_upload_size": "50M",
            "enable_registration": False,
            "enable_registration_without_verification": False,
            "require_email_for_registration": True,
            "email": {
                "smtp_host": "smtp.sendgrid.net",
                "smtp_port": 587,
                "smtp_user": "apikey",
                "smtp_pass": "SG.your_api_key",
                "force_tls": True,
                "require_transport_security": True,
                "notif_from": "CGRAPH <noreply@cgraph.org>",
                "app_name": "CGRAPH"
            },
            "password_config": {
                "enabled": True
            },
            "enable_metrics": True,
            "federation_cert_rotationdays": 3,
            "server_notices": {
                "server_notices_mxid": "@server:cgraph.org",
                "server_notices_display_name": "Server Notices",
                "server_notices_room_name": "Server Notices"
            }
        }

    @staticmethod
    async def setup_well_known_endpoints():
        """
        Setup .well-known endpoints for federation discovery
        Required for servers to find each other
        """
        return {
            "m.server": "matrix.cgraph.org:8448",
            "m.homeserver": {
                "base_url": "https://matrix.cgraph.org"
            }
        }
    