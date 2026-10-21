from fastapi import Response 


def pdf_response(content: bytes , filename: str = "resume.pdf") -> Response:
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'inline; filename ="{filename}"', 
            "X-Content-Type-Options": "nosniff"
        }
    )