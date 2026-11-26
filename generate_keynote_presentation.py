import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    # 16:9 widescreen dimensions (13.333 x 7.5 inches)
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Color Palette - Professional Tech / Apple Keynote Style
    DARK_BG = RGBColor(15, 23, 42)        # Slate 900
    WHITE = RGBColor(255, 255, 255)
    LIGHT_BG = RGBColor(248, 250, 252)    # Slate 50
    CARD_BG = RGBColor(255, 255, 255)
    BORDER_COLOR = RGBColor(226, 232, 240)
    PRIMARY_BLUE = RGBColor(37, 99, 235)  # Indigo/Blue
    ACCENT_CYAN = RGBColor(14, 165, 233)  # Sky Blue
    TEXT_DARK = RGBColor(15, 23, 42)
    TEXT_MUTED = RGBColor(100, 116, 139)  # Slate 500
    SUCCESS_GREEN = RGBColor(16, 185, 129)
    ALERT_AMBER = RGBColor(245, 158, 11)
    CARD_HEADER_BG = RGBColor(241, 245, 249)

    def add_header(slide, title_text, category_text="INT253 COLLEGE PROJECT PRESENTATION"):
        # Category pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.5), Inches(0.35))
        tf = cat_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = category_text.upper()
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_BLUE

        # Slide Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.8), Inches(11.5), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=BORDER_COLOR):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg_color
        if border_color:
            shape.line.color.rgb = border_color
            shape.line.width = Pt(1)
        else:
            shape.line.fill.background()
        return shape

    # ==========================================
    # SLIDE 1: TITLE SLIDE (Dark Keynote Theme)
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG
    bg.line.fill.background()

    # Title content
    tb = slide.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(4.0))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "COLLEGE CAPSTONE PROJECT | COURSE CODE: INT253"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_CYAN
    p0.space_after = Pt(16)

    p1 = tf.add_paragraph()
    p1.text = "SmartStock Pro"
    p1.font.size = Pt(46)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_after = Pt(8)

    p2 = tf.add_paragraph()
    p2.text = "Intelligent Inventory Management & Point of Sale (POS) Billing System"
    p2.font.size = Pt(22)
    p2.font.color.rgb = RGBColor(203, 213, 225)
    p2.space_after = Pt(36)

    p3 = tf.add_paragraph()
    p3.text = "Developed with Django 4.2 • WebRTC Webcam Barcode Scanner • Real-time Multi-Branch POS & Expiry Tracking"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(148, 163, 184)
    p3.space_after = Pt(20)

    p4 = tf.add_paragraph()
    p4.text = "Presented by: Student / Developer  |  Academic Term 2026"
    p4.font.size = Pt(14)
    p4.font.bold = True
    p4.font.color.rgb = WHITE

    # ==========================================
    # SLIDE 2: PROJECT ABSTRACT & PROBLEM STATEMENT
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Project Abstract & Problem Statement", "Introduction & Motivation")

    # Card 1: Traditional Retail Challenges
    add_card(slide, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Traditional Kirana & Retail Bottlenecks"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = RGBColor(225, 29, 72)
    p.space_after = Pt(14)

    challenges = [
        "Manual Pen-and-Paper Stock Registers: Prone to human errors, lost receipts, and severe data discrepancies.",
        "Uncontrolled Expiry & Spoilage: Perishable food and medicines expire unnoticed on shelves, leading to dead stock and financial loss.",
        "Costly Hardware Dependencies: Small retailers cannot afford expensive proprietary handheld barcode terminals.",
        "Stockouts & Missed Sales: Cashiers have no live stock threshold warnings when items drop below safety limits.",
        "Fragmented Store Outlets: Store owners cannot monitor branch revenues, stock transfers, or cashier audits remotely."
    ]
    for ch in challenges:
        p = tf.add_paragraph()
        p.text = "• " + ch
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

    # Card 2: SmartStock Pro Proposed Solution
    add_card(slide, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0), bg_color=RGBColor(240, 253, 250), border_color=SUCCESS_GREEN)
    tb = slide.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "The SmartStock Pro Solution"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.space_after = Pt(14)

    solutions = [
        "Zero-Cost Laptop Webcam Barcode Reader: WebRTC and canvas decoding with supermarket checkout audio beeps.",
        "Dynamic Expiry Date Lifecycle: Smart toggle for perishable vs non-perishable goods with 30-day and expired dashboard warning alerts.",
        "High-Speed Interactive POS Terminal: Sub-second live cart calculation, barcode search, and thermal receipt generator.",
        "Smart Multi-Mode Payment: Automated tendered & change calculator for Cash, plus zero-overhead Card, UPI QR, and Khata Credit support.",
        "Enterprise RBAC & Multi-Store Scaling: Strict Website Owner, Store Manager, and POS Cashier permission boundaries."
    ]
    for sol in solutions:
        p = tf.add_paragraph()
        p.text = "✓ " + sol
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

    # ==========================================
    # SLIDE 3: SYSTEM ARCHITECTURE & TECH STACK
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "System Architecture & Engineering Stack", "Technology & Design")

    tech_cards = [
        ("Backend Framework", "Django 4.2 (Python 3.9)", PRIMARY_BLUE, [
            "Model-View-Template (MVT) Pattern",
            "Atomic database transactions (@transaction.atomic)",
            "Robust ORM with select_related & prefetch_related",
            "Built-in CSRF, XSS, and SQL-injection protection"
        ]),
        ("Frontend & UI / UX", "Bootstrap 5 & Vanilla ES6+", ACCENT_CYAN, [
            "Responsive, mobile-friendly Indian retail theme",
            "Chart.js interactive revenue trajectory charts",
            "Bootstrap 5 modals for quick category/supplier creation",
            "Custom CSS design system with currency localization"
        ]),
        ("WebRTC Barcode Vision", "html5-qrcode & Web Audio", SUCCESS_GREEN, [
            "In-browser camera stream via navigator.mediaDevices",
            "Local canvas frame computer-vision barcode decoding",
            "1760Hz retail scanner sine-wave beep synthesizer",
            "Offline static asset bundling with zero network lag"
        ]),
        ("Database & Audit Logs", "Relational DB & Audit Trail", RGBColor(147, 51, 234), [
            "Normalized schema with strict foreign key integrity",
            "StockMovement audit trail tracking every single unit",
            "Indexed SKU & Barcode lookups for sub-10ms queries",
            "Automated SQLite/PostgreSQL migration lifecycle"
        ])
    ]

    for i, (title, subtitle, color, points) in enumerate(tech_cards):
        left = Inches(0.8 + i * 2.95)
        top = Inches(1.8)
        width = Inches(2.8)
        height = Inches(5.0)

        add_card(slide, left, top, width, height)

        # Header bar in card
        hbar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, Inches(0.85))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = color
        hbar.line.fill.background()

        tb = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.08), width - Inches(0.3), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p1 = tf.add_paragraph()
        p1.text = subtitle
        p1.font.size = Pt(10)
        p1.font.color.rgb = RGBColor(241, 245, 249)

        # Points
        tb_pts = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(1.0), width - Inches(0.3), Inches(3.8))
        tf_pts = tb_pts.text_frame
        tf_pts.word_wrap = True
        for idx, pt in enumerate(points):
            p = tf_pts.paragraphs[0] if idx == 0 else tf_pts.add_paragraph()
            p.text = "• " + pt
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(8)

    # ==========================================
    # SLIDE 4: ROLE-BASED ACCESS CONTROL (RBAC)
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Role-Based Access Control & User Permissions", "Security & Multi-Tenant Management")

    roles = [
        ("Website Owner (Super Admin)", RGBColor(225, 29, 72), "Full Root Governance", [
            "Exclusive access to User Management & Role Creation",
            "Granular permission checkboxes (POS, Inventory, Reports)",
            "One-click user active/inactive toggle switch",
            "Protected from cashier distraction — dedicated governance portal"
        ]),
        ("Store Admin & Manager", PRIMARY_BLUE, "Operational Control", [
            "Multi-store branch management (Add/Edit store outlets)",
            "Catalog administration: Products, Categories, Suppliers",
            "Inbound purchase orders with automatic stock increment",
            "Financial Profit & Loss reports and valuation analytics"
        ]),
        ("POS Cashier", SUCCESS_GREEN, "Counter & Billing Speed", [
            "Dedicated high-speed POS billing terminal (/pos/)",
            "Webcam barcode scanning and instant cart checkout",
            "Receipt generation and thermal print dispatch",
            "Restricted from deleting records or altering historical financial reports"
        ])
    ]

    for i, (role_name, color, role_desc, bullets) in enumerate(roles):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.8)
        height = Inches(5.0)

        add_card(slide, left, top, width, height)

        # Header badge
        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.2), top + Inches(0.25), width - Inches(0.4), Inches(0.8))
        badge.fill.solid()
        badge.fill.fore_color.rgb = color
        badge.line.fill.background()

        tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.28), width - Inches(0.5), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = role_name
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = role_desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = RGBColor(241, 245, 249)

        # Bullets
        tb_pts = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(1.2), width - Inches(0.5), Inches(3.6))
        tf_pts = tb_pts.text_frame
        tf_pts.word_wrap = True
        for idx, bullet in enumerate(bullets):
            p = tf_pts.paragraphs[0] if idx == 0 else tf_pts.add_paragraph()
            p.text = "✓ " + bullet
            p.font.size = Pt(11.5)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(10)

    # ==========================================
    # SLIDE 5: WEBCAM BARCODE SCANNER INNOVATION
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Zero-Hardware Laptop Webcam Barcode Scanner", "Key Innovation & Hardware Elimination")

    # Left Box: How It Works & Viva Talking Points
    add_card(slide, Inches(0.8), Inches(1.8), Inches(6.8), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(6.2), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Dual-Scanning Architecture"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(12)

    tech_details = [
        "WebRTC Media Capture: Connects to built-in laptop camera or external USB webcam via standard browser getUserMedia API.",
        "Client-Side Machine Vision (html5-qrcode): Decodes 1D retail barcodes (UPC-A, EAN-13, Code-128) and 2D QR codes in real time with zero server compute overhead.",
        "Synthesized Retail Audio Beep: Uses Web Audio API oscillator (1760 Hz high-pitch sine wave) to reproduce authentic supermarket counter audio feedback without external audio files.",
        "Automatic Cart & Stock Synchronizer: Decoded barcode triggers instant API lookup, checks stock threshold, unshifts item into POS state, and computes GST and grand total.",
        "HID Wedge Scanner Backward-Compatibility: Handheld laser scanners plug-and-play into search box using automatic Enter key listener."
    ]
    for td in tech_details:
        p = tf.add_paragraph()
        p.text = "• " + td
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(7)

    # Right Box: Key Viva Highlights & Flow
    add_card(slide, Inches(7.9), Inches(1.8), Inches(4.6), Inches(5.0), bg_color=RGBColor(240, 249, 255), border_color=ACCENT_CYAN)
    tb = slide.shapes.add_textbox(Inches(8.1), Inches(2.0), Inches(4.2), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Scanner Workflow"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(14)

    steps = [
        ("Step 1: Open Camera", "Click 'Camera Scan' in POS toolbar or Product Form"),
        ("Step 2: Stream & Capture", "Webcam renders live viewfinder with targeting box"),
        ("Step 3: CV Detection", "Canvas decodes barcode string in ~80 milliseconds"),
        ("Step 4: Retail Beep", "Web Audio API oscillator fires 1760Hz audio confirmation"),
        ("Step 5: Auto-Cart Add", "Item added to cart, quantity checked, totals refreshed"),
        ("Continuous Mode", "Toggle switch allows multiple items scanned consecutively")
    ]
    for s_title, s_desc in steps:
        p = tf.add_paragraph()
        p.text = s_title + ": "
        p.font.size = Pt(11.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK
        p_desc = tf.add_paragraph()
        p_desc.text = s_desc
        p_desc.font.size = Pt(10.5)
        p_desc.font.color.rgb = TEXT_MUTED
        p_desc.space_after = Pt(4)

    # ==========================================
    # SLIDE 6: PERISHABLE GOODS & EXPIRY DATE TRACKING
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Perishable Goods Lifecycle & Expiry Alerts", "Inventory Freshness & Wastage Prevention")

    # 3 Column Cards
    expiry_features = [
        ("Selective Expiry Toggle", PRIMARY_BLUE, "Flexible Product Classification", [
            "Toggled OFF for non-perishables (hardware, stationery, electronics) to avoid clutter.",
            "Toggled ON for perishables (dairy, medicines, packaged snacks, cosmetics).",
            "Smooth animated date-picker reveal upon enabling switch.",
            "Form validation guarantees mandatory date selection only when toggled ON."
        ]),
        ("Front Dashboard Alert Banner", RGBColor(225, 29, 72), "Real-Time Executive Warnings", [
            "Prominent alert banner placed at top of front dashboard.",
            "Red Danger Banner for products that are ALREADY EXPIRED.",
            "Amber Warning Banner for goods expiring within 30 days.",
            "Instant filter buttons: 'View Expired' and 'View Near Expiry'."
        ]),
        ("Freshness Watchlist Table", ALERT_AMBER, "Actionable Inventory Oversight", [
            "Dedicated dashboard table showing remaining shelf life in days.",
            "Color-coded badges: Expired (Red), Critical ≤7d (Orange), Warning ≤30d (Yellow).",
            "One-click action buttons to edit product or execute damaged stock write-off.",
            "Integrated into stock adjustment audit logs for accounting compliance."
        ])
    ]

    for i, (title, color, subtitle, points) in enumerate(expiry_features):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.8)
        height = Inches(5.0)

        add_card(slide, left, top, width, height)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.2), top + Inches(0.25), width - Inches(0.4), Inches(0.8))
        badge.fill.solid()
        badge.fill.fore_color.rgb = color
        badge.line.fill.background()

        tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.28), width - Inches(0.5), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = RGBColor(241, 245, 249)

        tb_pts = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(1.2), width - Inches(0.5), Inches(3.6))
        tf_pts = tb_pts.text_frame
        tf_pts.word_wrap = True
        for idx, pt in enumerate(points):
            p = tf_pts.paragraphs[0] if idx == 0 else tf_pts.add_paragraph()
            p.text = "• " + pt
            p.font.size = Pt(11.5)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(10)

    # ==========================================
    # SLIDE 7: POINT OF SALE (POS) & SMART BILLING
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Point of Sale (POS) Billing & Smart Payments", "Retail Counter Experience")

    # Card 1: POS Capabilities
    add_card(slide, Inches(0.8), Inches(1.8), Inches(5.6), Inches(5.0))
    tb = slide.shapes.add_textbox(Inches(1.1), Inches(2.0), Inches(5.0), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "POS Billing Terminal Features"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(12)

    pos_features = [
        "Real-Time Cart Ledger: Live subtotal, customizable GST tax rates (0%, 5%, 12%, 18%, 28%), and instant discount reductions.",
        "Stock Depletion Guard: Prevents cashiers from adding items exceeding physical shelf stock; alerts immediately.",
        "Quick Add Modals: Create new categories, suppliers, or customers on-the-fly without navigating away from the billing screen.",
        "Printable Thermal Receipts: Formatted printable receipts with store header, itemized quantities, GST breakdown, and transaction timestamps.",
        "Keyboard Hotkeys: Press F2 to instantly focus search/scanner, Enter to add, Esc to close."
    ]
    for pf in pos_features:
        p = tf.add_paragraph()
        p.text = "• " + pf
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_DARK
        p.space_after = Pt(8)

    # Card 2: Smart Payment Modes
    add_card(slide, Inches(6.8), Inches(1.8), Inches(5.7), Inches(5.0), bg_color=RGBColor(248, 250, 252), border_color=PRIMARY_BLUE)
    tb = slide.shapes.add_textbox(Inches(7.1), Inches(2.0), Inches(5.1), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Multi-Mode Payment Intelligence"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_BLUE
    p.space_after = Pt(12)

    pay_modes = [
        ("💵 Cash Transactions", "Displays 'Rs. Tendered' and live 'Change Due' calculator. Validates partial tenders with credit prompt."),
        ("💳 Card Payment (Swipe/POS)", "Hides cash tendered inputs. Automatically binds exact invoice grand total without change math."),
        ("📱 UPI QR Scan (GPay / PhonePe / Paytm)", "Hides cash inputs. Shows dedicated QR confirmation badge and logs exact digital payment in ledger."),
        ("📋 Customer Credit / Khata (Due Bill)", "Hides cash inputs. Records zero initial cash and logs outstanding ledger balance against customer profile.")
    ]
    for pm_title, pm_desc in pay_modes:
        p = tf.add_paragraph()
        p.text = pm_title
        p.font.size = Pt(12.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_DARK
        p_sub = tf.add_paragraph()
        p_sub.text = pm_desc
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED
        p_sub.space_after = Pt(6)

    # ==========================================
    # SLIDE 8: DATABASE SCHEMA & DATA INTEGRITY
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Relational Database Schema & Architecture", "Data Model & Business Logic")

    models_data = [
        ("Product", [
            "name, sku (unique), barcode (indexed)",
            "category_id, supplier_id",
            "cost_price, selling_price, current_stock",
            "min_stock_level, has_expiry, expiry_date"
        ]),
        ("Sale & SaleItem", [
            "invoice_number (unique), sale_date",
            "customer_id, payment_method, cashier",
            "subtotal, tax_amount, grand_total",
            "items: product_id, quantity, unit_price"
        ]),
        ("Purchase Order", [
            "invoice_number (unique), purchase_date",
            "supplier_id, store_id, total_amount",
            "status: received / pending / cancelled",
            "Auto-increments stock on status='received'"
        ]),
        ("StockMovement Audit", [
            "product_id, movement_type, quantity",
            "previous_stock, new_stock, created_at",
            "reference_number (INV/PO/AUDIT)",
            "Immutable ledger for full forensic audit"
        ])
    ]

    for i, (m_title, fields) in enumerate(models_data):
        col = i % 2
        row = i // 2
        left = Inches(0.8 + col * 5.95)
        top = Inches(1.8 + row * 2.6)
        width = Inches(5.8)
        height = Inches(2.4)

        add_card(slide, left, top, width, height)

        tb = slide.shapes.add_textbox(left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = "Entity: " + m_title
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_BLUE
        p.space_after = Pt(6)

        for fld in fields:
            p_f = tf.add_paragraph()
            p_f.text = "• " + fld
            p_f.font.size = Pt(11)
            p_f.font.color.rgb = TEXT_DARK
            p_f.space_after = Pt(2)

    # ==========================================
    # SLIDE 9: VERIFICATION, TESTING & PERFORMANCE
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    add_header(slide, "Verification, Testing & System Robustness", "Software Quality Assurance")

    test_cards = [
        ("Automated Unit Test Suite", "13 Passing Test Cases", SUCCESS_GREEN, [
            "13/13 Django unit tests passing cleanly in test suite",
            "Testing stock deduction, threshold alerts, and overselling prevention",
            "Testing transaction rollback when stock is insufficient",
            "Testing expiry date validation and near-expiry filter queries"
        ]),
        ("ACID Compliance & Atomicity", "Zero Data Corruption", PRIMARY_BLUE, [
            "@transaction.atomic wrappers on POS and PO processes",
            "Database row locking (select_for_update) prevents race conditions",
            "Stock adjustments and cash ledgers commit or rollback as one",
            "Enforced foreign key constraints (SET_NULL / PROTECT)"
        ]),
        ("Cross-Browser & Device Readiness", "Universal Responsiveness", RGBColor(147, 51, 234), [
            "Tested on macOS Safari, Google Chrome, and Mozilla Firefox",
            "WebRTC camera permission graceful error handling",
            "Web Audio API fallback across modern desktop/mobile browsers",
            "Offline static asset bundling guaranteeing presentation stability"
        ])
    ]

    for i, (title, subtitle, color, points) in enumerate(test_cards):
        left = Inches(0.8 + i * 3.95)
        top = Inches(1.8)
        width = Inches(3.8)
        height = Inches(5.0)

        add_card(slide, left, top, width, height)

        badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + Inches(0.2), top + Inches(0.25), width - Inches(0.4), Inches(0.8))
        badge.fill.solid()
        badge.fill.fore_color.rgb = color
        badge.line.fill.background()

        tb = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(0.28), width - Inches(0.5), Inches(0.75))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p2 = tf.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = RGBColor(241, 245, 249)

        tb_pts = slide.shapes.add_textbox(left + Inches(0.25), top + Inches(1.2), width - Inches(0.5), Inches(3.6))
        tf_pts = tb_pts.text_frame
        tf_pts.word_wrap = True
        for idx, pt in enumerate(points):
            p = tf_pts.paragraphs[0] if idx == 0 else tf_pts.add_paragraph()
            p.text = "✓ " + pt
            p.font.size = Pt(11.5)
            p.font.color.rgb = TEXT_DARK
            p.space_after = Pt(10)

    # ==========================================
    # SLIDE 10: FUTURE SCOPE & CONCLUSION
    # ==========================================
    slide = prs.slides.add_slide(blank_slide_layout)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = DARK_BG
    bg.line.fill.background()

    # Category
    tb_c = slide.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.3), Inches(0.4))
    tf_c = tb_c.text_frame
    p_c = tf_c.paragraphs[0]
    p_c.text = "PROJECT CONCLUSION & ROADMAP"
    p_c.font.size = Pt(12)
    p_c.font.bold = True
    p_c.font.color.rgb = ACCENT_CYAN

    # Title
    tb_t = slide.shapes.add_textbox(Inches(1.0), Inches(1.1), Inches(11.3), Inches(0.8))
    tf_t = tb_t.text_frame
    p_t = tf_t.paragraphs[0]
    p_t.text = "Future Enhancements & Summary"
    p_t.font.size = Pt(28)
    p_t.font.bold = True
    p_t.font.color.rgb = WHITE

    # Left Card: Roadmap
    add_card(slide, Inches(1.0), Inches(2.2), Inches(5.4), Inches(4.5), bg_color=RGBColor(30, 41, 59), border_color=RGBColor(51, 65, 85))
    tb_l = slide.shapes.add_textbox(Inches(1.2), Inches(2.4), Inches(5.0), Inches(4.1))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "Future Roadmap"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ACCENT_CYAN
    p.space_after = Pt(12)

    future_points = [
        "AI Demand Forecasting: Machine learning time-series models to predict seasonal sales and optimal reorder dates.",
        "Automated Supplier EDI / WhatsApp Notifications: Automatic dispatch of PO purchase orders to suppliers when stock hits critical threshold.",
        "Mobile Android / iOS PWA: Progressive Web App with smartphone camera scanning for mobile counter billing.",
        "Multi-Store Inter-Branch Stock Transfers: Transfer inventory between warehouse outlets with in-transit tracking."
    ]
    for pt in future_points:
        p = tf_l.add_paragraph()
        p.text = "→ " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_after = Pt(8)

    # Right Card: Conclusion
    add_card(slide, Inches(6.8), Inches(2.2), Inches(5.5), Inches(4.5), bg_color=RGBColor(30, 41, 59), border_color=PRIMARY_BLUE)
    tb_r = slide.shapes.add_textbox(Inches(7.0), Inches(2.4), Inches(5.1), Inches(4.1))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    p = tf_r.paragraphs[0]
    p.text = "Project Conclusion"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = SUCCESS_GREEN
    p.space_after = Pt(12)

    concl_points = [
        "Demonstrated a fully functional, production-ready inventory and POS system tailored for modern retail.",
        "Successfully eliminated hardware barcode dependencies by embedding WebRTC computer vision directly in the browser.",
        "Protected store profitability through automated perishable expiry tracking, low-stock alerts, and multi-mode payment handling.",
        "All software engineering milestones, unit testing, and architectural constraints met with 100% test pass rate."
    ]
    for pt in concl_points:
        p = tf_r.add_paragraph()
        p.text = "✓ " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_after = Pt(8)

    output_path = "/Users/yatharth/Desktop/untitled folder/SmartStock_Pro_INT253_Keynote_Presentation.pptx"
    prs.save(output_path)
    print(f"Presentation saved successfully to: {output_path}")

if __name__ == "__main__":
    create_presentation()
