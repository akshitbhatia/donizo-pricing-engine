#!/usr/bin/env python3
"""
Generate sample material data for Smart Semantic Pricing Engine.
Creates realistic construction materials with pricing and metadata.
"""

import random
from typing import List, Dict, Any

def generate_materials_data() -> List[Dict[str, Any]]:
    """Generate comprehensive sample materials data"""
    
    # Base material categories
    materials_data = []
    
    # Tiles and Ceramics
    tiles_data = [
        {
            "material_name": "Ceramic Wall Tile 20x20cm",
            "description": "White ceramic wall tile, 20x20cm, suitable for bathroom and kitchen walls",
            "unit_price": 12.50,
            "unit": "€/m²",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/ceramic-wall-tile-20x20"
        },
        {
            "material_name": "Porcelain Floor Tile 60x60cm",
            "description": "Grey porcelain floor tile, 60x60cm, matte finish, high durability",
            "unit_price": 28.90,
            "unit": "€/m²",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 8,
            "source_url": "https://www.castorama.fr/produit/porcelain-floor-tile-60x60"
        },
        {
            "material_name": "Mosaic Tile Sheet",
            "description": "Glass mosaic tile sheet, 30x30cm, various colors, for decorative accents",
            "unit_price": 45.00,
            "unit": "€/m²",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 6,
            "source_url": "https://www.bricodepot.fr/produit/mosaic-tile-sheet"
        },
        {
            "material_name": "Carrelage Salle de Bain Blanc",
            "description": "Carrelage mural blanc pour salle de bain, 15x15cm, résistant à l'humidité",
            "unit_price": 15.80,
            "unit": "€/m²",
            "region": "Occitanie",
            "vendor": "Weldom",
            "quality_score": 7,
            "source_url": "https://www.weldom.fr/produit/carrelage-salle-bain-blanc"
        }
    ]
    
    # Adhesives and Mortars
    adhesives_data = [
        {
            "material_name": "HydroFix Waterproof Adhesive",
            "description": "High-bond waterproof tile adhesive for interior walls, 25kg bag",
            "unit_price": 18.50,
            "unit": "€/bag",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 8,
            "source_url": "https://www.leroymerlin.fr/produit/hydrofix-adhesive"
        },
        {
            "material_name": "Colle Carrelage Rapide",
            "description": "Colle carrelage à prise rapide, 20kg, pour carrelage mural et sol",
            "unit_price": 16.90,
            "unit": "€/sac",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 7,
            "source_url": "https://www.castorama.fr/produit/colle-carrelage-rapide"
        },
        {
            "material_name": "Mortier de Jointoiement",
            "description": "Mortier de jointoiement gris, 5kg, pour joints de carrelage",
            "unit_price": 8.50,
            "unit": "€/sac",
            "region": "Nouvelle-Aquitaine",
            "vendor": "Brico Dépôt",
            "quality_score": 6,
            "source_url": "https://www.bricodepot.fr/produit/mortier-jointoiement"
        },
        {
            "material_name": "Adhesive Tile Glue Premium",
            "description": "Premium tile adhesive for heavy tiles, 25kg, white color",
            "unit_price": 22.00,
            "unit": "€/bag",
            "region": "Hauts-de-France",
            "vendor": "Weldom",
            "quality_score": 9,
            "source_url": "https://www.weldom.fr/produit/adhesive-tile-glue-premium"
        }
    ]
    
    # Paints and Finishes
    paints_data = [
        {
            "material_name": "Peinture Murale Blanche",
            "description": "Peinture murale blanche mate, 10L, couvrant et lavable",
            "unit_price": 35.00,
            "unit": "€/pot",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/peinture-murale-blanche"
        },
        {
            "material_name": "Interior Wall Paint",
            "description": "Premium interior wall paint, 5L, washable finish, various colors",
            "unit_price": 42.50,
            "unit": "€/can",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 8,
            "source_url": "https://www.castorama.fr/produit/interior-wall-paint"
        },
        {
            "material_name": "Primer Undercoat",
            "description": "Universal primer undercoat, 5L, for walls and ceilings",
            "unit_price": 28.00,
            "unit": "€/can",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 6,
            "source_url": "https://www.bricodepot.fr/produit/primer-undercoat"
        },
        {
            "material_name": "Peinture Plafond",
            "description": "Peinture plafond blanche, 10L, anti-taches et couvrante",
            "unit_price": 32.00,
            "unit": "€/pot",
            "region": "Occitanie",
            "vendor": "Weldom",
            "quality_score": 7,
            "source_url": "https://www.weldom.fr/produit/peinture-plafond"
        }
    ]
    
    # Plumbing Materials
    plumbing_data = [
        {
            "material_name": "Tuyau PVC 32mm",
            "description": "Tuyau PVC évacuation 32mm, 3m, pour eaux usées",
            "unit_price": 12.50,
            "unit": "€/m",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/tuyau-pvc-32mm"
        },
        {
            "material_name": "Robinet Mélangeur",
            "description": "Robinet mélangeur chromé pour lavabo, mitigeur thermostatique",
            "unit_price": 89.00,
            "unit": "€/piece",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 8,
            "source_url": "https://www.castorama.fr/produit/robinet-melangeur"
        },
        {
            "material_name": "Valve Shut-off",
            "description": "Shut-off valve 15mm, brass construction, for water supply",
            "unit_price": 15.50,
            "unit": "€/piece",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 6,
            "source_url": "https://www.bricodepot.fr/produit/valve-shut-off"
        },
        {
            "material_name": "Raccord Cuivre",
            "description": "Raccord cuivre 15mm, coude 90°, pour installation plomberie",
            "unit_price": 8.90,
            "unit": "€/piece",
            "region": "Nouvelle-Aquitaine",
            "vendor": "Weldom",
            "quality_score": 7,
            "source_url": "https://www.weldom.fr/produit/raccord-cuivre"
        }
    ]
    
    # Electrical Materials
    electrical_data = [
        {
            "material_name": "Câble Électrique 2.5mm²",
            "description": "Câble électrique rigide 2.5mm², 100m, pour installation électrique",
            "unit_price": 45.00,
            "unit": "€/rouleau",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/cable-electrique-2-5mm"
        },
        {
            "material_name": "Interrupteur Simple",
            "description": "Interrupteur simple va-et-vient, blanc, pour éclairage",
            "unit_price": 12.50,
            "unit": "€/piece",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 6,
            "source_url": "https://www.castorama.fr/produit/interrupteur-simple"
        },
        {
            "material_name": "Prise de Courant",
            "description": "Prise de courant 16A, 2P+T, blanche, avec obturateur",
            "unit_price": 8.90,
            "unit": "€/piece",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 7,
            "source_url": "https://www.bricodepot.fr/produit/prise-courant"
        },
        {
            "material_name": "Boîte d'Encapsulation",
            "description": "Boîte d'encapsulation 100x100mm, pour interrupteurs et prises",
            "unit_price": 3.50,
            "unit": "€/piece",
            "region": "Occitanie",
            "vendor": "Weldom",
            "quality_score": 6,
            "source_url": "https://www.weldom.fr/produit/boite-encapsulation"
        }
    ]
    
    # Wood and Carpentry
    wood_data = [
        {
            "material_name": "Planche Pin 200x20mm",
            "description": "Planche pin rabotée 200x20mm, 3m, pour charpente et construction",
            "unit_price": 18.50,
            "unit": "€/m",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/planche-pin-200x20"
        },
        {
            "material_name": "Panneau OSB 18mm",
            "description": "Panneau OSB 18mm, 122x244cm, pour contreplaqué et isolation",
            "unit_price": 28.00,
            "unit": "€/m²",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 6,
            "source_url": "https://www.castorama.fr/produit/panneau-osb-18mm"
        },
        {
            "material_name": "Vis à Bois",
            "description": "Vis à bois tête fraisée 4x60mm, 100 pièces, acier galvanisé",
            "unit_price": 12.00,
            "unit": "€/boite",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 7,
            "source_url": "https://www.bricodepot.fr/produit/vis-bois"
        },
        {
            "material_name": "Chevron Sapin",
            "description": "Chevron sapin 63x75mm, 4m, pour charpente traditionnelle",
            "unit_price": 15.80,
            "unit": "€/m",
            "region": "Nouvelle-Aquitaine",
            "vendor": "Weldom",
            "quality_score": 7,
            "source_url": "https://www.weldom.fr/produit/chevron-sapin"
        }
    ]
    
    # Insulation Materials
    insulation_data = [
        {
            "material_name": "Laine de Verre",
            "description": "Laine de verre R=3.2, 100mm, 6m², pour isolation thermique",
            "unit_price": 32.00,
            "unit": "€/rouleau",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/laine-verre"
        },
        {
            "material_name": "Plaque de Plâtre",
            "description": "Plaque de plâtre 13mm, 120x250cm, pour cloisons et plafonds",
            "unit_price": 8.50,
            "unit": "€/m²",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 6,
            "source_url": "https://www.castorama.fr/produit/plaque-platre"
        },
        {
            "material_name": "Isolant Phonique",
            "description": "Isolant phonique 50mm, 10m², pour isolation acoustique",
            "unit_price": 45.00,
            "unit": "€/rouleau",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 8,
            "source_url": "https://www.bricodepot.fr/produit/isolant-phonique"
        }
    ]
    
    # Combine all materials
    all_materials = (
        tiles_data + adhesives_data + paints_data + 
        plumbing_data + electrical_data + wood_data + insulation_data
    )
    
    # Add regional variations
    regions = [
        "Île-de-France", "Provence-Alpes-Côte d'Azur", "Auvergne-Rhône-Alpes",
        "Occitanie", "Nouvelle-Aquitaine", "Hauts-de-France", "Grand Est",
        "Bourgogne-Franche-Comté", "Centre-Val de Loire", "Normandie",
        "Bretagne", "Pays de la Loire", "Corse"
    ]
    
    vendors = ["Leroy Merlin", "Castorama", "Brico Dépôt", "Weldom", "Mr Bricolage"]
    
    # Create regional variations of materials
    for material in all_materials:
        # Add base material
        materials_data.append(material)
        
        # Create variations for other regions
        for region in regions:
            if region != material["region"]:
                # Create regional variation with price adjustment
                regional_material = material.copy()
                regional_material["region"] = region
                
                # Adjust price based on region (simplified)
                price_multipliers = {
                    "Île-de-France": 1.15,
                    "Provence-Alpes-Côte d'Azur": 1.10,
                    "Corse": 1.20,
                    "Hauts-de-France": 0.90,
                    "Normandie": 0.90
                }
                
                multiplier = price_multipliers.get(region, 1.0)
                regional_material["unit_price"] = round(material["unit_price"] * multiplier, 2)
                
                # Randomly change vendor for variety
                if random.random() < 0.3:
                    regional_material["vendor"] = random.choice(vendors)
                
                materials_data.append(regional_material)
    
    # Add some additional specialized materials
    specialized_materials = [
        {
            "material_name": "Enduit de Lissage",
            "description": "Enduit de lissage fin, 25kg, pour préparation des murs avant peinture",
            "unit_price": 18.50,
            "unit": "€/sac",
            "region": "Île-de-France",
            "vendor": "Leroy Merlin",
            "quality_score": 7,
            "source_url": "https://www.leroymerlin.fr/produit/enduit-lissage"
        },
        {
            "material_name": "Joint de Dilatation",
            "description": "Joint de dilatation 10mm, 3m, pour carrelage et sols",
            "unit_price": 12.00,
            "unit": "€/m",
            "region": "Provence-Alpes-Côte d'Azur",
            "vendor": "Castorama",
            "quality_score": 6,
            "source_url": "https://www.castorama.fr/produit/joint-dilatation"
        },
        {
            "material_name": "Gouttière PVC",
            "description": "Gouttière PVC 100mm, 3m, pour évacuation des eaux pluviales",
            "unit_price": 25.00,
            "unit": "€/m",
            "region": "Auvergne-Rhône-Alpes",
            "vendor": "Brico Dépôt",
            "quality_score": 7,
            "source_url": "https://www.bricodepot.fr/produit/gouttiere-pvc"
        }
    ]
    
    materials_data.extend(specialized_materials)
    
    return materials_data

def generate_test_queries() -> List[str]:
    """Generate test queries for the system"""
    return [
        "Need waterproof glue for bathroom tiles",
        "Matte tiles for bathroom wall, probably 60 by 60. Something durable. I'm in Marseille.",
        "colle pour carrelage salle de bain mur blanc",
        "glue tile interior wet wall high quality PACA",
        "maybe something for outdoor? cement-ish? matte or polished?",
        "Need strong glue, the waterproof one for the shower tiles. Not the cheap stuff. Should be white.",
        "Peinture murale blanche pour salon",
        "Tuyau PVC évacuation cuisine",
        "Câble électrique pour installation",
        "Planche bois charpente",
        "Laine isolation combles",
        "Robinet mélangeur douche",
        "Carrelage sol extérieur",
        "Enduit façade",
        "Panneau isolation phonique"
    ]

if __name__ == "__main__":
    # Generate and print sample data
    materials = generate_materials_data()
    print(f"Generated {len(materials)} materials")
    
    # Print first few materials as example
    for i, material in enumerate(materials[:5]):
        print(f"\nMaterial {i+1}:")
        print(f"  Name: {material['material_name']}")
        print(f"  Price: {material['unit_price']} {material['unit']}")
        print(f"  Region: {material['region']}")
        print(f"  Vendor: {material['vendor']}")
    
    # Print test queries
    queries = generate_test_queries()
    print(f"\nGenerated {len(queries)} test queries")
    for query in queries[:5]:
        print(f"  - {query}")
