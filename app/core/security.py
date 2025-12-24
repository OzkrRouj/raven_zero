from cryptography.fernet import Fernet


class SecurityService:
    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()

    @staticmethod
    def encrypt_data(data: bytes, key: str) -> bytes:
        f = Fernet(key.encode())
        return f.encrypt(data)

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: str, ttl: int = None) -> bytes:
        f = Fernet(key.encode())
        return f.decrypt(encrypted_data, ttl=ttl)


security_service = SecurityService()
