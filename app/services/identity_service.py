from typing import List 

from app.core.exceptions import ConflictException , ForbiddenException , NotFoundException 
from app.models.cover_letter import CoverLetterTemplate 
from app.repositories.cover_letter_repo import CoverLetterRepository 
from app.repositories.profile_repo import ProfileRepository  
from app.schemas.cover_letter import 