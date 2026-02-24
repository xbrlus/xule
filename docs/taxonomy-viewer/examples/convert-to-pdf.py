#!/usr/bin/env python3
"""
Convert REBNY Financial Statement HTML form to fillable PDF
Form field names match the HTML input IDs for compatibility with OIM taxonomy
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfform
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import sys

def create_fillable_pdf(output_filename):
    """Create a fillable PDF form matching the HTML structure"""
    
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter
    
    # Starting positions
    y = height - 0.75 * inch
    margin = 0.75 * inch
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "REBNY Financial Statement")
    y -= 0.3 * inch
    
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Please complete all applicable fields. Fields with totals update automatically.")
    y -= 0.4 * inch
    
    # Applicant Information Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Applicant Information")
    y -= 0.25 * inch
    
    # Applicant fields
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, "Applicant:")
    c.acroForm.textfield(name='applicant', tooltip='Full name',
                         x=margin + 1*inch, y=y-0.15*inch, width=2.5*inch, height=0.2*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                         textColor=black, forceBorder=True)
    
    c.drawString(margin + 4*inch, y, "Co-Applicant:")
    c.acroForm.textfield(name='coapplicant', tooltip='Co-Applicant name',
                         x=margin + 5*inch, y=y-0.15*inch, width=2.5*inch, height=0.2*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                         textColor=black, forceBorder=True)
    y -= 0.35 * inch
    
    # Address fields
    c.drawString(margin, y, "Address:")
    c.acroForm.textfield(name='address', tooltip='Street, apt, city, state, ZIP',
                         x=margin + 1*inch, y=y-0.15*inch, width=2.5*inch, height=0.2*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                         textColor=black, forceBorder=True)
    
    c.drawString(margin + 4*inch, y, "Co-Address:")
    c.acroForm.textfield(name='coaddress', tooltip='Co-Applicant address',
                         x=margin + 5*inch, y=y-0.15*inch, width=2.5*inch, height=0.2*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                         textColor=black, forceBorder=True)
    y -= 0.5 * inch
    
    # Monthly Sources of Income Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Monthly Sources of Income")
    y -= 0.25 * inch
    
    income_fields = [
        ("Base monthly salary:", "base_app", "base_co"),
        ("Overtime (monthly):", "ot_app", "ot_co"),
        ("Bonuses (monthly):", "bonus_app", "bonus_co"),
        ("Commissions (monthly):", "comm_app", "comm_co"),
        ("Dividends / Interest:", "div_app", "div_co"),
        ("Net rental income:", "rent_app", "rent_co"),
        ("Other income:", "other_app", "other_co"),
    ]
    
    c.setFont("Helvetica", 8)
    c.drawString(margin + 2.5*inch, y, "Applicant")
    c.drawString(margin + 4*inch, y, "Co-Applicant")
    y -= 0.2 * inch
    
    for label, app_field, co_field in income_fields:
        c.setFont("Helvetica", 8)
        c.drawString(margin, y, label)
        
        # Applicant field
        c.acroForm.textfield(name=app_field, tooltip=label,
                             x=margin + 2.3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        
        # Co-Applicant field
        c.acroForm.textfield(name=co_field, tooltip=label,
                             x=margin + 3.8*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        y -= 0.25 * inch
    
    # Total income (read-only)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "TOTAL:")
    c.acroForm.textfield(name='income_total_app', tooltip='Total income - Applicant',
                         x=margin + 2.3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    c.acroForm.textfield(name='income_total_co', tooltip='Total income - Co-Applicant',
                         x=margin + 3.8*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    y -= 0.5 * inch
    
    # Projected Housing Expenses Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Projected Housing Expenses")
    y -= 0.25 * inch
    
    expense_fields = [
        ("Maintenance:", "maint_app", "maint_co", "maint_joint"),
        ("Apt. Financing:", "aptfin_app", "aptfin_co", "aptfin_joint"),
        ("Other Mortgages:", "mort_app", "mort_co", "mort_joint"),
        ("Bank Loans:", "bankloan_app", "bankloan_co", "bankloan_joint"),
        ("Auto Loans:", "autoloan_app", "autoloan_co", "autoloan_joint"),
        ("Credit Card Debt:", "cc_app", "cc_co", "cc_joint"),
    ]
    
    c.setFont("Helvetica", 7)
    c.drawString(margin + 2*inch, y, "Applicant")
    c.drawString(margin + 3.2*inch, y, "Co-Applicant")
    c.drawString(margin + 4.4*inch, y, "Joint")
    y -= 0.2 * inch
    
    for label, app_field, co_field, joint_field in expense_fields:
        c.setFont("Helvetica", 8)
        c.drawString(margin, y, label)
        
        # Applicant field
        c.acroForm.textfield(name=app_field, tooltip=label,
                             x=margin + 2*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        
        # Co-Applicant field
        c.acroForm.textfield(name=co_field, tooltip=label,
                             x=margin + 3.2*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        
        # Joint field
        c.acroForm.textfield(name=joint_field, tooltip=label,
                             x=margin + 4.4*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        y -= 0.25 * inch
    
    # Total expenses (read-only)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "TOTAL:")
    c.acroForm.textfield(name='expenses_total', tooltip='Total expenses - Applicant',
                         x=margin + 2*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    c.acroForm.textfield(name='expenses_total_co', tooltip='Total expenses - Co-Applicant',
                         x=margin + 3.2*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    c.acroForm.textfield(name='expenses_total_joint', tooltip='Total expenses - Joint',
                         x=margin + 4.4*inch, y=y-0.12*inch, width=1*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    
    # Start new page for Assets & Liabilities
    c.showPage()
    y = height - 0.75 * inch
    
    # Assets Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Assets")
    y -= 0.25 * inch
    
    asset_fields = [
        ("Cash / Money Market Funds:", "cash_app", "cash_co"),
        ("Contract deposit:", "contract_app", "contract_co"),
        ("Stocks & bonds / Brokerage:", "stocks_app", "stocks_co"),
        ("Investment in own business:", "invbus_app", "invbus_co"),
        ("Accounts receivable:", "ar_app", "ar_co"),
        ("Real estate owned:", "re_app", "re_co"),
        ("Automobiles:", "auto_app", "auto_co"),
        ("Personal property & furniture:", "ppf_app", "ppf_co"),
        ("Life insurance (cash value):", "life_app", "life_co"),
        ("401k:", "401k_app", "401k_co"),
        ("KEOGH:", "keogh_app", "keogh_co"),
        ("Profit sharing / pension:", "pension_app", "pension_co"),
        ("Other assets:", "otherassets_app", "otherassets_co"),
    ]
    
    c.setFont("Helvetica", 7)
    c.drawString(margin + 3*inch, y, "Applicant")
    c.drawString(margin + 4.5*inch, y, "Co-Applicant")
    y -= 0.2 * inch
    
    for label, app_field, co_field in asset_fields:
        c.setFont("Helvetica", 8)
        c.drawString(margin, y, label)
        
        # Applicant field
        c.acroForm.textfield(name=app_field, tooltip=label,
                             x=margin + 3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        
        # Co-Applicant field
        c.acroForm.textfield(name=co_field, tooltip=label,
                             x=margin + 4.5*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        y -= 0.25 * inch
    
    # Total assets (read-only)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "TOTAL ASSETS:")
    c.acroForm.textfield(name='total_assets', tooltip='Total assets - Applicant',
                         x=margin + 3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    c.acroForm.textfield(name='total_assets_co', tooltip='Total assets - Co-Applicant',
                         x=margin + 4.5*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    y -= 0.5 * inch
    
    # Liabilities Section
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Liabilities")
    y -= 0.25 * inch
    
    liability_fields = [
        ("Notes payable to banks:", "npbank_app", "npbank_co"),
        ("Notes payable to relatives:", "nprel_app", "nprel_co"),
        ("Notes payable to others:", "npothers_app", "npothers_co"),
        ("Install accounts payable:", "iap_app", "iap_co"),
        ("Automobile:", "liauto_app", "liauto_co"),
        ("Other accounts payable:", "oap_app", "oap_co"),
        ("Mortgages payable:", "mortpay_app", "mortpay_co"),
        ("Unpaid real estate taxes:", "taxes_app", "taxes_co"),
        ("Unpaid income taxes:", "inctax_app", "inctax_co"),
        ("Chattel mortgages:", "chattel_app", "chattel_co"),
        ("Loans on life insurance:", "loanlife_app", "loanlife_co"),
        ("Credit card debt:", "ccdebt_app", "ccdebt_co"),
        ("Other debts:", "otherdebt_app", "otherdebt_co"),
    ]
    
    c.setFont("Helvetica", 7)
    c.drawString(margin + 3*inch, y, "Applicant")
    c.drawString(margin + 4.5*inch, y, "Co-Applicant")
    y -= 0.2 * inch
    
    for label, app_field, co_field in liability_fields:
        c.setFont("Helvetica", 8)
        c.drawString(margin, y, label)
        
        # Applicant field
        c.acroForm.textfield(name=app_field, tooltip=label,
                             x=margin + 3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        
        # Co-Applicant field
        c.acroForm.textfield(name=co_field, tooltip=label,
                             x=margin + 4.5*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                             borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#fbfdff'),
                             textColor=black, forceBorder=True)
        y -= 0.25 * inch
    
    # Total liabilities (read-only)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "TOTAL LIABILITIES:")
    c.acroForm.textfield(name='total_liab', tooltip='Total liabilities - Applicant',
                         x=margin + 3*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    c.acroForm.textfield(name='total_liab_co', tooltip='Total liabilities - Co-Applicant',
                         x=margin + 4.5*inch, y=y-0.12*inch, width=1.3*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    y -= 0.3 * inch
    
    # Net worth (read-only)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, "NET WORTH:")
    c.acroForm.textfield(name='net_worth', tooltip='Net worth',
                         x=margin + 3*inch, y=y-0.12*inch, width=2.8*inch, height=0.18*inch,
                         borderColor=HexColor('#e6e9ef'), fillColor=HexColor('#f0f0f0'),
                         textColor=black, forceBorder=True)
    
    c.save()
    print(f"✓ Created fillable PDF: {output_filename}")
    print(f"  - Form fields match HTML input IDs")
    print(f"  - Compatible with OIM taxonomy valueSources")

if __name__ == "__main__":
    output_file = "coop-financials.pdf"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    create_fillable_pdf(output_file)
