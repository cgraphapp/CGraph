# /backend/app/security/defense_layers.py
"""
Multiple security layers:
1. Network (WAF, TLS)
2. Application (input validation, auth)
3. Data (encryption, audit)
4. Operations (monitoring, incident response)
"""

class SecurityLayers:
    
    # Layer 1: Network Security
    NETWORK_SECURITY = {
        'tls_version': 'TLS 1.3',
        'ciphers': 'strong only',
        'hsts': 'enabled',
        'waf': 'AWS WAF with OWASP rules'
    }
    
    # Layer 2: Application Security
    APPLICATION_SECURITY = {
        'input_validation': 'strict whitelist',
        'sql_injection': 'parameterized queries',
        'xss': 'HTML escaping + CSP headers',
        'csrf': 'SameSite cookies',
        'authentication': 'MFA required',
        'authorization': 'role-based access',
        'rate_limiting': '100 req/min per IP'
    }
    
    # Layer 3: Data Security
    DATA_SECURITY = {
        'encryption_at_rest': 'AES-256',
        'encryption_in_transit': 'TLS 1.3',
        'key_management': 'AWS KMS',
        'password_hashing': 'bcrypt + salt',
        'audit_logging': 'all access tracked'
    }
    
    # Layer 4: Operations Security
    OPERATIONS_SECURITY = {
        'intrusion_detection': 'Falco runtime detection',
        'log_monitoring': 'CloudWatch + ELK',
        'vulnerability_scanning': 'Trivy + OWASP ZAP',
        'incident_response': '24/7 monitoring',
        'disaster_recovery': 'RTO < 5 minutes'
    }
