import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class CertificateGenerator:
    def __init__(self):
        self.template_path = getattr(settings, 'CERTIFICATE_TEMPLATE_PATH', None)
        self.font_path = getattr(settings, 'CERTIFICATE_FONT_PATH', None)
        self.qr_size = 150
        
    def generate_certificate(self, name, license_id, verification_url):
        """
        Generate a certificate PDF with name, QR code, and license details.
        
        Args:
            name (str): Recipient name
            license_id (str): License UUID
            verification_url (str): Verification URL
            
        Returns:
            io.BytesIO: Generated certificate PDF
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF canvas
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Set background
            c.setFillColor(HexColor("#f8f9fa"))
            c.rect(0, 0, width, height, fill=1, stroke=0)
            
            # Add border
            c.setStrokeColor(HexColor("#dee2e6"))
            c.setLineWidth(2)
            c.rect(20, 20, width - 40, height - 40, fill=0, stroke=1)
            
            # Add title
            c.setFillColor(HexColor("#212529"))
            c.setFont("Helvetica-Bold", 24)
            title_text = "Certificate of Completion"
            title_width = c.stringWidth(title_text, "Helvetica-Bold", 24)
            c.drawString((width - title_width) / 2, height - 80, title_text)
            
            # Add recipient name
            c.setFillColor(HexColor("#495057"))
            c.setFont("Helvetica", 18)
            name_text = f"This is to certify that"
            c.drawString((width - c.stringWidth(name_text, "Helvetica", 18)) / 2, height - 130, name_text)
            
            c.setFont("Helvetica-Bold", 20)
            name_width = c.stringWidth(name, "Helvetica-Bold", 20)
            c.drawString((width - name_width) / 2, height - 160, name)
            
            c.setFont("Helvetica", 16)
            completed_text = "has successfully completed the course"
            completed_width = c.stringWidth(completed_text, "Helvetica", 16)
            c.drawString((width - completed_width) / 2, height - 190, completed_text)
            
            # Add license ID
            c.setFillColor(HexColor("#6c757d"))
            c.setFont("Helvetica", 12)
            license_text = f"License ID: {license_id}"
            c.drawString(50, height - 250, license_text)
            
            # Add date
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            date_text = f"Issued on: {current_date}"
            c.drawString(50, height - 280, date_text)
            
            # Add QR code to PDF
            qr_img = self._generate_qr_code(verification_url)
            
            # Save QR code to temporary file
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_qr_file:
                qr_img.save(temp_qr_file, format='PNG')
                temp_qr_file.seek(0)
                
                # Add QR code to PDF
                qr_x = width - 170
                qr_y = height - 320
                c.drawImage(temp_qr_file.name, qr_x, qr_y, width=120, height=120)
                
                # Clean up temp file
                os.unlink(temp_qr_file.name)
            
            # Add verification text
            c.setFillColor(HexColor("#6c757d"))
            c.setFont("Helvetica", 10)
            verify_text = "Scan QR code to verify certificate"
            verify_width = c.stringWidth(verify_text, "Helvetica", 10)
            c.drawString((width - verify_width) / 2, height - 350, verify_text)
            
            # Add verification URL
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor("#adb5bd"))
            url_text = verification_url
            # Wrap long URLs
            if len(url_text) > 50:
                url_parts = [url_text[i:i+40] for i in range(0, len(url_text), 40)]
                for i, part in enumerate(url_parts):
                    c.drawString(50, height - 380 - (i * 15), part)
            else:
                c.drawString(50, height - 380, url_text)
            
            # Add signature line
            c.setStrokeColor(HexColor("#495057"))
            c.setLineWidth(1)
            c.line(width - 200, 100, width - 50, 100)
            
            # Add signature text
            c.setFillColor(HexColor("#6c757d"))
            c.setFont("Helvetica-Oblique", 12)
            c.drawString(width - 180, 80, "Authorized Signature")
            
            # Save PDF
            c.save()
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            raise Exception(f"Certificate generation failed: {str(e)}")
    
    def _create_default_template(self):
        """Create a default certificate template."""
        width, height = 1200, 800
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        border_color = '#2c3e50'
        draw.rectangle([20, 20, width-20, height-20], outline=border_color, width=5)
        draw.rectangle([30, 30, width-30, height-30], outline=border_color, width=2)
        
        # Add title
        try:
            title_font = ImageFont.truetype(self.font_path, 60) if self.font_path else ImageFont.load_default()
        except:
            title_font = ImageFont.load_default()
        
        title = "Certificate of Achievement"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2
        draw.text((title_x, 100), title, fill='#2c3e50', font=title_font)
        
        # Add subtitle
        try:
            subtitle_font = ImageFont.truetype(self.font_path, 30) if self.font_path else ImageFont.load_default()
        except:
            subtitle_font = ImageFont.load_default()
        
        subtitle = "This is to certify that"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2
        draw.text((subtitle_x, 250), subtitle, fill='#7f8c8d', font=subtitle_font)
        
        return img
    
    def _add_name(self, draw, img, name):
        """Add recipient name to certificate."""
        width, height = img.size
        
        try:
            name_font = ImageFont.truetype(self.font_path, 48) if self.font_path else ImageFont.load_default()
        except:
            name_font = ImageFont.load_default()
        
        # Calculate text position for centering
        text_bbox = draw.textbbox((0, 0), name, font=name_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (width - text_width) // 2
        text_y = 320  # Position for name
        
        # Draw name
        draw.text((text_x, text_y), name, fill='#2c3e50', font=name_font)
    
    def _add_license_details(self, draw, img, license_id):
        """Add license ID and creation date to certificate."""
        width, height = img.size
        
        try:
            detail_font = ImageFont.truetype(self.font_path, 20) if self.font_path else ImageFont.load_default()
        except:
            detail_font = ImageFont.load_default()
        
        # Add license ID
        license_text = f"License ID: {license_id}"
        draw.text((50, height - 100), license_text, fill='#7f8c8d', font=detail_font)
        
        # Add date
        from datetime import datetime
        date_text = f"Issued on: {datetime.now().strftime('%B %d, %Y')}"
        draw.text((50, height - 70), date_text, fill='#7f8c8d', font=detail_font)
    
    def _generate_qr_code(self, url):
        """Generate QR code for verification URL."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))
        
        return qr_img
    
    def _add_qr_code(self, template_img, qr_img):
        """Add QR code to certificate."""
        width, height = template_img.size
        
        # Position QR code in bottom right
        qr_x = width - self.qr_size - 50
        qr_y = height - self.qr_size - 50
        
        # Paste QR code
        template_img.paste(qr_img, (qr_x, qr_y))
        
        # Add "Scan to verify" text below QR code
        draw = ImageDraw.Draw(template_img)
        try:
            qr_font = ImageFont.truetype(self.font_path, 16) if self.font_path else ImageFont.load_default()
        except:
            qr_font = ImageFont.load_default()
        
        verify_text = "Scan to verify"
        text_bbox = draw.textbbox((0, 0), verify_text, font=qr_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = qr_x + (self.qr_size - text_width) // 2
        text_y = qr_y + self.qr_size + 5
        
        draw.text((text_x, text_y), verify_text, fill='#7f8c8d', font=qr_font)
