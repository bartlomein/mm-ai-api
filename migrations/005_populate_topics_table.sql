-- Migration: Populate topics table with stock market sectors and industries
-- File: 005_populate_topics_table.sql

-- Insert stock market sectors and industries (using ON CONFLICT to handle duplicates)
INSERT INTO topics (name, display_name, category, description) VALUES
    -- Main Sector Categories (Broad sector briefings)
    ('technology', 'Technology Sector', 'technology', 'Comprehensive coverage of the technology sector including software, hardware, and emerging tech'),
    ('healthcare', 'Healthcare Sector', 'healthcare', 'Comprehensive coverage of healthcare including biotech, pharma, and medical services'),
    ('energy', 'Energy Sector', 'energy', 'Comprehensive coverage of energy sector including oil, gas, renewables, and utilities'),
    ('finance', 'Financial Sector', 'finance', 'Comprehensive coverage of financial services including banks, fintech, and insurance'),
    ('industrial', 'Industrial Sector', 'industrial', 'Comprehensive coverage of industrial companies including manufacturing and aerospace'),
    ('consumer', 'Consumer Sector', 'consumer', 'Comprehensive coverage of consumer companies including retail and entertainment'),
    ('materials', 'Materials Sector', 'materials', 'Comprehensive coverage of materials sector including mining and chemicals'),
    ('utilities', 'Utilities Sector', 'utilities', 'Comprehensive coverage of utility companies including electric, gas, and water'),
    ('communication', 'Communication Sector', 'communication', 'Comprehensive coverage of communication companies including telecom and media'),
    ('real_estate', 'Real Estate Sector', 'real_estate', 'Comprehensive coverage of real estate investment trusts and property companies'),
    
    -- Healthcare Industry Subcategories
    ('biotechnology', 'Biotechnology', 'healthcare', 'Companies developing biological products and technologies for medical and agricultural applications'),
    ('pharmaceutical', 'Pharmaceutical', 'healthcare', 'Drug development, manufacturing, and healthcare companies'),
    ('medical_devices', 'Medical Devices', 'healthcare', 'Companies manufacturing medical equipment, devices, and diagnostic tools'),
    ('healthcare_services', 'Healthcare Services', 'healthcare', 'Healthcare providers, hospitals, and medical service companies'),
    
    -- Technology Industry Subcategories
    ('artificial_intelligence', 'Artificial Intelligence', 'technology', 'AI, machine learning, and automation technology companies'),
    ('software', 'Software', 'technology', 'Software development, SaaS, and enterprise technology companies'),
    ('semiconductors', 'Semiconductors', 'technology', 'Chip manufacturers, semiconductor equipment, and related technologies'),
    ('cybersecurity', 'Cybersecurity', 'technology', 'Information security, data protection, and cybersecurity companies'),
    ('cloud_computing', 'Cloud Computing', 'technology', 'Cloud infrastructure, services, and platform providers'),
    
    -- Energy Sector
    ('renewable_energy', 'Renewable Energy', 'energy', 'Solar, wind, hydroelectric, and other clean energy companies'),
    ('oil_gas', 'Oil & Gas', 'energy', 'Traditional energy companies including exploration, production, and refining'),
    ('electric_vehicles', 'Electric Vehicles', 'energy', 'EV manufacturers, battery technology, and charging infrastructure'),
    ('nuclear_energy', 'Nuclear Energy', 'energy', 'Nuclear power generation and related technologies'),
    
    -- Financial Sector
    ('banking', 'Banking', 'finance', 'Traditional banks, credit unions, and lending institutions'),
    ('fintech', 'Financial Technology', 'finance', 'Digital payments, cryptocurrency, and financial technology companies'),
    ('insurance', 'Insurance', 'finance', 'Insurance providers and related financial services'),
    ('reits', 'REITs & Real Estate Investment', 'finance', 'Real Estate Investment Trusts and property investment companies'),
    
    -- Industrial Sector
    ('aerospace_defense', 'Aerospace & Defense', 'industrial', 'Aircraft manufacturers, defense contractors, and space companies'),
    ('manufacturing', 'Manufacturing', 'industrial', 'Industrial manufacturing, automation, and production companies'),
    ('transportation', 'Transportation', 'industrial', 'Airlines, shipping, logistics, and transportation infrastructure'),
    ('construction', 'Construction', 'industrial', 'Construction companies, building materials, and infrastructure'),
    
    -- Consumer Sector
    ('retail', 'Retail', 'consumer', 'Traditional and e-commerce retail companies'),
    ('food_beverage', 'Food & Beverage', 'consumer', 'Food producers, restaurants, and beverage companies'),
    ('entertainment', 'Entertainment', 'consumer', 'Media, gaming, streaming, and entertainment companies'),
    ('automotive', 'Automotive', 'consumer', 'Traditional automotive manufacturers and suppliers'),
    
    -- Materials Sector
    ('metals_mining', 'Metals & Mining', 'materials', 'Mining companies, precious metals, and industrial metals'),
    ('chemicals', 'Chemicals', 'materials', 'Chemical manufacturers and specialty chemical companies'),
    
    -- Communication Sector
    ('telecommunications', 'Telecommunications', 'communication', 'Telecom providers, wireless carriers, and communication infrastructure'),
    ('media', 'Media', 'communication', 'Traditional media, publishing, and broadcasting companies')

-- Handle duplicate key conflicts by updating existing records
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    category = EXCLUDED.category,
    description = EXCLUDED.description,
    updated_at = now();