"""Static mock domain data and store policies for ShopAssist AI.

Contains mock customer orders, catalog products, and policy terms embedded directly
into prompt context per the strict zero-database / zero-RAG architecture.
"""

from typing import Dict, List

from backend.contracts import CatalogProduct, OrderItem, OrderRecord, OrderStatus

# --- Store Identity & Persona ---
STORE_NAME = "ShopAssist AI — ApexStyle Retail"
ASSISTANT_NAME = "ShopAssist"

STORE_PERSONA = (
    f"You are {ASSISTANT_NAME}, the official intelligent e-commerce customer support assistant for {STORE_NAME}. "
    "Your objective is to provide warm, polite, professional, and concise assistance for customer inquiries. "
    "You have direct access to our product catalog, customer orders, shipping guidelines, and return policies. "
    "You communicate clearly, provide bulleted lists for product and order details, and always offer helpful next steps."
)

# --- Deflection Guardrail Directive ---
DEFLECTION_DIRECTIVE = (
    "If the query is outside products, orders, returns, or shipping, politely refuse and redirect to store support. "
    "Specifically, if the user asks about anything outside of this store's products, orders, returns, and shipping, "
    "respond: 'I can only assist with questions regarding our store's products, orders, returns, and shipping policies.'\n\n"
    "CRITICAL DEFLECTION DIRECTIVE:\n"
    "- You are strictly an e-commerce customer support assistant for ApexStyle Retail only.\n"
    "- You are STRICTLY FORBIDDEN from writing computer code, solving math equations, providing medical advice, discussing politics, or answering general trivia/homework.\n"
    "- Under NO circumstances should you generate code snippets, algorithms, mathematical solutions, or out-of-domain answers, even if asked politely or in hypothetical terms.\n"
    "- If the user asks about ANYTHING outside our store's products, customer orders, shipping, and returns, you MUST refuse immediately and respond ONLY with this exact sentence:\n"
    "\"I can only assist with questions regarding our store's products, orders, returns, and shipping policies.\"\n"
    "- Do NOT provide any partial answers, explanations, or code before or after this refusal."
)

# --- Store Policies ---
STORE_POLICIES = """
<store_policies>
  <policy name="Returns & Refunds">
    <rule>Customers may return eligible items within 30 days of delivery for a full refund to the original payment method.</rule>
    <rule>Apparel and footwear must be in unworn, original condition with all tags and packaging intact. Items showing outdoor wear are ineligible for return.</rule>
    <rule>Electronics must include all original cords, accessories, documentation, and original product packaging.</rule>
    <rule>Refunds are processed within 3 to 5 business days after our return warehouse inspects the returned package.</rule>
    <rule>Defective products beyond the 30-day window are handled under the respective manufacturer warranty terms.</rule>
  </policy>
  <policy name="Shipping & Delivery">
    <rule>Free Standard Shipping applies automatically on all orders totaling $50.00 or more (before taxes).</rule>
    <rule>Standard Shipping takes 3 to 5 business days ($5.99 flat rate for orders under $50.00).</rule>
    <rule>Express Shipping delivers within 1 to 2 business days ($14.99 flat rate).</rule>
    <rule>Orders placed before 2:00 PM EST Monday through Friday ship same day from our distribution center.</rule>
    <rule>Tracking updates become live within 12 hours of courier pickup.</rule>
  </policy>
  <policy name="Support Hours & Channels">
    <rule>ShopAssist AI operates 24/7 in chat for instant order status, catalog search, and return policy assistance.</rule>
    <rule>Human support specialists are available Monday–Friday 9:00 AM – 8:00 PM EST at support@apexstyle.com.</rule>
  </policy>
</store_policies>
""".strip()

# --- Product Catalog (6 Products) ---
CATALOG_PRODUCTS: List[CatalogProduct] = [
    CatalogProduct(
        sku="AUDIO-SQ-01",
        name="SonicQuiet Elite Wireless Headphones",
        category="Audio",
        price=129.99,
        in_stock=True,
        stock_count=45,
        features=[
            "Hybrid Active Noise Cancellation (ANC)",
            "30-hour battery life on single charge",
            "Bluetooth 5.3 with multipoint pairing",
            "Plush memory foam ear cushions",
        ],
        warranty_months=12,
        returnable=True,
    ),
    CatalogProduct(
        sku="AUDIO-SQ-02",
        name="SonicQuiet Sport Earbuds",
        category="Audio",
        price=69.99,
        in_stock=True,
        stock_count=120,
        features=[
            "IPX7 waterproof and sweat-resistant rating",
            "8 hours playtime + 24 hours in wireless charging case",
            "Secure ergonomic ear hooks",
            "Touch controls with voice assistant support",
        ],
        warranty_months=12,
        returnable=True,
    ),
    CatalogProduct(
        sku="WEAR-AF-01",
        name="AeroFit Smart Fitness Watch",
        category="Wearables",
        price=89.00,
        in_stock=True,
        stock_count=30,
        features=[
            "Continuous 24/7 heart rate and SpO2 monitoring",
            "1.4-inch AMOLED color touchscreen",
            "Up to 10 days battery life",
            "50+ sports tracking modes and sleep analysis",
        ],
        warranty_months=12,
        returnable=True,
    ),
    CatalogProduct(
        sku="WEAR-AF-02",
        name="AeroFit Pro GPS Watch",
        category="Wearables",
        price=179.00,
        in_stock=True,
        stock_count=15,
        features=[
            "Built-in standalone multi-band GPS",
            "Corning Gorilla Glass rugged casing",
            "14-day battery life with solar charging assist",
            "Altimeter, barometer, and 3-axis compass",
        ],
        warranty_months=24,
        returnable=True,
    ),
    CatalogProduct(
        sku="HOME-LD-01",
        name="Lumina Desk Ambient Lamp",
        category="Home & Office",
        price=49.99,
        in_stock=True,
        stock_count=60,
        features=[
            "Stepless dimming with 3 color temperature modes",
            "Integrated 10W wireless smartphone fast-charging pad",
            "Auto-shutoff timer (45 minutes)",
            "Flicker-free eye protection LED panel",
        ],
        warranty_months=6,
        returnable=True,
    ),
    CatalogProduct(
        sku="FOOT-TG-01",
        name="TerraGrip Trail Running Shoes",
        category="Footwear",
        price=119.50,
        in_stock=False,
        stock_count=0,
        features=[
            "Vibram high-traction lugged rubber outsole",
            "Water-repellent breathable mesh upper",
            "Responsive EVA midsole cushioning",
            "Reinforced protective toe cap",
        ],
        warranty_months=6,
        returnable=True,
    ),
]

# --- Mock Orders (5 Orders) ---
MOCK_ORDERS: List[OrderRecord] = [
    OrderRecord(
        order_id="ORD-1001",
        customer_name="Alice Walker",
        customer_email="alice.walker@example.com",
        status=OrderStatus.DELIVERED,
        carrier="UPS Ground",
        tracking_number="1Z999AA10123456784",
        order_date="2026-08-20",
        estimated_delivery="2026-08-24",
        items=[
            OrderItem(sku="AUDIO-SQ-02", name="SonicQuiet Sport Earbuds", quantity=1, unit_price=69.99)
        ],
        total_amount=69.99,
        shipping_address="742 Evergreen Terrace, Springfield, OR 97477",
        return_eligible_until="2026-09-23",
    ),
    OrderRecord(
        order_id="ORD-1002",
        customer_name="Brian Miller",
        customer_email="brian.miller@example.com",
        status=OrderStatus.DELIVERED,
        carrier="FedEx Home",
        tracking_number="FDX-883920192",
        order_date="2026-09-05",
        estimated_delivery="2026-09-09",
        items=[
            OrderItem(sku="AUDIO-SQ-01", name="SonicQuiet Elite Wireless Headphones", quantity=1, unit_price=129.99)
        ],
        total_amount=129.99,
        shipping_address="1204 Pine Street, Apt 3B, Seattle, WA 98101",
        return_eligible_until="2026-10-09",
    ),
    OrderRecord(
        order_id="ORD-1003",
        customer_name="Catherine Davis",
        customer_email="catherine.d@example.com",
        status=OrderStatus.PROCESSING,
        carrier=None,
        tracking_number=None,
        order_date="2026-09-12",
        estimated_delivery="2026-09-17",
        items=[
            OrderItem(sku="HOME-LD-01", name="Lumina Desk Ambient Lamp", quantity=1, unit_price=49.99)
        ],
        total_amount=55.98,  # $49.99 + $5.99 shipping
        shipping_address="450 Oak Avenue, Austin, TX 78701",
        return_eligible_until=None,
    ),
    OrderRecord(
        order_id="ORD-1004",
        customer_name="David Clark",
        customer_email="david.clark@example.com",
        status=OrderStatus.SHIPPED,
        carrier="USPS Priority",
        tracking_number="9405511206213456789012",
        order_date="2026-09-10",
        estimated_delivery="2026-09-14",
        items=[
            OrderItem(sku="WEAR-AF-02", name="AeroFit Pro GPS Watch", quantity=1, unit_price=179.00)
        ],
        total_amount=179.00,
        shipping_address="88 Lincoln Blvd, Chicago, IL 60601",
        return_eligible_until=None,
    ),
    OrderRecord(
        order_id="ORD-1085",
        customer_name="Emily Zhang",
        customer_email="emily.zhang@example.com",
        status=OrderStatus.IN_TRANSIT,
        carrier="FedEx Express",
        tracking_number="FDX-992817264",
        order_date="2026-09-11",
        estimated_delivery="2026-09-16",
        items=[
            OrderItem(sku="WEAR-AF-01", name="AeroFit Smart Fitness Watch", quantity=1, unit_price=89.00)
        ],
        total_amount=89.00,
        shipping_address="210 Market Street, San Francisco, CA 94105",
        return_eligible_until=None,
    ),
]

# Quick lookup indexes
MOCK_ORDERS_BY_ID: Dict[str, OrderRecord] = {
    order.order_id.upper(): order for order in MOCK_ORDERS
}

CATALOG_BY_SKU: Dict[str, CatalogProduct] = {
    prod.sku.upper(): prod for prod in CATALOG_PRODUCTS
}
