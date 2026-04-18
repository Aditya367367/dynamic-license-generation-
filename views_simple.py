from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LicenseGenerateSerializer
from .services.pil_generator_service import FIELD_NAME_MAP, LicensePILGeneratorService


SERVICE = LicensePILGeneratorService()


class LicenseGenerateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = LicenseGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            data = SERVICE.generate(request, serializer.validated_data)
            return Response(
                {
                    "success": True,
                    "message": "License generated successfully",
                    "data": data,
                }
            )
        except Exception as exc:
            return Response(
                {
                    "success": False,
                    "message": "Failed to generate license",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def license_form_config(request):
    return Response(
        {
            "success": True,
            "data": {
                "fields": [
                    {"name": key, "label": label}
                    for key, label in FIELD_NAME_MAP.items()
                ]
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def license_records(request):
    return Response(
        {
            "success": True,
            "data": {
                "records": SERVICE.get_records(),
                "register_file": SERVICE.get_register_file(request),
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def license_file(request, relative_path: str):
    output_root = Path(settings.LICENSE_GENERATOR_OUTPUT_DIR).resolve()
    target = (output_root / relative_path).resolve()

    if not str(target).startswith(str(output_root)) or not target.exists():
        raise Http404("File not found")

    # Determine content type
    content_type = None
    if target.suffix.lower() in ['.jpg', '.jpeg']:
        content_type = 'image/jpeg'
    elif target.suffix.lower() == '.png':
        content_type = 'image/png'
    elif target.suffix.lower() == '.pdf':
        content_type = 'application/pdf'
    elif target.suffix.lower() == '.xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    # Determine if file should be downloaded
    as_attachment = request.query_params.get("download") == "1" or target.suffix.lower() == '.xlsx'
    
    return FileResponse(
        open(target, "rb"),
        content_type=content_type,
        as_attachment=as_attachment,
        filename=target.name,
    )


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_license_file(request, relative_path: str):
    """Delete a license file or directory."""
    output_root = Path(settings.LICENSE_GENERATOR_OUTPUT_DIR).resolve()
    target = (output_root / relative_path).resolve()

    # Security check: ensure the path is within the output directory
    if not str(target).startswith(str(output_root)):
        return Response(
            {"success": False, "error": "Invalid path"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if target.is_file():
            target.unlink()
            return Response(
                {"success": True, "message": f"File {relative_path} deleted successfully"}
            )
        elif target.is_dir():
            import shutil
            shutil.rmtree(target)
            return Response(
                {"success": True, "message": f"Directory {relative_path} deleted successfully"}
            )
        else:
            return Response(
                {"success": False, "error": "File or directory not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
    except Exception as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
