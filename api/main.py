# api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from typing import Dict, Any
import uvicorn

app = FastAPI(
    title="Without® DPP API",
    description="Digital Product Passport for Recycled MLP Bottles (Shampoo & Sunscreen)",
    version="1.0"
)

PRODUCTS_DIR = "../products"

class DPPResponse(BaseModel):
    dpp_id: str
    epc: str
    product_name: str
    variant: str
    is_sustainable: bool
    confidence: float
    brand: str
    client: str
    location: str
    qr_url: str
    waste_diverted_g: int

def load_dpp(epc: str) -> Dict[Any, Any]:
    # Extract serial from EPC for filename (e.g., sgtin_0614141_123456_0000000001.json)
    parts = epc.split('.') + ['']  # Handle missing parts
    filename = f"sgtin_{parts[3]}_{parts[4]}_{parts[5]}.json"  # Adapt to actual serial
    serial_part = parts[5].replace('000000000', 'DPP-MLP-2025-001-')  # Map to file
    filename = f"{serial_part}.json"
    path = os.path.join(PRODUCTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Bottle not found – Check EPC")
    with open(path, "r") as f:
        return json.load(f)

def simple_ai_check(dpp: dict) -> tuple[bool, float]:
    carbon = dpp["environmental_impact"]["carbon_footprint_kgCO2e"]
    recyclability = dpp["environmental_impact"]["recyclability_score"]
    recycled_content = dpp["packaging"]["bottle"]["recycled_content"]
    waste_diverted = dpp["product"]["waste_diverted_g"]
    
    score = (0.3 * (1 - carbon / 0.5)) + (0.3 * recyclability) + (0.2 * (recycled_content / 100)) + (0.2 * (waste_diverted / 100))
    return score > 0.85, score  # Higher threshold for Without® standards

@app.get("/dpp/bottles/{epc}", response_model=DPPResponse)
def get_dpp(epc: str):
    dpp = load_dpp(epc)
    sustainable, confidence = simple_ai_check(dpp)
    
    return DPPResponse(
        dpp_id=dpp["dpp_id"],
        epc=dpp["epc"],
        product_name=dpp["product"]["name"],
        variant=dpp["product"]["variant"],
        is_sustainable=sustainable,
        confidence=confidence,
        brand=dpp["metadata"]["brand"],
        client=dpp["metadata"]["client"],
        location=dpp["metadata"]["client_location"],
        qr_url=dpp["metadata"]["qr_code_url"],
        waste_diverted_g=dpp["product"]["waste_diverted_g"]
    )

@app.get("/")
def root():
    return {"message": "Without® DPP API – Access via /dpp/bottles/{epc} (e.g., urn:epc:id:sgtin:0614141.123456.0000000001)"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
