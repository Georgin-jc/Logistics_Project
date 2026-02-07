from fastapi import FastAPI
from Get_Delivery import get_deliveries_for_zust
import requests

app = FastAPI()

ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjMxOTcxMTY0NDY4ODRiODM5Nzk1ODIxYzhhYzJiMGM3IiwiaCI6Im11cm11cjY0In0="

@app.get("/deliveries/{zust}")
def deliveries(zust: str):
    return get_deliveries_for_zust(zust)

