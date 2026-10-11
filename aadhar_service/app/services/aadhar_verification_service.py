"""
Aadhar Service - Verification Logic

Business logic for Aadhar number verification.
Simulates UIDAI verification with hardcoded valid Aadhar numbers and holder data.

Author: GDB Architecture Team
"""

import logging
import asyncio
from datetime import datetime, date
from app.models.aadhar import AadharVerificationResponse

logger = logging.getLogger(__name__)


class AadharVerificationService:
    """
    Service for verifying Aadhar numbers.
    
    Simulates real UIDAI verification by checking against
    a list of 10 hardcoded valid Aadhar numbers with complete holder information.
    Uses async patterns for consistency with other services.
    """
    
    # Hardcoded valid Aadhar numbers with complete holder information
    AADHAR_DATABASE = {
        "123456789012": {
            "name": "Rajesh Kumar",
            "mobile_no": "9876543210",
            "address": "123, MG Road, Bangalore, Karnataka - 560001",
            "gender": "Male",
            "date_of_birth": date(1990, 5, 15),
            "photo_url": "https://randomuser.me/api/portraits/men/1.jpg"
        },
        "234567890123": {
            "name": "Priya Sharma",
            "mobile_no": "9876543211",
            "address": "456, Park Street, Kolkata, West Bengal - 700016",
            "gender": "Female",
            "date_of_birth": date(1985, 8, 22),
            "photo_url": "https://randomuser.me/api/portraits/women/2.jpg"
        },
        "345678901234": {
            "name": "Amit Patel",
            "mobile_no": "9876543212",
            "address": "789, SG Highway, Ahmedabad, Gujarat - 380015",
            "gender": "Male",
            "date_of_birth": date(1992, 3, 10),
            "photo_url": "https://randomuser.me/api/portraits/men/3.jpg"
        },
        "456789012345": {
            "name": "Sneha Reddy",
            "mobile_no": "9876543213",
            "address": "321, Banjara Hills, Hyderabad, Telangana - 500034",
            "gender": "Female",
            "date_of_birth": date(1988, 11, 5),
            "photo_url": "https://randomuser.me/api/portraits/women/4.jpg"
        },
        "567890123456": {
            "name": "Vikram Singh",
            "mobile_no": "9876543214",
            "address": "654, Connaught Place, New Delhi, Delhi - 110001",
            "gender": "Male",
            "date_of_birth": date(1995, 1, 20),
            "photo_url": "https://randomuser.me/api/portraits/men/5.jpg"
        },
        "678901234567": {
            "name": "Anjali Mehta",
            "mobile_no": "9876543215",
            "address": "987, Marine Drive, Mumbai, Maharashtra - 400002",
            "gender": "Female",
            "date_of_birth": date(1991, 7, 18),
            "photo_url": "https://randomuser.me/api/portraits/women/6.jpg"
        },
        "789012345678": {
            "name": "Karthik Iyer",
            "mobile_no": "9876543216",
            "address": "147, Anna Salai, Chennai, Tamil Nadu - 600002",
            "gender": "Male",
            "date_of_birth": date(1987, 9, 25),
            "photo_url": "https://randomuser.me/api/portraits/men/7.jpg"
        },
        "890123456789": {
            "name": "Divya Nair",
            "mobile_no": "9876543217",
            "address": "258, MG Road, Kochi, Kerala - 682016",
            "gender": "Female",
            "date_of_birth": date(1993, 4, 12),
            "photo_url": "https://randomuser.me/api/portraits/women/8.jpg"
        },
        "901234567890": {
            "name": "Arjun Desai",
            "mobile_no": "9876543218",
            "address": "369, FC Road, Pune, Maharashtra - 411004",
            "gender": "Male",
            "date_of_birth": date(1989, 12, 8),
            "photo_url": "https://randomuser.me/api/portraits/men/9.jpg"
        },
        "012345678901": {
            "name": "Meera Kapoor",
            "mobile_no": "9876543219",
            "address": "741, Mall Road, Shimla, Himachal Pradesh - 171001",
            "gender": "Female",
            "date_of_birth": date(1994, 6, 30),
            "photo_url": "https://randomuser.me/api/portraits/women/10.jpg"
        }
    }
    
    # Set of valid Aadhar numbers for quick lookup
    VALID_AADHAR_NUMBERS = set(AADHAR_DATABASE.keys())
    
    @classmethod
    async def verify(cls, aadhar_number: str) -> AadharVerificationResponse:
        """
        Verify if an Aadhar number is valid and return holder information.
        
        Args:
            aadhar_number: 12-digit Aadhar number to verify
            
        Returns:
            AadharVerificationResponse with verification result and holder data
        """
        logger.info(f"Verifying Aadhar number: {aadhar_number[:4]}********")
        
        # Simulate network latency for realistic third-party API behavior
        await asyncio.sleep(0.1)
        
        # Check if Aadhar number is in the valid list
        if aadhar_number in cls.AADHAR_DATABASE:
            holder_data = cls.AADHAR_DATABASE[aadhar_number]
            logger.info(f"✅ Aadhar verification successful: {aadhar_number[:4]}******** - {holder_data['name']}")
            
            return AadharVerificationResponse(
                aadhar_number=aadhar_number,
                is_valid=True,
                status="VERIFIED",
                message="Aadhar number verified successfully",
                name=holder_data["name"],
                mobile_no=holder_data["mobile_no"],
                address=holder_data["address"],
                gender=holder_data["gender"],
                date_of_birth=holder_data["date_of_birth"],
                photo_url=holder_data["photo_url"],
                timestamp=datetime.utcnow()
            )
        else:
            logger.warning(f"❌ Aadhar verification failed: {aadhar_number[:4]}********")
            return AadharVerificationResponse(
                aadhar_number=aadhar_number,
                is_valid=False,
                status="INVALID",
                message="Aadhar number not found in UIDAI database",
                timestamp=datetime.utcnow()
            )
    
    @classmethod
    async def get_valid_aadhar_numbers(cls) -> list[str]:
        """
        Get list of valid Aadhar numbers (for testing purposes).
        
        Returns:
            List of valid Aadhar numbers
        """
        return sorted(list(cls.VALID_AADHAR_NUMBERS))
