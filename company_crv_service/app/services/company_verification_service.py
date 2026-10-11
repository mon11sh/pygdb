"""
Company CRV Service - Verification Logic

Business logic for company registration number verification.
Simulates MCA (Ministry of Corporate Affairs) verification with hardcoded valid CINs.

Author: GDB Architecture Team
"""

import logging
import asyncio
from datetime import datetime
from app.models.company import CompanyVerificationResponse

logger = logging.getLogger(__name__)


class CompanyVerificationService:
    """
    Service for verifying company registration numbers.
    
    Simulates real MCA/ROC verification by checking against
    a list of 10 hardcoded valid registration numbers with full company details.
    Uses async patterns for consistency with other services.
    """
    
    # Hardcoded valid company registration numbers (CINs) with full details
    VALID_COMPANIES = {
        "U72900KA2020PTC123456": {
            "company_name": "Tech Innovations Pvt Ltd",
            "type": "Private Limited",
            "address": "123 Tech Park, Electronic City, Bangalore, Karnataka - 560100",
            "email": "info@techinnovations.com",
            "phone": "+91-80-12345678",
            "website": "https://techinnovations.com",
            "incorporation_date": "2020-01-15",
            "paid_up_capital": "10,00,000",
            "directors": ["Rajesh Kumar", "Priya Sharma"]
        },
        "L67120MH2019PLC234567": {
            "company_name": "Global Finance Ltd",
            "type": "Public Limited",
            "address": "456 Financial District, BKC, Mumbai, Maharashtra - 400051",
            "email": "contact@globalfinance.com",
            "phone": "+91-22-23456789",
            "website": "https://globalfinance.com",
            "incorporation_date": "2019-06-20",
            "paid_up_capital": "50,00,000",
            "directors": ["Suresh Menon", "Anita Desai", "Vikram Singh"]
        },
        "U74999DL2021PTC345678": {
            "company_name": "Digital Solutions Pvt Ltd",
            "type": "Private Limited",
            "address": "789 Cyber Hub, Gurugram, Delhi NCR - 122002",
            "email": "hello@digitalsolutions.in",
            "phone": "+91-124-3456789",
            "website": "https://digitalsolutions.in",
            "incorporation_date": "2021-03-10",
            "paid_up_capital": "25,00,000",
            "directors": ["Amit Patel", "Sneha Reddy"]
        },
        "L85110TN2018PLC456789": {
            "company_name": "Manufacturing Excellence Ltd",
            "type": "Public Limited",
            "address": "Plot 100, SIPCOT Industrial Park, Chennai, Tamil Nadu - 600058",
            "email": "info@manufacturingexcellence.com",
            "phone": "+91-44-45678901",
            "website": "https://manufacturingexcellence.com",
            "incorporation_date": "2018-09-05",
            "paid_up_capital": "1,00,00,000",
            "directors": ["Rahul Sharma", "Deepika Kapoor", "Manish Gupta"]
        },
        "U51909GJ2022PTC567890": {
            "company_name": "Retail Ventures Pvt Ltd",
            "type": "Private Limited",
            "address": "55 Commerce Center, Ahmedabad, Gujarat - 380009",
            "email": "support@retailventures.co.in",
            "phone": "+91-79-56789012",
            "website": "https://retailventures.co.in",
            "incorporation_date": "2022-02-28",
            "paid_up_capital": "15,00,000",
            "directors": ["Kiran Patel", "Meera Shah"]
        },
        "L24233WB2017PLC678901": {
            "company_name": "Eastern Chemicals Ltd",
            "type": "Public Limited",
            "address": "Industrial Area, Durgapur, West Bengal - 713213",
            "email": "contact@easternchemicals.com",
            "phone": "+91-343-6789012",
            "website": "https://easternchemicals.com",
            "incorporation_date": "2017-11-15",
            "paid_up_capital": "75,00,000",
            "directors": ["Arun Banerjee", "Suman Roy", "Priyanka Das"]
        },
        "U45200HR2023PTC789012": {
            "company_name": "Green Energy Solutions Pvt Ltd",
            "type": "Private Limited",
            "address": "Eco Park, Sector 62, Faridabad, Haryana - 121004",
            "email": "info@greenenergysolutions.in",
            "phone": "+91-129-7890123",
            "website": "https://greenenergysolutions.in",
            "incorporation_date": "2023-01-20",
            "paid_up_capital": "30,00,000",
            "directors": ["Vivek Tiwari", "Neha Agarwal"]
        },
        "L29130AP2019PLC890123": {
            "company_name": "Pharma Health Ltd",
            "type": "Public Limited",
            "address": "Pharma City, Visakhapatnam, Andhra Pradesh - 530046",
            "email": "corporate@pharmahealth.com",
            "phone": "+91-891-8901234",
            "website": "https://pharmahealth.com",
            "incorporation_date": "2019-08-12",
            "paid_up_capital": "2,00,00,000",
            "directors": ["Dr. Ramesh Naidu", "Dr. Lakshmi Devi", "Srinivas Rao"]
        },
        "U62013RJ2021PTC901234": {
            "company_name": "Textile Creations Pvt Ltd",
            "type": "Private Limited",
            "address": "Textile Market, Jaipur, Rajasthan - 302001",
            "email": "sales@textilecreations.in",
            "phone": "+91-141-9012345",
            "website": "https://textilecreations.in",
            "incorporation_date": "2021-05-30",
            "paid_up_capital": "20,00,000",
            "directors": ["Mahesh Jain", "Rekha Agarwal"]
        },
        "L15142UP2020PLC012345": {
            "company_name": "Food Processing Industries Ltd",
            "type": "Public Limited",
            "address": "Food Park, Greater Noida, Uttar Pradesh - 201310",
            "email": "info@foodprocessing.com",
            "phone": "+91-120-0123456",
            "website": "https://foodprocessing.com",
            "incorporation_date": "2020-04-18",
            "paid_up_capital": "1,50,00,000",
            "directors": ["Rajendra Singh", "Kavita Verma", "Alok Kumar"]
        }
    }
    
    # Keep backwards compatibility
    VALID_REGISTRATION_NUMBERS = set(VALID_COMPANIES.keys())
    
    @classmethod
    async def verify(cls, registration_number: str) -> CompanyVerificationResponse:
        """
        Verify if a company registration number is valid.
        
        Args:
            registration_number: 21-character CIN to verify
            
        Returns:
            CompanyVerificationResponse with verification result and company details
        """
        logger.info(f"Verifying company registration: {registration_number[:8]}*************")
        
        # Simulate network latency for realistic third-party API behavior
        await asyncio.sleep(0.1)
        
        # Check if registration number is in the valid list
        company_data = cls.VALID_COMPANIES.get(registration_number)
        
        if company_data:
            logger.info(f"✅ Company verification successful: {registration_number[:8]}*************")
            return CompanyVerificationResponse(
                registration_number=registration_number,
                is_valid=True,
                status="VERIFIED",
                message="Company registration number verified successfully",
                timestamp=datetime.utcnow(),
                company_name=company_data["company_name"],
                type=company_data["type"],
                address=company_data["address"],
                email=company_data["email"],
                phone=company_data["phone"],
                website=company_data["website"],
                incorporation_date=company_data["incorporation_date"],
                paid_up_capital=company_data["paid_up_capital"],
                directors=company_data["directors"]
            )
        else:
            logger.warning(f"❌ Company verification failed: {registration_number[:8]}*************")
            return CompanyVerificationResponse(
                registration_number=registration_number,
                is_valid=False,
                status="INVALID",
                message="Company registration number not found in MCA records",
                timestamp=datetime.utcnow()
            )
    
    @classmethod
    async def get_valid_registration_numbers(cls) -> list[str]:
        """
        Get list of valid registration numbers (for testing purposes).
        
        Returns:
            List of valid CINs
        """
        return sorted(list(cls.VALID_REGISTRATION_NUMBERS))
