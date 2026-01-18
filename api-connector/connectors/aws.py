"""
RHINOMETRIC v2.4.0 - AWS Connector
==================================

Conector para AWS CloudWatch metrics y logs.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AWSConnector:
    """Conector para AWS CloudWatch."""
    
    def __init__(
        self,
        region: str,
        access_key: str,
        secret_key: str
    ):
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testear conexión a AWS.
        
        Returns:
            dict: {success: bool, message: str, details: dict}
        """
        try:
            # Crear cliente CloudWatch
            session = boto3.Session(
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            
            cloudwatch = session.client('cloudwatch')
            
            # Test API call - list metrics (limited)
            response = cloudwatch.list_metrics(MaxRecords=1)
            
            # Get account ID
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            account_id = identity['Account']
            
            return {
                "success": True,
                "message": f"Connected to AWS CloudWatch ({self.region})",
                "details": {
                    "region": self.region,
                    "account_id": account_id,
                    "service": "CloudWatch"
                }
            }
        
        except NoCredentialsError:
            logger.error("Invalid AWS credentials")
            return {
                "success": False,
                "message": "Invalid AWS credentials",
                "details": {"error": "invalid_credentials"}
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS error: {error_code}")
            return {
                "success": False,
                "message": f"AWS error: {error_code}",
                "details": {"error": error_code}
            }
        
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error": str(e)}
            }
