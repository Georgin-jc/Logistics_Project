from fastapi import FastAPI
from Get_Delivery import get_deliveries_for_zust
import requests

app = FastAPI()

ORS_API_KEY = "----Paste your ORS API Key here----------"

@app.get("/deliveries/{zust}")
def deliveries(zust: str):
    return get_deliveries_for_zust(zust)

