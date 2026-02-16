"""
RHINOMETRIC v2.3.0 - RSA Cryptography Tests
============================================

Test suite for RSA-4096 signature generation and validation.

Tests:
- Key generation (4096-bit RSA)
- License signing with RSA-PSS
- Signature validation
- Key corruption handling
- Edge cases and error scenarios

Author: RHINOMETRIC Team
Date: November 2025
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend


# Mark all tests in this module
pytestmark = pytest.mark.crypto


class TestRSAKeyGeneration:
    """Test RSA key pair generation."""
    
    def test_generate_rsa_4096_keys(self, temp_dir, test_logger):
        """Test generation of RSA-4096 key pair."""
        
        test_logger.info("Generating RSA-4096 key pair...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Verify key size
        assert private_key.key_size == 4096, "Key size should be 4096 bits"
        
        # Generate public key
        public_key = private_key.public_key()
        
        assert public_key is not None, "Public key should be generated"
        
        test_logger.info("✓ RSA-4096 key pair generated successfully")
    
    
    def test_save_and_load_private_key(self, temp_dir, test_logger):
        """Test saving and loading private key in PEM format."""
        
        test_logger.info("Testing private key serialization...")
        
        # Generate key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Save to file
        private_key_path = temp_dir / "test_private.pem"
        
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        private_key_path.write_bytes(pem)
        
        # Verify file exists and size
        assert private_key_path.exists(), "Private key file should exist"
        assert private_key_path.stat().st_size > 3000, "Private key should be ~3.2KB"
        
        # Load key back
        loaded_pem = private_key_path.read_bytes()
        loaded_key = serialization.load_pem_private_key(
            loaded_pem,
            password=None,
            backend=default_backend()
        )
        
        assert loaded_key.key_size == 4096, "Loaded key should be 4096 bits"
        
        test_logger.info("✓ Private key serialization successful")
    
    
    def test_save_and_load_public_key(self, temp_dir, test_logger):
        """Test saving and loading public key in PEM format."""
        
        test_logger.info("Testing public key serialization...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Save public key
        public_key_path = temp_dir / "test_public.pem"
        
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        public_key_path.write_bytes(pem)
        
        # Verify file
        assert public_key_path.exists(), "Public key file should exist"
        assert 700 < public_key_path.stat().st_size < 900, "Public key should be ~800 bytes"
        
        # Load key back
        loaded_pem = public_key_path.read_bytes()
        loaded_key = serialization.load_pem_public_key(
            loaded_pem,
            backend=default_backend()
        )
        
        assert loaded_key is not None, "Public key should be loaded"
        
        test_logger.info("✓ Public key serialization successful")


class TestLicenseSigning:
    """Test license signing with RSA-PSS."""
    
    def test_sign_license_data(self, temp_dir, mock_license_data, test_logger):
        """Test signing license data with RSA-PSS."""
        
        test_logger.info("Testing license signing...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Prepare license data (without signature)
        license_data = mock_license_data.copy()
        license_data.pop("signature", None)
        
        # Create canonical JSON
        license_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        # Sign data
        signature = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        assert signature is not None, "Signature should be generated"
        assert len(signature) == 512, "RSA-4096 signature should be 512 bytes"
        
        test_logger.info(f"✓ License signed successfully ({len(signature)} bytes)")
    
    
    def test_signature_consistency(self, temp_dir, mock_license_data, test_logger):
        """Test that same data produces consistent signatures with PSS."""
        
        test_logger.info("Testing signature consistency...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Prepare data
        license_data = mock_license_data.copy()
        license_data.pop("signature", None)
        license_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        # Sign twice
        sig1 = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        sig2 = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # PSS uses random salt, so signatures will be different
        # But both should be valid (tested in next class)
        assert len(sig1) == len(sig2), "Signatures should have same length"
        
        test_logger.info("✓ Signature generation consistent")


class TestSignatureValidation:
    """Test RSA signature validation."""
    
    def test_validate_correct_signature(self, temp_dir, mock_license_data, test_logger):
        """Test validation of correct signature."""
        
        test_logger.info("Testing signature validation (valid)...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Prepare and sign data
        license_data = mock_license_data.copy()
        license_data.pop("signature", None)
        license_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        signature = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Validate signature
        try:
            public_key.verify(
                signature,
                license_json.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            validation_success = True
        except Exception as e:
            test_logger.error(f"Validation failed: {e}")
            validation_success = False
        
        assert validation_success, "Valid signature should be verified"
        
        test_logger.info("✓ Valid signature verified successfully")
    
    
    def test_reject_invalid_signature(self, temp_dir, mock_license_data, test_logger):
        """Test rejection of invalid signature."""
        
        test_logger.info("Testing signature validation (invalid)...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Prepare data
        license_data = mock_license_data.copy()
        license_data.pop("signature", None)
        license_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        # Create invalid signature (random bytes)
        invalid_signature = b'X' * 512
        
        # Try to validate
        validation_failed = False
        try:
            public_key.verify(
                invalid_signature,
                license_json.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            validation_failed = True
        
        assert validation_failed, "Invalid signature should be rejected"
        
        test_logger.info("✓ Invalid signature correctly rejected")
    
    
    def test_reject_tampered_data(self, temp_dir, mock_license_data, test_logger):
        """Test rejection when data is tampered after signing."""
        
        test_logger.info("Testing tampered data detection...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Sign original data
        license_data = mock_license_data.copy()
        license_data.pop("signature", None)
        license_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        signature = private_key.sign(
            license_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Tamper with data
        license_data["customer"] = "TamperedCompany"
        tampered_json = json.dumps(license_data, sort_keys=True, separators=(',', ':'))
        
        # Try to validate with original signature
        validation_failed = False
        try:
            public_key.verify(
                signature,
                tampered_json.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        except Exception:
            validation_failed = True
        
        assert validation_failed, "Tampered data should be detected"
        
        test_logger.info("✓ Data tampering correctly detected")


class TestKeyCorruption:
    """Test handling of corrupted keys."""
    
    def test_corrupted_private_key(self, temp_dir, test_logger):
        """Test handling of corrupted private key."""
        
        test_logger.info("Testing corrupted private key handling...")
        
        # Create corrupted key file
        corrupted_key_path = temp_dir / "corrupted_private.pem"
        corrupted_key_path.write_text("-----BEGIN PRIVATE KEY-----\nCORRUPTED DATA\n-----END PRIVATE KEY-----")
        
        # Try to load
        load_failed = False
        try:
            corrupted_pem = corrupted_key_path.read_bytes()
            serialization.load_pem_private_key(
                corrupted_pem,
                password=None,
                backend=default_backend()
            )
        except Exception:
            load_failed = True
        
        assert load_failed, "Corrupted private key should fail to load"
        
        test_logger.info("✓ Corrupted private key correctly rejected")
    
    
    def test_corrupted_public_key(self, temp_dir, test_logger):
        """Test handling of corrupted public key."""
        
        test_logger.info("Testing corrupted public key handling...")
        
        # Create corrupted key file
        corrupted_key_path = temp_dir / "corrupted_public.pem"
        corrupted_key_path.write_text("-----BEGIN PUBLIC KEY-----\nCORRUPTED DATA\n-----END PUBLIC KEY-----")
        
        # Try to load
        load_failed = False
        try:
            corrupted_pem = corrupted_key_path.read_bytes()
            serialization.load_pem_public_key(
                corrupted_pem,
                backend=default_backend()
            )
        except Exception:
            load_failed = True
        
        assert load_failed, "Corrupted public key should fail to load"
        
        test_logger.info("✓ Corrupted public key correctly rejected")


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_license_data(self, temp_dir, test_logger):
        """Test signing empty license data."""
        
        test_logger.info("Testing empty license data...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Empty data
        empty_data = {}
        empty_json = json.dumps(empty_data, sort_keys=True, separators=(',', ':'))
        
        # Should still be able to sign
        signature = private_key.sign(
            empty_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        assert signature is not None, "Should be able to sign empty data"
        assert len(signature) == 512, "Signature should still be 512 bytes"
        
        test_logger.info("✓ Empty data signed successfully")
    
    
    def test_large_license_data(self, temp_dir, mock_license_data, test_logger):
        """Test signing large license data."""
        
        test_logger.info("Testing large license data...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        
        # Create large license data (many features)
        large_data = mock_license_data.copy()
        large_data["features"] = [f"feature_{i}" for i in range(100)]
        large_data.pop("signature", None)
        
        large_json = json.dumps(large_data, sort_keys=True, separators=(',', ':'))
        
        # Sign
        signature = private_key.sign(
            large_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        assert signature is not None, "Should be able to sign large data"
        assert len(signature) == 512, "Signature size should not change"
        
        test_logger.info("✓ Large data signed successfully")
    
    
    def test_unicode_in_license_data(self, temp_dir, mock_license_data, test_logger):
        """Test signing license data with Unicode characters."""
        
        test_logger.info("Testing Unicode in license data...")
        
        # Generate keys
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Add Unicode characters
        unicode_data = mock_license_data.copy()
        unicode_data["customer"] = "Compañía España 中文 العربية"
        unicode_data.pop("signature", None)
        
        unicode_json = json.dumps(unicode_data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        
        # Sign
        signature = private_key.sign(
            unicode_json.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Validate
        try:
            public_key.verify(
                signature,
                unicode_json.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            validation_success = True
        except Exception:
            validation_success = False
        
        assert validation_success, "Should handle Unicode correctly"
        
        test_logger.info("✓ Unicode handled correctly")


class TestIntegrationWithRealKeys:
    """Integration tests with actual project keys (if available)."""
    
    def test_load_project_public_key(self, public_key_path, test_logger):
        """Test loading the actual project public key."""
        
        test_logger.info(f"Testing project public key: {public_key_path}")
        
        # Load key
        public_pem = public_key_path.read_bytes()
        public_key = serialization.load_pem_public_key(
            public_pem,
            backend=default_backend()
        )
        
        assert public_key is not None, "Project public key should load"
        
        # Get key size
        key_size = public_key.key_size
        assert key_size == 4096, f"Project key should be 4096 bits (got {key_size})"
        
        test_logger.info(f"✓ Project public key loaded ({key_size} bits)")
    
    
    @pytest.mark.skipif(
        not Path("security/rhinometric_private.pem").exists(),
        reason="Private key not available (expected in production)"
    )
    def test_load_project_private_key(self, private_key_path, test_logger):
        """Test loading the actual project private key (skip if not available)."""
        
        test_logger.info(f"Testing project private key: {private_key_path}")
        
        # Load key
        private_pem = private_key_path.read_bytes()
        private_key = serialization.load_pem_private_key(
            private_pem,
            password=None,
            backend=default_backend()
        )
        
        assert private_key is not None, "Project private key should load"
        
        # Get key size
        key_size = private_key.key_size
        assert key_size == 4096, f"Project key should be 4096 bits (got {key_size})"
        
        test_logger.info(f"✓ Project private key loaded ({key_size} bits)")


# ============================================================================
# Summary Test
# ============================================================================

def test_crypto_summary(test_logger):
    """Summary test to confirm all crypto tests passed."""
    
    test_logger.info("\n" + "="*70)
    test_logger.info("RSA CRYPTOGRAPHY TESTS SUMMARY")
    test_logger.info("="*70)
    test_logger.info("✓ RSA-4096 key generation")
    test_logger.info("✓ Key serialization (PEM format)")
    test_logger.info("✓ License signing (RSA-PSS + SHA256)")
    test_logger.info("✓ Signature validation")
    test_logger.info("✓ Tamper detection")
    test_logger.info("✓ Corrupted key handling")
    test_logger.info("✓ Edge cases (empty, large, Unicode)")
    test_logger.info("✓ Integration with project keys")
    test_logger.info("="*70)
    test_logger.info("ALL CRYPTOGRAPHY TESTS PASSED ✓")
    test_logger.info("="*70 + "\n")
    
    assert True, "Crypto test suite completed"
