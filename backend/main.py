from fastapi import FastAPI, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from web3 import Web3
import requests
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RARIBLE_API_KEY = "7d36e227-fd31-4611-b2aa-829064e88e29"
INFURA_URL = "https://mainnet.infura.io/v3/e140e14ae2dc43eb91ca74b9db4f7b26"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))


USE_LOCAL_TEST_FILE = True

RARIBLE_API_URL = "https://api.rarible.org/v0.1/items/ETHEREUM:{contract}:{token}"

def compute_sha256(data_bytes: bytes) -> str:
    return hashlib.sha256(data_bytes).hexdigest()

def get_rarible_metadata(contract_address: str, token_id: str) -> dict:
    url = RARIBLE_API_URL.format(contract=contract_address.lower(), token=token_id)
    headers = {"Accept": "application/json", "X-API-KEY": RARIBLE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 404:
        return {}
    elif response.status_code != 200:
        raise Exception(f"Rarible API request failed: {response.status_code}")
    return response.json()

def download_file(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content

def verify_signature(original_message: str, signed_message: str, claimed_address: str) -> bool:
    from eth_account.messages import encode_defunct
    try:
        encoded_message = encode_defunct(text=original_message)
        recovered_address = web3.eth.account.recover_message(encoded_message, signature=signed_message)
        return recovered_address.lower() == claimed_address.lower()
    except Exception as e:
        raise Exception(f"Signature verification failed: {str(e)}")

@app.post("/verify-nft/")
async def verify_nft(
    nft_contract: str = Form(...),
    token_id: str = Form(...),
    wallet_address: str = Form(...),
    original_message: str = Form(...),
    signed_message: str = Form(...),
    file: UploadFile = Form(...)
):
    # Step 1: Verify signature
    try:
        if not verify_signature(original_message, signed_message, wallet_address):
            raise HTTPException(status_code=403, detail="Signature verification failed: Wallet mismatch.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2: Get image data
    try:
        if USE_LOCAL_TEST_FILE:
            image_bytes = open("test_image.png", "rb").read()
            image_url = "local_test_image"
        else:
            metadata = get_rarible_metadata(nft_contract, token_id)
            image_url = None
            if metadata:
                # Adjust the path based on the actual metadata structure.
                image_url = metadata.get("meta", {}).get("content", [{}])[0].get("url")
            if not image_url:
                raise Exception("Image could not be fetched from Rarible metadata.")
            image_bytes = download_file(image_url)
        trusted_hash = compute_sha256(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching trusted image: {str(e)}")

    # Step 3: Read uploaded file
    try:
        user_file_bytes = await file.read()
        submitted_hash = compute_sha256(user_file_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {str(e)}")

    # Step 4: Compare hashes and respond
    is_authentic = (trusted_hash == submitted_hash)
    result_message = "NFT is authentic." if is_authentic else "NFT file does not match trusted source; it may be tampered with or fraudulent."

    return {
        "authentic": is_authentic,
        "trusted_hash": trusted_hash,
        "submitted_hash": submitted_hash,
        "image_url": image_url,
        "message": result_message
    }
