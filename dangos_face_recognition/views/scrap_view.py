import re
import requests
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from bs4 import BeautifulSoup
from ..models import Job

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def scrap_job(request):
    try:
        response = requests.get(
            "https://www.sunlife.co.id/en/life-moments/starting-my-career/jenis-jenis-pekerjaan/",
            timeout=15,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Connection": "keep-alive",
            }
        )

        if response.status_code != 200:
            return Response({
                "status": status.HTTP_502_BAD_GATEWAY,
                "message": "Failed to fetch source website"
            }, status=status.HTTP_502_BAD_GATEWAY)

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = []

        for p in soup.find_all("p"):
            strongs = p.find_all("strong")

            if len(strongs) < 2:
                continue

            job_text = strongs[1].get_text(strip=True)
            job_text = re.sub(r"^\d+\.\s*", "", job_text)

            if job_text and len(job_text) > 2:
                jobs.append(job_text)

        jobs = list(dict.fromkeys(jobs))
        created_count = 0
        existing_count = 0

        for job_title in jobs:
            _, created = Job.objects.get_or_create(
                title=job_title
            )
            if created:
                created_count += 1
            else:
                existing_count += 1

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Job types fetched successfully",
            "total": len(jobs),
            "summary": {
                "total_scraped": len(jobs),
                "created": created_count,
                "already_exists": existing_count
            },
            "data": jobs
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)