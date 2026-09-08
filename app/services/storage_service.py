import os 
import aiofiles 
from app.core.config import settings 
from app.core.security import encrypt_pdf_payload , decrypt_pdf_payload 

class StorageService:
    @staticmethod
    async def save_file(file_id: str , raw_bytes:bytes) -> str:
        """  encrypts and writes the file and returns storage path / key """
        encrypted_data = encrypt_pdf_payload(raw_bytes)

        if settings.STORAGE_BACKEND == "local":
            os.makedirs(settings.LOCAL_STORAGE_DIR , exist_ok=True)
            path = os.path.join(settings.LOCAL_STORAGE_DIR , f"{file_id}.enc")

            async with aiofiles.open(path,"wb") as f:
                await f.write(encrypted_data)
            return path 

        elif settings.STORAGE_BACKEND == "s3":
            ## will add this later 
            pass

    @staticmethod 
    async def get_file(path:str ) -> bytes:
        """ gets and decrypt the file  """ 
        if settings.STORAGE_BACKEND == "local":
            async with aiofiles.open(path,'rb') as f :
                encrypted_data  = await f.read()
            return decrypt_pdf_payload(encrypted_data)

        elif settings.STORAGE_BACKEND == "s3":
            pass 

        