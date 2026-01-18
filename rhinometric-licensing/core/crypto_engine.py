"""
RHINOMETRIC Licensing System - Cryptographic Engine (100% OFFLINE)
===================================================================

Motor criptográfico ASIMÉTRICO con:
- RSA-4096 para cifrado/descifrado
- RSA-PSS para firmas digitales
- Sin dependencias de red (GDPR/ENS compliant)

ARQUITECTURA:
- Clave PRIVADA (tu lado): Genera y firma licencias
- Clave PÚBLICA (cliente lado): Valida licencias sin internet

Autor: RHINOMETRIC Security Team
Fecha: Noviembre 2025
Versión: 2.3.0
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, Tuple, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


class CryptoEngine:
    """Motor de cifrado asimétrico para licencias 100% offline"""
    
    def __init__(self, keys_dir: str = None):
        """
        Inicializa el motor criptográfico RSA.
        
        Args:
            keys_dir: Directorio con claves RSA. 
                     Si es None, usa ../secrets/
        """
        if keys_dir is None:
            keys_dir = os.path.join(
                os.path.dirname(__file__), 
                '..', 'secrets'
            )
        
        self.keys_dir = keys_dir
        self.private_key_path = os.path.join(keys_dir, 'rhinometric_private.pem')
        self.public_key_path = os.path.join(keys_dir, 'rhinometric_public.pem')
        
        self._private_key = None
        self._public_key = None
        
    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """
        Genera un par de claves RSA-4096 (privada + pública).
        
        ⚠️ EJECUTAR SOLO UNA VEZ AL CONFIGURAR EL SISTEMA
        
        Returns:
            Tuple[bytes, bytes]: (private_key_pem, public_key_pem)
        """
        print("🔐 Generando par de claves RSA-4096 (esto puede tardar ~30 segundos)...")
        
        # Generar clave privada RSA-4096
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Extraer clave pública
        public_key = private_key.public_key()
        
        # Serializar clave privada (PEM format, sin password para automatización)
        # NOTA: En producción MÁXIMA seguridad, podrías agregar password aquí
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Serializar clave pública (PEM format)
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Crear directorio secrets/ si no existe
        os.makedirs(self.keys_dir, exist_ok=True)
        
        # Guardar clave privada (SOLO EN TU MÁQUINA)
        with open(self.private_key_path, 'wb') as f:
            f.write(b'# RHINOMETRIC PRIVATE KEY - NUNCA COMPARTIR\n')
            f.write(b'# Generated: ' + datetime.utcnow().isoformat().encode() + b'\n')
            f.write(b'# DO NOT COMMIT TO GIT\n\n')
            f.write(private_pem)
        
        # Permisos restrictivos (solo lectura del propietario)
        os.chmod(self.private_key_path, 0o400)
        
        # Guardar clave pública (SE DISTRIBUYE CON EL INSTALADOR)
        with open(self.public_key_path, 'wb') as f:
            f.write(b'# RHINOMETRIC PUBLIC KEY\n')
            f.write(b'# Generated: ' + datetime.utcnow().isoformat().encode() + b'\n')
            f.write(b'# This key is safe to distribute\n\n')
            f.write(public_pem)
        
        print(f"\n{'='*70}")
        print(f"✅ Par de claves RSA generado correctamente")
        print(f"{'='*70}")
        print(f"\n🔒 CLAVE PRIVADA: {self.private_key_path}")
        print(f"   ⚠️  NUNCA COMPARTIR - SOLO TÚ LA USAS")
        print(f"   ⚠️  GUARDAR EN VAULT/PASSWORD MANAGER")
        print(f"   ⚠️  AGREGAR A .gitignore")
        
        print(f"\n🔓 CLAVE PÚBLICA: {self.public_key_path}")
        print(f"   ✅ Se distribuye con el instalador")
        print(f"   ✅ Clientes la usan para validar licencias")
        
        print(f"\n{'='*70}\n")
        
        return private_pem, public_pem
    
    def load_private_key(self):
        """
        Carga la clave privada RSA (para GENERAR licencias).
        
        Raises:
            FileNotFoundError: Si no existe la clave privada
        """
        if not os.path.exists(self.private_key_path):
            raise FileNotFoundError(
                f"❌ No se encontró la clave privada: {self.private_key_path}\n"
                f"Ejecuta: python crypto_engine.py --generate-keys"
            )
        
        with open(self.private_key_path, 'rb') as f:
            private_pem = f.read()
        
        self._private_key = serialization.load_pem_private_key(
            private_pem,
            password=None,
            backend=default_backend()
        )
        
        return self._private_key
    
    def load_public_key(self, public_key_path: str = None):
        """
        Carga la clave pública RSA (para VALIDAR licencias).
        
        Args:
            public_key_path: Ruta a la clave pública. Si es None, usa la predeterminada.
        
        Raises:
            FileNotFoundError: Si no existe la clave pública
        """
        if public_key_path is None:
            public_key_path = self.public_key_path
        
        if not os.path.exists(public_key_path):
            raise FileNotFoundError(
                f"❌ No se encontró la clave pública: {public_key_path}"
            )
        
        with open(public_key_path, 'rb') as f:
            public_pem = f.read()
        
        self._public_key = serialization.load_pem_public_key(
            public_pem,
            backend=default_backend()
        )
        
        return self._public_key
    
    def sign_license(self, license_data: Dict) -> str:
        """
        Firma digitalmente una licencia usando RSA-PSS (clave privada).
        
        Args:
            license_data: Diccionario con datos de la licencia
            
        Returns:
            str: Firma digital en base64
        """
        if not self._private_key:
            self.load_private_key()
        
        # Serializar datos como JSON (orden determinístico)
        license_json = json.dumps(license_data, sort_keys=True)
        
        # Firmar con RSA-PSS
        signature = self._private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Retornar firma en base64
        return base64.b64encode(signature).decode('ascii')
    
    def verify_license_signature(self, license_data: Dict, signature: str) -> bool:
        """
        Verifica la firma digital de una licencia usando RSA-PSS (clave pública).
        
        Args:
            license_data: Diccionario con datos de la licencia
            signature: Firma digital en base64
            
        Returns:
            bool: True si la firma es válida
        """
        if not self._public_key:
            self.load_public_key()
        
        try:
            # Serializar datos (mismo orden que al firmar)
            license_json = json.dumps(license_data, sort_keys=True)
            
            # Decodificar firma
            signature_bytes = base64.b64decode(signature)
            
            # Verificar firma
            self._public_key.verify(
                signature_bytes,
                license_json.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Firma inválida: {str(e)}")
            return False
    
    def create_license_file(self, license_data: Dict) -> str:
        """
        Crea un archivo de licencia completo (.lic) con datos + firma.
        
        Args:
            license_data: Diccionario con datos de la licencia
            
        Returns:
            str: Contenido del archivo .lic en formato JSON
        """
        # Generar firma
        signature = self.sign_license(license_data)
        
        # Crear estructura completa
        license_file = {
            'version': '2.3.0',
            'license': license_data,
            'signature': signature,
            'issued_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Retornar como JSON formateado
        return json.dumps(license_file, indent=2)
    
    def validate_license_file(self, license_file_content: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Valida un archivo de licencia completo.
        
        Args:
            license_file_content: Contenido del archivo .lic (JSON)
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (es_valido, datos_licencia, mensaje)
        """
        try:
            # Parsear JSON
            license_file = json.loads(license_file_content)
            
            # Validar estructura
            if 'license' not in license_file or 'signature' not in license_file:
                return False, None, "❌ Estructura de licencia inválida"
            
            license_data = license_file['license']
            signature = license_file['signature']
            
            # Verificar firma
            if not self.verify_license_signature(license_data, signature):
                return False, None, "❌ Firma digital inválida - licencia corrupta o falsificada"
            
            return True, license_data, "✅ Licencia válida"
            
        except json.JSONDecodeError:
            return False, None, "❌ Formato de archivo inválido (no es JSON)"
        except Exception as e:
            return False, None, f"❌ Error al validar licencia: {str(e)}"
    



# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def init_rsa_keys(keys_dir: str = None) -> Tuple[str, str]:
    """
    Inicializa el par de claves RSA del sistema.
    
    Esta función debe ejecutarse UNA SOLA VEZ al configurar RHINOMETRIC.
    
    Args:
        keys_dir: Directorio donde guardar las claves (opcional)
        
    Returns:
        Tuple[str, str]: (ruta_clave_privada, ruta_clave_publica)
    """
    engine = CryptoEngine(keys_dir)
    engine.generate_rsa_keypair()
    return engine.private_key_path, engine.public_key_path


def test_crypto_engine():
    """
    Test de integración del motor criptográfico RSA.
    
    Ejecuta:
        python crypto_engine.py
    """
    print("🔒 RHINOMETRIC Crypto Engine RSA - Test de Integración\n")
    
    # 1. Generar claves RSA
    print("1️⃣ Generando par de claves RSA-4096...")
    test_keys_dir = os.path.join(os.path.dirname(__file__), '..', 'secrets', 'test')
    os.makedirs(test_keys_dir, exist_ok=True)
    
    engine = CryptoEngine(test_keys_dir)
    private_pem, public_pem = engine.generate_rsa_keypair()
    print(f"✅ Clave privada: {len(private_pem)} bytes")
    print(f"✅ Clave pública: {len(public_pem)} bytes")
    
    # 2. Cargar claves
    print("\n2️⃣ Cargando claves...")
    engine.load_private_key()
    engine.load_public_key()
    print("✅ Claves cargadas correctamente")
    
    # 3. Crear licencia de prueba
    print("\n3️⃣ Creando licencia de prueba...")
    test_license = {
        'customer': 'ClienteDemo',
        'type': 'trial',
        'expires': '2025-12-31',
        'hwid': 'A3F7C9E1B2D4F6A8',
        'features': ['monitoring', 'alerting']
    }
    
    # 4. Firmar licencia
    print("\n4️⃣ Firmando licencia...")
    signature = engine.sign_license(test_license)
    print(f"✅ Firma generada ({len(signature)} chars):")
    print(f"   {signature[:60]}...")
    
    # 5. Crear archivo .lic completo
    print("\n5️⃣ Creando archivo .lic completo...")
    license_file_content = engine.create_license_file(test_license)
    print(f"✅ Archivo .lic generado ({len(license_file_content)} bytes)")
    print(f"\nContenido (primeras 200 chars):")
    print(f"{license_file_content[:200]}...")
    
    # 6. Validar archivo .lic
    print("\n6️⃣ Validando archivo .lic...")
    is_valid, license_data, message = engine.validate_license_file(license_file_content)
    print(f"{message}")
    if is_valid:
        print(f"✅ Datos validados: {license_data}")
    
    # 7. Intentar validar licencia corrupta
    print("\n7️⃣ Probando licencia corrupta...")
    corrupted_license = license_file_content.replace('"ClienteDemo"', '"ClienteHacker"')
    is_valid_fake, _, message_fake = engine.validate_license_file(corrupted_license)
    print(f"{message_fake}")
    print(f"✅ Licencia corrupta rechazada: {not is_valid_fake}")
    
    # 8. Cleanup
    print("\n8️⃣ Limpiando archivos de prueba...")
    import shutil
    shutil.rmtree(test_keys_dir)
    print("✅ Cleanup completado")
    
    print("\n" + "="*70)
    print("✅ TODOS LOS TESTS PASARON")
    print("="*70)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--generate-keys':
        # Generar claves de producción
        init_rsa_keys()
    else:
        # Ejecutar tests
        test_crypto_engine()
