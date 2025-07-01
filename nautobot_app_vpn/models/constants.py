from django.db.models import TextChoices


# 🔹 Encryption Algorithms
class EncryptionAlgorithms(TextChoices):
    DES = "des", "DES (56-bit)"
    TRIPLE_DES = "3des", "3DES (168-bit)"
    AES_128_CBC = "aes-128-cbc", "AES-128-CBC"
    AES_192_CBC = "aes-192-cbc", "AES-192-CBC"
    AES_256_CBC = "aes-256-cbc", "AES-256-CBC"
    AES_128_GCM = "aes-128-gcm", "AES-128-GCM"
    AES_256_GCM = "aes-256-gcm", "AES-256-GCM"


# 🔹 Authentication Algorithms
class AuthenticationAlgorithms(TextChoices):
    NONE = "non-auth", "None"
    MD5 = "md5", "MD5 (128-bit)"
    SHA1 = "sha1", "SHA-1 (160-bit)"
    SHA256 = "sha256", "SHA-256"
    SHA384 = "sha384", "SHA-384"
    SHA512 = "sha512", "SHA-512"


# 🔹 Diffie-Hellman Groups
class DiffieHellmanGroups(TextChoices):
    GROUP_1 = "1", "Group 1 - 768-bit"
    GROUP_2 = "2", "Group 2 - 1024-bit"
    GROUP_5 = "5", "Group 5 - 1536-bit"
    GROUP_14 = "14", "Group 14 - 2048-bit"
    GROUP_15 = "15", "Group 15 - 3072-bit"
    GROUP_16 = "16", "Group 16 - 4096-bit"
    GROUP_19 = "19", "Group 19 - 256-bit elliptic curve"
    GROUP_20 = "20", "Group 20 - 384-bit elliptic curve"
    GROUP_21 = "21", "Group 21 - 521-bit elliptic curve"


# 🔹 IKE Authentication Types
class IKEAuthenticationTypes(TextChoices):
    PSK = "psk", "Pre-Shared Key"
    CERT = "cert", "Certificate-Based Authentication"


# 🔹 IPSec Protocols
class IPSECProtocols(TextChoices):
    ESP = "esp", "ESP (Encapsulating Security Payload)"
    AH = "ah", "AH (Authentication Header)"


# 🔹 Lifetime Units
class LifetimeUnits(TextChoices):
    SECONDS = "seconds", "Seconds"
    MINUTES = "minutes", "Minutes"
    HOURS = "hours", "Hours"
    DAYS = "days", "Days"

# 🔹 IKE Versions
class IKEVersions(TextChoices):
    IKEV1 = "ikev1", "IKEv1"
    IKEV2 = "ikev2", "IKEv2"
    IKEV2_PREFERRED = "ikev2-preferred", "IKEv2 Preferred" # Common practice

# 🔹 IKE Exchange Modes (Primarily for IKEv1)
class IKEExchangeModes(TextChoices):
    AUTO = "auto", "Auto"
    MAIN = "main", "Main"
    AGGRESSIVE = "aggressive", "Aggressive"

# 🔹 Identification Types
class IdentificationTypes(TextChoices):
    IP_ADDRESS = "ipaddr", "IP Address"
    FQDN = "fqdn", "FQDN (Hostname)"
    USER_FQDN = "ufqdn", "User FQDN (Email Address)"
    KEY_ID = "keyid", "Key ID (String)"
    # Add others if necessary based on PAN-OS versions

class IPAddressTypes(TextChoices):
    IP = "ip", "IP Address"
    FQDN = "fqdn", "FQDN"
    DYNAMIC = "dynamic", "Dynamic"