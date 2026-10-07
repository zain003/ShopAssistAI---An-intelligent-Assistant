"""Corpus generator: creates 60 realistic domain markdown documents for ShopAssist AI.

Categorized into:
- data/documents/policies/ (10 docs)
- data/documents/shipping/ (10 docs)
- data/documents/products/ (10 docs)
- data/documents/warranties/ (10 docs)
- data/documents/troubleshooting/ (10 docs)
- data/documents/payments/ (10 docs)
"""

import os
from pathlib import Path

BASE_DIR = Path("data/documents")

DOCUMENTS = {
    # ---------------- POLICIES (10) ----------------
    "policies/return_policy.md": """# ShopAssist Standard Return Policy

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-001  

## Overview
ShopAssist offers a 30-day return window for eligible products starting from the delivery timestamp confirmed by the carrier. We believe in customer satisfaction and make returns simple, fair, and transparent.

## Eligibility Criteria
To qualify for a full refund:
- Items must be returned within 30 days of the verified delivery date.
- Products must be in original condition, including all original packaging, cords, manuals, and accessories.
- Electronic products must have personal account locks removed and factory reset performed prior to shipment.
- Consumable items (screen protectors, cleaning wipes, earbud tips) must be unopened.

## Return Shipping and Restocking Fees
- Defective, damaged, or incorrect items receive a free prepaid return shipping label.
- Customer remorse returns (e.g. changed mind, accidental order) incur a flat $5.99 return shipping deduction.
- Opened consumer electronics returned in non-defective condition are subject to a 10% restocking fee if packaging is torn or accessories are missing.

## Processing Timelines
Once received at our fulfillment center, items are inspected within 2 to 3 business days. Approved refunds are credited to the original payment method within 3 to 5 business days.
""",

    "policies/exchange_policy.md": """# Product Exchange and Replacement Policy

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-002  

## Overview
If you received the wrong item, want a different color or size, or your product is defective, our exchange policy provides seamless replacements without requiring you to wait for a full return cycle.

## Direct Exchange Process
- Direct exchanges are permitted within 30 days of delivery.
- You can initiate an exchange via your customer account dashboard or by contacting live support.
- We offer Instant Exchange for verified loyalty members: your replacement item ships immediately before we receive your return.

## Price Differentials
- If the new item has the same retail price, no additional payment is required.
- If the replacement item is more expensive, you will be prompted to pay the difference prior to dispatch.
- If the replacement is less expensive, the remaining balance is refunded to your original payment method.

## Return Window for Exchanged Units
You must drop off the original item with the carrier within 14 days of initiating the exchange. Failure to return the original item within 14 days will result in an automatic charge for the retail value of the replacement unit.
""",

    "policies/refund_methods.md": """# Refund Methods and Store Credit Policy

**Category:** Policies  
**Last Updated:** February 2026  
**Document ID:** POL-003  

## Overview
This document explains the payment methods eligible for refunds, processing timelines, and bonus store credit incentives.

## Refund Options
When initiating a return, customers can choose between two refund options:
1. **Original Payment Method:** Refund is credited back to the credit card, debit card, or PayPal account used at checkout.
2. **ShopAssist Store Credit:** Receive immediate store credit with an additional 5% bonus credit (e.g. a $100 return yields $105 store credit).

## Bank Processing Timelines
- Credit and Debit Cards: 3 to 5 business days depending on issuing financial institution.
- PayPal and Digital Wallets: 24 to 48 hours.
- Klarna / Afterpay installments: Remaining installments canceled immediately; paid portions refunded in 5 to 7 business days.
- ShopAssist Gift Cards: Recredited instantaneously upon return inspection.

## Non-Refundable Charges
Original expedited shipping fees (Overnight, 2-Day Express) and gift wrapping fees are non-refundable unless the return is due to carrier negligence or a merchant error.
""",

    "policies/order_cancellation.md": """# Order Cancellation Guidelines

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-004  

## Overview
ShopAssist automated fulfillment centers begin processing orders rapidly to ensure fast delivery. This policy outlines when and how orders can be canceled.

## Immediate Cancellation Window
- Orders may be self-canceled online within 30 minutes of order placement.
- Navigate to Order History > Order Details > Cancel Order.
- Once an order status progresses to "Processing" or "Shipped", automated cancellation is no longer possible.

## Post-Processing Cancellation Requests
If the 30-minute window has elapsed:
- Our warehouse dispatch robots assign packing slots immediately; customer support cannot intercept picked parcels.
- Customers may refuse delivery at the door when the carrier arrives, causing the package to return to sender automatically.
- Alternatively, customers may accept delivery and generate a return label via the standard return portal.

## Refund for Canceled Orders
Self-canceled orders trigger an immediate authorization reversal. Credit card holds are released within 24 to 72 hours without any deduction.
""",

    "policies/price_match_guarantee.md": """# Price Match Guarantee Policy

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-005  

## Overview
We guarantee competitive pricing. If you find a lower price on an identical in-stock item from a qualified major retailer, we will match the price.

## Price Match Window
- Pre-purchase: Submit competitor URL during checkout or via live chat.
- Post-purchase: Submit price match request within 14 days of purchase date.

## Qualified Retailers and Conditions
- Qualified competitors include: Amazon (sold/shipped by Amazon directly), Best Buy, Target, and Walmart.
- The item must be identical in model number, color, condition, and warranty duration.
- The item must be currently in stock and available for immediate shipping at the competitor.

## Exclusions
Price matching does not apply to:
- Marketplace third-party sellers, auction sites, or refurbished listings.
- Black Friday, Cyber Monday, liquidation, clearance, or flash sale pricing.
- Bundle discounts, mail-in rebates, or pricing typographical errors.
""",

    "policies/international_returns.md": """# International Return Policy

**Category:** Policies  
**Last Updated:** February 2026  
**Document ID:** POL-006  

## Overview
ShopAssist ships globally to over 45 countries. International returns follow specialized customs and freight clearance procedures.

## Return Window and Conditions
- International orders have an extended 45-day return window from the delivery date.
- Products must be unopened or lightly inspected in pristine condition with all accessories.
- Personal data must be cleared from electronic devices.

## Shipping and Customs Charges
- Customers are responsible for international return postage unless the item arrived damaged or incorrect.
- We recommend using a trackable courier (DHL, FedEx International, UPS).
- Import duties, value-added taxes (VAT), and carrier brokerage fees paid at import cannot be refunded by ShopAssist; customers must submit Form C285 to local customs authorities for duty recovery.

## Return Processing Location
All international returns must be addressed to our Global Hub in Louisville, Kentucky, USA. Please write your RMA number prominently on the outer carton.
""",

    "policies/damaged_defective_goods.md": """# Damaged and Defective Goods Policy (DOA)

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-007  

## Overview
We stand behind the quality of our catalog. If an item arrives broken, cracked, defective, or dead on arrival (DOA), we replace it promptly at zero cost.

## 48-Hour Reporting Protocol
- Customers must notify ShopAssist within 48 hours of carrier-confirmed delivery for damaged parcels.
- Photographs of the outer packaging, shipping label, and damaged product are required.
- Do not discard the shipping carton or packaging materials until the carrier inspection is complete.

## Dead on Arrival (DOA) Electronics
- If an electronic device does not power on or exhibit fatal hardware fault out of the box, it is classified as DOA.
- ShopAssist immediately ships an advance replacement with complimentary Priority Express shipping.
- A prepaid return label is provided inside the replacement carton for returning the defective unit.

## Failure to Report Within 48 Hours
Damage reported after 48 hours is handled under standard warranty terms rather than instant carrier freight damage claims.
""",

    "policies/gift_returns.md": """# Gift Return and Exchange Policy

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-008  

## Overview
Received a gift ordered from ShopAssist? You can return or exchange the item discreetly without notifying the original gift purchaser.

## Initiating a Gift Return
- Access our Gift Return Portal at shopassist.ai/gift-returns.
- Enter the 12-digit Gift Order Number found on the packing slip (starts with "GFT-" or standard "ORD-").
- If no packing slip is available, our support team can locate the order using the recipient's shipping address.

## Refund Method for Gifts
- Gift returns are issued exclusively as ShopAssist Store Credit or digital gift cards.
- Refunds cannot be issued in cash or redirected to a third-party bank account.
- The original purchaser will NOT be notified of the return or exchange.

## Gift Exchange Options
Recipients may select an alternative item directly in the portal. If the new item value exceeds the gift value, the recipient pays the remaining balance during checkout.
""",

    "policies/privacy_and_data_policy.md": """# Customer Privacy and Data Protection Policy

**Category:** Policies  
**Last Updated:** February 2026  
**Document ID:** POL-009  

## Overview
ShopAssist is dedicated to protecting customer data privacy. We comply with GDPR, CCPA, and strict PCI-DSS payment industry standards.

## Data We Collect
- Contact Information: Full name, delivery address, email address, phone number.
- Order History: Products purchased, payment method tokens (we never store raw credit card numbers).
- Assistant Conversations: Anonymized chat queries used strictly for quality assurance and model alignment.

## Third-Party Data Sharing
- We do NOT sell, rent, or trade customer data to advertising brokers.
- Data is shared strictly with operational partners: shipping carriers (USPS, FedEx, UPS) and payment processors (Stripe, PayPal).

## Customer Data Rights
- Right to Access: You may download a full export of your personal data from your profile settings.
- Right to Deletion: Request account and data deletion by emailing privacy@shopassist.ai. Data deletion is executed within 30 days.
""",

    "policies/terms_of_service.md": """# Customer Terms of Service and Order Acceptance

**Category:** Policies  
**Last Updated:** January 2026  
**Document ID:** POL-010  

## Overview
These Terms of Service govern all purchases, interactions, and services provided across ShopAssist digital platforms.

## Order Acceptance and Cancellation Rights
- Receipt of an order confirmation email does not signify our final acceptance of your order.
- We reserve the right to cancel or limit order quantities if fraud is suspected, inventory pricing is erroneous, or stock is depleted.
- If an order is canceled post-payment, an immediate 100% refund is initiated.

## User Conduct
- Users agree not to misuse promotional coupon codes, deploy unauthorized scraping bots, or engage in abusive interactions with customer support staff or AI assistants.

## Limitation of Liability
ShopAssist is not liable for indirect, incidental, or consequential damages resulting from delayed carrier transit, hardware misuse, or third-party compatibility issues beyond the product's purchase price.
""",

    # ---------------- SHIPPING (10) ----------------
    "shipping/standard_shipping.md": """# Standard Shipping Guidelines

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-001  

## Overview
Standard Shipping is our reliable, economical delivery option available across all 50 US states and territories.

## Rates and Thresholds
- Orders totaling $50.00 or more (pre-tax, post-discount) qualify for Free Standard Shipping.
- Orders under $50.00 carry a flat shipping fee of $4.99.
- Continental US transit time is 3 to 5 business days. Alaska, Hawaii, and Puerto Rico average 5 to 7 business days.

## Carrier Partners
Standard parcels are dispatched via USPS Ground Advantage, FedEx Ground Economy, or UPS SurePost. The specific carrier is automatically selected based on destination density.

## Tracking and Notification
Tracking numbers are generated as soon as the shipping label is printed at the warehouse. Tracking scans activate within 12 to 24 hours of carrier pickup.
""",

    "shipping/express_shipping.md": """# Express 2-Day Shipping Service

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-002  

## Overview
When you need your items quickly, Express 2-Day Shipping provides guaranteed delivery within two business days.

## Pricing and Cutoff Times
- Flat rate: $12.99 per order regardless of item quantity.
- Daily Cutoff Time: 2:00 PM EST Monday through Friday.
- Orders placed before 2:00 PM EST ship same-day and arrive on the second business day.
- Orders placed after 2:00 PM EST ship the next business day.

## Delivery Scope
- Available to all continental US street addresses.
- Express 2-Day Shipping is not available for P.O. Boxes, APO/FPO military bases, or US territories.
- Saturday delivery is included in major metropolitan areas at no extra cost.

## Money-Back Guarantee
If your package fails to arrive within two business days due to carrier delay (excluding severe weather delays), we refund the entire $12.99 express shipping fee.
""",

    "shipping/overnight_delivery.md": """# Next-Day Priority Overnight Shipping

**Category:** Shipping  
**Last Updated:** February 2026  
**Document ID:** SHP-003  

## Overview
Priority Overnight provides next-business-day delivery for urgent orders.

## Rates and Schedule
- Flat fee: $24.99 per order.
- Cutoff Time: 1:00 PM EST Monday through Thursday.
- Orders placed on Friday before 1:00 PM EST arrive Monday. For Saturday delivery, a $15.00 weekend surcharge applies.

## Eligible Items
- In-stock consumer electronics, accessories, chargers, and small apparel items are eligible.
- Hazmat items (such as stand-alone lithium batteries over 100Wh) or heavy goods over 30 lbs are ineligible for air freight.

## Signature Requirements
All Priority Overnight parcels with a retail value of $150.00 or higher require a direct adult signature upon delivery.
""",

    "shipping/international_shipping.md": """# International Shipping and Customs (DDP)

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-004  

## Overview
ShopAssist delivers worldwide to over 45 countries using DHL Express and FedEx International Priority.

## Delivered Duty Paid (DDP)
- All international orders are shipped DDP (Delivered Duty Paid).
- Applicable customs duties, import tariffs, and local VAT/GST are calculated and collected during checkout.
- No surprise fees or carrier brokerage bills upon door delivery.

## Delivery Timeframes
- Canada & Mexico: 3 to 6 business days.
- United Kingdom & European Union: 4 to 7 business days.
- Australia, Japan, South Korea: 5 to 9 business days.
- Rest of World: 7 to 14 business days.

## Restrictions
Lithium battery shipments are limited to a maximum of 2 devices per consignment in accordance with IATA dangerous goods regulations.
""",

    "shipping/order_tracking.md": """# Live Order Tracking and Status Explanations

**Category:** Shipping  
**Last Updated:** February 2026  
**Document ID:** SHP-005  

## Overview
Every ShopAssist parcel features end-to-end milestone tracking so you can monitor your package from packing to doorstep.

## Tracking Status Definitions
- **Processing:** Order verified and allocated to inventory warehouse queue.
- **Preparing Shipment:** Items picked, boxed, and shipping label printed.
- **In Transit:** Carrier has scanned package at local distribution center and parcel is moving across hubs.
- **Out for Delivery:** Package is on the local delivery truck for delivery today between 9:00 AM and 8:00 PM.
- **Delivered:** Parcel scanned as deposited at mailbox, front porch, or concierge.

## How to Check Status
- Visit shopassist.ai/track and input your Order ID (e.g. `ORD-1001`) and billing zip code.
- Alternatively, ask the ShopAssist AI assistant directly in the chat with your order number.
""",

    "shipping/po_box_and_apo.md": """# P.O. Box and Military APO/FPO Delivery

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-006  

## Overview
ShopAssist proudly serves US military service personnel and customers utilizing Post Office boxes.

## Guidelines for P.O. Boxes
- P.O. Box shipments must be sent exclusively via Standard Shipping (USPS).
- FedEx and UPS private couriers cannot deliver to USPS P.O. Boxes.
- Maximum package weight for P.O. Box delivery is 20 lbs.

## Military APO / FPO / DPO Addresses
- Use the recipient's full military rank, unit, and box number.
- City must be designated as APO, FPO, or DPO.
- State code must be AA, AE, or AP.
- Country must always be selected as "United States" regardless of foreign stationing.
- Transit times range between 10 to 21 business days due to military postal transport.
""",

    "shipping/signature_confirmation.md": """# Signature Confirmation and Delivery Security

**Category:** Shipping  
**Last Updated:** February 2026  
**Document ID:** SHP-007  

## Overview
To prevent porch piracy and ensure secure handoff of high-value goods, ShopAssist implements signature confirmation protocols.

## Signature Rules by Order Value
- **Under $150.00:** Left in a secure location without signature.
- **$150.00 to $299.99:** Indirect Signature (neighbor or door tag release permitted).
- **$300.00 and above:** Direct Signature Required (recipient at delivery address must sign in person).

## Missed Delivery
If no one is available to sign:
- The carrier leaves a door tag notice.
- The carrier reattempts delivery up to three consecutive business days.
- After the third attempt, the parcel is held at the nearest carrier depot for 5 business days before returning to our warehouse.
""",

    "shipping/shipping_delays_and_weather.md": """# Severe Weather and Operational Delay Policy

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-008  

## Overview
While 98.4% of orders arrive on schedule, severe weather events and carrier network disruptions can occasionally delay delivery.

## Weather Exceptions
- Carriers (USPS, FedEx, UPS) declare weather exceptions for hurricanes, blizzards, floods, and wildfire air-quality grounding.
- During declared force majeure events, guaranteed transit time commitments are temporarily suspended by the carrier.

## Proactive Customer Notification
- If your parcel is delayed more than 48 hours beyond its estimated arrival date, our automated logistics monitor sends an email notification with an updated ETA.
- If an expedited shipping order (Overnight or 2-Day) is delayed due to our warehouse handling rather than weather, your shipping fee is refunded automatically.
""",

    "shipping/lost_or_stolen_packages.md": """# Lost, Missing, or Stolen Package Policy

**Category:** Shipping  
**Last Updated:** February 2026  
**Document ID:** SHP-009  

## Overview
Steps to take if your tracking shows "Delivered" but you cannot locate your package, or if the shipment has stopped tracking in transit.

## Package Marked "Delivered" But Not Found
1. Verify the delivery address in your order confirmation email.
2. Check surrounding areas: porches, side gates, garages, parcel lockers, and with neighbors.
3. Wait 24 hours: Carriers occasionally mark parcels delivered prematurely while still in the neighborhood.
4. If still missing after 24 hours, contact ShopAssist within 7 days.

## Investigation and Resolution
- We immediately launch a GPS geotag coordinate trace with the carrier.
- If the carrier confirmed misdelivery or porch theft, ShopAssist provides either a free replacement shipment or a 100% refund.
""",

    "shipping/split_shipments.md": """# Split Shipments and Multi-Warehouse Dispatch

**Category:** Shipping  
**Last Updated:** January 2026  
**Document ID:** SHP-010  

## Overview
ShopAssist operates fulfillment hubs across California, Ohio, and Texas. Multi-item orders may be divided into split shipments.

## Zero Additional Cost
- When an order is split into multiple packages, you are NEVER charged extra shipping fees.
- Your initial checkout shipping charge covers all parcels.

## Tracking Split Shipments
- Each package receives its own distinct tracking number.
- All tracking numbers appear under the same Order ID on your tracking portal.
- Items may arrive on different days depending on originating warehouse distance.
""",

    # ---------------- PRODUCTS (10) ----------------
    "products/soundflow_pro_headphones.md": """# SoundFlow Pro Wireless ANC Headphones User Guide

**Category:** Products  
**SKU:** SF-PRO-01  
**Price:** $129.99  
**Document ID:** PRD-001  

## Overview
The SoundFlow Pro Wireless Headphones deliver premium acoustic performance with Hybrid Active Noise Cancellation (up to 38dB noise suppression) and 40mm custom bio-cellulose drivers.

## Technical Specifications
- Bluetooth Version: 5.3 with multipoint pairing (connects 2 devices simultaneously).
- Supported Codecs: LDAC, AAC, SBC.
- Battery Life: 40 hours with ANC enabled; 60 hours with ANC disabled.
- Fast Charging: 10 minutes of USB-C charge yields 5 hours of playback.
- Weight: 250 grams with memory foam protein leather earcups.

## Package Contents
- SoundFlow Pro Headphones, hard travel case, 1.2m 3.5mm audio cable, USB-C braided charging cable, airplane audio adapter, quick start guide.
""",

    "products/soundflow_air_earbuds.md": """# SoundFlow Air True Wireless Earbuds User Manual

**Category:** Products  
**SKU:** SF-AIR-02  
**Price:** $79.99  
**Document ID:** PRD-002  

## Overview
Ultra-compact true wireless earbuds designed for active lifestyles, workouts, and crystal-clear calls.

## Key Features
- Water Resistance: IPX7 certified (submersible up to 1 meter for 30 minutes; sweatproof).
- Driver: 10mm graphene composite diaphragm.
- Microphones: 4-mic beamforming array with Environmental Noise Cancellation (ENC) for speech clarity.
- Battery: 8 hours per charge on earbuds; 24 additional hours in wireless charging case (32 hours total).
- Controls: Capacitive touch surfaces on both earbuds (tap for pause, double tap track skip, triple tap voice assistant).

## Tips for Best Fit
Includes 3 sizes of ergonomic liquid silicone tips (S, M, L). Choosing the airtight seal maximizes bass response and passive noise isolation.
""",

    "products/pulse_watch_active.md": """# Pulse Watch Active Smartwatch Specifications

**Category:** Products  
**SKU:** PW-ACT-03  
**Price:** $149.99  
**Document ID:** PRD-003  

## Overview
A comprehensive health and wellness smartwatch featuring a vibrant 1.43-inch AMOLED display and 24/7 biometric tracking.

## Health and Fitness Features
- Continuous Heart Rate, SpO2 Blood Oxygen, Stress Level, and Sleep Stage monitoring (REM, Light, Deep).
- 110+ sports modes including swimming, outdoor running, cycling, and yoga.
- Built-in multi-system GNSS (GPS, GLONASS, Galileo) for phone-free outdoor tracking.
- Water Resistance: 5 ATM (water resistant up to 50 meters; suitable for swimming).

## Battery and Compatibility
- Battery Capacity: 420mAh (up to 7 days normal usage, 14 days in battery saver mode).
- OS Compatibility: iOS 12.0+ and Android 8.0+ via the Companion App.
""",

    "products/pulse_band_fitness.md": """# Pulse Band Fitness Tracker Manual

**Category:** Products  
**SKU:** PB-FIT-04  
**Price:** $49.99  
**Document ID:** PRD-004  

## Overview
A lightweight, discreet fitness tracker for continuous daily activity and sleep monitoring.

## Features
- Screen: 1.1-inch color AMOLED touch display.
- Weight: Ultra-light 22 grams including silicone band.
- Activity Tracking: Steps, distance, calorie burn, active minutes, and sedentary reminders.
- Battery Life: Exceptional 14-day battery life on a single 90-minute magnetic charge.
- Water Resistance: 50-meter water resistance.

## Connectivity
Bluetooth 5.0 Low Energy. Synchronizes automatically with Apple Health and Google Fit via the free companion app.
""",

    "products/swift_charge_65w_gan.md": """# SwiftCharge 65W GaN Wall Charger Specifications

**Category:** Products  
**SKU:** SC-GAN-05  
**Price:** $39.99  
**Document ID:** PRD-005  

## Overview
Powered by Gallium Nitride (GaN III) semiconductors, the SwiftCharge 65W is 45% smaller than traditional silicon chargers while generating less heat.

## Port Configuration & Power Distribution
- USB-C1 Output: Up to 65W (5V/3A, 9V/3A, 12V/3A, 15V/3A, 20V/3.25A).
- USB-C2 Output: Up to 30W.
- USB-A Output: Up to 18W Quick Charge 3.0.
- Dual Port Usage (C1 + C2): 45W + 20W (powers laptop and phone simultaneously).
- Triple Port Usage (C1 + C2 + A): 45W + 10W + 10W.

## Safety Protections
Over-voltage, over-current, short-circuit, and smart thermal throttling at 85°C.
""",

    "products/swift_charge_powerbank_20k.md": """# SwiftCharge 20,000mAh Power Bank User Guide

**Category:** Products  
**SKU:** SC-PB-06  
**Price:** $59.99  
**Document ID:** PRD-006  

## Overview
High-capacity airline-approved portable power bank with bidirectional USB-C fast charging.

## Specifications
- Battery Capacity: 20,000mAh / 74Wh (fully TSA compliant for carry-on luggage).
- Maximum Output: 45W Power Delivery via USB-C port.
- Inputs: USB-C 45W fast recharge (fully recharges in 2.5 hours).
- Display: Integrated real-time LED percentage display.
- Pass-Through Charging: Charge external devices while the power bank recharges itself.

## Compatibility
Charges smartphones (iPhone 15 up to 4.5 times, Samsung S24 up to 4 times), tablets, Steam Deck, and USB-C ultrabooks.
""",

    "products/aura_rgb_mechanical_keyboard.md": """# Aura Pro RGB Mechanical Keyboard Guide

**Category:** Products  
**SKU:** AK-RGB-07  
**Price:** $99.99  
**Document ID:** PRD-007  

## Overview
A 75% compact mechanical gaming and productivity keyboard built with hot-swappable switch sockets and sound-dampening silicone foam.

## Features
- Switches: Pre-lubed Custom Linear Red Switches (45g actuation force).
- Sockets: 5-pin hot-swappable PCB (compatible with Cherry, Gateron, Kailh switches).
- Keycaps: Double-shot PBT keycaps with shine-through OEM profile.
- Connectivity: Tri-mode (Bluetooth 5.1, 2.4GHz wireless dongle, USB-C detachable cable).
- Lighting: 16.8 million color RGB with 18 onboard animations.
""",

    "products/aerogrip_vertical_mouse.md": """# AeroGrip Ergonomic Vertical Mouse Manual

**Category:** Products  
**SKU:** AG-VM-08  
**Price:** $44.99  
**Document ID:** PRD-008  

## Overview
Scientifically contoured vertical mouse designed by ergonomists to relieve wrist pronation and carpal tunnel strain.

## Specifications
- Angle: 57-degree natural handshake angle.
- Optical Sensor: Adjustable 800 / 1200 / 1600 / 2400 DPI with dedicated top button.
- Buttons: 6 silent click buttons including thumb forward/backward navigation keys.
- Battery: Rechargeable 500mAh lithium battery via USB-C (lasts up to 90 days per charge).
- Connection: Dual wireless (Bluetooth 5.0 + 2.4GHz USB Nano Receiver).
""",

    "products/echobeam_mini_projector.md": """# EchoBeam Smart Mini Projector User Guide

**Category:** Products  
**SKU:** EB-PRJ-09  
**Price:** $189.99  
**Document ID:** PRD-009  

## Overview
A portable DLP smart home cinema projector delivering crisp 1080p native resolution and integrated streaming apps.

## Key Specifications
- Brightness: 400 ANSI Lumens.
- Projection Size: 40 inches to 120 inches (projection distance 1.1m to 3.2m).
- Resolution: Native 1920x1080 (supports 4K decoding).
- Keystone: Automatic ±40 degree vertical keystone correction with auto-focus sensor.
- Audio: Built-in dual 5W stereo speakers with Dolby Audio decoding.
- Inputs: HDMI 2.0, USB 2.0, 3.5mm Aux audio, Wi-Fi 6, Bluetooth 5.2.
""",

    "products/titanshield_travel_backpack.md": """# TitanShield 35L Tech Travel Backpack

**Category:** Products  
**SKU:** TS-BP-10  
**Price:** $89.99  
**Document ID:** PRD-010  

## Overview
The ultimate backpack for remote workers, travelers, and tech commuters, engineered with ballistic weather-resistant fabrics.

## Structure and Compartments
- Volume: 35 Liters expandable to 42 Liters via wrap-around zipper.
- Laptop Protection: Suspended EVA foam compartment fits up to 16-inch laptops.
- Security: Integrated TSA-approved 3-digit combination lock on main zippers.
- Charging: External USB-A and USB-C pass-through charging ports connected to internal battery pocket.
- Fabric: 900D water-repellent Cordura with taped YKK water-resistant zippers.
""",

    # ---------------- WARRANTIES (10) ----------------
    "warranties/standard_hardware_warranty.md": """# Standard 1-Year Limited Hardware Warranty

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-001  

## Coverage Scope
ShopAssist provides a 1-year (12-month) limited manufacturer warranty on all new hardware products purchased directly from our store.

## What is Covered
- Mechanical failures resulting from defective materials or factory assembly.
- Component breakdown under normal, intended household or office usage.
- Faulty internal power supplies, ports, motherboards, or sensors.

## What is Excluded
- Normal cosmetic wear and tear (scratches, dents, fading).
- Accidental drops, liquid spills, fire damage, or theft.
- Damage caused by unauthorized third-party repairs or modifications.
- Natural disasters and power surge damage.
""",

    "warranties/extended_care_plan.md": """# ShopAssist Extended Care Protection Plans

**Category:** Warranties  
**Last Updated:** February 2026  
**Document ID:** WAR-002  

## Overview
Extended Care plans extend your standard 1-year hardware warranty to 2 or 3 years of comprehensive coverage with VIP benefits.

## Plan Options & Pricing
- 2-Year Extended Care: $19.99 (items under $100) / $34.99 (items over $100).
- 3-Year Extended Care: $29.99 (items under $100) / $49.99 (items over $100).

## Plan Benefits
- Zero deductible on all mechanical and electrical claims.
- Free two-way shipping for all repairs and replacements.
- Transferable coverage: if you gift or resell the item, coverage remains valid.
- 30-day money-back guarantee on plan purchase if no claims have been filed.
""",

    "warranties/accidental_damage_protection.md": """# Accidental Damage Protection Policy

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-003  

## Overview
Add-on accidental damage coverage for portable gear (headphones, earbuds, smartwatches, and chargers).

## Incident Coverage
- Cracked screens from accidental drops.
- Water and liquid spills (including pool or beverage exposure).
- Broken hinges, split headbands, or snapped ports.

## Claim Limits
- Up to 2 accidental incident claims per 12-month policy period.
- A nominal $15.00 service fee applies per accidental replacement claim.
- If the item cannot be repaired, a brand-new replacement unit is provided.
""",

    "warranties/battery_health_warranty.md": """# Battery Health and Degradation Warranty

**Category:** Warranties  
**Last Updated:** February 2026  
**Document ID:** WAR-004  

## Overview
Lithium-ion batteries naturally lose capacity over charge cycles. This policy clarifies the threshold between normal aging and defective batteries.

## Warranty Threshold
- If your rechargeable battery capacity drops below 80% of its original design capacity within the 1-year warranty window, it is considered defective.
- Customers receive a complimentary battery replacement or product replacement.

## How Capacity is Tested
- Our diagnostics center performs a calibrated charge/discharge cycle test.
- Batteries exhibiting swelling, thermal inflation, or leakage are replaced immediately under high-priority safety recall protocols.
""",

    "warranties/warranty_claim_procedure.md": """# Step-by-Step Warranty Claim and RMA Procedure

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-005  

## Overview
Filing a warranty claim is straightforward through our automated Return Merchandise Authorization (RMA) system.

## Filing Steps
1. Navigate to shopassist.ai/warranty and sign in.
2. Select your registered device and describe the defect symptoms.
3. Attach a 10-second video or photo showing the hardware issue.
4. Our automated system generates an RMA number within 2 hours.
5. Print the prepaid shipping label and attach it to your parcel.

## Turnaround Time
Once your device arrives at our repair facility:
- Standard repair or replacement turnaround is 3 to 5 business days.
- Express replacements for Extended Care holders dispatch within 24 hours of RMA approval.
""",

    "warranties/refurbished_product_warranty.md": """# Certified Refurbished 90-Day Warranty

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-006  

## Overview
ShopAssist Certified Refurbished products undergo rigorous 40-point hardware inspections, thorough cleaning, and factory repackaging.

## Coverage Terms
- All Certified Refurbished products include a 90-day limited warranty.
- Covers complete hardware defects, screen failures, and audio faults.
- Includes original OEM or certified compatible charging cables and accessories.

## Option to Extend
Customers may purchase an Extended Care 1-Year add-on plan for Certified Refurbished goods within 14 days of purchase.
""",

    "warranties/out_of_warranty_repairs.md": """# Out-of-Warranty Repair Service and Diagnostics

**Category:** Warranties  
**Last Updated:** February 2026  
**Document ID:** WAR-007  

## Overview
If your warranty has expired or your device suffered damage not covered under standard terms, we offer affordable factory repair services.

## Flat Diagnostic Fee
- Standard diagnostics fee: $19.99 (includes round-trip domestic shipping).
- If you approve the repair quote, the $19.99 diagnostic fee is credited directly toward your repair cost.

## Common Out-of-Warranty Repair Costs
- Headphone battery replacement: $29.99.
- Smartwatch screen assembly: $49.99.
- Charger cord or port rebuilding: $19.99.
- All completed repairs include a 90-day parts and labor guarantee.
""",

    "warranties/water_damage_limitations.md": """# Water Resistance Ratings and Liquid Limitations

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-008  

## Overview
Water resistance is not a permanent state and does not constitute absolute waterproofing under all conditions.

## Rating Clarifications
- **IPX4:** Splash-proof from rain and light exercise sweat. Do not submerge.
- **IPX7:** Immersion in fresh water up to 1 meter for 30 minutes. Not rated for high-velocity water sports.
- **5 ATM:** Water resistant up to 50 meters depth. Suitable for pool swimming and showering. Not rated for scuba diving or hot saunas.

## Liquid Ingress Warranty Exclusions
Standard warranty does NOT cover liquid damage caused by steam, hot water, salt water corrosion, or unsealed charging port covers.
""",

    "warranties/commercial_use_restrictions.md": """# Commercial and Industrial Usage Restrictions

**Category:** Warranties  
**Last Updated:** January 2026  
**Document ID:** WAR-009  

## Overview
Consumer electronics in the ShopAssist catalog are engineered and certified for consumer residential use.

## Restrictions
- Using items in continuous commercial operations (e.g. gym audio rental, taxi dash monitoring, internet café keyboards) reduces standard warranty duration to 90 days.
- Commercial operations require enrollment in the ShopAssist Enterprise Hardware Fleet program.
""",

    "warranties/replacement_parts_policy.md": """# Genuine OEM Replacement Parts and DIY Repair

**Category:** Warranties  
**Last Updated:** February 2026  
**Document ID:** WAR-010  

## Overview
We support consumer Right-to-Repair and supply genuine OEM replacement components for self-repair enthusiasts.

## Available Spare Parts
- SoundFlow ear cushions, audio cables, headband pads.
- Pulse Watch silicone sport bands, magnetic charging docks.
- Projector replacement power bricks, remote controls.

## Repair Impact on Warranty
Performing self-repairs with genuine ShopAssist OEM parts using our published repair manuals does NOT void remaining warranty on unaffected components.
""",

    # ---------------- TROUBLESHOOTING (10) ----------------
    "troubleshooting/bluetooth_pairing_issues.md": """# Troubleshooting Bluetooth Pairing and Dropouts

**Category:** Troubleshooting  
**Last Updated:** February 2026  
**Document ID:** TBL-001  

## Symptoms
Headphones or earbuds fail to discover in Bluetooth settings, continuously disconnect, or audio stutters.

## Step-by-Step Resolution
1. **Forget Device:** On your phone or laptop, open Bluetooth settings, select the device name, and choose "Forget This Device".
2. **Clear Pairing Memory:**
   - SoundFlow Pro: Power off. Press and hold Power + Volume Up for 7 seconds until the LED flashes blue and red rapidly.
   - SoundFlow Air: Place both earbuds into case. Hold case button for 10 seconds until LED blinks white 3 times.
3. **Toggle Bluetooth:** Turn off your host device Bluetooth, wait 10 seconds, and turn it back on.
4. **Re-pair:** Open case lid or power on headphones; select device from discovered list.

## Interference Factors
Ensure you are not in direct proximity to high-frequency microwave ovens, 2.4GHz Wi-Fi routers, or dense steel walls.
""",

    "troubleshooting/device_not_charging.md": """# Troubleshooting Devices That Will Not Charge

**Category:** Troubleshooting  
**Last Updated:** January 2026  
**Document ID:** TBL-002  

## Symptoms
Device does not display charging LED, battery percentage does not increase, or charger feels unusually warm.

## Troubleshooting Steps
1. **Inspect Charging Port:** Use a wooden toothpick or soft dry brush to remove lint or debris from the USB-C port. Never use metal needles.
2. **Test Alternative Power Source:** Switch to a wall outlet rather than a computer USB hub. Ensure the power adapter outputs at least 5V/2A (10W).
3. **Verify Cable Integrity:** Try a secondary known-good USB-C cable.
4. **Perform Battery Soft Reset:** Hold the power button down continuously for 20 seconds while plugged into a verified wall charger.

## Deep Discharge Recovery
If the device has been in storage for months, the battery may be in deep sleep. Leave connected to charger for at least 45 minutes before attempting to power on.
""",

    "troubleshooting/battery_drain_fast.md": """# Resolving Rapid Battery Drain Issues

**Category:** Troubleshooting  
**Last Updated:** February 2026  
**Document ID:** TBL-003  

## Symptoms
Battery life lasts significantly shorter than published manufacturer specifications.

## Recommended Optimizations
- **SoundFlow Headphones/Earbuds:** Disable LDAC high-res codec if listening in noisy environments; standard AAC uses 35% less power. Reduce listening volume from 100% to 70%.
- **Pulse Watch Active:** Set screen timeout to 5 seconds instead of "Always-on Display". Lower continuous SpO2 tracking frequency from 1-minute to 15-minute intervals.
- **Power Bank:** Avoid leaving devices plugged in after they reach 100% to prevent continuous trickling.

## Battery Recalibration Routine
Discharge the device completely until it shuts down automatically. Charge uninterrupted to 100% and keep plugged in for an additional 1 hour. Repeat twice.
""",

    "troubleshooting/firmware_update_failure.md": """# Resolving Firmware Update Loops and Errors

**Category:** Troubleshooting  
**Last Updated:** January 2026  
**Document ID:** TBL-004  

## Symptoms
Companion mobile app indicates "Update Failed" at 99%, or device is stuck with solid purple LED.

## Resolution Steps
1. Ensure the device battery is at least 60% before initiating firmware flash.
2. Keep the mobile phone within 1 foot (30 cm) of the device during wireless Bluetooth OTA transfer.
3. Turn off Wi-Fi on your phone and switch to Cellular Data (or vice versa) to prevent network socket drops.
4. If stuck in boot loop: Hold Power + Action button for 15 seconds to force emergency recovery mode, then open the companion app to resume flash.
""",

    "troubleshooting/audio_distortion_crackling.md": """# Fixing Audio Crackling, Distortion, or Low Volume

**Category:** Troubleshooting  
**Last Updated:** February 2026  
**Document ID:** TBL-005  

## Symptoms
Static noise, robotic distortion, unbalanced left/right volume, or muffled treble.

## Troubleshooting Checklist
1. **Clean Acoustic Mesh:** Check earbud nozzle or headphone grilles for earwax or dirt. Clean gently with an alcohol prep swab.
2. **Audio Codec Reset:** In Windows or macOS Bluetooth sound settings, toggle from "Hands-Free AG Audio" to "Stereo Headphones".
3. **Check EQ Presets:** In the companion app, reset the Equalizer to "Flat" or "Default".
4. **Mono Audio Setting:** Ensure phone accessibility settings do not have "Mono Audio" enabled.
""",

    "troubleshooting/factory_reset_instructions.md": """# Master Factory Reset Guide for All Devices

**Category:** Troubleshooting  
**Last Updated:** January 2026  
**Document ID:** TBL-006  

## Overview
A factory reset restores default factory settings, clears pairing memory, and resolves 95% of software freezes.

## Instructions by Model
- **SoundFlow Pro:** Press and hold Power + Volume (+) + Volume (-) simultaneously for 6 seconds. LED blinks red 3 times.
- **SoundFlow Air:** Place buds in case. Hold rear button for 12 seconds until LED flashes amber then green.
- **Pulse Watch Active:** Go to Settings > System > Factory Reset. Tap Confirm.
- **SwiftCharge Power Bank:** Hold power button for 15 seconds to reboot digital controller.
- **EchoBeam Projector:** Go to Android Settings > Device Preferences > Reset > Erase Everything.
""",

    "troubleshooting/water_exposure_recovery.md": """# Emergency Water Exposure Recovery Steps

**Category:** Troubleshooting  
**Last Updated:** January 2026  
**Document ID:** TBL-007  

## CRITICAL: What NOT to Do
- Do NOT turn the device on.
- Do NOT plug it into a charger.
- Do NOT use a hot hair dryer or oven (heat melts waterproof adhesives and ruptures lithium cells).
- Do NOT use uncooked rice (rice dust enters ports and forms cement-like sludge).

## Step-by-Step Drying Protocol
1. Dry the exterior immediately with a microfiber towel.
2. Shake gently with ports facing downward to dislodge droplets.
3. Place in a sealed container filled with silica gel packets for 48 hours.
4. Only attempt to power on after 48 hours of thorough desiccant drying.
""",

    "troubleshooting/smartwatch_sensor_calibration.md": """# Calibrating Smartwatch Heart Rate and GPS Sensors

**Category:** Troubleshooting  
**Last Updated:** February 2026  
**Document ID:** TBL-008  

## Symptoms
Heart rate displays "---", step counts inaccurate, or GPS track wandering wildly.

## Calibration Procedures
- **Skin Sensor:** Wipe bottom optical sensor with damp cloth. Wear watch one finger's width above wrist bone snug enough not to slide.
- **GPS Calibration:** Start an outdoor workout in an open sky area. Stand stationary for 60 seconds while the GPS icon pulses until it locks solid green before running.
- **Compass:** Perform a figure-8 motion in the air with the watch on your wrist for 15 seconds.
""",

    "troubleshooting/projector_keystone_focus.md": """# EchoBeam Projector Keystone and Focus Calibration

**Category:** Troubleshooting  
**Last Updated:** January 2026  
**Document ID:** TBL-009  

## Symptoms
Projected image is trapezoidal, blurry around corners, or auto-focus fails to trigger.

## Troubleshooting Steps
1. **Clean Lens:** Wipe glass projection lens with optical microfiber cloth using gentle circular strokes.
2. **Manual Focus Override:** Press Focus (+) or (-) on the remote control to bypass auto-focus sensor.
3. **Four-Corner Keystone:** Navigate to Settings > Projector Settings > Keystone Correction > 4-Point Manual Calibration to stretch corners precisely.
4. **Projection Angle:** Ensure the projector is positioned within 30 degrees perpendicular to the projection screen.
""",

    "troubleshooting/keyboard_key_unresponsive.md": """# Fixing Unresponsive Keys on Mechanical Keyboards

**Category:** Troubleshooting  
**Last Updated:** February 2026  
**Document ID:** TBL-010  

## Symptoms
A single key fails to register, registers double strokes (key chatter), or RGB LED is off.

## Troubleshooting Steps
1. **Remove Keycap:** Use the included wire keycap puller to pull straight up.
2. **Inspect Switch Stem:** Check for dust or liquid stickiness around the cross stem.
3. **Hot-Swap Switch Replacement:**
   - Use the metal switch puller to grip switch tabs top and bottom.
   - Pull straight out.
   - Inspect copper pins underneath: if bent, straighten carefully with tweezers.
   - Reinsert switch firmly until it clicks into the PCB plate.
4. **Test Key:** Connect keyboard via USB-C cable and test on key-test utility.
""",

    # ---------------- PAYMENTS (10) ----------------
    "payments/accepted_payment_methods.md": """# Accepted Payment Methods and Digital Wallets

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-001  

## Overview
ShopAssist offers safe, encrypted checkout supporting major cards, digital wallets, and local payment methods.

## Major Credit and Debit Cards
- Visa, Mastercard, American Express, Discover, Diners Club, JCB.
- Debit cards must have a 3-digit CVV and Visa/Mastercard logo.

## Digital Wallets and One-Click Checkout
- Apple Pay (Safari / iOS devices).
- Google Pay (Android / Chrome browsers).
- PayPal and PayPal Credit.
- Shop Pay (with saved delivery address and card token).

## Non-Accepted Methods
We do not accept personal checks, money orders, cash on delivery (COD), or cryptocurrencies.
""",

    "payments/split_payments_klarna_afterpay.md": """# Buy Now, Pay Later: Klarna and Afterpay Options

**Category:** Payments  
**Last Updated:** February 2026  
**Document ID:** PAY-002  

## Overview
Split your purchase into interest-free installments to manage your budget easily.

## Available BNPL Providers
- **Klarna:** Pay in 4 equal installments every 2 weeks. 0% interest, zero fees when paid on time.
- **Afterpay:** Pay in 4 equal installments every 2 weeks. Available for orders between $35.00 and $1,500.00.

## Eligibility and Credit Check
- Soft credit check only (does NOT impact your credit score).
- Must be at least 18 years old, possess a valid US billing address, and hold an active credit/debit card.
- Select Klarna or Afterpay at the payment step of checkout.
""",

    "payments/payment_declined_solutions.md": """# Resolving Declined Payments and Card Errors

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-003  

## Common Reasons for Card Declines
1. **Billing Address Mismatch (AVS):** The billing zip code entered must match the address on file with your bank statement.
2. **Card Expiration or CVV Error:** Verify expiration month/year and the 3-digit security code (4 digits on front for Amex).
3. **Fraud Protection Alert:** Large online electronics purchases often trigger your bank's anti-fraud algorithm.
4. **Daily Limit Exceeded:** The transaction exceeds your bank's daily online transaction limit.

## What to Do
- Call the 800-number on the back of your card and confirm you authorized the ShopAssist transaction.
- Try an alternative payment method (e.g. PayPal or Apple Pay).
""",

    "payments/sales_tax_and_exemptions.md": """# Sales Tax Calculation and Tax Exemption

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-004  

## How Sales Tax is Calculated
- Sales tax is calculated based on the delivery destination address in accordance with state and municipal sales tax laws (Wayfair Supreme Court ruling).
- Estimated tax displayed in cart becomes final once delivery address is verified.

## Tax-Exempt Organizations
- Educational institutions, charities, non-profits, and government agencies may qualify for tax-exempt purchases.
- Submit your State Resale Certificate or 501(c)(3) determination letter to tax@shopassist.ai prior to placing your order.
- Our finance team verifies exempt accounts within 24 business hours.
""",

    "payments/gift_card_rules.md": """# ShopAssist Digital Gift Card Rules and Terms

**Category:** Payments  
**Last Updated:** February 2026  
**Document ID:** PAY-005  

## Gift Card Features
- Denominations available from $10.00 to $500.00.
- Delivered instantly via email with printable PDF redemption certificate.
- **No Expiration Date:** ShopAssist gift cards never expire.
- **Zero Maintenance Fees:** No monthly dormancy or administration fees.

## How to Redeem
During checkout, enter the 16-character alphanumeric code in the "Gift Card or Promo Code" field and click Apply. Gift card balances can be combined with credit cards or PayPal.
""",

    "payments/promotional_codes_and_coupons.md": """# Promotional Coupon Codes and Stacking Rules

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-006  

## Promotional Guidelines
- Only one promo coupon code may be applied per order.
- Promo codes cannot be stacked with sitewide automatic flash sale discounts.
- Free shipping threshold ($50.00) applies AFTER promo discounts are calculated.

## Exclusions
Promo codes do not apply to:
- Certified Refurbished hardware.
- Digital gift card purchases.
- Out-of-warranty repair service fees.
""",

    "payments/invoice_and_receipt_requests.md": """# Downloading Formal Invoices and VAT/GST Receipts

**Category:** Payments  
**Last Updated:** February 2026  
**Document ID:** PAY-007  

## How to Download PDF Invoices
1. Log into your ShopAssist account.
2. Go to My Orders > Order Details.
3. Click "Download PDF Invoice".

## Business Details on Invoices
- Need your company name, tax ID, or VAT number displayed on the invoice?
- Check "This is a business purchase" during checkout to enter company details and tax registration numbers.
- For post-purchase invoice amendments, contact support@shopassist.ai with your Order ID.
""",

    "payments/currency_conversion.md": """# Multi-Currency Checkout and Exchange Rates

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-008  

## Currencies Supported
ShopAssist supports checkout in 12 global currencies including USD, CAD, EUR, GBP, AUD, JPY, and SGD.

## Exchange Rate Guarantee
- Live mid-market exchange rates are locked for 60 minutes once you initiate checkout.
- You will be charged the exact currency total displayed on the checkout screen.
- Your credit card issuer will not charge foreign transaction fees when paying in your local displayed currency.
""",

    "payments/security_and_fraud_prevention.md": """# Payment Security and Fraud Prevention Systems

**Category:** Payments  
**Last Updated:** February 2026  
**Document ID:** PAY-009  

## Encryption and Standards
- 256-bit SSL encryption across all website pages.
- Level 1 PCI-DSS compliant payment processing via Stripe.
- ShopAssist servers never store or have access to raw 16-digit credit card numbers or CVV codes.

## 3D Secure Verification
For your protection, transactions may prompt a 3D Secure 2.0 verification code sent by your card issuer via SMS or banking app.
""",

    "payments/chargebacks_and_disputes.md": """# Billing Disputes and Chargeback Policy

**Category:** Payments  
**Last Updated:** January 2026  
**Document ID:** PAY-010  

## Resolving Disputes Quickly
If you notice an unrecognized charge or billing discrepancy, we urge you to contact ShopAssist Customer Support first. Our team can resolve 99% of billing inquiries within 24 hours.

## Bank Chargebacks
- Filing a bank chargeback freezes your order fulfillment and account access pending investigation.
- Bank chargeback investigations require 60 to 90 business days to reach conclusion.
- Direct refunds processed with ShopAssist Support are completed in 3 to 5 business days, saving you weeks of waiting.
""",
}


def create_corpus():
    count = 0
    for rel_path, content in DOCUMENTS.items():
        file_path = BASE_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content.strip(), encoding="utf-8")
        count += 1
    print(f"Successfully generated {count} domain documents in {BASE_DIR}")


if __name__ == "__main__":
    create_corpus()
