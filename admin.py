from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from pathlib import Path

class LicenseAdminSite(admin.AdminSite):
    """Custom admin site that includes license file management."""
    
    def get_urls(self):
        from django.urls import include
        urls = super().get_urls()
        custom_urls = [
            path('license-files/', self.admin_view(self.license_files_view), name='license_files'),
            path('delete-license-folder/<path:file_or_folder_name>/', self.admin_view(self.delete_license_folder), name='delete_license_folder'),
        ]
        return custom_urls + urls
    
    def license_files_view(self, request):
        """Display license files and folders with delete options."""
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to access this page")
            return HttpResponseRedirect('/license-admin/')
        
        license_dir = Path(settings.LICENSE_GENERATOR_OUTPUT_DIR)
        
        if not license_dir.exists():
            messages.warning(request, "License directory does not exist")
            return render(request, 'admin/license_files.html', {
                'folders': [],
                'files': [],
                'title': 'License Files Management',
                'site_header': self.site_header,
                'site_title': self.site_title,
            })
        
        folders = []
        files = []
        
        # Get license register file
        register_file = license_dir / "license_register.xlsx"
        if register_file.exists():
            files.append({
                'name': register_file.name,
                'path': str(register_file.relative_to(license_dir)),
                'size': register_file.stat().st_size,
                'modified': register_file.stat().st_mtime,
                'type': 'register'
            })
        
        # Get license folders
        for item in license_dir.iterdir():
            if item.is_dir():
                files_in_folder = []
                for file_item in item.iterdir():
                    if file_item.is_file():
                        files_in_folder.append({
                            'name': file_item.name,
                            'path': str(file_item.relative_to(license_dir)),
                            'size': file_item.stat().st_size,
                            'modified': file_item.stat().st_mtime
                        })
                
                folders.append({
                    'name': item.name,
                    'path': str(item.relative_to(license_dir)),
                    'size': sum(f.stat().st_size for f in item.rglob('*') if f.is_file()),
                    'file_count': len([f for f in item.rglob('*') if f.is_file()]),
                    'modified': item.stat().st_mtime,
                    'files': files_in_folder
                })
        
        # Sort folders by modification time (newest first)
        folders.sort(key=lambda x: x['modified'], reverse=True)
        
        return render(request, 'admin/license_files.html', {
            'folders': folders,
            'files': files,
            'title': 'License Files Management',
            'site_header': self.site_header,
            'site_title': self.site_title,
        })

    def delete_license_folder(self, request, file_or_folder_name):
        """Delete a license file or folder."""
        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to delete files or folders")
            return HttpResponseRedirect('/license-admin/license-files/')
        
        license_dir = Path(settings.LICENSE_GENERATOR_OUTPUT_DIR)
        target_path = license_dir / file_or_folder_name
        
        if not target_path.exists():
            messages.error(request, f"File or folder '{file_or_folder_name}' does not exist")
            return HttpResponseRedirect('/license-admin/license-files/')
        
        try:
            if target_path.is_dir():
                import shutil
                shutil.rmtree(target_path)
                messages.success(request, f"Folder '{file_or_folder_name}' and all its contents have been deleted")
            elif target_path.is_file():
                target_path.unlink()
                messages.success(request, f"File '{file_or_folder_name}' has been deleted")
        except Exception as e:
            messages.error(request, f"Error deleting file or folder: {str(e)}")
        
        return HttpResponseRedirect('/license-admin/license-files/')

# Create a custom admin site instance
license_admin = LicenseAdminSite(name='license_admin')

# Register your models here.
