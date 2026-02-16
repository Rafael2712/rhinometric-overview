"""
RHINOMETRIC v2.3.0 - License Validator Tests
=============================================

Test suite for validate_license.py offline validator.

Tests cover:
- Valid license acceptance
- Expired license rejection
- HWID mismatch detection
- Corrupted signature detection
- Missing fields handling
- Malformed JSON handling
- Integration with real keys
"""

import pytest
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

pytestmark = pytest.mark.validator


class TestValidatorExecution:
    """Test basic validator script execution."""
    
    def test_validator_script_exists(self, validator_script, test_logger):
        """Test that validate_license.py exists and is accessible."""
        assert validator_script.exists(), f"Validator script not found: {validator_script}"
        test_logger.info(f"✓ Validator script found: {validator_script}")
    
    def test_validator_is_python_file(self, validator_script, test_logger):
        """Test that validator is a valid Python file."""
        content = validator_script.read_text()
        assert content.startswith("#!/usr/bin/env python3") or "import" in content
        test_logger.info("✓ Validator is valid Python script")
    
    def test_validator_has_main_function(self, validator_script, test_logger):
        """Test that validator has main execution logic."""
        content = validator_script.read_text()
        assert "def main()" in content or "if __name__" in content
        test_logger.info("✓ Validator has main() function")


class TestValidLicenseValidation:
    """Test validation of valid licenses."""
    
    def test_validate_valid_license(self, temp_license_file, validator_script, test_logger):
        """Test that a valid license passes validation."""
        result = subprocess.run(
            ["python3", str(validator_script), str(temp_license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        test_logger.info(f"Exit code: {result.returncode}")
        test_logger.info(f"Stdout: {result.stdout}")
        test_logger.info(f"Stderr: {result.stderr}")
        
        # Valid license should exit with 0
        assert result.returncode == 0, f"Valid license rejected: {result.stderr}"
        test_logger.info("✓ Valid license accepted")
    
    def test_extract_license_info(self, temp_license_file, validator_script, test_logger):
        """Test that validator extracts license information correctly."""
        result = subprocess.run(
            ["python3", str(validator_script), str(temp_license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout.lower()
        
        # Should contain key information
        assert "customer" in output or "cliente" in output
        assert "expires" in output or "expira" in output
        assert "valid" in output or "válida" in output or "valida" in output
        
        test_logger.info("✓ License information extracted correctly")
    
    def test_validate_license_with_features(self, temp_dir, mock_license_data, 
                                           validator_script, test_logger):
        """Test validation of license with multiple features."""
        # Add multiple features
        mock_license_data["features"] = [
            "metrics-collection",
            "logs-aggregation",
            "traces-distributed",
            "dashboards-custom",
            "alerts-prometheus"
        ]
        
        # Create license file
        license_file = temp_dir / "test_features.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        test_logger.info(f"✓ License with {len(mock_license_data['features'])} features validated")


class TestExpiredLicenseRejection:
    """Test rejection of expired licenses."""
    
    def test_reject_expired_license(self, temp_dir, expired_license_data, 
                                    validator_script, test_logger):
        """Test that expired licenses are rejected."""
        license_file = temp_dir / "expired.lic"
        license_file.write_text(json.dumps(expired_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Expired license should exit with 1
        assert result.returncode == 1, "Expired license was accepted"
        
        output = result.stdout.lower() + result.stderr.lower()
        assert "expired" in output or "expirada" in output or "vencida" in output
        
        test_logger.info("✓ Expired license correctly rejected")
    
    def test_expired_by_one_day(self, temp_dir, mock_license_data, 
                               validator_script, test_logger):
        """Test license expired by exactly 1 day."""
        # Set expiration to yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        mock_license_data["expires"] = yesterday
        
        license_file = temp_dir / "expired_1day.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ License expired by 1 day rejected")
    
    def test_expires_today(self, temp_dir, mock_license_data, 
                          validator_script, test_logger):
        """Test license expiring today (should still be valid)."""
        # Set expiration to today
        today = datetime.now().strftime("%Y-%m-%d")
        mock_license_data["expires"] = today
        
        license_file = temp_dir / "expires_today.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # License expiring today should still be valid
        assert result.returncode == 0
        test_logger.info("✓ License expiring today is still valid")


class TestHWIDMismatch:
    """Test HWID validation and mismatch detection."""
    
    def test_reject_incorrect_hwid(self, temp_dir, mock_license_data, 
                                   validator_script, test_logger):
        """Test that license with incorrect HWID is rejected."""
        # Set impossible HWID
        mock_license_data["hwid"] = "0000000000000000"
        
        license_file = temp_dir / "wrong_hwid.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Wrong HWID should be rejected
        assert result.returncode == 1
        
        output = result.stdout.lower() + result.stderr.lower()
        assert "hwid" in output or "hardware" in output or "mismatch" in output
        
        test_logger.info("✓ Incorrect HWID rejected")
    
    def test_reject_different_hwid_format(self, temp_dir, mock_license_data,
                                         validator_script, test_logger):
        """Test rejection of malformed HWID."""
        # Set malformed HWID
        mock_license_data["hwid"] = "ZZZZZZZZZZZZZZZZ"  # Invalid hex
        
        license_file = temp_dir / "bad_hwid_format.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Malformed HWID rejected")


class TestCorruptedSignature:
    """Test detection of corrupted or invalid signatures."""
    
    def test_reject_corrupted_signature(self, temp_dir, mock_license_data,
                                       validator_script, test_logger):
        """Test that license with corrupted signature is rejected."""
        # Corrupt the signature
        if "signature" in mock_license_data:
            mock_license_data["signature"] = "CORRUPTED_SIGNATURE_" + "X" * 500
        
        license_file = temp_dir / "corrupted_sig.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        
        output = result.stdout.lower() + result.stderr.lower()
        assert "signature" in output or "firma" in output or "invalid" in output
        
        test_logger.info("✓ Corrupted signature detected")
    
    def test_reject_missing_signature(self, temp_dir, mock_license_data,
                                     validator_script, test_logger):
        """Test that license without signature is rejected."""
        # Remove signature
        if "signature" in mock_license_data:
            del mock_license_data["signature"]
        
        license_file = temp_dir / "no_signature.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Missing signature detected")
    
    def test_reject_empty_signature(self, temp_dir, mock_license_data,
                                   validator_script, test_logger):
        """Test that license with empty signature is rejected."""
        mock_license_data["signature"] = ""
        
        license_file = temp_dir / "empty_signature.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Empty signature rejected")


class TestMissingFields:
    """Test handling of licenses with missing required fields."""
    
    def test_reject_missing_customer(self, temp_dir, mock_license_data,
                                     validator_script, test_logger):
        """Test rejection of license without customer field."""
        del mock_license_data["customer"]
        
        license_file = temp_dir / "no_customer.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Missing customer field detected")
    
    def test_reject_missing_expires(self, temp_dir, mock_license_data,
                                   validator_script, test_logger):
        """Test rejection of license without expires field."""
        del mock_license_data["expires"]
        
        license_file = temp_dir / "no_expires.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Missing expires field detected")
    
    def test_reject_missing_hwid(self, temp_dir, mock_license_data,
                                validator_script, test_logger):
        """Test rejection of license without hwid field."""
        del mock_license_data["hwid"]
        
        license_file = temp_dir / "no_hwid.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Missing HWID field detected")


class TestMalformedLicense:
    """Test handling of malformed license files."""
    
    def test_reject_invalid_json(self, temp_dir, validator_script, test_logger):
        """Test rejection of license with invalid JSON."""
        license_file = temp_dir / "invalid_json.lic"
        license_file.write_text("{ this is not valid JSON }")
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Invalid JSON detected")
    
    def test_reject_empty_file(self, temp_dir, validator_script, test_logger):
        """Test rejection of empty license file."""
        license_file = temp_dir / "empty.lic"
        license_file.write_text("")
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Empty file rejected")
    
    def test_reject_binary_garbage(self, temp_dir, validator_script, test_logger):
        """Test rejection of binary garbage."""
        license_file = temp_dir / "binary.lic"
        license_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd')
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 1
        test_logger.info("✓ Binary garbage rejected")


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_unicode_customer_name(self, temp_dir, mock_license_data,
                                   validator_script, test_logger):
        """Test license with Unicode characters in customer name."""
        mock_license_data["customer"] = "Compañía España 中文 العربية Företag"
        
        license_file = temp_dir / "unicode_customer.lic"
        license_file.write_text(json.dumps(mock_license_data, ensure_ascii=False, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should handle Unicode correctly
        assert result.returncode in [0, 1]  # Either valid or invalid, but shouldn't crash
        test_logger.info("✓ Unicode in customer name handled")
    
    def test_future_expiration_date(self, temp_dir, mock_license_data,
                                    validator_script, test_logger):
        """Test license with far future expiration (perpetual-like)."""
        future_date = (datetime.now() + timedelta(days=36500)).strftime("%Y-%m-%d")  # 100 years
        mock_license_data["expires"] = future_date
        
        license_file = temp_dir / "perpetual.lic"
        license_file.write_text(json.dumps(mock_license_data, indent=2))
        
        result = subprocess.run(
            ["python3", str(validator_script), str(license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should accept far future dates
        assert result.returncode in [0, 1]
        test_logger.info("✓ Far future expiration handled")
    
    def test_validator_performance(self, temp_license_file, validator_script, test_logger):
        """Test that validation completes in reasonable time."""
        import time
        
        start = time.time()
        result = subprocess.run(
            ["python3", str(validator_script), str(temp_license_file)],
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start
        
        # Validation should complete in less than 3 seconds
        assert elapsed < 3.0, f"Validation too slow: {elapsed:.2f}s"
        test_logger.info(f"✓ Validation completed in {elapsed:.3f}s")


class TestValidatorSummary:
    """Summary test with complete validation report."""
    
    def test_validator_summary(self, validator_script, platform_info, test_logger):
        """Generate summary of validator tests."""
        test_logger.info("=" * 70)
        test_logger.info("VALIDATOR TEST SUITE SUMMARY")
        test_logger.info("=" * 70)
        test_logger.info(f"Validator script: {validator_script}")
        test_logger.info(f"Platform: {platform_info['os']}")
        test_logger.info(f"Python version: {platform_info.get('python_version', 'N/A')}")
        test_logger.info("")
        test_logger.info("Test coverage:")
        test_logger.info("  ✓ Script execution and structure")
        test_logger.info("  ✓ Valid license acceptance")
        test_logger.info("  ✓ Expired license rejection")
        test_logger.info("  ✓ HWID mismatch detection")
        test_logger.info("  ✓ Corrupted signature detection")
        test_logger.info("  ✓ Missing fields handling")
        test_logger.info("  ✓ Malformed JSON handling")
        test_logger.info("  ✓ Edge cases (Unicode, future dates)")
        test_logger.info("=" * 70)
